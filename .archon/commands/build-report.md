# Build Report: Full Pipeline Summary

Generate a comprehensive summary of the entire build pipeline run.

## Input
Read ALL artifacts from `$ARTIFACTS_DIR/`:
1. `context_packet.json` — full PRD pipeline state
2. `phases/` — all phase files (Glob)
3. `discovery-table.md` — codebase patterns found
4. `implementation-report.md` — what was built
5. `verification-report.md` — Wall/Door/Room compliance
6. `review-correctness.md` — correctness review
7. `review-failures.md` — silent failure review
8. `review-tests.md` — test coverage review
9. `review-simplify.md` — simplification review
10. `fix-report.md` — fixes applied

## Generate Report

### Build Summary
- Product name and description
- Tech stack
- Total mechanisms built
- Total phases completed
- Wall/Door/Room counts and compliance rate

### Quality Scorecard
| Metric | Score |
|--------|-------|
| Wall compliance | X/Y (Z%) |
| Pulse checks passed | X/Y |
| Seam checks passed | X/Y |
| Full checkpoint | PASS/FAIL |
| Critical issues found | N (N fixed) |
| High issues found | N (N fixed) |
| Test coverage | X mechanisms tested |

### Per-Phase Summary
For each phase: what was built, validation results, issues found and fixed.

### Review Findings
- Top issues from each reviewer
- What was fixed vs deferred

### How to Run
- Tech stack and prerequisites
- Install commands
- Start commands
- Environment variables needed

### Predicted vs Actual
- Complexity: predicted vs actual
- Token usage: estimated vs actual
- Phases: planned vs completed

### Recommendations
- Issues deferred to human review
- Suggested improvements for next iteration
- Areas where the plan could be improved

Write report to `$ARTIFACTS_DIR/build-report.md` AND output it as your response.
Keep under 500 lines. Use tables.
