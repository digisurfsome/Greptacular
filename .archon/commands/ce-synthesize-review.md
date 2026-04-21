---
description: "Compound Engineering — Synthesize Reviews: Merge security, correctness, and performance findings into a prioritized action list"
argument-hint: <optional: additional context or priorities to weight>
---

# Compound Engineering: Review Synthesis

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read ALL three review files:
- `$ARTIFACTS_DIR/review-security.md`
- `$ARTIFACTS_DIR/review-correctness.md`
- `$ARTIFACTS_DIR/review-performance.md`

Also read:
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — for requirements and constraints

If any review file is missing, proceed with the reviews that exist. Note which reviews are missing in your output.

---

## Purpose

Merge findings from all three specialized reviews into a single, deduplicated, prioritized action list. The fix loop will use this document as its task list — so it must be clear, actionable, and ordered.

---

## Process

### Step 1: Collect All Findings

Read each review file and extract all findings into a unified list. For each finding, record:
- Original source (security / correctness / performance)
- Severity (HIGH / MEDIUM / LOW)
- File and line
- Issue description
- Recommended fix

### Step 2: Deduplicate

Look for findings that describe the SAME underlying issue from different angles. Common overlaps:

- Security's "unvalidated input" and Correctness's "missing type check" on the same field → merge into one finding
- Performance's "N+1 query" and Correctness's "slow response" for the same endpoint → merge, keep the more actionable description
- Security's "error leaks internal details" and Correctness's "error not handled" → merge under the higher severity

**Dedup rules**:
- If two findings reference the same file:line, they're likely the same issue
- If two findings describe the same root cause with different symptoms, merge them
- When merging, keep the HIGHER severity rating
- Note all source reviews in the merged finding (e.g., "Source: security + correctness")

### Step 3: Prioritize

Sort all findings into a strict priority order:

1. **HIGH security findings** — these block release. Fix first.
2. **HIGH correctness findings** — bugs that produce wrong results or crashes.
3. **HIGH performance findings** — issues that make the app unusable at target scale.
4. **MEDIUM security findings** — exploitable but with limited impact.
5. **MEDIUM correctness findings** — edge cases and partial failures.
6. **MEDIUM performance findings** — noticeable but not blocking.
7. **LOW findings** — all severities grouped together at the end.

Within each priority tier, order by estimated fix effort (quickest fixes first).

### Step 4: Add Fix Recommendations

For each HIGH finding, expand the fix recommendation into specific, actionable instructions:

- Exact file(s) to modify
- What code to change (specific enough that a developer can act on it without re-analyzing)
- What tests to run after the fix
- Estimated effort (quick fix / moderate / significant refactor)

For MEDIUM and LOW findings, the original fix recommendation from the review is sufficient.

### Step 5: Identify Cross-Cutting Concerns

Look for patterns across findings that suggest a systemic issue:

- Multiple findings about missing input validation → "Systemic: No input validation layer"
- Multiple N+1 queries → "Systemic: ORM used without eager loading"
- Multiple auth bypass findings → "Systemic: Auth middleware not applied consistently"

If systemic issues exist, add them as a separate section. These are often more impactful to fix than individual findings because one fix addresses multiple issues.

---

## Output Format

Write to `$ARTIFACTS_DIR/ce-review-synthesis.md`:

```markdown
# Review Synthesis

**Generated**: [ISO 8601 timestamp]
**Reviews merged**: [list which reviews were available]
**Total findings**: [count] ([count] HIGH, [count] MEDIUM, [count] LOW)
**Deduplicated from**: [original total across all reviews]

## Systemic Issues
[Only if patterns were found across multiple findings]

### [Systemic Issue Title]
- **Pattern**: [what keeps appearing]
- **Affected files**: [list]
- **Root fix**: [one change that addresses multiple findings]
- **Findings resolved**: [list finding numbers this would fix]

## HIGH Priority Findings

### Finding 1: [Title]
- **Source**: [security / correctness / performance / merged]
- **File**: [path:line]
- **Issue**: [clear description]
- **Impact**: [what goes wrong]
- **Fix**: [detailed, actionable fix instructions]
- **Test after fix**: [what to verify]
- **Effort**: [quick / moderate / significant]
- **Status**: [ ] Not started

### Finding 2: [Title]
...

## MEDIUM Priority Findings

### Finding N: [Title]
- **Source**: [review source]
- **File**: [path:line]
- **Issue**: [description]
- **Fix**: [recommended fix]
- **Status**: [ ] Not started

## LOW Priority Findings

### Finding N: [Title]
- **Source**: [review source]
- **File**: [path:line]
- **Issue**: [description]
- **Fix**: [recommended fix]
- **Status**: [ ] Not started

## Clean Summary
[Consolidated list of areas that all reviews found to be properly handled.]
```

**Rules**:
- Every finding MUST have a `Status: [ ] Not started` line — the fix loop uses this to track progress
- HIGH findings MUST have detailed fix instructions — not just "fix this"
- Preserve enough context that a developer reading ONLY this document can understand and fix each issue
- If there are zero HIGH findings, explicitly state: "No HIGH priority findings. The fix loop will focus on MEDIUM findings instead."

---

## Signal Completion

After writing the synthesis file, emit:
<promise>SYNTHESIS_COMPLETE</promise>

If no review files were found, write a synthesis noting this and still emit the promise.
