# Build Orchestrator — Full System Description

## What This Is

A build orchestration platform that lives inside AutoForge's existing navigation (alongside DunkStack, Workspace, Dashboard). One main nav item opens the system. Inside, four sub-tabs across the top — each tab is its own page with its own focused purpose and its own AI chat room (one objective per room). Together, they form a complete pipeline: from raw rules and a PRD, all the way through phased builds with live monitoring.

The tabs link together as one project. Past projects are saved and browsable. Each tab's work product feeds into the next.

---

## Tab 1: Rule Set Builder

**Purpose:** Take a pile of separate source documents (coding rules, contract templates, design specs, style guides — whatever you bring) and merge them into one clean, reusable rule set that gets attached to every build phase.

### Layout — Top to Bottom

**Top Section — The Originals**

- Text boxes across the page, each holding one source document
- Import from files or paste in directly
- These are your untouched originals — they never get modified, always preserved and visible
- Could be 3, could be 12 — however many sources you bring to the table

**The AI Chat (Own Room, Own MD)**

- This AI has ONE job: help you merge these originals intelligently
- You explain the objective — what you're building, how this connects to PRD phases, the big picture
- AI sees ALL originals at once before doing anything
- It comes back with a proposal: "These 2 should merge, these 3 should merge, this one stands alone"
- **It does NOT just go do it** — it proposes, you approve
- You can reject, adjust, re-ask until you're happy

**Middle Section — The Merge View**

- Side by side: original boxes on the left, merged result boxes on the right
- Each merged box shows at the top which originals fed into it (e.g., "Merged from Box 1, Box 3, Box 5")
- Visual progression: if you had 7 originals, you might now see 4 merged blocks (2 merged here, 3 merged here, 2 individuals)
- You can see the reduction: 7 originals became 4 blocks

**Bottom Section — The Placeholder Map**

- Mind map / outline view
- Each merged block gets a placeholder label (first, second, third...)
- Drag and reorder them
- AI writes connecting sentences between placeholders — little intros that frame what each section is about
- Drop-downs let you expand/collapse to read what's inside each placeholder
- AI can auto-organize the order, or you do it manually

**Final Output**

- All placeholders assembled in order with connecting sentences into one complete document
- This is your reusable rule set — the thing that gets added to every build phase
- Saved as a reusable entity per build type

**Key Principles:**
- Originals are always preserved and visible
- AI proposes, you approve — never auto-merges without permission
- Visual progression from many sources → grouped merges → final unified document
- Saved and reusable across projects

---

## Tab 2: Phase Chunker

**Purpose:** Take the PRD (which already exists — either you brought it or it was built using the PRD maker, which will eventually become a step before this) and break it into properly sized build phases based on token math and AI chunking.

Two parts on one page, working together:

### Part A — The Token Calculator (Deterministic, No AI)

This is pure math. A Python script running calculations. No AI guessing.

**Inputs (all editable fields):**

- **Model:** Which model you're using (e.g., Opus 4.6 = 200K context window)
- **Target percentage:** How much of that context you want to use (e.g., 50% = 100K usable tokens)
- **Testing budget per phase:** How many tokens to reserve for testing in each phase (e.g., 5,000 tokens — adjustable, this is a starting guess you refine over time)

**What it calculates and shows you transparently:**

- X tokens for the shared rules/description block (the output from Tab 1 that goes into every phase)
- X tokens for the coding chunk (the unique phase work — the actual build instructions)
- X tokens reserved for testing that phase
- Total per phase = all three added up, must stay under your ceiling
- Based on that math: how many phases the PRD needs to split into
- Each piece shown as a percentage of the total model capacity

**The visual:**

- Percentage bars or clear number breakdowns
- Rules portion + coding portion + testing portion = total per phase
- Everything adds up to 50% (or whatever target you set)
- You can see exactly where every token is allocated
- All numbers are adjustable — change the testing budget, the target percentage, the model, and everything recalculates

**Why this matters:** You're not guessing how big phases should be. The math tells you: given your rules, your model, and your testing needs, each phase can be exactly this big. No more, no less.

### Part B — The AI Chunking Room (Own AI, Own MD)

Separate AI from Tab 1. This one has its own focused MD file.

**Its ONLY job:** Take this PRD and break it into the right number of chunks (the number Part A calculated).

**The MD tells it:**

- Your sole job is to split this app spec into properly sized phases
- Each phase must be fully testable on its own
- Formatted so the coding agent can build and verify each phase cleanly
- Respect the token budgets that Part A calculated
- There is a skill set to this — chunks need to be logical units of work, not arbitrary cuts

**Output:** The PRD broken into N phases, each one properly sized, self-contained, and testable.

### How Tab 1 and Tab 2 Relate

Tab 1's rule set output becomes the "shared rules/description block" that Tab 2's math accounts for. The rule set goes into every phase. Tab 2 figures out how much room is left after the rules for actual coding and testing work.

In reality, these are more like settings/prep steps than a strict sequence. You need a PRD to chunk, and you need rules to factor into the math, but the order you set them up doesn't matter much. What matters is both exist before you move to Tab 3.

---

## Tab 3: Build Planner

**Purpose:** Define the agent roles, visualize the build sequence step by step, configure hooks, and generate the actual build script. This is where you organize what the build process looks like before anything runs.

### Agent Roles Section

Text boxes defining each role. Editable. Each one describes exactly what that agent does and what its MD instructions are.

**Default roles for a full build:**

- **Coder** — Gets the phase package, builds it
- **Reviewer** — Follows behind the coder, checks the code, catches issues before testing even starts (reduces tester workload significantly)
- **Tester(s)** — Could be multiple types depending on what testing is needed (unit tests, integration tests, etc.)

Each role is a saved, editable definition. You can add more roles, remove roles, customize per build type.

### The Build Sequence — Visual Step-by-Step

Shows the order of operations for each phase, laid out so you can see and understand every step:

1. **Coder** gets the phase package (rules + coding chunk + context from previous phase), builds it
2. **Reviewer** checks what coder built, writes up findings and any fixes needed
3. **Tester** runs testing on that chunk — each chunk is verified as thoroughly as possible so when phases are assembled, there are way fewer bugs
4. **Agent writes a summary/review** of what was built — this gets passed forward to the next phase's agents so they have full context
5. **Commit** — checkpoint after each completed phase
6. **Next phase starts** with the summary from the previous one injected in

All of this is visible, organized, editable. You see the structure before it becomes a script. You're not just getting a bash file dumped on you — you understand the organizational steps.

### Hooks

Testing hooks, commit hooks, automation triggers between steps. Configured here, visible here.

### Presets and Versioning

**Different build types need different setups:**

- **Full software build** — all roles, full testing, the works
- **Adding a feature** — lighter weight, focused scope
- **Reverse engineering spaghetti code** — different agent roles, different sequence
- **Clean room reverse engineering** — its own specialized approach

Each build type is a saved preset. When you come in, you pick: "Which preset do I want? Full build." It loads those roles, that sequence, those hooks.

**Versioning:**

- You can edit a preset per project, or save changes as a new version
- Version 1, Version 2, etc. — you choose which is the default
- If a recent version isn't working well, switch default back to an older version
- You're always learning, always adjusting — the system supports that without losing what worked before

### Saved as Projects

The build planner output is saved as its own project entity. It links to the rule set from Tab 1 and the phase chunks from Tab 2. All three tabs' outputs link together as one complete build project. You can come back, edit, reverse engineer what you did, learn from past builds.

---

## Tab 4: Operations Dashboard (Mission Control)

**Purpose:** NASA's control room. You're watching the launch. Live monitoring of what's being built, plus a queue system for lining up future builds and reviewing past ones.

### Top Bar — Always Visible

- **Phase progress indicator:** Dots or segments showing all phases. Completed phases are filled/colored, current phase is highlighted, remaining phases are empty/white. (Like a step wizard: 1-2-3-4-5-6-7, where dots 1-4 are colored and 5-7 are white)
- **Current agent role:** Which agent is active right now (coder? reviewer? tester?)
- **Token gauge:** A live counter/gauge showing current token usage as a percentage. If the math from Tab 2 said 50%, and you're watching it climb to 48%, 49%, 51%... you can see it. If it creeps to 52-53%, probably fine. If it hits 60%, 65%, 77% — something's wrong, you can intervene and stop it. This gives you the power to monitor and act.

### Live Log

Real-time scrolling feed of what the agent is doing right now. You see the actual work happening.

### Phase Detail View

Click on any phase dot to drill into it:

- What was built in that phase
- The reviewer's findings
- Test results
- The summary that got passed to the next phase

### The Queue

You've already prepped multiple builds using Tabs 1-3. They're lined up, ready to go.

- **Current build** is running — you can see it live
- **Next builds** are queued below, in order
- When current finishes, next one automatically starts
- You can click into any queued build to review it while the current one runs
- You can reorder the queue, push things back or forward
- While one build is running, you can be looking at and organizing the next one

### History

- Pull up any past completed build
- See all its phases, step into any phase to see what happened
- Compare past builds to current
- Mini-viewer that shows each tab's output in sequence for any build (rules used, phases, build plan, results)

---

## The Big Picture — How It All Fits Together

```
[Main AutoForge Nav Bar]
  DunkStack | Workspace | Dashboard | BUILD ORCHESTRATOR | YT Lab | Monitor

[Inside Build Orchestrator — Sub-tabs]
  Rule Set Builder | Phase Chunker | Build Planner | Operations Dashboard
```

**The flow:**

1. **Rule Set Builder** — You import all your source docs (coding standards, contracts, specs). AI helps you merge them into one clean rule set. This rule set goes into every build phase.

2. **Phase Chunker** — The token calculator does the math: given your model, your rules, and your testing needs, here's how many phases and how big each one can be. Then the AI splits the PRD into that many chunks, each one self-contained and testable.

3. **Build Planner** — You define which agents do what (coder, reviewer, tester), lay out the step-by-step sequence, configure hooks. Pick a preset for your build type or customize. This generates the actual build script.

4. **Operations Dashboard** — Hit go. Watch it build. Phase progress dots, live token gauge, scrolling log, agent status. Queue up future builds. Review past builds. Mission control.

**Each tab has its own AI chat with one focused objective.** The Rule Set Builder AI merges rules. The Phase Chunker AI splits PRDs. The Build Planner AI helps organize the sequence. They don't mix purposes.

**Everything is saved as a project.** Each tab's output is a saved entity. Tabs link together. Past projects are browsable. You can come back to any tab, any project, edit, version, and reuse.

**Presets and versioning throughout.** Build types (full build, feature add, reverse engineering) are presets with saved agent roles and sequences. Rule sets are reusable across projects. Phase chunker settings are adjustable and saved. Everything can be versioned — if the new version isn't working, roll back to what worked.

**The eventual pipeline:** Once the PRD maker is built (one of the first projects to build with this system), it slots in before Tab 1. Then the full pipeline becomes: Make PRD → Set Rules → Chunk Phases → Plan Build → Run and Monitor. But each piece works independently — you can bring your own PRD, use existing rules, or jump to any step.

---

## Future Addition: PRD Maker

Will be built as one of the first projects using this system. Once complete, it becomes Step 0 — the starting point before the Rule Set Builder. For now, PRDs are brought to the table manually. The PRD maker will eventually integrate into this same sub-tab navigation, likely as the first tab.

---

## Summary — One Sentence Per Tab

| Tab | What It Does |
|-----|-------------|
| **Rule Set Builder** | Merges multiple source documents into one reusable rule set that goes into every build phase |
| **Phase Chunker** | Does the token math and AI-splits the PRD into properly sized, testable build phases |
| **Build Planner** | Defines agent roles, build sequence, hooks, and generates the build script from presets |
| **Operations Dashboard** | Live mission control — phase tracking, token gauge, queue management, and build history |
