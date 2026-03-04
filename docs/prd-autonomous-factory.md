# Autonomous Factory Mode -- Product Requirements Document

## Document Info

| Field        | Value                            |
|--------------|----------------------------------|
| Author       | AutoForge Team                   |
| Status       | Draft                            |
| Created      | 2026-03-03                       |
| Last Updated | 2026-03-03                       |
| Target       | AutoForge v2.x                   |

---

## 1. Problem Statement

### The Human Bottleneck

Right now, AutoForge can build software autonomously -- but only in short sprints. An agent starts, fills its context window (~200K tokens), finishes what it can, and then **stops**. A human has to:

1. Notice the agent stopped
2. Figure out what was done vs. what's left
3. Start a new agent session with the right context
4. Wait for it, then repeat

This is like hiring a construction crew that builds one wall, packs up, and waits for you to come back and tell them to build the next one. The materials and blueprints are right there -- they just can't pick up where the last shift left off.

**The bigger problem:** Subscription rate limits. Claude's subscription gives you bursts of usage, then a 5-hour cooldown. Right now, when the limit hits, everything stops. Those 5 hours are wasted. A factory doesn't shut down because one shift ended -- the next shift clocks in.

### What We Want Instead

AutoForge should work like a **factory**: you give it the blueprints (a PRD), press start, and walk away. It breaks the work into shifts (phases), each agent works its shift, leaves notes for the next one (handoff), and the next agent picks up seamlessly. If a rate limit hits, it waits and resumes automatically. If something breaks, it takes a screenshot, checks the console errors, and fixes it -- just like a human developer would.

**In plain English:** You should be able to start a build before bed and wake up to a working app.

---

## 2. What Already Exists vs. What Needs to Be Built

### Already Built (we keep and build on these)

| Capability | Where It Lives | What It Does |
|---|---|---|
| Agent process management | `server/services/process_manager.py` | Start/stop/pause/resume agents, lock files, crash detection |
| WebSocket real-time updates | `server/routers/agent.py`, `useWebSocket.ts` | Live status and log streaming to the UI |
| Feature tracking in SQLite | `api/database.py`, `mcp_server/feature_mcp.py` | Features with status (pending/in_progress/passing/failing), dependencies |
| Rate limit detection | `rate_limit_utils.py` | Regex-based detection of 429 errors, exponential backoff |
| Agent session loop | `agent.py` | Auto-continue with delay, rate limit retry, error retry |
| Scheduler service | `server/services/scheduler_service.py` | APScheduler-based timed start/stop with crash recovery |
| Parallel orchestrator | `parallel_orchestrator.py` | Multiple agents with dependency-aware scheduling |
| Dev server manager | `server/services/dev_server_manager.py` | Start/stop dev servers, URL detection from output |
| Playwright MCP integration | `client.py` (lines 254-285) | Browser automation tools already available to agents |
| Multi-provider support | Settings UI, `registry.py` | Claude, Codex, Gemini, Ollama, custom providers |
| Workspace page | `ui/src/pages/WorkspacePage.tsx` | Three-panel split view, passoff editor, swarm panel |

### Needs to Be Built (the three new capabilities)

| Capability | What It Does | Priority |
|---|---|---|
| **Browser Preview Loop** | Agents can see their own UI output via screenshots, DOM reads, and console error checking | HIGH -- this is the "eyes" |
| **Handoff File Watcher** | AutoForge detects when an agent finishes and auto-starts the next one with context | HIGH -- this is the "relay baton" |
| **Phase Orchestration** | Break PRDs into context-window-sized phases and run them in sequence | MEDIUM -- enables multi-session builds |

---

## 3. Architecture Overview

```
                    +------------------------------------------+
                    |            AutoForge Server               |
                    |                                          |
  +--------+       |  +----------------+   +----------------+ |
  |  User   |------>  | Factory        |   | Phase          | |
  | Browser |  WS  |  | Controller     |   | Planner        | |
  |  (UI)   |<------|  | (new service)  |   | (new service)  | |
  +--------+       |  +-------+--------+   +-------+--------+ |
                    |          |                    |           |
                    |          v                    v           |
                    |  +-------+--------+   +------+--------+  |
                    |  | Process        |   | Handoff       |  |
                    |  | Manager        |   | Watcher       |  |
                    |  | (existing)     |   | (new service) |  |
                    |  +-------+--------+   +------+--------+  |
                    |          |                    |           |
                    +----------|--------------------|-----------+
                               |                    |
                    +----------|--------------------|-----------+
                    |          v                    v           |
                    |  +-------+--------+   +------+--------+  |
                    |  | Agent Process  |   | .autoforge/   |  |
                    |  | (Claude SDK)   |   | handoff.json  |  |
                    |  +-------+--------+   +---------------+  |
                    |          |                                |
                    |          v                                |
                    |  +-------+--------+                      |
                    |  | Playwright     |                      |
                    |  | Browser        |                      |
                    |  | (screenshots,  |                      |
                    |  |  DOM, console) |                      |
                    |  +----------------+                      |
                    |       Project Directory                   |
                    +------------------------------------------+
```

### Data Flow (One Full Factory Cycle)

```
1. User loads PRD into AutoForge
2. Phase Planner breaks PRD into phases (sized for context window)
3. Factory Controller starts Phase 1 agent
4. Agent builds code, uses Playwright to verify UI
5. Agent writes handoff.json when nearing context limit
6. Agent process exits
7. Handoff Watcher detects exit + handoff file
8. Factory Controller reads handoff, starts Phase 2 agent
9. Repeat until all phases complete (or rate limit -> queue + wait)
```

---

## 4. Detailed Specifications

### 4.1 Browser Preview Loop

**What it is:** The ability for an agent to see what it built -- take a screenshot of the running app, read the DOM tree, check console errors, and fix problems without human help.

**Why it matters:** Without this, agents are coding blind. They write HTML/CSS/React but never see the result. A human has to look at the screen and say "that button is in the wrong place." With the preview loop, the agent IS the human checking the screen.

#### 4.1.1 How It Works Today (Partial)

AutoForge already has Playwright MCP tools available to agents (defined in `client.py` lines 254-285):

```
mcp__playwright__browser_navigate
mcp__playwright__browser_take_screenshot
mcp__playwright__browser_snapshot (DOM accessibility tree)
mcp__playwright__browser_click
mcp__playwright__browser_evaluate (run JS in page)
mcp__playwright__browser_console_messages
mcp__playwright__browser_network_requests
... and more
```

The agent CAN use these tools. The problem is:

1. **No dev server management from the agent side.** The agent needs to start `npm run dev` (or equivalent) to have something to screenshot. Right now the dev server is managed separately by `DevServerProcessManager` and controlled from the UI.

2. **No structured preview-fix loop in the prompts.** The agent's coding prompt doesn't instruct it to: build -> start dev server -> screenshot -> check errors -> fix -> screenshot again.

3. **No connection between the dev server URL and the Playwright browser.** The agent doesn't know what URL to navigate to.

#### 4.1.2 What Needs to Change

**A. Dev Server Auto-Start via MCP Tool**

Add a new MCP tool `preview_start` to the feature MCP server (`mcp_server/feature_mcp.py`) that:

1. Reads the project's dev command from `.autoforge/devserver.json` (already stored by `project_config.py`)
2. Starts the dev server subprocess (reuse `DevServerProcessManager` logic)
3. Waits for the URL to be detected from output (up to 30 seconds)
4. Returns the URL to the agent

```python
# New MCP tool in feature_mcp.py
@mcp_tool
def preview_start() -> dict:
    """Start the project's dev server and return the URL.

    Returns:
        {"url": "http://localhost:3000", "status": "running"}
    """
```

Also add `preview_stop` and `preview_status` tools.

**B. Preview Loop Instructions in Coding Prompt**

Update the coding prompt template (`.claude/templates/coding_prompt.template.md`) to include a structured preview loop:

```markdown
## Visual Verification Protocol

After implementing a UI feature:
1. Call `preview_start` to ensure the dev server is running
2. Navigate Playwright to the dev server URL
3. Take a screenshot with `browser_take_screenshot`
4. Check for visual correctness against the feature spec
5. Read `browser_console_messages` for JavaScript errors
6. Read `browser_network_requests` for failed API calls
7. If errors found: fix the code, save, wait 2s for hot reload, re-screenshot
8. Repeat until the feature looks correct and has zero console errors

Skip the preview loop for:
- Backend-only features (APIs, database, CLI tools)
- Configuration changes
- Documentation
```

**C. Screenshot Storage for UI Display**

Store screenshots in `.autoforge/screenshots/` so the UI can display them:

```
.autoforge/screenshots/
  phase-1-feature-3-before.png
  phase-1-feature-3-after.png
  phase-2-feature-7-error.png
```

The UI can show these in the feature detail view as visual proof of completion.

#### 4.1.3 Technical Details

| Item | Detail |
|---|---|
| Browser engine | Playwright (already a dependency) |
| Default browser | Firefox (lower CPU, already configured) |
| Headless mode | Default on, configurable via settings |
| Screenshot format | PNG, stored in `.autoforge/screenshots/` |
| Max screenshot size | 1920x1080 (configurable) |
| Hot reload wait | 2 seconds after file save |
| Max retry loops | 5 (prevent infinite fix cycles) |

---

### 4.2 Handoff File Watcher

**What it is:** A system where AutoForge watches agent processes from the outside. When an agent finishes (process exits), AutoForge checks for a handoff file. If it exists, the next agent is automatically started with that context. The agent doesn't push a button -- it just writes a file and exits. AutoForge picks up the baton.

**Why "file watcher" and not "agent trigger"?** Because the agent is inside a sandbox. It can write files, but it shouldn't be able to start new agent processes. The control plane (AutoForge server) stays in charge. This is more reliable and more secure.

#### 4.2.1 The Handoff File

**Location:** `.autoforge/handoff.json`

**Written by:** The agent (via a new MCP tool)

**Read by:** The Factory Controller (server-side)

**Schema:**

```json
{
  "version": 1,
  "timestamp": "2026-03-03T22:15:00Z",
  "phase": {
    "current": 2,
    "total": 5,
    "name": "Core API Implementation"
  },
  "completed": {
    "summary": "Implemented user auth endpoints and database models",
    "features_completed": [1, 2, 3],
    "files_created": [
      "src/api/auth.py",
      "src/models/user.py",
      "src/middleware/jwt.py"
    ],
    "files_modified": [
      "src/app.py",
      "package.json"
    ]
  },
  "next_phase": {
    "summary": "Build the dashboard UI components",
    "priority_tasks": [
      "Create Dashboard layout component",
      "Implement data visualization charts",
      "Connect to API endpoints from Phase 2"
    ],
    "feature_ids_to_work": [4, 5, 6],
    "notes": "Auth middleware is ready -- dashboard routes should use it"
  },
  "current_bugs": [
    {
      "file": "src/api/auth.py",
      "line": 45,
      "description": "Token refresh endpoint returns 500 when token is expired (edge case)",
      "severity": "low"
    }
  ],
  "dev_server": {
    "command": "npm run dev",
    "url": "http://localhost:3000",
    "status": "was_running"
  },
  "context_usage": {
    "estimated_percent": 42,
    "turns_used": 127,
    "reason": "approaching_budget"
  },
  "git": {
    "last_commit": "a1b2c3d",
    "branch": "main",
    "uncommitted_changes": false
  }
}
```

#### 4.2.2 How the Watcher Works

The Handoff Watcher is a new service (`server/services/handoff_watcher.py`) that:

1. **Registers a callback** on the `AgentProcessManager` status change event
2. **When status changes to "stopped" or "crashed"**, it checks for `.autoforge/handoff.json`
3. **If handoff file exists:**
   - Validates the JSON schema
   - Moves the file to `.autoforge/handoff_history/handoff-{timestamp}.json` (archive)
   - Passes the handoff data to the Factory Controller
   - Factory Controller decides what to do next (start next phase, wait for rate limit, etc.)
4. **If no handoff file:** The agent finished without requesting continuation. Log it and stop.

```
Agent Process
    |
    |  (writes handoff.json)
    |  (exits)
    v
Process Manager
    |
    |  status -> "stopped"
    v
Handoff Watcher (callback)
    |
    |  checks .autoforge/handoff.json
    |  validates + archives
    v
Factory Controller
    |
    |  reads handoff data
    |  decides: start next? wait? done?
    v
Process Manager.start()
    |
    |  new agent with handoff context
    v
New Agent Process
```

#### 4.2.3 The Handoff MCP Tool

Add to `mcp_server/feature_mcp.py`:

```python
@mcp_tool
def factory_write_handoff(handoff_data: dict) -> dict:
    """Write a handoff file for the next agent session.

    Call this when you are approaching your context budget (>40%)
    or when you have completed all assigned work for this phase.

    The handoff file tells AutoForge what you accomplished, what's
    left to do, and any issues the next agent should know about.

    Args:
        handoff_data: Dictionary with completed work, next tasks,
                      bugs, and context usage info

    Returns:
        {"status": "written", "path": ".autoforge/handoff.json"}
    """
```

#### 4.2.4 Handoff Prompt Injection

When a new agent starts from a handoff, its prompt includes the handoff context:

```markdown
## Continuation Context (from previous agent session)

You are continuing work from a previous agent session. Here is what was
accomplished and what needs to be done next:

### What Was Completed
{handoff.completed.summary}

Features completed: {handoff.completed.features_completed}
Files created: {handoff.completed.files_created}

### Your Assignment for This Session
{handoff.next_phase.summary}

Priority tasks:
{handoff.next_phase.priority_tasks}

### Known Issues to Be Aware Of
{handoff.current_bugs}

### Important Notes
{handoff.next_phase.notes}
```

---

### 4.3 Phase Orchestration

**What it is:** A system that breaks a PRD into phases sized for the agent's context window, then runs them in sequence. Each phase is a chunk of work one agent can complete in one session.

**Why phases?** A full application might need 500K tokens of context to build. An agent session has ~200K tokens. You can't build the whole thing in one shot. Phases let you divide the work into digestible pieces.

#### 4.3.1 Phase Sizing

The target is **~50% of the context window** per phase (~100K tokens on a 200K model). Why 50% and not higher?

- The agent needs room for tool calls, file reads, and error fixing
- AutoForge's existing budget system targets 45% with a hard stop at 48%
- Leaving headroom prevents the agent from being cut off mid-implementation

**Sizing heuristics:**

| Work Type | Approximate Token Cost | Notes |
|---|---|---|
| Read existing file | ~1 token per character | Large files eat budget fast |
| Write new file | ~2 tokens per character | Agent generates + writes |
| Tool call overhead | ~500 tokens each | Includes the MCP protocol framing |
| Screenshot analysis | ~1,500 tokens each | Image encoding in the context |
| Error fix cycle | ~3,000 tokens per cycle | Read error + analyze + fix + verify |

**Rule of thumb:** 3-5 features per phase for a typical web app. Fewer for complex features, more for simple ones.

#### 4.3.2 The Phase Plan

The Phase Planner is a new service (`server/services/phase_planner.py`) that takes a list of features (from `features.db`) and groups them into phases:

```json
{
  "version": 1,
  "project_name": "my-app",
  "total_phases": 4,
  "phases": [
    {
      "number": 1,
      "name": "Foundation & Setup",
      "status": "completed",
      "features": [1, 2, 3],
      "description": "Project scaffolding, database setup, base layout",
      "estimated_tokens": 85000,
      "started_at": "2026-03-03T20:00:00Z",
      "completed_at": "2026-03-03T20:45:00Z"
    },
    {
      "number": 2,
      "name": "Core API",
      "status": "running",
      "features": [4, 5, 6, 7],
      "description": "Authentication, CRUD endpoints, middleware",
      "estimated_tokens": 95000,
      "context_used_percent": 34,
      "started_at": "2026-03-03T20:48:00Z"
    },
    {
      "number": 3,
      "name": "Dashboard UI",
      "status": "queued",
      "features": [8, 9, 10],
      "description": "Dashboard layout, charts, data tables",
      "estimated_tokens": 90000
    },
    {
      "number": 4,
      "name": "Polish & Testing",
      "status": "queued",
      "features": [11, 12],
      "description": "Error handling, responsive design, E2E tests",
      "estimated_tokens": 70000
    }
  ]
}
```

**Storage:** `.autoforge/phase_plan.json`

#### 4.3.3 Auto-Phase Generation

When factory mode is enabled, AutoForge can auto-generate phases from the feature list:

1. **Group by dependency chains.** Features that depend on each other go in the same phase (if they fit) or in sequential phases.
2. **Respect the dependency graph.** A feature can't be in Phase 2 if its dependency is in Phase 3.
3. **Balance phase sizes.** Try to keep each phase at 60-80% of the budget target (leaving room for error fixing).
4. **Foundation first.** Setup, scaffolding, and database features always go in Phase 1.

The auto-grouping uses the existing dependency resolver (`api/dependency_resolver.py`) which already has topological sorting via Kahn's algorithm.

#### 4.3.4 Phase Transitions

```
Phase 1 (completed)
    |
    | handoff.json written
    | agent exits
    v
    [Handoff Watcher detects completion]
    |
    | Is rate limit active?
    |---- YES --> Queue Phase 2, start countdown timer
    |              |
    |              | (5-hour cooldown expires)
    |              v
    |              Auto-start Phase 2
    |
    |---- NO  --> Start Phase 2 immediately (3-second delay)
    v
Phase 2 (running)
    |
    ...continues...
```

---

## 5. API Design (New Endpoints)

### 5.1 Factory Control Endpoints

```
POST   /api/projects/{name}/factory/start
  Body: {
    "mode": "continuous",        // "continuous" (run all phases) or "single" (one phase)
    "start_phase": 1,            // Which phase to start from (default: next incomplete)
    "model": "claude-opus-4-6",  // Model to use
    "yolo_mode": false,          // Skip testing
    "auto_commit": true,         // Git commit after each phase
    "rate_limit_strategy": "wait" // "wait" (auto-resume) or "stop" (manual resume)
  }
  Response: { "status": "started", "current_phase": 1, "total_phases": 4 }

POST   /api/projects/{name}/factory/stop
  Response: { "status": "stopped", "phase_completed": 2, "phase_total": 4 }

POST   /api/projects/{name}/factory/pause
  Response: { "status": "paused", "current_phase": 2, "context_used": 34 }

POST   /api/projects/{name}/factory/resume
  Response: { "status": "running", "current_phase": 2 }

GET    /api/projects/{name}/factory/status
  Response: {
    "mode": "continuous",
    "status": "running",           // running, paused, stopped, waiting_rate_limit, completed
    "current_phase": 2,
    "total_phases": 4,
    "phases": [ ... ],             // Full phase plan with status
    "rate_limit": {
      "active": false,
      "resumes_at": null
    },
    "started_at": "2026-03-03T20:00:00Z",
    "features_completed": 7,
    "features_total": 12
  }
```

### 5.2 Phase Management Endpoints

```
GET    /api/projects/{name}/phases
  Response: { "phases": [ ... ] }  // Full phase plan

POST   /api/projects/{name}/phases/generate
  Body: { "max_features_per_phase": 5, "target_budget_percent": 50 }
  Response: { "phases": [ ... ] }  // Generated phase plan

PUT    /api/projects/{name}/phases/{number}
  Body: { "features": [4, 5, 6], "name": "Updated name" }
  Response: { "phase": { ... } }   // Updated phase

POST   /api/projects/{name}/phases/{number}/retry
  Response: { "status": "retrying", "phase": 2 }  // Restart a failed phase
```

### 5.3 Handoff Endpoints

```
GET    /api/projects/{name}/handoffs
  Response: { "handoffs": [ ... ] }  // Archived handoff history

GET    /api/projects/{name}/handoffs/{timestamp}
  Response: { ... }                   // Specific handoff details
```

### 5.4 Preview Endpoints

```
GET    /api/projects/{name}/preview/screenshots
  Response: { "screenshots": ["phase-1-feature-3-after.png", ...] }

GET    /api/projects/{name}/preview/screenshots/{filename}
  Response: (binary PNG image)

GET    /api/projects/{name}/preview/status
  Response: { "dev_server": "running", "url": "http://localhost:3000" }
```

### 5.5 WebSocket Events (New)

Added to the existing WebSocket at `/ws/projects/{project_name}`:

```json
// Phase transition
{
  "type": "phase_update",
  "phase": 2,
  "status": "running",
  "total_phases": 4,
  "features_in_phase": [4, 5, 6, 7]
}

// Rate limit detected -- factory is waiting
{
  "type": "rate_limit_wait",
  "resumes_at": "2026-03-04T03:15:00Z",
  "cooldown_seconds": 18000,
  "queued_phase": 3
}

// Handoff detected
{
  "type": "handoff_detected",
  "from_phase": 1,
  "to_phase": 2,
  "summary": "Foundation complete, starting Core API"
}

// Screenshot captured
{
  "type": "screenshot_captured",
  "filename": "phase-2-feature-5-after.png",
  "feature_id": 5,
  "phase": 2
}

// Factory completed all phases
{
  "type": "factory_complete",
  "total_phases": 4,
  "total_features": 12,
  "duration_minutes": 180
}
```

---

## 6. UI Changes

### 6.1 Phase 1 MVP: Factory Toggle on Existing Page

Add to the existing project page (where the Start Agent button is):

```
+----------------------------------------------------------+
|  [Start Agent]  [Factory Mode: OFF -->]  [Settings gear]  |
+----------------------------------------------------------+
```

When Factory Mode is ON, the Start Agent button changes:

```
+----------------------------------------------------------+
|  [Start Factory]  [Factory Mode: ON <--]  [Settings gear] |
+----------------------------------------------------------+
```

Below the feature board, add a Phase Pipeline strip:

```
+----------------------------------------------------------+
|  FACTORY PIPELINE                                         |
|                                                           |
|  [Phase 1: Setup]  -->  [Phase 2: API]  -->  [Phase 3]   |
|   DONE (12 min)          RUNNING (34%)        QUEUED      |
|   3/3 features           2/4 features         0/3        |
|                                                           |
|  Rate limit: None  |  Next cooldown: ~2h from now         |
+----------------------------------------------------------+
```

### 6.2 Phase 2 Polish: Enhanced Pipeline View

Replace the strip with a richer timeline view:

```
+----------------------------------------------------------+
|  FACTORY PIPELINE                                 [Stop]  |
|                                                           |
|  Phase 1          Phase 2          Phase 3      Phase 4   |
|  +-----------+    +-----------+    +---------+  +-------+ |
|  | Setup     |    | Core API  |    | Dash UI |  | Polish| |
|  | 3/3 done  |--->| 2/4 done  |--->| queued  |->| queued| |
|  | 12 min    |    | 34% ctx   |    | 3 feat  |  | 2 feat| |
|  +-----------+    +-----------+    +---------+  +-------+ |
|       [done]         [running]                            |
|                                                           |
|  [Handoff Log]  |  [Screenshots]  |  [Phase Editor]       |
+----------------------------------------------------------+
```

### 6.3 Phase 3: Dedicated Factory Page

A full page at `/#/factory` with:

- **Left panel:** Phase list with drag-to-reorder
- **Center panel:** Live agent output (current phase)
- **Right panel:** Handoff history, screenshots, timeline
- **Top bar:** Factory controls (start/stop/pause), rate limit countdown, progress

This page can be built BY the factory itself (meta!) -- use AutoForge's factory mode to build the factory page as one of its phases.

---

## 7. Data Model

### 7.1 New Files in `.autoforge/`

```
.autoforge/
  handoff.json                    # Current handoff (written by agent, read by watcher)
  handoff_history/                # Archived handoffs
    handoff-2026-03-03T200000Z.json
    handoff-2026-03-03T204500Z.json
  phase_plan.json                 # Phase plan (generated or manual)
  factory_state.json              # Factory controller state (survives server restart)
  screenshots/                    # Agent-captured screenshots
    phase-1-feature-3-before.png
    phase-1-feature-3-after.png
```

### 7.2 Factory State File

```json
{
  "version": 1,
  "mode": "continuous",
  "status": "running",
  "current_phase": 2,
  "started_at": "2026-03-03T20:00:00Z",
  "model": "claude-opus-4-6",
  "yolo_mode": false,
  "auto_commit": true,
  "rate_limit_strategy": "wait",
  "rate_limit": {
    "active": false,
    "detected_at": null,
    "resumes_at": null,
    "queued_phase": null
  },
  "history": [
    {
      "phase": 1,
      "status": "completed",
      "started_at": "2026-03-03T20:00:00Z",
      "completed_at": "2026-03-03T20:12:00Z",
      "agent_pid": 12345,
      "features_completed": [1, 2, 3],
      "handoff_file": "handoff-2026-03-03T201200Z.json"
    }
  ]
}
```

### 7.3 Database Changes

No changes to the existing `features.db` schema. Phase information is stored in JSON files, not the database. This keeps the existing feature tracking system untouched and avoids migration complexity.

The phase plan references feature IDs from the existing database. This is a **read-only relationship** -- phases point to features, but features don't know about phases.

---

## 8. New Backend Services

### 8.1 Factory Controller (`server/services/factory_controller.py`)

The brain of factory mode. Responsibilities:

- Manage the factory lifecycle (start/stop/pause/resume)
- Coordinate phase transitions
- Handle rate limit queuing
- Persist state to `factory_state.json`
- Emit WebSocket events for the UI
- Interface with `AgentProcessManager` for process control

```python
class FactoryController:
    """Orchestrates multi-phase autonomous builds."""

    def __init__(self, project_name: str, project_dir: Path):
        self.project_name = project_name
        self.project_dir = project_dir
        self.state = FactoryState.load(project_dir)

    async def start(self, config: FactoryConfig) -> tuple[bool, str]:
        """Start factory mode for the project."""
        # 1. Load or generate phase plan
        # 2. Find the first incomplete phase
        # 3. Build the prompt with phase context + any handoff data
        # 4. Start the agent via ProcessManager
        # 5. Register handoff watcher callback
        # 6. Persist state

    async def on_agent_exit(self, exit_code: int):
        """Called when the current agent process exits."""
        # 1. Check for handoff file
        # 2. Archive handoff if found
        # 3. Update phase status
        # 4. Check for rate limit indicators
        # 5. Start next phase or queue for rate limit

    async def on_rate_limit_expired(self):
        """Called when rate limit cooldown finishes."""
        # 1. Start the queued phase

    async def stop(self):
        """Stop factory mode, preserving progress."""
        # 1. Stop current agent
        # 2. Save state
        # 3. Clean up watchers
```

### 8.2 Handoff Watcher (`server/services/handoff_watcher.py`)

Monitors agent process completion and triggers handoffs.

```python
class HandoffWatcher:
    """Watches for agent completion and handoff files."""

    def __init__(self, project_dir: Path, on_handoff: Callable):
        self.project_dir = project_dir
        self.on_handoff = on_handoff
        self.handoff_path = project_dir / ".autoforge" / "handoff.json"

    async def check_for_handoff(self) -> Optional[dict]:
        """Check for handoff file, validate, and archive."""
        if not self.handoff_path.exists():
            return None

        data = json.loads(self.handoff_path.read_text())
        self._validate_schema(data)
        self._archive(data)
        self.handoff_path.unlink()
        return data

    def _validate_schema(self, data: dict):
        """Validate handoff file has required fields."""
        required = ["version", "timestamp", "completed", "next_phase"]
        for field in required:
            if field not in data:
                raise ValueError(f"Handoff file missing required field: {field}")

    def _archive(self, data: dict):
        """Move handoff to history directory."""
        history_dir = self.project_dir / ".autoforge" / "handoff_history"
        history_dir.mkdir(exist_ok=True)
        timestamp = data["timestamp"].replace(":", "")
        archive_path = history_dir / f"handoff-{timestamp}.json"
        archive_path.write_text(json.dumps(data, indent=2))
```

### 8.3 Phase Planner (`server/services/phase_planner.py`)

Generates and manages phase plans.

```python
class PhasePlanner:
    """Generates phase plans from feature lists."""

    def generate_phases(
        self,
        project_dir: Path,
        max_features_per_phase: int = 5,
        target_budget_percent: int = 50,
    ) -> list[Phase]:
        """Auto-generate phases from the feature dependency graph."""
        # 1. Load features from database
        # 2. Topological sort using dependency_resolver
        # 3. Group into phases respecting dependencies
        # 4. Balance phase sizes
        # 5. Assign foundation features to Phase 1
        return phases
```

---

## 9. New MCP Tools (Agent-Side)

Added to `mcp_server/feature_mcp.py`:

| Tool | Description | Used For |
|---|---|---|
| `factory_write_handoff` | Write the handoff file with completion data and next-phase instructions | Phase transitions |
| `factory_get_phase` | Read the current phase assignment (which features to work on) | Agent knows its scope |
| `factory_get_handoff_context` | Read the previous agent's handoff data (injected in prompt too) | Understanding prior work |
| `preview_start` | Start the dev server, return URL | Browser preview loop |
| `preview_stop` | Stop the dev server | Cleanup |
| `preview_status` | Check if dev server is running and get URL | Before taking screenshots |
| `preview_save_screenshot` | Save a screenshot to `.autoforge/screenshots/` with a descriptive name | Visual record of progress |

---

## 10. Prompt Changes

### 10.1 Factory-Aware Coding Prompt Additions

Append to the existing coding prompt template when factory mode is active:

```markdown
## Factory Mode -- IMPORTANT

You are running in Factory Mode. This means:

1. **Context Budget:** You MUST stay under 45% context usage. When you reach
   ~40%, start wrapping up and write a handoff.

2. **Handoff Required:** Before your session ends, call `factory_write_handoff`
   with:
   - What you completed (features, files created/modified)
   - What the next agent should do
   - Any bugs or issues you found but didn't fix
   - Your context usage estimate

3. **Phase Scope:** You are working on Phase {N} of {total}. Your assigned
   features are: {feature_list}. Focus ONLY on these features.

4. **Visual Verification:** For UI features, use the preview loop:
   - `preview_start` to get the dev server URL
   - Navigate and screenshot with Playwright
   - Fix any visual issues or console errors
   - `preview_save_screenshot` to record your work

5. **Git:** Commit your work before writing the handoff. Use descriptive
   commit messages that reference the phase number.

6. **Do NOT:**
   - Work on features outside your phase scope
   - Spend time on premature optimization
   - Refactor code from previous phases (unless it blocks your work)
   - Leave the dev server running (call `preview_stop` when done)
```

### 10.2 Continuation Prompt (When Starting from Handoff)

```markdown
## Continuation from Previous Session

A previous agent completed Phase {N-1} and left the following handoff:

### Completed Work
{handoff.completed.summary}

Features done: {comma-separated list}

### Your Assignment (Phase {N})
{handoff.next_phase.summary}

Priority tasks:
{numbered list of tasks}

### Known Issues
{list of bugs/issues from handoff}

### Notes from Previous Agent
{handoff.next_phase.notes}

---

Start by reading the files mentioned above to understand what was built.
Then proceed with your assigned features.
```

---

## 11. Rate Limit Handling

### 11.1 Detection

AutoForge already detects rate limits in two places:

1. **`rate_limit_utils.py`**: Regex patterns matching "rate limit", "429", "too many requests", etc.
2. **`agent.py`**: Catches rate limit errors and extracts retry-after times.

For factory mode, rate limit detection also happens in the agent's output stream (`_stream_output` in `process_manager.py`). When a rate limit pattern is detected, the Factory Controller is notified.

### 11.2 Strategy: Wait and Resume

When a rate limit hits during factory mode:

```
1. Agent process exits (or gets stuck in retry loop)
2. Factory Controller detects rate limit from agent output or exit
3. Factory Controller:
   a. Saves current factory state
   b. Sets rate_limit.active = true
   c. Calculates resumes_at (5 hours from now, or from retry-after header)
   d. Emits "rate_limit_wait" WebSocket event
   e. Starts a timer
4. Timer fires at resumes_at:
   a. Sets rate_limit.active = false
   b. Starts the next phase (or retries current phase if incomplete)
   c. Emits "phase_update" WebSocket event
```

### 11.3 UI During Rate Limit

```
+----------------------------------------------------------+
|  FACTORY: WAITING FOR RATE LIMIT RESET                    |
|                                                           |
|  [====================>           ] 60% elapsed           |
|  Resumes at: 3:15 AM (4h 12m remaining)                  |
|                                                           |
|  Phase 2 completed | Phase 3 queued (3 features)          |
|                                                           |
|  [Resume Now]  [Stop Factory]                             |
+----------------------------------------------------------+
```

### 11.4 24/7 Operation Model

For subscription users who want continuous building:

```
Day 1, 8:00 PM:  Start factory, Phases 1-2 complete
Day 1, 9:30 PM:  Rate limit hit, queue Phase 3
Day 2, 2:30 AM:  Rate limit resets, Phase 3 auto-starts
Day 2, 3:15 AM:  Phase 3 complete, Phase 4 starts
Day 2, 4:00 AM:  Rate limit hit, queue Phase 5
Day 2, 9:00 AM:  Rate limit resets, Phase 5 auto-starts
Day 2, 9:45 AM:  ALL PHASES COMPLETE -- factory stops
```

The user slept through Phases 3-5. Woke up to a finished app.

---

## 12. Git Integration

### 12.1 Auto-Commit After Each Phase

When `auto_commit` is enabled in factory config:

```python
# After agent writes handoff and before starting next phase:
async def auto_commit_phase(project_dir: Path, phase: int):
    """Commit all changes from the completed phase."""
    subprocess.run(["git", "add", "-A"], cwd=project_dir)
    subprocess.run(
        ["git", "commit", "-m", f"factory: complete phase {phase}"],
        cwd=project_dir,
    )
```

### 12.2 Auto-Push (Optional)

If configured, push after each commit:

```python
if auto_push:
    subprocess.run(["git", "push", "origin", branch], cwd=project_dir)
```

### 12.3 Git Conflict Handling

If a push fails due to conflicts (someone else pushed):

1. Factory Controller pauses
2. Emits `git_conflict` WebSocket event
3. UI shows: "Git conflict detected. Please resolve manually and resume."
4. User resolves, clicks Resume
5. Factory continues from the current phase

---

## 13. Edge Cases and Error Handling

### 13.1 Agent Crash

| Scenario | Handling |
|---|---|
| Agent crashes without writing handoff | Retry current phase (up to 3 times, with exponential backoff). Uses existing `handle_crash_during_window` pattern from scheduler. |
| Agent writes partial handoff then crashes | Validate handoff schema. If invalid, treat as no handoff (retry phase). |
| Agent infinite loops (never exits) | Factory Controller monitors context budget via agent output. Force-stop after 48% context usage + 5 minute grace period. |

### 13.2 Rate Limit Edge Cases

| Scenario | Handling |
|---|---|
| Rate limit during Phase 1 (nothing completed yet) | Save partial progress via features.db. Retry Phase 1 when limit resets. |
| Rate limit with unknown retry-after | Default to 5 hours (Claude subscription pattern). |
| Multiple rate limits in quick succession | Exponential backoff: 5h, 10h, 15h. Cap at 24h. Alert user after 3rd limit. |
| Rate limit on a different provider (Gemini/Codex) | Each provider has different limits. Factory Controller uses provider-specific defaults. |

### 13.3 Corrupted Files

| Scenario | Handling |
|---|---|
| `handoff.json` is invalid JSON | Log error, archive the broken file, retry phase without handoff context. |
| `phase_plan.json` is corrupted | Regenerate from features.db. Phase progress is stored in `factory_state.json`, not the plan. |
| `factory_state.json` is corrupted | Reset factory state. User loses phase progress but features.db is authoritative. |
| Agent modifies `phase_plan.json` directly | File is outside the MCP tool contract. Validate on read, reject unexpected changes. |

### 13.4 Dev Server Issues

| Scenario | Handling |
|---|---|
| Dev server won't start | Agent logs error, skips visual verification, marks feature with note. |
| Dev server crashes during preview loop | Agent catches error, restarts dev server, retries screenshot. Max 3 retries. |
| Dev server port conflict | Use the next available port. Update URL in handoff data. |
| Hot reload doesn't work | Agent waits longer (5s instead of 2s), then restarts dev server if needed. |

### 13.5 Server Restart Recovery

If the AutoForge server restarts while factory mode is active:

1. On startup, check all registered projects for `factory_state.json`
2. If found with `status: "running"`:
   - Check if agent process is still alive (via lock file)
   - If alive: re-attach to process
   - If dead: treat as crash, retry current phase
3. If found with `status: "waiting_rate_limit"`:
   - Re-create the rate limit timer with remaining time
   - Continue waiting

This mirrors the existing pattern in `scheduler_service.py` (`_check_missed_windows_on_startup`).

---

## 14. Implementation Plan

### Phase 1: MVP (Target: Tonight)

**Goal:** Get a working handoff + auto-restart loop. No UI changes -- just the backend wiring.

**Scope:**
1. `server/services/handoff_watcher.py` -- Watch for agent exit + handoff file (~100 lines)
2. `server/services/factory_controller.py` -- Minimal version: start, handle handoff, restart (~200 lines)
3. `mcp_server/feature_mcp.py` -- Add `factory_write_handoff` MCP tool (~50 lines)
4. Update coding prompt template to include factory mode instructions (~30 lines)
5. New API endpoints: `POST factory/start`, `POST factory/stop`, `GET factory/status` (~100 lines)
6. Wire handoff watcher into process manager's status callbacks (~20 lines)

**Total:** ~500 lines of new code

**What it enables:** Start an agent, it writes a handoff when done, AutoForge reads the handoff and starts the next agent automatically. No UI needed -- just API calls.

**Testing:** Start a test project, enable factory mode via API call, watch the agent cycle through phases in the terminal output.

### Phase 2: Browser Preview + UI (Target: This Week)

**Goal:** Agents can see their UI output. Factory progress visible in the browser.

**Scope:**
1. `mcp_server/feature_mcp.py` -- Add `preview_start`, `preview_stop`, `preview_status` tools (~100 lines)
2. Update coding prompt with visual verification protocol (~50 lines)
3. Screenshot storage and API endpoints (~80 lines)
4. Factory Mode toggle in project page UI (~100 lines React)
5. Phase pipeline strip component (~150 lines React)
6. WebSocket events for phase transitions (~50 lines)

**Total:** ~530 lines of new code

### Phase 3: Phase Planner + Full UI (Target: Next Week)

**Goal:** Auto-generate phases from features. Dedicated factory page.

**Scope:**
1. `server/services/phase_planner.py` -- Auto-phase generation from dependency graph (~200 lines)
2. Phase management API endpoints (~100 lines)
3. Rate limit countdown timer with auto-resume (~100 lines)
4. Dedicated `/#/factory` page with full pipeline view (~500 lines React)
5. Handoff history viewer (~150 lines React)
6. Screenshot gallery in feature detail view (~100 lines React)

**Total:** ~1,150 lines of new code

### Phase 4: Polish and Advanced Features (Target: Following Week)

**Goal:** Production-ready factory mode.

**Scope:**
1. Server restart recovery (factory state persistence) (~100 lines)
2. Git auto-commit and push integration (~80 lines)
3. Multi-provider rate limit handling (different limits for Claude/Gemini/Codex) (~100 lines)
4. Factory analytics (time per phase, tokens per feature, error rates) (~200 lines)
5. Phase drag-to-reorder in UI (~100 lines React)
6. Factory mode for the Workspace page's split-view workflow (~150 lines React)

**Total:** ~730 lines of new code

---

## 15. File Inventory (New Files to Create)

```
server/services/
  factory_controller.py      # Factory mode orchestration (brain)
  handoff_watcher.py          # Watches for agent exit + handoff file
  phase_planner.py            # Generates phase plans from features

server/routers/
  factory.py                  # REST API endpoints for factory control

mcp_server/
  feature_mcp.py              # MODIFY: add handoff + preview MCP tools

ui/src/components/factory/
  FactoryToggle.tsx           # On/off switch for factory mode
  PhasePipeline.tsx           # Pipeline visualization strip
  PhaseCard.tsx               # Individual phase card in pipeline
  RateLimitCountdown.tsx      # Countdown timer during rate limit wait
  HandoffHistory.tsx          # List of archived handoffs
  ScreenshotGallery.tsx       # Grid of agent-captured screenshots

ui/src/pages/
  FactoryPage.tsx             # Dedicated factory page (Phase 3)

ui/src/hooks/
  useFactory.ts               # React Query hooks for factory API

.claude/templates/
  coding_prompt.template.md   # MODIFY: add factory mode instructions
  factory_continuation.md     # New: prompt for handoff-based continuation
```

---

## 16. Configuration

### 16.1 Settings UI Additions

Add to the existing Settings modal (`SettingsModal.tsx`):

```
Factory Mode
  [x] Enable factory mode (continuous autonomous builds)
  [ ] Auto-commit after each phase
  [ ] Auto-push to remote
  Rate limit strategy: [Wait and Resume v]
  Max phases per run: [Unlimited v]
  Target budget per phase: [50%]
```

### 16.2 Environment Variables (Optional)

```bash
# In ~/.autoforge/.env
FACTORY_AUTO_COMMIT=true
FACTORY_AUTO_PUSH=false
FACTORY_RATE_LIMIT_WAIT=18000    # 5 hours in seconds
FACTORY_MAX_PHASE_RETRIES=3
FACTORY_PHASE_BUDGET_PERCENT=50
```

---

## 17. Security Considerations

1. **Handoff file validation.** The handoff file is written by the agent inside its sandbox. The Factory Controller validates the schema before acting on it. Unknown fields are ignored. File paths in the handoff are not used for file operations -- they're informational only.

2. **Phase plan integrity.** The phase plan references feature IDs. The Factory Controller verifies that referenced feature IDs exist in `features.db` before starting a phase.

3. **Dev server isolation.** The dev server started by the preview MCP tool runs in the project directory, not the AutoForge directory. It's killed when the agent exits.

4. **Git operations.** Auto-commit and auto-push use the same git commands already in the security allowlist. No new permissions needed.

5. **Process limits.** Factory mode runs one agent at a time per project (not parallel). The existing lock file mechanism prevents double-starts. Parallel mode within a phase uses the existing `MAX_PARALLEL_AGENTS = 5` limit.

---

## 18. Success Metrics

| Metric | Target | How to Measure |
|---|---|---|
| Hands-off build time | 4+ hours without human intervention | Log factory run duration between first start and completion/stop |
| Phase transition success rate | >90% of handoffs result in successful next-phase starts | Count successful vs failed transitions |
| Preview loop error detection | Agent catches >80% of visual bugs before human sees them | Compare agent-found bugs vs human-found bugs |
| Rate limit recovery | 100% of rate limit waits result in auto-resume | Count auto-resumes vs manual interventions |
| Build completion rate | >70% of factory runs complete all phases | Count completed vs abandoned factory runs |

---

## 19. Glossary

| Term | Definition |
|---|---|
| **Factory Mode** | The continuous autonomous build system described in this document |
| **Phase** | A chunk of work sized to fit within one agent's context window (~100K tokens) |
| **Handoff** | A JSON file written by an agent containing what it did and what comes next |
| **Handoff Watcher** | Server-side service that detects agent completion and reads handoff files |
| **Factory Controller** | Server-side service that orchestrates the full factory lifecycle |
| **Phase Planner** | Service that generates phase plans from feature dependency graphs |
| **Preview Loop** | The cycle of: build code -> screenshot -> check errors -> fix -> screenshot |
| **Rate Limit Queue** | When a rate limit is hit, the next phase is queued and a timer set |
| **Context Budget** | The percentage of the agent's context window used (target: 45%, hard stop: 48%) |

---

## 20. Open Questions

1. **Should the agent or AutoForge decide when to handoff?** Current design: the agent writes the handoff when it approaches the context budget. Alternative: AutoForge monitors context usage and force-stops the agent. The agent-driven approach is simpler and more reliable (the agent knows what it's in the middle of).

2. **How to handle multi-provider factory runs?** If Claude hits a rate limit, should the factory try Gemini or Codex for the next phase? This would require provider-switching logic and prompt translation. Defer to Phase 4.

3. **Should phases be editable while the factory is running?** Allowing live phase editing adds complexity but gives users control. Start with "stop factory, edit, restart" and add live editing in Phase 3 if needed.

4. **Screenshot storage limits.** A long factory run could generate hundreds of screenshots. Add a retention policy (keep last 50 per project, or last 7 days) in Phase 4.

5. **What if the PRD changes mid-build?** If the user adds features or modifies the spec while the factory is running, should the phase plan auto-update? Start with "no" -- the user must stop and restart. Add incremental replanning in Phase 4.
