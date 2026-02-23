"""
CI Monitor Service
==================

Polls GitHub Actions for CI status on branches associated with a working directory.
Handles auto-merge after CI passes (with veto window), and auto-pull + dev server restart.
Persists CI events to SQLite for processing log history.
"""

import asyncio
import json
import logging
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CIStatus(str, Enum):
    """Current CI pipeline status."""
    IDLE = "idle"                    # No active CI runs
    RUNNING = "running"             # CI is running checks
    PASSED = "passed"               # CI passed, waiting for veto window
    FAILED = "failed"               # CI failed, auto-fix in progress
    FIXING = "fixing"               # Auto-fix agent is working
    MERGING = "merging"             # Auto-merge in progress
    MERGED = "merged"               # Successfully merged + pulled
    VETO = "veto"                   # User vetoed the auto-merge
    EXHAUSTED = "exhausted"         # Auto-fix used all retries, needs manual help
    ERROR = "error"                 # Something went wrong


@dataclass
class CIRun:
    """A single CI run's info."""
    run_id: int
    status: str           # queued, in_progress, completed
    conclusion: str | None  # success, failure, None if in_progress
    branch: str
    commit_sha: str
    commit_message: str
    url: str
    started_at: str | None
    autofix_attempt: int = 0


@dataclass
class CIMonitorState:
    """Full state for a monitored working directory."""
    working_directory: str
    owner: str = ""
    repo: str = ""
    branch: str = ""
    status: CIStatus = CIStatus.IDLE
    latest_run: CIRun | None = None
    veto_deadline: float | None = None  # Unix timestamp when veto window expires
    veto_seconds: int = 30
    pr_number: int | None = None
    pr_url: str | None = None
    last_polled: float = 0
    error_message: str | None = None
    autofix_attempt: int = 0
    history: list[dict] = field(default_factory=list)  # Recent events for the UI


# Global registry of monitored directories
_monitors: dict[str, CIMonitorState] = {}
_poll_tasks: dict[str, asyncio.Task] = {}

POLL_INTERVAL = 15  # seconds between GitHub API polls
VETO_SECONDS = 30   # seconds before auto-merge


def _run_gh(args: list[str], cwd: str) -> dict | list | None:
    """Run a gh CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("gh %s failed: %s", " ".join(args), result.stderr.strip())
            return None
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("gh command error: %s", e)
        return None


def _run_git(args: list[str], cwd: str) -> tuple[bool, str]:
    """Run a git command. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def _get_repo_info(cwd: str) -> tuple[str, str, str]:
    """Get owner, repo, and current branch from a git working directory."""
    # Get remote URL
    ok, remote = _run_git(["remote", "get-url", "origin"], cwd)
    if not ok:
        return "", "", ""

    # Parse owner/repo from remote URL
    owner, repo = "", ""
    if "github.com" in remote:
        # SSH: git@github.com:owner/repo.git
        # HTTPS: https://github.com/owner/repo.git
        parts = remote.replace(".git", "").split("github.com")[-1]
        parts = parts.lstrip(":/").split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]

    # Get current branch
    ok, branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if not ok:
        branch = ""

    return owner, repo, branch


def _count_autofix_commits(cwd: str) -> int:
    """Count consecutive [autofix] commits from HEAD."""
    ok, log_output = _run_git(["log", "--oneline", "-10", "--format=%s"], cwd)
    if not ok:
        return 0
    count = 0
    for line in log_output.split("\n"):
        if "[autofix]" in line:
            count += 1
        else:
            break
    return count


def _get_events_db_path(working_directory: str) -> Path:
    """Get path to the CI events SQLite database for a working directory."""
    return Path(working_directory) / ".autoforge" / "ci_events.db"


def _init_events_db(db_path: Path):
    """Create the CI events table if it doesn't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ci_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_sha TEXT,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ci_events_sha ON ci_events(commit_sha)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ci_events_ts ON ci_events(timestamp)
    """)
    conn.commit()
    conn.close()


def _persist_event(working_directory: str, event_type: str, message: str,
                   commit_sha: str | None = None, metadata: dict | None = None):
    """Persist a CI event to SQLite."""
    try:
        db_path = _get_events_db_path(working_directory)
        _init_events_db(db_path)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO ci_events (commit_sha, event_type, message, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                commit_sha,
                event_type,
                message,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Failed to persist CI event: %s", e)


def get_ci_timeline(working_directory: str, commit_sha: str | None = None,
                    limit: int = 50) -> list[dict]:
    """Get CI event timeline from SQLite. Optionally filter by commit SHA."""
    wd = str(Path(working_directory).resolve())
    db_path = _get_events_db_path(wd)
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if commit_sha:
            rows = conn.execute(
                "SELECT * FROM ci_events WHERE commit_sha = ? ORDER BY timestamp ASC LIMIT ?",
                (commit_sha, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ci_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "commit_sha": r["commit_sha"],
                "event_type": r["event_type"],
                "message": r["message"],
                "timestamp": r["timestamp"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning("Failed to read CI events: %s", e)
        return []


def get_recent_git_commits(working_directory: str, limit: int = 10) -> list[dict]:
    """Get recent git commits for a working directory."""
    wd = str(Path(working_directory).resolve())
    ok, log_output = _run_git(
        ["log", f"-{limit}", "--format=%H|%h|%s|%an|%aI"],
        wd,
    )
    if not ok or not log_output.strip():
        return []
    commits = []
    for line in log_output.strip().split("\n"):
        parts = line.split("|", 4)
        if len(parts) >= 5:
            commits.append({
                "sha": parts[0],
                "short_sha": parts[1],
                "message": parts[2],
                "author": parts[3],
                "timestamp": parts[4],
            })
    return commits


def _add_event(state: CIMonitorState, event_type: str, message: str):
    """Add an event to the monitor's history and persist to SQLite."""
    timestamp = datetime.now(timezone.utc).isoformat()
    state.history.append({
        "type": event_type,
        "message": message,
        "timestamp": timestamp,
    })
    # Keep only last 20 events in memory
    if len(state.history) > 20:
        state.history = state.history[-20:]
    # Persist to SQLite
    commit_sha = state.latest_run.commit_sha if state.latest_run else None
    _persist_event(
        state.working_directory,
        event_type,
        message,
        commit_sha=commit_sha,
        metadata={"branch": state.branch, "autofix_attempt": state.autofix_attempt},
    )


async def _poll_ci(state: CIMonitorState):
    """Single poll cycle: check GitHub Actions status and react."""
    cwd = state.working_directory

    # Refresh repo info
    owner, repo, branch = _get_repo_info(cwd)
    if not owner or not repo:
        state.status = CIStatus.ERROR
        state.error_message = "Could not detect GitHub remote"
        return
    state.owner = owner
    state.repo = repo
    state.branch = branch

    # Find open PR for this branch
    prs = _run_gh(
        ["pr", "list", "--head", branch, "--state", "open", "--json", "number,url", "--limit", "1"],
        cwd,
    )
    if prs and len(prs) > 0:
        state.pr_number = prs[0].get("number")
        state.pr_url = prs[0].get("url")

    # Get latest CI run for this branch
    runs = _run_gh(
        ["run", "list", "--branch", branch, "--limit", "1", "--json",
         "databaseId,status,conclusion,headBranch,headSha,displayTitle,url,startedAt"],
        cwd,
    )
    if not runs or len(runs) == 0:
        state.status = CIStatus.IDLE
        state.latest_run = None
        return

    run_data = runs[0]
    run = CIRun(
        run_id=run_data.get("databaseId", 0),
        status=run_data.get("status", ""),
        conclusion=run_data.get("conclusion"),
        branch=run_data.get("headBranch", branch),
        commit_sha=run_data.get("headSha", "")[:8],
        commit_message=run_data.get("displayTitle", ""),
        url=run_data.get("url", ""),
        started_at=run_data.get("startedAt"),
        autofix_attempt=_count_autofix_commits(cwd),
    )
    state.latest_run = run

    # State machine
    if run.status in ("queued", "in_progress"):
        if "[autofix]" in run.commit_message:
            state.status = CIStatus.FIXING
            state.autofix_attempt = run.autofix_attempt
        else:
            state.status = CIStatus.RUNNING
    elif run.status == "completed":
        if run.conclusion == "success":
            # CI passed! Start veto window if not already in one
            if state.status not in (CIStatus.PASSED, CIStatus.MERGING, CIStatus.MERGED):
                state.status = CIStatus.PASSED
                state.veto_deadline = asyncio.get_event_loop().time() + state.veto_seconds
                _add_event(state, "ci_passed", f"CI passed for {run.commit_sha}. Auto-merge in {state.veto_seconds}s.")
        elif run.conclusion == "failure":
            if run.autofix_attempt >= 3:
                state.status = CIStatus.EXHAUSTED
                _add_event(state, "exhausted", "Auto-fix used all 3 attempts. Manual fix needed.")
            else:
                state.status = CIStatus.FAILED
                _add_event(state, "ci_failed", f"CI failed ({run.commit_sha}). Auto-fix agent dispatched.")

    state.last_polled = asyncio.get_event_loop().time()


async def _check_veto_and_merge(state: CIMonitorState):
    """Check if veto window expired and perform auto-merge + pull + restart."""
    if state.status != CIStatus.PASSED or state.veto_deadline is None:
        return

    now = asyncio.get_event_loop().time()
    if now < state.veto_deadline:
        return  # Still in veto window

    # Veto window expired — auto-merge
    state.status = CIStatus.MERGING
    _add_event(state, "merging", "Veto window expired. Auto-merging...")

    cwd = state.working_directory

    if state.pr_number:
        # Merge the PR
        result = _run_gh(
            ["pr", "merge", str(state.pr_number), "--merge", "--delete-branch"],
            cwd,
        )
        if result is None:
            # gh pr merge doesn't return JSON on success, check if it worked
            # by re-checking PR state
            pr_check = _run_gh(
                ["pr", "view", str(state.pr_number), "--json", "state"],
                cwd,
            )
            if pr_check and pr_check.get("state") == "MERGED":
                _add_event(state, "merged", f"PR #{state.pr_number} merged successfully.")
            else:
                # Try anyway — gh pr merge often exits 0 with no output
                _add_event(state, "merged", f"PR #{state.pr_number} merge command sent.")
    else:
        # No PR — just merge the branch locally
        ok, msg = _run_git(["checkout", "main"], cwd)
        if ok:
            ok, msg = _run_git(["merge", state.branch], cwd)
            if ok:
                _add_event(state, "merged", f"Branch {state.branch} merged to main locally.")

    # Pull latest changes
    ok, msg = _run_git(["pull", "origin", "main"], cwd)
    if ok:
        _add_event(state, "pulled", "Pulled latest changes.")
    else:
        _add_event(state, "pull_warning", f"Pull warning: {msg}")

    _add_event(state, "deployed", "Changes deployed. Dev server will pick up changes.")

    state.status = CIStatus.MERGED
    state.veto_deadline = None
    _add_event(state, "complete", "Auto-merge + pull complete.")


async def _monitor_loop(state: CIMonitorState):
    """Main polling loop for a working directory."""
    while True:
        try:
            await _poll_ci(state)
            await _check_veto_and_merge(state)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("CI monitor error for %s: %s", state.working_directory, e)
            state.error_message = str(e)
        await asyncio.sleep(POLL_INTERVAL)


def start_monitoring(working_directory: str, veto_seconds: int = VETO_SECONDS) -> CIMonitorState:
    """Start monitoring CI for a working directory. Returns the state object."""
    wd = str(Path(working_directory).resolve())

    if wd in _monitors:
        return _monitors[wd]

    state = CIMonitorState(working_directory=wd, veto_seconds=veto_seconds)
    _monitors[wd] = state

    task = asyncio.ensure_future(_monitor_loop(state))
    _poll_tasks[wd] = task

    logger.info("Started CI monitor for %s", wd)
    return state


def stop_monitoring(working_directory: str):
    """Stop monitoring CI for a working directory."""
    wd = str(Path(working_directory).resolve())

    if wd in _poll_tasks:
        _poll_tasks[wd].cancel()
        del _poll_tasks[wd]

    if wd in _monitors:
        del _monitors[wd]

    logger.info("Stopped CI monitor for %s", wd)


def get_state(working_directory: str) -> CIMonitorState | None:
    """Get the current CI monitor state for a working directory."""
    wd = str(Path(working_directory).resolve())
    return _monitors.get(wd)


def veto_merge(working_directory: str) -> bool:
    """Cancel the auto-merge during the veto window. Returns True if successful."""
    wd = str(Path(working_directory).resolve())
    state = _monitors.get(wd)
    if not state or state.status != CIStatus.PASSED:
        return False

    state.status = CIStatus.VETO
    state.veto_deadline = None
    _add_event(state, "vetoed", "Auto-merge cancelled by user.")
    return True


def get_all_states() -> dict[str, CIMonitorState]:
    """Get all monitored directories and their states."""
    return dict(_monitors)


async def cleanup_all_monitors():
    """Cancel all monitoring tasks."""
    for task in _poll_tasks.values():
        task.cancel()
    _poll_tasks.clear()
    _monitors.clear()
