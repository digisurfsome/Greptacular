# Phase Forge PRD v2 — SaaS-Ready Build Specification

## Overview

**Product Name:** Phase Forge
**Type:** Browser userscript (Tampermonkey / Violentmonkey / OrangeMonkey compatible)
**File:** `tampermonkey-prompt-injector.js` (replaces existing v1.3)
**Version:** 2.0
**SaaS Path:** Userscript (prototype) → Chrome Extension + Web App (production)

Phase Forge is a sidebar UI injected onto AI chat websites (Claude.ai, ChatGPT, Gemini) that orchestrates multi-phase software builds. It guides users from idea → PRD → phased build plan → automated execution, all from the browser with zero backend.

**Target audience:** Beginners and non-technical users who want to build apps using AI chat interfaces ("vibe coders"). This is a top-of-funnel product designed to be the easiest on-ramp to AI-powered app development.

## SaaS Distribution Strategy

### Phase 1: Tampermonkey Script (Current Build)
- Single `.js` file, zero dependencies
- Personal tool / prototype for testing and iteration
- All logic client-side, all state in localStorage

### Phase 2: Chrome Extension + Web App (Production SaaS)
- **Lightweight extension (~200 lines):** Only handles DOM injection into Claude/ChatGPT/Gemini. No business logic. Communicates with the web app via `chrome.runtime.sendMessage`.
- **Web app (dashboard):** Login/auth/payments (Stripe), project storage in real database, orchestration engine, prompt management, collaboration features. This is what users pay for.
- **Safari:** Safari Web Extensions (same codebase as Chrome with minor adjustments)
- **Firefox:** WebExtension API (same codebase)
- **Why this protects the code:** Extension without web app = useless. Web app without extension = can't inject prompts. Together = the full product.

### Support Chat Strategy
- **v1 (current build):** Use a "Ask for help" button that injects a context-aware question into the user's own AI chat session. Zero cost.
- **v2 (SaaS):** Add API-powered chat in the web app dashboard as a premium feature with rate limiting.

---

## Existing Codebase

The current file is at `/home/user/Greptacular/tampermonkey-prompt-injector.js` (1,139 lines, v1.3). It is a working userscript called "Cloud Prompt Injector" with:

- 20 customizable prompt buttons in a 2-column grid
- Prompt injection into Claude/ChatGPT/Gemini chat inputs (ProseMirror, textarea, Quill)
- Gear button (⚙) opens full-screen editor overlay for editing prompts
- Zoom controls with localStorage persistence
- Dark theme (#262624 background, #da7757 orange accent, #e0e0e0 text)

**ALL existing functionality MUST be preserved.** The prompt injector becomes one part of the larger Phase Forge system, with clear visual separation between the two components.

## Target Sites

```
@match https://claude.ai/*
@match https://chatgpt.com/*
@match https://chat.openai.com/*
@match https://gemini.google.com/*
```

**Site auto-detection:** The script auto-detects which site it's running on via URL and adjusts CSS positioning and selectors accordingly. No manual toggle needed.

## Design System

- Background: `#1e1e1c`
- Surface: `#262624`
- Border: `#333` (subtle), `#555` (prominent)
- Accent: `#da7757` (orange/coral)
- Text primary: `#e0e0e0`
- Text secondary: `#999`
- Success: `#4ade80`
- Error: `#ff4444`
- Warning: `#fbbf24`
- Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Mono font: `'SF Mono', 'Fira Code', 'Consolas', monospace`

---

## Feature 1: Improved Zoom Pill Buttons

**Replace** the current tiny +/- zoom buttons on the prompt injector panel with a full-width pill control bar.

### UI Spec
```
┌──────────────────────┐
│   −    │     +        │  ← Full-width pill, 36px tall
├──────────────────────┤
│  Zoom: [100%] [Set]  │  ← Input + save button below
├──────────────────────┤
│ Prompt Injector  ⚙   │  ← Existing header
├──────────────────────┤
│ [1][2][3][4]...      │  ← Existing button grid
└──────────────────────┘
```

### Requirements
- Pill spans entire panel width, divided 50/50: left = "−", right = "+"
- Height: 36px minimum (stays clickable even at 30% zoom)
- `#262624` background, `#555` border/divider, `#da7757` on hover
- Below pill: zoom percentage input (editable) + "Set" button to persist
- Zoom range: 30% to 300%, step: 10%
- Stored in `localStorage` key `cpi-zoom-level`

---

## Feature 2: Phase Forge Panel

A **separate** fixed sidebar panel, independent from the prompt injector. Clear visual separation — different component, different position, different border accent.

### Layout
```
Position: fixed
Right: 0
Top: 0
Width: 340px
Height: 100vh
Background: #1e1e1c
Border-left: 2px solid #da7757
z-index: 99998
Overflow-y: auto
```

### Toggle Button
- Floating circle button, 44px diameter
- `#da7757` background, white "PF" text, bold
- Position: fixed, vertically centered (top: 50%, transform: translateY(-50%))
- When panel closed: `right: 16px`
- When panel open: `right: 356px` (panel width + gap)
- Clicking toggles panel visibility
- Panel state stored in `localStorage` key `pf-panel-open`

### Panel Header
```
┌──────────────────────────────────────┐
│ ⚡ PHASE FORGE          [project ▾] │
│ Status: Ready                        │
└──────────────────────────────────────┘
```
- Project name dropdown (stored in localStorage)
- Overall status indicator

### Panel Sections

The panel has **5 sections** in order. Each section header is clickable to expand/collapse (▶ collapsed, ▼ expanded). Sections after GitHub Repository start **locked** (grayed out, 🔒 icon) until the previous section is complete.

1. GitHub Repository (always unlocked)
2. PRD Builder (unlocked after repo URL saved OR skipped)
3. Build Configurator (locked until PRD captured)
4. Phase Manager (locked until configuration locked)
5. Phase Runner (locked until at least 1 phase exists)

---

## Feature 3: GitHub Repository Setup (Section 1)

### Collapsible Helper Text
```
┌────────────────────────────────────┐
│ 📁 Project Repository        [▾]  │
├────────────────────────────────────┤
│ Don't have a repo yet?             │
│                                    │
│ GitHub is a free website where     │
│ developers store their code —      │
│ think of it like Google Drive for  │
│ code. It's the industry standard   │
│ used by virtually every developer  │
│ and company worldwide. Your code   │
│ stays private and secure (only you │
│ can see it unless you share it).   │
│ Setting one up takes 2 minutes.    │
│                                    │
│ 1. Go to github.com — create a     │
│    free account (or sign in)       │
│ 2. Click "+" → "New repository"    │
│ 3. Name it (your project name)     │
│ 4. Select "Private"                │
│ 5. Click "Create repository"       │
│ 6. Copy the URL and paste below    │
│                                    │
│ Repo URL: [______________________] │
│                       [Save Repo]  │
│                                    │
│ [ ] Skip — I'll set this up later  │
│                                    │
│ Status: ✓ Repo saved               │
└────────────────────────────────────┘
```

### Requirements
- Helper text is collapsible (click "Don't have a repo yet?" to expand/collapse)
- URL input field stored in `localStorage` key `pf-repo-url`
- "Save Repo" button validates URL is not empty, saves, shows green checkmark
- "Skip" checkbox allows bypassing this step, unlocks Section 2
- The saved URL becomes available as `{{REPO_URL}}` placeholder in phase prompts
- Status indicator: empty = "Not set", saved = "✓ Repo saved" (green), skipped = "Skipped"

---

## Feature 4: PRD Builder (Section 2)

Locked until GitHub repo is saved or skipped. Shows 🔒 when locked.

### Mode Toggle
Three-way pill toggle at the top: `[I Have a PRD]` | `[Questionnaire]` | `[Rant Mode]`
- Orange highlight on active selection
- Stored in `localStorage` key `pf-prd-mode`

### "I Have a PRD" Path

When selected:
- Show a large textarea: "Paste your PRD here"
- A "Save PRD" button below it
- On save → stores to `pf-prd` in localStorage
- Shows green "PRD Captured ✓" status
- Unlocks Section 3 (Configure Build)
- Shows preview snippet (first 200 chars)
- Shows "Clear PRD" button to reset and redo

### Questionnaire Path

**Step 1 — Inject initial questionnaire:**
When user clicks "Start" button, inject this prompt into the chat:

```
I'm going to describe an app I want to build. I'll provide details in a structured format. Please acknowledge each section as I provide it, and wait for me to say I'm ready before analyzing.

Here are the basics:

**Temporary Build Name:** (this is just for identification — NOT the final product name, we'll pick that later)
**What is it?** (describe the app in 1-2 sentences)
**Who is it for?** (target user/audience)
**What problem does it solve?** (the core pain point)
**Why would anyone care?** (the value proposition)
**Core features:** (list the main things it does)
**Basic user flow:** (how someone uses it step by step)

Please fill these out as best you can in the chat, then click NEXT in the Phase Forge panel when done.
```

Status: `"Step 1 — Fill out questionnaire"`

**Step 2 — After user fills out and clicks NEXT, inject analysis prompt:**

```
Now analyze what I've provided against a complete PRD format. Rate the completeness as a percentage.

A complete PRD needs:
- App Identity (name, description, target user, problem statement)
- Feature List (prioritized, MVP-scoped, max 5-8 core features)
- Technical Stack recommendation
- Data Model (entities, relationships)
- User Flows (step by step for each core feature)
- UI/Page descriptions (what screens exist, what's on each)
- API Endpoints (if applicable)
- Testing Requirements

Based on what I've given you:
1. Show what percentage complete the PRD is
2. Show what you understood, organized by section
3. For anything missing or unclear, ask targeted follow-up questions
4. Group your questions by section

If you have enough for a complete PRD (80%+), generate it with the markers:
=== PRD READY ===
[full PRD content here]
=== END PRD ===
```

Status: `"Step 2 — Analyzing completeness"`

**Step 3+ — Loop until PRD captured:**

After each Claude response, if no `=== PRD READY ===` marker detected, show a "NEXT" button. When clicked, inject:

```
Based on what I just provided:
1. Update your completeness percentage
2. If now 80%+ complete: Generate the full PRD with === PRD READY === at the top and === END PRD === at the bottom
3. If still incomplete: Ask the remaining targeted questions needed

The PRD must be detailed enough that a coding agent can build the entire app from it without asking any clarification questions.
```

### Rant Path

**Step 1 — Inject rant invitation:**

```
I'm going to describe my app idea. It might be messy, stream of consciousness, out of order, or incomplete. That's fine.

Your job: Listen. Absorb everything. Do NOT interrupt. Do NOT organize yet. Do NOT ask questions yet. Just acknowledge you received it.

I'll click NEXT in the Phase Forge panel when I'm done explaining.
```

Status: `"Step 1 — Describe your idea freely"`

**Step 2 — After rant, inject organization prompt:**

```
Now take everything I described and:

1. Organize it into structured PRD sections:
   - App Identity (name, description, target user, problem)
   - Feature List (prioritized, MVP-scoped)
   - Technical Stack
   - Data Model
   - User Flows
   - UI/Page descriptions
   - API Endpoints
   - Testing Requirements

2. Show me what you understood (organized by section above)
3. Rate completeness as a percentage
4. Ask targeted follow-up questions ONLY for the gaps

If already 80%+ complete, generate the full PRD with:
=== PRD READY ===
[content]
=== END PRD ===
```

**Step 3+ — Same loop as Questionnaire path**

### PRD Auto-Capture

A `MutationObserver` watches Claude's responses for `=== PRD READY ===` and `=== END PRD ===` markers.

When detected:
1. Extract text between markers
2. Store in `localStorage` key `pf-prd`
3. Update status: `"PRD Captured ✓"` (green)
4. Unlock Section 3 (Configure Build)
5. Show a preview snippet of the captured PRD (first 200 chars)
6. Show "Clear PRD" button to reset and redo

### Editable Prompt Templates

All prompt text (questionnaire steps, rant steps, follow-up prompts) are editable:
- Small pencil icon (✏) next to each step label
- Click → expands an edit textarea with the current prompt text
- Edit, save → stored in localStorage key `pf-prompt-templates` as JSON, overrides defaults
- "Reset to Default" button per prompt to restore original text
- This allows prompt engineering iteration without touching code

### PRD Builder UI Elements
- Three-way mode toggle pill (I Have a PRD / Questionnaire / Rant)
- Start button
- NEXT button (appears after each AI response)
- Status text with step indicator
- PRD captured indicator (green checkmark)
- PRD preview (first 200 chars, expandable)
- Clear PRD button
- Pencil icons for editing prompt templates

---

## Feature 5: Build Configurator (Section 3)

Locked until PRD is captured. Shows 🔒 when locked.

### Model Selector
Dropdown with options:
```javascript
const MODEL_CONFIGS = {
  'claude-web':  { name: 'Claude Web',  maxTokens: 200000 },
  'codex-web':   { name: 'Codex Web',   maxTokens: 400000 },
  'gemini-web':  { name: 'Gemini Web',  maxTokens: 1000000 },
  'custom':      { name: 'Custom',      maxTokens: 200000 }  // editable
};
```
When "Custom" is selected, show an editable token count input.
Stored in `localStorage` key `pf-config-model`.

### Context Window Percentage Slider
- HTML range input
- Range: **35% to 65%**
- Default: **50%**
- Step: 5%
- Show current value as label: "Context Budget: 50%"
- This determines what percentage of max tokens to use as working budget
- Stored in `localStorage` key `pf-config-context-pct`

### Agent Role Toggles
Checkboxes for each role:

| Role | Default | Budget % | Can Disable? |
|------|---------|----------|--------------|
| Builder | ON | 40% | No (always on) |
| Reviewer | OFF | 8% | Yes |
| Architect | OFF | 8% | Yes |
| Tester | OFF | 15% | Yes |
| Planner | OFF | 5% | Yes |

Fixed overhead: 4% (system prompt, headers)
Fixed buffer: 20% (safety margin for back-and-forth)

Stored in `localStorage` key `pf-config-roles` as JSON array of active role keys.

### Token Budget Display
Calculated in real-time as user changes model/context%/roles:

```
Available: 100,000 tokens (200K × 50%)
├── Builder:   40,000 (40%)
├── Reviewer:   8,000 (8%)  [if enabled]
├── Buffer:    20,000 (20%)
├── Overhead:   4,000 (4%)
└── Free:      28,000 (28%)
```

Formula:
```
available = modelMaxTokens * (contextPercent / 100)
roleCosts = sum of each active role's percentage * available
overhead = available * 0.04
buffer = available * 0.20
builderBudget = available * 0.40
free = available - roleCosts - overhead - buffer
```

### Agent Role Directive Templates

These are prepended to each phase prompt when active. Each has a pencil (✏) edit button for customization:

**Builder (always on):**
```
=== AGENT ROLE: BUILDER (Primary) ===
You are the primary coding agent for this phase.
- Write all new code specified in the phase requirements
- Follow the PRD and phase spec exactly
- Create files, implement features, wire up imports
- Write clean, working code — optimize later
- Commit after each logical unit of work
===
```

**Reviewer:**
```
=== AGENT ROLE: REVIEWER ===
After writing each file/component, review it before moving on:
- Check for logic errors, missing edge cases
- Verify naming consistency with existing code
- Verify import paths are correct
- Flag any pattern violations against the PRD
- Fix issues immediately rather than noting them for later
===
```

**Architect:**
```
=== AGENT ROLE: ARCHITECT ===
After completing code for this phase, create/update architecture documentation:
- Create or update ARCHITECTURE.md with components added this phase
- Maintain a COMPONENT_INDEX.md listing every file with: purpose, dependencies, exports
- Document data flows between new and existing components
- This helps future agents understand the codebase in seconds instead of minutes
===
```

**Tester:**
```
=== AGENT ROLE: TESTER ===
While building this phase, also verify the PREVIOUS phase works:
- Run the shared testing script against previous phase's code
- Verify all previous features still function correctly
- Report any regressions found
- If tests fail, note what needs fixing before proceeding

{{TESTING_SCRIPT}}
===
```

**Planner:**
```
=== AGENT ROLE: PLANNER ===
Before writing code, briefly scan the NEXT phase requirements:
- Identify files that will need modification in the next phase
- Note potential conflicts with current phase's work
- Flag dependencies that current phase should prepare for
- Write a 3-5 line briefing note at the end of your response
- This is READ-ONLY analysis — do not write code for the next phase
===
```

### Shared Assets

Two textarea inputs:

**Testing Script:**
- Label: "Testing Script (injected into every phase as {{TESTING_SCRIPT}})"
- Placeholder: "Paste your testing script here. It will be appended to every phase prompt."
- Stored in `localStorage` key `pf-shared-testing-script`

**Architecture Doc:**
- Label: "Architecture Doc (injected as {{ARCHITECTURE_DOC}})"
- Placeholder: "This grows each phase. Paste initial architecture notes here."
- Stored in `localStorage` key `pf-shared-architecture`

### "Lock Configuration" Button
When clicked:
- Saves all config to localStorage
- Locks Section 3 (shows values but grayed out)
- Unlocks Section 4 (Phases)
- Shows "Edit Config" button to re-unlock

---

## Feature 6: Phase Manager (Section 4)

Locked until configuration is locked.

### Phase Import
Two options:

**Option A: Manual Import**
- "Import Phases" button opens a modal with a large textarea
- User pastes a document with phase markers:
```
--- PHASE 1: Project Setup ---
Set up the project with Next.js, install dependencies...

--- PHASE 2: Database Schema ---
Create the database models...

--- PHASE 3: Auth System ---
Implement authentication...
```
- Script splits on `--- PHASE N ---` pattern (with optional title after colon)
- Regex: `/---\s*PHASE\s*(\d+)\s*(?::\s*(.+?))?\s*---/gi`
- Each chunk becomes a phase with extracted title and content

**Option B: Auto-Split from PRD**
- "Auto-Generate Phases" button
- Injects a prompt into Claude asking it to split the captured PRD into phases:
```
Here is a PRD for an application. Split it into sequential build phases.

Rules:
- Each phase should be independently buildable
- Phase 1 is always project setup + boilerplate
- Later phases build on earlier ones
- Each phase should take roughly equal effort
- Output each phase in this EXACT format:

--- PHASE 1: [Title] ---
[Detailed requirements for this phase]

--- PHASE 2: [Title] ---
[Detailed requirements for this phase]

[Continue for all phases]

Here is the PRD:

=== PRD ===
{{CAPTURED_PRD}}
=== END PRD ===
```
- Then auto-capture the phases from Claude's response using the same `--- PHASE N ---` regex

### Phase List Display
```
┌────────────────────────────────────┐
│ Phases (9 total)                   │
├────────────────────────────────────┤
│ ✅ Phase 1: Project Setup          │
│ ✅ Phase 2: Database Schema        │
│ 🔄 Phase 3: Auth System     [3/9] │
│ ⬚ Phase 4: Dashboard              │
│ ⬚ Phase 5: API Endpoints          │
│ ⬚ Phase 6: Frontend Pages         │
│ ⬚ Phase 7: Search & Filter        │
│ ⬚ Phase 8: Polish & UX            │
│ ⬚ Phase 9: Testing & Deploy       │
├────────────────────────────────────┤
│ [Import Phases] [Auto-Generate]    │
│ [Clear All Phases]                 │
└────────────────────────────────────┘
```

Each phase item:
- Click to expand and see full content
- Status icons: `⬚` pending, `🔄` running, `✅` complete, `❌` failed
- Edit button (pencil icon) opens phase content in an editor modal

Phase data stored in `localStorage` key `pf-phases` as:
```javascript
[
  { id: 1, title: "Project Setup", content: "...", status: "complete" },
  { id: 2, title: "Database Schema", content: "...", status: "complete" },
  { id: 3, title: "Auth System", content: "...", status: "running" },
  { id: 4, title: "Dashboard", content: "...", status: "pending" },
  // ...
]
```

---

## Feature 7: Phase Runner Engine (Section 5)

Locked until at least 1 phase exists.

### Runner Controls
```
┌──────────────────────────────────────┐
│ Phase Runner                         │
├──────────────────────────────────────┤
│ ██████████░░░░░░░░░░ 3/9 (33%)     │
│ Status: Running Phase 3...           │
│                                      │
│ [▶ Start] [⏸ Pause] [⏹ Stop]       │
│                                      │
│ Auto-retry on error: [✓]            │
│ Delay between phases: [3] seconds    │
└──────────────────────────────────────┘
```

### Auto-Send Flow

When "Start" is clicked:

1. **Build the full prompt** for the current phase:
```
[Agent Directives — only active roles]

=== SHARED ASSETS ===
[Testing script if provided]
[Architecture doc if provided]

=== PROJECT REPO ===
[Repo URL if provided]

=== PHASE [N] of [TOTAL] ===
[Phase title]

[Phase content]

=== INSTRUCTIONS ===
When you are completely finished with this phase, end your response with:
=== PHASE COMPLETE ===
```

2. **Inject** the prompt into the chat input using existing `injectPrompt()` function
3. **Wait 500ms** then click the send button
4. **Start completion watcher** (MutationObserver)
5. **On completion detected:**
   - Check for `=== PHASE COMPLETE ===` in response → mark phase ✅
   - Check for error indicators → mark phase ❌, optionally auto-retry
   - If paused → stop, show "Paused after Phase N"
   - If more phases → wait `delayBetweenPhases` seconds → send next phase
6. **On all phases done:** show "Build Complete!" with green status

### Completion Detection Engine

```javascript
// Core logic:
// 1. MutationObserver watches the chat container for DOM changes
// 2. Track timestamp of last mutation
// 3. Poll every 1 second: if (now - lastMutation > 4000ms) AND sendButtonAvailable → complete
// 4. Also detect: retry buttons, error messages, rate limit notices
```

**Chat container selectors to try (in order):**
- `[data-testid="conversation-turn-list"]` (Claude.ai)
- `main` (general fallback)
- `div.conversation` (ChatGPT)
- `div[role="main"]` (Gemini)

**Send button selectors to try (in order):**
- `button[aria-label="Send Message"]` (Claude.ai)
- `button[data-testid="send-button"]` (ChatGPT)
- `button[aria-label="Send"]` (generic)
- Any non-disabled button with an SVG arrow icon near the input area
- The approach: find the editor element, go up to its form/container, find buttons within

**Rate limit / error detection:**
- Look for text containing "rate limit", "try again", "error", "something went wrong"
- Look for retry buttons
- If auto-retry enabled: wait 30 seconds, then retry the same phase

### Placeholder Replacement

Before sending any phase, replace these placeholders in the full prompt:
- `{{TESTING_SCRIPT}}` → contents of shared testing script textarea
- `{{ARCHITECTURE_DOC}}` → contents of shared architecture doc textarea
- `{{CAPTURED_PRD}}` → the captured PRD text
- `{{REPO_URL}}` → the saved GitHub repository URL
- `{{PHASE_NUMBER}}` → current phase number
- `{{TOTAL_PHASES}}` → total number of phases

### Runner State Persistence

Stored in `localStorage` key `pf-runner-state`:
```javascript
{
  currentPhaseIndex: 2,   // 0-based index
  status: "running",      // "idle" | "running" | "paused" | "stopped" | "complete"
  autoRetry: true,
  delayBetweenPhases: 3   // seconds
}
```

On page reload: if status was "running", show "Runner was interrupted. Resume from Phase N?" prompt.

---

## Feature 8: All localStorage Keys

| Key | Type | Description |
|-----|------|-------------|
| `cpi-custom-prompts` | JSON array | Prompt injector button content (existing) |
| `cpi-zoom-level` | number | Prompt injector zoom % (existing) |
| `pf-panel-open` | boolean | Phase Forge panel visibility |
| `pf-project-name` | string | Current project name |
| `pf-repo-url` | string | GitHub repository URL |
| `pf-prd-mode` | string | "have-prd", "questionnaire", or "rant" |
| `pf-prd` | string | Captured PRD text |
| `pf-prd-step` | number | Current PRD builder step |
| `pf-prompt-templates` | JSON object | Custom-edited prompt templates |
| `pf-config-model` | string | Model key |
| `pf-config-custom-tokens` | number | Custom model token count |
| `pf-config-context-pct` | number | Context window percentage (35-65) |
| `pf-config-roles` | JSON array | Active role keys |
| `pf-config-locked` | boolean | Configuration locked |
| `pf-shared-testing-script` | string | Testing script content |
| `pf-shared-architecture` | string | Architecture doc content |
| `pf-phases` | JSON array | Phase data (id, title, content, status) |
| `pf-runner-state` | JSON object | Runner current state |

---

## Technical Constraints

1. **Single file** — everything in one `.js` userscript file
2. **No external dependencies** — pure vanilla JS, no frameworks
3. **All CSS inline** — created via `document.createElement('style')`
4. **All HTML via DOM API** — `document.createElement()`, no `innerHTML` (XSS safety)
5. **No backend** — everything runs client-side, persists in localStorage
6. **No API keys** — all AI interaction happens through the host page's chat interface
7. **Background tab safe** — MutationObserver and setInterval work when tab is inactive
8. **Must not break host page** — use unique prefixed IDs/classes (`cpi-` for prompt injector, `pf-` for Phase Forge)
9. **Clear visual separation** — prompt injector and Phase Forge panel are visually distinct components

## File Structure

```javascript
// ==UserScript==
// @name         Phase Forge - AI Build Orchestrator
// @namespace    https://github.com/digisurfsome/Greptacular
// @version      2.0
// @description  Multi-phase build orchestrator with PRD builder, agent roles, and auto-send for Claude/ChatGPT/Gemini
// @author       AutoForge
// @match        https://claude.ai/*
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://gemini.google.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ===== SECTION: Constants & Config =====
  // Model configs, agent role definitions, storage keys, defaults

  // ===== SECTION: Storage Helpers =====
  // Load/save functions for all localStorage keys

  // ===== SECTION: Site Detection =====
  // Auto-detect Claude/ChatGPT/Gemini and set appropriate selectors

  // ===== SECTION: CSS Styles =====
  // All styles for prompt injector + Phase Forge panel

  // ===== SECTION: DOM Utilities =====
  // getEditor(), injectPrompt(), findSendButton(), clickSendButton()

  // ===== SECTION: Completion Detection =====
  // MutationObserver-based engine for detecting when AI finishes responding

  // ===== SECTION: Prompt Injector (existing, improved) =====
  // PROMPTS array, zoom pill, editor overlay, prompt grid panel

  // ===== SECTION: Phase Forge State =====
  // Reactive state for repo, PRD, config, phases, runner

  // ===== SECTION: GitHub Repository =====
  // Repo setup instructions, URL input, skip option

  // ===== SECTION: PRD Builder Engine =====
  // Three-way toggle, paste PRD, questionnaire, rant, step management, PRD capture

  // ===== SECTION: Editable Prompt Templates =====
  // Edit UI for all injected prompts, localStorage override, reset to default

  // ===== SECTION: Build Configurator =====
  // Model selection, context % calc, role toggles, budget calculator

  // ===== SECTION: Phase Manager =====
  // Phase import/parse, phase list management, phase editing

  // ===== SECTION: Phase Runner Engine =====
  // Auto-send loop, retry logic, progress tracking

  // ===== SECTION: Phase Forge Panel UI =====
  // Build the full sidebar panel with all sections

  // ===== SECTION: Init =====
  // Wait for page ready, build both panels

})();
```

---

## Success Criteria

1. Existing prompt injector works exactly as before (20 buttons, editor, injection)
2. Zoom pill buttons are full-width, 36px tall, usable at small zoom levels
3. Prompt injector and Phase Forge panel are visually distinct — clear separation
4. Phase Forge panel toggles on/off via floating "PF" button
5. GitHub repo section has beginner-friendly instructions and URL input
6. PRD Builder works in all three modes: I Have a PRD, Questionnaire, and Rant
7. PRD is auto-captured when AI outputs the markers
8. All prompt templates are editable via pencil icons without touching code
9. Configuration section calculates token budgets correctly
10. Phases can be imported manually or auto-generated
11. Phase Runner auto-sends phases, detects completion, advances to next
12. All state persists across page reloads via localStorage
13. Works on Claude.ai (primary), ChatGPT and Gemini (secondary)
14. Auto-detects which site and adjusts selectors/positioning accordingly
