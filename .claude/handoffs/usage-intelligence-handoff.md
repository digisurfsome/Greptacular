# Usage Intelligence System - Handoff Document

## Status: Ready to Implement

## Session Context

This handoff was written at the end of a high-context session (well past 50% context window) that built the foundation for all three features described below. The implementing agent should read the existing code first, as significant groundwork is already in place.

### What Was Built This Session

1. **Context mode toggle** (`1M ctx` / `200K ctx` button) -- switches between 1M beta and 200K standard context windows. Already working in WorkspaceChat.

2. **Usage tracking dashboard** (UsageDashboard component) -- compact expandable panel showing daily/weekly/monthly token usage, cost zone breakdown (standard 0-200K vs premium 200K+ at 1.5x), API-equivalent cost estimates. Already deployed in workspace.

3. **Rate limit learning system** -- `WorkspaceRateLimitEvent` and `WorkspacePremiumLedger` database tables, calibration logic that averages historical rate limit hits with 10% safety margin, confidence scoring (low/medium/high based on sample count). Backend and frontend complete.

4. **Auto-detection of rate limits** -- Both backend (exception pattern matching in `workspace_chat_session.py`) and frontend fallback (WebSocket error message pattern matching in `useWorkspaceChat.ts`) detect rate limit errors and auto-log them for calibration. No manual button press needed.

5. **Zero-meter bug fix** -- token_usage events now emit on conversation resume (not just new conversations) and include message_count.

### Key Files Modified This Session

- `server/services/workspace_database.py` -- New models: `WorkspaceRateLimitEvent`, `WorkspacePremiumLedger`. New functions: `get_usage_by_period()`, `get_conversation_cost_zones()`, `get_usage_summary()`, `log_rate_limit_event()`, `log_premium_usage()`, `get_rate_limit_history()`, `get_calibrated_limits()`, `get_premium_usage_summary()`
- `server/services/workspace_chat_session.py` -- token_usage with message_count on resume, rate limit auto-detection in error handler, premium usage logging after each message
- `server/routers/workspace.py` -- New endpoints: `GET /usage`, `GET /usage/{period}`, `GET /conversations/{id}/cost`, `POST /usage/rate-limit`, `GET /usage/rate-limits`, `GET /usage/calibration`, `GET /usage/premium`
- `ui/src/components/workspace/UsageDashboard.tsx` -- Full dashboard with CalibratedMeter bars, rate limit logging buttons, cost zone visualization
- `ui/src/components/workspace/EnhancedContextBudgetBar.tsx` -- Context window meter (already existed)
- `ui/src/hooks/useWorkspaceChat.ts` -- token_usage handler reads message_count, rate_limit_logged event handler, frontend rate limit auto-detection
- `ui/src/lib/api.ts` -- API functions for usage, cost zones, rate limits, calibration
- `ui/src/lib/types.ts` -- `WorkspaceChatRateLimitLoggedMessage` type

---

## Feature 1: Global Usage Meters (Workspace + AutoForge Combined)

### The Problem

The usage tracking system built this session ONLY covers the **workspace chat**. It tracks tokens from workspace conversations stored in `workspace_database.py`. But the user also runs **AutoForge agent sessions** (the coding agent, initializer agent, parallel orchestrators) which consume from the SAME Anthropic subscription quota. Right now those are invisible to the usage meters.

This means: the user runs AutoForge for 2 hours building software, then opens the workspace to work on PRDs, and the workspace meter says "Today: 0 tokens" -- which is a lie. The real daily usage is much higher. They could be 80% toward their daily rate limit and have no idea.

### What Needs to Happen

The usage tracking needs to become **global** -- covering BOTH workspace chat AND AutoForge agent runs. The meters should show:

1. **Combined total** -- all tokens from all sources today/this week/this month
2. **Source breakdown** -- "Workspace: 150K, AutoForge: 800K" so you can see what's consuming your quota
3. **Per-project breakdown** within AutoForge -- "Project Alpha: 300K, Project Beta: 500K"

### Where AutoForge Token Data Lives

AutoForge agent sessions are managed by a completely separate code path:

- `autonomous_agent_demo.py` -- entry point that runs agent sessions
- `agent.py` -- agent session loop using Claude Agent SDK
- `client.py` -- creates `ClaudeSDKClient` with security hooks
- `progress.py` -- progress tracking, database queries, webhook notifications
- `parallel_orchestrator.py` -- concurrent agent execution

The agent output is streamed as text lines (stdout). There is **no per-message token tracking** in the AutoForge path today. The agent just runs until features are done.

### Implementation Approach

**Option A: Unified token ledger (recommended)**

Create a new global database table (in `~/.autoforge/usage_ledger.db` or add to the workspace database) that both systems write to:

```sql
create table usage_ledger (
    id integer primary key autoincrement,
    timestamp datetime default current_timestamp,
    source text not null,          -- "workspace" or "autoforge"
    project_name text,             -- null for workspace, project name for autoforge
    conversation_id integer,       -- workspace conversation ID, or null
    feature_id integer,            -- autoforge feature ID, or null
    agent_index integer,           -- for parallel mode (0-4)
    token_estimate integer not null default 0,
    token_type text default 'combined',  -- "input", "output", or "combined"
    model text,                    -- "claude-opus-4-6", etc.
    context_mode text,             -- "1m" or "200k"
    notes text
);

create index idx_usage_ledger_timestamp on usage_ledger(timestamp);
create index idx_usage_ledger_source on usage_ledger(source);
```

**For workspace**: The existing `add_message()` function in `workspace_database.py` already stores token estimates per message. Add a hook that ALSO writes to the global ledger. Or, simpler: the `get_usage_by_period()` aggregation queries could be modified to read from BOTH the workspace messages table AND the global ledger.

**For AutoForge**: The `agent.py` session loop needs to estimate tokens from agent output and write to the global ledger. The simplest approach: after each agent turn (each `receive_response()` iteration), estimate the response tokens and log to the ledger. The `autonomous_agent_demo.py` already prints output lines -- those could be metered.

The key files to instrument for AutoForge token tracking:
- `agent.py` -- the `run_agent_session()` function, specifically where it calls `client.receive_response()` in the streaming loop
- `parallel_orchestrator.py` -- each spawned agent subprocess. Since these are subprocesses, they'd need to write to the ledger independently
- `progress.py` -- already tracks feature pass/fail status. Could be extended to also track token usage per feature

**For the UI**: The existing `UsageDashboard` component fetches from `/api/workspace/usage`. This endpoint needs to be modified (or a new global endpoint created) that aggregates from both sources. The dashboard should show:

```
Today: 950K (87%)        [========--------]
  Workspace: 150K  |  AutoForge: 800K
Week: 3.2M (64%)         [======----------]
Month: 12.1M (41%)       [====------------]
```

### The Sleep/Work Schedule Problem

The user works approximately 10am-2am and sleeps/gets ready 2am-10am (roughly 8-12 hour gap). The critical constraint:

- **During work hours**: Workspace PRD work is the priority. AutoForge building should NOT consume so many tokens that it triggers the 5-hour rate limit during work hours.
- **During sleep hours**: This is the ideal time to run AutoForge builds, because if the rate limit is hit, the 5-hour cooldown expires before the user wakes up.

This suggests a **scheduling mode** or **budget allocation** system:

1. **Work mode** (manual toggle or time-based): Workspace gets priority. AutoForge is paused or throttled to a token budget that won't trigger the daily limit.
2. **Sleep mode** (toggled when going to bed): AutoForge runs unrestricted. If it hits the limit, the cooldown happens during sleep.

The existing `ScheduleModal.tsx` and `server/services/scheduler_service.py` already handle time-based agent scheduling. This could be extended with a "token budget" concept: "Run AutoForge but stop if daily usage exceeds X tokens" where X is calibrated from rate limit history.

Relevant existing files:
- `server/routers/schedules.py` -- CRUD for schedule entries
- `server/services/scheduler_service.py` -- APScheduler-based automated scheduling
- `api/database.py` -- Schedule and ScheduleOverride models
- `ui/src/components/ScheduleModal.tsx` -- Schedule management UI

---

## Feature 2: Nerfing Detection Meter

### The Problem

AI model performance varies over time. Sometimes a new model release performs exceptionally well for the first week or two, then quality degrades. This could be due to:

1. **Intentional throttling** ("nerfing") -- the provider reduces model quality to manage costs/capacity
2. **Infrastructure load** -- too many users hitting the same hardware, causing slower/worse responses
3. **Routing changes** -- requests being routed to different model versions or hardware
4. **Caching/quantization changes** -- the provider optimizes for throughput at the expense of quality

The user wants a **nerfing detection meter** that uses statistical analysis of build outcomes to detect when model performance has degraded.

### Data Source: AutoForge Build Metrics

AutoForge builds produce measurable outcomes for every feature:
- **Pass/fail on first attempt** -- did the feature pass lint, type check, and tests on the first try?
- **Number of retries** -- how many coding sessions were needed?
- **Error types** -- what kinds of errors occurred (syntax, logic, type errors, test failures)?
- **Time per feature** -- how long did each feature take?
- **Agent turns per feature** -- how many back-and-forth turns with Claude?

These metrics are already partially tracked:
- `api/database.py` -- Feature model has `status` (pending/in_progress/passing/failing), `priority`, `category`
- `mcp_server/feature_mcp.py` -- `feature_mark_passing`, `feature_mark_failing` track outcomes
- `progress.py` -- tracks pass counts, feature completion

### What's Missing for Nerfing Detection

To detect nerfing, we need **consistent longitudinal data**. The user plans to run 40+ phase builds, which gives us a large dataset. What we need to collect per feature:

```sql
create table build_quality_metrics (
    id integer primary key autoincrement,
    timestamp datetime default current_timestamp,
    project_name text not null,
    feature_id integer not null,
    feature_category text,
    feature_complexity text,        -- "small", "medium", "large" (from feature sizing)

    -- Outcome metrics
    passed_first_try boolean,
    retry_count integer default 0,
    total_agent_turns integer,
    total_tokens_used integer,
    duration_seconds integer,

    -- Error classification
    syntax_errors integer default 0,
    type_errors integer default 0,
    lint_errors integer default 0,
    test_failures integer default 0,
    logic_errors integer default 0,

    -- Model info
    model_name text,                -- "claude-opus-4-6"
    context_mode text,              -- "1m" or "200k"

    -- For nerfing detection
    error_rate float,               -- errors / total_turns
    quality_score float             -- composite score 0-100
);

create index idx_bqm_timestamp on build_quality_metrics(timestamp);
create index idx_bqm_model on build_quality_metrics(model_name);
```

### Detection Algorithm

The nerfing detection would work as a **rolling window anomaly detector**:

1. **Baseline period**: First N builds establish the baseline error rate and quality score. Could use the first 10 builds, or a configurable window.

2. **Rolling average**: Maintain a 10-build rolling average of `error_rate` and `quality_score`.

3. **Anomaly detection**: If the current rolling average deviates from the baseline by more than a threshold (e.g., 2 standard deviations), flag it as potential nerfing.

4. **Confounding factor filtering**: Before flagging nerfing, check:
   - Is the feature complexity higher than baseline? (harder features = more errors, not nerfing)
   - Is the PRD quality lower? (if we have PRD quality scoring from the build-intelligence system)
   - Is the context window usage higher? (degradation from context, not nerfing)
   - Did the model name change? (different model = different baseline)

5. **Output**: A simple gauge:
   - **Green**: Performance within normal range
   - **Yellow**: Slight degradation detected (1-2 sigma)
   - **Red**: Significant degradation (2+ sigma), possible nerfing
   - **Data needed**: Show "Need N more builds for baseline" when insufficient data

### Where to Instrument

The best place to collect build quality metrics is in the agent session completion flow:

- `agent.py` -- after `run_agent_session()` completes, log metrics for all features that were worked on
- `autonomous_agent_demo.py` -- after each session, collect outcomes from the features database
- `parallel_orchestrator.py` -- after all agents complete, aggregate metrics

The UI would show the nerfing meter in the main AutoForge dashboard (`AgentMissionControl.tsx`) and optionally in the workspace `UsageDashboard`.

### Important Consideration

The user noted that different agents have different "personalities" -- some are more robust than others at high context percentages. This is real (stochastic sampling variance). The nerfing detector should account for this by:
- Using a LARGE enough sample size (10+ builds minimum)
- Looking at TRENDS, not individual outliers
- Comparing against the SAME model only (don't mix Opus and Sonnet baselines)

---

## Feature 3: Personal Style Learning ("Tim's Way")

### The Problem

When the user builds software through AutoForge, the agent makes decisions at every gap in the spec -- which UI library to use, how to structure state management, what error handling pattern to apply, etc. These decisions are currently made by the agent's default preferences. But the user has **consistent preferences** that emerge across builds: they favor certain patterns, avoid others, make specific tradeoff decisions predictably.

After 5+ software builds, there's enough data to detect these patterns. After 20+, the agent could accurately predict "Tim would do it this way" and apply those preferences automatically when the spec has gaps.

### How It Would Work

1. **Decision logging**: Every time the user makes a decision during spec creation, feature refinement, or build review that overrides or guides the agent, log it:
   - "User chose Tailwind over styled-components"
   - "User prefers server-side validation over client-only"
   - "User always wants toast notifications, never alert dialogs"
   - "User prefers flat file structure over deeply nested"

2. **Pattern extraction**: After N logged decisions, cluster them into preference categories:
   - **UI patterns**: component libraries, styling approach, animation preferences
   - **Architecture patterns**: state management, API design, folder structure
   - **Quality preferences**: error handling verbosity, test coverage expectations, code comment density
   - **Business logic patterns**: how they handle auth, payments, user roles, etc.

3. **Preference injection**: When generating prompts for AutoForge agents, inject learned preferences:
   ```
   [User Preferences - learned from 20 previous builds]
   - Always use Tailwind CSS v4 with the neobrutalism design pattern
   - Prefer React Query for server state, Zustand for client state
   - Use toast notifications for user feedback, never alert()
   - Flat component structure: src/components/{ComponentName}.tsx
   - Always include loading skeletons, not spinners
   ```

4. **Confidence scoring**: Each preference gets a confidence score based on how consistently it was chosen. Only inject preferences above a threshold (e.g., 80% consistency across 5+ decisions).

### Implementation Location

This would primarily live in the prompt generation pipeline:
- `prompts.py` -- `get_coding_prompt()` and `get_initializer_prompt()` would inject learned preferences
- A new `~/.autoforge/user_preferences.db` or table in the registry database to store learned patterns
- The spec creation flow (`.claude/commands/create-spec.md`, `server/services/spec_chat_session.py`) could also apply preferences during spec generation
- The expand project flow (`server/services/expand_chat_session.py`) similarly

### Bootstrapping

For cold-start (no data yet), the system could:
1. Ask the user to fill out a "style questionnaire" (5-10 questions about preferences)
2. Import preferences from an existing project's tech stack detection
3. Learn passively from the first few builds without injecting anything

---

## Priority Order

Based on the user's immediate needs:

1. **Feature 1: Global usage meters** -- HIGHEST PRIORITY. The user is about to start running AutoForge builds alongside workspace work. Without global tracking, they'll hit the 5-hour wall unexpectedly during work hours. The sleep/work schedule awareness is critical.

2. **Feature 2: Nerfing detection** -- MEDIUM PRIORITY. Needs data from 40+ phase builds to be useful. Start collecting metrics now so the detector has data when it's ready.

3. **Feature 3: Style learning** -- LOWER PRIORITY but high long-term value. Can be bootstrapped after 5+ software builds. Start with decision logging now, build the injection later.

---

## Technical Notes

- The workspace database lives at `~/.autoforge/workspace.db` (SQLAlchemy, managed by `server/services/workspace_database.py`)
- AutoForge per-project databases are at `{project_dir}/.autoforge/features.db`
- The project registry is at `~/.autoforge/registry.db`
- For global usage tracking, a new `~/.autoforge/usage_ledger.db` is recommended (or add tables to workspace.db)
- The UI build command is `cd ui && npm run build` (Vite 7)
- Python linting: `ruff check .` (line length 120, Python 3.11 target)
- TypeScript checking: `cd ui && npx tsc --noEmit`
