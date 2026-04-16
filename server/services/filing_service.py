"""
Filing Service — Folder, Tag, and Video Organization CRUD
==========================================================

Business logic for managing folders, tags, and video assignments.
Uses SQLite via SQLAlchemy for persistence.
"""

import logging
import threading
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models.filing import FilingBase, Folder, GamePlan, Tag, Transcript, VideoFolder, VideoTag, Worksheet

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database setup — singleton engine for filing tables
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None
_init_lock = threading.Lock()


def _get_session():
    """Get a SQLAlchemy session, initializing the engine if needed."""
    global _engine, _SessionLocal
    if _SessionLocal is None:
        with _init_lock:
            if _SessionLocal is None:
                db_path = Path.home() / ".autoforge" / "yt_filing.db"
                db_path.parent.mkdir(parents=True, exist_ok=True)
                _engine = create_engine(f"sqlite:///{db_path}", echo=False)
                FilingBase.metadata.create_all(_engine)
                _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal()


# ---------------------------------------------------------------------------
# Folder CRUD
# ---------------------------------------------------------------------------


async def create_folder(name: str, parent_id: int | None = None) -> dict:
    """Create a new folder."""
    if not name or not name.strip():
        raise ValueError("Folder name cannot be empty")
    session = _get_session()
    try:
        folder = Folder(name=name.strip(), parent_id=parent_id)
        session.add(folder)
        session.commit()
        session.refresh(folder)
        return _folder_to_dict(folder)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def list_folders() -> list[dict]:
    """List all folders."""
    session = _get_session()
    try:
        folders = session.query(Folder).order_by(Folder.name).all()
        return [_folder_to_dict(f) for f in folders]
    finally:
        session.close()


async def update_folder(folder_id: int, name: str | None = None, parent_id: int | None = None) -> dict:
    """Update folder name or parent."""
    session = _get_session()
    try:
        folder = session.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise ValueError(f"Folder {folder_id} not found")
        if name is not None:
            folder.name = name.strip()
        if parent_id is not None:
            # Prevent self-parenting
            if parent_id == folder_id:
                raise ValueError("Folder cannot be its own parent")
            folder.parent_id = parent_id if parent_id != 0 else None
        session.commit()
        session.refresh(folder)
        return _folder_to_dict(folder)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def delete_folder(folder_id: int) -> bool:
    """Delete a folder. Reassigns child folders to no parent."""
    session = _get_session()
    try:
        folder = session.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            return False
        # Reassign children to no parent
        session.query(Folder).filter(Folder.parent_id == folder_id).update({"parent_id": None})
        # Remove video-folder assignments
        session.query(VideoFolder).filter(VideoFolder.folder_id == folder_id).delete()
        session.delete(folder)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Tag CRUD
# ---------------------------------------------------------------------------


async def create_tag(name: str) -> dict:
    """Create a new tag."""
    if not name or not name.strip():
        raise ValueError("Tag name cannot be empty")
    session = _get_session()
    try:
        existing = session.query(Tag).filter(Tag.name == name.strip()).first()
        if existing:
            return _tag_to_dict(existing)
        tag = Tag(name=name.strip())
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return _tag_to_dict(tag)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def list_tags() -> list[dict]:
    """List all tags."""
    session = _get_session()
    try:
        tags = session.query(Tag).order_by(Tag.name).all()
        return [_tag_to_dict(t) for t in tags]
    finally:
        session.close()


async def delete_tag(tag_id: int) -> bool:
    """Delete a tag and remove all video associations."""
    session = _get_session()
    try:
        tag = session.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            return False
        session.query(VideoTag).filter(VideoTag.tag_id == tag_id).delete()
        session.delete(tag)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Video organization
# ---------------------------------------------------------------------------


async def assign_video_to_folder(video_id: str, folder_id: int) -> dict:
    """Assign a video to a folder (replaces any existing assignment)."""
    session = _get_session()
    try:
        # Remove existing folder assignment
        session.query(VideoFolder).filter(VideoFolder.video_id == video_id).delete()
        assignment = VideoFolder(video_id=video_id, folder_id=folder_id)
        session.add(assignment)
        session.commit()
        return {"video_id": video_id, "folder_id": folder_id}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def tag_video(video_id: str, tag_id: int) -> dict:
    """Add a tag to a video."""
    session = _get_session()
    try:
        existing = session.query(VideoTag).filter(
            VideoTag.video_id == video_id,
            VideoTag.tag_id == tag_id,
        ).first()
        if existing:
            return {"video_id": video_id, "tag_id": tag_id}
        vt = VideoTag(video_id=video_id, tag_id=tag_id)
        session.add(vt)
        session.commit()
        return {"video_id": video_id, "tag_id": tag_id}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def untag_video(video_id: str, tag_id: int) -> bool:
    """Remove a tag from a video."""
    session = _get_session()
    try:
        count = session.query(VideoTag).filter(
            VideoTag.video_id == video_id,
            VideoTag.tag_id == tag_id,
        ).delete()
        session.commit()
        return count > 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_video_tags(video_id: str) -> list[dict]:
    """Get all tags for a video."""
    session = _get_session()
    try:
        video_tags = session.query(VideoTag).filter(VideoTag.video_id == video_id).all()
        tag_ids = [vt.tag_id for vt in video_tags]
        if not tag_ids:
            return []
        tags = session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        return [_tag_to_dict(t) for t in tags]
    finally:
        session.close()


async def get_video_folder(video_id: str) -> dict | None:
    """Get the folder a video belongs to."""
    session = _get_session()
    try:
        vf = session.query(VideoFolder).filter(VideoFolder.video_id == video_id).first()
        if not vf:
            return None
        folder = session.query(Folder).filter(Folder.id == vf.folder_id).first()
        return _folder_to_dict(folder) if folder else None
    finally:
        session.close()


async def search_videos(query: str, folder_id: int | None = None, tag_ids: list[int] | None = None) -> list[str]:
    """Search video IDs by transcript text, filtered by folder/tags.

    Returns a list of video_id strings matching the criteria.
    """
    session = _get_session()
    try:
        # Start with all transcripts matching the text query
        q = session.query(Transcript.video_id)
        if query and query.strip():
            q = q.filter(Transcript.transcript_text.contains(query.strip()))

        # Filter by folder
        if folder_id is not None:
            folder_video_ids = [
                vf.video_id for vf in
                session.query(VideoFolder.video_id).filter(VideoFolder.folder_id == folder_id).all()
            ]
            q = q.filter(Transcript.video_id.in_(folder_video_ids))

        # Filter by tags (videos must have ALL specified tags)
        if tag_ids:
            for tid in tag_ids:
                tagged = [
                    vt.video_id for vt in
                    session.query(VideoTag.video_id).filter(VideoTag.tag_id == tid).all()
                ]
                q = q.filter(Transcript.video_id.in_(tagged))

        results = q.all()
        return [r[0] for r in results]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _folder_to_dict(folder: Folder) -> dict:
    return {
        "id": folder.id,
        "name": folder.name,
        "parent_id": folder.parent_id,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
    }


def _tag_to_dict(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
    }
