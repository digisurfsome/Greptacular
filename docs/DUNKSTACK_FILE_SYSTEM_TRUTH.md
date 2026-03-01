# DunkStack File System - Architecture Truth Document

> **Purpose**: The single source of truth for how DunkStack's file-based agent system works.
> If an agent breaks this system, restore from this document. Every agent session should
> be able to reconstruct the correct behavior from this file alone.

---

## The Big Picture (30-Second Version)

DunkStack agents communicate through **files**, not chat. The agent reads human
messages from a file, writes its responses to a file, and tracks its own state in
files. The chat stream is for **1-sentence status updates only** — all real content
lives in `.agent/`.

```
Human writes to:    .agent/comms/from_human.md  (via walkie-talkie panel)
Agent writes to:    .agent/comms/to_human.md    (via Write tool)
Agent's brain:      .agent/working_memory.md    (updated every 3 turns)
Session handoff:    .agent/bridge.md            (read on startup, then cleared)
File map:           .agent/index.md             (agent maintains this)
```

---

## Directory Structure

```
project-root/
  .agent/                          ← Agent's entire filing cabinet
    index.md                       ← Table of contents (agent maintains)
    system_prompt.md               ← Operating protocol (loaded into system prompt)
    working_memory.md              ← Agent's current state and task
    bridge.md                      ← Session continuity (temporary)

    comms/                         ← Two-way walkie-talkie
      from_human.md                ← Human → Agent (append-only, agent reads only)
      to_human.md                  ← Agent → Human (append-only, agent writes)
      control.md                   ← Mode signal: idle | continue | autopilot

    knowledge/                     ← Agent-created knowledge files
      [topic].md                   ← One file per domain (created as needed)

    output/                        ← Completed deliverables
      [deliverable].md             ← Work products (implementation plans, etc.)

    progress/                      ← Activity tracking
      build_log.md                 ← Append-only log of what was built and when

    settings/                      ← Configuration
      config.yml                   ← Safety thresholds, mode, Developer's Choice biases

    product/                       ← Product context (vision, users, constraints)
    specs/                         ← Feature specifications
    intake/                        ← Raw intake documents
    analytics/                     ← Decision tracking
      reports/                     ← Analytics reports

  agent-os/                        ← Shared standards (not per-agent)
    standards/                     ← Architecture, coding, UI/UX, security standards
```

---

## File Descriptions (One-Liner Each)

| File | Purpose |
|------|---------|
| `index.md` | Master map of every file — agent reads this FIRST every session |
| `system_prompt.md` | The operating protocol that gets loaded into the agent's system prompt |
| `working_memory.md` | Agent's current task, what was just done, what to do next, open questions |
| `bridge.md` | Saves state when a session ends so the next session can resume seamlessly |
| `comms/from_human.md` | Human's messages to the agent — timestamped, append-only, agent never modifies |
| `comms/to_human.md` | Agent's messages to the human — timestamped, append-only |
| `comms/control.md` | Session mode signal: `idle` (waiting), `continue` (keep going), `autopilot` (full auto) |
| `knowledge/[topic].md` | Agent-created reference files for specific topics it's learned about |
| `output/[name].md` | Completed work products (plans, analyses, code docs) |
| `progress/build_log.md` | Chronological log of builds, decisions, and outcomes |
| `settings/config.yml` | Tunable settings: safety thresholds, token budgets, Developer's Choice biases |

---

## Message Flow Diagrams

### Startup Flow (Agent Boots Up)

```
[User clicks Start Agent in UI]
        |
        v
WebSocket: {"type": "start_agent", ...}
        |
        v
Server creates DunkStackChatSession
        |
        v
session.start()  →  Creates Claude SDK client
                     Loads system_prompt.md into system prompt
                     Sets up security hooks
        |
        v
session.bootstrap()  →  Sends startup message to agent:
                         "Read .agent/index.md, working_memory.md,
                          bridge.md, from_human.md, control.md"
        |
        v
Agent reads all 5 files  →  Knows its state, sees human messages
        |
        v
Agent writes greeting to .agent/comms/to_human.md
        |
        v
Agent responds in chat: "Session started. See comms/to_human.md"
        |
        v
UI shows greeting in walkie-talkie panel (reads to_human.md)
```

### Human Sends Message (Walkie-Talkie Flow)

```
[Human types in walkie-talkie panel and hits Send]
        |
        v
REST: POST /api/dunkstack/comms/from-human
      {"content": "Here's my PRD...", "title": "PRD Upload"}
        |
        v
Server appends to .agent/comms/from_human.md:
  ## [2026-03-01 14:30] PRD Upload
  Here's my PRD...
        |
        v
Server broadcasts to UI: {"type": "comms_update", ...}
        |
        +--- Is there a running agent session? ---+
        |                                          |
       YES                                        NO
        |                                          |
        v                                     (Message waits
Server sends nudge to agent:                   in file until
  "New message in from_human.md at 14:30.      next startup)
   Re-read it now."
        |
        v
Agent re-reads .agent/comms/from_human.md
        |
        v
Agent processes the new message
        |
        v
Agent writes response to .agent/comms/to_human.md
        |
        v
Agent responds in chat: "Response posted. See comms/to_human.md"
```

### Agent Sends Message (Outbound Flow)

```
[Agent needs to tell human something]
        |
        v
Agent uses Write tool to APPEND to .agent/comms/to_human.md:
  ## [2026-03-01 14:35] Status - Analysis Complete
  I've finished analyzing the PRD. Key findings:
  - 12 features identified
  - 3 need clarification
  See .agent/output/prd_analysis.md for details.
        |
        v
Agent responds in chat: "Analysis complete. See comms/to_human.md"
        |
        v
UI polls or receives broadcast, shows message in walkie-talkie panel
```

### Session End / Handoff Flow

```
[Agent reaches context limit OR human stops agent]
        |
        v
Agent writes to .agent/bridge.md:
  - Current task
  - Progress so far
  - Next steps
  - Open questions
        |
        v
Agent updates .agent/working_memory.md with final state
        |
        v
Session closes
        |
        v
[Next session starts]
        |
        v
New agent reads bridge.md → incorporates context → deletes bridge.md
        |
        v
Reads working_memory.md → knows exactly where to resume
```

---

## The Three Communication Channels

### 1. Walkie-Talkie (File-Based) — PRIMARY
- **Human → Agent**: `from_human.md` via REST API / UI panel
- **Agent → Human**: `to_human.md` via Write tool
- **Format**: Timestamped markdown entries with `## [timestamp] Title` headers
- **Rule**: ALL substantive communication goes here

### 2. Chat Stream (WebSocket) — STATUS ONLY
- Agent's chat responses are limited to 1-2 sentences
- Used ONLY for: "Done. See [file]" or "Question posted. See comms/to_human.md"
- NEVER for explanations, code, analysis, or anything >3 sentences

### 3. Control Signal — MODE SWITCHING
- `comms/control.md` contains: `mode: idle | continue | autopilot`
- `idle` = agent waiting for human
- `continue` = human says keep going
- `autopilot` = agent runs autonomously until done

---

## Code Locations (Source of Truth)

| Component | File | Lines |
|-----------|------|-------|
| System prompt generator | `server/services/dunkstack_chat_session.py` | `get_dunkstack_system_prompt()` |
| Chat session (SDK client) | `server/services/dunkstack_chat_session.py` | `DunkStackChatSession` class |
| Bootstrap message | `server/services/dunkstack_chat_session.py` | `bootstrap()` method |
| REST endpoints (comms, control) | `server/routers/dunkstack.py` | Router endpoints |
| WebSocket handler | `server/routers/dunkstack.py` | `dunkstack_websocket()` |
| Message forwarding | `server/routers/dunkstack.py` | `write_from_human()` |
| File utilities | `server/services/agent_os_file_utils.py` | `AgentOSFileUtils` class |
| Universal templates | `server/templates/agent-os/universal/` | 9 template files |
| Template copier | `server/services/agent_os_file_utils.py` | `copy_universal_templates()` |

---

## Template System

When a new project is created, 9 universal template files are automatically
copied into `.agent/`. These files are NEVER overwritten if they already exist.

**Template source**: `server/templates/agent-os/universal/`

| Template | Destination |
|----------|-------------|
| `system_prompt.md` | `.agent/system_prompt.md` |
| `index.md` | `.agent/index.md` |
| `working_memory.md` | `.agent/working_memory.md` |
| `bridge.md` | `.agent/bridge.md` |
| `comms/to_human.md` | `.agent/comms/to_human.md` |
| `comms/from_human.md` | `.agent/comms/from_human.md` |
| `comms/control.md` | `.agent/comms/control.md` |
| `settings/config.yml` | `.agent/settings/config.yml` |
| `progress/build_log.md` | `.agent/progress/build_log.md` |

Additionally, standard templates are copied to `agent-os/standards/` and
product templates to `.agent/product/`.

---

## Safety Thresholds (config.yml)

```yaml
safety:
  warning_threshold_pct: 45      # Agent gets warned about context usage
  handoff_threshold_pct: 47.5    # Agent must stop coding and write handoff
  hard_stop_threshold_pct: 50    # Session is killed
  model_limit: 200000            # Context window size in tokens
```

---

## Rules That Must Never Be Broken

1. **Agent NEVER writes long responses in chat.** 3+ sentences = write to a file.
2. **Agent ALWAYS reads from_human.md every turn.** Not just on startup.
3. **Agent ALWAYS writes responses to to_human.md.** Not in chat.
4. **from_human.md is READ-ONLY for the agent.** Agent never modifies it.
5. **to_human.md is APPEND-ONLY.** Agent never overwrites previous entries.
6. **index.md is the source of truth** for what files exist. Agent maintains it.
7. **working_memory.md is updated every 3 turns** with current state.
8. **bridge.md is temporary.** Read on startup, then cleared.
9. **Templates never overwrite existing files.** Only copy if missing.
10. **REST from-human endpoint forwards to running agents.** Not just writes to file.

---

## Recovery Checklist

If the DunkStack file system is broken, verify these in order:

- [ ] `.agent/` directory exists with all subdirectories
- [ ] `system_prompt.md` contains the file-based operating protocol
- [ ] `index.md` lists all existing files
- [ ] `comms/from_human.md` exists and has the correct header
- [ ] `comms/to_human.md` exists and has the correct header
- [ ] `comms/control.md` exists with `mode: idle`
- [ ] `working_memory.md` exists with current state
- [ ] `settings/config.yml` exists with valid YAML
- [ ] `get_dunkstack_system_prompt()` loads `system_prompt.md` from the working directory
- [ ] `bootstrap()` sends the file-reading instructions on startup
- [ ] `write_from_human()` forwards messages to active agent sessions
- [ ] Template files exist in `server/templates/agent-os/universal/`
