# Idea Code Style Guide Generator Integration

## What This Is

The mentor's "Idea Code" methodology uses a specific prompt format to extract
design systems from screenshots. This prompt is already partially captured in
`STYLE_GUIDE_GENERATOR_PROMPT` in `server/services/style_manager.py`, but it's
only used as a template for generating style guides from our predefined styles.

This handoff covers integrating the FULL Idea Code prompt as:
1. The extraction engine for the screenshot-to-style feature
2. The output format standard for all generated style guides

## The Full Idea Code Prompt (Production Version)

This is the mentor's prompt, adapted for our system:

```
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
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: { light, DEFAULT, dark },
        surface: { canvas, base, muted },
        text: { primary, secondary, tertiary },
        border: { subtle },
      },
      fontFamily: { sans: [...] },
      borderRadius: { card, input, btn },
      boxShadow: { card },
    }
  }
}
```

### 6. Style Classification
From the following known styles, identify the PRIMARY match and optional
ACCENT match (if interactive elements differ from layout style):
Flat Design, Minimalism, Neumorphism, Glassmorphism, Skeuomorphism,
Neubrutalism, Bauhaus, Claymorphism, Retro Futurism, Cyberpunk,
Dark Mode Elegant, Warmer Shades

Format: "Primary: [style] (confidence: high/medium/low)"
Optional: "Accent: [style] for [which elements] (confidence: high/medium/low)"
```

## Where This Prompt Lives in the Codebase

Currently `STYLE_GUIDE_GENERATOR_PROMPT` in `style_manager.py` (line ~143) is a
simplified version used for injecting known style data into agent prompts.

For the screenshot extraction feature, the full prompt above would live in:
`server/services/style_extractor.py` as `EXTRACTION_PROMPT`

## Integration Points

1. **Screenshot extraction** (`style_extractor.py`): Uses the full prompt with an image
2. **Style guide generation** (`style_manager.py`): Uses the simplified version with known data
3. **Output format**: Both produce the same markdown structure (sections 1-5)
4. **Section 6 (classification)**: Only used in screenshot extraction mode

The key insight: the Idea Code format IS our style guide format. Every predefined
style's `get_style_guide_markdown()` already outputs in this same structure
(sections 1-5 + section 6 do's/don'ts). So extracted styles and predefined styles
produce identical output - the agent doesn't care where it came from.
