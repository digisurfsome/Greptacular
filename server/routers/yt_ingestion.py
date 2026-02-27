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
    re.compile(r"\b(look at this|as you can see|here'?s the prompt|on screen)\b", re.IGNORECASE),
    re.compile(r"\b(take a look|check this out|you can see here|shown here)\b", re.IGNORECASE),
    re.compile(r"\b(here'?s what|let me show|i'?ll show|showing you)\b", re.IGNORECASE),
    re.compile(r"\b(right here|this is what|the result|the output)\b", re.IGNORECASE),
    re.compile(r"\b(screenshot|screen shot|screen capture)\b", re.IGNORECASE),
    re.compile(r"\b(paste this|copy this|type this in|enter this)\b", re.IGNORECASE),
    re.compile(r"\b(the settings|the config|the interface|the dashboard)\b", re.IGNORECASE),
]


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


def _extract_urls(text: str) -> list[str]:
    """Extract all URLs from a block of text (e.g., video description)."""
    url_pattern = re.compile(
        r"https?://[^\s<>\"'\])]+",
        re.IGNORECASE,
    )
    urls = url_pattern.findall(text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        # Strip trailing punctuation that may have been captured
        u = u.rstrip(".,;:!?)")
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _analyze_screenshot_moments(segments: list[TranscriptSegment]) -> list[ScreenshotSuggestion]:
    """
    Analyze transcript segments for moments where a screenshot would be
    valuable — e.g., when the speaker references something visual on screen.
    """
    suggestions: list[ScreenshotSuggestion] = []
    seen_timestamps: set[int] = set()

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

    return suggestions


def _capture_screenshots(
    url: str,
    timestamps: list[float],
    video_id: str,
) -> list[str]:
    """
    Capture screenshots at specific timestamps using yt-dlp + ffmpeg.

    Returns a list of file paths for successfully captured images.
    Requires both yt-dlp and ffmpeg on PATH.
    """
    ytdlp_path = shutil.which("yt-dlp")
    ffmpeg_path = shutil.which("ffmpeg")

    if not ytdlp_path or not ffmpeg_path:
        logger.warning("yt-dlp or ffmpeg not found — screenshot capture unavailable")
        return []

    if not timestamps:
        return []

    # Create a persistent temp directory for screenshots
    screenshot_dir = Path(tempfile.gettempdir()) / "yt_lab_screenshots" / video_id
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    captured: list[str] = []

    for ts in timestamps[:20]:  # Cap at 20 screenshots to prevent abuse
        output_path = screenshot_dir / f"frame_{int(ts):06d}.jpg"
        if output_path.exists():
            captured.append(str(output_path))
            continue

        try:
            # Use yt-dlp to get the direct video URL, then ffmpeg to extract frame
            get_url_result = subprocess.run(
                [ytdlp_path, "--get-url", "--format", "best[height<=720]", url],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if get_url_result.returncode != 0:
                continue

            direct_url = get_url_result.stdout.strip().split("\n")[0]

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
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("Screenshot capture failed at %.1fs: %s", ts, exc)
            continue

    return captured


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

    # Format publish_date from YYYYMMDD to YYYY-MM-DD if available
    if publish_date and len(publish_date) == 8 and publish_date.isdigit():
        publish_date = f"{publish_date[:4]}-{publish_date[4:6]}-{publish_date[6:8]}"

    # Fetch transcript
    transcript = _get_transcript(video_id)

    # Extract URLs from description
    extracted_urls = _extract_urls(description)

    # Analyze transcript for screenshot-worthy moments
    screenshot_suggestions = _analyze_screenshot_moments(transcript)

    # Optionally capture screenshots
    screenshots: list[str] = []
    if body.capture_screenshots and screenshot_suggestions:
        timestamps = [s.timestamp for s in screenshot_suggestions]
        screenshots = _capture_screenshots(canonical_url, timestamps, video_id)

        # Mark captured suggestions
        captured_set = set(screenshots)
        for suggestion in screenshot_suggestions:
            output_path = str(
                Path(tempfile.gettempdir()) / "yt_lab_screenshots" / video_id / f"frame_{int(suggestion.timestamp):06d}.jpg"
            )
            if output_path in captured_set:
                suggestion.captured = True
                suggestion.filepath = output_path

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
    )


@router.get("/health")
async def yt_lab_health():
    """
    Check availability of optional dependencies (yt-dlp, ffmpeg,
    youtube-transcript-api).
    """
    has_ytdlp = shutil.which("yt-dlp") is not None
    has_ffmpeg = shutil.which("ffmpeg") is not None

    has_transcript_api = False
    try:
        import youtube_transcript_api  # type: ignore[import-untyped] # noqa: F401

        has_transcript_api = True
    except ImportError:
        pass

    has_api_key = bool(os.getenv("YOUTUBE_API_KEY"))

    return {
        "yt_dlp": has_ytdlp,
        "ffmpeg": has_ffmpeg,
        "youtube_transcript_api": has_transcript_api,
        "youtube_api_key": has_api_key,
    }
