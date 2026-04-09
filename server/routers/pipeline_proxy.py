"""
Pipeline Proxy Router
=====================

Simple HTTP proxy endpoint that lets external services (e.g., Activepieces
running in Docker) call Claude through AutoForge's subscription auth.

External callers POST a system prompt + user message, and get back Claude's
text response.  No API keys required on the caller side — AutoForge handles
auth via ``~/.claude/.credentials.json`` (subscription OAuth).

Health check endpoint included so Docker containers can verify connectivity
before attempting a Claude call.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline-proxy", tags=["pipeline-proxy"])

# Default model for proxy calls — Sonnet is fast and cheap on subscription
DEFAULT_MODEL = "claude-sonnet-4-6"

# Timeout for SDK calls (seconds).  Generous to handle rate-limit retries.
SDK_TIMEOUT_SECONDS = 300


# ============================================================================
# Pydantic Models
# ============================================================================

class ProxyChatRequest(BaseModel):
    """Request body for the proxy chat endpoint.

    Either provide ``system_prompt`` directly, or set ``stage_number`` to
    auto-load the corresponding SKILL.md file from disk.  When both are
    provided, ``system_prompt`` takes precedence (``stage_number`` is
    only used as a fallback when ``system_prompt`` is empty).
    """
    system_prompt: str = ""
    user_message: str
    model: Optional[str] = None
    max_turns: Optional[int] = None
    stage_number: Optional[int] = None


class ProxyChatResponse(BaseModel):
    """Response body for the proxy chat endpoint."""
    success: bool
    response_text: Optional[str] = None
    model: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Check if the proxy is reachable and the Claude CLI is available.

    Docker containers should call this before attempting a Claude call
    to verify connectivity.
    """
    cli_path = shutil.which("claude")
    return {
        "status": "ok",
        "cli_available": cli_path is not None,
    }


@router.post("/chat", response_model=ProxyChatResponse)
async def proxy_chat(body: ProxyChatRequest):
    """Call Claude via AutoForge's subscription auth and return the response.

    This is a synchronous (blocking) endpoint — the caller waits for Claude
    to finish.  Typical response times: 10-60 seconds depending on prompt
    length and model load.

    Uses the exact SDK pattern from ``yt_processor.py._call_via_sdk()``
    with all three known bug fixes applied:
    - ``force_subscription=True`` (never uses API keys)
    - ``permission_mode="acceptEdits"`` (never ``bypassPermissions``)
    - ``receive_response()`` wrapped in try/except for SDK stream errors
    """
    # Resolve system prompt: use explicit value, or auto-load from SKILL.md
    system_prompt = body.system_prompt
    if body.stage_number is not None and not system_prompt.strip():
        from server.routers.pipeline_chat import load_stage_prompt
        system_prompt = load_stage_prompt(body.stage_number)

    model = body.model or DEFAULT_MODEL
    max_turns = body.max_turns or 2
    t0 = time.time()

    try:
        response_text = await _call_claude_sdk(
            system_prompt=system_prompt,
            user_message=body.user_message,
            model=model,
            max_turns=max_turns,
            timeout=SDK_TIMEOUT_SECONDS,
        )
        duration = time.time() - t0
        return ProxyChatResponse(
            success=True,
            response_text=response_text,
            model=model,
            duration_seconds=round(duration, 2),
        )
    except Exception as exc:
        duration = time.time() - t0
        error_msg = str(exc)
        logger.exception("Pipeline proxy call failed after %.1fs: %s", duration, error_msg)
        return ProxyChatResponse(
            success=False,
            model=model,
            duration_seconds=round(duration, 2),
            error=error_msg,
        )


# ============================================================================
# SDK Call — Copied from yt_processor.py._call_via_sdk() with all fixes
# ============================================================================

async def _call_claude_sdk(
    system_prompt: str,
    user_message: str,
    model: str,
    max_turns: int,
    timeout: float,
) -> str:
    """Call Claude via the Agent SDK using SUBSCRIPTION auth ONLY.

    Uses ``ClaudeSDKClient`` with ``force_subscription=True`` — clears
    API key so the CLI falls back to ``~/.claude/.credentials.json``
    (subscription OAuth).  No API credits burned.

    CRITICAL: Uses ``permission_mode="acceptEdits"`` to match ALL working
    SDK clients in this codebase.  ``"bypassPermissions"`` causes exit
    code 3 (Bun runtime crash) on Windows.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    # CRITICAL: Remove CLAUDECODE env var — prevents nested session blocks
    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    # Use a temp directory as cwd so the CLI has somewhere to write
    scratch = tempfile.mkdtemp(prefix="pipeline_proxy_")

    # Create settings file matching the working pattern from yt_processor
    settings_file = Path(scratch) / ".claude-proxy-settings.json"
    settings_file.write_text(json.dumps({
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [],
        },
    }))

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=max_turns,
            permission_mode="acceptEdits",  # NEVER use "bypassPermissions"
            allowed_tools=[],
            cwd=scratch,
            settings=str(settings_file.resolve()),
            setting_sources=["user"],
        )
    )

    logger.info(
        "[proxy] Starting SDK call: model=%s max_turns=%d prompt=%d chars message=%d chars",
        model, max_turns, len(system_prompt), len(user_message),
    )

    async def _run_sdk() -> str:
        sdk_t0 = time.time()

        try:
            await client.__aenter__()
        except Exception as enter_err:
            err_str = str(enter_err)
            logger.error("[proxy] CLI failed to start: %s", err_str)
            raise RuntimeError(
                f"Claude CLI failed to start (model={model}): {err_str}"
            ) from enter_err

        logger.info("[proxy] CLI ready in %.1fs, sending query...", time.time() - sdk_t0)
        await client.query(user_message)

        full_text = ""
        msg_count = 0
        sdk_error: str | None = None
        rate_limit_count = 0

        # The SDK may THROW "Unknown message type: rate_limit_event"
        # instead of yielding it.  If we already have content, catch
        # the exception and use what we collected.
        try:
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                msg_count += 1

                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    rate_limit_count += 1
                    logger.warning("[proxy] Rate limit #%d — SDK will retry", rate_limit_count)
                    continue

                elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text

                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        result_text = ""
                        if hasattr(msg, "result") and msg.result:
                            result_text = str(msg.result)[:500]
                        elif hasattr(msg, "content"):
                            for block in getattr(msg, "content", []):
                                if hasattr(block, "text"):
                                    result_text += block.text
                        sdk_error = (
                            f"SDK error (model={model}): {result_text}"
                            if result_text
                            else f"SDK ResultMessage error (model={model})"
                        )
                        logger.error("[proxy] %s", sdk_error)

        except Exception as stream_exc:
            exc_str = str(stream_exc)
            logger.warning("[proxy] SDK stream exception: %s", exc_str)
            if full_text.strip() and "unknown message type" in exc_str.lower():
                logger.info("[proxy] Recovered: using %d chars collected before error", len(full_text))
            elif full_text.strip():
                logger.warning("[proxy] Stream error after %d chars — using collected text", len(full_text))
            else:
                raise

        total = time.time() - sdk_t0
        logger.info(
            "[proxy] Done: %d chars in %.1fs | %d messages | %d rate limits",
            len(full_text), total, msg_count, rate_limit_count,
        )

        if sdk_error:
            raise RuntimeError(sdk_error)

        if not full_text.strip():
            raise RuntimeError(
                f"Claude SDK returned empty response after {total:.0f}s "
                f"(messages={msg_count}, rate_limits={rate_limit_count})"
            )

        return full_text.strip()

    try:
        return await asyncio.wait_for(_run_sdk(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("[proxy] Timeout after %.0fs", timeout)
        raise RuntimeError(
            f"Claude SDK timed out after {timeout}s. "
            f"The model may be overloaded or rate-limited — try again."
        )
    finally:
        # Always clean up: close client and remove temp directory
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            shutil.rmtree(scratch, ignore_errors=True)
        except Exception:
            pass
