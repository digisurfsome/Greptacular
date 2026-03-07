# PRD: Plans Library — Auto-Captured, Searchable Plan Storage

## Problem

Every time an AI agent creates a PRD, handoff doc, or implementation plan, it gets buried in a GitHub file somewhere in the repo. The user never sees it again. Weeks of planning work gets lost because:

1. PRDs end up as random `.md` files scattered across repos
2. There's no central place to find them
3. No search, no sorting, no tags
4. The user forgets they exist — humans can't track dozens of plans across dozens of projects
5. The AI's default behavior (save as .md in repo) actively works against discoverability

## Solution: Plans Library

A first-class feature in AutoForge that **automatically captures and stores every PRD/plan** in a searchable, sortable library accessible from the UI.

### Core Principle: Deterministic Auto-Capture

If a document is named "PRD" or tagged as a plan/handoff, it **automatically** goes into the library. No manual step. No asking the user. No option to skip. The system intercepts it and stores it. This is not optional behavior — it's an automation that runs regardless of what the agent tries to do.

---

## User Experience

### Accessing the Library

- **Button in the main AutoForge header** — dropdown/panel that slides in
- **Keyboard shortcut** (e.g., `P` for plans)
- **Dedicated route** (`/#/plans`) for full-page view

### What You See

- **List of all plans** — card layout or table view, switchable
- Each card shows:
  - Plan title
  - Tags (auto-generated + user-added)
  - Date created
  - Project it belongs to (or "global")
  - Status: Draft / Ready / In Progress / Done / Archived
  - Preview snippet (first 2-3 lines)
- **Search bar** — full-text search across all plan content
- **Sort by**: Date (newest first default), name, project, status, tag
- **Filter by**: Project, tag, status, date range (last 24h, last week, last month, all)
- **Bulk actions**: Archive, tag, delete

### Plan Detail View

- Full rendered markdown content
- Edit capability (inline markdown editor)
- Metadata sidebar: tags, project, dates, status
- "Queue in Builder" button — sends plan to the build queue
- Version history (if plan was updated)

---

## Auto-Capture System (Deterministic)

### How It Works

1. **Keyword Detection**: Any file created by an agent containing "PRD" in the filename or `# PRD` in the first 5 lines gets auto-captured
2. **Explicit Tagging**: Agents can call a library API to store plans directly
3. **Hook-Based Interception**: A post-write hook checks every `.md` file created by agents. If it matches plan patterns, it's copied to the library database
4. **Chat Detection**: If an agent outputs a structured plan in conversation (detected by headings like "## Problem", "## Solution", "## Implementation"), offer one-click save to library

### Detection Patterns (auto-tag triggers)

| Pattern | Tag Applied |
|---------|-------------|
| Filename contains `PRD` or `prd` | `prd` |
| Filename contains `handoff` | `handoff` |
| Filename contains `plan` or `implementation-plan` | `plan` |
| Content has `## Problem` + `## Solution` | `prd` |
| Content has `## Handoff` or `## Context for Next Agent` | `handoff` |
| Agent explicitly calls `save_to_library()` | Whatever tag the agent specifies |

### Auto-Generated Metadata

- **Title**: Extracted from first `#` heading
- **Project**: Detected from which project directory the file was created in
- **Tags**: From detection patterns above + AI-generated topic tags (e.g., "auth", "UI", "database")
- **Created date**: Timestamp of creation
- **Source**: File path where the original was saved (for reference)

---

## Data Storage

### Database: Supabase (or SQLite for local-first)

**Table: `plans`**

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| title | text | Plan title (from first heading) |
| content | text | Full markdown content |
| project_name | text | Associated project (nullable for global plans) |
| status | enum | draft / ready / in_progress / done / archived |
| tags | text[] | Array of tags |
| source_path | text | Original file path where agent saved it |
| created_at | timestamp | When captured |
| updated_at | timestamp | Last modified |
| created_by | text | Agent name or "user" |
| search_vector | tsvector | Full-text search index |

**Table: `plan_versions`** (optional, for version history)

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| plan_id | uuid | FK to plans |
| content | text | Content at this version |
| changed_at | timestamp | When this version was saved |

---

## API Endpoints

```
GET    /api/plans                    — List all plans (with search/filter/sort params)
GET    /api/plans/:id                — Get single plan
POST   /api/plans                    — Create plan (used by auto-capture + manual)
PUT    /api/plans/:id                — Update plan
DELETE /api/plans/:id                — Delete plan
POST   /api/plans/:id/archive        — Archive plan
POST   /api/plans/:id/queue          — Send to build queue
GET    /api/plans/tags               — List all tags (for filter dropdown)
GET    /api/plans/search?q=          — Full-text search
```

---

## MCP Server Integration

Add tools to the existing MCP server so agents can interact with the library:

```
plan_save(title, content, tags[], project?)     — Save a plan to library
plan_list(project?, status?, tag?)              — List plans
plan_get(id)                                     — Get a plan by ID
plan_update(id, content?, status?, tags?)        — Update a plan
```

This means any agent session can:
1. Save plans it creates
2. Look up existing plans for context
3. Update plan status as features get built

---

## Hook-Based Auto-Capture (The Deterministic Part)

### Implementation

In `client.py` (or a new `plan_capture.py`), add a post-tool hook that runs after every file write:

```python
def check_for_plan(file_path: str, content: str) -> bool:
    """Check if a written file is a PRD/plan and auto-capture it."""
    filename = os.path.basename(file_path).lower()

    # Filename-based detection
    plan_keywords = ['prd', 'handoff', 'plan', 'implementation-plan', 'spec']
    if any(kw in filename for kw in plan_keywords):
        return True

    # Content-based detection
    if '## Problem' in content and '## Solution' in content:
        return True
    if '## Handoff' in content or '## Context for Next Agent' in content:
        return True

    return False
```

This runs **every time** an agent writes a `.md` file. If it matches, the plan is automatically inserted into the `plans` table. The agent doesn't have to do anything. The user doesn't have to do anything. It just happens.

---

## UI Components

### PlansLibrary (dropdown panel)
- Triggered by header button or `P` key
- Slides in from right side (like the existing Assistant panel)
- Shows search bar + scrollable list of plan cards
- Quick filters at top: All / PRDs / Handoffs / Plans

### PlansPage (full page, `/#/plans`)
- Full-screen view with sidebar filters
- Table or card view toggle
- Advanced search with date range picker
- Bulk operations toolbar

### PlanCard (individual plan)
- Title + tags as colored pills
- Date + project badge
- Status indicator
- Click to expand/view
- Quick actions: Archive, Edit Tags, Queue

---

## Migration Path

### Phase 1: Database + API + Auto-Capture Hook
- Create plans table (SQLite first, Supabase later)
- Build REST API endpoints
- Add post-write hook for auto-capture
- Basic plans list page

### Phase 2: UI Polish + Search
- Full PlansLibrary panel with search
- Tag management
- Sort and filter
- Plan detail view with editor

### Phase 3: Agent Integration
- MCP tools for plan CRUD
- Agents auto-save plans via MCP (belt AND suspenders with the hook)
- "Queue in Builder" integration
- Cross-project plan discovery

### Phase 4: Supabase Migration (when ready)
- Move from SQLite to Supabase for cloud sync
- Multi-device access
- Shared team libraries
- Real-time sync across sessions

---

## Success Criteria

1. **Zero-effort capture**: User never has to manually save a PRD to the library
2. **Findable in 5 seconds**: Search + sort gets you to any plan fast
3. **Nothing lost**: Every PRD/handoff/plan created in any session is in the library
4. **Actionable**: Plans can be sent to the build queue with one click
5. **Cross-project**: Library spans all projects, searchable globally
