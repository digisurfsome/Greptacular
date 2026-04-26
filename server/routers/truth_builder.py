"""
Truth Builder Router
====================

API endpoints for the truth builder pipeline. Runs video transcripts
through Claude AI (subscription SDK) to build a cumulative source-of-truth
document about an AI agency business model.

Endpoints:
    POST /api/truth-builder/run      — Start the pipeline (background task)
    GET  /api/truth-builder/status   — Check progress
    GET  /api/truth-builder/result   — Get the truth document content
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..services.truth_builder_service import (
    get_job_state,
    get_truth_document,
    is_running,
    run_truth_builder,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/truth-builder", tags=["truth-builder"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    """Optional request body for the run endpoint."""

    output_dir: Optional[str] = None


class RunResponse(BaseModel):
    """Response from the run endpoint."""

    status: str
    job_id: str


class StatusResponse(BaseModel):
    """Response from the status endpoint."""

    status: str
    job_id: Optional[str] = None
    progress: str = ""
    last_video: str = ""
    error_message: str = ""
    log_tail: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/run", response_model=RunResponse)
async def start_truth_builder(body: Optional[RunRequest] = None):
    """Start the truth builder pipeline as a background task.

    Returns immediately with a job_id. Use /status to track progress.
    """
    if is_running():
        raise HTTPException(
            status_code=409,
            detail="Truth builder is already running. Check /status for progress.",
        )

    try:
        output_dir = body.output_dir if body else None
        job_id = await run_truth_builder(output_dir=output_dir)
    except RuntimeError as exc:
        logger.error("Failed to start truth builder: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return RunResponse(status="started", job_id=job_id)


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Check the current status of the truth builder pipeline."""
    state = get_job_state()
    return StatusResponse(**state)


@router.get("/result", response_class=PlainTextResponse)
async def get_result():
    """Return the truth_document.md content as plain text."""
    content = get_truth_document()
    if not content:
        raise HTTPException(
            status_code=404,
            detail="No truth document found. Run the truth builder first.",
        )
    return PlainTextResponse(content=content)
