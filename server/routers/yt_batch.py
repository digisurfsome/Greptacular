"""
YT Batch Import Router
=======================

Provides batch YouTube video ingestion endpoints for the YT Strategy Lab.
Accepts multiple URLs, fetches previews in parallel, and queues batch
processing through the AI processing pipeline (yt_processor.py).
"""

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yt-lab", tags=["yt-lab"])


# ---------------------------------------------------------------------------
# In-memory batch state (V1 — will migrate to SQLite later)
# ---------------------------------------------------------------------------

_batches: dict[str, "BatchState"] = {}

# Stores ingestion data (transcript, metadata, etc.) needed for processing.
# Keyed by (batch_id, video_index). Separated from BatchVideoState to keep
# the API response clean (transcript data can be very large).
_ingestion_data: dict[tuple[str, int], dict] = {}


class BatchVideoState(BaseModel):
    """Tracks per-video status within a batch."""

    url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    channel: Optional[str] = None
    duration: int = 0
    thumbnail_url: str = ""
    publish_date: str = ""
    context: str = ""
    niche: str = ""
    tags: list[str] = []
    capture_screenshots: bool = False
    priority: int = 0
    status: str = "pending"  # pending | ingesting | ingested | processing | complete | error
    error: Optional[str] = None


class BatchState(BaseModel):
    """Tracks overall batch progress."""

    batch_id: str
    videos: list[BatchVideoState]
    model: str = "claude-sonnet-4-6"
    status: str = "pending"  # pending | ingesting | processing | complete | error
    total: int = 0
    ingested: int = 0
    processed: int = 0


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------


class BatchVideoInput(BaseModel):
    """A single video entry in a batch ingest request."""

    url: str = Field(..., min_length=5, max_length=2048)
    context: str = ""
    niche: str = ""
    tags: list[str] = []
    capture_screenshots: bool = False
    priority: int = 0


class BatchIngestRequest(BaseModel):
    """Request to ingest multiple YouTube URLs."""

    videos: list[BatchVideoInput] = Field(..., min_length=1, max_length=50)
    model: str = "claude-sonnet-4-6"


class BatchIngestResponse(BaseModel):
    """Response after batch ingest is queued."""

    batch_id: str
    total: int
    status: str


class BatchProcessRequest(BaseModel):
    """Request to process all ingested videos in a batch."""

    batch_id: str


class BatchStatusResponse(BaseModel):
    """Current status of a batch operation."""

    batch_id: str
    status: str
    total: int
    ingested: int
    processed: int
    videos: list[BatchVideoState]


# ---------------------------------------------------------------------------
# Background Tasks
# ---------------------------------------------------------------------------


async def _ingest_single_video(batch_id: str, index: int) -> None:
    """Ingest a single video using the existing yt_ingestion endpoint logic."""
    batch = _batches.get(batch_id)
    if not batch:
        return

    video = batch.videos[index]
    video.status = "ingesting"

    try:
        from .yt_ingestion import (
            _analyze_screenshot_moments,
            _extract_urls,
            _extract_video_id,
            _get_metadata_ytdlp,
            _get_transcript,
        )

        video_id = _extract_video_id(video.url)
        video.video_id = video_id

        canonical_url = f"https://www.youtube.com/watch?v={video_id}"

        # Run metadata + transcript in thread pool (they use subprocess / network)
        loop = asyncio.get_running_loop()
        metadata = await loop.run_in_executor(None, _get_metadata_ytdlp, canonical_url)
        transcript_segments = await loop.run_in_executor(None, _get_transcript, video_id)

        video.title = metadata.get("title", "Unknown")
        video.channel = metadata.get("channel", "Unknown")
        video.duration = metadata.get("duration", 0)
        video.thumbnail_url = metadata.get(
            "thumbnail_url",
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        )
        publish_date = metadata.get("publish_date", "")
        if publish_date and len(publish_date) == 8 and publish_date.isdigit():
            publish_date = f"{publish_date[:4]}-{publish_date[4:6]}-{publish_date[6:8]}"
        video.publish_date = publish_date

        # Extract URLs and screenshot moments from transcript
        description = metadata.get("description", "")
        extracted_urls = _extract_urls(description)
        screenshot_suggestions = _analyze_screenshot_moments(transcript_segments, video.duration)

        # Store ingestion data for the processing phase
        _ingestion_data[(batch_id, index)] = {
            "transcript": [
                {"text": s.text, "start": s.start, "duration": s.duration}
                for s in transcript_segments
            ],
            "metadata": {
                "title": video.title,
                "channel": video.channel,
                "duration": video.duration,
                "description": description,
            },
            "extracted_urls": extracted_urls,
            "screenshot_suggestions": [
                {"timestamp": s.timestamp, "reason": s.reason}
                for s in screenshot_suggestions
            ],
        }

        video.status = "ingested"
        batch.ingested += 1

    except Exception as exc:
        logger.warning("Batch ingest failed for %s: %s", video.url, exc)
        video.status = "error"
        video.error = str(exc)


async def _ingest_batch(batch_id: str) -> None:
    """Ingest all videos in a batch sequentially."""
    batch = _batches.get(batch_id)
    if not batch:
        return

    batch.status = "ingesting"

    # Sort by priority (lower = higher priority)
    sorted_indices = sorted(range(len(batch.videos)), key=lambda i: batch.videos[i].priority)

    for idx in sorted_indices:
        await _ingest_single_video(batch_id, idx)

    # Update status based on ingestion results
    if all(v.status in ("ingested", "error") for v in batch.videos):
        if any(v.status == "ingested" for v in batch.videos):
            batch.status = "ingested"  # Ready for processing
        else:
            batch.status = "error"


async def _process_single_video(batch_id: str, index: int, model: str) -> None:
    """Process a single ingested video through the AI pipeline."""
    from ..services.yt_processor import YTProcessor

    batch = _batches.get(batch_id)
    if not batch:
        return

    video = batch.videos[index]
    data = _ingestion_data.get((batch_id, index))

    if not data or not data.get("transcript"):
        logger.warning("No ingestion data for batch %s video %d — skipping", batch_id, index)
        video.status = "error"
        video.error = "No transcript data available for processing"
        return

    processor = YTProcessor(model=model)

    try:
        await processor.process(
            video_id=video.video_id or "",
            transcript=data["transcript"],
            metadata=data["metadata"],
            user_context=video.context,
            extracted_urls=data.get("extracted_urls", []),
            screenshot_suggestions=data.get("screenshot_suggestions", []),
            model=model,
        )

        video.status = "complete"
        batch.processed += 1
    except Exception as exc:
        logger.warning("Batch processing failed for %s: %s", video.url, exc)
        video.status = "error"
        video.error = f"Processing failed: {exc}"

    # Clean up stored ingestion data for this video
    _ingestion_data.pop((batch_id, index), None)


async def _process_batch(batch_id: str) -> None:
    """Process all ingested videos in a batch through the AI pipeline."""
    batch = _batches.get(batch_id)
    if not batch:
        return

    batch.status = "processing"

    for i, video in enumerate(batch.videos):
        if video.status != "ingested":
            continue

        video.status = "processing"
        await _process_single_video(batch_id, i, batch.model)

    batch.status = "complete"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/batch-ingest", response_model=BatchIngestResponse)
async def batch_ingest(body: BatchIngestRequest):
    """
    Accept an array of YouTube URLs with per-video context.
    Queues background ingestion for all videos and returns a batch_id
    for tracking progress.
    """
    batch_id = str(uuid.uuid4())[:12]

    videos = [
        BatchVideoState(
            url=v.url,
            context=v.context,
            niche=v.niche,
            tags=v.tags,
            capture_screenshots=v.capture_screenshots,
            priority=v.priority,
        )
        for v in body.videos
    ]

    batch = BatchState(
        batch_id=batch_id,
        videos=videos,
        model=body.model,
        total=len(videos),
    )
    _batches[batch_id] = batch

    # Start ingestion in background
    asyncio.create_task(_ingest_batch(batch_id))

    return BatchIngestResponse(
        batch_id=batch_id,
        total=len(videos),
        status="ingesting",
    )


@router.post("/batch-process")
async def batch_process(body: BatchProcessRequest):
    """
    Queue all ingested videos in a batch for AI processing.
    Requires batch-ingest to have completed first.
    """
    batch = _batches.get(body.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Guard against duplicate processing calls
    if batch.status in ("processing", "complete"):
        return {"batch_id": body.batch_id, "status": batch.status, "queued": 0}

    ingested_count = sum(1 for v in batch.videos if v.status == "ingested")
    if ingested_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No ingested videos ready for processing. Wait for ingestion to complete.",
        )

    # Start processing in background
    asyncio.create_task(_process_batch(body.batch_id))

    return {"batch_id": body.batch_id, "status": "processing", "queued": ingested_count}


@router.get("/batch-status/{batch_id}", response_model=BatchStatusResponse)
async def batch_status(batch_id: str):
    """Return current progress of a batch operation."""
    batch = _batches.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return BatchStatusResponse(
        batch_id=batch.batch_id,
        status=batch.status,
        total=batch.total,
        ingested=batch.ingested,
        processed=batch.processed,
        videos=batch.videos,
    )
