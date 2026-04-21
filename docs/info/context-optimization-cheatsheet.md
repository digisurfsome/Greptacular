# Claude Code Context Optimization — Cheat Sheet

---

## 1. Understand What "Context" Is

- Everything Claude can see at once: system prompt, full conversation, every tool call and output, every file read, every skill/MCP server/agent in the project
- Think of it as Claude's **working memory**
- Claude Code gives a **1 million token** context window
- **Startup overhead alone** burns ~8,000 tokens before you type anything (could be far more — creator found 62,000 on a fresh session)

**Action:** Open a fresh session and run `/context` to see your baseline token cost before sending anything.

---

## 2. How Tokens Actually Work (Critical)

- Claude **rereads the entire conversation from the beginning** on every message
- Cost compounds **exponentially**, not linearly
  - Message 1: ~500 tokens
  - Message 30: ~15,500 tokens (31x more)
  - After 30 messages: ~250,000 cumulative tokens
- One dev tracked a 100+ message chat: **98.5% of tokens were just rereading old history**

**Takeaway:** Every message is not just adding — it's multiplying.

---

## 3. Context Rot

- Happens as your session grows — model performance degrades as attention spreads across every token
- Symptoms: forgetting things, contradicting itself, editing files without reading them, vague responses
- **Retrieval accuracy:**
  - 92% at 256k tokens
  - 78% at 1 million tokens
- Even if you fill the window, the model gets measurably worse at using it
- Bad performance → worse token efficiency (e.g., 500k tokens to produce what 200k could have)

**Rule:** Avoid context rot at all costs. Don't let sessions run long.

---

## 4. Auto-Compaction — Why to Avoid It

- Fires automatically at **~95% of context window**
- You only keep **20–30% of original detail**
- Runs at the worst possible time (peak context rot = least intelligent model state)
- Analogy: packing for a trip 5 min before leaving vs. the night before

**Rule:** Never let auto-compaction trigger. Do manual compaction early.

---

## 5. Your Five Options After Every Claude Response

| Option | Command | When to Use |
|---|---|---|
| Continue | (just reply) | Fine for short early sessions |
| Rewind | `/re` or double-tap Escape | Claude did something wrong — drop failed attempts |
| Clear | `/clear` | Starting a new task entirely |
| Compact | `/compact` | Summarize and replace history with summary |
| Sub-agent | explicit prompt | Delegate isolated research/work to fresh context |

---

## 6. `/re` — Rewind (Anthropic's #1 Recommended Habit)

- Jump back to any previous message; everything after it is dropped
- Keeps context clean — failed attempts, broken code, wrong approaches stop polluting future responses
- Inside `/re` menu: **"Summarize from here"** option — creates a handoff note from Claude's future self to its past self

**Use it when:** Claude does something wrong instead of saying "that didn't work, try again."

---

## 7. Manual Compaction Strategy (Preferred Over `/compact`)

**Creator's personal workflow:**
1. When approaching ~120k tokens (12% of 1M window), say:
   > *"Give me a full summary of everything we've done and the current status of what we're about to do next."*
2. Copy that summary
3. Run `/clear`
4. Paste the summary in and keep going

- Feels like you never reset because all context is preserved in the summary
- Store data externally: tracking sheets, activity logs, task lists, decision logs — so resets are painless
- Analogy: closing browser tabs but keeping bookmarks

---

## 8. `/session-handoff` Skill (Custom Skill — Get from Free Community)

- Creator built a custom skill that automates the manual compaction workflow
- Type `/session-handoff` in a long session
- Output includes:
  - Where it started, decisions locked, what shipped
  - Key files for the next session
  - Running state, deferred/open questions
  - "Pick up from here" summary
- Copy output → `/clear` → paste → fresh context, fully oriented

---

## 9. Sub-Agents

- Each sub-agent gets its own **fresh context window**
- Does its own work, research, synthesis — sends back only the result
- You don't waste your main session's context on the research process
- Explicit trigger phrases:
  - *"Spin up a sub-agent to verify this."*
  - *"Spin up a sub-agent to review the codebase and summarize."*
  - *"Spin up a sub-agent using Haiku to summarize this."* (cheaper model for simple tasks)

**Key:** Delegate the right tasks — ones that are isolated and produce a usable output.

---

## 10. Session Limit — Watch It Constantly

- In the desktop app, the session limit is visible — watch it at all times
- If possible, keep it on a second monitor
- **Nearing the end of session:** Take a break. Don't start heavy work.
- **50%+ remaining + reset in <1 hr:** Abuse it. Spin up agent teams. Tackle heavy codebases. Make it hit the limit.

---

## 11. Convert Files to Markdown Before Giving to Claude

| Format | Token Reduction |
|---|---|
| HTML → Markdown | ~90% fewer tokens |
| PDF → Markdown | ~65–70% fewer tokens |
| DOCX → Markdown | ~33% fewer tokens |

- A 40-page PDF ≈ same space as a 130-page markdown file
- Tool: **Dockling** (or similar) — converts in seconds
- PDFs/DOCX/HTML carry layout/metadata/formatting noise the model doesn't need; it only needs the text

**Rule:** If it's text-based, convert it. Only use native format if you need OCR/vision.

---

## 12. `/btw` — Side Questions Without Polluting Context

- Opens a quick overlay for questions that **don't enter conversation history**
- Use when deep in a project and need a quick clarifying question
- Command: `/btw` — type your question — context stays clean

---

## 13. Plan Mode — Start Every Session Here

- Boris Cherny (creator of Claude Code) starts **every single session** in plan mode
- Tokens spent upfront on a clear plan = fewer correction tokens later
- Net cheaper in total even though you spend more at the start
- **Workflow:**
  1. Enter plan mode
  2. Get the plan right
  3. Let Claude one-shot the implementation

- Recommended tools: Ultra Plan, Superpowers (see linked videos)

---

## 14. CLAUDE.md Discipline

- Loads **every single session** — bloat here = paid bloat every conversation
- **Keep it under 200 lines / ~2,000 tokens**
- Only put in what Claude actively needs to do the job
- Move specialized instructions to **context files or skills** that load on demand
- Use **`.claudeignore`** to exclude folders/files Claude shouldn't read (huge win on large repos)

---

## 15. Output Tokens vs. Input Tokens

- Output tokens cost **more** than input tokens
- Telling Claude "be concise" doesn't move the needle much — most output tokens are hidden (file writes, tool calls, etc.)
- "Caveman mode" plugins tested — didn't save as much as people expected
- Real savings come from **context management**, not output brevity

---

## 16. Token Dashboard (Free Repo — Get from Community)

- Creator built a dashboard to see:
  - Sessions, turns, input tokens, output tokens, cache read, cache create
  - By model, by project, by tool
  - Last 7 or 30 days
  - Which prompts used the most tokens
  - Which files were opened most (e.g., "this file opened 181 times")
  - Which bash commands ran most often
- Use it to identify wasteful patterns you're not noticing
- Setup: Get the GitHub URL from the free school community → give it to Claude Code → say "help me set this up"

---

## 17. The 120k Token Rule

- Creator's personal rule for Opus + 1M context: **never go above ~120k tokens (~12%)**
- History: when context was 200k, he always compacted at ~60% = 120k — kept that as the baseline
- Not a hard technical limit — just a discipline habit
- If mid-output, finish the run, then reset
- **Prime time:** First 0–20% of session — model is freshest, CLAUDE.md is freshest, performance is peak

---

## 18. Session Chaining for Big Projects

Break large projects into specialized sessions:

1. **Discovery session** — Claude reads PDFs, codebase, gives summary doc
2. **Planning session** — reads summary doc, creates a plan
3. **Execution session** — reads finished plan, implements

- Each session has a single specialized task
- Like an assembly line — no session tries to do everything

---

## 19. 1M Token Window — The Right Mindset

- 1M is **insurance**, not a goal to fill
- Bigger window = more room for context rot, more distraction, worse output
- Just because the progress bar is at 50% doesn't mean keep going
- Recommendation for beginners: **start with 200k context window** — learn discipline first, graduate to 1M only if you need it
- More space invites worse habits

---

## 20. Third-Party Token Reduction Repos (10 Options)

> Don't install all 10. Pick 2–3 based on your workflow. Feed them to Claude Code and ask which fits your project.

| Repo | What It Does |
|---|---|
| Rust Token Killer | CLI proxy — filters terminal output before it hits context |
| Context Mode | Sandboxes raw tool output into SQLite instead of dumping to context |
| Code Review Graph | (graph-based code review optimization) |
| Token Savior | (token reduction framework) |
| Caveman Plugin | Makes Claude respond like a caveman (minimal words) |
| Claude Token Efficient | One CLAUDE.md file that keeps responses terse |
| Token Optimizer MCP | MCP server for token optimization |
| Claude Token Optimizer | Another token optimizer |
| Claude Context | Context management framework |

**Best approach:** Give Claude Code all the repo URLs and ask: *"Based on this specific project and its goals, which 2–3 of these would help the most and why?"*

> Tweet with all 10 repos linked in video description.

---

## 21. When Claude Goes Off the Rails

- If Claude feels repetitive or confused — even if not near context rot territory
- Just `/clear` or open a new session
- Don't fight it — a fresh session is almost always the right call

---

## Quick Reference — Commands

| Command | What It Does |
|---|---|
| `/context` | Check current token usage (run on fresh session to see baseline) |
| `/re` | Rewind to previous message — drop everything after it |
| `/clear` | Wipe the session, start fresh |
| `/compact` | Summarize session, replace history with summary |
| `/btw` | Ask a side question without adding it to context history |
| `/session-handoff` | (Custom skill) Generate a handoff summary for clean restart |
| Double-tap Escape | Open the rewind menu |

---

## Key Stats to Remember

- **98.5%** of tokens in a 100+ message chat = rereading old history
- Retrieval accuracy: **92%** at 256k → **78%** at 1M tokens
- One dev: $345/mo → $42,000/mo with bad context habits, **zero quality improvement**
- Thinking depth drops **67%** as sessions get longer
- "Edit without reading" behavior: **6%** early sessions → **34%** long sessions

---

## Habit Priority Order (Start Here)

1. Check `/context` on every fresh session
2. Start every session in **plan mode**
3. Use `/re` any time Claude does something wrong
4. Set a personal token ceiling (e.g., 120k) and reset before hitting it
5. Store progress externally (task lists, decision logs, tracker sheets)
6. Keep CLAUDE.md under 200 lines
7. Convert files to markdown before feeding to Claude
8. Use sub-agents for isolated research tasks
9. Watch the session limit bar — be strategic about when you burn tokens
10. Open a new session whenever something feels off
