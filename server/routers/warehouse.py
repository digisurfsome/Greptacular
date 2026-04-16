"""
Warehouse Router — Tool Page Loading and Execution Submission
===============================================================

REST endpoints for the tool warehouse UI.
Loads tool blueprints, validates inputs, and dispatches executions.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/warehouse", tags=["warehouse"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class ExecuteRequest(BaseModel):
    tool_id: str = Field(..., min_length=1)
    inputs: dict = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/tools/{tool_id}")
async def load_tool_page(tool_id: str):
    """Load a tool's blueprint and input schema."""
    from ..services.warehouse_service import load_tool_blueprint
    try:
        result = await load_tool_blueprint(tool_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error loading tool %s", tool_id)
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.post("/execute")
async def submit_execution(body: ExecuteRequest):
    """Submit a tool for execution with validated inputs."""
    from ..services.warehouse_service import (
        dispatch_execution,
        load_tool_blueprint,
        validate_inputs,
    )
    try:
        # Load blueprint to get schema
        blueprint = await load_tool_blueprint(body.tool_id)
        if not blueprint:
            raise HTTPException(status_code=404, detail=f"Tool {body.tool_id} not found")

        # Validate inputs
        valid, err = await validate_inputs(blueprint.get("input_schema", []), body.inputs)
        if not valid:
            raise HTTPException(status_code=422, detail=err)

        # Dispatch execution
        result = await dispatch_execution(body.tool_id, body.inputs)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error executing tool %s", body.tool_id)
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")


@router.get("/tools/{tool_id}/history")
async def get_execution_history(tool_id: str, limit: int = 20):
    """Get execution history for a tool."""
    from ..services.warehouse_service import get_execution_history
    try:
        return await get_execution_history(tool_id, limit)
    except Exception as exc:
        logger.exception("Error getting execution history for %s", tool_id)
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
