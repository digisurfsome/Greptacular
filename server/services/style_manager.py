"""
UI Style Manager
================

Manages the UI design style registry for the project creation flow.
Each style includes a complete Tailwind CSS theme configuration,
typography specs, component patterns, and audience matching metadata.

Integrates the "Visual DNA" style guide generator approach from
Idea Code methodology - extracting reusable design tokens and
component patterns for each style system.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Audience Matching Logic
# =============================================================================

AUDIENCE_PROFILES = {
    "health_50plus": {
        "label": "Health-conscious / 50+",
        "recommended": ["minimalism", "neumorphism"],
        "avoid": ["neubrutalism", "cyberpunk"],
    },
    "young_edgy": {
        "label": "Young / Edgy / Gen Z",
        "recommended": ["neubrutalism", "cyberpunk", "retro-futurism"],
        "avoid": ["skeuomorphism"],
    },
    "premium_luxury": {
        "label": "Premium / Luxury",
        "recommended": ["minimalism", "glassmorphism"],
        "avoid": ["flat-design"],
    },
    "friendly_approachable": {
        "label": "Friendly / Approachable",
        "recommended": ["claymorphism", "flat-design"],
        "avoid": ["cyberpunk", "neubrutalism"],
    },
    "finance_dashboard": {
        "label": "Finance / Dashboard",
        "recommended": ["neumorphism", "minimalism"],
        "avoid": ["claymorphism"],
    },
    "gaming_entertainment": {
        "label": "Gaming / Entertainment",
        "recommended": ["retro-futurism", "cyberpunk"],
        "avoid": ["minimalism"],
    },
}

VIBE_PROFILES = {
    "trustworthy": {
        "label": "Trustworthy",
        "boost": ["minimalism", "neumorphism", "flat-design"],
    },
    "fun": {
        "label": "Fun",
        "boost": ["claymorphism", "retro-futurism", "neubrutalism"],
    },
    "modern": {
        "label": "Modern",
        "boost": ["glassmorphism", "minimalism", "cyberpunk"],
    },
    "nostalgic": {
        "label": "Nostalgic",
        "boost": ["skeuomorphism", "retro-futurism", "warmer-shades"],
    },
}

AGE_PROFILES = {
    "under_30": {
        "label": "Under 30",
        "boost": ["neubrutalism", "cyberpunk", "retro-futurism", "glassmorphism"],
    },
    "30_50": {
        "label": "30-50",
        "boost": ["minimalism", "flat-design", "glassmorphism", "neumorphism"],
    },
    "50plus": {
        "label": "50+",
        "boost": ["minimalism", "flat-design", "warmer-shades"],
        "penalize": ["neubrutalism", "cyberpunk"],
    },
}


def recommend_styles(
    audience: str | None = None,
    vibe: str | None = None,
    age_group: str | None = None,
) -> list[dict]:
    """
    Recommend UI styles based on audience, vibe, and age group.

    Returns a ranked list of style IDs with scores and reasons.
    """
    scores: dict[str, float] = {s["id"]: 0.0 for s in STYLE_REGISTRY}
    reasons: dict[str, list[str]] = {s["id"]: [] for s in STYLE_REGISTRY}

    if audience and audience in AUDIENCE_PROFILES:
        profile = AUDIENCE_PROFILES[audience]
        for sid in profile["recommended"]:
            scores[sid] = scores.get(sid, 0) + 3.0
            reasons.setdefault(sid, []).append(f"Recommended for {profile['label']}")
        for sid in profile.get("avoid", []):
            scores[sid] = scores.get(sid, 0) - 2.0
            reasons.setdefault(sid, []).append(f"Not ideal for {profile['label']}")

    if vibe and vibe in VIBE_PROFILES:
        profile = VIBE_PROFILES[vibe]
        for sid in profile["boost"]:
            scores[sid] = scores.get(sid, 0) + 2.0
            reasons.setdefault(sid, []).append(f"Matches '{profile['label']}' vibe")

    if age_group and age_group in AGE_PROFILES:
        profile = AGE_PROFILES[age_group]
        for sid in profile.get("boost", []):
            scores[sid] = scores.get(sid, 0) + 1.5
            reasons.setdefault(sid, []).append(f"Good for {profile['label']} audience")
        for sid in profile.get("penalize", []):
            scores[sid] = scores.get(sid, 0) - 1.5
            reasons.setdefault(sid, []).append(f"Less suitable for {profile['label']}")

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {"style_id": sid, "score": score, "reasons": reasons.get(sid, [])}
        for sid, score in ranked
        if score > 0
    ]


# =============================================================================
# Style Guide Generator Prompt (Mentor's Methodology)
# =============================================================================

STYLE_GUIDE_GENERATOR_PROMPT = """
**Role:** You are an expert Design System Architect and Senior Frontend Engineer.
You specialize in "Atomic Design" principles and creating abstract, reusable component libraries.

**Objective:** Apply the {style_name} design system to this application.
Generate all UI components following these strict design tokens and patterns.

**Strict Constraints:**
1. All colors must use the defined CSS variables / Tailwind tokens below.
2. All components must follow the specified border-radius, shadow, and spacing rules.
3. Typography must use the defined font family and size hierarchy.
4. Never deviate from the style system - consistency is the #1 priority.

{style_sheet}

**Implementation Rules:**
- Use Tailwind CSS utility classes mapped to the theme extension below.
- Every component must reference the design tokens, never hardcoded values.
- Cards, buttons, inputs, and icons must follow the component patterns exactly.
- Maintain the specified density (cozy vs compact) across all layouts.
- Use the spacing scale consistently (base unit defined in the style guide).
"""


# =============================================================================
# Complete Style Registry
# =============================================================================

STYLE_REGISTRY: list[dict] = [
    # =========================================================================
    # CORE VISUAL STYLES
    # =========================================================================
    {
        "id": "flat-design",
        "name": "Flat Design",
        "category": "core",
        "description": "Simple 2D, solid colors, clean icons, minimal ornamentation",
        "best_for": "Clarity, scalability, universal appeal",
        "philosophy": "Remove all decorative elements. Every pixel serves a purpose. No gradients, no shadows, no textures - just pure color and form.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#60A5FA", "DEFAULT": "#3B82F6", "dark": "#2563EB"},
                "surface": {"canvas": "#FFFFFF", "base": "#F8FAFC", "muted": "#F1F5F9"},
                "text": {"primary": "#0F172A", "secondary": "#475569", "tertiary": "#94A3B8"},
                "border": {"subtle": "#E2E8F0", "DEFAULT": "#CBD5E1"},
                "status": {"success": "#22C55E", "error": "#EF4444", "warning": "#F59E0B", "info": "#3B82F6"},
            },
            "typography": {
                "font_family": "Inter",
                "hierarchy": [
                    {"level": "Display", "size": "36px", "weight": 700, "line_height": 1.2},
                    {"level": "H1", "size": "28px", "weight": 600, "line_height": 1.3},
                    {"level": "H2", "size": "22px", "weight": 600, "line_height": 1.35},
                    {"level": "H3", "size": "18px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid border-subtle",
                    "radius": "8px",
                    "shadow": "none",
                    "padding": "16px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "6px",
                    "padding": "10px 20px",
                    "hover": "brand-dark",
                },
                "inputs": {
                    "background": "surface-canvas",
                    "border": "1px solid border-DEFAULT",
                    "radius": "6px",
                    "padding": "10px 12px",
                },
                "icons": {"style": "Line/stroke, 1.5px, rounded caps", "size": "20px"},
            },
            "spacing": {
                "base_unit": "4px",
                "density": "Balanced",
                "card_gap": "16px",
                "section_gap": "24px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#60A5FA", "DEFAULT": "#3B82F6", "dark": "#2563EB"},
                    "surface": {"canvas": "#FFFFFF", "base": "#F8FAFC", "muted": "#F1F5F9"},
                    "text": {"primary": "#0F172A", "secondary": "#475569", "tertiary": "#94A3B8"},
                    "border": {"subtle": "#E2E8F0"},
                },
                "fontFamily": {"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "8px", "input": "6px", "btn": "6px"},
                "boxShadow": {"card": "none"},
            },
        },
    },
    {
        "id": "minimalism",
        "name": "Minimalism",
        "category": "core",
        "description": "Clean, white space, essential elements only, Apple-inspired",
        "best_for": "Premium feel, Apple-style elegance, professional apps",
        "philosophy": "Less is more. Every element earns its place. Generous whitespace creates hierarchy. Subtle details over bold statements.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#E5E7EB", "DEFAULT": "#111827", "dark": "#030712"},
                "surface": {"canvas": "#FFFFFF", "base": "#FFFFFF", "muted": "#F9FAFB"},
                "text": {"primary": "#111827", "secondary": "#6B7280", "tertiary": "#9CA3AF"},
                "border": {"subtle": "#F3F4F6", "DEFAULT": "#E5E7EB"},
                "status": {"success": "#10B981", "error": "#EF4444", "warning": "#F59E0B", "info": "#6366F1"},
            },
            "typography": {
                "font_family": "SF Pro Display, Inter",
                "hierarchy": [
                    {"level": "Display", "size": "48px", "weight": 600, "line_height": 1.1},
                    {"level": "H1", "size": "32px", "weight": 600, "line_height": 1.2},
                    {"level": "H2", "size": "24px", "weight": 500, "line_height": 1.3},
                    {"level": "H3", "size": "18px", "weight": 500, "line_height": 1.4},
                    {"level": "Body", "size": "15px", "weight": 400, "line_height": 1.7},
                    {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid border-subtle",
                    "radius": "12px",
                    "shadow": "0 1px 3px rgba(0,0,0,0.04)",
                    "padding": "24px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "10px",
                    "padding": "12px 24px",
                    "hover": "brand-dark",
                },
                "inputs": {
                    "background": "surface-muted",
                    "border": "none",
                    "radius": "10px",
                    "padding": "12px 16px",
                },
                "icons": {"style": "Thin stroke, 1px, rounded caps", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Cozy (generous whitespace)",
                "card_gap": "24px",
                "section_gap": "48px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#E5E7EB", "DEFAULT": "#111827", "dark": "#030712"},
                    "surface": {"canvas": "#FFFFFF", "base": "#FFFFFF", "muted": "#F9FAFB"},
                    "text": {"primary": "#111827", "secondary": "#6B7280", "tertiary": "#9CA3AF"},
                    "border": {"subtle": "#F3F4F6"},
                },
                "fontFamily": {"sans": ["'SF Pro Display'", "Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "12px", "input": "10px", "btn": "10px"},
                "boxShadow": {"card": "0 1px 3px rgba(0,0,0,0.04)"},
            },
        },
    },
    {
        "id": "neumorphism",
        "name": "Neumorphism",
        "category": "core",
        "description": "Soft shadows, embossed/extruded look, tactile feel",
        "best_for": "Finance apps, dashboards, toggles, premium tools",
        "philosophy": "Simulate soft, physical surfaces using dual shadows (light and dark). Elements appear pressed into or extruded from the background. Same background color for everything - depth comes from shadows only.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#818CF8", "DEFAULT": "#6366F1", "dark": "#4F46E5"},
                "surface": {"canvas": "#E0E5EC", "base": "#E0E5EC", "muted": "#D1D9E6"},
                "text": {"primary": "#2D3748", "secondary": "#5A6578", "tertiary": "#8A95A5"},
                "border": {"subtle": "transparent", "DEFAULT": "transparent"},
                "status": {"success": "#48BB78", "error": "#F56565", "warning": "#ECC94B", "info": "#63B3ED"},
            },
            "typography": {
                "font_family": "Inter",
                "hierarchy": [
                    {"level": "Display", "size": "32px", "weight": 700, "line_height": 1.2},
                    {"level": "H1", "size": "26px", "weight": 600, "line_height": 1.3},
                    {"level": "H2", "size": "20px", "weight": 600, "line_height": 1.35},
                    {"level": "H3", "size": "16px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 500, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "none",
                    "radius": "16px",
                    "shadow": "8px 8px 16px #b8bec7, -8px -8px 16px #ffffff",
                    "padding": "24px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "12px",
                    "padding": "12px 24px",
                    "hover": "inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff",
                },
                "inputs": {
                    "background": "surface-base",
                    "border": "none",
                    "radius": "12px",
                    "padding": "12px 16px",
                    "shadow": "inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff",
                },
                "icons": {"style": "Line/stroke, 1.5px, rounded caps", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Cozy (elements need breathing room for shadows)",
                "card_gap": "24px",
                "section_gap": "40px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#818CF8", "DEFAULT": "#6366F1", "dark": "#4F46E5"},
                    "surface": {"canvas": "#E0E5EC", "base": "#E0E5EC", "muted": "#D1D9E6"},
                    "text": {"primary": "#2D3748", "secondary": "#5A6578", "tertiary": "#8A95A5"},
                    "border": {"subtle": "transparent"},
                },
                "fontFamily": {"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "16px", "input": "12px", "btn": "12px"},
                "boxShadow": {
                    "card": "8px 8px 16px #b8bec7, -8px -8px 16px #ffffff",
                    "card-inset": "inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff",
                    "btn": "4px 4px 8px #b8bec7, -4px -4px 8px #ffffff",
                    "btn-pressed": "inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff",
                },
            },
        },
    },
    {
        "id": "glassmorphism",
        "name": "Glassmorphism",
        "category": "core",
        "description": "Frosted glass, translucent layers, blur effects, layered depth",
        "best_for": "Modern, futuristic, layered interfaces, premium dashboards",
        "philosophy": "Create depth through translucency. Frosted glass panels float above colorful backgrounds. Subtle borders catch light. Background blur creates physical depth.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#C084FC", "DEFAULT": "#A855F7", "dark": "#7C3AED"},
                "surface": {
                    "canvas": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "base": "rgba(255, 255, 255, 0.15)",
                    "muted": "rgba(255, 255, 255, 0.08)",
                },
                "text": {"primary": "#FFFFFF", "secondary": "rgba(255,255,255,0.8)", "tertiary": "rgba(255,255,255,0.5)"},
                "border": {"subtle": "rgba(255,255,255,0.18)", "DEFAULT": "rgba(255,255,255,0.25)"},
                "status": {"success": "#4ADE80", "error": "#FB7185", "warning": "#FBBF24", "info": "#60A5FA"},
            },
            "typography": {
                "font_family": "Inter",
                "hierarchy": [
                    {"level": "Display", "size": "36px", "weight": 700, "line_height": 1.2},
                    {"level": "H1", "size": "28px", "weight": 600, "line_height": 1.3},
                    {"level": "H2", "size": "22px", "weight": 600, "line_height": 1.35},
                    {"level": "H3", "size": "17px", "weight": 500, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "rgba(255, 255, 255, 0.15)",
                    "border": "1px solid rgba(255,255,255,0.18)",
                    "radius": "16px",
                    "shadow": "0 8px 32px rgba(0,0,0,0.12)",
                    "padding": "24px",
                    "backdrop_filter": "blur(12px) saturate(180%)",
                },
                "buttons": {
                    "primary_bg": "rgba(255,255,255,0.2)",
                    "primary_text": "#FFFFFF",
                    "radius": "12px",
                    "padding": "12px 24px",
                    "hover": "rgba(255,255,255,0.3)",
                    "backdrop_filter": "blur(8px)",
                },
                "inputs": {
                    "background": "rgba(255,255,255,0.08)",
                    "border": "1px solid rgba(255,255,255,0.15)",
                    "radius": "12px",
                    "padding": "12px 16px",
                },
                "icons": {"style": "Line/stroke, 1.5px, rounded caps, white", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Cozy",
                "card_gap": "20px",
                "section_gap": "40px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#C084FC", "DEFAULT": "#A855F7", "dark": "#7C3AED"},
                    "surface": {"canvas": "#4C1D95", "base": "rgba(255,255,255,0.15)", "muted": "rgba(255,255,255,0.08)"},
                    "text": {"primary": "#FFFFFF", "secondary": "rgba(255,255,255,0.8)", "tertiary": "rgba(255,255,255,0.5)"},
                    "border": {"subtle": "rgba(255,255,255,0.18)"},
                },
                "fontFamily": {"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "16px", "input": "12px", "btn": "12px"},
                "boxShadow": {"card": "0 8px 32px rgba(0,0,0,0.12)"},
                "backdropBlur": {"glass": "12px"},
            },
        },
    },
    {
        "id": "skeuomorphism",
        "name": "Skeuomorphism",
        "category": "core",
        "description": "Realistic textures, mimics physical objects, familiar and intuitive",
        "best_for": "Familiar, intuitive apps, nostalgic feel, older audiences",
        "philosophy": "Digital interfaces should reference real-world materials. Buttons look pressable, cards look like paper, toggles look like physical switches. Textures, gradients, and realistic shadows create familiarity.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#60A5FA", "DEFAULT": "#2563EB", "dark": "#1D4ED8"},
                "surface": {"canvas": "#E8E0D8", "base": "#F5F0EB", "muted": "#E0D8CF"},
                "text": {"primary": "#1A1A1A", "secondary": "#4A4A4A", "tertiary": "#8A8A8A"},
                "border": {"subtle": "#C4B8AB", "DEFAULT": "#A89888"},
                "status": {"success": "#22A559", "error": "#DC3545", "warning": "#FFC107", "info": "#0D6EFD"},
            },
            "typography": {
                "font_family": "Georgia, Palatino",
                "hierarchy": [
                    {"level": "Display", "size": "32px", "weight": 700, "line_height": 1.2},
                    {"level": "H1", "size": "26px", "weight": 700, "line_height": 1.3},
                    {"level": "H2", "size": "20px", "weight": 600, "line_height": 1.35},
                    {"level": "H3", "size": "16px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "11px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "linear-gradient(180deg, #FEFEFE 0%, #F0EBE3 100%)",
                    "border": "1px solid #C4B8AB",
                    "radius": "8px",
                    "shadow": "0 2px 8px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.5)",
                    "padding": "20px",
                },
                "buttons": {
                    "primary_bg": "linear-gradient(180deg, #3B82F6 0%, #1D4ED8 100%)",
                    "primary_text": "#FFFFFF",
                    "radius": "6px",
                    "padding": "10px 20px",
                    "hover": "linear-gradient(180deg, #60A5FA 0%, #2563EB 100%)",
                    "shadow": "0 2px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3)",
                },
                "inputs": {
                    "background": "#FFFFFF",
                    "border": "1px solid #A89888",
                    "radius": "4px",
                    "padding": "10px 12px",
                    "shadow": "inset 0 2px 4px rgba(0,0,0,0.08)",
                },
                "icons": {"style": "Solid filled, detailed, with subtle gradients", "size": "22px"},
            },
            "spacing": {
                "base_unit": "4px",
                "density": "Balanced to Compact",
                "card_gap": "16px",
                "section_gap": "32px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#60A5FA", "DEFAULT": "#2563EB", "dark": "#1D4ED8"},
                    "surface": {"canvas": "#E8E0D8", "base": "#F5F0EB", "muted": "#E0D8CF"},
                    "text": {"primary": "#1A1A1A", "secondary": "#4A4A4A", "tertiary": "#8A8A8A"},
                    "border": {"subtle": "#C4B8AB"},
                },
                "fontFamily": {"sans": ["Georgia", "'Palatino Linotype'", "Palatino", "serif"]},
                "borderRadius": {"card": "8px", "input": "4px", "btn": "6px"},
                "boxShadow": {
                    "card": "0 2px 8px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.5)",
                    "btn": "0 2px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3)",
                    "input-inset": "inset 0 2px 4px rgba(0,0,0,0.08)",
                },
            },
        },
    },
    {
        "id": "neubrutalism",
        "name": "Neubrutalism",
        "category": "core",
        "description": "Bold, raw, heavy outlines, clashing colors, unapologetically loud",
        "best_for": "Gen Z, edgy brands, standout apps, creative tools",
        "philosophy": "Reject polish. Embrace rawness. Thick black borders, stark shadows, clashing colors that demand attention. Anti-corporate, anti-minimalist. Digital punk.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#FDE68A", "DEFAULT": "#FACC15", "dark": "#EAB308"},
                "surface": {"canvas": "#FFFBEB", "base": "#FFFFFF", "muted": "#FEF3C7"},
                "text": {"primary": "#18181B", "secondary": "#3F3F46", "tertiary": "#71717A"},
                "border": {"subtle": "#18181B", "DEFAULT": "#18181B"},
                "status": {"success": "#22C55E", "error": "#EF4444", "warning": "#F97316", "info": "#3B82F6"},
            },
            "typography": {
                "font_family": "Space Grotesk, DM Sans",
                "hierarchy": [
                    {"level": "Display", "size": "42px", "weight": 800, "line_height": 1.1},
                    {"level": "H1", "size": "32px", "weight": 700, "line_height": 1.2},
                    {"level": "H2", "size": "24px", "weight": 700, "line_height": 1.3},
                    {"level": "H3", "size": "18px", "weight": 700, "line_height": 1.4},
                    {"level": "Body", "size": "15px", "weight": 500, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 600, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "3px solid #18181B",
                    "radius": "0px",
                    "shadow": "6px 6px 0px #18181B",
                    "padding": "20px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#18181B",
                    "radius": "0px",
                    "padding": "12px 24px",
                    "hover": "translate(-2px, -2px) with larger shadow",
                    "border": "3px solid #18181B",
                    "shadow": "4px 4px 0px #18181B",
                },
                "inputs": {
                    "background": "#FFFFFF",
                    "border": "3px solid #18181B",
                    "radius": "0px",
                    "padding": "12px 14px",
                },
                "icons": {"style": "Bold stroke, 2px+, sharp edges", "size": "22px"},
            },
            "spacing": {
                "base_unit": "4px",
                "density": "Balanced (elements need room for thick borders/shadows)",
                "card_gap": "20px",
                "section_gap": "36px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#FDE68A", "DEFAULT": "#FACC15", "dark": "#EAB308"},
                    "surface": {"canvas": "#FFFBEB", "base": "#FFFFFF", "muted": "#FEF3C7"},
                    "text": {"primary": "#18181B", "secondary": "#3F3F46", "tertiary": "#71717A"},
                    "border": {"subtle": "#18181B"},
                },
                "fontFamily": {"sans": ["'Space Grotesk'", "'DM Sans'", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "0px", "input": "0px", "btn": "0px"},
                "boxShadow": {
                    "card": "6px 6px 0px #18181B",
                    "btn": "4px 4px 0px #18181B",
                    "btn-hover": "6px 6px 0px #18181B",
                },
            },
        },
    },
    {
        "id": "bauhaus",
        "name": "Bauhaus",
        "category": "core",
        "description": "Geometric shapes, primary colors, grid-based, form follows function",
        "best_for": "Artistic, balanced, timeless design, creative portfolios",
        "philosophy": "Art meets function. Primary colors (red, blue, yellow) + black/white. Strong geometric shapes - circles, squares, triangles. Strict grid alignment. The Bauhaus school belief: form follows function.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#FCA5A5", "DEFAULT": "#DC2626", "dark": "#991B1B"},
                "accent_blue": "#2563EB",
                "accent_yellow": "#FACC15",
                "surface": {"canvas": "#FAFAFA", "base": "#FFFFFF", "muted": "#F5F5F5"},
                "text": {"primary": "#0A0A0A", "secondary": "#404040", "tertiary": "#737373"},
                "border": {"subtle": "#E5E5E5", "DEFAULT": "#0A0A0A"},
                "status": {"success": "#22C55E", "error": "#DC2626", "warning": "#FACC15", "info": "#2563EB"},
            },
            "typography": {
                "font_family": "DM Sans, Helvetica Neue",
                "hierarchy": [
                    {"level": "Display", "size": "48px", "weight": 700, "line_height": 1.1},
                    {"level": "H1", "size": "36px", "weight": 700, "line_height": 1.2},
                    {"level": "H2", "size": "24px", "weight": 500, "line_height": 1.3},
                    {"level": "H3", "size": "18px", "weight": 500, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "11px", "weight": 500, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "2px solid #0A0A0A",
                    "radius": "0px",
                    "shadow": "none",
                    "padding": "24px",
                },
                "buttons": {
                    "primary_bg": "#DC2626",
                    "primary_text": "#FFFFFF",
                    "radius": "0px",
                    "padding": "12px 28px",
                    "hover": "#991B1B",
                    "border": "2px solid #0A0A0A",
                },
                "inputs": {
                    "background": "#FFFFFF",
                    "border": "2px solid #0A0A0A",
                    "radius": "0px",
                    "padding": "10px 14px",
                },
                "icons": {"style": "Geometric, sharp edges, monoline", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Structured (grid-based rhythm)",
                "card_gap": "24px",
                "section_gap": "48px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#FCA5A5", "DEFAULT": "#DC2626", "dark": "#991B1B"},
                    "accent": {"blue": "#2563EB", "yellow": "#FACC15"},
                    "surface": {"canvas": "#FAFAFA", "base": "#FFFFFF", "muted": "#F5F5F5"},
                    "text": {"primary": "#0A0A0A", "secondary": "#404040", "tertiary": "#737373"},
                    "border": {"subtle": "#E5E5E5"},
                },
                "fontFamily": {"sans": ["'DM Sans'", "'Helvetica Neue'", "Helvetica", "ui-sans-serif", "sans-serif"]},
                "borderRadius": {"card": "0px", "input": "0px", "btn": "0px"},
                "boxShadow": {"card": "none"},
            },
        },
    },
    {
        "id": "claymorphism",
        "name": "Claymorphism",
        "category": "core",
        "description": "Soft, rounded, clay-like, hand-sculpted feel, warm and friendly",
        "best_for": "Warm, friendly, approachable apps, kids, wellness",
        "philosophy": "Everything looks like soft clay or play-doh. Inner shadows create a pillowy, 3D appearance. Pastel colors, extremely rounded corners, soft edges. Makes digital feel handmade and inviting.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#FDE68A", "DEFAULT": "#F59E0B", "dark": "#D97706"},
                "surface": {"canvas": "#FFF7ED", "base": "#FFFFFF", "muted": "#FEF3E2"},
                "text": {"primary": "#292524", "secondary": "#57534E", "tertiary": "#A8A29E"},
                "border": {"subtle": "rgba(0,0,0,0.05)", "DEFAULT": "rgba(0,0,0,0.08)"},
                "status": {"success": "#4ADE80", "error": "#FB7185", "warning": "#FBBF24", "info": "#60A5FA"},
            },
            "typography": {
                "font_family": "Nunito, Quicksand",
                "hierarchy": [
                    {"level": "Display", "size": "34px", "weight": 800, "line_height": 1.2},
                    {"level": "H1", "size": "26px", "weight": 700, "line_height": 1.3},
                    {"level": "H2", "size": "20px", "weight": 700, "line_height": 1.35},
                    {"level": "H3", "size": "16px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 500, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 600, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "none",
                    "radius": "24px",
                    "shadow": "0 8px 30px rgba(0,0,0,0.06), inset 0 -4px 8px rgba(0,0,0,0.04), inset 0 4px 8px rgba(255,255,255,0.8)",
                    "padding": "24px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "20px",
                    "padding": "14px 28px",
                    "hover": "brand-dark",
                    "shadow": "0 4px 12px rgba(245,158,11,0.3), inset 0 -2px 4px rgba(0,0,0,0.1), inset 0 2px 4px rgba(255,255,255,0.3)",
                },
                "inputs": {
                    "background": "surface-muted",
                    "border": "none",
                    "radius": "16px",
                    "padding": "14px 18px",
                    "shadow": "inset 0 2px 6px rgba(0,0,0,0.06)",
                },
                "icons": {"style": "Rounded, soft, filled with subtle gradients", "size": "22px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Cozy (extra padding for soft feel)",
                "card_gap": "20px",
                "section_gap": "40px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#FDE68A", "DEFAULT": "#F59E0B", "dark": "#D97706"},
                    "surface": {"canvas": "#FFF7ED", "base": "#FFFFFF", "muted": "#FEF3E2"},
                    "text": {"primary": "#292524", "secondary": "#57534E", "tertiary": "#A8A29E"},
                    "border": {"subtle": "rgba(0,0,0,0.05)"},
                },
                "fontFamily": {"sans": ["Nunito", "Quicksand", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "24px", "input": "16px", "btn": "20px"},
                "boxShadow": {
                    "card": "0 8px 30px rgba(0,0,0,0.06), inset 0 -4px 8px rgba(0,0,0,0.04), inset 0 4px 8px rgba(255,255,255,0.8)",
                    "btn": "0 4px 12px rgba(245,158,11,0.3), inset 0 -2px 4px rgba(0,0,0,0.1), inset 0 2px 4px rgba(255,255,255,0.3)",
                },
            },
        },
    },
    # =========================================================================
    # VIBE / AESTHETIC STYLES
    # =========================================================================
    {
        "id": "retro-futurism",
        "name": "Retro Futurism",
        "category": "vibe",
        "description": "Neon + vintage, 80s/90s nostalgia, arcade vibes, synthwave",
        "best_for": "Gaming, entertainment, fun/creative apps",
        "philosophy": "The future as imagined in the past. Neon glows against dark backgrounds. Grid lines fade into horizons. Chrome text reflects impossible sunsets. VHS tracking lines and CRT scan lines add analog warmth to digital.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#F0ABFC", "DEFAULT": "#D946EF", "dark": "#A21CAF"},
                "accent": {"cyan": "#06B6D4", "orange": "#F97316", "pink": "#EC4899"},
                "surface": {"canvas": "#0C0A1A", "base": "#1A1730", "muted": "#252040"},
                "text": {"primary": "#F5F3FF", "secondary": "#C4B5FD", "tertiary": "#7C3AED"},
                "border": {"subtle": "rgba(217,70,239,0.2)", "DEFAULT": "rgba(217,70,239,0.4)"},
                "status": {"success": "#4ADE80", "error": "#FB7185", "warning": "#FBBF24", "info": "#06B6D4"},
            },
            "typography": {
                "font_family": "Orbitron, Space Mono",
                "hierarchy": [
                    {"level": "Display", "size": "40px", "weight": 800, "line_height": 1.1},
                    {"level": "H1", "size": "30px", "weight": 700, "line_height": 1.2},
                    {"level": "H2", "size": "22px", "weight": 600, "line_height": 1.3},
                    {"level": "H3", "size": "16px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "11px", "weight": 500, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid rgba(217,70,239,0.3)",
                    "radius": "8px",
                    "shadow": "0 0 20px rgba(217,70,239,0.15), inset 0 1px 0 rgba(255,255,255,0.05)",
                    "padding": "20px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "4px",
                    "padding": "12px 24px",
                    "hover": "brand-light with glow",
                    "shadow": "0 0 12px rgba(217,70,239,0.4)",
                },
                "inputs": {
                    "background": "rgba(255,255,255,0.05)",
                    "border": "1px solid rgba(217,70,239,0.3)",
                    "radius": "4px",
                    "padding": "10px 14px",
                },
                "icons": {"style": "Line/stroke, 1.5px, neon glow effect", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Balanced",
                "card_gap": "20px",
                "section_gap": "36px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#F0ABFC", "DEFAULT": "#D946EF", "dark": "#A21CAF"},
                    "accent": {"cyan": "#06B6D4", "orange": "#F97316", "pink": "#EC4899"},
                    "surface": {"canvas": "#0C0A1A", "base": "#1A1730", "muted": "#252040"},
                    "text": {"primary": "#F5F3FF", "secondary": "#C4B5FD", "tertiary": "#7C3AED"},
                    "border": {"subtle": "rgba(217,70,239,0.2)"},
                },
                "fontFamily": {"sans": ["Orbitron", "'Space Mono'", "ui-monospace", "monospace"]},
                "borderRadius": {"card": "8px", "input": "4px", "btn": "4px"},
                "boxShadow": {
                    "card": "0 0 20px rgba(217,70,239,0.15)",
                    "neon": "0 0 12px rgba(217,70,239,0.4)",
                    "neon-cyan": "0 0 12px rgba(6,182,212,0.4)",
                },
            },
        },
    },
    {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "category": "vibe",
        "description": "Neon, dark, glowing, dystopian, high-tech low-life",
        "best_for": "Tech-forward, gaming, edgy brands, developer tools",
        "philosophy": "High-tech meets underground. Neon accents bleed through dark surfaces. Glitched elements, scan lines, monospaced type. Everything looks like it was hacked together in a rain-soaked megacity.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#67E8F9", "DEFAULT": "#06B6D4", "dark": "#0891B2"},
                "accent": {"green": "#22D3EE", "red": "#F43F5E", "yellow": "#FBBF24"},
                "surface": {"canvas": "#09090B", "base": "#18181B", "muted": "#27272A"},
                "text": {"primary": "#FAFAFA", "secondary": "#A1A1AA", "tertiary": "#52525B"},
                "border": {"subtle": "#27272A", "DEFAULT": "#3F3F46"},
                "status": {"success": "#22D3EE", "error": "#F43F5E", "warning": "#FBBF24", "info": "#06B6D4"},
            },
            "typography": {
                "font_family": "JetBrains Mono, Fira Code",
                "hierarchy": [
                    {"level": "Display", "size": "36px", "weight": 800, "line_height": 1.1},
                    {"level": "H1", "size": "28px", "weight": 700, "line_height": 1.2},
                    {"level": "H2", "size": "20px", "weight": 600, "line_height": 1.3},
                    {"level": "H3", "size": "16px", "weight": 600, "line_height": 1.4},
                    {"level": "Body", "size": "13px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "11px", "weight": 500, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid #3F3F46",
                    "radius": "2px",
                    "shadow": "0 0 16px rgba(6,182,212,0.08)",
                    "padding": "16px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#09090B",
                    "radius": "2px",
                    "padding": "10px 20px",
                    "hover": "brand-light with neon glow",
                    "border": "1px solid brand-DEFAULT",
                },
                "inputs": {
                    "background": "#09090B",
                    "border": "1px solid #3F3F46",
                    "radius": "2px",
                    "padding": "10px 12px",
                },
                "icons": {"style": "Monoline, sharp edges, 1.5px stroke", "size": "18px"},
            },
            "spacing": {
                "base_unit": "4px",
                "density": "Compact (data-dense, terminal-like)",
                "card_gap": "12px",
                "section_gap": "24px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#67E8F9", "DEFAULT": "#06B6D4", "dark": "#0891B2"},
                    "accent": {"green": "#22D3EE", "red": "#F43F5E", "yellow": "#FBBF24"},
                    "surface": {"canvas": "#09090B", "base": "#18181B", "muted": "#27272A"},
                    "text": {"primary": "#FAFAFA", "secondary": "#A1A1AA", "tertiary": "#52525B"},
                    "border": {"subtle": "#27272A"},
                },
                "fontFamily": {"sans": ["'JetBrains Mono'", "'Fira Code'", "ui-monospace", "monospace"]},
                "borderRadius": {"card": "2px", "input": "2px", "btn": "2px"},
                "boxShadow": {
                    "card": "0 0 16px rgba(6,182,212,0.08)",
                    "neon": "0 0 12px rgba(6,182,212,0.5)",
                },
            },
        },
    },
    {
        "id": "dark-mode",
        "name": "Dark Mode Elegant",
        "category": "vibe",
        "description": "Dark backgrounds, reduced eye strain, OLED-friendly, modern",
        "best_for": "Night use, OLED screens, developer tools, media apps",
        "philosophy": "Dark surfaces reduce eye strain and save battery on OLED. Subtle gray gradations create hierarchy without harsh contrasts. Muted colors pop against dark backgrounds. Professional and modern.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#93C5FD", "DEFAULT": "#3B82F6", "dark": "#1D4ED8"},
                "surface": {"canvas": "#0F172A", "base": "#1E293B", "muted": "#334155"},
                "text": {"primary": "#F1F5F9", "secondary": "#94A3B8", "tertiary": "#64748B"},
                "border": {"subtle": "#1E293B", "DEFAULT": "#334155"},
                "status": {"success": "#4ADE80", "error": "#FB7185", "warning": "#FBBF24", "info": "#60A5FA"},
            },
            "typography": {
                "font_family": "Inter",
                "hierarchy": [
                    {"level": "Display", "size": "36px", "weight": 700, "line_height": 1.2},
                    {"level": "H1", "size": "28px", "weight": 600, "line_height": 1.3},
                    {"level": "H2", "size": "22px", "weight": 600, "line_height": 1.35},
                    {"level": "H3", "size": "17px", "weight": 500, "line_height": 1.4},
                    {"level": "Body", "size": "14px", "weight": 400, "line_height": 1.6},
                    {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid #334155",
                    "radius": "12px",
                    "shadow": "0 4px 16px rgba(0,0,0,0.3)",
                    "padding": "20px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "8px",
                    "padding": "10px 22px",
                    "hover": "brand-light",
                },
                "inputs": {
                    "background": "#0F172A",
                    "border": "1px solid #334155",
                    "radius": "8px",
                    "padding": "10px 14px",
                },
                "icons": {"style": "Line/stroke, 1.5px, rounded caps", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Balanced",
                "card_gap": "16px",
                "section_gap": "32px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#93C5FD", "DEFAULT": "#3B82F6", "dark": "#1D4ED8"},
                    "surface": {"canvas": "#0F172A", "base": "#1E293B", "muted": "#334155"},
                    "text": {"primary": "#F1F5F9", "secondary": "#94A3B8", "tertiary": "#64748B"},
                    "border": {"subtle": "#1E293B"},
                },
                "fontFamily": {"sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]},
                "borderRadius": {"card": "12px", "input": "8px", "btn": "8px"},
                "boxShadow": {"card": "0 4px 16px rgba(0,0,0,0.3)"},
            },
        },
    },
    {
        "id": "warmer-shades",
        "name": "Warmer Shades",
        "category": "vibe",
        "description": "Cream/off-white backgrounds, warm tones, softer feel",
        "best_for": "Eye comfort, softer feel, wellness, reading apps",
        "philosophy": "Replace harsh whites with warm creams and off-whites. Colors lean warm (amber, terracotta, sage) instead of cool. Creates a comfortable, inviting space that feels like natural light instead of fluorescent.",
        "style_guide": {
            "color_tokens": {
                "brand": {"light": "#FDE68A", "DEFAULT": "#D97706", "dark": "#B45309"},
                "surface": {"canvas": "#FFFBF5", "base": "#FFF8F0", "muted": "#FEF3E2"},
                "text": {"primary": "#292524", "secondary": "#78716C", "tertiary": "#A8A29E"},
                "border": {"subtle": "#F5E6D3", "DEFAULT": "#E7D5C0"},
                "status": {"success": "#65A30D", "error": "#DC2626", "warning": "#D97706", "info": "#2563EB"},
            },
            "typography": {
                "font_family": "Lora, Merriweather",
                "hierarchy": [
                    {"level": "Display", "size": "36px", "weight": 600, "line_height": 1.2},
                    {"level": "H1", "size": "28px", "weight": 600, "line_height": 1.3},
                    {"level": "H2", "size": "22px", "weight": 500, "line_height": 1.35},
                    {"level": "H3", "size": "18px", "weight": 500, "line_height": 1.4},
                    {"level": "Body", "size": "15px", "weight": 400, "line_height": 1.7},
                    {"level": "Micro", "size": "12px", "weight": 400, "line_height": 1.5},
                ],
            },
            "components": {
                "cards": {
                    "background": "surface-base",
                    "border": "1px solid #F5E6D3",
                    "radius": "12px",
                    "shadow": "0 2px 8px rgba(140,100,60,0.06)",
                    "padding": "22px",
                },
                "buttons": {
                    "primary_bg": "brand-DEFAULT",
                    "primary_text": "#FFFFFF",
                    "radius": "10px",
                    "padding": "12px 24px",
                    "hover": "brand-dark",
                },
                "inputs": {
                    "background": "#FFFBF5",
                    "border": "1px solid #E7D5C0",
                    "radius": "10px",
                    "padding": "12px 16px",
                },
                "icons": {"style": "Line/stroke, 1.5px, rounded caps, warm tones", "size": "20px"},
            },
            "spacing": {
                "base_unit": "8px",
                "density": "Cozy (warm and relaxed)",
                "card_gap": "20px",
                "section_gap": "40px",
            },
            "tailwind_config": {
                "colors": {
                    "brand": {"light": "#FDE68A", "DEFAULT": "#D97706", "dark": "#B45309"},
                    "surface": {"canvas": "#FFFBF5", "base": "#FFF8F0", "muted": "#FEF3E2"},
                    "text": {"primary": "#292524", "secondary": "#78716C", "tertiary": "#A8A29E"},
                    "border": {"subtle": "#F5E6D3"},
                },
                "fontFamily": {"sans": ["Lora", "Merriweather", "Georgia", "serif"]},
                "borderRadius": {"card": "12px", "input": "10px", "btn": "10px"},
                "boxShadow": {"card": "0 2px 8px rgba(140,100,60,0.06)"},
            },
        },
    },
]


# =============================================================================
# Style Do's and Don'ts (Practical Guidelines for Agents)
# =============================================================================

STYLE_DOS_AND_DONTS: dict[str, dict[str, list[str]]] = {
    "flat-design": {
        "dos": [
            "Use solid, flat colors without gradients or textures",
            "Rely on color contrast and whitespace for visual hierarchy",
            "Keep icons simple, single-weight line or solid fill",
            "Use clear typography hierarchy with consistent weights",
            "Ensure touch targets are obvious through color differentiation",
        ],
        "donts": [
            "Never add drop shadows, embossing, or 3D effects",
            "Avoid gradients on backgrounds, buttons, or cards",
            "Don't use realistic textures or photographic backgrounds",
            "Avoid heavy border styling - use color blocks instead",
            "Don't mix more than 3-4 colors in a single view",
        ],
    },
    "minimalism": {
        "dos": [
            "Use generous whitespace (padding/margins at least 2x what feels 'enough')",
            "Limit each view to one primary action and minimal secondary options",
            "Use subtle, near-invisible borders (1px, low-opacity) or none at all",
            "Stick to a single font family with only 2-3 weight variations",
            "Let content breathe - section gaps should be 40-48px minimum",
        ],
        "donts": [
            "Never crowd the interface with multiple competing CTAs",
            "Avoid saturated or bold accent colors - use muted, desaturated tones",
            "Don't add decorative elements (icons, illustrations) unless essential",
            "Never use more than one box-shadow on the same element",
            "Avoid using colored backgrounds for cards - prefer white or near-white",
        ],
    },
    "neumorphism": {
        "dos": [
            "Always use dual shadows (one light, one dark) for the extruded effect",
            "Keep the background color identical to the card/element color (same surface)",
            "Use inset shadows for pressed/active states and input fields",
            "Maintain generous spacing so shadow pairs don't overlap between elements",
            "Use soft, muted brand colors - neumorphism works best with low saturation",
        ],
        "donts": [
            "Never use flat borders - depth comes exclusively from shadow pairs",
            "Don't place neumorphic elements on different-colored backgrounds",
            "Avoid high-contrast text on neumorphic surfaces - keep it medium contrast",
            "Never stack neumorphic cards on top of other neumorphic cards",
            "Don't use neumorphism for small elements like badges or pills - it gets muddy",
        ],
    },
    "glassmorphism": {
        "dos": [
            "Always apply backdrop-filter: blur() on translucent panels (12-20px blur)",
            "Use a colorful or gradient background behind glass panels so blur is visible",
            "Add subtle white/light border (1px, 15-25% opacity) to catch light on edges",
            "Layer glass panels at different opacity levels to create depth hierarchy",
            "Ensure text on glass panels has sufficient contrast - use text-shadow if needed",
        ],
        "donts": [
            "Never use glassmorphism on a solid white or plain background - it looks broken",
            "Don't make glass panels fully opaque - maintain at least some transparency",
            "Avoid nesting glass panels inside glass panels (blur stacking kills readability)",
            "Don't use glass effects on text-heavy content - body text needs solid backgrounds",
            "Never skip the backdrop-filter - a transparent div without blur is not glassmorphism",
        ],
    },
    "skeuomorphism": {
        "dos": [
            "Use subtle vertical gradients on buttons (lighter top, darker bottom)",
            "Apply inset shadows on inputs to simulate recessed physical fields",
            "Use realistic material textures (paper, leather, metal) for backgrounds",
            "Add inner highlight (inset top border or shadow) to simulate light reflection",
            "Use serif or classic fonts to reinforce the traditional, physical feeling",
        ],
        "donts": [
            "Don't flatten elements - every interactive component needs visible depth cues",
            "Avoid clean, minimal aesthetics - skeuomorphism thrives on visual richness",
            "Never use monospaced or geometric sans-serif fonts - they feel too digital",
            "Don't mix skeuomorphic elements with flat-design components in the same view",
            "Avoid pure white backgrounds - use off-white, cream, or subtle texture",
        ],
    },
    "neubrutalism": {
        "dos": [
            "Use thick black borders (2-3px minimum) on all interactive elements",
            "Apply hard-offset box shadows (e.g., 4px 4px 0px black) instead of soft shadows",
            "Use bold, clashing accent colors (yellow, pink, cyan) against white/cream",
            "Keep border-radius at 0px for the raw, angular aesthetic",
            "Make hover states shift the element position (translate) with shadow changes",
        ],
        "donts": [
            "Never use soft/blurred shadows - all shadows must be hard-edged offset blocks",
            "Don't round corners - neubrutalism demands sharp, angular geometry",
            "Avoid subtle, muted color palettes - colors should be loud and unapologetic",
            "Never use thin (1px) borders - the thick border is a defining characteristic",
            "Don't add smooth transitions longer than 150ms - keep interactions snappy and raw",
        ],
    },
    "bauhaus": {
        "dos": [
            "Restrict the palette to primary colors (red, blue, yellow) plus black and white",
            "Use strong geometric shapes (circles, squares, triangles) as decorative elements",
            "Align everything to a strict grid - asymmetry is intentional, not accidental",
            "Use bold, sans-serif typography with large size contrasts between headings and body",
            "Separate content areas with thick black lines or primary-color blocks",
        ],
        "donts": [
            "Never use gradients, textures, or photographic backgrounds",
            "Don't introduce secondary colors (greens, purples, oranges) into the palette",
            "Avoid rounded corners - Bauhaus uses sharp geometry exclusively",
            "Never add drop shadows or 3D effects - the style is strictly two-dimensional",
            "Don't use decorative or script fonts - only geometric sans-serifs belong here",
        ],
    },
    "claymorphism": {
        "dos": [
            "Use large border-radius values (16-24px) for that soft, rounded clay feel",
            "Apply inner shadows (both top-light and bottom-dark) for the pillowy 3D effect",
            "Choose warm, pastel color palettes (peach, cream, soft amber, blush pink)",
            "Use rounded, friendly fonts with higher-than-normal font weights (500-700)",
            "Add generous padding inside elements (20-28px) to enhance the puffy appearance",
        ],
        "donts": [
            "Never use sharp corners or zero border-radius - everything must feel soft",
            "Don't use dark or moody color schemes - claymorphism is warm and inviting",
            "Avoid hard-edged flat shadows - shadows must be soft with inner-shadow layering",
            "Never use thin, light font weights - they contradict the chunky clay aesthetic",
            "Don't use visible borders on cards - rely on shadow layering for edge definition",
        ],
    },
    "retro-futurism": {
        "dos": [
            "Apply neon glow effects (box-shadow with color spread) on interactive elements",
            "Use dark backgrounds (#0C0A1A range) so neon accents pop with maximum contrast",
            "Mix retro display fonts (Orbitron, Press Start) with monospace body text",
            "Add subtle scan-line or grid-line overlays for CRT/arcade atmosphere",
            "Use gradient color transitions between neon pink, cyan, and purple accents",
        ],
        "donts": [
            "Never use light/white backgrounds - the dark canvas is essential for neon glow",
            "Don't use more than 3 neon accent colors per view (too many glows = visual noise)",
            "Avoid conventional corporate fonts (Inter, Helvetica) - use display/mono fonts",
            "Never apply large border-radius - keep corners tight (4-8px) for a tech feel",
            "Don't use flat, unlit colors for buttons or CTAs - they need glow or gradient",
        ],
    },
    "cyberpunk": {
        "dos": [
            "Use monospaced fonts (JetBrains Mono, Fira Code) for all text, including headings",
            "Keep layouts compact and data-dense, like terminal interfaces",
            "Apply neon accent borders and glows sparingly for a high-tech hacker aesthetic",
            "Use near-black backgrounds (#09090B) with high-contrast neon text accents",
            "Add angular, sharp UI elements with minimal border-radius (0-2px)",
        ],
        "donts": [
            "Never use rounded, friendly designs - cyberpunk is angular and harsh",
            "Don't use warm, pastel, or earth-tone color palettes",
            "Avoid generous whitespace - cyberpunk UIs feel dense and information-packed",
            "Never use serif or handwritten fonts - everything is monospace or geometric sans",
            "Don't apply soft shadows - use hard neon glows or no shadows at all",
        ],
    },
    "dark-mode": {
        "dos": [
            "Use multiple gray surface levels (canvas, base, muted) for layered depth hierarchy",
            "Ensure text contrast ratios meet WCAG AA (4.5:1 for body, 3:1 for large text)",
            "Use slightly desaturated colors for accents - pure saturated hues are harsh on dark",
            "Apply subtle (0.3 opacity) shadows to create layered card elevation",
            "Test all status colors (success, error, warning) for readability on dark surfaces",
        ],
        "donts": [
            "Never use pure black (#000000) as the main background - use dark gray (#0F172A range)",
            "Don't use pure white (#FFFFFF) for body text - use off-white (#F1F5F9) to reduce glare",
            "Avoid high-saturation accent colors that vibrate against dark backgrounds",
            "Never rely on color alone for status indicators - add icons or text labels too",
            "Don't mix warm and cool grays in the surface hierarchy - pick one temperature",
        ],
    },
    "warmer-shades": {
        "dos": [
            "Replace pure whites with cream/off-white tones (#FFFBF5, #FFF8F0)",
            "Use warm accent colors (amber, terracotta, sage, warm gold) instead of cool blues",
            "Choose serif or rounded-serif fonts for a comfortable, literary reading feel",
            "Apply warm-tinted shadows (rgba with amber/brown) instead of pure black shadows",
            "Use generous line-height (1.6-1.7) for body text to enhance readability and calm",
        ],
        "donts": [
            "Never use cool blue or gray as the primary brand color - stay in the warm spectrum",
            "Don't use stark white (#FFFFFF) backgrounds - always shift toward cream/warm white",
            "Avoid high-contrast neon or electric accent colors that clash with warm tones",
            "Never use cold gray text colors - tint grays warm (stone/amber undertone)",
            "Don't use geometric sans-serif fonts (Inter, Helvetica) - prefer serif or soft sans",
        ],
    },
}


# =============================================================================
# Registry Lookup Functions
# =============================================================================


def get_style_registry() -> list[dict]:
    """
    Return the full style registry for the API.

    Returns a list of style objects with id, name, category, description,
    best_for, and philosophy. The full style_guide is included for the
    selected style but omitted from the list view for performance.
    """
    result = []
    for style in STYLE_REGISTRY:
        result.append({
            "id": style["id"],
            "name": style["name"],
            "category": style["category"],
            "description": style["description"],
            "best_for": style["best_for"],
            "philosophy": style["philosophy"],
        })
    return result


def get_style_option(style_id: str) -> dict | None:
    """
    Find and return a specific style by its unique ID.

    Returns the full style object including the style_guide, or None.
    """
    for style in STYLE_REGISTRY:
        if style["id"] == style_id:
            return style
    return None


def get_style_guide_markdown(style_id: str) -> str | None:
    """
    Generate a complete Markdown style guide document for a given style.

    This is used to inject into the spec creation prompt and also
    saved to the project's .autoforge/style_guide.md file.
    """
    style = get_style_option(style_id)
    if not style:
        return None

    guide = style["style_guide"]
    tokens = guide["color_tokens"]
    typo = guide["typography"]
    comps = guide["components"]
    spacing = guide["spacing"]
    tw = guide["tailwind_config"]

    lines = [
        f"# {style['name']} - Design System Style Guide",
        "",
        f"**Philosophy:** {style['philosophy']}",
        "",
        "---",
        "",
        "## 1. Abstract Color Tokens",
        "",
        "**Brand/Primary:**",
        f"- brand-light: {tokens['brand']['light']}",
        f"- brand-DEFAULT: {tokens['brand']['DEFAULT']}",
        f"- brand-dark: {tokens['brand']['dark']}",
        "",
        "**Surfaces:**",
        f"- surface-canvas: {tokens['surface']['canvas']} (main background)",
        f"- surface-base: {tokens['surface']['base']} (cards, panels)",
        f"- surface-muted: {tokens['surface']['muted']} (inputs, hover states)",
        "",
        "**Text:**",
        f"- text-primary: {tokens['text']['primary']} (headings, key values)",
        f"- text-secondary: {tokens['text']['secondary']} (body text, labels)",
        f"- text-tertiary: {tokens['text']['tertiary']} (placeholders, inactive)",
        "",
        "**Borders:**",
        f"- border-subtle: {tokens['border']['subtle']}",
        "",
        "**Status Colors:**",
        f"- success: {tokens['status']['success']}",
        f"- error: {tokens['status']['error']}",
        f"- warning: {tokens['status']['warning']}",
        f"- info: {tokens['status']['info']}",
        "",
    ]

    # Add accent colors if present
    if "accent" in tokens:
        lines.append("**Accent Colors:**")
        if isinstance(tokens["accent"], dict):
            for k, v in tokens["accent"].items():
                lines.append(f"- accent-{k}: {v}")
        lines.append("")

    lines.extend([
        "## 2. Typography System",
        "",
        f"**Font Family:** {typo['font_family']}",
        "",
        "| Level | Size | Weight | Line Height | Usage |",
        "|-------|------|--------|-------------|-------|",
    ])

    usage_map = {
        "Display": "Hero text, large metrics",
        "H1": "Page titles",
        "H2": "Section headers",
        "H3": "Card titles, subsections",
        "Body": "Regular text, descriptions",
        "Micro": "Labels, captions, small text",
    }
    for item in typo["hierarchy"]:
        usage = usage_map.get(item["level"], "")
        lines.append(f"| {item['level']} | {item['size']} | {item['weight']} | {item['line_height']} | {usage} |")

    lines.extend([
        "",
        "## 3. Component Patterns",
        "",
        "### Cards",
        f"- Background: {comps['cards']['background']}",
        f"- Border: {comps['cards']['border']}",
        f"- Radius: {comps['cards']['radius']}",
        f"- Shadow: {comps['cards']['shadow']}",
        f"- Padding: {comps['cards']['padding']}",
    ])
    if "backdrop_filter" in comps["cards"]:
        lines.append(f"- Backdrop Filter: {comps['cards']['backdrop_filter']}")

    lines.extend([
        "",
        "### Buttons (Primary)",
        f"- Background: {comps['buttons']['primary_bg']}",
        f"- Text Color: {comps['buttons']['primary_text']}",
        f"- Radius: {comps['buttons']['radius']}",
        f"- Padding: {comps['buttons']['padding']}",
        f"- Hover: {comps['buttons']['hover']}",
    ])
    if "border" in comps["buttons"]:
        lines.append(f"- Border: {comps['buttons']['border']}")
    if "shadow" in comps["buttons"]:
        lines.append(f"- Shadow: {comps['buttons']['shadow']}")

    lines.extend([
        "",
        "### Inputs",
        f"- Background: {comps['inputs']['background']}",
        f"- Border: {comps['inputs']['border']}",
        f"- Radius: {comps['inputs']['radius']}",
        f"- Padding: {comps['inputs']['padding']}",
    ])
    if "shadow" in comps["inputs"]:
        lines.append(f"- Shadow: {comps['inputs']['shadow']}")

    lines.extend([
        "",
        "### Icons",
        f"- Style: {comps['icons']['style']}",
        f"- Default Size: {comps['icons']['size']}",
        "",
        "## 4. Spacing & Layout",
        "",
        f"- Base Unit: {spacing['base_unit']}",
        f"- Density: {spacing['density']}",
        f"- Card Gaps: {spacing['card_gap']}",
        f"- Section Gaps: {spacing['section_gap']}",
        "",
        "## 5. Tailwind CSS Theme Extension",
        "",
        "```javascript",
        "// tailwind.config.js",
        "module.exports = {",
        "  theme: {",
        "    extend: " + json.dumps(tw, indent=6),
        "  }",
        "}",
        "```",
        "",
    ])

    # Append do's and don'ts if available for this style
    dos_and_donts = STYLE_DOS_AND_DONTS.get(style_id)
    if dos_and_donts:
        lines.append("## 6. Style Guidelines (Do's and Don'ts)")
        lines.append("")
        lines.append("### DO:")
        for item in dos_and_donts.get("dos", []):
            lines.append(f"- {item}")
        lines.append("")
        lines.append("### DON'T:")
        for item in dos_and_donts.get("donts", []):
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def save_style_guide(project_dir: Path, style_id: str) -> Path | None:
    """
    Generate and save the style guide markdown to the project's .autoforge directory.

    Returns the path to the saved file, or None if the style was not found.
    """
    guide_md = get_style_guide_markdown(style_id)
    if not guide_md:
        return None

    config_dir = project_dir / ".autoforge"
    config_dir.mkdir(parents=True, exist_ok=True)

    guide_path = config_dir / "style_guide.md"
    try:
        guide_path.write_text(guide_md, encoding="utf-8")
        logger.info("Saved style guide to %s", guide_path)
        return guide_path
    except OSError as e:
        logger.error("Failed to save style guide to %s: %s", guide_path, e)
        return None


def get_audience_profiles() -> dict:
    """Return the audience matching profiles for the API."""
    return {
        "audiences": AUDIENCE_PROFILES,
        "vibes": VIBE_PROFILES,
        "age_groups": AGE_PROFILES,
    }
