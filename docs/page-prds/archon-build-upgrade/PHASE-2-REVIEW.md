# Phase 2 Opus Review — Phase 1 Fixes + M4/M5/M6

**Reviewer:** Opus (adversarial quality gate)
**Scope:** Commits `0785e6a`, `3e15ddd`, `ef1f86c` on `main`
**Reference:** `docs/page-prds/archon-build-upgrade/README.md` (PRD v3), `PHASE-1-REVIEW.md`

---

## Summary

- **Mechanisms reviewed:** Phase 1 fixes (M10, M3, M2, M12) + Phase 2 additions (M4 per-phase unroll, M5 test-writer, M6 per-directory CLAUDE.md)
- **PASS: 14**  **MINOR: 3**  **FAIL: 2**
- **Overall verdict:** NEEDS FIXES
- **Top blockers:**
  1. `phase-handoff.md` command file was written but **never wired into the pipeline** — zero nodes reference it (C2/FAIL).
  2. `lint-autofix.py` script was written but **never wired into the pipeline** — no node invokes it (C5/FAIL).
  3. M3 grep test still returns 5 matches for "separate task" across 3 command files (A2/MINOR — known from Phase 1 review, partially but not fully resolved).

Everything else is clean: shell-quoting correct across all 24 `$<node>.output` references, mutual exclusivity holds on every node, models match §15, `context: fresh` set everywhere required, recovery branch and M10 fix both wired correctly.

---

## Section A — Phase 1 Fix Verification

### A1. M10 fix — `recovery-status-summary` node — **PASS**

**Evidence:** `prd-pipeline-c.yaml:623-634`

```yaml
- id: recovery-status-summary
  bash: |
    set -euo pipefail
    if [ $deploy-gate.output != PASS ]; then
      echo "failed"
    elif [ -f "$ARTIFACTS_DIR/triage-report.md" ]; then
      echo "recovered"
    else
      echo "shipped"
    fi
  depends_on: [build-deploy, deploy-gate]
  trigger_rule: all_done
```

Four-case truth table:

| Deploy-gate output | `triage-report.md` present | Status emitted | Correct? |
|---|---|---|---|
| `'PASS'` (escaped) | no | `shipped` | ✓ |
| `'PASS'` | yes (recovery ran + passed) | `recovered` | ✓ |
| `'FAIL'` | yes (recovery ran but failed) | `failed` | ✓ |
| `''` (skipped upstream) | n/a | `failed` | ✓ (`[ '' != PASS ]` is true) |

- `$deploy-gate.output` is BARE on line 626 — no outer double-quotes. Correct for escapedForBash substitution. ✓
- `depends_on` includes both `build-deploy` AND `deploy-gate`. ✓
- `trigger_rule: all_done` present. ✓
- Phase 1 review's FAIL on this is resolved.

### A2. M3 fix — grep for "separate task" and "defer to human" — **MINOR (partially resolved)**

**Evidence:** Grep across `.archon/commands/`:

```
prd-stage-10-v2.md:45:   Writing tests for flagged coverage gaps is part of this contract, not a separate task.
prd-stage-10-v2.md:162:- Zero instances of exemption language ("separate task", ...)
recovery-diagnose.md:22: "tests are a separate task" or "architectural issue out of scope"
build-fix-v2.md:31: **Writing tests for flagged coverage gaps is part of this contract, not a separate task.**
build-fix-v2.md:75: This step is not optional and is not a "separate task."
```

**Per PRD §7, a literal grep must return 0 matches.** It returns 5.

All 5 hits are in prohibition context (the prompts are telling the agent *not* to use this language). But a naive `grep -c "separate task"` cannot tell prohibition from permission. If the PRD's compliance test runs an unanchored grep, it still fails.

**Before** (`build-fix-v2.md:31`):
```
**Writing tests for flagged coverage gaps is part of this contract, not a separate task.**
```

**After (suggested, anchor the prohibition):**
```
**Writing tests for flagged coverage gaps is in scope for this phase. It is not deferrable.**
```

Same substitution needed at `build-fix-v2.md:75`, `prd-stage-10-v2.md:45`. Lines 162 and `recovery-diagnose.md:22` *quote* the banned phrase as the target of detection — those are safe only if the grep test excludes quoted occurrences. Either rephrase all 5 or anchor the test (`grep -v '"separate task"'`).

**"defer to human"** — grep across `.archon/commands/` returns zero matches. ✓

### A3. M2 fix — `full-checkpoint.py` language detection — **PASS**

**Evidence:** `full-checkpoint.py:72-114`

- Detects `package.json` / `pyproject.toml` / `requirements.txt` / `Cargo.toml` at lines 72-74. ✓
- Line 76-77: clean skip with `SKIP: no known project manifest …` when none match. ✓
- Three-branch `run_check` coverage is complete:
  - Node: `npm run lint` → `npm run typecheck` (fallback `npx tsc --noEmit`) → `npm test` (lines 80-107)
  - Python: `ruff check .` → `mypy .` → `pytest` (lines 83-110)
  - Rust: `cargo clippy -- -D warnings` → `cargo check` → `cargo test` (lines 86-113)
- `files_allowed` diff runs independent of language branch (line 117+) ✓
- Exit semantics: `sys.exit(1 if failures else 0)` at line 161 — if no manifest and no `files_allowed.json`, both lists are empty, exits 0 (soft skip). ✓

### A4. M12 fix — `features.yaml` annotation — **PASS**

**Evidence:** `features.yaml:1-14`

- Line 8 header: `# ── UNWIRED toggles (listed for future phases; changing them has no effect today) ──` ✓
- Each of the four unwired toggles has a clear inline `NOT WIRED in Phase 1` or `NOT IMPLEMENTED` comment (lines 9, 10, 11, 12). ✓
- File still parses as valid YAML (6 scalar key/value pairs, comments only). ✓
- Note: `scoped_claude_md` (M6) is now "partially wired" — `claude-md-presence-check` runs unconditionally, but the audit is not actually gated on this toggle. The comment on line 10 says "NOT WIRED" which is accurate as a toggle, even though the M6 audit node itself now runs. This is a labeling accuracy concern, not a code bug.

---

## Section B — Phase 2 YAML Correctness

### B1. Shell-quoting audit — **PASS**

Every bash-context `$<node>.output` reference audited:

| Line | Reference | Context | Quoting |
|---|---|---|---|
| 295 | `$compliance-gate.output` | `if [ $compliance-gate.output = PASS ]` | BARE ✓ |
| 297 | `$compliance-regate.output` | `elif [ ... = PASS ]` | BARE ✓ |
| 314 | `$phase-1-baseline.output` | shell arg to full-checkpoint.py | BARE ✓ |
| 425 | `$phase-2-compliance.output` | `if [ ... = PASS ]` | BARE ✓ |
| 427 | `$phase-2-recovery-regate.output` | `elif [ ... = PASS ]` | BARE ✓ |
| 438 | `$phase-2-baseline.output` | shell arg | BARE ✓ |
| 540 | `$phase-3-compliance.output` | `if [ ... = PASS ]` | BARE ✓ |
| 542 | `$phase-3-recovery-regate.output` | `elif [ ... = PASS ]` | BARE ✓ |
| 553 | `$phase-3-baseline.output` | shell arg | BARE ✓ |
| 565 | `$phase-1-baseline.output` | shell arg to claude-md-audit.py | BARE ✓ |
| 626 | `$deploy-gate.output` | `if [ ... != PASS ]` | BARE ✓ |
| 641 | `$recovery-status-summary.output` | shell arg | BARE ✓ |

All 12 bash-context references are bare — correct for `escapedForBash=true` substitution (outputs arrive already single-quoted via `shellQuote`).

Every `when:` clause uses the `"$node.output == 'VALUE'"` pattern with single-quoted RHS (lines 251, 259, 267, 282, 390, 398, 406, 420, 505, 513, 521, 535, 609, 644). condition-evaluator's `atomPattern` requires single quotes — all compliant. ✓

Zero instances of `"$node.output"` double-wrapped in bash `if` tests. Clean.

### B2. Mutual exclusivity — **PASS**

Every new Phase 2/3 node has exactly one of `command` / `bash` (no node has both):

- `phase-2-baseline` — bash only
- `phase-2-execute` — command only
- `phase-2-review-*` (×4) — command only
- `phase-2-fix` — command only
- `phase-2-test-writer` — command only
- `phase-2-compliance` — bash only
- `phase-2-recovery-diagnose/fix-prd/execute` — command only
- `phase-2-recovery-regate` — bash only
- `phase-2-final-status` — bash only
- `phase-2-checkpoint` — bash only
- Phase 3 mirrors the above. Confirmed clean.
- `claude-md-presence-check` — bash only
- `recovery-status-summary` — bash only

Builder 2's fix held.

### B3. Per-phase structure — **PASS (with caveat)**

For each of phase-2 and phase-3:

| Stage | Shipped | Expected | Match? |
|---|---|---|---|
| baseline | depends on prior checkpoint | ✓ | ✓ |
| execute | depends on baseline | ✓ | ✓ |
| 4 reviews | depend on execute (not each other) | ✓ | ✓ |
| fix | depends on all 4 reviews | just reviews (brief accepts) | ✓ |
| test-writer | depends on **execute** (runs parallel to fix path) | either after fix OR parallel | ✓ per brief |
| compliance | depends on BOTH fix AND test-writer | ✓ | ✓ |
| recovery-* | depend chain + `compliance` + `read-flag-recovery` | ✓ | ✓ |
| final-status | depends on compliance + regate, `trigger_rule: all_done` | ✓ | ✓ |
| checkpoint | depends on final-status | ✓ | ✓ |

- Phase 3's baseline depends on `phase-2-checkpoint` (line 446). ✓
- Phase 1's full-checkpoint → `phase-2-baseline` chain intact (line 331). ✓

**Caveat:** `phase-N-test-writer` runs in parallel with `phase-N-fix` (both depend only on `phase-N-execute`). The brief's answer framing explicitly allows this ("or just reviews"). Test-writer explicitly prohibits non-test file modifications (test-writer.md:37), so there is no write contention with fix. Compliance correctly gates on both. Accepted.

### B4. Model assignments — **PASS**

Audited against PRD §15:

| Node | Shipped | Expected |
|---|---|---|
| `phase-2-execute` | `model: sonnet` | sonnet ✓ |
| `phase-2-fix` | `model: opus, effort: medium` | opus/medium ✓ |
| `phase-2-test-writer` | `model: sonnet` | sonnet ✓ |
| `phase-2-recovery-diagnose/fix-prd/execute` | `model: opus, effort: high` | opus/high ✓ |
| Phase 3 equivalents | same | ✓ |
| `claude-md-presence-check` | no model (bash node) | none required ✓ |

Zero literal version strings (no "claude-opus-4-7" etc.). All use alias form. ✓

**But:** there are no `phase-handoff` nodes in the pipeline at all — see C2 below.

### B5. `context: fresh` — **PASS**

Every Phase 2/3 agent node has `context: fresh`:

- `phase-2-execute` (337), `phase-2-fix` (369), `phase-2-test-writer` (375), `phase-2-recovery-diagnose` (393), `phase-2-recovery-fix-prd` (401), `phase-2-recovery-execute` (408)
- `phase-3-execute` (452), `phase-3-fix` (484), `phase-3-test-writer` (490), `phase-3-recovery-diagnose` (508), `phase-3-recovery-fix-prd` (516), `phase-3-recovery-execute` (524)

Standard S5 satisfied.

### B6. Recovery branch wiring — **PASS**

Phase 1 M9 pattern replicated exactly for Phase 2 and Phase 3:

- All three recovery agent nodes per phase share the same `when:` clause (phase-2: lines 390/398/406; phase-3: 505/513/521). ✓
- `recovery-diagnose` depends on both the compliance node AND `read-flag-recovery` (lines 389, 504). ✓
- Subsequent recovery nodes chain via their predecessors, inheriting the skip-propagation correctly. ✓
- Regate has the same `when:` as the three recovery nodes (lines 420, 535). ✓
- `final-status` depends on `[compliance, regate]` with `trigger_rule: all_done` (lines 433-434, 548-549). ✓

### B7. Deploy-gate chain — **PASS**

- `deploy-gate` depends on `claude-md-presence-check` (line 584). ✓
- `claude-md-presence-check` depends on `phase-3-checkpoint` (line 567). ✓
- `recovery-status-summary` depends on `[build-deploy, deploy-gate]` with `trigger_rule: all_done` (lines 633-634) — runs even when `build-deploy` was skipped via its `when:` gate. ✓
- `archive-prd` depends on `recovery-status-summary` and is gated on `$read-flag-archive.output == 'true'` (lines 643-644). ✓

### B8. Feature flag coverage — **MINOR (acceptable deferral, flagged for Phase 3)**

- `features.yaml` lists `scoped_claude_md`, `codebase_cartographer`, `regression_harness`, `build_intelligence`, `build_intelligence_mode` — five additional toggles beyond the two actually wired (`recovery_pipeline`, `prd_archive`).
- Only **two** `read-flag-*` nodes exist: `read-flag-recovery` and `read-flag-archive`.
- No `read-flag-scoped-claude-md` — `claude-md-presence-check` runs unconditionally on line 563-567. Per Phase 1 review this was acceptable; noting here so Phase 3 knows the toggle is cosmetic.

Not a blocker. Comment annotation in `features.yaml:8-12` sets the right expectation.

---

## Section C — Phase 2 Command Files

### C1. `test-writer.md` — **PASS**

Compared against PRD §4 M5 template (from `$ARGUMENTS`-driven dispatch):

- Reads `$ARTIFACTS_DIR/phases/` with phase id from `$ARGUMENTS` (lines 12-14). ✓
- Reads `review-tests.md` if present (line 15). ✓
- WALL/test type matrix complete (lines 22-28). ✓
- "Do NOT modify non-test files" prohibition (line 37). ✓
- "Do NOT skip WALL steps claiming they are 'trivial'" (line 39). ✓
- Pass criteria: WALL count == test coverage rows (line 70). ✓
- Notes bugs to `test-writer-notes.md` rather than fixing them (line 38). ✓

No exemption language. Scoping is correct.

### C2. `phase-handoff.md` — **FAIL (not wired)**

**Evidence:**
- File exists at `.archon/commands/phase-handoff.md`, 54 lines, Haiku-appropriate summarization prompt. Structure is fine (bullet-only sections, "Under 100 lines total" constraint on line 49, reads phase spec + fix-report + deferred + test-writer-report + phase-checkpoint-result).
- **But:** grep for `phase-handoff` across `.archon/` returns **zero files**. No node in `prd-pipeline-c.yaml` has `command: phase-handoff`.

The file header explicitly states: *"This node runs at the end of each phase to produce a slim context document for the next phase's agent."* That node does not exist in the pipeline.

**Before (absent):** no node invocation.

**After (suggested, one per phase, inserted after phase-N-checkpoint and before the next phase's baseline):**
```yaml
  - id: phase-2-handoff
    command: phase-handoff
    arguments: "2"
    depends_on: [phase-2-checkpoint]
    model: haiku
    context: fresh
```

Without this, Phase 2's context-compaction purpose (Standard S5 context hygiene) is defeated — `phase-3-execute` will receive a fresh context with no slim handoff doc from Phase 2.

**Secondary issue — spec mismatch:** the brief asked for "under 50 lines"; the file is 54 lines. Inside Haiku's budget either way, but the builder missed the target by 4 lines.

### C3. `build-execute-v2.md` — **PASS**

- "Directory Rules (soft guidance — best-effort, not gated)" section present at lines 23-37. ✓
- "soft guidance" explicit in both the section header (line 23) and the v2 preamble (lines 5-7: *"best-effort guidance — the pipeline enforces it via an audit node, not a hard gate"*). ✓
- 3-level CLAUDE.md lookup order (dir → parent → root) specified (lines 26-29). ✓
- 80-line cap on per-directory CLAUDE.md files (line 37). ✓
- Still enforces the Sandbox `files_allowed` contract (lines 50-54). ✓

### C4. `claude-md-audit.py` — **PASS**

- Always exits 0. Two explicit `sys.exit(0)` sites (line 65 on usage error, line 123 at main end) and no other `sys.exit` calls. DOOR confirmed. ✓
- Writes `claude-md-audit.md` to `$artifacts_dir` with scope note, missing/present lists (lines 89-113). Readable format. ✓
- Correctly detects "new directories" mode when given `baseline_sha` (lines 18-37) by git-diffing parent directories of changed files. ✓
- Handles the "strip single-quote" pattern on line 68 (`sys.argv[2].strip("'")`) — matches the pattern used in `full-checkpoint.py:51`. ✓

### C5. `lint-autofix.py` — **FAIL (not wired) + MINOR (skip-vs-fail conflation)**

**Evidence — not wired:**
- File exists at `.archon/scripts/lint-autofix.py`, 93 lines, runs eslint/prettier/ruff/black/cargo fmt.
- Grep for `lint-autofix` across `.archon/` returns only the script itself. **No pipeline node invokes it.**
- The file header says: *"Intended use: call this BEFORE the fix agent runs, so the fix agent sees a clean slate and doesn't waste its budget on style issues."* No such invocation exists.

Per PRD §5 Phase 2 intent, autofix runs before each fix node. This would need a `phase-N-lint-autofix` bash node between `phase-N-review-*` and `phase-N-fix`, or run in parallel with reviews. None exists.

**Before (absent):** no node.

**After (suggested):**
```yaml
  - id: phase-2-lint-autofix
    bash: python .archon/scripts/lint-autofix.py
    depends_on: [phase-2-execute]
    timeout: 180000
```

Then `phase-2-fix.depends_on` adds `phase-2-lint-autofix`.

**Secondary — MINOR — skip vs. fail conflation:**

On `lint-autofix.py:20-31`, a `FileNotFoundError` on a tool (e.g., `npx` or `ruff` not installed) returns `(False, "SKIP: ...")`. The caller at line 72 (`(results if ok else failures).append(msg)`) routes SKIP messages into `failures`, which triggers `sys.exit(1)` at line 89.

**Before** (lines 20-31, 62-72):
```python
def run(cmd, label, cwd):
    try:
        result = subprocess.run(cmd, ...)
        if result.returncode == 0:
            return True, f"PASS: {label}"
        return False, f"FAIL: {label}\n..."
    except FileNotFoundError:
        return False, f"SKIP: {label} — command not found: {cmd[0]}"
    ...
# caller
ok, msg = run(['ruff', 'check', '--fix', '.'], ...)
(results if ok else failures).append(msg)
```

If `ruff` is not installed on the host, the script exits 1 even though no lint violation occurred. In a real setup this will false-positive the autofix gate.

**After (suggested):** return a 3-tuple `(True, False, msg)` where the middle bool is `is_skip`, and route SKIP into `results`, not `failures`. Or use a separate sentinel return value.

Prettier and black already handle this (lines 67, 77: unconditional `results.append(msg)` — non-blocking). The same treatment should apply to tool-not-found cases for the blocking tools.

### C6. `prd-stage-10-v2.md` Stage 10 extension — **PASS**

**Evidence:** lines 102-132

- Step 5a ("Generate Per-Directory CLAUDE.md Files (M6)") is clear and well-scoped. ✓
- 80-line cap per CLAUDE.md (line 109) — more restrictive than the brief's 200-line ceiling (which is acceptable; tighter is better for rules files). ✓
- "Do NOT repeat the project root CLAUDE.md — only rules specific to this directory" — good separation (line 110). ✓
- Complete template provided (lines 113-129). ✓
- Output wiring: `deliverables.claude_md_files` added to `context_packet.json` (lines 131-132, 188). ✓
- Final validation list (line 163) includes: *"Every major directory in the build order has a per-directory CLAUDE.md (Step 5a above)"*. ✓
- Step 6 (Final Validation) still includes the grep-for-exemption-language check (line 162). ✓

---

## Recommendation

Before Phase 3 can start, the fix agent must do the following, in severity order:

1. **[FAIL] Wire `phase-handoff` command into the pipeline.** Add a `phase-N-handoff` node per phase (Haiku, `context: fresh`) that runs after `phase-N-checkpoint` and before the next phase's `baseline`. Pass the phase number via `arguments` or `$ARGUMENTS`. Without this, M4's phase-handoff mechanism is absent — Phase 3's fresh context will have no slim doc to ingest.

2. **[FAIL] Wire `lint-autofix.py` into each per-phase group.** Add `phase-N-lint-autofix` bash nodes between `phase-N-execute` and `phase-N-fix` so the fix agent doesn't burn Opus/medium budget on style issues. Fix the `FileNotFoundError` → `failures` routing before wiring (otherwise missing tools will hard-fail the gate).

3. **[MINOR] Resolve M3 grep test.** Choose one of:
   - Rephrase the 3 negation-context hits in `build-fix-v2.md:31`, `build-fix-v2.md:75`, `prd-stage-10-v2.md:45` to drop the literal string "separate task" (e.g., "is in scope for this phase. It is not deferrable").
   - OR anchor the PRD §7 test so it excludes quoted occurrences and the prohibition-list entries.
   - Either way, `recovery-diagnose.md:22` is already inside a quoted example — that one is low-risk but worth the same treatment for consistency.

4. **[MINOR] Trim `phase-handoff.md` to ≤50 lines** before wiring, per the brief's Haiku context-window note. Currently 54 lines.

5. **[MINOR] Document that `features.yaml` toggles beyond `recovery_pipeline` and `prd_archive` are comment-only.** The annotation in lines 8-12 is good but a single-line note at the top of the file ("Only two toggles are wired into Phase 2; the rest are cosmetic until Phase 3 wires them") would close the gap completely.

Everything else — YAML schema conformance, shell-quoting, mutual exclusivity, model/effort assignments, `context: fresh`, recovery wiring, deploy-gate chain, M10 status-summary logic, `full-checkpoint.py` language detection, `features.yaml` annotation, Stage 10 extension — is ready.

**Verdict: NEEDS FIXES.** Ship-blockers are items 1 and 2. Items 3-5 can land in the same commit or be punted to a polish pass, operator's call.
