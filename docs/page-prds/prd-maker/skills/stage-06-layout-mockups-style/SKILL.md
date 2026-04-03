---
name: stage-06-layout-mockups-style
description: Define page layouts, wireframe patterns, component placement, and design tokens from classified mechanisms.
---

## Purpose

Transform classified mechanisms (with Wall/Door/Room blueprints from Stage 5) into visual structure: page layouts with component placement, navigation patterns, and a complete design token system. Three sequential sub-stages: 6a (arrangement selection), 6b (page mockups), 6c (style selection).

## When to Use

Activate when: `context_packet.stage_5.mechanism_blueprints` exists AND `context_packet.stage_4.mechanisms` exists (Stages 4-5 complete). Trigger phrases: "layout", "wireframe", "mockup", "style selection", "page arrangement", "design tokens", "component placement", "page layout".

Do NOT activate for: mechanism classification (Stage 5), phase sequencing (Stage 7), or any request about build ordering or verification protocols.

## Input Format

```json
{
  "stage_2": {
    "archetype_matches": [{ "archetype_id": "string", "confidence": 0.0 }]
  },
  "stage_3": {
    "concept_and_context": { "name": "string", "description": "string", "core_value_proposition": "string" },
    "target_user_and_market": { "primary_persona": {}, "pain_points": [], "goals": [] },
    "drift_anchor": "string"
  },
  "stage_4": {
    "mechanisms": [{ "id": "string", "name": "string", "description": "string", "category": "string" }],
    "mechanism_dependencies": [{ "from_id": "string", "to_id": "string", "relationship": "string" }]
  },
  "stage_5": {
    "mechanism_blueprints": [{
      "mechanism_id": "string",
      "steps": [{ "step": "string", "classification": "WALL|DOOR|ROOM" }]
    }]
  }
}
```

## Process

### Step 1: Classify App Type (Sub-6a)

Read `stage_2.archetype_matches[0].archetype_id` and `stage_3.concept_and_context`. Map to one of the 7 recognized app types using the deterministic lookup in `references/wireframe-pattern-lookup.md`:

`dashboard` | `chat` | `wizard` | `marketplace` | `tool` | `landing` | `settings`

If the archetype does not map cleanly, pick the CLOSEST match and note the deviation. This is never skipped.

### Step 2: Generate Arrangement Options (Sub-6a)

Using the app type, pull the standard wireframe pattern from the lookup table. Generate 2-3 arrangement options:

1. **Primary option**: The standard pattern for the app type (the 92% case)
2. **Secondary option**: A reasonable variation (e.g., top-nav instead of sidebar)
3. **Third option** (optional): Only if a hybrid pattern is genuinely viable

Each option has: `id`, `name` (e.g., "Sidebar + Top Nav + Content Grid"), `description` (what it looks like and why it fits).

Present to user. User MUST pick or adjust — this is a WALL. Record `selected_arrangement_id` and `user_adjustments`.

### Step 3: Identify UI-Facing Mechanisms (Sub-6b)

For each mechanism in `stage_4.mechanisms`, check its blueprint in `stage_5.mechanism_blueprints`:

- If the blueprint has steps classified as DOOR or ROOM → **user-facing** (needs a page or component)
- If ALL steps are WALL with zero user interaction → **backend-only** (no page needed, but still map to a page's "backend services" note)

### Step 4: Group Mechanisms into Pages (Sub-6b)

Apply standard grouping conventions from `references/component-placement-conventions.md`:

- Auth mechanisms → Login/Register page(s)
- Dashboard/overview mechanisms → Dashboard page
- CRUD mechanisms per entity → Entity list + detail pages
- Settings/preferences → Settings page
- Each major workflow → Its own page or modal

For each page, define: `page_name`, `route` (kebab-case, logical hierarchy), `layout_pattern` (from selected arrangement), `components` array, `user_approved`.

### Step 5: Place Components on Pages (Sub-6b)

For each page, identify every UI component needed. For each component specify:

- `component_name`: Descriptive (e.g., "TaskListTable", "CreateTaskModal")
- `placement`: Zone on the page — `"header"` | `"sidebar"` | `"main-content"` | `"footer"` | `"modal"` | `"drawer"`
- `mechanism_ids`: Array of mechanism IDs from Stage 4 this component serves
- Every `mechanism_id` must reference a real ID from `stage_4.mechanisms`

**Validation**: After all pages are defined, verify every mechanism from Stage 4 appears in at least one component's `mechanism_ids`. If any mechanism is "homeless," either add it to an existing page or create a new page.

Present each page to user for approval — this is a WALL. Set `user_approved: true` for each.

### Step 6: Curate Style Options (Sub-6c)

From the 12 predefined styles in `references/style-catalog.md`, select exactly 3 that best match:

1. **App type fit**: Dashboard → flat-design or dark-mode; Chat → minimalism or glassmorphism; etc.
2. **Target audience**: From `stage_3.target_user_and_market` — age range, professional vs casual, tech-savvy vs general
3. **Vibe match**: From `stage_3.concept_and_context.core_value_proposition` — premium, playful, technical, friendly

Present 3 options with: `id`, `name`, `vibe` (one-line description). Include a "Choose for me" default that selects the highest-scoring option. User picks one. Record `selected_style_id`.

### Step 7: Generate Design Tokens (Sub-6c)

For the selected style, populate the COMPLETE `design_tokens` object from `references/style-catalog.md`:

- `colors`: Primary, secondary, accent, surface, text, border, success, warning, error, info — all as hex values
- `typography`: Font families (heading, body, mono), size scale (xs through 4xl in rem), weights, line-heights
- `spacing`: Scale from 0.25rem to 6rem
- `border_radius`: sm, md, lg, xl, full
- `shadows`: sm, md, lg, xl

Generate `tailwind_config_overrides` — an object that can extend a Tailwind config with the selected style's tokens.

Calculate `audience_scores`: `audience_fit` (0-100), `vibe_match` (0-100), `age_range_fit` (0-100) based on persona alignment.

### Step 8: Validate and Score

Run all validation checks before writing output:

1. `app_type_classification` is set and recognized
2. `arrangement_options` has 2-3 entries, one selected
3. `pages` has ≥ 2 pages (auth + one functional)
4. Every page has `page_name`, `route`, `layout_pattern`, `components[]`, `user_approved`
5. Every mechanism from Stage 4 is on ≥ 1 page's component `mechanism_ids`
6. Every `mechanism_ids` entry references a real Stage 4 mechanism ID
7. `style_options_presented` has exactly 3 entries
8. `design_tokens` has `colors` and `typography` sub-objects with specific values
9. `selected_style_id` is from the predefined set or `"developers_choice"`
10. Run confidence scoring (see below)

## Output Format

```json
{
  "stage_6": {
    "sub_6a": {
      "app_type_classification": "string",
      "arrangement_options": [
        { "id": "string", "name": "string", "description": "string" }
      ],
      "selected_arrangement_id": "string",
      "user_adjustments": "string | null"
    },
    "sub_6b": {
      "pages": [
        {
          "page_name": "string",
          "route": "/kebab-case",
          "layout_pattern": "string",
          "components": [
            {
              "component_name": "string",
              "placement": "header|sidebar|main-content|footer|modal|drawer",
              "mechanism_ids": ["string"]
            }
          ],
          "user_approved": true
        }
      ]
    },
    "sub_6c": {
      "style_options_presented": [
        { "id": "string", "name": "string", "vibe": "string" }
      ],
      "selected_style_id": "string",
      "design_tokens": {
        "colors": { "primary": "#hex", "secondary": "#hex", "...": "..." },
        "typography": { "heading_font": "string", "body_font": "string", "sizes": {} },
        "spacing": { "1": "0.25rem", "...": "..." },
        "border_radius": { "sm": "string", "...": "..." },
        "shadows": { "sm": "string", "...": "..." }
      },
      "tailwind_config_overrides": {},
      "audience_scores": { "audience_fit": 0, "vibe_match": 0, "age_range_fit": 0 }
    }
  },
  "metadata": {
    "current_stage": 6,
    "confidence_scores": { "6": { "score": 0, "dimensions": {}, "gate_result": "pass|flag|fail" } },
    "stage_timestamps": { "6": "ISO-8601" }
  }
}
```

## Edge Cases

### Missing Input

- No `mechanism_blueprints` from Stage 5 → Trigger escape hatch. Cannot determine UI surfaces without blueprints.
- No `mechanisms` from Stage 4 → Trigger escape hatch. Nothing to lay out.
- No `archetype_matches` from Stage 2 → Fall back to analyzing `concept_and_context` description to classify app type. Log the fallback.

### Ambiguous Input

- Mechanism blueprint has only WALLs but mechanism name implies UI ("UserProfileEditor" with all-WALL steps) → Classify as user-facing with a flag. Ask user if available: "This mechanism appears backend-only but its name suggests UI. Should it have a page?"
- App is a hybrid (dashboard + chat) → Present the dominant pattern as primary, the secondary pattern as option 2, and a hybrid layout as option 3. Let user pick.

### Backend-Only Mechanisms

- Mechanisms with zero DOOR/ROOM steps are NOT placed on any page as components. Instead, note them in the nearest related page as "Backend service: [mechanism_name]" in a `backend_services` field. They still count as "mapped" for the all-mechanisms-mapped check.

### User Rejects All Style Options

- If user rejects all 3 curated styles AND the "Choose for me" default → Present 3 MORE from the remaining 9 styles. If still rejected → Trigger escape hatch with `reason: "style_rejection"` and `suggested_action: "custom_style_needed"`.

### Non-Standard App Type

- If the app doesn't fit any of the 7 standard types → Pick the closest match, present it with a note: "This is the closest standard pattern. What would you change?" The adjustment is a WALL.

### Scope Overflow

- If page creation implies mechanisms not in `stage_2.scope_contract` → Flag but do not create pages for out-of-scope mechanisms. Note the gap in metadata.

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): ≥2 pages? Every mechanism mapped? All 3 sub-stages populated? Design tokens complete (colors + typography + spacing)?
2. **Accuracy** (0-20): Wireframe pattern matches app type? Mechanisms on correct pages (auth→login, CRUD→entity pages)? Style matches target audience?
3. **Consistency** (0-20): No route conflicts? All component `mechanism_ids` reference real Stage 4 IDs? Style matches app type and archetype? All pages use selected arrangement consistently?
4. **Specificity** (0-20): Every component has exact placement + mechanism connection? Design tokens are specific values (hex, rem, px)? A developer could build any page from the spec alone?
5. **Handoff Readiness** (0-20): Could Stage 7 create file sandboxes and build orders? Every page/component detailed enough for token estimation? File paths inferable from page/component names?

**Total = sum of 5 dimensions (/100)**

- ≥ 90: PASS — proceed to Stage 7
- 70-89: WARN — flag low dimensions, proceed with warning
- < 70: FAIL — trigger escape hatch, do NOT pass output forward

## Escape Hatch

**When to trigger:**

- Required input fields missing (no blueprints, no mechanisms)
- App does not fit ANY wireframe pattern and user unavailable for guidance
- Mechanism cannot be mapped to any page (ambiguous UI surface, not backend-only)
- User rejects all 6 style options (3 curated + 3 alternates)
- Confidence score < 70 after one retry

**What to save:**

- Current `context_packet` with partial layout/style data
- Stage number (6) and active sub-stage (6a, 6b, or 6c)
- Pages already defined/approved vs remaining
- Unmapped mechanisms list
- What was attempted and what failed
- Suggested questions for the human

**How to signal:**

- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]`: `{ "stage": 6, "sub_stage": "6a|6b|6c", "reason": "string", "suggested_actions": ["string"] }`
- Save context packet snapshot
- Output structured NEEDS_HUMAN message

## Example

See `references/example-output.md` for a complete walkthrough: a task management app flowing through Sub-6a (dashboard type → sidebar arrangement), Sub-6b (5 pages with component placement), Sub-6c (flat-design style with full tokens).

**Quick summary of the flow:**

1. Archetype: "productivity-dashboard" → App type: `dashboard`
2. Lookup: dashboard → sidebar + top nav + content grid + cards
3. Options: (a) Sidebar+TopNav+Grid [selected], (b) TopNav-only+Grid, (c) Tabbed+Grid
4. Pages: Login, Dashboard, Task List, Task Detail, Settings — each with named components mapped to mechanism IDs
5. Style curation: flat-design (88), minimalism (82), dark-mode (79) → User picks flat-design
6. Tokens: `#3B82F6` primary, Inter/system-ui fonts, 4px spacing scale, etc.
