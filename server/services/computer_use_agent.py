"""
Computer Use Agent Service
==========================

Manages the lifecycle of a computer-use execution session. Each session
wraps a Claude computer-use agent that navigates a browser inside a
Docker container with X11 + noVNC.

State machine::

    idle -> running -> paused     -> running (resume)
                    -> takeover   -> running (resume)
                    -> completed
                    -> error
         -> completed (all steps done)
         -> error     (unrecoverable failure)

The agent loop is structured for full computer-use integration but
degrades gracefully when Docker or the container runtime is unavailable.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

from .docker_manager import get_docker_manager
from .screen_recorder import create_capture_manager, remove_capture_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Execution status enum (mirrors frontend YTExecutionStatus)
# ---------------------------------------------------------------------------


class ExecutionStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    TAKEOVER = "takeover"
    COMPLETED = "completed"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Type alias for the WebSocket broadcast callback
# ---------------------------------------------------------------------------

# Callback signature: async def callback(event: dict) -> None
BroadcastCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


# ---------------------------------------------------------------------------
# ComputerUseAgent
# ---------------------------------------------------------------------------


class ComputerUseAgent:
    """
    Manages a single computer-use execution session.

    Responsibilities:
      - Start/stop the Docker container via DockerManager
      - Create a CaptureManager for screen recording
      - Run the agent loop (step-by-step execution)
      - Broadcast real-time events to connected WebSocket clients
      - Support pause, resume, takeover, message injection, and step jumping
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._status = ExecutionStatus.IDLE
        self._project_id: str = ""
        self._step_ids: list[str] = []
        self._model: str = "claude-opus-4-6"
        self._current_step: int = 0
        self._total_steps: int = 0

        # Concurrency primitives for pause/resume
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._stop_requested = False
        self._takeover_mode = False

        # Injected messages queue (fed into the conversation)
        self._injected_messages: asyncio.Queue[str] = asyncio.Queue()

        # WebSocket broadcast subscribers
        self._broadcast_callbacks: list[BroadcastCallback] = []

        # Background task handle for the agent loop
        self._agent_task: Optional[asyncio.Task[None]] = None

        # noVNC URL (set after container starts)
        self._novnc_url: str = ""

    # -- Properties ---------------------------------------------------------

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @property
    def current_step(self) -> int:
        return self._current_step

    @property
    def total_steps(self) -> int:
        return self._total_steps

    @property
    def novnc_url(self) -> str:
        return self._novnc_url

    @property
    def project_id(self) -> str:
        return self._project_id

    # -- Broadcasting -------------------------------------------------------

    def add_broadcast_callback(self, callback: BroadcastCallback) -> None:
        """Register a WebSocket broadcast callback."""
        if callback not in self._broadcast_callbacks:
            self._broadcast_callbacks.append(callback)

    def remove_broadcast_callback(self, callback: BroadcastCallback) -> None:
        """Unregister a WebSocket broadcast callback."""
        try:
            self._broadcast_callbacks.remove(callback)
        except ValueError:
            pass

    async def _broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Send an event to all connected WebSocket clients."""
        event = {
            "type": event_type,
            "session_id": self._session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        # Fire-and-forget to each callback; remove broken ones
        to_remove: list[BroadcastCallback] = []
        for cb in self._broadcast_callbacks:
            try:
                await cb(event)
            except Exception:
                to_remove.append(cb)
        for cb in to_remove:
            self._broadcast_callbacks.remove(cb)

    # -- State transitions --------------------------------------------------

    async def _set_status(self, new_status: ExecutionStatus) -> None:
        """Update status and broadcast the change."""
        old = self._status
        self._status = new_status
        logger.info(
            "Session %s status: %s -> %s",
            self._session_id,
            old.value,
            new_status.value,
        )
        await self._broadcast("status_change", {"status": new_status.value})

    # -- Public control methods ---------------------------------------------

    async def start(
        self,
        project_id: str,
        step_ids: list[str],
        model: str = "claude-opus-4-6",
    ) -> None:
        """
        Launch the computer-use agent session.

        1. Starts a Docker container (or mock if Docker unavailable).
        2. Creates a CaptureManager for screen recording.
        3. Kicks off the agent loop as a background task.
        """
        if self._status not in (ExecutionStatus.IDLE, ExecutionStatus.COMPLETED, ExecutionStatus.ERROR):
            raise RuntimeError(f"Cannot start session in state '{self._status.value}'")

        self._project_id = project_id
        self._step_ids = list(step_ids)
        self._model = model
        self._current_step = 0
        self._total_steps = len(step_ids)
        self._stop_requested = False
        self._takeover_mode = False
        self._pause_event.set()

        # Start the Docker container
        docker = get_docker_manager()
        docker.start_container(self._session_id)
        self._novnc_url = docker.get_novnc_url(self._session_id)

        # Create the capture manager for screen recording
        captures_dir = f".autoforge/yt-lab/{project_id}/captures/{self._session_id}"
        create_capture_manager(
            session_id=self._session_id,
            project_id=project_id,
            captures_base_dir=captures_dir,
        )

        await self._set_status(ExecutionStatus.RUNNING)

        # Launch the agent loop in the background
        self._agent_task = asyncio.create_task(self._agent_loop())

    async def pause(self) -> None:
        """Pause the agent after the current tool call completes."""
        if self._status != ExecutionStatus.RUNNING:
            raise RuntimeError(f"Cannot pause session in state '{self._status.value}'")

        self._pause_event.clear()
        await self._set_status(ExecutionStatus.PAUSED)

    async def resume(self) -> None:
        """Resume a paused or takeover session."""
        if self._status not in (ExecutionStatus.PAUSED, ExecutionStatus.TAKEOVER):
            raise RuntimeError(f"Cannot resume session in state '{self._status.value}'")

        self._takeover_mode = False
        self._pause_event.set()
        await self._set_status(ExecutionStatus.RUNNING)

    async def stop(self) -> None:
        """Terminate the agent session and clean up resources."""
        self._stop_requested = True
        self._pause_event.set()  # Unblock if paused so the loop can exit

        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()
            try:
                await self._agent_task
            except asyncio.CancelledError:
                pass

        # Clean up Docker container and capture manager
        docker = get_docker_manager()
        docker.stop_container(self._session_id)
        remove_capture_manager(self._session_id)

        if self._status not in (ExecutionStatus.COMPLETED, ExecutionStatus.ERROR):
            await self._set_status(ExecutionStatus.COMPLETED)

    async def inject_message(self, message: str) -> None:
        """Add a user message to the agent conversation."""
        await self._injected_messages.put(message)
        await self._broadcast("user_message", {"content": message})

    async def set_takeover(self, enable: bool) -> None:
        """Toggle takeover mode (human takes control of the browser)."""
        self._takeover_mode = enable
        if enable:
            self._pause_event.clear()
            await self._set_status(ExecutionStatus.TAKEOVER)
        else:
            self._pause_event.set()
            await self._set_status(ExecutionStatus.RUNNING)

    async def jump_to_step(self, step_id: str) -> None:
        """Advance execution to a specific step by ID."""
        if step_id not in self._step_ids:
            raise ValueError(f"Step '{step_id}' not found in session steps")

        target_index = self._step_ids.index(step_id)
        self._current_step = target_index
        await self._broadcast(
            "step_change",
            {
                "step_id": step_id,
                "step_status": "in_progress",
                "current_step": self._current_step + 1,
                "total_steps": self._total_steps,
            },
        )

    # -- Agent loop ---------------------------------------------------------

    async def _agent_loop(self) -> None:
        """
        Main agent execution loop.

        Iterates through each step, broadcasting events as it progresses.
        The actual Claude computer-use API integration would replace the
        simulated work inside _execute_step. The loop respects pause/resume
        and stop signals between steps.
        """
        try:
            while self._current_step < self._total_steps:
                if self._stop_requested:
                    break

                # Wait if paused or in takeover mode
                await self._pause_event.wait()

                if self._stop_requested:
                    break

                step_id = self._step_ids[self._current_step]

                # Broadcast step start
                await self._broadcast(
                    "step_change",
                    {
                        "step_id": step_id,
                        "step_status": "in_progress",
                        "current_step": self._current_step + 1,
                        "total_steps": self._total_steps,
                    },
                )

                await self._broadcast(
                    "agent_action",
                    {
                        "description": f"Working on step: {step_id}",
                    },
                )

                # Execute the step (this is where computer-use API calls go)
                try:
                    await self._execute_step(step_id)
                except Exception as exc:
                    logger.error(
                        "Step %s failed in session %s: %s",
                        step_id,
                        self._session_id,
                        exc,
                    )
                    await self._broadcast("error", {"message": f"Step '{step_id}' failed: {exc}"})
                    await self._set_status(ExecutionStatus.ERROR)
                    return

                # Drain any injected messages between steps
                while not self._injected_messages.empty():
                    try:
                        msg = self._injected_messages.get_nowait()
                        await self._broadcast(
                            "agent_response",
                            {
                                "content": f"Acknowledged: {msg}",
                            },
                        )
                    except asyncio.QueueEmpty:
                        break

                # Mark step complete
                await self._broadcast(
                    "step_change",
                    {
                        "step_id": step_id,
                        "step_status": "complete",
                        "current_step": self._current_step + 1,
                        "total_steps": self._total_steps,
                    },
                )

                self._current_step += 1

            # All steps completed
            if not self._stop_requested:
                await self._set_status(ExecutionStatus.COMPLETED)

        except asyncio.CancelledError:
            logger.info("Agent loop cancelled for session %s", self._session_id)
        except Exception as exc:
            logger.exception("Unexpected error in agent loop for session %s", self._session_id)
            await self._broadcast("error", {"message": str(exc)})
            await self._set_status(ExecutionStatus.ERROR)

    async def _execute_step(self, step_id: str) -> None:
        """
        Execute a single strategy step.

        In production this would invoke the Claude computer-use API to
        perform browser actions. Currently provides a structured placeholder
        that broadcasts thinking events and simulates a short delay so the
        rest of the system (WebSocket viewers, capture manager, etc.) can
        be tested end-to-end.
        """
        await self._broadcast(
            "agent_thinking",
            {
                "content": f"Analyzing step '{step_id}' and planning actions...",
            },
        )

        # Placeholder delay -- replace with actual computer-use API calls
        await asyncio.sleep(1)

        await self._broadcast(
            "agent_thinking",
            {
                "content": f"Executing actions for step '{step_id}'...",
            },
        )

        await asyncio.sleep(1)


# ---------------------------------------------------------------------------
# Module-level session registry
# ---------------------------------------------------------------------------

_sessions: dict[str, ComputerUseAgent] = {}


def get_session(session_id: str) -> Optional[ComputerUseAgent]:
    """Retrieve an active execution session by ID."""
    return _sessions.get(session_id)


def create_session() -> ComputerUseAgent:
    """Create a new execution session with a unique ID."""
    session_id = uuid.uuid4().hex
    agent = ComputerUseAgent(session_id)
    _sessions[session_id] = agent
    logger.info("Execution session created: %s", session_id)
    return agent


def remove_session(session_id: str) -> None:
    """Remove a session from the registry."""
    removed = _sessions.pop(session_id, None)
    if removed:
        logger.info("Execution session removed: %s", session_id)


async def cleanup_all_sessions() -> None:
    """Stop all active sessions and clear the registry. Called during shutdown."""
    for session_id in list(_sessions.keys()):
        session = _sessions.get(session_id)
        if session:
            try:
                await session.stop()
            except Exception as exc:
                logger.warning("Error stopping session %s during cleanup: %s", session_id, exc)
    _sessions.clear()
    logger.info("All execution sessions cleaned up")
