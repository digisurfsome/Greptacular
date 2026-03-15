# DunkStack + Agent OS Operator's Manual

Version 1.0 -- February 2026

This manual covers everything you need to operate the DunkStack file-based context mechanism and the Agent OS PRD creation system end-to-end. It is written for a first-time tester who has access to the AutoForge server but has never interacted with either system before.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Step-by-Step Setup Walkthrough](#2-step-by-step-setup-walkthrough)
3. [The .agent Directory Structure](#3-the-agent-directory-structure)
4. [DunkStack Operations](#4-dunkstack-operations)
5. [Agent OS Workflow](#5-agent-os-workflow)
6. [Testing Each Stage](#6-testing-each-stage)
7. [REST API Reference](#7-rest-api-reference)
8. [WebSocket Protocol](#8-websocket-protocol)
9. [The Handoff](#9-the-handoff)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (for UI development only; not required for API testing)
- A registered project in the AutoForge registry (create one via the UI or CLI first)

### Starting the Server

**From source (Linux/macOS):**

```bash
cd /path/to/Greptacular
./start_ui.sh
```

**From source (Windows):**

```cmd
cd C:\path\to\Greptacular
start_ui.bat
```

**Manual startup (any platform):**

```bash
cd /path/to/Greptacular
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
python start_ui.py --port 8888
```

The server starts on `http://127.0.0.1:8888` by default.

### Verify the Server Is Running

```bash
curl http://127.0.0.1:8888/api/health
```

Expected response:

```json
{"status": "healthy"}
```

### Key URLs

| Purpose | URL |
|---------|-----|
| Health check | `GET http://127.0.0.1:8888/api/health` |
| DunkStack API root | `/api/dunkstack/...` |
| Agent OS API root | `/api/agent-os/...` |
| DunkStack WebSocket | `ws://127.0.0.1:8888/api/dunkstack/ws` |
| Agent OS WebSocket | `ws://127.0.0.1:8888/api/agent-os/ws/{project_name}` |
| Web UI (React app) | `http://127.0.0.1:8888/` |

### What You Need Before Testing

1. **A project registered in AutoForge.** The simplest way is to use the Web UI to create one, or register a directory manually through the projects API.
2. **The project name.** Both systems use `project_name` as a query parameter (DunkStack) or path parameter (Agent OS) to scope all operations to a specific project directory.

---

## 2. Step-by-Step Setup Walkthrough

This section walks you through setting up DunkStack from scratch -- from "I just cloned the repo" to "it's running and I'm talking to the agent." Follow these steps in order.

### Step 1: Start the Server

```bash
# Clone and enter the repo
cd /path/to/Greptacular

# Option A: Use the start script (recommended)
./start_ui.sh          # Linux/macOS
start_ui.bat           # Windows

# Option B: Manual start
python -m venv venv
source venv/bin/activate         # Linux/macOS
# venv\Scripts\activate          # Windows
pip install -r requirements.txt
cd ui && npm install && npm run build && cd ..
python start_ui.py --port 8888
```

Verify: `curl http://127.0.0.1:8888/api/health` should return `{"status": "healthy"}`.

### Step 2: Create or Select a Project

DunkStack operates on **AutoForge projects**. You need at least one.

**Via the UI:** Go to `http://127.0.0.1:8888` -> click "New Project" -> give it a name and directory.

**Via the API:**
```bash
curl -X POST "http://127.0.0.1:8888/api/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "path": "/path/to/my-app"}'
```

### Step 3: Initialize the .agent/ Directory

The `.agent/` directory holds all DunkStack and Agent OS files. It gets created automatically when the backend first touches a project, but you can also trigger it manually.

**Automatic:** Visit the DunkStack page (`http://127.0.0.1:8888/#/dunkstack`) and select your project. The backend creates the directory on the first API call.

**Manual (via API):**
```bash
# Any DunkStack endpoint will create .agent/ if it doesn't exist
curl "http://127.0.0.1:8888/api/dunkstack/config?project_name=my-app"
```

**Manual (via Agent OS):**
```bash
# Agent OS has its own init that creates the full tree
curl -X POST "http://127.0.0.1:8888/api/agent-os/standards/my-app/infer"
```

### Step 4: Understand the Two File Categories

There are two categories of files in `.agent/`:

#### Category A: Universal Files (Same for Every Project)

These files are **templates** -- they have the same initial content regardless of what app you're building. They ship with the repo at `.agent/` in the project root and get copied or created automatically.

| File | Purpose | Repo Location (Template) |
|------|---------|--------------------------|
| `system_prompt.md` | Agent operating protocol (file-based mode rules) | `.agent/system_prompt.md` |
| `index.md` | Master file map (agent reads first each session) | `.agent/index.md` |
| `working_memory.md` | Agent's current task, state, next steps | `.agent/working_memory.md` |
| `bridge.md` | Session continuity (read on startup, then deleted) | `.agent/bridge.md` |
| `comms/to_human.md` | Agent -> human messages (append-only) | `.agent/comms/to_human.md` |
| `comms/from_human.md` | Human -> agent messages (read-only for agent) | `.agent/comms/from_human.md` |
| `comms/control.md` | Session mode (idle/continue/autopilot) | `.agent/comms/control.md` |
| `settings/config.yml` | Safety thresholds, mode, API settings | `.agent/settings/config.yml` |
| `progress/build_log.md` | Append-only build log | `.agent/progress/build_log.md` |

**Where to find them in the repo:** All these templates live at `/home/user/Greptacular/.agent/` in the repo root. They are the "blank slate" versions.

#### Category B: Project-Specific Files (Generated per Project)

These files are **generated** by Agent OS during the PRD creation process. They're different for every project because they contain your app's specific information.

| File | Purpose | When It's Created |
|------|---------|-------------------|
| `product/vision.md` | App vision, problem statement, success | Stage 3: Product Discovery |
| `product/target-users.md` | Who uses it, their needs | Stage 3: Product Discovery |
| `product/use-cases.md` | Core and secondary use cases | Stage 3: Product Discovery |
| `product/roadmap.md` | MVP, v1.1, and future features | Stage 3: Product Discovery |
| `product/constraints.md` | Hard limits (budget, tech, timeline) | Stage 3: Product Discovery |
| `product/competitive-context.md` | What exists today, what's different | Stage 3: Product Discovery |
| `specs/feature-001-*.md` | Per-feature specification | Stage 6: Spec Generation |
| `knowledge/context-primer.md` | Build agent's first-read briefing | Stage 8: Handoff |
| `scope_boundary.md` | In-scope vs out-of-scope features | Stage 8: Handoff |
| `../agent-os/standards/*.md` | Tech stack, coding style, quality bars | Stage 2: Standards |

These are **created by the system** -- you don't need to place them manually. Agent OS generates them as you go through the PRD workflow.

### Step 5: Copy Universal Template Files to Your Project

If DunkStack auto-creation didn't populate all the files (or you're setting up manually), copy the templates from the repo root:

```bash
# Set your project directory
PROJECT_DIR="/path/to/my-app"

# Create the directory structure
mkdir -p "$PROJECT_DIR/.agent/comms"
mkdir -p "$PROJECT_DIR/.agent/knowledge"
mkdir -p "$PROJECT_DIR/.agent/output"
mkdir -p "$PROJECT_DIR/.agent/progress"
mkdir -p "$PROJECT_DIR/.agent/settings"
mkdir -p "$PROJECT_DIR/.agent/intake"
mkdir -p "$PROJECT_DIR/.agent/intake_staging"
mkdir -p "$PROJECT_DIR/.agent/analytics/reports"
mkdir -p "$PROJECT_DIR/agent-os/standards"

# Copy universal template files from the repo
REPO_DIR="/path/to/Greptacular"

cp "$REPO_DIR/.agent/system_prompt.md"         "$PROJECT_DIR/.agent/system_prompt.md"
cp "$REPO_DIR/.agent/index.md"                 "$PROJECT_DIR/.agent/index.md"
cp "$REPO_DIR/.agent/working_memory.md"        "$PROJECT_DIR/.agent/working_memory.md"
cp "$REPO_DIR/.agent/bridge.md"                "$PROJECT_DIR/.agent/bridge.md"
cp "$REPO_DIR/.agent/comms/to_human.md"        "$PROJECT_DIR/.agent/comms/to_human.md"
cp "$REPO_DIR/.agent/comms/from_human.md"      "$PROJECT_DIR/.agent/comms/from_human.md"
cp "$REPO_DIR/.agent/comms/control.md"         "$PROJECT_DIR/.agent/comms/control.md"
cp "$REPO_DIR/.agent/settings/config.yml"      "$PROJECT_DIR/.agent/settings/config.yml"
cp "$REPO_DIR/.agent/progress/build_log.md"    "$PROJECT_DIR/.agent/progress/build_log.md"
```

**Or, if you're lazy:** Just use the DunkStack UI. It creates everything automatically on first access.

### Step 6: Open the DunkStack Dashboard

1. Open `http://127.0.0.1:8888/#/dunkstack` in your browser
2. Select your project from the left sidebar
3. You should see:
   - **Center panel:** Comms Chat (empty, ready for messages)
   - **Top bar:** Model preset pills (Opus 4.6 · 200K selected by default)
   - **Context Gauge:** Green bar at 0% (no tokens used yet)

### Step 7: Pick Your Model Preset

Click one of the model pills in the top bar:

| Preset | Best For | Context Window |
|--------|----------|---------------|
| **Opus 4.6 · 200K** | Fast iteration, testing | 200K tokens |
| **Opus 4.6 · 1M** | Large codebases, deep analysis | 1M tokens |
| **Sonnet 4.6 · 1M** | Cost-effective, full context | 1M tokens |

This updates both the frontend gauge and the backend `config.yml` so the agent knows which model/window to respect.

### Step 8: Send Your First Message

Type a message in the center panel input and press Enter. This writes to `.agent/comms/from_human.md`. The agent reads this file every turn.

Example first messages:
- "Start building the auth feature"
- "Read the project specs and tell me your plan"
- "Focus on feature #1 first"

### Step 9: Set the Control Mode

In the Safety panel (shield icon, top bar), set the mode:

- **Idle** (default) -- Agent waits for instructions after each task
- **Continue** -- Agent automatically picks up the next feature
- **Autopilot** -- Full autonomous mode, works through the entire backlog

For first-time testing, start with **Idle** so you can see what happens after each task.

### Step 10: Use Agent OS to Create a PRD (Optional)

If you want to create a full PRD before building:

1. Click the **Sparkles** button in the top bar to open Agent OS
2. Start in the **Intake Dock** -- paste your app description or upload files
3. Walk through all stages: Standards -> Product -> Features -> Gaps -> Specs -> Handoff
4. When complete, the system generates `features.db` and the build agent can start

### Quick Reference: File Finder

If you need to manually find or edit any file, here's where everything lives in the repo:

| What You Need | Where to Find It |
|---------------|-----------------|
| DunkStack config template | `Greptacular/.agent/settings/config.yml` |
| Agent operating protocol | `Greptacular/.agent/system_prompt.md` |
| File index template | `Greptacular/.agent/index.md` |
| Working memory template | `Greptacular/.agent/working_memory.md` |
| Bridge template | `Greptacular/.agent/bridge.md` |
| Comms: to_human template | `Greptacular/.agent/comms/to_human.md` |
| Comms: from_human template | `Greptacular/.agent/comms/from_human.md` |
| Comms: control template | `Greptacular/.agent/comms/control.md` |
| Build log template | `Greptacular/.agent/progress/build_log.md` |
| Implementation plan | `Greptacular/.agent/output/implementation_plan.md` |
| Standards templates (6 files) | `Greptacular/server/templates/agent-os/standards/` |
| Product templates (6 files) | `Greptacular/server/templates/agent-os/product/` |
| Feature spec template | `Greptacular/server/templates/agent-os/specs/` |
| DunkStack router (backend) | `Greptacular/server/routers/dunkstack.py` |
| Agent OS router (backend) | `Greptacular/server/routers/agent_os.py` |
| DunkStack page (frontend) | `Greptacular/ui/src/pages/DunkStackPage.tsx` |
| DunkStack hook (frontend) | `Greptacular/ui/src/hooks/useDunkStack.ts` |
| Full CLI manual | `Greptacular/DUNKSTACK_MANUAL.md` |

---

## 3. The .agent Directory Structure

When Agent OS initializes for a project, it creates a complete directory tree under `{project_dir}/.agent/`. Here is every subdirectory and file, with its purpose:

```
{project_dir}/
  .agent/
    comms/                    # DunkStack communication files
      from_human.md           # Human writes messages here; agent reads only
      to_human.md             # Agent writes messages here; human reads only
      control.md              # Session control state (idle/continue/autopilot)
    knowledge/                # Reference material and context documents
      context-primer.md       # Build agent's first-read briefing (generated by handoff)
    product/                  # Product layer documents (6 files)
      vision.md               # Core purpose, problem statement, success definition
      target-users.md         # Primary users, user needs, user context
      use-cases.md            # Core and secondary use cases
      roadmap.md              # MVP features, v1.1 features, future
      constraints.md          # Hard constraints, technical constraints, timeline
      competitive-context.md  # Current alternatives, differentiators, opportunities
    specs/                    # Per-feature specification files
      feature-001-auth.md     # Example: spec for feature #1
      feature-002-dashboard.md
    intake/                   # Raw user input files (intake stage)
    intake_staging/           # Staging area for uploaded/pasted files (Stage 0)
      manifest.json           # Tracks all staged files with metadata and tags
    progress/                 # Build progress tracking
      build_log.md            # Append-only log of bridge saves and milestones
    settings/                 # Configuration files
      config.yml              # Safety thresholds, mode settings, API config
    output/                   # Agent output artifacts
    analytics/                # Analytics data
      reports/                # Generated reports
    scope_boundary.md         # What is in/out of scope (MVP vs future)
    working_memory.md         # Agent's scratchpad for current session
    index.md                  # File index for the agent
    bridge.md                 # Bridge save state for session continuity
  agent-os/
    standards/                # Standards layer (6 files)
      technology-stack.md     # Languages, frontend, backend, database, tools
      coding-conventions.md   # Style guide, component style, file organization, naming
      quality-standards.md    # Testing, documentation, performance
      ui-ux-standards.md      # Design system, responsive, accessibility
      security-requirements.md # Authentication, input validation, data protection
      architecture-patterns.md # API style, state management, auth, deployment
  .autoforge/
    features.db               # SQLite database with feature records (build system)
```

### Layer Architecture

Agent OS uses a three-layer context model:

| Layer | Location | Purpose |
|-------|----------|---------|
| **Standards** | `agent-os/standards/` | Technology choices, coding conventions, quality bars |
| **Product** | `.agent/product/` | Vision, users, use cases, constraints, competitive context |
| **Specs** | `.agent/specs/` | Per-feature implementation specifications |

Standards are at the project root level (`agent-os/standards/`) rather than inside `.agent/` so they can also be stored globally at `~/.autoforge/agent-os/standards/` and shared across projects. Project-level standards override global ones.

---

## 4. DunkStack Operations

DunkStack is a file-based context bridge between a human operator and an AI agent. Instead of real-time chat, communication happens through markdown files that both parties read and append to. The REST API and WebSocket provide programmatic access to these files.

### 3.1 Setting Up Comms Files

The comms system uses two markdown files as a walkie-talkie:

- **`from_human.md`** -- Human writes here; agent reads only, never modifies.
- **`to_human.md`** -- Agent writes here; human reads only.

Both files are append-only. Each entry gets a UTC timestamp header.

**Write a message to the agent:**

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/comms/from-human?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{"content": "Focus on the auth module next.", "title": "Priority Change", "category": "Direction"}'
```

**Read agent messages:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/comms/to-human?project_name=my-project"
```

Response:

```json
{
  "content": "# Agent Messages\n> Append new messages at the bottom...\n\n## [2026-02-26 14:30] Update - Auth Progress\nFinished JWT token validation...\n",
  "exists": true
}
```

### 3.2 Session Control

The control file determines what the agent should do next. Three modes:

| Mode | Meaning |
|------|---------|
| `idle` | Agent should stop and wait for further instructions |
| `continue` | Agent should continue working on the current task |
| `autopilot` | Agent should work autonomously, picking the next task itself |

**Set the control mode:**

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/control?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{"mode": "autopilot", "message": "Ship the MVP"}'
```

**Read the current mode:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/control?project_name=my-project"
```

Response:

```json
{"mode": "autopilot", "message": "Ship the MVP"}
```

### 3.3 Working Memory and Index

**Working memory** (`working_memory.md`) is the agent's scratchpad -- what it is currently thinking about, partial results, open threads.

**Index** (`index.md`) is the agent's map of all files it has encountered or created.

Both are read-only from the API (the agent writes them):

```bash
# Read working memory
curl "http://127.0.0.1:8888/api/dunkstack/working-memory?project_name=my-project"

# Read file index
curl "http://127.0.0.1:8888/api/dunkstack/index?project_name=my-project"
```

### 3.4 Bridge Saves

A bridge save captures the agent's current state so a new session can pick up where the old one left off. It records:

- What task was in progress
- How far along it was
- What the immediate next steps are
- Any open questions

**Create a bridge save:**

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/bridge/save?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "session_limit",
    "current_task": "Implementing user authentication",
    "progress": "JWT middleware done, login endpoint 80% complete",
    "next_steps": "1. Finish login validation\n2. Add refresh token endpoint",
    "open_questions": "Should we use httpOnly cookies or localStorage for tokens?"
  }'
```

**Read the current bridge state:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/bridge?project_name=my-project"
```

Bridge saves also append an entry to the build log at `.agent/progress/build_log.md`.

**Read the build log:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/build-log?project_name=my-project"
```

### 3.5 Config and Settings

Configuration is stored in `.agent/settings/config.yml` (YAML format). The API reads and writes this file. Configuration is divided into sections:

| Section | Controls |
|---------|----------|
| `safety` | Token usage thresholds (warning, handoff, hard stop percentages), model limit |
| `context_management` | Context window management settings |
| `session` | Session-level preferences |
| `mode` | Subscription vs API mode, model selection |
| `api` | API provider settings |

**Read the full config:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/config?project_name=my-project"
```

**Update specific config sections (PATCH -- merges, does not replace):**

```bash
curl -X PATCH "http://127.0.0.1:8888/api/dunkstack/config?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{
    "safety": {
      "warning_threshold_pct": 40,
      "handoff_threshold_pct": 45,
      "hard_stop_threshold_pct": 50,
      "model_limit": 200000
    },
    "mode": {"type": "subscription"}
  }'
```

### 3.6 Context Gauge (Token Tracking)

The context gauge tracks cumulative token usage across API calls. It uses an in-memory store (resets on server restart) and applies safety tiers based on configurable thresholds.

**Safety tiers:**

| Tier | Label | Default Threshold | Action |
|------|-------|-------------------|--------|
| 0 | OK | < 45% | Operating normally |
| 1 | WARNING | >= 45% | Approaching limit, prepare for handoff |
| 2 | HANDOFF | >= 47.5% | Stop coding, write handoff file |
| 3 | HARD STOP | >= 50% | Session should terminate |

**Get current token state:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/tokens?project_name=my-project"
```

Response:

```json
{
  "cumulative": {
    "input_tokens": 15000,
    "output_tokens": 5000,
    "cache_read_tokens": 2000,
    "cache_creation_tokens": 1000,
    "total_cost_usd": 0.45,
    "api_calls": 12
  },
  "model_limit": 200000,
  "mode": "subscription",
  "usage_percent": 10.0,
  "entries_count": 12,
  "safety": {
    "tier": 0,
    "label": "OK",
    "color": "green",
    "message": "Operating normally."
  }
}
```

**Record a token usage snapshot:**

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/tokens/record?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{
    "input_tokens": 3000,
    "output_tokens": 1200,
    "cache_read_tokens": 500,
    "cache_creation_tokens": 200,
    "total_cost_usd": 0.08
  }'
```

**Reset token tracking (new session):**

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/tokens/reset"
```

**Get full token log:**

```bash
curl "http://127.0.0.1:8888/api/dunkstack/tokens/log"
```

### 3.7 Project Scoping

Every DunkStack endpoint accepts an optional `project_name` query parameter. When provided, all file operations are scoped to `{project_dir}/.agent/` instead of the server's root `.agent/` directory.

```
GET /api/dunkstack/comms/to-human                          -> reads ROOT/.agent/comms/to_human.md
GET /api/dunkstack/comms/to-human?project_name=my-app      -> reads MY_APP_DIR/.agent/comms/to_human.md
```

The project name is resolved through the AutoForge project registry (`~/.autoforge/registry.db`), which maps names to absolute filesystem paths.

### 3.8 The DunkStack WebSocket

The WebSocket at `ws://127.0.0.1:8888/api/dunkstack/ws` provides real-time push notifications for all DunkStack state changes.

**Connect with wscat:**

```bash
npx wscat -c ws://127.0.0.1:8888/api/dunkstack/ws
```

On connection, you receive an `init` message with the current token state. After that, the server broadcasts events whenever the REST API is used.

See [Section 7: WebSocket Protocol](#7-websocket-protocol) for all message types.

---

## 5. Agent OS Workflow

Agent OS is a structured PRD (Product Requirements Document) creation system that guides you through 9 stages (0-8) to go from a raw idea to a fully populated `features.db` ready for the AutoForge build agent.

### Overview of All Stages

| Stage | Name | Method | What Happens |
|-------|------|--------|-------------|
| 0 | Intake Dock | REST | Upload/paste files, tag them, distribute to directories |
| 1 | Intake | WebSocket | Describe your idea; entities are extracted from your text |
| 2 | Standards Check | WebSocket | Answer questionnaire about tech stack, coding style, etc. |
| 3 | Product Discovery | WebSocket | Answer questions about vision, users, pain points, etc. |
| 4 | Feature Extraction | WebSocket | Features are derived from product context |
| 5 | Gap Analysis | WebSocket | Cross-layer consistency check finds missing pieces |
| 6 | Spec Generation | WebSocket | Detailed spec generated for each feature |
| 7 | Database Population | WebSocket | Features written to `features.db` with dependency graph |
| 8 | Handoff | WebSocket | Scope boundary + context primer assembled for build agent |

### Stage 0: Intake Dock (File Staging)

The intake dock is a file staging area where you can upload or paste documents before starting the interactive session. Files are:

1. **Staged** -- uploaded or pasted into a temporary directory
2. **Auto-tagged** -- keyword matching suggests a category (standards, product, spec, reference, intake)
3. **Manually tagged** -- you can override the auto-tag
4. **Processed** -- distributed to the correct Agent OS directories

Tags and where files go:

| Tag | Destination Directory |
|-----|----------------------|
| `standards` | `agent-os/standards/` |
| `product` | `.agent/product/` |
| `spec` | `.agent/specs/` |
| `reference` | `.agent/knowledge/` |
| `intake` | `.agent/intake/` |

Stage 0 is handled entirely through REST endpoints (no WebSocket needed).

### Stage 1: Intake

You describe what you want to build in natural language. The system:

1. Accumulates your raw input
2. Runs local entity extraction (no LLM needed) to populate `product_description` and `problem_statement`
3. Checks for blocking gaps (the two fields above are required to proceed)
4. If minimum info is present, auto-advances to Stage 2

**Extracted entity fields:**

| Field | Type | Severity if Missing |
|-------|------|---------------------|
| `product_name` | string | minor |
| `product_description` | string | **blocking** |
| `target_users` | list | important |
| `core_features` | list | important |
| `constraints` | list | minor |
| `tech_preferences` | list | minor |
| `problem_statement` | string | **blocking** |
| `competitive_refs` | list | minor |

### Stage 2: Standards Check

A questionnaire covering 5 categories with 15 questions total:

1. **Technology Stack** -- languages, frontend, backend, database, other tools
2. **Coding Style** -- style guide, component style, file organization, naming
3. **Quality** -- testing requirements, documentation requirements
4. **UI/UX** -- design system, mobile responsive (skipped if no frontend)
5. **Architecture** -- API style, state management, authentication, deployment

Questions can be skipped conditionally. For example, frontend-related questions are skipped if `tech_frontend` is "None".

If standards files already exist in the project, this stage auto-skips.

Output: 6 markdown files written to `agent-os/standards/`.

### Stage 3: Product Discovery

An adaptive question flow with 6 questions:

1. **Vision** -- "In one sentence, what does this product do for the user?"
2. **Target Users** -- "Who specifically uses this?"
3. **Core Problem** -- "What's the #1 pain point this solves?"
4. **Competitive Context** -- "What do people use today instead?"
5. **Constraints** -- "Any hard constraints?"
6. **Success Definition** -- "If this works perfectly, what happens?"

Questions are auto-skipped if the corresponding entity was already extracted during intake (e.g., if `product_description` is already populated, the vision question is skipped).

Output: 6 markdown files written to `.agent/product/`.

### Stage 4: Feature Extraction

The system reads all product documents, standards, and extracted entities, then derives a structured feature list. Each feature includes:

- **Name** and **description**
- **Priority**: `must_have` (MVP), `should_have` (v1.1), `nice_to_have` (future)
- **Complexity**: `small`, `medium`, `large`
- **Category**: auth, ui, data, api, infrastructure, integration, etc.
- **Dependencies**: which other features must exist first
- **Source**: which document/entity this feature derives from

Features are sorted by priority (must_have first) and assigned sequential integer IDs starting at 1.

### Stage 5: Gap Analysis

Cross-layer consistency check that looks for:

| Gap Type | Description |
|----------|-------------|
| `missing_detail` | A feature references something not fully defined |
| `contradiction` | Two pieces of context conflict |
| `unstated_dep` | A feature implicitly requires something not in the list |
| `standards_conflict` | A feature conflicts with standards |
| `scope_creep` | Feature set is too ambitious for MVP |

Each gap has severity (`blocking`, `important`, `minor`), a confidence score (0.0-1.0), and a recommendation. Gaps with confidence >= 85% (configurable) are flagged as auto-fillable and can be batch-resolved.

### Stage 6: Spec Generation

For each feature, a detailed markdown specification is generated containing:

- Overview
- Functional and technical requirements
- User stories (As a [user], I want to...)
- Acceptance criteria (checkboxes)
- Technical specification (API endpoints, data models, components, dependencies, edge cases)
- Standards references
- Success metrics

Specs are validated for quality: must have user stories, at least 2 acceptance criteria, standards references, and minimum 20 non-empty lines.

Output: One file per feature in `.agent/specs/` named `feature-{id:03d}-{slug}.md`.

### Stage 7: Database Population

Features are written to `.autoforge/features.db` (SQLite) using the AutoForge Feature model:

- ID, priority (integer 1-3), category, name, description
- Steps (extracted from spec acceptance criteria)
- Dependencies (feature ID references)
- Status fields (passes, in_progress)

A dependency graph is generated and validated for cycles using Kahn's algorithm. Build order is calculated via topological sort.

### Stage 8: Handoff

Two critical documents are generated:

1. **Scope Boundary** (`.agent/scope_boundary.md`) -- categorizes features into MVP / Next Phase / Future, includes build order and quality boundaries ("stop signals" to prevent scope creep during build).

2. **Context Primer** (`.agent/knowledge/context-primer.md`) -- the build agent's first-read briefing. Summarizes all three layers (standards, product, features), lists the build order, records key decisions, and indexes all specs.

The handoff assembly checks that all required artifacts exist:

- Standards files
- Product documents
- Spec files
- `features.db` populated
- `scope_boundary.md` generated
- `context-primer.md` generated

If all checks pass, the handoff is marked as ready and the session is complete.

---

## 6. Testing Each Stage

This section provides exact commands to test each stage. Replace `my-project` with your actual project name.

### 5.0 Test Intake Dock (Stage 0)

```bash
# List staged files (should be empty initially)
curl "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project"

# Paste a product description as a file
curl -X POST "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/paste" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "product-idea.md",
    "content": "# Task Manager App\n\nA simple task management app for small teams. Users can create projects, add tasks, assign them to team members, and track progress with kanban boards."
  }'

# Check what was staged (note the auto_tag field)
curl "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project"

# Tag the file explicitly as "product"
# Replace FILE_ID with the id from the previous response
curl -X PUT "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/FILE_ID/tag" \
  -H "Content-Type: application/json" \
  -d '{"tag": "product"}'

# Upload a file via multipart form (alternative to paste)
curl -X POST "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/upload" \
  -F "file=@/path/to/my-spec.md"

# Check readiness (needs at least one product or intake file, no untagged files)
curl "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/readiness"

# Process all staged files (distributes to directories)
curl -X POST "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/process"

# Remove a staged file
curl -X DELETE "http://127.0.0.1:8888/api/agent-os/intake-dock/my-project/FILE_ID"
```

### 5.1 Test Intake Through Handoff (Stages 1-8 via WebSocket)

The interactive stages (1-8) are driven through the Agent OS WebSocket. Use `wscat` or any WebSocket client.

```bash
npx wscat -c ws://127.0.0.1:8888/api/agent-os/ws/my-project
```

**Stage 1: Send your product description**

```json
{"type": "message", "content": "I want to build a task management app for small teams. Users create projects, add tasks, assign them, and track with kanban boards. Built with React and FastAPI."}
```

The server will respond with:
- A `message` event ("Processing your input...")
- A `progress` event with extracted entities and gaps
- If enough info is present, a `stage_change` event advancing to `standards`

**Stage 2: Answer standards questions**

After the stage change, you receive `question` events. Answer each:

```json
{"type": "answer", "answer": "TypeScript"}
```

Continue answering until all questions are done. Or skip the entire stage:

```json
{"type": "skip_stage"}
```

Or approve existing standards and move on:

```json
{"type": "approve"}
```

**Stage 3: Answer product questions**

Same pattern as Stage 2. Answer each question:

```json
{"type": "answer", "answer": "Small team leads who need simple project tracking"}
```

Or approve to generate documents and advance:

```json
{"type": "approve"}
```

**Stage 4: Review features**

Send any message to trigger feature extraction:

```json
{"type": "message", "content": "extract"}
```

You receive a `features` event with the feature list. Approve to continue:

```json
{"type": "approve"}
```

**Stage 5: Review gaps**

Send any message to trigger gap analysis:

```json
{"type": "message", "content": "analyze"}
```

Approve to continue:

```json
{"type": "approve"}
```

**Stage 6: Generate specs**

Send any message to trigger spec generation:

```json
{"type": "message", "content": "generate"}
```

You receive `spec_preview` events for each feature. Approve to continue:

```json
{"type": "approve"}
```

**Stage 7: Populate database**

Send any message to populate features.db:

```json
{"type": "message", "content": "populate"}
```

Approve to continue:

```json
{"type": "approve"}
```

**Stage 8: Handoff**

Send any message to assemble the handoff:

```json
{"type": "message", "content": "handoff"}
```

You receive a `handoff_ready` event and a `complete` event with the build plan.

### 5.2 Test REST Endpoints Independently

You can also test individual Agent OS subsystems without the WebSocket workflow:

```bash
# List standards files
curl "http://127.0.0.1:8888/api/agent-os/standards/my-project"

# Read a specific standards file
curl "http://127.0.0.1:8888/api/agent-os/standards/my-project/technology-stack.md"

# Write a standards file
curl -X PUT "http://127.0.0.1:8888/api/agent-os/standards/my-project/technology-stack.md" \
  -H "Content-Type: application/json" \
  -d '{"filename": "technology-stack.md", "content": "# Technology Stack\n\n## Languages\nTypeScript\n", "location": "project"}'

# Infer standards from codebase
curl -X POST "http://127.0.0.1:8888/api/agent-os/standards/my-project/infer"

# List product documents
curl "http://127.0.0.1:8888/api/agent-os/product/my-project"

# List features
curl "http://127.0.0.1:8888/api/agent-os/features/my-project"

# Add a feature manually
curl -X POST "http://127.0.0.1:8888/api/agent-os/features/my-project" \
  -H "Content-Type: application/json" \
  -d '{"name": "User Authentication", "description": "JWT-based login and registration", "priority": "must_have", "complexity": "medium", "category": "auth"}'

# List gaps
curl "http://127.0.0.1:8888/api/agent-os/gaps/my-project"

# Get handoff status
curl "http://127.0.0.1:8888/api/agent-os/handoff/my-project/status"

# Populate features.db
curl -X POST "http://127.0.0.1:8888/api/agent-os/handoff/my-project/populate-db"

# Calculate build order
curl -X POST "http://127.0.0.1:8888/api/agent-os/handoff/my-project/build-order"

# Assemble full handoff package
curl -X POST "http://127.0.0.1:8888/api/agent-os/handoff/my-project/assemble"

# Get build plan
curl "http://127.0.0.1:8888/api/agent-os/handoff/my-project/build-plan"

# Scan codebase (existing project)
curl -X POST "http://127.0.0.1:8888/api/agent-os/cre/my-project/scan"

# Get codebase analysis summary
curl "http://127.0.0.1:8888/api/agent-os/cre/my-project/summary"
```

### 5.3 Test Expand (Add Features to Existing Project)

```bash
# Analyze expansion request
curl -X POST "http://127.0.0.1:8888/api/agent-os/expand/my-project/analyze" \
  -H "Content-Type: application/json" \
  -d '{"description": "Add real-time notifications when tasks are assigned or completed"}'

# Add validated features
curl -X POST "http://127.0.0.1:8888/api/agent-os/expand/my-project/add" \
  -H "Content-Type: application/json" \
  -d '{"features": [{"name": "Real-time Notifications", "description": "WebSocket-based push notifications for task events", "priority": "should_have", "complexity": "medium", "category": "integration", "dependencies": []}]}'

# Get expansion summary
curl "http://127.0.0.1:8888/api/agent-os/expand/my-project/summary"
```

### 5.4 Test Session Management

```bash
# List active sessions
curl "http://127.0.0.1:8888/api/agent-os/sessions"

# Get session status for a project
curl "http://127.0.0.1:8888/api/agent-os/sessions/my-project"

# Cancel a session
curl -X DELETE "http://127.0.0.1:8888/api/agent-os/sessions/my-project"
```

---

## 7. REST API Reference

### 6.1 DunkStack Endpoints

All DunkStack endpoints are prefixed with `/api/dunkstack`. All accept an optional `project_name` query parameter.

#### Comms

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/comms/to-human` | -- | `{content: string, exists: bool}` |
| `GET` | `/comms/from-human` | -- | `{content: string, exists: bool}` |
| `POST` | `/comms/from-human` | `{content: string, title?: string, category?: string}` | `{status: "ok", timestamp: string}` |
| `POST` | `/comms/to-human` | `{content: string, title?: string, category?: string}` | `{status: "ok", timestamp: string}` |

#### Session Control

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/control` | -- | `{mode: string, message: string}` |
| `POST` | `/control` | `{mode: "idle"\|"continue"\|"autopilot", message?: string}` | `{status: "ok", mode: string}` |

#### Working Memory and Index

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/working-memory` | -- | `{content: string, exists: bool}` |
| `GET` | `/index` | -- | `{content: string, exists: bool}` |

#### Bridge Save

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/bridge` | -- | `{content: string, exists: bool}` |
| `POST` | `/bridge/save` | `{reason: string, current_task?: string, progress?: string, next_steps?: string, open_questions?: string}` | `{status: "ok", timestamp: string}` |

#### Config

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/config` | -- | `{config: object, exists: bool}` |
| `PATCH` | `/config` | `{safety?: object, context_management?: object, session?: object, mode?: object, api?: object}` | `{status: "ok", config: object}` |

#### Token Tracking

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/tokens` | -- | `{cumulative: object, model_limit: int, mode: string, usage_percent: float, entries_count: int, safety: object}` |
| `POST` | `/tokens/record` | `{input_tokens: int, output_tokens: int, cache_read_tokens?: int, cache_creation_tokens?: int, total_cost_usd?: float, timestamp?: string}` | `{status: "ok", usage_percent: float, safety: object}` |
| `POST` | `/tokens/reset` | -- | `{status: "ok"}` |
| `GET` | `/tokens/log` | -- | `{entries: array}` |

#### Build Log

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/build-log` | -- | `{content: string, exists: bool}` |

### 6.2 Agent OS Endpoints

All Agent OS endpoints are prefixed with `/api/agent-os`. The `project_name` is a path parameter (not query parameter).

#### Standards

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/standards/{project_name}` | -- | `{files: [{name, path, size, modified, location}]}` |
| `GET` | `/standards/{project_name}/{filename}` | -- | `{filename: string, content: string}` |
| `PUT` | `/standards/{project_name}/{filename}` | `{filename: string, content: string, location?: "project"\|"global"}` | `{status: "ok", path: string}` |
| `POST` | `/standards/{project_name}/infer` | -- | `{inferred: object}` |
| `GET` | `/standards/{project_name}/summary` | -- | `{summary: string}` |

#### Product

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/product/{project_name}` | -- | `{files: [{name, path, size, modified}]}` |
| `GET` | `/product/{project_name}/{filename}` | -- | `{filename: string, content: string}` |
| `PUT` | `/product/{project_name}/{filename}` | `{filename: string, content: string}` | `{status: "ok", path: string}` |
| `GET` | `/product/{project_name}/summary` | -- | `{summary: string}` |

#### Specs

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/specs/{project_name}` | -- | `{files: [{name, path, size, modified}]}` |
| `GET` | `/specs/{project_name}/{feature_id}` | -- | `{feature_id: int, filename: string, content: string}` |
| `GET` | `/specs/{project_name}/{feature_id}/quality` | -- | `{feature_id: int, quality: {valid: bool, issues: array}}` |

#### Features

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/features/{project_name}` | -- | `{features: [{id, name, description, priority, complexity, category, dependencies, source}]}` |
| `POST` | `/features/{project_name}` | `{name: string, description: string, priority?: string, complexity?: string, category?: string, dependencies?: int[]}` | `{feature: object}` |
| `PUT` | `/features/{project_name}/{feature_id}` | `{name?: string, description?: string, priority?: string, complexity?: string, category?: string}` | `{feature: object}` |
| `DELETE` | `/features/{project_name}/{feature_id}` | -- | `{status: "ok", removed: int}` |

#### Gap Analysis

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/gaps/{project_name}` | query: `severity?` | `{gaps: array}` |
| `POST` | `/gaps/{project_name}/{gap_id}/resolve` | `{resolution: string}` | `{gap: object}` |
| `POST` | `/gaps/{project_name}/auto-resolve` | -- | `{resolved: array, count: int}` |

#### Handoff

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/handoff/{project_name}/populate-db` | -- | `{status: "ok", feature_count: int}` |
| `POST` | `/handoff/{project_name}/build-order` | -- | `{build_order: int[]}` |
| `GET` | `/handoff/{project_name}/status` | -- | `{status: {features_db_populated, dependencies_set, scope_boundary_generated, context_primer_generated, build_order_calculated, handoff_complete}}` |
| `POST` | `/handoff/{project_name}/assemble` | -- | `{handoff: {ready: bool, missing: string[], feature_count: int, build_order: int[], estimated_sessions: int}}` |
| `GET` | `/handoff/{project_name}/build-plan` | -- | `{plan: string}` |

#### Intake Dock

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/intake-dock/{project_name}` | -- | `{files: [{id, name, size, type, tag, auto_tag, processed, destination_path, created_at}]}` |
| `POST` | `/intake-dock/{project_name}/upload` | multipart: `file` | `{file: object}` |
| `POST` | `/intake-dock/{project_name}/paste` | `{filename: string, content: string}` | `{file: object}` |
| `PUT` | `/intake-dock/{project_name}/{file_id}/tag` | `{tag: "standards"\|"product"\|"spec"\|"reference"\|"intake"}` | `{file: object}` |
| `DELETE` | `/intake-dock/{project_name}/{file_id}` | -- | `{status: "ok"}` |
| `GET` | `/intake-dock/{project_name}/readiness` | -- | `{standards: {count, ready}, product: {count, ready}, ..., untagged: int, can_proceed: bool}` |
| `POST` | `/intake-dock/{project_name}/process` | -- | `{processed: int, destinations: {tag: [filenames]}}` |

#### Expand

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/expand/{project_name}/analyze` | `{description: string}` | `{prompt: string, description: string}` |
| `POST` | `/expand/{project_name}/add` | `{features: [{name, description, priority, complexity, category, dependencies}]}` | `{status: "ok", added: array, conflicts: array, warnings: array, graph: object, new_build_order: int[]}` |
| `GET` | `/expand/{project_name}/summary` | -- | `{summary: string}` |

#### Codebase Reality Engine

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/cre/{project_name}/scan` | -- | `{analysis: {tech_stack, file_structure, code_patterns, linter_config, test_patterns}}` |
| `GET` | `/cre/{project_name}/analysis` | -- | `{analysis: object}` |
| `POST` | `/cre/{project_name}/apply-standards` | -- | `{prompt: string, message: string}` |
| `POST` | `/cre/{project_name}/apply-product` | -- | `{prompt: string, message: string}` |
| `POST` | `/cre/{project_name}/apply-features` | -- | `{prompt: string, message: string}` |
| `GET` | `/cre/{project_name}/summary` | -- | `{summary: string}` |

#### Context Primer

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/context-primer/{project_name}` | -- | `{content: string, path: string}` |
| `POST` | `/context-primer/{project_name}` | -- | `{status: "ok", content: string, path: string}` |

#### Sessions

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/sessions` | -- | `{sessions: string[]}` |
| `GET` | `/sessions/{project_name}` | -- | `{project_name, is_active, is_complete, current_stage, stage_index, message_count}` |
| `DELETE` | `/sessions/{project_name}` | -- | `{status: "ok", message: string}` |

---

## 8. WebSocket Protocol

### 7.1 DunkStack WebSocket

**Endpoint:** `ws://127.0.0.1:8888/api/dunkstack/ws`

#### Server-to-Client Messages

| Type | Fields | Trigger |
|------|--------|---------|
| `init` | `token_state: {cumulative, model_limit, mode, entries_count}` | On connection |
| `comms_update` | `channel: "from_human"\|"to_human", timestamp, title, content` | POST to comms endpoints |
| `control_update` | `mode, message` | POST to `/control` |
| `config_update` | `config: object` | PATCH to `/config` |
| `token_update` | `entry, cumulative, usage_percent, safety` | POST to `/tokens/record` |
| `token_reset` | (none) | POST to `/tokens/reset` |
| `bridge_saved` | `timestamp` | POST to `/bridge/save` |
| `ping` | (none) | Server keepalive (every 5 minutes) |
| `pong` | (none) | Response to client ping |

#### Client-to-Server Messages

| Type | Fields | Purpose |
|------|--------|---------|
| `ping` | (none) | Keepalive; server responds with `pong` |

### 7.2 Agent OS WebSocket

**Endpoint:** `ws://127.0.0.1:8888/api/agent-os/ws/{project_name}`

#### Client-to-Server Messages

| Type | Fields | Purpose |
|------|--------|---------|
| `ping` | (none) | Keepalive |
| `message` | `content: string` | Send free-form input to the current stage |
| `answer` | `answer: string` | Answer a questionnaire question |
| `approve` | (none) | Approve current stage output and advance |
| `skip_stage` | (none) | Skip the current stage entirely |

#### Server-to-Client Messages

| Type | Fields | When |
|------|--------|------|
| `stage_change` | `stage, index, total` | Stage advances (sent on connection and after each advance) |
| `message` | `content: string` | Informational text from the system |
| `question` | `question: {id, question, type, options?, category, required}` | Standards or product questionnaire |
| `progress` | `stage, ...stage-specific fields` | Progress update within a stage |
| `features` | `features: array, extraction_prompt: string` | Feature extraction result (Stage 4) |
| `gaps` | `gaps: array, analysis_prompt: string` | Gap analysis result (Stage 5) |
| `spec_preview` | `feature_id, feature_name, generation_prompt` | Spec preview for one feature (Stage 6) |
| `handoff_ready` | `status: {ready, missing, feature_count, build_order, estimated_sessions}` | Handoff assembly result (Stage 8) |
| `complete` | `handoff: object, build_plan: string` | Session complete -- all stages done |
| `error` | `message: string` | Error occurred |
| `pong` | (none) | Response to client ping |

### 7.3 Example WebSocket Session (Complete)

```
# Connect
> wscat -c ws://127.0.0.1:8888/api/agent-os/ws/my-project

# Server sends initial stage
< {"type":"stage_change","stage":"intake","index":0,"total":8}

# Send product description
> {"type":"message","content":"A recipe sharing app where home cooks can post recipes with photos, and followers can save and rate them. Built with Next.js and PostgreSQL."}
< {"type":"message","content":"Processing your input..."}
< {"type":"message","content":"I've captured your initial input. Moving to standards check."}
< {"type":"progress","stage":"intake","entities":{...},"gaps":[...]}
< {"type":"stage_change","stage":"standards","index":1,"total":8}

# Standards: first question appears automatically when you send any message
> {"type":"message","content":"start"}
< {"type":"question","question":{"id":"tech_languages","category":"Technology Stack","question":"What programming language(s) will this project use?","type":"text","required":true,...}}
< {"type":"progress","stage":"standards","total_questions":15,"answered":0,"skipped":0,"remaining":15,"current_category":"Technology Stack"}

# Answer the question
> {"type":"answer","answer":"TypeScript"}
< {"type":"question","question":{"id":"tech_frontend","category":"Technology Stack","question":"Frontend framework preference?","type":"choice","options":["React","Vue","Svelte","Next.js","None","Other"],...}}
< {"type":"progress","stage":"standards","total_questions":15,"answered":1,"skipped":0,"remaining":14,...}

# Skip remaining standards
> {"type":"approve"}
< {"type":"message","content":"Standards files generated."}
< {"type":"stage_change","stage":"product_discovery","index":2,"total":8}

# Product discovery questions
> {"type":"message","content":"start"}
< {"type":"question","question":{"id":"success_definition","question":"If this works perfectly, what happens? What does success look like?",...}}

> {"type":"answer","answer":"Home cooks have a beautiful portfolio of recipes, followers discover amazing dishes, and the community grows organically through sharing."}

# When all questions are done:
< {"type":"message","content":"All product questions answered. Documents generated."}
< {"type":"stage_change","stage":"feature_extraction","index":3,"total":8}

# Continue through remaining stages with approve...
> {"type":"approve"}
# ...
```

---

## 9. The Handoff

The handoff is the critical bridge between Agent OS (PRD creation) and AutoForge (automated build). Here is exactly what happens and what gets produced.

### What Agent OS Produces

| Artifact | Path | Consumed By |
|----------|------|-------------|
| `features.db` | `.autoforge/features.db` | AutoForge build agent (via Feature MCP server) |
| `context-primer.md` | `.agent/knowledge/context-primer.md` | Build agent's first read |
| `scope_boundary.md` | `.agent/scope_boundary.md` | Build agent scope guard |
| Standards files (6) | `agent-os/standards/*.md` | Build agent coding patterns |
| Product files (6) | `.agent/product/*.md` | Build agent product context |
| Spec files (per feature) | `.agent/specs/feature-*.md` | Build agent implementation specs |

### How features.db Is Structured

Each feature row in the database contains:

| Column | Type | Source |
|--------|------|--------|
| `id` | integer | Sequential from Agent OS feature list |
| `priority` | integer | 1 = must_have, 2 = should_have, 3 = nice_to_have |
| `category` | string | Feature category (auth, ui, data, etc.) |
| `name` | string | Feature name |
| `description` | string | Feature description |
| `steps` | JSON array | Acceptance criteria extracted from the spec |
| `passes` | boolean | False (not yet built) |
| `in_progress` | boolean | False (not yet claimed) |
| `dependencies` | JSON array | List of feature IDs this depends on |

### How the Build Agent Uses It

1. The **initializer agent** does NOT run -- `features.db` is already populated.
2. The **coding agent** starts, reads `context-primer.md` first for full project context.
3. It uses the Feature MCP server to call `feature_get_ready` (returns features whose dependencies are all passing).
4. It claims a feature via `feature_claim_and_get`.
5. It reads the feature's spec from `.agent/specs/feature-{id}-{slug}.md`.
6. It implements the feature following the standards in `agent-os/standards/`.
7. It marks the feature as passing via `feature_mark_passing`.
8. The scope boundary prevents scope creep -- its "STOP SIGNALS" section tells the agent what NOT to do.

### Verifying the Handoff

After running `POST /api/agent-os/handoff/{project_name}/assemble`, check the response:

```json
{
  "handoff": {
    "ready": true,
    "missing": [],
    "feature_count": 12,
    "build_order": [1, 3, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "estimated_sessions": 4
  }
}
```

If `ready` is `false`, the `missing` array tells you what needs to be created first.

You can also check the build plan for a human-readable summary:

```bash
curl "http://127.0.0.1:8888/api/agent-os/handoff/my-project/build-plan"
```

### Starting the Build Agent

Once the handoff is complete, start the AutoForge coding agent:

```bash
python autonomous_agent_demo.py --project-dir my-project
```

The agent will:
1. Detect that `features.db` already has features (skips initializer)
2. Read the context primer
3. Begin implementing features in dependency order

---

## 10. Troubleshooting

### Server Will Not Start

**Symptom:** `ModuleNotFoundError` or `ImportError`

**Fix:** Ensure you are in the activated virtual environment and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Symptom:** Port 8888 already in use

**Fix:** Either kill the existing process or use a different port:

```bash
python start_ui.py --port 9999
```

### "Project not found in registry"

**Symptom:** 404 error when calling Agent OS endpoints

**Fix:** The project must be registered in AutoForge. Create it via the UI or API first:

```bash
curl "http://127.0.0.1:8888/api/projects"
```

If the project is not listed, create it through the Web UI or register the directory.

### Agent OS Session Stuck on a Stage

**Symptom:** Sending messages but stage does not advance

**Fix:** Send `{"type": "approve"}` to force-approve the current stage, or `{"type": "skip_stage"}` to skip it entirely. You can also cancel the session and start over:

```bash
curl -X DELETE "http://127.0.0.1:8888/api/agent-os/sessions/my-project"
```

Then reconnect to the WebSocket to start a fresh session.

### WebSocket Disconnects Immediately

**Symptom:** Connection opens then closes with code 4000 or 4004

**Cause:** Invalid project name (4000) or project not found in registry (4004).

**Fix:** Verify the project exists:

```bash
curl "http://127.0.0.1:8888/api/projects"
```

### DunkStack Files Not Found

**Symptom:** `{"content": "", "exists": false}` for all comms endpoints

**Fix:** The `.agent/` directory structure is created lazily on the first write operation. Send a message to create it:

```bash
curl -X POST "http://127.0.0.1:8888/api/dunkstack/comms/from-human?project_name=my-project" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello"}'
```

### Token State Resets Unexpectedly

**Cause:** Token tracking is in-memory only. It resets when the server restarts.

**Workaround:** This is by design. Each server session starts with a clean token counter. The token log entries are not persisted to disk.

### Handoff Reports Missing Artifacts

**Symptom:** `POST /handoff/{project_name}/assemble` returns `ready: false`

**Fix:** Check the `missing` array. Common issues:

| Missing | Cause | Fix |
|---------|-------|-----|
| `standards files` | No `.md` files in `agent-os/standards/` | Run Standards Check (Stage 2) or write files manually |
| `product documents` | No `.md` files in `.agent/product/` | Run Product Discovery (Stage 3) or write files manually |
| `spec files` | No `.md` files in `.agent/specs/` | Run Spec Generation (Stage 6) or write files manually |
| `features.db` | Database not populated | `POST /handoff/{project_name}/populate-db` |
| `scope_boundary.md` | Not generated | Handoff assembly generates it, but requires other artifacts first |
| `context-primer.md` | Not generated | Requires all upstream layers to exist |

### Standards Questions Not Showing

**Symptom:** Stage 2 auto-skips even though you want to configure standards

**Cause:** Standards files already exist in the project (e.g., copied from templates during directory initialization).

**Fix:** Delete the existing standards files and restart the session:

```bash
rm {project_dir}/agent-os/standards/*.md
curl -X DELETE "http://127.0.0.1:8888/api/agent-os/sessions/my-project"
```

### Features.db Already Has Features

**Symptom:** Running `populate-db` clears existing features

**Cause:** By design, `populate-db` is idempotent. It deletes all existing rows and re-inserts from the current Agent OS feature list.

**Workaround:** If you have features from a previous initializer run that you want to keep, do not call `populate-db`. Use the handoff only for new projects.

### Codebase Scan Returns Empty Results

**Symptom:** `POST /cre/{project_name}/scan` returns empty arrays

**Cause:** The scanner looks for `package.json`, `requirements.txt`, `pyproject.toml`, and other manifest files in the project root. It also excludes `node_modules`, `.git`, `venv`, `__pycache__`, `dist`, and `build` directories. Scan depth is limited to 3 levels.

**Fix:** Ensure the project directory actually contains source code and manifest files at the root level.

### CORS Errors in Browser

**Symptom:** Browser console shows CORS errors when making API requests

**Cause:** By default, the server only allows requests from `localhost:5173` (Vite dev) and `localhost:8888` (production).

**Fix:** If you need remote access, start with the `AUTOFORGE_ALLOW_REMOTE=1` environment variable. WARNING: This disables localhost-only security restrictions.

---

## Appendix A: Config.yml Reference

The `.agent/settings/config.yml` file controls DunkStack behavior. Here is a complete example:

```yaml
safety:
  warning_threshold_pct: 45.0
  handoff_threshold_pct: 47.5
  hard_stop_threshold_pct: 50.0
  model_limit: 200000

context_management:
  max_working_memory_lines: 500

session:
  auto_bridge_on_limit: true

mode:
  type: subscription  # or "api"

api:
  provider: claude

agent_os:
  auto_select_threshold: 85
  mechanism_analysis:
    auto_select_threshold: 85
    present_alternatives_gap: 15
    min_viable_score: 60
  developers_choice:
    enabled: true
    bias_toward_standards: 0.3
    bias_toward_simplicity: 0.2
    bias_toward_adoption: 0.2
    bias_toward_docs: 0.1
  max_features_per_expansion: 5
```

## Appendix B: File Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Standards | `{kebab-case}.md` | `technology-stack.md` |
| Product docs | `{kebab-case}.md` | `competitive-context.md` |
| Spec files | `feature-{id:03d}-{slug}.md` | `feature-001-user-auth.md` |
| Comms files | `{snake_case}.md` | `from_human.md` |

## Appendix C: Priority Mapping

| Agent OS Priority | Database Integer | Meaning |
|-------------------|-----------------|---------|
| `must_have` | 1 | MVP -- build first |
| `should_have` | 2 | v1.1 -- build after MVP |
| `nice_to_have` | 3 | Future -- do not build yet |

## Appendix D: Entity Schema

The intake stage extracts these entities from user input:

```json
{
  "product_name": "string",
  "product_description": "string (blocking if missing)",
  "target_users": ["string"],
  "core_features": ["string"],
  "constraints": ["string"],
  "tech_preferences": ["string"],
  "problem_statement": "string (blocking if missing)",
  "competitive_refs": ["string"]
}
```

Fields marked "blocking" must be populated before the session can advance past intake. They are auto-populated from the first 500 characters of raw user input if not otherwise extracted.
