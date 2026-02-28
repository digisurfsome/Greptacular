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
    # Map raw model IDs to human-friendly names so the model self-identifies correctly.
    MODEL_DISPLAY_NAMES: dict[str, str] = {
        "claude-opus-4-6": "Claude Opus 4.6",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    }
    display_name = MODEL_DISPLAY_NAMES.get(model or "", model or "Claude")
    model_id_note = f" (model ID: {model})" if model else ""
    return f"""You are an expert coding assistant ({display_name}{model_id_note}, {context_tokens} token context).
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
        provider: Optional[str] = None,
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
            provider: CLI provider -- ``"claude"`` (default), ``"codex"`` (OpenAI),
                or ``"gemini"`` (Google). Determines which CLI backend handles messages.
        """
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.working_directory = working_directory or str(Path.home())
        self.context_mode = context_mode
        self.provider = provider or "claude"
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

        # Saved state from start() needed for mid-session auth fallback.
        # When subscription OAuth expires during a query, these allow
        # _fallback_to_api_key() to recreate the client with API key billing.
        self._shared_opts: Optional[dict[str, Any]] = None
        self._effort: str = "high"
        self._is_alternative_api: bool = False
        self._force_sub: bool = False

        # Backup of original .claude/settings.json in the working directory,
        # restored on close() to avoid clobbering user's project settings.
        self._original_project_settings: Optional[str] = None  # None = file didn't exist
        self._project_settings_path: Optional[Path] = None

        # Actual API usage from the latest ResultMessage.  Updated after each
        # _query_claude() call so the ``token_usage`` event reflects real API
        # numbers instead of heuristic estimates.
        self._last_api_usage: Optional[dict] = None

        # Legacy flag (no longer used — library files are now attached per-message)
        self._library_injected: bool = False

        # Multi-provider bridges (Codex / Gemini).  Initialized during start()
        # only when self.provider != "claude".
        self._codex_bridge: Optional[Any] = None  # CodexBridge instance
        self._gemini_bridge: Optional[Any] = None  # GeminiBridge instance
        self._provider_thread_id: Optional[str] = None  # Codex threadId / Gemini session_id

        # Walkie-talkie communication: in-memory message queue for injecting
        # user messages into a running agent via PreToolUse hook interception.
        self.walkie_talkie_queue: asyncio.Queue[str] = asyncio.Queue()
        self.walkie_talkie_enabled: bool = True  # Controlled by comm_check_frequency setting
        self.walkie_talkie_waiting: bool = False  # True when agent output [WAITING] tag

    async def close(self) -> None:
        """Clean up resources and close the Claude client (or Codex/Gemini bridge)."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Claude client for workspace session {self.session_id}: {e}")
            finally:
                self._client_entered = False
                self.client = None

        # Close Codex/Gemini bridges
        if self._codex_bridge:
            try:
                await self._codex_bridge.close()
            except Exception as e:
                logger.warning(f"Error closing Codex bridge for session {self.session_id}: {e}")
            finally:
                self._codex_bridge = None

        if self._gemini_bridge:
            try:
                await self._gemini_bridge.close()
            except Exception as e:
                logger.warning(f"Error closing Gemini bridge for session {self.session_id}: {e}")
            finally:
                self._gemini_bridge = None

        # Restore the original .claude/settings.json in the working directory
        # so we don't leave our effortLevel setting behind in the user's project.
        if self._project_settings_path:
            try:
                if self._original_project_settings is not None:
                    # Restore the original file content
                    with open(self._project_settings_path, "w", encoding="utf-8") as f:
                        f.write(self._original_project_settings)
                    logger.debug("Restored original .claude/settings.json at %s", self._project_settings_path)
                elif self._project_settings_path.exists():
                    # File didn't exist before we created it -- remove it
                    self._project_settings_path.unlink()
                    # Also remove .claude/ dir if it's now empty and we created it
                    parent = self._project_settings_path.parent
                    if parent.name == ".claude" and not any(parent.iterdir()):
                        parent.rmdir()
                    logger.debug("Removed temporary .claude/settings.json at %s", self._project_settings_path)
            except Exception as e:
                logger.warning("Failed to restore .claude/settings.json: %s", e)

    async def _fallback_to_api_key(self) -> bool:
        """Tear down the current client and recreate with API key billing.

        Called mid-session when subscription OAuth expires during a query.
        Returns True if the fallback succeeded (new client is ready).
        """
        if not self._shared_opts:
            logger.warning("Cannot fall back to API key: no saved shared_opts from start()")
            return False

        logger.warning(
            "Subscription auth expired mid-session. Falling back to API key billing."
        )

        # Tear down the expired client
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_entered = False
            self.client = None

        try:
            from registry import get_effective_sdk_env

            # Re-create SDK env with API key billing
            sdk_env = get_effective_sdk_env(force_subscription=False)
            self._force_sub = False

            # Re-inject effort level env var
            if self._effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self._effort

            # Update shared options: new env + enable 1M context beta
            self._shared_opts["env"] = sdk_env
            if not self._is_alternative_api:
                self._shared_opts["betas"] = ["context-1m-2025-08-07"]

            logger.info(
                "Recreating client with API key (betas=%s)",
                self._shared_opts.get("betas"),
            )

            # Re-create the client
            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=self._effort, **self._shared_opts)
                )
            except TypeError:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**self._shared_opts)
                )

            await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            self._client_entered = True
            logger.info("Workspace client recreated with API key billing (mid-session fallback)")
            return True

        except Exception:
            logger.exception("API key fallback also failed during mid-session recovery")
            self._client_entered = False
            self.client = None
            return False

    async def _fallback_to_subscription(self) -> bool:
        """Tear down the current client and recreate with subscription OAuth.

        Called when API key billing fails (e.g. credit balance too low) and the
        user may have refreshed their OAuth token via ``claude login``.
        Returns True if the new client started successfully.
        """
        if not self._shared_opts:
            logger.warning("Cannot fall back to subscription: no saved shared_opts from start()")
            return False

        logger.warning(
            "API key billing failed mid-session. Attempting subscription OAuth."
        )

        # Tear down the current client
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_entered = False
            self.client = None

        try:
            from registry import get_effective_sdk_env

            # Re-create SDK env with subscription auth (clears API key)
            sdk_env = get_effective_sdk_env(force_subscription=True)
            self._force_sub = True

            # Re-inject effort level env var
            if self._effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = self._effort

            # Update shared options: subscription = no 1M beta
            self._shared_opts["env"] = sdk_env
            self._shared_opts["betas"] = []

            logger.info("Recreating client with subscription OAuth")

            # Re-create the client
            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=self._effort, **self._shared_opts)
                )
            except TypeError:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**self._shared_opts)
                )

            await asyncio.wait_for(self.client.__aenter__(), timeout=60)
            self._client_entered = True
            logger.info("Workspace client recreated with subscription OAuth (mid-session fallback)")
            return True

        except Exception:
            logger.exception("Subscription fallback also failed during mid-session recovery")
            self._client_entered = False
            self.client = None
            return False

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
                effort=self.cost_settings.get("effort"),
                provider=self.provider,
            )
            self.conversation_id = int(conv.id)  # type coercion: Column[int] -> int
            yield {"type": "conversation_created", "conversation_id": self.conversation_id}

            # Auto-create a git branch for this conversation if the working
            # directory is a git repo, mimicking Claude Code's behavior.
            branch_name = self._create_workspace_branch()
            if branch_name:
                yield {"type": "branch_created", "branch": branch_name}

        # -----------------------------------------------------------------
        # Non-Claude providers: Codex or Gemini — initialize bridge and return.
        # The rest of start() is Claude-specific (SDK client, security settings).
        # -----------------------------------------------------------------
        if self.provider in ("codex", "gemini"):
            async for event in self._start_alt_provider(is_new_conversation):
                yield event
            return

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

            # Include effortLevel in the --settings override file.
            # This file is passed directly to the CLI via the `settings`
            # parameter and is ALWAYS loaded regardless of project detection
            # or setting_sources. This is the most reliable delivery mechanism.
            effort_for_settings = self.cost_settings.get("effort", "high")

            security_settings: dict = {
                "sandbox": {"enabled": False},
                "permissions": {
                    "defaultMode": "acceptEdits",
                    "allow": permissions_list,
                },
            }
            if effort_for_settings in ("low", "medium", "high"):
                # Top-level effortLevel key (recognized by some CLI versions)
                security_settings["effortLevel"] = effort_for_settings
                # Also set via the "env" block — this is a documented settings
                # key that injects env vars into the CLI process, ensuring
                # CLAUDE_CODE_EFFORT_LEVEL reaches the model even if the
                # top-level effortLevel key isn't recognized.
                security_settings["env"] = {
                    "CLAUDE_CODE_EFFORT_LEVEL": effort_for_settings,
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
        # System prompt: passed directly via the ``system_prompt`` parameter
        # (same pattern as the coding agent in client.py).  This avoids
        # writing CLAUDE.md to a scratch directory and lets us set ``cwd``
        # to the user's actual working directory so Bash commands run from
        # the correct location.
        #
        # The workspace prompt is short (~500 chars), well under the
        # Windows 8191-char command-line limit.  If the working directory
        # has its own CLAUDE.md, ``setting_sources=["project"]`` will
        # also load it -- giving the agent both workspace instructions
        # AND the project's own CLAUDE.md context.
        # -----------------------------------------------------------------
        system_prompt = get_workspace_system_prompt(self.working_directory, model=model, context_mode=self.context_mode)
        logger.info(
            "Workspace system_prompt: context_mode=%s, model=%s, cwd=%s",
            self.context_mode, model, self.working_directory,
        )

        # Also write effortLevel to the working directory's .claude/settings.json
        # as a secondary mechanism. The primary mechanism is the --settings file
        # above. This serves as backup when the working directory is a git repo
        # (the CLI detects it as a project and loads project settings).
        #
        # We back up the original file (if any) and restore it in close().
        effort_level = self.cost_settings.get("effort", "high")
        working_dir_path = Path(self.working_directory)
        project_settings_dir = working_dir_path / ".claude"
        project_settings_path = project_settings_dir / "settings.json"
        self._project_settings_path = project_settings_path

        # Back up existing .claude/settings.json before modifying
        if project_settings_path.exists():
            try:
                self._original_project_settings = project_settings_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("Could not back up .claude/settings.json: %s", e)
                self._original_project_settings = None
        else:
            self._original_project_settings = None  # File didn't exist

        # Merge effortLevel into existing settings (preserve other keys)
        project_settings: dict = {}
        if self._original_project_settings:
            try:
                project_settings = json.loads(self._original_project_settings)
            except (json.JSONDecodeError, ValueError):
                project_settings = {}
        if effort_level in ("low", "medium", "high"):
            project_settings["effortLevel"] = effort_level
            # Also inject via the "env" settings block (documented mechanism)
            if "env" not in project_settings:
                project_settings["env"] = {}
            project_settings["env"]["CLAUDE_CODE_EFFORT_LEVEL"] = effort_level
        project_settings_dir.mkdir(parents=True, exist_ok=True)
        with open(project_settings_path, "w") as f:
            json.dump(project_settings, f, indent=2)
        logger.info(
            "Wrote .claude/settings.json: effortLevel=%s, env.CLAUDE_CODE_EFFORT_LEVEL=%s at %s (backed_up=%s)",
            effort_level, effort_level, project_settings_path, self._original_project_settings is not None,
        )

        # Detect alternative API mode (Ollama, GLM, Vertex AI) -- these do not
        # support the 1M context beta, so we must disable it.
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex

        # Bash security hook -- wrapper that injects the working directory as
        # project_dir into context, so the security hook can load project-specific
        # allowed_commands.yaml.  Same pattern as client.py's bash_hook_with_context.
        working_dir_str = self.working_directory

        async def bash_hook_with_context(input_data, tool_use_id=None, context=None):
            """Wrapper that injects working_directory into context for security hook."""
            if context is None:
                context = {}
            context["project_dir"] = working_dir_str
            return await bash_security_hook(input_data, tool_use_id, context)

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
                HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
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

            # Env var fallback for effort (known buggy per #23604, but harmless).
            effort = cs.get("effort", "high")
            if effort in ("low", "medium", "high"):
                sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = effort
            logger.info(
                "EFFORT WIRING: effort=%s, settings_file_effortLevel=%s, "
                "env_var=%s, project_settings=%s, conversation_id=%s, model=%s",
                effort, effort_for_settings,
                sdk_env.get("CLAUDE_CODE_EFFORT_LEVEL"),
                effort_level, self.conversation_id, model,
            )

            # Shared SDK options (used by both the effort= path and the fallback).
            shared_opts: dict[str, Any] = dict(
                model=model,
                cli_path=system_cli,
                system_prompt=system_prompt,
                # "project" loads CLAUDE.md + .claude/settings.json from cwd.
                # "user" loads ~/.claude/settings.json (includes effortLevel
                # when cwd is the home directory and no git repo is detected).
                setting_sources=["project", "user"],
                allowed_tools=WORKSPACE_BUILTIN_TOOLS,
                permission_mode="acceptEdits",
                max_turns=cs["max_turns"],
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

            # Save state for mid-session auth fallback
            self._shared_opts = shared_opts
            self._effort = effort
            self._is_alternative_api = is_alternative_api
            self._force_sub = force_sub

            # Primary: pass effort= directly to ClaudeAgentOptions (SDK ≥0.1.36).
            # Falls back to the settings-file-only approach for older SDK versions.
            try:
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(effort=effort, **shared_opts)
                )
                logger.info("SDK client created with effort=%s (direct param)", effort)
            except TypeError:
                # Older SDK version without effort= parameter.
                # Effort is still delivered via:
                #   1. effortLevel in the --settings override file
                #   2. effortLevel in .claude/settings.json (project settings)
                #   3. CLAUDE_CODE_EFFORT_LEVEL env var (buggy fallback)
                logger.warning(
                    "SDK does not support effort= param (old version). "
                    "Falling back to settings file delivery. "
                    "Upgrade: pip install --upgrade claude-agent-sdk"
                )
                self.client = ClaudeSDKClient(
                    options=ClaudeAgentOptions(**shared_opts)
                )
            # Log the resolved SDK parameters for debugging
            resolved_betas = (
                []
                if is_alternative_api or self.context_mode != "1m"
                else ["context-1m-2025-08-07"]
            )
            has_api_key = bool(sdk_env.get("ANTHROPIC_API_KEY"))
            logger.info(
                "SDK client created: betas=%s, context_mode=%s, force_sub=%s, "
                "has_api_key=%s, is_alt=%s, cwd=%s",
                resolved_betas, self.context_mode, force_sub, has_api_key,
                is_alternative_api, self.working_directory,
            )
            logger.info("Entering workspace Claude client context...")
            _sub_auth_failed = False
            try:
                await asyncio.wait_for(self.client.__aenter__(), timeout=60)
                self._client_entered = True
                logger.info("Workspace Claude client ready")
            except asyncio.TimeoutError:
                if force_sub:
                    logger.warning(
                        "Subscription auth timed out (context_mode=%s, model=%s). "
                        "Will fall back to API key billing.",
                        self.context_mode, self.model,
                    )
                    _sub_auth_failed = True
                else:
                    logger.error(
                        "Timeout (60s) waiting for Claude CLI to start (context_mode=%s, model=%s).",
                        self.context_mode, self.model,
                    )
                    yield {
                        "type": "error",
                        "content": (
                            "The Claude CLI did not start within 60 seconds. "
                            "The model may be overloaded — try again or switch models."
                        ),
                    }
                    yield {"type": "response_done"}
                    return
            except Exception as _enter_err:
                _err_lower = str(_enter_err).lower()
                _auth_hints = ["401", "auth", "oauth", "expired", "credential", "token has expired"]
                if any(h in _err_lower for h in _auth_hints):
                    logger.warning(
                        "Auth failed (%s). Will fall back to API key billing.",
                        _enter_err,
                    )
                    _sub_auth_failed = True
                else:
                    raise  # Re-raise for the outer except to handle

            # ----------------------------------------------------------
            # Fallback: if subscription auth failed, retry with API key.
            # Same pattern used by yt_processor.py / yt_discovery.py.
            # ----------------------------------------------------------
            if _sub_auth_failed:
                # Tear down the failed client
                try:
                    await self.client.__aexit__(None, None, None)
                except Exception:
                    pass
                self.client = None

                # Re-create SDK env with API key billing
                sdk_env = get_effective_sdk_env(force_subscription=False)
                force_sub = False
                self._force_sub = False

                # Re-inject effort level env var
                if effort in ("low", "medium", "high"):
                    sdk_env["CLAUDE_CODE_EFFORT_LEVEL"] = effort

                # Update shared options: new env + enable 1M context beta
                shared_opts["env"] = sdk_env
                if not is_alternative_api:
                    shared_opts["betas"] = ["context-1m-2025-08-07"]

                logger.info(
                    "Retrying with API key billing (betas=%s)",
                    shared_opts.get("betas"),
                )

                # Re-create the client
                try:
                    self.client = ClaudeSDKClient(
                        options=ClaudeAgentOptions(effort=effort, **shared_opts)
                    )
                except TypeError:
                    self.client = ClaudeSDKClient(
                        options=ClaudeAgentOptions(**shared_opts)
                    )

                try:
                    await asyncio.wait_for(self.client.__aenter__(), timeout=60)
                    self._client_entered = True
                    logger.info("Workspace Claude client ready (API key fallback)")
                    yield {
                        "type": "text",
                        "content": (
                            "Subscription auth unavailable -- using API key billing for this session. "
                            "To use free subscription billing, run `claude login` in a terminal."
                        ),
                    }
                except Exception as _retry_err:
                    logger.exception("API key fallback also failed")
                    yield {
                        "type": "error",
                        "content": (
                            f"Failed to initialize workspace: {str(_retry_err)}\n\n"
                            "Neither subscription auth nor API key auth succeeded. "
                            "Set ANTHROPIC_API_KEY in ~/.autoforge/.env or save it in Settings, "
                            "or run `claude login` in a terminal to refresh subscription credentials."
                        ),
                    }
                    yield {"type": "response_done"}
                    return

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
                yield {"type": "response_done"}
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

    async def _start_alt_provider(self, is_new_conversation: bool) -> AsyncGenerator[dict, None]:
        """Initialize a Codex or Gemini session (called from start() for non-Claude providers).

        Creates the appropriate bridge, restores provider_thread_id from DB if
        resuming, and yields the initial greeting / token_usage events.
        """
        from . import workspace_database as db

        provider_display = {"codex": "OpenAI Codex", "gemini": "Google Gemini"}.get(
            self.provider, self.provider
        )

        # Map Claude model names to provider-specific defaults.
        # The session model is always a Claude name like "opus"/"sonnet",
        # which is meaningless to Codex/Gemini CLIs.
        from registry import WORKSPACE_PROVIDERS
        provider_config = WORKSPACE_PROVIDERS.get(self.provider, {})
        provider_model: str | None = None
        if self.provider != "claude":
            # Use the provider's default model — Claude model names don't apply
            provider_model = provider_config.get("default_model")

        try:
            if self.provider == "codex":
                from .codex_bridge import CodexBridge

                self._codex_bridge = CodexBridge(
                    cwd=self.working_directory,
                    model=provider_model,
                )
                # Restore threadId for resumed conversations
                if self.conversation_id and not is_new_conversation:
                    conv = db.get_conversation(self.conversation_id)
                    if conv and conv.get("provider_thread_id"):
                        self._codex_bridge.thread_id = conv["provider_thread_id"]
                        self._provider_thread_id = conv["provider_thread_id"]

                await self._codex_bridge.start()
                self._resolved_model_id = provider_model or "codex-default"
                logger.info("Codex bridge started for session %s (model=%s)", self.session_id, provider_model)

            elif self.provider == "gemini":
                from .gemini_bridge import GeminiBridge

                self._gemini_bridge = GeminiBridge(
                    cwd=self.working_directory,
                    model=provider_model,
                )
                # Restore session_id for resumed conversations
                if self.conversation_id and not is_new_conversation:
                    conv = db.get_conversation(self.conversation_id)
                    if conv and conv.get("provider_thread_id"):
                        self._gemini_bridge.session_id = conv["provider_thread_id"]
                        self._provider_thread_id = conv["provider_thread_id"]

                self._resolved_model_id = provider_model or "gemini-default"
                logger.info("Gemini bridge started for session %s (model=%s)", self.session_id, provider_model)

        except Exception as e:
            logger.exception("Failed to start %s bridge", self.provider)
            yield {"type": "error", "content": f"Failed to initialize {provider_display}: {str(e)}"}
            yield {"type": "response_done"}
            return

        # Emit greeting for new conversations
        if is_new_conversation:
            self._history_loaded = True
            greeting = f"Ready ({provider_display}). Working directory: **{self.working_directory}**."
            yield {"type": "text", "content": greeting}

        # Yield token usage
        assert self.conversation_id is not None
        total = get_conversation_token_total(self.conversation_id)
        msg_count = db.get_message_count(self.conversation_id)
        yield {
            "type": "token_usage",
            "total_tokens": total,
            "context_window": self.context_window,
            "message_count": msg_count,
            "model_id": self._resolved_model_id,
        }
        yield {"type": "response_done"}

    async def _query_alt_provider(self, message: str) -> AsyncGenerator[dict, None]:
        """Route a message through the Codex or Gemini bridge.

        Yields the same event shapes as ``_query_claude()`` so the WebSocket
        protocol stays identical regardless of provider.
        """
        from . import workspace_database as db

        bridge = self._codex_bridge if self.provider == "codex" else self._gemini_bridge
        if not bridge:
            yield {"type": "error", "content": f"{self.provider} bridge not initialized"}
            return

        full_text: list[str] = []
        try:
            async for event in bridge.send_streaming(message):
                event_type = event.get("type", "")
                if event_type == "text":
                    full_text.append(event.get("content", ""))
                    yield event
                elif event_type == "tool_call":
                    yield event
                elif event_type == "error":
                    yield event
                # Other events (init, result, tool_result) are internal — log only
                else:
                    logger.debug("Alt provider event: %s", event_type)
        except Exception as e:
            logger.exception("Error querying %s", self.provider)
            yield {"type": "error", "content": f"{self.provider} error: {str(e)}"}
            return

        # Persist assistant message in DB
        response_text = "".join(full_text)
        if response_text and self.conversation_id:
            tokens = estimate_tokens(response_text)
            add_message(self.conversation_id, "assistant", response_text, tokens)

        # Persist provider thread/session ID for resume
        thread_id = None
        if self.provider == "codex" and self._codex_bridge:
            thread_id = self._codex_bridge.thread_id
        elif self.provider == "gemini" and self._gemini_bridge:
            thread_id = self._gemini_bridge.session_id

        if thread_id and self.conversation_id:
            self._provider_thread_id = thread_id
            try:
                db.update_conversation(
                    self.conversation_id,
                    provider_thread_id=thread_id,
                )
            except Exception as e:
                logger.warning("Failed to persist provider_thread_id: %s", e)

        # Yield token usage
        if self.conversation_id:
            total = get_conversation_token_total(self.conversation_id)
            msg_count = db.get_message_count(self.conversation_id)
            yield {
                "type": "token_usage",
                "total_tokens": total,
                "context_window": self.context_window,
                "message_count": msg_count,
                "model_id": self._resolved_model_id,
            }

    async def send_message(
        self,
        user_message: str,
        attachments: list[ImageAttachment] | None = None,
        library_file_ids: list[int] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Send a user message and stream the provider's response.

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
        # Check that the appropriate backend is ready
        if self.provider == "codex" and not self._codex_bridge:
            yield {"type": "error", "content": "Codex session not initialized. Call start() first."}
            return
        elif self.provider == "gemini" and not self._gemini_bridge:
            yield {"type": "error", "content": "Gemini session not initialized. Call start() first."}
            return
        elif self.provider == "claude" and not self.client:
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

        # Per-message library file attachment: if the caller provided file IDs,
        # inline their content into THIS message only (not auto-injected).
        if library_file_ids:
            try:
                from .workspace_library import get_files_context_by_ids
                library_context, library_tokens = get_files_context_by_ids(
                    library_file_ids, token_cap=self.cost_settings.get("library_cap", 50_000)
                )
                if library_context:
                    message_to_send = f"{library_context}\n\n{message_to_send}"
                    logger.info(
                        "Attached %d library files: ~%d tokens",
                        len(library_file_ids), library_tokens,
                    )
            except Exception as e:
                logger.warning("Failed to load attached library files: %s", e)

        try:
            if self.provider in ("codex", "gemini"):
                async for chunk in self._query_alt_provider(message_to_send):
                    yield chunk
            else:
                async for chunk in self._query_claude(message_to_send, attachments=attachments):
                    yield chunk
            yield {"type": "response_done"}
        except Exception as e:
            logger.exception("Error during workspace %s query", self.provider)
            error_str = str(e).lower()

            # Detect auth errors — attempt mid-session fallback to API key billing.
            # If fallback succeeds, retry the message transparently.
            # NOTE: This triggers regardless of billing mode (_force_sub). Even in
            # 1M/API-key mode, the SDK may use OAuth if no API key is configured.
            _auth_hints = ["401", "authentication_error", "oauth", "token has expired", "credential"]
            if any(h in error_str for h in _auth_hints):
                logger.warning("Auth error during query — attempting API key fallback")
                fallback_ok = await self._fallback_to_api_key()
                if fallback_ok:
                    yield {
                        "type": "text",
                        "content": (
                            "Subscription auth expired — switched to API key billing. "
                            "To use free subscription billing, run `claude login` in a terminal.\n\n"
                        ),
                    }
                    # Retry the message with the new API-key-backed client
                    try:
                        async for chunk in self._query_claude(message_to_send, attachments=attachments):
                            yield chunk
                        yield {"type": "response_done"}
                        return  # Retry succeeded — skip the error path below
                    except Exception as retry_err:
                        logger.exception("Retry after API key fallback also failed")
                        # API key failed too (e.g. credit balance too low).
                        # Last resort: try subscription OAuth in case the user
                        # just ran `claude login` to refresh their token.
                        sub_ok = await self._fallback_to_subscription()
                        if sub_ok:
                            yield {
                                "type": "text",
                                "content": (
                                    "API key billing failed — retrying with subscription auth.\n\n"
                                ),
                            }
                            try:
                                async for chunk in self._query_claude(message_to_send, attachments=attachments):
                                    yield chunk
                                yield {"type": "response_done"}
                                return
                            except Exception as sub_retry_err:
                                logger.exception("Subscription retry also failed")
                                yield {
                                    "type": "error",
                                    "content": (
                                        f"All auth methods failed: {sub_retry_err}\n\n"
                                        "Run `claude login` in a terminal to refresh subscription, "
                                        "or add API credits at console.anthropic.com."
                                    ),
                                }
                        else:
                            yield {
                                "type": "error",
                                "content": (
                                    f"API key billing failed: {retry_err}\n\n"
                                    "Run `claude login` in a terminal to refresh subscription, "
                                    "or add API credits at console.anthropic.com."
                                ),
                            }
                else:
                    yield {
                        "type": "error",
                        "content": (
                            f"Authentication error: {str(e)}\n\n"
                            "Could not fall back to API key billing automatically. "
                            "Set ANTHROPIC_API_KEY in ~/.autoforge/.env or save it in Settings, "
                            "or run `claude login` in a terminal to refresh subscription credentials."
                        ),
                    }
            else:
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

            # Always signal response_done so the frontend resets isLoading.
            # Without this, the "Thinking..." spinner gets permanently stuck.
            yield {"type": "response_done"}

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

                            # Detect auth errors streamed as text by the CLI.
                            # When OAuth expires mid-query, the CLI reports
                            # "Failed to authenticate. API Error: 401 ..."
                            # as a text response instead of raising an exception.
                            # Catch this early so send_message() can trigger the
                            # API-key fallback transparently.
                            if len(full_response) < 500:
                                _resp_lower = full_response.lower()
                                if (
                                    "failed to authenticate" in _resp_lower
                                    or (
                                        "authentication_error" in _resp_lower
                                        and "401" in _resp_lower
                                    )
                                    or "oauth token has expired" in _resp_lower
                                ):
                                    raise RuntimeError(
                                        f"SDK authentication error: {full_response}"
                                    )

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
                        # Falls back to "unknown" instead of the raw UUID so the
                        # debug panel shows a readable name, not an opaque ID.
                        result_tool_use_id = getattr(block, "tool_use_id", None)
                        result_tool_name = (
                            self._tool_use_id_to_name.get(result_tool_use_id, "unknown")
                            if result_tool_use_id
                            else None
                        )

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

                # If the result is an error and the response looks like an auth
                # failure, raise so send_message() can attempt the fallback.
                if is_error and full_response:
                    _resp_lower = full_response.lower()
                    _auth_patterns = [
                        "failed to authenticate",
                        "authentication_error",
                        "oauth token has expired",
                    ]
                    if any(p in _resp_lower for p in _auth_patterns):
                        raise RuntimeError(
                            f"SDK authentication error: {full_response}"
                        )

                # Extract token counts from usage dict
                api_input = usage.get("input_tokens") if isinstance(usage, dict) else None
                api_output = usage.get("output_tokens") if isinstance(usage, dict) else None
                api_cache_create = usage.get("cache_creation_input_tokens") if isinstance(usage, dict) else None
                api_cache_read = usage.get("cache_read_input_tokens") if isinstance(usage, dict) else None

                # Store actual API usage for the token_usage event.
                # context_tokens = total input context sent to the API this turn
                # (new input + cached reads + newly cached).
                context_tokens = (api_input or 0) + (api_cache_read or 0) + (api_cache_create or 0)
                self._last_api_usage = {
                    "input_tokens": api_input or 0,
                    "output_tokens": api_output or 0,
                    "cache_read_tokens": api_cache_read or 0,
                    "cache_creation_tokens": api_cache_create or 0,
                    "context_tokens": context_tokens,
                    "cost_usd": cost_usd or 0.0,
                    "num_turns": num_turns_api,
                }

                logger.info(
                    "ResultMessage: model=%s cost=$%.4f input=%s output=%s "
                    "cache_create=%s cache_read=%s context=%s turns=%s duration=%sms is_error=%s",
                    result_model, cost_usd or 0.0, api_input, api_output,
                    api_cache_create, api_cache_read, context_tokens, num_turns_api,
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

            # Auto-summary DISABLED: was making direct Anthropic API calls
            # (Haiku) using the API key instead of routing through subscription.
            # Re-enable once summary service is rewired to use subscription billing.
            # try:
            #     from . import workspace_database as db
            #     from .workspace_summary import trigger_summary_generation
            #     messages_list = db.get_messages(self.conversation_id)
            #     message_count = len(messages_list)
            #     await trigger_summary_generation(
            #         conversation_id=self.conversation_id,
            #         get_messages_fn=db.get_messages,
            #         save_summary_fn=db.save_summary,
            #         message_count=message_count,
            #     )
            # except Exception as e:
            #     logger.warning(f"Failed to trigger summary generation: {e}")

            # Yield token usage update so the client can render the context-window meter.
            # Prefer actual API numbers from the ResultMessage when available;
            # fall back to heuristic estimates for backward compatibility.
            from . import workspace_database as db
            msg_count = db.get_message_count(self.conversation_id)

            if self._last_api_usage:
                api = self._last_api_usage
                yield {
                    "type": "token_usage",
                    # context_tokens = actual current context window utilization
                    # (input + cache_read + cache_creation from latest API call)
                    "total_tokens": api["context_tokens"],
                    "context_window": self.context_window,
                    "message_count": msg_count,
                    "model_id": self._resolved_model_id,
                    # Detailed breakdown for the UI
                    "api_input_tokens": api["input_tokens"],
                    "api_output_tokens": api["output_tokens"],
                    "api_cache_read_tokens": api["cache_read_tokens"],
                    "api_cache_creation_tokens": api["cache_creation_tokens"],
                    "cost_usd": api["cost_usd"],
                }
            else:
                total = get_conversation_token_total(self.conversation_id)
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
    provider: Optional[str] = None,
) -> WorkspaceChatSession:
    """Create a new workspace session, closing any existing one with the same ID.

    Args:
        session_id: Unique identifier for the session.
        conversation_id: Optional conversation ID to resume.
        working_directory: Absolute path for the agent's working directory.
        context_mode: Context window size -- ``"1m"`` or ``"200k"``. Defaults to ``"1m"``.
        cost_settings: Optional dict of cost control overrides.
        model: Optional model shorthand for per-panel routing (``"opus"`` or ``"sonnet"``).
        provider: CLI provider -- ``"claude"``, ``"codex"``, or ``"gemini"``.

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
            provider=provider,
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
