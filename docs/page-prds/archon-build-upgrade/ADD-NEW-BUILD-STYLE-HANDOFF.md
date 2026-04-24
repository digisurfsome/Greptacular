# Add-A-New-Build-Style Handoff PRD

> **Audience:** A brand-new agent asked to add a 7th (or Nth) build mode to an already-working pipeline-d.
> **Goal:** Add one new build mode to the pipeline WITHOUT modifying any stage prompt body or any workflow structure. Single-file architecture means this is a preamble-authoring task, not a rewrite.
> **Prerequisite:** Pass 0, Pass 1, Pass 2 must already be complete. Pipeline-d runs cleanly. All 11 stage command files are mode-agnostic with per-mode preamble branches.
> **Recommended model: Opus 4.7 high** (analytical, consistency-sensitive).

---

## 1. Why This Handoff Exists

The pipeline-d architecture was deliberately designed so that **adding a new build mode requires zero YAML edits and zero core prompt edits.** You only author new preamble branches.

This is the compounding-asset property:
- 1st build mode: expensive to define (6 modes authored across 11 stages = 66 preamble branches).
- 2nd build mode onwards: cheap (add 11 branches, one per stage).
- Nth build mode: same cost as 2nd. Doesn't get harder.

If you find yourself wanting to change the core prompt of a stage, or add a new node to the workflow YAML, **stop**. That means either the stage body isn't actually mode-agnostic (Pass 0 bug — report it) OR this new mode is so different it needs its own pipeline (which is itself a different and larger task).

---

## 2. Inputs You Need From the User

Before you start, get these in writing:

| Input | Description | Example |
|-------|-------------|---------|
| **Mode name** | Short machine-safe slug. Lowercase, hyphens. | `saas-with-stripe` |
| **Mode description** | One paragraph. What's being built. What distinguishes it from existing modes. | "A standalone-app variant that includes Stripe billing, multi-tenant auth, and a customer portal from day one. Differs from standalone-app by assuming paid product from the start." |
| **Boilerplate needed?** | yes/no | yes — Next.js + Supabase + Stripe |
| **UI needed?** | yes/no/minimal | yes |
| **Intended use** | When would the user pick this mode? | "Any time I'm building something I plan to charge for. Replaces the 'add billing later' pain." |
| **Differences per stage** | For each of the 11 PRD stages, what (if anything) differs from the closest existing mode? | Stage 3 (UI design) must include Stripe checkout, customer portal, subscription management. Stage 7 (DB) must include billing tables. |
| **Sibling mode** | Which existing mode is closest? You'll crib from its branches. | `standalone-app` |

If any input is missing, stop and ask the user. Do not guess. Guessing produces a bad mode that pollutes the preamble files forever.

---

## 3. Step-by-Step Recipe

### Step 1 — Read the existing preambles
Read every one of the 11 `.archon/commands/stage-NN.md` files (or wherever the preambles live per Pass 0's chosen layout). For each stage, read the 6 existing mode branches. Pay attention to:
- Structure (how each branch is formatted)
- Length (how detailed each gets)
- Voice (instructional, prescriptive, warning)
- What each branch asserts about scope

**Consistency is the whole game here.** Your new branches must match the existing style. Not longer, not shorter, not differently formatted.

### Step 2 — Read MASTER-MODULAR-ARCHITECTURE.md
Sections 2 through 5. Understand the existing 6 modes deeply. Your 7th has to fit into the same mental model.

### Step 3 — Read the archon skill
`C:\Users\lober\.claude\skills\archon\references\authoring-commands.md` — command file format. `references/variables.md` — variable syntax. `SKILL.md` — general orientation.

### Step 4 — Write the mode description section in MASTER-MODULAR-ARCHITECTURE.md
Open MASTER-MODULAR-ARCHITECTURE.md §2 (the "6 build modes" table). Add a new row for your mode. Add the new mode to §2's decision heuristic. Keep the existing rows untouched.

If your mode changes the typical multi-module build sequence (§2.4), note that too.

### Step 5 — Author the 11 new preamble branches
For each stage-NN.md file, add your new IF branch to the preamble block. Place it in the logical spot (e.g., right after the most-similar existing mode).

For each branch:
- Keep the same format as existing branches.
- Be specific about what the stage does differently in this mode.
- Call out what it does NOT do (scope negation is as important as scope definition).
- Reference the mode's sibling mode when you can ("Like standalone-app, but also produces Stripe-integration deliverables").

### Step 6 — Update the `build-type-select` preflight node
In `.archon/workflows/prd-pipeline-d.yaml`, find the `build-type-select` node (per `PIPELINE-REBUILD-NO-BASH-HANDOFF.md` §3.75.C). Add your new mode name to the tag enum and the JSON output schema enum. This is the ONLY YAML edit.

Update the inline mapping table in the prompt text to include the new name + one-line explanation.

### Step 7 — Test
Run pipeline-d with `@type <your-new-mode> Build <test target>`. Expected:
- Side-panel shows `Build type: <your-new-mode>` as the third announcement.
- Every stage's preamble injects the new mode's branch.
- Stages produce output appropriate to the new mode (spot-check 3 stages).

If any stage produces output that doesn't match the new mode's intent, the branch is under-specified — go back to Step 5 for that stage.

### Step 8 — Update the Standardized Module Contract (if applicable)
If your new mode introduces a new module shape (e.g., a paid-module variant with billing hooks), add a section to MASTER-MODULAR-ARCHITECTURE.md §4 describing the extra contract requirements. Otherwise skip.

### Step 9 — Document the mode
Create `docs/page-prds/archon-build-upgrade/mode-<your-mode-name>.md` with:
- The user inputs from §2 above (preserved for future reference).
- A full example build message that uses this mode.
- Known limitations.
- Any open questions you couldn't resolve.

### Step 10 — Commit and announce
Commit: `add build mode: <your-mode-name>`. Push to main.

Announce to the user:
- New mode name + tag syntax.
- Path to the mode documentation file.
- Test result summary.
- Any follow-up work flagged (e.g., "this mode surfaced that stage-08 doesn't handle multi-tenant auth well — note for Pass 2 V3 roadmap").

---

## 4. Success Criteria

- MASTER-MODULAR-ARCHITECTURE.md §2 has a row for the new mode.
- All 11 stage command files have a new IF branch for the new mode.
- `prd-pipeline-d.yaml`'s `build-type-select` node accepts the new mode name.
- Pipeline-d runs cleanly with `@type <new-mode>` and produces mode-appropriate output.
- A mode-specific documentation file exists in `docs/page-prds/archon-build-upgrade/`.
- Zero core stage prompt bodies were modified.
- Zero workflow structure changes (no new nodes, no changed dependencies).

---

## 5. What NOT to Do

- Do NOT modify the core body of any stage command file. You only add one new IF branch per stage.
- Do NOT add new nodes to `prd-pipeline-d.yaml`. The only allowed YAML edit is the enum in `build-type-select`.
- Do NOT rewrite any existing mode's branches. If you think one needs updating, that's a separate task — file it as a note.
- Do NOT invent a new preamble template structure. Match the existing one exactly.
- Do NOT skip Step 2 (inputs from the user). Undefined modes produce bad preambles.
- Do NOT add a mode just because it might be useful someday. Modes are commitments — every future pipeline change has to support them all.

---

## 6. Example — Hypothetical 7th Mode: `saas-with-stripe`

**Inputs collected from user:**
- Name: `saas-with-stripe`
- Description: standalone-app variant with Stripe billing + multi-tenant auth from day one.
- Boilerplate: yes (Next.js + Supabase + Stripe).
- UI: yes.
- Sibling mode: `standalone-app`.

**What the stage-06 preamble branch might look like (sketch, not spec):**

```
IF build_mode == "saas-with-stripe":
  Like standalone-app, but the product is a paid SaaS from day one.
  - Mechanisms MUST include: Stripe checkout integration, webhook handler
    for billing events, customer portal link, subscription state machine.
  - Auth is multi-tenant from the start. Design user + tenant separation.
  - DB schema MUST include: tenants, subscriptions, billing_events tables.
  - Do NOT design "add billing later" seams — billing is first-class.
  - Scope includes the full billed product surface. Do not defer anything
    that touches money or identity to a later phase.
```

Match this depth and format across all 11 stages.

---

## 7. Escape Hatch

If you get 3+ stages in and discover the new mode is fundamentally incompatible with the existing pipeline structure (e.g., it needs a 12th stage, or it changes the DAG topology), **stop and escalate.** That's not a preamble-authoring task — that's a pipeline redesign. Report to the user with:
- Which stages couldn't be accommodated.
- Why.
- Two proposals: (a) scope the new mode differently so it fits, or (b) design a separate pipeline variant for it.

Do not force-fit. A bad preamble is worse than no mode.
