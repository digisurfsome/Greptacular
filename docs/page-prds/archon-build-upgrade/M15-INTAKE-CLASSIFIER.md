# M15 — Intake Classifier + Iteration/Pipeline Split

**Status:** Deferred spec. Implement after first clean greenfield build + M13 (existing-app modes) + M14 (PRD self-check) are in.

**Goal:** Separate the iterative PRD-authoring phase from the fire-and-forget build pipeline. Add an entry gate that classifies input richness and routes to the right phase.

---

## Core insight

The current `prd-pipeline-c.yaml` assumes all intakes are barebones (one sentence / one paragraph) and runs all 10 PRD-making stages. In practice, owners arrive with **very different amounts of context:**

| Class | Example input | Pipeline behavior today | Problem |
|---|---|---|---|
| `barebones` | "build me an MP3 generator tool" | Runs stages 00-10 normally | ✅ Works as designed |
| `descriptive` | 18-section functional spec with no agent-OS context (who/why/what for) | Runs stages 00-10 anyway | ❌ Wastes tokens; produces weak context-free output |
| `agent-os-complete` | Descriptive + personas + market fit + system context | Runs stages 00-10 anyway | ❌ Parrots back what was already there |
| `fully-built-prd` | Already a pipeline-output-grade PRD ready to build | Runs stages 00-10 anyway | ❌ Huge waste; should skip to builder |

---

## Two-phase architecture

### Phase 1 — Iteration (interactive, owner-in-the-loop)

- Opus agent.
- Back-and-forth with owner.
- Agent asks questions about context: why exists, who uses it, what it's part of, end-target persona, business case, fit in larger system.
- Ends when PRD is agent-os-complete.
- Not a pipeline — a conversational tool.

### Phase 2 — Pipeline (fire-and-forget, no owner interaction)

- Current `prd-pipeline-c.yaml`.
- Takes agent-os-complete PRDs as input.
- Runs stages 04-10 + builder.
- No questions asked of owner. Halts and escalates only on error (per M14 loop cap).

### The bridge between them — Intake Classifier

A new pre-stage node that classifies the intake and routes accordingly.

---

## The classifier node

**ID:** `stage-neg-1-intake-classifier` (or rename stages to make room: s00 → s01 etc.)

**Model:** Opus. One call. Cheap per run.

**Input:** raw intake text (any size, any shape).

**Output (structured JSON):**
```json
{
  "class": "barebones" | "descriptive" | "agent-os-complete" | "fully-built-prd",
  "missing_context": [
    "why this exists",
    "who operates it",
    "end-target persona",
    "system it fits into"
  ],
  "route": "iteration-phase" | "pipeline-stage-00" | "pipeline-stage-04" | "pipeline-builder",
  "questions_for_owner": [
    "Is this a standalone app or part of a larger system?",
    "Who operates this — you internally, or external users?",
    "...etc"
  ]
}
```

**Routing table:**

| Class | Route |
|---|---|
| `barebones` | Iteration phase OR pipeline-stage-00 (owner choice) |
| `descriptive` | **Halt. Post questions. Wait for answers. Re-classify.** |
| `agent-os-complete` | Pipeline starting at stage 04 (skip redundant early stages) |
| `fully-built-prd` | Pipeline starting at `build-codebase-intelligence` (skip all PRD-making) |

---

## Owner notification for `descriptive` class

When classifier returns `descriptive`, the workflow halts and posts:

```
Your intake was classified as DESCRIPTIVE — rich functional spec but missing 
agent-OS context needed for a quality PRD.

Specifically missing:
  - $missing_context[0]
  - $missing_context[1]
  - ...

Before the pipeline can produce a quality PRD, please answer:
  1. $question_1
  2. $question_2
  3. ...

Paste your answers as a follow-up message. Pipeline will resume with your 
answers merged into the intake.
```

This is the **only** place in the pipeline that allows owner-in-the-loop after the pipeline is fired. Everything else remains fire-and-forget.

---

## Skip-ahead entry points

Classifier routes to different entry points in the workflow. Each route requires a labeled entry node:

```yaml
- id: pipeline-stage-00-entry
  # ... starts at stage 00
- id: pipeline-stage-04-entry
  # ... starts at stage 04, feeds classifier's parsed intake as if stages 00-03 already ran
- id: pipeline-builder-entry
  # ... starts at build-codebase-intelligence, feeds intake as pre-baked PRD
```

The classifier's `route` field determines which entry node fires.

**Implementation note:** this requires Archon to support conditional-entry workflows. Verify with archon skill source before speccing further.

---

## Why this matters for the CallPitch/multi-tool realization

The owner has realized that his 5 separate tool PRDs (Scraper, Detection Bot, MP3 Gen, Landing, Outreach) are actually **one multi-module app**. That means:

- Future intakes will often be "add Module N to this existing app."
- Those intakes are `descriptive` at best (owner knows the module, doesn't re-state the whole app context each time).
- Without M15, each Module PRD gets processed as if it were a standalone app. Wrong.

M15 + M13 together handle this: classifier detects the intake is for an existing app, routes to existing-app mode, runs a reduced set of stages focused on the new module.

---

## Do NOT start this until

- [ ] Pipeline runs successfully on at least one end-to-end greenfield build
- [ ] M13 (existing-app mode) is implemented
- [ ] M14 (PRD self-check) is implemented
- [ ] Owner confirms the iteration-vs-pipeline split is the right mental model (vs. one unified flow)

---

## Open questions

- Does the Iteration Phase live inside archon as a separate workflow, or outside as a Claude Code skill / standalone agent?
- For `fully-built-prd` class, how confident does the classifier need to be before skipping all PRD stages? (Probably > 0.9 confidence + automatic safety check.)
- Should the owner be able to **force** a route (e.g., "I know this is descriptive but run it as agent-os-complete anyway")? Probably yes, via flag.
- Does the classifier itself need review (could misclassify)? Probably worth a second Opus call on disagreement, but adds latency.
