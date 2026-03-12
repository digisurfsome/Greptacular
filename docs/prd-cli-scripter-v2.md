# PRD: CLI Scripter v2 — Full Pipeline Upgrade

> **Status:** Design — ready to build
> **Prerequisite:** CLI Scripter v1 (current) working and field-tested with 1-2 real builds
> **Context:** Everything needed to make CLI Scripter production-grade for daily use

---

## AGENT BRIEFING — READ THIS FIRST

You are implementing upgrades to the CLI Scripter page in AutoForge. This is an existing React + Python (FastAPI) application with a neobrutalism design system.

### What This Is

The CLI Scripter is a tool that generates bash scripts for building apps using Claude CLI (`claude -p`). It takes a PRD, splits it into phases, assigns agent roles (Architect, Coder, Reviewer, Verifier, Cartographer), and generates executable build scripts. The user runs those scripts to build software autonomously.

### Your Job

This PRD contains 24 implementation phases across 8 systems plus cross-cutting fixes. You will NOT build all 24 in one session. Work through them in the priority order listed in the "Recommended Build Priority" section at the bottom. Each phase is scoped to fit under 50% context window. Build as many as you can, commit after each one, and note where the next agent picks up.

### Key Files

| File | What | Lines |
|------|------|-------|
| `ui/src/pages/CliScripterPage.tsx` | Main page — most UI changes go here | ~1,976 |
| `server/routers/cli_scripter.py` | Backend API — generation, scripts, queue | ~472 |
| `ui/src/components/` | New components go here (PromptBar, RuleBlock, PhaseCard, ProjectFileBrowser, etc.) |
| `ui/src/hooks/` | New hooks go here (usePersistedState) |
| `ui/src/lib/` | Utilities go here (tokenEstimate, waveParser) |
| `server/routers/__init__.py` | Router imports — update if adding new routers |
| `server/main.py` | FastAPI app — update if adding new routers |

### How To Work

1. Read the PRD section for the phase you're building
2. Read the existing source files to understand current code patterns
3. Implement exactly what the PRD describes — the diagrams, data models, and component specs are precise and intentional
4. Match existing patterns: neobrutalism design, Tailwind CSS v4, React 19, TanStack Query, Radix UI, orange accent color scheme
5. After EVERY phase: run `cd ui && npm run build` — must pass with zero TypeScript errors
6. Commit to main after each phase with a clear message (e.g., "Phase 20: Add localStorage persistence layer")
7. If you run out of context, commit what you have and leave a note in the commit message about what's next

### What NOT To Do

- Don't restructure the page layout — make surgical additions to what exists
- Don't change the design system — match existing colors, fonts, spacing
- Don't add npm dependencies without checking if an existing package covers the need
- Don't skip the build check after each phase
- Don't try to build all 24 phases — focus on doing a few phases well rather than rushing through many

### Build Priority (work IN THIS ORDER)

1. **Phase 20-22** — Persistence + Clear buttons + Phase Assignments read-only fix *(most critical — nothing persists right now)*
2. **Phase 23** — Project directory file browser in two spots
3. **Phase 16-19** — Build Rules Library & Combiner (the biggest feature)
4. **Phase 7-9** — Build Storage & Queue (SQLite configs)
5. **Phase 12-13** — Prompt Visibility (PromptBar component)
6. **Phase 14** — Card-Based Build Estimate display
7. **Phase 15** — Parallel Wave building
8. **Phase 1-6** — Live Dashboard + Terminal Integration
9. **Phase 10-11** — Boilerplate Prep (only needed for dual builds)
10. **FIX** — Deterministic script templates (replace LLM with Python string formatting)

Start with #1. When done, move to #2. Keep going until you hit 40% context, then commit and stop.

---

## Overview

The CLI Scripter currently generates scripts and lets you copy commands. What's missing is **persistence** (nothing survives page reload), **rule management** (can't save/reuse/combine rule sets), **live monitoring** (can't watch builds from the UI), and **workflow polish** (prompts hidden, estimates unreadable, no parallel execution).

Eight systems + cross-cutting fixes, in priority order:

1. **Live Build Dashboard** — watch builds run from inside the page
2. **Terminal Integration** — start builds, monitor progress, copy commands
3. **Build Storage** — save, recall, queue, and reorder build configs
4. **Boilerplate Prep** — merge web + mobile repos for dual builds
5. **Prompt Visibility** — surface all 8 hidden prompts with lock/edit/reset
6. **Card Build Estimate** — replace unusable phase breakdown with pipeline cards
7. **Parallel Waves** — prompt-driven parallel phase execution
8. **Build Rules Library & Combiner** — named rule blocks, tags, two-way bound combiner, gate popup
9. **Cross-cutting: Persistence + Clear Buttons** — localStorage for all inputs, clear buttons everywhere

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

## System 5: Prompt Visibility & Edit Controls (3/10 difficulty)

### The Problem

The CLI Scripter has **8 prompts** that drive the entire build pipeline, but users don't know they exist. The role prompts (Architect, Coder, Reviewer, Verifier, Cartographer) are hidden inside expandable role cards. The generation prompts (PRD, Phase Split, Build Scripts) are in textareas but look like output fields, not editable inputs. Nothing says "you can change this."

Worse: all prompt edits are **lost on page reload** because they live in React state with no persistence.

### Current State

| Prompt | Where It Lives | Editable? | Discoverable? | Persisted? |
|--------|---------------|-----------|---------------|------------|
| Architect role prompt | CliScripterPage.tsx DEFAULT_AGENT_ROLES | Yes (textarea in expanded card) | No — hidden | No |
| Coder role prompt | Same | Yes | No — hidden | No |
| Reviewer role prompt | Same | Yes | No — hidden | No |
| Verifier role prompt | Same (+ template file fallback) | Yes | No — hidden | No |
| Cartographer role prompt | Same | Yes | No — hidden | No |
| PRD generation prompt | Built dynamically in generatePRD() | Yes | Barely | No |
| Phase split prompt | Built dynamically in generatePhaseSplit() | Yes | Barely | No |
| Build scripts prompt | Built dynamically in generateBuildScripts() | Yes | Barely | No |

### What It Should Look Like

Each prompt gets a **collapsible prompt bar** — a single-line strip that shows the prompt name and a lock/edit toggle. Default state: locked (read-only, collapsed). User clicks "Edit" to unlock and expand.

```
┌─────────────────────────────────────────────────────────────┐
│  📝 Architect Prompt                    [🔒 Locked] [Edit]  │
└─────────────────────────────────────────────────────────────┘

User clicks [Edit]:

┌─────────────────────────────────────────────────────────────┐
│  📝 Architect Prompt                   [🔓 Editing] [Lock]  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ You are a senior software architect. Before any     │    │
│  │ code is written, create a detailed PRD that...      │    │
│  │                                                     │    │
│  │ (editable textarea)                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  [Reset to Default]                          142 tokens     │
└─────────────────────────────────────────────────────────────┘
```

### Design Rules

1. **Default = Locked + Collapsed.** Show only the prompt name in a slim bar. No textarea visible. This keeps the page clean — most users will never edit prompts.

2. **Edit button unlocks.** Click "Edit" → bar expands to show the full prompt in an editable textarea. Border changes from zinc to orange to signal edit mode.

3. **Lock button saves.** Click "Lock" → textarea becomes read-only, bar collapses back to slim. Changes are preserved in state (and in saved configs if Build Storage is built).

4. **Reset to Default.** Small link that restores the original hardcoded prompt. Confirmation required ("Reset to default? Your changes will be lost.").

5. **Token count badge.** Each prompt bar shows its token count (chars/4) so users can see the cost of their prompt modifications.

6. **Placement:** Prompt bars appear directly under their parent section:
   - Role prompts → inside each role card (replace current hidden textarea)
   - PRD prompt → below the "Generate PRD" button
   - Phase split prompt → below the "Split into Phases" button
   - Build scripts prompt → below the "Generate Scripts" button

### Component: PromptBar

```typescript
interface PromptBarProps {
  label: string              // "Architect Prompt"
  value: string              // Current prompt text
  defaultValue: string       // Original default for reset
  onChange: (value: string) => void
  icon?: React.ReactNode     // Optional icon
}
```

Reusable across all 8 prompts. Single component, used 8 times.

### Persistence (ties into System 3: Build Storage)

When Build Storage (System 3) is built, prompt edits get saved as part of the `config_json`:

```json
{
  "prompts": {
    "architect": "You are a senior software architect...",
    "coder": "You are building Phase {phase_number}...",
    "reviewer": "You are a code reviewer...",
    "verifier": "Run full post-build verification...",
    "cartographer": "You are a technical documentat...",
    "prd_generation": null,       // null = use auto-generated default
    "phase_split": null,          // null = use auto-generated default
    "build_scripts": null         // null = use auto-generated default
  }
}
```

Until Build Storage exists, prompts live in React state (lost on reload). That's acceptable for v1 — power users who edit prompts will also save configs.

### Implementation Phases

**Phase 12: PromptBar component (2/10)**
- Build the PromptBar component (lock/edit toggle, collapsible, token count, reset)
- Integrate into role cards (replace current raw textareas)
- Integrate below generation buttons

**Phase 13: Prompt persistence in Build Storage (1/10)**
- Add `prompts` field to `config_json` in Build Storage data model
- Load/save prompt overrides with config
- Null = use default, string = use override

---

## System 6: Card-Based Build Estimate Display (2/10 difficulty)

### The Problem

The current Build Estimate "Phase Breakdown" section has phase names on the far left and token counts on the far right of the page. On a wide monitor, your eye has to travel the entire screen width to connect a label to its number. It's unusable.

### Solution: Pipeline Card Visualization

Replace the flex-row phase breakdown with a card-based pipeline where each phase is a compact card, connected with orange lines showing the flow.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Architect │───▶│ Phase 1  │───▶│ Phase 2  │───▶│ Phase 3  │───▶ ...
│  ~12K ⚡  │    │  ~85K ⚡  │    │  ~92K ⚡  │    │  ~92K ⚡  │
│   opus    │    │  sonnet  │    │  sonnet  │    │  sonnet  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Card Contents

Each card shows:
- **Phase name** (bold, top line)
- **Token estimate** (e.g., "~85K" — prominent, orange text)
- **Model** (opus/sonnet — small, muted text)

### Status Indicators (during active build)

- Gray border = pending (default)
- Cyan pulse border = currently running (uses existing `animate-pulse-neo`)
- Green border = completed successfully
- Red border = failed

### Connecting Lines

- Orange arrows (───▶) between cards
- If parallel phases exist (from dependency detection), show fork/merge:

```
                ┌──────────┐
           ───▶│ Phase 2  │───┐
          │    │  ~92K    │   │
          │    └──────────┘   │    ┌──────────┐
Phase 1 ──┤                   ├───▶│ Phase 4  │
          │    ┌──────────┐   │    └──────────┘
          │    │ Phase 3  │───┘
           ───▶│  ~92K    │
               └──────────┘
```

### Responsive Behavior

- Desktop (>1024px): Horizontal flow, cards in a row with wrapping
- Mobile (<768px): Vertical stack with downward arrows (↓)

### What Stays

Keep the 4-stat summary grid above (Phases, Active Roles, Est Total, CLI Sessions) — that part is compact and readable.

Keep the single summary line below: "Total: ~380K tokens • 6 CLI sessions • Est. 2.5 hours"

### Implementation

**Phase 14: Pipeline card component (2/10)**
- Replace the "Phase Breakdown" div (lines ~1682-1715 in CliScripterPage.tsx)
- PhaseCard component: rounded-lg, border, p-3, min-w-[120px]
- Connecting arrows: CSS pseudo-elements or inline arrow spans
- Container: flex flex-wrap gap-2 items-center
- Color scheme: bg-zinc-900/60, border-zinc-700/60, text-orange-400 for tokens

---

## System 7: Parallel Phase Building via Prompt-Driven Waves (3/10 difficulty)

### The Problem

Phases currently run strictly sequential: Phase 1 → 2 → 3 → 4. But often Phase 2 and Phase 3 have no dependencies on each other — they both only depend on Phase 1. Running them simultaneously cuts wall-clock time nearly in half.

### How It Works (Prompt-Driven, No Dependency Graph)

Instead of building a formal dependency resolution system, we let the **phase-splitting LLM** handle it. The LLM already thinks about dependencies when splitting a PRD — we just need it to **say the quiet part out loud** in a structured format.

**Step 1: Phase-split prompt already updated (DONE)**

The phase-splitting prompt now includes:
```
IMPORTANT: After splitting, state which phases can run IN PARALLEL
(no cross-dependencies) vs which must run sequentially. Format your
answer with execution waves, e.g.:
"Wave 1: [Phase 1] → Wave 2: [Phase 2, Phase 3] (parallel) → Wave 3: [Phase 4]"
```

**Step 2: LLM outputs a wave diagram in its phase plan**

The phase-split output will now include something like:

```
EXECUTION ORDER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session 1:  ┌─────────┐
            │ Phase 1  │  (setup + auth + DB)
            └────┬────┘
                 │
Session 2:  ┌────┴────┐  ┌─────────┐
            │ Phase 2  │  │ Phase 3  │  ← run in parallel
            │ (API)    │  │ (UI)     │
            └────┬────┘  └────┬────┘
                 │            │
Session 3:  ┌────┴────────────┴────┐
            │      Phase 4          │  (integration + polish)
            └──────────────────────┘

Wave 1: [Phase 1]
Wave 2: [Phase 2, Phase 3] — parallel, no cross-dependencies
Wave 3: [Phase 4] — depends on Phase 2 and Phase 3
```

**Step 3: Parse the wave structure from the LLM output**

After the phase split returns, parse the "Wave X: [...]" lines:

```typescript
// Parse wave structure from LLM phase-split output
function parseWaves(phaseOutput: string): number[][] {
  const waves: number[][] = []
  const waveRegex = /Wave\s+(\d+):\s*\[([^\]]+)\]/gi
  let match
  while ((match = waveRegex.exec(phaseOutput)) !== null) {
    const phaseNums = match[2]
      .split(',')
      .map(s => parseInt(s.replace(/[^0-9]/g, '')))
      .filter(n => !isNaN(n))
    waves.push(phaseNums)
  }
  return waves  // e.g., [[1], [2, 3], [4]]
}
```

If parsing fails (LLM didn't output wave format), fall back to sequential: `[[1], [2], [3], [4]]`

**Step 4: Generate parallel `run_all.sh`**

Current sequential script:
```bash
bash phase1_build.sh
bash phase2_build.sh
bash phase3_build.sh
bash phase4_build.sh
```

New wave-based script:
```bash
echo "=== Wave 1 ==="
bash phase1_build.sh
if [ $? -ne 0 ]; then echo "Wave 1 failed"; exit 1; fi

echo "=== Wave 2 (parallel) ==="
bash phase2_build.sh &
PID_phase2=$!
bash phase3_build.sh &
PID_phase3=$!
wait $PID_phase2
STATUS2=$?
wait $PID_phase3
STATUS3=$?
if [ $STATUS2 -ne 0 ] || [ $STATUS3 -ne 0 ]; then
  echo "Wave 2 failed (phase2=$STATUS2, phase3=$STATUS3)"
  exit 1
fi

echo "=== Wave 3 ==="
bash phase4_build.sh
```

**Step 5: Show waves in the Build Estimate card display (ties into System 6)**

The pipeline card visualization groups cards by wave:

```
Wave 1                Wave 2                    Wave 3
┌──────────┐    ┌──────────┐              ┌──────────┐
│ Phase 1  │───▶│ Phase 2  │──────┐──────▶│ Phase 4  │
│  ~85K    │    │  ~92K    │      │       │  ~92K    │
└──────────┘    └──────────┘      │       └──────────┘
                ┌──────────┐      │
                │ Phase 3  │──────┘
                │  ~92K    │
                └──────────┘
```

Parallel phases are stacked vertically within the same wave column. A bracket or merge arrow shows where they rejoin.

### Where This Plugs In

| Component | Change |
|-----------|--------|
| Phase-split prompt (CliScripterPage.tsx) | ✅ Already updated — tells LLM to output waves |
| Phase plan display (UI) | Parse and show wave groupings |
| `_generate_master_script()` (cli_scripter.py) | Generate parallel bash with `&` and `wait` |
| Build Estimate cards (System 6) | Group cards by wave, show parallel stacking |
| Build Settings (UI) | Add toggle: "Parallel phases: [On] [Off]" — default Off |

### Rate Limit Warning

Running 2+ Claude CLI sessions simultaneously burns through the 5-hour token window faster. When parallel is enabled, show:
```
⚠️ Parallel mode uses tokens ~2x faster per wall-clock hour.
```

### Safety

- Each parallel phase writes to its own log file (phase2.log, phase3.log)
- If any phase in a wave fails, subsequent waves don't start
- Toggle defaults to Off — user opts in to parallel execution
- Fall back to sequential if wave parsing fails

### Implementation

**Phase 15: Wave parsing + parallel script generation (3/10)**
- Parse "Wave X: [...]" from LLM phase-split output
- Update `_generate_master_script()` to support wave-based execution
- Add parallel toggle to Build Settings
- Update Build Estimate to show wave groupings
- Add rate limit warning when parallel is enabled

---

## System 8: Build Rules Library & Combiner (5/10 difficulty)

### The Problem

Build rules are the foundation of every build — they tell the agent HOW to code. But right now:
1. Rules live in plain textareas with no structure
2. You can't save or reuse rule sets across builds
3. You can't mix and match rules from different sources (your own, a mentor's, project-specific)
4. The split-phase toggle is buried in settings where you can forget about it
5. There's no way to combine multiple rule sets into the Phase 1 and Phase 2+ rules

### Architecture: Three Layers

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Rule Block Library (persistent, reusable)     │
│  Named blocks you create once, use across many builds   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Combiner (three output slots)                 │
│  Checkboxes select which blocks merge into each slot    │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: Phase Rules (what the build actually uses)    │
│  Filled by the Combiner via Send buttons                │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: Rule Block Library

A scrollable list of named, persistent text blocks. Each block is a self-contained set of rules (e.g., "Mentor's Code Standards", "Security Protocol", "TypeScript Strict", "Condensed Phase 2 Rules").

**Block layout:**

```
┌─ "Code Standards" ─────────────────── [Edit] [Clear] ─┐
│                                              ☑ Main   │
│  Always use TypeScript strict mode...        ☑ P1     │
│  No any types. Prefer interfaces...          ☐ P2+    │
│                                                        │
│  Tags: [security] [typescript] [core]    ⋮ drag ≡     │
└────────────────────────────────────────────────────────┘
```

**Block features:**
- **Name** (editable) — displayed as the block header
- **Text content** — the actual rules (editable textarea, default locked)
- **Three checkboxes on the right rail** — `☐ Main`, `☐ P1`, `☐ P2+` control which combiner slots this block feeds into. These are **two-way bound** with the combiner below (check from either location, both update).
- **Tags** — filterable metadata separate from the name. Examples: `[security]`, `[testing]`, `[typescript]`, `[mentor]`. Click a tag to filter the library to only blocks with that tag. Click again to show all.
- **Labels** — visual grouping headers for drag-and-drop ordering. Like folder names ("Core", "Style", "Project-Specific"). Blocks under the same label stay grouped when dragged.
- **Drag-and-drop** — reorder blocks. The merge order in the combiner follows the library order (top block's text first).
- **Edit/Lock toggle** — default locked (read-only). Click Edit to unlock the textarea. Click Lock to save. Prevents accidental edits.
- **Clear button** — empties the text content (with confirmation).
- **[+ New Block] button** — adds a blank block at the bottom.
- **Delete block** — removes block entirely (with confirmation).

**Sorting/filtering:**
- Filter by tag: click any tag to show only blocks with that tag
- Sort by: drag order (default), name (A-Z), date created
- When filtered by tag, the filtered view preserves drag order within results

### Layer 2: Combiner

Three output slots that merge checked blocks into ready-to-use rule text.

```
┌─ Main Combined ─────────────────── [↻ Re-pull] ───────┐
│ ☑ Code Standards                                       │
│ ☑ Mentor's Rules        ← two-way bound to blocks ↑   │
│ ☐ Security Protocol                                    │
│ ☐ Condensed Rules                                      │
│                                                        │
│ Preview: "Always use TypeScript strict mode...         │
│ No any types... Test every function... No magic..."    │
│                                          142 tokens    │
└────────────────────────────────────────────────────────┘

┌─ Phase 1 Combo ─────────────────── [↻ Re-pull] ───────┐
│ ☑ Code Standards                                       │
│ ☑ Mentor's Rules        ← two-way bound to blocks ↑   │
│ ☑ Security Protocol                                    │
│ ☐ Condensed Rules                                      │
│                                                        │
│ Preview: "Always use TypeScript... Test every...       │
│ Validate all inputs... Sanitize SQL..."                │
│                                          218 tokens    │
└────────────────────────────────────────────────────────┘

┌─ Phase 2+ Combo ────────────────── [↻ Re-pull] ───────┐
│ ☐ Code Standards                                       │
│ ☑ Mentor's Rules        ← two-way bound to blocks ↑   │
│ ☐ Security Protocol                                    │
│ ☑ Condensed Rules                                      │
│                                                        │
│ Preview: "Test every function... No magic...           │
│ Short version: TS strict, test all..."                 │
│                                           89 tokens    │
└────────────────────────────────────────────────────────┘
```

**Combiner features:**
- **Checklist** — shows all blocks from the library. Checked = included in this combo's merge.
- **Two-way binding** — checking a block in the combiner checks the corresponding checkbox (Main/P1/P2+) on the block card above. Unchecking from either location unchecks both.
- **Re-pull button (↻)** — re-merges from all currently checked blocks with their latest text content. Use after editing a block's text above.
- **Preview** — read-only preview of the merged text (first ~200 chars).
- **Token count** — shows estimated tokens for the merged content.
- **Merge order** — follows the library's drag order (top to bottom).

### Layer 3: The "Go" Gate (Single vs Split Phase)

The existing `splitPhaseRules` toggle gets removed from Build Settings and replaced with a **gate popup** on the Generate/Process button.

When the user hits the main action button (Generate All, or the individual Send buttons), a popup appears:

```
┌──────────────────────────────────────────┐
│  How are you building this?              │
│                                          │
│  ┌──────────────┐  ┌───────────────────┐ │
│  │ Single Phase │  │   Split Phase     │ │
│  │              │  │                   │ │
│  │ Uses: Main   │  │ Uses: P1 Combo    │ │
│  │ Combined     │  │  + P2+ Combo      │ │
│  │              │  │                   │ │
│  │  142 tokens  │  │ 218 + 89 tokens   │ │
│  └──────────────┘  └───────────────────┘ │
│                                          │
│  Last used: Split Phase                  │
└──────────────────────────────────────────┘
```

**Gate behavior:**
- **Cannot be skipped** — you must click one of the two options to proceed.
- **Shows token counts** — so you know the cost of each choice.
- **Shows "Last used"** — reminds you what you picked last time.
- **One click proceeds** — clicking an option immediately triggers the action. No second confirmation needed. The choice IS the confirmation.
- **Remembers last choice** — persisted in localStorage so "Last used" label is always accurate.

**What happens after the choice:**
- **Single Phase** → Main Combined text is sent as the rules for all phases
- **Split Phase** → Phase 1 Combo is sent as Phase 1 rules, Phase 2+ Combo is sent as Phase 2+ rules

### Data Model (Persistence)

Rule blocks persist to `~/.autoforge/cli_scripter_rules.json`:

```json
{
  "version": 1,
  "blocks": [
    {
      "id": "uuid-1",
      "name": "Code Standards",
      "content": "Always use TypeScript strict mode...",
      "tags": ["typescript", "core"],
      "label": "Core",
      "order": 0,
      "combiner_main": true,
      "combiner_p1": true,
      "combiner_p2plus": false,
      "created_at": "2026-03-12T10:00:00Z",
      "updated_at": "2026-03-12T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "name": "Mentor's Rules",
      "content": "Test every function...",
      "tags": ["mentor", "testing"],
      "label": "Core",
      "order": 1,
      "combiner_main": true,
      "combiner_p1": true,
      "combiner_p2plus": true,
      "created_at": "2026-03-12T10:00:00Z",
      "updated_at": "2026-03-12T10:00:00Z"
    }
  ],
  "last_phase_mode": "split"
}
```

**Backend endpoints:**

```
GET  /api/cli-scripter/rules          — Load all rule blocks
POST /api/cli-scripter/rules          — Save all rule blocks (full replace)
GET  /api/cli-scripter/rules/combined — Get merged text for a slot (main|p1|p2plus)
```

### Implementation Phases

**Phase 16: Rule Block Library component (3/10)**
- RuleBlock component: name, content, edit/lock, clear, delete
- Library container: scrollable list, [+ New Block] button
- Drag-and-drop reorder (use existing patterns from queue management)
- Tags: add/remove tags per block, click-to-filter
- Labels: grouping headers, drag respects label groups

**Phase 17: Combiner + two-way binding (3/10)**
- Three combiner slots: Main Combined, Phase 1 Combo, Phase 2+ Combo
- Checkbox list in each slot, two-way bound to block checkboxes
- Re-pull button: re-merge from checked blocks
- Preview text + token count
- Merge order follows library drag order

**Phase 18: Gate popup + Send flow (2/10)**
- Gate popup component: two-button modal (Single Phase / Split Phase)
- Intercepts Generate All button click
- Routes combined text to correct Phase Rules fields
- Persists last choice to localStorage
- Remove old `splitPhaseRules` toggle from Build Settings

**Phase 19: Backend persistence (2/10)**
- JSON file at `~/.autoforge/cli_scripter_rules.json`
- REST endpoints: GET/POST rules, GET combined text
- Load on page mount, save on every block change (debounced 1 second)

---

## Cross-Cutting Fix: Persistence + Clear Buttons (3/10 difficulty)

### The Problem

Almost NOTHING in CLI Scripter persists between page reloads. Every `useState` variable resets to its default. The user has to re-enter everything — app name, description, features, settings, prompts, AI results — every single time.

### What Currently Persists

| Field | Persisted? | Where |
|-------|-----------|-------|
| GitHub PAT | ✅ Yes | localStorage |
| Everything else | ❌ No | React state only |

### What MUST Persist

All user-entered data should survive page reloads. Two tiers:

**Tier 1: localStorage (immediate, no backend needed)**
| Field | Key |
|-------|-----|
| App name | `cli_scripter_app_name` |
| App description | `cli_scripter_app_description` |
| Boilerplate selection | `cli_scripter_boilerplate` |
| Features list | `cli_scripter_features` |
| Dependencies | `cli_scripter_dependencies` |
| Build settings (turns, transition, error handling, git commits, phase count) | `cli_scripter_settings` |
| Agent role configs (enabled, model, prompt overrides) | `cli_scripter_roles` |
| Phase assignments | `cli_scripter_phase_assignments` |
| Include verification toggle | `cli_scripter_include_verification` |
| Project directory | `cli_scripter_project_dir` |
| Split phase mode (last used) | `cli_scripter_phase_mode` |

**Tier 2: Backend persistence (for data that should survive browser clears)**
| Field | Where |
|-------|-------|
| Rule blocks + combiner state | `~/.autoforge/cli_scripter_rules.json` (System 8) |
| Saved build configs | SQLite `build_configs` table (System 3) |
| Build queue | SQLite `build_queue` table (System 3) |

**Tier 3: Session-only (intentionally NOT persisted)**
| Field | Why |
|-------|-----|
| AI generation results (PRD, phases, scripts) | These are outputs, not inputs. User regenerates them. |
| Loading/error states | Transient UI state |
| GitHub validation state | Re-validates on token change |

### Clear Buttons

Every persistent text input gets a clear button (small `✕` icon on the right edge of the field):
- **Single-click** clears the field
- **No confirmation** for small fields (app name, description)
- **Confirmation dialog** for large fields (rules, features, phase assignments, AI results)
- Clear buttons are subtle (zinc-500, hover to orange) — visible but not distracting

### Implementation

**Phase 20: localStorage persistence layer (2/10)**
- Custom `usePersistedState` hook:
  ```typescript
  function usePersistedState<T>(key: string, defaultValue: T): [T, (v: T) => void]
  ```
- Replace all `useState` calls for Tier 1 fields with `usePersistedState`
- Debounced saves (500ms) to avoid thrashing on every keystroke
- Load from localStorage on mount, fall back to defaults if missing

**Phase 21: Clear buttons (1/10)**
- ClearButton component: small ✕ icon, positioned at right edge of input/textarea
- Add to all text inputs and textareas
- Confirmation dialog for fields with >100 characters of content
- Clear also clears the persisted localStorage value

---

## Cross-Cutting Fix: Phase Assignments → Read-Only Output (1/10 difficulty)

### The Problem

The Phase Assignments section is currently an editable textarea, which implies the user should fill it in manually. That's wrong — the LLM decides phase assignments during the phase split step. The user shouldn't be deciding "Phase 1: auth, Phase 2: API" by hand. The whole point of the AI split is that the AI figures this out.

### Current State

```typescript
const [phaseAssignments, setPhaseAssignments] = useState('')
// Rendered as an editable <textarea>
```

### Fix

1. **Make it read-only** — change from `<textarea>` to a styled read-only display block (pre-formatted text with a subtle border). No cursor, no editing.
2. **Populate automatically** — after the "Split into Phases" step completes, parse the AI output and fill the Phase Assignments display with the result.
3. **Add a "Regenerate" button** — if the user doesn't like what the AI decided, they click "Regenerate" to re-run the phase split. They don't hand-edit.
4. **Show empty state** — before phase split runs: "Phase assignments will appear here after generating the phase split."
5. **Remove from localStorage persistence** — this is an AI output, not user input. Don't persist it (it gets regenerated).

### Implementation

**Phase 22: Phase Assignments read-only conversion (1/10)**
- Change textarea to read-only styled div with `whitespace-pre-wrap`
- Auto-populate from phase split AI result
- Add "↻ Regenerate Split" button
- Empty state message when no split has been generated

---

## Cross-Cutting Fix: Project Directory File Browser (3/10 difficulty)

### The Problem

The user picks a project directory but has no way to see what's already in it. They can't check what files exist, what's been built before, or whether they're pointing at the right folder. The directory path is just a text input — a blind field.

### Solution: Mini File Browser in Two Spots

Add a compact, collapsible file browser that shows the contents of the selected project directory. **Same component, same data, shown in two places:**

1. **Top of page** — in the Project Basics section, below the directory input
2. **Bottom of page** — in the Generate section, above the Generate All button

Both instances are synced — they show the same directory, same view. This way the user can see their project files from either end of the page without scrolling.

### File Browser Design

```
┌─ Project Files ──────────────────── [↻ Refresh] [▼] ─┐
│                                                        │
│  📁 src/                                               │
│  📁 scripts/cli-scripter/          ← previous builds   │
│  📄 package.json                   2 hours ago          │
│  📄 CLAUDE.md                      3 hours ago          │
│  📄 tsconfig.json                  1 day ago            │
│                                                        │
│  Recent commits:                                        │
│  • "Phase 2: API endpoints" — 2 hours ago              │
│  • "Phase 1: Auth + DB setup" — 5 hours ago            │
│  • "Initial boilerplate" — 1 day ago                   │
└────────────────────────────────────────────────────────┘
```

**Features:**
- **Collapsible** — default collapsed (just a slim "Project Files ▶" bar). Click to expand. Stays open once expanded until manually collapsed.
- **Top-level only** — shows files and folders at the root of the project directory. Not a full tree — just enough to see what's there.
- **Recent timestamps** — show relative time ("2 hours ago") for the most recently modified files.
- **Recent commits** — if it's a git repo, show the last 3 commit messages with timestamps. Quick way to see what's been built.
- **Refresh button** — re-reads the directory (doesn't auto-poll, to avoid performance issues).
- **Highlight build artifacts** — if a `scripts/cli-scripter/` folder exists (from previous builds), highlight it in orange so the user knows there are existing scripts.
- **Error state** — if the directory doesn't exist or is empty, show "Directory not found" or "Empty directory" with appropriate styling.

### Backend

Reuse the existing filesystem browser API (`server/routers/filesystem.py`) — it already handles directory listing with security controls. Just need a lightweight endpoint or reuse the existing one:

```
GET /api/filesystem/list?path={project_dir}&depth=1
```

For git info:
```
GET /api/cli-scripter/project-info?path={project_dir}
```
Returns: `{ files: [...], recent_commits: [...], has_previous_builds: boolean }`

### Implementation

**Phase 23: Project directory file browser (3/10)**
- ProjectFileBrowser component: collapsible, top-level file list, recent commits
- Mount in Project Basics section (below directory input)
- Mount in Generate section (above Generate All button)
- Both instances share the same data (React Query cache keyed on project path)
- Backend: reuse filesystem.py + add git log endpoint
- Refresh button, error states, highlight previous builds

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
| 12 | System 5 | PromptBar component (lock/edit/collapse) | 2/10 | — |
| 13 | System 5 | Prompt persistence in Build Storage | 1/10 | — |
| 14 | System 6 | Pipeline card component (Build Estimate) | 2/10 | — |
| 15 | System 7 | Parallel wave parsing + CLI script generation | 3/10 | — |
| 16 | System 8 | Rule Block Library component | 3/10 | — |
| 17 | System 8 | Combiner + two-way binding | 3/10 | — |
| 18 | System 8 | Gate popup + Send flow | 2/10 | — |
| 19 | System 8 | Backend rule persistence | 2/10 | — |
| 20 | Fix | localStorage persistence layer | 2/10 | — |
| 21 | Fix | Clear buttons on all inputs | 1/10 | — |
| 22 | Fix | Phase Assignments → read-only output | 1/10 | — |
| 23 | Fix | Project directory file browser (×2 spots) | 3/10 | — |
| FIX | — | Deterministic script templates | 2/10 | ~5K/build |

Each phase is under 50% context window. Total: ~24 phases across 3-4 weeks.

### Recommended Build Priority

Build persistence, UX fixes, and the rules library FIRST — these are the most painful gaps for daily use:

1. **Phase 20-22 (Persistence + Clear buttons + Phase Assignments fix)** — do this immediately, affects everything
2. **Phase 23 (File browser)** — know what you're building into before you start
3. **Phase 16-19 (System 8: Rules Library)** — the core workflow improvement
4. **Phase 7-9 (System 3: Build Storage)** — save/load/queue configs
5. **Phase 12-13 (System 5: Prompt Visibility)** — surface hidden prompts
6. **Phase 14 (System 6: Card Build Estimate)** — fix the unusable display
7. **Phase 15 (System 7: Parallel Waves)** — optional optimization
8. **Phase 1-6 (Systems 1-2: Live Dashboard + Terminal)** — nice to have, not blocking
9. **Phase 10-11 (System 4: Boilerplate)** — only needed for dual builds
