"""
Screenshot Analyzer Service
============================

AI-powered analysis of video screenshots using Claude vision.
Performs OCR text extraction, UI/app identification, content classification,
relevance scoring, and context linking to transcript segments.

Uses Claude Haiku 4.5 for fast, cost-effective vision analysis.
"""

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

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
# Analysis
# ---------------------------------------------------------------------------


def _get_api_key() -> Optional[str]:
    """Get the Anthropic API key from settings database or environment."""
    try:
        from registry import get_effective_sdk_env
        sdk_env = get_effective_sdk_env()
        key = sdk_env.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY")


def _encode_image(filepath: str) -> Optional[str]:
    """Read an image file and return its base64-encoded content."""
    path = Path(filepath)
    if not path.exists() or not path.is_file():
        return None
    try:
        data = path.read_bytes()
        return base64.b64encode(data).decode("utf-8")
    except OSError as exc:
        logger.warning("Failed to read image %s: %s", filepath, exc)
        return None


def _get_media_type(filepath: str) -> str:
    """Determine the media type from file extension."""
    ext = Path(filepath).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return media_types.get(ext, "image/jpeg")


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


def analyze_screenshot(filepath: str) -> ScreenshotAnalysis:
    """
    Analyze a single screenshot using Claude Haiku 4.5 vision.

    Returns an ScreenshotAnalysis with OCR text, UI identification,
    content classification, relevance score, and summary.

    Falls back to empty analysis if the API key is not set or the
    call fails.
    """
    api_key = _get_api_key()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — screenshot analysis unavailable")
        return ScreenshotAnalysis()

    img_b64 = _encode_image(filepath)
    if not img_b64:
        return ScreenshotAnalysis()

    media_type = _get_media_type(filepath)

    try:
        import anthropic  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("anthropic package not installed — screenshot analysis unavailable")
        return ScreenshotAnalysis()

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot from a tutorial video. "
                                "Respond with ONLY a JSON object (no markdown, no backticks) with these keys:\n"
                                '- "ocr_text": All visible text (prompts, URLs, data, labels)\n'
                                '- "ui_detected": What app/website is shown (e.g., "Facebook Ads Manager", "VS Code", "Google Search")\n'
                                '- "classification": One of: "prompt", "result", "dashboard", "form", "navigation", "other"\n'
                                '- "relevance_score": 1-10, how useful this is for understanding the tutorial strategy\n'
                                '- "summary": One sentence describing what is happening on screen'
                            ),
                        },
                    ],
                }
            ],
        )

        # Parse the response
        text = response.content[0].text.strip()  # type: ignore[union-attr]
        # Try to extract JSON from the response
        # Sometimes the model wraps it in backticks
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(text)

        return ScreenshotAnalysis(
            ocr_text=str(data.get("ocr_text", "")),
            ui_detected=str(data.get("ui_detected", "")),
            classification=str(data.get("classification", "other")),
            relevance_score=max(1, min(10, int(data.get("relevance_score", 5)))),
            summary=str(data.get("summary", "")),
        )
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

    Each screenshot is analyzed individually with vision AI, then linked to
    the nearest transcript segment.
    """
    results: list[ScreenshotCapture] = []

    for i, filepath in enumerate(filepaths):
        timestamp = timestamps[i] if i < len(timestamps) else 0.0
        reason = reasons[i] if i < len(reasons) else "periodic capture"

        analysis = analyze_screenshot(filepath)
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
