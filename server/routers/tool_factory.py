"""Tool Factory Router — REST endpoints for tool registry + blueprint generation.

Phase 1: Registry CRUD (all [ROBOT])
Phase 2: Blueprint generation + PRD upload (mixed [ROBOT]/[AGENT])
"""

import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.tool_factory import IngestionSource, ToolStatus
from ..services.tool_registry import ToolRegistryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tool-factory", tags=["tool-factory"])

# Shared registry instance
_registry = ToolRegistryService()


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class GenerateBlueprintRequest(BaseModel):
    """Request to generate a blueprint from YT Lab project data."""
    project_name: str = Field(..., min_length=1, max_length=200)
    project_description: str = Field(default="")
    steps: list[dict] = Field(..., min_length=1)
    source_video_id: str = Field(default="")
    source_video_title: str = Field(default="")
    source_video_channel: str = Field(default="")
    source_project_id: str = Field(default="")
    skip_prompt_conversion: bool = Field(default=False)


class PRDUploadRequest(BaseModel):
    """Request body for paste-in PRD upload."""
    content: str = Field(..., min_length=50)
    filename: str = Field(default="pasted_prd.md")
    user_context: str = Field(default="")


# ---------------------------------------------------------------------------
# Phase 1: Registry Endpoints [ROBOT]
# ---------------------------------------------------------------------------

@router.get("/tools")
async def list_tools(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List tools, optionally filtered by status."""
    tool_status = None
    if status:
        try:
            tool_status = ToolStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    tools = await _registry.list_tools(status=tool_status, limit=limit, offset=offset)
    return {"tools": [t.model_dump() for t in tools], "count": len(tools)}


@router.get("/stats")
async def get_stats():
    """Aggregate statistics."""
    return await _registry.get_stats()


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get a single tool by ID."""
    tool = await _registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    return tool.model_dump()


@router.delete("/tools/{tool_id}")
async def archive_tool(tool_id: str):
    """Archive (soft-delete) a tool."""
    tool = await _registry.archive_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    return {"status": "archived", "tool_id": tool_id}


# ---------------------------------------------------------------------------
# Phase 2: Blueprint Generation Endpoints [MIXED]
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate_blueprint(body: GenerateBlueprintRequest):
    """Generate blueprint from steps (sync — waits for completion)."""
    from ..services.sheet_blueprint import generate_blueprint as _generate

    try:
        blueprint = await _generate(
            project_name=body.project_name,
            project_description=body.project_description,
            steps=body.steps,
            source_video_id=body.source_video_id,
            source_video_title=body.source_video_title,
            source_video_channel=body.source_video_channel,
            source_project_id=body.source_project_id,
            skip_prompt_conversion=body.skip_prompt_conversion,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Blueprint generation failed")
        raise HTTPException(status_code=500, detail=f"Blueprint generation failed: {e}")

    # Auto-register in tool registry
    tool = await _registry.create_tool(blueprint)

    return {
        "blueprint": blueprint.model_dump(),
        "tool_id": tool.tool_id,
    }


@router.post("/generate-stream")
async def generate_blueprint_stream(body: GenerateBlueprintRequest):
    """Generate blueprint with SSE progress events."""
    from ..services.sheet_blueprint import generate_blueprint as _generate

    queue: asyncio.Queue = asyncio.Queue()
    start_time = time.time()

    def on_progress(message: str) -> None:
        elapsed = round(time.time() - start_time, 1)
        queue.put_nowait({"type": "log", "message": message, "elapsed": elapsed})

    async def run_generation() -> None:
        try:
            blueprint = await _generate(
                project_name=body.project_name,
                project_description=body.project_description,
                steps=body.steps,
                source_video_id=body.source_video_id,
                source_video_title=body.source_video_title,
                source_video_channel=body.source_video_channel,
                source_project_id=body.source_project_id,
                skip_prompt_conversion=body.skip_prompt_conversion,
                on_progress=on_progress,
            )
            tool = await _registry.create_tool(blueprint)
            elapsed = round(time.time() - start_time, 1)
            queue.put_nowait({
                "type": "result",
                "data": {"blueprint": blueprint.model_dump(), "tool_id": tool.tool_id},
                "elapsed": elapsed,
            })
        except Exception as exc:
            elapsed = round(time.time() - start_time, 1)
            queue.put_nowait({"type": "error", "message": str(exc), "elapsed": elapsed})
        finally:
            queue.put_nowait(None)

    asyncio.create_task(run_generation())

    async def event_generator():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/generate-from-prd")
async def generate_from_prd(body: PRDUploadRequest):
    """Generate blueprint from a PRD document (paste-in)."""
    from ..services.prd_ingestion import extract_steps_from_prd, save_prd_upload
    from ..services.sheet_blueprint import generate_blueprint as _generate

    try:
        # Save the PRD
        prd = save_prd_upload(body.filename, body.content)

        # Extract steps via Claude
        extraction = await extract_steps_from_prd(body.content, body.user_context)

        # Generate blueprint from extracted steps
        blueprint = await _generate(
            project_name=extraction.project_name,
            project_description=extraction.project_description,
            steps=extraction.steps,
            ingestion_source=IngestionSource.PRD_UPLOAD,
            source_prd_id=prd.prd_id,
            skip_prompt_conversion=False,
        )

        tool = await _registry.create_tool(blueprint)

        return {
            "prd_id": prd.prd_id,
            "extraction": extraction.model_dump(),
            "blueprint": blueprint.model_dump(),
            "tool_id": tool.tool_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("PRD blueprint generation failed")
        raise HTTPException(status_code=500, detail=f"PRD processing failed: {e}")


# ---------------------------------------------------------------------------
# Phase 4: Google Auth + Deploy Endpoints [ROBOT]
# ---------------------------------------------------------------------------

@router.get("/google/auth-url")
async def google_auth_url():
    """Get OAuth URL for Google authorization. [ROBOT]"""
    from ..services.google_auth import start_oauth_flow

    try:
        url = start_oauth_flow()
        return {"auth_url": url}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/google/callback")
async def google_callback(body: dict):
    """Handle OAuth callback with authorization code. [ROBOT]"""
    from ..services.google_auth import handle_oauth_callback

    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")

    success = handle_oauth_callback(code)
    if not success:
        raise HTTPException(status_code=500, detail="OAuth token exchange failed")

    return {"status": "authenticated"}


@router.get("/google/status")
async def google_status():
    """Check if Google OAuth is authenticated. [ROBOT]"""
    from ..services.google_auth import is_authenticated

    return {"authenticated": is_authenticated()}


@router.post("/deploy/{tool_id}")
async def deploy_tool(tool_id: str, body: dict = None):
    """Deploy blueprint as Google Sheet. [ROBOT]"""
    from ..models.tool_factory import ToolStatus
    from ..services.google_auth import get_credentials
    from ..services.sheet_deployer import deploy_sheet
    from ..services.sheet_theme_engine import preset_theme_to_theme_config

    body = body or {}

    tool = await _registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    creds = get_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated with Google. Call /google/auth-url first.")

    # Resolve theme: tool's active theme > blueprint theme > default preset
    theme = tool.active_theme or tool.blueprint.theme
    if not theme:
        theme = preset_theme_to_theme_config("modern-minimalist")

    # Update status to deploying
    await _registry.update_tool(tool_id, status=ToolStatus.DEPLOYING)

    try:
        result = await deploy_sheet(
            blueprint=tool.blueprint,
            theme=theme,
            credentials=creds,
            folder_id=body.get("folder_id"),
        )

        # Update tool with sheet details
        await _registry.update_tool(
            tool_id,
            status=ToolStatus.ACTIVE,
            sheet_id=result["sheet_id"],
            sheet_url=result["sheet_url"],
            sheet_title=result["sheet_title"],
            active_theme=theme,
        )

        return result

    except Exception as e:
        await _registry.update_tool(tool_id, status=ToolStatus.ERROR)
        logger.exception("Deployment failed for tool %s", tool_id)
        raise HTTPException(status_code=500, detail=f"Deployment failed: {e}")


@router.post("/deploy/{tool_id}/redeploy-theme")
async def redeploy_tool_theme(tool_id: str):
    """Re-apply theme to deployed sheet. [ROBOT]"""
    from ..services.google_auth import get_credentials
    from ..services.sheet_deployer import redeploy_theme

    tool = await _registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    if not tool.sheet_id:
        raise HTTPException(status_code=400, detail="Tool is not deployed yet")
    if not tool.active_theme:
        raise HTTPException(status_code=400, detail="Tool has no active theme")

    creds = get_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated with Google")

    success = await redeploy_theme(tool.sheet_id, tool.active_theme, creds)
    if not success:
        raise HTTPException(status_code=500, detail="Theme redeployment failed")

    return {"status": "redeployed", "sheet_id": tool.sheet_id}


@router.post("/upload-prd")
async def upload_prd(
    file: Optional[UploadFile] = File(None),
    user_context: str = Form(""),
):
    """Upload a PRD file (.md or .txt) and extract structured steps.

    Accepts multipart/form-data with a file upload.
    """
    from ..services.prd_ingestion import extract_steps_from_prd, save_prd_upload, validate_prd_content

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    filename = file.filename or "upload.md"
    if not filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    content_bytes = await file.read()
    content = content_bytes.decode("utf-8", errors="replace")

    if not validate_prd_content(content):
        raise HTTPException(status_code=422, detail="PRD content is too short or invalid")

    try:
        prd = save_prd_upload(filename, content)
        extraction = await extract_steps_from_prd(content, user_context)

        return {
            "prd_id": prd.prd_id,
            "extraction": extraction.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("PRD upload processing failed")
        raise HTTPException(status_code=500, detail=f"PRD upload failed: {e}")
