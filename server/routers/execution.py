"""
Execution Router
================

REST and WebSocket endpoints for computer-use execution sessions.
Provides start/stop/pause/resume controls, message injection, takeover
mode, step jumping, and real-time event streaming via WebSocket.

Frontend endpoints:
  POST /api/execution/start
  POST /api/execution/{session_id}/pause
  POST /api/execution/{session_id}/resume
  POST /api/execution/{session_id}/stop
  POST /api/execution/{session_id}/inject
  POST /api/execution/{session_id}/takeover
  POST /api/execution/{session_id}/jump
  GET  /api/execution/{session_id}/state
  WS   /ws/execution/{session_id}
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ..services.computer_use_agent import (
    create_session,
    get_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution", tags=["execution"])


# ---------------------------------------------------------------------------
# Pydantic Request / Response Models
# ---------------------------------------------------------------------------


class StartExecutionRequest(BaseModel):
    """Body for POST /start — mirrors frontend YTStartExecutionRequest."""

    project_id: str
    step_ids: list[str]
    model: str = Field(default="claude-opus-4-6")


class StartExecutionResponse(BaseModel):
    """Response for POST /start — mirrors frontend YTStartExecutionResponse."""

    session_id: str
    novnc_url: str
    status: str


class InjectMessageRequest(BaseModel):
    """Body for POST /{session_id}/inject."""

    message: str


class TakeoverRequest(BaseModel):
    """Body for POST /{session_id}/takeover."""

    enable: bool


class JumpToStepRequest(BaseModel):
    """Body for POST /{session_id}/jump."""

    step_id: str


class ExecutionSessionState(BaseModel):
    """Response for GET /{session_id}/state — mirrors frontend YTExecutionSession."""

    session_id: str
    project_id: str
    status: str
    current_step: int
    total_steps: int
    novnc_url: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _require_session(session_id: str):
    """Return the ComputerUseAgent for the session or raise 404."""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution session '{session_id}' not found",
        )
    return session


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=StartExecutionResponse)
async def start_execution(request: StartExecutionRequest) -> StartExecutionResponse:
    """Start a new computer-use execution session."""
    session = create_session()

    try:
        await session.start(
            project_id=request.project_id,
            step_ids=request.step_ids,
            model=request.model,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return StartExecutionResponse(
        session_id=session.session_id,
        novnc_url=session.novnc_url,
        status=session.status.value,
    )


@router.post("/{session_id}/pause")
async def pause_execution(session_id: str) -> dict[str, str]:
    """Pause the agent after the current tool call completes."""
    session = _require_session(session_id)

    try:
        await session.pause()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": session.status.value}


@router.post("/{session_id}/resume")
async def resume_execution(session_id: str) -> dict[str, str]:
    """Resume a paused or takeover session."""
    session = _require_session(session_id)

    try:
        await session.resume()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": session.status.value}


@router.post("/{session_id}/stop")
async def stop_execution(session_id: str) -> dict[str, str]:
    """Stop the execution session and clean up resources."""
    session = _require_session(session_id)

    try:
        await session.stop()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": session.status.value}


@router.post("/{session_id}/inject")
async def inject_message(session_id: str, request: InjectMessageRequest) -> dict[str, bool]:
    """Inject a user message into the agent conversation."""
    session = _require_session(session_id)

    await session.inject_message(request.message)

    return {"success": True}


@router.post("/{session_id}/takeover")
async def set_takeover(session_id: str, request: TakeoverRequest) -> dict[str, str]:
    """Toggle takeover mode (human controls the browser)."""
    session = _require_session(session_id)

    try:
        await session.set_takeover(request.enable)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"status": session.status.value}


@router.post("/{session_id}/jump")
async def jump_to_step(session_id: str, request: JumpToStepRequest) -> dict[str, Any]:
    """Jump execution to a specific step."""
    session = _require_session(session_id)

    try:
        await session.jump_to_step(request.step_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "step_id": request.step_id,
        "current_step": session.current_step,
    }


@router.get("/{session_id}/state", response_model=ExecutionSessionState)
async def get_execution_state(session_id: str) -> ExecutionSessionState:
    """Get the current state of an execution session."""
    session = _require_session(session_id)

    return ExecutionSessionState(
        session_id=session.session_id,
        project_id=session.project_id,
        status=session.status.value,
        current_step=session.current_step,
        total_steps=session.total_steps,
        novnc_url=session.novnc_url,
    )


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------


async def execution_websocket(websocket: WebSocket, session_id: str) -> None:
    """
    WebSocket handler for real-time execution events.

    Wire this up in main.py as::

        @app.websocket("/ws/execution/{session_id}")
        async def execution_ws(websocket: WebSocket, session_id: str):
            await execution_websocket(websocket, session_id)

    Server -> Client events (JSON):
      - status_change: { status }
      - agent_action:  { description }
      - agent_thinking: { content }
      - step_change:   { step_id, step_status, current_step, total_steps }
      - screenshot:    { image_url }
      - user_message:  { content }
      - agent_response: { content }
      - error:         { message }

    Client -> Server:
      - { "type": "ping" }  (keep-alive, replied with pong)
    """
    await websocket.accept()
    logger.info("Execution WebSocket connected for session %s", session_id)

    session = get_session(session_id)
    if session is None:
        await websocket.send_json(
            {
                "type": "error",
                "session_id": session_id,
                "timestamp": "",
                "data": {"message": f"Session '{session_id}' not found"},
            }
        )
        await websocket.close()
        return

    # Queue for forwarding broadcast events to this specific WebSocket
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def on_event(event: dict[str, Any]) -> None:
        """Callback registered with the session to receive broadcast events."""
        await event_queue.put(event)

    session.add_broadcast_callback(on_event)

    # Send initial state so the client is synchronized immediately
    await websocket.send_json(
        {
            "type": "status_change",
            "session_id": session_id,
            "timestamp": "",
            "data": {"status": session.status.value},
        }
    )

    async def _forward_events() -> None:
        """Forward events from the session broadcast queue to the WebSocket."""
        try:
            while True:
                event = await event_queue.get()
                await websocket.send_json(event)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _receive_messages() -> None:
        """Receive messages from the WebSocket client (keep-alive pings)."""
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except (json.JSONDecodeError, TypeError):
                    pass
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    forward_task = asyncio.create_task(_forward_events())
    receive_task = asyncio.create_task(_receive_messages())

    try:
        # Wait until either task ends (disconnect or error)
        done, pending = await asyncio.wait(
            [forward_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    finally:
        session.remove_broadcast_callback(on_event)
        logger.info("Execution WebSocket disconnected for session %s", session_id)
