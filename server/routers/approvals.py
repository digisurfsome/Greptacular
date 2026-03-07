"""
Approvals API Router
====================

Human-in-the-loop approval gates for dangerous agent commands.
Agents request approval, the UI displays pending requests, and users
approve or deny. Requests auto-expire after 5 minutes (TTL enforced
at read time).
"""

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..utils.project_helpers import get_project_path as _get_project_path
from ..utils.validation import validate_project_name

# Lazy imports to avoid circular dependencies
_create_database = None
_ApprovalRequest = None

# TTL for pending approval requests (seconds)
APPROVAL_TTL_SECONDS = 300  # 5 minutes

logger = logging.getLogger(__name__)


# ==========================================================================
# Pydantic request/response models
# ==========================================================================

class ApprovalCreateRequest(BaseModel):
    """Request body for creating an approval request."""
    agent_id: str = Field(..., min_length=1, max_length=100)
    command: str = Field(..., min_length=1)
    reason: str | None = None


class ApprovalResolveRequest(BaseModel):
    """Request body for approving or denying a request."""
    status: str = Field(..., pattern=r'^(approved|denied)$')
    resolved_by: str | None = None


# ==========================================================================
# Database helpers (same pattern as actions.py)
# ==========================================================================

def _get_db_classes():
    """Lazy import of database classes."""
    global _create_database, _ApprovalRequest
    if _create_database is None:
        import sys
        root = Path(__file__).parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from api.database import ApprovalRequest, create_database
        _create_database = create_database
        _ApprovalRequest = ApprovalRequest
    return _create_database, _ApprovalRequest


@contextmanager
def _get_db_session(project_dir: Path):
    """Context manager for database sessions."""
    create_database, _ = _get_db_classes()
    _, SessionLocal = create_database(project_dir)
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _resolve_project(project_name: str) -> Path:
    """Validate and resolve a project name to its directory path."""
    project_name = validate_project_name(project_name)
    project_dir = _get_project_path(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found in registry")
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")
    return project_dir


def _expire_stale_requests(db, ApprovalRequest) -> int:
    """Expire any pending requests older than the TTL.

    Returns the number of requests that were expired.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=APPROVAL_TTL_SECONDS)
    expired = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.status == 'pending',
            ApprovalRequest.requested_at < cutoff,
        )
        .all()
    )
    count = 0
    for req in expired:
        req.status = 'expired'
        req.resolved_at = datetime.now(timezone.utc)
        count += 1
    if count > 0:
        db.commit()
    return count


# ==========================================================================
# Router
# ==========================================================================

router = APIRouter(prefix="/api/projects/{project_name}/approvals", tags=["approvals"])


@router.post("")
async def create_approval(project_name: str, body: ApprovalCreateRequest):
    """Create a new approval request from an agent.

    The agent pauses and waits for the user to approve or deny the
    requested command via the UI.
    """
    project_dir = _resolve_project(project_name)
    _, ApprovalRequest = _get_db_classes()

    with _get_db_session(project_dir) as db:
        approval = ApprovalRequest(
            agent_id=body.agent_id,
            project_name=project_name,
            command=body.command,
            reason=body.reason,
            status='pending',
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval.to_dict()


@router.get("")
async def list_approvals(
    project_name: str,
    status: Optional[str] = Query(None, pattern=r'^(pending|approved|denied|expired|all)$'),
    limit: int = Query(50, ge=1, le=200),
):
    """List approval requests for a project, optionally filtered by status.

    Pending requests older than 5 minutes are automatically expired
    before the list is returned.
    """
    project_dir = _resolve_project(project_name)
    _, ApprovalRequest = _get_db_classes()

    with _get_db_session(project_dir) as db:
        # Expire stale pending requests on every read
        expired_count = _expire_stale_requests(db, ApprovalRequest)
        if expired_count > 0:
            logger.debug("Expired %d stale approval requests for %s", expired_count, project_name)

        query = db.query(ApprovalRequest).filter(
            ApprovalRequest.project_name == project_name
        ).order_by(ApprovalRequest.requested_at.desc())

        if status and status != 'all':
            query = query.filter(ApprovalRequest.status == status)

        approvals = query.limit(limit).all()
        return {
            "items": [a.to_dict() for a in approvals],
            "total": query.count(),
        }


@router.put("/{approval_id}")
async def resolve_approval(project_name: str, approval_id: int, body: ApprovalResolveRequest):
    """Approve or deny a pending approval request.

    Only pending requests can be resolved. Expired or already-resolved
    requests return a 409 Conflict.
    """
    project_dir = _resolve_project(project_name)
    _, ApprovalRequest = _get_db_classes()

    with _get_db_session(project_dir) as db:
        # Expire stale requests first so we don't approve an expired one
        _expire_stale_requests(db, ApprovalRequest)

        approval = db.query(ApprovalRequest).filter(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.project_name == project_name,
        ).first()

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if approval.status != 'pending':
            raise HTTPException(
                status_code=409,
                detail=f"Cannot resolve request with status '{approval.status}'"
            )

        approval.status = body.status
        approval.resolved_at = datetime.now(timezone.utc)
        approval.resolved_by = body.resolved_by
        db.commit()
        db.refresh(approval)
        return approval.to_dict()
