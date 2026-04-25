# Known Issues — Archon Pipeline / Template / Ecosystem

> Running log of bugs, friction points, and upstream issues that matter but aren't yet fixed. File them here so future agents don't rediscover them from scratch.

---

## Issue #1 — Cannot create a second project from the same GitHub template

**Status:** Unresolved. Workaround TBD. Likely upstream Archon bug.

### What the template is

`digisurfsome/archon-module-template` is a GitHub template repository set up to scaffold new modular build projects. It contains pre-loaded:
- `.archon/` directory structure (workflows, commands, config)
- `.archon/scripts/` pre-populated so new modules don't need to re-create plumbing
- Baseline `CLAUDE.md`, `README.md`, `.gitignore`

Workflow:
1. On GitHub, click "Use this template" on `digisurfsome/archon-module-template`.
2. Create a new repo — e.g., `digisurfsome/audio-recorder-scaled`.
3. Register that new repo in Archon as a project.
4. Run pipeline-d against it.

### The problem

**Archon will not let the user register a second project created from the same template.** After the first copy (`audio-recorder-scaled`) was registered and used, attempting to register a second template-derived repo under a different name fails — no matter what the new repo is named.

The first copy works fine. Only the second+ copies break.

### What we don't know yet

- Is the rejection at the GitHub-side (template-clone step fails) or the Archon-side (registration step fails)?
- Is Archon keying projects by template-origin-URL and refusing duplicates?
- Is there a cache/DB entry (`C:\Users\lober\.archon\archon.db`) that needs clearing?
- Does this affect local-registered projects or only GitHub-registered?
- Does running `archon isolation cleanup` or deleting an entry from `C:\Users\lober\.archon\config.yaml` unblock it?

### Why this matters

The whole modular architecture (MASTER-MODULAR-ARCHITECTURE.md) assumes you'll spin up many small module repos from this template — 5+ for CallPitch alone. If the second template copy can't be registered, the architecture can't scale past the first module. Hard blocker for CallPitch-style multi-module builds.

### Current workaround (interim — confirmed pattern)

**Use `git clone` instead of "Use this template" GitHub button.** The template second-copy bug appears to trigger only when GitHub's "Use this template" feature is invoked. A plain `git clone` followed by repointing the remote to a new GitHub repo bypasses whatever Archon-side metadata is causing the rejection.

```
git clone https://github.com/digisurfsome/archon-module-template.git <new-repo-name>
cd <new-repo-name>
# Create empty new repo on GitHub first, then:
git remote set-url origin https://github.com/digisurfsome/<new-repo-name>.git
git push -u origin main
# Then register in Archon as a normal project — no template metadata to trip on
```

This is the pattern Pass 0/1/2 work uses (see those handoffs §0.5).

### Other workarounds to try if `git clone` doesn't unblock everyone

1. **Rename the first project's Archon registration** to something unrelated, then register the second. If the conflict is name-collision inside Archon's DB, this might clear it.
2. **Inspect `C:\Users\lober\.archon\archon.db`** (SQLite) for template-origin fields and manually delete stale entries.
3. **Run without the template** — hand-create the `.archon/` directory in each new repo. Loses the convenience but unblocks multi-module builds.

### Upstream action needed

- [ ] File an issue on `coleam00/archon` (the upstream Archon fork source) OR the AutoForgeAI fork at `https://github.com/AutoForgeAI/autoforge` with:
  - Minimal repro steps (create template, use once, try to use twice)
  - Exact error message from the second attempt
  - Relevant logs from the Archon backend
- [ ] Link the filed issue back here once created.

### To-do for next session

1. **Reproduce the error cleanly** — create a third test repo from the template and capture the exact error message (screenshot + stderr).
2. **Test workaround #1** (rename first project's registration) first — lowest-risk.
3. **If workaround found**, document it in a "Workaround" subsection of this issue.
4. **File the upstream bug** per above.

---

## Issue #2 — Archon substitutes unknown variables to empty string before bash runs

**Status:** Known. Cause of most bash failures in pipeline-c. Eliminated in pipeline-d rebuild by removing bash nodes entirely.

### The behavior

If a bash node references `$SOME_VAR` and that variable is not defined as an Archon variable or upstream node output, Archon substitutes it to an empty string **before** handing the script to bash. The bash script then runs with `[ -d "" ]` or `[ '' = PASS ]` — always false, producing cascading gate failures.

### Reference

Full post-mortem documented inline in `PIPELINE-REBUILD-NO-BASH-HANDOFF.md` §2 bug #4 and #5.

### Resolution

Pipeline-d (Pass 1) eliminates bash nodes in favor of `prompt:` nodes with `output_format: json`. Variable substitution failures become impossible when there are no bash nodes.

---

## Issue #3 — Graph view stuck on "Loading graph..."

**Status:** Open. Frontend bug in forked Archon.

### The behavior

When viewing a running or completed workflow run in the Archon UI, the graph visualization panel shows "Loading graph..." and never resolves to the actual DAG visualization. The run itself completes fine — only the visualization is broken.

### Impact

Low. Run status, node output, and artifacts are all accessible via other panels. The graph view is a nice-to-have, not a blocker. User can inspect run results without it.

### To-do

- [ ] Check if the upstream Archon (before fork) has the same bug.
- [ ] If fork-specific, file an internal issue and fix in a UI patch session.

---

## Issue #4 — Three build phases hardcoded regardless of PRD's actual phase count

**Status:** Open. Pipeline-c and BUILD variant both assume exactly 3 phases.

### The behavior

The build half of pipeline-c has three hardcoded phase nodes (phase-1, phase-2, phase-3) with compliance gates between each. If the PRD outputs a different phase count (2 phases, or 4+ phases), the pipeline either leaves later phases unbuilt or fails because the PRD doesn't populate all three.

### Fix

Defer to Pass 2 (V3 Roadmap) or a dedicated follow-up. Needs either:
- **Dynamic phase loop** — a loop node that iterates through however many phases the PRD defined.
- **Explicit phase declaration in PRD** — stage 10 outputs `phase_count: N`, the workflow reads it and activates the right number.

---

## How to Add New Issues

When you encounter a new friction point:
1. Add a new `## Issue #N` section following the template above.
2. Fill in: what the problem is, why it matters, what we don't know, interim workaround, upstream action needed.
3. Commit with message `docs: add known issue #N — <short description>`.
4. Reference this file in whatever PRD you're working on so the next agent sees it.
