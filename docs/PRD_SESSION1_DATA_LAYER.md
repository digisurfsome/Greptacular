# PRD Session 1: Orchestrator Data Layer (Action History, Verification, Commit Standards, Log Compaction)

**Status:** Draft
**Date:** 2026-03-06
**Session Budget:** ~55-65K tokens (50% of 200K context window)
**Branch:** TBD (created at session start)

---

## Agent OS Context

This PRD follows the Agent OS 3-layer model. The coding agent MUST read all three layers before writing any code.

---

## STANDARDS LAYER

### Coding Conventions

- **Language:** Python 3.11+ (backend), TypeScript + React 19 (UI)
- **Python Style:** ruff, line length 120, PEP 8
- **TypeScript Style:** ESLint, strict mode
- **Key Patterns:**
  - SQLAlchemy ORM for all database models (see `api/database.py`)
  - FastAPI routers in `server/routers/` with Pydantic request/response models
  - React Query (TanStack) for all API data fetching in UI
  - Tailwind CSS v4 with neobrutalism design tokens (see `ui/src/styles/globals.css`)

### Architecture Standards

- **Architecture Type:** Monolithic Python backend + React SPA
- **Folder Structure:**
  ```
  api/database.py          — SQLAlchemy models (add new tables here)
  server/routers/          — FastAPI route handlers (one file per domain)
  server/services/         — Business logic services
  mcp_server/feature_mcp.py — MCP tools exposed to agents
  agent.py                 — Agent session loop
  progress.py              — Progress tracking + webhooks
  prompts.py               — Prompt template loading
  ui/src/components/       — React components
  ui/src/hooks/            — React Query hooks
  ui/src/lib/api.ts        — REST API client
  ui/src/lib/types.ts      — TypeScript interfaces
  ```

### Quality Standards

- **Testing:** `ruff check .` (lint), `mypy .` (type check), `cd ui && npm run build` (TS build check)
- **Security:** No secrets in code, input validation on all endpoints, SQLite parameterized queries only
- **Performance:** API responses under 300ms, batch DB writes (every 10 actions or 5 seconds)

### Technology Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite, uvicorn
- **Frontend:** React 19, TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI
- **Icons:** Lucide React for all icons

### Martin's Building Rules (MANDATORY)

These rules apply to ALL UI components created in this session and future sessions. The coding agent MUST follow every rule below without exception.

#### File Structure Rules
- One component per file
- Group related components in feature folders
- Create TypeScript interfaces for ALL data types in `types/index.ts`
- Add custom hooks for reusable logic

#### UI Component Rules (REQUIRED)
- **Modal.tsx** — Base modal with overlay, close button, title, content slots
- **ConfirmModal.tsx** — "Are you sure?" dialog for destructive actions
- **Toast.tsx** — Slide-in notification (success, error, info variants)
- **ToastContext.tsx** — Global toast state with `showToast(message, type)`
- **Skeleton.tsx** — Animated placeholder matching content shape
- **EmptyState.tsx** — Icon + message + CTA button for empty lists
- **Button.tsx** — With loading state support (spinner inside, disable on loading)
- **Avatar.tsx** — User avatar with initials fallback on image failure

#### BANNED — DO NOT USE
- `alert()` — Use Toast
- `confirm()` — Use ConfirmModal
- `prompt()` — Use a proper form Modal
- `console.log` for user feedback — Use Toast
- Text-only empty states — Use EmptyState component
- Browser default dialogs of any kind

#### Page Pattern Rules (for user data)
Every data type MUST have:
1. **List View** — Cards/rows, "Create New" button, click navigates to Detail
2. **Detail View** — Read-only display, Edit/Delete buttons, ConfirmModal on delete
3. **Create View** — Form, save navigates to Detail, cancel returns to List
4. **Edit View** — Pre-filled form, save navigates to Detail, cancel returns to Detail

#### Navigation Flow
```
LIST → (click item) → DETAIL → (click edit) → EDIT
  ↓                      ↑                       ↑
  (click new)            save                    save
  ↓                      ↑                       |
CREATE ─── save ────────►┘                       ┘
```

#### Feedback Patterns (MANDATORY)
- **On Success:** Toast + navigate to appropriate view
- **On Error:** Toast + stay on current view + keep form data
- **On Delete:** ConfirmModal → loading state on button → Toast + redirect
- **On Loading:** Skeleton cards for lists, spinner inside buttons, `disabled` during async

#### Design System
| Element | Class |
|---------|-------|
| Page Title | `text-2xl font-semibold text-text-primary` |
| Section Header | `text-lg font-semibold text-text-primary` |
| Card Title | `text-base font-medium text-text-primary` |
| Body Text | `text-sm text-text-secondary` |
| Small/Meta | `text-xs text-text-tertiary` |
| Card | `bg-surface-base rounded-card border border-border-subtle shadow-card p-6` |
| Primary Button | `bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg` |
| Input | `bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand` |

#### Responsive Design (MANDATORY)
- Mobile-first: default styles are mobile, scale up with `sm:`, `lg:`
- Sidebar hidden on mobile, hamburger toggle, slides in as overlay
- Cards: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`
- Touch targets: minimum 44x44px for all clickable elements
- Forms: full width on mobile, `lg:max-w-md` on desktop

#### Critical Rules Checklist
1. NO database calls in components — use service layer / React Query hooks only
2. NO unprotected routes for authenticated features
3. NO inline styles — Tailwind only
4. NO `any` types — define TypeScript interfaces
5. ALL database writes include `created_at` / `updated_at` timestamps
6. ALL user data scoped to authenticated user
7. ALL destructive actions require ConfirmModal
8. ALL async operations show loading state
9. ALL empty lists use EmptyState with icon + CTA
10. ALL success/error actions show Toast
11. ALL buttons show loading state during async
12. ALL dates formatted as relative time (not raw timestamps)
13. ALL long text truncated with ellipsis
14. ALL detail pages have back navigation (`ArrowLeft` icon + "Back")
15. ALL pages set document title via `usePageTitle` hook
16. ALL forms autofocus first input
17. ALL lists with > 5 expected items have search/filter
18. ALL error states have retry action
19. Use Lucide React for all icons
20. Zero console errors in production

#### Animations (MANDATORY)
- Modals: fade backdrop + scale content (`transition-all duration-200 ease-out`)
- Toasts: slide in from top-right (`transition-transform duration-300 ease-out`)
- Cards: subtle lift on hover (`hover:shadow-md hover:-translate-y-0.5 transition-all duration-200`)
- Buttons: slight scale on press (`active:scale-[0.98] transition-all duration-150`)

#### Accessibility Basics
- Focus states: `focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2`
- Escape key closes modals
- Icon buttons have `aria-label`
- Screen reader text: `<span className="sr-only">...</span>`

---

## PRODUCT LAYER

### Vision

AutoForge is an autonomous coding agent system. Agents build complete applications over multiple sessions. The orchestrator and state layers are production-ready for execution — but lack observability. Operators can't see what agents did, can't verify test results after the fact, and can't search agent activity. This session adds the data infrastructure to make agent behavior fully auditable.

### Target Users

- **AutoForge operators** — people running agents who need to understand what happened
- **Future sessions** — Session 2 builds UI on top of what this session creates

### Core Use Cases

1. Operator wants to see every tool call an agent made in a session, searchable by tool name
2. Operator wants to see historical test results for a feature, not just current pass/fail
3. Agent commit messages follow a parseable convention so `git log` is useful for progress tracking
4. Old logs don't pile up forever — automatic compaction with summary preservation

### Roadmap

- **Session 1 (this PRD):** Database models, API routes, capture hooks, compaction service
- **Session 2 (next PRD):** Approval gates, checkpoints, and all UI panels

---

## SPECS LAYER

### Feature 1: Structured Action History

#### Overview
Log every tool call made by every agent into a searchable `action_log` table. This replaces reading raw stdout for debugging.

#### Requirements
1. New SQLAlchemy model `ActionLog` in `api/database.py`
2. Fields: `id`, `session_id`, `agent_index` (int, default 0), `turn_number` (int), `tool_name` (str), `tool_input_summary` (str, max 500 chars), `result_summary` (str, max 1000 chars), `duration_ms` (int), `status` (str: "success" or "error"), `created_at` (datetime)
3. Index on `(session_id, created_at)` for fast queries
4. In `agent.py`: wrap the agent SDK's tool-use callback to emit `ActionLog` entries
5. Batch writes: accumulate up to 10 entries or 5 seconds, then flush to DB
6. New FastAPI router `server/routers/actions.py`:
   - `GET /api/projects/{name}/actions?session_id=X&tool_name=Y&status=Z&limit=50&offset=0` — paginated, filterable
   - `GET /api/projects/{name}/actions/summary` — counts grouped by tool_name, total error count, avg duration

#### Acceptance Criteria
- [ ] ActionLog model exists with all fields and index
- [ ] Agent tool calls are captured with correct truncation
- [ ] Batch writing works (no per-call DB hit)
- [ ] API returns paginated results with filters
- [ ] Summary endpoint returns correct aggregations
- [ ] `ruff check .` and `mypy .` pass

#### Technical Notes
- Use the project's existing `features.db` SQLite database
- Truncation: `tool_input_summary[:500]`, `result_summary[:1000]`
- Session ID: generate UUID at agent session start, pass through
- For parallel mode: `agent_index` differentiates concurrent agents

---

### Feature 2: Commit Message Standardization

#### Overview
Standardize agent commit messages to a parseable format. Soft validation (warn, don't block).

#### Requirements
1. Commit format: `[autoforge] <type>(<scope>): <description>`
   - Types: `feat`, `fix`, `test`, `refactor`, `chore`
   - Scope: feature ID (e.g., `#3`) or `system`
   - Examples:
     - `[autoforge] feat(#3): Add user authentication form`
     - `[autoforge] fix(#7): Fix null check in payment handler`
     - `[autoforge] chore(system): Update dependencies`
2. Add commit message format instructions to `coding_prompt.template.md` in the orientation section (STEP 0 or STEP 1), with 3 examples
3. New utility file `commit_utils.py`:
   - `parse_commit_message(msg: str) -> dict | None` — extracts type, scope, description; returns None if non-conforming
   - `extract_feature_ids(msg: str) -> list[int]` — pulls feature IDs from commit messages
   - `validate_commit_message(msg: str) -> tuple[bool, str]` — returns (valid, reason)
4. New API endpoint in an appropriate router:
   - `GET /api/projects/{name}/commits?feature_id=3&limit=20` — git log filtered by feature ID using `extract_feature_ids`

#### Acceptance Criteria
- [ ] Commit format documented in coding prompt template
- [ ] Parser correctly handles conforming and non-conforming messages
- [ ] Feature ID extraction works for single and multiple IDs
- [ ] API endpoint returns commits filtered by feature
- [ ] `ruff check .` and `mypy .` pass

#### Technical Notes
- Use regex: `r'^\[autoforge\]\s+(feat|fix|test|refactor|chore)\(([^)]+)\):\s+(.+)$'`
- `extract_feature_ids`: scan for `#\d+` patterns
- Git log: shell out to `git log --oneline --format="%H %s"` in project dir
- Soft validation only — log warnings for non-conforming, never block

---

### Feature 3: Verification Result Persistence

#### Overview
Persist test results (pass/fail, output) so operators can see historical verification for any feature.

#### Requirements
1. New SQLAlchemy model `VerificationResult` in `api/database.py`
2. Fields: `id`, `feature_id` (int, FK to features), `session_id` (str), `agent_index` (int, default 0), `test_type` (str: "lint", "typecheck", "e2e", "manual"), `passed` (bool), `output` (text, max 10KB), `duration_ms` (int), `created_at` (datetime)
3. Index on `(feature_id, created_at)`
4. Extend MCP tools `feature_mark_passing` and `feature_mark_failing` in `mcp_server/feature_mcp.py`:
   - Add optional parameter `verification_output` (str)
   - Add optional parameter `test_type` (str, default "manual")
   - When provided, create a `VerificationResult` record alongside the status change
5. New FastAPI router `server/routers/verifications.py`:
   - `GET /api/projects/{name}/features/{id}/verifications?limit=20` — history for one feature
   - `GET /api/projects/{name}/verifications?passed=false&limit=50` — all failures across features

#### Acceptance Criteria
- [ ] VerificationResult model exists with all fields and index
- [ ] MCP mark_passing/mark_failing accept and store verification output
- [ ] API returns verification history per feature
- [ ] API returns cross-feature failure list
- [ ] Output truncated to 10KB on write
- [ ] `ruff check .` and `mypy .` pass

#### Technical Notes
- Same `features.db` database
- Backward compatible: `verification_output` is optional, existing callers unaffected
- Truncation: `output[:10240]`

---

### Feature 4: Log Compaction

#### Overview
Auto-cleanup old action logs and verification results. Preserve aggregated summaries before deleting.

#### Requirements
1. Retention defaults: 30 days for `action_log` and `verification_results`, 7 days for `orchestrator_debug.log`
2. Configurable in `~/.autoforge/config.yaml` under a `retention:` key:
   ```yaml
   retention:
     action_log_days: 30
     verification_log_days: 30
     debug_log_days: 7
   ```
3. New SQLAlchemy model `ActionLogSummary` in `api/database.py`:
   - Fields: `id`, `date` (str, YYYY-MM-DD), `session_id` (str), `tool_name` (str), `call_count` (int), `error_count` (int), `avg_duration_ms` (int)
   - Unique constraint on `(date, session_id, tool_name)`
4. New service `server/services/log_compaction.py`:
   - `compact_action_logs(db_path, retention_days)` — aggregate old rows into `ActionLogSummary`, then delete
   - `compact_verification_logs(db_path, retention_days)` — delete old rows (no summary needed, feature-level data is sufficient)
   - `rotate_debug_log(log_path, retention_days)` — rename to `.1`, `.2`, keep 3 rotations, delete older
   - `run_compaction(project_dir)` — orchestrates all three
5. Hook into server startup: run compaction for all registered projects
6. Schedule daily via APScheduler (already used in `server/services/scheduler_service.py`)

#### Acceptance Criteria
- [ ] ActionLogSummary model exists with unique constraint
- [ ] Compaction correctly aggregates before deleting
- [ ] Debug log rotation keeps 3 files max
- [ ] Retention config loaded from `~/.autoforge/config.yaml`
- [ ] Compaction runs on server startup
- [ ] Daily schedule registered in APScheduler
- [ ] `ruff check .` and `mypy .` pass

#### Technical Notes
- Use `DELETE FROM action_log WHERE created_at < datetime('now', '-30 days')` after aggregation
- Aggregation query: `SELECT date(created_at), session_id, tool_name, COUNT(*), SUM(CASE WHEN status='error' THEN 1 ELSE 0 END), AVG(duration_ms) FROM action_log WHERE created_at < ? GROUP BY 1,2,3`
- For debug log rotation: use Python's `pathlib` to rename files

---

## Database Schema (All New Tables)

```sql
-- Feature 1: Action History
CREATE TABLE action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_index INTEGER DEFAULT 0,
    turn_number INTEGER,
    tool_name TEXT NOT NULL,
    tool_input_summary TEXT,
    result_summary TEXT,
    duration_ms INTEGER,
    status TEXT NOT NULL DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_action_log_session ON action_log(session_id, created_at);

-- Feature 3: Verification Results
CREATE TABLE verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL REFERENCES features(id),
    session_id TEXT,
    agent_index INTEGER DEFAULT 0,
    test_type TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    output TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_verification_feature ON verification_results(feature_id, created_at);

-- Feature 4: Log Compaction Summaries
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

## Session Plan (Execution Order)

1. **Database models** — Add `ActionLog`, `VerificationResult`, `ActionLogSummary` to `api/database.py`
2. **Commit utils** — Create `commit_utils.py` with parser, extractor, validator
3. **Agent hook** — Wire action logging into `agent.py` tool callback with batch writes
4. **MCP extensions** — Add `verification_output` and `test_type` params to mark_passing/mark_failing
5. **API routers** — Create `actions.py`, `verifications.py` routers; add commits endpoint
6. **Log compaction service** — Create `log_compaction.py`, wire to startup + scheduler
7. **Prompt update** — Add commit message format to `coding_prompt.template.md`
8. **Validation** — `ruff check .`, `mypy .`, `cd ui && npm run build`

---

## Success Criteria

- [ ] Every agent tool call logged to `action_log` with truncated input/output
- [ ] API can filter action logs by session, tool name, status
- [ ] Agent commit messages follow `[autoforge] type(scope): description` format
- [ ] Commit parser extracts feature IDs correctly
- [ ] MCP mark_passing/mark_failing persist verification output
- [ ] Verification history queryable per feature and cross-feature
- [ ] Old logs compacted after retention period with summaries preserved
- [ ] All lint/type checks pass
- [ ] No UI work in this session (that's Session 2)

---

## Out of Scope (Deferred to Session 2)

- UI panels for action log, verification history, commits
- Approval gates (human-in-the-loop)
- Checkpoints with rollback
- Settings UI for retention config
