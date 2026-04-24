# Archon Build-Half Upgrade (Stripe Blueprint Compliance)

**Status:** Ready to Build
**Author:** Derived from YT Strategy Lab v2 post-mortem + Stripe Minions articles
**Related specs:** `.claude/specs/spec-006-testing-layer.md`, `.claude/handoffs/build-intelligence-handoff.md`
**Scope:** Modify the Archon execution pipeline (not the PRD maker) to enforce deterministic gates, bounded contracts, and per-phase isolation.

---

## Companion Documents (read these alongside this PRD)

| File | Purpose |
|------|---------|
| [`PIPELINE-REBUILD-NO-BASH-HANDOFF.md`](./PIPELINE-REBUILD-NO-BASH-HANDOFF.md) | **Full handoff PRD for a brand-new agent to rebuild `prd-pipeline-c.yaml` as `prd-pipeline-d.yaml` without bash nodes.** Catalogues every Windows/bash failure we hit, maps each to a prompt-node or command-node replacement, references the archon skill, and gives a step-by-step plan with success criteria. **Do this rebuild BEFORE applying the V3 roadmap fixes below.** |
| [`PRD-MAKER-V3-ROADMAP.md`](./PRD-MAKER-V3-ROADMAP.md) | **10 concrete fixes to lift PRD Maker 7.5 → 9.5/10.** I/O examples per mechanism, acceptance tests per deliverable, golden path trace (Stage 8.5), 4→2 reviewers, production red team (Stage 8.75), reproducibility seed lock, programmatic compile check, deployment target router (Stage 0.5), mechanism contract + boundary gate, cross-platform harness plan. |
| [`BUILD-ONLY-WORKFLOW-PRD.md`](./BUILD-ONLY-WORKFLOW-PRD.md) | Spec for `prd-pipeline-BUILD.yaml` — stripped pipeline that skips Stages 0–10 and imports a pre-made PRD bundle, so re-runs don't re-generate the PRD. |
| [`MASTER-MODULAR-ARCHITECTURE.md`](./MASTER-MODULAR-ARCHITECTURE.md) | 6 build modes (standalone-app, module, module-host, assembly, feature-add, contract-spec), universal context preamble mechanism, standardized Module Contract. |
| [`MP3-GEN-SYSTEM-CONTEXT-PREAMBLE.md`](./MP3-GEN-SYSTEM-CONTEXT-PREAMBLE.md) | Ready-to-paste context block (persona + "this is a module" framing + DO/DO NOT scope rails) for the MP3 Generator PRD run. |
| [`M13-EXISTING-APP-MODE.md`](./M13-EXISTING-APP-MODE.md) | Mechanism spec: how the pipeline handles adding features to an existing app vs a green-field build. |
| [`M14-PRD-SELF-CHECK.md`](./M14-PRD-SELF-CHECK.md) | Mechanism spec: PRD self-validation stage before the build half starts. |
| [`M15-INTAKE-CLASSIFIER.md`](./M15-INTAKE-CLASSIFIER.md) | Mechanism spec: classify incoming requests into one of the 6 build modes automatically. |
| [`PHASE-1-REVIEW.md`](./PHASE-1-REVIEW.md) | Review notes from Phase 1 of the build-half upgrade. |

---

## 0. Drift Anchor (locked — do not redefine downstream)

> AutoForge's PRD maker produces solid plans. The build-half (execution pipeline) currently takes those plans and lets agents self-grade their work, with no mechanical enforcement. This spec replaces agent-based gating with deterministic bash/python gates, tightens the contract agents inherit, and adds a per-phase loop so multi-phase builds stay isolated. Goal: an unattended build pipeline where an agent cannot ship a broken build because a script refuses to let it.

**What this is NOT:** a rewrite of the PRD maker. The PRD maker stays exactly as is. Only the workflow YAML, command prompts, and a handful of new bash scripts get touched.

---

## 1. Standards Layer (global principles — apply to every mechanism)

These are the rules every mechanism in this spec must obey. If a mechanism violates one of these, it's wrong.

### S1 — Deterministic Over Agentic
Any check that can be done by a script (lint, typecheck, git diff, file count, issue count) **MUST** be done by a script. Agents are allowed to write content, not to judge whether content passed. Borrowed from Stripe Minions blueprint pattern.

### S2 — No Exemption Language
Prompts that feed the fix agent, verify agent, or test agent may not contain:
- "defer to human"
- "architectural, out of scope"
- "separate task per instructions"
- "two-strike rule" applied to *categories* of work (only individual attempts)

Every review item gets either fixed or the pipeline fails. No third option.

### S3 — Gates Are Bash, Not Agents
The compliance gate, full checkpoint, and quality checks are shell scripts with `exit 1` on failure. They are not markdown instructions for an agent to interpret.

### S4 — Bounded Retry (softened for non-coder operator)
A single fix *attempt* may retry twice — that cap stays, it prevents infinite loops.
But at the pipeline level, "gate failed twice" does NOT mean hard stop. It means **activate the Recovery Pipeline (M9)** — an Opus-powered agent that diagnoses, writes a fix PRD, and executes the fix automatically. Only after the Recovery Pipeline also fails do we halt, and even then the halt comes with a plain-English report, not a stack trace.

### S5 — Fresh Context Per Phase
Every phase in a multi-phase build gets a fresh agent with a slim handoff doc. No agent carries context across phase boundaries.

### S6 — Scoped Rule Files
CLAUDE.md files live at the scope they apply to (per-directory), not globally. Agents auto-read the one for the directory they're working in. Stripe pattern.

### S7 — Shift Feedback Left
Linters and typecheckers run after every file write during the build (cheap, fast), not at the end (expensive, late). If eslint-autofix can fix it, run autofix deterministically before paying LLM tokens to "fix" it.

### S8 — Single Responsibility Per Agent
Each agent in the pipeline has one job with one measurable output. The fix agent does not also write tests. The test writer does not also fix. The reviewer does not also fix.

### S9 — Non-Coder Safety Net (the rule that makes this different from Stripe)
Stripe's Minions are built for engineers who can read CI logs. This pipeline is built for a non-coder operator. Therefore: **every failure mode must produce a plain-English diagnosis AND an auto-recovery attempt before ever halting for human attention.** A failure in this pipeline that requires the user to "go read code to figure out what broke" is a pipeline bug, not a user problem. The Recovery Pipeline (M9) is the physical embodiment of this rule.

---

## 2. Product Layer (what we're building toward)

**The Bull Chute Principle:** A rodeo keeps bulls controlled through narrow chutes with gates that only open at the right moment. Our pipeline is the chute. Each deterministic gate is a door. Each agent is one segment of the chute — it can move the bull forward, but it cannot open a closed gate. No agent can decide "I'll skip this gate" — the gate either opens (script returns 0) or it doesn't (script returns 1). Only then does the bull advance.

**North Star Metric:** After this spec ships, the YT Strategy Lab v2 build, re-run with no human intervention, should either (a) deploy cleanly with all 51 review issues addressed, or (b) halt at a gate with a specific, mechanical failure reason. Never again: "deploy succeeded with 34 issues deferred."

---

## 3. Current State Audit (so the builder knows what exists)

| Component | Status | Location |
|---|---|---|
| PRD maker (Stages 0–10) | Working, do not touch | Archon workflow + `.archon/commands/stage-*.md` |
| `prd-pipeline-b.yaml` | Linear DAG, no loops, no gates | `.archon/workflows/prd-pipeline-b.yaml` |
| `build-execute.md` | Handles all phases in one agent context | `.archon/commands/build-execute.md` |
| `build-verify.md` | Agent-based, advisory classification only | `.archon/commands/build-verify.md` |
| `build-fix.md` | Contains exemption language | `.archon/commands/build-fix.md` |
| Four reviewers | Working, parallel | `.archon/commands/build-review-*.md` |
| Full checkpoint | Text in generated phase files, agent-enforced | Stage 8 output, embedded in phases/*.md |
| Compliance gate | Does not exist | — |
| Per-phase loop | Does not exist | — |
| Test-writer as separate agent | Does not exist (bundled into fix) | — |
| Build intelligence / calibration | Specced, not built | `.claude/handoffs/build-intelligence-handoff.md` |

---

## 4. Mechanisms (12 total, classified Wall/Door)

### Mechanism 1 — Compliance Gate Script [WALL]
**Purpose:** After the fix agent runs, mechanically verify every issue flagged by reviewers has a corresponding fix entry. If count mismatch → fail pipeline.

**Classification:** WALL. One correct answer. Pass/fail.

**Deterministic:** 100%. No agent involved.

**Contract:**
- Input: `$ARTIFACTS_DIR/review-correctness.md`, `review-failures.md`, `review-tests.md`, `review-simplify.md`, `fix-report.md`
- Parse: count issues flagged per severity (CRITICAL, HIGH, MEDIUM, LOW)
- Parse: count fixes applied per severity in fix-report.md
- Rule: Every CRITICAL and HIGH must have a matching fix entry. MEDIUM/LOW may be explicitly listed as "accepted tech debt" in a `deferred.md` file with a reason per item (max 3 deferrals).
- Output: `compliance-gate-result.md` + exit code

**Script:** Translated to Python per HANDOFF.md (Windows compatibility). Lives at `.archon/scripts/compliance-gate.py`. Reads `sys.argv[1]` as the artifacts dir. Logic identical to the bash pseudocode below:

```
count_issues(severity) = grep -hE "^[*-] \*\*\[<severity>\]" $ARTIFACTS_DIR/review-*.md | line count
count_fixes(severity)  = grep -cE "^### Fix [0-9]+:.*\[<severity>\]" $ARTIFACTS_DIR/fix-report.md

if critical_fixes < critical_issues: FAIL "<n> CRITICAL issues unaddressed" -> exit 1
if high_fixes     < high_issues:     FAIL "<n> HIGH issues unaddressed"     -> exit 1
else: PASS -> exit 0
```

**YAML wiring (in prd-pipeline-c.yaml):**
```yaml
- id: compliance-gate
  bash: python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-fix-issues]
```

Reason: Archon script nodes cannot receive CLI args (dag-executor.ts line 1569). A bash node expands `$ARTIFACTS_DIR` (via variable substitution, line 1348) and can pass it to Python as argv[1]. `depends_on: build-fix-issues` matches the real node id in prd-pipeline-b.yaml line 184.

**Success criteria:**
- Re-running on YT Strategy Lab artifacts: exit 1 with message "34 issues unaddressed"
- Re-running on Team Task Manager artifacts: exit 0

---

### Mechanism 2 — Full Checkpoint Script [WALL]
**Purpose:** End-of-phase gate. Runs lint + typecheck + tests + files_allowed diff. Replaces the agent-enforced checkpoint that Stage 8 currently embeds as markdown.

**Classification:** WALL.

**Deterministic:** 100%.

**Contract:**
- Input: `$ARTIFACTS_DIR` (folds in files_allowed.json path), baseline git SHA captured from an upstream bash node, project cwd (automatic in bash nodes)
- Checks (in order, each must exit 0):
  1. `npm run lint` (or language-appropriate) — invoked via `subprocess.run` in Python
  2. `npm run typecheck` / `npx tsc --noEmit` (or equivalent — Python: `mypy`, Rust: `cargo check`)
  3. `npm test` (or equivalent)
  4. `git diff --name-only $BASELINE_SHA` ⊆ `files_allowed` (no unauthorized files modified) — computed via Python `json` + `set` difference, no `jq`/`comm`/process-substitution required
- Output: `phase-N-checkpoint-result.md` + exit code

**Script:** Python translation per HANDOFF.md lives at `.archon/scripts/full-checkpoint.py`. It takes two args: artifacts dir and baseline SHA. Logic is the four checks above in sequence, each shelling out via `subprocess.run`.

**YAML wiring (in prd-pipeline-c.yaml):**
```yaml
# Capture the baseline SHA before the phase runs.
- id: phase-baseline
  bash: git rev-parse HEAD
  depends_on: [build-codebase-intelligence]

# ... build-execute-phase runs here ...

# Checkpoint: invoke the Python translation of the full-checkpoint gate,
# passing the captured baseline via node-output substitution.
- id: full-checkpoint
  bash: |
    set -euo pipefail
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-baseline.output
  timeout: 300000
  depends_on: [compliance-gate]
```

Reason: `$phase-baseline.output` is a node-output reference Archon substitutes via `substituteNodeOutputRefs` (dag-executor.ts line 195–200). `escapedForBash=true` (line 1357) single-quotes the value for safe interpolation. `$ARTIFACTS_DIR` substitutes automatically (line 1348). PROJECT_DIR is the workflow cwd (automatic in bash nodes). `npm run lint` / `npm test` / `tsc` invoke via `subprocess.run` inside the `.py` — no positional argv needed. Archon does NOT define `$BASELINE_SHA`; we capture it ourselves from an upstream `git rev-parse HEAD` bash node.

**Success criteria:**
- Phase with a broken test → exit 1
- Phase that writes outside files_allowed → exit 1
- Clean phase → exit 0

---

### Mechanism 3 — Stage 10 Prompt Tightening [WALL]
**Purpose:** Remove all exemption language from what Stage 10 writes into build-fix.md and related prompts. Make the contract explicit: every review item must be addressed or pipeline fails.

**Classification:** WALL. Text edit. No ambiguity.

**Files to edit:**
- `.archon/commands/stage-10.md` (the prompt that generates phase files)
- `.archon/commands/build-fix.md` (if this is hand-maintained rather than generated)

**Edits required:**

1. **Delete exemption language.** Search for and remove:
   - "tests are a separate task per instructions"
   - Any "defer to human" clauses applied to categories
   - Any "architectural issues → out of scope" clauses

2. **Replace with mandatory contract block:**

```markdown
### Contract (MANDATORY — NO EXCEPTIONS)

You MUST address every issue flagged in these files:
- review-correctness.md
- review-failures.md
- review-tests.md
- review-simplify.md

For each issue:
- CRITICAL or HIGH severity → fix it. No exceptions.
- MEDIUM or LOW → fix it, OR list it in `deferred.md` with:
  (a) the specific reason it cannot be fixed in this phase, and
  (b) evidence (file path, line number) showing you attempted a fix

Writing tests for flagged coverage gaps is part of this contract, not a separate task.
If review-tests.md lists untested WALL steps, you write those tests before claiming done.

The compliance gate script (.archon/scripts/compliance-gate.py) runs after you finish.
It will count issues vs fixes. If it emits FAIL, the recovery branch activates; if recovery also fails, the pipeline halts.
```

3. **Two-strike rule scope correction:**

Change: "If the same fix fails twice: STOP. Document it and move on."
To: "If the same individual fix attempt fails twice: note in deferred.md, continue to other issues. You may not declare entire categories (e.g., 'all tests', 'all async issues') as exempt."

**Success criteria:**
- Grep for "separate task" in `.archon/commands/` returns zero results
- Grep for "defer to human" returns zero results outside of the deferred.md schema itself
- Next build's fix-report.md has no line claiming a category-wide exemption

---

### Mechanism 4 — Per-Phase YAML Loop [DOOR]
**Purpose:** Replace the single `build-execute` node with per-phase execution. Each phase gets a fresh agent context and runs the full build → test → review → fix → gate cycle for that phase alone.

**Classification:** DOOR. Structured via manual unroll (Archon's `loop:` node is an AI-prompt loop, not an array iterator — it does not support `for_each`/`over`/`as`/`body`).

**Chosen approach:** Stage 10 generates the complete `prd-pipeline-c.yaml` with N unrolled phase groups. Phase 1 of this PRD implementation assumes a fixed 3-phase unroll; dynamic N-phase generation is Phase 2 work.

**YAML snippet (unrolled — 3-phase example):**

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
    bash: python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    timeout: 60000
    depends_on: [phase-1-fix]

  - id: phase-1-checkpoint
    bash: |
      python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-1-baseline.output
    timeout: 300000
    depends_on: [phase-1-compliance]

  # ========= PHASE 2 (depends on phase-1-checkpoint success) =========
  - id: phase-2-baseline
    bash: git rev-parse HEAD
    depends_on: [phase-1-checkpoint]
  # ... same pattern as Phase 1, ids prefixed phase-2- ...

  # ========= PHASE 3 ... =========

  - id: deploy-gate
    bash: python .archon/scripts/deploy-gate.py "$ARTIFACTS_DIR"
    timeout: 60000
    depends_on: [phase-3-checkpoint]

  - id: build-deploy
    command: build-deploy
    depends_on: [deploy-gate]
    model: sonnet
```

Reason: `depends_on` chains enforce sequential phase execution. The four review nodes in the same layer (all depending on `phase-N-execute`) run concurrently — Archon runs independent nodes in the same topological layer via `Promise.allSettled`. `context: fresh` per phase gives the S5 isolation requirement. Default `trigger_rule: all_success` means if any gate fails, downstream phases and deploy are skipped — the correct behavior for the PRD's intent.

**How phase count is determined:** Stage 10 already produces a phases count. The unrolled YAML must be generated by Stage 10 based on that count. A fixed 3-phase unroll is acceptable for Phase 1 of this PRD; true dynamic unrolling is Phase 2 work.

**Why not `for_each`:** Archon has no such construct. `schemas/loop.ts` defines `loop:` as an AI iteration with fields `prompt`, `until`, `max_iterations`, `fresh_context`, `until_bash`, `interactive`, `gate_message`. There is no `over:`, no `as:`, no `body:`, no `type: parallel`. Node types are exactly `command`, `prompt`, `bash`, `script`, `loop`, `approval`, `cancel`.

**Success criteria:**
- A 3-phase build creates 3 separate agent contexts
- Phase N+1 does not start until phase N's full-checkpoint exits 0
- If compliance-gate exits 1 in phase 2, phase 3 never runs

---

### Mechanism 5 — Test Writer Node [WALL]
**Purpose:** Dedicated agent whose only job is writing tests for WALL steps flagged by review-tests.md. Split out from the fix agent so tests cannot be skipped.

**Classification:** WALL.

**Deterministic:** No (agent writes code), but its contract is enforced by a deterministic gate.

**Contract:**
- Input: phase file + review-tests.md (flagged untested WALLs)
- Output: test files at the paths specified in the phase's Stage 5 blueprints
- Follows the project's existing test framework (vitest, pytest, etc.)
- Every WALL step in the phase gets at least one test

**Prompt file (new):** `.archon/commands/test-writer.md`

```markdown
# Test Writer

You write tests. That is your only job.

## Inputs
- `$ARTIFACTS_DIR/phases/` — the generated phase spec files (one `.md` per phase). Read the one matching the phase id passed in `$ARGUMENTS` (for example `phase-1.md` when `$ARGUMENTS` is `phase-1`).
- `$ARTIFACTS_DIR/review-tests.md` — flagged coverage gaps (if already built)

## Contract
For every step in the phase file classified as WALL, there must be at least one test.
- Unit tests for service-layer logic
- Integration tests for API endpoints
- Edge cases flagged by review-tests.md

## Where Tests Go
Use the project's existing test layout. If unsure, check `package.json` for the test script and mirror existing `*.test.ts` file locations.

## What You Do Not Do
- You do not modify non-test files
- You do not fix bugs you notice — flag them in `test-writer-notes.md` for the fix agent
- You do not skip WALL steps claiming they're "trivial" — every WALL gets a test

## Output
- Test files at their target paths
- `test-writer-report.md` listing files created and which WALL step each covers
```

**Success criteria:**
- WALL step count (from stage_5 in context_packet.json) == test count (from test-writer-report.md)
- All tests pass (via full-checkpoint.py)

---

### Mechanism 6 — Scoped CLAUDE.md Auto-Attach [DOOR]
**Purpose:** Follow Stripe's pattern — per-directory rule files used by agents when they work in that directory. Reduces global context bloat.

**Classification:** DOOR — **soft guidance, not a WALL.** The agent prompt is advisory; enforcement is observation-only via a post-build audit node. Archon has no native per-directory CLAUDE.md auto-attach feature (the Claude SDK's `settingSources` option loads only `project` or `user` CLAUDE.md — not per-directory sub-CLAUDEs).

**Approach:**
- During Stage 10, emit a `CLAUDE.md` for each new major directory the phase creates (e.g., `server/services/CLAUDE.md`, `ui/src/components/yt-lab/CLAUDE.md`)
- These files state: what lives here, what conventions apply, what must not happen
- Build agent's prompt suggests reading the CLAUDE.md when entering a directory (best-effort; agent may or may not obey)
- A post-build audit bash node reports which new directories are missing a CLAUDE.md (soft check, DOOR not WALL)

**Prompt edit to build-execute.md:**

```markdown
## Directory Rules (soft guidance — best-effort, not gated)
Before writing a file at path P, check for CLAUDE.md files in these locations (in order):
1. path/to/file/dir/CLAUDE.md
2. path/to/file/dir/../CLAUDE.md
3. Project root CLAUDE.md

Read the most-specific one that exists. Its rules apply to your work in this file.
```

**Post-build audit node (in prd-pipeline-c.yaml):**
```yaml
- id: claude-md-presence-check
  bash: |
    set -euo pipefail
    # Every directory that got a new file in this run should have a CLAUDE.md.
    # Emit report; don't fail the build (soft check, DOOR not WALL).
    python .archon/scripts/claude-md-audit.py "$ARTIFACTS_DIR"
  depends_on: [phase-3-checkpoint]
```

Reason: Replaces `$()` shell-substitution syntax (which is not what the agent computes — the prompt is advisory text, not executable) with straight English. The audit node converts enforcement from "trust the agent" to "observe the outcome," staying honest about the DOOR classification.

**Success criteria:**
- After a build, each domain directory has a CLAUDE.md (target, not gate)
- CLAUDE.md files are scoped (under 200 lines each)
- The audit script produces a report listing any new directories without a CLAUDE.md

---

### Mechanism 7 — Codebase Cartographer [DOOR]
**Purpose:** Haiku agent, runs after all phases complete. Reads the built codebase and produces `CODEBASE_MAP.md` — a living reference doc.

**Classification:** DOOR.

**Prompt file (new):** `.archon/commands/codebase-cartographer.md`

```markdown
# Codebase Cartographer

You are a Haiku agent. Keep output mechanical and complete.

## Your Job
Produce `CODEBASE_MAP.md` at the project root. Overwrite if it exists.

## Structure
1. **File Tree** — `tree`-style output, top 3 levels, one-line purpose per file
2. **Module Exports** — table: file path | what it exports | consumers
3. **Dependency Graph** — import edges between top-level modules
4. **Change Map** — "If you want to change X, edit Y" — one row per major user-facing feature

## Constraints
- Read only. Do not modify anything except CODEBASE_MAP.md.
- No opinions. No TODOs. No "could be improved" comments.
- If you can't parse a file, skip it and note in a "Skipped" section.
```

**YAML wiring (in prd-pipeline-c.yaml):**
```yaml
- id: codebase-cartographer
  command: codebase-cartographer
  depends_on: [phase-3-checkpoint]   # or the last phase's checkpoint
  model: haiku
  context: fresh
```

Reason: Uses the real Archon model alias (`haiku` — per Archon CLAUDE.md line 486), correct node type (`command:` since it's an AI agent), and a clean dep chain. The prompt file `codebase-cartographer.md` is discovered by filename via Archon's command loader.

**Success criteria:**
- File exists after build
- Under 500 lines
- Every top-level source file appears in at least one table

---

### Mechanism 8 — Pre-Deploy Gate + Deferred Budget [WALL]
**Purpose:** Final mechanical gate before `build-deploy`. Reads the cumulative deferred.md files, caps total deferrals, verifies no CRITICAL/HIGH remain.

**Classification:** WALL.

**Deterministic:** 100%.

**Script:** Python translation at `.archon/scripts/deploy-gate.py` (per HANDOFF bash→Python rule). Reads `sys.argv[1]` as artifacts dir. Logic:

```
# Aggregate all deferred.md files
deferred_count = total bullet-line count across $ARTIFACTS_DIR/runs/*/deferred.md

# Count remaining CRITICAL/HIGH vs fixed
remaining = grep count of "^[*-] \*\*\[(CRITICAL|HIGH)\]" across runs/*/review-*.md
fixed     = grep count of "^### Fix [0-9]+:"             across runs/*/fix-report.md

if remaining > fixed: FAIL "<n> CRITICAL/HIGH items not in fix-report" -> exit 1
if deferred_count > 5: FAIL "<n> deferrals exceeds budget of 5"        -> exit 1
else: PASS "<n> deferrals, 0 remaining criticals" -> exit 0
```

**YAML wiring (in prd-pipeline-c.yaml):**
```yaml
- id: deploy-gate
  bash: python .archon/scripts/deploy-gate.py "$ARTIFACTS_DIR"
  timeout: 60000
  depends_on: [build-final-report]
```

Reason: Same pattern as M1/M2 — `type: script` + `args:` doesn't exist in Archon. Use a bash node that inlines the arg via `$ARTIFACTS_DIR` substitution. Corrected `final-report` → `build-final-report` (the real node id in prd-pipeline-b.yaml line 195).

**Success criteria:**
- Any build with unaddressed CRITICAL or HIGH fails deploy
- Any build with more than 5 deferred items fails deploy

---

### Mechanism 9 — Recovery Pipeline [WALL]
**Purpose:** When a deterministic gate reports FAIL, a recovery branch auto-activates. Opus on high effort: diagnoses what broke, writes a focused fix PRD, executes it, re-runs the gate. If recovery still fails, the next phase is halted and the run ends with a plain-English report — not a log dump.

**Classification:** WALL. Clear pass/fail rules, implemented via conditional `when:` branches.

**Model:** **`model: opus`, `effort: high`.** Non-negotiable. This is the critical recovery moment. (The PRD says "Opus 4.7" colloquially; Archon's alias is `opus` and the SDK resolves to the latest Opus release. No literal "4.7" string is valid in YAML.)

**Activation rule:** Any gate emits `FAIL` on stdout. Recovery branch runs immediately — Archon cannot count "two consecutive failures" across separate runs, because it is a forward-only DAG with no failure-branch primitive. If the owner wants a two-strike rule, that logic must be implemented INSIDE the gate script (tracking state in `$ARTIFACTS_DIR/gate-attempts.json`).

**Architectural note (why it's wired this way):**
- Archon has no `on_failure:` field and no error-handling DAG branch.
- When a gate node hard-fails, default `trigger_rule: all_success` skips everything downstream, and a recovery node cannot inspect the failed node's output (condition-evaluator.ts returns empty string for outputs of failed nodes).
- Solution: gates exit 0 and emit `PASS`/`FAIL` on stdout. Archon captures that as `$gate.output`. Downstream recovery nodes use `when:` to branch on that value. An aggregator node uses `trigger_rule: all_done` to merge the PASS and recovery-PASS paths before the next phase.

**Five nodes per phase:**

**Gate (exits 0, emits PASS/FAIL):**
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

**Recovery branch (runs only when gate said FAIL):**
```yaml
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
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
  depends_on: [phase-1-recovery-execute]
  when: "$phase-1-compliance.output == 'FAIL'"
```

**Final-status aggregator (merges the two success paths — initial PASS or recovery PASS):**
```yaml
# Phase 2 only proceeds if either:
#   (a) compliance gate passed first time, OR
#   (b) recovery ran AND its regate passed.
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

- id: phase-2-execute
  command: build-implement
  depends_on: [phase-1-final-status]   # hard fail here halts phase 2
  model: sonnet
  context: fresh
```

**Why this works:**
1. Gate nodes exit 0 and emit `PASS`/`FAIL`. Archon captures that as `$gate.output`.
2. Recovery branch uses `when:` — a supported field in Archon's condition-evaluator. Only runs on FAIL.
3. `phase-1-final-status` aggregates. `trigger_rule: all_done` runs once all upstream nodes have settled (completed, failed, or skipped — dag-executor.ts line 652). Recovery-regate will be in `skipped` state when the initial gate passed; `all_done` still fires.
4. Bash nodes reference `$<node>.output` — Archon substitutes via `substituteNodeOutputRefs` with `escapeForBash=true` which single-quotes the value safely.
5. If final-status exits 1, downstream phase 2 is skipped by default `trigger_rule: all_success`. Pipeline halts at the right place.

**Output files (all at `$ARTIFACTS_DIR/recovery-N/`):**
- `triage-report.md` — plain English, readable by user (written by `recovery-diagnose`)
- `fix-prd.md` — auto-generated fix spec (written by `recovery-fix-prd`)
- `recovery-execution-report.md` — what got changed (written by `recovery-execute`)
- `final-failure-report.md` — only if the regate also fails

**Token budget per activation:** 50–120K Opus tokens. Only runs on gate FAIL.

**Success criteria:**
- When manually triggered on the YT Strategy Lab failure artifacts: produces a triage-report.md that correctly identifies "fix agent skipped 34 issues" as root cause
- Writes a fix-prd.md that, if executed, would address the 34 missed issues
- After `recovery-execute` runs, the regate emits `PASS`

**Alternative (heavier, matches original intent more literally):** Build the recovery pipeline as a single separate workflow (`prd-pipeline-c-recovery.yaml`) that a human or cron-trigger launches on gate failure. Cleaner node boundaries but breaks the "unattended" claim of S9. The inline `when:`-branch pattern above is the one compatible with Archon's engine as-is.

---

### Mechanism 10 — PRD Archive [WALL]
**Purpose:** Every PRD pipeline run archives its final artifacts into a central, chronologically-sorted folder so the user can browse any past PRD without digging through artifact directories.

**Classification:** WALL.

**Deterministic:** 100% (it's a file copy script).

**Contract:**
- Input: `$ARTIFACTS_DIR/runs/{run-id}/` (the run that just completed)
- Output: `docs/generated-prds/{YYYY-MM-DD}__{build-name}/` containing:
  - `context_packet.json` (full final version)
  - `phases/` folder (all phase files)
  - `CLAUDE.md`, `BUILD_RULES.md`, `README.md`
  - `triage-report.md` + `fix-prd.md` if recovery ran
  - `final-summary.md` (single-page human-readable overview)
- Also: `docs/generated-prds/INDEX.md` — a living table: date | build name | status (shipped / failed / recovered) | token cost | one-line summary

**Script:** Python translation per HANDOFF at `.archon/scripts/archive-prd.py`. Takes three args (artifacts dir, build name, status). Logic:

```
DATE = today (YYYY-MM-DD)
ARCHIVE = docs/generated-prds/{DATE}__{BUILD_NAME}/
mkdir -p ARCHIVE
copy context_packet.json, phases/, *.md from artifacts dir into ARCHIVE
append row to docs/generated-prds/INDEX.md: "- {DATE} | {BUILD_NAME} | {STATUS} | [{ARCHIVE}]({ARCHIVE}/)"
```

**YAML wiring (in prd-pipeline-c.yaml):**
```yaml
# Upstream aggregator that reports whether any recovery ran this build.
# If any `$ARTIFACTS_DIR/recovery-*/` directory exists, mark the run "recovered";
# otherwise "shipped". Gives archive-prd a real status signal instead of a hardcode.
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

Reason: `$BASE_BRANCH` is a real Archon-provided variable (per Archon CLAUDE.md line 670). Used here as a stand-in for "build name" — the owner can swap for any other identifier that makes sense. The archive destination is `docs/generated-prds/` in the **Greptacular repo** (not in Archon's workspace); the Python script's cwd resolves relative to the Greptacular repo because the workflow runs there. `$recovery-status-summary.output` is left bare — Archon's `substituteNodeOutputRefs` with `escapedForBash=true` (dag-executor.ts line 1357) single-quotes the value via `shellQuote` (line 183), so argv[3] receives a properly-quoted `'shipped'` or `'recovered'` without needing outer quotes.

**Success criteria:**
- After any pipeline run, `docs/generated-prds/{date}__{name}/` exists
- INDEX.md lists the new entry
- All PRDs browseable in one folder

---

### Mechanism 11 — Regression Harness [WALL]
**Purpose:** Every time the pipeline itself changes (new gate script, new prompt, YAML edit), automatically re-run a standardized test suite to confirm nothing broke. Self-testing for the pipeline.

**Classification:** WALL.

**Deterministic:** 100%.

**Contract:**
- Input: `.archon/` directory (or a git commit SHA)
- Runs: Tests A, B, C (see §9)
- Output: `regression-report.md` with PASS/FAIL per test + exit code

**Activation:** Can be run manually (`npm run regression`) or auto-triggered on any commit that touches `.archon/`.

**Script:** Python at `.archon/scripts/regression-harness.py`. Reads fixtures dir and scripts dir from env vars (Archon script nodes cannot receive argv — see M1 evidence).

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

**YAML wiring:** Do NOT add regression-harness as a node inside `prd-pipeline-c.yaml`. A `depends_on: []` node is a root node and would run on every invocation of the main pipeline, burning tokens before every real build. Instead, split it into its own workflow file.

**DELETE this block from `prd-pipeline-c.yaml` (it must not appear in the main pipeline):**

```yaml
- id: regression-harness
  bash: |
    FIXTURES=".archon/test-fixtures" \
    SCRIPTS_DIR=".archon/scripts" \
    python .archon/scripts/regression-harness.py
  depends_on: []   # standalone — invoked manually or by a separate workflow
```

**CREATE a new standalone file `.archon/workflows/regression-harness.yaml` with this content:**

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

Reason: env vars pass in where args can't. Paths are relative to the workflow cwd (the repo root) because Archon does not export `$ARCHON_HOME` to bash child processes — relative `.archon/scripts/...` paths resolve unconditionally. Workflow files are discovered independently by `workflow-discovery.ts`, so the main pipeline and the regression workflow coexist cleanly.

**Success criteria:**
- Running regression-harness on current .archon/ produces PASS
- Deliberately breaking a gate script → running regression → FAIL with specific reason

---

### Mechanism 12 — Feature Toggles [DOOR]
**Purpose:** Central config file that enables/disables each optional mechanism. Lets the user kill a feature that's causing noise without rewriting code.

**Classification:** DOOR (exact format is a judgment call).

**File:** `.archon/features.yaml`

```yaml
# Toggle any of these on/off. Defaults are the recommended production settings.
# If a toggle is missing, it defaults to the value below.

recovery_pipeline: true       # M9: auto-diagnose and fix on gate failure
prd_archive: true              # M10: copy PRDs to docs/generated-prds/
regression_harness: true       # M11: self-tests before pipeline changes
codebase_cartographer: true    # M7: Haiku builds CODEBASE_MAP.md after build
scoped_claude_md: true         # M6: per-directory CLAUDE.md auto-attach
build_intelligence: false      # Phase 3: learn from prior builds — OFF until 5+ builds logged
build_intelligence_mode: defensive  # Options: defensive (warn about known failures) only
                                    # "prescriptive" mode is NOT implemented by design
```

**Each toggle is enforced by an upstream `read-flag-*` bash node** that emits `'true'` or `'false'` as its stdout. Downstream nodes use a `when:` condition against that output. Archon's `when:` only reads `$nodeId.output[.field]` — it cannot read external files directly, and there is no `enabled: false` field on nodes.

**Example wiring for `recovery_pipeline: true/false`:**

```yaml
- id: read-flag-recovery
  bash: |
    uv run --with pyyaml python -c "import yaml; c=yaml.safe_load(open('.archon/features.yaml')); print(str(c.get('recovery_pipeline',True)).lower())"
  depends_on: []   # or earliest possible ancestor

- id: phase-1-recovery-diagnose
  command: recovery-diagnose
  when: "$phase-1-compliance.output == 'FAIL' && $read-flag-recovery.output == 'true'"
  depends_on: [phase-1-compliance, read-flag-recovery]
  model: opus
  effort: high
```

Applying this pattern to all 6 toggled mechanisms (`recovery_pipeline`, `prd_archive`, `regression_harness`, `codebase_cartographer`, `scoped_claude_md`, `build_intelligence`) adds 6 read-flag nodes at pipeline start. Every read-flag node MUST use the `uv run --with pyyaml python -c "..."` prefix shown above — plain `python -c "import yaml; ..."` will fail on a fresh Windows install because Archon's bash nodes invoke whatever `python` is in PATH with no automatic dependency install (dag-executor.ts line 1362), and PyYAML is not guaranteed to be present. `uv` is already required by Archon's script-node runtime, and `--with pyyaml` provisions it into an ephemeral venv. `features.yaml` itself lives at `.../source/.archon/features.yaml` per HANDOFF §3.

**Fallback if the read-flag pattern is too heavy for Phase 1:** Remove M12 from Phase 1 entirely and wire toggles manually by commenting out nodes in the YAML when a feature is not desired. Re-introduce the read-flag pattern in Phase 1b.

**Success criteria:**
- Setting `prd_archive: false` skips the archive step (via `$read-flag-archive.output == 'true'`) but pipeline still completes
- Setting `recovery_pipeline: false` skips the recovery branch on gate failure (reverts to plain halt-on-failure — not recommended, but useful for debugging)
- Missing features.yaml → read-flag node's YAML `get(..., True)` default applies, no error

---

## 5. Phases

### Phase 1 — Core Gates + Safety Net (highest urgency, ~1 day)
**Mechanisms:** 1, 2, 3, 8, 9, 10, 11, 12
**Why first:** M1/M2/M3/M8 form the closed loop that would have caught YT Strategy Lab. M9 (Recovery Pipeline) is what makes failure non-hostile to a non-coder. M10–M12 are small infrastructure items that ride along cheaply.

**Files to create:**
- `.archon/scripts/compliance-gate.py` (Python per HANDOFF bash→Python rule)
- `.archon/scripts/full-checkpoint.py`
- `.archon/scripts/deploy-gate.py`
- `.archon/scripts/archive-prd.py`
- `.archon/scripts/regression-harness.py`
- `.archon/commands/recovery-diagnose.md`
- `.archon/commands/recovery-fix-prd.md` (matches `command: recovery-fix-prd` in M9 wiring)
- `.archon/commands/recovery-execute.md`
- `.archon/features.yaml`

Per HANDOFF.md §2 Correction B — do NOT edit the originals. Create copies:

**Files to CREATE (not edit):**
- `.archon/commands/prd-stage-10-v2.md` — copy of prd-stage-10.md with exemption language removed
- `.archon/commands/build-fix-v2.md` — copy of build-fix.md with mandatory contract block added; pipeline YAML assigns `model: opus` to this node
- `.archon/workflows/prd-pipeline-c.yaml` — copy of prd-pipeline-b.yaml with gate/recovery/archive nodes inserted and `command:` references updated to the `-v2` variants

**Token estimate:** ~65K

### Phase 2 — Structural (~2–3 days)
**Mechanisms:** 4, 5, 6
**Why second:** Multi-phase loop + test writer + scoped CLAUDE.md fix the hidden problems that didn't bite YT Strategy Lab (because it was one phase) but will bite the next bigger build.

**Files to create:**
- `.archon/commands/test-writer.md` — the prompt file is as shown in §4 M5.
  Node wiring in prd-pipeline-c.yaml:

  ```yaml
  - id: phase-1-test-writer
    command: test-writer
    prompt: "phase-1"
    depends_on: [phase-1-execute]
    model: sonnet
    context: fresh
  ```
  (Repeat per phase, prefixing ids with `phase-N-` and passing the matching phase id via `prompt:`.)
- `.archon/commands/phase-handoff.md`
- `.archon/workflows/prd-pipeline-c.yaml` already created in Phase 1 (per HANDOFF §2 Correction B); Phase 2 extends it with per-phase unrolled groups (M4), the test-writer node above, and the `claude-md-presence-check` audit node (M6).
- `.archon/scripts/lint-autofix.py` (Python per HANDOFF bash→Python rule)
- `.archon/scripts/claude-md-audit.py` (for M6 soft-check audit node)

**Files to update (via `-v2` copies — HANDOFF §2 Correction B):**
- The Phase 1 `prd-stage-10-v2.md` is extended in Phase 2 to also emit per-directory CLAUDE.md files
- `.archon/commands/build-execute-v2.md` — copy of build-execute.md with the "Directory Rules (soft guidance)" section appended (M6)

**Token estimate:** ~90K

### Phase 3 — Learning Loop (optional, ~3–5 days)
**Mechanisms:** 7 + build-intelligence-handoff.md implementation
**Why last:** Quality-of-life and long-term learning. Not required to fix the current failure mode. Defer if Phase 1+2 ship cleanly.

**Files to create:**
- `.archon/commands/codebase-cartographer.md`
- `.archon/scripts/record-build-metrics.py` (Python per HANDOFF bash→Python rule)
- Build-intelligence infrastructure per existing handoff doc

**Token estimate:** ~70K

**Total build budget:** 200K ± 40K.

---

## 6. Dependencies Between Mechanisms

```
M1 (compliance-gate) ──┐
M2 (full-checkpoint) ──┤
M3 (prompt tighten)  ──┼─► integrate into pipeline ──► M4 (YAML loop)
M8 (deploy-gate)     ──┘                                    │
                                                            ├─► M5 (test writer)
                                                            ├─► M6 (scoped CLAUDE.md)
                                                            └─► M7 (cartographer) [optional]
```

Phase 1 mechanisms are independent and can build in parallel. Phase 2 depends on Phase 1 being merged (otherwise you'd be wiring scripts into a pipeline that doesn't have scripts yet).

---

## 7. Full Checkpoint Criteria (per phase of THIS build)

### Phase 1 complete when:
- [ ] All 5 Python scripts exist at `.archon/scripts/` (`compliance-gate.py`, `full-checkpoint.py`, `deploy-gate.py`, `archive-prd.py`, `regression-harness.py`)
- [ ] Running `python .archon/scripts/compliance-gate.py <YT-lab-fixture>` returns exit 1 with an issue count mismatch message
- [ ] Running `python .archon/scripts/full-checkpoint.py <broken-phase-fixture> <sha>` returns exit 1
- [ ] Running `python .archon/scripts/deploy-gate.py <YT-lab-fixture>` returns exit 1
- [ ] Grep for "separate task" in `.archon/commands/prd-stage-10-v2.md` and `build-fix-v2.md` returns 0 matches
- [ ] `prd-pipeline-c.yaml` wires the bash nodes for gates + recovery branch + archive before deploy
- [ ] An end-to-end dry run on a trivial spec produces build + gate PASS or gate FAIL with a real reason

### Phase 2 complete when:
- [ ] `prd-pipeline-c.yaml` runs a 2-phase unrolled test build with fresh agent contexts per phase
- [ ] test-writer agent produces test files equal in count to WALL steps in the phase
- [ ] Each directory created by the build has a CLAUDE.md (via the `claude-md-presence-check` audit node)
- [ ] If phase 1 of a test build fails compliance-gate (emits `FAIL`) AND recovery also fails, phase 2 never starts

### Phase 3 complete when:
- [ ] `CODEBASE_MAP.md` exists after a build and covers every top-level module
- [ ] build-metrics.jsonl grows by one entry per build
- [ ] Stage 0 reads the last 5 entries and injects "common failures" into context

---

## 8. Success Criteria (the whole spec)

**North Star:** Re-run the YT Strategy Lab v2 build end-to-end with no human intervention. Expected outcomes (either is acceptable):
- **Happy path:** Deploy succeeds. All 51 review issues addressed. `deferred.md` has ≤5 items, each with valid reasons.
- **Controlled failure:** Pipeline halts at a specific gate with a mechanical reason ("compliance-gate: 34 issues unaddressed"). No deploy. Human reads one file to know why.

**Forbidden outcome:** "Deploy succeeded with 34 issues deferred." If this happens, the spec failed.

**Quantitative:**
- Zero instances of exemption language in commands/
- Every new check is deterministic (bash/python, not agent)
- Phase isolation verified: phase 2 agent cannot see phase 1 agent's context

---

## 9. Test Plan

Three tests. All three must pass before Phase 1 is declared done. All three run automatically via M11 (`regression-harness.py`).

### Test A — Gate Script Unit Tests (deterministic, ~30 sec)
**Purpose:** Confirm each gate script does exactly what it claims.

Fixtures (checked into `.archon/test-fixtures/`):
- `yt-strategy-lab-fail/` — snapshot of the actual failed run (reviews with 51 issues, fix-report with 17 fixes, no deferred.md)
- `task-manager-pass/` — snapshot of the clean Team Task Manager run
- `broken-phase/` — phase dir with a deliberately failing test + unauthorized file change

Assertions (scripts are Python per HANDOFF bash→Python rule; invoke via `python .archon/scripts/<name>.py <arg>`):
1. `python .archon/scripts/compliance-gate.py .archon/test-fixtures/yt-strategy-lab-fail` → exit 1, stderr contains "34 issues unaddressed"
2. `python .archon/scripts/compliance-gate.py .archon/test-fixtures/task-manager-pass` → exit 0
3. `python .archon/scripts/full-checkpoint.py .archon/test-fixtures/broken-phase <sha>` → exit 1, identifies the failing test
4. `python .archon/scripts/deploy-gate.py .archon/test-fixtures/yt-strategy-lab-fail` → exit 1, lists remaining CRITICAL/HIGH
5. `python .archon/scripts/deploy-gate.py .archon/test-fixtures/task-manager-pass` → exit 0
6. `python .archon/scripts/archive-prd.py .archon/test-fixtures/task-manager-pass test shipped` → creates `docs/generated-prds/{date}__test/` and appends to INDEX.md

Fixtures must be real directories with pre-made `review-*.md`, `fix-report.md`, `files_allowed.json`. These fixtures do NOT exist yet — creating them is part of Phase 1.

**Pass criteria:** All 6 assertions hold. Zero false positives, zero false negatives.

### Test B — Red-Team Replay on YT Strategy Lab (the key regression)
**Purpose:** Prove the new pipeline would have caught the actual historical failure.

**Availability caveat:** This test assumes a snapshot of the YT Strategy Lab v2 workspace (pre-deploy) exists as a git tag or preserved artifact bundle. If artifacts were not preserved, the test is ungated — flag to the owner and proceed with Tests A and C only.

Steps:
1. Restore the YT Strategy Lab v2 workspace to the state it was in right before deploy ran (use git tag / artifact snapshot)
2. Run the v2 pipeline (`prd-pipeline-c.yaml`) from `build-fix-v2` onward (skip re-running reviews — use the recorded review outputs)
3. Observe: `compliance-gate.py` MUST emit `FAIL` on stdout. Deploy MUST not run.
4. Observe: Recovery Pipeline (M9) activates via `when:` branch. Triage report names root cause as "fix agent skipped 34 issues under exemption language."
5. Observe: Recovery fix PRD is written. `recovery-execute` runs. Regate emits `PASS`.
6. Observe: `phase-N-final-status` aggregates to PASS; deploy now proceeds with 0 unaddressed CRITICAL/HIGH.

**Pass criteria:** The historical failure is physically impossible to reproduce in v2.

### Test C — Fresh Tiny Build End-to-End (~15 min, ~40K tokens)
**Purpose:** Smoke test the entire pipeline on something small and new.

Input spec: "A one-page React component that displays a countdown timer with start/stop/reset buttons, with tests."

Steps:
1. Run full pipeline (Stages 0–10 PRD maker untouched, new build-half with all 12 mechanisms active)
2. Observe per-phase isolation (if multi-phase), gate pass/fail at each checkpoint
3. Check final artifacts:
   - Archive folder exists at `docs/generated-prds/{date}__countdown-timer/`
   - INDEX.md updated
   - `CODEBASE_MAP.md` exists (if M7 toggle on)
   - `deferred.md` has ≤3 entries with valid reasons
   - Lint, typecheck, tests all pass

**Pass criteria:** Countdown timer app builds, tests pass, deploy gate green, archive populated. Total tokens within 20% of estimate.

### Deliberate break-and-fix (bonus, not blocking)
Break `compliance-gate.py` (flip a `<` to `>` in the severity comparison). Run the regression harness. Expect Test A to fail with a specific message pointing at the wrong comparison. Revert. Re-run. Pass.

---

## 10. Rollback Plan

If v2 pipeline misbehaves:
1. Switch the Archon runner back to `prd-pipeline-b.yaml` (v1) — it still exists, unmodified (per HANDOFF §2 Correction B, we created `prd-pipeline-c.yaml` alongside rather than editing v1)
2. The new Python scripts and `-v2` command files are standalone; they don't break v1 because Archon discovers commands by filename and v1 references `build-fix`, not `build-fix-v2`
3. No in-place edits to the original `prd-stage-10.md` or `build-fix.md` were made, so there is nothing to revert in those files

---

## 11. Token Budget for Build

Estimated breakdown for the coder executing this spec:

| Phase | Mechanism Work | Tokens |
|---|---|---|
| P1 | 5 bash scripts + 3 recovery prompts + features.yaml + YAML edits + prompt edits (M1, M2, M3, M8, M9, M10, M11, M12) | 65K |
| P2 | 2 new prompt files + 1 new YAML + 1 new bash + prompt edits (M4, M5, M6) | 90K |
| P3 | 1 prompt file + 1 bash + build-intelligence scaffolding (M7 + optional learning layer) | 70K |
| **Regression runs** | Test A/B/C execution during development | ~25K |
| **Total** | | **~250K** |

Fits in a single build if batched. Recommended split: P1 alone (so we validate gates before wiring in the YAML loop), then P2 + P3 together.

**Note on Recovery Pipeline (M9):** Its 50–120K Opus budget is *runtime* cost, not build cost. It only burns tokens when a gate fails on a real build — not during implementation of this spec.

---

## 12. Out of Scope

- Rewriting the PRD maker (Stages 0–10) — they work
- Replacing Archon's engine — we use what we have
- Adding agents for agents' sake (e.g., "review the reviewer") — violates Standards S1
- Real-time agent monitoring / human-in-the-loop — owner is not a coder, cannot review mid-stream
- MCP / Toolshed integration — out of current scope (Stripe has it; we don't need it yet)
- Rewriting the YT Strategy Lab build — that's a separate follow-up once this pipeline lands

---

## 13. Notes for the Builder

- This is a **surgical upgrade**, not a rewrite. No existing files are edited in place — the entire upgrade is additive via `-v2`-suffixed command copies and a new `prd-pipeline-c.yaml` (per HANDOFF §2 Correction B).
- All new scripts go in `.archon/scripts/` (new directory if needed). All new scripts are Python (`.py`), not bash — Archon's script-node runtime map supports `.py → uv` but not `.sh`, and Windows bash compatibility requires git-bash which is not guaranteed.
- All new prompts go in `.archon/commands/` alongside existing ones. Naming: `<name>-v2.md` when replacing an existing command; plain `<name>.md` for brand-new commands.
- The v2 YAML is additive — v1 stays as a safety net. Archon's command loader discovers by filename, so `build-fix` and `build-fix-v2` co-exist cleanly.
- **`for_each` does NOT exist in Archon.** Archon's `loop:` node is an AI-prompt iteration, not an array iterator. Per-phase execution is implemented via manual unroll (M4 AFTER block). No alternative is needed — this is settled.
- **Gates exit 0, emit `PASS`/`FAIL` on stdout.** Archon has no `on_failure:` branch; recovery branching uses `when:` against `$gate.output`. See M9 for the canonical pattern.
- **Script nodes cannot receive CLI args** (`uv run` invocation, per dag-executor.ts line 1569). All args are passed via bash-node wrappers using `$ARTIFACTS_DIR` substitution and `$<node>.output` references, or via env vars for standalone scripts.
- When in doubt, bias toward deterministic. If you find yourself writing an agent to "decide if X passed," stop and write a Python script instead.

---

## 14. Standards Compliance Self-Check (builder must verify before done)

- [ ] S1 — Every gate in this spec is a Python script invoked from a bash node, not an agent
- [ ] S2 — No exemption language in any prompt this spec touches (enforced on the `-v2` copies of `prd-stage-10` and `build-fix`)
- [ ] S3 — Gates emit `PASS`/`FAIL` on stdout (exit 0 for the gate node itself); recovery branches off `$gate.output == 'FAIL'`
- [ ] S4 — Retry caps are numeric and enforced in the Python scripts or YAML `retry:` config, not in prompts
- [ ] S5 — Every phase-N node gets `context: fresh` in the unrolled YAML
- [ ] S6 — CLAUDE.md files scoped to directories, not stuffed into root (soft check via `claude-md-presence-check` audit node)
- [ ] S7 — Lint runs as part of `full-checkpoint.py` after each phase, not only at end
- [ ] S8 — Each agent has one job; no agent does two things (e.g., fix + tests)
- [ ] S9 — Every gate failure produces plain-English diagnosis (via `recovery-diagnose`) + auto-recovery attempt (via `recovery-execute`) before halting; no failure requires the user to read code

---

## 15. Model Assignment Table (where model choice actually matters)

Most of the pipeline stays Sonnet. Only the places where model choice moves the needle get upgraded. Opus is 5–6× the cost of Sonnet, so we only pay for it where judgment quality is load-bearing.

All values in the "New Model" column are Archon YAML aliases. No literal "Opus 4.7" string — Archon resolves `opus` to the latest Opus release via the Claude SDK (`sonnet`, `opus`, `haiku`, `claude-*`, `inherit` are the valid aliases; see Archon CLAUDE.md line 486).

| Node | Current Model | New Model | Effort | Reason |
|---|---|---|---|---|
| Stage 0–10 (PRD maker) | `sonnet` | **`sonnet` (unchanged)** | default | PRD maker already produces solid plans. Not the bottleneck. |
| `build-execute` (per phase) | `sonnet` | **`sonnet` (unchanged)** | default | Code execution is well-scoped by the contract. Sonnet is enough. |
| `test-writer` (M5) | N/A | **`sonnet`** | default | Mechanical: one test per WALL step. No judgment required. |
| `build-verify` | `sonnet` | **`sonnet` (unchanged)** | default | Advisory only — deterministic gates are the real check. |
| Four reviewers | `sonnet` | **`sonnet` (unchanged)** | default | Parallel, bounded scope per reviewer. Sonnet handles this. |
| **`build-fix-v2`** | `sonnet` | **`model: opus`** | `medium` | **PERMANENT UPGRADE.** This is where YT Strategy Lab broke. Fix agent has to judge ambiguous review items, trace cause-and-effect, and produce clean edits across 51 issues. Wired in prd-pipeline-c.yaml as `build-fix-v2` (copy-don't-overwrite per HANDOFF §2). |
| `phase-handoff` | N/A | **`haiku`** | default | Summarization. Haiku is correct. |
| `codebase-cartographer` (M7) | N/A | **`haiku`** | default | Mechanical file-tree walk. Haiku is correct. |
| `final-report` | N/A | **`haiku`** | default | Summarization. |
| **Recovery Pipeline M9.1 Diagnose** | N/A | **`model: opus`** | **`high`** | Must identify root cause from noisy evidence. Highest-stakes reasoning in the pipeline. |
| **Recovery Pipeline M9.2 Write Fix PRD** | N/A | **`model: opus`** | **`high`** | Writing a PRD that will actually work requires Opus-tier planning. |
| **Recovery Pipeline M9.3 Execute Fix** | N/A | **`model: opus`** | **`high`** | The user can't clean up after a sloppy recovery. Has to be right the first time. |
| Recovery Pipeline M9.4 Re-Gate | N/A | **N/A (bash)** | — | Deterministic. No model. |
| Compliance gate, full checkpoint, deploy gate, archive, regression | N/A | **N/A (bash)** | — | Deterministic by design (Standard S1). |

### Summary
- **1 permanent Sonnet→Opus upgrade:** `build-fix`. This is the fix for the YT Strategy Lab failure mode.
- **1 pipeline branch always on Opus high effort:** Recovery Pipeline (M9.1–M9.3). Only runs on gate failure, so cost is bounded.
- **Everything else stays Sonnet or Haiku.** We are not Opus-flooding the pipeline.

### Cost implication
Normal build (no recovery): tokens shift ~10% higher due to build-fix on Opus. Acceptable for the reliability gain.
Recovery build (gate failed): additional 50–120K Opus tokens. Only happens on actual failures, which should be rare after Phase 1 ships.
