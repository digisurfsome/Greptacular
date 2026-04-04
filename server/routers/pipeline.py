"""
Pipeline Router
===============

REST endpoints for managing skill pipelines — sequential execution of
skill prompts where output from stage N feeds into stage N+1.

Also provides CRUD for pipeline projects (saved, reusable prompt chain
configurations) and a folder-loading utility for discovering SKILL.md files.
"""

import asyncio
import io
import logging
import re
from pathlib import Path
from typing import Optional

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
    output_mode: str = "json"
    stages: list[PipelineStageConfig]


class PipelineStopRequest(BaseModel):
    """Request body for stopping a skill pipeline."""
    pipeline_id: str


class PipelineAnswerRequest(BaseModel):
    """Request body for answering a pipeline question or sending a message."""
    pipeline_id: str
    answer: str


class PipelineProjectCreate(BaseModel):
    """Request body for creating a pipeline project."""
    name: str
    description: Optional[str] = None
    output_mode: str = "json"
    default_model: str = "opus"
    default_token_budget: int = 400_000
    stages: list[PipelineStageConfig]


class PipelineProjectUpdate(BaseModel):
    """Request body for updating a pipeline project."""
    name: Optional[str] = None
    description: Optional[str] = None
    output_mode: Optional[str] = None
    default_model: Optional[str] = None
    default_token_budget: Optional[int] = None
    stages: Optional[list[PipelineStageConfig]] = None


class PipelineProjectClone(BaseModel):
    """Request body for cloning a pipeline project."""
    new_name: str


class FolderLoadRequest(BaseModel):
    """Request body for loading SKILL.md files from a folder."""
    folder_path: str


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
        output_mode=body.output_mode,
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


@router.post("/force-advance")
async def force_advance_pipeline(body: PipelineStopRequest):
    """Force-advance the pipeline to the next stage.

    Closes the current session, marks the running stage as completed
    with whatever output has been collected, and lets the pipeline
    continue to the next stage.
    """
    from ..services.pipeline_orchestrator import get_pipeline

    pipeline = get_pipeline(body.pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    result = await pipeline.force_advance()
    return result


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


# ============================================================================
# Pipeline Project Endpoints
# ============================================================================

@router.post("/projects")
async def create_project(body: PipelineProjectCreate):
    """Create a new pipeline project (saved prompt chain configuration)."""
    import json

    from ..services.workspace_database import save_pipeline_project

    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Project name must not be empty")
    if not body.stages:
        raise HTTPException(status_code=400, detail="At least one stage is required")

    stages_json = json.dumps([s.model_dump() for s in body.stages])
    project = save_pipeline_project(
        name=body.name.strip(),
        stages_json=stages_json,
        description=body.description,
        output_mode=body.output_mode,
        default_model=body.default_model,
        default_token_budget=body.default_token_budget,
    )
    return project


@router.get("/projects")
async def list_projects():
    """List all saved pipeline projects."""
    from ..services.workspace_database import list_pipeline_projects
    return list_pipeline_projects()


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a pipeline project by ID."""
    from ..services.workspace_database import get_pipeline_project

    project = get_pipeline_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Pipeline project not found")
    return project


@router.patch("/projects/{project_id}")
async def update_project(project_id: int, body: PipelineProjectUpdate):
    """Update a pipeline project."""
    import json

    from ..services.workspace_database import update_pipeline_project

    kwargs: dict = {}
    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=400, detail="Project name must not be empty")
        kwargs["name"] = body.name.strip()
    if body.description is not None:
        kwargs["description"] = body.description
    if body.output_mode is not None:
        kwargs["output_mode"] = body.output_mode
    if body.default_model is not None:
        kwargs["default_model"] = body.default_model
    if body.default_token_budget is not None:
        kwargs["default_token_budget"] = body.default_token_budget
    if body.stages is not None:
        if not body.stages:
            raise HTTPException(status_code=400, detail="At least one stage is required")
        kwargs["stages_json"] = json.dumps([s.model_dump() for s in body.stages])

    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = update_pipeline_project(project_id, **kwargs)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline project not found")
    return result


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a pipeline project."""
    from ..services.workspace_database import delete_pipeline_project

    deleted = delete_pipeline_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pipeline project not found")
    return {"success": True, "message": f"Pipeline project {project_id} deleted"}


@router.post("/projects/{project_id}/clone")
async def clone_project(project_id: int, body: PipelineProjectClone):
    """Clone a pipeline project with a new name."""
    from ..services.workspace_database import clone_pipeline_project

    if not body.new_name.strip():
        raise HTTPException(status_code=400, detail="New name must not be empty")

    result = clone_pipeline_project(project_id, body.new_name.strip())
    if not result:
        raise HTTPException(status_code=404, detail="Source pipeline project not found")
    return result


# ============================================================================
# Folder Loading
# ============================================================================

def _extract_label_from_markdown(content: str, fallback: str) -> str:
    """Extract the label from the first ``# heading`` in a Markdown file.

    Falls back to *fallback* if no heading is found.
    """
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


@router.post("/load-folder")
async def load_folder(body: FolderLoadRequest):
    """Load SKILL.md files from subdirectories of the given folder.

    Returns an array of ``{label, skill_text}`` objects, one per
    subdirectory that contains a ``SKILL.md`` file.  Subdirectories
    are sorted alphabetically.

    Security:
    - Path must be absolute.
    - Path must exist and be a directory.
    - Only reads ``.md`` files (specifically ``SKILL.md``).
    """
    folder = Path(body.folder_path)

    if not folder.is_absolute():
        raise HTTPException(status_code=400, detail="folder_path must be an absolute path")
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {body.folder_path}")
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {body.folder_path}")

    stages: list[dict] = []
    subdirs = sorted([d for d in folder.iterdir() if d.is_dir()])

    for subdir in subdirs:
        # Prefer SKILL-COMPLETE.md (has all references baked in), fall back to SKILL.md
        skill_file = subdir / "SKILL-COMPLETE.md"
        if not skill_file.is_file():
            skill_file = subdir / "SKILL.md"
        if not skill_file.is_file():
            continue
        try:
            content = skill_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to read %s: %s", skill_file, e)
            continue

        label = _extract_label_from_markdown(content, fallback=subdir.name)
        stages.append({"label": label, "skill_text": content})

    logger.info("Loaded %d SKILL.md files from %s", len(stages), body.folder_path)
    return stages
