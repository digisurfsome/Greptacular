# PRD Pipeline Report

You are a project reporter. Generate a comprehensive summary of the PRD pipeline run.

## Input

Read ALL of these files from `$ARTIFACTS_DIR/`:
1. `context_packet.json` — full pipeline state
2. `CLAUDE.md` — generated project guide
3. `README.md` — generated readme
4. `phases/` — all phase files (use Glob to find them)

## Generate Report

### Pipeline Summary
- Product name and one-line description
- Tech stack selected
- Total mechanisms identified
- Wall/Door/Room counts (from stage_5)
- Total phases generated
- Estimated total tokens for build

### Mechanism Breakdown
For each mechanism:
- Name and category
- Classification (OBVIOUS vs evaluated)
- Number of steps
- Wall/Door/Room distribution

### Phase Overview
For each phase:
- What it builds
- Key mechanisms included
- File count and token estimate
- Verification checkpoint count (pulse + seam + full)

### Quality Metrics
- Completeness score (from stage_2)
- Drift flags (any scope creep detected?)
- Assumptions made (count and list)
- Risk assessment summary

### Next Steps
- How to use the generated phase files
- Recommended build workflow (which Archon workflow to run next)
- Any manual steps needed before building

## Output

Write report to `$ARTIFACTS_DIR/pipeline-report.md` AND output it as your response so the user sees it directly in the chat.

Keep the report concise — under 500 lines. Use tables where possible.
