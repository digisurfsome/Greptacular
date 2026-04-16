"""
Transcript Service — Save and Retrieve Persistent Transcripts
==============================================================

Handles transcript persistence so they no longer disappear between sessions.
Supports YouTube-sourced, manually pasted, and uploaded transcripts.
"""

import logging

from .filing_service import _get_session
from ..models.filing import Transcript

logger = logging.getLogger(__name__)


async def save_transcript(
    video_id: str,
    transcript_text: str,
    title: str | None = None,
    source: str = "youtube",
) -> dict:
    """Save or update a transcript for a video."""
    if not video_id or not video_id.strip():
        raise ValueError("video_id cannot be empty")
    if not transcript_text or not transcript_text.strip():
        raise ValueError("transcript_text cannot be empty")
    if source not in ("youtube", "paste", "upload"):
        raise ValueError(f"Invalid source: {source}")

    session = _get_session()
    try:
        existing = session.query(Transcript).filter(Transcript.video_id == video_id).first()
        if existing:
            existing.transcript_text = transcript_text
            existing.title = title or existing.title
            existing.source = source
            session.commit()
            session.refresh(existing)
            return _transcript_to_dict(existing)

        transcript = Transcript(
            video_id=video_id.strip(),
            transcript_text=transcript_text,
            title=title,
            source=source,
        )
        session.add(transcript)
        session.commit()
        session.refresh(transcript)
        return _transcript_to_dict(transcript)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_transcript(video_id: str) -> dict | None:
    """Get a transcript by video ID."""
    session = _get_session()
    try:
        transcript = session.query(Transcript).filter(Transcript.video_id == video_id).first()
        return _transcript_to_dict(transcript) if transcript else None
    finally:
        session.close()


async def list_transcripts(limit: int = 50, offset: int = 0) -> list[dict]:
    """List transcripts ordered by creation date (newest first)."""
    session = _get_session()
    try:
        transcripts = (
            session.query(Transcript)
            .order_by(Transcript.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [_transcript_to_dict(t) for t in transcripts]
    finally:
        session.close()


async def delete_transcript(video_id: str) -> bool:
    """Delete a transcript by video ID."""
    session = _get_session()
    try:
        count = session.query(Transcript).filter(Transcript.video_id == video_id).delete()
        session.commit()
        return count > 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _transcript_to_dict(t: Transcript) -> dict:
    return {
        "id": t.id,
        "video_id": t.video_id,
        "title": t.title,
        "source": t.source,
        "transcript_text": t.transcript_text,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }
