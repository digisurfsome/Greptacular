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
  "stage_7": {
    "phases": [{
      "phase_number": 1,
      "name": "string",
      "mechanism_ids": ["string"],
      "estimated_tokens": 0,
      "build_order": ["src/file1.ts", "src/file2.tsx"],
      "files_allowed": ["string"],
      "files_read_only": ["string"],
      "files_forbidden": ["string"],
      "depends_on": [],
      "do_not_change": ["string"]
    }],
    "token_budget": {
      "total_spec_tokens": 0,
      "budget_per_phase_content": 0,
      "overhead_per_phase": 25000,
      "total_budget": 0,
      "phases_needed": 0
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

## Process

### Step 1: Load and Index Phase Data

Read `stage_7.phases`. For each phase, index its `build_order` (file sequence), `files_allowed` (sandbox), and `mechanism_ids`. Build a lookup: `mechanism_id → phase_number` so you know which mechanisms live in which phase.

### Step 2: Build Dependency Interface Map

Read `stage_4.mechanism_dependencies`. For each dependency edge `(from_id, to_id)`, check if both mechanisms appear in the SAME phase. If yes, identify which file in the build order is the CONSUMER (imports from the other). That file is a seam check insertion point. Record: `{component_a, component_b, trigger_file}`.

If two connected mechanisms are in DIFFERENT phases, the seam check goes in the LATER phase at the first file that imports from the earlier phase's mechanism.

### Step 3: Insert Pulse Checks (Every File)

For EACH file in each phase's `build_order`, generate a pulse check:

1. Read the file's name and purpose from context (mechanism blueprints, file sandbox)
2. Generate SPECIFIC checks — not generic. Examples:
   - `auth.ts` → `["file exists", "exports loginUser function", "exports logoutUser function", "no syntax errors"]`
   - `AuthContext.tsx` → `["file exists", "exports AuthProvider component", "exports useAuth hook", "no syntax errors"]`
3. Assign `file_path` = the file from build_order

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
- `"Compare modified files against files_allowed list"`
- `"Flag any file modified that is NOT in files_allowed"`
- `"Flag any file in build_order that was NOT created/modified"`
- `"Flag any unexpected imports from files outside sandbox"`

**functional_checks** — runtime verification (tech-stack-specific):
- Read `stage_0.tech_stack` to determine commands (e.g., `"npm run build"`, `"cargo build"`)
- Add phase-specific checks: `"Navigate to /sign-in route"`, `"Verify dashboard page renders"`
- Always include: compile check, existing features still work, new features render

**gate_condition** — binary pass/fail:
- `"ALL pattern_checks pass (zero unauthorized file modifications) AND ALL functional_checks pass (app compiles, new pages render, existing routes work). If ANY check fails, fix before next phase."`

### Step 6: Embed Violation Rules Per Phase

For each phase, populate the 4-level violation tree using `references/violation-decision-tree.md`. Customize triggers to the phase's specific sandbox:

- **low**: `triggers` reference that phase's shared files. `response`: `"log_and_proceed"`
- **medium**: `triggers` reference files from other phases' `files_allowed`. `response`: `"review_and_decide"`. Include `decision_tree`: `{"additive": "proceed_with_caution", "destructive": "revert_file", "unclear": "flag_human"}`
- **high**: `triggers`: file deletion, core config changes outside scope. `response`: `"revert_entire_phase"`
- **critical**: `triggers`: `.env`, `CLAUDE.md`, `package.json scripts`, build config, CI/CD. `response`: `"full_stop"`

### Step 7: Calculate Overhead and Validate Budget

For each phase, calculate `overhead_tokens` by summing the 7 overhead components (see `references/overhead-budget-breakdown.md`). Standard total: ~25,000 tokens.

**Validation checks:**
1. Every phase from Stage 7 has a corresponding `protocol_injected_phases` entry
2. Every file in every build_order has a pulse_check
3. Seam checks exist at every mechanism interface point within each phase
4. Every phase has full_checkpoint with both pattern_checks and functional_checks
5. violation_rules has all four severity levels for every phase
6. `overhead_tokens` ≤ 30,000 per phase
7. `estimated_tokens` (Stage 7) + `overhead_tokens` ≤ 350,000 per phase

If overhead exceeds 30,000 for any phase, trim verbose descriptions. If total exceeds 350,000, signal back to Stage 7 for re-splitting.

## Output Format

```json
{
  "stage_8": {
    "protocol_injected_phases": [
      {
        "phase_number": 1,
        "pulse_checks": [
          {
            "file_path": "src/lib/auth.ts",
            "checks": ["file exists", "exports loginUser", "exports logoutUser", "no syntax errors"]
          }
        ],
        "seam_checks": [
          {
            "component_a": "src/lib/auth.ts",
            "component_b": "src/contexts/AuthContext.tsx",
            "verification": "AuthContext imports loginUser and logoutUser from auth.ts"
          }
        ],
        "full_checkpoint": {
          "pattern_checks": ["git diff --name-only against files_allowed", "flag unauthorized modifications", "flag incomplete build_order items"],
          "functional_checks": ["npm run build succeeds", "navigate to /sign-in renders login form"],
          "gate_condition": "ALL pattern_checks pass AND ALL functional_checks pass. Fix before next phase."
        },
        "violation_rules": {
          "low": {
            "triggers": ["touched shared types file", "added import to existing utility"],
            "response": "log_and_proceed"
          },
          "medium": {
            "triggers": ["modified file from another phase's files_allowed"],
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
│   ├─ Pattern: git diff --name-only vs files_allowed; flag unauthorized changes
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
