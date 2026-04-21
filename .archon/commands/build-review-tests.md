# Review: Test Coverage Analyzer

One of 4 parallel review agents. Your job: evaluate test coverage and identify gaps.

## Input
Read `$ARTIFACTS_DIR/implementation-report.md` for what was built.
Read `$ARTIFACTS_DIR/context_packet.json` for mechanism blueprints (stage_5).
Use Glob to find test files and source files. Read them.

## Focus Areas
1. **Missing tests**: Features built but no test coverage
2. **WALL step coverage**: Every WALL classification should have a test verifying the exact behavior
3. **Edge case coverage**: Happy path tested but failure paths missing
4. **Integration gaps**: Individual units tested but connections between mechanisms untested
5. **Test quality**: Tests that pass but don't actually verify behavior (tautological tests)
6. **Regression risk**: Code changes without corresponding test updates

## Evidence Standard
Every finding MUST reference the specific mechanism step and the missing test case.

## Output
Write findings to `$ARTIFACTS_DIR/review-tests.md`:
- Coverage summary (what's tested vs not)
- Missing test cases by mechanism
- WALL steps without verification tests
- Suggested test additions
