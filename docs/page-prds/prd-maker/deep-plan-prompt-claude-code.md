# Deep Plan Prompt — Claude Code Version (Agent Spawning)

> Works in: Claude Code CLI, Claude Code in VS Code terminal
> This version actually spawns parallel agents for exploration. Much more thorough.
> Copy everything below the line and paste it. Replace {YOUR_IDEA} with your concept.
> If you have an existing codebase, run this FROM that project directory.

---

```
I need a deep multi-perspective plan for this idea. Use agent spawning to do this properly — do NOT try to do everything yourself in one linear pass.

## My Idea

{YOUR_IDEA}

---

## Instructions — Follow this 5-phase process EXACTLY

### Phase 1: Parallel Exploration

Launch 3 Explore agents IN PARALLEL (single message, 3 Agent tool calls) with these focuses:

**Agent 1 — "Market & Pattern Scout"**
Research what exists in this space. What are the closest apps? What tech stacks do they use? What patterns work? What UX conventions exist for this type of app? If we have an existing codebase, scan the directory structure, entry points, and build system.

**Agent 2 — "Mechanism Mapper"**
From the idea description, identify every MECHANISM (not feature — mechanism). A mechanism is an engine part: "recommendation algorithm", "real-time sync", "payment flow", "content pipeline". Map what mechanisms this app needs, which are standard (use a library) and which are custom (build from scratch). If we have existing code, find existing patterns and utilities we can reuse.

**Agent 3 — "Risk & Complexity Analyst"**
What's hard about this? What could go wrong? What are the technical unknowns? What has the highest chance of requiring a rewrite? What integrations are needed? If we have existing code, find integration points, API boundaries, and data flow.

Wait for all 3 to complete before proceeding.

### Phase 2: Three Design Perspectives

Launch 3 Plan agents IN PARALLEL with the exploration results from Phase 1 included in each prompt:

**Agent A — "Simplicity Architect"**
Design the simplest possible version. Minimum code, maximum reuse, fastest to ship. Cut everything non-essential. Use existing libraries/services over custom code. Goal: working MVP in minimum time.

**Agent B — "Experience Architect"**
Design the version that feels incredible to use. First impression, micro-interactions, retention hooks, shareability. Focus on what the user FEELS, not engineering elegance.

**Agent C — "Scale Architect"**
Design the version built for 100x growth. Clean data model, API-first, proper abstractions, integration-ready. What breaks at scale and how to prevent it from day one.

Each agent must output:
1. Architecture overview
2. Page/screen map
3. Core data model
4. Implementation phases (each independently deployable)
5. Estimated complexity (X/10)
6. Biggest risk with this approach

Wait for all 3 to complete before proceeding.

### Phase 3: Consolidation (Do this yourself — do NOT spawn an agent)

Read all 6 agent outputs. Merge the three design perspectives into ONE plan:
- Default to the simplicity approach UNLESS UX or scale has a clearly justified reason for more complexity
- For each decision, note which perspective won and why
- Flag non-negotiables from each perspective

### Phase 4: Write the Final Plan

Use this EXACT structure:

# Deep Plan: [App Name]

## 1. One-Sentence Pitch
## 2. Core Mechanisms Table
## 3. User Journey (First 60 Seconds)
## 4. Architecture Overview (Layer / Tech / Why)
## 5. Page Map (Page / Purpose / Key Components)
## 6. Data Model (Core tables only)
## 7. Implementation Phases (each independently deployable, with files list)
## 8. Risks & Hard Parts (table with mitigation)
## 9. What Got Cut (from the 3 perspectives, what was dropped and why)
## 10. Competitive Edge

### Phase 5: Honest Assessment

- Difficulty: X/10
- Time to MVP: X days/weeks
- Biggest risk: [one sentence]
- Will people pay for this? [yes/no/maybe with reasoning]
- If I could only build ONE feature: [the atomic core]
```
