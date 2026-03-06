# PRD: Orchestrator & State Layer Completion

**Status:** Draft
**Date:** 2026-03-06
**Priority:** High
**Depends on:** parallel_orchestrator.py, factory_controller.py, agent.py, security.py, progress.py

---

## Executive Summary

An audit of the orchestrator and state machine layers found **production-ready** orchestration, security, and prompt contracts — but identified six gaps that prevent full observability, auditability, and supervised autonomy. This PRD scopes the work to close those gaps.

---

## Current State (What's Solid)

| Component | Maturity | Notes |
|-----------|----------|-------|
| Parallel Orchestrator | ★★★★ | Dependency scheduling, multi-agent, atomic claims |
| Factory Controller | ★★★★ | Multi-phase state, rate limit handling, persistence |
| Security Policy | ★★★★ | Hierarchical allowlist, path validation, defense-in-depth |
| System Prompt Contract | ★★★★★ | Budget tracking, role clarity, wrap-up protocol |
| Feature State Model | ★★★★ | SQLite with status + deps, composite indexes |

---

## Gaps to Close

### Gap 1: Approval Gates (Human-in-the-Loop)

**Problem:** `DANGEROUS_COMMANDS` in security.py (sudo, kubectl, aws, gcloud, az) are currently hard-blocked. There's no way for a supervised operator to approve a dangerous command for a specific run.

**Requirements:**

1. **Approval Request Model**
   - New SQLAlchemy model `ApprovalRequest` in `api/database.py`
   - Fields: `id`, `agent_id`, `command`, `reason`, `status` (pending/approved/denied/expired), `requested_at`, `resolved_at`, `resolved_by`
   - TTL: requests expire after 5 minutes if unresolved

2. **Approval API**
   - `POST /api/approvals` — agent requests approval (called from security hook)
   - `GET /api/approvals?status=pending` — UI polls for pending requests
   - `PUT /api/approvals/{id}` — operator approves or denies
   - WebSocket event `approval_request` pushed to UI in real-time

3. **Security Hook Integration**
   - In `security.py`, when a command matches `DANGEROUS_COMMANDS`:
     - Create `ApprovalRequest` record
     - Push WebSocket notification to UI
     - Block execution, return "awaiting approval" message to agent
     - On approval: execute command (one-shot, not blanket)
     - On denial/expiry: return denial message to agent

4. **UI Component**
   - Approval banner/modal in `AgentMissionControl.tsx`
   - Shows: command, requesting agent, timestamp, approve/deny buttons
   - Audio chime on new request (optional, settings toggle)

5. **Audit Trail**
   - All approval decisions logged to `ApprovalRequest` table
   - Queryable via `GET /api/approvals?status=all`

**Scope:** ~3 files new, ~4 files modified
**Risk:** Low — additive only, blocked commands stay blocked until approval flow is wired

---

### Gap 2: Structured Action History

**Problem:** No structured log of what tools the agent called, what results came back, or timestamps. Debugging agent behavior requires reading raw stdout.

**Requirements:**

1. **Action Log Model**
   - New table `action_log` in the project's `features.db`
   - Fields: `id`, `session_id`, `agent_index`, `turn_number`, `tool_name`, `tool_input_summary` (truncated to 500 chars), `result_summary` (truncated to 1000 chars), `duration_ms`, `status` (success/error), `created_at`
   - Index on `(session_id, created_at)`

2. **Log Capture Hook**
   - In `agent.py`, wrap the agent SDK's tool-use callback to emit action log entries
   - Capture: tool name, truncated input, truncated output, wall-clock duration
   - Write to DB in batches (every 10 actions or 5 seconds, whichever first)

3. **API Endpoints**
   - `GET /api/projects/{name}/actions?session_id=X&limit=50&offset=0` — paginated action history
   - `GET /api/projects/{name}/actions/summary` — counts by tool name, error rate

4. **UI Integration**
   - New "Action Log" tab in project detail view
   - Table: timestamp, tool, input preview, status, duration
   - Filter by session, tool name, status
   - Click to expand full input/output

**Scope:** ~2 files new, ~3 files modified
**Risk:** Low — read-only logging, no impact on agent execution path

---

### Gap 3: Artifact Versioning (Checkpoints)

**Problem:** No way to snapshot code state at key moments (feature complete, before risky refactor, phase boundary). Only git commits exist, which are agent-authored and inconsistent.

**Requirements:**

1. **Checkpoint Model**
   - New table `checkpoints` in project's `features.db`
   - Fields: `id`, `session_id`, `label` (e.g. "feature-3-complete", "phase-2-start"), `git_sha`, `feature_snapshot` (JSON of all feature statuses), `created_at`

2. **Automatic Checkpoints**
   - Created when: feature marked passing, phase boundary in factory mode, agent session ends
   - Each checkpoint records the git SHA + full feature status snapshot

3. **Manual Checkpoints**
   - MCP tool `checkpoint_create(label)` available to agents
   - API endpoint `POST /api/projects/{name}/checkpoints` for UI

4. **Rollback Support**
   - `POST /api/projects/{name}/checkpoints/{id}/rollback` — creates a new branch at that SHA, resets feature statuses to snapshot
   - Confirmation required (returns preview of what changes)

5. **UI**
   - Checkpoint timeline in project detail view
   - Shows: label, SHA (short), feature counts at that point, timestamp
   - "Rollback to here" button with confirmation dialog

**Scope:** ~2 files new, ~4 files modified
**Risk:** Medium — rollback touches git state; requires confirmation gate

---

### Gap 4: Verification Result Persistence

**Problem:** Test results (pass/fail, console output, screenshots) are ephemeral. Can't inspect what happened in a prior test run.

**Requirements:**

1. **Verification Log Model**
   - New table `verification_results` in project's `features.db`
   - Fields: `id`, `feature_id`, `session_id`, `agent_index`, `test_type` (lint/typecheck/e2e/manual), `passed` (bool), `output` (text, truncated to 10KB), `duration_ms`, `created_at`

2. **Capture Points**
   - Agent marks feature passing/failing → attach verification output
   - MCP tool `feature_mark_passing` / `feature_mark_failing` extended with optional `verification_output` param
   - Testing agent's Playwright results captured automatically

3. **API Endpoints**
   - `GET /api/projects/{name}/features/{id}/verifications` — history of all test runs for a feature
   - `GET /api/projects/{name}/verifications?passed=false` — all failures across features

4. **UI**
   - In feature detail panel: "Verification History" section
   - Each entry: test type, pass/fail badge, timestamp, expandable output
   - Failed verifications highlighted in red

**Scope:** ~1 file new, ~4 files modified (MCP server, database model, API router, UI)
**Risk:** Low — additive, extends existing mark_passing/failing flow

---

### Gap 5: Commit Message Standardization

**Problem:** Agent-authored commit messages are inconsistent. No template or validation. Makes git log hard to parse for progress tracking.

**Requirements:**

1. **Commit Message Template**
   - Format: `[autoforge] <type>(<scope>): <description>`
   - Types: `feat`, `fix`, `test`, `refactor`, `chore`
   - Scope: feature ID or "system"
   - Example: `[autoforge] feat(#3): Add user authentication form`

2. **Template Injection**
   - Add commit message format to `coding_prompt.template.md` in the STEP 0 / orientation section
   - Include 3 examples in the prompt

3. **Validation (Soft)**
   - In `progress.py` or a new `commit_utils.py`: function to parse and validate commit messages
   - Log warnings for non-conforming messages (don't block commits)
   - Factory controller can include conformance stats in phase summaries

4. **Git Log Parsing**
   - Utility function to extract feature IDs from commit messages
   - Used by handoff package to show per-feature commit history
   - API endpoint: `GET /api/projects/{name}/commits?feature_id=3`

**Scope:** ~1 file new, ~2 files modified
**Risk:** Low — soft validation only, no blocking

---

### Gap 6: Log Compaction

**Problem:** `orchestrator_debug.log`, action history, and verification results grow unbounded. No cleanup strategy.

**Requirements:**

1. **Retention Policy**
   - Default: 30 days for action_log, verification_results
   - Default: 7 days for orchestrator_debug.log
   - Configurable in `~/.autoforge/config.yaml` under `retention:` key

2. **Compaction Job**
   - Runs on server startup and daily via APScheduler (already used for scheduling)
   - Deletes rows older than retention period
   - Rotates `orchestrator_debug.log` (rename to `.1`, `.2`, keep 3 rotations)

3. **Summary Preservation**
   - Before deleting old action_log entries: aggregate into `action_log_summary` table
   - Fields: `date`, `session_id`, `tool_name`, `call_count`, `error_count`, `avg_duration_ms`
   - Summaries kept indefinitely (tiny rows)

4. **Settings UI**
   - Add retention settings to Settings modal
   - Fields: action log days, verification log days, debug log days

**Scope:** ~1 file new, ~3 files modified
**Risk:** Low — only deletes old data, summaries preserved

---

## Implementation Order

| Phase | Gaps | Rationale |
|-------|------|-----------|
| **Phase A** | #2 (Action History) + #5 (Commit Messages) | Foundation — needed by everything else, low risk |
| **Phase B** | #4 (Verification Results) + #3 (Checkpoints) | Build on action history, adds observability |
| **Phase C** | #1 (Approval Gates) | Highest complexity, needs UI + security changes |
| **Phase D** | #6 (Log Compaction) | Cleanup — do last once we know what's being logged |

---

## Database Schema Summary

```sql
-- Gap 1: Approval Gates
CREATE TABLE approval_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    command TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/approved/denied/expired
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by TEXT
);

-- Gap 2: Action History
CREATE TABLE action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_index INTEGER DEFAULT 0,
    turn_number INTEGER,
    tool_name TEXT NOT NULL,
    tool_input_summary TEXT,        -- truncated to 500 chars
    result_summary TEXT,            -- truncated to 1000 chars
    duration_ms INTEGER,
    status TEXT NOT NULL DEFAULT 'success',  -- success/error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_action_log_session ON action_log(session_id, created_at);

-- Gap 3: Checkpoints
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    label TEXT NOT NULL,
    git_sha TEXT NOT NULL,
    feature_snapshot TEXT,          -- JSON blob
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gap 4: Verification Results
CREATE TABLE verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL REFERENCES features(id),
    session_id TEXT,
    agent_index INTEGER DEFAULT 0,
    test_type TEXT NOT NULL,        -- lint/typecheck/e2e/manual
    passed BOOLEAN NOT NULL,
    output TEXT,                    -- truncated to 10KB
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_verification_feature ON verification_results(feature_id, created_at);

-- Gap 6: Log Compaction Summaries
CREATE TABLE action_log_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    session_id TEXT,
    tool_name TEXT NOT NULL,
    call_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    avg_duration_ms INTEGER,
    UNIQUE(date, session_id, tool_name)
);
```

---

## Success Criteria

- [ ] Operator can approve/deny dangerous commands from the UI with full audit trail
- [ ] Every tool call by every agent is logged with timestamps and searchable via API
- [ ] Automatic checkpoints at phase boundaries and feature completions, with rollback capability
- [ ] Test results for every feature are persisted and viewable in the UI
- [ ] Agent commit messages follow a parseable convention
- [ ] Logs older than retention period are compacted without losing summary data

---

## Out of Scope

- Multi-user approval workflows (single operator is sufficient)
- Real-time streaming of action logs (polling/refresh is fine)
- Screenshot capture from Playwright runs (future enhancement)
- Cross-project action log queries
