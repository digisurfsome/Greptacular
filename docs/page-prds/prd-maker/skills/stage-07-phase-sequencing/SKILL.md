---
name: stage-07-phase-sequencing
description: Split a complete PRD spec into token-budgeted build phases with file sandboxes, build orders, and dependency mapping.
---

## Purpose

Takes a complete spec (mechanisms scaffolded with Wall/Door/Room classifications, wireframes approved, style selected from Stages 0–6) and splits it into buildable phases using math-based token budget calculations. Each phase becomes a self-contained containment unit with its own file sandbox, forced build order, and explicit dependency mapping. Stage 7 does the structural split; Stage 8 injects enforcement protocols.

## When to Use

Activate when ALL of the following are present in the context packet:
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
    "sub_6a": { "arrangement_type": "...", "wireframe_pattern": "..." },
    "sub_6b": [{ "page_name": "...", "components": [...], "mechanism_connections": [...] }],
    "sub_6c": { "design_tokens": { "colors": {...}, "typography": {...} } }
  },
  "stage_0": { "tech_stack": { "framework": "...", "language": "..." } }
}
```

## Process

### Step 1: Estimate Total Token Count

Aggregate all build content from Stages 3–6. For each mechanism blueprint, estimate tokens based on complexity:
- Simple mechanism (1–2 files, WALL-dominant): ~15,000–25,000 tokens
- Medium mechanism (3–5 files, mixed W/D/R): ~30,000–60,000 tokens
- Complex mechanism (6+ files, DOOR/ROOM-heavy): ~60,000–120,000 tokens

Add per-page UI tokens from Stage 6b (~5,000–15,000 tokens per page depending on component count). Sum all estimates to get `total_spec_tokens`.

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
  "token_budget": {
    "total_spec_tokens": 650000,
    "budget_per_phase_content": 325000,
    "overhead_per_phase": 25000,
    "total_budget": 500000,
    "phases_needed": 2
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Core Auth & Data Layer",
      "mechanism_ids": ["M1", "M2", "M3"],
      "estimated_tokens": 310000,
      "build_order": [
        { "file_path": "src/lib/auth.ts", "operation": "create", "rationale": "Core auth logic — all other files depend on this" },
        { "file_path": "src/contexts/AuthContext.tsx", "operation": "create", "rationale": "State wrapper for auth — needed by UI" },
        { "file_path": "src/pages/SignIn.tsx", "operation": "create", "rationale": "UI consumes AuthContext" },
        { "file_path": "src/App.tsx", "operation": "modify", "rationale": "Wire auth routes — integration last" }
      ],
      "files_allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx", "src/pages/SignIn.tsx", "src/pages/SignUp.tsx", "src/App.tsx"],
      "files_read_only": ["CLAUDE.md", "package.json"],
      "files_forbidden": ["src/lib/supabase.ts", ".env", "supabase/migrations/*"],
      "depends_on": [],
      "do_not_change": ["CLAUDE.md", ".env", "BUILD_RULES.md"]
    }
  ],
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

Phase 1 — "Auth & Task Engine" (~290K content + 25K overhead = 315K):
- Mechanisms: M1 (Auth, ~120K), M2 (Tasks CRUD, ~170K)
- Build order: `src/lib/auth.ts` → `src/lib/tasks.ts` → `src/contexts/AuthContext.tsx` → `src/contexts/TaskContext.tsx` → `src/pages/SignIn.tsx` → `src/pages/TaskList.tsx` → `src/pages/TaskDetail.tsx` → modify `src/App.tsx`
- files_allowed: all 8 files above
- files_read_only: `CLAUDE.md`, `package.json`, `tsconfig.json`
- files_forbidden: `.env`, `src/pages/Dashboard.tsx`, `src/lib/notifications.ts`

Phase 2 — "Dashboard & Notifications" (~290K + 25K = 315K):
- Mechanisms: M3 (Dashboard, ~160K), M4 (Notifications, ~130K)
- Build order: `src/lib/dashboard.ts` → `src/lib/notifications.ts` → `src/contexts/NotificationContext.tsx` → `src/pages/Dashboard.tsx` → `src/pages/NotificationSettings.tsx` → modify `src/App.tsx`
- files_allowed: all 6 files above
- files_read_only: `src/lib/auth.ts`, `src/lib/tasks.ts`, `src/contexts/AuthContext.tsx`, `CLAUDE.md`
- files_forbidden: `.env`, Phase 1's UI files
- depends_on: [1]

**Verification:** 290K + 25K = 315K ≤ 350K ✓ for both phases. All 4 mechanisms assigned. No splits. DAG is valid (2→1). Confidence: 94/100.
