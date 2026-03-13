"""
Token Budget Service — Usage tracking against rolling subscription windows.

Stores per-session token usage in a SQLite ledger at ``~/.autoforge/token_budget.db``.
Provides rolling-window queries (5-hour, weekly, monthly) and calibration support
so the owner can see how much of their Anthropic Max subscription is being used.
"""

import logging
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = Path.home() / ".autoforge" / "token_budget.db"

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS token_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_type TEXT NOT NULL,
                model TEXT NOT NULL,
                input_tokens INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
                cache_read_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens INTEGER NOT NULL DEFAULT 0,
                cost_usd REAL NOT NULL DEFAULT 0.0,
                duration_seconds REAL DEFAULT 0.0,
                project_name TEXT,
                phase TEXT,
                source TEXT DEFAULT 'autoforge'
            );

            CREATE TABLE IF NOT EXISTS calibration_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                window_type TEXT NOT NULL,
                tracked_total INTEGER,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS budget_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_token_log_ts
                ON token_log(timestamp);
        """)
        # Seed defaults if empty
        cur = conn.execute("SELECT COUNT(*) FROM budget_settings")
        if cur.fetchone()[0] == 0:
            defaults = [
                ("daily_work_start", "10:00"),
                ("daily_work_end", "18:00"),
                ("build_window_start", "00:00"),
                ("build_window_end", "08:00"),
                ("5hour_budget_pct", "100"),
                ("weekly_budget_pct", "100"),
                ("monthly_budget_pct", "100"),
            ]
            conn.executemany(
                "INSERT OR IGNORE INTO budget_settings (key, value) VALUES (?, ?)",
                defaults,
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_session(
    session_type: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    cost_usd: float = 0.0,
    duration_seconds: float = 0.0,
    project_name: Optional[str] = None,
    phase: Optional[str] = None,
    source: str = "autoforge",
) -> int:
    """Record a CLI session's token usage. Returns the new row id."""
    total = input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO token_log
               (timestamp, session_type, model, input_tokens, output_tokens,
                cache_creation_tokens, cache_read_tokens, total_tokens,
                cost_usd, duration_seconds, project_name, phase, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (now, session_type, model, input_tokens, output_tokens,
             cache_creation_tokens, cache_read_tokens, total,
             cost_usd, duration_seconds, project_name, phase, source),
        )
        conn.commit()
        row_id = cur.lastrowid
        logger.info(
            "token_budget: logged %s/%s — %d total tokens ($%.4f) [id=%d]",
            session_type, model, total, cost_usd, row_id,
        )
        return row_id
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rolling window queries
# ---------------------------------------------------------------------------

def _sum_tokens_since(since_iso: str) -> dict:
    """Sum token usage since a given ISO timestamp."""
    conn = _get_conn()
    try:
        row = conn.execute(
            """SELECT
                 COALESCE(SUM(input_tokens), 0) as input_tokens,
                 COALESCE(SUM(output_tokens), 0) as output_tokens,
                 COALESCE(SUM(cache_creation_tokens), 0) as cache_creation_tokens,
                 COALESCE(SUM(cache_read_tokens), 0) as cache_read_tokens,
                 COALESCE(SUM(total_tokens), 0) as total_tokens,
                 COALESCE(SUM(cost_usd), 0.0) as cost_usd,
                 COALESCE(SUM(duration_seconds), 0.0) as duration_seconds,
                 COUNT(*) as session_count
               FROM token_log
               WHERE timestamp >= ?""",
            (since_iso,),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_window_status() -> dict:
    """Get current usage for all three rolling windows."""
    now = datetime.now(timezone.utc)

    five_hr_ago = (now - timedelta(hours=5)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    return {
        "five_hour": _sum_tokens_since(five_hr_ago),
        "weekly": _sum_tokens_since(week_ago),
        "monthly": _sum_tokens_since(month_ago),
        "timestamp": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def get_recent_sessions(limit: int = 50) -> list[dict]:
    """Get recent token log entries, newest first."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM token_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def add_calibration(window_type: str, notes: Optional[str] = None) -> int:
    """Record a 'I Hit the Wall' calibration point."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Get tracked total for the relevant window
    if window_type == "5hour":
        since = (now - timedelta(hours=5)).isoformat()
    elif window_type == "weekly":
        since = (now - timedelta(days=7)).isoformat()
    else:
        since = (now - timedelta(days=30)).isoformat()

    sums = _sum_tokens_since(since)
    tracked_total = sums["total_tokens"]

    conn = _get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO calibration_points
               (timestamp, window_type, tracked_total, notes)
               VALUES (?, ?, ?, ?)""",
            (now_iso, window_type, tracked_total, notes),
        )
        conn.commit()
        logger.info(
            "token_budget: calibration point — %s window, tracked=%d tokens",
            window_type, tracked_total,
        )
        return cur.lastrowid
    finally:
        conn.close()


def get_calibration_points(limit: int = 20) -> list[dict]:
    """Get recent calibration points."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM calibration_points ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_settings() -> dict:
    """Get all budget settings as a dict."""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT key, value FROM budget_settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        conn.close()


def update_settings(updates: dict) -> dict:
    """Update budget settings. Returns the full settings dict."""
    conn = _get_conn()
    try:
        for key, value in updates.items():
            conn.execute(
                "INSERT OR REPLACE INTO budget_settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
        conn.commit()
    finally:
        conn.close()
    return get_settings()


# Auto-init on import
init_db()
