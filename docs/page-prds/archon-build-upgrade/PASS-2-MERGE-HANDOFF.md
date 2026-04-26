# Pass 2 — Merge Handoff: V3 Roadmap + PRD Scorecard

**Status:** Handoff for fresh agent. Do this WHILE owner smoke-tests Pass 1 (`pipeline-d.yaml`).
**Owner is not a coder.** No jargon. Plain English.
**Output:** ONE merged spec file. No code changes. PRD work only.

---

## What you're doing

Two source PRDs exist. Merge into one unified Pass 2 spec that an executing agent can run later.

1. **V3 Roadmap** — 10 paint-by-numbers fixes. Takes PRD maker from 7.5/10 → 9.5/10.
2. **PRD Scorecard / Self-Check** — quality gate after stage 10. Scores PRD by percentage. Kicks back if too low. Caps revision loops. Notifies owner on stuck.

Both exist as separate PRDs. Owner wants ONE spec the next agent can execute end-to-end.

---

## Read first (in this order)

| Order | Path | Why |
|---|---|---|
| 1 | `docs/page-prds/archon-build-upgrade/README.md` | Index. Orients you to the upgrade project. |
| 2 | `docs/page-prds/archon-build-upgrade/PRD-MAKER-V3-ROADMAP.md` | Source A. The 10 fixes. |
| 3 | `docs/page-prds/archon-build-upgrade/M14-PRD-SELF-CHECK.md` | Source B. The scorecard / triage / kickback loop. |
| 4 | `docs/page-prds/archon-build-upgrade/PASS-0-PREAMBLE-AUDIT-HANDOFF.md` | Context — what Pass 0 did to stage prompts. |
| 5 | `docs/page-prds/archon-build-upgrade/PIPELINE-REBUILD-NO-BASH-HANDOFF.md` | Context — what Pass 1 built (pipeline-d.yaml). |
| 6 | `docs/page-prds/archon-build-upgrade/PASS-1-DELTA.md` | Context — late decisions during Pass 1. |
| 7 | `C:\Users\lober\archon-pipeline-rebuild\.archon\workflows\pipeline-d.yaml` | The actual built pipeline. Know what already exists before you spec changes. |

Do NOT read the rest of `archon-build-upgrade/`. Reference history, not needed.

---

## The Scorecard feature — what it is

(M14 covers this. Summarized here so you can see the merge shape.)

- After stage 10 produces the PRD, run **3 parallel reviewer nodes** (Opus, fresh context):
  - correctness
  - completeness
  - coherence
  - (optional 4th: build-feasibility)
- Each reviewer returns findings + a **percentage score** for its lens.
- A **triage node** (one Opus call) aggregates findings + scores, classifies:
  - **clean** → proceed to build
  - **tier 1 (tiny)** → Sonnet in-place edit, no re-run, no loop count
  - **tier 2 (medium)** → re-run broken stage + downstream stages
  - **tier 3 (structural)** → re-run from root forward
- Loop cap: **2 revisions max**. Past 2 → flag owner, do not auto-build.
- Per-stage **revision preamble** (conditional block) injected when `revision_mode == true`.

---

## Where the merge lives

The V3 Roadmap has 10 fixes. The scorecard isn't on that list — it's deferred in M14. **Add it as Fix #11**, OR fold it into existing fixes if a clean home exists. Your call. Justify the placement.

Likely cleanest: **new Fix #11 — "Post-Stage-10 Quality Gate"** because it adds nodes, not edits to existing stages. But if you find a V3 fix it merges naturally into, say so.

---

## What to produce

**One file:**

```
docs/page-prds/archon-build-upgrade/PASS-2-UNIFIED-SPEC.md
```

**Structure:**

```
# Pass 2 — Unified Upgrade Spec (V3 Roadmap + Scorecard)

## Goal
One sentence. (Take pipeline-d from baseline → 9.5/10 + add safety net.)

## Source materials
- V3 Roadmap (10 fixes)
- M14 Scorecard / Self-Check
Brief one-line each on what they bring.

## Pre-flight (what already shipped)
Brief list. Pass 0 (mode-agnostic stages + 6-mode preambles), Pass 0.5 (contract-spec patches), Pass 1 (pipeline-d.yaml 24 nodes, no bash, no python, fail-fast on @type). Executing agent must NOT redo these.

## The 11 fixes (ordered)
For each: number, title, problem, fix, files touched, est tokens, depends-on.
Fixes 1-10 = V3 Roadmap (carry over verbatim or tightened).
Fix 11 (or wherever) = the Scorecard.

## Scorecard fix — full spec
Architecture diagram (steal M14's). Reviewer node count + lenses. Score schema.
Triage tier rules. Loop cap. Owner notify message. Revision preamble block.
Dependency map for tier 2 cascades (validate against actual stage files in
C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\commands\).

## Execution order
Which fixes block which. What can run parallel vs. serial. Total est tokens.

## Acceptance checks
Per fix: how the executing agent proves it shipped. Plain checks owner can verify.

## Out of scope
What this Pass 2 does NOT do. (E.g. KNOWN-ISSUES #4 hardcoded 3 build phases —
note whether it's in or out.)

## Open questions for owner
Anything you couldn't decide. Keep short.
```

---

## Hard rules

1. **Do not edit pipeline-d.yaml.** This is a PRD. The next agent edits code.
2. **Do not modify the source PRDs.** V3 Roadmap and M14 stay as-is.
3. **Repo:** work in `C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\` (Greptacular). NOT in `archon-pipeline-rebuild` — that's the engine repo.
4. **Commit only the new file.** `git add docs/page-prds/archon-build-upgrade/PASS-2-UNIFIED-SPEC.md`. Never `-A`.
5. **Commit message:** ASCII single line, no `[`, no `Pass`, no `the`. Hooks block those. Try: `add pass 2 unified spec merging v3 roadmap and scorecard`.
6. **Do NOT push.** Owner pushes.
7. **No bash, no python in the spec.** Pipeline is bash-free. Anything you spec must be Archon-native (prompt nodes, when:, depends_on, dispatcher booleans). See pipeline-d.yaml for patterns.
8. **No workflow imports.** Archon engine doesn't support them (confirmed Pass 1). Single-file, switches inline.
9. **Plain English.** Owner is not a coder. Each fix needs a one-sentence "what this gets you" in normal words.
10. **Token estimates use the rule:** ~500K tokens per 30 min agent time. Don't quote human hours.

---

## Decisions you can make alone

- Fix ordering / dependencies between V3 fixes and the scorecard.
- Whether scorecard becomes Fix #11 or folds into an existing V3 fix.
- Reviewer count (3 vs 4 — M14 leans 3, you decide).
- Percentage thresholds (e.g. "below 70% = tier 2 reroll"). Pick a default, mark as tunable.
- Triage output JSON schema (extend M14's if needed).

## Decisions to escalate (Open questions section)

- Tier 3 behavior: auto-rerun once or hard-stop immediately? (M14 leans auto-once. Confirm.)
- Should the scorecard ALSO run between PRD stages (mid-pipeline gate) or only post-stage-10? Default: post only. Flag if you see strong reason for mid-pipeline.
- Does a low score on a single lens (e.g. 50% coherence, 95% others) trigger reroll, or only aggregate? Pick a default + flag.

---

## What "done" looks like

- One file at `docs/page-prds/archon-build-upgrade/PASS-2-UNIFIED-SPEC.md`.
- 11 fixes (or however many — justify count).
- Clear execution order.
- Acceptance checks owner can read without asking what words mean.
- Committed to main, not pushed.
- Final reply to owner lists: file path, commit hash, fix count, total est tokens, biggest open question.

---

## What you should NOT do

- Do not start implementing fixes. Spec only.
- Do not touch `archon-pipeline-rebuild/`.
- Do not redesign Pass 0 or Pass 1 work. They shipped.
- Do not invent new stages or rename existing ones.
- Do not add a new build mode (the 6 are locked).
- Do not propose anything requiring engine features that don't exist (env: field, `||` in when:, workflow imports). If you need them, spec a workaround using dispatcher booleans + prompt-node wrappers (Pass 1 patterns).

---

**Caveman: terse OK. Owner reads spec. Dense > fluffy.**
