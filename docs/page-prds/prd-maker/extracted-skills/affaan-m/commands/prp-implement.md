# PRP Implement - Plan Execution with Continuous Validation

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/prp-implement.md

## Overview

"Execute a plan file step-by-step with continuous validation. Every change is verified immediately -- never accumulate broken state."

The core philosophy emphasizes catching mistakes early through validation loops after each change.

## Phase Structure

### Phase 0 - DETECT

Identifies the project's package manager and available validation scripts by checking for specific lock files:

- `bun.lockb`
- `pnpm-lock.yaml`
- `yarn.lock`
- `package-lock.json`

Or configuration files:

- `pyproject.toml`
- `requirements.txt`
- `Cargo.toml`
- `go.mod`

Available commands to check: type-check, lint, test, and build.

### Phase 1 - LOAD

Reads the plan file and extracts:

- Summary (what's being built)
- Patterns to Mirror (code conventions)
- Files to Change (creation/modification targets)
- Step-by-Step Tasks (implementation sequence)
- Validation Commands (verification methods)
- Acceptance Criteria (definition of done)

### Phase 2 - PREPARE

Manages git state through branch detection and decision logic:

- Creates feature branches when needed (`feat/{plan-name}`)
- Stops if working tree is dirty on main
- Syncs remote changes

### Phase 3 - EXECUTE

Processes tasks sequentially with a per-task loop:

1. Read MIRROR reference
2. Implement following patterns
3. Validate immediately after each file change
4. Track progress

"If implementation must deviate from the plan: Note WHAT changed, Note WHY it changed."

### Phase 4 - VALIDATE

Five validation levels in sequence:

1. **Static Analysis** (type-checking, linting)
2. **Unit Tests** (minimum one per function)
3. **Build Check** (zero-error requirement)
4. **Integration Testing** (server startup and health checks)
5. **Edge Case Testing** (from plan specifications)

### Phase 5 - REPORT

Creates implementation report at `.claude/PRPs/reports/{plan-name}-report.md` documenting:

- Summary
- Assessment metrics
- Completed tasks
- Validation results
- Files changed
- Deviations
- Issues
- Tests written
- Next steps

### Phase 6 - OUTPUT

Reports completion status with:

- Validation summary
- Files changed count
- Deviations summary
- Available artifacts including archived plan location

## Golden Rules

"If a validation fails, fix it before moving on. Never accumulate broken state."

Type/lint/test failures require immediate fixes before progression.
