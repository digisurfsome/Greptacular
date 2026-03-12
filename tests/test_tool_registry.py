"""Unit tests for server/services/tool_registry.py — all [ROBOT], no LLM calls."""

import asyncio
import json

import pytest

from server.models.tool_factory import (
    ChainConfigRow,
    SheetBlueprint,
    StepType,
    ThemeColors,
    ThemeComponents,
    ThemeConfig,
    ThemeSource,
    ThemeTypography,
    ToolStatus,
)
from server.services.tool_registry import ToolRegistryService


def _make_blueprint(name: str = "Test Tool") -> SheetBlueprint:
    return SheetBlueprint(
        blueprint_id="bp_test123",
        tool_name=name,
        tool_description="A test tool",
        source_video_id="dQw4w9WgXcQ",
        source_video_title="Test Video",
        source_video_channel="TestChannel",
        source_project_id="proj_123",
        chain_config=[
            ChainConfigRow(
                row_number=1,
                step_type=StepType.RESEARCH,
                title="Research",
                prompt_template="Do research",
                expected_output="Report",
                input_source="user_input",
                output_destination="row_1_output",
                original_step_id="s1",
                original_step_order=1,
            )
        ],
        detected_apis=[],
        user_input_variables=["niche"],
    )


def _make_theme() -> ThemeConfig:
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


@pytest.fixture
def registry_service(tmp_path):
    """Create a registry service with a temp file."""
    return ToolRegistryService(registry_path=tmp_path / "test_registry.json")


class TestToolRegistryCRUD:
    def test_create_tool(self, registry_service):
        tool = asyncio.get_event_loop().run_until_complete(
            registry_service.create_tool(_make_blueprint())
        )
        assert tool.tool_id.startswith("tool_")
        assert tool.status == ToolStatus.DRAFT
        assert registry_service.registry_path.exists()

    def test_get_tool_exists(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))
        found = loop.run_until_complete(registry_service.get_tool(tool.tool_id))
        assert found is not None
        assert found.tool_id == tool.tool_id

    def test_get_tool_missing(self, registry_service):
        result = asyncio.get_event_loop().run_until_complete(
            registry_service.get_tool("nonexistent_id")
        )
        assert result is None

    def test_list_tools_all(self, registry_service):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(registry_service.create_tool(_make_blueprint("Tool A")))
        loop.run_until_complete(registry_service.create_tool(_make_blueprint("Tool B")))
        tools = loop.run_until_complete(registry_service.list_tools())
        assert len(tools) == 2

    def test_list_tools_by_status(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))
        loop.run_until_complete(registry_service.archive_tool(tool.tool_id))

        draft_tools = loop.run_until_complete(registry_service.list_tools(status=ToolStatus.DRAFT))
        archived_tools = loop.run_until_complete(registry_service.list_tools(status=ToolStatus.ARCHIVED))
        assert len(draft_tools) == 0
        assert len(archived_tools) == 1

    def test_list_tools_pagination(self, registry_service):
        loop = asyncio.get_event_loop()
        for i in range(5):
            loop.run_until_complete(registry_service.create_tool(_make_blueprint(f"Tool {i}")))

        page1 = loop.run_until_complete(registry_service.list_tools(limit=2, offset=0))
        page2 = loop.run_until_complete(registry_service.list_tools(limit=2, offset=2))
        assert len(page1) == 2
        assert len(page2) == 2

    def test_update_tool(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))
        original_updated = tool.updated_at

        updated = loop.run_until_complete(
            registry_service.update_tool(tool.tool_id, status=ToolStatus.ACTIVE)
        )
        assert updated is not None
        assert updated.status == ToolStatus.ACTIVE
        assert updated.updated_at >= original_updated

    def test_update_theme(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))
        theme = _make_theme()

        updated = loop.run_until_complete(
            registry_service.update_theme(tool.tool_id, theme)
        )
        assert updated is not None
        assert updated.active_theme is not None
        assert updated.active_theme.theme_id == "test-theme"

    def test_archive_tool(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))
        archived = loop.run_until_complete(registry_service.archive_tool(tool.tool_id))
        assert archived is not None
        assert archived.status == ToolStatus.ARCHIVED

    def test_record_run(self, registry_service):
        loop = asyncio.get_event_loop()
        tool = loop.run_until_complete(registry_service.create_tool(_make_blueprint()))

        loop.run_until_complete(registry_service.record_run(tool.tool_id, tokens_used=1500))
        updated = loop.run_until_complete(registry_service.get_tool(tool.tool_id))
        assert updated.times_run == 1
        assert updated.total_tokens_used == 1500
        assert updated.last_run_at is not None

    def test_get_stats(self, registry_service):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(registry_service.create_tool(_make_blueprint("A")))
        tool_b = loop.run_until_complete(registry_service.create_tool(_make_blueprint("B")))
        loop.run_until_complete(registry_service.archive_tool(tool_b.tool_id))

        stats = loop.run_until_complete(registry_service.get_stats())
        assert stats["total_tools"] == 2
        assert stats["total_tools_created"] == 2
        assert stats["by_status"]["draft"] == 1
        assert stats["by_status"]["archived"] == 1

    def test_atomic_save(self, registry_service):
        """File isn't corrupted — verify JSON is valid after save."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(registry_service.create_tool(_make_blueprint()))

        raw = registry_service.registry_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)  # Should not raise
        assert "tools" in parsed
        assert len(parsed["tools"]) == 1
