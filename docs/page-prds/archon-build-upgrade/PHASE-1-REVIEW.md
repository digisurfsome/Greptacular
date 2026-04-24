# Phase 1 Build Review

**Reviewer:** Claude Opus 4.7 (re-used from v3 validation session — warmed up on the PRD and Archon source)
**Date:** 2026-04-19
**Scope:** Correctness review of Sonnet's Phase 1 build against the PRD and Archon engine behavior. Things Test A could not catch.
**Where the build actually lives:** `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\` (Archon workspace — **not** in the Greptacular git repo). Sonnet committed nothing to the Greptacular dev repo; the build files are runtime-only under Archon's workspace path. Flag to owner: if this was the intended location, fine; if git-tracking was expected, Phase 1 is not in version control.

---

## Summary

- Mechanisms reviewed: M1, M2, M3, M8, M9, M10, M11, M12
- **PASS:** 4 (M1, M8, M9, M11)
- **MINOR:** 3 (M2, M3, M12)
- **FAIL:** 1 (M10)
- **Overall verdict:** **NEEDS FIXES** — one real bug (M10) breaks the status-threading logic the whole v3 M10 edit was meant to fix. The other three findings are quality/polish issues, not blockers. Fix M10 first, then ship.

Test A passed 8/8, but Test A only exercises the five gate scripts on fixtures. It does **not** run the YAML wiring, does not trigger recovery, and does not verify that `$recovery-status-summary` actually detects recovery-run artifacts. That's how M10 got through.

---

## Top 3 Blockers

1. **M10 recovery-status-summary never detects recovery.** It checks for `$ARTIFACTS_DIR/recovery-*/` directories, but the recovery command prompts write their outputs **flat** to `$ARTIFACTS_DIR/` (triage-report.md, fix-prd.md, recovery-execution-report.md). The check always fails → archive-prd always gets labeled `shipped`, even after a successful recovery. Fix below.
2. **M3 Stage 10 success criterion may falsely fail.** PRD §7 Phase 1 complete criterion says: *"Grep for 'separate task' in `.archon/commands/prd-stage-10-v2.md` and `build-fix-v2.md` returns 0 matches."* Both files contain the literal string `"separate task"` — in prohibition context (i.e., telling the agent "you may NOT declare work a separate task"). Letter-of-the-law, the grep test would return matches and flag Phase 1 as not complete. Owner decides whether the grep test is too naive or the files need to rephrase. Flagged as AMBIGUOUS under M3.
3. **M2 full-checkpoint assumes Node.** Hard-codes `npm run lint` / `npm run typecheck` / `npm test`. A Python-only or Rust-only project would fail all three checks unconditionally. Phase 1 doesn't require multi-language, but this should be fixed before any non-Node project hits this pipeline.

---

## Per-mechanism findings

### M1 — Compliance Gate Script

**Verdict:** ✅ PASS

**Evidence:**
- `compliance-gate.py` lines 23–51: `count_issues` / `count_fixes` use the exact regex patterns from PRD §4 M1 (`^[*-] \*\*\[<severity>\]` and `^### Fix [0-9]+:.*\[<severity>\]`).
- Lines 65–82: the severity-by-severity comparison matches PRD pseudocode. `unaddressed = max(0, issues - fixes)` is correct — no negative counts when fixes > issues.
- YAML wiring at `prd-pipeline-c.yaml:232–240` wraps the script in a `set +e` + stdout `PASS`/`FAIL` + `exit 0` pattern. Matches M9's gate contract.
- Fixture counts verified: yt-strategy-lab-fail has 5 CRITICAL + 46 HIGH across the four review files; fix-report.md has 5 CRITICAL + 12 HIGH → 34 unaddressed HIGH. Gate emits `FAIL: 34 issues unaddressed (CRITICAL: 0, HIGH: 34) …`. Matches PRD §8 success criterion.
- Result-file write at lines 86–94 is best-effort (`except OSError: pass`) so the gate never hard-fails on a write error.

**Problem:** None.

---

### M2 — Full Checkpoint Script

**Verdict:** ⚠️ MINOR

**Evidence:**
- `full-checkpoint.py` lines 72–89: hardcodes `npm run lint`, `npm run typecheck`, `npm test`. Fallback at lines 78–84 tries `npx tsc --noEmit` if `npm run typecheck` is missing.
- Lines 94–118: `files_allowed` diff is implemented correctly. Set difference against `git diff --name-only $baseline_sha`. Skips cleanly if `files_allowed.json` is absent (line 122).
- Line 51: `baseline_sha = sys.argv[2].strip("'")` — defensive strip in case Archon's shellQuote wrapping survives bash's quote removal. Harmless.

**Problem:** PRD §4 M2 says the checks are language-appropriate: *"`npm run lint` (or language-appropriate) … Python: `mypy`, Rust: `cargo check`."* The shipped script only tries Node. A Python-only project hits this pipeline → `npm` isn't installed → all three checks return `FileNotFoundError` → the checkpoint fails mechanically on correct code.

**BEFORE (current shipped code, full-checkpoint.py lines 71–89):**

```python
# ── 1. Lint ──────────────────────────────────────────────────────────────
passed, msg = run_check(['npm', 'run', 'lint'], 'lint')
(results if passed else failures).append(msg)

# ── 2. Typecheck ─────────────────────────────────────────────────────────
passed, msg = run_check(['npm', 'run', 'typecheck'], 'typecheck')
if not passed:
    # Fallback: try tsc --noEmit directly
    passed2, msg2 = run_check(['npx', 'tsc', '--noEmit'], 'typecheck (tsc)')
    if passed2:
        results.append(msg2)
    else:
        failures.append(msg2)
else:
    results.append(msg)

# ── 3. Tests ─────────────────────────────────────────────────────────────
passed, msg = run_check(['npm', 'test'], 'tests')
(results if passed else failures).append(msg)
```

**AFTER (replacement):**

```python
# ── Detect project language(s) from files at cwd ─────────────────────────
has_node  = os.path.exists('package.json')
has_py    = os.path.exists('pyproject.toml') or os.path.exists('requirements.txt')
has_rust  = os.path.exists('Cargo.toml')

if not (has_node or has_py or has_rust):
    results.append("SKIP: no known project manifest (package.json/pyproject.toml/Cargo.toml) — skipping lint/typecheck/test")
else:
    # ── 1. Lint ──────────────────────────────────────────────────────────
    if has_node:
        passed, msg = run_check(['npm', 'run', 'lint'], 'lint (npm)')
        (results if passed else failures).append(msg)
    if has_py:
        passed, msg = run_check(['ruff', 'check', '.'], 'lint (ruff)')
        (results if passed else failures).append(msg)
    if has_rust:
        passed, msg = run_check(['cargo', 'clippy', '--', '-D', 'warnings'], 'lint (clippy)')
        (results if passed else failures).append(msg)

    # ── 2. Typecheck ─────────────────────────────────────────────────────
    if has_node:
        passed, msg = run_check(['npm', 'run', 'typecheck'], 'typecheck (npm)')
        if not passed:
            passed2, msg2 = run_check(['npx', 'tsc', '--noEmit'], 'typecheck (tsc)')
            (results if passed2 else failures).append(msg2)
        else:
            results.append(msg)
    if has_py:
        passed, msg = run_check(['mypy', '.'], 'typecheck (mypy)')
        (results if passed else failures).append(msg)
    if has_rust:
        passed, msg = run_check(['cargo', 'check'], 'typecheck (cargo check)')
        (results if passed else failures).append(msg)

    # ── 3. Tests ─────────────────────────────────────────────────────────
    if has_node:
        passed, msg = run_check(['npm', 'test'], 'tests (npm)')
        (results if passed else failures).append(msg)
    if has_py:
        passed, msg = run_check(['pytest'], 'tests (pytest)')
        (results if passed else failures).append(msg)
    if has_rust:
        passed, msg = run_check(['cargo', 'test'], 'tests (cargo test)')
        (results if passed else failures).append(msg)
```

**Why this works:** Detects language from manifest files at the project root (cheap, deterministic), runs only the checks that apply, and skips cleanly if no known manifest is found. Matches the PRD §4 M2 contract language.

---

### M3 — Stage 10 Prompt Tightening

**Verdict:** ⚠️ MINOR (AMBIGUOUS — PRD success criterion vs. shipped prompt content)

**Evidence:**
- `build-fix-v2.md` has the mandatory contract block at lines 21–37 with the exact text the PRD §4 M3 specified. ✅
- `build-fix-v2.md` line 66: `You may NOT declare a category of work "a separate task per instructions"` — the phrase appears in a prohibition.
- `prd-stage-10-v2.md` line 60: `"tests are a separate task per instructions"` — also in a "Do NOT include:" block.
- `build-fix-v2.md` line 65 contains `"all tests", "all async issues", "architectural issues"` — same pattern, quoting the forbidden language while forbidding it.
- Both files cleanly encode the mandatory contract, the item-scoped two-strike rule, the deferred.md rules, and the compliance gate reference. The **content** matches PRD §4 M3 perfectly.

**Problem:** PRD §7 Phase 1 success criterion line: *"Grep for 'separate task' in `.archon/commands/prd-stage-10-v2.md` and `build-fix-v2.md` returns 0 matches."* A naive grep returns matches (the forbidden phrases are quoted in prohibition context). The builder followed the letter of the §4 M3 template (which explicitly includes a "Do NOT include" list), but that list references the banned phrases verbatim. The §7 grep test and the §4 M3 template contradict each other.

**BEFORE (current shipped code, build-fix-v2.md lines 64–66):**

```markdown
- You may NOT declare entire categories exempt (e.g., "all tests", "all async issues", "architectural issues")
- You may NOT declare a category of work "a separate task per instructions"
```

**AFTER (replacement — rephrase the prohibition without quoting the banned phrase):**

```markdown
- You may NOT declare entire categories exempt — every issue gets an individual attempt before deferral
- You may NOT split work into this-phase vs. follow-up-task scopes; reviewer findings are in scope for THIS phase
- You may NOT label work architectural or out-of-scope to skip a fix — architectural concerns still get a fix entry or a deferred.md entry with evidence
```

**And BEFORE (prd-stage-10-v2.md lines 59–63):**

```markdown
   Do NOT include:
   - "tests are a separate task per instructions"
   - "defer to human" applied to categories of work
   - "architectural issues → out of scope"
   - Any language that allows an agent to skip a WALL step without a deferred.md entry
```

**AFTER (replacement):**

```markdown
   Do NOT include any language that lets an agent skip a WALL step, declare tests out-of-scope,
   defer entire categories of work, or split fixes into follow-up tasks. Every flagged issue
   gets a fix entry OR a deferred.md entry with reason and evidence — no third option.
```

**Why this works:** Removes the literal banned strings while keeping the meaning — the prohibition is stronger without them because it describes the behavior, not the catchphrases. Side effect: PRD §7's grep test now returns 0 matches and the Phase 1 complete checklist signs off clean.

**Owner decision flag (AMBIGUOUS):** Two ways to resolve — (a) rephrase the prompts as above; (b) relax the §7 grep test to inspect only agent-authored output (e.g., build-fix output files), not the prompt templates themselves. Either is defensible. I recommend (a) because it's a 1-minute edit and keeps the §7 criterion enforceable.

---

### M8 — Pre-Deploy Gate + Deferred Budget

**Verdict:** ✅ PASS

**Evidence:**
- `deploy-gate.py` lines 35–60: `count_remaining` uses `^[*-] \*\*\[(CRITICAL|HIGH)\]` across both flat and nested paths. `count_fixed` counts `^### Fix N:` globally. `count_deferred` counts bullet entries in `deferred.md`.
- Line 22: `DEFERRED_CAP = 5` matches PRD §4 M8.
- Lines 93–103: checks match the PRD contract — `remaining > fixed → FAIL`, `deferred_count > 5 → FAIL`.
- Lines 30–32: `collect_files` handles both single-run (flat) and multi-phase (runs/*/) layouts. Matches PRD's cumulative-across-runs intent.
- YAML at `prd-pipeline-c.yaml:326–334`: wrapped in the standard `set +e` / stdout PASS-FAIL / `exit 0` pattern.

**Problem:** None.

---

### M9 — Recovery Pipeline

**Verdict:** ✅ PASS

**Evidence:**
- Gate emits PASS/FAIL on stdout and exits 0 (`prd-pipeline-c.yaml:232–240`). Archon captures stdout as `nodeOutput.output` (dag-executor.ts:1368).
- Recovery branch nodes (`recovery-diagnose`, `recovery-fix-prd`, `recovery-execute`) use `when: "$compliance-gate.output == 'FAIL' && $read-flag-recovery.output == 'true'"` — valid per condition-evaluator.ts atomPattern (line 88) and AND logic (lines 157–166). Hyphens in node ids allowed.
- `depends_on` on each recovery node correctly includes `compliance-gate` and `read-flag-recovery` as dependencies (not just in the `when:` — required so the engine waits for those outputs). ✅
- Model `opus` + `effort: high` on all three agent nodes — matches PRD §15.
- `compliance-regate` re-runs the gate after recovery with the same PASS/FAIL/exit-0 pattern, gated on the same `when:` so it's skipped when recovery didn't run.
- `compliance-final-status` aggregator at lines 292–304 uses `trigger_rule: all_done` correctly. I traced all four states:
  - **Initial gate PASS →** `[ 'PASS' = PASS ]` true → echo PASS (exit 0). ✅
  - **Initial FAIL, recovery toggle off →** regate skipped → `$compliance-regate.output` = `''` → first `[ 'FAIL' = PASS ]` false → `[ '' = PASS ]` false → else exit 1. ✅
  - **Initial FAIL, recovery ran, regate PASS →** first false, `elif [ 'PASS' = PASS ]` true → echo PASS. ✅
  - **Initial FAIL, recovery ran, regate FAIL →** both false → else exit 1. ✅
- Shell quoting: every `$<node>.output` reference in the final-status bash is UNWRAPPED by outer quotes. Archon's `substituteNodeOutputRefs` with `escapedForBash=true` (dag-executor.ts:1357) auto-wraps via `shellQuote` (line 183). No double-wrapping anywhere. Verified each reference.
- `set -euo pipefail` in the aggregator: `set -u` is harmless here because all references are substituted to literals (single-quoted strings) before bash sees them.

**Problem:** None. The most intricate piece of the build and it composes correctly.

**Minor note (not a defect):** `recovery-fix-prd` and `recovery-execute` prompts don't specify an `idle_timeout`. Opus-high can stall on long reasoning; the v3 report's "optional observations" noted this and called it non-blocking. Still non-blocking, just reiterating.

---

### M10 — PRD Archive

**Verdict:** ❌ FAIL

**Evidence:**
- `prd-pipeline-c.yaml:370–379` — `recovery-status-summary` bash checks for subdirectories matching `$ARTIFACTS_DIR/recovery-*/`.
- `recovery-diagnose.md` line 30: writes to `$ARTIFACTS_DIR/triage-report.md` (flat).
- `recovery-fix-prd.md` line 25: writes to `$ARTIFACTS_DIR/fix-prd.md` (flat).
- `recovery-execute.md` line 34: writes to `$ARTIFACTS_DIR/recovery-execution-report.md` (flat). Also appends to `$ARTIFACTS_DIR/fix-report.md`.
- **None of the recovery prompts create a `recovery-N/` subdirectory.** The PRD §4 M9 says *"Output files (all at `$ARTIFACTS_DIR/recovery-N/`)"* — the builder ignored that path convention when writing the recovery prompts, and then the `recovery-status-summary` check relies on it.

**Problem:** After a successful recovery run, `ls "$ARTIFACTS_DIR"/recovery-*/` returns nothing (no such directory exists), so the node always emits `shipped`. The archive's status column will never correctly read `recovered`. This is the exact bug the v3 M10 fix was created to solve — it's been re-introduced by a prompt/bash mismatch.

Secondary: no path emits `failed`. If `full-checkpoint` fails (hard exit 1), deploy-gate is skipped, `$deploy-gate.output == ''`, `build-deploy` is skipped by its `when:`, `recovery-status-summary` (trigger_rule: all_done) still runs, `archive-prd` then runs too and labels the run `shipped` — even though the deploy never happened. The PRD contract says status ∈ `{shipped, failed, recovered}`. The shipped wiring only ever emits `shipped` or `recovered`, and as shown above, `recovered` is unreachable.

**Two options — pick one.** I recommend Option A (cheaper, fixes both problems in one spot).

#### Option A — Fix in `recovery-status-summary` (RECOMMENDED)

Use a different detection signal: the existence of `triage-report.md` (written only by recovery-diagnose). And add a `failed` branch by checking `$deploy-gate.output`.

**BEFORE (current shipped, prd-pipeline-c.yaml:370–379):**

```yaml
- id: recovery-status-summary
  bash: |
    set -euo pipefail
    if ls "$ARTIFACTS_DIR"/recovery-*/ 2>/dev/null | head -1 >/dev/null 2>&1; then
      echo "recovered"
    else
      echo "shipped"
    fi
  depends_on: [build-deploy]
  trigger_rule: all_done
```

**AFTER (replacement):**

```yaml
# Status threading: detects recovery via triage-report.md (written by recovery-diagnose),
# and failure via deploy-gate output. Falls through to "shipped" only when deploy passed
# and no recovery ran.
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

**Why this works:**
- `$deploy-gate.output` substitutes to `'PASS'`, `'FAIL'`, or `''` (skipped). `[ 'PASS' != PASS ]` false, `[ 'FAIL' != PASS ]` true, `[ '' != PASS ]` true — so any non-PASS state (including skipped after checkpoint failure) routes to `failed`.
- `triage-report.md` is a concrete artifact recovery-diagnose always writes first in the recovery chain. If it exists, recovery ran. This is the same detection the v3 M10 note suggested, it just uses a real artifact the prompts actually produce.
- `depends_on` adds `deploy-gate` so the output is available.
- `trigger_rule: all_done` preserved — still runs even when upstream nodes were skipped.

#### Option B — Fix in the recovery prompts (ALTERNATIVE)

If you want to keep `recovery-*/` subdirectory convention, change all three recovery prompts to write to `$ARTIFACTS_DIR/recovery-1/…` instead of `$ARTIFACTS_DIR/…`, and add a counter if multi-recovery is ever expected. This is more edits and doesn't fix the missing `failed` state.

I recommend Option A.

---

### M11 — Regression Harness

**Verdict:** ✅ PASS

**Evidence:**
- Separate file `regression-harness.yaml` exists at `.archon/workflows/regression-harness.yaml` — not inside `prd-pipeline-c.yaml`. ✅
- Standalone workflow has proper `name:`, `description:`, and a single `regression-run` node with `timeout: 300000`. Schema-valid per `bashNodeSchema`.
- `regression-harness.py` is self-contained: reads env vars with defaults (`FIXTURES`, `SCRIPTS_DIR`), exits 0 on all PASS, exits 1 on any FAIL. Doesn't import anything that requires non-stdlib packages.
- Test A is comprehensive: A1 (compliance FAIL), A2 (compliance PASS), A3 (full-checkpoint FAIL via unauthorized file change), A4 (deploy-gate FAIL), A5 (deploy-gate PASS), A6 (archive-prd creates dir + updates INDEX). Matches PRD §9 assertion list.
- The builder enhanced A6 to verify the archive directory was created AND the INDEX entry was appended — a correct extension beyond the PRD spec.

**Minor side-effect (not a defect):** A6 creates a real `docs/generated-prds/{today}__regression-test-{today}/` directory and appends an INDEX row every regression run. Running regression daily over months = accumulation. Not blocking. If you want cleanup, add a `shutil.rmtree(expected_dir)` at the end of A6 and remove the appended INDEX row. Not required for Phase 1 sign-off.

**Problem:** None.

---

### M12 — Feature Toggles

**Verdict:** ⚠️ MINOR

**Evidence:**
- `features.yaml` lists 6 toggles per PRD §4 M12. ✅
- Two read-flag nodes exist: `read-flag-recovery` (`prd-pipeline-c.yaml:32–40`) and `read-flag-archive` (lines 42–50). Both use the correct `uv run --with pyyaml python -c "..."` prefix per v3 Edit 4. ✅
- Both nodes default to `True` via `c.get(…, True)` — correct per PRD M12 "If a toggle is missing, it defaults to the value below."
- `recovery-diagnose`, `recovery-fix-prd`, `recovery-execute`, `compliance-regate` all consult `read-flag-recovery` in their `when:`. ✅
- `archive-prd` consults `read-flag-archive` in its `when:` (line 389). ✅

**Problem:** **Two of six toggles are unwired.** `features.yaml` exposes `regression_harness`, `codebase_cartographer`, `scoped_claude_md`, `build_intelligence` — but there are no corresponding `read-flag-*` nodes and nothing downstream checks them. The v3 PRD narrative said *"Applying this pattern to all 6 toggled mechanisms (`recovery_pipeline`, `prd_archive`, `regression_harness`, `codebase_cartographer`, `scoped_claude_md`, `build_intelligence`) adds 6 read-flag nodes at pipeline start."*

**Context that makes it minor not a FAIL:** Phase 1 scope is M1/M2/M3/M8/M9/M10/M11/M12. M11 is now a standalone workflow (not in the main pipeline, so no toggle is meaningful — a user just chooses to run it or not). M6 (scoped_claude_md) and M7 (codebase_cartographer) are Phase 2/3 scope and aren't wired at all yet. `build_intelligence` is Phase 3. So the missing read-flags would toggle mechanisms that don't exist in this pipeline. Wiring them now would add dead nodes.

**Recommendation:** Comment the unwired toggles in `features.yaml` to reflect what's active. Keep the four Phase 2/3 toggles visible so the owner knows they exist, but mark them clearly. Re-enable wiring when Phase 2/3 lands.

**BEFORE (current `features.yaml` lines 9–11):**

```yaml
codebase_cartographer: true   # M7: Haiku builds CODEBASE_MAP.md after build (Phase 3 — not yet wired)
scoped_claude_md: true        # M6: per-directory CLAUDE.md auto-attach (Phase 2 — not yet wired)
build_intelligence: false     # Phase 3: learn from prior builds — OFF until 5+ builds logged
```

**AFTER (replacement — mark clearly to prevent false expectations):**

```yaml
# ── UNWIRED toggles (listed for future phases; changing them has no effect today) ──
codebase_cartographer: true   # M7 (Phase 3): Haiku builds CODEBASE_MAP.md — NOT WIRED in Phase 1
scoped_claude_md: true        # M6 (Phase 2): per-directory CLAUDE.md auto-attach — NOT WIRED in Phase 1
regression_harness: true      # M11: self-tests run as separate workflow `archon workflow run regression-harness` — no toggle needed
build_intelligence: false     # Phase 3: learn from prior builds — OFF until 5+ builds logged, NOT WIRED in Phase 1
```

**Why this works:** No code change needed. Documents reality so the owner doesn't assume toggling does something it doesn't. When Phase 2 lands, the Phase 2 builder can flip these from "NOT WIRED" to wired read-flag nodes.

**Secondary minor:** If `features.yaml` contains malformed YAML, `yaml.safe_load()` raises → the bash node fails → the workflow hard-halts before Stage 0 even starts. Consider wrapping in try/except for robustness:

```yaml
bash: |
  uv run --with pyyaml python -c "
  import yaml, os
  path = '.archon/features.yaml'
  try:
      c = yaml.safe_load(open(path)) if os.path.exists(path) else {}
      if not isinstance(c, dict): c = {}
  except Exception:
      c = {}
  print(str(c.get('recovery_pipeline', True)).lower())
  "
```

Not blocking — malformed YAML is the owner's own foot-gun — but a 10-second change to make the pipeline immune to it.

---

## Cross-cutting findings

### YAML schema compliance

**Verdict:** ✅ PASS

Every node uses exactly one of `command`/`bash`/`prompt`/`loop`/`script`/`approval`/`cancel` (mutually exclusive per `dag-node.ts:378–396`). `timeout` values are all positive integers. `depends_on` references all resolve to real node ids in the file (verified by reading through the whole YAML). `trigger_rule` values are all from the valid enum (`all_success` default, `all_done` on `build-final-report` / `compliance-final-status` / `recovery-status-summary`).

### Shell-quoting audit (every `$<node>.output` reference)

**Verdict:** ✅ PASS

Audited every `$<node>.output` reference in `prd-pipeline-c.yaml`:

| Reference | Location | Wrapping check |
|---|---|---|
| `$compliance-gate.output` | compliance-final-status bash line 295 | bare — ✅ |
| `$compliance-regate.output` | compliance-final-status bash line 297 | bare — ✅ |
| `$compliance-gate.output` | recovery-diagnose `when:` line 251 | inside `'…'` literal on RHS — ✅ (required by condition-evaluator) |
| `$read-flag-recovery.output` | recovery-diagnose `when:` line 251 | same as above — ✅ |
| (same pattern) | recovery-fix-prd, recovery-execute, compliance-regate `when:` | ✅ |
| `$phase-1-baseline.output` | full-checkpoint bash line 315 | bare — ✅ |
| `$deploy-gate.output` | build-deploy `when:` line 359 | inside `'…'` — ✅ |
| `$recovery-status-summary.output` | archive-prd bash line 386 | bare — ✅ |
| `$read-flag-archive.output` | archive-prd `when:` line 389 | inside `'…'` — ✅ |

No double-wrapping. The v3 shell-quoting trap has been avoided throughout.

### `uv run --with pyyaml` coverage

**Verdict:** ✅ PASS (for what's wired)

Both shipped read-flag nodes (`read-flag-recovery`, `read-flag-archive`) use `uv run --with pyyaml python -c "…"`. No plain `python -c "import yaml"` anywhere in the YAML. Future read-flag nodes must use the same prefix — flagged in M12 for Phase 2/3 builders.

### Recovery branch flow integrity

**Verdict:** ✅ PASS

All four recovery nodes have consistent `when:` expressions. `depends_on` correctly threads gate + flag-node outputs. Aggregator uses `all_done`. Four-state truth table verified (see M9 above). The branch composes correctly against `condition-evaluator.ts:87–88` and `substituteNodeOutputRefs` behavior.

### Model / effort field coverage

**Verdict:** ✅ PASS — matches PRD §15 exactly

| Node | Shipped model / effort | PRD §15 expected | Match |
|---|---|---|---|
| stage-10-output-generator | (inherits workflow `opus`) | sonnet for most, `build-fix-v2` upgraded | Stage 10 inherits workflow opus — fine, this is a content-generation node where Opus doesn't hurt |
| build-codebase-intelligence | (inherits) | no override specified | ✅ |
| build-execute | `sonnet` | `sonnet` | ✅ |
| build-verify-compliance | `sonnet` | `sonnet` | ✅ |
| review-* (all 4) | `sonnet` | `sonnet` | ✅ |
| build-fix-issues | `opus` + `effort: medium` | `opus` + `medium` | ✅ — the permanent upgrade |
| recovery-diagnose | `opus` + `effort: high` | `opus` + `high` | ✅ |
| recovery-fix-prd | `opus` + `effort: high` | `opus` + `high` | ✅ |
| recovery-execute | `opus` + `effort: high` | `opus` + `high` | ✅ |
| build-final-report | `haiku` | `haiku` | ✅ |
| build-deploy | `sonnet` | `sonnet` | ✅ |

No literal "Opus 4.7" strings. No invalid model aliases. No typos.

### One observation on the commit location

**Not a defect, but a workflow question:** All Phase 1 files live at `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\`. Nothing is in the Greptacular git repo (`C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular`). `git log` in the Greptacular repo shows only your two PRD commits (v3 fixes + validation report) — no Phase 1 scripts/commands/YAML.

If the intent was for Archon to own its own workspace as the canonical storage, fine. If the intent was to version-control these files in the Greptacular repo (as the PRD implies with paths like `.archon/scripts/compliance-gate.py`), Phase 1 is not in git. Flag for the owner — this affects rollback strategy from PRD §10.

---

## Recommendation

**Apply M10 fix, then ship.** The M10 bug is real — status threading is broken and that was the whole point of the v3 M10 edit. Option A is a 10-line YAML change. After that, M2 and M3 are MINORs worth a second commit but not blockers; the pipeline runs correctly on Node projects today and the M3 grep test is a success-criteria wording issue, not a functional one. M12 is documentation cleanup.

Order of operations for the fix agent:
1. **M10 (FAIL)** — apply Option A YAML replacement in `prd-pipeline-c.yaml` lines 370–379. Non-negotiable.
2. **M3 (MINOR)** — rephrase the two prompt blocks in `build-fix-v2.md` and `prd-stage-10-v2.md` so §7's grep test passes without changing behavior.
3. **M2 (MINOR)** — add language detection to `full-checkpoint.py`. Only needed before a non-Node project hits this pipeline; can defer to Phase 2.
4. **M12 (MINOR)** — edit comments in `features.yaml`. Optional, purely documentation.

After M10 fix, Phase 1 is ready to ship on a Node project. The North Star test (re-run YT Strategy Lab and produce either clean deploy or mechanical gate-failure reason, no "deploy succeeded with 34 issues deferred") will work as designed.
