# OS Automation Skills — Pipeline Overview

> **What this is:** 10 stages that turn any manual process description into a complete, buildable CLAUDE.md automation file. Adapted from the PRD Maker app pipeline, paired down for automation systems.

---

## The Pipeline

```
Stage 0: Process Capture          ← "What does the human do today?"
    │
Stage 1: 6-Step Mapping           ← Map to INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE
    │
Stage 2: Step Decomposition       ← Break every step into inputs, outputs, decisions, errors
    │
    ├── GAP ANALYSIS (early pass) ← Quick scan for obvious missing pieces
    │
Stage 3: Automation Classification ← Each step: code, AI, or human?
    │
Stage 4: Environment Setup        ← APIs, keys, dependencies, cost math
    │
Stage 5: Error Handling            ← Retries, rollback, quality gates, data retention
    │
Stage 6: Dashboard Design         ← Terminal dashboard, CLI commands, notification rules
    │
Stage 7: Build Order              ← Dependencies, file structure, build phases, MVP path
    │
Stage 8: Test Cases               ← Sample data, testing checklist, health checks
    │
Stage 9: Gap Analysis (final)     ← Full 18-point sweep — what did we miss?
    │
Stage 10: CLAUDE.md Generator     ← Render the final build file
```

## Why This Order

1. **Capture first, organize second.** Stage 0 gets everything on paper raw. Stage 1 maps it to the pattern.
2. **Decompose before classifying.** You need to know all the steps (Stage 2) before deciding how each one gets automated (Stage 3).
3. **Early gap check.** After decomposition, do a quick gap scan to catch showstoppers before investing in detailed design.
4. **Environment after classification.** Once you know which APIs and AI models are needed (Stage 3), then nail down keys, costs, and rate limits (Stage 4).
5. **Error handling before dashboard.** Know what can go wrong (Stage 5) before designing what the operator sees (Stage 6).
6. **Build order after design is complete.** Stages 0-6 are design. Stage 7 plans the construction.
7. **Test cases before final gap check.** Having test cases (Stage 8) lets the gap analysis (Stage 9) check if testing is adequate.
8. **Gap analysis at the end.** Maximum surface area to check against. Catches everything.
9. **Generator last.** Pure rendering — zero decisions. Every ambiguity was resolved upstream.

## Gap Analysis Runs Twice

- **After Stage 2 (early pass):** 2-minute scan for showstoppers. "Are we missing any major API? Is this actually multi-phase? Any legal blockers?"
- **After Stage 8 (final pass):** Full 18-point checklist. Every gap must be covered or explicitly marked as N/A with reasoning.

## How to Use

### For a new automation:
1. Run stages 0-10 in order
2. Each stage reads the output of previous stages
3. The final output is a CLAUDE.md file ready to build from

### For testing the framework:
1. Take a process description (from a YouTube video, a brain dump, documentation)
2. Run it through the pipeline
3. Note any gaps where the stages didn't ask the right questions
4. Update the relevant stage skill
5. After ~10 diverse processes, the pipeline stabilizes

## Files

| File | Stage | Purpose |
|------|-------|---------|
| `stage-00-process-capture.md` | 0 | Raw intake of manual process |
| `stage-01-six-step-mapping.md` | 1 | Map to 6-step pattern |
| `stage-02-step-decomposition.md` | 2 | Break into granular steps |
| `stage-03-automation-classification.md` | 3 | Code vs AI vs Human per step |
| `stage-04-environment-setup.md` | 4 | APIs, keys, costs, rate limits |
| `stage-05-error-handling.md` | 5 | Failures, retries, rollback, quality |
| `stage-06-dashboard-design.md` | 6 | Terminal dashboard + CLI |
| `stage-07-build-order.md` | 7 | Dependencies, file structure, MVP |
| `stage-08-test-cases.md` | 8 | Sample data, verification, monitoring |
| `stage-09-gap-analysis.md` | 9 | 18-point gap checklist (runs twice) |
| `stage-10-claude-md-generator.md` | 10 | Render final CLAUDE.md |
