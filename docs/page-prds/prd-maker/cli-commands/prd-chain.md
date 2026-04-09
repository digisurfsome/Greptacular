---
description: Run PRD pipeline stages 3-10 automatically from context_packet.json
---

# PRD Chain -- Automated Pipeline Stages 3 through 10

You will process a `context_packet.json` through PRD pipeline stages 3-10 sequentially. Each stage reads the packet, processes it according to its skill instructions, and writes the updated packet back to disk.

## Input

`$ARGUMENTS` is the path to the directory containing `context_packet.json`.

Example: `/prd-chain prd-output/my-app/`

If `$ARGUMENTS` is empty, ask the user for the directory path.

## Before Starting

1. **Read** `context_packet.json` from the specified directory.
2. **Check** `metadata.current_stage` to determine where to start:
   - current_stage is 2: start at Stage 3 (raw document needs structuring)
   - current_stage is 3: start at Stage 4 (document already structured, skip Agent OS step)
   - current_stage is 4-9: resume at the next stage (picking up from checkpoint)
   - current_stage is 10: all stages complete, report and stop
3. **Verify** the required prior stage data exists. If stage_0, stage_1, or stage_2 are missing, tell the user to run `/prd-prep` first.

## Critical Rules

1. **Process ONE stage at a time.** Complete each stage fully before starting the next.
2. **Write the updated context_packet.json after EACH stage.** This is your checkpoint. If the session runs out of context, the user can start a new session and run `/prd-chain` again to resume automatically.
3. **Stage 6 is normally interactive** (asks user to pick layout, approve pages, pick style). In chain mode, AUTO-SELECT the best options based on archetype matches, target user profile, and app type. Do not pause for user input. Note your auto-selections in the output so the user can review later.
4. **Read each stage's full SKILL.md** (including reference appendices) before processing that stage.
5. **Follow the skill's confidence scoring.** If a stage scores below 70, STOP the chain and report the issue. Do not continue with low-confidence output.
6. **Do NOT hallucinate data.** If a stage needs information that does not exist in the context_packet, flag it and either use the skill's escape hatch mechanism or stop.

## Stage Skill Files

Read these in order as needed. Each file contains the full skill instructions, input/output schema, and reference appendices:

- Stage 3: docs/page-prds/prd-maker/skills-complete/stage-03-agent-os-structuring/SKILL.md
- Stage 4: docs/page-prds/prd-maker/skills-complete/stage-04-mechanism-extraction/SKILL.md
- Stage 5: docs/page-prds/prd-maker/skills-complete/stage-05-seven-question-scaffolding/SKILL.md
- Stage 6: docs/page-prds/prd-maker/skills-complete/stage-06-layout-mockups-style/SKILL.md
- Stage 7: docs/page-prds/prd-maker/skills-complete/stage-07-phase-sequencing/SKILL.md
- Stage 8: docs/page-prds/prd-maker/skills-complete/stage-08-protocol-injection/SKILL.md
- Stage 9: docs/page-prds/prd-maker/skills-complete/stage-09-verification-agent-setup/SKILL.md
- Stage 10: docs/page-prds/prd-maker/skills-complete/stage-10-output-generator/SKILL.md

## Execution Loop

For each stage N (starting from the determined start point):

### Step A: Load the Skill
Read the full SKILL.md file for stage N. Understand:
- What input fields from the context_packet this stage needs
- What processing steps to follow
- What output fields this stage produces
- What confidence scoring criteria to apply

### Step B: Process
Follow the skill's processing instructions exactly. Use the reference appendices in the skill file for any lookups, classifications, or template matching. The context_packet contains all prior stage outputs -- read the fields the skill specifies as input.

### Step C: Score
Apply the skill's 5-dimension confidence scoring:
- Completeness (0-20)
- Accuracy (0-20)
- Consistency (0-20)
- Specificity (0-20)
- Handoff Readiness (0-20)

Total = 0-100.
- 90 or above: PASS. Continue normally.
- 70 to 89: FLAG. Continue but note the flag in metadata.
- Below 70: FAIL. Stop the chain. Report which stage failed, why, and what is missing.

### Step D: Update the Packet
Add your output to `context_packet.stage_N` following the skill's output schema.
Update `metadata.current_stage` to N.
Update `metadata.confidence_scores.N` with your scoring.
Update `metadata.stage_timestamps.N` with current ISO 8601 timestamp.
Update `metadata.updated_at`.

### Step E: Write to Disk
Write the updated `context_packet.json` to the output directory. This is your checkpoint.

### Step F: Report
Print a brief status line:

  [Stage N: Stage Name] Score: XX/100 (PASS/FLAG/FAIL) | summary of output

Then proceed to the next stage.

## Stage 10 Special Handling

Stage 10 is the Output Generator. In addition to updating the context_packet, it produces deliverable files. Write these to the output directory:

- phases/phase-1.md, phases/phase-2.md, etc. (one per build phase)
- build.sh (or build.bat on Windows)
- CLAUDE.md (build agent instructions)
- BUILD_RULES.md (enforcement rules)
- README.md (project readme)

Create a phases/ subdirectory in the output directory for the phase files.

## Context Window Management

These stages with their full skill files will use significant context. If you notice:
- Your responses becoming shorter or less detailed
- You are struggling to recall earlier stage outputs
- You are losing track of the skill instructions

Then STOP at the current stage boundary (after writing the checkpoint). Report:

  CONTEXT LIMIT REACHED
  Last completed stage: N
  Context packet is saved to disk at: [path]
  To resume: start a new session and run /prd-chain [same-directory]
  It will automatically pick up from Stage N+1.

## Final Report

After all stages complete (or if stopped early), print a summary showing:
- Which stages were completed and their confidence scores (PASS/FLAG for each)
- List of all files generated
- The output directory path
- If paused due to context limits, clear instructions for resuming
- Any flags or warnings from the pipeline run
