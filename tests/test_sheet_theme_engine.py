"""Unit tests for sheet_theme_engine.py — all [ROBOT] functions."""

import pytest

from server.services.sheet_theme_engine import (
    _PRESET_DEFINITIONS,
    build_theme_requests,
    create_custom_theme,
    hex_to_sheets_color,
    list_preset_themes,
    preset_theme_to_theme_config,
    style_extraction_to_theme_config,
    theme_to_sheets_format,
)


class TestHexToSheetsColor:
    def test_hex_to_sheets_color(self):
        result = hex_to_sheets_color("#FF5733")
        assert result["red"] == 1.0
        assert abs(result["green"] - 0.341) < 0.01
        assert abs(result["blue"] - 0.2) < 0.01

    def test_hex_to_sheets_color_black(self):
        result = hex_to_sheets_color("#000000")
        assert result == {"red": 0.0, "green": 0.0, "blue": 0.0}

    def test_hex_to_sheets_color_white(self):
        result = hex_to_sheets_color("#FFFFFF")
        assert result == {"red": 1.0, "green": 1.0, "blue": 1.0}

    def test_hex_without_hash(self):
        result = hex_to_sheets_color("FF5733")
        assert result["red"] == 1.0

    def test_hex_shorthand(self):
        result = hex_to_sheets_color("#FFF")
        assert result == {"red": 1.0, "green": 1.0, "blue": 1.0}

    def test_hex_lowercase(self):
        result = hex_to_sheets_color("#ff5733")
        assert result["red"] == 1.0


class TestPresetThemes:
    def test_preset_theme_loads(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        assert theme.theme_name == "Ocean Depths"
        assert theme.source.value == "preset"
        assert theme.theme_id == "preset-ocean-depths"

    def test_all_presets_load(self):
        """All 10 presets load without error."""
        themes = list_preset_themes()
        assert len(themes) == 10
        for theme in themes:
            assert theme.theme_id.startswith("preset-")
            assert theme.colors.brand_default
            assert theme.typography.font_family_heading

    def test_preset_to_theme_config_has_all_fields(self):
        theme = preset_theme_to_theme_config("sunset-boulevard")
        assert theme.colors.brand_light
        assert theme.colors.brand_default
        assert theme.colors.brand_dark
        assert theme.colors.surface_canvas
        assert theme.colors.surface_base
        assert theme.colors.text_primary
        assert theme.typography.font_family_heading
        assert theme.typography.font_family_body
        assert theme.components is not None

    def test_unknown_preset_raises(self):
        with pytest.raises(ValueError, match="Unknown preset theme"):
            preset_theme_to_theme_config("nonexistent-theme")

    def test_preset_count_matches_definitions(self):
        assert len(_PRESET_DEFINITIONS) == 10


class TestThemeToSheetsFormat:
    def test_theme_to_sheets_format(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        fmt = theme_to_sheets_format(theme)
        assert "header_format" in fmt
        assert "body_format" in fmt
        assert "alt_row_format" in fmt
        assert "input_format" in fmt
        assert "title_format" in fmt

    def test_header_format_has_background(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        fmt = theme_to_sheets_format(theme)
        header = fmt["header_format"]
        assert "backgroundColor" in header
        assert "red" in header["backgroundColor"]

    def test_body_format_has_text(self):
        theme = preset_theme_to_theme_config("modern-minimalist")
        fmt = theme_to_sheets_format(theme)
        body = fmt["body_format"]
        assert "textFormat" in body
        assert body["textFormat"]["fontFamily"] == "DejaVu Sans"


class TestBuildThemeRequests:
    def test_build_theme_requests(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        sheet_ids = {"Guide": 0, "Setup": 1, "Chain Config": 2, "Output History": 3, "Chain Runner": 4}
        requests = build_theme_requests(theme, sheet_ids)
        assert isinstance(requests, list)
        assert len(requests) > 0

    def test_requests_include_conditional_formatting(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        sheet_ids = {"Guide": 0, "Setup": 1, "Chain Config": 2, "Output History": 3, "Chain Runner": 4}
        requests = build_theme_requests(theme, sheet_ids)
        cond_format_requests = [r for r in requests if "addConditionalFormatRule" in r]
        assert len(cond_format_requests) == 4  # Done, Error, Pending, Running

    def test_requests_include_input_highlight(self):
        theme = preset_theme_to_theme_config("ocean-depths")
        sheet_ids = {"Guide": 0, "Setup": 1, "Chain Config": 2}
        requests = build_theme_requests(theme, sheet_ids)
        repeat_cells = [r for r in requests if "repeatCell" in r]
        assert len(repeat_cells) > 0


class TestCustomTheme:
    def test_custom_theme_creation(self):
        colors = {
            "brand_light": "#e0e0e0",
            "brand_default": "#333333",
            "brand_dark": "#111111",
            "surface_canvas": "#ffffff",
            "surface_base": "#fafafa",
            "surface_muted": "#f0f0f0",
            "text_primary": "#000000",
            "text_secondary": "#666666",
            "text_tertiary": "#999999",
            "border_subtle": "#cccccc",
        }
        theme = create_custom_theme(colors=colors, theme_name="My Theme")
        assert theme.source.value == "custom"
        assert theme.theme_name == "My Theme"
        assert theme.theme_id.startswith("custom-")
        assert theme.colors.brand_default == "#333333"


class TestStyleExtractionToThemeConfig:
    def test_style_extraction_to_theme_config(self):
        """Mock style_extractor output -> ThemeConfig."""
        extraction = {
            "identified_style": {
                "primary": "minimalism",
                "primary_confidence": "high",
                "accent": None,
                "accent_confidence": "low",
            },
            "extracted_tokens": {
                "colors": {
                    "brand": {"light": "#e0e7ff", "DEFAULT": "#4f46e5", "dark": "#3730a3"},
                    "surface": {"canvas": "#ffffff", "base": "#f9fafb", "muted": "#f3f4f6"},
                    "text": {"primary": "#111827", "secondary": "#6b7280", "tertiary": "#9ca3af"},
                    "border": {"subtle": "#e5e7eb"},
                },
                "fontFamily": {"sans": ["Inter", "sans-serif"]},
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#e0e7ff", "DEFAULT": "#4f46e5", "dark": "#3730a3"},
                    "surface": {"canvas": "#ffffff", "base": "#f9fafb", "muted": "#f3f4f6"},
                    "text": {"primary": "#111827", "secondary": "#6b7280", "tertiary": "#9ca3af"},
                    "border": {"subtle": "#e5e7eb"},
                },
                "fontFamily": {"sans": ["Inter", "sans-serif"]},
            },
            "style_guide_markdown": "# Style Guide\n...",
        }

        theme = style_extraction_to_theme_config(extraction)
        assert theme.source.value == "extracted"
        assert theme.colors.brand_default == "#4f46e5"
        assert theme.typography.font_family_body == "Inter"
        assert theme.style_classification == "minimalism"
        assert theme.theme_id == "extracted-minimalism"

    def test_extraction_with_empty_tailwind(self):
        extraction = {
            "identified_style": {"primary": None},
            "extracted_tokens": {},
            "tailwind_config": {},
            "style_guide_markdown": "",
        }
        theme = style_extraction_to_theme_config(extraction)
        assert theme.source.value == "extracted"
        # Should use defaults
        assert theme.colors.brand_default == "#4f46e5"
