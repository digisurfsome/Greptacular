# AutoForge Pre-Build Intelligence Pipeline Handoff

## Overview

This handoff describes three features that run BEFORE AutoForge starts building code, transforming the build process from "blindly execute the spec" into "analyze, plan, then execute with consistency."

**The core problem today:** AutoForge takes an `app_spec.txt` and immediately hands it to an initializer agent that creates features, then coding agents that implement them. There is:
1. **No validation** of the spec -- missing auth flows, contradictory requirements, and vague descriptions are discovered mid-build, wasting agent sessions
2. **No architecture planning** -- each coding agent session makes independent architectural decisions (database schema, API structure, component hierarchy), leading to inconsistency across features
3. **No dependency intelligence** -- the initializer creates features but dependency relationships are manually specified via `depends_on_indices`, which is error-prone and often incomplete

**The solution:** A 3-phase pre-build pipeline that runs before the first line of application code is written:

```
Phase 0: SPEC ANALYSIS (new agent type)
  Spec Analyzer reads app_spec.txt
  Validates completeness, detects contradictions
  Estimates build complexity and flags missing infrastructure
  Outputs spec-analysis.md with completeness score (1-5)
  Blocks build if score < 3 (configurable)

Phase 0.5: ARCHITECTURE PLANNING (new agent type)
  Architect reads validated spec
  Designs database schema, API structure, component tree
  Defines routing map, state management, auth strategy
  Outputs ARCHITECTURE.md committed to project root
  All subsequent agents reference this document

Phase 1: INITIALIZATION (existing, enhanced)
  Initializer creates features from spec (existing behavior)
  NEW: Second pass auto-detects dependencies between features
  Uses AI analysis + heuristics to call feature_add_dependency
  Validates acyclic graph via existing Kahn's algorithm
```

### Why This Matters

Consider a 200-feature project. Without pre-build intelligence:
- Agent session 15 discovers the spec says "users can only have one profile" but feature 87 says "switch between profiles" -- 14 wasted sessions
- Agent session 30 designs a REST API with `/api/v1/users`, while agent session 45 creates `/users` -- inconsistent API surface
- Feature 150 ("edit user settings") runs before Feature 12 ("user registration") because no dependency was specified

With pre-build intelligence:
- The contradiction is caught before any code is written
- Every agent references the same `ARCHITECTURE.md` for consistent decisions
- Dependencies are auto-detected: "edit settings" depends on "registration"

---

## Feature 1: Smart Spec Analyzer Agent

### What It Does

A new agent type (`spec-analyzer`) that runs as the very first phase, before initialization. It reads the `app_spec.txt` and performs comprehensive validation, producing a structured report that identifies issues before any build resources are spent.

### Why It Is Cheap

The spec analyzer:
- Does NOT use Playwright (no browser needed -- pure text analysis)
- Does NOT write application code (read-only analysis + one report file)
- Uses 30-50 turns (vs 100-150 for coding agents, vs 200 for initializer)
- Only reads `app_spec.txt` and writes `spec-analysis.md`
- Runs exactly once per project, before the initializer

On a Max subscription, this is roughly 25% the rate limit impact of a single coding agent session.

### Implementation

#### 1.1 New Agent Type: `spec-analyzer`

Add to `autonomous_agent_demo.py` CLI args:

```python
parser.add_argument(
    "--agent-type",
    choices=["initializer", "coding", "testing", "spec-analyzer", "architect"],
    default=None,
    help="Agent type (used by orchestrator to spawn specialized subprocesses)",
)
```

#### 1.2 Spec Analyzer Prompt Template

Create `.claude/templates/spec_analyzer_prompt.template.md`:

```markdown
## YOUR ROLE - SPEC ANALYZER AGENT

You are a **specification analysis agent** responsible for validating the application
specification BEFORE any code is written. Your job is to find problems, gaps,
contradictions, and missing infrastructure that would cause wasted effort during
the build phase.

You are the first line of defense against spec-level bugs.

### STEP 1: READ THE SPEC

Read `app_spec.txt` in the project root. This contains the complete specification
for the application to be built.

```bash
cat app_spec.txt
```

Study it thoroughly. You need to understand every feature, every user flow, every
technical requirement, and every implicit assumption.

### STEP 2: COMPLETENESS ANALYSIS

Check whether the spec covers all necessary aspects of a production application.

**User Flow Coverage:**
- Is there a complete registration/login/logout flow?
- Are all CRUD operations specified for every entity?
- Are edit/delete flows specified (not just create/view)?
- Are error states handled (invalid input, not found, server error)?
- Are empty states described (what does the user see with no data)?
- Is there a clear landing/home page flow?

**Authentication & Authorization:**
- Is auth required? If so, is the full auth flow specified?
- Are roles/permissions defined? Which pages require which roles?
- Is session management described (remember me, session timeout)?
- Is password reset/recovery specified?
- Are protected routes identified?

**Data Model:**
- Are all entities and their relationships clearly defined?
- Are required fields vs optional fields specified?
- Are data types clear (string, number, date, enum)?
- Are constraints specified (unique email, min/max length)?
- Are cascade behaviors defined (what happens when a parent is deleted)?

**Infrastructure:**
- Is the tech stack specified (frontend framework, backend, database)?
- Are deployment requirements mentioned?
- Are environment-specific configs needed (dev vs prod)?

**Missing Common Features:**
- Search/filter functionality for list views
- Pagination for large datasets
- Loading states and error boundaries
- Responsive design requirements
- Form validation rules

For each gap found, note:
- What is missing
- Why it matters (what breaks without it)
- Suggested addition (brief)

### STEP 3: CONTRADICTION DETECTION

Look for statements that conflict with each other:

- Feature A says X, but Feature B implies not-X
- A constraint in one section is violated by a requirement in another
- The data model implies a relationship that the UI flow contradicts
- Role permissions that conflict (e.g., "only admins can delete" vs "users can manage their own content")

For each contradiction found, note:
- The two conflicting statements (with quotes)
- Why they conflict
- Which one is likely intended (if determinable)

### STEP 4: COMPLEXITY ESTIMATION

Estimate the build scope:

| Tier | Feature Count | Estimated Build Time | Agent Sessions |
|------|--------------|---------------------|----------------|
| Simple | 50-100 features | ~1 day | 50-100 coding sessions |
| Medium | 100-200 features | ~2-3 days | 100-200 coding sessions |
| Large | 200-350 features | ~4-7 days | 200-350 coding sessions |
| Enterprise | 350+ features | ~1-2 weeks | 350+ coding sessions |

Count the distinct features, pages, entities, and API endpoints described in the
spec. Factor in complexity modifiers:
- Real-time features (+30% complexity)
- File upload/media (+20%)
- Complex permissions/roles (+25%)
- Third-party integrations (+15% per integration)
- Charts/data visualization (+20%)

### STEP 5: DEPENDENCY RISK ANALYSIS

Flag relationships that could cause build ordering issues:

- "Feature X requires Feature Y to exist, but Y is not in the spec"
- "Payment processing is mentioned but no pricing model is defined"
- "User accounts are assumed but no auth flow is specified"
- "File uploads are required but no storage strategy is defined"
- "Email notifications are mentioned but no email service is specified"
- "Admin panel requires user management that isn't fully specified"

### STEP 6: GENERATE REPORT

Create `spec-analysis.md` in the `.autoforge/` directory:

```markdown
# Spec Analysis Report
Generated: [date]

## Completeness Score: [1-5]/5

**1** = Critical gaps, should not proceed
**2** = Major gaps, significant rework risk
**3** = Moderate gaps, can proceed with caveats
**4** = Minor gaps, ready to build
**5** = Comprehensive, no issues found

## Summary
[2-3 sentence overview of spec quality]

## Completeness Gaps
| # | Category | Gap | Severity | Suggestion |
|---|----------|-----|----------|------------|
| 1 | Auth     | No password reset flow | HIGH | Add forgot-password feature |
| 2 | Data     | No cascade delete behavior | MEDIUM | Specify for each entity |

## Contradictions Found
| # | Statement A | Statement B | Resolution |
|---|-------------|-------------|------------|
| 1 | "Users have one profile" (Section 3) | "Switch profiles" (Section 7) | Clarify: single or multi-profile? |

## Complexity Estimate
- **Tier:** [Simple/Medium/Large/Enterprise]
- **Estimated Features:** [count]
- **Estimated Build Time:** [range]
- **Complexity Modifiers:** [list active modifiers]

## Dependency Risks
| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| 1 | Payments without pricing model | Cannot implement checkout | Define pricing tiers |

## Missing Infrastructure
- [ ] [Item 1]
- [ ] [Item 2]

## Recommendations
1. [Highest priority fix]
2. [Second priority]
3. [Third priority]

## Verdict
[PROCEED / REVISE SPEC FIRST / CRITICAL ISSUES - DO NOT BUILD]
```

Commit the report:
```bash
git add .autoforge/spec-analysis.md
git commit -m "Add spec analysis report - completeness score [X]/5"
```

### IMPORTANT
- Do NOT modify the app_spec.txt - you are an analyst, not an editor
- Do NOT create features - that is the initializer's job
- Do NOT write application code
- Your ONLY output is the spec-analysis.md report
- Be thorough but concise -- each finding should be actionable
```

#### 1.3 Client Configuration for Spec Analyzer

In `client.py`, add spec-analyzer agent type handling:

```python
SPEC_ANALYZER_TOOLS = [
    # No feature tools needed -- this agent only reads the spec and writes a report
]
```

The spec analyzer gets:
- Built-in tools: Read, Write, Edit, Bash, Grep, Glob (for reading the spec and writing the report)
- NO Feature MCP tools (not interacting with the feature database)
- NO Playwright MCP server (no browser needed)
- `max_turns`: 75 (limited scope -- read spec, analyze, write report)

```python
# In the feature_tools_map:
feature_tools_map = {
    "coding": CODING_AGENT_TOOLS,
    "testing": TESTING_AGENT_TOOLS,
    "initializer": INITIALIZER_AGENT_TOOLS,
    "spec-analyzer": SPEC_ANALYZER_TOOLS,
    "architect": ARCHITECT_TOOLS,  # See Feature 2
}

# In the max_turns_map:
max_turns_map = {
    "coding": 150,
    "testing": 75,
    "initializer": 200,
    "spec-analyzer": 75,
    "architect": 100,  # See Feature 2
}
```

Since the spec analyzer has no feature tools, it does not need the features MCP server. Add logic to skip starting the features MCP server when the agent type is `spec-analyzer`:

```python
# In create_client(), conditionally include MCP servers
mcp_servers = {}

# Only start features MCP server for agent types that need it
if agent_type not in ("spec-analyzer",):
    mcp_servers["features"] = {
        "command": sys.executable,
        "args": ["-m", "mcp_server.feature_mcp"],
        "env": {
            "PROJECT_DIR": str(project_dir.resolve()),
            "PYTHONPATH": str(Path(__file__).parent.resolve()),
        },
    }
```

#### 1.4 Orchestrator Integration

In `parallel_orchestrator.py`, add a spec analysis phase before initialization:

```python
async def _run_spec_analyzer(self) -> tuple[bool, int]:
    """Run spec analyzer agent as blocking subprocess.

    Returns:
        Tuple of (should_proceed, completeness_score).
        should_proceed is True if the score meets the threshold.
    """
    debug_log.section("SPEC ANALYSIS PHASE")
    debug_log.log("SPEC", "Starting spec analyzer subprocess",
        project_dir=str(self.project_dir))

    cmd = [
        sys.executable, "-u",
        str(AUTOFORGE_ROOT / "autonomous_agent_demo.py"),
        "--project-dir", str(self.project_dir),
        "--agent-type", "spec-analyzer",
        "--max-iterations", "1",
    ]
    if self.model:
        cmd.extend(["--model", self.model])

    print("Running spec analyzer agent...", flush=True)

    # ... subprocess management identical to _run_initializer() ...

    # After completion, parse the report for the completeness score
    report_path = self.project_dir / ".autoforge" / "spec-analysis.md"
    score = self._parse_completeness_score(report_path)

    return score >= self.min_spec_score, score

def _parse_completeness_score(self, report_path: Path) -> int:
    """Parse the completeness score from spec-analysis.md.

    Looks for the pattern '## Completeness Score: X/5' in the report.
    Returns 0 if the report doesn't exist or the pattern isn't found.
    """
    if not report_path.exists():
        return 0
    content = report_path.read_text(encoding="utf-8")
    match = re.search(r"Completeness Score:\s*(\d)/5", content)
    return int(match.group(1)) if match else 0
```

Integration into `run_loop()`:

```python
async def run_loop(self):
    # ... existing startup code ...

    # Phase 0: Spec analysis (if enabled and not already done)
    if self.run_spec_analyzer and not self._spec_analysis_done():
        print("=" * 70, flush=True)
        print("  SPEC ANALYSIS PHASE", flush=True)
        print("=" * 70, flush=True)

        should_proceed, score = await self._run_spec_analyzer()

        if not should_proceed:
            print(f"\nSpec completeness score: {score}/5 (below threshold {self.min_spec_score})")
            print("Recommendation: Revise the spec before building.")
            print("To override, use --skip-spec-analysis or lower --min-spec-score")
            if not self.force_build:
                return
            print("--force-build enabled, proceeding despite low score...")

        print(f"\nSpec analysis complete. Score: {score}/5")

    # Phase 0.5: Architecture planning (if enabled and not already done)
    # ... (See Feature 2) ...

    # Phase 1: Check if initialization needed (existing code)
    if not has_features(self.project_dir):
        # ... existing initialization code ...
```

New CLI flags:

```python
parser.add_argument(
    "--skip-spec-analysis",
    action="store_true",
    default=False,
    help="Skip the spec analysis phase",
)
parser.add_argument(
    "--min-spec-score",
    type=int,
    default=3,
    help="Minimum completeness score (1-5) to proceed with build (default: 3)",
)
parser.add_argument(
    "--force-build",
    action="store_true",
    default=False,
    help="Proceed with build even if spec score is below threshold",
)
```

New `__init__` parameters for `ParallelOrchestrator`:

```python
def __init__(
    self,
    # ... existing params ...
    run_spec_analyzer: bool = True,
    min_spec_score: int = 3,
    force_build: bool = False,
):
    # ... existing init ...
    self.run_spec_analyzer = run_spec_analyzer
    self.min_spec_score = min_spec_score
    self.force_build = force_build
```

Helper to check if analysis was already done:

```python
def _spec_analysis_done(self) -> bool:
    """Check if spec analysis has already been completed."""
    report = self.project_dir / ".autoforge" / "spec-analysis.md"
    return report.exists()
```

#### 1.5 Prompt Loading in prompts.py

Add a new prompt loader function:

```python
def get_spec_analyzer_prompt(project_dir: Path | None = None) -> str:
    """Load the spec analyzer prompt (project-specific if available)."""
    return load_prompt("spec_analyzer_prompt", project_dir)
```

#### 1.6 Agent Session Routing in agent.py

In `run_autonomous_agent()`, add routing for the new agent type:

```python
if agent_type == "spec-analyzer":
    prompt = get_spec_analyzer_prompt(project_dir)
    client = create_client(
        project_dir=project_dir,
        model=model,
        yolo_mode=True,  # No Playwright needed
        agent_type="spec-analyzer",
    )
    # Run single session -- spec analysis is always one pass
    await run_agent_session(client, prompt)
    return
```

#### 1.7 File Changes

| File | Change |
|---|---|
| `.claude/templates/spec_analyzer_prompt.template.md` | NEW -- spec analyzer agent prompt |
| `autonomous_agent_demo.py` | Add `spec-analyzer` and `architect` to agent-type choices |
| `client.py` | Add `SPEC_ANALYZER_TOOLS` (empty list), add to `feature_tools_map` and `max_turns_map`, conditionally skip features MCP server |
| `parallel_orchestrator.py` | Add `_run_spec_analyzer()`, `_parse_completeness_score()`, `_spec_analysis_done()`, new CLI flags (`--skip-spec-analysis`, `--min-spec-score`, `--force-build`), Phase 0 in `run_loop()` |
| `prompts.py` | Add `get_spec_analyzer_prompt()` function |
| `agent.py` | Add spec-analyzer routing in `run_autonomous_agent()` |
| `server/routers/settings.py` | Expose `run_spec_analyzer`, `min_spec_score` in settings API |
| `ui/src/components/SettingsModal.tsx` | Add spec analysis toggle and minimum score slider |

---

## Feature 2: Architecture Planner Agent

### What It Does

A new agent type (`architect`) that runs after spec analysis and before initialization. It reads the validated spec and produces a comprehensive `ARCHITECTURE.md` document that every subsequent agent references for consistent architectural decisions.

### The Problem It Solves

Today, each coding agent session makes independent decisions about:
- Database schema (table names, column types, relationships)
- API structure (endpoint paths, HTTP methods, request/response shapes)
- Component hierarchy (which components exist, where they live, how they compose)
- State management (context vs. stores vs. props, where state lives)
- File structure (directory layout, naming conventions)
- Auth strategy (JWT vs. session, middleware patterns)

This leads to inconsistency. Agent session 15 creates `/api/users` with camelCase responses, while agent session 30 creates `/api/v1/products` with snake_case. Agent session 20 puts all components in `src/components/`, while agent session 40 creates `src/features/auth/components/`. The coding agents waste turns re-discovering and reconciling these decisions.

With an `ARCHITECTURE.md` produced once by a dedicated architect agent, every coding agent starts with the same blueprint.

### Why It Is Cheap

The architect agent:
- Does NOT use Playwright (no browser needed -- pure design work)
- Does NOT implement code (design only, writes one document)
- Uses 50-80 turns (reads spec, designs architecture, writes document)
- Runs exactly once per project, before initialization
- On Max subscription: roughly 40% the rate limit impact of a coding agent

### Implementation

#### 2.1 New Agent Type: `architect`

Already added in Feature 1's agent-type choices update.

#### 2.2 Architect Prompt Template

Create `.claude/templates/architect_prompt.template.md`:

```markdown
## YOUR ROLE - ARCHITECTURE PLANNER AGENT

You are an **architecture planner agent** responsible for designing the technical
architecture of the application BEFORE any code is written. Your decisions will
guide every coding agent that follows, ensuring consistency across the entire build.

You are the chief architect. Every coding agent will reference your blueprint.

### STEP 1: READ THE SPEC AND ANALYSIS

Read the app specification and the spec analysis report:

```bash
cat app_spec.txt
cat .autoforge/spec-analysis.md
```

Understand:
- Every feature and user flow
- The tech stack requirements
- Any gaps or risks identified by the spec analyzer
- The complexity tier and scope

### STEP 2: DESIGN THE DATABASE SCHEMA

Define every table, column, type, and relationship:

```markdown
## Database Schema

### users
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | |
| email | TEXT | UNIQUE, NOT NULL | Used for login |
| password_hash | TEXT | NOT NULL | bcrypt hashed |
| name | TEXT | NOT NULL | Display name |
| role | TEXT | NOT NULL, DEFAULT 'user' | 'user' or 'admin' |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL | Updated on every write |

### posts
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | |
| user_id | INTEGER | FOREIGN KEY -> users.id, NOT NULL | CASCADE DELETE |
| title | TEXT | NOT NULL, max 200 chars | |
| content | TEXT | NOT NULL | Markdown supported |
| status | TEXT | NOT NULL, DEFAULT 'draft' | 'draft', 'published', 'archived' |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

### Indexes
- users: UNIQUE(email)
- posts: INDEX(user_id), INDEX(status), INDEX(created_at DESC)

### Relationships
- users 1:N posts (cascade delete)
- users 1:1 user_settings (cascade delete)
```

Design principles:
- Use the simplest type that works (TEXT over VARCHAR for SQLite)
- Every table has `id`, `created_at`
- Tables with mutable data have `updated_at`
- Define CASCADE behavior for every foreign key
- Add indexes for columns used in WHERE, ORDER BY, JOIN
- Use enums as TEXT with documented allowed values

### STEP 3: DESIGN THE API STRUCTURE

Define every endpoint, method, auth requirement, and shape:

```markdown
## API Structure

Base path: `/api`

### Authentication
| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| POST | /api/auth/register | None | { email, password, name } | { user, token } |
| POST | /api/auth/login | None | { email, password } | { user, token } |
| POST | /api/auth/logout | Required | - | { success } |
| GET | /api/auth/me | Required | - | { user } |

### Users
| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| GET | /api/users | Admin | ?page&limit&search | { users[], total, page } |
| GET | /api/users/:id | Required | - | { user } |
| PATCH | /api/users/:id | Owner/Admin | { name?, email? } | { user } |
| DELETE | /api/users/:id | Admin | - | { success } |

### Posts
| Method | Endpoint | Auth | Request | Response |
|--------|----------|------|---------|----------|
| GET | /api/posts | Optional | ?page&limit&status&author | { posts[], total } |
| POST | /api/posts | Required | { title, content, status? } | { post } |
| GET | /api/posts/:id | Optional | - | { post } |
| PATCH | /api/posts/:id | Owner/Admin | { title?, content?, status? } | { post } |
| DELETE | /api/posts/:id | Owner/Admin | - | { success } |
```

Design principles:
- RESTful conventions: plural nouns, HTTP verbs for actions
- Consistent response format: `{ data }` for single, `{ data[], total }` for lists
- ALL responses use camelCase JSON keys
- Pagination: `?page=1&limit=20` on all list endpoints
- Error format: `{ error: { code, message, details? } }`
- Status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Server Error)
- Auth strategy: JWT in Authorization header (Bearer token)

### STEP 4: MAP THE COMPONENT TREE

Define the page and component hierarchy:

```markdown
## Component Tree

### Pages (src/pages/)
- `HomePage.tsx` - Landing page, hero section, feature highlights
- `LoginPage.tsx` - Login form
- `RegisterPage.tsx` - Registration form
- `DashboardPage.tsx` - Main dashboard after login
- `PostListPage.tsx` - Browse all published posts
- `PostDetailPage.tsx` - Single post view
- `PostEditorPage.tsx` - Create/edit post (shared component)
- `ProfilePage.tsx` - User profile and settings
- `AdminUsersPage.tsx` - Admin user management
- `NotFoundPage.tsx` - 404 page

### Shared Components (src/components/)
- `layout/` - AppLayout, Navbar, Sidebar, Footer
- `ui/` - Button, Input, Select, Modal, Toast, Card, Badge, Spinner, EmptyState
- `forms/` - LoginForm, RegisterForm, PostForm, ProfileForm
- `data/` - DataTable, Pagination, SearchBar, FilterBar

### Component Patterns
- Pages fetch data, components render it (smart/dumb pattern)
- Forms use React Hook Form with Zod validation
- Data fetching via TanStack Query hooks in src/hooks/
- Error boundaries around each page
- Loading skeletons (not "Loading..." text) for async content
```

### STEP 5: DEFINE THE ROUTING MAP

```markdown
## Routing Map

| Path | Component | Auth | Layout |
|------|-----------|------|--------|
| / | HomePage | None | Public |
| /login | LoginPage | Guest only | Public |
| /register | RegisterPage | Guest only | Public |
| /dashboard | DashboardPage | Required | App |
| /posts | PostListPage | None | Public |
| /posts/:id | PostDetailPage | None | Public |
| /posts/new | PostEditorPage | Required | App |
| /posts/:id/edit | PostEditorPage | Owner | App |
| /profile | ProfilePage | Required | App |
| /admin/users | AdminUsersPage | Admin | App |
| * | NotFoundPage | None | Public |

### Layouts
- **PublicLayout**: Navbar + content (no sidebar)
- **AppLayout**: Navbar + Sidebar + content (authenticated users)

### Route Guards
- `RequireAuth` - Redirects to /login if not authenticated
- `RequireGuest` - Redirects to /dashboard if already authenticated
- `RequireAdmin` - Redirects to /dashboard if not admin role
```

### STEP 6: CHOOSE PATTERNS AND CONVENTIONS

```markdown
## Patterns and Conventions

### State Management
- Server state: TanStack Query (useQuery, useMutation)
- Auth state: React Context (AuthContext with useAuth hook)
- UI state: Component-local useState (no global UI state)
- Form state: React Hook Form

### File Structure
```
src/
  components/    # Reusable UI components
    layout/      # Layout components (Navbar, Sidebar, Footer)
    ui/          # Primitive UI components (Button, Input, Modal)
    forms/       # Form components
    data/        # Data display components (Table, List)
  pages/         # Route-level page components
  hooks/         # Custom React hooks (useAuth, usePosts, etc.)
  lib/           # Utilities (api client, validators, formatters)
  contexts/      # React contexts (AuthContext)
  types/         # TypeScript type definitions
```

### Naming Conventions
- Files: PascalCase for components (`UserCard.tsx`), camelCase for utilities (`formatDate.ts`)
- Components: PascalCase (`UserCard`, `PostList`)
- Hooks: camelCase with `use` prefix (`useAuth`, `usePosts`)
- API functions: camelCase with verb prefix (`getUsers`, `createPost`)
- Types/Interfaces: PascalCase with descriptive names (`User`, `CreatePostRequest`)
- CSS classes: Tailwind utility classes (no custom CSS files)
- Database tables: snake_case plural (`user_settings`)
- API endpoints: kebab-case plural (`/api/user-settings`)

### Error Handling
- API: try/catch with error response format `{ error: { code, message } }`
- React: Error boundaries per page, toast notifications for user-facing errors
- Forms: Inline validation errors below fields, server errors in toast
- Network: Retry logic via TanStack Query (3 retries with exponential backoff)

### Authentication Pattern
- JWT stored in httpOnly cookie (not localStorage)
- Auth context provides: user, login(), logout(), isAuthenticated, isAdmin
- Protected routes use RequireAuth wrapper component
- API client automatically includes auth token from cookie
- Token refresh handled by middleware (transparent to components)
```

### STEP 7: WRITE ARCHITECTURE.md

Compile all sections above into a single `ARCHITECTURE.md` file in the project root.

The document must be:
- Complete enough that a coding agent can implement any feature without guessing
- Consistent in naming, patterns, and conventions
- Specific about the tech stack choices (not vague "use a framework")
- Opinionated -- make decisions, don't list options

```bash
git add ARCHITECTURE.md
git commit -m "Add architecture blueprint - [tech stack] with [N] entities"
```

### IMPORTANT
- Do NOT implement any code -- you are designing, not building
- Do NOT create features -- that is the initializer's job
- Do NOT start the development server
- Your ONLY output is the ARCHITECTURE.md document
- Be opinionated: make specific decisions, don't say "you could use X or Y"
- Every decision must be justified by the spec requirements
```

#### 2.3 Client Configuration for Architect

In `client.py`, add architect agent type handling:

```python
ARCHITECT_TOOLS = [
    # No feature tools needed -- this agent only reads the spec and writes ARCHITECTURE.md
]
```

The architect gets:
- Built-in tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch
- NO Feature MCP tools
- NO Playwright MCP server
- `max_turns`: 100 (more than spec analyzer -- the architecture document is substantial)

The features MCP server should be skipped for architect agents as well:

```python
if agent_type not in ("spec-analyzer", "architect"):
    mcp_servers["features"] = { ... }
```

#### 2.4 Orchestrator Integration

Add an architecture planning phase after spec analysis and before initialization:

```python
async def _run_architect(self) -> bool:
    """Run architect agent as blocking subprocess.

    Returns True if architecture document was created.
    """
    debug_log.section("ARCHITECTURE PHASE")

    cmd = [
        sys.executable, "-u",
        str(AUTOFORGE_ROOT / "autonomous_agent_demo.py"),
        "--project-dir", str(self.project_dir),
        "--agent-type", "architect",
        "--max-iterations", "1",
    ]
    if self.model:
        cmd.extend(["--model", self.model])

    print("Running architect agent...", flush=True)

    # ... subprocess management identical to _run_initializer() ...

    # Verify output was created
    arch_path = self.project_dir / "ARCHITECTURE.md"
    if not arch_path.exists():
        print("WARNING: Architect did not produce ARCHITECTURE.md", flush=True)
        return False

    return True

def _architecture_done(self) -> bool:
    """Check if architecture planning has already been completed."""
    return (self.project_dir / "ARCHITECTURE.md").exists()
```

Integration into `run_loop()`:

```python
# Phase 0.5: Architecture planning (if enabled and not already done)
if self.run_architect and not self._architecture_done():
    print("=" * 70, flush=True)
    print("  ARCHITECTURE PLANNING PHASE", flush=True)
    print("=" * 70, flush=True)
    print("Designing application architecture...", flush=True)
    print("NOTE: This may take 5-10 minutes.", flush=True)

    success = await self._run_architect()

    if not success:
        print("WARNING: Architecture planning did not produce ARCHITECTURE.md")
        print("Proceeding with initialization (agents will make ad-hoc decisions)")
    else:
        print("Architecture planning complete. ARCHITECTURE.md committed.")
```

New CLI flags:

```python
parser.add_argument(
    "--skip-architect",
    action="store_true",
    default=False,
    help="Skip the architecture planning phase",
)
```

New `__init__` parameter:

```python
self.run_architect = not skip_architect  # True by default
```

#### 2.5 Coding Prompt Updated to Reference ARCHITECTURE.md

The coding prompt template needs a small addition to STEP 1 (Get Your Bearings) so every coding agent reads the architecture document:

Add after the existing step 5 (`git log --oneline -20`):

```markdown
# 6. Read architecture blueprint (if it exists)
if [ -f ARCHITECTURE.md ]; then cat ARCHITECTURE.md; fi
```

And add a new guidance section after STEP 1:

```markdown
### ARCHITECTURE REFERENCE (MANDATORY)

If `ARCHITECTURE.md` exists in the project root, you MUST follow it for ALL
architectural decisions including:
- Database table names, column names, and types
- API endpoint paths, methods, and response formats
- Component names, locations, and patterns
- File structure and naming conventions
- State management approach
- Auth strategy and patterns

**DO NOT deviate from ARCHITECTURE.md.** If you think the architecture is wrong
for your feature, implement it as specified anyway and note your concern in
`claude-progress.txt`. Consistency across all agents is more important than
any single agent's opinion about the "right" way to do something.
```

#### 2.6 Initializer Prompt Updated to Reference ARCHITECTURE.md

Add to the initializer prompt, before the "Create Features" task:

```markdown
### READ ARCHITECTURE BLUEPRINT (if it exists)

If `ARCHITECTURE.md` exists in the project root, read it before creating features.
Use the architecture document to:
- Name features consistently with the defined component names and routes
- Ensure feature descriptions reference the correct API endpoints
- Order features according to the architectural dependencies
- Include features for every entity, endpoint, and component defined in the architecture
```

#### 2.7 File Changes

| File | Change |
|---|---|
| `.claude/templates/architect_prompt.template.md` | NEW -- architect agent prompt |
| `autonomous_agent_demo.py` | `architect` already added in Feature 1's agent-type update |
| `client.py` | Add `ARCHITECT_TOOLS` (empty list), add to `feature_tools_map` and `max_turns_map`, skip features MCP server for architect |
| `parallel_orchestrator.py` | Add `_run_architect()`, `_architecture_done()`, new CLI flag (`--skip-architect`), Phase 0.5 in `run_loop()` |
| `prompts.py` | Add `get_architect_prompt()` function |
| `agent.py` | Add architect routing in `run_autonomous_agent()` |
| `.claude/templates/coding_prompt.template.md` | Add ARCHITECTURE.md reading in STEP 1, add ARCHITECTURE REFERENCE section |
| `.claude/templates/initializer_prompt.template.md` | Add ARCHITECTURE.md reading instruction before feature creation |
| `server/routers/settings.py` | Expose `run_architect` toggle in settings API |
| `ui/src/components/SettingsModal.tsx` | Add architecture planning toggle |

---

## Feature 3: Dependency Auto-Detection

### What It Does

An enhancement to the existing initializer agent. After creating all features (the current behavior), the initializer performs a second pass that analyzes feature relationships and automatically calls `feature_add_dependency` and `feature_set_dependencies` to build the dependency graph.

### The Problem It Solves

Currently, the initializer prompt instructs the agent to specify `depends_on_indices` in the `feature_create_bulk` call. This works but has limitations:
1. The initializer must reason about dependencies while simultaneously designing features -- two complex tasks competing for attention
2. Index-based references are fragile -- if the agent reorders features, the indices break
3. The initializer often misses non-obvious dependencies (e.g., "filter by category" depends on "categories CRUD")
4. For large specs (200+ features), the initializer's context budget is mostly consumed by feature creation, leaving little room for dependency analysis

By splitting dependency detection into an explicit second pass, we:
- Let the initializer focus on feature quality during creation
- Apply dedicated analysis to dependencies after all features exist
- Use the feature names and descriptions (not indices) for more accurate detection
- Leverage the existing cycle detection in `dependency_resolver.py` as a safety net

### Implementation

#### 3.1 Initializer Prompt Enhancement

Add a new phase to `.claude/templates/initializer_prompt.template.md` after the feature creation task:

```markdown
### FIFTH TASK: Dependency Auto-Detection (Second Pass)

Now that all features have been created, perform a dependency analysis pass.
For each feature, determine which other features must be completed first.

**Step 1: Retrieve all features**

```
Use the feature_get_stats tool to confirm all features were created.
```

**Step 2: Analyze dependencies for each feature**

For each feature (starting from index 5 -- indices 0-4 are infrastructure and have
no dependencies):

1. Read the feature name and description
2. Identify which other features must exist before this one can be implemented
3. Use `feature_set_dependencies` to set ALL dependencies for the feature at once

**Dependency Detection Heuristics:**

Apply these rules to determine dependencies:

| Pattern | Dependency |
|---------|-----------|
| "Edit [entity]" or "Update [entity]" | Depends on "Create [entity]" |
| "Delete [entity]" | Depends on "Create [entity]" |
| "View [entity] list" | Depends on "Create [entity]" |
| "Filter [entity]" or "Search [entity]" | Depends on "View [entity] list" |
| "Sort [entity]" | Depends on "View [entity] list" |
| "[Entity] pagination" | Depends on "View [entity] list" |
| Any page requiring login | Depends on "User can log in" |
| "Profile page" or "Settings page" | Depends on "User can log in" |
| "Admin [anything]" | Depends on "User can log in" + "Admin role exists" |
| "Dashboard" | Depends on "User can log in" + relevant data features |
| "Export [entity]" | Depends on "View [entity] list" |
| "Import [entity]" | Depends on "Create [entity]" |
| "Notification for [action]" | Depends on the [action] feature |
| "Modal for [action]" | Depends on the page containing the modal |
| Style/UI tests | Depend on the functional feature they style |

**Dependency Principles:**

1. **ALL features after index 4 MUST depend on [0, 1, 2, 3, 4]** (infrastructure)
2. **Wide graphs, not chains**: If features A, B, C all depend on D, they should each
   depend directly on D -- not A -> B -> C -> D
3. **Maximum 20 dependencies per feature**: If a feature seems to need more than 20
   dependencies, it probably only needs the direct ones (not transitive)
4. **No circular dependencies**: The `feature_set_dependencies` tool will reject cycles
5. **Independent features should have NO shared dependencies beyond infrastructure**:
   e.g., "User can create post" and "Admin can manage users" only share infrastructure deps

**Step 3: Validate the graph**

After setting all dependencies:
```
Use the feature_get_stats tool to confirm no features are in an error state.
```

If any dependency was rejected due to a cycle, review the conflicting features
and adjust. Cycles usually indicate a feature should be split into two parts.

**Step 4: Log the dependency graph**

Print a summary of the dependency structure for debugging:
- How many features have 0 non-infrastructure dependencies (leaf features)
- How many features have 1-3 dependencies (typical)
- How many features have 4+ dependencies (complex integration points)
- Maximum dependency depth (longest chain from infrastructure to leaf)

**IMPORTANT:**
- Use `feature_set_dependencies` (not `feature_add_dependency`) to set all deps at once
- This is more efficient and atomic than adding one at a time
- Only set dependencies for features at index 5+ (infrastructure features have none)
- The cycle detection in the MCP server will reject invalid dependencies automatically
```

#### 3.2 No New Agent Type Needed

This is an enhancement to the existing initializer agent, not a new agent type. The initializer already has access to all the necessary MCP tools:
- `feature_get_stats` -- to verify features were created
- `feature_set_dependencies` -- to set dependencies in bulk
- `feature_add_dependency` -- for individual additions if needed

The initializer's turn budget is 200, which is sufficient for feature creation (100-140 turns) plus dependency detection (40-60 turns).

#### 3.3 Leveraging Existing Infrastructure

The dependency auto-detection leverages infrastructure that already exists in the codebase:

**Cycle Detection** (`api/dependency_resolver.py`):
- `would_create_circular_dependency()` -- called by `feature_add_dependency` and `feature_set_dependencies` MCP tools
- Uses DFS traversal to detect cycles before they are committed
- Returns an error message if a cycle would be created, allowing the agent to adjust

**Kahn's Algorithm** (`api/dependency_resolver.py`):
- `resolve_dependencies()` -- topological sort with priority-aware ordering
- Already used by the orchestrator to determine feature execution order
- Will automatically respect the new auto-detected dependencies

**Scheduling Scores** (`api/dependency_resolver.py`):
- `compute_scheduling_scores()` -- BFS + reverse topo sort for priority scoring
- Features with more dependents get higher scheduling priority
- The auto-detected dependencies will improve scheduling accuracy

**Existing MCP Tools** (`mcp_server/feature_mcp.py`):
- `feature_set_dependencies` -- sets all dependencies for a feature at once with validation
- `feature_add_dependency` -- adds a single dependency with cycle detection
- Both enforce `MAX_DEPENDENCIES_PER_FEATURE = 20` limit

#### 3.4 Dependency Visualization in UI

The existing `DependencyGraph.tsx` component already visualizes dependencies using dagre layout. Auto-detected dependencies will automatically appear in this visualization with no UI changes needed. The graph component reads from the same feature database that the MCP tools write to.

However, consider adding a visual indicator for auto-detected vs. manual dependencies:

```python
# In the Feature model (api/database.py), add an optional metadata field:
# This is a FUTURE enhancement, not required for the initial implementation.
# dependency_metadata = Column(JSON, default=dict)  # { "source": "auto" | "manual" }
```

#### 3.5 File Changes

| File | Change |
|---|---|
| `.claude/templates/initializer_prompt.template.md` | Add FIFTH TASK: Dependency Auto-Detection (second pass after feature creation) |

That's it. The beauty of this feature is that it leverages entirely existing infrastructure. No new Python code, no new MCP tools, no database changes. It is purely a prompt enhancement that instructs the initializer to use tools it already has access to.

---

## Implementation Priority

Build these in order:

1. **Feature 3: Dependency Auto-Detection** -- Prompt change only, zero code changes, immediate impact. Every project gets better dependency graphs starting with the next initializer run. This is the highest ROI change in this document.

2. **Feature 2: Architecture Planner Agent** -- Moderate effort (new prompt template + orchestrator phase). The architecture document has an outsized impact on build quality because it eliminates the most common source of inconsistency. Should be implemented before Feature 1 because the architect benefits from reading the spec directly, even without formal analysis.

3. **Feature 1: Smart Spec Analyzer Agent** -- Moderate effort (new prompt template + orchestrator phase + score parsing). Valuable for catching spec issues early, but less urgent than the architecture planner because spec issues can also be caught during the spec creation chat session (`server/services/spec_chat_session.py`).

### Suggested Implementation Order Within Each Feature

**Feature 3 (Dependency Auto-Detection):**
1. Update `initializer_prompt.template.md` with the second pass instructions
2. Test with a sample project to verify dependency detection quality
3. Verify cycle detection catches any issues

**Feature 2 (Architecture Planner):**
1. Create `architect_prompt.template.md`
2. Add `get_architect_prompt()` to `prompts.py`
3. Add architect routing in `agent.py`
4. Add `ARCHITECT_TOOLS` and config to `client.py`
5. Add `_run_architect()` and orchestrator phase to `parallel_orchestrator.py`
6. Update `coding_prompt.template.md` to reference ARCHITECTURE.md
7. Update `initializer_prompt.template.md` to reference ARCHITECTURE.md
8. Add `--skip-architect` CLI flag
9. Add settings UI toggle

**Feature 1 (Spec Analyzer):**
1. Create `spec_analyzer_prompt.template.md`
2. Add `get_spec_analyzer_prompt()` to `prompts.py`
3. Add spec-analyzer routing in `agent.py`
4. Add `SPEC_ANALYZER_TOOLS` and config to `client.py`
5. Add `_run_spec_analyzer()` and orchestrator phase to `parallel_orchestrator.py`
6. Add score parsing logic
7. Add CLI flags (`--skip-spec-analysis`, `--min-spec-score`, `--force-build`)
8. Add settings UI toggle and score slider

---

## Cost Analysis (Max Subscription)

All agents run through Claude Code under the Max subscription. There is zero additional API cost. The "cost" is rate limit usage.

### Per-Project Cost of Pre-Build Intelligence

| Phase | Agent Type | Turns | Playwright | Rate Limit Impact |
|---|---|---|---|---|
| Spec Analysis | spec-analyzer | 30-50 | No | Light |
| Architecture Planning | architect | 50-80 | No | Light-Medium |
| Dependency Detection | initializer (enhanced) | +40-60 turns | No | Light |
| **Total Pre-Build Overhead** | | **120-190 turns** | | **Light-Medium** |

### Comparison: With vs. Without Pre-Build Intelligence

For a typical project with 200 features:

**Without Pre-Build Intelligence:**
- 200 coding sessions x 120 turns avg = ~24,000 turns
- ~10% sessions wasted on inconsistency fixes = ~2,400 turns wasted
- ~5% sessions wasted on missing spec issues = ~1,200 turns wasted
- ~8% sessions with ordering issues (wrong dependencies) = ~1,920 turns wasted
- **Effective turns: ~29,520 total (5,520 wasted)**

**With Pre-Build Intelligence:**
- 1 spec analysis session = ~40 turns
- 1 architecture session = ~65 turns
- Enhanced initializer = ~60 extra turns
- 200 coding sessions x 110 turns avg (fewer reruns, consistent architecture) = ~22,000 turns
- ~3% sessions wasted on inconsistency = ~660 turns wasted
- ~1% sessions wasted on spec issues = ~220 turns wasted
- ~2% sessions with ordering issues = ~440 turns wasted
- **Effective turns: ~23,485 total (1,320 wasted)**

**Net savings: ~6,035 turns (~20% reduction)** for a one-time investment of ~165 turns.

The pre-build phase pays for itself after the first 10 coding sessions, because every subsequent session benefits from:
- Consistent architecture (fewer "fix inconsistency" sessions)
- Better dependency ordering (fewer "blocked" sessions)
- Cleaner spec (fewer "what does this mean?" sessions)

---

## UI Integration

### Spec Analysis Report Viewer

When the spec analyzer produces `.autoforge/spec-analysis.md`, show it in the UI:
- New section in the project dashboard: "Spec Analysis" (collapsed by default)
- Show the completeness score as a colored badge (1-2: red, 3: yellow, 4-5: green)
- Render the markdown report with collapsible sections
- If score < threshold, show a warning banner: "Spec needs revision before building"

### Architecture Document Viewer

When the architect produces `ARCHITECTURE.md`, show it in the UI:
- New tab in the project view: "Architecture"
- Render the markdown with syntax highlighting for code blocks
- Searchable (developers can quickly find the schema for a specific entity)

### Pipeline Status Indicator

Add a visual indicator showing which pre-build phases have been completed:

```
[x] Spec Analysis (Score: 4/5)    [x] Architecture    [x] Initialization    [ ] Building...
```

This could be shown as a horizontal stepper/progress bar at the top of the project dashboard.

### Settings Panel Additions

Add to the Settings modal:
- **Spec Analysis** toggle (enable/disable, default: enabled)
- **Minimum Spec Score** slider (1-5, default: 3)
- **Architecture Planning** toggle (enable/disable, default: enabled)
- **Force Build** checkbox (proceed despite low spec score, default: off)

### File Changes for UI

| File | Change |
|---|---|
| `ui/src/lib/types.ts` | Add `specAnalysisScore`, `hasArchitecture` fields to project status |
| `ui/src/components/SettingsModal.tsx` | Add pre-build intelligence settings |
| `ui/src/App.tsx` | Add pipeline status indicator, spec/architecture viewers |
| `server/routers/projects.py` | Return spec analysis score and architecture status in project data |
| `server/routers/settings.py` | Expose new settings |

---

## Complete File Changes Summary

### New Files

| File | Description |
|---|---|
| `.claude/templates/spec_analyzer_prompt.template.md` | Spec analyzer agent prompt |
| `.claude/templates/architect_prompt.template.md` | Architecture planner agent prompt |

### Modified Files

| File | Changes |
|---|---|
| `autonomous_agent_demo.py` | Add `spec-analyzer` and `architect` to `--agent-type` choices |
| `client.py` | Add `SPEC_ANALYZER_TOOLS`, `ARCHITECT_TOOLS`, update `feature_tools_map`, `max_turns_map`, conditionally skip features MCP server for non-feature agents |
| `parallel_orchestrator.py` | Add `_run_spec_analyzer()`, `_run_architect()`, `_parse_completeness_score()`, `_spec_analysis_done()`, `_architecture_done()`, Phase 0 + Phase 0.5 in `run_loop()`, new CLI flags, new `__init__` params |
| `prompts.py` | Add `get_spec_analyzer_prompt()`, `get_architect_prompt()` |
| `agent.py` | Add spec-analyzer and architect routing in `run_autonomous_agent()` |
| `.claude/templates/coding_prompt.template.md` | Add ARCHITECTURE.md reading in STEP 1, add ARCHITECTURE REFERENCE section |
| `.claude/templates/initializer_prompt.template.md` | Add ARCHITECTURE.md reading, add FIFTH TASK (dependency auto-detection second pass) |
| `server/routers/settings.py` | Expose pre-build intelligence settings |
| `server/routers/projects.py` | Return spec analysis score and architecture status |
| `ui/src/lib/types.ts` | Add pre-build status fields |
| `ui/src/components/SettingsModal.tsx` | Add pre-build intelligence toggles and sliders |
| `ui/src/App.tsx` | Add pipeline status indicator |

---

## Notes for Implementation

- All agents run through Claude Code under Max subscription -- zero additional API cost
- The spec analyzer and architect are the two cheapest agent types (no Playwright, no feature database interaction)
- Both pre-build phases are idempotent -- if `spec-analysis.md` or `ARCHITECTURE.md` already exists, the phase is skipped
- The `--skip-spec-analysis` and `--skip-architect` flags provide escape hatches for fast iteration
- The `--force-build` flag allows proceeding despite a low spec score (useful for prototyping)
- Feature 3 (dependency auto-detection) requires ZERO code changes -- it is purely a prompt enhancement
- The dependency auto-detection leverages existing cycle detection, so invalid dependencies are caught automatically
- Consider caching the spec analysis score in the project config so the UI can display it without re-parsing the markdown file
- The architecture document should be treated as read-only by coding agents -- if they find issues, they document them in `claude-progress.txt` rather than modifying the architecture
- For YOLO mode, spec analysis and architecture planning should still run (they are cheap and valuable even without testing)
