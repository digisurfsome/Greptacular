# Screenshot Style Extractor: Reverse-Engineer Any App's Design System

## Two Products Here

### Product A: Standalone App (Lead Magnet / Low-Cost SaaS)
A simple web app where anyone can upload a screenshot of any app they like and get back:
1. The identified base style (from our 12-style registry)
2. Whether it's a mix of two styles (and which ones)
3. A complete, production-ready style sheet they can paste into their project
4. The mentor's "Idea Code" style guide format output

**This is the lead magnet.** Give it away free or charge $5/month. It hooks people into the full AutoForge system.

### Product B: Integration into AutoForge
Add a "Upload a screenshot" option alongside "Pick a style" in the project creation wizard. User uploads a screenshot, AI extracts the style, generates the style sheet, and it flows into the same pipeline as the style picker.

---

## Product A: Standalone App Architecture

### User Flow (60 seconds total)
```
Upload screenshot
    → AI analyzes the image
    → "This looks like Minimalism with Glassmorphism accents"
    → Shows the extracted color palette, typography guess, component patterns
    → Generates complete style sheet in multiple formats:
        - Tailwind CSS theme config
        - CSS custom properties
        - The mentor's Idea Code format
        - Raw design tokens JSON
    → "Copy to clipboard" / "Download" / "Send to AutoForge"
```

### The AI Prompt (This is the core)

This is the mentor's "Idea Code" prompt adapted for style IDENTIFICATION + style sheet generation:

```
Role: You are an expert Design System Architect. You specialize in identifying
and classifying visual design languages.

Task: I will provide a screenshot of an app or website. Your job is to:

1. IDENTIFY the primary UI design style from this list:
   - Flat Design, Minimalism, Neumorphism, Glassmorphism, Skeuomorphism,
     Neubrutalism, Bauhaus, Claymorphism, Retro Futurism, Cyberpunk,
     Dark Mode Elegant, Warmer Shades

2. IDENTIFY if there's a secondary/accent style applied to interactive elements
   (buttons, inputs, toggles) that differs from the base layout style.

3. EXTRACT the Visual DNA - the specific design tokens being used:

   COLOR TOKENS (extract exact hex values from the screenshot):
   - Brand/Primary color
   - Surface colors (background, card, muted)
   - Text colors (primary, secondary, tertiary)
   - Border colors
   - Status colors if visible (success, error, warning)

   TYPOGRAPHY (identify or approximate):
   - Font family (or closest Google Font match)
   - Size hierarchy (heading, body, micro sizes)
   - Weight usage patterns

   COMPONENT PATTERNS:
   - Card style (border, radius, shadow, background)
   - Button style (background, border, radius, padding, hover clues)
   - Input style (background, border, radius)
   - Icon style (line weight, caps, fill)

   SPACING:
   - Base unit estimate (4px, 8px, etc.)
   - Density (cozy, balanced, compact)
   - Corner radius consistency

4. OUTPUT a complete style sheet in this exact format:
   [Tailwind config object]
   [CSS custom properties block]
   [Design tokens JSON]

Strict Constraints:
- Name tokens by FUNCTION not content (brand-DEFAULT not "login-button-blue")
- Generalize all findings into reusable tokens
- If you can't determine exact values, give your best approximation with [approx] tag
- Always identify the closest match from the 12 known styles
- If it's a custom/hybrid style, say which 2 styles it most closely combines
```

### Tech Stack (Keep It Dead Simple)

```
Frontend: Single HTML page with Tailwind (or React if you want it SPA)
Backend:  Single API endpoint that:
          1. Accepts image upload (base64 or multipart)
          2. Sends to Claude/GPT-4V with the prompt above
          3. Parses the structured response
          4. Returns JSON with style ID, tokens, and formatted outputs

No database needed. Stateless. Can run on Vercel/Netlify serverless.
```

### API Shape

```
POST /api/extract-style
  Body: { image: base64_string }
  Response: {
    "identified_style": {
      "primary": "minimalism",
      "primary_confidence": 0.85,
      "accent": "glassmorphism",      // null if pure single style
      "accent_confidence": 0.72
    },
    "extracted_tokens": {
      "color_tokens": { ... },
      "typography": { ... },
      "components": { ... },
      "spacing": { ... }
    },
    "outputs": {
      "tailwind_config": "module.exports = { theme: { extend: { ... } } }",
      "css_variables": ":root { --brand-primary: #...; ... }",
      "design_tokens_json": { ... },
      "idea_code_format": "## Style Guide Analysis\n..."
    },
    "style_sheet_markdown": "# Extracted Design System\n\n## 1. Color Tokens\n..."
  }
```

### Revenue Model Options

1. **Free tier:** 3 extractions/day, watermarked output
2. **Pro ($5-9/mo):** Unlimited extractions, all output formats, "Send to AutoForge" button
3. **Lead magnet:** Completely free, but requires email signup → funnels to AutoForge

### Marketing Angle

Everyone on YouTube is saying "find an app you like, screenshot it, give it to AI."
Your tool says: "Great, do that. But instead of a loose screenshot, get a REAL style sheet."
It's the bridge between what everyone's already doing and doing it RIGHT.

Tagline: **"Stop copying screenshots. Start copying design systems."**

---

## Product B: Integration into AutoForge

### Where It Fits in the Flow

Current flow: Name → Folder → Boilerplate → **Style Picker** → Method → Chat

New flow: Name → Folder → Boilerplate → **Style Picker (3 tabs)** → Method → Chat

The Style Picker step gets 3 tabs:
1. **Browse Styles** (existing) - Pick from 12 predefined styles
2. **Describe Your App** (just built) - AI recommends based on description
3. **Extract from Screenshot** (NEW) - Upload image, AI extracts style

### UI for Tab 3

```
┌─────────────────────────────────────────┐
│  [Browse Styles] [Describe] [Screenshot]│
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │   Drop an image here or click    │  │
│  │        to upload (.png/.jpg)      │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ── After upload + analysis ──          │
│                                         │
│  Detected: Minimalism + Glassmorphism   │
│  Confidence: 85%                        │
│                                         │
│  Extracted palette:                     │
│  [■ #111827] [■ #FFFFFF] [■ #A855F7]   │
│                                         │
│  [Use This Style]  [Try Another Image]  │
│                                         │
└─────────────────────────────────────────┘
```

### How "Use This Style" Works

When the user clicks "Use This Style" after screenshot extraction:
1. The extracted tokens are saved as a CUSTOM style entry (not one of the 12 predefined)
2. A `style_guide.md` is generated from the extracted tokens (same format as predefined styles)
3. The style_id in project_config.json is set to `"custom-extracted"`
4. The full extracted style guide markdown is saved to `.autoforge/style_guide.md`
5. The existing `_get_style_context()` in prompts.py already reads this file - no changes needed

### Backend for Screenshot Extraction

New file: `server/services/style_extractor.py`

```python
"""
Style Extractor
===============

Analyzes a screenshot using a vision-capable LLM to identify the UI design
style and extract design tokens into a reusable style sheet.
"""

async def extract_style_from_image(image_base64: str) -> dict:
    """
    Send screenshot to vision LLM with the extraction prompt.
    Parse structured response into style identification + tokens.

    Returns:
        {
            "identified_style": {"primary": "minimalism", "accent": "glassmorphism" | None},
            "extracted_tokens": { color_tokens, typography, components, spacing },
            "style_guide_markdown": "# Extracted Design System\n...",
            "tailwind_config": { ... },
        }
    """
    # 1. Build the prompt (the big extraction prompt from above)
    # 2. Call Claude/GPT-4V with image + prompt
    # 3. Parse the response (the LLM returns structured markdown)
    # 4. Extract the JSON/config portions
    # 5. Return structured result
    pass
```

New endpoint in `server/routers/projects.py`:

```python
@styles_router.post("/extract-from-screenshot")
async def extract_from_screenshot(body: dict):
    """Accept a base64 image and return extracted style analysis."""
    image_data = body.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="No image provided")

    from ..services.style_extractor import extract_style_from_image
    result = await extract_style_from_image(image_data)
    return result
```

### Implementation Order

**Phase 1: Standalone app (Product A) - can be built independently**
1. Create the extraction prompt (adapt mentor's Idea Code prompt)
2. Build single-endpoint API that accepts image + returns style analysis
3. Build simple upload UI (single page)
4. Test with 10-20 diverse app screenshots to validate accuracy
5. Deploy as standalone (Vercel/Netlify)

**Phase 2: AutoForge integration (Product B)**
1. Add `style_extractor.py` service
2. Add `/api/styles/extract-from-screenshot` endpoint
3. Add Tab 3 UI to NewProjectModal style step
4. Handle custom extracted styles in project_config.json
5. Test end-to-end: screenshot → extraction → style guide → agent uses it

### Key Decision: Which Vision Model?

The extraction needs a vision-capable model. Options:
- **Claude (Sonnet/Opus)** - Best quality, already in the stack, supports base64 images
- **GPT-4V** - Good quality, would need separate API key
- **Gemini** - Free tier available, good for the standalone lead magnet app

For AutoForge integration, use whatever model the user already has configured.
For the standalone app, Claude Sonnet is the best balance of quality and cost.

### Accuracy Expectations

The style identification won't be 100% accurate - some apps use custom hybrid styles that don't cleanly map to our 12 categories. That's fine. The value is:
1. Getting the CLOSEST match (or identifying a 2-style mix)
2. Extracting actual color hex values, radius patterns, shadow styles
3. Generating a usable style sheet regardless of perfect classification

Even if it says "this is 70% Minimalism with Glassmorphism accents" and you disagree, the extracted HEX values and component patterns are still correct and usable.

---

## Files Reference

**Existing files this builds on:**
- `server/services/style_manager.py` - The 12 style definitions (tokens, configs, etc.)
- `server/services/style_modifiers.py` - Accessibility modifiers
- `server/routers/projects.py` - Style API endpoints
- `prompts.py` - `_get_style_context()` reads style_guide.md (already handles custom guides)
- `ui/src/components/NewProjectModal.tsx` - Style picker step in project creation

**New files to create:**
- `server/services/style_extractor.py` - Vision LLM integration for extraction
- Standalone app: separate repo or `tools/style-extractor/` directory
