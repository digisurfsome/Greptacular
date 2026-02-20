"""
Notifications Router
====================

REST API endpoints for the agent-user communication system.
Allows the UI to write to the agent's inbox and read message history.
"""

import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..utils.project_helpers import get_project_path as _get_project_path
from ..utils.validation import validate_project_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["notifications"])


class InboxMessage(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class InboxMessageResponse(BaseModel):
    sent: bool
    id: str


@router.post("/{project_name}/notifications/inbox", response_model=InboxMessageResponse)
async def send_to_inbox(project_name: str, message: InboxMessage):
    """Send a message to the agent's inbox. The agent will see this on its next check_inbox() call."""
    project_name = validate_project_name(project_name)

    project_dir = _get_project_path(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail="Project not found")

    inbox_path = project_dir / ".autoforge" / "inbox.jsonl"
    inbox_path.parent.mkdir(parents=True, exist_ok=True)

    message_id = str(uuid4())
    entry = {
        "id": message_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "text": message.text,
    }

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
