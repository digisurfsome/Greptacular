# PRD Pipeline - Full Flow Diagram

## The Complete Pipeline

```
INTERACTIVE (you talk, CLI responds)          AUTOMATED (hands-off)
==========================================    ================================

Step 0: Boilerplate Selection                 Step 4: Mechanism Extraction
  "Do you have a boilerplate?"                  Decomposes concept into
  Pick from 5 sheets or describe yours          buildable mechanisms (A-N)
       |                                              |
       v                                              v
Step 1: Idea Capture                          Step 5: Seven-Question Scaffolding
  "Tell me about the app"                       Classifies each mechanism step
  Back-and-forth brainstorm                     as WALL / DOOR / ROOM
       |                                              |
       v                                              v
Step 2: First Agent OS Pass                   Step 6: Layout, Mockups, Style
  Claude structures your idea into              Auto-selects layout, pages,
  product identity, personas,                   and visual style based on
  feasibility, problem statement                archetype matches
       |                                              |
       v                                              v
Step 3A: Gap Analysis                         Step 7: Phase Sequencing
  Scans for missing mechanisms                  Splits into build phases with
  Asks targeted questions                       token budgets and file sandboxes
  You answer the gaps                                 |
       |                                              v
       v                                        Step 8: Protocol Injection
Step 3B: Second Agent OS Pass                   Embeds verification checkpoints
  Merges gap analysis answers                   into each phase
  with original Agent OS into                         |
  a COMPLETE spec (~90%)                              v
       |                                        Step 9: Verification Agent Setup
       |                                          Configures the two-strike
       |                                          verification protocol
       |                                              |
       v                                              v
  context_packet.json ------>------>-------> Step 10: Output Generator
  (saved to disk)                               Renders everything into:
                                                - phase-1.md through phase-N.md
                                                - build.sh
                                                - CLAUDE.md
                                                - BUILD_RULES.md
                                                - README.md
```

## Two Ways to Enter

### Way 1: Full CLI Pipeline (from scratch)
```
/prd-start prd-output/my-app/     <-- Steps 0 through 3B (interactive)
/prd-chain prd-output/my-app/     <-- Steps 4 through 10 (automated)
```

### Way 2: Bring Your Own Agent OS (what you do now)
```
[brainstorm in Claude web/desktop]
[make Agent OS manually]
[do gap analysis manually]
[make second Agent OS pass manually]
[save final Agent OS doc to prd-output/my-app/agent-os.md]

/prd-prep prd-output/my-app/agent-os.md   <-- Converts to context_packet.json
/prd-chain prd-output/my-app/              <-- Steps 4 through 10 (automated)
```

## What Each Command Does

| Command | Input | Output | Interactive? |
|---------|-------|--------|-------------|
| `/prd-start` | Empty folder | context_packet.json + phase docs | YES - back and forth chat |
| `/prd-prep` | Your Agent OS markdown file | context_packet.json | NO - reads and converts |
| `/prd-chain` | Folder with context_packet.json | PRD files (phases, build.sh, etc.) | NO - runs automatically |

## The Step Numbering

| Old Number | New Label | Name | Type |
|------------|-----------|------|------|
| 0 | Step 0 | Boilerplate Selection | Interactive |
| 1 | Step 1 | Idea Capture | Interactive |
| 2 | Step 2 | First Agent OS Pass | Claude processes (you review) |
| NEW | Step 3A | Gap Analysis | Interactive |
| NEW | Step 3B | Second Agent OS Pass | Claude processes (you review) |
| 4 | Step 4 | Mechanism Extraction | Automated |
| 5 | Step 5 | Seven-Question Scaffolding | Automated |
| 6 | Step 6 | Layout, Mockups, Style | Automated (auto-selects) |
| 7 | Step 7 | Phase Sequencing | Automated |
| 8 | Step 8 | Protocol Injection | Automated |
| 9 | Step 9 | Verification Agent Setup | Automated |
| 10 | Step 10 | Output Generator | Automated |

Note: The original skills kept their numbering (stage-03 through stage-10).
Steps 3A and 3B are the new additions that replace what was previously Step 3.
The context_packet still uses stage_0 through stage_10 internally.
