# PRD: Workspace Session Persistence — Stop Sessions from Dying on Navigation

## The Problem

In both the **WorkspacePage** (split-view panels) and **DashboardPage** (multi-pane layout), AI chat sessions are destroyed when:

1. **Panel collapse**: Clicking the collapse button on Research/PRD/Coder panels → ternary conditional renders `CollapsedPanelBar` instead of `WorkspaceChat` → React unmounts `WorkspaceChat` → WebSocket closes → server destroys session
2. **Tab switch (PRD panel)**: Clicking the "Passoff" tab in the PRD Builder panel → ternary at `WorkspacePage.tsx:580` renders `PassoffEditor` instead of `WorkspaceChat` → same kill chain
3. **Dashboard pane collapse**: Same ternary pattern at `DashboardPage.tsx:390`
4. **Conversation switch (single-panel mode)**: Clicking a different conversation in sidebar → `disconnect()` called → old session destroyed, new one created (this one is by design and acceptable)

### The Kill Chain

```
User collapses panel / switches tab
  → React ternary unmounts WorkspaceChat
    → useWorkspaceChat hook unmounts → WebSocket closes
      → Server: WebSocketDisconnect caught in finally block
        → ws_remove_session(session_id) called
          → _sessions.pop(session_id) + session.close()
            → Claude SDK client.__aexit__() / codex_bridge.close() / gemini_bridge.close()
              → AI agent context DESTROYED (tool state, working memory gone)
```

Conversation history survives in SQLite (`workspace_messages` table), but the **live agent** is dead. Resuming requires creating a brand new Claude SDK client, reloading history, and rebuilding context — expensive in tokens and latency.

---

## The Solution: Two-Layer Fix

### Layer 1: CSS Visibility (Quick Win — Prevents Unmount)

Replace React ternary conditionals with CSS-based show/hide so both components stay mounted simultaneously. This is the simplest fix and prevents the unmount entirely.

### Layer 2: Background Sessions (Resilience — Already Built)

Wire the existing `BackgroundSessionManager` (Phase 2, already committed) into the workspace WebSocket handler so that even if a WebSocket disconnects (browser tab close, network drop), the AI session continues running in the background and can be reattached.

Layer 1 is the **immediate fix** for the user's problem. Layer 2 is the **infrastructure** that makes it bulletproof.

---

## Layer 1: CSS Visibility Fixes

### File: `ui/src/pages/WorkspacePage.tsx`

#### Fix 1: Research Panel Collapse (lines 487-526)

**Current (kills session):**
```tsx
{researchCollapsed ? (
  <CollapsedPanelBar ... />
) : (
  <div className="flex-1 ...">
    <WorkspaceChat ... />
  </div>
)}
```

**Fixed (preserves session):**
```tsx
{researchCollapsed && (
  <CollapsedPanelBar ... />
)}
<div
  className={`flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border relative ${
    researchCollapsed ? 'hidden' : ''
  }`}
>
  <WorkspaceChat ... />
</div>
```

The pattern: render `CollapsedPanelBar` conditionally AND always render the panel div, toggling `hidden` class. `hidden` sets `display: none` which removes the element from layout (no space taken) but keeps the React tree mounted. The WebSocket stays alive.

#### Fix 2: PRD Panel Collapse (lines 529-616)

Same pattern as Fix 1. Replace the PRD panel's ternary with:
```tsx
{prdCollapsed && (
  <CollapsedPanelBar ... />
)}
<div className={`flex-1 ... ${prdCollapsed ? 'hidden' : ''}`}>
  {/* Tab bar + tab content */}
</div>
```

#### Fix 3: PRD Tab Switch — Passoff vs Chat (lines 580-614)

**Current (kills session):**
```tsx
{showPassoffOverlay ? (
  <PassoffEditor ... />
) : (
  <WorkspaceChat ... />
)}
```

**Fixed (preserves session):**
```tsx
<div className={showPassoffOverlay ? 'flex-1 overflow-hidden' : 'hidden'}>
  <PassoffEditor ... />
</div>
<div className={showPassoffOverlay ? 'hidden' : 'contents'}>
  <WorkspaceChat ... />
</div>
```

Both `PassoffEditor` and `WorkspaceChat` stay mounted. Only visibility toggles. `contents` makes the div transparent to flex layout so `WorkspaceChat` fills the space correctly.

#### Fix 4: Coder Panel Collapse (lines 619-658)

Same pattern as Fix 1.

### File: `ui/src/pages/DashboardPage.tsx`

#### Fix 5: Dashboard Pane Collapse (lines 390-460)

**Current (kills session):**
```tsx
{panes.map((pane, idx) => {
  if (pane.collapsed) {
    return <CollapsedPaneBar key={pane.id} ... />
  }
  return (
    <div key={pane.id} ...>
      <WorkspaceChat ... />
    </div>
  )
})}
```

**Fixed (preserves session):**
```tsx
{panes.map((pane, idx) => {
  const isLast = idx === panes.length - 1
  return (
    <React.Fragment key={pane.id}>
      {pane.collapsed && (
        <CollapsedPaneBar ... />
      )}
      <div
        className={`flex-1 min-w-0 flex flex-col overflow-hidden relative ${
          !isLast ? 'border-r border-border' : ''
        } ${pane.collapsed ? 'hidden' : ''}`}
      >
        {/* Pane header */}
        <div className="flex items-center ...">
          ...
        </div>
        {/* Chat area - always mounted */}
        <WorkspaceChat ... />
      </div>
    </React.Fragment>
  )
})}
```

---

## Layer 2: Background Session Integration

This uses the `BackgroundSessionManager` already built in Phase 2 (`server/services/background_session_manager.py`). The workspace WebSocket handler needs to route through it so sessions survive WebSocket disconnects.

### File: `server/routers/workspace.py`

The existing PRD at `PRD_MISSION_CONTROL_PHASE_3_4.md` describes the full WebSocket protocol transformation. The same changes apply here — the workspace WebSocket handler at line 1106 needs to:

1. Create sessions via `BackgroundSessionManager.create_session()` instead of directly via `ws_create_session()`
2. Attach the WebSocket as a viewer via `attach_viewer()`
3. In the `finally` block, call `detach_viewer()` instead of `remove_session()`
4. Support `attach` messages for reconnecting to existing sessions

**This is already fully specified in `PRD_MISSION_CONTROL_PHASE_3_4.md` Phase 3.** No duplicate specification needed.

### File: `server/main.py`

Add BackgroundSessionManager cleanup to the lifespan shutdown:

```python
# In the shutdown section (around line 96):
from .services.background_session_manager import get_background_session_manager

# After existing cleanup calls:
try:
    manager = await get_background_session_manager()
    await manager.stop()
except Exception as e:
    logger.warning("Error stopping background session manager: %s", e)
```

---

## Implementation Order

| Step | Layer | File | What | Complexity |
|------|-------|------|------|------------|
| 1 | 1 | `WorkspacePage.tsx` | Fix Research panel collapse (CSS hidden) | Small |
| 2 | 1 | `WorkspacePage.tsx` | Fix PRD panel collapse (CSS hidden) | Small |
| 3 | 1 | `WorkspacePage.tsx` | Fix PRD tab switch (both mounted) | Small |
| 4 | 1 | `WorkspacePage.tsx` | Fix Coder panel collapse (CSS hidden) | Small |
| 5 | 1 | `DashboardPage.tsx` | Fix dashboard pane collapse (CSS hidden) | Small |
| 6 | 2 | `server/routers/workspace.py` | WebSocket → BackgroundSessionManager | Large (see Phase 3 PRD) |
| 7 | 2 | `server/main.py` | Add manager shutdown cleanup | Small |

**Steps 1-5 are the immediate fix.** They can be done in one commit and will solve the user's problem right away.

**Steps 6-7 are the resilience layer.** They make sessions survive even hard disconnects (browser close, network drop). These are already fully specified in `PRD_MISSION_CONTROL_PHASE_3_4.md`.

---

## Build Verification

After each step, run:
```bash
cd ui && npm run build    # TypeScript + Vite build
cd ui && npm run lint     # ESLint
```

### Specific Test Cases

After Layer 1 (CSS fixes):
1. Open split view → start a conversation in Research panel → collapse Research → expand Research → **conversation should still be streaming/active**
2. Open split view → start a conversation in PRD panel → click Passoff tab → click Chat tab → **conversation should still be active**
3. Open split view → start a conversation in Coder panel → collapse Coder → expand Coder → **conversation should still be active**
4. Open dashboard → start a Codex session in a pane → collapse the pane → expand it → **session should still be running**

### Edge Cases to Verify
- Flex layout still works correctly with `hidden` class (no extra space taken by hidden panels)
- `CollapsedPanelBar` click handlers still work
- Passoff tab content still receives correct props when both components are mounted
- No duplicate WebSocket connections (both components mounted but only one should connect)

---

## Context: Key Code Locations

| File | Lines | What |
|------|-------|------|
| `ui/src/pages/WorkspacePage.tsx` | 487-526 | Research panel ternary (collapse) |
| `ui/src/pages/WorkspacePage.tsx` | 529-616 | PRD panel ternary (collapse) |
| `ui/src/pages/WorkspacePage.tsx` | 580-614 | PRD tab ternary (Passoff vs Chat) |
| `ui/src/pages/WorkspacePage.tsx` | 619-658 | Coder panel ternary (collapse) |
| `ui/src/pages/DashboardPage.tsx` | 390-460 | Dashboard pane ternary (collapse) |
| `ui/src/hooks/useWorkspaceChat.ts` | 136-154 | Hook unmount cleanup (closes WebSocket) |
| `ui/src/components/workspace/WorkspaceChat.tsx` | 436-470 | conversationId change handler (disconnect/start) |
| `server/routers/workspace.py` | 1402-1405 | finally block that kills server session |
| `server/services/workspace_chat_session.py` | 1536-1551 | `remove_session()` that destroys the AI client |
| `server/services/workspace_chat_session.py` | 242-270 | `close()` that kills Claude/Codex/Gemini bridges |

## Branch

All work goes on: `claude/add-openai-codex-dashboard-TaqNT`
