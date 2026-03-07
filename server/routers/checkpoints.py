"""
Checkpoints API Router
======================

Git checkpoint and rollback support. Each checkpoint stores the current
git SHA and a JSON snapshot of all feature statuses. Users can preview
changes between a checkpoint and the current state, or roll back to a
previous checkpoint by creating a new branch at that SHA and resetting
feature statuses.
"""

import json
import logging
import subprocess
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..utils.project_helpers import get_project_path as _get_project_path
from ..utils.validation import validate_project_name

# Lazy imports to avoid circular dependencies
_create_database = None
_Checkpoint = None
_Feature = None

logger = logging.getLogger(__name__)


# ==========================================================================
# Pydantic request/response models
# ==========================================================================

class CheckpointCreateRequest(BaseModel):
    """Request body for creating a manual checkpoint."""
    label: str = Field(..., min_length=1, max_length=255)
    session_id: str | None = None


# ==========================================================================
# Database helpers (same pattern as actions.py)
# ==========================================================================

def _get_db_classes():
    """Lazy import of database classes."""
    global _create_database, _Checkpoint, _Feature
    if _create_database is None:
        import sys
        root = Path(__file__).parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from api.database import Checkpoint, Feature, create_database
        _create_database = create_database
        _Checkpoint = Checkpoint
        _Feature = Feature
    return _create_database, _Checkpoint, _Feature


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
# Checkpoint creation helper (reusable by router and MCP tool)
# ==========================================================================

def create_checkpoint_record(
    project_dir: Path,
    label: str,
    session_id: str | None = None,
    db_session=None,
) -> dict:
    """Create a checkpoint with the current git SHA and feature snapshot.

    Args:
        project_dir: Path to the project directory (for git operations).
        label: Human-readable label for the checkpoint.
        session_id: Optional agent session ID.
        db_session: An active SQLAlchemy session. If None, one is created.

    Returns:
        Dictionary representation of the new Checkpoint record.
    """
    _, Checkpoint, Feature = _get_db_classes()

    # Get current git SHA
    git_sha = _get_git_sha(project_dir)

    def _do_create(db):
        features = db.query(Feature).all()
        snapshot = json.dumps([
            {
                "id": f.id,
                "name": f.name,
                "passes": bool(f.passes) if f.passes is not None else False,
                "in_progress": bool(f.in_progress) if f.in_progress is not None else False,
            }
            for f in features
        ])

        checkpoint = Checkpoint(
            session_id=session_id,
            label=label,
            git_sha=git_sha,
            feature_snapshot=snapshot,
        )
        db.add(checkpoint)
        db.commit()
        db.refresh(checkpoint)
        return checkpoint.to_dict()

    if db_session is not None:
        return _do_create(db_session)

    # Caller didn't provide a session — create one from project_dir
    create_database, _, _ = _get_db_classes()
    _, SessionLocal = create_database(project_dir)
    session = SessionLocal()
    try:
        result = _do_create(session)
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _get_git_sha(project_dir: Path) -> str:
    """Get the current HEAD git SHA for a project directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.warning("Failed to get git SHA for %s: %s", project_dir, e)
    return "unknown"


# ==========================================================================
# Router
# ==========================================================================

router = APIRouter(prefix="/api/projects/{project_name}/checkpoints", tags=["checkpoints"])


@router.get("")
async def list_checkpoints(
    project_name: str,
    limit: int = Query(50, ge=1, le=200),
):
    """List checkpoints for a project, newest first."""
    project_dir = _resolve_project(project_name)
    _, Checkpoint, _ = _get_db_classes()

    with _get_db_session(project_dir) as db:
        checkpoints = (
            db.query(Checkpoint)
            .order_by(Checkpoint.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "items": [c.to_dict() for c in checkpoints],
            "total": db.query(Checkpoint).count(),
        }


@router.post("")
async def create_checkpoint(project_name: str, body: CheckpointCreateRequest):
    """Create a manual checkpoint with the current git SHA and feature snapshot."""
    project_dir = _resolve_project(project_name)
    result = create_checkpoint_record(
        project_dir=project_dir,
        label=body.label,
        session_id=body.session_id,
    )
    return result


@router.get("/{checkpoint_id}")
async def get_checkpoint(project_name: str, checkpoint_id: int):
    """Get a single checkpoint with its full feature snapshot."""
    project_dir = _resolve_project(project_name)
    _, Checkpoint, _ = _get_db_classes()

    with _get_db_session(project_dir) as db:
        checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        data = checkpoint.to_dict()
        # Parse the feature snapshot JSON for the response
        if data.get("feature_snapshot"):
            try:
                data["feature_snapshot_parsed"] = json.loads(data["feature_snapshot"])
            except (json.JSONDecodeError, TypeError):
                data["feature_snapshot_parsed"] = []
        return data


@router.post("/{checkpoint_id}/rollback")
async def rollback_checkpoint(
    project_name: str,
    checkpoint_id: int,
    confirm: bool = Query(False, description="Set to true to execute the rollback, false for preview"),
):
    """Preview or execute a rollback to a checkpoint.

    With confirm=false (default), returns a preview of what would change:
    the git SHA diff and feature status differences.

    With confirm=true, creates a new branch at the checkpoint's git SHA
    and resets feature statuses from the snapshot.
    """
    project_dir = _resolve_project(project_name)
    _, Checkpoint, Feature = _get_db_classes()

    with _get_db_session(project_dir) as db:
        checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint_id).first()
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        # Parse the saved feature snapshot
        saved_features = []
        if checkpoint.feature_snapshot:
            try:
                saved_features = json.loads(checkpoint.feature_snapshot)
            except (json.JSONDecodeError, TypeError):
                pass

        # Build a map of saved feature states: id -> {passes, in_progress}
        saved_map = {f["id"]: f for f in saved_features}

        # Get current feature states
        current_features = db.query(Feature).all()
        current_map = {
            f.id: {
                "id": f.id,
                "name": f.name,
                "passes": bool(f.passes) if f.passes is not None else False,
                "in_progress": bool(f.in_progress) if f.in_progress is not None else False,
            }
            for f in current_features
        }

        # Compute differences
        changes = []
        for fid, current in current_map.items():
            saved = saved_map.get(fid)
            if saved is None:
                # Feature exists now but not in snapshot (added after checkpoint)
                changes.append({
                    "feature_id": fid,
                    "name": current["name"],
                    "change": "added_after_checkpoint",
                    "current_passes": current["passes"],
                    "snapshot_passes": None,
                })
            elif current["passes"] != saved.get("passes", False):
                changes.append({
                    "feature_id": fid,
                    "name": current["name"],
                    "change": "status_changed",
                    "current_passes": current["passes"],
                    "snapshot_passes": saved.get("passes", False),
                })

        # Get current git SHA for comparison
        current_sha = _get_git_sha(project_dir)

        if not confirm:
            # Preview mode — just return the diff
            return {
                "preview": True,
                "checkpoint_id": checkpoint.id,
                "checkpoint_label": checkpoint.label,
                "checkpoint_sha": checkpoint.git_sha,
                "current_sha": current_sha,
                "sha_differs": current_sha != checkpoint.git_sha,
                "feature_changes": changes,
                "change_count": len(changes),
            }

        # Execute rollback: create a new branch at the checkpoint SHA
        if checkpoint.git_sha != "unknown" and current_sha != checkpoint.git_sha:
            branch_name = f"rollback-{checkpoint_id}"
            try:
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name, checkpoint.git_sha],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Git checkout failed: {result.stderr.strip()}"
                    )
            except subprocess.TimeoutExpired:
                raise HTTPException(status_code=500, detail="Git checkout timed out")
            except FileNotFoundError:
                raise HTTPException(status_code=500, detail="Git not found on PATH")

        # Reset feature statuses from the snapshot
        reset_count = 0
        for fid, saved in saved_map.items():
            feature = db.query(Feature).filter(Feature.id == fid).first()
            if feature:
                feature.passes = saved.get("passes", False)
                feature.in_progress = saved.get("in_progress", False)
                reset_count += 1
        db.commit()

        return {
            "preview": False,
            "checkpoint_id": checkpoint.id,
            "checkpoint_label": checkpoint.label,
            "branch_created": f"rollback-{checkpoint_id}" if checkpoint.git_sha != "unknown" else None,
            "features_reset": reset_count,
            "feature_changes": changes,
        }
