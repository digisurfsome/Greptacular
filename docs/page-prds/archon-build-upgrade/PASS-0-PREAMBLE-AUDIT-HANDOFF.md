# Pass 0 — Preamble Audit & Authoring Handoff PRD

> **Audience:** A brand-new agent with zero prior conversation context.
> **Goal:** Make every stage node prompt in the PRD pipeline **build-mode-agnostic**, and author per-stage preamble blocks that inject mode-specific context for all 6 build modes.
> **This is Pass 0 of a 4-pass sequence. Runs BEFORE Pass 1 (the no-bash rebuild).**
> **Recommended model: Opus 4.7 high** (analysis + rewriting heavy work).

---

## 1. Pass Sequence — Where This Fits

| Pass | Name | Status |
|------|------|--------|
| **Pass 0 (THIS DOC)** | Preamble audit + authoring. Output: mode-agnostic stage prompts + per-stage preamble blocks for all 6 modes. | Active |
| Pass 1 | No-bash rebuild + three preflight switches. Consumes Pass 0 output. | Blocked by Pass 0 |
| Pass 2 | V3 paint-by-numbers layer. | Blocked by Pass 1 |
| Pass 3 | Module contract enforcement. | Blocked by Pass 2 |

**Pass 0 is independent of everything else.** It touches only `.archon/commands/*.md` files (the stage node prompts). It does not touch any workflow YAML. You can start immediately.

---

## 2. System Overview — What You Are Walking Into

### What Archon is
Archon is a YAML-driven AI workflow engine. Workflows live at `.archon/workflows/*.yaml`. Each workflow node of type `command:` loads a prompt file from `.archon/commands/*.md` and sends it to an AI model. Those prompt files ARE what you'll be auditing and rewriting.

### The pipeline you're fixing
`.archon/workflows/prd-pipeline-c.yaml` is an 11-stage PRD maker (stages 00–10) followed by 3 build phases. Each stage has a corresponding command file at `.archon/commands/stage-NN.md` (or similarly named). These command files were authored under the assumption that every build is a **standalone-app** (a whole self-contained product). They likely leak that assumption into their prompts.

### The 6 build modes (from MASTER-MODULAR-ARCHITECTURE.md §2)

| Mode | What's being built |
|------|---------------------|
| `standalone-app` | Small self-contained app. Default assumption. |
| `module` | One mechanism, headless, API/CLI only, part of a larger system |
| `module-host` | Empty dashboard shell that modules bolt into |
| `assembly` | Wire pre-existing modules into a pre-existing host |
| `feature-add` | Add a feature to an existing app |
| `contract-spec` | Produce shared DB schema + module interface contracts (no code) |

**Different modes want different things from each stage.** Example: Stage 6 "design mechanisms" for `standalone-app` includes UI, DB, auth, routing. For `module`, it's just the mechanism's internals — the host owns UI/DB/auth. If the current stage-06 prompt says "design the database schema for this app," it's leaking standalone-app bias. That's exactly what this pass fixes.

### The preamble mechanism (from MASTER-MODULAR-ARCHITECTURE.md §3)
Every stage command file gets a **preamble block at the top** with IF branches for all 6 build modes. The stage's abstract instructions follow underneath. Template lives in MASTER-MODULAR §3 — read it before starting.

### Skill references
- **archon-dev skill** at `C:\Users\lober\.claude\skills\archon-dev\` — use the `research` and `plan` cookbooks for investigation and planning phases of your work.
- **archon skill** at `C:\Users\lober\.claude\skills\archon\` — reference `references/authoring-commands.md` for the command file format and variable syntax.

---

## 3. What's Wrong — The Audit Premise

**Hypothesis (unverified):** every one of the 11 stage command files has at least one line that assumes `standalone-app`. Prove it or disprove it per stage.

Examples of what "mode-leaking" looks like:
- Stage 6 prompt: "design the database schema" → leaks. For `module` mode, the schema comes from contract-spec, not from this stage.
- Stage 3 prompt: "define the dashboard UI" → leaks. For `module` and `module-host`, UI is either absent or deferred.
- Stage 7 prompt: "design deployment strategy" → leaks. For `contract-spec` mode, there's no code to deploy.

The fix: strip those assumptions from the core stage prompt, move them into the `standalone-app` IF branch of the preamble. The core prompt stays agnostic — the preamble injects the mode-specific context.

---

## 4. Your Deliverables

When Pass 0 is done, the following must exist and be committed:

### 4.1 Rewritten stage command files
- `.archon/commands/stage-00.md` through `.archon/commands/stage-10.md` (11 files total).
- Each file starts with a preamble block that branches on `$BUILD_TYPE` (the variable the pipeline passes in).
- The body below the preamble is the abstract stage instructions — mode-agnostic.

**If the original stage files live under different names**, preserve the names. Map the old names to stages 00–10 in your audit report.

### 4.2 Preamble blocks (embedded in the above OR separate files)
Two acceptable layouts — pick one and stay consistent:

**Layout A (embedded):** Each `stage-NN.md` has the preamble block inlined at the top. Simpler. Recommended.

**Layout B (separate):** Create `.archon/commands/preambles/stage-NN-preamble.md` files and reference them via include/import syntax. Only use this if Archon's command file format supports includes (check via the archon skill). If not, use Layout A.

Each preamble has IF branches for all 6 modes per MASTER-MODULAR §3:
```
IF build_mode == "standalone-app":
  [context block — what this stage does for a full standalone app]

IF build_mode == "module":
  [context block — what this stage does for an isolated module]

IF build_mode == "module-host":
  [context block]

IF build_mode == "assembly":
  [context block]

IF build_mode == "feature-add":
  [context block]

IF build_mode == "contract-spec":
  [context block]
```

Some modes may legitimately say "this stage is not applicable — emit an empty deliverable and explain why." That's acceptable. Example: `contract-spec` mode likely skips Stage 8 (deployment) because there's no code to deploy yet.

### 4.3 Audit report
A markdown file at `docs/page-prds/archon-build-upgrade/PASS-0-AUDIT-REPORT.md` documenting:

For each of the 11 stages:
- **Mode-leak findings.** What assumptions did the original prompt make? Quote the offending lines.
- **Where each leak moved.** Which IF branch of the preamble now carries that logic.
- **Core prompt delta.** Short summary of what changed in the abstract stage body.
- **Mode applicability.** Which of the 6 modes apply to this stage, which skip.

Plus a summary section:
- Total lines of leak found → total lines moved to preambles.
- Any stages where you disagree with MASTER-MODULAR's mode definitions (and why).
- Any new build mode you noticed might be needed (for the `ADD-NEW-BUILD-STYLE-HANDOFF.md` author to pick up).

---

## 5. Step-by-Step Plan

### Step 1 — Read the references
1. `MASTER-MODULAR-ARCHITECTURE.md` §2 (6 build modes), §3 (preamble template), §4 (module contract), §5 (per-build custom contracts).
2. `PIPELINE-REBUILD-NO-BASH-HANDOFF.md` §3.75.C (how `build-type-select` wires in Pass 1 — so you know your preambles will be consumed).
3. archon-dev skill `cookbooks/research.md` and `cookbooks/plan.md`.
4. archon skill `references/authoring-commands.md` and `references/variables.md`.

### Step 2 — Inventory the existing stage files
Glob `.archon/commands/*.md`. List every file. Map each to a stage number (00–10) or note if it's orphaned/unused. If the mapping isn't obvious, read `prd-pipeline-c.yaml` to see which commands are referenced by which stage nodes.

### Step 3 — Audit each stage one at a time
Work stage-00 through stage-10 in order. For each stage:

1. **Read the current prompt.** Note the structural sections.
2. **Run the "mode test":** for each of the 6 build modes, ask: "If we ran this stage in `X` mode without any preamble, would it produce the right thing?" If not, note which lines break.
3. **Categorize the leaks:**
   - *Universal assumption* (e.g., "this is a full app") → move to `standalone-app` IF branch.
   - *Partial assumption* (e.g., "you have a UI") → move to modes that have UIs (`standalone-app`, `module-host`).
   - *Non-leak* (truly abstract) → keep in core prompt.
4. **Draft the preamble block.** 6 IF branches. Use MASTER-MODULAR §3 as the exact template shape. Make each branch self-contained — a reader should understand the stage's job in that mode just from reading its branch.
5. **Rewrite the core prompt.** Strip the leaks. Leave the abstract task description.

Commit after each stage with message `pass-0: stage-NN — audit + preamble + rewrite`.

### Step 4 — Cross-stage consistency check
Once all 11 stages are done:
- For each of the 6 modes, read every stage's preamble branch for that mode. Does the mode make sense across the whole pipeline? Does a module-mode run actually produce a sensible 11-stage output?
- Flag any mode where the pipeline doesn't coherently apply. Some modes may be "this stage is skipped" — document that explicitly.

### Step 5 — Write the audit report
Per §4.3 above. Full detail per stage.

### Step 6 — Validate against the existing bundle
Use the reference bundle at `C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\artifacts\runs\0087c45cd7da9fc15fad9193f3277946` — this is an existing PRD output (standalone-app mode). Your rewritten stage prompts + `standalone-app` preamble branches should, in theory, still produce this same output. Cross-check spot-sample 2-3 stages to make sure you didn't strip something essential.

### Step 7 — Commit and hand off
Commit everything. Push to `main`. The Pass 1 agent reads your output and starts the rebuild.

---

## 6. Success Criteria

- All 11 stage command files exist, each with a preamble block having IF branches for all 6 modes.
- Every core prompt body is mode-agnostic — a reader can't tell which of the 6 modes the pipeline is running just from the body.
- The audit report lists every moved assumption with before/after line references.
- A spot-check run of stages 0–3 in `standalone-app` mode (just the prompts, no YAML changes) produces output comparable to the reference bundle.
- Zero workflow YAML files were modified during Pass 0. You only touch `.archon/commands/`.

---

## 7. What NOT to Do

- Do not touch `.archon/workflows/*.yaml`. Pass 1 owns that.
- Do not add new switches or preflight nodes. Pass 1 owns those.
- Do not rewrite MASTER-MODULAR-ARCHITECTURE.md. Its design is canonical — you consume it.
- Do not skip modes that feel redundant. If `module-host` mode seems identical to `standalone-app` for a given stage, write it out anyway — users rely on all 6 being available.
- Do not invent a 7th build mode. If you think one is needed, note it in your audit report for `ADD-NEW-BUILD-STYLE-HANDOFF.md` to pick up.
- Do not drive-by fix unrelated bugs in stage prompts. Audit + mode-agnostic rewrite only.

---

## 8. What to Report Back When Done

- Path to audit report: `docs/page-prds/archon-build-upgrade/PASS-0-AUDIT-REPORT.md`
- Paths to rewritten stage files: list all 11.
- Commit hash and branch.
- One-line summary per stage: "stage-06: stripped 4 standalone-app assumptions, added 6 mode branches."
- Any surprises that might change Pass 1's scope (e.g., "stage-08 cannot be made mode-agnostic because X").
