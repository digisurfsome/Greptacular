"""
GitHub Integration Service
===========================
Creates GitHub repositories and optionally initializes them from boilerplate
template repos using the GitHub API.
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


async def validate_github_token(token: str) -> dict:
    """Validate a GitHub token and return user info."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise ValueError(f"Invalid GitHub token (HTTP {resp.status_code})")
        data = resp.json()
        return {"login": data["login"], "name": data.get("name", ""), "avatar_url": data.get("avatar_url", "")}


async def create_repo_from_template(
    token: str,
    template_owner: str,
    template_repo: str,
    new_repo_name: str,
    private: bool = True,
    description: str = "",
) -> dict:
    """Create a new GitHub repo from a template repo using the GitHub template API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API_BASE}/repos/{template_owner}/{template_repo}/generate",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "name": new_repo_name,
                "private": private,
                "description": description,
            },
            timeout=30.0,
        )
        if resp.status_code == 201:
            data = resp.json()
            return {
                "status": "success",
                "repo_url": data["html_url"],
                "clone_url": data["clone_url"],
                "full_name": data["full_name"],
                "private": data["private"],
            }
        elif resp.status_code == 422:
            error_data = resp.json()
            msg = error_data.get("message", "")
            errors = error_data.get("errors", [])
            if errors:
                msg = errors[0].get("message", msg)
            raise ValueError(f"Could not create repo: {msg}")
        else:
            raise RuntimeError(f"GitHub API error (HTTP {resp.status_code}): {resp.text}")


async def create_empty_repo(
    token: str,
    repo_name: str,
    private: bool = True,
    description: str = "",
) -> dict:
    """Create an empty GitHub repo (for scratch/no boilerplate)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GITHUB_API_BASE}/user/repos",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "name": repo_name,
                "private": private,
                "description": description,
                "auto_init": True,
            },
            timeout=30.0,
        )
        if resp.status_code == 201:
            data = resp.json()
            return {
                "status": "success",
                "repo_url": data["html_url"],
                "clone_url": data["clone_url"],
                "full_name": data["full_name"],
                "private": data["private"],
            }
        elif resp.status_code == 422:
            error_data = resp.json()
            msg = error_data.get("message", "")
            errors = error_data.get("errors", [])
            if errors:
                msg = errors[0].get("message", msg)
            raise ValueError(f"Could not create repo: {msg}")
        else:
            raise RuntimeError(f"GitHub API error (HTTP {resp.status_code}): {resp.text}")


def slugify_repo_name(name: str) -> str:
    """Convert a project name to a valid GitHub repo name."""
    slug = re.sub(r'[^a-zA-Z0-9_-]', '-', name.strip())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug.lower() if slug else "my-app"
