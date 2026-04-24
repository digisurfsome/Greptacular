# Pipeline Rebuild — No-Bash Handoff PRD

> **Audience:** A brand-new agent with zero prior conversation context.
> **Goal:** Rebuild `prd-pipeline-c.yaml` so it runs on Windows without any fragile bash plumbing. Same behavior, fewer failure modes.
> **Order:** Do THIS rebuild first. V3 Roadmap fixes go on top AFTER the rebuild is working.

---

## 1. System Overview — What You Are Walking Into

### What Archon is
Archon (fork of `coleam00/archon`) is a YAML-driven workflow engine that runs AI "nodes" in a DAG. Each workflow lives at `.archon/workflows/<name>.yaml`. Each node is one of four types:
- `command:` — loads an `.md` prompt file from `.archon/commands/`
- `prompt:` — inline AI prompt string
- `bash:` — raw shell script, stdout captured as `$nodeId.output`
- `loop:` — iterates an AI prompt until a completion signal

Full authoring reference is in the **archon skill** at:
- `C:\Users\lober\.claude\skills\archon\SKILL.md`
- `C:\Users\lober\.claude\skills\archon\references\workflow-dag.md`
- `C:\Users\lober\.claude\skills\archon\references\variables.md`
- `C:\Users\lober\.claude\skills\archon\references\dag-advanced.md`

**Read the skill before you start.** It tells you the exact fields, the variable rules, and the supported output formats.

### What the user owns
- Dev repo: `c:\Users\lober\GitHub\Greptacular - AutoForge Build\Greptacular`
- Live install: `C:\Users\lober\Greptacular` (port 8888)
- User is NOT a coder. Write plain English in status updates. No jargon dumps.
- Commits go to `main`. No branches.

### What pipeline-c does today
`.archon/workflows/prd-pipeline-c.yaml` is an 11-stage PRD maker + 3-phase deterministic builder. It produces a full PRD bundle (stages 0–10), then builds the app in 3 phases with compliance gates between each.

It works — until the bash glue trips on Windows.

---

## 2. What Is Wrong — Catalogue of Failures We Actually Hit

Every one of these was a real, session-burning error. The new pipeline must make all of them impossible by design.

| # | Bug | Root cause | Current band-aid |
|---|-----|------------|------------------|
| 1 | `python: command not found` | git-bash on Windows has `python3` not `python` | Rewrote 15 spots from `python` → `python3` |
| 2 | `uv: command not found` | `uv run --with pyyaml` assumes uv on PATH | Replaced with plain `python3 -c` + try/except yaml fallback, then pure `echo` |
| 3 | `git rev-parse HEAD: fatal` | WSL-style `/mnt/c/...` path vs git-bash `/c/...` path | Added `|| echo "HEAD-fallback"` to 3 baseline nodes |
| 4 | Empty bundle dir — `FAIL: source bundle not found at ` | Archon substitutes unknown variables to empty string BEFORE bash runs. `$PRD_BUNDLE_DIR` was never defined, so `[ -d "$PRD_BUNDLE_DIR" ]` became `[ -d "" ]` | Inlined the literal path as a hardcoded string |
| 5 | Cascading compliance gate failures | Upstream node emits empty string → `[ '' = PASS ]` evaluates false → downstream fails | Same as #4 — fix the variable, fix the gate |
| 6 | `baseBranch: master not found` | `.archon/config.yaml` pinned to `master` after rename to `main` | Deleted the config to force auto-detect |
| 7 | Worktree creation failed — no origin | Local-registered project had no GitHub remote | Pushed to GitHub, added `origin` |
| 8 | "Invalid codebase name format" | Registration name with dashes conflicted with regex | Renamed to `audio-recorder-scaled` |

**Pattern:** every one of these bugs is a bash-layer bug, a variable-substitution bug, or a Windows-shell bug. None of them exist if you delete bash from the workflow.

---

## 3. Rebuild Goal

**One sentence:** replace every `bash:` node in `prd-pipeline-c.yaml` with a `prompt:` node or a `command:` node that uses structured output (`output_format:` JSON) to pass data between nodes.

Where bash was doing logic (grep, file reads, path math, PASS/FAIL gates), the AI node does it. Where bash was doing file IO (copy a bundle, write a JSON artifact), the AI node uses its own file tools.

Bash is allowed ONLY for operations bash is uniquely good at AND that cannot fail on Windows git-bash with an empty variable — basically nothing in the current pipeline qualifies.

### Naming
- New file: `.archon/workflows/prd-pipeline-d.yaml` (monolith — full PRD + Build end-to-end)
- After monolith is green, duplicate to:
  - `.archon/workflows/prd-pipeline-d-prd-only.yaml` (PRD half only)
  - `.archon/workflows/prd-pipeline-d-build-only.yaml` (Build half only, imports pre-made bundle)
- Keep `prd-pipeline-c.yaml` in place as a reference — do NOT delete it.
- Once pipeline-d is green against `audio-recorder-scaled`, pipeline-c can be archived.

---

## 3.5. THREE-VARIANT ARCHITECTURE — Monolith First, Split Second

The owner wants three shippable workflows:
1. **Full** — PRD + Build (end-to-end)
2. **PRD-only** — stages 0–10, outputs a bundle
3. **Build-only** — takes a pre-made bundle, runs the 3 build phases

**Rule: design for the split from day one. Do NOT build three separate files.**

### The Seam

The monolith has one boundary node named `prd-bundle-ready`. It sits between stage 10 (last PRD stage) and phase-1 (first build stage). Its job:
- Write a manifest JSON to `$ARTIFACTS_DIR/bundle/manifest.json` listing every artifact produced by the PRD half (paths, sizes, stage IDs).
- Emit JSON output `{ "status": "READY", "bundle_path": "<path>" }`.
- Nothing above it touches build logic. Nothing below it touches PRD logic.

### How the three variants are produced

Once the monolith is green:
- **Full** = `prd-pipeline-d.yaml` (the monolith, unchanged).
- **PRD-only** = copy monolith → delete every node after `prd-bundle-ready`. Done.
- **Build-only** = copy monolith → delete every node before `prd-bundle-ready`, replace `prd-bundle-ready` with `import-bundle` entry node that reads an existing bundle path from `$ARGUMENTS` into `$ARTIFACTS_DIR/bundle/` using AI tools (Read, Write), emits the same `{ status: READY, bundle_path }` JSON.

### Why this over "build separate, connect later"

Merging three divergent workflow files into one is harder than splitting one clean file into three. Forward direction (split) is trivial copy-delete. Backward direction (merge) means reconciling three sets of drift. Always build monolith-first when a clean seam exists.

### Maintenance rule

Bug fixes go into the monolith. The two variants are regenerated from the monolith. Never edit a variant directly — if you do, document the divergence in the variant's header comment so the next rebuild doesn't wipe it.

---

## 3.75. STEP 0 — MODEL / EFFORT OVERRIDE PREFLIGHT NODE

Every variant (monolith, PRD-only, Build-only) starts with the SAME preflight node. It decides which Opus version and effort level runs for the rest of the workflow.

### Supported model/effort combos (exact wording the user uses)

| User name (message tag) | Archon `model:` | Archon `effort:` |
|-------------------------|-----------------|-------------------|
| `opus-4.6-medium` (**default**) | `claude-opus-4-6` | `medium` |
| `opus-4.6-high` | `claude-opus-4-6` | `high` |
| `opus-4.6-extrahigh` | `claude-opus-4-6` | `max` |
| `opus-4.7-medium` | `claude-opus-4-7` | `medium` |
| `opus-4.7-high` | `claude-opus-4-7` | `high` |
| `opus-4.7-extrahigh` | `claude-opus-4-7` | `max` |

`extrahigh` maps to Archon's internal `effort: max` value (confirmed in `packages/workflows/src/dag-executor.test.ts:5100`).

### How the user passes the override

The user includes a tag at the start of the build message. Examples:
```
@model opus-4.7-high Build audio-recorder-scaled
@model opus-4.6-extrahigh Build the MP3 generator
Build audio-recorder-scaled          ← no tag = use default (opus-4.6-medium)
```

### Preflight node spec

```yaml
- id: model-select
  prompt: |
    The user's build message is: $ARGUMENTS

    Parse the beginning of the message for a tag of the form `@model <name>` where <name>
    is one of: opus-4.6-medium, opus-4.6-high, opus-4.6-extrahigh,
               opus-4.7-medium, opus-4.7-high, opus-4.7-extrahigh.

    If no tag is present, use the default: opus-4.6-medium.

    Map the name to Archon values using this table:
      opus-4.6-medium    → model=claude-opus-4-6, effort=medium
      opus-4.6-high      → model=claude-opus-4-6, effort=high
      opus-4.6-extrahigh → model=claude-opus-4-6, effort=max
      opus-4.7-medium    → model=claude-opus-4-7, effort=medium
      opus-4.7-high      → model=claude-opus-4-7, effort=high
      opus-4.7-extrahigh → model=claude-opus-4-7, effort=max

    Respond with JSON ONLY. Also include a one-line human-readable announcement
    as the `announcement` field — this is the FIRST thing the user sees on the
    workflow status side-panel and confirms the choice.
  model: haiku
  output_format:
    type: json
    schema:
      user_name:     { type: string }   # e.g. "opus-4.6-medium"
      model:         { type: string }   # e.g. "claude-opus-4-6"
      effort:        { type: string, enum: [low, medium, high, max] }
      source:        { type: string, enum: [default, message-override] }
      announcement:  { type: string }   # e.g. "Using opus-4.6-medium (default — no @model tag in message)"
  allowed_tools: []
```

### How downstream Opus-assigned nodes consume the override

Every node that was previously using `opus` (or implicitly opus because of workflow default) must reference the preflight output:

```yaml
- id: phase-1-build
  command: build-phase-1
  depends_on: [model-select, prd-bundle-ready]
  model:  '$model-select.output.model'
  effort: '$model-select.output.effort'
```

Nodes that must stay on cheap models (Haiku preflights, gate checks) keep their hardcoded `model: haiku` — do NOT wire them to the preflight output. The override only applies to "heavy lifting" nodes.

### Status visibility — FIRST LINE IN THE SIDE PANEL

The preflight node runs first. Its `announcement` field is what the Archon UI renders on the status side-panel as the first human-readable line. Because of this:
- Non-override run shows: `Using opus-4.6-medium (default — no @model tag in message)`
- Override run shows: `Using opus-4.7-high (override from message tag)`

The user knows at a glance which brain is doing the work before any real money is spent. If the side-panel shows the wrong model, the user cancels the run immediately — no waste.

### Acceptance tests

The rebuild is not done until the preflight node can:
1. Correctly default to opus-4.6-medium on a message with no tag.
2. Correctly map `@model opus-4.7-high Build X` to model=claude-opus-4-7, effort=high.
3. Emit a clear `announcement` string that appears FIRST in the side-panel.
4. Survive a malformed tag (e.g., `@model opus-9.9-ludicrous`) by falling back to default AND surfacing a warning in the announcement.

### Why this is worth the one extra node

- Pinning to 4.6 by default makes weekly Opus limit 3-5x less likely to trip.
- Override from message means zero YAML edits day-to-day.
- Announcement in side-panel = instant confirmation the run is using what you expected.
- Adding a new model later (opus-4.8, sonnet-5, etc.) = one line in the mapping table. No code changes.

---

## 4. Plan of Action — Step by Step

### Step 1 — Read the skill
Read in this order:
1. `C:\Users\lober\.claude\skills\archon\SKILL.md`
2. `C:\Users\lober\.claude\skills\archon\references\workflow-dag.md`
3. `C:\Users\lober\.claude\skills\archon\references\variables.md`
4. `C:\Users\lober\.claude\skills\archon\references\dag-advanced.md` (pay attention to `output_format` and `allowed_tools`)

### Step 2 — Map pipeline-c
Open `.archon/workflows/prd-pipeline-c.yaml`. For every node, write one row:
- `id`
- Current type (`bash` / `prompt` / `command` / `loop`)
- What the node actually DOES in one sentence (not how)
- Inputs it consumes (upstream node outputs, $ARGUMENTS, files)
- Outputs it produces (string, JSON, file path)

This map is your contract. Save it as `docs/page-prds/archon-build-upgrade/PIPELINE-D-NODE-MAP.md` before touching YAML.

### Step 3 — Classify each bash node into one of three rewrites

**A. Gate / compliance check** (e.g., "did phase 1 pass?")
→ Rewrite as a `prompt:` node with `output_format: json` and a fixed schema like `{ "status": "PASS" | "FAIL", "reason": string }`. Downstream nodes use `$nodeId.output.status == "PASS"` in a `when:` condition. No more `[ '' = PASS ]`.

**B. File IO** (e.g., "copy bundle into artifacts dir", "write phase output to file")
→ Rewrite as a `prompt:` node with `allowed_tools: [Read, Write, Edit]`. Prompt tells the AI exactly which file to read/copy/write. AI uses its own tools — no bash, no path mangling.

**C. Environment poke** (e.g., `git rev-parse HEAD`, `date`, `pwd`)
→ Either drop it (the pipeline doesn't actually need a git SHA baseline to work) OR move it into the artifact directory as a JSON file written by a `prompt:` node that asks the AI to capture the value via its own tools.

### Step 4 — Rewrite nodes one at a time
Do NOT do a big-bang rewrite. For each node:
1. Copy the node from pipeline-c into pipeline-d.
2. Convert per Step 3 rules.
3. If the node is an "Opus heavy-lifting" node (build phase, review, fix, compliance-writing), wire its `model:` and `effort:` to `$model-select.output.model` and `$model-select.output.effort` per Section 3.75.
4. Run pipeline-d against `audio-recorder-scaled` with `--resume` support.
5. Fix, commit, move to the next.

The VERY FIRST node you write into pipeline-d is the `model-select` preflight from Section 3.75. Nothing else runs until it lands, because every downstream Opus node depends on its output.

Add a `prd-bundle-ready` seam node between stage 10 and phase-1 per Section 3.5 — this is the split point for the two variants.

Commit after every node with message `pipeline-d: convert <node-id> to prompt/command`.

### Step 5 — Split the monolith into three variants (AFTER monolith is green)
See Section 3.5. Duplicate pipeline-d.yaml into:
- `prd-pipeline-d-prd-only.yaml` — delete everything after the `prd-bundle-ready` seam node.
- `prd-pipeline-d-build-only.yaml` — delete everything before `prd-bundle-ready`; replace it with an `import-bundle` entry node that reads an existing bundle path from `$ARGUMENTS` using AI file tools (Read, Write, Glob).

Both variants MUST keep the Step 0 model-select preflight node. Announcement still appears first in the side-panel.

The existing `prd-pipeline-BUILD.yaml` is the old build-only workflow (the bash-fragile one). It can be deleted once `prd-pipeline-d-build-only.yaml` passes the same test against `audio-recorder-scaled`.

### Step 6 — Preserve the preamble mechanism
`MASTER-MODULAR-ARCHITECTURE.md` defines a `build_mode` flag and a unified preamble block. The rebuild must keep this — do not flatten modular build modes into a single path.

### Step 7 — Test against audio-recorder-scaled
Target project lives at:
`C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\`

Existing bundle path (use as fixture):
`C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\artifacts\runs\0087c45cd7da9fc15fad9193f3277946`

Run command:
```
archon workflow run prd-pipeline-d --branch feat/mp3-gen-d "Build audio-recorder-scaled" 
```
Always `run_in_background: true`. Watch `/tasks` or TaskOutput.

### Step 8 — Success criteria
- Pipeline-d monolith completes all 11 PRD stages on a fresh run.
- Pipeline-d monolith completes all 3 build phases with compliance gates producing real PASS/FAIL from AI JSON output, not bash string equality.
- Zero `bash:` nodes remain (or, if any remain, they are one-line commands that cannot fail on an empty variable).
- Same artifacts are produced as pipeline-c — PRD bundle, phase outputs, compliance reports.
- Step 0 preflight node's `announcement` is the FIRST human-readable line visible in the Archon side-panel every run.
- Default run (no `@model` tag) uses `opus-4.6-medium`. Override run with `@model opus-4.7-high` uses `claude-opus-4-7` with `effort: high`.
- `prd-pipeline-d-prd-only.yaml` runs stages 0–10 only and exits cleanly at the `prd-bundle-ready` seam with a valid manifest.
- `prd-pipeline-d-build-only.yaml` reads a bundle path from `$ARGUMENTS`, imports it, and runs all 3 build phases.

---

## 5. Files — What to Preserve vs Rewrite

### Preserve (read-only — do not edit)
- `.archon/workflows/prd-pipeline-c.yaml` (reference)
- `.archon/workflows/prd-pipeline-b.yaml` (historical reference)
- Every `.archon/commands/*.md` — these are mostly safe, they are AI prompts
- `C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\artifacts\runs\0087c45cd7da9fc15fad9193f3277946` (test fixture)

### Rewrite (new files)
- `.archon/workflows/prd-pipeline-d.yaml` (monolith — full PRD + Build)
- `.archon/workflows/prd-pipeline-d-prd-only.yaml` (PRD half, after monolith works)
- `.archon/workflows/prd-pipeline-d-build-only.yaml` (Build half, after monolith works)
- `docs/page-prds/archon-build-upgrade/PIPELINE-D-NODE-MAP.md` (your working map from Step 2)

### Possibly edit
- `.archon/commands/*.md` — if a command file assumes bash-style variable substitution, fix only that file.

### Do not touch
- `.archon/config.yaml` — if missing, leave missing. Archon auto-detects base branch.
- Global user archon config at `C:\Users\lober\.archon\` — user pulls from project `.archon/` first.

---

## 6. Key Architectural Decisions Already Locked In

Do not re-litigate these. They are final.

1. **Separate repo per module.** The user is building 5 modules (Scraper, Detection Bot, MP3 Gen, Landing Pages, Outreach). Each gets its own GitHub repo via the `digisurfsome/archon-module-template` template. No monorepo.
2. **Commit to `main` directly.** No feature branches in the user's repos. Worktree branches created by Archon are fine.
3. **Sonnet builds, Opus reviews.** Do not assign Opus as a per-phase Reviewer in the new pipeline.
4. **45-minute PRD phase is acceptable** for now. The user has a build-only workflow (`prd-pipeline-BUILD.yaml`) that skips it.
5. **Unified preamble + build_mode flag** from `MASTER-MODULAR-ARCHITECTURE.md` is the canonical modular model. Supersedes M13/M14/M15 PRDs.

---

## 7. Skill Reference Cheat Sheet

From `C:\Users\lober\.claude\skills\archon\SKILL.md`:

**Node structure:**
```yaml
- id: gate-phase-1
  prompt: "Check the phase 1 output: $phase-1.output. Respond with JSON."
  model: haiku
  output_format:
    type: json
    schema:
      status: { enum: [PASS, FAIL] }
      reason: { type: string }
  depends_on: [phase-1]
```

**Conditional edge (replaces bash `[ = PASS ]`):**
```yaml
- id: phase-2
  command: build-phase-2
  depends_on: [gate-phase-1]
  when: '$gate-phase-1.output.status == "PASS"'
```

**File IO without bash:**
```yaml
- id: import-bundle
  prompt: |
    Copy every file from $SOURCE_BUNDLE_DIR into $ARTIFACTS_DIR/bundle/.
    Use your Read, Write, Edit tools. Do not use shell commands.
  allowed_tools: [Read, Write, Edit, Glob]
```

**Key variables:**
- `$ARGUMENTS` — user's message
- `$ARTIFACTS_DIR` — pre-created per-run artifact dir
- `$WORKFLOW_ID` — run id
- `$nodeId.output` — upstream output (string OR JSON depending on `output_format`)

**Unknown variables substitute to empty string BEFORE the node runs.** This is the #1 bug source. If you type `$PRD_BUNDLE_DIR` and it was never defined anywhere, you get empty string. Always verify every `$VAR` is either a documented Archon variable or a defined upstream `$nodeId.output`.

---

## 8. What to Report Back When Done

After the rebuild is green:
- One-line summary of what changed (e.g., "converted 14 bash nodes to prompt nodes with JSON output_format")
- Path to the new workflow file
- Commit hash and branch
- Path to the node map you wrote in Step 2
- List of any bash nodes you could not eliminate and why

---

## 9. After the Rebuild — V3 Roadmap Layer

Once pipeline-d runs green on audio-recorder-scaled, apply the V3 Roadmap fixes from:
`docs/page-prds/archon-build-upgrade/PRD-MAKER-V3-ROADMAP.md`

That doc has 10 concrete fixes (compile-check, verify-deliverables, 2-reviewer, golden-path + red-team, reproducibility, deployment router) that take the PRD maker from 7.5/10 to 9.5/10. Those are additive — they sit on top of pipeline-d. Do not start them until the rebuild is confirmed working.

---

## 10. Do Not

- Do not rewrite pipeline-c in place. Always create pipeline-d as a new file.
- Do not use `bash:` for anything that reads an environment variable defined upstream. Use prompt + JSON output instead.
- Do not sugarcoat status to the user. If a node is stuck, say it's stuck and why.
- Do not guess at filenames or paths — use Glob / Read to verify.
- Do not skip the node map in Step 2. The map IS the design.
- Do not delete pipeline-c until the user says so.
