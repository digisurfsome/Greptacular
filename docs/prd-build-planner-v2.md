# PRD: Build Planner v2 — Completion & Upgrade

> Agent OS 3-Layer Format: Standards | Product | Specs
>
> Split into 2 agents. Agent 1 = Phases 1-4 (fix + persistence + presets + auth).
> Agent 2 = Phases 5-8 (queue + dashboard + execution + log streaming).
> Each agent sized to stay under 50% context window.

---

## STANDARDS LAYER

### Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 19 + TypeScript (strict) | Existing setup in `ui/` |
| Styling | Tailwind CSS v4 | Neobrutalism design system from `ui/src/styles/globals.css` |
| Components | Radix UI primitives via `ui/src/components/ui/` | shadcn/ui Button, Input, Textarea, Select, Dialog, Tooltip, Tabs, Switch |
| Icons | Lucide React | All icons from this library only |
| Data Fetching | TanStack React Query | `useQuery`, `useMutation`, `useQueryClient` |
| Routing | Hash-based (`window.location.hash`) | Routes defined in `ui/src/main.tsx` |
| Backend | FastAPI (Python 3.11+) | Routers in `server/routers/`, services in `server/services/` |
| Database | SQLite via SQLAlchemy 2.0 | Declarative base pattern from `api/database.py` |
| AI Calls | Claude CLI subprocess (`claude -p --model sonnet`) | Subscription auth, NOT API key |
| WebSocket | FastAPI WebSocket | Pattern from `server/routers/design_guide.py` |
| Process Mgmt | `subprocess.Popen` / `asyncio.create_subprocess_exec` | Pattern from `server/services/factory_controller.py` |

### Code Conventions

**Frontend:**
- Named function exports (not default)
- One component per file
- Feature components in `ui/src/components/workspace/build-planner/`
- Page component in `ui/src/pages/BuildPlannerPage.tsx`
- All TypeScript interfaces in `ui/src/lib/types.ts`
- All API functions in `ui/src/lib/api.ts` using `fetchJSON<T>()`
- Custom hooks in `ui/src/hooks/useBuildPlanner.ts`
- Semantic Tailwind tokens (`bg-card`, `text-foreground`, `border-border`) not hardcoded colors
- No `alert()`, `confirm()`, `prompt()` -- use toast and Dialog components
- Loading states: skeleton cards for lists, spinner-in-button for actions
- Empty states: icon + message + CTA button

**Backend:**
- Router prefix: `/api/build-planner`
- Pydantic request/response models
- Lazy imports for services in routers
- SQLAlchemy sessions with `get_db_session()`, always close in `finally`
- Logging via `logging.getLogger(__name__)`

### Auth Model for AI Calls

The current backend (`server/routers/build_planner.py`) calls `anthropic.Anthropic(api_key=...)` directly. This burns API credits. It must be replaced with Claude CLI subprocess calls using subscription auth.

**Pattern to follow** (from `run_all_phases.sh`):
```bash
claude -p --model sonnet --dangerously-skip-permissions "prompt here"
```

**Python equivalent:**
```python
import subprocess
result = subprocess.run(
    ["claude", "-p", "--model", "sonnet", "--dangerously-skip-permissions", prompt],
    capture_output=True, text=True, timeout=300
)
output = result.stdout
```

This uses the owner's $200/month Max subscription -- zero additional cost per call.

### File Structure (Target State)

```
ui/src/
  pages/
    BuildPlannerPage.tsx              # Slim orchestrator, imports sub-components
  components/workspace/build-planner/
    ProjectBasicsSection.tsx           # App name, description, boilerplate, GitHub
    RuleBlocksSection.tsx              # Rule block stack with phase scoping
    RuleBlockItem.tsx                  # Single rule block with phase toggle
    FeaturesSection.tsx                # Feature list with S/M/L sizing
    BuildSettingsSection.tsx           # Model, turns, transitions, etc.
    PhaseAssignmentsSection.tsx        # Phase assignments textarea
    GenerateSection.tsx                # Generate buttons + output areas
    OutputArea.tsx                     # Reusable output display component
    SaveLoadPanel.tsx                  # Save/load/delete plans
    PresetManager.tsx                  # Build rule preset CRUD
    GenerateAllProgress.tsx            # Progress indicator for sequential generation
    QueuePanel.tsx                     # Build queue list (Agent 2)
    QueueItem.tsx                      # Single queue item (Agent 2)
    LiveDashboard.tsx                  # Running build dashboard (Agent 2)
    LogStream.tsx                      # WebSocket log output (Agent 2)
  hooks/
    useBuildPlanner.ts                 # React Query hooks for plans + presets
    useBuildQueue.ts                   # React Query hooks for queue (Agent 2)
    useBuildDashboard.ts              # WebSocket hook for live dashboard (Agent 2)
server/routers/
    build_planner.py                   # REST endpoints (rewritten)
server/services/
    build_planner_service.py           # Script generation + Claude CLI calls
    build_planner_db.py                # SQLAlchemy models + session management
    build_queue_service.py             # Queue management + execution (Agent 2)
```

### Database Location

Build planner data lives in `~/.autoforge/build_planner.db` (global, not per-project). This is because build plans are independent of AutoForge projects -- a plan creates a project, it does not belong to one.

---

## PRODUCT LAYER

### What It Is

Build Planner is a single-page tool inside AutoForge that turns project ideas into phased build scripts. The user fills out a form (app name, features, rules, settings), clicks "Generate All," and gets bash scripts that call Claude CLI to build the app in phases.

### What Exists Today (25-30% Complete)

The current implementation is a 1089-line monolithic React component (`BuildPlannerPage.tsx`) with a single backend endpoint that calls the Anthropic API directly (costs API credits). It works as an MVP but has these problems:

1. **Monolith** -- everything crammed into one file, no sub-components
2. **Wrong auth** -- uses `anthropic.Anthropic(api_key=...)` instead of subscription CLI
3. **No persistence** -- refresh the page and everything is lost
4. **No presets** -- rules must be retyped for every new plan
5. **No phase scoping** -- rules cannot be targeted to specific phases
6. **Manual 3-step generation** -- user must click 3 buttons in sequence and manually chain outputs
7. **Custom API pattern** -- uses hand-rolled `callGenerate()` instead of project's `fetchJSON` + React Query
8. **No queue** -- cannot prepare multiple builds
9. **No dashboard** -- cannot see what is running

### What the User Wants

**Fast prep:** Fill out the form in 2-3 minutes while another build is running. Save it. Come back later or add it to a queue.

**Reusable rules:** The owner collects build rules from YouTube mentors and their own experience. They update these rules regularly. They want to save a set of rules as a preset ("Web App Standard", "API-Only", "Mobile") and apply it to any new plan with one click.

**Phase-scoped rules:** Different rules apply at different build stages. "Set up the project structure" is Phase 1 only. "Follow existing patterns" is Phase 2+. "Always use TypeScript strict mode" is all phases. Each rule block needs a toggle for this.

**One-click generation:** Click "Generate All" and it runs PRD generation, then phase-split, then build scripts automatically. Show progress. Keep individual buttons for manual control.

**Queue + Dashboard (Agent 2):** Prepare 3-4 builds, add them to a queue, and let them run overnight. Watch progress on a NASA-style dashboard with log streaming.

### User Flow

```
Open Build Planner (/# /build-planner)
  |
  v
Fill form (project basics + rules + features + settings)
  |
  +-- Load saved plan? --> Select from list --> Form populated
  |
  +-- Load rule preset? --> Select preset --> Rule blocks populated
  |
  v
Click "Generate All"
  |
  v
[Step 1/3] PRD generated (progress bar shows step)
  |
  v
[Step 2/3] Phase-split generated (uses PRD output as input)
  |
  v
[Step 3/3] Build scripts generated (uses phase-split output as input)
  |
  v
Review outputs (collapsible panels for each step's result)
  |
  +-- Save Plan --> Stored in SQLite, can reload later
  |
  +-- Add to Queue --> Plan enters build queue (Agent 2)
  |
  +-- Copy scripts --> Manual use outside AutoForge
```

### Value Tiers

| Tier | Features | Status |
|------|----------|--------|
| Free | Google Sheet walkthrough (external) | Exists |
| Basic | Form + Generate All + Save/Load + Presets | Agent 1 builds this |
| Pro | Queue + Dashboard + Log Streaming + Execution | Agent 2 builds this |

---

## SPECS LAYER

### Phase 1: Break Up the Monolith + Fix Patterns

**Goal:** Split `BuildPlannerPage.tsx` from 1089 lines into proper sub-components. Replace custom API calls with project patterns. Zero behavior change -- same UI, same functionality, just properly organized.

**Why first:** Every subsequent phase adds to these files. Getting the structure right before adding features prevents a bigger mess later.

#### Task 1.1: Extract Types [ROBOT]

Move all TypeScript interfaces from `BuildPlannerPage.tsx` into `ui/src/lib/types.ts`.

Types to extract:
- `FeatureRow` (line 41-45)
- `Boilerplate` (line 51-57)
- New: `BuildPlannerFormState` -- all form state in one interface
- New: `GenerateStep` -- tracks progress of multi-step generation

Add to `types.ts`:
```typescript
// Build Planner Types
export interface BuildPlannerFeatureRow {
  id: number
  name: string
  size: 'S' | 'M' | 'L'
}

export interface BuildPlannerBoilerplate {
  id: string
  label: string
  tech: string
  templateOwner: string | null
  templateRepo: string | null
}

export interface BuildPlannerFormState {
  appName: string
  appDescription: string
  boilerplate: string
  ruleBlocks: RuleBlock[]
  features: BuildPlannerFeatureRow[]
  dependencies: string
  model: string
  turns: string
  transition: string
  errorHandling: string
  gitCommits: string
  phaseCount: string
  phaseAssignments: string
}

export interface RuleBlock {
  id: string
  label: string
  content: string
  phaseScope: 'all' | 'phase1' | 'phase2plus'
  collapsed: boolean
}

export interface GenerateStep {
  id: 'prd' | 'phase-split' | 'build-scripts'
  label: string
  status: 'pending' | 'running' | 'complete' | 'error'
  prompt: string
  result: string
  error: string | null
}
```

#### Task 1.2: Extract Constants [ROBOT]

Move constants from `BuildPlannerPage.tsx` into a new file `ui/src/components/workspace/build-planner/constants.ts`:
- `BOILERPLATES` array (lines 59-88)
- `MODELS` array (lines 90-94)
- `TURNS_OPTIONS`, `TRANSITION_OPTIONS`, `ERROR_OPTIONS`, `GIT_OPTIONS`, `PHASE_COUNT_OPTIONS` (lines 96-100)

#### Task 1.3: Extract Sub-Components [ROBOT]

Create these files in `ui/src/components/workspace/build-planner/`:

1. **`ProjectBasicsSection.tsx`** -- Lines 661-797. Props: form state + setters for appName, appDescription, boilerplate, GitHub fields. Contains the boilerplate selector, GitHub repo creation.

2. **`RuleBlocksSection.tsx`** -- Lines 799-897. Props: ruleBlocks state + handlers. Contains the rule block stack, add/remove buttons, combine-rules button.

3. **`FeaturesSection.tsx`** -- Lines 899-954. Props: features state + handlers, dependencies state. Contains feature list with S/M/L selectors.

4. **`BuildSettingsSection.tsx`** -- Lines 959-998. Props: model, turns, transition, errorHandling, gitCommits, phaseCount + setters.

5. **`PhaseAssignmentsSection.tsx`** -- Lines 1001-1012. Props: phaseAssignments + setter.

6. **`GenerateSection.tsx`** -- Lines 1014-1081. Props: generate handlers, output state. Contains the 3 generate buttons and output areas.

7. **`OutputArea.tsx`** -- Lines 253-341. The existing `OutputArea` inline component extracted to its own file with proper typing.

8. **`SectionCard.tsx`** -- Lines 140-158. Reusable card wrapper with icon + title.

9. **Reusable form components** (`TextInput.tsx`, `TextArea.tsx`, `SelectInput.tsx`) -- Lines 160-251. Extract or replace with shadcn/ui equivalents.

**Rule:** Each component gets its own file. Each file under 150 lines. `BuildPlannerPage.tsx` becomes a slim orchestrator that imports and renders sub-components, manages top-level state, and passes props down. Target: `BuildPlannerPage.tsx` drops to under 200 lines.

#### Task 1.4: Replace Custom API Call [ROBOT]

Remove the hand-rolled `callGenerate()` function (lines 110-122) and the hard-coded `API_BASE` (lines 106-108).

Replace with a proper function in `ui/src/lib/api.ts`:
```typescript
export async function buildPlannerGenerate(
  prompt: string,
  model: string
): Promise<{ result: string }> {
  return fetchJSON('/build-planner/generate', {
    method: 'POST',
    body: JSON.stringify({ prompt, model }),
  })
}
```

All generate calls in the component should use this function, ideally through React Query mutations in `useBuildPlanner.ts`.

#### Test Plan for Phase 1

```
[ROBOT] 1. npm run lint -- zero errors
[ROBOT] 2. npm run build -- compiles clean
[ROBOT] 3. Visual check: page renders identically to before the refactor
[ROBOT] 4. All 3 generate buttons still produce prompts
[ROBOT] 5. Copy button works on all output areas
[ROBOT] 6. GitHub repo creation flow still works
[ROBOT] 7. No console errors
[ROBOT] 8. BuildPlannerPage.tsx is under 200 lines
[ROBOT] 9. No file in components/workspace/build-planner/ exceeds 200 lines
```

---

### Phase 2: Subscription Auth + "Generate All" Button

**Goal:** Switch the backend from API-key-based Anthropic calls to Claude CLI subprocess calls (subscription auth). Add a single "Generate All" button that chains the 3 generation steps automatically.

#### Task 2.1: Rewrite Backend Generate Endpoint [ROBOT]

Replace the current `server/routers/build_planner.py` entirely:

```python
"""
Build Planner Router
====================
REST endpoints for the Build Planner page.
AI generation uses Claude CLI (subscription auth).
"""

import asyncio
import logging
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/build-planner", tags=["build-planner"])


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "sonnet"


class GenerateResponse(BaseModel):
    result: str


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Run a prompt through Claude CLI using subscription auth."""
    # Map full model names to CLI shortnames
    model_map = {
        "claude-sonnet-4-6-20250514": "sonnet",
        "claude-opus-4-6-20250514": "opus",
        "claude-haiku-4-5-20250414": "haiku",
    }
    model_name = model_map.get(request.model, request.model)

    try:
        # Run Claude CLI in print mode -- uses subscription, not API key
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p",
            "--model", model_name,
            "--dangerously-skip-permissions",
            request.prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=300
        )

        if proc.returncode != 0:
            error_msg = stderr.decode().strip() or "Claude CLI returned non-zero exit code"
            logger.error("Claude CLI error: %s", error_msg)
            raise HTTPException(status_code=502, detail=error_msg)

        return GenerateResponse(result=stdout.decode().strip())

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Claude CLI timed out after 300 seconds")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        )
    except Exception as e:
        logger.error("Build planner generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

Key changes:
- Removes `import anthropic` and `_get_api_key()` -- no more API key dependency
- Uses `asyncio.create_subprocess_exec` for non-blocking execution
- Maps full model IDs to CLI shortnames (`sonnet`, `opus`, `haiku`)
- 300-second timeout to handle long generations
- Uses `--dangerously-skip-permissions` to avoid interactive prompts

#### Task 2.2: Add "Generate All" Endpoint [AGENT]

New endpoint that chains 3 generations sequentially on the server side:

```python
class GenerateAllRequest(BaseModel):
    app_name: str
    app_description: str
    boilerplate_label: str
    boilerplate_tech: str
    rules_text: str
    feature_list_text: str
    dependencies: str
    model: str = "sonnet"
    phase_count: str = "3"
    turns: str = "25"
    transition: str = "Pause"
    error_handling: str = "Retry once then skip"
    git_commits: str = "After each feature"
    phase_assignments: str = ""


class GenerateAllResponse(BaseModel):
    prd_prompt: str
    prd_result: str
    phase_prompt: str
    phase_result: str
    build_prompt: str
    build_result: str


@router.post("/generate-all", response_model=GenerateAllResponse)
async def generate_all(request: GenerateAllRequest):
    """Run all 3 generation steps sequentially. Uses subscription auth."""
    # Step 1: Assemble and run PRD prompt
    # Step 2: Assemble phase-split prompt using PRD result
    # Step 3: Assemble build-scripts prompt using phase-split result
    # Return all prompts and results
```

This endpoint assembles the 3 prompts server-side (same logic currently in the frontend `generatePRD()`, `generatePhaseSplit()`, `generateBuildScripts()` functions) and runs them sequentially. The frontend calls this single endpoint and gets all results back.

#### Task 2.3: Add "Generate All" Button to UI [ROBOT]

Add a `GenerateAllProgress.tsx` component:

```
+-------------------------------------------------------+
| Generate All                                          |
|                                                       |
| [=====>        ] Step 1/3: Generating PRD...         |
|                                                       |
| [  ] PRD Prompt           [completed / pending]      |
| [  ] Phase-Split Prompt   [completed / pending]      |
| [  ] Build Scripts Prompt [completed / pending]      |
+-------------------------------------------------------+
```

Behavior:
- "Generate All" button sits above the 3 individual buttons
- Clicking it calls `POST /api/build-planner/generate-all`
- While running, shows a progress indicator with the current step
- On completion, populates all 3 output areas
- Individual buttons remain for manual control
- If "Generate All" fails at step 2, results from step 1 are still shown

#### Task 2.4: Server-Sent Events for Progress (Optional Upgrade) [ROBOT]

If the single POST endpoint feels too "black box" (user sees nothing for 2-3 minutes), upgrade to streaming:

Add a streaming endpoint:
```python
@router.post("/generate-all-stream")
async def generate_all_stream(request: GenerateAllRequest):
    """Stream progress updates for all 3 generation steps."""
    async def event_generator():
        # yield {"step": 1, "status": "running", "label": "Generating PRD..."}
        # ... run step 1 ...
        # yield {"step": 1, "status": "complete", "result": prd_result}
        # yield {"step": 2, "status": "running", "label": "Splitting into phases..."}
        # ... etc
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

The frontend uses `EventSource` or `fetch` with streaming to show real-time step progress.

**Recommendation:** Start with the simple POST endpoint. Only add streaming if user feedback says the wait is confusing.

#### Test Plan for Phase 2

```
[ROBOT] 1. npm run lint && npm run build -- both clean
[ROBOT] 2. ruff check server/routers/build_planner.py -- clean
[ROBOT] 3. Start backend, hit POST /api/build-planner/generate with a simple prompt
         -- returns result from Claude CLI, not API key
[ROBOT] 4. Verify no ANTHROPIC_API_KEY is read or required
[AGENT] 5. Click "Generate All" button in UI -- all 3 steps run and complete
[AGENT] 6. Verify step 2 uses step 1's output, step 3 uses step 2's output
[ROBOT] 7. Click individual "Generate PRD Prompt" button -- still works independently
[ROBOT] 8. Click "Run with AI" on an individual output -- uses subscription auth
[ROBOT] 9. Timeout test: send an absurdly long prompt, verify 504 after 300s
[ROBOT] 10. Error test: stop Claude CLI, verify clean error message
```

---

### Phase 3: Persistence (Save/Load Plans)

**Goal:** Users can save a plan, close the browser, come back, and load it. Plans are stored in SQLite.

#### Task 3.1: Database Models [ROBOT]

Create `server/services/build_planner_db.py`:

```python
"""
Build Planner Database Models
==============================
SQLAlchemy models for build plans and rule presets.
Database file: ~/.autoforge/build_planner.db
"""

from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import JSON


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class BuildPlan(Base):
    """A saved build plan with all form state."""
    __tablename__ = "build_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    # Complete form state serialized as JSON
    form_state = Column(JSON, nullable=False)
    # Generated outputs (nullable -- only present after generation)
    prd_prompt = Column(Text, nullable=True)
    prd_result = Column(Text, nullable=True)
    phase_prompt = Column(Text, nullable=True)
    phase_result = Column(Text, nullable=True)
    build_prompt = Column(Text, nullable=True)
    build_result = Column(Text, nullable=True)
    # Queue position (null = not queued)
    queue_position = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)


class RulePreset(Base):
    """A reusable set of rule blocks."""
    __tablename__ = "rule_presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    # Array of RuleBlock objects as JSON
    rule_blocks = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)


# --- Engine & Session Management ---

_engine = None
_SessionLocal = None

def _get_db_path() -> Path:
    db_dir = Path.home() / ".autoforge"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "build_planner.db"

def get_engine():
    global _engine
    if _engine is None:
        db_path = _get_db_path()
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(_engine)
    return _engine

def get_db_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()
```

**Status values for `BuildPlan.status`:**
- `draft` -- saved but not fully generated
- `ready` -- generation complete, outputs present
- `queued` -- in the build queue (Agent 2)
- `running` -- currently executing (Agent 2)
- `complete` -- build finished (Agent 2)
- `failed` -- build failed (Agent 2)

#### Task 3.2: CRUD Endpoints [ROBOT]

Add to `server/routers/build_planner.py`:

```
GET    /api/build-planner/plans          -- List all plans (id, name, status, updated_at)
POST   /api/build-planner/plans          -- Create plan (form_state JSON)
GET    /api/build-planner/plans/{id}     -- Get full plan by ID
PUT    /api/build-planner/plans/{id}     -- Update plan (partial update)
DELETE /api/build-planner/plans/{id}     -- Delete plan
```

Pydantic models:
```python
class PlanSummary(BaseModel):
    id: int
    name: str
    status: str
    updated_at: str  # ISO format

class PlanCreate(BaseModel):
    name: str
    form_state: dict

class PlanUpdate(BaseModel):
    name: str | None = None
    form_state: dict | None = None
    status: str | None = None
    prd_prompt: str | None = None
    prd_result: str | None = None
    phase_prompt: str | None = None
    phase_result: str | None = None
    build_prompt: str | None = None
    build_result: str | None = None

class PlanDetail(BaseModel):
    id: int
    name: str
    status: str
    form_state: dict
    prd_prompt: str | None
    prd_result: str | None
    phase_prompt: str | None
    phase_result: str | None
    build_prompt: str | None
    build_result: str | None
    queue_position: int | None
    created_at: str
    updated_at: str
```

#### Task 3.3: React Query Hooks [ROBOT]

Create `ui/src/hooks/useBuildPlanner.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useBuildPlans() {
  return useQuery({
    queryKey: ['build-planner', 'plans'],
    queryFn: () => fetchJSON<PlanSummary[]>('/build-planner/plans'),
  })
}

export function useBuildPlan(id: number | null) {
  return useQuery({
    queryKey: ['build-planner', 'plans', id],
    queryFn: () => fetchJSON<PlanDetail>(`/build-planner/plans/${id}`),
    enabled: id !== null,
  })
}

export function useCreatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PlanCreate) =>
      fetchJSON<PlanDetail>('/build-planner/plans', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['build-planner', 'plans'] }),
  })
}

export function useUpdatePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: PlanUpdate & { id: number }) =>
      fetchJSON<PlanDetail>(`/build-planner/plans/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['build-planner', 'plans'] }),
  })
}

export function useDeletePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      fetchJSON(`/build-planner/plans/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['build-planner', 'plans'] }),
  })
}

export function useGenerateAll() {
  return useMutation({
    mutationFn: (data: GenerateAllRequest) =>
      fetchJSON<GenerateAllResponse>('/build-planner/generate-all', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}
```

#### Task 3.4: Save/Load UI Panel [ROBOT]

Create `SaveLoadPanel.tsx`:

Layout:
```
+--------------------------------------------+
| Saved Plans                        [+ New] |
|--------------------------------------------|
| My SaaS App          draft    2 min ago  X |
| Landing Page         ready    1 hr ago   X |
| Mobile App v2        draft    3 days ago X |
+--------------------------------------------+
```

Behavior:
- Sits above or beside the form (collapsible panel)
- Lists all saved plans with name, status badge, relative timestamp
- Click a plan name to load it into the form
- Delete button with confirmation dialog
- "New Plan" button clears the form
- "Save" button in the page header saves current form state
- Auto-save not implemented yet (keep it explicit)

#### Test Plan for Phase 3

```
[ROBOT] 1. npm run lint && npm run build -- both clean
[ROBOT] 2. ruff check server/ -- clean
[ROBOT] 3. Create a plan via POST /api/build-planner/plans -- returns plan with ID
[ROBOT] 4. List plans via GET /api/build-planner/plans -- shows the new plan
[ROBOT] 5. Get plan via GET /api/build-planner/plans/{id} -- returns full detail
[ROBOT] 6. Update plan via PUT /api/build-planner/plans/{id} -- name changes
[ROBOT] 7. Delete plan via DELETE /api/build-planner/plans/{id} -- plan gone
[ROBOT] 8. In UI: fill form, click Save, refresh page, click plan name -- form repopulated
[ROBOT] 9. In UI: delete a plan -- confirm dialog appears, plan removed from list
[ROBOT] 10. Empty state: no plans saved -- shows icon + "No saved plans" + CTA
[ROBOT] 11. Database file exists at ~/.autoforge/build_planner.db
```

---

### Phase 4: Rule Presets + Phase-Scoped Rules

**Goal:** Users can save rule block sets as named presets, load presets into plans, and assign each rule block to a phase scope (All Phases / Phase 1 Only / Phase 2+).

#### Task 4.1: Phase Scope Toggle on Rule Blocks [ROBOT]

Upgrade `RuleBlockItem.tsx` to add a phase scope selector:

```
+------------------------------------------------------+
| [All Phases v]  Tech Stack Rules              [^ v X] |
|------------------------------------------------------|
| Use TypeScript strict mode for all files.            |
| Use Tailwind CSS v4 for styling.                     |
| No inline styles.                                    |
+------------------------------------------------------+
```

Each rule block gets:
- **Phase scope dropdown** at top-left: "All Phases" | "Phase 1 Only" | "Phase 2+"
- **Label field** -- short name for the block (editable inline)
- **Content area** -- the actual rules text (auto-expanding)
- **Collapse toggle** -- minimize to just show label + scope badge
- **Delete button** -- removes block (with confirmation)
- **Drag handle** -- left side, for reordering (optional in Phase 4, can defer to later)

The `RuleBlock` type already has `phaseScope` and `label` fields (defined in Phase 1 types).

Phase scope affects prompt generation:
- `all` -- this block is included in every phase script
- `phase1` -- this block is included ONLY in the Phase 1 script
- `phase2plus` -- this block is included in Phase 2 and all subsequent phases

Update the `getRulesText()` helper (or its equivalent in `GenerateSection.tsx`) to accept a phase number parameter and filter rule blocks by scope.

#### Task 4.2: Preset CRUD Endpoints [ROBOT]

Add to `server/routers/build_planner.py`:

```
GET    /api/build-planner/presets          -- List all presets
POST   /api/build-planner/presets          -- Create preset
GET    /api/build-planner/presets/{id}     -- Get preset by ID
PUT    /api/build-planner/presets/{id}     -- Update preset
DELETE /api/build-planner/presets/{id}     -- Delete preset
```

Pydantic models:
```python
class PresetSummary(BaseModel):
    id: int
    name: str
    description: str | None
    block_count: int
    updated_at: str

class PresetCreate(BaseModel):
    name: str
    description: str | None = None
    rule_blocks: list[dict]  # Array of {label, content, phaseScope}

class PresetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rule_blocks: list[dict] | None = None

class PresetDetail(BaseModel):
    id: int
    name: str
    description: str | None
    rule_blocks: list[dict]
    created_at: str
    updated_at: str
```

#### Task 4.3: React Query Hooks for Presets [ROBOT]

Add to `ui/src/hooks/useBuildPlanner.ts`:

```typescript
export function useRulePresets() {
  return useQuery({
    queryKey: ['build-planner', 'presets'],
    queryFn: () => fetchJSON<PresetSummary[]>('/build-planner/presets'),
  })
}

export function useCreatePreset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PresetCreate) =>
      fetchJSON<PresetDetail>('/build-planner/presets', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['build-planner', 'presets'] }),
  })
}

// ... useUpdatePreset, useDeletePreset following same pattern
```

#### Task 4.4: Preset Manager UI [ROBOT]

Create `PresetManager.tsx`:

Layout:
```
+--------------------------------------------+
| Rule Presets                               |
|--------------------------------------------|
| [Load Preset v]  [Save Current as Preset]  |
|--------------------------------------------|
| Web App Standard    5 blocks   Edit | Del  |
| API-Only            3 blocks   Edit | Del  |
| Mobile First        4 blocks   Edit | Del  |
+--------------------------------------------+
```

Behavior:
- "Load Preset" dropdown lists all saved presets
- Selecting a preset replaces the current rule blocks with the preset's blocks
- "Save Current as Preset" opens a dialog asking for preset name + optional description
- Saves the current rule blocks (with labels, content, and phase scopes) as a new preset
- Edit button opens inline editing of the preset (name, description)
- Delete button with confirmation
- Sits inside or adjacent to the Rule Blocks section

#### Task 4.5: Update Prompt Generation for Phase Scoping [ROBOT]

When generating prompts (especially the build scripts prompt), the system must filter rule blocks by phase:

```typescript
function getRulesForPhase(ruleBlocks: RuleBlock[], phaseNumber: number): string {
  return ruleBlocks
    .filter(block => {
      if (block.phaseScope === 'all') return true
      if (block.phaseScope === 'phase1' && phaseNumber === 1) return true
      if (block.phaseScope === 'phase2plus' && phaseNumber >= 2) return true
      return false
    })
    .map(block => {
      const header = block.label ? `## ${block.label}` : ''
      return header ? `${header}\n${block.content}` : block.content
    })
    .join('\n\n')
}
```

This function is used by the build-scripts generation prompt to create per-phase rule injection. The PRD prompt and phase-split prompt use ALL rules (since they run once, not per-phase).

#### Task 4.6: Default Starter Blocks [ROBOT]

When the user clicks "New Plan" or opens Build Planner for the first time with no loaded plan, pre-populate 3 starter rule blocks:

1. **"Tech Stack"** -- scope: All Phases, content: empty, placeholder: "e.g., Use TypeScript strict mode. Use Tailwind CSS v4. No inline styles..."
2. **"Project Setup"** -- scope: Phase 1 Only, content: empty, placeholder: "e.g., Create project structure, install dependencies, set up routing..."
3. **"Coding Standards"** -- scope: Phase 2+, content: empty, placeholder: "e.g., Follow existing patterns. Read all code before modifying. Import from existing files..."

#### Test Plan for Phase 4

```
[ROBOT] 1. npm run lint && npm run build -- both clean
[ROBOT] 2. ruff check server/ -- clean
[ROBOT] 3. Each rule block shows phase scope dropdown with 3 options
[ROBOT] 4. Changing phase scope persists when saving the plan
[ROBOT] 5. Phase scope dropdown visually indicates current selection
[ROBOT] 6. Create a preset via POST /api/build-planner/presets -- success
[ROBOT] 7. List presets via GET /api/build-planner/presets -- shows preset
[ROBOT] 8. In UI: save current rules as preset, then load it into a new plan -- blocks match
[ROBOT] 9. In UI: delete a preset -- confirmation dialog, preset removed
[ROBOT] 10. New plan starts with 3 starter blocks with correct phase scopes
[ROBOT] 11. Generate PRD prompt -- includes ALL rule blocks regardless of scope
[ROBOT] 12. Generate build scripts prompt -- rules are filtered by phase scope
[ROBOT] 13. Collapsed rule block shows label + scope badge, not full content
```

---

### Phase 5: Build Queue (Agent 2 Starts Here)

**Goal:** Users can add completed plans to a build queue. The queue is an ordered list of plans waiting to execute.

#### Task 5.1: Queue Data Model [ROBOT]

The `BuildPlan` model already has a `queue_position` column (nullable integer). Plans with a non-null `queue_position` are in the queue. Queue position determines execution order (lower = sooner).

No new database model needed. Add a queue service in `server/services/build_queue_service.py`:

```python
"""
Build Queue Service
====================
Manages the ordered queue of build plans waiting for execution.
"""

def add_to_queue(plan_id: int) -> int:
    """Add a plan to the end of the queue. Returns the queue position."""
    # Set plan.status = 'queued'
    # Set plan.queue_position = max(existing positions) + 1
    # Return the position

def remove_from_queue(plan_id: int) -> None:
    """Remove a plan from the queue. Recompacts positions."""
    # Set plan.queue_position = None
    # Set plan.status = 'ready' (if it was 'queued')
    # Recompact remaining positions to fill gaps

def reorder_queue(plan_ids: list[int]) -> None:
    """Set queue order from an ordered list of plan IDs."""
    # Validate all IDs are currently queued
    # Assign positions 1, 2, 3, ... in the given order

def get_queue() -> list[BuildPlan]:
    """Get all queued plans ordered by queue_position."""
    # SELECT * FROM build_plans WHERE queue_position IS NOT NULL
    # ORDER BY queue_position ASC

def get_next() -> BuildPlan | None:
    """Get the next plan to execute (lowest queue_position)."""

def mark_running(plan_id: int) -> None:
    """Mark a plan as currently running."""
    # Set plan.status = 'running'

def mark_complete(plan_id: int) -> None:
    """Mark a plan as completed. Removes from queue."""
    # Set plan.status = 'complete'
    # Set plan.queue_position = None

def mark_failed(plan_id: int, error: str) -> None:
    """Mark a plan as failed. Removes from queue."""
    # Set plan.status = 'failed'
    # Set plan.queue_position = None
```

#### Task 5.2: Queue API Endpoints [ROBOT]

Add to `server/routers/build_planner.py`:

```
GET    /api/build-planner/queue              -- Get ordered queue
POST   /api/build-planner/queue/{plan_id}    -- Add plan to queue
DELETE /api/build-planner/queue/{plan_id}    -- Remove plan from queue
PUT    /api/build-planner/queue/reorder      -- Reorder queue (body: {plan_ids: [3, 1, 5]})
POST   /api/build-planner/queue/run-next     -- Start executing the next queued plan
POST   /api/build-planner/queue/run-all      -- Start executing all queued plans sequentially
```

#### Task 5.3: Queue UI Panel [ROBOT]

Create `QueuePanel.tsx`:

```
+------------------------------------------------------+
| Build Queue (3 builds)            [Run Next] [Run All]|
|------------------------------------------------------|
| 1. My SaaS App     3 phases  ready         [^ v  X] |
| 2. Landing Page     2 phases  ready         [^ v  X] |
| 3. Mobile App       4 phases  generating... [^ v  X] |
+------------------------------------------------------+
```

Behavior:
- Shows all queued plans in order
- Drag handles (or up/down arrows) for reordering
- Delete (X) button removes from queue (not from saved plans)
- Status badge per item: ready / generating / running
- "Run Next" starts the first queued plan
- "Run All" starts sequential execution of all queued plans
- When a plan is running, its row gets a pulsing border animation
- Queue panel is a collapsible section on the Build Planner page

Create `QueueItem.tsx` for each row.

#### Task 5.4: React Query Hooks for Queue [ROBOT]

Create `ui/src/hooks/useBuildQueue.ts`:

```typescript
export function useBuildQueue() {
  return useQuery({
    queryKey: ['build-planner', 'queue'],
    queryFn: () => fetchJSON<QueuedPlan[]>('/build-planner/queue'),
    refetchInterval: 5000, // Poll every 5s while queue is active
  })
}

export function useAddToQueue() { /* ... */ }
export function useRemoveFromQueue() { /* ... */ }
export function useReorderQueue() { /* ... */ }
export function useRunNext() { /* ... */ }
export function useRunAll() { /* ... */ }
```

#### Task 5.5: "Add to Queue" Button on Form [ROBOT]

Add an "Add to Queue" button next to the existing "Save" button in the page header.

Behavior:
1. Validates that the plan has been generated (all 3 outputs present)
2. If not generated, shows toast: "Generate scripts first before queuing"
3. If generated, saves the plan (if unsaved) and adds it to the queue
4. Shows toast: "Added to queue (position #N)"
5. Queue panel auto-expands to show the new item

#### Test Plan for Phase 5

```
[ROBOT] 1. npm run lint && npm run build -- both clean
[ROBOT] 2. ruff check server/ -- clean
[ROBOT] 3. POST /api/build-planner/queue/{id} -- plan added to queue
[ROBOT] 4. GET /api/build-planner/queue -- returns ordered list
[ROBOT] 5. DELETE /api/build-planner/queue/{id} -- plan removed, positions recompacted
[ROBOT] 6. PUT /api/build-planner/queue/reorder with [3,1,2] -- order changes
[ROBOT] 7. In UI: click "Add to Queue" -- plan appears in queue panel
[ROBOT] 8. In UI: reorder items -- order persists after refresh
[ROBOT] 9. In UI: remove item from queue -- item gone, others reorder
[ROBOT] 10. Empty queue shows "No builds queued" with CTA
[ROBOT] 11. Cannot add an ungenerated plan to queue -- error toast
```

---

### Phase 6: Build Execution Engine

**Goal:** When the user clicks "Run Next" or "Run All," the system actually executes the build by running the generated bash scripts via subprocess.

#### Task 6.1: Script Writer Service [ROBOT]

Create logic in `server/services/build_planner_service.py` to write generated scripts to disk:

```python
def write_build_scripts(plan: BuildPlan, output_dir: Path) -> list[Path]:
    """Write the generated bash scripts to disk as real .sh files.

    Takes the build_result from the plan (which contains the generated
    script content) and writes individual phase scripts + run_all.sh.

    Returns list of script file paths created.
    """
    # Parse the build_result to extract individual phase scripts
    # Write each to output_dir/phase1.sh, phase2.sh, etc.
    # Write output_dir/run_all.sh master script
    # chmod +x all scripts
    # Return list of paths
```

Scripts are written to a build-specific directory:
```
~/.autoforge/builds/{plan_id}_{timestamp}/
  phase1.sh
  phase2.sh
  phase3.sh
  run_all.sh
  build.log
```

#### Task 6.2: Build Executor [ROBOT + AGENT]

Add execution logic to `server/services/build_queue_service.py`:

```python
class BuildExecutor:
    """Runs a build plan by executing its generated scripts."""

    def __init__(self, plan: BuildPlan, broadcast: Callable):
        self.plan = plan
        self.broadcast = broadcast  # WebSocket broadcast function
        self.process: subprocess.Popen | None = None
        self.build_dir: Path | None = None
        self.cancelled = False

    async def execute(self) -> None:
        """Run the build plan's scripts sequentially."""
        # 1. Write scripts to disk
        # 2. Mark plan as running
        # 3. For each phase script:
        #    a. Broadcast: {"type": "phase_start", "phase": N, "total": M}
        #    b. Run: subprocess.Popen(["bash", script_path], ...)
        #    c. Stream stdout/stderr line-by-line via broadcast
        #    d. On completion: broadcast phase_complete
        # 4. On all complete: mark plan as complete
        # 5. On error: mark plan as failed

    def cancel(self) -> None:
        """Cancel the running build."""
        self.cancelled = True
        if self.process:
            self.process.terminate()
```

The executor pattern follows `factory_controller.py`:
- Subprocess for each phase script
- Line-by-line stdout streaming
- Error handling with status updates
- Cancellation support

#### Task 6.3: Build Run Endpoints [ROBOT]

```
POST   /api/build-planner/queue/run-next       -- Start next queued build
POST   /api/build-planner/queue/run-all        -- Start all queued builds
POST   /api/build-planner/builds/{id}/cancel   -- Cancel a running build
GET    /api/build-planner/builds/{id}/status    -- Get build status
GET    /api/build-planner/builds/active        -- Get currently running build (if any)
```

#### Test Plan for Phase 6

```
[ROBOT] 1. ruff check server/ -- clean
[ROBOT] 2. Write scripts for a simple 2-phase plan -- files exist on disk
[ROBOT] 3. Scripts have correct content (phase-specific rules, correct model flags)
[ROBOT] 4. Scripts have executable permission
[ROBOT] 5. POST /api/build-planner/queue/run-next -- plan status changes to 'running'
[ROBOT] 6. POST /api/build-planner/builds/{id}/cancel -- process terminated, status 'failed'
[ROBOT] 7. GET /api/build-planner/builds/active -- returns running build or null
[ROBOT] 8. Build directory created at ~/.autoforge/builds/{plan_id}_{timestamp}/
[ROBOT] 9. build.log file captures all output
[AGENT] 10. End-to-end: queue a plan, run it, scripts execute, plan marked complete
```

---

### Phase 7: Live Dashboard

**Goal:** When a build is running, show real-time progress: current phase, elapsed time, overall progress, log output.

#### Task 7.1: WebSocket Endpoint [ROBOT]

Add to `server/routers/build_planner.py`:

```python
@router.websocket("/ws/builds/{plan_id}")
async def build_websocket(websocket: WebSocket, plan_id: int):
    """WebSocket for real-time build updates.

    Server -> Client messages:
    - {"type": "phase_start", "phase": 1, "total": 3, "label": "Project Setup"}
    - {"type": "phase_complete", "phase": 1, "duration_seconds": 120}
    - {"type": "log", "line": "...", "phase": 1, "timestamp": "..."}
    - {"type": "progress", "phase": 1, "total": 3, "elapsed_seconds": 45}
    - {"type": "complete", "total_duration_seconds": 360}
    - {"type": "error", "phase": 2, "message": "Claude CLI exited with code 1"}
    - {"type": "cancelled"}
    """
    await websocket.accept()
    # Register this websocket for broadcasts from BuildExecutor
    # Keep alive until build completes or client disconnects
```

Follow the pattern from `server/routers/design_guide.py`:
- Accept WebSocket immediately
- Loop receiving messages (for keep-alive pings)
- Register for broadcast events from the executor
- Clean up on disconnect

#### Task 7.2: Dashboard UI [ROBOT]

Create `LiveDashboard.tsx`:

```
+----------------------------------------------------------------------+
| LIVE BUILD: My SaaS App                                    [Cancel] |
|----------------------------------------------------------------------|
|                                                                      |
| Phase 2 of 3 — Feature Building                                     |
| [=========>                    ] 45%                                 |
|                                                                      |
| +--------+  +--------+  +--------+                                  |
| | Ph 1   |  | Ph 2   |  | Ph 3   |                                  |
| | 2m 15s |  | 1m 30s |  | --:--  |                                  |
| | done   |  | active |  | next   |                                  |
| +--------+  +--------+  +--------+                                  |
|                                                                      |
| Elapsed: 3m 45s    Est. remaining: ~4m                              |
|----------------------------------------------------------------------|
| LOG OUTPUT                                                   [Copy] |
|----------------------------------------------------------------------|
| [14:32:01] Starting Phase 2...                                      |
| [14:32:05] Reading existing code...                                 |
| [14:32:12] Creating Dashboard component...                          |
| [14:33:01] Running lint check...                                    |
| > (auto-scrolling, newest at bottom)                                |
+----------------------------------------------------------------------+
```

Components:
- **Phase progress bar** -- overall percentage based on phases completed
- **Phase cards** -- small cards showing each phase's status and duration
- **Timer** -- elapsed time, live-updating every second
- **Estimated remaining** -- based on average phase duration so far
- **Log output area** -- scrollable, auto-scrolling, monospace font
- **Cancel button** -- stops the build with confirmation dialog
- **Copy log button** -- copies full log to clipboard

#### Task 7.3: Dashboard WebSocket Hook [ROBOT]

Create `ui/src/hooks/useBuildDashboard.ts`:

```typescript
import { useState, useEffect, useRef, useCallback } from 'react'

interface BuildDashboardState {
  isConnected: boolean
  currentPhase: number
  totalPhases: number
  phaseLabel: string
  phases: PhaseStatus[]
  logs: LogEntry[]
  elapsedSeconds: number
  status: 'idle' | 'running' | 'complete' | 'error' | 'cancelled'
  error: string | null
}

interface PhaseStatus {
  phase: number
  status: 'pending' | 'running' | 'complete' | 'error'
  durationSeconds: number | null
}

interface LogEntry {
  line: string
  phase: number
  timestamp: string
}

export function useBuildDashboard(planId: number | null): BuildDashboardState {
  // Connect to /ws/builds/{planId}
  // Parse incoming messages and update state
  // Auto-reconnect on disconnect
  // Return reactive state
}
```

#### Task 7.4: Log Stream Component [ROBOT]

Create `LogStream.tsx`:

```typescript
// Auto-scrolling log output with:
// - Monospace font
// - Phase-colored left border per log line
// - Timestamp prefix
// - Auto-scroll to bottom (with "scroll lock" when user scrolls up)
// - Max 5000 lines in memory (older lines dropped)
// - Copy full log button
// - Search/filter input (optional, nice-to-have)
```

#### Task 7.5: Page Layout Integration [ROBOT]

The Build Planner page needs a layout that accommodates both the form and the dashboard. Two approaches:

**Option A (Recommended): Conditional display**
- When no build is running: full-width form
- When a build is running: form collapses, dashboard expands
- Toggle button to switch between form and dashboard

**Option B: Split view**
- Left panel: queue list (narrow)
- Right panel: dashboard OR form (wide)

Go with Option A for simplicity. The dashboard replaces the main content area when a build is active.

#### Test Plan for Phase 7

```
[ROBOT] 1. npm run lint && npm run build -- both clean
[ROBOT] 2. WebSocket endpoint accepts connections at /ws/builds/{plan_id}
[ROBOT] 3. WebSocket sends phase_start, log, phase_complete, complete messages
[ROBOT] 4. Dashboard shows when build is running
[ROBOT] 5. Phase progress bar updates in real-time
[ROBOT] 6. Phase cards show correct status (done/active/next)
[ROBOT] 7. Log output auto-scrolls to bottom
[ROBOT] 8. Scrolling up pauses auto-scroll, scrolling to bottom resumes
[ROBOT] 9. Cancel button terminates the build
[ROBOT] 10. Timer counts up in real-time
[ROBOT] 11. Copy log button copies full log to clipboard
[ROBOT] 12. Dashboard hides when build completes, form returns
[ROBOT] 13. Disconnecting and reconnecting WebSocket recovers state
```

---

### Phase 8: Polish + Integration Testing

**Goal:** End-to-end testing, edge cases, UI polish, and documentation.

#### Task 8.1: End-to-End Flow Test [AGENT]

Test the complete flow:
1. Open Build Planner
2. Fill in project basics
3. Add 3 rule blocks with different phase scopes
4. Add 5 features
5. Configure build settings
6. Click "Generate All" -- all 3 steps complete
7. Save the plan
8. Add to queue
9. Click "Run Next"
10. Watch dashboard show progress
11. Build completes
12. Close browser, reopen, load saved plan -- all data intact

#### Task 8.2: Error Handling Polish [ROBOT]

Ensure all error paths show user-friendly messages:
- Claude CLI not installed
- Claude CLI rate-limited
- Network disconnection during WebSocket
- Plan not found (deleted by another tab)
- Queue empty when clicking "Run Next"
- Build script has syntax error
- Disk full when writing scripts

#### Task 8.3: UI Polish [ROBOT]

- Loading skeletons for plan list and queue
- Empty states for: no plans, no presets, empty queue, no build running
- Toast notifications for: save success, delete success, queue add, build complete, build error
- Keyboard shortcuts: Ctrl+S to save plan, Escape to close panels
- Responsive layout: form sections stack on narrow screens

#### Task 8.4: Register Router in Main App [ROBOT]

Ensure `build_planner` router is registered in:
- `server/routers/__init__.py` (if it has a registry pattern)
- `server/main.py` or wherever routers are mounted

Also verify the hash route in `ui/src/main.tsx` for `#/build-planner` exists and points to `BuildPlannerPage`.

#### Test Plan for Phase 8

```
[AGENT] 1. Full end-to-end flow from form fill to build execution
[ROBOT] 2. All error paths show toast messages, not raw errors
[ROBOT] 3. Empty states render correctly for all panels
[ROBOT] 4. Loading skeletons appear during data fetching
[ROBOT] 5. Ctrl+S saves the plan (keyboard shortcut)
[ROBOT] 6. npm run lint && npm run build -- zero warnings
[ROBOT] 7. ruff check server/ -- clean
[ROBOT] 8. No console.log statements left in production code
[ROBOT] 9. All TODO comments resolved or tracked in backlog
[ROBOT] 10. Page renders on mobile viewport (stacked, not broken)
```

---

## AGENT ASSIGNMENT SUMMARY

### Agent 1: Phases 1-4 (Fix + Persistence + Presets + Auth)

| Phase | What | Estimated Complexity |
|-------|------|---------------------|
| 1 | Break up monolith, extract 9+ components, fix patterns | 4/10 -- mechanical refactoring |
| 2 | Rewrite backend auth (CLI subprocess), add "Generate All" | 5/10 -- new endpoint + async subprocess |
| 3 | SQLite persistence, CRUD endpoints, save/load UI | 5/10 -- standard CRUD pattern |
| 4 | Phase-scoped rules, rule presets, preset CRUD | 4/10 -- UI + CRUD |

**Context budget:** Phases 1-4 involve ~15 files (9 new components, 2 backend files, 2 hooks, types, api). Each file is 80-200 lines. Total new code: ~2000 lines. Well within 50% context window.

**Critical path:** Phase 1 must be done first (structure). Phases 2-4 can technically be done in any order but 2 before 3 is recommended (auth fix before persistence to avoid saving API-key-based outputs).

### Agent 2: Phases 5-8 (Queue + Dashboard + Execution + Polish)

| Phase | What | Estimated Complexity |
|-------|------|---------------------|
| 5 | Build queue data model, API, UI panel | 4/10 -- standard CRUD + ordering |
| 6 | Build execution engine (subprocess, script writer) | 6/10 -- process management |
| 7 | Live dashboard with WebSocket log streaming | 6/10 -- real-time UI |
| 8 | Polish, error handling, end-to-end testing | 3/10 -- cleanup |

**Context budget:** Phases 5-8 involve ~10 files (4 new components, 2 services, 1 hook, endpoint additions). Total new code: ~1800 lines. Well within 50% context window.

**Critical path:** Phase 5 before 6 (queue before execution). Phase 6 before 7 (execution before dashboard). Phase 8 last (polish after everything works).

---

## APPENDIX: What NOT to Build

These are explicitly out of scope for this PRD. They belong in the feature backlog:

1. **Dependency graph visualization** -- Separate PRD already exists
2. **AI feature generator** -- "describe app, get features" -- future
3. **Cost estimator** -- token/cost prediction -- future
4. **Multi-model per phase** -- Haiku for setup, Opus for complex -- future
5. **Drag-and-drop rule reordering** -- Nice-to-have, not critical for v2
6. **Template library** -- Community-shared templates -- future SaaS feature
7. **Collaborative planning** -- Multi-user editing -- future SaaS feature
8. **CI/CD generation** -- GitHub Actions, Netlify config -- future
9. **Style Set picker** -- Design system integration -- separate feature
10. **One-click "Start Build"** -- Create AutoForge project from plan -- Phase 3 of a future PRD

---

## APPENDIX: Existing Code to Preserve

The following functionality from the current `BuildPlannerPage.tsx` must survive the refactor:

1. **Boilerplate selector** with 4 options (Web/Mobile/Full Stack/Scratch)
2. **GitHub repo creation** (token validation, repo creation, template support)
3. **Rule blocks** with add/remove/combine functionality
4. **Feature list** with S/M/L sizing
5. **Build settings** (model, turns, transitions, error handling, git, phase count)
6. **Phase assignments** textarea
7. **3 generate buttons** (PRD, Phase-Split, Build Scripts)
8. **"Run with AI" button** on each output
9. **Copy to clipboard** on all outputs
10. **GitHub token persistence** in localStorage

Nothing is deleted -- it is reorganized into sub-components.
