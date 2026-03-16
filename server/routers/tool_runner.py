"""Tool Runner Router — REST + WebSocket endpoints for the Hybrid Execution Engine.

Endpoints:
  POST /api/tool-runner/{tool_id}/run          — Start a run, stream events via SSE
  GET  /api/tool-runner/{tool_id}/runs         — List runs for a tool
  GET  /api/tool-runner/runs/{run_id}          — Get run state
  POST /api/tool-runner/runs/{run_id}/cancel   — Cancel a run
  WS   /api/tool-runner/{tool_id}/ws           — WebSocket stream of run events
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models.tool_factory import GeneratedTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tool-runner", tags=["tool-runner"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class StartRunRequest(BaseModel):
    variables: dict[str, str] = {}
    start_from_step: int = 1
    stop_after_step: Optional[int] = None


class StartRunResponse(BaseModel):
    run_id: str
    tool_id: str
    tool_name: str
    total_steps: int


# ---------------------------------------------------------------------------
# Helper: load tool from registry
# ---------------------------------------------------------------------------

def _get_tool(tool_id: str) -> "GeneratedTool":
    from ..services.tool_registry import load_tool_registry

    registry = load_tool_registry()
    for tool in registry.tools:
        if tool.tool_id == tool_id:
            return tool
    raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")


# ---------------------------------------------------------------------------
# POST /api/tool-runner/{tool_id}/run  — SSE streaming run
# ---------------------------------------------------------------------------

@router.post("/{tool_id}/run")
async def start_run_stream(tool_id: str, body: StartRunRequest) -> StreamingResponse:
    """Start executing a tool chain and stream progress events via SSE."""
    from ..models.tool_factory import RunConfig
    from ..services.tool_runner import ToolRunner

    tool = _get_tool(tool_id)

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    config = RunConfig(
        run_id=run_id,
        tool_id=tool_id,
        variables=body.variables,
        start_from_step=body.start_from_step,
        stop_after_step=body.stop_after_step,
    )

    runner = ToolRunner(tool=tool, config=config)

    async def event_stream():
        try:
            async for event in runner.run():
                data = json.dumps(event)
                yield f"data: {data}\n\n"
        except Exception as exc:
            err = json.dumps({"type": "run_error", "run_id": run_id, "error": str(exc)})
            yield f"data: {err}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/tool-runner/{tool_id}/runs  — list runs for tool
# ---------------------------------------------------------------------------

@router.get("/{tool_id}/runs")
async def list_runs(tool_id: str) -> dict:
    from ..services.tool_runner import get_runs_for_tool

    runs = get_runs_for_tool(tool_id)
    return {
        "tool_id": tool_id,
        "runs": [r.model_dump() for r in runs],
        "count": len(runs),
    }


# ---------------------------------------------------------------------------
# GET /api/tool-runner/runs/{run_id}  — get run state
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    from ..services.tool_runner import get_run

    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return state.model_dump()


# ---------------------------------------------------------------------------
# POST /api/tool-runner/runs/{run_id}/cancel  — cancel a run
# ---------------------------------------------------------------------------

@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str) -> dict:
    from ..services.tool_runner import cancel_run

    success = cancel_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found or not cancellable")
    return {"run_id": run_id, "status": "cancelled"}


# ---------------------------------------------------------------------------
# WebSocket /api/tool-runner/{tool_id}/ws  — WebSocket run stream
# ---------------------------------------------------------------------------

@router.websocket("/{tool_id}/ws")
async def run_websocket(websocket: WebSocket, tool_id: str) -> None:
    """WebSocket endpoint: client sends StartRunRequest JSON, receives run events."""
    from ..models.tool_factory import RunConfig
    from ..services.tool_runner import ToolRunner

    await websocket.accept()
    try:
        # Wait for the start message
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=30)
        body_data = json.loads(raw)

        variables = body_data.get("variables", {})
        start_from_step = body_data.get("start_from_step", 1)
        stop_after_step = body_data.get("stop_after_step")

        tool = _get_tool(tool_id)

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        config = RunConfig(
            run_id=run_id,
            tool_id=tool_id,
            variables=variables,
            start_from_step=start_from_step,
            stop_after_step=stop_after_step,
        )

        runner = ToolRunner(tool=tool, config=config)

        async for event in runner.run():
            await websocket.send_json(event)

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("Tool runner WebSocket disconnected: tool_id=%s", tool_id)
    except Exception as exc:
        logger.error("Tool runner WebSocket error: %s", exc, exc_info=True)
        try:
            await websocket.send_json({"type": "run_error", "error": str(exc)})
            await websocket.close()
        except Exception:
            pass
