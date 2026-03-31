# Features for Next Session

## 1. Chat Search (Priority: HIGH)

**Why:** Owner wasted 2 days searching through Claude Code Web chats with no search. This is critical for any multi-chat workflow.

**What:** Full-text search across ALL workspace conversations — messages, titles, everything.

**Backend:**
- New endpoint: `GET /api/workspace/search?q=keyword&limit=20`
- Search across `workspace_messages` table: `content LIKE '%keyword%'`
- Better: Add SQLite FTS5 virtual table for fast full-text search
- Return: conversation_id, conversation_title, message_id, role, content snippet with match highlighted, timestamp
- File: `server/routers/workspace.py` — add new route
- File: `server/services/workspace_database.py` — add search query function

**Frontend:**
- Search bar at top of Conversations sidebar (left panel)
- Live/predictive filtering as user types (debounced 300ms)
- Results show: chat name, matching text snippet (highlighted), date
- Click result → navigates to that conversation, scrolls to matching message
- File: `ui/src/components/workspace/WorkspacePage.tsx` — add search input to sidebar
- File: `ui/src/lib/api.ts` — add `searchWorkspaceChats(query)` function

**Difficulty: 3/10 | Confidence: 95%**

## 2. Prompt Buttons (Priority: HIGH)

**Why:** Owner has to type/dictate the same instructions repeatedly. Pre-set buttons save time and reduce errors.

**What:** A row of quick-action buttons above the chat input. One click sends a pre-written message.

**Default buttons:**
- "Merge & Push" → sends "Merge your changes to main, push to origin/main, confirm commit hash. Run `cd ui && npm run build` first."
- "Write Handoff" → sends "Write a comprehensive handoff summary to .claude/handoffs/ including: what was done, what's broken, what's next, key decisions."
- "End Session" → triggers the existing end session flow
- "Be Creative" → sends "Think outside the box. Don't just follow the obvious path. Consider alternative approaches."
- "Run Tests" → sends "Run all tests and report results. Fix any failures."

**Customization:**
- User can add/edit/remove buttons
- Store in localStorage or in the workspace settings DB
- Each button: { label, message, icon?, color? }

**Frontend:**
- Horizontal scrollable row of pill/chip buttons between the chat messages and input area
- Only show when input is empty (hide when typing)
- File: `ui/src/components/workspace/WorkspaceChat.tsx` — add PromptButtons component above input
- Alternatively: dropdown/popover menu triggered by a button

**Difficulty: 2/10 | Confidence: 99%**

## 3. Fix Token Gauges (Priority: MEDIUM)

**Why:** The token panel shows cumulative SDK totals (485K) instead of actual current context position (~300K). Numbers bounce around and are unreliable.

**What the gauges should show:**
- **Context position:** The LATEST API turn's `input_tokens + cache_read_tokens` (this is your actual context fill level)
- **Session total output:** Sum of all `output_tokens` across all turns (correct as-is)
- **API cost equivalent:** What this would cost at API rates (correct as-is)
- **Subscription note:** "Included in Max plan" or similar
- **Walkie-talkie savings:** "X tokens saved by walkie-talkie mode" (future)

**The fix:**
- In `useWorkspaceChat.ts`, the `token_usage` handler should store the LATEST turn's values, not accumulate
- The `result_summary` token log entry already has per-turn values — use those
- The context bar should show `latest_input_tokens / context_window`, NOT `cumulative_total / context_window`
- File: `ui/src/hooks/useWorkspaceChat.ts` — token_usage handler
- File: `ui/src/components/workspace/WorkspaceChat.tsx` — TokenLogPanel
- File: `server/services/workspace_chat_session.py` — the token_usage yield (already partially fixed)

**Difficulty: 3/10 | Confidence: 85%**

## 4. Merge 3 Agent Fixes (Priority: CRITICAL — do first)

**Before any of the above, merge the 3 battle agents' work:**
- Agent 1: flushSync, pong timeout, handleSend stability
- Agent 2: Auto-scroll, walkie-talkie display
- Agent 3: TCP_NODELAY monkey-patch (server/tcp_nodelay.py)

**Check for conflicts between agents** — they all edited the same files (useWorkspaceChat.ts, WorkspaceChat.tsx). Resolve carefully.

**Test after merge:** Start a chat, send a message, response must appear WITHOUT sending another message.

## 5. PRD Manager System (Priority: FUTURE)

Owner has 40-50 PRDs sitting in AutoForge that haven't been implemented. A manager agent could:
- Read all PRDs from a folder
- Prioritize them
- Assign to sub-agents
- Track completion
- Report status

This is part of the Swarm Architecture — see `.claude/handoffs/swarm-architecture-design.md`.
