# OS Automation Skills — Stage 10: CLAUDE.md Generator

> **What this does:** Takes everything from Stages 0-9 and renders it into a single, drop-in-and-run CLAUDE.md build file. This is the final output — the deliverable.

---

## When to Use

After Stage 9 gap analysis scores COMPLETE or NEAR_COMPLETE. All gaps must be resolved before generating.

## Input

All stage outputs (0-9).

## Process

### Step 1: Assemble the CLAUDE.md

Render all decisions into a single markdown file following this exact structure:

```markdown
# [System Name] — CLAUDE.md Build File

> **What this is:** Drop this file as CLAUDE.md into a project folder, run `claude`, and it builds the complete [system name]. 

---

## Mission
[One paragraph from Stage 0 — what this system does and why]

---

## API Keys Required
[From Stage 4 — full .env template with every key]
[For each key: how to get it, what plan, what cost]

---

## Tech Stack
[From Stage 4 — runtime, dependencies with versions]

---

## Database Schema
[From Stage 4 — full SQL or schema definition]

---

## Pipeline Architecture
[From Stage 1 — text diagram of the flow]
[CLI commands with examples]

---

## File Structure
[From Stage 7 — exact tree of all files]

---

## Module Specifications
[From Stages 2, 3, 7 — for each file:]
  - Functions with signatures
  - What it imports
  - Rate limiting rules
  - Error handling rules
  - For AI steps: the prompt skeleton

---

## Rules
[From all stages — numbered list of constraints:]
  1. Rate limit rules
  2. Save incrementally rule
  3. Error handling defaults
  4. Quality gate rules
  5. Any domain-specific rules

---

## Testing Checklist
[From Stage 8 — numbered checklist with commands]

---

## Build Order
[From Stage 7 — numbered build phases with test criteria]
```

### Step 2: Validate Completeness

Check the generated CLAUDE.md against:

| Section | Must Include | Source Stage |
|---------|-------------|-------------|
| Mission | Clear 1-paragraph purpose | Stage 0 |
| API Keys | Every key with how-to-get | Stage 4 |
| Tech Stack | Runtime + all dependencies | Stage 4 |
| Database | Full schema SQL | Stage 4 |
| Pipeline | Architecture diagram + CLI commands | Stage 1 |
| File Structure | Exact file tree | Stage 7 |
| Module Specs | Every function in every file | Stages 2, 3, 7 |
| Rules | All constraints numbered | Stages 5, 3 |
| Testing | Numbered checklist with real test data | Stage 8 |
| Build Order | Phased with test criteria | Stage 7 |

### Step 3: Add Dashboard Section (if Stage 6 produced one)

```markdown
## Dashboard
[ASCII mockup of terminal dashboard]
[CLI commands for status/health/report]
```

### Step 4: Verify Build-Readiness

The CLAUDE.md is ready when:
- [ ] A developer who has never seen this project can read it and build the system
- [ ] Every file is specified — no "figure it out" sections
- [ ] Every function is defined — inputs, outputs, behavior
- [ ] Every API interaction has rate limits and error handling
- [ ] The build order means they can test as they go, not just at the end
- [ ] The testing checklist uses real data, not hypotheticals

## Output

The CLAUDE.md file itself — written to `docs/operating-system-creator/CLAUDE-MD-[SYSTEM-NAME].md`

## Rules

1. The CLAUDE.md is the ONLY deliverable that matters. Everything else was scaffolding to produce this.
2. It must be self-contained. No references to "see Stage 3 for details." Everything is inlined.
3. A fresh Claude Code session with only this file should be able to build the entire system.
4. If something is unclear in the CLAUDE.md, the gap analysis (Stage 9) failed. Go back and fix it.
