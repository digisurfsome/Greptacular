"""Unit tests for sheet_deployer.py — all [ROBOT] functions."""

from unittest.mock import MagicMock, patch

import pytest

from server.models.tool_factory import (
    ChainConfigRow,
    DetectedAPI,
    SheetBlueprint,
    StepType,
    ThemeColors,
    ThemeComponents,
    ThemeConfig,
    ThemeSource,
    ThemeTypography,
)
from server.services.sheet_deployer import (
    _build_chain_data,
    _build_chain_runner_data,
    _build_data_validation,
    _build_guide_data,
    _build_output_history_data,
    _build_setup_data,
)


def _sample_blueprint() -> SheetBlueprint:
    """Create a sample SheetBlueprint for testing."""
    return SheetBlueprint(
        blueprint_id="bp_test123",
        tool_name="SEO Keyword Research Tool",
        tool_description="Automated keyword research using competitor analysis",
        source_video_id="abc123",
        source_video_title="How to Do SEO in 2026",
        source_video_channel="Marketing Pro",
        source_project_id="proj_test",
        chain_config=[
            ChainConfigRow(
                row_number=1,
                step_type=StepType.RESEARCH,
                title="Research Competitors",
                prompt_template="Analyze the top 10 competitors for {{niche}}",
                expected_output="List of competitor keywords",
                input_source="user_input",
                output_destination="row_1_output",
                original_step_id="step_1",
                original_step_order=1,
            ),
            ChainConfigRow(
                row_number=2,
                step_type=StepType.GENERATION,
                title="Generate Keywords",
                prompt_template="Based on {{previousOutput}}, generate 50 keywords",
                expected_output="Keyword list with search volume estimates",
                input_source="row_1",
                output_destination="row_2_output",
                original_step_id="step_2",
                original_step_order=2,
            ),
        ],
        detected_apis=[
            DetectedAPI(
                service_name="SerpAPI",
                service_key="serpapi",
                detection_pattern="search results",
                signup_url="https://serpapi.com",
                required_env_vars=["SERPAPI_KEY"],
            ),
        ],
        user_input_variables=["niche", "target_audience"],
    )


def _sample_theme() -> ThemeConfig:
    """Create a sample ThemeConfig for testing."""
    return ThemeConfig(
        theme_id="preset-ocean-depths",
        theme_name="Ocean Depths",
        source=ThemeSource.PRESET,
        colors=ThemeColors(
            brand_light="#a8dadc",
            brand_default="#2d8b8b",
            brand_dark="#1a2332",
            surface_canvas="#f1faee",
            surface_base="#ffffff",
            surface_muted="#ddf0e6",
            text_primary="#1a2332",
            text_secondary="#2d8b8b",
            text_tertiary="#7aafb0",
            border_subtle="#a8dadc",
        ),
        typography=ThemeTypography(
            font_family_heading="DejaVu Sans",
            font_family_body="DejaVu Sans",
        ),
        components=ThemeComponents(),
    )


class TestBuildGuideTabData:
    def test_guide_has_tool_name(self):
        bp = _sample_blueprint()
        rows = _build_guide_data(bp)
        assert rows[1][1] == "SEO Keyword Research Tool"

    def test_guide_has_description(self):
        bp = _sample_blueprint()
        rows = _build_guide_data(bp)
        assert "keyword research" in rows[2][1].lower()

    def test_guide_has_api_keys(self):
        bp = _sample_blueprint()
        rows = _build_guide_data(bp)
        api_rows = [r for r in rows if "SerpAPI" in str(r)]
        assert len(api_rows) >= 1


class TestBuildSetupTabData:
    def test_setup_has_variables(self):
        bp = _sample_blueprint()
        rows = _build_setup_data(bp)
        labels = [r[0] for r in rows]
        assert "niche" in labels
        assert "target_audience" in labels

    def test_setup_has_api_keys_section(self):
        bp = _sample_blueprint()
        rows = _build_setup_data(bp)
        flat = str(rows)
        assert "API KEYS" in flat
        assert "SerpAPI" in flat


class TestBuildChainTabData:
    def test_chain_rows_match_blueprint(self):
        bp = _sample_blueprint()
        rows = _build_chain_data(bp)
        # Row 0 is header, rows 1+ are data
        assert len(rows) == 3  # header + 2 steps
        assert rows[1][1] == "Research Competitors"
        assert rows[2][1] == "Generate Keywords"

    def test_chain_has_status_pending(self):
        bp = _sample_blueprint()
        rows = _build_chain_data(bp)
        assert rows[1][6] == "Pending"
        assert rows[2][6] == "Pending"

    def test_chain_has_step_types(self):
        bp = _sample_blueprint()
        rows = _build_chain_data(bp)
        assert rows[1][2] == "research"
        assert rows[2][2] == "generation"


class TestBuildConditionalFormatting:
    def test_build_conditional_formatting(self):
        rules = _build_data_validation(chain_tab_id=2)
        assert isinstance(rules, list)
        assert len(rules) == 2  # Status dropdown + Step Type dropdown

    def test_status_dropdown(self):
        rules = _build_data_validation(chain_tab_id=2)
        status_rule = rules[0]
        validation = status_rule["setDataValidation"]["rule"]
        values = [v["userEnteredValue"] for v in validation["condition"]["values"]]
        assert "Pending" in values
        assert "Done" in values
        assert "Error" in values
        assert "Running" in values

    def test_step_type_dropdown(self):
        rules = _build_data_validation(chain_tab_id=2)
        type_rule = rules[1]
        validation = type_rule["setDataValidation"]["rule"]
        values = [v["userEnteredValue"] for v in validation["condition"]["values"]]
        assert "research" in values
        assert "generation" in values
        assert "action" in values
        assert "manual" in values


class TestDeploySheetMock:
    @pytest.mark.asyncio
    async def test_deploy_sheet_mock(self):
        """Full deploy with mocked Sheets API."""
        from server.services.sheet_deployer import deploy_sheet

        bp = _sample_blueprint()
        theme = _sample_theme()

        mock_service = MagicMock()
        mock_spreadsheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock create response
        mock_spreadsheets.create.return_value.execute.return_value = {
            "spreadsheetId": "sheet_123",
            "sheets": [
                {"properties": {"title": "Guide", "sheetId": 0}},
                {"properties": {"title": "Setup", "sheetId": 1}},
                {"properties": {"title": "Chain Config", "sheetId": 2}},
                {"properties": {"title": "Output History", "sheetId": 3}},
                {"properties": {"title": "Chain Runner", "sheetId": 4}},
            ],
        }

        mock_values = MagicMock()
        mock_spreadsheets.values.return_value = mock_values
        mock_values.batchUpdate.return_value.execute.return_value = {}
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("server.services.sheet_deployer._get_sheets_service", return_value=mock_service):
            result = await deploy_sheet(bp, theme, credentials=MagicMock())

        assert result["sheet_id"] == "sheet_123"
        assert "docs.google.com" in result["sheet_url"]
        assert "AutoForge Tool" in result["sheet_title"]

    @pytest.mark.asyncio
    async def test_redeploy_theme_mock(self):
        """Theme swap with mocked Sheets API."""
        from server.services.sheet_deployer import redeploy_theme

        theme = _sample_theme()

        mock_service = MagicMock()
        mock_spreadsheets = MagicMock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        mock_spreadsheets.get.return_value.execute.return_value = {
            "sheets": [
                {"properties": {"title": "Guide", "sheetId": 0}},
                {"properties": {"title": "Setup", "sheetId": 1}},
                {"properties": {"title": "Chain Config", "sheetId": 2}},
            ],
        }
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("server.services.sheet_deployer._get_sheets_service", return_value=mock_service):
            result = await redeploy_theme("sheet_123", theme, credentials=MagicMock())

        assert result is True
        mock_spreadsheets.batchUpdate.assert_called_once()


class TestOutputHistory:
    def test_output_history_headers(self):
        rows = _build_output_history_data()
        assert rows[0] == ["Run #", "Timestamp", "Step", "Input Summary", "Output Summary", "Tokens Used", "Duration"]


class TestChainRunner:
    def test_chain_runner_has_instructions(self):
        bp = _sample_blueprint()
        rows = _build_chain_runner_data(bp)
        flat = str(rows)
        assert "Apps Script" in flat
        assert str(len(bp.chain_config)) in flat
