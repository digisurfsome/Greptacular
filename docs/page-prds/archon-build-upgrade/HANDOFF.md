# HANDOFF — Archon Build Upgrade (spec-009)

**Read this BEFORE touching the PRD or any files.**

This handoff corrects 3 mistakes in `README.md` (the PRD). The PRD logic is still good. Only the file paths were wrong.

---

## 1. Where files actually live

Archon is a separate tool installed at `C:\Users\lober\.archon\`. The files this PRD edits are NOT in the Greptacular repo — they are in the Archon install's **project source folder** for Greptacular:

**Base path (use this for every `.archon/...` reference in the PRD):**
```
C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\
```

**Confirmed contents:**
```
workflows/
  prd-pipeline-b.yaml          ← the workflow we are upgrading
  prd-pipeline-a.yaml
  prd-pipeline.yaml
  (plus ce-*, idea-to-spec*, mobbin-wireframe, spec-to-build, style-extractor)

commands/
  build-fix.md                 ← referenced in PRD mechanism M3
  build-verify.md              ← referenced in PRD mechanism M2
  build-implement.md
  build-codebase-plan.md
  build-deploy.md
  build-report.md
  build-review-correctness.md
  build-review-failures.md
  build-review-simplify.md
  build-review-tests.md
  prd-stage-00.md through prd-stage-10.md  ← stage-10 referenced in PRD M3
  (plus ce-*, prd-a-stage-02-enhanced, prd-a-stage-03-enhanced, prd-report)

scripts/                       ← DOES NOT YET EXIST. You will create it.
```

**Every `.archon/...` path in the PRD should be read as relative to the base path above.**

---

## 2. Two corrections to the PRD

### Correction A — Scripts must be Python or TypeScript, not bash

The PRD shows bash snippets (`compliance-gate.sh`, `full-checkpoint.sh`, etc.). Archon's script discovery only supports:

- **`.py`** (runs via `uv`) ← recommend this; simpler for the owner to read
- **`.ts`** or **`.js`** (runs via `bun`)
- **NO `.sh`, no bash**

**Action:** Translate every bash snippet in the PRD into equivalent Python. Logic stays the same (exit 0 / exit 1, same checks). Store them in `.archon/scripts/` using `.py` extension.

**YAML syntax for a script node** (reference — taken from Archon source tests):

```yaml
- id: compliance-gate
  script: compliance-gate    # filename without extension; matches .archon/scripts/compliance-gate.py
  runtime: uv                # 'uv' for .py, 'bun' for .ts/.js
  depends_on: [build-fix]
```

### Correction B — Copy, don't overwrite

Owner's explicit instruction: **do not modify `prd-pipeline-b.yaml` or the existing command prompts directly.** Instead:

1. Copy `prd-pipeline-b.yaml` → `prd-pipeline-c.yaml` and edit the copy.
2. For any command prompt that Phase 1 modifies (M3: `build-fix.md` and `prd-stage-10.md`), create a `-v2.md` version rather than overwriting. Example: `build-fix-v2.md`, `prd-stage-10-v2.md`.
3. Point `prd-pipeline-c.yaml` at the `-v2` command names.

This keeps the original `prd-pipeline-b` workflow working as a fallback. Owner can A/B compare by choosing which workflow to run.

**Note for the PRD:** update §4 M3 to use `-v2.md` naming, and add a new mechanism step "Create `prd-pipeline-c.yaml` as the edited copy of `prd-pipeline-b.yaml`."

---

## 3. What Phase 1 actually creates (full file list with real paths)

After your corrections, Phase 1 should produce exactly these artifacts:

**New files (under `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\`):**

```
scripts/                                   ← new directory
  compliance-gate.py                       ← M1
  full-checkpoint.py                       ← M2
  deploy-gate.py                           ← M8
  archive-prd.py                           ← M10
  regression-harness.py                    ← M11

commands/
  build-fix-v2.md                          ← M3 (tightened contract)
  prd-stage-10-v2.md                       ← M3 (tightened Stage 10 output)
  recovery-diagnose.md                     ← M9 step 1
  recovery-fix-prd.md                      ← M9 step 2
  recovery-execute.md                      ← M9 step 3

workflows/
  prd-pipeline-c.yaml                      ← the edited copy of prd-pipeline-b
```

**Plus (in the Greptacular repo at `C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\`):**

```
.archon/features.yaml                      ← M12 feature toggles
docs/generated-prds/                       ← M10 archive destination (create empty + .gitkeep + INDEX.md)
docs/generated-prds/INDEX.md               ← index table, empty for now
```

Wait — `.archon/features.yaml` conflict. Owner's Greptacular repo doesn't have a `.archon/` folder and shouldn't get one. Put feature toggles alongside the scripts instead:

```
C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\features.yaml
```

Update the PRD §4 M12 to reflect this path.

---

## 4. What Phase 1 does NOT do

Explicit reminder (the PRD says this but it's worth repeating):

- Does NOT modify `prd-pipeline-b.yaml` (copy to `-c`, edit the copy)
- Does NOT modify `build-fix.md` or `prd-stage-10.md` (create `-v2` versions)
- Does NOT execute Phase 2 or Phase 3
- Does NOT run the pipeline end-to-end against a real build (that's Test C, which comes later)

Phase 1 only creates the files above and runs Test A (unit tests on the gate scripts). Stop after that. Report PASS/FAIL in plain English to the owner.

---

## 5. Testing (per PRD §9)

**Test A — Unit tests on the gate scripts (must run before commit).**
Create fixture artifact directories at `.archon/test-fixtures/` with pre-made `review-*.md` and `fix-report.md` files. Run each script against fixtures. Verify exit codes.

Example fixtures:
- `test-fixtures/yt-strategy-lab-artifacts/` — should make `compliance-gate.py` exit 1
- `test-fixtures/task-manager-artifacts/` — should make `compliance-gate.py` exit 0
- `test-fixtures/broken-checkpoint/` — should make `full-checkpoint.py` exit 1

Tests pass = all expected exit codes match. Report `PASS` or `FAIL: <which script, what happened>`.

**Tests B and C run in a later session.** Don't do them yet.

---

## 6. Critical PRD references

The PRD (`README.md` in this folder) has everything else you need:

- **§1 Standards S1–S9** — rules every mechanism must obey
- **§4 Mechanisms M1–M12** — with code snippets (translate bash → Python)
- **§5 Phases** — M1, M2, M3, M8, M9, M10, M11, M12 are Phase 1
- **§9 Test Plan** — Tests A, B, C
- **§15 Model Assignment Table** — which model runs which node

---

## 7. Commit convention

Per repo's `CLAUDE.md`:
- Commit directly to `main`, no branches
- Add only changed files (never `git add -A`)
- Clear message
- Do NOT push (owner will push)
- Report file paths, commit hash, branch

Note: Phase 1 writes files into `C:\Users\lober\.archon\...` (outside the Greptacular git repo) AND into `C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\docs\generated-prds\`. Only the latter is under git. Commit only the repo files. Files under `C:\Users\lober\.archon\...` are not tracked by Greptacular — they live in the Archon install and persist independently.

---

## 8. If something is unclear

Stop and ask the owner. Do not guess paths, do not invent filenames, do not assume. The owner would rather you ask than waste tokens building the wrong thing.

Owner is not a coder. Plain English only in reports.

---

## 9. Starter prompt (paste this at the top of the fresh agent's first message)

> *Read `docs/page-prds/archon-build-upgrade/HANDOFF.md` first. Then read `docs/page-prds/archon-build-upgrade/README.md` (the PRD) with the corrections from HANDOFF.md applied mentally. Then summarize in 3 sentences what Phase 1 actually does, where the files go, and what Test A is. Wait for me to say "go" before executing anything.*

---

## Summary of what changed vs. the original PRD

| PRD said | Reality |
|---|---|
| `.archon/commands/build-fix.md` | `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\commands\build-fix.md` |
| `.archon/workflows/prd-pipeline-b.yaml` | `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\workflows\prd-pipeline-b.yaml` |
| `.archon/scripts/*.sh` (bash) | `.archon/scripts/*.py` (Python, under same Archon path) |
| Edit `prd-pipeline-b.yaml` directly | Copy to `prd-pipeline-c.yaml`, edit the copy |
| Edit `build-fix.md` directly | Create `build-fix-v2.md`, leave original untouched |
| `.archon/features.yaml` in Greptacular repo | `.../source/.archon/features.yaml` under Archon install |

Nothing else in the PRD needs to change. Logic, mechanisms, gates, Recovery Pipeline, model assignments — all still correct.
