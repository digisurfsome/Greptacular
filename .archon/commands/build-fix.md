# Fix: Synthesize Reviews and Fix Issues

Read all 4 review reports, prioritize findings, and fix what needs fixing.

## Input
Read ALL review reports from `$ARTIFACTS_DIR/`:
- `review-correctness.md`
- `review-failures.md`
- `review-tests.md`
- `review-simplify.md`
Also read `verification-report.md` for Wall/Door/Room compliance issues.

## Process

### Step 1: Deduplicate
Multiple reviewers may flag the same issue. Merge duplicates, keep the most detailed version.

### Step 2: Prioritize
| Priority | Fix? | Criteria |
|----------|------|----------|
| Critical | YES immediately | Bugs, security, data loss |
| High | YES | Logic errors, missing error handling, WALL violations |
| Medium | YES if quick | Pattern inconsistencies, missing edge cases |
| Low | NO — document only | Style preferences, minor optimizations |

### Step 3: Fix Critical and High Issues
For each issue:
1. Read the file at the referenced line
2. Understand the problem
3. Apply the fix
4. Run validation (compile, lint, test) after each fix
5. If fix breaks something else: revert and try alternative approach

### Step 4: Two-Strike Rule
If the same fix fails twice: STOP. Document it as "needs human review" and move on.

### Step 5: Add Missing Tests
From review-tests.md findings, add tests for:
- All WALL steps that lack verification tests
- Critical edge cases identified by reviewers
- Integration points between mechanisms

## Output
Write fix report to `$ARTIFACTS_DIR/fix-report.md`:
- Issues fixed (count by severity)
- Issues deferred to human (with rationale)
- Tests added
- Final validation results (compile, lint, test)
