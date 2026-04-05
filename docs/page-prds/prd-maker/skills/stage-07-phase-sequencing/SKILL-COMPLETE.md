---
name: stage-07-phase-sequencing
description: Split a complete PRD spec into token-budgeted build phases with file sandboxes, build orders, and dependency mapping.
---

## Purpose

Takes a complete spec (mechanisms scaffolded with Wall/Door/Room classifications, wireframes approved, style selected from Stages 0–6) and splits it into buildable phases using math-based token budget calculations. Each phase becomes a self-contained containment unit with its own file sandbox, forced build order, and explicit dependency mapping. Stage 7 does the structural split; Stage 8 injects enforcement protocols.

## When to Use

Activate when ALL of the following are present in the context packet:
- `stage_0.tech_stack` — framework and language (needed for file path conventions and tech-appropriate build orders)
- `stage_5.mechanism_blueprints` — mechanisms with W/D/R classifications
- `stage_4.mechanisms` and `stage_4.mechanism_dependencies` — mechanism list and dependency graph
- `stage_6.sub_6a`, `stage_6.sub_6b`, `stage_6.sub_6c.design_tokens` — wireframes and style
- `stage_3.drift_anchor` and `stage_2.scope_contract` — product identity and scope

This skill produces: `stage_7.token_budget`, `stage_7.phases`, `stage_7.mandatory_build_order`.

## Input Format

```json
{
  "stage_2": { "scope_contract": "..." },
  "stage_3": { "drift_anchor": "..." },
  "stage_4": {
    "mechanisms": [{ "id": "M1", "name": "...", "tags": ["OBVIOUS"] }],
    "mechanism_dependencies": [{ "from": "M1", "to": "M2" }]
  },
  "stage_5": {
    "mechanism_blueprints": [{ "mechanism_id": "M1", "wdr_classification": {...} }]
  },
  "stage_6": {
    "sub_6a": {
      "app_type_classification": "dashboard|chat|wizard|marketplace|tool|landing|settings",
      "arrangement_options": [{ "id": "...", "name": "...", "description": "..." }],
      "selected_arrangement_id": "...",
      "user_adjustments": "string | null"
    },
    "sub_6b": {
      "pages": [
        {
          "page_name": "...",
          "route": "/...",
          "layout_pattern": "...",
          "components": [
            { "component_name": "...", "placement": "...", "mechanism_ids": ["M1"] }
          ],
          "backend_services": ["M5"],
          "user_approved": true
        }
      ],
      "all_mechanisms_mapped": true,
      "pages_approved": true
    },
    "sub_6c": {
      "style_options_presented": [{ "id": "...", "name": "...", "vibe": "..." }],
      "selected_style_id": "...",
      "design_tokens": { "colors": {"primary": "#hex", "...":" ..."}, "typography": {"heading_font": "...", "body_font": "...", "sizes": {}} },
      "tailwind_config_overrides": {},
      "audience_scores": { "audience_fit": 0, "vibe_match": 0, "age_range_fit": 0 }
    }
  },
  "stage_0": { "tech_stack": { "framework": "...", "language": "...", "database": "...", "auth_provider": "..." } }
}
```

## Process

### Step 1: Estimate Total Token Count

Aggregate all build content from Stages 3–6. Use `stage_0.tech_stack` to select appropriate file path conventions and adjust estimates for framework-specific overhead (e.g., Next.js API routes vs plain Express handlers).

For each mechanism blueprint, estimate tokens based on complexity:

| Complexity | Criteria | Token Range |
|------------|----------|-------------|
| **Simple** | 1–2 files, WALL-dominant, single concern. No state management, no API calls. Example: a static config module, a utility library, a type definitions file. | ~15,000–25,000 tokens |
| **Medium** | 3–5 files, mixed W/D/R, 2–3 connected components. Basic state management (one context or store), one API endpoint, possibly one database table. Example: a settings page with a form, an API route, and a service file. | ~30,000–60,000 tokens |
| **Complex** | 6+ files, DOOR/ROOM-heavy, cross-cutting integrations. Shared state across multiple consumers, multiple API endpoints, database schema with relations, multi-page UI with interactive components. Example: an auth system with sign-in/sign-up pages, session management, protected routes, and a user profile. | ~60,000–120,000 tokens |

For finer-grained estimation, use per-file token budgets when summing mechanism totals:

| File Type | Criteria | Token Range |
|-----------|----------|-------------|
| **Trivial file** | Single-purpose, no logic branching — type definitions, constants, re-export barrels, static config | ~200–500 tokens |
| **Simple file** | One function/component, no state, no API calls — a utility helper, a presentational component, a validation schema | ~500–1,500 tokens |
| **Medium file** | 2–3 exports, basic state or one API call — a form component with validation, a service file with CRUD operations, a context provider | ~1,500–3,000 tokens |
| **Complex file** | 4+ exports, shared state, multiple API calls, conditional logic — a page with data fetching + filtering + pagination, an auth service with multiple flows, a database migration with relations | ~3,000–6,000 tokens |
| **Heavy file** | Full-page orchestration, multi-step workflows, real-time updates, complex UI interactions — a dashboard with charts + filters + live data, an editor with undo/redo, a checkout flow | ~6,000–12,000 tokens |

To estimate a mechanism's total tokens: classify each file in its blueprint, sum the per-file estimates, then add 10–15% for build instruction prose (rationale text, sandbox declarations, build order commentary). Cross-check: the per-file sum should fall within the mechanism complexity range above.

Add per-page UI tokens from Stage 6b based on component count and page type:

| Page Type | Criteria | Token Range |
|-----------|----------|-------------|
| **Simple** | Static or display-only, 1–2 components, no forms or data fetching | ~5,000–8,000 tokens |
| **Form page** | User input, validation, 1 API call, 3–4 components | ~8,000–12,000 tokens |
| **Data-heavy** | Tables, charts, filters, multiple API calls, 5+ components | ~12,000–20,000 tokens |
| **Interactive** | Real-time updates, drag-and-drop, editors, complex state, 8+ components | ~20,000–40,000 tokens |

Sum all mechanism and page estimates to get `total_spec_tokens`.

### Step 2: Calculate Phase Count

Apply the formula (see [references/token-budget-math.md](references/token-budget-math.md)):

```
total_budget = 500,000 tokens (50% of 1M context)
overhead_per_phase = 25,000 tokens (fixed)
budget_per_phase_content = 325,000 tokens
phases_needed = ceil(total_spec_tokens / 325,000)
```

Minimum 1 phase. If `total_spec_tokens` ≤ 325,000, use 1 phase.

### Step 3: Find Natural Break Points

1. Sort mechanisms by dependency order (topological sort using `stage_4.mechanism_dependencies`).
2. Walk the sorted list, accumulating token estimates.
3. When accumulated tokens approach 325,000, look for the nearest mechanism boundary.
4. NEVER split a mechanism across phases. If a mechanism straddles the boundary, keep it in whichever phase maintains the best fit.
5. Keep tightly-coupled mechanisms together (check dependency edges — if M1→M2, prefer same phase).
6. Verify: every mechanism appears in exactly one phase.

### Step 4: Assign File Sandboxes

For each phase, derive file paths from the mechanisms' blueprints and Stage 6b page layouts. Classify into three tiers (see [references/file-sandbox-template.md](references/file-sandbox-template.md)):

- **files_allowed**: Exact file paths this phase creates or modifies. Mark each as NEW or MODIFY.
- **files_read_only**: Files from prior phases this phase can reference for patterns (e.g., auth patterns, DB helpers). Always include CLAUDE.md.
- **files_forbidden**: Everything else. Explicitly list critical files: `.env`, existing migrations, config files, and files owned by other phases.
- **do_not_change**: Global protections that apply to ALL phases: `CLAUDE.md`, `.env`, `BUILD_RULES.md`, existing migration files.

### Step 5: Define Build Order Per Phase

Within each phase, define a forced linear sequence following Martin's pattern (see [references/build-order-patterns.md](references/build-order-patterns.md)):

1. **Core logic** — Business logic, utilities, helpers, types
2. **State management** — Contexts, stores, hooks, data fetching
3. **UI components** — Pages, components, forms
4. **Integration** — Route wiring, exports, entry points

Every file in `files_allowed` MUST appear in `build_order`. Each entry includes `file_path`, `operation` ("create" or "modify"), and `rationale` explaining its position.

### Step 6: Define Phase Dependencies

- Phase 1 always has `depends_on: []`.
- Default: sequential (Phase N depends on Phase N-1).
- If two phases share no mechanism dependencies and no file overlaps, they MAY run in parallel (rare).
- Dependencies must form a DAG — verify no cycles.

### Step 7: Verify Fit

For each phase, confirm:
- `estimated_tokens + 25,000 (overhead) ≤ 350,000`
- If exceeded, move the last mechanism to the next phase and recalculate.
- Confirm: `sum(all phases' estimated_tokens) ≈ total_spec_tokens` (±10%).
- Do NOT compress content to fit. Adjust split points instead.

## Output Format

Written to `context_packet.stage_7`:

```json
{
  "phase_count": 2,
  "total_estimated_tokens": 650000,
  "token_budget": {
    "budget_per_phase_content": 325000,
    "overhead_per_phase": 25000,
    "total_budget": 500000
  },
  "phases": [
    {
      "phase_number": 1,
      "phase_name": "Core Auth & Data Layer",
      "mechanisms_included": ["M1", "M2", "M3"],
      "estimated_content_tokens": 310000,
      "estimated_total_tokens": 335000,
      "build_order": [
        { "file_path": "src/lib/auth.ts", "operation": "create", "rationale": "Core auth logic — all other files depend on this" },
        { "file_path": "src/contexts/AuthContext.tsx", "operation": "create", "rationale": "State wrapper for auth — needed by UI" },
        { "file_path": "src/pages/SignIn.tsx", "operation": "create", "rationale": "UI consumes AuthContext" },
        { "file_path": "src/App.tsx", "operation": "modify", "rationale": "Wire auth routes — integration last" }
      ],
      "file_sandbox": {
        "allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx", "src/pages/SignIn.tsx", "src/pages/SignUp.tsx", "src/App.tsx"],
        "read_only": ["CLAUDE.md", "package.json"],
        "forbidden": ["src/lib/supabase.ts", ".env", "supabase/migrations/*"]
      },
      "depends_on": [],
      "do_not_change": ["CLAUDE.md", ".env", "BUILD_RULES.md"]
    }
  ],
  "no_mechanism_split": true,
  "token_math_verified": true,
  "mandatory_build_order": [
    { "rule": "Core logic files before state management", "phases_affected": [1, 2] },
    { "rule": "State management before UI components", "phases_affected": [1, 2] },
    { "rule": "UI components before integration/routing", "phases_affected": [1, 2] }
  ]
}
```

Also update metadata:
```json
{
  "metadata.current_stage": 7,
  "metadata.stage_timestamps.7": "ISO-8601",
  "metadata.confidence_scores.7": { "score": 92, "dimensions": {...} }
}
```

## Edge Cases

### Missing Input

If `stage_4.mechanisms` is empty or missing: trigger escape hatch. Phase sequencing requires a mechanism list — there is nothing to split.

If `stage_6.sub_6b` (page mockups) is missing: proceed with mechanism-only file inference. Flag `handoff_readiness` confidence dimension as reduced (max 12/20). Build orders will lack specific page/component paths.

If `stage_4.mechanism_dependencies` is missing: treat all mechanisms as independent. Default to sequential phases ordered by mechanism complexity (simplest first). Flag in metadata.

### Ambiguous Input

If a mechanism has no clear file mapping (no page in Stage 6b references it): create a placeholder path based on the mechanism name and tech stack conventions (e.g., `src/lib/{mechanism-name-kebab}.ts`). Add a warning to the phase noting the inferred path.

If mechanism token estimates vary by >50% depending on interpretation: use the higher estimate. It is safer to have extra phases than to overflow.

### Scope Overflow

If total estimated tokens exceed 2,000,000 (would produce 7+ phases): flag as `NEEDS_HUMAN` with message "Spec is unusually large ({N} tokens). Consider splitting into separate projects." Still produce the phase list but mark confidence as ≤ 70.

If a single mechanism exceeds 325,000 tokens: it cannot fit in one phase. Flag as `NEEDS_HUMAN` with message "Mechanism {id} exceeds single-phase budget. It must be decomposed before phase sequencing."

## Confidence Scoring

Score each dimension 0–20 after producing output:

1. **Completeness** (0–20): All mechanisms assigned to exactly one phase? All phases have 3-tier sandboxes, build orders with rationales, explicit dependencies?
2. **Accuracy** (0–20): Token estimates realistic for the tech stack? Mechanism groupings respect dependency order? File paths match Stage 0 conventions?
3. **Consistency** (0–20): Phase dependencies match mechanism dependencies? File sandboxes don't overlap (same file in "allowed" for two phases)? Build orders reference only sandbox files?
4. **Specificity** (0–20): File paths are exact (not "some auth file")? Token estimates are numbers? Build order rationales are concrete (not "needed later")?
5. **Handoff Readiness** (0–20): Could Stage 8 inject pulse checks after each build order entry? Are sandbox lists precise enough for `git diff` verification? Are phase boundaries unambiguous?

**Total = sum of all 5 (/100)**

- **≥ 90**: PASS — proceed to Stage 8.
- **70–89**: WARN — flag low dimensions in metadata, proceed with warning. Retry once if no human available.
- **< 70**: FAIL — trigger escape hatch. Do NOT write output forward.

## Escape Hatch

**Trigger when:**
- Required input fields missing and cannot be inferred (no mechanism list)
- Total spec tokens cannot be estimated (Stages 3–6 output is empty)
- A mechanism has no file mapping and cannot be inferred
- Mechanism dependencies form a cycle preventing clean phase split
- Confidence score < 70 after one retry
- Single mechanism exceeds 325,000 tokens

**Save:**
- Partial `stage_7` with whatever phases were successfully created
- Step number where halt occurred
- Which mechanisms were assigned vs. unassigned
- Token budget calculation (even if incomplete)
- Suggested questions for the human

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{
    "stage": 7,
    "step": "Step N description",
    "reason": "Specific problem",
    "mechanisms_assigned": ["M1", "M2"],
    "mechanisms_unassigned": ["M5"],
    "suggested_actions": ["Decompose mechanism M5", "Clarify file mapping for M5"]
  }]
}
```

## Example

**Input:** A task management app with 4 mechanisms (Auth, Tasks CRUD, Dashboard, Notifications) totaling ~580,000 estimated tokens.

**Token math:**
```
total_spec_tokens = 580,000
phases_needed = ceil(580,000 / 325,000) = 2
```

**Phase split** (at mechanism boundary between Tasks CRUD and Dashboard):

Phase 1 — "Auth & Task Engine" (estimated_content_tokens: ~290K, estimated_total_tokens: ~315K):
- mechanisms_included: M1 (Auth, ~120K), M2 (Tasks CRUD, ~170K)
- build_order: `src/lib/auth.ts` → `src/lib/tasks.ts` → `src/contexts/AuthContext.tsx` → `src/contexts/TaskContext.tsx` → `src/pages/SignIn.tsx` → `src/pages/TaskList.tsx` → `src/pages/TaskDetail.tsx` → modify `src/App.tsx`
- file_sandbox.allowed: all 8 files above
- file_sandbox.read_only: `CLAUDE.md`, `package.json`, `tsconfig.json`
- file_sandbox.forbidden: `.env`, `src/pages/Dashboard.tsx`, `src/lib/notifications.ts`

Phase 2 — "Dashboard & Notifications" (estimated_content_tokens: ~290K, estimated_total_tokens: ~315K):
- mechanisms_included: M3 (Dashboard, ~160K), M4 (Notifications, ~130K)
- build_order: `src/lib/dashboard.ts` → `src/lib/notifications.ts` → `src/contexts/NotificationContext.tsx` → `src/pages/Dashboard.tsx` → `src/pages/NotificationSettings.tsx` → modify `src/App.tsx`
- file_sandbox.allowed: all 6 files above
- file_sandbox.read_only: `src/lib/auth.ts`, `src/lib/tasks.ts`, `src/contexts/AuthContext.tsx`, `CLAUDE.md`
- file_sandbox.forbidden: `.env`, Phase 1's UI files
- depends_on: [1]

**Verification:** 290K + 25K = 315K ≤ 350K for both phases. All 4 mechanisms assigned (no_mechanism_split: true). DAG is valid (2→1). token_math_verified: true. Confidence: 94/100.


---
## REFERENCE: build-order-patterns

# Build Order Patterns — Phase Sequencing Reference

## Martin's Pattern: The Four Layers

Every phase follows the same forced linear sequence. This is derived from Martin's structural checklist and ensures predictable, auditable builds.

```
Layer 1: CORE LOGIC      — Business logic, utilities, helpers, types, database schemas
Layer 2: STATE MANAGEMENT — Contexts, stores, hooks, data fetching, API clients
Layer 3: UI COMPONENTS    — Pages, components, forms, modals, layouts
Layer 4: INTEGRATION      — Route wiring, exports, entry points, app configuration
```

## Why This Order

- **Core logic first**: Everything downstream depends on the types, utilities, and business rules defined here. Building UI before logic forces the agent to make assumptions that it later has to fix.
- **State second**: State management wraps core logic and exposes it to UI. Without it, UI components can't access data.
- **UI third**: With logic and state in place, UI components are straightforward — they consume hooks and call functions. No guessing.
- **Integration last**: Wiring routes and exports is the final step that connects everything. Doing it earlier means wiring to components that don't exist yet.

## Concrete Examples By Tech Stack

### React + TypeScript

```
1. src/lib/auth.ts              (core logic — auth functions)
2. src/lib/validators.ts        (core logic — validation rules)
3. src/types/user.ts            (core logic — type definitions)
4. src/contexts/AuthContext.tsx  (state — wraps auth logic)
5. src/hooks/useAuth.ts         (state — hook for consuming auth)
6. src/pages/SignIn.tsx          (UI — sign-in page)
7. src/pages/SignUp.tsx          (UI — sign-up page)
8. src/components/AuthGuard.tsx  (UI — route protection component)
9. src/App.tsx                   (integration — add routes)
```

### Next.js + TypeScript

```
1. src/lib/db.ts                (core logic — database client)
2. src/lib/auth.ts              (core logic — auth utilities)
3. src/types/index.ts           (core logic — type definitions)
4. src/app/api/auth/route.ts    (state/API — auth API route)
5. src/hooks/useAuth.ts         (state — client-side auth hook)
6. src/app/sign-in/page.tsx     (UI — sign-in page)
7. src/app/sign-up/page.tsx     (UI — sign-up page)
8. src/middleware.ts             (integration — route protection)
9. src/app/layout.tsx            (integration — layout wrapper)
```

### Python + FastAPI

```
1. src/models/user.py           (core logic — data models)
2. src/services/auth_service.py (core logic — business logic)
3. src/schemas/user.py          (core logic — Pydantic schemas)
4. src/dependencies/auth.py     (state — dependency injection)
5. src/routers/auth.py          (UI/API — route handlers)
6. src/main.py                  (integration — register router)
```

### Flutter + Dart

```
1. lib/models/user.dart         (core logic — data models)
2. lib/services/auth_service.dart (core logic — business logic)
3. lib/providers/auth_provider.dart (state — state management)
4. lib/screens/sign_in_screen.dart  (UI — sign-in screen)
5. lib/screens/sign_up_screen.dart  (UI — sign-up screen)
6. lib/app.dart                     (integration — route registration)
```

## Build Order Entry Format

Each entry in the `build_order` array MUST have:

```json
{
  "file_path": "src/lib/auth.ts",
  "operation": "create",
  "rationale": "Core auth logic — session management, token validation. All auth UI and state depend on this."
}
```

### Operation Values

| Value | When to Use |
|-------|-------------|
| `create` | File does not exist, phase creates it from scratch |
| `modify` | File exists (from a prior phase or boilerplate), phase adds to or changes it |

### Rationale Guidelines

Good rationales explain WHY this file is at this position:
- "Core auth logic — all auth UI depends on these functions"
- "State wrapper — must exist before any component can consume auth"
- "Page component — consumes AuthContext, must come after state layer"
- "Route wiring — final integration step, all pages must exist first"

Bad rationales (too vague — avoid these):
- "Needed for the app"
- "Important file"
- "Should come first"
- "Related to auth"

## Cross-Phase Patterns

When a file is MODIFIED across phases (e.g., `App.tsx` gets new routes in each phase):

- Phase 1: `{ "file_path": "src/App.tsx", "operation": "create", "rationale": "Initial app shell with auth routes" }`
- Phase 2: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add dashboard routes — auth routes already wired" }`
- Phase 3: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add settings routes — all prior routes stable" }`

The file appears in `files_allowed` for ALL phases that touch it, but only Phase 1 has `"create"`. Subsequent phases use `"modify"` and their rationale references what was already done.


---
## REFERENCE: file-sandbox-template

# File Sandbox Template — Phase Sequencing Reference

## The Three Tiers

Every phase MUST have all three tiers defined. No exceptions.

### Tier 1: FILES ALLOWED

Exact file paths this phase can create or modify. Be explicit — list every file path with its operation status.

```
files_allowed:
  - src/lib/auth.ts              (NEW — create from scratch)
  - src/contexts/AuthContext.tsx  (NEW — create from scratch)
  - src/pages/SignIn.tsx          (NEW — create from scratch)
  - src/pages/SignUp.tsx          (NEW — create from scratch)
  - src/App.tsx                   (MODIFY — add routes only)
  - supabase/migrations/00001_auth.sql (NEW — create migration)
```

**Rules:**
- Every file in `build_order` MUST appear here
- Mark each as NEW (create) or MODIFY (change existing)
- MODIFY files should specify WHAT is allowed (e.g., "add routes only", "add export")
- Keep the list precise — "src/components/*" is NOT acceptable, list each file

### Tier 2: FILES READ-ONLY

Files the phase can reference for patterns but MUST NOT modify. These are typically files from prior phases or global config.

```
files_read_only:
  - CLAUDE.md                     (global — always read-only)
  - package.json                  (reference for dependencies)
  - tsconfig.json                 (reference for paths)
  - src/lib/supabase.ts           (reference for DB pattern)
  - src/components/ui/Button.tsx  (reference for component pattern)
```

**Rules:**
- Always include CLAUDE.md
- Include files from prior phases that this phase needs to reference
- Include configuration files the agent might need to check
- A file can be READ-ONLY in one phase and ALLOWED in another (the phase that creates it has ALLOWED, subsequent phases have READ-ONLY)

### Tier 3: FILES FORBIDDEN

Everything not in ALLOWED or READ-ONLY. For critical files, list them explicitly even though "everything else" covers them.

```
files_forbidden:
  - .env                          (NEVER — contains secrets)
  - .env.local                    (NEVER — contains secrets)
  - supabase/migrations/00000_*.sql (existing migrations — never modify)
  - src/lib/credits.ts            (owned by Phase 2 — do not touch)
  - src/pages/Dashboard.tsx       (owned by Phase 2 — do not touch)
  - ANY files in node_modules/
  - ANY files in .git/
```

**Rules:**
- Explicitly list `.env` and `.env.local` (critical, never touch)
- Explicitly list existing migration files
- Explicitly list files owned by other phases
- Include `node_modules/` and `.git/`
- Use "ANY files not listed above" as the catch-all at the end

## DO NOT CHANGE Protections

Some files must NEVER be modified by ANY phase. These appear in every phase's `do_not_change` array AND in every phase's `files_forbidden`:

```
do_not_change (global):
  - CLAUDE.md
  - .env
  - .env.local
  - BUILD_RULES.md
  - package-lock.json (modify only via npm install, not directly)
  - Any existing migration files (those with numbers lower than this phase's migrations)
```

## Enforcement Model

The sandbox is an **alarm system, not a fence**. The agent CAN touch any file during the build. After it finishes:

1. `git diff --name-only $SNAPSHOT` captures every file created, modified, or deleted
2. The diff is compared against the phase's `files_allowed` list
3. Unauthorized changes trigger violation handling:
   - **LOW**: Touched shared types/config → log and proceed
   - **MEDIUM**: Modified another phase's file → review and decide (additive = proceed with caution, destructive = revert)
   - **HIGH**: Modified `.env`, deleted files, touched forbidden core → halt and revert

## Complete Phase Sandbox Example

```json
{
  "phase_number": 2,
  "name": "Dashboard & Analytics",
  "files_allowed": [
    "src/lib/dashboard.ts",
    "src/lib/analytics.ts",
    "src/contexts/DashboardContext.tsx",
    "src/pages/Dashboard.tsx",
    "src/pages/Analytics.tsx",
    "src/components/charts/BarChart.tsx",
    "src/components/charts/LineChart.tsx",
    "src/App.tsx"
  ],
  "files_read_only": [
    "CLAUDE.md",
    "package.json",
    "tsconfig.json",
    "src/lib/auth.ts",
    "src/contexts/AuthContext.tsx",
    "src/lib/supabase.ts"
  ],
  "files_forbidden": [
    ".env",
    ".env.local",
    "supabase/migrations/00001_auth.sql",
    "src/pages/SignIn.tsx",
    "src/pages/SignUp.tsx",
    "src/contexts/AuthContext.tsx",
    "node_modules/**",
    ".git/**"
  ],
  "do_not_change": [
    "CLAUDE.md",
    ".env",
    ".env.local",
    "BUILD_RULES.md"
  ]
}
```


---
## REFERENCE: token-budget-math

# Token Budget Math — Phase Sequencing Reference

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| Total context window | 1,000,000 tokens | Claude 1M context |
| Total budget for spec content | 500,000 tokens | 50% of context — other 50% is agent working memory, tools, system prompts |
| Overhead per phase | 25,000 tokens | Fixed templated content (see breakdown below) |
| Content budget per phase | 325,000 tokens | 350,000 target minus 25,000 overhead |
| Target per phase (total) | 350,000 tokens | 35% of context — significant headroom below the 50% ceiling |

## Overhead Breakdown (Per Phase)

| Component | Tokens | Purpose |
|-----------|--------|---------|
| Build rules preamble | ~8,000 | Martin's structural rules, DO NOT CHANGE protections |
| File sandbox declaration | ~2,000 | ALLOWED / READ-ONLY / FORBIDDEN lists |
| Build order with pulse points | ~3,000 | Forced linear sequence with pulse check markers |
| Seam check definitions | ~2,000 | Connection-point verification rules |
| Full checkpoint at end | ~5,000 | End-of-phase pattern + functional verification |
| Pattern verification prompt | ~3,000 | Instructions for verifying build patterns |
| Violation handling | ~2,000 | Severity rules and escalation protocol |
| **Total** | **~25,000** | |

This overhead is predictable because it is templated. The preamble is the same text every time (with project-specific file lists swapped in). This allows advance calculation — account for overhead BEFORE splitting, not after.

## Phase Count Formula

```
phases_needed = ceil(total_spec_tokens / budget_per_phase_content)
             = ceil(total_spec_tokens / 325,000)
```

## Token Estimation Heuristics

### Per-Mechanism Estimates

| Complexity | Characteristics | Token Range |
|------------|----------------|-------------|
| Simple | 1–2 files, WALL-dominant, single concern | 15,000–25,000 |
| Medium | 3–5 files, mixed W/D/R, 2–3 connected components | 30,000–60,000 |
| Complex | 6+ files, DOOR/ROOM-heavy, integrations, multi-page | 60,000–120,000 |

### Per-Page UI Estimates (from Stage 6b)

| Page Type | Token Range |
|-----------|-------------|
| Simple static page (about, settings) | 5,000–8,000 |
| Form page (sign in, create item) | 8,000–12,000 |
| Dashboard / data-heavy page | 12,000–20,000 |
| Complex interactive page (editor, kanban) | 20,000–40,000 |

### Additional Content Estimates

| Content Type | Token Range |
|-------------|-------------|
| Database schema / migration | 3,000–8,000 per table |
| API route / endpoint | 5,000–10,000 per route |
| Shared utility / helper library | 3,000–6,000 per file |
| Type definitions | 2,000–5,000 per domain area |

## Worked Examples

### Example 1: Small App (1 Phase)

```
Mechanisms:
  M1 Auth (simple):     20,000 tokens
  M2 Profile (simple):  18,000 tokens
  M3 Settings (simple): 15,000 tokens
Total:                  53,000 tokens

phases_needed = ceil(53,000 / 325,000) = 1

Phase 1: 53,000 content + 25,000 overhead = 78,000 total
78,000 ≤ 350,000 ✓
```

### Example 2: Medium App (2 Phases)

```
Mechanisms:
  M1 Auth (medium):         45,000 tokens
  M2 Tasks CRUD (complex):  90,000 tokens
  M3 Dashboard (complex):   80,000 tokens
  M4 Notifications (medium):50,000 tokens
  M5 Search (medium):       40,000 tokens
  M6 Settings (simple):     20,000 tokens
Total:                     325,000 tokens

phases_needed = ceil(325,000 / 325,000) = 1

But check fit: 325,000 + 25,000 = 350,000 ≤ 350,000 ✓ (exactly at limit)
Keep as 1 phase, OR split to 2 for safety margin.

If split to 2:
  Phase 1 (M1+M2+M3): 215,000 + 25,000 = 240,000 ≤ 350,000 ✓
  Phase 2 (M4+M5+M6): 110,000 + 25,000 = 135,000 ≤ 350,000 ✓
```

### Example 3: Large App (3 Phases)

```
Mechanisms:
  M1 Auth (complex):           100,000 tokens
  M2 Payments (complex):       110,000 tokens
  M3 Content Editor (complex): 120,000 tokens
  M4 Analytics (complex):       95,000 tokens
  M5 Social (medium):           60,000 tokens
  M6 Admin Panel (complex):     80,000 tokens
  M7 Notifications (medium):    45,000 tokens
  M8 Search (medium):           40,000 tokens
Total:                         650,000 tokens

phases_needed = ceil(650,000 / 325,000) = 2

Check fit with 2 phases:
  Best split: M1+M2+M3 = 330,000 → 330,000 + 25,000 = 355,000 > 350,000 ✗
  Adjusted: M1+M2 = 210,000 → 210,000 + 25,000 = 235,000 ✓
            M3+M4+M5+M6+M7+M8 = 440,000 → 440,000 + 25,000 = 465,000 > 350,000 ✗

Need 3 phases:
  Phase 1 (M1+M2):       210,000 + 25,000 = 235,000 ✓
  Phase 2 (M3+M4):       215,000 + 25,000 = 240,000 ✓
  Phase 3 (M5+M6+M7+M8): 225,000 + 25,000 = 250,000 ✓

All phases ≤ 350,000 ✓
```

## Verification Checklist

After calculating phases:
- [ ] Every phase: `estimated_tokens + 25,000 ≤ 350,000`
- [ ] `sum(all phase estimated_tokens)` ≈ `total_spec_tokens` (±10%)
- [ ] `phases.length` ≈ `ceil(total_spec_tokens / 325,000)` (±1 for boundary adjustments)
- [ ] No mechanism split across phases
- [ ] No mechanism dropped (all mechanism IDs from Stage 4 appear in exactly one phase)

