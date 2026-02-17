# Intelligent Context Handoff System - Handoff Document

## Status: Ready to Implement

## Overview

This document describes a system for managing the most expensive resource in AI-assisted development: **context window quality**. It addresses the reality that after ~50% context usage, model performance degrades -- cracks widen and errors start falling through. Rather than accept this degradation or rely on crude compaction, this system:

1. **Knows where you are** -- real-time context meter with hard stop capability
2. **Prepares the handoff in real-time** -- continuously categorizes and pre-compacts context as the conversation happens (not after the fact)
3. **Executes a clean baton pass** -- at 49%, stops accepting new work and spends the last 1% preparing a handoff package that a new agent can absorb with near-zero information loss
4. **Uses RAG as a safety net** -- full conversation history is retrievable, so the handoff can be compact (high-priority context) while the RAG fills in details on demand

The core insight: **compaction after the fact always loses details because everything looks equally important in retrospect. But if you categorize in real-time as ideas are being discussed, you know what's critical vs. what's fluff.**

---

## Part 1: Context Window Meter with Hard Stop

### What Exists Today

The workspace chat already tracks token usage via `EnhancedContextBudgetBar` and the `UsageDashboard`. The `useWorkspaceChat` hook receives `token_usage` events with `total_tokens` and `context_window` from the server. The `contextMode` toggle switches between 1M and 200K.

### What Needs to Be Added

**1. Context percentage display that's always visible and accurate**

The current meter shows tokens used vs. total budget. For the 50% rule, we need:
- A prominent percentage display (already exists, fixed to show precision)
- A **configurable warning threshold** (default 45%) and **hard stop threshold** (default 49%)
- Visual state changes: green (0-45%), yellow (45-49%), red (49%+)

**2. Hard stop at configurable threshold**

When the context reaches the hard stop threshold:
- Block further user input (disable the send button)
- Show a full-width banner: "Context at 49%. Preparing handoff..."
- Automatically trigger the handoff preparation (Part 2)
- Provide a "Start New Conversation with Handoff" button

**3. User-configurable thresholds**

Add to the settings panel (`SettingsModal.tsx`) or the workspace header:
- Warning threshold: slider 30-90%, default 45%
- Hard stop threshold: slider 35-95%, default 49%
- Hard stop enabled: toggle on/off (some users may not want this)

### Where to Implement

- `ui/src/components/workspace/WorkspaceChat.tsx` -- add input blocking logic, threshold checking
- `ui/src/components/workspace/EnhancedContextBudgetBar.tsx` -- add threshold markers on the bar
- `ui/src/hooks/useWorkspaceChat.ts` -- add threshold state, warning events
- `server/services/workspace_chat_session.py` -- server-side threshold enforcement (backup)
- Settings storage: localStorage for quick access, optionally persisted to workspace database

---

## Part 2: Real-Time Context Categorization (The Revolutionary Part)

### The Problem with After-the-Fact Compaction

When Claude's built-in compaction runs, it sees a giant wall of conversation and tries to summarize it. The problem:
- It doesn't know which details the user cares about most
- Technical specifics (exact error messages, specific API endpoints, code patterns) get generalized
- Context from early in the conversation that was critical for a decision gets dropped because it's "old"
- The user's exact words about what they want get paraphrased into something subtly different

### The Solution: Categorize as You Go

As each message is exchanged, the system categorizes its content into buckets in real-time. This is the same principle as the user's PRD real-time filing system -- watching multiple windows fill in as the conversation happens.

**Category buckets:**

```
1. DECISIONS     -- Concrete decisions made ("we're using Tailwind", "the meter goes in the header")
2. REQUIREMENTS  -- What the user explicitly asked for ("I need a toast notification")
3. ARCHITECTURE  -- Technical decisions about structure ("the ledger table goes in workspace.db")
4. CODE_CHANGES  -- Files modified, what was changed, why
5. BUGS_FOUND    -- Issues discovered, whether fixed or still open
6. IDEAS         -- Ideas mentioned but not yet implemented (future work)
7. CONTEXT       -- Background info that explains WHY decisions were made
8. FLUFF         -- Pleasantries, tangents, thinking-out-loud that doesn't affect the work
```

**How categorization works:**

After each message exchange (user message + assistant response), a lightweight background process:
1. Takes the message pair
2. Classifies each substantive piece of information into a category
3. Extracts the key facts/decisions/requirements as structured items
4. Stores them in a categorized index

This can be done by:
- **Option A (cheap)**: A rules-based classifier using keyword patterns. Fast, free, but less accurate.
- **Option B (accurate)**: A small model call (Haiku) that takes the message pair and outputs categorized items. Costs ~100 tokens per classification. Over a 100-message conversation, that's ~10K tokens -- negligible.
- **Option C (hybrid)**: Rules-based for obvious categories (code changes are easy to detect), Haiku for ambiguous content.

### Data Model

```sql
create table context_categories (
    id integer primary key autoincrement,
    conversation_id integer not null,
    message_id integer,                    -- which message this came from
    category text not null,                -- DECISIONS, REQUIREMENTS, etc.
    priority text default 'medium',        -- "critical", "high", "medium", "low"
    content text not null,                 -- the extracted fact/decision/requirement
    timestamp datetime default current_timestamp,
    included_in_handoff boolean default false
);

create index idx_cc_conversation on context_categories(conversation_id);
create index idx_cc_category on context_categories(category, conversation_id);
```

### Where to Implement

- `server/services/workspace_context_tracker.py` -- new service: categorization logic, runs after each message
- `server/services/workspace_chat_session.py` -- trigger categorization after storing each assistant response (background task, non-blocking)
- `server/services/workspace_database.py` -- new model and CRUD for `context_categories`
- Could reuse the auto-summary trigger pattern already in `_query_claude()` (lines 497-510)

---

## Part 3: The Baton Pass (Intelligent Handoff)

### What Happens at 49%

When context hits the hard stop threshold:

**Step 1: Generate the handoff package (the last 1% of context)**

The system takes the categorized index from Part 2 and builds a structured handoff:

```markdown
# Conversation Handoff: [auto-generated title]

## Active Task
[What we were working on when the handoff triggered]

## Decisions Made (DO NOT REVISIT)
- [Decision 1] -- [why]
- [Decision 2] -- [why]
...

## Requirements (MUST IMPLEMENT)
- [Requirement 1] -- [status: done/in-progress/pending]
- [Requirement 2] -- [status]
...

## Architecture
- [Key architectural decisions and patterns established]

## Code Changes This Session
- [file]: [what changed and why]
...

## Open Issues
- [Bug or issue still unresolved]
...

## Pending Ideas (NOT YET STARTED)
- [Idea mentioned but not implemented]
...

## Context for Understanding
- [Key background info the new agent needs]
...

## Files to Read First
- [Critical files the new agent should read to get oriented]
```

**Step 2: Store the handoff**

- Save as a `.claude/handoffs/auto-handoff-{timestamp}.md` file (like the existing handoff pattern)
- Also store in the workspace database for retrieval
- Save the full categorized index as structured data (not just the summary)

**Step 3: Present to the user**

- Show the handoff content in the chat for review
- "Start New Conversation with Handoff" button
- Option to edit the handoff before passing it

**Step 4: New conversation initialization**

When the user clicks "Start New Conversation with Handoff":
1. Create a new conversation in the workspace database
2. Inject the handoff as the first system context (prepended to the first message, similar to how history is loaded in `send_message()` lines 360-406)
3. The new agent reads the handoff and is immediately oriented

### The RAG Safety Net

The handoff is a SUMMARY -- it's the critical facts arranged by priority. But sometimes the new agent needs a detail that didn't make the cut. That's where RAG comes in.

**How RAG enhances the handoff:**

1. The FULL conversation history remains in the database (it already is -- `workspace_messages` table)
2. The categorized index from Part 2 provides searchable, structured metadata
3. When the new agent encounters something unclear from the handoff, it can query:
   - "What exactly did the user say about the meter design?" -> RAG retrieves the relevant messages
   - "What error was encountered with the toggle?" -> RAG finds the specific error discussion

**RAG implementation options:**

- **Option A (simple)**: Keyword search over stored messages filtered by category. Fast, no embedding needed.
- **Option B (semantic)**: Embed messages using a small model, store vectors, enable similarity search. More accurate but heavier infrastructure.
- **Option C (hybrid + existing)**: The workspace already has an auto-summary system (`workspace_summary.py`). Extend it with the categorized index. The new agent gets: handoff summary + categorized index + ability to query specific past messages.

### Existing Infrastructure to Leverage

- `server/services/workspace_summary.py` -- auto-summary generation with `trigger_summary_generation()`
- `server/services/workspace_database.py` -- `get_messages_for_context()` already does budget-aware message loading
- `server/services/workspace_chat_session.py` -- `send_message()` already prepends history/summary to first message in resumed conversations (lines 360-406)
- `.claude/handoffs/` -- established pattern for handoff documents
- `ui/src/components/workspace/ChatForkModal.tsx` -- existing fork-chat UI that could be adapted for handoff-to-new-chat

---

## Part 4: Pre-Compaction (Continuous Background Compression)

### The Concept

Instead of waiting until 49% to prepare for handoff, do lightweight pre-compaction continuously. Think of it as "progressive summarization" happening alongside the conversation.

**Every 10% of context usage:**
1. Take all categorized items since the last checkpoint
2. Merge/deduplicate with the running handoff state
3. Validate: are earlier decisions still valid, or were they overridden?
4. Update priority: items discussed more recently get a freshness boost
5. Store the updated handoff state

This means at 49%, the handoff is 90% already done. The final 1% is just:
- Adding the "active task" (what we were literally in the middle of)
- Final validation pass
- Formatting and presentation

### The Priority Scoring Algorithm

Each categorized item gets a priority score based on:

```
score = base_weight(category) * recency_factor * mention_count * override_penalty

where:
  base_weight: DECISIONS=10, REQUIREMENTS=9, BUGS=8, ARCHITECTURE=7, CODE_CHANGES=6, IDEAS=4, CONTEXT=3, FLUFF=0
  recency_factor: 1.0 for recent (last 10%), decaying to 0.5 for oldest items
  mention_count: boost if referenced multiple times (indicates importance)
  override_penalty: 0 if a later decision explicitly overrode this one
```

Items scoring above the threshold make it into the handoff. Items below the threshold are available via RAG but not in the handoff summary.

---

## Part 5: Context Window for AutoForge Agents (Not Just Workspace)

### The Problem

Everything above applies to the workspace chat. But AutoForge coding agents ALSO run long sessions and ALSO suffer from context degradation. The difference: AutoForge agents run autonomously, so there's no user to click "Start New Conversation."

### What AutoForge Agents Need

1. **Self-monitoring**: The agent should track its own context usage (it already processes `token_usage`-equivalent data internally via the Claude SDK)
2. **Self-handoff**: When approaching 50%, the agent should:
   - Finish the current feature (don't leave work half-done)
   - Write a handoff note to the features database or a file
   - Exit cleanly
   - The orchestrator spawns a fresh agent that reads the handoff

3. **Feature-level context tracking**: Each feature attempt should log how much context it consumed. This feeds into the nerfing detection system (from the other handoff document).

### Where to Implement

- `agent.py` -- add context threshold monitoring to the agent session loop
- `autonomous_agent_demo.py` -- handle clean agent restarts after threshold exit
- `parallel_orchestrator.py` -- handle threshold-triggered agent cycling in parallel mode
- The MCP feature server (`mcp_server/feature_mcp.py`) could gain a `feature_set_handoff_note` tool

---

## Implementation Priority

1. **Context meter with hard stop** (Part 1) -- Quick win, high impact. Just UI logic and threshold checking.
2. **Real-time categorization** (Part 2) -- The foundation everything else depends on. Start with Option A (rules-based) for speed, upgrade to Haiku later.
3. **Pre-compaction checkpoints** (Part 4) -- Natural extension of Part 2. Once categorization works, periodic compression is straightforward.
4. **The baton pass** (Part 3) -- The payoff. Requires Parts 1+2 to be working.
5. **AutoForge agent self-handoff** (Part 5) -- Separate track, can be built in parallel.

---

## Key Design Principles

1. **Never lose the user's exact words** -- The raw conversation is always in the database. Categorization and compression add structure on top, they don't replace the original.
2. **Categorize in real-time, not after the fact** -- This is the difference between filing papers as they arrive vs. sorting a pile at the end of the month.
3. **The handoff is a curated highlight reel, RAG is the full tape** -- The new agent gets a crisp briefing AND the ability to go deeper on any topic.
4. **50% is not a suggestion** -- The hard stop should be enforced by default. Users can override it, but the system should make the healthy choice the easy choice.
5. **Progressive, not sudden** -- Pre-compaction at 10% intervals means the handoff is never a surprise and never a scramble.

---

## Related Handoff Documents

- `.claude/handoffs/usage-intelligence-handoff.md` -- Global usage meters, rate limit learning, nerfing detection, style learning. Built in the same session as this document.
- `.claude/handoffs/build-intelligence-handoff.md` -- Build history intelligence, PRD quality scoring. Overlaps with the nerfing detection concept.

## Technical Context from This Session

The following was built and pushed during this session (branch: `claude/debug-chat-feature-2Hk7b`):
- Context mode toggle (1M/200K) with toast notification
- Usage dashboard with daily/weekly/monthly tracking
- Cost zone estimation (standard vs premium tier)
- Rate limit learning with auto-detection
- Zero-meter bug fixes
- All code passes `ruff check`, `tsc --noEmit`, and `eslint`
