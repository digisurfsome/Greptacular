"""
CI Status Router
================

REST endpoints for CI monitoring, auto-merge control, and status polling.
"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.ci_monitor import (
    CIStatus,
    get_all_states,
    get_ci_timeline,
    get_recent_git_commits,
    get_state,
    start_monitoring,
    stop_monitoring,
    veto_merge,
)

router = APIRouter(prefix="/api/ci", tags=["ci"])


# ============================================================================
# Response Models
# ============================================================================

class CIRunResponse(BaseModel):
    run_id: int
    status: str
    conclusion: str | None
    branch: str
    commit_sha: str
    commit_message: str
    url: str
    started_at: str | None
    autofix_attempt: int


class CIEventResponse(BaseModel):
    type: str
    message: str
    timestamp: str


class CIStatusResponse(BaseModel):
    working_directory: str
    owner: str
    repo: str
    branch: str
    status: str
    latest_run: CIRunResponse | None
    veto_deadline: float | None
    veto_remaining: float | None
    pr_number: int | None
    pr_url: str | None
    autofix_attempt: int
    error_message: str | None
    history: list[CIEventResponse]


class StartMonitorRequest(BaseModel):
    working_directory: str
    veto_seconds: int = 30


class VetoResponse(BaseModel):
    success: bool
    message: str


class GitCommitResponse(BaseModel):
    sha: str
    short_sha: str
    message: str
    author: str
    timestamp: str


class CITimelineEvent(BaseModel):
    id: int
    commit_sha: str | None
    event_type: str
    message: str
    timestamp: str
    metadata: dict | None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/monitor/start", response_model=CIStatusResponse)
async def start_ci_monitor(req: StartMonitorRequest):
    """Start monitoring CI for a working directory."""
    wd = req.working_directory
    if not Path(wd).is_dir():
        raise HTTPException(status_code=400, detail=f"Directory not found: {wd}")

    state = start_monitoring(wd, veto_seconds=req.veto_seconds)

    # Give it a moment to do the first poll
    await asyncio.sleep(1)

    return _state_to_response(state)


@router.post("/monitor/stop")
async def stop_ci_monitor(req: StartMonitorRequest):
    """Stop monitoring CI for a working directory."""
    stop_monitoring(req.working_directory)
    return {"success": True}


@router.get("/status")
async def get_ci_status(working_directory: str) -> CIStatusResponse:
    """Get current CI status for a working directory."""
    state = get_state(working_directory)
    if not state:
        # Not yet monitored — start monitoring automatically
        state = start_monitoring(working_directory)
        await asyncio.sleep(1)

    return _state_to_response(state)


@router.post("/veto", response_model=VetoResponse)
async def veto_auto_merge(req: StartMonitorRequest):
    """Cancel the auto-merge during the veto window."""
    success = veto_merge(req.working_directory)
    if success:
        return VetoResponse(success=True, message="Auto-merge cancelled.")
    return VetoResponse(success=False, message="No active merge to veto (window may have expired).")


@router.get("/all")
async def get_all_ci_statuses() -> list[CIStatusResponse]:
    """Get CI status for all monitored directories."""
    states = get_all_states()
    return [_state_to_response(s) for s in states.values()]


@router.get("/commits", response_model=list[GitCommitResponse])
async def get_git_commits(working_directory: str, limit: int = 10):
    """Get recent git commits for a working directory."""
    if not Path(working_directory).is_dir():
        raise HTTPException(status_code=400, detail=f"Directory not found: {working_directory}")
    if limit < 1 or limit > 50:
        limit = 10
    commits = get_recent_git_commits(working_directory, limit=limit)
    return [GitCommitResponse(**c) for c in commits]


@router.get("/timeline", response_model=list[CITimelineEvent])
async def get_ci_timeline_endpoint(
    working_directory: str,
    commit_sha: str | None = None,
    limit: int = 50,
):
    """Get CI event timeline for a working directory. Optionally filter by commit SHA."""
    if not Path(working_directory).is_dir():
        raise HTTPException(status_code=400, detail=f"Directory not found: {working_directory}")
    events = get_ci_timeline(working_directory, commit_sha=commit_sha, limit=limit)
    return [CITimelineEvent(**e) for e in events]


# ============================================================================
# Helpers
# ============================================================================

def _state_to_response(state) -> CIStatusResponse:
    """Convert internal state to API response."""
    now = asyncio.get_event_loop().time()
    veto_remaining = None
    if state.veto_deadline and state.status == CIStatus.PASSED:
        veto_remaining = max(0, state.veto_deadline - now)

    latest_run = None
    if state.latest_run:
        r = state.latest_run
        latest_run = CIRunResponse(
            run_id=r.run_id,
            status=r.status,
            conclusion=r.conclusion,
            branch=r.branch,
            commit_sha=r.commit_sha,
            commit_message=r.commit_message,
            url=r.url,
            started_at=r.started_at,
            autofix_attempt=r.autofix_attempt,
        )

    return CIStatusResponse(
        working_directory=state.working_directory,
        owner=state.owner,
        repo=state.repo,
        branch=state.branch,
        status=state.status.value,
        latest_run=latest_run,
        veto_deadline=state.veto_deadline,
        veto_remaining=veto_remaining,
        pr_number=state.pr_number,
        pr_url=state.pr_url,
        autofix_attempt=state.autofix_attempt,
        error_message=state.error_message,
        history=[CIEventResponse(**e) for e in state.history],
    )
