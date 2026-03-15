# PRD: YT Lab Tool Analyzer — "Can This Tool Be Made?"

**Created: 2026-03-14 — Session 10b**
**Status: Ready to build**
**Priority: HIGHEST — This is the flywheel that makes the entire tool factory self-improving**
**Location: Inserted into YT Lab pipeline BEFORE "Generate Tool" button**

---

## What This Is

An AI analyzer that sits between the step extraction phase and the tool generation phase in YT Lab. It answers one question: **"Can this tool actually execute end-to-end with the components we currently have?"**

Two modes:
1. **Quick Check** — Fast scan. If all steps can execute → proceed to Generate Tool.
2. **Full Gap Analysis** — Deep analysis. Identifies missing components, generates PRDs to build them, tracks what's been added over time.

---

## Why It Matters

Right now, YT Lab creates beautiful 8-12 step prompt chains that look complete but CAN'T EXECUTE because the execution layer is missing components. The owner has to manually figure out what's missing. This analyzer automates that discovery.

**The flywheel:** Every time the analyzer identifies a gap and a component gets built, ALL future tools benefit. After processing 10-15 videos, most new tools will pass Quick Check automatically because the component library covers 95%+ of common step types.

---

## Where It Lives

**In the YT Lab pipeline, AFTER strategy extraction (steps created) and BEFORE Generate Tool:**

```
Current flow:
  YouTube URL → Ingestion → Discovery → Strategy Extraction → [steps shown] → Generate Tool

New flow:
  YouTube URL → Ingestion → Discovery → Strategy Extraction → [steps shown] →
  ┌─────────────────────────────────────┐
  │  TOOL ANALYZER (NEW)                │
  │  Quick Check: Can we make this?     │
  │  YES → Generate Tool                │
  │  NO  → Gap Analysis → Build Plan    │
  └─────────────────────────────────────┘
  → Generate Tool
```

**UI placement:** Below the step list, above the "Generate Tool" button. Shows a status indicator:
- Green: "All steps executable — ready to generate"
- Yellow: "N steps need components — analyzing..."
- Red: "N components missing — build plan ready"

---

## Phase 1: Component Registry

### 1.1 Define the execution component catalog

A registry of all execution capabilities the system currently has. Each component has:

```yaml
component:
  name: "claude_api"
  type: "ai_generation"
  description: "Text generation via Claude API (subscription auth)"
  handles:
    - "write", "create", "generate", "draft", "compose", "analyze", "research"
    - "summarize", "rewrite", "translate", "brainstorm"
  requirements: []  # No external setup needed
  status: "available"

component:
  name: "openai_api"
  type: "ai_generation"
  description: "Text generation via OpenAI API (requires API key)"
  handles:
    - Same as claude_api
  requirements: ["OPENAI_API_KEY"]
  status: "available"

component:
  name: "google_sheets_deploy"
  type: "output"
  description: "Deploy prompt chain to Google Sheets with Chain Runner"
  handles:
    - "deploy to sheets", "create spreadsheet", "sheets"
  requirements: ["google_oauth"]
  status: "available"

component:
  name: "playwright_browser"
  type: "browser_automation"
  description: "Headless browser for known/repeated web tasks"
  handles:
    - "navigate to", "click", "fill form", "upload", "download", "screenshot"
  requirements: ["playwright installed"]
  status: "not_built"  # Planned in Tool Execution Engine Phase 3

component:
  name: "computer_use"
  type: "browser_automation"
  description: "Claude computer use for unknown/third-party web interactions"
  handles:
    - "log in to", "interact with", "use the website", "configure in dashboard"
  requirements: ["display server", "chrome", "computer use API access"]
  status: "not_built"  # Planned in Tool Execution Engine Phase 3

component:
  name: "webhook_output"
  type: "integration"
  description: "POST step output to webhook URL (Zapier/Make/n8n)"
  handles:
    - "send to zapier", "trigger webhook", "notify", "push to"
  requirements: ["webhook_url configured"]
  status: "not_built"  # Planned in Tool Execution Engine Phase 2

component:
  name: "file_creation"
  type: "output"
  description: "Write files to disk or Google Drive"
  handles:
    - "save as", "export", "create file", "write to", "PDF", "CSV", "HTML"
  requirements: ["google_drive_oauth or local filesystem"]
  status: "not_built"  # Planned in Tool Execution Engine Phase 2

component:
  name: "cli_execution"
  type: "system"
  description: "Run CLI commands (claude -p, npm, git, etc.)"
  handles:
    - "run command", "execute", "CLI", "terminal", "bash", "claude -p"
  requirements: ["bash available"]
  status: "available"  # CLI Scripter already does this

component:
  name: "email_send"
  type: "integration"
  description: "Send emails via SendGrid/SMTP"
  handles:
    - "send email", "email to", "notify via email"
  requirements: ["SENDGRID_API_KEY or SMTP config"]
  status: "not_built"
```

**File:** `server/services/component_registry.py`
**Storage:** `~/.autoforge/component_registry.json` (persists across sessions, updated as components are built)

### 1.2 Auto-detect available components on startup

On server start, check which components are actually available:
- Is Playwright installed? → `playwright_browser.status = "available"`
- Is Google OAuth configured? → `google_sheets_deploy.status = "available"`
- Are API keys present? → Mark relevant API components as available
- Is computer use accessible? → Check if Claude computer use API works on current plan

---

## Phase 2: Quick Check (Mode 1)

### 2.1 Step-to-component matching

For each step in the extracted chain:
1. Read the step's type (generation, research, action, manual)
2. Read the step's prompt text
3. Match against component registry using keyword matching + AI classification
4. Return: `{step_number, step_title, required_components, all_available: bool}`

**Matching approach (two layers):**

**Layer 1 — Keyword matching (fast, zero tokens):**
Scan step title + prompt for component keywords. If a match is found with >80% confidence, use it.

**Layer 2 — AI classification (if keyword matching is ambiguous):**
Send the step prompt to Claude Haiku (fast, cheap) with the component catalog and ask: "Which components does this step need to execute? Return a list."

### 2.2 Quick Check result

```json
{
  "tool_name": "AI-Fulfilled Agency Builder",
  "total_steps": 8,
  "executable_steps": 5,
  "blocked_steps": 3,
  "pass": false,
  "details": [
    {"step": 1, "title": "Generate Brand Style Guide", "components": ["claude_api"], "status": "ready"},
    {"step": 2, "title": "Research Competitor Ads", "components": ["claude_api", "web_search"], "status": "ready"},
    {"step": 3, "title": "Build Storefront", "components": ["claude_api", "file_creation"], "status": "blocked", "missing": ["file_creation"]},
    {"step": 5, "title": "Upload Ads to Meta", "components": ["computer_use", "meta_api"], "status": "blocked", "missing": ["computer_use", "meta_api"]},
    {"step": 7, "title": "Automate DM Outreach", "components": ["computer_use", "social_api"], "status": "blocked", "missing": ["computer_use", "social_api"]}
  ],
  "missing_components": ["file_creation", "computer_use", "meta_api", "social_api"],
  "recommendation": "3 steps blocked. file_creation is easiest to add (4/10). computer_use unblocks 2 steps (7/10). Build file_creation first for quick win."
}
```

### 2.3 UI display

Below the step list, above Generate Tool:

```
┌─────────────────────────────────────────────────┐
│  ⚡ Tool Readiness Check                        │
│                                                  │
│  5/8 steps ready  ████████░░░░  62%             │
│                                                  │
│  ✅ Steps 1, 2, 4, 6, 8 — Ready                │
│  ❌ Step 3 — Needs: file_creation               │
│  ❌ Step 5 — Needs: computer_use, meta_api      │
│  ❌ Step 7 — Needs: computer_use, social_api    │
│                                                  │
│  Missing components:                             │
│  • file_creation (4/10 to build, unblocks 1)    │
│  • computer_use (7/10 to build, unblocks 2)     │
│  • meta_api adapter (6/10, unblocks 1)          │
│  • social_api adapter (5/10, unblocks 1)        │
│                                                  │
│  [Run Full Analysis]  [Generate Tool Anyway]     │
└─────────────────────────────────────────────────┘
```

If all steps are ready:
```
┌─────────────────────────────────────────────────┐
│  ✅ Tool Readiness Check                        │
│                                                  │
│  8/8 steps ready  ████████████  100%            │
│                                                  │
│  All steps can execute with current components.  │
│                                                  │
│  [Generate Tool]                                 │
└─────────────────────────────────────────────────┘
```

---

## Phase 3: Full Gap Analysis (Mode 2)

### 3.1 Triggered when Quick Check fails

When user clicks "Run Full Analysis", the analyzer:

1. **For each missing component**, generate a complete build specification:
   - What the component does
   - Files to create
   - How it plugs into the existing Tool Runner / execution engine
   - Estimated difficulty (1-10)
   - Dependencies on other components

2. **Prioritize by impact:**
   - How many steps across ALL tools (not just this one) does this component unblock?
   - Query the tool registry for all tools, count blocked steps per missing component
   - Rank: build the component that unblocks the most steps first

3. **Generate a mini-PRD for each missing component:**

```markdown
## Component: file_creation
**Difficulty:** 4/10
**Unblocks:** 7 steps across 3 tools
**What it does:** Takes AI-generated content and writes to disk or Google Drive
**Files to create:**
- server/services/execution/file_creator.py — File writing handler
- Add to component_registry.json
**Integration point:** Tool Runner execute_step() → when step type is file_create → call file_creator
**Dependencies:** Google Drive OAuth (already configured)
**Estimated build time:** 1 agent session
```

### 3.2 Build Plan output

The full analysis produces a prioritized build plan:

```
BUILD PLAN — AI-Fulfilled Agency Builder
=========================================

Priority 1: file_creation (4/10, unblocks 7 steps across 3 tools)
Priority 2: webhook_output (2/10, unblocks 4 steps across 2 tools)
Priority 3: computer_use (7/10, unblocks 12 steps across 5 tools)
Priority 4: meta_api adapter (6/10, unblocks 2 steps across 1 tool)

Build order recommendation:
1. file_creation + webhook_output (same session, low difficulty)
2. computer_use (separate session, complex)
3. meta_api (after computer_use, can use computer_use as fallback)

After building priorities 1-2:
  This tool: 7/8 steps ready (87%)
  All tools: 45/52 steps ready (86%)

After building all 4:
  This tool: 8/8 steps ready (100%)
  All tools: 52/52 steps ready (100%)
```

### 3.3 One-click PRD generation

"Generate PRD for [component]" button that creates a full PRD document at `docs/prd-component-{name}.md` ready for an agent to build.

---

## Phase 4: Component Tracker Dashboard

### 4.1 Global component status page

A new section in YT Lab Tools that shows:

```
COMPONENT LIBRARY
=================
Available (6):          Not Built (4):         In Progress (1):
✅ claude_api           ❌ computer_use        🔨 file_creation
✅ openai_api           ❌ meta_api
✅ google_sheets        ❌ social_api
✅ cli_execution        ❌ email_send
✅ web_search
✅ webhook_output

COVERAGE: 78% of all tool steps can execute
          (42/54 steps across 7 tools)
```

### 4.2 Cross-tool impact view

Shows which components would have the biggest impact if built:

```
HIGHEST IMPACT COMPONENTS TO BUILD:
1. computer_use — unblocks 12 steps across 5 tools
2. file_creation — unblocks 7 steps across 3 tools
3. meta_api — unblocks 2 steps across 1 tool
4. email_send — unblocks 2 steps across 2 tools
```

---

## Phase 5: Auto-Fix Loop

### 5.1 Execute → Fail → Diagnose → Fix → Retry

When a tool runs and a step fails:

1. **Capture the error** — full error message, stack trace, step context
2. **Diagnose** — AI agent analyzes: is this a bug in the component, a missing component, or a prompt issue?
3. **If bug:** Generate a fix PR (code changes to the component)
4. **If missing component:** Add to the gap analysis, update component registry
5. **If prompt issue:** Suggest prompt modifications
6. **Retry** — after fix is applied, re-run the failed step
7. **If it passes:** Mark the fix as verified, continue to next step
8. **Max retries:** 3 per step, then escalate to user

### 5.2 Learning from failures

Each failure-fix cycle is logged:
```json
{
  "step_type": "browser_action",
  "component": "playwright_browser",
  "error": "Selector #submit-btn not found",
  "diagnosis": "Site redesigned, selector changed",
  "fix": "Switch to computer_use for this step",
  "result": "passed"
}
```

This log feeds back into the analyzer — next time a similar step is encountered, it knows to recommend computer_use over Playwright for that type of site interaction.

---

## Phase 6: Self-Building — The System That Builds Its Own Tools

### 6.1 The Core Idea

When the analyzer discovers a missing component, it doesn't just write a PRD and wait. **It spawns a coding agent to build the missing component right now.** The discovering agent already has full context — it knows what's missing, why it's needed, and exactly how it plugs into the existing system. That context is the most expensive thing to rebuild. Use it.

**This is the flywheel at full speed:** YouTube video → extract steps → analyzer finds gap → agent builds component → component goes live → next video benefits automatically. No human in the loop except a server restart notification.

### 6.2 The Build Flow

```
Analyzer discovers missing component
        │
        ▼
┌──────────────────────────────────────────┐
│  SELF-BUILD DECISION                     │
│                                          │
│  Difficulty ≤ 5/10?  → Auto-build        │
│  Difficulty 6-7/10?  → Build with review │
│  Difficulty ≥ 8/10?  → PRD only (human)  │
│                                          │
│  Context window > 50%? → Hand off         │
│  Context window ≤ 50%? → Build in-place  │
└──────────────────────────────────────────┘
        │
        ▼ (Auto-build path)
┌──────────────────────────────────────────┐
│  BUILD AGENT                             │
│                                          │
│  1. Generate component spec from gap     │
│     analysis (already has full context)  │
│                                          │
│  2. Write the code                       │
│     - Component implementation           │
│     - Registration in component_registry │
│     - Integration point (Tool Runner     │
│       execute_step() routing)            │
│                                          │
│  3. Run lint + type check                │
│                                          │
│  4. git add + git commit                 │
│     "Auto-built component: {name}        │
│      Triggered by: {tool_name} step {N}  │
│      Unblocks: {count} steps across      │
│      {count} tools"                      │
│                                          │
│  5. git push origin main                 │
│                                          │
│  6. Notify user:                         │
│     "Built {component_name}. Restart     │
│      server to activate. {N} tools       │
│      now have full coverage."            │
└──────────────────────────────────────────┘
```

### 6.3 Who Builds — The Discovering Agent vs. A Fresh Agent

**Option A: Discovering agent builds (preferred when context ≤ 50%)**
- The analyzer agent already knows: what's missing, which steps need it, how existing components work, where integration points are
- Rebuilding that context in a fresh agent costs tokens and risks information loss
- If context window is under 50%, the discovering agent IS the builder
- After building, it returns to analyzer duties OR hands off to a fresh analyzer agent

**Option B: Fresh agent builds (when context > 50%)**
- If the discovering agent is deep in a multi-tool analysis and context is filling up
- The discovering agent writes a build spec file: `~/.autoforge/build_queue/{component_name}.json`
- A fresh agent picks it up, builds, commits, pushes
- The discovering agent continues analyzing remaining tools

**Build spec file format:**
```json
{
  "component_name": "file_creation",
  "triggered_by": {"tool": "AI-Fulfilled Agency Builder", "step": 3},
  "difficulty": 4,
  "description": "Takes AI-generated content and writes to disk or Google Drive",
  "integration_point": "tool_runner.execute_step() → when step.type == 'file_create'",
  "files_to_create": [
    "server/services/execution/file_creator.py"
  ],
  "files_to_modify": [
    "server/services/component_registry.py"
  ],
  "dependencies": ["google_drive_oauth"],
  "test_scenario": "Generate HTML content via Claude, write to local disk, verify file exists",
  "context_from_analyzer": "Full gap analysis output + component registry state at time of discovery"
}
```

### 6.4 Context Window Control

The build agent operates under strict context rules:

| Context % | Action |
|---|---|
| 0-40% | Build freely |
| 40-45% | Wrap up current file, commit what's done |
| 45-50% | COLD STOP — commit, push, write handoff note |
| 50%+ | Do NOT start a build — write spec file for fresh agent |

**The handoff note** (written to `~/.autoforge/build_queue/{component_name}_handoff.md`):
- What was built so far
- What's left to build
- Files created/modified
- The commit hash of progress so far
- Enough context for a fresh agent to finish

### 6.5 Safety Rails

**What the build agent CAN do:**
- Create new files in `server/services/execution/` and `server/services/api_adapters/`
- Modify `component_registry.py` (add new component entries)
- Modify `tool_runner.py` (add routing for new step types)
- Run lint, type check
- Git commit and push to main

**What the build agent CANNOT do:**
- Modify UI code (UI changes require user review + `npm run build`)
- Delete existing files
- Modify core pipeline files (`sheet_blueprint.py`, `yt_processor.py`, etc.)
- Run the full test suite (takes too long, wastes context)
- Push to any branch other than main

**Why no UI changes:** Backend components are safe to auto-build — they're isolated, testable, and won't break the existing UI. UI changes need visual review. The build agent adds backend capability; a future human session adds the UI to expose it.

### 6.6 Notification System

After a successful auto-build, the system notifies the user:

**In-app notification (if AutoForge is running):**
```
┌─────────────────────────────────────────────────┐
│  🔧 New Component Built Automatically           │
│                                                  │
│  Component: file_creation                        │
│  Triggered by: "AI-Fulfilled Agency Builder"     │
│  What it does: Writes AI-generated content to    │
│  disk or Google Drive                            │
│                                                  │
│  Impact:                                         │
│  • 7 steps across 3 tools now executable         │
│  • Global coverage: 78% → 91%                   │
│                                                  │
│  Commit: abc1234                                 │
│  Status: Ready — restart server to activate      │
│                                                  │
│  [View Commit]  [Restart Server]  [Dismiss]      │
└─────────────────────────────────────────────────┘
```

**Build log** (persisted to `~/.autoforge/auto_builds/`):
```json
{
  "component": "file_creation",
  "built_at": "2026-03-15T02:34:00Z",
  "triggered_by": "AI-Fulfilled Agency Builder, step 3",
  "commit_hash": "abc1234",
  "files_created": ["server/services/execution/file_creator.py"],
  "files_modified": ["server/services/component_registry.py"],
  "steps_unblocked": 7,
  "tools_affected": ["agency-builder", "listicle-forge", "seo-engine"],
  "context_used": "38%",
  "build_duration_seconds": 180
}
```

### 6.7 The Overnight Factory

The ultimate vision: the user queues up 10 YouTube videos before bed. Overnight:

1. Each video goes through ingestion → discovery → strategy extraction → steps
2. Analyzer runs Quick Check on each tool
3. First tool has 2 missing components → auto-build kicks in, builds both
4. Second tool needs a component that was just built → passes Quick Check
5. Third tool needs a new component → auto-build
6. By morning: 10 tools ready, 4 new components built, global coverage at 95%

The user wakes up to a notification: "Processed 10 videos. Built 4 new components. All 10 tools are ready to generate."

**This is software that builds its own tools. Each video it can't fully process makes it more capable for the next one. The gap shrinks to zero over time.**

---

## Implementation Order

```
Phase 1 (Registry)  →  Phase 2 (Quick Check)  →  Phase 3 (Gap Analysis)  →  Phase 4 (Dashboard)  →  Phase 5 (Auto-Fix)  →  Phase 6 (Self-Build)
```

| Phase | Difficulty | What It Gets You |
|---|---|---|
| 1: Component Registry | 3/10 | Catalog of what's available vs missing |
| 2: Quick Check | 4/10 | Instant "can we make this?" answer per tool |
| 3: Gap Analysis | 5/10 | Prioritized build plans + auto-generated PRDs |
| 4: Dashboard | 3/10 | Global view of component coverage across all tools |
| 5: Auto-Fix Loop | 6/10 | Self-healing execution with learning |
| 6: Self-Building | 7/10 | System builds its own missing components automatically |

**Total: ~28/60 difficulty. Six phases. Each is a standalone commit.**

---

## Files To Create

| File | Phase | Purpose |
|---|---|---|
| `server/services/component_registry.py` | 1 | Component catalog + availability detection |
| `~/.autoforge/component_registry.json` | 1 | Persistent component state |
| `server/services/tool_analyzer.py` | 2-3 | Quick Check + Gap Analysis logic |
| `server/routers/tool_analyzer.py` | 2 | REST endpoints for analyzer |
| `ui/src/components/tool-factory/ToolReadinessCheck.tsx` | 2 | Quick Check UI component |
| `ui/src/components/tool-factory/GapAnalysisView.tsx` | 3 | Gap Analysis results + PRD generation |
| `ui/src/pages/ComponentDashboardPage.tsx` | 4 | Global component status page |
| `server/services/execution_monitor.py` | 5 | Failure capture + diagnosis + retry |
| `server/services/auto_builder.py` | 6 | Self-build orchestrator — spawns coding agents for missing components |
| `server/services/build_notifier.py` | 6 | In-app + log notifications for auto-built components |

## Files To Modify

| File | Phase | Changes |
|---|---|---|
| `ui/src/pages/YTStrategyLabPage.tsx` | 2 | Insert ToolReadinessCheck before Generate Tool |
| `server/routers/tool_factory.py` | 2 | Add analyzer endpoints |
| `server/services/sheet_blueprint.py` | 2 | Pass component availability to blueprint generation |
| `server/services/tool_analyzer.py` | 6 | Add auto-build trigger when gap analysis finds buildable components |
| `server/routers/tool_analyzer.py` | 6 | Add build status + notification endpoints |

---

## Success Criteria

1. **Phase 1:** Component registry loads on startup, correctly detects which components are available
2. **Phase 2:** Quick Check runs in <5 seconds and correctly identifies blocked steps
3. **Phase 3:** Gap Analysis generates accurate mini-PRDs that an agent can build from
4. **Phase 4:** Dashboard shows global coverage % and highest-impact components to build
5. **Phase 5:** A failed step automatically diagnoses, fixes, and retries successfully
6. **Phase 6:** Analyzer discovers missing component → agent builds it → commits → pushes → user restarts → component is live. No human writes code.

## The End State

After processing 15-20 YouTube videos through this system:
- Component library covers 95%+ of common step types
- Quick Check passes for 19 out of 20 new videos
- The 1 in 20 that fails triggers auto-build → component gets built → future tools benefit
- The system is self-improving: every tool it CAN'T make today makes it MORE capable tomorrow
- **The user's only job is to feed it YouTube videos and restart the server when notified**
- First software that builds its own tools automatically — each gap it discovers makes it stronger
