# DunkStack System Guide

Technical reference for the DunkStack agent interface. Written for future agents and non-coder humans alike.

Last updated: 2026-03-03

---

## 1. What Is DunkStack?

DunkStack is AutoForge's autonomous coding agent interface. It launches a Claude SDK agent inside a project directory and provides a dashboard to monitor, communicate with, and control that agent in real time. The core innovation is a **two-channel communication pattern** that minimizes API costs while maximizing agent capability. Instead of burning expensive API tokens on every human-to-agent message, DunkStack uses a free file-based "walkie-talkie" channel for most communication, reserving the API channel only for the initial session start and rare follow-up instructions.

---

## 2. The Two-Channel Architecture

This is the central design idea. There are two ways to talk to the agent, and they have very different costs.

### Channel 1: API Chat (the expensive channel)

- Located in the **left column** of the DunkStack UI.
- Each message sent here is a real Claude API call.
- Message history grows with each exchange (because the Claude SDK maintains conversation context).
- Typing a message in the API Chat when no agent is running will **auto-start** the agent.
- **Use sparingly.** The first message ("hi", or a task description) starts the session. After that, prefer the walkie-talkie.

**How it works technically:**
- The frontend calls `dunkstackSendToAgent(projectName, message)` which hits `POST /api/dunkstack/agent/send`.
- The backend calls `session.send_message(message)` on the `DunkStackCodingSession`, which calls `client.query(message)` on the Claude SDK client.
- The response streams back via WebSocket as `agent_event` messages.

### Channel 2: Walkie-Talkie (the free channel)

- Located in the **right column** of the DunkStack UI (the largest column, ~50% width).
- Messages are written to **files** in the `.agent/comms/` directory:
  - `from_human.md` -- messages from the human to the agent
  - `to_human.md` -- messages from the agent to the human
  - `control.md` -- session control signals (idle/continue/autopilot)
- The agent reads these files as part of its normal tool-call workflow. No additional API calls are needed.
- **Cost: zero.** Reading a file the agent is already working next to costs nothing extra.

**How it works technically:**
- The frontend calls `dunkstackWriteFromHuman(content, title)` which hits `POST /api/dunkstack/comms/from-human`.
- The backend appends a timestamped markdown entry to `.agent/comms/from_human.md`.
- The agent's system prompt instructs it to check `from_human.md` periodically (at tool-call boundaries).
- The agent writes responses to `.agent/comms/to_human.md`.
- The frontend polls both files every 3 seconds via `dunkstackReadToHuman()` and `dunkstackReadFromHuman()`.
- A WebSocket at `/api/dunkstack/ws` also pushes `comms_update` events for faster updates.

**The analogy:** API Chat is like a cell phone call -- high quality, but every minute costs money. The walkie-talkie is like a walkie-talkie -- free, always on, and the agent checks it every time it picks up a tool (5-10 times per minute during active work).

---

## 3. The File Cabinet System

The `.agent/` directory is the agent's "filing cabinet" -- an organized set of files that sit alongside the agent during a session. This extends the agent's effective context capacity dramatically because the agent does not load all documents into its context window at once. Instead, it reads summaries and indexes first, then dives into specific files only when needed.

### Directory structure

```
.agent/
  index.md              -- Master file map. 1-sentence summary of every file.
  system_prompt.md      -- The agent's operating instructions (loaded as system prompt).
  working_memory.md     -- Agent's scratchpad for current session state.
  bridge.md             -- Handoff data from previous session.
  comms/
    from_human.md       -- Human-to-agent messages (walkie-talkie input).
    to_human.md         -- Agent-to-human messages (walkie-talkie output).
    control.md          -- Session control mode signal (idle/continue/autopilot).
  knowledge/            -- PRDs, build instructions, guidance files.
  output/               -- Implementation plans, generated artifacts.
  progress/             -- Build logs, progress tracking.
  settings/
    config.yml          -- Safety thresholds, mode config, model settings.
```

### How the agent uses it

1. On startup, the agent reads `index.md` to understand what files are available.
2. It reads `working_memory.md` to recover any in-progress state.
3. If `bridge.md` has content, it reads the handoff from the previous session.
4. It reads `from_human.md` for any pending instructions.
5. It reads `control.md` to know its operating mode.
6. Only then does it begin working.

The key insight is that the agent "thumbs through" summaries first -- it does not read every document cover to cover. This keeps context usage low while still giving the agent access to extensive reference material in the `knowledge/` folder.

---

## 4. Session Control Modes

The session control mode is stored in `.agent/comms/control.md` and can be changed from the Safety Panel in the UI. Three modes exist:

### Idle

- Agent pauses at each tool-call boundary, waiting up to 5 minutes for human input.
- Like a real-time conversation through the walkie-talkie.
- Best for: interactive debugging, code review, pair programming.

### Continue

- No pauses. Agent keeps working through tasks without waiting.
- You must keep work queued up (in `from_human.md` or in the task files) or the agent will finish and the session ends.
- Best for: implementing a known list of tasks.

### Autopilot

- Hybrid algorithm that stalls when it thinks the human is writing (to avoid interrupting), and proceeds when there is work to do.
- Best for: background operation where you occasionally drop in with instructions.

**How it works technically:**
- The frontend calls `dunkstackUpdateControl(mode, message)` which hits `POST /api/dunkstack/control`.
- The backend writes the mode to `.agent/comms/control.md`.
- A `control_update` event is broadcast via WebSocket.
- The agent reads `control.md` at startup and between tasks. The actual pause/continue behavior depends on the agent's system prompt instructions (in `.agent/system_prompt.md`), which tell it how to interpret each mode.

---

## 5. Context Safety

The context gauge (colored bar below the nav) tracks cumulative token usage against the model's context window limit. Four tiers:

| Tier | Label | Threshold | Color | Action |
|------|-------|-----------|-------|--------|
| 0 | OK | 0-45% | Green | Normal operation |
| 1 | WARNING | 45% | Yellow/Orange | Start wrapping up current work |
| 2 | HANDOFF | 47.5% | Orange | Write bridge save, prepare to hand off |
| 3 | HARD STOP | 50% | Red | Stop immediately |

**How it works technically:**
- The `DunkStackCodingSession` reports token usage after each API response via `_report_token_usage()`, which calls the in-process `record_tokens()` function.
- The dunkstack router maintains cumulative token counters and computes `usage_percent = (input + output) / model_limit * 100`.
- Safety tier is computed based on configurable thresholds in `.agent/settings/config.yml`.
- Updates are broadcast via WebSocket as `token_update` events.
- The `DunkStackContextGauge` component renders the bar with zone markers at 70%, 85%, and 90%.
- The `DunkStackSafetyPanel` shows the tier indicators with active states.

**Note on thresholds:** The default thresholds (45/47.5/50%) are conservative. The gauge bar visual zones (green/yellow/orange/red) use different breakpoints (70/85/90%) for the color gradient. The safety tiers and gauge colors are independent systems -- the safety tiers control agent behavior, the gauge colors are visual feedback for the human.

---

## 6. Bridge Save (Session Handoff)

Bridge save creates a snapshot of the current session state so the next agent session can pick up where this one left off. The data is written to `.agent/bridge.md`.

### What gets saved

- **Reason** for the handoff (manual, context limit, error).
- **Current task** -- what the agent was working on.
- **Progress** -- what is done, what is in progress.
- **Next steps** -- what should be done next.
- **Open questions** -- unresolved decisions or blockers.

### How it works

- The human clicks "Save Bridge State" in the Safety Panel, or the agent auto-saves when context safety hits the HANDOFF tier.
- The frontend calls `dunkstackSaveBridge(data)` which hits `POST /api/dunkstack/bridge/save`.
- The backend writes a timestamped YAML/markdown block to `.agent/bridge.md`.
- A `bridge_saved` event is broadcast via WebSocket.
- On the next session start, the agent's bootstrap message instructs it to read `bridge.md` and incorporate the context (step 3 of the startup sequence).

---

## 7. UI Layout

The DunkStack page is a full-screen layout at the `/#/dunkstack` route. It has these major sections:

### Top Navigation Bar
- Back button to AutoForge main page.
- "DunkStack" label with the Layers icon.
- **Model preset pills** -- switch between Opus 4.6 200K, Opus 4.6 1M, and Sonnet 4.6 1M. Selection persists to localStorage and pushes config to backend.
- **Panel toggle buttons** -- Safety (shield), Files (document), Preview (globe), Agent OS (sparkles).
- Guide button (book icon), Theme selector, Dark mode toggle.

### Context Gauge
- Full-width bar below the nav.
- Shows: usage percentage, total tokens, input/output breakdown, cache reads, cost, API call count, remaining capacity.
- Color-coded zones: green (0-70%), yellow (70-85%), orange (85-90%), red (90%+).
- Safety badge (OK/WARNING/HANDOFF/HARD STOP).
- SUB/API billing mode badge.
- Reset button to clear counters.

### Agent Control Bar
- Visible when a project is selected.
- Start/Stop agent button with status indicator (green pulse = running, amber = starting, red = error, grey = idle).
- Shows current model ID and project name.

### Left Sidebar: Projects
- Collapsible project list.
- "New Project" inline form.
- Each project shows name and feature progress (passing/total).
- Selection persists to localStorage.
- Mobile: opens as a slide-out drawer.

### Center Area: Three-Column Agent View (when in Chat mode)

The center uses a **resizable three-column layout** with draggable splitter handles:

1. **API Chat** (~15% width, left) -- Message input at bottom, persistent message history. Typing here auto-starts the agent if not running. Status dot shows agent state.

2. **Event Log** (~35% width, middle) -- Real-time stream of agent activity: text output, tool calls (cyan badges), tool results (green/red), token usage summaries, errors, status changes. Auto-scrolls.

3. **Walkie-Talkie / DunkStack Chat** (~50% width, right) -- The main communication channel. Shows file-based comms log (from `from_human.md` and `to_human.md`). Start/Stop agent buttons. Connection status dot. Mode badge (IDLE/CONTINUE/AUTOPILOT/ACTIVE).

On mobile: only the walkie-talkie column is shown (full width). API Chat and Event Log are hidden.

### Right Panel (toggleable, desktop only)

- **Safety** -- Context safety tiers, session control mode buttons (Idle/Continue/Autopilot), bridge save button, current usage percentage.
- **Files** -- Tab-based file viewer for `.agent/` contents: Index, Working Memory, Bridge, Build Log, Config.
- **Preview** -- Live preview iframe of the project's dev server. Start/stop server controls, viewport toggles (desktop/tablet/mobile), resizable width, half-screen snap. Drag handle on the left edge.
- **Agent OS** -- PRD creator workflow with standards panel, product panel, spec cards, gap analysis, expand panel.

### Guide Panel (floating)

- Draggable, resizable, tabbed panel.
- Tabs: User Guide (inline React content), CLI Reference (renders `DUNKSTACK_MANUAL.md`), Notes (CRUD with tags/dates, persisted to localStorage).
- Position and size persist across reloads.
- Escape key closes it.

---

## 8. Current Implementation Status

Honest assessment of what works and what does not, based on the actual code.

### Agent Start/Stop/Status

**Status: Implemented and working**

- `DunkStackCodingSession` creates a Claude SDK client with full coding tools (Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch).
- System prompt loaded from `.agent/system_prompt.md` with fallback to default.
- Bootstrap message instructs agent to read its file-based state.
- Streaming via `client.query()` + `client.receive_response()`.
- Auth fallback: subscription -> API key -> subscription (three-way fallback).
- Session registry keyed by project name (one agent per project).
- Frontend: Start/Stop buttons in both the Agent Control Bar and the Walkie-Talkie header.
- Backend endpoints: `POST /api/dunkstack/agent/start`, `POST /api/dunkstack/agent/stop`, `GET /api/dunkstack/agent/status`, `POST /api/dunkstack/agent/send`.

### Walkie-Talkie File Communication

**Status: Implemented and working**

- Backend reads/writes `.agent/comms/from_human.md` and `.agent/comms/to_human.md`.
- Markdown format with `## [timestamp] Title` headers.
- Frontend polls every 3 seconds + WebSocket push for real-time updates.
- Optimistic UI updates (message appears immediately before server confirms).
- Comms reset endpoint to clear both files.

### Context Gauge and Token Tracking

**Status: Implemented and working**

- In-memory cumulative token counters in the dunkstack router.
- `DunkStackCodingSession._report_token_usage()` reports after each API response.
- WebSocket broadcasts `token_update` events with cumulative totals and safety tier.
- Token reset endpoint clears counters.
- Gauge component shows percentage, breakdown, cost, remaining tokens.
- Billing mode detection (subscription vs API) based on context window size.

### Safety Tiers

**Status: Implemented and working (UI only -- no automatic agent behavior enforcement)**

- Safety tier computed from usage percentage against configurable thresholds.
- `DunkStackSafetyPanel` renders tier indicators with active states.
- `DunkStackContextGauge` shows safety badge.
- Thresholds configurable via `.agent/settings/config.yml`.

**What is missing:** The safety tiers are purely informational in the current implementation. There is no automatic mechanism that forces the agent to stop at HARD STOP or auto-triggers a bridge save at HANDOFF. The agent's system prompt may instruct it to check context usage, but the backend does not enforce these boundaries. The `PreCompact` hook fires when the Claude CLI auto-compacts, but this is based on the CLI's own internal threshold, not the DunkStack safety tiers.

### Session Control Modes (Idle/Continue/Autopilot)

**Status: Partially implemented (UI exists, backend writes file, but agent behavior not enforced)**

- The three mode buttons exist in the Safety Panel.
- Clicking a mode writes to `.agent/comms/control.md` via `POST /api/dunkstack/control`.
- WebSocket broadcasts `control_update` events.
- The walkie-talkie header shows the current mode badge.

**What is missing:** The agent does not actually implement idle/continue/autopilot behavior at the SDK level. There is no PreToolUse hook that pauses execution in idle mode, no timer that waits for human input, and no autopilot algorithm that detects whether the human is typing. The control mode is written to a file that the agent *could* read, but the system prompt's instructions for interpreting these modes are not connected to any enforcement mechanism. The agent would need to voluntarily check the file and adjust its own behavior, which depends entirely on prompt compliance.

### Bridge Save

**Status: Implemented and working (manual save works, auto-save at HANDOFF does not)**

- Manual "Save Bridge State" button in Safety Panel.
- Backend writes to `.agent/bridge.md` via `POST /api/dunkstack/bridge/save`.
- WebSocket broadcasts `bridge_saved` event.
- Agent bootstrap reads `bridge.md` at startup (step 3).

**What is missing:** Automatic bridge save when the HANDOFF safety tier is reached. The agent's PreCompact hook fires emergency wrap-up instructions, but it does not automatically write bridge data to the file. A future implementation should trigger `saveBridge()` when safety tier reaches 2.

### File Cabinet / File Viewer

**Status: Implemented and working**

- Files panel shows tabs: Index, Working Memory, Bridge, Build Log, Config.
- Each tab fetches content from the corresponding DunkStack API endpoint.
- Config tab renders as formatted JSON.
- The `.agent/` directory is auto-created with subdirectories when needed.
- Universal templates are copied from `server/templates/agent-os/universal/` if files do not exist.

### Model Selection and Switching

**Status: Implemented and working**

- Three model presets: Opus 4.6 200K (subscription), Opus 4.6 1M (API key), Sonnet 4.6 1M (API key).
- Selection persists to localStorage.
- `POST /api/dunkstack/model-preset` updates backend state (model limit, billing mode).
- Agent start uses the selected preset's model ID and context window.
- Smart billing: 200K = subscription (free), 1M = API key (paid).

### WebSocket Real-Time Updates

**Status: Implemented and working**

- WebSocket at `/api/dunkstack/ws`.
- Handles: `init`, `comms_update`, `control_update`, `token_update`, `token_reset`, `comms_reset`, `config_update`, `bridge_saved`, `agent_event`, and all streaming event types.
- Auto-reconnect on disconnect (3-second delay).
- Ping/pong keepalive support.

### Live Preview Panel

**Status: Implemented and working**

- Iframe-based live preview of project dev server.
- Start/stop dev server controls.
- Viewport toggles (desktop/tablet/mobile).
- Resizable width with drag handle.
- Half-screen snap toggle.
- URL auto-detection from dev server output.
- Polls dev server status every 3 seconds.

### Agent OS (PRD Creator)

**Status: Implemented and working (separate system from DunkStack agent)**

- IntakeDock for initial project description.
- AgentOSChat for 9-stage PRD creation workflow.
- Right panel shows: Standards, Product details, Spec cards, Gap analysis, Expand options.
- This is a standalone feature that shares the DunkStack page but uses different backend services.

### Walkie-Talkie Message Injection via PreToolUse Hooks

**Status: NOT implemented**

- The original DunkStack design called for injecting human messages into the agent's context at PreToolUse hook boundaries (before each tool call). This would allow the agent to "hear" new instructions without requiring a separate API call.
- **Current state:** The only PreToolUse hook is for bash command security validation (`bash_hook_with_context`). There is no hook that reads `from_human.md` and injects its contents.
- The agent relies on its system prompt to voluntarily read `from_human.md`, which it does at startup but may not do between every tool call.
- **This is the most important missing piece.** Without PreToolUse injection, the walkie-talkie is a one-way suggestion box that the agent may or may not check. With it, the walkie-talkie becomes a true real-time communication channel.

---

## 9. Architecture (File Map)

### Frontend Components

| File | Description |
|------|-------------|
| `ui/src/pages/DunkStackPage.tsx` | Full-page layout, model presets, project sidebar, panel toggles, agent control bar |
| `ui/src/components/dunkstack/DunkStackAgentView.tsx` | Three-column resizable layout: API Chat, Event Log, Walkie-Talkie |
| `ui/src/components/dunkstack/DunkStackCommsChat.tsx` | Walkie-talkie chat interface with file-based messaging |
| `ui/src/components/dunkstack/DunkStackContextGauge.tsx` | Token usage progress bar with color zones and safety badge |
| `ui/src/components/dunkstack/DunkStackSafetyPanel.tsx` | Safety tiers, session control buttons, bridge save |
| `ui/src/components/dunkstack/DunkStackGuidePanel.tsx` | Floating draggable/resizable guide with User Guide, CLI Reference, Notes tabs |
| `ui/src/components/dunkstack/DunkStackPreviewPanel.tsx` | Live iframe preview of project dev server |
| `ui/src/hooks/useDunkStack.ts` | React hook: WebSocket connection, file polling, token state, agent control |
| `ui/src/lib/api.ts` | REST API client functions (dunkstack* exports, ~30 functions) |

### Backend Services

| File | Description |
|------|-------------|
| `server/routers/dunkstack.py` | REST + WebSocket endpoints for comms, control, tokens, config, bridge, agent lifecycle |
| `server/services/dunkstack_session.py` | `DunkStackCodingSession` -- Claude SDK client with file-based protocol, auth fallback, streaming |
| `server/services/dunkstack_chat_session.py` | `DunkStackChatSession` -- Alternative session class (used by some endpoints) |

### Shared Backend (used by both DunkStack and main AutoForge)

| File | Description |
|------|-------------|
| `server/routers/agent.py` | Agent control endpoints for main AutoForge (start/stop/pause/resume) |
| `server/services/process_manager.py` | `AgentProcessManager` -- subprocess lifecycle for autonomous_agent_demo.py |
| `client.py` | `create_client()` -- Claude SDK client factory with security hooks (used by main agent, not DunkStack) |
| `security.py` | Bash command allowlist validation, `bash_security_hook()` |

### Configuration Files

| File | Description |
|------|-------------|
| `.agent/settings/config.yml` | Safety thresholds, mode config |
| `.agent/system_prompt.md` | Agent operating instructions (loaded as system prompt) |
| `.agent/index.md` | Master file map |
| `server/templates/agent-os/universal/` | Template files copied to new `.agent/` directories |
| `ui/public/DUNKSTACK_MANUAL.md` | CLI reference manual (served statically, rendered in Guide panel) |

---

## 10. What Needs Building

Prioritized list of what is missing or incomplete, with enough detail for an agent to build each item.

### Priority 1: PreToolUse Hook for Walkie-Talkie Injection

**Impact: Critical -- this is the core innovation that makes DunkStack work as designed.**

Currently, the walkie-talkie relies on the agent voluntarily reading `from_human.md`. The original design calls for a `PreToolUse` hook that:

1. Reads `.agent/comms/from_human.md` before every tool call.
2. If there are new messages (track a "last read" timestamp or line count), injects them into the agent's context.
3. Also reads `.agent/comms/control.md` and adjusts behavior:
   - `idle`: Pause execution (return a hook result that stalls for N seconds, or inject a "wait for human" instruction).
   - `continue`: Proceed normally.
   - `autopilot`: Proceed, but check if human is actively typing (could use a timestamp-based heuristic on `from_human.md` modification time).

**Where to implement:** In `server/services/dunkstack_session.py`, add a new `PreToolUse` hook alongside the existing bash security hook. The hook should be added to the `hooks` dict in `DunkStackCodingSession.start()`.

**Challenge:** The Claude Agent SDK's `PreToolUse` hook returns `SyncHookJSONOutput` which can approve, reject, or modify tool use. It may not directly support "pause and wait." The implementation may need to return a modified tool input that includes injected context, or use a `reject` with a custom message that instructs the agent to read new instructions.

### Priority 2: Automatic Bridge Save at HANDOFF Threshold

**Impact: High -- prevents data loss when context runs out.**

When the safety tier reaches 2 (HANDOFF at 47.5%), the system should automatically:

1. Call the bridge save endpoint to write current state to `.agent/bridge.md`.
2. Inject a message to the agent (via walkie-talkie or API) instructing it to commit all work and stop.

**Where to implement:** In `server/routers/dunkstack.py`, in the `record_tokens()` function where safety tier is computed. When tier transitions from 1 to 2, trigger a bridge save and optionally send a stop signal.

### Priority 3: Automatic Agent Stop at HARD STOP Threshold

**Impact: High -- prevents wasted API spend.**

When safety tier reaches 3 (HARD STOP at 50%):

1. Automatically stop the agent session.
2. Broadcast a notification to the UI.

**Where to implement:** Same location as Priority 2, but triggers `session.stop()` instead of just a bridge save.

### Priority 4: Session Control Mode Enforcement

**Impact: Medium -- makes the three control modes actually do something.**

For `idle` mode:
- After each agent response, inject a message telling the agent to wait for human input before continuing.
- In the PreToolUse hook (Priority 1), add a delay or polling loop that checks for new `from_human.md` entries.

For `autopilot` mode:
- Implement the hybrid algorithm: if `from_human.md` was modified within the last N seconds, wait briefly (human is typing). Otherwise, proceed.

`continue` mode works as-is (no pauses needed).

### Priority 5: File Cabinet Document System

**Impact: Medium -- extends context capacity.**

The `.agent/knowledge/` directory exists but needs:

1. A standard file format with 1-sentence summary, 2-sentence description, and table of contents at the top of each document.
2. An index generator that scans `knowledge/` and updates `index.md` with summaries.
3. Agent system prompt instructions to use the "thumb through summaries" pattern before reading full documents.

**Where to implement:** Template files in `server/templates/agent-os/universal/`, system prompt in `.agent/system_prompt.md`.

### Priority 6: Working Memory Auto-Update

**Impact: Low-Medium -- improves session continuity.**

The agent should update `.agent/working_memory.md` periodically (every N tool calls or after completing a task). Currently this depends on prompt compliance.

A PreToolUse hook could track tool call count and inject a reminder to update working memory every 20 calls.

### Priority 7: Multi-Provider Support

**Impact: Low -- extends DunkStack beyond Claude.**

The DunkStack agent currently only supports Claude via the Claude Agent SDK. The broader AutoForge system supports Codex and Gemini for workspace chat, but DunkStack's `DunkStackCodingSession` is Claude-only.

Supporting other providers would require abstracting the SDK client interface or implementing provider-specific session classes.

---

## Appendix: API Endpoint Reference

All endpoints are prefixed with `/api/dunkstack`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/comms/to-human` | Read agent-to-human messages |
| GET | `/comms/from-human` | Read human-to-agent messages |
| POST | `/comms/from-human` | Write a human message |
| POST | `/comms/reset` | Clear both comms files |
| GET | `/control` | Read current control mode |
| POST | `/control` | Set control mode (idle/continue/autopilot) |
| GET | `/working-memory` | Read working memory file |
| GET | `/index` | Read index file |
| GET | `/bridge` | Read bridge file |
| POST | `/bridge/save` | Save bridge state |
| GET | `/build-log` | Read build log |
| GET | `/config` | Read config |
| POST | `/config` | Update config |
| POST | `/model-preset` | Update model and context window |
| GET | `/sdk-env` | Get SDK environment info |
| GET | `/tokens` | Get cumulative token state |
| POST | `/tokens/record` | Record new token usage |
| POST | `/tokens/reset` | Reset token counters |
| GET | `/tokens/log` | Get token usage history |
| POST | `/agent/start` | Start coding agent session |
| POST | `/agent/stop` | Stop coding agent session |
| GET | `/agent/status` | Get agent status |
| POST | `/agent/send` | Send message to running agent |
| WS | `/ws` | WebSocket for real-time updates |
