"""Tool Analyzer Router — readiness checks and gap analysis for tool steps.

Endpoints:
  POST /api/tool-analyzer/quick-check   — fast keyword-based readiness check
  POST /api/tool-analyzer/gap-analysis   — full analysis with build plans
  GET  /api/tool-analyzer/components     — list all components with status
  POST /api/tool-analyzer/generate-prd/{name} — generate mini-PRD for a component
  GET  /api/tool-analyzer/coverage       — global coverage stats
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.component_registry import get_component_registry
from ..services.tool_analyzer import (
    gap_analysis,
    get_coverage_stats,
    quick_check,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tool-analyzer", tags=["tool-analyzer"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AnalyzerRequest(BaseModel):
    """Request body for quick-check and gap-analysis endpoints."""
    steps: list[dict] = Field(..., min_length=1)
    tool_name: str = Field(default="")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/quick-check")
async def run_quick_check(body: AnalyzerRequest):
    """Fast keyword-based readiness check against the component registry."""
    try:
        result = quick_check(steps=body.steps, tool_name=body.tool_name)
        return result.model_dump(by_alias=True)
    except Exception as e:
        logger.exception("Quick check failed")
        raise HTTPException(status_code=500, detail=f"Quick check failed: {e}")


@router.post("/gap-analysis")
async def run_gap_analysis(body: AnalyzerRequest):
    """Full gap analysis with build plans for missing components."""
    try:
        result = gap_analysis(steps=body.steps, tool_name=body.tool_name)
        return result.model_dump(by_alias=True)
    except Exception as e:
        logger.exception("Gap analysis failed")
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {e}")


@router.get("/components")
async def list_components():
    """List all components with their current status."""
    registry = get_component_registry()
    components = registry.get_all()
    return {"components": [c.model_dump() for c in components]}


@router.post("/generate-prd/{component_name}")
async def generate_prd(component_name: str):
    """Generate a mini-PRD for building a missing component."""
    registry = get_component_registry()
    comp = registry.get_by_name(component_name)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component not found: {component_name}")

    # Generate a simple PRD template (no AI call needed for this)
    prd = f"""# Mini-PRD: {comp.name}

## Overview
{comp.description}

## Current Status
**{comp.status.value}** — {comp.status_detail}

## Requirements
{chr(10).join(f'- {r}' for r in comp.requirements)}

## Handles (Keywords)
{', '.join(comp.handles)}

## Implementation Plan

### What to Build
A service module that integrates {comp.name} into the tool execution engine,
allowing tool steps that require this component to execute automatically.

### Files to Create/Modify
- `server/services/{comp.name}_executor.py` — Main service module
- `server/routers/tool_analyzer.py` — Update component status after build
- Tests for the new service

### Integration Points
- Tool execution engine step handler
- Component registry status update

### Acceptance Criteria
1. Component status changes to "available" after configuration
2. Tool steps matching [{', '.join(comp.handles[:5])}] execute successfully
3. Error handling for missing credentials or API failures
4. Logging for all external API calls
"""

    return {"component_name": component_name, "prd": prd}


@router.get("/coverage")
async def coverage_stats():
    """Global coverage statistics."""
    return get_coverage_stats()


@router.post("/refresh")
async def refresh_components():
    """Re-detect component availability."""
    registry = get_component_registry()
    registry.refresh()
    return {"status": "refreshed", "components": [c.model_dump() for c in registry.get_all()]}


# ---------------------------------------------------------------------------
# Gap Dashboard + Build Specs (tool analyzer flywheel)
# ---------------------------------------------------------------------------


@router.get("/gaps")
async def get_gaps():
    """Get all detected capability gaps for the dashboard."""
    from ..services.tool_analyzer_service import get_gap_dashboard_data
    try:
        return await get_gap_dashboard_data()
    except Exception as e:
        logger.exception("Failed to get gap dashboard data")
        raise HTTPException(status_code=500, detail=f"Failed: {e}")


@router.get("/build-specs")
async def get_build_specs():
    """List all generated build specs."""
    from ..services.tool_analyzer_service import list_build_specs
    try:
        return await list_build_specs()
    except Exception as e:
        logger.exception("Failed to list build specs")
        raise HTTPException(status_code=500, detail=f"Failed: {e}")


@router.post("/build-specs/{gap_id}")
async def create_build_spec(gap_id: int):
    """Generate a build spec for a specific gap."""
    from ..services.tool_analyzer_service import generate_build_spec
    try:
        return await generate_build_spec(gap_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as e:
        logger.exception("Failed to generate build spec for gap %d", gap_id)
        raise HTTPException(status_code=500, detail=f"Failed: {e}")
