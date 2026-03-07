"""
DunkStack Router
================

REST and WebSocket endpoints for the DunkStack file-based context mechanism.

Provides:
- Reading/writing .agent/comms/ files (walkie-talkie through files)
- Reading/writing .agent/working_memory.md, index.md, bridge.md
- Reading .agent/settings/config.yml (safety thresholds, mode config)
- Context gauge token tracking state
- Session control (idle/continue/autopilot mode)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..services.dunkstack_chat_session import DunkStackChatSession

import yaml
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dunkstack", tags=["dunkstack"])

# Root of the project (parent of server/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _agent_dir(project_name: Optional[str] = None) -> Path:
    """Return the .agent directory path, optionally scoped to a project."""
    if project_name:
        from ..utils.project_helpers import get_project_path
        project_dir = get_project_path(project_name)
        if project_dir and project_dir.exists():
            return project_dir / ".agent"
    return ROOT_DIR / ".agent"


def _ensure_agent_dir(project_name: Optional[str] = None):
    """Ensure .agent directory structure exists and universal templates are in place."""
    agent = _agent_dir(project_name)
    for subdir in ["comms", "knowledge", "output", "progress", "settings"]:
        (agent / subdir).mkdir(parents=True, exist_ok=True)

    # Copy universal DunkStack template files if they don't already exist
    from ..services.agent_os_file_utils import copy_universal_templates
    copy_universal_templates(agent)


def _reset_comms_files(project_name: Optional[str] = None) -> None:
    """Reset comms files to their template defaults for a fresh session.

    Overwrites to_human.md, from_human.md, and control.md with clean templates
    so that stale content from previous sessions doesn't bleed through.
    """
    agent = _agent_dir(project_name)
    comms = agent / "comms"
    comms.mkdir(parents=True, exist_ok=True)

    # Reset to_human.md (agent -> human messages)
    (comms / "to_human.md").write_text(
        "# Agent Messages\n"
        "> Append new messages at the bottom. Never delete previous entries.\n"
        "> Format: ## [timestamp] Category - Brief Title\n\n"
        "[No messages yet]\n",
        encoding="utf-8",
    )

    # Reset from_human.md (human -> agent messages)
    (comms / "from_human.md").write_text(
        "# Human Messages\n"
        "> Human writes messages here. Agent reads only, never modifies.\n"
        "> Format: ## [timestamp] Message Title\n\n"
        "[No messages yet]\n",
        encoding="utf-8",
    )

    # Reset control.md to idle
    (comms / "control.md").write_text(
        "# Session Control\nmode: idle\nmessage: none\n",
        encoding="utf-8",
    )

    logger.info("Reset comms files for %s", project_name or "default")


# ============================================================================
# Pydantic Models
# ============================================================================


class CommsMessage(BaseModel):
    """A message to append to a comms file."""
    content: str
    title: Optional[str] = None
    category: Optional[str] = "Message"


class ControlUpdate(BaseModel):
    """Update the session control mode."""
    mode: str  # idle | continue | autopilot
    message: Optional[str] = None


class ConfigUpdate(BaseModel):
    """Partial update to config.yml settings."""
    safety: Optional[dict] = None
    context_management: Optional[dict] = None
    session: Optional[dict] = None
    mode: Optional[dict] = None
    api: Optional[dict] = None
    agent_os: Optional[dict] = None


class ModelPresetUpdate(BaseModel):
    """Update the active model preset (derives billing mode automatically)."""
    model_id: str  # claude-opus-4-6 | claude-sonnet-4-6
    context_window: int  # 200000 | 1000000


class BridgeSaveRequest(BaseModel):
    """Request to create a bridge save."""
    reason: str = "manual"
    current_task: Optional[str] = None
    progress: Optional[str] = None
    next_steps: Optional[str] = None
    open_questions: Optional[str] = None


class BenchmarkCheckpoint(BaseModel):
    """A single checkpoint in a benchmark run."""
    name: str
    token_target: int
    task: str = ""


class BenchmarkStartRequest(BaseModel):
    """Request to start benchmark mode with optional custom checkpoints."""
    checkpoints: Optional[list[BenchmarkCheckpoint]] = None


class TokenSnapshot(BaseModel):
    """A snapshot of token usage for the context gauge."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_cost_usd: float = 0.0
    timestamp: Optional[str] = None


# ============================================================================
# In-memory token tracking (per-session, resets on server restart)
# ============================================================================

_token_state = {
    "entries": [],       # List of TokenSnapshot dicts
    "cumulative": {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "total_cost_usd": 0.0,
        "api_calls": 0,
    },
    "model_limit": 200000,
    "mode": "subscription",  # subscription | api
}

# Track previous safety tier for transition detection (auto bridge save / auto stop)
_previous_safety_tier: int = 0

# Benchmark mode state
_benchmark_state: dict = {
    "active": False,
    "checkpoints": [],  # List of {"name": str, "token_target": int, "task": str, "reached": bool, "reached_at_tokens": int | None}
    "current_checkpoint_index": 0,
}

DEFAULT_BENCHMARK_CHECKPOINTS = [
    {"name": "CP-1", "token_target": 10000, "task": "Email Notification Service"},
    {"name": "CP-2", "token_target": 35000, "task": "Activity Feed Generator"},
    {"name": "MR-1", "token_target": 50000, "task": "Comments (Memory Recall)"},
    {"name": "CP-3", "token_target": 65000, "task": "Search & Filter Engine"},
    {"name": "MR-2", "token_target": 75000, "task": "Labels (Memory Recall)"},
    {"name": "CP-4", "token_target": 90000, "task": "Webhook Dispatcher"},
    {"name": "MR-3", "token_target": 95000, "task": "Audit Log (Memory Recall)"},
]

# Active WebSocket connections for real-time updates
_ws_connections: list[WebSocket] = []


async def _broadcast(msg: dict):
    """Broadcast a message to all connected WebSocket clients."""
    dead = []
    for ws in _ws_connections:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_connections.remove(ws)


# ============================================================================
# File Operations - Comms
# ============================================================================


@router.get("/comms/to-human")
def read_to_human(project_name: Optional[str] = None):
    """Read the agent's messages to the human."""
    path = _agent_dir(project_name) / "comms" / "to_human.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


@router.get("/comms/from-human")
def read_from_human(project_name: Optional[str] = None):
    """Read the human's messages to the agent."""
    path = _agent_dir(project_name) / "comms" / "from_human.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


@router.post("/comms/from-human")
async def write_from_human(msg: CommsMessage, project_name: Optional[str] = None):
    """Append a message to from_human.md (human → agent communication).

    Also forwards the message to any running DunkStack agent sessions so the
    agent processes it immediately (instead of only seeing it on next startup).
    """
    _ensure_agent_dir(project_name)
    path = _agent_dir(project_name) / "comms" / "from_human.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    title = msg.title or msg.category or "Message"
    entry = f"\n\n## [{timestamp}] {title}\n{msg.content}\n"

    # Read existing content or create with header
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# Human Messages\n> Human writes messages here. Agent reads only, never modifies.\n> Format: ## [timestamp] Message Title\n"

    path.write_text(existing + entry, encoding="utf-8")

    # Broadcast the new message to UI clients
    await _broadcast({
        "type": "comms_update",
        "channel": "from_human",
        "timestamp": timestamp,
        "title": title,
        "content": msg.content,
    })

    # Forward to any running agent sessions so they process it immediately.
    # The agent receives a nudge telling it to re-read from_human.md and respond.
    forwarded = False
    if _agent_sessions:
        nudge = (
            f"New message from the human was posted to .agent/comms/from_human.md at {timestamp}. "
            "Re-read .agent/comms/from_human.md now and respond to the latest message. "
            "Write your response to .agent/comms/to_human.md (NOT in chat). "
            "Chat reply: 1-sentence status only."
        )
        for session_id, session in list(_agent_sessions.items()):
            try:
                # Stream agent response events to all connected WS clients
                async for event in session.send_message(nudge):
                    await _broadcast(event)
                forwarded = True
                logger.info("Forwarded walkie-talkie message to agent session %s", session_id)
            except Exception as e:
                logger.warning("Failed to forward message to agent session %s: %s", session_id, e)

    return {"status": "ok", "timestamp": timestamp, "forwarded_to_agent": forwarded}


@router.post("/comms/to-human")
async def write_to_human(msg: CommsMessage, project_name: Optional[str] = None):
    """Append a message to to_human.md (agent → human communication)."""
    _ensure_agent_dir(project_name)
    path = _agent_dir(project_name) / "comms" / "to_human.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    title = msg.title or msg.category or "Update"
    entry = f"\n\n## [{timestamp}] {msg.category} - {title}\n{msg.content}\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = "# Agent Messages\n> Append new messages at the bottom. Never delete previous entries.\n> Format: ## [timestamp] Category - Brief Title\n"

    path.write_text(existing + entry, encoding="utf-8")

    await _broadcast({
        "type": "comms_update",
        "channel": "to_human",
        "timestamp": timestamp,
        "title": title,
        "content": msg.content,
    })

    return {"status": "ok", "timestamp": timestamp}


@router.post("/comms/reset")
async def reset_comms(project_name: Optional[str] = None):
    """Reset all comms files to clean templates for a fresh session.

    Clears to_human.md, from_human.md, and control.md so stale content
    from previous sessions doesn't bleed into new ones.
    """
    _ensure_agent_dir(project_name)
    _reset_comms_files(project_name)

    await _broadcast({"type": "comms_reset", "project_name": project_name})

    return {"status": "ok", "message": "Comms files reset to clean state"}


# ============================================================================
# Session Control
# ============================================================================


@router.get("/control")
def read_control(project_name: Optional[str] = None):
    """Read the current session control mode."""
    path = _agent_dir(project_name) / "comms" / "control.md"
    if not path.exists():
        return {"mode": "idle", "message": "none"}

    content = path.read_text(encoding="utf-8")
    mode = "idle"
    message = "none"

    for line in content.splitlines():
        if line.startswith("mode:"):
            mode = line.split(":", 1)[1].strip()
        elif line.startswith("message:"):
            message = line.split(":", 1)[1].strip()

    return {"mode": mode, "message": message}


@router.post("/control")
async def update_control(update: ControlUpdate, project_name: Optional[str] = None):
    """Update the session control mode."""
    _ensure_agent_dir(project_name)
    path = _agent_dir(project_name) / "comms" / "control.md"

    content = f"# Session Control\nmode: {update.mode}\nmessage: {update.message or 'none'}\n"
    path.write_text(content, encoding="utf-8")

    await _broadcast({
        "type": "control_update",
        "mode": update.mode,
        "message": update.message,
    })

    return {"status": "ok", "mode": update.mode}


# ============================================================================
# Working Memory & Index
# ============================================================================


@router.get("/working-memory")
def read_working_memory(project_name: Optional[str] = None):
    """Read the agent's working memory."""
    path = _agent_dir(project_name) / "working_memory.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


@router.get("/index")
def read_index(project_name: Optional[str] = None):
    """Read the agent's file index."""
    path = _agent_dir(project_name) / "index.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


# ============================================================================
# Bridge Save
# ============================================================================


@router.post("/bridge/save")
async def save_bridge(req: BridgeSaveRequest, project_name: Optional[str] = None):
    """Create a bridge save for session continuity."""
    _ensure_agent_dir(project_name)
    path = _agent_dir(project_name) / "bridge.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# Bridge State
Saved: {timestamp}
Reason: {req.reason}

## Current Task
{req.current_task or '[No active task]'}

## Progress on Current Task
{req.progress or '[No progress recorded]'}

## Immediate Next Steps
{req.next_steps or '[No next steps defined]'}

## Open Questions
{req.open_questions or '[None]'}
"""
    path.write_text(content, encoding="utf-8")

    # Also append to build log
    log_path = _agent_dir(project_name) / "progress" / "build_log.md"
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8")
    else:
        log_content = "# Build Log\n> Append-only. Each entry includes timestamp, what was done, and why.\n"

    log_entry = f"\n\n## [{timestamp}] Bridge Save\nReason: {req.reason}\nTask: {req.current_task or 'None'}\n"
    log_path.write_text(log_content + log_entry, encoding="utf-8")

    await _broadcast({"type": "bridge_saved", "timestamp": timestamp})

    return {"status": "ok", "timestamp": timestamp}


@router.get("/bridge")
def read_bridge(project_name: Optional[str] = None):
    """Read the bridge state (if exists)."""
    path = _agent_dir(project_name) / "bridge.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


# ============================================================================
# Config / Settings
# ============================================================================


@router.get("/config")
def read_config(project_name: Optional[str] = None):
    """Read the agent config.yml as JSON."""
    path = _agent_dir(project_name) / "settings" / "config.yml"
    if not path.exists():
        return {"config": {}, "exists": False}

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return {"config": config, "exists": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read config: {e}")


@router.patch("/config")
async def update_config(update: ConfigUpdate, project_name: Optional[str] = None):
    """Partially update config.yml settings."""
    _ensure_agent_dir(project_name)
    path = _agent_dir(project_name) / "settings" / "config.yml"

    # Read existing
    config = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            config = {}

    # Merge updates
    for key in ["safety", "context_management", "session", "mode", "api"]:
        val = getattr(update, key, None)
        if val is not None:
            if key in config and isinstance(config[key], dict):
                config[key].update(val)
            else:
                config[key] = val

    # Write back
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Update in-memory token state
    if update.safety and "model_limit" in update.safety:
        _token_state["model_limit"] = update.safety["model_limit"]
    if update.mode and "type" in update.mode:
        _token_state["mode"] = update.mode["type"]

    await _broadcast({"type": "config_update", "config": config})

    return {"status": "ok", "config": config}


# ============================================================================
# Auth / SDK Environment
# ============================================================================


def _is_subscription_mode() -> bool:
    """Check if the current model preset should use subscription billing.

    200K context = subscription (free with Claude Max)
    1M context   = API key billing (costs money)

    Same logic as client.py: use_api_billing = (agent_type == "initializer")
    maps to: subscription = (context_window <= 200_000)
    """
    return _token_state["model_limit"] <= 200_000


@router.get("/sdk-env")
def get_sdk_env():
    """Get the correct SDK environment vars for the current DunkStack model preset.

    Returns the env dict that should be passed to ClaudeSDKClient or
    ClaudeAgentOptions(env=...) to route billing correctly:
    - 200K models → subscription OAuth (free)
    - 1M models  → API key billing (paid)
    """
    from registry import get_effective_sdk_env

    force_sub = _is_subscription_mode()
    sdk_env = get_effective_sdk_env(force_subscription=force_sub)

    # Redact API keys in the response (for display/debugging only)
    redacted = {}
    for k, v in sdk_env.items():
        if "KEY" in k or "TOKEN" in k or "SECRET" in k:
            redacted[k] = f"{v[:8]}...{v[-4:]}" if len(v) > 12 else "***"
        else:
            redacted[k] = v

    return {
        "mode": "subscription" if force_sub else "api",
        "model_limit": _token_state["model_limit"],
        "env_keys": list(sdk_env.keys()),
        "env_redacted": redacted,
    }


@router.post("/model-preset")
async def update_model_preset(preset: ModelPresetUpdate, project_name: Optional[str] = None):
    """Update the active model preset and derive billing mode automatically.

    This is the single entry point for model changes. It:
    1. Updates the in-memory token state (model_limit, mode)
    2. Persists to config.yml
    3. Broadcasts to WebSocket clients
    """
    # Derive billing mode: 200K = subscription, 1M = api
    is_sub = preset.context_window <= 200_000
    mode_str = "subscription" if is_sub else "api"

    # Update in-memory state
    _token_state["model_limit"] = preset.context_window
    _token_state["mode"] = mode_str

    # Persist to config.yml
    _ensure_agent_dir(project_name)
    config_path = _agent_dir(project_name) / "settings" / "config.yml"
    config: dict = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            config = {}

    config.setdefault("api", {})["model_id"] = preset.model_id
    config.setdefault("safety", {})["model_limit"] = preset.context_window
    config.setdefault("mode", {})["type"] = mode_str

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Log the billing mode so it's visible in server output
    logger.info(
        "DunkStack model preset: %s @ %dK → billing: %s",
        preset.model_id,
        preset.context_window // 1000,
        mode_str,
    )

    await _broadcast({
        "type": "model_preset_update",
        "model_id": preset.model_id,
        "model_limit": preset.context_window,
        "mode": mode_str,
    })

    return {
        "status": "ok",
        "model_id": preset.model_id,
        "model_limit": preset.context_window,
        "mode": mode_str,
    }


# ============================================================================
# Context Gauge - Token Tracking
# ============================================================================


@router.get("/tokens")
def get_token_state(project_name: Optional[str] = None):
    """Get the current token tracking state for the context gauge."""
    cumulative = _token_state["cumulative"]
    model_limit = _token_state["model_limit"]
    total_tokens = cumulative["input_tokens"] + cumulative["output_tokens"]
    usage_pct = (total_tokens / model_limit * 100) if model_limit > 0 else 0

    return {
        "cumulative": cumulative,
        "model_limit": model_limit,
        "mode": _token_state["mode"],
        "usage_percent": round(usage_pct, 2),
        "entries_count": len(_token_state["entries"]),
        "safety": _get_safety_status(usage_pct),
    }


@router.post("/tokens/record")
async def record_tokens(snapshot: TokenSnapshot, project_name: Optional[str] = None):
    """Record a token usage snapshot from an API call."""
    ts = snapshot.timestamp or datetime.now(timezone.utc).isoformat()

    entry = {
        "input_tokens": snapshot.input_tokens,
        "output_tokens": snapshot.output_tokens,
        "cache_read_tokens": snapshot.cache_read_tokens,
        "cache_creation_tokens": snapshot.cache_creation_tokens,
        "total_cost_usd": snapshot.total_cost_usd,
        "timestamp": ts,
    }
    _token_state["entries"].append(entry)

    # Update cumulative
    cum = _token_state["cumulative"]
    cum["input_tokens"] += snapshot.input_tokens
    cum["output_tokens"] += snapshot.output_tokens
    cum["cache_read_tokens"] += snapshot.cache_read_tokens
    cum["cache_creation_tokens"] += snapshot.cache_creation_tokens
    cum["total_cost_usd"] += snapshot.total_cost_usd
    cum["api_calls"] += 1

    # Calculate safety status
    model_limit = _token_state["model_limit"]
    total = cum["input_tokens"] + cum["output_tokens"]
    usage_pct = (total / model_limit * 100) if model_limit > 0 else 0
    safety = _get_safety_status(usage_pct)

    # ── Auto-actions on safety tier transitions ──
    global _previous_safety_tier
    current_tier = safety.get("tier", 0)

    if current_tier >= 2 and _previous_safety_tier < 2:
        # Transition to HANDOFF tier — auto-save bridge state
        asyncio.create_task(_auto_bridge_save(project_name, usage_pct))

    if current_tier >= 3 and _previous_safety_tier < 3:
        # Transition to HARD STOP tier — stop the agent
        asyncio.create_task(_auto_stop_agent(project_name))

    _previous_safety_tier = current_tier

    # Check benchmark checkpoints
    await _check_benchmark_checkpoints(total)

    await _broadcast({
        "type": "token_update",
        "entry": entry,
        "cumulative": cum,
        "usage_percent": round(usage_pct, 2),
        "safety": safety,
    })

    return {"status": "ok", "usage_percent": round(usage_pct, 2), "safety": safety}


@router.post("/tokens/reset")
async def reset_tokens(project_name: Optional[str] = None):
    """Reset token tracking state (new session)."""
    global _previous_safety_tier
    _token_state["entries"] = []
    _token_state["cumulative"] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "total_cost_usd": 0.0,
        "api_calls": 0,
    }
    _previous_safety_tier = 0

    await _broadcast({"type": "token_reset"})
    return {"status": "ok"}


@router.get("/tokens/log")
def get_token_log(project_name: Optional[str] = None):
    """Get the full token log entries."""
    return {"entries": _token_state["entries"]}


def _get_safety_status(usage_pct: float) -> dict:
    """Determine the safety tier based on usage percentage."""
    # Read thresholds from config or use defaults
    config_path = _agent_dir() / "settings" / "config.yml"
    warning_pct = 45.0
    handoff_pct = 47.5
    hard_stop_pct = 50.0

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            safety = config.get("safety", {})
            warning_pct = safety.get("warning_threshold_pct", 45.0)
            handoff_pct = safety.get("handoff_threshold_pct", 47.5)
            hard_stop_pct = safety.get("hard_stop_threshold_pct", 50.0)
        except Exception:
            pass

    if usage_pct >= hard_stop_pct:
        return {"tier": 3, "label": "HARD STOP", "color": "red", "message": "Session should terminate."}
    elif usage_pct >= handoff_pct:
        return {"tier": 2, "label": "HANDOFF", "color": "red", "message": "Stop coding. Write handoff file."}
    elif usage_pct >= warning_pct:
        return {"tier": 1, "label": "WARNING", "color": "orange", "message": "Approaching limit. Prepare for handoff if needed."}
    else:
        return {"tier": 0, "label": "OK", "color": "green", "message": "Operating normally."}


async def _auto_bridge_save(project_name: Optional[str], usage_pct: float) -> None:
    """Auto-save bridge state when HANDOFF threshold is reached.

    Writes current session state to .agent/bridge.md and injects a
    walkie-talkie message telling the agent to wrap up and commit.
    """
    try:
        agent = _agent_dir(project_name)
        bridge_path = agent / "bridge.md"
        comms_dir = agent / "comms"
        comms_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        bridge_content = (
            f"# Bridge State (Auto-saved)\n"
            f"Saved: {timestamp}\n"
            f"Reason: Context usage reached HANDOFF threshold ({usage_pct:.1f}%)\n\n"
            f"## Instructions\n"
            f"This bridge save was auto-generated by the safety system.\n"
            f"The agent should commit all work and prepare for handoff.\n"
        )
        bridge_path.write_text(bridge_content, encoding="utf-8")

        # Inject a walkie-talkie message to the agent
        from_human_path = comms_dir / "from_human.md"
        handoff_msg = (
            f"\n\n## [{timestamp}] SYSTEM — HANDOFF THRESHOLD REACHED\n"
            f"Context usage is at {usage_pct:.1f}%. You are in the HANDOFF zone.\n\n"
            f"**IMMEDIATELY:**\n"
            f"1. Commit all current work (`git add -A && git commit`)\n"
            f"2. Write your handoff notes to .agent/bridge.md\n"
            f"3. Stop working on new tasks\n"
            f"4. If in factory mode, call `factory_write_handoff`\n"
        )
        if from_human_path.exists():
            existing = from_human_path.read_text(encoding="utf-8")
        else:
            existing = "# Human Messages\n"
        from_human_path.write_text(existing + handoff_msg, encoding="utf-8")

        await _broadcast({
            "type": "bridge_saved",
            "auto": True,
            "reason": f"HANDOFF threshold ({usage_pct:.1f}%)",
            "timestamp": timestamp,
        })

        logger.info("Auto bridge save triggered at %.1f%% usage", usage_pct)

    except Exception as e:
        logger.error("Auto bridge save failed: %s", e)


async def _auto_stop_agent(project_name: Optional[str]) -> None:
    """Auto-stop the coding agent when HARD STOP threshold is reached.

    Stops the DunkStack coding session and broadcasts a notification.
    """
    try:
        from ..services.dunkstack_session import get_coding_session, remove_coding_session

        # Try to find the session by project_name or iterate all
        session = None
        if project_name:
            session = get_coding_session(project_name)

        if not session:
            # Try to find any running session
            from ..services.dunkstack_session import list_coding_sessions
            for s_info in list_coding_sessions():
                if s_info.get("status") == "running":
                    p_name = s_info.get("project_name")
                    if p_name:
                        session = get_coding_session(p_name)
                        project_name = p_name
                        break

        if session and session.status == "running":
            logger.warning("HARD STOP: Auto-stopping agent for %s", project_name)
            await remove_coding_session(project_name)

            await _broadcast({
                "type": "agent_event",
                "status": "stopped",
                "reason": "HARD STOP — context limit reached",
            })

            await _broadcast({
                "type": "hard_stop",
                "project_name": project_name,
                "message": "Agent auto-stopped: context usage exceeded HARD STOP threshold.",
            })

            logger.info("Agent auto-stopped at HARD STOP threshold for %s", project_name)
        else:
            logger.debug("HARD STOP triggered but no running agent found")

    except Exception as e:
        logger.error("Auto-stop agent failed: %s", e)


# ============================================================================
# Benchmark Mode
# ============================================================================


@router.post("/benchmark/start")
async def start_benchmark(req: Optional[BenchmarkStartRequest] = None):
    """Start benchmark mode with optional custom checkpoints.

    If no checkpoints are provided, uses the default benchmark checkpoints
    that cover a range of token targets from 10K to 95K.
    """
    if req and req.checkpoints:
        checkpoints = [
            {
                "name": cp.name,
                "token_target": cp.token_target,
                "task": cp.task,
                "reached": False,
                "reached_at_tokens": None,
            }
            for cp in req.checkpoints
        ]
    else:
        checkpoints = [
            {**cp, "reached": False, "reached_at_tokens": None}
            for cp in DEFAULT_BENCHMARK_CHECKPOINTS
        ]

    _benchmark_state["active"] = True
    _benchmark_state["checkpoints"] = checkpoints
    _benchmark_state["current_checkpoint_index"] = 0

    logger.info("Benchmark mode started with %d checkpoints", len(checkpoints))

    await _broadcast({
        "type": "benchmark_started",
        "total_checkpoints": len(checkpoints),
    })

    return {
        "status": "ok",
        "benchmark": _benchmark_state,
    }


@router.post("/benchmark/stop")
async def stop_benchmark():
    """Stop benchmark mode and return final state."""
    _benchmark_state["active"] = False

    logger.info("Benchmark mode stopped")

    await _broadcast({"type": "benchmark_stopped"})

    return {
        "status": "ok",
        "benchmark": _benchmark_state,
    }


@router.get("/benchmark/status")
def get_benchmark_status():
    """Get the current benchmark state including checkpoint progress."""
    return {"benchmark": _benchmark_state}


async def _check_benchmark_checkpoints(total_tokens: int) -> None:
    """Check if any benchmark checkpoints have been reached and broadcast.

    Only fires one checkpoint per call (the first unreached one whose
    token_target has been met) to keep events sequential.
    """
    if not _benchmark_state["active"]:
        return

    checkpoints = _benchmark_state["checkpoints"]
    for i, cp in enumerate(checkpoints):
        if not cp["reached"] and total_tokens >= cp["token_target"]:
            cp["reached"] = True
            cp["reached_at_tokens"] = total_tokens
            _benchmark_state["current_checkpoint_index"] = i + 1
            await _broadcast({
                "type": "benchmark_checkpoint",
                "checkpoint": cp["name"],
                "token_target": cp["token_target"],
                "actual_tokens": total_tokens,
                "task": cp.get("task", ""),
                "index": i,
                "total_checkpoints": len(checkpoints),
            })
            break  # Only fire one checkpoint at a time


# ============================================================================
# Build Log
# ============================================================================


@router.get("/build-log")
def read_build_log(project_name: Optional[str] = None):
    """Read the build log."""
    path = _agent_dir(project_name) / "progress" / "build_log.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}


# ============================================================================
# Coding Agent - Start/Stop/Status/Send
# ============================================================================


class AgentStartRequest(BaseModel):
    """Request to start the coding agent."""
    project_name: str
    model_id: str = "claude-opus-4-6"
    context_window: int = 200000


class AgentMessageRequest(BaseModel):
    """Request to send a message to the running agent."""
    message: str


@router.post("/agent/start")
async def start_coding_agent(req: AgentStartRequest):
    """Start a coding agent session for a project.

    Creates a DunkStackCodingSession, initializes the Claude SDK client,
    and sends the startup message so the agent begins following the
    file-based protocol (reads index.md, working_memory.md, etc.).
    """
    from ..services.dunkstack_session import (
        create_coding_session,
        get_coding_session,
    )
    from ..utils.project_helpers import get_project_path

    # Check if already running
    existing = get_coding_session(req.project_name)
    if existing and existing.status == "running":
        return {"status": "already_running", **existing.get_status()}

    # Resolve project path
    project_dir = get_project_path(req.project_name)
    if not project_dir or not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    # Ensure .agent/ directory exists and reset comms for a clean session
    _ensure_agent_dir(req.project_name)
    _reset_comms_files(req.project_name)

    # Create session (async - stops any existing session for this project)
    session = await create_coding_session(
        project_name=req.project_name,
        project_dir=project_dir,
        model_id=req.model_id,
        context_window=req.context_window,
    )

    # Start the agent - this initializes the SDK client AND sends the
    # bootstrap message so the agent reads its .agent/ files and begins working.
    all_events = []
    async for event in session.start():
        all_events.append(event)
        await _broadcast({"type": "agent_event", **event})

    # Check if start succeeded
    if session.status != "running":
        return {
            "status": "error",
            "error": session.error or "Failed to start",
            "events": all_events,
        }

    return {
        "status": "running",
        **session.get_status(),
        "events": all_events,
    }


@router.post("/agent/send")
async def send_to_coding_agent(req: AgentMessageRequest, project_name: Optional[str] = None):
    """Send a message to the running coding agent and get its response.

    The message is sent directly to the Claude SDK client. The agent
    will process it according to its file-based protocol.
    """
    from ..services.dunkstack_session import get_coding_session

    if not project_name:
        raise HTTPException(status_code=400, detail="project_name query param required")

    session = get_coding_session(project_name)
    if not session or session.status != "running":
        raise HTTPException(status_code=404, detail="No running agent for this project")

    response_events = []
    async for event in session.send_message(req.message):
        response_events.append(event)
        await _broadcast({"type": "agent_event", **event})

    return {"status": "ok", "events": response_events}


@router.post("/agent/stop")
async def stop_coding_agent(project_name: Optional[str] = None):
    """Stop the running coding agent."""
    from ..services.dunkstack_session import get_coding_session, remove_coding_session

    if not project_name:
        raise HTTPException(status_code=400, detail="project_name query param required")

    session = get_coding_session(project_name)
    if not session:
        return {"status": "not_running"}

    await remove_coding_session(project_name)

    await _broadcast({"type": "agent_event", "status": "stopped"})

    return {"status": "stopped"}


@router.get("/agent/status")
def get_coding_agent_status(project_name: Optional[str] = None):
    """Get the status of the coding agent."""
    from ..services.dunkstack_session import get_coding_session

    if not project_name:
        return {"status": "stopped"}

    session = get_coding_session(project_name)
    if not session:
        return {"status": "stopped"}

    return session.get_status()


@router.get("/agent/sessions")
def list_coding_sessions():
    """List all active coding agent sessions."""
    from ..services.dunkstack_session import list_coding_sessions as _list

    return {"sessions": _list()}


# ============================================================================
# WebSocket - Real-time updates
# ============================================================================


# Active agent sessions keyed by session_id
_agent_sessions: dict[str, "DunkStackChatSession"] = {}


async def _record_token_usage(
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
    total_cost_usd: float,
) -> None:
    """Record token usage into the in-memory DunkStack gauge and broadcast."""
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "total_cost_usd": total_cost_usd,
        "timestamp": ts,
    }
    _token_state["entries"].append(entry)

    cum = _token_state["cumulative"]
    cum["input_tokens"] += input_tokens
    cum["output_tokens"] += output_tokens
    cum["cache_read_tokens"] += cache_read_tokens
    cum["cache_creation_tokens"] += cache_creation_tokens
    cum["total_cost_usd"] += total_cost_usd
    cum["api_calls"] += 1

    model_limit = _token_state["model_limit"]
    total = cum["input_tokens"] + cum["output_tokens"]
    usage_pct = (total / model_limit * 100) if model_limit > 0 else 0
    safety = _get_safety_status(usage_pct)

    # Check benchmark checkpoints
    await _check_benchmark_checkpoints(total)

    await _broadcast({
        "type": "token_update",
        "entry": entry,
        "cumulative": cum,
        "usage_percent": round(usage_pct, 2),
        "safety": safety,
    })


@router.websocket("/ws")
async def dunkstack_websocket(ws: WebSocket):
    """WebSocket for real-time DunkStack updates and agent chat.

    Client -> Server:
    - {"type": "ping"} - Keep-alive ping
    - {"type": "start_agent", "model_id": str, "context_mode": str,
       "working_directory": str, "effort": str} - Start a new agent session
    - {"type": "message", "content": str} - Send a message to the running agent
    - {"type": "stop_agent"} - Stop the running agent session

    Server -> Client:
    - {"type": "init", "token_state": {...}} - Initial state
    - {"type": "pong"} - Keep-alive pong
    - {"type": "agent_started", "session_id": str} - Agent session started
    - {"type": "agent_stopped"} - Agent session stopped
    - {"type": "text", "content": str} - Agent text response chunk
    - {"type": "tool_call", "tool": str, "input": dict} - Agent tool call
    - {"type": "token_usage", ...} - Token usage from agent
    - {"type": "response_done"} - Agent finished responding
    - {"type": "error", "content": str} - Error message
    - {"type": "status", "content": str} - Status message
    - All existing types (comms_update, token_update, etc.) via broadcast
    """
    await ws.accept()
    _ws_connections.append(ws)
    logger.info("DunkStack WebSocket connected (total: %d)", len(_ws_connections))

    current_session_id: Optional[str] = None

    try:
        # Send initial state
        await ws.send_json({
            "type": "init",
            "token_state": {
                "cumulative": _token_state["cumulative"],
                "model_limit": _token_state["model_limit"],
                "mode": _token_state["mode"],
                "entries_count": len(_token_state["entries"]),
            },
        })

        # Keep alive and listen for client messages
        while True:
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=300)
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await ws.send_json({"type": "pong"})

                elif msg_type == "start_agent":
                    # Start a new agent session
                    from ..services.dunkstack_chat_session import DunkStackChatSession

                    model_id = msg.get("model_id", "claude-opus-4-6")
                    context_mode = msg.get("context_mode", "1m")
                    working_directory = msg.get("working_directory")
                    effort = msg.get("effort", "high")

                    # Resolve working directory from project name if provided
                    project_name = msg.get("project_name")
                    if not working_directory and project_name:
                        from ..utils.project_helpers import get_project_path
                        project_path = get_project_path(project_name)
                        if project_path and project_path.exists():
                            working_directory = str(project_path)

                    if not working_directory:
                        working_directory = str(Path.home())

                    # Close existing session if any
                    if current_session_id and current_session_id in _agent_sessions:
                        old_session = _agent_sessions.pop(current_session_id)
                        try:
                            await old_session.close()
                        except Exception as e:
                            logger.warning("Error closing old DunkStack session: %s", e)

                    # Reset comms files for a clean session (fixes stale chat)
                    _ensure_agent_dir(project_name)
                    _reset_comms_files(project_name)

                    session_id = f"dunkstack-{id(ws)}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
                    session = DunkStackChatSession(
                        session_id=session_id,
                        model_id=model_id,
                        working_directory=working_directory,
                        context_mode=context_mode,
                        effort=effort,
                        on_token_usage=_record_token_usage,
                    )

                    _agent_sessions[session_id] = session
                    current_session_id = session_id

                    # Start the session and stream initialization events
                    try:
                        async for event in session.start():
                            await ws.send_json(event)
                        await ws.send_json({
                            "type": "agent_started",
                            "session_id": session_id,
                            "model_id": model_id,
                            "context_mode": context_mode,
                        })

                        # Auto-bootstrap: tell the agent to read its .agent/ files
                        # This is what makes the walkie-talkie system work on startup
                        try:
                            async for event in session.bootstrap():
                                await ws.send_json(event)
                        except Exception as boot_err:
                            logger.warning("DunkStack bootstrap failed (non-fatal): %s", boot_err)

                    except Exception as e:
                        logger.exception("Failed to start DunkStack agent session")
                        await ws.send_json({
                            "type": "error",
                            "content": f"Failed to start agent: {str(e)}",
                        })
                        # Clean up failed session
                        _agent_sessions.pop(session_id, None)
                        current_session_id = None

                elif msg_type == "message":
                    # Send a message to the running agent
                    content = msg.get("content", "").strip()
                    if not content:
                        await ws.send_json({"type": "error", "content": "Empty message."})
                        continue

                    if not current_session_id or current_session_id not in _agent_sessions:
                        await ws.send_json({
                            "type": "error",
                            "content": "No agent session running. Start an agent first.",
                        })
                        continue

                    session = _agent_sessions[current_session_id]

                    # Also write to from_human.md for the file-based record
                    _ensure_agent_dir()
                    path = _agent_dir() / "comms" / "from_human.md"
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                    entry_text = f"\n\n## [{timestamp}] Message\n{content}\n"
                    if path.exists():
                        existing = path.read_text(encoding="utf-8")
                    else:
                        existing = "# Human Messages\n> Human writes messages here.\n"
                    path.write_text(existing + entry_text, encoding="utf-8")

                    # Stream agent response
                    try:
                        async for event in session.send_message(content):
                            await ws.send_json(event)

                            # Also write agent text responses to to_human.md
                            if event.get("type") == "response_done":
                                pass  # Will write accumulated text below

                    except Exception as e:
                        logger.exception("Error during DunkStack agent message")
                        await ws.send_json({
                            "type": "error",
                            "content": f"Agent error: {str(e)}",
                        })
                        await ws.send_json({"type": "response_done"})

                elif msg_type == "stop_agent":
                    # Stop the running agent session
                    if current_session_id and current_session_id in _agent_sessions:
                        session = _agent_sessions.pop(current_session_id)
                        try:
                            await session.close()
                        except Exception as e:
                            logger.warning("Error stopping DunkStack session: %s", e)
                        current_session_id = None
                        await ws.send_json({"type": "agent_stopped"})
                    else:
                        await ws.send_json({"type": "error", "content": "No agent session running."})

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("DunkStack WebSocket error: %s", e)
    finally:
        # Clean up agent session on disconnect
        if current_session_id and current_session_id in _agent_sessions:
            session = _agent_sessions.pop(current_session_id)
            try:
                await session.close()
            except Exception as e:
                logger.warning("Error closing DunkStack session on disconnect: %s", e)

        if ws in _ws_connections:
            _ws_connections.remove(ws)
        logger.info("DunkStack WebSocket disconnected (total: %d)", len(_ws_connections))


# ============================================================================
# Agent Process Management
# ============================================================================

# In-memory agent process state (one agent per DunkStack session)
_agent_process: Optional[subprocess.Popen] = None
_agent_output_task: Optional[asyncio.Task] = None
_agent_status: str = "stopped"  # stopped | running | crashed
_agent_output_lines: list[str] = []  # Rolling buffer of output lines
_AGENT_OUTPUT_MAX = 2000  # Keep last N lines


class AgentStartRequest(BaseModel):
    """Request to start the DunkStack coding agent."""
    project_name: Optional[str] = None
    model: Optional[str] = None  # claude-opus-4-6 | claude-sonnet-4-6


def _get_project_dir(project_name: Optional[str]) -> Path:
    """Resolve project directory from name, or fall back to ROOT_DIR."""
    if project_name:
        from ..utils.project_helpers import get_project_path
        project_dir = get_project_path(project_name)
        if project_dir and project_dir.exists():
            return project_dir
    return ROOT_DIR


async def _stream_agent_output() -> None:
    """Stream agent subprocess output to WebSocket clients and buffer."""
    global _agent_status, _agent_process
    if not _agent_process or not _agent_process.stdout:
        return

    try:
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, _agent_process.stdout.readline)
            if not line:
                break

            decoded = line.decode("utf-8", errors="replace").rstrip()

            # Buffer the output line
            _agent_output_lines.append(decoded)
            if len(_agent_output_lines) > _AGENT_OUTPUT_MAX:
                _agent_output_lines.pop(0)

            # Broadcast to WebSocket clients
            await _broadcast({
                "type": "agent_output",
                "line": decoded,
            })

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.warning("Agent output streaming error: %s", e)
    finally:
        if _agent_process and _agent_process.poll() is not None:
            exit_code = _agent_process.returncode
            if exit_code != 0 and _agent_status == "running":
                _agent_status = "crashed"
            elif _agent_status == "running":
                _agent_status = "stopped"

            await _broadcast({
                "type": "agent_status",
                "status": _agent_status,
                "exit_code": exit_code,
            })


@router.post("/agent/start")
async def start_agent(req: AgentStartRequest = AgentStartRequest()):
    """Start the DunkStack coding agent for a project."""
    global _agent_process, _agent_output_task, _agent_status, _agent_output_lines

    if _agent_status == "running" and _agent_process and _agent_process.poll() is None:
        return {"status": "already_running", "pid": _agent_process.pid}

    project_dir = _get_project_dir(req.project_name)

    # Determine model and billing from current preset
    model = req.model
    if not model:
        # Default: use model from current preset
        model = "claude-sonnet-4-6"  # safe default

    billing_mode = "subscription" if _token_state["model_limit"] <= 200_000 else "api"

    # Build command
    cmd = [
        sys.executable,
        "-u",  # Unbuffered output
        str(ROOT_DIR / "dunkstack_agent.py"),
        "--project-dir", str(project_dir.resolve()),
        "--model", model,
        "--billing-mode", billing_mode,
    ]

    # Build subprocess environment with API provider settings
    from registry import get_effective_sdk_env
    api_env = get_effective_sdk_env(force_subscription=billing_mode == "subscription")
    subprocess_env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        **api_env,
    }

    try:
        popen_kwargs: dict[str, Any] = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "cwd": str(project_dir),
            "env": subprocess_env,
        }
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        _agent_process = subprocess.Popen(cmd, **popen_kwargs)
        _agent_status = "running"
        _agent_output_lines.clear()

        # Start output streaming
        _agent_output_task = asyncio.create_task(_stream_agent_output())

        logger.info("DunkStack agent started: PID %d, project=%s, model=%s, billing=%s",
                     _agent_process.pid, project_dir, model, billing_mode)

        await _broadcast({
            "type": "agent_status",
            "status": "running",
            "pid": _agent_process.pid,
            "model": model,
            "billing_mode": billing_mode,
        })

        return {
            "status": "started",
            "pid": _agent_process.pid,
            "model": model,
            "billing_mode": billing_mode,
        }

    except Exception as e:
        logger.exception("Failed to start DunkStack agent")
        _agent_status = "crashed"
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {e}")


@router.post("/agent/stop")
async def stop_agent():
    """Stop the running DunkStack agent."""
    global _agent_process, _agent_output_task, _agent_status

    if not _agent_process or _agent_status == "stopped":
        return {"status": "not_running"}

    try:
        # Cancel output streaming
        if _agent_output_task:
            _agent_output_task.cancel()
            try:
                await _agent_output_task
            except asyncio.CancelledError:
                pass

        # Terminate the process
        pid = _agent_process.pid
        _agent_process.terminate()
        try:
            _agent_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _agent_process.kill()
            _agent_process.wait(timeout=5)

        _agent_status = "stopped"
        _agent_process = None

        logger.info("DunkStack agent stopped: PID %d", pid)

        await _broadcast({
            "type": "agent_status",
            "status": "stopped",
        })

        return {"status": "stopped", "pid": pid}

    except Exception as e:
        logger.exception("Error stopping DunkStack agent")
        _agent_status = "crashed"
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {e}")


@router.get("/agent/status")
def get_agent_status():
    """Get the DunkStack agent status."""
    global _agent_status, _agent_process

    # Check if process is still alive
    if _agent_process and _agent_process.poll() is not None:
        exit_code = _agent_process.returncode
        if _agent_status == "running":
            _agent_status = "stopped" if exit_code == 0 else "crashed"

    return {
        "status": _agent_status,
        "pid": _agent_process.pid if _agent_process and _agent_process.poll() is None else None,
        "model_limit": _token_state["model_limit"],
        "mode": _token_state["mode"],
    }


@router.get("/agent/output")
def get_agent_output(tail: int = 100):
    """Get recent agent output lines."""
    lines = _agent_output_lines[-tail:] if tail < len(_agent_output_lines) else _agent_output_lines
    return {"lines": lines, "total": len(_agent_output_lines)}
