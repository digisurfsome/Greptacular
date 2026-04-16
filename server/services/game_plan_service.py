"""
Game Plan Service — AI-Generated Strategy Summaries
=====================================================

Uses the Claude Agent SDK (subscription auth) to distill video transcripts
into concise, actionable game plans with key strategies and effort estimates.

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
from ..models.filing import GamePlan

logger = logging.getLogger(__name__)

SDK_TIMEOUT_SECONDS = 300

GAME_PLAN_SYSTEM_PROMPT = """You are a strategy distillation assistant. Given a video transcript,
create a concise game plan summary that captures the key strategy and actionable steps.

Return ONLY valid JSON with this exact structure (no markdown fences, no explanation):
{
  "key_strategy": "One-sentence summary of the core strategy",
  "prerequisites": ["Things needed before starting"],
  "steps_overview": [
    {
      "order": 1,
      "title": "Step title",
      "description": "What this step involves",
      "key_actions": ["Specific action 1", "Specific action 2"]
    }
  ],
  "estimated_effort": "low|medium|high",
  "estimated_time": "Total time estimate (e.g. '1 week', '2-3 days')",
  "key_insights": ["Important insight 1", "Important insight 2"],
  "potential_pitfalls": ["Common mistake or risk to watch for"],
  "expected_outcome": "What success looks like after completing this plan"
}

Be concise but specific. Focus on actionable intelligence, not narrative recap.
The game plan should let someone execute the strategy WITHOUT watching the video."""


async def generate_game_plan(
    video_id: str,
    transcript_text: str,
    model: str = "claude-sonnet-4-6",
    on_progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """Generate a game plan from a transcript using Claude SDK."""
    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty")

    user_message = f"Distill this video transcript into a concise game plan:\n\n{transcript_text[:50000]}"
    raw_text = await _call_claude_sdk(
        system_prompt=GAME_PLAN_SYSTEM_PROMPT,
        user_message=user_message,
        model=model,
        on_progress=on_progress,
    )

    game_plan_data = _parse_json_response(raw_text)

    # Store in database
    session = _get_session()
    try:
        game_plan = GamePlan(
            video_id=video_id,
            game_plan_json=json.dumps(game_plan_data),
            model=model,
        )
        session.add(game_plan)
        session.commit()
        session.refresh(game_plan)
        return {
            "id": game_plan.id,
            "video_id": game_plan.video_id,
            "data": game_plan_data,
            "model": game_plan.model,
            "created_at": game_plan.created_at.isoformat() if game_plan.created_at else None,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_game_plan(video_id: str) -> dict | None:
    """Get the most recent game plan for a video."""
    session = _get_session()
    try:
        game_plan = (
            session.query(GamePlan)
            .filter(GamePlan.video_id == video_id)
            .order_by(GamePlan.created_at.desc())
            .first()
        )
        if not game_plan:
            return None
        return {
            "id": game_plan.id,
            "video_id": game_plan.video_id,
            "data": json.loads(game_plan.game_plan_json),
            "model": game_plan.model,
            "created_at": game_plan.created_at.isoformat() if game_plan.created_at else None,
        }
    finally:
        session.close()


async def list_game_plans(video_id: str) -> list[dict]:
    """List all game plans for a video."""
    session = _get_session()
    try:
        plans = (
            session.query(GamePlan)
            .filter(GamePlan.video_id == video_id)
            .order_by(GamePlan.created_at.desc())
            .all()
        )
        return [
            {
                "id": p.id,
                "video_id": p.video_id,
                "data": json.loads(p.game_plan_json),
                "model": p.model,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
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
    """Call Claude via Agent SDK with subscription auth."""
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    def _log(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    scratch = tempfile.mkdtemp(prefix="game_plan_")
    settings_file = pathlib.Path(scratch) / ".claude-gameplan-settings.json"
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
        _log("[GamePlan SDK] Starting...")
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
                            _log(f"[GamePlan SDK] Received {len(full_text):,} chars")
                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        result_text = getattr(msg, "result", "") or ""
                        raise RuntimeError(f"SDK error: {str(result_text)[:500]}")
        except Exception as stream_exc:
            if full_text.strip() and "unknown message type" in str(stream_exc).lower():
                _log(f"[GamePlan SDK] Recovered with {len(full_text):,} chars despite stream error")
            elif full_text.strip():
                _log(f"[GamePlan SDK] Stream error after {len(full_text):,} chars — using collected text")
            else:
                raise

        if not full_text.strip():
            raise RuntimeError("Claude SDK returned empty response for game plan generation")
        return full_text.strip()

    try:
        return await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
    except asyncio.TimeoutError:
        raise RuntimeError(f"Game plan generation timed out after {effective_timeout}s")
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
        raise ValueError(f"Failed to parse game plan JSON: {e}\nRaw text: {text[:500]}")
