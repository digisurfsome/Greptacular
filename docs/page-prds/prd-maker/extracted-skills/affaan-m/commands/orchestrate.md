# Orchestrate Command - Multi-Agent Workflow Orchestration

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/orchestrate.md

## Overview

The `/orchestrate` command enables sequential multi-agent workflows for complex development tasks, with support for tmux/worktree orchestration across multiple sessions.

## Workflow Types & Agent Chains

| Type | Chain | Purpose |
|------|-------|---------|
| **Feature** | planner -> tdd-guide -> code-reviewer -> security-reviewer | Full feature implementation |
| **Bugfix** | planner -> tdd-guide -> code-reviewer | Investigation and resolution |
| **Refactor** | architect -> code-reviewer -> tdd-guide | Safe structural changes |
| **Security** | security-reviewer -> code-reviewer -> architect | Risk-focused review |

## Execution Process

Each agent:

1. Receives context from predecessors
2. Produces structured handoff documents
3. Passes results forward

**Handoff format includes sections for:**

- Context
- Findings
- Modified files
- Open questions
- Recommendations

## Key Phases

1. Agent invocation with prior context
2. Output collection in structured format
3. Sequential or parallel handoff to next agent
4. Results aggregation into final report

## Distributed Execution

For external workers, use:

```bash
node scripts/orchestrate-worktrees.js plan.json --execute
```

The `seedPaths` parameter overlays selected local files into isolated worker worktrees, maintaining branch isolation while exposing in-progress scripts and documentation.

## Final Reporting

Reports consolidate:

- All agent outputs
- List of modified files
- Test results
- Security findings
- Clear recommendation: **SHIP / NEEDS WORK / BLOCKED**

## Control Plane Snapshot

Run `node scripts/orchestration-status.js` to export:

- Session metadata
- Worker states
- Branch information
- Recent handoff summaries

For multi-session workflows.
