# Wave 1 — Agent 3: Computer Use Execution Engine

> **Wave 1 agents run in parallel** — they have zero code dependencies on each other.
> Each agent owns a vertical slice of the YT Strategy Lab system.

---

## Agent Summary (Wave 1)

| Agent | Focus Area | PRD(s) | Key Output |
|-------|-----------|--------|------------|
| Agent 1 | YouTube Auto-Processor | 07 | AI processing pipeline (transcript → steps) |
| Agent 2 | Batch YouTube Import | 01 | Multi-URL import UI + backend |
| **Agent 3** | **Computer Use Engine** | **02, 09** | **Backend services + Docker setup + API endpoints** |
| Agent 4 | Video Screenshot Intelligence | 04 | Enhanced screenshot capture + OCR |
| Agent 5 | Model Routing & Roles | 06 | Per-step model selection + role system |

---

## Mission

Build the backend execution engine that runs YT Strategy Lab steps autonomously using Anthropic's Computer Use API in a Docker container. This is **Phase 4** — the foundation that Phases 5, 6, 7, and 8 all depend on.

You are building:
1. A Python service class (`ComputerUseAgent`) that loops Claude API calls with the `computer_20250124` tool
2. A Docker container manager for Xvfb + Chromium + noVNC lifecycle
3. FastAPI REST + WebSocket endpoints for starting/stopping/pausing execution sessions
4. A Dockerfile for the computer-use container environment

**You are NOT building:**
- The live viewer UI (Phase 5 / Agent for Wave 2)
- Pause/resume/takeover UI controls (Phase 6)
- Screen recording with ffmpeg (Phase 8)
- Any frontend React components

---

## Read These Files First

Study these files to understand the existing patterns before writing any code:

| File | What to Learn |
|------|--------------|
| `docs/yt-strategies/CONTEXT_PRIMER.md` | Full system context, architectural decisions, vocabulary, integration points |
| `docs/yt-strategies/prds/02-custom-computer-use-engine.md` | Primary PRD — architecture, agent loop, API spec, environment variables |
| `docs/yt-strategies/prds/09-computer-use-options-comparison.md` | Decision doc — why custom API, agent loop code, tool definitions |
| `server/services/process_manager.py` | **Pattern to follow** — process lifecycle (start/stop/pause/resume), output streaming, sanitization |
| `server/routers/yt_ingestion.py` | **Pattern to follow** — FastAPI router with Pydantic models, `/api/yt-lab` prefix |
| `server/routers/__init__.py` | Router registration pattern (export + import) |
| `server/main.py` | Router inclusion pattern (`app.include_router`) |
| `server/services/terminal_manager.py` | PTY session management — pattern for interactive container sessions |
| `ui/src/lib/types.ts` (lines 1390-1469) | `YTStrategyStep` schema — what step data looks like (prompt, model, expectedOutput, aiOutput) |
| `CLAUDE.md` | Project-wide build commands, architecture overview |

---

## Files to Create

### 1. `server/services/computer_use_agent.py` — Core Agent Class

The heart of the execution engine. Manages the Claude API agent loop with computer-use tools.

```python
class ComputerUseAgent:
    """
    Manages a single computer-use agent execution session.

    Loops Claude API calls with computer_20250124, text_editor_20250124,
    and bash_20250124 tools. Executes tool calls (screenshot, click, type, etc.)
    and streams events to registered callbacks.
    """

    def __init__(self, session_id: str, model: str = "claude-opus-4-6"):
        ...

    async def execute_step(self, step_prompt: str, context: str = "",
                           role_system_prompt: str = "") -> StepResult:
        """Execute a single strategy step. Returns result with aiOutput and screenshots."""

    async def execute_steps(self, steps: list[StepConfig]) -> list[StepResult]:
        """Execute multiple steps sequentially, passing context forward."""

    async def pause(self) -> None:
        """Pause after current tool call completes. Takes screenshot of current state."""

    async def resume(self) -> None:
        """Resume from paused state with screenshot context."""

    async def inject_message(self, message: str) -> None:
        """Inject a human message between tool calls."""

    async def stop(self) -> None:
        """Stop execution entirely. Cleanup resources."""

    def on_event(self, callback: Callable[[ExecutionEvent], Awaitable[None]]) -> None:
        """Register callback for execution events (status, screenshots, agent messages)."""
```

**Key implementation details:**
- Use `anthropic.Anthropic()` client (reads `ANTHROPIC_API_KEY` from env)
- Tool definitions: `computer_20250124`, `text_editor_20250124`, `bash_20250124`
- Display dimensions: read from env vars (`COMPUTER_USE_DISPLAY_WIDTH`, `COMPUTER_USE_DISPLAY_HEIGHT`)
- The agent loop runs until `stop_reason == "end_turn"` (no more tool calls)
- Pause checks happen BETWEEN tool calls (never interrupt mid-action)
- Screenshots are captured via the computer-use tool's screenshot action
- All events are emitted to registered callbacks for WebSocket streaming
- Handle `tool_use` blocks in response → execute tool → return `tool_result`

**Pydantic models to define in this file:**

```python
class StepConfig(BaseModel):
    step_id: str
    prompt: str
    model: str = "claude-opus-4-6"
    role_system_prompt: str = ""
    previous_outputs: list[str] = []

class StepResult(BaseModel):
    step_id: str
    ai_output: str
    screenshots: list[str]  # base64 encoded
    status: Literal["completed", "error", "paused"]
    error_message: str = ""

class ExecutionEvent(BaseModel):
    type: Literal["status", "screenshot", "step_progress", "agent_message", "error"]
    session_id: str
    data: dict  # varies by type
```

### 2. `server/services/docker_manager.py` — Container Lifecycle

Manages Docker container start/stop/health for the computer-use environment.

```python
class DockerManager:
    """
    Manages Docker containers for computer-use execution.

    Each session gets its own container with Xvfb, Chromium, and noVNC.
    Containers are ephemeral — created on session start, destroyed on stop.
    """

    def __init__(self):
        ...

    async def start_container(self, session_id: str) -> ContainerInfo:
        """Start a new container. Returns connection info (noVNC port, VNC port)."""

    async def stop_container(self, session_id: str) -> None:
        """Stop and remove the container."""

    async def get_container_status(self, session_id: str) -> ContainerStatus:
        """Check if container is running, get ports and health."""

    async def health_check(self, session_id: str) -> bool:
        """Verify container services (Xvfb, Chromium, noVNC) are responsive."""

    async def take_screenshot(self, session_id: str) -> str:
        """Capture current screen state. Returns base64-encoded PNG."""
```

**Key implementation details:**
- Use `docker` Python SDK (`import docker; docker.from_env()`)
- Container image: read from `COMPUTER_USE_DOCKER_IMAGE` env var (default: `anthropic/computer-use-reference:latest`)
- Port mapping: assign dynamic host ports for VNC (5900), noVNC (6080), control API (8080)
- Container labels: tag with `session_id` for easy lookup
- Cleanup: always remove containers on stop (no lingering containers)
- Health check: verify noVNC WebSocket is responding before returning from `start_container`
- Timeout: container start has a configurable timeout (default 30s)

**Pydantic models:**

```python
class ContainerInfo(BaseModel):
    session_id: str
    container_id: str
    novnc_port: int
    vnc_port: int
    novnc_url: str  # e.g., "http://localhost:6080/vnc.html?autoconnect=true&resize=scale"
    status: Literal["starting", "running", "stopped", "error"]

class ContainerStatus(BaseModel):
    running: bool
    container_id: str | None
    ports: dict[str, int]
    uptime_seconds: float
```

### 3. `server/services/execution_engine.py` — Session Orchestrator

Top-level orchestrator that ties together the agent and Docker container.

```python
class ExecutionEngine:
    """
    Orchestrates computer-use execution sessions.

    Manages the lifecycle: start container → run agent → stream events → cleanup.
    This is what the router calls — it coordinates DockerManager and ComputerUseAgent.
    """

    def __init__(self):
        self.docker_manager = DockerManager()
        self.sessions: dict[str, ExecutionSession] = {}

    async def start_session(self, project_id: str, steps: list[StepConfig]) -> str:
        """Start execution session. Returns session_id."""

    async def pause_session(self, session_id: str) -> None:
        """Pause the running session."""

    async def resume_session(self, session_id: str) -> None:
        """Resume a paused session."""

    async def inject_message(self, session_id: str, message: str) -> None:
        """Send human message to agent mid-execution."""

    async def stop_session(self, session_id: str) -> None:
        """Stop session and cleanup container."""

    async def get_session_status(self, session_id: str) -> SessionStatus:
        """Get current status, progress, screenshots."""

class ExecutionSession(BaseModel):
    session_id: str
    project_id: str
    status: Literal["starting", "running", "paused", "completed", "error"]
    current_step_index: int = 0
    total_steps: int = 0
    container_info: ContainerInfo | None = None
    started_at: str  # ISO datetime
    screenshots: list[str] = []
```

**Key implementation details:**
- Generate session IDs with `uuid.uuid4().hex[:12]`
- Store active sessions in memory (`self.sessions` dict)
- Session startup flow: create container → wait for health → create agent → start execution loop
- On error: capture screenshot, log error, emit error event, but don't crash the engine
- Cleanup: always stop container even if agent errors out
- Concurrent sessions: support multiple sessions (different projects) but limit total containers

### 4. `server/routers/execution.py` — REST + WebSocket API

FastAPI router exposing execution engine to the UI.

```python
router = APIRouter(prefix="/api/execution", tags=["execution"])

# REST endpoints
POST /api/execution/start          → Start a new execution session
POST /api/execution/{session_id}/pause    → Pause session
POST /api/execution/{session_id}/resume   → Resume session
POST /api/execution/{session_id}/stop     → Stop session
POST /api/execution/{session_id}/inject   → Inject human message
GET  /api/execution/{session_id}/status   → Get session status

# WebSocket endpoint (register in server/main.py, NOT in router)
WS   /ws/execution/{session_id}    → Real-time execution events stream
```

**Follow the pattern from `server/routers/yt_ingestion.py`:**
- Pydantic request/response models at top of file
- Router prefix: `/api/execution`
- Register in `server/routers/__init__.py` and `server/main.py`
- WebSocket handler follows pattern from `server/main.py` existing WS endpoints

**Pydantic models for the router:**

```python
class StartExecutionRequest(BaseModel):
    project_id: str
    steps: list[StepConfig]

class StartExecutionResponse(BaseModel):
    session_id: str
    status: str
    novnc_url: str | None = None

class InjectMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)

class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    current_step_index: int
    total_steps: int
    novnc_url: str | None
    started_at: str
    screenshots: list[str]
```

### 5. `docker/computer-use/Dockerfile` — Container Image

```dockerfile
FROM ubuntu:22.04

# Install Xvfb, Chromium, noVNC, websockify, and utilities
# Configure supervisord to manage all services
# Expose ports: 5900 (VNC), 6080 (noVNC), 8080 (control)
# Set display resolution from build args or env vars
```

**Key requirements:**
- Xvfb virtual display at configurable resolution (default 1920x1080)
- Chromium browser pre-installed with sensible defaults
- noVNC + websockify for WebSocket-based VNC streaming
- Lightweight — minimize image size where possible
- Non-root user for security
- Health check endpoint on port 8080

### 6. `docker/computer-use/supervisord.conf` — Process Manager

Manages Xvfb, Chromium, noVNC, and websockify inside the container.

---

## Files to Modify

### `server/routers/__init__.py`
Add export:
```python
from .execution import router as execution_router
```

### `server/main.py`
Add import + include:
```python
from .routers import execution_router
app.include_router(execution_router)
```

Also add WebSocket endpoint:
```python
@app.websocket("/ws/execution/{session_id}")
async def execution_websocket(websocket: WebSocket, session_id: str):
    ...
```

### `requirements.txt`
Add (if not already present):
```
docker>=7.0.0
anthropic>=0.40.0
```

---

## Implementation Steps

Follow this order strictly:

### Step 1: Pydantic Models & Types
Define all shared Pydantic models in a dedicated section or file. These are the contract between services.

### Step 2: Docker Manager (`server/services/docker_manager.py`)
- Implement container lifecycle using the `docker` Python SDK
- Test with: `docker run -d anthropic/computer-use-reference:latest`
- Verify noVNC is accessible at the mapped port
- Implement health check (HTTP GET to noVNC endpoint)
- Implement screenshot capture via X11 tools in the container

### Step 3: Computer Use Agent (`server/services/computer_use_agent.py`)
- Implement the agent loop following the code in PRD `09-computer-use-options-comparison.md`
- Tool definitions: `computer_20250124`, `text_editor_20250124`, `bash_20250124`
- Handle `tool_use` response blocks → execute tool → return `tool_result`
- Implement pause/resume (flag check between tool calls)
- Implement message injection (append to message history)
- Emit events via registered callbacks
- Handle errors gracefully (capture screenshot on error, don't crash)

### Step 4: Execution Engine (`server/services/execution_engine.py`)
- Orchestrate Docker + Agent lifecycle
- Session management (create, track, cleanup)
- Multi-step execution with context passing (previous step outputs)
- Error recovery (stop container on agent crash)

### Step 5: FastAPI Router (`server/routers/execution.py`)
- REST endpoints following `yt_ingestion.py` pattern
- WebSocket handler for real-time event streaming
- Register router in `__init__.py` and `main.py`

### Step 6: Dockerfile (`docker/computer-use/`)
- Write Dockerfile based on Ubuntu 22.04
- Install and configure Xvfb, Chromium, noVNC, websockify
- Write supervisord.conf for process management
- Test: `docker build -t autoforge-computer-use . && docker run -p 6080:6080 autoforge-computer-use`

### Step 7: Integration & Testing
- Wire everything together
- Test single-step execution end-to-end
- Test multi-step sequential execution
- Test pause/resume flow
- Test error handling (container crash, API error)
- Verify WebSocket events stream correctly

---

## Patterns to Follow

### FastAPI Router Pattern
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/execution", tags=["execution"])

class SomeRequest(BaseModel):
    field: str = Field(..., min_length=1)

@router.post("/endpoint", response_model=SomeResponse)
async def endpoint_name(request: SomeRequest) -> SomeResponse:
    """Docstring explaining the endpoint."""
    ...
```

### Service Class Pattern (from `process_manager.py`)
- Services are classes that manage state and lifecycle
- Use `logging.getLogger(__name__)` for all logging
- Sanitize output before streaming (use `sanitize_output()` from process_manager)
- Status is a `Literal` string union, not an enum
- Use `asyncio` for async operations
- Error handling: catch, log, emit event, continue

### WebSocket Event Pattern
```python
# Events follow this shape:
{
    "type": "status" | "screenshot" | "step_progress" | "agent_message" | "error",
    "session_id": "abc123",
    "data": {
        # varies by type
    }
}
```

### Environment Variable Pattern
```python
import os

COMPUTER_USE_ENABLED = os.getenv("COMPUTER_USE_ENABLED", "true").lower() == "true"
COMPUTER_USE_DOCKER_IMAGE = os.getenv("COMPUTER_USE_DOCKER_IMAGE", "anthropic/computer-use-reference:latest")
COMPUTER_USE_DISPLAY_WIDTH = int(os.getenv("COMPUTER_USE_DISPLAY_WIDTH", "1920"))
COMPUTER_USE_DISPLAY_HEIGHT = int(os.getenv("COMPUTER_USE_DISPLAY_HEIGHT", "1080"))
COMPUTER_USE_NOVNC_PORT = int(os.getenv("COMPUTER_USE_NOVNC_PORT", "6080"))
COMPUTER_USE_DEFAULT_MODEL = os.getenv("COMPUTER_USE_DEFAULT_MODEL", "claude-opus-4-6")
```

---

## Acceptance Criteria

1. **Single-step execution**: Agent can execute one strategy step end-to-end via the API — receives a prompt, operates in the browser, returns `aiOutput` and screenshots
2. **Multi-step execution**: Agent can execute a sequence of steps, passing context (previous outputs) between them
3. **Docker lifecycle**: Containers start reliably, noVNC is accessible, containers are cleaned up on stop
4. **Pause/resume**: Pausing waits for current tool call to complete, takes screenshot; resuming sends screenshot + context back to agent
5. **Message injection**: Human messages can be injected between tool calls and the agent responds to them
6. **WebSocket streaming**: All execution events (status changes, screenshots, agent messages, step progress) stream to connected clients in real-time
7. **Error handling**: Agent errors don't crash the engine; errors are captured, logged, and reported via WebSocket
8. **Health checks**: Container health is verified before starting the agent; unhealthy containers are reported
9. **API endpoints**: All REST endpoints return proper Pydantic responses with correct HTTP status codes
10. **Router registration**: Execution router is properly registered in `server/routers/__init__.py` and `server/main.py`

---

## Constraints & Rules

1. **No frontend code.** This agent builds backend only. The live viewer UI is Phase 5 (Wave 2).
2. **No SQLAlchemy models.** Session state lives in memory. Persistent storage for execution history is a future phase.
3. **No React Router.** Not relevant to this agent, but do not modify `ui/src/main.tsx` routing.
4. **Use existing `ANTHROPIC_API_KEY`.** Do not create a separate API key flow. Use the key already configured in AutoForge's `.env`.
5. **Default to Opus 4.6 for computer use.** Sonnet is acceptable for simpler steps. Never default to Haiku for computer use.
6. **Router prefix is `/api/execution`**, NOT `/api/yt-lab/execution`. Execution is a standalone system that future features (beyond YT Lab) can also use.
7. **Docker is optional at runtime.** If Docker is not installed, the engine should report `COMPUTER_USE_ENABLED=false` gracefully, not crash.
8. **Container cleanup is mandatory.** Every code path that starts a container must have a corresponding cleanup path. Use try/finally.
9. **Sanitize all output.** Follow the `sanitize_output()` pattern from `process_manager.py` to redact API keys and tokens before streaming.
10. **No hardcoded model names.** Use constants read from environment variables. Follow the `MODEL_OPTIONS` pattern.
11. **Log everything.** Use `logger.info()` for lifecycle events, `logger.error()` for failures, `logger.debug()` for tool call details.
12. **Python 3.11+ only.** Use modern syntax: `X | None` instead of `Optional[X]`, `list[str]` instead of `List[str]`.

---

## Integration Points (for Wave 2 Agents)

This agent's output will be consumed by:

- **Phase 5 (Live Execution Viewer)**: Reads WebSocket events at `/ws/execution/{session_id}`, embeds noVNC iframe using `ContainerInfo.novnc_url`
- **Phase 6 (Pause/Resume/Takeover)**: Calls `/api/execution/{session_id}/pause`, `/resume`, `/inject` REST endpoints
- **Phase 8 (Screen Recording)**: Attaches to the Docker container's X11 display for ffmpeg capture

Ensure your API contracts are clean and well-documented so downstream agents can integrate without ambiguity.

---

## Quick Reference: Key Types from Existing Codebase

```typescript
// From ui/src/lib/types.ts — what step data looks like
interface YTStrategyStep {
  id: string
  projectId: string
  order: number
  title: string
  description: string
  prompt: string           // ← This is what gets sent to the agent
  expectedOutput: string
  notes: string
  aiOutput: string         // ← Agent writes results here
  status: 'pending' | 'in_progress' | 'complete'
  model: string            // ← e.g., "claude-opus-4-6"
  subSteps: YTStrategySubStep[]
}
```

```python
# From PRD 09 — the computer-use tool definitions
tools = [
    {
        "type": "computer_20250124",
        "name": "computer",
        "display_width_px": 1920,
        "display_height_px": 1080,
        "display_number": 0,
    },
    {
        "type": "text_editor_20250124",
        "name": "str_replace_editor",
    },
    {
        "type": "bash_20250124",
        "name": "bash",
    }
]
```
