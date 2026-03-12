"""Data models for the Video-to-Tool Factory."""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from ..services.api_research import BlueprintAPIResearch

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StepType(str, Enum):
    RESEARCH = "research"
    GENERATION = "generation"
    ACTION = "action"
    MANUAL = "manual"


class ToolStatus(str, Enum):
    DRAFT = "draft"              # Blueprint generated, not yet deployed
    DEPLOYING = "deploying"      # Google Sheet creation in progress
    ACTIVE = "active"            # Deployed and ready to use
    ERROR = "error"              # Deployment failed
    ARCHIVED = "archived"        # Soft-deleted


class ThemeSource(str, Enum):
    PRESET = "preset"            # From theme-factory presets
    EXTRACTED = "extracted"      # From style_extractor.py (image → theme)
    CUSTOM = "custom"            # User-created custom theme


class IngestionSource(str, Enum):
    YOUTUBE = "youtube"
    PRD_UPLOAD = "prd_upload"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Theme Models
# ---------------------------------------------------------------------------

class ThemeColors(BaseModel):
    """Color palette for a theme."""
    brand_light: str = Field(description="Light brand color hex")
    brand_default: str = Field(description="Primary brand color hex")
    brand_dark: str = Field(description="Dark brand color hex")
    surface_canvas: str = Field(description="Page background hex")
    surface_base: str = Field(description="Card/container background hex")
    surface_muted: str = Field(description="Input/subtle background hex")
    text_primary: str = Field(description="Main text color hex")
    text_secondary: str = Field(description="Muted/secondary text hex")
    text_tertiary: str = Field(description="Hint/placeholder text hex")
    border_subtle: str = Field(description="Border/divider color hex")
    status_success: str = Field(default="#22c55e", description="Success indicator hex")
    status_error: str = Field(default="#ef4444", description="Error indicator hex")
    status_warning: str = Field(default="#f59e0b", description="Warning indicator hex")


class ThemeTypography(BaseModel):
    """Typography configuration for a theme."""
    font_family_heading: str = Field(description="Google Font name for headings")
    font_family_body: str = Field(description="Google Font name for body text")
    font_weight_heading: int = Field(default=700, description="Heading weight (400-900)")
    font_weight_body: int = Field(default=400, description="Body weight (400-700)")
    base_size_px: int = Field(default=14, description="Base font size in pixels")


class ThemeComponents(BaseModel):
    """Component styling tokens."""
    card_radius_px: int = Field(default=8, description="Card border radius")
    button_radius_px: int = Field(default=6, description="Button border radius")
    input_radius_px: int = Field(default=4, description="Input border radius")
    shadow_card: str = Field(default="0 1px 3px rgba(0,0,0,0.1)", description="Card box shadow CSS")
    spacing_unit_px: int = Field(default=8, description="Base spacing unit (4, 8, or 10)")
    density: str = Field(default="cozy", description="'cozy' (whitespace-heavy) or 'compact' (data-dense)")


class ThemeConfig(BaseModel):
    """Universal theme config — every generated tool carries one.

    This is the convergence point for both theme paths:
    - Path A: style_extractor.py → ThemeConfig (source='extracted')
    - Path B: theme-factory presets → ThemeConfig (source='preset')
    - Path C: user creates custom → ThemeConfig (source='custom')
    """
    theme_id: str = Field(description="Unique theme identifier")
    theme_name: str = Field(description="Human-readable display name")
    source: ThemeSource = Field(description="How this theme was created")
    colors: ThemeColors
    typography: ThemeTypography
    components: ThemeComponents
    tailwind_config: dict = Field(default_factory=dict, description="Raw Tailwind extension JSON for web previews")
    style_classification: Optional[str] = Field(
        default=None,
        description="Style ID from style_extractor (e.g. 'neubrutalism', 'glassmorphism')"
    )
    source_image_path: Optional[str] = Field(
        default=None,
        description="Path to source image if extracted from screenshot"
    )


# ---------------------------------------------------------------------------
# Chain Config Models (what goes into the Google Sheet)
# ---------------------------------------------------------------------------

class DetectedAPI(BaseModel):
    """An external API/service detected from step prompt text."""
    service_name: str = Field(description="e.g. 'Meta Marketing API'")
    service_key: str = Field(description="e.g. 'meta_marketing'")
    detection_pattern: str = Field(description="What text triggered detection")
    signup_url: str = Field(description="URL where user gets API key")
    required_env_vars: list[str] = Field(description="e.g. ['META_APP_ID', 'META_APP_SECRET']")


class ChainConfigRow(BaseModel):
    """One row in the Chain Config tab of the generated Google Sheet."""
    row_number: int = Field(description="1-indexed row position in chain")
    step_type: StepType
    title: str = Field(description="Short step title for the sheet")
    prompt_template: str = Field(description="The AI prompt with {{variables}} and {{previousOutput}}")
    expected_output: str = Field(description="What this step should produce")
    input_source: str = Field(description="'user_input', 'row_N', or 'row_N+row_M' for merged inputs")
    output_destination: str = Field(description="'row_N_output' cell reference")
    model_recommendation: str = Field(default="sonnet", description="Recommended AI model for this step")
    apis_required: list[str] = Field(default_factory=list, description="Service keys needed")
    is_gate: bool = Field(default=False, description="If True, chain pauses here for user review")
    max_retries: int = Field(default=1, description="Auto-retry on failure")
    timeout_seconds: int = Field(default=120, description="Max execution time per step")
    notes: str = Field(default="", description="Implementation notes from video extraction")
    original_step_id: str = Field(description="ID of the source YTStrategyStep")
    original_step_order: int = Field(description="Original order in the video")


class SheetBlueprint(BaseModel):
    """Complete blueprint for a Google Sheet tool."""
    blueprint_id: str = Field(description="Unique ID for this blueprint")
    tool_name: str = Field(description="Name of the tool (derived from video title)")
    tool_description: str = Field(description="One-line description of what the tool does")
    source_video_id: str = Field(description="YouTube video ID that generated this")
    source_video_title: str = Field(description="Original video title")
    source_video_channel: str = Field(description="Channel name")
    source_project_id: str = Field(description="YT Lab project ID")

    chain_config: list[ChainConfigRow] = Field(description="The prompt chain rows")
    detected_apis: list[DetectedAPI] = Field(description="All APIs detected across all steps")
    user_input_variables: list[str] = Field(
        description="Variables the user must fill in before running"
    )

    theme: Optional[ThemeConfig] = Field(default=None, description="Selected theme")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # API pricing research (None if research was skipped or failed entirely)
    api_research: Optional[BlueprintAPIResearch] = Field(
        default=None,
        description="Pricing research results for detected APIs",
    )

    # PRD input path additions
    ingestion_source: IngestionSource = Field(default=IngestionSource.YOUTUBE)
    source_prd_id: Optional[str] = Field(default=None, description="Set when source is PRD upload")


# ---------------------------------------------------------------------------
# Tool Registry (persisted)
# ---------------------------------------------------------------------------

class GeneratedTool(BaseModel):
    """A generated tool tracked in the registry.

    Lifecycle: DRAFT → DEPLOYING → ACTIVE (or ERROR) → ARCHIVED
    """
    tool_id: str = Field(description="Unique tool identifier")
    blueprint: SheetBlueprint = Field(description="The full blueprint used to create this tool")
    status: ToolStatus = Field(default=ToolStatus.DRAFT)

    # Google Sheet details (populated after deployment)
    sheet_id: Optional[str] = Field(default=None, description="Google Sheets document ID")
    sheet_url: Optional[str] = Field(default=None, description="Direct link to the sheet")
    sheet_title: Optional[str] = Field(default=None, description="Title as it appears in Google Drive")

    # Theme (separate from blueprint so it can be swapped independently)
    active_theme: Optional[ThemeConfig] = Field(default=None, description="Currently applied theme")

    # Execution tracking
    times_run: int = Field(default=0, description="How many times the chain has been executed")
    last_run_at: Optional[str] = Field(default=None)
    total_tokens_used: int = Field(default=0, description="Cumulative token usage across all runs")

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: list[str] = Field(default_factory=list, description="User-assigned tags for organization")


class ToolRegistry(BaseModel):
    """Root model for the tool registry file."""
    tools: list[GeneratedTool] = Field(default_factory=list)
    total_tools_created: int = Field(default=0)
    total_tools_deployed: int = Field(default=0)


# ---------------------------------------------------------------------------
# PRD Input Models
# ---------------------------------------------------------------------------

class PRDUpload(BaseModel):
    """A PRD document uploaded directly instead of YouTube video."""
    prd_id: str
    filename: str
    content: str
    source: Literal["upload"] = "upload"
    uploaded_at: str


class PRDExtractionResult(BaseModel):
    """Result of extracting steps from a PRD document."""
    project_name: str
    project_description: str
    niche: str
    tags: list[str]
    steps: list[dict]               # Same shape as YTStrategyStep for pipeline compatibility
    extraction_model: str
    extraction_time: float
