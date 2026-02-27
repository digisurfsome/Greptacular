# PRD: Prompt Assembly & Agent Orchestration Dashboard

**Status:** Draft — Ready for Review
**Priority:** Critical
**Date:** 2026-02-27
**Codename:** LaunchPad

---

## 1. Summary

A visual dashboard for assembling multi-file agent prompts from reusable template blocks, calculating context window budgets, AI-chunking oversized PRDs into dependency-aware waves, and automatically orchestrating parallel agent execution — wave by wave — until the entire build completes with a final integration test.

**Two deployment modes:**
1. **Freestanding tool** — Generates a file bundle you copy/paste into any builder (Claude Code, Cursor, Windsurf, etc.)
2. **Workspace-integrated** — Plugs into the existing AutoForge workspace, auto-spins agents via `parallel_orchestrator.py`, and leverages the dependency graph

---

## 2. The Problem

Building a non-trivial app with AI agents today requires:
1. Writing a detailed PRD
2. Manually creating a context primer that explains the whole system
3. Manually writing build/test/lint configurations
4. Estimating whether it all fits in context (spoiler: it usually doesn't)
5. Manually splitting the PRD into chunks that make logical sense
6. Figuring out dependencies between chunks (what must build before what)
7. Organizing chunks into waves
8. Copy/pasting each wave's prompt into an agent session
9. Waiting, then copy/pasting the next wave
10. Running a final integration test

Steps 2-9 are repetitive, error-prone, and identical in structure across every project. This tool automates all of them.

---

## 3. Core Concept

### 3.1 The Assembly Metaphor

Think of it like a document builder with **blocks**. Each block is a prompt component:

```
┌─────────────────────────────────────────────────┐
│  LAUNCHPAD — Prompt Assembly                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  [📄 Context Primer]          ← auto-generated   │
│  ─────────────────────                           │
│  [📄 PRD / App Spec]          ← user paste/edit  │
│  ─────────────────────                           │
│  [📝 Custom Note]             ← free text block  │
│  ─────────────────────                           │
│  [📄 Build Config]            ← template          │
│  ─────────────────────                           │
│  [📄 Testing Strategy]        ← template          │
│  ─────────────────────                           │
│  [📄 Lint / Type-check]       ← template          │
│  ─────────────────────                           │
│  [📄 Agent OS Format]         ← template          │
│                                                  │
│  ↕ drag to reorder    [+ Add Block]             │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │  TOKEN BUDGET                            │    │
│  │  ████████████████░░░░░░░░  68,400 / 200K │    │
│  │  Base overhead: 22,100    PRD: 46,300    │    │
│  │  Remaining for agent work: 131,600       │    │
│  │  Status: ✅ FITS — single session         │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│       [ Generate Files ]  [ Launch Agents → ]   │
└─────────────────────────────────────────────────┘
```

### 3.2 What Happens When It Doesn't Fit

When the PRD exceeds the 50% context threshold (the point where agent performance degrades), the AI takes over:

```
┌─────────────────────────────────────────────────┐
│  TOKEN BUDGET                                    │
│  ████████████████████████████  142,000 / 200K    │
│  Base overhead: 22,100    PRD: 119,900           │
│  ⚠️  EXCEEDS 50% THRESHOLD (100K)                │
│                                                  │
│  AI recommends: Split into 3 waves               │
│                                                  │
│  [ Auto-Chunk PRD ]  [ Manual Split ]           │
└─────────────────────────────────────────────────┘
```

Clicking "Auto-Chunk" triggers the AI chunking engine (Section 5).

---

## 4. Block System

### 4.1 Block Types

| Block Type | Source | Editable | Project-Specific |
|-----------|--------|----------|------------------|
| **Context Primer** | Auto-generated from PRD | Yes (override) | Yes — generated per project |
| **PRD / App Spec** | User paste or file import | Yes | Yes |
| **Custom Note** | User-created free text | Yes | Yes |
| **Build Config** | Template library | Yes (customize) | Partially — framework-specific |
| **Testing Strategy** | Template library | Yes (customize) | Partially |
| **Lint / Type-check** | Template library | Yes (customize) | Partially |
| **Agent OS Format** | Template (standard) | Yes (customize) | No — universal |
| **CLAUDE.md** | Auto-generated | Yes (override) | Yes |
| **Dependency Map** | Auto-generated from chunks | Read-only | Yes |

### 4.2 Block Operations

- **Add** — From template library or blank
- **Remove** — Delete a block
- **Reorder** — Drag-and-drop to change sequence
- **Edit** — Inline text editor per block
- **Duplicate** — Copy a block (useful for variant configs)
- **Collapse/Expand** — Toggle block visibility
- **Lock** — Prevent accidental edits to finalized blocks

### 4.3 Template Library

Pre-built blocks that ship with the tool, organized by category:

**Universal (every project):**
- Agent OS system prompt format
- Standard testing patterns (unit, integration, e2e)
- Standard lint/format configs (ESLint, Ruff, Prettier)
- Git commit conventions
- Error handling patterns

**Framework-specific:**
- React + Vite + Tailwind build config
- Next.js build config
- Python + FastAPI build config
- Node.js + Express build config
- Flutter build config

**Custom (user-created):**
- Users save their own blocks to a personal library
- Shareable as JSON exports

### 4.4 Context Primer Generation

The Context Primer is the most important auto-generated block. When the user pastes/writes their PRD, the AI reads it and generates a primer that:

1. Summarizes the entire application in 2-3 paragraphs
2. Lists all major systems and how they connect
3. Defines the tech stack and architecture pattern
4. Describes the data model at a high level
5. Identifies key constraints and non-obvious decisions

This block is generated **after the PRD is finalized** because it must reflect the complete picture. It's the "explain the whole app to an agent that's never seen it" document.

**Sequence dependency:** PRD must be complete → then Context Primer is generated → then token math is calculated.

---

## 5. Token Math Engine

### 5.1 The Problem It Solves

AI coding agents have a context window (e.g., 200K tokens for Opus). As context fills up, quality degrades. The industry consensus is that crossing ~50% utilization starts degrading output quality. This engine calculates exactly where you stand.

### 5.2 Token Counting

Every block in the assembly gets token-counted in real-time:

```
Token Breakdown:
─────────────────────────────────
Context Primer         4,200 tokens
PRD / App Spec        46,300 tokens
Build Config           2,800 tokens
Testing Strategy       3,100 tokens
Lint / Type-check      1,200 tokens
Agent OS Format        8,500 tokens
CLAUDE.md              1,900 tokens
─────────────────────────────────
TOTAL PROMPT:         68,000 tokens
─────────────────────────────────
```

### 5.3 Budget Calculation

```
Model Context Window:         200,000 tokens
─────────────────────────────────────────────
50% Safety Line:              100,000 tokens
Prompt (assembled blocks):    -68,000 tokens
─────────────────────────────────────────────
Available for agent work:      32,000 tokens
─────────────────────────────────────────────
Status: ✅ FITS — 32K remaining for agent code generation
```

### 5.4 The "Cab Ride Cost"

This is the base overhead — the tokens consumed by blocks that are **project-agnostic** and present in every session regardless of PRD content:

```
Cab Ride Cost (fixed overhead):
─────────────────────────────────
Agent OS Format        8,500 tokens
Build Config           2,800 tokens
Testing Strategy       3,100 tokens
Lint / Type-check      1,200 tokens
CLAUDE.md              1,900 tokens
─────────────────────────────────
FIXED OVERHEAD:       17,500 tokens
─────────────────────────────────
```

This matters for chunking. When the AI splits a PRD, each chunk must carry this overhead. So available space per chunk is:

```
Per-chunk budget = (model_window * 0.50) - cab_ride_cost - context_primer_tokens
                 = 100,000 - 17,500 - 4,200
                 = 78,300 tokens available for PRD content per chunk
```

If your PRD is 150,000 tokens, you need ceil(150,000 / 78,300) = **2 chunks minimum**. But the AI may create more chunks based on logical boundaries (you don't split mid-feature).

### 5.5 Model Presets

| Model | Context Window | 50% Line | Notes |
|-------|---------------|----------|-------|
| Opus 200K | 200,000 | 100,000 | Default |
| Opus 1M | 1,000,000 | 500,000 | Extended context |
| Sonnet 200K | 200,000 | 100,000 | Faster, cheaper |
| Sonnet 1M | 1,000,000 | 500,000 | Extended fast |

User selects the model they'll run agents with. Budget math adjusts automatically.

### 5.6 Adjustable Safety Threshold

Default is 50%, but users can adjust:
- **Conservative (40%)** — Maximum quality, most chunks
- **Standard (50%)** — Balanced (recommended)
- **Aggressive (65%)** — Fewer chunks, risk of quality degradation
- **Custom** — User sets their own percentage

---

## 6. AI Chunking Engine

### 6.1 When It Activates

Triggered when: `total_prompt_tokens > (model_window * safety_threshold)`

### 6.2 What the AI Does

The chunking AI (runs inside the tool, separate from the build agents) performs:

1. **Reads the full PRD** to understand all features, dependencies, and architecture
2. **Identifies natural boundaries** — features that are logically self-contained
3. **Calculates chunk count** — Based on token math (Section 5.4)
4. **Groups features into chunks** respecting:
   - Logical cohesion (related features stay together)
   - Dependency order (foundations before features that need them)
   - Token budget per chunk (never exceeds the per-chunk limit)
   - Testing boundaries (each chunk should be independently testable)
5. **Assigns dependencies between chunks** — Which chunks must complete before others can start
6. **Organizes chunks into waves** — Chunks with no unmet dependencies form a wave

### 6.3 Chunking Output

```json
{
  "chunk_plan": {
    "model": "opus_200k",
    "safety_threshold": 0.50,
    "total_prd_tokens": 150000,
    "cab_ride_cost": 17500,
    "context_primer_tokens": 4200,
    "per_chunk_budget": 78300,
    "min_chunks": 2,
    "actual_chunks": 4,
    "reason": "Logical boundaries required 4 chunks instead of minimum 2",
    "chunks": [
      {
        "chunk_id": 1,
        "name": "Foundation — Database, Auth, Core API",
        "token_count": 38200,
        "features": ["database-schema", "auth-system", "core-api-routes"],
        "dependencies": [],
        "wave": 1,
        "test_criteria": "DB migrations run, auth flow works, API returns 200"
      },
      {
        "chunk_id": 2,
        "name": "UI Shell — Layout, Navigation, Design System",
        "token_count": 42100,
        "features": ["app-layout", "navigation", "design-tokens", "component-library"],
        "dependencies": [],
        "wave": 1,
        "test_criteria": "App renders, navigation works, components display"
      },
      {
        "chunk_id": 3,
        "name": "Feature Set A — Dashboard, Analytics, Charts",
        "token_count": 35800,
        "features": ["dashboard-page", "analytics-engine", "chart-components"],
        "dependencies": [1, 2],
        "wave": 2,
        "test_criteria": "Dashboard loads with real data, charts render"
      },
      {
        "chunk_id": 4,
        "name": "Feature Set B — Settings, Export, Notifications",
        "token_count": 33900,
        "features": ["settings-page", "data-export", "notification-system"],
        "dependencies": [1, 2],
        "wave": 2,
        "test_criteria": "Settings save, export downloads file, notifications display"
      }
    ],
    "waves": [
      {"wave": 1, "chunks": [1, 2], "parallel_agents": 2},
      {"wave": 2, "chunks": [3, 4], "parallel_agents": 2},
      {"wave": 3, "chunks": ["integration-test"], "parallel_agents": 1}
    ]
  }
}
```

### 6.4 User Review & Adjustment

After auto-chunking, the user sees a visual breakdown and can:
- **Move features** between chunks (recalculates token counts)
- **Split a chunk** further if it's too heavy
- **Merge chunks** if they're small enough to combine
- **Change dependencies** (with cycle detection — uses existing `dependency_resolver.py` Kahn's algorithm)
- **Re-run AI analysis** after manual adjustments

---

## 7. Wave Orchestration Engine

### 7.1 How Waves Work

```
WAVE 1 (parallel)          WAVE 2 (parallel)         WAVE 3 (serial)
┌──────────┐ ┌──────────┐  ┌──────────┐ ┌──────────┐  ┌──────────────────┐
│ Chunk 1  │ │ Chunk 2  │  │ Chunk 3  │ │ Chunk 4  │  │ Integration Test │
│ Foundation│ │ UI Shell │  │ Dashboard│ │ Settings │  │ Full system test │
│ Agent 1  │ │ Agent 2  │  │ Agent 1  │ │ Agent 2  │  │ Agent 1          │
└──────────┘ └──────────┘  └──────────┘ └──────────┘  └──────────────────┘
     │              │            │              │              │
     ▼              ▼            ▼              ▼              ▼
  ✅ PASS        ✅ PASS      ✅ PASS       ✅ PASS        ✅ PASS
                                                              │
                                                         BUILD COMPLETE
```

### 7.2 Execution Modes

**Mode 1: Freestanding (Copy/Paste)**

The tool generates a file bundle:
```
output/
  wave-1/
    agent-1-prompt.md       # Foundation chunk + all template blocks
    agent-2-prompt.md       # UI Shell chunk + all template blocks
  wave-2/
    agent-1-prompt.md       # Dashboard chunk + all template blocks
    agent-2-prompt.md       # Settings chunk + all template blocks
  wave-3/
    integration-test.md     # Final test prompt
  execution-guide.md        # Human-readable wave-by-wave instructions
  launch-plan.json          # Machine-readable execution plan
```

Each prompt file is a complete, self-contained document: the chunk's PRD content + context primer + all template blocks assembled in the user's chosen order. Copy/paste into any agent tool.

**Mode 2: Workspace-Integrated (Auto-Launch)**

Pressing "Launch Agents" triggers:
1. Converts chunks to AutoForge features via `feature_create_bulk`
2. Sets dependencies via `feature_add_dependency` (with cycle detection)
3. Calls `parallel_orchestrator.py` which:
   - Spawns agents for Wave 1 chunks (up to `MAX_PARALLEL_AGENTS = 5`)
   - Each agent claims its chunk via `feature_claim_and_get`
   - Monitors completion, blocks Wave 2 until Wave 1 dependencies are met
   - Spawns Wave 2 agents when ready
   - Continues until all waves complete
4. Runs final integration test as the last wave
5. Reports results back to the dashboard

### 7.3 Wave Dashboard (Real-Time)

```
┌──────────────────────────────────────────────────────────┐
│  LAUNCHPAD — Wave Execution                               │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Wave 1 ████████████████████████████ COMPLETE (2/2)       │
│    ├─ Chunk 1: Foundation ✅ 4m 23s (Agent: Spark)        │
│    └─ Chunk 2: UI Shell   ✅ 3m 51s (Agent: Fizz)        │
│                                                           │
│  Wave 2 ██████████░░░░░░░░░░░░░░░░░ IN PROGRESS (1/2)    │
│    ├─ Chunk 3: Dashboard  🔄 2m 10s (Agent: Octo)        │
│    └─ Chunk 4: Settings   ✅ 3m 02s (Agent: Hoot)        │
│                                                           │
│  Wave 3 ░░░░░░░░░░░░░░░░░░░░░░░░░░░ QUEUED               │
│    └─ Integration Test    ⏳ Waiting for Wave 2           │
│                                                           │
│  [ Pause All ]  [ Cancel ]  [ View Logs ]                │
└──────────────────────────────────────────────────────────┘
```

Uses existing WebSocket infrastructure (`/ws/projects/{project_name}`) with `agent_update` messages for real-time status and mascot assignments (Spark, Fizz, Octo, Hoot, Buzz).

### 7.4 Integration with Existing AutoForge Systems

| LaunchPad Component | AutoForge System | Integration Point |
|--------------------|--------------------|-------------------|
| Chunks → Features | `feature_create_bulk` | MCP tool via `mcp_server/feature_mcp.py` |
| Chunk dependencies | `feature_add_dependency` | Uses `dependency_resolver.py` cycle detection |
| Wave visualization | `DependencyGraph.tsx` | Reuse dagre graph layout component |
| Agent spawning | `parallel_orchestrator.py` | `MAX_PARALLEL_AGENTS = 5`, atomic claim |
| Progress tracking | `progress.py` | WebSocket `progress` + `agent_update` messages |
| Agent mascots | `AgentMissionControl.tsx` | Spark, Fizz, Octo, Hoot, Buzz |
| Context tracking | `DunkStackContextGauge` | Token counting + safety thresholds |

---

## 8. Prompt Chain Sequence

The tool enforces a specific generation order because blocks have data dependencies:

```
Step 1: User pastes/writes PRD
            │
Step 2: AI generates Context Primer (needs complete PRD)
            │
Step 3: User selects/customizes template blocks
            │
Step 4: Token Math calculates budget (needs all blocks)
            │
Step 5: If over threshold → AI Chunking (needs PRD + budget)
            │
Step 6: User reviews/adjusts chunks and waves
            │
Step 7: Generate output files OR launch agents
```

### 8.1 What's Automatic vs. Manual

| Step | Automatic | Manual | Notes |
|------|-----------|--------|-------|
| PRD input | - | User writes/pastes | Core creative work |
| Context Primer | AI generates | User can edit | Override if AI misunderstands |
| Template blocks | Pre-loaded defaults | User adds/removes/reorders | Most users keep defaults |
| Token counting | Real-time calculation | - | Updates on every edit |
| Chunk decision | AI recommends | User approves | Shows math transparently |
| Chunking | AI splits | User adjusts boundaries | Drag features between chunks |
| Dependencies | AI infers | User validates | Cycle detection prevents errors |
| Wave assignment | Auto from dependencies | User can override | Topological sort |
| Agent OS formatting | Auto template | User can customize | Standard format wraps each chunk |
| File generation | Auto | - | One click |
| Agent launch | Auto (workspace mode) | Copy/paste (freestanding) | Both produce same output |

---

## 9. Data Model

### 9.1 Assembly (SQLite — `launchpad.db`)

```sql
CREATE TABLE assemblies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    project_name TEXT,                    -- NULL for freestanding
    model_preset TEXT DEFAULT 'opus_200k',
    safety_threshold REAL DEFAULT 0.50,
    status TEXT DEFAULT 'draft',          -- draft, chunked, ready, executing, complete
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blocks (
    id INTEGER PRIMARY KEY,
    assembly_id INTEGER REFERENCES assemblies(id),
    block_type TEXT NOT NULL,             -- primer, prd, note, build, test, lint, agent_os, claudemd, depmap
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    token_count INTEGER DEFAULT 0,
    sort_order INTEGER NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,    -- TRUE = from template library
    template_id TEXT,                     -- reference to template source
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    assembly_id INTEGER REFERENCES assemblies(id),
    chunk_index INTEGER NOT NULL,
    name TEXT NOT NULL,
    prd_content TEXT NOT NULL,            -- the PRD slice for this chunk
    token_count INTEGER DEFAULT 0,
    wave INTEGER NOT NULL,
    test_criteria TEXT,
    status TEXT DEFAULT 'pending',        -- pending, in_progress, passed, failed
    agent_name TEXT,                      -- mascot name when running
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE chunk_dependencies (
    chunk_id INTEGER REFERENCES chunks(id),
    depends_on_chunk_id INTEGER REFERENCES chunks(id),
    PRIMARY KEY (chunk_id, depends_on_chunk_id)
);

CREATE TABLE template_library (
    id TEXT PRIMARY KEY,                  -- e.g., 'build-react-vite'
    category TEXT NOT NULL,               -- universal, framework, custom
    name TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    framework TEXT,                       -- NULL for universal
    is_builtin BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 9.2 Token Budget Snapshot

Calculated on-the-fly, not stored. Computed from block and chunk token counts against model preset.

---

## 10. API Endpoints

### 10.1 REST Routes (`server/routers/launchpad.py`)

```
# Assembly CRUD
GET    /api/launchpad/assemblies              — List all assemblies
POST   /api/launchpad/assemblies              — Create new assembly
GET    /api/launchpad/assemblies/{id}         — Get assembly with blocks
PUT    /api/launchpad/assemblies/{id}         — Update assembly settings
DELETE /api/launchpad/assemblies/{id}         — Delete assembly

# Block CRUD
GET    /api/launchpad/assemblies/{id}/blocks  — List blocks in order
POST   /api/launchpad/assemblies/{id}/blocks  — Add block
PUT    /api/launchpad/blocks/{block_id}       — Update block content
DELETE /api/launchpad/blocks/{block_id}       — Remove block
PUT    /api/launchpad/assemblies/{id}/blocks/reorder — Reorder blocks (array of IDs)

# Token Math
GET    /api/launchpad/assemblies/{id}/budget  — Calculate full token budget

# AI Operations
POST   /api/launchpad/assemblies/{id}/generate-primer  — AI generates context primer
POST   /api/launchpad/assemblies/{id}/chunk             — AI chunks the PRD
PUT    /api/launchpad/chunks/{chunk_id}                 — Update chunk (move features)
POST   /api/launchpad/assemblies/{id}/rechunk           — Re-run chunking after edits

# Wave Execution
POST   /api/launchpad/assemblies/{id}/generate-files    — Generate output file bundle
POST   /api/launchpad/assemblies/{id}/launch             — Launch agents (workspace mode)
GET    /api/launchpad/assemblies/{id}/status              — Execution status
POST   /api/launchpad/assemblies/{id}/pause               — Pause execution
POST   /api/launchpad/assemblies/{id}/cancel              — Cancel execution

# Template Library
GET    /api/launchpad/templates                 — List templates (filterable)
POST   /api/launchpad/templates                 — Create custom template
DELETE /api/launchpad/templates/{id}            — Delete custom template
```

### 10.2 WebSocket (`/ws/launchpad/{assembly_id}`)

Real-time events during execution:

```json
{"type": "wave_started",     "wave": 1, "agents": 2}
{"type": "chunk_started",    "chunk_id": 1, "agent": "Spark"}
{"type": "chunk_progress",   "chunk_id": 1, "log": "Installing dependencies..."}
{"type": "chunk_completed",  "chunk_id": 1, "status": "passed", "duration": 263}
{"type": "wave_completed",   "wave": 1, "passed": 2, "failed": 0}
{"type": "wave_started",     "wave": 2, "agents": 2}
{"type": "integration_test", "status": "running"}
{"type": "build_complete",   "status": "passed", "total_duration": 847}
```

---

## 11. UI Components

### 11.1 New Components

| Component | Purpose |
|-----------|---------|
| `LaunchPadPage.tsx` | Main page — block assembly + token budget + execution |
| `BlockEditor.tsx` | Individual block card with inline editor, drag handle, token count |
| `BlockList.tsx` | Sortable list of blocks (drag-and-drop via `@dnd-kit/sortable`) |
| `TokenBudget.tsx` | Token budget bar with breakdown, cab ride cost, status indicator |
| `ChunkView.tsx` | Visual chunk card showing features, token count, wave assignment |
| `ChunkEditor.tsx` | Drag features between chunks, merge/split chunks |
| `WavePipeline.tsx` | Horizontal pipeline showing Wave 1 → Wave 2 → ... → Integration |
| `WaveExecutionDashboard.tsx` | Real-time execution progress with agent mascots |
| `TemplateLibrary.tsx` | Browse/search/add templates organized by category |
| `LaunchPadSettings.tsx` | Model preset selector, safety threshold slider |

### 11.2 Reused Components

| Existing Component | Reuse |
|-------------------|-------|
| `DependencyGraph.tsx` | Chunk dependency visualization (dagre layout) |
| `AgentMissionControl.tsx` | Agent mascot display during execution |
| `CelebrationOverlay.tsx` | Confetti on build complete |
| `DunkStackContextGauge` | Token budget visualization pattern |

### 11.3 Page Layout

```
┌──────────────────────────────────────────────────────────────┐
│  ← AutoForge / LaunchPad                    [Settings] [?]   │
├────────────┬─────────────────────────────────────────────────┤
│            │                                                  │
│  BLOCKS    │   EDITOR / PREVIEW                              │
│            │                                                  │
│ ┌────────┐ │   Selected block content editor                  │
│ │Primer  │ │   with syntax highlighting                       │
│ ├────────┤ │   and token count display                        │
│ │PRD     │ │                                                  │
│ ├────────┤ │                                                  │
│ │Build   │ │                                                  │
│ ├────────┤ │                                                  │
│ │Test    │ │                                                  │
│ ├────────┤ │                                                  │
│ │Lint    │ │                                                  │
│ ├────────┤ │                                                  │
│ │Agent OS│ │                                                  │
│ └────────┘ │                                                  │
│            │                                                  │
│ [+Add]     │  ┌──────────────────────────────────────────┐   │
│            │  │ TOKEN BUDGET:  ██████░░░  68K / 200K ✅  │   │
│ ────────── │  └──────────────────────────────────────────┘   │
│ TEMPLATES  │                                                  │
│ Universal  │  [ Generate Files ]  [ Launch Agents → ]        │
│ React      │                                                  │
│ Python     │                                                  │
│ Custom     │                                                  │
│            │                                                  │
├────────────┴─────────────────────────────────────────────────┤
│  (When chunked: Wave Pipeline view replaces editor)          │
│  Wave 1: [Chunk 1] [Chunk 2]  →  Wave 2: [Chunk 3] [Chunk 4]│
│                                  →  Wave 3: [Integration]     │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. Token Counting Implementation

### 12.1 Approach

Use `tiktoken` (Python) for accurate GPT-compatible token counts on the backend. The frontend displays counts returned by the API.

```python
# server/services/token_counter.py
import tiktoken

# cl100k_base is close enough for Claude token estimation
encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoder.encode(text))

def calculate_budget(blocks: list[Block], model_preset: str, safety_threshold: float) -> dict:
    model_windows = {
        "opus_200k": 200_000,
        "opus_1m": 1_000_000,
        "sonnet_200k": 200_000,
        "sonnet_1m": 1_000_000,
    }
    window = model_windows[model_preset]
    safety_line = int(window * safety_threshold)

    block_counts = [(b.title, count_tokens(b.content)) for b in blocks]
    total = sum(c for _, c in block_counts)

    # Cab ride = everything except the PRD block
    prd_tokens = sum(c for t, c in block_counts if "prd" in t.lower() or "spec" in t.lower())
    cab_ride = total - prd_tokens

    return {
        "model_window": window,
        "safety_line": safety_line,
        "total_tokens": total,
        "prd_tokens": prd_tokens,
        "cab_ride_cost": cab_ride,
        "remaining": safety_line - total,
        "fits": total <= safety_line,
        "utilization": total / window,
        "breakdown": block_counts,
    }
```

### 12.2 Real-Time Updates

Token counts recalculate on block content change. Debounced at 500ms to avoid excessive API calls during typing.

---

## 13. AI Chunking Implementation

### 13.1 Chunking Prompt

The chunking AI receives:
- The full PRD text
- The token budget (per-chunk limit, cab ride cost)
- Feature list extracted from the PRD

It returns a structured chunk plan (Section 6.3 schema).

### 13.2 Dependency Inference

The AI infers dependencies by analyzing:
- Data model references (feature B reads table created by feature A)
- UI dependencies (page C needs navigation built in chunk B)
- API dependencies (frontend D calls API built in chunk A)

Dependencies are validated using the existing `dependency_resolver.py`:
- **Kahn's algorithm** for topological sort (wave assignment)
- **DFS** for cycle detection (prevents circular dependencies)

### 13.3 Wave Assignment

Chunks are assigned to waves by topological sort:
- **Wave 1:** Chunks with zero dependencies
- **Wave 2:** Chunks whose dependencies are all in Wave 1
- **Wave N:** Chunks whose dependencies are all in Waves < N
- **Final Wave:** Integration test (depends on all other waves)

---

## 14. File Generation (Freestanding Mode)

### 14.1 Per-Chunk Prompt File

Each generated prompt file is a complete, self-contained document assembled from the user's blocks:

```markdown
# [Agent OS Format Header]

## Context Primer
[Auto-generated primer content]

## Application Specification — Chunk 1: Foundation
[PRD content for this chunk only]

## Build Configuration
[Build config block content]

## Testing Strategy
[Testing block content]
[Chunk-specific test criteria appended]

## Code Quality
[Lint/type-check block content]

# [Any custom note blocks the user added]
```

### 14.2 Execution Guide

A human-readable `execution-guide.md` that explains:
- How many waves and why
- What each wave builds
- Dependencies between waves
- Test criteria per chunk
- Step-by-step instructions for manual execution

### 14.3 Launch Plan JSON

Machine-readable `launch-plan.json` for tools that can consume structured plans:

```json
{
  "version": "1.0.0",
  "model": "opus_200k",
  "waves": [...],
  "chunks": [...],
  "total_estimated_cost": "$X.XX",
  "files": {
    "wave-1/agent-1-prompt.md": "sha256:...",
    "wave-1/agent-2-prompt.md": "sha256:..."
  }
}
```

---

## 15. Workspace Integration (Auto-Launch Mode)

### 15.1 Bridge to AutoForge

When the user clicks "Launch Agents" in workspace mode:

1. **Create AutoForge features** from chunks:
   ```python
   for chunk in chunks:
       feature_create(
           name=chunk.name,
           description=chunk.prd_content,
           steps=chunk.test_criteria,
           priority=chunk.wave  # Wave number = priority
       )
   ```

2. **Set dependencies** via `feature_add_dependency`:
   ```python
   for chunk in chunks:
       for dep_id in chunk.dependencies:
           feature_add_dependency(chunk.feature_id, dep_id)
   ```

3. **Launch orchestrator** — calls `parallel_orchestrator.py` which:
   - Reads the dependency graph from `features.db`
   - Spawns agents for Wave 1 features (up to `MAX_PARALLEL_AGENTS`)
   - Each agent receives the assembled prompt (template blocks + chunk PRD)
   - Monitors completion, respects dependencies
   - Spawns next wave when dependencies are met
   - Continues until all waves complete

4. **Integration test** — final wave runs a comprehensive test agent

### 15.2 Prompt Delivery

Each spawned agent receives its prompt via the existing `prompts.py` fallback chain:
- LaunchPad writes the assembled prompt to `.autoforge/prompts/coding_prompt.md`
- Agent picks it up on startup
- Each chunk's specific PRD content is loaded as the feature description

---

## 16. Monetization Considerations

### 16.1 Freestanding Version

**Free tier:**
- Basic block assembly (up to 5 blocks)
- Token counting
- Manual chunking

**Paid tier:**
- AI context primer generation
- AI auto-chunking
- Template library (full)
- File bundle generation

### 16.2 Workspace-Integrated Version

**Included with AutoForge workspace** — the auto-launch feature is the premium upgrade:
- Everything in paid freestanding tier
- Automatic agent orchestration
- Real-time wave dashboard
- Agent mascots and progress tracking

**User pays their own API key costs** — LaunchPad just orchestrates. The AI token costs for building are on the user's API key. LaunchPad's own AI costs (primer generation, chunking) are minimal (one or two Sonnet calls).

---

## 17. Implementation Waves

### Wave 1: Core Assembly (No AI)
- Block system with CRUD and drag-and-drop reorder
- Template library with built-in templates
- Token counting (real-time)
- Token budget display with cab ride cost
- Model preset selector
- File generation (freestanding mode — manual chunking only)

### Wave 2: AI Intelligence
- Context primer auto-generation
- AI chunking engine
- Dependency inference and cycle detection
- Wave assignment via topological sort
- Chunk editor (move features between chunks)
- Chunk dependency graph (reuse `DependencyGraph.tsx`)

### Wave 3: Orchestration
- Wave execution engine (bridge to `parallel_orchestrator.py`)
- Real-time wave dashboard with WebSocket
- Agent mascot assignment
- Pause/cancel controls
- Integration test as final wave
- Build completion celebration (reuse `CelebrationOverlay.tsx`)

### Wave 4: Polish
- Custom template creation and export
- Assembly save/load (resume later)
- Execution history
- Cost estimation
- LaunchPad-specific keyboard shortcuts

---

## 18. Files to Create

| File | Purpose |
|------|---------|
| `server/routers/launchpad.py` | REST + WebSocket endpoints |
| `server/services/launchpad_service.py` | Assembly, chunking, wave execution logic |
| `server/services/token_counter.py` | Token counting with tiktoken |
| `server/models/launchpad.py` | SQLAlchemy models (Assembly, Block, Chunk, Template) |
| `ui/src/pages/LaunchPadPage.tsx` | Main page component |
| `ui/src/components/launchpad/BlockEditor.tsx` | Block card with editor |
| `ui/src/components/launchpad/BlockList.tsx` | Sortable block list |
| `ui/src/components/launchpad/TokenBudget.tsx` | Token budget visualization |
| `ui/src/components/launchpad/ChunkView.tsx` | Chunk card |
| `ui/src/components/launchpad/ChunkEditor.tsx` | Chunk adjustment UI |
| `ui/src/components/launchpad/WavePipeline.tsx` | Wave visualization |
| `ui/src/components/launchpad/WaveExecutionDashboard.tsx` | Real-time execution |
| `ui/src/components/launchpad/TemplateLibrary.tsx` | Template browser |
| `ui/src/hooks/useLaunchPad.ts` | React Query hooks for API |
| `ui/src/hooks/useLaunchPadWebSocket.ts` | WebSocket for execution events |

## 19. Files to Modify

| File | Change |
|------|--------|
| `ui/src/main.tsx` | Add `/#/launchpad` route |
| `server/main.py` | Mount `launchpad` router |
| `requirements.txt` | Add `tiktoken` dependency |
| `ui/src/lib/types.ts` | Add LaunchPad TypeScript types |
| `ui/src/components/Sidebar.tsx` (or equivalent nav) | Add LaunchPad nav item |

---

## 20. Success Criteria

- [ ] User can assemble prompt from template blocks with drag-and-drop reorder
- [ ] Token budget displays in real-time with cab ride cost breakdown
- [ ] AI generates context primer from PRD content
- [ ] AI auto-chunks PRD when it exceeds the safety threshold
- [ ] User can adjust chunks (move features, merge, split)
- [ ] Dependency graph visualizes chunk relationships with cycle detection
- [ ] Freestanding mode generates complete file bundle
- [ ] Workspace mode auto-launches agents wave-by-wave
- [ ] Real-time wave dashboard shows agent progress with mascots
- [ ] Integration test runs as final wave
- [ ] Build completion triggers celebration overlay
- [ ] `npm run build` succeeds with no TypeScript errors
- [ ] `npm run lint` passes

---

## 21. Why This Matters

Seven months of manually doing this workflow distilled into one tool. Every time you build an app with AI agents, you do the same dance: write the PRD, write the primer, figure out if it fits, manually chunk it, manually figure out the order, manually spin up agents.

This tool turns "2 hours of copy-paste orchestration" into "paste your PRD, click Launch, go get coffee."

And because the base components (build config, test strategy, lint rules, agent OS format) are templatized and reusable, every subsequent project starts at 80% assembled instead of 0%.
