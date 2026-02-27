"""
Execution Router
================

REST API and WebSocket endpoints for the Computer Use Execution Engine.
Manages execution sessions: start, pause, resume, inject messages, stop.

Endpoints:
  POST /api/execution/start              — Start a new execution session
  POST /api/execution/{session_id}/pause — Pause session
  POST /api/execution/{session_id}/resume — Resume session
  POST /api/execution/{session_id}/inject — Inject human message
  POST /api/execution/{session_id}/stop  — Stop session
  GET  /api/execution/{session_id}/status — Get session status
  GET  /api/execution/health             — Check engine availability
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..services.computer_use_agent import (
    ComputerUseAgent,
    ExecutionEvent,
    StepConfig,
    StepResult,
)
from ..services.docker_manager import (
    ContainerInfo,
    DockerManager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution", tags=["execution"])

# ---------------------------------------------------------------------------
# Pydantic Request/Response Models
# ---------------------------------------------------------------------------


class StartExecutionRequest(BaseModel):
    """Request to start a new execution session."""

    project_id: str = Field(..., min_length=1)
    steps: list[StepConfig] = Field(..., min_length=1)


class StartExecutionResponse(BaseModel):
    """Response after starting an execution session."""

    session_id: str
    status: str
    novnc_url: str | None = None
    container_id: str | None = None


class InjectMessageRequest(BaseModel):
    """Request to inject a human message into a session."""

    message: str = Field(..., min_length=1, max_length=10000)


class SessionStatusResponse(BaseModel):
    """Current status of an execution session."""

    session_id: str
    project_id: str
    status: Literal["starting", "running", "paused", "completed", "error", "stopped"]
    current_step_index: int
    total_steps: int
    novnc_url: str | None = None
    started_at: str
    results: list[StepResult] = []


class ExecutionHealthResponse(BaseModel):
    """Health status of the execution engine."""

    enabled: bool
    docker_available: bool
    active_sessions: int


# ---------------------------------------------------------------------------
# Execution Session State
# ---------------------------------------------------------------------------


class ExecutionSession:
    """Tracks the state of a running execution session."""

    def __init__(
        self,
        session_id: str,
        project_id: str,
        steps: list[StepConfig],
    ):
        self.session_id = session_id
        self.project_id = project_id
        self.steps = steps
        self.status: Literal[
            "starting", "running", "paused", "completed", "error", "stopped"
        ] = "starting"
        self.current_step_index = 0
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.container_info: ContainerInfo | None = None
        self.agent: ComputerUseAgent | None = None
        self.results: list[StepResult] = []
        self.task: asyncio.Task | None = None
        self.websocket_clients: set[WebSocket] = set()


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------

_docker_manager = DockerManager()
_sessions: dict[str, ExecutionSession] = {}


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=StartExecutionResponse)
async def start_execution(request: StartExecutionRequest) -> StartExecutionResponse:
    """Start a new computer-use execution session."""
    session_id = uuid.uuid4().hex[:12]

    session = ExecutionSession(
        session_id=session_id,
        project_id=request.project_id,
        steps=request.steps,
    )
    _sessions[session_id] = session

    # Try to start Docker container
    container_info: ContainerInfo | None = None
    docker_available = await _docker_manager.is_available()

    if docker_available:
        try:
            container_info = await _docker_manager.start_container(session_id)
            session.container_info = container_info
        except Exception as e:
            logger.warning(
                f"Docker container failed to start: {e}. "
                "Proceeding without container (agent tools may be limited)."
            )

    # Create and configure the agent
    first_step_model = request.steps[0].model if request.steps else "claude-opus-4-6"
    agent = ComputerUseAgent(session_id=session_id, model=first_step_model)

    # Register event callback for WebSocket broadcasting
    async def broadcast_event(event: ExecutionEvent) -> None:
        await _broadcast_to_session(session_id, event.model_dump())

    agent.on_event(broadcast_event)
    session.agent = agent
    session.status = "running"

    # Start execution in the background
    session.task = asyncio.create_task(
        _run_session(session_id), name=f"execution-{session_id}"
    )

    logger.info(
        f"Execution session {session_id} started for project {request.project_id} "
        f"({len(request.steps)} steps)"
    )

    return StartExecutionResponse(
        session_id=session_id,
        status="running",
        novnc_url=container_info.novnc_url if container_info else None,
        container_id=container_info.container_id if container_info else None,
    )


@router.post("/{session_id}/pause")
async def pause_execution(session_id: str) -> dict:
    """Pause a running execution session."""
    session = _get_session(session_id)
    if session.status != "running":
        raise HTTPException(
            status_code=400, detail=f"Session is {session.status}, not running"
        )

    if session.agent:
        await session.agent.pause()
    session.status = "paused"

    return {"session_id": session_id, "status": "paused"}


@router.post("/{session_id}/resume")
async def resume_execution(session_id: str) -> dict:
    """Resume a paused execution session."""
    session = _get_session(session_id)
    if session.status != "paused":
        raise HTTPException(
            status_code=400, detail=f"Session is {session.status}, not paused"
        )

    if session.agent:
        await session.agent.resume()
    session.status = "running"

    return {"session_id": session_id, "status": "running"}


@router.post("/{session_id}/inject")
async def inject_message(session_id: str, request: InjectMessageRequest) -> dict:
    """Inject a human message into a running or paused session."""
    session = _get_session(session_id)
    if session.status not in ("running", "paused"):
        raise HTTPException(
            status_code=400, detail=f"Session is {session.status}, cannot inject"
        )

    if session.agent:
        await session.agent.inject_message(request.message)

    return {"session_id": session_id, "message": "injected"}


@router.post("/{session_id}/stop")
async def stop_execution(session_id: str) -> dict:
    """Stop an execution session and clean up resources."""
    session = _get_session(session_id)

    # Stop the agent
    if session.agent:
        await session.agent.stop()

    # Cancel the background task
    if session.task and not session.task.done():
        session.task.cancel()

    # Stop the container
    await _docker_manager.stop_container(session_id)

    session.status = "stopped"

    logger.info(f"Execution session {session_id} stopped")
    return {"session_id": session_id, "status": "stopped"}


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """Get current status and progress of an execution session."""
    session = _get_session(session_id)

    return SessionStatusResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        status=session.status,
        current_step_index=session.current_step_index,
        total_steps=len(session.steps),
        novnc_url=(
            session.container_info.novnc_url if session.container_info else None
        ),
        started_at=session.started_at,
        results=session.results,
    )


@router.get("/health", response_model=ExecutionHealthResponse)
async def execution_health() -> ExecutionHealthResponse:
    """Check if the execution engine is available."""
    from ..services.docker_manager import COMPUTER_USE_ENABLED

    docker_available = await _docker_manager.is_available()

    return ExecutionHealthResponse(
        enabled=COMPUTER_USE_ENABLED,
        docker_available=docker_available,
        active_sessions=len(
            [s for s in _sessions.values() if s.status in ("running", "paused")]
        ),
    )


# ---------------------------------------------------------------------------
# WebSocket Endpoint (registered separately in main.py)
# ---------------------------------------------------------------------------


async def execution_websocket_handler(websocket: WebSocket, session_id: str) -> None:
    """Handle WebSocket connections for real-time execution events."""
    await websocket.accept()

    session = _sessions.get(session_id)
    if not session:
        await websocket.send_json({"type": "error", "data": {"error": "Session not found"}})
        await websocket.close()
        return

    session.websocket_clients.add(websocket)
    logger.info(f"WebSocket client connected to session {session_id}")

    # Send current status immediately
    await websocket.send_json(
        {
            "type": "status",
            "session_id": session_id,
            "data": {
                "status": session.status,
                "current_step": session.current_step_index,
                "total_steps": len(session.steps),
            },
        }
    )

    try:
        while True:
            # Keep connection alive; client can also send messages
            data = await websocket.receive_text()
            # Client messages could be used for chat/inject in the future
            logger.debug(f"WebSocket message from client: {data[:100]}")
    except WebSocketDisconnect:
        pass
    finally:
        session.websocket_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected from session {session_id}")


# ---------------------------------------------------------------------------
# Background Task: Session Execution
# ---------------------------------------------------------------------------


async def _run_session(session_id: str) -> None:
    """Background task that runs the agent through all steps."""
    session = _sessions.get(session_id)
    if not session or not session.agent:
        return

    try:
        results = await session.agent.execute_steps(session.steps)
        session.results = results
        session.current_step_index = len(session.steps)
        session.status = "completed"

        await _broadcast_to_session(
            session_id,
            {
                "type": "status",
                "session_id": session_id,
                "data": {"status": "completed", "results_count": len(results)},
            },
        )

        logger.info(
            f"Session {session_id} completed: "
            f"{sum(1 for r in results if r.status == 'completed')}/{len(results)} "
            "steps succeeded"
        )

    except asyncio.CancelledError:
        logger.info(f"Session {session_id} task cancelled")
        session.status = "stopped"

    except Exception as e:
        logger.error(f"Session {session_id} failed: {e}")
        session.status = "error"
        await _broadcast_to_session(
            session_id,
            {
                "type": "error",
                "session_id": session_id,
                "data": {"error": str(e)},
            },
        )

    finally:
        # Clean up container
        try:
            await _docker_manager.stop_container(session_id)
        except Exception as e:
            logger.debug(f"Container cleanup for {session_id}: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_session(session_id: str) -> ExecutionSession:
    """Get a session by ID or raise 404."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


async def _broadcast_to_session(session_id: str, message: dict) -> None:
    """Broadcast a message to all WebSocket clients of a session."""
    session = _sessions.get(session_id)
    if not session:
        return

    disconnected: set[WebSocket] = set()
    for ws in session.websocket_clients:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)

    session.websocket_clients -= disconnected


async def cleanup_all_execution_sessions() -> None:
    """Clean up all sessions. Called during server shutdown."""
    for session_id in list(_sessions.keys()):
        session = _sessions[session_id]
        if session.agent:
            await session.agent.stop()
        if session.task and not session.task.done():
            session.task.cancel()
    await _docker_manager.cleanup_all()
    _sessions.clear()
    logger.info("All execution sessions cleaned up")
