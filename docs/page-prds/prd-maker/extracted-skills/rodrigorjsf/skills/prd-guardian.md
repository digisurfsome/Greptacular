# PRD Guardian Skill

PRD Guardian is a skill for projects using `prd-generator-plugin` that enforces consultation of project-specific skills before implementing features, making architectural decisions, or reviewing code.

## Key Activation Points

The skill triggers when you're about to:
- Implement a feature
- Make architectural decisions
- Review or refactor code

## Required Check Sequence

Before proceeding with work, verify these five skills in order:

1. **project-guardian** — PRD alignment check
2. **project-architecture** — Canonical stack verification
3. **project-domain-rules** — Business invariant compliance
4. **project-compliance** — Regulatory requirement validation
5. **project-docs** — Documentation currency confirmation

## Version Synchronization

Compare version numbers between `.claude/skills/project-guardian/SKILL.md` and `docs/prd/PRD.md`. If they differ, alert the user: *"Project skills are out of sync with PRD. Run `/prd-evolve` to sync before proceeding."* Continue work but flag material discrepancies.

## Mandatory Warnings

These situations always require alerts:
- Missing `docs/prd/PRD.md` — suggest `/prd-new`
- Missing `.claude/skills/project-guardian/SKILL.md` — note skills not generated
- Feature removal without `/prd-evolve` — remind to run sync command first

## Documentation Reference Structure

Key files include the PRD, architecture specs, entity models, skill enforcements, and domain/backend/frontend/infrastructure standards guides.
