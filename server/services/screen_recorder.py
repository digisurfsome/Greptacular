"""
Screen Recorder Service
=======================

Captures screenshots, short video clips, and full session recordings from
an X11 virtual display inside a Docker container. Used during computer-use
execution to document agent actions.

Capture Types:
  - Screenshots: single frame via xdotool/import
  - Short clips (3-10s): ffmpeg x11grab around key moments
  - Full session recording: long-running ffmpeg subprocess (opt-in)

Storage:
  .autoforge/yt-lab/{project_id}/captures/step-{N}/
"""

import logging
import os
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DISPLAY_WIDTH = 1920
DEFAULT_DISPLAY_HEIGHT = 1080
DEFAULT_CLIP_FPS = 15
DEFAULT_SESSION_FPS = 10
DEFAULT_CLIP_CRF = 28
DEFAULT_SESSION_CRF = 30
FFMPEG_PRESET = "ultrafast"
FFMPEG_CODEC = "libx264"

# Maximum timeout buffer added to clip duration for subprocess
CLIP_TIMEOUT_BUFFER = 10


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class CaptureType(str, Enum):
    SCREENSHOT = "screenshot"
    CLIP = "clip"
    SESSION = "session"


class CaptureTrigger(str, Enum):
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    BUTTON_CLICK = "button_click"
    FORM_FILL = "form_fill"
    NAVIGATION = "navigation"
    USER_PAUSE = "user_pause"
    ERROR = "error"
    MANUAL = "manual"


@dataclass
class CaptureRecord:
    """Metadata for a single capture (screenshot or clip)."""

    id: str
    session_id: str
    step_number: int
    capture_type: CaptureType
    trigger: CaptureTrigger
    file_path: str
    filename: str
    duration: Optional[float] = None  # seconds, for clips/sessions
    timestamp: float = 0.0  # time since session start
    created_at: str = ""
    status: str = "ready"  # "ready" or "capturing" (for async clips)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_number": self.step_number,
            "capture_type": self.capture_type.value,
            "trigger": self.trigger.value,
            "file_path": self.file_path,
            "filename": self.filename,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "status": self.status,
        }


# ---------------------------------------------------------------------------
# Screenshot Capture
# ---------------------------------------------------------------------------


def capture_screenshot(
    display_number: int,
    output_path: str,
    width: int = DEFAULT_DISPLAY_WIDTH,
    height: int = DEFAULT_DISPLAY_HEIGHT,
) -> bool:
    """
    Capture a single screenshot from the X11 virtual display.

    Uses ffmpeg to grab exactly one frame from the display. Falls back to
    the ``import`` command from ImageMagick if ffmpeg fails.

    Args:
        display_number: X11 display number (e.g. 1 for :1)
        output_path: Destination file path (should end with .jpg or .png)
        width: Display width in pixels
        height: Display height in pixels

    Returns:
        True if the screenshot was captured successfully, False otherwise.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-video_size",
                f"{width}x{height}",
                "-f",
                "x11grab",
                "-i",
                f":{display_number}",
                "-frames:v",
                "1",
                "-q:v",
                "2",
                output_path,
            ],
            timeout=10,
            capture_output=True,
            check=True,
        )
        logger.info("Screenshot captured: %s", output_path)
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.warning("ffmpeg screenshot failed (%s), trying import fallback", exc)

    # Fallback: ImageMagick import
    try:
        env = os.environ.copy()
        env["DISPLAY"] = f":{display_number}"
        subprocess.run(
            ["import", "-window", "root", output_path],
            timeout=10,
            capture_output=True,
            check=True,
            env=env,
        )
        logger.info("Screenshot captured (import): %s", output_path)
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.error("Screenshot capture failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Short Clip Capture
# ---------------------------------------------------------------------------


def capture_clip(
    display_number: int,
    output_path: str,
    duration: int = 5,
    width: int = DEFAULT_DISPLAY_WIDTH,
    height: int = DEFAULT_DISPLAY_HEIGHT,
) -> bool:
    """
    Capture a short video clip from the X11 virtual display.

    Uses ffmpeg x11grab with libx264 ultrafast preset for minimal CPU impact.

    Args:
        display_number: X11 display number (e.g. 1 for :1)
        output_path: Destination file path (should end with .mp4)
        duration: Clip duration in seconds (typically 3-10)
        width: Display width in pixels
        height: Display height in pixels

    Returns:
        True if the clip was captured successfully, False otherwise.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-video_size",
                f"{width}x{height}",
                "-framerate",
                str(DEFAULT_CLIP_FPS),
                "-f",
                "x11grab",
                "-i",
                f":{display_number}",
                "-t",
                str(duration),
                "-c:v",
                FFMPEG_CODEC,
                "-preset",
                FFMPEG_PRESET,
                "-crf",
                str(DEFAULT_CLIP_CRF),
                "-pix_fmt",
                "yuv420p",
                output_path,
            ],
            timeout=duration + CLIP_TIMEOUT_BUFFER,
            capture_output=True,
            check=True,
        )
        logger.info("Clip captured (%ds): %s", duration, output_path)
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.error("Clip capture failed: %s", exc)
        return False


def capture_clip_async(
    display_number: int,
    output_path: str,
    duration: int = 5,
    width: int = DEFAULT_DISPLAY_WIDTH,
    height: int = DEFAULT_DISPLAY_HEIGHT,
    on_complete: Optional[Callable[[bool], None]] = None,
) -> threading.Thread:
    """
    Non-blocking version of capture_clip. Returns the running thread.

    Args:
        on_complete: Optional callback invoked when the clip finishes.
            Called with a single bool argument indicating success.
    """

    def _run():
        result = capture_clip(display_number, output_path, duration, width, height)
        if on_complete is not None:
            on_complete(result)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


# ---------------------------------------------------------------------------
# Full Session Recording
# ---------------------------------------------------------------------------


class SessionRecorder:
    """
    Records the full execution session from an X11 virtual display.

    Runs ffmpeg as a long-lived subprocess. Call ``start()`` to begin
    recording and ``stop()`` to gracefully terminate.

    This is opt-in only — not started by default.
    """

    def __init__(
        self,
        display_number: int,
        output_path: str,
        width: int = DEFAULT_DISPLAY_WIDTH,
        height: int = DEFAULT_DISPLAY_HEIGHT,
    ):
        self.display_number = display_number
        self.output_path = output_path
        self.width = width
        self.height = height
        self.process: Optional[subprocess.Popen] = None  # type: ignore[type-arg]
        self._started_at: Optional[float] = None

    @property
    def is_recording(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def elapsed(self) -> float:
        """Seconds since recording started, or 0 if not recording."""
        if self._started_at is None:
            return 0.0
        return time.time() - self._started_at

    def start(self) -> bool:
        """Start recording. Returns True on success."""
        if self.is_recording:
            logger.warning("Session recorder already running")
            return True

        output = Path(self.output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-y",
                    "-video_size",
                    f"{self.width}x{self.height}",
                    "-framerate",
                    str(DEFAULT_SESSION_FPS),
                    "-f",
                    "x11grab",
                    "-i",
                    f":{self.display_number}",
                    "-c:v",
                    FFMPEG_CODEC,
                    "-preset",
                    FFMPEG_PRESET,
                    "-crf",
                    str(DEFAULT_SESSION_CRF),
                    "-pix_fmt",
                    "yuv420p",
                    self.output_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._started_at = time.time()
            logger.info("Session recording started: %s", self.output_path)
            return True
        except (OSError, FileNotFoundError) as exc:
            logger.error("Failed to start session recording: %s", exc)
            self.process = None
            return False

    def stop(self) -> bool:
        """Stop recording gracefully. Returns True if stopped cleanly."""
        if not self.is_recording or self.process is None:
            logger.warning("Session recorder not running")
            return False

        final_elapsed = self.elapsed

        try:
            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=10)
            logger.info(
                "Session recording stopped (%.1fs): %s",
                final_elapsed,
                self.output_path,
            )
            return True
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg did not terminate in time, killing")
            self.process.kill()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.error("ffmpeg did not respond to SIGKILL within 5s")
            return True
        except Exception as exc:
            logger.error("Error stopping session recording: %s", exc)
            return False
        finally:
            self.process = None
            self._started_at = None


# ---------------------------------------------------------------------------
# Capture Manager (ties it all together for an execution session)
# ---------------------------------------------------------------------------


class CaptureManager:
    """
    Manages all captures for a single execution session.

    Provides methods for auto-triggered captures (step start/complete, clicks,
    form fills, navigation, errors) and manual captures. Tracks all captures
    in an ordered list with metadata.
    """

    def __init__(
        self,
        session_id: str,
        project_id: str,
        captures_dir: str,
        display_number: int = 1,
        width: int = DEFAULT_DISPLAY_WIDTH,
        height: int = DEFAULT_DISPLAY_HEIGHT,
    ):
        self.session_id = session_id
        self.project_id = project_id
        self.captures_dir = Path(captures_dir)
        self.display_number = display_number
        self.width = width
        self.height = height

        self.captures: list[CaptureRecord] = []
        self._lock = threading.Lock()
        self._session_recorder: Optional[SessionRecorder] = None
        self._session_start_time: float = time.time()

        # Ensure base captures directory exists
        self.captures_dir.mkdir(parents=True, exist_ok=True)

    def _step_dir(self, step_number: int) -> Path:
        """Get the capture directory for a specific step."""
        step_dir = self.captures_dir / f"step-{step_number}"
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir

    def _make_filename(
        self,
        step_number: int,
        capture_type: CaptureType,
        trigger: CaptureTrigger,
    ) -> tuple[Path, str]:
        """Generate a unique filename for a capture."""
        ext = ".jpg" if capture_type == CaptureType.SCREENSHOT else ".mp4"
        short_id = uuid.uuid4().hex[:8]
        filename = f"{trigger.value}-{short_id}{ext}"
        step_dir = self._step_dir(step_number)
        return step_dir / filename, filename

    def _record(
        self,
        step_number: int,
        capture_type: CaptureType,
        trigger: CaptureTrigger,
        file_path: Path,
        filename: str,
        duration: Optional[float] = None,
        status: str = "ready",
    ) -> CaptureRecord:
        """Create and store a CaptureRecord."""
        from datetime import datetime, timezone

        record = CaptureRecord(
            id=uuid.uuid4().hex,
            session_id=self.session_id,
            step_number=step_number,
            capture_type=capture_type,
            trigger=trigger,
            file_path=str(file_path),
            filename=filename,
            duration=duration,
            timestamp=time.time() - self._session_start_time,
            created_at=datetime.now(timezone.utc).isoformat(),
            status=status,
        )
        with self._lock:
            self.captures.append(record)
        return record

    # ---- Auto-capture triggers ----

    def on_step_start(self, step_number: int) -> Optional[CaptureRecord]:
        """Screenshot when a step begins."""
        path, fname = self._make_filename(
            step_number, CaptureType.SCREENSHOT, CaptureTrigger.STEP_START
        )
        if capture_screenshot(self.display_number, str(path), self.width, self.height):
            return self._record(
                step_number, CaptureType.SCREENSHOT, CaptureTrigger.STEP_START, path, fname
            )
        return None

    def on_step_complete(self, step_number: int) -> list[CaptureRecord]:
        """Screenshot + 3s clip when a step completes."""
        records: list[CaptureRecord] = []

        # Screenshot
        ss_path, ss_fname = self._make_filename(
            step_number, CaptureType.SCREENSHOT, CaptureTrigger.STEP_COMPLETE
        )
        if capture_screenshot(self.display_number, str(ss_path), self.width, self.height):
            records.append(
                self._record(
                    step_number, CaptureType.SCREENSHOT, CaptureTrigger.STEP_COMPLETE, ss_path, ss_fname
                )
            )

        # 3s clip (async — status starts as "capturing", updated on completion)
        clip_path, clip_fname = self._make_filename(
            step_number, CaptureType.CLIP, CaptureTrigger.STEP_COMPLETE
        )
        clip_record = self._record(
            step_number, CaptureType.CLIP, CaptureTrigger.STEP_COMPLETE, clip_path, clip_fname,
            duration=3.0, status="capturing",
        )
        capture_clip_async(
            self.display_number, str(clip_path), duration=3, width=self.width, height=self.height,
            on_complete=lambda ok, r=clip_record: setattr(r, "status", "ready" if ok else "failed"),
        )
        records.append(clip_record)

        return records

    def on_button_click(self, step_number: int) -> CaptureRecord:
        """3s clip when the agent clicks a button."""
        path, fname = self._make_filename(step_number, CaptureType.CLIP, CaptureTrigger.BUTTON_CLICK)
        record = self._record(
            step_number, CaptureType.CLIP, CaptureTrigger.BUTTON_CLICK, path, fname,
            duration=3.0, status="capturing",
        )
        capture_clip_async(
            self.display_number, str(path), duration=3, width=self.width, height=self.height,
            on_complete=lambda ok, r=record: setattr(r, "status", "ready" if ok else "failed"),
        )
        return record

    def on_form_fill(self, step_number: int) -> CaptureRecord:
        """5s clip when the agent fills a form."""
        path, fname = self._make_filename(step_number, CaptureType.CLIP, CaptureTrigger.FORM_FILL)
        record = self._record(
            step_number, CaptureType.CLIP, CaptureTrigger.FORM_FILL, path, fname,
            duration=5.0, status="capturing",
        )
        capture_clip_async(
            self.display_number, str(path), duration=5, width=self.width, height=self.height,
            on_complete=lambda ok, r=record: setattr(r, "status", "ready" if ok else "failed"),
        )
        return record

    def on_navigation(self, step_number: int) -> Optional[CaptureRecord]:
        """Screenshot after the agent navigates to a new page."""
        path, fname = self._make_filename(step_number, CaptureType.SCREENSHOT, CaptureTrigger.NAVIGATION)
        if capture_screenshot(self.display_number, str(path), self.width, self.height):
            return self._record(
                step_number, CaptureType.SCREENSHOT, CaptureTrigger.NAVIGATION, path, fname
            )
        return None

    def on_user_pause(self, step_number: int) -> Optional[CaptureRecord]:
        """Screenshot when the user pauses execution."""
        path, fname = self._make_filename(step_number, CaptureType.SCREENSHOT, CaptureTrigger.USER_PAUSE)
        if capture_screenshot(self.display_number, str(path), self.width, self.height):
            return self._record(
                step_number, CaptureType.SCREENSHOT, CaptureTrigger.USER_PAUSE, path, fname
            )
        return None

    def on_error(self, step_number: int) -> list[CaptureRecord]:
        """Screenshot + 5s clip on error."""
        records: list[CaptureRecord] = []

        ss_path, ss_fname = self._make_filename(
            step_number, CaptureType.SCREENSHOT, CaptureTrigger.ERROR
        )
        if capture_screenshot(self.display_number, str(ss_path), self.width, self.height):
            records.append(
                self._record(
                    step_number, CaptureType.SCREENSHOT, CaptureTrigger.ERROR, ss_path, ss_fname
                )
            )

        clip_path, clip_fname = self._make_filename(step_number, CaptureType.CLIP, CaptureTrigger.ERROR)
        clip_record = self._record(
            step_number, CaptureType.CLIP, CaptureTrigger.ERROR, clip_path, clip_fname,
            duration=5.0, status="capturing",
        )
        capture_clip_async(
            self.display_number, str(clip_path), duration=5, width=self.width, height=self.height,
            on_complete=lambda ok, r=clip_record: setattr(r, "status", "ready" if ok else "failed"),
        )
        records.append(clip_record)

        return records

    def manual_capture(self, step_number: int, include_clip: bool = True) -> list[CaptureRecord]:
        """User-triggered capture: screenshot + optional 5s clip."""
        records: list[CaptureRecord] = []

        ss_path, ss_fname = self._make_filename(
            step_number, CaptureType.SCREENSHOT, CaptureTrigger.MANUAL
        )
        if capture_screenshot(self.display_number, str(ss_path), self.width, self.height):
            records.append(
                self._record(
                    step_number, CaptureType.SCREENSHOT, CaptureTrigger.MANUAL, ss_path, ss_fname
                )
            )

        if include_clip:
            clip_path, clip_fname = self._make_filename(
                step_number, CaptureType.CLIP, CaptureTrigger.MANUAL
            )
            clip_record = self._record(
                step_number, CaptureType.CLIP, CaptureTrigger.MANUAL, clip_path, clip_fname,
                duration=5.0, status="capturing",
            )
            capture_clip_async(
                self.display_number, str(clip_path), duration=5, width=self.width, height=self.height,
                on_complete=lambda ok, r=clip_record: setattr(r, "status", "ready" if ok else "failed"),
            )
            records.append(clip_record)

        return records

    # ---- Full session recording ----

    def start_session_recording(self) -> bool:
        """Start full session recording (opt-in)."""
        if self._session_recorder and self._session_recorder.is_recording:
            return True

        output_path = str(self.captures_dir / "session-recording.mp4")
        self._session_recorder = SessionRecorder(
            display_number=self.display_number,
            output_path=output_path,
            width=self.width,
            height=self.height,
        )
        return self._session_recorder.start()

    def stop_session_recording(self) -> Optional[CaptureRecord]:
        """Stop full session recording and return the capture record."""
        if not self._session_recorder or not self._session_recorder.is_recording:
            return None

        duration = self._session_recorder.elapsed
        self._session_recorder.stop()

        output_path = self.captures_dir / "session-recording.mp4"
        if output_path.exists():
            return self._record(
                step_number=0,
                capture_type=CaptureType.SESSION,
                trigger=CaptureTrigger.MANUAL,
                file_path=output_path,
                filename="session-recording.mp4",
                duration=duration,
            )
        return None

    @property
    def is_recording_session(self) -> bool:
        return self._session_recorder is not None and self._session_recorder.is_recording

    # ---- Query captures ----

    def get_captures(self, step_number: Optional[int] = None) -> list[dict]:
        """Get all captures, optionally filtered by step number."""
        with self._lock:
            captures = list(self.captures)
        if step_number is not None:
            captures = [c for c in captures if c.step_number == step_number]
        return [c.to_dict() for c in captures]

    def get_capture_by_id(self, capture_id: str) -> Optional[CaptureRecord]:
        """Find a specific capture by ID."""
        for c in self.captures:
            if c.id == capture_id:
                return c
        return None


# ---------------------------------------------------------------------------
# Global session registry
# ---------------------------------------------------------------------------

_capture_managers: dict[str, CaptureManager] = {}


def get_capture_manager(session_id: str) -> Optional[CaptureManager]:
    """Retrieve an active CaptureManager by session ID."""
    return _capture_managers.get(session_id)


def create_capture_manager(
    session_id: str,
    project_id: str,
    captures_base_dir: str,
    display_number: int = 1,
) -> CaptureManager:
    """
    Create and register a CaptureManager for a new execution session.

    Args:
        session_id: Unique execution session ID
        project_id: YT Lab project ID
        captures_base_dir: Base directory, typically
            .autoforge/yt-lab/{project_id}/captures/
        display_number: X11 display number in the Docker container
    """
    manager = CaptureManager(
        session_id=session_id,
        project_id=project_id,
        captures_dir=captures_base_dir,
        display_number=display_number,
    )
    _capture_managers[session_id] = manager
    logger.info("CaptureManager created for session %s (project %s)", session_id, project_id)
    return manager


def remove_capture_manager(session_id: str) -> None:
    """Remove a CaptureManager from the registry."""
    manager = _capture_managers.pop(session_id, None)
    if manager and manager.is_recording_session:
        manager.stop_session_recording()
    if manager:
        logger.info("CaptureManager removed for session %s", session_id)


async def cleanup_all_capture_managers() -> None:
    """Stop all recorders and clear the registry (used during shutdown)."""
    import asyncio

    def _sync_cleanup():
        for sid in list(_capture_managers.keys()):
            remove_capture_manager(sid)
        _capture_managers.clear()

    await asyncio.to_thread(_sync_cleanup)
