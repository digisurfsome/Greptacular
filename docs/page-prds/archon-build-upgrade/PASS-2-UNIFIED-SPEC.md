# Pass 2 — Unified Upgrade Spec (V3 Roadmap + Scorecard)

**Status:** Spec only. Executing agent ships this in a later session. No code in this doc.
**Pipeline target:** `C:\Users\lober\archon-pipeline-rebuild\.archon\workflows\pipeline-d.yaml` (24 nodes, shipped in Pass 1).
**Engine constraint:** Archon-native only — `prompt:` / `command:` nodes, `when:` / `depends_on`, dispatcher booleans, structured `output_format`. **No bash, no python, no workflow imports** (those don't exist in this engine).

---

## 1. Goal

Take pipeline-d from baseline → 9.5/10 (V3 Roadmap fixes) AND add a post-stage-10-v2 PRD quality gate (Scorecard) so a bad PRD never burns a Sonnet build cycle.

---

## 2. Source materials

| Source | What it brings |
|---|---|
| `PRD-MAKER-V3-ROADMAP.md` | 10 paint-by-numbers fixes (I/O examples, verify blocks, golden path, 2 reviewers, red team, reproducibility, compile check, deploy router, boundary gate, harness) |
| `M14-PRD-SELF-CHECK.md` | 3-reviewer scorecard, triage node, 3-tier kickback, 2-loop cap, owner notify, per-stage revision preamble |

---

## 3. Pre-flight — what already shipped (DO NOT redo)

| Pass | What landed | Where |
|---|---|---|
| Pass 0 | 11 mode-agnostic stage prompts with 6-mode preambles (`$BUILD_TYPE`) | `archon-pipeline-rebuild/.archon/commands/prd-stage-{00,01,02,03,04,05,07,08,09,10,10-v2}.md` |
| Pass 0 | Stage-06 gap confirmed intentional (skip, never re-author) | n/a |
| Pass 0.5 | contract-spec scoring overrides folded into stage-04 step 3 + stage-07 step 4 | stage files |
| Pass 1 | `pipeline-d.yaml` — 24 nodes, no bash, no python, fail-fast on @type | `archon-pipeline-rebuild/.archon/workflows/pipeline-d.yaml` |
| Pass 1 | 3 preflights (model-select, mode-select, build-type-select) + dispatcher booleans + import-bundle + 11 stage prompt-wrappers + prd-bundle-ready + 3 phases + 3 gates + final-review | same |
| Pass 1 Δ | 6 wrapper cards + 3-spot model defaults + `@type` REQUIRED + ASCII-only commit hooks | description block + wrappers |

Executing agent treats all of the above as locked. Touch them only where a fix explicitly says so.

---

## 4. The 11 fixes (ordered)

Numbering preserves the V3 Roadmap so cross-references survive. Fix 10 is folded as SATISFIED. Fix 11 = Scorecard (full spec in §5).

### Fix 1 — I/O examples + failure modes per mechanism
- **Problem:** stage-04 emits mechanism specs without concrete inputs/outputs/failure rows. Coder hallucinates the contract.
- **Fix:** edit `prd-stage-04.md` body to require, for every mechanism: an `inputs:` JSON example, an `outputs:` block (success + every error), a `failure_modes:` table (Failure | Symptom | Recovery — must cover network err / timeout / invalid input / service down / partial). If PRD lacks detail, mark `INCOMPLETE` and HALT for that mechanism.
- **Files touched:** `prd-stage-04.md` (one prompt edit, mode-agnostic — applies regardless of `$BUILD_TYPE`).
- **Tokens:** ~3K (prompt edit).
- **Depends on:** none.
- **What this gets you:** the mechanism spec a coder reads has zero "guess the JSON shape" gaps.

### Fix 2 — Acceptance test per deliverable (`verify:` blocks)
- **Problem:** phase files list "create file X" but nothing checks the file actually exposes what was specified.
- **Fix:** edit `prd-stage-07.md` (phase planning) AND `prd-stage-10-v2.md` (output generator) to require a `verify:` block per build item. Block declares: a one-line check the builder runs, and a single-line expected stdout/marker. Pipeline-native (no python script): add a new `verify-deliverables` prompt node per phase that the build phase calls — it Read's the phase file, parses every `verify:` block, asks the model to evaluate (or runs the inline check via the Bash tool the builder already has), emits PASS/FAIL JSON.
- **Files touched:** `prd-stage-07.md`, `prd-stage-10-v2.md`, pipeline-d.yaml (3 new prompt nodes — one per phase, gated `when: $gate-phase-N.output.status == "PASS"` chained before phase-N+1).
- **Tokens:** ~5K (2 prompt edits + 3 YAML node specs).
- **Depends on:** Fix 1 (mechanisms must have I/O so verify: blocks have something to check against).
- **What this gets you:** "done" means "the file does what was specified," not "a file exists with that name."

### Fix 3 — Golden Path Trace (Stage 8.5 equivalent)
- **Problem:** integration gaps hide between mechanisms. Nobody walks one real input through every component.
- **Fix:** new prompt node `golden-path-trace` after `stage-09`, before `stage-10-v2`. Reads stages 04 + 05 + 07 outputs from `$ARTIFACTS_DIR`. Picks one happy-path example, walks it step-by-step through every mechanism (exact input → exact output per step). Then walks one failure-path example. If a step can't be traced, emits `GAP: <question>` and HALTS. Output: `golden-path-trace.md` + JSON `{status: READY|GAP, gaps: []}`. Stage-10-v2 reads this and refuses to ship if `GAP` present.
- **Files touched:** pipeline-d.yaml (1 new node), `prd-stage-10-v2.md` (add gap check to validation step).
- **Tokens:** ~3K.
- **Depends on:** Fix 1 (needs I/O detail to trace).
- **What this gets you:** every integration seam between mechanisms gets walked end-to-end. Gaps surface BEFORE build.

### Fix 4 — Split final-review into 2 specialists
- **Problem:** pipeline-d's `final-review` is a single Opus node covering everything. Diluted lens.
- **Fix:** replace `final-review` with two parallel prompt nodes:
  - `review-correctness-and-contracts` — logic bugs, integration mismatches, interface drift, compliance contract block presence, exemption language scan.
  - `review-production-readiness` — security, performance, observability, deployment edge cases.
  Both run after `gate-phase-3`. A `final-review-synthesis` node (Sonnet, cheap) reads both reports, emits the SHIP / NEEDS_FIXES / BROKEN verdict.
- **Files touched:** pipeline-d.yaml (delete 1 node, add 3 nodes — 2 reviewers + 1 synthesis), 3 new command files at `.archon/commands/build-review-correctness-and-contracts.md`, `.archon/commands/build-review-production-readiness.md`, `.archon/commands/build-review-synthesis.md`.
- **Tokens:** ~4K.
- **Depends on:** none.
- **What this gets you:** two sharp lenses on the build instead of one fuzzy one. Same Opus cost (parallel).

### Fix 5 — Production Failure Red Team
- **Problem:** every reviewer plays "validate." Nobody plays "predict the dumbest production failure."
- **Fix:** new prompt node `red-team-production` after `golden-path-trace`, before `stage-10-v2`. Opus, fresh context, SRE persona. Outputs ranked top-5 likely production failures with: scenario / root cause / blast radius / detection lag / recovery / **exact prevention text** to add to a phase file. Then a small Haiku patch step (`red-team-patch`) reads the report and patches the prevention items into the right phase files (or notes them in stage-10-v2's open-questions).
- **Files touched:** pipeline-d.yaml (2 new nodes), `red-team-production.md` + `red-team-patch.md` command files.
- **Tokens:** ~3K.
- **Depends on:** Fix 3 (red team reads golden-path output).
- **What this gets you:** prevention text gets written INTO the PRD before any builder sees it.

### Fix 6 — Reproducibility (run seed + ledger + restart cache)
- **Problem:** same PRD twice = different output. Pipeline restart re-runs completed stages. Burns tokens.
- **Fix:** Archon-native version (NO python script):
  - **Seed node** at very top of pipeline (after dispatcher, before stage-00): `run-seed` prompt node hashes `$ARGUMENTS` + records pipeline version + model versions + run started_at. Writes `$ARTIFACTS_DIR/run-seed.json`. Emits `{run_id, prd_input_hash}`.
  - **Per-stage checkpoint:** add to every stage prompt's instructions: "after writing your stage outputs, also append one JSON line to `$ARTIFACTS_DIR/run-ledger.jsonl` with `{stage, output_hash, completed_at}`." Hash via prompt instruction (model computes a stable hash of the file it just wrote — model can do this).
  - **Restart skip:** add a 3-line check at the top of every stage prompt: "Read `run-ledger.jsonl` if it exists. If your stage's entry is present AND `prd_input_hash` matches the seed, emit `{status: CACHED}` and exit. Else proceed."
- **Files touched:** pipeline-d.yaml (1 new `run-seed` node), all 11 stage prompts (cache check + ledger append blocks — appended to existing prompts, do NOT touch the body or preamble).
- **Tokens:** ~6K (heaviest of the cheap fixes).
- **Depends on:** none.
- **What this gets you:** pipeline restart after a mid-run failure skips completed stages. Big time save on long runs. Plus same-input → same-output is now provable.

### Fix 7 — Programmatic compile check per phase
- **Problem:** nothing checks that files the phase CLAIMED to create actually exist + parse + export what was specified.
- **Fix:** Archon-native — replace V3's python script with a per-phase prompt node `phase-N-compile-check` between `phase-N` and `gate-phase-N`. Node uses `Read` + `Glob` + `Grep` to verify: every file in phase-N's `files_allowed` exists, every file the phase file declared as "create" was created, every named function/class is present in the file, no phantom imports. Emits PASS/FAIL JSON. `gate-phase-N` reads BOTH `phase-N.status` AND `phase-N-compile-check.status` — both must be PASS.
- **Files touched:** pipeline-d.yaml (3 new nodes — one per phase), 1 command file `phase-compile-check.md`.
- **Tokens:** ~3K.
- **Depends on:** none (Fix 2 strengthens it but they're independent).
- **What this gets you:** hallucinations ("I made the file" when no file exists) get caught before reviewer spend.

### Fix 8 — Deployment target router (Stage 0.5)
- **Problem:** every PRD assumes Linux+systemd. Docker / Windows / serverless deployments come out wrong.
- **Fix:** new prompt node `deployment-target` after dispatcher, before stage-00. Haiku. Parses `$ARGUMENTS` for deployment hints (or asks dispatcher to surface a default per build_type — module = host-provided, contract-spec = none, etc). Writes `$ARTIFACTS_DIR/deployment-target.json` with `{platform, runtime, service_manager, cron}`. Stage-07 prompt reads this file and branches its phase output (e.g., systemd .service vs Dockerfile vs cloud config).
- **Files touched:** pipeline-d.yaml (1 new node), `deployment-target.md` command file, `prd-stage-07.md` (add a "deployment artifact" output line conditional on `deployment-target.json`).
- **Tokens:** ~4K.
- **Depends on:** Fix 6 nice-to-have (seed makes deploy target part of the seed). Otherwise none.
- **What this gets you:** PRD emits the right deploy artifact for the user's actual target. Owner picks platform once, downstream stages obey.

### Fix 9 — Mechanism Boundary Enforcement
- **Problem:** AI can leak `mp3_generator` logic into `alerts.py` because nothing forbids cross-mechanism imports.
- **Fix:** edit `prd-stage-04.md` body to also emit `mechanism-contracts.json` listing per-mechanism `{files, may_import, may_not_import}`. Then add a per-phase `phase-N-boundary-check` prompt node (between `phase-N-compile-check` and `gate-phase-N`) that Read's `mechanism-contracts.json` + `Grep`s every changed file's import lines, fails if any file imports outside its mechanism's `may_import` list. Emits PASS/FAIL.
- **Files touched:** `prd-stage-04.md`, pipeline-d.yaml (3 new nodes), `phase-boundary-check.md` command file.
- **Tokens:** ~4K.
- **Depends on:** Fix 1 (boundaries are clearer when I/O is specified).
- **What this gets you:** modules stay modular. AI can't accidentally couple them.

### Fix 10 — Cross-platform harness — **SATISFIED BY PASS 1**
- Pass 1 already removed all bash + python from pipeline-d. Cross-platform fragility is gone. No work in Pass 2. Note this for the executing agent so they don't try to re-implement it.

### Fix 11 — Post-Stage-10-v2 Quality Gate (Scorecard) — **NEW**
Full spec in §5.

---

## 5. Scorecard fix — full spec

### 5.1 Architecture

```
stage-10-v2 (existing)
    |
    v
[run scorecard]                   --- 3 prompt nodes in parallel, Opus, fresh context
+-- prd-review-correctness          ('@model-prd' from preflight)
+-- prd-review-completeness
+-- prd-review-coherence
    |
    v
prd-triage  (Opus, single call)   --- aggregates the 3, classifies tier
    |
    +-- tier == "clean"   --> proceed to prd-bundle-ready (existing)
    +-- tier == 1         --> prd-fix-tiny (Sonnet, in-place edit) --> prd-bundle-ready
    +-- tier == 2         --> prd-revision-trigger --> re-run from broken_stage forward
    +-- tier == 3         --> prd-revision-trigger --> re-run from root forward
    |
    v
revision counter (in dispatcher's downstream state)
    +-- count <= 2: loop back into the appropriate stage-NN with revision_mode=true
    +-- count == 2 still flagged: prd-revision-escalate (writes handoff, halts build path)
```

### 5.2 Reviewer count + lenses

**3 reviewers**, not 4. (M14 leans 3; build-feasibility folds into correctness.)

| Node | Lens (one sentence) |
|---|---|
| `prd-review-correctness` | Are facts, references, mechanism dependencies, and tech-stack picks logically sound and internally consistent? Includes build feasibility. |
| `prd-review-completeness` | Are all required sections present for the active `$BUILD_TYPE` (per stage-10-v2's per-mode deliverable list)? Any silent gaps? |
| `prd-review-coherence` | Does the PRD tell one story end-to-end? Does drift_anchor hold across stages 04 / 05 / 07 / 10-v2? Any contradictions? |

All 3 run in parallel after `stage-10-v2`. All `model: $model-select.output.model_prd` / effort matched. Fresh context — they do NOT see prior reviewer output.

### 5.3 Score schema (each reviewer emits)

```
output_format:
  type: object
  properties:
    score:        { type: string }                # "0".."100" as string per Archon JSON enum constraints
    findings:     { type: string }                # newline-joined findings list, severity-prefixed: "[CRITICAL]..." / "[HIGH]..." / "[MEDIUM]..." / "[LOW]..."
    blocking:     { type: string, enum: ["true","false"] }   # any CRITICAL/HIGH finding
    announcement: { type: string }                # one-line side-panel summary
  required: [score, findings, blocking, announcement]
```

### 5.4 Triage tier rules

`prd-triage` (Opus, one call) inputs all three reviewer outputs + the PRD bundle path. Computes:

- `aggregate = (correctness.score + completeness.score + coherence.score) / 3`
- `min_lens = min(...)`
- `any_blocking = OR(reviewer.blocking == "true")`

Decision table:

| Condition | Tier | Action |
|---|---|---|
| `aggregate >= 85` AND `min_lens >= 70` AND NOT `any_blocking` | `clean` | Proceed to `prd-bundle-ready` (no revision). |
| `aggregate >= 70` AND only typos/cosmetic findings (no CRITICAL/HIGH) | `1` | Run `prd-fix-tiny` (Sonnet, in-place edit). Does NOT consume revision count. |
| `aggregate >= 60` AND broken stage is locatable (one stage's outputs cited as the root) | `2` | Re-run broken stage + downstream stages with `revision_mode=true`. Consumes 1 revision count. |
| `aggregate < 60` OR root cause is structural (stage-00 / stage-01 / stage-03 wrong) | `3` | Re-run from root stage forward with `revision_mode=true`. Consumes 1 revision count. |
| Any single lens `< 50` | escalate to `tier 2` minimum (regardless of aggregate) — single-lens floor. |

Owner-tunable: thresholds (85 / 70 / 60 / 50) live in `prd-triage`'s prompt as named numbers, easy to edit.

### 5.5 Triage output schema

```
output_format:
  type: object
  properties:
    tier:                { type: string, enum: ["clean", "1", "2", "3"] }
    broken_stage:        { type: string }      # e.g. "stage-04" or "" for clean/tier-1/tier-3
    root_cause:          { type: string }      # one sentence
    findings_summary:    { type: string }      # newline-joined top issues
    affected_stages:     { type: string }      # comma-separated list of stages to re-run
    revision_number:     { type: string }      # "1" first time triage runs, "2" second time, etc.
    confidence:          { type: string }      # "0".."1" as string
    announcement:        { type: string }
  required: [tier, broken_stage, root_cause, findings_summary, affected_stages, revision_number, confidence, announcement]
```

### 5.6 Loop cap + escalation

- **Max 2 revision loops** (tier 2 + tier 3 BOTH count; tier 1 does NOT).
- After 2 revisions, if reviewers still flag CRITICAL/HIGH issues:
  - `prd-revision-escalate` node fires.
  - Writes a handoff at `C:\Users\lober\.autoforge\handoffs\session-prd-revision-stuck-<run_id>.md` with the message in §5.7.
  - Sets `prd_runs_ok = "false"` for downstream `build_runs_ok` calculation (effectively halts build path).
  - PRD bundle is preserved at `$ARTIFACTS_DIR` for owner's manual review.

### 5.7 Owner notify message (verbatim)

```
PRD revision limit reached (2 attempts).
Reviewers still flagging issues after 2 revisions.

Build type:    <build_type>
Run ID:        <run_id>
Bundle:        <ARTIFACTS_DIR>

Root causes across revisions:
  Attempt 1:   <r1_root_cause>
  Attempt 2:   <r2_root_cause>

Top remaining issues:
  <findings_summary from latest triage>

Likely causes:
  - Genuine off-day on agents (try again later)
  - Contradictory or impossible requirements in the intake
  - A real structural problem that needs human judgment

Next steps - pick one:
  1. Approve as-is and force build
  2. Discard and re-run from scratch with adjusted intake
  3. Edit intake (especially stage-01 input) and re-run
```

### 5.8 Per-stage revision preamble (conditional block)

Every one of the 11 stage command files (`prd-stage-{00..05,07..09,10-v2}.md`) gets a single conditional preamble block appended ABOVE the existing CONTEXT PREAMBLE (so it fires before mode branching):

```
## REVISION CONTEXT (only active when revision_mode == "true")

revision_mode = $REVISION_MODE
revision_number = $REVISION_NUMBER
broken_stage = $BROKEN_STAGE
root_cause = $REVISION_ROOT_CAUSE
findings_to_address = $REVISION_FINDINGS
affected_components = $REVISION_AFFECTED

IF $REVISION_MODE == "true":
  This is revision attempt $REVISION_NUMBER for this PRD.
  - You have full permission to change sections related to the root cause.
  - Preserve sections unrelated to the root cause from the prior run.
  - Do not redo work that was already correct.
  - Address the listed findings explicitly. For each, note in your stage output
    which finding you addressed and how.

ELSE:
  Ignore this block. Proceed normally.
```

Pipeline-d wires the env vars on every stage node (Pass 1 already passes `BUILD_TYPE`; add the 5 new vars alongside, sourced from `prd-triage` outputs when revision_mode is true, defaulted to "" / "false" otherwise).

### 5.9 Dependency map for tier 2 cascades

Validated against actual stage files in `archon-pipeline-rebuild/.archon/commands/`. Source of truth: each stage's "Input" section names which prior stages' artifacts it reads.

| Stage | Reads from | Feeds into |
|---|---|---|
| `stage-00` | `$ARGUMENTS` | 02, 03, 04, 07, 10-v2 |
| `stage-01` | context_packet (stage_0) | 02, 03 |
| `stage-02` | stage_0, stage_1 | 03 |
| `stage-03` | stage_1, stage_2 | 04, 10-v2 |
| `stage-04` | stage_2, stage_3 | 05, 07, 10-v2 |
| `stage-05` | stage_4, stage_0 | 07, 08, 10-v2 |
| `stage-07` | stage_4, stage_5, stage_0 | 08, 10-v2 |
| `stage-08` | stage_5, stage_7 | 09, 10-v2 |
| `stage-09` | stage_7, stage_8 | 10-v2 |
| `stage-10-v2` | all prior | (final) |

Tier 2 broken-stage example: triage names `stage-04` as broken → re-run 04, 05, 07, 08, 09, 10-v2. Skip 00, 01, 02, 03.

### 5.10 New nodes summary

| Node | Type | Model | Depends on | When |
|---|---|---|---|---|
| `prd-review-correctness` | prompt | model_prd | stage-10-v2 | `prd_runs_ok == "true"` |
| `prd-review-completeness` | prompt | model_prd | stage-10-v2 | same |
| `prd-review-coherence` | prompt | model_prd | stage-10-v2 | same |
| `prd-triage` | prompt | model_prd | all 3 reviewers | same |
| `prd-fix-tiny` | prompt | sonnet-4.6 (override hardcoded — Sonnet, single edit pass) | prd-triage | `prd-triage.tier == "1"` |
| `prd-revision-trigger` | prompt | haiku | prd-triage | `prd-triage.tier == "2" OR == "3"` AND `revision_number <= 2` |
| `prd-revision-escalate` | prompt | haiku | prd-triage | `prd-triage.tier in ["2","3"]` AND `revision_number > 2` |
| `prd-bundle-ready` (existing) | — | — | new dep on `prd-triage`'s "clean"/"tier-1-resolved" path | unchanged |

`prd-revision-trigger` re-launches the affected stages by writing the 5 revision env vars and emitting `revision_mode = "true"`. Stage nodes re-read their command files; preamble's IF kicks in. **Note:** Archon DAG is not re-entrant. Spec the loop as a pre-declared second copy of stages-NN-rev1 + stages-NN-rev2 (same prompts, gated by revision_number) OR confirm with engine docs whether `loop:` node type can wrap the chain. Mark this as the biggest open question — see §9.

---

## 6. Execution order

Independent fixes can ship in parallel. Dependencies form 4 ship-blocks:

| Block | Fixes | Why this order | Est tokens (cumulative spec→YAML edits) |
|---|---|---|---|
| **A — Cheap, parallel** | 1, 4, 7 | Prompt edits + small node adds. No deps. Land same session. | ~10K |
| **B — Build on A** | 2, 3, 5 | Need Fix 1's I/O detail (Fix 2 verify blocks check it; Fix 3 trace reads it; Fix 5 red team reads Fix 3 trace). | ~11K |
| **C — Heavier** | 6, 9 | Fix 6 touches every stage (cache + ledger). Fix 9 adds boundary contract + 3 gate nodes. Land after A/B settle so re-edits are minimal. | ~10K |
| **D — Last, biggest** | 8, 11 | Fix 8 adds branching to stage-07. Fix 11 (Scorecard) adds 7 new nodes + revision preamble in 11 files + DAG re-entry workaround. Highest risk, ship last. | ~14K |

**Total YAML/prompt edits: ~45K tokens of changes.** At 500K tokens / 30 min, executing agent ships full Pass 2 in ~3 min of pure output time (excluding read overhead). Realistic wall-clock: 8–15 min including reads + tests.

Within a block, fixes are parallel-safe (different files / different nodes). Across blocks, finish A before starting B, etc.

---

## 7. Acceptance checks (owner-readable, per fix)

| Fix | How owner verifies |
|---|---|
| 1 | Run any PRD. Open `phases/phase-1.md`. Every mechanism block has 3 sub-headers: Inputs / Outputs / Failure Modes. Failure Modes table has at least 5 rows covering network/timeout/invalid/down/partial. |
| 2 | Open any phase file. Every build item has a `verify:` block with a one-line check. After build, `verify-deliverables` node's report shows PASS for every item. |
| 3 | After PRD half, file `golden-path-trace.md` exists in `$ARTIFACTS_DIR`. It walks ONE example through every mechanism by name. Has a "Failure Trace" section after the happy path. No `GAP:` markers (or pipeline halted with the gap, which is also a pass). |
| 4 | Build halves run 2 review nodes in parallel after gate-phase-3, then 1 synthesis node. Side-panel shows 2 reviewer announcements + 1 synthesis verdict. |
| 5 | File `red-team-report.md` exists in `$ARTIFACTS_DIR`. 5 ranked failures, each with prevention text. Phase files contain the prevention text (or stage-10-v2 lists them in open questions). |
| 6 | Restart a failed run mid-pipeline. Completed stages print `CACHED` in side-panel and skip. `run-seed.json` and `run-ledger.jsonl` exist in `$ARTIFACTS_DIR`. |
| 7 | Inject a fake hallucination (e.g., builder claims `foo.py` created but it isn't). `phase-N-compile-check` emits FAIL. Pipeline halts before reviewer spend. |
| 8 | File `deployment-target.json` exists in `$ARTIFACTS_DIR` with the right platform. For `linux-systemd` target, phase files emit `.service` artifacts; for `docker-compose`, a Dockerfile. |
| 9 | File `mechanism-contracts.json` exists in `$ARTIFACTS_DIR`. After build, intentionally insert a forbidden import — `phase-N-boundary-check` emits FAIL. |
| 10 | N/A (already shipped in Pass 1). |
| 11 | After stage-10-v2, side-panel shows 3 reviewer announcements + 1 triage announcement. Tier-1 case: `prd-fix-tiny` runs, no stage re-run, build proceeds. Tier-2 case: affected stages re-run with `revision_mode=true` printed in their announcements. After 2 revisions stuck: handoff file appears at `C:\Users\lober\.autoforge\handoffs\session-prd-revision-stuck-<run_id>.md`. |

---

## 8. Out of scope

- **KNOWN-ISSUES #4 (3 build phases hardcoded)** — NOT addressed in Pass 2. Pass 2 keeps 3 phases. Variable phase count requires DAG generation (currently impossible in Archon's static YAML model). Lift this in a Pass 3 or Pass 4 once Pass 2 stabilizes.
- **Adding a 7th build mode** — out of scope (locked at 6). See `ADD-NEW-BUILD-STYLE-HANDOFF.md` for that recipe.
- **Stage-06 re-introduction** — out of scope. Gap is intentional per Pass 0 audit.
- **Engine-feature requests (env: field, `||` in `when:`, workflow imports)** — engine doesn't support them. All Pass 2 fixes use existing patterns: dispatcher booleans, `when: == / !=` only, single-file YAML.
- **Mid-pipeline scorecard** — only post-stage-10-v2 gate is in scope. Per-stage mid-pipeline review is too expensive (3 Opus reviewers × 11 stages = 33 extra calls per run).

---

## 9. Open questions (owner please decide before executing agent starts)

1. **Tier 3 first-attempt behavior — auto-rerun or hard-stop immediately?** Default in this spec: auto-rerun once (consumes revision count 1), then escalate on the 2nd. M14 leans the same way. **Owner confirm or override.**

2. **Single-lens floor (50%) — auto-tier-2 trigger?** Default: yes — any one lens below 50% forces at least tier 2 even if aggregate is good. Could be too aggressive. **Owner confirm or relax to "single-lens 50% only flags, doesn't trigger reroll."**

3. **DAG re-entry for revision loop — pre-declared duplicate stages OR `loop:` node?** Archon DAG is static. Spec proposes either:
   - **(a)** Pre-declare `stage-NN-rev1` and `stage-NN-rev2` for every stage (22 extra nodes total, but all guarded by `when:` so they only fire when needed). Heavier YAML, simple semantics.
   - **(b)** Use Archon's `loop:` node type (mentioned in skill but not used in pipeline-d). Cleaner YAML, untested in this engine version.
   **Owner pick.** Default in this spec: (a), because Pass 1 confirmed engine doesn't support imports/templating; copy-paste is reliable.

4. **Tier 1 fix model — Sonnet or Haiku?** Spec defaults to Sonnet (M14 said Sonnet). Haiku would be 5x cheaper but tier 1 is rare; not worth tuning. **Owner confirm Sonnet is fine.**

5. **`prd-revision-escalate` halt method.** Spec sets `prd_runs_ok = "false"` to keep build half off. But that requires re-piping dispatcher output, which dispatcher already emitted. Cleaner: have escalate write a `prd-revision-escalated.json` file, and `prd-bundle-ready` checks for it before emitting READY. **Owner: OK with this approach?**

---

## 10. What "done" looks like for the executing agent

- Pipeline-d.yaml grows from 24 nodes → roughly 50–55 nodes (3 reviewers + 1 triage + 1 tier-1 fixer + 1 trigger + 1 escalator + 3 verify + 3 compile-check + 3 boundary-check + 1 golden-path + 2 red-team + 1 deploy-target + 1 run-seed + 2 reviewer split + 1 synthesis + ~22 revision-stages duplicates if option 9.3.a is chosen).
- ~6 new command files in `archon-pipeline-rebuild/.archon/commands/`.
- 11 stage prompt files get a revision preamble + cache check + ledger append (small additive edits, body untouched).
- `prd-stage-04.md` body grows for Fix 1 + Fix 9.
- `prd-stage-07.md` and `prd-stage-10-v2.md` bodies grow for Fix 2 + Fix 8.
- One smoke test per fix per build_type covers Pass 2 acceptance.

---

**End of unified spec.** Pass 2 = V3 Roadmap fixes 1–9 (Fix 10 satisfied) + Fix 11 (Scorecard). Execution = 4 ship-blocks. Total agent time at 500K tok / 30 min: ~3 min pure output, 8–15 min wall-clock with reads.

---

## Appendix A — Owner Decisions (locked)

Owner reviewed the 5 open questions. Picks below are final. Executing agent: treat as spec, not options.

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | DAG re-entry for revision loop: (a) duplicate stage nodes gated by `revision_mode==true` vs (b) single `loop:` wrapper | **(a) duplicate nodes** | Engine has no loop primitive (Pass 1 confirmed). Option b needs feature that doesn't exist. Doubles node count for revisable stages — accept the cost. Future engine upgrade can refactor to (b). |
| 2 | Tier 3 first-attempt: auto-rerun once vs hard-stop immediately | **Auto-once.** Hard-stop on attempt 2. | Matches M14 lean. One full cascade re-run is cheaper than burning a Sonnet build cycle on a structurally broken PRD. Two = pattern, not luck. |
| 3 | Single-lens floor: any reviewer below threshold triggers reroll, or only aggregate? | **Two-gate.** Aggregate >= 80% AND no single lens < 65%. Either gate fails -> tier 2 reroll. | Prevents one weak lens (e.g. 50% coherence) from sneaking through on strong aggregate. Both numbers tunable later. |
| 4 | Tier 1 fix model: Sonnet vs Opus vs Haiku | **Sonnet.** | M14 default. Haiku saves 5x but tier 1 is rare — not worth tuning. Opus overkill for typo-class fixes. |
| 5 | `prd-revision-escalate` halt mechanism: real halt node vs prompt-only flag | **Handoff file + dispatcher gate.** Escalate node writes `prd-revision-escalated.json` to bundle dir. `prd-bundle-ready` checks for that file before emitting READY. If present -> READY = false, build path blocks. Also write owner notification to `C:\Users\lober\.autoforge\handoffs\pass-2-escalate-{timestamp}.md`. | Engine has no halt primitive. File-based gate is reliable + readable by owner. Handoff file = how owner finds out. |

**All other open items in spec body that weren't on this list:** executing agent uses spec defaults.

**Acceptance check for these decisions:** when executing agent ships Pass 2, verify each row above is reflected in the YAML/commands. Reviewer (Opus) should fail the run if any decision was ignored.

---

**End of Appendix A.**
