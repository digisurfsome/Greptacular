# PRD Validation Report — Archon Build Upgrade

**Reviewer:** Independent technical review against Archon source at `C:\Users\lober\archon\Archon\`
**Date:** 2026-04-19
**Scope:** Technical correctness of PRD + HANDOFF.md corrections. Strategy is locked and not reviewed.

---

## Summary

- Total mechanisms: 12
- PASS: 3 (M1, M8, M10 — with HANDOFF.md's bash→Python correction applied)
- MINOR: 3 (M3, M5, M11)
- FAIL: 5 (M2, M4, M6, M7, M12)
- AMBIGUOUS / cross-cutting: 1 (M9 — requires architectural change)

**Overall verdict: NEEDS REVISION**

The PRD's strategy is sound. HANDOFF.md catches three blockers (paths, bash→Python, copy-don't-overwrite). However, HANDOFF.md still leaves several mechanism-level technical errors unfixed. After applying the fixes below, Phase 1 can execute.

---

## Top 3 blockers

1. **Scripts can't take CLI args.** Archon runs script nodes as `uv run script.py` (no trailing args — see `dag-executor.ts` line 1569). Any script that depends on `$ARTIFACTS_DIR`, `$PROJECT_DIR`, `$BASELINE_SHA` etc. must read them from environment variables set via `$ARTIFACTS_DIR` variable substitution baked into a **bash wrapper** OR the script must read them from env vars that Archon auto-injects. The PRD's script signatures (`script.sh ARG1 ARG2 ARG3`) will not work as YAML script nodes. This affects M1, M2, M8, M10, M11.
2. **Recovery Pipeline (M9) cannot trigger on node failure.** Archon has no `on_failure:` branch. `when:` expressions only compare node *outputs*, not states. `trigger_rule: all_done` runs regardless of success, but a recovery node still can't inspect whether upstream failed. The fix requires restructuring M9 as a wrapper bash node that runs the gate AND conditionally invokes recovery, OR making each gate write its result to stdout and having recovery check that with `when:`.
3. **`for_each` loops do NOT exist in Archon (M4).** Archon's `loop:` node is an AI-prompt loop (run a Claude prompt until it emits a completion signal string). It does not iterate over arrays. Per-phase isolation must be done by the fallback approach HANDOFF mentions ("unroll manually") — generate N phase-groups at pipeline-build time, OR drive per-phase iteration by a single `loop:` node whose prompt reads `phases/N.md` and whose `until:` signal is "ALL_PHASES_DONE". Both require substantial PRD rework.

---

## Per-mechanism findings

### M1 — Compliance Gate Script

**Verdict:** MINOR (PASS once HANDOFF correction + arg-passing fix applied)

**Evidence:**
- `script-discovery.ts` lines 34-38: runtime map is `.ts/.js → bun`, `.py → uv`. No `.sh` support.
- `dag-executor.ts` line 1569: named uv scripts invoked as `uv run --with <deps> <path>`. **No trailing positional args are passed to the script.**
- `dag-executor.ts` line 1362: bash nodes DO support inline scripts via `bash -c`, and variable substitution (line 1348) expands `$ARTIFACTS_DIR` before execution.

**Problem:** HANDOFF says translate the bash to Python. Fine. But the PRD's script takes `$ARTIFACTS_DIR` as argv[1]. Archon scripts receive NO argv. The Python script would need to read an env var, or — cleaner — use a bash node that inlines `$ARTIFACTS_DIR` before calling `python .archon/scripts/compliance-gate.py <path>`.

**BEFORE (PRD §4 M1 YAML reference from HANDOFF):**
```yaml
- id: compliance-gate
  script: compliance-gate
  runtime: uv
  depends_on: [build-fix]
```

**AFTER (replace with this exact block):**
```yaml
- id: compliance-gate
  bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

Reason: bash node supports `$ARTIFACTS_DIR` substitution (dag-executor.ts line 1348-1356) AND lets you pass CLI args. Depends_on ID corrected to `build-fix-issues` to match prd-pipeline-b.yaml line 184.

Alternative (stay inside script node, require script to read env): change the script node `deps:` list or have the script read `os.environ['ARTIFACTS_DIR']` and pre-set it in a wrapper bash node. The bash-wrapper approach above is simpler.

**Bash script body itself:** the PRD's bash logic in §4 M1 (lines 101-136) is shell-correct but uses `grep -E`, `wc`, `[[ ]]`, `$((…))`. On Windows this works only if `bash` resolves to git-bash (standard on Windows dev boxes). HANDOFF already translates to Python; keep that translation. Python version is fine, but it should read `sys.argv[1]` as the artifacts dir.

---

### M2 — Full Checkpoint Script

**Verdict:** FAIL

**Evidence:**
- Takes 3 positional args (`PHASE_DIR`, `PROJECT_DIR`, `BASELINE_SHA`). Script nodes can't receive them (see M1 evidence).
- `cd "$PROJECT_DIR"` in a bash node has no meaning — each bash invocation spawns fresh with `cwd` set by Archon (dag-executor.ts line 1363). The PROJECT_DIR is whatever the Archon workflow's cwd is at runtime; you can still `cd` inside the bash script, but only relative to already-accessible paths.
- `$BASELINE_SHA` — Archon does NOT define this variable. Archon supports `$ARTIFACTS_DIR`, `$WORKFLOW_ID`, `$BASE_BRANCH`, `$DOCS_DIR`, `$LOOP_USER_INPUT`, `$REJECTION_REASON` only (see Archon CLAUDE.md lines 668-673, executor-shared.ts). `$BASELINE_SHA` will be left as the literal text "$BASELINE_SHA".

**Problem:** The script needs BASELINE_SHA to diff files. Two ways to get one: (a) capture it in a prior bash node's stdout and reference via `$<nodeid>.output`, or (b) compute it inside the checkpoint script with `git rev-parse HEAD~N`. Option (a) is cleaner.

**BEFORE (PRD §4 M2):**
```yaml
- id: full-checkpoint
  type: script
  script: .archon/scripts/full-checkpoint.sh
  args: ["$PHASE_DIR", "$PROJECT_DIR", "$BASELINE_SHA"]
  depends_on: [compliance-gate]
```

**AFTER (replace with this exact block):**
```yaml
# Capture the baseline SHA before the phase runs.
- id: phase-baseline
  bash: git -C "$DOCS_DIR/.." rev-parse HEAD
  depends_on: [build-codebase-intelligence]

# ... build-execute-phase runs here ...

# Checkpoint: invoke the Python translation of full-checkpoint.sh,
# passing the captured baseline via node-output substitution.
- id: full-checkpoint
  bash: |
    set -euo pipefail
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/full-checkpoint.py" \
      "$ARTIFACTS_DIR" \
      "$phase-baseline.output"
  timeout: 300000
  depends_on: [compliance-gate]
```

Reason: `$phase-baseline.output` is a node-output reference Archon substitutes via `substituteNodeOutputRefs` (dag-executor.ts line 195-200). Passing `escapedForBash=true` (line 1357) single-quotes the value for safe bash interpolation. PHASE_DIR folds into ARTIFACTS_DIR; the Python script can derive `files_allowed.json` path from that. PROJECT_DIR is the workflow cwd (automatic in bash nodes). `npm run lint / npm test / tsc` in the Python script is fine — just invoke via `subprocess.run` inside the .py.

**Additional issue:** The PRD's bash script uses `jq`, `comm`, process substitution (`<(echo ...)`). These are standard on git-bash/Linux but not always reliable in CI. The Python translation in `full-checkpoint.py` eliminates that — use Python's `json` module for `files_allowed.json` and `set` difference for the diff.

---

### M3 — Stage 10 Prompt Tightening

**Verdict:** MINOR — HANDOFF correctly says create `-v2.md` copies, but PRD §5 lists the wrong filenames.

**Evidence:** HANDOFF section 3 lists `build-fix-v2.md`, `prd-stage-10-v2.md`. PRD §5 Phase 1 "Files to edit" still says `stage-10.md` and `build-fix.md`.

**BEFORE (PRD §5 Phase 1 "Files to edit"):**
```
- `.archon/commands/stage-10.md` (remove exemption language)
- `.archon/commands/build-fix.md` (if separate from Stage 10; ALSO change model: sonnet → opus)
- `.archon/workflows/prd-pipeline-b.yaml` (insert gate nodes + recovery branch + archive step)
```

**AFTER (replace with this exact block):**
```
Per HANDOFF.md §2 Correction B — do NOT edit the originals. Create copies:

Files to CREATE (not edit):
- `.archon/commands/prd-stage-10-v2.md` — copy of prd-stage-10.md with exemption language removed
- `.archon/commands/build-fix-v2.md` — copy of build-fix.md with mandatory contract block added; pipeline YAML assigns model: opus to this node
- `.archon/workflows/prd-pipeline-c.yaml` — copy of prd-pipeline-b.yaml with gate/recovery/archive nodes inserted and command: references updated to the `-v2` variants
```

**Extra note on the contract block (PRD §4 M3):** The markdown block is copy-pasteable. No fix needed. The two-strike rule rewording is fine as prose.

**Also:** Run these greps as success-criteria checks after the edit (PRD §4 M3 "Success criteria" is correct):
```bash
grep -rn "separate task" .archon/commands/   # expect 0
grep -rn "defer to human" .archon/commands/  # expect 0
```

---

### M4 — Per-Phase YAML Loop

**Verdict:** FAIL (as specified — the syntax shown does not exist)

**Evidence:**
- `schemas/loop.ts` lines 6-31: the only `loop:` node is an AI iteration — fields are `prompt`, `until`, `max_iterations`, `fresh_context`, `until_bash`, `interactive`, `gate_message`. There is no `over:`, no `as:`, no `body:`, no `for_each:`, no `type: parallel`, no `type: for_each`.
- `dag-node.ts` — node types are exactly: command, prompt, bash, script, loop, approval, cancel. `type:` is NOT a field; mode is determined by which of those keys is present.

**Problem:** The PRD's YAML in §4 M4 is entirely fictional syntax. Archon will reject it at load time.

**Two working alternatives:**

**Option A — Unroll manually (recommended, matches HANDOFF fallback):** Stage 10 emits an intermediate manifest at `$ARTIFACTS_DIR/phases.json`. A pre-step bash node reads the manifest and emits ready-made YAML, OR Stage 10 writes the complete `prd-pipeline-c.yaml` itself with 3 unrolled phase groups. The latter is simpler.

**Option B — Single AI loop node iterates phases:** One `loop:` node whose prompt says "read phases/next.md, do the work, run the gate, when all phases processed output ALL_DONE". AI decides when done. Downside: loses parallel review fan-out per phase.

**BEFORE (PRD §4 M4 lines 262-371) — the entire `for_each` block is invalid. Delete it.**

**AFTER (replace with Option A — unrolled example for a 3-phase build):**
```yaml
# Only the per-phase section shown. Stages 0-10 unchanged.
nodes:
  # ... stages 0-10 unchanged ...

  - id: build-codebase-intelligence
    command: build-codebase-plan
    depends_on: [stage-10-output-generator]
    context: fresh
    idle_timeout: 600000

  # ========= PHASE 1 =========
  - id: phase-1-baseline
    bash: git rev-parse HEAD
    depends_on: [build-codebase-intelligence]

  - id: phase-1-execute
    command: build-implement
    depends_on: [phase-1-baseline]
    model: sonnet
    context: fresh
    idle_timeout: 900000

  - id: phase-1-review-correctness
    command: build-review-correctness
    depends_on: [phase-1-execute]
    model: sonnet
    context: fresh
  - id: phase-1-review-failures
    command: build-review-failures
    depends_on: [phase-1-execute]
    model: sonnet
    context: fresh
  - id: phase-1-review-tests
    command: build-review-tests
    depends_on: [phase-1-execute]
    model: sonnet
    context: fresh
  - id: phase-1-review-simplify
    command: build-review-simplify
    depends_on: [phase-1-execute]
    model: sonnet
    context: fresh

  - id: phase-1-fix
    command: build-fix-v2
    depends_on: [phase-1-review-correctness, phase-1-review-failures, phase-1-review-tests, phase-1-review-simplify]
    model: opus
    context: fresh

  - id: phase-1-compliance
    bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
    timeout: 60000
    depends_on: [phase-1-fix]

  - id: phase-1-checkpoint
    bash: |
      python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/full-checkpoint.py" "$ARTIFACTS_DIR" "$phase-1-baseline.output"
    timeout: 300000
    depends_on: [phase-1-compliance]

  # ========= PHASE 2 (depends on phase-1-checkpoint success) =========
  - id: phase-2-baseline
    bash: git rev-parse HEAD
    depends_on: [phase-1-checkpoint]
  # ... same pattern as Phase 1, ids prefixed phase-2- ...

  # ========= PHASE 3 ... =========

  - id: deploy-gate
    bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/deploy-gate.py" "$ARTIFACTS_DIR"
    timeout: 60000
    depends_on: [phase-3-checkpoint]

  - id: build-deploy
    command: build-deploy
    depends_on: [deploy-gate]
    model: sonnet
```

Reason: `depends_on` chains enforce sequential phase execution. Four review nodes in the same layer (all depending on `phase-N-execute`) run concurrently (dag-executor.ts: independent nodes in same topological layer run via `Promise.allSettled`). `context: fresh` per phase gives the S5 isolation requirement. Default `trigger_rule: all_success` means if any gate fails, downstream phases and deploy are skipped — correct behavior for the PRD's intent.

**How phase count is determined:** The PRD's Stage 10 already produces a phases count. The unrolled YAML must be generated by Stage 10 based on that count. For Phase 1 of this PRD implementation, a fixed 3-phase unroll is acceptable; true dynamic unrolling is Phase 2 work.

---

### M5 — Test Writer Node

**Verdict:** MINOR

**Evidence:** Prompt is clean markdown. Contract is reasonable. The only issue is how it's wired into the DAG.

**Problem:** M5 is listed as a Phase 2 item but the YAML stub in M4 wires it before `build-verify`. Fine in principle. The prompt tells the agent to "not modify non-test files" — this is S8-compliant. The success-criterion `WALL step count == test count` is measurable IF the phase spec enumerates WALL steps in a structured way.

**BEFORE (PRD §5 Phase 2 "Files to create"):**
```
- `.archon/commands/test-writer.md`
```

**AFTER (replace with this exact block):**
```
- `.archon/commands/test-writer.md` — the prompt file is as shown in §4 M5.
  Node wiring in prd-pipeline-c.yaml:

  - id: phase-N-test-writer
    command: test-writer
    depends_on: [phase-N-execute]
    model: sonnet
    context: fresh
```

Reason: ensures the command name in YAML matches the file. No other change needed.

---

### M6 — Scoped CLAUDE.md Auto-Attach

**Verdict:** FAIL

**Evidence:** This is a *prompt instruction* to `build-execute` telling the agent to read `$(dirname P)/CLAUDE.md`. Nothing enforces it. Archon has no native "scoped CLAUDE.md" feature. The Claude SDK itself has a `settingSources` option (per Archon's config.yaml) that loads `project` or `user` CLAUDE.md — but not per-directory sub-CLAUDEs.

**Problem:** The PRD frames this as a mechanism, but the only deliverable is a prompt edit. The agent may or may not obey. S1 (deterministic over agentic) is violated. This is best framed honestly as a prompt guideline, not a gate.

**BEFORE (PRD §4 M6 "Prompt edit to build-execute.md"):**
```markdown
## Directory Rules
Before writing a file at path P, check for CLAUDE.md files in these locations (in order):
1. $(dirname P)/CLAUDE.md
2. $(dirname $(dirname P))/CLAUDE.md
3. Root CLAUDE.md

Read the most-specific one that exists. Its rules apply to your work in this file.
```

**AFTER (keep the prompt addition, but re-classify this mechanism honestly + add an enforcement step):**
```markdown
## Directory Rules (soft guidance — best-effort, not gated)
Before writing a file at path P, check for CLAUDE.md files in these locations (in order):
1. path/to/file/dir/CLAUDE.md
2. path/to/file/dir/../CLAUDE.md
3. Project root CLAUDE.md

Read the most-specific one that exists. Its rules apply to your work in this file.
```
And add a post-build verification node:
```yaml
- id: claude-md-presence-check
  bash: |
    set -euo pipefail
    # Every directory that got a new file in this run should have a CLAUDE.md.
    # Emit report; don't fail the build (soft check, DOOR not WALL).
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/claude-md-audit.py" "$ARTIFACTS_DIR"
  depends_on: [phase-3-checkpoint]
```

Reason: replaces the `$()` shell-substitution syntax (which is not what the agent computes — the prompt is advisory text, not executable) with straight English, and adds a deterministic audit step. Marks the mechanism as a DOOR rather than a WALL since enforcement is observation-only.

---

### M7 — Codebase Cartographer

**Verdict:** FAIL (path ambiguity + same args-issue)

**Evidence:** Prompt body is fine. YAML wiring in §4 M4 references `command: codebase-cartographer` — valid, but the command file must live at `commands/codebase-cartographer.md` per Archon discovery rules (see CLAUDE.md line 552 and `loader.ts` command discovery).

**Problem:** PRD §4 M7 doesn't actually show a wiring snippet, only a prompt. The YAML from M4 is invalid (see M4 FAIL). Also, "Haiku" model assignment — Haiku 3.5 isn't a string Archon recognizes unless set as `haiku` (per config.yaml model aliases in Archon CLAUDE.md line 486). That part is fine; just confirm.

**BEFORE (PRD §4 M7 — no YAML wiring shown):**
```
(no YAML)
```

**AFTER (replace M7's "Prompt file" section's tail with this wiring):**
```yaml
- id: codebase-cartographer
  command: codebase-cartographer
  depends_on: [phase-3-checkpoint]   # or the last phase's checkpoint
  model: haiku
  context: fresh
```

Reason: uses the real Archon model alias (`haiku`), correct node type (`command:` since it's an AI agent), and clean dep chain. The prompt file `codebase-cartographer.md` is created per HANDOFF §3.

---

### M8 — Pre-Deploy Gate + Deferred Budget

**Verdict:** MINOR (same arg-passing issue as M1)

**BEFORE (implied YAML wiring):**
```yaml
- id: deploy-gate
  type: script
  script: .archon/scripts/deploy-gate.sh
  args: ["$ARTIFACTS_DIR"]
  depends_on: [final-report]
```

**AFTER:**
```yaml
- id: deploy-gate
  bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/deploy-gate.py" "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-final-report]
```

Reason: same as M1/M2 — `type: script` + `args:` doesn't exist; use a bash node that inlines the arg via `$ARTIFACTS_DIR` substitution. Corrected `final-report` → `build-final-report` (the real node id in prd-pipeline-b.yaml line 195).

**Logic of the script itself is fine** (when translated to Python per HANDOFF).

---

### M9 — Recovery Pipeline

**Verdict:** FAIL (cannot activate as specified)

**Evidence:** This is the biggest architectural blocker.
- Archon has NO `on_failure:` field, NO error-handling DAG branch.
- When a gate exits 1, its node state is `failed`. Downstream nodes with default `trigger_rule: all_success` simply SKIP. Nothing runs.
- `trigger_rule: all_done` would run the downstream regardless of state, but the downstream can't tell WHY upstream failed (no access to the failed node's output/error — see condition-evaluator.ts: `resolveOutputRef` returns empty string for failed nodes with no output).
- There is no "re-gate" primitive. Once a node is marked failed, the workflow proceeds with it marked failed. No loop-back.

**Problem:** The PRD describes a failure → diagnose → write-fix-prd → execute-fix → re-gate loop. This does not map to Archon's DAG model at all. Archon is a forward-only DAG; it has retries (per-node `retry:` config) but no error-branching subgraph.

**Options:**

**Option A (lean, matches Archon):** Reframe gates to *never* fail at the node level. Instead, gate nodes always exit 0 but write their result to stdout (`PASS` or `FAIL:<reason>`). Downstream "recovery-trigger" nodes use `when:` to branch.

**Option B (heavier, matches the PRD's intent):** Build the recovery pipeline as a **single separate workflow** (`prd-pipeline-c-recovery.yaml`) and have the main pipeline's gate scripts, on failure, write a flag file that a human or cron-like trigger runs the recovery workflow on. Cleaner but breaks "unattended" claim.

Option A is the one compatible with Archon's engine. Full replacement:

**BEFORE (PRD §4 M9 step flow, lines 549-579):** The whole "Activation rule: any gate returns exit 1 twice" pattern — delete it.

**AFTER (replace with this exact block):**
```yaml
# Gates never hard-fail. They write PASS/FAIL to stdout (captured as node output).
- id: phase-1-compliance
  bash: |
    set +e
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-fix]

# Recovery branch only runs if compliance gate said FAIL.
- id: phase-1-recovery-diagnose
  command: recovery-diagnose
  depends_on: [phase-1-compliance]
  when: "$phase-1-compliance.output == 'FAIL'"
  model: opus
  effort: high
  context: fresh

- id: phase-1-recovery-write-prd
  command: recovery-fix-prd
  depends_on: [phase-1-recovery-diagnose]
  when: "$phase-1-compliance.output == 'FAIL'"
  model: opus
  effort: high
  context: fresh

- id: phase-1-recovery-execute
  command: recovery-execute
  depends_on: [phase-1-recovery-write-prd]
  when: "$phase-1-compliance.output == 'FAIL'"
  model: opus
  effort: high
  context: fresh

- id: phase-1-recovery-regate
  bash: |
    set +e
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-recovery-execute]
  when: "$phase-1-compliance.output == 'FAIL'"

# Phase 2 only proceeds if either:
#   (a) compliance gate passed first time, OR
#   (b) recovery ran AND its regate passed.
# Since `when:` doesn't support OR across two different node outputs cleanly
# with these exact semantics, use an aggregator bash node.
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

- id: phase-2-execute
  command: build-implement
  depends_on: [phase-1-final-status]   # hard fail here halts phase 2
  model: sonnet
  context: fresh
```

Reason:
1. Gate nodes exit 0 and emit `PASS`/`FAIL`. Archon captures that as `$gate.output`.
2. Recovery branch uses `when:` — supported (condition-evaluator.ts). Only runs on FAIL.
3. `phase-1-final-status` aggregates. It uses `trigger_rule: all_done` because recovery-regate will be in `skipped` state when compliance passed. `all_done` runs once all upstream nodes have settled (completed, failed, or skipped — dag-executor.ts line 652).
4. Bash nodes can reference `$<node>.output` — escapeForBash=true wraps in single quotes (dag-executor.ts line 1357 + 195-200). The bash `[ "$foo" = "X" ]` comparison works on the single-quoted substituted values.
5. If final-status exits 1, downstream phase 2 is skipped (default all_success trigger) — the pipeline halts at the right place.

**Model assignment:** `effort: high` is a VALID field per `dag-node.ts` line 132 (`effortLevelSchema` = enum `'low' | 'medium' | 'high' | 'max'`). Note: Claude uses `effort`; Codex uses `modelReasoningEffort`. The PRD says "Opus 4.7" but Archon's Claude model aliases are `sonnet`, `opus`, `haiku`, `claude-*`, `inherit` (Archon CLAUDE.md line 486). Use `model: opus`.

**Non-negotiable caveat:** The PRD's "two consecutive failures triggers recovery" language must be dropped — Archon cannot count consecutive failures. The only supported pattern is "any single gate failure triggers recovery immediately." If the owner insists on 2-strike, that logic has to go INSIDE the gate script (track state in `$ARTIFACTS_DIR/gate-attempts.json`).

---

### M10 — PRD Archive

**Verdict:** PASS (after HANDOFF bash→Python + arg fix)

**Evidence:** The bash script is clean. It can run as a Python translation.

**BEFORE (implied YAML wiring):**
```yaml
- id: archive-prd
  type: script
  script: .archon/scripts/archive-prd.sh
  args: [...]
```

**AFTER:**
```yaml
- id: archive-prd
  bash: |
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/archive-prd.py" \
      "$ARTIFACTS_DIR" \
      "$BASE_BRANCH" \
      "shipped"
  depends_on: [build-deploy]
```

Reason: `$BASE_BRANCH` is a real Archon variable (Archon CLAUDE.md line 670). Used here as a stand-in for "build name" — owner can swap for whatever identifier makes sense.

**Minor content note:** The archive destination is `docs/generated-prds/` which is in the **Greptacular repo** (not in Archon's workspace). That path is correct per HANDOFF §3. Make sure the Python script's cwd resolves relative to the Greptacular repo, which it will when the workflow runs there.

---

### M11 — Regression Harness

**Verdict:** MINOR (same arg-passing + path issues)

**Evidence:** Logic in the bash snippet is readable but won't validate cleanly:
- `bash .archon/scripts/compliance-gate.sh "$FIXTURES/..."` — if HANDOFF's Python translation is used, this becomes `python compliance-gate.py <fixture>`.
- The `|| { echo FAIL; exit 1; }` + `&&` pattern works.
- But `FIXTURES="${1:-.archon/test-fixtures}"` expects argv[1], which as noted doesn't exist for script nodes.

**BEFORE (PRD §4 M11 snippet, lines 651-671):**
```bash
FIXTURES="${1:-.archon/test-fixtures}"
# ... bash logic using $FIXTURES ...
```

**AFTER (replace M11 implementation with Python + env-var based):**
```python
# .archon/scripts/regression-harness.py
import os, subprocess, sys

FIXTURES = os.environ.get("FIXTURES", ".archon/test-fixtures")
SCRIPTS = os.environ.get("SCRIPTS_DIR", ".archon/scripts")

def expect(cmd, expected_code, label):
    result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    if result.returncode != expected_code:
        print(f"FAIL: {label} (expected {expected_code}, got {result.returncode})")
        print(result.stderr)
        sys.exit(1)
    print(f"PASS: {label}")

print("=== Test A: Unit tests on gate scripts ===")
expect(["python", f"{SCRIPTS}/compliance-gate.py", f"{FIXTURES}/yt-strategy-lab-fail"], 1,
       "compliance-gate on yt-strategy-lab should exit 1")
expect(["python", f"{SCRIPTS}/compliance-gate.py", f"{FIXTURES}/task-manager-pass"], 0,
       "compliance-gate on task-manager should exit 0")

print("=== ALL REGRESSION TESTS PASS ===")
```

And wire it as:
```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR="$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts" \
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/regression-harness.py"
  depends_on: []   # standalone — invoked manually or by a separate workflow
```

Reason: env vars pass in where args can't. Bash node substitutes `$ARCHON_HOME` only if Archon sets it — which it does (CLAUDE.md line 556). If not, fall back to `$HOME/.archon/...`.

---

### M12 — Feature Toggles

**Verdict:** FAIL

**Evidence:** PRD says "each mechanism reads its flag at runtime. If a toggle is false, the node becomes a no-op (or is skipped in the DAG)." 

The key phrase: "skipped in the DAG." How does a node skip based on a YAML file external to Archon?

- `when:` conditions only read `$nodeId.output[.field]` — NOT external files. (condition-evaluator.ts line 88.)
- There is no `enabled: false` or `disabled: true` field on nodes (dag-node.ts — full schema reviewed).
- So the toggle file is only useful IF a prior bash node reads it and emits the flag value as its output, THEN downstream nodes use `when:` against that.

**Problem:** The PRD implies a simple boolean toggle per node. That's not free in Archon — each toggleable mechanism needs an upstream "read-feature-flag" bash node.

**BEFORE (PRD §4 M12 "Each mechanism reads its flag at runtime"):**
```
Each mechanism reads its flag at runtime. If a toggle is false, the corresponding node becomes a no-op (or is skipped in the DAG). Toggles do not require a pipeline rebuild.
```

**AFTER (replace with this exact block):**
```
Each toggle is enforced by an upstream `read-flag-*` bash node that emits 'true' or 'false' as its stdout. Downstream nodes use a `when:` condition against that output.

Example for `recovery_pipeline: true/false`:

- id: read-flag-recovery
  bash: |
    python -c "import yaml,sys; c=yaml.safe_load(open('$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []   # or earliest possible ancestor

- id: phase-1-recovery-diagnose
  command: recovery-diagnose
  when: "$phase-1-compliance.output == 'FAIL' && $read-flag-recovery.output == 'true'"
  depends_on: [phase-1-compliance, read-flag-recovery]
  model: opus
  effort: high

Applying this pattern to all 6 toggled mechanisms (recovery_pipeline, prd_archive, regression_harness, codebase_cartographer, scoped_claude_md, build_intelligence) adds 6 read-flag nodes at pipeline start. Features.yaml itself lives at .../source/.archon/features.yaml per HANDOFF §3.
```

Reason: This is the ONLY way to wire YAML-file-driven toggles into Archon's DAG without modifying Archon. The `when:` syntax is documented and tested (condition-evaluator.ts supports `&&` per line 157). Fail-closed behavior (unparseable condition → skip) is safe.

**If the owner accepts this complexity, it works. If not, alternative = remove M12 entirely for Phase 1 and wire toggles manually by commenting out nodes in the YAML.**

---

## Cross-cutting findings

### Copy-don't-overwrite pattern

**Verdict:** PASS (HANDOFF correctly identifies this; path corrections are accurate)

**Evidence:**
- HANDOFF §1 paths confirmed: `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\` exists per the Bash listing performed during this review (workflows + commands folders confirmed to contain the expected files; no scripts/ folder yet).
- Archon's workflow discovery is by filename (loader scans `.archon/workflows/*.yaml`). Creating `prd-pipeline-c.yaml` alongside `-b.yaml` adds a new discoverable workflow without disturbing the existing one (CLAUDE.md line 691).
- Command files are discovered by filename-without-extension (CLAUDE.md line 681). `build-fix-v2.md` creates a new command `build-fix-v2` without touching `build-fix`.

No fix needed. HANDOFF is correct here.

### Feature toggles

**Verdict:** FAIL (see M12 above for the fix pattern)

### Recovery Pipeline (M9)

**Verdict:** FAIL (see M9 above for the compatible rewrite)

### Per-phase loop (M4)

**Verdict:** FAIL (see M4 above — use unrolled phase groups)

### Model assignment per node

**Verdict:** PASS

**Evidence:**
- `dag-node.ts` line 118-119: `model: z.string().optional()` and `provider: z.enum(['claude','codex']).optional()` — both valid per-node.
- `effort: effortLevelSchema.optional()` at line 132 with enum values `'low' | 'medium' | 'high' | 'max'`. PRD's `effort: high` is valid.
- Existing prd-pipeline-b.yaml lines 136, 148, 158 etc. already uses `model: sonnet` per-node — confirmed pattern.

No fix needed.

### Effort level field

**Verdict:** PASS

**Evidence:** Confirmed in `dag-node.ts` line 132. PRD says "Opus 4.7, high effort" — in YAML that's:
```yaml
model: opus
effort: high
```
`effort: high` is correct. `model: opus` is the Archon alias (there's no "4.7" literal — the SDK resolves the actual Claude release). If the owner really wants to pin a specific model version, `model: claude-opus-4-20250514` or similar is also accepted per the `claude-*` pattern (CLAUDE.md line 486).

Note: the PRD interchangeably says "Opus 4.7" — that exact string is NOT a supported alias. Stick with `model: opus` for auto-resolution, or pin to the full SDK id.

---

## Test plan findings

### Test A — Gate Script Unit Tests

**Verdict:** MINOR — commands executable after arg-passing fix.

**BEFORE (PRD §9 Test A assertions):**
```
compliance-gate.sh yt-strategy-lab-fail → exit 1
```

**AFTER (use Python entry — per HANDOFF):**
```
python .archon/scripts/compliance-gate.py .archon/test-fixtures/yt-strategy-lab-fail → exit 1
python .archon/scripts/compliance-gate.py .archon/test-fixtures/task-manager-pass → exit 0
python .archon/scripts/full-checkpoint.py .archon/test-fixtures/broken-phase <sha> → exit 1
python .archon/scripts/deploy-gate.py .archon/test-fixtures/yt-strategy-lab-fail → exit 1
python .archon/scripts/deploy-gate.py .archon/test-fixtures/task-manager-pass → exit 0
python .archon/scripts/archive-prd.py .archon/test-fixtures/task-manager-pass test shipped → creates docs/generated-prds/{date}__test/
```

Fixtures must be real directories with pre-made `review-*.md`, `fix-report.md`, `files_allowed.json`. Those fixtures do NOT exist yet — they must be created as part of Phase 1.

### Test B — Red-Team Replay

**Verdict:** AMBIGUOUS

**Problem:** The test says "Restore the YT Strategy Lab v2 workspace to the state it was in right before deploy ran (use git tag / artifact snapshot)." This assumes such a snapshot exists. If artifacts were not preserved, the test is ungated. Unchanged from PRD; just flag for the owner.

No fix required for PRD correctness — just a gate on availability of historical artifacts.

### Test C — Fresh Tiny Build

**Verdict:** PASS (conceptually)

Logic is fine. This runs after Phase 1+2. Proceed as PRD states.

---

## Final corrected PRD sections (consolidated apply-these-edits)

Apply these as a single edit pass to the PRD:

### §4 M1 — wire via bash node
Replace the script-node YAML stub (implied by HANDOFF) with:
```yaml
- id: compliance-gate
  bash: python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/compliance-gate.py" "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

### §4 M2 — delete "type: script / args:" block, replace with bash wrapper that uses `$phase-N-baseline.output`:
```yaml
- id: phase-1-baseline
  bash: git rev-parse HEAD
  depends_on: [build-codebase-intelligence]

- id: full-checkpoint
  bash: |
    python "$ARCHON_HOME/workspaces/digisurfsome/Greptacular/source/.archon/scripts/full-checkpoint.py" "$ARTIFACTS_DIR" "$phase-1-baseline.output"
  timeout: 300000
  depends_on: [compliance-gate]
```

### §4 M4 — delete entire `for_each` snippet (lines 262-371). Replace with unrolled-phases YAML (full block under "M4 AFTER" above).

### §4 M6 — soften language + add audit bash node (full block under "M6 AFTER" above).

### §4 M7 — append YAML wiring (block under "M7 AFTER" above).

### §4 M8 — replace implied `type: script / args:` with bash node (block under "M8 AFTER" above). Fix `final-report` → `build-final-report`.

### §4 M9 — delete entire two-strike activation rule and step flow. Replace with the 5-node `compliance → recovery-diagnose → recovery-fix-prd → recovery-execute → recovery-regate` + `final-status` aggregator pattern (block under "M9 AFTER" above). Drop "two consecutive failures" — Archon can't count.

### §4 M10 — archive node uses bash wrapper with `$ARTIFACTS_DIR` and `$BASE_BRANCH` (block under "M10 AFTER" above).

### §4 M11 — translate bash to Python, read fixtures from env var, not argv[1] (block under "M11 AFTER" above).

### §4 M12 — replace "each mechanism reads its flag at runtime" with the upstream read-flag-* bash node pattern (block under "M12 AFTER" above). OR remove M12 from Phase 1.

### §5 Phase 1 "Files to edit" — replace with the HANDOFF-correct list of files to CREATE (block under "M3 AFTER" above).

### §15 Model Assignment — all "Opus 4.7" references: use `model: opus` + `effort: high` (or `effort: medium` where PRD says medium). No literal "4.7" string.

---

## Recommendation

**NEEDS REVISION before execution.** The PRD's strategy and Standards Layer (S1–S9) are sound, and HANDOFF.md catches three real blockers (paths, runtime, copy-don't-overwrite). But 5 mechanisms still have YAML that won't validate against Archon's schema, and M9 (the whole Recovery Pipeline) requires an architectural rewrite because Archon has no on-failure branching.

Apply the 11 fixes in the "Final corrected PRD sections" block above, then Phase 1 (M1, M2, M3, M8, M10, M11, M12 with the simpler skip-M9-if-too-complex fallback OR the reshaped M9) is buildable. Phase 2's M4 (per-phase loop) still needs the unrolled-groups approach.

If the owner wants to execute Phase 1 in the next 1 day: **skip M9 and M12 for now**, ship M1+M2+M3+M8+M10+M11 with the bash-wrapper YAML pattern. That delivers the critical YT Strategy Lab fix (compliance-gate catches the 34-issues case) with zero architectural assumptions. M9 and M12 can come in a Phase 1b after more schema work.

---

## Optional observations (not required fixes)

1. **Bash on Windows:** Archon's bash nodes call `execFileAsync('bash', ['-c', ...])` (dag-executor.ts line 1362). On Windows this requires `bash.exe` in PATH — typically from git-bash. Confirm git-bash is installed where the Archon server runs. If unavailable, all bash-node-based gates above will fail with ENOENT ("bash executable not found in PATH").
2. **Script node `cwd` is always the workflow's cwd.** There is no per-node cwd override. The Python translations of full-checkpoint etc. must use absolute paths or derive paths from `$ARTIFACTS_DIR`.
3. **`$ARCHON_HOME` substitution** — I wrote all bash snippets using `$ARCHON_HOME` which Archon sets (CLAUDE.md line 556). If the owner does not set it, fall back to `$HOME/.archon`. Archon does NOT auto-substitute it in bash scripts the way it does `$ARTIFACTS_DIR`; it's passed as a shell env var and `bash -c` inherits the parent process env, so it's available.
4. **Claude model "Opus 4.7"** — there is no such public Anthropic release as of Jan 2025. The PRD language is loose. Use `model: opus` and let Archon/SDK resolve to the latest Opus version available at run time.
5. **Strategic note (non-binding):** The real fix for YT Strategy Lab is M1 + M3. Those two alone — compliance-gate script + exemption-language removal — would have caught the failure. Everything else is nice-to-have or future-proofing. If time is tight, ship M1+M3 as standalone, validate on fixtures, then iterate.
