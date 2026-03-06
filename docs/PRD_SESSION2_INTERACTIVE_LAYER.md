# PRD Session 2: Interactive Layer (Approval Gates, Checkpoints, All UI Panels)

**Status:** Draft
**Date:** 2026-03-06
**Session Budget:** ~50-60K tokens (50% of 200K context window)
**Branch:** TBD (created at session start)
**Depends on:** Session 1 (PRD_SESSION1_DATA_LAYER.md) must be completed first

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
  api/database.py          — SQLAlchemy models (Session 1 added ActionLog, VerificationResult, ActionLogSummary)
  server/routers/          — FastAPI route handlers (Session 1 added actions.py, verifications.py)
  server/services/         — Business logic services (Session 1 added log_compaction.py)
  security.py              — Bash command validation + allowlist hierarchy
  mcp_server/feature_mcp.py — MCP tools (Session 1 extended mark_passing/mark_failing)
  commit_utils.py          — Commit message parsing (added in Session 1)
  ui/src/components/       — React components (this session adds new panels)
  ui/src/hooks/            — React Query hooks (this session adds new hooks)
  ui/src/lib/api.ts        — REST API client (this session adds new endpoints)
  ui/src/lib/types.ts      — TypeScript interfaces (this session adds new types)
  ```

### Quality Standards

- **Testing:** `ruff check .` (lint), `mypy .` (type check), `cd ui && npm run build` (TS build check)
- **Security:** No secrets in code, input validation on all endpoints, approval decisions audited
- **Performance:** API responses under 300ms, WebSocket for real-time approval notifications

### Technology Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, SQLite, uvicorn, APScheduler
- **Frontend:** React 19, TypeScript, Vite 7, TanStack Query, Tailwind CSS v4, Radix UI, Lucide React
- **Real-time:** WebSocket (existing pattern in `useWebSocket.ts`)

### Martin's Building Rules (MANDATORY)

These rules apply to ALL UI components created in this session. The coding agent MUST follow every rule below without exception.

#### File Structure Rules
- One component per file
- Group related components in feature folders
- Create TypeScript interfaces for ALL data types in `types/index.ts`
- Add custom hooks for reusable logic

#### UI Component Rules (REQUIRED — Use Existing or Create)
- **Modal.tsx** — Base modal with overlay, close button, title, content slots
- **ConfirmModal.tsx** — "Are you sure?" dialog for destructive actions
- **Toast.tsx** — Slide-in notification (success, error, info variants)
- **ToastContext.tsx** — Global toast state with `showToast(message, type)`
- **Skeleton.tsx** — Animated placeholder matching content shape
- **EmptyState.tsx** — Icon + message + CTA button for empty lists
- **Button.tsx** — With loading state support (spinner inside, disable on loading)
- **Avatar.tsx** — User avatar with initials fallback on image failure

Check if these already exist in `ui/src/components/ui/` before creating. Use existing versions. Only create if missing.

#### BANNED — DO NOT USE
- `alert()` — Use Toast
- `confirm()` — Use ConfirmModal
- `prompt()` — Use a proper form Modal
- `console.log` for user feedback — Use Toast
- Text-only empty states — Use EmptyState component
- Browser default dialogs of any kind
- Inline styles — Tailwind only
- `any` types — define TypeScript interfaces

#### Page Pattern Rules (for user data)
Every data type MUST have:
1. **List View** — Cards/rows, click navigates to Detail
2. **Detail View** — Read-only display, action buttons
3. **Create View** — Form with save/cancel (where applicable)
4. **Edit View** — Pre-filled form (where applicable)

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
| Danger Button | `bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-3 rounded-lg` |
| Secondary Button | `bg-surface-muted hover:bg-border-subtle text-text-primary font-medium px-6 py-3 rounded-lg` |
| Input | `bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand` |

#### Layout Structure
```
┌─────────────────────────────────────────────────┐
│ HEADER: Logo          User Avatar | Sign Out    │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│   SIDEBAR    │         MAIN CONTENT             │
│   (240px)    │         (scrollable)             │
│              │                                  │
│   - Nav      │         Cards, forms,            │
│   - [Items]  │         data display             │
│   - Help     │                                  │
└──────────────┴──────────────────────────────────┘
```

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
6. ALL destructive actions require ConfirmModal
7. ALL async operations show loading state
8. ALL empty lists use EmptyState with icon + CTA
9. ALL success/error actions show Toast
10. ALL buttons show loading state during async
11. ALL dates formatted as relative time (not raw timestamps)
12. ALL long text truncated with ellipsis
13. ALL detail pages have back navigation (`ArrowLeft` icon + "Back")
14. ALL pages set document title via `usePageTitle` hook
15. ALL forms autofocus first input
16. ALL lists with > 5 expected items have search/filter
17. ALL error states have retry action
18. Use Lucide React for all icons
19. Zero console errors in production

#### Animations (MANDATORY)
- Modals: fade backdrop + scale content (`transition-all duration-200 ease-out`)
- Toasts: slide in from top-right (`transition-transform duration-300 ease-out`)
- Cards: subtle lift on hover (`hover:shadow-md hover:-translate-y-0.5 transition-all duration-200`)
- Buttons: slight scale on press (`active:scale-[0.98] transition-all duration-150`)
- Sidebar on mobile: slide in (`transition-transform duration-300`)

#### Accessibility Basics
- Focus states: `focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2`
- Escape key closes modals
- Icon buttons have `aria-label`
- Screen reader text: `<span className="sr-only">...</span>`
- Keyboard navigation support for approval actions

#### Dark Mode
- Use CSS variables for BOTH modes (not hardcoded hex)
- Light mode in `:root`, dark mode in `.dark`
- Reference via `var(--color-*)` in Tailwind config
- ThemeToggle component in header

#### Loading Button Pattern
```tsx
<button disabled={loading} className="flex items-center gap-2 ...">
  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
  {loading ? 'Loading...' : children}
</button>
```

#### Date Formatting
```ts
// Never show raw timestamps
"Just now" | "5m ago" | "2h ago" | "Yesterday" | "3d ago" | "Jan 15"
```

#### Error Boundary
Wrap app in ErrorBoundary. Show "Something went wrong" + Refresh button on crash.

#### Search/Filter for Lists
```tsx
const filteredItems = items.filter(item =>
  item.title.toLowerCase().includes(searchQuery.toLowerCase())
);
```

With search input using `Search` icon from Lucide and "No results" feedback.

#### Unsaved Changes Warning
```ts
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (hasChanges) { e.preventDefault(); e.returnValue = ''; }
  };
  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, [hasChanges]);
```

#### 404 Handling
- Route-level: `<Route path="*" element={<NotFoundPage />} />`
- Data-level: EmptyState with "Item not found" + "Back to Dashboard" CTA

#### Hover States (MANDATORY)
- Cards: `hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer`
- Buttons: `hover:bg-brand-dark transition-colors`
- Links: `hover:text-brand hover:underline`
- Icon buttons: `hover:bg-surface-muted rounded-lg p-2 transition-colors`
- Table rows: `hover:bg-surface-muted transition-colors`
- Sidebar items: `hover:bg-surface-muted rounded-lg transition-colors`

---

## PRODUCT LAYER

### Vision

Session 1 built the data layer (action logs, verification results, commit parsing, log compaction). This session adds the interactive surfaces: operators can approve dangerous commands in real-time, create/rollback checkpoints, and see all the Session 1 data through polished UI panels.

### Target Users

- **AutoForge operators** — people running agents who need real-time control and historical visibility

### Core Use Cases

1. Operator sees a real-time notification when an agent wants to run `kubectl` — approves or denies from the UI
2. Operator browses the action log for a session to understand what an agent did and where it spent time
3. Operator views verification history for a feature to see when it started passing and what the test output was
4. Operator views a checkpoint timeline and can rollback to a known-good state
5. Operator configures log retention settings from the Settings modal
6. Operator searches commits filtered by feature ID to track what changed for a specific feature

### Roadmap

- **Session 1 (completed):** Database models, API routes, capture hooks, compaction service
- **Session 2 (this PRD):** Approval gates, checkpoints, all UI panels, settings

---

## SPECS LAYER

### Feature 1: Approval Gates (Human-in-the-Loop)

#### Overview
When an agent attempts a command from `DANGEROUS_COMMANDS` (sudo, kubectl, aws, gcloud, az), pause execution and ask the operator for approval via the UI.

#### Requirements

**Backend:**

1. New SQLAlchemy model `ApprovalRequest` in `api/database.py`
   - Fields: `id`, `agent_id` (str), `project_name` (str), `command` (str), `reason` (str, optional), `status` (str: "pending" | "approved" | "denied" | "expired"), `requested_at` (datetime), `resolved_at` (datetime, nullable), `resolved_by` (str, nullable)
   - Default status: "pending"

2. TTL: requests expire after 5 minutes if unresolved. Check on read, update status to "expired".

3. New FastAPI router `server/routers/approvals.py`:
   - `POST /api/approvals` — agent requests approval (body: `agent_id`, `project_name`, `command`, `reason`)
   - `GET /api/approvals?status=pending&project_name=X` — list pending requests
   - `GET /api/approvals?status=all&project_name=X&limit=50` — full audit trail
   - `PUT /api/approvals/{id}` — approve or deny (body: `status`, `resolved_by`)

4. WebSocket integration: push `approval_request` event to UI when new request created (use existing WebSocket pattern in `server/routers/agent.py`)

5. Security hook integration in `security.py`:
   - When command matches `DANGEROUS_COMMANDS` and approval flow is enabled:
     - Create `ApprovalRequest` record
     - Push WebSocket notification
     - Return blocking response to agent: "Command requires operator approval. Waiting..."
     - Poll for resolution (check every 2 seconds, timeout at 5 minutes)
     - On approval: allow command execution (one-shot, not blanket)
     - On denial/expiry: return "Command denied by operator" to agent

6. Feature toggle: `APPROVAL_GATES_ENABLED` in settings (default: false). When disabled, dangerous commands stay hard-blocked as today.

**Frontend:**

7. New component `ui/src/components/ApprovalBanner.tsx`:
   - Fixed banner at top of `AgentMissionControl.tsx` when pending approvals exist
   - Shows: command (truncated), requesting agent, time ago
   - Two buttons: "Approve" (green) and "Deny" (red)
   - Approve/Deny buttons show loading state during API call
   - Toast on success ("Command approved" / "Command denied")
   - Auto-dismiss banner when resolved

8. New component `ui/src/components/ApprovalHistory.tsx`:
   - Table in project detail view showing all past approval decisions
   - Columns: Command, Agent, Status (badge), Requested, Resolved, Resolved By
   - Status badges: pending=yellow, approved=green, denied=red, expired=gray
   - Search/filter by status
   - EmptyState when no approvals

9. Audio notification (optional): play a chime sound when approval request arrives. Toggle in settings.

10. React Query hook `useApprovals(projectName)` with 2-second polling for pending requests

#### Acceptance Criteria
- [ ] ApprovalRequest model exists with all fields
- [ ] API endpoints work for create, list, update
- [ ] WebSocket pushes approval_request event
- [ ] Security hook pauses agent on dangerous command, resumes on approval
- [ ] Denial returns clear message to agent
- [ ] Expiry after 5 minutes works
- [ ] Banner appears in UI with approve/deny buttons
- [ ] History table shows all decisions
- [ ] Feature toggle works (disabled = hard-block as before)
- [ ] Toast feedback on approve/deny
- [ ] Loading states on buttons
- [ ] `ruff check .`, `mypy .`, `npm run build` all pass

#### Technical Notes
- Polling in security hook: use `time.sleep(2)` in a loop with 150 iterations (5 min)
- One-shot approval: the `ApprovalRequest` record is consumed once. Same command requires new approval.
- Don't modify `BLOCKED_COMMANDS` — those stay hard-blocked always. Only `DANGEROUS_COMMANDS` get the approval flow.

---

### Feature 2: Artifact Checkpoints

#### Overview
Snapshot git SHA + feature status at key moments. Support rollback to a checkpoint.

#### Requirements

**Backend:**

1. New SQLAlchemy model `Checkpoint` in `api/database.py`
   - Fields: `id`, `session_id` (str, nullable), `label` (str), `git_sha` (str), `feature_snapshot` (text — JSON blob of all feature statuses), `created_at` (datetime)

2. Automatic checkpoint creation:
   - When `feature_mark_passing` is called in MCP server → create checkpoint labeled `feature-{id}-complete`
   - When factory controller transitions phases → create checkpoint labeled `phase-{n}-complete`
   - When agent session ends → create checkpoint labeled `session-end-{session_id}`

3. MCP tool `checkpoint_create(label: str)` — agents can create manual checkpoints

4. New FastAPI router `server/routers/checkpoints.py`:
   - `GET /api/projects/{name}/checkpoints?limit=50` — list checkpoints (newest first)
   - `POST /api/projects/{name}/checkpoints` — create manual checkpoint (body: `label`)
   - `GET /api/projects/{name}/checkpoints/{id}` — detail with full feature snapshot
   - `POST /api/projects/{name}/checkpoints/{id}/rollback` — rollback:
     - Creates new git branch `rollback-{checkpoint_id}` at the checkpoint's SHA
     - Resets feature statuses in DB to match `feature_snapshot`
     - Returns preview of changes (features that will change status)
     - Requires `confirm=true` query param to actually execute

5. Helper function `create_checkpoint(project_dir, label, session_id=None)`:
   - Gets current `git rev-parse HEAD`
   - Queries all features → serialize to JSON
   - Inserts `Checkpoint` record

**Frontend:**

6. New component `ui/src/components/CheckpointTimeline.tsx`:
   - Vertical timeline in project detail view
   - Each entry: label, short SHA (linked), feature counts (passing/total), relative timestamp
   - "Rollback" button on each checkpoint
   - Click "Rollback" → ConfirmModal showing what will change (features that flip status)
   - On confirm → API call → Toast on success → refresh feature list

7. New component `ui/src/components/CheckpointDetail.tsx`:
   - Expanded view showing full feature snapshot
   - Table: Feature ID, Name, Status at checkpoint vs current status
   - Highlight differences

8. React Query hook `useCheckpoints(projectName)` with standard caching

#### Acceptance Criteria
- [ ] Checkpoint model exists with all fields
- [ ] Auto-checkpoints created on feature completion, phase transition, session end
- [ ] MCP tool available for manual checkpoints
- [ ] API endpoints for list, create, detail, rollback
- [ ] Rollback creates branch + resets feature statuses
- [ ] Rollback requires confirmation
- [ ] Timeline UI shows checkpoints with relative timestamps
- [ ] Rollback flow: button → ConfirmModal → loading → Toast
- [ ] EmptyState when no checkpoints
- [ ] `ruff check .`, `mypy .`, `npm run build` all pass

#### Technical Notes
- `git rev-parse HEAD` to get SHA
- `git checkout -b rollback-{id} {sha}` for rollback branch
- Feature snapshot: `json.dumps([{"id": f.id, "name": f.name, "passes": f.passes, "in_progress": f.in_progress} for f in features])`
- Rollback preview: compare snapshot to current state, return list of changes

---

### Feature 3: Action Log UI Panel

#### Overview
UI to browse the action log data created by Session 1.

#### Requirements

1. New component `ui/src/components/ActionLogPanel.tsx`:
   - Tab/panel in project detail view
   - Table columns: Timestamp (relative), Tool Name, Input Preview (truncated), Status (badge), Duration
   - Status badges: success=green, error=red
   - Click row to expand full input/output in a slide-out or accordion
   - Filters: session dropdown, tool name dropdown, status toggle
   - Search by tool name or input content
   - Pagination (20 per page)
   - EmptyState: "No actions recorded yet" with explanation

2. New component `ui/src/components/ActionLogSummary.tsx`:
   - Summary card at top: total calls, error rate %, avg duration, most-used tool
   - Pulled from `/api/projects/{name}/actions/summary`

3. React Query hooks:
   - `useActionLog(projectName, filters)` — paginated action log
   - `useActionLogSummary(projectName)` — summary stats

4. TypeScript types in `types/index.ts`:
   ```ts
   interface ActionLogEntry {
     id: number;
     session_id: string;
     agent_index: number;
     turn_number: number | null;
     tool_name: string;
     tool_input_summary: string | null;
     result_summary: string | null;
     duration_ms: number | null;
     status: 'success' | 'error';
     created_at: string;
   }

   interface ActionLogSummary {
     total_calls: number;
     error_count: number;
     error_rate: number;
     avg_duration_ms: number;
     tools: { tool_name: string; count: number; error_count: number; avg_duration_ms: number }[];
   }
   ```

5. Add API functions to `ui/src/lib/api.ts`

#### Acceptance Criteria
- [ ] Table renders action log entries with all columns
- [ ] Filters work: session, tool name, status
- [ ] Pagination works
- [ ] Row expansion shows full input/output
- [ ] Summary card shows correct stats
- [ ] EmptyState when no data
- [ ] Loading skeletons during fetch
- [ ] Relative timestamps
- [ ] Search functionality
- [ ] `npm run build` passes

---

### Feature 4: Verification History UI Panel

#### Overview
UI to browse verification results created by Session 1.

#### Requirements

1. New component `ui/src/components/VerificationHistory.tsx`:
   - Section in feature detail panel
   - List of verification runs: test type (badge), pass/fail (badge), timestamp, duration
   - Click to expand output (code block, scrollable, max-height)
   - EmptyState: "No verification results yet"

2. New component `ui/src/components/FailuresList.tsx`:
   - Cross-feature view: all recent failures
   - Table: Feature Name, Test Type, Timestamp, link to feature detail
   - Filter by test type
   - EmptyState: "All clear — no recent failures" (with check icon)

3. React Query hooks:
   - `useVerificationHistory(projectName, featureId)` — per-feature
   - `useRecentFailures(projectName)` — cross-feature failures

4. TypeScript types in `types/index.ts`:
   ```ts
   interface VerificationResult {
     id: number;
     feature_id: number;
     session_id: string | null;
     agent_index: number;
     test_type: 'lint' | 'typecheck' | 'e2e' | 'manual';
     passed: boolean;
     output: string | null;
     duration_ms: number | null;
     created_at: string;
   }
   ```

5. Add API functions to `ui/src/lib/api.ts`

#### Acceptance Criteria
- [ ] Per-feature verification list renders correctly
- [ ] Pass/fail badges with correct colors
- [ ] Output expandable in code block
- [ ] Cross-feature failures list works
- [ ] Filter by test type
- [ ] EmptyState for both components
- [ ] Relative timestamps
- [ ] `npm run build` passes

---

### Feature 5: Commits Panel

#### Overview
UI to view agent commits filtered by feature.

#### Requirements

1. New component `ui/src/components/CommitsPanel.tsx`:
   - In project detail view
   - List of commits: SHA (short), message, relative timestamp
   - Commit messages parsed: type badge (feat/fix/test/refactor/chore), scope, description
   - Non-conforming messages shown without badge (no error, just no badge)
   - Filter by feature ID dropdown
   - EmptyState: "No commits yet"

2. React Query hook: `useCommits(projectName, featureId?)`

3. TypeScript types:
   ```ts
   interface Commit {
     sha: string;
     message: string;
     timestamp: string;
     parsed: {
       type: string;
       scope: string;
       description: string;
     } | null;  // null if non-conforming
   }
   ```

4. Add API function to `ui/src/lib/api.ts`

#### Acceptance Criteria
- [ ] Commits list renders with parsed badges
- [ ] Feature filter works
- [ ] Non-conforming messages handled gracefully
- [ ] Relative timestamps
- [ ] EmptyState when no commits
- [ ] `npm run build` passes

---

### Feature 6: Settings Extensions

#### Overview
Add retention config and approval gate toggle to existing Settings modal.

#### Requirements

1. In existing `SettingsModal.tsx`, add new section "Data & Logs":
   - Toggle: "Enable approval gates for dangerous commands" (default: off)
   - Number input: "Action log retention (days)" (default: 30, min: 1, max: 365)
   - Number input: "Verification log retention (days)" (default: 30, min: 1, max: 365)
   - Number input: "Debug log retention (days)" (default: 7, min: 1, max: 90)
   - Toggle: "Audio notification for approval requests" (default: off)

2. Backend: extend settings model in `server/routers/settings.py` and `registry.py` to include new fields

3. Settings persisted to `~/.autoforge/config.yaml`

#### Acceptance Criteria
- [ ] New section visible in Settings modal
- [ ] All inputs work with proper validation (min/max)
- [ ] Settings persist across server restarts
- [ ] Approval gate toggle controls whether approval flow is active
- [ ] `ruff check .`, `mypy .`, `npm run build` all pass

---

## New Database Tables (This Session)

```sql
-- Feature 1: Approval Gates
CREATE TABLE approval_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    command TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by TEXT
);
CREATE INDEX idx_approval_status ON approval_requests(project_name, status);

-- Feature 2: Checkpoints
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    label TEXT NOT NULL,
    git_sha TEXT NOT NULL,
    feature_snapshot TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_checkpoint_project ON checkpoints(created_at DESC);
```

---

## Session Plan (Execution Order)

1. **Read Session 1 output** — Verify `ActionLog`, `VerificationResult`, `ActionLogSummary` models exist, routers work
2. **Database models** — Add `ApprovalRequest`, `Checkpoint` to `api/database.py`
3. **Approval backend** — Router, security hook integration, WebSocket event, polling loop
4. **Checkpoint backend** — Router, auto-checkpoint hooks, MCP tool, rollback logic
5. **Settings extensions** — Add new fields to settings model and config
6. **TypeScript types** — Add all new interfaces to `types/index.ts`
7. **API client** — Add all new endpoint functions to `api.ts`
8. **React Query hooks** — Create hooks for approvals, checkpoints, action log, verifications, commits
9. **UI panels** — Build all components:
   - ApprovalBanner + ApprovalHistory
   - CheckpointTimeline + CheckpointDetail
   - ActionLogPanel + ActionLogSummary
   - VerificationHistory + FailuresList
   - CommitsPanel
   - Settings extensions
10. **Wire into app** — Add panels to project detail view, banner to mission control
11. **Validation** — `ruff check .`, `mypy .`, `cd ui && npm run build`

---

## Success Criteria

- [ ] Operator can approve/deny dangerous commands from UI with real-time notification
- [ ] Approval history shows full audit trail with status badges
- [ ] Checkpoint timeline shows all auto/manual checkpoints
- [ ] Rollback creates branch + resets features with confirmation flow
- [ ] Action log table is searchable, filterable, paginated with summary stats
- [ ] Verification history shows per-feature test results with expandable output
- [ ] Failures list shows cross-feature view of recent failures
- [ ] Commits panel shows parsed messages with feature filter
- [ ] Settings modal has retention config and approval gate toggle
- [ ] All Martin's building rules followed: Toasts, ConfirmModals, EmptyStates, Skeletons, loading buttons, relative dates, truncation, back navigation, search/filter, hover states, animations, accessibility
- [ ] All lint/type checks pass
- [ ] Zero console errors
- [ ] Responsive: works on mobile and desktop

---

## Out of Scope

- Multi-user approval workflows
- Real-time streaming of action logs (polling is fine)
- Screenshot capture from Playwright
- Cross-project queries
- Approval chain (single approve/deny is sufficient)
