# Spec 007 — Skin Builder (Screenshot → Stylesheet)

## What This Is
You take a screenshot of any app, website, or product that has the look you want. Feed it into the Skin Builder. It generates a complete CSS stylesheet + theme file that makes your skin look exactly like that reference. No design decisions. No Figma. No designer. One screenshot, one prompt run, done.

## Why It Matters
The skin is what makes a pipeline look like a product. Without theming, every deployment looks the same. With the Skin Builder, every deployment can look completely different — match a client's brand, match a competitor's style, match any aesthetic you want — in minutes, not days. This is the "heat shrink" that forms perfectly to whatever shape it needs to be.

---

## How It Works

### The Input
- A screenshot (PNG, JPG, or a URL to an app/website)
- Optional: the client's brand name and one-sentence description
- Optional: any specific colors you know you want

### The Output
- A complete `theme.css` file with CSS custom properties
- A `theme-config.json` with all token values for use in TypeScript/Tailwind
- Applied automatically to the skin template

### The Process
```
Screenshot uploaded
         ↓
Stage 1: Color Extraction
  Claude Vision analyzes screenshot
  Extracts: primary, secondary, accent, background, surface, text, border colors
  Identifies: font families, weights, sizes used
  Notes: border radius style (sharp/medium/rounded)
  Notes: shadow style (none/soft/dramatic)
  Notes: spacing density (compact/comfortable/spacious)
         ↓
Stage 2: Token Generation
  Maps extracted values to CSS custom property names
  Generates the full token set (see format below)
         ↓
Stage 3: Component Style Rules
  Generates style rules for: buttons, cards, inputs, nav, tables, badges
  Matches the visual style of the reference screenshot
         ↓
Stage 4: theme.css Output
  Complete stylesheet ready to drop into the skin template
         ↓
Stage 5: theme-config.json
  Same values as structured JSON for Tailwind/TypeScript use
```

---

## The 5-Stage Prompt System

### Stage 1 Prompt — Color + Typography Extraction
```
You are analyzing a UI screenshot to extract design tokens.

Look at this screenshot and identify:

COLORS:
- Primary color (main brand color, used for primary buttons, key UI elements)
- Secondary color (supporting brand color)
- Accent color (highlight, CTA, active states)
- Background color (main page background)
- Surface color (cards, panels, modals — slightly different from background)
- Text primary (main body text)
- Text secondary (labels, captions, subdued text)
- Border color (dividers, input borders)
- Success color (confirmations, pass states)
- Warning color (caution states)
- Error color (failures, validation errors)

TYPOGRAPHY:
- Primary font family (headings, brand name if visible)
- Body font family (paragraph text)
- Base font size (estimate in px)
- Heading weight (300/400/500/600/700/800)
- Body weight

SHAPE:
- Border radius style: sharp (0-2px) / medium (4-8px) / rounded (12px+) / pill (9999px)
- Shadow style: none / subtle / medium / dramatic
- Spacing: compact / comfortable / spacious

Return as JSON only. No explanation.
```

### Stage 2 Prompt — Token Mapping
```
Given these extracted design values:
{stage_1_output}

Map them to this CSS custom property naming system:
--color-primary, --color-primary-hover, --color-primary-text
--color-secondary, --color-secondary-hover
--color-accent, --color-accent-hover
--color-bg, --color-surface, --color-surface-elevated
--color-text, --color-text-muted, --color-text-disabled
--color-border, --color-border-strong
--color-success, --color-warning, --color-error
--font-heading, --font-body
--font-size-base, --font-size-sm, --font-size-lg, --font-size-xl, --font-size-2xl
--font-weight-heading, --font-weight-body
--radius-sm, --radius-md, --radius-lg, --radius-full
--shadow-sm, --shadow-md, --shadow-lg
--spacing-xs, --spacing-sm, --spacing-md, --spacing-lg, --spacing-xl

Return complete CSS :root { } block with all properties assigned.
```

### Stage 3 Prompt — Component Style Rules
```
Given these CSS tokens:
{stage_2_output}

Write CSS rules for these components that match the visual style in the reference screenshot:
- .btn-primary (the main action button)
- .btn-secondary
- .card (content card/panel)
- .input (text input field)
- .nav-item (navigation link)
- .badge (status badge/tag)
- .table-row
- .modal-overlay and .modal-content

Use only the CSS custom properties defined in the token set (var(--color-primary), etc.).
Do not hardcode any color values.
Return only the CSS rules. No explanation.
```

### Stage 4 Prompt — Final Assembly
```
Combine these into one complete theme.css file:

TOKENS:
{stage_2_output}

COMPONENT RULES:
{stage_3_output}

ALSO ADD:
- CSS reset (box-sizing, margin: 0)
- Body: font-family var(--font-body), background var(--color-bg), color var(--color-text)
- Smooth transitions: all interactive elements get transition: all 0.15s ease
- Focus ring: consistent focus-visible style using --color-accent

Output: complete, valid CSS file ready to use. Start with /* Theme generated by Skin Builder */ comment.
```

### Stage 5 — JSON Config (for Tailwind/TypeScript)
```
Convert this CSS :root block into a JSON theme config:
{stage_2_output}

Format:
{
  "colors": {
    "primary": "#value",
    "primaryHover": "#value",
    ...
  },
  "fonts": {
    "heading": "Font Name, fallback",
    "body": "Font Name, fallback"
  },
  "radii": {
    "sm": "2px",
    "md": "6px",
    ...
  }
}

This is used to extend the Tailwind config. Return JSON only.
```

---

## Implementation

### `copilot/skin_builder.py`
```python
import anthropic
import base64
from pathlib import Path

class SkinBuilder:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def build_from_screenshot(self, screenshot_path: str, brand_context: str = "") -> dict:
        """
        Full pipeline: screenshot → theme.css + theme-config.json
        """
        # Load image
        image_data = base64.b64encode(Path(screenshot_path).read_bytes()).decode()
        image_type = "image/png" if screenshot_path.endswith('.png') else "image/jpeg"

        # Stage 1: Extract design tokens
        stage1 = self._run_stage(STAGE_1_PROMPT, image_data, image_type)
        # Stage 2: Map to CSS properties
        stage2 = self._run_stage(STAGE_2_PROMPT.format(stage_1_output=stage1))
        # Stage 3: Component styles
        stage3 = self._run_stage(STAGE_3_PROMPT.format(stage_2_output=stage2))
        # Stage 4: Final CSS
        theme_css = self._run_stage(STAGE_4_PROMPT.format(
            stage_2_output=stage2, stage_3_output=stage3
        ))
        # Stage 5: JSON config
        theme_json = self._run_stage(STAGE_5_PROMPT.format(stage_2_output=stage2))

        return {
            "theme_css": theme_css,
            "theme_config": theme_json
        }

    def apply_to_skin(self, theme_css: str, skin_path: str):
        """Write theme.css to the skin's public folder."""
        theme_file = Path(skin_path) / "src" / "styles" / "theme.css"
        theme_file.write_text(theme_css)

    def _run_stage(self, prompt: str, image_data: str = None, image_type: str = None) -> str:
        messages = []
        if image_data:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": image_type, "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        else:
            messages = [{"role": "user", "content": prompt}]

        resp = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=messages
        )
        return resp.content[0].text
```

---

## How It Connects to the Skin Template

In `skin/src/main.tsx`:
```tsx
import './styles/theme.css'   // ← Skin Builder output drops here
import './styles/globals.css'  // ← Base styles that use the CSS variables
```

The skin's components use only CSS variables:
```css
/* Good — uses theme tokens */
.btn-primary {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-radius: var(--radius-md);
}

/* Bad — hardcoded color */
.btn-primary {
  background: #3B82F6;   /* NEVER do this */
}
```

This means dropping a new `theme.css` completely changes the entire look without touching any component code.

---

## Success Criteria

- [ ] Feed a screenshot of any app → get a complete `theme.css` back within 30 seconds
- [ ] `theme.css` contains all required CSS custom properties (full token set)
- [ ] Drop `theme.css` into the skin template → visual style changes to match the reference
- [ ] `theme-config.json` exports correctly and can extend Tailwind config
- [ ] No hardcoded color values in any skin component (all via CSS vars)
- [ ] Two completely different screenshots produce two completely different-looking skins
- [ ] Component styles (button, card, input, nav) visually match the reference screenshot style

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File
| File | Assertions |
|------|-----------|
| `copilot/skin_builder.py` | File exists; `SkinBuilder` class defined; `build_from_screenshot()`, `apply_to_skin()`, `_run_stage()` all present; no syntax errors |
| Stage prompt constants | All 5 stage prompts (`STAGE_1_PROMPT` through `STAGE_5_PROMPT`) defined as string constants; each contains the expected output format instructions |
| Generated `theme.css` | After a test run: file exists at `skin/src/styles/theme.css`; contains `:root {`; at minimum 10 CSS custom properties defined |
| Generated `theme-config.json` | After a test run: file exists; valid JSON; contains `colors`, `fonts`, `radii` keys |

### Seam Checks — Connection Points
**Seam 1: Stage 1 (extraction) → Stage 2 (token mapping)**
- Stage 1 output is valid JSON (parseable without error)
- Stage 2 receives Stage 1 JSON and produces a CSS `:root {}` block
- The `:root {}` block contains all required custom property names

**Seam 2: Stage 4 (final CSS) → skin template**
- `apply_to_skin(theme_css, skin_path)` writes file to `skin/src/styles/theme.css`
- `skin/src/main.tsx` imports `./styles/theme.css` (grep check)
- After `npm run build` in skin/, CSS variables resolve in the output

**Seam 3: theme.css → component rendering**
- No component files in `skin/src/` use hardcoded hex values (grep `-r "#[0-9a-fA-F]{3,6}" skin/src/components/`)
- CSS variables are defined in theme.css AND referenced in component styles — no orphaned variables

### Full Checkpoint (Phase 7 Gate)
**Pattern checks (git diff):**
```
Expected new file: copilot/skin_builder.py
Expected modified file: skin/src/styles/theme.css (after test run)
Expected new file: theme-config.json (output artifact, gitignore optional)
No modification to pieces/ or AP configuration.
```

**Functional checks:**
```bash
# Test with a real screenshot (use any screenshot you have)
python -c "
from copilot.skin_builder import SkinBuilder
builder = SkinBuilder()
result = builder.build_from_screenshot('test_screenshot.png')
assert result['theme_css'], 'No theme CSS generated'
assert ':root {' in result['theme_css'], 'Missing :root block'
import json
config = json.loads(result['theme_config'])
assert 'colors' in config, 'Missing colors in config'
assert 'primary' in config['colors'], 'Missing primary color'
builder.apply_to_skin(result['theme_css'], 'skin/')
print('✓ Skin Builder working')
"

# Confirm CSS variables resolve in skin build
cd skin && npm run build   # must exit 0
grep -c "var(--color" src/components/*.tsx && echo "✓ CSS vars used in components"
```

**Gate condition:** `build_from_screenshot()` produces valid theme.css with ≥10 CSS custom properties. `npm run build` passes after theme is applied. Zero hardcoded colors in component files. PASS or FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Generated colors are close but not exactly matching screenshot | Log, acceptable variance |
| MEDIUM | Stage N output fails to parse for Stage N+1 (JSON error between stages) | Fix that stage's output format instruction |
| HIGH | `npm run build` fails after theme.css applied (CSS syntax error) | Validate CSS before applying; fix stage 4 prompt |
| CRITICAL | Claude Vision stage (Stage 1) refuses to process image or returns empty | Stop — check image format and size; may need a different input method |

### Two-Strike Rule
Max 2 end-to-end runs per screenshot. If theme.css is still invalid after 2 attempts, stop for human review — likely a prompt format issue in one of the 5 stages.
