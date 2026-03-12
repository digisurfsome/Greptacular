# PRD: CLI Scripter v2 — Live Build Dashboard, Terminal Integration, Build Storage

> **Status:** Design — ready to build
> **Prerequisite:** CLI Scripter v1 (current) working and field-tested with 1-2 real builds
> **Context:** These are the features that didn't fit in the initial CLI Scripter sessions

---

## Overview

The CLI Scripter currently generates scripts and lets you copy commands. What's missing is the **live experience** — watching builds run, managing saved builds, and controlling the pipeline from the UI instead of juggling terminal windows.

Three systems, in build order:

1. **Live Build Dashboard** — watch builds run from inside the page
2. **Terminal Integration** — start builds, monitor progress, copy commands
3. **Build Storage** — save, recall, queue, and reorder build configs

---

## System 1: Live Build Dashboard (5/10 difficulty)

### What It Does

Adds a top-of-page dashboard strip that appears once a build starts. Shows which phase is active, estimated vs actual tokens, and a phase-by-phase progress indicator.

### Phase Progress Bar (top of page)

```
┌──────────────────────────────────────────────────────────────────────┐
│  🔶 Building: My SaaS App                                    46m 12s │
│                                                                      │
│  [Architect] ──▶ [Phase 1] ──▶ [Phase 2] ──▶ [Phase 3] ──▶ [Verify] │
│     ✅ 2m       ✅ 12m       🔵 8m...       ⬜ --          ⬜ --     │
│                                                                      │
│  Tokens: 43K / ~85K est.  │  Phase 2 of 5  │  ETA: ~25 min          │
└──────────────────────────────────────────────────────────────────────┘
```

**Phase indicators:**
- ⬜ Gray = pending
- 🔵 Cyan pulse = active (currently running)
- ✅ Green = completed successfully
- 🔴 Red = failed

**Live data sources:**
- Phase status: parse the CLI output for phase markers (deterministic — look for "Phase X complete" patterns)
- Token count: read from the CLI's token usage output line at session end
- Timing: simple wall clock from start to now

### How It Gets Data

Two approaches (pick during build):

**Option A: Log file polling (3/10 difficulty)**
- The `run_all.sh` script already writes stdout to a log file
- Backend endpoint polls the log file every 5 seconds
- Frontend polls the backend endpoint
- Deterministic: just reading a file, no LLM involved

**Option B: WebSocket streaming (5/10 difficulty)**
- Backend spawns the build as a subprocess
- Stdout/stderr piped to a WebSocket
- Frontend renders in real-time
- More responsive but more complex

**Recommendation:** Start with Option A. It works, it's simple, and the 5-second delay doesn't matter for builds that take 10+ minutes per phase.

### API Endpoints

```
POST /api/cli-scripter/start-build     — Start run_all.sh as subprocess
GET  /api/cli-scripter/build-status    — Current phase, tokens, timing
GET  /api/cli-scripter/build-log       — Last N lines of build output
POST /api/cli-scripter/stop-build      — Kill the subprocess
```

### Implementation Phases

**Phase 1: Backend process manager (3/10)**
- Subprocess spawner for run_all.sh
- PID tracking, log file capture
- Status endpoint (running/stopped/completed/failed)
- Stop endpoint (SIGTERM → SIGKILL)

**Phase 2: Progress parser (2/10)**
- Regex parser for CLI output patterns:
  - `"Phase X complete"` → mark phase done
  - `"Total tokens: X"` → update token count
  - `"Error:"` or non-zero exit → mark phase failed
- This is 100% deterministic — pure Python regex, no LLM

**Phase 3: Dashboard UI (3/10)**
- Top strip component (sticky, only shows during active build)
- Phase indicator circles with connecting lines
- Token counter, timer, ETA estimate
- Start/Stop buttons

---

## System 2: Terminal Integration (4/10 difficulty)

### The Problem

The user juggles between the CLI Scripter page and terminal windows. They need to:
1. Start a build (currently: copy command, switch to terminal, paste, enter)
2. Monitor progress (currently: watch terminal scroll)
3. Check specific phases (currently: scroll through terminal history)

### Embedded Terminal Panels

Two panels, one on each side of the page header area, that show live build output.

```
┌─────────────────┬──────────────────────────┬─────────────────┐
│  BUILD LOG       │     CLI Scripter          │  PHASE STATUS   │
│                 │     [Dashboard strip]      │                 │
│ > Phase 1...    │                            │ ✅ Architect    │
│ > Implementing  │     [Form sections]        │ ✅ Phase 1      │
│ > auth module   │                            │ 🔵 Phase 2     │
│ > Running lint  │                            │ ⬜ Phase 3      │
│ > ...           │                            │ ⬜ Verify       │
│                 │                            │ ⬜ Cartographer │
│ [Auto-scroll ↓] │                            │                 │
└─────────────────┴──────────────────────────┴─────────────────┘
```

**Left panel: Build Log**
- Streams the raw CLI output (tail -f style)
- Auto-scrolls to bottom
- Can be collapsed/hidden
- Shows last ~200 lines

**Right panel: Phase Status**
- Compact phase list with status icons
- Per-phase timing and token count
- Click a completed phase to see its summary

### CLI Commands with One-Click Copy

Every generated script gets a row with:
```
[📋] cd /my-project && bash scripts/cli-scripter/phase1.sh
```
One click copies the full command. Already partially built — just needs polish.

### "Can't Auto-Paste Into External Terminal"

Correct — browsers can't inject text into external applications. The best we can do:
1. **Copy button** (already built) — copies command to clipboard
2. **Embedded terminal** — if AutoForge already has a terminal component (it does — `Terminal.tsx` with xterm.js), we could potentially reuse it for the CLI Scripter page
3. **Start from UI** — the Start Build button triggers the backend to run the subprocess, so the user doesn't need to paste anything

### Auto-Refresh Interval

The user mentioned wanting 1-minute or 5-minute refresh for the status view. Add a toggle:
```
Refresh: [15s] [30s] [1m] [5m] [Off]
```
Default: 30 seconds. This controls how often the frontend polls `/api/cli-scripter/build-status`.

### Implementation Phases

**Phase 4: Reuse existing Terminal component (3/10)**
- Import `Terminal.tsx` / xterm.js component
- Feed it the build log stream
- Collapsible left panel

**Phase 5: Phase status sidebar (2/10)**
- Right panel with phase list
- Powered by the progress parser from System 1
- Click-to-expand completed phases

**Phase 6: Refresh interval selector (1/10)**
- Simple toggle component
- Controls poll interval for status endpoint

---

## System 3: Build Storage & Queue Management (5/10 difficulty)

### The Problem

The user configures a build (app name, rules, features, roles, phase rules) — but where does it go? Right now it's just form state that disappears on page reload. They need:

1. **Save a build config** — "I made this, save it for later"
2. **Load a saved config** — "Pull up the one I made yesterday"
3. **Queue management** — reorder, remove, add from saved builds
4. **Build history** — "Show me what I've already built"

### Data Model

```sql
-- Saved build configurations
CREATE TABLE build_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- "My SaaS App"
    created_at TEXT NOT NULL,              -- ISO 8601
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'draft',           -- draft | queued | building | completed | failed
    config_json TEXT NOT NULL,             -- Full form state as JSON
    scripts_dir TEXT,                      -- Path where scripts were written
    project_dir TEXT,
    total_tokens_used INTEGER,
    build_duration_seconds INTEGER,
    phase_count INTEGER,
    notes TEXT
);

-- Build queue (ordered list of configs to run)
CREATE TABLE build_queue (
    position INTEGER PRIMARY KEY,          -- 1, 2, 3... (reorderable)
    config_id INTEGER NOT NULL REFERENCES build_configs(id),
    added_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    status TEXT DEFAULT 'pending'          -- pending | running | completed | failed | skipped
);
```

### UI: Build Library

A sidebar or modal that shows saved builds:

```
┌─────────────────────────────────────┐
│  📁 Saved Builds                     │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 🟢 My SaaS App               │   │
│  │    Built Mar 12 • 4 phases    │   │
│  │    [Load] [Queue] [Delete]    │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ 📝 SEO Dashboard (draft)      │   │
│  │    Saved Mar 11 • Not built   │   │
│  │    [Load] [Queue] [Delete]    │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │ 📝 Marketing Tools (draft)    │   │
│  │    Saved Mar 10 • Not built   │   │
│  │    [Load] [Queue] [Delete]    │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Queue Management

The existing Build Queue section gets upgraded:

```
┌─────────────────────────────────────────┐
│  🔢 Build Queue                          │
│                                          │
│  1. ⏳ My SaaS App      [↑] [↓] [✕]     │
│  2. ⏳ SEO Dashboard     [↑] [↓] [✕]     │
│  3. ⏳ Marketing Tools   [↑] [↓] [✕]     │
│                                          │
│  [▶ Start Queue]  [⏸ Pause After Current] │
│                                          │
│  Estimated total: ~450K tokens • ~2.5 hrs │
└─────────────────────────────────────────┘
```

**Queue features:**
- Drag-and-drop reorder (or up/down arrows)
- Remove from queue (doesn't delete the saved config)
- Start queue = runs builds sequentially
- Pause after current = finishes the active build, then stops
- Total estimate = sum of all queued builds

### Config JSON Structure

The `config_json` field stores the FULL form state:

```json
{
  "appName": "My SaaS App",
  "appDescription": "...",
  "boilerplate": "web-supabase-stripe",
  "ruleBlocks": ["...", "...", "..."],
  "combinedRules": "...",
  "splitPhaseRules": true,
  "phase1Rules": "...",
  "phase2PlusRules": "...",
  "features": [{"id": 1, "name": "Auth", "size": "M"}, ...],
  "dependencies": "...",
  "turns": "25",
  "transition": "Auto-continue",
  "errorHandling": "Retry once then skip",
  "gitCommits": "After each feature",
  "phaseCount": "Auto",
  "agentRoles": [...],
  "includeVerification": true,
  "phaseAssignments": "...",
  "projectDir": "C:/Projects/my-app"
}
```

### API Endpoints

```
GET    /api/cli-scripter/configs              — List all saved configs
POST   /api/cli-scripter/configs              — Save new config
GET    /api/cli-scripter/configs/{id}         — Load a config
PUT    /api/cli-scripter/configs/{id}         — Update a config
DELETE /api/cli-scripter/configs/{id}         — Delete a config
GET    /api/cli-scripter/queue                — Get queue (existing, upgrade)
PUT    /api/cli-scripter/queue/reorder        — Reorder queue
POST   /api/cli-scripter/queue/start          — Start processing queue
POST   /api/cli-scripter/queue/pause          — Pause after current build
```

### Implementation Phases

**Phase 7: SQLite storage backend (2/10)**
- SQLAlchemy models for build_configs and build_queue
- CRUD endpoints
- Save/Load from form state

**Phase 8: Build Library UI (3/10)**
- Sidebar or modal component
- Save button in the form (saves current state)
- Load button (populates form from saved config)
- Delete with confirmation

**Phase 9: Queue management upgrade (3/10)**
- Reorder (up/down buttons or drag-and-drop)
- Add from library
- Start/pause queue
- Total estimate display

---

## System 4: Boilerplate Prep Integration (2/10 difficulty)

### Context

Two boilerplates exist:
- **Web-BoilerPlate-D2D** (Supabase + Stripe): `github.com/digisurfsome/Web-BoilerPlate-D2D`
- **apparence-kit-firebase** (Flutter + Firebase): `github.com/digisurfsome/apparence-kit-firebase`

When doing a **dual build** (web + mobile), these need to be merged first. That merge is ~2,500 tokens of deterministic prep work.

### What Needs Documenting

Each boilerplate needs an analysis doc:
- What features are already built
- File structure
- Database schema (Supabase tables / Firebase collections)
- API endpoints that exist
- Auth flow already implemented
- What needs connecting when merging the two

### How It Fits Into CLI Scripter

When the user selects "Full Stack (Web + Mobile)" boilerplate:
1. Show estimated prep tokens: ~2,500
2. Add a "Prep Phase 0" to the build that merges the two repos
3. This prep phase is deterministic (git clone, file moves, config edits) — no LLM needed
4. Phase 1 then starts with the merged codebase

### Implementation

**Phase 10: Boilerplate analysis docs (1/10)**
- Create `docs/boilerplate-web-d2d.md` and `docs/boilerplate-flutter-firebase.md`
- Document features, structure, schema for each
- These feed into the PRD generation prompt as context

**Phase 11: Prep phase for dual builds (2/10)**
- When "Full Stack" selected, add Phase 0 to scripts
- Phase 0 script: clone both repos, merge into project dir, update configs
- 100% deterministic — bash script, no LLM

---

## Deterministic Audit (Stripe Minions Pattern)

Per the Stripe Minions architecture, every step should be either a **robot step** (deterministic Python/bash, no LLM, no tokens) or an **agent step** (LLM required). Here's the full audit:

### Robot Steps (deterministic — no LLM)
| Step | What It Does | Current State |
|------|-------------|---------------|
| Script file writing | Write .sh files to disk | ✅ Built (backend) |
| Git repo creation | GitHub API call | ✅ Built |
| Token estimation | chars/4 math | ✅ Built |
| Phase budget math | cab ride + buffer calculation | ✅ Built |
| Build log parsing | Regex for phase markers | ❌ Not built (System 1) |
| Process management | Start/stop subprocess | ❌ Not built (System 1) |
| Config save/load | JSON to/from SQLite | ❌ Not built (System 3) |
| Queue ordering | Array reorder | ❌ Not built (System 3) |
| Boilerplate merge | Git clone + file ops | ❌ Not built (System 4) |
| Script template assembly | Variable substitution into .sh templates | ⚠️ Currently LLM — SHOULD be deterministic |

### Agent Steps (LLM required)
| Step | What It Does | Current State |
|------|-------------|---------------|
| PRD generation | Creative reasoning from description | ✅ Correct — needs LLM |
| Rule combining | Conflict resolution between rule blocks | ✅ Correct — needs LLM |
| Phase content assignment | Deciding which features go where | ✅ Correct — needs LLM |
| Code implementation | The actual build | ✅ Correct — needs LLM |
| Code review | Bug finding | ✅ Correct — needs LLM |
| Documentation | Codebase mapping | ✅ Correct — needs LLM |

### Key Fix: Script Template Assembly

Currently the "Generate Build Scripts" step calls the LLM to generate bash scripts. This is wasteful — the scripts are just templates with variables filled in. Should be:

```python
# DETERMINISTIC (Python, no LLM):
def generate_phase_script(phase_num, total_phases, model, max_turns, rules, phase_spec):
    return f"""#!/bin/bash
# Phase {phase_num} of {total_phases}
claude --model {model} --max-turns {max_turns} -p "{rules}\n\n{phase_spec}"
"""
```

This saves ~5,000 tokens per build and eliminates hallucination risk on the script structure.

---

## Build Order (all systems)

| Phase | System | What | Difficulty | Tokens Saved |
|-------|--------|------|-----------|-------------|
| 1 | System 1 | Backend process manager | 3/10 | — |
| 2 | System 1 | Progress parser (regex) | 2/10 | — |
| 3 | System 1 | Dashboard UI strip | 3/10 | — |
| 4 | System 2 | Embedded terminal panel | 3/10 | — |
| 5 | System 2 | Phase status sidebar | 2/10 | — |
| 6 | System 2 | Refresh interval selector | 1/10 | — |
| 7 | System 3 | SQLite config storage | 2/10 | — |
| 8 | System 3 | Build Library UI | 3/10 | — |
| 9 | System 3 | Queue management upgrade | 3/10 | — |
| 10 | System 4 | Boilerplate analysis docs | 1/10 | — |
| 11 | System 4 | Prep phase for dual builds | 2/10 | — |
| FIX | — | Deterministic script templates | 2/10 | ~5K/build |

Each phase is under 50% context window. Total: ~12 sessions across 1-2 weeks.
