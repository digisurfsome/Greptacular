# Codebase Ingestion & Rebuild Planning — "Spaghetti to Spec"

## Status: Ready for Implementation

## Overview

A new flow in AutoForge that lets users throw an existing codebase (messy vibe-coded app, legacy project, prototype that needs a rewrite) into the system and get a complete rebuild plan. Uses the **1M context window** (already enabled on CLI subscription via `betas=["context-1m-2025-08-07"]` in `client.py` line 641) to deeply analyze even large codebases without API costs.

**What exists today:** A converter skill (`/gsd-to-autoforge-spec`) that transforms output from an EXTERNAL tool (GSD framework) into AutoForge format. Requires installing GSD separately, running 4 parallel Claude agents outside AutoForge, then manually converting. CLI-only, no UI.

**What this builds:** A fully native, UI-integrated codebase analysis pipeline that:
1. Reads an existing codebase directly (no external tools needed)
2. Maps the entire architecture, dependencies, and feature set using the 1M context window
3. Generates a structured rebuild plan with PRDs for every feature
4. Produces an AutoForge `app_spec.txt` ready to feed into the build pipeline
5. Optionally consumes GSD output if it already exists (backward compatible)

**Why this matters:** Every developer who's vibe-coded an app and wants to "do it right" needs this. Every agency inheriting legacy code needs this. Every founder who hired cheap devs and got spaghetti needs this. This is the entry point for a massive segment of users — and it's a natural lead magnet for AutoForge itself.

---

## The User Flow

### In the UI: "Import Existing Project"

Add a new path to the NewProjectModal (or a new top-level button):

```
┌─────────────────────────────────────────┐
│  How do you want to start?              │
│                                         │
│  [🆕 Build From Scratch]               │
│  Start with an idea, build from zero    │
│                                         │
│  [📂 Import Existing Code]  ← NEW      │
│  Analyze a codebase and create a        │
│  rebuild/refactor plan                  │
│                                         │
│  [📋 From Template]                     │
│  Start from a pre-built boilerplate     │
└─────────────────────────────────────────┘
```

### "Import Existing Code" Flow

```
Step 1: Select Source
├── Browse to the codebase folder (FolderBrowser.tsx — already exists)
├── OR paste a git clone URL (clone into temp dir)
└── Show file count + estimated size: "Found 247 files, ~180K tokens"

Step 2: Choose Goal
├── 🔨 "Full Rebuild" — Analyze everything, create spec, rebuild from scratch
│   └── "The code is a mess. I want to understand what it does and rebuild it properly."
├── 🔧 "Refactor Plan" — Map the codebase, identify issues, plan refactoring
│   └── "The code works but needs cleanup. Give me a plan to fix it."
├── 📝 "Feature Extraction" — Just map what exists into features
│   └── "I need documentation of what this app does, feature by feature."
└── 🔀 "Migrate Tech Stack" — Rebuild with different technology
    └── "I want the same app but in React/Node instead of [current stack]."

Step 3: Analysis Configuration
├── Care Level: [1] [2] [3] [4] [5] (same 1-5 scale from spec creation)
│   └── Level 1: Quick scan, AI decides everything
│   └── Level 5: Deep analysis, user reviews every finding
├── Design Style: (only for Full Rebuild / Migrate)
│   └── Use existing style picker (12 styles, mixing, palettes, modifiers)
└── Priority Focus: (checkboxes)
    ├── ☑ Map all features and user flows
    ├── ☑ Identify technical debt and anti-patterns
    ├── ☑ Document database schema and relationships
    ├── ☑ Map API endpoints and contracts
    ├── ☑ Trace component/page hierarchy
    └── ☑ Identify security vulnerabilities

Step 4: Analysis Agent Runs (real-time progress via WebSocket)
├── Phase 1: Discovery (file tree, config files, entry points)
├── Phase 2: Deep Read (routes, models, components — uses 1M context)
├── Phase 3: Dependency Mapping (imports, calls, data flow)
├── Phase 4: Feature Extraction (what does this app actually DO?)
├── Phase 5: Issue Detection (spaghetti, dead code, anti-patterns)
└── Phase 6: Synthesis (structured analysis document)

Step 5: Review Analysis Results
├── Interactive dashboard showing what the analyzer found:
│   ├── Tech Stack identified
│   ├── Architecture diagram (component/page tree)
│   ├── Feature list (extracted from code behavior)
│   ├── Dependency graph (file-level and feature-level)
│   ├── Issues found (technical debt, security, dead code)
│   ├── Database schema (if detected)
│   └── API endpoint map (if detected)
├── User can edit/correct any findings before proceeding
└── "Looks good — generate the spec" button

Step 6: Spec Generation
├── Converts analysis into app_spec.txt (AutoForge format)
├── Creates initializer_prompt.md with correct feature_count
├── Optionally references original code as EXTRA_READ_PATHS
│   (so coding agents can peek at original implementation for context)
└── Ready to run through normal AutoForge build pipeline
```

---

## Architecture

### New Agent Type: `codebase-analyzer`

**File changes in `client.py`:**

```python
# Add to feature_tools_map (line ~336)
"codebase-analyzer": [],  # No feature tools needed — read-only analysis

# Add to max_turns_map (line ~353)
# This agent gets the MOST turns because it needs to read an entire codebase.
# The 1M context window (already enabled via betas) makes this feasible.
"codebase-analyzer": 300,

# In the allowed_tools section, codebase-analyzer gets:
# Read, Glob, Grep, WebFetch, WebSearch (for looking up framework docs)
# NO Write, Edit, Bash (read-only agent)
```

**The codebase-analyzer is READ-ONLY.** It does not modify any files. It only reads the source codebase and produces structured analysis output. This is critical for trust — users need to know their messy code won't be touched during analysis.

### New Prompt Template: `codebase_analysis_prompt.template.md`

This is the core of the feature. The prompt guides the analysis agent through a multi-phase deep dive:

```markdown
## YOUR ROLE - CODEBASE ANALYSIS AGENT

You are analyzing an existing codebase to produce a comprehensive map of
its architecture, features, dependencies, and issues. You have access to
the 1M context window — use it aggressively. Read as much code as you can.

### ANALYSIS GOAL: [ANALYSIS_GOAL]
### SOURCE DIRECTORY: [SOURCE_DIR]
### PRIORITY FOCUS: [PRIORITY_FOCUS]

---

## PHASE 1: DISCOVERY (Turns 1-30)

Start by understanding the project at a high level:

1. Read config files first:
   - package.json / pyproject.toml / Cargo.toml / go.mod / pom.xml
   - .env.example / .env.template (NOT .env itself — security)
   - tsconfig.json / webpack.config / vite.config
   - docker-compose.yml / Dockerfile
   - README.md / CONTRIBUTING.md

2. Map the directory structure:
   - Use Glob to list all source files
   - Identify the tech stack from file extensions and configs
   - Find entry points (main.ts, app.py, index.html, etc.)
   - Identify test directories (if any exist)

3. Produce DISCOVERY REPORT:
   ```
   Tech Stack: [frontend] + [backend] + [database] + [other]
   Entry Points: [list]
   File Count: [N] source files, [M] test files, [K] config files
   Estimated Complexity: Simple / Medium / Advanced
   Key Directories: [list with purpose of each]
   ```

## PHASE 2: DEEP READ (Turns 30-120)

Read the most important files in detail. Prioritize:

1. **Route definitions** — Every URL the app serves
2. **Database models/schemas** — Every table/collection/entity
3. **API endpoints** — Every REST/GraphQL endpoint with request/response shapes
4. **Components/Pages** — Every UI component, organized by page
5. **Services/Utilities** — Shared logic, helpers, middleware
6. **Authentication** — Auth flow, session management, role definitions
7. **State management** — Redux/Zustand/Context/Vuex stores

For each file you read, note:
- What it does (1-2 sentences)
- What it depends on (imports)
- What depends on it (used by)
- Any issues you see (code smells, security, dead code)

USE THE 1M CONTEXT WINDOW. Read entire files, not just headers.
The more code you hold in context, the better your dependency mapping.

## PHASE 3: DEPENDENCY MAPPING (Turns 120-170)

Using what you've read, build the dependency graph:

1. **File-level dependencies**: Which files import which
2. **Feature-level dependencies**: Which features require which other features
3. **Data flow**: How data moves from database → API → frontend → user
4. **External dependencies**: Third-party APIs, services, SDKs

Identify:
- Circular dependencies
- God files (files that everything depends on)
- Orphaned files (files nothing imports)
- Tight coupling (files that should be independent but aren't)

## PHASE 4: FEATURE EXTRACTION (Turns 170-220)

This is the most important phase. Convert code into FEATURES.

For each distinct thing a user can DO in this app, create a feature entry:
- Feature name (user-action format: "User can create a new post")
- Category: functional / style / infrastructure
- Current implementation quality: good / messy / broken / missing
- Files involved (which source files implement this feature)
- Dependencies (which other features must work for this one to work)
- Test steps (how you would verify this feature works)
- Issues (specific problems with the current implementation)

**Counting rules:**
- Each CRUD operation = 1 feature (create, read, update, delete separately)
- Each page/route = 1+ features (depending on what it does)
- Each user role/permission check = 1 feature
- Each integration (email, payment, upload) = 1+ features
- Each validation rule = 1 feature
- Authentication/authorization = multiple features

**Target feature counts (same tiers as new projects):**
- Simple apps: 25-55 features
- Medium apps: ~105 features
- Advanced apps: ~155-205 features

## PHASE 5: ISSUE DETECTION (Turns 220-260)

Catalog every problem you found:

### Technical Debt
- Duplicated code
- Inconsistent patterns (sometimes REST, sometimes GraphQL)
- Missing error handling
- No input validation
- Hardcoded values that should be config

### Security Issues
- SQL injection vulnerabilities
- XSS vulnerabilities
- Exposed secrets/credentials
- Missing authentication on routes
- Insecure dependencies (check package.json versions)

### Architecture Issues
- No separation of concerns (business logic in UI components)
- Database queries in route handlers (no service layer)
- No TypeScript / type safety
- Global mutable state
- Missing environment variable handling

### Dead Code
- Unused imports
- Unreachable functions
- Commented-out code blocks
- Files that nothing references

## PHASE 6: SYNTHESIS (Turns 260-300)

Produce the final structured output. Write to `[OUTPUT_DIR]/.autoforge/analysis/`:

### File 1: `analysis_report.md`
Complete human-readable analysis with all findings from Phases 1-5.

### File 2: `feature_map.json`
Structured JSON of all extracted features:
```json
{
  "features": [
    {
      "name": "User can register with email and password",
      "category": "functional",
      "quality": "messy",
      "source_files": ["src/pages/Register.tsx", "src/api/auth.ts"],
      "depends_on": [],
      "test_steps": ["Navigate to /register", "Fill in email and password", "..."],
      "issues": ["No email validation", "Password stored in plaintext"]
    }
  ],
  "total_features": 87,
  "complexity_tier": "medium"
}
```

### File 3: `dependency_graph.json`
File-level and feature-level dependency data for visualization.

### File 4: `issue_report.md`
Categorized list of all issues found, sorted by severity.

### File 5: `rebuild_recommendations.md`
Specific recommendations for the rebuild:
- What to keep from the original code
- What to throw away
- Architecture recommendations for the rebuild
- Suggested tech stack (keep same or migrate)
- Estimated feature count for the AutoForge spec
- Priority order for rebuilding
```

### New Service: `server/services/analysis_session.py`

Manages the codebase analysis conversation:

```python
class AnalysisSession:
    """Manages codebase analysis using the 1M context window."""

    def __init__(self, project_name: str, source_dir: str, output_dir: str):
        self.project_name = project_name
        self.source_dir = Path(source_dir)   # The messy codebase to analyze
        self.output_dir = Path(output_dir)   # The new AutoForge project dir
        self.analysis_goal = "full_rebuild"   # or refactor, extract, migrate
        self.care_level = 3
        self.priority_focus = []

    async def start(self):
        """Launch the codebase-analyzer agent."""
        # 1. Load codebase_analysis_prompt.template.md
        # 2. Replace placeholders: [SOURCE_DIR], [ANALYSIS_GOAL], [PRIORITY_FOCUS]
        # 3. Configure EXTRA_READ_PATHS to include source_dir (read-only)
        # 4. Create ClaudeSDKClient with:
        #    - agent_type="codebase-analyzer"
        #    - max_turns=300
        #    - 1M context beta (already enabled by default)
        #    - Read/Glob/Grep tools only (no Write/Edit/Bash)
        #    - WebSearch for looking up framework documentation
        # 5. Stream analysis progress to WebSocket

    async def convert_to_spec(self):
        """Convert analysis output to AutoForge app_spec.txt."""
        # Read analysis_report.md and feature_map.json
        # Generate app_spec.txt in AutoForge XML format
        # Generate initializer_prompt.md with feature_count
        # User reviews and approves

    async def start_rebuild(self):
        """Kick off the normal AutoForge build pipeline."""
        # Set EXTRA_READ_PATHS to include source_dir
        # (so coding agents can reference original implementation)
        # Run: spec-analyzer → architect → initializer → coding agents
```

### New Router: `server/routers/analysis.py`

```python
# WebSocket for real-time analysis progress
@router.websocket("/ws/analyze/{project_name}")
async def analysis_websocket(websocket: WebSocket, project_name: str):
    """Stream codebase analysis progress."""

# REST endpoints
@router.post("/api/projects/{project_name}/analyze")
async def start_analysis(project_name: str, config: AnalysisConfig):
    """Start codebase analysis."""
    # config includes: source_dir, goal, care_level, priority_focus

@router.get("/api/projects/{project_name}/analysis")
async def get_analysis(project_name: str):
    """Get analysis results (report, features, issues)."""

@router.post("/api/projects/{project_name}/analysis/convert")
async def convert_to_spec(project_name: str):
    """Convert analysis to AutoForge spec."""

@router.get("/api/projects/{project_name}/analysis/status")
async def analysis_status(project_name: str):
    """Get analysis progress (phase, % complete, files read)."""
```

### UI Components

**New: `ImportProjectFlow.tsx`**

Multi-step wizard (same pattern as NewProjectModal):

```
Step 1: CodebaseSelector
├── FolderBrowser (existing component)
├── OR git URL input + clone button
├── File stats display (count, size, estimated tokens)
└── Tech stack auto-detect preview

Step 2: GoalSelector
├── 4 goal cards (rebuild, refactor, extract, migrate)
├── Each with icon, title, description
└── For "migrate": tech stack picker for target

Step 3: AnalysisConfig
├── Care level: 1-5 button group
├── Priority focus: checkboxes
└── Design style picker (for rebuild/migrate goals)

Step 4: AnalysisProgress
├── Phase indicator (1-6) with current phase highlighted
├── File count: "Reading file 47/247..."
├── Live log output (like AgentMissionControl)
├── Estimated time remaining
└── [Pause] [Cancel] buttons

Step 5: AnalysisResults
├── Tab: Overview (tech stack, complexity, file count, feature count)
├── Tab: Features (extracted feature list, editable)
├── Tab: Architecture (component tree, dependency graph — use DependencyGraph.tsx)
├── Tab: Issues (categorized issue list with severity)
├── Tab: Recommendations (rebuild plan)
└── [Generate Spec & Start Building] button

Step 6: SpecReview
├── Generated app_spec.txt preview
├── Feature count confirmation
├── Edit capabilities (same as create-spec Phase 7)
└── [Start AutoForge Build] button
```

**New: `AnalysisDashboard.tsx`**

A results dashboard that visualizes the analysis output:

```
┌──────────────────────────────────────────────────────┐
│ Codebase Analysis: my-spaghetti-app                  │
│                                                      │
│ Tech: React 18 + Express + MongoDB    Complexity: ██ │
│ Files: 247 source, 12 tests, 38 config               │
│ Features Found: 87        Issues Found: 34            │
│                                                      │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│ │Features │ │ Arch    │ │ Issues  │ │ Plan    │    │
│ │   87    │ │  tree   │ │   34    │ │  ready  │    │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │
│                                                      │
│ Feature Quality Breakdown:                           │
│ ████████░░░░░░ Good: 23 (26%)                       │
│ ██████████████ Messy: 48 (55%)                      │
│ ████░░░░░░░░░░ Broken: 11 (13%)                     │
│ ██░░░░░░░░░░░░ Missing: 5 (6%)                      │
│                                                      │
│ Top Issues:                                          │
│ 🔴 3 security vulnerabilities (SQL injection, XSS)  │
│ 🟠 8 missing error handlers                         │
│ 🟡 12 duplicated code blocks                        │
│ 🔵 11 dead code / unused imports                    │
│                                                      │
│ [Generate Rebuild Spec]  [Export Analysis Report]     │
└──────────────────────────────────────────────────────┘
```

---

## The 1M Context Window Strategy

This feature is specifically designed to leverage the 1M context window that's already enabled on the CLI subscription (`client.py` line 641: `betas=["context-1m-2025-08-07"]`).

### Why 1M Matters Here

A typical messy codebase:
- 100 files × 200 lines avg × 40 chars/line = ~800K characters ≈ ~200K tokens
- 250 files × 300 lines avg × 40 chars/line = ~3M characters ≈ ~750K tokens

With 1M tokens of context, the analyzer can hold:
- **Small apps (50-100 files):** Entire codebase in context at once
- **Medium apps (100-250 files):** Most of the codebase, with strategic file selection
- **Large apps (250+ files):** Multi-pass analysis with compaction between passes

### File Prioritization Strategy

For codebases that exceed 1M tokens, the analyzer uses a priority system:

**Priority 1 (Always read):**
- Config files (package.json, tsconfig, etc.)
- Entry points (index.ts, app.py, main.go)
- Route definitions
- Database models/schemas
- Environment configs

**Priority 2 (Read if budget allows):**
- Page/view components
- API endpoint handlers
- Service/business logic files
- Middleware

**Priority 3 (Skim via Grep):**
- Utility/helper files
- Style files (CSS/SCSS)
- Test files
- Generated code

**Priority 4 (Skip):**
- node_modules, venv, .git
- Build output (dist, build, .next)
- Binary files (images, fonts)
- Lock files (package-lock.json, yarn.lock)

### The Compaction Advantage

The PreCompact hook (already implemented in `client.py` lines 527-607) means that even if the analyzer reads more than 1M tokens worth of code, the system will automatically compact earlier reads while preserving key findings. The analysis prompt instructs the agent to produce structured summaries at the end of each phase — these summaries survive compaction while the raw file contents can be discarded.

---

## Backward Compatibility with GSD

If the user has already run GSD's `/gsd:map-codebase`, the analysis agent should detect and use that output:

```python
# In the analysis prompt:
## CHECK FOR EXISTING ANALYSIS

Before starting your own analysis, check if `.planning/codebase/` exists
in the source directory. If it does, these files were produced by the GSD
framework and contain pre-analyzed data:

- STACK.md — Technology stack
- ARCHITECTURE.md — Code architecture
- STRUCTURE.md — Directory layout
- CONVENTIONS.md — Code conventions
- INTEGRATIONS.md — External services

If these files exist, READ THEM FIRST. They give you a head start.
You still need to do your own deep read of the actual source code
(GSD produces summaries, not detailed feature extraction), but the
GSD output helps you prioritize what to read.

If these files do NOT exist, proceed with Phase 1: Discovery from scratch.
```

---

## How This Feeds Into the Normal Build Pipeline

After analysis and spec generation, the project enters the standard AutoForge pipeline:

```
[Import Existing Code]
        ↓
[Codebase Analyzer Agent] ← NEW (uses 1M context, read-only)
        ↓
[User Reviews Analysis]
        ↓
[Generate app_spec.txt]
        ↓
[Spec Analyzer Agent] ← EXISTING (validates spec quality)
        ↓
[Architect Agent] ← EXISTING (designs clean architecture)
        ↓
[Initializer Agent] ← EXISTING (creates features in DB)
        ↓
[Coding Agents] ← EXISTING (implement features)
        ↓
[Testing Agents] ← EXISTING (verify features)
```

**Key enhancement:** During the coding phase, set `EXTRA_READ_PATHS` to include the original source directory. This way, coding agents can reference the original implementation when building the clean version — they can see HOW something was implemented (even if messily) and use that as context for building it properly.

---

## Standalone App Potential

This codebase analysis system is a **natural standalone product**. The components that could be extracted:

### Standalone App 1: "Code Autopsy"
Just the analysis part — throw a codebase in, get a detailed report:
- Architecture map
- Feature inventory
- Issue catalog
- Dependency graph
- No rebuild — just understanding

**Lead magnet angle:** Free tier analyzes up to 50 files. Shows enough to be useful. Full analysis requires AutoForge (or a paid tier).

### Standalone App 2: "PRD from Code"
Analysis + spec generation — take a codebase and produce product documentation:
- Feature list with user stories
- Technical architecture doc
- API documentation
- Database schema documentation
- Useful for teams inheriting legacy code, onboarding new devs, or just documenting what exists

**Lead magnet angle:** Every team that says "we don't have documentation" needs this. Free generates the feature list, paid generates the full PRD.

### Standalone App 3: "Stack Migrator"
Analysis + migration planning — take a codebase in Framework A, plan the rebuild in Framework B:
- "Take my jQuery app and plan a React rebuild"
- "Take my Django app and plan a Node.js rebuild"
- Maps features, then shows how each would be implemented in the target stack
- Generates an AutoForge spec for the target stack

**Lead magnet angle:** Every company going through a tech stack migration needs this. The analysis is free, the actual rebuild uses AutoForge.

### Standalone App 4: "Design System from Code" (your UI idea)
Already discussed in the roadmap — the design/style system as its own product. Takes an existing app's CSS/styles and extracts a design system, or takes an audience profile and generates a complete design system with components.

**Lead magnet angle:** Free generates style tokens for 1 style. Paid unlocks mixing, palettes, modifiers, and export to Figma/CSS/Tailwind.

### How to Structure These as Lead Magnets

Each standalone app should:
1. Be a simple, focused tool (one page, one job)
2. Use AutoForge's existing infrastructure under the hood
3. Provide genuine value in the free tier (not just a teaser)
4. Have a natural upgrade path to AutoForge for the full experience
5. Be deployable via AutoForge itself (dogfooding — build the lead magnets WITH AutoForge)

The bridge website spec you already have (`.claude/generated-prds/bridge-website-spec.xml`) could be the distribution platform — a landing site that showcases these standalone tools and funnels users to AutoForge.

---

## Implementation Files

### New Files to Create

| File | Purpose |
|------|---------|
| `.claude/templates/codebase_analysis_prompt.template.md` | Analysis agent prompt (the big one) |
| `server/services/analysis_session.py` | Analysis session management |
| `server/routers/analysis.py` | REST + WebSocket endpoints |
| `ui/src/components/ImportProjectFlow.tsx` | Multi-step import wizard |
| `ui/src/components/AnalysisDashboard.tsx` | Results visualization |
| `server/schemas.py` (modify) | Add `AnalysisConfig`, `AnalysisStatus` models |

### Existing Files to Modify

| File | Change |
|------|--------|
| `client.py` | Add `codebase-analyzer` to agent type maps, configure read-only tools |
| `agent.py` | Add `codebase-analyzer` dispatch (lines ~222-242) |
| `autonomous_agent_demo.py` | Add `codebase-analyzer` to `--agent-type` choices |
| `prompts.py` | Add `get_analysis_prompt()` with placeholder replacement |
| `server/main.py` | Register new `analysis` router |
| `ui/src/App.tsx` | Add import flow route/entry point |
| `ui/src/components/NewProjectModal.tsx` | Add "Import Existing Code" option |

### Settings

| Key | Type | Default | UI Control |
|-----|------|---------|------------|
| `analysis_max_turns` | int | 300 | Button group: [150] [200] [300] |
| `analysis_care_level` | int | 3 | Button group: [1-5] |
| `analysis_include_original_as_reference` | bool | true | Toggle |

The `analysis_include_original_as_reference` toggle controls whether coding agents can see the original source code (via EXTRA_READ_PATHS) during rebuild. Default ON — seeing the original implementation helps agents build the clean version.

---

## What NOT to Change

1. **The existing GSD converter skill** — Keep it working for users who already use GSD
2. **The spec-analyzer and architect agents** — They still validate and plan AFTER analysis
3. **The build pipeline** — After spec generation, everything flows normally
4. **The 1M context beta flag** — Already enabled, don't touch it
5. **EXTRA_READ_PATHS security** — Sensitive directory blocking still applies

---

## Edge Cases

1. **Massive codebases (1000+ files):** The analyzer uses the priority system and compaction. Phase 2 focuses on the most important files. The analysis report notes "X files were not deeply analyzed due to size — consider running again with narrower priority focus."

2. **No clear entry point:** Some messy codebases don't have obvious structure. The analyzer falls back to file extension analysis + package manager configs to determine what's what.

3. **Multiple languages:** The analyzer handles polyglot projects (React frontend + Python backend + Go microservices). It produces separate feature maps per service/component.

4. **Monorepos:** Detect `lerna.json`, `pnpm-workspace.yaml`, `nx.json`, etc. Analyze each package separately, then map inter-package dependencies.

5. **The code doesn't run:** That's fine. The analyzer only READS code — it doesn't execute it. A broken app can still be analyzed for features, architecture, and issues.

6. **User wants to keep some original code:** The "Refactor Plan" goal preserves the existing codebase and produces a plan for incremental improvements rather than a full rebuild. The spec focuses on what to change, not what to rewrite.
