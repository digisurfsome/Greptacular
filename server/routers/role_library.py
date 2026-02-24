"""
Role Library Router
===================

CRUD API for role blueprints — pre-PRD documents that describe agent roles
to be built for the terminal.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/workspace/roles", tags=["role_library"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class BlueprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role_tag: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    one_liner: str = Field(..., min_length=1, max_length=300)
    prd_content: str = ""
    subcategory: Optional[str] = None
    target_files: Optional[list[str]] = None
    status: str = "draft"


class BlueprintUpdate(BaseModel):
    name: Optional[str] = None
    role_tag: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    one_liner: Optional[str] = None
    prd_content: Optional[str] = None
    target_files: Optional[list[str]] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/")
async def list_blueprints(category: Optional[str] = None):
    """List all role blueprints, optionally filtered by category."""
    from ..services.workspace_database import list_blueprints as _list
    return _list(category=category)


@router.get("/categories")
async def list_categories():
    """Return distinct categories with counts."""
    from ..services.workspace_database import list_blueprint_categories
    return list_blueprint_categories()


@router.get("/{blueprint_id}")
async def get_blueprint(blueprint_id: int):
    """Get a single role blueprint by ID."""
    from ..services.workspace_database import get_blueprint as _get
    bp = _get(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return bp


@router.post("/", status_code=201)
async def create_blueprint(body: BlueprintCreate):
    """Create a new role blueprint."""
    from ..services.workspace_database import create_blueprint as _create
    try:
        return _create(
            name=body.name,
            role_tag=body.role_tag,
            category=body.category,
            one_liner=body.one_liner,
            prd_content=body.prd_content,
            subcategory=body.subcategory,
            target_files=body.target_files,
            status=body.status,
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=409, detail=f"Role tag '{body.role_tag}' already exists")
        raise


@router.patch("/{blueprint_id}")
async def update_blueprint(blueprint_id: int, body: BlueprintUpdate):
    """Update a role blueprint (partial update)."""
    from ..services.workspace_database import update_blueprint as _update
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = _update(blueprint_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return result


@router.delete("/{blueprint_id}")
async def delete_blueprint(blueprint_id: int):
    """Delete a role blueprint."""
    from ..services.workspace_database import delete_blueprint as _delete
    if not _delete(blueprint_id):
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"success": True}
