"""
Workspace GitHub Service
========================

Lists GitHub repositories via the `gh` CLI and manages local clones
for use as workspace working directories. Unlike workspace_repos.py
(which manages authenticated PAT-based connections for context injection),
this module provides a lightweight "repo picker" backed by the user's
existing `gh` authentication.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPOS_DIR = Path.home() / ".autoforge" / "workspace" / "repos"


def _ensure_repos_dir() -> Path:
    """Create the repos directory if it doesn't already exist."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    return REPOS_DIR


def list_github_repos() -> dict[str, Any]:
    """
    List GitHub repos accessible to the authenticated user via `gh`.

    Returns a dict with:
        - "repos": list of repo dicts (name, nameWithOwner, url, description, updatedAt, isPrivate)
        - "error": optional error string if something went wrong

    Gracefully handles missing `gh` CLI and authentication failures.
    """
    try:
        result = subprocess.run(
            [
                "gh", "repo", "list",
                "--json", "name,nameWithOwner,url,description,updatedAt,isPrivate",
                "--limit", "100",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        logger.warning("gh CLI not found on PATH")
        return {
            "repos": [],
            "error": "gh CLI not found. Install from https://cli.github.com/",
        }
    except subprocess.TimeoutExpired:
        logger.warning("gh repo list timed out after 15 seconds")
        return {
            "repos": [],
            "error": "Request timed out. Check your network connection.",
        }

    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.warning("gh repo list failed: %s", stderr)

        # Detect common authentication issues
        if "auth" in stderr.lower() or "login" in stderr.lower():
            return {
                "repos": [],
                "error": "Not authenticated. Run: gh auth login",
            }

        return {
            "repos": [],
            "error": f"gh CLI error: {stderr[:200]}",
        }

    try:
        repos = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error("Failed to parse gh output as JSON")
        return {
            "repos": [],
            "error": "Failed to parse repository list from gh CLI.",
        }

    return {"repos": repos, "error": None}


def ensure_repo_cloned(repo_url: str, repo_name: str) -> str:
    """
    Ensure a repo is cloned locally, returning the local path.

    Uses a shallow clone (--depth 1) for speed. If the repo is already
    cloned at the expected location, skips cloning and returns the
    existing path immediately.

    Args:
        repo_url: The HTTPS URL of the repository (e.g. https://github.com/owner/repo).
        repo_name: A short name used as the local directory name.

    Returns:
        The absolute path to the local clone as a string.

    Raises:
        ValueError: If cloning fails.
    """
    repos_dir = _ensure_repos_dir()

    # Sanitize the repo name to avoid path traversal
    safe_name = repo_name.replace("/", "__").replace("\\", "__")
    local_path = repos_dir / safe_name

    if local_path.exists() and (local_path / ".git").exists():
        logger.info("Repo already cloned at %s", local_path)
        return str(local_path)

    logger.info("Cloning %s into %s (shallow)", repo_url, local_path)

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(local_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise ValueError("git is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise ValueError("Clone timed out after 120 seconds")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("git clone failed: %s", stderr)
        raise ValueError(f"Clone failed: {stderr[:300]}")

    return str(local_path)
