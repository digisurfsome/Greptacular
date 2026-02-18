"""
Workspace Chat Session
======================

Manages workspace chat sessions with full read/write Claude agent capabilities.
Forked from assistant_chat_session.py with key differences:

- Full tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
- ``acceptEdits`` permission mode (not bypassPermissions)
- Bash security hook via HookMatcher for safe command execution
- No MCP servers (workspace is project-agnostic)
- 100-message context loading with NO per-message truncation
- Token estimation tracked per-message
- Global database (workspace_database), not per-project
- Session registry keyed by session_id string, not project_name
- Working directory configurable per-conversation (defaults to home directory)
- Configurable context window: 1,000,000 tokens (beta ``context-1m-2025-08-07``) or 200,000 tokens
"""

import json
import logging
import os
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher
from dotenv import load_dotenv

from ..schemas import ImageAttachment
from .chat_constants import ROOT_DIR, make_multimodal_message  # noqa: F401
from .workspace_database import (
    add_message,
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


def get_workspace_system_prompt(working_directory: str, model: str = "") -> str:
    """Generate the system prompt for the workspace agent.

    Args:
        working_directory: Absolute path to the agent's working directory.
        model: The model ID being used (e.g. "claude-opus-4-6").

    Returns:
        A system prompt string describing the workspace agent's capabilities and guidelines.
    """
    return f"""You are an expert coding assistant in the IdeaForge Workspace.
You are powered by {model or 'Claude'} with a 1,000,000 token context window.

You have full access to the filesystem and can read, write, edit files, and run bash commands.
Your current working directory is: {working_directory}

## Capabilities

- **Read**: Read file contents
- **Write**: Create or overwrite files
- **Edit**: Make targeted edits to existing files
- **Bash**: Run shell commands (subject to security allowlist)
- **Glob**: Find files by pattern
- **Grep**: Search file contents with regex
- **WebFetch**: Fetch and analyze web content
- **WebSearch**: Search the web for information

## Guidelines

1. Be thorough and precise. Read files before editing them.
2. When modifying code, preserve existing style and conventions.
3. Explain your reasoning and approach before making changes.
4. After making changes, verify them (run linters, type checkers, tests as appropriate).
5. If a bash command might be destructive, explain what it does first.
6. Use absolute file paths when possible.
7. When searching, use Glob and Grep rather than bash find/grep."""


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
    ):
        """Initialize the workspace chat session.

        Args:
            session_id: Unique identifier for this session (used as registry key).
            conversation_id: Optional existing conversation ID to resume.
            working_directory: Absolute path for the agent's cwd. Defaults to the user's home directory.
            context_mode: Context window size -- ``"1m"`` (1,000,000 tokens with beta flag)
                or ``"200k"`` (200,000 tokens, no beta). Defaults to ``"1m"``.
        """
        self.session_id = session_id
        self.conversation_id = conversation_id
        self.working_directory = working_directory or str(Path.home())
        self.context_mode = context_mode
        self.context_window = CONTEXT_WINDOW_TOKENS if context_mode == "1m" else CONTEXT_WINDOW_200K
        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False
        self.created_at = datetime.now()
        self._history_loaded: bool = False

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
            )
            self.conversation_id = int(conv.id)  # type coercion: Column[int] -> int
            yield {"type": "conversation_created", "conversation_id": self.conversation_id}

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

        # Determine model from SDK env (provider-aware) or fallback to env/default
        model = (
            sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_MODEL)
        )

        # -----------------------------------------------------------------
        # System prompt: written as CLAUDE.md in a scratch directory so the
        # SDK reads it via setting_sources=["project"] without clobbering
        # any existing CLAUDE.md in the user's actual working directory.
        # -----------------------------------------------------------------
        workspace_scratch = Path.home() / ".autoforge" / ".workspace_scratch"
        workspace_scratch.mkdir(parents=True, exist_ok=True)
        claude_md_path = workspace_scratch / "CLAUDE.md"
        system_prompt = get_workspace_system_prompt(self.working_directory, model=model)
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)
        logger.info(f"Wrote workspace system prompt to {claude_md_path}")

        # Detect alternative API mode (Ollama, GLM, Vertex AI) -- these do not
        # support the 1M context beta, so we must disable it.
        base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
        is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
        is_alternative_api = bool(base_url) or is_vertex

        # Bash security hook -- same allowlist-based hook the coding agent uses
        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[bash_security_hook])
            ]
        }

        try:
            logger.info(f"Creating workspace ClaudeSDKClient for session {self.session_id}...")
            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=model,
                    cli_path=system_cli,
                    # System prompt loaded from CLAUDE.md via setting_sources.
                    # This avoids Windows command line length limits (~8191 chars).
                    setting_sources=["project"],
                    allowed_tools=WORKSPACE_BUILTIN_TOOLS,
                    permission_mode="acceptEdits",
                    max_turns=100,
                    cwd=str(workspace_scratch),  # Scratch dir for CLAUDE.md
                    settings=str(settings_file.resolve()),
                    env=sdk_env,
                    hooks=hooks,
                    # Enable 1M token context window only in 1M mode.
                    # Disabled for alternative APIs and when user selects 200K mode.
                    betas=(
                        []
                        if is_alternative_api or self.context_mode != "1m"
                        else ["context-1m-2025-08-07"]
                    ),
                )
            )
            logger.info("Entering workspace Claude client context...")
            await self.client.__aenter__()
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
                greeting = (
                    "Hello! I'm your workspace assistant with full read/write access. "
                    "I can read, edit, and create files, run shell commands, and search the web. "
                    f"My working directory is **{self.working_directory}**. How can I help?"
                )

                assert self.conversation_id is not None
                greeting_tokens = estimate_tokens(greeting)
                add_message(self.conversation_id, "assistant", greeting, greeting_tokens)

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

            # Calculate remaining budget for messages (reserve space for summary)
            MESSAGE_TOKEN_BUDGET = 400_000
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
                library_context, library_tokens = get_active_files_context(self.conversation_id)
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
            await self.client.query(make_multimodal_message(content_blocks))
            logger.info(f"Sent multimodal message with {len(attachments)} image(s)")
        else:
            await self.client.query(message)

        full_response = ""

        # Stream the response
        async for msg in self.client.receive_response():
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
                        yield {
                            "type": "tool_call",
                            "tool": tool_name,
                            "input": tool_input,
                        }

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
            }

            # Log premium-zone usage for cost tracking
            try:
                db.log_premium_usage(self.conversation_id)
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
) -> WorkspaceChatSession:
    """Create a new workspace session, closing any existing one with the same ID.

    Args:
        session_id: Unique identifier for the session.
        conversation_id: Optional conversation ID to resume.
        working_directory: Absolute path for the agent's working directory.
        context_mode: Context window size -- ``"1m"`` or ``"200k"``. Defaults to ``"1m"``.

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
