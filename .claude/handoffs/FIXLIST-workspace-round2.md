# FIXLIST: Workspace Round 2

**Date:** 2026-03-30
**Scope:** 8 bugs/missing features in the Workspace chat system
**Priority order:** Critical bugs first, then missing features

---

## Summary

The workspace chat has several issues:
1. Walkie-talkie messages sent via the main input bar never appear as chat bubbles
2. Attachments (images, files) are silently dropped when routing through walkie-talkie
3. `sleep` is already in the security allowlist (NO FIX NEEDED -- confirmed at `security.py` line 55)
4. Input bar does not visually change to green when in walkie-talkie mode
5. Auto-bridge at context threshold is completely unimplemented
6. Past chat selection dropdown in New Chat form is unimplemented
7. Bridge save is never called from the workspace UI
8. Handoff loading only reads `session-latest.md`, ignoring per-conversation scoped handoffs

---

## FIX 1 (CRITICAL): Walkie-talkie messages not showing as bubbles in main chat

**Problem:** When `isLoading && firstMessageSent`, `handleSend` routes through walkie-talkie (line 938-947). It calls `addWalkieTalkieEntry('user', content)` which only adds to the `walkieTalkieLog` array (a separate sidebar log). It does NOT add the message to the `messages` array, so nothing shows in the main chat bubble area. The user types something, it vanishes from the input, and they see nothing in chat.

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`
**Lines:** 938-947 (inside `handleSend`)

**Current code (lines 938-947):**
```tsx
    if (isLoading && firstMessageSent) {
      console.info('[WorkspaceChat] handleSend: routing via walkie-talkie (turn active)')
      sendWalkieTalkie(content)
      addWalkieTalkieEntry('user', content)
      setInputValue('')
      const textarea = inputRef.current
      if (textarea) {
        textarea.style.height = 'auto'
      }
      return
    }
```

**Fix:** After `addWalkieTalkieEntry`, also add a message to the `messages` array so it renders as a chat bubble. The hook exposes `messages` as state via `setMessages` -- but `setMessages` is NOT exported from `useWorkspaceChat`. So the fix must happen in TWO places:

### Step 1: Export a helper from the hook

**File:** `ui/src/hooks/useWorkspaceChat.ts`
**After line 109** (end of `addWalkieTalkieEntry` callback), add a new callback:

```tsx
  const addLocalMessage = useCallback(
    (role: 'user' | 'assistant' | 'system', content: string) => {
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role,
          content,
          timestamp: new Date(),
        },
      ]);
    },
    [],
  );
```

**At line 770** (in the return object), add `addLocalMessage` to the returned interface:

```tsx
  return {
    messages,
    addLocalMessage,   // <-- ADD THIS
    isLoading,
    ...
  };
```

**Also update the `UseWorkspaceChatReturn` interface** (around line 21) to include:
```tsx
  addLocalMessage: (role: 'user' | 'assistant' | 'system', content: string) => void;
```

### Step 2: Use it in WorkspaceChat.tsx

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`
**Where the hook is destructured** (around line 340-360), add `addLocalMessage` to the destructuring.

**Then change lines 938-947 to:**
```tsx
    if (isLoading && firstMessageSent) {
      console.info('[WorkspaceChat] handleSend: routing via walkie-talkie (turn active)')
      sendWalkieTalkie(content)
      addWalkieTalkieEntry('user', content)
      addLocalMessage('user', `[walkie-talkie] ${content}`)
      setInputValue('')
      const textarea = inputRef.current
      if (textarea) {
        textarea.style.height = 'auto'
      }
      return
    }
```

The `[walkie-talkie]` prefix distinguishes these from normal messages visually. The main chat area will now show what the user sent.

---

## FIX 2 (CRITICAL): Attachments silently dropped in walkie-talkie mode

**Problem:** When `handleSend` routes via walkie-talkie (line 938), it calls `sendWalkieTalkie(content)` with only the text. The `pendingImages` and `pendingFiles` arrays are never checked or included. Images and file attachments are silently dropped.

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`
**Lines:** 931-947

**Current code:** The walkie-talkie early-return at line 938 happens BEFORE the file-processing block at lines 952-964 and the attachments block at line 967.

**Fix:** Move the file-content-appending logic ABOVE the walkie-talkie check, or at minimum warn the user. The walkie-talkie channel (`sendWalkieTalkie`) only accepts a string -- it cannot transport binary image data. Two options:

### Option A (Recommended): Warn and drop with notice
Add before the `sendWalkieTalkie` call at line 940:

```tsx
    if (isLoading && firstMessageSent) {
      console.info('[WorkspaceChat] handleSend: routing via walkie-talkie (turn active)')

      // Append file text contents to walkie-talkie message (images cannot be sent)
      let wtContent = content
      if (pendingFiles.length > 0) {
        const fileTexts = await Promise.all(
          pendingFiles.map(async (file) => {
            try {
              const text = await fileToText(file)
              return `\n--- File: ${file.name} ---\n${text}\n--- End: ${file.name} ---`
            } catch {
              return `\n--- File: ${file.name} (could not read) ---`
            }
          })
        )
        wtContent = wtContent + fileTexts.join('\n')
      }
      if (pendingImages.length > 0) {
        wtContent += `\n[Note: ${pendingImages.length} image(s) could not be sent via walkie-talkie -- images require a new turn]`
      }

      sendWalkieTalkie(wtContent)
      addWalkieTalkieEntry('user', wtContent)
      addLocalMessage('user', `[walkie-talkie] ${content}${pendingImages.length > 0 ? ` (+${pendingImages.length} images dropped)` : ''}`)
      setInputValue('')
      setPendingImages([])
      setPendingFiles([])
      const textarea = inputRef.current
      if (textarea) {
        textarea.style.height = 'auto'
      }
      return
    }
```

**Note:** This also requires making `handleSend` an async function. Check line 931 -- it already IS `async` (`const handleSend = useCallback(async () => {`). Good.

---

## FIX 3: CONFIRMED NOT NEEDED

`sleep` is already in `ALLOWED_COMMANDS` at `security.py` line 55:
```python
    "sleep",
```
No action required.

---

## FIX 4 (VISUAL): Make input bar visually GREEN when in walkie-talkie mode

**Problem:** When the agent is running and `firstMessageSent` is true, messages route through walkie-talkie. But the main input textarea looks identical to normal mode. The user has no visual cue that they are in walkie-talkie mode.

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`
**Line:** 1883

**Current code (line 1883):**
```tsx
className="flex-1 resize-y min-h-[44px] max-h-[240px] rounded-md border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none ring-ring focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
```

**Fix:** Make the className dynamic based on walkie-talkie state:
```tsx
className={`flex-1 resize-y min-h-[44px] max-h-[240px] rounded-md border px-3 py-2 text-sm outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50 ${
  isLoading && firstMessageSent
    ? 'border-green-500 bg-green-50 dark:bg-green-950/20 text-foreground placeholder:text-green-600 dark:placeholder:text-green-400 ring-green-400'
    : 'border-border bg-input text-foreground placeholder:text-muted-foreground ring-ring'
}`}
```

**Also update the send button** at line 1893. Currently amber:
```tsx
className="bg-amber-600 hover:bg-amber-700 text-white"
```

Change to green to match:
```tsx
className="bg-green-600 hover:bg-green-700 text-white"
```

---

## FIX 5 (FEATURE): Auto-bridge at context threshold -- NOT IMPLEMENTED

**Problem:** The workspace system prompt (line 326-327 of `workspace_chat_session.py`) tells the agent to write a handoff "when approaching context limits." But there is no server-side mechanism to auto-save a bridge when token usage crosses a threshold. DunkStack has this (`_auto_bridge_save` at `dunkstack.py` line 864), but workspace does not.

**File:** `server/services/workspace_chat_session.py`

**What needs to happen:**

1. The hook already tracks `totalTokens` and `contextWindow` in the frontend. The backend already sends `token_usage` events via WebSocket.

2. Add a check in the WebSocket message handler (in `server/routers/workspace.py`) or in the session's token tracking. When `totalTokens / contextWindow > 0.80` (80%), auto-save a bridge.

3. Implementation approach:

**In `server/routers/workspace.py`**, add a helper similar to DunkStack's `_auto_bridge_save`:

```python
async def _workspace_auto_bridge(session, conversation_id: int, usage_pct: float):
    """Auto-save bridge when context usage exceeds threshold."""
    from pathlib import Path
    from datetime import datetime, timezone

    handoff_dir = Path.home() / ".autoforge" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conv_label = f"session-{conversation_id}" if conversation_id else "session-latest"
    path = handoff_dir / f"{conv_label}.md"

    content = f"""# Auto-Bridge Save -- {timestamp}

## Reason
Context usage reached {usage_pct:.1f}% -- auto-saving for session continuity.

## Instructions
This bridge was auto-generated. The agent should commit work and prepare for handoff.
"""
    path.write_text(content, encoding="utf-8")
    logger.info("Workspace auto-bridge saved to %s at %.1f%%", path, usage_pct)
```

4. Call this from the token tracking path in the WebSocket handler. The session object already has `total_tokens` -- add a check after each `token_usage` event.

**Estimated difficulty:** 4/10 -- straightforward port of DunkStack pattern.

---

## FIX 6 (FEATURE): Past chat selection dropdown in New Chat form -- NOT IMPLEMENTED

**Problem:** The New Chat form in `WorkspaceSidebar.tsx` (lines 186-301) has name, category, provider, model, and effort inputs. But there is no dropdown to select a past conversation to fork/resume from. The user cannot seed a new chat with context from a previous one.

**File:** `ui/src/components/workspace/WorkspaceSidebar.tsx`
**Lines:** 186-301 (the `showNewChatForm` block)

**What needs to happen:**

1. Add a `<select>` or combobox in the new-chat form that lists existing conversations.
2. When a past conversation is selected, pass its ID to the backend so the new conversation's system prompt can include the past conversation's handoff/summary.
3. The backend already has `GET /api/workspace/bridge?conversation_id=N` which returns the handoff for a specific conversation.

**Implementation sketch:**

In `WorkspaceSidebar.tsx`, add state:
```tsx
const [forkFromConvId, setForkFromConvId] = useState<number | null>(null)
```

Add a dropdown in the form that maps `conversations` data to options. Pass `forkFromConvId` to `createConversationMut.mutate()` as a new field. The backend create-conversation endpoint would then load the referenced conversation's handoff into the new conversation's system prompt.

**Estimated difficulty:** 5/10 -- needs frontend dropdown + backend integration.

---

## FIX 7 (FEATURE): Bridge save never called from workspace UI

**Problem:** The backend has `POST /api/workspace/bridge/save` (line 1016 of `server/routers/workspace.py`). But NO workspace UI component ever calls it. The `handleEndSession` function (line 1007 of `WorkspaceChat.tsx`) sends a walkie-talkie message telling the agent to write a handoff, but it relies entirely on the agent writing it. The UI should also explicitly call the save endpoint.

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`
**Line:** 1007-1012

**Current code:**
```tsx
  const handleEndSession = useCallback(() => {
    if (!isLoading) return
    const endMessage = `End session. Write your handoff summary...`
    sendWalkieTalkie(endMessage)
    addWalkieTalkieEntry('user', 'End Session (handoff requested)')
  }, [isLoading, sendWalkieTalkie, addWalkieTalkieEntry])
```

**Fix:** After sending the walkie-talkie end message, also call the bridge save API:

```tsx
  const handleEndSession = useCallback(async () => {
    if (!isLoading) return
    const endMessage = `End session. Write your handoff summary (as described in your system prompt) including: summary of what was discussed, decisions made, current state, and next steps. Then stop polling and end your turn.`
    sendWalkieTalkie(endMessage)
    addWalkieTalkieEntry('user', 'End Session (handoff requested)')

    // Also save bridge via REST as a safety net
    const effectiveId = conversationId ?? activeConversationId
    try {
      await fetch('/api/workspace/bridge/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reason: 'end_session',
          conversation_id: effectiveId,
          current_task: 'Session ended by user',
        }),
      })
    } catch (e) {
      console.warn('Bridge save failed:', e)
    }
  }, [isLoading, sendWalkieTalkie, addWalkieTalkieEntry, conversationId, activeConversationId])
```

**Note:** Import or use the existing `fetchJSON` helper from `api.ts` instead of raw `fetch` if preferred. Also need to add a corresponding API function in `ui/src/lib/api.ts`:

```tsx
export async function workspaceSaveBridge(data: {
  reason?: string
  current_task?: string
  progress?: string
  next_steps?: string
  open_questions?: string
  conversation_id?: number | null
}): Promise<{ status: string; timestamp: string; filename: string }> {
  return fetchJSON('/workspace/bridge/save', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
```

---

## FIX 8 (BUG): Only loads session-latest.md -- needs per-conversation scoping

**Problem:** The system prompt builder in `workspace_chat_session.py` (lines 259-275) only reads `session-latest.md` regardless of which conversation is being opened. If the user has 5 conversations, they ALL get the same handoff from the last session that ended -- which may be completely irrelevant.

**File:** `server/services/workspace_chat_session.py`
**Lines:** 259-275

**Current code:**
```python
    handoff_section = ""
    handoff_dir = os.path.join(str(Path.home()), ".autoforge", "handoffs")
    latest_handoff = os.path.join(handoff_dir, "session-latest.md")
    try:
        if os.path.isfile(latest_handoff):
            with open(latest_handoff, "r", encoding="utf-8", errors="replace") as f:
                handoff_content = f.read(10000)
            if handoff_content.strip():
                handoff_section = f"""
## Previous Session Context
The following handoff was written by the previous agent session. Use it for continuity:

{handoff_content}
"""
    except OSError:
        pass
```

**Fix:** The function `_build_system_prompt` needs a `conversation_id` parameter. When present, try `session-{conversation_id}.md` first, falling back to `session-latest.md`:

```python
    handoff_section = ""
    handoff_dir = os.path.join(str(Path.home()), ".autoforge", "handoffs")

    # Try conversation-specific handoff first, then fall back to latest
    candidates = []
    if conversation_id:
        candidates.append(os.path.join(handoff_dir, f"session-{conversation_id}.md"))
    candidates.append(os.path.join(handoff_dir, "session-latest.md"))

    for handoff_path in candidates:
        try:
            if os.path.isfile(handoff_path):
                with open(handoff_path, "r", encoding="utf-8", errors="replace") as f:
                    handoff_content = f.read(10000)
                if handoff_content.strip():
                    handoff_section = f"""
## Previous Session Context
The following handoff was written by the previous agent session. Use it for continuity:

{handoff_content}
"""
                    break  # Use the first valid handoff found
        except OSError:
            continue
```

**Also:** Update the `_build_system_prompt` function signature to accept `conversation_id: Optional[int] = None` and pass it from the caller. The `start()` method (which calls `_build_system_prompt`) already knows the `conversation_id`.

Check the `_build_system_prompt` signature (around line 140) and the `start()` method call site. The `start()` method stores `self.conversation_id` -- pass it through.

**Also update the bridge save** (Fix 7) to use `conversation_id` in the filename so the handoff is scoped per-conversation. The backend `save_workspace_bridge` already does this (line 1027): `conv_label = f"session-{req.conversation_id}" if req.conversation_id else "session-latest"`. Good -- the save side is correct, only the load side needs fixing.

---

## Checklist

- [ ] **FIX 1** -- Add `addLocalMessage` to `useWorkspaceChat` hook return; use it in `handleSend` walkie-talkie path to show bubbles
- [ ] **FIX 2** -- Process `pendingFiles` before walkie-talkie send; warn about dropped images
- [ ] ~~FIX 3~~ -- No action needed (`sleep` already allowed)
- [ ] **FIX 4** -- Green border/bg on input textarea + green send button when in walkie-talkie mode
- [ ] **FIX 5** -- Implement `_workspace_auto_bridge` in workspace router, triggered at 80% context usage
- [ ] **FIX 6** -- Add past-conversation dropdown to New Chat form in `WorkspaceSidebar.tsx`
- [ ] **FIX 7** -- Call bridge save API from `handleEndSession`; add `workspaceSaveBridge` to `api.ts`
- [ ] **FIX 8** -- Make `_build_system_prompt` accept `conversation_id`; try per-conversation handoff file first
- [ ] **VERIFY** -- Run `cd ui && npm run build` after all changes
- [ ] **VERIFY** -- Run `cd ui && npm run lint` after all changes
