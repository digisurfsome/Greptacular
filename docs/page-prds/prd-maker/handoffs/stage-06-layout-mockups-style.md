# Build Stage 6 Skill: Layout + Mockups + Style

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-06-layout-mockups-style/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | Idea Capture | Capture the user's raw brain dump with zero filtering or structure | Raw text, preserved contradictions, word count |
| 2 | Gap Analysis | Match to archetype, identify missing mechanism categories (A-N), ask targeted questions | Complete mechanism map, archetype match, gap answers |
| 3 | Agent OS Structuring | Transform messy raw material into organized concept document | Product identity, problem statement, target users, feasibility |
| 4 | Mechanism Extraction | Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION | Mechanism list with dependencies and evaluation tags |
| 5 | 7-Question Scaffolding | Classify every process step as WALL / DOOR / ROOM using 7 questions | Per-mechanism W/D/R blueprint with verification methods |
| **6** | **Layout + Mockups + Style** | **Define page layouts, wireframe patterns, and design system** | **Per-page component specs, style tokens, typography** |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 6: Layout + Mockups + Style.** It reads from stages before it (primarily Stage 5 blueprints, Stage 4 mechanisms, Stage 3 concept, Stage 2 archetype) and writes to its own namespace (`stage_6`) in the context packet.

---

## Your Stage: Layout + Mockups + Style

### Purpose

Stage 6 takes the classified mechanisms from Stage 5 (with their Wall/Door/Room blueprints) and arranges them into visual structure: page layouts, navigation patterns, UI mockups, and style selection. This is where "what the machine does" (from Stage 5) becomes "what the user sees." Without Stage 5, wireframing is guessing. With Stage 5, wireframing is deterministic -- you are arranging known pieces whose behavior, connections, and constraints are already fully specified.

Stage 6 has three sub-stages that run in sequence: 6a (Arrangement Selection), 6b (Page Mockups), 6c (Style Selection).

### Inputs (What This Stage Receives)

From `context_packet.stage_5`:

- `mechanism_blueprints` (array): Wall/Door/Room blueprints for all mechanisms. Tells Stage 6 exactly what components exist, how many screens each mechanism requires, what UI elements are walls (fixed), doors (configurable within constraints), or rooms (dynamic content).

From `context_packet.stage_4`:

- `mechanisms` (array): Mechanism list with names, descriptions, categories, and dependencies
- `mechanism_dependencies` (array): Dependencies between mechanisms (from_id, to_id, relationship)

From `context_packet.stage_3`:

- `concept_and_context` (object): Product identity -- product name, one-line description, core value proposition
- `target_user_and_market` (object): Who the app is for -- personas, pain points, goals, market context
- `drift_anchor` (string): Canonical product description for scope creep detection

From `context_packet.stage_2`:

- `archetype_matches` (array): Matched app archetypes with confidence scores -- this drives the wireframe pattern lookup in Sub-6a

### Outputs (What This Stage Produces)

Written to `context_packet.stage_6`:

**Sub-6a: Arrangement Selection**

| Field | Type | Description |
|-------|------|-------------|
| `sub_6a` | `object` | Arrangement selection data |
| `sub_6a.app_type_classification` | `string` | App type for wireframe lookup (e.g., `"dashboard"`, `"chat"`, `"wizard"`, `"marketplace"`, `"tool"`, `"landing"`) |
| `sub_6a.arrangement_options` | `array` | 2-3 arrangement options presented to user |
| `sub_6a.arrangement_options[].id` | `string` | Option identifier |
| `sub_6a.arrangement_options[].name` | `string` | Pattern name (e.g., `"Sidebar + Top Nav + Content Grid"`) |
| `sub_6a.arrangement_options[].description` | `string` | What it looks like and why it fits |
| `sub_6a.selected_arrangement_id` | `string` | Which arrangement the user picked |
| `sub_6a.user_adjustments` | `string \| null` | Any adjustments the user requested, or null |

**Sub-6b: Page Mockups**

| Field | Type | Description |
|-------|------|-------------|
| `sub_6b` | `object` | Page mockup data |
| `sub_6b.pages` | `array` | Per-page mockup specifications |
| `sub_6b.pages[].page_name` | `string` | Page name (e.g., `"Dashboard"`, `"Settings"`, `"Task Detail"`) |
| `sub_6b.pages[].layout_pattern` | `string` | Layout pattern applied to this page |
| `sub_6b.pages[].components` | `array` | Components placed on this page |
| `sub_6b.pages[].components[].component_name` | `string` | Component name |
| `sub_6b.pages[].components[].placement` | `string` | Where on the page (`"header"`, `"sidebar"`, `"main-content"`, `"footer"`) |
| `sub_6b.pages[].components[].mechanism_ids` | `string[]` | Which mechanisms this component connects to |
| `sub_6b.pages[].user_approved` | `boolean` | Whether user approved this page layout |

**Sub-6c: Style Selection**

| Field | Type | Description |
|-------|------|-------------|
| `sub_6c` | `object` | Style selection data |
| `sub_6c.style_options_presented` | `array` | 3 curated style options shown to user |
| `sub_6c.style_options_presented[].id` | `string` | Style identifier from the 12 predefined set |
| `sub_6c.style_options_presented[].name` | `string` | Style name (e.g., `"Flat Design"`, `"Minimalism"`, `"Glassmorphism"`) |
| `sub_6c.style_options_presented[].vibe` | `string` | Short vibe description |
| `sub_6c.selected_style_id` | `string` | Which style the user picked (or `"developers_choice"`) |
| `sub_6c.design_tokens` | `object` | Complete design token set for the selected style |
| `sub_6c.design_tokens.colors` | `object` | Color palette (key-value: primary, secondary, surface, text, border, status colors) |
| `sub_6c.design_tokens.typography` | `object` | Font families, size hierarchy, weights, line-heights |
| `sub_6c.design_tokens.spacing` | `object` | Spacing scale |
| `sub_6c.design_tokens.border_radius` | `object` | Border radius tokens |
| `sub_6c.design_tokens.shadows` | `object` | Shadow tokens |
| `sub_6c.tailwind_config_overrides` | `object` | Tailwind configuration overrides for the selected style |
| `sub_6c.audience_scores` | `object` | Style fit scores: `audience_fit` (0-100), `vibe_match` (0-100), `age_range_fit` (0-100) |

### Process

#### Sub-6a: Arrangement Selection (Deterministic Lookup)

1. Read `archetype_matches` from Stage 2 to identify the primary app type
2. Apply the deterministic wireframe pattern lookup:

```
APP TYPE          -> WIREFRAME PATTERN (92% case)
dashboard         -> sidebar + top nav + main content grid + cards
chat              -> conversation list + message thread + input bar
wizard / form     -> step indicator + single form area + next/back
marketplace       -> search bar + filter sidebar + product grid
tool              -> toolbar + workspace + properties panel
landing page      -> hero + features + testimonials + CTA
settings          -> tab list + form sections
```

3. Generate 2-3 arrangement options based on the app type. The PRIMARY option is the standard pattern. Secondary options are reasonable variations (e.g., top nav instead of sidebar for a dashboard).
4. Present options to user. User picks or adjusts. This is a WALL -- cannot be skipped. The build cannot start until the arrangement is approved.
5. Record selected arrangement and any user adjustments.

**For the 8% that do not fit standard patterns:** Present the closest match and ask the user to adjust. The adjustment step is still a WALL.

#### Sub-6b: Page Mockups (Component Placement)

1. For each mechanism from Stage 4, determine if it is user-facing (needs a page/component) or backend-only (no page needed). Use the Stage 5 blueprints: if a mechanism has steps classified as DOOR or ROOM, it likely has a UI surface. If it is all WALLs with no user interaction steps, it may be backend-only.
2. Group mechanisms into pages. Standard groupings:
   - Auth mechanisms -> Login/Register page(s)
   - Dashboard/overview mechanisms -> Dashboard page
   - CRUD mechanisms for each entity -> Entity list + detail pages
   - Settings/preferences mechanisms -> Settings page
   - Each major workflow -> Its own page or modal
3. For each page:
   a. Name the page and assign a route
   b. Select the layout pattern from the chosen arrangement
   c. Place components: identify each UI component, assign it a placement zone (header, sidebar, main-content, footer), and connect it to the mechanism IDs it serves
   d. Verify every mechanism with a UI surface appears on at least one page
4. Present each page layout to user for approval. This is a WALL -- cannot be skipped.
5. Verify `all_mechanisms_mapped` is true -- every mechanism from Stage 4 appears on at least one page's mechanisms array. No mechanism is "homeless."

#### Sub-6c: Style Selection (Curated Options)

1. From the 12 predefined styles, select 3 that best match the app type and target audience (from Stage 3):

| ID | Name | Best For |
|----|------|----------|
| flat-design | Flat Design | Clarity, scalability, universal appeal |
| minimalism | Minimalism | Premium feel, Apple-style elegance |
| neumorphism | Neumorphism | Finance apps, dashboards, toggles |
| glassmorphism | Glassmorphism | Modern SaaS, trendy products |
| skeuomorphism | Skeuomorphism | Familiarity, older demographics |
| neubrutalism | Neubrutalism | Young/edgy, Gen Z products |
| bauhaus | Bauhaus | Design-forward, artistic |
| claymorphism | Claymorphism | Friendly, approachable products |
| retro-futurism | Retro Futurism | Gaming, entertainment |
| cyberpunk | Cyberpunk | Edgy tech, gaming |
| dark-mode | Dark Mode Elegant | Developer tools, media apps |
| warmer-shades | Warmer Shades | Nostalgic, comfortable feel |

2. Present exactly 3 curated options (NOT 12 -- decision paralysis). Include a "Choose for me" default option that selects the best match automatically.
3. User selects a style. Record `selected_style_id`.
4. Populate the complete `design_tokens` object for the selected style: colors (primary, secondary, surface, text, border, status), typography (font family, sizes, weights, line-heights), spacing scale, border radius, shadows.
5. Generate `tailwind_config_overrides` for the selected style.
6. Calculate `audience_scores` based on the target user personas from Stage 3.

### Rules and Constraints

1. **Wireframe pattern is deterministic** -- based on app type lookup, not AI creativity. The AI identifies the app type; the wireframe pattern follows from the lookup table. The 92% case is handled by the table. The 8% edge case still uses the closest match + user adjustment.
2. **User MUST approve layout before build starts** -- this is a WALL. Cannot be skipped. Cannot be auto-approved in normal flow. If running in automated mode without human input, the layouts must match the deterministic pattern for the app type and `user_approved` is set to `true` with a note.
3. **Style is applied AFTER layout, not before** -- "You don't pick colors before you know how many pages you have." Sub-6c always runs after Sub-6b.
4. **Do NOT give 12 style choices** -- give exactly 3 curated options to prevent decision paralysis. Plus a "Choose for me" default.
5. **Style upgrade happens AFTER app is built** -- never put an upgrade option between the user and completion. The full 12-style catalog is a premium feature for later.
6. **Every mechanism must appear on at least one page** -- `all_mechanisms_mapped` must be `true`. No mechanism is homeless.
7. **Components must reference real mechanism IDs** from Stage 4 -- no invented mechanism references.
8. **Navigation pattern must match the app type** -- a chat app does not get a sidebar-heavy dashboard layout unless the user explicitly requests it.
9. **Pages must have routes** that follow conventions (kebab-case, logical hierarchy).
10. **Scope check:** Before adding pages, verify all mechanisms are within the `scope_contract` from Stage 2. If a mechanism seems to imply pages not in scope, flag it.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-06-extraction.md`** -- The full extraction dossier for Stage 6. This is your primary source of truth for what the stage does. Contains the sub-stage breakdown, the wireframe pattern lookup table, style set system details, and the rules about deterministic layout selection.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 6's namespace (section 2.8). Understand exactly which fields you read from Stage 5 (section 2.7), Stage 4 (section 2.6), Stage 3 (section 2.5), and Stage 2 (section 2.4), and which fields you write.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 6's contract. Your skill must produce output that meets all 6 "Done When" criteria and passes the confidence scoring. Pay special attention to Accuracy (wireframe pattern matches app type, mechanisms on correct pages) and Specificity (components have exact placement, mechanism connection, and interaction description).

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. While Stage 5 uses this as its primary lens, Stage 6 should be aware of UI-related structural rules (component per file, mobile-first, focus states, loading states, etc.) that affect component specification.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/skills/design-system.md`** -- The design system skill. Study its approach to design token generation (colors, typography, spacing, border-radius, shadows, breakpoints), visual audit dimensions, and "AI slop detection." Your style selection process should produce tokens at this quality level.

7. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/skills/frontend-patterns.md`** -- Frontend development patterns for React, Next.js, state management, and UI best practices. Study the component composition patterns, compound component patterns, and state management approaches. Your page/component specifications should align with these patterns.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. A perfect Stage 6 output has:
- Sub-6a: A confirmed app type, 2-3 arrangement options with one selected, clear justification for the pattern match
- Sub-6b: Every page named with a route, every component placed with mechanism connections, every mechanism mapped to at least one page, user approval recorded for each page
- Sub-6c: 3 curated style options (not 12), one selected, complete design tokens (colors, typography, spacing, border-radius, shadows), Tailwind overrides, audience scores

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns: The 3 sub-stages always run in order (arrangement -> pages -> style). Pages follow from the arrangement. Style follows from the pages. This ordering is a WALL.
- Decision patterns: App type -> wireframe pattern is a deterministic lookup. Style curation uses audience/persona matching. Component placement follows UX conventions for the app type.
- Quality signals: Every mechanism mapped to a page (no homeless mechanisms). Routes that follow conventions. Design tokens that are complete (not partial). Tailwind overrides that actually work.
- Edge cases: App that does not fit standard patterns. Mechanisms that are backend-only (no page). User who wants a non-standard arrangement. "Choose for me" default behavior.

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases like "layout", "wireframe", "mockup", "style selection", "page arrangement", "design tokens"? Is it specific enough to avoid false matches with Stage 5 (scaffolding) or Stage 7 (phase sequencing)? Does it specify that the skill PRODUCES page layouts, component specs, and design tokens?

2. **Output Format Completeness** -- Is the output format completely specified with exact fields matching the context packet schema (section 2.8)? Could Stage 7 parse this output programmatically to create file sandbox lists and build orders?

3. **Explicit Edge Case Handling** -- What happens when the app does not fit standard wireframe patterns? When a mechanism has no UI surface? When the user rejects all 3 style options? When Stage 5 blueprints are ambiguous about which mechanisms are user-facing?

4. **Composability** -- Could Stage 7 consume this output cleanly to split the build into phases? Does the output contain ONLY the structured layout/style data (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-06-layout-mockups-style
description: {{SINGLE LINE DESCRIPTION -- this is a YAML field, multi-line SILENTLY FAILS}}
---

## Purpose

{{1-2 sentences}}

## When to Use

{{Trigger conditions -- what input or request activates this skill}}

## Input Format

{{Exact JSON structure this skill expects from the context packet}}

## Process

### Step 1: {{Name}}
{{Detailed instructions with decision criteria}}

### Step 2: {{Name}}
{{...}}

[... as many steps as needed ...]

## Output Format

{{Exact JSON structure this skill writes to the context packet -- field names, types, validation rules}}

## Edge Cases

### Missing Input
{{What to do when required fields are empty or missing}}

### Ambiguous Input
{{What to do when input can be interpreted multiple ways}}

### Scope Overflow
{{What to do when the stage discovers work that belongs to a different stage}}

## Confidence Scoring

{{The 5 scoring dimensions from the stage contract, with self-scoring instructions}}

## Escape Hatch

{{When to trigger, what to save, how to signal NEEDS_HUMAN}}

## Example

{{One realistic example showing input (mechanisms + blueprints) -> sub-6a (app type + arrangement) -> sub-6b (pages with components) -> sub-6c (style with tokens)}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/wireframe-pattern-lookup.md` -- The full app-type-to-wireframe-pattern lookup table with all variations
   - `references/style-catalog.md` -- The 12 predefined styles with complete token sets, audience fit data, and curation rules
   - `references/component-placement-conventions.md` -- Standard component placement conventions per app type (where nav goes, where CTA goes, where forms go)
   - `references/example-output.md` -- Extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
blueprints = context_packet["stage_5"]["mechanism_blueprints"]
mechanisms = context_packet["stage_4"]["mechanisms"]
mechanism_dependencies = context_packet["stage_4"]["mechanism_dependencies"]
concept = context_packet["stage_3"]["concept_and_context"]
target_user = context_packet["stage_3"]["target_user_and_market"]
drift_anchor = context_packet["stage_3"]["drift_anchor"]
archetype_matches = context_packet["stage_2"]["archetype_matches"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_6"] = {
    "sub_6a": {
        "app_type_classification": "dashboard",
        "arrangement_options": [...],
        "selected_arrangement_id": "opt_1",
        "user_adjustments": null
    },
    "sub_6b": {
        "pages": [...]
    },
    "sub_6c": {
        "style_options_presented": [...],
        "selected_style_id": "flat-design",
        "design_tokens": { "colors": {...}, "typography": {...}, ... },
        "tailwind_config_overrides": {...},
        "audience_scores": { "audience_fit": 85, "vibe_match": 90, "age_range_fit": 80 }
    }
}
context_packet["metadata"]["current_stage"] = 6
context_packet["metadata"]["confidence_scores"]["6"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    },
    "gate_result": "pass"  # or "flag" or "fail"
}
context_packet["metadata"]["stage_timestamps"]["6"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify `app_type_classification` is set and matches a recognized type
2. Verify `arrangement_options` has 2-3 options and one is selected
3. Verify `pages` has at least 2 pages (auth + one functional page)
4. Verify every page has a `page_name`, `layout_pattern`, `components` array, and `user_approved`
5. Verify every mechanism from Stage 4 appears on at least one page (`all_mechanisms_mapped`)
6. Verify every component's `mechanism_ids` reference real mechanism IDs from Stage 4
7. Verify `style_options_presented` has exactly 3 entries
8. Verify `design_tokens` has all required sub-objects (colors, typography at minimum)
9. Verify `selected_style_id` is from the predefined set or `"developers_choice"`
10. Run the confidence scoring
11. If score < 70, trigger escape hatch instead of writing
12. If score 70-89, write but flag in metadata
13. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~30,000-50,000 tokens (by Stage 6, Stages 0-5 data is substantial)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

The style catalog (12 styles with complete tokens) is large. Store it in `references/style-catalog.md` rather than in the SKILL.md body. The SKILL.md should reference it and describe the curation algorithm (how to pick 3 from 12).

---

## Escape Hatch Pattern

Include this in your SKILL.md:

```
When to trigger:
- Required input fields are missing (no blueprints from Stage 5, no mechanisms from Stage 4)
- The app does not fit ANY standard wireframe pattern and the user is not available to
  provide guidance on a custom arrangement
- A mechanism cannot be mapped to any page (no UI surface identifiable, but the mechanism
  is not backend-only -- ambiguous)
- The user rejects all 3 style options AND the default, requiring a custom style that
  cannot be generated from the predefined set
- Confidence score is below 70 after one retry

What to save:
- Current context_packet with whatever partial layout/style data exists
- Stage number (6) and which sub-stage was active (6a, 6b, or 6c)
- List of pages already defined and approved vs remaining
- List of unmapped mechanisms (if any)
- What was attempted and what failed
- Suggested questions for the human (e.g., "Your app combines dashboard and chat patterns.
  Which should be the primary layout? Options: A) Sidebar dashboard with embedded chat panel,
  B) Chat-first with dashboard widgets in sidebar, C) Separate pages for each.")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array with stage=6, sub_stage, reason
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Does page_list have at least 2 pages? Is every mechanism mapped to
   at least one page? Are all 3 sub-stages populated (arrangement, pages, style)?
   Does the style have complete design tokens (colors, typography, spacing)?
2. Accuracy: Does the wireframe pattern match the app type? Are mechanisms on the
   correct pages (auth on login page, CRUD on entity pages)? Does the style
   match the target audience? Are component placements following standard UX conventions?
3. Consistency: Do page routes conflict? Do component mechanism_ids reference real
   mechanism IDs from Stage 4? Does the style match the app type and archetype?
   Do all pages use the selected arrangement pattern consistently?
4. Specificity: Does every component have exact placement, exact mechanism connection,
   and exact interaction description? Are design tokens specific values (not "a nice
   blue" but "#3B82F6")? Could a developer build any page from the specification alone?
5. Handoff Readiness: Could Stage 7 create file sandbox lists and build orders from
   this output? Is every page/component detailed enough to estimate token cost?
   Are file paths inferable from the page/component names?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 7
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-06-layout-mockups-style/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-06-layout-mockups-style/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases ("layout", "wireframe", "mockup", "style", "page arrangement", "design tokens", "component placement") and specifies what the skill produces (page layouts with component specs and complete design token set)
- [ ] **Output completeness:** Every output field has a name, type, and description matching context-packet-schema.md section 2.8. Stage 7 could parse the output programmatically to create file sandbox lists.
- [ ] **Edge cases explicit:** Non-standard app types, backend-only mechanisms, user rejection of all style options, ambiguous UI surface, hybrid app types -- all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured layout/style data. No conversational text, no preamble. Stage 7 can consume the output as-is to split into build phases.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions (completeness, accuracy, consistency, specificity, handoff readiness)
- [ ] **Escape hatch included:** Trigger conditions (missing input, non-standard patterns, unmappable mechanisms, style rejection, low confidence), save protocol, and NEEDS_HUMAN signal method are documented
- [ ] **Example included:** At least one realistic example showing mechanisms flowing through Sub-6a (app type lookup, arrangement selection), Sub-6b (page creation with component placement), and Sub-6c (style curation and token generation)
- [ ] **Context packet fields match schema:** Every field read (stage_5.mechanism_blueprints, stage_4.mechanisms, stage_3.concept_and_context, stage_2.archetype_matches, etc.) and written (stage_6.sub_6a, stage_6.sub_6b, stage_6.sub_6c) matches context-packet-schema.md
- [ ] **Wireframe lookup table encoded:** The app-type-to-wireframe-pattern mapping is encoded as a deterministic lookup (in SKILL.md or references), not left to AI judgment
- [ ] **Style catalog referenced:** The 12 predefined styles with their token sets are accessible (in references/), with the curation algorithm (3 from 12) clearly documented
- [ ] **Three sub-stages documented:** Sub-6a, Sub-6b, Sub-6c are each described as distinct sequential steps with their own inputs, process, and outputs

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-06-layout-mockups-style/SKILL.md`
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.8 for writes, sections 2.4-2.7 for reads)
- [ ] Stage 6 contract criteria from stage-contracts.md are achievable by following the skill's process (all 6 "Done When" criteria)
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] The wireframe pattern lookup is deterministic (app type in, pattern out), not AI-driven
- [ ] Style curation is 3 options from 12 (not all 12), with a "Choose for me" default
- [ ] Sub-6a, Sub-6b, Sub-6c are clearly sequenced: arrangement first, then pages, then style
- [ ] Every mechanism from Stage 4 is traceable to at least one page in the output
- [ ] Design tokens are complete and specific (hex values, px values, font names -- not vague descriptions)
