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

## Implementation Order

```
Phase 1 (Registry)  →  Phase 2 (Quick Check)  →  Phase 3 (Gap Analysis)  →  Phase 4 (Dashboard)  →  Phase 5 (Auto-Fix)
```

| Phase | Difficulty | What It Gets You |
|---|---|---|
| 1: Component Registry | 3/10 | Catalog of what's available vs missing |
| 2: Quick Check | 4/10 | Instant "can we make this?" answer per tool |
| 3: Gap Analysis | 5/10 | Prioritized build plans + auto-generated PRDs |
| 4: Dashboard | 3/10 | Global view of component coverage across all tools |
| 5: Auto-Fix Loop | 6/10 | Self-healing execution with learning |

**Total: ~21/50 difficulty. Five phases. Each is a standalone commit.**

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

## Files To Modify

| File | Phase | Changes |
|---|---|---|
| `ui/src/pages/YTStrategyLabPage.tsx` | 2 | Insert ToolReadinessCheck before Generate Tool |
| `server/routers/tool_factory.py` | 2 | Add analyzer endpoints |
| `server/services/sheet_blueprint.py` | 2 | Pass component availability to blueprint generation |

---

## Success Criteria

1. **Phase 1:** Component registry loads on startup, correctly detects which components are available
2. **Phase 2:** Quick Check runs in <5 seconds and correctly identifies blocked steps
3. **Phase 3:** Gap Analysis generates accurate mini-PRDs that an agent can build from
4. **Phase 4:** Dashboard shows global coverage % and highest-impact components to build
5. **Phase 5:** A failed step automatically diagnoses, fixes, and retries successfully

## The End State

After processing 15-20 YouTube videos through this system:
- Component library covers 95%+ of common step types
- Quick Check passes for 19 out of 20 new videos
- The 1 in 20 that fails triggers Gap Analysis → component gets built → future tools benefit
- The system is self-improving: every tool it CAN'T make today makes it MORE capable tomorrow
