"""
AutoForge Deploy Agent — runs in background, watches for new commits on main,
auto-pulls and restarts the server. Zero interaction needed.

Usage:
    python deploy_agent.py              # Run in foreground
    pythonw deploy_agent.py             # Run hidden (no window)
    start_deploy_agent.bat              # Double-click to start

Logs to: C:\Users\lober\Greptacular\deploy_agent.log
"""

import subprocess
import time
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# === CONFIG ===
LIVE_DIR = r"C:\Users\lober\Greptacular"
CHECK_INTERVAL = 30  # seconds between checks
LOG_FILE = os.path.join(LIVE_DIR, "deploy_agent.log")
STARTUP_SCRIPT = os.path.join(LIVE_DIR, "start_ui.bat")

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("deploy-agent")


def run(cmd: list[str], cwd: str = LIVE_DIR, timeout: int = 120) -> tuple[int, str]:
    """Run a command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def get_local_head() -> str:
    """Get current local HEAD commit hash."""
    code, out = run(["git", "rev-parse", "HEAD"])
    return out if code == 0 else ""


def get_remote_head() -> str:
    """Fetch and get remote main HEAD commit hash."""
    # Fetch with retry
    for attempt in range(3):
        code, out = run(["git", "fetch", "origin", "main"])
        if code == 0:
            break
        wait = 2 ** (attempt + 1)
        log.warning(f"Fetch failed (attempt {attempt+1}), retrying in {wait}s: {out}")
        time.sleep(wait)
    else:
        return ""

    code, out = run(["git", "rev-parse", "origin/main"])
    return out if code == 0 else ""


def kill_servers():
    """Kill running AutoForge processes."""
    log.info("Stopping servers...")
    # Kill python processes running start_ui or uvicorn (not this script)
    my_pid = os.getpid()
    subprocess.run(
        ["powershell", "-Command",
         f"Get-Process python -ErrorAction SilentlyContinue | "
         f"Where-Object {{$_.Id -ne {my_pid}}} | Stop-Process -Force"],
        capture_output=True
    )
    subprocess.run(
        ["taskkill", "/f", "/im", "node.exe"],
        capture_output=True
    )
    time.sleep(2)


def pull_and_deploy():
    """Pull latest main and restart the server."""
    log.info("=" * 50)
    log.info("New commits detected — deploying...")

    # Pull
    code, out = run(["git", "pull", "origin", "main", "--no-edit"])
    if code != 0:
        log.error(f"Pull failed: {out}")
        return False
    log.info(f"Pull: {out}")

    # Clean UI dist so start_ui.bat rebuilds it
    dist_dir = os.path.join(LIVE_DIR, "ui", "dist")
    if os.path.exists(dist_dir):
        log.info("Cleaning ui/dist for rebuild...")
        import shutil
        shutil.rmtree(dist_dir, ignore_errors=True)

    # Kill existing servers
    kill_servers()

    # Restart
    log.info("Starting AutoForge...")
    subprocess.Popen(
        ["cmd", "/c", "start", "", STARTUP_SCRIPT],
        cwd=LIVE_DIR,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
    )

    log.info("Deploy complete! Server is starting up.")
    log.info("=" * 50)
    return True


def main():
    log.info("=" * 50)
    log.info("AutoForge Deploy Agent started")
    log.info(f"Watching: {LIVE_DIR}")
    log.info(f"Checking every {CHECK_INTERVAL}s")
    log.info("=" * 50)

    if not os.path.isdir(LIVE_DIR):
        log.error(f"Live directory not found: {LIVE_DIR}")
        sys.exit(1)

    last_head = get_local_head()
    log.info(f"Current HEAD: {last_head[:8]}")

    while True:
        try:
            remote_head = get_remote_head()
            if remote_head and remote_head != last_head:
                log.info(f"Local:  {last_head[:8]}")
                log.info(f"Remote: {remote_head[:8]}")
                if pull_and_deploy():
                    last_head = remote_head
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log.info("Deploy agent stopped by user.")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
