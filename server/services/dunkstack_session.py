"""
DunkStack Coding Session
=========================

Manages a coding agent session for the DunkStack file-based context system.
This is the missing piece: an actual Claude SDK agent that reads .agent/ files,
follows the file-based protocol, and does the coding work.

The agent:
- Loads system_prompt.md as its operating protocol
- Reads working_memory.md, index.md on startup
- Writes all substantive output to .agent/ files
- Communicates via from_human.md / to_human.md
- Has full coding tools (Read, Write, Edit, Bash, Glob, Grep)
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher, SyncHookJSONOutput

_root_str = str(Path(__file__).parent.parent.parent)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from security import bash_security_hook  # noqa: E402

logger = logging.getLogger(__name__)

# Full set of coding tools for the DunkStack agent
DUNKSTACK_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]

# Default system prompt when .agent/system_prompt.md doesn't exist
DEFAULT_SYSTEM_PROMPT = """You are a coding agent operating in file-based mode.
ALL substantive output is written to designated files using the Write tool.
Your conversation responses contain ONLY status confirmations (1-2 sentences max).

On startup, read .agent/index.md and .agent/working_memory.md to understand your state.
Write progress to .agent/comms/to_human.md and check .agent/comms/from_human.md for instructions."""

# Startup message sent to the agent on first turn
STARTUP_MESSAGE = """Begin your session. Follow the file-based operating protocol:

1. Read .agent/index.md (your file map)
2. Read .agent/working_memory.md (your current state)
3. If .agent/bridge.md has content, read it and incorporate the context
4. Read .agent/comms/from_human.md for any instructions
5. Read .agent/comms/control.md for mode signal
6. Begin working on whatever task is described

Remember: Write ALL substantive output to files. Chat responses are status-only (1-2 sentences max)."""


class DunkStackCodingSession:
    """Manages one coding agent session using the file-based DunkStack protocol.

    Creates a Claude SDK client with full tools that operates within a project
    directory, following the .agent/ file-based communication protocol.
    """

    def __init__(
        self,
        project_name: str,
        project_dir: Path,
        model_id: str = "claude-opus-4-6",
        context_window: int = 200_000,
    ):
        self.project_name = project_name
        self.project_dir = project_dir
        self.model_id = model_id
        self.context_window = context_window
        self.created_at = datetime.now(tz=timezone.utc)

        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False
        self._status: str = "stopped"  # stopped | starting | running | error
        self._error: Optional[str] = None

        # Track the settings file for cleanup
        self._settings_file: Optional[Path] = None

    @property
    def status(self) -> str:
        return self._status

    @property
    def error(self) -> Optional[str]:
        return self._error

    def _load_system_prompt(self) -> str:
        """Load the system prompt from .agent/system_prompt.md or use default."""
        prompt_path = self.project_dir / ".agent" / "system_prompt.md"
        if prompt_path.is_file():
            try:
                return prompt_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to read system_prompt.md: %s", e)
        return DEFAULT_SYSTEM_PROMPT

    def _is_subscription_mode(self) -> bool:
        """200K context = subscription (free), 1M = API billing."""
        return self.context_window <= 200_000

    async def start(self) -> AsyncGenerator[dict[str, Any], None]:
        """Initialize the Claude SDK client and prepare for messaging.

        Yields status events as the agent starts up.
        """
        self._status = "starting"
        self._error = None

        yield {"type": "agent_status", "status": "starting"}

        # ── Security settings file ──
        try:
            security_settings = {
                "sandbox": {"enabled": False},
                "permissions": {
                    "defaultMode": "acceptEdits",
                    "allow": DUNKSTACK_TOOLS,
                },
            }
            settings_dir = Path.home() / ".autoforge"
            settings_dir.mkdir(parents=True, exist_ok=True)
            self._settings_file = settings_dir / ".dunkstack_claude_settings.json"
            with open(self._settings_file, "w") as f:
                json.dump(security_settings, f, indent=2)
        except Exception as e:
            self._status = "error"
            self._error = str(e)
            yield {"type": "error", "content": f"Failed to write settings: {e}"}
            return

        # ── SDK environment (billing mode) ──
        try:
            from registry import DEFAULT_MODEL, get_effective_sdk_env

            force_sub = self._is_subscription_mode()
            sdk_env = get_effective_sdk_env(force_subscription=force_sub)
            billing = "subscription" if force_sub else "API key"
            logger.info(
                "DunkStack agent billing: %s (context=%dK, model=%s)",
                billing, self.context_window // 1000, self.model_id,
            )
        except Exception as e:
            self._status = "error"
            self._error = str(e)
            yield {"type": "error", "content": f"Failed to load SDK config: {e}"}
            return

        # ── System prompt ──
        system_prompt = self._load_system_prompt()

        # ── Bash security hook ──
        project_dir_str = str(self.project_dir)

        async def bash_hook_with_context(input_data, tool_use_id=None, context=None):
            if context is None:
                context = {}
            context["project_dir"] = project_dir_str
            return await bash_security_hook(input_data, tool_use_id, context)

        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
            ],
        }

        # ── Detect alternative API mode ──
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex

        # ── Create Claude SDK client ──
        system_cli = shutil.which("claude")

        try:
            shared_opts = dict(
                model=self.model_id,
                cli_path=system_cli,
                system_prompt=system_prompt,
                setting_sources=["project", "user"],
                allowed_tools=DUNKSTACK_TOOLS,
                permission_mode="acceptEdits",
                max_turns=50,
                cwd=str(self.project_dir),
                settings=str(self._settings_file.resolve()),
                env=sdk_env,
                hooks=hooks,
                betas=(
                    []
                    if is_alternative_api or self._is_subscription_mode()
                    else ["context-1m-2025-08-07"]
                ),
            )

            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(**shared_opts)
            )

            logger.info("DunkStack: entering Claude client context...")
            try:
                await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            except asyncio.TimeoutError:
                self._status = "error"
                self._error = "Claude CLI did not start within 60 seconds"
                yield {
                    "type": "error",
                    "content": (
                        "The Claude CLI did not start within 60 seconds. "
                        "If using subscription (200K) mode, ensure you're logged in "
                        "(run `claude login`). Or switch to 1M API mode."
                    ),
                }
                return

            self._client_entered = True
            self._status = "running"
            logger.info("DunkStack coding agent ready for %s", self.project_name)
            yield {"type": "agent_status", "status": "running", "model": self.model_id}

        except Exception as e:
            self._status = "error"
            self._error = str(e)
            logger.exception("Failed to create DunkStack Claude client")
            yield {"type": "error", "content": f"Failed to start agent: {e}"}

    async def send_message(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Send a message to the running agent and stream response events.

        Yields events:
        - {"type": "text", "content": str} - Text output from the agent
        - {"type": "tool_use", "tool": str, "input": str} - Tool call
        - {"type": "tool_result", "tool": str, "output": str} - Tool result
        - {"type": "response_done"} - Agent finished responding
        - {"type": "token_usage", ...} - Token usage from the response
        - {"type": "error", "content": str} - Error
        """
        if not self.client or not self._client_entered:
            yield {"type": "error", "content": "Agent not started"}
            return

        try:
            result = await self.client.process_message(message)

            # Process the result message
            if hasattr(result, "content"):
                for block in result.content:
                    block_type = getattr(block, "type", "unknown")

                    if block_type == "text":
                        yield {"type": "text", "content": block.text}
                    elif block_type == "tool_use":
                        tool_name = getattr(block, "name", "unknown")
                        tool_input = getattr(block, "input", {})
                        yield {
                            "type": "tool_use",
                            "tool": tool_name,
                            "input": str(tool_input)[:500],
                        }
                    elif block_type == "tool_result":
                        yield {
                            "type": "tool_result",
                            "output": str(getattr(block, "content", ""))[:500],
                        }

            # Extract token usage if available
            if hasattr(result, "usage"):
                usage = result.usage
                yield {
                    "type": "token_usage",
                    "input_tokens": getattr(usage, "input_tokens", 0),
                    "output_tokens": getattr(usage, "output_tokens", 0),
                    "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
                    "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
                }

            yield {"type": "response_done"}

        except Exception as e:
            logger.exception("Error processing message in DunkStack session")
            yield {"type": "error", "content": str(e)}

    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing DunkStack client: %s", e)
            finally:
                self._client_entered = False
                self.client = None

        # Clean up settings file
        if self._settings_file and self._settings_file.exists():
            try:
                self._settings_file.unlink()
            except Exception:
                pass

        self._status = "stopped"
        logger.info("DunkStack coding agent stopped for %s", self.project_name)

    def get_status(self) -> dict[str, Any]:
        """Get the current session status."""
        return {
            "status": self._status,
            "project_name": self.project_name,
            "model_id": self.model_id,
            "context_window": self.context_window,
            "billing": "subscription" if self._is_subscription_mode() else "api",
            "created_at": self.created_at.isoformat(),
            "error": self._error,
        }


# ── Session Registry (thread-safe) ──────────────────────────────────────

_sessions: dict[str, DunkStackCodingSession] = {}
_sessions_lock = threading.Lock()


def get_coding_session(project_name: str) -> Optional[DunkStackCodingSession]:
    """Get the active coding session for a project."""
    with _sessions_lock:
        return _sessions.get(project_name)


def create_coding_session(
    project_name: str,
    project_dir: Path,
    model_id: str = "claude-opus-4-6",
    context_window: int = 200_000,
) -> DunkStackCodingSession:
    """Create a new coding session, replacing any existing one."""
    with _sessions_lock:
        old = _sessions.pop(project_name, None)

    # Stop old session outside lock to avoid deadlock
    if old:
        asyncio.ensure_future(_safe_stop(old))

    session = DunkStackCodingSession(
        project_name=project_name,
        project_dir=project_dir,
        model_id=model_id,
        context_window=context_window,
    )

    with _sessions_lock:
        _sessions[project_name] = session

    return session


def remove_coding_session(project_name: str) -> Optional[DunkStackCodingSession]:
    """Remove and return a session (caller should call stop())."""
    with _sessions_lock:
        return _sessions.pop(project_name, None)


def list_coding_sessions() -> list[dict[str, Any]]:
    """List all active coding sessions."""
    with _sessions_lock:
        return [s.get_status() for s in _sessions.values()]


async def _safe_stop(session: DunkStackCodingSession) -> None:
    """Safely stop a session, logging errors."""
    try:
        await session.stop()
    except Exception as e:
        logger.warning("Error stopping old DunkStack session: %s", e)


async def cleanup_all_coding_sessions() -> None:
    """Stop all active sessions. Called on server shutdown."""
    with _sessions_lock:
        sessions = list(_sessions.values())
        _sessions.clear()
    for s in sessions:
        await _safe_stop(s)
