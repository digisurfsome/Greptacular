---
description: "Compound Engineering — Compound: Document learnings from this build cycle for future runs"
argument-hint: <optional: additional reflections or notes to include>
---

# Compound Engineering: Compound Learnings

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read these files:
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — what was built and why
- `$ARTIFACTS_DIR/ce-plan.md` — the implementation plan (check which tasks completed)
- `$ARTIFACTS_DIR/ce-review-synthesis.md` — review findings and fixes

If any file is missing, work with what's available. The compound step should always produce output even with partial data.

---

## Purpose

Extract reusable learnings from this build cycle. The goal is compound improvement: each cycle should make the next cycle faster, with fewer bugs and better architecture decisions. This is the step that turns isolated builds into an improving system.

---

## Process

### Step 1: Gather Metrics

From the available files, extract:

**From context packet**:
- Mode (pre-build / existing-code / add-feature)
- Tech stack used
- App description / feature description

**From plan**:
- Total tasks planned
- Total tasks completed (count `[x]` lines)
- Total tasks incomplete (count `[ ]` lines)

**From review synthesis**:
- Total findings by severity
- Number of HIGH findings that were fixed
- Number of systemic issues identified
- Areas that were clean (no findings)

### Step 2: Identify What Went Well

Look for patterns that should be REPEATED in future cycles:

- **Architecture decisions that survived review**: If the plan's architecture choices produced zero or minimal review findings, those are good patterns.
- **Clean areas from reviews**: What security/correctness/performance areas had no findings? Those patterns are working.
- **Efficient task completion**: Were there tasks that went smoothly with no issues? What made them work?
- **Good testing practices**: Were bugs caught by tests rather than review? That's the testing strategy working.

Select the top 3 most impactful positive patterns.

### Step 3: Identify What Went Wrong

Look for patterns that should be AVOIDED in future cycles:

- **HIGH findings from review**: Each one represents a mistake in the build phase. What caused it?
- **Systemic issues**: If the synthesis identified cross-cutting problems, why weren't they caught during planning?
- **Incomplete tasks**: If any tasks were not completed, what blocked them?
- **Plan gaps**: Were there requirements from the context packet that didn't have corresponding tasks?

Select the top 3 most impactful issues.

### Step 4: Extract Reusable Patterns

For each positive pattern, write it as a rule that future cycles can follow:

```
**Pattern**: [descriptive name]
**Context**: [when this applies — tech stack, project type, etc.]
**Rule**: [specific, actionable instruction for future builds]
**Evidence**: [what happened this cycle that proves this works]
```

For each negative pattern, write it as an anti-pattern:

```
**Anti-Pattern**: [descriptive name]
**Context**: [when this risk appears]
**What went wrong**: [specific description]
**Prevention**: [what to do differently next time]
**Evidence**: [what happened this cycle]
```

### Step 5: Write the Learnings Document

Create the learnings directory if it doesn't exist: `docs/ce-learnings/`

Generate a filename based on the current date and project: `docs/ce-learnings/YYYY-MM-DD-[project-or-feature-slug].md`

Write the document:

```markdown
# Compound Engineering Learnings

**Date**: [YYYY-MM-DD]
**Project/Feature**: [name or description]
**Mode**: [pre-build / existing-code / add-feature]
**Tech Stack**: [summary]

## Build Summary

- **Tasks planned**: [count]
- **Tasks completed**: [count]
- **Review findings**: [HIGH: X, MEDIUM: Y, LOW: Z]
- **Systemic issues**: [count]

## What Went Well

### 1. [Pattern Name]
[Description of what worked and why]

### 2. [Pattern Name]
[Description]

### 3. [Pattern Name]
[Description]

## Issues Found in Review

### 1. [Issue Name]
- **Severity**: [HIGH/MEDIUM]
- **Root cause**: [why this happened]
- **Fix applied**: [what was done]
- **Prevention**: [how to avoid this next time]

### 2. [Issue Name]
...

### 3. [Issue Name]
...

## Reusable Patterns

### [Pattern Name]
- **When to use**: [context]
- **Rule**: [actionable instruction]
- **Evidence**: [from this cycle]

## Anti-Patterns to Avoid

### [Anti-Pattern Name]
- **When this appears**: [context]
- **What goes wrong**: [description]
- **Do instead**: [alternative approach]

## Notes for Future Cycles
[Any additional observations, edge cases discovered, or configuration
tips that don't fit the categories above but would help a future build.]
```

### Step 6: Validate and Signal

Validate the learnings document:
1. Has at least 1 "What Went Well" entry
2. Has at least 1 "Issues Found" entry (or explicitly states "No issues found in review — clean build")
3. Has at least 1 reusable pattern
4. Date and project name are filled in
5. Build metrics match the source files

After writing, emit:
<promise>COMPOUND_COMPLETE</promise>

---

## Note on Accumulation

If `docs/ce-learnings/` already contains prior learnings documents, do NOT modify them. Each build cycle produces its own file. Over time, the directory accumulates a knowledge base that future planning stages can reference.

If this is the first cycle, mention in the notes: "First compound engineering cycle — baseline patterns established."
