"""
Batch Import Models
===================

SQLAlchemy 2.0 models for tracking bulk import jobs and their individual items.
Provides crash recovery by persisting state to SQLite.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .filing import FilingBase, _utc_now


class BatchJob(FilingBase):
    """A bulk import job containing multiple video URLs."""
    __tablename__ = "yt_batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | running | complete | failed | paused
    total_urls = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class BatchItem(FilingBase):
    """A single URL within a batch import job."""
    __tablename__ = "yt_batch_items"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("yt_batch_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    video_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | processing | complete | failed | skipped
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
