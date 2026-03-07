"""
Rate Limit Logger — persistent event logging for rate limit tracking.

Logs rate limit hits, cooldown completions, and session completions to
~/.autoforge/rate_limit_log.json. Maintains a rolling window of the last
1000 events and daily aggregated statistics.

This is Phase 1 event logging — synchronous file I/O, no async needed.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Maximum events to retain in the rolling window
MAX_EVENTS = 1000

# Maximum daily stat entries to retain (roughly 6 months)
MAX_DAILY_STATS = 180


def _get_log_path() -> Path:
    """Return the path to the rate limit log file."""
    return Path.home() / ".autoforge" / "rate_limit_log.json"


def _load_log() -> dict[str, Any]:
    """Load the log file safely, returning a clean structure on any failure."""
    log_path = _get_log_path()
    if not log_path.exists():
        return {"events": [], "daily_stats": {}}

    try:
        raw = log_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        # Validate expected structure
        if not isinstance(data, dict):
            logger.warning("Rate limit log is not a dict — resetting")
            return {"events": [], "daily_stats": {}}
        if not isinstance(data.get("events"), list):
            data["events"] = []
        if not isinstance(data.get("daily_stats"), dict):
            data["daily_stats"] = {}
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read rate limit log, starting fresh: %s", e)
        return {"events": [], "daily_stats": {}}


def _save_log(data: dict[str, Any]) -> None:
    """Save the log file safely, creating directories as needed."""
    log_path = _get_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.error("Failed to write rate limit log: %s", e)


def _trim_events(data: dict[str, Any]) -> None:
    """Trim events list to MAX_EVENTS (oldest removed first)."""
    events = data.get("events", [])
    if len(events) > MAX_EVENTS:
        data["events"] = events[-MAX_EVENTS:]


def _trim_daily_stats(data: dict[str, Any]) -> None:
    """Trim daily stats to MAX_DAILY_STATS (oldest removed first)."""
    stats = data.get("daily_stats", {})
    if len(stats) > MAX_DAILY_STATS:
        # Sort keys chronologically and keep the most recent
        sorted_keys = sorted(stats.keys())
        keys_to_remove = sorted_keys[:-MAX_DAILY_STATS]
        for key in keys_to_remove:
            del stats[key]


def _today_key() -> str:
    """Return today's date as a YYYY-MM-DD string in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ensure_daily_stats(data: dict[str, Any], day: str) -> dict[str, Any]:
    """Ensure a daily stats entry exists for the given day, returning it."""
    stats = data.setdefault("daily_stats", {})
    if day not in stats:
        stats[day] = {
            "tokens_input": 0,
            "tokens_output": 0,
            "sessions": 0,
            "rate_limit_hits": 0,
            "total_cooldown_minutes": 0,
        }
    return stats[day]


# ── Public API ────────────────────────────────────────────────────


def log_rate_limit_hit(
    *,
    tokens_used_session: int = 0,
    tokens_used_cumulative: int = 0,
    retry_after_seconds: int = 0,
    session_duration_minutes: float = 0,
    project: str = "",
    model: str = "",
) -> None:
    """Log a rate limit hit event.

    Args:
        tokens_used_session: Tokens used in the current session.
        tokens_used_cumulative: Total tokens used across sessions.
        retry_after_seconds: How long the API told us to wait.
        session_duration_minutes: How long the session ran before hitting the limit.
        project: Project name.
        model: Model identifier (e.g. "claude-opus-4-6").
    """
    data = _load_log()
    now = datetime.now(timezone.utc).isoformat()
    day = _today_key()

    event: dict[str, Any] = {
        "timestamp": now,
        "type": "rate_limit_hit",
        "tokens_used_session": tokens_used_session,
        "tokens_used_cumulative": tokens_used_cumulative,
        "retry_after_seconds": retry_after_seconds,
        "session_duration_minutes": round(session_duration_minutes, 1),
        "project": project,
        "model": model,
    }
    data.setdefault("events", []).append(event)

    # Update daily stats
    day_stats = _ensure_daily_stats(data, day)
    day_stats["rate_limit_hits"] += 1

    _trim_events(data)
    _trim_daily_stats(data)
    _save_log(data)

    logger.info(
        "Rate limit hit logged: project=%s model=%s retry_after=%ds",
        project, model, retry_after_seconds,
    )


def log_rate_limit_cleared(
    *,
    cooldown_actual_seconds: int = 0,
) -> None:
    """Log when a rate limit cooldown ends.

    Args:
        cooldown_actual_seconds: How long the actual cooldown lasted.
    """
    data = _load_log()
    now = datetime.now(timezone.utc).isoformat()
    day = _today_key()

    event: dict[str, Any] = {
        "timestamp": now,
        "type": "rate_limit_cleared",
        "cooldown_actual_seconds": cooldown_actual_seconds,
    }
    data.setdefault("events", []).append(event)

    # Update daily stats — add cooldown minutes
    day_stats = _ensure_daily_stats(data, day)
    day_stats["total_cooldown_minutes"] += round(cooldown_actual_seconds / 60, 1)

    _trim_events(data)
    _trim_daily_stats(data)
    _save_log(data)

    logger.info("Rate limit cleared: cooldown was %ds", cooldown_actual_seconds)


def log_session_complete(
    *,
    tokens_input: int = 0,
    tokens_output: int = 0,
    duration_seconds: float = 0,
    project: str = "",
    model: str = "",
) -> None:
    """Log when an agent session completes (handoff or normal exit).

    Args:
        tokens_input: Input tokens consumed during the session.
        tokens_output: Output tokens generated during the session.
        duration_seconds: Total session duration in seconds.
        project: Project name.
        model: Model identifier.
    """
    data = _load_log()
    now = datetime.now(timezone.utc).isoformat()
    day = _today_key()

    event: dict[str, Any] = {
        "timestamp": now,
        "type": "session_complete",
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "duration_seconds": round(duration_seconds, 1),
        "project": project,
        "model": model,
    }
    data.setdefault("events", []).append(event)

    # Update daily stats
    day_stats = _ensure_daily_stats(data, day)
    day_stats["tokens_input"] += tokens_input
    day_stats["tokens_output"] += tokens_output
    day_stats["sessions"] += 1

    _trim_events(data)
    _trim_daily_stats(data)
    _save_log(data)

    logger.info(
        "Session complete logged: project=%s model=%s tokens_in=%d tokens_out=%d duration=%.0fs",
        project, model, tokens_input, tokens_output, duration_seconds,
    )


def get_recent_events(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent events, newest first.

    Args:
        limit: Maximum number of events to return (default 50).

    Returns:
        List of event dicts, most recent first.
    """
    data = _load_log()
    events = data.get("events", [])
    # Return newest first, capped at limit
    return list(reversed(events[-limit:]))


def get_daily_stats(days: int = 7) -> dict[str, dict[str, Any]]:
    """Return daily aggregated stats for the last N days.

    Args:
        days: Number of days to include (default 7).

    Returns:
        Dict mapping date strings (YYYY-MM-DD) to stat dicts.
        Only includes days that have data.
    """
    data = _load_log()
    all_stats = data.get("daily_stats", {})
    # Sort by date descending, take last N days
    sorted_keys = sorted(all_stats.keys(), reverse=True)[:days]
    return {k: all_stats[k] for k in sorted(sorted_keys)}
