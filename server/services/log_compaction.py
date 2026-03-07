"""
Log Compaction Service
======================

Auto-cleanup for old action logs and verification results.

Provides three operations:
1. Action log compaction: aggregates old ActionLog rows into ActionLogSummary,
   then deletes the originals.
2. Verification log cleanup: deletes old VerificationResult rows past retention.
3. Debug log rotation: rotates orchestrator_debug.log files.

Retention periods are configurable via ~/.autoforge/config.yaml under a
``retention`` key. Defaults to 30 days for action/verification logs and
7 days for debug logs.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Default retention periods (in days)
DEFAULT_RETENTION = {
    "action_log_days": 30,
    "verification_log_days": 30,
    "debug_log_days": 7,
}


def _load_retention_config() -> dict:
    """Load retention config from ~/.autoforge/config.yaml.

    Merges any ``retention`` section from the org config file with the
    built-in defaults. Missing keys fall back to defaults.

    Returns:
        Dict with action_log_days, verification_log_days, debug_log_days.
    """
    config_path = Path.home() / ".autoforge" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            return {**DEFAULT_RETENTION, **config.get("retention", {})}
        except Exception as e:
            logger.warning("Failed to load retention config: %s", e)
    return dict(DEFAULT_RETENTION)


def compact_action_logs(project_dir: Path, retention_days: int = 30) -> int:
    """Aggregate old action_log rows into action_log_summary, then delete originals.

    For each group of (date, session_id, tool_name), creates or updates a
    summary row with call count, error count, and average duration. Then
    deletes the original detailed rows.

    Args:
        project_dir: Path to the project directory.
        retention_days: Delete action logs older than this many days.

    Returns:
        Number of action_log rows deleted.
    """
    from sqlalchemy import text

    from api.database import ActionLogSummary, create_database

    _, SessionLocal = create_database(project_dir)
    session = SessionLocal()
    deleted = 0
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Aggregate rows that will be deleted
        aggregates = session.execute(text("""
            SELECT date(created_at) as d, session_id, tool_name,
                   COUNT(*) as cnt,
                   SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errs,
                   CAST(AVG(duration_ms) AS INTEGER) as avg_dur
            FROM action_log
            WHERE created_at < :cutoff
            GROUP BY 1, 2, 3
        """), {"cutoff": cutoff.isoformat()})

        for row in aggregates:
            # Upsert into summary table
            existing = session.query(ActionLogSummary).filter(
                ActionLogSummary.date == row.d,
                ActionLogSummary.session_id == row.session_id,
                ActionLogSummary.tool_name == row.tool_name,
            ).first()
            if existing:
                existing.call_count += row.cnt
                existing.error_count += row.errs
                if row.avg_dur and existing.avg_duration_ms:
                    # Running average approximation
                    existing.avg_duration_ms = (existing.avg_duration_ms + row.avg_dur) // 2
            else:
                session.add(ActionLogSummary(
                    date=row.d,
                    session_id=row.session_id,
                    tool_name=row.tool_name,
                    call_count=row.cnt,
                    error_count=row.errs,
                    avg_duration_ms=row.avg_dur,
                ))

        # Delete the compacted rows
        result = session.execute(text(
            "DELETE FROM action_log WHERE created_at < :cutoff"
        ), {"cutoff": cutoff.isoformat()})
        deleted = result.rowcount
        session.commit()

        if deleted > 0:
            logger.info("Compacted %d action_log rows for %s", deleted, project_dir.name)
    except Exception as e:
        session.rollback()
        logger.error("Action log compaction failed for %s: %s", project_dir.name, e)
    finally:
        session.close()
    return deleted


def compact_verification_logs(project_dir: Path, retention_days: int = 30) -> int:
    """Delete old verification_results rows past retention period.

    Args:
        project_dir: Path to the project directory.
        retention_days: Delete verification results older than this many days.

    Returns:
        Number of verification_results rows deleted.
    """
    from sqlalchemy import text

    from api.database import create_database

    _, SessionLocal = create_database(project_dir)
    session = SessionLocal()
    deleted = 0
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        result = session.execute(text(
            "DELETE FROM verification_results WHERE created_at < :cutoff"
        ), {"cutoff": cutoff.isoformat()})
        deleted = result.rowcount
        session.commit()
        if deleted > 0:
            logger.info("Deleted %d old verification_results for %s", deleted, project_dir.name)
    except Exception as e:
        session.rollback()
        logger.error("Verification log compaction failed for %s: %s", project_dir.name, e)
    finally:
        session.close()
    return deleted


def rotate_debug_log(project_dir: Path, max_rotations: int = 3) -> None:
    """Rotate orchestrator_debug.log, keeping N historical copies.

    Shifts existing rotations (log.1 -> log.2, etc.) and moves the
    current log to log.1 if it is non-empty.

    Args:
        project_dir: Path to the project directory.
        max_rotations: Number of rotated copies to keep.
    """
    log_path = project_dir / ".autoforge" / "orchestrator_debug.log"
    if not log_path.exists():
        return

    try:
        # Delete the oldest rotation
        oldest = log_path.with_suffix(f".log.{max_rotations}")
        if oldest.exists():
            oldest.unlink()

        # Shift existing rotations (N-1 -> N, N-2 -> N-1, ...)
        for i in range(max_rotations - 1, 0, -1):
            src = log_path.with_suffix(f".log.{i}")
            dst = log_path.with_suffix(f".log.{i + 1}")
            if src.exists():
                src.rename(dst)

        # Rotate current log to .log.1 if it has content
        if log_path.stat().st_size > 0:
            log_path.rename(log_path.with_suffix(".log.1"))
            logger.info("Rotated debug log for %s", project_dir.name)
    except Exception as e:
        logger.error("Debug log rotation failed for %s: %s", project_dir.name, e)


def run_compaction(project_dir: Path) -> dict:
    """Run all compaction tasks for a single project.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Dict with counts of deleted action_logs and verification_logs.
    """
    config = _load_retention_config()
    results = {
        "action_logs_deleted": compact_action_logs(project_dir, config["action_log_days"]),
        "verification_logs_deleted": compact_verification_logs(project_dir, config["verification_log_days"]),
    }
    rotate_debug_log(project_dir)
    return results


async def run_compaction_all_projects() -> None:
    """Run compaction for all registered projects.

    Called on server startup and daily via APScheduler. Iterates the
    project registry and runs compaction for each project directory.
    """
    import sys
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        from registry import list_registered_projects
        # list_registered_projects returns dict[str, dict] mapping name -> info
        projects = list_registered_projects()
        for project_name, info in projects.items():
            try:
                project_dir = Path(info["path"])
                if project_dir.exists():
                    run_compaction(project_dir)
            except Exception as e:
                logger.error("Compaction failed for %s: %s", project_name, e)
    except Exception as e:
        logger.error("Compaction scan failed: %s", e)
