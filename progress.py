"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
Uses direct SQLite access for database queries.
"""

import base64
import json
import os
import sqlite3
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

WEBHOOK_URL = os.environ.get("PROGRESS_N8N_WEBHOOK_URL")
PROGRESS_CACHE_FILE = ".progress_cache"

# Pushover notification settings
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.environ.get("PUSHOVER_API_TOKEN")

# Twilio SMS notification settings
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER = os.environ.get("TWILIO_TO_NUMBER")

# SQLite connection settings for parallel mode safety
SQLITE_TIMEOUT = 30  # seconds to wait for locks


def _get_connection(db_file: Path) -> sqlite3.Connection:
    """Get a SQLite connection with proper timeout settings for parallel mode."""
    return sqlite3.connect(db_file, timeout=SQLITE_TIMEOUT)


def has_features(project_dir: Path) -> bool:
    """
    Check if the project has features in the database.

    This is used to determine if the initializer agent needs to run.
    We check the database directly (not via API) since the API server
    may not be running yet when this check is performed.

    Returns True if:
    - features.db exists AND has at least 1 feature, OR
    - feature_list.json exists (legacy format)

    Returns False if no features exist (initializer needs to run).
    """
    # Check legacy JSON file first
    json_file = project_dir / "feature_list.json"
    if json_file.exists():
        return True

    # Check SQLite database
    from autoforge_paths import get_features_db_path
    db_file = get_features_db_path(project_dir)
    if not db_file.exists():
        return False

    try:
        with closing(_get_connection(db_file)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM features")
            count: int = cursor.fetchone()[0]
            return bool(count > 0)
    except Exception:
        # Database exists but can't be read or has no features table
        return False


def count_passing_tests(project_dir: Path) -> tuple[int, int, int]:
    """
    Count passing, in_progress, and total tests via direct database access.

    Args:
        project_dir: Directory containing the project

    Returns:
        (passing_count, in_progress_count, total_count)
    """
    from autoforge_paths import get_features_db_path
    db_file = get_features_db_path(project_dir)
    if not db_file.exists():
        return 0, 0, 0

    try:
        with closing(_get_connection(db_file)) as conn:
            cursor = conn.cursor()
            # Single aggregate query instead of 3 separate COUNT queries
            # Handle case where in_progress column doesn't exist yet (legacy DBs)
            try:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN passes = 1 THEN 1 ELSE 0 END) as passing,
                        SUM(CASE WHEN in_progress = 1 THEN 1 ELSE 0 END) as in_progress
                    FROM features
                """)
                row = cursor.fetchone()
                total = row[0] or 0
                passing = row[1] or 0
                in_progress = row[2] or 0
            except sqlite3.OperationalError:
                # Fallback for databases without in_progress column
                cursor.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN passes = 1 THEN 1 ELSE 0 END) as passing
                    FROM features
                """)
                row = cursor.fetchone()
                total = row[0] or 0
                passing = row[1] or 0
                in_progress = 0
            return passing, in_progress, total
    except Exception as e:
        print(f"[Database error in count_passing_tests: {e}]")
        return 0, 0, 0


def get_all_passing_features(project_dir: Path) -> list[dict]:
    """
    Get all passing features for webhook notifications.

    Args:
        project_dir: Directory containing the project

    Returns:
        List of dicts with id, category, name for each passing feature
    """
    from autoforge_paths import get_features_db_path
    db_file = get_features_db_path(project_dir)
    if not db_file.exists():
        return []

    try:
        with closing(_get_connection(db_file)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, category, name FROM features WHERE passes = 1 ORDER BY priority ASC"
            )
            features = [
                {"id": row[0], "category": row[1], "name": row[2]}
                for row in cursor.fetchall()
            ]
            return features
    except Exception:
        return []


def send_pushover_notification(title: str, message: str, priority: int = 0) -> None:
    """Send a push notification via Pushover.

    Silently returns if Pushover credentials are not configured.
    Never raises exceptions — prints a warning on failure.

    Args:
        title: Notification title (e.g. "Feature Passed", "BUILD COMPLETE")
        message: Notification body text
        priority: 0 = normal, 1 = high (bypass quiet hours), 2 = emergency (repeats until acknowledged)
    """
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        return

    params: dict[str, str | int] = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "priority": priority,
    }

    # Emergency priority requires retry interval and expiration
    if priority == 2:
        params["retry"] = 30    # Retry every 30 seconds
        params["expire"] = 3600  # Stop retrying after 1 hour

    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(
            "https://api.pushover.net/1/messages.json",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[Pushover notification failed: {e}]")


def send_sms_notification(message: str) -> None:
    """Send an SMS notification via Twilio.

    Silently returns if Twilio credentials are not configured.
    Uses urllib with HTTP Basic Auth — no external dependencies.
    Never raises exceptions — prints a warning on failure.

    Args:
        message: SMS body text (max 1600 chars per Twilio, truncated if needed)
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER or not TWILIO_TO_NUMBER:
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

    params = {
        "To": TWILIO_TO_NUMBER,
        "From": TWILIO_FROM_NUMBER,
        "Body": message[:1600],  # Twilio SMS body limit
    }

    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        # Basic Auth: base64-encode "account_sid:auth_token"
        credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            },
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[Twilio SMS notification failed: {e}]")


def send_critical_notification(title: str, message: str) -> None:
    """Send an urgent notification via Pushover (emergency) and SMS.

    Intended for agent crashes, unrecoverable errors, or situations
    requiring immediate human attention. This function is not called
    from progress tracking directly — it is exported for use by the
    agent crash handler and scheduler.

    Pushover emergency priority (2) causes the notification to repeat
    every 30 seconds until the user acknowledges it in the Pushover app.

    Args:
        title: Alert title (e.g. "Agent Crashed", "Requires Input")
        message: Detailed description of the issue
    """
    send_pushover_notification(title, message, priority=2)
    send_sms_notification(f"[URGENT] {title}: {message}")


def send_progress_webhook(passing: int, total: int, project_dir: Path) -> None:
    """Send webhook and push/SMS notifications when progress increases.

    Fires the existing n8n webhook (if configured) and also sends Pushover
    and Twilio SMS notifications for feature completions and build completion.
    Each notification channel is independent — any combination can be configured.
    """
    from autoforge_paths import get_progress_cache_path
    cache_file = get_progress_cache_path(project_dir)
    previous = 0
    previous_passing_ids = set()

    # Read previous progress and passing feature IDs
    if cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text())
            previous = cache_data.get("count", 0)
            previous_passing_ids = set(cache_data.get("passing_ids", []))
        except Exception:
            previous = 0

    # Only notify if progress increased
    if passing > previous:
        # Find which features are now passing via API
        completed_tests = []
        current_passing_ids = []

        # Detect transition from old cache format (had count but no passing_ids)
        # In this case, we can't reliably identify which specific tests are new
        is_old_cache_format = len(previous_passing_ids) == 0 and previous > 0

        # Get all passing features via direct database access
        all_passing = get_all_passing_features(project_dir)
        for feature in all_passing:
            feature_id = feature.get("id")
            current_passing_ids.append(feature_id)
            # Only identify individual new tests if we have previous IDs to compare
            if not is_old_cache_format and feature_id not in previous_passing_ids:
                # This feature is newly passing
                name = feature.get("name", f"Feature #{feature_id}")
                category = feature.get("category", "")
                if category:
                    completed_tests.append(f"{category} {name}")
                else:
                    completed_tests.append(name)

        project_name = project_dir.name

        # --- Existing n8n webhook ---
        if WEBHOOK_URL:
            payload = {
                "event": "test_progress",
                "passing": passing,
                "total": total,
                "percentage": round((passing / total) * 100, 1) if total > 0 else 0,
                "previous_passing": previous,
                "tests_completed_this_session": passing - previous,
                "completed_tests": completed_tests,
                "project": project_name,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            try:
                req = urllib.request.Request(
                    WEBHOOK_URL,
                    data=json.dumps([payload]).encode("utf-8"),  # n8n expects array
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception as e:
                print(f"[Webhook notification failed: {e}]")

        # --- Pushover and SMS notifications ---
        all_complete = passing == total and total > 0

        if all_complete:
            # All features passing — high-priority notification
            msg = f"AutoForge: ALL {total} features passing! Build complete for {project_name}"
            send_pushover_notification("BUILD COMPLETE", msg, priority=1)
            send_sms_notification(msg)
        elif completed_tests:
            # Individual feature(s) completed — normal-priority notification
            feature_summary = ", ".join(completed_tests)
            msg = f"AutoForge: Feature '{feature_summary}' passed ({passing}/{total}) - {project_name}"
            send_pushover_notification("Feature Passed", msg, priority=0)
            send_sms_notification(msg)

        # Update cache with count and passing IDs
        cache_file.write_text(
            json.dumps({"count": passing, "passing_ids": current_passing_ids})
        )
    else:
        # Update cache even if no change (for initial state)
        if not cache_file.exists():
            all_passing = get_all_passing_features(project_dir)
            current_passing_ids = [f.get("id") for f in all_passing]
            cache_file.write_text(
                json.dumps({"count": passing, "passing_ids": current_passing_ids})
            )


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type = "INITIALIZER" if is_initializer else "CODING AGENT"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """Print a summary of current progress."""
    passing, in_progress, total = count_passing_tests(project_dir)

    if total > 0:
        percentage = (passing / total) * 100
        status_parts = [f"{passing}/{total} tests passing ({percentage:.1f}%)"]
        if in_progress > 0:
            status_parts.append(f"{in_progress} in progress")
        print(f"\nProgress: {', '.join(status_parts)}")
        send_progress_webhook(passing, total, project_dir)
    else:
        print("\nProgress: No features in database yet")
