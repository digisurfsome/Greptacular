"""
Worksheet Service — AI-Generated Structured Worksheets
=======================================================

Uses the Claude Agent SDK (subscription auth) to extract structured
action items from video transcripts, producing an interactive checklist.

SDK pattern copied from yt_processor.py._call_via_sdk() — do not deviate.
"""

import asyncio
import json
import logging
import os
import pathlib
import shutil
import tempfile
import time
from typing import Callable, Optional

from .filing_service import _get_session
from ..models.filing import Worksheet

logger = logging.getLogger(__name__)

SDK_TIMEOUT_SECONDS = 300

WORKSHEET_SYSTEM_PROMPT = """You are a strategy extraction assistant. Given a video transcript,
extract a structured worksheet with actionable items.

Return ONLY valid JSON with this exact structure (no markdown fences, no explanation):
{
  "title": "Worksheet title based on video topic",
  "action_items": [
    {
      "order": 1,
      "title": "Brief action title",
      "description": "What to do and why",
      "prerequisites": ["Any required tools or accounts"],
      "tools_needed": ["Specific tools, platforms, or services"],
      "time_estimate": "Estimated time (e.g. '15 minutes', '2 hours')",
      "difficulty": "easy|medium|hard",
      "category": "setup|content|outreach|analysis|automation"
    }
  ],
  "prerequisites": ["Overall prerequisites for the entire worksheet"],
  "estimated_total_time": "Total time estimate"
}

Extract 5-15 concrete, actionable items from the transcript. Each item should be
specific enough that someone could complete it without watching the video.
Prioritize by impact (most impactful first)."""


async def generate_worksheet(
    video_id: str,
    transcript_text: str,
    model: str = "claude-sonnet-4-6",
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """Generate a structured worksheet from a transcript using Claude SDK."""
    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty")

    user_message = f"Extract a structured worksheet from this video transcript:\n\n{transcript_text[:50000]}"
    raw_text = await _call_claude_sdk(
        system_prompt=WORKSHEET_SYSTEM_PROMPT,
        user_message=user_message,
        model=model,
        on_progress=on_progress,
    )

    # Parse JSON from response (may have markdown fences)
    worksheet_data = _parse_json_response(raw_text)

    # Store in database
    session = _get_session()
    try:
        worksheet = Worksheet(
            video_id=video_id,
            worksheet_json=json.dumps(worksheet_data),
            model=model,
        )
        session.add(worksheet)
        session.commit()
        session.refresh(worksheet)
        return {
            "id": worksheet.id,
            "video_id": worksheet.video_id,
            "data": worksheet_data,
            "model": worksheet.model,
            "created_at": worksheet.created_at.isoformat() if worksheet.created_at else None,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_worksheet(video_id: str) -> dict | None:
    """Get the most recent worksheet for a video."""
    session = _get_session()
    try:
        worksheet = (
            session.query(Worksheet)
            .filter(Worksheet.video_id == video_id)
            .order_by(Worksheet.created_at.desc())
            .first()
        )
        if not worksheet:
            return None
        return {
            "id": worksheet.id,
            "video_id": worksheet.video_id,
            "data": json.loads(worksheet.worksheet_json),
            "model": worksheet.model,
            "created_at": worksheet.created_at.isoformat() if worksheet.created_at else None,
        }
    finally:
        session.close()


async def list_worksheets(video_id: str) -> list[dict]:
    """List all worksheets for a video."""
    session = _get_session()
    try:
        worksheets = (
            session.query(Worksheet)
            .filter(Worksheet.video_id == video_id)
            .order_by(Worksheet.created_at.desc())
            .all()
        )
        return [
            {
                "id": w.id,
                "video_id": w.video_id,
                "data": json.loads(w.worksheet_json),
                "model": w.model,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in worksheets
        ]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Claude SDK call — copied from yt_processor.py._call_via_sdk()
# ---------------------------------------------------------------------------


async def _call_claude_sdk(
    system_prompt: str,
    user_message: str,
    model: str,
    timeout: float | None = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> str:
    """Call Claude via Agent SDK with subscription auth.

    CRITICAL RULES (from sdk-client-pattern.md):
    1. force_subscription=True — no API keys
    2. permission_mode="acceptEdits" — never bypassPermissions
    3. receive_response() wrapped in try/except
    4. on_progress callbacks passed through
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    def _log(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    # Remove CLAUDECODE to prevent nested session blocking
    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    scratch = tempfile.mkdtemp(prefix="worksheet_")
    settings_file = pathlib.Path(scratch) / ".claude-worksheet-settings.json"
    settings_file.write_text(json.dumps({
        "permissions": {"defaultMode": "acceptEdits", "allow": []},
    }))

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=2,
            permission_mode="acceptEdits",
            allowed_tools=[],
            cwd=scratch,
            settings=str(settings_file.resolve()),
            setting_sources=["user"],
        )
    )

    effective_timeout = timeout if timeout is not None else SDK_TIMEOUT_SECONDS

    async def _run_sdk() -> str:
        _log("[Worksheet SDK] Starting...")
        try:
            await client.__aenter__()
        except Exception as enter_err:
            raise RuntimeError(f"Claude CLI failed to start: {enter_err}") from enter_err

        await client.query(user_message)
        full_text = ""

        try:
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
                            _log(f"[Worksheet SDK] Received {len(full_text):,} chars")
                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        result_text = getattr(msg, "result", "") or ""
                        raise RuntimeError(f"SDK error: {str(result_text)[:500]}")
        except Exception as stream_exc:
            if full_text.strip() and "unknown message type" in str(stream_exc).lower():
                _log(f"[Worksheet SDK] Recovered with {len(full_text):,} chars despite stream error")
            elif full_text.strip():
                _log(f"[Worksheet SDK] Stream error after {len(full_text):,} chars — using collected text")
            else:
                raise

        if not full_text.strip():
            raise RuntimeError("Claude SDK returned empty response for worksheet generation")
        return full_text.strip()

    try:
        return await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
    except asyncio.TimeoutError:
        raise RuntimeError(f"Worksheet generation timed out after {effective_timeout}s")
    finally:
        try:
            await client.__aexit__(None, None, None)
        except Exception as e:
            logger.warning("SDK client shutdown error: %s", e)
        shutil.rmtree(scratch, ignore_errors=True)


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from Claude response, stripping markdown fences if present."""
    import re as _re

    text = raw_text.strip()
    # Search for JSON inside markdown fences (handles text before the fence)
    fence_match = _re.search(r'```(?:json)?\s*\n(.*?)\n```', text, _re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse worksheet JSON: {e}\nRaw text: {text[:500]}")
