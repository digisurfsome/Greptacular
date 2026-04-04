"""
Pipeline Router
===============

REST endpoints for managing skill pipelines — sequential execution of
skill prompts where output from stage N feeds into stage N+1.
"""

import asyncio
import io
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# ============================================================================
# Pydantic Models
# ============================================================================

class PipelineStageConfig(BaseModel):
    """Configuration for a single stage in the skill pipeline."""
    label: str
    skill_text: str


class PipelineStartRequest(BaseModel):
    """Request body for starting a skill pipeline."""
    working_directory: str
    kickoff_message: str
    token_budget: int = 400_000
    model: str = "opus"
    stages: list[PipelineStageConfig]


class PipelineStopRequest(BaseModel):
    """Request body for stopping a skill pipeline."""
    pipeline_id: str


class PipelineAnswerRequest(BaseModel):
    """Request body for answering a pipeline question or sending a message."""
    pipeline_id: str
    answer: str


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/start")
async def start_pipeline(body: PipelineStartRequest):
    """Create and start a new skill pipeline.

    Returns the pipeline ID and initial status.  The pipeline runs
    asynchronously; poll ``/status/{pipeline_id}`` for progress.
    """
    from ..services.pipeline_orchestrator import create_pipeline

    if not body.stages:
        raise HTTPException(status_code=400, detail="At least one stage is required")

    if not body.kickoff_message.strip():
        raise HTTPException(status_code=400, detail="kickoff_message must not be empty")

    pipeline = await create_pipeline(
        working_directory=body.working_directory,
        stages=[s.model_dump() for s in body.stages],
        kickoff_message=body.kickoff_message,
        token_budget=body.token_budget,
        model=body.model,
    )

    # Run the pipeline in the background so the POST returns immediately
    async def _run_pipeline():
        try:
            async for _event in pipeline.run():
                pass  # Events are consumed; status is tracked internally
        except Exception as e:
            logger.exception("Background pipeline %s failed: %s", pipeline.pipeline_id, e)

    asyncio.create_task(_run_pipeline())

    return {
        "pipeline_id": pipeline.pipeline_id,
        "status": pipeline.status.value,
    }


@router.post("/stop")
async def stop_pipeline(body: PipelineStopRequest):
    """Stop a running skill pipeline."""
    from ..services.pipeline_orchestrator import get_pipeline

    pipeline = get_pipeline(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    await pipeline.stop()
    return {"success": True, "message": f"Pipeline {body.pipeline_id} stopped"}


@router.post("/answer")
async def answer_pipeline(body: PipelineAnswerRequest):
    """Send an answer or message to a running pipeline stage.

    If the pipeline is waiting for user input (agent asked a question),
    this delivers the answer and resumes execution.  Otherwise it acts
    as a walkie-talkie message injected into the running stage.
    """
    from ..services.pipeline_orchestrator import get_pipeline

    pipeline = get_pipeline(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not body.answer.strip():
        raise HTTPException(status_code=400, detail="Answer must not be empty")

    await pipeline.inject_answer(body.answer.strip())
    return {"success": True}


@router.get("/status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    """Get the current status of a skill pipeline.

    Checks in-memory pipelines first, then falls back to the database
    for completed/historical runs.
    """
    from ..services.pipeline_orchestrator import get_pipeline

    # Try in-memory first
    pipeline = get_pipeline(pipeline_id)
    if pipeline:
        return pipeline.get_status()

    # Fall back to database for historical runs
    from ..services.workspace_database import get_pipeline_run, get_pipeline_stage_outputs

    run = get_pipeline_run(pipeline_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    stage_outputs = get_pipeline_stage_outputs(pipeline_id)
    run["stages"] = stage_outputs
    return run


@router.get("/history")
async def get_pipeline_history():
    """List all pipeline runs (most recent first)."""
    from ..services.workspace_database import list_pipeline_runs
    return list_pipeline_runs(limit=50)


@router.get("/export/{pipeline_id}")
async def export_pipeline(pipeline_id: str):
    """Export the combined output of a pipeline as a downloadable Markdown file."""
    from ..services.pipeline_orchestrator import get_pipeline

    # Try in-memory first
    pipeline = get_pipeline(pipeline_id)
    if pipeline:
        content = pipeline.get_combined_output()
    else:
        # Fall back to database
        from ..services.workspace_database import get_pipeline_run, get_pipeline_stage_outputs

        run = get_pipeline_run(pipeline_id)
        if not run:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        stage_outputs = get_pipeline_stage_outputs(pipeline_id)

        # Reconstruct the combined output from database records
        parts = [f"# Skill Pipeline Output — {pipeline_id}\n"]
        parts.append(f"**Model:** {run.get('model', 'unknown')}  ")
        parts.append(f"**Total Duration:** {run.get('total_duration', 0)}s  ")
        parts.append(f"**Total Tokens:** {run.get('total_tokens', 0)}\n")

        for stage in stage_outputs:
            idx = stage.get("stage_index", 0)
            label = stage.get("label", f"Stage {idx}")
            parts.append(f"\n---\n\n## Stage {idx}: {label}\n")
            status = stage.get("status", "unknown")
            if status == "completed":
                parts.append(
                    f"*Duration: {stage.get('duration_seconds', 0)}s "
                    f"| Tokens: {stage.get('tokens_used', 0)}*\n"
                )
                parts.append(stage.get("output_text", ""))
            elif status == "failed":
                parts.append(f"**FAILED:** {stage.get('error', 'Unknown error')}\n")
            else:
                parts.append(f"*Status: {status}*\n")

        content = "\n".join(parts)

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=pipeline-{pipeline_id}-output.md"},
    )
