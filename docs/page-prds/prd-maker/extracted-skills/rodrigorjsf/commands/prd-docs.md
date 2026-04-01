# /prd-docs — Refresh Project Documentation

Manually trigger the `project-docs` skill to update the `docs/` tree for the current project.

## When to Use

- After implementing a significant feature or refactor
- When onboarding a new contributor and docs feel stale
- When you want to force a full docs review
- As a spot-check that documentation reflects current implementation

## Execution

1. **Verify project context**: Confirm `docs/prd/PRD.md` exists. If not, warn: *"No PRD found. Run `/prd-new` first."*

2. **Detect mode**:
   - `docs/index.md` absent → **CREATE mode** (generate all sub-files from scratch)
   - `docs/index.md` present → **UPDATE mode** (diff and refresh)

3. **Apply project-docs skill**: Follow the instructions at `.claude/skills/project-docs/SKILL.md` exactly for the detected mode.

4. **Report**: After completing, list the files created or updated and summarize what changed.
