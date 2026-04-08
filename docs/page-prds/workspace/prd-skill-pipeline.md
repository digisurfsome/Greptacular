# PRD: Skill Pipeline — Sequential Prompt Chain for Workspace

> **Page:** WorkspacePage (`/#/workspace`)
> **Feature:** Skill Pipeline panel (alongside Swarm / Factory)
> **Status:** Draft
> **Date:** 2026-04-04

---

## Agent OS Context

### STANDARDS

#### Architecture Patterns
- **One WebSocket per page** — all pipeline events flow through the existing `ws://localhost:8888/api/workspace/ws` connection. No new WebSocket connections.
- **Subscription auth only** — all Claude calls use `force_subscription=True` via `get_effective_sdk_env()`. No API keys.
- **SDK client pattern** — use `permission_mode="acceptEdits"` + settings file. Wrap `receive_response()` in try/except for rate_limit_event recovery. Pass `on_progress` callbacks through.
- **Neobrutalism design system** — Tailwind CSS v4, CSS variables from `globals.css`, existing color tokens (`neo-pending`, `neo-progress`, `neo-done`).
- **Backend services pattern** — Python async services in `server/services/`, FastAPI routers in `server/routers/`, SQLite persistence via SQLAlchemy.

#### Coding Conventions
- Python: ruff (line length 120, Python 3.11 target), mypy strict returns
- TypeScript: ESLint, React 19, TanStack Query, Radix UI primitives
- File organization: services in `server/services/`, routers in `server/routers/`, components in `ui/src/components/workspace/`

### PRODUCT

#### Vision
AutoForge is an autonomous coding agent system. The Workspace is its interactive AI chat environment with full read/write capabilities, 1M-token context, and real-time streaming.

The **Skill Pipeline** extends the Workspace to support sequential prompt chains — a user loads N skill prompts (markdown), the pipeline runs them one after another through Claude, and the output of each skill feeds as context into the next. This automates multi-step workflows like the 11-stage PRD Maker pipeline.

#### Use Case: PRD Maker Pipeline
The immediate use case is running the 11-stage PRD Maker pipeline (Stages 0-10) that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage has:
- A **skill prompt** (markdown file, ~500-700 lines) that instructs Claude what to do
- A **completion contract** (criteria that must be true before advancing)
- An **output** that feeds into the next stage's context
- Some stages are **interactive** (need user answers), others are **autonomous**

#### Roadmap Position
This is the first pipeline-capable feature in the Workspace. Future uses: any sequential prompt chain, automated code review pipelines, multi-step research workflows.

---

## SPEC: Skill Pipeline Feature

### 1. Overview

A new panel mode in the Workspace (toggle button next to Swarm/Factory) that lets users:
1. Configure a pipeline of N skill prompts (upload files or paste text, editable inline)
2. Set a kickoff message and token budget
3. Run the pipeline sequentially — output of skill N feeds as context to skill N+1
4. Watch progress in real-time (which stage is running, completed, failed)
5. Export all outputs as a single combined file when done

### 2. UI Design

#### 2.1 Toggle Button
- New button in the WorkspacePage toolbar (line ~438) next to Swarm/Factory
- Icon: `Workflow` from lucide-react (or `ListOrdered`)
- Label: "Pipeline"
- Color when active: `bg-emerald-600 text-white hover:bg-emerald-700`
- Clicking toggles the PipelinePanel open/closed (same pattern as SwarmPanel)

#### 2.2 PipelinePanel Component
Slides in from the right side of the Workspace (same position as SwarmPanel). Two modes:

**Configure Mode** (before running):
```
┌──────────────────────────────────────────┐
│  ⚡ Skill Pipeline                    ✕  │
├──────────────────────────────────────────┤
│                                          │
│  Kickoff Message:                        │
│  ┌────────────────────────────────────┐  │
│  │ [textarea - message to start       │  │
│  │  skill 1]                          │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Token Budget:  [400K ▾]                 │
│  Model:         [opus ▾]                 │
│                                          │
│  ── Skills ──────────────────────────    │
│                                          │
│  1. [📎 Upload] Stage 0: Technical Fo…  │
│     ┌────────────────────────────────┐   │
│     │ [editable textarea showing     │   │
│     │  skill content, collapsed by   │   │
│     │  default, expandable]          │   │
│     └────────────────────────────────┘   │
│                                          │
│  2. [📎 Upload] Stage 1: Idea Capture   │
│     [collapsed]                          │
│                                          │
│  ... (up to 11+ skills) ...             │
│                                          │
│  [+ Add Skill]                           │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │    ⚡ Launch Pipeline              │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Running Mode** (during execution):
```
┌──────────────────────────────────────────┐
│  ⚡ Skill Pipeline — Running          ✕  │
├──────────────────────────────────────────┤
│                                          │
│  ■ Stop Pipeline                         │
│                                          │
│  Token Budget: 400K │ Used: 127K         │
│  ━━━━━━━━━━░░░░░░░░░░░░░░░  32%         │
│                                          │
│  ── Progress ────────────────────────    │
│                                          │
│  ✅ 1. Stage 0: Technical Foundation     │
│     3,241 tokens · 45s                   │
│     [▸ View Output]                      │
│                                          │
│  ✅ 2. Stage 1: Idea Capture             │
│     2,876 tokens · 38s                   │
│     [▸ View Output]                      │
│                                          │
│  🔄 3. Stage 2: Gap Analysis             │
│     Running... 1,204 tokens so far       │
│     [Streaming output preview...]        │
│                                          │
│  ⏳ 4. Stage 3: Agent OS Structuring     │
│  ⏳ 5. Stage 4: Mechanism Extraction     │
│  ... remaining stages ...                │
│                                          │
│  ── When Complete ───────────────────    │
│  [📥 Download All Outputs]               │
│                                          │
└──────────────────────────────────────────┘
```

#### 2.3 Skill Slot Behavior
- Each skill slot has:
  - A **number** (position in sequence)
  - A **label** (auto-extracted from first `# heading` in content, or "Skill N")
  - A **file upload button** (📎) that reads `.md` file and populates the textarea
  - An **editable textarea** — collapsed by default (shows first line), click to expand for full editing
  - A **delete button** (✕) to remove the skill
- Skills can be reordered via drag-and-drop (optional v2, not required for v1)
- "Add Skill" button appends a new empty slot

#### 2.4 Output Viewer
- Each completed stage has a collapsible "View Output" section
- Shows the full text output from that stage
- When all stages complete, "Download All Outputs" button generates a single markdown file:

```markdown
# Skill Pipeline Output
Generated: 2026-04-04 11:42 PM
Model: opus | Token Budget: 400K | Total Tokens: 287,432

---

## Stage 1: Technical Foundation
[full output text]

---

## Stage 2: Idea Capture
[full output text]

---

## Stage 3: Gap Analysis
[full output text]

... etc for all stages ...
```

### 3. Backend Architecture

#### 3.1 Pipeline Orchestrator (`server/services/pipeline_orchestrator.py`)

New service file. Core class: `SkillPipeline`.

```python
class SkillStage:
    """A single skill in the pipeline."""
    index: int              # 0-based position
    label: str              # Display name
    skill_text: str         # The full skill prompt (markdown)
    status: StageStatus     # pending / running / completed / failed
    output: str             # Collected output text
    tokens_used: int        # API-reported tokens for this stage
    duration_seconds: float # Wall clock time
    conversation_id: int    # Workspace conversation ID (for DB persistence)

class SkillPipeline:
    """Sequential prompt chain orchestrator."""
    
    pipeline_id: str
    stages: list[SkillStage]
    kickoff_message: str
    token_budget: int           # e.g. 400_000
    model: str                  # "opus" or "sonnet"
    status: PipelineStatus      # idle / running / completed / failed / stopped
    total_tokens_used: int
    working_directory: str
    
    async def run() -> AsyncGenerator[PipelineEvent]:
        """
        Sequential execution loop:
        1. For stage 0: send kickoff_message + skill_text as system context
        2. Collect full output text from the agent
        3. Check token budget — if exceeded, close session and start fresh
        4. For stage N+1: send skill_text + previous stage's output as context
        5. Repeat until all stages complete or error
        """
    
    async def stop():
        """Cancel the running pipeline."""
```

**Key execution logic:**

For each stage, the orchestrator:
1. Creates a `WorkspaceChatSession` with the configured model and context mode
2. Starts the session (creates SDK client, gets greeting)
3. Sends a message that includes:
   - The skill prompt text (as the primary instruction)
   - The previous stage's output (wrapped in `<previous_stage_output>` tags)
   - For stage 0 only: the user's kickoff message
4. Streams the response, collecting the full output text
5. Monitors `context_tokens` from the `token_usage` event — if it exceeds the budget, the orchestrator:
   - Saves a handoff summary of what's been accomplished
   - Closes the current session
   - Opens a fresh session for the same stage with the handoff context
6. When the agent finishes responding, stores the output and advances to the next stage
7. Emits `PipelineEvent` objects for real-time UI updates

**Message format sent to each stage's agent:**

```
[SKILL PIPELINE — Stage {N}: {label}]

You are executing stage {N} of a {total}-stage skill pipeline.

## Your Skill Instructions

{skill_text}

## Context From Previous Stage

<previous_stage_output stage="{N-1}" label="{prev_label}">
{previous_output}
</previous_stage_output>

## Rules
1. Follow the skill instructions above completely.
2. Your full response IS the output for this stage.
3. Do not ask clarifying questions — just execute the skill.
4. Be thorough — your output feeds directly into the next stage.
```

For stage 0, the previous output section is replaced with:
```
## User's Kickoff Message
{kickoff_message}
```

#### 3.2 Pipeline Events

Events emitted by the orchestrator and sent to the frontend via WebSocket:

| Event Type | Data | When |
|---|---|---|
| `pipeline_started` | `{pipeline_id, total_stages}` | Pipeline begins |
| `pipeline_stage_started` | `{stage_index, label}` | A stage begins running |
| `pipeline_stage_text` | `{stage_index, text}` | Streaming text from current stage |
| `pipeline_stage_completed` | `{stage_index, label, output, tokens_used, duration}` | A stage finishes |
| `pipeline_stage_failed` | `{stage_index, label, error}` | A stage errors out |
| `pipeline_token_usage` | `{total_tokens, budget, percent}` | Updated token count |
| `pipeline_budget_exceeded` | `{stage_index, tokens_used, budget}` | Token budget hit, spawning new session |
| `pipeline_completed` | `{pipeline_id, total_tokens, total_duration}` | All stages done |
| `pipeline_stopped` | `{pipeline_id}` | User stopped the pipeline |
| `pipeline_error` | `{error}` | Fatal error |

#### 3.3 Database Models

Add to `server/services/workspace_database.py`:

```python
class PipelineRun(Base):
    """A pipeline execution record."""
    __tablename__ = "pipeline_runs"
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)          # User-facing name
    status = Column(String, default="idle")        # idle/running/completed/failed/stopped
    model = Column(String, default="opus")
    token_budget = Column(Integer, default=400000)
    total_tokens = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)
    working_directory = Column(String, nullable=True)
    kickoff_message = Column(Text, nullable=True)
    stages_json = Column(Text)                     # JSON: [{label, skill_text}]
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

class PipelineStageOutput(Base):
    """Output from a single pipeline stage."""
    __tablename__ = "pipeline_stage_outputs"
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(String, index=True)       # FK to pipeline_runs.pipeline_id
    stage_index = Column(Integer)
    label = Column(String)
    output_text = Column(Text)
    tokens_used = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    status = Column(String, default="pending")
    error = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

#### 3.4 Router Endpoints

New file: `server/routers/pipeline.py` (prefix: `/api/pipeline`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/start` | Start a pipeline. Body: `{working_directory, kickoff_message, token_budget, model, stages: [{label, skill_text}]}` |
| `POST` | `/stop` | Stop the running pipeline |
| `GET` | `/status` | Get current pipeline status + all stage statuses |
| `GET` | `/status/{pipeline_id}` | Get specific pipeline status |
| `GET` | `/history` | List past pipeline runs |
| `GET` | `/export/{pipeline_id}` | Download combined outputs as single markdown file |
| `GET` | `/stage/{pipeline_id}/{stage_index}` | Get output for a specific stage |

Pipeline events are multiplexed onto the **existing** workspace WebSocket. The frontend sends:
```json
{"type": "pipeline_start", "kickoff_message": "...", "token_budget": 400000, "model": "opus", "stages": [...]}
{"type": "pipeline_stop"}
```

The backend sends pipeline events through the same WebSocket connection.

#### 3.5 Router Registration

Add to `server/main.py` alongside existing routers:
```python
from .routers import pipeline_router
app.include_router(pipeline_router)
```

Add to `server/routers/__init__.py`:
```python
from .pipeline import router as pipeline_router
```

### 4. Frontend Architecture

#### 4.1 New Files

| File | Purpose |
|---|---|
| `ui/src/components/workspace/PipelinePanel.tsx` | Main panel component (config + running modes) |
| `ui/src/components/workspace/PipelineSkillSlot.tsx` | Individual skill slot (upload, edit, collapse) |

#### 4.2 API Functions

Add to `ui/src/lib/api.ts`:

```typescript
// Pipeline types
export interface PipelineStageConfig {
  label: string
  skill_text: string
}

export interface PipelineStartRequest {
  working_directory: string
  kickoff_message: string
  token_budget: number
  model: string
  stages: PipelineStageConfig[]
}

export interface PipelineStageStatus {
  stage_index: number
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  output: string
  tokens_used: number
  duration_seconds: number
  error?: string
}

export interface PipelineStatus {
  pipeline_id: string
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped'
  total_tokens: number
  token_budget: number
  total_duration: number
  stages: PipelineStageStatus[]
}

// Pipeline API calls
export async function startPipeline(body: PipelineStartRequest): Promise<{pipeline_id: string}>
export async function stopPipeline(): Promise<void>
export async function getPipelineStatus(pipelineId: string): Promise<PipelineStatus>
export async function getPipelineHistory(): Promise<PipelineStatus[]>
export async function exportPipelineOutputs(pipelineId: string): Promise<Blob>
```

#### 4.3 WebSocket Integration

Extend `useWorkspaceChat.ts` to handle pipeline event types:
- `pipeline_started`, `pipeline_stage_started`, `pipeline_stage_text`, `pipeline_stage_completed`, `pipeline_token_usage`, `pipeline_completed`, etc.
- Expose pipeline state via new fields: `pipelineStatus`, `pipelineStages`, `pipelineTokens`

#### 4.4 WorkspacePage Integration

In `WorkspacePage.tsx`:
- Add `showPipeline` state (same pattern as `showSwarm` / `showFactory`)
- Add toggle button after the Factory button (~line 438)
- Render `<PipelinePanel>` conditionally when `showPipeline` is true
- Mutually exclusive with SwarmPanel (closing one opens the other, or both can coexist)

### 5. Token Budget Behavior

- Default: 400K tokens
- Toggle options: 200K, 400K, 450K (dropdown in config mode)
- The orchestrator monitors `context_tokens` from `ResultMessage` after each agent turn
- When `context_tokens` exceeds the budget:
  1. Let the current response finish
  2. Save the output collected so far
  3. Close the session
  4. Create a new session for the SAME stage with a condensed handoff
  5. Continue from where it left off
- The token bar in the UI shows: used / budget with percentage

### 6. Combined Export Format

When user clicks "Download All Outputs", the backend generates:

```markdown
# Skill Pipeline Output

**Generated:** {timestamp}
**Model:** {model}
**Token Budget:** {budget_formatted}
**Total Tokens Used:** {total_tokens_formatted}
**Total Duration:** {duration_formatted}
**Stages Completed:** {completed_count}/{total_count}

---

## Stage 0: {label}
**Tokens:** {tokens} | **Duration:** {duration}

{full_output_text}

---

## Stage 1: {label}
**Tokens:** {tokens} | **Duration:** {duration}

{full_output_text}

---

... (all stages) ...
```

### 7. Build Plan

#### Phase 1: Backend (estimated ~80K tokens)
1. Create `server/services/pipeline_orchestrator.py` — SkillPipeline class with sequential execution, token budget monitoring, event emission
2. Add DB models to `server/services/workspace_database.py` — PipelineRun, PipelineStageOutput tables
3. Create `server/routers/pipeline.py` — REST endpoints + WebSocket message handling
4. Register router in `server/main.py` and `server/routers/__init__.py`

#### Phase 2: Frontend (estimated ~70K tokens)
5. Add pipeline types + API functions to `ui/src/lib/api.ts`
6. Build `PipelineSkillSlot.tsx` — upload, edit, collapse/expand per skill
7. Build `PipelinePanel.tsx` — config mode + running mode + output viewer + export
8. Add pipeline event handling to `useWorkspaceChat.ts`
9. Add toggle button + panel mount in `WorkspacePage.tsx`

#### Phase 3: Integration + Polish (estimated ~20K tokens)
10. Wire WebSocket pipeline events end-to-end
11. Test with sample skill files
12. Verify export/download works

**Total estimated build:** ~170K tokens

### 8. Files Modified/Created

| Action | File |
|---|---|
| **CREATE** | `server/services/pipeline_orchestrator.py` |
| **CREATE** | `server/routers/pipeline.py` |
| **CREATE** | `ui/src/components/workspace/PipelinePanel.tsx` |
| **CREATE** | `ui/src/components/workspace/PipelineSkillSlot.tsx` |
| **MODIFY** | `server/services/workspace_database.py` (add 2 tables) |
| **MODIFY** | `server/main.py` (register router) |
| **MODIFY** | `server/routers/__init__.py` (export router) |
| **MODIFY** | `ui/src/lib/api.ts` (add types + functions) |
| **MODIFY** | `ui/src/hooks/useWorkspaceChat.ts` (pipeline events) |
| **MODIFY** | `ui/src/pages/WorkspacePage.tsx` (toggle button + panel) |

### 9. Dependencies

No new npm or pip packages needed. Everything builds on:
- `WorkspaceChatSession` (existing) — runs each skill as a chat session
- `workspace_database` (existing) — SQLite persistence
- `ws_send_and_flush` (existing) — WebSocket message delivery
- Lucide icons (existing) — `Workflow` or `ListOrdered` icon
- Tailwind CSS v4 (existing) — styling

### 10. Future Enhancements (v2)

- **Drag-and-drop reordering** of skills
- **Completion contract validation** — parse `## Contract` section from skill files, auto-check output
- **Interactive pause points** — skills that need user input trigger `agent_waiting` for question/answer
- **Pipeline templates** — save/load pipeline configurations (e.g. "PRD Maker 11-Stage")
- **Parallel skill groups** — some stages could run concurrently if they don't depend on each other
- **Pipeline history + comparison** — compare outputs from different runs
