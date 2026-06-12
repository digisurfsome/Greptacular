"""
Preview Machine Router — drive the scripts/preview_machine/ pipeline from the UI.

Endpoints (prefix /api/preview-machine):
  GET  /status                       — running state + live log tail
  POST /run                          — start one pipeline stage (409 if busy)
  POST /stop                         — terminate the running stage
  GET  /files                        — *.csv files available as stage inputs
  GET  /calibration?target_pct=70    — runlog tail + copywriter calibration math

All business logic (including argv validation) lives in the service.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import preview_machine_service as pm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preview-machine", tags=["preview-machine"])


class RunRequest(BaseModel):
    stage: str = Field(..., description="One of: biz_pull, gsa_filter, site_age, copywriter, sitegen")
    args: list[str] = Field(default_factory=list, description="Validated argv tail for the stage")


@router.get("/status")
async def get_status():
    """Current pipeline state and the last ~500 log lines."""
    return pm.get_status()


@router.post("/run")
async def run_stage(request: RunRequest):
    """Start a single pipeline stage. 409 if a stage is already running."""
    try:
        return pm.run_stage(request.stage, request.args)
    except ValueError as exc:
        # Bad stage name or argument validation failure.
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        # Already running.
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/stop")
async def stop_stage():
    """Terminate the running stage (no-op if nothing is running)."""
    return pm.stop()


@router.get("/files")
async def list_files():
    """CSV files in scripts/preview_machine, newest first."""
    return {"files": pm.list_files()}


@router.get("/calibration")
async def get_calibration(target_pct: int = 70):
    """Recent runlog events + calibration summary (suggested --per-hour)."""
    if target_pct < 1 or target_pct > 100:
        raise HTTPException(status_code=400, detail="target_pct must be between 1 and 100")
    return pm.get_runlog(target_pct=target_pct)
