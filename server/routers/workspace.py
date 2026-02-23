"""
Workspace Chat Router
=====================

WebSocket and REST endpoints for the workspace chat agent.
Unlike the assistant (read-only, per-project), the workspace is a global
read/write agent with a 1M-token context window.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkspaceConversationSummary(BaseModel):
    """Summary of a workspace conversation."""
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    pinned: bool = False
    tags: str = ""
    context_mode: str = "1m"
    model: str = "opus"
    effort: str = "high"
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int


class WorkspaceMessageModel(BaseModel):
    """A message within a workspace conversation."""
    id: int
    role: str
    content: str
    token_estimate: int
    timestamp: Optional[str]


class WorkspaceConversationDetail(BaseModel):
    """Full workspace conversation with messages."""
    id: int
    title: Optional[str]
    category: str
    working_directory: Optional[str]
    pinned: bool = False
    tags: str = ""
    context_mode: str = "1m"
    model: str = "opus"
    effort: str = "high"
    created_at: Optional[str]
    updated_at: Optional[str]
    message_count: int
    messages: list[WorkspaceMessageModel]


class ConversationCreateRequest(BaseModel):
    """Request body for creating a new workspace conversation."""
    title: Optional[str] = None
    category: str = "general"
    working_directory: Optional[str] = None
    context_mode: str = "1m"
    model: str = "opus"
    effort: str = "high"


class ConversationUpdateRequest(BaseModel):
    """Request body for updating a workspace conversation."""
    title: Optional[str] = None
    category: Optional[str] = None
    pinned: Optional[bool] = None
    tags: Optional[str] = None
    context_mode: Optional[str] = None
    model: Optional[str] = None
    effort: Optional[str] = None


# ============================================================================
# REST Endpoints - Conversation Management
# ============================================================================

@router.get("/conversations", response_model=list[WorkspaceConversationSummary])
async def list_conversations():
    """List all workspace conversations."""
    from ..services.workspace_database import get_conversations

    conversations = get_conversations()
    return [WorkspaceConversationSummary(**c) for c in conversations]


@router.post("/conversations", response_model=WorkspaceConversationSummary)
async def create_new_conversation(body: ConversationCreateRequest):
    """Create a new workspace conversation."""
    from ..services.workspace_database import create_conversation

    conversation = create_conversation(
        title=body.title,
        category=body.category,
        working_directory=body.working_directory,
        context_mode=body.context_mode,
        model=body.model,
        effort=body.effort,
    )
    return WorkspaceConversationSummary(
        id=int(conversation.id),
        title=str(conversation.title) if conversation.title else None,
        category=str(conversation.category),
        working_directory=str(conversation.working_directory) if conversation.working_directory else None,
        pinned=bool(conversation.pinned) if hasattr(conversation, 'pinned') else False,
        tags="",
        context_mode=str(conversation.context_mode) if conversation.context_mode else "1m",
        model=str(conversation.model) if conversation.model else "opus",
        effort=str(conversation.effort) if conversation.effort else "high",
        created_at=conversation.created_at.isoformat() if conversation.created_at else None,
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        message_count=0,
    )


@router.get("/conversations/{conversation_id}", response_model=WorkspaceConversationDetail)
async def get_conversation_detail(conversation_id: int):
    """Get a specific workspace conversation with all messages."""
    from ..services.workspace_database import get_conversation

    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return WorkspaceConversationDetail(
        id=conversation["id"],
        title=conversation["title"],
        category=conversation["category"],
        working_directory=conversation["working_directory"],
        pinned=conversation.get("pinned", False),
        tags=conversation.get("tags", ""),
        context_mode=conversation.get("context_mode", "1m"),
        model=conversation.get("model", "opus"),
        effort=conversation.get("effort", "high"),
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        message_count=len(conversation["messages"]),
        messages=[WorkspaceMessageModel(**m) for m in conversation["messages"]],
    )


@router.patch("/conversations/{conversation_id}", response_model=WorkspaceConversationSummary)
async def update_conversation(conversation_id: int, body: ConversationUpdateRequest):
    """Update a workspace conversation's title or category."""
    from ..services.workspace_database import update_conversation as db_update_conversation

    updated = db_update_conversation(
        conversation_id,
        title=body.title,
        category=body.category,
        pinned=body.pinned,
        tags=body.tags,
        context_mode=body.context_mode,
        model=body.model,
        effort=body.effort,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return WorkspaceConversationSummary(
        id=updated["id"],
        title=updated["title"],
        category=updated["category"],
        working_directory=updated["working_directory"],
        pinned=updated.get("pinned", False),
        tags=updated.get("tags", ""),
        context_mode=updated.get("context_mode", "1m"),
        model=updated.get("model", "opus"),
        effort=updated.get("effort", "high"),
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
        message_count=updated.get("message_count", 0),
    )


class BulkDeleteRequest(BaseModel):
    """Request body for bulk deleting conversations."""
    conversation_ids: list[int]


@router.post("/conversations/bulk-delete")
async def bulk_delete_conversations_endpoint(body: BulkDeleteRequest):
    """Delete multiple workspace conversations at once."""
    from ..services.workspace_database import delete_conversations_bulk

    if not body.conversation_ids:
        raise HTTPException(status_code=400, detail="No conversation IDs provided")
    if len(body.conversation_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 conversations per bulk delete")

    count = delete_conversations_bulk(body.conversation_ids)
    return {"success": True, "deleted_count": count}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: int):
    """Delete a workspace conversation and all its messages."""
    from ..services.workspace_database import delete_conversation

    success = delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"success": True, "message": "Conversation deleted"}


@router.get("/conversations/{conversation_id}/tokens")
async def get_conversation_tokens(conversation_id: int):
    """Get the estimated token usage for a conversation.

    The context window size depends on the conversation's ``context_mode``:
    ``"200k"`` uses a 200,000-token window; everything else (including the
    default ``"1m"``) uses 1,000,000 tokens.
    """
    from ..services.workspace_database import get_conversation, get_conversation_token_total

    total = get_conversation_token_total(conversation_id)

    # Determine the correct context window from the conversation's context_mode
    conv = get_conversation(conversation_id)
    context_mode = (conv.get("context_mode") if conv else None) or "1m"
    context_window = 200_000 if context_mode == "200k" else 1_000_000

    return {
        "total_tokens": total,
        "context_window": context_window,
        "usage_percent": round(total / context_window * 100, 1) if context_window > 0 else 0,
    }


# ============================================================================
# Summary Endpoints
# ============================================================================

class SummaryResponse(BaseModel):
    """Response model for a conversation summary."""
    id: int
    conversation_id: int
    summary: str
    message_count: int
    token_estimate: int
    created_at: Optional[str]


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: int):
    """Get the latest summary for a conversation."""
    from ..services import workspace_database as db

    summary = db.get_latest_summary(conversation_id)
    if not summary:
        return None
    return SummaryResponse(**summary)


@router.post("/conversations/{conversation_id}/summarize", response_model=SummaryResponse)
async def force_regenerate_summary(conversation_id: int):
    """Force regenerate the summary for a conversation."""
    from ..services import workspace_database as db
    from ..services.workspace_summary import generate_summary

    # Verify conversation exists
    conversation = db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all messages
    messages = db.get_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # Generate summary (awaited since this is a manual trigger)
    summary_text = await generate_summary(conversation_id, messages, len(messages))
    if not summary_text:
        raise HTTPException(status_code=500, detail="Summary generation failed")

    # Save it
    result = db.save_summary(conversation_id, summary_text, len(messages))
    return SummaryResponse(**result)


# ============================================================================
# Category Endpoints
# ============================================================================

class CategoryCreate(BaseModel):
    """Request body for creating a new workspace category."""
    name: str
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Request body for updating a workspace category."""
    name: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    """Response model for a workspace category."""
    id: int
    name: str
    color: Optional[str]
    sort_order: int
    created_at: Optional[str]


class CategoryReorder(BaseModel):
    """Request body for reordering workspace categories."""
    ordered_ids: list[int]


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    """List all workspace categories ordered by sort_order."""
    from ..services import workspace_database as db

    categories = db.get_categories()
    return [CategoryResponse(**c) for c in categories]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(body: CategoryCreate):
    """Create a new workspace category."""
    from ..services import workspace_database as db

    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Category name is required")
    if body.name.strip().lower() == "uncategorized":
        raise HTTPException(status_code=400, detail="Cannot create a category named 'Uncategorized'")
    try:
        category = db.create_category(body.name.strip(), body.color)
        return CategoryResponse(**category)
    except Exception as e:
        if "UNIQUE" in str(e).upper():
            raise HTTPException(status_code=409, detail="Category name already exists")
        raise


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category_endpoint(category_id: int, body: CategoryUpdate):
    """Update a category's name or color."""
    from ..services import workspace_database as db

    if body.name and body.name.strip().lower() == "uncategorized":
        raise HTTPException(status_code=400, detail="Cannot rename to 'Uncategorized'")
    result = db.update_category(category_id, name=body.name, color=body.color)
    if not result:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(**result)


@router.delete("/categories/{category_id}")
async def delete_category_endpoint(category_id: int):
    """Delete a category. Conversations in this category become Uncategorized."""
    from ..services import workspace_database as db

    success = db.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}


@router.post("/categories/reorder", response_model=list[CategoryResponse])
async def reorder_categories_endpoint(body: CategoryReorder):
    """Reorder categories by providing an ordered list of IDs."""
    from ..services import workspace_database as db

    categories = db.reorder_categories(body.ordered_ids)
    return [CategoryResponse(**c) for c in categories]


# ============================================================================
# Search Endpoint
# ============================================================================

class SearchExcerpt(BaseModel):
    """A single matching excerpt from a message."""
    message_id: int
    role: str
    excerpt: str


class SearchResultItem(BaseModel):
    """A search result with conversation info and matching excerpts."""
    conversation_id: int
    conversation_title: Optional[str]
    category: str
    matching_excerpts: list[SearchExcerpt]


@router.get("/search", response_model=list[SearchResultItem])
async def search_conversations_endpoint(q: str = "", limit: int = 20):
    """Full-text search across workspace conversations and messages."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    if limit < 1 or limit > 100:
        limit = 20

    from ..services import workspace_database as db

    results = db.search_conversations(q.strip(), limit=limit)
    return [SearchResultItem(**r) for r in results]


# ============================================================================
# Usage Tracking Endpoints
# ============================================================================

@router.get("/usage")
async def get_usage_overview():
    """Get usage summary across daily, weekly, and monthly periods."""
    from ..services import workspace_database as db
    return db.get_usage_summary()


@router.get("/usage/{period}")
async def get_usage_period(period: str):
    """Get usage for a specific period (daily, weekly, monthly)."""
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Period must be daily, weekly, or monthly")

    from ..services import workspace_database as db
    return db.get_usage_by_period(period)


@router.get("/conversations/{conversation_id}/cost")
async def get_conversation_cost(conversation_id: int):
    """Get cost zone breakdown for a conversation."""
    from ..services import workspace_database as db

    # Look up the conversation's model to use correct pricing
    conv = db.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    model = conv.get("model", "opus") or "opus"
    result = db.get_conversation_cost_zones(conversation_id, model=model)

    return result


@router.post("/usage/rate-limit")
async def log_rate_limit(event_type: str, notes: str | None = None):
    """Log a rate limit event for calibration.

    Call this when you hit a rate limit (5-hour wait, weekly cap, etc.)
    to help calibrate the usage prediction meters.
    """
    if event_type not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="event_type must be daily, weekly, or monthly")

    from ..services import workspace_database as db

    # Get current usage to record what the limits looked like at time of hit
    usage = db.get_usage_by_period(event_type)
    result = db.log_rate_limit_event(
        event_type=event_type,
        tokens_at_hit=usage["total_tokens"],
        premium_tokens_at_hit=0,  # Will be filled by the premium ledger
        message_count_at_hit=usage["message_count"],
        notes=notes,
    )
    return result


@router.get("/usage/rate-limits")
async def get_rate_limits():
    """Get rate limit event history."""
    from ..services import workspace_database as db
    return db.get_rate_limit_history()


@router.get("/usage/calibration")
async def get_calibration():
    """Get calibrated limits based on historical rate limit events."""
    from ..services import workspace_database as db

    try:
        return db.get_calibrated_limits()
    except Exception as e:
        logger.warning("Failed to get calibrated limits: %s", e)
        # Return empty calibration data so the UI degrades gracefully
        empty = {"estimated_limit": None, "safe_limit": None, "sample_count": 0, "last_hit": None, "confidence": "none"}
        return {"daily": empty, "weekly": empty, "monthly": empty}


@router.get("/usage/premium")
async def get_premium_summary():
    """Get premium-zone usage summary across all conversations."""
    from ..services import workspace_database as db
    return db.get_premium_usage_summary()


# ============================================================================
# Token Processing Log
# ============================================================================

@router.get("/conversations/{conversation_id}/token-log")
async def get_token_log(conversation_id: int):
    """Get the full token processing log for a conversation.

    Returns every logged event: assistant turns, tool calls, tool results,
    and SDK-reported result summaries with actual API token counts.
    """
    from ..services import workspace_database as db
    entries = db.get_token_log(conversation_id)
    return {"entries": entries, "count": len(entries)}


@router.get("/conversations/{conversation_id}/token-log/summary")
async def get_token_log_summary(conversation_id: int):
    """Get a summary of token usage for a conversation.

    Includes per-tool breakdowns, cumulative API usage, and estimated vs
    actual token counts.
    """
    from ..services import workspace_database as db
    return db.get_token_log_summary(conversation_id)


@router.delete("/conversations/{conversation_id}/token-log")
async def clear_token_log(conversation_id: int):
    """Clear all token log entries for a conversation."""
    from ..services import workspace_database as db
    count = db.clear_token_log(conversation_id)
    return {"deleted": count}


# ============================================================================
# Fork, Paginate, Export, Inject Endpoints (Phase 4)
# ============================================================================

class ForkRequest(BaseModel):
    """Request body for forking a conversation."""
    fork_at_message_id: Optional[int] = None


@router.post("/conversations/{conversation_id}/fork")
async def fork_conversation_endpoint(conversation_id: int, body: ForkRequest):
    """Fork a conversation from a specific message point."""
    from ..services.workspace_database import fork_conversation as db_fork

    try:
        new_conversation = db_fork(
            conversation_id=conversation_id,
            fork_at_message_id=body.fork_at_message_id,
        )
        return new_conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
):
    """Get paginated messages for a conversation."""
    from ..services.workspace_database import get_messages_paginated

    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be non-negative")

    return get_messages_paginated(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )


@router.get("/conversations/{conversation_id}/export")
async def export_conversation_endpoint(conversation_id: int, format: str = "markdown"):
    """Export a conversation as a downloadable file."""
    if format != "markdown":
        raise HTTPException(status_code=400, detail="Only 'markdown' format is supported")

    from ..services.workspace_database import export_conversation_markdown, get_conversation

    try:
        markdown_content = export_conversation_markdown(conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    conv = get_conversation(conversation_id)
    safe_title = (conv.get("title") or "conversation").replace(" ", "_") if conv else "conversation"
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in ("_", "-"))
    filename = f"{safe_title}_{conversation_id}.md"

    from fastapi.responses import Response

    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


class InjectRequest(BaseModel):
    """Request body for injecting messages from another conversation."""
    source_conversation_id: int
    message_ids: list[int] | str  # list of IDs or "all"


@router.post("/conversations/{conversation_id}/inject")
async def get_injection_content(conversation_id: int, body: InjectRequest):
    """Fetch formatted injection content from a source conversation.

    Returns the formatted injection text that the frontend will prepend
    to the user's next message. Does NOT modify any conversations.
    """
    from ..services.workspace_database import get_conversation, get_messages_paginated

    source = get_conversation(body.source_conversation_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source conversation not found")

    target = get_conversation(conversation_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target conversation not found")

    source_title = source.get("title") or "Untitled"

    result = get_messages_paginated(body.source_conversation_id, limit=500, offset=0)
    all_messages = result["messages"]

    if body.message_ids == "all":
        selected = all_messages
    else:
        id_set = set(body.message_ids) if isinstance(body.message_ids, list) else set()
        selected = [m for m in all_messages if m["id"] in id_set]

    if not selected:
        raise HTTPException(status_code=400, detail="No messages selected for injection")

    formatted_messages = []
    for m in selected:
        role_label = "User" if m["role"] == "user" else "Assistant"
        formatted_messages.append(f"{role_label}: {m['content']}")

    return {
        "source_title": source_title,
        "source_conversation_id": body.source_conversation_id,
        "message_count": len(selected),
        "formatted_messages": formatted_messages,
    }


# ============================================================================
# GitHub Repo Selector Endpoints
# ============================================================================

class GitHubCloneRequest(BaseModel):
    """Request body for cloning a GitHub repository."""
    repo_url: str
    repo_name: str


@router.get("/github/repos")
async def list_github_repos():
    """List GitHub repos available via the `gh` CLI."""
    from ..services.workspace_github import list_github_repos as gh_list_repos

    return gh_list_repos()


@router.post("/github/clone")
async def clone_github_repo(body: GitHubCloneRequest):
    """Clone a GitHub repo locally and return the local path."""
    from ..services.workspace_github import ensure_repo_cloned

    if not body.repo_url or not body.repo_name:
        raise HTTPException(status_code=400, detail="repo_url and repo_name are required")

    try:
        local_path = ensure_repo_cloned(body.repo_url, body.repo_name)
        return {"local_path": local_path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Git Branch Management Endpoints
# ============================================================================

class BranchRenameRequest(BaseModel):
    """Request body for renaming a git branch."""
    old_name: str
    new_name: str


class BranchInfoResponse(BaseModel):
    """Response model for branch information."""
    current_branch: str
    branches: list[str]


@router.get("/git/branches")
async def list_git_branches(working_directory: str):
    """List git branches for a working directory."""
    import subprocess
    from pathlib import Path

    work_dir = Path(working_directory)
    if not work_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid working directory")

    try:
        result = subprocess.run(
            ["git", "branch", "--list", "--no-color"],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail="Not a git repository")

        branches = []
        current = "main"
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line.startswith("* "):
                current = line[2:].strip()
                branches.append(current)
            elif line:
                branches.append(line)

        return BranchInfoResponse(current_branch=current, branches=branches)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system")


@router.post("/git/branch/rename")
async def rename_git_branch(body: BranchRenameRequest, working_directory: str):
    """Rename a git branch locally and update remote."""
    import subprocess
    from pathlib import Path

    work_dir = Path(working_directory)
    if not work_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid working directory")

    old_name = body.old_name.strip()
    new_name = body.new_name.strip()

    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Branch names cannot be empty")
    if old_name in ("main", "master"):
        raise HTTPException(status_code=400, detail="Cannot rename main/master branch")

    try:
        # Rename the local branch
        result = subprocess.run(
            ["git", "branch", "-m", old_name, new_name],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=400, detail=f"Failed to rename branch: {result.stderr.strip()}"
            )

        # Try to update remote (delete old, push new)
        # Delete old remote branch (ignore errors if it doesn't exist on remote)
        subprocess.run(
            ["git", "push", "origin", "--delete", old_name],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Push new branch name and set upstream
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", new_name],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        remote_updated = push_result.returncode == 0

        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "remote_updated": remote_updated,
            "message": f"Branch renamed from '{old_name}' to '{new_name}'" + (
                " (remote updated)" if remote_updated else " (local only - push manually)"
            ),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system")


class GitRemoteInfoResponse(BaseModel):
    """Response model for git remote info."""
    remote_url: str
    github_url: str
    owner: str
    repo: str


@router.get("/git/remote-info")
async def get_git_remote_info(working_directory: str):
    """Get the GitHub remote URL and owner/repo for a working directory."""
    import subprocess
    from pathlib import Path

    work_dir = Path(working_directory)
    if not work_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid working directory")

    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail="No remote origin found")

        remote_url = result.stdout.strip()

        # Parse owner/repo from various URL formats:
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        owner = ""
        repo = ""
        github_url = ""

        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                # git@github.com:owner/repo.git
                path_part = remote_url.split(":", 1)[1]
            else:
                # https://github.com/owner/repo.git
                from urllib.parse import urlparse
                parsed = urlparse(remote_url)
                path_part = parsed.path.lstrip("/")

            # Remove .git suffix
            if path_part.endswith(".git"):
                path_part = path_part[:-4]

            parts = path_part.split("/")
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1]
                github_url = f"https://github.com/{owner}/{repo}"

        if not github_url:
            raise HTTPException(status_code=400, detail="Not a GitHub repository")

        return GitRemoteInfoResponse(
            remote_url=remote_url,
            github_url=github_url,
            owner=owner,
            repo=repo,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get remote info: {str(e)}")


class GitCommitInfo(BaseModel):
    """Response model for a single git commit."""
    sha: str
    short_sha: str
    message: str
    author: str
    timestamp: str
    relative_time: str


class GitCommitsResponse(BaseModel):
    """Response model for recent git commits."""
    commits: list[GitCommitInfo]
    branch: str


@router.get("/git/commits")
async def list_recent_git_commits(working_directory: str, limit: int = 10):
    """Get recent git commits for a working directory."""
    import subprocess
    from datetime import datetime, timezone
    from pathlib import Path

    work_dir = Path(working_directory)
    if not work_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid working directory")

    if limit < 1 or limit > 50:
        limit = 10

    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get recent commits with format: sha|author|timestamp|message
        result = subprocess.run(
            [
                "git", "log",
                f"-{limit}",
                "--format=%H|%an|%aI|%s",
            ],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail="Not a git repository or no commits")

        commits = []
        now = datetime.now(timezone.utc)
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            sha, author, timestamp_str, message = parts

            # Calculate relative time
            try:
                commit_time = datetime.fromisoformat(timestamp_str)
                delta = now - commit_time
                total_seconds = int(delta.total_seconds())
                if total_seconds < 60:
                    relative = "just now"
                elif total_seconds < 3600:
                    mins = total_seconds // 60
                    relative = f"{mins}m ago"
                elif total_seconds < 86400:
                    hours = total_seconds // 3600
                    relative = f"{hours}h ago"
                else:
                    days = total_seconds // 86400
                    relative = f"{days}d ago"
            except (ValueError, TypeError):
                relative = ""

            commits.append(GitCommitInfo(
                sha=sha,
                short_sha=sha[:7],
                message=message,
                author=author,
                timestamp=timestamp_str,
                relative_time=relative,
            ))

        return GitCommitsResponse(commits=commits, branch=branch)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get commits: {str(e)}")


class GitPrInfoResponse(BaseModel):
    """Response model for pull request info."""
    pr_url: str
    pr_number: int
    pr_title: str
    pr_state: str


@router.get("/git/pr-info")
async def get_git_pr_info(working_directory: str, branch: Optional[str] = None):
    """Get PR info for the current branch using gh CLI."""
    import subprocess
    from pathlib import Path

    work_dir = Path(working_directory)
    if not work_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid working directory")

    try:
        # If no branch specified, get the current one
        if not branch:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail="Not a git repository")
            branch = result.stdout.strip()

        if not branch:
            raise HTTPException(status_code=400, detail="Could not determine current branch")

        # Use gh CLI to find PR for this branch
        result = subprocess.run(
            [
                "gh", "pr", "view", branch,
                "--json", "url,number,title,state",
            ],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=404,
                detail=f"No pull request found for branch '{branch}'"
            )

        pr_data = json.loads(result.stdout)
        return GitPrInfoResponse(
            pr_url=pr_data["url"],
            pr_number=pr_data["number"],
            pr_title=pr_data["title"],
            pr_state=pr_data["state"],
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="gh CLI not found on system")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PR info: {str(e)}")


# ============================================================================
# Walkie-Talkie Status Endpoint
# ============================================================================

@router.get("/sessions/{session_id}/walkie-talkie/status")
async def get_walkie_talkie_status(session_id: str):
    """Get the walkie-talkie status for a workspace session.

    Useful for debugging and for the UI to check if a session is waiting.
    """
    from ..services.workspace_chat_session import get_session as ws_get_session

    session = ws_get_session(session_id)
    if not session:
        return {"active": False, "waiting": False, "queue_size": 0}
    return {
        "active": session.walkie_talkie_enabled,
        "waiting": session.walkie_talkie_waiting,
        "queue_size": session.walkie_talkie_queue.qsize(),
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

_STREAM_SENTINEL = object()


async def _stream_with_walkie_talkie(
    websocket: WebSocket,
    session,
    response_gen,
):
    """Stream an agent response while concurrently handling walkie-talkie messages.

    The core problem: Starlette WebSockets are single-reader — you can't call
    ``receive_text()`` while you're in an ``async for chunk`` loop.  So during
    response streaming, walkie-talkie messages from the client sit in the
    transport buffer and never reach the session queue.

    This helper decouples response generation from WebSocket I/O using an
    ``asyncio.Queue``.  A background producer feeds chunks into the queue while
    the main coroutine alternates between:

    1. Sending queued response chunks to the client.
    2. Polling for incoming walkie-talkie messages (short timeout).

    Worst-case delivery latency for a walkie-talkie message is ~250 ms, which
    is well within the seconds-long gap between agent tool calls where the
    ``PreToolUse`` hook actually fires.
    """
    chunk_queue: asyncio.Queue = asyncio.Queue()

    async def _produce():
        try:
            async for chunk in response_gen:
                await chunk_queue.put(chunk)
        finally:
            await chunk_queue.put(_STREAM_SENTINEL)

    producer = asyncio.create_task(_produce())

    try:
        while True:
            # --- 1. Wait for the next response chunk (with timeout) ---
            try:
                chunk = await asyncio.wait_for(chunk_queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                chunk = None

            if chunk is _STREAM_SENTINEL:
                break

            if chunk is not None:
                await websocket.send_json(chunk)
                if chunk.get("type") == "agent_waiting":
                    logger.info(
                        "Agent waiting in session %s: %s",
                        session.session_id,
                        chunk.get("question", "")[:80],
                    )
                # Drain any buffered chunks for throughput
                while not chunk_queue.empty():
                    c = chunk_queue.get_nowait()
                    if c is _STREAM_SENTINEL:
                        return
                    await websocket.send_json(c)

            # --- 2. Poll for incoming walkie-talkie / ping messages ---
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                msg = json.loads(data)
                msg_type = msg.get("type")
                if msg_type == "walkie_talkie":
                    content = msg.get("content", "")
                    if content:
                        await session.queue_walkie_talkie_message(content)
                        await websocket.send_json({
                            "type": "walkie_talkie_queued",
                            "content": content[:100],
                        })
                        logger.info(
                            "Walkie-talkie queued during stream in session %s",
                            session.session_id,
                        )
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
    finally:
        producer.cancel()
        try:
            await producer
        except asyncio.CancelledError:
            pass


@router.websocket("/ws")
async def workspace_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for workspace chat.

    Message protocol:

    Client -> Server:
    - {"type": "start", "conversation_id": int | null, "working_directory": "...", "context_mode": "1m"|"200k"} - Start/resume session
    - {"type": "message", "content": "..."} - Send user message
    - {"type": "walkie_talkie", "content": "..."} - Inject message into running agent
    - {"type": "answer", "answers": {...}} - Answer to structured questions
    - {"type": "ping"} - Keep-alive ping

    Server -> Client:
    - {"type": "conversation_created", "conversation_id": int} - New conversation created
    - {"type": "text", "content": "..."} - Text chunk from Claude
    - {"type": "tool_call", "tool": "...", "input": {...}} - Tool being called
    - {"type": "token_usage", "total_tokens": int, "context_window": int} - Token usage update
    - {"type": "token_log", "entry": {...}} - Per-turn token processing log entry
    - {"type": "agent_waiting", "question": "..."} - Agent is waiting for user input
    - {"type": "walkie_talkie_queued", "content": "..."} - Confirmation that message was queued
    - {"type": "response_done"} - Response complete
    - {"type": "error", "content": "..."} - Error message
    - {"type": "pong"} - Keep-alive pong
    """
    # Always accept WebSocket first to avoid opaque 403 errors
    await websocket.accept()

    # Generate a unique session ID from the websocket object
    session_id = f"ws-{id(websocket)}"
    logger.info(f"Workspace WebSocket connected, session_id={session_id}")

    from ..services.workspace_chat_session import create_session as ws_create_session
    from ..services.workspace_chat_session import get_session as ws_get_session
    from ..services.workspace_chat_session import remove_session as ws_remove_session

    session = None

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                logger.debug(f"Workspace received message type: {msg_type}")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                elif msg_type == "start":
                    # Get optional conversation_id and working_directory
                    conversation_id = message.get("conversation_id")
                    working_directory = message.get("working_directory")

                    # If resuming an existing conversation without an explicit working_directory,
                    # look it up from the database so the agent uses the same cwd.
                    if conversation_id is not None and working_directory is None:
                        from ..services.workspace_database import get_conversation
                        conv = get_conversation(conversation_id)
                        if conv:
                            working_directory = conv.get("working_directory")

                    logger.debug(
                        f"Processing start message with conversation_id={conversation_id}, "
                        f"working_directory={working_directory}"
                    )

                    try:
                        # Extract context mode from start message.
                        # Default to "200k" (safer/cheaper) rather than "1m" so that
                        # any frontend bug that omits context_mode doesn't silently
                        # activate 1M billing.
                        context_mode = message.get("context_mode", "200k")
                        if context_mode not in ("1m", "200k"):
                            logger.warning(
                                "Invalid context_mode '%s' in start message, defaulting to '200k'",
                                context_mode,
                            )
                            context_mode = "200k"

                        # Extract cost control settings from start message
                        cost_settings = message.get("cost_settings")
                        logger.info(
                            "WS EFFORT TRACE: cost_settings=%s, effort=%s",
                            cost_settings, cost_settings.get("effort") if cost_settings else None,
                        )

                        # Extract model preference from start message (for per-panel model routing)
                        model = message.get("model")  # e.g. "opus", "sonnet", or None

                        # Server-side safety net: when resuming an existing conversation,
                        # cross-check context_mode against the stored DB value. The DB
                        # record is authoritative — if the frontend sends a stale or
                        # missing context_mode, use the DB value instead.
                        if conversation_id is not None:
                            from ..services.workspace_database import get_conversation as get_conv_for_mode
                            conv_for_mode = get_conv_for_mode(conversation_id)
                            if conv_for_mode:
                                stored_mode = conv_for_mode.get("context_mode")
                                stored_model = conv_for_mode.get("model")
                                if stored_mode and stored_mode != context_mode:
                                    logger.warning(
                                        "context_mode mismatch: WS=%s, DB=%s for conversation %d. Using DB value.",
                                        context_mode, stored_mode, conversation_id,
                                    )
                                    context_mode = stored_mode
                                if stored_model and stored_model != model:
                                    logger.warning(
                                        "model mismatch: WS=%s, DB=%s for conversation %d. Using DB value.",
                                        model, stored_model, conversation_id,
                                    )
                                    model = stored_model

                        # Log full start params for debugging 200K vs 1M issues
                        logger.info(
                            "WS start: context_mode=%s, model=%s, conversation_id=%s, session_id=%s",
                            context_mode, model, conversation_id, session_id,
                        )

                        # Create a new workspace session
                        logger.debug(f"Creating workspace session {session_id}")
                        session = await ws_create_session(
                            session_id,
                            conversation_id=conversation_id,
                            working_directory=working_directory,
                            context_mode=context_mode,
                            cost_settings=cost_settings,
                            model=model,
                        )

                        # Wire walkie-talkie settings from the global settings store.
                        # The comm_check_frequency value of "never" disables the hook entirely.
                        try:
                            from registry import get_setting
                            comm_freq = get_setting("comm_check_frequency", "per_feature")
                            session.walkie_talkie_enabled = comm_freq != "never"
                            logger.debug(
                                "Walkie-talkie: enabled=%s (comm_check_frequency=%s)",
                                session.walkie_talkie_enabled, comm_freq,
                            )
                        except Exception as e:
                            logger.warning("Failed to load walkie-talkie settings: %s", e)

                        logger.debug("Workspace session created, starting...")

                        # Stream the initial response with walkie-talkie support.
                        # Previously this was a plain ``async for`` loop which blocked
                        # the WebSocket reader, so walkie-talkie messages sent during
                        # the initial session could never be received.
                        await _stream_with_walkie_talkie(
                            websocket, session,
                            session.start(),
                        )
                        logger.debug("Workspace session start complete")
                    except Exception as e:
                        logger.exception(f"Error starting workspace session {session_id}")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Failed to start session: {str(e)}"
                        })

                elif msg_type == "walkie_talkie":
                    # Walkie-talkie: inject a message into the running agent's queue.
                    # The message will be delivered on the agent's next tool call via
                    # the PreToolUse hook.
                    content = message.get("content", "")
                    if content and session:
                        await session.queue_walkie_talkie_message(content)
                        await websocket.send_json({
                            "type": "walkie_talkie_queued",
                            "content": content[:100],  # Truncated echo for UI confirmation
                        })
                    elif not session:
                        await websocket.send_json({
                            "type": "error",
                            "content": "No active session. Send 'start' first."
                        })

                elif msg_type == "message":
                    if not session:
                        session = ws_get_session(session_id)
                        if not session:
                            await websocket.send_json({
                                "type": "error",
                                "content": "No active session. Send 'start' first."
                            })
                            continue

                    user_content = message.get("content", "").strip()
                    if not user_content:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Empty message"
                        })
                        continue

                    # Extract optional image attachments
                    raw_attachments = message.get("attachments", [])
                    attachments = None
                    if raw_attachments:
                        from ..schemas import ImageAttachment
                        try:
                            attachments = [ImageAttachment(**att) for att in raw_attachments]
                        except Exception as e:
                            logger.warning("Invalid attachment data: %s", e)

                    # Stream Claude's response while listening for walkie-talkie
                    # messages.  The helper multiplexes response chunks with
                    # incoming WebSocket reads so the user can inject messages
                    # into the running agent mid-stream.
                    await _stream_with_walkie_talkie(
                        websocket, session,
                        session.send_message(user_content, attachments=attachments),
                    )

                elif msg_type == "answer":
                    # User answered a structured question
                    if not session:
                        session = ws_get_session(session_id)
                        if not session:
                            await websocket.send_json({
                                "type": "error",
                                "content": "No active session. Send 'start' first."
                            })
                            continue

                    # Format the answers as a natural response
                    answers = message.get("answers", {})
                    if isinstance(answers, dict):
                        response_parts = []
                        for question_idx, answer_value in answers.items():
                            if isinstance(answer_value, list):
                                response_parts.append(", ".join(answer_value))
                            else:
                                response_parts.append(str(answer_value))
                        user_response = "; ".join(response_parts) if response_parts else "OK"
                    else:
                        user_response = str(answers)

                    # Stream Claude's response (with walkie-talkie support)
                    await _stream_with_walkie_talkie(
                        websocket, session,
                        session.send_message(user_response),
                    )

                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {msg_type}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON"
                })

    except WebSocketDisconnect:
        logger.info(f"Workspace chat WebSocket disconnected for session {session_id}")

    except Exception as e:
        logger.exception(f"Workspace chat WebSocket error for session {session_id}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}"
            })
        except Exception:
            pass

    finally:
        # Clean up the session on disconnect -- workspace sessions are not resumed
        # across WebSocket connections (unlike the assistant which keeps sessions alive).
        await ws_remove_session(session_id)


# ============================================================================
# Library Endpoints
# ============================================================================

@router.get("/library")
async def list_global_library_files():
    """List all global library files (not attached to any conversation)."""
    from ..services.workspace_library import list_global_files
    return list_global_files()


@router.get("/library/conversation/{conversation_id}")
async def list_conversation_library_files(conversation_id: int):
    """List files for a conversation (global + per-chat)."""
    from ..services.workspace_library import list_conversation_files
    return list_conversation_files(conversation_id)


@router.get("/library/active/{conversation_id}")
async def get_active_library_files(conversation_id: int):
    """Get all files currently active in a conversation's context."""
    from ..services.workspace_library import get_active_files
    return get_active_files(conversation_id)


@router.post("/library/upload")
async def upload_library_file(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = Form(None),
    display_name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):
    """Upload a file to the library via multipart form data."""
    from ..services.workspace_library import MAX_FILE_SIZE, upload_file, validate_file_extension

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    filename = file.filename or "untitled"
    if not validate_file_extension(filename):
        raise HTTPException(status_code=400, detail=f"File type not supported: {filename}")

    result = upload_file(
        filename=filename,
        content=content,
        conversation_id=conversation_id,
        display_name=display_name,
        tags=tags,
    )
    return result


@router.post("/library/upload-text")
async def upload_text_content(body: dict):
    """Upload text content directly (for paste operations)."""
    from ..services.workspace_library import upload_text

    filename = body.get("filename", "untitled.txt")
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    result = upload_text(
        filename=filename,
        text_content=content,
        conversation_id=body.get("conversation_id"),
        display_name=body.get("display_name"),
        tags=body.get("tags"),
    )
    return result


@router.get("/library/{file_id}/content")
async def get_library_file_content(file_id: int):
    """Get the content of a library file."""
    from ..services.workspace_library import get_file_content

    content = get_file_content(file_id)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or content unavailable")
    return {"content": content}


@router.patch("/library/{file_id}")
async def update_library_file(file_id: int, body: dict):
    """Update file metadata (display_name, tags)."""
    from ..services.workspace_library import update_file_metadata

    result = update_file_metadata(
        file_id=file_id,
        display_name=body.get("display_name"),
        tags=body.get("tags"),
    )
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


@router.delete("/library/{file_id}")
async def delete_library_file(file_id: int):
    """Delete a library file."""
    from ..services.workspace_library import delete_file

    success = delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True}


@router.post("/library/{file_id}/toggle/{conversation_id}")
async def toggle_library_file_context(file_id: int, conversation_id: int):
    """Toggle a file's active/inactive status in a conversation's context."""
    from ..services.workspace_library import toggle_file_in_context

    result = toggle_file_in_context(file_id, conversation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="File not found")
    return result


# ============================================================================
# Repository Endpoints
# ============================================================================

@router.post("/repos/connect")
async def connect_repository(body: dict):
    """Connect a GitHub repository."""
    from ..services.workspace_repos import connect_repo

    repo_url = body.get("repo_url", "")
    token = body.get("token", "")
    branch = body.get("branch", "main")
    conversation_id = body.get("conversation_id")

    if not repo_url:
        raise HTTPException(status_code=400, detail="Repository URL is required")
    if not token:
        raise HTTPException(status_code=400, detail="Personal access token is required")

    try:
        result = connect_repo(
            repo_url=repo_url,
            token=token,
            branch=branch,
            conversation_id=conversation_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/repos/{repo_id}")
async def disconnect_repository(repo_id: int, delete_local: bool = False):
    """Disconnect a repo and optionally delete local clone."""
    from ..services.workspace_repos import disconnect_repo

    success = disconnect_repo(repo_id, delete_local=delete_local)
    if not success:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"success": True}


@router.get("/repos")
async def list_repositories(conversation_id: Optional[int] = None):
    """List connected repositories."""
    from ..services.workspace_repos import list_repos
    return list_repos(conversation_id=conversation_id)


@router.get("/repos/{repo_id}/tree")
async def get_repository_tree(repo_id: int):
    """Get file tree for a connected repo."""
    from ..services.workspace_repos import get_repo_tree

    tree = get_repo_tree(repo_id)
    if tree is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return tree


@router.get("/repos/{repo_id}/file")
async def get_repository_file(repo_id: int, path: str):
    """Read a specific file from a connected repo."""
    from ..services.workspace_repos import get_repo_file

    content = get_repo_file(repo_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or binary file")
    return {"content": content, "path": path}


@router.post("/repos/{repo_id}/sync")
async def sync_repository(repo_id: int):
    """Pull latest changes for a connected repo."""
    from ..services.workspace_repos import sync_repo

    try:
        result = sync_repo(repo_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
