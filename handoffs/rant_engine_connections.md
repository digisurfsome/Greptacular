# Handoff #2: Rant-to-Spec Engine — Three Connection Modes

## Agent Instructions

The core Rant-to-Spec Engine (see `handoffs/rant_to_spec_engine.md`) is a framework-agnostic Python module. This handoff covers connecting that engine to three delivery modes. **All three use the exact same engine** — the difference is the frame: how users interact with it, where it lives, and how output flows.

Study the AutoForge codebase thoroughly before implementing. The engine integration points, UI patterns, API architecture, and WebSocket conventions are already established — follow them.

---

## The Three Modes

```
┌─────────────────────────────────────────────────────────────┐
│                    RANT-TO-SPEC ENGINE                       │
│                    (Core Python Module)                       │
└─────────┬──────────────────┬──────────────────┬─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌────────────────┐ ┌─────────────────────┐
│  CONNECTION A   │ │  CONNECTION B  │ │    CONNECTION C      │
│  AutoForge      │ │  Standalone    │ │    Mobile/Web Admin  │
│  Build Process  │ │  App           │ │    Panel             │
│                 │ │                │ │                      │
│ Integrated into │ │ Independent    │ │ In-app admin area    │
│ /create-spec    │ │ web app with   │ │ for capturing ideas  │
│ flow. Engine    │ │ its own UI.    │ │ on the go. Minimal   │
│ powers the spec │ │ Full rant-to-  │ │ capture UI, syncs    │
│ creation step   │ │ spec workflow  │ │ to saved sessions    │
│ before build.   │ │ with save/     │ │ for later review.    │
│                 │ │ resume.        │ │                      │
└─────────────────┘ └────────────────┘ └─────────────────────┘
```

---

## Connection A: AutoForge Build Process Integration

### What It Does

Integrates the Rant-to-Spec Engine into AutoForge's existing spec creation flow. When a user creates a new project, instead of (or in addition to) the current spec creation chat, they can dump a raw rant and the engine transforms it into a proper `app_spec.txt`.

### Where It Fits in AutoForge

Study these existing files:
- `server/routers/spec_creation.py` — Current WebSocket-based spec creation
- `server/services/spec_chat_session.py` — Current spec chat session logic
- `.claude/commands/create-spec.md` — CLI spec creation command
- `.claude/templates/initializer_prompt.template.md` — What the spec feeds into
- `ui/src/components/ExpandProjectModal.tsx` — UI pattern for project modification flows

### Implementation Plan

#### Backend Changes

1. **New router:** `server/routers/rant_spec.py`
   - `POST /api/projects/{name}/rant-spec/start` — Start a new rant session
     - Body: `{ raw_rant: string, profile?: string | PriorityProfile }`
     - Returns: `RantSession` (after Stage 1+2 complete)
   - `GET /api/projects/{name}/rant-spec/session` — Get current session state
   - `POST /api/projects/{name}/rant-spec/research` — Trigger Stage 3 (research)
     - Body: `{ decision_ids?: string[] }` (optional, defaults to all Deep)
   - `POST /api/projects/{name}/rant-spec/resolve` — Resolve a decision
     - Body: `{ decision_id: string, chosen_option: string, notes?: string }`
   - `POST /api/projects/{name}/rant-spec/developers-choice` — Accept dev choice
     - Body: `{ decision_id?: string }` (omit for "accept all")
   - `POST /api/projects/{name}/rant-spec/assemble` — Run Stage 5, generate spec
   - `POST /api/projects/{name}/rant-spec/weight` — Reweight with new profile
     - Body: `PriorityProfile`
   - `WebSocket /ws/projects/{name}/rant-spec` — Real-time progress updates
     - Emits: `stage_progress`, `decision_classified`, `research_complete`, `spec_ready`

2. **New service:** `server/services/rant_spec_service.py`
   - Wraps `RantEngine` with project-aware logic
   - Saves sessions to `{project_dir}/.autoforge/rant_sessions/`
   - Connects engine events to WebSocket broadcasts

3. **Integration point:** In `server/routers/projects.py`, add rant-spec as an alternative project creation path
   - New project flow: Create project → Choose "Rant my idea" OR "Structured spec" → Engine produces `app_spec.txt` → Normal initializer agent takes over

#### Frontend Changes

4. **New component:** `ui/src/components/RantSpecFlow.tsx`
   - Large text area for rant input (no formatting required — raw dump)
   - "Process My Idea" button → calls start endpoint
   - Progress visualization as engine processes stages
   - Decision review panel:
     - **Autopilot section:** Collapsed by default, shows what was auto-decided (expandable)
     - **Soft section:** Quick confirm cards — show recommendation + one-click accept
     - **Deep section:** Full decision templates with:
       - Options grid (summary view)
       - Expand button for deep explanation of each option
       - Developer's Choice highlighted with confidence badge
       - "Accept Dev Choice" button per decision
     - **"Accept All Developer's Choices"** master button at the top
     - Priority profile selector (dropdown of built-in profiles + custom)
   - Final review → "Generate Spec" → shows assembled spec → "Start Building"

5. **Entry point:** Add "Rant My Idea" option to project creation flow
   - In the project creation modal/page, add alongside existing spec creation
   - Use a toggle or tab: "Structured Spec" | "Rant My Idea"

6. **Decision template component:** `ui/src/components/DecisionTemplate.tsx`
   - Reusable card for rendering a Decision
   - Confidence meter (visual bar/circle with %)
   - Developer's Choice badge with expandable explanation
   - Option comparison grid
   - Dimension relevance indicators (only show relevant ones)

#### UI Design Notes

Follow AutoForge's existing neobrutalism design system:
- Use the CSS variables from `ui/src/styles/globals.css`
- Decision confidence → use `--color-neo-done` (green) for high, `--color-neo-pending` (yellow) for medium, red accent for low
- Autopilot items → subtle, muted styling (they're handled, don't need attention)
- Deep items → bold borders, prominent placement
- Developer's Choice → special badge styling, distinct from regular recommendations

---

## Connection B: Standalone App

### What It Does

A completely independent web application for idea capture and spec generation. No AutoForge dependency. Users can:
- Dump rants anytime
- Save sessions for later
- Review and resolve decisions at their own pace
- Export finished specs (AutoForge XML, plain text, markdown, or JSON)
- Manage a library of idea sessions

### Tech Stack

Use the same stack as AutoForge's UI (shared knowledge base for the developer):
- **Backend:** FastAPI (Python) — wraps the engine
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, Radix UI
- **Database:** SQLite for session storage (via SQLAlchemy)
- **Auth:** Simple local auth (email/password) — this is a personal tool

### Implementation Plan

#### Project Structure

```
rant-app/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── database.py          # SQLAlchemy models for sessions, users
│   ├── routers/
│   │   ├── sessions.py      # CRUD for rant sessions
│   │   ├── decisions.py     # Decision resolution endpoints
│   │   └── export.py        # Spec export in multiple formats
│   └── requirements.txt     # Includes rant_engine as dependency
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # Session library overview
│   │   │   ├── NewRant.tsx        # Rant input page
│   │   │   ├── SessionReview.tsx  # Decision review/resolution
│   │   │   └── SpecPreview.tsx    # Final spec viewer + export
│   │   ├── components/
│   │   │   ├── RantInput.tsx           # Big text area with voice hint
│   │   │   ├── StageProgress.tsx       # Pipeline progress visualization
│   │   │   ├── DecisionCard.tsx        # Individual decision template
│   │   │   ├── DecisionGrid.tsx        # All decisions in sortable grid
│   │   │   ├── DevChoiceBanner.tsx     # "Accept All Dev Choices" CTA
│   │   │   ├── PrioritySliders.tsx     # Visual priority profile editor
│   │   │   ├── ConfidenceMeter.tsx     # Visual confidence indicator
│   │   │   └── ExportOptions.tsx       # Format selection for export
│   │   └── hooks/
│   │       ├── useRantSession.ts  # Session state management
│   │       └── useWebSocket.ts    # Real-time engine progress
│   └── package.json
├── init.sh
└── app_spec.txt             # This app's own spec (meta!)
```

#### Key Pages

**Dashboard (Session Library):**
- Grid of saved sessions with status badges (raw, processing, decisions pending, complete)
- Quick stats: X ideas captured, Y specs complete, Z decisions pending
- Sort by date, status, completeness
- "New Rant" prominent CTA

**New Rant Page:**
- Giant text area (full viewport height minus header)
- Placeholder text: "Just start typing. No structure needed. Brain dump your app idea..."
- Word count indicator
- Optional: profile selector before processing
- "Process My Idea" button → transitions to review page with real-time progress

**Session Review Page:**
- Three-tab layout: Autopilot | Needs Confirmation | Deep Decisions
- Or single page with sections, collapsible
- Each decision as a card with:
  - Title + context
  - Options comparison (grid or accordion)
  - Developer's Choice prominently displayed
  - Confidence meter
  - "Accept Dev Choice" / "Choose Manually" toggle
  - If choosing manually: option selector with reasoning field
- Top bar: session progress (X of Y decisions resolved)
- "Accept All Developer's Choices" floating action button
- "Re-weight" button → opens priority profile sliders

**Spec Preview + Export:**
- Rendered spec view (syntax highlighted XML + human-readable summary)
- Decisions audit log (what was decided and why)
- Export buttons: AutoForge XML, Markdown, JSON, Plain Text
- "Send to AutoForge" button (if AutoForge is configured — generates project and copies spec)

#### Backend API

```
POST   /api/sessions                    # Start new rant session
GET    /api/sessions                    # List all sessions
GET    /api/sessions/:id                # Get session detail
DELETE /api/sessions/:id                # Delete session
PATCH  /api/sessions/:id/rant          # Update rant text (add more)
POST   /api/sessions/:id/process       # Run engine pipeline
POST   /api/sessions/:id/research      # Run research stage
POST   /api/sessions/:id/resolve       # Resolve a decision
POST   /api/sessions/:id/dev-choice    # Accept developer's choice (one or all)
POST   /api/sessions/:id/reweight      # Apply new priority profile
POST   /api/sessions/:id/assemble      # Generate final spec
GET    /api/sessions/:id/export/:fmt   # Export spec (xml, md, json, txt)
WS     /ws/sessions/:id                # Real-time progress
GET    /api/profiles                    # List priority profiles
POST   /api/profiles                   # Save custom profile
```

---

## Connection C: Mobile/Web Admin Panel

### What It Does

A lightweight capture interface designed for on-the-go idea capture. When you're out and an idea hits, you need to get it down FAST with minimal friction. This isn't the full review experience — it's the "emergency capture" mode that syncs to your saved sessions for later review.

### Where It Lives

This is an additional route/panel within either:
- The Standalone App (Connection B) — as a `/capture` mobile-optimized route
- OR as a panel within a generated app's admin area (if the user builds apps with AutoForge that have admin panels)

**Recommended approach:** Build it as a mobile-optimized route within Connection B that can ALSO be embedded as an iframe or micro-frontend in other apps.

### Implementation Plan

#### Mobile Capture Page: `/capture`

Ultra-minimal UI optimized for speed:
- Full-screen text area (no chrome, no distractions)
- Auto-saves every 5 seconds to prevent data loss
- "Save & Process Later" button (saves raw, queues for processing)
- "Save & Process Now" button (saves and kicks off engine immediately)
- Optional: voice input button (uses browser Web Speech API for transcription)
- Session title auto-generated from first sentence

#### Design Principles
- **Sub-second to first keystroke** — page loads with cursor in text area
- **Zero mandatory fields** — just start typing
- **Offline capable** — save to localStorage, sync when connected (via service worker)
- **No decisions on this screen** — capture only. Review happens later on desktop or full mobile view
- **Swipe gestures** — swipe right to save and start new, swipe left to discard

#### Quick Review Mode: `/capture/review`

Simplified decision review for mobile (not the full grid):
- Vertical card stack (swipe-based like Tinder for decisions)
- Each card: decision title, developer's choice, confidence
- Swipe right = accept dev choice
- Swipe left = skip (review later on desktop)
- Tap = expand for details
- Big "Accept All Remaining" button at bottom

#### API (extends Connection B's backend)

```
POST   /api/capture                     # Quick save a rant (minimal fields)
GET    /api/capture/pending             # Get rants saved but not yet processed
POST   /api/capture/:id/process        # Queue for processing
GET    /api/capture/decisions/pending   # All unresolved decisions across all sessions
POST   /api/capture/decisions/swipe     # Batch resolve (accept/skip)
```

#### Embeddable Widget

For embedding in other apps' admin panels:

```html
<!-- Drop this in any admin panel -->
<iframe
  src="https://your-rant-app.com/capture?embed=true&token=USER_TOKEN"
  style="width: 100%; height: 100vh; border: none;"
></iframe>
```

Or as a React component:
```tsx
import { RantCapture } from '@your-org/rant-capture-widget';

// In your admin panel
<RantCapture
  apiUrl="https://your-rant-app.com/api"
  token={userToken}
  onSaved={(sessionId) => console.log('Captured:', sessionId)}
/>
```

---

## Shared Components Across All Three Connections

These UI components should be built ONCE in a shared package and imported by all three modes:

| Component | What It Does |
|-----------|-------------|
| `DecisionCard` | Renders a single decision with options, dev choice, confidence |
| `ConfidenceMeter` | Visual confidence indicator (circular or bar) |
| `DevChoiceBadge` | "Developer's Choice" badge with expand for explanation |
| `PrioritySliders` | Visual priority profile editor (sliders for each dimension) |
| `StageProgress` | Pipeline progress visualization (5 stages) |
| `OptionComparisonGrid` | Side-by-side option comparison table |
| `DimensionTag` | Tag showing a relevant dimension (vendor lock-in, security, etc.) |

Build these in a shared location:
- If within AutoForge: `ui/src/components/rant/`
- If standalone: `frontend/src/components/shared/`

---

## Implementation Order

1. **Connection A (AutoForge integration)** — Highest value, existing codebase to build on, immediate benefit to the AutoForge workflow. The engine replaces/augments the current spec creation chat.

2. **Connection B (Standalone app)** — Second priority. Use AutoForge itself to build this app (the meta play). Create the app_spec.txt from the engine handoff, run it through AutoForge, get the standalone app built.

3. **Connection C (Mobile capture)** — Built as an extension of Connection B. Once B exists, C is just a mobile-optimized route + offline capability + the swipe review interface.

---

## Integration Between Modes

All three modes can share the same backend session storage:

```
Sessions saved in Connection C (mobile capture)
    → Appear in Connection B (standalone) for full review
    → Can be imported into Connection A (AutoForge) to create a project

Sessions created in Connection A (AutoForge spec creation)
    → Can be exported and viewed in Connection B
    → Decisions visible in Connection C for mobile review
```

The bridge: a shared session format (the `RantSession` JSON from the engine). Any mode can read/write this format. Cross-mode sync is just file/API exchange of the same JSON structure.

---

## What This Agent Should Do

1. Study the AutoForge codebase thoroughly (especially the files listed in Connection A)
2. Implement Connection A first (AutoForge integration)
3. Create the shared UI components
4. Build Connection B as a standalone app (can use AutoForge to bootstrap it)
5. Add Connection C as a mobile route within Connection B
6. Test all three modes work with the same engine and can share sessions

**Prerequisites:** The core Rant-to-Spec Engine (Handoff #1) must be built first. This agent assumes `rant_engine/` exists as an importable package.
