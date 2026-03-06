"""
Commit Message Utilities
========================

Parse, validate, and extract feature IDs from autoforge-standard commit messages.
Format: [autoforge] <type>(<scope>): <description>

Types: feat, fix, test, refactor, chore
Scope: Feature ID (e.g., #3) or descriptive label (e.g., system)
"""

import re
import subprocess
from pathlib import Path

# Commit message regex: matches [autoforge] type(scope): description
COMMIT_PATTERN = re.compile(
    r'^\[autoforge\]\s+(feat|fix|test|refactor|chore)\(([^)]+)\):\s+(.+)$'
)

# Feature ID pattern: matches #N references in commit messages
FEATURE_ID_PATTERN = re.compile(r'#(\d+)')

# Allowed commit types for validation
VALID_COMMIT_TYPES = {"feat", "fix", "test", "refactor", "chore"}


def parse_commit_message(msg: str) -> dict | None:
    """Parse an autoforge-format commit message.

    Args:
        msg: The commit message string to parse.

    Returns:
        Dict with 'type', 'scope', and 'description' keys, or None if
        the message does not match the expected format.
    """
    match = COMMIT_PATTERN.match(msg.strip())
    if not match:
        return None
    return {
        "type": match.group(1),
        "scope": match.group(2),
        "description": match.group(3),
    }


def extract_feature_ids(msg: str) -> list[int]:
    """Extract feature IDs (#N) from a commit message.

    Args:
        msg: The commit message to search for feature references.

    Returns:
        List of integer feature IDs found in the message.
    """
    return [int(m.group(1)) for m in FEATURE_ID_PATTERN.finditer(msg)]


def validate_commit_message(msg: str) -> tuple[bool, str]:
    """Validate a commit message against the autoforge format.

    Args:
        msg: The commit message to validate.

    Returns:
        Tuple of (is_valid, reason_string). Reason is "Valid" on success
        or a descriptive error message on failure.
    """
    parsed = parse_commit_message(msg)
    if parsed is None:
        return False, "Does not match format: [autoforge] type(scope): description"
    if parsed["type"] not in VALID_COMMIT_TYPES:
        return False, f"Invalid type '{parsed['type']}'. Must be one of: {', '.join(sorted(VALID_COMMIT_TYPES))}"
    return True, "Valid"


def get_project_commits(
    project_dir: Path,
    feature_id: int | None = None,
    limit: int = 20,
) -> list[dict]:
    """Get git log for a project, optionally filtered by feature ID.

    Runs ``git log`` in the project directory and parses each commit
    message against the autoforge format. Results include parsed metadata
    and extracted feature IDs for each commit.

    Args:
        project_dir: Path to the project's git repository.
        feature_id: If provided, only return commits referencing this feature.
        limit: Maximum number of commits to return (default 20).

    Returns:
        List of commit dicts with keys: sha, message, parsed, feature_ids.
        Returns empty list on any git error.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={limit}", "--format=%H %s"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            sha, *msg_parts = line.split(" ", 1)
            message = msg_parts[0] if msg_parts else ""
            parsed = parse_commit_message(message)
            feature_ids = extract_feature_ids(message)

            commit = {
                "sha": sha,
                "message": message,
                "parsed": parsed,
                "feature_ids": feature_ids,
            }

            # Filter by feature_id if requested
            if feature_id is not None:
                if feature_id in feature_ids:
                    commits.append(commit)
            else:
                commits.append(commit)

        return commits
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []
