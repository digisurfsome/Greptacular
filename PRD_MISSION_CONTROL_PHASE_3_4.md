# PRD: Mission Control Phase 3-4 — Viewer Protocol & Dashboard Integration

## Overview

This PRD is a handoff document for a fresh agent to implement Phases 3 and 4 of the "Mission Control" background session architecture. **Phases 1 and 2 are already complete and committed.** This document provides the focused context needed to implement the remaining work.

### What Was Already Built (DO NOT REBUILD)

**Phase 1** (committed, branch `claude/add-openai-codex-dashboard-TaqNT`):
- `ui/src/hooks/useWorkspaceChat.ts`: Replaced the hard 10-minute timeout with a provider-aware system. Codex/Gemini get a non-destructive 30-min notice instead of killing the session. Claude keeps the 10-min safety timeout.
- `ui/src/components/workspace/WorkspaceSidebar.tsx`: Changed `streamingConversationId?: number | null` prop to `streamingIds?: Set<number>`. Updated `isStreaming` check to `streamingIds?.has(conv.id) ?? false`.
- `ui/src/pages/DashboardPage.tsx`: Now passes full `streamingIds` Set to sidebar instead of `firstStreamingId`.
- `ui/src/pages/WorkspacePage.tsx`: Changed from single `streamingConversationId` state to `streamingIds: Set<number>` with add/delete logic.

**Phase 2** (committed, same branch):
- `server/services/background_session_manager.py` (963 lines): The core engine.
  - `SessionState` enum: queued/running/streaming/waiting_input/completed/failed/cancelled
  - `OutputBuffer`: Ring buffer (2000 events) with monotonic sequence numbers, batch SQLite persistence
  - `BackgroundSession`: Wraps `WorkspaceChatSession`, runs as asyncio.Task, manages viewers, input queue, heartbeat
  - `BackgroundSessionManager`: Singleton, 10-session concurrency limit, auto-cleanup after 1 hour
  - Singleton access via `get_background_session_manager()`
- `server/services/workspace_database.py`: Added `WorkspaceSessionEvent` model for event persistence/replay.

### What Needs to Be Built

**Phase 3**: Transform the WebSocket endpoint from "session owner" to "viewer" that attaches/detaches from background sessions.

**Phase 4**: Update the dashboard UI to show session status, add session management controls, and make the sidebar self-sufficient.

---

## Phase 3: Viewer WebSocket Protocol

### The Problem

Currently in `server/routers/workspace.py` (line 1106), the WebSocket handler:
1. Generates `session_id = f"ws-{id(websocket)}"` — tied to the WebSocket object
2. Creates a `WorkspaceChatSession` directly via `ws_create_session()`
3. Calls `session.start()` and `session.send_message()` directly, streaming results to the single WebSocket
4. In the `finally` block (line 1402-1405), calls `ws_remove_session(session_id)` — **destroying the session on disconnect**

### The Solution

Transform the WebSocket handler so it routes through the `BackgroundSessionManager` instead of managing sessions directly. The WebSocket becomes a "viewer" that can attach and detach.

### File: `server/routers/workspace.py`

#### New WebSocket Protocol

Replace the `workspace_chat_websocket` function (lines 1106-1405) with a new viewer-mode protocol:

**Client → Server messages (keep existing + add new):**
```
{"type": "start", ...}          → Create a BackgroundSession and attach as viewer
{"type": "message", ...}        → Submit message to attached background session
{"type": "walkie_talkie", ...}  → Inject walkie-talkie message
{"type": "answer", ...}         → Answer structured questions
{"type": "ping"}                → Keepalive (unchanged)
{"type": "detach"}              → NEW: Stop watching (session keeps running)
{"type": "attach", "session_id": "...", "since_seq": 0}  → NEW: Attach to existing session with catch-up
```

**Server → Client messages (keep existing + add new):**
```
All existing types (text, tool_call, token_usage, response_done, error, etc.)
{"type": "session_created", "session_id": "...", "conversation_id": int}  → NEW
{"type": "attached", "session_id": "...", "state": "...", "seq": int}     → NEW
{"type": "replay", "events": [...]}         → NEW: Catch-up events
{"type": "replay_done", "current_seq": int} → NEW: Replay complete
{"type": "heartbeat", "session_id": "...", "state": "...", "seq": int, "uptime_seconds": float}  → NEW
{"type": "session_completed"}               → NEW
{"type": "session_failed", "error": "..."}  → NEW
```

#### Implementation Details

```python
@router.websocket("/ws")
async def workspace_chat_websocket(websocket: WebSocket):
    await websocket.accept()

    manager = get_background_session_manager()
    attached_session_id: str | None = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "start":
                # Create a NEW background session and attach as viewer
                # Extract all the same params as before (conversation_id, working_directory,
                # context_mode, cost_settings, model, provider)
                # Keep ALL the existing validation logic (context_mode safety, DB cross-check, etc.)

                bg_session = await manager.create_session(
                    conversation_id=conversation_id,
                    provider=provider or "claude",
                    model=model or "opus",
                    working_directory=working_directory,
                    context_mode=context_mode,
                    cost_settings=cost_settings,
                )

                attached_session_id = bg_session.session_id
                seq = manager.attach_viewer(bg_session.session_id, websocket)

                await websocket.send_json({
                    "type": "session_created",
                    "session_id": bg_session.session_id,
                    "conversation_id": bg_session.conversation_id,
                })

                # The session's _run() loop starts automatically and broadcasts
                # events to all viewers. No need to call session.start() here.

            elif msg_type == "attach":
                # Attach to an EXISTING background session (for reconnection/catch-up)
                session_id = message.get("session_id")
                since_seq = message.get("since_seq", 0)

                session = manager.get_session(session_id)
                if not session:
                    await websocket.send_json({"type": "error", "content": "Session not found"})
                    continue

                # Detach from previous session if any
                if attached_session_id:
                    manager.detach_viewer(attached_session_id, websocket)

                attached_session_id = session_id
                current_seq = manager.attach_viewer(session_id, websocket)

                # Replay missed events
                events = session._output_buffer.get_since(since_seq)
                if events:
                    await websocket.send_json({"type": "replay", "events": events})
                await websocket.send_json({
                    "type": "replay_done",
                    "current_seq": current_seq,
                    "state": session.state.value,
                })

            elif msg_type == "message":
                if not attached_session_id:
                    await websocket.send_json({"type": "error", "content": "No active session. Send 'start' first."})
                    continue
                # Extract content, attachments, library_file_ids (same as current code)
                await manager.submit_message(attached_session_id, {
                    "type": "message",
                    "content": user_content,
                    "attachments": raw_attachments,
                    "library_file_ids": library_file_ids,
                })

            elif msg_type == "walkie_talkie":
                if attached_session_id:
                    session = manager.get_session(attached_session_id)
                    if session and session._chat_session:
                        await session._chat_session.queue_walkie_talkie_message(message.get("content", ""))
                        await websocket.send_json({"type": "walkie_talkie_queued", "content": message.get("content", "")[:100]})

            elif msg_type == "answer":
                if attached_session_id:
                    # Format answers same as current code, submit as message
                    answers = message.get("answers", {})
                    # ... same formatting logic ...
                    await manager.submit_message(attached_session_id, {"type": "message", "content": user_response})

            elif msg_type == "detach":
                if attached_session_id:
                    manager.detach_viewer(attached_session_id, websocket)
                    attached_session_id = None
                    await websocket.send_json({"type": "detached"})

    except WebSocketDisconnect:
        pass
    finally:
        # CRITICAL: detach viewer, do NOT destroy the session
        if attached_session_id:
            manager.detach_viewer(attached_session_id, websocket)
```

#### Key Points
1. **Keep all existing validation logic** from the current `start` handler (context_mode safety net, DB cross-check for model/provider, walkie-talkie settings).
2. The `_stream_with_walkie_talkie` helper is no longer needed for background sessions — the `BackgroundSession._run()` loop handles streaming internally and broadcasts to viewers.
3. However, walkie-talkie messages need to be forwarded to the underlying `WorkspaceChatSession` directly.
4. The `finally` block MUST call `detach_viewer()`, NOT `remove_session()`.

#### New REST Endpoints (add to same file)

```python
@router.get("/sessions")
async def list_background_sessions():
    """List all background sessions with status."""
    manager = get_background_session_manager()
    return manager.list_sessions(include_completed=True)

@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    manager = get_background_session_manager()
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.to_status_dict()

@router.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: str):
    manager = get_background_session_manager()
    await manager.cancel_session(session_id)
    return {"status": "cancelled"}

@router.get("/sessions/{session_id}/events")
async def get_session_events(session_id: str, since_seq: int = 0, limit: int = 200):
    """REST fallback for getting session events (alternative to WebSocket replay)."""
    manager = get_background_session_manager()
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    events = session._output_buffer.get_since(since_seq)
    if limit:
        events = events[:limit]
    return {"events": events, "current_seq": session._output_buffer._seq}
```

### File: `ui/src/hooks/useWorkspaceChat.ts`

#### Changes Needed

1. **Add `attachedSessionId` state** to track which background session this viewer is connected to:
```typescript
const [attachedSessionId, setAttachedSessionId] = useState<string | null>(null);
const lastSeqRef = useRef<number>(0);
```

2. **Update the `ws.onopen` handler**: On reconnect, send an `attach` message instead of `start` if we have an `attachedSessionId`:
```typescript
ws.onopen = () => {
    // ... existing setup ...
    if (wasReconnect && attachedSessionId) {
        // Reattach to existing background session
        ws.send(JSON.stringify({
            type: "attach",
            session_id: attachedSessionId,
            since_seq: lastSeqRef.current,
        }));
    }
    // Otherwise, wait for start() to be called
};
```

3. **Handle new message types in `ws.onmessage`**:
```typescript
case "session_created":
    setAttachedSessionId(parsed.session_id);
    lastSeqRef.current = 0;
    break;
case "replay":
    // Process replayed events (same handlers as live events)
    for (const event of parsed.events) {
        processEvent(event);  // reuse existing event processing
        lastSeqRef.current = event._seq || lastSeqRef.current;
    }
    break;
case "replay_done":
    lastSeqRef.current = parsed.current_seq;
    // Transition from "catching up" to "live"
    break;
case "heartbeat":
    // Update UI with session status, reset any disconnect warning timers
    lastSeqRef.current = parsed.seq;
    break;
case "session_completed":
    setIsLoading(false);
    sessionReadyRef.current = true;
    break;
case "session_failed":
    setIsLoading(false);
    sessionReadyRef.current = true;
    setMessages(prev => [...prev, {
        id: `fail-${Date.now()}`,
        role: "system",
        content: `Session failed: ${parsed.error}`,
        timestamp: new Date(),
    }]);
    break;
```

4. **Update sequence tracking**: In ALL event handlers that process live events (text, tool_call, etc.), update `lastSeqRef.current` from `event._seq` if present.

5. **Expose `attachedSessionId` in the return value** so parent components can save/restore it:
```typescript
return {
    // ... existing returns ...
    attachedSessionId,
};
```

6. **Update cleanup**: On unmount, the hook should send a `detach` message instead of closing causing session destruction:
```typescript
// In cleanup effect:
if (wsRef.current?.readyState === WebSocket.OPEN && attachedSessionIdRef.current) {
    wsRef.current.send(JSON.stringify({ type: "detach" }));
}
```

---

## Phase 4: Dashboard Integration

### File: `ui/src/hooks/useBackgroundSessions.ts` (NEW)

Create a React Query hook for polling background session status:

```typescript
import { useQuery } from '@tanstack/react-query';

interface BackgroundSessionStatus {
    session_id: string;
    conversation_id: number;
    state: string;
    provider: string;
    model: string;
    created_at: string;
    started_at: string | null;
    completed_at: string | null;
    uptime_seconds: number;
    viewer_count: number;
    event_count: number;
}

export function useBackgroundSessions() {
    return useQuery<BackgroundSessionStatus[]>({
        queryKey: ['background-sessions'],
        queryFn: async () => {
            const res = await fetch('/api/workspace/sessions');
            if (!res.ok) throw new Error('Failed to fetch sessions');
            return res.json();
        },
        refetchInterval: 5000,  // Poll every 5 seconds
    });
}
```

### File: `ui/src/components/workspace/WorkspaceSidebar.tsx`

Make the sidebar self-sufficient for showing session status by using the `useBackgroundSessions` hook:

```typescript
// Instead of relying on streamingIds prop alone, ALSO query background sessions
const { data: bgSessions } = useBackgroundSessions();

// Build a map of conversation_id → session state
const sessionStateMap = useMemo(() => {
    const map = new Map<number, { state: string; provider: string; uptime: number }>();
    bgSessions?.forEach(s => {
        map.set(s.conversation_id, { state: s.state, provider: s.provider, uptime: s.uptime_seconds });
    });
    return map;
}, [bgSessions]);
```

Then for each conversation item, show richer indicators:
- **Running/Streaming**: Cyan pulsing dot + shimmer (existing) + duration badge ("2h 15m")
- **Waiting Input**: Yellow pulsing dot
- **Completed (recent)**: Green check for 5 minutes after completion
- **Failed**: Red dot with error indicator

### File: `ui/src/pages/DashboardPage.tsx`

1. **Save/restore `attachedSessionId` per pane** in the pane state and localStorage.
2. When a pane mounts, if it has an `attachedSessionId`, send `attach` instead of `start`.
3. Add a session status bar at the top of each pane showing: `Running 2h 15m | Codex | 47 events | [Cancel]`

### File: `ui/src/components/workspace/WorkspaceChat.tsx`

Add a session status header above the chat messages:

```tsx
{attachedSessionId && (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-card border-b border-border text-xs">
        <span className={`h-2 w-2 rounded-full ${isRunning ? 'bg-cyan-500 animate-pulse' : 'bg-zinc-500'}`} />
        <span className="text-muted-foreground">
            Session {attachedSessionId.slice(0, 8)}
        </span>
        <span className="text-muted-foreground">|</span>
        <span className="font-medium">{provider}</span>
        <span className="text-muted-foreground">|</span>
        <span>{formatDuration(uptimeSeconds)}</span>
        <div className="ml-auto">
            <Button variant="ghost" size="sm" onClick={onCancel} className="h-5 px-2 text-[10px]">
                Cancel
            </Button>
        </div>
    </div>
)}
```

---

## Context: Key Code Patterns

### How BackgroundSession._run() Works (already built)

The background session's `_run()` method:
1. Creates the underlying `WorkspaceChatSession` via `ws_create_session()`
2. Calls `session.start()` and iterates the async generator
3. Each event (dict) is passed to `_output_buffer.append(event)` which assigns a sequence number
4. Each event is broadcast to all connected `_viewers` via `_broadcast(event)`
5. Waits for messages from `_input_queue` (submitted by viewers)
6. Calls `session.send_message()` for each message, repeating steps 3-4
7. Handles exceptions: marks session as FAILED, broadcasts error event
8. Runs a heartbeat loop every 10 seconds

### How Events Flow Currently (in workspace.py)

Currently, `_stream_with_walkie_talkie()` receives events from the session generator and sends them directly to a single WebSocket. With background sessions, events are:
1. Generated by `WorkspaceChatSession.start()` or `.send_message()`
2. Captured by `BackgroundSession._run()`
3. Stored in `OutputBuffer` with a sequence number
4. Broadcast to all viewers in `_viewers` set

### WorkspaceChatSession Integration

The `BackgroundSession` uses `WorkspaceChatSession` from `server/services/workspace_chat_session.py`. Key methods it calls:
- `session.start()` → async generator yielding event dicts
- `session.send_message(content, attachments, library_file_ids)` → async generator yielding event dicts
- `session.queue_walkie_talkie_message(content)` → queues message for PreToolUse hook
- `session.close()` → cleanup

### The OutputBuffer Catch-Up Protocol

When a viewer connects with `since_seq=50`:
1. `OutputBuffer.get_since(50)` returns all events with seq > 50
2. First checks the in-memory ring buffer (deque of last 2000 events)
3. If seq is too old for the ring buffer, falls back to SQLite query
4. Returns events sorted by sequence number

---

## Implementation Order

1. **Phase 3a**: Add REST endpoints for session management (list, status, cancel, events)
2. **Phase 3b**: Transform WebSocket handler to use BackgroundSessionManager
3. **Phase 3c**: Update `useWorkspaceChat.ts` for new protocol (attach, replay, heartbeat, detach)
4. **Phase 4a**: Create `useBackgroundSessions` hook
5. **Phase 4b**: Update WorkspaceSidebar with self-sufficient session indicators
6. **Phase 4c**: Add session status bar to WorkspaceChat
7. **Phase 4d**: Update DashboardPage for pane session persistence

### Build Verification

After each phase, run:
```bash
cd ui && npm run build    # TypeScript + Vite build
cd ui && npm run lint     # ESLint
```

The Python backend has no type-check or lint requirement for the router changes, but ensure imports are clean.

---

## Branch

All work goes on: `claude/add-openai-codex-dashboard-TaqNT`

## Files Summary

| File | Phase | Action |
|------|-------|--------|
| `server/routers/workspace.py` | 3 | Major refactor of WebSocket handler + new REST endpoints |
| `ui/src/hooks/useWorkspaceChat.ts` | 3 | Add attach/replay/heartbeat/detach protocol |
| `ui/src/hooks/useBackgroundSessions.ts` | 4 | NEW - React Query hook for session polling |
| `ui/src/components/workspace/WorkspaceSidebar.tsx` | 4 | Add self-sufficient session status via useBackgroundSessions |
| `ui/src/components/workspace/WorkspaceChat.tsx` | 4 | Add session status header bar |
| `ui/src/pages/DashboardPage.tsx` | 4 | Pane session persistence (save/restore attachedSessionId) |
