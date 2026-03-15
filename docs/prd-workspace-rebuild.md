# PRD: Workspace Rebuild — One Agent Per Page Architecture

## Document Purpose
This is a descriptive PRD for a fresh coding agent to turn into full implementation specs. It covers the complete rebuild of AutoForge's workspace from a multi-agent-per-page architecture to a one-agent-per-page architecture. Each section describes WHAT to build and WHY, with enough technical context for an agent to make implementation decisions.

---

## Background & Problem Statement

The current workspace was built with multiple chat sessions on a single page, sharing one WebSocket connection. This required:
- A background session manager that multiplexes events from multiple sessions
- A viewer protocol for attaching/detaching from sessions and replaying missed events
- Complex state management tracking which session is active, which is streaming, etc.

This architecture is an 8-9/10 difficulty problem (comparable to what Claude Code Web's 20-engineer team built). It has been unreliable — streaming bugs, token log not updating, sessions getting stuck, events going to the wrong session. Two weeks of debugging has not fully resolved these issues.

**The solution:** Switch to one agent per page. Each page gets its own WebSocket, its own session, its own everything. Navigation between pages uses a sidebar with descriptive buttons — visually identical to the current sidebar, but each "session" is actually a separate route/page. This drops difficulty to 3-4/10 across the board.

---

## Architecture Overview

### Core Principle
Every page with an agent has exactly ONE WebSocket connection to exactly ONE backend session. Pages don't share sessions. Pages don't know about each other's sessions. The server handles each connection independently.

### Page Types
1. **General Chat Page** — One agent, one conversation. Like Claude.ai but with AutoForge capabilities (context gauge, file browser, terminal, skills).
2. **Factory Page** — One agent with a job queue. Builds apps from PRDs in sequence. Has build-specific UI (queue list, progress, phase tracking).
3. **DunkStack Page** — One agent with the filing cabinet system (file-based context management). Used for specialist roles in team builds. Multiple DunkStack pages can share the same project filesystem and communicate via file-based messaging.

### Navigation
- Left sidebar shows all active pages as descriptive buttons
- Each button shows: page name, provider icon (Claude/Codex/Gemini), context window %, brief description
- Buttons are grouped by type: General Chats, Factory Builds, DunkStack Sessions
- Clicking a button navigates to that page's route (e.g., `/chat/abc123`, `/factory/def456`, `/dunkstack/ghi789`)
- "New Page" button at top — choose type (General/Factory/DunkStack) and provider (Claude/Codex/Gemini)
- Pages can be hidden/archived without deletion
- For Factory pages, sidebar shows the build queue items with descriptions — clicking one opens the full PRD/parameters view

### Provider Support
- Claude (Anthropic) — subscription model, already built
- Codex (OpenAI) — subscription model, already built in workspace
- Gemini (Google) — subscription model, already built in workspace
- Provider is chosen at page creation time and stays fixed for that page
- Each provider uses its existing adapter code — no new adapters needed

---

## Phase 1: Factory Page (Single Agent, Build Queue)

### What It Is
A dedicated page for the app factory. One Claude agent that takes PRDs from a queue and builds apps one at a time. This is the #1 priority — the core reason AutoForge exists.

### What Gets Stripped From Current Workspace
- `BackgroundSessionManager` — the multi-session multiplexer. Remove entirely.
- Session sidebar with multiple chat entries — replaced with build queue sidebar
- Viewer protocol (attach/detach/replay) — not needed with one session
- `attachedSessionIdRef` and all session-switching logic — gone
- Multiple WebSocket event routing ("which session does this event belong to?") — gone

### What Stays
- Chat message display (message list, markdown rendering)
- Input box with send button
- WebSocket connection to backend (simplified to one session)
- Token log display
- Terminal panel
- File browser panel
- Backend `workspace_chat_session.py` (the actual Claude SDK session runner)
- All existing API routes that aren't session-multiplexing related

### What Gets Added
- **Build Queue Panel** (sidebar): List of PRDs/jobs lined up. Each entry shows: build name, description, status (queued/active/complete/failed), estimated phases. Click to expand and see full PRD, parameters, build config.
- **Role Selector**: Dropdown to pick which agent role file to load (from `.claude/agents/` directory). Default roles: Builder, Tester, Security Reviewer. The "revolver" — can switch roles mid-session or between build phases.
- **Context Window Gauge**: Visual bar showing current token usage as percentage. Color-coded: green (0-40%), yellow (40-70%), orange (70-85%), red (85-100%). Numeric display of tokens used / total.
- **Context Warnings**: At 40% — yellow indicator. At 45% — notification banner "approaching limit." At 50% — red alert, agent should wrap up.
- **Auto-Continue**: When one build finishes (agent signals done or hits context limit), automatically pick up next job from queue. 3-second delay between jobs.
- **Build Progress Tracking**: Which phase of the current build is active. Features completed vs remaining. Pass/fail status per feature.

### Backend Changes
- New route: `POST /api/factory/queue` — add a job to the queue
- New route: `GET /api/factory/queue` — list queue items
- New route: `DELETE /api/factory/queue/{id}` — remove a queue item
- New route: `POST /api/factory/start` — start processing the queue
- New route: `POST /api/factory/stop` — stop after current job finishes
- WebSocket: `/ws/factory/{page_id}` — single session, streams events to the one connected page
- Queue storage: SQLite table (id, name, description, prd_path, status, created_at, started_at, completed_at)

### How the Factory Runs
1. User adds PRDs to the queue (upload files or paste text)
2. User hits "Start"
3. Backend creates a Claude session with the Builder role loaded
4. Agent receives the first PRD as its prompt
5. Agent codes, tests, builds — streaming output appears on the page
6. When agent signals completion (or hits context limit), backend marks job complete
7. Backend picks next job from queue, starts new session
8. Repeat until queue is empty
9. User can pause/resume/stop at any time

---

## Phase 2: General Chat Pages (Multiple Independent Pages)

### What It Is
Multiple independent chat pages, each with one agent. Create as many as you want. Each can use a different provider (Claude, Codex, Gemini). Same chat UI as the workspace has now, but simplified to one session per page.

### Implementation
- Route: `/chat/:pageId` — each page has a unique ID
- Component: `ChatPage.tsx` — renders the same for every page, parameterized by pageId
- WebSocket: `/ws/chat/{pageId}` — one connection per page
- "New Chat" button creates a new page entry in the database, assigns a unique ID, navigates to it
- Provider selection happens at creation time (dropdown: Claude / Codex / Gemini)
- Page metadata stored in SQLite: id, name, provider, created_at, last_active, context_pct, description

### Sidebar Navigation
- Groups pages by provider: Claude (with count), Codex (with count), Gemini (with count)
- Each entry shows: name, provider icon, context %, last active time
- Click navigates to that page's route
- Right-click or "..." menu: rename, archive, delete
- Drag to reorder (optional, low priority)
- Custom presets: user can arrange a set of specific pages for quick access (e.g., "Project Alpha" preset shows 2 Claude + 1 Codex + 1 Gemini pages)

### What Each Chat Page Has
- Full chat UI (messages, input, send)
- Context window gauge
- Role selector (pick agent role from `.claude/agents/`)
- Terminal panel (toggle)
- File browser panel (toggle)
- Skill invoker (load and inject skills from `.claude/skills/`)
- All existing workspace features minus the multi-session complexity

---

## Phase 3: CLI Capabilities on Every Page

### What It Is
Wiring up Claude Code CLI capabilities that the SDK supports but AutoForge hasn't exposed in the UI yet. These apply to ALL page types (General, Factory, DunkStack).

### Skills System
- **Skill Browser Panel**: Shows all `.claude/skills/` files. Each skill has a title and description (first 2 lines of the file). Click to expand and read full skill content.
- **Skill Injection**: Click "Use" on a skill → its content gets injected into the current prompt/system message. The agent now has that skill's instructions.
- **CLAUDE.md Skill References**: Support the pattern where CLAUDE.md lists skill titles with pointers to files. Agent reads the title list (low token cost), only loads the full skill file when it needs it.
- **Skill Management**: Create new skills, edit existing ones, organize into categories. Each skill is just a markdown file.

### Agent Roles System
- **Role Files**: `.claude/agents/*.md` files. Each defines a persona: name, model preference, system prompt, allowed tools, specialty description.
- **Role Selector**: Dropdown on every page. Pick a role → it becomes the agent's system prompt for that session.
- **Role Editor**: Create/edit roles from the UI. Form fields: name, model, system prompt text, tools allowed, description.
- **Role Revolver**: For factory builds — define a sequence of roles that auto-rotate per build phase. E.g., Phase 1: Builder → Phase 2: Tester → Phase 3: Security → Phase 4: Builder. Configurable per build or as a preset.

### Hooks System
- **PreToolUse Hooks**: Already exist for security (bash command allowlist). Extend to support custom hooks defined in UI.
- **PostToolUse Hooks**: New. Run a check after every tool call. Example: "after every file write, run lint."
- **Hook Configuration UI**: List of active hooks. Each hook has: trigger (which tool), condition (optional), action (script to run or check to perform).
- **Walkie-Talkie Hook**: Already built for human↔agent messaging. Listed as a configurable hook that can be enabled/disabled per page.

### Context Window Management
- **Token Gauge**: Already described in Phase 1. Apply to all page types.
- **Warning Thresholds**: Configurable. Default: 40% notify, 45% warn, 50% stop.
- **Auto-Handoff**: When hitting the stop threshold, agent saves its current state (what it was working on, what's left) to a handoff file. New session can pick up from there.

---

## Phase 4: DunkStack Filing Cabinet + Specialist Pinwheel

### What It Is
The DunkStack system where multiple specialist agents on separate pages share the same project filesystem and communicate through file-based messaging. An orchestrator manages the build sequence. This is the "dream team" setup.

### Shared Filesystem (The Filing Cabinet)
- Multiple DunkStack pages can be linked to the same project directory
- Each agent reads/writes to the same files — same codebase, same docs, same everything
- The DunkStack filing cabinet system (index files, organized storage, context-efficient retrieval) is already designed in previous PRDs — this just makes it accessible to multiple agents
- No special setup needed for sharing — it's just multiple agents with the same `project_dir` configured

### Agent-to-Agent Messaging (The Walkie-Talkie Extended)
- Message file location: `{project_dir}/.autoforge/agent_messages/`
- Message format: JSON files named `{timestamp}_{from}_{to}.json`
- Fields: `from_agent`, `to_agent` (or "all"), `message_type` (status_update, handoff, request, alert), `content`, `timestamp`, `read_by` (list)
- Each agent's PreToolUse hook checks for new messages addressed to it (or "all") on every tool call
- Agents identify themselves: "orchestrator", "builder", "tester", "security", etc. — matches their role file name
- Cleanup: messages older than the current build session get archived

### The Orchestrator
- **NOT an AI agent** — it's a Python script. Burns zero API tokens.
- Manages the build sequence: which specialist goes when
- Watches for status messages from active agents
- Activates the next specialist when the current one signals "done"
- Handles error cases: agent crashes, agent hits context limit, agent reports failure
- Configuration: a YAML or JSON file defining the build pipeline:
  ```yaml
  pipeline:
    - agent: builder
      task: "Implement authentication module"
      success_signal: "AUTH_COMPLETE"
    - agent: tester
      task: "Test authentication module"
      success_signal: "AUTH_TESTS_PASS"
    - agent: security
      task: "Security review of auth module"
      success_signal: "AUTH_SECURITY_CLEAR"
    - agent: builder
      task: "Implement dashboard"
      ...
  ```
- Sends green-light messages to agents: "Your turn. Here's your task."
- Monitors for completion signals or timeout

### Warm Standby Agents (The Rotation System)
- For roles that burn context fast (mainly coders), have 2-3 instances ready
- A "reporter" agent (Sonnet, cheap) writes `BUILD_STATUS.md` after each milestone
- Standby agents periodically read `BUILD_STATUS.md` to stay warm
- When the active coder hits 70% context, orchestrator signals handoff
- Next coder takes over — already has project context from status updates
- The reporter agent's updates include: files created/modified since last update, current build state, what's done, what's next, any issues encountered

### DunkStack Page UI
- Same base layout as General Chat page
- Additional panels:
  - **Filing Cabinet Browser**: Navigate the organized file storage (indexes, categories)
  - **Team Status Panel**: Shows all linked agents, their status (active/standby/idle), context %, current task
  - **Message Log**: Recent agent-to-agent messages (read-only view for the human)
  - **Pipeline View**: Visual representation of the build sequence — which step is active, which are done, which are pending
  - **Orchestrator Controls**: Start/pause/stop the pipeline. Override: manually activate a specific agent.

---

## Phase 5: Multi-Provider Specialist Team

### What It Is
Extending the DunkStack pinwheel to include agents from different providers. Claude agents, Codex agents, and Gemini agents all working on the same project, communicating through the same filing cabinet.

### Why It Works
- The file-based messaging system is provider-agnostic — it's JSON files on disk
- The shared filesystem is just a directory — any agent can read/write files
- Each agent runs on its own page with its own provider connection
- The orchestrator doesn't care which provider an agent uses — it just sends/receives messages through files

### Provider Strengths (Recommended Role Assignments)
- **Claude (Opus)**: Best reasoning, architecture decisions, complex logic, orchestration oversight
- **Claude (Sonnet)**: Good all-rounder, cost-effective for testing, documentation, reporter role
- **Codex/GPT**: Strong backend coding, API design, database work
- **Gemini**: Strong frontend/UI work, large context window for reading big codebases

### What Needs to Happen
- Verify existing Codex and Gemini adapters work with the new single-socket page architecture
- Ensure agent-to-agent message format is understood by all providers (standard JSON, no provider-specific formatting)
- Test: Claude builder + Gemini UI specialist sharing a project, communicating through files
- Provider-specific system prompts: each provider may need slightly different instructions for how to read/write agent messages (since they each have different tool APIs)

### Configuration
- Each DunkStack page's role file includes the preferred provider
- Orchestrator pipeline config specifies provider per step:
  ```yaml
  pipeline:
    - agent: architect
      provider: claude
      model: opus
    - agent: backend_coder
      provider: codex
      model: gpt-5.4
    - agent: frontend_coder
      provider: gemini
      model: gemini-pro
    - agent: tester
      provider: claude
      model: sonnet
  ```

---

## Implementation Priority & Session Estimates

### Priority Order
1. **Phase 1: Factory Page** — Gets the app factory running. #1 business priority.
2. **Phase 2: General Chat Pages** — Gets multiple independent chats working.
3. **Phase 3: CLI Capabilities** — Adds skills, roles, hooks to all pages.
4. **Phase 4: DunkStack Pinwheel** — Specialist team with shared filesystem.
5. **Phase 5: Multi-Provider Team** — Cross-company agent collaboration.

### Session Estimates (100K tokens per session, ~15 min each)
- Phase 1: 2-3 sessions (30-45 min coding)
- Phase 2: 2-3 sessions (30-45 min coding)
- Phase 3: 1-2 sessions (15-30 min coding)
- Phase 4: 2-3 sessions (30-45 min coding)
- Phase 5: 1-2 sessions (15-30 min coding)
- **Total: 8-13 sessions, ~2-3 hours of pure coding time**

### What Exists vs What's New
- **Exists (keep):** Chat UI, WebSocket infrastructure, Claude/Codex/Gemini adapters, terminal panel, file browser, token tracking, security hooks, MCP servers, factory controller base, walkie-talkie system, DunkStack file system design
- **Strip out:** BackgroundSessionManager, viewer protocol, session multiplexing, attachedSessionIdRef, multi-session state management
- **Build new:** Route-per-page architecture, build queue UI, role selector/revolver, skill browser, context gauge, agent-to-agent messaging, orchestrator script, team status panel, pipeline view

---

## Key Design Decisions (For the Coding Agent)

1. **One WebSocket per page, period.** No exceptions. No "optimization" that puts two sessions on one socket.
2. **Pages are created on demand.** No pre-building 20 pages. Click "New" → page exists. Close → page archived.
3. **Provider chosen at creation, fixed for page lifetime.** No mid-conversation provider switching.
4. **The orchestrator is Python, not AI.** Rule-based sequencing. Zero token cost for coordination logic.
5. **File-based messaging for agent communication.** Not WebSocket relay, not API calls between agents. Files in the shared project directory.
6. **Role revolver uses existing `.claude/agents/` files.** No new format — same markdown files the CLI uses.
7. **Skills use existing `.claude/skills/` files.** Same format, same loading pattern. Just adding UI.
8. **Sidebar is navigation, not session management.** Each sidebar entry is a link to a page route, not a session switcher.
9. **The existing workspace code is the starting point.** Strip the multi-session parts, keep the working parts. Don't rebuild from scratch.
10. **Test each phase before starting the next.** Phase 1 must work before Phase 2 begins.
