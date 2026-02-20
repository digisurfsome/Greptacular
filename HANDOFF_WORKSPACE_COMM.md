# Handoff: Workspace Communication System (Walkie-Talkie)

## What This Is

A set of features were built for a walkie-talkie communication system — countdown timers, roadmap tracking, file attachments, auto-reply, configurable settings. The features work, but they were **wired into the AutoForge agent system instead of the Workspace chat system**. This branch (`claude/fix-workspace-features-X9VMA`) must NEVER be merged.

The next agent needs to rebuild these features in the correct location: the **Workspace chat system** (`ui/src/pages/WorkspacePage.tsx`, `ui/src/components/workspace/`, `server/services/workspace_chat_session.py`).

## Reference Branch

All code examples are on branch `claude/fix-workspace-features-X9VMA`. The next agent can check out this branch read-only to see working implementations. Commits:

```
663e7b8 fix: per-panel model selector for split-view + Research defaults to Opus 200K
4f32c7a feat: auto-summary checkpoint, roadmap tracking, pause commands, file attachments
1e5b559 feat: configurable walkie-talkie params with countdown timer and auto-reply
```

## DO NOT TOUCH (AutoForge System)

These files belong to the AutoForge autonomous coding system. **Never modify them:**
- `client.py` — Agent SDK client with MCP servers, security hooks
- `agent.py` — Agent session loop
- `prompts.py` — Prompt template loading (the `get_coding_prompt` function)
- `mcp_server/feature_mcp.py` — Feature management MCP server
- `mcp_server/comm_mcp.py` — Communication MCP server (AutoForge-specific)
- `autonomous_agent_demo.py` — Agent entry point
- `parallel_orchestrator.py` — Multi-agent orchestrator

## Features to Rebuild (in the Workspace system)

### 1. Per-Panel Model Selector (DONE CORRECTLY on this branch)
**What:** Each split-view panel (Research/PRD/Coder) gets its own Opus/Sonnet toggle in the header bar. Research defaults to Opus 200K, PRD to Opus 1M, Coder to Sonnet 1M. Persisted to localStorage.

**Reference files (correctly placed, can be cherry-picked):**
- `ui/src/pages/WorkspacePage.tsx` — State variables `researchModel`, `prdModel`, `coderModel` with localStorage persistence. Passed as `preferredModel` + `onModelChange` props.
- `ui/src/components/workspace/WorkspaceChat.tsx` — `onModelChange` prop added to interface. Small Opus/Sonnet pill toggle rendered in panel label bar when `fixedContextMode` is set.

**This one is safe to use as-is.** Only touches workspace files.

### 2. Configurable Communication Settings
**What:** Three settings in Settings > Walkie-Talkie section:
- Check Frequency: per_feature / every_tool_call / never
- Wait Timeout: 30s / 1m / 2m / 5m
- Auto-Reply on Timeout: toggle

**Reference files (shared infrastructure, safe):**
- `server/schemas.py` — `comm_check_frequency`, `comm_wait_timeout`, `comm_auto_reply` added to `SettingsResponse` and `SettingsUpdate` with validators
- `server/routers/settings.py` — GET/PATCH handlers for the three settings
- `ui/src/lib/types.ts` — TypeScript types for Settings/SettingsUpdate interfaces
- `ui/src/hooks/useProjects.ts` — DEFAULT_SETTINGS updated with comm defaults
- `ui/src/components/SettingsModal.tsx` — UI section with button groups and toggle

**WHERE IT NEEDS TO GO:** These settings need to control the **workspace chat session** behavior, not the AutoForge agent prompt. Instead of injecting into `prompts.py`, the workspace chat session (`server/services/workspace_chat_session.py`) should read these settings and use them to configure its own communication behavior.

### 3. Countdown Timer + Keep Going Button + Auto-Reply
**What:** When the agent is in "waiting" phase (blocking on `chat_with_user`), the UI shows:
- Countdown timer with progress bar draining down
- "Keep Going" button to instantly dismiss the wait
- Auto-reply sends "keep going" message when timer hits 0 (if enabled)

**Reference file:**
- `ui/src/components/AgentNotifications.tsx` — Full implementation with `useEffect` timer that calculates remaining time from `agentPhase.timestamp`, sends auto-reply via `sendToAgentInbox` when countdown hits 0

**WHERE IT NEEDS TO GO:** This component needs to be integrated into `ui/src/pages/WorkspacePage.tsx` instead of only being available in the AutoForge main page. The workspace page needs its own notification/comm panel — either shared across all three panels or per-panel.

### 4. Roadmap Tracking
**What:** Agent sends structured messages that the UI renders as a visual checklist:
- `[ROADMAP] 1. Step one | 2. Step two | 3. Step three` — Parsed into checklist with progress bar
- `[PROGRESS] 2/4 Step label` — Marks steps as done
- `[FINISHING]` — Shows amber "finishing soon" banner

**Reference file:**
- `ui/src/components/AgentNotifications.tsx` — `parseRoadmap()` and `parseProgress()` functions, roadmap state with checklist rendering, progress bar, finishing-soon indicator

**WHERE IT NEEDS TO GO:** The workspace chat session needs to be instructed (in its system prompt in `workspace_chat_session.py`) to send these structured messages. The UI component needs to be in the workspace page and parse messages from the workspace WebSocket, not from the AutoForge outbox.

### 5. Image/File Attachments
**What:** Users can attach files (images, PDFs, text) to messages:
- Paperclip button, paste from clipboard, drag-and-drop
- Preview thumbnails for images, extension badges for other files
- Max 5 attachments, 5MB each
- Allowed: .png, .jpg, .jpeg, .gif, .webp, .pdf, .txt, .md, .json, .csv
- Backend saves to disk, inbox message includes file paths

**Reference files:**
- `ui/src/components/AgentNotifications.tsx` — `PendingAttachment` type, `fileToBase64()`, `handleFileSelect()`, `handlePaste()`, preview rendering, hidden file input
- `ui/src/lib/api.ts` — `sendToAgentInbox()` updated to accept optional attachments array
- `server/routers/notifications.py` — `InboxAttachment` model, `_save_attachment()` function, updated endpoint accepting attachments, saving to `.autoforge/inbox_attachments/`

**WHERE IT NEEDS TO GO:** The workspace already has image attachment support (`WorkspaceChat.tsx` has `pendingImages`, `imageInputRef`, `fileToText()`). The file attachment capability from notifications.py needs to be adapted for the workspace's own message system (which goes through WebSocket, not the notifications REST API).

### 6. Auto-Summary Checkpoint (WRONG PLACE — needs complete redesign)
**What:** Auto-inject a final "Build Summary Report" task at the end of every feature list. The agent sends a summary via walkie-talkie before finishing and opens a chat_with_user window for follow-up tasks.

**Reference file (DO NOT USE AS-IS):**
- `mcp_server/feature_mcp.py` — Checkpoint injection in `feature_create_bulk()`. This modifies the AutoForge feature system.

**WHERE IT NEEDS TO GO:** For the workspace, this should be a prompt instruction in `workspace_chat_session.py` system prompt — tell the workspace agent "before you finish, send a summary of what you built." No feature injection needed since the workspace doesn't use the feature queue system.

### 7. Pause Commands (prompt-only, needs redirect)
**What:** User types "pause 5m" in chat, agent recognizes it and waits.

**Reference file (WRONG PLACE):**
- `prompts.py` — `_get_comm_context()` function generates prompt instructions for pause command recognition

**WHERE IT NEEDS TO GO:** These instructions should go into the workspace chat session system prompt (`workspace_chat_session.py` around line 130-172 where `SYSTEM_PROMPT` is defined), not the AutoForge coding prompt.

## Architecture Notes

### AutoForge Communication (existing, don't touch)
```
AutoForge Agent → mcp_server/comm_mcp.py → .autoforge/outbox.jsonl → WebSocket → App.tsx
User → REST API (notifications router) → .autoforge/inbox.jsonl → comm_mcp.py → Agent
```

### Workspace Communication (what needs to be built)
```
Workspace Agent → WebSocket messages → WorkspacePage.tsx
User → WebSocket messages → workspace_chat_session.py → Agent
```

The workspace already has a real-time bidirectional WebSocket. It does NOT use the file-based inbox/outbox system. The comm features need to work through the existing WebSocket, not by bolting on the AutoForge comm MCP server.

### Key Workspace Files to Modify
- `server/services/workspace_chat_session.py` — System prompt, session lifecycle
- `server/routers/workspace.py` — WebSocket handler
- `ui/src/pages/WorkspacePage.tsx` — Page layout, state management
- `ui/src/hooks/useWorkspaceChat.ts` — WebSocket hook, message handling
- `ui/src/components/workspace/WorkspaceChat.tsx` — Chat component

### Key Workspace Files to READ (understand the system first)
- `server/services/workspace_chat_session.py` — How workspace sessions work
- `ui/src/hooks/useWorkspaceChat.ts` — How WebSocket messages flow
- `ui/src/components/workspace/WorkspaceChat.tsx` — How the chat UI works

## Summary

| Feature | Reference Location | Correct Target |
|---------|-------------------|----------------|
| Per-panel model selector | WorkspacePage.tsx, WorkspaceChat.tsx | **Already correct** |
| Comm settings | schemas.py, settings router, SettingsModal | **Already correct** (shared) |
| Countdown + Keep Going + Auto-reply | AgentNotifications.tsx | WorkspacePage.tsx (new component) |
| Roadmap tracking | AgentNotifications.tsx | WorkspacePage.tsx + workspace_chat_session.py |
| File attachments | notifications.py, AgentNotifications.tsx | Workspace WebSocket system |
| Auto-summary | feature_mcp.py (WRONG) | workspace_chat_session.py system prompt |
| Pause commands | prompts.py (WRONG) | workspace_chat_session.py system prompt |
