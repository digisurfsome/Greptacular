# Agent Prompting System -- The Complete Guide

How to orchestrate multiple AI agents to build a complete application, using nothing but a chat window.

---

## Table of Contents

1. [What This Is](#what-this-is)
2. [Why You Need This](#why-you-need-this)
3. [Two Ways to Build](#two-ways-to-build)
4. [Chunking Mode (The Simple Way)](#chunking-mode)
5. [Strategy Mode (The Powerful Way)](#strategy-mode)
6. [Your Four Foundation Documents](#your-four-foundation-documents)
7. [Writing Agent Prompts That Actually Work](#writing-agent-prompts-that-actually-work)
8. [Token Economics for Humans](#token-economics-for-humans)
9. [Common Mistakes](#common-mistakes)
10. [Quick Start (15 Minutes)](#quick-start)

---

## What This Is

You are getting a system that turns one person into a dev team.

Here is the problem: AI can write code. But it cannot build an entire application in a single conversation. The chat runs out of memory. The AI starts forgetting what it already built. The code turns into a mess where nothing connects to anything else.

This system solves that. You break your app into pieces, write a focused prompt for each piece, and hand each prompt to a separate AI chat session. Each session builds one part. The parts fit together because they all share the same blueprint documents.

**The result:** You run 3 agents in parallel, merge their work, run 3 more, merge again, run QA. What would take a solo developer weeks gets done in hours. What would take a dev team days gets done while you watch.

**This works with any AI chat interface.** Claude.ai, ChatGPT, Gemini, or whatever else you prefer. You are copy-pasting prompts into chat windows. That is all.

**This works for any application.** The examples in this repo are for a specific project (YT Strategy Lab), but the system is a template. Swap in your own app idea, your own features, your own architecture, and the same orchestration pattern applies.

---

## Why You Need This

### The Token Limit Problem

Every AI chat has a context window -- a maximum amount of text it can hold in its memory at once. Think of it like a whiteboard. The AI reads your prompt, reads the code it is writing, reads its own previous messages, and all of that fills up the whiteboard. Once the whiteboard is full, the AI starts dropping older information to make room for new information.

For a large application, you will hit this limit long before you finish building. The AI will forget files it created earlier. It will rewrite things it already wrote. It will introduce bugs because it cannot see the full picture anymore.

**The math is simple.** A 200K-token context window sounds like a lot. But after you account for the system prompt, the AI's own thinking, and the back-and-forth conversation, you realistically have about 60K tokens of usable space. A single feature with backend + frontend code can easily consume 20-40K tokens. Two or three features and you are at the wall.

### The Spaghetti Code Problem

Even if context windows were infinite, there is a second problem: AI writes better code when it has a focused task. Tell an AI "build me an entire project management app" and you get generic, loosely connected code. Tell it "build the task assignment module that follows this specific API pattern and reads from this specific database schema" and you get clean, precise code that fits into a larger system.

**Focused prompts produce better code.** Period.

### What This System Gives You

- **Parallel execution.** Multiple agents building different features at the same time.
- **Focused context.** Each agent only thinks about its one piece, not the whole app.
- **Shared architecture.** Foundation documents ensure every agent follows the same patterns, uses the same naming conventions, and builds for the same interfaces.
- **Predictable merges.** Because you control which files each agent touches, their work rarely conflicts.
- **Quality verification.** Dedicated QA agents review the combined work and fix integration issues.

---

## Two Ways to Build

You have two approaches. Pick the one that matches your project.

### Chunking Mode -- The Simple Way

**Best for:** Apps with 3-8 independent features. Projects where you want to get something working fast. People who are new to this system.

You divide your app into chunks. Each chunk is a self-contained piece of functionality. You write one prompt per chunk. You run the chunks one at a time (or in parallel if they do not overlap). Done.

**Think of it like this:** You are building a house. Chunking Mode means you hire one crew for the kitchen, one crew for the bathroom, one crew for the bedroom. Each crew works independently. They all follow the same building code (your shared documents), so everything connects when they are done.

### Strategy Mode -- The Powerful Way

**Best for:** Apps with 8+ features. Complex systems where features depend on each other. Projects where quality and architecture matter more than speed. People who want maximum control.

You create a full set of planning documents first -- vision, technical context, individual feature specs, and an orchestration plan. Then you execute in waves: Wave 1 builds the foundation features in parallel, you merge them, Wave 2 builds features that depend on Wave 1, you merge again, Wave 3 runs QA across everything.

**Think of it like this:** You are building a skyscraper. Strategy Mode means you have an architect, a general contractor, specialized crews, and an inspection team. The architect creates the blueprints. The general contractor sequences the work. The crews execute. The inspectors verify.

### When to Use Each

| Situation | Use |
|-----------|-----|
| Your app has fewer than 8 features | Chunking Mode |
| Features are mostly independent | Chunking Mode |
| You want to start building today | Chunking Mode |
| Your app has complex feature dependencies | Strategy Mode |
| Multiple features share the same files | Strategy Mode |
| You need enterprise-quality architecture | Strategy Mode |
| You are building something you plan to sell | Strategy Mode |

You can also start with Chunking Mode and graduate to Strategy Mode later. They are not mutually exclusive.

---

## Chunking Mode

### How It Works

1. Write a one-page description of your app (what it does, who it is for, what tech stack).
2. Break the app into 3-8 independent chunks.
3. Write one prompt per chunk.
4. Open a fresh AI chat for each chunk, paste the prompt, let it build.
5. Combine the outputs into your project.

### Step 1: Write Your App Description

This is a single document that every agent will read. It does not need to be fancy. It needs to answer three questions:

- **What is this app?** One paragraph.
- **What tech stack does it use?** Language, framework, database, styling.
- **What are the naming conventions?** How do you name files, functions, variables, components.

Here is a template you can copy and fill in:

---

**App Description Template**

```
APP NAME: [Your app name]

WHAT IT DOES:
[One paragraph describing the app, who uses it, what problem it solves]

TECH STACK:
- Frontend: [e.g., React with TypeScript, Tailwind CSS]
- Backend: [e.g., Python with FastAPI, or Node.js with Express]
- Database: [e.g., SQLite, PostgreSQL, localStorage]
- Other: [e.g., WebSockets for real-time updates]

NAMING CONVENTIONS:
- Files: [e.g., kebab-case for files, PascalCase for React components]
- Functions: [e.g., camelCase]
- Database tables: [e.g., snake_case]
- API routes: [e.g., /api/resource-name]

FOLDER STRUCTURE:
[List your project's folder structure so agents know where to put files]
```

---

### Step 2: Break Your App Into Chunks

A good chunk has these properties:

- **Self-contained.** It creates its own files and only lightly touches shared files (like a types file or a main router file).
- **Independently testable.** You can verify it works without the other chunks being done.
- **Clear boundaries.** You can list exactly which files it creates or modifies.

**Example:** Say you are building a project management app. Your chunks might be:

| Chunk | What It Builds | Files It Creates |
|-------|---------------|-----------------|
| 1. User Auth | Login, signup, sessions | auth routes, auth pages, user model |
| 2. Project CRUD | Create, read, update, delete projects | project routes, project pages, project model |
| 3. Task Board | Kanban board with drag-and-drop | task routes, board component, task model |
| 4. Notifications | Email and in-app notifications | notification service, notification component |
| 5. Dashboard | Overview page with charts | dashboard page, stats API |

Notice how each chunk owns its own files. Chunk 1 does not need Chunk 3 to be done first. They can all build independently as long as they follow the same app description.

### Step 3: Write One Prompt Per Chunk

Each chunk prompt follows this structure:

---

**Chunk Prompt Template**

```
You are building ONE feature of a larger application.

## The App
[Paste your app description here, or tell the agent to read a file]

## What You Are Building
[One paragraph describing this specific chunk]

## Files to Create
[Exact list of files this agent should create]

## Files to Modify
[Exact list of existing files this agent should add to -- be specific about what to add]

## Patterns to Follow
[Name specific patterns from the existing codebase, like "follow the same router
pattern as auth.py" or "use the same component structure as UserCard.tsx"]

## What NOT to Do
- Do not modify files outside your list
- Do not install new dependencies without asking
- Do not change the database schema for other features
- [Any other guardrails specific to your project]

## When You Are Done
Run [your lint/build commands] and fix any errors before finishing.
```

---

### Step 4: Run the Chunks

Open a fresh AI chat window for each chunk. Paste the prompt. Let the agent build.

**If chunks are independent:** Run them all at the same time in separate chat windows.

**If chunks have dependencies:** Run the foundation chunks first. Copy the files they created into your project. Then run the dependent chunks, making sure the files from the earlier chunks are available.

### Step 5: Combine the Outputs

Take the code from each agent and put it in your project. If two agents modified the same file (like a types file), you will need to manually combine those changes. This is usually straightforward -- each agent added different things to the same file.

### When Chunks Need to Talk to Each Other

Sometimes two chunks share a boundary. Chunk A creates data that Chunk B reads. In this case, define the interface between them in your app description:

```
SHARED INTERFACES:

The User model has these fields: id, email, name, role.
The Project model has these fields: id, name, ownerId, createdAt.
The Task model has these fields: id, title, projectId, assigneeId, status.

All API responses follow this shape:
{ data: T, error: string | null }
```

When every agent reads the same interface definitions, they will build code that connects properly without ever talking to each other.

---

## Strategy Mode

This is the full-power version. It requires more upfront planning, but it produces significantly better results for complex applications.

The YT Strategy Lab build (the files in this repo) is a complete, real-world example of Strategy Mode. Every document referenced below has a corresponding example file you can study.

### The Five Phases

1. **Create your foundation documents** (Vision + Context Primer + PRDs)
2. **Create the orchestration plan** (which agents, what order, what depends on what)
3. **Write individual agent prompts** (one per agent, following the 5-step template)
4. **Execute waves** (run agents in parallel, merge between waves)
5. **QA wave** (dedicated verification agents test the combined work)

### Phase 1: Create Your Foundation Documents

You need four documents before you write a single agent prompt. These are the shared knowledge base that every agent reads. They are the reason your agents produce code that works together.

See the section [Your Four Foundation Documents](#your-four-foundation-documents) below for exactly what goes in each one.

**Time estimate:** 2-4 hours for a medium-complexity app. Most of this time is thinking about your architecture, which you would have to do anyway.

### Phase 2: Create the Orchestration Plan

The orchestration plan is your execution roadmap. It answers:

- How many agents do you need?
- Which features does each agent build?
- Which agents can run at the same time? (agents that do not share files)
- Which agents must wait for others to finish? (dependency chains)
- How much of the context window will each agent use?

**Example from this repo:** See `00-ORCHESTRATION-GUIDE.md` in this folder. It lays out 8 agents across 3 waves:

- **Wave 1:** 3 agents running simultaneously (Auto-Processor, Screenshot Intelligence, Computer Use Engine). No dependencies between them.
- **Wave 2:** 3 agents running simultaneously (Batch Import, Live Viewer, Screen Recording). Each depends on something from Wave 1.
- **Wave 3:** 2 QA agents running simultaneously. They verify everything built in Waves 1 and 2.

**How to decide what goes in which wave:**

Draw your features as a tree. Features at the top (no dependencies) go in Wave 1. Features that depend on Wave 1 features go in Wave 2. Keep going until everything is placed. Then group features within each wave so that agents in the same wave do not modify the same files.

Here is the dependency tree from the YT Strategy Lab build:

```
Phase 1 (already done)
    |
    +-- Auto-Processor (Wave 1, Agent 1)
    |       |
    |       +-- Batch Import (Wave 2, Agent 4)
    |
    +-- Computer Use Engine (Wave 1, Agent 3)
    |       |
    |       +-- Live Viewer + Pause/Resume (Wave 2, Agent 5)
    |       |
    |       +-- Screen Recording (Wave 2, Agent 6)
    |
    +-- Screenshot Intelligence (Wave 1, Agent 2)  -- independent, no downstream deps
```

Features at the same depth level can run in the same wave.

### Phase 3: Write Individual Agent Prompts

Each agent gets its own prompt file. The prompt follows a specific 5-step template (covered in detail in [Writing Agent Prompts That Actually Work](#writing-agent-prompts-that-actually-work) below).

Every prompt file in this folder is a real example:

| File | What It Shows |
|------|--------------|
| `wave1-agent1-auto-processor.md` | A single-feature agent prompt (one feature, clean scope) |
| `wave2-agent4-batch-import-model-routing.md` | A multi-feature agent prompt (two features in one session) |
| `wave3-qa-agent-a-features.md` | A QA agent prompt (verification, not building) |

### Phase 4: Execute Waves

This is where the building happens.

**For each wave:**

1. Open a fresh AI chat window for each agent in the wave.
2. Copy and paste the agent's prompt into the chat.
3. Let the agent work. It will read the foundation documents, confirm its understanding, build the code, and verify it compiles.
4. When all agents in the wave are done, collect their code.
5. Combine all agent outputs into your project. This is the **merge point.**
6. Verify the combined code compiles and runs.
7. Move to the next wave.

**Why you must merge between waves:**

Wave 2 agents depend on code that Wave 1 agents built. If you skip the merge, Wave 2 agents will not have access to Wave 1's code. They will either fail or build incompatible substitutes.

**Handling merge conflicts (in plain language):**

Sometimes two agents in the same wave both added code to the same file. For example, Agent 1 added new types to `types.ts` and Agent 2 also added different types to `types.ts`. Both sets of types are valid -- they just need to be combined into one file.

This is almost always simple:
- Open the file.
- You will see one agent's additions.
- Find the other agent's version of the same file.
- Copy the additions from the second agent and paste them into the first version.
- Both sets of code are usually just appended to the file, so they do not actually conflict.

The orchestration plan includes a **Conflict Risk Matrix** (see `00-ORCHESTRATION-GUIDE.md` for an example) that tells you exactly which files might need this treatment and how hard the merge will be.

### Phase 5: QA Wave

After all build waves are done and merged, you run QA agents. These are separate chat sessions with a different kind of prompt. Instead of "build this feature," the prompt says "test these features and fix any bugs."

QA agents:
- Read all the same foundation documents as the build agents.
- Get a list of specific features to verify.
- Get specific test cases to execute (like "does the button appear after this action?").
- Fix any bugs they find.
- Produce a verification report.

See `wave3-qa-agent-a-features.md` and `wave3-qa-agent-b-execution.md` in this folder for real QA agent prompts.

**You can split QA across multiple agents** so each one has a manageable scope. In the YT Strategy Lab build, QA Agent A handles UI and backend features while QA Agent B handles the execution engine and Docker stack. They run in parallel.

---

## Your Four Foundation Documents

These are the documents every agent reads before writing code. They are what turns a collection of independent chat sessions into a coordinated team.

### 1. Vision Document (The WHY)

**What it does:** Prevents agents from making wrong assumptions about the purpose of your app.

**Why it matters:** Without a vision document, each agent invents its own understanding of what the app is for. Agent 1 might build a one-off tool. Agent 3 might build a platform. Agent 5 might optimize for a completely different user. The vision document aligns everyone.

**What goes in it:**
- What this app actually is (one paragraph, no jargon)
- Who it is for
- What problem it solves
- What it is NOT (common misunderstandings to prevent)
- Key architectural principles (like "every module must be self-contained" or "all data flows through the API")

**Example from this repo:** `docs/yt-strategies/VISION.md`

This vision document starts with the most important line: **"Every agent must read this before building anything."** It then spends several paragraphs explaining that YT Strategy Lab is a mini-app factory, NOT a single-purpose tool. Without this, agents would build hardcoded features instead of a flexible template system.

**To create yours:** Open a fresh AI chat and paste this prompt:

```
I am building an application. I need you to help me write a Vision Document
that I will share with AI coding agents who will build different parts of the app.

Here is what my app does:
[Describe your app in 2-3 paragraphs]

Here is what my app is NOT:
[List common misunderstandings]

Write a Vision Document that covers:
1. What this app actually is (clear, specific, no jargon)
2. Who it is for
3. What problem it solves
4. The key architectural principles (self-contained modules, etc.)
5. What it is NOT and what misconceptions to prevent

Start with the line: "Every agent must read this before building anything."
Keep it under 2 pages.
```

### 2. Context Primer (The Technical HOW)

**What it does:** Gives every agent the same technical vocabulary and codebase patterns.

**Why it matters:** Without a context primer, Agent 1 might name its API routes `/api/v1/users` while Agent 3 names its routes `/users/api`. Agent 2 might use camelCase while Agent 4 uses snake_case. The context primer is the style guide that prevents this drift.

**What goes in it:**
- Existing systems and what they do (a table is ideal)
- The dependency chain between features
- A glossary of project-specific terms
- Code patterns to follow (with actual code examples from your project)
- File location map (where things live in the project)
- Architectural decisions and WHY they were made
- What NOT to do (anti-patterns specific to your project)

**Example from this repo:** `docs/yt-strategies/CONTEXT_PRIMER.md`

This context primer is thorough. It includes a table of 12 existing systems, a dependency diagram, a glossary, code patterns for the FastAPI router, React components, API client, and data persistence, a complete file location map, 8 architectural decision records with reasoning, and a list of 12 explicit anti-patterns.

**To create yours:** This document takes more effort than the vision document because it requires actual knowledge of your codebase. If you have an existing project, open a chat and ask the AI to analyze it:

```
I need you to create a Context Primer document for my codebase.
This document will be shared with AI coding agents who will build new features.

Here is my project structure:
[Paste your folder structure]

Here are the key files and what they do:
[List your main files with one-line descriptions]

Here is an example of how I structure [API routes / components / models]:
[Paste one example]

Write a Context Primer that covers:
1. A table of existing systems/modules and what they do
2. Code patterns to follow (with examples from the codebase)
3. File naming and location conventions
4. Architectural decisions and WHY they were made
5. A glossary of project-specific terms
6. What NOT to do (anti-patterns to avoid)
```

If you are starting from scratch (no existing codebase), decide your tech stack and patterns upfront and write the context primer as the blueprint for what the codebase WILL look like.

### 3. PRDs -- Product Requirements Documents (The WHAT)

**What it does:** Gives each feature a complete specification so the agent knows exactly what to build.

**Why it matters:** "Build a notification system" is vague. "Build a notification system with these 4 API endpoints, these 3 UI components, this database schema, and these 6 edge cases" is buildable. PRDs are the difference between an agent that guesses and an agent that executes.

**What goes in it (per PRD):**
- What this feature does (one paragraph)
- User stories or use cases
- Technical specification (API endpoints, database changes, UI components)
- Edge cases and error handling
- What it depends on (other features that must exist first)
- Acceptance criteria (how do you know it is done)

**Example from this repo:** The `docs/yt-strategies/prds/` folder contains 9 PRDs, one per feature phase. Each one is a detailed specification that an agent can execute without asking clarifying questions.

**How many PRDs do you need?** One per feature or feature group. If your app has 6 features, you write 6 PRDs. If two features are small and closely related, you can combine them into one PRD (like the YT Strategy Lab did with Batch Import + Model Routing).

### 4. Orchestration Guide (The WHEN)

**What it does:** Maps out the execution sequence -- which agents run when, what depends on what, and how the pieces merge.

**Why it matters:** Without it, you run agents in the wrong order, create dependency conflicts, and waste time on features that cannot work until other features are done.

**What goes in it:**
- Architecture diagram (the dependency tree)
- Wave breakdown (which agents run in each wave)
- Token budget per agent (will the prompt + feature fit in the context window?)
- Files created by each agent (so you can spot potential merge conflicts)
- Conflict risk matrix (which files get modified by multiple agents)
- Merge strategy (what to do between waves)

**Example from this repo:** `00-ORCHESTRATION-GUIDE.md` in this folder. It is the most operational of the four documents -- less prose, more tables and diagrams.

**To create yours:** Once you have your PRDs and know your features, open a chat and paste:

```
I have these features to build for my app:
[List all features with one-line descriptions]

These are the dependencies between them:
[List which features depend on which]

These are the files each feature will create or modify:
[List files per feature]

Create an orchestration guide that:
1. Groups features into parallel waves (features with no shared dependencies)
2. Shows the execution order (Wave 1 -> merge -> Wave 2 -> merge -> QA)
3. Estimates token usage per agent (rough: small feature ~20K, medium ~35K, large ~45K)
4. Identifies files that multiple agents will modify (merge conflict risks)
5. Specifies the merge strategy between waves
```

---

## Writing Agent Prompts That Actually Work

Every agent prompt in this system follows a 5-step template. Each step exists for a specific reason. Skip a step and the quality drops measurably.

### The 5-Step Template

Here is the template, followed by an explanation of why each step matters.

---

**Agent Prompt Template**

```
# Build Agent [N] -- [Feature Name]

## What You Are Building

[One paragraph. What is this feature? What does it do in the context of the
larger app? What phase are you in?]

## Step 1: Read These Documents (In This Order)

Read these documents before writing any code:

1. Vision Document -- what this app is and is not:
   [paste the contents or tell the agent where to find it]

2. Context Primer -- technical patterns and architecture:
   [paste the contents or tell the agent where to find it]

3. Your PRD -- the specific feature you are building:
   [paste the contents or tell the agent where to find it]

## Step 2: Prove Understanding

Before writing code, briefly state:
1. What you are building (one paragraph, in your own words)
2. What files you will create or modify (complete list)
3. What existing patterns you will follow

## Step 3: Build

[Detailed file-by-file specification:]

### Backend
- File 1 (NEW) -- what it does, what patterns to follow
- File 2 (MODIFY) -- what to add, where to add it

### Frontend
- File 3 (NEW) -- what it does, what components to use
- File 4 (MODIFY) -- what to add

### Key Rules
- [Project-specific constraints from your Context Primer]

## Step 4: Quick Verification

After building, verify your code compiles and passes basic checks.
[Your project's lint/build/test commands go here]

## Step 5: Post-Build Verification

[Full testing protocol -- what to check end-to-end]

## Important

- Stay under 50% of the context window.
- [Any other constraints]
```

---

### Why Each Step Matters

**Step 1: Read These Documents (In This Order)**

This is not optional. Without this step, the agent starts coding immediately based on your one-paragraph description. It invents its own architecture, its own naming patterns, its own database schema. All of that will conflict with what the other agents are building.

The order matters too. Vision first (so the agent understands the big picture), Context Primer second (so it knows the patterns), PRD third (so it knows the details of its specific task). An agent that reads the PRD first without the vision will build the right feature in the wrong way.

**Step 2: Prove Understanding**

This is the secret weapon of the entire system.

Before the agent writes a single line of code, it must explain what it is about to build. This does two things:

1. **It catches misunderstandings before they become bugs.** If the agent says "I will create a new database table" and your Context Primer says "no database tables in V1, use localStorage," you catch it immediately instead of discovering it 2,000 lines of code later.

2. **It forces the agent to plan.** The act of listing every file it will create or modify forces the agent to think through the full scope before starting. This dramatically reduces the chance of "I forgot to update the router" or "I missed the types file" mistakes.

When you read the agent's Step 2 response, check it against your PRD and Context Primer. If anything is off, correct it right there. You are saving yourself from having to redo the entire build.

**Step 3: Build**

This is where you are most specific. Do not say "build the backend." Say "create `server/routers/processing.py` with a POST endpoint at `/api/process` that accepts a `ProcessRequest` body and returns a `ProcessResponse`." The more specific your build instructions, the less the agent has to guess.

List every file. Mark each one as NEW (create it) or MODIFY (add to an existing file). Specify what patterns to follow, ideally by referencing an existing file in the codebase ("follow the same pattern as `auth.py`").

**Step 4: Quick Verification**

Code that does not compile is code that does not ship. This step forces the agent to run your project's lint and build commands and fix any errors before moving on. Without it, agents will hand you code full of import errors, type mismatches, and syntax issues.

**Step 5: Post-Build Verification**

This goes beyond "does it compile" to "does it actually work." Can you click the button and see the expected result? Does the API return the right data? Do error cases get handled? This is where integration bugs get caught at the agent level instead of later in QA.

### Adapting the Template

You do not need to follow this template word for word. But you need every step to be present in some form. Here is the minimum:

- Agent reads shared context before coding.
- Agent explains its plan before coding.
- Agent has a detailed file list to work from.
- Agent verifies its code compiles.
- Agent tests that the feature works.

---

## Token Economics for Humans

### What Is a Token?

A token is roughly one word or a piece of a word. The sentence "The quick brown fox jumps" is about 5 tokens. A typical line of code is 10-15 tokens. A 200-line source file is about 2,000-3,000 tokens.

### The 50% Rule

AI models have a maximum context window (the total amount of text they can work with at once). For Claude, this is currently 200,000 tokens. For GPT-4, it varies by version.

**Never use more than 50% of the context window for your prompt + feature code.**

Why? Because the other 50% is consumed by:
- The AI's system prompt and internal instructions (~10-15K)
- The conversation history (your messages + the AI's responses) (~20-30K)
- The AI's "thinking" space (internal reasoning, planning) (~10-20K)

If your prompt + the code the agent writes + the foundation documents consume 80% of the context, the AI has no room to think. It starts making errors, forgetting earlier code, and producing lower quality output. 50% is the practical ceiling. 40% is comfortable. 30% is ideal.

### How to Estimate Your Budget

Here is a rough guide for estimating token usage:

| Content | Approximate Tokens |
|---------|-------------------|
| Your Vision Document | 2,000 - 5,000 |
| Your Context Primer | 5,000 - 15,000 |
| One PRD | 3,000 - 8,000 |
| The agent prompt itself | 1,000 - 3,000 |
| **Total fixed overhead** | **~11,000 - 31,000** |

That leaves roughly 60,000-90,000 tokens for the AI to read existing code, write new code, and think through problems.

A **small feature** (one new file, minor changes to 2-3 existing files) uses about 15,000-25,000 tokens of that space.

A **medium feature** (2-3 new files, changes to 4-5 existing files) uses about 25,000-40,000 tokens.

A **large feature** (5+ new files, significant changes to many existing files) uses about 40,000-55,000 tokens.

### What to Do When It Does Not Fit

If a feature is too large for a single agent session:

1. **Split the feature into two agents.** One builds the backend, the other builds the frontend. Or one builds the core logic, the other builds the edge cases.

2. **Reduce the foundation documents.** Instead of pasting the full Context Primer, paste only the sections relevant to this agent's feature. The Vision Document can usually stay full-length.

3. **Use a model with a larger context window.** Claude's 200K context is large. But if you are on a model with 128K or less, you will need to be more aggressive about splitting features.

### The Budget Table

The orchestration guide includes a budget table for each agent. Here is what the YT Strategy Lab's budget looks like:

```
Available after fixed overhead: ~61K tokens

Agent 1:  23K / 61K = 38%  -- comfortable
Agent 2:  19K / 61K = 31%  -- comfortable
Agent 3:  43K / 61K = 70%  -- tight but fits
Agent 4:  39K / 61K = 64%  -- moderate
Agent 5:  47K / 61K = 77%  -- tightest
Agent 6:  20K / 61K = 33%  -- comfortable
```

Agent 5 is at 77% of available space. That is tight. If it starts running into quality issues, you would split it into two agents. Agents 1, 2, and 6 have plenty of room and could potentially take on more scope.

---

## Common Mistakes

These will waste your time or ruin your build. Avoid all of them.

### 1. No Shared Context Document

**The mistake:** You write agent prompts that describe the feature but do not include (or reference) a shared context document with patterns, naming conventions, and architecture.

**What happens:** Agent 1 creates `api/routes/users.js`. Agent 2 creates `server/routers/user_router.py`. Agent 3 creates `backend/controllers/UserController.ts`. Three agents, three completely different architectures. Nothing connects.

**The fix:** Always write a Context Primer first. Every agent reads it before coding.

### 2. No "Prove Understanding" Step

**The mistake:** You go straight from "read these documents" to "build this feature."

**What happens:** The agent misinterprets your PRD and builds something slightly wrong. You do not find out until the end when the code does not work. You have to start over.

**The fix:** Always require the agent to explain its plan before coding. Review the plan. Correct misunderstandings before code gets written.

### 3. Agents That Modify the Same Files Without Coordination

**The mistake:** You assign Agent 1 and Agent 2 to both modify `types.ts` without noting this in the orchestration plan.

**What happens:** Both agents create different versions of the same file. When you try to combine their work, you have to manually figure out which changes to keep from each version.

**The fix:** Your orchestration plan should include a conflict risk matrix that lists every file modified by multiple agents. Keep agents in the same wave on different files whenever possible. When overlap is unavoidable, make it append-only (each agent adds to the end of the file, never changes existing code).

### 4. Skipping the Merge Between Waves

**The mistake:** You start Wave 2 agents before combining and verifying Wave 1's output.

**What happens:** Wave 2 agents cannot see Wave 1's code. They build on top of an imaginary foundation. When you merge everything at the end, nothing connects.

**The fix:** Always merge between waves. Verify the combined code compiles before starting the next wave.

### 5. No Verification Step

**The mistake:** The agent prompt does not include any instruction to verify the code compiles or works.

**What happens:** The agent hands you code with import errors, type mismatches, and missing dependencies. You spend more time debugging the agent's output than it would have taken to build the feature yourself.

**The fix:** Every agent prompt ends with a verification step. At minimum: lint + build. Ideally: lint + build + basic end-to-end testing.

### 6. One Giant Prompt Instead of Focused Prompts

**The mistake:** You write a single 50-page prompt that describes every feature of your app and give it to one agent session.

**What happens:** The agent runs out of context window halfway through. It forgets what it built in Feature 1 while building Feature 5. Code quality degrades linearly as the session gets longer.

**The fix:** One agent per feature (or small feature group). Each agent gets a focused, manageable prompt. The foundation documents handle coordination.

### 7. Telling the Agent WHAT but Not HOW

**The mistake:** Your prompt says "build a user authentication system" but does not specify which files to create, which patterns to follow, or which existing code to reference.

**What happens:** The agent invents its own architecture. It might be fine. It might be completely different from everything else in your project. You are gambling.

**The fix:** Be explicit about files, patterns, and constraints. "Create `server/routers/auth.py` following the same pattern as `server/routers/projects.py`" is 10 times better than "build auth."

### 8. Not Listing Files Each Agent Creates

**The mistake:** You let agents decide which files to create and where to put them.

**What happens:** One agent creates `utils/helpers.ts`, another creates `lib/helpers.ts`, another creates `shared/utils.ts`. Duplicate logic in three places with three different names.

**The fix:** Your prompt specifies the exact file path for every file the agent creates. The orchestration plan maps files to agents so there is no ambiguity.

---

## Quick Start

If you want to get started right now, here is the minimum viable setup. This uses Chunking Mode. You can graduate to Strategy Mode later.

### You Need 15 Minutes and 3 Documents

**Document 1: App Description (5 minutes)**

Open any text editor and write:

```
APP: [Your app name]

WHAT: [2-3 sentences about what it does and who uses it]

TECH: [Your tech stack -- e.g., "React + TypeScript frontend, Python FastAPI backend,
SQLite database, Tailwind CSS for styling"]

PATTERNS:
- API routes go in server/routers/ and are prefixed with /api/
- React components go in ui/src/components/
- Shared types go in ui/src/lib/types.ts
- [Add any other patterns you want to enforce]
```

**Document 2: Feature List (5 minutes)**

List every feature your app needs. For each one, write:
- One sentence describing it
- The files it would create

```
FEATURES:

1. User Auth -- login, signup, password reset
   Creates: server/routers/auth.py, ui/src/pages/LoginPage.tsx, ui/src/pages/SignupPage.tsx

2. Dashboard -- overview page with key metrics
   Creates: server/routers/dashboard.py, ui/src/pages/DashboardPage.tsx

3. [Next feature...]
```

**Document 3: Your First Agent Prompt (5 minutes)**

Pick the feature with the fewest dependencies (usually auth or the main data model). Copy this template and fill it in:

```
You are building one feature of a larger application.

## The App
[Paste your App Description here]

## What You Are Building
[Paste the one-sentence description of this feature]

## Files to Create
[List the files from your Feature List]

## Patterns to Follow
- Follow the naming conventions in the App Description above
- Use TypeScript for all frontend code
- Use Pydantic models for all API request/response bodies
- [Add patterns from your App Description]

## Step 1: Before you write any code, tell me:
1. What you are building (in your own words)
2. Every file you will create or modify
3. Any questions you have about the architecture

## Step 2: Build the feature. Create every file listed above.

## Step 3: Verify your code compiles. Fix any errors.
```

### Now Run It

1. Open Claude.ai, ChatGPT, or your preferred AI chat.
2. Paste the agent prompt.
3. Let the agent work through the steps.
4. Review the "Prove Understanding" response in Step 1. If anything looks wrong, correct it before the agent starts coding.
5. Collect the code.
6. Repeat for the next feature.

### Then Grow

Once you have built 2-3 features this way, you will naturally see where you need more structure:

- **Features are conflicting?** You need a Context Primer.
- **Agents are making wrong assumptions?** You need a Vision Document.
- **Features depend on each other?** You need an Orchestration Guide.
- **Quality is inconsistent?** You need PRDs with acceptance criteria.

Add these documents as you need them. You do not have to build the full Strategy Mode setup on day one. Start simple, add structure when the simple approach starts breaking down.

---

## How the Example Files Map to This System

Everything described in this guide has a working example in this repo. Here is how they connect:

| This Guide Says | Example File |
|----------------|-------------|
| Write a Vision Document | `docs/yt-strategies/VISION.md` |
| Write a Context Primer | `docs/yt-strategies/CONTEXT_PRIMER.md` |
| Write PRDs for each feature | `docs/yt-strategies/prds/01-09*.md` (9 PRDs) |
| Write an Orchestration Guide | `docs/yt-strategies/agent-prompts/00-ORCHESTRATION-GUIDE.md` |
| Write single-feature agent prompts | `wave1-agent1-auto-processor.md` |
| Write multi-feature agent prompts | `wave2-agent4-batch-import-model-routing.md` |
| Write QA agent prompts | `wave3-qa-agent-a-features.md`, `wave3-qa-agent-b-execution.md` |
| Create seed templates | `docs/yt-strategies/templates/ai-ad-agency-project-seed.json` |
| Create blank templates | `docs/yt-strategies/templates/blank-agency-template.json` |

Study these files. They are not theoretical examples. They are the actual documents used to orchestrate the build of a real application with 8 agents across 3 waves.

Adapt them for your own project. Change the names, change the features, change the tech stack. The structure stays the same.
