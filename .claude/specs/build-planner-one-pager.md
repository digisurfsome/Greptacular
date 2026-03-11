# Agent OS Context: Build Planner (One-Pager)

---

## STANDARDS

### Tech Stack
- **Framework**: React 19 + TypeScript (strict mode)
- **Styling**: Tailwind CSS v4 with existing design tokens from `ui/src/styles/globals.css`
- **Components**: Radix UI primitives + shadcn/ui (`ui/src/components/ui/`)
- **Icons**: Lucide React
- **Data Fetching**: TanStack React Query
- **Routing**: Hash-based client-side routing (pattern: `window.location.hash = '#/build-planner'`)
- **State**: React useState/useCallback hooks (no external state library)

### Code Conventions
- Named function exports (not default exports)
- Return type: `React.JSX.Element`
- Tailwind utility classes for all styling
- shadcn/ui components for all form elements (Button, Input, Textarea, Select, Dialog, Tooltip, Checkbox, Switch, Tabs)
- API calls via TanStack Query hooks in `ui/src/hooks/`
- Types in `ui/src/lib/types.ts`
- Backend routers follow FastAPI pattern in `server/routers/`
- Database models in `api/database.py` using SQLAlchemy 2.0 declarative base
- Pydantic schemas in `server/schemas.py`

### Auth Model
- Uses subscription auth (`force_subscription=True`) for all Claude CLI calls
- Same auth flow as the existing coding agent — goes through `get_effective_sdk_env()` in `registry.py`
- No API key needed for standard 200k context models
- API key path only for 1M token models (edge case, not default)

### Design System
- Neobrutalism style matching existing AutoForge UI
- Dark mode support via `.dark` class selector
- CSS variables in oklch color format
- Responsive: mobile-aware but desktop-primary

---

## PRODUCT

### Vision
Build Planner is a single-page tool inside AutoForge/Greptacular that turns a PRD + reusable instruction blocks into phase-separated bash scripts with Claude CLI calls baked in. It replaces the "paste one giant prompt and pray" workflow with a structured, repeatable system.

### Product Story
Vibe coders today are pasting everything into one prompt, running out of tokens, getting half-built apps, and starting over. YouTube creators discover better prompting techniques daily/weekly, but there's no way to modularly upgrade your build process — you rewrite everything each time.

Build Planner separates **how you build** (instruction blocks that persist across projects) from **what you're building** (the PRD that changes). Instruction blocks can be toggled per phase, reordered, saved as templates, and upgraded independently. When a creator drops a new technique, you add one block — you don't rewrite your entire prompt.

### Target User
Non-technical "vibe coders" who use Claude Code via subscription. They watch YouTube tutorials, collect prompting techniques, and build apps by describing what they want. They are NOT developers — every option needs a tooltip explaining what it does in plain language.

### Business Model
- **Entry product**: The one-pager (this spec)
- **Upsell**: Deluxe version with dedicated pages per section, LLM per stage, full dashboard
- **Flywheel**: Owner curates best YouTube creator techniques → becomes the template library → creators adopt the platform

### Use Cases
1. **New build**: Fill instruction blocks + paste PRD → generate phase scripts → run
2. **Template reuse**: Load saved template (instruction blocks) → swap in new PRD → generate
3. **Mid-session save**: Fill halfway, save as draft project, come back later
4. **Queue builds**: Complete multiple builds, add to queue, run sequentially
5. **Watch a build**: Minimal dashboard shows phase progress, tokens consumed while build runs
6. **Upgrade workflow**: Add/edit/remove individual instruction blocks without touching anything else

---

## SPECS

### Page Route
- Hash route: `#/build-planner`
- Navigation button added to App.tsx header bar (next to existing DunkStack, Workspace, Dashboard, YT Lab buttons)
- Page component: `ui/src/pages/BuildPlannerPage.tsx`

### Page Layout (Top to Bottom)

#### 1. Live Dashboard Strip (top, always visible when a build is running)
- Sticky bar at top of page
- Shows: project name, current phase (e.g., "Phase 2 of 5"), tokens consumed, estimated tokens remaining
- Simple progress bar
- Hidden when no build is running
- "Stop" button to cancel

#### 2. Project Header Bar
- **Project name** text input
- **Status badge**: Draft | Ready | Queued | Running | Complete
- **Buttons**: Save Project, Load Project, New Project
- **Template controls**: Save as Template, Load Template (dropdown of saved templates)
- Templates only save the instruction blocks (Section 3) — not the PRD

#### 3. Instruction Blocks (the key innovation)
- A vertical stack of text boxes, each with:
  - **Phase toggle** at top of each block: three options as pill buttons
    - "Phase 1 Only" — this block only goes into the first phase script
    - "Phase 2+ Only" — this block goes into phase 2 and all subsequent phase scripts
    - "All Phases" — this block goes into every phase script
  - **Text area** — the actual instruction content (auto-expanding height)
  - **Label field** — short name for the block (e.g., "Tech Stack Rules", "Testing Contract", "Component Pattern")
  - **Drag handle** — left side, for reordering blocks via drag-and-drop
  - **Delete button** — remove block (with confirmation)
  - **Collapse/expand toggle** — minimize to just show the label (saves screen space)
- **"+ Add Block" button** at bottom of the stack — adds a new empty instruction block
- Blocks are ordered top-to-bottom; order determines injection order in generated scripts
- **Pre-populated starter blocks** for new projects (user can delete/edit):
  - "Tech Stack" (All Phases) — empty, placeholder text: "e.g., Use React 19, TypeScript strict, Tailwind v4..."
  - "Project Setup" (Phase 1 Only) — empty, placeholder: "e.g., Create project structure, install dependencies..."
  - "Testing Script" (Phase 2+) — empty, placeholder: "Paste your custom test script here..."

#### 4. PRD Section
- **Header**: "Build Spec (PRD)" with tooltip: "This is the actual coding specification — what features to build, what screens to create, what APIs to set up. This gets split across phases."
- **Large text area** — paste or type the full PRD
- **Token counter** — shows estimated token count of the PRD content (live, as you type)
- **"Break into Phases" button** — sends PRD to AI, returns suggested phase breakdown
  - Uses Claude CLI (subscription auth) to analyze the PRD
  - Returns: list of phases, each with a summary of what's included and estimated token count
  - Results appear below in an editable phase list
- **Phase breakdown display** (appears after AI analysis):
  - Numbered list of phases
  - Each phase shows: phase number, summary, features included, estimated tokens
  - User can: edit phase content, merge two phases, split a phase, reorder phases
  - Manual override dropdown: force number of phases (2, 3, 4, 5, 6, 7, 8)

#### 5. CLI Configuration Panel
- **Collapsible section** — "Build Settings" with expand/collapse
- Every single option has a **tooltip** (using shadcn Tooltip component) with plain-language explanation
- All options have sensible defaults so user can skip this entirely

**Subsections:**

**Model & Session**
| Option | Type | Default | Tooltip |
|--------|------|---------|---------|
| Model | Dropdown | Sonnet | "Which AI brain to use. Opus = smartest but slowest. Sonnet = good balance. Haiku = fastest but less capable." |
| Max turns per session | Dropdown: 5, 10, 25, 50, Unlimited | 25 | "How many back-and-forth exchanges Claude gets per phase before stopping. Higher = more thorough but costs more tokens." |
| Auto-continue between phases | Dropdown: Yes, No, Pause | Pause | "Should the next phase start automatically when the current one finishes? 'Pause' lets you review before continuing." |

**Build Behavior**
| Option | Type | Default | Tooltip |
|--------|------|---------|---------|
| YOLO mode | Toggle | Off | "Skip all testing for speed. Good for quick prototyping. Turn off for production-quality builds." |
| Batch size | Dropdown: 1, 2, 3 | 3 | "How many features Claude works on per session. Higher = faster but Claude may lose focus." |
| Parallel agents | Dropdown: 1, 2, 3, 4, 5 | 1 | "Run multiple Claude sessions at once. More agents = faster but costs more. Start with 1 if unsure." |
| Git commits | Dropdown | After each feature | "When should code be saved to git? More frequent = safer but more commits to review." |
| Error handling | Dropdown | Retry once then skip | "What happens when Claude hits an error? 'Stop' pauses everything. 'Skip' moves to the next feature. 'Retry' tries once more then skips." |

**Testing**
| Option | Type | Default | Tooltip |
|--------|------|---------|---------|
| Testing approach | Dropdown | Full testing | "Full = runs all tests. Lint-only = just checks code compiles. YOLO = no tests at all." |
| Test framework | Dropdown: Auto-detect, Jest, Vitest, Pytest, Playwright | Auto-detect | "Which test runner to use. Auto-detect picks the right one based on your project." |
| Run tests | Dropdown | After each feature | "When to run tests. More frequent = catches bugs earlier but takes longer." |
| Custom test script | Textarea | Empty | "Paste your own test commands here. These run exactly as written after Claude's built-in tests. Great for custom validation scripts." |

**Environment**
| Option | Type | Default | Tooltip |
|--------|------|---------|---------|
| File access | Dropdown | Project folder only | "Where Claude can read/write files. 'Project only' is safest. 'Extra paths' lets Claude reference docs or other projects." |
| Extra read paths | Text input (shown if above = Extra) | Empty | "Comma-separated folders Claude can READ (not write). Example: /Users/me/docs,/Users/me/reference" |
| Network access | Dropdown | Localhost only | "Can Claude make network requests? 'Localhost' means only your machine. 'External' allows API calls to the internet." |
| Deployment target | Dropdown | None yet | "Where will this app be deployed? Helps Claude set up the right config files. Pick 'None' if you'll decide later." |

#### 6. Output & Actions Section

**Preview & Generate**
- **"Preview Scripts" button** — shows a read-only preview of what the bash scripts will look like
  - Modal/panel showing each phase script with syntax highlighting
  - User can review before generating
- **Script summary**: number of scripts, total estimated tokens, estimated cost
- **"Generate Scripts" button** — creates .sh files in the project directory
  - One script per phase: `phase1_setup.sh`, `phase2_build.sh`, etc.
  - Plus a master `run_all.sh` that executes them in sequence
- **"Generate & Run" button** — generates scripts AND starts Phase 1 immediately
  - Dashboard strip at top lights up
  - Output streams in real-time

**Project Actions**
- **Save Project** — saves current state to database (works even if half-filled)
- **Add to Queue** — marks build as ready, adds to build queue
- **Queue Manager** (expandable panel):
  - List of queued builds: name, number of phases, status
  - Drag to reorder queue
  - Remove from queue button per item
  - "Run Next" button — starts the next queued build
  - "Run All" button — runs all queued builds sequentially
- **Saved Projects** (expandable panel):
  - List of all saved projects (drafts and completed)
  - Click to load
  - Delete button per project
  - Filter: All | Drafts | Completed | Queued

### Backend Requirements

#### New Database Model: `BuildPlan`
```
Table: build_plans
- id: Integer, primary key
- name: String(255), required
- status: String(50), default 'draft' (draft|ready|queued|running|complete|failed)
- instruction_blocks: JSON (array of {label, content, phase_scope, order})
- prd_content: Text
- phase_breakdown: JSON (array of {phase_number, summary, content, estimated_tokens})
- cli_config: JSON (all the dropdown/toggle selections)
- custom_test_script: Text
- generated_scripts: JSON (array of {filename, content})
- queue_position: Integer, nullable
- created_at: DateTime
- updated_at: DateTime
```

#### New Database Model: `BuildTemplate`
```
Table: build_templates
- id: Integer, primary key
- name: String(255), required
- instruction_blocks: JSON (array of {label, content, phase_scope, order})
- cli_config: JSON (default settings to load with template)
- created_at: DateTime
- updated_at: DateTime
```

#### New Router: `server/routers/build_planner.py`
- Prefix: `/api/build-planner`
- Endpoints:
  - `GET /plans` — list all saved plans
  - `POST /plans` — create new plan
  - `GET /plans/{id}` — get plan by ID
  - `PUT /plans/{id}` — update plan
  - `DELETE /plans/{id}` — delete plan
  - `POST /plans/{id}/generate` — generate bash scripts from plan
  - `POST /plans/{id}/run` — generate and run (starts Phase 1)
  - `POST /plans/{id}/queue` — add to queue
  - `DELETE /plans/{id}/queue` — remove from queue
  - `GET /queue` — get ordered queue
  - `PUT /queue/reorder` — reorder queue
  - `POST /queue/run-next` — run next queued build
  - `POST /analyze-prd` — send PRD text, get phase breakdown suggestion
  - `GET /templates` — list templates
  - `POST /templates` — save template
  - `PUT /templates/{id}` — update template
  - `DELETE /templates/{id}` — delete template

#### WebSocket: `/ws/build-planner/{plan_id}`
- Real-time updates when a build is running:
  - `phase_start` — new phase beginning
  - `phase_complete` — phase finished
  - `output` — streaming Claude CLI output
  - `token_update` — token consumption update
  - `error` — error occurred
  - `complete` — all phases done

#### Script Generation Logic
When "Generate" is clicked, the backend:
1. Reads all instruction blocks and their phase_scope settings
2. Reads the phase breakdown (PRD split into chunks)
3. For each phase, assembles:
   - Instruction blocks where phase_scope = "all" OR matches current phase
   - The PRD chunk for that phase
   - CLI flags based on config (--yolo, --batch-size, --max-concurrency, etc.)
4. Wraps each phase in a bash script:
   ```bash
   #!/bin/bash
   # Phase N of M — [phase summary]
   # Generated by Build Planner

   cd "$PROJECT_DIR"

   claude --model [model] --max-turns [turns] --print "
   [assembled instruction blocks for this phase]

   --- BUILD SPEC (Phase N of M) ---
   [PRD chunk for this phase]
   "
   ```
5. Creates a master `run_all.sh` that runs phases in sequence with pause/continue logic

### File Structure (New Files)
```
ui/src/pages/BuildPlannerPage.tsx          — Main page component
ui/src/components/build-planner/
  InstructionBlock.tsx                      — Single instruction block with phase toggle
  InstructionBlockStack.tsx                 — Draggable stack of instruction blocks
  PrdSection.tsx                            — PRD input + phase calculator
  CliConfigPanel.tsx                        — All CLI settings with tooltips
  OutputSection.tsx                         — Preview, generate, run buttons
  QueueManager.tsx                          — Queue panel
  SavedProjects.tsx                         — Saved projects panel
  TemplateManager.tsx                       — Save/load templates
  LiveDashboard.tsx                         — Running build status strip
  PhaseBreakdown.tsx                        — Editable phase list after AI analysis
ui/src/hooks/useBuildPlanner.ts            — React Query hooks for API calls
ui/src/lib/build-planner-types.ts          — TypeScript types
server/routers/build_planner.py            — FastAPI router
server/services/build_planner_service.py   — Script generation + queue management logic
```

### Implementation Phases (for building THIS feature)

**Phase 1: Core Page + Instruction Blocks**
- Create BuildPlannerPage with routing
- Build InstructionBlock and InstructionBlockStack components
- Drag-and-drop reordering
- Phase scope toggles (Phase 1 / Phase 2+ / All)
- Add/remove/collapse blocks
- Add nav button to App.tsx header

**Phase 2: PRD + Phase Calculator + CLI Config**
- PRD text area with token counter
- "Break into Phases" AI integration
- Phase breakdown display (editable)
- CLI config panel with all dropdowns and tooltips
- Custom test script textarea

**Phase 3: Script Generation + Save/Load**
- Backend router + database models
- Script generation logic
- Script preview modal
- Save/load projects
- Save/load templates

**Phase 4: Queue + Live Dashboard**
- Queue manager UI + backend
- Build execution via process manager
- WebSocket for real-time updates
- Live dashboard strip
- Run all / run next queue controls
