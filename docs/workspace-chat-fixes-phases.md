# Workspace Chat Fixes — Phase Plan

These fixes correspond to numbered items on the user's annotated screenshots.
**IMAGE REFERENCE**: Each number (e.g., #14, #18) refers to a red-numbered annotation
on the screenshots the user took of the workspace chat UI. Include those screenshots
when passing work to the next agent.

## Phase 1 — COMPLETED (this session)

| Image # | Fix | Status |
|---------|-----|--------|
| B1/B2 | WebSocket zombie reconnect race condition — connection generation counter in `useWorkspaceChat.ts` | DONE |
| #16 | Text area stays tall after sending — reset `style.height` in `handleSend` | DONE |
| #17 | Send button always spinning — now shows red Stop button when loading, calls `POST /sessions/{id}/cancel` | DONE |
| #10 | Context bar showing 748K/200K (cumulative) — now uses `apiTokenTotals.currentContext` (latest API turn) | DONE |
| C1-C3 | Context warnings at 40/45/50/55/60% — injected as system messages in chat | DONE |
| C5 | Activity spinner — pulsing dot + elapsed timer replaces "Thinking..." | DONE |

## Phase 2 — Token Log & Cost Display Fixes

These are all in `ui/src/components/workspace/TokenLogPanel.tsx` and `WorkspaceChat.tsx`.

| Image # | What | Fix |
|---------|------|-----|
| #1 | Token Log header shows cumulative input/output that's confusing | Show TWO rows: "This Turn" (latest API response) and "Session Total" (sum). The data is already in the `tokenLog` entries — `result_summary` events have `api_input_tokens` and `api_output_tokens`. Latest turn = last `result_summary`. Session total = sum of all `result_summary` entries. |
| #4 | "56.7K tok" is unlabeled | Label it clearly: "Total Output: 56.7K" or "Session: 56.7K total". The value comes from summing `api_input_tokens + api_output_tokens` across all turns. |
| #5 | Cache/Context numbers misleading (748K cumulative) | Replace with: "Current Context: 142K/200K (71%)" + "Cache Hit Rate: 89%". Current context = latest `result_summary`'s `api_input_tokens + api_cache_read_tokens + api_cache_creation_tokens`. Cache rate = `latestCacheRead / (latestInput + latestCacheRead)`. |
| #6 | Cost display only shows API equivalent | Show API cost + subscription estimate. Subscription est = `(apiCost / apiEquivalentRate) * subscriptionDailyRate`. For now, just show both: "API Equivalent: $17.25" + "Subscription users pay flat monthly rate". |
| #7 | No mini context gauge near Summary/Clear buttons | Add a small inline percentage bar: `[Summary] [Clear] [Context: ███░░ 42%]`. Use the same `apiTokenTotals.currentContext / contextBudget` calculation from the main context bar. |
| #8 | Log entries show "~15t" (estimated tokens) | Use actual `api_input_tokens`/`api_output_tokens` from the `result_summary` events instead of character-based estimates. The SDK returns exact counts with every API response. |
| #9 | Per-entry cost shows same running total for multiple entries | Show incremental cost per action: "This action: $0.12 | Running: $11.97". Incremental = current `result_summary`'s `api_total_cost_usd`. |
| #11 | Daily stats show "7651%" | Fix the percentage denominator. It's probably dividing total tokens by some wrong value. Remove the percentage unless it represents daily quota usage. Show: "Today: 17.9K tokens across N conversations | ~$0.09" |

**Key principle**: The Anthropic API returns `usage` data with EVERY response:
```json
{
  "usage": {
    "input_tokens": 2095,
    "output_tokens": 503,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 1500
  }
}
```
The backend already captures this in `result_summary` token log entries. Don't calculate or estimate — read from the API data.

**Files to modify**:
- `ui/src/components/workspace/TokenLogPanel.tsx` — main token log display
- `ui/src/components/workspace/WorkspaceChat.tsx` — context bar, daily stats
- `ui/src/components/workspace/UsageDashboard.tsx` — usage dashboard widget

## Phase 3 — UI/UX Improvements

| Image # | What | Fix |
|---------|------|-----|
| #2 | AutoForge/Claude pill badges need tooltips | Add hover tooltips: "AutoForge: prompt orchestration layer" and "Claude: underlying AI model". File: look for the badge rendering in `WorkspaceChatHeader.tsx` or similar. |
| #12 | Folder dropdown for new chat needs "+" button | When creating a new chat, the category dropdown should have an "Add new category" option at the bottom. File: `ui/src/components/workspace/WorkspaceSidebar.tsx` — the new chat form. |
| #13 | Library panel needs refresh button | Add a refresh/reload button next to the Library/Repos/Walkie-talkie tabs. One button that refreshes whichever tab is active. File: `ui/src/components/workspace/WorkspaceLibrary.tsx`. |
| #14 | PRD list wastes vertical space (token count on separate line) | Put the token count (10K, 15K, etc.) on the same line as the PRD name. File: `ui/src/components/workspace/WorkspaceLibrary.tsx` — the library file list rendering. |
| #15 | Auto-timestamp on new chats | Auto-add date/time stamp (format: `M.DD.YY/HH:MMp`) to new conversation titles. Add sorting: "Recent" (most recently used first) and "Sequential" (chronological order). File: `ui/src/components/workspace/WorkspaceSidebar.tsx` — conversation creation and list sorting. |
| #18 | Token log panel too wide, no resize | Add a draggable resize handle on the left edge of the token log panel. Currently hardcoded to `w-[320px]`. File: `ui/src/components/workspace/TokenLogPanel.tsx` — change to use a resizable container. |

## Phase 4 — Walkie-Talkie Persistence

| Image # | What | Fix |
|---------|------|-----|
| #6 (2nd image) | Walkie-talkie messages disappear on page refresh | Currently stored in React state only (`walkieTalkieLog` in `useWorkspaceChat.ts`). Need to persist to the database. The backend already has `workspace_database.py` — add a `WorkspaceWalkieTalkieMessage` model and CRUD. Save entries on send, load on conversation open. |
| Tab persistence | Walkie-talkie tab resets to Library on refresh | Save the active tab to localStorage. File: `ui/src/components/workspace/WorkspaceLibrary.tsx` — save/restore the selected tab index. |

**Files to modify**:
- `server/services/workspace_database.py` — add walkie-talkie message model
- `server/routers/workspace.py` — add REST endpoints for WT message CRUD
- `ui/src/hooks/useWorkspaceChat.ts` — load historical WT messages on conversation open
- `ui/src/components/workspace/WorkspaceLibrary.tsx` — save active tab to localStorage

## Phase 5 — Context Injection into System Prompt (C4)

Inject `[CONTEXT_USAGE: X/200000 (Y%)]` into the agent's system prompt so the agent itself can see its context utilization and self-regulate.

**Approach**: The walkie-talkie PreToolUse hook already injects messages at runtime. Add a periodic context usage injection alongside walkie-talkie messages.

**Files**:
- `server/services/workspace_chat_session.py` — in the PreToolUse hook, check current context % and inject a status line
- Track `last_context_injection_pct` to avoid flooding (only inject on 5% increments)

## Phase 6 — Multi-Repo Per Chat (F1)

Connect multiple repos to one chat. Add/remove repos during conversation.

This is a significant architecture change:
- UI: Add repo pill chips in the chat header with + and X buttons
- Backend: Extend `WorkspaceConversation` model to support multiple working directories
- Agent: May need to adjust filesystem sandboxing to allow multiple directories
- Save for a dedicated session.
