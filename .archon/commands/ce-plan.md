---
description: "Compound Engineering — Plan: Create a detailed, task-by-task implementation plan from the context packet"
argument-hint: <optional overrides or priorities — otherwise reads context packet automatically>
---

# Compound Engineering: Implementation Plan

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read `$ARTIFACTS_DIR/context-packet/context-packet.json`. This file was written by the intake stage and contains all requirements, tech stack, and constraints.

If the file does not exist or is malformed, STOP and report:
> "Cannot create a plan — context packet is missing or corrupted. The intake stage must run first."

---

## Purpose

Transform the context packet into a concrete, ordered, checkboxed implementation plan. Each task must be atomic, testable, and sequenced so that earlier tasks do not depend on later ones.

---

## Process

### Step 1: Analyze the Context Packet

Read the context packet and identify the mode:

- **pre-build**: No existing code. Plan includes project setup, scaffolding, and all features.
- **existing-code**: Existing code. Plan focuses on improvements, refactoring, and fixes.
- **add-feature**: Existing code + new feature. Plan includes integration tasks alongside feature implementation.

Extract:
- All requirements (must-have first, nice-to-have second)
- Tech stack decisions
- Constraints and do-not-touch areas
- Integration points and risks (if applicable)

### Step 2: Determine Architecture (Pre-Build Only)

If mode is `pre-build`, make and document architecture decisions:

```
## Architecture Decisions

**Project Structure**: [monorepo / separate frontend+backend / single app]
**Directory Layout**: [describe folder structure]
**State Management**: [approach for frontend state]
**API Pattern**: [REST / GraphQL / tRPC / none]
**Database Strategy**: [ORM choice, migration approach]
**Auth Approach**: [session / JWT / OAuth / none]
```

Keep decisions practical. Choose boring, well-supported technology over cutting-edge. Match the tech stack from the context packet.

### Step 3: Create the Do-Not-Break List (Existing Code Only)

If mode is `existing-code` or `add-feature`, create a preservation list:

```
## Do Not Break

These existing behaviors MUST continue working after implementation:
1. [existing behavior to preserve]
2. [existing behavior to preserve]
...

Files to NOT modify (per user request):
- [path]
- [path]
```

### Step 4: Build the Task List

Create a numbered, checkboxed task list. Follow these rules:

**Task Granularity**:
- Each task should take 5-30 minutes for a capable developer
- If a task would take longer, split it into subtasks
- Each task must be independently verifiable (you can check if it works without completing the next task)

**Task Ordering**:
- Infrastructure and setup tasks first (dependencies, config, scaffolding)
- Core data models and types second
- Backend logic third
- Frontend/UI fourth
- Integration and wiring fifth
- Tests sixth (or alongside each task if TDD)
- Polish and edge cases last

**Task Format**:
```
- [ ] **Task N: [Short Title]**
  - What: [1-2 sentences describing exactly what to build]
  - Files: [list of files to create or modify]
  - Tests: [what to verify after completing this task]
  - Dependencies: [which prior tasks must be done first, if any]
```

**Task Quality Rules**:
- Every task MUST have a "Tests" line — even if it's just "run the app and verify no errors"
- Every task MUST list specific files, not vague areas
- No task should say "implement the feature" — that's too vague, break it down
- Group related tasks with section headers if the plan exceeds 10 tasks

### Step 5: Add Dependencies to Install

If any tasks require installing new packages, create a separate section:

```
## Dependencies to Install

**Before starting implementation:**
- `npm install [package]` — [why]
- `pip install [package]` — [why]
```

### Step 6: Write the Plan

Write the complete plan to `$ARTIFACTS_DIR/ce-plan.md` with this structure:

```markdown
# Implementation Plan

**Mode**: [pre-build | existing-code | add-feature]
**Generated**: [ISO 8601 timestamp]
**Source**: context-packet.json

## Summary
[2-3 sentence overview of what will be built/changed]

## Architecture Decisions
[only for pre-build mode]

## Do Not Break
[only for existing-code and add-feature modes]

## Dependencies to Install
[if any]

## Tasks

### Phase 1: Setup and Infrastructure
- [ ] **Task 1: ...**
  ...

### Phase 2: Core Implementation
- [ ] **Task N: ...**
  ...

### Phase 3: Integration and Testing
- [ ] **Task N: ...**
  ...

### Phase 4: Polish and Edge Cases
- [ ] **Task N: ...**
  ...

## Verification Checklist
After all tasks are complete, verify:
- [ ] All must-have requirements from context packet are implemented
- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors
- [ ] Do-not-break items still work (if applicable)
```

### Step 7: Validate and Signal

Validate the plan:
1. Every must-have requirement from the context packet has at least one task covering it
2. Every task has: title, what, files, tests
3. Tasks are in a logical sequence (no circular dependencies)
4. Total task count is between 3 and 50 (if more than 50, you over-split; if fewer than 3, you under-split)

If validation passes, emit:
<promise>PLAN_COMPLETE</promise>

If validation reveals gaps (requirements with no tasks), add tasks to cover them before emitting.
