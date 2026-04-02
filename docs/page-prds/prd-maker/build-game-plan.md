# PRD Maker — Build-Out Game Plan

> **Status:** Active plan. Follow this sequence.
> **Date:** 2026-04-02
> **Author:** Opus 4.6 consulting session

---

## The 7-Folder View (Your Diagram, Mapped)

| Your Folder | What Happens | Our Steps |
|---|---|---|
| 1. Tim's 10 Step Plan + Research | ✅ DONE — the research-reference.md, stage extractions, extracted skills, mechanism framework, Martin's checklist | Already complete |
| 2. AI Critique of Tim's Plan + Research | ✅ DONE — the consulting report just written (verdict on Martin's checklist, Step 0 architecture, skill mapping, contracts) | Already complete |
| 3. Output Critique | Build the skills, run them, critique what comes out | Phases 2-3 below |
| 4. Testing Output | Run a real app idea through all stages | Phase 4 below |
| 5. Iterating + Re-testing Output | Adjust skills based on test results, rerun | Phase 5 below |
| 6. Start Using Skills to Dial In to Make App | Use refined skills to build real apps you need | Phase 6 below |
| 7. Make Into Deterministic App Using Skills | Convert proven skills into modular app with API-style connections | Phase 7 below |

---

## Phase 1: Foundation Fixes (Before Any Skills Get Built)

These are the pre-work items from the consulting report. They MUST happen before building any stage skills because every downstream skill inherits these decisions.

### 1A. Agnosticize Martin's Checklist

**What:** Take `trial-idea-1-structural-checklist.md` (192 rules) and create `martin-agnostic-checklist.md` where all Firebase/Gemini-specific rules are converted to generic patterns.

**How:** One fresh agent gets:
- The full trial-idea-1-structural-checklist.md
- Instructions to tag each rule as UNIVERSAL / STACK-SPECIFIC / PATTERN
- For STACK-SPECIFIC rules: rewrite as generic (e.g., "serverTimestamp()" → "database server timestamp function")
- For PATTERN rules: extract the principle, note the Firebase example as one implementation
- Output: `martin-agnostic-checklist.md` with a new "Type" column (UNIVERSAL/STACK-SPECIFIC/PATTERN)

**Agent type:** Fresh agent, solo, detailed prompt. This is a judgment call on every rule — not a subagent task.

**Output file:** `docs/page-prds/prd-maker/martin-agnostic-checklist.md`

### 1B. Add Severity Column

**What:** Add CRITICAL / STANDARD / POLISH severity to each rule in the agnostic checklist.

**How:** Same agent that did 1A, or a second pass by another fresh agent.
- CRITICAL: Security, auth, data integrity, build-breaking (~40 rules)
- STANDARD: UX quality, component patterns, mobile responsiveness (~100 rules)
- POLISH: Cosmetic, nice-to-have (~52 rules)

**Can be done:** In parallel with 1A (same agent does both in one pass) or as a second pass.

**Output file:** Added column to `martin-agnostic-checklist.md`

### 1C. Create Industry Standards Supplement

**What:** Create a supplementary checklist covering the 8+ gaps identified in the consulting report (i18n, config externalization, logging, security beyond auth, etc.)

**How:** Fresh agent gets:
- The 8 gaps from the consulting report
- The 30-category master checklist (from research-reference.md)
- The arc42 template (from extracted-skills/arc42/)
- The 12-Factor App doc (from extracted-skills/frameworks/)
- Instructions: create a structured checklist in the same format as Martin's (Rule / Description / Technical Spec / Boilerplate Match)

**Agent type:** Fresh agent. This is research + judgment — needs full thinking capacity.

**Output file:** `docs/page-prds/prd-maker/industry-standards-checklist.md`

### 1D. Create App Archetype Library

**What:** Define 6-8 common app archetypes with their default mechanism requirements (A-N categories) and standard pages.

**How:** Fresh agent gets:
- The mechanism-identification-framework.md
- The archetypes listed in the consulting report (Dashboard, Marketplace, Chat, CRUD/Tool, Social, Wizard, Landing, SaaS)
- Instructions: for each archetype, list which A-N categories are typically needed and what pages are standard

**Agent type:** Fresh agent OR could be a subagent since this is more structured/deterministic.

**Output file:** `docs/page-prds/prd-maker/app-archetype-library.md`

### 1E. Define Context Packet Schema

**What:** Create the JSON schema for the data object that flows through all 10 stages.

**How:** Fresh agent gets:
- The context_packet from the consulting report
- The stage-by-stage input/output descriptions from all 10 stage extractions
- Instructions: define a JSON schema where each stage has a clear section it reads and writes

**Agent type:** Could be subagent — this is structured/deterministic.

**Output file:** `docs/page-prds/prd-maker/context-packet-schema.md`

### 1F. Write Stage Contracts (Completion Criteria)

**What:** For each stage (0-10), define the exact "done when..." conditions.

**How:** Fresh agent gets:
- The contracts from the consulting report
- The nicknisi confidence rubric as a reference pattern
- All 10 stage extractions
- Instructions: write a mini-contract per stage with measurable completion criteria

**Agent type:** Fresh agent — requires judgment about what "done" means.

**Output file:** `docs/page-prds/prd-maker/stage-contracts.md`

### Phase 1 Summary

| Task | Agent Type | Depends On | Can Parallel? |
|---|---|---|---|
| 1A. Agnosticize checklist | Fresh agent | Nothing | ✅ Yes |
| 1B. Add severity | Same as 1A or fresh | 1A | Do with 1A |
| 1C. Industry standards supplement | Fresh agent | Nothing | ✅ Yes |
| 1D. App archetype library | Fresh or subagent | Nothing | ✅ Yes |
| 1E. Context packet schema | Fresh or subagent | Nothing | ✅ Yes |
| 1F. Stage contracts | Fresh agent | Nothing | ✅ Yes |

**All of Phase 1 can run in parallel.** 4-5 agents working simultaneously. This is "fix the foundation" work.

---

## Phase 2: Build Stage Skills (One Agent Per Stage)

After Phase 1 is done, we have: an agnostic checklist, severity ratings, industry standards, archetypes, a context packet schema, and stage contracts. NOW we build the skills.

### Build Order

The consulting report recommended Stage 5 first (it's the engine). But given your process (skills → test → iterate), I think we should build them in pipeline order (0 → 10) so we can test the FLOW, not just individual stages. Here's why:

- Building 0 → 10 in order means each agent has the previous stage's output format to reference
- You can test partial pipelines early (run Stages 0-2 on a real idea even before Stage 3 exists)
- The "test as you go" approach matches your philosophy better than "build the engine first"

**However:** If time is tight, Stage 5 (the engine) is the highest-risk stage. If you want to de-risk first, build 5 before 1-4.

### Per-Stage Build Process

For EACH stage (0 through 10):

1. **One fresh agent** gets a detailed handoff prompt containing:
   - The full system overview (1-page summary of the 10-stage pipeline)
   - The specific stage extraction (from `stage-extractions/stage-NN-extraction.md`)
   - The relevant skill fragments (from the consulting report's skill mapping)
   - The context packet schema (what input this stage receives, what output it produces)
   - The stage contract (completion criteria)
   - The structural preamble (Martin's agnostic checklist — for context)
   - The skill-creator skill (from `.claude/skills/skill-creator/SKILL.md`) — so it follows the right format
   - Any reference skills it should study (e.g., Stage 1 gets nicknisi's ideation SKILL.md)
   - **Plus:** Whatever Nate B. Jones materials you're going to share (assessed in Step 2)

2. **The agent builds:** A complete SKILL.md for that stage following the skill-creator format, with:
   - Frontmatter (name, description)
   - Full process documentation
   - References (bundled context files the skill needs)
   - Input/output format matching the context packet schema
   - Completion criteria from the stage contract

3. **The agent outputs:** The skill to `docs/page-prds/prd-maker/skills/stage-NN-[name]/SKILL.md`

### Stage Build Sequence

| Stage | Name | Key Reference Skill | Parallel Group |
|---|---|---|---|
| 0 | Technical Foundation | rodrigorjsf Block 5-7 interrogation | Group A |
| 1 | Idea Capture | nicknisi ideation intake | Group A |
| 2 | Gap Analysis | nicknisi confidence scoring + mechanism framework | Group A |
| 3 | Agent OS Structuring | rodrigorjsf context_packet | Group B (needs 0-2 output format) |
| 4 | Mechanism Extraction | mechanism-identification-framework.md + product-lens ICE | Group B |
| 5 | 7-Question Scaffolding | Original IP (7 questions + W/D/R) + haberlah DO NOT CHANGE | Group C (needs 4 output) |
| 6 | Layout + Mockups + Style | design-system + frontend-patterns + Martin's style prompt | Group C |
| 7 | Phase Sequencing | haberlah phased prompts + token budget math | Group D (needs 5-6 output) |
| 8 | Protocol Injection | verification-loop + quality-gate | Group D |
| 9 | Verification Agent Setup | loop-operator + reviewer pattern | Group D |
| 10 | Output Generator | sop-creator + spec-template + nicknisi contract | Group E (needs all) |

**Parallel Groups:**
- Group A (Stages 0, 1, 2): Can build simultaneously — they're intake stages with independent logic
- Group B (Stages 3, 4): Can build simultaneously — but should reference Group A's output format
- Group C (Stages 5, 6): Can build simultaneously
- Group D (Stages 7, 8, 9): Can build simultaneously
- Group E (Stage 10): Must wait for all others — it's the serializer

**Total: 5 sequential rounds, with 2-3 agents running in parallel per round.** Could be done in 5 sessions.

---

## Phase 3: First Test Run (One App Idea Through the Pipeline)

### What Happens

1. Pick a real app idea you actually want built (one of your marketing tools)
2. Run it through Stage 0 skill → get platform profile
3. Run through Stage 1 → get raw capture
4. Run through Stage 2 → get gap-filled concept
5. Continue through all stages
6. Evaluate: did each stage produce what the contract says? Did the final output look buildable?

### The Evaluation Criteria

For each stage, score:
- **Completeness:** Did it fill all fields in the context packet? (0-10)
- **Accuracy:** Is what it produced correct / sensible? (0-10)
- **Handoff Quality:** Could the next stage use this output without confusion? (0-10)
- **Contract Met:** Did it meet all completion criteria? (Yes/No)

For the final output (Stage 10):
- **Buildability:** Could an agent actually build an app from this spec? (0-10)
- **Determinism:** Are the instructions precise or vague? (0-10)
- **Completeness:** Are there obvious gaps a developer would notice? (0-10)

### What to Look For

- Stages where the agent "invented" information instead of asking for it
- Stages where the output format didn't match what the next stage expected
- Stages that took too long or used too many tokens
- Stages where the contract was met but the output still felt wrong (contract needs tightening)

---

## Phase 4: Iterate Skills Based on Test Results

### Process

1. Review Phase 3 evaluation scores
2. Identify the 2-3 worst-performing stages
3. For each: diagnose WHY it underperformed (bad skill instructions? bad input format? missing context?)
4. Rewrite those stage skills with the fixes
5. Rerun the pipeline with the same app idea
6. Compare scores — did it improve?

### When to Stop Iterating

Stop when:
- All stages score ≥7 on all criteria
- All contracts are met
- The final output is buildable without the human saying "wait, that's wrong"

Don't aim for perfection. Aim for "good enough to build a real app" — then the app-building process will surface the next round of issues.

---

## Phase 5: Build 3-5 Real Apps Using the Skills

### Purpose

This is where you make the apps you actually need for your marketing flow. The skills are the builder. Each app build is also a stress test of the pipeline.

### What You Learn

- Do different app types (dashboard vs tool vs marketplace) surface different skill weaknesses?
- Are there patterns across all builds? (e.g., "Stage 4 always struggles with X")
- Is the boilerplate matching working? (all apps on same boilerplate = all apps have same structural foundation)

### The Self-Assessment System

After each build, run the evaluation criteria from Phase 3 again. Track scores over time. You should see improvement as you refine skills between builds.

---

## Phase 6: Build the App-Tester / Assessor

### What It Is

A skill (and eventually an app feature) that evaluates the OUTPUT of the pipeline:

1. Takes the final Phase 10 output
2. Goes through each stage's contract criteria
3. Scores each stage's contribution to the final product
4. Identifies which stages need adjustment
5. Produces a "build health report"

### When to Build It

After Phase 5. You need 3-5 completed builds to have enough data to know what the assessor should check for. Building it before that = guessing.

---

## Phase 7: Convert Skills to Modular App

### The Modular Architecture

Each stage becomes a module. Modules connect via the context_packet (the JSON data object). Swapping Stage order = changing which module reads/writes the packet next. 

```
[Stage 0] → context_packet → [Stage 1] → context_packet → [Stage 2] → ...
     ↑                            ↑                            ↑
     │                            │                            │
  Module 0                    Module 1                    Module 2
  (pluggable)                (pluggable)                (pluggable)
```

**The "API cord" metaphor:** Each module exposes:
- `input_schema`: what fields it reads from the context_packet
- `output_schema`: what fields it writes to the context_packet
- `process()`: the actual logic
- `contract`: completion criteria

To swap Stage 5 to position 1: unplug its cord from position 5, plug into position 1. As long as the input_schema fields exist in the context_packet at that point, it works.

### When to Do This

After Phase 5 (3-5 real apps built). NOT before. The skills need to be stable before you bolt them into an app. Building the app too early = welding to the floor while you're still rearranging furniture.

---

## What Happens RIGHT NOW (This Session)

### Step 1 (Current): This Game Plan ✅
You're reading it.

### Step 2 (Next): You Share Nate B. Jones Materials
You give me the skill-making skill and the "distill loose info into gold" skill. I assess them and determine what (if anything) to incorporate into our skill-building process.

### Step 3 (After Assessment): I Write Handoff Prompts
I create the exact, detailed prompts for:
- Phase 1 agents (foundation fixes — 4-5 prompts)
- Phase 2 first batch (Stage 0, 1, 2 skills — 3 prompts)

These prompts are self-contained. Any fresh agent can pick one up cold and execute.

### Step 4 (You Execute): Run the Agents
You take my prompts, spin up fresh agents, let them build. Come back with results.

---

## Nate B. Jones Skill Kit Integration

**Reference file:** `nate-jones-skill-kit.md`

Every stage skill is built using Nate's Prompt 2 (Output-Extraction Method) and audited using Prompt 3 (Agent-Readiness Audit with 4 criteria). See reference file for full details.

Build process per skill:
1. Agent gets the stage extraction + skill fragments + context packet schema
2. Agent builds SKILL.md following Nate's Prompt 2 methodology
3. A SECOND agent audits the skill using Nate's Prompt 3 (4 agent-readiness criteria)
4. If any criterion fails → revise and re-audit
5. Only skills passing all 4 criteria enter the pipeline

---

## Testing Architecture

### In-Phase Testing (During Build)

| Check Type | When | What It Does |
|---|---|---|
| **PULSE** (light) | Every 3 files | Lint, type check, import resolution |
| **SEAM** (medium) | At component connections | Interface matching, data flow between connected parts |
| **FULL** (heavy) | End of each phase | Full lint+type, unit tests, file sandbox verification, build order check |

### Post-Build Testing (Stage 11)

| Stage | What | How |
|---|---|---|
| **11A: Automated** | Lint, type, unit tests, integration tests, build succeeds, zero console errors | CLI — `npm run build`, `npm run test`, etc. |
| **11B: Functional** | Navigate every route, test every form/CRUD/auth/error state, responsive check | Agent-driven walkthrough in terminal |
| **11C: Computer-Use** | Generate user manual → generate test script → computer-use agent clicks every button | Automated UI testing via computer use |

### Bug Feedback Loop

```
Bug found → Classify (structural/mechanism/UI/integration)
  → Route to specific phase that caused it
  → Re-run ONLY that phase
  → Re-test from 11A
  → Repeat until clean
```

**NOT re-run the whole pipeline. Fix the specific phase.**

---

## Escape Hatch Protocol

Every stage includes this standard pattern:

```
Agent hits unsolvable problem
  → SAVE context_packet to disk (nothing lost)
  → LOG what happened, what was tried, what failed
  → SIGNAL "NEEDS_HUMAN" to controller
  → PRESENT: current stage, progress so far, specific problem, suggested options
  → WAIT for human response
  → RESUME from saved state
```

---

## Context Packet Version Control

Every stage saves a snapshot BEFORE modifying:
```
context_packet_v0.json  (after Stage 0)
context_packet_v1.json  (after Stage 1)
...
context_packet_v10.json (after Stage 10)
```

If Stage N corrupts data → roll back to v(N-1) → re-run Stage N.

---

## Confidence Gate (Every Stage, Not Just Stage 2)

Every stage outputs a confidence score with its results:
- ≥ 90: Pass to next stage
- 70-89: Flag concerns, ask human "proceed or revise?"
- < 70: Do not proceed. Escape hatch.

---

## Scope Creep Detector

Every stage checks: "Am I still within the scope defined in the Stage 2 contract?" If the agent is adding features/complexity not in the contract → flag it, don't add it.

---

## Existing App Path (Future — Phase 7+)

Greenfield path (Stages 0-10) built first. Then add "Existing App" variant:
- Stage 0 gets a CODEBASE ANALYSIS sub-step (scan what exists)
- Martin's checklist → CHECK mode (which rules are already followed?)
- Mechanisms → only NEW ones
- Phases → must not break existing code

---

## Pipeline Execution Strategy

### Phase 3-4 (Testing): Run manually in terminal, one stage at a time.
### Phase 5+ (Production): Build AutoForge dashboard page.

The AutoForge dashboard:
- Visual pipeline showing all 11 stages
- "Start" button kicks off Stage 0
- Each stage runs via CLI
- Chat box for human input when needed
- Status per stage (pending/running/needs-input/complete/error)
- Context packet saved after each stage
- Escape hatch button on every stage

**This dashboard IS the first app built with the PRD Maker.** The system builds itself.

---

## Key Principles (Summary)

1. **Skills before app.** Always. Skills are cheap to change, apps are expensive.
2. **One agent per stage.** Fresh context, full thinking, clean output.
3. **Modular everything.** Context packet is the bus. Stages are modules. Cords, not welds.
4. **Test with real ideas.** Not toy examples — apps you actually want to use.
5. **The assessor comes AFTER builds.** You need data before you can evaluate.
6. **Default stack for everyone.** Your boilerplate. Deactivate what you don't need. Users peel away from defaults.
7. **Subagents for retrieval, fresh agents for judgment.** Reading files = subagent. Building a skill = fresh agent.
8. **Contracts at every stage.** "Done" has a measurable definition. No vibes.
9. **Iterate in small cycles.** Build 1 stage → test → fix → next stage. Not "build all 10 → pray."
10. **Guard context window.** Subagents do the heavy lifting. Main agent consults.
11. **Escape hatch everywhere.** Save state before crashing. Never lose work.
12. **Version control on context packet.** Snapshots after every stage. Rollback capability.
13. **Confidence gates between stages.** Don't pass garbage downstream.
14. **Scope creep detection.** Flag anything not in the contract.
15. **Nate's 4-criteria audit on every skill.** Agent-ready or don't ship it.
16. **Test in terminal.** Real file system, real builds, real databases. Not sandboxes.
17. **Bug feedback targets specific phases.** Don't rebuild everything for one bug.
