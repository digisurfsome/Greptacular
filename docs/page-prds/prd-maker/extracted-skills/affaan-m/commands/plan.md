# Plan Command

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/plan.md

## Overview

A planning command that creates step-by-step implementation plans and WAITS for user confirmation before touching any code.

## Core Principle

**"WAIT for user CONFIRM before touching any code"**

**Critical Rule**: "The planner agent will **NOT** write any code until you explicitly confirm"

## What This Command Does

1. Restate Requirements
2. Identify Risks
3. Create Step Plan
4. Wait for Confirmation

## When to Use `/plan`

- Starting new features
- Making significant architectural changes
- Working on complex refactoring
- Multiple files/components affected
- Unclear or ambiguous requirements

## How It Works

### Planner Agent Workflow

1. Analyze request and restate requirements
2. Break down into phases with actionable steps
3. Identify dependencies
4. Assess risks and blockers
5. Estimate complexity
6. Present plan and WAIT for confirmation

### Confirmation Responses

- **Affirmative**: "yes/proceed/similar"
- **Modifications**: "modify: [changes]"
- **Alternative**: "different approach: [alternative]"
- **Sequencing**: "skip phase 2 and do phase 3 first"

## Example Usage

Example phases for a real-time notifications implementation:

- Phase 1: Database Schema
- Phase 2: Notification Service
- Phase 3: Integration Points
- Phase 4: Frontend Components

## Important Notes

The planner agent will NOT write any code until you explicitly confirm. You can modify, reorder, or reject any phase.

## Integration with Other Commands

- `/prp-plan` - Artifact-producing planning (more comprehensive)
- `/prp-implement` - Plan execution

## Related Agents

- `/tdd` - Test-driven development
- `/build-fix` - Build errors
- `/code-review` - Implementation review
