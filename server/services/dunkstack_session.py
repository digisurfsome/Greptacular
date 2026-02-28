"""
DunkStack Coding Session
=========================

Manages Claude SDK coding agent sessions for the DunkStack file-based agent system.

The DunkStack system uses ``.agent/`` directory files for context management (working
memory, comms, bridge saves) and model preset selection.  This module provides the
coding agent that reads the file-based system prompt and performs coding work within
the project directory.

Key design decisions:

- System prompt loaded from ``.agent/system_prompt.md`` (file-based protocol)
- Full coding tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
- Bash security hooks from ``security.py`` for safe command execution
- Token usage reported back to the DunkStack ``/tokens/record`` endpoint
- PreCompact hook guides compaction toward file-based recovery
- Session registry keyed by ``project_name`` (one coding agent per project)
- Streaming via ``client.query()`` + ``client.receive_response()`` (same pattern
  as workspace_chat_session.py)
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

# Default system prompt when .agent/system_prompt.md doesn't exist.
# Provides minimal file-based protocol instructions so the agent still
# operates correctly even without the full template.
DEFAULT_SYSTEM_PROMPT = """\
You are a coding agent operating in file-based mode.
ALL substantive output is written to designated files using the Write tool.
Your conversation responses contain ONLY status confirmations (1-2 sentences max).

On startup, read .agent/index.md and .agent/working_memory.md to understand your state.
Write progress to .agent/comms/to_human.md and check .agent/comms/from_human.md for instructions."""

# Startup message sent to the agent on first turn.  Instructs it to
# bootstrap from the file-based state files before doing any work.
STARTUP_MESSAGE = """\
Begin your session. Follow the file-based operating protocol:

1. Read .agent/index.md (your file map)
2. Read .agent/working_memory.md (your current state)
3. If .agent/bridge.md has content, read it and incorporate the context
4. Read .agent/comms/from_human.md for any instructions
5. Read .agent/comms/control.md for mode signal
6. Begin working on whatever task is described

Remember: Write ALL substantive output to files. Chat responses are status-only (1-2 sentences max)."""

# Settings file path (separate from workspace to avoid collisions)
_SETTINGS_DIR = Path.home() / ".autoforge"
_SETTINGS_FILE = _SETTINGS_DIR / ".dunkstack_claude_settings.json"

# Model shorthand mapping
_MODEL_MAP = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
}


def _resolve_model_id(model: Optional[str], sdk_env: dict[str, str]) -> str:
    """Resolve a model shorthand or full ID to a concrete model identifier.

    Priority:
    1. Known shorthand ("opus", "sonnet") maps to full ID.
    2. A full model ID (contains "-") is used directly.
    3. Falls back to the environment default or Opus.
    """
    if model and model in _MODEL_MAP:
        return _MODEL_MAP[model]
    if model and "-" in model:
        return model

    # Fall back to environment or default
    from registry import DEFAULT_MODEL
    env_model = sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL") or os.getenv(
        "ANTHROPIC_DEFAULT_OPUS_MODEL"
    )
    return env_model or DEFAULT_MODEL


class DunkStackCodingSession:
    """Manages one coding agent session using the file-based DunkStack protocol.

    Creates a Claude SDK client with full tools that operates within a project
    directory, following the .agent/ file-based communication protocol.

    Lifecycle:
        1. Create via ``create_coding_session()``
        2. Iterate ``start()`` to initialize and send the bootstrap message
        3. Iterate ``send_message()`` to inject follow-up instructions
        4. Call ``stop()`` to clean up resources
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
                content = prompt_path.read_text(encoding="utf-8")
                if content.strip():
                    return content
            except Exception as e:
                logger.warning("Failed to read system_prompt.md: %s", e)
        logger.info("Using default DunkStack system prompt (no .agent/system_prompt.md)")
        return DEFAULT_SYSTEM_PROMPT

    def _is_subscription_mode(self) -> bool:
        """200K context = subscription (free), 1M = API billing."""
        return self.context_window <= 200_000

    async def start(self) -> AsyncGenerator[dict[str, Any], None]:
        """Initialize the Claude SDK client, send the bootstrap message, and stream.

        Creates the client with bash security hooks and a PreCompact hook,
        enters the async context, then sends ``STARTUP_MESSAGE`` so the agent
        reads its file-based state and begins working.

        Yields:
            Event dicts:
            - ``{"type": "agent_status", "status": str}``
            - ``{"type": "text", "content": str}``
            - ``{"type": "tool_call", "tool": str, "input": dict}``
            - ``{"type": "result", "usage": dict}``
            - ``{"type": "response_done"}``
            - ``{"type": "error", "content": str}``
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
            _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(security_settings, f, indent=2)
        except Exception as e:
            self._status = "error"
            self._error = str(e)
            yield {"type": "error", "content": f"Failed to write settings: {e}"}
            return

        # ── SDK environment (billing mode) ──
        try:
            from registry import get_effective_sdk_env

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

        # ── Bash security hook scoped to the project directory ──
        project_dir_str = str(self.project_dir)

        async def bash_hook_with_context(
            input_data: Any, tool_use_id: Any = None, context: Any = None
        ) -> dict[str, Any]:
            if context is None:
                context = {}
            context["project_dir"] = project_dir_str
            result: dict[str, Any] = await bash_security_hook(input_data, tool_use_id, context)
            return result

        # ── PreCompact hook for file-based recovery ──
        async def pre_compact_hook(
            input_data: Any, tool_use_id: Any = None, context: Any = None
        ) -> SyncHookJSONOutput:
            """Guide compaction to preserve file-based protocol awareness."""
            logger.info("[DunkStack] Context compaction triggered")
            return SyncHookJSONOutput(
                hookSpecificOutput={  # type: ignore[typeddict-item]
                    "hookEventName": "PreCompact",
                    "customInstructions": (
                        "## DunkStack Compaction Guidelines\n"
                        "After compaction, re-read .agent/index.md and "
                        ".agent/working_memory.md.\n"
                        "These files are the source of truth, not conversation "
                        "history.\n\n"
                        "## DISCARD\n"
                        "- Full file contents from Read results (keep: "
                        "'Read file X')\n"
                        "- Large Grep/Glob outputs (keep: 'Found N matches')\n"
                        "- Verbose Bash output (keep: command + success/failure)\n\n"
                        "## PRESERVE\n"
                        "- Current task and progress state\n"
                        "- Files created or modified (paths only)\n"
                        "- Unresolved errors or blockers\n"
                    ),
                }
            )

        hooks: dict[str, list[HookMatcher]] = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
            ],
            "PreCompact": [
                HookMatcher(hooks=[pre_compact_hook]),
            ],
        }

        # ── Detect alternative API mode ──
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex

        use_1m_beta = self.context_window > 200_000 and not is_alternative_api

        # ── Create Claude SDK client ──
        system_cli = shutil.which("claude")

        try:
            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=self.model_id,
                    cli_path=system_cli,
                    system_prompt=system_prompt,
                    setting_sources=["project", "user"],
                    allowed_tools=DUNKSTACK_TOOLS,
                    permission_mode="acceptEdits",
                    max_turns=50,
                    cwd=str(self.project_dir),
                    settings=str(_SETTINGS_FILE.resolve()),
                    env=sdk_env,
                    hooks=hooks,
                    betas=["context-1m-2025-08-07"] if use_1m_beta else [],
                )
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
            return

        # ── Send bootstrap message and stream the response ──
        async for event in self._stream_response(STARTUP_MESSAGE):
            yield event

        yield {"type": "response_done"}

    async def send_message(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Send a follow-up message to the running agent and stream the response.

        Use this to inject human messages or additional instructions after the
        initial bootstrap.

        Yields:
            Event dicts (same types as ``start()``).
        """
        if not self.client or not self._client_entered:
            yield {"type": "error", "content": "Agent not started. Call start() first."}
            return

        if self._status != "running":
            yield {"type": "error", "content": f"Agent not running (status: {self._status})"}
            return

        async for event in self._stream_response(message):
            yield event

        yield {"type": "response_done"}

    async def _stream_response(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Send a message and yield typed events from the SDK response stream.

        Uses ``client.query()`` + ``client.receive_response()`` -- the same
        streaming pattern as workspace_chat_session.py.  Handles AssistantMessage
        (TextBlock, ToolUseBlock), UserMessage (ToolResultBlock), and ResultMessage.

        Args:
            message: The message to send to the agent.

        Yields:
            text, tool_call, tool_result, result, or error events.
        """
        if not self.client:
            return

        # Send the query with a generous timeout (Opus can be slow to accept)
        try:
            await asyncio.wait_for(self.client.query(message), timeout=120)
        except asyncio.TimeoutError:
            logger.error("Timeout (120s) waiting for DunkStack query acceptance")
            yield {"type": "error", "content": "Agent did not accept request within 120s."}
            return
        except Exception as e:
            logger.exception("Error sending query to DunkStack agent")
            yield {"type": "error", "content": f"Query error: {e}"}
            return

        # Stream the response.  Opus can take 30-60s for the first token.
        first_token_timeout = 300  # 5 minutes for first token
        ongoing_timeout = 300  # 5 minutes between subsequent tokens
        first_token_received = False

        try:
            response_iter = self.client.receive_response().__aiter__()
            while True:
                try:
                    timeout = first_token_timeout if not first_token_received else ongoing_timeout
                    msg = await asyncio.wait_for(response_iter.__anext__(), timeout=timeout)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    label = "first token" if not first_token_received else "next token"
                    logger.error("Timeout waiting for %s from DunkStack agent", label)
                    yield {"type": "error", "content": f"Response stream timed out ({label})."}
                    return

                first_token_received = True
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "TextBlock" and hasattr(block, "text"):
                            text = block.text
                            if text:
                                yield {"type": "text", "content": text}

                        elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                            yield {
                                "type": "tool_call",
                                "tool": block.name,
                                "input": getattr(block, "input", {}),
                            }

                # UserMessage contains ToolResultBlock events
                elif msg_type == "UserMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "ToolResultBlock":
                            result_content = str(getattr(block, "content", ""))
                            is_error = getattr(block, "is_error", False)
                            # Truncate very large results to avoid flooding the WebSocket
                            truncated = result_content[:2000] if len(result_content) > 2000 else result_content
                            yield {
                                "type": "tool_result",
                                "output": truncated,
                                "is_error": is_error,
                            }

                # ResultMessage is the SDK's final summary with actual API usage
                elif msg_type == "ResultMessage":
                    usage = getattr(msg, "usage", None) or {}
                    cost_usd = getattr(msg, "total_cost_usd", None)
                    num_turns = getattr(msg, "num_turns", None)

                    api_input = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
                    api_output = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
                    api_cache_create = (
                        usage.get("cache_creation_input_tokens", 0) if isinstance(usage, dict) else 0
                    )
                    api_cache_read = (
                        usage.get("cache_read_input_tokens", 0) if isinstance(usage, dict) else 0
                    )

                    result_data = {
                        "input_tokens": api_input,
                        "output_tokens": api_output,
                        "cache_creation_tokens": api_cache_create,
                        "cache_read_tokens": api_cache_read,
                        "total_cost_usd": cost_usd or 0.0,
                        "num_turns": num_turns,
                    }

                    logger.info(
                        "DunkStack ResultMessage: cost=$%.4f input=%d output=%d "
                        "cache_create=%d cache_read=%d turns=%s",
                        cost_usd or 0.0, api_input, api_output,
                        api_cache_create, api_cache_read, num_turns,
                    )

                    yield {"type": "result", "usage": result_data}

                    # Report token usage to the DunkStack token tracking endpoint
                    await self._report_token_usage(result_data)

        except Exception as e:
            logger.exception("Error streaming DunkStack agent response")
            yield {"type": "error", "content": f"Streaming error: {e}"}

    async def _report_token_usage(self, usage: dict[str, Any]) -> None:
        """Report token usage to the DunkStack token tracking endpoint.

        Calls the in-process ``record_tokens`` function from the dunkstack router
        rather than making an HTTP request, avoiding network overhead.
        """
        try:
            from ..routers.dunkstack import TokenSnapshot, record_tokens

            snapshot = TokenSnapshot(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cache_read_tokens=usage.get("cache_read_tokens", 0),
                cache_creation_tokens=usage.get("cache_creation_tokens", 0),
                total_cost_usd=usage.get("total_cost_usd", 0.0),
            )
            await record_tokens(snapshot, project_name=self.project_name)
        except Exception as e:
            logger.warning("Failed to report token usage to DunkStack: %s", e)

    async def stop(self) -> None:
        """Stop the agent and clean up the SDK client."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing DunkStack client: %s", e)
            finally:
                self._client_entered = False
                self.client = None

        self._status = "stopped"
        logger.info("DunkStack coding agent stopped for %s", self.project_name)

    def get_status(self) -> dict[str, Any]:
        """Get the current session status as a serializable dict."""
        return {
            "status": self._status,
            "project_name": self.project_name,
            "model_id": self.model_id,
            "context_window": self.context_window,
            "billing": "subscription" if self._is_subscription_mode() else "api",
            "created_at": self.created_at.isoformat(),
            "error": self._error,
        }


# =============================================================================
# Session Registry (thread-safe, keyed by project_name)
# =============================================================================

_sessions: dict[str, DunkStackCodingSession] = {}
_sessions_lock = threading.Lock()


def get_coding_session(project_name: str) -> Optional[DunkStackCodingSession]:
    """Get the active coding session for a project."""
    with _sessions_lock:
        return _sessions.get(project_name)


async def create_coding_session(
    project_name: str,
    project_dir: Path,
    model_id: str = "claude-opus-4-6",
    context_window: int = 200_000,
) -> DunkStackCodingSession:
    """Create a new coding session, stopping any existing one for the same project.

    Resolves model shorthands ("opus", "sonnet") to full IDs and applies any
    environment-level model overrides.

    Args:
        project_name: Registered name of the project.
        project_dir: Absolute path to the project directory.
        model_id: Full model ID or shorthand ("opus", "sonnet").
        context_window: Context window size (200000 or 1000000).

    Returns:
        The newly created (but not yet started) session.
    """
    # Resolve model shorthand to full ID
    from registry import get_effective_sdk_env

    sdk_env = get_effective_sdk_env(force_subscription=context_window <= 200_000)
    resolved_model = _resolve_model_id(model_id, sdk_env)

    old_session: Optional[DunkStackCodingSession] = None

    with _sessions_lock:
        old_session = _sessions.pop(project_name, None)
        session = DunkStackCodingSession(
            project_name=project_name,
            project_dir=project_dir,
            model_id=resolved_model,
            context_window=context_window,
        )
        _sessions[project_name] = session

    # Stop old session outside lock to avoid deadlock
    if old_session:
        try:
            await old_session.stop()
        except Exception as e:
            logger.warning("Error stopping old DunkStack session for %s: %s", project_name, e)

    return session


async def remove_coding_session(project_name: str) -> None:
    """Remove and stop a coding session.

    Args:
        project_name: The project name to remove.
    """
    session: Optional[DunkStackCodingSession] = None

    with _sessions_lock:
        session = _sessions.pop(project_name, None)

    if session:
        try:
            await session.stop()
        except Exception as e:
            logger.warning("Error stopping DunkStack session for %s: %s", project_name, e)


def list_coding_sessions() -> list[dict[str, Any]]:
    """List all active coding sessions with their status dicts."""
    with _sessions_lock:
        return [s.get_status() for s in _sessions.values()]


async def cleanup_all_coding_sessions() -> None:
    """Stop all active sessions. Called on server shutdown."""
    sessions_to_stop: list[DunkStackCodingSession] = []

    with _sessions_lock:
        sessions_to_stop = list(_sessions.values())
        _sessions.clear()

    for session in sessions_to_stop:
        try:
            await session.stop()
        except Exception as e:
            logger.warning(
                "Error stopping DunkStack session for %s: %s",
                session.project_name, e,
            )
