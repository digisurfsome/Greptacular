"""
Style Modifiers
===============

Accessibility modifiers that layer on top of base UI styles.
These provide targeted overrides for specific accessibility needs
without replacing the entire base style.
"""

import logging

logger = logging.getLogger(__name__)


STYLE_MODIFIERS: list[dict] = [
    {
        "id": "high-contrast-buttons",
        "name": "High Contrast Buttons",
        "description": (
            "Increases button visibility with stronger borders, bolder text, and higher contrast backgrounds. "
            "Great for users who need clear interactive element identification."
        ),
        "category": "accessibility",
        "icon": "contrast",  # lucide icon name
        "token_overrides": {
            "buttons": {
                "border": "2px solid currentColor",
                "font_weight": 700,
                "min_height": "44px",
                "focus_ring": "3px solid brand-DEFAULT",
                "contrast_ratio": "4.5:1 minimum (WCAG AA)",
            }
        },
        "prompt_additions": [
            "All buttons MUST have clearly visible borders (min 2px solid)",
            "Button text must be bold (font-weight 700+)",
            "Minimum button height of 44px for touch accessibility",
            "Focus states must use a visible 3px ring in the brand color",
            "Button colors must meet WCAG AA contrast ratio (4.5:1)",
            "Hover states must provide clear visual feedback (not just cursor change)",
        ],
        "compatible_with": "all",  # works with all base styles
        "conflicts_with": [],
    },
    {
        "id": "large-touch-targets",
        "name": "Large Touch Targets",
        "description": (
            "Ensures all interactive elements meet 48px minimum touch target size. "
            "Increases padding, spacing, and tap areas throughout the interface."
        ),
        "category": "accessibility",
        "icon": "pointer",
        "token_overrides": {
            "buttons": {"min_height": "48px", "padding": "14px 28px"},
            "inputs": {"min_height": "48px", "padding": "14px 18px"},
            "spacing": {"card_gap": "24px", "section_gap": "48px"},
            "links": {"min_height": "44px", "padding": "8px 4px"},
        },
        "prompt_additions": [
            "All interactive elements (buttons, links, inputs, toggles) must have a minimum 48x48px touch target",
            "Add extra padding to clickable elements to meet touch target requirements",
            "Space interactive elements at least 16px apart to prevent accidental taps",
            "Checkbox and radio button touch targets must extend beyond the visible element",
            "Navigation items must be large enough to tap easily on mobile devices",
        ],
        "compatible_with": "all",
        "conflicts_with": [],
    },
    {
        "id": "high-contrast-text",
        "name": "High Contrast Text",
        "description": (
            "Ensures all text meets WCAG AAA (7:1) contrast ratio. "
            "Increases font weight and avoids light gray text on white backgrounds."
        ),
        "category": "accessibility",
        "icon": "type",
        "token_overrides": {
            "text": {
                "primary_min_contrast": "7:1 (WCAG AAA)",
                "secondary_min_contrast": "4.5:1 (WCAG AA)",
                "body_weight": 500,
                "small_text_weight": 600,
            }
        },
        "prompt_additions": [
            "All body text must meet WCAG AAA contrast ratio (7:1 against background)",
            "Secondary/muted text must meet at least WCAG AA (4.5:1)",
            "Never use light gray (#9CA3AF or lighter) text on white backgrounds",
            "Body text weight should be 500+ (medium), not 400 (regular)",
            "Small text (12px and below) must use font-weight 600+",
            "Placeholder text must meet 3:1 contrast minimum",
        ],
        "compatible_with": "all",
        "conflicts_with": [],
    },
    {
        "id": "larger-type",
        "name": "Larger Type Scale",
        "description": (
            "Increases base font size to 18px+ and scales all typography up. "
            "Better readability for users with low vision or reading from a distance."
        ),
        "category": "accessibility",
        "icon": "a-large-small",
        "token_overrides": {
            "typography": {
                "base_size": "18px",
                "body_line_height": 1.8,
                "min_font_size": "16px",
                "heading_scale_factor": 1.15,
            }
        },
        "prompt_additions": [
            "Base body font size must be 18px minimum (not 14px or 16px)",
            "No text in the app should be smaller than 16px",
            "Line height for body text must be at least 1.8 for readability",
            "Heading sizes should scale up proportionally (multiply base scale by 1.15x)",
            "Labels and captions should be 16px minimum with 600+ weight",
            "Ensure text containers allow for the larger type without overflow",
        ],
        "compatible_with": "all",
        "conflicts_with": [],
    },
]


def get_modifier_registry(include_tokens: bool = False) -> list[dict]:
    """Return all available style modifiers.

    Args:
        include_tokens: If True, include the full token_overrides dict for
            each modifier. Used by the live preview engine to apply modifier
            effects visually.

    Returns a list suitable for API responses. By default omits
    the full token_overrides and prompt_additions for performance.
    """
    result = []
    for m in STYLE_MODIFIERS:
        entry: dict = {
            "id": m["id"],
            "name": m["name"],
            "description": m["description"],
            "category": m["category"],
            "icon": m["icon"],
        }
        if include_tokens:
            entry["token_overrides"] = m.get("token_overrides", {})
        result.append(entry)
    return result


def get_modifier(modifier_id: str) -> dict | None:
    """Find a specific modifier by ID.

    Args:
        modifier_id: The unique identifier of the modifier to look up.

    Returns:
        The full modifier dict, or None if not found.
    """
    for m in STYLE_MODIFIERS:
        if m["id"] == modifier_id:
            return m
    return None


def get_modifier_prompt_additions(modifier_ids: list[str]) -> str:
    """Generate prompt content for active modifiers.

    Builds a markdown section listing all active modifier rules
    that the agent must follow on top of the base style.

    Args:
        modifier_ids: List of modifier IDs that are currently active.

    Returns:
        A markdown string with accessibility override rules, or
        empty string if no valid modifiers are active.
    """
    if not modifier_ids:
        return ""

    sections = []
    for mid in modifier_ids:
        mod = get_modifier(mid)
        if not mod:
            logger.warning("Skipping unknown modifier ID: %s", mid)
            continue
        rules = "\n".join(f"- {rule}" for rule in mod["prompt_additions"])
        sections.append(f"### {mod['name']}\n{rules}")

    if not sections:
        return ""

    return (
        "\n## ACCESSIBILITY MODIFIERS\n\n"
        "The following accessibility requirements OVERRIDE base style defaults where they conflict:\n\n"
        + "\n\n".join(sections)
        + "\n"
    )


def validate_modifiers(modifier_ids: list[str]) -> tuple[bool, str]:
    """Validate a list of modifier IDs.

    Checks that all IDs exist, no more than 3 are active, and
    there are no conflicts between selected modifiers.

    Args:
        modifier_ids: List of modifier IDs to validate.

    Returns:
        A tuple of (is_valid, error_message). error_message is empty
        when is_valid is True.
    """
    if len(modifier_ids) > 3:
        return False, "Maximum 3 modifiers can be active at once"

    # Check all IDs exist
    valid_ids = {m["id"] for m in STYLE_MODIFIERS}
    invalid = [mid for mid in modifier_ids if mid not in valid_ids]
    if invalid:
        return False, f"Unknown modifier IDs: {', '.join(invalid)}"

    # Check for conflicts between selected modifiers
    active_mods = [get_modifier(mid) for mid in modifier_ids]
    for mod in active_mods:
        if mod and mod["conflicts_with"]:
            conflicts = set(mod["conflicts_with"]) & set(modifier_ids)
            if conflicts:
                return False, f"Modifier '{mod['id']}' conflicts with: {', '.join(conflicts)}"

    return True, ""
