"""Unit tests for server/models/tool_factory.py — all [ROBOT], no LLM calls."""

import json

from server.models.tool_factory import (
    ChainConfigRow,
    GeneratedTool,
    IngestionSource,
    PRDUpload,
    SheetBlueprint,
    StepType,
    ThemeColors,
    ThemeComponents,
    ThemeConfig,
    ThemeSource,
    ThemeTypography,
    ToolRegistry,
    ToolStatus,
)


def _make_theme_config() -> ThemeConfig:
    return ThemeConfig(
        theme_id="test-theme",
        theme_name="Test Theme",
        source=ThemeSource.PRESET,
        colors=ThemeColors(
            brand_light="#e0f0ff",
            brand_default="#3b82f6",
            brand_dark="#1e40af",
            surface_canvas="#ffffff",
            surface_base="#f9fafb",
            surface_muted="#f3f4f6",
            text_primary="#111827",
            text_secondary="#6b7280",
            text_tertiary="#9ca3af",
            border_subtle="#e5e7eb",
        ),
        typography=ThemeTypography(
            font_family_heading="Inter",
            font_family_body="Inter",
        ),
        components=ThemeComponents(),
    )


def _make_chain_row(row_number: int = 1) -> ChainConfigRow:
    return ChainConfigRow(
        row_number=row_number,
        step_type=StepType.RESEARCH,
        title="Test Step",
        prompt_template="Do research on {{niche}}",
        expected_output="Research report",
        input_source="user_input",
        output_destination=f"row_{row_number}_output",
        original_step_id="abc123",
        original_step_order=row_number,
    )


def _make_blueprint() -> SheetBlueprint:
    return SheetBlueprint(
        blueprint_id="bp_test123",
        tool_name="Test Tool",
        tool_description="A test tool",
        source_video_id="dQw4w9WgXcQ",
        source_video_title="Test Video",
        source_video_channel="TestChannel",
        source_project_id="proj_123",
        chain_config=[_make_chain_row(1), _make_chain_row(2)],
        detected_apis=[],
        user_input_variables=["niche"],
    )


class TestStepTypeEnum:
    def test_step_type_enum_values(self):
        assert StepType.RESEARCH.value == "research"
        assert StepType.GENERATION.value == "generation"
        assert StepType.ACTION.value == "action"
        assert StepType.MANUAL.value == "manual"
        assert len(StepType) == 4


class TestToolStatusLifecycle:
    def test_tool_status_lifecycle(self):
        assert ToolStatus.DRAFT.value == "draft"
        assert ToolStatus.DEPLOYING.value == "deploying"
        assert ToolStatus.ACTIVE.value == "active"
        assert ToolStatus.ERROR.value == "error"
        assert ToolStatus.ARCHIVED.value == "archived"
        assert len(ToolStatus) == 5


class TestThemeConfig:
    def test_theme_config_creation(self):
        theme = _make_theme_config()
        assert theme.theme_id == "test-theme"
        assert theme.source == ThemeSource.PRESET
        assert theme.colors.brand_default == "#3b82f6"
        assert theme.typography.font_weight_heading == 700
        assert theme.components.card_radius_px == 8

    def test_theme_config_extracted_source(self):
        theme = _make_theme_config()
        theme.source = ThemeSource.EXTRACTED
        theme.source_image_path = "/tmp/screenshot.png"
        assert theme.source == ThemeSource.EXTRACTED
        assert theme.source_image_path == "/tmp/screenshot.png"


class TestChainConfigRow:
    def test_chain_config_row_defaults(self):
        row = _make_chain_row()
        assert row.max_retries == 1
        assert row.timeout_seconds == 120
        assert row.is_gate is False
        assert row.apis_required == []
        assert row.notes == ""


class TestSheetBlueprint:
    def test_sheet_blueprint_serialization(self):
        bp = _make_blueprint()
        json_str = bp.model_dump_json()
        parsed = json.loads(json_str)
        restored = SheetBlueprint.model_validate(parsed)
        assert restored.blueprint_id == bp.blueprint_id
        assert len(restored.chain_config) == 2
        assert restored.user_input_variables == ["niche"]

    def test_sheet_blueprint_ingestion_source(self):
        bp = _make_blueprint()
        assert bp.ingestion_source == IngestionSource.YOUTUBE
        assert bp.source_prd_id is None

        bp2 = _make_blueprint()
        bp2.ingestion_source = IngestionSource.PRD_UPLOAD
        bp2.source_prd_id = "prd_abc123"
        assert bp2.ingestion_source == IngestionSource.PRD_UPLOAD


class TestGeneratedTool:
    def test_generated_tool_defaults(self):
        tool = GeneratedTool(
            tool_id="tool_test123",
            blueprint=_make_blueprint(),
        )
        assert tool.status == ToolStatus.DRAFT
        assert tool.times_run == 0
        assert tool.total_tokens_used == 0
        assert tool.sheet_id is None
        assert tool.tags == []


class TestPRDUpload:
    def test_prd_upload_model(self):
        prd = PRDUpload(
            prd_id="prd_abc123",
            filename="my_prd.md",
            content="# My PRD\n\nThis is a PRD document with enough content.",
            uploaded_at="2025-01-01T00:00:00Z",
        )
        assert prd.prd_id == "prd_abc123"
        assert prd.source == "upload"
        assert prd.filename == "my_prd.md"


class TestIngestionSource:
    def test_ingestion_source_enum(self):
        assert IngestionSource.YOUTUBE.value == "youtube"
        assert IngestionSource.PRD_UPLOAD.value == "prd_upload"
        assert IngestionSource.MANUAL.value == "manual"
        assert len(IngestionSource) == 3


class TestToolRegistry:
    def test_tool_registry_empty(self):
        registry = ToolRegistry()
        assert registry.tools == []
        assert registry.total_tools_created == 0
        assert registry.total_tools_deployed == 0
