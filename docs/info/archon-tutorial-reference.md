# Archon Tutorial & Reference Guide

> Compiled from Cole Medin's introductory video and 3-hour livestream (April 2026).
> Archon is the first open-source harness builder for AI coding.

---

## Table of Contents

1. [What Is Archon?](#1-what-is-archon)
2. [Core Concepts](#2-core-concepts)
3. [Installation & Setup](#3-installation--setup)
4. [Running Workflows](#4-running-workflows)
5. [Parallel Execution](#5-parallel-execution)
6. [The Web UI](#6-the-web-ui)
7. [The Archon Skill](#7-the-archon-skill)
8. [Default Workflows That Ship with Archon](#8-default-workflows-that-ship-with-archon)
9. [Building Custom Workflows](#9-building-custom-workflows)
10. [Workflow YAML Structure](#10-workflow-yaml-structure)
11. [Node Types](#11-node-types)
12. [Model Selection Per Node](#12-model-selection-per-node)
13. [Session & Context Management Between Nodes](#13-session--context-management-between-nodes)
14. [Human-in-the-Loop](#14-human-in-the-loop)
15. [Adapters (Slack, Telegram, GitHub)](#15-adapters-slack-telegram-github)
16. [Registering Projects](#16-registering-projects)
17. [Token Efficiency Tips](#17-token-efficiency-tips)
18. [Using Your Anthropic Subscription](#18-using-your-anthropic-subscription)
19. [Using Local/Alternative Models](#19-using-localalternative-models)
20. [Dark Factory Concept](#20-dark-factory-concept)
21. [Tips & Patterns from Daily Use](#21-tips--patterns-from-daily-use)

---

## 1. What Is Archon?

Archon is an open-source **harness builder** for AI coding. It sits **above** your coding agent (Claude Code, Codex, etc.) and orchestrates multiple coding agent sessions together through workflows you define.

**Key distinction:** Archon is NOT a single harness (like BMAD, GSD, or the Ralph Loop). It's a **harness builder** — you use it to create any harness you want, custom to your own development process.

### The Evolution That Led Here

| Era | Focus | Scope |
|-----|-------|-------|
| **Prompt Engineering** (2022-2024) | Craft prompts to get the single best LLM output | Single turn |
| **Context Engineering** (2025) | Curate perfect context for a single coding agent session | Single session |
| **Harness Engineering** (2026) | Orchestrate multiple coding agent sessions with deterministic steps | Multi-session workflows |

Each evolution builds on the previous one — they don't replace each other.

### Why Harnesses Matter

- Without a harness: 6.7% PR acceptance rate from AI-generated code.
- With a harness: up to ~70% PR acceptance rate.
- The only difference is the harness — same underlying model.
- Stripe ships 1,300 AI-only PRs per week using their internal harness (Stripe Minions).
- ~40% of Claude Code's own codebase is harness-related code (agent teams, sub-agents).

### What Problem Archon Solves

Before Archon, you had your commands, skills, and rules, but YOU had to remember the order to use them, manually switch between coding sessions, and kick off each step. This is "AI shepherding." Archon packages your entire process into a single workflow you define once and run forever, reusable across projects.

---

## 2. Core Concepts

### Workflows
A workflow is your development process encoded as YAML. It's a sequence of **nodes** that Archon executes in order (with support for branching, loops, and parallel execution).

### Nodes
Each node is either:
- **A prompt** sent to a coding agent session (Claude Code, Codex, etc.)
- **A deterministic command** (bash, Python, or TypeScript script) that runs without AI

### The Hybrid Secret
The power comes from mixing AI-driven nodes with deterministic nodes. You guarantee certain things happen (like running tests) instead of hoping the coding agent remembers. This is what makes Stripe Minions so powerful and what Archon gives you.

### Work Trees
When running workflows (especially in parallel), Archon automatically creates git worktrees for isolation. Parallel workflows don't step on each other's toes, don't override changes, and don't create merge conflicts.

---

## 3. Installation & Setup

### Prerequisites
1. **A coding agent**: Claude Code (primary) or Codex
2. **GitHub CLI** (`gh`) — needed for most workflows that deal with issues/PRs
3. **Bun** — the setup process installs this automatically if missing

### Step-by-Step Installation

**Step 1: Clone the repo**
```bash
git clone https://github.com/coleam00/archon.git
cd archon
```

**Step 2: Open your coding agent in the Archon repo**
```bash
claude
```
(Or use `claude --dangerously-skip-permissions` if you don't want to approve each action.)

**Step 3: Say "set up Archon"**
That's literally it. The Archon skill loads automatically and walks you through everything:

1. **Prerequisite check** — verifies git, bun, etc. are installed
2. **First project registration** — asks what repo you want to use Archon with. Options:
   - Clone a GitHub repo
   - Specify a local path to an existing project
3. **Platform selection** — CLI is included by default. Optionally add:
   - GitHub (talk to Archon via GitHub issues)
   - Telegram
   - Slack
4. **CLI installation** — installs `archon` as a global command
5. **Credential setup** — opens a SEPARATE terminal (for security — API keys never go through the LLM):
   - **Database**: SQLite (easiest) or Postgres
   - **Coding agent**: Claude or Codex
   - **Authentication**: Anthropic subscription (global auth), OAuth token, or API key
   - **Platform API keys**: walks you through getting keys for each selected platform
   - **Allowed users**: comma-separated list of usernames allowed to invoke Archon
6. **Skill copy** — optionally copies the Archon skill into your target project
7. **Validation** — tests credentials and runs a test workflow to confirm everything works

**Step 4: Go back to the first Claude session and say "done"**
It will verify everything and confirm setup is complete.

### The Credential Setup Wizard (Separate Terminal)
If the automatic terminal doesn't open (common on VPS/certain OS), manually open a new terminal and run:
```bash
archon setup
```
This launches the same interactive wizard.

---

## 4. Running Workflows

### Method 1: From Your Project via CLI (Most Common)

Open Claude Code in your target project (must have the Archon skill copied in):
```
Use Archon to fix issue number 176
```
That's it. Claude loads the Archon skill, picks the right workflow, and invokes the CLI. The workflow runs as a **background process**.

### Method 2: From the Archon Repo

Open Claude Code in the Archon repo itself and point it at any codebase:
```
Use the fix GitHub issue workflow to fix issue #2 on [repo path or URL]
```
This automatically registers the repo with Archon if it isn't already.

### Method 3: From the Web UI

Start the web UI:
```
Spin up the front end and back end of Archon
```
(Run this from Claude Code inside the Archon repo.)

Then go to the web UI (default port 5178) and chat:
```
Fix GitHub issue 3 for the rag YouTube chat project
```
The web UI agent has context for all registered projects and workflows. It routes automatically.

### Method 4: From Slack/Telegram/GitHub

Once adapters are configured, you can talk to Archon directly from these platforms. Example in GitHub: `@archon fix this issue`.

### Monitoring Running Workflows

- **In Claude Code**: Workflows run as background processes. Press down arrow + enter to see logs. Ask Claude "give me a status update" at any time.
- **In the Web UI**: Dashboard shows all running workflows. Click into any for real-time logs and tool calls.
- **Using /loop**: You can use Claude Code's `/loop` command to have it check workflow progress on an interval (e.g., every 10 minutes).

---

## 5. Parallel Execution

This is one of Archon's killer features. You can run many workflows simultaneously.

### How to Run Multiple Workflows

Just list them:
```
Use Archon to fix GitHub issues 5, 7, 8, 9, 10, and 11
```
Archon spins up all six as background processes. Each runs in its own worktree — no conflicts.

### Chaining Parallel Steps

You can even chain parallel work:
```
Run these fix workflows in parallel. Wait until all are done. Then run the 
validate PR workflow on all the resulting PRs in parallel. Then view the PRs, 
address any issues, and push the changes.
```

### Real-World Scale
- One user reported running 30+ Archon workflows in parallel across 4 projects.
- Rate limits are the practical constraint, not Archon itself.

---

## 6. The Web UI

### Starting It
From Claude Code in the Archon repo:
```
Start the backend and frontend of Archon
```
Default runs on port **5178**.

### Features

- **Dashboard / Mission Control**: See all running, paused, and completed workflows at a glance.
- **Chat Interface**: An AI agent with context about all your registered projects and workflows. Ask it to run workflows, check status, or answer questions.
- **Workflow Logs**: Click into any workflow to see:
  - The node flow (which steps completed, where it currently is)
  - All tool calls from the coding agent in real time
  - Branching decisions that were made
  - Pause states for human-in-the-loop
- **Project Management**: Click "Add Project" to register new repos via GitHub URL or local path.
- **Workflow Viewer**: View and (soon) visually edit workflows — "think N8N but for software development."
- **Workflow Builder** (coming): Visual node-based workflow builder.

### What You Can Ask the Web UI Agent
```
What projects and workflows do I have?
Fix GitHub issue 3 for [project name]
Use the interactive PRD workflow for [project]
```
It knows all registered projects and all available workflows (defaults + custom).

---

## 7. The Archon Skill

The Archon skill is the bridge between your coding agent and the Archon CLI. It's a file you copy into any project's `.claude/skills/` directory.

### Location in Archon Repo
```
.claude/skills/   (inside the Archon repo)
```

### What It Does
- Teaches your coding agent how to use the `archon` CLI
- Includes descriptions of all available workflows so the agent can pick the right one
- Handles workflow invocation, monitoring, resuming, and status checks

### How to Copy It
Either:
- The setup wizard copies it for you
- Ask Claude: "Copy the Archon skill into [path to your project]"
- Manually copy the skill file

### Key Point
The `archon` CLI is global — it works from any directory. But your coding agent only knows HOW to use it if the skill is loaded. So every project you want to use Archon with needs the skill file.

### Using with Second Brain
Put the Archon skill in your second brain repo. Then your second brain can delegate coding work across any repo via Archon workflows.

---

## 8. Default Workflows That Ship with Archon

All of these are ready to use immediately after installation:

| Workflow | What It Does |
|----------|-------------|
| **Fix GitHub Issue** | Full pipeline: classify issue (bug vs feature) -> research -> investigate/plan -> implement -> validate -> create PR -> review |
| **Idea to PR** | Takes a feature idea through the full process to a pull request |
| **Interactive PRD** | Human-in-the-loop PRD creation — asks you questions in rounds to build out the spec |
| **Ralph Loop** | The Ralph Loop methodology as an Archon workflow |
| **PIV Loop** | Plan -> Implement -> Validate loop with fresh sessions between stages |
| **PR Review / Validation** | Comprehensive pull request review workflow |
| **Create Issues** | Investigate a problem and create a proper GitHub issue |
| **Adversarial Dev** | Adversarial development harness |
| **Archon Assist** | Basic single-node workflow for simple tasks |
| **Workflow Builder** | Meta-workflow that helps you create new workflows |

### Where They Live
```
.archon/   (inside the Archon repo)
```
These are also bundled into the CLI, so they're available from any repo.

### Two Uses for Default Workflows
1. **Use directly** — if one matches your process
2. **Reference for building custom ones** — your coding agent can study them to understand node parameters, loops, branching, etc.

---

## 9. Building Custom Workflows

### Method 1: Use the Workflow Builder Workflow (Recommended)
From Claude Code in the Archon repo:
```
Use the workflow builder workflow to help me make an Archon workflow
```
It asks you questions about what you want, researches existing workflows for patterns, then generates the YAML.

### Method 2: Describe What You Want
```
Load the Archon skill. I want to create a version of the GitHub fix issue 
workflow but specifically for Linear instead of GitHub. Ask me questions to 
make sure you understand my Linear setup and exactly how I want the workflow 
to function.
```

### Method 3: Take Inspiration from Existing Frameworks
```
Load the Archon skill. I want you to help me make an Archon workflow that 
takes heavy inspiration from GSD [link to repo]. Analyze the repo, dig deep 
into its process, and analyze existing Archon workflows to understand how to 
translate GSD's ideas into a new workflow.
```

### Tips for Building Workflows
- **Always have the agent ask you questions first** before generating the YAML. Reduces bad assumptions.
- **Start with inline prompts** in the YAML so you can see everything in one place. Later, extract long prompts into command files for cleanliness.
- **Iterate** — first run will likely reveal issues. Look at the logs, adjust prompting and node structure.
- **Use existing workflows as reference** — even for something totally custom, let the agent study default workflows for patterns.
- **Validate with CLI**: Archon CLI has a validate command to check YAML structure before running.

---

## 10. Workflow YAML Structure

Every workflow is a YAML file with this general structure:

```yaml
# Description — used by the skill to determine when to use this workflow
# (like a Claude Code skill description)
description: "Use this workflow when the user wants to fix a GitHub issue..."

# Default provider and model
provider: claude
model: sonnet

# The nodes — step by step
nodes:
  - id: classify
    prompt: "Classify this issue as a bug or feature request..."
    model: haiku  # Override model for this specific node
    
  - id: research
    command: archon-web-research  # Reference external command file
    
  - id: investigate
    prompt: "Investigate the root cause..."
    depends_on: [classify, research]  # Only runs after these complete
    condition: "classify.output == 'bug'"  # Branching logic
    
  - id: plan
    prompt: "Create a development plan..."
    condition: "classify.output == 'feature'"
    
  - id: implement
    command: archon-fix-issue
    session: fresh  # Start a brand new coding agent session
    
  - id: validate
    type: deterministic  # No AI — runs a script
    script: "npm test && npm run lint"
    
  - id: human_review
    type: human_approval
    message: "Review the implementation. Approve or provide feedback."
    
  - id: create_pr
    prompt: "Create a pull request with a clear description..."
    depends_on: [human_review]
```

### Key YAML Parameters

| Parameter | Purpose |
|-----------|---------|
| `description` | Tells the agent when to use this workflow (like a skill trigger) |
| `provider` | Which coding agent (claude, codex) |
| `model` | Default model for all nodes |
| `nodes[].model` | Override model for a specific node |
| `nodes[].prompt` | Inline prompt to send to the coding agent |
| `nodes[].command` | Reference to an external command/prompt file |
| `nodes[].depends_on` | Dependencies — waits for these nodes to complete first |
| `nodes[].condition` | Branching logic based on prior node output |
| `nodes[].session` | `fresh` = new session, `continue` = same session as prior node |
| `nodes[].type` | `deterministic` for scripts, `human_approval` for gates |

### Commands (External Prompt Files)
Long prompts can be stored as separate markdown files in the commands folder:
```
.archon/commands/archon-fix-issue.md
.archon/commands/archon-web-research.md
```
Referenced in YAML with: `command: archon-fix-issue`

These work exactly like Claude Code skills/commands — just longer prompts loaded at the right time.

---

## 11. Node Types

### Prompt Nodes (AI-Driven)
Send a prompt into a coding agent session. The agent does the work with its full toolkit (file editing, bash, search, etc.).

```yaml
- id: investigate
  prompt: "Investigate the issue by reading the codebase..."
  model: sonnet
```

### Deterministic Nodes (No AI)
Run a script guaranteed — no AI deciding whether to do it.

```yaml
- id: run_tests
  type: deterministic
  script: "npm test && npm run lint && npm run build"
```

**This is crucial.** Coding agents sometimes forget or skip validation steps. Deterministic nodes guarantee your tests/linting/builds always run.

### Human Approval Nodes
Pause the workflow and wait for human input.

```yaml
- id: review_plan
  type: human_approval
  message: "Here is the plan. Approve or provide feedback."
```

### Command Nodes
Reference an external prompt file instead of inline.

```yaml
- id: research
  command: archon-web-research
```

---

## 12. Model Selection Per Node

One of the most powerful token-saving features. You set a default model for the workflow, then override per node.

```yaml
model: sonnet  # Default for all nodes

nodes:
  - id: classify
    model: haiku      # Classification doesn't need powerful reasoning
    
  - id: research
    # No model specified — uses default (sonnet)
    
  - id: implement
    model: opus       # Only implementation gets the big model
    
  - id: review
    model: haiku      # Review can be lighter
```

### Why This Matters
- Cole reports better results using Sonnet with an Archon workflow than using Opus alone in Claude Code
- The harness elevates the model's capabilities
- Using Haiku for classification/simple nodes dramatically reduces token usage
- A full fix-GitHub-issue workflow uses less than 20% of a 5-hour rate limit

---

## 13. Session & Context Management Between Nodes

### Fresh vs. Continue Sessions

Each node can either:
- **`session: fresh`** — Start a brand new coding agent session (clean context)
- **`session: continue`** — Continue the conversation from the previous node

**Best practice:** Use fresh sessions between major phases (planning -> implementation) to avoid bias buildup. Your planning session accumulates context that can bias the implementation.

### Passing Context Between Fresh Sessions — The Artifact Directory

When using fresh sessions, pass context through artifacts:

1. **Planning node** outputs a plan to the artifact directory
2. **Implementation node** (fresh session) is prompted to read the plan from the artifact directory

```yaml
- id: plan
  prompt: "Create a detailed plan. Save it to the artifact directory."
  session: fresh

- id: implement
  prompt: "Read the plan from the artifact directory. Implement it."
  session: fresh  # Clean context, reads plan as artifact
```

The artifact directory is a workflow primitive — Archon manages it per workflow execution.

### When to Use Continue
- When the next node needs the full conversation context
- When you're switching models but want to keep the conversation
- For iterative loops where context accumulates usefully

### When to Use Fresh
- Between planning and implementation (avoid bias)
- When the previous session is bloated with context you don't need
- When injecting different skills/MCPs that might conflict

---

## 14. Human-in-the-Loop

### Adding Approval Gates
You can inject yourself at any point in a workflow:

```yaml
- id: human_review
  type: human_approval
  message: "Review the plan and approve or provide feedback."
```

### How It Works
1. Workflow pauses at the approval node
2. In the Web UI, the workflow shows a "paused" state
3. You review the output (plan, code, etc.)
4. You either approve (workflow continues) or provide feedback (workflow loops back)
5. From CLI: Claude Code reads the pause state and relays the question to you

### Feedback Loops
You can create loops where the agent iterates based on your feedback:
- Agent creates a plan -> you review -> you say "add more validation" -> agent revises -> you approve -> workflow continues

### Where to Put Approval Gates
- After planning (before implementation starts)
- After implementation (before PR creation)
- After the final review
- Anywhere you want control — it's your workflow

### The Philosophy
Archon is NOT about removing you from the loop. It's about letting you choose WHERE you're in the loop. You can be hands-off (Ralph Loop style) or hands-on (approve every step).

---

## 15. Adapters (Slack, Telegram, GitHub)

Archon supports multiple interfaces for interacting with workflows:

| Adapter | How It Works |
|---------|-------------|
| **CLI** | Always included. Run from any terminal. Best for local use. |
| **Web UI** | Chat interface + dashboard. Good for monitoring and visual management. |
| **GitHub** | Comment `@archon fix this issue` on any issue. Archon responds in the thread. |
| **Slack** | Message Archon in a Slack channel. Each thread = separate conversation. |
| **Telegram** | Chat with Archon bot. Good for mobile/remote triggering. |

### Security
- You define a list of allowed users per platform
- Only authorized users can invoke Archon (prevents random people spending your tokens on public repos)
- Mention name is configurable (default: `@archon`)

### All Adapters Support
- Parallel execution
- Conversation management
- Workflow monitoring

---

## 16. Registering Projects

Archon needs to know about your projects. Three ways to register:

### Automatic Registration
Run any Archon workflow on a repo for the first time — it auto-registers.

### Via Web UI
Click "Add Project" in the web UI. Provide GitHub URL or local path.

### During Setup
The setup wizard registers your first project.

### What Registration Does
- Stores the project in Archon's database (SQLite or Postgres)
- Makes it available in the Web UI agent's context
- Enables the agent to route requests to the right repo

---

## 17. Token Efficiency Tips

### From Cole's Real Usage Data
- Running 4 fix-GitHub-issue workflows + 4 validate-PR workflows + additional prompting used ~43% of a 5-hour rate limit on the $200/month plan.
- Individual fix-GitHub-issue workflow is "pretty token efficient for how much it's actually doing."
- You could run the fix-GitHub-issue workflow "at least a couple dozen times" before hitting the 5-hour limit.

### Strategies
1. **Use Haiku for classification, research, and review nodes** — save Opus/Sonnet for implementation
2. **Use fresh sessions** between major phases to keep context lean
3. **Extract long prompts into command files** — they only load when that node executes
4. **Inject skills/MCPs only where needed** — not every node needs every tool
5. **Use Sonnet as default** — with a good harness, Sonnet often outperforms standalone Opus
6. **Run deterministic nodes for validation** — cheaper than having the AI decide whether to test

---

## 18. Using Your Anthropic Subscription

**You ARE allowed to use your Anthropic subscription (Max plan) with Archon.** This has been explicitly confirmed by Boris Chernny (creator of Claude Code).

### The Rule
- Anthropic subscription is allowed with the Claude Agent SDK for **personal use**
- Archon runs locally on your machine and uses the Claude Agent SDK = personal use = allowed
- This is different from third-party tools (Open Claw, Open Code) that do workarounds to use the subscription — those violate ToS

### What's NOT Allowed
- Deploying an agent to a production platform where OTHER people use YOUR subscription
- Third-party tools that circumvent the SDK to use subscription auth

### How to Set Up
During the credential wizard, choose "Use global auth" — it uses your existing Claude Code authentication. No separate API key needed.

---

## 19. Using Local/Alternative Models

### Via Claude Code's Provider Support
Claude Code can integrate with:
- **Ollama** for local models (direct integration)
- **MiniMax API** (e.g., MiniMax M2.7)
- **Other providers** via Claude Code's configuration

### Via PI Agent SDK (Coming Soon)
PI makes it easy to use any model. Once Archon supports PI as a coding agent, local model usage becomes even simpler.

### Real-World Example
- Cole has tested MiniMax M2.7 with Archon workflows
- Community members have used Gemma 4 to drive Archon workflows
- Results aren't as good as Opus, but with a good harness, smaller models still produce solid results

### How to Configure
Change the model in Claude Code's settings or in the workflow YAML's model field.

---

## 20. Dark Factory Concept

A **dark factory** is a codebase that self-evolves — AI handles ALL code writing, reviewing, PR management, and releases. No human writes or reviews code. Humans only create issues (bugs/features).

### Cole's Dark Factory Experiment
- Public GitHub repo managed entirely by Archon workflows
- Archon workflows handle: issue triage, implementation, code review, PR management, releases, deployment
- Anyone can create an issue; Archon determines if it should be addressed and handles it automatically
- Use case: A "chat with my YouTube content" RAG application

### The Archon Workflows Involved
- **Issue triage** — classify and prioritize incoming issues
- **Implementation** — full GSD/PIV-style development
- **Review** — automated code review
- **Release management** — handle versioning and deployment

### Important Note
This is an **experiment** — Cole doesn't recommend this for production software where reliability matters. The point is to push limits and see what's possible.

---

## 21. Tips & Patterns from Daily Use

### Cole's Daily Pattern
1. File work items as GitHub issues (bugs AND features)
2. Open Claude Code in the project (with Archon skill)
3. "Use Archon to fix issues 5, 7, 8, 9, 10, 11" — all in parallel
4. Monitor in Web UI or ask Claude for status updates
5. Review resulting PRs
6. Run validate-PR workflows on all PRs in parallel
7. Address feedback, merge

### Ask the Agent to Ask YOU Questions
Before building a workflow:
```
Ask me questions to make sure you understand my setup and exactly 
how I want the workflow to function
```
This reduces assumptions and produces better first-draft workflows.

### Git Log as Long-Term Memory
Use git commits and GitHub issues as your coding agent's long-term memory. The git log is version-controlled, searchable, and always available.

### Don't Abandon What You Already Have
- Your existing skills, commands, and rules all work inside Archon workflows
- Archon doesn't replace your process — it packages it
- You can reference skills and MCPs per-node

### Workflow Iteration Pattern
1. Build the workflow (using workflow builder or manual YAML)
2. Run the validate CLI command to check structure
3. Run it on a test case
4. Check logs in Web UI for issues
5. Adjust prompts and node structure
6. Repeat

### Resuming Interrupted Workflows
If a workflow gets interrupted:
- It can be resumed later via the CLI
- The workflow picks up from the last interrupted node
- Just tell Claude: "Resume these workflows"

### The Codebase Architecture is Clean
Archon was architected with generic interfaces so adding new adapters (Slack, GitHub) or coding agents (PI, Codex) is easy. Claude Code can often one-shot new integrations by following existing patterns.

---

## Quick Reference Card

| I want to... | Do this |
|---|---|
| Install Archon | Clone repo, open Claude Code, say "set up Archon" |
| Fix a GitHub issue | "Use Archon to fix issue #123" |
| Fix many issues at once | "Use Archon to fix issues 1, 2, 3, 4, 5" |
| Create a PRD | "Use the interactive PRD workflow" |
| Build a custom workflow | "Use the workflow builder workflow to help me make an Archon workflow" |
| Start the Web UI | (In Archon repo) "Start the backend and frontend of Archon" |
| Register a new project | Web UI "Add Project" button, or just run a workflow on the repo |
| Copy skill to a project | "Copy the Archon skill into [path]" |
| Check workflow status | "Give me a status update" or check Web UI dashboard |
| Review PR | "Use the validate PR workflow on PR #456" |
| See all workflows/projects | (In Web UI) "What projects and workflows do I have?" |
| Change model for a node | Edit the YAML: add `model: haiku` to the node |
| Add human approval | Add a `type: human_approval` node in the YAML |
| Use with Second Brain | Copy Archon skill into second brain repo |

---

## Links

- **Archon Repository**: https://github.com/coleam00/archon
- **GSD (referenced framework)**: Search GitHub for "GSD spec driven development"
- **Archon Skill Location**: `.claude/skills/` in the Archon repo
- **Default Workflows Location**: `.archon/` in the Archon repo
- **Web UI Default Port**: 5178
