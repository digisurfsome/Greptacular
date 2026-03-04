"""Factory mode REST API — start/stop/status for autonomous multi-phase builds."""

import logging
import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from registry import get_project_dir
from server.services.factory_controller import get_factory_controller, get_existing_controller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_name}/factory", tags=["factory"])


class FactoryStartRequest(BaseModel):
    mode: str = "continuous"  # "continuous" or "single"
    model: str = "claude-opus-4-6"
    yolo_mode: bool = False
    auto_commit: bool = True
    rate_limit_strategy: str = "wait"  # "wait" or "stop"
    start_phase: int = 1


class FactorySettingsRequest(BaseModel):
    handoff_threshold: Optional[int] = Field(None, ge=35, le=55)
    handoff_template: Optional[str] = None


class FactoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


def _resolve_project(project_name: str) -> Path:
    """Resolve project name to directory path."""
    project_dir = get_project_dir(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    return Path(project_dir)


@router.post("/start")
async def factory_start(project_name: str, req: FactoryStartRequest) -> FactoryResponse:
    """Start factory mode for a project."""
    project_dir = _resolve_project(project_name)
    controller = get_factory_controller(project_name, project_dir)
    success, msg = await controller.start(
        mode=req.mode,
        model=req.model,
        yolo_mode=req.yolo_mode,
        auto_commit=req.auto_commit,
        rate_limit_strategy=req.rate_limit_strategy,
        start_phase=req.start_phase,
    )
    return FactoryResponse(success=success, message=msg)


@router.post("/stop")
async def factory_stop(project_name: str) -> FactoryResponse:
    """Stop factory mode."""
    project_dir = _resolve_project(project_name)
    controller = get_factory_controller(project_name, project_dir)
    success, msg = await controller.stop()
    return FactoryResponse(success=success, message=msg)


@router.get("/status")
async def factory_status(project_name: str) -> FactoryResponse:
    """Get factory mode status."""
    project_dir = _resolve_project(project_name)
    controller = get_factory_controller(project_name, project_dir)
    status = await controller.get_status()
    return FactoryResponse(success=True, message="ok", data=status)


@router.put("/settings")
async def factory_update_settings(project_name: str, req: FactorySettingsRequest) -> FactoryResponse:
    """Update factory settings (handoff threshold and/or template)."""
    project_dir = _resolve_project(project_name)
    controller = get_factory_controller(project_name, project_dir)
    result = await controller.update_settings(
        handoff_threshold=req.handoff_threshold,
        handoff_template=req.handoff_template,
    )
    return FactoryResponse(success=True, message="Settings updated", data=result)


@router.get("/handoffs")
async def factory_handoffs(project_name: str) -> FactoryResponse:
    """Get archived handoff history."""
    import json
    project_dir = _resolve_project(project_name)
    history_dir = project_dir / ".autoforge" / "handoff_history"

    handoffs = []
    if history_dir.exists():
        for f in sorted(history_dir.glob("handoff-*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["_filename"] = f.name
                handoffs.append(data)
            except Exception:
                continue

    return FactoryResponse(success=True, message=f"{len(handoffs)} handoffs", data={"handoffs": handoffs})


@router.get("/handoffs/{filename}")
async def factory_handoff_detail(project_name: str, filename: str) -> FactoryResponse:
    """Get a specific archived handoff."""
    import json
    project_dir = _resolve_project(project_name)

    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    handoff_path = project_dir / ".autoforge" / "handoff_history" / filename
    if not handoff_path.exists():
        raise HTTPException(status_code=404, detail="Handoff not found")

    try:
        data = json.loads(handoff_path.read_text(encoding="utf-8"))
        return FactoryResponse(success=True, message="ok", data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read handoff: {e}")


# ── Phase PRD Document Management ────────────────────────────────


@router.get("/phases/documents")
async def list_phase_documents(project_name: str) -> FactoryResponse:
    """List all phase PRD documents (numbered .md files in .autoforge/phases/)."""
    project_dir = _resolve_project(project_name)
    phases_dir = project_dir / ".autoforge" / "phases"

    documents = []
    if phases_dir.exists():
        for f in sorted(phases_dir.glob("*.md")):
            try:
                # Extract phase number from filename (e.g., "1.md" -> 1)
                phase_num = int(f.stem)
                content = f.read_text(encoding="utf-8")
                documents.append({
                    "phase": phase_num,
                    "filename": f.name,
                    "size": len(content),
                    "preview": content[:200] + ("..." if len(content) > 200 else ""),
                })
            except (ValueError, Exception):
                continue

    return FactoryResponse(
        success=True,
        message=f"{len(documents)} phase documents",
        data={"documents": documents, "total": len(documents)},
    )


@router.get("/phases/documents/{phase_num}")
async def get_phase_document(project_name: str, phase_num: int) -> FactoryResponse:
    """Read a specific phase PRD document."""
    project_dir = _resolve_project(project_name)
    doc_path = project_dir / ".autoforge" / "phases" / f"{phase_num}.md"

    if not doc_path.exists():
        raise HTTPException(status_code=404, detail=f"Phase {phase_num} document not found")

    content = doc_path.read_text(encoding="utf-8")
    return FactoryResponse(
        success=True,
        message="ok",
        data={"phase": phase_num, "content": content, "size": len(content)},
    )


@router.put("/phases/documents/{phase_num}")
async def update_phase_document(project_name: str, phase_num: int, body: dict) -> FactoryResponse:
    """Create or update a phase PRD document."""
    project_dir = _resolve_project(project_name)
    phases_dir = project_dir / ".autoforge" / "phases"
    phases_dir.mkdir(parents=True, exist_ok=True)

    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    doc_path = phases_dir / f"{phase_num}.md"
    doc_path.write_text(content, encoding="utf-8")

    return FactoryResponse(
        success=True,
        message=f"Phase {phase_num} document saved",
        data={"phase": phase_num, "size": len(content)},
    )


@router.delete("/phases/documents/{phase_num}")
async def delete_phase_document(project_name: str, phase_num: int) -> FactoryResponse:
    """Delete a phase PRD document."""
    project_dir = _resolve_project(project_name)
    doc_path = project_dir / ".autoforge" / "phases" / f"{phase_num}.md"

    if not doc_path.exists():
        raise HTTPException(status_code=404, detail=f"Phase {phase_num} document not found")

    doc_path.unlink()
    return FactoryResponse(
        success=True,
        message=f"Phase {phase_num} document deleted",
        data={"phase": phase_num},
    )


@router.post("/phases/documents/upload")
async def upload_phase_documents(
    project_name: str, files: List[UploadFile] = File(...)
) -> FactoryResponse:
    """Upload multiple phase PRD documents.

    Files are assigned phase numbers based on:
    1. If filename starts with a number (e.g., "1.md", "3-dashboard.md"), use that number
    2. Otherwise, assign sequential numbers starting from the next available
    """
    project_dir = _resolve_project(project_name)
    phases_dir = project_dir / ".autoforge" / "phases"
    phases_dir.mkdir(parents=True, exist_ok=True)

    # Find existing phase numbers
    existing: set[int] = set()
    if phases_dir.exists():
        for f in phases_dir.glob("*.md"):
            try:
                existing.add(int(f.stem))
            except ValueError:
                pass

    uploaded = []
    next_num = max(existing, default=0) + 1

    for file in files:
        raw = await file.read()
        text = raw.decode("utf-8", errors="replace")

        # Try to extract phase number from filename
        phase_num = None
        name = file.filename or ""
        # Match leading digits: "1.md", "3-dashboard.md", "05_api.md"
        match = re.match(r"^(\d+)", name)
        if match:
            phase_num = int(match.group(1))

        if phase_num is None:
            phase_num = next_num
            next_num += 1

        doc_path = phases_dir / f"{phase_num}.md"
        doc_path.write_text(text, encoding="utf-8")
        uploaded.append({"phase": phase_num, "filename": name, "size": len(text)})

    return FactoryResponse(
        success=True,
        message=f"Uploaded {len(uploaded)} phase documents",
        data={"uploaded": uploaded},
    )
