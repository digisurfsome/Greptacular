"""
UI Design Style Registry
=========================

Comprehensive registry of 12 UI design styles for project creation.
Each style includes Tailwind CSS configuration, design tokens, audience
matching metadata, and CSS preview snippets for visual selection in the UI.

Styles are organized into two categories:
- **core**: Foundational visual paradigms (flat, minimal, neumorphic, etc.)
- **vibe**: Aesthetic/mood-driven styles (cyberpunk, retro-futurism, etc.)

The registry powers three workflows:
1. Style selection during project creation (UI picker with previews)
2. Agent prompt injection via ``get_style_prompt_context()`` so the coding
   agent maintains consistent styling throughout feature implementation
3. Audience-based recommendation via ``recommend_style()`` for guided selection
"""

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Style Registry
# =============================================================================

STYLE_REGISTRY: list[dict] = [
    # -----------------------------------------------------------------
    # CORE VISUAL STYLES
    # -----------------------------------------------------------------
    {
        "id": "flat-design",
        "name": "Flat Design",
        "description": "Simple 2D elements with solid colors, clean iconography, and minimal visual noise. "
        "Eliminates gradients, drop shadows, and textures in favor of crisp edges and bold color blocks.",
        "best_for": "Clarity, scalability, and universal accessibility across devices and screen sizes",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#2196F3",
                    "secondary": "#FF9800",
                    "accent": "#4CAF50",
                },
                "surface": {
                    "background": "#FFFFFF",
                    "card": "#F5F5F5",
                    "elevated": "#EEEEEE",
                },
                "text": {
                    "primary": "#212121",
                    "secondary": "#757575",
                    "muted": "#9E9E9E",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "#E0E0E0",
                    "strong": "#BDBDBD",
                    "subtle": "#F5F5F5",
                },
                "status": {
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "info": "#2196F3",
                },
            },
            "fontFamily": {
                "sans": ["Inter", "Roboto", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
                "mono": ["Roboto Mono", "Fira Code", "Consolas", "monospace"],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.375rem",
                "md": "0.5rem",
                "lg": "0.75rem",
                "xl": "1rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "none",
                "DEFAULT": "none",
                "md": "0 1px 2px 0 rgba(0,0,0,0.05)",
                "lg": "0 2px 4px 0 rgba(0,0,0,0.05)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Inter, Roboto, sans-serif",
                "heading_weight": "600",
                "body_weight": "400",
                "line_height": "1.5",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "0.5rem",
                "card_border": "1px solid #E0E0E0",
                "card_shadow": "none",
                "button_radius": "0.375rem",
                "button_style": "solid fill with no shadow, uppercase or sentence-case label",
                "input_radius": "0.375rem",
                "input_style": "solid border, no shadow, flat background on focus",
                "icon_style": "outlined, monoline, consistent 24px grid",
            },
        },
        "audience_match": {
            "recommended_for": [
                "enterprise-dashboard",
                "productivity-tool",
                "mobile-app",
                "cross-platform",
                "content-platform",
                "e-commerce",
            ],
            "avoid_for": [
                "luxury-brand",
                "gaming-entertainment",
                "artistic-portfolio",
            ],
        },
        "css_preview": (
            '<div style="font-family:Inter,Roboto,sans-serif;background:#FFFFFF;border:1px solid #E0E0E0;'
            "border-radius:0.5rem;padding:16px;width:200px;\">"
            '<div style="font-size:14px;font-weight:600;color:#212121;margin-bottom:8px;">Flat Design</div>'
            '<div style="font-size:12px;color:#757575;margin-bottom:12px;">Clean and simple</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:#2196F3;color:#FFF;padding:4px 12px;border-radius:0.375rem;'
            'font-size:11px;font-weight:500;">Primary</span>'
            '<span style="background:#F5F5F5;color:#212121;padding:4px 12px;border-radius:0.375rem;'
            'font-size:11px;border:1px solid #E0E0E0;">Secondary</span>'
            "</div></div>"
        ),
    },
    {
        "id": "minimalism",
        "name": "Minimalism",
        "description": "Maximizes white space and strips away all non-essential elements. "
        "Every pixel serves a purpose. Typography becomes the primary design element with "
        "restrained color use and deliberate negative space.",
        "best_for": "Premium, Apple-style products that convey sophistication and focus",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#111827",
                    "secondary": "#6B7280",
                    "accent": "#3B82F6",
                },
                "surface": {
                    "background": "#FFFFFF",
                    "card": "#FFFFFF",
                    "elevated": "#F9FAFB",
                },
                "text": {
                    "primary": "#111827",
                    "secondary": "#4B5563",
                    "muted": "#9CA3AF",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "#E5E7EB",
                    "strong": "#D1D5DB",
                    "subtle": "#F3F4F6",
                },
                "status": {
                    "success": "#059669",
                    "warning": "#D97706",
                    "error": "#DC2626",
                    "info": "#2563EB",
                },
            },
            "fontFamily": {
                "sans": ["Inter", "SF Pro Display", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
                "mono": ["SF Mono", "JetBrains Mono", "Fira Code", "monospace"],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.5rem",
                "md": "0.625rem",
                "lg": "0.75rem",
                "xl": "1rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 1px 2px 0 rgba(0,0,0,0.03)",
                "DEFAULT": "0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px -1px rgba(0,0,0,0.03)",
                "md": "0 4px 6px -1px rgba(0,0,0,0.04), 0 2px 4px -2px rgba(0,0,0,0.03)",
                "lg": "0 10px 15px -3px rgba(0,0,0,0.04), 0 4px 6px -4px rgba(0,0,0,0.03)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Inter, SF Pro Display, sans-serif",
                "heading_weight": "600",
                "body_weight": "400",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "spacious",
            },
            "component_patterns": {
                "card_radius": "0.75rem",
                "card_border": "1px solid #E5E7EB",
                "card_shadow": "0 1px 3px 0 rgba(0,0,0,0.04)",
                "button_radius": "0.5rem",
                "button_style": "subtle fill or ghost, medium font-weight, generous padding",
                "input_radius": "0.5rem",
                "input_style": "thin border, generous padding, subtle focus ring",
                "icon_style": "thin stroke (1.5px), Lucide or Heroicons style",
            },
        },
        "audience_match": {
            "recommended_for": [
                "premium-luxury",
                "saas-product",
                "portfolio-showcase",
                "content-platform",
                "productivity-tool",
            ],
            "avoid_for": [
                "children-app",
                "gaming-entertainment",
                "young-edgy",
            ],
        },
        "css_preview": (
            '<div style="font-family:Inter,sans-serif;background:#FFFFFF;border:1px solid #E5E7EB;'
            "border-radius:0.75rem;padding:20px;width:200px;\">"
            '<div style="font-size:14px;font-weight:600;color:#111827;margin-bottom:6px;'
            'letter-spacing:-0.01em;">Minimalism</div>'
            '<div style="font-size:12px;color:#9CA3AF;margin-bottom:16px;line-height:1.5;">'
            "Less is more</div>"
            '<div style="display:flex;gap:8px;">'
            '<span style="background:#111827;color:#FFF;padding:6px 14px;border-radius:0.5rem;'
            'font-size:11px;font-weight:500;">Action</span>'
            '<span style="background:transparent;color:#6B7280;padding:6px 14px;border-radius:0.5rem;'
            'font-size:11px;border:1px solid #E5E7EB;">Cancel</span>'
            "</div></div>"
        ),
    },
    {
        "id": "neumorphism",
        "name": "Neumorphism",
        "description": "Soft UI with dual shadows creating an embossed or extruded appearance. "
        "Elements appear to push out from or sink into the background surface, creating a tactile, "
        "physical feel through careful light and shadow interplay.",
        "best_for": "Finance dashboards, toggle controls, and interfaces requiring a premium tactile feel",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#6C5CE7",
                    "secondary": "#A29BFE",
                    "accent": "#00CEC9",
                },
                "surface": {
                    "background": "#E0E5EC",
                    "card": "#E0E5EC",
                    "elevated": "#E8ECF1",
                },
                "text": {
                    "primary": "#2D3436",
                    "secondary": "#636E72",
                    "muted": "#B2BEC3",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "transparent",
                    "strong": "#C8CED6",
                    "subtle": "#EDF0F4",
                },
                "status": {
                    "success": "#00B894",
                    "warning": "#FDCB6E",
                    "error": "#E17055",
                    "info": "#74B9FF",
                },
            },
            "fontFamily": {
                "sans": ["Nunito", "Poppins", "-apple-system", "sans-serif"],
                "mono": ["Fira Code", "JetBrains Mono", "monospace"],
            },
            "borderRadius": {
                "sm": "0.5rem",
                "DEFAULT": "0.75rem",
                "md": "1rem",
                "lg": "1.25rem",
                "xl": "1.5rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "3px 3px 6px #B8BEC7, -3px -3px 6px #FFFFFF",
                "DEFAULT": "6px 6px 12px #B8BEC7, -6px -6px 12px #FFFFFF",
                "md": "8px 8px 16px #B8BEC7, -8px -8px 16px #FFFFFF",
                "lg": "12px 12px 24px #B8BEC7, -12px -12px 24px #FFFFFF",
                "inset": "inset 4px 4px 8px #B8BEC7, inset -4px -4px 8px #FFFFFF",
                "inset-sm": "inset 2px 2px 4px #B8BEC7, inset -2px -2px 4px #FFFFFF",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Nunito, Poppins, sans-serif",
                "heading_weight": "700",
                "body_weight": "400",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "1rem",
                "card_border": "none",
                "card_shadow": "6px 6px 12px #B8BEC7, -6px -6px 12px #FFFFFF",
                "button_radius": "0.75rem",
                "button_style": "raised with dual shadow, pressed state uses inset shadow",
                "input_radius": "0.75rem",
                "input_style": "inset shadow (sunken), no visible border, same bg as surface",
                "icon_style": "rounded, filled or duotone, soft edges",
            },
        },
        "audience_match": {
            "recommended_for": [
                "finance-dashboard",
                "smart-home",
                "health-fitness",
                "settings-panel",
                "premium-luxury",
            ],
            "avoid_for": [
                "content-heavy",
                "e-commerce",
                "data-dense-table",
                "accessibility-critical",
            ],
        },
        "css_preview": (
            '<div style="font-family:Nunito,sans-serif;background:#E0E5EC;border-radius:1rem;'
            "padding:16px;width:200px;box-shadow:6px 6px 12px #B8BEC7,-6px -6px 12px #FFFFFF;\">"
            '<div style="font-size:14px;font-weight:700;color:#2D3436;margin-bottom:8px;">'
            "Neumorphism</div>"
            '<div style="font-size:12px;color:#636E72;margin-bottom:12px;">Soft & tactile</div>'
            '<div style="display:flex;gap:8px;">'
            '<span style="background:#E0E5EC;color:#6C5CE7;padding:6px 14px;border-radius:0.75rem;'
            "font-size:11px;font-weight:600;box-shadow:3px 3px 6px #B8BEC7,-3px -3px 6px #FFFFFF;\">"
            "Raised</span>"
            '<span style="background:#E0E5EC;color:#636E72;padding:6px 14px;border-radius:0.75rem;'
            "font-size:11px;box-shadow:inset 2px 2px 4px #B8BEC7,inset -2px -2px 4px #FFFFFF;\">"
            "Inset</span>"
            "</div></div>"
        ),
    },
    {
        "id": "glassmorphism",
        "name": "Glassmorphism",
        "description": "Frosted glass effect with translucent layers, background blur, and luminous borders. "
        "Creates depth through transparency rather than shadow, with elements floating on a vibrant backdrop.",
        "best_for": "Modern, futuristic interfaces with layered content and vibrant imagery",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#7C3AED",
                    "secondary": "#06B6D4",
                    "accent": "#F472B6",
                },
                "surface": {
                    "background": "#0F172A",
                    "card": "rgba(255, 255, 255, 0.08)",
                    "elevated": "rgba(255, 255, 255, 0.12)",
                },
                "text": {
                    "primary": "#F8FAFC",
                    "secondary": "#CBD5E1",
                    "muted": "#94A3B8",
                    "inverse": "#0F172A",
                },
                "border": {
                    "default": "rgba(255, 255, 255, 0.15)",
                    "strong": "rgba(255, 255, 255, 0.25)",
                    "subtle": "rgba(255, 255, 255, 0.08)",
                },
                "status": {
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#FB7185",
                    "info": "#38BDF8",
                },
            },
            "fontFamily": {
                "sans": ["Inter", "SF Pro Display", "-apple-system", "sans-serif"],
                "mono": ["JetBrains Mono", "Fira Code", "monospace"],
            },
            "borderRadius": {
                "sm": "0.5rem",
                "DEFAULT": "0.75rem",
                "md": "1rem",
                "lg": "1.25rem",
                "xl": "1.5rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 2px 8px rgba(0,0,0,0.2)",
                "DEFAULT": "0 4px 16px rgba(0,0,0,0.25)",
                "md": "0 8px 32px rgba(0,0,0,0.3)",
                "lg": "0 16px 48px rgba(0,0,0,0.35)",
                "glow": "0 0 20px rgba(124,58,237,0.3)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Inter, SF Pro Display, sans-serif",
                "heading_weight": "600",
                "body_weight": "400",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "1rem",
                "card_border": "1px solid rgba(255,255,255,0.15)",
                "card_shadow": "0 8px 32px rgba(0,0,0,0.3)",
                "card_backdrop": "blur(16px) saturate(180%)",
                "button_radius": "0.75rem",
                "button_style": "translucent background, subtle border, backdrop-blur, hover brightens",
                "input_radius": "0.75rem",
                "input_style": "translucent background, subtle border, backdrop-blur on focus",
                "icon_style": "outlined, thin stroke, subtle glow on interactive states",
            },
        },
        "audience_match": {
            "recommended_for": [
                "modern-saas",
                "creative-tool",
                "music-media",
                "landing-page",
                "portfolio-showcase",
            ],
            "avoid_for": [
                "accessibility-critical",
                "data-dense-table",
                "print-friendly",
                "low-end-devices",
            ],
        },
        "css_preview": (
            '<div style="font-family:Inter,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);'
            "border-radius:1rem;padding:4px;width:200px;\">"
            '<div style="background:rgba(255,255,255,0.12);backdrop-filter:blur(16px);'
            "border:1px solid rgba(255,255,255,0.2);border-radius:0.75rem;padding:16px;\">"
            '<div style="font-size:14px;font-weight:600;color:#F8FAFC;margin-bottom:6px;">'
            "Glassmorphism</div>"
            '<div style="font-size:12px;color:#CBD5E1;margin-bottom:12px;">Frosted layers</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:rgba(124,58,237,0.5);color:#F8FAFC;padding:5px 12px;'
            "border-radius:0.75rem;font-size:11px;font-weight:500;"
            'border:1px solid rgba(255,255,255,0.2);">Glass</span>'
            '<span style="background:rgba(255,255,255,0.1);color:#CBD5E1;padding:5px 12px;'
            "border-radius:0.75rem;font-size:11px;"
            'border:1px solid rgba(255,255,255,0.1);">Frost</span>'
            "</div></div></div>"
        ),
    },
    {
        "id": "skeuomorphism",
        "name": "Skeuomorphism",
        "description": "Mimics real-world objects with realistic textures, gradients, and shadows. "
        "Leather, wood, metal, and paper textures create familiarity. Elements look and behave "
        "like their physical counterparts.",
        "best_for": "Familiar, intuitive interfaces and nostalgic or craft-oriented applications",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#C0392B",
                    "secondary": "#2980B9",
                    "accent": "#F39C12",
                },
                "surface": {
                    "background": "#ECE9E0",
                    "card": "#F5F0E8",
                    "elevated": "#FAFAF5",
                },
                "text": {
                    "primary": "#2C3E50",
                    "secondary": "#5D6D7E",
                    "muted": "#95A5A6",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "#BDC3C7",
                    "strong": "#95A5A6",
                    "subtle": "#D5D8DC",
                },
                "status": {
                    "success": "#27AE60",
                    "warning": "#F39C12",
                    "error": "#E74C3C",
                    "info": "#3498DB",
                },
            },
            "fontFamily": {
                "sans": ["Georgia", "Palatino Linotype", "Book Antiqua", "serif"],
                "display": ["Playfair Display", "Georgia", "serif"],
                "mono": ["Courier New", "Courier", "monospace"],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.375rem",
                "md": "0.5rem",
                "lg": "0.625rem",
                "xl": "0.75rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 1px 2px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3)",
                "DEFAULT": "0 2px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.2)",
                "md": "0 4px 8px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.15)",
                "lg": "0 8px 16px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
                "inset": "inset 0 2px 4px rgba(0,0,0,0.2)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Georgia, Palatino Linotype, serif",
                "heading_weight": "700",
                "body_weight": "400",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "0.5rem",
                "card_border": "1px solid #BDC3C7",
                "card_shadow": "0 2px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.2)",
                "button_radius": "0.375rem",
                "button_style": "gradient background (light top to dark bottom), inset highlight, pressed "
                "state inverts gradient",
                "input_radius": "0.375rem",
                "input_style": "inset shadow, subtle gradient background, embossed label",
                "icon_style": "detailed, realistic, glossy or textured fills",
            },
        },
        "audience_match": {
            "recommended_for": [
                "music-production",
                "note-taking",
                "reading-app",
                "craft-artisan",
                "nostalgic-brand",
            ],
            "avoid_for": [
                "modern-saas",
                "young-edgy",
                "data-dense-table",
                "mobile-first",
            ],
        },
        "css_preview": (
            '<div style="font-family:Georgia,serif;background:#ECE9E0;border-radius:0.5rem;'
            "padding:2px;width:200px;\">"
            '<div style="background:linear-gradient(180deg,#FAFAF5,#F0EBE0);border:1px solid #BDC3C7;'
            "border-radius:0.375rem;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.2),"
            'inset 0 1px 0 rgba(255,255,255,0.3);">'
            '<div style="font-size:14px;font-weight:700;color:#2C3E50;margin-bottom:6px;">'
            "Skeuomorphism</div>"
            '<div style="font-size:12px;color:#5D6D7E;margin-bottom:12px;">Real-world feel</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:linear-gradient(180deg,#E74C3C,#C0392B);color:#FFF;'
            "padding:5px 12px;border-radius:0.375rem;font-size:11px;font-weight:600;"
            'box-shadow:0 2px 3px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.2);">'
            "Button</span>"
            '<span style="background:linear-gradient(180deg,#FAFAF5,#ECE9E0);color:#5D6D7E;'
            "padding:5px 12px;border-radius:0.375rem;font-size:11px;border:1px solid #BDC3C7;"
            'box-shadow:inset 0 1px 3px rgba(0,0,0,0.1);">Input</span>'
            "</div></div></div>"
        ),
    },
    {
        "id": "neubrutalism",
        "name": "Neubrutalism",
        "description": "Bold, raw aesthetic with heavy black outlines, hard offset shadows, clashing "
        "vibrant colors, and zero border radius. Intentionally unpolished and attention-grabbing, "
        "rejecting conventional design refinement.",
        "best_for": "Gen Z audiences, edgy brands, creative agencies, and bold statements",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#FF6B6B",
                    "secondary": "#4ECDC4",
                    "accent": "#FFE66D",
                },
                "surface": {
                    "background": "#FFFFFF",
                    "card": "#FFEAA7",
                    "elevated": "#DFE6E9",
                },
                "text": {
                    "primary": "#000000",
                    "secondary": "#2D3436",
                    "muted": "#636E72",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "#000000",
                    "strong": "#000000",
                    "subtle": "#2D3436",
                },
                "status": {
                    "success": "#00B894",
                    "warning": "#FDCB6E",
                    "error": "#FF6B6B",
                    "info": "#74B9FF",
                },
            },
            "fontFamily": {
                "sans": ["DM Sans", "Space Grotesk", "-apple-system", "sans-serif"],
                "mono": ["Space Mono", "JetBrains Mono", "monospace"],
            },
            "borderRadius": {
                "sm": "0",
                "DEFAULT": "0",
                "md": "0",
                "lg": "0",
                "xl": "0",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "2px 2px 0px #000000",
                "DEFAULT": "4px 4px 0px #000000",
                "md": "5px 5px 0px #000000",
                "lg": "8px 8px 0px #000000",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "DM Sans, Space Grotesk, sans-serif",
                "heading_weight": "800",
                "body_weight": "500",
                "line_height": "1.4",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "0",
                "card_border": "3px solid #000000",
                "card_shadow": "5px 5px 0px #000000",
                "button_radius": "0",
                "button_style": "thick black border (2-3px), hard offset shadow, bold color fill, "
                "translate on hover to remove shadow",
                "input_radius": "0",
                "input_style": "thick black border (2-3px), no shadow, white background",
                "icon_style": "bold stroke (2px+), simple geometric shapes",
            },
        },
        "audience_match": {
            "recommended_for": [
                "young-edgy",
                "creative-agency",
                "startup-landing",
                "blog-personal",
                "event-promo",
            ],
            "avoid_for": [
                "finance-dashboard",
                "healthcare",
                "enterprise-corporate",
                "50-plus-audience",
            ],
        },
        "css_preview": (
            '<div style="font-family:DM Sans,sans-serif;background:#FFEAA7;border:3px solid #000;'
            "padding:16px;width:200px;box-shadow:5px 5px 0px #000;\">"
            '<div style="font-size:14px;font-weight:800;color:#000;margin-bottom:6px;">'
            "NEUBRUTALISM</div>"
            '<div style="font-size:12px;color:#2D3436;margin-bottom:12px;font-weight:500;">'
            "Bold & raw</div>"
            '<div style="display:flex;gap:8px;">'
            '<span style="background:#FF6B6B;color:#000;padding:5px 12px;font-size:11px;'
            'font-weight:700;border:2px solid #000;box-shadow:2px 2px 0px #000;">SMASH</span>'
            '<span style="background:#4ECDC4;color:#000;padding:5px 12px;font-size:11px;'
            'font-weight:700;border:2px solid #000;box-shadow:2px 2px 0px #000;">GRAB</span>'
            "</div></div>"
        ),
    },
    {
        "id": "bauhaus",
        "name": "Bauhaus",
        "description": "Geometric shapes, primary colors (red, blue, yellow), and strict grid-based layouts. "
        "Inspired by the 1919 German art school, combining form and function with mathematical precision "
        "and bold typographic hierarchy.",
        "best_for": "Artistic, balanced, and timeless designs with strong visual structure",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#E63946",
                    "secondary": "#457B9D",
                    "accent": "#F4D35E",
                },
                "surface": {
                    "background": "#F1FAEE",
                    "card": "#FFFFFF",
                    "elevated": "#F8F9FA",
                },
                "text": {
                    "primary": "#1D3557",
                    "secondary": "#457B9D",
                    "muted": "#A8DADC",
                    "inverse": "#F1FAEE",
                },
                "border": {
                    "default": "#1D3557",
                    "strong": "#000000",
                    "subtle": "#A8DADC",
                },
                "status": {
                    "success": "#2A9D8F",
                    "warning": "#F4D35E",
                    "error": "#E63946",
                    "info": "#457B9D",
                },
            },
            "fontFamily": {
                "sans": ["Montserrat", "Futura", "Century Gothic", "sans-serif"],
                "display": ["Bebas Neue", "Montserrat", "sans-serif"],
                "mono": ["IBM Plex Mono", "Courier New", "monospace"],
            },
            "borderRadius": {
                "sm": "0",
                "DEFAULT": "0",
                "md": "0",
                "lg": "0",
                "xl": "0",
                "full": "50%",
            },
            "boxShadow": {
                "sm": "none",
                "DEFAULT": "none",
                "md": "4px 4px 0px #1D3557",
                "lg": "6px 6px 0px #1D3557",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Montserrat, Futura, sans-serif",
                "heading_weight": "900",
                "body_weight": "400",
                "line_height": "1.5",
            },
            "spacing": {
                "base_unit": "8px",
                "density": "structured",
            },
            "component_patterns": {
                "card_radius": "0",
                "card_border": "2px solid #1D3557",
                "card_shadow": "none",
                "button_radius": "0",
                "button_style": "solid primary color fill, black or navy border, uppercase text, "
                "geometric precision",
                "input_radius": "0",
                "input_style": "strong bottom border or full border, geometric, no rounding",
                "icon_style": "geometric, constructed from circles/triangles/squares, primary colors only",
            },
        },
        "audience_match": {
            "recommended_for": [
                "artistic-portfolio",
                "design-agency",
                "education-platform",
                "architecture-firm",
                "museum-gallery",
            ],
            "avoid_for": [
                "children-app",
                "friendly-approachable",
                "casual-social",
            ],
        },
        "css_preview": (
            '<div style="font-family:Montserrat,sans-serif;background:#F1FAEE;border:2px solid #1D3557;'
            "padding:16px;width:200px;\">"
            '<div style="font-size:14px;font-weight:900;color:#1D3557;margin-bottom:6px;'
            'text-transform:uppercase;letter-spacing:0.05em;">Bauhaus</div>'
            '<div style="font-size:12px;color:#457B9D;margin-bottom:12px;">Form follows function</div>'
            '<div style="display:flex;gap:8px;align-items:center;">'
            '<span style="display:inline-block;width:20px;height:20px;background:#E63946;"></span>'
            '<span style="display:inline-block;width:20px;height:20px;background:#457B9D;'
            'border-radius:50%;"></span>'
            '<span style="display:inline-block;width:0;height:0;border-left:10px solid transparent;'
            'border-right:10px solid transparent;border-bottom:20px solid #F4D35E;"></span>'
            '<span style="background:#1D3557;color:#F1FAEE;padding:4px 10px;font-size:10px;'
            'font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Action</span>'
            "</div></div>"
        ),
    },
    {
        "id": "claymorphism",
        "name": "Claymorphism",
        "description": "Soft, rounded elements that look hand-sculpted from clay. Features pastel colors, "
        "generous padding, inner shadows for depth, and a warm, playful dimensionality that invites "
        "interaction.",
        "best_for": "Warm, friendly, approachable interfaces for consumer-facing products",
        "category": "core",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#7C5CFC",
                    "secondary": "#FF8FAB",
                    "accent": "#5CE1E6",
                },
                "surface": {
                    "background": "#F0EDFF",
                    "card": "#FFFFFF",
                    "elevated": "#F8F6FF",
                },
                "text": {
                    "primary": "#2D2B55",
                    "secondary": "#6E6B99",
                    "muted": "#A8A5C8",
                    "inverse": "#FFFFFF",
                },
                "border": {
                    "default": "rgba(124,92,252,0.15)",
                    "strong": "rgba(124,92,252,0.3)",
                    "subtle": "rgba(124,92,252,0.08)",
                },
                "status": {
                    "success": "#5CE6A1",
                    "warning": "#FFD166",
                    "error": "#FF6B8A",
                    "info": "#5CE1E6",
                },
            },
            "fontFamily": {
                "sans": ["Quicksand", "Nunito", "Poppins", "sans-serif"],
                "mono": ["Fira Code", "JetBrains Mono", "monospace"],
            },
            "borderRadius": {
                "sm": "0.75rem",
                "DEFAULT": "1rem",
                "md": "1.25rem",
                "lg": "1.5rem",
                "xl": "2rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 4px 8px rgba(124,92,252,0.08), inset 0 -2px 4px rgba(0,0,0,0.04), "
                "inset 0 2px 4px rgba(255,255,255,0.8)",
                "DEFAULT": "0 8px 16px rgba(124,92,252,0.1), inset 0 -3px 6px rgba(0,0,0,0.05), "
                "inset 0 3px 6px rgba(255,255,255,0.9)",
                "md": "0 12px 24px rgba(124,92,252,0.12), inset 0 -4px 8px rgba(0,0,0,0.05), "
                "inset 0 4px 8px rgba(255,255,255,0.9)",
                "lg": "0 16px 32px rgba(124,92,252,0.15), inset 0 -6px 10px rgba(0,0,0,0.06), "
                "inset 0 6px 10px rgba(255,255,255,0.9)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Quicksand, Nunito, sans-serif",
                "heading_weight": "700",
                "body_weight": "500",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "spacious",
            },
            "component_patterns": {
                "card_radius": "1.5rem",
                "card_border": "none",
                "card_shadow": "0 8px 16px rgba(124,92,252,0.1), inset 0 -3px 6px rgba(0,0,0,0.05), "
                "inset 0 3px 6px rgba(255,255,255,0.9)",
                "button_radius": "1rem",
                "button_style": "rounded, pastel fill, inner highlight shadow, bouncy hover animation",
                "input_radius": "1rem",
                "input_style": "soft border, inner shadow on focus, rounded, generous padding",
                "icon_style": "rounded, chunky stroke (2px), playful, slightly oversized",
            },
        },
        "audience_match": {
            "recommended_for": [
                "friendly-approachable",
                "children-app",
                "health-wellness",
                "social-platform",
                "onboarding-flow",
            ],
            "avoid_for": [
                "finance-dashboard",
                "enterprise-corporate",
                "data-dense-table",
                "young-edgy",
            ],
        },
        "css_preview": (
            '<div style="font-family:Quicksand,sans-serif;background:#F0EDFF;'
            "border-radius:1.5rem;padding:4px;width:200px;\">"
            '<div style="background:#FFFFFF;border-radius:1.25rem;padding:16px;'
            "box-shadow:0 8px 16px rgba(124,92,252,0.1),inset 0 -3px 6px rgba(0,0,0,0.05),"
            'inset 0 3px 6px rgba(255,255,255,0.9);">'
            '<div style="font-size:14px;font-weight:700;color:#2D2B55;margin-bottom:6px;">'
            "Claymorphism</div>"
            '<div style="font-size:12px;color:#6E6B99;margin-bottom:12px;font-weight:500;">'
            "Soft & sculpted</div>"
            '<div style="display:flex;gap:8px;">'
            '<span style="background:#7C5CFC;color:#FFF;padding:6px 14px;border-radius:1rem;'
            "font-size:11px;font-weight:600;box-shadow:0 4px 8px rgba(124,92,252,0.2),"
            'inset 0 1px 2px rgba(255,255,255,0.3);">Clay</span>'
            '<span style="background:#FF8FAB;color:#FFF;padding:6px 14px;border-radius:1rem;'
            "font-size:11px;font-weight:600;box-shadow:0 4px 8px rgba(255,143,171,0.2),"
            'inset 0 1px 2px rgba(255,255,255,0.3);">Mold</span>'
            "</div></div></div>"
        ),
    },
    # -----------------------------------------------------------------
    # VIBE / AESTHETIC STYLES
    # -----------------------------------------------------------------
    {
        "id": "retro-futurism",
        "name": "Retro Futurism",
        "description": "Neon glows layered with vintage 80s/90s nostalgia. Synthwave gradients, "
        "chrome accents, and arcade-inspired typography create an atmosphere of optimistic futurism "
        "as imagined from the past.",
        "best_for": "Gaming, entertainment, music apps, and nostalgia-driven experiences",
        "category": "vibe",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#FF6EC7",
                    "secondary": "#00FFFF",
                    "accent": "#FFD700",
                },
                "surface": {
                    "background": "#1A0533",
                    "card": "#2D1052",
                    "elevated": "#3D1A6E",
                },
                "text": {
                    "primary": "#F0E6FF",
                    "secondary": "#C4A8FF",
                    "muted": "#8B6FC0",
                    "inverse": "#1A0533",
                },
                "border": {
                    "default": "rgba(255,110,199,0.3)",
                    "strong": "#FF6EC7",
                    "subtle": "rgba(255,110,199,0.15)",
                },
                "status": {
                    "success": "#39FF14",
                    "warning": "#FFD700",
                    "error": "#FF1744",
                    "info": "#00FFFF",
                },
            },
            "fontFamily": {
                "sans": ["Orbitron", "Space Grotesk", "Rajdhani", "sans-serif"],
                "display": ["Orbitron", "Press Start 2P", "monospace"],
                "mono": ["Space Mono", "VT323", "monospace"],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.375rem",
                "md": "0.5rem",
                "lg": "0.75rem",
                "xl": "1rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 0 8px rgba(255,110,199,0.3)",
                "DEFAULT": "0 0 15px rgba(255,110,199,0.4)",
                "md": "0 0 25px rgba(255,110,199,0.4), 0 0 50px rgba(255,110,199,0.1)",
                "lg": "0 0 40px rgba(255,110,199,0.5), 0 0 80px rgba(255,110,199,0.15)",
                "neon-cyan": "0 0 15px rgba(0,255,255,0.5), 0 0 30px rgba(0,255,255,0.2)",
                "neon-gold": "0 0 15px rgba(255,215,0,0.5), 0 0 30px rgba(255,215,0,0.2)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Orbitron, Space Grotesk, sans-serif",
                "heading_weight": "700",
                "body_weight": "400",
                "line_height": "1.5",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "0.5rem",
                "card_border": "1px solid rgba(255,110,199,0.3)",
                "card_shadow": "0 0 15px rgba(255,110,199,0.2)",
                "button_radius": "0.375rem",
                "button_style": "neon border glow, dark fill, text-shadow glow, hover intensifies glow",
                "input_radius": "0.375rem",
                "input_style": "dark background, neon border on focus, subtle inner glow",
                "icon_style": "outlined with neon glow, thin stroke, sci-fi aesthetic",
            },
        },
        "audience_match": {
            "recommended_for": [
                "gaming-entertainment",
                "music-media",
                "event-promo",
                "young-edgy",
                "nostalgia-brand",
            ],
            "avoid_for": [
                "enterprise-corporate",
                "healthcare",
                "finance-dashboard",
                "50-plus-audience",
            ],
        },
        "css_preview": (
            '<div style="font-family:Orbitron,monospace;background:#1A0533;border:1px solid rgba(255,110,199,0.4);'
            "border-radius:0.5rem;padding:16px;width:200px;box-shadow:0 0 20px rgba(255,110,199,0.2);\">"
            '<div style="font-size:13px;font-weight:700;color:#FF6EC7;margin-bottom:6px;'
            'text-shadow:0 0 10px rgba(255,110,199,0.5);">RETRO FUTURE</div>'
            '<div style="font-size:11px;color:#C4A8FF;margin-bottom:12px;">Neon nostalgia</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:transparent;color:#00FFFF;padding:4px 10px;border-radius:0.375rem;'
            "font-size:10px;font-weight:600;border:1px solid #00FFFF;"
            'box-shadow:0 0 8px rgba(0,255,255,0.3);text-shadow:0 0 6px rgba(0,255,255,0.5);">'
            "NEON</span>"
            '<span style="background:transparent;color:#FFD700;padding:4px 10px;border-radius:0.375rem;'
            "font-size:10px;font-weight:600;border:1px solid #FFD700;"
            'box-shadow:0 0 8px rgba(255,215,0,0.3);text-shadow:0 0 6px rgba(255,215,0,0.5);">'
            "GLOW</span>"
            "</div></div>"
        ),
    },
    {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "description": "Dark, high-contrast aesthetic with neon accents, glitch effects, and dystopian "
        "undertones. Draws from sci-fi culture with terminal-inspired typography, harsh angular cuts, "
        "and electric color combinations.",
        "best_for": "Tech-forward products, gaming, developer tools, and edgy brands",
        "category": "vibe",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#00F0FF",
                    "secondary": "#FF00FF",
                    "accent": "#39FF14",
                },
                "surface": {
                    "background": "#0A0A0F",
                    "card": "#12121A",
                    "elevated": "#1A1A2E",
                },
                "text": {
                    "primary": "#E0E0FF",
                    "secondary": "#A0A0C0",
                    "muted": "#606080",
                    "inverse": "#0A0A0F",
                },
                "border": {
                    "default": "rgba(0,240,255,0.2)",
                    "strong": "#00F0FF",
                    "subtle": "rgba(0,240,255,0.08)",
                },
                "status": {
                    "success": "#39FF14",
                    "warning": "#FFE100",
                    "error": "#FF0055",
                    "info": "#00F0FF",
                },
            },
            "fontFamily": {
                "sans": ["Rajdhani", "Orbitron", "Share Tech", "sans-serif"],
                "display": ["Orbitron", "Rajdhani", "sans-serif"],
                "mono": ["Share Tech Mono", "Fira Code", "monospace"],
            },
            "borderRadius": {
                "sm": "0",
                "DEFAULT": "0.125rem",
                "md": "0.25rem",
                "lg": "0.375rem",
                "xl": "0.5rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 0 5px rgba(0,240,255,0.3)",
                "DEFAULT": "0 0 10px rgba(0,240,255,0.4), 0 0 20px rgba(0,240,255,0.1)",
                "md": "0 0 20px rgba(0,240,255,0.4), 0 0 40px rgba(0,240,255,0.15)",
                "lg": "0 0 30px rgba(0,240,255,0.5), 0 0 60px rgba(0,240,255,0.2)",
                "neon-magenta": "0 0 15px rgba(255,0,255,0.5), 0 0 30px rgba(255,0,255,0.2)",
                "neon-green": "0 0 15px rgba(57,255,20,0.5), 0 0 30px rgba(57,255,20,0.2)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Rajdhani, Orbitron, sans-serif",
                "heading_weight": "700",
                "body_weight": "400",
                "line_height": "1.5",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "compact",
            },
            "component_patterns": {
                "card_radius": "0.25rem",
                "card_border": "1px solid rgba(0,240,255,0.2)",
                "card_shadow": "0 0 10px rgba(0,240,255,0.15)",
                "button_radius": "0.125rem",
                "button_style": "angular, neon border, dark fill, text glow on hover, "
                "optional clip-path for angled corners",
                "input_radius": "0.125rem",
                "input_style": "dark background, neon cyan border on focus, monospace font option",
                "icon_style": "angular, tech-inspired, neon glow effect, thin sharp lines",
            },
        },
        "audience_match": {
            "recommended_for": [
                "gaming-entertainment",
                "developer-tool",
                "young-edgy",
                "tech-startup",
                "crypto-web3",
            ],
            "avoid_for": [
                "healthcare",
                "children-app",
                "friendly-approachable",
                "50-plus-audience",
                "enterprise-corporate",
            ],
        },
        "css_preview": (
            '<div style="font-family:Rajdhani,sans-serif;background:#0A0A0F;border:1px solid rgba(0,240,255,0.3);'
            "border-radius:0.25rem;padding:16px;width:200px;box-shadow:0 0 15px rgba(0,240,255,0.15);\">"
            '<div style="font-size:14px;font-weight:700;color:#00F0FF;margin-bottom:6px;'
            'text-shadow:0 0 8px rgba(0,240,255,0.5);letter-spacing:0.1em;">CYBERPUNK</div>'
            '<div style="font-size:11px;color:#A0A0C0;margin-bottom:12px;font-family:Share Tech Mono,'
            'monospace;">// Neon dystopia</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:rgba(0,240,255,0.1);color:#00F0FF;padding:4px 10px;'
            "border-radius:0.125rem;font-size:10px;font-weight:700;border:1px solid #00F0FF;"
            'box-shadow:0 0 8px rgba(0,240,255,0.3);">HACK</span>'
            '<span style="background:rgba(255,0,255,0.1);color:#FF00FF;padding:4px 10px;'
            "border-radius:0.125rem;font-size:10px;font-weight:700;border:1px solid #FF00FF;"
            'box-shadow:0 0 8px rgba(255,0,255,0.3);">JACK</span>'
            "</div></div>"
        ),
    },
    {
        "id": "dark-mode",
        "name": "Dark Mode Elegance",
        "description": "Purpose-built dark interface with carefully tuned contrast ratios, reduced "
        "eye strain, and OLED-friendly pure blacks. Uses elevation through subtle lightening "
        "rather than shadows, with accent colors that pop against dark surfaces.",
        "best_for": "Night/low-light usage, OLED screens, developer tools, and media consumption",
        "category": "vibe",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#818CF8",
                    "secondary": "#34D399",
                    "accent": "#F472B6",
                },
                "surface": {
                    "background": "#0F0F0F",
                    "card": "#1A1A1A",
                    "elevated": "#262626",
                },
                "text": {
                    "primary": "#EDEDED",
                    "secondary": "#A3A3A3",
                    "muted": "#737373",
                    "inverse": "#0F0F0F",
                },
                "border": {
                    "default": "#2E2E2E",
                    "strong": "#404040",
                    "subtle": "#1F1F1F",
                },
                "status": {
                    "success": "#34D399",
                    "warning": "#FBBF24",
                    "error": "#F87171",
                    "info": "#60A5FA",
                },
            },
            "fontFamily": {
                "sans": ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
                "mono": ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
            },
            "borderRadius": {
                "sm": "0.375rem",
                "DEFAULT": "0.5rem",
                "md": "0.625rem",
                "lg": "0.75rem",
                "xl": "1rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 1px 2px rgba(0,0,0,0.4)",
                "DEFAULT": "0 2px 4px rgba(0,0,0,0.5)",
                "md": "0 4px 8px rgba(0,0,0,0.6)",
                "lg": "0 8px 16px rgba(0,0,0,0.7)",
                "glow": "0 0 15px rgba(129,140,248,0.15)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Inter, -apple-system, sans-serif",
                "heading_weight": "600",
                "body_weight": "400",
                "line_height": "1.6",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "comfortable",
            },
            "component_patterns": {
                "card_radius": "0.75rem",
                "card_border": "1px solid #2E2E2E",
                "card_shadow": "0 2px 4px rgba(0,0,0,0.5)",
                "button_radius": "0.5rem",
                "button_style": "elevated surface color, subtle border, gentle hover brightening",
                "input_radius": "0.5rem",
                "input_style": "dark background (#1A1A1A), subtle border, focus ring with brand color glow",
                "icon_style": "outlined, medium stroke, muted by default, brighter on hover",
            },
        },
        "audience_match": {
            "recommended_for": [
                "developer-tool",
                "media-consumption",
                "productivity-tool",
                "mobile-app",
                "saas-product",
            ],
            "avoid_for": [
                "print-friendly",
                "children-app",
                "document-heavy",
            ],
        },
        "css_preview": (
            '<div style="font-family:Inter,sans-serif;background:#0F0F0F;border:1px solid #2E2E2E;'
            "border-radius:0.75rem;padding:16px;width:200px;\">"
            '<div style="font-size:14px;font-weight:600;color:#EDEDED;margin-bottom:6px;">'
            "Dark Mode</div>"
            '<div style="font-size:12px;color:#737373;margin-bottom:12px;">Easy on the eyes</div>'
            '<div style="display:flex;gap:6px;">'
            '<span style="background:#818CF8;color:#0F0F0F;padding:5px 12px;border-radius:0.5rem;'
            'font-size:11px;font-weight:500;">Primary</span>'
            '<span style="background:#262626;color:#A3A3A3;padding:5px 12px;border-radius:0.5rem;'
            'font-size:11px;border:1px solid #404040;">Surface</span>'
            "</div></div>"
        ),
    },
    {
        "id": "warm-tones",
        "name": "Warm Tones",
        "description": "Replaces cold whites and blues with cream, off-white, and warm amber tones. "
        "Creates an inviting, organic atmosphere reminiscent of natural materials like paper, "
        "sandstone, and warm wood. Reduces visual harshness while maintaining readability.",
        "best_for": "Eye comfort, softer feel, reading-heavy apps, and wellness brands",
        "category": "vibe",
        "tailwind_config": {
            "colors": {
                "brand": {
                    "primary": "#C2703E",
                    "secondary": "#7C9A5E",
                    "accent": "#D4A574",
                },
                "surface": {
                    "background": "#FFF8F0",
                    "card": "#FFFCF5",
                    "elevated": "#FFF3E6",
                },
                "text": {
                    "primary": "#3D2C2E",
                    "secondary": "#6B5B5E",
                    "muted": "#A89090",
                    "inverse": "#FFF8F0",
                },
                "border": {
                    "default": "#E8DDD0",
                    "strong": "#D4C4B0",
                    "subtle": "#F2EBE0",
                },
                "status": {
                    "success": "#7C9A5E",
                    "warning": "#D4956A",
                    "error": "#C75C5C",
                    "info": "#6B8FB0",
                },
            },
            "fontFamily": {
                "sans": ["Lora", "Merriweather", "Georgia", "serif"],
                "display": ["Playfair Display", "Lora", "serif"],
                "body": ["Source Sans 3", "Open Sans", "sans-serif"],
                "mono": ["IBM Plex Mono", "Courier New", "monospace"],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.5rem",
                "md": "0.625rem",
                "lg": "0.75rem",
                "xl": "1rem",
                "full": "9999px",
            },
            "boxShadow": {
                "sm": "0 1px 2px rgba(61,44,46,0.06)",
                "DEFAULT": "0 2px 4px rgba(61,44,46,0.08), 0 1px 2px rgba(61,44,46,0.04)",
                "md": "0 4px 8px rgba(61,44,46,0.08), 0 2px 4px rgba(61,44,46,0.04)",
                "lg": "0 8px 16px rgba(61,44,46,0.1), 0 4px 8px rgba(61,44,46,0.05)",
            },
        },
        "design_tokens": {
            "typography": {
                "font_family": "Lora, Merriweather, Georgia, serif",
                "heading_weight": "700",
                "body_weight": "400",
                "line_height": "1.7",
            },
            "spacing": {
                "base_unit": "4px",
                "density": "spacious",
            },
            "component_patterns": {
                "card_radius": "0.75rem",
                "card_border": "1px solid #E8DDD0",
                "card_shadow": "0 2px 4px rgba(61,44,46,0.08)",
                "button_radius": "0.5rem",
                "button_style": "warm fill colors, no hard edges, slightly heavier font weight, "
                "warm hover tint",
                "input_radius": "0.5rem",
                "input_style": "cream background, warm border, generous line-height for readability",
                "icon_style": "rounded, warm stroke color, slightly thicker (2px), organic feel",
            },
        },
        "audience_match": {
            "recommended_for": [
                "health-wellness",
                "reading-app",
                "food-recipe",
                "lifestyle-blog",
                "friendly-approachable",
                "50-plus-audience",
            ],
            "avoid_for": [
                "developer-tool",
                "gaming-entertainment",
                "young-edgy",
                "tech-startup",
            ],
        },
        "css_preview": (
            '<div style="font-family:Lora,Georgia,serif;background:#FFF8F0;border:1px solid #E8DDD0;'
            "border-radius:0.75rem;padding:16px;width:200px;\">"
            '<div style="font-size:14px;font-weight:700;color:#3D2C2E;margin-bottom:6px;">'
            "Warm Tones</div>"
            '<div style="font-size:12px;color:#A89090;margin-bottom:12px;line-height:1.5;">'
            "Gentle & inviting</div>"
            '<div style="display:flex;gap:6px;">'
            '<span style="background:#C2703E;color:#FFF8F0;padding:5px 12px;border-radius:0.5rem;'
            'font-size:11px;font-weight:600;">Warm</span>'
            '<span style="background:#FFF3E6;color:#6B5B5E;padding:5px 12px;border-radius:0.5rem;'
            'font-size:11px;border:1px solid #E8DDD0;">Soft</span>'
            "</div></div>"
        ),
    },
]


# =============================================================================
# Registry Lookup Functions
# =============================================================================


def get_style_registry() -> list[dict]:
    """
    Return all styles as a list of dicts with category grouping.

    Groups styles by their category (core vs vibe) for organized display
    in the UI style picker.

    Returns:
        List of dicts with keys: category, label, styles.
    """
    categories: dict[str, dict] = {
        "core": {
            "category": "core",
            "label": "Core Visual Styles",
            "styles": [],
        },
        "vibe": {
            "category": "vibe",
            "label": "Vibe / Aesthetic Styles",
            "styles": [],
        },
    }

    for style in STYLE_REGISTRY:
        cat = style.get("category", "core")
        if cat in categories:
            categories[cat]["styles"].append(style)

    return list(categories.values())


def get_style_option(style_id: str) -> dict | None:
    """
    Find and return a specific style by its unique ID.

    Searches across all styles in the registry.

    Args:
        style_id: The unique identifier of the style (e.g., "minimalism", "cyberpunk").

    Returns:
        The style dict if found, or None if no style matches the given ID.
    """
    for style in STYLE_REGISTRY:
        if style["id"] == style_id:
            return style
    return None


def get_style_tailwind_config(style_id: str) -> dict | None:
    """
    Get just the Tailwind CSS configuration for a style.

    Useful when only the theme extension values are needed, without
    the full style metadata.

    Args:
        style_id: The unique identifier of the style.

    Returns:
        The tailwind_config dict if found, or None if no style matches.
    """
    style = get_style_option(style_id)
    if style is None:
        return None
    return style.get("tailwind_config")


# =============================================================================
# Prompt Context Generation
# =============================================================================


def get_style_prompt_context(style_id: str) -> str:
    """
    Generate a comprehensive markdown prompt section describing the style's design system.

    This output is injected into the coding agent's prompt so it maintains
    consistent styling throughout feature implementation. Includes philosophy,
    color tokens, typography, component rules, layout guidance, Tailwind config,
    and do's/don'ts.

    Args:
        style_id: The unique identifier of the style.

    Returns:
        A markdown string ready for agent prompt injection. Returns a fallback
        message if the style ID is not found.
    """
    style = get_style_option(style_id)
    if style is None:
        logger.warning("Style '%s' not found in registry, returning fallback prompt context", style_id)
        return (
            f"## Design Style\n\n"
            f"The requested style `{style_id}` was not found in the registry. "
            f"Use clean, modern defaults with good contrast and consistent spacing."
        )

    tc = style["tailwind_config"]
    dt = style["design_tokens"]
    colors = tc["colors"]
    typo = dt["typography"]
    spacing = dt["spacing"]
    components = dt["component_patterns"]

    # Build the comprehensive prompt context
    sections: list[str] = []

    # -- Header and Philosophy --
    sections.append(f"## Design System: {style['name']}\n")
    sections.append(f"**Style ID:** `{style['id']}` | **Category:** {style['category']}\n")
    sections.append("### Philosophy\n")
    sections.append(f"{style['description']}\n")
    sections.append(f"**Best suited for:** {style['best_for']}\n")

    # -- Color Tokens --
    sections.append("### Color Tokens\n")
    sections.append("Use these exact colors throughout the application. Do NOT invent new colors.\n")

    sections.append("#### Brand Colors")
    sections.append("```")
    for name, value in colors["brand"].items():
        sections.append(f"  {name}: {value}")
    sections.append("```\n")

    sections.append("#### Surface Colors")
    sections.append("```")
    for name, value in colors["surface"].items():
        sections.append(f"  {name}: {value}")
    sections.append("```\n")

    sections.append("#### Text Colors")
    sections.append("```")
    for name, value in colors["text"].items():
        sections.append(f"  {name}: {value}")
    sections.append("```\n")

    sections.append("#### Border Colors")
    sections.append("```")
    for name, value in colors["border"].items():
        sections.append(f"  {name}: {value}")
    sections.append("```\n")

    sections.append("#### Status Colors")
    sections.append("```")
    for name, value in colors["status"].items():
        sections.append(f"  {name}: {value}")
    sections.append("```\n")

    # -- Typography --
    sections.append("### Typography\n")
    sections.append(f"- **Font Family:** `{typo['font_family']}`")
    sections.append(f"- **Heading Weight:** {typo['heading_weight']}")
    sections.append(f"- **Body Weight:** {typo['body_weight']}")
    sections.append(f"- **Line Height:** {typo['line_height']}")

    font_families = tc["fontFamily"]
    sections.append("\n**Font Stacks:**")
    for stack_name, stack_fonts in font_families.items():
        sections.append(f"- `{stack_name}`: {', '.join(stack_fonts)}")
    sections.append("")

    # -- Component Styling Rules --
    sections.append("### Component Styling Rules\n")
    sections.append("Apply these patterns consistently to every component.\n")

    sections.append("#### Cards")
    sections.append(f"- Border Radius: `{components['card_radius']}`")
    sections.append(f"- Border: `{components['card_border']}`")
    sections.append(f"- Shadow: `{components['card_shadow']}`")
    if "card_backdrop" in components:
        sections.append(f"- Backdrop Filter: `{components['card_backdrop']}`")
    sections.append("")

    sections.append("#### Buttons")
    sections.append(f"- Border Radius: `{components['button_radius']}`")
    sections.append(f"- Style: {components['button_style']}")
    sections.append("")

    sections.append("#### Inputs")
    sections.append(f"- Border Radius: `{components['input_radius']}`")
    sections.append(f"- Style: {components['input_style']}")
    sections.append("")

    sections.append("#### Icons")
    sections.append(f"- Style: {components['icon_style']}")
    sections.append("")

    # -- Layout and Spacing --
    sections.append("### Layout & Spacing\n")
    sections.append(f"- **Base Unit:** {spacing['base_unit']}")
    sections.append(f"- **Density:** {spacing['density']}")
    density_guidance = {
        "compact": "Use tighter padding (8-12px) and smaller gaps (4-8px). Prioritize information density.",
        "comfortable": "Use moderate padding (12-16px) and balanced gaps (8-12px). Standard spacing.",
        "spacious": "Use generous padding (16-24px) and wider gaps (12-20px). Emphasize breathing room.",
        "structured": "Use grid-aligned spacing. All values should be multiples of the base unit.",
    }
    density = spacing["density"]
    if density in density_guidance:
        sections.append(f"- **Guidance:** {density_guidance[density]}")
    sections.append("")

    # -- Tailwind Config Extension --
    sections.append("### Tailwind CSS Configuration\n")
    sections.append("Add this to your `tailwind.config.ts` or CSS `@theme` block:\n")
    sections.append("```javascript")
    sections.append("// tailwind.config.ts extend.theme")
    sections.append("{")

    # Colors
    sections.append("  colors: {")
    sections.append("    brand: {")
    for name, value in colors["brand"].items():
        sections.append(f"      '{name}': '{value}',")
    sections.append("    },")
    sections.append("    surface: {")
    for name, value in colors["surface"].items():
        sections.append(f"      '{name}': '{value}',")
    sections.append("    },")
    sections.append("    status: {")
    for name, value in colors["status"].items():
        sections.append(f"      '{name}': '{value}',")
    sections.append("    },")
    sections.append("  },")

    # Font Family
    sections.append("  fontFamily: {")
    for stack_name, stack_fonts in font_families.items():
        fonts_str = ", ".join(f"'{f}'" for f in stack_fonts)
        sections.append(f"    '{stack_name}': [{fonts_str}],")
    sections.append("  },")

    # Border Radius
    sections.append("  borderRadius: {")
    for name, value in tc["borderRadius"].items():
        sections.append(f"    '{name}': '{value}',")
    sections.append("  },")

    # Box Shadow
    sections.append("  boxShadow: {")
    for name, value in tc["boxShadow"].items():
        sections.append(f"    '{name}': '{value}',")
    sections.append("  },")

    sections.append("}")
    sections.append("```\n")

    # -- Do's and Don'ts --
    sections.append("### Do's and Don'ts\n")

    # Generate style-specific do's and don'ts based on the style characteristics
    dos_donts = _get_dos_and_donts(style_id, style)
    sections.append("**DO:**")
    for do_item in dos_donts["dos"]:
        sections.append(f"- {do_item}")
    sections.append("")
    sections.append("**DON'T:**")
    for dont_item in dos_donts["donts"]:
        sections.append(f"- {dont_item}")
    sections.append("")

    return "\n".join(sections)


def _get_dos_and_donts(style_id: str, style: dict) -> dict[str, list[str]]:
    """
    Return style-specific do's and don'ts for agent guidance.

    Each style has unique constraints that the agent must follow to maintain
    visual consistency. This function maps each style ID to curated guidelines.

    Args:
        style_id: The style identifier.
        style: The full style dict (used for fallback generic advice).

    Returns:
        Dict with 'dos' and 'donts' keys, each containing a list of strings.
    """
    guidelines: dict[str, dict[str, list[str]]] = {
        "flat-design": {
            "dos": [
                "Use solid, flat color fills for all surfaces and buttons",
                "Maintain consistent icon weight and style (outlined, monoline)",
                "Use color to create hierarchy instead of shadows or gradients",
                "Keep interactive states simple: color shift, no elevation change",
                "Use whitespace generously to separate content sections",
            ],
            "donts": [
                "Add drop shadows, gradients, or any 3D effects",
                "Use textures or patterns on backgrounds",
                "Mix outlined and filled icon styles",
                "Use more than 3-4 brand colors in a single view",
                "Add decorative borders when color alone suffices",
            ],
        },
        "minimalism": {
            "dos": [
                "Maximize white space; let content breathe",
                "Use typography as the primary visual element",
                "Limit the color palette to 2-3 colors maximum per view",
                "Use subtle transitions and micro-interactions",
                "Align everything to a strict grid system",
            ],
            "donts": [
                "Add decorative elements that don't serve a function",
                "Use bold or saturated colors for large areas",
                "Overcrowd layouts; every element needs breathing room",
                "Use heavy borders or thick dividers",
                "Add animations that are flashy or attention-grabbing",
            ],
        },
        "neumorphism": {
            "dos": [
                "Use the same background color for cards AND the page (elements emerge from surface)",
                "Apply dual shadows (light + dark) consistently to raised elements",
                "Use inset shadows for inputs, toggles, and pressed states",
                "Keep the color palette muted and close to the background tone",
                "Use accent colors sparingly for interactive elements only",
            ],
            "donts": [
                "Place neumorphic elements on differently-colored backgrounds",
                "Use flat/hard shadows; always use the soft dual-shadow technique",
                "Use high-contrast borders; neumorphism relies on shadows, not borders",
                "Apply this style to text-heavy pages; it works best for dashboards and controls",
                "Forget accessibility; ensure sufficient contrast for all text",
            ],
        },
        "glassmorphism": {
            "dos": [
                "Always use backdrop-filter: blur() on glass elements",
                "Place glass elements over colorful or gradient backgrounds for the best effect",
                "Use translucent whites/blacks for card backgrounds (rgba values)",
                "Add subtle luminous borders (rgba white 0.1-0.2) for glass edge definition",
                "Layer glass panels at different opacity levels for depth hierarchy",
            ],
            "donts": [
                "Use glass effects on plain white/single-color backgrounds (the effect is invisible)",
                "Skip the backdrop-filter; without blur the style doesn't work",
                "Use fully opaque backgrounds on any glass component",
                "Forget that backdrop-filter is GPU-intensive; limit glass layers per view",
                "Use glass effects for data-dense tables or forms; readability suffers",
            ],
        },
        "skeuomorphism": {
            "dos": [
                "Use subtle gradients (top-light to bottom-dark) on interactive elements",
                "Add inset highlights on the top edge of raised elements",
                "Use realistic shadow depth that matches implied light direction (top-left)",
                "Apply texture sparingly for premium feel (leather, linen, paper)",
                "Make buttons look physically pressable with gradient inversion on click",
            ],
            "donts": [
                "Use flat, solid colors without any depth or gradient",
                "Mix light directions; pick one consistent light source",
                "Over-texture every surface; use texture as accent, not default",
                "Ignore modern usability patterns; skeuomorphism should enhance, not confuse",
                "Apply this style to minimalist content; it works best with rich interfaces",
            ],
        },
        "neubrutalism": {
            "dos": [
                "Use thick black borders (2-3px) on ALL interactive elements and cards",
                "Apply hard offset shadows (no blur) using solid black",
                "Use clashing, vibrant color combinations confidently",
                "Keep border-radius at 0 for the authentic brutalist look",
                "Make hover states shift the element (translate) to collapse the shadow",
            ],
            "donts": [
                "Add border-radius to cards or buttons (this breaks the style)",
                "Use soft/blurred shadows; shadows must be hard, offset, and solid",
                "Use muted or pastel colors; neubrutalism demands bold, saturated palettes",
                "Over-polish the design; rawness is intentional, not a bug",
                "Forget accessibility; bold colors still need WCAG-compliant text contrast",
            ],
        },
        "bauhaus": {
            "dos": [
                "Use only primary colors (red, blue, yellow) plus black and white as accents",
                "Build layouts on strict geometric grids",
                "Use geometric shapes (circles, triangles, squares) as design elements",
                "Apply heavy typographic hierarchy with bold, uppercase headings",
                "Maintain mathematical precision in spacing and alignment",
            ],
            "donts": [
                "Use rounded, organic shapes or curves (stay geometric)",
                "Add gradients, shadows, or decorative flourishes",
                "Use more than the core Bauhaus palette without deliberate intent",
                "Break the grid alignment; every element should snap to the grid",
                "Use script or decorative fonts; stick to geometric sans-serif typefaces",
            ],
        },
        "claymorphism": {
            "dos": [
                "Use very rounded corners (1rem+) on all components",
                "Apply both outer AND inner shadows for the clay/molded look",
                "Use soft pastel colors as the base palette",
                "Add subtle inner highlights (top edge) for the sculpted 3D effect",
                "Use playful, rounded typography (Quicksand, Nunito)",
            ],
            "donts": [
                "Use sharp corners or zero border-radius",
                "Use harsh, saturated colors; keep everything soft and pastel",
                "Skip the inner shadow; without it, elements look flat, not clay-like",
                "Use thin, angular typography; the font should match the soft aesthetic",
                "Apply this to data-dense interfaces; it works best for consumer-facing apps",
            ],
        },
        "retro-futurism": {
            "dos": [
                "Use neon colors (#FF6EC7, #00FFFF, #FFD700) as accents on dark backgrounds",
                "Add text-shadow and box-shadow glows in neon colors",
                "Use synthwave-style gradients (pink to purple to blue) for backgrounds",
                "Choose futuristic/technical fonts like Orbitron or Space Grotesk",
                "Create depth with layered neon borders and subtle glow effects",
            ],
            "donts": [
                "Use neon colors on light backgrounds (they lose their glow effect)",
                "Use standard corporate fonts; typography must feel futuristic/retro",
                "Overdo the glow effects; 2-3 neon accents per view maximum",
                "Use flat design patterns; this style needs depth, glow, and atmosphere",
                "Forget the vintage aspect; mix neon futurism with retro grid/chrome touches",
            ],
        },
        "cyberpunk": {
            "dos": [
                "Use near-black backgrounds (#0A0A0F) with neon accent colors",
                "Apply neon glow box-shadows on interactive elements",
                "Use monospace or tech-inspired fonts for a terminal/hacker aesthetic",
                "Create angular, sharp UI elements (low border-radius, clip-path angles)",
                "Add subtle scanline or glitch effects for atmosphere",
            ],
            "donts": [
                "Use warm, friendly colors or rounded, soft shapes",
                "Use serif or handwriting fonts; everything should feel digital/tech",
                "Make backgrounds anything lighter than very dark gray",
                "Use more than 2-3 neon accent colors per view; it becomes garish",
                "Forget contrast; neon text must be readable against dark backgrounds",
            ],
        },
        "dark-mode": {
            "dos": [
                "Use surface elevation (lighter shades of gray) to create hierarchy",
                "Maintain WCAG AA contrast ratios (4.5:1 for body text, 3:1 for large text)",
                "Use desaturated accent colors; pure neons are too harsh on dark backgrounds",
                "Apply subtle borders (#2E2E2E) to define card edges",
                "Test on actual OLED screens; pure black (#000000) vs near-black (#0F0F0F) matters",
            ],
            "donts": [
                "Use pure white (#FFFFFF) text; use off-white (#EDEDED) to reduce eye strain",
                "Use the same shadow values as light mode; dark mode needs different shadow opacity",
                "Invert light mode colors directly; dark mode requires deliberate palette design",
                "Use fully saturated colors for large areas; they vibrate against dark backgrounds",
                "Forget hover/focus states; they need to be more visible than in light mode",
            ],
        },
        "warm-tones": {
            "dos": [
                "Replace all pure whites with cream (#FFF8F0) and off-whites",
                "Use warm grays (with brown/amber undertones) instead of cool grays",
                "Choose serif or rounded sans-serif fonts for a warm, human feel",
                "Apply warm-tinted shadows (using brown/amber, not pure black)",
                "Use earth-tone accent colors (terracotta, sage, amber, clay)",
            ],
            "donts": [
                "Use pure white (#FFFFFF) or cool blue-tinted grays",
                "Use neon or electric accent colors; keep everything warm and natural",
                "Use geometric, technical fonts; they clash with the warm aesthetic",
                "Apply cool-tinted shadows (blue/gray); shadows should be warm",
                "Mix warm backgrounds with cold accent colors (electric blue, neon green)",
            ],
        },
    }

    if style_id in guidelines:
        return guidelines[style_id]

    # Fallback for any unknown style (should not happen with the fixed registry)
    return {
        "dos": [
            f"Follow the {style['name']} design language consistently",
            "Use the specified color tokens for all elements",
            "Maintain consistent spacing and typography",
            "Test components for visual consistency",
        ],
        "donts": [
            "Mix this style with conflicting design patterns",
            "Invent new colors outside the defined palette",
            "Ignore the specified component patterns",
            "Break the established visual hierarchy",
        ],
    }


# =============================================================================
# Style Recommendation Engine
# =============================================================================

# Scoring matrices for the recommendation engine. Each maps a user-provided
# value to a dict of style_id -> score_contribution. Higher scores mean
# stronger recommendation.

_AUDIENCE_SCORES: dict[str, dict[str, int]] = {
    "health-conscious": {
        "warm-tones": 5,
        "minimalism": 4,
        "claymorphism": 4,
        "flat-design": 3,
        "dark-mode": 2,
        "neumorphism": 2,
    },
    "young-edgy": {
        "neubrutalism": 5,
        "cyberpunk": 5,
        "retro-futurism": 4,
        "glassmorphism": 3,
        "dark-mode": 3,
        "bauhaus": 2,
    },
    "premium-luxury": {
        "minimalism": 5,
        "glassmorphism": 4,
        "dark-mode": 4,
        "neumorphism": 3,
        "warm-tones": 3,
        "skeuomorphism": 2,
    },
    "friendly-approachable": {
        "claymorphism": 5,
        "warm-tones": 5,
        "flat-design": 4,
        "minimalism": 3,
        "skeuomorphism": 2,
    },
    "finance-dashboard": {
        "neumorphism": 5,
        "dark-mode": 4,
        "minimalism": 4,
        "flat-design": 3,
        "glassmorphism": 2,
    },
    "gaming-entertainment": {
        "cyberpunk": 5,
        "retro-futurism": 5,
        "neubrutalism": 3,
        "glassmorphism": 3,
        "dark-mode": 3,
    },
}

_VIBE_SCORES: dict[str, dict[str, int]] = {
    "trustworthy": {
        "minimalism": 5,
        "flat-design": 4,
        "dark-mode": 3,
        "warm-tones": 3,
        "neumorphism": 2,
    },
    "fun": {
        "neubrutalism": 5,
        "claymorphism": 5,
        "retro-futurism": 4,
        "flat-design": 2,
        "bauhaus": 2,
    },
    "modern": {
        "glassmorphism": 5,
        "minimalism": 4,
        "dark-mode": 4,
        "cyberpunk": 3,
        "flat-design": 3,
    },
    "nostalgic": {
        "retro-futurism": 5,
        "skeuomorphism": 5,
        "warm-tones": 3,
        "bauhaus": 3,
        "neubrutalism": 2,
    },
    "edgy": {
        "cyberpunk": 5,
        "neubrutalism": 5,
        "retro-futurism": 3,
        "glassmorphism": 2,
        "dark-mode": 2,
    },
    "warm": {
        "warm-tones": 5,
        "claymorphism": 4,
        "skeuomorphism": 3,
        "minimalism": 2,
        "flat-design": 2,
    },
}

_AGE_GROUP_SCORES: dict[str, dict[str, int]] = {
    "under-30": {
        "neubrutalism": 4,
        "cyberpunk": 4,
        "glassmorphism": 3,
        "retro-futurism": 3,
        "dark-mode": 2,
        "claymorphism": 2,
        "bauhaus": 1,
    },
    "30-50": {
        "minimalism": 4,
        "flat-design": 3,
        "glassmorphism": 3,
        "dark-mode": 3,
        "neumorphism": 2,
        "warm-tones": 2,
        "bauhaus": 2,
    },
    "50-plus": {
        "warm-tones": 5,
        "flat-design": 4,
        "minimalism": 3,
        "skeuomorphism": 3,
        "neumorphism": 2,
        "dark-mode": 2,
    },
}

# Human-readable reasons for why each style suits certain contexts.
# Used to populate the 'reason' field in recommendation results.
_STYLE_REASONS: dict[str, str] = {
    "flat-design": "Clean, universally readable, and scales well across all devices and screen sizes",
    "minimalism": "Premium, distraction-free experience that lets content take center stage",
    "neumorphism": "Tactile, physical feel ideal for interactive controls and dashboard widgets",
    "glassmorphism": "Modern, layered depth that feels futuristic and visually striking",
    "skeuomorphism": "Familiar, intuitive interactions that mirror real-world objects",
    "neubrutalism": "Bold, unapologetic aesthetic that grabs attention and stands out",
    "bauhaus": "Timeless geometric precision with strong visual structure and hierarchy",
    "claymorphism": "Warm, playful dimensionality that feels approachable and inviting",
    "retro-futurism": "Nostalgic neon atmosphere perfect for entertainment and creative experiences",
    "cyberpunk": "High-tech, edgy aesthetic that resonates with digital-native audiences",
    "dark-mode": "Eye-friendly, modern interface optimized for extended use and OLED displays",
    "warm-tones": "Gentle, organic feel that reduces visual strain and conveys warmth",
}


def recommend_style(audience: str, vibe: str, age_group: str) -> list[dict]:
    """
    Given audience type, vibe, and age group, return ranked style recommendations.

    Scores each style by summing weights from three scoring dimensions
    (audience, vibe, age_group), then returns all styles with a non-zero
    score sorted by total score descending.

    Args:
        audience: One of "health-conscious", "young-edgy", "premium-luxury",
                  "friendly-approachable", "finance-dashboard", "gaming-entertainment".
        vibe: One of "trustworthy", "fun", "modern", "nostalgic", "edgy", "warm".
        age_group: One of "under-30", "30-50", "50-plus".

    Returns:
        List of dicts sorted by score descending, each containing:
        - style_id: The style identifier
        - style_name: Human-readable style name
        - score: Total recommendation score (higher = better match)
        - reason: Human-readable explanation of why this style fits
    """
    scores: dict[str, int] = {}

    # Accumulate scores from all three dimensions
    audience_map = _AUDIENCE_SCORES.get(audience, {})
    for style_id, score in audience_map.items():
        scores[style_id] = scores.get(style_id, 0) + score

    vibe_map = _VIBE_SCORES.get(vibe, {})
    for style_id, score in vibe_map.items():
        scores[style_id] = scores.get(style_id, 0) + score

    age_map = _AGE_GROUP_SCORES.get(age_group, {})
    for style_id, score in age_map.items():
        scores[style_id] = scores.get(style_id, 0) + score

    # Build result list with style metadata
    results: list[dict] = []
    for style_id, total_score in scores.items():
        style = get_style_option(style_id)
        if style is None:
            continue
        results.append({
            "style_id": style_id,
            "style_name": style["name"],
            "score": total_score,
            "reason": _STYLE_REASONS.get(style_id, f"Matches the selected criteria for {style['name']}"),
        })

    # Sort by score descending, then alphabetically by name for ties
    results.sort(key=lambda x: (-x["score"], x["style_name"]))

    return results
