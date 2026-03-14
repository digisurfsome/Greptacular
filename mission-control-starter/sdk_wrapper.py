"""
Mission Control SDK Wrapper
============================
Clean, standalone wrapper for calling Claude via the Agent SDK.
Uses subscription auth (no API keys needed).

Based on the proven pattern from AutoForge's yt_processor._call_via_sdk().

Usage:
    import asyncio
    from sdk_wrapper import call_claude

    result = asyncio.run(call_claude(
        system_prompt="You are a helpful assistant.",
        user_message="Summarize this issue: ...",
    ))
    print(result)
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)


def get_subscription_env() -> dict:
    """
    Build environment variables that force subscription auth.

    How it works: by clearing ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN,
    the Claude CLI falls back to ~/.claude/.credentials.json which uses
    your subscription OAuth. This means no API credits are burned.

    You must have run `claude login` at least once for this to work.
    """
    env = os.environ.copy()

    # Clear any API keys so the CLI uses subscription credentials instead
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("ANTHROPIC_AUTH_TOKEN", None)

    return env


async def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-6",
    timeout: int = 300,
    on_progress=None,
) -> str:
    """
    Call Claude using subscription auth and return the response text.

    Args:
        system_prompt: Instructions for Claude (what role to play, how to respond).
        user_message: The actual request/question to send.
        model: Which Claude model to use. Defaults to Sonnet.
        timeout: Max seconds to wait for a response. Defaults to 300 (5 min).
        on_progress: Optional callback function(message: str) for real-time logs.
                     If provided, progress messages are sent to both the logger
                     and this callback. This is critical for UI feedback.

    Returns:
        The full text response from Claude.

    Raises:
        FileNotFoundError: If the Claude CLI is not installed.
        RuntimeError: If Claude returns no content and an unrecoverable error occurs.
    """

    def _log(message: str) -> None:
        """
        Log to both the Python logger and the on_progress callback.

        Why both? The logger writes to server logs for debugging.
        The on_progress callback streams to the browser so the user
        can see what's happening in real time. Without this, SDK calls
        that take 2+ minutes look like the app is frozen.
        """
        logger.info(message)
        if on_progress:
            on_progress(message)

    # --- Step 1: Find the Claude CLI ---
    cli_path = shutil.which("claude")
    if not cli_path:
        raise FileNotFoundError(
            "Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
        )
    _log(f"Using Claude CLI at: {cli_path}")

    # --- Step 2: Get subscription environment (clears API keys) ---
    sdk_env = get_subscription_env()
    _log(f"Auth: subscription mode (API keys cleared)")

    # --- Step 3: Create a temp scratch directory ---
    # The SDK needs a working directory. We use a temp dir so we don't
    # pollute the project directory with scratch files.
    scratch_dir = tempfile.mkdtemp(prefix="mission_control_")
    _log(f"Scratch dir: {scratch_dir}")

    try:
        # --- Step 4: Create settings file ---
        # CRITICAL: Use "acceptEdits", NOT "bypassPermissions".
        # bypassPermissions crashes the CLI (exit code 3, Bun runtime crash).
        # This was a bug that took 20+ agents to diagnose in AutoForge.
        settings = {
            "permissions": {
                "defaultMode": "acceptEdits",
                "allow": [],
            }
        }
        settings_file = Path(scratch_dir) / "settings.json"
        settings_file.write_text(json.dumps(settings))

        # --- Step 5: Create the SDK client ---
        _log(f"Creating SDK client with model: {model}")
        client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=model,
                cli_path=cli_path,
                system_prompt=system_prompt,
                env=sdk_env,
                max_turns=2,
                permission_mode="acceptEdits",  # NEVER "bypassPermissions"
                allowed_tools=[],
                cwd=scratch_dir,
                settings=str(settings_file),
                setting_sources=["user"],
            )
        )

        # --- Step 6: Send message and collect response ---
        _log("Sending message to Claude...")
        client.send_user_message(user_message)

        full_text = ""

        # CRITICAL: Wrap receive_response() in try/except.
        #
        # The SDK throws "Unknown message type: rate_limit_event" as an
        # EXCEPTION (not a yielded message). This happens AFTER the full
        # response has been collected, which means it throws away a
        # completed 18,000+ char response if not caught.
        #
        # The fix: catch the exception and keep whatever text we already have.
        try:
            async for msg in client.receive_response():
                # Collect text content from the response stream
                if hasattr(msg, "content"):
                    full_text += msg.content
                    _log(f"Received {len(full_text)} chars so far...")
        except Exception as exc:
            error_msg = str(exc).lower()

            if full_text.strip() and "unknown message type" in error_msg:
                # Known bug: rate_limit_event throws after response is complete.
                # We already have the full text, so just use it.
                _log(
                    f"Recovered from rate_limit_event error "
                    f"(have {len(full_text)} chars of response)"
                )
            elif full_text.strip():
                # Unknown error, but we have some text. Try to use it.
                _log(
                    f"Error during response ({exc}), "
                    f"but recovered {len(full_text)} chars"
                )
            else:
                # No text at all — nothing to recover. Re-raise.
                raise RuntimeError(
                    f"Claude returned no content. Error: {exc}"
                ) from exc

        _log(f"Done. Got {len(full_text)} chars total.")
        return full_text

    finally:
        # Clean up the scratch directory
        try:
            shutil.rmtree(scratch_dir)
        except OSError:
            pass  # Best-effort cleanup


# --- Convenience: run from command line for quick testing ---
if __name__ == "__main__":
    import sys

    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Say hello!"

    result = asyncio.run(
        call_claude(
            system_prompt="You are a helpful assistant. Be concise.",
            user_message=message,
            on_progress=print,  # Print progress to terminal
        )
    )
    print("\n--- Response ---")
    print(result)
