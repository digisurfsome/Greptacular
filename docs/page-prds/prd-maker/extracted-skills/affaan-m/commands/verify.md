# Verification Command

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/verify.md

## Overview

A standardized verification workflow with conditional stopping points and multiple scope options for different development stages.

## Execution Order (5 Phases)

1. **Build Check** - Execute build command; stop if failed
2. **Type Check** - Run TypeScript checker; report errors with file:line
3. **Lint Check** - Execute linter; report warnings and errors
4. **Test Suite** - Run all tests; report pass/fail count and coverage %
5. **Console.log Audit** - Search source files for console.log statements

## Additional Checks

**Git Status** - Display uncommitted changes and files modified since last commit

## Output Format

Standard report template:

```
VERIFICATION: PASS/FAIL
Build:        OK/FAIL
Types:        OK/X errors
Lint:         OK/X issues
Tests:        X/Y passed, Z% coverage
Secrets:      OK/X found
Console logs: OK/X console.logs
PR Ready:     YES/NO
```

## Arguments

Four execution modes supported:

| Mode | Description |
|------|-------------|
| `quick` | Only build + types |
| `full` | All checks (default) |
| `pre-commit` | Checks relevant for commits |
| `pre-pr` | Full checks plus security scan |
