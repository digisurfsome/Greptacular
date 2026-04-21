---
description: "Compound Engineering — Performance Review: Focused performance and efficiency audit of codebase changes"
argument-hint: <optional: specific files or directories to focus on>
---

# Compound Engineering: Performance Review

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read these files before reviewing:
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — to understand the tech stack and scale expectations
- `$ARTIFACTS_DIR/ce-plan.md` — to understand what was implemented

---

## Purpose

Perform a focused performance audit of the code produced during the work phase. You are a performance specialist — you check ONLY for performance issues, unnecessary computation, and scalability problems. Do not comment on security, correctness (unless it causes perf issues), or code style.

---

## Scope

Review ALL code that was created or modified during the work phase. To find what changed:

1. Check `git diff` if in a git repository
2. If no git history, read the files listed in the plan's task "Files" entries
3. If `$ARGUMENTS` specifies files, focus on those

Check the context packet for `target_scale` — adjust severity ratings based on whether this is a personal project vs a public-facing product.

---

## Performance Checklist

Check EVERY item below. For each finding, rate it HIGH / MEDIUM / LOW. Scale matters: an N+1 query is LOW for a personal tool but HIGH for a public API.

### Database & Queries

- [ ] **N+1 queries**: Are there loops that make individual DB queries per item instead of batch queries?
- [ ] **Missing indexes**: Are columns used in WHERE, JOIN, or ORDER BY clauses indexed?
- [ ] **Over-fetching**: Are queries selecting all columns (`SELECT *`) when only a few are needed?
- [ ] **Missing pagination**: Can any endpoint return unbounded result sets? Are lists paginated?
- [ ] **Unnecessary joins**: Are there JOIN operations that could be avoided with denormalization or caching?
- [ ] **Transaction scope**: Are transactions held open longer than necessary?

### API & Network

- [ ] **Large payloads**: Are API responses sending more data than the client needs?
- [ ] **Missing compression**: Are large responses compressed (gzip/brotli)?
- [ ] **Chatty APIs**: Does the client need multiple round-trips to get data that could be fetched in one call?
- [ ] **Missing caching headers**: Are static or rarely-changing responses cacheable?
- [ ] **Synchronous blocking**: Are there synchronous operations that block the event loop?

### Frontend (if applicable)

- [ ] **Unnecessary re-renders**: Are React components re-rendering when their props haven't changed?
- [ ] **Large bundle size**: Are heavy libraries imported when lighter alternatives exist?
- [ ] **Missing lazy loading**: Are large components or routes loaded eagerly when they could be lazy-loaded?
- [ ] **Unoptimized images**: Are images served at appropriate sizes?
- [ ] **Memory leaks**: Are event listeners cleaned up? Are intervals/timeouts cleared?

### Algorithms & Data Structures

- [ ] **Unnecessary O(n^2)**: Are there nested loops that could be replaced with hash maps or sets?
- [ ] **Redundant computation**: Is the same value computed multiple times when it could be computed once?
- [ ] **Inefficient data structures**: Is a linear search used where a hash lookup would work?
- [ ] **Large object copies**: Are large objects or arrays being deep-copied unnecessarily?

### Concurrency & Resources

- [ ] **Connection pool exhaustion**: Are DB connections pooled and properly released?
- [ ] **File handle leaks**: Are files, streams, and connections closed after use?
- [ ] **Unbounded queues**: Can any queue or buffer grow without limit?
- [ ] **Missing rate limiting**: Can any endpoint be called at unlimited frequency?

---

## Output Format

Write findings to `$ARTIFACTS_DIR/review-performance.md`:

```markdown
# Performance Review

**Reviewed**: [ISO 8601 timestamp]
**Files reviewed**: [count]
**Target scale**: [from context packet: personal / team / public]
**Findings**: [count by severity]

## HIGH Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [specific description of the performance problem]
- **Impact**: [quantified if possible — e.g., "1 query per item = 100 queries for 100 items"]
- **Fix**: [specific optimization with code snippet if helpful]

## MEDIUM Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Impact**: [expected impact]
- **Fix**: [recommended optimization]

## LOW Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Fix**: [recommended optimization]

## Clean Areas
[List performance areas that were checked and found to be properly handled.]
```

**Rules for findings**:
- Quantify impact when possible. "Slow" is vague. "N+1 query producing 50 DB calls per page load" is specific.
- Always provide a concrete fix, not just "optimize this."
- Adjust severity based on `target_scale` from context packet.
- Do NOT report security issues, correctness bugs, or style concerns.
- Do NOT suggest premature optimizations for code that is already fast enough for its scale.

---

## Signal Completion

After writing the review file, emit:
<promise>PERFORMANCE_REVIEW_COMPLETE</promise>

If you could not access the codebase or find any changed files, write a review file noting this and still emit the promise.
