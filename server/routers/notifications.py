"""
Workspace Notifications Router
===============================

REST endpoints for managing structured workspace agent notifications.
Supports notification types: summary, roadmap, progress, milestone.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspace/notifications", tags=["workspace-notifications"])


# ============================================================================
# Pydantic Models
# ============================================================================

class NotificationCreateRequest(BaseModel):
    """Request body for creating a new notification."""
    conversation_id: Optional[int] = None
    notification_type: str  # "summary", "roadmap", "progress", "milestone"
    title: str
    content: str
    metadata: Optional[dict] = None


class NotificationResponse(BaseModel):
    """Response model for a single notification."""
    id: int
    conversation_id: Optional[int]
    notification_type: str
    title: str
    content: str
    metadata: Optional[dict] = None
    is_read: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    conversation_id: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 50,
):
    """List all notifications with optional filters.

    Args:
        conversation_id: Filter by conversation ID.
        type: Filter by notification type (summary, roadmap, progress, milestone).
        limit: Maximum number of results (default 50).
    """
    from ..services.workspace_database import VALID_NOTIFICATION_TYPES, get_notifications

    if type is not None and type not in VALID_NOTIFICATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid notification type '{type}'. Must be one of: {', '.join(VALID_NOTIFICATION_TYPES)}",
        )

    if limit < 1 or limit > 500:
        limit = 50

    notifications = get_notifications(
        conversation_id=conversation_id,
        notification_type=type,
        limit=limit,
    )
    return [NotificationResponse(**n) for n in notifications]


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification_detail(notification_id: int):
    """Get a single notification by ID."""
    from ..services.workspace_database import get_notification

    notification = get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse(**notification)


@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification_endpoint(body: NotificationCreateRequest):
    """Create a new notification."""
    from ..services.workspace_database import create_notification

    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    try:
        notification = create_notification(
            conversation_id=body.conversation_id,
            notification_type=body.notification_type,
            title=body.title.strip(),
            content=body.content.strip(),
            metadata=body.metadata,
        )
        return NotificationResponse(**notification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification_endpoint(notification_id: int):
    """Delete a single notification."""
    from ..services.workspace_database import delete_notification

    success = delete_notification(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "message": "Notification deleted"}


@router.delete("/")
async def clear_notifications_endpoint(conversation_id: Optional[int] = None):
    """Clear all notifications, optionally filtered by conversation ID."""
    from ..services.workspace_database import clear_notifications

    count = clear_notifications(conversation_id=conversation_id)
    return {"success": True, "deleted_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read_endpoint(notification_id: int):
    """Mark a single notification as read."""
    from ..services.workspace_database import mark_notification_read

    notification = mark_notification_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse(**notification)


@router.post("/mark-all-read")
async def mark_all_read_endpoint(conversation_id: Optional[int] = None):
    """Mark all notifications as read, optionally filtered by conversation ID."""
    from ..services.workspace_database import mark_all_notifications_read

    count = mark_all_notifications_read(conversation_id=conversation_id)
    return {"success": True, "updated_count": count}
