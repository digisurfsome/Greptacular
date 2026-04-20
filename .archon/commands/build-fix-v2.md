# Fix: Synthesize Reviews and Fix Issues (v2)

Read all 4 review reports, prioritize findings, and fix every issue.

> **v2 change:** Mandatory contract enforced. Exemption language removed.
> The compliance gate script runs after you finish and counts issues vs. fixes.
> If it emits FAIL, the recovery branch activates automatically.

## Input

Read ALL review reports from `$ARTIFACTS_DIR/`:
- `review-correctness.md`
- `review-failures.md`
- `review-tests.md`
- `review-simplify.md`

Also read `verification-report.md` for Wall/Door/Room compliance issues if present.

---

### Contract (MANDATORY — NO EXCEPTIONS)

You MUST address every issue flagged in the above files.

For each issue:
- **CRITICAL or HIGH severity → fix it. No exceptions.**
- **MEDIUM or LOW → fix it**, OR list it in `$ARTIFACTS_DIR/deferred.md` with:
  (a) the specific reason it cannot be fixed in this phase, and
  (b) evidence (file path, line number) showing you attempted a fix

**Writing tests for flagged coverage gaps is part of this contract, not a separate task.**
If `review-tests.md` lists untested WALL steps, you write those tests before claiming done.

The compliance gate script (`.archon/scripts/compliance-gate.py`) runs after you finish.
It will count issues vs. fixes. If it emits FAIL, the recovery branch activates;
if recovery also fails, the pipeline halts.

---

## Process

### Step 1: Deduplicate
Multiple reviewers may flag the same issue. Merge duplicates, keep the most detailed version.

### Step 2: Prioritize
| Priority | Fix? | Criteria |
|----------|------|----------|
| Critical | YES immediately | Bugs, security, data loss |
| High | YES | Logic errors, missing error handling, WALL violations |
| Medium | YES — or deferred.md entry with reason + evidence | Pattern inconsistencies, missing edge cases |
| Low | YES — or deferred.md entry with reason + evidence | Style preferences, minor optimizations |

### Step 3: Fix Critical and High Issues
For each issue:
1. Read the file at the referenced line
2. Understand the problem
3. Apply the fix
4. Run validation (compile, lint, test) after each fix
5. If fix breaks something else: revert and try alternative approach

### Step 4: Two-Strike Rule (item-scoped, not category-scoped)
If the **same individual fix attempt** fails twice:
- Add an entry to `$ARTIFACTS_DIR/deferred.md` for that specific item with the reason
- Continue to the **next issue** — do NOT stop working
- You may NOT declare entire categories exempt (e.g., "all tests", "all async issues", "architectural issues")
- You may NOT declare a category of work "a separate task per instructions"

### Step 5: Add Missing Tests
From `review-tests.md` findings, add tests for:
- **All WALL steps that lack verification tests** (mandatory — same contract as CRITICAL/HIGH)
- Critical edge cases identified by reviewers
- Integration points between mechanisms

This step is not optional and is not a "separate task."

### Step 6: Write deferred.md (if any items deferred)
Format each deferred item as:
```
- [MEDIUM|LOW] <issue description>
  Reason: <specific reason this cannot be fixed in this phase>
  Attempted: <file path, line number, what was tried>
```

Maximum 5 deferred items total (enforced by deploy-gate.py at pipeline end).

## Output

Write fix report to `$ARTIFACTS_DIR/fix-report.md`:

```markdown
# Fix Report

## Summary
Fixed X of Y review issues. Z items deferred (see deferred.md).

## Issues Fixed
### Fix 1: <description> [SEVERITY]
<what was changed and why>

### Fix 2: <description> [SEVERITY]
...

## Validation
- Lint: PASS/FAIL
- TypeCheck: PASS/FAIL
- Tests: PASS/FAIL (N tests, N passing)
```

Each fix entry **must** include `[CRITICAL]`, `[HIGH]`, `[MEDIUM]`, or `[LOW]` in the heading —
the compliance gate script matches on `^### Fix N:.*\[SEVERITY\]`.
