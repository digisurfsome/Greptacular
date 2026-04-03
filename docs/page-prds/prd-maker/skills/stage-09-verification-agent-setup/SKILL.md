---
name: stage-09-verification-agent-setup
description: Configure independent verification agent (Agent B) with git-diff rules, two-strike retry, and per-phase checker configs for PRD build phases.
---

## Purpose

Configure an independent verification agent that audits builder output after each phase using git diff as ground truth. Produces both automated (Agent B) and manual (preamble merge) verification paths, the two-strike retry rule, and per-phase checker configs that Stage 10 renders into build scripts.

## When to Use

Activate when the context packet contains completed `stage_8.protocol_injected_phases`, `stage_7.phases`, and `stage_0.tech_stack`. This skill produces `stage_9.*` — the verification agent configuration, two-strike rule, 4-step verification protocol, per-phase checker configs, Agent B config, and manual preamble config.

## Input Format

```json
{
  "stage_8": {
    "protocol_injected_phases": [
      {
        "phase_number": 1,
        "pulse_checks": [...],
        "seam_checks": [...],
        "full_checkpoint": {...},
        "violation_rules": {
          "LOW": { "action": "log_and_proceed" },
          "MEDIUM": { "action": "review_change" },
          "HIGH": { "action": "revert_entire_phase" },
          "CRITICAL": { "action": "full_stop_revert_flag" }
        },
        "overhead_tokens": 25000
      }
    ]
  },
  "stage_7": {
    "phases": [
      {
        "phase_number": 1,
        "files_allowed": ["src/lib/auth.ts", "src/contexts/AuthContext.tsx"],
        "files_read_only": ["package.json"],
        "files_forbidden": [".env", "CLAUDE.md"],
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

1. **Self-Report** — Agent lists every file created/modified. Compare against `files_allowed`.
2. **Diff Check** — Run `git diff PHASE_N_BASELINE..HEAD --name-only`. Compare against BOTH self-report AND `files_allowed`. Mismatch between self-report and diff is itself a violation.
3. **Violation Response** — For any file in diff NOT in `files_allowed`, apply `stage_8.protocol_injected_phases[N].violation_rules` decision tree.
4. **Functional Checks** — Run tech-stack-appropriate compile, test, render, and route checks.

Map tech stack to functional check commands using the reference in `references/four-step-verification.md`.

### Step 3: Generate Per-Phase Checker Configs

For each phase in `stage_7.phases`:

1. Copy `files_allowed` as the verification baseline
2. Set `baseline_snapshot` to `"git_commit_hash_before_phase_N_starts"`
3. Determine applicable functional checks:
   - Phase 1: compile only (no prior features to regression-test)
   - Phase 2+: compile + test (if tests exist from prior phases)
   - Phases with UI: add render check + route check
4. Define `expected_outcomes` — specific exit codes and observable results
5. Add `overrides` for phase-specific deviations (e.g., Phase 1 skips test check)

Cross-reference each phase's `violation_rules` from Stage 8 to ensure severity levels match.

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

### Step 7: Validate Consistency with Stage 8

Before writing output, verify:

1. Every violation severity in checker config matches Stage 8's `violation_rules`
2. Functional checks reference real commands from `stage_0.tech_stack`
3. Stage 8's `full_checkpoint` gate aligns with the 4-step protocol
4. No checker rule contradicts the builder's phase spec
5. `per_phase_checker_config` has exactly one entry per phase from Stage 7

If any contradiction is found, flag the specific conflict and attempt resolution. If unresolvable, trigger escape hatch.

## Output Format

```json
{
  "stage_9": {
    "verification_mode": "automated_agent_b | manual_preamble_merge",
    "two_strike_rule": {
      "max_retries": 2,
      "on_second_failure": "stop_for_human_review",
      "rationale": "string"
    },
    "verification_protocol": {
      "step_1_self_report": {
        "description": "Agent lists every file created or modified",
        "compare_against": "files_allowed list from phase spec",
        "output_format": "newline-separated file paths"
      },
      "step_2_diff_check": {
        "command": "git diff PHASE_N_BASELINE..HEAD --name-only",
        "compare_against": ["self_report", "allowed_files_list"],
        "mismatch_is_violation": true
      },
      "step_3_violation_response": "stage_8.protocol_injected_phases[N].violation_rules",
      "step_4_functional": {
        "commands": ["tech-stack-specific compile", "test", "lint"],
        "page_render_check": true
      }
    },
    "per_phase_checker_config": [
      {
        "phase_number": 1,
        "baseline_snapshot": "git_commit_hash_before_phase_1_starts",
        "allowed_files": ["copied from stage_7.phases[0].files_allowed"],
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
| `stage_8.protocol_injected_phases` | FAIL — trigger escape hatch. Cannot configure verification without protocols. |
| `stage_7.phases` | FAIL — trigger escape hatch. Cannot build per-phase configs without phase definitions. |
| `stage_0.tech_stack` | WARN — default to Node/npm commands. Flag in confidence scoring (Accuracy penalty). |
| `stage_8.*.violation_rules` empty for some phases | Generate default LOW/MEDIUM/HIGH/CRITICAL tree for those phases. Flag as override. |

### Ambiguous Input

| Ambiguity | Resolution |
|-----------|------------|
| Tech stack has both `build_command` and `compile_command` | Use `build_command` for functional check. |
| Phase has no `files_allowed` (empty list) | Treat as infrastructure-only phase. Set `skip_functional: true` in overrides. |
| Violation rules differ between Stage 8 phases | Use the strictest interpretation. Log the discrepancy. |

### Scope Overflow

| Discovery | Action |
|-----------|--------|
| Phase spec needs restructuring to be verifiable | Do NOT restructure. Flag as `NEEDS_HUMAN` with suggestion: "Phase N may need splitting — verification requires clearer file boundaries." |
| Functional checks need new tooling not in tech stack | Log the gap. Use closest available command. Flag in confidence. |

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness** (0-20): Both verification approaches configured? Every phase has `per_phase_checker_config`? All 4 protocol steps defined? Two-strike rule set with `max_retries=2`?

2. **Accuracy** (0-20): Functional checks use real commands from `stage_0.tech_stack`? Agent B config matches spec (~10K tokens, clean context, persistent)? Violation severities match Stage 8 exactly?

3. **Consistency** (0-20): Checker's `allowed_files` matches Stage 7's `files_allowed` per phase? Protocol aligns with Stage 8's `full_checkpoint`? Both approaches use identical core protocol?

4. **Specificity** (0-20): Git commands are exact (not "run a diff")? Preamble template is concrete text? Expected outcomes include exit codes?

5. **Handoff Readiness** (0-20): Stage 10 can render `build.sh` from this output? Bash retry logic is copy-ready? Preamble is paste-ready into Phase N+1?

**Total /100: >= 90 PASS | 70-89 WARN (flag + proceed) | < 70 FAIL (escape hatch)**

## Escape Hatch

**Trigger when:**
- Required inputs missing (no `protocol_injected_phases`, no `phases`, no `tech_stack`)
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
