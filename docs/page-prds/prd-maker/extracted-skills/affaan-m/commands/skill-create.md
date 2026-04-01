# Skill Create - Local Skill Generation

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/skill-create.md

## Front Matter

```yaml
name: skill-create
description: Analyze local git history to extract coding patterns and generate SKILL.md files. Local version of the Skill Creator GitHub App.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
```

## Overview

"Analyze your repository's git history to extract coding patterns and generate SKILL.md files that teach Claude your team's practices."

## Usage Commands

- `/skill-create` - Analyze current repo
- `/skill-create --commits 100` - Analyze last 100 commits
- `/skill-create --output ./skills` - Custom output directory
- `/skill-create --instincts` - Generate instincts for continuous-learning-v2

## Four-Step Process

### Step 1: Gather Git Data

Three bash commands extract:

- Commits (via `git log`)
- File frequencies
- Message patterns

### Step 2: Detect Patterns

| Pattern | What's Detected |
|---------|----------------|
| Commit conventions | Commit message formats |
| File co-changes | Files that change together |
| Workflow sequences | Common workflow patterns |
| Architecture | Architectural patterns |
| Testing patterns | Testing frameworks and approaches |

### Step 3: Generate SKILL.md

Output template includes frontmatter:

```yaml
name: <project-name>
description: <detected description>
version: 1.0
source: git-history
analyzed_commits: <count>
```

And sections for:

- Conventions
- Architecture
- Workflows
- Testing

### Step 4: Generate Instincts

YAML format with fields:

- `id` - Unique identifier
- `trigger` - When to activate
- `confidence` - 0.8 default
- `domain` - Applicable domain
- `source` - Origin reference

For continuous-learning-v2.

## Example Output

Demonstrates a TypeScript project output with:

- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- Folder structure conventions
- Component workflows
- Testing frameworks (Vitest with 80%+ coverage targets)

## GitHub App Integration

Links to external Skill Creator GitHub App for "10k+ commits, team sharing, auto-PRs."

## Related Commands

- `/instinct-import` - Import generated instincts
- `/instinct-status` - View learned instincts
- `/evolve` - Cluster instincts into skills/agents

## Attribution

"Part of [Everything Claude Code](https://github.com/affaan-m/everything-claude-code)"
