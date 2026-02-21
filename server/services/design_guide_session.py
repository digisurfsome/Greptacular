"""
Design Guide Chat Session
==========================

Manages AI-driven design guide conversations for project creation.

Unlike other chat sessions in the codebase, this session:
- Does NOT require a project directory (runs during project creation, before a project exists)
- Does NOT use MCP servers (no feature management needed)
- Does NOT persist conversations to disk (ephemeral, in-memory only)
- DOES parse structured action blocks from Claude's responses to drive UI changes

The session guides users through design style selection by chatting with Claude,
which can recommend styles based on the user's project description, audience,
and preferences. Claude embeds ``action`` fenced code blocks in its responses
to programmatically select styles, colors, and fonts in the UI.
"""

import json
import logging
import os
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger(__name__)

# Scratch directory for design guide settings and system prompt.
# Uses a dedicated subdirectory under ~/.autoforge to avoid clobbering
# any project CLAUDE.md or workspace scratch files.
DESIGN_GUIDE_SCRATCH_DIR = Path.home() / ".autoforge" / ".design_guide_scratch"

# Regex to extract ```action ... ``` fenced code blocks from Claude's text.
# Uses non-greedy match to handle multiple action blocks in a single response.
ACTION_BLOCK_PATTERN = re.compile(
    r"```action\s*\n(.*?)\n\s*```",
    re.DOTALL,
)


def get_design_guide_system_prompt(context: dict) -> str:
    """Generate the system prompt for the design guide assistant.

    The prompt instructs Claude to act as a friendly design consultant that
    helps users pick visual styles for their application. Claude can embed
    structured action blocks to programmatically drive UI selections.

    Args:
        context: Design guide context from the client, which may include
            fields like ``appName``, ``appDescription``, ``availableStyles``,
            and ``currentSelections``.

    Returns:
        A system prompt string.
    """
    # Build a summary of available styles if provided
    styles_summary = ""
    available_styles = context.get("availableStyles", [])
    if available_styles:
        style_lines = []
        for style in available_styles:
            sid = style.get("id", "unknown")
            name = style.get("name", sid)
            desc = style.get("description", "")
            best_for = style.get("best_for", "")
            style_lines.append(f"- **{name}** (id: `{sid}`): {desc}")
            if best_for:
                style_lines.append(f"  Best for: {best_for}")
        styles_summary = "\n".join(style_lines)

    # Build current selections summary if provided
    selections_summary = ""
    current_selections = context.get("currentSelections", {})
    if current_selections:
        sel_parts = []
        if current_selections.get("styleId"):
            sel_parts.append(f"- Current style: `{current_selections['styleId']}`")
        if current_selections.get("colorOverrides"):
            sel_parts.append(f"- Color overrides: {json.dumps(current_selections['colorOverrides'])}")
        if current_selections.get("fontFamily"):
            sel_parts.append(f"- Font: {current_selections['fontFamily']}")
        selections_summary = "\n".join(sel_parts)

    app_name = context.get("appName", "")
    app_description = context.get("appDescription", "")

    return f"""You are a friendly, approachable AI Design Guide helping a user choose the visual style for their application.

## Your Personality

- Warm and encouraging, like a knowledgeable friend who happens to be a designer
- Use plain, non-technical language. Avoid jargon like "design tokens" or "typography hierarchy"
- Be concise. Keep responses to 2-4 short paragraphs maximum
- Ask one question at a time, never overwhelm with multiple choices
- Narrate what you are doing as you "click" things: "Let me pull up that style for you..."

## Your First Message

Start by introducing yourself briefly. Then ask the user about their experience level with design:
- "Have you designed apps before, or is this your first time?"
This helps you calibrate how much explanation to give.

## How You Work

You help users by:
1. Understanding what their app does and who it is for
2. Recommending a visual style that matches their audience and vibe
3. Selecting styles by embedding action blocks in your responses
4. Explaining WHY a style works for their use case, in simple terms

## Embedding Actions

When you want to change something in the UI, include a fenced code block with the language tag `action` containing a JSON object. Example:

I think this clean, modern style would work perfectly for your app. Let me show you what it looks like.

```action
{{"action": "select_style", "styleId": "minimalism"}}
```

Available actions:
- `{{"action": "select_style", "styleId": "<id>"}}` - Select a design style
- `{{"action": "set_color", "token": "<token_name>", "value": "<hex>"}}` - Override a color
- `{{"action": "set_font", "fontFamily": "<font_name>"}}` - Change the font
- `{{"action": "reset_customizations"}}` - Reset all customizations to style defaults

Always narrate what you are selecting and why BEFORE the action block. The user sees the action happen in real time.

## Available Styles

{styles_summary if styles_summary else "(No styles provided - ask the user what kind of look they want and make general recommendations)"}

## App Context

{f"**App Name:** {app_name}" if app_name else "(No app name provided yet)"}
{f"**Description:** {app_description}" if app_description else "(No description provided yet)"}

## Current Selections

{selections_summary if selections_summary else "(Nothing selected yet)"}

## Guidelines

1. If the user seems unsure, start by asking about their app's audience and mood/vibe
2. Recommend 1-2 styles at a time, not all of them
3. When you select a style, explain in simple terms what makes it a good fit
4. If the user wants to customize colors or fonts, guide them through it one step at a time
5. Be encouraging - there are no wrong choices, just different vibes
6. Keep the conversation moving forward. After selecting a style, ask if they like it or want to try something different"""


class DesignGuideChatSession:
    """
    Manages an AI design guide conversation.

    This is an ephemeral, in-memory session that talks to Claude about design
    choices. It does not require a project directory or MCP servers, and does
    not persist conversation history to disk.

    Claude's responses are parsed for ``action`` fenced code blocks, which are
    extracted and sent to the client as separate ``action`` messages so the UI
    can react to them programmatically.
    """

    def __init__(self, session_id: str, context: dict):
        """
        Initialize the design guide session.

        Args:
            session_id: Unique identifier for this session.
            context: Design context from the client containing available styles,
                current selections, app info, etc.
        """
        self.session_id = session_id
        self.context = context
        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False
        self.messages: list[dict] = []
        self.created_at = datetime.now()

    async def close(self) -> None:
        """Clean up resources and close the Claude client."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Claude client for design guide session {self.session_id}: {e}")
            finally:
                self._client_entered = False
                self.client = None

    async def start(self) -> AsyncGenerator[dict, None]:
        """
        Initialize the session with the Claude client and get the initial greeting.

        Writes the system prompt to a scratch CLAUDE.md file, creates the
        ClaudeSDKClient, and sends the initial message to Claude.

        Yields:
            Message chunks:
            - ``{"type": "text", "content": str}`` - Text from Claude
            - ``{"type": "action", "action": dict}`` - Parsed action block
            - ``{"type": "response_done"}`` - Response complete
            - ``{"type": "error", "content": str}`` - Error
        """
        # Ensure scratch directory exists for system prompt and settings
        DESIGN_GUIDE_SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

        # Write security settings - read-only, no tools needed beyond basic conversation
        security_settings = {
            "sandbox": {"enabled": False},
            "permissions": {
                "defaultMode": "bypassPermissions",
                "allow": [],
            },
        }
        settings_file = DESIGN_GUIDE_SCRATCH_DIR / ".design_guide_settings.json"
        with open(settings_file, "w") as f:
            json.dump(security_settings, f, indent=2)

        # Write system prompt as CLAUDE.md so the SDK reads it via setting_sources=["project"]
        system_prompt = get_design_guide_system_prompt(self.context)
        claude_md_path = DESIGN_GUIDE_SCRATCH_DIR / "CLAUDE.md"
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)
        logger.info(f"Wrote design guide system prompt to {claude_md_path}")

        # Resolve the Claude CLI and SDK environment
        system_cli = shutil.which("claude")

        try:
            from registry import get_effective_sdk_env

            # Design guide uses subscription billing (200K context is sufficient)
            sdk_env = get_effective_sdk_env(force_subscription=True)
        except Exception as e:
            logger.exception("Failed to load registry/SDK environment")
            yield {"type": "error", "content": f"Failed to load configuration: {str(e)}"}
            return

        # Use Sonnet for the design guide - faster and cheaper than Opus,
        # and design advice does not require Opus-level reasoning.
        model = (
            sdk_env.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6")
        )

        try:
            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=model,
                    cli_path=system_cli,
                    # System prompt loaded from CLAUDE.md via setting_sources
                    setting_sources=["project"],
                    # No tools needed - pure conversational session
                    allowed_tools=[],
                    permission_mode="bypassPermissions",
                    max_turns=50,
                    cwd=str(DESIGN_GUIDE_SCRATCH_DIR.resolve()),
                    settings=str(settings_file.resolve()),
                    env=sdk_env,
                )
            )
            await self.client.__aenter__()
            self._client_entered = True
            logger.info("Design guide Claude client ready")
        except Exception as e:
            logger.exception("Failed to create design guide Claude client")
            yield {"type": "error", "content": f"Failed to initialize design guide: {str(e)}"}
            return

        # Send initial message to get Claude's greeting
        try:
            async for chunk in self._query_claude("Begin the design guide conversation."):
                yield chunk
            yield {"type": "response_done"}
        except Exception as e:
            logger.exception("Failed to start design guide conversation")
            yield {"type": "error", "content": f"Failed to start conversation: {str(e)}"}

    async def send_message(self, user_message: str, context: Optional[dict] = None) -> AsyncGenerator[dict, None]:
        """
        Send a user message and stream Claude's response.

        Optionally accepts updated context (e.g., current selections changed
        by the user directly in the UI) to include in the message.

        Args:
            user_message: The user's message text.
            context: Optional updated context to append to the message.

        Yields:
            Message chunks:
            - ``{"type": "text", "content": str}`` - Text from Claude
            - ``{"type": "action", "action": dict}`` - Parsed action block
            - ``{"type": "response_done"}`` - Response complete
            - ``{"type": "error", "content": str}`` - Error
        """
        if not self.client:
            yield {"type": "error", "content": "Session not initialized. Call start() first."}
            return

        # Store user message in memory
        self.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
        })

        # If updated context is provided, append it as a system note
        message_to_send = user_message
        if context:
            # Merge updated context into session context
            self.context.update(context)
            # Include context update as a note so Claude knows the current state
            selections = context.get("currentSelections", {})
            if selections:
                context_note = f"\n\n[System note: The user's current selections are now: {json.dumps(selections)}]"
                message_to_send = user_message + context_note

        try:
            async for chunk in self._query_claude(message_to_send):
                yield chunk
            yield {"type": "response_done"}
        except Exception as e:
            logger.exception("Error during design guide Claude query")
            yield {"type": "error", "content": f"Error: {str(e)}"}

    async def _query_claude(self, message: str) -> AsyncGenerator[dict, None]:
        """
        Send a message to Claude and stream the response, parsing action blocks.

        Claude's text response is scanned for fenced code blocks with the
        ``action`` language tag. Each valid action block is extracted and yielded
        as a separate ``{"type": "action", "action": {...}}`` chunk. The
        surrounding text is yielded as ``{"type": "text", "content": "..."}``
        chunks.

        Args:
            message: The message to send to Claude.

        Yields:
            Parsed message chunks (text and action types).
        """
        if not self.client:
            return

        await self.client.query(message)

        full_response = ""

        async for msg in self.client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        text = block.text
                        if text:
                            full_response += text
                            # Parse and yield text with action blocks extracted
                            async for chunk in self._parse_and_yield(text):
                                yield chunk

        # Store the complete response in memory
        if full_response:
            self.messages.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat(),
            })

    async def _parse_and_yield(self, text: str) -> AsyncGenerator[dict, None]:
        """
        Parse text for action blocks and yield text/action chunks.

        Splits the text around ``action`` fenced code blocks. Text segments
        are yielded as ``{"type": "text"}`` and valid JSON action blocks are
        yielded as ``{"type": "action"}``. Invalid JSON in action blocks is
        passed through as regular text.

        Args:
            text: Raw text from Claude that may contain action blocks.

        Yields:
            ``{"type": "text", "content": str}`` or
            ``{"type": "action", "action": dict}`` chunks.
        """
        # Find all action blocks and their positions
        last_end = 0
        for match in ACTION_BLOCK_PATTERN.finditer(text):
            # Yield any text before this action block
            preceding_text = text[last_end:match.start()]
            if preceding_text:
                yield {"type": "text", "content": preceding_text}

            # Try to parse the action block as JSON
            action_json = match.group(1).strip()
            try:
                action = json.loads(action_json)
                yield {"type": "action", "action": action}
            except json.JSONDecodeError:
                # If the JSON is invalid, yield the raw block as text
                logger.warning(f"Invalid JSON in action block: {action_json[:100]}")
                yield {"type": "text", "content": match.group(0)}

            last_end = match.end()

        # Yield any remaining text after the last action block
        remaining = text[last_end:]
        if remaining:
            yield {"type": "text", "content": remaining}


# =============================================================================
# Session Registry
# =============================================================================

# Thread-safe registry of active design guide sessions, keyed by session_id.
_sessions: dict[str, DesignGuideChatSession] = {}
_sessions_lock = threading.Lock()


def get_session(session_id: str) -> Optional[DesignGuideChatSession]:
    """Get an existing design guide session by ID."""
    with _sessions_lock:
        return _sessions.get(session_id)


async def create_session(session_id: str, context: dict) -> DesignGuideChatSession:
    """
    Create a new design guide session, closing any existing one with the same ID.

    Args:
        session_id: Unique identifier for the session.
        context: Design context from the client.

    Returns:
        The newly created session.
    """
    old_session: Optional[DesignGuideChatSession] = None

    with _sessions_lock:
        old_session = _sessions.pop(session_id, None)
        session = DesignGuideChatSession(session_id, context)
        _sessions[session_id] = session

    if old_session:
        try:
            await old_session.close()
        except Exception as e:
            logger.warning(f"Error closing old design guide session {session_id}: {e}")

    return session


async def remove_session(session_id: str) -> None:
    """Remove and close a design guide session."""
    session: Optional[DesignGuideChatSession] = None

    with _sessions_lock:
        session = _sessions.pop(session_id, None)

    if session:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing design guide session {session_id}: {e}")


def list_sessions() -> list[str]:
    """List all active design guide session IDs."""
    with _sessions_lock:
        return list(_sessions.keys())


async def cleanup_all_design_guide_sessions() -> None:
    """Close all active design guide sessions. Called on server shutdown."""
    sessions_to_close: list[DesignGuideChatSession] = []

    with _sessions_lock:
        sessions_to_close = list(_sessions.values())
        _sessions.clear()

    for session in sessions_to_close:
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing design guide session {session.session_id}: {e}")
