# M14 — Post-Stage-10 PRD Self-Check + Revision Loop

**Status:** Deferred spec. Implement after first clean greenfield build of `prd-pipeline-c.yaml` is proven. Pairs with M13.

**Goal:** After stage 10 produces the PRD, run a review pass before handing off to the builder. Fix problems at the right level. Cap loops. Flag owner if structurally broken.

---

## Why this matters

Current pipeline: stages 00-10 produce PRD → stage-10 output → build starts immediately.

Problem: no safety check between PRD and build. A bad PRD burns an entire Sonnet build cycle before compliance-gate catches it. Cheaper to catch it at the PRD layer.

---

## Architecture

```
stage-10 (output generator)
    ↓
┌─ prd-review-correctness    ┐
├─ prd-review-completeness   ├─ 3-5 parallel reviewers, Opus, fresh context
├─ prd-review-coherence      ┤  retry: 3, on_error: all (bench pattern)
└─ prd-review-build-feasibility ┘
    ↓
prd-triage  (Opus, one classification call)
    ↓
    ├─ tier 1 → prd-fix-tiny (Sonnet, in-place edit) → done
    ├─ tier 2 → re-run from [broken_stage] forward with revision context → loop
    ├─ tier 3 → re-run from root stage forward with revision context → loop
    └─ clean  → proceed to build-codebase-intelligence
    ↓
(loop counter: max 2 revisions, then flag owner)
```

---

## Three tiers

### Tier 1 — Tiny / cosmetic (in-place edit, no re-run)

**What counts:** typos, missing field, inconsistent naming, broken cross-reference, markdown formatting, short section needing one paragraph.

**Fix agent:** `prd-fix-tiny`, Sonnet, single edit pass.

**Restart from:** nowhere. PRD is clean. Proceed to build.

**Loop impact:** does not consume a revision count.

### Tier 2 — Medium / one stage is wrong (re-run from broken stage forward)

**What counts:** one section factually wrong, mechanism breakdown off, persona misread, integration point missing, protocol testing section out of date because upstream changed.

**IMPORTANT:** re-running just the broken stage is WRONG. Downstream stages consumed its output. They are now stale and must re-run too.

**Fix agent:** re-run the broken stage + every downstream stage that consumed its output.

**Restart from:** `broken_stage` forward. Use dependency map (below) to skip stages that don't depend on the broken one.

**Dependency map (approximate — validate during implementation):**

| Stage | Depends on | Feeds into |
|---|---|---|
| 00 tech-foundation | (none) | 03, 04, 05, 10 |
| 01 idea-capture | (none) | 02, 03 |
| 02 gap-analysis | 01 | 03 |
| 03 structure | 00, 01, 02 | 04, 10 |
| 04 mechanism | 00, 03 | 05, 10 |
| 05 wall-door-room | 00, 04 | 06, 10 |
| 06-09 build scaffolding | 05 | 10 |
| 10 output generator | all prior | (final) |

**Example:** mechanism (stage 04) broken → re-run 04, 05, 06, 07, 08, 09, 10. Skip 00, 01, 02, 03.

**Revision preamble injected into each re-run stage command (conditional):**

```
IF revision_mode == true:
  ## REVISION CONTEXT
  This is revision attempt $revision_number for this PRD.
  Root cause: $triage_root_cause
  Broken upstream stage: $broken_stage_id
  Specific findings to address: $findings_list
  Components to focus on: $affected_components
  
  You have full permission to change sections related to the root cause.
  Preserve sections unrelated to the root cause from the prior run.
  Do not redo work that was already correct.
```

Each stage command file gets this preamble block at top, fires only when `$revision_mode == true`. Conditional, not duplicated.

### Tier 3 — Structural / foundation is wrong (re-run from root forward)

**What counts:** tech foundation wrong, whole mechanism model wrong, core idea misread the user. Cascades through everything.

**Fix agent:** re-run from the broken root stage (usually 00 or 01) forward. Everything downstream.

**Restart from:** `broken_root_stage` forward. Full cascade.

**Same revision preamble** as Tier 2.

---

## The triage node

**`prd-triage`** — one Opus call after reviewers return.

**Input:** all reviewer findings + current PRD.

**Output (structured JSON):**
```json
{
  "tier": 1 | 2 | 3 | "clean",
  "broken_stage": "stage-XX" | null,
  "root_cause": "short string",
  "findings": [...],
  "affected_components": [...],
  "confidence": 0.0-1.0
}
```

**Why Opus:** triage is judgment-heavy. Cheap per-call (one invocation per revision loop). Worth the Opus quality.

---

## Loop cap + escalation

**Max 2 revision loops.** After 2 revisions, if reviewers still flag problems:

**Do NOT continue to build.** Stop and flag owner.

**Owner notification message:**
```
PRD revision limit reached (2 attempts).
Reviewers still flagging issues after 2 revisions.
Root causes across revisions:
  Attempt 1: $r1_root_cause
  Attempt 2: $r2_root_cause

This may indicate:
  - Genuine hallucination / off-day on agents (try again later)
  - Contradictory / impossible requirements in the intake
  - A real structural problem that needs human judgment

Current PRD state saved to: $prd_path
Review decision points:
  1. Approve as-is and build anyway
  2. Discard and re-run from scratch
  3. Edit intake and re-run from stage 01
```

**Why 2 loops:** enough to catch one bad pass + one bad fix. Beyond 2 = pattern, not luck. Infinite loops burn tokens and bury the signal.

**Why notify instead of auto-build:** owner's rule is "never halt for no reason." But this is a reason — sustained failures across 2 revisions = real signal. Auto-building on a PRD that 2 review passes couldn't clean is worse than pausing.

---

## Tier 1 loop handling

Tier 1 (tiny) fixes don't count against the 2-loop cap because they don't re-run stages. One-off edits. Can loop 3-5 times on tiny stuff if needed (though realistically if reviewers keep finding typos, one Sonnet pass gets them all).

---

## Implementation notes

1. **Build triage node first** — it's the brain of the loop. Test with canned reviewer inputs before wiring live.
2. **Dependency map** — validate by reading actual stage command files. The table above is approximate.
3. **Revision preamble** — add to each stage command file as a single conditional block. One edit per file, ~8 files touched.
4. **Counter state** — stored in workflow context as `$revision_number`, incremented at triage node.
5. **Escalation UX** — how does the "flag owner" message actually reach the owner? Likely via archon's handoff file mechanism (`C:\Users\lober\.autoforge\handoffs\`). Confirm at implementation time.

**Est effort:** 15-30 min agent time. More than M13 because it adds new nodes + triage logic + per-stage preambles.

---

## Do NOT start this until

- [ ] `prd-pipeline-c.yaml` completes at least one successful greenfield build end-to-end
- [ ] Owner has run the pipeline on 2-3 real projects and has feel for failure modes
- [ ] Dependency map validated against actual stage command files

---

## Open questions

- Should tier 3 also hard-stop and notify owner, given how expensive a full re-run is? Or auto-re-run once? Lean: auto-re-run once, then escalate on loop 2.
- Do we need a separate "build-feasibility" reviewer? Or fold into correctness? Probably separate — it's a distinct lens.
- Reviewer count: 3 vs 5? Start with 3, scale if we find gaps.
