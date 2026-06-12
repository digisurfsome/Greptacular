"""
Preview Machine Service — run the scripts/preview_machine/ pipeline stages.

This service drives the standalone Preview Machine pipeline (biz_pull → gsa_filter
→ site_age → copywriter → sitegen) one stage at a time as a subprocess.

SECURITY MODEL (defense in depth):
  - Stage name is checked against a strict whitelist; never used to build a path
    from user input. We map stage -> "<stage>.py" ourselves.
  - The subprocess is ALWAYS launched as an argv list ([sys.executable, ...]) with
    shell=False. User input never touches a shell, so injection is impossible.
  - Every arg is validated: CSV filenames must be real *.csv files that already
    exist in scripts/preview_machine (no path separators, no ".."), and flags are
    checked against a per-stage whitelist with typed values.

There is at most ONE running pipeline process at a time (singleton). Combined
stdout/stderr is captured into an in-memory ring buffer (last ~500 lines).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# server/services/preview_machine_service.py -> repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
PREVIEW_DIR = REPO_ROOT / "scripts" / "preview_machine"
COPY_DIR = PREVIEW_DIR / "copy"
RUNLOG_PATH = COPY_DIR / "runlog.jsonl"

LOG_RING_SIZE = 500

# Stage name -> script filename. The ONLY way a stage maps to a script. User
# input is matched against these keys; it never builds a filename directly.
STAGE_SCRIPTS = {
    "biz_pull": "biz_pull.py",
    "gsa_filter": "gsa_filter.py",
    "site_age": "site_age.py",
    "copywriter": "copywriter.py",
    "sitegen": "sitegen.py",
}

# Flags that take a value (string/int). Anything not here is treated as a bare
# flag and must be in the per-stage bare-flag set.
_VALUE_FLAGS = {
    "--outdir", "--model", "--batch-size", "--per-hour", "--auto-retry",
    "--verdicts", "--limit", "--copydir", "--findcat",
}
_MODEL_CHOICES = {"sonnet", "haiku"}
_INT_FLAGS = {"--batch-size", "--per-hour", "--auto-retry", "--limit"}


class _ArgError(ValueError):
    """Raised when an argument fails validation."""


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------
def _is_safe_csv(name: str) -> bool:
    """A CSV arg must be a bare filename (no separators / '..') for an existing
    *.csv in scripts/preview_machine."""
    if not name or "/" in name or "\\" in name or ".." in name:
        return False
    if not name.lower().endswith(".csv"):
        return False
    return (PREVIEW_DIR / name).is_file()


def _validate_args(stage: str, args: list[str]) -> list[str]:
    """Validate raw args for a stage and return the sanitized argv tail.

    Raises _ArgError on anything not explicitly allowed. The returned list is a
    fresh, value-checked copy — never the caller's list.
    """
    safe: list[str] = []
    i = 0
    n = len(args)

    while i < n:
        tok = args[i]
        if not isinstance(tok, str):
            raise _ArgError("arguments must be strings")

        if tok.startswith("--"):
            if tok not in _VALUE_FLAGS and tok not in {"--offline"}:
                raise _ArgError(f"flag not allowed: {tok}")

            # Per-stage flag whitelist
            if stage == "copywriter":
                allowed = {"--outdir", "--model", "--batch-size", "--per-hour",
                           "--auto-retry", "--verdicts", "--limit"}
            elif stage == "sitegen":
                allowed = {"--offline", "--copydir"}
            elif stage == "biz_pull":
                allowed = {"--findcat"}
            else:  # gsa_filter / site_age — no flags
                allowed = set()
            if tok not in allowed:
                raise _ArgError(f"flag {tok} not allowed for stage {stage}")

            if tok == "--offline":
                safe.append(tok)
                i += 1
                continue

            # Value flags need a following value
            if i + 1 >= n:
                raise _ArgError(f"flag {tok} requires a value")
            val = args[i + 1]
            if not isinstance(val, str):
                raise _ArgError(f"value for {tok} must be a string")

            if tok in _INT_FLAGS:
                if not re.fullmatch(r"\d+", val):
                    raise _ArgError(f"{tok} must be a non-negative integer")
            elif tok == "--model":
                if val not in _MODEL_CHOICES:
                    raise _ArgError("--model must be sonnet or haiku")
            elif tok == "--outdir" or tok == "--copydir":
                # Restrict to a bare directory name (the copy cache) — no traversal.
                if not re.fullmatch(r"[A-Za-z0-9_-]+", val):
                    raise _ArgError(f"{tok} must be a simple directory name")
            elif tok == "--findcat":
                if not re.fullmatch(r"[A-Za-z0-9 ]+", val):
                    raise _ArgError("--findcat must be alphanumeric")
            elif tok == "--verdicts":
                if not re.fullmatch(r"[A-Za-z, ]+", val):
                    raise _ArgError("--verdicts contains illegal characters")
            safe.append(tok)
            safe.append(val)
            i += 2
            continue

        # Positional token — only allowed as a CSV input for stages 2-5.
        if stage in ("gsa_filter", "site_age", "copywriter", "sitegen"):
            if not _is_safe_csv(tok):
                raise _ArgError(f"not a valid CSV file in preview_machine: {tok}")
            safe.append(tok)
            i += 1
            continue

        raise _ArgError(f"unexpected argument: {tok}")

    return safe


# ---------------------------------------------------------------------------
# Pipeline runner (singleton)
# ---------------------------------------------------------------------------
class _PipelineRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None
        self._reader: Optional[threading.Thread] = None
        self._log: deque[str] = deque(maxlen=LOG_RING_SIZE)
        self.stage: Optional[str] = None
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.exit_code: Optional[int] = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, stage: str, args: list[str]) -> None:
        if stage not in STAGE_SCRIPTS:
            raise _ArgError(f"unknown stage: {stage}")
        with self._lock:
            if self.running:
                raise RuntimeError("a pipeline stage is already running")
            safe_args = _validate_args(stage, list(args or []))
            cmd = [sys.executable, STAGE_SCRIPTS[stage], *safe_args]

            self._log.clear()
            self.stage = stage
            self.started_at = time.time()
            self.finished_at = None
            self.exit_code = None
            self._log.append(f"$ python {' '.join(cmd[1:])}")

            # shell=False (argv list) — user input never reaches a shell.
            self._proc = subprocess.Popen(
                cmd,
                cwd=str(PREVIEW_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._reader = threading.Thread(target=self._pump_output, daemon=True)
            self._reader.start()

    def _pump_output(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        try:
            for line in proc.stdout:
                self._log.append(line.rstrip("\n"))
        except Exception as exc:  # pragma: no cover - defensive
            self._log.append(f"[log reader error: {exc}]")
        finally:
            code = proc.wait()
            self.exit_code = code
            self.finished_at = time.time()
            self._log.append(f"[stage exited with code {code}]")

    def stop(self) -> bool:
        with self._lock:
            if not self.running or self._proc is None:
                return False
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            return True

    def status(self) -> dict:
        return {
            "running": self.running,
            "stage": self.stage,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "log": list(self._log),
        }


_runner = _PipelineRunner()


# ---------------------------------------------------------------------------
# Public API used by the router
# ---------------------------------------------------------------------------
def run_stage(stage: str, args: list[str]) -> dict:
    """Start a pipeline stage. Raises ValueError on bad input, RuntimeError if busy."""
    _runner.start(stage, args)
    return _runner.status()


def stop() -> dict:
    stopped = _runner.stop()
    return {"stopped": stopped, **_runner.status()}


def get_status() -> dict:
    return _runner.status()


def list_files() -> list[dict]:
    """All *.csv files in scripts/preview_machine, newest first."""
    files: list[dict] = []
    if not PREVIEW_DIR.is_dir():
        return files
    for p in PREVIEW_DIR.glob("*.csv"):
        if not p.is_file():
            continue
        st = p.stat()
        files.append({"name": p.name, "size": st.st_size, "mtime": st.st_mtime})
    files.sort(key=lambda f: f["mtime"], reverse=True)
    return files


def _parse_ts(ts: str) -> float:
    """Mirror copywriter.py::parse_ts."""
    import calendar
    return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))


def get_runlog(target_pct: int = 70) -> dict:
    """Read copy/runlog.jsonl and compute the same calibration math as
    copywriter.py::calibrate(). Returns recent events + a calibration summary."""
    if not RUNLOG_PATH.exists():
        return {
            "events": [],
            "calibration": {
                "has_data": False,
                "message": "No run log yet — run the copywriter (stage 4) at least "
                           "once to gather timing data.",
            },
        }

    events = []
    for ln in RUNLOG_PATH.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError:
            continue

    total_written = sum(e.get("written", 0) for e in events if e.get("event") == "batch_done")
    gen_secs = sum(e.get("secs", 0) for e in events if e.get("event") == "batch_done")
    limits = [e for e in events if e.get("event") == "rate_limited"]
    starts = [e for e in events if e.get("event") == "run_start"]

    cal: dict = {
        "has_data": bool(total_written and gen_secs),
        "target_pct": target_pct,
        "total_written": total_written,
        "capacity_per_hour": None,
        "limit_hit": False,
        "limit_ts": None,
        "window_hours": None,
        "done_before_limit": None,
        "burn_rate_per_hour": None,
        "suggested_per_hour": None,
        "message": None,
    }

    if not cal["has_data"]:
        cal["message"] = "Not enough data yet — run a batch or two first."
        # Recent events tail (last 50)
        return {"events": events[-50:], "calibration": cal}

    # Pure generation speed (waits excluded) — same formula as calibrate().
    capacity_per_hour = total_written / (gen_secs / 3600)
    cal["capacity_per_hour"] = round(capacity_per_hour, 1)

    if limits and starts:
        first_limit = _parse_ts(limits[0]["ts"])
        run_start = max(
            (_parse_ts(s["ts"]) for s in starts if _parse_ts(s["ts"]) <= first_limit),
            default=None,
        )
        if run_start is not None:
            window_h = (first_limit - run_start) / 3600
            done_before = sum(
                e.get("written", 0) for e in events
                if e.get("event") == "batch_done" and _parse_ts(e["ts"]) <= first_limit
            )
            cal["limit_hit"] = True
            cal["limit_ts"] = limits[0]["ts"]
            cal["window_hours"] = round(window_h, 2)
            cal["done_before_limit"] = done_before
            if window_h > 0 and done_before:
                burn_rate = done_before / window_h
                cal["burn_rate_per_hour"] = round(burn_rate, 1)
                cal["suggested_per_hour"] = int(burn_rate * target_pct / 100)
                cal["message"] = (
                    f"Hit the ceiling after {window_h:.2f}h and {done_before} businesses. "
                    f"At {target_pct}% of that burn rate, run --per-hour "
                    f"{cal['suggested_per_hour']}."
                )
    else:
        # No limit recorded — honest message that the ceiling is unknown.
        cal["suggested_per_hour"] = int(capacity_per_hour * target_pct / 100)
        cal["message"] = (
            "No rate limit recorded yet — you haven't hit the ceiling, so the real "
            f"max is unknown. At {target_pct}% of pure speed that's about "
            f"--per-hour {cal['suggested_per_hour']}, but the subscription ceiling is "
            "usually lower. Run full speed until a limit hits, then calculate again."
        )

    return {"events": events[-50:], "calibration": cal}
