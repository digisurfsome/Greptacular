# Archon Build-Half Upgrade (Stripe Blueprint Compliance)

**Status:** Ready to Build
**Author:** Derived from YT Strategy Lab v2 post-mortem + Stripe Minions articles
**Related specs:** `.claude/specs/spec-006-testing-layer.md`, `.claude/handoffs/build-intelligence-handoff.md`
**Scope:** Modify the Archon execution pipeline (not the PRD maker) to enforce deterministic gates, bounded contracts, and per-phase isolation.

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

**Script snippet:**
```bash
#!/usr/bin/env bash
# .archon/scripts/compliance-gate.sh
set -euo pipefail
ARTIFACTS_DIR="${1:?artifacts dir required}"

count_issues() {
  local severity="$1"
  grep -hE "^[*-] \*\*\[${severity}\]" \
    "$ARTIFACTS_DIR"/review-*.md 2>/dev/null | wc -l
}

count_fixes() {
  local severity="$1"
  grep -cE "^### Fix [0-9]+:.*\[${severity}\]" \
    "$ARTIFACTS_DIR/fix-report.md" 2>/dev/null || echo 0
}

critical_issues=$(count_issues CRITICAL)
critical_fixes=$(count_fixes CRITICAL)
high_issues=$(count_issues HIGH)
high_fixes=$(count_fixes HIGH)

echo "CRITICAL: $critical_issues issues, $critical_fixes fixes"
echo "HIGH: $high_issues issues, $high_fixes fixes"

if [[ $critical_fixes -lt $critical_issues ]]; then
  echo "FAIL: $((critical_issues - critical_fixes)) CRITICAL issues unaddressed" >&2
  exit 1
fi
if [[ $high_fixes -lt $high_issues ]]; then
  echo "FAIL: $((high_issues - high_fixes)) HIGH issues unaddressed" >&2
  exit 1
fi
echo "PASS: compliance gate"
```

**Success criteria:**
- Re-running on YT Strategy Lab artifacts: exit 1 with message "34 issues unaddressed"
- Re-running on Team Task Manager artifacts: exit 0

---

### Mechanism 2 — Full Checkpoint Script [WALL]
**Purpose:** End-of-phase gate. Runs lint + typecheck + tests + files_allowed diff. Replaces the agent-enforced checkpoint that Stage 8 currently embeds as markdown.

**Classification:** WALL.

**Deterministic:** 100%.

**Contract:**
- Input: `$PHASE_DIR/files_allowed.json`, `$PROJECT_DIR`, `$BASELINE_SHA` (git sha before phase started)
- Checks (in order, each must exit 0):
  1. `npm run lint` (or language-appropriate)
  2. `npm run typecheck` (or equivalent — Python: `mypy`, Rust: `cargo check`)
  3. `npm test` (or equivalent)
  4. `git diff --name-only $BASELINE_SHA` ⊆ `files_allowed` (no unauthorized files modified)
- Output: `phase-N-checkpoint-result.md` + exit code

**Script snippet:**
```bash
#!/usr/bin/env bash
# .archon/scripts/full-checkpoint.sh
set -euo pipefail
PHASE_DIR="${1:?phase dir}"
PROJECT_DIR="${2:?project dir}"
BASELINE_SHA="${3:?baseline sha}"

cd "$PROJECT_DIR"

# 1. Lint
npm run lint 2>&1 | tee "$PHASE_DIR/checkpoint-lint.log"

# 2. Typecheck
npx tsc --noEmit 2>&1 | tee "$PHASE_DIR/checkpoint-tsc.log"

# 3. Tests
npm test -- --run 2>&1 | tee "$PHASE_DIR/checkpoint-test.log"

# 4. Files allowed diff
changed=$(git diff --name-only "$BASELINE_SHA" | sort -u)
allowed=$(jq -r '.files_allowed[]' "$PHASE_DIR/files_allowed.json" | sort -u)
unauthorized=$(comm -23 <(echo "$changed") <(echo "$allowed"))

if [[ -n "$unauthorized" ]]; then
  echo "FAIL: unauthorized files changed:" >&2
  echo "$unauthorized" >&2
  exit 1
fi

echo "PASS: phase checkpoint"
```

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

The compliance gate script (.archon/scripts/compliance-gate.sh) runs after you finish.
It will count issues vs fixes. If it fails, the pipeline halts.
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
**Purpose:** Replace the single `build-execute` node with a loop that iterates per phase. Each iteration gets a fresh agent context and runs the full build → test → review → fix → gate cycle for that phase alone.

**Classification:** DOOR. Several valid ways to structure this in Archon's YAML; we pick one.

**Chosen approach:** Template-based `for_each` if Archon supports it; otherwise, unroll manually (generate phase-1, phase-2, phase-3 node groups from a phase manifest at pipeline-start time).

**YAML snippet (for_each variant):**

```yaml
# .archon/workflows/prd-pipeline-b-v2.yaml
version: 2
name: prd-pipeline-b-v2
description: PRD pipeline with deterministic gates and per-phase loop

nodes:
  # Stages 0-10 unchanged (omitted for brevity)

  # New: per-phase loop
  - id: build-phase-loop
    type: for_each
    over: $stage-10.output.phases  # array from PRD maker
    as: phase
    depends_on: [stage-10]
    body:
      - id: build-execute-phase
        command: build-execute
        context: fresh
        model: sonnet
        input: "$phase"

      - id: build-lint-autofix
        type: script
        script: .archon/scripts/lint-autofix.sh
        args: ["$PROJECT_DIR"]
        depends_on: [build-execute-phase]

      - id: test-writer
        command: test-writer
        context: fresh
        model: sonnet
        depends_on: [build-lint-autofix]
        input: "$phase"

      - id: build-verify
        command: build-verify
        context: fresh
        model: sonnet
        depends_on: [test-writer]

      - id: reviews
        type: parallel
        depends_on: [build-verify]
        nodes:
          - id: review-correctness
            command: build-review-correctness
            context: fresh
            model: sonnet
          - id: review-failures
            command: build-review-failures
            context: fresh
            model: sonnet
          - id: review-tests
            command: build-review-tests
            context: fresh
            model: sonnet
          - id: review-simplify
            command: build-review-simplify
            context: fresh
            model: sonnet

      - id: build-fix
        command: build-fix
        context: fresh
        model: sonnet
        depends_on: [reviews]

      - id: compliance-gate
        type: script
        script: .archon/scripts/compliance-gate.sh
        args: ["$ARTIFACTS_DIR"]
        depends_on: [build-fix]

      - id: full-checkpoint
        type: script
        script: .archon/scripts/full-checkpoint.sh
        args: ["$PHASE_DIR", "$PROJECT_DIR", "$BASELINE_SHA"]
        depends_on: [compliance-gate]

      - id: phase-handoff
        command: phase-handoff
        context: fresh
        model: haiku
        depends_on: [full-checkpoint]
        input: "$phase"

  - id: codebase-cartographer
    command: codebase-cartographer
    context: fresh
    model: haiku
    depends_on: [build-phase-loop]

  - id: final-report
    command: build-final-report
    context: fresh
    model: haiku
    depends_on: [codebase-cartographer]

  - id: deploy-gate
    type: script
    script: .archon/scripts/deploy-gate.sh
    args: ["$ARTIFACTS_DIR"]
    depends_on: [final-report]

  - id: deploy
    command: build-deploy
    model: sonnet
    depends_on: [deploy-gate]
```

**If Archon doesn't support `for_each`:** unroll — Stage 10 writes out `phase-1.yaml`, `phase-2.yaml`, etc. and a wrapper YAML includes them sequentially. Slightly more files, same behavior.

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
- `$PHASE_FILE` — the phase spec including all WALL steps
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
- All tests pass (via full-checkpoint.sh)

---

### Mechanism 6 — Scoped CLAUDE.md Auto-Attach [DOOR]
**Purpose:** Follow Stripe's pattern — per-directory rule files auto-read by agents when they traverse that directory. Reduces global context bloat.

**Classification:** DOOR.

**Approach:**
- During Stage 10, emit a `CLAUDE.md` for each new major directory the phase creates (e.g., `server/services/CLAUDE.md`, `ui/src/components/yt-lab/CLAUDE.md`)
- These files state: what lives here, what conventions apply, what must not happen
- Build agent's prompt instructs it to read the CLAUDE.md when entering a directory

**Prompt edit to build-execute.md:**

```markdown
## Directory Rules
Before writing a file at path P, check for CLAUDE.md files in these locations (in order):
1. $(dirname P)/CLAUDE.md
2. $(dirname $(dirname P))/CLAUDE.md
3. Root CLAUDE.md

Read the most-specific one that exists. Its rules apply to your work in this file.
```

**Success criteria:**
- After a build, each domain directory has a CLAUDE.md
- CLAUDE.md files are scoped (under 200 lines each)

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

**Success criteria:**
- File exists after build
- Under 500 lines
- Every top-level source file appears in at least one table

---

### Mechanism 8 — Pre-Deploy Gate + Deferred Budget [WALL]
**Purpose:** Final mechanical gate before `build-deploy`. Reads the cumulative deferred.md files, caps total deferrals, verifies no CRITICAL/HIGH remain.

**Classification:** WALL.

**Deterministic:** 100%.

**Script snippet:**
```bash
#!/usr/bin/env bash
# .archon/scripts/deploy-gate.sh
set -euo pipefail
ARTIFACTS_DIR="${1:?artifacts dir}"

# Aggregate all deferred.md files
deferred_count=0
for f in "$ARTIFACTS_DIR"/runs/*/deferred.md; do
  [[ -f "$f" ]] || continue
  n=$(grep -cE "^[*-] " "$f" || echo 0)
  deferred_count=$((deferred_count + n))
done

# Check no remaining CRITICAL/HIGH in any review that lacks a matching fix
remaining=$(grep -hE "^[*-] \*\*\[(CRITICAL|HIGH)\]" \
  "$ARTIFACTS_DIR"/runs/*/review-*.md 2>/dev/null | wc -l)
fixed=$(grep -chE "^### Fix [0-9]+:" \
  "$ARTIFACTS_DIR"/runs/*/fix-report.md 2>/dev/null || echo 0)

if [[ $remaining -gt $fixed ]]; then
  echo "FAIL: $((remaining - fixed)) CRITICAL/HIGH items not in fix-report" >&2
  exit 1
fi

if [[ $deferred_count -gt 5 ]]; then
  echo "FAIL: $deferred_count deferrals exceeds budget of 5" >&2
  exit 1
fi

echo "PASS: deploy gate ($deferred_count deferrals, 0 remaining criticals)"
```

**Success criteria:**
- Any build with unaddressed CRITICAL or HIGH fails deploy
- Any build with more than 5 deferred items fails deploy

---

### Mechanism 9 — Recovery Pipeline [WALL]
**Purpose:** When a deterministic gate fails twice, this self-contained mini-pipeline auto-activates. Opus 4.7 on high effort: diagnoses what broke, writes a focused fix PRD, executes it, re-runs gates. Only if IT fails does the main pipeline halt for human attention — and even then, it halts with a plain-English report, not a log dump.

**Classification:** WALL. Clear pass/fail rules.

**Model:** **Opus 4.7, high effort.** Non-negotiable. This is the critical recovery moment.

**Activation rule:** Any gate returns exit 1 twice in a row. The second failure triggers this pipeline.

**Four internal steps:**

**Step 9.1 — Diagnose** (Opus 4.7 high effort)
- Reads: failing gate's stderr/output, all review-*.md files, fix-report.md, build logs, context_packet.json, relevant code files
- Writes: `triage-report.md` — plain-English summary with:
  - What broke (in user's language, not coder terms)
  - Why it broke (root cause, not symptom)
  - Confidence level in the diagnosis (HIGH / MEDIUM / LOW)

**Step 9.2 — Write Fix PRD** (Opus 4.7 high effort)
- Reads: triage-report.md
- Writes: `fix-prd.md` — a scoped PRD following the same Standards Layer as the main spec, but small (usually 1 mechanism, rarely 2)
- Includes: Drift anchor, mechanisms, success criteria, test plan

**Step 9.3 — Execute Fix** (Opus 4.7 high effort)
- Reads: fix-prd.md
- Implements: code edits, new tests, prompt tweaks — whatever the fix PRD specifies
- Writes: `recovery-execution-report.md` — what was changed and why

**Step 9.4 — Re-Gate** (deterministic)
- Re-runs the gates that originally failed
- If all pass → pipeline rejoins main flow, continues as if nothing happened
- If any fail → ONE more pass through 9.1–9.3 allowed
- If second pass also fails → halt with `final-failure-report.md` and notify user

**Output files (all at $ARTIFACTS_DIR/recovery-N/):**
- `triage-report.md` (plain English, readable by user)
- `fix-prd.md` (the auto-generated fix spec)
- `recovery-execution-report.md` (what got changed)
- `final-failure-report.md` (only if recovery also fails)

**Token budget per activation:** 50–120K Opus tokens. Only runs on failure.

**Success criteria:**
- When manually triggered on the YT Strategy Lab failure artifacts: produces a triage-report.md that correctly identifies "fix agent skipped 34 issues" as root cause
- Writes a fix-prd.md that, if executed, would address the 34 missed issues
- After execution, compliance-gate.sh exits 0

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

**Script snippet:**
```bash
#!/usr/bin/env bash
# .archon/scripts/archive-prd.sh
set -euo pipefail
RUN_DIR="${1:?run dir required}"
BUILD_NAME="${2:?build name required}"
STATUS="${3:?status: shipped|failed|recovered}"

DATE=$(date +%Y-%m-%d)
ARCHIVE="docs/generated-prds/${DATE}__${BUILD_NAME}"
mkdir -p "$ARCHIVE"

cp "$RUN_DIR/context_packet.json" "$ARCHIVE/" 2>/dev/null || true
cp -r "$RUN_DIR/phases" "$ARCHIVE/" 2>/dev/null || true
cp "$RUN_DIR"/*.md "$ARCHIVE/" 2>/dev/null || true

# Append to INDEX.md
INDEX="docs/generated-prds/INDEX.md"
[[ -f "$INDEX" ]] || echo "# Generated PRDs Index" > "$INDEX"
echo "- $DATE | $BUILD_NAME | $STATUS | [$ARCHIVE]($ARCHIVE/)" >> "$INDEX"
```

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

**Script snippet:**
```bash
#!/usr/bin/env bash
# .archon/scripts/regression-harness.sh
set -euo pipefail
FIXTURES="${1:-.archon/test-fixtures}"

echo "=== Test A: Unit tests on gate scripts ==="
bash .archon/scripts/compliance-gate.sh "$FIXTURES/yt-strategy-lab-fail" \
  && { echo "FAIL: should have exited 1"; exit 1; } || echo "PASS"
bash .archon/scripts/compliance-gate.sh "$FIXTURES/task-manager-pass" \
  || { echo "FAIL: should have exited 0"; exit 1; }
echo "PASS"

echo "=== Test B: Red-team replay ==="
# (full implementation in §9)

echo "=== Test C: Fresh tiny build ==="
# (full implementation in §9)

echo "=== ALL REGRESSION TESTS PASS ==="
```

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

**Each mechanism reads its flag at runtime.** If a toggle is `false`, the corresponding node becomes a no-op (or is skipped in the DAG). Toggles do not require a pipeline rebuild.

**Success criteria:**
- Setting `prd_archive: false` skips the archive step but pipeline still completes
- Setting `recovery_pipeline: false` reverts to plain halt-on-failure (not recommended, but useful for debugging)
- Missing file → all defaults applied, no error

---

## 5. Phases

### Phase 1 — Core Gates + Safety Net (highest urgency, ~1 day)
**Mechanisms:** 1, 2, 3, 8, 9, 10, 11, 12
**Why first:** M1/M2/M3/M8 form the closed loop that would have caught YT Strategy Lab. M9 (Recovery Pipeline) is what makes failure non-hostile to a non-coder. M10–M12 are small infrastructure items that ride along cheaply.

**Files to create:**
- `.archon/scripts/compliance-gate.sh`
- `.archon/scripts/full-checkpoint.sh`
- `.archon/scripts/deploy-gate.sh`
- `.archon/scripts/archive-prd.sh`
- `.archon/scripts/regression-harness.sh`
- `.archon/commands/recovery-diagnose.md`
- `.archon/commands/recovery-write-prd.md`
- `.archon/commands/recovery-execute.md`
- `.archon/features.yaml`

**Files to edit:**
- `.archon/commands/stage-10.md` (remove exemption language)
- `.archon/commands/build-fix.md` (if separate from Stage 10; ALSO change model: sonnet → opus)
- `.archon/workflows/prd-pipeline-b.yaml` (insert gate nodes + recovery branch + archive step)

**Token estimate:** ~65K

### Phase 2 — Structural (~2–3 days)
**Mechanisms:** 4, 5, 6
**Why second:** Multi-phase loop + test writer + scoped CLAUDE.md fix the hidden problems that didn't bite YT Strategy Lab (because it was one phase) but will bite the next bigger build.

**Files to create:**
- `.archon/commands/test-writer.md`
- `.archon/commands/phase-handoff.md`
- `.archon/workflows/prd-pipeline-b-v2.yaml` (new version, keep v1 as fallback)
- `.archon/scripts/lint-autofix.sh`

**Files to edit:**
- `.archon/commands/stage-10.md` (emit per-directory CLAUDE.md files)
- `.archon/commands/build-execute.md` (directory rules section)

**Token estimate:** ~90K

### Phase 3 — Learning Loop (optional, ~3–5 days)
**Mechanisms:** 7 + build-intelligence-handoff.md implementation
**Why last:** Quality-of-life and long-term learning. Not required to fix the current failure mode. Defer if Phase 1+2 ship cleanly.

**Files to create:**
- `.archon/commands/codebase-cartographer.md`
- `.archon/scripts/record-build-metrics.sh`
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
- [ ] All 3 bash scripts exist at `.archon/scripts/` and are executable
- [ ] Running `compliance-gate.sh` on YT Strategy Lab artifacts returns exit 1 with an issue count mismatch message
- [ ] Running `full-checkpoint.sh` on a deliberately broken test directory returns exit 1
- [ ] Running `deploy-gate.sh` on the same YT Strategy Lab run returns exit 1
- [ ] Grep for "separate task" in `.archon/commands/` returns 0 matches
- [ ] YAML has the 3 script nodes wired in sequence before deploy
- [ ] An end-to-end dry run on a trivial spec produces build + gate PASS or gate FAIL with a real reason

### Phase 2 complete when:
- [ ] `prd-pipeline-b-v2.yaml` runs a 2-phase test build with fresh agent contexts per phase
- [ ] test-writer agent produces test files equal in count to WALL steps in the phase
- [ ] Each directory created by the build has a CLAUDE.md
- [ ] If phase 1 of a test build fails compliance-gate, phase 2 never starts

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

Three tests. All three must pass before Phase 1 is declared done. All three run automatically via M11 (`regression-harness.sh`).

### Test A — Gate Script Unit Tests (deterministic, ~30 sec)
**Purpose:** Confirm each gate script does exactly what it claims.

Fixtures (checked into `.archon/test-fixtures/`):
- `yt-strategy-lab-fail/` — snapshot of the actual failed run (reviews with 51 issues, fix-report with 17 fixes, no deferred.md)
- `task-manager-pass/` — snapshot of the clean Team Task Manager run
- `broken-phase/` — phase dir with a deliberately failing test + unauthorized file change

Assertions:
1. `compliance-gate.sh yt-strategy-lab-fail` → exit 1, stderr contains "34 issues unaddressed"
2. `compliance-gate.sh task-manager-pass` → exit 0
3. `full-checkpoint.sh broken-phase` → exit 1, identifies the failing test
4. `deploy-gate.sh yt-strategy-lab-fail` → exit 1, lists remaining CRITICAL/HIGH
5. `deploy-gate.sh task-manager-pass` → exit 0
6. `archive-prd.sh task-manager-pass` → creates `docs/generated-prds/{date}__test/` and appends to INDEX.md

**Pass criteria:** All 6 assertions hold. Zero false positives, zero false negatives.

### Test B — Red-Team Replay on YT Strategy Lab (the key regression)
**Purpose:** Prove the new pipeline would have caught the actual historical failure.

Steps:
1. Restore the YT Strategy Lab v2 workspace to the state it was in right before deploy ran (use git tag / artifact snapshot)
2. Run the v2 pipeline from `build-fix` onward (skip re-running reviews — use the recorded review outputs)
3. Observe: `compliance-gate.sh` MUST exit 1. Deploy MUST not run.
4. Observe: Recovery Pipeline (M9) activates. Triage report names root cause as "fix agent skipped 34 issues under exemption language."
5. Observe: Recovery fix PRD is written. Execute it. Re-gate. Gate passes.
6. Observe: Deploy now proceeds with 0 unaddressed CRITICAL/HIGH.

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
Break `compliance-gate.sh` (change `-lt` to `-gt`). Run regression harness. Expect Test A to fail with a specific message pointing at the wrong comparison. Revert. Re-run. Pass.

---

## 10. Rollback Plan

If v2 pipeline misbehaves:
1. Switch the Archon runner back to `prd-pipeline-b.yaml` (v1) — it still exists, unmodified
2. The new scripts are standalone; they don't break v1
3. The Stage 10 prompt edits are the one thing that would need reverting — keep a git tag on the pre-edit commit

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

- This is a **surgical upgrade**, not a rewrite. Every existing file should be preserved unless explicitly edited in Section 4.
- All new scripts go in `.archon/scripts/` (new directory if needed).
- All new prompts go in `.archon/commands/` alongside existing ones.
- The v2 YAML is additive — v1 stays as a safety net.
- If `for_each` is not a native Archon construct, ask before picking an alternative (unrolled phases vs. a wrapper script).
- When in doubt, bias toward deterministic. If you find yourself writing an agent to "decide if X passed," stop and write a bash script instead.

---

## 14. Standards Compliance Self-Check (builder must verify before done)

- [ ] S1 — Every gate in this spec is a bash/python script, not an agent
- [ ] S2 — No exemption language in any prompt this spec touches
- [ ] S3 — `exit 1` on every failure mode; no agent-judged pass/fail
- [ ] S4 — Retry caps are numeric and enforced in the YAML, not prompts
- [ ] S5 — Every phase in the loop gets `context: fresh`
- [ ] S6 — CLAUDE.md files scoped to directories, not stuffed into root
- [ ] S7 — Lint runs as a script node during build, not only at end
- [ ] S8 — Each agent has one job; no agent does two things (e.g., fix + tests)
- [ ] S9 — Every failure mode produces plain-English diagnosis + auto-recovery attempt before halting; no failure requires the user to read code

---

## 15. Model Assignment Table (where model choice actually matters)

Most of the pipeline stays Sonnet. Only the places where model choice moves the needle get upgraded. Opus is 5–6× the cost of Sonnet, so we only pay for it where judgment quality is load-bearing.

| Node | Current Model | New Model | Effort | Reason |
|---|---|---|---|---|
| Stage 0–10 (PRD maker) | Sonnet | **Sonnet (unchanged)** | default | PRD maker already produces solid plans. Not the bottleneck. |
| `build-execute` (per phase) | Sonnet | **Sonnet (unchanged)** | default | Code execution is well-scoped by the contract. Sonnet is enough. |
| `test-writer` (M5) | N/A | **Sonnet** | default | Mechanical: one test per WALL step. No judgment required. |
| `build-verify` | Sonnet | **Sonnet (unchanged)** | default | Advisory only — deterministic gates are the real check. |
| Four reviewers | Sonnet | **Sonnet (unchanged)** | default | Parallel, bounded scope per reviewer. Sonnet handles this. |
| **`build-fix`** | Sonnet | **Opus 4.7** | medium | **PERMANENT UPGRADE.** This is where YT Strategy Lab broke. Fix agent has to judge ambiguous review items, trace cause-and-effect, and produce clean edits across 51 issues. This is the one permanent Sonnet→Opus swap. |
| `phase-handoff` | N/A | **Haiku** | default | Summarization. Haiku is correct. |
| `codebase-cartographer` (M7) | N/A | **Haiku** | default | Mechanical file-tree walk. Haiku is correct. |
| `final-report` | N/A | **Haiku** | default | Summarization. |
| **Recovery Pipeline M9.1 Diagnose** | N/A | **Opus 4.7** | **high** | Must identify root cause from noisy evidence. Highest-stakes reasoning in the pipeline. |
| **Recovery Pipeline M9.2 Write Fix PRD** | N/A | **Opus 4.7** | **high** | Writing a PRD that will actually work requires Opus-tier planning. |
| **Recovery Pipeline M9.3 Execute Fix** | N/A | **Opus 4.7** | **high** | The user can't clean up after a sloppy recovery. Has to be right the first time. |
| Recovery Pipeline M9.4 Re-Gate | N/A | **N/A (bash)** | — | Deterministic. No model. |
| Compliance gate, full checkpoint, deploy gate, archive, regression | N/A | **N/A (bash)** | — | Deterministic by design (Standard S1). |

### Summary
- **1 permanent Sonnet→Opus upgrade:** `build-fix`. This is the fix for the YT Strategy Lab failure mode.
- **1 pipeline branch always on Opus high effort:** Recovery Pipeline (M9.1–M9.3). Only runs on gate failure, so cost is bounded.
- **Everything else stays Sonnet or Haiku.** We are not Opus-flooding the pipeline.

### Cost implication
Normal build (no recovery): tokens shift ~10% higher due to build-fix on Opus. Acceptable for the reliability gain.
Recovery build (gate failed): additional 50–120K Opus tokens. Only happens on actual failures, which should be rare after Phase 1 ships.
