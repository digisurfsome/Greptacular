"""Sheet Theme Engine — converts theme formats to unified ThemeConfig and Google Sheets formatting.

ALL functions are [ROBOT] — pure Python, zero LLM calls.
"""

import logging
from pathlib import Path
from typing import Optional

from ..models.tool_factory import (
    ThemeColors,
    ThemeComponents,
    ThemeConfig,
    ThemeSource,
    ThemeTypography,
)

logger = logging.getLogger(__name__)

# Path to preset theme .md files
THEME_FACTORY_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "skills" / "theme-factory" / "themes"

# ---------------------------------------------------------------------------
# Preset theme color/font mappings (parsed from .md files)
# Each preset has 4 named colors that map to ThemeColors fields
# ---------------------------------------------------------------------------

_PRESET_DEFINITIONS: dict[str, dict] = {
    "arctic-frost": {
        "name": "Arctic Frost",
        "colors": {
            "brand_light": "#d4e4f7",
            "brand_default": "#4a6fa5",
            "brand_dark": "#3a5a8a",
            "surface_canvas": "#fafafa",
            "surface_base": "#ffffff",
            "surface_muted": "#e8eef5",
            "text_primary": "#1a2332",
            "text_secondary": "#4a6fa5",
            "text_tertiary": "#c0c0c0",
            "border_subtle": "#d4e4f7",
        },
        "typography": {
            "font_family_heading": "DejaVu Sans",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "botanical-garden": {
        "name": "Botanical Garden",
        "colors": {
            "brand_light": "#6a9c73",
            "brand_default": "#4a7c59",
            "brand_dark": "#3a6245",
            "surface_canvas": "#f5f3ed",
            "surface_base": "#ffffff",
            "surface_muted": "#eae6dd",
            "text_primary": "#2a3d2e",
            "text_secondary": "#4a7c59",
            "text_tertiary": "#8a9a8e",
            "border_subtle": "#d0cdc5",
        },
        "typography": {
            "font_family_heading": "DejaVu Serif",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
        "extra": {"accent": "#f9a620", "accent2": "#b7472a"},
    },
    "desert-rose": {
        "name": "Desert Rose",
        "colors": {
            "brand_light": "#d4a5a5",
            "brand_default": "#b87d6d",
            "brand_dark": "#5d2e46",
            "surface_canvas": "#faf5f0",
            "surface_base": "#ffffff",
            "surface_muted": "#e8d5c4",
            "text_primary": "#5d2e46",
            "text_secondary": "#b87d6d",
            "text_tertiary": "#c4a898",
            "border_subtle": "#e8d5c4",
        },
        "typography": {
            "font_family_heading": "FreeSans",
            "font_family_body": "FreeSans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "forest-canopy": {
        "name": "Forest Canopy",
        "colors": {
            "brand_light": "#a4ac86",
            "brand_default": "#2d4a2b",
            "brand_dark": "#1e3220",
            "surface_canvas": "#faf9f6",
            "surface_base": "#ffffff",
            "surface_muted": "#eeeee6",
            "text_primary": "#2d4a2b",
            "text_secondary": "#7d8471",
            "text_tertiary": "#a4ac86",
            "border_subtle": "#d0d4c4",
        },
        "typography": {
            "font_family_heading": "FreeSerif",
            "font_family_body": "FreeSans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "golden-hour": {
        "name": "Golden Hour",
        "colors": {
            "brand_light": "#f4c94c",
            "brand_default": "#f4a900",
            "brand_dark": "#c08600",
            "surface_canvas": "#faf6ee",
            "surface_base": "#ffffff",
            "surface_muted": "#d4b896",
            "text_primary": "#4a403a",
            "text_secondary": "#c1666b",
            "text_tertiary": "#a8968a",
            "border_subtle": "#d4b896",
        },
        "typography": {
            "font_family_heading": "FreeSans",
            "font_family_body": "FreeSans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "midnight-galaxy": {
        "name": "Midnight Galaxy",
        "colors": {
            "brand_light": "#a490c2",
            "brand_default": "#4a4e8f",
            "brand_dark": "#2b1e3e",
            "surface_canvas": "#1e1830",
            "surface_base": "#2b1e3e",
            "surface_muted": "#3a3060",
            "text_primary": "#e6e6fa",
            "text_secondary": "#a490c2",
            "text_tertiary": "#7a6e9a",
            "border_subtle": "#4a4e8f",
        },
        "typography": {
            "font_family_heading": "FreeSans",
            "font_family_body": "FreeSans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "modern-minimalist": {
        "name": "Modern Minimalist",
        "colors": {
            "brand_light": "#d3d3d3",
            "brand_default": "#36454f",
            "brand_dark": "#1e2a32",
            "surface_canvas": "#ffffff",
            "surface_base": "#fafafa",
            "surface_muted": "#f0f0f0",
            "text_primary": "#36454f",
            "text_secondary": "#708090",
            "text_tertiary": "#d3d3d3",
            "border_subtle": "#e0e0e0",
        },
        "typography": {
            "font_family_heading": "DejaVu Sans",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "ocean-depths": {
        "name": "Ocean Depths",
        "colors": {
            "brand_light": "#a8dadc",
            "brand_default": "#2d8b8b",
            "brand_dark": "#1a2332",
            "surface_canvas": "#f1faee",
            "surface_base": "#ffffff",
            "surface_muted": "#ddf0e6",
            "text_primary": "#1a2332",
            "text_secondary": "#2d8b8b",
            "text_tertiary": "#7aafb0",
            "border_subtle": "#a8dadc",
        },
        "typography": {
            "font_family_heading": "DejaVu Sans",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "sunset-boulevard": {
        "name": "Sunset Boulevard",
        "colors": {
            "brand_light": "#f4a261",
            "brand_default": "#e76f51",
            "brand_dark": "#264653",
            "surface_canvas": "#fdf8f0",
            "surface_base": "#ffffff",
            "surface_muted": "#e9c46a",
            "text_primary": "#264653",
            "text_secondary": "#e76f51",
            "text_tertiary": "#a0a0a0",
            "border_subtle": "#e9c46a",
        },
        "typography": {
            "font_family_heading": "DejaVu Serif",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
    "tech-innovation": {
        "name": "Tech Innovation",
        "colors": {
            "brand_light": "#00ffff",
            "brand_default": "#0066ff",
            "brand_dark": "#0044aa",
            "surface_canvas": "#1e1e1e",
            "surface_base": "#2a2a2a",
            "surface_muted": "#333333",
            "text_primary": "#ffffff",
            "text_secondary": "#00ffff",
            "text_tertiary": "#888888",
            "border_subtle": "#444444",
        },
        "typography": {
            "font_family_heading": "DejaVu Sans",
            "font_family_body": "DejaVu Sans",
            "font_weight_heading": 700,
            "font_weight_body": 400,
        },
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def hex_to_sheets_color(hex_color: str) -> dict:
    """Convert hex color string to Google Sheets API color format.

    Args:
        hex_color: Color string like "#FF5733" or "FF5733".

    Returns:
        Dict with "red", "green", "blue" keys, each 0.0-1.0.
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return {"red": round(r, 3), "green": round(g, 3), "blue": round(b, 3)}


def style_extraction_to_theme_config(extraction: dict) -> ThemeConfig:
    """Map style_extractor.py output to ThemeConfig.

    Args:
        extraction: Dict from style_extractor.parse_extraction_response() with keys:
            identified_style, extracted_tokens, tailwind_config, style_guide_markdown.

    Returns:
        ThemeConfig with source='extracted'.
    """
    tailwind = extraction.get("tailwind_config") or extraction.get("extracted_tokens") or {}
    style_info = extraction.get("identified_style", {})

    # Extract colors from tailwind config
    colors_cfg = tailwind.get("colors", {})
    brand = colors_cfg.get("brand", {})
    surface = colors_cfg.get("surface", {})
    text = colors_cfg.get("text", {})
    border = colors_cfg.get("border", {})

    colors = ThemeColors(
        brand_light=brand.get("light", "#e0e7ff"),
        brand_default=brand.get("DEFAULT", "#4f46e5"),
        brand_dark=brand.get("dark", "#3730a3"),
        surface_canvas=surface.get("canvas", "#ffffff"),
        surface_base=surface.get("base", "#f9fafb"),
        surface_muted=surface.get("muted", "#f3f4f6"),
        text_primary=text.get("primary", "#111827"),
        text_secondary=text.get("secondary", "#6b7280"),
        text_tertiary=text.get("tertiary", "#9ca3af"),
        border_subtle=border.get("subtle", "#e5e7eb"),
    )

    # Extract fonts from tailwind config
    font_family = tailwind.get("fontFamily", {})
    sans_fonts = font_family.get("sans", ["Inter", "sans-serif"])
    heading_font = sans_fonts[0] if isinstance(sans_fonts, list) and sans_fonts else "Inter"
    body_font = heading_font  # Same family unless serif is specified
    if "serif" in font_family:
        serif_fonts = font_family["serif"]
        if isinstance(serif_fonts, list) and serif_fonts:
            heading_font = serif_fonts[0]

    typography = ThemeTypography(
        font_family_heading=heading_font,
        font_family_body=body_font,
    )

    primary_style = style_info.get("primary")
    style_id = primary_style if primary_style else "extracted"

    return ThemeConfig(
        theme_id=f"extracted-{style_id}",
        theme_name=f"Extracted: {style_id.replace('-', ' ').title()}",
        source=ThemeSource.EXTRACTED,
        colors=colors,
        typography=typography,
        components=ThemeComponents(),
        tailwind_config=tailwind,
        style_classification=primary_style,
    )


def preset_theme_to_theme_config(theme_name: str) -> ThemeConfig:
    """Load a preset theme by slug name and return ThemeConfig.

    Args:
        theme_name: Slug like "ocean-depths", "sunset-boulevard".

    Returns:
        ThemeConfig with source='preset'.

    Raises:
        ValueError: If theme_name is not a known preset.
    """
    slug = theme_name.lower().strip()
    if slug not in _PRESET_DEFINITIONS:
        available = ", ".join(sorted(_PRESET_DEFINITIONS.keys()))
        raise ValueError(f"Unknown preset theme: '{theme_name}'. Available: {available}")

    defn = _PRESET_DEFINITIONS[slug]
    return ThemeConfig(
        theme_id=f"preset-{slug}",
        theme_name=defn["name"],
        source=ThemeSource.PRESET,
        colors=ThemeColors(**defn["colors"]),
        typography=ThemeTypography(**defn["typography"]),
        components=ThemeComponents(),
    )


def list_preset_themes() -> list[ThemeConfig]:
    """Return all 10 preset themes as ThemeConfig objects."""
    themes = []
    for slug in sorted(_PRESET_DEFINITIONS.keys()):
        themes.append(preset_theme_to_theme_config(slug))
    return themes


def theme_to_sheets_format(theme: ThemeConfig) -> dict:
    """Convert ThemeConfig to Google Sheets API CellFormat dicts.

    Returns:
        Dict with keys: header_format, body_format, alt_row_format,
        input_format, title_format, each containing a CellFormat dict.
    """
    return {
        "header_format": {
            "backgroundColor": hex_to_sheets_color(theme.colors.brand_default),
            "textFormat": {
                "foregroundColor": hex_to_sheets_color(theme.colors.surface_canvas),
                "fontFamily": theme.typography.font_family_heading,
                "fontSize": theme.typography.base_size_px + 2,
                "bold": True,
            },
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
        },
        "body_format": {
            "backgroundColor": hex_to_sheets_color(theme.colors.surface_base),
            "textFormat": {
                "foregroundColor": hex_to_sheets_color(theme.colors.text_primary),
                "fontFamily": theme.typography.font_family_body,
                "fontSize": theme.typography.base_size_px,
                "bold": False,
            },
        },
        "alt_row_format": {
            "backgroundColor": hex_to_sheets_color(theme.colors.surface_canvas),
            "textFormat": {
                "foregroundColor": hex_to_sheets_color(theme.colors.text_primary),
                "fontFamily": theme.typography.font_family_body,
                "fontSize": theme.typography.base_size_px,
                "bold": False,
            },
        },
        "input_format": {
            "backgroundColor": hex_to_sheets_color(theme.colors.brand_light),
            "textFormat": {
                "foregroundColor": hex_to_sheets_color(theme.colors.text_primary),
                "fontFamily": theme.typography.font_family_body,
                "fontSize": theme.typography.base_size_px,
                "bold": False,
            },
            "borders": {
                "bottom": {
                    "style": "SOLID",
                    "width": 2,
                    "color": hex_to_sheets_color(theme.colors.brand_default),
                },
            },
        },
        "title_format": {
            "backgroundColor": hex_to_sheets_color(theme.colors.brand_dark),
            "textFormat": {
                "foregroundColor": hex_to_sheets_color(theme.colors.surface_canvas),
                "fontFamily": theme.typography.font_family_heading,
                "fontSize": theme.typography.base_size_px + 6,
                "bold": True,
            },
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
        },
    }


def build_theme_requests(theme: ThemeConfig, sheet_ids: dict[str, int]) -> list[dict]:
    """Assemble full batchUpdate request list for applying theme to all 5 sheet tabs.

    Args:
        theme: The theme to apply.
        sheet_ids: Mapping of tab name to sheetId (e.g. {"Guide": 0, "Setup": 1, ...}).

    Returns:
        List of Google Sheets API request dicts for a batchUpdate call.
    """
    formats = theme_to_sheets_format(theme)
    requests: list[dict] = []

    for tab_name, sid in sheet_ids.items():
        # Header row formatting (row 0 or row 1 depending on tab)
        header_row = 0
        if tab_name == "Guide":
            # Guide tab: row 0 is title, row 1+ is content
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": formats["title_format"]},
                    "fields": "userEnteredFormat",
                }
            })
            header_row = 1
        else:
            # Other tabs: row 0 is column headers
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": formats["header_format"]},
                    "fields": "userEnteredFormat",
                }
            })

        # Body rows (rows 1-100)
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": header_row + 1, "endRowIndex": 100},
                "cell": {"userEnteredFormat": formats["body_format"]},
                "fields": "userEnteredFormat",
            }
        })

        # Freeze header row
        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sid,
                    "gridProperties": {"frozenRowCount": header_row + 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        })

    # Conditional formatting for Chain Config status column (assumed col index 6)
    chain_sid = sheet_ids.get("Chain Config")
    if chain_sid is not None:
        requests.extend(_build_conditional_formatting(theme, chain_sid))

    # Input cell highlighting for Setup tab
    setup_sid = sheet_ids.get("Setup")
    if setup_sid is not None:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": setup_sid,
                    "startRowIndex": 1,
                    "endRowIndex": 50,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },
                "cell": {"userEnteredFormat": formats["input_format"]},
                "fields": "userEnteredFormat",
            }
        })

    return requests


def _build_conditional_formatting(theme: ThemeConfig, chain_tab_id: int) -> list[dict]:
    """Build conditional format rules for the status column in Chain Config tab.

    Returns:
        List of addConditionalFormatRule requests.
    """
    # Status column is column G (index 6)
    status_range = {
        "sheetId": chain_tab_id,
        "startRowIndex": 1,
        "endRowIndex": 100,
        "startColumnIndex": 6,
        "endColumnIndex": 7,
    }

    rules = [
        ("Done", theme.colors.status_success),
        ("Error", theme.colors.status_error),
        ("Pending", theme.colors.status_warning),
        ("Running", theme.colors.brand_default),
    ]

    requests = []
    for idx, (text, color) in enumerate(rules):
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [status_range],
                    "booleanRule": {
                        "condition": {
                            "type": "TEXT_EQ",
                            "values": [{"userEnteredValue": text}],
                        },
                        "format": {
                            "backgroundColor": hex_to_sheets_color(color),
                            "textFormat": {"bold": True},
                        },
                    },
                },
                "index": idx,
            }
        })

    return requests


def create_custom_theme(
    colors: dict,
    typography: Optional[dict] = None,
    components: Optional[dict] = None,
    theme_name: str = "Custom Theme",
) -> ThemeConfig:
    """Create a ThemeConfig from user-provided values.

    Args:
        colors: Dict with ThemeColors fields (brand_light, brand_default, etc.).
        typography: Optional dict with ThemeTypography fields.
        components: Optional dict with ThemeComponents fields.
        theme_name: Display name for the theme.

    Returns:
        ThemeConfig with source='custom'.
    """
    import uuid

    theme_id = f"custom-{uuid.uuid4().hex[:8]}"
    return ThemeConfig(
        theme_id=theme_id,
        theme_name=theme_name,
        source=ThemeSource.CUSTOM,
        colors=ThemeColors(**colors),
        typography=ThemeTypography(**(typography or {"font_family_heading": "Arial", "font_family_body": "Arial"})),
        components=ThemeComponents(**(components or {})),
    )
