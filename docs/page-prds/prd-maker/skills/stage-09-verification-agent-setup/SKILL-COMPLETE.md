---
name: stage-09-verification-agent-setup
description: Configure independent verification agent (Agent B) with git-diff rules, two-strike retry, and per-phase checker configs for PRD build phases.
---

## Purpose

Configure an independent verification agent that audits builder output after each phase using git diff as ground truth. Produces both automated (Agent B) and manual (preamble merge) verification paths, the two-strike retry rule, and per-phase checker configs that Stage 10 renders into build scripts.

## When to Use

Activate when the context packet contains completed `stage_8.instrumented_phases`, `stage_7.phases`, and `stage_0.tech_stack`. This skill produces `stage_9.*` — the `verifier_config` wrapper (approach, prompt, inputs, token budget, retry config, persistence flag), `checker_builder_consistency` (Boolean confirming no builder/verifier contradictions), `verification_overhead_total` (total verification tokens across all phases), plus the detailed verification protocol, per-phase checker configs, Agent B config, and manual preamble config.

## Input Format

```json
{
  "stage_8": {
    "instrumented_phases": [
      {
        "phase_number": 1,
        "pulse_points": [...],
        "seam_checks": [...],
        "full_checkpoint": {...},
        "violation_handling": {
          "low": { "response": "log_and_proceed" },
          "medium": { "response": "review_and_decide" },
          "high": { "response": "revert_entire_phase" },
          "critical": { "response": "full_stop" }
        },
        "overhead_tokens": 25000
      }
    ]
  },
  "stage_7": {
    "phases": [
      {
        "phase_number": 1,
        "file_sandbox": {
          "allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx"],
          "read_only": ["package.json"],
          "forbidden": [".env", "CLAUDE.md"]
        },
        "build_order": [...]
      }
    ]
  },
  "stage_0": {
    "tech_stack": {
      "framework": "react",
      "language": "typescript",
      "runtime": "node",
      "database": "supabase",
      "build_command": "npm run build",
      "test_command": "npm run test",
      "lint_command": "npm run lint"
    }
  }
}
```

## Process

### Step 1: Determine Verification Mode

Read `stage_0.tech_stack`. Map to delivery approach:

| Signal | Mode | Rationale |
|--------|------|-----------|
| `tech_stack.runtime` is `node`, `python`, `rust`, `go` AND no explicit `manual_delivery: true` | `automated_agent_b` | CLI-capable stack implies bash automation |
| `tech_stack` contains `manual_delivery: true` OR platform is web-only (Bolt, Lovable, etc.) | `manual_preamble_merge` | No CLI automation available |
| Ambiguous | `automated_agent_b` | Default to automated; manual config is always generated anyway |

**Both configs are always generated regardless of mode.** The `verification_mode` field tells Stage 10 which wrapper to use as PRIMARY.

### Step 2: Build the 4-Step Verification Protocol

Define the universal verification protocol (identical for both modes):

1. **Self-Report** — Agent lists every file created/modified. Compare against `file_sandbox.allowed`.
2. **Diff Check** — Run `git diff PHASE_N_BASELINE..HEAD --name-only`. Compare against BOTH self-report AND `file_sandbox.allowed`. Mismatch between self-report and diff is itself a violation.
3. **Violation Response** — For any file in diff NOT in `file_sandbox.allowed`, apply `stage_8.instrumented_phases[N].violation_handling` decision tree.
4. **Functional Checks** — Run tech-stack-appropriate compile, test, render, and route checks.

Map tech stack to functional check commands using the reference in `references/four-step-verification.md`.

### Step 3: Generate Per-Phase Checker Configs

For each phase in `stage_7.phases`:

1. Copy `file_sandbox.allowed` as the verification baseline
2. Set `baseline_snapshot` to `"git_commit_hash_before_phase_N_starts"`
3. Determine applicable functional checks:
   - Phase 1: compile only (no prior features to regression-test)
   - Phase 2+: compile + test (if tests exist from prior phases)
   - Phases with UI: add render check + route check
4. Define `expected_outcomes` — specific exit codes and observable results
5. Add `overrides` for phase-specific deviations (e.g., Phase 1 skips test check)

Cross-reference each phase's `violation_handling` from Stage 8 to ensure severity levels match.

### Step 4: Configure Agent B (Automated Verifier)

Build the `agent_b_config` object:

- **context_tokens**: ~10,000. Agent B is intentionally lean.
- **clean_context**: `true`. No knowledge of builder's reasoning.
- **persistent_across_phases**: `true`. Accumulates pattern log across the build.
- **receives**: Exactly 4 items: `["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"]`
- **produces**: Single classification per phase: `CLEAN | LOW | MEDIUM | HIGH | CRITICAL`
- **on_high_or_critical**: `"git reset --hard $PHASE_BASELINE && retry_with_fresh_agent_a && apply_two_strike_rule"`

Use the complete Agent B prompt template from `references/agent-b-config-template.md`.

### Step 5: Configure Two-Strike Rule

Set the auto-retry parameters (non-negotiable values):

- `max_retries`: `2` (always 2, not configurable)
- `on_second_failure`: `"stop_for_human_review"`
- `rationale`: `"If 2 fresh agents fail the same phase, the problem is the phase spec, not the agents. Human must intervene."`

Do NOT allow 3+ retries. See `references/two-strike-bash-script.md` for the bash implementation.

### Step 6: Configure Manual Preamble

Build the `manual_preamble_config`:

- Write a concrete preamble template that opens Phase N+1's prompt with Phase N validation
- Set `check_duration_estimate`: `"30 seconds"`
- Set `agent_count`: `"same as phase count, NOT doubled"`
- Set `on_issues_found`: `"fix_inline_before_proceeding_with_phase_work"`

The preamble must reference specific checks from Phase N's `full_checkpoint`, NOT generic "validate the previous phase." See `references/manual-preamble-template.md`.

### Step 7: Validate Consistency and Compute Totals

Before writing output, verify and compute:

1. Every violation severity in checker config matches Stage 8's `violation_handling`
2. Functional checks reference real commands from `stage_0.tech_stack`
3. Stage 8's `full_checkpoint` gate aligns with the 4-step protocol
4. No checker rule contradicts the builder's phase spec
5. `per_phase_checker_config` has exactly one entry per phase from Stage 7

**Set `checker_builder_consistency`**: Cross-reference every severity level in the verifier's instructions against Stage 8's violation thresholds. Confirm there is no case where the builder is told "this is acceptable" but the verifier would classify it as a violation (or vice versa). Set to `true` if all severity levels, thresholds, and actions are aligned. Set to `false` and flag specific conflicts if any contradiction exists.

**Compute `verification_overhead_total`**: Sum the estimated verification token cost across ALL phases. For automated mode, this is `verifier_config.verifier_token_budget` multiplied by the number of phases (e.g., 10,000 tokens/phase x 4 phases = 40,000 tokens). For manual mode, estimate the preamble overhead per phase (~2,000-3,000 tokens) and sum across phases. This number tells Stage 10 the total token cost of the verification layer.

**Populate `verifier_config`**: Assemble the contract-required wrapper object:
- `approach`: Set from Step 1's verification mode determination ("automated" or "manual")
- `verifier_prompt`: The complete Agent B prompt (from Step 4) for automated, or the preamble template (from Step 6) for manual
- `verifier_inputs`: The 4 items Agent B receives: `["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"]`
- `verifier_token_budget`: ~10,000 for automated (from Agent B config), or ~2,000-3,000 for manual preamble
- `retry_config`: Map from `two_strike_rule` — `max_retries` (always 2), `retry_action` (git reset + fresh agent), `escalation_action` (stop for human review)
- `persistent_verifier`: `true` for automated (Agent B accumulates pattern knowledge), `false` for manual (each phase agent is independent)

If any contradiction is found during consistency validation, flag the specific conflict and attempt resolution. If unresolvable, trigger escape hatch.

## Output Format

```json
{
  "stage_9": {
    "verifier_config": {
      "approach": "automated | manual",
      "verifier_prompt": "Complete self-contained prompt for Agent B (automated) or the validation preamble for Phase N+1 (manual) — a fresh agent can execute this without additional context",
      "verifier_inputs": ["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"],
      "verifier_token_budget": 10000,
      "retry_config": {
        "max_retries": 2,
        "retry_action": "git reset --hard $PHASE_BASELINE, spawn fresh Agent A with clean context",
        "escalation_action": "stop_for_human_review"
      },
      "persistent_verifier": true
    },
    "checker_builder_consistency": true,
    "verification_overhead_total": 40000,
    "verification_mode": "automated_agent_b | manual_preamble_merge",
    "two_strike_rule": {
      "max_retries": 2,
      "on_second_failure": "stop_for_human_review",
      "rationale": "string"
    },
    "verification_protocol": {
      "step_1_self_report": {
        "description": "Agent lists every file created or modified",
        "compare_against": "file_sandbox.allowed list from phase spec",
        "output_format": "newline-separated file paths"
      },
      "step_2_diff_check": {
        "command": "git diff PHASE_N_BASELINE..HEAD --name-only",
        "compare_against": ["self_report", "allowed_files_list"],
        "mismatch_is_violation": true
      },
      "step_3_violation_response": "stage_8.instrumented_phases[N].violation_handling",
      "step_4_functional": {
        "commands": ["tech-stack-specific compile", "test", "lint"],
        "page_render_check": true
      }
    },
    "per_phase_checker_config": [
      {
        "phase_number": 1,
        "baseline_snapshot": "git_commit_hash_before_phase_1_starts",
        "allowed_files": ["copied from stage_7.phases[0].file_sandbox.allowed"],
        "functional_checks": ["npm run build"],
        "expected_outcomes": ["exit code 0"],
        "overrides": { "skip_test_check": true }
      }
    ],
    "agent_b_config": {
      "context_tokens": 10000,
      "clean_context": true,
      "persistent_across_phases": true,
      "receives": ["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"],
      "produces": "CLEAN | LOW | MEDIUM | HIGH | CRITICAL",
      "on_high_or_critical": "git reset --hard $PHASE_BASELINE, retry fresh Agent A, apply two_strike_rule"
    },
    "manual_preamble_config": {
      "preamble_template": "concrete template text — see references/manual-preamble-template.md",
      "check_duration_estimate": "30 seconds",
      "agent_count": "same as phase count, NOT doubled",
      "on_issues_found": "fix_inline_before_proceeding_with_phase_work"
    }
  }
}
```

Metadata updates:

```json
{
  "metadata.current_stage": 9,
  "metadata.confidence_scores.9": { "score": 0, "dimensions": {...} },
  "metadata.stage_timestamps.9": "ISO-8601"
}
```

## Edge Cases

### Missing Input

| Missing Field | Action |
|---------------|--------|
| `stage_8.instrumented_phases` | FAIL — trigger escape hatch. Cannot configure verification without protocols. |
| `stage_7.phases` | FAIL — trigger escape hatch. Cannot build per-phase configs without phase definitions. |
| `stage_0.tech_stack` | WARN — default to Node/npm commands. Flag in confidence scoring (Accuracy penalty). |
| `stage_8.*.violation_handling` empty for some phases | Generate default LOW/MEDIUM/HIGH/CRITICAL tree for those phases. Flag as override. |

### Ambiguous Input

| Ambiguity | Resolution |
|-----------|------------|
| Tech stack has both `build_command` and `compile_command` | Use `build_command` for functional check. |
| Phase has no `file_sandbox.allowed` (empty list) | Treat as infrastructure-only phase. Set `skip_functional: true` in overrides. |
| Violation rules differ between Stage 8 phases | Use the strictest interpretation. Log the discrepancy. |

### Scope Overflow

| Discovery | Action |
|-----------|--------|
| Phase spec needs restructuring to be verifiable | Do NOT restructure. Flag as `NEEDS_HUMAN` with suggestion: "Phase N may need splitting — verification requires clearer file boundaries." |
| Functional checks need new tooling not in tech stack | Log the gap. Use closest available command. Flag in confidence. |

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): Both verification approaches configured? Every phase has `per_phase_checker_config`? All 4 protocol steps defined? Two-strike rule set with `max_retries=2`? `verifier_config` wrapper fully populated (approach, verifier_prompt, verifier_inputs, verifier_token_budget, retry_config, persistent_verifier)? `checker_builder_consistency` set? `verification_overhead_total` computed?

2. **Accuracy** (0-20): Functional checks use real commands from `stage_0.tech_stack`? Agent B config matches spec (~10K tokens, clean context, persistent)? Violation severities match Stage 8 exactly? `verification_overhead_total` is within ±15% of actual sum?

3. **Consistency** (0-20): Checker's `allowed_files` matches Stage 7's `file_sandbox.allowed` per phase? Protocol aligns with Stage 8's `full_checkpoint`? Both approaches use identical core protocol? `checker_builder_consistency` is `true` — no case where builder rules and verifier rules contradict?

4. **Specificity** (0-20): Git commands are exact (not "run a diff")? Preamble template is concrete text? Expected outcomes include exit codes? `verifier_config.verifier_prompt` is a complete, self-contained prompt (not a reference to another file)?

5. **Handoff Readiness** (0-20): Stage 10 can render `build.sh` from this output? Bash retry logic is copy-ready? Preamble is paste-ready into Phase N+1? `verifier_config.retry_config` has all three fields (`max_retries`, `retry_action`, `escalation_action`) so Stage 10 can mechanically generate the retry loop?

**Total /100: >= 90 PASS | 70-89 WARN (flag + proceed) | < 70 FAIL (escape hatch)**

## Escape Hatch

**Trigger when:**
- Required inputs missing (no `instrumented_phases`, no `phases`, no `tech_stack`)
- Tech stack unrecognized (cannot determine compile/test commands)
- Stage 8 violation rules are incomplete or contradictory
- Checker config would contradict builder's phase spec
- Confidence score < 70 after one retry

**Save:** Current `context_packet`, stage number (9), step where halt occurred, which phases have configs and which don't, suggested questions for human.

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{ "stage": 9, "reason": "...", "suggested_actions": [...] }]
}
```

## Example

See `references/four-step-verification.md` for a complete walkthrough showing both automated and manual flows for a React+TypeScript app with 3 phases. The example covers:
- Phase 1 (auth): compile-only check, Agent B classifies CLEAN
- Phase 2 (dashboard): compile + test + route check, Agent B detects MEDIUM drift on shared types file
- Phase 3 (payments): Agent B detects HIGH violation, triggers revert + retry, fresh Agent A passes on second attempt
- Manual flow: Phase 2 opens with Phase 1 validation preamble, finds and fixes a missing export inline


---
## REFERENCE: agent-b-config-template

# Agent B Configuration Template

## Agent B Prompt (Automated Verifier)

```
You are a build verification agent. You audit the builder agent's output for a single phase.
You have NO knowledge of WHY the builder made its decisions. You see only evidence.

## Your Inputs

1. ALLOWED_FILES: The list of files this phase was permitted to create or modify.
2. GIT_DIFF: Output of `git diff PHASE_N_BASELINE..HEAD --name-only` — every file actually touched.
3. FUNCTIONAL_RESULTS: Output of compile, test, render, and route checks.
4. VIOLATION_TREE: The severity classification rules for unauthorized file changes.

## Your Job

Compare GIT_DIFF against ALLOWED_FILES. For every file in the diff:
- If it appears in ALLOWED_FILES: PASS (expected change)
- If it does NOT appear in ALLOWED_FILES: classify using the VIOLATION_TREE

Review FUNCTIONAL_RESULTS:
- If any check failed (non-zero exit code, render error, route 404): flag as functional failure

## Your Output

Produce exactly ONE classification for this phase:

| Classification | Meaning | Trigger |
|----------------|---------|---------|
| CLEAN | All files in diff are in allowed list. All functional checks pass. | Zero violations, zero failures |
| LOW | 1-2 files outside allowed list, but they are shared types/config files. All functional checks pass. | Minor drift, additive changes only |
| MEDIUM | Files from another phase's domain were modified, OR a functional check has warnings (not errors). | Cross-phase drift or soft failures |
| HIGH | Files were deleted, core config was changed, OR a functional check failed (non-zero exit). | Dangerous drift or build breakage |
| CRITICAL | .env, CLAUDE.md, build config, or environment files were modified. OR multiple functional checks failed. | Security-relevant changes or cascading failures |

## Format

```
PHASE: {N}
CLASSIFICATION: {CLEAN|LOW|MEDIUM|HIGH|CRITICAL}
FILES_IN_DIFF: {count}
FILES_ALLOWED: {count}
UNAUTHORIZED_FILES: {list or "none"}
FUNCTIONAL_CHECKS: {all_pass|failures_list}
PATTERN_NOTE: {any cumulative observation from prior phases, or "first phase"}
```

## Rules

- You CANNOT edit any files. You are read-only.
- You CANNOT access the builder's conversation, reasoning, or context.
- If classification is HIGH or CRITICAL, the orchestrator will revert and retry.
- Be precise. "MEDIUM" is not "probably fine" — it means cross-phase drift was detected.
- If this is not the first phase, note patterns (e.g., "builder has drifted toward types.ts in 2 of 3 phases").
```

## Token Budget

- **Per-verification**: ~10,000 tokens
  - Allowed files list: ~500 tokens
  - Git diff output: ~1,000 tokens (typical phase touches 5-15 files)
  - Functional check results: ~2,000 tokens (build output, test output)
  - Violation decision tree: ~2,000 tokens
  - Agent B prompt: ~2,000 tokens
  - Working space: ~2,500 tokens
- **Across full build (4 phases)**: ~40,000 tokens total

## Persistence Model

Agent B persists across all phases. Its cumulative context grows by ~1,000 tokens per phase (the classification output + pattern note). By Phase 4 of a 4-phase build, Agent B's total context is ~13,000 tokens.

### Pattern Accumulation

After each phase, Agent B appends to its pattern log:

```
PHASE 1: CLEAN — 0 unauthorized files
PHASE 2: LOW — types.ts touched (shared type added)
PHASE 3: LOW — types.ts touched again (same file)
PHASE 4: MEDIUM — types.ts + utils/helpers.ts touched — PATTERN DETECTED: builder consistently drifts toward types.ts. Flagging as systemic.
```

If the same file appears as unauthorized in 3+ phases, escalate from LOW to MEDIUM regardless of individual severity, and add: `"SYSTEMIC: builder repeatedly touches {file} across phases. Consider adding to allowed list or splitting differently."`

## Integration with Orchestrator

```bash
# The orchestrator calls Agent B after each phase
PHASE_RESULT=$(run_agent_b \
  --allowed-files "phase-${N}-allowed.txt" \
  --diff-output "phase-${N}-diff.txt" \
  --functional-results "phase-${N}-checks.txt" \
  --violation-tree "violation-rules.json" \
  --pattern-log "agent-b-pattern-log.txt" \
)

# Parse the classification
CLASSIFICATION=$(echo "$PHASE_RESULT" | grep "CLASSIFICATION:" | cut -d' ' -f2)
```


---
## REFERENCE: four-step-verification

# Four-Step End-of-Phase Verification Protocol

## Overview

Every phase ends with this 4-step verification. It is identical for automated and manual modes — only the delivery wrapper differs.

## The Protocol

### Step 1: Self-Report

The builder agent lists every file it created, modified, or deleted during the phase.

**Input**: Agent's own memory of what it changed.
**Compare against**: `file_sandbox.allowed` from the phase spec.
**Output format**:
```
FILES_CREATED:
- src/lib/auth.ts
- src/contexts/AuthContext.tsx

FILES_MODIFIED:
- src/App.tsx (added routes)

FILES_DELETED:
(none)
```

**Why this exists**: First-pass sanity check. Fast, but unreliable — agents can forget files or hallucinate changes. This is a courtesy check, NOT ground truth.

### Step 2: Diff Check (Ground Truth)

Run the deterministic git diff command.

**Command**: `git diff PHASE_N_BASELINE..HEAD --name-only`

**Compare against**:
1. The self-report from Step 1
2. The `file_sandbox.allowed` list from the phase spec

**Mismatch handling**:
- File in diff but NOT in self-report: Agent forgot to mention it. This is a violation (agent honesty failure).
- File in self-report but NOT in diff: Agent hallucinated a change. Flag but not critical.
- File in diff but NOT in `file_sandbox.allowed`: Unauthorized file change. Classify using violation tree.

**Why this is ground truth**: `git diff` is mechanical. It cannot lie, cannot forget, cannot hallucinate. It captures every byte that changed.

### Step 3: Violation Response

For every unauthorized file (in diff but NOT in `file_sandbox.allowed`), apply the violation decision tree from `stage_8.instrumented_phases[N].violation_handling`:

| Severity | Example | Action |
|----------|---------|--------|
| LOW | Touched a shared `types.ts` to add an export | Log it. Note in phase report. Proceed. |
| MEDIUM | Modified a file from another phase's domain | STOP. If additive (added export/prop): log + proceed with caution. If destructive (renamed, changed logic): revert that file to baseline. |
| HIGH | Deleted files, modified core config, changed auth logic | REVERT ENTIRE PHASE. Re-run with tighter constraints. |
| CRITICAL | Modified `.env`, `CLAUDE.md`, build config, environment files | FULL STOP. REVERT. FLAG. Human must intervene. |

### Step 4: Functional Checks

Run tech-stack-appropriate verification commands.

#### Command Mapping

| Tech Stack | Compile Check | Test Check | Lint Check |
|------------|--------------|------------|------------|
| Node/React/Next.js | `npm run build` | `npm run test` | `npm run lint` |
| Python/Django/Flask | `python -m py_compile {files}` | `python -m pytest` | `ruff check .` |
| Rust | `cargo build` | `cargo test` | `cargo clippy` |
| Go | `go build ./...` | `go test ./...` | `golangci-lint run` |
| Flutter/Dart | `flutter build` | `flutter test` | `flutter analyze` |

#### Render & Route Checks (Web Apps)

For phases that create UI pages:
- **Render check**: Do new pages/components render without errors? (Check browser console for React errors, 500s, blank screens)
- **Route check**: Can you navigate to expected routes? (e.g., `/sign-in` returns 200, not 404)

#### Expected Outcomes

Each functional check has a specific pass condition:
- Compile: exits with code 0
- Test: 0 failures (warnings OK)
- Lint: 0 errors (warnings OK)
- Render: no runtime errors in console
- Route: expected routes return 200

**ALL FOUR STEPS MUST PASS BEFORE THE NEXT PHASE BEGINS.**

---

## Complete Example: React + TypeScript App (3 Phases)

### Phase 1: Auth System

**Allowed files**: `src/lib/auth.ts`, `src/contexts/AuthContext.tsx`, `src/pages/SignIn.tsx`, `src/pages/SignUp.tsx`, `src/App.tsx`

**Automated flow (Agent B)**:
1. Agent A builds auth system
2. `git diff phase-1-baseline..HEAD --name-only` returns:
   ```
   src/lib/auth.ts
   src/contexts/AuthContext.tsx
   src/pages/SignIn.tsx
   src/pages/SignUp.tsx
   src/App.tsx
   ```
3. Agent B compares: all 5 files are in allowed list. Zero unauthorized files.
4. Functional checks: `npm run build` exits 0. No tests yet (Phase 1 override: `skip_test_check: true`).
5. **Classification: CLEAN**. Proceed to Phase 2.

**Manual flow**: Phase 1 has no preamble (no prior phase to validate). Phase 2 will open with Phase 1 validation.

### Phase 2: Dashboard + Data Layer

**Allowed files**: `src/pages/Dashboard.tsx`, `src/hooks/useData.ts`, `src/lib/api.ts`, `src/components/DataTable.tsx`

**Automated flow (Agent B)**:
1. Agent A builds dashboard
2. `git diff phase-2-baseline..HEAD --name-only` returns:
   ```
   src/pages/Dashboard.tsx
   src/hooks/useData.ts
   src/lib/api.ts
   src/components/DataTable.tsx
   src/lib/types.ts          <-- NOT in allowed list
   ```
3. Agent B compares: 4 files match, 1 unauthorized (`types.ts`).
4. Agent B checks violation tree: `types.ts` is a shared types file. Classification: **LOW**.
5. Functional checks: `npm run build` exits 0. `npm run test` exits 0 (auth tests from Phase 1 still pass).
6. **Classification: LOW**. Log drift, proceed to Phase 3.
7. Pattern log: `"Phase 2: LOW — types.ts touched (shared type added)"`

**Manual flow (Phase 2 prompt opens with)**:
```
## Pre-Phase Validation (Phase 1 Deliverables)
Before starting Phase 2 work, validate Phase 1:
Run: git diff phase-1-baseline..HEAD --name-only
Expected: src/lib/auth.ts, src/contexts/AuthContext.tsx, src/pages/SignIn.tsx, src/pages/SignUp.tsx, src/App.tsx
Run: npm run build (expect exit 0)
Navigate to /sign-in and /sign-up (expect pages render)
```
Agent finds Phase 1 clean. Proceeds with Phase 2 work.

### Phase 3: Payments

**Allowed files**: `src/pages/Checkout.tsx`, `src/lib/payments.ts`, `src/components/PaymentForm.tsx`

**Automated flow (Agent B) — failure scenario**:
1. Agent A builds payments
2. `git diff phase-3-baseline..HEAD --name-only` returns:
   ```
   src/pages/Checkout.tsx
   src/lib/payments.ts
   src/components/PaymentForm.tsx
   src/lib/auth.ts            <-- Phase 1's file! NOT in allowed list
   .env                       <-- CRITICAL
   ```
3. Agent B compares: 3 files match, 2 unauthorized.
4. `src/lib/auth.ts` = modified another phase's file = MEDIUM/HIGH.
5. `.env` = environment file = **CRITICAL**.
6. Functional checks skipped (CRITICAL already determined).
7. **Classification: CRITICAL**. Trigger revert.

**Revert + retry**:
1. `git reset --hard phase-3-baseline`
2. Fresh Agent A (new context, no memory of failed attempt)
3. Fresh Agent A builds payments without touching auth.ts or .env
4. Agent B verifies: CLEAN
5. **Phase 3 passes on second attempt.**

**If second attempt also failed**: STOP. Write failure report. Human reviews Phase 3 spec.


---
## REFERENCE: manual-preamble-template

# Manual Preamble Template

## Purpose

For users pasting prompts into Claude Code web/desktop (no bash automation), verification of Phase N is merged as a 30-second preamble into Phase N+1's prompt. This avoids doubling the agent count.

## Template

The following template is inserted at the TOP of Phase N+1's prompt, before the phase's own work begins. Replace `{N}` with the previous phase number and fill in the phase-specific values.

```markdown
## Pre-Phase Validation (Phase {N} Deliverables)

Before starting Phase {N+1} work, validate that Phase {N} was completed correctly.

### File Check
Run: `git diff {PHASE_N_BASELINE}..HEAD --name-only`

Expected files (Phase {N} allowed list):
{ALLOWED_FILES_LIST — one per line}

**If any file in the diff is NOT in the expected list above:**
- Shared types/config file (e.g., types.ts, index.ts) -> Note it, proceed
- File from a different phase's domain -> STOP. Revert that file: `git checkout {PHASE_N_BASELINE} -- {file}`
- Core system file (.env, CLAUDE.md, build config) -> STOP. Revert ALL Phase {N} changes: `git reset --hard {PHASE_N_BASELINE}` and redo Phase {N} from scratch

### Functional Check
Run these commands and verify they pass:
{FUNCTIONAL_COMMANDS — one per line with expected outcome}

Example:
- `npm run build` -> exits with code 0
- `npm run test` -> all tests pass (0 failures)
- Navigate to {EXPECTED_ROUTES} -> pages render without errors

### Verdict
- All files match + all checks pass -> Proceed with Phase {N+1} work below
- Minor issues (1-2 extra shared files, warnings but no errors) -> Fix inline, then proceed
- Major issues (wrong files modified, build fails, tests fail) -> Fix ALL issues before starting Phase {N+1}

---
## Phase {N+1}: {PHASE_NAME}
{... Phase N+1's actual instructions follow ...}
```

## Customization Rules

1. **`ALLOWED_FILES_LIST`**: Copy directly from `stage_7.phases[N].file_sandbox.allowed`. One file per line.
2. **`FUNCTIONAL_COMMANDS`**: Derive from `stage_0.tech_stack`:
   - Node/React: `npm run build`, `npm run test`, route checks
   - Python: `python -m pytest`, `ruff check .`, `mypy .`
   - Rust: `cargo build`, `cargo test`
   - Go: `go build ./...`, `go test ./...`
3. **`EXPECTED_ROUTES`**: Derive from the pages/routes created in Phase N (from `stage_6.sub_6b` mapped to phases in Stage 7).
4. **`PHASE_N_BASELINE`**: The git commit hash or tag created before Phase N started. In practice, this is set by the build script or manually noted.

## Duration Estimate

The preamble check takes approximately 30 seconds of the agent's time:
- Read the diff output: ~5 seconds
- Compare against allowed list: ~10 seconds
- Run functional checks (if not already run): ~10 seconds
- Make pass/fix/redo decision: ~5 seconds

This is negligible compared to the 10-30 minutes a typical phase takes.

## Agent Count Impact

| Approach | Phases | Agents | Idle Gaps |
|----------|--------|--------|-----------|
| Separate checker agents | 4 | 8 (4 build + 4 check) | 4 gaps (5-25 min each) |
| Preamble merge | 4 | 4 (each checks previous) | 0 extra gaps |

The preamble approach saves 4 idle gaps and halves the agent sessions for manual users.

## Edge Case: Phase 1

Phase 1 has no previous phase to validate. Its prompt does NOT include the preamble. The preamble first appears in Phase 2's prompt (validating Phase 1).

## Edge Case: Final Phase

The final phase's output has no "next phase" to validate it. For manual users, the final phase should include its own self-validation step at the end (the standard 4-step protocol runs as an epilogue rather than as the next phase's preamble).


---
## REFERENCE: two-strike-bash-script

# Two-Strike Bash Script Pattern

## Purpose

Bash implementation of the two-strike retry rule for automated (Agent B) verification. Copy this pattern into `build.sh` generation in Stage 10.

## Script Pattern

```bash
#!/bin/bash
set -euo pipefail

# ============================================================
# Two-Strike Verification Loop
# If a phase fails HIGH/CRITICAL twice, stop for human review.
# ============================================================

PHASE_NUMBER=$1
PHASE_FILE="phases/phase-${PHASE_NUMBER}.md"
BASELINE_TAG="phase-${PHASE_NUMBER}-baseline"

# Capture baseline before phase starts
git tag -f "$BASELINE_TAG" HEAD

run_phase() {
    local attempt=$1
    echo "=== Phase ${PHASE_NUMBER}, Attempt ${attempt} ==="

    # Run builder agent (Agent A)
    # Replace with actual agent invocation command
    claude --prompt-file "$PHASE_FILE" \
           --permission-mode acceptEdits \
           --settings-file .claude/settings.json

    # Capture diff
    git diff "${BASELINE_TAG}..HEAD" --name-only > "phase-${PHASE_NUMBER}-diff.txt"

    # Run functional checks
    run_functional_checks "$PHASE_NUMBER" > "phase-${PHASE_NUMBER}-checks.txt" 2>&1
    FUNC_EXIT=$?

    # Run Agent B (verifier)
    CLASSIFICATION=$(run_agent_b \
        --allowed-files "phases/phase-${PHASE_NUMBER}-allowed.txt" \
        --diff-output "phase-${PHASE_NUMBER}-diff.txt" \
        --functional-results "phase-${PHASE_NUMBER}-checks.txt" \
        --violation-tree "violation-rules.json" \
        --pattern-log "agent-b-pattern-log.txt" \
    | grep "CLASSIFICATION:" | cut -d' ' -f2)

    echo "Phase ${PHASE_NUMBER} classification: ${CLASSIFICATION}"
    echo "$CLASSIFICATION"
}

# --- Attempt 1 ---
RESULT=$(run_phase 1)

if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
    echo "!!! Phase ${PHASE_NUMBER} FAILED verification (${RESULT}). Reverting..."
    git reset --hard "$BASELINE_TAG"

    # --- Attempt 2 (fresh agent, clean context) ---
    RESULT=$(run_phase 2)

    if [ "$RESULT" = "HIGH" ] || [ "$RESULT" = "CRITICAL" ]; then
        echo "!!! Phase ${PHASE_NUMBER} FAILED TWICE (${RESULT}). STOPPING FOR HUMAN REVIEW."
        git reset --hard "$BASELINE_TAG"

        # Write failure report
        cat > "phase-${PHASE_NUMBER}-failure-report.txt" <<REPORT
PHASE: ${PHASE_NUMBER}
STATUS: FAILED_TWICE
CLASSIFICATION: ${RESULT}
ACTION_REQUIRED: Human review needed.
REASON: Two fresh agents failed the same phase. The problem is likely the phase specification, not the agents.
SUGGESTED_ACTIONS:
  1. Review the phase spec for ambiguity or contradictions
  2. Check if file_sandbox.allowed is too restrictive
  3. Check if the phase scope is too large (consider splitting)
  4. Review the functional check expectations
REPORT

        exit 1
    fi
fi

# If we get here, phase passed (CLEAN, LOW, or MEDIUM)
echo "Phase ${PHASE_NUMBER} PASSED verification: ${RESULT}"

# Tag the successful completion
git tag -f "phase-${PHASE_NUMBER}-complete" HEAD
```

## Functional Check Helper

```bash
run_functional_checks() {
    local phase=$1
    local exit_code=0

    echo "--- Compile Check ---"
    # Tech-stack-specific: replace with actual commands
    npm run build 2>&1 || exit_code=1

    echo "--- Test Check ---"
    if [ -f "package.json" ] && grep -q '"test"' package.json; then
        npm run test 2>&1 || exit_code=1
    else
        echo "No test script found. Skipping."
    fi

    echo "--- Render Check ---"
    # For web apps: start dev server, check routes, stop
    # This is tech-stack-specific and may use curl or playwright
    echo "Render check: manual verification required for web apps"

    return $exit_code
}
```

## Key Rules

1. **max_retries = 2. Always.** Do not make this configurable. Three retries waste tokens and almost never succeed when two have failed.
2. **Fresh agent on retry.** The retried Agent A has zero memory of the first attempt. Clean context, clean slate.
3. **Revert before retry.** `git reset --hard $BASELINE_TAG` ensures the second attempt starts from the exact same state as the first.
4. **Exit 1 on double failure.** The build script stops. A human must read the failure report and intervene.
5. **Tag baselines.** Every phase gets a git tag before it starts. This is the rollback point.

## Integration Notes

- Stage 10 fills in the actual agent invocation commands based on `stage_0.tech_stack`
- Stage 10 fills in the actual functional check commands
- The `run_agent_b` function is a wrapper around the Agent B prompt from `agent-b-config-template.md`
- The pattern log (`agent-b-pattern-log.txt`) persists across phases for Agent B's cumulative awareness

