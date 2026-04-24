# M13 — Existing-App Mode (Conditional Stage Behavior)

**Status:** Deferred spec. Do not implement until `prd-pipeline-c.yaml` is proven running end-to-end on a greenfield build.

**Goal:** One pipeline, two modes. Greenfield = current behavior. Existing-app = stages 00/02/03 morph to fit. No forked pipeline file.

---

## Why conditional, not forked

- Most nodes (stages 04-10, all build/review/phase nodes, recovery branch) do not change between modes.
- Forking = two YAML files to maintain, drift risk, edits get made to one and forgotten on the other.
- Conditional = one YAML, one source of truth, flag decides behavior at three specific nodes.

---

## The flag

Pipeline-level variable `project_mode: greenfield | existing`.

**How it gets set:**
- **Auto-detect (preferred):** new pre-stage node scans target workspace. If code files exist (package.json, requirements.txt, go.mod, Cargo.toml, pyproject.toml, src/ with content) → `existing`. Else → `greenfield`.
- **Manual override:** user flag in intake. Beats auto-detect.

Stored in workflow context. All three morphed stages read `$project_mode`.

---

## Stage 00 — Tech Foundation (needs edit)

Stage 00 is really a **foundation mode picker**, not just a stack picker. Four modes, all end at the same 1992-point checklist applied to the chosen foundation.

| Mode | Source of foundation | Stage 00 action |
|---|---|---|
| `default-boilerplate` | One of owner's pre-built boilerplates | Pick best-fit boilerplate, run 1992-point checklist against it |
| `user-boilerplate` | User supplies their own boilerplate | Analyze user boilerplate, run 1992-point checklist against it |
| `user-existing-app` | User has a running app to extend | Scan target repo, run 1992-point checklist against it |
| `greenfield-custom` | None of the above fits (rare) | Pick stack from scratch, run 1992-point checklist against the chosen plan |

**Key distinction:** first three modes **observe** — they document what's already there. Only `greenfield-custom` **chooses**. No mode should try to swap a user's React for Vue.

**Command file:** edit `.archon/commands/prd-stage-00-tech-foundation.md` — add mode selection at top, then 1992-point checklist runs against the chosen foundation in all four branches.

**Output:** same schema across all modes. Fields get populated from observation or selection depending on mode. Flag deprecated deps / security advisories as **notes**, not blockers (owner decides).

### Sub-step split (recommended during implementation)

Stage 00 currently conflates two decisions. Split into sub-stages:

- **Stage 00a — Foundation Mode Picker.** Picks one of the four modes above. Cheap call. May ask owner if ambiguous.
- **Stage 00b — Stack Observer/Chooser.** Given the mode, either observes (modes 1-3) or picks (mode 4) the stack. Runs 1992-point checklist.

Rationale: can't pick a stack before knowing the foundation. Splitting makes the ordering explicit and lets 00b skip expensive stack-picking logic when it's really just documenting what's already there.

---

## Stage 02 — Gap Analysis + Market Research (needs edit)

**Greenfield behavior (current):** market research, competitor analysis, gap identification.

**Existing-app behavior (new):**
- Keep market research (still useful — is this feature a good idea?)
- **Add Feature Interaction Matrix:** list existing app features, map new feature against each. For each existing feature, answer:
  - Does new feature touch this? (yes/no)
  - If yes, does it break it, extend it, or replace it?
  - Migration / backward compat required?
- Output section: "Feature Interaction Matrix" appended to gap analysis.

**Command file:** edit `.archon/commands/prd-stage-02-gap-analysis.md` — add existing-app section.

---

## Stage 03 — Agent OS Structuring (small add)

**Greenfield behavior (current):** personas, feasibility, market fit.

**Existing-app behavior (new):**
- All current sections stay.
- **Add Integration Points section:**
  - Existing APIs/endpoints touched
  - Existing DB schemas affected
  - Existing auth/permission flows affected
  - Risk register — what could break
  - Backward compatibility plan
  - Data migration plan (if any)

**Command file:** edit `.archon/commands/prd-stage-03-structure.md` — add section, conditional on `$project_mode == 'existing'`.

---

## Stages 01, 04, 05+ — No change

- **01 Idea Capture** — mode-agnostic.
- **04 Mechanism Extraction** — mechanisms are mechanisms.
- **05+ Wall/Door/Room + build + review + recovery** — all unchanged.

---

## Implementation order (when ready)

1. Add mode-detection pre-node OR add mode flag to intake.
2. Edit stage 00 command to branch on mode.
3. Edit stage 02 command to append interaction matrix.
4. Edit stage 03 command to append integration section.
5. Test: run greenfield build — should behave identically.
6. Test: run existing-app build on Greptacular itself as dogfood.

**Est effort:** ~3-5 min agent time for edits. Testing time dominates.

---

## Open questions (defer to implementation)

- Does auto-detect run as a new stage (pre-00) or inline in stage-00? Recommend pre-00 so flag is set before any stage needs it.
- What counts as "existing code"? Threshold = any non-config source file, OR specific file count?
- Do we want `project_mode: hybrid` for "existing app but greenfield module"? Probably overkill. Start with binary.

---

## Do NOT start this until

- [ ] `prd-pipeline-c.yaml` has completed at least one successful greenfield build end-to-end
- [ ] Post-Stage-10 PRD self-check mechanism is specced (M14, separate doc)
- [ ] Owner explicitly greenlights existing-app mode as next priority
