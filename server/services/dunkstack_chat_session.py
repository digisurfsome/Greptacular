"""
DunkStack Chat Session
======================

Manages a DunkStack coding agent session with full read/write Claude capabilities.
Integrates the Claude SDK client into the DunkStack file-based context mechanism.

Key differences from WorkspaceChatSession:
- No conversation persistence in SQLite (DunkStack uses file-based context)
- Token usage reported to DunkStack's in-memory gauge (via callback)
- System prompt includes DunkStack context mechanism instructions
- Simpler lifecycle: start → send_message → close
"""

import asyncio
import json
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher, SyncHookJSONOutput
from dotenv import load_dotenv

# Ensure project root is on sys.path before importing root-level modules
_root_str = str(Path(__file__).parent.parent.parent)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from security import bash_security_hook  # noqa: E402

load_dotenv()

logger = logging.getLogger(__name__)

# Tools available to the DunkStack agent.
DUNKSTACK_BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]


def get_dunkstack_system_prompt(
    working_directory: str,
    model: str = "",
    context_mode: str = "1m",
) -> str:
    """Generate the system prompt for the DunkStack agent.

    Loads the file-based operating protocol from .agent/system_prompt.md if it
    exists in the working directory, then prepends the agent identity header.

    Args:
        working_directory: Absolute path to the agent's working directory.
        model: The model ID being used (e.g. "claude-opus-4-6").
        context_mode: Context window mode -- "1m" or "200k".

    Returns:
        A system prompt string.
    """
    context_tokens = "1,000,000" if context_mode == "1m" else "200,000"
    MODEL_DISPLAY_NAMES: dict[str, str] = {
        "claude-opus-4-6": "Claude Opus 4.6",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    }
    display_name = MODEL_DISPLAY_NAMES.get(model or "", model or "Claude")
    model_id_note = f" (model ID: {model})" if model else ""

    # Load the file-based operating protocol if it exists
    file_protocol = ""
    protocol_path = Path(working_directory) / ".agent" / "system_prompt.md"
    if protocol_path.is_file():
        try:
            file_protocol = protocol_path.read_text(encoding="utf-8")
            logger.info("Loaded DunkStack file-based protocol from %s", protocol_path)
        except Exception as e:
            logger.warning("Failed to load file-based protocol: %s", e)

    identity = f"""You are an expert coding agent ({display_name}{model_id_note}, {context_tokens} token context).
Working directory: {working_directory}

You are the DunkStack agent — a specialist coding assistant with deep expertise in the codebase you're working with.

## Core Rules
- Read files before editing. Preserve existing code style.
- Use absolute paths. Prefer Glob/Grep over bash find/grep.
- After completing edits, commit changes: `git add` only changed files (never -A), write a clear commit message, do NOT push.
- Report which files changed, the commit hash, and branch name.

## Context Efficiency
You have a {context_tokens}-token context window. Be efficient:
- Don't re-read files you've already read unless they may have changed.
- Summarize large outputs rather than quoting them in full.
- Focus on the task at hand — don't explore tangential code paths."""

    if file_protocol:
        return identity + "\n\n---\n\n" + file_protocol
    return identity


class DunkStackChatSession:
    """Manages a DunkStack coding agent session with Claude SDK.

    Provides the actual AI agent backend for DunkStack. Creates a real
    ClaudeSDKClient, processes messages through the Claude API, and reports
    token usage to the DunkStack token gauge.
    """

    def __init__(
        self,
        session_id: str,
        model_id: str = "claude-opus-4-6",
        working_directory: Optional[str] = None,
        context_mode: str = "1m",
        effort: str = "high",
        on_token_usage: Optional[Any] = None,
    ):
        """Initialize the DunkStack chat session.

        Args:
            session_id: Unique identifier for this session.
            model_id: Full model ID (e.g. "claude-opus-4-6", "claude-sonnet-4-6").
            working_directory: Absolute path for the agent's cwd.
            context_mode: Context window size -- "1m" or "200k".
            effort: Thinking effort level -- "low", "medium", "high".
            on_token_usage: Optional async callback for reporting token usage.
                Called with (input_tokens, output_tokens, cache_read, cache_create, cost_usd).
        """
        self.session_id = session_id
        self.model_id = model_id
        self.working_directory = working_directory or str(Path.home())
        self.context_mode = context_mode
        self.effort = effort
        self.on_token_usage = on_token_usage

        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False

        # Auth state for mid-session fallback
        self._force_sub: bool = False
        self._shared_opts: Optional[dict[str, Any]] = None
        self._is_alternative_api: bool = False

        # Mapping from tool_use_id to tool name for readable logging.
        self._tool_use_id_to_name: dict[str, str] = {}

    async def _fallback_to_api_key(self) -> bool:
        """Tear down the current client and recreate with API key billing.

        Called mid-session when subscription OAuth expires during a query.
        Returns True if the fallback succeeded (new client is ready).
        """
        if not self._shared_opts:
            logger.warning("DunkStack: cannot fall back to API key — no saved shared_opts")
            return False

        logger.warning("DunkStack: subscription auth expired, falling back to API key")

        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_entered = False
            self.client = None

        try:
            from registry import get_effective_sdk_env

            sdk_env = get_effective_sdk_env(force_subscription=False)
            self._force_sub = False
            if self.effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self.effort

            self._shared_opts["env"] = sdk_env
            if not self._is_alternative_api:
                self._shared_opts["betas"] = ["context-1m-2025-08-07"]

            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=self.effort, **self._shared_opts)
                )
            except TypeError:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**self._shared_opts)
                )

            await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            self._client_entered = True
            logger.info("DunkStack client recreated with API key billing")
            return True
        except Exception:
            logger.exception("DunkStack API key fallback failed")
            self._client_entered = False
            self.client = None
            return False

    async def _fallback_to_subscription(self) -> bool:
        """Tear down the current client and recreate with subscription OAuth.

        Called when API key billing fails and the user may have refreshed
        their OAuth token via ``claude login``.
        """
        if not self._shared_opts:
            logger.warning("DunkStack: cannot fall back to subscription — no saved shared_opts")
            return False

        logger.warning("DunkStack: API key failed, trying subscription OAuth")

        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_entered = False
            self.client = None

        try:
            from registry import get_effective_sdk_env

            sdk_env = get_effective_sdk_env(force_subscription=True)
            self._force_sub = True
            if self.effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self.effort

            self._shared_opts["env"] = sdk_env
            self._shared_opts["betas"] = []

            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=self.effort, **self._shared_opts)
                )
            except TypeError:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**self._shared_opts)
                )

            await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            self._client_entered = True
            logger.info("DunkStack client recreated with subscription OAuth")
            return True
        except Exception:
            logger.exception("DunkStack subscription fallback failed")
            self._client_entered = False
            self.client = None
            return False

    async def close(self) -> None:
        """Clean up resources and close the Claude client."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("Error closing DunkStack client for session %s: %s", self.session_id, e)
            finally:
                self._client_entered = False
                self.client = None

    async def start(self) -> AsyncGenerator[dict, None]:
        """Initialize the session with the Claude SDK client.

        Creates the SDK client with the selected model, security hooks,
        and appropriate billing mode.

        Yields:
            Message chunks:
            - {"type": "text", "content": str}
            - {"type": "response_done"}
            - {"type": "error", "content": str}
        """
        # Security settings
        try:
            security_settings: dict = {
                "sandbox": {"enabled": False},
                "permissions": {
                    "defaultMode": "acceptEdits",
                    "allow": DUNKSTACK_BUILTIN_TOOLS,
                },
            }
            if self.effort in ("low", "medium", "high"):
                security_settings["effortLevel"] = self.effort
                security_settings["env"] = {
                    "CLAUDE_CODE_EFFORT_LEVEL": self.effort,
                }

            settings_dir = Path.home() / ".autoforge"
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_file = settings_dir / ".dunkstack_claude_settings.json"
            with open(settings_file, "w") as f:
                json.dump(security_settings, f, indent=2)
        except Exception as e:
            logger.exception("Failed to write DunkStack security settings")
            yield {"type": "error", "content": f"Failed to write settings: {str(e)}"}
            yield {"type": "response_done"}
            return

        # SDK environment and billing
        try:
            from registry import get_effective_sdk_env

            # ALL Claude models use subscription auth — no exceptions
            force_sub = True
            self._force_sub = force_sub
            sdk_env = get_effective_sdk_env(force_subscription=force_sub)
            if self.effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self.effort

            logger.info(
                "DunkStack billing: %s (%s context, model=%s)",
                "Subscription" if force_sub else "API key",
                self.context_mode, self.model_id,
            )
        except Exception as e:
            logger.exception("Failed to load SDK environment")
            yield {"type": "error", "content": f"Failed to load configuration: {str(e)}"}
            yield {"type": "response_done"}
            return

        # System prompt
        system_prompt = get_dunkstack_system_prompt(
            self.working_directory,
            model=self.model_id,
            context_mode=self.context_mode,
        )

        # Detect alternative API mode
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex
        self._is_alternative_api = is_alternative_api

        # Bash security hook
        working_dir_str = self.working_directory

        async def bash_hook_with_context(input_data, tool_use_id=None, context=None):
            if context is None:
                context = {}
            context["project_dir"] = working_dir_str
            return await bash_security_hook(input_data, tool_use_id, context)

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

        # ── Walkie-talkie PreToolUse hook ──
        # Injects human messages from .agent/comms/from_human.md at tool-call
        # boundaries, enforces idle/continue/autopilot session control modes.
        _walkie_state: dict[str, int] = {"last_size": 0}
        _project_dir_path = Path(self.working_directory)

        # Seed last_size to current file size so we only inject NEW messages
        _from_human_init = _project_dir_path / ".agent" / "comms" / "from_human.md"
        if _from_human_init.exists():
            try:
                _walkie_state["last_size"] = _from_human_init.stat().st_size
            except Exception:
                pass

        async def walkie_talkie_hook(
            input_data: Any, tool_use_id: Any = None, context: Any = None
        ) -> SyncHookJSONOutput:
            """Check walkie-talkie for new messages and enforce session control."""
            comms_dir = _project_dir_path / ".agent" / "comms"
            from_human_path = comms_dir / "from_human.md"
            control_path = comms_dir / "control.md"

            new_messages: str | None = None
            control_mode = "continue"

            # Check for new messages (compare byte offset)
            if from_human_path.exists():
                try:
                    current_size = from_human_path.stat().st_size
                    if current_size > _walkie_state["last_size"]:
                        content = from_human_path.read_text(encoding="utf-8")
                        new_content = content[_walkie_state["last_size"]:]
                        _walkie_state["last_size"] = current_size
                        if new_content.strip():
                            new_messages = new_content.strip()
                except Exception as e:
                    logger.debug("Walkie-talkie read error: %s", e)

            # Check control mode
            if control_path.exists():
                try:
                    raw = control_path.read_text(encoding="utf-8").strip().lower()
                    for line in raw.splitlines():
                        if line.startswith("mode:"):
                            mode_val = line.split(":", 1)[1].strip()
                            if mode_val in ("idle", "continue", "autopilot"):
                                control_mode = mode_val
                            break
                except Exception:
                    pass

            # IDLE mode: block the tool call and wait
            if control_mode == "idle":
                reason = (
                    "SESSION MODE: IDLE. The human has paused your session. "
                    "Do NOT proceed with any work. "
                )
                if new_messages:
                    reason += (
                        f"New walkie-talkie message:\n\n{new_messages}\n\n"
                        "Read and acknowledge this message by writing to "
                        ".agent/comms/to_human.md, then wait for mode change."
                    )
                else:
                    reason += (
                        "Check .agent/comms/control.md periodically. "
                        "Resume work when mode changes to 'continue' or 'autopilot'."
                    )
                await asyncio.sleep(10)
                return SyncHookJSONOutput(
                    hookSpecificOutput={  # type: ignore[typeddict-item]
                        "hookEventName": "PreToolUse",
                        "decision": "block",
                        "reason": reason,
                    }
                )

            # AUTOPILOT mode: check if human is actively typing
            if control_mode == "autopilot" and from_human_path.exists():
                try:
                    mtime = from_human_path.stat().st_mtime
                    if time.time() - mtime < 30:
                        await asyncio.sleep(3)
                except Exception:
                    pass

            # If there are new messages, block once to inject them
            if new_messages:
                return SyncHookJSONOutput(
                    hookSpecificOutput={  # type: ignore[typeddict-item]
                        "hookEventName": "PreToolUse",
                        "decision": "block",
                        "reason": (
                            "WALKIE-TALKIE — NEW MESSAGE FROM HUMAN:\n\n"
                            f"{new_messages}\n\n"
                            "Read and acknowledge this message by writing a response to "
                            ".agent/comms/to_human.md (using the Write tool). "
                            "If the message contains new instructions, adjust your plan. "
                            "Then continue your work."
                        ),
                    }
                )

            # No new messages, mode is continue or autopilot — approve
            return SyncHookJSONOutput(
                hookSpecificOutput={  # type: ignore[typeddict-item]
                    "hookEventName": "PreToolUse",
                    "decision": "approve",
                }
            )

        hooks: dict[str, list[HookMatcher]] = {
            "PreToolUse": [
                HookMatcher(hooks=[walkie_talkie_hook]),  # All tools
                HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
            ],
            "PreCompact": [
                HookMatcher(hooks=[pre_compact_hook]),
            ],
        }

        # Create and start the Claude SDK client
        system_cli = shutil.which("claude")

        try:
            shared_opts: dict[str, Any] = dict(
                model=self.model_id,
                cli_path=system_cli,
                system_prompt=system_prompt,
                setting_sources=["project", "user"],
                allowed_tools=DUNKSTACK_BUILTIN_TOOLS,
                permission_mode="acceptEdits",
                max_turns=50,
                cwd=self.working_directory,
                settings=str(settings_file.resolve()),
                env=sdk_env,
                hooks=hooks,
                betas=(
                    []
                    if is_alternative_api or self.context_mode != "1m"
                    else ["context-1m-2025-08-07"]
                ),
            )
            self._shared_opts = shared_opts

            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=self.effort, **shared_opts)
                )
            except TypeError:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**shared_opts)
                )

            logger.info(
                "DunkStack SDK client created: model=%s, context_mode=%s, cwd=%s",
                self.model_id, self.context_mode, self.working_directory,
            )

            # Enter client context with auth fallback
            _sub_auth_failed = False
            force_sub_local = force_sub
            try:
                await asyncio.wait_for(self.client.__aenter__(), timeout=60)
                self._client_entered = True
                logger.info("DunkStack Claude client ready")
            except asyncio.TimeoutError:
                if force_sub_local:
                    logger.warning("DunkStack subscription auth timed out, falling back to API key")
                    _sub_auth_failed = True
                else:
                    yield {
                        "type": "error",
                        "content": "The Claude CLI did not start within 60 seconds. Try again or switch models.",
                    }
                    yield {"type": "response_done"}
                    return
            except Exception as _enter_err:
                _err_lower = str(_enter_err).lower()
                _auth_hints = ["401", "auth", "oauth", "expired", "credential", "token has expired"]
                if force_sub_local and any(h in _err_lower for h in _auth_hints):
                    logger.warning("DunkStack subscription auth failed (%s), falling back", _enter_err)
                    _sub_auth_failed = True
                else:
                    raise

            # Auth fallback: retry with API key billing
            if _sub_auth_failed:
                try:
                    await self.client.__aexit__(None, None, None)
                except Exception:
                    pass
                self.client = None

                sdk_env = get_effective_sdk_env(force_subscription=False)
                if self.effort in ("low", "medium", "high"):
                    sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self.effort
                shared_opts["env"] = sdk_env
                if not is_alternative_api:
                    shared_opts["betas"] = ["context-1m-2025-08-07"]

                try:
                    self.client = ClaudeSDKClient(
                        options=ClaudeAgentOptions(effort=self.effort, **shared_opts)
                    )
                except TypeError:
                    self.client = ClaudeSDKClient(
                        options=ClaudeAgentOptions(**shared_opts)
                    )

                try:
                    await asyncio.wait_for(self.client.__aenter__(), timeout=60)
                    self._client_entered = True
                    yield {
                        "type": "text",
                        "content": (
                            "Subscription auth unavailable — using API key billing. "
                            "Run `claude login` in a terminal to refresh subscription credentials."
                        ),
                    }
                except Exception as _retry_err:
                    yield {"type": "error", "content": f"Failed to initialize agent: {str(_retry_err)}"}
                    yield {"type": "response_done"}
                    return

        except Exception as e:
            logger.exception("Failed to create DunkStack Claude client")
            yield {"type": "error", "content": f"Failed to initialize agent: {str(e)}"}
            yield {"type": "response_done"}
            return

        yield {
            "type": "text",
            "content": f"Agent ready. Model: **{self.model_id}** ({self.context_mode} context). Working directory: **{self.working_directory}**",
        }
        yield {"type": "response_done"}

    async def bootstrap(self) -> AsyncGenerator[dict, None]:
        """Send the DunkStack bootstrap message to the agent.

        This tells the agent to read its .agent/ files (index, working memory,
        bridge, comms, control) so it has full context before the user sends
        any messages. Should be called immediately after start() completes.

        Yields the same event types as send_message().
        """
        bootstrap_msg = (
            "You are starting a new session. Follow your file-based operating protocol:\n"
            "1. Read .agent/index.md (your file map)\n"
            "2. Read .agent/working_memory.md (your current state)\n"
            "3. If .agent/bridge.md has data, read and incorporate it\n"
            "4. Read .agent/comms/from_human.md for human messages — respond to ANY unread messages\n"
            "5. Read .agent/comms/control.md for mode signal\n"
            "6. Write your response/greeting to .agent/comms/to_human.md (NOT in chat)\n"
            "7. Respond in chat with a 1-sentence status ONLY\n\n"
            "## Polling Loop (IMPORTANT)\n"
            "After completing your current tasks, enter a polling loop to stay alive:\n"
            "- Read .agent/comms/walkie-check.txt every ~30 seconds\n"
            "- Check .agent/comms/from_human.md for any new messages\n"
            "- Check .agent/comms/control.md for mode changes\n"
            "- If you find new instructions, process them immediately\n"
            "- Continue until the human says 'end session' or context approaches limit\n\n"
            "Begin now."
        )
        async for event in self.send_message(bootstrap_msg):
            yield event

    async def send_message(self, user_message: str) -> AsyncGenerator[dict, None]:
        """Send a user message and stream the agent's response.

        Args:
            user_message: The user's message text.

        Yields:
            Message chunks:
            - {"type": "text", "content": str}
            - {"type": "tool_call", "tool": str, "input": dict}
            - {"type": "token_usage", ...}
            - {"type": "response_done"}
            - {"type": "error", "content": str}
        """
        if not self.client:
            yield {"type": "error", "content": "Agent not initialized. Start the session first."}
            yield {"type": "response_done"}
            return

        # Timeouts based on model
        is_opus = "opus" in self.model_id
        query_timeout = 180 if is_opus else 90
        first_token_timeout = 300 if is_opus else 120

        try:
            await asyncio.wait_for(
                self.client.query(user_message),
                timeout=query_timeout,
            )
        except asyncio.TimeoutError:
            yield {
                "type": "error",
                "content": f"The model did not accept the request within {query_timeout}s. Try again or switch models.",
            }
            yield {"type": "response_done"}
            return

        if is_opus:
            yield {"type": "status", "content": "Waiting for Opus response..."}

        full_response = ""
        first_token_received = False

        try:
            response_iter = self.client.receive_response().__aiter__()
            while True:
                try:
                    timeout = first_token_timeout if not first_token_received else 300
                    msg = await asyncio.wait_for(response_iter.__anext__(), timeout=timeout)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    if not first_token_received:
                        yield {"type": "error", "content": f"No response after {first_token_timeout}s. Try the 200K context mode."}
                    else:
                        yield {"type": "error", "content": "Response stream timed out after 5 minutes of silence."}
                    yield {"type": "response_done"}
                    return

                first_token_received = True
                msg_type = type(msg).__name__

                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__

                        if block_type == "TextBlock" and hasattr(block, "text"):
                            text = block.text
                            if text:
                                full_response += text
                                yield {"type": "text", "content": text}

                        elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                            tool_name = block.name
                            tool_input = getattr(block, "input", {})
                            tool_use_id = getattr(block, "id", None)
                            if tool_use_id:
                                self._tool_use_id_to_name[tool_use_id] = tool_name
                            yield {
                                "type": "tool_call",
                                "tool": tool_name,
                                "input": tool_input,
                            }

                # Silently skip SDK informational events (e.g. rate_limit_event)
                elif msg_type in ("RateLimitEvent", "rate_limit_event"):
                    logger.debug("Skipping SDK event type: %s", msg_type)

                elif msg_type == "ResultMessage":
                    usage = getattr(msg, "usage", None) or {}
                    cost_usd = getattr(msg, "total_cost_usd", None)

                    api_input = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
                    api_output = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
                    api_cache_create = usage.get("cache_creation_input_tokens", 0) if isinstance(usage, dict) else 0
                    api_cache_read = usage.get("cache_read_input_tokens", 0) if isinstance(usage, dict) else 0

                    logger.info(
                        "DunkStack ResultMessage: cost=$%.4f input=%s output=%s cache_create=%s cache_read=%s",
                        cost_usd or 0.0, api_input, api_output, api_cache_create, api_cache_read,
                    )

                    yield {
                        "type": "token_usage",
                        "input_tokens": api_input,
                        "output_tokens": api_output,
                        "cache_read_tokens": api_cache_read,
                        "cache_creation_tokens": api_cache_create,
                        "total_cost_usd": cost_usd or 0.0,
                    }

                    # Report to DunkStack token gauge via callback
                    if self.on_token_usage:
                        try:
                            await self.on_token_usage(
                                api_input, api_output,
                                api_cache_read, api_cache_create,
                                cost_usd or 0.0,
                            )
                        except Exception as e:
                            logger.warning("Failed to report token usage: %s", e)

            yield {"type": "response_done"}

        except Exception as e:
            error_str = str(e).lower()

            # SDK throws "Unknown message type: rate_limit_event" as an exception
            # AFTER the full response has been collected. Recover if we have text.
            if full_response.strip() and "unknown message type" in error_str:
                logger.info("DunkStack: recovered from 'unknown message type' with %d chars", len(full_response))
                yield {"type": "response_done"}
                return
            if full_response.strip():
                logger.warning("DunkStack: exception after partial response (%d chars), using what we have: %s", len(full_response), e)
                yield {"type": "response_done"}
                return

            logger.exception("Error during DunkStack query")
            _auth_hints = ["401", "authentication_error", "oauth", "token has expired", "credential"]
            if any(h in error_str for h in _auth_hints):
                logger.warning("DunkStack auth error — attempting API key fallback")
                fallback_ok = await self._fallback_to_api_key()
                if fallback_ok:
                    yield {
                        "type": "text",
                        "content": (
                            "Subscription auth expired — switched to API key billing. "
                            "Run `claude login` to refresh subscription credentials.\n\n"
                        ),
                    }
                    try:
                        async for chunk in self.send_message(user_message):
                            yield chunk
                        return
                    except Exception as retry_err:
                        logger.exception("DunkStack retry after API key fallback failed")
                        # API key also failed — try subscription as last resort
                        sub_ok = await self._fallback_to_subscription()
                        if sub_ok:
                            yield {
                                "type": "text",
                                "content": "API key failed — retrying with subscription auth.\n\n",
                            }
                            try:
                                async for chunk in self.send_message(user_message):
                                    yield chunk
                                return
                            except Exception as sub_err:
                                yield {
                                    "type": "error",
                                    "content": (
                                        f"All auth methods failed: {sub_err}\n\n"
                                        "Run `claude login` or add API credits at console.anthropic.com."
                                    ),
                                }
                        else:
                            yield {
                                "type": "error",
                                "content": (
                                    f"API key fallback also failed: {retry_err}\n\n"
                                    "Run `claude login` or add API credits at console.anthropic.com."
                                ),
                            }
                else:
                    yield {
                        "type": "error",
                        "content": (
                            f"Authentication error: {str(e)}\n\n"
                            "Could not fall back to API key billing. "
                            "Run `claude login` or set ANTHROPIC_API_KEY in Settings."
                        ),
                    }
            else:
                yield {"type": "error", "content": f"Error: {str(e)}"}
            yield {"type": "response_done"}
