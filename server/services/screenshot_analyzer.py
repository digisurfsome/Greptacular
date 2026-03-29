"""
Screenshot Analyzer Service
============================

AI-powered analysis of video screenshots using Claude vision.
Performs OCR text extraction, UI/app identification, content classification,
relevance scoring, and context linking to transcript segments.

Uses Claude via SUBSCRIPTION AUTH (SDK subprocess) — NO API CREDITS BURNED.
The Claude CLI's Read tool can view images natively, so we send file paths
and let the CLI analyze them.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class ScreenshotAnalysis(BaseModel):
    """Result of AI vision analysis on a single screenshot."""

    ocr_text: str = ""
    ui_detected: str = ""
    classification: str = "other"  # prompt | result | dashboard | form | navigation | other
    relevance_score: int = Field(default=5, ge=1, le=10)
    summary: str = ""


class ScreenshotCapture(BaseModel):
    """A captured and analyzed screenshot from a video."""

    timestamp: float
    reason: str
    image_path: str
    ocr_text: str = ""
    ui_detected: str = ""
    classification: str = "other"
    relevance_score: int = Field(default=5, ge=1, le=10)
    transcript_segment: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_nearest_transcript(
    timestamp: float,
    transcript_segments: list[dict],
) -> str:
    """Find the transcript segment closest to the given timestamp."""
    if not transcript_segments:
        return ""

    best_segment = ""
    best_distance = float("inf")

    for seg in transcript_segments:
        start = float(seg.get("start", 0))
        distance = abs(start - timestamp)
        if distance < best_distance:
            best_distance = distance
            best_segment = seg.get("text", "")

    return best_segment


# ---------------------------------------------------------------------------
# SDK-based Analysis (Subscription Auth)
# ---------------------------------------------------------------------------

SDK_TIMEOUT_SECONDS = 300


async def _call_via_sdk(
    user_message: str,
    model: str = "claude-haiku-4-5",
    timeout: float | None = None,
    cwd: str | None = None,
) -> str:
    """Call Claude via the Agent SDK using SUBSCRIPTION auth ONLY.

    Copied from yt_processor._call_via_sdk() — uses force_subscription=True
    so the CLI falls back to ~/.claude/.credentials.json (subscription OAuth).
    NO API CREDITS BURNED.

    AGENTS: DO NOT add an API key fallback here. If this fails, let it fail.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    t0 = time.time()

    # CRITICAL: Remove CLAUDECODE env var — it blocks nested Claude CLI sessions.
    os.environ.pop("CLAUDECODE", None)

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH")

    sdk_env = get_effective_sdk_env(force_subscription=True)
    sdk_env.pop("CLAUDECODE", None)

    # Use provided cwd or a temp directory
    scratch = cwd or tempfile.mkdtemp(prefix="screenshot_analyzer_")
    own_scratch = cwd is None

    # Create settings file matching the working pattern
    settings_file = Path(scratch) / ".claude-screenshot-settings.json"
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
            system_prompt=(
                "You are a screenshot analysis assistant. You analyze images from tutorial videos. "
                "You MUST use the Read tool to view image files when given file paths. "
                "Always respond with valid JSON only — no markdown, no backticks, no explanation."
            ),
            env=sdk_env,
            max_turns=5,
            permission_mode="acceptEdits",
            allowed_tools=["Read"],
            cwd=scratch,
            settings=str(settings_file.resolve()),
            setting_sources=["user"],
        )
    )

    effective_timeout = timeout if timeout is not None else SDK_TIMEOUT_SECONDS

    async def _run_sdk() -> str:
        full_text = ""
        msg_count = 0
        rate_limit_count = 0

        try:
            await client.__aenter__()
        except Exception as enter_err:
            raise RuntimeError(
                f"Claude CLI failed to start for screenshot analysis: {enter_err}"
            ) from enter_err

        await client.query(user_message)

        try:
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                msg_count += 1

                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    rate_limit_count += 1
                    continue
                elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        result_text = ""
                        if hasattr(msg, "result") and msg.result:
                            result_text = str(msg.result)[:500]
                        raise RuntimeError(f"SDK error: {result_text}")
        except Exception as stream_exc:
            exc_str = str(stream_exc)
            if full_text.strip() and "unknown message type" in exc_str.lower():
                pass  # Use collected text
            elif full_text.strip():
                pass  # Try to use what we have
            else:
                raise

        if not full_text.strip():
            raise RuntimeError(
                f"Claude SDK returned empty response. "
                f"Messages: {msg_count}, Rate limits: {rate_limit_count}"
            )
        return full_text.strip()

    try:
        return await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
    finally:
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass
        if own_scratch:
            try:
                shutil.rmtree(scratch, ignore_errors=True)
            except Exception:
                pass


def _parse_analysis_json(text: str) -> list[dict]:
    """Parse JSON response from the SDK — handles single object or array."""
    # Strip markdown code fences if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Try parsing as JSON array first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
    except json.JSONDecodeError:
        pass

    # Try to find JSON array
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        try:
            result = json.loads(array_match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Try to find individual JSON objects
    results = []
    for m in re.finditer(r"\{[^{}]*\}", text):
        try:
            results.append(json.loads(m.group(0)))
        except json.JSONDecodeError:
            continue
    return results


async def _analyze_batch_via_sdk(
    filepaths: list[str],
) -> list[ScreenshotAnalysis]:
    """Analyze a batch of screenshots via the SDK (subscription auth)."""
    if not filepaths:
        return []

    # Build the prompt — ask Claude to read each image and analyze it
    file_list = "\n".join(f"  {i + 1}. {fp}" for i, fp in enumerate(filepaths))
    prompt = (
        f"Analyze these {len(filepaths)} screenshots from a tutorial video.\n\n"
        f"Image files to read and analyze:\n{file_list}\n\n"
        "For EACH image, use the Read tool to view it, then analyze what you see.\n\n"
        "After viewing ALL images, respond with a JSON array containing one object per image, "
        "in the same order as the files listed above. Each object must have these keys:\n"
        '- "ocr_text": All visible text (prompts, URLs, data, labels)\n'
        '- "ui_detected": What app/website is shown (e.g., "Facebook Ads Manager", "VS Code")\n'
        '- "classification": One of: "prompt", "result", "dashboard", "form", "navigation", "other"\n'
        '- "relevance_score": 1-10, how useful this is for understanding the tutorial strategy\n'
        '- "summary": One sentence describing what is happening on screen\n\n'
        "Respond with ONLY the JSON array. No markdown, no backticks, no explanation."
    )

    try:
        # Use the parent directory of the screenshots as cwd so Read can access them
        first_path = Path(filepaths[0])
        cwd = str(first_path.parent)

        response = await _call_via_sdk(prompt, cwd=cwd)
        parsed = _parse_analysis_json(response)

        results: list[ScreenshotAnalysis] = []
        for i in range(len(filepaths)):
            if i < len(parsed):
                data = parsed[i]
                results.append(ScreenshotAnalysis(
                    ocr_text=str(data.get("ocr_text", "")),
                    ui_detected=str(data.get("ui_detected", "")),
                    classification=str(data.get("classification", "other")),
                    relevance_score=max(1, min(10, int(data.get("relevance_score", 5)))),
                    summary=str(data.get("summary", "")),
                ))
            else:
                results.append(ScreenshotAnalysis())

        return results
    except Exception as exc:
        logger.warning("Screenshot batch analysis via SDK failed: %s", exc)
        return [ScreenshotAnalysis() for _ in filepaths]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_screenshot(filepath: str) -> ScreenshotAnalysis:
    """
    Analyze a single screenshot using Claude via subscription auth (SDK).

    Returns a ScreenshotAnalysis with OCR text, UI identification,
    content classification, relevance score, and summary.

    Falls back to empty analysis if the SDK call fails.
    """
    try:
        results = asyncio.run(_analyze_batch_via_sdk([filepath]))
        return results[0] if results else ScreenshotAnalysis()
    except Exception as exc:
        logger.warning("Screenshot analysis failed for %s: %s", filepath, exc)
        return ScreenshotAnalysis()


def analyze_screenshots_batch(
    filepaths: list[str],
    timestamps: list[float],
    reasons: list[str],
    transcript_segments: list[dict],
) -> list[ScreenshotCapture]:
    """
    Analyze a batch of screenshots and return enriched ScreenshotCapture objects.

    Uses the Claude SDK (subscription auth) to analyze all screenshots in one
    batched call for efficiency. Each screenshot is linked to the nearest
    transcript segment.

    NO API CREDITS BURNED — uses subscription auth via force_subscription=True.
    """
    # Run the async SDK analysis from sync context
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're already in an async context — run in a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            analyses = pool.submit(
                asyncio.run, _analyze_batch_via_sdk(filepaths)
            ).result(timeout=SDK_TIMEOUT_SECONDS + 30)
    else:
        analyses = asyncio.run(_analyze_batch_via_sdk(filepaths))

    results: list[ScreenshotCapture] = []
    for i, filepath in enumerate(filepaths):
        timestamp = timestamps[i] if i < len(timestamps) else 0.0
        reason = reasons[i] if i < len(reasons) else "periodic capture"
        analysis = analyses[i] if i < len(analyses) else ScreenshotAnalysis()
        nearest_text = _find_nearest_transcript(timestamp, transcript_segments)

        results.append(
            ScreenshotCapture(
                timestamp=timestamp,
                reason=reason,
                image_path=filepath,
                ocr_text=analysis.ocr_text,
                ui_detected=analysis.ui_detected,
                classification=analysis.classification,
                relevance_score=analysis.relevance_score,
                transcript_segment=nearest_text,
            )
        )

    return results
