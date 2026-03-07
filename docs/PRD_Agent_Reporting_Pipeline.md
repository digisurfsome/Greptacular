# PRD: Agent Reporting & Self-Learning Pipeline

**Status:** Draft
**Author:** AutoForge Team
**Date:** 2026-03-07

---

## Problem

When agents finish a build (clean or broken), we have no structured way to:
- See what each agent actually did during its session
- Compare clean builds vs problem builds
- Spot patterns (e.g., "Feature type X fails 60% of the time")
- Feed learnings back into better prompts and plans

We need a **reporting log** that agents write, a **data pipeline** that aggregates it, and a **spreadsheet export** that makes weak points obvious at a glance.

---

## What Already Exists (We Build On This)

| Data Source | What It Captures | Where |
|---|---|---|
| `ActionLog` table | Every tool call: name, duration, status, session_id | `features.db` |
| `VerificationResult` table | Lint/typecheck/e2e pass/fail per feature | `features.db` |
| `Checkpoint` table | Git SHA snapshots per session | `features.db` |
| `Feature` table | Feature status (passes, in_progress, reviewed) | `features.db` |
| WebSocket `agent_update` | Real-time state: thinking/working/testing/success/error | In-memory only |
| `orchestrator_debug.log` | Spawn/complete events with timestamps | File on disk |
| Progress cache | Passing count over time | `.progress_cache` file |

**What's Missing:**
- No **session summary** record (duration, features attempted/completed/failed, error count)
- No **error classification** (why did it fail? prompt issue? code issue? timeout?)
- No **historical comparison** across sessions
- No **export to spreadsheet** for trend analysis
- No **feedback loop** from failures back to prompts

---

## Design

### Part 1: Agent Session Report (What Agents Must Log)

At the **end of every agent session**, the system writes a `SessionReport` record to the database.

#### SessionReport Table Schema

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | TEXT | 8-char UUID (matches ActionLog) |
| `project_name` | TEXT | Project identifier |
| `agent_type` | TEXT | `initializer`, `coding`, `testing`, `review`, `qa` |
| `agent_index` | INTEGER | 0-based agent number (for parallel) |
| `model` | TEXT | Model used (e.g., `claude-sonnet-4-6`) |
| `yolo_mode` | BOOLEAN | Whether YOLO was on |
| `started_at` | DATETIME | Session start timestamp |
| `ended_at` | DATETIME | Session end timestamp |
| `duration_seconds` | INTEGER | Total wall-clock time |
| `outcome` | TEXT | `success`, `partial`, `failure`, `crash`, `timeout` |
| `features_attempted` | TEXT | JSON array of feature IDs attempted |
| `features_completed` | TEXT | JSON array of feature IDs marked passing |
| `features_failed` | TEXT | JSON array of feature IDs that failed |
| `total_tool_calls` | INTEGER | Count of tool executions |
| `total_errors` | INTEGER | Count of tool errors/blocks |
| `error_summary` | TEXT | JSON array of `{tool, error_type, message}` for top errors |
| `lint_passed` | BOOLEAN | Did lint pass at session end? |
| `typecheck_passed` | BOOLEAN | Did typecheck pass? |
| `e2e_passed` | BOOLEAN | Did e2e tests pass? (NULL if not run) |
| `tokens_in` | INTEGER | Input tokens consumed (if available) |
| `tokens_out` | INTEGER | Output tokens generated (if available) |
| `git_sha_start` | TEXT | Git SHA at session start |
| `git_sha_end` | TEXT | Git SHA at session end |
| `failure_category` | TEXT | Classified failure reason (see categories below) |
| `failure_detail` | TEXT | Free-text detail about what went wrong |
| `retry_count` | INTEGER | How many retries/continues happened |

#### Failure Categories

Standardized categories so we can filter and count in the spreadsheet:

| Category | Meaning | Example |
|---|---|---|
| `prompt_unclear` | Agent misunderstood the task | Built wrong component |
| `dependency_missing` | Needed a feature that wasn't done yet | Import from unbuilt module |
| `lint_fail` | Code doesn't pass linting | Unused imports, formatting |
| `typecheck_fail` | TypeScript/type errors | Wrong prop types |
| `e2e_fail` | Browser tests fail | Element not found, timeout |
| `runtime_error` | Code crashes at runtime | Null reference, bad import |
| `timeout` | Agent hit iteration/time limit | Ran out of turns |
| `rate_limited` | API rate limit hit | 429 errors |
| `crash` | Agent process died unexpectedly | OOM, signal kill |
| `security_blocked` | Command blocked by security | Tried to run blocked command |
| `none` | Clean build, no failure | Everything passed |

#### How It Gets Populated

1. **Automatic fields** — `agent.py` already tracks session_id, start time, tool calls. At session end, we query ActionLog for counts and errors.
2. **Outcome detection** — Check feature status after session: all passing = `success`, some passing = `partial`, none passing = `failure`.
3. **Failure classification** — Pattern-match the last errors in ActionLog:
   - Tool `bash` with "lint" in input + error status → `lint_fail`
   - Tool `bash` with "tsc" or "typecheck" → `typecheck_fail`
   - Tool blocked status → `security_blocked`
   - Session ended by timeout → `timeout`
   - Process exit code != 0 → `crash`
4. **Git SHAs** — Capture `git rev-parse HEAD` at start and end of session.

---

### Part 2: Data Pipeline (Aggregation & Export)

#### New API Endpoints

```
GET /api/reports/sessions?project={name}&from={date}&to={date}
    → Returns all SessionReport records for a project in date range

GET /api/reports/summary?project={name}&from={date}&to={date}
    → Returns aggregated stats:
      - Total sessions, success rate, avg duration
      - Failure category breakdown (counts + percentages)
      - Feature-level stats (avg attempts to pass, slowest features)
      - Model comparison (if multiple models used)

GET /api/reports/export?project={name}&format=xlsx
    → Downloads spreadsheet with all session data
```

#### Spreadsheet Export Structure

**Tab 1: Session Log** (one row per agent session)

| Session ID | Date | Agent Type | Model | Duration | Outcome | Features Done | Features Failed | Errors | Failure Category | Detail |
|---|---|---|---|---|---|---|---|---|---|---|
| a1b2c3d4 | 2026-03-07 | coding | sonnet-4-6 | 4m 32s | success | 1 | 0 | 0 | none | — |
| e5f6g7h8 | 2026-03-07 | coding | sonnet-4-6 | 8m 15s | failure | 0 | 1 | 3 | lint_fail | 12 unused imports |
| i9j0k1l2 | 2026-03-07 | testing | sonnet-4-6 | 2m 01s | success | 3 | 0 | 0 | none | — |

**Tab 2: Feature Report** (one row per feature)

| Feature ID | Name | Category | Attempts | Sessions to Pass | Avg Duration | First Fail Reason | Final Status |
|---|---|---|---|---|---|---|---|
| 1 | Auth login | core | 1 | 1 | 3m 20s | none | passing |
| 5 | Dashboard chart | UI | 3 | 3 | 12m 45s | e2e_fail | passing |
| 12 | Export PDF | integration | 4 | — | 18m 00s | runtime_error | failing |

**Tab 3: Failure Analysis** (pivot table style)

| Failure Category | Count | % of Failures | Avg Duration | Most Affected Features | Suggested Action |
|---|---|---|---|---|---|
| lint_fail | 15 | 35% | 6m 12s | #3, #7, #14 | Add lint rules to prompt |
| e2e_fail | 8 | 19% | 9m 45s | #5, #9 | Improve test selectors |
| timeout | 7 | 16% | 15m 00s | #12, #18 | Break into smaller features |
| prompt_unclear | 5 | 12% | 7m 30s | #8, #11 | Rewrite feature descriptions |

**Tab 4: Trends** (daily/weekly rollup)

| Date | Sessions | Success Rate | Avg Duration | Top Failure | Features Completed |
|---|---|---|---|---|---|
| 2026-03-05 | 12 | 75% | 5m 30s | lint_fail | 8 |
| 2026-03-06 | 18 | 83% | 4m 15s | e2e_fail | 14 |
| 2026-03-07 | 8 | 88% | 3m 50s | none | 7 |

---

### Part 3: Self-Learning Feedback Loop

The numbers from the spreadsheet drive **automatic improvements**:

#### 3a. Weak Point Detection

After every N sessions (configurable, default 10), the system runs analysis:

```
IF failure_category "lint_fail" > 30% of failures:
   → Flag: "Lint failures are the #1 problem"
   → Suggested action: "Add explicit lint rules to coding prompt"
   → Auto-inject into next agent's prompt: "IMPORTANT: Run `npm run lint` after every file change"

IF feature X has > 3 failed attempts:
   → Flag: "Feature #{X} is consistently failing"
   → Suggested action: "Break into sub-features or rewrite description"
   → Surface in UI with warning badge

IF avg_duration for agent_type "coding" > 10 minutes:
   → Flag: "Coding sessions are running long"
   → Suggested action: "Reduce batch size or simplify features"
```

#### 3b. Prompt Enhancement Database

New table `PromptLearning`:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `trigger_category` | TEXT | Which failure category triggered this |
| `trigger_threshold` | REAL | What percentage triggered it (e.g., 0.30) |
| `prompt_injection` | TEXT | Text to add to agent prompts |
| `active` | BOOLEAN | Whether this learning is currently applied |
| `created_at` | DATETIME | When the learning was created |
| `effectiveness` | REAL | Success rate change after applying (updated over time) |

Example learnings:

| Trigger | Injection | Effectiveness |
|---|---|---|
| `lint_fail > 30%` | "Always run lint before marking feature complete" | +22% success rate |
| `e2e_fail > 20%` | "Use data-testid attributes on all interactive elements" | +15% success rate |
| `timeout > 15%` | "If stuck for more than 3 tool calls, try a different approach" | +8% success rate |

#### 3c. How Learnings Get Applied

1. Before spawning an agent, query `PromptLearning` where `active = True`
2. Append all active `prompt_injection` texts to the coding/testing prompt
3. After the session, compare outcome against historical baseline
4. Update `effectiveness` score: did this learning actually help?
5. Auto-deactivate learnings with negative effectiveness after 20+ sessions

---

### Part 4: UI Integration

#### Reports Page (`/#/workspace/reports` or `/#/reports`)

- **Session Timeline** — Scrollable list of recent sessions with outcome badges (green/yellow/red)
- **Success Rate Chart** — Line chart showing success % over time
- **Failure Breakdown** — Pie/bar chart of failure categories
- **Slow Features** — Table of features sorted by avg attempts-to-pass
- **Active Learnings** — List of currently applied prompt enhancements with effectiveness scores
- **Export Button** — Download .xlsx with all tabs described above

#### Project Dashboard Additions

- **Build Health Badge** — On each project card: "92% success rate (last 20 sessions)"
- **Trend Arrow** — Up/down indicator showing if success rate is improving or declining
- **Warning Flags** — Red badges on features that have failed 3+ times

---

## Implementation Phases

### Phase 1: Session Reports (Foundation)
- Add `SessionReport` model to `api/database.py`
- Add report generation logic at end of `agent.py` session loop
- Wire into parallel_orchestrator for multi-agent sessions
- Add `/api/reports/sessions` endpoint

### Phase 2: Spreadsheet Export
- Add `/api/reports/export` endpoint using `openpyxl`
- Generate all 4 tabs (Session Log, Feature Report, Failure Analysis, Trends)
- Add "Export" button to UI

### Phase 3: Failure Analysis & Weak Point Detection
- Build analysis function that runs after every 10 sessions
- Surface weak points in UI with warning badges
- Add Failure Analysis tab to reports page

### Phase 4: Self-Learning Prompt Enhancement
- Add `PromptLearning` table
- Auto-generate learnings from failure patterns
- Inject active learnings into agent prompts
- Track effectiveness and auto-deactivate bad learnings

### Phase 5: UI Reports Page
- Build full reports page with charts and tables
- Add build health badges to project dashboard
- Add trend indicators

---

## Success Metrics

| Metric | Target | How Measured |
|---|---|---|
| Session success rate visible | 100% of sessions tracked | Count of SessionReport rows vs agent runs |
| Failure patterns identified | Top 3 categories surfaced | Failure Analysis tab populated |
| Prompt learnings applied | At least 3 active learnings | PromptLearning table count |
| Success rate improvement | +15% over 30 days | Compare week-1 vs week-4 success rates |
| Export works | < 5 seconds for 500 sessions | Download timing |

---

## Key Design Decisions

1. **SQLite, not a separate database** — Keep everything in `features.db` so it travels with the project
2. **Automatic classification, not manual** — Agents don't self-report failure reasons; we pattern-match from ActionLog
3. **Spreadsheet as primary analysis tool** — Users know Excel; don't build a custom analytics UI first
4. **Learnings are additive prompts** — We append to prompts, never rewrite them, so learnings are safe to auto-apply
5. **Effectiveness tracking prevents bad learnings** — If a learning makes things worse, it auto-deactivates
