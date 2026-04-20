# PRD Validation Report — v3 (Independent Third Review)

**Reviewer:** Claude Opus 4.7 (fresh pass, no prior report read)
**Date:** 2026-04-19
**Scope:** Technical correctness only. Strategy locked per owner instruction.
**Method:** Read Archon engine source first (schemas + dag-executor + condition-evaluator + loader + script-discovery + the real baseline YAML/command files), then validated the PRD line-by-line against that evidence.

**Independence confirmation:** I did not open `HANDOFF.md`, `VALIDATION-REPORT.md`, `VALIDATION-REPORT-v2.md`, or any `*.backup-*.md` file. I only read the live `README.md` PRD and Archon source.

---

## Summary

- Total mechanisms: 12
- PASS: 8 (M1, M2, M3, M4, M6, M7, M8, M9)
- MINOR: 4 (M5, M10, M11, M12)
- FAIL: 0
- AMBIGUOUS: 0
- **Overall verdict: READY — proceed with Phase 1 after applying the 4 minor fixes below.**

The PRD's core architecture is sound. Every major mechanism matches Archon's real schema and executor behavior. The gate/recovery/aggregator pattern is correctly composed. `when:` expressions use supported syntax. `$<node>.output` substitution respects the shellQuote single-quote wrapping rule. Model aliases and `effort` values are real.

The 4 minor findings are all small: one prompt-variable mistake, one missing status-threading, one dependency assumption, and one node that shouldn't be in the main workflow file. All four have copy-paste fixes below.

---

## Top 3 Blockers

**None.** Nothing in the PRD blocks Phase 1 execution as-is. The 4 MINOR findings are quality/correctness issues that should be fixed but do not prevent the pipeline from running.

If you want a prioritized order:
1. **M12 PyYAML** — will fail on a machine without PyYAML installed; easy fix below.
2. **M11 regression-harness** — if left as-is it will re-run on every pipeline invocation, wasting tokens; easy fix below.
3. **M5 `$PHASE_FILE`** — will result in the LLM seeing the literal string `$PHASE_FILE` instead of a real file path; easy fix below.

---

## Per-mechanism findings

### M1 — Compliance Gate Script

**Verdict:** ✅ PASS

**Evidence:**
- `dag-executor.ts:1348` — `$ARTIFACTS_DIR` is substituted in bash nodes via `substituteWorkflowVariables`.
- `dag-executor.ts:1362` — bash runs via `execFileAsync('bash', ['-c', finalScript], { cwd, timeout })`.
- `schemas/dag-node.ts:179–182` — `bashNodeSchema` accepts `bash: string` + `timeout: number` (ms).
- `prd-pipeline-b.yaml:184` — real upstream node id is `build-fix-issues`. The PRD's `depends_on: [build-fix-issues]` matches.

**Problem:** None.

The PRD's YAML block is exactly the shape Archon's loader expects. Bash wrapper correctly passes `$ARTIFACTS_DIR` (literal text substitution) as `sys.argv[1]` to Python. `timeout: 60000` (60s) is within the positive-number requirement in `dag-node.ts:444`.

---

### M2 — Full Checkpoint Script

**Verdict:** ✅ PASS

**Evidence:**
- `dag-executor.ts:183–184` — `shellQuote` wraps substituted values in single quotes.
- `dag-executor.ts:1357` — `substituteNodeOutputRefs(substitutedScript, nodeOutputs, true)` — bash nodes get `escapedForBash=true`, so `$phase-baseline.output` becomes `'abc123sha'` (already single-quoted).
- `loader.ts:144` regex — `/\$([a-zA-Z_][a-zA-Z0-9_-]*)\.output/g` — allows hyphens in node ids. `phase-baseline` and `phase-1-baseline` both match.
- The PRD correctly leaves `$phase-baseline.output` **unwrapped by outer quotes** — good.

**Problem:** None. `python ... "/real/path" 'abc123sha'` is the expanded command — valid bash, correct arg order.

---

### M3 — Stage 10 Prompt Tightening

**Verdict:** ✅ PASS

**Evidence:** This is text editing on two markdown prompt files. No engine-level correctness question. The mandatory-contract block and two-strike-rule rewording are prose changes that the prompt consumers (Claude agents) will read.

**Problem:** None.

---

### M4 — Per-Phase YAML Loop

**Verdict:** ✅ PASS

**Evidence:**
- `schemas/loop.ts:6–31` — `loopNodeConfigSchema` has no `over:` / `as:` / `body:` / `for_each:` fields. PRD's claim that Archon lacks array iteration is correct.
- `schemas/dag-node.ts:283–291` — the seven node types (command, prompt, bash, loop, approval, cancel, script) are the exhaustive list. No parallel/foreach types exist.
- `dag-executor.ts` topological execution — independent nodes in the same layer run concurrently; `depends_on` serializes.
- `prd-pipeline-b.yaml:24–211` — shows the exact same linear-with-parallel-reviewers pattern the PRD emulates.

**Problem:** None. The unrolled 3-phase YAML respects depends_on edges, uses `context: fresh` per phase (S5 compliance), and relies on default `trigger_rule: all_success` to halt downstream phases on gate failure. This is the only way to get per-phase iteration in Archon today.

---

### M5 — Test Writer Node

**Verdict:** ⚠️ MINOR

**Problem:** The PRD's prompt file says:
> `$PHASE_FILE` — the phase spec including all WALL steps

`$PHASE_FILE` is **not a built-in Archon variable**. The substitution map in `executor-shared.ts:256–298` covers exactly: `$WORKFLOW_ID`, `$ARTIFACTS_DIR`, `$BASE_BRANCH`, `$DOCS_DIR`, `$1`, `$2`, `$3`, `$ARGUMENTS`, `$LOOP_USER_INPUT`, `$REJECTION_REASON`. Nothing else is substituted. The LLM will see the literal string `$PHASE_FILE` in its prompt, which will confuse it.

**Evidence:** `executor-shared.ts:269–298` — `substituteWorkflowVariables` only recognizes the variables listed above.

**BEFORE (current PRD §4 M5, lines ~345–348):**

```markdown
## Inputs
- `$PHASE_FILE` — the phase spec including all WALL steps
- `$ARTIFACTS_DIR/review-tests.md` — flagged coverage gaps (if already built)
```

**AFTER (replace with this exact block):**

```markdown
## Inputs
- `$ARTIFACTS_DIR/phases/` — the generated phase spec files (one `.md` per phase). Read the one matching the phase id passed in `$ARGUMENTS` (for example `phase-1.md` when `$ARGUMENTS` is `phase-1`).
- `$ARTIFACTS_DIR/review-tests.md` — flagged coverage gaps (if already built)
```

And in the node wiring, pass the phase id as an argument:

**BEFORE (current PRD §5, Phase 2 wiring, lines ~806–812):**

```yaml
- id: phase-N-test-writer
  command: test-writer
  depends_on: [phase-N-execute]
  model: sonnet
  context: fresh
```

**AFTER (replace with this exact block — example for phase 1):**

```yaml
- id: phase-1-test-writer
  command: test-writer
  prompt: "phase-1"
  depends_on: [phase-1-execute]
  model: sonnet
  context: fresh
```

**Why this works:** `$ARGUMENTS` is a real Archon-substituted variable (`executor-shared.ts:269+`) populated from the `prompt:` field on command nodes (or positional args). The test-writer prompt will receive `phase-1` as `$ARGUMENTS` and read `$ARTIFACTS_DIR/phases/phase-1.md`.

*Caveat: confirm the actual convention used by Stage 10 for where phase files land (it may be a different subpath). If stage-10-output-generator writes phase files elsewhere, point the prompt at that path. The core fix — kill `$PHASE_FILE`, use a real substitutable variable — stands regardless.*

---

### M6 — Scoped CLAUDE.md Auto-Attach

**Verdict:** ✅ PASS

**Evidence:**
- `command:` nodes + `bash:` audit nodes are both valid. Schema allows `depends_on` chaining (`dag-node.ts:115`).
- The PRD explicitly calls this a DOOR (soft guidance) and uses an observation-only audit node. Honest.
- `python .archon/scripts/claude-md-audit.py "$ARTIFACTS_DIR"` follows the same pattern as M1.

**Problem:** None. The `set -euo pipefail` prelude works under git-bash on Windows.

---

### M7 — Codebase Cartographer

**Verdict:** ✅ PASS

**Evidence:**
- `dag-node.ts:147–159` — `commandNodeSchema` accepts `command: string` + base fields.
- `model: haiku` — valid Claude alias per `prd-pipeline-b.yaml:198` (already in use for build-final-report).
- `context: fresh` — valid enum per `dag-node.ts:120`.

**Problem:** None.

---

### M8 — Pre-Deploy Gate + Deferred Budget

**Verdict:** ✅ PASS

**Evidence:** Same pattern as M1. `depends_on: [build-final-report]` matches the real node id in `prd-pipeline-b.yaml:195`.

**Problem:** None.

---

### M9 — Recovery Pipeline

**Verdict:** ✅ PASS — the most intricate mechanism in the PRD, and it composes correctly.

**Evidence (this mechanism required the most verification):**
- **Gate exits 0, emits PASS/FAIL on stdout:** `executeBashNode` captures stdout as node output (`dag-executor.ts:1368`). Downstream `when:` expressions read that via the condition-evaluator.
- **`when:` syntax:** `condition-evaluator.ts:87–88` — atomPattern is `/^\$([a-zA-Z_][a-zA-Z0-9_-]*)\.output(?:\.([a-zA-Z_][a-zA-Z0-9_]*))?\s*(==|!=|<=|>=|<|>)\s*'([^']*)'$/`. The PRD's `"$phase-1-compliance.output == 'FAIL'"` matches exactly. Single quotes on the RHS are required — the PRD does this correctly.
- **Hyphens in node ids:** allowed by both loader regex and condition-evaluator regex.
- **`trigger_rule: all_done` for aggregator:** confirmed real — `schemas/dag-node.ts:24–29` defines `all_done` as a valid trigger rule. Skipped + completed nodes both count as "settled," so the aggregator fires whether recovery ran or not.
- **`shellQuote` in aggregator:** the aggregator uses `[ $phase-1-compliance.output = PASS ]`. After substitution: `[ 'PASS' = PASS ]` (or `[ '' = PASS ]` if the node was skipped). Both are valid POSIX test expressions and evaluate correctly.
- **Compound `when:` (for M12 integration):** `condition-evaluator.ts:153–170` implements `&&` and `||` with AND higher precedence. The PRD's `"$phase-1-compliance.output == 'FAIL' && $read-flag-recovery.output == 'true'"` is valid.
- **`effort: high` + `model: opus`:** both valid — `dag-node.ts:41` (`effortLevelSchema`) and the model alias list.

**Problem:** None. The architectural note in the PRD about "why it's wired this way" is accurate.

**Note (not a bug):** the aggregator's `elif` branch uses `[ $phase-1-recovery-regate.output = PASS ]`. When initial compliance passed, recovery-regate was skipped and has no entry in `nodeOutputs` → `substituteNodeOutputRefs` returns `''` → the expansion becomes `[ '' = PASS ]` → false → drops to `else echo FAIL; exit 1`. But that `else` is only reached if `$phase-1-compliance.output = PASS` was also false. So the logic still works: if initial gate passed, the first `if` fires and we exit with PASS. The else branch only triggers when both are non-PASS, which is the actual failure mode. Correct.

---

### M10 — PRD Archive

**Verdict:** ⚠️ MINOR

**Problem:** The bash node hardcodes the status string `"shipped"`:

```bash
python .archon/scripts/archive-prd.py \
  "$ARTIFACTS_DIR" \
  "$BASE_BRANCH" \
  "shipped"
```

But the archive script is supposed to record one of `shipped / failed / recovered` (per PRD §4 M10 bullet: "status (shipped / failed / recovered)"). Because `archive-prd` hangs off `depends_on: [build-deploy]` with default `trigger_rule: all_success`, the node only runs on a successful deploy, so "shipped" is technically correct for the happy path — but recovery runs will also label as "shipped" (since recovery-PASS still reaches deploy), erasing the distinction.

**Evidence:** `prd-pipeline-b.yaml` structure + PRD's own §4 M10 contract. The script receives a static string, so it has no way to know whether recovery ran.

**BEFORE (current PRD §4 M10, lines ~646–653):**

```yaml
- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

**AFTER (replace with this exact block):**

```yaml
# Upstream aggregator that reports whether any recovery ran this build.
- id: recovery-status-summary
  bash: |
    set -euo pipefail
    # Look at all phase-N-final-status outputs. If any recovery-regate output is non-empty
    # (i.e., recovery actually executed), mark the run as "recovered". Otherwise "shipped".
    if ls "$ARTIFACTS_DIR"/recovery-*/ 2>/dev/null | head -1 >/dev/null; then
      echo "recovered"
    else
      echo "shipped"
    fi
  depends_on: [build-deploy]

- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      $recovery-status-summary.output
  depends_on: [recovery-status-summary]
```

**Why this works:** `$recovery-status-summary.output` is shellQuoted automatically (`dag-executor.ts:183,1357`), so the Python script receives `'shipped'` or `'recovered'` as a properly-quoted argv[3]. No outer quotes needed. `recovery-*/` subfolder presence is a simple filesystem signal that recovery executed.

---

### M11 — Regression Harness

**Verdict:** ⚠️ MINOR

**Problem:** The PRD places the regression-harness node inside `prd-pipeline-c.yaml` with `depends_on: []`. A node with no dependencies is a **root node** and runs on every pipeline invocation. The author's comment says "standalone — invoked manually or by a separate workflow," but putting it in the main pipeline YAML contradicts that — every `/workflow run prd-pipeline-c` will execute this node, spending tokens and time on regression tests before the real build starts.

**Evidence:** `dag-executor.ts` topological execution — `depends_on: []` → root node → scheduled at layer 0 → always runs unless `when:` blocks it.

**BEFORE (current PRD §4 M11, lines ~705–712):**

```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR=".archon/scripts" \
    python .archon/scripts/regression-harness.py
  depends_on: []   # standalone — invoked manually or by a separate workflow
```

**AFTER (replace with this exact block — move to a separate workflow file):**

Create a new file `.archon/workflows/regression-harness.yaml`:

```yaml
name: regression-harness
description: |
  Self-test suite for the Archon pipeline. Runs Tests A/B/C against the
  current state of .archon/scripts/ and fails if any gate behaves wrong.
  Invoke manually or from CI — not part of prd-pipeline-c.

nodes:
  - id: regression-run
    bash: |
      FIXTURES=".archon/test-fixtures" \
      SCRIPTS_DIR=".archon/scripts" \
      python .archon/scripts/regression-harness.py
    timeout: 300000
```

And **remove** the `regression-harness` node from `prd-pipeline-c.yaml` entirely. Invoke it separately:
```
archon workflow run regression-harness
```

**Why this works:** Keeping regression tests out of the main build pipeline matches the PRD's stated intent ("invoked manually or by a separate workflow") and prevents accidental token spend on every build. Workflow files are discovered independently by `workflow-discovery.ts` — both files coexist.

---

### M12 — Feature Toggles

**Verdict:** ⚠️ MINOR

**Problem:** The read-flag bash node uses:

```yaml
bash: |
  python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
```

`import yaml` requires **PyYAML** installed in the system Python environment. On a fresh Windows install (the owner's target), `python` may resolve to the Microsoft Store stub (which launches the installer) or to a Python without PyYAML. The node will fail with `ModuleNotFoundError: No module named 'yaml'`.

Archon's bash nodes do **not** run inside `uv run`, so there's no automatic dependency install. `execFileAsync('bash', ['-c', finalScript], { cwd, timeout })` just invokes whatever `python` resolves to.

**Evidence:** `dag-executor.ts:1362` — no env overrides, no uv wrapper. Plain bash execution.

**BEFORE (current PRD §4 M12, lines ~749–751):**

```yaml
- id: read-flag-recovery
  bash: |
    python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []   # or earliest possible ancestor
```

**AFTER (replace with this exact block — use uv with PyYAML as a declared dep):**

```yaml
- id: read-flag-recovery
  bash: |
    uv run --with pyyaml python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []
```

Apply the same `uv run --with pyyaml` prefix to every `read-flag-*` bash node (6 total per the PRD).

**Why this works:** Archon's architecture already requires `uv` to be installed (per the `uv` runtime in script nodes, `script-discovery.ts:34–38`). `uv run --with pyyaml python -c "..."` auto-installs PyYAML into an ephemeral venv and runs the one-liner. No system Python dependency management needed.

**Alternative (stdlib-only, slightly more brittle but zero deps):**

```yaml
- id: read-flag-recovery
  bash: |
    python -c "import re,sys; t=open('.archon/features.yaml').read() if __import__('os').path.exists('.archon/features.yaml') else ''; m=re.search(r'^recovery_pipeline:\s*(true|false)', t, re.M); print((m.group(1) if m else 'true').lower())"
  depends_on: []
```

This parses the YAML flag with a regex — fragile (breaks on unusual YAML formatting) but needs no PyYAML.

**Recommendation:** Use the `uv run --with pyyaml` form. Cleaner and more robust.

---

## Cross-cutting findings

### Copy-don't-overwrite pattern

**Verdict:** ✅ PASS

**Evidence:** `workflow-discovery.ts` and the command loader both discover files by filename. `prd-pipeline-b.yaml` and `prd-pipeline-c.yaml` coexist. `build-fix.md` and `build-fix-v2.md` coexist — AI command resolution goes by the exact name referenced in `command:`. Rollback is genuinely safe: leaving v1 files untouched means you can switch which workflow you invoke without rolling back anything.

No correction needed.

### Feature toggles (M12 mechanism)

**Verdict:** ⚠️ MINOR — see M12 above for the PyYAML fix. The overall pattern (upstream read-flag node emitting `true`/`false` + downstream `when:` conditions on `.output`) is syntactically valid per `condition-evaluator.ts:87–88`.

### Recovery pipeline composition (M9)

**Verdict:** ✅ PASS — covered in M9. The four-node-per-phase pattern (gate → diagnose → fix-prd → execute → regate → aggregator) is sound. `trigger_rule: all_done` on the aggregator is the right choice for merging the two success paths. The architectural note in the PRD accurately describes why this works.

### Per-phase iteration (M4)

**Verdict:** ✅ PASS — the manual unroll is the only correct approach given Archon has no `for_each`. Confirmed against `schemas/loop.ts` (no array-iteration primitives) and the exhaustive node list in `schemas/dag-node.ts`.

### Model assignment (§15)

**Verdict:** ✅ PASS

**Evidence:**
- `sonnet`, `opus`, `haiku` — all valid Claude aliases per Archon's own CLAUDE.md and actual usage in `prd-pipeline-b.yaml:16, 198`.
- `effort: medium` and `effort: high` — both valid per `dag-node.ts:41` (`effortLevelSchema = z.enum(['low', 'medium', 'high', 'max'])`).
- No literal "Opus 4.7" string anywhere in the PRD YAML. Good.
- Per-node `model:` overrides workflow-level model — confirmed in `dag-executor.ts:363–398` (`resolveNodeProviderAndModel`).

### Effort level

**Verdict:** ✅ PASS — `effort` is a real field on `dagNodeBaseSchema` (line 132). `'high'` is a valid enum value. Only applies to AI nodes (Claude), which is exactly where the PRD uses it.

---

## Test plan findings

### Test A — Gate Script Unit Tests

**Verdict:** ✅ PASS (commands are executable once scripts + fixtures exist)

All 6 assertions invoke `python .archon/scripts/<name>.py <arg>` — same Python invocation pattern as the bash nodes in the real pipeline, so if Test A passes, the real nodes pass by construction. `python` must be in PATH (same assumption as the pipeline itself).

**Caveat:** Test A depends on fixture folders (`yt-strategy-lab-fail/`, `task-manager-pass/`, `broken-phase/`) that do not yet exist. The PRD acknowledges this — creating fixtures is Phase 1 work. Document only.

### Test B — Red-Team Replay on YT Strategy Lab

**Verdict:** ✅ PASS (conceptually sound — contingent on artifact preservation)

The PRD correctly flags the "availability caveat" (needs preserved pre-deploy snapshot). Step 2's "run from `build-fix-v2` onward" requires Archon's resume behavior — `/workflow resume` re-runs a failed run but skipping completed nodes. This pattern works for the described purpose.

**Minor note (not a correction):** The PRD says "Run the v2 pipeline from `build-fix-v2` onward." Archon has no "start from node X" command — the only way to skip upstream work is to have the upstream nodes already exist as completed in a workflow run. If the YT Strategy Lab snapshot includes a workflow run record with completed upstream nodes, resume works. If it's only file artifacts, you'd need to stub the upstream nodes as trivially-passing for this test. Operationally OK either way; just flagging.

### Test C — Fresh Tiny Build End-to-End

**Verdict:** ✅ PASS — smoke test, tests the real pipeline end-to-end on a tiny input.

No corrections needed. The success criteria (archive folder exists, INDEX.md updated, CODEBASE_MAP.md present if toggle on, deferred.md ≤3 entries) are all file-system observable.

### Deliberate break-and-fix (bonus)

**Verdict:** ✅ PASS — a good regression confidence check.

---

## 🔴 Final corrected PRD sections — apply-these-edits

Only 4 edits are required. Group them and hand to the builder in one pass.

### Edit 1 — M5 Test Writer prompt inputs and wiring

**PRD §4 M5, lines ~345–348 — replace:**

```markdown
## Inputs
- `$PHASE_FILE` — the phase spec including all WALL steps
- `$ARTIFACTS_DIR/review-tests.md` — flagged coverage gaps (if already built)
```

**with:**

```markdown
## Inputs
- `$ARTIFACTS_DIR/phases/` — the generated phase spec files (one `.md` per phase). Read the one matching the phase id passed in `$ARGUMENTS` (for example `phase-1.md` when `$ARGUMENTS` is `phase-1`).
- `$ARTIFACTS_DIR/review-tests.md` — flagged coverage gaps (if already built)
```

**PRD §5 Phase 2 wiring, lines ~806–812 — replace:**

```yaml
- id: phase-N-test-writer
  command: test-writer
  depends_on: [phase-N-execute]
  model: sonnet
  context: fresh
```

**with (example for phase 1, repeat per phase with ids prefixed):**

```yaml
- id: phase-1-test-writer
  command: test-writer
  prompt: "phase-1"
  depends_on: [phase-1-execute]
  model: sonnet
  context: fresh
```

### Edit 2 — M10 archive-prd status threading

**PRD §4 M10, lines ~646–653 — replace:**

```yaml
- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

**with:**

```yaml
- id: recovery-status-summary
  bash: |
    set -euo pipefail
    if ls "$ARTIFACTS_DIR"/recovery-*/ 2>/dev/null | head -1 >/dev/null; then
      echo "recovered"
    else
      echo "shipped"
    fi
  depends_on: [build-deploy]

- id: archive-prd
  bash: |
    python .archon/scripts/archive-prd.py \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      $recovery-status-summary.output
  depends_on: [recovery-status-summary]
```

### Edit 3 — M11 move regression harness out of pipeline

**PRD §4 M11, lines ~705–712 — DELETE this block from `prd-pipeline-c.yaml`:**

```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR=".archon/scripts" \
    python .archon/scripts/regression-harness.py
  depends_on: []
```

**and instead create `.archon/workflows/regression-harness.yaml` containing:**

```yaml
name: regression-harness
description: |
  Self-test suite for the Archon pipeline. Runs Tests A/B/C against the
  current state of .archon/scripts/ and fails if any gate behaves wrong.
  Invoke manually or from CI — not part of prd-pipeline-c.

nodes:
  - id: regression-run
    bash: |
      FIXTURES=".archon/test-fixtures" \
      SCRIPTS_DIR=".archon/scripts" \
      python .archon/scripts/regression-harness.py
    timeout: 300000
```

Invoke with `archon workflow run regression-harness`.

### Edit 4 — M12 feature-toggle read-flag nodes use uv

**PRD §4 M12, lines ~749–751 (and all other `read-flag-*` nodes) — replace:**

```yaml
- id: read-flag-recovery
  bash: |
    python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []
```

**with (apply this prefix to all 6 read-flag nodes):**

```yaml
- id: read-flag-recovery
  bash: |
    uv run --with pyyaml python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []
```

---

## Optional observations (not required for Phase 1)

1. **`$WORKFLOW_ID` for archive paths.** M10's archive destination `docs/generated-prds/{YYYY-MM-DD}__{build-name}/` uses `$BASE_BRANCH` as a stand-in for "build name." If two builds happen on the same branch on the same day, they'll collide. Consider `{YYYY-MM-DD}__{WORKFLOW_ID}__{BASE_BRANCH}/` or similar. Not blocking.

2. **`recovery-status-summary` scope (Edit 2).** My fix checks for any `recovery-*/` directory. If recovery ran in phase 1 but the final build still shipped, that's legitimately `recovered`. If a future phase wants to distinguish "recovered once" vs "recovered thrice" the summary node can be elaborated. Sufficient for Phase 1.

3. **Retry on gate nodes.** Archon supports `retry:` on bash nodes (`schemas/retry.ts` via `stepRetryConfigSchema`). If transient bash failures are a worry (e.g., filesystem races), the gate nodes could add a small retry. Not in scope for this PRD, but available.

4. **`idle_timeout` on command nodes.** The baseline workflow uses `idle_timeout: 600000` on heavy stages. The PRD's new command nodes (`recovery-diagnose`, `recovery-fix-prd`, `recovery-execute`) don't specify one. Opus-high work can stall; consider adding `idle_timeout: 900000` (15 min) to the three recovery command nodes. Not blocking — the executor has sane defaults.

---

## Recommendation

**Proceed with Phase 1 after applying Edits 1–4 above.**

The PRD's architecture is technically sound. Every claim about Archon's engine that I verified (node types, schema fields, substitution behavior, shell quoting, when-expression syntax, trigger rule semantics, model aliases, effort values, copy-don't-overwrite discovery, script-node arg limitation, no `for_each`) checks out against the real source code. The recovery pipeline in M9 — the most complex mechanism — composes correctly.

The 4 MINOR fixes are small, mechanical edits. None require rework of the PRD's strategy. After applying them, hand the spec to the builder and execute Phase 1.

If the builder hits any behavior in the engine that contradicts this report, stop and walkie-talkie me — I'll have missed something. But based on the source I read (8+ Archon files end-to-end and the real baseline YAML/command files), the PRD is ready.
