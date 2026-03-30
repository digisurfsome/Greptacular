# AGENT TASK: Fix Workspace Walkie-Talkie System

**READ THESE FILES FIRST (in order):**
1. `.claude/handoffs/walkie-talkie-revolution-handoff.md` — full technical details
2. This file — your task list

**IMPORTANT RULES:**
- Test after EACH fix. Don't batch everything then discover it's broken.
- Do NOT modify the WebSocket connection architecture (one socket per page)
- Do NOT break the existing chat functionality
- ALL Claude models use subscription auth (force_sub = True). NEVER use API keys.
- Read `CLAUDE.md` in the project root for full project rules

---

## TASK LIST (Do in this order)

### Task 1: Agent Polling Loop (HIGHEST PRIORITY)
**Goal**: Keep the SDK turn alive so walkie-talkie messages arrive instantly, not 20 minutes late.

**What to do:**
1. In `server/services/workspace_chat_session.py`, update the system prompt (function `get_workspace_system_prompt()`) to tell the agent:
   - After completing each task/response, enter a polling loop
   - Read `.autoforge/walkie-check.txt` every ~30 seconds
   - The PreToolUse hook will inject walkie-talkie messages when they arrive
   - Continue polling until user says "end session" or context limit approaches
2. Create a tiny file `.autoforge/walkie-check.txt` containing just "ok" — this is the polling target
3. The 300-second stream silence timeout at line ~1792 of `workspace_chat_session.py` does NOT need changing — polling tool calls reset this timer automatically

**How to verify:** Start a chat, send one message, then send a walkie-talkie. The agent should receive it within ~30 seconds (when its next poll triggers the hook).

### Task 2: Main Chat Input Switches to Walkie-Talkie After First Message
**Goal**: User types in the same main chat input for every message. First message = API call. All subsequent = walkie-talkie injection. User doesn't notice any difference.

**What to do:**
1. In `ui/src/components/workspace/WorkspaceChat.tsx`, track whether the first message has been sent (e.g., `const [firstMessageSent, setFirstMessageSent] = useState(false)`)
2. In the send handler, if `firstMessageSent` is true AND the agent is currently in a turn (isLoading), route the message through `sendWalkieTalkie()` instead of the normal `send_message` WebSocket path
3. The message should still appear in the main chat UI (add it as a user message bubble)
4. Set `firstMessageSent = true` after the first message
5. Reset `firstMessageSent = false` when starting a new conversation

**How to verify:** Send message #1 (appears in chat, agent responds). Send message #2 (appears in chat, but token log shows no new API turn — it was injected via walkie-talkie).

### Task 3: Auto-Start Turn from Walkie-Talkie (Fallback)
**Goal**: If the polling loop fails or the turn ends, walkie-talkie messages should automatically start a new turn.

**What to do:**
1. In `server/routers/workspace.py`, in the walkie-talkie handler (~line 1251), after queuing the message, check if no response_task is active (or it's done)
2. If no active turn, automatically start one: `response_task = asyncio.create_task(_stream_to_ws(session.send_message(content)))`
3. This ensures messages always get through, even if polling stopped

**How to verify:** Let the agent's turn end completely. Send a walkie-talkie. Agent should automatically respond.

### Task 4: "End Session" Button
**Goal**: User clicks a button to stop the polling loop and end the session gracefully.

**What to do:**
1. Add an "End Session" button in the chat header or near the send button (only visible when agent is in polling mode)
2. When clicked, send a walkie-talkie message: "End session. Write your handoff summary to .autoforge/handoffs/session-{conversation_id}.md including: summary of what was discussed, decisions made, current state, and next steps. Then stop."
3. The agent writes the handoff file and stops polling

### Task 5: Wire Up Walkie-Talkie Settings
**Goal**: The settings dashboard (Check Frequency, Wait Timeout, Auto-reply) should actually work on the backend.

**What to do:**
1. In `workspace_chat_session.py` `__init__()`, read `comm_check_frequency` from settings
2. Set `self.walkie_talkie_enabled = (freq != "never")`
3. The wait timeout and auto-reply are already UI-only and work fine for now

### Task 6: Context Handoff / Session Chaining
**Goal**: When context gets high, auto-save a handoff file. New chats can include past chat context.

**What to do:**
1. Port the bridge save system from DunkStack (`server/routers/dunkstack.py` lines 405-451) to workspace
2. Add a `POST /api/workspace/bridge/save` endpoint
3. Add handoff file writing to the system prompt (agent writes summary before ending)
4. In the "New Chat" form (`WorkspaceChat.tsx`), add a multi-select dropdown listing previous conversations
5. Selected conversations' handoff files get loaded into the new session's system prompt
6. Store handoff files at `.autoforge/handoffs/session-{id}.md`

### Task 7: Fix Existing Bugs (Already committed but double-check)
- Model badge flipping 1M→200K (knownContextMode cache in WorkspaceChat.tsx)
- Messages stuck until user sends another (asyncio.to_thread wrapping in workspace_chat_session.py)
- Context bar showing wrong numbers (cap at context window size)
- Walkie-talkie messages lost during sub-agents (_pending_walkie_deliveries safety net)

---

## TESTING CHECKLIST

After all changes:
1. [ ] Start a new chat, send one message — agent responds normally
2. [ ] Send second message — goes via walkie-talkie (check token log: no new API turn)
3. [ ] Agent should poll and receive walkie-talkie within 30 seconds
4. [ ] Let agent idle 5+ minutes — turn stays alive
5. [ ] Click "End Session" — agent writes handoff and stops
6. [ ] Start NEW chat, select previous chat in dropdown — agent has previous context
7. [ ] Set walkie-talkie to "Never" in settings — polling stops
8. [ ] Model badge shows correct model throughout
9. [ ] Context bar shows reasonable numbers
10. [ ] `cd ui && npm run build` succeeds
11. [ ] `cd ui && npm run lint` passes
