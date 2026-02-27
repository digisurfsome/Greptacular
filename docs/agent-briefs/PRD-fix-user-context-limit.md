# PRD: Fix user_context Character Limit in YT Strategy Lab

> **Priority:** High — blocks normal usage
> **Complexity:** Low — single field validation change + minor UI work
> **Estimated context cost:** ~15% (briefing + 3 files to edit)

---

## Problem

The `user_context` field in YT Lab's processing and discovery endpoints is capped at **10,000 characters** via Pydantic validation:

```python
# server/routers/yt_processing.py:68
user_context: str = Field("", max_length=10_000)
```

Users frequently paste long-form notes, stream-of-consciousness context, and multi-topic instructions that exceed 10K characters. The backend returns a 422 validation error:

```json
{"detail":[{"type":"string_too_long","loc":["body","user_context"],"msg":"String should have at most 10000 characters"}]}
```

The error is shown raw in the UI with no user-friendly message and no way to know how much to cut.

---

## Solution

1. **Raise the backend limit** to 100,000 characters (~25K tokens — still well within what Claude can handle in a single prompt)
2. **Add a character counter** to the textarea in the UI so users can see their length
3. **Show a friendly error** if somehow exceeded, instead of raw JSON

---

## Files to Modify

| File | Change |
|------|--------|
| `server/routers/yt_processing.py:68` | Change `max_length=10_000` → `max_length=100_000` |
| `ui/src/pages/YTStrategyLabPage.tsx:1518` | Add character counter below the userContext textarea |
| `ui/src/components/yt-lab/DiscoveryPanel.tsx:439` | Add character counter below the discovery userContext textarea |

---

## Agent Handoff

```
## MANDATORY: Context Efficiency Rules

You are working on the Greptacular codebase. Follow these rules strictly to preserve your context window for coding:

### Step 1: Read Briefings (do this FIRST, before anything else)
1. Read `AGENT_BRIEFING.md` at project root — master architecture overview
2. Read `docs/agent-briefs/yt-lab-discovery.md` — covers both processing and discovery

### Step 2: Read ONLY Files You Will Edit
- `server/routers/yt_processing.py` — the Pydantic model with the max_length limit
- `ui/src/pages/YTStrategyLabPage.tsx` — the processing textarea (around line 1518)
- `ui/src/components/yt-lab/DiscoveryPanel.tsx` — the discovery textarea (around line 439)

Do NOT read any other files. The briefs cover everything else.

### Step 3: Use Subagents for Everything Else
- If you need to check how other textareas show character counts, spawn an Explore subagent
- If you need to understand the API call pattern, spawn an Explore subagent
- NEVER run Glob/Grep yourself unless it's a single targeted search

### Step 4: Context Budget
- Stop coding at 50% context usage
- This task should complete well under 30%

---

## Your Task

Fix the user_context character limit in YT Strategy Lab. Three changes:

### 1. Backend: Raise the limit (server/routers/yt_processing.py)

Line 68 — change `max_length=10_000` to `max_length=100_000`:

```python
user_context: str = Field("", max_length=100_000)
```

### 2. Frontend: Add character counter to processing textarea (ui/src/pages/YTStrategyLabPage.tsx)

Find the textarea around line 1518 where `value={userContext}` and `onChange` sets it. Add a small character counter below it showing current length and max:

```tsx
<p className="text-xs text-gray-500 mt-1 text-right">
  {userContext.length.toLocaleString()} / 100,000
</p>
```

If over 90,000 chars, make it yellow. If over 100,000, make it red.

### 3. Frontend: Add character counter to discovery textarea (ui/src/components/yt-lab/DiscoveryPanel.tsx)

Same pattern around line 439 where the discovery panel's userContext textarea lives. Same counter style.

## Files You Will Modify
- server/routers/yt_processing.py
- ui/src/pages/YTStrategyLabPage.tsx
- ui/src/components/yt-lab/DiscoveryPanel.tsx

## Acceptance Criteria
- User can submit user_context up to 100,000 characters without error
- Both textareas show a character counter (current / max)
- Counter turns yellow at 90% usage, red at 100%
- No raw JSON errors shown to the user
```

---

## Notes

- 100K chars is ~25K tokens — Claude handles this easily, even with a full transcript already in the prompt
- No database changes needed
- No new files needed
- Should take a single agent session well under 30% context
