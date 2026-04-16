"""
Batch Import Service — Hardened Bulk URL Processing
=====================================================

Handles parallel URL processing with SQLite persistence for crash recovery.
Each batch job tracks individual item status so processing can resume.
"""

import logging
import re
from datetime import datetime, timezone

from .filing_service import _get_session
from ..models.batch import BatchItem, BatchJob

logger = logging.getLogger(__name__)


async def create_batch_job(urls: list[str]) -> dict:
    """Create a new batch import job from a list of URLs.

    Validates URLs and creates individual BatchItem records for tracking.
    """
    if not urls:
        raise ValueError("No URLs provided")

    # Deduplicate and validate URLs
    clean_urls = []
    seen = set()
    for url in urls:
        url = url.strip()
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        clean_urls.append(url)

    if not clean_urls:
        raise ValueError("No valid URLs after deduplication")

    session = _get_session()
    try:
        job = BatchJob(
            status="pending",
            total_urls=len(clean_urls),
            processed=0,
            failed=0,
        )
        session.add(job)
        session.flush()  # Get job.id before creating items

        for url in clean_urls:
            video_id = _extract_video_id(url)
            item = BatchItem(
                batch_id=job.id,
                url=url,
                video_id=video_id,
                status="pending",
            )
            session.add(item)

        session.commit()
        session.refresh(job)
        return _job_to_dict(job, session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_batch_job(job_id: int) -> dict | None:
    """Get a batch job with its items."""
    session = _get_session()
    try:
        job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None
        return _job_to_dict(job, session)
    finally:
        session.close()


async def list_batch_jobs(limit: int = 20) -> list[dict]:
    """List batch jobs ordered by creation date (newest first)."""
    session = _get_session()
    try:
        jobs = (
            session.query(BatchJob)
            .order_by(BatchJob.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_job_to_dict(j, session) for j in jobs]
    finally:
        session.close()


async def update_item_status(
    item_id: int,
    status: str,
    error: str | None = None,
) -> dict | None:
    """Update the status of a batch item."""
    session = _get_session()
    try:
        item = session.query(BatchItem).filter(BatchItem.id == item_id).first()
        if not item:
            return None
        item.status = status
        if error:
            item.error = error
        item.updated_at = datetime.now(timezone.utc)
        session.commit()

        # Update parent job counts
        _update_job_counts(item.batch_id, session)
        session.refresh(item)
        return _item_to_dict(item)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_pending_items(job_id: int) -> list[dict]:
    """Get all pending items for a batch job (for resume)."""
    session = _get_session()
    try:
        items = (
            session.query(BatchItem)
            .filter(BatchItem.batch_id == job_id, BatchItem.status == "pending")
            .all()
        )
        return [_item_to_dict(i) for i in items]
    finally:
        session.close()


async def update_job_status(job_id: int, status: str) -> dict | None:
    """Update the overall batch job status."""
    session = _get_session()
    try:
        job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return None
        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(job)
        return _job_to_dict(job, session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _update_job_counts(job_id: int, session) -> None:
    """Recalculate processed/failed counts for a job."""
    job = session.query(BatchJob).filter(BatchJob.id == job_id).first()
    if not job:
        return
    items = session.query(BatchItem).filter(BatchItem.batch_id == job_id).all()
    job.processed = sum(1 for i in items if i.status in ("complete", "failed", "skipped"))
    job.failed = sum(1 for i in items if i.status == "failed")
    # Auto-complete job if all items are done
    if job.processed >= job.total_urls and job.status == "running":
        job.status = "complete"
    session.commit()


def _job_to_dict(job: BatchJob, session) -> dict:
    items = session.query(BatchItem).filter(BatchItem.batch_id == job.id).all()
    return {
        "id": job.id,
        "status": job.status,
        "total_urls": job.total_urls,
        "processed": job.processed,
        "failed": job.failed,
        "items": [_item_to_dict(i) for i in items],
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def _item_to_dict(item: BatchItem) -> dict:
    return {
        "id": item.id,
        "batch_id": item.batch_id,
        "url": item.url,
        "video_id": item.video_id,
        "status": item.status,
        "error": item.error,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }
