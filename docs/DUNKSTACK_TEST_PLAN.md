# DunkStack Test & Development Plan

> **Author**: Human + Claude session, March 2026
> **Status**: Active — Phase 1
> **Purpose**: Hand this document to any agent session so they understand what we're building, why, and what to do next.

---

## The Vision (Read This First)

DunkStack is a **file-based context management system** for AI coding agents. Instead of stuffing everything into the chat stream (which burns context tokens), agents read and write to structured files in a `.agent/` directory. The chat stream is for 1-sentence status updates only.

### Why This Matters — Three Hypotheses We're Testing

1. **Sharper agents** — By offloading memory to files, the agent's active context stays focused on the current task. Hypothesis: 20-40% improvement in output quality vs. chat-only agents.

2. **Longer effective context** — The agent's "memory" lives in files, not in the conversation history. It can work across sessions by reading `bridge.md` and `working_memory.md`. Hypothesis: Effective context extends 20-40% beyond the model's raw context window.

3. **Cheaper API calls** — The chat stream carries almost nothing (just status updates). All the heavy content lives in files the agent reads on demand. Less tokens in the conversation = lower cost per session.

4. **Multi-agent communication** — This is the big one. If agents read/write to shared files, multiple agents can collaborate without any of them needing to hold the full project in their own context. Agent A writes findings to a file, Agent B reads it. No chat-to-chat bridging, no token waste. This enables teams of specialized agents that would be impossible with chat-only architectures.

### The Products That Come From This

- **DunkStack Engine** — The file-based agent system. This is what we're testing now.
- **PRD Maker (Agent OS)** — A standalone SaaS product that creates perfect PRDs through a multi-stage interactive workflow. Currently ~60-70% built inside AutoForge. Will be extracted, decoupled, and finished as its own product. Goes everywhere — AutoForge, DunkStack, any tool. Potential $10M-$50M SaaS business.
- **DunkStack + PRD Maker** — Once both work independently, the PRD Maker feeds specs into DunkStack's file system and agents build from them.

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

### Phase 1: Test One Agent (CURRENT PHASE)

**Goal**: Prove the file-based system works with a single agent.

**What to test**:
1. Start a DunkStack agent session on a registered project
2. Feed it a PRD through the walkie-talkie panel (paste directly — don't use Agent OS)
3. Verify the agent reads `from_human.md`, processes the PRD, and writes responses to `to_human.md`
4. Verify `working_memory.md` gets updated every ~3 turns
5. Verify the agent stays focused (doesn't dump long explanations into chat)
6. Verify the agent can actually build code based on the PRD
7. Kill the session, restart it, verify `bridge.md` → `working_memory.md` handoff works (session continuity)

**What we're measuring**:
- Does the agent stay on task better than a regular chat-based agent?
- Does context usage feel lower? (Check the ContextGauge)
- Does session handoff actually work? (Can it resume where it left off?)
- Does the code output quality match or beat a standard agent session?

**Success criteria**: The agent reads the PRD, builds features from it, communicates through files, and can resume after a session restart. If this works, Phase 2.

**Failure mode**: If the agent ignores the file system and dumps everything into chat, or can't resume sessions, or produces worse code than a normal agent — we troubleshoot. If we can't fix it after genuine effort, the single-agent file system hypothesis is invalidated, but the file architecture still has value for multi-agent communication (Phase 3).

---

### Phase 2: Optimize the Single Agent

**Goal**: Tune the system based on Phase 1 findings.

**Possible optimizations**:
- Adjust the system prompt (`system_prompt.md`) if the agent isn't following file protocols
- Tune safety thresholds in `config.yml` (when to warn, when to handoff)
- Adjust how often `working_memory.md` gets updated
- Improve the bootstrap message if the agent is missing context on startup
- Refine the `bridge.md` format for better session continuity

**Success criteria**: Consistent, reliable single-agent behavior across multiple test sessions with different PRDs.

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

**This is the proof point for the file system architecture.** If three agents can do it, the protocol works. The question then becomes scaling it.

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
