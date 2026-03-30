# HANDOFF: Walkie-Talkie Revolution — Keep Turns Alive, Chain Sessions

**Date**: 2026-03-30
**From**: Claude Opus session (workspace/chat-8, ~70% context)
**Priority**: HIGH — this is the #1 cost-reduction and capability-extension feature

---

## THE BIG IDEA (Read This First)

The owner discovered that walkie-talkie messages injected during an active Claude SDK turn are **dramatically cheaper** than regular chat messages because they don't trigger a full conversation history resend. Combined with file-based context chaining between sessions, this could extend effective agent context from 1 session to 10-20+ sessions with full continuity.

**The math:**
- Regular chat: Each message resends FULL history. 20 messages at avg 100K history = 2M input tokens
- Walkie-talkie (during active turn): Injected via PreToolUse hook. 0 additional history resend. Just ~100 tokens per injection
- Savings: 80-95% for long conversations, NOT the 40-50% originally estimated — it's even better

---

## CRITICAL DISCOVERY: [WAITING] Does NOT Keep Turns Alive

**This is the #1 thing to understand.**

When the agent outputs `[WAITING]What next?[/WAITING]`:
1. The server detects the tag and sends `agent_waiting` WebSocket event to UI
2. The UI shows the countdown timer
3. **BUT THE TURN IS OVER.** The SDK's `receive_response()` iterator has ended via `StopAsyncIteration`
4. The session is idle — no API connection, no pending calls
5. Walkie-talkie messages go into the queue but CANNOT be delivered (no tool calls happening)
6. The only way to deliver them is a NEW turn via `send_message()` — which costs full history resend

**The [WAITING] tag is purely a UI signal. It does NOT keep the SDK turn alive.**

This means the current architecture does NOT achieve the token savings the owner envisions. We need to change it.

---

## THE SOLUTION: Agent Polling Loop (Keep Turn Alive)

Instead of the agent ending its turn with `[WAITING]`, it should enter a **polling loop** that keeps the turn alive:

### How It Works

1. Agent finishes its current task
2. Agent enters a wait loop — makes periodic lightweight tool calls (e.g., `Read .autoforge/walkie-check.txt`)
3. On EACH tool call, the PreToolUse hook fires and checks the walkie-talkie queue
4. If a message is found → hook blocks the tool, injects the message → agent processes it
5. If no message → tool executes (returns small file content), agent waits ~30s, repeats
6. The turn NEVER ends until the user explicitly says "end session" or context runs out

### Token Cost of Polling

- Each poll: ~50-100 tokens (tool_use + tool_result for a tiny file read)
- At 1 poll per 30 seconds: ~200 tokens/minute, ~12K tokens/hour
- Over a 2-hour session: ~24K polling overhead
- vs. 20 regular messages with 100K avg history: ~2M tokens
- **Net savings: ~99%**

### What Needs to Change

| Change | File | Difficulty | Risk |
|--------|------|-----------|------|
| 1. System prompt: tell agent to poll instead of [WAITING] | `workspace_chat_session.py` | 2/10 | Low |
| 2. Create `.autoforge/walkie-check.txt` file for polling target | `workspace_chat_session.py` | 1/10 | None |
| 3. Remove/extend the 300s stream silence timeout (not needed with polling) | `workspace_chat_session.py` line 1792 | 1/10 | Low |
| 4. Update [WAITING] detection to handle new pattern | `workspace_chat_session.py` | 2/10 | Low |
| 5. Update UI to show "agent waiting" state from polling | `WorkspaceChat.tsx` | 2/10 | Low |

**Total difficulty: 3/10. Total risk: Low.** These are mostly system prompt changes + minor code tweaks.

### System Prompt Addition (Draft)

```
## Walkie-Talkie Communication Protocol

After completing each task or response, enter a wait loop instead of ending your turn:

1. Output your response text as normal
2. Then enter a polling loop:
   - Read the file `.autoforge/walkie-check.txt`
   - If a walkie-talkie message is injected (you'll see [WALKIE-TALKIE MESSAGE FROM USER]), process it and respond
   - If no message, wait ~30 seconds, then read the file again
   - Continue polling until the user sends "end session" or you approach context limits

IMPORTANT: Do NOT end your turn with [WAITING]. Keep the turn alive by polling.
The user will communicate exclusively via walkie-talkie (the amber panel on the right).
Your responses appear in the main chat — that's fine. The cost savings come from
keeping the turn alive so the full conversation history is not resent.

When approaching context limits (you'll know from the system's context warnings),
write a handoff summary to `.autoforge/handoff/session-latest.md` before ending.
```

### Implementation Notes

- The polling Read call should target a tiny file (< 100 bytes) to minimize token cost
- The 30-second interval is a suggestion to the agent, not enforced by code
- The agent can break the loop for legitimate reasons (context limit, explicit "end" command)
- The PreToolUse hook already works for this — no changes needed to the hook itself

---

## TASK 2: File-Based Context Chaining Between Sessions

### What It Is

When a session approaches its context limit, the agent writes a handoff file. The next session reads it on startup, gaining full context of everything that happened before. Chain 10-20 sessions together for continuous multi-session work.

### What Already Exists (DunkStack Has This!)

DunkStack already has a complete bridge/handoff system:
- `POST /api/dunkstack/bridge/save` — saves structured state to `.agent/bridge.md`
- Agent startup protocol reads `.agent/bridge.md` and incorporates context
- Auto-bridge at safety threshold (~47.5% context) — automatically saves state
- Files: `.agent/bridge.md`, `.agent/working_memory.md`, `.agent/build_log.md`

**Key files:**
- `server/routers/dunkstack.py` lines 405-451 (bridge save endpoint)
- `server/services/dunkstack_session.py` lines 72-82 (startup protocol)
- `server/routers/dunkstack.py` lines 753-803 (auto-bridge on threshold)

### What Needs to Be Built for Workspace

Port the DunkStack bridge system to the Workspace page:

| Change | Difficulty | Details |
|--------|-----------|---------|
| 1. Add bridge save endpoint for workspace | 3/10 | Port from DunkStack: `POST /api/workspace/bridge/save` |
| 2. Add bridge read endpoint | 2/10 | `GET /api/workspace/bridge` |
| 3. System prompt: read bridge file on startup | 2/10 | Add to `get_workspace_system_prompt()` |
| 4. Auto-bridge at context threshold | 3/10 | Port DunkStack's 3-tier safety system |
| 5. UI: "Save Bridge State" button | 2/10 | Already exists in DunkStack, port to Workspace |
| 6. System prompt: write handoff before ending | 2/10 | Instructions for agent to write summary |

**Total difficulty: 4/10.** Most of this is porting existing DunkStack code.

### Handoff File Format (Recommended)

```markdown
# Session Handoff — {timestamp}

## Session Summary
{2-3 paragraph summary of what was discussed and accomplished}

## Decisions Made
- {key decision 1}
- {key decision 2}

## Current State
{what's working, what's broken, what's in progress}

## Next Steps
1. {next priority}
2. {next priority}

## Open Questions
- {anything unresolved}

## Files Changed This Session
- {file path}: {what changed}

## Raw Conversation Log
{full conversation text — gives the next agent complete context}
```

### Token Budget for Handoff

- Summary sections: ~2-5K tokens
- Raw conversation log: ~20-50K tokens (depending on session length)
- Total: ~25-55K per session handoff
- With 1M context: 15-40 session chains possible
- With compressed summaries only (no raw log): 40-200 session chains

---

## TASK 3: Wire Up Walkie-Talkie Settings Dashboard

### Current State

The settings UI exists and saves to the database correctly:
- Check Frequency: per_feature / every_tool_call / never
- Wait Timeout: 30s / 1m / 2m / 5m
- Auto-reply on timeout: toggle

**BUT the backend doesn't read these settings.** `walkie_talkie_enabled` is hardcoded to `True` in `workspace_chat_session.py` line 375. The settings are UI-only.

### What Needs to Change

| Setting | Current State | Needed Change |
|---------|--------------|---------------|
| `comm_check_frequency` | Only hides UI bar when "never" | Backend should set `walkie_talkie_enabled = False` when "never" |
| `comm_wait_timeout` | Only controls UI countdown timer | With polling approach, this controls poll frequency hint |
| `comm_auto_reply` | Only controls UI auto-reply | With polling approach, this becomes less relevant (agent is always polling) |

### Implementation

In `workspace_chat_session.py`, at session creation:
```python
# Read walkie-talkie settings from the global settings store
from registry import get_setting
freq = get_setting("comm_check_frequency", "every_tool_call")
self.walkie_talkie_enabled = (freq != "never")
```

With the polling approach, "per_feature" vs "every_tool_call" distinction doesn't apply to workspace (no features concept). Recommend simplifying to just "On" / "Off" for workspace, or repurposing:
- "every_tool_call" = Agent polls continuously (most responsive, slightly more token cost)
- "per_feature" = Agent polls every 60 seconds (less responsive, lower cost)
- "never" = Agent doesn't poll, behaves like current system

---

## TASK 4: Auto-Start Turn from Walkie-Talkie (Fallback)

If the polling approach fails or the turn ends unexpectedly, we need a fallback: when a walkie-talkie message arrives and no turn is active, automatically start a new turn.

### Implementation

In `server/routers/workspace.py`, the walkie-talkie handler (lines 1251-1263):

```python
elif msg_type == "walkie_talkie":
    content = message.get("content", "")
    if not session:
        await websocket.send_json({"type": "error", "content": "No active session."})
    elif content:
        await session.queue_walkie_talkie_message(content)
        await websocket.send_json({"type": "walkie_talkie_queued", "content": content[:100]})

        # NEW: If no turn is active, auto-start one with the walkie-talkie content
        if not response_task or response_task.done():
            response_task = asyncio.create_task(
                _stream_to_ws(
                    session.send_message(
                        f"[Walkie-talkie message from user]: {content}",
                    )
                )
            )
```

**Difficulty: 2/10. Risk: Low.** This is a simple check + task creation.

This ensures that even if the polling loop fails, walkie-talkie messages still trigger agent responses. The cost is higher (full history resend) but the UX is seamless.

---

## TASK 5: Fix Existing Bugs (Already Committed, Needs Deploy)

### Bug Fixes Already on Main (commit 0e18aa0)

1. **Walkie-talkie messages lost during sub-agent execution** — Added `_pending_walkie_deliveries` safety net that re-delivers unacknowledged messages at the start of the next turn. File: `workspace_chat_session.py`

### Bug Fixes Already on Main (commit 0147910, merged as 1f7bf9e)

1. **Model badge flipping 1M→200K** — Added `knownContextMode` state cache in `WorkspaceChat.tsx`
2. **Messages stuck until user sends another** — Wrapped ~15 sync DB calls in `asyncio.to_thread()` in `workspace_chat_session.py`
3. **Context bar showing 1.9M/1.0M** — Capped `currentContext` at context window size in `WorkspaceChat.tsx` and `TokenLogPanel.tsx`

**These need to be deployed:** Pull on live install, restart `start_ui.bat`, Ctrl+Shift+R.

---

## PRIORITY ORDER

| # | Task | Difficulty | Impact | Dependencies |
|---|------|-----------|--------|--------------|
| 1 | Deploy existing bug fixes | 0/10 | High | None (already on main) |
| 2 | Agent polling loop (keep turns alive) | 3/10 | MASSIVE | None |
| 3 | Auto-start turn from walkie-talkie (fallback) | 2/10 | High | None |
| 4 | Wire up walkie-talkie settings | 2/10 | Medium | None |
| 5 | Port bridge/handoff system from DunkStack | 4/10 | MASSIVE | None |
| 6 | Auto-bridge at context threshold | 3/10 | High | Task 5 |

**Recommended approach: Do tasks 2+3 together first.** They give 90% of the benefit. Task 5 is the next big win.

---

## KEY FILES TO READ

Before making ANY changes, read these files completely:

| File | Why |
|------|-----|
| `server/services/workspace_chat_session.py` | The entire session lifecycle — query, hooks, response streaming |
| `server/routers/workspace.py` lines 1050-1300 | WebSocket handler — message routing, walkie-talkie, session management |
| `ui/src/components/workspace/WorkspaceChat.tsx` lines 240-340, 850-910 | Settings state, walkie-talkie handlers, countdown |
| `ui/src/hooks/useWorkspaceChat.ts` lines 440-470, 670-690 | WebSocket event handlers, sendWalkieTalkie |
| `ui/src/components/workspace/CountdownTimerBar.tsx` | Full file — understand the timer |
| `server/services/dunkstack_session.py` lines 72-82 | Bridge startup protocol (to port) |
| `server/routers/dunkstack.py` lines 405-451, 738-803 | Bridge save + auto-bridge (to port) |

---

## WHAT NOT TO TOUCH

- Do NOT modify the WebSocket connection architecture (one socket per page)
- Do NOT modify `useWorkspaceChat.ts` WebSocket connection logic
- Do NOT change how `send_message()` loads conversation history from DB
- Do NOT remove the `_pending_walkie_deliveries` safety net (it's needed as fallback)
- Do NOT modify the PreToolUse hook mechanism (it works correctly)

---

## TESTING PLAN

1. Start a workspace chat with Claude Opus 1M
2. Send one API message: "Enter walkie-talkie polling mode"
3. Agent should start polling (making periodic Read calls)
4. Send a walkie-talkie message via the amber panel
5. Agent should receive it (via hook injection) and respond
6. Send several more walkie-talkies — all should be received
7. Verify token log shows minimal overhead per poll cycle
8. Let it idle for 5+ minutes — verify the turn stays alive
9. Send "end session" via walkie-talkie — agent should write handoff and end

---

## OWNER CONTEXT

- The owner is NOT a coder. Explain changes in plain language.
- This is the #1 priority feature — it's the foundation for the owner's SaaS product
- The owner wants to use this for cold email automation systems (see cold email playbook)
- The DunkStack page was the testing facility; Workspace is the production target
- The owner has been trying to get this working for a month
- The walkie-talkie UI already exists and mostly works — this is about making the BACKEND deliver on the vision
