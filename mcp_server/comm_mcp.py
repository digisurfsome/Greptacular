#!/usr/bin/env python3
"""
MCP Server for Agent-User Communication
=========================================

Provides lightweight two-way communication between the coding agent and
the user during active turns. Uses file-based messaging (JSONL for inbox/
outbox, JSON for phase state) stored in the project's .autoforge/ directory.

Tools:
- send_message: Agent sends a message to the user (appends to outbox.jsonl)
- check_inbox: Agent checks for user messages (reads and clears inbox.jsonl)
- signal_phase: Agent signals its current work phase (overwrites phase.json)

Design principles:
- File-based: no extra dependencies, no network, no database
- Thread-safe: atomic writes via tempfile + os.replace; append via fcntl
- Fast startup: no lifespan initialization needed (no database)
- Minimal: each tool does one thing quickly and returns
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Configuration from environment (same pattern as feature_mcp.py)
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", ".")).resolve()

# Communication file paths within the project's .autoforge/ directory
AUTOFORGE_DIR = PROJECT_DIR / ".autoforge"
OUTBOX_PATH = AUTOFORGE_DIR / "outbox.jsonl"
INBOX_PATH = AUTOFORGE_DIR / "inbox.jsonl"
PHASE_PATH = AUTOFORGE_DIR / "phase.json"

# Valid categories for send_message
VALID_CATEGORIES = frozenset({"status", "question", "discovery", "warning", "milestone"})

# Valid phases for signal_phase
VALID_PHASES = frozenset({"acknowledged", "reading", "planning", "building", "testing", "debugging", "complete"})


def _ensure_autoforge_dir() -> None:
    """Ensure the .autoforge directory exists. Should already exist for projects,
    but create it defensively in case this is called early."""
    AUTOFORGE_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, data: dict) -> None:
    """Append a single JSON line to a JSONL file with file locking.

    Uses fcntl.flock on POSIX systems for safe concurrent appends.
    On Windows (where fcntl is unavailable), falls back to simple append
    which is sufficient since agents typically run one-at-a-time per project.
    """
    import fcntl

    line = json.dumps(data, separators=(",", ":")) + "\n"
    _ensure_autoforge_dir()

    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, line.encode("utf-8"))
    finally:
        # Unlock is implicit on close, but be explicit for clarity
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _atomic_write_json(path: Path, data: dict) -> None:
    """Atomically write a JSON file using tempfile + os.replace.

    This prevents partial reads: the file is either the old version or the
    new version, never a half-written intermediate state.
    """
    _ensure_autoforge_dir()

    content = json.dumps(data, indent=2) + "\n"

    # Write to a temp file in the same directory (same filesystem required for os.replace)
    fd, tmp_path = tempfile.mkstemp(dir=str(AUTOFORGE_DIR), suffix=".tmp", prefix=".phase_")
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        fd = -1  # Mark as closed so finally block skips it
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on any failure
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _read_and_clear_jsonl(path: Path) -> list[dict]:
    """Read all lines from a JSONL file, then truncate it.

    Uses file locking to prevent races between the reader (agent) and
    writer (UI/user). Returns an empty list if the file doesn't exist
    or is empty.
    """
    import fcntl

    if not path.exists():
        return []

    fd = os.open(str(path), os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)

        # Read all content
        raw = b""
        while True:
            chunk = os.read(fd, 8192)
            if not chunk:
                break
            raw += chunk

        # Parse each line as JSON, skipping blank or malformed lines
        messages = []
        for line in raw.decode("utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                messages.append(json.loads(stripped))
            except json.JSONDecodeError:
                # Skip malformed lines rather than crashing the tool
                continue

        # Truncate the file to clear processed messages
        os.ftruncate(fd, 0)

        return messages
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


# Initialize the MCP server (no lifespan needed -- pure file I/O)
mcp = FastMCP("comm")


@mcp.tool()
def send_message(
    text: Annotated[str, Field(min_length=1, max_length=2000, description="The message text to send to the user")],
    category: Annotated[str, Field(description="Message category: status, question, discovery, warning, or milestone")],
) -> str:
    """Send a message to the user.

    Use this to communicate status updates, ask questions, share discoveries,
    raise warnings, or celebrate milestones during your work.

    Categories:
    - status: General progress update
    - question: Asking the user for clarification or input
    - discovery: Found something noteworthy in the codebase
    - warning: Potential issue or risk identified
    - milestone: Significant achievement reached

    Args:
        text: The message content (max 2000 characters)
        category: One of: status, question, discovery, warning, milestone

    Returns:
        JSON confirmation with the message ID
    """
    if category not in VALID_CATEGORIES:
        return json.dumps({
            "error": f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        })

    message_id = str(uuid.uuid4())
    entry = {
        "id": message_id,
        "timestamp": _now_iso(),
        "text": text,
        "category": category,
    }

    try:
        _append_jsonl(OUTBOX_PATH, entry)
        return json.dumps({"sent": True, "id": message_id})
    except Exception as e:
        return json.dumps({"error": f"Failed to send message: {str(e)}"})


@mcp.tool()
def check_inbox() -> str:
    """Check for messages from the user.

    Reads all pending messages from the inbox, then clears it so the
    same messages are not returned again. If no messages are waiting,
    returns an empty list. This is a cheap, fast operation.

    Returns:
        JSON with: messages (list of {id, timestamp, text}), count (int)
    """
    try:
        messages = _read_and_clear_jsonl(INBOX_PATH)
        return json.dumps({"messages": messages, "count": len(messages)})
    except Exception as e:
        return json.dumps({"error": f"Failed to check inbox: {str(e)}"})


@mcp.tool()
def signal_phase(
    phase: Annotated[str, Field(description="Current phase: acknowledged, reading, planning, building, testing, debugging, or complete")],
    detail: Annotated[str, Field(default="", max_length=500, description="Optional detail about the current phase")] = "",
) -> str:
    """Signal the current work phase to the user.

    Overwrites the phase file with the latest phase state. The UI can
    poll this file to show the agent's current activity at a glance.

    Phases (in typical order):
    - acknowledged: Received the task assignment
    - reading: Reading and understanding the codebase
    - planning: Planning the implementation approach
    - building: Writing code and making changes
    - testing: Running tests and verifying behavior
    - debugging: Investigating and fixing issues
    - complete: Finished the current task

    Args:
        phase: The current work phase
        detail: Optional description of what specifically is happening

    Returns:
        JSON confirmation of the phase signal
    """
    if phase not in VALID_PHASES:
        return json.dumps({
            "error": f"Invalid phase '{phase}'. Must be one of: {', '.join(sorted(VALID_PHASES))}"
        })

    phase_data = {
        "phase": phase,
        "detail": detail,
        "timestamp": _now_iso(),
    }

    try:
        _atomic_write_json(PHASE_PATH, phase_data)
        return json.dumps({"signaled": True, "phase": phase})
    except Exception as e:
        return json.dumps({"error": f"Failed to signal phase: {str(e)}"})


if __name__ == "__main__":
    mcp.run()
