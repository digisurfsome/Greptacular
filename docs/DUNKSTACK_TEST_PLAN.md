# DunkStack Test & Development Plan

> **Author**: Human + Claude session, March 2026
> **Status**: Active — Phase 1
> **Purpose**: Hand this document to any agent session so they understand what we're building, why, and what to do next.

---

## The Vision (Read This First)

DunkStack is a **file-based context management system** for AI coding agents. Instead of stuffing everything into the chat stream (which burns context tokens), agents read and write to structured files in a `.agent/` directory. The chat stream is for 1-sentence status updates only.

### The Original Idea — How This Started

The original vision was simple: **use the million-token context model to build entire applications in one shot, with one agent, without session handoffs.** One model, one session, reads the PRD, codes the whole thing. No teaching a second agent what the first one did. No degradation from context switching.

The problem: a million-token session building an entire app would cost $40-$50+ in API calls at current rates. That's too expensive for most use cases.

Then the key insight hit: **if the agent communicates through files instead of the chat stream, the conversation history stays tiny.** The chat stream only carries 1-sentence status updates. All the real content — PRDs, plans, code context, decisions — lives in files that the agent reads via tool use. The conversation tokens (which are the expensive part, since they compound every turn) stay minimal.

One idea turned into **four benefits**:

### The Four Benefits We're Testing

1. **Cheaper API calls (~50% cost reduction)** — By moving substantive content out of the chat stream and into files, the conversation token count stays flat instead of growing every turn. In a normal agent session, every message includes the full conversation history. In DunkStack, the history is just a series of "Done. See file X." messages. The tool-use tokens (reading/writing files) still cost money, so the net savings is estimated around 50%, not 70-80%. But 50% off a $40 build is $20 — that adds up fast.

2. **Sharper agents (sustained quality over long sessions)** — In a normal agent, quality degrades as context fills up. The agent is trying to hold the entire conversation, all the code it wrote, all the decisions it made, in active context. By session midpoint, it's swimming in noise. DunkStack agents offload memory to files and only load what's relevant to the current task. Hypothesis: the agent stays sharper longer because its active context is always clean and focused. The first 10K tokens might look similar to a normal agent (neither has accumulated noise yet), but from 10K-30K tokens onward, the DunkStack agent should maintain quality while the normal agent starts to degrade.

3. **Longer effective context (20-40% extension)** — Because memory lives in files (`working_memory.md`, `bridge.md`, knowledge files), the agent's effective reach extends beyond its raw context window. A 200K model using DunkStack should perform like it has 240K-280K effective context. And with million-token models, this becomes even more dramatic — the agent could potentially sustain an entire large application build without running out of room.

4. **Multi-agent communication (the big unlock)** — This is where it gets transformative. If one agent can read/write files, any number of agents can. Agent A writes its analysis to a file, Agent B reads it. No chat-to-chat bridging, no central controller copying messages, no token waste. Each agent maintains its own clean context while sharing knowledge through the file system. This enables specialized agent teams that would be impossible with chat-only architectures. And because each agent's chat stream is cheap (just status updates), running 3 or 5 or 20 agents becomes economically viable.

### The Endgame — What This Enables

**Single million-token agent**: One agent, one session, builds an entire application from a PRD. The file system keeps it sharp and cheap. Compare the cost and quality against a traditional multi-session agent doing the same thing.

**Three million-token agents as a team**: Architect + Builder + Reviewer, each with a million tokens. Effective context = 3 million tokens. They communicate through files. Could build a serious application in one coordinated session. Cost is ~50% of what it would be with chat-based agents.

**Million-token orchestrator + team of 200K sub-agents**: One big-brain manager that never loses the big picture, directing a team of 5-10 specialized 200K agents. The orchestrator plans, assigns, and reviews through files. The sub-agents execute, report back through files. The orchestrator can run the entire build from start to finish without losing context.

**5x5 million-token swarm**: For building something massive (think Amazon-scale). Five million-token models, all communicating through the shared file system, each owning a domain of the application. With proper orchestration logic for message routing and task assignment, this could build in days what currently takes months.

The key insight: **if three agents can communicate through files, there's no theoretical reason 25 can't.** The protocol is the same. The only thing that changes is the orchestration logic (who gets which messages, task assignment, conflict resolution). Phase 3 proves the protocol with three. Everything after that is scaling.

### The Products That Come From This

- **DunkStack Engine** — The file-based agent system. This is what we're testing now.
- **PRD Maker (Agent OS)** — A standalone SaaS product that creates perfect PRDs through a multi-stage interactive workflow. Currently ~60-70% built inside AutoForge. Will be extracted, decoupled, and finished as its own product. Goes everywhere — AutoForge, DunkStack, any tool. Potential $10M-$50M SaaS business.
- **DunkStack + PRD Maker** — Once both work independently, the PRD Maker feeds specs into DunkStack's file system and agents build from them.
- **DunkStack Multi-Agent Platform** — The swarm system. Patentable technology. If companies adopt file-based multi-agent communication, this is a level or two above current agent technology.

---

## Current State of the Code

### What's Built and Clean
- All DunkStack backend services (`dunkstack_session.py`, `dunkstack_chat_session.py`, `dunkstack.py` router)
- All DunkStack UI components (CommsChat, ContextGauge, SafetyPanel, AgentView, GuidePanel, PreviewPanel)
- `useDunkStack.ts` React hooks
- The `.agent/` file system architecture (templates, file utilities)
- File-based comms protocol (from_human.md, to_human.md, control.md, working_memory.md, bridge.md)

### What's Tangled (Known — Fix Later)
- `DunkStackPage.tsx` imports 7 Agent OS (PRD Maker) components and 4 `useAgentOS` hooks — the PRD Maker is embedded as a view mode inside DunkStack's main page
- `agent_os_handoff.py` bridges Agent OS output into AutoForge's `features.db` — this is the pipe connecting the systems
- DunkStack sidebar uses `useProjects()` from AutoForge to show feature stats

### Why We're NOT Fixing the Tangle Right Now
The tangle is in the **PRD Maker integration**, not in the **DunkStack engine**. We can test the engine by simply feeding it a PRD directly (paste it into the walkie-talkie / from_human.md). We don't need to use the embedded PRD Maker to test the core engine. The PRD Maker decoupling is Phase 4 work.

---

## The Plan — Four Phases

### Phase 1: Test One Agent — 200K Model (CURRENT PHASE)

**Goal**: Prove the file-based system works with a single agent using the standard 200K context model.

**Step 1a — Simple coding task**:
1. Start a DunkStack agent session on a registered project
2. Feed it a simple PRD through the walkie-talkie panel (paste directly — don't use Agent OS)
3. Verify the agent reads `from_human.md`, processes the PRD, and writes responses to `to_human.md`
4. Verify `working_memory.md` gets updated every ~3 turns
5. Verify the agent stays focused (doesn't dump long explanations into chat)
6. Verify the agent can actually build code based on the PRD
7. Kill the session, restart it, verify `bridge.md` → `working_memory.md` handoff works (session continuity)

**Step 1b — Bigger coding job**:
1. Give it a more complex PRD that pushes it toward the 100K token mark
2. Watch for quality degradation as context fills — does the file system keep it sharp?
3. Compare behavior at 50K tokens vs. 80K tokens vs. near-limit
4. This tests the "sustained sharpness" hypothesis at the 200K model level

**Step 1c — Million-token model, single-shot build**:
1. Switch to the million-token context model (1M tokens)
2. Give it a full application PRD — something that would normally require multiple sessions
3. See if one agent, one session, can build the entire thing
4. Measure: quality, cost, total tokens used, time to completion
5. Compare against what it would cost to build the same thing with a regular multi-session agent

### How to Measure Each Benefit

> **Full benchmark protocol with exact test tasks, PRDs, scoring criteria, and step-by-step procedures: [`docs/DUNKSTACK_BENCHMARK_PROTOCOL.md`](./DUNKSTACK_BENCHMARK_PROTOCOL.md)**

**Summary of the benchmark approach:**

**Sharpness → "Consistency Test"**: Give the agent 4 coding tasks of identical difficulty at 4 token checkpoints (10K, 35K, 65K, 90K). Each task has 8 specific requirements. Score each. If DunkStack stays at 7.5-8/8 while the control drops to 5-6.5/8 at CP-4, sharpness is proven.

**Effective Context → "Memory Recall Test"**: The PRD embeds 6 technical constraints (UTC timestamps, request_id in responses, specific error format, snake_case tables, input validation, pagination). At 50K, 75K, and 95K tokens, ask for new features WITHOUT reminding the agent of the constraints. Count how many constraints it still follows. DunkStack should remember them (they're in working_memory.md). Normal agent will have them buried 95K tokens back.

**Cost → Direct comparison**: Run the exact same build on both systems. Compare total tokens billed and USD cost. The ContextGauge already tracks this for DunkStack. Target: ~50% savings.

**Multi-agent comms → Phase 3**: Three agents collaborating through shared files. Success = they read each other's output and produce correct follow-up work.

**Success criteria for Phase 1**: The agent reads the PRD, builds features from it, communicates through files, and can resume after a session restart. If this works, Phase 2.

**Failure mode**: If the agent ignores the file system and dumps everything into chat, or can't resume sessions, or produces worse code than a normal agent — we troubleshoot. If we can't fix it after genuine effort, the single-agent file system hypothesis is invalidated, but the file architecture still has value for multi-agent communication (Phase 3).

**Even if the single-agent benefits are marginal**: The file system still enables multi-agent teams (Phase 3). Even if one agent isn't dramatically sharper or cheaper, the ability for multiple agents to communicate through files is a standalone breakthrough. So Phase 1 failure doesn't kill the project — it just narrows the value proposition to multi-agent use cases.

---

### Phase 2: Optimize the Single Agent

**Goal**: Tune the system based on Phase 1 findings.

**Possible optimizations**:
- Adjust the system prompt (`system_prompt.md`) if the agent isn't following file protocols
- Tune safety thresholds in `config.yml` (when to warn, when to handoff)
- Adjust how often `working_memory.md` gets updated
- Improve the bootstrap message if the agent is missing context on startup
- Refine the `bridge.md` format for better session continuity
- Optimize which files the agent reads on each turn (minimize unnecessary reads)

**Success criteria**: Consistent, reliable single-agent behavior across multiple test sessions with different PRDs. Cost and quality numbers from Phase 1 improve with tuning.

---

### Phase 3: Three-Agent Team

**Goal**: Prove that multiple agents can collaborate through the shared file system.

**Setup**:
- **Agent 1**: Architect — reads the PRD, creates implementation plans, writes them to `.agent/output/`
- **Agent 2**: Builder — reads the implementation plans, writes code
- **Agent 3**: Reviewer — reads the code, writes feedback to files, Builder reads feedback

**What this proves**:
- Agents can communicate through files without chat-to-chat bridging
- The effective context window triples (3 agents × 100K = 300K effective context)
- Specialized roles work better than one generalist agent
- The file system protocol scales beyond one agent

**What to build for this**:
- Multi-agent orchestration (who reads/writes which files, turn order or event-driven)
- Shared vs. per-agent file spaces within `.agent/`
- Message routing logic (how Agent 2 knows Agent 1 posted something new)

**Success criteria**: Three agents collaboratively build a feature that would be too complex for a single agent's context window. They communicate through files, not through a central controller copying messages between them.

**This is the proof point for the file system architecture.** If three agents can communicate through files, there's no reason 25 can't. The protocol is the same — only the orchestration logic changes. Phase 3 proves the protocol. Everything after is scaling.

---

### Phase 4: PRD Maker Decoupling & Multi-Agent Scaling

**Goal**: Extract the PRD Maker from AutoForge, finish building it as a standalone product, and connect it to DunkStack properly.

**PRD Maker work**:
- Remove Agent OS component imports from `DunkStackPage.tsx`
- Remove the `agent_os_handoff.py` bridge to AutoForge's `features.db`
- Build the PRD Maker as its own route/page/service that outputs to files, not to a database
- The PRD Maker's output should write directly to `.agent/specs/` or `.agent/intake/` — feeding DunkStack's file system natively
- Make it portable: works with DunkStack, works with AutoForge, works standalone as a SaaS product

**Multi-agent scaling work**:
- After proving 3 agents work in Phase 3, introduce 5+ agent swarms
- Build the orchestration layer for message routing, task assignment, and conflict resolution
- The file system is the foundation — the orchestration logic sits on top

---

## Future Agent Team Configurations (Post-Phase 3)

Once the three-agent team works, these configurations become possible:

| Configuration | Description | Use Case |
|---------------|-------------|----------|
| **1 × 1M agent** | Single million-token agent, one-shot build | Small-to-medium apps, rapid prototyping |
| **3 × 1M agents** | Architect + Builder + Reviewer, all million-token | Medium-to-large apps, high quality |
| **1 × 1M orchestrator + 5 × 200K sub-agents** | Big-brain manager directing specialized workers | Complex apps with distinct domains |
| **5 × 1M agents** | Full swarm, all million-token, all communicating | Enterprise-scale applications |
| **1 × 1M orchestrator + N × 200K workers** | Scalable team, orchestrator plans, workers execute | Variable-scale builds |

The optimal configuration depends on the project size. A small app doesn't need 5 million-token agents. A large app (think Amazon-scale) might want a 5×5 grid of million-token models all coordinating through the file system. The key is that the file system protocol makes ALL of these configurations possible, and the cost stays manageable because the chat streams are cheap.

**The patentable innovation**: File-based inter-agent communication that keeps each agent's conversation stream minimal while enabling unlimited agent collaboration. This is architecturally different from every current multi-agent framework (which either copies messages between agents or uses a central controller as a bottleneck).

---

## How to Feed a PRD to DunkStack (For Testing Now)

You do NOT need the Agent OS PRD Maker to test. Just:

1. Start the server (`./start_ui.sh` or `start_ui.bat`)
2. Navigate to `/#/dunkstack` in the browser
3. Select a registered project from the sidebar
4. Click "Start Agent"
5. Use the walkie-talkie panel (CommsChat) to paste your PRD directly
6. The system writes it to `.agent/comms/from_human.md` and nudges the agent
7. The agent reads it and starts working

Alternatively, you can manually write the PRD to `{project_dir}/.agent/comms/from_human.md` before starting the agent, and it will pick it up on bootstrap.

---

## Key Files Reference

| What | Where |
|------|-------|
| Benchmark protocol (exact tests) | `docs/DUNKSTACK_BENCHMARK_PROTOCOL.md` |
| File system architecture | `docs/DUNKSTACK_FILE_SYSTEM_TRUTH.md` |
| Full operator's manual | `DUNKSTACK_MANUAL.md` |
| Backend session manager | `server/services/dunkstack_session.py` |
| Backend chat session | `server/services/dunkstack_chat_session.py` |
| Backend router | `server/routers/dunkstack.py` |
| File utilities | `server/services/agent_os_file_utils.py` |
| UI main page | `ui/src/pages/DunkStackPage.tsx` |
| UI hooks | `ui/src/hooks/useDunkStack.ts` |
| UI components | `ui/src/components/dunkstack/` |
| Agent templates | `server/templates/agent-os/universal/` |
| Contamination audit | This document, "Current State of the Code" section |

---

## Rules for Agents Working on This

1. **Do NOT touch the Agent OS / PRD Maker integration right now.** It's tangled but harmless if you don't use it. Phase 4 work.
2. **Do NOT import AutoForge feature system concepts** (features.db, Feature model, feature MCP) into DunkStack code.
3. **The file system is the source of truth** — not the chat stream, not a database.
4. **Test with a manually-provided PRD** — paste it into the walkie-talkie or write it to `from_human.md`.
5. **If something breaks**, check `docs/DUNKSTACK_FILE_SYSTEM_TRUTH.md` first — it has the recovery checklist.
6. **Shared infrastructure is fine** — `bash_security_hook`, `get_effective_sdk_env`, `~/.autoforge/` config path. These are utilities, not AutoForge logic.
