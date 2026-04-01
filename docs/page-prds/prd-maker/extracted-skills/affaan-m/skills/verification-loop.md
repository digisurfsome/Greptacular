# Verification Loop Skill

**Name**: verification-loop
**Description**: A comprehensive verification system for Claude Code sessions.
**Origin**: ECC

## When to Use

- After completing a feature or significant code change
- Before creating a PR
- When ensuring quality gates pass
- After refactoring

## Verification Phases (6 Total)

### Phase 1: Build Verification

Commands:
- npm: `npm run build 2>&1 | tail -20`
- pnpm: `pnpm build 2>&1 | tail -20`

**Rule:** Stop and fix if build fails.

### Phase 2: Type Check

- TypeScript: `npx tsc --noEmit 2>&1 | head -30`
- Python: `pyright . 2>&1 | head -30`

Report all type errors; fix critical ones before continuing.

### Phase 3: Lint Check

- JavaScript/TypeScript: `npm run lint 2>&1 | head -30`
- Python: `ruff check . 2>&1 | head -30`

### Phase 4: Test Suite

Command: `npm run test -- --coverage 2>&1 | tail -50`

**Target:** 80% minimum coverage.

Report: total tests, passed count, failed count, coverage percentage.

### Phase 5: Security Scan

- Check for secrets: `grep -rn "sk-" --include="*.ts" --include="*.js" .`
- Check for API keys: `grep -rn "api_key" --include="*.ts" --include="*.js" .`
- Check for debug statements: `grep -rn "console.log" --include="*.ts" --include="*.tsx" src/`

### Phase 6: Diff Review

Commands: `git diff --stat` and `git diff HEAD~1 --name-only`

Review criteria: unintended changes, missing error handling, potential edge cases.

## Output Format

Structured report showing: Build, Types, Lint, Tests, Security, Diff statuses with overall PR readiness determination and issues list.

## Continuous Mode

Run verification every 15 minutes or after major changes; set checkpoints after each function/component completion.

## Integration Note

Complements PostToolUse hooks; hooks catch immediate issues while this skill provides comprehensive review.
