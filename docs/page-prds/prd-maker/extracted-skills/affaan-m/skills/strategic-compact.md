# Strategic Compact Skill

**Name**: strategic-compact
**Description**: Strategic context compaction for long Claude Code sessions.
**Origin**: ECC

## When to Activate

- Sessions approaching 200K+ tokens
- Multi-phase workflows (research -> plan -> implement -> test)
- Switching between unrelated tasks
- After major milestones
- When responses degrade

## Why Strategic Compaction?

Strategic compaction principles:
- "Compact research context, keep implementation plan" (after exploration)
- "Fresh start for next phase" (after milestones)
- "Clear exploration context before different task" (pre-shift)

## Hook Setup

Location: `~/.claude/settings.json`

Environment variable: `COMPACT_THRESHOLD` (default: 50 tool calls before first suggestion)

Hook targets: PreToolUse (Edit/Write matchers)

## Compaction Decision Guide

| Transition | Action | Rationale |
|-----------|--------|-----------|
| Research -> Planning | Compact | Reduces bulky research, preserves distilled plan |
| Planning -> Implementation | Compact | Plan stored; frees context for code |
| Debugging -> Next feature | Compact | Debug traces interfere with new work |
| Mid-implementation | Skip | Loses critical variable names and state |
| After failed approach | Compact | Clears dead-end reasoning |

## What Survives Compaction

**Persists:** CLAUDE.md instructions, TodoWrite tasks, memory files, Git state, disk files.

**Lost:** Intermediate reasoning, previously-read file contents, conversation context, tool histories.

## Best Practices

1. Compact after planning finalization
2. Compact post-debugging
3. Preserve mid-implementation context
4. Use hook suggestions as guidance
5. Write before compacting
6. Include summary with `/compact` command

## Token Optimization Patterns

- **Trigger-Table Lazy Loading**: Skills load conditionally
- **Context Composition Awareness**: Monitor consumption
- **Duplicate Instruction Detection**: Avoid redundant context
- **Context Optimization Tools**: token-optimizer MCP, context-mode
