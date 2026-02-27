"""
YT Batch Import Router
=======================

Provides batch YouTube video ingestion endpoints for the YT Strategy Lab.
Accepts multiple URLs, fetches previews in parallel, and queues batch
processing through the existing ingestion pipeline.

Phase 2's AI processing pipeline (yt_processing.py) is not yet built.
Processing calls are stubbed — batch-ingest and preview work fully,
batch-process queues jobs but processing is a placeholder until Phase 2.
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
        from .yt_ingestion import _extract_video_id, _get_metadata_ytdlp, _get_transcript

        video_id = _extract_video_id(video.url)
        video.video_id = video_id

        canonical_url = f"https://www.youtube.com/watch?v={video_id}"

        # Run metadata + transcript in thread pool (they use subprocess)
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(None, _get_metadata_ytdlp, canonical_url)
        await loop.run_in_executor(None, _get_transcript, video_id)

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

    # Check if all succeeded
    if all(v.status in ("ingested", "error") for v in batch.videos):
        if any(v.status == "ingested" for v in batch.videos):
            batch.status = "ingesting"  # Ready for processing
        else:
            batch.status = "error"


async def _process_batch(batch_id: str) -> None:
    """Process all ingested videos in a batch through the AI pipeline.

    NOTE: Phase 2 (yt_processing.py) is not yet built. This is a stub
    that marks videos as complete. When Phase 2 is available, this will
    call POST /api/yt-lab/process for each video.
    """
    batch = _batches.get(batch_id)
    if not batch:
        return

    batch.status = "processing"

    for video in batch.videos:
        if video.status != "ingested":
            continue

        video.status = "processing"

        # TODO: Replace with actual Phase 2 processing call:
        #   response = await _call_processing_pipeline(video, batch.model)
        # For now, mark as complete after a brief delay to simulate processing
        await asyncio.sleep(0.1)

        video.status = "complete"
        batch.processed += 1

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
