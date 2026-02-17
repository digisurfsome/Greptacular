"""
Workspace Repository Service
=============================

Manages GitHub repository connections for the workspace.
Repos are cloned to ~/.autoforge/workspace/repos/ and made
accessible to Claude's tools within chat sessions.
"""

import logging
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

REPOS_DIR = Path.home() / ".autoforge" / "workspace" / "repos"


def ensure_repos_dir() -> Path:
    """Create repos directory if it doesn't exist."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    return REPOS_DIR


def validate_repo_url(url: str) -> bool:
    """
    Validate that the URL looks like a GitHub HTTPS repo URL.

    Accepts:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
    """
    pattern = r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(\.git)?$"
    return bool(re.match(pattern, url))


def _build_authenticated_url(repo_url: str, token: str) -> str:
    """Insert token into GitHub HTTPS URL for authenticated clone."""
    return repo_url.replace("https://", f"https://{token}@", 1)


def extract_repo_name(repo_url: str) -> str:
    """Extract 'owner/repo' from a GitHub URL."""
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return parts[-1]


def _local_dir_name(repo_url: str) -> str:
    """Generate a safe directory name from repo URL: owner_repo."""
    name = extract_repo_name(repo_url)
    return name.replace("/", "_")


def _sanitize_error(error_text: str, token: str) -> str:
    """Remove token from error messages to prevent credential leakage."""
    if token:
        error_text = error_text.replace(token, "***")
    return error_text


def _repo_to_dict(repo_obj) -> dict:
    """Convert a WorkspaceConnectedRepo ORM object to a dict."""
    return {
        "id": repo_obj.id,
        "conversation_id": repo_obj.conversation_id,
        "repo_url": repo_obj.repo_url,
        "repo_name": repo_obj.repo_name,
        "local_path": repo_obj.local_path,
        "branch": repo_obj.branch,
        "last_synced_at": (
            repo_obj.last_synced_at.isoformat() if repo_obj.last_synced_at else None
        ),
        "created_at": repo_obj.created_at.isoformat() if repo_obj.created_at else None,
    }


def connect_repo(
    repo_url: str,
    token: str,
    branch: str = "main",
    conversation_id: Optional[int] = None,
) -> dict:
    """
    Connect a GitHub repo: validate, encrypt token, clone, store metadata.

    Raises:
        ValueError: If URL is invalid or clone fails.
    """
    from .workspace_database import WorkspaceConnectedRepo, get_db_session
    from .workspace_token_encryption import store_token

    if not validate_repo_url(repo_url):
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    token_ref = f"repo_{uuid.uuid4().hex[:16]}"
    store_token(token_ref, token)

    ensure_repos_dir()
    local_dir = REPOS_DIR / _local_dir_name(repo_url)

    if local_dir.exists():
        shutil.rmtree(local_dir)

    auth_url = _build_authenticated_url(repo_url, token)
    try:
        result = subprocess.run(
            ["git", "clone", "--branch", branch, "--depth", "1", auth_url, str(local_dir)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            error_msg = _sanitize_error(result.stderr, token)
            raise ValueError(f"Git clone failed: {error_msg.strip()}")
    except subprocess.TimeoutExpired:
        raise ValueError("Git clone timed out after 120 seconds")

    repo_name = extract_repo_name(repo_url)

    session = get_db_session()
    try:
        repo = WorkspaceConnectedRepo(
            conversation_id=conversation_id,
            repo_url=repo_url,
            repo_name=repo_name,
            local_path=str(local_dir),
            access_token_ref=token_ref,
            branch=branch,
            last_synced_at=datetime.now(timezone.utc),
        )
        session.add(repo)
        session.commit()
        session.refresh(repo)
        logger.info("Connected repo %d: %s (branch=%s)", repo.id, repo_name, branch)
        return _repo_to_dict(repo)
    finally:
        session.close()


def disconnect_repo(repo_id: int, delete_local: bool = False) -> bool:
    """Disconnect a repo: remove DB record, delete encrypted token, optionally delete clone."""
    from .workspace_database import WorkspaceConnectedRepo, get_db_session
    from .workspace_token_encryption import delete_token

    session = get_db_session()
    try:
        repo = (
            session.query(WorkspaceConnectedRepo)
            .filter(WorkspaceConnectedRepo.id == repo_id)
            .first()
        )
        if not repo:
            return False

        if repo.access_token_ref:
            delete_token(repo.access_token_ref)

        if delete_local and repo.local_path:
            local_path = Path(repo.local_path)
            if local_path.exists():
                shutil.rmtree(local_path)

        session.delete(repo)
        session.commit()
        logger.info("Disconnected repo %d", repo_id)
        return True
    finally:
        session.close()


def sync_repo(repo_id: int) -> dict:
    """Pull latest changes for a connected repo."""
    from .workspace_database import WorkspaceConnectedRepo, get_db_session
    from .workspace_token_encryption import retrieve_token

    session = get_db_session()
    try:
        repo = (
            session.query(WorkspaceConnectedRepo)
            .filter(WorkspaceConnectedRepo.id == repo_id)
            .first()
        )
        if not repo:
            raise ValueError("Repository not found")

        local_path = Path(repo.local_path) if repo.local_path else None
        if not local_path or not local_path.exists():
            raise ValueError("Local repository directory not found")

        token = None
        if repo.access_token_ref:
            token = retrieve_token(repo.access_token_ref)

        if token:
            auth_url = _build_authenticated_url(repo.repo_url, token)
            result = subprocess.run(
                ["git", "-C", str(local_path), "pull", auth_url, repo.branch or "main"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            error_msg = _sanitize_error(result.stderr, token) if result.stderr else ""
        else:
            result = subprocess.run(
                ["git", "-C", str(local_path), "pull", "origin", repo.branch or "main"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            error_msg = result.stderr or ""

        if result.returncode != 0:
            raise ValueError(f"Git pull failed: {error_msg.strip()}")

        repo.last_synced_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(repo)
        return _repo_to_dict(repo)
    finally:
        session.close()


def get_repo_tree(repo_id: int, max_depth: int = 3) -> Optional[list[dict]]:
    """Get the file tree of a connected repo, excluding .git/ directory."""
    from .workspace_database import WorkspaceConnectedRepo, get_db_session

    session = get_db_session()
    try:
        repo = (
            session.query(WorkspaceConnectedRepo)
            .filter(WorkspaceConnectedRepo.id == repo_id)
            .first()
        )
        if not repo or not repo.local_path:
            return None

        local_path = Path(repo.local_path)
        if not local_path.exists():
            return None

        tree: list[dict] = []
        base_depth = len(local_path.parts)

        for dirpath, dirnames, filenames in os.walk(local_path):
            current_path = Path(dirpath)
            current_depth = len(current_path.parts) - base_depth

            if ".git" in dirnames:
                dirnames.remove(".git")

            if current_depth >= max_depth:
                dirnames.clear()
                continue

            for d in sorted(dirnames):
                rel_path = (current_path / d).relative_to(local_path)
                tree.append({"path": str(rel_path), "type": "dir", "size": 0})

            for f in sorted(filenames):
                full_path = current_path / f
                rel_path = full_path.relative_to(local_path)
                try:
                    size = full_path.stat().st_size
                except OSError:
                    size = 0
                tree.append({"path": str(rel_path), "type": "file", "size": size})

        return tree
    finally:
        session.close()


def get_repo_file(repo_id: int, file_path: str) -> Optional[str]:
    """
    Read a specific file from a connected repo.

    Validates path stays within repo directory (path traversal protection).
    """
    from .workspace_database import WorkspaceConnectedRepo, get_db_session

    session = get_db_session()
    try:
        repo = (
            session.query(WorkspaceConnectedRepo)
            .filter(WorkspaceConnectedRepo.id == repo_id)
            .first()
        )
        if not repo or not repo.local_path:
            return None

        repo_dir = Path(repo.local_path).resolve()
        target = (repo_dir / file_path).resolve()

        # Path traversal protection
        try:
            target.relative_to(repo_dir)
        except ValueError:
            logger.warning("Path traversal attempt blocked: %s", file_path)
            return None

        if not target.is_file():
            return None

        try:
            return target.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return None
    finally:
        session.close()


def list_repos(conversation_id: Optional[int] = None) -> list[dict]:
    """List connected repos, optionally filtered by conversation."""
    from .workspace_database import WorkspaceConnectedRepo, get_db_session

    session = get_db_session()
    try:
        if conversation_id is None:
            repos = (
                session.query(WorkspaceConnectedRepo)
                .order_by(WorkspaceConnectedRepo.created_at.desc())
                .all()
            )
        else:
            repos = (
                session.query(WorkspaceConnectedRepo)
                .filter(
                    (WorkspaceConnectedRepo.conversation_id.is_(None))
                    | (WorkspaceConnectedRepo.conversation_id == conversation_id)
                )
                .order_by(WorkspaceConnectedRepo.created_at.desc())
                .all()
            )
        return [_repo_to_dict(r) for r in repos]
    finally:
        session.close()
