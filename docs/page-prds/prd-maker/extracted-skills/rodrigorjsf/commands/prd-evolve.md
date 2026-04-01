---
description: Evolve the PRD and project skills when product scope changes
argument-hint: [description of what changed]
allowed-tools: AskUserQuestion, Agent, Read, Write, Edit, Bash, TodoWrite, WebSearch, WebFetch
model: opus
---

# /prd-evolve — PRD Evolution

You are orchestrating an incremental PRD evolution. You update ONLY the artifacts impacted by the described scope change, preserving all existing decisions that remain valid.

**CRITICAL RULES:**
- All generated/updated files MUST remain in English
- Do NOT regenerate artifacts that are unaffected by the change
- Every skill header must be updated with the new `prd_version`
- Respond to the user in whatever language they write

**Input:** `$1` — description of what changed (required)

---

## PHASE 0 — Read Current State

Create tasks: Delta Analysis / Research & Validation (if needed) / Artifact Updates / Commit

### Pre-flight Check

Before reading any files, verify that `docs/prd/PRD.md` exists.
If it does NOT exist:
- Error: "No PRD found at docs/prd/PRD.md. Run `/prd-new` first to generate the initial PRD."
- Exit without modifying any files.

Read the following files:
- `docs/prd/PRD.md` — extract current version from header
- `docs/prd/ARCHITECTURE.md`
- `docs/prd/ER.md` (if exists)
- `.claude/skills/project-guardian/SKILL.md` — read `prd_version` field
- `.claude/skills/project-architecture/SKILL.md`
- `.claude/skills/project-domain-rules/SKILL.md`
- `.claude/skills/project-compliance/SKILL.md`
- `.claude/skills/project-cicd/SKILL.md` (if exists) — read `vcs` and `pipeline_file` from frontmatter
- Identify existing pipeline file: check for `.github/workflows/ci.yml`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`

Check for stale skills: if any skill's `prd_version` < PRD's current version, warn the user that skills were already out of sync before this evolution.

---

## PHASE 1 — Delta Analysis

Mark task "Delta Analysis" as in_progress.

Dispatch `requirements-analyst` agent with:
```json
{
  "mode": "delta",
  "change_description": "$1",
  "current_prd_summary": "<key sections from PRD.md>",
  "current_architecture_summary": "<stack table + ADRs from ARCHITECTURE.md>"
}
```

The agent returns:
```json
{
  "delta_type": ["new_feature" | "removed_feature" | "new_tech" | "new_technology" | "compliance_change" | "architecture_change" | "architecture_pivot" | "integration_change"],
  "new_prd_version": "X.Y",
  "affected_artifacts": ["PRD.md §2", "project-domain-rules", ...],
  "pending_research": ["<new tech or regulation>"],
  "clarifications_needed": ["<question if change is ambiguous>"]
}
```

If `clarifications_needed` is non-empty, ask the user those questions via `AskUserQuestion` before continuing.

Mark task "Delta Analysis" as completed.

---

## PHASE 2 — Research & Validation (conditional)

If `delta.pending_research` is non-empty:

Mark task "Research & Validation" as in_progress.

Dispatch `official-researcher` agents in parallel for each new tech/regulation.

Then dispatch `research-validator` in a fresh Agent context to validate all new research.

Loop (max 3 iterations) until all research is `approved: true` or `partially_validated`.

Mark task "Research & Validation" as completed.

---

## PHASE 3 — Artifact Updates (selective parallel)

Mark task "Artifact Updates" as in_progress.

Based on `delta.affected_artifacts`, dispatch ONLY the relevant update agents in parallel:

**If PRD.md sections affected:**
Dispatch `prd-writer` with:
```json
{
  "mode": "update",
  "sections_to_update": ["<list from delta>"],
  "change_description": "$1",
  "new_prd_version": "<delta.new_prd_version>",
  "delta": "<structured delta from requirements-analyst: new/updated/removed requirements, NFRs, domain rules, integrations>",
  "research_refs": "<new validated refs>",
  "current_prd_path": "docs/prd/PRD.md"
}
```

**If architecture affected:**
Dispatch `architecture-designer` with:
```json
{
  "mode": "update",
  "change_description": "$1",
  "current_architecture": "<ARCHITECTURE.md content>",
  "new_decisions": "<from delta analysis>"
}
```
Present updated architecture to user for approval before writing.

**If stack changes:**
Dispatch `stack-guide-generator` with:
```json
{
  "mode": "update",
  "changed_layers": ["<layers affected>"],
  "new_technologies": ["<list>"]
}
```

**If delta_type includes `new_tech`, `new_technology`, `architecture_change`, or `architecture_pivot`:**
Dispatch `cicd-generator` with:
```json
{
  "mode": "update",
  "context_packet": {
    "identity": "<from PRD.md header>",
    "infrastructure": {
      "vcs": "<from project-cicd SKILL.md frontmatter vcs field>",
      "branch_strategy": "<from project-cicd SKILL.md frontmatter or ARCHITECTURE.md>"
    },
    "repo_structure": "monorepo"
  },
  "architecture": "<updated architecture from architecture-designer output if dispatched, otherwise current ARCHITECTURE.md>",
  "changed_services": "<services affected by the change>",
  "change_description": "$1"
}
```

**Always — update affected skills:**
Dispatch `skills-generator` with:
```json
{
  "mode": "update",
  "affected_skills": ["<list from delta>", "project-docs"],
  "change_description": "$1",
  "new_prd_version": "<delta.new_prd_version>",
  "context_delta": "<delta output>"
}
```

(Note: `project-docs` is always included — any product delta warrants a documentation review.)

**Sequential step — Apply project-docs skill UPDATE mode:**
After skills-generator completes, invoke the project-docs skill UPDATE mode:
1. Read current `docs/index.md` and all sub-files
2. Read updated `docs/prd/PRD.md` and `docs/prd/ARCHITECTURE.md`
3. Compare docs vs current implementation and the change described in `$1`
4. Update stale sections, remove sections that no longer apply, add sections for new aspects
Follow the skill instructions at `.claude/skills/project-docs/SKILL.md` exactly.
Add updated docs/ files to the commit staging area.

Mark task "Artifact Updates" as completed.

---

## PHASE 4 — Commit

Mark task "Commit" as in_progress.

Stage only the modified files and commit:
```bash
git add docs/prd/ docs/stack/ CLAUDE.md backend/ frontend/ infrastructure/ .claude/skills/ .claude/settings.json
git add .github/ 2>/dev/null; git add .gitlab-ci.yml 2>/dev/null; git add bitbucket-pipelines.yml 2>/dev/null; true
git commit -m "feat(prd): evolve to v<new_version> — $1

Updated artifacts: <comma-separated list of affected_artifacts>
prd-generator-plugin: /prd-evolve"
```

Mark task "Commit" as completed.

---

## Completion Summary

Report to user (in their language):
1. PRD updated to version `<new_version>`
2. Artifacts updated: list with brief reason each was updated (include CI/CD pipeline file if updated)
3. Artifacts untouched: list (so user knows what was preserved)
4. If any research was `partially_validated`: show the specific issues flagged
