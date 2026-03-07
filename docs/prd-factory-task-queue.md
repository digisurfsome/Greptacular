# PRD: Factory Task Queue ("The Train")

**Status:** Draft
**Date:** 2026-03-04
**Author:** Owner + Claude (Session 6)

---

## Problem Statement

Right now, factory mode handles one project with one objective at a time. The owner has 60-70 software projects that need various fixes, features, QA sweeps, and refactors. Today the workflow is:

1. Open a project
2. Work with an agent manually
3. When done (or blocked), switch to the next project
4. Repeat

This creates a "stagnant pond" — dozens of tasks sitting around waiting because the owner can only work one at a time, and each one requires hands-on agent interaction.

## Vision

**A work order queue where you set up all your tasks ahead of time, hit go, and walk away.** Each task is a self-contained "train car" that the factory processes sequentially — different projects, different repos, different objectives, all running autonomously through the night or while you're doing other work.

> "It's one thing to have a factory. But when you haven't had a factory before to make lots of software, you have lots of edits across lots of different softwares."

## Core Concept: The Train

```
[Task 1: Bug Fix]  →  [Task 2: QA Sweep]  →  [Task 3: Add Feature]  →  [Task 4: Refactor]
  repo: AppA             repo: AppB              repo: AppA              repo: AppC
  mode: bug_fix          mode: qa_sweep          mode: add_feature       mode: refactor
  est: ~1 session        est: ~3 sessions        est: ~2 sessions        est: ~4 sessions
  STATUS: RUNNING        STATUS: QUEUED          STATUS: QUEUED          STATUS: QUEUED
```

Each "train car" (task) contains:
- **Project/Repo** — which software to work on (dropdown from registered projects)
- **Mode Preset** — QA Sweep, Bug Fix, Add Feature, Refactor, Custom
- **Objective** — the detailed description of what needs doing
- **Attachments** — files, links, screenshots, error logs
- **Estimated effort** — rough guess at session count (can be auto-estimated by management agent)
- **Priority** — drag to reorder the queue

## Architecture

### 1. Task Queue (Data Model)

```
TaskQueue (stored in ~/.autoforge/task_queue.json or SQLite)
├── id: uuid
├── position: int (queue order, drag-reorderable)
├── status: queued | running | completed | failed | paused
├── project_name: string (from project registry)
├── project_dir: path (resolved from registry)
├── factory_preset: string (qa_sweep, bug_fix, add_feature, refactor, custom)
├── objective: string (the full objective text)
├── attachments: list[{name, path, type}] (optional files/links)
├── estimated_sessions: int | null (auto or manual estimate)
├── actual_sessions: int (tracked during execution)
├── created_at: datetime
├── started_at: datetime | null
├── completed_at: datetime | null
├── completion_summary: string | null (from final handoff)
├── handoff_history: list[handoff_data] (all handoffs within this task)
└── error: string | null (if failed)
```

### 2. Queue Executor

The Queue Executor replaces the current single-project factory controller as the top-level orchestrator:

```
Queue Executor
├── Pulls next task from queue (status=queued, lowest position)
├── Switches active project context (repo, features.db, etc.)
├── Starts Factory Controller for that project with task's preset + objective
├── Factory runs agents until objective is done (multi-session handoffs)
├── On completion → marks task done, pulls next task
├── On failure → marks failed, optionally skips or retries, pulls next
├── On rate limit → pauses, waits, resumes (same as current factory)
└── Respects scheduling windows (daytime vs nighttime rules)
```

**Key design decision:** The Factory Controller stays as-is for single-project orchestration. The Queue Executor is a layer above it that manages the sequence of projects.

### 3. Task Creation UI ("Work Order Form")

The current Factory panel objective textarea becomes one task. A new queue view shows all tasks:

```
┌─────────────────────────────────────────────────┐
│  FACTORY TASK QUEUE                    [+ Add]  │
├─────────────────────────────────────────────────┤
│  ▶ 1. Fix login bug         AppA    🐛 Bug Fix │
│      "Submit button does nothing..."  ~1 sess   │
│                                                  │
│  ⏳ 2. QA sweep             AppB    🔍 QA      │
│      "Full button + function test..." ~3 sess   │
│                                                  │
│  ⏳ 3. Add dark mode        AppA    ✨ Feature  │
│      "Implement dark mode toggle..." ~2 sess    │
│                                                  │
│  ⏳ 4. Clean up spaghetti   AppC    🧹 Refactor│
│      "Reverse engineer the auth..." ~4 sess     │
├─────────────────────────────────────────────────┤
│  [▶ Start Queue]  [⏸ Pause]  Est: ~10 sessions │
└─────────────────────────────────────────────────┘
```

**Work order form fields:**
1. **Project** — dropdown of registered projects (changes the repo context)
2. **Mode** — preset pills (QA Sweep, Bug Fix, Add Feature, Refactor, Custom)
3. **Objective** — textarea with preset base prompt pre-filled, editable
4. **Attachments** — drag-drop zone for files, screenshots, error logs
5. **Notes** — any additional context (links, reproduction steps, etc.)
6. **Estimated sessions** — auto-calculated or manual override

### 4. Repo Switching

When the Queue Executor moves to the next task:

1. Current factory controller shuts down cleanly
2. Queue Executor resolves new project from registry
3. New factory controller starts with new project dir
4. Agent subprocess spawns in the new project directory
5. All MCP tools (feature tracking, preview, etc.) point to new project

This is already supported because `get_factory_controller(project_name, project_dir)` creates a controller per project. The Queue Executor just calls them in sequence.

### 5. Rate Limit Intelligence

**Current behavior:** Factory waits on rate limit, then resumes.

**Enhanced behavior for queue:**
- Track rate limit windows historically (when they hit, how long they last)
- Predict upcoming windows based on usage patterns
- **Daytime rules:** Pause queue during predicted rate limit windows so owner can use agents manually
- **Nighttime rules:** Queue runs through rate limits (wait and retry automatically)
- Configurable schedule: "Run queue from 10pm to 8am" or "Run anytime"
- If a 5-hour window hits, queue pauses and resumes after cooldown

### 6. Management Agent (Future Enhancement)

A lightweight management agent that runs between tasks to:
- **Estimate effort** — read the objective, look at the project, estimate how many sessions it'll take
- **Optimize ordering** — put quick fixes first, long refactors last
- **Assess completion** — after a task's agents finish, verify the objective was actually met
- **Adjust guidance** — if a task is simpler than expected, tell the agent "you have plenty of context budget, be thorough"
- **Generate summaries** — create a completion report for the owner to review

The management agent runs at ~5% context cost per task, so it's cheap overhead for significantly smarter orchestration.

**Without management agent:** Each task gets the standard preset prompt + objective + handoff template. The agent manages its own context budget using the hardcoded thresholds. This works fine — the management agent is an optimization, not a requirement.

### 7. Completion & Reporting

When a task completes:
- Final handoff summary is saved as the task's completion_summary
- Git commits are auto-created (if auto_commit enabled)
- Owner gets a notification (if notifications enabled)
- Task status updates in the queue UI (green checkmark)

When the entire queue completes:
- Summary report generated: "5 tasks completed, 1 failed, 0 skipped"
- Each task's completion summary listed
- Failed tasks highlighted with error details
- Total sessions used, total time elapsed

## Implementation Phases

### Phase 1: Queue Data Model + Basic UI
- TaskQueue model (JSON file or SQLite)
- Queue list view in Factory panel (below the current objective area)
- Add/edit/delete/reorder tasks
- Each task has: project, preset, objective
- No execution yet — just the queue management UI

### Phase 2: Queue Executor
- New service: `server/services/queue_executor.py`
- Processes tasks sequentially
- Uses existing FactoryController per project
- Repo switching between tasks
- Status tracking + WebSocket events
- Start/stop/pause queue controls

### Phase 3: Scheduling & Rate Limit Intelligence
- Time-based scheduling (run queue during specific hours)
- Rate limit window prediction from historical data
- Daytime/nighttime behavior rules
- Pause/resume around predicted windows

### Phase 4: Management Agent
- Lightweight agent that estimates effort per task
- Runs between tasks for assessment
- Generates completion reports
- Optimizes queue ordering

### Phase 5: Attachments & Rich Context
- File attachments per task (screenshots, logs, docs)
- Link attachments (URLs to issues, PRs, etc.)
- Attachments injected into agent prompt context

## Key Design Decisions

1. **Queue Executor sits above Factory Controller** — don't merge them. Factory handles single-project multi-session. Queue handles multi-project sequencing.

2. **Tasks are self-contained work orders** — each task has everything the agent needs. No cross-task dependencies (keeps it simple).

3. **Management agent is optional** — the system works without it using preset prompts and fixed thresholds. Management agent is a Phase 4 optimization.

4. **Rate limit handling stays in Factory Controller** — Queue Executor just waits for the factory to finish (whether that includes rate limit waits or not).

5. **Storage: JSON first, SQLite later** — start with `~/.autoforge/task_queue.json` for simplicity. Migrate to SQLite if we need querying/filtering.

6. **One task runs at a time** — no parallel task execution across projects. Parallel agents within a single task (existing feature) is fine, but queue is sequential. This avoids rate limit conflicts.

## Success Metrics

- Owner can queue 10+ tasks across different projects and walk away
- Queue processes overnight without intervention
- Each task's agents hand off cleanly with context preserved
- Rate limits handled gracefully (pause, wait, resume)
- Completion report tells owner exactly what got done

## Out of Scope (for now)

- Parallel task execution across projects
- Task dependencies (task B depends on task A)
- Multi-user queue management
- Cloud/remote execution
- Cost tracking per task
