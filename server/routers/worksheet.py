"""
Worksheet Router — Generate and Retrieve AI Worksheets
========================================================

REST endpoints for generating structured worksheets from transcripts.
Uses Claude SDK (subscription auth) for AI processing.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/worksheet", tags=["worksheet"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class GenerateWorksheetRequest(BaseModel):
    video_id: str = Field(..., min_length=1, max_length=64)
    transcript_text: str = Field(..., min_length=1)
    model: str = Field(default="claude-sonnet-4-6", max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate")
async def generate_worksheet(body: GenerateWorksheetRequest):
    from ..services.worksheet_service import generate_worksheet
    try:
        return await generate_worksheet(
            video_id=body.video_id,
            transcript_text=body.transcript_text,
            model=body.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.error("Worksheet generation setup error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Error generating worksheet")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/{video_id}")
async def get_worksheet(video_id: str):
    from ..services.worksheet_service import get_worksheet
    try:
        result = await get_worksheet(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Worksheet not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting worksheet")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/{video_id}/all")
async def list_worksheets(video_id: str):
    from ..services.worksheet_service import list_worksheets
    try:
        return await list_worksheets(video_id)
    except Exception as exc:
        logger.exception("Error listing worksheets")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
