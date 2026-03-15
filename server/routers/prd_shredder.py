"""PRD Shredder Router — REST + SSE endpoints for the PRD queue.

Phase 1: Queue CRUD + status
Phase 2: Analysis trigger
Phase 3: Execution control (start/stop/logs)
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.prd_shredder import PRDStatus
from ..services.prd_shredder import get_shredder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prd-shredder", tags=["prd-shredder"])


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class EnqueueRequest(BaseModel):
    """Request to add a PRD to the shredder queue."""
    title: str = Field(..., min_length=1, max_length=500)
    prd_text: str = Field(..., min_length=10)
    target_repo: str = Field(..., min_length=1)
    target_branch: str = Field(default="main")


class EnqueueResponse(BaseModel):
    id: str
    title: str
    status: str
    position: int


# ---------------------------------------------------------------------------
# Queue Endpoints
# ---------------------------------------------------------------------------

@router.post("/enqueue", response_model=EnqueueResponse)
async def enqueue_prd(body: EnqueueRequest):
    """Add a PRD to the shredder queue."""
    shredder = get_shredder()
    item = await shredder.enqueue(
        title=body.title,
        prd_text=body.prd_text,
        target_repo=body.target_repo,
        target_branch=body.target_branch,
    )

    # Calculate position in queue
    all_items = await shredder.queue.list_all()
    queued = [i for i in all_items if i.status == PRDStatus.QUEUED]
    position = next((idx + 1 for idx, i in enumerate(queued) if i.id == item.id), len(queued))

    return EnqueueResponse(
        id=item.id,
        title=item.title,
        status=item.status.value,
        position=position,
    )


@router.get("/queue")
async def list_queue(status: Optional[str] = None):
    """List all items in the queue, optionally filtered by status."""
    shredder = get_shredder()
    all_items = await shredder.queue.list_all()

    if status:
        try:
            filter_status = PRDStatus(status)
            all_items = [i for i in all_items if i.status == filter_status]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    return {
        "items": [i.model_dump() for i in all_items],
        "count": len(all_items),
    }


@router.get("/stats")
async def get_stats():
    """Get queue statistics."""
    shredder = get_shredder()
    stats = await shredder.queue.get_stats()
    return stats.model_dump()


@router.get("/items/{item_id}")
async def get_item(item_id: str):
    """Get a single queue item by ID."""
    shredder = get_shredder()
    item = await shredder.queue.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
    return item.model_dump()


@router.get("/items/{item_id}/logs")
async def get_item_logs(item_id: str, offset: int = 0):
    """Get build logs for a queue item."""
    shredder = get_shredder()
    item = await shredder.queue.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
    logs = item.build_log[offset:]
    return {"logs": logs, "total": len(item.build_log), "offset": offset}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    """Delete an item from the queue (only if queued or done/failed)."""
    shredder = get_shredder()
    item = await shredder.queue.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

    if item.status not in (PRDStatus.QUEUED, PRDStatus.DONE, PRDStatus.FAILED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete item with status '{item.status.value}'. Wait for it to finish."
        )

    await shredder.queue.delete(item_id)
    return {"deleted": True, "item_id": item_id}


# ---------------------------------------------------------------------------
# SSE Logs Stream
# ---------------------------------------------------------------------------

@router.get("/items/{item_id}/stream")
async def stream_logs(item_id: str):
    """SSE endpoint that streams build logs in real-time."""
    shredder = get_shredder()
    item = await shredder.queue.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

    queue: asyncio.Queue = asyncio.Queue()

    def on_progress(message: str) -> None:
        queue.put_nowait({"type": "log", "message": message})

    shredder.subscribe_progress(item_id, on_progress)

    async def event_generator():
        try:
            # Send existing logs first
            for log_line in item.build_log:
                yield f"data: {json.dumps({'type': 'log', 'message': log_line})}\n\n"

            # Stream new logs
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                    # Check if item is done
                    current = await shredder.queue.get(item_id)
                    if current and current.status in (PRDStatus.DONE, PRDStatus.FAILED):
                        yield f"data: {json.dumps({'type': 'complete', 'status': current.status.value})}\n\n"
                        break
        finally:
            shredder.unsubscribe_progress(item_id, on_progress)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Control Endpoints
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_shredder():
    """Start the background processing loop."""
    shredder = get_shredder()
    await shredder.start_loop()
    return {"status": "started"}


@router.post("/stop")
async def stop_shredder():
    """Stop the background processing loop."""
    shredder = get_shredder()
    await shredder.stop_loop()
    return {"status": "stopped"}


@router.get("/status")
async def shredder_status():
    """Get shredder running status."""
    shredder = get_shredder()
    stats = await shredder.queue.get_stats()
    return {
        "running": shredder._running,
        "stats": stats.model_dump(),
    }


@router.post("/items/{item_id}/retry")
async def retry_item(item_id: str):
    """Reset a failed item back to queued for re-processing."""
    shredder = get_shredder()
    item = await shredder.retry_item(item_id)
    if not item:
        raise HTTPException(
            status_code=400,
            detail="Item not found or not in FAILED status"
        )
    return {"retried": True, "item_id": item_id, "status": item.status.value}


@router.post("/retry-all-failed")
async def retry_all_failed():
    """Reset ALL failed items back to queued."""
    shredder = get_shredder()
    count = await shredder.retry_all_failed()
    return {"retried": count, "message": f"{count} failed item(s) reset to queued"}


# ---------------------------------------------------------------------------
# Build Rules CRUD
# ---------------------------------------------------------------------------

class CreateRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=1)
    category: str = Field(default="custom")
    enabled: bool = True
    order: int = 0


class UpdateRuleRequest(BaseModel):
    name: Optional[str] = None
    text: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None
    order: Optional[int] = None


@router.get("/rules")
async def list_rules(category: Optional[str] = None):
    """List all build rules, optionally filtered by category."""
    shredder = get_shredder()
    if category:
        from ..models.prd_shredder import RuleCategory
        try:
            cat = RuleCategory(category)
            rules = shredder.rules.list_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        rules = shredder.rules.list_all()
    return {"rules": [r.model_dump() for r in rules], "count": len(rules)}


@router.post("/rules")
async def create_rule(body: CreateRuleRequest):
    """Create a new build rule."""
    from ..models.prd_shredder import BuildRule, RuleCategory
    try:
        cat = RuleCategory(body.category)
    except ValueError:
        cat = RuleCategory.CUSTOM
    rule = BuildRule(name=body.name, text=body.text, category=cat, enabled=body.enabled, order=body.order)
    shredder = get_shredder()
    created = shredder.rules.add(rule)
    return created.model_dump()


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, body: UpdateRuleRequest):
    """Update an existing build rule."""
    shredder = get_shredder()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "category" in updates:
        from ..models.prd_shredder import RuleCategory
        try:
            updates["category"] = RuleCategory(updates["category"])
        except ValueError:
            updates["category"] = RuleCategory.CUSTOM
    rule = shredder.rules.update(rule_id, **updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a build rule."""
    shredder = get_shredder()
    if not shredder.rules.delete(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"deleted": True}


@router.patch("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str):
    """Toggle the enabled state of a build rule."""
    shredder = get_shredder()
    rule = shredder.rules.toggle(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


# ---------------------------------------------------------------------------
# Shredder Config
# ---------------------------------------------------------------------------

class ConfigUpdate(BaseModel):
    github_token: Optional[str] = None
    default_branch: Optional[str] = None


@router.get("/config")
async def get_config():
    """Get shredder configuration (GitHub token is masked)."""
    shredder = get_shredder()
    config = shredder.config.get()
    masked = config.model_dump()
    if masked["github_token"]:
        token = masked["github_token"]
        masked["github_token_masked"] = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
    return masked


@router.put("/config")
async def update_config(body: ConfigUpdate):
    """Update shredder configuration."""
    shredder = get_shredder()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    config = shredder.config.update(**updates)
    masked = config.model_dump()
    if masked["github_token"]:
        token = masked["github_token"]
        masked["github_token_masked"] = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
    return masked
