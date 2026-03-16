# PRD: Workspace Chat UX — File Visibility + Stuck Message Fix

## Problem Statement

Two issues with the Workspace chat:

### Issue 1: Tool calls show boxes, not file content
Currently, when the agent reads/edits files, the chat shows generic boxes like "Running: cd C:\Users\lober\Greptacular && git status". The user wants to SEE the actual file content flowing by — like Claude Code does with collapsible file previews and inline diffs.

### Issue 2: Messages get stuck until user sends another message
When the user sends a message, the response sometimes doesn't appear until they send a follow-up "where are you?" message. Then both the delayed response AND the follow-up arrive at once.

**Root cause:** `sessionReadyRef` in `useWorkspaceChat.ts` (line 656-660). After every message send, `sessionReadyRef` is set to `false`. It's only set back to `true` on `response_done`. If the backend is slow, the user's next message gets queued in `queuedPayloadRef` instead of sent. The queued message only dispatches on the next `response_done` (line 407-413), which creates the "stuck then burst" behavior.

---

## Phase 1: Fix Stuck Messages (Critical Bug)

**Files:** `ui/src/hooks/useWorkspaceChat.ts`

**The fix:** Allow sending messages while waiting for a response. The `sessionReadyRef` gate was designed to prevent sending before the session is established (before the greeting), NOT to prevent sending during a response. The WebSocket handler on the backend already supports receiving messages at any time (it runs `_stream_to_ws` in a background task specifically so it can still receive messages — see `workspace.py` line 1226-1235).

**Changes:**
1. In `sendMessage()` (line 656): Remove the `sessionReadyRef.current` check for message sends. Always send if WebSocket is open. Keep the queuing logic ONLY for the initial greeting phase (before the first `response_done`).
2. Add a separate `greetingReceivedRef` that starts `false` and is set to `true` on the first `response_done` or `greeting` event. Use THIS for the queue gate instead of `sessionReadyRef`.
3. Remove `sessionReadyRef.current = false` from `sendMessage()` (line 657) — this is the line that causes the stuck behavior.

**Test:** Send a message, wait for streaming to start, send another message before response finishes. Both should appear in order without getting stuck.

---

## Phase 2: Richer Tool Call Display

**Files:**
- `ui/src/hooks/useWorkspaceChat.ts` — `describeToolCall()` function (line 788+) and `case "tool_call"` handler (line 330)
- `ui/src/components/workspace/WorkspaceChat.tsx` — message rendering

**Current behavior:** Tool calls render as system messages with plain text like "Reading server.py" or "Editing WorkspaceChat.tsx". They appear as styled boxes.

**Desired behavior:** Match Claude Code's style:
- **Read/Glob/Grep**: Show as a compact collapsible with file name as the header. When expanded, show the file content or search results. Header is bold text, no box border.
- **Edit**: Show as an inline diff — old text in red, new text in green, with file name header.
- **Write**: Show file name + line count, expandable to show content.
- **Bash**: Show command in monospace, expandable to show output.
- **Other tools**: Compact bold label, no box.

### Backend changes needed

The backend currently sends tool_call messages with `tool` (name) and `input` (the tool parameters). To show file content and diffs, we also need the tool RESULT.

**File:** `server/services/workspace_chat_session.py`

In the message streaming loop, when a tool result comes back from the Claude SDK, emit a new WebSocket event:

```python
{"type": "tool_result", "tool": "Read", "input": {...}, "output": "file content here...", "truncated": false}
```

The Claude Agent SDK already yields tool results — they just need to be forwarded to the WebSocket.

### Frontend changes needed

**File:** `ui/src/hooks/useWorkspaceChat.ts`

1. Add a `case "tool_result"` handler that updates the most recent tool_call message with the result content.
2. Modify the tool_call message type to include an optional `result` field and `expanded` state.

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`

3. Create a new `ToolCallMessage` component that renders differently based on tool type:
   - **Read**: Collapsible code block with syntax highlighting (file extension → language)
   - **Edit**: Side-by-side or inline diff view (old_string → new_string from input)
   - **Write**: Collapsible with line count badge
   - **Bash**: Command in monospace header, output in collapsible
   - **Grep/Glob**: Results list, collapsible
4. Default state: collapsed (just the bold label). Click to expand.
5. Style: no border boxes. Bold tool name, muted file path, subtle background on hover.

### Message format examples

**Read (collapsed):**
```
▸ Read  server/routers/workspace.py
```

**Read (expanded):**
```
▾ Read  server/routers/workspace.py
  ┃ 1005  @router.get("/sessions/{session_id}/walkie-talkie/status")
  ┃ 1006  async def get_walkie_talkie_status(session_id: str):
  ┃ 1007      """Get the walkie-talkie status..."""
  ┃ ...
```

**Edit (collapsed):**
```
▸ Edit  WorkspaceChat.tsx  (+3 -2)
```

**Edit (expanded):**
```
▾ Edit  WorkspaceChat.tsx  (+3 -2)
  - const contextBudgetTotal = (fixedContextMode ?? pendingContextModeProp ?? '200k') === '1m' ? 1_000_000 : 200_000
  + const contextBudgetTotal = sessionContextMode === '1m' ? 1_000_000 : 200_000
```

**Bash (collapsed):**
```
▸ $ git status
```

---

## Phase 3: Polish

1. Add keyboard shortcut to expand/collapse all tool calls at once
2. Add a toggle in chat header: "Show tool details" (on/off, persisted to localStorage)
3. Limit expanded content to 50 lines with a "Show more" button
4. Syntax highlighting for common file types (tsx, py, json, yaml, md)

---

## Implementation Notes

- Phase 1 is the critical bug fix — do this first, it's 15 minutes of work
- Phase 2 backend change requires checking what the Claude Agent SDK yields for tool results. Look at `workspace_chat_session.py`'s `send_message()` method and the `async for msg in client.receive_response()` loop
- The Edit tool's input already contains `old_string` and `new_string` — the diff can be rendered from the INPUT alone, no result needed
- Read tool results need to be forwarded from the SDK response
- Don't break the existing message deduplication logic (REST + WebSocket merge)
