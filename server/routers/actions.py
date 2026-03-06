"""
Actions API Router
==================

Structured action history for agent tool calls. Provides paginated access
to ActionLog entries with filtering by session, tool name, and status.
Also serves the commits endpoint for git log parsing.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..utils.project_helpers import get_project_path as _get_project_path
from ..utils.validation import validate_project_name

# Lazy imports to avoid circular dependencies
_create_database = None
_ActionLog = None
_ActionLogSummary = None

logger = logging.getLogger(__name__)


def _get_db_classes():
    """Lazy import of database classes."""
    global _create_database, _ActionLog, _ActionLogSummary
    if _create_database is None:
        import sys
        root = Path(__file__).parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from api.database import ActionLog, ActionLogSummary, create_database
        _create_database = create_database
        _ActionLog = ActionLog
        _ActionLogSummary = ActionLogSummary
    return _create_database, _ActionLog, _ActionLogSummary


@contextmanager
def _get_db_session(project_dir: Path):
    """Context manager for database sessions."""
    create_database, _, _ = _get_db_classes()
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


# ==========================================================================
# Actions Router
# ==========================================================================

router = APIRouter(prefix="/api/projects/{project_name}/actions", tags=["actions"])


@router.get("")
async def get_actions(
    project_name: str,
    session_id: Optional[str] = Query(None),
    tool_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get paginated action log entries with optional filters.

    Supports filtering by session_id, tool_name, and status (success/error).
    Results are ordered by most recent first.
    """
    project_dir = _resolve_project(project_name)
    _, ActionLog, _ = _get_db_classes()

    with _get_db_session(project_dir) as db:
        query = db.query(ActionLog).order_by(ActionLog.created_at.desc())
        if session_id:
            query = query.filter(ActionLog.session_id == session_id)
        if tool_name:
            query = query.filter(ActionLog.tool_name == tool_name)
        if status:
            query = query.filter(ActionLog.status == status)

        total = query.count()
        actions = query.offset(offset).limit(limit).all()

        return {
            "actions": [
                {
                    "id": a.id,
                    "session_id": a.session_id,
                    "agent_index": a.agent_index,
                    "turn_number": a.turn_number,
                    "tool_name": a.tool_name,
                    "tool_input_summary": a.tool_input_summary,
                    "result_summary": a.result_summary,
                    "duration_ms": a.duration_ms,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in actions
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/summary")
async def get_actions_summary(project_name: str):
    """Get action summary: counts by tool name, error rate, avg duration.

    Provides an aggregate view of all tool calls across sessions,
    useful for identifying hot spots and error-prone tools.
    """
    from sqlalchemy import case, func

    project_dir = _resolve_project(project_name)
    _, ActionLog, _ = _get_db_classes()

    with _get_db_session(project_dir) as db:
        results = db.query(
            ActionLog.tool_name,
            func.count().label("call_count"),
            func.sum(case((ActionLog.status == 'error', 1), else_=0)).label("error_count"),
            func.avg(ActionLog.duration_ms).label("avg_duration_ms"),
        ).group_by(ActionLog.tool_name).all()

        total_calls = sum(r.call_count for r in results)
        total_errors = sum(r.error_count for r in results)

        return {
            "tools": [
                {
                    "tool_name": r.tool_name,
                    "call_count": r.call_count,
                    "error_count": r.error_count,
                    "avg_duration_ms": round(r.avg_duration_ms) if r.avg_duration_ms else None,
                }
                for r in results
            ],
            "total_calls": total_calls,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_calls * 100, 1) if total_calls > 0 else 0,
        }


# ==========================================================================
# Commits Router
# ==========================================================================

commits_router = APIRouter(prefix="/api/projects/{project_name}", tags=["commits"])


@commits_router.get("/commits")
async def get_commits(
    project_name: str,
    feature_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Get parsed git log for a project, optionally filtered by feature ID.

    Each commit is parsed against the autoforge commit message format
    ([autoforge] type(scope): description) and annotated with extracted
    feature IDs.
    """
    import sys
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from commit_utils import get_project_commits

    project_dir = _resolve_project(project_name)
    commits = get_project_commits(project_dir, feature_id=feature_id, limit=limit)
    return {"commits": commits}
