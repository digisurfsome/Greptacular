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

Present to user. User MUST pick or adjust — this is a WALL. Record `selected_arrangement_id` and `user_adjustments`. Set `navigation_pattern` to the pattern of the selected arrangement: `"sidebar"` | `"top_nav"` | `"tabbed"` | `"custom"`.

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

For each page, also populate a `connections` array that maps each interactive component to the mechanism it triggers and what action it performs. Each entry has: `component_name`, `triggers_mechanism` (mechanism ID), and `action` (human-readable description of what happens, e.g., "opens create form", "submits auth request"). This tells Stage 7 exactly what each component DOES, not just what mechanism it belongs to.

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
2. `navigation_pattern` is set to one of `"sidebar"` | `"top_nav"` | `"tabbed"` | `"custom"`
3. `arrangement_options` has 2-3 entries, one selected
4. `pages` has ≥ 2 pages (auth + one functional)
5. Every page has `page_name`, `route`, `layout_pattern`, `components[]`, `connections[]`, `user_approved`
6. Every page's `connections` array has at least one entry for each interactive component, and every `triggers_mechanism` references a real Stage 4 mechanism ID
7. Every mechanism from Stage 4 is on ≥ 1 page's component `mechanism_ids` OR in a page's `backend_services` array (backend-only mechanisms)
8. Every `mechanism_ids` and `backend_services` entry references a real Stage 4 mechanism ID
9. `all_mechanisms_mapped` is `true` and `pages_approved` is `true`
10. `style_options_presented` has exactly 3 entries
11. `design_tokens` has `colors` and `typography` sub-objects with specific values
12. `selected_style_id` is from the predefined set or `"developers_choice"`
13. Run confidence scoring (see below)

## Output Format

```json
{
  "stage_6": {
    "sub_6a": {
      "app_type_classification": "string",
      "navigation_pattern": "sidebar|top_nav|tabbed|custom",
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
          "connections": [
            {
              "component_name": "string",
              "triggers_mechanism": "string (mechanism ID)",
              "action": "string (what the component triggers — e.g., 'opens create form', 'submits auth request', 'fetches dashboard data')"
            }
          ],
          "backend_services": ["string (mechanism IDs for backend-only mechanisms served by this page)"],
          "user_approved": true
        }
      ],
      "all_mechanisms_mapped": true,
      "pages_approved": true
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


---
## REFERENCE: component-placement-conventions

# Component Placement Conventions

> Standard UI component placement patterns per app type. Used by Sub-6b to place components on pages.

## Universal Placement Rules

These apply to ALL app types:

1. **Navigation** goes at the top (horizontal) or left side (vertical sidebar). Never bottom, never right.
2. **Primary action buttons** (CTA) go top-right of the content area or bottom-right of forms.
3. **Search** goes at the top, either in the nav bar or immediately below it.
4. **User menu / avatar** goes top-right corner, always.
5. **Notifications** go top-right, near the user menu (bell icon pattern).
6. **Breadcrumbs** go immediately below the top nav, above the content area.
7. **Modals** center on screen with backdrop overlay.
8. **Toast notifications** appear top-right or bottom-right, stacked.
9. **Loading states** replace the content area; never show a blank page.
10. **Empty states** show in the content area with illustration + CTA to create first item.

## Per-App-Type Conventions

### Dashboard

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Summary cards (KPIs) | Main content, top row | 3-5 cards in a row, full-width |
| Data tables | Main content, below cards | Full-width or 2/3 width |
| Charts/graphs | Main content, mixed with tables | Card containers, responsive grid |
| Activity feed | Sidebar (right) or bottom of main | Scrollable, time-ordered |
| Quick actions | Top bar or sidebar | Common operations (create, export) |
| Filters / date range | Top of content area, below breadcrumbs | Persistent across page sections |
| Navigation items | Left sidebar | Grouped by category with icons |

### Chat

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Conversation list | Left panel (fixed width ~300px) | Scrollable, search at top |
| Message thread | Center panel (flex) | Scrollable, newest at bottom |
| Message input | Bottom of center panel | Fixed position, expands on focus |
| User/channel info | Right panel (collapsible) | Member list, shared files, pinned items |
| Typing indicator | Above input bar | Inline with message thread |
| File attachments | Inline in messages + drag-drop zone | Preview thumbnails |
| Emoji/reaction picker | Popover from input bar or message hover | Floating panel |

### Wizard / Form

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Step indicator | Top of content area | Horizontal steps with numbers/labels |
| Form fields | Center content (max-width ~600px) | Single column, generous spacing |
| Field validation | Inline below each field | Red text + icon on error |
| Next/Back buttons | Bottom of form area, right-aligned | Primary (next) + secondary (back) |
| Summary/review step | Final step, read-only view of all inputs | Editable via "edit" links per section |
| Progress bar | Top, as part of step indicator | Percentage or step count |
| Help text / tooltips | Inline below labels or hover info icons | Context-sensitive |

### Marketplace

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Search bar | Top, prominent, full-width or centered | Auto-suggest, recent searches |
| Category filters | Left sidebar (desktop) / top accordion (mobile) | Collapsible sections per filter type |
| Product grid | Main content (right of filters) | 3-4 columns, responsive to 1-2 on mobile |
| Product card | Within grid | Image, title, price, rating, CTA |
| Sort controls | Top of product grid, right-aligned | Dropdown: relevance, price, rating, newest |
| Pagination | Bottom of product grid | Page numbers or infinite scroll |
| Cart icon | Top nav, right side | Badge with item count |
| Product detail | Full page (replaces grid) | Image gallery left, info right |

### Tool

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Toolbar | Top of workspace | Icon buttons, grouped by function |
| Tool palette | Left sidebar (narrow, icon-only) | Vertical icon strip |
| Canvas/workspace | Center (takes maximum space) | Scrollable/zoomable |
| Properties panel | Right sidebar (collapsible) | Context-sensitive to selected element |
| Layers panel | Right sidebar (below properties) | Drag-reorderable list |
| Zoom controls | Bottom-right of canvas | Zoom in/out/fit buttons |
| Status bar | Bottom of screen, full-width | File info, cursor position, zoom level |
| Command palette | Center modal (on keyboard shortcut) | Searchable command list |

### Landing Page

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Nav bar | Top, sticky on scroll | Logo left, links center/right, CTA right |
| Hero section | Full-width, first section | Headline, subheadline, CTA, optional image/video |
| Feature grid | Below hero | 3-4 columns, icon + title + description |
| Social proof / testimonials | Below features | Carousel or grid of testimonial cards |
| Pricing table | Own section | 2-4 tier columns, highlight recommended |
| FAQ | Below pricing | Accordion pattern |
| CTA banner | Above footer | Full-width, contrasting background |
| Footer | Bottom | Logo, link columns, social icons, legal |

### Settings

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Tab/section nav | Left sidebar (vertical) or top (horizontal) | Category labels: Profile, Security, Notifications, etc. |
| Form sections | Main content area | Grouped by category, separated by dividers |
| Toggle switches | Inline in form sections | Right-aligned within rows |
| Save/Cancel buttons | Bottom of each section or sticky footer | Primary (save) + secondary (cancel) |
| Danger zone | Bottom of settings, red-bordered | Account deletion, data export |
| Avatar upload | Top of profile section | Click-to-upload with preview |
| Connected accounts | Own section | List with connect/disconnect buttons |

## Page Grouping Rules

When grouping mechanisms into pages:

| Mechanism Pattern | Page Pattern | Notes |
|------------------|-------------|-------|
| Auth (login, register, forgot password) | 1-3 pages: Login, Register, Forgot Password | Can be combined into one page with tabs |
| CRUD for an entity | 2 pages: Entity List + Entity Detail | Detail page handles create/edit via modal or inline |
| User profile | 1 page: Profile (within settings or standalone) | Combines view + edit modes |
| Search + Browse | 1 page with filters | Search is a component, not a separate page |
| Notifications | 0 pages (dropdown) or 1 page (full history) | Depends on notification volume |
| Admin panel | Multiple pages mirroring main app | Often a separate route prefix (/admin/*) |
| Onboarding | 1 wizard page (multi-step) | Shown once after registration |
| Error pages | 2 pages: 404, 500 | Static, minimal |

## Route Conventions

| Route Pattern | Usage |
|--------------|-------|
| `/` | Dashboard or landing (authenticated vs not) |
| `/login`, `/register`, `/forgot-password` | Auth pages |
| `/{entity}` | Entity list (e.g., `/tasks`, `/products`) |
| `/{entity}/:id` | Entity detail (e.g., `/tasks/123`) |
| `/{entity}/new` | Create new entity |
| `/settings` | Settings root |
| `/settings/{section}` | Settings sub-section |
| `/admin` | Admin panel root |
| `/admin/{entity}` | Admin entity management |


---
## REFERENCE: example-output

# Example Output — Task Management App

> Complete walkthrough of Stage 6 processing a task management app ("TaskFlow") with 8 mechanisms from Stage 4.

## Input Summary

**App concept:** TaskFlow — a team task management app with boards, lists, and card-based workflows.

**Archetype match:** `productivity-dashboard` (confidence: 0.92)

**Mechanisms from Stage 4:**

| ID | Name | Category | Has UI (from Stage 5 blueprints) |
|----|------|----------|----------------------------------|
| M1 | User Authentication | Auth | Yes (DOOR: login form, register form) |
| M2 | Team Management | Admin | Yes (DOOR: invite members, ROOM: team settings) |
| M3 | Board CRUD | Core | Yes (DOOR: create/edit board, ROOM: board view) |
| M4 | Task CRUD | Core | Yes (DOOR: create/edit task, ROOM: task detail) |
| M5 | Task Assignment | Core | Yes (DOOR: assign dropdown) |
| M6 | Notification Engine | System | Backend-only (all WALL steps) |
| M7 | Dashboard Analytics | Reporting | Yes (ROOM: charts, WALL: data aggregation) |
| M8 | User Preferences | Settings | Yes (DOOR: theme toggle, notification prefs) |

## Sub-6a Output: Arrangement Selection

```json
{
  "sub_6a": {
    "app_type_classification": "dashboard",
    "arrangement_options": [
      {
        "id": "opt_1",
        "name": "Sidebar + Top Nav + Content Grid",
        "description": "Collapsible left sidebar for board navigation, top bar with search and user menu, main area with card grid. Standard pattern for task management tools (Trello, Asana, Linear)."
      },
      {
        "id": "opt_2",
        "name": "Top Nav Only + Content Grid",
        "description": "No sidebar. Top nav with board switcher dropdown. Main area with full-width card grid. Simpler layout, better for fewer boards."
      },
      {
        "id": "opt_3",
        "name": "Sidebar + Kanban Columns",
        "description": "Left sidebar for boards, main area uses horizontal kanban columns instead of a grid. Best for workflow-heavy task management."
      }
    ],
    "selected_arrangement_id": "opt_1",
    "user_adjustments": null
  }
}
```

## Sub-6b Output: Page Mockups

```json
{
  "sub_6b": {
    "pages": [
      {
        "page_name": "Login",
        "route": "/login",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "LoginForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "RegisterLink",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Register",
        "route": "/register",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "RegisterForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Dashboard",
        "route": "/",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TopNavBar",
            "placement": "header",
            "mechanism_ids": []
          },
          {
            "component_name": "SearchBar",
            "placement": "header",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "UserMenu",
            "placement": "header",
            "mechanism_ids": ["M1", "M8"]
          },
          {
            "component_name": "TaskSummaryCards",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "RecentActivityFeed",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "TeamOverviewWidget",
            "placement": "main-content",
            "mechanism_ids": ["M2", "M7"]
          }
        ],
        "backend_services": ["M6"],
        "user_approved": true
      },
      {
        "page_name": "Board Detail",
        "route": "/boards/:id",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "BoardHeader",
            "placement": "main-content",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TaskCardGrid",
            "placement": "main-content",
            "mechanism_ids": ["M4", "M5"]
          },
          {
            "component_name": "CreateTaskButton",
            "placement": "main-content",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "TaskDetailDrawer",
            "placement": "drawer",
            "mechanism_ids": ["M4", "M5"]
          }
        ],
        "user_approved": true
      },
      {
        "page_name": "Settings",
        "route": "/settings",
        "layout_pattern": "sidebar-tabs-form",
        "components": [
          {
            "component_name": "SettingsTabNav",
            "placement": "sidebar",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ProfileSection",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "TeamManagementSection",
            "placement": "main-content",
            "mechanism_ids": ["M2"]
          },
          {
            "component_name": "NotificationPreferences",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ThemeToggle",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          }
        ],
        "user_approved": true
      }
    ],
    "all_mechanisms_mapped": true,
    "pages_approved": true
  }
}
```

### Mechanism Mapping Verification

| Mechanism | Pages |
|-----------|-------|
| M1 (Auth) | Login, Register, Dashboard (UserMenu), Settings (ProfileSection) |
| M2 (Team) | Dashboard (TeamOverviewWidget), Settings (TeamManagementSection) |
| M3 (Board CRUD) | Dashboard (BoardSidebar), Board Detail (BoardSidebar, BoardHeader) |
| M4 (Task CRUD) | Dashboard (SearchBar), Board Detail (TaskCardGrid, CreateTaskButton, TaskDetailDrawer) |
| M5 (Task Assignment) | Board Detail (TaskCardGrid, TaskDetailDrawer) |
| M6 (Notifications) | Dashboard (backend_services) — backend-only, no UI components |
| M7 (Analytics) | Dashboard (TaskSummaryCards, RecentActivityFeed, TeamOverviewWidget) |
| M8 (Preferences) | Dashboard (UserMenu), Settings (SettingsTabNav, NotificationPreferences, ThemeToggle) |

**All mechanisms mapped: ✅**

## Sub-6c Output: Style Selection

### Style Curation Scoring

| Style | audience_fit | vibe_match | app_type_fit | Composite |
|-------|-------------|------------|-------------|-----------|
| flat-design | 90 | 85 | 95 | **89.75** |
| minimalism | 85 | 80 | 85 | **83.25** |
| dark-mode | 80 | 75 | 90 | **80.75** |

### Output

```json
{
  "sub_6c": {
    "style_options_presented": [
      {
        "id": "flat-design",
        "name": "Flat Design",
        "vibe": "Clean, clear, universal — the 'just works' default for productivity tools"
      },
      {
        "id": "minimalism",
        "name": "Minimalism",
        "vibe": "Premium, elegant — Apple-inspired feel for a focused task experience"
      },
      {
        "id": "dark-mode",
        "name": "Dark Mode Elegant",
        "vibe": "Refined dark theme — easy on the eyes for long work sessions"
      }
    ],
    "selected_style_id": "flat-design",
    "design_tokens": {
      "colors": {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "accent": "#F59E0B",
        "surface": "#FFFFFF",
        "surface_alt": "#F8FAFC",
        "text": "#1E293B",
        "text_secondary": "#64748B",
        "border": "#E2E8F0",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6"
      },
      "typography": {
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "mono_font": "JetBrains Mono, Fira Code, monospace",
        "sizes": {
          "xs": "0.75rem",
          "sm": "0.875rem",
          "base": "1rem",
          "lg": "1.125rem",
          "xl": "1.25rem",
          "2xl": "1.5rem",
          "3xl": "1.875rem",
          "4xl": "2.25rem"
        },
        "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
        "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
      },
      "spacing": {
        "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
        "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
        "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
      },
      "border_radius": {
        "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"
      },
      "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.07)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.1)"
      }
    },
    "tailwind_config_overrides": {
      "extend": {
        "colors": {
          "primary": "#3B82F6",
          "secondary": "#8B5CF6",
          "accent": "#F59E0B",
          "surface": { "DEFAULT": "#FFFFFF", "alt": "#F8FAFC" }
        },
        "fontFamily": {
          "heading": ["Inter", "system-ui", "sans-serif"],
          "body": ["Inter", "system-ui", "sans-serif"],
          "mono": ["JetBrains Mono", "Fira Code", "monospace"]
        },
        "borderRadius": {
          "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem"
        },
        "boxShadow": {
          "sm": "0 1px 2px rgba(0,0,0,0.05)",
          "md": "0 4px 6px rgba(0,0,0,0.07)",
          "lg": "0 10px 15px rgba(0,0,0,0.1)"
        }
      }
    },
    "audience_scores": {
      "audience_fit": 90,
      "vibe_match": 85,
      "age_range_fit": 88
    }
  }
}
```

## Confidence Scoring

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Completeness | 19/20 | 5 pages, all 8 mechanisms mapped, all 3 sub-stages populated, full design tokens |
| Accuracy | 19/20 | Dashboard pattern correct for productivity app; auth on login pages, CRUD on board detail, analytics on dashboard |
| Consistency | 20/20 | No route conflicts; all mechanism_ids reference real M1-M8; flat-design matches productivity archetype |
| Specificity | 18/20 | Every component has placement and mechanism connection; tokens are hex/rem values; a developer could build from this |
| Handoff Readiness | 18/20 | Stage 7 can create file lists from page/component names; token estimates derivable from component count |

**Total: 94/100 — PASS**

## Metadata Written

```json
{
  "metadata": {
    "current_stage": 6,
    "updated_at": "2026-04-03T14:30:00Z",
    "confidence_scores": {
      "6": {
        "score": 94,
        "dimensions": {
          "completeness": 19,
          "accuracy": 19,
          "consistency": 20,
          "specificity": 18,
          "handoff_readiness": 18
        },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "6": "2026-04-03T14:30:00Z"
    }
  }
}
```


---
## REFERENCE: style-catalog

# Style Catalog — 12 Predefined Styles

> Complete token sets for all 12 styles. The skill curates 3 from these 12 based on app type + audience fit.

## Curation Algorithm

To select 3 styles from the catalog:

1. **Score each style** against three criteria (0-100 each):
   - `audience_fit`: Does the style match the target user's age, profession, and expectations?
   - `vibe_match`: Does the style's vibe align with the product's core value proposition?
   - `app_type_fit`: Is this style commonly used for this app type?
2. **Composite score** = (audience_fit × 0.4) + (vibe_match × 0.35) + (app_type_fit × 0.25)
3. **Pick top 3** by composite score. If a tie, prefer more universally appealing styles.
4. **"Choose for me"** default = highest composite score.

### App Type Affinity Matrix

| Style | dashboard | chat | wizard | marketplace | tool | landing | settings |
|-------|-----------|------|--------|-------------|------|---------|----------|
| flat-design | 95 | 80 | 90 | 85 | 80 | 85 | 90 |
| minimalism | 85 | 85 | 85 | 80 | 75 | 95 | 85 |
| neumorphism | 80 | 60 | 75 | 55 | 70 | 60 | 85 |
| glassmorphism | 75 | 80 | 70 | 75 | 65 | 90 | 70 |
| skeuomorphism | 50 | 45 | 60 | 55 | 65 | 40 | 70 |
| neubrutalism | 55 | 65 | 50 | 70 | 55 | 85 | 45 |
| bauhaus | 60 | 55 | 55 | 60 | 70 | 80 | 50 |
| claymorphism | 55 | 70 | 75 | 65 | 45 | 75 | 60 |
| retro-futurism | 45 | 50 | 40 | 50 | 60 | 70 | 35 |
| cyberpunk | 50 | 55 | 35 | 45 | 70 | 65 | 40 |
| dark-mode | 90 | 85 | 65 | 70 | 95 | 75 | 80 |
| warmer-shades | 70 | 75 | 80 | 75 | 50 | 80 | 80 |

### Audience Affinity Guide

| Audience Trait | Best Styles | Avoid |
|---------------|-------------|-------|
| Enterprise / Corporate | flat-design, minimalism, dark-mode | neubrutalism, cyberpunk, claymorphism |
| Gen Z / Young Adults | neubrutalism, glassmorphism, cyberpunk | skeuomorphism, neumorphism |
| Creative Professionals | bauhaus, minimalism, dark-mode | skeuomorphism, flat-design |
| General Consumer | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |
| Developers / Technical | dark-mode, flat-design, minimalism | claymorphism, skeuomorphism |
| Older Demographics (50+) | skeuomorphism, warmer-shades, flat-design | cyberpunk, neubrutalism |
| Health / Wellness | claymorphism, minimalism, warmer-shades | cyberpunk, neubrutalism |
| Gaming / Entertainment | cyberpunk, retro-futurism, neubrutalism | minimalism, flat-design |
| Finance / Banking | neumorphism, dark-mode, minimalism | claymorphism, retro-futurism |
| Education | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |

---

## Style Definitions

### 1. flat-design

**Vibe:** Clean, clear, universal — the "just works" default
**Best for:** Clarity, scalability, universal appeal

```json
{
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#8B5CF6",
    "accent": "#F59E0B",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.07)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.1)"
  }
}
```

**Tailwind overrides:**
```json
{
  "extend": {
    "colors": { "primary": "#3B82F6", "secondary": "#8B5CF6", "accent": "#F59E0B" },
    "fontFamily": { "heading": ["Inter", "system-ui", "sans-serif"], "body": ["Inter", "system-ui", "sans-serif"] }
  }
}
```

---

### 2. minimalism

**Vibe:** Premium, elegant, Apple-inspired — less is more
**Best for:** Premium feel, Apple-style elegance

```json
{
  "colors": {
    "primary": "#000000",
    "secondary": "#6B7280",
    "accent": "#2563EB",
    "surface": "#FFFFFF",
    "surface_alt": "#FAFAFA",
    "text": "#111827",
    "text_secondary": "#9CA3AF",
    "border": "#F3F4F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#2563EB"
  },
  "typography": {
    "heading_font": "SF Pro Display, -apple-system, system-ui, sans-serif",
    "body_font": "SF Pro Text, -apple-system, system-ui, sans-serif",
    "mono_font": "SF Mono, Menlo, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(0,0,0,0.04)",
    "md": "0 4px 6px rgba(0,0,0,0.04)",
    "lg": "0 10px 20px rgba(0,0,0,0.06)",
    "xl": "0 25px 50px rgba(0,0,0,0.08)"
  }
}
```

---

### 3. neumorphism

**Vibe:** Soft, tactile, embossed — like pressing real buttons
**Best for:** Finance apps, dashboards, toggles

```json
{
  "colors": {
    "primary": "#6366F1",
    "secondary": "#8B5CF6",
    "accent": "#EC4899",
    "surface": "#E0E5EC",
    "surface_alt": "#D1D9E6",
    "text": "#2D3748",
    "text_secondary": "#718096",
    "border": "#C9D1DC",
    "success": "#48BB78",
    "warning": "#ECC94B",
    "error": "#FC8181",
    "info": "#63B3ED"
  },
  "typography": {
    "heading_font": "Poppins, sans-serif",
    "body_font": "Poppins, sans-serif",
    "mono_font": "Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "3px 3px 6px #b8b9be, -3px -3px 6px #ffffff",
    "md": "5px 5px 10px #b8b9be, -5px -5px 10px #ffffff",
    "lg": "8px 8px 16px #b8b9be, -8px -8px 16px #ffffff",
    "xl": "12px 12px 24px #b8b9be, -12px -12px 24px #ffffff"
  }
}
```

---

### 4. glassmorphism

**Vibe:** Frosted glass, depth, modern — translucent layers
**Best for:** Modern SaaS, trendy products

```json
{
  "colors": {
    "primary": "#7C3AED",
    "secondary": "#2DD4BF",
    "accent": "#F472B6",
    "surface": "rgba(255, 255, 255, 0.25)",
    "surface_alt": "rgba(255, 255, 255, 0.15)",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "rgba(255, 255, 255, 0.3)",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Plus Jakarta Sans, sans-serif",
    "body_font": "Plus Jakarta Sans, sans-serif",
    "mono_font": "JetBrains Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 2px 8px rgba(0,0,0,0.1)",
    "md": "0 8px 32px rgba(0,0,0,0.12)",
    "lg": "0 16px 48px rgba(0,0,0,0.15)",
    "xl": "0 24px 64px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Glassmorphism requires `backdrop-filter: blur(16px)` on surface elements.

---

### 5. skeuomorphism

**Vibe:** Familiar, physical, textured — like real-world objects
**Best for:** Familiarity, older demographics

```json
{
  "colors": {
    "primary": "#2E7D32",
    "secondary": "#5D4037",
    "accent": "#FF8F00",
    "surface": "#F5F0EB",
    "surface_alt": "#EDE7E0",
    "text": "#3E2723",
    "text_secondary": "#6D4C41",
    "border": "#BCAAA4",
    "success": "#2E7D32",
    "warning": "#FF8F00",
    "error": "#C62828",
    "info": "#1565C0"
  },
  "typography": {
    "heading_font": "Georgia, Times New Roman, serif",
    "body_font": "Verdana, Geneva, sans-serif",
    "mono_font": "Courier New, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.625rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3)",
    "md": "0 3px 6px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.25)",
    "lg": "0 6px 12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.2)",
    "xl": "0 10px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)"
  }
}
```

---

### 6. neubrutalism

**Vibe:** Bold, raw, unapologetic — thick borders, loud colors
**Best for:** Young/edgy, Gen Z products

```json
{
  "colors": {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "surface": "#FFFFFF",
    "surface_alt": "#FFF8E1",
    "text": "#000000",
    "text_secondary": "#333333",
    "border": "#000000",
    "success": "#4ECDC4",
    "warning": "#FFE66D",
    "error": "#FF6B6B",
    "info": "#45B7D1"
  },
  "typography": {
    "heading_font": "Space Grotesk, sans-serif",
    "body_font": "Space Grotesk, sans-serif",
    "mono_font": "Space Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.25rem",
      "xl": "1.5rem", "2xl": "2rem", "3xl": "2.5rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.1, "normal": 1.4, "relaxed": 1.6 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "2px 2px 0 #000000",
    "md": "4px 4px 0 #000000",
    "lg": "6px 6px 0 #000000",
    "xl": "8px 8px 0 #000000"
  }
}
```

**Note:** Neubrutalism uses thick solid borders (2-3px black) instead of subtle borders.

---

### 7. bauhaus

**Vibe:** Geometric, primary colors, form-follows-function
**Best for:** Design-forward, artistic

```json
{
  "colors": {
    "primary": "#D32F2F",
    "secondary": "#1976D2",
    "accent": "#FBC02D",
    "surface": "#FAFAFA",
    "surface_alt": "#F5F5F5",
    "text": "#212121",
    "text_secondary": "#757575",
    "border": "#BDBDBD",
    "success": "#388E3C",
    "warning": "#FBC02D",
    "error": "#D32F2F",
    "info": "#1976D2"
  },
  "typography": {
    "heading_font": "Oswald, sans-serif",
    "body_font": "Roboto, sans-serif",
    "mono_font": "Roboto Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.75rem", "3xl": "2.25rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0", "lg": "0", "xl": "0", "full": "50%" },
  "shadows": {
    "sm": "0 2px 4px rgba(0,0,0,0.1)",
    "md": "0 4px 8px rgba(0,0,0,0.12)",
    "lg": "0 8px 16px rgba(0,0,0,0.15)",
    "xl": "0 16px 32px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Bauhaus uses sharp corners (border-radius: 0) except for deliberate circles (full: 50%).

---

### 8. claymorphism

**Vibe:** Soft, puffy, friendly — like clay or dough
**Best for:** Friendly, approachable products

```json
{
  "colors": {
    "primary": "#7C5CFC",
    "secondary": "#FF8A65",
    "accent": "#4DD0E1",
    "surface": "#F0EEFF",
    "surface_alt": "#E8E4FF",
    "text": "#2D2B55",
    "text_secondary": "#6E6B9A",
    "border": "#D4D0F0",
    "success": "#66BB6A",
    "warning": "#FFB74D",
    "error": "#EF5350",
    "info": "#42A5F5"
  },
  "typography": {
    "heading_font": "Nunito, sans-serif",
    "body_font": "Nunito, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 600, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.75rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem", "full": "9999px" },
  "shadows": {
    "sm": "0 4px 8px rgba(124,92,252,0.15), inset 0 -2px 4px rgba(0,0,0,0.05)",
    "md": "0 8px 16px rgba(124,92,252,0.18), inset 0 -3px 6px rgba(0,0,0,0.06)",
    "lg": "0 12px 24px rgba(124,92,252,0.2), inset 0 -4px 8px rgba(0,0,0,0.07)",
    "xl": "0 16px 32px rgba(124,92,252,0.22), inset 0 -5px 10px rgba(0,0,0,0.08)"
  }
}
```

---

### 9. retro-futurism

**Vibe:** Neon + nostalgia, VHS tracking lines, 80s sci-fi
**Best for:** Gaming, entertainment

```json
{
  "colors": {
    "primary": "#FF00FF",
    "secondary": "#00FFFF",
    "accent": "#FFFF00",
    "surface": "#1A0033",
    "surface_alt": "#2A0052",
    "text": "#FFFFFF",
    "text_secondary": "#B794F6",
    "border": "#6B21A8",
    "success": "#00FF88",
    "warning": "#FFFF00",
    "error": "#FF0066",
    "info": "#00CCFF"
  },
  "typography": {
    "heading_font": "Orbitron, sans-serif",
    "body_font": "Rajdhani, sans-serif",
    "mono_font": "Share Tech Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 8px rgba(255,0,255,0.4)",
    "md": "0 0 16px rgba(255,0,255,0.5)",
    "lg": "0 0 32px rgba(255,0,255,0.5), 0 0 8px rgba(0,255,255,0.3)",
    "xl": "0 0 48px rgba(255,0,255,0.6), 0 0 16px rgba(0,255,255,0.4)"
  }
}
```

---

### 10. cyberpunk

**Vibe:** Dark, glitchy, neon-on-black, tech-dystopia
**Best for:** Edgy tech, gaming

```json
{
  "colors": {
    "primary": "#00F0FF",
    "secondary": "#FF003C",
    "accent": "#B6FF00",
    "surface": "#0D0D0D",
    "surface_alt": "#1A1A2E",
    "text": "#E0E0E0",
    "text_secondary": "#888888",
    "border": "#333355",
    "success": "#B6FF00",
    "warning": "#FFB800",
    "error": "#FF003C",
    "info": "#00F0FF"
  },
  "typography": {
    "heading_font": "Exo 2, sans-serif",
    "body_font": "IBM Plex Sans, sans-serif",
    "mono_font": "IBM Plex Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 6px rgba(0,240,255,0.3)",
    "md": "0 0 12px rgba(0,240,255,0.4)",
    "lg": "0 0 24px rgba(0,240,255,0.4), 0 0 6px rgba(255,0,60,0.2)",
    "xl": "0 0 48px rgba(0,240,255,0.5), 0 0 12px rgba(255,0,60,0.3)"
  }
}
```

---

### 11. dark-mode

**Vibe:** Refined dark, professional, easy on the eyes
**Best for:** Developer tools, media apps

```json
{
  "colors": {
    "primary": "#818CF8",
    "secondary": "#34D399",
    "accent": "#FBBF24",
    "surface": "#111827",
    "surface_alt": "#1F2937",
    "text": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "border": "#374151",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.3)",
    "md": "0 4px 6px rgba(0,0,0,0.4)",
    "lg": "0 10px 15px rgba(0,0,0,0.5)",
    "xl": "0 20px 25px rgba(0,0,0,0.6)"
  }
}
```

---

### 12. warmer-shades

**Vibe:** Warm, nostalgic, comfortable — earth tones and soft edges
**Best for:** Nostalgic, comfortable feel

```json
{
  "colors": {
    "primary": "#B45309",
    "secondary": "#92400E",
    "accent": "#D97706",
    "surface": "#FFFBEB",
    "surface_alt": "#FEF3C7",
    "text": "#451A03",
    "text_secondary": "#78350F",
    "border": "#D6C4A8",
    "success": "#65A30D",
    "warning": "#D97706",
    "error": "#DC2626",
    "info": "#0284C7"
  },
  "typography": {
    "heading_font": "Lora, Georgia, serif",
    "body_font": "Source Sans 3, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.375rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(120,53,15,0.08)",
    "md": "0 4px 8px rgba(120,53,15,0.1)",
    "lg": "0 8px 16px rgba(120,53,15,0.12)",
    "xl": "0 16px 32px rgba(120,53,15,0.15)"
  }
}
```


---
## REFERENCE: wireframe-pattern-lookup

# Wireframe Pattern Lookup Table

> Deterministic mapping from app type to wireframe pattern. This is NOT AI creativity — it's a lookup. The AI identifies the app type; the pattern follows from this table.

## Primary Patterns (92% Case)

| App Type | Wireframe Pattern | Navigation | Content Area | Key Elements |
|----------|------------------|------------|-------------|-------------|
| `dashboard` | Sidebar + Top Nav + Content Grid + Cards | Collapsible sidebar (left), breadcrumb top bar | Grid of cards/widgets, charts, tables | Summary cards, data tables, charts, activity feed, quick actions |
| `chat` | Conversation List + Message Thread + Input Bar | Left panel (conversation list), no top nav needed | Message thread (center), optional right panel (details) | Contact/channel list, message bubbles, input with attachments, typing indicator |
| `wizard` | Step Indicator + Single Form Area + Next/Back | Step progress bar (top), minimal nav | Single form section (center), navigation buttons (bottom) | Progress steps, form fields, validation, prev/next buttons, summary step |
| `marketplace` | Search Bar + Filter Sidebar + Product Grid | Top search bar, left filter panel | Product card grid (center), pagination | Search input, category filters, price range, sort, product cards, cart icon |
| `tool` | Toolbar + Workspace + Properties Panel | Toolbar (top), tool palette (left optional) | Canvas/workspace (center), properties panel (right) | Tool buttons, canvas area, property editors, layers panel, zoom controls |
| `landing` | Hero + Features + Testimonials + CTA | Sticky top nav with CTA button | Full-width sections, stacked vertically | Hero with headline + CTA, feature grid, testimonial cards, pricing table, footer |
| `settings` | Tab List + Form Sections | Vertical tab list (left) or horizontal tabs (top) | Form sections per tab | Tab navigation, labeled form groups, toggles, save/cancel buttons |

## Secondary Patterns (Variations)

### Dashboard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Top Nav Only + Grid | No sidebar, horizontal nav with dropdowns | Simple dashboards with < 5 sections |
| Sidebar + Cards Only | No top nav, sidebar handles all navigation | Data-heavy dashboards, admin panels |
| Tabbed Dashboard | Tab bar at top, each tab is a dashboard view | Multi-role dashboards (e.g., admin vs user view) |

### Chat Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Full-width Thread | No conversation list visible, toggle to switch | Mobile-first chat, single-conversation focus |
| Chat + Sidebar Widgets | Conversation list + thread + right sidebar with tools | Support/helpdesk apps with customer context |
| Threaded Channels | Channel list + thread + nested replies | Team communication (Slack-like) |

### Wizard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Sidebar Steps | Steps listed in left sidebar instead of top bar | Complex wizards with 8+ steps |
| Card-per-Step | Each step is a card, all visible, expand on click | Short wizards (3-4 steps) where overview matters |
| Modal Wizard | Wizard in a modal overlay | Secondary flows (e.g., onboarding after signup) |

### Marketplace Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Map + List | Split view: map (left/top) + list (right/bottom) | Location-based marketplaces (Airbnb-like) |
| Gallery Grid | No filter sidebar, full-width masonry grid | Visual-first marketplaces (art, photography) |
| Category Browse | Category cards → subcategory → product list | Deep catalog with hierarchical categories |

### Tool Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Split Pane | Two resizable panes (e.g., code editor + preview) | Editor/IDE tools, diff viewers |
| Canvas Only | Full-screen canvas, floating toolbars | Drawing/design tools, whiteboard apps |
| Command Palette | Minimal UI, keyboard-driven with command palette | Developer tools, power-user interfaces |

### Landing Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Single Page Scroll | All sections on one page, smooth scroll between | Simple products with one offering |
| Multi-page Marketing | Landing + separate pages for features, pricing, docs | Complex products needing deep content |
| App-Shell Landing | Landing that transitions into the app (no full reload) | SaaS products with free-tier access |

## Hybrid Pattern Resolution

When an app combines two types (e.g., dashboard + chat):

1. Identify the DOMINANT type — what does the user spend 70%+ of their time doing?
2. Use the dominant type's pattern as the PRIMARY arrangement
3. Embed the secondary type as a component WITHIN the primary layout:
   - Chat in a dashboard → Chat panel in sidebar or slide-out drawer
   - Dashboard in a tool → Stats widgets in the tool's properties panel
   - Marketplace with chat → Chat as a modal/drawer from product detail
4. Present BOTH the pure dominant pattern AND the hybrid as separate arrangement options

## Archetype-to-App-Type Mapping

| Archetype Keywords | App Type |
|-------------------|----------|
| productivity, admin, analytics, monitoring, CRM, ERP | `dashboard` |
| messaging, communication, support, helpdesk | `chat` |
| onboarding, form-builder, survey, checkout, registration | `wizard` |
| e-commerce, listings, search-browse, two-sided | `marketplace` |
| editor, builder, IDE, canvas, designer | `tool` |
| marketing, portfolio, product-page, SaaS-homepage | `landing` |
| preferences, configuration, profile, account | `settings` |

If the archetype contains keywords from multiple types, it's a hybrid — follow the hybrid resolution above.

