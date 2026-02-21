# HANDOFF: Finish Swarm + Walkie-Talkie Polish (Last 10%)

**Status:** Both systems are 90-100% built and wired. This is polish work, not architecture.

**Estimated effort:** ~1 hour total for a Sonnet 4.6 1M agent.

**Branch:** Work on whatever branch is current. All prior work is on `claude/setup-agents-implementation-UNSOn`.

---

## TASK 1: CountdownTimerBar — Show Agent's Question (20 min)

**File:** `ui/src/components/workspace/CountdownTimerBar.tsx` (130 lines)

**Problem:** When the agent enters `[WAITING]` state and asks a question (e.g., "Should I use REST or GraphQL?"), the CountdownTimerBar shows a generic "Agent waiting for response..." message instead of the actual question.

**Fix:**

1. Add a `question` prop to CountdownTimerBar:
   ```typescript
   interface CountdownTimerBarProps {
     active: boolean
     totalSeconds: number
     autoReply: boolean
     question?: string  // ADD THIS
     onKeepGoing: () => void
     onTimeout: () => void
   }
   ```

2. Display the question when present:
   - Replace "Agent waiting for response..." with the actual question text
   - Truncate long questions with ellipsis (max ~100 chars)
   - Keep the generic message as fallback when `question` is undefined

3. **Wire it up in WorkspacePage.tsx:**
   - The `agent_waiting` WebSocket event already carries `question` field
   - Find where `timerActive` is set to `true` (should be near `agent_waiting` handler)
   - Store the question in state: `const [agentQuestion, setAgentQuestion] = useState<string>("")`
   - Pass it: `<CountdownTimerBar question={agentQuestion} ... />`

4. Add a text input inside the timer bar for custom responses:
   - Small input field next to "Keep Going" button
   - When user types and presses Enter, send as walkie-talkie message AND dismiss timer
   - This lets users answer the agent's question directly from the timer bar

**Test:** Start a workspace session, ask the agent to do something that requires a decision. Verify the question appears in the timer bar and you can respond from it.

---

## TASK 2: Verify `comm_check_frequency` Settings Wire-Up (15 min)

**File:** `server/services/workspace_chat_session.py` (~line 1100-1150)

**Problem:** The `comm_check_frequency` setting has 3 options (`per_feature`, `every_tool_call`, `never`) but may not be fully wired into the PreToolUse hook.

**What to check:**

1. Find the PreToolUse hook function (search for `pre_tool_use` or `PreToolUse`)
2. Verify it reads `comm_check_frequency` from settings
3. Confirm behavior for each value:
   - `every_tool_call` — hook checks walkie-talkie queue on EVERY tool call (default)
   - `per_feature` — hook only checks at feature boundaries (may need a flag tracking feature state)
   - `never` — hook is a no-op, walkie-talkie messages are never delivered mid-session

4. If `per_feature` isn't implemented (likely — it's the hardest one), either:
   - Implement it by tracking a `feature_boundary` flag that gets set when agent calls feature MCP tools
   - OR simplify to just `every_tool_call` and `never`, removing `per_feature` from the settings dropdown

**Files to check:**
- `server/services/workspace_chat_session.py` — the hook implementation
- `ui/src/components/SettingsModal.tsx` — the dropdown options
- `server/schemas.py` — the settings model

---

## TASK 3: "Sent!" Confirmation Feedback (10 min)

**File:** `ui/src/components/workspace/WorkspaceChat.tsx`

**Problem:** When user sends a walkie-talkie message, the input clears but there's no visual confirmation.

**Fix:**

1. After `sendWalkieTalkie()` succeeds, show a brief "Sent!" badge next to the input
2. Implementation:
   ```typescript
   const [showSent, setShowSent] = useState(false)

   const handleSend = async () => {
     await sendWalkieTalkie(message)
     setMessage("")
     setShowSent(true)
     setTimeout(() => setShowSent(false), 1500)
   }
   ```
3. Style: Small green "Sent!" text or checkmark that fades out after 1.5s
4. Check if this is already partially implemented — search for "Sent" or "sent" in WorkspaceChat.tsx

---

## TASK 4: Verify Swarm Walkie-Talkie Delivery (15 min)

**Files:**
- `server/services/swarm_orchestrator.py` (~694 lines)
- `server/routers/swarm.py` (~299 lines)

**Problem:** The swarm has a walkie-talkie inject endpoint (`POST /api/swarm/{swarm_id}/inject`) and the SwarmPanel UI has per-stage message input, but it's unclear if messages actually reach the underlying `WorkspaceChatSession` agents.

**What to verify:**

1. In `swarm_orchestrator.py`, find where each stage creates its agent session
2. Confirm each stage's session has `walkie_talkie_enabled = True`
3. Trace the inject endpoint: does it call `queue_walkie_talkie_message()` on the correct stage's session?
4. If the wiring is broken, fix it:
   - The SwarmPipeline needs a mapping: `stage_name → WorkspaceChatSession`
   - The inject endpoint needs to look up the right session and queue the message

**Test:** If possible, start a simple swarm, use the inject endpoint to send a message to stage 1, and check server logs for delivery.

---

## TASK 5: Header Status Indicator Polish (10 min)

**File:** `ui/src/components/workspace/WorkspaceChat.tsx` or `ui/src/pages/WorkspacePage.tsx`

**Problem:** The header should show:
- Pulsing amber dot + "Live" when agent is actively working
- Pulsing amber dot + "Waiting" when agent is in `[WAITING]` state
- No dot when agent is idle/stopped

**What to check:**
1. Search for the header status indicator (look for "Live", "Waiting", "pulsing", "amber dot")
2. Verify it reacts to `agent_waiting` WebSocket events
3. Verify it reacts to agent running/stopped state changes
4. If not wired, add state transitions:
   - Agent starts → "Live"
   - `agent_waiting` event → "Waiting"
   - Agent stops → remove indicator

---

## NEXT BIG FEATURE: Automated Holding Patterns

After finishing the 5 tasks above, the next major feature is documented in:

**`docs/PRD_AUTOMATED_HOLDING_PATTERNS.md`** (549 lines, comprehensive)

This is the session persistence system that keeps agents alive between tasks at near-zero cost. It builds directly on the walkie-talkie system (auto-reply chaining) and the [WAITING] mechanism. The PRD has full implementation details, phased build order, and cost analysis.

**TL;DR of the holding pattern:** Agent finishes task → enters [WAITING] loop → auto-reply chains keep it alive → user sends walkie-talkie message → agent resumes with full context intact → saves ~$0.90 per resume vs cold start.

---

## FILES REFERENCE (Quick Navigation)

| Area | File | Lines |
|------|------|-------|
| Walkie-talkie backend | `server/services/workspace_chat_session.py` | ~1215 |
| Workspace router | `server/routers/workspace.py` | check |
| Swarm orchestrator | `server/services/swarm_orchestrator.py` | ~694 |
| Swarm router | `server/routers/swarm.py` | ~299 |
| CountdownTimerBar | `ui/src/components/workspace/CountdownTimerBar.tsx` | ~130 |
| WorkspaceChat | `ui/src/components/workspace/WorkspaceChat.tsx` | check |
| SwarmPanel | `ui/src/components/workspace/SwarmPanel.tsx` | ~434 |
| WorkspacePage | `ui/src/pages/WorkspacePage.tsx` | check |
| Settings modal | `ui/src/components/SettingsModal.tsx` | check |
| Settings schema | `server/schemas.py` | check |
| WS hook | `ui/src/hooks/useWorkspaceChat.ts` | check |
| API client | `ui/src/lib/api.ts` | check |
| Types | `ui/src/lib/types.ts` | check |
| Walkie-talkie PRD | `docs/PRD_WALKIE_TALKIE_SYSTEM.md` | ~663 |
| Holding patterns PRD | `docs/PRD_AUTOMATED_HOLDING_PATTERNS.md` | ~549 |
| Walkie-talkie tests | `docs/walkie-talkie-testing.md` | ~237 |
