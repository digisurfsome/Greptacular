# Build Orchestrator — Full Product Spec (Deluxe Multi-Page Version)

This is the consolidated master spec covering the complete Build Orchestrator product. It merges the one-pager (MVP), the CLI workspace integration (PRD 11), and the SaaS product vision (PRD 10) into one document. Hand this to an agent to generate detailed per-page PRDs.

---

## PRODUCT OVERVIEW

### What It Is
A multi-page dashboard inside AutoForge that lets users visually configure, orchestrate, and automate AI-powered app builds. Users fill in forms, pick from dropdowns, save reusable templates, and the system generates phase-separated bash scripts with Claude CLI calls — then optionally runs them end to end with wave-based orchestration, quality gates, and real-time monitoring.

### Two Product Tiers (Same Codebase)

| Tier | Name | What It Does |
|------|------|-------------|
| **Entry** | Build Planner (One-Pager) | Single page: instruction blocks + PRD → phase scripts. Local only. |
| **Deluxe** | Build Orchestrator | Multi-page: PRD decomposition, role configs, wave orchestration, prompt library, templates, live execution dashboard. Full automation. |

The one-pager is Phase 1 of building the deluxe. Every feature in the one-pager carries forward — the deluxe just adds dedicated pages for things that were collapsed sections on the one-pager.

### The Core Innovation
**Instruction blocks** — reusable, phase-scoped text blocks that separate "how you build" from "what you're building." Blocks can be:
- **Phase 1 Only** — setup rules, project scaffolding instructions
- **Phase 2+ Only** — ongoing rules, testing contracts, component patterns
- **All Phases** — universal standards like tech stack, coding conventions

Blocks persist across projects (saved as templates), can be reordered, toggled, and upgraded independently. When a YouTube creator drops a new technique, you add one block — you don't rewrite your entire prompt.

---

## TARGET USERS

### Primary: Vibe Coders
Non-technical users who build apps by describing what they want to AI. They watch YouTube tutorials, collect prompting techniques, and use Claude Code via subscription. They are NOT developers — every option needs a tooltip explaining what it does in plain language.

### Secondary: Power Users
Developers who already have Claude Code CLI set up. They understand agents, commands, and hooks. They want organizational power of multi-agent orchestration without manually writing dozens of markdown files and YAML configs.

### Tertiary: SaaS Users (Future)
Non-technical users who will never use a terminal. They get the web-only version (generates copy-paste prompts for any AI tool). This is the standalone SaaS product — same decomposition engine, different output format.

---

## BUSINESS MODEL

### Funnel Strategy
1. **Free content** (YouTube series, 12+ videos from existing documentation) → builds email list
2. **Entry product** (Build Planner one-pager) → free inside AutoForge
3. **Deluxe product** (Build Orchestrator multi-page) → AutoForge feature
4. **SaaS product** (web-only, no CLI required) → standalone paid product
5. **PRD Maker addon** → rough idea → structured PRD (upstream product)
6. **Template/Prompt Pack marketplace** → recurring value

### YouTube Content Map (12+ videos)
- "How I Build Apps 10x Faster With AI Agents"
- "Why Your AI Keeps Forgetting (And How To Fix It)"
- "Build Any App With AI — The Simple Way"
- "Turn One AI Into a Dev Team (Wave Method)"
- "The Prompt Template That Changed Everything"
- "8 Mistakes Killing Your AI Builds"
- "The One Document Every AI Build Needs"
- "How to Stop AI From Guessing Your Architecture"
- "Why Your AI Makes The Wrong App (Bad PRDs)"
- "How to Run 8 AI Agents at Once"
- "Which AI Build Method Is Right For You?"
- "Build Your First AI App in 15 Minutes"

### Flywheel
Owner curates best YouTube creator techniques → becomes the template library → creators adopt the platform → more techniques flow in → library grows → more users.

---

## PAGES & FEATURES

### Page 1: Build Planner (The One-Pager Entry Point)

**Route:** `#/build-planner`

This is the MVP single-page experience. Everything on one scrollable page. Six sections top to bottom:

**Section 1 — Live Dashboard Strip**
- Sticky bar at top, only visible when a build is running
- Shows: project name, current phase ("Phase 2 of 5"), tokens consumed, estimated tokens remaining
- Progress bar + Stop button

**Section 2 — Project Header Bar**
- Project name input, status badge (Draft|Ready|Queued|Running|Complete)
- Save/Load/New Project buttons
- Template controls: Save as Template, Load Template dropdown
- Templates save instruction blocks only (not PRD)

**Section 3 — Instruction Blocks (Core Innovation)**
- Vertical stack of text boxes, each with:
  - Phase toggle pills: "Phase 1 Only" | "Phase 2+ Only" | "All Phases"
  - Auto-expanding text area for instruction content
  - Label field (e.g., "Tech Stack Rules", "Testing Contract")
  - Drag handle for reordering
  - Delete button (with confirmation)
  - Collapse/expand toggle
- "+ Add Block" button at bottom
- Order = injection order in generated scripts
- Pre-populated starters: "Tech Stack" (All), "Project Setup" (Phase 1), "Testing Script" (Phase 2+)

**Section 4 — PRD Section**
- Large text area for full PRD
- Live token counter (estimates as you type)
- "Break into Phases" button → sends to AI, returns suggested phase breakdown
- Phase breakdown display: numbered list with summary, features, estimated tokens per phase
- User can edit/merge/split/reorder phases
- Manual override: force number of phases (2-8)

**Section 5 — CLI Configuration Panel**
- Collapsible "Build Settings" section
- Every option has a tooltip with plain-language explanation
- Sensible defaults so user can skip entirely

| Category | Options |
|----------|---------|
| **Model & Session** | Model (Opus/Sonnet/Haiku), Max turns (5/10/25/50/Unlimited), Auto-continue (Yes/No/Pause) |
| **Build Behavior** | YOLO mode toggle, Batch size (1-3), Parallel agents (1-5), Git commit frequency, Error handling (Stop/Skip/Retry) |
| **Testing** | Testing approach (Full/Lint-only/YOLO), Test framework (Auto-detect/Jest/Vitest/Pytest/Playwright), Test frequency, Custom test script |
| **Environment** | File access scope, Extra read paths, Network access (Localhost/External), Deployment target |

**Section 6 — Output & Actions**
- Preview Scripts button → modal with syntax-highlighted bash
- Script summary: count, total tokens, estimated cost
- Generate Scripts → creates phase .sh files + run_all.sh
- Generate & Run → generates + starts Phase 1 immediately
- Save Project, Add to Queue
- Queue Manager panel (list, reorder, run next/all)
- Saved Projects panel (list, filter by status, load/delete)

---

### Page 2: PRD Decomposition Engine

**Route:** `#/build-orchestrator/decompose`

Dedicated page for the AI-powered PRD analysis that was a button on the one-pager. Expanded with full visualization.

**Features:**
- PRD input (paste, upload file, or generate with PRD Maker)
- AI decomposition: PRD → features + dependencies + waves + token budgets
- Feature list with: name, description, size (S/M/L), estimated tokens
- Interactive dependency graph (extends existing DependencyGraph.tsx with dagre layout)
- Wave plan: features grouped into sequential waves with parallel groups
- Token budget table: per-agent usage vs available context
- File ownership map: which files each agent creates or modifies
- Conflict risk matrix: files touched by multiple agents in the same wave

**Shared Engine:**
The decomposition engine is shared between CLI and SaaS modes:
- `cli` mode: assumes CLAUDE.md provides shared context, agents read files directly, accounts for MCP overhead
- `web` mode: assumes foundation docs pasted into each prompt, generates monolithic prompts

**Engine Interface:**
```python
class DecompositionEngine:
    def decompose(
        self,
        prd_text: str,
        context_window: int = 200_000,
        max_parallel_agents: int = 3,
        mode: Literal["web", "cli"] = "cli"
    ) -> DecompositionResult:
        # Returns: features, dependencies, waves, token_budgets, file_map, conflicts
```

---

### Page 3: Role Configuration Dashboard

**Route:** `#/build-orchestrator/roles`

Visual interface for defining and customizing agent roles. Each role becomes a `.claude/agents/*.md` file.

**Pre-built Roles (ship with product):**

| Role | Model | Purpose |
|------|-------|---------|
| Orchestrator | Opus | Manages build, spawns sub-agents, does not write code |
| Architect | Opus | Designs interfaces, file structure, data models. Output only. |
| Builder | Sonnet | Implements features following architect's blueprint |
| QA | Sonnet | Tests features, breaks things, reports bugs |
| Reviewer | Opus | Code review, security audit, performance analysis |
| Doc Writer | Sonnet | Reads code, writes user-facing documentation |
| Fixer | Sonnet | Takes QA reports, fixes bugs, re-runs tests |
| Integrator | Opus | Merges wave outputs, resolves conflicts, verifies combined build |

**Role Card UI:**
- Name and filename
- Role prompt (markdown editor with preview)
- Model dropdown (Opus/Sonnet/Haiku)
- File/directory scope whitelist
- Restrictions (what this role cannot do)
- Quality gates (lint/build/test/custom)
- Prompt source: Custom or from Prompt Library
- Actions: Load from Library, Save to Library, Duplicate, Import/Export as .md

**Generated Output:**
Each role → `.claude/agents/{name}.md` with YAML frontmatter (name, model, description) + role prompt content.

---

### Page 4: Wave Orchestration Dashboard

**Route:** `#/build-orchestrator/waves`

Visual interface for organizing features into waves, setting parallel groups, defining quality gates, and automating transitions.

**Wave View UI:**
- Horizontal lanes, one per wave
- Feature cards draggable between lanes
- Parallel groups within lanes (simultaneous execution)
- Dependency arrows between features across waves
- Quality gate indicators between waves (pass/fail/pending)

**Per-Wave Configuration:**
- Agent assignments (which roles handle which features)
- Parallelism (1-5 simultaneous agents)
- Quality gates: Lint, Build, Test, Manual review, Custom command
- Transition behavior: Auto-start | Notify and wait | Run integrator first
- Failure behavior: Spawn fixer | Retry wave | Stop and alert | Rollback (with confirmation)

**Generated Output:**
- `.autoforge/hooks/wave-transition.yaml` — quality gate definitions and transition rules
- `.claude/commands/build-feature.md` — architect → builder → QA chain
- `.claude/commands/full-build.md` — execute all waves with gates

---

### Page 5: Prompt Library

**Route:** `#/build-orchestrator/library`

Central library for storing, organizing, tagging, and reusing prompts across projects. Single unified library — tags handle organization.

**Library Item Fields:**
- Name, Content (markdown), Tags, Description, Created/Updated, Usage count, Source (Built-in/User/Imported)

**Tag System:**
- Pre-built categories: `role:*`, `hook:*`, `pattern:*`, `stack:*`, `feature:*`
- Users can create custom tags (freeform `category:value` convention)

**Library UI:**
- List view (sortable by name, date, usage count)
- Multi-select tag filter
- Full-text search across name, description, content
- Preview panel (click prompt → see full content)
- Actions: Edit, Duplicate, Delete, Export, "Use in Project"

**Integration Points:**
- Role Configuration: "Load from Library" on each role card
- Wave Configuration: "Load hook prompt from Library"
- Templates reference library items by ID (updates propagate)

**Import/Export:**
- Individual prompts as .md files
- Filtered set as .zip
- Import .md files into library
- Future: shared team library / prompt packs

---

### Page 6: Template System

**Route:** `#/build-orchestrator/templates`

Save entire project configurations as named templates. Load to instantly set up new projects.

**Template Contents:**
- Project metadata (name pattern, description, tech stack)
- Role configurations (which roles, prompts, models)
- Wave plan (wave count, feature assignments, parallel groups)
- Quality gate configurations
- Hook configurations
- Prompt library references (by ID, so library updates propagate)

**Pre-built Templates:**

| Template | Use Case | Roles | Waves |
|----------|----------|-------|-------|
| Quick Build | Small apps (3-5 features) | Builder + QA | 2 |
| Standard Build | Medium apps (5-10 features) | Architect + Builder + QA | 3 |
| Enterprise Build | Large apps (10+ features) | All 8 roles | 4+ |
| Clean Room | Rebuild from spec, no old code reference | Architect + Builder + Reviewer + QA | 3 (strict gates) |
| TDD Build | Test-first development | Architect + QA (tests) + Builder (pass tests) | 3 |
| Security Audit | Security-focused with audit gates | Builder + Reviewer + QA | 3 (security gates) |
| Rapid Prototype | YOLO fast build | Builder only | 1 (lint-only gate) |

**Template UI:**
- Grid of template cards (name, description, role count, wave count)
- Detail view (full configuration preview)
- "Use Template" → creates pre-filled project
- "Save as Template" → saves current project config
- Import/Export as JSON

---

### Page 7: Build Execution Dashboard

**Route:** `#/build-orchestrator/run/{project_id}`

Real-time monitoring of a running build. Replaces the Live Dashboard Strip from the one-pager with a full page.

**Runtime View:**
- Wave progress bar (which wave is active/done/pending)
- Agent cards: role, assigned features, status (thinking/building/testing/done/error), live log output
- Quality gate status (pass/fail per gate between waves)
- Interactive dependency graph (nodes colored by status)
- Build timeline (horizontal, showing wave transitions, gate checks, agent activity)
- Token consumption tracking

**Execution Flow:**
1. Generate `.claude/` files from dashboard configuration
2. Wave 1: Spawn parallel agents → monitor → wait for completion → run quality gates
3. Merge point: optional integrator agent → verify combined build → git checkpoint
4. Wave 2-N: same pattern
5. QA Wave: verification agents → collect reports → spawn fixers if needed → final report

**Controls:**
- Pause/Resume/Cancel build
- View per-agent logs
- Manual gate override (force pass/fail)
- Re-run failed wave

**WebSocket Events:**
`wave_start`, `wave_progress`, `gate_start`, `gate_result`, `wave_complete`, `merge_start`, `merge_complete`, `build_complete`

**Progress Persistence:**
Build state saved to database — dashboard reconnects after browser refresh without losing state. Git checkpoint commits at each merge point.

---

### Page 8: Project Management

**Route:** `#/build-orchestrator/projects`

Central hub for all build projects with full lifecycle management.

**Project List View:**
- Card grid: name, status badge, last built date, feature count, completion %
- Statuses: Draft | Ready | Building | Complete | Failed
- Quick actions: Open, Duplicate, Delete, Export

**Project Detail View (tabs):**
- **PRD tab** — source PRD + decomposition results
- **Configuration tab** — roles, waves, hooks, gates (the full dashboard)
- **Build History tab** — past executions with expandable details (agent logs, gate results, duration)
- **Generated Files tab** — preview of all `.claude/` files generated

---

### Page 9: PRD Maker (Addon/Future)

**Route:** `#/build-orchestrator/prd-maker`

Takes a rough app idea and generates a structured, detailed PRD. This is the upstream product that makes everything else work better.

**Input Options:**
- Free text description ("I want an app that...")
- Bullet point feature list
- Existing code (reverse-engineering mode — drop in code, get rebuild PRD)
- Voice memo transcript

**Output:**
- Structured PRD: overview, user stories, technical spec, API endpoints, database schema, UI components, edge cases, acceptance criteria
- Feature dependency graph
- Suggested tech stack
- Token budget estimates per feature

**Generation Flow:**
- Multi-step: structure → detail → edge cases (user reviews between steps)
- "Go Deeper" button on any section
- "Send to Orchestrator" button → creates new project with PRD pre-filled

**Reverse-Engineering Mode:**
- Upload/paste code from existing app
- AI analyzes structure, identifies features, maps architecture
- Generates PRD for what the app SHOULD be (cleaned up, properly structured)
- Generates foundation documents for rebuild

---

## TECHNICAL ARCHITECTURE

### Tech Stack
- **Frontend:** React 19, TypeScript strict, Tailwind CSS v4, Radix UI + shadcn/ui, TanStack Query, dagre (graph layout), xterm.js (terminal)
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite
- **Routing:** Hash-based client-side (`#/build-orchestrator/*`)
- **Real-time:** WebSocket for build progress
- **Auth:** Subscription-based (Claude CLI), no API key needed for standard models

### Database Models

```
BuildProject
  - id: Integer PK
  - name: String(255)
  - description: Text
  - prd_content: Text
  - tech_stack: JSON
  - status: String (draft|ready|building|complete|failed)
  - template_id: FK nullable
  - instruction_blocks: JSON (array of {label, content, phase_scope, order})
  - phase_breakdown: JSON (array of {phase_number, summary, content, estimated_tokens})
  - cli_config: JSON (all settings)
  - generated_scripts: JSON (array of {filename, content})
  - queue_position: Integer nullable
  - created_at, updated_at: DateTime

BuildFeature
  - id: Integer PK
  - project_id: FK
  - name: String
  - description: Text
  - size: String (small|medium|large)
  - estimated_tokens: Integer
  - wave_number: Integer
  - parallel_group: Integer
  - status: String (pending|active|done|failed)
  - assigned_role: String
  - order: Integer

BuildFeatureDependency
  - id: Integer PK
  - feature_id: FK
  - depends_on_id: FK

BuildRole
  - id: Integer PK
  - project_id: FK
  - name: String
  - prompt_content: Text
  - prompt_library_id: FK nullable
  - model: String (opus|sonnet|haiku)
  - scope_whitelist: JSON
  - restrictions: JSON
  - quality_gates: JSON

BuildWave
  - id: Integer PK
  - project_id: FK
  - wave_number: Integer
  - status: String (pending|active|complete|failed)
  - transition_behavior: String (auto|notify|integrator)
  - failure_behavior: String (fix|retry|stop|rollback)

BuildQualityGate
  - id: Integer PK
  - wave_id: FK
  - name: String
  - command: String
  - required: Boolean
  - status: String (pending|running|passed|failed)
  - output: Text nullable

BuildExecution
  - id: Integer PK
  - project_id: FK
  - started_at, completed_at: DateTime
  - status: String (running|complete|failed|cancelled)
  - current_wave: Integer
  - log: Text

PromptLibraryItem
  - id: Integer PK
  - name: String
  - description: Text
  - content: Text
  - tags: JSON (list of strings)
  - source: String (builtin|user|imported)
  - usage_count: Integer
  - created_at, updated_at: DateTime

BuildTemplate
  - id: Integer PK
  - name: String
  - description: Text
  - category: String
  - config: JSON (serialized full configuration)
  - source: String (builtin|user|imported)
  - created_at, updated_at: DateTime
```

### API Endpoints

**Build Projects** (`server/routers/build_orchestrator.py`)
```
GET    /api/build-projects
POST   /api/build-projects
GET    /api/build-projects/:id
PUT    /api/build-projects/:id
DELETE /api/build-projects/:id
```

**PRD Decomposition**
```
POST   /api/build-projects/:id/decompose
PUT    /api/build-projects/:id/features/:fid
POST   /api/build-projects/:id/features/:fid/deps
DELETE /api/build-projects/:id/features/:fid/deps/:did
POST   /api/build-planner/analyze-prd
```

**Roles**
```
GET    /api/build-projects/:id/roles
POST   /api/build-projects/:id/roles
PUT    /api/build-projects/:id/roles/:rid
DELETE /api/build-projects/:id/roles/:rid
```

**Waves**
```
GET    /api/build-projects/:id/waves
PUT    /api/build-projects/:id/waves/:wid
PUT    /api/build-projects/:id/waves/:wid/gates/:gid
```

**Execution**
```
POST   /api/build-projects/:id/execute
POST   /api/build-projects/:id/execute/pause
POST   /api/build-projects/:id/execute/resume
POST   /api/build-projects/:id/execute/cancel
GET    /api/build-projects/:id/executions
GET    /api/build-projects/:id/executions/:eid
```

**Script Generation**
```
POST   /api/build-projects/:id/generate-files
GET    /api/build-projects/:id/generated-files
POST   /api/build-planner/plans/:id/generate
POST   /api/build-planner/plans/:id/run
```

**Queue**
```
GET    /api/build-planner/queue
PUT    /api/build-planner/queue/reorder
POST   /api/build-planner/queue/run-next
POST   /api/build-planner/plans/:id/queue
DELETE /api/build-planner/plans/:id/queue
```

**Prompt Library**
```
GET    /api/prompt-library
POST   /api/prompt-library
GET    /api/prompt-library/:id
PUT    /api/prompt-library/:id
DELETE /api/prompt-library/:id
GET    /api/prompt-library/tags
POST   /api/prompt-library/import
GET    /api/prompt-library/export
```

**Templates**
```
GET    /api/build-templates
POST   /api/build-templates
GET    /api/build-templates/:id
PUT    /api/build-templates/:id
DELETE /api/build-templates/:id
POST   /api/build-projects/from-template/:id
POST   /api/build-templates/from-project/:id
POST   /api/build-templates/import
GET    /api/build-templates/:id/export
```

**WebSocket**
```
WS     /ws/build-projects/:id        (real-time build updates)
WS     /ws/build-planner/:plan_id    (one-pager build updates)
```

### New Services
```
server/services/
  build_orchestrator.py         — Wave execution engine (extends parallel_orchestrator)
  build_decomposition.py        — PRD → features + waves (shared engine)
  build_file_generator.py       — Config → .claude/ agent/command/hook files
  prompt_library_database.py    — Prompt library CRUD + tag management
  build_template_database.py    — Template CRUD + serialization
  build_project_database.py     — Build project CRUD + state management
```

### New UI Files
```
ui/src/pages/
  BuildPlannerPage.tsx           — One-pager (Page 1)
  BuildOrchestratorPage.tsx      — Multi-page container with tab nav

ui/src/components/build-planner/
  InstructionBlock.tsx           — Single block with phase toggle
  InstructionBlockStack.tsx      — Draggable stack
  PrdSection.tsx                 — PRD input + phase calculator
  CliConfigPanel.tsx             — All CLI settings with tooltips
  OutputSection.tsx              — Preview, generate, run
  QueueManager.tsx               — Queue panel
  SavedProjects.tsx              — Saved projects panel
  TemplateManager.tsx            — Save/load templates
  LiveDashboard.tsx              — Running build status strip
  PhaseBreakdown.tsx             — Editable phase list

ui/src/components/build-orchestrator/
  ProjectSetup.tsx               — PRD input + decomposition
  RoleConfigurator.tsx           — Role card grid
  RoleCard.tsx                   — Individual role config
  WaveOrchestrator.tsx           — Wave lane view with DnD
  WaveCard.tsx                   — Individual wave config
  QualityGateConfig.tsx          — Gate config per wave
  HookConfigurator.tsx           — Hook setup for transitions
  BuildRunner.tsx                — Execution view
  BuildTimeline.tsx              — Horizontal timeline
  AgentStatusCard.tsx            — Live agent status
  DependencyGraphBuild.tsx       — Feature dependency viz
  PromptLibrary.tsx              — Library browser
  PromptEditor.tsx               — Markdown editor with preview
  TemplatesBrowser.tsx           — Template grid
  TemplateDetail.tsx             — Full template preview
  BuildHistory.tsx               — Past execution list
  GeneratedFilesPreview.tsx      — .claude/ file preview

ui/src/hooks/
  useBuildPlanner.ts             — React Query hooks (one-pager)
  useBuildOrchestrator.ts        — React Query hooks (multi-page)
  usePromptLibrary.ts            — Prompt library hooks
  useBuildTemplates.ts           — Template hooks
  useBuildWebSocket.ts           — WebSocket for build updates

ui/src/lib/
  build-planner-types.ts         — TypeScript types
```

### Integration with Existing AutoForge Systems
- **parallel_orchestrator.py** — Wave execution calls into existing parallel orchestrator for spawning agents within a wave
- **process_manager.py** — Agent lifecycle (start/stop/pause/resume) uses existing process manager
- **feature_mcp.py** — Build projects can optionally create feature databases for MCP tracking
- **WebSocket** — New event types alongside existing ones, same infrastructure
- **dependency_resolver.py** — Decomposition uses existing Kahn's algorithm for topological sort

---

## BUILD ORDER (How to Build THIS Product)

### Phase 1 — One-Pager MVP (Build Planner)
1. BuildPlannerPage with routing + nav button
2. Instruction blocks: stack, phase toggles, drag-and-drop, collapse/expand
3. PRD section with token counter
4. CLI config panel with tooltips
5. Script preview + generate
6. Save/load projects (basic database)

### Phase 2 — Backend + Persistence
7. Database models (BuildProject, BuildTemplate)
8. API router (CRUD + script generation)
9. Template save/load
10. Queue system (basic)

### Phase 3 — AI Integration
11. PRD decomposition engine (AI-powered phase breakdown)
12. Phase breakdown display (editable)
13. Token budget calculations

### Phase 4 — Prompt Library
14. PromptLibraryItem database model
15. Library CRUD + tag management
16. Library browser UI (search, filter, preview)
17. Integration with role configs

### Phase 5 — Role Configuration
18. BuildRole database model
19. Role card grid UI
20. Pre-built role prompts (8 roles)
21. Role → .claude/agents/*.md file generation

### Phase 6 — Wave Orchestration
22. BuildWave + BuildQualityGate models
23. Wave lane view UI with drag-and-drop
24. Quality gate configuration
25. Transition + failure behavior settings
26. Hook file generation

### Phase 7 — Build Execution
27. Build execution engine (wave runner with gates)
28. WebSocket real-time updates
29. Full execution dashboard
30. Build timeline visualization
31. Git checkpoint integration

### Phase 8 — Polish & Templates
32. Pre-built templates (7 templates)
33. Template browser UI
34. Project management page (list, detail, history)
35. Import/export (prompts, templates, projects)
36. PRD Maker integration (future addon hook)

---

## WHAT THIS DOES NOT DO

- Does NOT replace the existing AutoForge Initializer + Coding Agent flow
- Does NOT require changes to Claude Code CLI itself (generates standard .claude/ files)
- Does NOT make API calls during builds (agents are CLI sessions; only decomposition uses AI API)
- Does NOT handle billing/subscriptions (feature inside AutoForge, not separate paid product — SaaS version is a separate codebase)
