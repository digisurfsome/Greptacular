# PRD: Projects + Library Merge

## Overview

Merge the existing "Categories" (conversation grouping) and "Library" (file management) systems into a unified **Projects** concept. Two project types: **Projects** (general-purpose) and **App Projects** (software builds). Files live inside projects with tags for organization and cross-project sharing. The Library panel comes to the Dashboard.

---

## 1. Database Schema Changes

### 1a. Rename `workspace_categories` → `workspace_projects`

**Current** `workspace_categories`:
- id, name, color, sort_order, created_at, updated_at

**New** `workspace_projects`:
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | existing |
| name | String(255) | existing |
| color | String(20) | existing |
| sort_order | Integer | existing |
| **project_type** | String(20) | NEW: `'general'` or `'app'` (default: `'general'`) |
| **description** | Text | NEW: optional project description |
| **icon** | String(50) | NEW: optional emoji or icon name |
| **working_directory** | String(500) | NEW: default repo path for app projects |
| created_at | DateTime | existing |
| updated_at | DateTime | existing |

**Migration**: Rename table, add new columns with defaults. All existing categories become `project_type='general'`.

### 1b. Update `workspace_conversations`

**Current**: `category` column (String, stores category name as text)

**Change**: Keep `category` column but rename to `project_name` (or add a `project_id` FK). Since the current system uses the category name string directly, we'll add a proper `project_id` FK column and migrate existing data:

| Column | Type | Notes |
|--------|------|-------|
| project_id | Integer FK → workspace_projects.id | NEW: nullable, replaces text-based `category` |
| **tags** | String(500) | NEW: comma-separated tags like "og-build", "r&d", "prd" |

**Migration**: For each conversation with a `category` value, look up the matching project by name and set `project_id`. Keep `category` column temporarily for backward compat, remove in a later release.

### 1c. Add `project_id` to `workspace_library_folders`

**Current**: id, name, parent_id, created_at, updated_at

**Add**:
| Column | Type | Notes |
|--------|------|-------|
| **project_id** | Integer FK → workspace_projects.id | NEW: nullable (null = global/unscoped) |

Root folders belong to a project. Child folders inherit the project from their root.

### 1d. Add tags to `workspace_library_files`

**Current**: id, conversation_id, folder_id, filename, display_name, file_type, content, file_path, file_size, tags, active_in_context, created_at

The `tags` column already exists (comma-separated string). No schema change needed — we just need to use it properly in the UI.

### 1e. New table: `workspace_project_tags` (predefined tag management)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| project_id | Integer FK | which project this tag belongs to |
| name | String(100) | tag display name (e.g., "OG Build", "R&D", "PRD") |
| color | String(20) | optional color for the tag pill |
| sort_order | Integer | ordering |

This lets users predefine tags per project (especially useful for App Projects which have standard tag categories).

---

## 2. Backend API Changes

### 2a. Projects CRUD (replaces Categories)

Rename all category endpoints to project endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workspace/projects` | List all projects |
| POST | `/workspace/projects` | Create project (with type, description, icon) |
| PATCH | `/workspace/projects/{id}` | Update project (name, color, type, description, icon, working_directory) |
| DELETE | `/workspace/projects/{id}` | Delete project |
| PUT | `/workspace/projects/reorder` | Reorder projects |
| GET | `/workspace/projects/{id}/conversations` | Get conversations for a project |
| GET | `/workspace/projects/{id}/files` | Get library files for a project |

### 2b. Project Tags CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workspace/projects/{id}/tags` | List predefined tags for a project |
| POST | `/workspace/projects/{id}/tags` | Create a tag |
| PATCH | `/workspace/projects/{id}/tags/{tag_id}` | Update tag |
| DELETE | `/workspace/projects/{id}/tags/{tag_id}` | Delete tag |

### 2c. Library Scoping

Update existing library endpoints to support project filtering:

- `GET /workspace/library?project_id=5` — filter files by project
- `GET /workspace/library/tree?project_id=5` — folder tree for a project
- `POST /workspace/library/save-from-chat` — add `project_id` and `tags` to the request body
- `POST /workspace/library/upload` — add `project_id` to the upload

### 2d. Conversation Updates

- `POST /workspace/conversations` — add `project_id` and `tags` to creation payload
- `PATCH /workspace/conversations/{id}` — allow updating `project_id` and `tags`

---

## 3. Frontend Changes

### 3a. Sidebar: Categories → Projects

**WorkspaceSidebar.tsx** changes:
- Rename all "Category" labels to "Project"
- "Manage Categories" modal becomes "Manage Projects" modal
- Project items show an icon badge: folder icon for general, code icon for app projects
- Each project section can be collapsed/expanded (existing behavior)
- Conversations within projects can have tag pills displayed inline

### 3b. New Chat Flow Enhancement

**Current flow**: Click "New Chat" → pick model → (optionally) pick category from separate dropdown → naming form appears

**New flow**: Click "New Chat" → pick model → Enhanced creation form:

```
┌─────────────────────────────┐
│ New Chat                    │
├─────────────────────────────┤
│ Name: [________________]    │
│                             │
│ Project: [▼ Select/Create ] │
│   ○ AutoForge 1 (app)      │
│   ○ Research (general)      │
│   ○ + Create New Project    │
│                             │
│ Tags: [og-build] [+ Add]   │
│                             │
│ Repository: [▼ Select ]     │
│   (shown for app projects)  │
│                             │
│ Model: ○Son ○Opus ○Opus1M  │
│ Effort: ○Low ○Med ○High    │
│                             │
│ [Start Chat]                │
└─────────────────────────────┘
```

Key changes:
- Project dropdown replaces category dropdown
- "Create New Project" option inline (no need to go to Manage modal first)
- Quick inline project creation: name, type (general/app), color picker
- Tags section: pick from predefined project tags or type a new one
- Repository selector only shown when project_type = 'app'
- Everything in one unified form (no separate category dropdown button)

### 3c. Dashboard: Library Panel

Add a collapsible right-side Library panel to `DashboardPage.tsx`:

```
┌──────────┬──────────────────────────┬─────────────┐
│ Sidebar  │ Chat Pane(s)             │ Library  [×]│
│          │                          │             │
│ PROJECTS │ [Chat messages...]       │ Project: ▼  │
│  AF 1    │                          │ [AutoForge] │
│  AF 2    │                          │             │
│  Rsrch   │                          │ Tags: [All] │
│          │                          │ [OG Build]  │
│          │                          │ [R&D]       │
│          │                          │             │
│          │                          │ 📁 Prompts  │
│          │                          │   spec.md   │
│          │                          │   prd.md    │
│          │                          │ 📁 Docs     │
│          │                          │   notes.md  │
│          │                          │             │
│          │                          │ [Upload]    │
│          │                          │ [From Lib]  │
│          │                          │             │
│          │                          │ Sort: ▼     │
│          │                          │ [Name]      │
│          │                          │ [Date]      │
│          │                          │ [Type]      │
└──────────┴──────────────────────────┴─────────────┘
```

Features:
- **Context-aware**: When a chat pane is focused and it belongs to a project, library auto-filters to that project
- **Project dropdown**: Switch between projects or show "All Files"
- **Tag filter**: Filter files by tags within the selected project
- **Sort options**: By name, date, type, tag
- **Upload button**: Upload from computer
- **"From Library" button**: Browse and attach an existing library file to the current chat
- **Drag support** (future): Drag a file from library into a chat pane
- **Toggle**: Toggle button in the dashboard header to show/hide (keyboard shortcut: `L`)

### 3d. Save-to-Library from Chat (Enhanced)

**Current**: "Save to Library" button on assistant messages → saves to root with auto-generated name

**New flow**: "Save to Library" button → Destination picker modal:

```
┌─────────────────────────────────┐
│ Save to Library                 │
├─────────────────────────────────┤
│ Name: [auto-filled from msg]   │
│                                 │
│ Project: [▼ AutoForge 1]       │
│ Folder:  [▼ / Prompts]         │
│ Tags:    [prd] [+ Add tag]     │
│                                 │
│ [Save]  [Cancel]                │
└─────────────────────────────────┘
```

- Auto-fills the project based on the current conversation's project
- Folder picker shows the project's folder tree
- Tag picker shows predefined tags + ability to add new ones
- Works in both Workspace page and Dashboard

### 3e. Manage Projects Modal (replaces Manage Categories)

Enhanced version of the existing category management modal:

```
┌─────────────────────────────────────────┐
│ Manage Projects                         │
├─────────────────────────────────────────┤
│ [+ New Project]                         │
│                                         │
│ 📁 AutoForge 1          [app] [✏️] [🗑] │
│    Tags: OG Build, R&D, PRD             │
│    Repo: ~/Projects/autoforge           │
│    3 conversations, 12 files            │
│                                         │
│ 📁 Research              [gen] [✏️] [🗑] │
│    Tags: (none)                         │
│    5 conversations, 2 files             │
│                                         │
│ [Reorder ↕]                             │
└─────────────────────────────────────────┘
```

Edit form for a project:
- Name (editable, pencil icon)
- Type toggle: General / App Project
- Color picker
- Description (optional textarea)
- Icon picker (emoji)
- Working directory (for app projects, uses RepoSelector)
- Predefined tags: add/remove/reorder tag chips

---

## 4. Data Migration

1. Rename `workspace_categories` table to `workspace_projects`, add new columns
2. For each conversation with `category` text, resolve to `project_id` FK
3. Existing library folders get `project_id = NULL` (global) — users can move them into projects later
4. All existing library files keep working unchanged

The migration is backward-compatible: everything that exists today continues to work, the new project features are additive.

---

## 5. Implementation Order

### Phase 1: Database + Backend (no UI breakage)
1. Add new columns to `workspace_categories` (keep old table name internally, expose as "projects" in API)
2. Add `project_id` to `workspace_conversations` and `workspace_library_folders`
3. Create `workspace_project_tags` table
4. Add new API endpoints alongside existing category endpoints
5. Migrate existing category data

### Phase 2: Sidebar + New Chat
6. Rename sidebar labels: Categories → Projects
7. Enhance new-chat form with project selection + inline creation
8. Update "Manage Categories" → "Manage Projects" modal

### Phase 3: Dashboard Library Panel
9. Create `DashboardLibrary` component (adapted from WorkspaceLibrary)
10. Add toggle button + keyboard shortcut
11. Add project/tag filtering
12. Add sort options

### Phase 4: Save-to-Library Enhancement
13. Create destination picker modal
14. Wire up save-from-chat with project + folder + tag selection
15. Wire up "From Library" attachment picker in chats

---

## 6. What's NOT in Scope (Future)

- Cloud backup for library files (S3/GCS)
- Drag-and-drop files into chat
- File versioning / history
- Collaborative (multi-user) projects
- Prompt template system (mentioned by user — separate feature)
- AI-powered auto-tagging of files
