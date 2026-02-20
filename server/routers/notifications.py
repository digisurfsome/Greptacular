"""
Notifications Router
====================

REST API endpoints for the agent-user communication system.
Allows the UI to write to the agent's inbox and read message history.
Supports text messages and file/image attachments.
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..utils.project_helpers import get_project_path as _get_project_path
from ..utils.validation import validate_project_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["notifications"])

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5 MB per attachment
MAX_ATTACHMENTS = 5
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".txt", ".md", ".json", ".csv"}


class InboxAttachment(BaseModel):
    """An attachment (image or file) sent with an inbox message."""
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str = Field(..., max_length=100)
    base64_data: str = Field(..., description="Base64-encoded file content")


class InboxMessage(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    attachments: list[InboxAttachment] = Field(default_factory=list, max_length=MAX_ATTACHMENTS)


class InboxMessageResponse(BaseModel):
    sent: bool
    id: str


def _save_attachment(project_dir: Path, attachment: InboxAttachment) -> str:
    """Save a base64 attachment to disk and return the file path."""
    # Validate extension
    ext = Path(attachment.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # Decode and check size
    try:
        data = base64.b64decode(attachment.base64_data)
    except Exception:
        raise ValueError(f"Invalid base64 data for '{attachment.filename}'")
    if len(data) > MAX_ATTACHMENT_SIZE:
        raise ValueError(f"Attachment '{attachment.filename}' exceeds {MAX_ATTACHMENT_SIZE // (1024 * 1024)} MB limit")

    # Save to inbox attachments directory
    attach_dir = project_dir / ".autoforge" / "inbox_attachments"
    attach_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid4().hex[:8]}_{Path(attachment.filename).name}"
    file_path = attach_dir / safe_name
    file_path.write_bytes(data)

    return str(file_path)


@router.post("/{project_name}/notifications/inbox", response_model=InboxMessageResponse)
async def send_to_inbox(project_name: str, message: InboxMessage):
    """Send a message to the agent's inbox. The agent will see this on its next check_inbox() call."""
    project_name = validate_project_name(project_name)

    project_dir = _get_project_path(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail="Project not found")

    inbox_path = project_dir / ".autoforge" / "inbox.jsonl"
    inbox_path.parent.mkdir(parents=True, exist_ok=True)

    # Save any attachments to disk
    attachment_paths: list[dict] = []
    for att in message.attachments:
        try:
            saved_path = _save_attachment(project_dir, att)
            attachment_paths.append({
                "filename": att.filename,
                "mime_type": att.mime_type,
                "path": saved_path,
            })
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    message_id = str(uuid4())
    entry: dict = {
        "id": message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "text": message.text,
    }
    if attachment_paths:
        entry["attachments"] = attachment_paths

    line = json.dumps(entry, separators=(",", ":")) + "\n"

    try:
        import fcntl
        fd = os.open(str(inbox_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, line.encode("utf-8"))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to inbox: {e}")

    return InboxMessageResponse(sent=True, id=message_id)


@router.get("/{project_name}/notifications/phase")
async def get_phase(project_name: str):
    """Get the agent's current work phase."""
    project_name = validate_project_name(project_name)

    project_dir = _get_project_path(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail="Project not found")

    phase_path = project_dir / ".autoforge" / "phase.json"
    if not phase_path.exists():
        return {"phase": None, "detail": "", "timestamp": None}

    try:
        content = phase_path.read_text()
        if not content.strip():
            return {"phase": None, "detail": "", "timestamp": None}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {"phase": None, "detail": "", "timestamp": None}
