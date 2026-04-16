"""
Filing Router — Folder/Tag CRUD and Video Organization
========================================================

REST endpoints for organizing YT Lab videos into folders with tags.
Supports search with folder and tag filtering.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/filing", tags=["filing"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: int | None = None


class UpdateFolderRequest(BaseModel):
    name: str | None = None
    parent_id: int | None = None


class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class VideoFolderRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    folder_id: int


class VideoTagRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    tag_id: int


class SearchRequest(BaseModel):
    query: str = ""
    folder_id: int | None = None
    tag_ids: list[int] = []


# ---------------------------------------------------------------------------
# Folder Endpoints
# ---------------------------------------------------------------------------


@router.post("/folders")
async def create_folder(body: CreateFolderRequest):
    from ..services.filing_service import create_folder
    try:
        return await create_folder(body.name, body.parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error creating folder")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/folders")
async def list_folders():
    from ..services.filing_service import list_folders
    try:
        return await list_folders()
    except Exception as exc:
        logger.exception("Error listing folders")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.put("/folders/{folder_id}")
async def update_folder(folder_id: int, body: UpdateFolderRequest):
    from ..services.filing_service import update_folder
    try:
        return await update_folder(folder_id, body.name, body.parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error updating folder")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: int):
    from ..services.filing_service import delete_folder
    try:
        success = await delete_folder(folder_id)
        if not success:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting folder")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


# ---------------------------------------------------------------------------
# Tag Endpoints
# ---------------------------------------------------------------------------


@router.post("/tags")
async def create_tag(body: CreateTagRequest):
    from ..services.filing_service import create_tag
    try:
        return await create_tag(body.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error creating tag")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/tags")
async def list_tags():
    from ..services.filing_service import list_tags
    try:
        return await list_tags()
    except Exception as exc:
        logger.exception("Error listing tags")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int):
    from ..services.filing_service import delete_tag
    try:
        success = await delete_tag(tag_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tag not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting tag")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


# ---------------------------------------------------------------------------
# Video Organization Endpoints
# ---------------------------------------------------------------------------


@router.post("/videos/folder")
async def assign_video_folder(body: VideoFolderRequest):
    from ..services.filing_service import assign_video_to_folder
    try:
        return await assign_video_to_folder(body.video_id, body.folder_id)
    except Exception as exc:
        logger.exception("Error assigning video to folder")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.post("/videos/tag")
async def tag_video(body: VideoTagRequest):
    from ..services.filing_service import tag_video
    try:
        return await tag_video(body.video_id, body.tag_id)
    except Exception as exc:
        logger.exception("Error tagging video")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.delete("/videos/{video_id}/tags/{tag_id}")
async def untag_video(video_id: str, tag_id: int):
    from ..services.filing_service import untag_video
    try:
        success = await untag_video(video_id, tag_id)
        return {"ok": success}
    except Exception as exc:
        logger.exception("Error untagging video")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/videos/{video_id}/tags")
async def get_video_tags(video_id: str):
    from ..services.filing_service import get_video_tags
    try:
        return await get_video_tags(video_id)
    except Exception as exc:
        logger.exception("Error getting video tags")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/videos/{video_id}/folder")
async def get_video_folder(video_id: str):
    from ..services.filing_service import get_video_folder
    try:
        result = await get_video_folder(video_id)
        return result or {"folder": None}
    except Exception as exc:
        logger.exception("Error getting video folder")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


# ---------------------------------------------------------------------------
# Batch Import Endpoints
# ---------------------------------------------------------------------------


class BatchCreateRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)


@router.post("/batch")
async def create_batch(body: BatchCreateRequest):
    """Create a new batch import job from a list of URLs."""
    from ..services.batch_import_service import create_batch_job
    try:
        return await create_batch_job(body.urls)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error creating batch job")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/batch")
async def list_batches():
    """List all batch import jobs."""
    from ..services.batch_import_service import list_batch_jobs
    try:
        return await list_batch_jobs()
    except Exception as exc:
        logger.exception("Error listing batch jobs")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/batch/{job_id}")
async def get_batch(job_id: int):
    """Get a batch job by ID."""
    from ..services.batch_import_service import get_batch_job
    try:
        result = await get_batch_job(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Batch job not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting batch job")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.post("/search")
async def search_videos(body: SearchRequest):
    from ..services.filing_service import search_videos
    try:
        video_ids = await search_videos(body.query, body.folder_id, body.tag_ids or None)
        return {"video_ids": video_ids}
    except Exception as exc:
        logger.exception("Error searching videos")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
