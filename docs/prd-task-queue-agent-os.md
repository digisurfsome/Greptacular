# Agent OS Blueprint: Factory Task Queue ("The Train")

**Status:** Draft
**Date:** 2026-03-04
**Author:** Owner + Claude (Session 7)
**Depends on:** Factory Controller (built), Factory Presets (built), Rate Limit Logger (built)
**Implementation:** 6 phases, each under 50% context window

---

## STANDARDS LAYER

### Technology Stack
- **Backend:** Python 3.11+ with FastAPI, Pydantic models, async/await
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS v4, TanStack Query (React Query)
- **Data Storage:** JSON file (`~/.autoforge/task_queue.json`) — migrate to SQLite later if needed
- **Real-time:** WebSocket events via existing `server/websocket.py` broadcast pattern
- **Agent Runtime:** Claude Agent SDK via `server/services/process_manager.py`

### Architecture Patterns
- **Services** live in `server/services/` — one file per domain (e.g. `queue_executor.py`)
- **Routers** live in `server/routers/` — thin REST layer, Pydantic request/response models
- **React hooks** in `ui/src/hooks/` — wrap TanStack Query `useQuery`/`useMutation`
- **UI components** in `ui/src/components/factory/` — colocated with existing factory UI
- **Global config** stored in `~/.autoforge/` — created on first use, safe file I/O
- **Registration** — new routers registered in `server/routers/__init__.py` AND `server/main.py`

### Key Existing Code to Understand
| File | What It Does | Why It Matters |
|---|---|---|
| `server/services/factory_controller.py` | Brain of factory mode — phases, handoffs, agent lifecycle | Queue Executor sits ABOVE this, calls it per task |
| `server/services/handoff_watcher.py` | Detects handoff.json when agent exits | Used by factory controller, queue executor listens for task completion |
| `server/services/process_manager.py` | Starts/stops Claude agent subprocesses | Factory controller calls this to start agents |
| `server/services/rate_limit_logger.py` | Logs rate limit events to JSON | Queue executor checks this for scheduling decisions |
| `server/routers/factory.py` | REST endpoints for factory (start/stop/status/presets) | Pattern to follow for queue endpoints |
| `ui/src/components/factory/FactoryPanel.tsx` | Factory UI — mode pills, objective textarea, status bar | Queue UI lives alongside or below this |
| `ui/src/hooks/useFactory.ts` | React Query hooks for factory API | Pattern to follow for queue hooks |
| `ui/src/lib/api.ts` | API client functions (fetch wrappers) | Add queue API functions here |
| `registry.py` | Maps project names to directory paths | Queue Executor uses this to resolve project dirs |
| `server/routers/__init__.py` | Registers all routers | Must add queue_router here |
| `server/main.py` | FastAPI app setup, includes all routers | Must include queue_router here |

### Coding Conventions
- Python: ruff-clean, type hints on public methods, `logging.getLogger(__name__)`
- TypeScript: ESLint-clean, `interface` for data shapes, `type` for unions
- Tailwind: semantic tokens (`bg-card`, `text-foreground`, `border-border`), no hardcoded colors
- Pydantic: `BaseModel` for all request/response schemas, `Optional` with `Field` for validation
- File I/O: always handle missing dirs (`mkdir(parents=True, exist_ok=True)`), corrupted JSON (reset to default), OS errors (log and continue)
- Commits: conventional commits (`feat:`, `fix:`, `docs:`), directly to `main`

### Quality Standards
- `cd ui && npm run build` must pass (TypeScript + build)
- `ruff check .` must pass (Python linting)
- No hardcoded paths — use `Path.home() / ".autoforge"` for global, `project_dir / ".autoforge"` for project
- All UI must work with existing themes (no custom colors, use semantic tokens)
- WebSocket events must follow existing `{"type": "...", "data": {...}}` pattern

---

## PRODUCT LAYER

### Vision

**A work order queue where you set up all your tasks ahead of time, hit go, and walk away.** Different projects, different repos, different objectives — the factory processes them sequentially like train cars on a track. Each "car" is a self-contained work order: project, mode, objective, everything the agent needs.

The owner has 60-70 software projects. Today it's one-at-a-time, hands-on. The Train makes it: load up 10 tasks, hit start, go to sleep, wake up to completed work.

### Target User
- Non-coder owner with 60-70 software projects
- Needs overnight autonomous processing across multiple repos
- Already has factory mode working for single-project continuous runs
- Wants to fill out "work orders" with project + mode + objective, then walk away

### Core Concept

```
[Task 1: Bug Fix]  →  [Task 2: QA Sweep]  →  [Task 3: Add Feature]  →  [Task 4: Refactor]
  repo: AppA             repo: AppB              repo: AppA              repo: AppC
  mode: bug_fix          mode: qa_sweep          mode: add_feature       mode: refactor
  est: ~1 session        est: ~3 sessions        est: ~2 sessions        est: ~4 sessions
  STATUS: RUNNING        STATUS: QUEUED          STATUS: QUEUED          STATUS: QUEUED
```

### Key Design Decisions
1. **Queue Executor sits ABOVE Factory Controller** — don't merge them. Factory = single-project multi-session. Queue = multi-project sequencing.
2. **Tasks are self-contained work orders** — each has everything the agent needs. No cross-task dependencies.
3. **One task runs at a time** — sequential, not parallel. Avoids rate limit conflicts.
4. **JSON first, SQLite later** — start simple with `~/.autoforge/task_queue.json`.
5. **Rate limit handling stays in Factory Controller** — Queue Executor just waits for the factory to finish.
6. **Management agent is optional** — system works without it using presets + objectives. Management agent is a future enhancement.

### Use Cases
1. **Bug Fix Campaign** — Queue 15 bug fixes across 8 repos, factory works through them overnight
2. **QA Blitz** — Queue QA sweeps for all 20 apps, systematic testing one by one
3. **Feature Rollout** — Same feature across 5 apps (e.g. dark mode), each with its own task
4. **Mixed Batch** — 3 bug fixes, 2 QA sweeps, 1 refactor — different repos, different modes
5. **Morning Review** — Wake up, check completion report, see what got done, what failed

---

## SPECS LAYER

### Data Model: Task

```python
# Stored in ~/.autoforge/task_queue.json as a list
{
  "tasks": [
    {
      "id": "uuid-string",
      "position": 1,                    # Queue order (drag-reorderable)
      "status": "queued",               # queued | running | completed | failed | paused
      "project_name": "my-app",         # From project registry
      "project_dir": "/path/to/my-app", # Resolved from registry
      "factory_preset": "bug_fix",      # qa_sweep | bug_fix | add_feature | refactor | custom
      "objective": "Fix the login...",   # Full objective text
      "model": "claude-opus-4-6",       # Model to use for this task
      "yolo_mode": false,               # YOLO mode for this task
      "estimated_sessions": 2,          # Manual or auto estimate
      "actual_sessions": 0,             # Tracked during execution
      "created_at": "2026-03-04T...",
      "started_at": null,
      "completed_at": null,
      "completion_summary": null,       # From final handoff
      "handoff_history": [],            # All handoffs within this task
      "error": null,                    # Error message if failed
      "notes": ""                       # Additional context
    }
  ],
  "queue_status": "idle",               # idle | running | paused
  "started_at": null,
  "completed_at": null
}
```

### API Endpoints

All endpoints on a new router: `server/routers/task_queue.py`
Prefix: `/api/task-queue`

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/task-queue` | — | Get full queue (all tasks + queue_status) |
| `POST` | `/api/task-queue/tasks` | `TaskCreateRequest` | Add a new task to the queue |
| `PUT` | `/api/task-queue/tasks/{task_id}` | `TaskUpdateRequest` | Edit a task (objective, preset, etc.) |
| `DELETE` | `/api/task-queue/tasks/{task_id}` | — | Remove a task from the queue |
| `POST` | `/api/task-queue/tasks/reorder` | `ReorderRequest` | Reorder tasks (drag-drop) |
| `POST` | `/api/task-queue/start` | — | Start processing the queue |
| `POST` | `/api/task-queue/stop` | — | Stop the queue (finish current task) |
| `POST` | `/api/task-queue/pause` | — | Pause (can resume later) |
| `POST` | `/api/task-queue/resume` | — | Resume a paused queue |
| `GET` | `/api/task-queue/report` | — | Get completion report for last run |

#### Pydantic Models

```python
class TaskCreateRequest(BaseModel):
    project_name: str
    factory_preset: str = "custom"
    objective: str = ""
    model: str = "claude-opus-4-6"
    yolo_mode: bool = False
    estimated_sessions: Optional[int] = None
    notes: str = ""

class TaskUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    factory_preset: Optional[str] = None
    objective: Optional[str] = None
    model: Optional[str] = None
    yolo_mode: Optional[bool] = None
    estimated_sessions: Optional[int] = None
    notes: Optional[str] = None

class ReorderRequest(BaseModel):
    task_ids: list[str]  # Ordered list of task IDs in new position order

class QueueResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
```

### Queue Executor Service

`server/services/queue_executor.py` — the orchestrator above Factory Controller.

```python
class QueueExecutor:
    """Processes tasks from the queue sequentially."""

    async def start(self):
        """Start processing the queue from the first queued task."""
        # 1. Load queue
        # 2. Find first task with status=queued
        # 3. Set queue_status = "running"
        # 4. Call _execute_task(task)
        # 5. On completion, mark task done, pull next
        # 6. On queue empty, set queue_status = "idle", generate report

    async def stop(self):
        """Stop the queue after current task finishes."""
        # Set a flag so after current task completes, we don't pull next

    async def pause(self):
        """Pause the queue (can resume later)."""

    async def resume(self):
        """Resume a paused queue from where it left off."""

    async def _execute_task(self, task: dict):
        """Execute a single task using Factory Controller."""
        # 1. Resolve project_dir from registry
        # 2. Get or create FactoryController for this project
        # 3. Start factory with task's preset + objective + model
        # 4. Wait for factory to complete (listen for factory_complete event)
        # 5. Capture completion_summary from factory state
        # 6. Mark task as completed or failed

    async def _on_task_complete(self, task: dict):
        """Called when a task finishes."""
        # 1. Update task status + completion_summary
        # 2. Save queue
        # 3. Broadcast WebSocket event
        # 4. Pull next queued task, or finish if empty

    def _generate_report(self) -> dict:
        """Generate completion report for the queue run."""
        # Summary: X completed, Y failed, Z skipped
        # Per-task: summary, sessions used, duration
        # Total: sessions, time elapsed
```

### WebSocket Events

Follow existing pattern in `server/websocket.py`:

| Event Type | When | Data |
|---|---|---|
| `queue_started` | Queue begins processing | `{task_count}` |
| `queue_task_started` | A task begins executing | `{task_id, project_name, preset, position}` |
| `queue_task_completed` | A task finishes | `{task_id, project_name, status, summary}` |
| `queue_task_failed` | A task fails | `{task_id, project_name, error}` |
| `queue_completed` | All tasks done | `{completed, failed, total, report}` |
| `queue_paused` | Queue was paused | `{current_task_id}` |
| `queue_stopped` | Queue was stopped | `{completed_so_far}` |

### UI Components

#### TaskQueuePanel (new component)

Lives in `ui/src/components/factory/TaskQueuePanel.tsx`. Displayed below the FactoryPanel when there are queued tasks, or as a tab/section.

```
┌─────────────────────────────────────────────────┐
│  TASK QUEUE                            [+ Add]  │
├─────────────────────────────────────────────────┤
│  ▶ 1. Fix login bug         AppA    🐛 Bug Fix │
│      "Submit button does nothing..."  ~1 sess   │
│      [Edit] [Remove]                            │
│                                                  │
│  ⏳ 2. QA sweep             AppB    🔍 QA      │
│      "Full button + function test..." ~3 sess   │
│      [Edit] [Remove]                            │
│                                                  │
│  ⏳ 3. Add dark mode        AppA    ✨ Feature  │
│      "Implement dark mode toggle..." ~2 sess    │
│      [Edit] [Remove]                            │
│                                                  │
│  ⏳ 4. Clean up spaghetti   AppC    🧹 Refactor│
│      "Reverse engineer the auth..." ~4 sess     │
│      [Edit] [Remove]                            │
├─────────────────────────────────────────────────┤
│  [▶ Start Queue]  [⏸ Pause]  Est: ~10 sessions │
└─────────────────────────────────────────────────┘
```

Features:
- Drag-to-reorder tasks (change position)
- Each task row: project name, preset icon, objective preview (truncated), session estimate
- Edit button opens task form modal
- Remove button (with confirmation)
- Start/Stop/Pause controls in footer
- Status badges: running (blue pulse), queued (gray), completed (green), failed (red)

#### TaskFormModal (new component)

Modal for creating or editing a task. Lives in `ui/src/components/factory/TaskFormModal.tsx`.

Fields:
1. **Project** — dropdown of registered projects (from `/api/projects` existing endpoint)
2. **Mode** — preset pills (same style as FactoryPanel mode pills)
3. **Objective** — textarea, pre-filled with preset base prompt when mode selected
4. **Model** — dropdown (claude-opus-4-6, claude-sonnet-4-6)
5. **YOLO Mode** — toggle
6. **Estimated Sessions** — number input (optional)
7. **Notes** — textarea for additional context
8. **Save / Cancel** buttons

#### QueueReportModal (new component)

Modal showing completion report after queue finishes. `ui/src/components/factory/QueueReportModal.tsx`.

Shows:
- Summary line: "5 completed, 1 failed, 0 skipped"
- Per-task: project, preset, status (checkmark/X), completion_summary, sessions used
- Total time elapsed
- Failed tasks highlighted with error details

### React Hooks

In `ui/src/hooks/useTaskQueue.ts`:

```typescript
// Fetch the full queue
useTaskQueue()              // GET /api/task-queue, polls every 5s when queue running

// Task CRUD
useCreateTask()             // POST /api/task-queue/tasks
useUpdateTask()             // PUT /api/task-queue/tasks/{id}
useDeleteTask()             // DELETE /api/task-queue/tasks/{id}
useReorderTasks()           // POST /api/task-queue/tasks/reorder

// Queue controls
useStartQueue()             // POST /api/task-queue/start
useStopQueue()              // POST /api/task-queue/stop
usePauseQueue()             // POST /api/task-queue/pause
useResumeQueue()            // POST /api/task-queue/resume

// Report
useQueueReport()            // GET /api/task-queue/report
```

### API Client Functions

In `ui/src/lib/api.ts`, add:

```typescript
// Task Queue API
export interface QueueTask { ... }  // Matches the JSON schema above
export interface QueueState { tasks: QueueTask[]; queue_status: string; ... }

export const taskQueueGet = () => fetchJSON<QueueState>('/api/task-queue')
export const taskQueueCreateTask = (data: TaskCreateRequest) => fetchJSON('/api/task-queue/tasks', { method: 'POST', body: data })
export const taskQueueUpdateTask = (taskId: string, data: TaskUpdateRequest) => fetchJSON(`/api/task-queue/tasks/${taskId}`, { method: 'PUT', body: data })
export const taskQueueDeleteTask = (taskId: string) => fetchJSON(`/api/task-queue/tasks/${taskId}`, { method: 'DELETE' })
export const taskQueueReorder = (taskIds: string[]) => fetchJSON('/api/task-queue/tasks/reorder', { method: 'POST', body: { task_ids: taskIds } })
export const taskQueueStart = () => fetchJSON('/api/task-queue/start', { method: 'POST' })
export const taskQueueStop = () => fetchJSON('/api/task-queue/stop', { method: 'POST' })
export const taskQueuePause = () => fetchJSON('/api/task-queue/pause', { method: 'POST' })
export const taskQueueResume = () => fetchJSON('/api/task-queue/resume', { method: 'POST' })
export const taskQueueReport = () => fetchJSON('/api/task-queue/report')
```

---

## IMPLEMENTATION PHASES

Each phase is designed to be completed by ONE agent session staying under 50% context window. The agent reads this PRD (~15% context), reads existing code (~10-15% context), implements (~15-20% context), leaving buffer.

---

### Phase 1: Task Queue Data Model + Storage Service

**Goal:** Create the backend data layer — JSON storage, CRUD operations, no API endpoints yet.

**Files to create:**
- `server/services/task_queue_store.py` — TaskQueueStore class

**What to build:**
1. `TaskQueueStore` class with methods:
   - `load()` → reads `~/.autoforge/task_queue.json`, returns queue dict
   - `save(data)` → writes queue dict to JSON (safe I/O: mkdir, handle corrupt)
   - `add_task(task_data)` → create task with UUID, append to list, auto-position
   - `update_task(task_id, updates)` → update fields on a task
   - `delete_task(task_id)` → remove task, re-number positions
   - `reorder_tasks(task_ids)` → set positions from ordered ID list
   - `get_task(task_id)` → get single task by ID
   - `get_next_queued()` → get first task with status="queued" (lowest position)
   - `mark_running(task_id)` → set status=running, started_at=now
   - `mark_completed(task_id, summary)` → set status=completed, completion_summary, completed_at
   - `mark_failed(task_id, error)` → set status=failed, error message
   - `get_queue_status()` → return queue_status field
   - `set_queue_status(status)` → update queue_status (idle/running/paused)

2. All methods are synchronous (file I/O). Called from async endpoints via `await asyncio.to_thread()` if needed, or just called directly since JSON reads are fast.

3. Default empty queue structure on first load:
```json
{
  "tasks": [],
  "queue_status": "idle",
  "started_at": null,
  "completed_at": null,
  "total_completed": 0,
  "total_failed": 0
}
```

**Pattern to follow:** Look at how `server/services/rate_limit_logger.py` does safe JSON file I/O with `_load_log()` and `_save_log()`. Same pattern: load, modify, save, handle errors.

**Estimated context usage:** ~30% (one new file, reads rate_limit_logger.py for pattern)

---

### Phase 2: Task Queue REST API

**Goal:** REST endpoints for task CRUD and queue controls. No execution yet — just managing the queue.

**Files to create:**
- `server/routers/task_queue.py` — REST router

**Files to modify:**
- `server/routers/__init__.py` — register `task_queue_router`
- `server/main.py` — include `task_queue_router`

**What to build:**
1. All 10 endpoints from the API table above
2. Pydantic models: `TaskCreateRequest`, `TaskUpdateRequest`, `ReorderRequest`, `QueueResponse`
3. Each endpoint calls `TaskQueueStore` methods
4. Project name validation: check `get_project_dir(project_name)` exists when creating/updating tasks
5. Queue start/stop/pause/resume just set the `queue_status` field (actual execution is Phase 4)

**Pattern to follow:** `server/routers/factory.py` — same structure: router prefix, Pydantic models, response wrapper, `_resolve_project` helper.

**Estimated context usage:** ~35% (new router file + 2 modifications + reads existing patterns)

---

### Phase 3: Task Queue UI — Queue List + Task Form

**Goal:** React components for viewing, adding, editing, and reordering tasks.

**Files to create:**
- `ui/src/components/factory/TaskQueuePanel.tsx` — queue list view
- `ui/src/components/factory/TaskFormModal.tsx` — create/edit task modal
- `ui/src/hooks/useTaskQueue.ts` — React Query hooks

**Files to modify:**
- `ui/src/lib/api.ts` — add queue API functions + TypeScript interfaces
- `ui/src/components/factory/FactoryPanel.tsx` — render TaskQueuePanel below factory controls

**What to build:**
1. **TaskQueuePanel** — list of tasks with:
   - Task rows: project name, preset icon/badge, objective preview (truncated to 1-2 lines), session estimate
   - Status badges: queued (gray), running (blue pulse), completed (green check), failed (red X)
   - [+ Add] button in header → opens TaskFormModal
   - [Edit] button per task → opens TaskFormModal in edit mode
   - [Remove] button per task (with inline confirmation)
   - Footer: [Start Queue] / [Stop] / [Pause] buttons + total session estimate
   - Drag-to-reorder (use HTML5 drag-and-drop or a simple up/down arrow buttons)

2. **TaskFormModal** — modal overlay with form:
   - Project dropdown (fetch from `/api/projects`)
   - Mode pills (same `PRESET_ICONS` pattern from FactoryPanel)
   - Objective textarea (pre-fill from preset when selected)
   - Model dropdown
   - YOLO toggle
   - Session estimate (number input)
   - Notes textarea
   - Save / Cancel

3. **useTaskQueue hooks** — following `useFactory.ts` patterns:
   - `useTaskQueue()` — polls queue status (5s when running, 10s idle)
   - `useCreateTask()`, `useUpdateTask()`, `useDeleteTask()` — mutations that invalidate queue query
   - `useStartQueue()`, `useStopQueue()`, etc. — mutations

4. **API functions** — in `api.ts`, matching the endpoint table

5. **FactoryPanel integration** — render `<TaskQueuePanel />` below the existing factory panel content

**Pattern to follow:** `FactoryPanel.tsx` for Tailwind styling, status badges, preset icons. `useFactory.ts` for hook structure.

**Estimated context usage:** ~40% (3 new files + 2 modifications + reads existing UI patterns)

---

### Phase 4: Queue Executor — Sequential Task Processing

**Goal:** The brain — processes tasks from the queue, switching projects, starting factory for each.

**Files to create:**
- `server/services/queue_executor.py` — QueueExecutor class

**Files to modify:**
- `server/routers/task_queue.py` — wire start/stop/pause/resume to executor
- `server/websocket.py` — add queue WebSocket events (if not already broadcasting)

**What to build:**
1. **QueueExecutor** class:
   - `start()` — loads queue, finds first queued task, begins processing loop
   - `stop()` — sets stop flag, lets current task finish, then stops
   - `pause()` / `resume()` — pause between tasks
   - `_execute_task(task)` — the core:
     1. Resolve `project_dir` from `registry.get_project_dir(task["project_name"])`
     2. Get `FactoryController` via `get_factory_controller(project_name, project_dir)`
     3. Register a WebSocket callback to listen for `factory_complete` event
     4. Call `controller.start(mode="continuous", model=task["model"], factory_preset=task["factory_preset"], objective=task["objective"], yolo_mode=task["yolo_mode"])`
     5. Wait for factory to complete (asyncio.Event or poll factory status)
     6. Capture completion summary from `controller.get_status()`
     7. Mark task completed or failed in store
   - `_on_task_complete()` — update store, broadcast WS event, pull next task
   - `_generate_report()` — summary of completed run

2. **Repo switching** — between tasks:
   - Factory controller for previous project stops cleanly (already handled by `controller.stop()` or natural completion)
   - New controller created for next project via `get_factory_controller(new_name, new_dir)`
   - This is already supported — each project gets its own controller instance

3. **WebSocket events** — broadcast queue-level events (queue_started, queue_task_started, etc.)

4. **Wire to router** — `task_queue.py` start/stop/pause/resume endpoints call `QueueExecutor` methods

**Key detail:** The executor needs to detect when a factory finishes. Options:
- Poll `controller.get_status()` every 5s until `status == "completed"` or `status == "idle"`
- Or listen for the `factory_complete` WebSocket event
- Simplest: poll with `asyncio.sleep(5)` loop

**Pattern to follow:** `factory_controller.py` for async patterns, `_broadcast()` for WS events.

**Estimated context usage:** ~40% (new service + 2 modifications + reads factory controller)

---

### Phase 5: Completion Reports + Queue Status UI Updates

**Goal:** Completion reporting, live status updates in the UI, and queue report modal.

**Files to create:**
- `ui/src/components/factory/QueueReportModal.tsx` — completion report display

**Files to modify:**
- `server/services/queue_executor.py` — add `_generate_report()` logic, store report
- `server/routers/task_queue.py` — add GET `/report` endpoint
- `ui/src/hooks/useTaskQueue.ts` — add `useQueueReport()` hook
- `ui/src/lib/api.ts` — add `taskQueueReport()` function
- `ui/src/components/factory/TaskQueuePanel.tsx` — live status updates + report button
- `ui/src/hooks/useWebSocket.ts` — handle queue WS events for live updates

**What to build:**
1. **Report generation** in executor:
   - On queue complete, generate report dict:
     - `total`, `completed`, `failed`, `skipped` counts
     - Per-task: project, preset, status, completion_summary, sessions_used, duration
     - Overall: total sessions, total time elapsed
   - Store report in queue JSON (`last_report` field)

2. **QueueReportModal** — displays the report:
   - Summary header: "5 completed, 1 failed"
   - Task table: project | mode | status | summary | sessions
   - Failed tasks highlighted in red with error details
   - Total time and sessions at bottom
   - Close button

3. **Live UI updates:**
   - TaskQueuePanel shows running task with blue pulse
   - When a task completes, it moves to completed (green check) in real-time
   - Progress indicator: "Task 3/8 running"
   - When queue finishes, show "View Report" button → opens QueueReportModal

4. **WebSocket handling** — `useWebSocket.ts` processes queue events to update React Query cache

**Estimated context usage:** ~35% (1 new file + 5 modifications)

---

### Phase 6: Scheduling + Rate Limit Integration

**Goal:** Time-based queue scheduling (night mode) and rate limit awareness.

**Files to modify:**
- `server/services/queue_executor.py` — add scheduling logic and rate limit checks
- `server/routers/task_queue.py` — add schedule config endpoints
- `server/services/task_queue_store.py` — add schedule config storage
- `ui/src/components/factory/TaskQueuePanel.tsx` — schedule controls in UI

**What to build:**
1. **Schedule configuration** stored in queue JSON:
```json
{
  "schedule": {
    "enabled": false,
    "nighttime_start": "22:00",
    "nighttime_end": "10:00",
    "timezone": "America/Chicago",
    "nighttime_mode": "full_speed",
    "daytime_mode": "paused",
    "weekend_mode": "full_speed"
  }
}
```

2. **Schedule logic in executor:**
   - Before starting next task, check schedule
   - If daytime + daytime_mode="paused" → wait until nighttime window
   - If nighttime → full speed, handle rate limits with wait+retry
   - Weekend override
   - Use `datetime` + `zoneinfo` for timezone-aware scheduling

3. **Rate limit integration:**
   - Read `rate_limit_logger.get_daily_stats()` to understand current usage
   - If approaching predicted rate limit during daytime → pause queue
   - During nighttime → rate limits are handled by factory controller (wait + resume)
   - Basic: just respect the schedule windows. Advanced prediction is a later phase.

4. **Schedule UI:**
   - Section in TaskQueuePanel or separate settings area
   - Night start/end time pickers
   - Toggle: scheduled vs run-anytime
   - Status indicator: "Queue runs at 10:00 PM" or "Running now"

5. **API endpoints:**
   - `GET /api/task-queue/schedule` — get schedule config
   - `PUT /api/task-queue/schedule` — update schedule config

**Estimated context usage:** ~35% (4 modifications + schedule logic)

---

## SUCCESS METRICS

- Owner can queue 10+ tasks across different projects and walk away
- Queue processes overnight without intervention
- Each task's agents hand off cleanly with context preserved
- Rate limits handled gracefully (pause, wait, resume)
- Completion report tells owner exactly what got done
- UI updates in real-time as tasks progress
- Schedule window respected (no daytime processing when configured)

## OUT OF SCOPE (For Now)

- Parallel task execution across projects
- Task dependencies (task B depends on task A)
- File attachments on tasks (Phase 5 of original PRD — deferred)
- Management agent between tasks (Phase 4 of original PRD — deferred)
- Multi-user queue management
- Cloud/remote execution
- Cost tracking per task
