"""
Workspace Summary Service
=========================

Generates conversation summaries using a lightweight Claude model (Haiku).
Summaries are stored in a history table and cached on the conversation record.

The summary generation is fire-and-forget -- it runs as an ``asyncio.create_task``
background coroutine so it never blocks the main chat WebSocket.
"""

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Summary generation threshold: generate a new summary every N messages
SUMMARY_INTERVAL = 50

# Maximum tokens to allocate for summary in context
SUMMARY_TOKEN_BUDGET = 2000

SUMMARY_PROMPT = """Summarize this conversation concisely. Capture:
1) What is being discussed or built
2) Key decisions made
3) Current status and progress
4) Open questions or unresolved items

Keep the summary under 500 words. Be specific about technical details, file names, and decisions. \
Do not include pleasantries or meta-commentary about the conversation itself."""


async def should_generate_summary(
    message_count: int,
    last_summary_message_count: Optional[int],
) -> bool:
    """Check if we should generate a summary based on message count thresholds.

    Returns True when ``message_count`` crosses a multiple of ``SUMMARY_INTERVAL``
    since the last summary was generated.

    Args:
        message_count: Current total number of messages in the conversation.
        last_summary_message_count: The message count recorded when the last
            summary was generated, or None if no summary exists yet.

    Returns:
        True if a new summary should be generated.
    """
    if message_count < SUMMARY_INTERVAL:
        return False

    last_count = last_summary_message_count or 0
    # Check if we've crossed a new threshold since the last summary
    return (message_count // SUMMARY_INTERVAL) > (last_count // SUMMARY_INTERVAL)


async def generate_summary(
    conversation_id: int,
    messages: list[dict],
    message_count: int,
) -> Optional[str]:
    """Generate a summary using a Haiku model call.

    This runs as a fire-and-forget task -- it should NOT block the main chat.
    Uses the Anthropic Python SDK directly (not the Agent SDK) for a simple
    one-shot completion.

    Args:
        conversation_id: The conversation to summarize.
        messages: List of message dicts with 'role' and 'content' keys.
        message_count: Total messages in the conversation at time of generation.

    Returns:
        The summary text, or None if generation failed.
    """
    try:
        import anthropic
    except ImportError:
        logger.error(
            "anthropic package not installed. Cannot generate summaries. "
            "Install with: pip install anthropic"
        )
        return None

    try:
        # Determine the Haiku model to use
        model = os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-3-5-haiku-20241022")

        # Build the messages payload: include all provided messages as context
        formatted_messages: list[dict] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content.strip():
                formatted_messages.append({"role": role, "content": content})

        if not formatted_messages:
            logger.warning("No messages to summarize for conversation %d", conversation_id)
            return None

        # Add the summary request as the final user message
        formatted_messages.append({
            "role": "user",
            "content": SUMMARY_PROMPT,
        })

        # Ensure messages alternate correctly (Anthropic requirement):
        # If the first message is assistant, prepend a system context
        if formatted_messages[0]["role"] == "assistant":
            formatted_messages.insert(0, {
                "role": "user",
                "content": "(Beginning of conversation)",
            })

        # Merge consecutive same-role messages
        merged: list[dict] = []
        for msg in formatted_messages:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(dict(msg))
        formatted_messages = merged

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system="You are a conversation summarizer. Produce clear, concise summaries.",
            messages=formatted_messages,
        )

        summary_text = response.content[0].text if response.content else None
        if summary_text:
            logger.info(
                "Generated summary for conversation %d (%d messages, %d chars)",
                conversation_id,
                message_count,
                len(summary_text),
            )
        return summary_text

    except Exception:
        logger.exception("Failed to generate summary for conversation %d", conversation_id)
        return None


async def trigger_summary_generation(
    conversation_id: int,
    get_messages_fn,
    save_summary_fn,
    message_count: int,
) -> None:
    """Fire-and-forget summary generation.

    Call this after each message exchange. It checks the threshold and
    spawns a background task if a summary is needed.

    Args:
        conversation_id: The conversation ID.
        get_messages_fn: Callable that takes conversation_id and returns list[dict] of messages.
        save_summary_fn: Callable(conversation_id, summary_text, message_count) to persist.
        message_count: Current total message count.
    """
    from . import workspace_database as db

    # Get the last summary's message count
    last_summary = db.get_latest_summary(conversation_id)
    last_count = last_summary["message_count"] if last_summary else None

    if not await should_generate_summary(message_count, last_count):
        return

    # Spawn background task -- never blocks the chat WebSocket
    asyncio.create_task(
        _background_summarize(conversation_id, get_messages_fn, save_summary_fn, message_count)
    )


async def _background_summarize(
    conversation_id: int,
    get_messages_fn,
    save_summary_fn,
    message_count: int,
) -> None:
    """Background coroutine that generates and saves a summary.

    Args:
        conversation_id: The conversation to summarize.
        get_messages_fn: Callable that takes conversation_id and returns list[dict].
        save_summary_fn: Callable(conversation_id, summary_text, message_count) to persist.
        message_count: Total messages at time of trigger.
    """
    try:
        messages = get_messages_fn(conversation_id)
        summary_text = await generate_summary(conversation_id, messages, message_count)
        if summary_text:
            save_summary_fn(conversation_id, summary_text, message_count)
    except Exception:
        logger.exception("Background summary generation failed for conversation %d", conversation_id)
