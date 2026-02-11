"""
Style Extractor
===============

Analyzes a screenshot using a vision-capable LLM to identify the UI design
style and extract design tokens into a reusable style sheet.

Implements the mentor's "Idea Code" methodology for extracting the Visual DNA
from any application screenshot into a production-ready design system.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Full Idea Code Extraction Prompt (Production Version)
# =============================================================================

EXTRACTION_PROMPT = """
Role: You are an expert Design System Architect and Senior Frontend Engineer.
You specialize in "Atomic Design" principles and creating abstract, reusable
component libraries.

Objective: I will provide an image. Your task is to ignore the specific content,
text, and business context of the image. Instead, extract the underlying Visual
Design Language (the "Visual DNA"). I need a generic, reusable style guide that
I can apply to any type of application, not just the one shown in the image.

Strict Constraints (Read Carefully):
1. Do not mention specific text found in the image
2. Do not mention specific business logic
3. Generalize all findings into reusable tokens and classes
4. Name tokens by FUNCTION not content (brand-DEFAULT not "revenue-title-color")

Output Requirements - Generate a Technical Design System Report covering:

### 1. Abstract Color Tokens (Global Variables)
Extract the palette named by function:
- Brand/Primary: (main interaction color with light/DEFAULT/dark variants)
- Surface/Backgrounds: (canvas, base/cards, muted/inputs)
- Text Hierarchy: (primary, secondary/muted, tertiary)
- Borders/Dividers: (line colors)
- Status Colors: (success, error, warning if present)

Provide EXACT hex values where possible, with [approx] tag if estimated.

### 2. Global Typography System
- Font family (or closest Google Font match)
- Define the abstract hierarchy:
  Display/Hero | Headings (H1-H3) | Body (regular/bold) | Microcopy
- Include weights (400-700) and approximate line-heights

### 3. Universal Component Patterns
- Surfaces/Cards: radius, border, shadow, background (provide CSS values)
- Buttons: primary/secondary styles (padding, radius, color, hover)
- Form Inputs: background, border, radius
- Icons: visual style description (stroke weight, caps, fill)

### 4. Layout & Spacing Physics
- Spacing scale base unit (4px, 8px, or 10px)
- Density: Cozy (whitespace-heavy) or Compact (data-dense)
- Radius consistency rule

### 5. Tailwind CSS Theme Extension
Provide a valid JSON object (NOT JavaScript module.exports) for the theme extension:
```json
{
  "colors": {
    "brand": { "light": "#hex", "DEFAULT": "#hex", "dark": "#hex" },
    "surface": { "canvas": "#hex", "base": "#hex", "muted": "#hex" },
    "text": { "primary": "#hex", "secondary": "#hex", "tertiary": "#hex" },
    "border": { "subtle": "#hex" }
  },
  "fontFamily": { "sans": ["FontName", "fallback"] },
  "borderRadius": { "card": "Xpx", "input": "Xpx", "btn": "Xpx" },
  "boxShadow": { "card": "shadow-value" }
}
```

### 6. Style Classification
From the following known styles, identify the PRIMARY match and optional
ACCENT match (if interactive elements differ from layout style):
Flat Design, Minimalism, Neumorphism, Glassmorphism, Skeuomorphism,
Neubrutalism, Bauhaus, Claymorphism, Retro Futurism, Cyberpunk,
Dark Mode Elegant, Warmer Shades

Format your classification as:
PRIMARY_STYLE: style-id (confidence: high/medium/low)
ACCENT_STYLE: style-id or none (confidence: high/medium/low)

Use these exact style IDs: flat-design, minimalism, neumorphism, glassmorphism,
skeuomorphism, neubrutalism, bauhaus, claymorphism, retro-futurism, cyberpunk,
dark-mode, warmer-shades
""".strip()


# Map display names to style IDs for fuzzy matching
STYLE_NAME_TO_ID = {
    "flat design": "flat-design",
    "flat": "flat-design",
    "minimalism": "minimalism",
    "minimal": "minimalism",
    "minimalist": "minimalism",
    "neumorphism": "neumorphism",
    "neumorphic": "neumorphism",
    "glassmorphism": "glassmorphism",
    "glass": "glassmorphism",
    "skeuomorphism": "skeuomorphism",
    "skeuomorphic": "skeuomorphism",
    "neubrutalism": "neubrutalism",
    "neo-brutalism": "neubrutalism",
    "neo brutalism": "neubrutalism",
    "bauhaus": "bauhaus",
    "claymorphism": "claymorphism",
    "clay": "claymorphism",
    "retro futurism": "retro-futurism",
    "retro-futurism": "retro-futurism",
    "retro": "retro-futurism",
    "synthwave": "retro-futurism",
    "cyberpunk": "cyberpunk",
    "cyber": "cyberpunk",
    "dark mode": "dark-mode",
    "dark mode elegant": "dark-mode",
    "dark": "dark-mode",
    "warmer shades": "warmer-shades",
    "warm": "warmer-shades",
}

VALID_STYLE_IDS = {
    "flat-design", "minimalism", "neumorphism", "glassmorphism",
    "skeuomorphism", "neubrutalism", "bauhaus", "claymorphism",
    "retro-futurism", "cyberpunk", "dark-mode", "warmer-shades",
}


def _normalize_style_id(raw: str) -> str | None:
    """Try to normalize a raw style name/ID to a valid style ID."""
    cleaned = raw.strip().lower().strip("'\"")
    if cleaned in VALID_STYLE_IDS:
        return cleaned
    return STYLE_NAME_TO_ID.get(cleaned)


def _parse_confidence(text: str) -> str:
    """Extract confidence level from text."""
    text_lower = text.lower()
    if "high" in text_lower:
        return "high"
    if "medium" in text_lower or "moderate" in text_lower:
        return "medium"
    return "low"


def _extract_tailwind_json(text: str) -> dict | None:
    """Extract the Tailwind theme JSON from the response text."""
    # Try to find JSON block in code fence
    json_patterns = [
        r'```json\s*\n(.*?)\n\s*```',
        r'```\s*\n(\{.*?\})\n\s*```',
    ]
    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    # Try to find a standalone JSON object that looks like a Tailwind config
    obj_match = re.search(r'(\{[^{}]*"colors"[^{}]*\{.*?\}.*?\})', text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def _parse_style_classification(text: str) -> dict:
    """Parse style classification from the response text."""
    result = {
        "primary": None,
        "primary_confidence": "low",
        "accent": None,
        "accent_confidence": "low",
    }

    # Look for PRIMARY_STYLE: pattern
    primary_match = re.search(
        r'PRIMARY_STYLE:\s*([a-zA-Z\s-]+?)(?:\s*\(confidence:\s*(high|medium|low)\))?',
        text, re.IGNORECASE,
    )
    if primary_match:
        style_id = _normalize_style_id(primary_match.group(1))
        if style_id:
            result["primary"] = style_id
            result["primary_confidence"] = primary_match.group(2) or "medium"

    # Look for ACCENT_STYLE: pattern
    accent_match = re.search(
        r'ACCENT_STYLE:\s*([a-zA-Z\s-]+?)(?:\s*\(confidence:\s*(high|medium|low)\))?',
        text, re.IGNORECASE,
    )
    if accent_match:
        raw_accent = accent_match.group(1).strip().lower()
        if raw_accent not in ("none", "n/a", "null", ""):
            style_id = _normalize_style_id(raw_accent)
            if style_id:
                result["accent"] = style_id
                result["accent_confidence"] = accent_match.group(2) or "medium"

    # Fallback: look for "Primary: Style Name" pattern
    if not result["primary"]:
        fallback = re.search(
            r'(?:primary|main|base)\s*(?:style)?[:=]\s*([a-zA-Z\s-]+?)(?:\s*\(|$|\n)',
            text, re.IGNORECASE,
        )
        if fallback:
            style_id = _normalize_style_id(fallback.group(1))
            if style_id:
                result["primary"] = style_id
                result["primary_confidence"] = "medium"

    return result


def parse_extraction_response(response_text: str) -> dict:
    """Parse the LLM response into structured extraction data.

    Args:
        response_text: The raw text response from the vision LLM.

    Returns:
        Structured dict with identified_style, extracted_tokens,
        style_guide_markdown, and tailwind_config.
    """
    classification = _parse_style_classification(response_text)
    tailwind_config = _extract_tailwind_json(response_text) or {}

    return {
        "identified_style": classification,
        "extracted_tokens": tailwind_config,
        "style_guide_markdown": response_text,
        "tailwind_config": tailwind_config,
    }


async def extract_style_from_image(image_base64: str) -> dict:
    """Send screenshot to vision LLM with the extraction prompt.

    This function sends the image to a Claude model with the Idea Code
    extraction prompt and parses the structured response.

    Args:
        image_base64: Base64-encoded image data (png or jpg).

    Returns:
        Structured dict with:
        - identified_style: {primary, primary_confidence, accent, accent_confidence}
        - extracted_tokens: Tailwind config JSON
        - style_guide_markdown: Full markdown style guide
        - tailwind_config: Parsed Tailwind theme extension

    Raises:
        RuntimeError: If the API call fails.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "The anthropic package is required for screenshot extraction. "
            "Install it with: pip install anthropic"
        )

    # Determine media type from base64 header or default to png
    media_type = "image/png"
    if image_base64.startswith("/9j/"):
        media_type = "image/jpeg"
    elif image_base64.startswith("iVBOR"):
        media_type = "image/png"
    elif image_base64.startswith("R0lGOD"):
        media_type = "image/gif"

    # Strip data URI prefix if present
    if "," in image_base64 and image_base64.index(",") < 100:
        parts = image_base64.split(",", 1)
        if "base64" in parts[0]:
            # Extract media type from data URI
            type_match = re.match(r'data:(\w+/\w+)', parts[0])
            if type_match:
                media_type = type_match.group(1)
            image_base64 = parts[1]

    client = anthropic.Anthropic()

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        logger.error("Vision API call failed: %s", e)
        raise RuntimeError(f"Failed to analyze screenshot: {e}")

    response_text = message.content[0].text if message.content else ""
    return parse_extraction_response(response_text)
