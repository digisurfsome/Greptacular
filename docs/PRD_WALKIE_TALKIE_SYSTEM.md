# PRD: Walkie-Talkie Communication System

## CRITICAL BOUNDARIES

**BUILD IN:** Workspace session system only (files under `ui/src/components/workspace/`, `ui/src/pages/WorkspacePage.tsx`, `ui/src/hooks/useWorkspaceChat.ts`, `server/routers/workspace.py`, `server/services/workspace_chat_session.py`, `server/services/workspace_database.py`, `server/schemas.py`)

**DO NOT TOUCH:** AutoForge app builder system. This means: do NOT modify `agent.py`, `client.py`, `autonomous_agent_demo.py`, `parallel_orchestrator.py`, `mcp_server/feature_mcp.py`, or any files in `server/routers/` that are NOT `workspace.py` or `settings.py`. Do NOT modify `server/services/assistant_chat_session.py`. The AutoForge system is production-stable and must not be altered.

**DO NOT TOUCH:** Any existing functionality in the workspace. The passoff system, conversation management, library, repos, cost controls, context budget bars, usage dashboard -- all of these must continue working exactly as they do now.

---

## 1. OVERVIEW

### What Is The Walkie-Talkie System?

The walkie-talkie system enables **bidirectional communication between the user and a running Claude agent within a single sustained API call**. Currently, when the user sends a message, Claude responds, and that's one round-trip. The walkie-talkie allows the user to inject messages into an agent that is ACTIVELY working (calling tools, writing code, doing research) without interrupting its API call.

### Why Does This Matter?

**Cost optimization:** On the 1M token context window (API billing), each API call has overhead. If the agent needs 5 back-and-forth exchanges to build a feature, that's 5 API calls. With walkie-talkie, the agent stays in one sustained API call while receiving user input via tool-call interception. One API call instead of five = 3-5x cost reduction.

**Steering:** The user can redirect the agent mid-work. "Actually, use PostgreSQL instead of SQLite" -- sent while the agent is building the database layer, received before it commits to SQLite.

**Collaboration:** The agent can request clarification without ending its turn. "I found two approaches for auth. Which do you prefer?" -- then waits for user response and continues.

### How It Works (High Level)

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE API CALL                          │
│                                                             │
│  Agent working: Read → Edit → Bash → Read → ...            │
│                              ↑                              │
│                    PreToolUse Hook fires                    │
│                    Checks message queue                     │
│                              ↓                              │
│                    Message found? ──Yes──→ Inject message   │
│                         │                  as tool result   │
│                         No                       ↓          │
│                         │                  Agent processes   │
│                         ↓                  and continues     │
│                    Tool proceeds                             │
│                    normally                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. ARCHITECTURE

### 2.1 Message Queue (Per-Session, In-Memory)

Each `WorkspaceChatSession` gets a message queue (async queue). Messages flow:

```
User types in UI
    → WebSocket: {"type": "walkie_talkie", "content": "..."}
    → Server: workspace router handler
    → Queue: session.walkie_talkie_queue.put(message)
```

### 2.2 Agent Message Interception (PreToolUse Hook)

The Claude Agent SDK already supports `PreToolUse` hooks (used for bash security). We add a second hook that:

1. Fires before EVERY tool call the agent makes
2. Checks the session's message queue (non-blocking)
3. If a message is waiting:
   - Consumes it from the queue
   - Returns a "block" result with the user's message injected
   - The agent sees: "User message received: [content]. Address this before continuing."
4. If no messages: returns None (tool proceeds normally)

### 2.3 Agent-Initiated Waiting (Wait Tool)

For the reverse direction (agent wants user input), we add a lightweight MCP server OR a custom tool mechanism:

**Option A (Recommended): Bash-based wait command**
- Agent writes a message to a known file: `echo "WALKIE_TALKIE_WAIT: What database should I use?" > ~/.autoforge/.walkie_talkie_signal`
- The PreToolUse hook on the NEXT Bash/tool call detects this signal file
- Server sends WebSocket message to UI: `{"type": "agent_waiting", "question": "..."}`
- CountdownTimerBar activates
- When user responds, message goes to queue
- Next tool call hook delivers the message
- Signal file is cleaned up

**Option B: MCP Server**
- Add a walkie-talkie MCP server with two tools: `check_messages()` and `wait_for_input(question)`
- `check_messages()`: Non-blocking, returns any queued messages or "No messages"
- `wait_for_input(question)`: Blocking, sends question to UI, waits for response up to timeout
- Requires adding MCP server config to `WorkspaceChatSession`

**Option C (Simplest for MVP): Agent output parsing**
- Agent outputs structured text: `[WAITING]What database should I use?[/WAITING]`
- The WebSocket handler in workspace.py detects this pattern in streamed text
- UI shows the CountdownTimerBar with the question
- User responds via walkie-talkie input
- Response queued for next tool call interception
- This requires NO changes to the SDK client setup

**Recommendation: Start with Option C for the wait mechanism (agent output parsing) because it requires zero SDK configuration changes. The PreToolUse hook handles message injection. Together they cover both directions.**

### 2.4 Check Frequency

The settings already define `comm_check_frequency` with values:
- `per_feature`: Check every N tool calls (e.g., every 10th). In workspace context, interpret as "periodic"
- `every_tool_call`: Check before every single tool call (most responsive, slight overhead)
- `never`: Walkie-talkie disabled

### 2.5 Auto-Reply

When `comm_auto_reply` is enabled and the agent is waiting:
1. CountdownTimerBar counts down from `comm_wait_timeout` seconds
2. When countdown reaches zero, auto-sends "Continue with your best judgment" to the queue
3. Agent receives this and proceeds with its own decision

When `comm_auto_reply` is disabled:
1. CountdownTimerBar still shows but doesn't auto-fire
2. Agent stays in waiting state until user explicitly responds
3. After timeout, agent receives "No response received within timeout. Proceed with your best judgment."

---

## 3. FILE-BY-FILE IMPLEMENTATION PLAN

### 3.1 Backend Files

#### `server/services/workspace_chat_session.py` (MODIFY)

**Changes:**
1. Add `walkie_talkie_queue` attribute to `WorkspaceChatSession.__init__()`:
   ```python
   import asyncio
   # In __init__:
   self.walkie_talkie_queue: asyncio.Queue[str] = asyncio.Queue()
   self.walkie_talkie_enabled: bool = True  # controlled by settings
   self.walkie_talkie_waiting: bool = False  # true when agent is waiting for input
   ```

2. Add `queue_walkie_talkie_message()` method:
   ```python
   async def queue_walkie_talkie_message(self, content: str) -> None:
       """Queue a walkie-talkie message for the running agent to receive."""
       await self.walkie_talkie_queue.put(content)
   ```

3. Add walkie-talkie PreToolUse hook in `start()` method, alongside the existing bash_security_hook:
   ```python
   async def walkie_talkie_hook(input_data, tool_use_id=None, context=None):
       """Check for walkie-talkie messages before each tool call."""
       if not self.walkie_talkie_enabled:
           return None  # Disabled, proceed normally

       try:
           message = self.walkie_talkie_queue.get_nowait()
           # Message found! Block the tool and inject the message
           return SyncHookJSONOutput(
               hookSpecificOutput={
                   "hookEventName": "PreToolUse",
                   "decision": "block",
                   "reason": (
                       f"[WALKIE-TALKIE MESSAGE FROM USER]\n\n"
                       f"{message}\n\n"
                       f"[END WALKIE-TALKIE MESSAGE]\n\n"
                       f"Please acknowledge and address this message. "
                       f"Then continue with your previous task. "
                       f"Your planned tool call was not executed — "
                       f"you may re-attempt it after addressing the message."
                   ),
               }
           )
       except asyncio.QueueEmpty:
           return None  # No messages, proceed normally
   ```

4. Register the hook in the `hooks` dict (in `start()` method):
   ```python
   hooks = {
       "PreToolUse": [
           HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
           HookMatcher(hooks=[walkie_talkie_hook]),  # Fires for ALL tools
       ],
       "PreCompact": [
           HookMatcher(hooks=[workspace_pre_compact_hook])
       ],
   }
   ```
   **IMPORTANT:** The walkie_talkie_hook must be a SEPARATE HookMatcher from the bash_security_hook. The bash hook only matches "Bash" tools. The walkie-talkie hook matches ALL tools (no `matcher` param = catch-all).

5. Add waiting state detection in `_query_claude()` response streaming:
   ```python
   # In the response streaming loop, after yielding text:
   if text:
       full_response += text
       yield {"type": "text", "content": text}

       # Check for agent-initiated wait signal
       if "[WAITING]" in full_response and "[/WAITING]" in full_response:
           import re
           wait_match = re.search(r'\[WAITING\](.*?)\[/WAITING\]', full_response, re.DOTALL)
           if wait_match:
               self.walkie_talkie_waiting = True
               yield {
                   "type": "agent_waiting",
                   "question": wait_match.group(1).strip(),
               }
   ```

6. Update the system prompt in `get_workspace_system_prompt()` to include walkie-talkie instructions:
   ```
   ## Walkie-Talkie Communication

   You have a walkie-talkie communication channel with the user. While you're working:

   - **Receiving messages:** The user can send you messages at any time. If a tool call
     is blocked with a "[WALKIE-TALKIE MESSAGE FROM USER]" notification, read the message,
     acknowledge it briefly, and adjust your work if needed. Then continue with your task
     (re-attempting any tool call that was intercepted).

   - **Requesting input:** When you need user input or want to present options, output:
     [WAITING]Your question here[/WAITING]
     Then pause and wait for the user's response via the walkie-talkie channel.
     The user's response will arrive as a walkie-talkie message on your next tool call.

   - **Keep working:** Between walkie-talkie exchanges, continue working autonomously.
     Don't pause unnecessarily. The walkie-talkie is for when you genuinely need input
     or when the user wants to steer your direction.
   ```

#### `server/routers/workspace.py` (MODIFY)

**Changes:**
1. In the WebSocket handler (the `websocket_endpoint` function), add handling for the `walkie_talkie` message type:
   ```python
   elif msg_type == "walkie_talkie":
       content = data.get("content", "")
       if content and session:
           await session.queue_walkie_talkie_message(content)
           await websocket.send_json({
               "type": "walkie_talkie_queued",
               "content": content[:100],  # Truncated echo for UI confirmation
           })
   ```

2. Forward `agent_waiting` messages from the session stream to the WebSocket:
   ```python
   # In the message streaming loop:
   if chunk["type"] == "agent_waiting":
       await websocket.send_json(chunk)
   ```

3. Add a REST endpoint for checking walkie-talkie status:
   ```python
   @router.get("/workspace/sessions/{session_id}/walkie-talkie/status")
   async def get_walkie_talkie_status(session_id: str):
       session = get_session(session_id)
       if not session:
           return {"active": False}
       return {
           "active": session.walkie_talkie_enabled,
           "waiting": session.walkie_talkie_waiting,
           "queue_size": session.walkie_talkie_queue.qsize(),
       }
   ```

#### `server/schemas.py` (VERIFY - likely no changes needed)

The walkie-talkie settings fields already exist:
- `comm_check_frequency: str = "per_feature"` (line ~454)
- `comm_wait_timeout: int = 120` (line ~489)
- `comm_auto_reply: bool = True` (line ~492)

Verify these are being loaded and passed to the workspace session. If not, wire them through.

### 3.2 Frontend Files

#### `ui/src/hooks/useWorkspaceChat.ts` (MODIFY)

**Changes:**
1. Add `sendWalkieTalkie(content: string)` method:
   ```typescript
   const sendWalkieTalkie = useCallback((content: string) => {
     if (wsRef.current?.readyState === WebSocket.OPEN) {
       wsRef.current.send(JSON.stringify({
         type: "walkie_talkie",
         content,
       }))
     }
   }, [])
   ```

2. Add handler for `agent_waiting` messages from server:
   ```typescript
   // In the WebSocket onmessage handler:
   case "agent_waiting":
     onAgentWaiting?.(parsed.question)
     break
   case "walkie_talkie_queued":
     // Optional: show confirmation toast
     break
   ```

3. Add `onAgentWaiting` to the hook's options/callbacks.

4. Return `sendWalkieTalkie` from the hook.

#### `ui/src/components/workspace/WorkspaceChat.tsx` (MODIFY)

**Changes:**
1. Add a walkie-talkie input area that appears when:
   - Agent is currently streaming/working (connection active, response not done)
   - Walkie-talkie is enabled in settings
   - Display as a small input bar at the bottom of the chat, ABOVE the regular input
   - Styled differently (amber/yellow theme to match CountdownTimerBar)
   - Placeholder: "Send walkie-talkie message..."
   - Send on Enter

2. When `agent_waiting` is received:
   - Activate CountdownTimerBar with the agent's question
   - Show the question prominently
   - Focus the walkie-talkie input for immediate typing
   - When user responds OR auto-reply fires, send via `sendWalkieTalkie()`

3. Wire up CountdownTimerBar:
   - `active`: Set to true when `agent_waiting` received
   - `timeout`: From settings `comm_wait_timeout`
   - `autoReply`: From settings `comm_auto_reply`
   - `onTimeout`: Send auto-reply message via `sendWalkieTalkie("Continue with your best judgment")`
   - `onKeepGoing`: Reset timer (or send custom message)

#### `ui/src/components/workspace/CountdownTimerBar.tsx` (VERIFY/MINOR MODIFY)

This component is already built. Verify it:
- Accepts `active`, `timeout`, `autoReply`, `onTimeout`, `onKeepGoing` props
- Shows countdown, progress bar, "Keep Going" button
- Auto-fires `onTimeout` when countdown reaches zero (if autoReply enabled)

May need minor changes:
- Add display of the agent's question (from `agent_waiting` event)
- Add a text input field for custom response (not just "Keep Going")

#### `ui/src/pages/WorkspacePage.tsx` (MODIFY)

**Changes:**
1. Pass walkie-talkie state and handlers to WorkspaceChat components
2. Wire up settings values (comm_check_frequency, comm_wait_timeout, comm_auto_reply) to the chat panels
3. Ensure the walkie-talkie input works in BOTH single-panel and trifecta modes
4. For trifecta mode: each panel independently handles walkie-talkie for its own session

#### `ui/src/lib/types.ts` (MODIFY)

**Changes:**
1. Add WebSocket message types:
   ```typescript
   // In WSMessageType union:
   | "walkie_talkie_queued"
   | "agent_waiting"
   ```

2. Add interfaces:
   ```typescript
   interface AgentWaitingMessage {
     type: "agent_waiting"
     question: string
   }

   interface WalkieTalkieQueuedMessage {
     type: "walkie_talkie_queued"
     content: string
   }
   ```

### 3.3 System Prompt Updates

#### `server/services/workspace_chat_session.py` - `get_workspace_system_prompt()`

Add the walkie-talkie section (shown above in section 3.1, item 6). This goes in the existing system prompt function. Place it after the "Pause Commands" section.

---

## 4. DATA FLOW DIAGRAMS

### 4.1 User Sends Message While Agent Works

```
User types "Use PostgreSQL" in walkie-talkie input
    ↓
WorkspaceChat calls sendWalkieTalkie("Use PostgreSQL")
    ↓
WebSocket sends: {"type": "walkie_talkie", "content": "Use PostgreSQL"}
    ↓
workspace.py WebSocket handler receives it
    ↓
session.queue_walkie_talkie_message("Use PostgreSQL")
    ↓
Message added to session.walkie_talkie_queue
    ↓
Agent makes its next tool call (e.g., Read "schema.sql")
    ↓
PreToolUse hook fires → walkie_talkie_hook()
    ↓
Queue has message → hook returns "block" with message content
    ↓
Agent sees: "Tool blocked - WALKIE-TALKIE MESSAGE: Use PostgreSQL"
    ↓
Agent acknowledges, switches to PostgreSQL, re-attempts Read tool
    ↓
PreToolUse hook fires → no messages → tool proceeds normally
    ↓
Agent continues working with PostgreSQL
```

### 4.2 Agent Requests User Input

```
Agent outputs: "I found two options. [WAITING]PostgreSQL or MySQL?[/WAITING]"
    ↓
_query_claude() detects [WAITING] tag in streamed text
    ↓
Yields: {"type": "agent_waiting", "question": "PostgreSQL or MySQL?"}
    ↓
WebSocket sends agent_waiting to client
    ↓
WorkspaceChat receives onAgentWaiting("PostgreSQL or MySQL?")
    ↓
CountdownTimerBar activates with question displayed
    ↓
User types "PostgreSQL" (or auto-reply fires after timeout)
    ↓
sendWalkieTalkie("PostgreSQL")
    ↓
[Same flow as 4.1 - message queued, delivered on next tool call]
    ↓
Agent receives "PostgreSQL", continues building with PostgreSQL
```

### 4.3 Auto-Reply Flow

```
Agent outputs [WAITING] tag
    ↓
CountdownTimerBar activates (120 second countdown)
    ↓
User doesn't respond...
    ↓
Timer reaches 0
    ↓
onTimeout fires → sendWalkieTalkie("Continue with your best judgment")
    ↓
Agent receives auto-reply, proceeds with its own decision
    ↓
CountdownTimerBar deactivates
```

---

## 5. UI DESIGN SPECIFICATIONS

### 5.1 Walkie-Talkie Input Bar

**Appears when:** Agent is actively working (isLoading === true) AND walkie-talkie is enabled

**Position:** Fixed at bottom of chat panel, ABOVE the regular message input. The regular input should still be visible but slightly dimmed/disabled while agent is working.

**Styling:**
```
- Background: amber-50 (light yellow tint)
- Border: 1px solid amber-300
- Left accent: 3px amber-500 bar
- Icon: Radio/Walkie-talkie icon (from Lucide: Radio or MessageSquareMore)
- Input placeholder: "Send message to working agent..."
- Send button: amber-500 background, white text
- Height: ~40px (compact, not intrusive)
```

**Behavior:**
- Enter key sends the message
- Shift+Enter for newline
- After sending, input clears
- Brief "Sent!" confirmation (fade after 1.5s)
- Disappears when agent stops working (isLoading becomes false)

### 5.2 CountdownTimerBar Enhancement

The existing CountdownTimerBar needs these additions:
- Display the agent's question text (from `agent_waiting` event)
- Include a text input for custom response (not just "Keep Going")
- "Keep Going" button becomes "Send" button when custom text is entered
- Question text wraps if long, max 2 lines with ellipsis

### 5.3 Walkie-Talkie Status Indicator

In the chat header (WorkspaceChatHeader.tsx), add a small indicator:
- When walkie-talkie is enabled and agent is working: pulsing amber dot
- When agent is waiting for input: pulsing amber dot + "Waiting" text
- When disabled: no indicator

---

## 6. SETTINGS INTEGRATION

The settings already exist in `SettingsModal.tsx` (lines 690-762). Verify they're being read by the workspace chat. The flow should be:

```
SettingsModal → PATCH /api/settings → SQLite registry
WorkspacePage → GET /api/settings → reads comm_check_frequency, comm_wait_timeout, comm_auto_reply
WorkspacePage → passes to WorkspaceChat → passes to useWorkspaceChat hook
useWorkspaceChat → includes in WebSocket "start" message → workspace_chat_session receives them
```

If this flow isn't wired up yet, wire it up. The settings values need to reach the `WorkspaceChatSession` instance so the PreToolUse hook can respect `comm_check_frequency` and the wait mechanism can use `comm_wait_timeout`.

---

## 7. EDGE CASES AND ERROR HANDLING

### 7.1 Multiple Messages Queued
If the user sends multiple walkie-talkie messages before the agent's next tool call, they should be concatenated with a separator:
```
[WALKIE-TALKIE MESSAGE FROM USER]
Message 1: Use PostgreSQL
---
Message 2: Also add Redis for caching
[END WALKIE-TALKIE MESSAGE]
```

Or delivered one per tool call (simpler). Recommend: deliver all at once to avoid repeated tool blocking.

### 7.2 Agent Not Making Tool Calls
If the agent is in a pure text generation phase (thinking, not calling tools), the PreToolUse hook won't fire. Messages will be delivered on the next tool call. This is acceptable -- the user should see their message in the queue (UI shows "Message queued, will be delivered on next tool call").

### 7.3 Session Disconnected
If the WebSocket disconnects while messages are queued, they're lost (in-memory queue). For MVP this is acceptable. Future enhancement: persist queue to SQLite.

### 7.4 Agent Ignores Message
The agent might acknowledge but not change behavior. This is acceptable -- the hook delivers the message, the agent has autonomy in how to respond.

### 7.5 Rapid Tool Calls
If the agent is making rapid tool calls (e.g., multiple Glob searches), the hook fires on each one. With `every_tool_call` frequency, each call checks the queue. With `per_feature` frequency, only every Nth call checks. For MVP, implement `every_tool_call` only. `per_feature` can be added later.

---

## 8. TESTING PLAN

### 8.1 Manual Testing Steps

1. **Basic message delivery:**
   - Start a workspace conversation
   - Ask agent to do a multi-step task ("Read all Python files in this directory and summarize them")
   - While agent is working (calling Read tool repeatedly), send a walkie-talkie message
   - Verify: agent receives the message and acknowledges it
   - Verify: agent continues with its original task

2. **Agent-initiated wait:**
   - Ask agent: "Help me set up a database. Ask me what type I want."
   - Agent should output [WAITING] tag
   - Verify: CountdownTimerBar appears with the question
   - Type a response
   - Verify: agent receives response and continues

3. **Auto-reply:**
   - Same as #2 but don't respond
   - Verify: countdown reaches zero
   - Verify: auto-reply is sent ("Continue with your best judgment")
   - Verify: agent proceeds

4. **Trifecta mode:**
   - Enable split view
   - Start agents in two panels simultaneously
   - Send walkie-talkie to each panel independently
   - Verify: messages go to the correct panel

5. **Settings:**
   - Change comm_check_frequency to "never"
   - Verify: walkie-talkie input doesn't appear
   - Change back to "every_tool_call"
   - Verify: walkie-talkie input appears when agent works

### 8.2 Automated Testing

Add to `test_phase1_workspace.py`:
- Test that `walkie_talkie_queue` is created on session init
- Test that `queue_walkie_talkie_message()` adds to queue
- Test that the hook function returns None on empty queue
- Test that the hook function returns block result when message queued
- Test multiple messages concatenation

---

## 9. IMPLEMENTATION ORDER

Build in this exact sequence:

### Phase 1: Backend Message Queue (30 min)
1. Add `walkie_talkie_queue` and related attributes to `WorkspaceChatSession.__init__()`
2. Add `queue_walkie_talkie_message()` method
3. Add walkie-talkie PreToolUse hook function
4. Register hook in the hooks dict in `start()`
5. Test: verify hook fires and blocks tool with queued message

### Phase 2: WebSocket Wiring (20 min)
1. Add `walkie_talkie` message type handler in workspace.py WebSocket endpoint
2. Add `agent_waiting` forwarding in the response stream
3. Add the REST status endpoint (optional, for debugging)
4. Test: verify messages flow from WebSocket to queue

### Phase 3: Frontend Message Sending (30 min)
1. Add `sendWalkieTalkie()` to `useWorkspaceChat.ts`
2. Add `agent_waiting` handler to WebSocket message processing
3. Add walkie-talkie input bar to WorkspaceChat.tsx
4. Wire up CountdownTimerBar for agent waiting state
5. Test: verify UI sends messages and receives agent_waiting events

### Phase 4: System Prompt + Agent Behavior (15 min)
1. Update `get_workspace_system_prompt()` with walkie-talkie instructions
2. Add [WAITING] tag detection in `_query_claude()` response streaming
3. Test: verify agent uses [WAITING] tags and responds to walkie-talkie messages

### Phase 5: Settings Integration (15 min)
1. Verify settings flow from SettingsModal to WorkspaceChatSession
2. Wire up comm_check_frequency to the hook's behavior
3. Wire up comm_wait_timeout and comm_auto_reply to CountdownTimerBar
4. Test: verify changing settings affects behavior

### Phase 6: Polish (20 min)
1. Add walkie-talkie status indicator in chat header
2. Add "Message queued" confirmation in UI
3. Handle edge cases (multiple messages, disconnection)
4. Final end-to-end test

---

## 10. COMPATIBILITY

### Model Compatibility
The walkie-talkie system works with ANY model (Opus 4.6, Sonnet 4.6) because it operates at the SDK hook level, not the model level. The PreToolUse hook fires regardless of which model is running. The [WAITING] tag parsing is model-agnostic text matching.

### Context Mode Compatibility
Works with both 1M and 200K context modes. The hook mechanism is independent of context window size.

### Panel Compatibility
Works in single-panel mode AND trifecta mode. Each panel has its own session, its own queue, and its own hooks. In trifecta, each panel independently supports walkie-talkie.

### Backward Compatibility
When walkie-talkie is disabled (comm_check_frequency = "never"):
- No hook is registered (or hook always returns None)
- No walkie-talkie input bar shown
- No CountdownTimerBar activation
- System behaves exactly as before

---

## 11. FUTURE ENHANCEMENTS (NOT IN THIS BUILD)

These are noted for context but should NOT be implemented now:
- Persistent message queue (SQLite instead of in-memory)
- Inter-panel walkie-talkie (Panel 1 sending to Panel 2's agent)
- Message history/log for walkie-talkie exchanges
- Voice-to-text walkie-talkie input
- Automated walkie-talkie from automation rules
- Rate limiting on walkie-talkie messages (prevent spam)
