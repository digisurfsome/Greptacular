---
description: "Compound Engineering — Correctness Review: Focused logic and error handling audit of codebase changes"
argument-hint: <optional: specific files or directories to focus on>
---

# Compound Engineering: Correctness Review

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read these files before reviewing:
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — to understand what was built and the requirements
- `$ARTIFACTS_DIR/ce-plan.md` — to understand what was implemented and the acceptance criteria

---

## Purpose

Perform a focused correctness audit of the code produced during the work phase. You are a logic and correctness specialist — you check ONLY for bugs, logic errors, and missing error handling. Do not comment on security, performance, or code style unless it directly causes incorrect behavior.

---

## Scope

Review ALL code that was created or modified during the work phase. To find what changed:

1. Check `git diff` if in a git repository
2. If no git history, read the files listed in the plan's task "Files" entries
3. If `$ARGUMENTS` specifies files, focus on those

Also read the context packet's requirements to verify that what was built matches what was asked for.

---

## Correctness Checklist

Check EVERY item below. For each finding, rate it HIGH / MEDIUM / LOW.

### Logic Errors

- [ ] **Off-by-one errors**: Are loop bounds correct? Are array indexes within range? Are pagination offsets right?
- [ ] **Incorrect conditionals**: Are if/else branches handling the right cases? Are boolean conditions correct (AND vs OR, negation)?
- [ ] **Wrong comparisons**: Are equality checks using the right operator (== vs === in JS)? Are null/undefined checks correct?
- [ ] **State management bugs**: Is state updated in the right order? Are race conditions possible between state updates?
- [ ] **Incorrect data transformations**: Are map/filter/reduce operations producing the expected output? Are type conversions correct?

### Edge Cases

- [ ] **Empty inputs**: What happens when arrays are empty, strings are blank, or numbers are zero?
- [ ] **Null/undefined handling**: Are nullable values checked before access? Can any code path produce an unexpected null?
- [ ] **Boundary values**: What happens at min/max values? Integer overflow? Very long strings?
- [ ] **Concurrent access**: If multiple users can modify the same data, are there race conditions?
- [ ] **First/last element**: Does the code handle the first item, last item, and single-item cases correctly?

### Error Handling

- [ ] **Uncaught exceptions**: Are all async operations wrapped in try/catch? Are promises properly handled (no unhandled rejections)?
- [ ] **Missing error paths**: Does every function that can fail have an error handling path? Are errors propagated correctly?
- [ ] **Error swallowing**: Are any catch blocks empty or just logging without handling? Does the caller know something failed?
- [ ] **Graceful degradation**: When an external service fails, does the app crash or degrade gracefully?
- [ ] **Validation errors**: Are invalid inputs caught at the boundary and reported clearly to the user?

### Business Logic

- [ ] **Requirements match**: Does the implementation match every must-have requirement from the context packet?
- [ ] **Missing features**: Are any required features only partially implemented or entirely missing?
- [ ] **Wrong behavior**: Does any feature do something different from what was specified?
- [ ] **Data integrity**: Are database writes consistent? Can partial failures leave data in an inconsistent state?
- [ ] **User-facing messages**: Are error messages, labels, and notifications correct and helpful?

### Type Safety

- [ ] **Type mismatches**: Are function arguments the expected types? Are return types correct?
- [ ] **Implicit coercion**: Are there any implicit type coercions that could produce unexpected results?
- [ ] **Generic type issues**: Are generic types properly constrained? Can any accept unexpected types?
- [ ] **Interface compliance**: Do objects match their declared interfaces/types?

---

## Output Format

Write findings to `$ARTIFACTS_DIR/review-correctness.md`:

```markdown
# Correctness Review

**Reviewed**: [ISO 8601 timestamp]
**Files reviewed**: [count]
**Requirements checked**: [count matched / total]
**Findings**: [count by severity]

## HIGH Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [specific description of the bug or logic error]
- **Impact**: [what goes wrong — data corruption, crash, wrong result, etc.]
- **Reproduction**: [how to trigger this bug]
- **Fix**: [specific code change to fix it]

## MEDIUM Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Impact**: [what goes wrong]
- **Fix**: [recommended fix]

## LOW Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Fix**: [recommended fix]

## Requirements Verification

| Requirement | Status | Notes |
|-------------|--------|-------|
| [requirement from context packet] | PASS / FAIL / PARTIAL | [details] |

## Clean Areas
[List correctness areas that were checked and found to be properly handled.]
```

**Rules for findings**:
- Include reproduction steps for every HIGH finding — how do you trigger the bug?
- For logic errors, explain what the code DOES vs what it SHOULD do
- For missing error handling, explain what exception can occur and what happens when it does
- Cross-reference against the context packet requirements — every must-have should appear in the Requirements Verification table
- Do NOT report security issues, performance issues, or style concerns. Those are other reviewers' jobs.

---

## Signal Completion

After writing the review file, emit:
<promise>CORRECTNESS_REVIEW_COMPLETE</promise>

If you could not access the codebase or find any changed files, write a review file noting this and still emit the promise.
