# /prd-docs -- Refresh Project Documentation

## Purpose

Manually trigger the `project-docs` skill to update the `docs/` tree for the current project.

## When to Use

1. After implementing a significant feature or refactor
2. When onboarding a new contributor and docs feel stale
3. When you want to force a full docs review
4. As a spot-check that documentation reflects current implementation

## Execution

### Phase 1 -- Verify Project Context

Confirm `docs/prd/PRD.md` exists. If absent, warn: "No PRD found. Run `/prd-new` first."

### Phase 2 -- Detect Mode

- **CREATE mode**: triggered when `docs/index.md` is absent (generate all sub-files from scratch)
- **UPDATE mode**: triggered when `docs/index.md` is present (diff and refresh)

### Phase 3 -- Apply Skill

Follow instructions at `.claude/skills/project-docs/SKILL.md` exactly for the detected mode.

### Phase 4 -- Report

- List files created or updated
- Summarize what changed
