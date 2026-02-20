# Handoff: Workspace Model Selection, Cost Display & Opus Hang Fixes

## Context

The workspace chat feature has three interconnected bugs discovered through real usage testing with the Anthropic API console as ground truth.

**Branch:** `claude/fix-workspace-features-X9VMA`

---

## Bug 1: Model Pill Buttons Allow Mid-Chat Switching (Confusing UX)

### Problem
The pill buttons (Opus 4.6 · 1M / Opus 4.6 · 200K / Sonnet 4.6 · 1M) in the top-right of WorkspaceChat are clickable mid-conversation but changes are **deferred** to the next conversation. This caused the user to think they switched to Sonnet, but the current session kept running Opus. The Anthropic API console confirmed only Opus was ever called.

### What Needs to Change
1. **The pill buttons in WorkspaceChat should NOT be clickable during an active session.** Once a chat starts, the model is locked. The pills become read-only identification badges showing what model this chat is using.
2. **The model choice happens at chat creation time only.** The sidebar's "New Chat" naming form already has a pill model selector (added this session). That's where the user picks the model — alongside naming the chat and picking the repo.
3. **Remove the "Next conversation: X" toast/on-deck indicator.** It's confusing. The model is chosen when you create the chat, period.

### Key Files & Lines
- **`ui/src/components/workspace/WorkspaceChat.tsx`**
  - Lines 171-176: `MODEL_PRESETS` array definition
  - Lines 700-713: Pill button `onClick` handler — this needs to be disabled when a session is active (`conversationId !== null`)
  - Lines 734-766: On-deck indicator — remove this entirely
  - Lines 284-289: Where `start()` is called with model — should read from the conversation's stored model, not from a ref

- **`ui/src/components/workspace/WorkspaceSidebar.tsx`**
  - Lines 57-61: `SIDEBAR_MODEL_PRESETS` — this is the correct place for model selection
  - Lines 349-377: Pill selector in the naming form — already implemented, works correctly

- **`ui/src/pages/WorkspacePage.tsx`**
  - Lines 120-132: `modelPresetIndex` state and `handleModelPresetChange` — this wiring is correct for the sidebar, but WorkspaceChat should read the model from the conversation record, not from shared page state

### Suggested Approach
- Store the selected model in the conversation record (backend: add `model` column to `WorkspaceConversation` table, pass it in the `POST /workspace/conversations` create call)
- When WorkspaceChat loads a conversation, read the model from the conversation record
- Make the pill buttons in WorkspaceChat purely visual (no onClick) when `conversationId` is set
- Keep the sidebar pill selector as the only place to choose model for new chats

---

## Bug 2: Two Different Cost Formulas Showing Different Numbers

### Problem
The UI shows two different dollar amounts for the same chat:
- **Top bar** (EnhancedContextBudgetBar): Shows e.g. "$2.12" with breakdown "in: $0.85 + out: ~$1.27"
- **Cost zone** (UsageDashboard): Shows e.g. "API equiv: $2.55"
- **Real Anthropic console**: $3.69 total for two chats

Neither matches reality. They use completely different formulas.

### Top Bar Formula (EnhancedContextBudgetBar.tsx)
**File:** `ui/src/components/workspace/EnhancedContextBudgetBar.tsx`

```
Input rates:  Opus $5/MTok standard, $10/MTok extended (>200K)
              Sonnet $3/MTok standard, $6/MTok extended
Output rates: Opus $25/MTok standard, $37.50/MTok extended
              Sonnet $15/MTok standard, $22.50/MTok extended
Output guess: 30% of input tokens (HEURISTIC — not measured)
```

- Lines 70-79: Rate constants (these are correct for Opus 4.6 / Sonnet 4.5)
- Lines 106-115: `estimateTotalCost()` — uses 30% output heuristic
- Lines 82-89: `estimateInputCost()`
- Lines 92-103: `estimateOutputCost()` — fabricates output tokens as `input * 0.3`
- **IS model-aware** (accepts `preferredModel` prop)
- **Bug:** Uses all-or-nothing pricing (if >200K, ALL tokens at extended rate). Real billing uses split-tier (first 200K standard, overage at extended).
- **Bug:** 30% output heuristic is too low. Real conversations often have 50-100%+ output ratio, causing this to consistently underestimate.

### Cost Zone Formula (workspace_database.py backend)
**File:** `server/services/workspace_database.py`

```
Input rate:  $15/MTok standard (STALE — this is Opus 4.1 pricing, not 4.6)
             $22.50/MTok premium (1.5x multiplier)
Output:      NOT INCLUDED AT ALL
```

- Lines 1472-1527: `get_conversation_cost_zones()` full function
- Line 1495: `STANDARD_INPUT_RATE = 15.0` — **WRONG, should be $5 for Opus 4.6**
- **NOT model-aware** — hardcodes one rate regardless of selected model
- **Bug:** Stale Opus 4.1 rate ($15 instead of $5)
- **Bug:** Ignores output tokens entirely
- **Accidentally close to real cost** because 3x-too-high input rate roughly compensates for missing output

### Display Location
**File:** `ui/src/components/workspace/UsageDashboard.tsx`
- Lines 315-325: Shows "API equiv: $X.XX" from the backend cost zone data
- Line 280: Tooltip says `@ $15/MTok` — **wrong rate displayed to user**
- Line 291: Tooltip says `@ $22.50/MTok (1.5x)` — also wrong

### What Needs to Change
1. **Update backend rates** in `workspace_database.py` line 1495: Change `15.0` to `5.0` (Opus 4.6 rate)
2. **Make backend model-aware**: Accept the conversation's model and use appropriate rate table:
   - Opus 4.6: $5/MTok input standard, $10/MTok extended, $25/MTok output standard, $37.50/MTok extended
   - Sonnet 4.5: $3/MTok input standard, $6/MTok extended, $15/MTok output standard, $22.50/MTok extended
3. **Add output token tracking**: Store actual output tokens per assistant message (not a heuristic). The backend already stores `token_estimate` per message — add `output_token_estimate` field or calculate from actual assistant message content.
4. **Fix top bar extended pricing**: Change from all-or-nothing to split-tier (first 200K at standard rate, overage at extended rate)
5. **Unify or clearly differentiate**: Either show one cost number everywhere, or clearly label what each one measures
6. **Fix tooltips** in UsageDashboard.tsx lines 280 and 291

---

## Bug 3: Opus 4.6 · 1M Hangs Indefinitely (Timeout Fix Not Working)

### Problem
Selecting "Opus 4.6 · 1M" and sending a message results in infinite "Thinking..." with no response. The user waited 30+ minutes. The timeout fix from the previous commit (`asyncio.wait_for`) did NOT resolve this — the SDK subprocess is likely blocking at a level that Python's asyncio cannot interrupt.

### What Was Already Tried (didn't work)
**File:** `server/services/workspace_chat_session.py` lines 706-770
- Wrapped `client.query()` with `asyncio.wait_for(timeout=180)` for Opus
- Added first-token timeout of 300s on `receive_response()` iterator
- Added `{"type": "status"}` message for "Waiting for Opus..."
- Added `WorkspaceChatStatusMessage` type in `ui/src/lib/types.ts`
- Added `case "status"` handler in `ui/src/hooks/useWorkspaceChat.ts`

**Why it didn't work:** The Claude Agent SDK's `client.query()` and `client.receive_response()` likely use subprocess pipes or blocking I/O that `asyncio.wait_for` cannot cancel. The coroutine is awaitable but the underlying operation is not truly async-cancellable.

### What Needs Investigation
1. **Check how the Claude Agent SDK implements `query()` and `receive_response()`** — is it truly async or wrapping blocking subprocess I/O? If it's `asyncio.to_thread()` or subprocess pipes, `wait_for` timeout will fire but the underlying operation continues.
2. **Check if `context-1m-2025-08-07` beta is actually available for Opus 4.6** — there are known issues where the 1M beta works for Sonnet but not Opus on some accounts. The beta flag is set at line 485-489 of `workspace_chat_session.py`.
3. **Check server logs** — the `logger.info(f"Resolved model: {self.model} -> {model}")` at line 395 should show whether the client even initializes.
4. **Consider process-level timeout** — instead of async timeout, spawn the SDK call in a subprocess or thread with a hard kill after N seconds. Or use `asyncio.create_task()` with `task.cancel()` and handle `CancelledError`.
5. **Consider a health-check ping** — after calling `client.query()`, send periodic WebSocket messages ("Still waiting...") from a background task, and kill the SDK process if no response after the timeout.

### Key Files
- `server/services/workspace_chat_session.py` lines 706-770: Current timeout code
- `server/services/workspace_chat_session.py` lines 457-499: SDK client creation with beta flag
- `server/services/workspace_chat_session.py` lines 385-395: MODEL_MAP resolution
- `server/routers/workspace.py` lines 1007-1009: WebSocket streaming loop

---

## Architecture Reference

### Model Selection Flow (Current — Broken)
```
User clicks pill → sets pendingPresetRef (deferred) → next start() reads ref →
WebSocket sends {type:"start", model:"opus"|"sonnet"} →
Backend MODEL_MAP resolves to full model ID → SDK client created with model
```

### Model Selection Flow (Desired)
```
User creates new chat → picks model in naming form → model stored on conversation →
WorkspaceChat reads model from conversation → pills are read-only badges →
WebSocket sends {type:"start", model:"opus"|"sonnet"} → same backend flow
```

### Cost Calculation Flow
```
Frontend EnhancedContextBudgetBar:
  totalTokens (from WebSocket token_usage) → INPUT_RATES[model] + OUTPUT_RATES[model] * 0.3 → top bar $

Backend get_conversation_cost_zones:
  SUM(token_estimate) from WorkspaceMessage → hardcoded $15/MTok → "API equiv" $
```

### Files Modified This Session
- `ui/src/components/workspace/WorkspaceChat.tsx` — on-deck indicator added
- `ui/src/components/workspace/WorkspaceSidebar.tsx` — model picker in naming form added
- `ui/src/pages/WorkspacePage.tsx` — model preset state management added
- `ui/src/hooks/useWorkspaceChat.ts` — "status" message handler added
- `ui/src/lib/types.ts` — WorkspaceChatStatusMessage type added
- `server/services/workspace_chat_session.py` — asyncio timeout + status message added (NOT WORKING for the hang)
