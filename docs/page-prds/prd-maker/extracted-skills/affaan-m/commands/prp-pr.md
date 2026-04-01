# PRP PR - Create Pull Request Workflow

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/prp-pr.md

## Overview

Automates GitHub PR creation from feature branches with unpushed commits. Discovers templates, analyzes changes, and handles the complete PR lifecycle.

## Core Parameters

- **Input**: `$ARGUMENTS` (optional base branch name and/or flags like `--draft`)
- **Default base branch**: `main`
- **Recognized flags**: `--draft`

## Phase 1: VALIDATE

**Precondition checks:**

| Check | Requirement | Failure Action |
|-------|-------------|----------------|
| Not on base | Current branch must differ from base | "Switch to a feature branch first." |
| Clean workspace | No uncommitted changes | "Commit or stash first. Use `/prp-commit`." |
| Commits ahead | Non-empty `git log origin/<base>..HEAD` | "No commits ahead -- nothing to PR." |
| No existing PR | `gh pr list --head <branch>` empty | "PR already exists: #<number>" |

**Validation commands:**

```bash
git branch --show-current
git status --short
git log origin/<base>..HEAD --oneline
gh pr list --head <branch> --json number
```

## Phase 2: DISCOVER

**Template search order:**

1. `.github/PULL_REQUEST_TEMPLATE/` (user selects or uses `default.md`)
2. `.github/PULL_REQUEST_TEMPLATE.md`
3. `.github/pull_request_template.md`
4. `docs/pull_request_template.md`

**Commit analysis:**

- Extract conventional commit types (`feat`, `fix`, etc.)
- Use dominant type for title if multiple commits
- Command: `git log origin/<base>..HEAD --format="%h %s" --reverse`

**File categorization:**

- Analyze: source, tests, docs, config, migrations
- Command: `git diff origin/<base>..HEAD --stat` and `--name-only`

**PRP artifact references:**

- `.claude/PRPs/reports/` (implementation reports)
- `.claude/PRPs/plans/` (executed plans)
- `.claude/PRPs/prds/` (related product requirements)

## Phase 3: PUSH

```bash
git push -u origin HEAD
```

**On divergence:**

```bash
git fetch origin
git rebase origin/<base>
git push -u origin HEAD
```

Stop if rebase conflicts occur.

## Phase 4: CREATE

**Template-based PR:** Fill sections from analysis; preserve all template sections (use "N/A" if inapplicable).

**Default format (no template):**

```markdown
## Summary
<1-2 sentence description>

## Changes
<bulleted grouped changes>

## Files Changed
<table/list with Added/Modified/Deleted>

## Testing
<test description or "Needs testing">

## Related Issues
<linked issues or "None">
```

**Command:**

```bash
gh pr create \
  --title "<PR title>" \
  --base <base-branch> \
  --body "<PR body>"
```

Add `--draft` if flag was parsed.

## Phase 5: VERIFY

```bash
gh pr view --json number,url,title,state,baseRefName,headRefName,additions,deletions,changedFiles
gh pr checks --json name,status,conclusion 2>/dev/null || true
```

## Phase 6: OUTPUT

Report includes:

- PR number/title
- URL
- Branch names
- Change statistics
- CI status
- Referenced artifacts
- Next-step commands

## Edge Cases

- **Missing `gh` CLI**: Direct installation link required
- **Authentication failure**: "Run `gh auth login` first."
- **Force push needed**: Use `--force-with-lease` only
- **Multiple templates**: List files and request user selection
- **Large PR (>20 files)**: Warn and suggest logical splitting
