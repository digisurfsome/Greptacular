---
description: "Compound Engineering — Work Executor: Implement one task at a time from the plan, run tests, mark complete"
argument-hint: <optional: specific task number to work on, otherwise picks the next unchecked task>
---

# Compound Engineering: Work Executor

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read these files before doing any work:
- `$ARTIFACTS_DIR/ce-plan.md` — the implementation plan with checkboxed tasks
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — original requirements and constraints

If either file is missing, STOP and report:
> "Cannot execute work — missing plan or context packet. Run the intake and plan stages first."

---

## Purpose

Implement exactly ONE task from the plan per iteration. Mark it complete. Run tests. Report status. This command runs inside a loop — each iteration picks up the next unchecked task.

---

## Process

### Step 1: Find the Next Task

Read `$ARTIFACTS_DIR/ce-plan.md` and find the first unchecked task:
- Look for lines matching `- [ ] **Task`
- Skip lines matching `- [x] **Task` (already completed)

If `$ARGUMENTS` specifies a task number, use that task instead of the next sequential one.

If ALL tasks are already checked, skip to Step 6 (all done).

### Step 2: Understand the Task

For the selected task, extract:
- **Title**: The task name
- **What**: What needs to be built or changed
- **Files**: Which files to create or modify
- **Tests**: How to verify the task is complete
- **Dependencies**: Which prior tasks this depends on (verify they're checked)

If a dependency task is NOT checked, STOP and report:
> "Task N depends on Task M, which is not yet complete. Completing Task M first."
Then work on the dependency instead.

### Step 3: Implement the Task

Execute the implementation. Follow these rules strictly:

**Scope Discipline**:
- Implement ONLY what the task description says
- Do NOT fix unrelated code you encounter
- Do NOT refactor adjacent code "while you're in there"
- Do NOT add features not in the plan
- If you notice something broken that's outside this task, note it but do NOT fix it

**Code Quality**:
- Match the existing codebase style exactly (indentation, naming, imports)
- Add error handling for all new code paths
- Use descriptive variable and function names
- Add comments for non-obvious logic (explain WHY, not WHAT)

**For New Files**:
- Follow the project's file naming conventions
- Add appropriate imports and exports
- Include file-level comments if the project uses them

**For Modified Files**:
- Read the existing file first to understand context
- Make minimal changes — touch only what the task requires
- Preserve existing formatting and style

### Step 4: Run Tests

After implementing, run whatever testing is available:

1. **If the project has a test runner** (jest, pytest, go test, cargo test):
   - Run the full test suite if it takes under 60 seconds
   - Run only relevant tests if the suite is slow
   - Report: pass count, fail count, and any failures

2. **If the project has linting** (eslint, ruff, clippy):
   - Run the linter on modified files
   - Fix any linting errors introduced by your changes
   - Do NOT fix pre-existing linting errors in untouched code

3. **If the project has type checking** (typescript, mypy, pyright):
   - Run the type checker
   - Fix any type errors introduced by your changes

4. **If no testing infrastructure exists**:
   - Verify the code compiles/parses without errors
   - Check for obvious runtime errors by reading the code path
   - Report: "No test infrastructure — verified via manual code review"

### Step 5: Mark Task Complete

Update `$ARTIFACTS_DIR/ce-plan.md`:
- Change `- [ ] **Task N:` to `- [x] **Task N:`
- Do NOT modify any other part of the plan

Report what was done:

```
## Task N Complete: [Title]

**What was done**: [1-2 sentences]
**Files changed**: [list]
**Test results**: [pass/fail summary]
**Notes**: [any issues encountered, or "none"]
**Remaining tasks**: [count of unchecked tasks]
```

### Step 6: Check if All Done

Count remaining unchecked tasks (`- [ ]` lines) in the plan.

- If unchecked tasks remain: Report the next task title and what it involves. The loop will continue.
- If ALL tasks are checked: Report completion and emit:

<promise>ALL_TASKS_COMPLETE</promise>

---

## Error Handling

**If a task is unclear or ambiguous**:
- Make a reasonable interpretation based on the context packet
- Document your interpretation in the task completion report
- Do NOT skip the task

**If a task requires a dependency that doesn't exist**:
- Install the dependency if it's listed in the plan's "Dependencies to Install" section
- If it's NOT listed, note it as a gap and install it anyway if it's clearly needed
- Add a note about the unlisted dependency

**If tests fail after your changes**:
- Investigate whether YOUR changes caused the failure
- If yes: fix the issue before marking the task complete
- If no (pre-existing failure): note it in the report but still mark the task complete

**If you cannot complete a task**:
- Do NOT mark it complete
- Report exactly what went wrong and what you tried
- The loop will present this to the user (if interactive) or retry (if autonomous)
