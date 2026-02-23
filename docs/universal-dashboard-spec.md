# Universal Dashboard: Contextual AI Workspace System

## System Specification — Agent OS Format

**Version:** 1.0.0
**Date:** 2026-02-22
**Status:** Implementation-Ready
**Depends on:** Autoforge UI (React 19, TanStack Query, Tailwind v4, WebSocket infrastructure)

---

# LAYER 1: STANDARDS — Architecture & Infrastructure

## 1.1 System Identity

| Field | Value |
|-------|-------|
| System Name | Universal Dashboard |
| Platform | React 19 SPA (extends Autoforge UI) |
| Purpose | Contextual AI workspace for building, editing, and monitoring automation systems |
| Core Abstraction | Each automation system declares its shape via a manifest; the dashboard renders a purpose-built workspace from that manifest |
| Key Differentiator | The AI assistant in each tab is pre-loaded with that system's architecture — it knows what it's looking at without you explaining |

## 1.2 Design Principles

1. **Manifest-Driven** — The dashboard does not hardcode knowledge of any system type. It reads a manifest file and renders accordingly. New system types require zero dashboard code changes.
2. **Context Carries** — When you switch tabs, the AI context switches with you. No re-explaining. No "let me read the codebase first."
3. **Structure Over Text** — Components that have known shapes (agents, schemas, hooks, pipelines) are edited via purpose-built forms, not raw text editors. The underlying files remain plain text.
4. **Lateral Navigation** — You can reach any system from any other system. No "go back to home first." Tab-to-tab is instant.
5. **Progressive Disclosure** — The meta dashboard shows the big picture. Click into a system for detail. Click into a component for editing. Three levels, always accessible.

## 1.3 Three-Level Navigation Model

```
Level 3: Meta Dashboard (Home)
  ├── All registered automation systems as cards
  ├── Cross-system search
  ├── Global AI assistant (knows all systems)
  └── System health overview
        │
        ▼
Level 2: System Dashboard (Tab)
  ├── System-specific layout (pipeline, graph, grid, kanban)
  ├── Component sidebar (agents, scripts, schemas, hooks, outputs)
  ├── Live status / monitoring
  └── Scoped AI assistant (knows THIS system deeply)
        │
        ▼
Level 1: Component Editor (Panel)
  ├── Structured form for known component types
  ├── Raw text fallback for unknown types
  ├── Input/output schema visualization
  ├── Test-with-sample-input button
  └── AI inline assist (knows THIS component's role)
```

## 1.4 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | React 19 | Already used by Autoforge UI |
| State | TanStack Query + Zustand | TanStack for server state, Zustand for client UI state (tabs, panels) |
| Styling | Tailwind CSS v4 | Neobrutalism design system already defined in Autoforge |
| Real-time | WebSocket | Already implemented in Autoforge for agent status/progress |
| Layout Engine | CSS Grid + dagre | Grid for dashboard layouts, dagre for pipeline/graph views (already in Autoforge) |
| Terminal | xterm.js | Already integrated in Autoforge for interactive terminal |
| Editor | CodeMirror 6 | Lightweight, extensible, supports custom languages and structured editing |
| Routing | React Router (hash) | Already used by Autoforge (`/#/docs` route exists) |

## 1.5 Backend Extensions

The Autoforge FastAPI server needs these new endpoints:

```
# Manifest Management
GET    /api/manifests                        # List all registered system manifests
GET    /api/manifests/{system_id}            # Get one manifest
PUT    /api/manifests/{system_id}            # Update manifest
POST   /api/manifests                        # Register new system

# Component Operations
GET    /api/systems/{system_id}/components   # List components from manifest
GET    /api/systems/{system_id}/components/{component_id}  # Read component file
PUT    /api/systems/{system_id}/components/{component_id}  # Write component file
POST   /api/systems/{system_id}/components/{component_id}/test  # Test with sample input

# System State
GET    /api/systems/{system_id}/state        # Pipeline/system live state
GET    /api/systems/{system_id}/outputs      # Stage outputs
GET    /api/systems/{system_id}/logs         # System logs

# Cross-System
GET    /api/search?q=...&systems=...         # Search across systems
POST   /api/systems/{system_id}/run          # Execute a system (like running the pipeline)
POST   /api/systems/{system_id}/run/{stage}  # Execute a single stage

# AI Context
GET    /api/systems/{system_id}/ai-context   # Get the pre-built AI context for a system
```

---

# LAYER 2: PRODUCT — Features & User Experience

## 2.1 The Manifest System

The manifest is the heart of the entire dashboard. It's the contract between your automation system and the dashboard UI. Every system that wants a dashboard declares itself via a manifest file.

### 2.1.1 Manifest File Location

```
{project_root}/.swarm/manifest.yaml
```

The `.swarm/` directory is the standard location for dashboard metadata. This parallels `.autoforge/` for Autoforge projects and `.claude/` for Claude Code configuration.

### 2.1.2 Manifest Schema

```yaml
# .swarm/manifest.yaml
version: "1.0"

# === System Identity ===
system:
  name: "Rant-to-PRD Pipeline"
  id: "rant-to-prd"                    # URL-safe, unique across registry
  type: "sequential-pipeline"           # Determines default layout
  description: "7-stage rant to PRD transformation"
  icon: "pipeline"                      # Dashboard icon (pipeline|swarm|graph|grid|custom)
  color: "#6366f1"                      # Accent color for this system's tab

# === Component Registry ===
# Every file the dashboard should know about
components:
  agents:
    - id: "transcriber"
      path: ".claude/agents/rant-transcriber.md"
      role: "Stage 1 — Transcriber"
      model: "opus"
      temperature: 0
      max_tokens: 32000
      description: "Transforms raw rant into structured bullets"
      inputs:
        - "input/rant.txt"
      outputs:
        - "stage1/raw_capture.json"

    - id: "classifier"
      path: ".claude/agents/rant-classifier.md"
      role: "Stage 2 — Classifier"
      model: "sonnet"
      temperature: 0
      max_tokens: 32000
      description: "Places every item into PRD sections"
      inputs:
        - "stage1/raw_capture.json"
      outputs:
        - "stage2/classified.json"

    - id: "gap-analyst"
      path: ".claude/agents/rant-gap-analyst.md"
      role: "Stage 3 — Gap Analyst"
      model: "opus"
      temperature: 0
      max_tokens: 16384
      description: "Identifies gaps, auto-fills defaults, generates decision questions"
      inputs:
        - "stage2/classified.json"
        - "stage1/raw_capture.json"
      outputs:
        - "stage3/gap_report.json"

    - id: "decision-facilitator"
      path: ".claude/agents/rant-decision-facilitator.md"
      role: "Stage 4 — Decision Facilitator"
      model: "sonnet"
      temperature: 0.3
      max_tokens: 16384
      description: "Interactive gap decision collection"
      inputs:
        - "stage3/gap_report.json"
      outputs:
        - "stage4/decisions.json"

    - id: "mechanism-analyst"
      path: ".claude/agents/rant-mechanism-analyst.md"
      role: "Stage 5 — Mechanism Analyst"
      model: "opus"
      temperature: 0
      max_tokens: 32000
      description: "Determines implementation approach for every mechanism"
      inputs:
        - "stage2/classified.json"
        - "stage3/gap_report.json"
        - "stage4/decisions.json"
      outputs:
        - "stage5/mechanisms.json"

    - id: "prd-compiler"
      path: ".claude/agents/rant-prd-compiler.md"
      role: "Stage 6 — PRD Compiler"
      model: "opus"
      temperature: 0
      max_tokens: 65536
      description: "Compiles all stage outputs into final PRD"
      inputs:
        - "stage1/raw_capture.json"
        - "stage2/classified.json"
        - "stage3/gap_report.json"
        - "stage4/decisions.json"
        - "stage5/mechanisms.json"
      outputs:
        - "stage6/final_prd.md"
        - "stage6/final_prd.json"

    - id: "autoforge-bridge"
      path: ".claude/agents/rant-autoforge-bridge.md"
      role: "Stage 7 — Autoforge Bridge"
      model: "sonnet"
      temperature: 0
      max_tokens: 32000
      description: "Transforms PRD into Autoforge app_spec.txt"
      optional: true
      inputs:
        - "stage6/final_prd.json"
      outputs:
        - "stage7/app_spec.txt"
        - "stage7/features.json"

  scripts:
    - id: "pipeline"
      path: ".claude/scripts/rant-pipeline.sh"
      role: "Pipeline Orchestrator"
      executable: true
      description: "Main bash script that runs all stages sequentially"

  hooks:
    - id: "pre-stage"
      path: ".claude/hooks/pre-stage-check.sh"
      trigger: "before-stage"
      description: "Verify prerequisites before each stage"

    - id: "post-stage"
      path: ".claude/hooks/post-stage-log.sh"
      trigger: "after-stage"
      description: "Log completion, update token tracking"

    - id: "post-write"
      path: ".claude/hooks/post-write-validate.sh"
      trigger: "after-write"
      description: "Validate JSON output schema"

  schemas:
    - id: "spec"
      path: "docs/rant-to-prd-spec.md"
      role: "System Specification"
      description: "Complete system spec with all stage schemas"

  configs:
    - id: "pipeline-state"
      path: "rant-pipeline/pipeline_state.json"
      role: "Pipeline State"
      live: true  # Dashboard should poll/watch this file

# === Pipeline Definition ===
# Only for type: "sequential-pipeline"
pipeline:
  stages:
    - stage: 1
      agent: "transcriber"
      name: "Transcribe"
    - stage: 2
      agent: "classifier"
      name: "Classify"
    - stage: 3
      agent: "gap-analyst"
      name: "Analyze Gaps"
    - stage: 4
      agent: "decision-facilitator"
      name: "Decide"
      interactive: true
    - stage: 5
      agent: "mechanism-analyst"
      name: "Mechanisms"
    - stage: 6
      agent: "prd-compiler"
      name: "Compile PRD"
    - stage: 7
      agent: "autoforge-bridge"
      name: "Autoforge"
      optional: true

  state_file: "rant-pipeline/pipeline_state.json"
  log_file: "rant-pipeline/pipeline.log"
  token_file: "rant-pipeline/token_usage.json"

# === Dashboard Configuration ===
dashboard:
  layout: "pipeline-flow"         # Layout engine to use
  primary_view: "stage-monitor"   # Default view on tab open
  sidebar_sections:               # What appears in the left sidebar
    - "agents"
    - "scripts"
    - "hooks"
    - "schemas"
    - "outputs"

  # AI assistant context — injected when this tab is active
  ai_context: |
    You are assisting with the Rant-to-PRD Pipeline, a 7-stage system that
    transforms unstructured "rants" into production-ready PRDs using Claude
    Code CLI agents.

    Stages: (1) Transcriber, (2) Classifier, (3) Gap Analyst,
    (4) Decision Facilitator, (5) Mechanism Analyst, (6) PRD Compiler,
    (7) Autoforge Bridge (optional).

    Each stage reads from disk, writes to disk. The pipeline script
    orchestrates execution. Each agent is a .md file in .claude/agents/.

    When the user asks about a stage, read its agent file and output schema.
    When they ask about errors, check the pipeline log and validation files.

  # Quick actions shown as buttons in the dashboard
  actions:
    - label: "Run Pipeline"
      command: "bash .claude/scripts/rant-pipeline.sh"
      icon: "play"
    - label: "Resume"
      command: "bash .claude/scripts/rant-pipeline.sh --resume"
      icon: "refresh"
    - label: "View PRD"
      command: "open"
      target: "stage6/final_prd.md"
      icon: "document"

### 2.1.3 System Types and Their Layouts

The manifest `type` field determines which layout engine renders the system dashboard. This is the core of "universal but specialized" — the dashboard shell is the same, but the content area morphs to match the system's shape.

| Type | Layout | Best For | Visual Model |
|------|--------|----------|--------------|
| `sequential-pipeline` | Left-to-right stage flow | Rant-to-PRD, ETL pipelines, build systems | Horizontal swim lanes, each stage a card |
| `parallel-swarm` | Grid of agent cards | Multi-agent concurrent systems | NxM grid, each agent shows status/output |
| `dependency-graph` | dagre node graph | Feature dependency systems (Autoforge) | Nodes and edges, topological layout |
| `kanban` | Column-based board | Task management, feature tracking | Columns: pending, in-progress, done |
| `tree` | Hierarchical tree view | File system tools, org structures | Collapsible tree with detail panel |
| `custom` | User-defined layout | Anything else | Layout defined in manifest via grid template |

### 2.1.4 Manifest Discovery

The dashboard discovers systems through three mechanisms:

1. **Autoforge Registry** — Any project registered in `~/.autoforge/registry.db` that has a `.swarm/manifest.yaml` is automatically discovered.
2. **Directory Scan** — The dashboard scans a configurable list of directories for `.swarm/manifest.yaml` files.
3. **Manual Registration** — User clicks "+ New System" and points to a directory.

```
Discovery Priority:
  1. ~/.autoforge/registry.db (existing Autoforge projects)
  2. ~/.swarm/registry.db (new standalone registry)
  3. Configured scan paths from ~/.swarm/config.yaml
```

---

## 2.2 Meta Dashboard (Level 3 — Home)

The entry point. Shows all registered automation systems at a glance.

### 2.2.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  UNIVERSAL DASHBOARD                              [Search] [+ New]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ ◆ Rant-to-PRD   │  │ ◇ Test Swarm    │  │ ◇ Deploy Bot    │    │
│  │   Pipeline       │  │   v2            │  │                 │    │
│  │                  │  │                  │  │                 │    │
│  │  7 stages        │  │  5 agents       │  │  3 stages       │    │
│  │  ■■■■■□□  5/7    │  │  ■■■□□  3/5     │  │  ■□□  1/3       │    │
│  │                  │  │                  │  │                 │    │
│  │  Last run: 2m    │  │  Last run: 1h   │  │  Last run: 3d   │    │
│  │  Status: running │  │  Status: idle   │  │  Status: idle   │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │ ◇ Code Review   │  │  + Create New   │                          │
│  │   Agent          │  │    System       │                          │
│  │                  │  │                 │                          │
│  │  1 agent         │  │  Choose type:   │                          │
│  │  ■  1/1          │  │  ◻ Pipeline     │                          │
│  │                  │  │  ◻ Swarm        │                          │
│  │  Last run: 5m    │  │  ◻ Graph        │                          │
│  │  Status: done    │  │  ◻ Custom       │                          │
│  └─────────────────┘  └─────────────────┘                          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  AI: Ready. Ask me about any system or search across all of them.   │
│  You: _                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2.2 System Cards

Each card shows:
- **Name and icon** (from manifest)
- **Component count** (agents, stages, etc.)
- **Progress bar** (stages validated / total, or agents complete / total)
- **Last run timestamp**
- **Status indicator:** idle, running, paused, error, complete
- **Accent color** (from manifest `color` field)

Clicking a card opens that system in a new tab (Level 2).

### 2.2.3 Cross-System Search

The search bar at the top searches across ALL registered systems:
- File names and paths
- Component roles and descriptions
- Agent prompt content
- Output content (stage outputs, logs)

Results are grouped by system with the system accent color for quick visual scanning.

### 2.2.4 Global AI Assistant

The meta dashboard has its own AI context:

```
You are the Universal Dashboard assistant. You have access to all registered
automation systems. You can:
- Compare how different systems handle similar problems
- Search across all system components
- Suggest which system to use for a given task
- Help create new system manifests

Registered systems: [dynamically injected list from registry]
```

---

## 2.3 System Dashboard (Level 2 — Tab)

When you click into a system, you get a purpose-built workspace. The layout depends on the manifest `type`.

### 2.3.1 Pipeline Layout (type: "sequential-pipeline")

For the Rant-to-PRD system:

```
┌──────────────────────────────────────────────────────────────────────┐
│ [← Home] [Rant-to-PRD] [Test Swarm] [Deploy Bot] [+]               │
├──────────┬───────────────────────────────────────────────────────────┤
│          │                                                           │
│ COMPS    │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐              │
│          │  │ S1   │──▶│ S2   │──▶│ S3   │──▶│ S4   │              │
│ ▼ Agents │  │Trans.│   │Class.│   │Gaps  │   │Decide│              │
│   Trans. │  │  ✅  │   │  ✅  │   │  🔄  │   │  ⏳  │              │
│   Class. │  └──────┘   └──────┘   └──────┘   └──────┘              │
│   Gaps   │                                                           │
│   Decide │  ┌──────┐   ┌──────┐   ┌──────┐                         │
│   Mechs  │  │ S5   │──▶│ S6   │──▶│ S7   │                         │
│   Comp.  │  │Mechs │   │Compile│  │Bridge│                         │
│   Bridge │  │  ⏳  │   │  ⏳  │   │  ⏳  │                         │
│          │  └──────┘   └──────┘   └──────┘                         │
│ ▶ Scripts│                                                           │
│ ▶ Hooks  │  STAGE 3 DETAIL:                                         │
│ ▶ Schemas│  Agent: rant-gap-analyst.md (opus)                       │
│ ▶ Outputs│  Status: Running (2m 14s)                                │
│          │  Items processed: 47/47                                   │
│          │  Type A: 23 | Type B: 18 | Type C: 6 (so far)           │
│──────────│  Token usage: 14,200 in / 8,400 out                     │
│ ACTIONS  │                                                           │
│          │  [View Input] [View Output] [Edit Agent] [Re-run Stage]  │
│ ▶ Run    │                                                           │
│ ▶ Resume ├───────────────────────────────────────────────────────────┤
│ ▶ View   │  AI: Stage 3 is running. The gap analyst has classified  │
│   PRD    │  23 items as covered (Type A) and auto-filled 18 gaps    │
│          │  (Type B). 6 ambiguous gaps identified so far — these    │
│          │  will become decision questions in Stage 4.               │
│          │                                                           │
│          │  You: _                                                    │
└──────────┴───────────────────────────────────────────────────────────┘
```

### 2.3.2 Swarm Layout (type: "parallel-swarm")

For concurrent agent systems:

```
┌──────────────────────────────────────────────────────────────────────┐
│ [← Home] [Test Swarm v2]                                            │
├──────────┬───────────────────────────────────────────────────────────┤
│          │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│ AGENTS   │  │ Agent: Spark │  │ Agent: Fizz  │  │ Agent: Octo  │   │
│          │  │ Feature #12  │  │ Feature #8   │  │ Feature #15  │   │
│ Spark    │  │ Status: test │  │ Status: code │  │ Status: done │   │
│ Fizz     │  │ ████░░ 67%  │  │ ██░░░░ 33%  │  │ ██████ 100% │   │
│ Octo     │  │ 3m elapsed  │  │ 5m elapsed  │  │ ✅ Passed    │   │
│ Hoot     │  └──────────────┘  └──────────────┘  └──────────────┘   │
│ Buzz     │                                                           │
│          │  ┌──────────────┐  ┌──────────────┐                      │
│ ─────    │  │ Agent: Hoot  │  │ Agent: Buzz  │                      │
│ QUEUE    │  │ Feature #3   │  │   (idle)     │                      │
│ #4 pend  │  │ Status: code │  │ Waiting for  │                      │
│ #7 pend  │  │ █░░░░░ 15%  │  │ next feature │                      │
│ #9 pend  │  │ 1m elapsed  │  │              │                      │
│          │  └──────────────┘  └──────────────┘                      │
└──────────┴───────────────────────────────────────────────────────────┘
```

### 2.3.3 Graph Layout (type: "dependency-graph")

Uses dagre (already in Autoforge) to render dependency relationships:

```
┌──────────────────────────────────────────────────────────────────────┐
│ [← Home] [Feature Graph]                                            │
├──────────┬───────────────────────────────────────────────────────────┤
│          │           ┌──────┐                                        │
│ FEATURES │     ┌────▶│ F-3  │────┐                                  │
│          │     │     │ Auth │    │                                   │
│ ✅ F-1   │  ┌──────┐└──────┘  ┌──────┐                             │
│ ✅ F-2   │  │ F-1  │          │ F-5  │                              │
│ 🔄 F-3  │  │ Init │────┐     │ API  │                              │
│ ⏳ F-4   │  └──────┘    │     └──────┘                              │
│ ⏳ F-5   │     │      ┌──────┐   │                                  │
│ ⏳ F-6   │     └─────▶│ F-4  │───┘                                  │
│          │            │ DB   │                                       │
│          │            └──────┘                                       │
└──────────┴───────────────────────────────────────────────────────────┘
```

### 2.3.4 Tab Behavior

- **Persistent tabs** — Opening a system adds a tab. Tabs persist until closed.
- **Lazy loading** — Tab content only loads when activated. Background tabs don't consume resources.
- **Tab state** — Each tab remembers its scroll position, selected component, and AI conversation.
- **Tab reordering** — Drag tabs to reorder.
- **Tab overflow** — More than ~8 tabs shows a dropdown menu.
- **Quick switch** — Keyboard shortcut (Ctrl+1-9) switches to tab by position. Ctrl+Tab cycles.

---

## 2.4 Component Editor (Level 1 — Panel)

When you click a component in the sidebar, the editor panel opens. The editor is **type-aware** — it knows the shape of what you're editing and renders structured controls rather than raw text.

### 2.4.1 Agent Editor

For `.md` agent files, the editor parses the frontmatter and prompt sections:

```
┌─ Agent Editor: rant-transcriber.md ──────────────────────────────────┐
│                                                                       │
│  CONFIGURATION                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Role:     [Stage 1 — Transcriber          ]                  │  │
│  │  Model:    [opus ▼]      Temp: [0.0 ]    Max: [32000  ]     │  │
│  │  Status:   ✅ Valid markdown   │  1,247 words   │  v1.0.0    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  DATA FLOW                                                            │
│  ┌──────────────────┐          ┌──────────────────┐                  │
│  │ INPUT             │   ──▶   │ OUTPUT            │                  │
│  │ input/rant.txt    │          │ stage1/           │                  │
│  │                   │          │  raw_capture.json │                  │
│  │ [View] [Browse]   │          │ [View] [Schema]   │                  │
│  └──────────────────┘          └──────────────────┘                  │
│                                                                       │
│  SYSTEM PROMPT                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  You are the Transcriber agent. Your job is to read the raw   │  │
│  │  rant file and extract every discrete mechanism, feature,     │  │
│  │  constraint, preference, and vision statement the user        │  │
│  │  mentions.                                                     │  │
│  │                                                                │  │
│  │  CRITICAL RULES:                                               │  │
│  │  1. NEVER summarize. Preserve full detail.                    │  │
│  │  2. Every item must include the original quote.               │  │
│  │  ...                                                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  QUALITY GATE                                                         │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  ☑ DDR >= 0.60    ☑ item_count > 0    ☑ All items have       │  │
│  │                                          original_quotes      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  [Save] [Test with Sample] [View Last Output] [Diff] [Revert]       │
└──────────────────────────────────────────────────────────────────────┘
```

**"Test with Sample"** button: Runs the agent with a small sample input and shows the output inline. This lets you iterate on prompts without running the full pipeline.

### 2.4.2 Schema Editor

For JSON schema files (stage outputs), the editor shows:
- Tree view of the schema structure
- Required vs optional fields
- Type annotations
- Example values
- Validation rule summaries

### 2.4.3 Script Editor

For bash scripts, the editor shows:
- Syntax-highlighted code (CodeMirror)
- Function list sidebar (jump to function)
- Run button with terminal output inline
- Environment variable reference (what vars the script reads)

### 2.4.4 Hook Editor

For hook scripts:
- Trigger type (before-stage, after-stage, after-write)
- Which stages it applies to
- Environment variables it receives
- Syntax-highlighted code
- Test button (simulate hook execution)

### 2.4.5 Output Viewer

For stage output JSON files:
- Collapsible JSON tree view
- Metadata summary at top (item counts, token usage, timestamps)
- Diff against previous output (if re-run)
- Search within output
- "Open in AI" button — loads the output into the AI context for analysis

### 2.4.6 Raw Fallback

For any component type not recognized, the editor falls back to a plain CodeMirror text editor with syntax highlighting based on file extension.

---

## 2.5 Contextual AI Assistant

The AI assistant is the feature that transforms this from "a file browser with nice visuals" into something actually powerful. It works at all three levels.

### 2.5.1 Context Injection Model

```
AI Context = Base Context + System Context + Component Context + Conversation History
```

| Level | What's Injected |
|-------|----------------|
| Meta (Level 3) | List of all systems, their types, statuses, component counts |
| System (Level 2) | Full manifest, current pipeline state, recent logs, component list |
| Component (Level 1) | The component file content, its role, inputs, outputs, quality gate |

The AI context is NOT the full file contents of everything — that would blow the context window. Instead, it's a structured summary generated from the manifest, with the ability to read specific files on demand.

### 2.5.2 AI Capabilities Per Level

**Meta Dashboard AI can:**
- "Which system uses opus the most?" → scans manifests
- "Create a new pipeline system for data ETL" → generates manifest template
- "Compare how Rant-to-PRD and Test Swarm handle errors" → reads both system specs

**System Dashboard AI can:**
- "Why did Stage 3 fail?" → reads validation.json, pipeline.log
- "How many tokens has this run used?" → reads token_usage.json
- "Rewrite the classifier to be stricter" → edits agent file
- "What would happen if I swapped Stage 3 to sonnet?" → analyzes the trade-off

**Component Editor AI can:**
- "This prompt is too long, tighten it" → edits in-place
- "Add a quality gate for minimum 50 items" → modifies gate section
- "Show me the last output this agent produced" → reads output file
- "The output is missing cluster_04, debug it" → reads input + output, identifies the gap

### 2.5.3 AI Panel Behavior

- The AI panel is always at the bottom of the screen (collapsible)
- Expand/collapse with keyboard shortcut `A` (same as Autoforge)
- The AI conversation persists per tab (switching tabs switches conversations)
- AI can be told to "watch" a running stage and report when it finishes or errors
- AI responses include file links — click to jump to the referenced file/line

### 2.5.4 AI Actions

The AI can perform actions (with user confirmation):
- Edit component files
- Run stages or the full pipeline
- Create new components (agents, hooks, schemas)
- Navigate to other systems (proposes tab switch)

Actions require a confirmation step:

```
AI: I'll update the transcriber agent to enforce a minimum of 50 items.
    Here's the change:
    
    [diff preview]
    
    [Apply] [Edit First] [Cancel]
```

---

## 2.6 Lateral Navigation (Cross-System)

The core UX innovation: you're never trapped in one system. From any tab, you can reach any other system instantly.

### 2.6.1 Navigation Methods

| Method | Action |
|--------|--------|
| Tab click | Switch to an already-open system |
| Home button | Go to meta dashboard (Level 3) |
| Ctrl+Tab | Cycle through open tabs |
| Ctrl+1-9 | Jump to tab by position |
| Command palette (Ctrl+K) | Search and switch to any system (even closed ones) |
| AI suggestion | AI says "you might want to check your Test Swarm for this pattern" — click to navigate |
| Component cross-reference | A manifest can reference components in other systems — clicking follows the reference |

### 2.6.2 Command Palette

The command palette is the power-user's navigation tool:

```
┌─ Command Palette ──────────────────────────────────┐
│  > rant transcriber                                 │
│                                                     │
│  AGENTS                                             │
│  ◆ Rant-to-PRD > rant-transcriber.md (Stage 1)    │
│  ◆ Rant-to-PRD > rant-classifier.md (Stage 2)     │
│                                                     │
│  SYSTEMS                                            │
│  ◇ Rant-to-PRD Pipeline (7 stages)                │
│                                                     │
│  OUTPUTS                                            │
│  ◆ Rant-to-PRD > stage1/raw_capture.json           │
│                                                     │
│  ACTIONS                                            │
│  ▶ Run Rant-to-PRD Pipeline                        │
│  ▶ Resume Rant-to-PRD Pipeline                     │
└─────────────────────────────────────────────────────┘
```

Searches across: system names, component names, component roles, file paths, and available actions.

---

## 2.7 System Creation Wizard

When the user clicks "+ New System" from the meta dashboard, a wizard guides them through manifest creation.

### 2.7.1 Wizard Steps

**Step 1: Choose Type**
```
What kind of system are you building?

  ◉ Sequential Pipeline — Stages run one after another
  ○ Parallel Swarm — Multiple agents run concurrently
  ○ Dependency Graph — Tasks with dependencies
  ○ Kanban Board — Task tracking with columns
  ○ Custom — Define your own layout
```

**Step 2: Name and Location**
```
System name: [My ETL Pipeline        ]
Project directory: [/home/user/etl-project  ] [Browse]
Description: [Extract, transform, load data from APIs  ]
```

**Step 3: Define Components (type-specific)**

For "Sequential Pipeline":
```
Define your stages:

  Stage 1: [Extract     ] Agent: [extract-agent.md    ] Model: [sonnet ▼]
  Stage 2: [Transform   ] Agent: [transform-agent.md  ] Model: [opus ▼]
  Stage 3: [Validate    ] Agent: [validate-agent.md   ] Model: [sonnet ▼]
  Stage 4: [Load        ] Agent: [load-agent.md       ] Model: [sonnet ▼]

  [+ Add Stage]
```

**Step 4: Generate**

The wizard generates:
- `.swarm/manifest.yaml` — complete manifest
- Skeleton agent files — `.claude/agents/{name}.md` with boilerplate
- Pipeline script — `.claude/scripts/{name}-pipeline.sh`
- Hook scripts — `.claude/hooks/` with standard pre/post hooks
- Directory structure for stage outputs

The user can then fill in the agent prompts and customize.

### 2.7.2 Template Library

Pre-built templates for common system types:

| Template | Type | Stages/Agents | Description |
|----------|------|---------------|-------------|
| Rant-to-PRD | pipeline | 7 stages | Transform rant to PRD |
| Code Review | single | 1 agent | Deep code review |
| Test Suite | swarm | 3-5 agents | Parallel test execution |
| Data Pipeline | pipeline | 3-5 stages | ETL data processing |
| Content Generator | pipeline | 4 stages | Content creation workflow |
| Research Agent | graph | 5-8 tasks | Research with dependencies |

---

## 2.8 Real-Time Monitoring

When a system is running (pipeline executing, swarm active), the dashboard provides live monitoring.

### 2.8.1 WebSocket Events

The dashboard subscribes to system-specific WebSocket channels:

```
ws://localhost:{port}/ws/systems/{system_id}
```

Event types:

| Event | Payload | Description |
|-------|---------|-------------|
| `stage_start` | `{stage, agent, timestamp}` | A stage began execution |
| `stage_progress` | `{stage, items_processed, total, detail}` | Progress within a stage |
| `stage_complete` | `{stage, status, duration, token_usage}` | Stage finished |
| `stage_error` | `{stage, error, retry_count}` | Stage encountered error |
| `pipeline_complete` | `{status, total_duration, total_tokens}` | Pipeline finished |
| `agent_output` | `{agent_id, line, type}` | Raw agent output line |
| `validation_result` | `{stage, valid, errors}` | Stage validation result |

### 2.8.2 Live Stage Card Updates

When a stage is running, its card in the pipeline view shows:
- Elapsed time (live counter)
- Token consumption (live counter)
- Items processed / total
- Current sub-task (e.g., "Classifying item 23/47")
- Spinner animation

When a stage completes:
- Card turns green (success) or red (failure)
- Summary stats appear (duration, tokens, item count)
- Output becomes clickable

### 2.8.3 Log Streaming

The dashboard streams the pipeline log in real-time:
- Filterable by stage
- Filterable by severity (INFO, WARN, ERROR)
- Auto-scroll with pause-on-hover
- Clickable timestamps jump to stage context

---

## 2.9 Keyboard Shortcuts

Extending Autoforge's existing shortcut system:

| Shortcut | Action |
|----------|--------|
| `?` | Show keyboard shortcut help |
| `A` | Toggle AI assistant panel |
| `Ctrl+K` | Command palette |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+1-9` | Jump to tab N |
| `Ctrl+H` | Go to meta dashboard (home) |
| `E` | Toggle component editor |
| `G` | Toggle graph/list view (in graph systems) |
| `R` | Run system (with confirmation) |
| `L` | Toggle log panel |
| `Ctrl+S` | Save current component |
| `Ctrl+P` | Quick file finder within current system |
| `Escape` | Close modal/panel/palette |

---

# LAYER 3: SPECS — Technical Implementation

## 3.1 React Component Architecture

```
src/
  components/
    dashboard/
      MetaDashboard.tsx          # Level 3 — system card grid
      SystemCard.tsx             # Individual system card on meta dashboard
      SystemDashboard.tsx        # Level 2 — tab content, delegates to layout
      TabBar.tsx                 # Tab strip with drag-reorder
      TabProvider.tsx            # Tab state management (Zustand)

    layouts/
      PipelineLayout.tsx         # Sequential pipeline view (stage flow)
      SwarmLayout.tsx            # Parallel agent grid
      GraphLayout.tsx            # dagre dependency graph
      KanbanLayout.tsx           # Column board
      TreeLayout.tsx             # Hierarchical tree
      CustomLayout.tsx           # User-defined grid template

    editors/
      AgentEditor.tsx            # Structured agent file editor
      ScriptEditor.tsx           # Syntax-highlighted script editor
      SchemaEditor.tsx           # JSON schema tree view
      HookEditor.tsx             # Hook editor with trigger config
      OutputViewer.tsx           # JSON output tree with search
      RawEditor.tsx              # CodeMirror fallback editor
      EditorPanel.tsx            # Editor container with type detection

    sidebar/
      ComponentSidebar.tsx       # Left sidebar with component tree
      SidebarSection.tsx         # Collapsible section (agents, scripts, etc.)
      ActionButtons.tsx          # Quick action buttons

    ai/
      DashboardAI.tsx            # AI panel container
      AIContextProvider.tsx      # Context injection based on current level
      AIConversation.tsx         # Chat interface (extends AssistantChat.tsx)
      AIActionConfirm.tsx        # Action confirmation modal

    monitoring/
      StageCard.tsx              # Individual stage card with live status
      StageDetail.tsx            # Expanded stage detail panel
      LogStream.tsx              # Real-time log viewer
      TokenTracker.tsx           # Token usage display
      ProgressBar.tsx            # Stage progress bar

    wizard/
      CreateSystemWizard.tsx     # New system creation flow
      TypeSelector.tsx           # System type picker
      StageConfigurator.tsx      # Stage definition for pipelines
      AgentConfigurator.tsx      # Agent definition for swarms
      TemplateLibrary.tsx        # Pre-built template browser

    shared/
      CommandPalette.tsx         # Ctrl+K search and navigate
      StatusIndicator.tsx        # Status dot (idle/running/error/done)
      DataFlowDiagram.tsx        # Input → Output visual for agents

  hooks/
    useManifest.ts               # Load and parse manifest YAML
    useSystemState.ts            # Subscribe to system state (WebSocket)
    useSystemWebSocket.ts        # WebSocket connection for system events
    useTabs.ts                   # Tab state management
    useCommandPalette.ts         # Command palette state and search
    useComponentFile.ts          # Read/write component files via API
    useAIContext.ts              # Build AI context from current location

  lib/
    manifest.ts                  # Manifest YAML parser and validator
    layout-registry.ts           # Maps system type → layout component
    ai-context-builder.ts        # Builds AI context string from manifest + state
    component-type-detector.ts   # Determines editor type from file extension + manifest role

  stores/
    tabStore.ts                  # Zustand store for tab state
    dashboardStore.ts            # Global dashboard state
```

## 3.2 Manifest Parser

The manifest parser reads YAML and produces a typed TypeScript object:

```typescript
interface SwarmManifest {
  version: string;
  system: {
    name: string;
    id: string;
    type: SystemType;
    description: string;
    icon: string;
    color: string;
  };
  components: {
    agents: AgentComponent[];
    scripts: ScriptComponent[];
    hooks: HookComponent[];
    schemas: SchemaComponent[];
    configs: ConfigComponent[];
  };
  pipeline?: PipelineDefinition;    // Only for sequential-pipeline
  swarm?: SwarmDefinition;          // Only for parallel-swarm
  graph?: GraphDefinition;          // Only for dependency-graph
  dashboard: DashboardConfig;
}

type SystemType =
  | "sequential-pipeline"
  | "parallel-swarm"
  | "dependency-graph"
  | "kanban"
  | "tree"
  | "custom";

interface AgentComponent {
  id: string;
  path: string;
  role: string;
  model: "opus" | "sonnet" | "haiku";
  temperature: number;
  max_tokens: number;
  description: string;
  inputs: string[];
  outputs: string[];
  optional?: boolean;
}

interface DashboardConfig {
  layout: string;
  primary_view: string;
  sidebar_sections: string[];
  ai_context: string;
  actions: DashboardAction[];
}
```

## 3.3 AI Context Builder

The context builder generates a focused context string based on where the user is in the dashboard:

```typescript
function buildAIContext(
  level: "meta" | "system" | "component",
  manifest?: SwarmManifest,
  component?: ComponentBase,
  systemState?: SystemState
): string {
  const parts: string[] = [];

  if (level === "meta") {
    parts.push("You are the Universal Dashboard assistant.");
    parts.push(`Registered systems: ${getAllSystems().map(s => s.name).join(", ")}`);
    // ... meta-level context
  }

  if (level === "system" && manifest) {
    parts.push(manifest.dashboard.ai_context);
    parts.push(`Current state: ${JSON.stringify(systemState)}`);
    parts.push(`Components: ${manifest.components.agents.map(a => a.role).join(", ")}`);
    // ... system-level context
  }

  if (level === "component" && component) {
    parts.push(`You are helping edit: ${component.role}`);
    parts.push(`File: ${component.path}`);
    parts.push(`Inputs: ${component.inputs?.join(", ")}`);
    parts.push(`Outputs: ${component.outputs?.join(", ")}`);
    // ... component-level context
  }

  return parts.join("\n\n");
}
```

## 3.4 Layout Registry

Maps system types to React components:

```typescript
const layoutRegistry: Record<SystemType, React.ComponentType<LayoutProps>> = {
  "sequential-pipeline": PipelineLayout,
  "parallel-swarm": SwarmLayout,
  "dependency-graph": GraphLayout,
  "kanban": KanbanLayout,
  "tree": TreeLayout,
  "custom": CustomLayout,
};

// SystemDashboard.tsx uses this to render the right layout:
function SystemDashboard({ manifest }: Props) {
  const Layout = layoutRegistry[manifest.system.type];
  return <Layout manifest={manifest} />;
}
```

## 3.5 Backend Router

New FastAPI router for manifest/system operations:

```python
# server/routers/systems.py

@router.get("/manifests")
async def list_manifests():
    """Discover all .swarm/manifest.yaml files from registry."""

@router.get("/manifests/{system_id}")
async def get_manifest(system_id: str):
    """Read and parse a specific system manifest."""

@router.get("/systems/{system_id}/components")
async def list_components(system_id: str):
    """List all components declared in the manifest."""

@router.get("/systems/{system_id}/components/{component_id}")
async def read_component(system_id: str, component_id: str):
    """Read a component file's content."""

@router.put("/systems/{system_id}/components/{component_id}")
async def write_component(system_id: str, component_id: str, body: ComponentUpdate):
    """Write updated content to a component file."""

@router.post("/systems/{system_id}/run")
async def run_system(system_id: str, options: RunOptions):
    """Execute a system's pipeline/swarm."""

@router.post("/systems/{system_id}/run/{stage}")
async def run_stage(system_id: str, stage: int):
    """Execute a single stage of a pipeline system."""

@router.get("/systems/{system_id}/state")
async def get_system_state(system_id: str):
    """Read current pipeline/swarm state."""

@router.get("/systems/{system_id}/ai-context")
async def get_ai_context(system_id: str, level: str = "system", component_id: str = None):
    """Build and return AI context for a given navigation level."""

@router.websocket("/ws/systems/{system_id}")
async def system_websocket(websocket: WebSocket, system_id: str):
    """Real-time system events (stage progress, completions, errors)."""
```

## 3.6 Integration with Autoforge

The Universal Dashboard extends the existing Autoforge UI rather than replacing it:

| Autoforge Feature | Dashboard Integration |
|-------------------|----------------------|
| Project registry | Systems discovered from the same registry |
| Feature kanban | Becomes one layout type (kanban) in the dashboard |
| Agent mission control | Becomes the swarm layout view |
| Dependency graph | Becomes the graph layout view |
| Assistant panel | Becomes the dashboard AI (with context injection) |
| Terminal tabs | Available in every system dashboard |
| WebSocket infrastructure | Extended with system-specific event types |

**Migration path:** The existing Autoforge UI continues to work as-is. The Universal Dashboard is a new route (`/#/dashboard`) that provides the multi-system workspace. Autoforge projects that add a `.swarm/manifest.yaml` get the enhanced dashboard view. Projects without manifests continue using the standard Autoforge UI.

**Routing:**
```
/#/                  → Existing Autoforge UI (unchanged)
/#/docs              → Existing docs (unchanged)
/#/dashboard         → Universal Dashboard meta view (new)
/#/dashboard/:id     → System dashboard for a specific system (new)
```

---

# APPENDICES

## Appendix A: Why a Manifest (Not Auto-Detection)

You might ask: why not just scan the file system and auto-detect the system type? Three reasons:

1. **Intent over inference.** A directory with 7 `.md` agent files could be a pipeline, a swarm, or unrelated files. Only the creator knows the intent. The manifest is explicit.

2. **Dashboard configuration.** The AI context, quick actions, sidebar sections, and layout are system-specific. These can't be inferred — they need to be declared.

3. **Stability.** Auto-detection breaks when you add a file or rename something. The manifest is stable — it changes only when you change it.

The wizard makes manifest creation painless. You answer 3-4 questions and get a complete manifest.

## Appendix B: Comparison to Existing Tools

| Feature | VS Code | Autoforge (current) | Universal Dashboard |
|---------|---------|---------------------|---------------------|
| File editing | Generic text editor | N/A (terminal) | Type-aware structured editor |
| System awareness | None (it's a file editor) | Per-project features | Full system architecture awareness |
| AI context | Copilot (code-level) | Assistant (project-level) | System-level with component drill-down |
| Multi-system | Workspaces (folders) | Project switcher | Tabbed with instant lateral nav |
| Live monitoring | Extensions required | Agent mission control | Built-in per-system-type monitoring |
| Creation wizard | File > New File | Create project wizard | System-type-aware wizard with templates |

The key differentiator: VS Code knows about files. Autoforge knows about features. The Universal Dashboard knows about **systems** — their architecture, their state, their components, and how they all connect.

## Appendix C: Manifest Examples

### Minimal Manifest (Single Agent)

```yaml
version: "1.0"
system:
  name: "Code Reviewer"
  id: "code-reviewer"
  type: "kanban"
  description: "Automated code review agent"
  icon: "grid"
  color: "#10b981"
components:
  agents:
    - id: "reviewer"
      path: ".claude/agents/code-review.md"
      role: "Code Review Agent"
      model: "opus"
      temperature: 0
      max_tokens: 32000
      description: "Reviews code for quality, security, and performance"
      inputs: []
      outputs: []
dashboard:
  layout: "kanban"
  primary_view: "board"
  sidebar_sections: ["agents"]
  ai_context: "You are assisting with a code review agent system."
  actions:
    - label: "Run Review"
      command: "claude --agent .claude/agents/code-review.md"
      icon: "play"
```

### Parallel Swarm Manifest

```yaml
version: "1.0"
system:
  name: "Test Swarm"
  id: "test-swarm"
  type: "parallel-swarm"
  description: "5-agent parallel test execution"
  icon: "swarm"
  color: "#f59e0b"
components:
  agents:
    - id: "test-agent-1"
      path: ".claude/agents/test-runner.md"
      role: "Test Runner"
      model: "sonnet"
      temperature: 0
      max_tokens: 16384
      description: "Runs assigned test suite"
      inputs: ["test-queue/"]
      outputs: ["test-results/"]
  scripts:
    - id: "orchestrator"
      path: ".claude/scripts/test-orchestrator.sh"
      role: "Swarm Orchestrator"
      executable: true
      description: "Distributes tests across agents"
swarm:
  max_concurrency: 5
  claim_strategy: "atomic"
  queue_source: "test-queue/"
  result_target: "test-results/"
dashboard:
  layout: "swarm-grid"
  primary_view: "agent-grid"
  sidebar_sections: ["agents", "scripts", "outputs"]
  ai_context: |
    You are assisting with a parallel test swarm that runs 5 agents
    concurrently. Each agent claims test suites from a queue and
    writes results.
  actions:
    - label: "Run Swarm"
      command: "bash .claude/scripts/test-orchestrator.sh"
      icon: "play"
    - label: "View Results"
      command: "open"
      target: "test-results/"
      icon: "folder"
```

## Appendix D: File Inventory (New Files)

```
# Frontend (ui/src/)
ui/src/components/dashboard/
  MetaDashboard.tsx
  SystemCard.tsx
  SystemDashboard.tsx
  TabBar.tsx
  TabProvider.tsx
ui/src/components/layouts/
  PipelineLayout.tsx
  SwarmLayout.tsx
  GraphLayout.tsx
  KanbanLayout.tsx
  TreeLayout.tsx
  CustomLayout.tsx
ui/src/components/editors/
  AgentEditor.tsx
  ScriptEditor.tsx
  SchemaEditor.tsx
  HookEditor.tsx
  OutputViewer.tsx
  RawEditor.tsx
  EditorPanel.tsx
ui/src/components/sidebar/
  ComponentSidebar.tsx
  SidebarSection.tsx
  ActionButtons.tsx
ui/src/components/ai/
  DashboardAI.tsx
  AIContextProvider.tsx
  AIConversation.tsx
  AIActionConfirm.tsx
ui/src/components/monitoring/
  StageCard.tsx
  StageDetail.tsx
  LogStream.tsx
  TokenTracker.tsx
  ProgressBar.tsx
ui/src/components/wizard/
  CreateSystemWizard.tsx
  TypeSelector.tsx
  StageConfigurator.tsx
  AgentConfigurator.tsx
  TemplateLibrary.tsx
ui/src/components/shared/
  CommandPalette.tsx
  StatusIndicator.tsx
  DataFlowDiagram.tsx
ui/src/hooks/
  useManifest.ts
  useSystemState.ts
  useSystemWebSocket.ts
  useTabs.ts
  useCommandPalette.ts
  useComponentFile.ts
  useAIContext.ts
ui/src/lib/
  manifest.ts
  layout-registry.ts
  ai-context-builder.ts
  component-type-detector.ts
ui/src/stores/
  tabStore.ts
  dashboardStore.ts

# Backend (server/)
server/routers/systems.py
server/services/manifest_service.py
server/services/system_state_service.py

# Config
.swarm/manifest.yaml  (per project — not in this repo)
```

## Appendix E: Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Manifest schema definition and parser
- [ ] `.swarm/manifest.yaml` reader on backend
- [ ] Meta dashboard with system cards
- [ ] Tab bar with system switching
- [ ] Pipeline layout (single layout type)
- [ ] Component sidebar
- [ ] Raw editor (CodeMirror) for all component types
- [ ] Basic system state display
- [ ] Route setup (`/#/dashboard`)

### Phase 2: Smart Editors
- [ ] Agent editor (structured form)
- [ ] Output viewer (JSON tree)
- [ ] Script editor (syntax highlighting + function list)
- [ ] Hook editor
- [ ] Schema editor
- [ ] "Test with Sample" for agents

### Phase 3: AI Integration
- [ ] AI context injection per level
- [ ] System-scoped AI conversations
- [ ] AI action confirmation flow
- [ ] "Open in AI" for outputs
- [ ] AI-assisted manifest creation

### Phase 4: Additional Layouts
- [ ] Swarm layout
- [ ] Graph layout
- [ ] Kanban layout
- [ ] Tree layout
- [ ] Custom layout engine

### Phase 5: Real-Time Monitoring
- [ ] WebSocket events for system execution
- [ ] Live stage card updates
- [ ] Log streaming
- [ ] Token tracking
- [ ] Progress bars

### Phase 6: Power Features
- [ ] Command palette (Ctrl+K)
- [ ] Cross-system search
- [ ] Template library
- [ ] System creation wizard
- [ ] Keyboard shortcut system
- [ ] Manifest diffing and versioning

## Appendix F: Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Manifest format | YAML | Human-readable, comment-friendly, standard in DevOps |
| State management | Zustand (client) + TanStack Query (server) | Zustand for fast UI state (tabs, panels), TanStack for cached server data |
| Editor | CodeMirror 6 | Extensible, lightweight, supports custom modes for structured editing |
| Layout system | CSS Grid + dagre | Grid for tabular layouts, dagre for graphs (already used by Autoforge) |
| AI context | Structured summary (not raw files) | Keeps context window small, focused on what matters at each level |
| Multi-system nav | Persistent tabs | Familiar pattern (browser tabs), preserves state per system |
| Backend integration | New router, not new service | Systems router calls existing Autoforge services where possible |
| Migration path | New route, old UI unchanged | Zero disruption to existing Autoforge users |

---

## Appendix G: Separation of Concerns — Workspace vs Software Factory

### The Two Systems

This project contains two completely independent systems that share infrastructure but never share runtime state:

| | Autoforge (Software Factory) | Universal Dashboard (Workspace) |
|--|--|--|
| **Purpose** | Builds applications autonomously | Manages, edits, and monitors automation systems |
| **Config directory** | `.autoforge/` | `.swarm/` |
| **Database** | `features.db` (SQLite, per-project) | `manifest.yaml` (YAML, per-system) |
| **Registry** | `~/.autoforge/registry.db` | `~/.swarm/registry.db` |
| **UI route** | `/#/` | `/#/dashboard` |
| **Backend router** | `server/routers/features.py`, `agent.py`, etc. | `server/routers/systems.py` (new) |
| **WebSocket** | `/ws/projects/{name}` | `/ws/systems/{id}` |
| **What it controls** | Agent execution, feature lifecycle, test results | Manifest reading, component editing, system monitoring |

### The Iron Rules

1. **The workspace NEVER writes to `.autoforge/`** — It can read Autoforge project data for display purposes (showing features on a kanban layout), but it never modifies `features.db`, never starts or stops Autoforge agents, never changes Autoforge configuration. Autoforge has its own UI for that.

2. **The workspace NEVER calls Autoforge agent functions** — It does not import from `agent.py`, `client.py`, `progress.py`, or any module that controls Autoforge's agent lifecycle. If the workspace needs to run a pipeline, it executes shell commands (same as a user would), not internal function calls.

3. **The workspace has its own state** — Tab state, AI conversations, manifest cache, system monitoring — all stored in `.swarm/` or in Zustand/TanStack client state. None of this touches Autoforge's data.

4. **Shared infrastructure is read-only** — The workspace uses the same React framework, Tailwind design system, WebSocket protocol, and FastAPI server. But these are infrastructure — like two apps running on the same operating system. Sharing React doesn't create coupling any more than two programs sharing Linux creates coupling.

5. **Component patterns are copied, not shared** — The workspace has its own `PipelineLayout.tsx`, inspired by but independent from Autoforge's `DependencyGraph.tsx`. The workspace has its own `StageCard.tsx`, not a re-export of Autoforge's feature cards. Same design language, separate code.

6. **If either system crashes, the other is unaffected** — A bug in the workspace's manifest parser cannot corrupt an Autoforge build. A bug in Autoforge's agent loop cannot crash the workspace. This is the test: can you delete the entire `.swarm/` directory and Autoforge still works perfectly? Yes. Can you delete `.autoforge/` and the dashboard still loads? Yes (it just shows no Autoforge-linked systems).

### Why This Matters

AI coding agents are powerful but they're not perfect. When an agent modifies code, there's always a risk of unintended side effects. By keeping the workspace and factory completely separated:

- An agent working on dashboard features cannot accidentally break the app-building pipeline
- An agent working on Autoforge cannot accidentally corrupt workspace state
- Testing one system doesn't require testing the other
- You can deploy updates to one without touching the other
- A third-party developer can work on the dashboard without needing to understand Autoforge internals

### For Future Developers

If you are an AI agent or human developer working on this codebase:

- **Working on the dashboard?** Stay in `ui/src/components/dashboard/`, `server/routers/systems.py`, and `.swarm/`. Do not import from or modify anything in `server/routers/features.py`, `agent.py`, `client.py`, or `.autoforge/`.
- **Working on Autoforge?** Stay in the existing Autoforge modules. Do not import from or modify anything in `server/routers/systems.py` or `.swarm/`.
- **Working on shared infrastructure** (FastAPI server setup, WebSocket protocol, React framework)? Changes here affect both systems — test both after any modification.

---

*End of specification. The Universal Dashboard extends Autoforge's existing React UI with manifest-driven, contextual AI workspaces. Each automation system declares its shape, and the dashboard renders a purpose-built environment with type-aware editors, scoped AI, and instant lateral navigation between systems.*
