"""
Agent OS Router
===============

REST and WebSocket endpoints for the Agent OS PRD creation system.

Provides:
- Standards CRUD (read, write, list, infer from codebase)
- Product document CRUD
- Spec document CRUD
- Feature list management
- Gap analysis trigger
- Mechanism analysis trigger
- Handoff trigger
- Interactive PRD creation WebSocket session
- Intake dock file staging
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..services.agent_os_codebase import AgentOSCodebaseAnalyzer
from ..services.agent_os_expand import AgentOSExpand
from ..services.agent_os_features import AgentOSFeatures
from ..services.agent_os_file_utils import AgentOSFileUtils
from ..services.agent_os_handoff import AgentOSHandoff
from ..services.agent_os_intake_dock import AgentOSIntakeDock
from ..services.agent_os_session import (
    create_session,
    get_session,
    list_sessions,
    remove_session,
)
from ..services.agent_os_specs import AgentOSSpecs
from ..services.agent_os_standards import AgentOSStandards
from ..utils.project_helpers import get_project_path
from ..utils.validation import is_valid_project_name, validate_project_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-os", tags=["agent-os"])


# ============================================================================
# Pydantic Models
# ============================================================================


class StandardsFileContent(BaseModel):
    filename: str
    content: str
    location: str = "project"  # "project" or "global"


class ProductFileContent(BaseModel):
    filename: str
    content: str


class SpecFileContent(BaseModel):
    feature_id: int
    content: str


class FeatureCreate(BaseModel):
    name: str
    description: str
    priority: str = "should_have"
    complexity: str = "medium"
    category: str = "general"
    dependencies: list[int] = []


class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[str] = None
    category: Optional[str] = None


class GapResolution(BaseModel):
    resolution: str


class SessionStatus(BaseModel):
    project_name: str
    is_active: bool
    is_complete: bool
    current_stage: str
    stage_index: int
    message_count: int


class PasteFileRequest(BaseModel):
    filename: str
    content: str


class TagFileRequest(BaseModel):
    tag: str  # "standards" | "product" | "spec" | "reference" | "intake"


class ExpandRequest(BaseModel):
    description: str  # Natural language feature description


class ExpandAddRequest(BaseModel):
    features: list[dict]  # Validated features to add


# ============================================================================
# Helpers
# ============================================================================


def _resolve_project(project_name: str) -> Path:
    """Validate project name and resolve its path, or raise HTTPException."""
    validate_project_name(project_name)
    project_dir = get_project_path(project_name)
    if not project_dir:
        raise HTTPException(status_code=404, detail="Project not found in registry")
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")
    return project_dir


def _get_file_utils(project_dir: Path) -> AgentOSFileUtils:
    return AgentOSFileUtils(project_dir)


# ============================================================================
# Standards Endpoints
# ============================================================================


@router.get("/standards/{project_name}")
async def list_standards(project_name: str):
    """List all standards files (project + global)."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    return {"files": fu.list_files_in_layer("standards")}


@router.get("/standards/{project_name}/{filename}")
async def get_standard(project_name: str, filename: str):
    """Read one standards file."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    content = fu.read_standards_file(filename)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Standards file not found: {filename}")
    return {"filename": filename, "content": content}


@router.put("/standards/{project_name}/{filename}")
async def update_standard(project_name: str, filename: str, body: StandardsFileContent):
    """Write/update one standards file."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    path = fu.write_standards_file(filename, body.content, location=body.location)
    return {"status": "ok", "path": str(path)}


@router.post("/standards/{project_name}/infer")
async def infer_standards(project_name: str):
    """Trigger codebase inference, return inferred answers."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    standards = AgentOSStandards(project_dir, fu)
    inferred = standards.infer_standards_from_codebase()
    return {"inferred": inferred}


@router.get("/standards/{project_name}/summary")
async def get_standards_summary(project_name: str):
    """Get text summary of all standards."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    standards = AgentOSStandards(project_dir, fu)
    return {"summary": standards.get_standards_summary()}


# ============================================================================
# Product Endpoints
# ============================================================================


@router.get("/product/{project_name}")
async def list_product_files(project_name: str):
    """List all product documents."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    return {"files": fu.list_files_in_layer("product")}


@router.get("/product/{project_name}/{filename}")
async def get_product_file(project_name: str, filename: str):
    """Read one product document."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    content = fu.read_product_file(filename)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Product file not found: {filename}")
    return {"filename": filename, "content": content}


@router.put("/product/{project_name}/{filename}")
async def update_product_file(project_name: str, filename: str, body: ProductFileContent):
    """Write/update one product document."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    path = fu.write_product_file(filename, body.content)
    return {"status": "ok", "path": str(path)}


@router.get("/product/{project_name}/summary")
async def get_product_summary(project_name: str):
    """Get text summary of product layer."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    # Read all product files and build a summary
    files = fu.list_files_in_layer("product")
    parts: list[str] = []
    for f in files:
        content = fu.read_product_file(f["name"])
        if content:
            parts.append(f"**{f['name']}:** {content[:200]}")
    return {"summary": "\n".join(parts) if parts else "No product documents yet."}


# ============================================================================
# Specs Endpoints
# ============================================================================


@router.get("/specs/{project_name}")
async def list_specs(project_name: str):
    """List all spec files."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    return {"files": fu.list_files_in_layer("specs")}


@router.get("/specs/{project_name}/{feature_id}")
async def get_spec(project_name: str, feature_id: int):
    """Read one spec by feature ID."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    # Search for spec file matching feature ID
    specs_files = fu.list_files_in_layer("specs")
    prefix = f"feature-{feature_id:03d}-"
    for f in specs_files:
        if f["name"].startswith(prefix):
            content = fu.read_spec_file(f["name"])
            return {"feature_id": feature_id, "filename": f["name"], "content": content}
    raise HTTPException(status_code=404, detail=f"No spec found for feature {feature_id}")


@router.get("/specs/{project_name}/{feature_id}/quality")
async def get_spec_quality(project_name: str, feature_id: int):
    """Get quality report for one spec."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)

    # Find and read the spec
    specs_files = fu.list_files_in_layer("specs")
    prefix = f"feature-{feature_id:03d}-"
    for f in specs_files:
        if f["name"].startswith(prefix):
            content = fu.read_spec_file(f["name"])
            if content is None:
                raise HTTPException(status_code=404, detail="Spec file unreadable")
            # Use AgentOSSpecs to validate (needs minimal setup)
            # Create a minimal features mock for validation
            specs_service = AgentOSSpecs(project_dir, fu, features=None, mechanism=None)
            specs_service._spec_contents[feature_id] = content
            report = specs_service.validate_spec(feature_id)
            return {"feature_id": feature_id, "quality": report}
    raise HTTPException(status_code=404, detail=f"No spec found for feature {feature_id}")


# ============================================================================
# Features Endpoints
# ============================================================================


# In-memory features store per project (session-scoped)
_project_features: dict[str, AgentOSFeatures] = {}


def _get_features_service(project_name: str, project_dir: Path) -> AgentOSFeatures:
    """Get the features service for a project.

    Prefers the active session's features instance to stay in sync
    with the WebSocket workflow. Falls back to a standalone instance.
    """
    # If there's an active session, use its features (keeps REST and WS in sync)
    session = get_session(project_name)
    if session is not None and session.features is not None:
        return session.features

    # Fallback: standalone instance for REST-only usage
    if project_name not in _project_features:
        fu = _get_file_utils(project_dir)
        _project_features[project_name] = AgentOSFeatures(
            project_dir, fu, entities={}, config={},
        )
    return _project_features[project_name]


@router.get("/features/{project_name}")
async def list_features(project_name: str):
    """Get feature list with priorities and dependencies."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    return {"features": features.get_feature_list()}


@router.post("/features/{project_name}")
async def add_feature(project_name: str, body: FeatureCreate):
    """Manually add a feature."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    new = features.add_feature({
        "name": body.name,
        "description": body.description,
        "priority": body.priority,
        "complexity": body.complexity,
        "category": body.category,
        "dependencies": body.dependencies,
    })
    return {"feature": new}


@router.put("/features/{project_name}/{feature_id}")
async def update_feature(project_name: str, feature_id: int, body: FeatureUpdate):
    """Update a feature."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    updates = body.model_dump(exclude_none=True)
    updated = features.update_feature(feature_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id} not found")
    return {"feature": updated}


@router.delete("/features/{project_name}/{feature_id}")
async def remove_feature(project_name: str, feature_id: int):
    """Remove a feature."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    removed = features.remove_feature(feature_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id} not found")
    return {"status": "ok", "removed": feature_id}


# ============================================================================
# Gap Analysis Endpoints
# ============================================================================


@router.get("/gaps/{project_name}")
async def list_gaps(project_name: str, severity: Optional[str] = None):
    """Get all gaps (optionally filter by severity)."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    gaps = features.get_all_gaps()
    if severity:
        gaps = [g for g in gaps if g.get("severity") == severity]
    return {"gaps": gaps}


@router.post("/gaps/{project_name}/{gap_id}/resolve")
async def resolve_gap(project_name: str, gap_id: int, body: GapResolution):
    """Resolve a gap with explanation."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    resolved = features.resolve_gap(gap_id, body.resolution)
    if resolved is None:
        raise HTTPException(status_code=404, detail=f"Gap {gap_id} not found")
    return {"gap": resolved}


@router.post("/gaps/{project_name}/auto-resolve")
async def auto_resolve_gaps(project_name: str):
    """Auto-resolve all high-confidence gaps."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    resolved = features.auto_resolve_gaps()
    return {"resolved": resolved, "count": len(resolved)}


# ============================================================================
# Handoff Endpoints
# ============================================================================


@router.post("/handoff/{project_name}/populate-db")
async def populate_db(project_name: str):
    """Populate features.db from specs."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    try:
        count = handoff.populate_features_db()
        return {"status": "ok", "feature_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to populate DB: {e}")


@router.post("/handoff/{project_name}/build-order")
async def calculate_build_order(project_name: str):
    """Calculate and return build order."""
    project_dir = _resolve_project(project_name)
    features = _get_features_service(project_name, project_dir)
    fu = _get_file_utils(project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    order = handoff.calculate_build_order()
    return {"build_order": order}


@router.get("/handoff/{project_name}/status")
async def get_handoff_status(project_name: str):
    """Get current handoff status."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    return {"status": handoff.get_handoff_status()}


@router.post("/handoff/{project_name}/assemble")
async def assemble_handoff(project_name: str):
    """Final handoff assembly + validation."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    try:
        handoff.generate_scope_boundary()
        handoff.generate_context_primer()
    except Exception as e:
        logger.warning("Handoff generation warning: %s", e)
    status = handoff.assemble_handoff_package()
    return {"handoff": status}


@router.get("/handoff/{project_name}/build-plan")
async def get_build_plan(project_name: str):
    """Get human-readable build plan."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    return {"plan": handoff.get_build_plan_summary()}


# ============================================================================
# Intake Dock Endpoints
# ============================================================================


_intake_docks: dict[str, AgentOSIntakeDock] = {}


def _get_intake_dock(project_name: str, project_dir: Path) -> AgentOSIntakeDock:
    """Get or create an intake dock instance for a project."""
    if project_name not in _intake_docks:
        fu = _get_file_utils(project_dir)
        _intake_docks[project_name] = AgentOSIntakeDock(project_dir, fu)
    return _intake_docks[project_name]


@router.get("/intake-dock/{project_name}")
async def list_staged_files(project_name: str):
    """List all staged files."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    return {"files": dock.get_staged_files()}


@router.post("/intake-dock/{project_name}/upload")
async def upload_file(project_name: str, file: UploadFile):
    """Upload and stage a file (multipart form)."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)

    content = await file.read()
    filename = file.filename or "upload.md"
    mime_type = file.content_type or "application/octet-stream"

    entry = dock.stage_file(filename, content, mime_type)
    return {"file": entry}


@router.post("/intake-dock/{project_name}/paste")
async def paste_text(project_name: str, body: PasteFileRequest):
    """Create a file from pasted text."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    entry = dock.stage_text(body.filename, body.content)
    return {"file": entry}


@router.put("/intake-dock/{project_name}/{file_id}/tag")
async def tag_staged_file(project_name: str, file_id: str, body: TagFileRequest):
    """Set tag for a staged file."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    entry = dock.tag_file(file_id, body.tag)
    if entry is None:
        raise HTTPException(status_code=400, detail="Invalid file ID or tag")
    return {"file": entry}


@router.delete("/intake-dock/{project_name}/{file_id}")
async def remove_staged_file(project_name: str, file_id: str):
    """Remove a staged file."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    removed = dock.remove_file(file_id)
    if not removed:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "ok"}


@router.get("/intake-dock/{project_name}/readiness")
async def get_readiness(project_name: str):
    """Get readiness checklist status."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    return dock.get_readiness()


@router.post("/intake-dock/{project_name}/process")
async def process_intake(project_name: str):
    """Process all staged files - distribute to directories."""
    project_dir = _resolve_project(project_name)
    dock = _get_intake_dock(project_name, project_dir)
    result = dock.process_files()
    return result


# ============================================================================
# Expand Endpoints (Phase 7)
# ============================================================================


def _get_expand_service(project_name: str, project_dir: Path) -> AgentOSExpand:
    """Create an expand service instance with all dependencies."""
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    return AgentOSExpand(project_dir, fu, features, specs_service, handoff, config={})


@router.post("/expand/{project_name}/analyze")
async def analyze_expansion(project_name: str, body: ExpandRequest):
    """Analyze user input to extract and validate new features."""
    project_dir = _resolve_project(project_name)
    expand = _get_expand_service(project_name, project_dir)
    prompt = expand.get_expansion_prompt(body.description)
    return {"prompt": prompt, "description": body.description}


@router.post("/expand/{project_name}/add")
async def add_expanded_features(project_name: str, body: ExpandAddRequest):
    """Add validated features, update deps, return summary."""
    project_dir = _resolve_project(project_name)
    expand = _get_expand_service(project_name, project_dir)

    # Validate
    validation = expand.process_expansion(body.features)
    if not validation["added"]:
        return {
            "status": "no_features_added",
            "conflicts": validation["conflicts"],
            "warnings": validation["warnings"],
        }

    # Add
    added = expand.add_features(validation["added"])

    # Update dependency graph
    try:
        graph = expand.update_dependency_graph()
    except Exception as e:
        graph = {"error": str(e)}

    # Recalculate build order
    try:
        build_order = expand.recalculate_build_order()
    except Exception as e:
        build_order = []
        logger.warning("Could not recalculate build order: %s", e)

    return {
        "status": "ok",
        "added": added,
        "conflicts": validation["conflicts"],
        "warnings": validation["warnings"],
        "graph": graph,
        "new_build_order": build_order,
    }


@router.get("/expand/{project_name}/summary")
async def get_expansion_summary(project_name: str):
    """Get summary of last expansion."""
    project_dir = _resolve_project(project_name)
    expand = _get_expand_service(project_name, project_dir)
    return {"summary": expand.get_expansion_summary()}


# ============================================================================
# Codebase Reality Engine Endpoints (Phase 7)
# ============================================================================


@router.post("/cre/{project_name}/scan")
async def scan_codebase(project_name: str):
    """Trigger a full codebase scan."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    analysis = analyzer.scan_codebase()
    return {"analysis": analysis}


@router.get("/cre/{project_name}/analysis")
async def get_cre_analysis(project_name: str):
    """Get scan results (runs scan if not cached)."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    analysis = analyzer.scan_codebase()
    return {"analysis": analysis}


@router.post("/cre/{project_name}/apply-standards")
async def apply_inferred_standards(project_name: str):
    """Generate and write inferred standards from codebase scan."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    prompt = analyzer.get_standards_inference_prompt()
    return {"prompt": prompt, "message": "Send this prompt to Claude, then POST the result back."}


@router.post("/cre/{project_name}/apply-product")
async def apply_inferred_product(project_name: str):
    """Generate and write inferred product layer from codebase scan."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    prompt = analyzer.get_product_inference_prompt()
    return {"prompt": prompt, "message": "Send this prompt to Claude, then POST the result back."}


@router.post("/cre/{project_name}/apply-features")
async def apply_inferred_features(project_name: str):
    """Generate and write inferred features from codebase scan."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    prompt = analyzer.get_feature_inference_prompt()
    return {"prompt": prompt, "message": "Send this prompt to Claude, then POST the result back."}


@router.get("/cre/{project_name}/summary")
async def get_cre_summary(project_name: str):
    """Get human-readable scan summary."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    analyzer = AgentOSCodebaseAnalyzer(project_dir, fu)
    analyzer.scan_codebase()
    return {"summary": analyzer.get_analysis_summary()}


# ============================================================================
# Context Primer Endpoints
# ============================================================================


@router.get("/context-primer/{project_name}")
def get_context_primer(project_name: str):
    """Read the context primer from .agent/knowledge/context-primer.md."""
    project_dir = _resolve_project(project_name)
    primer_path = project_dir / ".agent" / "knowledge" / "context-primer.md"
    if not primer_path.is_file():
        raise HTTPException(status_code=404, detail="Context primer not found. Run handoff assembly first.")
    content = primer_path.read_text(encoding="utf-8")
    return {"content": content, "path": str(primer_path)}


@router.post("/context-primer/{project_name}")
async def regenerate_context_primer(project_name: str):
    """Regenerate the context primer by re-running assembly logic."""
    project_dir = _resolve_project(project_name)
    fu = _get_file_utils(project_dir)
    features = _get_features_service(project_name, project_dir)
    specs_service = AgentOSSpecs(project_dir, fu, features, mechanism=None)
    handoff = AgentOSHandoff(project_dir, fu, features, specs_service)
    try:
        path = handoff.generate_context_primer()
        content = path.read_text(encoding="utf-8")
        return {"status": "ok", "content": content, "path": str(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate context primer: {e}")


# ============================================================================
# Session Endpoints
# ============================================================================


@router.get("/sessions")
async def list_agent_os_sessions():
    """List active sessions."""
    return {"sessions": list_sessions()}


@router.get("/sessions/{project_name}", response_model=SessionStatus)
async def get_session_status(project_name: str):
    """Get session status."""
    validate_project_name(project_name)
    session = get_session(project_name)
    if not session:
        raise HTTPException(status_code=404, detail="No active session for this project")
    return SessionStatus(
        project_name=project_name,
        is_active=True,
        is_complete=session.is_complete(),
        current_stage=session.get_stage(),
        stage_index=session.current_stage_index,
        message_count=len(session.get_messages()),
    )


@router.delete("/sessions/{project_name}")
async def cancel_session(project_name: str):
    """Cancel and remove session."""
    validate_project_name(project_name)
    session = get_session(project_name)
    if not session:
        raise HTTPException(status_code=404, detail="No active session for this project")
    remove_session(project_name)
    return {"status": "ok", "message": "Session cancelled"}


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws/{project_name}")
async def agent_os_websocket(websocket: WebSocket, project_name: str):
    """Interactive Agent OS PRD creation session."""
    await websocket.accept()

    if not is_valid_project_name(project_name):
        await websocket.send_json({"type": "error", "message": "Invalid project name"})
        await websocket.close(code=4000, reason="Invalid project name")
        return

    project_dir = get_project_path(project_name)
    if not project_dir:
        await websocket.send_json({"type": "error", "message": "Project not found"})
        await websocket.close(code=4004, reason="Project not found")
        return

    if not project_dir.exists():
        await websocket.send_json({"type": "error", "message": "Project directory not found"})
        await websocket.close(code=4004, reason="Project directory not found")
        return

    # Get or create session
    session = get_session(project_name)
    if not session:
        session = create_session(project_name, project_dir)

    # Send initial state
    await websocket.send_json({
        "type": "stage_change",
        "stage": session.get_stage(),
        "index": session.current_stage_index,
        "total": len(session.STAGES),
    })

    try:
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                msg_type = msg.get("type", "message")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type == "message":
                    async for event in session.process_message(msg.get("content", "")):
                        await websocket.send_json(event)

                elif msg_type == "answer":
                    async for event in session.process_message(msg.get("answer", "")):
                        await websocket.send_json(event)

                elif msg_type == "approve":
                    async for event in session.process_message("__approve__"):
                        await websocket.send_json(event)

                elif msg_type == "skip_stage":
                    session.advance_stage()
                    await websocket.send_json({
                        "type": "stage_change",
                        "stage": session.get_stage(),
                        "index": session.current_stage_index,
                        "total": len(session.STAGES),
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        logger.info("Agent OS WebSocket disconnected for %s", project_name)
    except Exception as e:
        logger.error("Agent OS WebSocket error: %s", e, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
