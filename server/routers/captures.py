"""
Captures Router
===============

REST API endpoints for managing screen captures during computer-use execution.
Provides endpoints to list captures, retrieve capture files, trigger manual
captures, and control full session recording.

All endpoints are scoped under /api/yt-lab/execution/{session_id}/captures.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..services.screen_recorder import (
    get_capture_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yt-lab/execution", tags=["yt-lab-captures"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class CaptureItem(BaseModel):
    """A single capture record."""

    id: str
    session_id: str
    step_number: int
    capture_type: str  # "screenshot" | "clip" | "session"
    trigger: str  # "step_start" | "step_complete" | etc.
    file_path: str
    filename: str
    duration: Optional[float] = None
    timestamp: float = 0.0
    created_at: str = ""


class CaptureListResponse(BaseModel):
    """Response for listing captures."""

    session_id: str
    captures: list[CaptureItem]
    total: int
    is_recording: bool = False


class ManualCaptureRequest(BaseModel):
    """Request to trigger a manual capture."""

    step_number: int = Field(..., ge=1, description="Current step number")
    include_clip: bool = Field(True, description="Include a 5s video clip alongside the screenshot")


class ManualCaptureResponse(BaseModel):
    """Response after a manual capture."""

    captures: list[CaptureItem]


class RecordingStatusResponse(BaseModel):
    """Response for recording status."""

    is_recording: bool
    session_id: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _require_manager(session_id: str):
    """Get the CaptureManager for a session or raise 404."""
    manager = get_capture_manager(session_id)
    if manager is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active capture session found for session_id={session_id}",
        )
    return manager


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{session_id}/captures", response_model=CaptureListResponse)
async def list_captures(
    session_id: str,
    step_number: Optional[int] = None,
) -> CaptureListResponse:
    """List all captures for an execution session, optionally filtered by step."""
    manager = _require_manager(session_id)
    captures = manager.get_captures(step_number=step_number)

    return CaptureListResponse(
        session_id=session_id,
        captures=[CaptureItem(**c) for c in captures],
        total=len(captures),
        is_recording=manager.is_recording_session,
    )


@router.get("/{session_id}/captures/{capture_id}")
async def get_capture_file(session_id: str, capture_id: str):
    """Retrieve a specific capture file by ID."""
    manager = _require_manager(session_id)
    record = manager.get_capture_by_id(capture_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Capture {capture_id} not found in session {session_id}",
        )

    file_path = Path(record.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Capture file not found on disk: {record.filename}",
        )

    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=record.filename,
    )


@router.post("/{session_id}/capture", response_model=ManualCaptureResponse)
async def manual_capture(session_id: str, request: ManualCaptureRequest) -> ManualCaptureResponse:
    """Trigger a manual capture (screenshot + optional clip)."""
    manager = _require_manager(session_id)

    records = manager.manual_capture(
        step_number=request.step_number,
        include_clip=request.include_clip,
    )

    return ManualCaptureResponse(
        captures=[CaptureItem(**r.to_dict()) for r in records],
    )


@router.post("/{session_id}/recording/start", response_model=RecordingStatusResponse)
async def start_recording(session_id: str) -> RecordingStatusResponse:
    """Start full session recording."""
    manager = _require_manager(session_id)

    success = manager.start_session_recording()
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to start session recording. Check ffmpeg availability.",
        )

    return RecordingStatusResponse(
        is_recording=True,
        session_id=session_id,
    )


@router.post("/{session_id}/recording/stop", response_model=RecordingStatusResponse)
async def stop_recording(session_id: str) -> RecordingStatusResponse:
    """Stop full session recording."""
    manager = _require_manager(session_id)

    record = manager.stop_session_recording()
    if record is None:
        raise HTTPException(
            status_code=400,
            detail="No active session recording to stop.",
        )

    return RecordingStatusResponse(
        is_recording=False,
        session_id=session_id,
    )
