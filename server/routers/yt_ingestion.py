"""
YT Ingestion Router
====================

Provides YouTube video ingestion endpoints for the YT Strategy Lab.
Extracts transcripts, metadata, description links, and screenshot suggestions
from YouTube videos.

Dependencies (not in requirements.txt — install manually):
  pip install youtube-transcript-api yt-dlp

The transcript extraction uses youtube-transcript-api (no API key needed).
Metadata extraction uses yt-dlp (no API key needed).
An optional YOUTUBE_API_KEY env var can be set for YouTube Data API v3
metadata, but yt-dlp is the primary fallback and works without any key.
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yt-lab", tags=["yt-lab"])

# Maximum transcript length (characters) to prevent oversized responses
MAX_TRANSCRIPT_CHARS = 500_000

# Phrases that suggest a visual element is being shown on screen
VISUAL_CUE_PATTERNS: list[re.Pattern[str]] = [
    # Existing verbal cues
    re.compile(r"\b(look at this|as you can see|here'?s the prompt|on screen)\b", re.IGNORECASE),
    re.compile(r"\b(take a look|check this out|you can see here|shown here)\b", re.IGNORECASE),
    re.compile(r"\b(here'?s what|let me show|i'?ll show|showing you)\b", re.IGNORECASE),
    re.compile(r"\b(right here|this is what|the result|the output)\b", re.IGNORECASE),
    re.compile(r"\b(screenshot|screen shot|screen capture)\b", re.IGNORECASE),
    re.compile(r"\b(paste this|copy this|type this in|enter this)\b", re.IGNORECASE),
    re.compile(r"\b(the settings|the config|the interface|the dashboard)\b", re.IGNORECASE),
    # Screen transition cues
    re.compile(r"\b(i opened up|i went to|i navigated to|i clicked on)\b", re.IGNORECASE),
    re.compile(r"\b(i'?m going to|let me go to|switch over to|heading to)\b", re.IGNORECASE),
    # Result cues
    re.compile(r"\b(here'?s what it created|the output was|it generated)\b", re.IGNORECASE),
    re.compile(r"\b(and it gave me|the result is|this is what we got)\b", re.IGNORECASE),
    # Instruction cues
    re.compile(r"\b(all i typed was|i just prompted it to|i asked it to)\b", re.IGNORECASE),
    re.compile(r"\b(the prompt i used|i wrote this|i entered this)\b", re.IGNORECASE),
]

# Duration-based screenshot interval in seconds
DURATION_SCREENSHOT_INTERVAL = 45

# Maximum number of screenshots per video to prevent abuse
MAX_SCREENSHOTS = 30

# Minimum gap between screenshots in seconds (for deduplication)
MIN_SCREENSHOT_GAP = 5


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Request body for video ingestion."""

    url: str = Field(..., min_length=5, max_length=2048)
    capture_screenshots: bool = False


class TranscriptSegment(BaseModel):
    """A single segment of the video transcript."""

    text: str
    start: float
    duration: float


class ScreenshotSuggestion(BaseModel):
    """A suggested timestamp for capturing a screenshot."""

    timestamp: float
    reason: str
    captured: bool = False
    filepath: Optional[str] = None


class ScreenshotCapture(BaseModel):
    """A captured and analyzed screenshot from a video."""

    timestamp: float
    reason: str
    image_path: str
    ocr_text: str = ""
    ui_detected: str = ""
    classification: str = "other"  # prompt | result | dashboard | form | navigation | other
    relevance_score: int = Field(default=5, ge=1, le=10)
    transcript_segment: str = ""


class IngestResponse(BaseModel):
    """Complete ingestion result returned to the client."""

    video_id: str
    title: str
    channel: str
    duration: int
    publish_date: str
    thumbnail_url: str
    description: str
    transcript: list[TranscriptSegment]
    extracted_urls: list[str]
    screenshot_suggestions: list[ScreenshotSuggestion]
    screenshots: list[str]
    # Enhanced screenshot intelligence fields
    analyzed_screenshots: list[ScreenshotCapture] = []
    screenshot_summary: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from various URL formats.

    Supports:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
      - https://youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _get_transcript(video_id: str) -> list[TranscriptSegment]:
    """
    Fetch the transcript for a YouTube video using youtube-transcript-api.

    Falls back gracefully if the library is not installed or if no transcript
    is available.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("youtube-transcript-api not installed — transcript extraction unavailable")
        return []

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_data = ytt_api.fetch(video_id)

        segments: list[TranscriptSegment] = []
        total_chars = 0
        for entry in transcript_data:
            text = entry.text  # type: ignore[attr-defined]
            start = float(entry.start)  # type: ignore[attr-defined]
            duration = float(entry.duration)  # type: ignore[attr-defined]
            total_chars += len(text)
            if total_chars > MAX_TRANSCRIPT_CHARS:
                logger.warning("Transcript exceeded %d chars, truncating", MAX_TRANSCRIPT_CHARS)
                break
            segments.append(TranscriptSegment(text=text, start=start, duration=duration))
        return segments
    except Exception as exc:
        logger.warning("Failed to fetch transcript for %s: %s", video_id, exc)
        return []


def _get_metadata_ytdlp(url: str) -> dict:
    """
    Extract video metadata using yt-dlp (no API key required).

    Returns a dict with title, channel, duration, publish_date, thumbnail_url,
    and description. Returns empty/default values if yt-dlp is not installed.
    """
    ytdlp_path = shutil.which("yt-dlp")
    if not ytdlp_path:
        logger.warning("yt-dlp not found on PATH — metadata extraction unavailable")
        return {}

    try:
        result = subprocess.run(
            [
                ytdlp_path,
                "--dump-json",
                "--no-download",
                "--no-warnings",
                "--no-playlist",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("yt-dlp returned non-zero exit code: %s", result.stderr[:500])
            return {}

        data = json.loads(result.stdout)
        return {
            "title": data.get("title", "Unknown"),
            "channel": data.get("channel", data.get("uploader", "Unknown")),
            "duration": int(data.get("duration", 0)),
            "publish_date": data.get("upload_date", ""),
            "thumbnail_url": data.get("thumbnail", ""),
            "description": data.get("description", ""),
        }
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp timed out fetching metadata")
        return {}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("yt-dlp metadata extraction failed: %s", exc)
        return {}


def _clean_extracted_url(url: str) -> str:
    """Strip trailing punctuation without breaking parenthesized URLs like Wikipedia."""
    # First strip trailing punctuation that is never part of a URL
    url = url.rstrip(".,;:!?")
    # Only strip trailing ')' if parentheses are unbalanced (more close than open)
    while url.endswith(")") and url.count(")") > url.count("("):
        url = url[:-1]
    return url


def _extract_urls(text: str) -> list[str]:
    """Extract all URLs from a block of text (e.g., video description)."""
    url_pattern = re.compile(
        r"https?://[^\s<>\"']+",
        re.IGNORECASE,
    )
    urls = url_pattern.findall(text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        u = _clean_extracted_url(u)
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _analyze_screenshot_moments(
    segments: list[TranscriptSegment],
    video_duration: int = 0,
) -> list[ScreenshotSuggestion]:
    """
    Analyze transcript segments for moments where a screenshot would be
    valuable — e.g., when the speaker references something visual on screen.

    Also generates duration-based suggestions as a baseline (every
    DURATION_SCREENSHOT_INTERVAL seconds) to ensure coverage of moments
    that verbal cues might miss.
    """
    suggestions: list[ScreenshotSuggestion] = []
    seen_timestamps: set[int] = set()

    # 1. Cue-based detection from transcript
    for segment in segments:
        for pattern in VISUAL_CUE_PATTERNS:
            match = pattern.search(segment.text)
            if match:
                # Round to nearest second to avoid near-duplicate timestamps
                rounded = int(segment.start)
                if rounded not in seen_timestamps:
                    seen_timestamps.add(rounded)
                    suggestions.append(
                        ScreenshotSuggestion(
                            timestamp=segment.start,
                            reason=f'Speaker says: "{match.group(0)}" — likely showing something on screen',
                        )
                    )
                # Only one suggestion per segment to avoid spam
                break

    # 2. Duration-based periodic suggestions (baseline coverage)
    if video_duration > 0:
        t = float(DURATION_SCREENSHOT_INTERVAL)
        while t < video_duration:
            rounded = int(t)
            # Only add if not too close to an existing cue-based suggestion
            too_close = any(abs(rounded - ts) < MIN_SCREENSHOT_GAP for ts in seen_timestamps)
            if not too_close:
                seen_timestamps.add(rounded)
                suggestions.append(
                    ScreenshotSuggestion(
                        timestamp=t,
                        reason="Periodic capture (baseline coverage)",
                    )
                )
            t += DURATION_SCREENSHOT_INTERVAL

    # Sort by timestamp and cap at MAX_SCREENSHOTS
    suggestions.sort(key=lambda s: s.timestamp)
    return suggestions[:MAX_SCREENSHOTS]


def _capture_screenshots(
    url: str,
    timestamps: list[float],
    video_id: str,
    multi_frame: bool = True,
) -> tuple[list[str], list[float]]:
    """
    Capture screenshots at specific timestamps using yt-dlp + ffmpeg.

    When multi_frame is True, captures 3 frames around each cue timestamp
    (cue-2s, cue, cue+2s) to ensure the most informative frame is captured.

    Returns a tuple of (file_paths, actual_timestamps) for successfully
    captured images. Requires both yt-dlp and ffmpeg on PATH.
    """
    ytdlp_path = shutil.which("yt-dlp")
    ffmpeg_path = shutil.which("ffmpeg")

    if not ytdlp_path or not ffmpeg_path:
        logger.warning("yt-dlp or ffmpeg not found — screenshot capture unavailable")
        return [], []

    if not timestamps:
        return [], []

    # Create a persistent temp directory for screenshots
    screenshot_dir = Path(tempfile.gettempdir()) / "yt_lab_screenshots" / video_id
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    # Expand timestamps for multi-frame capture
    expanded_timestamps: list[float] = []
    if multi_frame:
        for ts in timestamps:
            for offset in [-2.0, 0.0, 2.0]:
                candidate = max(0.0, ts + offset)
                # Deduplicate: skip if too close to an existing timestamp
                too_close = any(abs(candidate - et) < 1.0 for et in expanded_timestamps)
                if not too_close:
                    expanded_timestamps.append(candidate)
    else:
        expanded_timestamps = list(timestamps)

    # Cap at MAX_SCREENSHOTS
    expanded_timestamps = expanded_timestamps[:MAX_SCREENSHOTS]

    captured: list[str] = []
    captured_timestamps: list[float] = []

    # Get the direct video URL once (reuse for all frames)
    direct_url: Optional[str] = None
    try:
        get_url_result = subprocess.run(
            [ytdlp_path, "--get-url", "--format", "best[height<=720]", url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if get_url_result.returncode == 0:
            direct_url = get_url_result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("Failed to get direct URL: %s", exc)

    if not direct_url:
        return [], []

    for ts in expanded_timestamps:
        output_path = screenshot_dir / f"frame_{int(ts * 10):07d}.jpg"
        if output_path.exists():
            captured.append(str(output_path))
            captured_timestamps.append(ts)
            continue

        try:
            subprocess.run(
                [
                    ffmpeg_path,
                    "-ss", str(ts),
                    "-i", direct_url,
                    "-vframes", "1",
                    "-q:v", "2",
                    "-y",
                    str(output_path),
                ],
                capture_output=True,
                timeout=30,
            )

            if output_path.exists():
                captured.append(str(output_path))
                captured_timestamps.append(ts)
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("Screenshot capture failed at %.1fs: %s", ts, exc)
            continue

    return captured, captured_timestamps


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=IngestResponse)
def ingest_video(body: IngestRequest):
    """
    Ingest a YouTube video: extract transcript, metadata, description links,
    and optionally capture screenshots at key visual moments.
    """
    # Validate and extract video ID
    try:
        video_id = _extract_video_id(body.url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL — could not extract video ID")

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    # Fetch metadata via yt-dlp
    metadata = _get_metadata_ytdlp(canonical_url)

    title = metadata.get("title", "Unknown")
    channel = metadata.get("channel", "Unknown")
    duration = metadata.get("duration", 0)
    publish_date = metadata.get("publish_date", "")
    thumbnail_url = metadata.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
    description = metadata.get("description", "")

    # Format publish_date from YYYYMMDD to YYYY-MM-DD if it's a valid date
    if publish_date and len(publish_date) == 8 and publish_date.isdigit():
        try:
            from datetime import datetime as _dt

            _dt.strptime(publish_date, "%Y%m%d")
            publish_date = f"{publish_date[:4]}-{publish_date[4:6]}-{publish_date[6:8]}"
        except ValueError:
            publish_date = ""

    # Fetch transcript
    transcript = _get_transcript(video_id)

    # Extract URLs from description
    extracted_urls = _extract_urls(description)

    # Analyze transcript for screenshot-worthy moments (with duration-based baseline)
    screenshot_suggestions = _analyze_screenshot_moments(transcript, duration)

    # Optionally capture and analyze screenshots
    screenshots: list[str] = []
    analyzed_screenshots: list[ScreenshotCapture] = []
    screenshot_summary = ""

    if body.capture_screenshots and screenshot_suggestions:
        timestamps = [s.timestamp for s in screenshot_suggestions]
        captured_paths, captured_timestamps = _capture_screenshots(
            canonical_url, timestamps, video_id, multi_frame=True,
        )
        screenshots = captured_paths

        # Mark captured suggestions
        captured_set = set(captured_paths)
        for suggestion in screenshot_suggestions:
            output_path = str(
                Path(tempfile.gettempdir())
                / "yt_lab_screenshots"
                / video_id
                / f"frame_{int(suggestion.timestamp * 10):07d}.jpg"
            )
            if output_path in captured_set:
                suggestion.captured = True
                suggestion.filepath = output_path

        # Run AI vision analysis on captured screenshots
        if captured_paths:
            try:
                from server.services.screenshot_analyzer import analyze_screenshots_batch

                # Build reason list matching captured timestamps
                captured_reasons = []
                for ct in captured_timestamps:
                    # Find the closest original suggestion reason
                    closest_reason = "multi-frame capture"
                    best_dist = float("inf")
                    for s in screenshot_suggestions:
                        dist = abs(s.timestamp - ct)
                        if dist < best_dist:
                            best_dist = dist
                            closest_reason = s.reason
                    captured_reasons.append(closest_reason)

                transcript_dicts = [
                    {"text": s.text, "start": s.start, "duration": s.duration}
                    for s in transcript
                ]

                analyzed_screenshots = analyze_screenshots_batch(
                    filepaths=captured_paths,
                    timestamps=captured_timestamps,
                    reasons=captured_reasons,
                    transcript_segments=transcript_dicts,
                )

                # Generate summary from analyzed screenshots
                high_relevance = [
                    s for s in analyzed_screenshots if s.relevance_score >= 7
                ]
                if high_relevance:
                    classifications = set(s.classification for s in high_relevance)
                    ui_apps = set(s.ui_detected for s in high_relevance if s.ui_detected)
                    parts = []
                    if ui_apps:
                        parts.append(f"Apps shown: {', '.join(sorted(ui_apps))}")
                    if classifications:
                        parts.append(f"Content types: {', '.join(sorted(classifications))}")
                    parts.append(
                        f"{len(high_relevance)} of {len(analyzed_screenshots)} screenshots "
                        f"rated high relevance"
                    )
                    screenshot_summary = ". ".join(parts)
            except Exception as exc:
                logger.warning("Screenshot analysis failed: %s", exc)

    return IngestResponse(
        video_id=video_id,
        title=title,
        channel=channel,
        duration=duration,
        publish_date=publish_date,
        thumbnail_url=thumbnail_url,
        description=description,
        transcript=transcript,
        extracted_urls=extracted_urls,
        screenshot_suggestions=screenshot_suggestions,
        screenshots=screenshots,
        analyzed_screenshots=analyzed_screenshots,
        screenshot_summary=screenshot_summary,
    )


@router.get("/health")
async def yt_lab_health():
    """
    Check availability of optional dependencies (yt-dlp, ffmpeg,
    youtube-transcript-api). Returns 503 if critical deps are missing.
    """
    from fastapi.responses import JSONResponse

    has_ytdlp = shutil.which("yt-dlp") is not None
    has_ffmpeg = shutil.which("ffmpeg") is not None

    has_transcript_api = False
    try:
        import youtube_transcript_api  # type: ignore[import-untyped] # noqa: F401

        has_transcript_api = True
    except ImportError:
        pass

    has_api_key = bool(os.getenv("YOUTUBE_API_KEY"))

    body = {
        "yt_dlp": has_ytdlp,
        "ffmpeg": has_ffmpeg,
        "youtube_transcript_api": has_transcript_api,
        "youtube_api_key": has_api_key,
        "status": "ok" if (has_ytdlp and has_transcript_api) else "degraded",
    }

    status_code = 200 if (has_ytdlp and has_transcript_api) else 503
    return JSONResponse(content=body, status_code=status_code)


@router.delete("/screenshots")
def cleanup_screenshots():
    """
    Delete all cached screenshot files to reclaim disk space.
    Returns the number of files and bytes cleaned up.
    """
    screenshot_dir = Path(tempfile.gettempdir()) / "yt_lab_screenshots"
    if not screenshot_dir.exists():
        return {"deleted_files": 0, "freed_bytes": 0}

    total_files = 0
    total_bytes = 0

    for path in screenshot_dir.rglob("*"):
        if path.is_file():
            total_bytes += path.stat().st_size
            path.unlink(missing_ok=True)
            total_files += 1

    # Remove empty directories
    for path in sorted(screenshot_dir.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    try:
        screenshot_dir.rmdir()
    except OSError:
        pass

    return {"deleted_files": total_files, "freed_bytes": total_bytes}
