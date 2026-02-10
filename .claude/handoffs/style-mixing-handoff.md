# Handoff: Style Mixing & Accessibility Modifiers

## Context

AutoForge lets users pick a UI design style during project creation (Step 4 of the New Project modal). There are 12 styles in `server/services/style_registry.py` (flat-design, minimalism, neumorphism, glassmorphism, skeuomorphism, neubrutalism, bauhaus, claymorphism, retro-futurism, cyberpunk, dark-mode, warm-tones). The selected style's design tokens, Tailwind config, and do's/don'ts get injected into the coding agent's prompt via `_get_style_context()` in `prompts.py`, ensuring the AI builds the entire app with consistent styling.

**The problem:** A single style choice doesn't always serve all audience needs. Example: A sugar/glycemic-index scanning app for diabetics and keto users ranges from 20-somethings doing keto to elderly diabetics with vision/cognitive issues. The AI recommendation engine might suggest **Flat Design** for its clarity and trust — but a 70-year-old diabetic with declining vision needs bigger touch targets and higher-contrast buttons than stock Flat Design provides.

**The solution:** Allow users to select a **base style** plus optional **modifiers** (overlays) that adjust specific components without replacing the entire style. Think of it like CSS specificity — the base style provides the foundation, and modifiers surgically override specific tokens.

---

## What Already Exists

### Style Selection Flow (Complete)
- **UI:** `ui/src/components/NewProjectModal.tsx` — Step 4 has a working style picker with AI recommendations
- **API:** `server/routers/projects.py` — `GET /api/styles` and `GET /api/styles/recommend`
- **Registry:** `server/services/style_registry.py` — All 12 styles with complete Tailwind configs, design tokens, css_preview data, audience matching, do's/don'ts
- **Storage:** `server/services/boilerplate_manager.py` → `save_project_config()` stores `"style": style_id` in `.autoforge/project_config.json`
- **Prompt Injection:** `prompts.py` → `_get_style_context()` reads the style from config and calls `get_style_prompt_context()` to generate ~3500 chars of agent instructions
- **Hooks:** `ui/src/hooks/useProjects.ts` — `useStyles()`, `useStyleRecommendations()`
- **Types:** `ui/src/lib/types.ts` — `StyleOption`, `StyleCategory`, `StyleRecommendation`

### The Recommendation Engine
`recommend_style(audience, vibe, age_group)` in `style_registry.py` scores styles using three scoring matrices (`_AUDIENCE_SCORES`, `_VIBE_SCORES`, `_AGE_GROUP_SCORES`). Returns sorted list of `{style_id, style_name, score, reason}`.

---

## What Needs to Be Built

### 1. Modifier System Architecture

**Concept:** Modifiers are partial style overlays that surgically override specific design tokens from the base style. They should NOT be full styles — they're narrow, targeted adjustments.

**Initial modifier set (start with these 3-4):**

| Modifier ID | Name | What It Changes |
|---|---|---|
| `high-contrast-buttons` | High-Contrast Buttons | Button colors, button text weight, focus ring width, min button height |
| `large-touch-targets` | Large Touch Targets | Min button height (48px+), input height, tap areas, spacing around interactives |
| `high-contrast-text` | High-Contrast Text | Text colors adjusted for WCAG AAA (7:1), increased font weight for body |
| `larger-type` | Larger Typography | Base font size 18px+, heading scale, line-height increase |

**Data structure for a modifier:**
```python
{
    "id": "high-contrast-buttons",
    "name": "High-Contrast Buttons",
    "description": "Increases button contrast and size for better visibility and tap accuracy",
    "accessibility_tag": "vision",  # categories: vision, motor, cognitive
    "token_overrides": {
        # These MERGE over the base style's design_tokens.component_patterns
        "component_patterns": {
            "button_style": "HIGH CONTRAST: solid fill using brand.primary with white text, "
                           "minimum 4.5:1 contrast ratio, font-weight 700, "
                           "min-height 48px, clear focus ring (3px solid, offset 2px)",
            "button_radius": None,  # None = inherit from base style (don't override)
        },
        # These MERGE over the base style's tailwind_config
        "tailwind_overrides": {
            "minHeight": {"btn": "3rem"},  # 48px
        },
    },
    "prompt_additions": [
        "ALL buttons must have a minimum contrast ratio of 4.5:1 (WCAG AA) against their background",
        "Primary action buttons must be at least 48px tall with 16px horizontal padding",
        "Focus indicators must be visible: 3px solid ring with 2px offset, using brand.primary color",
        "Never use color alone to indicate button state — combine with border/shadow/text changes",
    ],
    "compatible_with": ["*"],  # All styles, or specific IDs
    "conflicts_with": [],  # Modifiers that can't be used together
}
```

### 2. Storage

Currently `project_config.json` stores:
```json
{"boilerplate": "react-vite-tailwind", "style": "flat-design"}
```

Add modifiers:
```json
{
    "boilerplate": "react-vite-tailwind",
    "style": "flat-design",
    "style_modifiers": ["high-contrast-buttons", "large-touch-targets"]
}
```

**Files to modify:**
- `server/services/boilerplate_manager.py` → `save_project_config()` — add `style_modifiers` field
- `server/schemas.py` → `ProjectCreate` schema — add optional `style_modifiers: list[str]`

### 3. Prompt Injection (The Critical Part)

The modifier's prompt additions get appended AFTER the base style's prompt context. This is the key integration point.

**Modify:** `prompts.py` → `_get_style_context()`

Current flow:
1. Read `style_id` from `project_config.json`
2. Call `get_style_prompt_context(style_id)` → returns base style markdown
3. Inject into prompt

New flow:
1. Read `style_id` AND `style_modifiers` from `project_config.json`
2. Call `get_style_prompt_context(style_id)` → base style markdown
3. For each modifier, call `get_modifier_prompt_context(modifier_id)` → modifier markdown
4. Concatenate: base style + "\n\n" + modifier sections
5. Inject combined result into prompt

**Example combined output (Flat Design + High-Contrast Buttons):**

```markdown
## Design System: Flat Design
[... existing 3500 chars of Flat Design context ...]

## Accessibility Modifier: High-Contrast Buttons

**IMPORTANT: The following rules OVERRIDE the base style's button guidelines above.**

### Button Override Rules
- ALL buttons must have a minimum contrast ratio of 4.5:1 (WCAG AA) against their background
- Primary action buttons must be at least 48px tall with 16px horizontal padding
- Focus indicators must be visible: 3px solid ring with 2px offset
- Never use color alone to indicate button state

### Override Tokens
When the base style says to use specific button colors, verify they meet 4.5:1 contrast.
If they don't, darken the fill or lighten the text until they do. For Flat Design specifically:
- Primary button: keep #2196F3 fill but use #FFFFFF text (contrast 3.2:1 — NOT enough)
  → OVERRIDE: darken to #1565C0 fill with #FFFFFF text (contrast 5.5:1 — passes AA)
- Secondary button: keep #FF9800 fill → use #000000 text (not #FFFFFF)
```

### 4. Making Modifiers Style-Aware (The "Don't Go Off The Rails" Part)

This is the hardest part. A modifier must know how it interacts with each base style. Naively saying "make buttons high contrast" doesn't work because:

- **Flat Design** buttons are solid fills — you darken the fill color
- **Glassmorphism** buttons are translucent — you can't just darken a translucent fill; you need to increase opacity AND darken
- **Cyberpunk** buttons have neon glow borders — high contrast means brighter glow + ensuring text glow doesn't wash out readability
- **Neubrutalism** buttons already have thick borders — high contrast means bolder fills inside the border frame

**Approach: Per-style adjustment hints**

Each modifier should include an optional `style_hints` dict mapping base style IDs to specific override instructions:

```python
"style_hints": {
    "flat-design": "Darken brand.primary by 20% for button fills. Use pure white text.",
    "glassmorphism": "Increase button background opacity to 0.85 minimum. Add 1px solid border matching brand.primary.",
    "cyberpunk": "Increase neon glow intensity by 50%. Use solid fill instead of transparent for primary buttons.",
    "neubrutalism": "Keep the thick border but ensure fill color has 4.5:1 contrast with text. Increase shadow offset for pressed state.",
    "dark-mode": "Use brand.primary at full saturation for button fills (not desaturated). Ensure text is pure white.",
    # Styles not listed: use generic instructions from prompt_additions
}
```

When generating modifier prompt context, check if the base style has a hint and include it:

```python
def get_modifier_prompt_context(modifier_id: str, base_style_id: str) -> str:
    modifier = get_modifier(modifier_id)
    context = f"## Accessibility Modifier: {modifier['name']}\n\n"
    context += "**These rules OVERRIDE the base style's guidelines where they conflict.**\n\n"

    # Add generic rules
    for rule in modifier["prompt_additions"]:
        context += f"- {rule}\n"

    # Add style-specific hint if available
    hint = modifier.get("style_hints", {}).get(base_style_id)
    if hint:
        context += f"\n### Style-Specific Adjustments for {base_style_id}\n"
        context += f"{hint}\n"

    return context
```

### 5. UI Changes

**In `NewProjectModal.tsx` Step 4**, after the user selects a base style, show a collapsible "Accessibility & Modifiers" section below the style grid:

```
[Selected: Flat Design ✓]

▼ Accessibility Modifiers (optional)
  ☐ High-Contrast Buttons — Better visibility for all users
  ☐ Large Touch Targets — Bigger buttons and inputs (48px+)
  ☐ High-Contrast Text — WCAG AAA text contrast (7:1)
  ☐ Larger Typography — 18px+ base font size

  💡 Recommended for your audience: High-Contrast Buttons, Large Touch Targets
```

The recommendation engine should suggest modifiers based on the same audience/age_group signals:
- `50-plus` age group → auto-suggest `high-contrast-buttons` + `large-touch-targets`
- `health-conscious` audience → suggest `high-contrast-text` (medical context = precision matters)

**Files to modify:**
- `ui/src/components/NewProjectModal.tsx` — add modifier checkboxes after style selection
- `ui/src/lib/types.ts` — add `StyleModifier` type
- `ui/src/lib/api.ts` — update `createProject()` to pass `style_modifiers`
- `ui/src/hooks/useProjects.ts` — add `useStyleModifiers()` hook if modifiers have their own endpoint, or include them in the styles response

### 6. API Changes

**Option A (simpler):** Include modifiers in the existing `/api/styles` response:
```json
{
  "categories": [...existing...],
  "modifiers": [
    {"id": "high-contrast-buttons", "name": "...", "description": "...", "accessibility_tag": "vision"},
    ...
  ]
}
```

**Option B (separate endpoint):** `GET /api/styles/modifiers` — returns available modifiers. Cleaner separation but more plumbing.

Recommend **Option A** since there are only 3-4 modifiers and they're tightly coupled to styles.

**Add modifier recommendation to `/api/styles/recommend`:** The response should also include suggested modifiers based on audience/age:
```json
[
  {"style_id": "flat-design", "score": 12, "reason": "...", "suggested_modifiers": ["high-contrast-buttons", "large-touch-targets"]}
]
```

---

## Guard Rails: How to Prevent Style Mixing From Going Off The Rails

### 1. Modifiers Are NOT Styles
A modifier should NEVER contain a full color palette, font stack, or complete component pattern. It only overrides specific tokens. If you find yourself writing more than ~200 words of prompt additions for a single modifier, you're building a style, not a modifier.

### 2. Explicit Override Hierarchy
The prompt must make the hierarchy crystal clear to the AI agent:
```
Base Style tokens → Modifier overrides → WCAG minimums (non-negotiable)
```
If a modifier conflicts with WCAG minimums, WCAG wins. Always.

### 3. Limit Modifier Count
Maximum 3 active modifiers per project. More than that creates contradictory instructions that confuse the agent. Enforce this in the API schema validation.

### 4. Conflict Detection
Some modifiers may conflict:
- `larger-type` + a hypothetical `compact-layout` modifier = contradiction
- Define `conflicts_with` on each modifier and validate at creation time

### 5. Test the Combined Prompt
After implementing, test the combined prompt output manually:
```python
from server.services.style_registry import get_style_prompt_context
from server.services.style_modifiers import get_modifier_prompt_context

base = get_style_prompt_context("flat-design")
mod1 = get_modifier_prompt_context("high-contrast-buttons", "flat-design")
mod2 = get_modifier_prompt_context("large-touch-targets", "flat-design")

combined = base + "\n\n" + mod1 + "\n\n" + mod2
print(f"Total prompt size: {len(combined)} chars")
# Should be < 6000 chars total. If more, the agent context is getting bloated.
```

### 6. Prompt Budget
The base style context is ~3500 chars. Each modifier should add no more than ~500 chars. With 3 modifiers = ~5000 chars total. This is within reason for prompt injection but watch it. If it bloats past 6000 chars, the agent starts losing focus on the actual coding task.

---

## Concrete Use Case: Sugar/Glycemic Index App

**App:** Users scan barcodes to check glycemic index of foods. Target audience: keto dieters (20s-30s) through elderly diabetics (60s-80s).

**Recommended configuration:**
- **Base Style:** Flat Design (trust, clarity, universal accessibility)
- **Modifiers:** `high-contrast-buttons` + `large-touch-targets`

**What the agent would see in its prompt:**
1. Full Flat Design system (solid colors, clean icons, no shadows, Inter font)
2. Override: buttons must be 48px+ tall, 4.5:1 contrast minimum, darkened #1565C0 primary fills
3. Override: all tap targets 48px minimum, inputs full height, generous spacing around interactive elements

**What this produces:**
- Clean, trustworthy medical-feeling app (Flat Design base)
- Scannable buttons that a 75-year-old with declining vision can hit reliably
- Large enough touch targets that shaky hands don't miss
- All without abandoning the base style's clean aesthetic

---

## Implementation Order

1. **Define modifier data structures** in a new file `server/services/style_modifiers.py`
2. **Write the 4 initial modifiers** with generic prompt_additions + style_hints for the top 3-4 base styles (flat-design, warm-tones, minimalism, dark-mode — the ones most likely paired with accessibility modifiers)
3. **Update `_get_style_context()`** in `prompts.py` to also read and inject modifiers
4. **Update storage** — `boilerplate_manager.py` `save_project_config()` + `project_config.json` schema
5. **Update API** — modify `/api/styles` response to include modifiers, update `/api/styles/recommend` to suggest modifiers
6. **Update UI** — add modifier checkboxes to NewProjectModal.tsx Step 4
7. **Update types/hooks/api** — TypeScript types, API client, React Query hooks
8. **Test the combined prompt** — verify it's < 6000 chars and makes sense end-to-end
9. **Build the app** — `cd ui && npm run build` to verify TypeScript compiles clean

---

## Key Files Reference

| File | Role |
|---|---|
| `server/services/style_registry.py` | Base style definitions (DO NOT MODIFY — add modifiers separately) |
| `server/services/style_modifiers.py` | **NEW** — Modifier definitions and prompt context generation |
| `prompts.py` | Prompt injection — modify `_get_style_context()` to include modifiers |
| `server/services/boilerplate_manager.py` | Storage — `save_project_config()` needs `style_modifiers` field |
| `server/routers/projects.py` | API endpoints — modify styles endpoint to include modifiers |
| `server/routers/__init__.py` | Router registration (may not need changes if modifiers are in styles router) |
| `ui/src/components/NewProjectModal.tsx` | UI — add modifier checkboxes after style selection |
| `ui/src/lib/types.ts` | TypeScript types — add `StyleModifier` interface |
| `ui/src/lib/api.ts` | API client — update `createProject()` call signature |
| `ui/src/hooks/useProjects.ts` | React Query hooks — may need modifier hook |
| `server/schemas.py` | Pydantic schemas — add `style_modifiers` to `ProjectCreate` |
