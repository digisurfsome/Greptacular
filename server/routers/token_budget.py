"""
Token Budget Router — API for tracking token usage against subscription windows.

Endpoints:
  GET  /api/token-budget/status     — Current window percentages + estimates
  POST /api/token-budget/log        — Record a session's token usage
  POST /api/token-budget/calibrate  — Record a "hit the wall" event
  GET  /api/token-budget/history    — Recent session log
  GET  /api/token-budget/settings   — Get budget settings
  PUT  /api/token-budget/settings   — Update budget settings
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services import token_budget as tb

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/token-budget", tags=["token-budget"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class TokenLogRequest(BaseModel):
    session_type: str  # 'cli_scripter' | 'workspace' | 'agent' | 'other'
    model: str  # 'opus' | 'sonnet' | 'haiku'
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    project_name: Optional[str] = None
    phase: Optional[str] = None
    source: str = "autoforge"


class CalibrateRequest(BaseModel):
    window_type: str = "5hour"  # '5hour' | 'weekly' | 'monthly'
    notes: Optional[str] = None


class SettingsUpdate(BaseModel):
    settings: dict


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def get_status():
    """Current usage for all three rolling windows."""
    return tb.get_window_status()


@router.post("/log")
async def log_usage(request: TokenLogRequest):
    """Record a session's token usage."""
    row_id = tb.log_session(
        session_type=request.session_type,
        model=request.model,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        cache_creation_tokens=request.cache_creation_tokens,
        cache_read_tokens=request.cache_read_tokens,
        cost_usd=request.cost_usd,
        duration_seconds=request.duration_seconds,
        project_name=request.project_name,
        phase=request.phase,
        source=request.source,
    )
    return {"id": row_id, "status": "logged"}


@router.post("/calibrate")
async def calibrate(request: CalibrateRequest):
    """Record a 'I Hit the Wall' calibration point."""
    if request.window_type not in ("5hour", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="window_type must be '5hour', 'weekly', or 'monthly'")
    row_id = tb.add_calibration(
        window_type=request.window_type,
        notes=request.notes,
    )
    return {"id": row_id, "status": "calibrated"}


@router.get("/history")
async def get_history(limit: int = 50):
    """Recent token log entries."""
    sessions = tb.get_recent_sessions(limit=limit)
    calibrations = tb.get_calibration_points(limit=10)
    return {"sessions": sessions, "calibrations": calibrations}


@router.get("/settings")
async def get_settings():
    """Get all budget settings."""
    return tb.get_settings()


@router.put("/settings")
async def update_settings(request: SettingsUpdate):
    """Update budget settings."""
    return tb.update_settings(request.settings)
