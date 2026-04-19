# PRD Validation Report — v2 (Independent Second Review)

**Scope:** Technical correctness only. Strategy is locked. This pass verifies that every YAML snippet, node-type choice, file path, substitution pattern, and Archon-engine claim in the PRD would actually execute against Archon's current schema (`packages/workflows/src/schemas/*`) and engine (`packages/workflows/src/dag-executor.ts`).

**Did NOT read:** `VALIDATION-REPORT.md`, `README.backup-pre-validation.md`, `HANDOFF.md`. Verified only against Archon source (`C:\Users\lober\archon\Archon\`) and the live PRD (`README.md`).

---

## Summary

- Total mechanisms: 12
- ✅ PASS: 5  (M3, M4, M5, M7, C-strategic concerns)
- ⚠️ MINOR: 5 (M1, M6, M8, M10, M11, M12)
- ❌ FAIL: 2 (M2, M9)
- ❓ AMBIGUOUS: 0

**Overall verdict: NEEDS REVISION — small, surgical.** The core architecture is sound. Node-type choices are correct, `when:` syntax matches the real evaluator, `for_each` is properly avoided, model/effort fields are valid, copy-don't-overwrite is the right pattern. But there is **one substitution bug that breaks M2 and M9 on execution**, and one **path-fragility pattern copied across seven mechanisms**. Both are 5-minute edits. Nothing here needs rethinking.

---

## Top blockers

1. **`$<node>.output` is wrapped in outer double quotes in bash scripts.** Archon already single-quotes these values at substitution time (`dag-executor.ts` line 1357 + `shellQuote()` in the same file). Wrapping them again in `"..."` produces literal quote characters in the final shell argument. `git rev-parse` hands Python `'abc123'` with real apostrophes; string comparisons against `"PASS"` hit `"'PASS'" = "PASS"` which is always false. **Breaks M2 (full-checkpoint) and M9 (recovery final-status aggregator) on the happy path.** Fix: drop the outer double quotes around every `$<node>.output` reference.

2. **`$ARCHON_HOME` is not guaranteed to be set in bash child processes.** Archon's code reads `process.env.ARCHON_HOME ?? defaultPath` internally, but does not export it to subprocesses. If the user hasn't manually `export ARCHON_HOME=...`, every bash node that references it gets an empty string, so paths resolve to `/workspaces/digisurfsome/...` (absolute root) and `python` fails with "file not found." Affects M1, M2, M4, M6, M8, M9, M10, M11, M12 — all the Python-invoking bash nodes. Fix: use relative paths like `.archon/scripts/compliance-gate.py` (Archon bash nodes run with `cwd` = the workspace source directory, confirmed at `dag-executor.ts` line 1362–1365).

3. **None of these are rethink-the-architecture problems.** Both are mechanical syntax corrections.

---

## Per-mechanism findings

### M1 — Compliance Gate Script
**Verdict:** ⚠️ MINOR (path fragility only — logic sound)
**Evidence:** `dag-executor.ts` lines 1347–1365 (bash node execution path); `substituteWorkflowVariables` plain-replaces `$ARTIFACTS_DIR` without shell-quoting (executor-shared.ts line 269+), so wrapping it in `"..."` is correct.
**Problem:** `$ARCHON_HOME` is not exported to bash child processes by default. Relative paths work because bash node `cwd` is the project root.

**BEFORE (PRD §4 M1, lines ~113–116):**
```yaml
- id: compliance-gate
  bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

**AFTER (replace with this exact block):**
```yaml
- id: compliance-gate
  bash: python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

**Why this works:** Archon runs bash nodes with `cwd` set to the workspace repo root (the directory that contains `.archon/`). `$ARTIFACTS_DIR` is substituted by `substituteWorkflowVariables` as a plain string — the surrounding `"..."` correctly handles paths with spaces. The script path is now unconditionally resolvable.

---

### M2 — Full Checkpoint Script
**Verdict:** ❌ FAIL (quoting bug breaks the node on every execution)
**Evidence:** `dag-executor.ts` line 1357 calls `substituteNodeOutputRefs(substitutedScript, nodeOutputs, true)`. With `escapedForBash=true`, the value is wrapped in single quotes via `shellQuote()`. If the PRD's YAML also wraps the reference in outer double quotes, the final shell argument contains literal quote characters.

**Problem:** `"$phase-baseline.output"` becomes `"'abc123sha'"` after substitution. In bash, that is an argument of 10 characters (including the two apostrophes), not 7. Python's `sys.argv[2]` receives `'abc123sha'`. Any `git diff 'abc123sha'` call fails with "unknown revision".

Also: the same `$ARCHON_HOME` fragility from M1 applies.

**BEFORE (PRD §4 M2, lines ~148–164):**
```yaml
- id: phase-baseline
  bash: git -C "$DOCS_DIR/.." rev-parse HEAD
  depends_on: [build-codebase-intelligence]

# ... build-execute-phase runs here ...

- id: full-checkpoint
  bash: |
    set -euo pipefail
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/full-checkpoint.py" \
      "$ARTIFACTS_DIR" \
      "$phase-baseline.output"
  timeout: 300000
  depends_on: [compliance-gate]
```

**AFTER (replace with this exact block):**
```yaml
- id: phase-baseline
  bash: git rev-parse HEAD
  depends_on: [build-codebase-intelligence]

# ... build-execute-phase runs here ...

- id: full-checkpoint
  bash: |
    set -euo pipefail
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-baseline.output
  timeout: 300000
  depends_on: [compliance-gate]
```

**Why this works:**
- `git rev-parse HEAD` runs in workflow cwd (the repo root) directly — no `-C "$DOCS_DIR/.."` trick needed, and `$DOCS_DIR` isn't guaranteed to resolve to the repo root anyway (it's `docs/` by default per executor-shared.ts line 289).
- Archon trims the trailing newline from bash-node stdout (dag-executor.ts line 1368 — `stdout.replace(/\n$/, '')`), so the captured output is a clean SHA.
- The reference `$phase-baseline.output` is NOT wrapped in outer quotes. At substitution time Archon replaces it with `'abc123sha'` (single-quoted by `shellQuote`). Bash parses that single-quoted token as the string `abc123sha` — exactly 1 argument, no literal quote characters inside.
- `"$ARTIFACTS_DIR"` stays double-quoted because it goes through `substituteWorkflowVariables` (plain replacement, no auto-quoting) and may contain spaces.

---

### M3 — Stage 10 Prompt Tightening
**Verdict:** ✅ PASS
**Evidence:** The mechanism is pure text editing on markdown prompt files. The PRD correctly targets `-v2` copies (`prd-stage-10-v2.md`, `build-fix-v2.md`) rather than editing originals. No YAML, no runtime behavior to validate.

No code snippet to correct. Phase 1 should execute this exactly as written.

---

### M4 — Per-Phase YAML Loop
**Verdict:** ✅ PASS (architectural reasoning is correct, with one inherited quoting fix)
**Evidence:**
- Archon has no `for_each` / `over:` / `as:` / `body:` — confirmed by reading `schemas/loop.ts` end-to-end. Loop nodes have exactly: `prompt`, `until`, `max_iterations`, `fresh_context`, `until_bash`, `interactive`, `gate_message`. The PRD's assertion (line 320) is accurate.
- `depends_on` chains correctly serialize phases. Parallel sibling nodes (the 4 reviewers all depending on `phase-N-execute`) run concurrently via `Promise.allSettled` — confirmed by dag-executor's topological layer pattern.
- `context: fresh` per-phase satisfies S5.
- Default `trigger_rule: all_success` means a failed gate skips downstream phases. Correct.

**One inherited fix:** the phase-N-checkpoint bash snippet (PRD line 291–294) has the same C1 quoting bug as M2. Copy the M2 fix to every phase-N-checkpoint node.

**BEFORE (PRD §4 M4, lines ~291–294):**
```yaml
- id: phase-1-checkpoint
  bash: |
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/full-checkpoint.py" "$ARTIFACTS_DIR" "$phase-1-baseline.output"
  timeout: 300000
  depends_on: [phase-1-compliance]
```

**AFTER (replace with this exact block):**
```yaml
- id: phase-1-checkpoint
  bash: |
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-1-baseline.output
  timeout: 300000
  depends_on: [phase-1-compliance]
```

**Why this works:** Same reasoning as M2. Apply the identical edit to `phase-2-checkpoint`, `phase-3-checkpoint`, etc. when unrolled.

Also replace `phase-1-compliance` similarly (see M9 below — the gate wrappers use `$ARCHON_HOME` too).

---

### M5 — Test Writer Node
**Verdict:** ✅ PASS
**Evidence:** Uses `command: test-writer` — a standard AI command node. `depends_on: [phase-N-execute]` is valid. `model: sonnet` is valid. `context: fresh` is valid (enum in dag-node.ts line 120: `z.enum(['fresh', 'shared'])`).

No runtime behavior to validate beyond "Archon will load a markdown file named `test-writer.md` from `.archon/commands/`." That's the standard command-discovery path.

No code snippet to correct.

---

### M6 — Scoped CLAUDE.md Auto-Attach
**Verdict:** ⚠️ MINOR (path fragility only)
**Evidence:** The PRD correctly notes that Claude SDK's `settingSources` only loads `project` or `user` CLAUDE.md, not per-directory ones. The M6 approach — soft agent guidance + observation-only audit node — is the correct workaround.

**Problem:** Same `$ARCHON_HOME` path fragility as M1.

**BEFORE (PRD §4 M6, lines ~403–410):**
```yaml
- id: claude-md-presence-check
  bash: |
    set -euo pipefail
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/claude-md-audit.py" "$ARTIFACTS_DIR"
  depends_on: [phase-3-checkpoint]
```

**AFTER (replace with this exact block):**
```yaml
- id: claude-md-presence-check
  bash: |
    set -euo pipefail
    python .archon/scripts/claude-md-audit.py "$ARTIFACTS_DIR"
  depends_on: [phase-3-checkpoint]
```

**Why this works:** Relative path resolves unconditionally from the workflow cwd.

---

### M7 — Codebase Cartographer
**Verdict:** ✅ PASS
**Evidence:** Uses `command: codebase-cartographer` — the right node type for an AI-driven task. `model: haiku` is a valid Archon alias (schema allows `z.string().optional()` and `isModelCompatible` accepts haiku for `claude` provider). `context: fresh` is valid. `depends_on: [phase-3-checkpoint]` assumes phase 3 is the last phase, which is the PRD's stated 3-phase Phase-1 unroll.

No code snippet to correct.

---

### M8 — Pre-Deploy Gate + Deferred Budget
**Verdict:** ⚠️ MINOR (path fragility only)
**Evidence:** Logic is sound. `depends_on: [build-final-report]` matches the real node id in `prd-pipeline-b.yaml` line 195. Bash-node + `$ARTIFACTS_DIR` substitution is the same correct pattern as M1.

**BEFORE (PRD §4 M8, lines ~490–493):**
```yaml
- id: deploy-gate
  bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/deploy-gate.py" "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-final-report]
```

**AFTER (replace with this exact block):**
```yaml
- id: deploy-gate
  bash: python .archon/scripts/deploy-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-final-report]
```

**Why this works:** Same reasoning as M1. Relative path resolves from cwd.

---

### M9 — Recovery Pipeline
**Verdict:** ❌ FAIL (quoting bug breaks the final-status aggregator on every run — including the happy path where the compliance gate passes first time)
**Evidence:**
- `when: "$<node>.output == 'VALUE'"` syntax matches `condition-evaluator.ts` atomPattern (line 87–88). Single-atom and compound `&&`/`||` forms are both supported.
- `trigger_rule: all_done` exists in `triggerRuleSchema` (dag-node.ts line 24–29). It correctly fires after all upstream nodes have settled (completed | failed | skipped).
- `effort: high` is a valid enum value (dag-node.ts line 41: `z.enum(['low', 'medium', 'high', 'max'])`).
- `model: opus` is a valid Claude alias.
- The pattern of "gate exits 0 + emits PASS/FAIL on stdout" is correct — that's how you expose gate results to a downstream `when:` branch, because hard-failed nodes skip their `$output` dependents by default.

**Problem:** The final-status aggregator wraps `$<node>.output` references in double quotes in a bash script. Because Archon single-quotes these values at substitution time (dag-executor.ts line 1357 + `shellQuote` line 183), the outer `"..."` preserves the apostrophes as literal characters. Every comparison against `"PASS"` will fail. That means even the **normal happy path** (compliance gate passes first time) triggers the `else` branch and exits 1, halting the whole pipeline.

Also: `set -euo pipefail` with `-u` (nounset) is fine here — Archon substitutes `$<node>.output` tokens BEFORE bash parses the script, so `-u` never sees an unresolved variable reference. Skipped-node outputs become `''` (empty string, valid shell token). No change needed to `set -euo pipefail`.

Gate node (exits 0, emits PASS/FAIL) — also has the $ARCHON_HOME fragility.

**BEFORE — gate node (PRD §4 M9, lines ~520–530):**
```yaml
- id: phase-1-compliance
  bash: |
    set +e
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-fix]
```

**AFTER — gate node:**
```yaml
- id: phase-1-compliance
  bash: |
    set +e
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-fix]
```

**Why this works:** Relative script path + gate still exits 0 and emits PASS/FAIL on stdout. Archon trims the trailing newline so `$phase-1-compliance.output` is exactly `PASS` or `FAIL`.

---

**BEFORE — recovery-regate node (PRD §4 M9, lines ~558–567):**
```yaml
- id: phase-1-recovery-regate
  bash: |
    set +e
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-recovery-execute]
  when: "$phase-1-compliance.output == 'FAIL'"
```

**AFTER — recovery-regate node:**
```yaml
- id: phase-1-recovery-regate
  bash: |
    set +e
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-recovery-execute]
  when: "$phase-1-compliance.output == 'FAIL'"
```

**Why this works:** The `when:` string is read by condition-evaluator directly (not through shell), so `$phase-1-compliance.output == 'FAIL'` is parsed as a single-atom expression against the nodeOutputs map. The evaluator compares the captured stdout (`PASS` or `FAIL`) against the literal `'FAIL'` — equality works correctly there. Only the bash-embedded references suffer the shell-quoting issue.

---

**BEFORE — final-status aggregator (PRD §4 M9, lines ~574–586) — THIS IS THE BROKEN NODE:**
```yaml
- id: phase-1-final-status
  bash: |
    set -euo pipefail
    if [ "$phase-1-compliance.output" = "PASS" ]; then
      echo "PASS"
    elif [ "$phase-1-recovery-regate.output" = "PASS" ]; then
      echo "PASS"
    else
      echo "FAIL" >&2
      exit 1
    fi
  depends_on: [phase-1-compliance, phase-1-recovery-regate]
  trigger_rule: all_done
```

**AFTER — final-status aggregator (replace with this exact block):**
```yaml
- id: phase-1-final-status
  bash: |
    set -euo pipefail
    if [ $phase-1-compliance.output = PASS ]; then
      echo "PASS"
    elif [ $phase-1-recovery-regate.output = PASS ]; then
      echo "PASS"
    else
      echo "FAIL" >&2
      exit 1
    fi
  depends_on: [phase-1-compliance, phase-1-recovery-regate]
  trigger_rule: all_done
```

**Why this works:**
- Archon substitutes `$phase-1-compliance.output` with `'PASS'` (single-quoted) at line 1357. Without the outer `"..."`, bash parses `'PASS'` as the string `PASS`. `[ PASS = PASS ]` → true. Happy path works.
- If the compliance gate emitted `FAIL` and the recovery-regate ran, the recovery-regate's output becomes the token checked next. `[ 'FAIL' = PASS ]` → false, check recovery-regate, same pattern.
- If recovery-regate was skipped (because gate passed first time), Archon substitutes it with `''` (empty single-quoted string). `[ '' = PASS ]` → false — but the first branch already matched, so we never reach it.
- `set -u` does not trip because the token has already been text-substituted before bash parses the script. There are no literal `$var` references bash could flag as unbound.
- `PASS` and `FAIL` literals on the right side are word tokens with no spaces, so they don't need quoting. (If you prefer the defensive style, wrapping JUST the right side in `"..."` is also safe: `[ $phase-1-compliance.output = "PASS" ]`.)

---

### M10 — PRD Archive
**Verdict:** ⚠️ MINOR (path fragility + one semantic concern worth flagging, not failing)
**Evidence:** `$BASE_BRANCH` is a valid Archon substitution variable (`executor-shared.ts` line 297: `.replace(/\$BASE_BRANCH/g, baseBranch)`). It is plain-replaced, not shell-quoted — so wrapping it in `"..."` in bash is correct.

**Problem 1:** Same `$ARCHON_HOME` fragility.
**Problem 2 (flag, don't fail):** Using `$BASE_BRANCH` as the archive's "build name" is semantically weird — for most builds, the base branch is `main` or `dev`, so every archive would land in `docs/generated-prds/{date}__main/`. That's functional but not informative. Acceptable for Phase 1 as the PRD itself admits, but worth the owner knowing.

**BEFORE (PRD §4 M10, lines ~648–655):**
```yaml
- id: archive-prd
  bash: |
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/archive-prd.py" \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

**AFTER (replace with this exact block):**
```yaml
- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

**Why this works:** Relative path resolves reliably. `$ARTIFACTS_DIR` and `$BASE_BRANCH` go through plain substitution and are safely wrapped in outer `"..."`. The "shipped" literal is hard-coded.

---

### M11 — Regression Harness
**Verdict:** ⚠️ MINOR (path fragility — logic and env-var technique are both correct)
**Evidence:** The `VAR=value VAR2=value command` prefix pattern is valid bash — sets env vars only for the invoked process. `depends_on: []` is fine: the schema strips empty arrays in its transform (`dag-node.ts` line 505–507), effectively making this a standalone node.

**BEFORE (PRD §4 M11, lines ~708–714):**
```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR="$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts" \
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/regression-harness.py"
  depends_on: []
```

**AFTER (replace with this exact block):**
```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR=".archon/scripts" \
    python .archon/scripts/regression-harness.py
  depends_on: []
```

**Why this works:** All paths become relative to the workflow cwd. The `regression-harness.py` already reads `FIXTURES` and `SCRIPTS_DIR` from `os.environ` (per PRD line 686–687) and uses them when shelling out — that pattern continues to work with relative values because the regression harness itself runs in the same cwd.

---

### M12 — Feature Toggles
**Verdict:** ⚠️ MINOR (path fragility + heavy pattern — works, but add a note)
**Evidence:**
- `when:` supports compound `&&` expressions per `condition-evaluator.ts` line 157 (`splitOutsideQuotes(orClause, '&&')`).
- `$read-flag-recovery.output == 'true'` is a valid atom — matches atomPattern (node id `read-flag-recovery` is lowercase + hyphens, which satisfies the `[a-zA-Z_][a-zA-Z0-9_-]*` regex).
- Adding 6 upstream read-flag bash nodes is heavier than ideal, but it's the only way to gate nodes on external config given Archon has no external-file-read primitive in `when:`.

**Problem:** `$ARCHON_HOME` fragility again, plus the inline `python -c` needs to reference `features.yaml` at a resolvable path.

**BEFORE (PRD §4 M12, lines ~750–761):**
```yaml
- id: read-flag-recovery
  bash: |
    python -c "import yaml,sys; c=yaml.safe_load(open('$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []

- id: phase-1-recovery-diagnose
  command: recovery-diagnose
  when: "$phase-1-compliance.output == 'FAIL' && $read-flag-recovery.output == 'true'"
  depends_on: [phase-1-compliance, read-flag-recovery]
  model: opus
  effort: high
```

**AFTER (replace with this exact block):**
```yaml
- id: read-flag-recovery
  bash: |
    python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []

- id: phase-1-recovery-diagnose
  command: recovery-diagnose
  when: "$phase-1-compliance.output == 'FAIL' && $read-flag-recovery.output == 'true'"
  depends_on: [phase-1-compliance, read-flag-recovery]
  model: opus
  effort: high
```

**Why this works:** Relative path to `features.yaml`. Removed unused `import sys`. `python -c` runs with cwd = workflow repo root (same as any other bash node). PyYAML must be installed — note that the base `python` must have `yaml` importable. If the environment uses `uv`, the read-flag can be rewritten as `uv run --with pyyaml python -c "..."` but that adds overhead per read-flag call. Simpler: tell the owner to `pip install pyyaml` in the Python env Archon invokes.

**Also note (not a code fix — a design flag):** Six read-flag nodes across one workflow is heavy. The PRD itself offers a Phase 1b fallback ("comment out nodes manually until read-flag is ready") in lines 765–766, which is a reasonable first-pass simplification.

---

## Cross-cutting findings

### Copy-don't-overwrite pattern
**Verdict:** ✅ PASS
**Evidence:** Archon's workflow loader (`loader.ts`) discovers YAML files by scanning a directory; commands likewise. Filenames are unique keys. Adding `prd-pipeline-c.yaml` alongside `prd-pipeline-b.yaml` and `-v2.md` copies alongside originals is fully safe — nothing overwrites, nothing shadows, v1 stays callable (per CLAUDE.md: "resolveWorkflowName resolves workflow names via a 4-tier fallback — exact, case-insensitive, suffix, substring"). The rollback plan in PRD §10 is accurate.

No fix required.

---

### Feature toggles
**Verdict:** ✅ PASS with one practical note
**Evidence:** See M12 above. The read-flag-node + `when:` compound pattern is the correct Archon-native way to express config-based toggling. There is no `enabled: false` field on nodes, no external-file-read in `when:`, so this pattern is the only path.

**Practical note:** The `python -c "import yaml; ..."` read-flag assumes PyYAML is installed in whichever Python the bash nodes invoke. If it isn't, add `uv run --with pyyaml` prefix (but that multiplies per-call overhead). Recommended: document a one-time `pip install pyyaml` as a prerequisite.

No code fix beyond the ones already given in M12.

---

### Recovery Pipeline (M9) end-to-end flow
**Verdict:** ✅ PASS (architecture) / ❌ FAIL (execution, until M9 quoting fix applied)
**Evidence:**
- Gate node (exits 0, emits PASS/FAIL on stdout) — ✓ correct, stdout is captured as `$<gate>.output`.
- Recovery branch with `when: "$<gate>.output == 'FAIL'"` — ✓ valid atom expression per condition-evaluator.
- `trigger_rule: all_done` on aggregator — ✓ fires after all upstream settle (completed / failed / skipped). Skipped `$<node>.output` becomes `''` in bash substitution.
- Default `trigger_rule: all_success` on phase-2-execute correctly halts when `phase-1-final-status` exits 1 — ✓.

Once the M9 quoting fix is applied, the full recovery flow (gate → diagnose → fix-prd → execute → regate → final-status → next phase) is executable exactly as the PRD describes.

---

### Per-phase iteration (M4)
**Verdict:** ✅ PASS — manual unroll is the correct choice
**Evidence:** Fully confirmed by reading `schemas/loop.ts`. The Archon `loop:` node is an iterative AI prompt (fields: `prompt`, `until`, `max_iterations`, `fresh_context`, `until_bash`, `interactive`, `gate_message`) — not an array iterator. There is no `for_each`, no `over:`, no `type: parallel`. Manual unroll with explicit `phase-N-*` node IDs is the only option available. PRD lines 230 and 319–320 correctly state this.

No fix required.

---

### Model assignment
**Verdict:** ✅ PASS
**Evidence:** `dagNodeBaseSchema.model = z.string().optional()` — accepts any string. `isModelCompatible()` (cited in schemas/dag-node.ts import line 19) validates provider/model pairs at load time. `sonnet`, `opus`, `haiku` are valid Claude aliases (Archon CLAUDE.md line 486). The PRD correctly avoids literal "Opus 4.7" strings.

No fix required.

---

### Effort level
**Verdict:** ✅ PASS
**Evidence:** `effortLevelSchema = z.enum(['low', 'medium', 'high', 'max'])` (dag-node.ts line 41). Field is `effort` (dag-node.ts line 132). `effort: high` and `effort: medium` used in PRD §15 are both valid.

No fix required.

---

## Test plan findings

### Test A — Gate Script Unit Tests
**Verdict:** ✅ PASS (commands are executable — Python scripts must be written to match the asserted outputs, which is the builder's job)
**Evidence:** Assertions invoke `python .archon/scripts/<name>.py <fixture-dir>` with relative paths, which resolve from the cwd where the builder runs the test. The fixture layout (`.archon/test-fixtures/yt-strategy-lab-fail/`, etc.) is under the workspace root, reachable from cwd.

No fix required at the command level. (The assertions hold only if the builder actually constructs the fixtures and the scripts as specified — that's implementation, not PRD correctness.)

---

### Test B — Red-Team Replay on YT Strategy Lab
**Verdict:** ✅ PASS (conceptually sound; execution availability depends on whether the pre-deploy snapshot was preserved)
**Evidence:** The PRD already flags the snapshot-availability caveat in lines 922–923. If the snapshot exists, the test flow is correct — run `prd-pipeline-c.yaml` from `build-fix-v2` onward against the preserved artifact bundle, observe `compliance-gate.py` emits `FAIL`, observe `when:`-gated recovery activates.

**One implementation note (not a correction):** "Run the v2 pipeline from `build-fix-v2` onward" cannot literally be expressed in Archon — Archon workflows always start at their first topological layer. In practice this means pre-populating `$ARTIFACTS_DIR` with the recorded review outputs so the reviewer nodes have nothing to produce (or creating a pruned variant workflow `prd-pipeline-c-replay.yaml` that starts at `build-fix-v2`). The PRD should clarify which approach the builder takes.

No code snippet to correct; this is a design clarification for the builder.

---

### Test C — Fresh Tiny Build End-to-End
**Verdict:** ✅ PASS
**Evidence:** The input spec (one-page React countdown timer) is small enough to land inside the 40K token estimate. The observable criteria (archive folder exists, INDEX.md updated, CODEBASE_MAP.md exists when M7 toggle on, deferred.md ≤3, lint/typecheck/tests green) are all mechanically checkable.

No fix required.

---

## 🔴 Consolidated fix list — apply-these-edits.md

Six edits total, grouped by PRD section. Hand this chunk to a builder; the result is a PRD that executes correctly.

### Edit 1 — M1 compliance-gate node (PRD §4 M1, replace lines ~113–116)
```yaml
- id: compliance-gate
  bash: python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

### Edit 2 — M2 phase-baseline + full-checkpoint nodes (PRD §4 M2, replace lines ~148–164)
```yaml
- id: phase-baseline
  bash: git rev-parse HEAD
  depends_on: [build-codebase-intelligence]

# ... build-execute-phase runs here ...

- id: full-checkpoint
  bash: |
    set -euo pipefail
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-baseline.output
  timeout: 300000
  depends_on: [compliance-gate]
```

### Edit 3 — M4 phase-N-checkpoint nodes (PRD §4 M4, replace lines ~291–294 and mirror across all phase-N instances)
```yaml
- id: phase-1-checkpoint
  bash: |
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-1-baseline.output
  timeout: 300000
  depends_on: [phase-1-compliance]
```

Also fix the `phase-1-compliance` node in M4 block (PRD line 287) identically to Edit 6 below — relative path, drop `$ARCHON_HOME`.

### Edit 4 — M6 claude-md-presence-check node (PRD §4 M6, replace lines ~403–410)
```yaml
- id: claude-md-presence-check
  bash: |
    set -euo pipefail
    python .archon/scripts/claude-md-audit.py "$ARTIFACTS_DIR"
  depends_on: [phase-3-checkpoint]
```

### Edit 5 — M8 deploy-gate node (PRD §4 M8, replace lines ~490–493)
```yaml
- id: deploy-gate
  bash: python .archon/scripts/deploy-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-final-report]
```

### Edit 6 — M9 gate + recovery-regate + final-status nodes (PRD §4 M9, replace lines ~520–586)

Gate node:
```yaml
- id: phase-1-compliance
  bash: |
    set +e
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-fix]
```

Recovery-regate node:
```yaml
- id: phase-1-recovery-regate
  bash: |
    set +e
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-recovery-execute]
  when: "$phase-1-compliance.output == 'FAIL'"
```

Final-status aggregator (THE CRITICAL ONE):
```yaml
- id: phase-1-final-status
  bash: |
    set -euo pipefail
    if [ $phase-1-compliance.output = PASS ]; then
      echo "PASS"
    elif [ $phase-1-recovery-regate.output = PASS ]; then
      echo "PASS"
    else
      echo "FAIL" >&2
      exit 1
    fi
  depends_on: [phase-1-compliance, phase-1-recovery-regate]
  trigger_rule: all_done
```

### Edit 7 — M10 archive-prd node (PRD §4 M10, replace lines ~648–655)
```yaml
- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

### Edit 8 — M11 regression-harness node (PRD §4 M11, replace lines ~708–714)
```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR=".archon/scripts" \
    python .archon/scripts/regression-harness.py
  depends_on: []
```

### Edit 9 — M12 read-flag-recovery node (PRD §4 M12, replace lines ~750–753)
```yaml
- id: read-flag-recovery
  bash: |
    python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []
```

(Apply the same `.archon/features.yaml` relative-path pattern to the other 5 read-flag nodes M12 implies: `read-flag-archive`, `read-flag-regression`, `read-flag-cartographer`, `read-flag-scoped-claude-md`, `read-flag-build-intelligence`.)

---

## Recommendation

**Apply the 9 edits above, then proceed with Phase 1 as written.**

The PRD's architecture is correct. Node-type choices (bash vs script vs command) are right. `when:` syntax matches Archon's condition-evaluator exactly. `trigger_rule: all_done` + skipped-node semantics for the recovery aggregator is a valid pattern. The `for_each`-doesn't-exist observation is accurate. The copy-don't-overwrite rollback plan is sound. Model/effort YAML is valid.

Two failure modes are in the PRD: one is a substitution-quoting bug present on exactly two mechanisms (M2 full-checkpoint, M9 final-status); the other is `$ARCHON_HOME` fragility scattered across seven bash nodes. Both are mechanical edits — not architectural rethinks. Once applied, the pipeline as written will actually execute end-to-end against Archon's current engine.

Phase 1 is go. No rework needed beyond the copy-paste fixes above.

---

## Optional observations (not blocking)

1. **PyYAML dependency for M12.** The read-flag nodes use `python -c "import yaml; ..."`. If the Python interpreter Archon calls doesn't have PyYAML installed, every read-flag node will fail with `ModuleNotFoundError`. Document as a prerequisite, or wrap the call in `uv run --with pyyaml python -c "..."` (adds per-call overhead — 6 calls × whatever `uv run` bootstrap costs).

2. **Bash availability on Windows.** Archon invokes bash nodes via `execFileAsync('bash', ['-c', script])` (dag-executor.ts line 1362). On Windows, this requires git-bash (or similar) to be on PATH. If bash is missing, every bash node fails with `ENOENT` and the engine emits a clear error — not silent corruption. Document as a prerequisite.

3. **`"Opus 4.7"` nomenclature.** PRD line 509 correctly clarifies that `opus` is the YAML alias and no literal "4.7" string is valid. Good catch already in the PRD.

4. **Test B "run from build-fix-v2 onward."** Archon cannot start a workflow mid-DAG. To execute Test B as described, the builder must either pre-populate `$ARTIFACTS_DIR` so upstream nodes become no-ops, or create a pruned variant `prd-pipeline-c-replay.yaml`. Flag for the builder before they start Test B.

5. **`$DOCS_DIR/..` in the original M2 baseline-capture.** The PRD's pre-fix `git -C "$DOCS_DIR/.." rev-parse HEAD` is a roundabout way to reach the repo root. `$DOCS_DIR` defaults to `docs/`, so the expression resolves to `docs/..` = repo root. But if someone sets `docs.path: /some/absolute/path` in `.archon/config.yaml`, this breaks. The fix given in Edit 2 (`git rev-parse HEAD` with no `-C` flag — uses bash-node cwd) is unambiguously correct regardless of docsDir.

6. **Six read-flag nodes is heavy for Phase 1.** The PRD's own fallback (PRD lines 765–766) — "comment out nodes manually in the YAML" — is a legitimate Phase-1a simplification. Worth raising with the owner as an option, since it removes 6 nodes from the first-pass YAML in exchange for "toggles require a YAML edit instead of a config-file edit."
