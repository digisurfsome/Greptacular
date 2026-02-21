"""
Swarm Router
============

REST and WebSocket endpoints for managing swarm pipelines — concurrent
autonomous agent teams that share files and auto-hand off work.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/swarm", tags=["swarm"])


# ============================================================================
# Pydantic Models
# ============================================================================

class SwarmStageConfig(BaseModel):
    """Configuration for a single stage in the swarm pipeline."""
    name: str
    label: str
    model: str = "opus"
    context_mode: str = "1m"
    initial_prompt: str
    output_file: str
    trigger_file: Optional[str] = None


class SwarmStartRequest(BaseModel):
    """Request body for starting a swarm pipeline."""
    working_directory: str
    task_description: Optional[str] = None  # Used with default pipeline
    stages: Optional[list[SwarmStageConfig]] = None  # Custom pipeline
    research_model: str = "sonnet"
    prd_model: str = "opus"
    coder_model: str = "sonnet"


class SwarmInjectRequest(BaseModel):
    """Request body for injecting a message into a swarm stage."""
    stage_name: str
    content: str


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/pipelines")
async def list_pipelines():
    """List all active swarm pipelines."""
    from ..services.swarm_orchestrator import list_swarms
    return await list_swarms()


@router.post("/start")
async def start_swarm(body: SwarmStartRequest):
    """Start a new swarm pipeline.

    If `stages` is provided, uses the custom pipeline definition.
    Otherwise, builds the default Research → PRD → Coder pipeline
    using `task_description`.
    """
    from ..services.swarm_orchestrator import (
        build_default_pipeline_stages,
        create_swarm,
    )

    if body.stages:
        # Custom pipeline
        stages = [s.model_dump() for s in body.stages]
    elif body.task_description:
        # Default 3-stage pipeline
        stages = build_default_pipeline_stages(
            task_description=body.task_description,
            research_model=body.research_model,
            prd_model=body.prd_model,
            coder_model=body.coder_model,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'task_description' or 'stages' must be provided",
        )

    pipeline = await create_swarm(
        working_directory=body.working_directory,
        stages=stages,
    )

    return {
        "swarm_id": pipeline.swarm_id,
        "status": pipeline.status.value,
        "shared_dir": str(pipeline.shared_dir),
        "stages": [s.name for s in pipeline.stages],
    }


@router.get("/{swarm_id}/status")
async def get_swarm_status(swarm_id: str):
    """Get the current status of a swarm pipeline."""
    from ..services.swarm_orchestrator import get_swarm

    pipeline = await get_swarm(swarm_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Swarm not found")

    return pipeline.get_status()


@router.post("/{swarm_id}/stop")
async def stop_swarm_endpoint(swarm_id: str):
    """Stop a running swarm pipeline."""
    from ..services.swarm_orchestrator import stop_swarm

    success = await stop_swarm(swarm_id)
    if not success:
        raise HTTPException(status_code=404, detail="Swarm not found")

    return {"success": True, "message": f"Swarm {swarm_id} stopped"}


@router.get("/{swarm_id}/files")
async def list_shared_files(swarm_id: str):
    """List files in the swarm's shared workspace."""
    from ..services.swarm_orchestrator import get_swarm

    pipeline = await get_swarm(swarm_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Swarm not found")

    return pipeline._list_shared_files()


@router.get("/{swarm_id}/files/{filename}")
async def read_shared_file(swarm_id: str, filename: str):
    """Read a file from the swarm's shared workspace."""
    from ..services.swarm_orchestrator import get_swarm

    pipeline = await get_swarm(swarm_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Swarm not found")

    content = pipeline.read_shared_file(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    return {"filename": filename, "content": content}


@router.post("/{swarm_id}/inject")
async def inject_message(swarm_id: str, body: SwarmInjectRequest):
    """Inject a walkie-talkie message into a running swarm stage."""
    from ..services.swarm_orchestrator import get_swarm

    pipeline = await get_swarm(swarm_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Swarm not found")

    success = await pipeline.inject_message(body.stage_name, body.content)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Stage '{body.stage_name}' is not running or walkie-talkie is disabled",
        )

    return {"success": True, "stage": body.stage_name}


# ============================================================================
# WebSocket Endpoint - Real-time Swarm Events
# ============================================================================

@router.websocket("/ws/{swarm_id}")
async def swarm_websocket(websocket: WebSocket, swarm_id: str):
    """WebSocket endpoint for real-time swarm pipeline events.

    Client -> Server:
    - {"type": "start"} - Begin running the pipeline (after POST /start created it)
    - {"type": "inject", "stage_name": "...", "content": "..."} - Inject message
    - {"type": "ping"} - Keep-alive

    Server -> Client:
    - {"type": "swarm_stage_started", "stage": "...", "data": {...}}
    - {"type": "swarm_stage_completed", "stage": "...", "data": {...}}
    - {"type": "swarm_file_created", "stage": "...", "data": {...}}
    - {"type": "swarm_handoff", "stage": "...", "data": {...}}
    - {"type": "swarm_status_change", "data": {...}}
    - {"type": "swarm_error", "data": {...}}
    - {"type": "pong"}
    """
    await websocket.accept()
    logger.info("Swarm WebSocket connected for %s", swarm_id)

    from ..services.swarm_orchestrator import get_swarm

    pipeline = await get_swarm(swarm_id)
    if not pipeline:
        await websocket.send_json({"type": "error", "content": f"Swarm '{swarm_id}' not found"})
        await websocket.close()
        return

    # Background task to stream events from the pipeline
    event_stream_task: Optional[asyncio.Task] = None

    async def stream_events():
        """Stream pipeline events to the WebSocket."""
        try:
            async for event in pipeline.run():
                try:
                    await websocket.send_json(event.to_dict())
                except Exception:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception("Event stream error: %s", e)
            try:
                await websocket.send_json({"type": "error", "content": str(e)})
            except Exception:
                pass

    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "start":
                    if event_stream_task and not event_stream_task.done():
                        await websocket.send_json({
                            "type": "error",
                            "content": "Pipeline is already running",
                        })
                    else:
                        # Send initial status
                        await websocket.send_json({
                            "type": "swarm_status_change",
                            "data": {"status": "starting"},
                            "stage": None,
                            "timestamp": None,
                        })
                        event_stream_task = asyncio.create_task(stream_events())

                elif msg_type == "inject":
                    stage = msg.get("stage_name", "")
                    content = msg.get("content", "")
                    if stage and content:
                        success = await pipeline.inject_message(stage, content)
                        await websocket.send_json({
                            "type": "inject_result",
                            "success": success,
                            "stage": stage,
                        })

                elif msg_type == "stop":
                    await pipeline.stop()
                    if event_stream_task and not event_stream_task.done():
                        event_stream_task.cancel()
                    await websocket.send_json({
                        "type": "swarm_status_change",
                        "data": {"status": "stopped"},
                        "stage": None,
                        "timestamp": None,
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {msg_type}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})

    except WebSocketDisconnect:
        logger.info("Swarm WebSocket disconnected for %s", swarm_id)
    except Exception:
        logger.exception("Swarm WebSocket error for %s", swarm_id)
    finally:
        if event_stream_task and not event_stream_task.done():
            event_stream_task.cancel()
            try:
                await event_stream_task
            except asyncio.CancelledError:
                pass
