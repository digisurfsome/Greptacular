# YT Strategy Lab — Context Primer

> **Read this BEFORE your phase PRD.** This document is the mental model for the entire YT Strategy Lab system. Without it, you will build something that technically works but doesn't connect to the rest of the system.

---

## 1. The Big Picture (30-Second Summary)

**YT Strategy Lab** is a platform for extracting actionable, repeatable business strategies from YouTube videos and then executing those strategies autonomously using AI agents with computer-use capabilities. It lives inside the **AutoForge** application (Greptacular codebase) — an autonomous coding agent system with a React UI.

**Who it's for:** Entrepreneurs, agency builders, and content strategists who watch "how I built X" videos and want to operationalize the strategies shown — not just take notes, but have an AI agent actually DO the steps.

**What problem it solves:** Watching a 10-minute YouTube video about building an AI ad agency is interesting. But turning that into a repeatable, step-by-step workflow with prompts, model selection, and autonomous execution is hours of manual work. This system automates the entire pipeline: **Video → Transcript → Strategy → Steps → Prompts → Execution**.

**How the pieces relate:** A YouTube URL enters the system → the ingestion backend extracts transcript/metadata/screenshots → AI processes it into a structured project with steps → the strategy builder lets users review/edit → the computer-use execution engine runs each step autonomously in a browser → users watch live, pause/resume, and chat with the agent.

---

## 2. Foundation Mechanisms / Core Systems Table

These are the existing systems in AutoForge that YT Strategy Lab builds on top of or integrates with.

| # | Name | What It Does | Key File(s) |
|---|------|-------------|-------------|
| 1 | **Hash Router** | Client-side routing via `window.location.hash`. Each page gets a `/#/route` prefix. | `ui/src/main.tsx` |
| 2 | **FastAPI Server** | Python backend with REST + WebSocket. All routers registered in `server/main.py`. | `server/main.py`, `server/routers/__init__.py` |
| 3 | **React Query** | Data fetching/caching with TanStack Query. Used for all API calls in the UI. | `ui/src/hooks/useProjects.ts`, `ui/src/lib/api.ts` |
| 4 | **Neobrutalism Design System** | Tailwind CSS v4 with custom CSS variables, bold borders, flat cards. | `ui/src/styles/globals.css` |
| 5 | **Role Library** | System prompts that shape AI agent behavior. Already built at `/#/roles`. | `ui/src/pages/RoleLibraryPage.tsx` |
| 6 | **Subscription Piping** | Model access through AutoForge's subscription system. No raw API keys needed. | `client.py`, `env_constants.py` |
| 7 | **Process Manager** | Agent process lifecycle (start/stop/pause/resume). Pattern for computer-use engine. | `server/services/process_manager.py` |
| 8 | **WebSocket Updates** | Real-time UI updates via `/ws/projects/{name}`. Pattern for execution streaming. | `server/websocket.py`, `ui/src/hooks/useWebSocket.ts` |
| 9 | **Terminal Manager** | PTY-based terminal sessions. Pattern for interactive Docker container sessions. | `server/services/terminal_manager.py` |
| 10 | **Workspace Standards** | UI/UX build standards for all new workspace pages. | `ui/WORKSPACE_STANDARDS.md` |
| 11 | **Security Model** | Bash command allowlist, filesystem sandboxing, per-project configs. | `security.py`, `client.py` |
| 12 | **localStorage Persistence** | V1 data storage for YT Lab projects and steps. Will migrate to SQLite later. | `ui/src/pages/YTStrategyLabPage.tsx` |

---

## 3. Phase Dependency Chain

### Phase Overview

```
Phase 1 (DONE)  → Core UI + Ingestion: Dashboard page, YouTube ingestion, project CRUD
Phase 2         → AI Auto-Processor: Drop URL → fully populated project with AI-generated steps
Phase 3         → Batch Import: Multiple URLs at once with context per video
Phase 4         → Computer Use Engine: Docker container + agent loop + API endpoints
Phase 5         → Live Execution Viewer: Split-screen layout with noVNC iframe
Phase 6         → Pause/Resume/Takeover: Human-in-the-loop controls
Phase 7         → Model Routing + Roles: Per-step model selection and role system prompts
Phase 8         → Screen Recording: ffmpeg capture of execution sessions
Phase 9         → Video Screenshot Intelligence: Enhanced screenshot capture from source videos
```

### Dependency Diagram

```
Phase 1 (Core UI + Ingestion) ──DONE──
    │
    ├──→ Phase 2 (AI Auto-Processor)
    │        │
    │        └──→ Phase 3 (Batch Import) ── depends on Phase 2's processing pipeline
    │
    ├──→ Phase 4 (Computer Use Engine) ── independent of Phase 2/3
    │        │
    │        ├──→ Phase 5 (Live Viewer) ── needs Phase 4's container + WebSocket
    │        │        │
    │        │        └──→ Phase 6 (Pause/Resume) ── needs Phase 5's UI + Phase 4's agent loop
    │        │
    │        ├──→ Phase 7 (Model Routing) ── needs Phase 4's execution engine
    │        │
    │        └──→ Phase 8 (Screen Recording) ── needs Phase 4's Docker container + ffmpeg
    │
    └──→ Phase 9 (Screenshot Intelligence) ── only needs Phase 1's ingestion backend
```

### What Each Phase Produces and Consumes

```
Phase 1 (DONE)
  Produces:
    - ui/src/pages/YTStrategyLabPage.tsx         (dashboard, project CRUD, strategy builder)
    - ui/src/components/yt-lab/VideoIngestPanel.tsx (YouTube URL input + preview)
    - server/routers/yt_ingestion.py              (POST /api/yt-lab/ingest, GET /api/yt-lab/health)
    - ui/src/lib/types.ts                         (YTStrategy* types, YTIngest* types)
    - ui/src/lib/api.ts                           (ingestYouTubeVideo(), getYTLabHealth())
    - Route: /#/yt-lab                            (in ui/src/main.tsx)
    - Nav button: "YT Lab"                        (in ui/src/App.tsx)

Phase 2 (AI Auto-Processor) — PRD: 07-youtube-auto-processor.md
  Consumes from Phase 1:
    - server/routers/yt_ingestion.py: IngestResponse (transcript, metadata, screenshot_suggestions)
    - ui/src/lib/types.ts: YTStrategyProject, YTStrategyStep, YTIngestResponse
  Produces:
    - server/routers/yt_processing.py             (POST /api/yt-lab/process)
    - Processing pipeline that sends transcript + context to Claude API
    - Returns structured project data matching YTStrategyProject + YTStrategyStep schemas

Phase 3 (Batch Import) — PRD: 01-batch-youtube-import.md
  Consumes from Phase 1:
    - server/routers/yt_ingestion.py: POST /api/yt-lab/ingest (called per URL)
  Consumes from Phase 2:
    - server/routers/yt_processing.py: POST /api/yt-lab/process (called per video)
  Produces:
    - Batch import UI (multi-URL textarea, preview cards, context fields)
    - server/routers/yt_batch.py (POST /api/yt-lab/batch-ingest, POST /api/yt-lab/batch-process)

Phase 4 (Computer Use Engine) — PRD: 02-custom-computer-use-engine.md
  Consumes from Phase 1:
    - ui/src/lib/types.ts: YTStrategyStep (step.prompt, step.model, step.expectedOutput)
  Produces:
    - server/services/computer_use_agent.py       (ComputerUseAgent class with agent loop)
    - server/routers/execution.py                 (REST API: /api/execution/start, /pause, /resume)
    - server/services/docker_manager.py           (Docker container lifecycle)
    - Dockerfile for computer-use container       (Xvfb + Chromium + noVNC + ffmpeg)
    - WebSocket: /ws/execution/{session_id}       (real-time agent events)

Phase 5 (Live Execution Viewer) — PRD: 03-live-execution-viewer.md
  Consumes from Phase 4:
    - WebSocket /ws/execution/{session_id}: agent status, step progress, screenshots
    - Docker container: noVNC endpoint (port 6080)
  Produces:
    - ui/src/components/yt-lab/ExecutionViewer.tsx (split-screen layout)
    - 280px sidebar (step tracker) + 48px top bar (controls) + noVNC iframe (main area)

Phase 6 (Pause/Resume/Takeover) — PRD: 05-pause-resume-takeover.md
  Consumes from Phase 4:
    - server/routers/execution.py: /api/execution/pause, /resume, /inject-message
    - server/services/computer_use_agent.py: pause(), resume(), inject_message()
  Consumes from Phase 5:
    - ui/src/components/yt-lab/ExecutionViewer.tsx (adds controls to top bar)
  Produces:
    - Chat input in top bar for mid-execution messaging
    - Pause/Resume/Stop buttons with state management
    - Takeover mode (pause agent + direct noVNC interaction)

Phase 7 (Model Routing + Roles) — PRD: 06-model-routing-and-roles.md
  Consumes from Phase 4:
    - server/services/computer_use_agent.py: model parameter selection
  Consumes from Phase 1:
    - ui/src/pages/YTStrategyLabPage.tsx: step editor model dropdown (already exists)
  Produces:
    - Auto-routing logic (select_model() based on step keywords)
    - Role attachment system (per-step system prompt from Role Library)
    - Integration with existing Role Library at /#/roles

Phase 8 (Screen Recording) — PRD: 08-screen-recording-and-capture.md
  Consumes from Phase 4:
    - Docker container: X11 display access for ffmpeg capture
    - server/services/computer_use_agent.py: step transition events (triggers capture)
  Produces:
    - server/services/screen_recorder.py          (SessionRecorder, clip capture, screenshot capture)
    - Capture gallery UI (thumbnails + video playback per step)
    - Storage at .autoforge/yt-lab/{project_id}/captures/

Phase 9 (Screenshot Intelligence) — PRD: 04-video-screenshot-intelligence.md
  Consumes from Phase 1:
    - server/routers/yt_ingestion.py: _analyze_screenshot_moments(), _capture_screenshots()
  Produces:
    - Enhanced screenshot detection patterns (screen transitions, results, instructions)
    - OCR analysis of captured screenshots (Claude vision API)
    - Screenshot → step linking (associate screenshots with relevant strategy steps)
```

---

## 4. Vocabulary / Glossary

| Term | Definition | Where It Lives |
|------|-----------|---------------|
| **Project** | A YT Strategy Lab project. Contains metadata (name, niche, tags, source URL) and an ordered list of Steps. Stored in localStorage under `yt-lab-projects`. | `ui/src/lib/types.ts` → `YTStrategyProject` |
| **Step** | A single action in a strategy workflow. Has a title, description, prompt (for AI execution), expected output, notes, AI output, model selection, and sub-steps. | `ui/src/lib/types.ts` → `YTStrategyStep` |
| **Sub-Step** | A granular task within a Step. Has its own prompt and status. | `ui/src/lib/types.ts` → `YTStrategySubStep` |
| **Strategy Builder** | The detail view of a project where users edit steps, prompts, and sub-steps. Has a collapsible sidebar for step navigation. | `ui/src/pages/YTStrategyLabPage.tsx` (detail view) |
| **Ingestion** | The process of fetching transcript, metadata, URLs, and screenshot suggestions from a YouTube video URL. No AI involved — pure data extraction. | `server/routers/yt_ingestion.py` |
| **Processing** | The AI step that takes raw ingestion data + user context and produces a fully populated project with steps and prompts. Uses Claude API. | PRD: `07-youtube-auto-processor.md` |
| **Execution** | Running a strategy step autonomously using the computer-use agent in a Docker container with a real browser. | PRD: `02-custom-computer-use-engine.md` |
| **Computer Use Agent** | The Python class that loops Claude API calls with `computer_20250124` tool type, executing browser actions in a virtual display. | PRD: `02-custom-computer-use-engine.md` |
| **noVNC** | WebSocket-based VNC client that renders a remote desktop in an HTML5 canvas. Used to show the agent's browser in an iframe. | PRD: `03-live-execution-viewer.md` |
| **Role** | A system prompt that shapes how the AI agent approaches a task (e.g., "Researcher", "Marketer", "Designer"). Comes from the existing Role Library. | `ui/src/pages/RoleLibraryPage.tsx`, PRD: `06-model-routing-and-roles.md` |
| **Model Routing** | Per-step selection of which Claude model to use (Opus for complex, Sonnet for balanced, Haiku for simple). Can be "Auto" to let the system decide. | PRD: `06-model-routing-and-roles.md` |
| **Seed Template** | A pre-populated project JSON file with all steps and prompts filled out. Users can import these as starting points. | `docs/yt-strategies/templates/` |
| **Niche** | The business vertical a strategy targets (e.g., "Automotive / Car Dealerships"). Strategies use `{variables}` for niche-specific details. | `YTStrategyProject.niche` |

**Easily confused terms:**
- **Ingestion** vs **Processing**: Ingestion is data extraction only (transcript, metadata). Processing is AI analysis that turns raw data into structured steps. They are separate endpoints.
- **Step** (YT Lab) vs **Feature** (AutoForge core): Steps are strategy workflow actions. Features are coding tasks tracked in `features.db`. They are completely separate systems.
- **Project** (YT Lab) vs **Project** (AutoForge core): YT Lab projects are strategy workflows in localStorage. AutoForge projects are coding projects in the registry. They share no data.

---

## 5. Existing Codebase Patterns

### FastAPI Router Pattern

Study `server/routers/yt_ingestion.py` — this is the pattern for all new YT Lab backend routes.

```python
# File: server/routers/yt_ingestion.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/yt-lab", tags=["yt-lab"])

# Pydantic request/response models at top of file
class IngestRequest(BaseModel):
    url: str = Field(..., min_length=5, max_length=2048)
    capture_screenshots: bool = False

class IngestResponse(BaseModel):
    video_id: str
    title: str
    # ... all fields typed

# Endpoint with docstring
@router.post("/ingest", response_model=IngestResponse)
async def ingest_video(request: IngestRequest) -> IngestResponse:
    """Ingest a YouTube video: fetch transcript, metadata, and screenshot suggestions."""
    # Implementation
```

**Key rules:**
- Router prefix: `/api/yt-lab` for all YT Lab endpoints
- Pydantic models for ALL request/response bodies
- Register in `server/routers/__init__.py` and import in `server/main.py`
- Helper functions are private (`_extract_video_id`, `_get_transcript`)

### Router Registration Pattern

```python
# server/routers/__init__.py — add export:
from .yt_processing import router as yt_processing_router

# server/main.py — add import + include:
from .routers import yt_processing_router
app.include_router(yt_processing_router)
```

### React Page Pattern (Hash Route)

Study `ui/src/pages/YTStrategyLabPage.tsx` — this is the pattern.

```tsx
// ui/src/main.tsx — route registration:
import { YTStrategyLabPage } from './pages/YTStrategyLabPage'

// Inside Root() component:
if (hash === '#/yt-lab' || hash.startsWith('#/yt-lab/')) {
  return <YTStrategyLabPage />
}
```

**Key rules:**
- Single-file page components in `ui/src/pages/`
- Multi-view pages manage their own view state internally (list/detail/create/edit)
- Use `window.location.hash` for navigation, NOT React Router
- Import UI primitives from `@/components/ui/` (Button, Card, Badge, Input, etc.)
- Import icons from `lucide-react`
- Import types from `@/lib/types`

### API Client Pattern

Study `ui/src/lib/api.ts` — specifically the YT Lab functions at the bottom:

```tsx
// ui/src/lib/api.ts
export async function ingestYouTubeVideo(url: string, captureScreenshots = false) {
  const res = await fetch(`${API_BASE}/yt-lab/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, capture_screenshots: captureScreenshots }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<YTIngestResponse>
}
```

**Key rules:**
- Functions in `api.ts`, NOT inline in components
- Type the return value with `as Promise<T>`
- Throw on non-ok responses
- API_BASE is already defined at the top of the file

### localStorage Pattern (V1 Persistence)

Study `YTStrategyLabPage.tsx` constants section:

```tsx
const STORAGE_KEY_PROJECTS = 'yt-lab-projects'

function stepsStorageKey(projectId: string): string {
  return `yt-lab-steps-${projectId}`
}

// Load:
const stored = localStorage.getItem(STORAGE_KEY_PROJECTS)
const projects: YTStrategyProject[] = stored ? JSON.parse(stored) : []

// Save:
localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(updatedProjects))
```

**Key rules:**
- Projects stored as JSON array under `yt-lab-projects`
- Steps stored separately per project under `yt-lab-steps-{projectId}`
- Always parse with fallback to empty array
- Future phases will migrate to SQLite via `api/database.py` pattern

### Component Pattern

Study `ui/src/components/yt-lab/VideoIngestPanel.tsx`:

```tsx
interface VideoIngestPanelProps {
  onIngestComplete?: (result: YTIngestResponse) => void
}

// Self-contained component, manages own state
// Calls parent via callback props
// Uses lucide-react icons + Radix UI primitives
```

### Type Definition Pattern

Study `ui/src/lib/types.ts` YT Lab section (lines 1390-1469):

```tsx
export type YTStrategyStepStatus = 'pending' | 'in_progress' | 'complete'

export interface YTStrategyStep {
  id: string
  projectId: string
  order: number
  title: string
  description: string
  prompt: string
  expectedOutput: string
  notes: string
  aiOutput: string
  status: YTStrategyStepStatus
  model: string
  subSteps: YTStrategySubStep[]
}
```

**Key rules:**
- All types in `ui/src/lib/types.ts`
- Prefix with `YT` to distinguish from AutoForge core types
- Status types are string unions, not enums
- Use `interface` not `type` for objects

---

## 6. File Location Map

### What Already Exists (Phase 1 — DONE)

```
ui/src/pages/YTStrategyLabPage.tsx          ← Main page (1500+ lines). 4 views: list, create, edit, detail
ui/src/components/yt-lab/VideoIngestPanel.tsx ← YouTube URL input + preview component (421 lines)
ui/src/lib/types.ts                          ← YT* types at bottom (lines 1390-1469)
ui/src/lib/api.ts                            ← ingestYouTubeVideo() and getYTLabHealth() at bottom
ui/src/main.tsx                              ← Route: /#/yt-lab (line 58)
ui/src/App.tsx                               ← Nav button: "YT Lab" with FlaskConical icon
server/routers/yt_ingestion.py               ← Backend: POST /api/yt-lab/ingest, GET /api/yt-lab/health
server/routers/__init__.py                   ← Exports yt_ingestion_router
server/main.py                               ← Includes yt_ingestion_router
```

### What Gets Created (by Phase)

```
docs/yt-strategies/
├── CONTEXT_PRIMER.md                        ← THIS DOCUMENT
├── ai-ad-agency-breakdown.md                ← Detailed video breakdown (exists)
├── prds/
│   ├── 01-batch-youtube-import.md           ← Phase 3 spec (exists)
│   ├── 02-custom-computer-use-engine.md     ← Phase 4 spec (exists)
│   ├── 03-live-execution-viewer.md          ← Phase 5 spec (exists)
│   ├── 04-video-screenshot-intelligence.md  ← Phase 9 spec (exists)
│   ├── 05-pause-resume-takeover.md          ← Phase 6 spec (exists)
│   ├── 06-model-routing-and-roles.md        ← Phase 7 spec (exists)
│   ├── 07-youtube-auto-processor.md         ← Phase 2 spec (exists)
│   ├── 08-screen-recording-and-capture.md   ← Phase 8 spec (exists)
│   └── 09-computer-use-options-comparison.md ← Decision doc (exists)
└── templates/
    ├── ai-ad-agency-project-seed.json       ← Pre-populated 9-step project (exists)
    └── blank-agency-template.json           ← Generic template with {variables} (exists)

server/routers/
├── yt_ingestion.py                          ← Phase 1 (exists)
├── yt_processing.py                         ← Phase 2: POST /api/yt-lab/process
├── yt_batch.py                              ← Phase 3: batch ingest + process
└── execution.py                             ← Phase 4: /api/execution/* endpoints

server/services/
├── computer_use_agent.py                    ← Phase 4: ComputerUseAgent class
├── docker_manager.py                        ← Phase 4: container lifecycle
└── screen_recorder.py                       ← Phase 8: ffmpeg capture

ui/src/components/yt-lab/
├── VideoIngestPanel.tsx                     ← Phase 1 (exists)
├── BatchImportView.tsx                      ← Phase 3: multi-URL import UI
├── ExecutionViewer.tsx                      ← Phase 5: split-screen layout
├── ExecutionTopBar.tsx                      ← Phase 5/6: controls + chat input
├── StepTracker.tsx                          ← Phase 5: sidebar step list
└── CaptureGallery.tsx                       ← Phase 8: screenshot/video thumbnails

docker/
└── computer-use/
    ├── Dockerfile                           ← Phase 4: Xvfb + Chromium + noVNC + ffmpeg
    └── supervisord.conf                     ← Phase 4: process manager config
```

### What Already Exists (Study These for Patterns)

| File | What to Learn |
|------|--------------|
| `ui/src/pages/YTStrategyLabPage.tsx` | Page structure, view state management, localStorage CRUD, step editor UI |
| `ui/src/components/yt-lab/VideoIngestPanel.tsx` | Self-contained component pattern, progressive status display |
| `server/routers/yt_ingestion.py` | FastAPI router pattern, Pydantic models, helper function structure |
| `server/services/process_manager.py` | Process lifecycle pattern — model for computer-use agent management |
| `server/services/terminal_manager.py` | PTY session management — pattern for interactive Docker sessions |
| `ui/src/hooks/useWebSocket.ts` | WebSocket hook pattern — use for execution streaming |
| `ui/src/pages/RoleLibraryPage.tsx` | Role CRUD pattern — integrate role selection per step |
| `ui/WORKSPACE_STANDARDS.md` | Mandatory UI standards (layout, typography, states, responsive) |
| `ui/src/styles/globals.css` | CSS variables, color tokens, animation definitions |
| `server/main.py` | Router registration pattern (import + include) |

---

## 7. Architectural Decisions (The WHYs)

### AD-1: localStorage for V1, SQLite Later

**Decision:** Store YT Lab projects and steps in browser localStorage, not SQLite.

**Why:** Speed of iteration. The existing AutoForge features system uses SQLite via SQLAlchemy, which is the right call for multi-agent concurrent access. But YT Lab V1 is a single-user tool where the data is simple JSON objects. localStorage means zero backend schema work, instant persistence, and no migration headaches during rapid UI iteration.

**Implication:** Do NOT create SQLAlchemy models for YT Lab data yet. All reads/writes go through localStorage. When we migrate to SQLite (for SaaS multi-user support), we'll create models in `api/database.py` following the existing `Feature` model pattern.

### AD-2: Separate Backend for Ingestion, Not for Project CRUD

**Decision:** YouTube ingestion hits a FastAPI endpoint. Project/step CRUD stays client-side.

**Why:** Ingestion requires Python packages (`youtube-transcript-api`, `yt-dlp`, `ffmpeg`) that can't run in the browser. But project CRUD is just JSON manipulation — no reason to round-trip to the server for that in V1.

**Implication:** New backend routes only for things that REQUIRE server-side execution (AI processing, ingestion, execution engine, screen recording). Project management stays in the page component.

### AD-3: Hash-Based Routing (Not React Router)

**Decision:** Use `window.location.hash` for all routing. YT Lab lives at `/#/yt-lab`.

**Why:** The entire AutoForge UI uses hash routing. It's established. All pages (Workspace, DunkStack, Roles, Dashboard, YT Lab) follow this pattern. React Router would introduce a conflicting routing system.

**Implication:** All navigation uses `window.location.hash = '#/yt-lab'`. Never use `<Link>` from React Router. The `Root()` component in `main.tsx` switches on hash value.

### AD-4: Custom Computer Use API (Not Chrome Extension)

**Decision:** Build a custom execution engine using Anthropic's Computer Use API in a Docker container, not rely on Claude in Chrome.

**Why:** Chrome Extension can't be embedded in an iframe, can't be programmatically controlled, and can't be deployed as SaaS. The custom API approach gives us: iframe embedding (noVNC), full agent loop control (pause/resume/inject), screen recording (ffmpeg on X11), model flexibility (Opus/Sonnet per step), and SaaS deployability (Docker container per user).

**Implication:** The execution engine is a Docker container running Xvfb + Chromium + noVNC. The Python agent loop lives server-side, NOT in the browser. The UI communicates via REST + WebSocket.

### AD-5: Subscription-Based Model Access (No Raw API Keys)

**Decision:** All Claude API calls go through AutoForge's existing subscription system.

**Why:** Users already configure their API access in AutoForge settings. Adding a separate API key flow for YT Lab would confuse users and fragment the billing model. The subscription piping handles Opus/Sonnet/Haiku routing, rate limiting, and billing.

**Implication:** Never ask users for an ANTHROPIC_API_KEY in YT Lab UI. Use the existing `client.py` / `env_constants.py` infrastructure for all model calls. The `ANTHROPIC_API_KEY` env var is already set.

### AD-6: Opus 4.6 Default for Computer Use, Sonnet for Processing

**Decision:** Computer-use execution defaults to Opus 4.6. Video processing (transcript → steps) defaults to Sonnet 4.6.

**Why:** Computer use requires strong visual understanding and multi-step reasoning — Opus is significantly better at screen interaction. Video processing is mostly text extraction and structuring — Sonnet is sufficient and faster/cheaper.

**Implication:** The model dropdown defaults in the step editor should be Opus for execution. The processing pipeline (Phase 2) should default to Sonnet. Haiku should NOT be used for computer use (insufficient reasoning for screen interaction).

### AD-7: Steps Have Sub-Steps (Two-Level Nesting Only)

**Decision:** Each Step can contain Sub-Steps. No deeper nesting.

**Why:** Strategies from videos naturally break into major steps (e.g., "Create Brand Guide") with sub-tasks (e.g., "Generate color palette", "Create logo concepts"). Two levels covers 95% of cases. Deeper nesting creates complexity without value.

**Implication:** `YTStrategyStep.subSteps: YTStrategySubStep[]`. Sub-steps have their own prompts and statuses. Do NOT add sub-sub-steps.

### AD-8: All Prefix with YT to Avoid Naming Collisions

**Decision:** All TypeScript types for YT Lab are prefixed with `YT` (e.g., `YTStrategyProject`, `YTStrategyStep`).

**Why:** AutoForge already has `ProjectSummary`, `Feature`, and other generic names. Prefixing prevents collisions in the shared `types.ts` file and makes it obvious which types belong to YT Lab.

**Implication:** Always prefix: `YTStrategyProject`, `YTStrategyStep`, `YTStrategySubStep`, `YTProjectStatus`, `YTStrategyStepStatus`, `YTIngestResponse`, `YTTranscriptSegment`, `YTScreenshotSuggestion`, `YTLabHealth`.

---

## 8. Integration Points Across Phases

### Phase 1 → Phase 2 (Ingestion → Processing)

```python
# Phase 2 consumes the ingestion response
from server.routers.yt_ingestion import IngestResponse, TranscriptSegment, ScreenshotSuggestion

# Phase 2 endpoint receives ingestion data + user context
class ProcessRequest(BaseModel):
    video_id: str
    transcript: list[TranscriptSegment]
    metadata: dict  # title, channel, duration, description
    user_context: str
    extracted_urls: list[str]
    screenshot_suggestions: list[ScreenshotSuggestion]
    model: str = "claude-sonnet-4-6"

# Phase 2 returns structured project data
class ProcessResponse(BaseModel):
    project: dict  # matches YTStrategyProject shape
    steps: list[dict]  # matches YTStrategyStep shape
    processing_time: float
```

### Phase 1 → Phase 4 (Step Data → Execution Engine)

```typescript
// The execution engine reads step data from the strategy builder
interface ExecutionRequest {
  projectId: string
  stepId: string
  prompt: string          // from YTStrategyStep.prompt
  model: string           // from YTStrategyStep.model (e.g., "claude-opus-4-6")
  roleSystemPrompt?: string  // from Phase 7's role attachment
  previousOutputs?: string[] // from completed steps' aiOutput fields
}
```

```python
# Backend receives execution request
class StartExecutionRequest(BaseModel):
    project_id: str
    step_id: str
    prompt: str
    model: str = "claude-opus-4-6"
    role_system_prompt: str = ""
    previous_outputs: list[str] = []
```

### Phase 4 → Phase 5 (Execution Engine → Live Viewer)

```typescript
// WebSocket messages from execution engine to UI
interface ExecutionEvent {
  type: 'status' | 'screenshot' | 'step_progress' | 'agent_message' | 'error'
  session_id: string
  data: {
    status?: 'starting' | 'running' | 'paused' | 'completed' | 'error'
    screenshot_url?: string    // base64 or file path
    current_step?: number
    total_steps?: number
    agent_text?: string        // what the agent is saying/thinking
    error_message?: string
  }
}

// noVNC iframe source
const novncUrl = `http://localhost:6080/vnc.html?autoconnect=true&resize=scale`
```

### Phase 5 → Phase 6 (Live Viewer → Pause/Resume)

```typescript
// REST API calls from UI controls
await fetch('/api/execution/pause', { method: 'POST', body: JSON.stringify({ session_id }) })
await fetch('/api/execution/resume', { method: 'POST', body: JSON.stringify({ session_id }) })
await fetch('/api/execution/inject-message', {
  method: 'POST',
  body: JSON.stringify({ session_id, message: "Skip this step" })
})
```

### Phase 7 (Role Library Integration)

```typescript
// Fetch roles from existing Role Library
const roles = await fetch('/api/roles').then(r => r.json())

// Attach role to step execution
const executionRequest = {
  ...stepData,
  roleSystemPrompt: selectedRole.system_prompt
}
```

---

## 9. Config Structure

### Environment Variables

```bash
# Already configured in AutoForge (DO NOT DUPLICATE)
ANTHROPIC_API_KEY=sk-ant-...     # Used by computer-use agent and processing pipeline

# New for YT Lab (add to .env)
COMPUTER_USE_ENABLED=true         # Enable/disable computer-use execution
COMPUTER_USE_DOCKER_IMAGE=anthropic/computer-use-reference:latest
COMPUTER_USE_DISPLAY_WIDTH=1920   # Virtual display resolution
COMPUTER_USE_DISPLAY_HEIGHT=1080
COMPUTER_USE_NOVNC_PORT=6080      # noVNC WebSocket port
COMPUTER_USE_DEFAULT_MODEL=claude-opus-4-6  # Default for execution
YT_LAB_DEFAULT_PROCESSING_MODEL=claude-sonnet-4-6  # Default for transcript processing

# Optional
YOUTUBE_API_KEY=                   # YouTube Data API v3 (optional, yt-dlp is primary)
CHROME_EXTENSION_MODE=false        # Enable Chrome Extension fallback
```

### localStorage Keys

```
yt-lab-projects          → JSON array of YTStrategyProject objects
yt-lab-steps-{projectId} → JSON array of YTStrategyStep objects (per project)
```

### Docker Container Ports

```
5900  → VNC (internal)
6080  → noVNC WebSocket (exposed for iframe)
8080  → Control API (health check, session management)
```

---

## 10. Testing Strategy

### Backend Tests

Test files go in the project root alongside existing test files:

```
test_yt_ingestion.py         ← Tests for ingestion router
test_yt_processing.py        ← Tests for processing pipeline
test_execution_engine.py     ← Tests for computer-use agent
```

**Test pattern** (follows existing `test_client.py`):

```python
import pytest
from server.routers.yt_ingestion import _extract_video_id, _extract_urls

def test_extract_video_id_standard():
    assert _extract_video_id("https://www.youtube.com/watch?v=abc12345678") == "abc12345678"

def test_extract_video_id_short():
    assert _extract_video_id("https://youtu.be/abc12345678") == "abc12345678"

def test_extract_urls_from_description():
    text = "Check out https://example.com and https://other.com for more"
    urls = _extract_urls(text)
    assert len(urls) == 2
    assert "https://example.com" in urls
```

### Frontend Tests

Follow existing Playwright pattern:

```bash
cd ui
npm run test:e2e        # Playwright end-to-end tests
```

### CI/CD

Existing GitHub Actions workflow (`.github/workflows/ci.yml`) runs:
- Python: ruff lint + security tests
- UI: ESLint + TypeScript build

New YT Lab code must pass both. Run `npm run build` in `ui/` to verify TypeScript compiles.

---

## 11. What NOT to Do

1. **Don't create SQLAlchemy models for YT Lab data.** V1 uses localStorage. When we need SQLite, it'll be a dedicated migration phase with proper schema design.

2. **Don't use React Router.** The app uses hash-based routing via `window.location.hash`. All existing pages follow this pattern. Do not introduce `react-router-dom`.

3. **Don't put Claude API calls in FastAPI routes directly.** The processing pipeline (Phase 2) should use a service class (like `server/services/spec_chat_session.py`), NOT inline API calls in the router.

4. **Don't create separate API key configuration for YT Lab.** Use the existing `ANTHROPIC_API_KEY` from AutoForge's `.env`. The subscription piping is already built.

5. **Don't add npm dependencies without checking `ui/package.json`.** The UI already has React 19, TanStack Query, Tailwind v4, Radix UI, lucide-react, xterm.js, dagre. Check what's available before adding anything.

6. **Don't add Python dependencies without checking `requirements.txt`.** FastAPI, Pydantic, SQLAlchemy, uvicorn, etc. are already installed. Only `youtube-transcript-api` and `yt-dlp` were added for ingestion.

7. **Don't modify `YTStrategyLabPage.tsx` without reading it first.** It's 1500+ lines with 4 view states. Understand the view switching mechanism before editing.

8. **Don't create a `YTStrategyStep.status` that conflicts with execution status.** The step status (`pending`/`in_progress`/`complete`) is about content readiness. The execution status (`starting`/`running`/`paused`/`completed`/`error`) is about the agent running that step. These are SEPARATE states.

9. **Don't skip the `ui/WORKSPACE_STANDARDS.md` build standards.** Every new page/component must follow these standards for layout, typography, loading states, error states, responsive breakpoints, and dark mode.

10. **Don't hardcode model names as bare strings throughout the codebase.** Use constants. The model dropdown in `YTStrategyLabPage.tsx` already defines `MODEL_OPTIONS` — reference that pattern.

11. **Don't put Docker container management in the router.** Container lifecycle belongs in `server/services/docker_manager.py`, NOT in `server/routers/execution.py`. The router calls the service.

12. **Don't build a custom video player.** Use HTML5 `<video>` element for playback of captured clips. No need for video.js or other libraries.

---

## Quick Reference: PRD-to-Phase Mapping

| PRD File | Phase | Build Priority |
|----------|-------|---------------|
| `07-youtube-auto-processor.md` | Phase 2 | HIGH — unlocks the core value prop |
| `01-batch-youtube-import.md` | Phase 3 | MEDIUM — quality-of-life for multi-video users |
| `02-custom-computer-use-engine.md` | Phase 4 | HIGH — the execution engine everything else needs |
| `03-live-execution-viewer.md` | Phase 5 | HIGH — makes execution visible and usable |
| `05-pause-resume-takeover.md` | Phase 6 | MEDIUM — human-in-the-loop controls |
| `06-model-routing-and-roles.md` | Phase 7 | LOW — enhances quality but not blocking |
| `08-screen-recording-and-capture.md` | Phase 8 | LOW — nice-to-have for documentation |
| `04-video-screenshot-intelligence.md` | Phase 9 | LOW — enhances ingestion accuracy |
| `09-computer-use-options-comparison.md` | N/A | Decision document, not a build phase |
