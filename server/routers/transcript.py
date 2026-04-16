"""
Transcript Router — Paste/Save/Retrieve Transcripts
=====================================================

REST endpoints for persistent transcript storage.
Supports YouTube-sourced, manually pasted, and uploaded transcripts.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcript", tags=["transcript"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class SaveTranscriptRequest(BaseModel):
    video_id: str = Field(..., min_length=1, max_length=64)
    transcript_text: str = Field(..., min_length=1)
    title: str | None = None
    source: str = Field(default="youtube", pattern=r"^(youtube|paste|upload)$")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/save")
async def save_transcript(body: SaveTranscriptRequest):
    from ..services.transcript_service import save_transcript
    try:
        return await save_transcript(
            video_id=body.video_id,
            transcript_text=body.transcript_text,
            title=body.title,
            source=body.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Error saving transcript")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/{video_id}")
async def get_transcript(video_id: str):
    from ..services.transcript_service import get_transcript
    try:
        result = await get_transcript(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Transcript not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting transcript")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/")
async def list_transcripts(limit: int = 50, offset: int = 0):
    from ..services.transcript_service import list_transcripts
    try:
        return await list_transcripts(limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Error listing transcripts")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.delete("/{video_id}")
async def delete_transcript(video_id: str):
    from ..services.transcript_service import delete_transcript
    try:
        success = await delete_transcript(video_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transcript not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting transcript")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
