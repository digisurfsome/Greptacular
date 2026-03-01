# DunkStack Benchmark Protocol

> **Purpose**: The exact tests, PRDs, scoring criteria, and procedures for measuring whether DunkStack's file-based system actually delivers on its four claimed benefits. Hand this to any agent running benchmarks.

---

## Overview

We're testing four claims. Each has a specific test methodology:

| Claim | Test Name | What We Measure |
|-------|-----------|-----------------|
| Cheaper API calls | Cost Comparison | Total tokens billed, DunkStack vs. standard agent |
| Sharper agents | Consistency Test | Code quality at 4 token checkpoints |
| Longer effective context | Memory Recall Test | Constraint adherence at 3 late-session checkpoints |
| Multi-agent communication | Communication Test | Agents reading/acting on each other's file output |

---

## Test Setup

### Requirements
- Two identical registered projects (one for DunkStack, one for control)
- Same model for both runs (start with 200K, then repeat with 1M)
- Same PRD fed to both
- Record token counts at each checkpoint (DunkStack has ContextGauge; for control, check API usage dashboard or billing)

### The Control Run
The **control** is a standard agent session — regular Claude Code or AutoForge, no file system, normal chat-based conversation. Same PRD, same model, same tasks. This is what we're comparing against.

### Checkpoint Token Targets (200K model)
| Checkpoint | Token Target | When to Insert Test Task |
|------------|-------------|--------------------------|
| CP-1 | ~10K tokens | Early session, agent is fresh |
| CP-2 | ~35K tokens | Mid-early, some context accumulated |
| CP-3 | ~65K tokens | Mid-late, significant context load |
| CP-4 | ~90K tokens | Late session, approaching limits |

For the 1M model, scale proportionally: CP-1 at ~50K, CP-2 at ~175K, CP-3 at ~325K, CP-4 at ~450K.

---

## Test 1: The Consistency Test (Sharpness)

### Purpose
Measure whether code quality stays constant as context fills up.

### Method
Give the agent 4 coding tasks of **identical difficulty** at each checkpoint. Each task has **8 specific requirements** with clear pass/fail criteria. Score each task. Compare scores across checkpoints.

**If DunkStack works**: Scores stay flat (8/8 at every checkpoint).
**If it doesn't**: Scores drop at later checkpoints (same as a normal agent).
**Comparison**: Run the same 4 tasks on the control agent at the same token checkpoints.

### The PRD (Feed This First)

Paste this into the walkie-talkie at session start. This gives the agent a project to work on between checkpoints, burning tokens naturally:

```
# TaskFlow — A Task Management API

Build a REST API for a task management system using Node.js, Express, and SQLite.

## Core Requirements

### Data Model
- Users: id, email, name, role (admin/member), created_at
- Projects: id, name, description, owner_id (FK to users), created_at
- Tasks: id, title, description, status (todo/in_progress/done), priority (low/medium/high/critical), assignee_id (FK to users), project_id (FK to projects), due_date, created_at, updated_at

### Endpoints to Build
- CRUD for users, projects, and tasks
- GET /projects/:id/tasks — list tasks with filtering by status and priority
- POST /tasks/:id/assign — assign a task to a user
- GET /users/:id/tasks — get all tasks assigned to a user
- GET /projects/:id/stats — task counts by status

### Technical Standards
- All timestamps in UTC, stored as ISO 8601 strings
- All API responses include a `request_id` field (UUID v4) and a `timestamp` field
- All error responses use format: { "error": "message", "code": "ERROR_CODE", "request_id": "uuid" }
- Database table names must be snake_case and plural
- All input must be validated with a schema validator (Zod, Joi, or similar) before processing
- All list endpoints support pagination with `page` and `limit` query params

Build this incrementally. Start with the database schema, then users CRUD, then projects, then tasks.
```

### The 4 Checkpoint Tasks

After the agent has been building the TaskFlow app and reaches each token checkpoint, interrupt with one of these tasks. Paste it into the walkie-talkie.

---

#### CP-1 Task (~10K tokens): Email Notification Service

```
Build an email notification service module (notifications.ts or notifications.js).

Requirements (all 8 must be met):
1. Export a function `sendTaskNotification(taskId, eventType, recipientEmail)` where eventType is one of: "assigned", "due_soon", "overdue", "completed"
2. Each event type must produce a different subject line (not generic)
3. The email body must include the task title, project name, and a link formatted as /tasks/{taskId}
4. Must validate that recipientEmail is a valid email format before sending (regex or library)
5. Must throw a typed error `NotificationError` (custom error class) if sending fails
6. Must log every send attempt with timestamp, recipient, event type, and success/failure to a file `notifications.log`
7. Must be async and return a Promise<{ sent: boolean, messageId: string }>
8. Must have a rate limiter: max 10 emails per recipient per hour, throw `RateLimitError` if exceeded
```

---

#### CP-2 Task (~35K tokens): Activity Feed Generator

```
Build an activity feed module (activity_feed.ts or activity_feed.js).

Requirements (all 8 must be met):
1. Export a function `getActivityFeed(projectId, options?)` that returns the last N activities for a project
2. Activities must be generated from task state changes (created, assigned, status changed, completed)
3. Each activity entry must have: id, actor (user name), action (verb string), target (task title), timestamp, metadata (object)
4. The `options` parameter must support: limit (default 20, max 100), before (cursor-based pagination using timestamp), after (filter activities after this date)
5. Must aggregate rapid sequential actions: if the same user performs 3+ actions within 60 seconds, collapse into "X made N changes to Y"
6. Must sanitize all user-generated content in the feed (strip HTML tags, limit string lengths to 500 chars)
7. Must return results sorted by timestamp descending with a `hasMore` boolean for pagination
8. Must cache results for 30 seconds using an in-memory cache with TTL, and invalidate cache when new activities are added
```

---

#### CP-3 Task (~65K tokens): Search & Filter Engine

```
Build a search and filter module (search.ts or search.js).

Requirements (all 8 must be met):
1. Export a function `searchTasks(query, filters, options?)` that performs full-text search across task titles and descriptions
2. Filters must support: status (array), priority (array), assignee_id, project_id, due_before (date), due_after (date) — all optional and combinable
3. Must support AND logic between different filter types and OR logic within array filters (e.g., status: ["todo", "in_progress"] means either)
4. Must rank results by relevance: exact title match > title contains > description contains, with ties broken by updated_at descending
5. Options must support: page (default 1), limit (default 25, max 50), sort_by (relevance/created_at/due_date/priority), sort_order (asc/desc)
6. Must return: { results: Task[], total: number, page: number, pages: number, query: string, applied_filters: object }
7. Must handle edge cases: empty query returns all (filtered only), special characters in query must be escaped for SQL safety, whitespace-only query treated as empty
8. Must build SQL queries using parameterized statements (no string concatenation), and log every search with query, filter count, result count, and execution time in ms
```

---

#### CP-4 Task (~90K tokens): Webhook Dispatcher

```
Build a webhook dispatcher module (webhooks.ts or webhooks.js).

Requirements (all 8 must be met):
1. Export a function `registerWebhook(projectId, url, events[])` where events is a subset of: "task.created", "task.updated", "task.completed", "task.deleted"
2. Export a function `dispatchWebhook(projectId, event, payload)` that sends POST requests to all registered webhooks for that event
3. Each webhook POST must include headers: X-Webhook-Id (UUID), X-Webhook-Event (event name), X-Webhook-Timestamp (ISO 8601), X-Webhook-Signature (HMAC-SHA256 of body using a per-webhook secret)
4. Must retry failed deliveries (non-2xx response) up to 3 times with exponential backoff: 1s, 4s, 16s
5. Must track delivery status per webhook: { webhook_id, event, status (pending/delivered/failed), attempts, last_attempt_at, response_code }
6. Must validate webhook URLs: must be HTTPS (except localhost for dev), must resolve to a valid host, must not be a private IP range (10.x, 172.16-31.x, 192.168.x)
7. Must support `unregisterWebhook(webhookId)` that removes and cancels any pending retries
8. Must enforce a max of 10 webhooks per project, return a structured error if limit exceeded
```

---

### Scoring

For each checkpoint task, grade each of the 8 requirements as:
- **Pass (1)** — requirement fully implemented and correct
- **Partial (0.5)** — attempted but has bugs or is incomplete
- **Fail (0)** — missing or fundamentally wrong

**Score per checkpoint** = sum of 8 requirements (max 8.0)

**Expected results**:

| Checkpoint | DunkStack (hypothesis) | Normal Agent (expected) |
|------------|----------------------|------------------------|
| CP-1 (10K) | 7.5-8.0 | 7.5-8.0 |
| CP-2 (35K) | 7.5-8.0 | 7.0-7.5 |
| CP-3 (65K) | 7.0-8.0 | 6.0-7.0 |
| CP-4 (90K) | 7.0-7.5 | 5.0-6.5 |

The key metric is **score drop from CP-1 to CP-4**. DunkStack should show minimal drop. Normal agent should show significant drop.

---

## Test 2: The Memory Recall Test (Effective Context Length)

### Purpose
Measure whether the agent remembers early constraints when building late features.

### Method
The PRD above contains **6 embedded constraints** (the "Technical Standards" section). These are specific, checkable rules. As the agent builds features throughout the session, check whether late-session code still follows these rules — without reminding the agent.

### The 6 Constraints to Track

These are already in the TaskFlow PRD above:

| # | Constraint | How to Check |
|---|-----------|-------------|
| C1 | All timestamps in UTC, stored as ISO 8601 strings | Search generated code for `new Date()` without `.toISOString()`, or local timezone references |
| C2 | All API responses include `request_id` (UUID v4) and `timestamp` fields | Check if endpoint responses include these fields |
| C3 | Error responses use format `{ error, code, request_id }` | Check error handlers in generated code |
| C4 | Database table names are snake_case and plural | Check schema definitions |
| C5 | All input validated with schema validator before processing | Check if endpoint handlers validate input |
| C6 | All list endpoints support `page` and `limit` query params | Check list endpoint implementations |

### Memory Recall Checkpoints

At three points in the session, ask the agent to build a **new feature** that should naturally follow all 6 constraints — but **do NOT remind it of the constraints**. Just describe the feature:

#### MR-1 (~50K tokens): "Build a comments endpoint"

```
Add a comments system. Users can comment on tasks. Build:
- POST /tasks/:id/comments — add a comment
- GET /tasks/:id/comments — list comments for a task
- DELETE /comments/:id — delete a comment (author or admin only)
```

**Check**: Does the code include request_id in responses? Validation? Pagination? UTC timestamps? Proper error format?

#### MR-2 (~75K tokens): "Build a labels/tags system"

```
Add labels to tasks. Build:
- POST /projects/:id/labels — create a label (name + color)
- GET /projects/:id/labels — list labels
- POST /tasks/:id/labels — attach a label to a task
- DELETE /tasks/:id/labels/:labelId — remove a label
- GET /tasks?label=:labelName — filter tasks by label
```

**Check**: Same 6 constraints. Especially: is the table `labels` (not `Label`)? Is the filter endpoint paginated?

#### MR-3 (~95K+ tokens): "Build an audit log"

```
Add an audit log that tracks all changes to tasks. Build:
- Middleware or hook that captures: who changed what, old value, new value, timestamp
- GET /projects/:id/audit-log — list audit entries with filtering by date range and user
- GET /tasks/:id/audit-log — audit entries for a specific task
```

**Check**: Same 6 constraints. This is the final test — deep in the session, does the agent still remember the rules from the beginning?

### Scoring

For each Memory Recall checkpoint, grade each of the 6 constraints:
- **Remembered (1)** — constraint followed correctly without being reminded
- **Partially (0.5)** — some instances follow the constraint, others don't
- **Forgotten (0)** — constraint ignored entirely

**Score per checkpoint** = sum of 6 (max 6.0)

**Expected results**:

| Checkpoint | DunkStack (hypothesis) | Normal Agent (expected) |
|------------|----------------------|------------------------|
| MR-1 (50K) | 5.5-6.0 | 4.5-5.5 |
| MR-2 (75K) | 5.0-6.0 | 3.5-5.0 |
| MR-3 (95K) | 5.0-5.5 | 2.5-4.0 |

**Key metric**: How many constraints does the agent still remember at MR-3? DunkStack should remember most (they're in working_memory.md or knowledge files). Normal agent will have them buried 95K tokens back in conversation history.

---

## Test 3: Cost Comparison

### Purpose
Measure the actual dollar savings of DunkStack vs. standard agent.

### Method
This is the simplest test — just run the same build on both systems and compare bills.

### What to Record

| Metric | DunkStack | Control | Calculation |
|--------|-----------|---------|-------------|
| Total input tokens (cumulative) | From ContextGauge | From API dashboard | - |
| Total output tokens (cumulative) | From ContextGauge | From API dashboard | - |
| Cache read tokens | From ContextGauge | From API dashboard | - |
| Cache creation tokens | From ContextGauge | From API dashboard | - |
| Total cost (USD) | From ContextGauge | From API dashboard | - |
| Number of API calls | From ContextGauge | From API dashboard | - |
| Conversation tokens (non-tool) | See below | See below | - |
| Tool-use tokens | See below | See below | - |
| **Cost savings** | - | - | `(Control - DunkStack) / Control × 100%` |

### Isolating Conversation vs. Tool-Use Tokens

This is the key comparison. In DunkStack, conversation tokens should be tiny (just status messages). In the control, conversation tokens grow every turn because the full history is included.

DunkStack already tracks total input/output. To isolate conversation vs. tool tokens, check the token log entries (`/api/dunkstack/tokens/log`). Each entry corresponds to an API call. Entries where the agent was reading/writing files are tool-heavy. Entries that are pure conversation are the baseline.

For a rough split: compare the **average tokens per API call** between DunkStack and control. DunkStack should have lower average input tokens per call (because conversation history is thin).

---

## Test 4: Communication Test (Multi-Agent File Handoff)

### Purpose
Prove that Agent B can receive knowledge from Agent A **exclusively through the file system** — no shared chat, no shared context, no central controller passing messages. This is the patent-critical test for file-based inter-agent communication.

### Why This Can Be Tested Now
DunkStack currently runs one agent per project (session registry is keyed by project name — starting a second kills the first). But **sequential handoff is actually a stronger proof** than simultaneous agents: Agent A's entire context is gone when Agent B starts. If B still produces correct work based on A's output, knowledge transferred through files and files alone.

Simultaneous multi-agent requires a small code change (multi-key session registry). That's Phase 3 work. This test proves the communication protocol works without that change.

### Estimated Time: 15-20 Minutes

### Method

#### Step 1: Agent A — The Architect (5-8 minutes)

Start a DunkStack agent. Paste this into the walkie-talkie:

```
You are Agent A — the Architect. Your job is to design a system and leave your work in files for the next agent.

Design a blog platform database schema and API. Write ALL of your output to files — the next agent will read them.

Create these files:

1. `.agent/output/schema_design.md` — Full database schema with:
   - 4 tables: users, posts, comments, tags
   - Every column: name, type, constraints, foreign keys
   - A many-to-many join table for posts<->tags
   - Include 3 specific business rules (e.g., "posts must have at least one tag", "comments can only be edited within 15 minutes", "users can have a max of 5 draft posts")

2. `.agent/output/api_design.md` — API endpoint specification:
   - At least 8 endpoints with method, path, request body, response shape
   - Error codes and their meanings
   - A specific pagination pattern (cursor-based, not offset-based)

3. `.agent/output/architecture_notes.md` — Key decisions:
   - Why cursor-based pagination (not offset)
   - A specific note about the posts-tags relationship
   - At least one performance recommendation

Do NOT create any actual code files. Only write the design documents above. When you're done, update .agent/working_memory.md and write a summary to .agent/comms/to_human.md.
```

Wait for Agent A to finish writing all 3 files. Verify the files exist and have content. Then **stop the agent session.**

#### Step 2: Verify Agent A's Context Is Gone

After stopping Agent A:
- The DunkStack session is destroyed
- Agent A's conversation history is gone
- The ONLY things that persist are the files in `.agent/`
- This is critical — Agent B has zero access to Agent A's thoughts, reasoning, or conversation

#### Step 3: Agent B — The Builder (8-12 minutes)

Start a **new** DunkStack agent on the **same project**. Paste this:

```
You are Agent B — the Builder. A previous architect agent designed a system and left their work in files.

Read these files:
- .agent/output/schema_design.md
- .agent/output/api_design.md
- .agent/output/architecture_notes.md

Then implement the system EXACTLY as designed:

1. Create the database schema code (SQLite with an ORM or raw SQL — your choice)
2. Implement ALL endpoints from the API design document
3. Follow the pagination pattern specified in the design
4. Implement ALL business rules from the schema design
5. Follow the performance recommendation from the architecture notes

Write your implementation to the project source directory (not .agent/).

IMPORTANT: You must follow the architect's design exactly. Do not deviate, add extra endpoints, or change the schema. Your job is faithful implementation of what was designed.

When done, write a build report to .agent/output/build_report.md listing:
- Each endpoint implemented (with the file/line number)
- Each business rule implemented (with the file/line number)
- Any issues or ambiguities you found in the design
```

#### Step 4: Score the Communication

After Agent B finishes, grade these criteria:

| # | Criterion | Pass/Fail | How to Check |
|---|-----------|-----------|-------------|
| COM-1 | Agent B read all 3 design files | | Check agent's tool use — did it Read the files? |
| COM-2 | Database schema matches Agent A's design (all tables, columns, FKs) | | Compare code against schema_design.md |
| COM-3 | All 8+ API endpoints implemented matching Agent A's spec | | Compare endpoints against api_design.md |
| COM-4 | Cursor-based pagination (not offset) used as A specified | | Check pagination implementation |
| COM-5 | All 3 business rules from schema_design.md implemented | | Check for rule enforcement in code |
| COM-6 | Performance recommendation followed | | Check for A's specific suggestion in code |
| COM-7 | Agent B did NOT add extra endpoints/tables not in A's design | | Compare — B should be faithful, not creative |
| COM-8 | Build report correctly maps back to A's design documents | | Read build_report.md |

**Score**: X/8

**Pass threshold**: 6/8 or higher = communication proven.

### What This Proves (Patent Language)

If Agent B scores 6+/8:
- **Knowledge transferred through files alone** — no shared context, no message passing, no central controller
- **Agent A's reasoning was preserved in structured documents** — schema, API spec, architecture notes
- **Agent B independently reconstructed the architect's intent** and produced faithful implementation
- **Zero conversation tokens were shared** between agents — total isolation except through the file system
- **The file system acted as the sole communication channel** — this is the patentable mechanism

### What This Doesn't Prove (Yet)
- Simultaneous agent collaboration (requires multi-key session registry — Phase 3)
- Real-time back-and-forth between agents (requires file-watching or polling — Phase 3)
- Scaling beyond 2 agents (requires orchestration logic — Phase 3)

But the core protocol — agents communicating through files — is proven if this test passes.

---

## Running the Full Benchmark

### Step-by-Step Procedure

**Run 1: DunkStack (test subject)**

1. Register a fresh project, start DunkStack agent
2. Paste the TaskFlow PRD into walkie-talkie
3. Let agent build. Monitor ContextGauge
4. At ~10K tokens: paste CP-1 task (Email Notification). Wait for completion. Score it
5. Let agent continue building
6. At ~35K tokens: paste CP-2 task (Activity Feed). Wait for completion. Score it
7. Let agent continue building
8. At ~50K tokens: paste MR-1 (Comments). Wait for completion. Score constraints
9. At ~65K tokens: paste CP-3 task (Search & Filter). Wait for completion. Score it
10. At ~75K tokens: paste MR-2 (Labels). Wait for completion. Score constraints
11. At ~90K tokens: paste CP-4 task (Webhooks). Wait for completion. Score it
12. At ~95K tokens: paste MR-3 (Audit Log). Wait for completion. Score constraints
13. Record final token/cost numbers from ContextGauge

**Run 2: Control (standard agent)**

1. Same project setup, same model, but use regular Claude Code / AutoForge (no file system)
2. Same PRD, same checkpoint tasks at same token targets
3. Same scoring

**Run 3 (optional): Million-token model**

1. Repeat Run 1 with 1M model, scaled checkpoints
2. See if it can build the entire thing in one session
3. Compare cost against Run 1 + Run 2

### Results Template

```
# Benchmark Results — [Date]

## Setup
- Model: [model name and ID]
- DunkStack version: [commit hash]
- Control method: [Claude Code / AutoForge / other]

## Consistency Test (Sharpness)
| Checkpoint | Tokens | DunkStack Score | Control Score |
|------------|--------|----------------|---------------|
| CP-1       | ~10K   |    /8          |    /8         |
| CP-2       | ~35K   |    /8          |    /8         |
| CP-3       | ~65K   |    /8          |    /8         |
| CP-4       | ~90K   |    /8          |    /8         |
| **Drop**   |        | CP1-CP4 =      | CP1-CP4 =     |

## Memory Recall Test (Context Length)
| Checkpoint | Tokens | DunkStack Score | Control Score |
|------------|--------|----------------|---------------|
| MR-1       | ~50K   |    /6          |    /6         |
| MR-2       | ~75K   |    /6          |    /6         |
| MR-3       | ~95K   |    /6          |    /6         |
| **Drop**   |        | MR1-MR3 =      | MR1-MR3 =     |

## Cost Comparison
| Metric              | DunkStack | Control | Savings |
|---------------------|-----------|---------|---------|
| Total input tokens  |           |         |         |
| Total output tokens |           |         |         |
| Total cost (USD)    |           |         |   %     |
| API calls           |           |         |         |
| Avg tokens/call     |           |         |         |

## Notes
[Observations, anomalies, anything interesting]
```

---

## Integration Into the Software (Implementation Plan)

### What Already Exists
- ContextGauge tracks tokens, cost, cache, safety tiers in real-time
- Token snapshots recorded per API call (in-memory)
- WebSocket broadcasts token updates to UI
- Config.yml has safety thresholds

### What to Build

#### Phase A: Benchmark Persistence (Backend)

**1. SQLite benchmark storage** (`server/services/benchmark_database.py`)
- Table: `benchmark_runs` — id, name, model, mode (dunkstack/control), started_at, ended_at
- Table: `benchmark_checkpoints` — id, run_id, checkpoint_name (CP-1, MR-2, etc.), token_count, scores (JSON), timestamp
- Table: `benchmark_tokens` — id, run_id, snapshot of token state at each checkpoint

**2. Benchmark API endpoints** (add to `server/routers/dunkstack.py` or new `benchmark.py` router)
- `POST /api/benchmark/start` — create a new benchmark run, reset token state
- `POST /api/benchmark/checkpoint` — record a checkpoint with scores and current token state
- `POST /api/benchmark/end` — finalize the run
- `GET /api/benchmark/runs` — list all benchmark runs
- `GET /api/benchmark/runs/:id` — get full run with checkpoints
- `GET /api/benchmark/compare?run1=X&run2=Y` — side-by-side comparison

#### Phase B: Benchmark Mode (UI)

**3. Benchmark toggle in DunkStack UI**
- Button or mode switch in the DunkStack page header
- When active: shows a checkpoint progress bar (CP-1 through MR-3)
- At each checkpoint: prompts user to paste the test task, shows a scoring form (8 checkboxes for consistency, 6 for memory recall)
- Auto-captures token state when user marks a checkpoint

**4. Benchmark results panel**
- Table view of past runs
- Side-by-side comparison of DunkStack vs. control runs
- Charts: score over tokens (line chart), cost comparison (bar chart)
- Exportable as JSON/CSV

#### Phase C: Auto-Detection (Nice-to-Have)

**5. Automatic constraint checking**
- After agent builds code, scan generated files for constraint violations:
  - Grep for `new Date()` without UTC conversion (C1 violation)
  - Grep for response objects missing `request_id` (C2 violation)
  - Check table names in schema files (C4 violation)
  - Check for missing input validation (C5 violation)
- Produces an auto-score that supplements manual scoring
- This is enhancement — manual scoring comes first

#### Build Order
1. Phase A first — persistence, so results survive restarts
2. Phase B second — UI for conducting and viewing benchmarks
3. Phase C later — nice automation, not required for initial testing

**You can run the benchmarks manually before any of this is built.** The protocol above works with just the walkie-talkie, ContextGauge, and a text file to record scores. The software integration makes it repeatable and comparable.
