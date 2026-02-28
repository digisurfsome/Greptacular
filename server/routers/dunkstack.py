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
from typing import Any, Optional

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
    """Append a message to from_human.md (human → agent communication)."""
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

    # Broadcast the new message to connected clients
    await _broadcast({
        "type": "comms_update",
        "channel": "from_human",
        "timestamp": timestamp,
        "title": title,
        "content": msg.content,
    })

    return {"status": "ok", "timestamp": timestamp}


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
    _token_state["entries"] = []
    _token_state["cumulative"] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
        "total_cost_usd": 0.0,
        "api_calls": 0,
    }

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
# WebSocket - Real-time updates
# ============================================================================


@router.websocket("/ws")
async def dunkstack_websocket(ws: WebSocket):
    """WebSocket for real-time DunkStack updates (token gauge, comms, control)."""
    await ws.accept()
    _ws_connections.append(ws)
    logger.info("DunkStack WebSocket connected (total: %d)", len(_ws_connections))

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

                # Handle client messages
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong"})

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
