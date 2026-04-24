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
- New file: `.archon/workflows/prd-pipeline-d.yaml`
- Keep `prd-pipeline-c.yaml` in place as a reference — do NOT delete it.
- Once pipeline-d is green against `audio-recorder-scaled`, pipeline-c can be archived.

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
3. Run pipeline-d against `audio-recorder-scaled` with `--resume` support.
4. Fix, commit, move to the next.

Commit after every node with message `pipeline-d: convert <node-id> to prompt/command`.

### Step 5 — Remove build-only assumptions
The user also has `prd-pipeline-BUILD.yaml` that starts from an existing bundle. When pipeline-d is working, duplicate it into `prd-pipeline-BUILD-d.yaml` and strip stages 0–10 the same way.

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
- Pipeline-d completes all 11 PRD stages on a fresh run
- Pipeline-d completes all 3 build phases with compliance gates producing real PASS/FAIL from AI JSON output, not bash string equality
- Zero `bash:` nodes remain (or, if any remain, they are one-line commands that cannot fail on an empty variable)
- Same artifacts are produced as pipeline-c — PRD bundle, phase outputs, compliance reports

---

## 5. Files — What to Preserve vs Rewrite

### Preserve (read-only — do not edit)
- `.archon/workflows/prd-pipeline-c.yaml` (reference)
- `.archon/workflows/prd-pipeline-b.yaml` (historical reference)
- Every `.archon/commands/*.md` — these are mostly safe, they are AI prompts
- `C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\artifacts\runs\0087c45cd7da9fc15fad9193f3277946` (test fixture)

### Rewrite (new files)
- `.archon/workflows/prd-pipeline-d.yaml` (the rebuild)
- `.archon/workflows/prd-pipeline-BUILD-d.yaml` (after pipeline-d works)
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
