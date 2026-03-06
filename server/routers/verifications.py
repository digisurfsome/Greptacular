"""
Verifications API Router
========================

Historical test/verification results for features. Provides access to
VerificationResult records with filtering by feature ID and pass/fail status.
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
_VerificationResult = None

logger = logging.getLogger(__name__)


def _get_db_classes():
    """Lazy import of database classes."""
    global _create_database, _VerificationResult
    if _create_database is None:
        import sys
        root = Path(__file__).parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from api.database import VerificationResult, create_database
        _create_database = create_database
        _VerificationResult = VerificationResult
    return _create_database, _VerificationResult


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


def _verification_to_dict(v) -> dict:
    """Convert a VerificationResult model to a serializable dict."""
    return {
        "id": v.id,
        "feature_id": v.feature_id,
        "session_id": v.session_id,
        "agent_index": v.agent_index,
        "test_type": v.test_type,
        "passed": v.passed,
        "output": v.output,
        "duration_ms": v.duration_ms,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


router = APIRouter(prefix="/api/projects/{project_name}", tags=["verifications"])


@router.get("/features/{feature_id}/verifications")
async def get_feature_verifications(
    project_name: str,
    feature_id: int,
    limit: int = Query(20, ge=1, le=200),
):
    """Get verification history for a specific feature.

    Returns the most recent verification results ordered by creation time,
    useful for tracking a feature's test history across sessions.
    """
    project_dir = _resolve_project(project_name)
    _, VerificationResult = _get_db_classes()

    with _get_db_session(project_dir) as db:
        results = db.query(VerificationResult).filter(
            VerificationResult.feature_id == feature_id
        ).order_by(VerificationResult.created_at.desc()).limit(limit).all()

        return {
            "verifications": [_verification_to_dict(v) for v in results],
            "feature_id": feature_id,
        }


@router.get("/verifications")
async def get_all_verifications(
    project_name: str,
    passed: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """Get verifications across all features, optionally filtered by pass/fail.

    Without a filter, returns the most recent verifications across all features.
    Use passed=true or passed=false to filter for passing or failing results.
    """
    project_dir = _resolve_project(project_name)
    _, VerificationResult = _get_db_classes()

    with _get_db_session(project_dir) as db:
        query = db.query(VerificationResult).order_by(VerificationResult.created_at.desc())
        if passed is not None:
            query = query.filter(VerificationResult.passed == passed)
        results = query.limit(limit).all()

        return {
            "verifications": [_verification_to_dict(v) for v in results],
        }
