# Build Agent 5 — Phase 5: Live Execution Viewer + Phase 6: Pause/Resume/Takeover

## What You're Building

You are building **two tightly coupled features** inside the **YT Strategy Lab** system in the AutoForge application (Greptacular codebase). YT Strategy Lab is a platform for extracting actionable strategies from YouTube videos and executing them with AI agents.

**Feature A (Phase 5):** The split-screen live execution viewer — a 280px sidebar with step tracker + agent log, a 48px top bar with controls, and a noVNC iframe showing the agent's browser in real-time.

**Feature B (Phase 6):** Pause/resume/takeover controls — the state machine and UI that lets users pause the agent, chat with it, take over the browser manually, and resume.

**Prerequisites:** Phase 4 (Computer Use Engine) must be done. You'll be building the UI that connects to Phase 4's API endpoints and WebSocket.

---

## Step 1: Read These Documents (In This Order)

**Do not write any code until you have read all documents and confirmed your understanding.**

1. **Vision Document** — Read this FIRST. It explains what this system actually IS:
   ```
   docs/yt-strategies/VISION.md
   ```

2. **Context Primer** — Technical architecture and patterns:
   ```
   docs/yt-strategies/CONTEXT_PRIMER.md
   ```

3. **PRD for Live Execution Viewer** (Feature A):
   ```
   docs/yt-strategies/prds/03-live-execution-viewer.md
   ```

4. **PRD for Pause/Resume/Takeover** (Feature B):
   ```
   docs/yt-strategies/prds/05-pause-resume-takeover.md
   ```

5. **Build Standards**:
   ```
   .claude/build-prompts/App Builder Prompt Template (Platform-Agnostic).txt
   ```

6. **Also read Phase 4's PRD** for API/WebSocket interface understanding:
   ```
   docs/yt-strategies/prds/02-custom-computer-use-engine.md
   ```

---

## Step 2: Prove Understanding

Before writing code, briefly state:
1. The split-screen layout dimensions and what goes where
2. The full state machine: IDLE → RUNNING → PAUSED → TAKEOVER → COMPLETE
3. How the WebSocket events stream from backend to UI
4. The complete list of files you will create or modify

---

## Step 3A: Build Live Execution Viewer (Phase 5)

### Components to Create

- **`ui/src/components/yt-lab/ExecutionViewer.tsx`** — Main split-screen layout:
  - Left sidebar: 280px (step tracker top, agent log bottom)
  - Top bar: 48px (project info, chat input, controls)
  - Main area: noVNC iframe (remaining space)
  - Responsive: sidebar collapses to icons at <1200px, full-screen browser at <768px

- **`ui/src/components/yt-lab/StepTracker.tsx`** — Left sidebar top half:
  - Numbered step list with status indicators: ✓ (done/green), ● (active/cyan pulse), ○ (pending/gray)
  - Active step highlighted with accent border
  - Progress bar at top showing overall completion
  - Click step for details popover

- **`ui/src/components/yt-lab/AgentLog.tsx`** — Left sidebar bottom half:
  - Real-time scrolling log with timestamps
  - Color-coded entries: actions (blue), thinking (gray), errors (red), success (green)
  - Auto-scroll to bottom, user can scroll up to review

- **`ui/src/components/yt-lab/BrowserView.tsx`** — noVNC iframe wrapper:
  - iframe connecting to noVNC WebSocket
  - View-only by default (user watches)
  - Interactive in takeover mode
  - Maintains display aspect ratio with black letterboxing

- **`ui/src/hooks/useExecutionWebSocket.ts`** — WebSocket hook:
  - Connect to `/ws/execution/{session_id}`
  - Handle events: status_change, agent_action, agent_thinking, step_change, screenshot, error
  - Follow existing `ui/src/hooks/useWebSocket.ts` patterns

### Integration
- Add execution viewer as a new view state in `YTStrategyLabPage.tsx`
- "Run" button on a step or project transitions to execution viewer
- Add types to `ui/src/lib/types.ts` (ExecutionEvent union type)

---

## Step 3B: Build Pause/Resume/Takeover (Phase 6)

### Execution Controls Bar (integrated into top bar)

- **`ui/src/components/yt-lab/ExecutionTopBar.tsx`** — Top bar with:
  - Left: Project name, current step, "Step X of Y"
  - Center: Chat input ("Talk to the agent...")
  - Right: Model indicator, state-dependent buttons:
    - Running → Pause button
    - Paused → Resume + Take Over buttons
    - Takeover → "Return Control" button (amber)
    - Always → Stop button (destructive)

### State Machine
- Manage execution state: `idle | running | paused | takeover | completed | error`
- State transitions trigger API calls:
  - Pause → `POST /api/execution/{id}/pause`
  - Resume → `POST /api/execution/{id}/resume`
  - Take Over → `POST /api/execution/{id}/takeover` with `enable: true`
  - Return Control → `POST /api/execution/{id}/takeover` with `enable: false`
  - Inject message → `POST /api/execution/{id}/inject`
  - Stop → `POST /api/execution/{id}/stop`

### Takeover Mode
- noVNC switches from view-only to interactive (`vnc.viewOnly = false`)
- Top bar shows "YOU ARE IN CONTROL" indicator
- On return: screenshot taken, agent receives context about what user did

### Chat Messages
- Chat input in top bar sends messages via inject endpoint
- Messages appear in agent log with "YOU:" prefix
- Agent responses appear with "AGENT:" prefix

---

## Step 4: Quick Verification

After building, run:
```bash
cd ui && npm run lint && npm run build
cd .. && ruff check server/
```

Fix any errors. Commit your work.

---

## Step 5: Follow Post-Build Verification Protocol

After the build compiles clean, execute the full verification protocol:
```
.claude/templates/e2e_verification_prompt.template.md
```
Read it. Follow all 8 phases. Fix any issues found.

---

## Important

- **Both features depend on Phase 4** — check that `server/routers/execution.py` and `server/services/computer_use_agent.py` exist from Agent 3's work.
- These two features are tightly coupled — Phase 6 adds controls to Phase 5's layout. Build them together.
- Follow `ui/WORKSPACE_STANDARDS.md` for layout, responsive behavior, loading/error states.
- Stay under 50% context window if possible. If verification pushes you to 55-60%, that's acceptable.
- Commit with clear messages. Push to your branch when done.
