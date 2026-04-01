# PRD Guardian Skill

> Source: rodrigorjsf/prd-generator-plugin/skills/prd-guardian/SKILL.md

## Overview

The PRD Guardian skill activates in projects managed by prd-generator-plugin. Its core function: ensure AI agents consult project-specific enforcement skills before implementing features, making architectural decisions, or reviewing generated code.

## Activation Trigger

Load this skill when working in any project containing:
- `docs/prd/PRD.md`
- `.claude/skills/project-guardian/SKILL.md`

## Decision Flow

Three-question gate:
1. About to implement a feature?
2. Making an architectural decision?
3. Reviewing or refactoring code?

Any "yes" answer --> load project skills --> proceed.

## Required Check Order (Sequential)

1. **project-guardian** -- Consistency with PRD
2. **project-architecture** -- Technology/pattern alignment with canonical stack
3. **project-domain-rules** -- Domain invariants and ubiquitous language respect
4. **project-compliance** -- Regulated data handling and requirement adherence
5. **project-docs** -- Post-implementation documentation currency

## Stale Skills Detection Protocol

Compare version headers:
- `.claude/skills/project-guardian/SKILL.md` --> `prd_version: X.Y`
- `docs/prd/PRD.md` --> `Version: X.Y`

If versions differ: Warn user to run `/prd-evolve` to sync. Do not block -- alert and allow user discretion. Flag if discrepancy appears material to current task.

## Hard Stops (Unconditional Triggers)

| Condition | Response |
|---|---|
| Missing `docs/prd/PRD.md` | Warn; suggest `/prd-new` |
| Missing `.claude/skills/project-guardian/SKILL.md` | Warn; project skills not generated |
| User requests feature removal without `/prd-evolve` | Remind to run `/prd-evolve` first |

## File Directory Reference

**Core PRD files:**
- `docs/prd/PRD.md` -- source of truth
- `docs/prd/ARCHITECTURE.md` -- canonical stack
- `docs/prd/ER.md` -- entity relationships

**Skill enforcement modules:**
- `.claude/skills/project-guardian/`
- `.claude/skills/project-architecture/`
- `.claude/skills/project-domain-rules/`
- `.claude/skills/project-compliance/`
- `.claude/skills/project-docs/`

**Development standards:**
- `docs/index.md`
- `backend/CLAUDE.md`
- `frontend/CLAUDE.md`
- `infrastructure/CLAUDE.md`
