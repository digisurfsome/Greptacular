# DunkStack File-Based Agent System - Implementation Plan

> **Status**: Draft v1.0
> **Created**: 2026-02-25
> **Author**: Planning Agent
> **Audience**: Implementation agents (Claude Code sessions)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Critical Rules](#critical-rules)
4. [Phase 1: DunkStack Agent Session](#phase-1-dunkstack-agent-session)
5. [Phase 2: DunkStack Dependency System](#phase-2-dunkstack-dependency-system)
6. [Phase 3: DunkStack Router Enhancements](#phase-3-dunkstack-router-enhancements)
7. [Phase 4: UI Wiring](#phase-4-ui-wiring)
8. [Cross-Cutting Concerns](#cross-cutting-concerns)
9. [Testing Strategy](#testing-strategy)
10. [File Inventory](#file-inventory)

---

## Executive Summary

DunkStack is a file-based agent architecture for AutoForge's App Builder feature. Unlike the existing Workspace chat system (which uses in-memory queues and conversational API responses), DunkStack enforces a protocol where:

- The agent writes ALL substantive output to files in `.agent/`
- API responses are limited to 1-3 sentences (status only)
- Human-agent communication flows through `from_human.md` and `to_human.md`
- An idle engine manages session lifecycle between agent queries
- A bridge system preserves state across sessions

The system is **completely self-contained** -- it does not modify any existing AutoForge files. We study AutoForge's patterns (workspace_chat_session.py, dependency_resolver.py, database.py, feature_mcp.py, process_manager.py, client.py, agent.py) as reference, then build our own parallel implementations.

---

## Architecture Overview

```
                    +------------------+
                    |   React UI       |
                    | (App Builder pg) |
                    +--------+---------+
                             |
                    REST + WebSocket
                             |
              +--------------+--------------+
              |    DunkStack Router          |
              |  server/routers/dunkstack.py |
              |  (ALREADY EXISTS - enhance)  |
              +--------------+--------------+
                             |
              +--------------+--------------+
              |   DunkStack Session          |
              | server/services/             |
              |   dunkstack_session.py       |
              |                              |
              |  - Claude SDK client         |
              |  - Idle engine loop          |
              |  - File-based walkie-talkie  |
              |  - Bridge load/save          |
              |  - Token tracking            |
              +--------------+--------------+
                             |
                +------------+------------+
                |                         |
      +---------+--------+    +----------+---------+
      | .agent/ Files     |    | DunkStack Features |
      | (comms, memory,   |    | dunkstack_features |
      |  bridge, output)  |    | .py + features.db  |
      +-------------------+    +--------------------+
```

### Key Differences from Workspace Chat

| Aspect | Workspace Chat | DunkStack |
|--------|---------------|-----------|
| Communication | In-memory asyncio.Queue | File-based (from_human.md, to_human.md) |
| Response style | Full conversational responses | 1-3 sentence status updates |
| Agent output | Streamed to WebSocket | Written to .agent/ files |
| Session continuity | Database conversation history | bridge.md + working_memory.md |
| Idle behavior | Waiting for user message | Active idle loop (check files, check control.md) |
| Token tracking | Database per-conversation | In-memory + DunkStack router /tokens/ endpoints |
| Feature management | AutoForge features.db (project-level) | Own features.db in .agent/ directory |

---

## Critical Rules

1. **HANDS OFF existing AutoForge code** -- Do not modify any file that exists today in the repository (except `.agent/` files and new DunkStack files we create)
2. **Study, don't import** -- Read AutoForge code as reference, then write equivalent DunkStack code. Do not import from AutoForge's `api/`, `mcp_server/`, or `server/services/workspace_*` modules
3. **Self-contained** -- Every DunkStack file lives in one of these locations:
   - `server/services/dunkstack_*.py` (new service files)
   - `server/routers/dunkstack.py` (already exists, enhance it)
   - `.agent/` directory (file-based protocol files)
4. **File-based protocol is sacred** -- The agent MUST write to files, NOT return long API responses. This is the entire point of DunkStack

---

## Phase 1: DunkStack Agent Session

**This is the hardest and most important phase. Build it first.**

### What We're Building

A new service (`dunkstack_session.py`) that manages a Claude SDK agent session with:
- File-based communication (not in-memory queues)
- An idle engine that manages the session lifecycle
- Bridge system for cross-session continuity
- Token tracking fed to the DunkStack router

### Files to Create

#### `server/services/dunkstack_session.py` (~500-600 lines)

This is the core file. It replaces `workspace_chat_session.py`'s role for the App Builder context.

**Reference files to study:**
- `server/services/workspace_chat_session.py` -- Claude SDK client setup, hooks, session lifecycle
- `client.py` -- ClaudeSDKClient creation, hook patterns, security settings
- `agent.py` -- Agent session loop, response streaming, error handling

**Key Classes:**

```python
class DunkStackSession:
    """Manages a DunkStack file-based agent session.

    Unlike WorkspaceChatSession (conversational, in-memory queue),
    DunkStack uses file-based communication and an idle engine loop.
    """

    def __init__(
        self,
        session_id: str,
        project_dir: Path,       # Where the app is being built
        agent_dir: Path,         # .agent/ directory (could be project_dir/.agent)
        model: str = "sonnet",   # "opus" or "sonnet"
    ):
        self.session_id = session_id
        self.project_dir = project_dir
        self.agent_dir = agent_dir
        self.client: Optional[ClaudeSDKClient] = None
        self._client_entered: bool = False

        # Idle engine state
        self._mode: str = "idle"              # idle | continue | autopilot
        self._idle_cycle_seconds: int = 300   # From config.yml
        self._running: bool = False
        self._idle_task: Optional[asyncio.Task] = None

        # Token tracking
        self._turn_count: int = 0
        self._last_api_usage: Optional[dict] = None
```

**Key Methods:**

1. **`async def start() -> AsyncGenerator[dict, None]`**
   - Load system prompt from `.agent/system_prompt.md`
   - Create Claude SDK client (similar to workspace_chat_session.py lines 370-710)
   - Set up bash security hook (same pattern as workspace)
   - Set up file-based walkie-talkie hook (NEW -- reads from_human.md instead of asyncio.Queue)
   - Set up PreCompact hook (same pattern as workspace)
   - Load bridge on start (read bridge.md, incorporate context, delete bridge.md)
   - Read initial state from index.md, working_memory.md, control.md
   - Start the idle engine loop
   - Yield session-started event

2. **`async def _idle_engine_loop()`**
   - This is the heart of DunkStack. Runs as a background asyncio task.
   - Loop:
     ```
     while self._running:
         # 1. Read control.md
         mode = self._read_control_mode()

         if mode == "autopilot":
             # Send "Continue working on the next task" to the agent
             await self._send_to_agent("Continue working. Check working_memory.md for current state.")
             # Agent works, writes to files, returns 1-2 sentence status
             # Loop immediately continues

         elif mode == "continue":
             # One-shot: do next thing, then flip back to idle
             await self._send_to_agent("Do the next task. Check working_memory.md for current state.")
             self._write_control_mode("idle")

         elif mode == "idle":
             # Check from_human.md for new messages
             new_messages = self._check_from_human()
             if new_messages:
                 # Send them to the agent
                 await self._send_to_agent(new_messages)
             else:
                 # Nothing to do -- sleep
                 await asyncio.sleep(self._idle_cycle_seconds)
     ```

3. **`async def _send_to_agent(message: str) -> str`**
   - Wrapper around `self.client.query()` + `self.client.receive_response()`
   - Streams response, tracks tokens
   - After each response, feeds token data to DunkStack router's `/tokens/record` endpoint
   - Returns the (brief) status response text

4. **`async def _file_walkie_talkie_hook(input_data, tool_use_id, context)`**
   - PreToolUse hook that fires on EVERY tool call
   - Reads `.agent/comms/from_human.md`, checks for NEW messages (track last-seen timestamp)
   - If new message found: block the tool, inject "[WALKIE-TALKIE MESSAGE FROM USER]" (same pattern as workspace)
   - This enables mid-task human interruption via file writes

5. **`async def _bridge_load()`**
   - Read `.agent/bridge.md` if it exists
   - Parse the bridge state (current task, progress, next steps, open questions)
   - Incorporate into the first message sent to the agent
   - Delete bridge.md after loading

6. **`async def _bridge_save(reason: str = "session_end")`**
   - Read current working_memory.md for state
   - Write a new bridge.md with:
     - Timestamp
     - Reason (session_end, hard_stop, manual)
     - Current task from working_memory
     - What was accomplished
     - Next steps
   - Append entry to progress/build_log.md
   - Update index.md if new files were created

7. **`async def close()`**
   - Save bridge (if bridge_on_end is True in config)
   - Stop idle engine loop
   - Close Claude SDK client

8. **`async def send_human_message(content: str)`**
   - Called by the router when UI sends a message
   - Appends to `.agent/comms/from_human.md` (same format as the router's existing endpoint)
   - If the agent is in idle mode, immediately trigger a check (wake up the idle loop)

9. **`async def set_control_mode(mode: str)`**
   - Write to `.agent/comms/control.md`
   - If switching from idle to continue/autopilot, wake up the idle loop

**Implementation Notes:**

- **System prompt delivery**: Load `.agent/system_prompt.md` content and pass it as the `system_prompt` parameter to `ClaudeAgentOptions`. This is the same mechanism workspace_chat_session.py uses (line 471: `system_prompt=get_workspace_system_prompt(...)`).

- **Claude SDK client creation pattern** (study workspace_chat_session.py lines 420-710):
  ```python
  from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
  from claude_agent_sdk.types import HookMatcher

  # Security settings (same structure as workspace)
  security_settings = {
      "sandbox": {"enabled": False},
      "permissions": {
          "defaultMode": "acceptEdits",
          "allow": ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"],
      },
  }

  # Write settings file
  settings_file = agent_dir / ".claude_settings.json"
  settings_file.write_text(json.dumps(security_settings, indent=2))

  # Create client
  client = ClaudeSDKClient(
      options=ClaudeAgentOptions(
          model=model,
          cli_path=shutil.which("claude"),
          system_prompt=system_prompt_text,
          setting_sources=["project"],
          allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"],
          permission_mode="acceptEdits",
          max_turns=150,
          cwd=str(project_dir),
          settings=str(settings_file.resolve()),
          env=sdk_env,
          hooks={
              "PreToolUse": [
                  HookMatcher(matcher="Bash", hooks=[bash_hook]),
                  HookMatcher(hooks=[file_walkie_talkie_hook]),
              ],
              "PreCompact": [
                  HookMatcher(hooks=[pre_compact_hook]),
              ],
          },
      )
  )
  ```

- **File-based walkie-talkie vs. in-memory queue**: The workspace uses `asyncio.Queue` (line 228). DunkStack reads from `from_human.md` instead. Key difference: we need to track which messages have been "seen" (by timestamp or line count) so we don't re-deliver old messages.

- **Token tracking integration**: After each `receive_response()` cycle, extract the `ResultMessage` usage data (study workspace_chat_session.py lines 1146-1203) and POST it to the DunkStack router's `/tokens/record` endpoint. The router already handles safety tier calculation.

- **Idle engine wakeup mechanism**: Use an `asyncio.Event` that the idle loop waits on with a timeout. When a new message arrives or control mode changes, set the event to wake the loop immediately instead of waiting for the full `idle_cycle_seconds`.

**Complexity estimate**: ~500-600 lines of Python

**Dependencies**: None (this is the foundation)

---

#### `server/services/dunkstack_file_utils.py` (~100-150 lines)

Utility functions for reading/writing `.agent/` protocol files.

**Key Functions:**

```python
def read_agent_file(agent_dir: Path, relative_path: str) -> Optional[str]:
    """Read a file from the .agent/ directory, returning None if not found."""

def write_agent_file(agent_dir: Path, relative_path: str, content: str) -> None:
    """Write content to a file in the .agent/ directory, creating dirs as needed."""

def append_agent_file(agent_dir: Path, relative_path: str, entry: str) -> None:
    """Append an entry to an agent file (for append-only files like build_log.md)."""

def read_control_mode(agent_dir: Path) -> tuple[str, str]:
    """Read control.md and return (mode, message). Defaults to ('idle', 'none')."""

def write_control_mode(agent_dir: Path, mode: str, message: str = "none") -> None:
    """Write the mode to control.md."""

def check_from_human_new(agent_dir: Path, last_seen_timestamp: Optional[str]) -> list[dict]:
    """Parse from_human.md and return messages newer than last_seen_timestamp.
    Each dict has: timestamp, title, content."""

def append_to_human(agent_dir: Path, category: str, title: str, content: str) -> str:
    """Append a message to to_human.md. Returns the timestamp used."""

def append_from_human(agent_dir: Path, title: str, content: str) -> str:
    """Append a message to from_human.md. Returns the timestamp used."""

def read_config(agent_dir: Path) -> dict:
    """Read config.yml and return as dict."""

def update_index(agent_dir: Path, new_files: list[str]) -> None:
    """Add new file entries to the index.md."""
```

**Implementation Notes:**
- All file operations use `encoding="utf-8"`
- Timestamps use UTC in format `YYYY-MM-DD HH:MM` (matching existing router format)
- The `check_from_human_new()` function parses the `## [YYYY-MM-DD HH:MM] Title` headers to identify new messages

**Complexity estimate**: ~100-150 lines

**Dependencies**: None

---

### Phase 1 Testing Checklist

- [ ] Session starts and creates Claude SDK client
- [ ] System prompt loads from `.agent/system_prompt.md`
- [ ] File-based walkie-talkie hook reads from_human.md correctly
- [ ] Idle engine loops: idle mode sleeps, autopilot continues, continue does one-shot
- [ ] Bridge loads on session start, saves on session end
- [ ] Token data flows to DunkStack router's `/tokens/record`
- [ ] Session closes cleanly (client disposed, bridge saved)

---

## Phase 2: DunkStack Dependency System

**Modeled after AutoForge's dependency system, but completely separate code and database.**

### What We're Building

A self-contained feature management system with:
- Own SQLite database in `.agent/features.db`
- Own SQLAlchemy models
- Own dependency resolver (ported from AutoForge's `api/dependency_resolver.py`)
- Feature management functions (claim, mark passing/failing, get ready, etc.)
- A `dependency_map.md` file the agent reads for build order

### Files to Create

#### `server/services/dunkstack_features.py` (~450-550 lines)

**Reference files to study:**
- `api/database.py` -- SQLAlchemy models, database creation, migrations, atomic transactions
- `api/dependency_resolver.py` -- Kahn's algorithm, DFS cycle detection, scheduling scores
- `mcp_server/feature_mcp.py` -- Feature management tools (claim, mark, create, etc.)

**Key Components:**

**1. Database Models (~80 lines)**

```python
from sqlalchemy import Boolean, Column, Integer, String, Text, create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import JSON

class DunkBase(DeclarativeBase):
    """SQLAlchemy declarative base for DunkStack features."""
    pass

class DunkFeature(DunkBase):
    """Feature model for DunkStack's App Builder."""
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(Integer, nullable=False, default=999, index=True)
    category = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)          # JSON array of step strings
    passes = Column(Boolean, nullable=False, default=False, index=True)
    in_progress = Column(Boolean, nullable=False, default=False, index=True)
    dependencies = Column(JSON, nullable=True)     # JSON array of feature IDs

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "priority": self.priority,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "passes": self.passes if self.passes is not None else False,
            "in_progress": self.in_progress if self.in_progress is not None else False,
            "dependencies": self.dependencies if self.dependencies else [],
        }
```

**2. Database Creation (~60 lines)**

Port the pattern from `api/database.py` lines 387-457:
- `create_dunkstack_database(agent_dir: Path)` -- Creates engine + sessionmaker
- WAL mode for concurrent access
- IMMEDIATE transactions via event hooks (same pattern as AutoForge)
- `atomic_transaction()` context manager (same pattern as AutoForge)

The database file lives at `.agent/features.db` (NOT the project's `.autoforge/features.db`).

**3. Dependency Resolver (~120 lines)**

Port from `api/dependency_resolver.py` (all 353 lines, adapted for DunkStack):

- `resolve_dependencies(features)` -- Kahn's algorithm with priority-aware ordering
- `are_dependencies_satisfied(feature, all_features, passing_ids)` -- Check if deps met
- `would_create_circular_dependency(features, source_id, target_id)` -- DFS cycle detection
- `compute_scheduling_scores(features)` -- Unblocking potential + depth + priority
- `get_ready_features(features, limit)` -- Features ready to work on
- `get_blocked_features(features)` -- Features blocked by unmet deps
- `validate_dependencies(feature_id, dependency_ids, all_feature_ids)` -- Input validation

These are direct ports. The algorithms (Kahn's, DFS) are identical. The only changes are:
- Uses `DunkFeature` model instead of `Feature`
- Uses `.agent/features.db` instead of `.autoforge/features.db`

**4. Feature Management Functions (~200 lines)**

Port from `mcp_server/feature_mcp.py`, adapted as regular Python functions (not MCP tools):

```python
class DunkStackFeatureManager:
    """Manages features for the DunkStack App Builder."""

    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        self._engine, self._session_maker = create_dunkstack_database(agent_dir)

    def get_stats(self) -> dict:
        """Get progress statistics. Returns {passing, in_progress, total, percentage}."""

    def get_by_id(self, feature_id: int) -> Optional[dict]:
        """Get a specific feature by ID."""

    def get_summary(self, feature_id: int) -> Optional[dict]:
        """Get minimal feature info (id, name, passes, in_progress, deps)."""

    def get_ready(self, limit: int = 10) -> list[dict]:
        """Get features ready to work on (deps satisfied, not in progress)."""

    def get_blocked(self) -> list[dict]:
        """Get features blocked by unmet dependencies."""

    def get_graph(self) -> dict:
        """Get dependency graph data for visualization ({nodes, edges})."""

    def claim_and_get(self, feature_id: int) -> dict:
        """Atomically claim a feature and return its details."""

    def mark_in_progress(self, feature_id: int) -> dict:
        """Mark a feature as in progress."""

    def mark_passing(self, feature_id: int) -> dict:
        """Mark a feature as passing (complete)."""

    def mark_failing(self, feature_id: int) -> dict:
        """Mark a feature as failing."""

    def skip(self, feature_id: int) -> dict:
        """Skip a feature (move to end of queue)."""

    def clear_in_progress(self, feature_id: int) -> dict:
        """Clear in-progress status."""

    def create_feature(self, category, name, description, steps) -> dict:
        """Create a single feature."""

    def create_bulk(self, features: list[dict]) -> dict:
        """Create multiple features at once."""

    def add_dependency(self, feature_id: int, dependency_id: int) -> dict:
        """Add a dependency between features."""

    def remove_dependency(self, feature_id: int, dependency_id: int) -> dict:
        """Remove a dependency."""

    def set_dependencies(self, feature_id: int, dependency_ids: list[int]) -> dict:
        """Set all dependencies for a feature at once."""

    def generate_dependency_map(self) -> str:
        """Generate a markdown representation of the dependency graph for the agent.
        Writes to .agent/knowledge/dependency_map.md and returns the content."""

    def dispose(self):
        """Dispose of the database engine."""
```

**5. Dependency Map Generation (~50 lines)**

The `generate_dependency_map()` method creates a human-readable markdown file at `.agent/knowledge/dependency_map.md` that the agent reads to understand build order:

```markdown
# Dependency Map
Generated: 2026-02-25 14:30

## Build Order (topological sort)
1. [DONE] #1 Project Setup - Initial configuration
2. [READY] #2 Database Schema - Core data models (depends on: #1)
3. [BLOCKED] #3 API Endpoints - REST API (blocked by: #2)
4. [IN PROGRESS] #4 Authentication - User auth system

## Ready to Build (dependencies satisfied)
- #2 Database Schema (priority: 2, score: 850.0)

## Blocked Features
- #3 API Endpoints (blocked by: #2 Database Schema)

## Statistics
- Total: 10 | Passing: 3 | In Progress: 1 | Ready: 2 | Blocked: 4
```

This file is regenerated every time a feature status changes, so the agent always has an up-to-date view.

**Complexity estimate**: ~450-550 lines

**Dependencies**: Phase 1 (the session uses the feature manager to track progress)

---

### Phase 2 Integration with Phase 1

The `DunkStackSession` creates a `DunkStackFeatureManager` on startup:

```python
# In DunkStackSession.__init__:
self.features = DunkStackFeatureManager(agent_dir)

# In _idle_engine_loop, after agent completes work:
# Regenerate the dependency map so agent's next read is up-to-date
self.features.generate_dependency_map()
```

The idle engine can also use feature stats to determine when the project is complete:

```python
stats = self.features.get_stats()
if stats["total"] > 0 and stats["passing"] == stats["total"]:
    # All features complete! Notify UI, save bridge, stop.
    await self._broadcast({"type": "project_complete", "stats": stats})
    await self._bridge_save(reason="project_complete")
    self._running = False
```

### Phase 2 Testing Checklist

- [ ] Database creates at `.agent/features.db`
- [ ] Features can be created (single and bulk)
- [ ] Dependencies can be added/removed with cycle detection
- [ ] Topological sort returns correct build order
- [ ] Scheduling scores prioritize unblocking features
- [ ] `get_ready()` returns only features with satisfied deps
- [ ] `claim_and_get()` is atomic (no double-claim)
- [ ] `mark_passing()` / `mark_failing()` update correctly
- [ ] `generate_dependency_map()` produces readable markdown
- [ ] Feature status changes trigger dependency map regeneration

---

## Phase 3: DunkStack Router Enhancements

**The router already exists with comms, control, bridge, config, and token endpoints. We add agent lifecycle and feature management endpoints.**

### File to Modify

#### `server/routers/dunkstack.py` (enhance existing, add ~300-400 lines)

**Reference files to study:**
- `server/routers/agent.py` -- Agent lifecycle (start/stop/pause/resume) endpoints
- `server/routers/features.py` -- Feature CRUD endpoints
- `server/routers/workspace.py` -- WebSocket session management

**New Endpoints to Add:**

**1. Agent Lifecycle (~100 lines)**

```python
# POST /api/dunkstack/agent/start
# Body: { project_dir: str, model?: str }
# Returns: { status: "ok", session_id: str }
@router.post("/agent/start")
async def start_agent(request: AgentStartRequest):
    """Start a DunkStack agent session for the App Builder."""
    session = await create_dunkstack_session(
        project_dir=request.project_dir,
        model=request.model or "sonnet",
    )
    # Start the session (creates Claude client, loads bridge, starts idle engine)
    async for event in session.start():
        await _broadcast(event)
    return {"status": "ok", "session_id": session.session_id}

# POST /api/dunkstack/agent/stop
@router.post("/agent/stop")
async def stop_agent():
    """Stop the running DunkStack agent session."""
    session = _get_active_session()
    if not session:
        raise HTTPException(404, "No active DunkStack session")
    await session.close()
    _clear_active_session()
    return {"status": "ok"}

# GET /api/dunkstack/agent/status
@router.get("/agent/status")
async def agent_status():
    """Get the current DunkStack agent status."""
    session = _get_active_session()
    if not session:
        return {"status": "stopped", "session_id": None}
    return {
        "status": "running",
        "session_id": session.session_id,
        "mode": session.current_mode,
        "turn_count": session.turn_count,
    }
```

**2. Feature Management Endpoints (~150 lines)**

```python
# GET /api/dunkstack/features
@router.get("/features")
async def list_features():
    """List all features with their status."""
    manager = _get_feature_manager()
    # Return all features as a list
    ...

# GET /api/dunkstack/features/stats
@router.get("/features/stats")
async def feature_stats():
    """Get feature completion statistics."""
    ...

# GET /api/dunkstack/features/ready
@router.get("/features/ready")
async def ready_features():
    """Get features ready to be worked on."""
    ...

# GET /api/dunkstack/features/blocked
@router.get("/features/blocked")
async def blocked_features():
    """Get features blocked by unmet dependencies."""
    ...

# GET /api/dunkstack/features/graph
@router.get("/features/graph")
async def feature_graph():
    """Get the dependency graph for visualization."""
    ...

# GET /api/dunkstack/features/{feature_id}
@router.get("/features/{feature_id}")
async def get_feature(feature_id: int):
    """Get a specific feature by ID."""
    ...

# POST /api/dunkstack/features
@router.post("/features")
async def create_feature(request: FeatureCreateRequest):
    """Create a new feature."""
    ...

# POST /api/dunkstack/features/bulk
@router.post("/features/bulk")
async def create_features_bulk(request: BulkFeatureCreateRequest):
    """Create multiple features at once."""
    ...

# PUT /api/dunkstack/features/{feature_id}/status
@router.put("/features/{feature_id}/status")
async def update_feature_status(feature_id: int, request: FeatureStatusUpdate):
    """Update a feature's status (passing, failing, in_progress, skip)."""
    ...

# POST /api/dunkstack/features/{feature_id}/dependencies
@router.post("/features/{feature_id}/dependencies")
async def add_dependency(feature_id: int, request: DependencyRequest):
    """Add a dependency to a feature."""
    ...

# DELETE /api/dunkstack/features/{feature_id}/dependencies/{dep_id}
@router.delete("/features/{feature_id}/dependencies/{dep_id}")
async def remove_dependency(feature_id: int, dep_id: int):
    """Remove a dependency from a feature."""
    ...
```

**3. Enhanced WebSocket Events (~50 lines)**

Add new event types to the existing WebSocket handler:

```python
# New event types to broadcast:
# - agent_status: { type: "agent_status", status: "running"|"idle"|"stopped", mode: "idle"|"continue"|"autopilot" }
# - feature_update: { type: "feature_update", feature_id: int, status: str, stats: dict }
# - agent_output: { type: "agent_output", content: str }  # Brief status lines from agent
# - project_complete: { type: "project_complete", stats: dict }
# - file_change: { type: "file_change", path: str, action: "created"|"modified" }
```

**4. Pydantic Models for New Endpoints (~50 lines)**

```python
class AgentStartRequest(BaseModel):
    project_dir: str
    model: Optional[str] = "sonnet"

class FeatureCreateRequest(BaseModel):
    category: str
    name: str
    description: str
    steps: list[str]

class BulkFeatureCreateRequest(BaseModel):
    features: list[FeatureCreateRequest]

class FeatureStatusUpdate(BaseModel):
    action: str  # "passing" | "failing" | "in_progress" | "skip" | "clear_in_progress"

class DependencyRequest(BaseModel):
    dependency_id: int
```

**5. Session Registry (~30 lines)**

```python
# Module-level session registry (like workspace's _sessions dict)
_active_session: Optional[DunkStackSession] = None
_session_lock = threading.Lock()

def _get_active_session() -> Optional[DunkStackSession]:
    with _session_lock:
        return _active_session

def _set_active_session(session: DunkStackSession) -> None:
    with _session_lock:
        global _active_session
        _active_session = session

def _clear_active_session() -> None:
    with _session_lock:
        global _active_session
        _active_session = None
```

**Implementation Notes:**

- The feature manager is instantiated when the agent starts and attached to the session. Feature endpoints read from the session's feature manager.
- When no session is active, feature endpoints can still work by creating a standalone `DunkStackFeatureManager` from the `.agent/` directory (for viewing features in the UI without an agent running).
- All feature status changes broadcast a `feature_update` event via WebSocket so the UI updates in real-time.

**Complexity estimate**: ~300-400 lines added to existing router

**Dependencies**: Phase 1 (session) and Phase 2 (features)

---

### Phase 3 Testing Checklist

- [ ] `/agent/start` creates and starts a DunkStack session
- [ ] `/agent/stop` cleanly stops the session
- [ ] `/agent/status` returns correct status
- [ ] Feature CRUD endpoints work (list, get, create, bulk create)
- [ ] Feature status updates work (passing, failing, in_progress, skip)
- [ ] Dependency add/remove works with validation
- [ ] WebSocket broadcasts feature updates in real-time
- [ ] WebSocket broadcasts agent status changes
- [ ] Features endpoints work both with and without an active session

---

## Phase 4: UI Wiring

**Connect the App Builder page to DunkStack endpoints.**

### Reference Files to Study

- `ui/src/pages/WorkspacePage.tsx` -- Workspace chat UI (WebSocket, message handling)
- `ui/src/components/workspace/` -- Workspace panel components
- `ui/src/hooks/useWebSocket.ts` -- WebSocket hook pattern
- `ui/src/hooks/useProjects.ts` -- React Query hooks for API calls
- `ui/src/lib/api.ts` -- REST API client
- `ui/src/lib/types.ts` -- TypeScript type definitions
- `ui/src/components/DependencyGraph.tsx` -- Dependency graph visualization (dagre)
- `ui/WORKSPACE_STANDARDS.md` -- UI design standards

### Files to Create/Modify

#### `ui/src/hooks/useDunkStack.ts` (~200-250 lines)

React Query hooks for all DunkStack endpoints.

```typescript
// Agent lifecycle hooks
export function useDunkStackStatus() { ... }
export function useStartDunkStackAgent() { ... }
export function useStopDunkStackAgent() { ... }

// Feature hooks
export function useDunkStackFeatures() { ... }
export function useDunkStackFeatureStats() { ... }
export function useDunkStackReadyFeatures() { ... }
export function useDunkStackBlockedFeatures() { ... }
export function useDunkStackFeatureGraph() { ... }
export function useCreateDunkStackFeature() { ... }
export function useCreateDunkStackFeaturesBulk() { ... }
export function useUpdateDunkStackFeatureStatus() { ... }
export function useAddDunkStackDependency() { ... }
export function useRemoveDunkStackDependency() { ... }

// Comms hooks
export function useDunkStackComms() { ... }
export function useSendDunkStackMessage() { ... }

// Control hooks
export function useDunkStackControl() { ... }
export function useSetDunkStackControl() { ... }

// Config hooks
export function useDunkStackConfig() { ... }
export function useUpdateDunkStackConfig() { ... }

// Token hooks
export function useDunkStackTokenState() { ... }

// Working memory / index
export function useDunkStackWorkingMemory() { ... }
export function useDunkStackIndex() { ... }
export function useDunkStackBuildLog() { ... }
```

**Complexity estimate**: ~200-250 lines

---

#### `ui/src/hooks/useDunkStackWebSocket.ts` (~100-150 lines)

WebSocket connection to `/api/dunkstack/ws` for real-time updates.

```typescript
export function useDunkStackWebSocket() {
    // Connect to DunkStack WebSocket
    // Handle event types:
    //   - token_update: Update token gauge
    //   - comms_update: New message in from_human or to_human
    //   - control_update: Mode changed
    //   - agent_status: Agent running/idle/stopped
    //   - feature_update: Feature status changed
    //   - project_complete: All features done
    //   - bridge_saved: Bridge save occurred
    //   - config_update: Config changed

    // Invalidate React Query caches when relevant events arrive
    // (e.g., invalidate features query when feature_update received)
}
```

**Reference**: Study `ui/src/hooks/useWebSocket.ts` for the existing WebSocket pattern.

**Complexity estimate**: ~100-150 lines

---

#### `ui/src/components/appbuilder/` (new directory, ~800-1000 lines total)

These components make up the App Builder page's DunkStack integration.

**1. `TokenGauge.tsx` (~80-100 lines)**
- Circular or bar gauge showing context window usage
- Color changes based on safety tier (green/orange/red)
- Reads from DunkStack WebSocket token_update events
- Shows: usage %, safety tier label, total tokens

**2. `CommsPanel.tsx` (~120-150 lines)**
- Split view: from_human messages (left/top) and to_human messages (right/bottom)
- Messages rendered as timestamped cards
- Input box at bottom for sending new from_human messages
- Auto-scrolls to latest message
- Polls or uses WebSocket for real-time updates

**3. `ControlBar.tsx` (~80-100 lines)**
- Shows current mode: idle / continue / autopilot
- Buttons: "Continue" (one-shot), "Autopilot" (toggle), "Stop" (kill session)
- "Wait N minutes" dropdown (sets idle_cycle_seconds in config)
- Visual indicator of agent state (idle spinner, working animation, autopilot pulse)

**4. `FeatureBoard.tsx` (~150-200 lines)**
- Kanban-style board with columns: Pending, In Progress, Passing, Blocked
- Feature cards show: name, category, dependency count, priority
- Click to expand feature details
- Drag to reorder (updates priority)
- "Add Feature" button

**5. `DependencyGraphPanel.tsx` (~100-150 lines)**
- Wrapper around AutoForge's DependencyGraph component pattern
- Uses dagre for layout (same library)
- Nodes colored by status (pending=yellow, in_progress=cyan, done=green, blocked=red)
- Edges show dependency relationships
- Click node to see feature details
- Toggle between kanban and graph view (same pattern as AutoForge's G keyboard shortcut)

**6. `WorkingMemoryPanel.tsx` (~60-80 lines)**
- Read-only view of `.agent/working_memory.md`
- Rendered as markdown
- Auto-refreshes on a timer or WebSocket event
- Collapsible panel

**7. `BuildLogPanel.tsx` (~60-80 lines)**
- Read-only view of `.agent/progress/build_log.md`
- Rendered as markdown
- Scrollable, newest entries at bottom
- Auto-refreshes

**8. `AgentStatusBar.tsx` (~50-70 lines)**
- Top bar showing: agent status, current mode, turn count, session duration
- Token gauge (compact inline version)
- Quick action buttons (continue, stop)

**Implementation Notes:**

- Follow `ui/WORKSPACE_STANDARDS.md` for layout patterns, loading/empty/error states
- Use the neobrutalism design system (CSS variables from `ui/src/styles/globals.css`)
- Color tokens: `--color-neo-pending` (yellow), `--color-neo-progress` (cyan), `--color-neo-done` (green)
- All components use the hooks from `useDunkStack.ts` and `useDunkStackWebSocket.ts`
- Components should handle the "no session active" state gracefully (show features read-only, disable control buttons)

**Complexity estimate**: ~800-1000 lines total across all components

**Dependencies**: Phase 3 (router endpoints must exist)

---

#### `ui/src/pages/AppBuilderPage.tsx` (~150-200 lines)

The main page component that assembles the DunkStack UI.

```typescript
// Layout:
// +---------------------------------------------+
// | AgentStatusBar (top)                         |
// +-----+---------------------------------------+
// |     | FeatureBoard OR DependencyGraphPanel   |
// |Comms|                                        |
// |Panel|                                        |
// |     +---------------------------------------+
// |     | BuildLogPanel | WorkingMemoryPanel     |
// +-----+---------------------------------------+
// | ControlBar (bottom)                          |
// +---------------------------------------------+
```

**Complexity estimate**: ~150-200 lines

**Dependencies**: All Phase 4 components

---

### Phase 4 Testing Checklist

- [ ] Token gauge updates in real-time via WebSocket
- [ ] Comms panel shows from_human and to_human messages
- [ ] Sending a message from UI appends to from_human.md
- [ ] Control buttons change agent mode (idle/continue/autopilot)
- [ ] Feature board shows all features with correct statuses
- [ ] Dependency graph renders with dagre layout
- [ ] Working memory panel shows current agent state
- [ ] Build log panel shows append-only entries
- [ ] Agent status bar reflects running/idle/stopped state
- [ ] UI handles "no active session" gracefully
- [ ] WebSocket reconnects on disconnect

---

## Cross-Cutting Concerns

### Error Handling

Every DunkStack component must handle errors gracefully:

1. **Claude SDK errors** (rate limits, auth failures, timeouts)
   - Study `agent.py` lines 147-159 for rate limit detection
   - Study `rate_limit_utils.py` for backoff strategies
   - On rate limit: pause idle engine, wait, resume
   - On auth error: broadcast error event to UI, stop session

2. **File I/O errors** (permissions, disk full, file locked)
   - All file operations wrapped in try/except
   - Fallback to in-memory state if file write fails
   - Log warnings but don't crash the session

3. **Database errors** (SQLite locked, corruption)
   - Use IMMEDIATE transactions (same as AutoForge)
   - 30-second busy_timeout
   - Retry logic for transient lock failures

### Logging

All DunkStack files use Python's `logging` module with the `__name__` pattern:
```python
logger = logging.getLogger(__name__)
```

Log levels:
- `INFO` -- Session start/stop, feature status changes, mode changes
- `WARNING` -- File I/O errors, non-fatal failures
- `ERROR` -- Claude SDK errors, database errors
- `DEBUG` -- File reads/writes, hook invocations, idle loop iterations

### Security

1. **Bash security hook**: Same pattern as workspace -- use `security.py`'s `bash_security_hook` with project_dir context injection
2. **File access**: Agent is restricted to project_dir via Claude SDK's filesystem permissions
3. **No secrets in .agent/ files**: The comms files, working memory, and bridge should never contain API keys or credentials

### Configuration

All configurable values live in `.agent/settings/config.yml`. The session reads this on startup and when the config is updated via the router:

```yaml
safety:
  warning_threshold_pct: 45
  handoff_threshold_pct: 47.5
  hard_stop_threshold_pct: 50
  model_limit: 200000

context_management:
  working_memory_frequency: 3    # Update every N turns
  file_read_budget: 4000         # Max tokens per turn on file reads
  api_response_max_sentences: 3  # Max sentences in chat response

session:
  idle_cycle_seconds: 300        # Wait between idle checks
  bridge_on_end: true            # Auto-save bridge on session end
```

---

## Testing Strategy

### Unit Tests

Create `tests/test_dunkstack_features.py` (~200 lines):
- Test DunkFeature model creation and to_dict()
- Test dependency resolver (Kahn's, cycle detection, scheduling scores)
- Test feature manager (CRUD, status transitions, atomic claiming)
- Test dependency map generation

Create `tests/test_dunkstack_file_utils.py` (~100 lines):
- Test file read/write/append operations
- Test control mode parsing
- Test from_human message parsing and timestamp filtering
- Test index.md updating

### Integration Tests

Create `tests/test_dunkstack_session.py` (~150 lines):
- Test session start/stop lifecycle
- Test idle engine mode transitions
- Test bridge load/save cycle
- Test token tracking flow

### Manual Testing Protocol

1. Start the DunkStack agent via the UI
2. Verify the agent reads system_prompt.md and starts in idle mode
3. Send a message via the comms panel -- verify it appears in from_human.md
4. Switch to "continue" mode -- verify agent does one task and returns to idle
5. Switch to "autopilot" -- verify agent continues working without intervention
6. Check working_memory.md updates every 3 turns
7. Stop the agent -- verify bridge.md is saved
8. Restart the agent -- verify bridge.md is loaded and deleted
9. Check token gauge updates in real-time
10. Create features via the API -- verify they appear in the kanban board
11. Verify dependency graph renders correctly

---

## File Inventory

### New Files (to create)

| File | Phase | Est. Lines | Purpose |
|------|-------|-----------|---------|
| `server/services/dunkstack_session.py` | 1 | 500-600 | Core agent session with idle engine |
| `server/services/dunkstack_file_utils.py` | 1 | 100-150 | File I/O utilities for .agent/ protocol |
| `server/services/dunkstack_features.py` | 2 | 450-550 | Feature management + dependency resolver |
| `ui/src/hooks/useDunkStack.ts` | 4 | 200-250 | React Query hooks for all endpoints |
| `ui/src/hooks/useDunkStackWebSocket.ts` | 4 | 100-150 | WebSocket hook for real-time updates |
| `ui/src/components/appbuilder/TokenGauge.tsx` | 4 | 80-100 | Context window usage gauge |
| `ui/src/components/appbuilder/CommsPanel.tsx` | 4 | 120-150 | Human-agent message display |
| `ui/src/components/appbuilder/ControlBar.tsx` | 4 | 80-100 | Idle/continue/autopilot controls |
| `ui/src/components/appbuilder/FeatureBoard.tsx` | 4 | 150-200 | Kanban feature board |
| `ui/src/components/appbuilder/DependencyGraphPanel.tsx` | 4 | 100-150 | Dependency graph visualization |
| `ui/src/components/appbuilder/WorkingMemoryPanel.tsx` | 4 | 60-80 | Working memory viewer |
| `ui/src/components/appbuilder/BuildLogPanel.tsx` | 4 | 60-80 | Build log viewer |
| `ui/src/components/appbuilder/AgentStatusBar.tsx` | 4 | 50-70 | Status bar with quick actions |
| `ui/src/pages/AppBuilderPage.tsx` | 4 | 150-200 | Main page assembly |
| `tests/test_dunkstack_features.py` | 2 | 200 | Feature + dependency unit tests |
| `tests/test_dunkstack_file_utils.py` | 1 | 100 | File utility unit tests |
| `tests/test_dunkstack_session.py` | 1 | 150 | Session integration tests |

### Existing Files (to enhance)

| File | Phase | Est. Lines Added | Purpose |
|------|-------|-----------------|---------|
| `server/routers/dunkstack.py` | 3 | 300-400 | Agent lifecycle + feature endpoints |

### Existing Files (reference only -- DO NOT MODIFY)

| File | What to Extract |
|------|----------------|
| `server/services/workspace_chat_session.py` | Claude SDK client setup, hooks, session lifecycle |
| `client.py` | ClaudeSDKClient creation, security settings, hook patterns |
| `agent.py` | Agent session loop, response streaming, error handling |
| `api/database.py` | SQLAlchemy models, database creation, IMMEDIATE transactions |
| `api/dependency_resolver.py` | Kahn's algorithm, DFS cycle detection, scheduling scores |
| `mcp_server/feature_mcp.py` | Feature management functions (claim, mark, create, etc.) |
| `server/services/process_manager.py` | Process lifecycle, lock files, cleanup |
| `security.py` | Bash command allowlist validation |
| `server/routers/agent.py` | Agent lifecycle endpoint patterns |
| `server/routers/features.py` | Feature CRUD endpoint patterns |
| `server/routers/workspace.py` | WebSocket session management patterns |
| `ui/src/hooks/useWebSocket.ts` | WebSocket hook pattern |
| `ui/src/hooks/useProjects.ts` | React Query hook patterns |
| `ui/src/components/DependencyGraph.tsx` | Dagre graph visualization |

### Total Estimated Lines

| Phase | Lines |
|-------|-------|
| Phase 1 (Session + Utils) | 600-750 |
| Phase 2 (Features + Deps) | 450-550 |
| Phase 3 (Router Enhancements) | 300-400 |
| Phase 4 (UI Components) | 1,150-1,430 |
| Tests | 450 |
| **Total** | **2,950-3,580** |

---

## Build Order Summary

```
Phase 1 ──────────────────────────────────────────
  1a. dunkstack_file_utils.py (no dependencies)
  1b. dunkstack_session.py (depends on 1a)

Phase 2 ──────────────────────────────────────────
  2a. dunkstack_features.py (no dependencies)
  2b. Integrate features with session (depends on 1b, 2a)

Phase 3 ──────────────────────────────────────────
  3a. Router enhancements (depends on 1b, 2a)

Phase 4 ──────────────────────────────────────────
  4a. useDunkStack.ts hooks (depends on 3a)
  4b. useDunkStackWebSocket.ts (depends on 3a)
  4c. UI components (depends on 4a, 4b)
  4d. AppBuilderPage.tsx (depends on 4c)
```

Phases 1a and 2a can be built in parallel since they have no dependencies on each other. Phase 1b depends on 1a. Phase 2b depends on both 1b and 2a. Phase 3 depends on both Phase 1 and Phase 2. Phase 4 depends entirely on Phase 3.

---

## Appendix: Key Patterns to Port

### Pattern 1: Claude SDK Client Creation

**Source**: `workspace_chat_session.py` lines 420-710

**What to extract**:
- Security settings JSON structure
- ClaudeAgentOptions construction
- Hook registration (PreToolUse, PreCompact)
- Model resolution from registry
- Environment variable setup via `get_effective_sdk_env()`
- Client context manager (`__aenter__` / `__aexit__`)

**What to change for DunkStack**:
- System prompt comes from `.agent/system_prompt.md` file, not a function
- Working directory is the project being built, not a user-chosen directory
- No conversation history database (state lives in .agent/ files)
- Walkie-talkie reads files instead of asyncio.Queue

### Pattern 2: Walkie-Talkie Hook

**Source**: `workspace_chat_session.py` lines 572-620

**What to extract**:
- Hook function signature: `async def hook(input_data, tool_use_id=None, context=None)`
- Block format: `{"decision": "block", "reason": "[WALKIE-TALKIE MESSAGE FROM USER]..."}`
- Message concatenation for multiple queued messages

**What to change for DunkStack**:
- Read from `.agent/comms/from_human.md` instead of `asyncio.Queue`
- Track last-seen message timestamp to avoid re-delivering
- Parse the `## [YYYY-MM-DD HH:MM] Title` format to extract messages

### Pattern 3: Token Tracking from ResultMessage

**Source**: `workspace_chat_session.py` lines 1146-1203

**What to extract**:
- How to access `usage` from ResultMessage: `getattr(msg, "usage", None) or {}`
- Token fields: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`
- Cost calculation: `getattr(msg, "total_cost_usd", None)`

**What to change for DunkStack**:
- Instead of storing in workspace database, POST to `/api/dunkstack/tokens/record`
- The router's existing `_get_safety_status()` handles tier calculation

### Pattern 4: Dependency Resolution

**Source**: `api/dependency_resolver.py` (full file, 353 lines)

**What to extract**: Everything -- the algorithms are portable.

**What to change**:
- Function signatures stay the same
- Uses `DunkFeature.to_dict()` output (same shape as `Feature.to_dict()`)
- Lives in `dunkstack_features.py` instead of a separate file

### Pattern 5: Atomic Database Operations

**Source**: `api/database.py` lines 358-557 and `mcp_server/feature_mcp.py`

**What to extract**:
- IMMEDIATE transaction configuration via engine events
- `atomic_transaction()` context manager
- Atomic UPDATE...WHERE patterns for concurrent safety (e.g., `UPDATE features SET in_progress=1 WHERE id=:id AND passes=0 AND in_progress=0`)

**What to change**:
- Database path is `.agent/features.db`, not `.autoforge/features.db`
- Uses `DunkBase` / `DunkFeature` models
- No engine cache (single session = single database)

---

*End of implementation plan.*
