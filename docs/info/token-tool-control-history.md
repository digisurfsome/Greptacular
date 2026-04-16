# Token & Tool Control — What We Did and Why

> **Purpose of this file:** record of the token/tool optimization work so we can pick up where we left off next time without re-diagnosing.
> Updated: 2026-04-16

---

## The Problem We Were Solving

AutoForge workspace chat was burning through tokens faster than Claude Code web. Two specific leaks:

1. **File system overhead** — agents were exploring the repo from scratch every task. A previous pass put directory maps in place (`ui/CLAUDE.md`, `server/CLAUDE.md`, `docs/CLAUDE.md`) to reduce exploration.
2. **Tool use appeared excessive** — too many Glob/Grep/Read calls per turn vs. what Claude Code web seems to do.

The goal: match or beat Claude Code web's token efficiency for equivalent work.

---

## Changes Made (all on `main`)

### 1. Trimmed root `CLAUDE.md` — 150 lines → 50 lines
**Commit:** `7a549b2`

Removed:
- Duplicate "Tool Usage Rules" section (already in `.claude/rules/tool-efficiency.md`)
- Duplicate "Exploration Guardrails" (same — duplicated)
- Duplicate "After Edits" block (appeared twice, bug)

Moved out (so they only load when relevant, not every turn):
- Deploy Chain → `docs/references/deploy-chain.md`
- Communication / walkie-talkie / structured tags → `docs/references/communication.md`
- Verbose "Mandatory Reads" explanation — kept as 2-line pointer to the full guide

Why this matters: root CLAUDE.md loads on every agent turn. Every line saved here compounds across the whole session.

### 2. Created unified page index
**Commit:** `7a549b2`
**File:** `docs/references/page-index.md`

One row per page = every file for that page (page component + component folder + hook + router + service + PRD folder). Agent reads ONE file instead of three separate map files for single-page tasks.

Root CLAUDE.md now points here FIRST, with the three directory maps as fallback for full-inventory needs.

### 3. Added Subagent-First rule to root CLAUDE.md
**Commit:** `7a549b2`

New default: any search, file discovery, or code exploration → spawn an Explore subagent instead of searching in main context.

Why: main context is the user's conversation. Every Glob/Grep/Read result stays in context until the session ends. Subagents run in their own context and return a short summary — keeps main context clean and long-lived.

Exception: multi-step decision-making tasks where the agent needs to see each result and course-correct stay in main context.

### 4. Lowered workspace chat `max_turns` default — 50 → 34
**Commit:** `ceeecef`
**File:** `server/services/workspace_chat_session.py` line 88

`max_turns` = internal turns the agent can take for ONE of your messages. Normal work rarely exceeds 15–20 turns. 34 is a runaway cap — it kills agents stuck in tool-call loops, not normal work. Per-session override still available via WebSocket start message (range 10–100).

### 5. Disconnected unused Claude.ai MCP servers
**Not a code change — done via Claude.ai account settings → Customize → Connectors**

Before disconnect: ~115–130 MCP tool names loaded into every workspace chat session as deferred tools. Big offenders were Airtable (~17 tools), Asana (~27), Canva (~35), Figma (~14).

After disconnect: ~0 tool-name tax for MCPs that were the problem. AWS Marketplace and Excalidraw were **removed** (they don't respect Disconnect because they don't require auth). Airtable/Asana/Canva/Figma/Gmail/Google Calendar/Linear/PostHog/WordPress/Monday were **disconnected** (tool names replaced with single `authenticate` stubs, then effectively zero-cost).

Kept connected (they don't cost tokens in Claude Code — they're Claude.ai chat connectors, not MCP servers):
- Google Drive
- GitHub Integration

### 6. Per-turn effort pill (separate work by another agent)
**Commits:** `d764af8`, `d0ea8e9`, `89ae6c9`
**File:** `ui/src/pages/WorkspacePage.tsx` + backend plumbing

Mid-conversation effort shifter — Low / Medium / High pill next to the send button. Lets the owner dial effort per-message. Replaced the idea of auto-dropping default effort to low.

### 7. Header token meter rewired + 5-hour ledger now captures workspace chat
**Date:** 2026-04-16

**The problem:** The top-bar token meter (`TokenBudgetBadge`) was displaying the 5-hour rolling total from the `token_budget.db` ledger — but that ledger was only being written by CLI Scripter, NOT by workspace chat. Workspace runs wrote only to the per-conversation `workspace_token_log` table. Net effect: the meter jumped around randomly, dropped between messages, and gave numbers you couldn't trust. There was also no way to distinguish main-agent usage from subagent usage (the SDK already rolls subagent tokens into each main-agent turn, so this "bug" was a false premise — but the meter was still broken for a different reason).

**What changed:**

| Area | File | Change |
|------|------|--------|
| Frontend hook | `ui/src/hooks/useTokenBudget.ts` | Added `useCurrentWorkspaceConversationId()` (parses URL hash, listens to `hashchange`) and `useCurrentWorkspaceTokenUsage()` (polls per-conversation summary every 5s). Zero WebSocket impact — does NOT touch `useWorkspaceChat.ts`. |
| Header badge | `ui/src/components/TokenBudgetBadge.tsx` | Rewritten. Now shows `Ctx: 156K / 200K` format using the active conversation's `current_context_tokens` / `max_context_tokens`. Color thresholds are % of max (50/75/90) so they work for both 200K and 1M context modes. Hides when you're not on a workspace conversation page. |
| Backend summary | `server/services/workspace_database.py` → `get_token_log_summary` | Now also returns `context_mode` and `max_context_tokens` (200000 or 1000000) so the frontend can render the denominator. |
| Backend type | `ui/src/lib/types.ts` → `TokenLogSummary` | Added `context_mode?: string` and `max_context_tokens?: number`. |
| Ledger write hook | `server/services/workspace_chat_session.py` | After each `result_summary` writes to `workspace_token_log`, now ALSO calls `token_budget.log_session(session_type="workspace_chat", source="workspace", ...)`. This mirrors every main-agent turn into the global 5-hour ledger, so the Token Budget dashboard and (pre-existing) 5-hour views finally capture workspace chat usage — not just CLI Scripter runs. |

**What the header meter now means (post-change):**
- `Ctx: X / Y` — X is context tokens in use for the current conversation's most recent turn; Y is that conversation's context window size (200K or 1M).
- Monotonically grows within a conversation as context accumulates; resets on `/compact` or a new conversation.
- "Main agent only" by construction — subagent work is already bundled into each parent turn by the SDK, so NO filtering or per-agent-type field is needed.
- Hides on non-workspace pages (badge lives in global `App.tsx` header, so it renders on every page).

**What the 5-hour / Token Budget dashboard views now capture (post-change):**
- CLI Scripter sessions (unchanged)
- Workspace chat turns (NEW — previously invisible)
- AutoForge calibration entries (unchanged)

Each workspace turn writes one row to the `token_log` table with `session_type="workspace_chat"` and `source="workspace"`. Rows age out of the 5-hour window naturally as they always did.

**False starts / things NOT done:**
- Did NOT add an `agent_type` column to the workspace DB. Subagent usage is already rolled up into parent turns — adding a column would have been wasted work.
- Did NOT touch `useWorkspaceChat.ts` or `WorkspaceChat.tsx` (CLAUDE.md ban on fiddling with the WebSocket hook). The new badge logic gets the conversation ID by reading the URL hash directly — same mechanism `WorkspacePage.tsx` uses.
- Did NOT add a backfill for old workspace conversations that ran before this change. Their turns were never logged to `token_budget.db` and never will be. Going forward only.

**Verification after pulling:**
1. Open a fresh workspace chat. Send one message and wait for the response.
2. Top-bar badge should show `Ctx: ~XK / 200K` (or `/ 1M`) with color based on %.
3. Navigate away (e.g. to Dashboard). Badge should disappear.
4. Navigate back to the conversation. Badge should reappear with the correct number.
5. Hit `/api/token-budget/status` in browser — `five_hour.total_tokens` should now include your workspace turn (previously it wouldn't have).

---

## What's Still on the Table (Remaining Levers)

In priority order, if we need to squeeze more out later:

| # | Lever | Effort | Expected Savings | Notes |
|---|-------|--------|-------------------|-------|
| 1 | Shorten descriptions in `ui/CLAUDE.md` / `server/CLAUDE.md` / `docs/CLAUDE.md` to 3–5 words | 45 min | 5–10% on full-inventory reads | Lower priority now that `page-index.md` reduces how often those get read |
| 2 | Audit sub-agent context inheritance — do spawned subagents reload the full root CLAUDE.md or inherit? If reload, we're paying the (now slimmer) tax Nx per session. | 30 min audit | Unknown, possibly meaningful | Worth checking in AutoForge's agent spawning code |
| 3 | Hard hook enforcement — `.claude/settings.json` pre-hook counting Glob/Grep calls, blocks after N | 2 hrs | 15–25% on misbehaving agents | Only if softer rules aren't working. Can frustrate legitimate investigation. |
| 4 | Per-directory CLAUDE.md in deep folders (e.g., `ui/src/components/workspace/CLAUDE.md`) | 1 hr per folder | 5–10% on that page's work | Only worth it for 3–4 most-used pages |
| 5 | Shrink the three directory CLAUDE.md maps — some rows still have long descriptions | 30 min | 5% | Minor |

**What we are NOT doing (and why):**
- NOT dropping the default `effortLevel` to low — replaced by the per-turn shifter pill. Owner can dial it mid-conversation now.
- NOT adding hard per-turn tool caps — the prose rules + subagent default + `max_turns=34` cover it. Hard caps create dead-ends.

---

## Quick Verification

To check the changes are live after pulling to `C:\Users\lober\Greptacular`:

1. `cat CLAUDE.md | wc -l` — should be ~55 lines, not ~150
2. `ls docs/references/page-index.md` — should exist
3. `ls docs/references/deploy-chain.md` — should exist
4. `ls docs/references/communication.md` — should exist
5. `grep 'max_turns' server/services/workspace_chat_session.py` — should show `"max_turns": 34`
6. Open a fresh workspace chat, ask the agent to list its deferred MCP tools — should be minimal (no Airtable/Asana/Canva/Figma mega-schemas)

---

## Honest Accounting — What I Got Wrong

- **Initial MCP estimate was inflated.** I first claimed MCPs were costing "5–15k tokens per turn." Real cost was closer to 1–2k per turn because Claude Code uses deferred tool loading (only tool names load by default, full schemas load via `ToolSearch` on demand). The other agent who said "not affected" was more correct than I was.
- **Net MCP savings:** real but smaller than first claimed. Still worth doing — disconnect cut ~80% of the MCP name tax, Remove on AWS Marketplace + Excalidraw finished the job.

---

## Files Changed Summary

| File | Change |
|------|--------|
| `CLAUDE.md` | Trimmed 150 → 50 lines, added Subagent-First rule |
| `docs/references/page-index.md` | **NEW** — unified per-page file index |
| `docs/references/deploy-chain.md` | **NEW** — moved out of root |
| `docs/references/communication.md` | **NEW** — moved out of root |
| `server/services/workspace_chat_session.py` | `max_turns` 50 → 34; mirror workspace turns into `token_budget.db` ledger |
| `server/services/workspace_database.py` | `get_token_log_summary` now returns `context_mode` + `max_context_tokens` |
| `ui/src/hooks/useTokenBudget.ts` | Added `useCurrentWorkspaceConversationId` + `useCurrentWorkspaceTokenUsage` hooks |
| `ui/src/components/TokenBudgetBadge.tsx` | Rewritten — per-conversation `Ctx: X / Y` meter, % color thresholds |
| `ui/src/lib/types.ts` | `TokenLogSummary` gained `context_mode` + `max_context_tokens` fields |

---

## Next Session Starter Prompt (if you want to pick this up later)

> "Read `docs/info/token-tool-control-history.md` for the context of prior token/tool optimization work. Then review the Remaining Levers section and tell me which one you'd tackle next and why."
