"""
Workspace Chat Session
======================

Manages workspace chat sessions with full read/write Claude agent capabilities.
Forked from assistant_chat_session.py with key differences:

- Full tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
- ``acceptEdits`` permission mode (not bypassPermissions)
- Bash security hook via HookMatcher for safe command execution
- No MCP servers (workspace is project-agnostic)
- Token-budget context loading (100K cap) with NO per-message truncation
- Token estimation tracked per-message
- Global database (workspace_database), not per-project
- Session registry keyed by session_id string, not project_name
- Working directory configurable per-conversation (defaults to home directory)
- Configurable context window: 1,000,000 tokens (beta ``context-1m-2025-08-07``) or 200,000 tokens
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher, SyncHookJSONOutput
from dotenv import load_dotenv

from ..schemas import ImageAttachment
from .chat_constants import ROOT_DIR, make_multimodal_message  # noqa: F401
from .workspace_database import (
    add_message,
    add_token_log_entry,
    create_conversation,
    estimate_tokens,
    get_conversation_token_total,
)

# Ensure project root is on sys.path before importing root-level modules
_root_str = str(Path(__file__).parent.parent.parent)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from security import bash_security_hook  # noqa: E402

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger(__name__)

# Full set of built-in tools for the workspace agent.
# Unlike the assistant (read-only), the workspace agent can modify files and run commands.
WORKSPACE_BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]

# Maximum messages to load from history when resuming a conversation.
# No per-message truncation is applied -- the full content of each message is sent.
MAX_HISTORY_MESSAGES = 100

# Claude's context window with the 1M beta enabled (context-1m-2025-08-07).
# This is the core capability of the workspace -- must match the beta flag below.
CONTEXT_WINDOW_TOKENS = 1_000_000

# Standard 200K context window (no beta flag required).
CONTEXT_WINDOW_200K = 200_000

# Cost control defaults.  Overridable per-session via the WebSocket ``start`` message.
# These values represent the "economy" baseline; higher values increase quality and cost.
DEFAULT_COST_SETTINGS = {
    "effort": "high",             # Thinking effort: "low", "medium", "high"
    "max_tokens": 16384,          # Output token cap per response (4096-65536)
    "max_turns": 50,              # Max agent turns per message (10-100)
    "history_budget": 100_000,    # Token budget for history on resume (25000-400000)
    "library_cap": 50_000,        # Token cap for library file injection (10000-200000)
}

# Validation ranges for cost settings (min, max)
COST_SETTING_RANGES = {
    "max_tokens": (4096, 65536),
    "max_turns": (10, 100),
    "history_budget": (25_000, 400_000),
    "library_cap": (10_000, 200_000),
}
VALID_EFFORT_LEVELS = ("low", "medium", "high")


def validate_cost_settings(raw: dict) -> dict:
    """Validate and clamp cost settings, returning a clean dict with defaults for missing keys."""
    result = dict(DEFAULT_COST_SETTINGS)

    effort = raw.get("effort")
    if effort in VALID_EFFORT_LEVELS:
        result["effort"] = effort

    for key in ("max_tokens", "max_turns", "history_budget", "library_cap"):
        val = raw.get(key)
        if val is not None:
            try:
                val = int(val)
                lo, hi = COST_SETTING_RANGES[key]
                result[key] = max(lo, min(hi, val))
            except (ValueError, TypeError):
                pass  # keep default

    return result


def get_workspace_system_prompt(working_directory: str, model: str = "", context_mode: str = "1m") -> str:
    """Generate the system prompt for the workspace agent.

    Args:
        working_directory: Absolute path to the agent's working directory.
        model: The model ID being used (e.g. "claude-opus-4-6").
        context_mode: Context window mode -- "1m" or "200k".

    Returns:
        A system prompt string describing the workspace agent's capabilities and guidelines.
    """
    context_tokens = "1,000,000" if context_mode == "1m" else "200,000"
    return f"""You are an expert coding assistant ({model or 'Claude'}, {context_tokens} token context).
Working directory: {working_directory}

Read files before editing. Preserve existing code style. Use absolute paths. Prefer Glob/Grep over bash find/grep.

After completing edits, commit changes: `git add` only changed files (never -A), write a clear commit message, do NOT push. Report which files changed, the commit hash, and branch name.

Use structured tags when appropriate: [SUMMARY]...[/SUMMARY], [ROADMAP]...[/ROADMAP], [PROGRESS]...[/PROGRESS] — the UI renders these as cards.

If a tool call is blocked with "[WALKIE-TALKIE MESSAGE FROM USER]", acknowledge it, adjust if needed, then continue your task. Use [WAITING]question[/WAITING] when you need user input."""


class WorkspaceChatSession:
    """Manages a workspace conversation with full read/write Claude capabilities.

    Unlike the assistant (read-only), the workspace agent can modify files
    and run bash commands. Uses acceptEdits permission mode with bash
    security hooks for safe command execution.

    Persists conversation history (with per-message token estimates)
    to a global SQLite database at ``~/.autoforge/workspace.db``.
    """

    def __init__(
        self,
        session_id: str,
        conversation_id: Optional[int] = None,
        working_directory: Optional[str] = None,
        context_mode: str = "1m",
        cost_settings: Optional[dict] = None,
        model: Optional[str] = None,
    ):
        """Initialize the workspace chat session.

        Args:
            session_id: Unique identifier for this session (used as registry key).
            conversation_id: Optional existing conversation ID to resume.
            working_directory: Absolute path for the agent's cwd. Defaults to the user's home directory.
            context_mode: Context window size -- ``"1m"`` (1,000,000 tokens with beta flag)
                or ``"200k"`` (200,000 tokens, no beta). Defaults to ``"1m"``.
            cost_settings: Optional dict of cost control overrides (effort, max_tokens,
                max_turns, history_budget, library_cap). Missing keys use defaults.
            model: Optional model shorthand for per-panel routing (``"opus"`` or ``"sonnet"``).
                When ``None``, defaults to the Opus model.
        """
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.working_directory = working_directory or str(Path.home())
        self.context_mode = context_mode
        # Both Opus 4.6 and Sonnet 4.6 support the 1M context beta (context-1m-2025-08-07).
        if context_mode == "1m":
            self.context_window = CONTEXT_WINDOW_TOKENS
        else:
            self.context_window = CONTEXT_WINDOW_200K
        self.cost_settings = validate_cost_settings(cost_settings or {})
        self.model = model
        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False
        self.created_at = datetime.now()
        self._history_loaded: bool = False

        # Resolved model ID (populated during start(), exposed for UI display).
        self._resolved_model_id: Optional[str] = None

        # Mapping from tool_use_id (UUID) to tool name, populated during
        # ToolUseBlock processing so that ToolResultBlock logs can reference
        # the human-readable tool name instead of the opaque UUID.
        self._tool_use_id_to_name: dict[str, str] = {}

        # Walkie-talkie communication: in-memory message queue for injecting
        # user messages into a running agent via PreToolUse hook interception.
        self.walkie_talkie_queue: asyncio.Queue[str] = asyncio.Queue()
        self.walkie_talkie_enabled: bool = True  # Controlled by comm_check_frequency setting
        self.walkie_talkie_waiting: bool = False  # True when agent output [WAITING] tag

    async def close(self) -> None:
        """Clean up resources and close the Claude client."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Claude client for workspace session {self.session_id}: {e}")
            finally:
                self._client_entered = False
                self.client = None

    async def queue_walkie_talkie_message(self, content: str) -> None:
        """Queue a walkie-talkie message for the running agent to receive.

        The message will be delivered on the agent's next tool call via the
        PreToolUse hook. If multiple messages are queued before delivery,
        they are concatenated into a single delivery.
        """
        await self.walkie_talkie_queue.put(content)

    def _create_workspace_branch(self) -> Optional[str]:
        """Auto-create a git branch for this conversation if inside a git repo.

        Creates a branch named ``workspace/chat-{conversation_id}`` and checks
        it out. Returns the branch name on success, or ``None`` if the
        working directory is not a git repo or branch creation fails.
        """
        wd = self.working_directory
        if not wd or wd == str(Path.home()):
            return None

        # Check if the directory is a git repo
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=wd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None
        except Exception:
            return None

        branch_name = f"workspace/chat-{self.conversation_id}"
        try:
            # Create and checkout the new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=wd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info(
                    "Auto-created branch '%s' for conversation %d in %s",
                    branch_name, self.conversation_id, wd,
                )
                return branch_name

            # Branch might already exist (e.g. resumed session) — try switching
            result = subprocess.run(
                ["git", "checkout", branch_name],
                cwd=wd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info("Switched to existing branch '%s'", branch_name)
                return branch_name

            logger.warning("Failed to create/switch branch '%s': %s", branch_name, result.stderr.strip())
            return None
        except Exception as e:
            logger.warning("Branch creation error: %s", e)
            return None

    async def start(self) -> AsyncGenerator[dict, None]:
        """Initialize the session with the Claude client.

        Creates a new conversation if none exists, writes security settings
        and system prompt to scratch files, then starts the Claude SDK client
        with bash security hooks and the 1M context window beta.

        For resumed conversations, history is loaded on the first ``send_message()`` call.

        Yields:
            Message chunks:
            - ``{"type": "conversation_created", "conversation_id": int}``
            - ``{"type": "text", "content": str}``
            - ``{"type": "response_done"}``
            - ``{"type": "error", "content": str}``
        """
        # Track whether this is a brand-new conversation (determines greeting behavior)
        is_new_conversation = self.conversation_id is None

        # Create a new conversation in the global workspace database if needed
        if is_new_conversation:
            conv = create_conversation(
                working_directory=self.working_directory,
                context_mode=self.context_mode,
                model=self.model,
            )
            self.conversation_id = int(conv.id)  # type coercion: Column[int] -> int
            yield {"type": "conversation_created", "conversation_id": self.conversation_id}

            # Auto-create a git branch for this conversation if the working
            # directory is a git repo, mimicking Claude Code's behavior.
            branch_name = self._create_workspace_branch()
            if branch_name:
                yield {"type": "branch_created", "branch": branch_name}

        # -----------------------------------------------------------------
        # Security settings: full tools with acceptEdits permission mode.
        # Written to a dedicated file since there is no project directory.
        # -----------------------------------------------------------------
        try:
            permissions_list = [
                "Read",
                "Write",
                "Edit",
                "Bash",
                "Glob",
                "Grep",
                "WebFetch",
                "WebSearch",
            ]

            security_settings = {
                "sandbox": {"enabled": False},
                "permissions": {
                    "defaultMode": "acceptEdits",
                    "allow": permissions_list,
                },
            }

            settings_dir = Path.home() / ".autoforge"
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_file = settings_dir / ".workspace_claude_settings.json"
            with open(settings_file, "w") as f:
                json.dump(security_settings, f, indent=2)
        except Exception as e:
            logger.exception("Failed to write workspace security settings")
            yield {"type": "error", "content": f"Failed to write settings: {str(e)}"}
            yield {"type": "response_done"}
            return

        # -----------------------------------------------------------------
        # Claude SDK client: full tools, bash security hook, 1M context beta.
        # -----------------------------------------------------------------
        system_cli = shutil.which("claude")

        try:
            from registry import DEFAULT_MODEL, get_effective_sdk_env
            # Route billing based on the context-mode toggle:
            #   1M  → keep API key (1M beta requires API billing)
            #   200K → strip API key so CLI uses subscription OAuth
            force_sub = self.context_mode != "1m"
            sdk_env = get_effective_sdk_env(force_subscription=force_sub)
            if force_sub:
                logger.info("Workspace billing: Subscription (200K context, context_mode=%s)", self.context_mode)
            else:
                logger.info("Workspace billing: API key (1M context, context_mode=%s)", self.context_mode)
        except Exception as e:
            logger.exception("Failed to load registry/SDK environment")
            yield {"type": "error", "content": f"Failed to load configuration: {str(e)}"}
            yield {"type": "response_done"}
            return

        # Per-panel model routing: resolve the model shorthand to a full model ID.
        # When self.model is set (from the UI panel), use it to pick the right model.
        # Otherwise fall back to the environment default (Opus).
        MODEL_MAP = {
            "opus": (
                sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
                or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_MODEL)
            ),
            "sonnet": (
                sdk_env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
                or os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6")
            ),
        }
        model = MODEL_MAP.get(self.model or "", MODEL_MAP["opus"])
        self._resolved_model_id = model  # Store for UI display
        logger.info(f"Resolved model: {self.model} -> {model}")

        # -----------------------------------------------------------------
        # System prompt: written as CLAUDE.md in a scratch directory so the
        # SDK reads it via setting_sources=["project"] without clobbering
        # any existing CLAUDE.md in the user's actual working directory.
        # -----------------------------------------------------------------
        workspace_scratch = Path.home() / ".autoforge" / ".workspace_scratch"
        workspace_scratch.mkdir(parents=True, exist_ok=True)
        claude_md_path = workspace_scratch / "CLAUDE.md"
        system_prompt = get_workspace_system_prompt(self.working_directory, model=model, context_mode=self.context_mode)
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)
        # Log context_mode tracing to help debug 200K vs 1M issues
        context_snippet = system_prompt[:120].replace('\n', ' ')
        logger.info(
            "Wrote workspace CLAUDE.md: context_mode=%s, model=%s, prompt_start='%s'",
            self.context_mode, model, context_snippet,
        )

        # Detect alternative API mode (Ollama, GLM, Vertex AI) -- these do not
        # support the 1M context beta, so we must disable it.
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex

        # Bash security hook -- same allowlist-based hook the coding agent uses
        # PreCompact hook -- guides summarization to keep context lean and cheap
        async def workspace_pre_compact_hook(input_data, tool_use_id=None, context=None):
            """Guide compaction to discard verbose tool results and keep costs low."""
            trigger = input_data.get("trigger", "auto")
            logger.info(f"[Workspace] Context compaction triggered ({trigger})")

            compaction_guidance = "\n".join([
                "## Workspace Compaction Guidelines",
                "Keep the conversation lean to minimize token costs.",
                "",
                "## DISCARD (verbose/redundant)",
                "- Full file contents from Read tool results (keep only: 'Read file X, ~N lines')",
                "- Large Grep/Glob outputs (keep only: 'Found N matches in these files: ...')",
                "- Full Bash command outputs (keep only: command + success/failure + key output lines)",
                "- Repeated reads of the same file",
                "- CSS/HTML/JSON content dumps",
                "",
                "## PRESERVE (important context)",
                "- What the user asked for and key decisions made",
                "- Files that were created or modified (paths only)",
                "- Current task state and any open questions",
                "- Error messages that are still relevant",
            ])

            return SyncHookJSONOutput(
                hookSpecificOutput={  # type: ignore[typeddict-item]
                    "hookEventName": "PreCompact",
                    "customInstructions": compaction_guidance,
                }
            )

        # Walkie-talkie hook: checks the in-memory message queue before every
        # tool call.  When a user message is waiting, the hook blocks the tool
        # and injects the message so the agent can address it before proceeding.
        async def walkie_talkie_hook(input_data, tool_use_id=None, context=None):
            """Check for walkie-talkie messages before each tool call."""
            if not self.walkie_talkie_enabled:
                return None  # Disabled via settings, proceed normally

            # Drain all queued messages into a single delivery
            messages: list[str] = []
            while True:
                try:
                    msg = self.walkie_talkie_queue.get_nowait()
                    messages.append(msg)
                except asyncio.QueueEmpty:
                    break

            if not messages:
                return None  # No messages, proceed normally

            # Reset waiting state -- user has responded
            self.walkie_talkie_waiting = False

            # Concatenate multiple messages with separators
            if len(messages) == 1:
                body = messages[0]
            else:
                parts = [f"Message {i + 1}: {m}" for i, m in enumerate(messages)]
                body = "\n---\n".join(parts)

            logger.info(
                "Walkie-talkie: delivering %d message(s) to agent in session %s",
                len(messages), self.session_id,
            )

            # Return the same plain-dict format used by bash_security_hook.
            # Previous code used SyncHookJSONOutput with hookSpecificOutput
            # which placed "decision"/"reason" inside the wrong structure —
            # the SDK silently ignored those fields so the tool proceeded
            # normally and the consumed message was permanently lost.
            return {
                "decision": "block",
                "reason": (
                    f"[WALKIE-TALKIE MESSAGE FROM USER]\n\n"
                    f"{body}\n\n"
                    f"[END WALKIE-TALKIE MESSAGE]\n\n"
                    f"Please acknowledge and address this message. "
                    f"Then continue with your previous task. "
                    f"Your planned tool call was not executed — "
                    f"you may re-attempt it after addressing the message."
                ),
            }

        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                HookMatcher(hooks=[walkie_talkie_hook]),  # Fires for ALL tools
            ],
            "PreCompact": [
                HookMatcher(hooks=[workspace_pre_compact_hook])
            ],
        }

        try:
            logger.info(f"Creating workspace ClaudeSDKClient for session {self.session_id}...")
            cs = self.cost_settings
            logger.info(
                f"Cost settings: effort={cs['effort']}, max_tokens={cs['max_tokens']}, "
                f"max_turns={cs['max_turns']}, history_budget={cs['history_budget']}, "
                f"library_cap={cs['library_cap']}"
            )

            # Wire up Anthropic's real effort control via Claude Code CLI env var.
            # The Agent SDK passes env vars through to the underlying CLI process.
            effort = cs.get("effort", "high")
            if effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = effort

            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=model,
                    cli_path=system_cli,
                    # System prompt loaded from CLAUDE.md via setting_sources.
                    # This avoids Windows command line length limits (~8191 chars).
                    setting_sources=["project"],
                    allowed_tools=WORKSPACE_BUILTIN_TOOLS,
                    permission_mode="acceptEdits",
                    # Cost controls: max_turns from dashboard, effort via
                    # CLAUDE_CODE_EFFORT_LEVEL env var (injected into sdk_env above).
                    max_turns=cs["max_turns"],
                    cwd=str(workspace_scratch),  # Scratch dir for CLAUDE.md
                    settings=str(settings_file.resolve()),
                    env=sdk_env,
                    hooks=hooks,
                    # Enable 1M token context window for 1M mode.
                    # The context-1m beta supports both Opus 4.6 and Sonnet 4.6.
                    # Disabled for alternative APIs and 200K mode.
                    betas=(
                        []
                        if is_alternative_api or self.context_mode != "1m"
                        else ["context-1m-2025-08-07"]
                    ),
                )
            )
            # Log the resolved SDK parameters for debugging
            resolved_betas = (
                []
                if is_alternative_api or self.context_mode != "1m"
                else ["context-1m-2025-08-07"]
            )
            has_api_key = bool(sdk_env.get("ANTHROPIC_API_KEY"))
            logger.info(
                "SDK client created: betas=%s, context_mode=%s, force_sub=%s, has_api_key=%s, is_alt=%s",
                resolved_betas, self.context_mode, force_sub, has_api_key, is_alternative_api,
            )
            logger.info("Entering workspace Claude client context...")
            try:
                await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            except asyncio.TimeoutError:
                logger.error(
                    "Timeout (60s) waiting for Claude CLI to start (context_mode=%s, model=%s). "
                    "This often means subscription OAuth credentials are missing or expired. "
                    "Check ~/.claude/.credentials.json or switch to API key billing (1M mode).",
                    self.context_mode, self.model,
                )
                yield {
                    "type": "error",
                    "content": (
                        "The Claude CLI did not start within 60 seconds. "
                        "If using subscription (200K) mode, ensure you're logged in "
                        "(run `claude login` in a terminal). "
                        "Or switch to 1M API mode which uses your API key."
                    ),
                }
                yield {"type": "response_done"}
                return
            self._client_entered = True
            logger.info("Workspace Claude client ready")
        except Exception as e:
            logger.exception("Failed to create workspace Claude client")
            yield {"type": "error", "content": f"Failed to initialize workspace: {str(e)}"}
            yield {"type": "response_done"}
            return

        # Send initial greeting only for NEW conversations.
        # Resumed conversations load history on the first send_message() call.
        if is_new_conversation:
            self._history_loaded = True
            try:
                branch_suffix = ""
                if branch_name:
                    branch_suffix = f" Branch: **{branch_name}**."
                greeting = (
                    f"Ready. Working directory: **{self.working_directory}**.{branch_suffix}"
                )

                assert self.conversation_id is not None
                # Don't persist the greeting to the database — it adds unnecessary
                # tokens to the conversation history on resume without providing value.
                # It's only displayed in the UI for the current session.

                yield {"type": "text", "content": greeting}

                # Yield initial token usage so the client can render the meter
                total = get_conversation_token_total(self.conversation_id)
                from . import workspace_database as db
                msg_count = db.get_message_count(self.conversation_id)
                yield {
                    "type": "token_usage",
                    "total_tokens": total,
                    "context_window": self.context_window,
                    "message_count": msg_count,
                    "model_id": self._resolved_model_id,
                }

                yield {"type": "response_done"}
            except Exception as e:
                logger.exception("Failed to send workspace greeting")
                yield {"type": "error", "content": f"Failed to start conversation: {str(e)}"}
        else:
            # Resumed conversation -- yield current token totals so the meter
            # shows existing usage immediately, then signal response_done.
            total = get_conversation_token_total(self.conversation_id)
            from . import workspace_database as db
            msg_count = db.get_message_count(self.conversation_id)
            yield {
                "type": "token_usage",
                "total_tokens": total,
                "context_window": self.context_window,
                "message_count": msg_count,
                "model_id": self._resolved_model_id,
            }
            yield {"type": "response_done"}

    async def send_message(
        self, user_message: str, attachments: list[ImageAttachment] | None = None
    ) -> AsyncGenerator[dict, None]:
        """Send a user message and stream Claude's response.

        For resumed conversations, the first call automatically loads messages
        from the database using a dynamic token budget strategy with optional summary context.

        Args:
            user_message: The user's message text.
            attachments: Optional list of image attachments to include.

        Yields:
            Message chunks:
            - ``{"type": "text", "content": str}``
            - ``{"type": "tool_call", "tool": str, "input": dict}``
            - ``{"type": "token_usage", "total_tokens": int, "context_window": int}``
            - ``{"type": "response_done"}``
            - ``{"type": "error", "content": str}``
        """
        if not self.client:
            yield {"type": "error", "content": "Session not initialized. Call start() first."}
            return

        if self.conversation_id is None:
            yield {"type": "error", "content": "No conversation ID set."}
            return

        # Estimate tokens and store the user message in the global database
        user_tokens = estimate_tokens(user_message)
        add_message(self.conversation_id, "user", user_message, user_tokens)

        # For resumed conversations, include full history context in the first message.
        # Uses dynamic token-budget loading: summary first, then recent messages
        # up to the remaining budget (no fixed message cap or per-message truncation).
        message_to_send = user_message
        if not self._history_loaded:
            self._history_loaded = True
            from . import workspace_database as db

            # Load the latest summary first
            latest_summary = db.get_latest_summary(self.conversation_id)
            summary_context = ""
            summary_tokens = 0
            if latest_summary:
                summary_context = latest_summary["summary"]
                summary_tokens = latest_summary.get("token_estimate", len(summary_context) // 4)

            # Calculate remaining budget for messages (reserve space for summary).
            # Configurable via cost dashboard to avoid pushing input into
            # long-context premium pricing (above 200K: 2× input & 1.5× output).
            MESSAGE_TOKEN_BUDGET = self.cost_settings["history_budget"]
            remaining_budget = MESSAGE_TOKEN_BUDGET - summary_tokens

            # Load messages dynamically up to the budget
            history_messages, loaded_tokens = db.get_messages_for_context(
                self.conversation_id,
                token_budget=remaining_budget,
            )
            # Exclude the current message we just added (it's the last one chronologically)
            if history_messages and history_messages[-1]["content"] == user_message:
                history_messages = history_messages[:-1]

            if summary_context or history_messages:
                history_lines: list[str] = []
                if summary_context:
                    history_lines.append("[Conversation summary:]")
                    history_lines.append(summary_context)
                    history_lines.append("")
                if history_messages:
                    history_lines.append("[Recent conversation history:]")
                    for msg in history_messages:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        history_lines.append(f"{role}: {msg['content']}")
                history_lines.append("[End of history. Continue the conversation:]")
                history_lines.append(f"User: {user_message}")
                message_to_send = "\n".join(history_lines)
                logger.info(
                    f"Loaded context: summary={bool(summary_context)}, "
                    f"messages={len(history_messages)}, tokens={loaded_tokens + summary_tokens}"
                )

        # Inject active library file content into the message
        if self.conversation_id:
            try:
                from .workspace_library import get_active_files_context
                library_context, library_tokens = get_active_files_context(
                    self.conversation_id, token_cap=self.cost_settings["library_cap"]
                )
                if library_context:
                    message_to_send = f"{library_context}\n\n{message_to_send}"
            except Exception as e:
                logger.warning("Failed to load library context: %s", e)

        try:
            async for chunk in self._query_claude(message_to_send, attachments=attachments):
                yield chunk
            yield {"type": "response_done"}
        except Exception as e:
            logger.exception("Error during workspace Claude query")
            error_str = str(e).lower()
            yield {"type": "error", "content": f"Error: {str(e)}"}

            # Auto-detect rate limit / billing errors and log them for calibration
            rate_limit_patterns = [
                "rate limit", "rate_limit", "ratelimit",
                "usage limit", "usage_limit",
                "too many requests", "429",
                "capacity", "overloaded",
                "please wait", "try again later",
                "resume at", "resume usage",
                "credit balance", "balance too low",
                "insufficient credit", "billing",
            ]
            if any(p in error_str for p in rate_limit_patterns):
                try:
                    from . import workspace_database as db
                    usage = db.get_usage_by_period("daily")
                    db.log_rate_limit_event(
                        event_type="daily",
                        tokens_at_hit=usage["total_tokens"],
                        message_count_at_hit=usage["message_count"],
                        notes=f"Auto-detected: {str(e)[:200]}",
                    )
                    logger.info("Auto-logged rate limit event from error: %s", str(e)[:100])
                    yield {
                        "type": "rate_limit_logged",
                        "event_type": "daily",
                        "tokens_at_hit": usage["total_tokens"],
                    }
                except Exception as log_err:
                    logger.warning("Failed to auto-log rate limit: %s", log_err)

    async def _query_claude(
        self, message: str, attachments: list[ImageAttachment] | None = None
    ) -> AsyncGenerator[dict, None]:
        """Stream a response from Claude for the given message.

        Accumulates the full response text, computes a token estimate, stores
        the message in the database, and yields a ``token_usage`` event so the
        client can render a context-window meter.

        Args:
            message: The message (or history-prefixed message) to send to Claude.
            attachments: Optional list of image attachments to include.

        Yields:
            Message chunks:
            - ``{"type": "text", "content": str}``
            - ``{"type": "tool_call", "tool": str, "input": dict}``
            - ``{"type": "token_usage", "total_tokens": int, "context_window": int}``
        """
        if not self.client:
            return

        # Timeouts — Opus is significantly slower than Sonnet, especially
        # with the 1M context beta.  Use generous limits but don't hang forever.
        # When self.model is None or empty, the default is Opus, so use Opus timeouts.
        is_sonnet = self.model == "sonnet"
        is_opus = not is_sonnet  # Default to Opus timeouts (None/empty/opus all get Opus)
        query_timeout = 180 if is_opus else 90   # seconds to accept the query
        first_token_timeout = 300 if is_opus else 120  # seconds for first token

        # Build the message content -- multimodal if attachments are present
        if attachments and len(attachments) > 0:
            content_blocks: list[dict[str, Any]] = []
            if message:
                content_blocks.append({"type": "text", "text": message})
            for att in attachments:
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": att.mimeType,
                        "data": att.base64Data,
                    }
                })
            try:
                await asyncio.wait_for(
                    self.client.query(make_multimodal_message(content_blocks)),
                    timeout=query_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout ({query_timeout}s) waiting for query acceptance (multimodal, model={self.model})")
                yield {"type": "error", "content": f"The model ({self.model}) did not accept the request within {query_timeout}s. It may be overloaded — try again or switch models."}
                return
            logger.info(f"Sent multimodal message with {len(attachments)} image(s)")
        else:
            try:
                await asyncio.wait_for(
                    self.client.query(message),
                    timeout=query_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout ({query_timeout}s) waiting for query acceptance (model={self.model})")
                yield {"type": "error", "content": f"The model ({self.model}) did not accept the request within {query_timeout}s. It may be overloaded — try again or switch models."}
                return

        # Notify UI that we're waiting — Opus can take 30-60+ seconds for
        # the first token, so give the user feedback that the system is alive.
        if is_opus:
            yield {"type": "status", "content": "Waiting for Opus response (this model is slower than Sonnet — hang tight)..."}

        full_response = ""
        first_token_received = False

        # ── Token processing log tracking ──
        turn_number = 0
        turn_text_length = 0
        turn_tool_calls: list[str] = []  # tool names in current assistant turn
        conv_id = self.conversation_id  # capture for logging

        # Stream the response with a first-token timeout
        response_iter = self.client.receive_response().__aiter__()
        while True:
            try:
                timeout = first_token_timeout if not first_token_received else 300
                msg = await asyncio.wait_for(response_iter.__anext__(), timeout=timeout)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                if not first_token_received:
                    logger.error(f"Timeout ({first_token_timeout}s) waiting for first token from {self.model}")
                    yield {"type": "error", "content": f"No response from {self.model} after {first_token_timeout}s. The 1M context beta may not be available, or the model may be overloaded. Try the 200K context mode."}
                else:
                    logger.error(f"Timeout (300s) waiting for next token from {self.model}")
                    yield {"type": "error", "content": f"Response stream from {self.model} timed out after 5 minutes of silence."}
                return
            first_token_received = True
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                turn_number += 1
                turn_text_length = 0
                turn_tool_calls = []

                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        text = block.text
                        if text:
                            full_response += text
                            turn_text_length += len(text)
                            yield {"type": "text", "content": text}

                            # Detect agent-initiated wait signal: [WAITING]...[/WAITING]
                            if "[WAITING]" in full_response and "[/WAITING]" in full_response:
                                wait_match = re.search(
                                    r'\[WAITING\](.*?)\[/WAITING\]',
                                    full_response,
                                    re.DOTALL,
                                )
                                if wait_match and not self.walkie_talkie_waiting:
                                    self.walkie_talkie_waiting = True
                                    yield {
                                        "type": "agent_waiting",
                                        "question": wait_match.group(1).strip(),
                                    }

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        tool_name = block.name
                        tool_input = getattr(block, "input", {})
                        # Map tool_use_id -> tool_name so ToolResultBlock can look up the name
                        tool_use_id = getattr(block, "id", None)
                        if tool_use_id:
                            self._tool_use_id_to_name[tool_use_id] = tool_name
                        turn_tool_calls.append(tool_name)
                        yield {
                            "type": "tool_call",
                            "tool": tool_name,
                            "input": tool_input,
                        }

                        # Log the tool call
                        if conv_id is not None:
                            input_str = json.dumps(tool_input) if tool_input else ""
                            input_len = len(input_str)
                            try:
                                entry = add_token_log_entry(
                                    conversation_id=conv_id,
                                    event_type="tool_call",
                                    turn_number=turn_number,
                                    tool_name=tool_name,
                                    tool_input_length=input_len,
                                    estimated_tokens=input_len // 4,
                                    model=self.model,
                                )
                                yield {"type": "token_log", "entry": entry}
                            except Exception as e:
                                logger.warning("Failed to log tool_call: %s", e)

                # Log the assistant turn summary
                if conv_id is not None:
                    try:
                        entry = add_token_log_entry(
                            conversation_id=conv_id,
                            event_type="assistant_turn",
                            turn_number=turn_number,
                            text_length=turn_text_length,
                            num_tool_calls=len(turn_tool_calls),
                            estimated_tokens=turn_text_length // 4,
                            model=self.model,
                        )
                        yield {"type": "token_log", "entry": entry}
                    except Exception as e:
                        logger.warning("Failed to log assistant_turn: %s", e)

            # Handle UserMessage (tool results) — log each tool result
            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "ToolResultBlock":
                        result_content = str(getattr(block, "content", ""))
                        is_error = getattr(block, "is_error", False)
                        result_len = len(result_content)
                        # Resolve tool_use_id to the human-readable tool name
                        # via the mapping built during ToolUseBlock processing.
                        result_tool_use_id = getattr(block, "tool_use_id", None)
                        result_tool_name = self._tool_use_id_to_name.get(result_tool_use_id, result_tool_use_id) if result_tool_use_id else None

                        if conv_id is not None:
                            try:
                                entry = add_token_log_entry(
                                    conversation_id=conv_id,
                                    event_type="tool_result",
                                    turn_number=turn_number,
                                    tool_name=result_tool_name,
                                    tool_result_length=result_len,
                                    tool_is_error=is_error,
                                    estimated_tokens=result_len // 4,
                                    model=self.model,
                                )
                                yield {"type": "token_log", "entry": entry}
                            except Exception as e:
                                logger.warning("Failed to log tool_result: %s", e)

            # Handle ResultMessage — the SDK's final summary with actual API usage
            elif msg_type == "ResultMessage":
                usage = getattr(msg, "usage", None) or {}
                cost_usd = getattr(msg, "total_cost_usd", None)
                num_turns_api = getattr(msg, "num_turns", None)
                duration_ms = getattr(msg, "duration_ms", None)
                duration_api_ms = getattr(msg, "duration_api_ms", None)
                is_error = getattr(msg, "is_error", False)
                result_model = getattr(msg, "model", self.model)

                # Extract token counts from usage dict
                api_input = usage.get("input_tokens") if isinstance(usage, dict) else None
                api_output = usage.get("output_tokens") if isinstance(usage, dict) else None
                api_cache_create = usage.get("cache_creation_input_tokens") if isinstance(usage, dict) else None
                api_cache_read = usage.get("cache_read_input_tokens") if isinstance(usage, dict) else None

                logger.info(
                    "ResultMessage: model=%s cost=$%.4f input=%s output=%s "
                    "cache_create=%s cache_read=%s turns=%s duration=%sms is_error=%s",
                    result_model, cost_usd or 0.0, api_input, api_output,
                    api_cache_create, api_cache_read, num_turns_api,
                    duration_ms, is_error,
                )

                if conv_id is not None:
                    try:
                        entry = add_token_log_entry(
                            conversation_id=conv_id,
                            event_type="result_summary",
                            turn_number=turn_number,
                            api_input_tokens=api_input,
                            api_output_tokens=api_output,
                            api_cache_creation_tokens=api_cache_create,
                            api_cache_read_tokens=api_cache_read,
                            api_total_cost_usd=cost_usd,
                            api_num_turns=num_turns_api,
                            api_duration_ms=duration_ms,
                            api_duration_api_ms=duration_api_ms,
                            estimated_tokens=(api_input or 0) + (api_output or 0),
                            model=result_model or self.model,
                        )
                        yield {"type": "token_log", "entry": entry}
                    except Exception as e:
                        logger.warning("Failed to log result_summary: %s", e)

        # Store the complete response with its token estimate
        if full_response and self.conversation_id is not None:
            response_tokens = estimate_tokens(full_response)
            add_message(self.conversation_id, "assistant", full_response, response_tokens)

            # Trigger auto-summary check in background
            try:
                from . import workspace_database as db
                from .workspace_summary import trigger_summary_generation
                messages_list = db.get_messages(self.conversation_id)
                message_count = len(messages_list)
                await trigger_summary_generation(
                    conversation_id=self.conversation_id,
                    get_messages_fn=db.get_messages,
                    save_summary_fn=db.save_summary,
                    message_count=message_count,
                )
            except Exception as e:
                logger.warning(f"Failed to trigger summary generation: {e}")

            # Yield token usage update so the client can render the context-window meter
            total = get_conversation_token_total(self.conversation_id)
            from . import workspace_database as db
            msg_count = db.get_message_count(self.conversation_id)
            yield {
                "type": "token_usage",
                "total_tokens": total,
                "context_window": self.context_window,
                "message_count": msg_count,
                "model_id": self._resolved_model_id,
            }

            # Log premium-zone usage for cost tracking
            try:
                db.log_premium_usage(self.conversation_id, model=self.model or "opus")
            except Exception as e:
                logger.warning(f"Failed to log premium usage: {e}")

    def get_conversation_id(self) -> Optional[int]:
        """Get the current conversation ID."""
        return self.conversation_id


# =============================================================================
# Session Registry (thread-safe, keyed by session_id)
# =============================================================================

_sessions: dict[str, WorkspaceChatSession] = {}
_sessions_lock = threading.Lock()


def get_session(session_id: str) -> Optional[WorkspaceChatSession]:
    """Get an existing workspace session by its session ID.

    Args:
        session_id: The unique session identifier.

    Returns:
        The session instance, or None if no session exists for that ID.
    """
    with _sessions_lock:
        return _sessions.get(session_id)


async def create_session(
    session_id: str,
    conversation_id: Optional[int] = None,
    working_directory: Optional[str] = None,
    context_mode: str = "1m",
    cost_settings: Optional[dict] = None,
    model: Optional[str] = None,
) -> WorkspaceChatSession:
    """Create a new workspace session, closing any existing one with the same ID.

    Args:
        session_id: Unique identifier for the session.
        conversation_id: Optional conversation ID to resume.
        working_directory: Absolute path for the agent's working directory.
        context_mode: Context window size -- ``"1m"`` or ``"200k"``. Defaults to ``"1m"``.
        cost_settings: Optional dict of cost control overrides.
        model: Optional model shorthand for per-panel routing (``"opus"`` or ``"sonnet"``).

    Returns:
        The newly created session instance.
    """
    old_session: Optional[WorkspaceChatSession] = None

    with _sessions_lock:
        old_session = _sessions.pop(session_id, None)
        session = WorkspaceChatSession(
            session_id,
            conversation_id=conversation_id,
            working_directory=working_directory,
            context_mode=context_mode,
            cost_settings=cost_settings,
            model=model,
        )
        _sessions[session_id] = session

    if old_session:
        try:
            await old_session.close()
        except Exception as e:
            logger.warning(f"Error closing old workspace session {session_id}: {e}")

    return session


async def remove_session(session_id: str) -> None:
    """Remove and close a workspace session.

    Args:
        session_id: The session identifier to remove.
    """
    session: Optional[WorkspaceChatSession] = None

    with _sessions_lock:
        session = _sessions.pop(session_id, None)

    if session:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing workspace session {session_id}: {e}")


async def cleanup_all_workspace_sessions() -> None:
    """Close all active workspace sessions. Called on server shutdown."""
    sessions_to_close: list[WorkspaceChatSession] = []

    with _sessions_lock:
        sessions_to_close = list(_sessions.values())
        _sessions.clear()

    for session in sessions_to_close:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing workspace session {session.session_id}: {e}")
