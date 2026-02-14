# AutoForge PRD Context Document

> **Purpose**: Give a fresh agent everything it needs to convert a handoff document into
> a production-ready `app_spec.txt` PRD for the AutoForge autonomous coding system.
>
> **Usage**: Reference this document at the start of any handoff-to-PRD conversion session.

---

## SECTION 1: STANDARDS LAYER

### 1.1 AutoForge Architecture Overview

AutoForge is an autonomous coding agent system built on the Claude Agent SDK. It uses a
**two-agent pattern** to build complete applications across multiple sessions:

1. **Initializer Agent** (Session 1) -- Reads the `app_spec.txt` specification and creates
   features in a SQLite database (`features.db`). Sets up project scaffolding, `init.sh`,
   and git repository. Does NOT implement any code.

2. **Coding Agent** (Sessions 2+) -- Picks up features one by one (or in batches of 1-3),
   implements them, verifies them through browser automation (Playwright MCP), and marks
   them as passing. Each agent session operates under a strict 45% context window budget.

**Feature lifecycle states:**
```
PENDING --> IN_PROGRESS --> PASSING
                |
                v
             FAILING (rolls back to pending, agent retries)
```

**How agents interact with features:**
- Features live in SQLite, managed through an MCP (Model Context Protocol) server
- MCP tools: `feature_get_by_id`, `feature_mark_in_progress`, `feature_mark_passing`,
  `feature_mark_failing`, `feature_skip`, `feature_create_bulk`, etc.
- Features are IMMUTABLE once created -- agents can only change the `passes` status
- Features are never deleted, edited, reordered, or consolidated after creation

**Testing modes:**
- **Standard mode**: Full Playwright browser testing + lint/typecheck. Features verified
  with real UI interaction and screenshots before marking as passing.
- **YOLO mode**: Skips browser testing entirely. Features marked passing after lint and
  typecheck succeed. Used for rapid prototyping only.

**Parallel execution:**
- Up to 5 concurrent coding agents can work simultaneously
- Features declare dependencies so agents never work on blocked features
- Dependencies must form a DAG (directed acyclic graph) -- no cycles allowed
- The orchestrator uses `feature_claim_and_get` for atomic feature assignment

### 1.2 Coding Standards (25 Rules)

These rules are enforced by the coding agent during implementation. The PRD does not need
to repeat them, but feature steps should be written with awareness of these constraints.

**Technical rules (1-7):**
1. NO database calls in UI components -- use a service layer
2. NO unprotected routes for authenticated features
3. NO inline styles -- Tailwind CSS only
4. NO `any` types -- define TypeScript interfaces for everything
5. ALL database writes include `createdAt` / `updatedAt` timestamps
6. ALL user data scoped to the authenticated user
7. Wrap the app in an `ErrorBoundary` component

**UI/UX rules (8-25):**
8. NO `alert()`, `confirm()`, `prompt()` -- use Modal/ConfirmModal/Toast
9. ALL destructive actions require a ConfirmModal
10. ALL async operations show loading state (Skeleton for lists, Spinner in buttons)
11. ALL empty lists use EmptyState component with icon and CTA
12. ALL success/error actions show Toast feedback
13. ALL saved items have a Detail View (read-only) separate from Edit View
14. ALL forms validate before submission
15. ALL buttons show loading state during async actions
16. ALL avatars have fallback for failed images
17. ALL pages set document title via `usePageTitle` hook
18. ALL forms autofocus the first input
19. ALL lists with > 5 expected items have search/filter
20. ALL error states have a retry action
21. ALL dates formatted as relative time (not raw timestamps)
22. ALL long text truncated with ellipsis
23. ALL detail pages have back navigation
24. Use Lucide React for all icons
25. Zero console errors in production

**Navigation flow pattern:**
```
LIST --> click item --> DETAIL (read-only) --> click edit --> EDIT --> save --> DETAIL
LIST --> click new  --> CREATE --> save --> DETAIL
DETAIL --> delete (with ConfirmModal) --> LIST
```

**File structure convention:**
```
src/
  config/          # Backend configuration
  contexts/        # Auth, Theme, Toast, feature contexts
  hooks/           # useAuth, usePageTitle, custom hooks
  components/
    ProtectedRoute.tsx
    ErrorBoundary.tsx
    Layout.tsx
    ui/            # Modal, ConfirmModal, Toast, Button, Avatar, Skeleton, EmptyState
  pages/           # LandingPage, LoginPage, Dashboard, Profile, [Item]Detail/Create/Edit
  services/        # api.ts (ALL backend operations)
  utils/           # formatDate.ts, pluralize.ts
  types/           # index.ts (ALL TypeScript interfaces)
```

### 1.3 The app_spec.txt XML Format

This is the exact format the Initializer Agent reads. Every PRD you produce must follow
this structure precisely.

```xml
<project_specification>
  <project_name>my-app-name</project_name>

  <overview>
    2-3 sentences describing what this app does, what problem it solves,
    and who it is for.
  </overview>

  <technology_stack>
    <frontend>
      <framework>React with Vite</framework>
      <styling>Tailwind CSS</styling>
      <state_management>React hooks and context</state_management>
      <routing>React Router</routing>
      <port>3000</port>
    </frontend>
    <backend>
      <runtime>Node.js with Express</runtime>
      <database>SQLite with better-sqlite3</database>
      <port>3001</port>
    </backend>
    <communication>
      <api>RESTful endpoints</api>
    </communication>
  </technology_stack>

  <prerequisites>
    <environment_setup>
      - Node.js 18+ installed
      - npm package manager
      - Any required API keys or services
    </environment_setup>
  </prerequisites>

  <feature_count>NUMBER</feature_count>

  <core_features>
    <category_name>
      - Feature description starting with action verb
      - Another testable behavior
    </category_name>
    <!-- Repeat for all categories -->
  </core_features>

  <database_schema>
    <tables>
      <table_name>
        - id (PRIMARY KEY)
        - field_name (TYPE, constraints)
        - created_at, updated_at
      </table_name>
    </tables>
  </database_schema>

  <api_endpoints_summary>
    <category>
      - GET /api/resource (list with pagination)
      - POST /api/resource (create)
      - GET /api/resource/:id (get single)
      - PUT /api/resource/:id (update)
      - DELETE /api/resource/:id (delete)
    </category>
  </api_endpoints_summary>

  <ui_layout>
    <main_structure>
      - Header with navigation and user menu
      - Sidebar for navigation (collapsible on mobile)
      - Main content area
    </main_structure>
  </ui_layout>

  <design_system>
    <color_palette>
      - Primary: #3B82F6
      - Background: #FFFFFF (light), #1A1A1A (dark)
      - Text: #1F2937 (light), #E5E5E5 (dark)
      - Error: #EF4444
      - Success: #10B981
    </color_palette>
    <typography>
      - Font family: Inter, system-ui, sans-serif
      - Headings: font-semibold
      - Body: font-normal
    </typography>
  </design_system>

  <ui_ux_standards>
    <banned_patterns>
      - alert(), confirm(), prompt() - Use modals and toasts instead
      - Text-only empty states - Use EmptyState component with icon + CTA
      - Loading states that just say "Loading..." - Use skeleton loaders
      - Delete without confirmation - Always use ConfirmModal
      - Raw timestamps - Format as relative time
    </banned_patterns>
    <required_components>
      - Modal, ConfirmModal, Toast/notification system, Skeleton loader
      - EmptyState, ErrorBoundary, Button with loading state, Avatar with fallback
    </required_components>
    <page_patterns>
      - List View -> Detail View (read-only) -> Create View / Edit View
      - Never open directly into edit mode from a list
      - Separate view and edit concerns
    </page_patterns>
    <feedback_protocol>
      - Success: toast + navigate. Error: toast + stay + keep data.
      - Delete: confirm -> loading -> toast + redirect
    </feedback_protocol>
    <polish_requirements>
      - Relative dates, text truncation, back navigation, hover states, focus states
      - Autofocus, pluralization, search/filter, retry on error, unsaved changes warning
    </polish_requirements>
    <accessibility_basics>
      - Focus rings, Escape closes modals, aria-labels on icon buttons, labels on inputs
    </accessibility_basics>
  </ui_ux_standards>

  <coding_standards>
    <architecture>
      - One component per file, feature folders for grouping
      - Service layer: DB/API calls in services, not UI components
      - TypeScript interfaces for all data types, no 'any'
      - createdAt/updatedAt on all DB writes
      - User data scoped by user ID
    </architecture>
    <routing>
      - Public vs protected vs admin routes as separate concerns
      - Route-level 404 catch-all
      - Auth redirects
    </routing>
    <error_handling>
      - ErrorBoundary wraps entire app
      - User-friendly error messages, not raw errors
      - Offline detection, session expiry handling
      - Retry action on every error state
    </error_handling>
  </coding_standards>

  <key_interactions>
    <user_flow_name>
      1. User navigates to /page
      2. User performs action
      3. System responds with result
      4. User sees confirmation
    </user_flow_name>
  </key_interactions>

  <implementation_steps>
    <step number="1">
      <title>Phase Title</title>
      <tasks>
        - Task 1
        - Task 2
      </tasks>
    </step>
  </implementation_steps>

  <success_criteria>
    <functionality>
      - All features work as specified
      - No console errors in browser
      - Data persists correctly in database
    </functionality>
    <user_experience>
      - Responsive on all device sizes
      - Fast load times
      - Clear feedback for all actions
    </user_experience>
    <technical_quality>
      - Clean code structure
      - Proper error handling
      - Secure authentication
    </technical_quality>
  </success_criteria>
</project_specification>
```

### 1.4 Feature Writing Rules

**Sizing constraints:**
- Target 15-20 features per spec for AutoForge internal features (self-building)
- For standalone apps built BY AutoForge, the Initializer expands spec features into
  165-405 granular test cases. Your PRD defines the high-level features; the Initializer
  breaks them down.
- Each high-level feature in `<core_features>` should be completable in one coding agent
  session (roughly 30-60 minutes of agent work)

**How to write good features:**
- Start with an action verb: "User can...", "System displays...", "API returns..."
- Be specific and testable -- someone should be able to verify pass/fail
- One behavior per feature line
- Group by functional area using XML category tags

**Good features:**
```
- User can create a new project with name and description
- Dashboard displays total revenue and order count for the current month
- API returns 401 for unauthenticated requests to protected endpoints
- Search results update in real-time as user types (debounced 300ms)
```

**Bad features:**
```
- Implement the dashboard (too vague, not testable)
- Make it work (meaningless)
- Add all CRUD operations (too broad, should be split)
- Style the app (not specific enough)
```

**Dependency ordering in the spec:**
- Foundation features first: database setup, project scaffolding, core API
- Authentication second (if applicable)
- Core CRUD operations third
- UI polish and advanced features last
- The Initializer will create explicit dependency edges in the feature database

**Infrastructure features (indices 0-4) are mandatory** for any app with a database:
1. Database connection established
2. Database schema applied correctly
3. Data persists across server restart
4. No mock data patterns in codebase
5. Backend API queries real database

All other features depend on these five. They ensure the coding agent builds with a real
database, not mock data or in-memory stores.

**The 20 mandatory test categories** that the Initializer distributes features across:
Infrastructure, Security & Access Control, Navigation Integrity, Real Data Verification,
Workflow Completeness, Error Handling, UI-Backend Integration, State & Persistence,
URL & Direct Access, Double-Action & Idempotency, Data Cleanup & Cascade, Default & Reset,
Search & Filter Edge Cases, Form Validation, Feedback & Notification, Responsive & Layout,
Accessibility, Temporal & Timezone, Concurrency & Race Conditions, Export/Import, Performance.

---

## SECTION 2: PRODUCT LAYER

### 2.1 What AutoForge Is

AutoForge is an autonomous coding agent system that builds complete, production-grade
web applications. It differentiates itself through:

- **Two-agent architecture**: Initializer creates a structured feature database, coding
  agents implement features one by one with full verification
- **QA pipeline**: Code review agents, regression testing agents, and final QA sweeps
  ensure professional output (planned/in-progress)
- **Consistent design system**: 12 built-in styles with full Tailwind token sets,
  4 accessibility modifiers, and style mixing (base + accent)
- **Real verification**: Playwright browser testing with screenshots, not just "code
  that compiles"

### 2.2 Current Capabilities

- **12 design styles** with complete Tailwind theme tokens
- **4 accessibility modifiers** for enhanced usability
- **Style mixing** -- combine a base style with accent elements from another
- **Parallel agent mode** -- up to 5 concurrent coding agents working on independent features
- **Batch feature implementation** -- agents can implement 1-3 features per session
- **Scheduler** -- automated builds on a time-based schedule
- **WebSocket real-time UI** -- live progress tracking with agent mascots
- **YOLO mode** -- rapid prototyping without browser testing
- **Project registry** -- manage multiple projects across any directory

### 2.3 The Vision

- **Pre-build intelligence**: Spec analysis, architecture planning, complexity estimation
- **QA pipeline**: Code review + regression testing + final QA sweep per build
- **Post-build reports**: Documentation generation, performance audit, security audit
- **Credit-based pricing**: $219-799 per build with BYOK (bring your own key) option
- **Marketplace**: Boilerplate templates, custom styles, plugins

---

## SECTION 3: HANDOFF-TO-PRD CONVERSION INSTRUCTIONS

This is the actionable workflow for converting a handoff document into a complete
`app_spec.txt` ready for AutoForge.

### 3.1 Step-by-Step Conversion Process

**Step 1: Read the entire handoff document.**
Understand the full scope. Identify:
- What is being built (the product)
- Who uses it (target user)
- What the core problem is (pain point)
- All features described, including implicit ones
- Any technical requirements or constraints mentioned
- External integrations or APIs needed

**Step 2: Determine if this is an AutoForge-internal feature or a standalone app.**
- **AutoForge-internal**: Features that extend AutoForge itself (new pipeline stage,
  new UI panel, new agent type). These go into the AutoForge codebase with its existing
  FastAPI + React architecture.
- **Standalone app**: A new application built BY AutoForge from scratch. These get their
  own `app_spec.txt` with a fresh tech stack.

**Step 3: Break the handoff into atomic features.**
Each feature must be:
- Independently buildable by a single coding agent session
- Independently testable (you can verify pass/fail without other features)
- Specific enough that the agent knows exactly what to build
- Small enough to fit within the 45% context budget (~120 agent turns)

If a described capability is too large, split it:
```
BAD:  "Full admin panel with user management, analytics, and settings"
GOOD: "Admin can view list of all users with search and pagination"
      "Admin can edit user roles via dropdown on user detail page"
      "Admin can deactivate a user account with confirmation modal"
      "Admin dashboard displays user count and activity chart"
      "Admin can configure system settings via settings page"
```

**Step 4: Order by dependencies.**
Build the dependency tree:
1. Infrastructure (database, project setup) -- always first
2. Authentication and authorization (if needed)
3. Core data models and CRUD -- the foundation entities
4. Core UI pages -- list views, detail views, forms
5. Business logic -- workflows, calculations, automations
6. Integrations -- external APIs, webhooks, notifications
7. Polish -- search, filters, responsive design, accessibility
8. Advanced features -- analytics, export/import, performance

**Step 5: Write concrete feature descriptions.**
Use the `<core_features>` format with category tags. Each line starts with an action
verb and describes one testable behavior.

**Step 6: Set proper categories.**
Choose from these standard categories (or create domain-specific ones):
- `infrastructure` -- database, server setup, health checks
- `authentication` -- login, register, session management
- `core_data` or domain-specific name -- primary CRUD operations
- `api_layer` -- REST endpoints, validation, error responses
- `dashboard` -- analytics, charts, summary views
- `user_interface` -- responsive layout, navigation, modals
- `search_and_filter` -- search, sort, filter functionality
- `settings` -- user preferences, app configuration
- `integration` -- external APIs, webhooks
- `polish` -- accessibility, performance, edge cases

**Step 7: Define the tech stack.**
For standalone apps, specify:
- Frontend framework (React + Vite is the default)
- Styling (Tailwind CSS is the default)
- Backend runtime (Node.js + Express is the default)
- Database (SQLite with better-sqlite3 is the default)
- Any additional libraries needed (charting, file upload, etc.)

**Step 8: Write the database schema.**
Define all tables with their columns, types, and relationships. Include:
- Primary keys
- Foreign keys with references
- NOT NULL constraints on required fields
- UNIQUE constraints where appropriate
- `created_at` and `updated_at` on every table

**Step 9: Define API endpoints.**
List all REST endpoints grouped by resource:
- Include HTTP method, path, and brief description
- Cover CRUD for every entity
- Include auth endpoints if applicable
- Include any special endpoints (search, bulk operations, etc.)

**Step 10: Estimate feature count.**
Count the total testable behaviors across all categories. Use these reference ranges:
- Simple app (utility, calculator, notes): 25-55 features
- Medium app (blog, task manager with auth): ~105 features
- Advanced app (e-commerce, CRM, SaaS): 155-205 features

The Initializer agent will expand these into the full 165-405 granular test cases.

### 3.2 Example Conversion

**Handoff excerpt:**
> "Users can create projects. Each project has a name, description, and status
> (active/archived). Users should be able to search their projects and archive
> old ones. The dashboard shows a count of active projects."

**Converted to `<core_features>` format:**

```xml
<core_features>
  <project_management>
    - User can create a new project with name and description
    - User can view a list of all their projects with pagination
    - User can view project detail page (read-only) with all fields
    - User can edit project name and description from detail page
    - User can delete a project with confirmation modal
    - User can archive a project (status changes to archived)
    - User can unarchive a project (status changes to active)
    - User can search projects by name (debounced input)
    - User can filter projects by status (active/archived/all)
    - Empty project list shows EmptyState with "Create your first project" CTA
  </project_management>

  <dashboard>
    - Dashboard displays count of active projects
    - Dashboard count updates when projects are created or archived
    - Dashboard links to project list view
  </dashboard>
</core_features>
```

**Corresponding database schema:**

```xml
<database_schema>
  <tables>
    <projects>
      - id (INTEGER PRIMARY KEY AUTOINCREMENT)
      - user_id (INTEGER NOT NULL, FOREIGN KEY -> users.id)
      - name (TEXT NOT NULL)
      - description (TEXT)
      - status (TEXT NOT NULL DEFAULT 'active', CHECK IN ('active', 'archived'))
      - created_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
      - updated_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
    </projects>
  </tables>
</database_schema>
```

**Corresponding API endpoints:**

```xml
<api_endpoints_summary>
  <projects>
    - GET /api/projects (list with pagination, search, status filter)
    - POST /api/projects (create)
    - GET /api/projects/:id (get single)
    - PUT /api/projects/:id (update name, description)
    - DELETE /api/projects/:id (delete)
    - PATCH /api/projects/:id/archive (archive/unarchive)
    - GET /api/projects/stats (dashboard counts)
  </projects>
</api_endpoints_summary>
```

### 3.3 Handling AutoForge-Internal Handoffs

When the handoff describes a feature for AutoForge itself (not a standalone app), the
conversion is different:

1. **Tech stack is fixed**: FastAPI backend (Python), React 19 + TypeScript + Vite frontend,
   Tailwind CSS v4, TanStack Query, SQLAlchemy for database
2. **Features map to the existing codebase**: New routers in `server/routers/`, new
   services in `server/services/`, new components in `ui/src/components/`
3. **The PRD should reference existing patterns**: Follow the same conventions as existing
   routers, services, and components
4. **Testing uses existing infrastructure**: `ruff check .` for Python linting,
   `npm run lint` and `npm run build` for TypeScript, Playwright for e2e

For internal features, the `app_spec.txt` becomes a "feature spec" that describes the
new capability within the existing architecture rather than a standalone project.

---

## SECTION 4: QUALITY CHECKLIST

Before finalizing any PRD, verify every item:

### Feature Quality
- [ ] Every feature starts with an action verb ("User can...", "System displays...", "API returns...")
- [ ] Every feature describes exactly one testable behavior
- [ ] No feature is too vague ("implement the feature", "make it work")
- [ ] No feature is too broad (should be split if it describes multiple behaviors)
- [ ] Every feature is independently verifiable (how would you confirm pass/fail?)
- [ ] No feature exceeds 8 steps (split if larger)
- [ ] Features cover happy path AND error cases

### Structural Integrity
- [ ] Dependencies form a valid DAG -- no circular references
- [ ] Foundation features (infrastructure, auth) have no dependencies on later features
- [ ] Feature ordering follows the dependency tree (foundation first, polish last)
- [ ] Feature count matches the `<feature_count>` tag
- [ ] Feature IDs are sequential with no gaps
- [ ] Category assignments are logical and consistent

### Technical Completeness
- [ ] `<technology_stack>` specifies all frameworks, libraries, and ports
- [ ] `<database_schema>` covers every entity mentioned in features
- [ ] Every table has `id`, `created_at`, `updated_at` columns
- [ ] `<api_endpoints_summary>` covers CRUD for every entity
- [ ] All foreign key relationships are defined
- [ ] Authentication is specified if any features require it

### Spec Completeness
- [ ] `<overview>` clearly describes what this builds, for whom, and why
- [ ] `<prerequisites>` lists all environment requirements
- [ ] `<ui_layout>` describes the main page structure
- [ ] `<design_system>` specifies colors, typography, and spacing
- [ ] `<ui_ux_standards>` section is present with banned patterns and required components
- [ ] `<coding_standards>` section is present with architecture and error handling rules
- [ ] `<key_interactions>` describes at least 2-3 critical user flows
- [ ] `<implementation_steps>` provides a phased build order
- [ ] `<success_criteria>` defines what "done" means for functionality, UX, and quality

### Common Mistakes to Avoid
- Forgetting the 5 mandatory infrastructure features for database-backed apps
- Writing features that require multiple agent sessions to implement (too large)
- Omitting error handling and edge case features
- Specifying a tech stack without port numbers
- Leaving `<feature_count>` as a placeholder instead of an actual number
- Listing infrastructure items (auth, responsive design) as core differentiating features
  when they should be assumed baseline requirements
- Creating linear dependency chains (A->B->C->D) instead of wide graphs that enable
  parallel execution

---

## APPENDIX A: Complete Minimal Example

Below is a complete, minimal `app_spec.txt` for a simple task management app. Use this
as a structural template when producing PRDs.

```xml
<project_specification>
  <project_name>task-flow</project_name>

  <overview>
    TaskFlow is a personal task management application that helps users organize
    their work with projects and tasks. Users can create projects, add tasks to
    them, and track completion status. Built for individual productivity.
  </overview>

  <technology_stack>
    <frontend>
      <framework>React with Vite</framework>
      <styling>Tailwind CSS</styling>
      <state_management>React hooks and context</state_management>
      <routing>React Router</routing>
      <port>3000</port>
    </frontend>
    <backend>
      <runtime>Node.js with Express</runtime>
      <database>SQLite with better-sqlite3</database>
      <port>3001</port>
    </backend>
    <communication>
      <api>RESTful endpoints</api>
    </communication>
  </technology_stack>

  <prerequisites>
    <environment_setup>
      - Node.js 18+ installed
      - npm package manager
    </environment_setup>
  </prerequisites>

  <feature_count>55</feature_count>

  <core_features>
    <authentication>
      - User can register with email and password
      - User can log in with email and password
      - User can log out
      - System redirects unauthenticated users to login page
      - Login form shows error message for invalid credentials
    </authentication>

    <projects>
      - User can create a new project with name and description
      - User can view a list of all their projects
      - User can view project detail page with task count
      - User can edit project name and description
      - User can delete a project with confirmation modal
      - User can archive a project
      - Deleting a project also deletes all its tasks
    </projects>

    <tasks>
      - User can create a task within a project with title and due date
      - User can view list of tasks in a project
      - User can view task detail page
      - User can edit task title, description, and due date
      - User can mark a task as complete
      - User can mark a completed task as incomplete
      - User can delete a task with confirmation
      - Tasks display due date as relative time
      - Overdue tasks are visually highlighted
    </tasks>

    <dashboard>
      - Dashboard shows total tasks, completed tasks, and overdue count
      - Dashboard shows list of upcoming tasks (next 7 days)
      - Dashboard links to relevant project pages
    </dashboard>

    <search_and_filter>
      - User can search tasks by title across all projects
      - User can filter tasks by status (all, active, completed)
      - User can sort tasks by due date or creation date
    </search_and_filter>

    <user_interface>
      - App is responsive on mobile (375px), tablet (768px), desktop (1920px)
      - Loading states show skeleton placeholders
      - Empty states show helpful message with CTA
      - All forms validate required fields before submission
      - Toast notifications for all create/update/delete actions
    </user_interface>
  </core_features>

  <database_schema>
    <tables>
      <users>
        - id (INTEGER PRIMARY KEY AUTOINCREMENT)
        - email (TEXT UNIQUE NOT NULL)
        - password_hash (TEXT NOT NULL)
        - name (TEXT)
        - created_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
        - updated_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
      </users>
      <projects>
        - id (INTEGER PRIMARY KEY AUTOINCREMENT)
        - user_id (INTEGER NOT NULL, FOREIGN KEY -> users.id)
        - name (TEXT NOT NULL)
        - description (TEXT)
        - status (TEXT NOT NULL DEFAULT 'active')
        - created_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
        - updated_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
      </projects>
      <tasks>
        - id (INTEGER PRIMARY KEY AUTOINCREMENT)
        - project_id (INTEGER NOT NULL, FOREIGN KEY -> projects.id ON DELETE CASCADE)
        - user_id (INTEGER NOT NULL, FOREIGN KEY -> users.id)
        - title (TEXT NOT NULL)
        - description (TEXT)
        - due_date (TEXT)
        - completed (INTEGER NOT NULL DEFAULT 0)
        - created_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
        - updated_at (TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)
      </tasks>
    </tables>
  </database_schema>

  <api_endpoints_summary>
    <authentication>
      - POST /api/auth/register
      - POST /api/auth/login
      - POST /api/auth/logout
      - GET /api/auth/me
    </authentication>
    <projects>
      - GET /api/projects (list user's projects)
      - POST /api/projects (create)
      - GET /api/projects/:id (get single with task count)
      - PUT /api/projects/:id (update)
      - DELETE /api/projects/:id (delete with cascade)
      - PATCH /api/projects/:id/archive (archive)
    </projects>
    <tasks>
      - GET /api/projects/:projectId/tasks (list tasks in project)
      - POST /api/projects/:projectId/tasks (create task)
      - GET /api/tasks/:id (get single task)
      - PUT /api/tasks/:id (update)
      - DELETE /api/tasks/:id (delete)
      - PATCH /api/tasks/:id/complete (toggle completion)
      - GET /api/tasks/search?q=term (search across projects)
    </tasks>
    <dashboard>
      - GET /api/dashboard/stats (task counts)
      - GET /api/dashboard/upcoming (next 7 days tasks)
    </dashboard>
  </api_endpoints_summary>

  <ui_layout>
    <main_structure>
      - Header with app name, navigation links, and user menu
      - Sidebar with project list (collapsible on mobile)
      - Main content area for current page
    </main_structure>
  </ui_layout>

  <design_system>
    <color_palette>
      - Primary: #3B82F6 (blue)
      - Background: #FFFFFF (light), #1A1A1A (dark)
      - Text: #1F2937 (light), #E5E5E5 (dark)
      - Error: #EF4444
      - Success: #10B981
      - Warning: #F59E0B
    </color_palette>
    <typography>
      - Font family: Inter, system-ui, sans-serif
      - Headings: font-semibold
      - Body: font-normal
    </typography>
  </design_system>

  <ui_ux_standards>
    <banned_patterns>
      - alert(), confirm(), prompt() - Use modals and toasts instead
      - Text-only empty states - Use EmptyState component with icon + CTA
      - Loading states that just say "Loading..." - Use skeleton loaders
      - Delete without confirmation - Always use ConfirmModal
      - Raw timestamps - Format as relative time
    </banned_patterns>
    <required_components>
      - Modal, ConfirmModal, Toast/notification system, Skeleton loader
      - EmptyState, ErrorBoundary, Button with loading state, Avatar with fallback
    </required_components>
    <page_patterns>
      - List View -> Detail View (read-only) -> Create View / Edit View
      - Never open directly into edit mode from a list
      - Separate view and edit concerns
    </page_patterns>
    <feedback_protocol>
      - Success: toast + navigate. Error: toast + stay + keep data.
      - Delete: confirm -> loading -> toast + redirect
    </feedback_protocol>
    <polish_requirements>
      - Relative dates, text truncation, back navigation, hover states, focus states
      - Autofocus, pluralization, search/filter, retry on error, unsaved changes warning
    </polish_requirements>
    <accessibility_basics>
      - Focus rings, Escape closes modals, aria-labels on icon buttons, labels on inputs
    </accessibility_basics>
  </ui_ux_standards>

  <coding_standards>
    <architecture>
      - One component per file, feature folders for grouping
      - Service layer: DB/API calls in services, not UI components
      - TypeScript interfaces for all data types, no 'any'
      - createdAt/updatedAt on all DB writes
      - User data scoped by user ID
    </architecture>
    <routing>
      - Public vs protected vs admin routes as separate concerns
      - Route-level 404 catch-all
      - Auth redirects
    </routing>
    <error_handling>
      - ErrorBoundary wraps entire app
      - User-friendly error messages, not raw errors
      - Retry action on every error state
    </error_handling>
  </coding_standards>

  <key_interactions>
    <create_task_flow>
      1. User navigates to a project detail page
      2. User clicks "Add Task" button
      3. Create form appears with title (required) and due date (optional)
      4. User fills in fields and clicks Save
      5. Task appears in the project's task list with success toast
      6. Task count on project card updates
    </create_task_flow>
    <complete_task_flow>
      1. User views task list in a project
      2. User clicks checkbox next to a task
      3. Task moves to completed state with visual change
      4. Dashboard stats update to reflect new completion count
    </complete_task_flow>
  </key_interactions>

  <implementation_steps>
    <step number="1">
      <title>Project Setup and Database</title>
      <tasks>
        - Initialize React frontend with Vite and Tailwind
        - Set up Express backend with SQLite
        - Create database schema and migration
        - Implement health check endpoint
      </tasks>
    </step>
    <step number="2">
      <title>Authentication</title>
      <tasks>
        - Implement user registration and login API
        - Create login and register pages
        - Add session management with JWT
        - Create ProtectedRoute component
      </tasks>
    </step>
    <step number="3">
      <title>Projects CRUD</title>
      <tasks>
        - Build project API endpoints
        - Create project list, detail, create, and edit pages
        - Implement archive functionality
        - Add cascade delete for projects
      </tasks>
    </step>
    <step number="4">
      <title>Tasks CRUD</title>
      <tasks>
        - Build task API endpoints
        - Create task list, detail, create, and edit views
        - Implement task completion toggle
        - Add due date display and overdue highlighting
      </tasks>
    </step>
    <step number="5">
      <title>Dashboard and Search</title>
      <tasks>
        - Build dashboard with stats and upcoming tasks
        - Implement cross-project task search
        - Add filtering and sorting
      </tasks>
    </step>
    <step number="6">
      <title>Polish</title>
      <tasks>
        - Add responsive design for all breakpoints
        - Implement loading skeletons and empty states
        - Add toast notifications and form validation
        - Verify accessibility basics
      </tasks>
    </step>
  </implementation_steps>

  <success_criteria>
    <functionality>
      - All CRUD operations work for projects and tasks
      - Authentication flow is complete and secure
      - Dashboard displays accurate, real-time statistics
      - Search returns relevant results across all user projects
    </functionality>
    <user_experience>
      - Responsive on mobile (375px), tablet (768px), desktop (1920px)
      - All actions provide immediate visual feedback
      - Loading states prevent user confusion
      - Error messages are helpful and actionable
    </user_experience>
    <technical_quality>
      - Zero console errors
      - All data persists in SQLite (no mock data)
      - TypeScript strict mode with no 'any' types
      - Service layer pattern consistently applied
    </technical_quality>
  </success_criteria>
</project_specification>
```

---

## APPENDIX B: Quick Reference Card

**When you receive a handoff, follow this sequence:**

```
1. READ the handoff completely
2. IDENTIFY: standalone app or AutoForge-internal feature?
3. EXTRACT: product identity (name, description, target user, core problem)
4. LIST: all features mentioned or implied
5. SPLIT: any feature too large for one agent session
6. ORDER: by dependency (foundation -> core -> advanced -> polish)
7. CATEGORIZE: assign each feature to a category tag
8. DERIVE: database schema from the features
9. DERIVE: API endpoints from the CRUD operations
10. WRITE: the complete app_spec.txt in XML format
11. VERIFY: against the Section 4 quality checklist
12. OUTPUT: the file ready for .autoforge/prompts/app_spec.txt
```

**Default tech stack (use unless handoff specifies otherwise):**
- Frontend: React + Vite + Tailwind CSS + React Router
- Backend: Node.js + Express
- Database: SQLite + better-sqlite3
- Ports: Frontend 3000, Backend 3001

**Feature count reference:**
- Simple: 25-55 features (expanded to ~165 test cases by Initializer)
- Medium: ~105 features (expanded to ~265 test cases)
- Advanced: 155-205 features (expanded to ~405 test cases)
