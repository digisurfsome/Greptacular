# PRP Commit - Smart Commit Workflow

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/prp-commit.md

## Overview

The Smart Commit tool enables quick commits using natural language file targeting. Users describe what to commit in plain English via the argument `$ARGUMENTS`.

## Four Phases

### Phase 1 - ASSESS

Execute `git status --short` to check for changes. Stop if empty. Display a summary of added, modified, deleted, and untracked files.

### Phase 2 - INTERPRET & STAGE

Parse the user's input to determine staging strategy:

| Input | Action |
|-------|--------|
| Blank input | Stage everything via `git add -A` |
| "staged" | Use pre-staged files only |
| Glob patterns like `*.ts` | Stage matching files |
| "except tests" | Stage all then remove test files |
| "only new files" | Stage untracked files |
| Natural language like "the auth changes" | Cross-reference `git status` and `git diff` |
| Specific filenames | Stage directly |

Verify staging with `git diff --cached --stat`. Stop if nothing matched.

### Phase 3 - COMMIT

Generate a single-line message using format `{type}: {description}`.

**Commit Types:**

| Type | Usage |
|------|-------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation changes |
| `test` | Adding or updating tests |
| `chore` | Build, config, dependencies |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |

**Message Rules:**

- Use imperative mood ("add feature" not "added feature")
- Lowercase after type prefix
- No period
- Under 72 characters
- Describe WHAT changed

### Phase 4 - OUTPUT

Report:

- Commit hash
- Message
- File count
- Next steps (push, create PR, or code review)

## Usage Examples

- `/prp-commit` -- stages all, auto-generates message
- `/prp-commit staged` -- commits pre-staged files
- `/prp-commit *.ts` -- stages TypeScript files
- `/prp-commit except tests` -- stages all except tests
- `/prp-commit the database migration` -- finds and stages migration files
- `/prp-commit only new files` -- stages untracked files
