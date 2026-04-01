# Feedback Loop Design Guide

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/feedback-loop-guide.md

## Purpose

Guide for creating feedback loops in implementation specs, enabling validation during development through playgrounds, experiments, and check commands.

## Component-Type Mapping

| Component Type | Feedback Mechanism | Check Command |
|---|---|---|
| Data/logic layers | Test files with describe blocks | `pnpm test -- --filter {module}` |
| UI components | Dev server or Storybook | Start before building; validate after changes |
| API endpoints | curl/httpie scripts or test harnesses | Execute after adding routes |
| CLI tools | The tool itself with test inputs | Validate subcommands as built |
| Config/types/constants | Skip -- typecheck suffices | N/A |

## Three Essential Design Questions

### 1. Playground Identification

What environment enables agent interaction? Options:
- Test suites
- Dev servers
- Storybook
- Script harnesses
- The tool itself

The playground should be set up BEFORE writing implementation code.

### 2. Experiment Design

Create parameterized, reproducible checks using specific values. Examples:
- Empty state
- Single item
- Many items
- Error paths with concrete numbers

Avoid vague criteria.

### 3. Fastest Check Command

Prioritize scoped, text-based commands executable in seconds. The inner-loop command should run in seconds, not minutes.

## When to Skip

Skip feedback loops for:
- Type definitions
- Config changes
- Constants
- Simple re-exports
- Migrations verified elsewhere

## Infrastructure Mapping

Prefer existing tools:
- Test runners for data layers
- Dev servers for UI
- Storybook for isolated components
- API testing tools for endpoints
- Makefiles for CLI tools
