"""
Background Session Manager
===========================

Decouples AI chat sessions from WebSocket connections, allowing sessions to
run as independent background asyncio tasks.  Viewers (WebSocket connections)
can attach and detach freely without interrupting a running session.

Architecture:
    BackgroundSession — wraps a WorkspaceChatSession, runs it as a background
        asyncio.Task, buffers all output events in a ring buffer (with SQLite
        persistence), and broadcasts events to zero-or-more connected viewers.

    OutputBuffer — in-memory ring buffer (deque) with monotonic sequence
        numbers.  Supports catch-up replay via ``get_since(seq)`` and batch
        persistence to the ``workspace_session_events`` table.

    BackgroundSessionManager — singleton that manages all BackgroundSession
        instances, enforces concurrency limits, maps conversation IDs to
        active sessions, and auto-cleans completed sessions after 1 hour.

Key design decisions:
    - Sessions are NOT tied to WebSocket lifetimes.  A session continues
      running even when zero viewers are connected.
    - Output is buffered so late-joining viewers can catch up via sequence
      numbers without re-running the session.
    - Events are persisted to SQLite in batches (every 50 events or 5 seconds)
      for durability without per-event write overhead.
    - The manager is a process-wide singleton, accessed via
      ``get_background_session_manager()``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import WebSocket

from .workspace_chat_session import WorkspaceChatSession
from .workspace_database import (
    WorkspaceSessionEvent,
    get_db_session,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum events kept in the in-memory ring buffer per session.
# Older events are evicted from memory but remain in SQLite.
OUTPUT_BUFFER_MAX_SIZE = 2000

# Batch persistence thresholds: flush to SQLite every N events or M seconds.
PERSIST_BATCH_SIZE = 50
PERSIST_INTERVAL_SECONDS = 5.0

# How often the background session sends a heartbeat to connected viewers.
HEARTBEAT_INTERVAL_SECONDS = 10.0

# Sessions in terminal states are removed from memory after this duration.
CLEANUP_AGE_SECONDS = 3600  # 1 hour

# Maximum concurrent background sessions allowed.
MAX_CONCURRENT_SESSIONS = 10


# ---------------------------------------------------------------------------
# SessionState
# ---------------------------------------------------------------------------

class SessionState(str, Enum):
    """Lifecycle states for a background AI session.

    State transitions::

        QUEUED -> RUNNING -> STREAMING -> COMPLETED
                          |-> STREAMING -> WAITING_INPUT -> STREAMING ...
                          |-> FAILED
        (any) -> CANCELLED
    """
    QUEUED = "queued"
    RUNNING = "running"
    STREAMING = "streaming"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _is_terminal(state: SessionState) -> bool:
    """Return True if the state is a terminal (final) state."""
    return state in (SessionState.COMPLETED, SessionState.FAILED, SessionState.CANCELLED)


# ---------------------------------------------------------------------------
# OutputBuffer
# ---------------------------------------------------------------------------

class OutputBuffer:
    """Coroutine-safe ring buffer with monotonic sequence numbers and SQLite persistence.

    Every event appended to the buffer receives a monotonically increasing
    sequence number.  Viewers use ``get_since(seq)`` to retrieve events they
    haven't seen yet (catch-up replay).

    Events are also accumulated in ``_pending_persist`` and flushed to the
    ``workspace_session_events`` table in batches for durability.
    """

    def __init__(self, session_id: str, conversation_id: Optional[int]) -> None:
        self._session_id = session_id
        self._conversation_id = conversation_id

        # In-memory ring buffer.  Each entry is (sequence, event_dict).
        self._buffer: deque[tuple[int, dict[str, Any]]] = deque(maxlen=OUTPUT_BUFFER_MAX_SIZE)

        # Monotonic sequence counter (starts at 0, first event is seq=1).
        self._sequence: int = 0

        # Pending events awaiting batch persistence.
        self._pending_persist: list[tuple[int, dict[str, Any]]] = []
        self._last_flush_time: float = time.monotonic()

        # Lock protects _buffer, _sequence, and _pending_persist.
        self._lock = asyncio.Lock()

    @property
    def current_sequence(self) -> int:
        """The sequence number of the most recently appended event (0 if empty)."""
        return self._sequence

    async def append(self, event: dict[str, Any]) -> int:
        """Append an event to the buffer.

        Args:
            event: The event dict to append (must contain a ``type`` key).

        Returns:
            The sequence number assigned to this event.
        """
        async with self._lock:
            self._sequence += 1
            seq = self._sequence
            self._buffer.append((seq, event))
            self._pending_persist.append((seq, event))

        # Check if we should flush to SQLite (outside the lock to avoid
        # holding it during I/O).
        await self._maybe_flush()
        return seq

    async def get_since(self, after_seq: int) -> list[tuple[int, dict[str, Any]]]:
        """Return all events with sequence numbers greater than ``after_seq``.

        This is the primary catch-up mechanism: a reconnecting viewer provides
        the last sequence number it received, and this method returns everything
        it missed.

        Args:
            after_seq: Return events with sequence > this value.

        Returns:
            List of (sequence, event_dict) tuples in order.
        """
        async with self._lock:
            return [(seq, ev) for seq, ev in self._buffer if seq > after_seq]

    async def flush(self) -> None:
        """Force-flush all pending events to SQLite.

        Called at session completion to ensure no events are lost.
        Skips flushing if conversation_id is not yet set (events remain
        in _pending_persist for a future flush once the ID is available).
        """
        async with self._lock:
            if self._conversation_id is None:
                logger.debug(
                    "Skipping flush for session %s (conversation_id not yet set, %d events pending)",
                    self._session_id, len(self._pending_persist),
                )
                return
            batch = list(self._pending_persist)
            self._pending_persist.clear()
            self._last_flush_time = time.monotonic()

        if batch:
            await self._persist_batch(batch)

    async def _maybe_flush(self) -> None:
        """Flush pending events if batch size or time threshold is met."""
        async with self._lock:
            # Don't flush if conversation_id is not yet set — events stay in
            # _pending_persist until the conversation is created, preventing
            # permanent data loss.
            if self._conversation_id is None:
                return
            should_flush = (
                len(self._pending_persist) >= PERSIST_BATCH_SIZE
                or (time.monotonic() - self._last_flush_time) >= PERSIST_INTERVAL_SECONDS
            )
            if not should_flush:
                return
            batch = list(self._pending_persist)
            self._pending_persist.clear()
            self._last_flush_time = time.monotonic()

        if batch:
            await self._persist_batch(batch)

    async def _persist_batch(self, batch: list[tuple[int, dict[str, Any]]]) -> None:
        """Write a batch of events to the ``workspace_session_events`` table.

        Runs the blocking SQLAlchemy I/O in a thread executor to avoid
        blocking the event loop.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._persist_batch_sync, batch)

    def _persist_batch_sync(self, batch: list[tuple[int, dict[str, Any]]]) -> None:
        """Synchronous batch insert into SQLite (runs in a thread)."""
        # Skip persistence if conversation_id is not yet known (new conversations
        # set it when the conversation_created event fires).  The events remain
        # in the in-memory ring buffer for replay and will be persisted once the
        # conversation_id is available on the next flush cycle.
        if self._conversation_id is None:
            logger.debug(
                "Skipping persistence of %d events for session %s (conversation_id not yet set)",
                len(batch), self._session_id,
            )
            return

        db_session = get_db_session()
        try:
            for seq, event in batch:
                event_type = event.get("type", "unknown")
                event_data = json.dumps(event, default=str)
                db_session.add(WorkspaceSessionEvent(
                    session_id=self._session_id,
                    conversation_id=self._conversation_id,
                    sequence=seq,
                    event_type=event_type,
                    event_data=event_data,
                ))
            db_session.commit()
            logger.debug(
                "Persisted %d events for session %s (seq %d-%d)",
                len(batch), self._session_id,
                batch[0][0], batch[-1][0],
            )
        except Exception as e:
            logger.error("Failed to persist event batch for session %s: %s", self._session_id, e)
            db_session.rollback()
        finally:
            db_session.close()


# ---------------------------------------------------------------------------
# BackgroundSession
# ---------------------------------------------------------------------------

class BackgroundSession:
    """An independent background AI session decoupled from any WebSocket.

    Wraps a ``WorkspaceChatSession`` and runs it as an asyncio background task.
    Output events are buffered and broadcast to connected viewers in real time.
    Viewers can attach/detach without affecting session lifecycle.
    """

    def __init__(
        self,
        *,
        session_id: str,
        conversation_id: Optional[int],
        provider: str = "claude",
        model: str = "opus",
        working_directory: Optional[str] = None,
        context_mode: str = "1m",
        cost_settings: Optional[dict[str, Any]] = None,
        manager: Optional["BackgroundSessionManager"] = None,
    ) -> None:
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.provider = provider
        self.model = model
        self.working_directory = working_directory
        self.context_mode = context_mode
        self.cost_settings = cost_settings

        self.state = SessionState.QUEUED
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

        self._output_buffer = OutputBuffer(session_id, conversation_id)
        self._viewers: set[WebSocket] = set()
        self._input_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None
        self._chat_session: Optional[WorkspaceChatSession] = None
        self._manager = manager

        # Lock for viewer set mutations.
        self._viewer_lock = asyncio.Lock()

    # ----- Public API -----

    async def start(self) -> None:
        """Create the underlying WorkspaceChatSession and launch the background task.

        This method transitions the session from QUEUED to RUNNING and starts
        the ``_run()`` coroutine as a background asyncio.Task.

        Raises:
            RuntimeError: If the session has already been started.
        """
        if self._task is not None:
            raise RuntimeError(f"Session {self.session_id} is already started")

        self.state = SessionState.RUNNING
        self.started_at = datetime.now(timezone.utc)

        # Create the underlying workspace chat session.  We generate a unique
        # internal session_id for the WorkspaceChatSession registry (prefixed
        # with "bg-" to distinguish from direct WebSocket sessions).
        internal_session_id = f"bg-{self.session_id}"
        self._chat_session = WorkspaceChatSession(
            session_id=internal_session_id,
            conversation_id=self.conversation_id,
            working_directory=self.working_directory,
            context_mode=self.context_mode,
            cost_settings=self.cost_settings,
            model=self.model,
            provider=self.provider,
        )

        # Launch the background run loop.
        self._task = asyncio.create_task(
            self._run(),
            name=f"bg-session-{self.session_id}",
        )

    async def submit_message(
        self,
        message: str,
        *,
        attachments: Any = None,
        library_file_ids: Optional[list[int]] = None,
    ) -> int:
        """Submit a user message to the running session.

        The message is placed in the input queue and will be picked up by the
        background ``_run()`` loop.  Also appends a ``user_message`` event to
        the output buffer so viewers see what the user sent.

        Args:
            message: The user's message text.
            attachments: Optional list of ImageAttachment objects.
            library_file_ids: Optional list of library file IDs to include.

        Returns:
            The sequence number of the ``user_message`` event in the output buffer.

        Raises:
            RuntimeError: If the session is in a terminal state.
        """
        if _is_terminal(self.state):
            raise RuntimeError(
                f"Cannot submit message to session {self.session_id} in state {self.state.value}"
            )

        msg_data: dict[str, Any] = {"content": message}
        if attachments:
            msg_data["attachments"] = attachments
        if library_file_ids:
            msg_data["library_file_ids"] = library_file_ids
        await self._input_queue.put(msg_data)

        # Record the user message as a buffer event so viewers see it.
        seq = await self._output_buffer.append({
            "type": "user_message",
            "content": message,
        })
        await self._broadcast({
            "type": "user_message",
            "content": message,
            "seq": seq,
        })
        return seq

    async def attach_viewer(self, ws: WebSocket) -> int:
        """Register a WebSocket as a viewer of this session.

        The viewer will receive all future events via broadcast.  Returns the
        current buffer sequence number so the viewer can call ``get_since()``
        for catch-up replay.

        Args:
            ws: The WebSocket connection to attach.

        Returns:
            The current output buffer sequence number.
        """
        async with self._viewer_lock:
            self._viewers.add(ws)
        logger.info(
            "Viewer attached to session %s (total viewers: %d)",
            self.session_id, len(self._viewers),
        )
        return self._output_buffer.current_sequence

    async def detach_viewer(self, ws: WebSocket) -> None:
        """Remove a WebSocket viewer.  The session continues running.

        Args:
            ws: The WebSocket connection to detach.
        """
        async with self._viewer_lock:
            self._viewers.discard(ws)
        logger.info(
            "Viewer detached from session %s (remaining viewers: %d)",
            self.session_id, len(self._viewers),
        )

    async def get_events_since(self, after_seq: int) -> list[tuple[int, dict[str, Any]]]:
        """Retrieve buffered events after the given sequence number (catch-up replay).

        Args:
            after_seq: Return events with sequence > this value.

        Returns:
            List of (sequence, event_dict) tuples.
        """
        return await self._output_buffer.get_since(after_seq)

    async def cancel(self) -> None:
        """Cancel the running session.

        Transitions to CANCELLED state, cancels the background task, and
        closes the underlying chat session.
        """
        if _is_terminal(self.state):
            return

        self.state = SessionState.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

        if self._task and not self._task.done():
            # Cancel the background task — its finally block will close the
            # chat session and flush the output buffer, so we must NOT close
            # the chat session again here (double-close bug).
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        else:
            # Task was never started or already finished — close directly
            # since _run()'s finally block won't run.
            if self._chat_session:
                try:
                    await self._chat_session.close()
                except Exception as e:
                    logger.warning("Error closing chat session during cancel: %s", e)
            await self._output_buffer.flush()

        # Notify viewers of cancellation.
        cancel_event: dict[str, Any] = {"type": "session_cancelled", "session_id": self.session_id}
        seq = await self._output_buffer.append(cancel_event)
        cancel_event["seq"] = seq
        await self._broadcast(cancel_event)
        await self._output_buffer.flush()

    def to_status_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable status summary of this session."""
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "provider": self.provider,
            "model": self.model,
            "working_directory": self.working_directory,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "viewer_count": len(self._viewers),
            "buffer_sequence": self._output_buffer.current_sequence,
        }

    # ----- Background run loop -----

    async def _run(self) -> None:
        """Background coroutine: initialize the session, process messages, stream output.

        This is the main loop that runs as an asyncio.Task.  It:
        1. Calls ``start()`` on the underlying WorkspaceChatSession.
        2. Waits for user messages in the input queue.
        3. Streams the AI response, buffering and broadcasting each event.
        4. Sends periodic heartbeats to connected viewers.
        5. Handles errors gracefully (marks session as FAILED, never crashes).
        """
        assert self._chat_session is not None

        heartbeat_task: Optional[asyncio.Task[None]] = None

        try:
            # Phase 1: Initialize the underlying session (start the AI client).
            self.state = SessionState.RUNNING
            await self._emit_state_event()

            async for event in self._chat_session.start():
                # Track conversation_id for new conversations.
                if (
                    event.get("type") == "conversation_created"
                    and self.conversation_id is None
                ):
                    new_conv_id = event.get("conversation_id")
                    if new_conv_id is not None:
                        self.conversation_id = new_conv_id
                        self._output_buffer._conversation_id = new_conv_id
                        # Update the manager's reverse index.
                        if self._manager is not None:
                            async with self._manager._lock:
                                self._manager._conversation_sessions[new_conv_id] = self.session_id
                await self._buffer_and_broadcast(event)

            # Start the heartbeat loop.
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(),
                name=f"bg-heartbeat-{self.session_id}",
            )

            # Phase 2: Message processing loop — wait for user input, stream responses.
            while not _is_terminal(self.state):
                self.state = SessionState.WAITING_INPUT
                await self._emit_state_event()

                # Wait for a user message (structured dict with content + optional attachments).
                try:
                    msg_data = await self._input_queue.get()
                except asyncio.CancelledError:
                    raise

                # Unpack structured message data.
                if isinstance(msg_data, dict):
                    msg_content = msg_data.get("content", "")
                    msg_attachments = msg_data.get("attachments")
                    msg_library_file_ids = msg_data.get("library_file_ids")
                else:
                    # Backward compat: plain string
                    msg_content = str(msg_data)
                    msg_attachments = None
                    msg_library_file_ids = None

                # Transition to streaming.
                self.state = SessionState.STREAMING
                await self._emit_state_event()

                # Stream the AI response.
                async for event in self._chat_session.send_message(
                    msg_content,
                    attachments=msg_attachments,
                    library_file_ids=msg_library_file_ids,
                ):
                    await self._buffer_and_broadcast(event)

            # If we exit the loop normally (shouldn't happen unless state was
            # set externally), mark completed.
            if not _is_terminal(self.state):
                self.state = SessionState.COMPLETED
                self.completed_at = datetime.now(timezone.utc)

        except asyncio.CancelledError:
            # Session was cancelled via cancel() — state already set.
            logger.info("Background session %s cancelled", self.session_id)

        except Exception as e:
            logger.exception("Background session %s failed", self.session_id)
            self.state = SessionState.FAILED
            self.completed_at = datetime.now(timezone.utc)
            self.error_message = str(e)

            # Emit an error event so viewers see what happened.
            # Wrap in try/except: if _buffer_and_broadcast itself raised the
            # original exception, calling it again here would fail too.
            try:
                await self._buffer_and_broadcast({
                    "type": "error",
                    "content": f"Session failed: {e}",
                })
                await self._emit_state_event()
            except Exception:
                logger.warning(
                    "Failed to broadcast error event for session %s", self.session_id,
                )

        finally:
            # Stop heartbeat.
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Flush all remaining events to SQLite.
            try:
                await self._output_buffer.flush()
            except Exception:
                logger.warning(
                    "Failed to flush output buffer for session %s", self.session_id,
                )

            # Close the underlying chat session.
            if self._chat_session:
                try:
                    await self._chat_session.close()
                except Exception as e:
                    logger.warning(
                        "Error closing chat session in background run (session %s): %s",
                        self.session_id, e,
                    )

            logger.info(
                "Background session %s ended in state %s",
                self.session_id, self.state.value,
            )

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat events to connected viewers.

        Heartbeats keep WebSocket connections alive and let the UI show
        that the session is still active (especially during long tool calls
        where no text output is produced).
        """
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                heartbeat: dict[str, Any] = {
                    "type": "heartbeat",
                    "session_id": self.session_id,
                    "state": self.state.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "viewer_count": len(self._viewers),
                    "seq": self._output_buffer.current_sequence,
                }
                # Heartbeats are broadcast directly (not buffered) to avoid
                # filling the output buffer with noise.
                await self._broadcast(heartbeat)
        except asyncio.CancelledError:
            pass

    async def _buffer_and_broadcast(self, event: dict[str, Any]) -> None:
        """Append an event to the output buffer and broadcast to all viewers.

        Args:
            event: The event dict to buffer and broadcast.
        """
        seq = await self._output_buffer.append(event)
        # Add the sequence number to the broadcast copy so viewers can track position.
        broadcast_event = {**event, "seq": seq}
        # Diagnostic: log token_log broadcasts to confirm backend is emitting them
        if event.get("type") == "token_log":
            logger.info(
                "token_log broadcast: seq=%d viewers=%d entry_type=%s",
                seq, len(self._viewers), event.get("entry", {}).get("event_type", "?"),
            )
        await self._broadcast(broadcast_event)

    async def _emit_state_event(self) -> None:
        """Emit a ``session_state`` event reflecting the current session state."""
        await self._buffer_and_broadcast({
            "type": "session_state",
            "session_id": self.session_id,
            "state": self.state.value,
        })

    async def _broadcast(self, event: dict[str, Any]) -> None:
        """Send an event to all connected viewers.

        Failed sends (disconnected viewers) are silently removed from the
        viewer set to avoid accumulating dead connections.

        Args:
            event: The event dict to send as JSON.
        """
        async with self._viewer_lock:
            viewers = set(self._viewers)

        if not viewers:
            return

        dead_viewers: list[WebSocket] = []
        message = json.dumps(event, default=str)

        for ws in viewers:
            try:
                await ws.send_text(message)
            except Exception:
                # WebSocket is likely disconnected — mark for removal.
                dead_viewers.append(ws)

        # Remove dead viewers outside the broadcast loop.
        if dead_viewers:
            async with self._viewer_lock:
                for ws in dead_viewers:
                    self._viewers.discard(ws)
            logger.debug(
                "Removed %d dead viewer(s) from session %s",
                len(dead_viewers), self.session_id,
            )


# ---------------------------------------------------------------------------
# BackgroundSessionManager (Singleton)
# ---------------------------------------------------------------------------

class BackgroundSessionManager:
    """Process-wide manager for all background AI sessions.

    Provides creation, lookup, cancellation, viewer attachment, and
    automatic cleanup of completed sessions.  Thread-safe with asyncio locks.
    """

    def __init__(self, max_concurrent: int = MAX_CONCURRENT_SESSIONS) -> None:
        # Active sessions keyed by session_id.
        self._sessions: dict[str, BackgroundSession] = {}

        # Reverse index: conversation_id -> active session_id.
        # Only sessions in non-terminal states are tracked here.
        self._conversation_sessions: dict[int, str] = {}

        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Start the manager's periodic cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(
                self._cleanup_loop(),
                name="bg-session-cleanup",
            )
            logger.info("BackgroundSessionManager started (max_concurrent=%d)", self._max_concurrent)

    async def stop(self) -> None:
        """Stop the manager: cancel all sessions and the cleanup task."""
        # Cancel all active sessions.
        async with self._lock:
            session_ids = list(self._sessions.keys())

        for sid in session_ids:
            try:
                await self.cancel_session(sid)
            except Exception as e:
                logger.warning("Error cancelling session %s during shutdown: %s", sid, e)

        # Stop the cleanup loop.
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        logger.info("BackgroundSessionManager stopped")

    async def create_session(
        self,
        conversation_id: Optional[int] = None,
        provider: str = "claude",
        model: str = "opus",
        working_directory: Optional[str] = None,
        context_mode: str = "1m",
        cost_settings: Optional[dict[str, Any]] = None,
    ) -> BackgroundSession:
        """Create and start a new background session.

        Args:
            conversation_id: The workspace conversation ID to associate with.
                Pass None for new conversations (the underlying session will
                create one and broadcast a ``conversation_created`` event).
            provider: AI provider (``"claude"``, ``"codex"``, ``"gemini"``).
            model: Model shorthand (``"opus"``, ``"sonnet"``).
            working_directory: Absolute path for the session's working directory.
            context_mode: Context window mode (``"1m"`` or ``"200k"``).
            cost_settings: Optional cost control overrides.

        Returns:
            The newly created and started BackgroundSession.

        Raises:
            RuntimeError: If the concurrency limit is reached or the
                conversation already has an active session.
        """
        async with self._lock:
            # Enforce concurrency limit (count only non-terminal sessions).
            active_count = sum(
                1 for s in self._sessions.values()
                if not _is_terminal(s.state)
            )
            if active_count >= self._max_concurrent:
                raise RuntimeError(
                    f"Maximum concurrent sessions ({self._max_concurrent}) reached. "
                    f"Cancel an existing session first."
                )

            # Check if the conversation already has an active session.
            if conversation_id is not None:
                existing_sid = self._conversation_sessions.get(conversation_id)
                if existing_sid and existing_sid in self._sessions:
                    existing = self._sessions[existing_sid]
                    if not _is_terminal(existing.state):
                        raise RuntimeError(
                            f"Conversation {conversation_id} already has an active session "
                            f"({existing_sid}, state={existing.state.value}). "
                            f"Cancel it first."
                        )

            # Generate a unique session ID.
            session_id = str(uuid.uuid4())

            session = BackgroundSession(
                session_id=session_id,
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                working_directory=working_directory,
                context_mode=context_mode,
                cost_settings=cost_settings,
                manager=self,
            )

            self._sessions[session_id] = session
            if conversation_id is not None:
                self._conversation_sessions[conversation_id] = session_id

        # Start the session outside the lock to avoid holding it during
        # potentially slow initialization.  If start() fails, clean up the
        # registration so the conversation isn't permanently blocked.
        try:
            await session.start()
        except Exception:
            async with self._lock:
                self._sessions.pop(session_id, None)
                if self._conversation_sessions.get(conversation_id) == session_id:
                    del self._conversation_sessions[conversation_id]
            raise

        logger.info(
            "Created background session %s for conversation %s (provider=%s, model=%s)",
            session_id, conversation_id, provider, model,
        )
        return session

    async def cancel_session(self, session_id: str) -> None:
        """Cancel a running background session.

        Args:
            session_id: The session to cancel.

        Raises:
            KeyError: If no session exists with the given ID.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"No session found with ID {session_id}")

        await session.cancel()

        # Update the reverse index.
        async with self._lock:
            conv_id = session.conversation_id
            if self._conversation_sessions.get(conv_id) == session_id:
                del self._conversation_sessions[conv_id]

        logger.info("Cancelled background session %s", session_id)

    def get_session(self, session_id: str) -> Optional[BackgroundSession]:
        """Get a session by its ID (non-async, lock-free read).

        Args:
            session_id: The session to look up.

        Returns:
            The BackgroundSession, or None if not found.
        """
        return self._sessions.get(session_id)

    def get_session_for_conversation(self, conversation_id: int) -> Optional[BackgroundSession]:
        """Get the active session for a conversation (non-async, lock-free read).

        Args:
            conversation_id: The conversation to look up.

        Returns:
            The active BackgroundSession, or None if no active session exists.
        """
        session_id = self._conversation_sessions.get(conversation_id)
        if session_id is None:
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        # Only return non-terminal sessions.
        if _is_terminal(session.state):
            return None
        return session

    def list_sessions(self, include_completed: bool = False) -> list[dict[str, Any]]:
        """List all sessions as status dicts.

        Args:
            include_completed: If True, include sessions in terminal states.
                If False (default), only active sessions are returned.

        Returns:
            List of session status dicts (see ``BackgroundSession.to_status_dict``).
        """
        results: list[dict[str, Any]] = []
        for session in self._sessions.values():
            if not include_completed and _is_terminal(session.state):
                continue
            results.append(session.to_status_dict())
        return results

    async def submit_message(
        self,
        session_id: str,
        message: str,
        *,
        attachments: Any = None,
        library_file_ids: Optional[list[int]] = None,
    ) -> int:
        """Submit a user message to a running session.

        Args:
            session_id: The session to send the message to.
            message: The user's message text.
            attachments: Optional list of ImageAttachment objects.
            library_file_ids: Optional list of library file IDs.

        Returns:
            The sequence number of the ``user_message`` event.

        Raises:
            KeyError: If no session exists with the given ID.
            RuntimeError: If the session is in a terminal state.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"No session found with ID {session_id}")
        return await session.submit_message(
            message, attachments=attachments, library_file_ids=library_file_ids,
        )

    async def attach_viewer(self, session_id: str, ws: WebSocket) -> int:
        """Attach a WebSocket viewer to a session.

        Args:
            session_id: The session to attach to.
            ws: The WebSocket connection.

        Returns:
            The current buffer sequence number (for catch-up replay).

        Raises:
            KeyError: If no session exists with the given ID.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"No session found with ID {session_id}")
        return await session.attach_viewer(ws)

    async def detach_viewer(self, session_id: str, ws: WebSocket) -> None:
        """Detach a WebSocket viewer from a session.

        Args:
            session_id: The session to detach from.
            ws: The WebSocket connection.

        Raises:
            KeyError: If no session exists with the given ID.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"No session found with ID {session_id}")
        await session.detach_viewer(ws)

    async def _cleanup_loop(self) -> None:
        """Periodically remove old completed/failed/cancelled sessions from memory.

        Sessions in terminal states are removed after ``CLEANUP_AGE_SECONDS``
        (1 hour by default).  Their events remain in SQLite for historical access.
        """
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute.
                await self._cleanup_completed()
        except asyncio.CancelledError:
            pass

    async def _cleanup_completed(self) -> None:
        """Remove sessions in terminal states that are older than the cleanup threshold."""
        now = datetime.now(timezone.utc)
        to_remove: list[str] = []

        async with self._lock:
            for sid, session in self._sessions.items():
                if not _is_terminal(session.state):
                    continue
                if session.completed_at is None:
                    continue
                age = (now - session.completed_at).total_seconds()
                if age > CLEANUP_AGE_SECONDS:
                    to_remove.append(sid)

            for sid in to_remove:
                removed = self._sessions.pop(sid)
                conv_id = removed.conversation_id
                if self._conversation_sessions.get(conv_id) == sid:
                    del self._conversation_sessions[conv_id]

        if to_remove:
            logger.info(
                "Cleaned up %d completed background session(s): %s",
                len(to_remove), to_remove,
            )


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_manager_instance: Optional[BackgroundSessionManager] = None
_manager_lock = asyncio.Lock()


async def get_background_session_manager() -> BackgroundSessionManager:
    """Get or create the process-wide BackgroundSessionManager singleton.

    The manager is lazily initialized on first access and its cleanup task
    is started automatically.

    Returns:
        The singleton BackgroundSessionManager instance.
    """
    global _manager_instance

    if _manager_instance is not None:
        return _manager_instance

    async with _manager_lock:
        # Double-checked locking: another coroutine may have initialized
        # the manager while we were waiting for the lock.
        if _manager_instance is not None:
            return _manager_instance

        _manager_instance = BackgroundSessionManager()
        await _manager_instance.start()
        return _manager_instance


async def cleanup_background_sessions() -> None:
    """Shutdown the background session manager if it was initialized.

    Cancels all active sessions and stops the cleanup loop.
    Safe to call even if the manager was never created.
    """
    global _manager_instance
    if _manager_instance is not None:
        await _manager_instance.stop()
        _manager_instance = None
        logger.info("Background session manager cleaned up")
