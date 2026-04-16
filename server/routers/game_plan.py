"""
Game Plan Router — Generate and Retrieve Strategy Summaries
=============================================================

REST endpoints for generating game plan distillations from transcripts.
Uses Claude SDK (subscription auth) for AI processing.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game-plan", tags=["game-plan"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class GenerateGamePlanRequest(BaseModel):
    video_id: str = Field(..., min_length=1, max_length=64)
    transcript_text: str = Field(..., min_length=1)
    model: str = Field(default="claude-sonnet-4-6", max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate")
async def generate_game_plan(body: GenerateGamePlanRequest):
    from ..services.game_plan_service import generate_game_plan
    try:
        return await generate_game_plan(
            video_id=body.video_id,
            transcript_text=body.transcript_text,
            model=body.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        logger.error("Game plan generation setup error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Error generating game plan")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/{video_id}")
async def get_game_plan(video_id: str):
    from ..services.game_plan_service import get_game_plan
    try:
        result = await get_game_plan(video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Game plan not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting game plan")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/{video_id}/all")
async def list_game_plans(video_id: str):
    from ..services.game_plan_service import list_game_plans
    try:
        return await list_game_plans(video_id)
    except Exception as exc:
        logger.exception("Error listing game plans")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
