"""
Filing Models — Folder, Tag, VideoTag
======================================

SQLAlchemy 2.0 models for organizing YT Lab videos into folders with tags.
Tables are created via Base.metadata.create_all() called from the service layer.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class FilingBase(DeclarativeBase):
    """Declarative base for filing-related tables."""
    pass


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class Folder(FilingBase):
    """A folder for organizing YT Lab videos."""
    __tablename__ = "yt_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey("yt_folders.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, default=_utc_now)


class Tag(FilingBase):
    """A tag that can be applied to videos."""
    __tablename__ = "yt_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=_utc_now)


class VideoTag(FilingBase):
    """Many-to-many relationship between videos and tags."""
    __tablename__ = "yt_video_tags"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("yt_tags.id", ondelete="CASCADE"), nullable=False)


class VideoFolder(FilingBase):
    """Assignment of a video to a folder."""
    __tablename__ = "yt_video_folders"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("yt_folders.id", ondelete="CASCADE"), nullable=False)


class Transcript(FilingBase):
    """Persistent transcript storage for a video."""
    __tablename__ = "yt_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True, unique=True)
    title = Column(String(500), nullable=True)
    source = Column(String(50), nullable=False, default="youtube")  # "youtube" | "paste" | "upload"
    transcript_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class Worksheet(FilingBase):
    """AI-generated structured worksheet for a video."""
    __tablename__ = "yt_worksheets"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True)
    worksheet_json = Column(Text, nullable=False)  # JSON string of worksheet data
    model = Column(String(100), nullable=True, default="claude-sonnet-4-6")
    created_at = Column(DateTime, default=_utc_now)


class GamePlan(FilingBase):
    """AI-generated game plan summary for a video."""
    __tablename__ = "yt_game_plans"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True)
    game_plan_json = Column(Text, nullable=False)  # JSON string of game plan data
    model = Column(String(100), nullable=True, default="claude-sonnet-4-6")
    created_at = Column(DateTime, default=_utc_now)
