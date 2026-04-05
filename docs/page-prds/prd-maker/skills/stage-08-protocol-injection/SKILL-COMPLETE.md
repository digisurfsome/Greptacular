---
name: stage-08-protocol-injection
description: Embed pulse/seam/full verification protocols inline into phased build orders from Stage 7.
---

## Purpose

Take phases from Stage 7 (with file sandboxes and build orders) and inject three tiers of verification checkpoints INTO them — pulse checks after every file, seam checks at mechanism connection points, full checkpoints at phase boundaries — producing self-verifying build units with embedded violation handling.

## When to Use

Activate when: `context_packet.stage_7.phases` exists AND `context_packet.stage_5.mechanism_blueprints` exists AND `context_packet.stage_4.mechanism_dependencies` exists. Trigger phrases: "protocol injection", "inject verification", "embed checks", "pulse seam full", "verification protocols", "inject protocols into phases".

Do NOT activate for: phase splitting (Stage 7), verification agent setup (Stage 9), output generation (Stage 10), or any layout/style work (Stage 6).

## Input Format

```json
{
  "stage_0": {
    "tech_stack": {
      "framework": "string",
      "language": "string"
    }
  },
  "stage_7": {
    "phase_count": 0,
    "total_estimated_tokens": 0,
    "phases": [{
      "phase_number": 1,
      "phase_name": "string",
      "mechanisms_included": ["string"],
      "estimated_content_tokens": 0,
      "estimated_total_tokens": 0,
      "build_order": [
        { "file_path": "src/file1.ts", "operation": "create", "rationale": "string" },
        { "file_path": "src/file2.tsx", "operation": "create", "rationale": "string" }
      ],
      "file_sandbox": {
        "allowed": ["string"],
        "read_only": ["string"],
        "forbidden": ["string"]
      },
      "depends_on": [],
      "do_not_change": ["string"]
    }],
    "token_budget": {
      "budget_per_phase_content": 0,
      "overhead_per_phase": 25000,
      "total_budget": 0
    }
  },
  "stage_5": {
    "mechanism_blueprints": [{
      "mechanism_id": "string",
      "steps": [{ "step": "string", "classification": "WALL|DOOR|ROOM" }]
    }]
  },
  "stage_4": {
    "mechanism_dependencies": [{
      "from_id": "string",
      "to_id": "string",
      "relationship": "string"
    }]
  }
}
```

**Note on `stage_0.tech_stack`:** Required for generating tech-stack-specific functional check commands in the full checkpoint (Step 5). For example, `npm run build` for Node/React, `cargo build` for Rust, `python manage.py check` for Django.

**Note on `build_order` format:** Each entry is an object with `file_path`, `operation` ("create" or "modify"), and `rationale` — matching Stage 7's output exactly. When iterating over build_order entries, use `entry.file_path` to get the file path.

**Note on field name mapping from Stage 7:** Stage 7 outputs `phase_name` (not `name`), `mechanisms_included` (not `mechanism_ids`), `estimated_content_tokens` and `estimated_total_tokens` (not `estimated_tokens`), and nests sandbox lists under `file_sandbox.allowed` / `file_sandbox.read_only` / `file_sandbox.forbidden` (not flat `files_allowed` / `files_read_only` / `files_forbidden`). The input format above matches Stage 7's actual output schema. When referencing sandbox lists in process steps, use `phase.file_sandbox.allowed`, `phase.file_sandbox.read_only`, and `phase.file_sandbox.forbidden`.

## Process

### Step 1: Load and Index Phase Data

Read `stage_7.phases`. For each phase, index its `build_order` (array of `{file_path, operation, rationale}` objects), `file_sandbox.allowed` (sandbox allowlist), and `mechanisms_included`. Build a lookup: `mechanism_id → phase_number` so you know which mechanisms live in which phase.

### Step 2: Build Dependency Interface Map

Read `stage_4.mechanism_dependencies`. For each dependency edge `(from_id, to_id)`, check if both mechanisms appear in the SAME phase. If yes, identify which file in the build order is the CONSUMER (imports from the other). That file is a seam check insertion point. Record: `{component_a, component_b, trigger_file}`.

If two connected mechanisms are in DIFFERENT phases, the seam check goes in the LATER phase at the first file that imports from the earlier phase's mechanism.

### Step 3: Insert Pulse Checks (Every File)

For EACH entry in each phase's `build_order`, generate a pulse check using `entry.file_path`:

1. Read the file's name and purpose from context (mechanism blueprints, file sandbox)
2. Generate SPECIFIC checks — not generic. Examples:
   - `auth.ts` → `["file exists", "exports loginUser function", "exports logoutUser function", "no syntax errors"]`
   - `AuthContext.tsx` → `["file exists", "exports AuthProvider component", "exports useAuth hook", "no syntax errors"]`
3. Assign `after_file` = `entry.file_path` from the build_order entry

Use `references/protocol-tier-templates.md` for the check generation patterns. Every file gets a pulse check — no exceptions.

### Step 4: Insert Seam Checks at Connection Points

Using the interface map from Step 2, for each connection point within a phase:

1. Identify `component_a` (provider) and `component_b` (consumer)
2. Generate SPECIFIC verification: `"AuthContext.tsx imports from auth.ts and re-exports auth state"` — not generic `"A imports B"`
3. Place the seam check after the CONSUMER file in the build order (the file that creates the connection)

If a phase has NO mechanism interfaces (single-mechanism phase, no cross-mechanism connections), it gets zero seam checks. This is valid — pulse and full checkpoint still apply.

### Step 5: Define Full Checkpoint at Phase Boundary

For each phase, create a `full_checkpoint` with three parts:

**pattern_checks** — sandbox compliance via git diff:
- `"Run git diff --name-only $PHASE_N_BASELINE to list all modified files"`
- `"Compare modified files against file_sandbox.allowed list"`
- `"Flag any file modified that is NOT in file_sandbox.allowed"`
- `"Flag any file in build_order that was NOT created/modified"`
- `"Flag any unexpected imports from files outside sandbox"`

**functional_checks** — runtime verification (tech-stack-specific):
- Read `stage_0.tech_stack` to determine commands (e.g., `"npm run build"`, `"cargo build"`)
- Add phase-specific checks: `"Navigate to /sign-in route"`, `"Verify dashboard page renders"`
- Always include: compile check, new features render, existing features still work

**Regression checks (for Phase N where N > 1):** When the phase is not the first phase, add explicit regression verification steps that confirm features from ALL earlier phases still work. For example, if Phase 1 built auth routes (/sign-in, /sign-up) and Phase 2 builds a dashboard, Phase 2's functional_checks MUST include: `"Navigate to /sign-in — still renders (Phase 1 regression)"` and `"Navigate to /sign-up — still renders (Phase 1 regression)"`. This ensures each phase boundary catches regressions immediately, not at the end of the entire build. The regression checks should be listed after the new-feature checks and labeled with which phase they verify.

**gate_condition** — binary pass/fail:
- `"ALL pattern_verification checks pass (zero unauthorized file modifications) AND ALL functional_checks pass (app compiles, new pages render, prior-phase features still work). If ANY check fails, fix before Phase N+1 starts."`

### Step 6: Embed Violation Rules Per Phase

For each phase, populate the 4-level violation tree using `references/violation-decision-tree.md`. Customize triggers to the phase's specific sandbox:

- **low**: `triggers` reference that phase's shared files. `response`: `"log_and_proceed"`
- **medium**: `triggers` reference files from other phases' `file_sandbox.allowed`. `response`: `"review_and_decide"`. Include `decision_tree`: `{"additive": "proceed_with_caution", "destructive": "revert_file", "unclear": "flag_human"}`
- **high**: `triggers`: file deletion, core config changes outside scope. `response`: `"revert_entire_phase"`
- **critical**: `triggers`: `.env`, `CLAUDE.md`, `package.json scripts`, build config, CI/CD. `response`: `"full_stop"`

### Step 7: Calculate Overhead and Validate Budget

For each phase, calculate `overhead_tokens` by summing the 7 overhead components (see `references/overhead-budget-breakdown.md`). Standard total: ~25,000 tokens.

**Validation checks:**
1. Every phase from Stage 7 has a corresponding `instrumented_phases` entry
2. Every file in every build_order has a `pulse_points` entry (matched by `after_file`)
3. Seam checks exist at every mechanism interface point within each phase
4. Every phase has `full_checkpoint` with both `pattern_verification` and `functional_checks`
5. `violation_handling` has all four severity levels (low, medium, high, critical) for every phase
6. `overhead_tokens` ≤ 30,000 per phase
7. `estimated_total_tokens` (Stage 7) + `overhead_tokens` ≤ 350,000 per phase
8. For phases where `phase_number > 1`, `functional_checks` includes regression verification for all prior phases' features
9. `total_overhead_tokens` equals sum of all phases' `overhead_tokens`
10. `budget_verified` is `true` only if check #7 passes for ALL phases

If overhead exceeds 30,000 for any phase, trim verbose descriptions. If total exceeds 350,000, signal back to Stage 7 for re-splitting.

## Output Format

```json
{
  "stage_8": {
    "instrumented_phases": [
      {
        "phase_number": 1,
        "pulse_points": [
          {
            "after_file": "src/lib/auth.ts",
            "checks": ["file exists", "exports loginUser", "exports logoutUser", "no syntax errors"]
          }
        ],
        "seam_checks": [
          {
            "location": "after src/contexts/AuthContext.tsx",
            "checks": ["AuthContext imports loginUser and logoutUser from auth.ts"]
          }
        ],
        "full_checkpoint": {
          "pattern_verification": ["git diff --name-only against file_sandbox.allowed", "flag unauthorized modifications", "flag incomplete build_order items"],
          "functional_checks": ["npm run build succeeds", "navigate to /sign-in renders login form"],
          "gate_condition": "ALL pattern_verification pass AND ALL functional_checks pass. Fix before next phase."
        },
        "violation_handling": {
          "low": {
            "triggers": ["touched shared types file", "added import to existing utility"],
            "response": "log_and_proceed"
          },
          "medium": {
            "triggers": ["modified file from another phase's file_sandbox.allowed"],
            "response": "review_and_decide",
            "decision_tree": {
              "additive": "proceed_with_caution",
              "destructive": "revert_file",
              "unclear": "flag_human"
            }
          },
          "high": {
            "triggers": ["deleted files", "modified core config outside scope"],
            "response": "revert_entire_phase"
          },
          "critical": {
            "triggers": ["modified .env", "modified CLAUDE.md", "modified build config"],
            "response": "full_stop"
          }
        },
        "overhead_tokens": 25000
      }
    ],
    "total_overhead_tokens": 25000,
    "budget_verified": true,
    "overhead_breakdown": {
      "build_rules_preamble": 8000,
      "file_sandbox_declaration": 2000,
      "build_order_with_pulse": 3000,
      "seam_check_definitions": 2000,
      "full_checkpoint": 5000,
      "pattern_verification": 3000,
      "violation_handling": 2000
    }
  },
  "metadata": {
    "current_stage": 8,
    "confidence_scores": {
      "8": { "score": 0, "dimensions": {}, "gate_result": "pass|flag|fail" }
    },
    "stage_timestamps": { "8": "ISO-8601" }
  }
}
```

**Output field mapping to stage-contracts.md:**
- `instrumented_phases` (not `protocol_injected_phases`) — matches contract terminology
- `pulse_points[].after_file` (not `pulse_checks[].file_path`) — clarifies placement semantics
- `full_checkpoint.pattern_verification` (not `pattern_checks`) — matches contract field name
- `violation_handling` (not `violation_rules`) — matches contract field name
- `total_overhead_tokens` — sum of all phases' `overhead_tokens`, required by contract
- `budget_verified` — boolean confirming all phases fit within token budget after injection

## Edge Cases

### Missing Input

- No `stage_7.phases` → Escape hatch. Cannot inject protocols without phases.
- No `stage_4.mechanism_dependencies` → Proceed with zero seam checks per phase. Pulse and full checkpoint still apply. Log: `"No mechanism dependencies — seam checks skipped."`
- Empty `build_order` in a phase → Escape hatch for that phase. Cannot inject pulse checks into empty build order.

### Ambiguous Input

- Mechanism dependency exists but neither file is in the current phase's build_order → Skip this seam check for this phase. The seam belongs to whichever phase contains the consumer file.
- File appears in build_order but has no clear purpose from mechanism blueprints → Generate minimal pulse check: `["file exists", "no syntax errors"]`. Flag as `"generic_pulse"` in metadata.

### Scope Overflow

- If protocol injection reveals that a phase needs files not in its sandbox (e.g., seam check requires reading a file from another phase) → Do NOT modify the sandbox. Note it as a read dependency. Stage 7 already handles `files_read_only`.
- If overhead exceeds 30,000 tokens → Trim check descriptions to single-line commands. If still over, flag for Stage 7 re-split.

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): Every file has a pulse check? Every mechanism interface has a seam check? Every phase has full_checkpoint with pattern + functional checks? All 4 violation severity levels defined per phase?

2. **Accuracy** (0-20): Seam checks placed at actual mechanism interfaces (not arbitrary)? Functional checks match the tech stack (`npm run build` for Node, `cargo build` for Rust)? Violation triggers are realistic and specific to each phase's sandbox?

3. **Consistency** (0-20): Protocol-injected phases match Stage 7 phases exactly (same numbers, same files)? Seam check connection points align with Stage 4 dependency graph? Violation severity classification is uniform across all phases?

4. **Specificity** (0-20): Pulse checks verify specific exports per file (not generic "file works")? Seam checks name exact import relationships? Functional checks are executable commands? Gate conditions are binary pass/fail?

5. **Handoff Readiness** (0-20): Could Stage 9 configure a verifier agent from these protocols alone? Every check, threshold, and rollback action is explicit? No interpretation needed?

**Total = sum (/100).** ≥90: PASS. 70-89: WARN (flag, proceed). <70: FAIL (escape hatch).

## Escape Hatch

**When to trigger:**
- Required fields missing (no phases from Stage 7, no mechanism data from Stage 4)
- Phase build_order has zero files
- Mechanism dependencies are circular or unresolvable
- Overhead exceeds 30,000 tokens after trimming
- Confidence score < 70 after one retry

**What to save:**
- Current context_packet with whatever phases were successfully injected
- Stage number (8) and step where halt occurred
- Which phases were injected vs which failed
- Overhead calculations per phase
- Suggested human questions (e.g., "Phase 3 has no mechanism interfaces — confirm zero seam checks?")

**How to signal:**
- Set `metadata.status = "needs_human"`
- Add entry to `metadata.escape_hatches[]`: `{"stage": 8, "step": "string", "reason": "string", "suggested_actions": ["string"]}`
- Save context_packet snapshot
- Output structured `NEEDS_HUMAN` message

## Example

**Input:** Phase 1 "Auth System" with build_order: `[auth.ts, AuthContext.tsx, SignIn.tsx, SignUp.tsx, App.tsx(routes)]`. Mechanisms: `auth_core` depends on nothing. `auth_ui` depends on `auth_core`. Both in Phase 1.

**Protocol-injected output (inline):**

```
Phase 1: Auth System
├── BUILD ORDER with embedded protocols:
│   1. Create src/lib/auth.ts
│      └─ PULSE: [file exists, exports loginUser, exports logoutUser, no syntax errors]
│   2. Create src/contexts/AuthContext.tsx
│      └─ PULSE: [file exists, exports AuthProvider, exports useAuth hook, no syntax errors]
│   3. Create src/pages/SignIn.tsx
│      └─ PULSE: [file exists, exports SignIn component, no syntax errors]
│      └─ SEAM: SignIn.tsx imports useAuth from AuthContext ← AuthContext imports from auth.ts
│   4. Create src/pages/SignUp.tsx
│      └─ PULSE: [file exists, exports SignUp component, no syntax errors]
│   5. Wire routes in App.tsx
│      └─ PULSE: [file exists, routes array includes /sign-in and /sign-up, no syntax errors]
│      └─ SEAM: App.tsx routes point to SignIn and SignUp page components
│
├── FULL CHECKPOINT (gate):
│   ├─ Pattern: git diff --name-only vs file_sandbox.allowed; flag unauthorized changes
│   ├─ Functional: npm run build succeeds; /sign-in renders; /sign-up renders
│   └─ Gate: ALL pass → proceed to Phase 2. ANY fail → fix first.
│
└── VIOLATION RULES:
    ├─ LOW: touched shared types → log, proceed
    ├─ MEDIUM: modified another phase's file → review (additive: proceed / destructive: revert)
    ├─ HIGH: deleted files or changed core config → revert entire phase
    └─ CRITICAL: modified .env, CLAUDE.md, build config → FULL STOP
```

Overhead: ~25,000 tokens. Phase estimated_tokens (Stage 7): 80,000. Total: 105,000 ≤ 350,000. ✅


---
## REFERENCE: overhead-budget-breakdown

# Overhead Budget Breakdown

## Standard Per-Phase Overhead (~25,000 tokens)

Every protocol-injected phase adds a fixed overhead on top of Stage 7's `estimated_tokens`. This overhead is predictable because it uses standardized templates.

| Component | Token Estimate | What It Contains |
|-----------|---------------|------------------|
| Build rules preamble | ~8,000 | Martin's structural rules applicable to this phase. Sourced from the agnostic checklist. Includes banned patterns, file naming conventions, component structure rules, state management rules. |
| File sandbox declaration | ~2,000 | `files_allowed`, `files_read_only`, `files_forbidden` lists with explanations. Includes "DO NOT MODIFY" warnings for protected files. |
| Build order with pulse points | ~3,000 | The ordered file list with pulse check definitions after each entry. More files = more tokens, but pulse checks are concise (~50 tokens each). |
| Seam check definitions | ~2,000 | Connection-point verification instructions. Typically 2-5 seam checks per phase at ~200-400 tokens each. Phases with no interfaces: ~200 tokens (just the "no seam checks needed" note). |
| Full checkpoint | ~5,000 | Pattern verification instructions (~2,000), functional check commands (~1,500), gate condition (~500), checkpoint summary format (~1,000). |
| Pattern verification prompt | ~3,000 | Instructions for the git diff process: how to run it, how to compare, how to interpret results, what to report. |
| Violation handling | ~2,000 | The 4-level decision tree with triggers and responses customized to this phase's sandbox. |
| **TOTAL** | **~25,000** | |

## Budget Validation Rules

1. **Per-phase overhead MUST be ≤ 30,000 tokens.** If it exceeds this after injection, trim verbose descriptions. Checks should be single-line commands, not paragraphs.

2. **Per-phase total MUST be ≤ 350,000 tokens.** Formula: `stage_7.phases[].estimated_tokens + overhead_tokens ≤ 350,000`. This leaves room for the Claude context window overhead (system prompt, tools, etc.).

3. **If overhead exceeds 30,000**, apply these trims in order:
   - Reduce build rules preamble to only the rules relevant to this phase's mechanisms (can drop to ~4,000)
   - Condense pulse checks to single-line format: `"PULSE: auth.ts → [exists, exports loginUser/logoutUser]"`
   - Merge similar seam checks
   - If still over: flag for Stage 7 to re-split the phase

4. **If total exceeds 350,000**, signal back to Stage 7 that this phase has too much content and needs to be split into sub-phases.

## Overhead Variation by Phase Size

| Phase Size (files) | Typical Pulse Overhead | Typical Seam Overhead | Total Overhead Range |
|--------------------|-----------------------|----------------------|---------------------|
| 2-5 files | ~500 tokens | ~400 tokens | 22,000 - 24,000 |
| 6-10 files | ~1,000 tokens | ~800 tokens | 24,000 - 26,000 |
| 11-15 files | ~1,500 tokens | ~1,200 tokens | 26,000 - 28,000 |
| 16+ files | ~2,000+ tokens | ~1,600+ tokens | 28,000 - 30,000 |

Phases with 16+ files are rare (Stage 7 typically caps at ~12 files per phase). If you see one, it's likely a candidate for splitting.

## Recording the Breakdown

The `overhead_breakdown` object in the output is a TEMPLATE — it records the standard budget allocation, not the per-phase actual. Per-phase actuals are in each phase's `overhead_tokens` field.

```json
{
  "overhead_breakdown": {
    "build_rules_preamble": 8000,
    "file_sandbox_declaration": 2000,
    "build_order_with_pulse": 3000,
    "seam_check_definitions": 2000,
    "full_checkpoint": 5000,
    "pattern_verification": 3000,
    "violation_handling": 2000
  }
}
```

This is the same for every run. Individual phase `overhead_tokens` may vary slightly based on file count and seam check count.


---
## REFERENCE: protocol-tier-templates

# Protocol Tier Templates

## Pulse Check Template (Per-File)

Generate after EVERY file in the build_order. Checks must be SPECIFIC to the file.

### Pattern: Determine checks from file type and purpose

| File Type | Standard Checks | Additional Checks |
|-----------|----------------|-------------------|
| Library/utility (`.ts`, `.py`) | file exists, no syntax errors | exports expected functions by name |
| React component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports named component, accepts expected props |
| Context/Provider (`.tsx`) | file exists, no syntax errors | exports Provider component, exports custom hook |
| Page component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports default/named page component |
| Route config (`App.tsx`, `router.ts`) | file exists, no syntax errors | route paths defined, routes point to imports |
| API route (`/api/*.ts`) | file exists, no syntax errors | exports handler function, correct HTTP method |
| Schema/model (`.prisma`, `.sql`) | file exists, no syntax errors | defines expected tables/models |
| Config file (`.config.ts`) | file exists, no syntax errors | exports config object |
| Style file (`.css`, `.scss`) | file exists | defines expected classes/tokens |
| Test file (`.test.ts`) | file exists, no syntax errors | imports subject under test, has test cases |

### Deriving "Expected Functions/Components"

Read the mechanism blueprint (`stage_5.mechanism_blueprints`) for the mechanism this file serves. Each WALL step = a deterministic function. Each DOOR step = a constrained AI function. Each ROOM step = a creative component. The exports should map to these steps.

Example: Mechanism "auth_core" has steps:
- WALL: "Hash password" → expect `hashPassword` export
- WALL: "Verify password" → expect `verifyPassword` export
- DOOR: "Validate email format" → expect `validateEmail` export

Pulse check for `auth.ts`: `["file exists", "exports hashPassword", "exports verifyPassword", "exports validateEmail", "no syntax errors"]`

## Seam Check Template (At Connection Points)

Place ONLY where two mechanisms interface. Derive placement from `stage_4.mechanism_dependencies`.

### Pattern: Identify the connection

1. Find the dependency edge: `from_id → to_id` (from provides, to consumes)
2. Find which file in the build_order belongs to the consumer mechanism
3. The seam check goes AFTER that consumer file

### Verification content

The verification string must name BOTH sides and the specific connection:

- Import check: `"[Consumer] imports [specific function/component] from [Provider]"`
- Data flow: `"[Consumer] passes [specific data] received from [Provider]"`
- Route wiring: `"Route [path] points to [PageComponent] which imports [required context]"`

### When NO seam checks apply

A phase with a single mechanism and no cross-mechanism dependencies within it gets zero seam checks. This is correct — not an error. Pulse checks and the full checkpoint still provide coverage.

## Full Checkpoint Template (Phase Boundary Gate)

Always placed at the END of each phase. Three mandatory parts:

### Pattern Checks (git diff verification)

Always include these 5 checks:
1. `"Run git diff --name-only $PHASE_N_BASELINE to list all actually modified files"`
2. `"Compare actual modified files against this phase's files_allowed list"`
3. `"FLAG: any file modified that is NOT in files_allowed"`
4. `"FLAG: any file in build_order that was NOT created or modified"`
5. `"FLAG: any new imports from files outside this phase's sandbox"`

### Functional Checks (runtime verification)

Determine from `stage_0.tech_stack`:

| Stack | Compile Check | Test Check | Render Check |
|-------|--------------|------------|--------------|
| Node/React | `npm run build` | `npm run test` (if tests exist) | Navigate to new routes |
| Python/Django | `python manage.py check` | `python manage.py test` | Hit new endpoints |
| Rust | `cargo build` | `cargo test` | Run binary with args |
| Flutter | `flutter analyze` | `flutter test` | Launch on emulator |
| Go | `go build ./...` | `go test ./...` | Run binary |

Add phase-specific checks: name the exact pages/routes/features this phase adds.

### Gate Condition

Always this format (customize the specifics):
`"ALL pattern_checks pass (zero unauthorized file modifications) AND ALL functional_checks pass ([compile command] succeeds, [specific pages] render, existing features still work). If ANY check fails, fix before Phase N+1 starts."`

The gate is BINARY: pass or fail. No "proceed with warnings" at the gate level — that's what violation severity handles.


---
## REFERENCE: violation-decision-tree

# Violation Decision Tree

## The Four Severity Levels

Every phase gets all four levels. Triggers are customized per phase based on its `files_allowed` sandbox.

```
VIOLATION DETECTED (via git diff comparison)
│
├─ LOW: Touched shared/common files
│   Triggers:
│   - Modified a shared types file (e.g., types.ts, interfaces.ts)
│   - Added an import to an existing utility file
│   - Added an export to a shared constants file
│   - Modified a shared config that multiple phases reference
│   Response: log_and_proceed
│   Action: Log the modification in the phase report. Note which file
│   was touched and why. Proceed with the build. Review at full checkpoint.
│
├─ MEDIUM: Modified another phase's domain file
│   Triggers:
│   - Modified a file listed in ANOTHER phase's files_allowed
│   - Added a new export to a file owned by another phase
│   - Changed import structure of a file from another phase
│   Response: review_and_decide
│   Decision Tree:
│   ├─ Additive change (added export, added prop, added route):
│   │   → proceed_with_caution — log it, continue, verify at checkpoint
│   ├─ Destructive change (renamed function, changed logic, removed export):
│   │   → revert_file — git checkout that specific file, re-run phase
│   │   with constraint: "Do NOT modify [file]"
│   └─ Unclear (can't determine if additive or destructive):
│       → flag_human — save state, present the diff, ask human to decide
│
├─ HIGH: Deleted files or changed core config outside scope
│   Triggers:
│   - Deleted any file (rm, unlink)
│   - Modified core config files outside this phase's scope
│   - Changed authentication logic outside the auth phase
│   - Modified database schema outside the data-model phase
│   - Changed environment variable definitions
│   Response: revert_entire_phase
│   Action: git reset --hard to phase baseline snapshot. Re-run with
│   tighter constraints or break the phase into smaller sub-phases.
│
└─ CRITICAL: Touched protected files
    Triggers:
    - Modified CLAUDE.md
    - Modified .env or any .env.* file
    - Modified package.json "scripts" section
    - Modified build configuration (vite.config, webpack.config, tsconfig)
    - Modified CI/CD configuration (.github/workflows, Dockerfile)
    - Modified security configuration (auth middleware, CORS settings)
    Response: full_stop
    Action: IMMEDIATELY STOP. Revert ALL changes. Flag for human review.
    This is either a prompt injection attempt or a fundamentally confused
    agent. Do NOT retry automatically. Human must inspect and approve
    before any further work.
```

## Customizing Triggers Per Phase

When embedding the violation tree into a specific phase:

1. **LOW triggers**: List the specific shared files relevant to this phase. Example: Phase 2 (Dashboard) might list `src/types/index.ts` and `src/lib/utils.ts`.

2. **MEDIUM triggers**: List specific files from OTHER phases' sandboxes. Example: If Phase 1 owns `src/lib/auth.ts`, then Phase 2's MEDIUM triggers include `"modified src/lib/auth.ts (owned by Phase 1)"`.

3. **HIGH triggers**: Always include file deletion. Add phase-specific high-severity items (e.g., "changed auth logic" for non-auth phases).

4. **CRITICAL triggers**: These are the same across ALL phases. The protected file list is global.

## Self-Report vs Git Diff

The violation tree is evaluated using TWO inputs:

1. **Agent self-report** (Step 1): Agent lists files it created/modified. This is the FIRST pass.
2. **Git diff** (Step 2): Run `git diff --name-only $BASELINE`. This is GROUND TRUTH.

If the self-report and git diff DO NOT MATCH, that ITSELF is a violation:
- If agent reported MORE files than git shows → probably harmless (agent over-reported), log as LOW
- If git shows MORE files than agent reported → agent touched files it didn't disclose. Treat as MEDIUM minimum, escalate to HIGH if the undisclosed files are from another phase's domain.

