# Optimization Tracker

> **Master list of everything we're doing (and plan to do) to reduce token usage and improve agent efficiency.**
> Updated: 2026-04-03
>
> Use the "Your Notes" sections to jot down ideas. Bring them up with an agent when ready.

---

## Status Key
- DONE = Implemented and live
- NEXT = Ready to build, high priority
- PLANNED = Designed but not yet built
- IDEA = Concept, needs more thought

---

## 1. File Maps (DONE)

**What:** CLAUDE.md files in each major directory that tell agents exactly where every file is.
**Why:** Eliminates 30-50% of exploratory tool calls (Glob, Grep, Read).
**Files created:**
- `ui/CLAUDE.md` — Full page, component, hook, and utility file map
- `server/CLAUDE.md` — Full router and service file map
- `docs/CLAUDE.md` — Docs directory map with "don't read this" guidance

**How it saves tokens:** Agent reads a 100-line map file (cheap) instead of running 5-10 Glob/Grep searches + reading 5-10 files to figure out where things are (expensive).

**Your Notes:**
> _Write your ideas here..._

---

## 2. Tool Efficiency Rules (DONE)

**What:** `.claude/rules/tool-efficiency.md` — Mandatory rules every agent follows.
**Why:** Prevents wasteful tool usage patterns.
**Key rules:**
- Read the map before exploring
- Stay in your lane (only touch files related to your task)
- Maximum 3 exploratory searches
- No drive-by improvements
- Batch reads into parallel calls
- Token budget awareness (target: <15 tool calls per single-page task)

**How it saves tokens:** Each unnecessary tool call costs 500-2,000 tokens. Rules prevent 5-10 unnecessary calls per task = 5,000-20,000 tokens saved per task.

**Your Notes:**
> _Write your ideas here..._

---

## 3. New Page Standards (DONE)

**What:** `.claude/rules/new-page-standards.md` — Structure template for all future pages.
**Why:** Consistent structure means agents know where to find things without searching.
**Key patterns:**
- Predictable file locations (page, components, hooks, router, service, PRD folder)
- Naming conventions (PascalCase pages, kebab-case folders, snake_case Python)
- Anti-patterns list (what NOT to do)
- Mandatory file map updates when adding new pages

**How it saves tokens:** Future pages follow the same pattern, so agents don't need to explore to understand the structure.

**Your Notes:**
> _Write your ideas here..._

---

## 4. Rant Compressor Agent (PLANNED)

**What:** A Haiku-powered agent that sits between you and the worker agent. Takes your voice/text brain dump and compresses it into a short, structured task description before sending.
**Why:** Your rants are ~2,000 tokens. Compressed = ~300 tokens. Over a 10-turn conversation with Opus, that's ~17,000 input tokens saved on the expensive model.
**Architecture:**
- Haiku agent with a simple system prompt: "Compress into TASK, CONTEXT, FILES, CONSTRAINTS"
- UI: "Prep" button → shows side-by-side (your rant | compressed) → "Send" button
- Toggle: auto-compress ON/OFF
- Cost: ~$0.001 per compression (Haiku is 25x cheaper than Opus)

**Build location:** Workspace chat UI + a new lightweight service

**Your Notes:**
> _Write your ideas here..._

---

## 5. Task Scout Agent (PLANNED)

**What:** A Haiku agent that runs before the worker starts. Reads the task + file maps → outputs a JSON with exactly which files and tools the worker needs.
**Why:** Gives the worker a "tool rental kit" so it doesn't explore blindly.
**Architecture:**
- Input: compressed task + directory CLAUDE.md files
- Output: `{ files_needed: [...], tools_allowed: [...], scope_directories: [...], do_not_explore: [...] }`
- Injected into the worker's system prompt
- Cost: ~1,000 tokens per scout call
- Savings: eliminates 5-15 exploratory tool calls from the worker

**Build location:** Background session manager or a new pre-task service

**Your Notes:**
> _Write your ideas here..._

---

## 6. Scope Lock Rules (PLANNED)

**What:** System prompt rules that prevent agents from touching files outside their task scope.
**Why:** Prevents cascade where fixing one thing breaks another and the agent spends 30 minutes chasing it.
**How:**
- "If you need to edit a file outside your assigned scope, STOP and ask the human first."
- Combined with Task Scout output: "Your scope is: [file list]. Do not modify files outside this list."

**Your Notes:**
> _Write your ideas here..._

---

## 7. Token Budget Per Task (PLANNED)

**What:** Hard token budget in the system prompt: "You have a budget of X tokens for this task."
**Why:** Prevents runaway sessions that burn 200K tokens on a 20K task.
**How:**
- Simple tasks (fix a button, update text): 30,000 token budget
- Medium tasks (add a feature to one page): 80,000 token budget
- Complex tasks (multi-page feature, new page): 150,000 token budget
- System prompt says: "If approaching your budget, STOP and report progress so far."

**Your Notes:**
> _Write your ideas here..._

---

## 8. Map Keeper Agent (IDEA)

**What:** An agent whose only job is keeping the CLAUDE.md file maps up to date as the codebase changes.
**Why:** If file maps go stale, agents start exploring again and we lose the savings.
**Options:**
- A: Post-commit hook that checks if new files were created and flags the map for update
- B: Periodic Haiku agent that diffs the directory listing against the map and updates it
- C: Rule in new-page-standards that says "update the map" (manual, but free)

**Your Notes:**
> _Write your ideas here..._

---

## 9. Log Analysis Dashboard (IDEA)

**What:** Pull the token log data (already tracked in workspace.db) into a visual optimization dashboard.
**Why:** See which tools eat the most tokens, which conversations were expensive, and spot patterns.
**What exists already:**
- `workspace_token_log` table tracks every tool call, result, tokens, and cost
- `get_conversation_token_total()` already computes per-tool breakdowns
- `TokenLogPanel` component already shows this data per conversation
**What's needed:**
- Cross-conversation aggregation (daily/weekly totals)
- "Top 10 most expensive conversations" view
- "Average tool calls per task type" breakdown
- Recommendations: "Conversations with >20 Read calls could benefit from file maps"

**Your Notes:**
> _Write your ideas here..._

---

## 10. Root CLAUDE.md Optimization (PLANNED)

**What:** Slim down the root CLAUDE.md from ~500 lines to a routing table.
**Why:** Every agent reads it every session. Most of it is irrelevant to most tasks.
**Plan:**
- Keep ONLY: subscription auth rules, SDK pattern, WebSocket rule, and task-type routing
- Move everything else to sub-files (most already moved to ui/server/docs CLAUDE.md files)
- Add: "Read .claude/rules/tool-efficiency.md before starting any task"
- Add: "New page? Read .claude/rules/new-page-standards.md first"
- Target: root CLAUDE.md under 150 lines

**Your Notes:**
> _Write your ideas here..._

---

## 11. Deterministic Coding Patterns (IDEA)

**What:** Build the Wall/Door/Room system (from PRD Maker) into AutoForge's coding workflow.
**Why:** Deterministic steps (Walls) don't need AI. Only Doors and Rooms need AI thinking. This would massively reduce token usage for predictable work.
**Connection to PRD Maker:** Stage 5 (7-Question Scaffolding) classifies every step as Wall, Door, or Room. If we bring that classification into the workspace, agents skip AI for Wall steps entirely.

**Your Notes:**
> _Write your ideas here..._

---

## Token Cost Reference

Quick reference for how much things cost (Opus 4.6):

| Action | Approximate Cost |
|--------|-----------------|
| Reading a 200-line file | ~1,500 tokens input |
| Reading a 2000-line file | ~15,000 tokens input |
| One Glob search result | ~500 tokens input |
| One Grep search result | ~1,000 tokens input |
| Agent reading root CLAUDE.md | ~4,000 tokens input |
| Your typical rant message | ~2,000 tokens input |
| Compressed task description | ~300 tokens input |
| 10-turn conversation overhead | Each turn re-sends entire history |

**The multiplier effect:** In a 10-turn conversation, every token in the first message gets re-sent 10 times. A 2,000-token rant in turn 1 = 20,000 tokens by turn 10. Compression pays for itself many times over.

---

## Quick Wins Summary (Priority Order)

1. **File maps** (DONE) — Biggest immediate savings
2. **Tool efficiency rules** (DONE) — Prevents wasteful patterns
3. **Page standards** (DONE) — Consistent structure going forward
4. **Root CLAUDE.md slim-down** (NEXT) — Reduces per-session overhead
5. **Rant compressor** (NEXT) — Reduces your input cost
6. **Task scout** (NEXT) — Gives workers a focused kit
7. **Scope lock** (NEXT) — Prevents scope creep in agents
8. **Token budget per task** (NEXT) — Prevents runaway sessions
9. **Map keeper** (LATER) — Maintenance automation
10. **Log dashboard** (LATER) — Visibility and ongoing optimization
11. **Deterministic patterns** (LATER) — Highest ceiling but most complex
