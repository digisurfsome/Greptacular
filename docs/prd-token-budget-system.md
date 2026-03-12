# PRD: Token Budget System — Usage Tracking + Smart Scheduler

> **Status:** Design
> **Prerequisite:** CLI Scripter with Build Queue (Option A) must be working first
> **Difficulty:** Option B = 5/10, Option C = 7/10
> **Priority:** Build after CLI Scripter is field-tested with 2-3 real app builds

---

## Problem Statement

The owner runs a $200/month Anthropic Max plan with three rolling usage windows:

| Window | What It Is | Risk |
|--------|-----------|------|
| **5-hour rolling** | Burst limit — hit this and you're locked out for hours | Can't use Claude for PRD work, daily tasks |
| **Weekly rolling** | Sustained limit — pace across the week | Run dry by Wednesday, nothing left for Thu-Fri |
| **Monthly cap** | Hard ceiling — $200/month of subscription value | Waste budget on low-priority builds |

Today there's **zero visibility** into usage. The owner runs builds, hits walls, and loses productive daytime hours. The goal: know where you stand at all times and automate pacing so the builder never eats the owner's working hours.

---

## The Three Rolling Windows (What We're Tracking)

Anthropic doesn't expose a "check your usage" API. So we build our own ledger from CLI output + manual calibration.

### Data We CAN Capture
- **Per-session tokens** — Claude CLI reports input/output tokens at session end
- **Timestamp** — when each session started and ended
- **Model used** — Opus/Sonnet/Haiku (different costs against the window)
- **Source** — CLI Scripter build vs. Workspace chat vs. direct Claude Code

### Data We CANNOT Capture
- Exact position in Anthropic's internal rate counters
- Usage from Claude web UI, mobile app, or other tools outside AutoForge
- The exact token-to-time conversion Anthropic uses internally

### The Calibration Button
When the owner hits a rate limit wall, they press a button: **"I Just Hit the Wall"**

This records a hard data point: at this exact timestamp, the 5-hour window was exhausted. From this we can:
1. Calculate backwards: total tokens used in last 5 hours = our tracked sum
2. If our tracked sum < what Anthropic thinks, the gap = usage from outside AutoForge
3. Over time, the gap shrinks as more work moves into AutoForge
4. A learning algorithm tightens the estimate with each calibration point

---

## Option B: Token Ledger + Dashboard (5/10 difficulty)

### What It Builds

1. **Token Ledger** — SQLite table logging every CLI session
2. **Rolling Window Calculator** — queries the ledger for 5hr/weekly/monthly sums
3. **Dashboard Gauges** — 3 arc gauges showing % used for each window
4. **Calibration Button** — "I Hit the Wall" button that records a calibration point
5. **Header Badge** — small token counter visible on every page

### Data Model

```sql
-- Token usage log (one row per CLI session)
CREATE TABLE token_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,           -- ISO 8601
    session_type TEXT NOT NULL,        -- 'cli_scripter' | 'workspace' | 'agent' | 'other'
    model TEXT NOT NULL,               -- 'opus' | 'sonnet' | 'haiku'
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    duration_seconds INTEGER,
    project_name TEXT,
    phase TEXT,                        -- 'architect' | 'phase1_build' | 'verify' etc.
    source TEXT DEFAULT 'autoforge'    -- 'autoforge' | 'manual_entry'
);

-- Calibration points (when user hits rate limit)
CREATE TABLE calibration_points (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    window_type TEXT NOT NULL,         -- '5hour' | 'weekly' | 'monthly'
    tracked_total INTEGER,             -- what our ledger shows
    notes TEXT
);

-- Budget settings
CREATE TABLE budget_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Keys: 'daily_work_hours', 'build_window_start', 'build_window_end',
--        '5hour_budget_pct', 'weekly_budget_pct', 'monthly_budget_pct'
```

### Dashboard UI

Three gauge arcs side by side:
```
 ┌─────────────────────────────────────────────┐
 │   5-Hour Window    Weekly Window    Monthly  │
 │   ┌───────┐        ┌───────┐      ┌───────┐│
 │   │ 67%   │        │ 34%   │      │ 12%   ││
 │   │ ████░░│        │ ███░░░│      │ █░░░░░││
 │   └───────┘        └───────┘      └───────┘│
 │   ~182K tokens     ~1.2M tokens   ~4.1M    │
 │   est. 1.5hr left  est. 3 days    24 days  │
 │                                             │
 │   [🔴 I Just Hit the Wall]                  │
 │                                             │
 │   Recent Sessions:                          │
 │   ┌────────────────────────────────────┐    │
 │   │ 2:15 PM  CLI Scripter  architect  │    │
 │   │          opus  43,200 tokens       │    │
 │   │ 1:30 PM  CLI Scripter  phase1     │    │
 │   │          sonnet  87,100 tokens     │    │
 │   │ 12:45 PM Workspace  chat          │    │
 │   │          opus  15,400 tokens       │    │
 │   └────────────────────────────────────┘    │
 └─────────────────────────────────────────────┘
```

### Header Badge (every page)

Small pill in the top bar showing the most critical number:
```
[⚡ 5hr: 67%]  or  [⚡ 5hr: OK]
```

Changes color: green (<50%), yellow (50-75%), orange (75-90%), red (>90%).

### API Endpoints

```
GET  /api/token-budget/status          — Current window percentages + estimates
POST /api/token-budget/log             — Record a session's token usage
POST /api/token-budget/calibrate       — Record a "hit the wall" event
GET  /api/token-budget/history         — Recent session log
GET  /api/token-budget/settings        — Get budget settings
PUT  /api/token-budget/settings        — Update budget settings
```

### Implementation Phases

**Phase 1: Ledger + Logging (2/10)**
- SQLite table + Pydantic models
- API endpoints for logging and querying
- Hook into CLI Scripter's `_run_claude_cli()` to auto-log token counts
- Hook into Workspace chat's `token_usage` WebSocket events

**Phase 2: Dashboard UI (3/10)**
- New dashboard tab or widget
- Three gauge components
- Recent sessions list
- Calibration button

**Phase 3: Header Badge (2/10)**
- Small component in App.tsx header
- Polls `/api/token-budget/status` every 60 seconds
- Color-coded by severity

---

## Option C: Smart Scheduler / Governor (7/10 difficulty)

> **Prerequisite:** Option B must be working and calibrated with at least 5 data points

### What It Adds On Top of Option B

1. **Work Hours System** — Define when YOU work vs. when builds run
2. **Budget Allocation** — Reserve X% of each window for human work
3. **Build Governor** — Automatically pauses builds when approaching limits
4. **Daily Planner** — Override defaults for specific days
5. **Learning Engine** — Improves estimates over time from calibration data

### Work Hours System

```
Default Schedule:
  Work hours:   10:00 AM - 6:00 PM (human uses Claude)
  Build hours:  12:00 AM - 8:00 AM (builds run unattended)
  Buffer zone:  8:00 AM - 10:00 AM (finish current build, no new starts)

Budget Reservation:
  5-hour window:  Reserve 40% for human work
  Weekly window:  Reserve 30% for human work
  Monthly window: Reserve 20% for human work
```

### Build Governor Logic

```python
def should_start_next_build(queue_item):
    status = get_budget_status()
    now = datetime.now()

    # Hard stops
    if status.five_hour_pct > 90:
        return False, "5-hour window nearly exhausted"
    if status.weekly_pct > 95:
        return False, "Weekly budget nearly exhausted"

    # Work hours protection
    if is_work_hours(now):
        reserved = status.five_hour_pct + estimate_build_pct(queue_item)
        human_reserve = get_setting('5hour_reserve_pct')  # e.g., 40%
        if reserved > (100 - human_reserve):
            return False, f"Would eat into work-hours reserve ({human_reserve}%)"

    # Estimate: will this build fit in remaining budget?
    estimated_tokens = estimate_build_tokens(queue_item)
    remaining_tokens = status.five_hour_remaining
    if estimated_tokens > remaining_tokens * 0.8:  # 80% safety margin
        return False, "Build likely exceeds remaining 5-hour budget"

    return True, "Go"
```

### Where It Pauses

The governor can pause at these natural breakpoints:
1. **Between queued apps** — safest, no context loss
2. **Between phases** — safe, each phase is independent
3. **Between role steps** — safe (between coder and reviewer)
4. **NEVER mid-session** — don't interrupt a running Claude CLI call

When paused, the queue shows:
```
⏸ Paused — 5-hour window at 87%
   Estimated resume: 2:30 PM (when window rolls)
   Next: Phase 3 of "My SaaS App"
   [▶ Force Resume]  [⏭ Skip to Next App]
```

### Daily Planner (Override)

```
 ┌─────────────────────────────────────────────┐
 │  Tomorrow: March 12, 2026                    │
 │                                              │
 │  Default: Work 10am-6pm, Builds midnight-8am │
 │                                              │
 │  Override for tomorrow:                       │
 │  ○ Use defaults                              │
 │  ● Custom:                                   │
 │    Work hours: [9:00 AM] to [12:00 PM]       │
 │    Build hours: [12:00 PM] to [11:59 PM]     │
 │    Reason: "Light work day, run builds all    │
 │            afternoon"                         │
 │                                              │
 │  Estimated capacity tomorrow:                 │
 │    ~3 builds (sonnet phases)                  │
 │    ~1 build (opus-heavy pipeline)             │
 └─────────────────────────────────────────────┘
```

### Learning Engine

After 10+ calibration points, the system can:

1. **Estimate tokens-per-build** — average by project type and complexity
2. **Predict wall-hit time** — "at current pace, you'll hit the 5hr wall at 3:15 PM"
3. **Suggest build schedule** — "run 2 builds tonight, save the 3rd for tomorrow"
4. **Auto-adjust reserves** — if you consistently use 60% during work hours, adjust from 40% to 65%

The learning is simple rolling averages + linear regression. No ML needed.

### Data Model Additions (on top of Option B)

```sql
-- Schedule overrides for specific days
CREATE TABLE schedule_overrides (
    date TEXT PRIMARY KEY,          -- '2026-03-12'
    work_start TEXT,                -- '09:00'
    work_end TEXT,                  -- '12:00'
    build_start TEXT,               -- '12:00'
    build_end TEXT,                 -- '23:59'
    notes TEXT
);

-- Build estimates (learned from past builds)
CREATE TABLE build_estimates (
    id INTEGER PRIMARY KEY,
    project_type TEXT,              -- 'web-supabase' | 'flutter' | 'scratch'
    phase_count INTEGER,
    feature_count INTEGER,
    total_tokens INTEGER,
    duration_seconds INTEGER,
    timestamp TEXT
);
```

### API Endpoints (additional)

```
GET  /api/token-budget/schedule         — Get work/build hours for today
PUT  /api/token-budget/schedule         — Set default schedule
POST /api/token-budget/schedule/override — Override for a specific date
GET  /api/token-budget/estimate/:count  — Estimate tokens for N builds
GET  /api/token-budget/prediction       — Predict when wall will be hit
POST /api/token-budget/governor/check   — Should we start the next build?
```

### Implementation Phases

**Phase 4: Work Hours + Governor (4/10)**
- Schedule data model + settings UI
- Governor check function
- Integration with CLI Scripter queue (check before starting each build)
- Pause/resume UI in queue

**Phase 5: Daily Planner (3/10)**
- Override table + form UI
- Calendar-style day view
- Capacity estimation based on historical data

**Phase 6: Learning Engine (4/10)**
- Build estimates table
- Rolling average calculator
- Wall-hit predictor
- Auto-adjust logic
- "Recommendations" panel in dashboard

---

## What's NOT in Scope

- Integration with Anthropic's actual rate limit API (doesn't exist for subscriptions)
- Multi-account load balancing (save for when business partner's account is integrated)
- Cost optimization / cheapest-model routing (different feature)
- Integration with non-Claude models (Gemini, GPT) budget tracking

---

## The "Hit the Wall" Button — Design Detail

This is the single most important UX element. It needs to be:
- **Visible everywhere** — in the header badge, on the dashboard, in the queue
- **One click** — no confirmation dialog, just record it
- **Informative** — after pressing, show: "Got it. Your 5-hour window resets around [estimated time]."
- **Educational** — first few times, show a tooltip explaining what this does

```
Button states:
  Default:  [🔴 I Hit the Wall]
  Pressed:  [✓ Recorded at 2:15 PM — window resets ~7:15 PM]
  Cooldown: [⏳ Wall hit 15 min ago — too soon to recalibrate]
```

---

## Build Order

1. **Option B Phase 1** — Ledger + logging (get data flowing first)
2. **Option B Phase 2** — Dashboard (see the data)
3. **Option B Phase 3** — Header badge (ambient awareness)
4. *Field test for 1 week — run 5-10 builds, press the wall button 3-5 times*
5. **Option C Phase 4** — Work hours + governor
6. **Option C Phase 5** — Daily planner
7. **Option C Phase 6** — Learning engine

Each phase is under 50% context window. Total: 6 phases across ~2 weeks of development.
