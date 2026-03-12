"""Tool Themes Router — REST endpoints for theme management.

All endpoints are [ROBOT] except /themes/extract which calls the existing style_extractor.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.tool_factory import ThemeConfig
from ..services.sheet_theme_engine import (
    create_custom_theme,
    list_preset_themes,
    preset_theme_to_theme_config,
    style_extraction_to_theme_config,
    theme_to_sheets_format,
)
from ..services.tool_registry import ToolRegistryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tool-factory", tags=["tool-themes"])

_registry = ToolRegistryService()


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class ThemePreview(BaseModel):
    """Preview of what a theme looks like applied to sample data."""
    theme: ThemeConfig
    sample_cells: list[dict] = Field(description="Sample cells with applied formatting")
    color_swatches: list[dict] = Field(description="Color swatches for palette display")
    font_preview: dict = Field(description="Font preview info")


class ExtractThemeRequest(BaseModel):
    """Request to extract theme from an image."""
    image_base64: str = Field(..., min_length=100)


class CustomThemeRequest(BaseModel):
    """Request to create a custom theme."""
    theme_name: str = Field(default="Custom Theme", max_length=100)
    colors: dict = Field(...)
    typography: Optional[dict] = None
    components: Optional[dict] = None


class SwapThemeRequest(BaseModel):
    """Request to swap theme on a tool."""
    theme_id: Optional[str] = None
    theme_name: Optional[str] = None
    custom_theme: Optional[CustomThemeRequest] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/themes")
async def list_themes():
    """List all available themes (10 presets + user-created). [ROBOT]"""
    presets = list_preset_themes()
    return {"themes": [t.model_dump() for t in presets], "count": len(presets)}


@router.get("/themes/{theme_id}")
async def get_theme(theme_id: str):
    """Get a single theme by ID. [ROBOT]"""
    # Try preset first (theme_id format: "preset-ocean-depths")
    slug = theme_id.replace("preset-", "") if theme_id.startswith("preset-") else theme_id
    try:
        theme = preset_theme_to_theme_config(slug)
        return theme.model_dump()
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Theme not found: {theme_id}")


@router.post("/themes/extract")
async def extract_theme(body: ExtractThemeRequest):
    """Upload image -> call style_extractor -> return ThemeConfig. [AGENT] (calls existing style_extractor)"""
    from ..services.style_extractor import extract_style_from_image

    try:
        extraction = await extract_style_from_image(body.image_base64)
        theme = style_extraction_to_theme_config(extraction)
        return theme.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Theme extraction failed")
        raise HTTPException(status_code=500, detail=f"Theme extraction failed: {e}")


@router.post("/themes/preview")
async def preview_theme(body: dict):
    """Generate preview of theme on sample data. [ROBOT]"""
    theme_id = body.get("theme_id")
    if not theme_id:
        raise HTTPException(status_code=400, detail="theme_id is required")

    slug = theme_id.replace("preset-", "") if theme_id.startswith("preset-") else theme_id
    try:
        theme = preset_theme_to_theme_config(slug)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Theme not found: {theme_id}")

    formats = theme_to_sheets_format(theme)

    # Build sample cells
    sample_cells = [
        {"label": "Title Cell", "value": "My Strategy Tool", "format": formats["title_format"]},
        {"label": "Header Cell", "value": "Step #", "format": formats["header_format"]},
        {"label": "Body Cell", "value": "Research competitors", "format": formats["body_format"]},
        {"label": "Alt Row Cell", "value": "Generate ad copy", "format": formats["alt_row_format"]},
        {"label": "Input Cell", "value": "[Your Brand Name]", "format": formats["input_format"]},
    ]

    # Build color swatches
    color_swatches = [
        {"name": "Brand", "hex": theme.colors.brand_default},
        {"name": "Brand Light", "hex": theme.colors.brand_light},
        {"name": "Brand Dark", "hex": theme.colors.brand_dark},
        {"name": "Surface", "hex": theme.colors.surface_base},
        {"name": "Canvas", "hex": theme.colors.surface_canvas},
        {"name": "Text", "hex": theme.colors.text_primary},
        {"name": "Success", "hex": theme.colors.status_success},
        {"name": "Error", "hex": theme.colors.status_error},
        {"name": "Warning", "hex": theme.colors.status_warning},
    ]

    font_preview = {
        "heading": {"font": theme.typography.font_family_heading, "weight": theme.typography.font_weight_heading},
        "body": {"font": theme.typography.font_family_body, "weight": theme.typography.font_weight_body},
    }

    preview = ThemePreview(
        theme=theme,
        sample_cells=sample_cells,
        color_swatches=color_swatches,
        font_preview=font_preview,
    )
    return preview.model_dump()


@router.put("/tools/{tool_id}/theme")
async def swap_tool_theme(tool_id: str, body: SwapThemeRequest):
    """Swap theme on existing tool, re-apply formatting if deployed. [ROBOT]"""
    tool = await _registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    # Resolve theme
    theme: Optional[ThemeConfig] = None
    if body.custom_theme:
        theme = create_custom_theme(
            colors=body.custom_theme.colors,
            typography=body.custom_theme.typography,
            components=body.custom_theme.components,
            theme_name=body.custom_theme.theme_name,
        )
    elif body.theme_name:
        try:
            theme = preset_theme_to_theme_config(body.theme_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif body.theme_id:
        slug = body.theme_id.replace("preset-", "") if body.theme_id.startswith("preset-") else body.theme_id
        try:
            theme = preset_theme_to_theme_config(slug)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Provide theme_id, theme_name, or custom_theme")

    # Update in registry
    await _registry.update_theme(tool_id, theme)

    # If tool is deployed, re-apply formatting
    redeployed = False
    if tool.sheet_id and tool.status.value == "active":
        try:
            from ..services.google_auth import get_credentials
            from ..services.sheet_deployer import redeploy_theme

            creds = get_credentials()
            if creds:
                redeployed = await redeploy_theme(tool.sheet_id, theme, creds)
        except Exception as e:
            logger.warning("Failed to redeploy theme to sheet %s: %s", tool.sheet_id, e)

    return {
        "tool_id": tool_id,
        "theme": theme.model_dump(),
        "redeployed": redeployed,
    }


@router.post("/themes/custom")
async def create_custom_theme_endpoint(body: CustomThemeRequest):
    """Create custom theme from user inputs. [ROBOT]"""
    try:
        theme = create_custom_theme(
            colors=body.colors,
            typography=body.typography,
            components=body.components,
            theme_name=body.theme_name,
        )
        return theme.model_dump()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid theme data: {e}")
