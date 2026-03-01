# PROVISIONAL PATENT APPLICATION

## United States Patent and Trademark Office
## Provisional Application for Patent

---

## TITLE OF THE INVENTION

**System and Method for Managing Artificial Intelligence Agent Context Windows Through Structured File-Based State Persistence, Output Redirection, and Multi-Agent Filesystem Communication**

---

## INVENTOR(S)

Name: [YOUR FULL LEGAL NAME]
Address: [YOUR FULL ADDRESS]
City, State, ZIP: [CITY, STATE, ZIP]
Country: USA
Citizenship: USA

---

## CORRESPONDENCE ADDRESS

[YOUR FULL ADDRESS OR PATENT ATTORNEY ADDRESS]

---

## FILING FEE

Micro Entity: $220 (as of 2026)
Small Entity: $440
Large Entity: $880

Note: Most individual inventors qualify as Micro Entity. See 37 CFR 1.29.

---

## CROSS-REFERENCE TO RELATED APPLICATIONS

None.

---

## FIELD OF THE INVENTION

The present invention relates generally to artificial intelligence systems, and more specifically to methods and systems for managing context window utilization in large language model (LLM)-based AI agents through structured file-based state persistence, output redirection, session continuity mechanisms, and multi-agent coordination via filesystem-based message routing.

---

## BACKGROUND OF THE INVENTION

### The Context Window Problem

Large language models (LLMs) such as Claude, GPT, and similar systems operate within a fixed "context window" — a maximum number of tokens (words and subwords) that the model can process in a single session. Current models offer context windows ranging from 128,000 to 1,000,000 tokens.

In conventional AI agent operation, the agent communicates through conversational API responses. Every instruction from the user, every response from the agent, every file read, every tool result, and every intermediate reasoning step accumulates in this context window. This creates a fundamental problem: **context window degradation**.

### Context Window Degradation

As the context window fills, the following degradation patterns emerge:

1. **Attention Dilution**: The model's attention mechanism must spread across an ever-growing history. Important instructions from early in the session receive diminishing attention weight as newer content accumulates.

2. **Output Quality Decline**: Empirically observed degradation begins at approximately 40-50% context utilization. The agent produces less precise code, misses requirements specified earlier in the conversation, and makes errors it would not have made at the beginning of the session.

3. **Cost Escalation**: Output tokens cost 3-5x more than input tokens in most LLM pricing models. Verbose conversational responses consume expensive output token budget while simultaneously degrading the context window.

4. **Session Termination**: When the context window fills completely, the session must end. All accumulated context — the agent's understanding of the project, decisions made, architectural patterns established — is lost unless manually reconstructed.

5. **Compaction Loss**: Some systems attempt automatic "compaction" (summarization of conversation history). However, compaction performed after-the-fact inevitably loses critical details because all information appears equally important in retrospect. Specific error messages, exact user requirements, nuanced architectural decisions, and critical edge cases are generalized or dropped entirely.

### Prior Art Limitations

Existing approaches to context management include:

- **Retrieval-Augmented Generation (RAG)**: Stores information in external databases and retrieves relevant chunks. However, RAG systems retrieve information reactively and do not address the fundamental problem of context window accumulation from the agent's own output.

- **Conversation Summarization**: Periodically summarizes conversation history to reduce token count. Loses critical details and nuance, particularly for technical development work.

- **Multi-Session Handoffs**: Starting new sessions and manually briefing the new session. Requires significant human labor and inevitably loses context.

- **Tool-Augmented Memory**: Providing the agent with memory tools to store and retrieve facts. These tools add to context window consumption and require the agent to make explicit decisions about what to remember.

None of these approaches address the core insight of the present invention: that **the agent's own conversational output is the primary driver of context window consumption**, and that redirecting this output from the conversational channel to structured persistent files fundamentally changes the utilization economics of the context window.

### The Multi-Agent Coordination Problem

As AI agent systems evolve from single-agent to multi-agent architectures — where multiple LLM-based agents collaborate on complex tasks — a second fundamental problem emerges: **inter-agent communication overhead**.

Existing multi-agent frameworks (such as CrewAI, AutoGen, LangGraph, and similar systems) coordinate agents through one or more of the following mechanisms:

- **API-Based Message Passing**: Agents communicate via API calls or function invocations. Each message consumes context window tokens in both the sending and receiving agent. Messages are ephemeral and lost on session restart.

- **Shared Memory Objects**: Agents read and write to in-memory data structures (dictionaries, queues, state machines). These exist only during runtime and are destroyed when the process terminates, providing no crash recovery or persistence.

- **Message Brokers**: External infrastructure (RabbitMQ, Kafka, Redis Pub/Sub) routes messages between agents. This introduces deployment complexity, requires additional infrastructure, and creates a single point of failure external to the agents themselves.

- **Hierarchical Orchestration**: A central orchestrator agent dispatches tasks to worker agents and collects results. All communication passes through the orchestrator, creating a bottleneck and requiring the orchestrator to consume context window tokens proportional to the total communication volume.

All of these approaches share common limitations: they consume context window capacity for coordination overhead, they lack persistence across crashes and session boundaries, they impose hierarchy constraints on communication topology, and they provide limited operator visibility into inter-agent communication. The human operator cannot easily observe, inject into, or modify communications between agents in real-time.

The present invention extends the file-based architecture described above to solve this multi-agent coordination problem: because each agent already maintains its state on the filesystem, the filesystem itself becomes the natural communication fabric between agents — requiring no additional infrastructure, providing automatic persistence, enabling hierarchy-independent addressing, and giving the human operator full read/write access to all inter-agent communications.

---

## SUMMARY OF THE INVENTION

The present invention provides a system and method for managing AI agent context windows through structured file-based state persistence. The invention comprises the following interconnected mechanisms:

1. **Output Redirection Protocol**: A method whereby the AI agent's substantive output — analysis, code, explanations, plans, and all work products — is redirected from the conversational API response channel to persistent structured files on the filesystem. The conversational channel is restricted to brief status signals of three sentences or fewer. This prevents the agent's own output from accumulating in the context window.

2. **Hierarchical File Protocol**: A structured directory of designated files that collectively serve as the agent's persistent memory independent of context window contents. The directory includes files for working state, decision history, change tracking, scope boundaries, and bidirectional human-agent communication.

3. **Selective Reading Strategy**: A method whereby the agent reads only targeted portions of its persistent files each turn, budgeted to a configurable token limit (default: 4,000 tokens per turn), rather than re-reading entire file contents. This further minimizes context window consumption while maintaining full access to all stored information.

4. **Bridge Mechanism for Session Continuity**: A method that captures the agent's complete working state to a structured file upon session termination and restores from that file upon session resumption, enabling continuity across session boundaries at minimal token cost (approximately 2,500-3,000 tokens per bridge cycle versus re-sending entire conversation history).

5. **Bidirectional File-Based Communication Protocol**: A method whereby both the human operator and the AI agent exchange detailed communications through designated files rather than through conversational messages. The human writes instructions to a designated input file; the agent writes responses and questions to a designated output file. This replaces the conventional pattern of conversational message exchange, dramatically reducing context window consumption from both directions.

6. **Tiered Context Safety System**: A monitoring system that tracks context window utilization and triggers progressive interventions at configurable thresholds — a warning notification at a first threshold (default: 45%), a handoff preparation trigger at a second threshold (default: 47.5%), and a hard session stop at a third threshold (default: 50%) — preventing the agent from operating in the degraded utilization range.

7. **Idle Engine for Session Persistence**: A holding pattern mechanism that keeps an API session alive at near-zero token cost after task completion, using tiered strategies ranging from zero-cost wait states to minimal heartbeat operations (~30 tokens per cycle), preserving the full context window for immediate reuse without incurring cold-start costs.

8. **Compaction Recovery Protocol**: A method whereby, if the underlying platform performs automatic context compaction (summarization), the agent immediately recovers by re-reading its persistent file state rather than relying on the degraded compacted conversation history. The files serve as the authoritative source of truth, rendering compaction events harmless.

9. **Real-Time Context Categorization**: A method that categorizes conversation content into prioritized buckets (Decisions, Requirements, Architecture, Code Changes, Bugs, Ideas, Context, Fluff) in real-time as messages are exchanged, enabling intelligent pre-compaction at configurable intervals and producing handoff packages that preserve critical information while discarding low-value content.

10. **Multi-Agent Filesystem Communication Protocol**: A method and system for coordinating multiple AI agents through filesystem-based message routing, wherein each agent is assigned a designated mailbox directory on the shared filesystem. Agents communicate by writing message files to other agents' mailbox directories and reading from their own. The filesystem acts as a persistent, zero-infrastructure message bus that enables hierarchy-independent addressing (any agent can message any other agent regardless of organizational position), automatic crash recovery (messages survive agent restarts because they are files), full operator visibility (the human can read all inter-agent communications), and operator injection (the human can write messages to any specific agent's mailbox to redirect, correct, or instruct individual agents mid-task).

11. **Agent Discovery and Registry Protocol**: A method whereby each agent registers its identity, capabilities, and mailbox location in a shared registry file on the filesystem. Other agents and the human operator can read this registry to discover available agents, their current status, and their communication endpoints, enabling dynamic swarm composition without hardcoded routing.

12. **Filesystem-Based Message Routing with Guaranteed Delivery**: A message protocol wherein each inter-agent message is written as an individual file with structured metadata (sender, recipient, timestamp, message type, priority, correlation identifier), enabling message ordering, threading, priority routing, and audit trails through standard filesystem operations. Messages transition through states (pending, read, acknowledged) via file renaming or relocation, providing guaranteed delivery semantics without a message broker.

The combined effect of mechanisms 1-9 is that the effective utilizable capacity of a given context window increases from approximately 50% (conventional operation) to approximately 85% (file-based operation), representing a 70% increase in effective working capacity using the same model at the same cost. Session persistence costs are reduced by approximately 6,000x compared to conventional cold-start session resumption.

The additional effect of mechanisms 10-12 is that multiple AI agents can coordinate on complex tasks using the same filesystem architecture already established for single-agent state persistence, requiring zero additional infrastructure, providing automatic persistence across crashes and session boundaries, and enabling human operators to observe and intervene in inter-agent communications in real-time — capabilities that no existing multi-agent framework provides through a unified filesystem-based approach.

---

## DETAILED DESCRIPTION OF THE INVENTION

### 1. System Architecture Overview

The invention operates as a layered architecture:

```
+---------------------------------------------------+
|              HUMAN INTERFACE                        |
|  Input Files > Communication Files > Notifications  |
+---------------------------------------------------+
|              PROCESS ENGINE                         |
|  Task Queue > Work Execution > Testing > Delivery   |
+---------------------------------------------------+
|          FILE-BASED CONTEXT MANAGEMENT              |
|  Index > Selective Read > Working Memory > Bridge   |
+---------------------------------------------------+
|              API LAYER                              |
|  Thin status channel (3 sentences maximum)          |
+---------------------------------------------------+
```

The critical innovation is the **File-Based Context Management** layer, which sits between the process engine (where the agent does work) and the API layer (where the agent communicates with the hosting platform). In conventional operation, the process engine and API layer are the same channel — the agent does work BY producing conversational output. In the present invention, these are separated: the agent does work by writing to files, and the API channel carries only minimal status signals.

### 2. The File Protocol Directory Structure

The invention specifies a structured directory (herein referred to as the "agent directory") with the following hierarchy:

```
.agent/
  index.md              Master navigation map of all files
  working_memory.md     Agent's current task, state, and active context
  bridge.md             Session continuity data (temporary)
  system_prompt.md      Core operating protocol instructions

  comms/                Bidirectional communication channels
    to_human.md         Agent-to-human messages (append-only)
    from_human.md       Human-to-agent messages (read-only for agent)
    control.md          Mode signals: idle, continue, or autopilot

  knowledge/            Persistent knowledge files (one per domain)
    [topic].md

  output/               Completed work products
    [deliverable].md

  progress/             Build tracking (append-only)
    build_log.md        Chronological record of actions and decisions

  settings/
    config.yml          Adjustable operational parameters
```

Each file has a specific designated role, access pattern (append-only, read-only, read-write), and update frequency. The agent is instructed to maintain this structure as its authoritative state.

### 3. Output Redirection Protocol

The core mechanism of the invention is the Output Redirection Protocol, which operates as follows:

**Rule**: Before generating ANY response longer than three sentences, the agent MUST redirect the content to the appropriate file and respond with only a status reference.

**Correct Operation Example**:
- Agent completes analysis
- Agent writes full analysis to `.agent/output/analysis.md` using filesystem write tool
- Agent responds in conversation: "Analysis complete. See .agent/output/analysis.md"
- Context window impact: ~20 tokens (status message only)

**Conventional Operation Comparison**:
- Agent completes analysis
- Agent writes full analysis into conversational response
- Context window impact: 500-5,000+ tokens (entire analysis content)

This redirection is enforced through explicit protocol instructions embedded in the agent's system prompt, with drift-detection patterns that identify when the agent begins producing verbose output and redirect it back to file-based operation.

**Drift Detection Patterns**:
The system monitors for specific conversational patterns that indicate the agent is reverting to verbose output mode:
- "Let me explain..." → Redirect to file
- "Here's what I found..." → Redirect to file
- "The code looks like..." → Redirect to file
- Any response exceeding the configured sentence limit → Redirect to file

### 4. Selective Reading Strategy

Rather than reading entire files each turn (which would consume context window capacity), the agent employs a budgeted selective reading strategy:

1. Read the master index file FIRST (~500 tokens) to determine what exists and where
2. For files under 50 lines, read the entire file
3. For files over 50 lines, read the heading structure first (first 20 lines), then read ONLY the specific section needed
4. Total file read budget per turn: configurable, default 4,000 tokens

This ensures the agent has access to ALL persistent information through its file structure while consuming minimal context window capacity per turn.

### 5. The Bridge Mechanism

The Bridge Mechanism provides session continuity at minimal token cost:

**Session Save Sequence** (triggered on session end, approaching timeout, or emergency disconnect):
1. Write complete working state to bridge.md: current task, progress percentage, active context references, next steps, and any critical state
2. Update working_memory.md with final state summary
3. Update index.md if new files were created during the session
4. Append session summary to progress/build_log.md
5. Respond briefly: "State saved. Safe to end session."

**Token Cost of Save**: ~800-1,200 output tokens

**Session Resume Sequence** (triggered on new session start):
1. Read index.md (~500 tokens) — learn what files exist
2. Read working_memory.md (~400 tokens) — recover current state
3. Read bridge.md (~500-800 tokens) — recover session-specific continuity data, then delete bridge.md
4. Read comms/from_human.md — check for any messages posted while agent was offline
5. Read comms/control.md — check operating mode
6. Resume work from the state described in working_memory.md

**Token Cost of Resume**: ~1,400-1,700 input tokens

**Total Bridge Cycle Cost**: ~2,500-3,000 tokens

**Comparison to Conventional Resume**: In conventional operation, resuming a session requires re-sending the ENTIRE conversation history. For a session with 200,000 tokens of accumulated history, this costs 200,000 input tokens just to "wake up" the agent. The Bridge Mechanism achieves equivalent continuity at 1.25-1.5% of this cost.

### 6. Bidirectional File-Based Communication

The invention replaces conversational message exchange with a file-based communication protocol:

**Human-to-Agent Channel** (`comms/from_human.md`):
- The human writes detailed instructions, requirements, and feedback to this file
- The agent reads this file (read-only access) at the start of each session and periodically during work
- Format: Timestamped entries with section headers
- The agent NEVER modifies this file

**Agent-to-Human Channel** (`comms/to_human.md`):
- The agent writes detailed questions, reports, and explanations to this file
- Append-only: new entries are appended, previous entries are never modified
- Format: Timestamped entries with category tags
- The human reads this file asynchronously

**Control Channel** (`comms/control.md`):
- Contains mode signals: idle (wait for input), continue (keep working), autopilot (work without checking in)
- Checked by the agent after idle cycles and at configurable intervals

This three-file communication system replaces what would conventionally be dozens or hundreds of conversational messages, each of which would accumulate in the context window. Instead, the agent reads the latest human input (~200-500 tokens) and the current mode signal (~10 tokens) per cycle.

### 7. Tiered Context Safety System

The invention includes a multi-tiered safety system that prevents the agent from operating in the degraded performance range:

**Tier 1 — Warning** (configurable, default 45% utilization):
- Agent receives a notification that context is approaching the safety boundary
- Agent begins prioritizing task completion over starting new work
- No interruption to current work

**Tier 2 — Handoff Preparation** (configurable, default 47.5% utilization):
- Agent stops accepting new coding tasks
- Agent writes comprehensive handoff state to bridge.md and working_memory.md
- Agent completes any in-progress operation to a safe stopping point

**Tier 3 — Hard Stop** (configurable, default 50% utilization):
- Session is terminated to prevent degraded operation
- If Tier 2 handoff preparation was completed, the next session can resume cleanly
- Optional: automated code review of work produced in the final session segment

The thresholds are configurable through the settings file (`config.yml`), allowing users to adjust based on their specific model, task complexity, and risk tolerance.

### 8. Idle Engine (Holding Pattern System)

When the agent completes a task and has no new work queued, instead of ending the API session (which incurs cold-start costs to resume), the system enters a holding pattern:

**Tiered Hold Strategies** (cheapest to most expensive):

| Tier | Strategy | Token Cost | Description |
|------|----------|-----------|-------------|
| T0 | Wait Pause | 0 tokens | Agent signals readiness and waits. Completely free. |
| T1 | Heartbeat Micro-Read | ~30 tokens | Read one line of a status file. Minimal cost to keep session alive. |
| T2 | Context Summary | ~200 tokens | Agent generates brief internal checkpoint. Useful as state snapshot. |
| T3 | Proactive Check | ~500 tokens | Agent performs lightweight validation on recent work. |

**Hold Loop Operation**:
1. Agent completes task
2. Agent enters wait state (T0, zero cost)
3. On timeout, performs heartbeat micro-read (T1, ~30 tokens)
4. Checks for new task signal in hold signal file
5. If no new task, returns to step 2
6. If new task found, exits hold and executes task with full context preserved
7. Emergency exit after configurable maximum cycles (default 50 cycles, ~4 hours at 5-minute intervals)

**Cost Comparison** (session with 300,000 tokens of accumulated context):

| Scenario | Cost to Resume |
|----------|---------------|
| Cold start (new API session) | 300K input tokens x $3/MTok = $0.90 |
| Holding pattern resume | ~50 tokens per cycle = $0.00015 |
| Wait pause (zero tokens) | $0.00 |

Over a workday with 20 task transitions: $18 in cold starts versus ~$0.003 in holding patterns — approximately a 6,000x cost reduction.

**External Task Injection**: A signal file mechanism allows external systems (user interfaces, scheduled jobs, other agents) to inject tasks into a holding agent by writing to a designated signal file. An empty signal file means "keep holding." Content in the signal file is interpreted as a new task. Deletion of the signal file triggers graceful session end.

### 9. Compaction Recovery Protocol

Modern LLM platforms may automatically "compact" (summarize) conversation history when it grows large. This compaction is destructive — it replaces detailed conversation history with an abbreviated summary, losing specifics.

The present invention renders compaction harmless:

1. If the agent detects a compaction event (conversation history appears shorter than expected, or context about previous work feels absent), it immediately executes the following recovery:
2. Read `.agent/index.md` — recover the complete file map
3. Read `.agent/working_memory.md` — recover current task and state
4. Read `.agent/comms/from_human.md` — recover any recent human input
5. Resume work from the file-described state

Because ALL substantive work product and state is stored in files (not in conversation history), the compacted conversation history is irrelevant. The files ARE the source of truth. The conversation history is merely a log of status messages, and losing it has no impact on the agent's ability to continue working.

This is a critical differentiator from conventional operation, where compaction causes the agent to lose understanding of the project, forget requirements, and produce errors.

### 10. Real-Time Context Categorization

Rather than attempting after-the-fact summarization (which treats all information as equally important), the invention categorizes conversation content in real-time as it occurs:

**Category Buckets with Priority Weights**:

| Category | Weight | Description |
|----------|--------|-------------|
| DECISIONS | 10 | Concrete decisions made by the user or agent |
| REQUIREMENTS | 9 | Explicit user requirements and specifications |
| BUGS_FOUND | 8 | Issues discovered, whether fixed or open |
| ARCHITECTURE | 7 | Technical decisions about system structure |
| CODE_CHANGES | 6 | Files modified, what changed, and why |
| IDEAS | 4 | Ideas mentioned but not yet implemented |
| CONTEXT | 3 | Background information explaining decisions |
| FLUFF | 0 | Pleasantries, tangents, non-substantive content |

**Categorization occurs after each message exchange** using one of:
- Rules-based classification using keyword and pattern matching (zero additional cost)
- Lightweight model classification using a smaller, cheaper model (~100 tokens per classification)
- Hybrid approach combining both methods

**Progressive Pre-Compaction**: Every 10% of context utilization, the categorized items are merged, deduplicated, and priority-scored. Items referenced multiple times receive a frequency boost. Items explicitly overridden by later decisions receive a penalty. By the time the context safety system triggers at 49%, the handoff package is 90% pre-built.

**Priority Scoring Algorithm**:
```
score = base_weight(category) x recency_factor x mention_count x override_penalty

where:
  base_weight: from category table above
  recency_factor: 1.0 for items in last 10% of conversation, decaying to 0.5 for oldest
  mention_count: multiplier for items referenced multiple times
  override_penalty: 0 if a later decision explicitly superseded this item
```

### 11. Effective Capacity Analysis

**Conventional AI Agent Operation** (200K context window):
- System prompt and tool definitions: ~16,000 tokens (permanent)
- Usable capacity: ~184,000 tokens
- Practical utilization before degradation: ~50% = ~92,000 working tokens
- Every agent response, file read, and user message accumulates in this space

**File-Based Operation** (200K context window, present invention):
- System prompt and tool definitions: ~16,000 tokens (permanent)
- File protocol overhead per turn: ~4,000-5,000 tokens (selective reads + brief status response)
- Usable capacity: ~184,000 tokens
- Practical utilization target: 85% = ~156,400 working tokens
- Agent responses do NOT accumulate (redirected to files)
- Only brief status messages (~20 tokens each) accumulate in conversation history

**Result**: 70% more effective working capacity from the same model at the same price.

**Scaling to 1M Context Window**:
- Conventional: ~500,000 usable tokens at 50% utilization
- File-based: ~850,000 usable tokens at 85% utilization
- Difference: 350,000 additional working tokens — the equivalent of an entire additional context window

### 12. Multi-Agent Filesystem Communication Architecture

The present invention extends the single-agent file-based architecture described in Sections 1-11 to a multi-agent system wherein two or more AI agents coordinate through the filesystem as a shared communication fabric.

#### 12.1 Architectural Principle

In a multi-agent configuration, each agent maintains its own `.agent/` directory as described in Section 2 (for its own state management, output redirection, and context window management). Additionally, a shared communication layer is established on the same filesystem:

```
project/
  .swarm/                           Shared multi-agent layer
    registry.yml                    Agent discovery registry

    mailboxes/                      Per-agent communication endpoints
      agent-alpha/
        inbox/                      Messages TO this agent
          msg_001_from_beta.md      Individual message files
          msg_002_from_human.md     Operator-injected message
        outbox/                     Messages FROM this agent (copies)
          msg_003_to_gamma.md
        status.yml                  Agent's current status and capabilities

      agent-beta/
        inbox/
        outbox/
        status.yml

      agent-gamma/
        inbox/
        outbox/
        status.yml

    broadcast/                      Messages to all agents
      announcement_001.md

    coordination/                   Shared coordination files
      task_board.md                 Shared task registry
      decisions_log.md              Cross-agent decision record
      conflicts.md                  Conflict detection and resolution log

  agent-alpha/
    .agent/                         Agent Alpha's private state (per Section 2)

  agent-beta/
    .agent/                         Agent Beta's private state

  agent-gamma/
    .agent/                         Agent Gamma's private state
```

The critical innovation is that the **same filesystem** that each agent already uses for its own state persistence (as described in Sections 1-11) also serves as the inter-agent communication channel. No additional infrastructure — no message brokers, no API gateways, no shared databases — is required. The filesystem IS the message bus.

#### 12.2 Separation of Concerns

The architecture maintains a clear separation between:

1. **Private Agent State** (`.agent/` directory per agent): Each agent's working memory, bridge files, knowledge, and output, as described in Sections 1-11. No other agent reads or writes to another agent's private `.agent/` directory.

2. **Shared Communication State** (`.swarm/` directory): The inter-agent communication layer where all agents and the human operator have designated read/write access patterns. This is the novel addition for multi-agent coordination.

This separation ensures that the single-agent context management benefits (output redirection, selective reading, bridge mechanism, etc.) are fully preserved even in a multi-agent configuration. Each agent manages its own context window using the single-agent protocol, and the multi-agent communication adds only minimal additional token overhead (reading one's inbox).

### 13. Agent Mailbox System and Message Protocol

#### 13.1 Mailbox Structure

Each agent is assigned a mailbox directory within `.swarm/mailboxes/` consisting of:

- **inbox/**: A directory where other agents (and the human operator) deposit message files intended for this agent. The agent reads from its own inbox at configurable intervals.
- **outbox/**: A directory where the agent keeps copies of messages it has sent to other agents. This provides an audit trail and enables replay in case of delivery failure.
- **status.yml**: A structured file declaring the agent's current state (idle, working, waiting, error), capabilities, current task, and availability for new work.

#### 13.2 Message File Format

Each inter-agent message is a structured file with the following format:

```yaml
---
id: msg_20260301_143022_alpha_to_beta_001
from: agent-alpha
to: agent-beta
timestamp: 2026-03-01T14:30:22Z
type: request | response | inform | delegate | escalate | acknowledge
priority: critical | high | normal | low
correlation_id: null | <id of message being replied to>
thread_id: null | <shared thread identifier>
status: pending | read | acknowledged
---

[Message body in markdown format]

The analysis of module X is complete. Key findings:

1. The authentication layer has a race condition in session validation
2. The database connection pool is undersized for the expected load
3. Recommend implementing connection retry logic before proceeding

Please review finding #1 before I proceed with the fix, as it may affect
your work on the user session manager.
```

The structured header enables:
- **Message ordering**: Timestamps provide natural ordering; filesystem creation time serves as backup
- **Threading**: Correlation and thread IDs enable multi-turn conversations between agents
- **Priority routing**: Agents can process high-priority messages first by reading file headers before full content
- **Audit trails**: All messages are persistent files, creating a complete communication history
- **State tracking**: Message status transitions (pending → read → acknowledged) are tracked through file metadata or header updates

#### 13.3 Message Lifecycle

Messages follow a defined lifecycle:

1. **Composition**: Sending agent writes message file to its own outbox/ (local copy)
2. **Delivery**: Sending agent copies the message file to the recipient's inbox/ directory
3. **Detection**: Receiving agent detects new files in its inbox/ during its next mailbox check cycle
4. **Reading**: Receiving agent reads the message, updating the status field to "read"
5. **Processing**: Receiving agent acts on the message content
6. **Acknowledgment**: If required by message type, receiving agent updates status to "acknowledged" or writes a response message back to the sender's inbox
7. **Archival**: Processed messages may be moved to an archive/ subdirectory to keep the inbox clean while preserving history

#### 13.4 Token Budget for Multi-Agent Communication

The mailbox check operation is designed to be lightweight:

- **Inbox scan**: List directory contents (~10-20 tokens for filesystem operation)
- **Message triage**: Read only the YAML headers of new messages (~50 tokens per message) to determine priority
- **Selective reading**: Read full content only for messages above the current priority threshold
- **Total budget per mailbox check cycle**: Configurable, default 500 tokens
- **Check frequency**: Configurable, default every 5 turns or upon explicit notification

This ensures that multi-agent communication does not undermine the context window efficiency gains described in Sections 1-11.

### 14. Hierarchy-Independent Message Routing

#### 14.1 The Topology Problem in Existing Systems

Conventional multi-agent frameworks impose communication topologies that constrain agent interaction:

- **Star topology**: All communication passes through a central orchestrator. If Agent A needs information from Agent C, the message must route through the orchestrator, doubling the communication cost and creating a bottleneck.
- **Chain topology**: Agents are organized in a pipeline. Agent A can only communicate with Agent B (its successor), not with Agent D (three steps away).
- **Tree topology**: Agents are organized hierarchically. Communication follows the tree structure — siblings cannot communicate directly without routing through their parent.

These topological constraints are artifacts of the communication mechanism (API calls, function invocations) rather than inherent requirements of the task being performed.

#### 14.2 Flat Addressing via Filesystem

The present invention implements flat addressing: **any agent can write a message to any other agent's inbox directory**, regardless of their organizational role, task assignment, or position in any logical hierarchy.

The routing mechanism is trivially simple:
1. Agent Alpha wants to send a message to Agent Gamma
2. Agent Alpha writes a message file to `.swarm/mailboxes/agent-gamma/inbox/`
3. Agent Gamma reads the file on its next mailbox check cycle

No routing table, no orchestrator relay, no API endpoint discovery. The filesystem path IS the address. If you know the agent's name, you know its mailbox location.

This enables communication patterns that are impossible or expensive in conventional systems:
- **Peer-to-peer**: Any agent communicates directly with any other agent
- **Broadcast**: An agent writes to `.swarm/broadcast/` to reach all agents simultaneously
- **Selective multicast**: An agent writes the same message to multiple specific agents' inboxes
- **Ad hoc collaboration**: Two agents can establish a direct communication thread without involving any orchestrator or modifying any routing configuration

#### 14.3 The Operator as a First-Class Participant

A distinctive feature of the filesystem-based approach is that the **human operator has the same communication primitives as the agents**. The operator can:

1. **Read any agent's inbox or outbox**: Full visibility into all inter-agent communications by browsing the `.swarm/mailboxes/` directory with standard filesystem tools (file manager, terminal, text editor)

2. **Write to any agent's inbox**: Inject instructions, corrections, or context to a specific agent by creating a message file in that agent's inbox directory. The message follows the same format as inter-agent messages, with `from: human-operator`

3. **Read the broadcast channel**: See all announcements and system-wide communications

4. **Write to the broadcast channel**: Send instructions to all agents simultaneously

5. **Modify an agent's status**: Update an agent's `status.yml` to change its availability, pause it, or redirect its task assignment

6. **Observe communication patterns**: By examining the outbox directories across agents, the operator can see the full communication graph — who is talking to whom, about what, and how frequently

This capability is particularly valuable for:
- **Debugging**: When a multi-agent system produces unexpected results, the operator can examine the exact communications that led to the outcome
- **Steering**: The operator can redirect individual agents mid-task without stopping the entire swarm
- **Conflict resolution**: When agents disagree (e.g., conflicting architectural decisions), the operator can observe the conflict in the communication files and inject a resolution
- **Quality control**: The operator can monitor the quality and relevance of inter-agent communications and intervene when communication patterns become unproductive

### 15. Crash Recovery and Session Boundary Handling in Multi-Agent Systems

#### 15.1 The Crash Recovery Advantage

Because all inter-agent messages are persistent files, the system provides automatic crash recovery without additional mechanisms:

1. **Agent crashes**: If Agent Beta crashes mid-task, unread messages remain in its inbox. When Agent Beta restarts and reads its bridge file (per Section 5), it also scans its inbox for pending messages and resumes communication from where it left off.

2. **System-wide restart**: If the entire system restarts, all agents recover via their individual bridge mechanisms AND resume inter-agent communications by scanning their inboxes. No messages are lost because they are files, not in-memory objects.

3. **Partial swarm operation**: If one agent in a multi-agent swarm is unavailable, other agents can continue depositing messages in the unavailable agent's inbox. When it comes back online, it processes the accumulated messages. This is analogous to email — the sender doesn't need the recipient to be online at the time of sending.

#### 15.2 Cross-Session Multi-Agent Continuity

The bridge mechanism described in Section 5 extends naturally to multi-agent scenarios. When an agent writes its bridge file on session termination, it includes:

- A summary of pending inter-agent communications (messages sent but not yet acknowledged)
- The correlation IDs of active conversation threads with other agents
- The current state of any collaborative tasks

On session resume, the agent reads its bridge file and its inbox, reconstructing both its private state and its position in all ongoing inter-agent conversations. This enables multi-agent projects that span days, weeks, or months of elapsed time, with agents coming online and offline at different times while maintaining coherent collaboration.

### 16. Security and Access Control in Multi-Agent Filesystem Communication

#### 16.1 Access Control Model

The filesystem-based communication architecture leverages standard filesystem permissions for access control:

- **Agent isolation**: Each agent's private `.agent/` directory is readable/writable only by that agent's process
- **Inbox write access**: An agent's inbox is writable by any authorized agent or the human operator, but is read-only for the owning agent (preventing self-messages that could cause loops)
- **Outbox read access**: An agent's outbox is readable by authorized agents and the operator for audit purposes, writable only by the owning agent
- **Broadcast access**: The broadcast directory is writable by any authorized agent or the operator, readable by all
- **Registry access**: The registry file is append-writable by agents (for registration) and read-writable by the operator (for administration)

#### 16.2 Message Validation

Agents validate incoming messages before processing:
- Verify the `from` field matches an agent listed in the registry
- Verify the message format conforms to the expected schema
- Reject messages from unknown or deregistered agents
- Rate-limit processing of messages from any single source to prevent flooding
- Log all rejected messages for operator review

---

## BRIEF DESCRIPTION OF THE DRAWINGS

**Figure 1**: System Architecture Diagram — Shows the layered architecture with Human Interface, Process Engine, File-Based Context Management, and API Layer, with arrows indicating data flow between layers.

**Figure 2**: Agent Directory Structure — Shows the hierarchical file structure of the .agent/ directory with all designated files and their access patterns (read-only, write-only, append-only, read-write).

**Figure 3**: Output Redirection Flow — Compares conventional operation (agent output → conversational response → context window accumulation) versus invented operation (agent output → persistent file → brief status to conversational response).

**Figure 4**: Bridge Mechanism Sequence Diagram — Shows the save sequence on session end and the restore sequence on session resume, with token costs annotated at each step.

**Figure 5**: Holding Pattern State Machine — Shows the tiered hold loop from T0 (zero-cost wait) through T1 (heartbeat micro-read) with transitions for new task arrival, budget exhaustion, and maximum cycle reached.

**Figure 6**: Context Window Utilization Comparison — Bar chart comparing conventional utilization (~50% effective) versus file-based utilization (~85% effective) for 200K and 1M context windows.

**Figure 7**: Tiered Context Safety System — Shows the three threshold tiers (warning at 45%, handoff at 47.5%, hard stop at 50%) with the actions triggered at each tier.

**Figure 8**: Bidirectional Communication Protocol — Shows the three-file communication system (from_human.md, to_human.md, control.md) with read/write access patterns for both human and agent.

**Figure 9**: Real-Time Context Categorization Flow — Shows message pairs being categorized into priority buckets in real-time, with progressive pre-compaction at 10% intervals.

**Figure 10**: Cost Comparison — Table comparing session resume costs: cold start ($0.90 for 300K context) versus holding pattern ($0.00015 per cycle) versus wait pause ($0.00).

**Figure 11**: Multi-Agent Filesystem Communication Architecture — Shows the shared `.swarm/` directory structure with per-agent mailbox directories (inbox, outbox, status), broadcast directory, coordination directory, and registry file. Shows arrows indicating message flow between agents through the filesystem.

**Figure 12**: Message Routing Flow — Sequence diagram showing Agent Alpha composing a message, writing it to Agent Beta's inbox directory, Agent Beta detecting the new file during a mailbox check cycle, reading the message, and writing an acknowledgment response to Agent Alpha's inbox. Also shows the human operator injecting a message to Agent Gamma's inbox in parallel.

**Figure 13**: Communication Topology Comparison — Side-by-side comparison of conventional multi-agent topologies (star through orchestrator, chain pipeline, tree hierarchy) versus the invented flat filesystem addressing where any agent can message any other agent directly. Shows how the filesystem-based approach eliminates routing bottlenecks and hierarchy constraints.

**Figure 14**: Crash Recovery in Multi-Agent Communication — Shows Agent Beta crashing while messages are pending in its inbox, the messages persisting as files on the filesystem, and Agent Beta recovering by scanning its inbox upon restart alongside reading its bridge file for private state recovery.

[NOTE TO INVENTOR: These figures should be created as simple diagrams before filing. Hand-drawn diagrams on plain white paper are acceptable for provisional applications. Each figure should be labeled and referenced in the text above.]

---

## CLAIMS

### Independent Claims

**Claim 1.** A method for extending the effective utilization of artificial intelligence context windows, the method comprising:

(a) configuring an AI agent to redirect all substantive output from an API response channel to persistent structured files on a filesystem, the API response channel being restricted to status messages not exceeding a configurable sentence limit;

(b) maintaining a hierarchical directory of designated files comprising at minimum: a master index file, a working memory file for agent state, a bridge file for session continuity, and a bidirectional communication channel comprising separate files for human-to-agent and agent-to-human messages;

(c) implementing a selective reading strategy wherein the agent reads a budgeted subset of its persistent files per operational turn, the budget being configurable in tokens, enabling access to all stored information while consuming minimal context window capacity;

(d) monitoring context window utilization and triggering progressive interventions at configurable thresholds to prevent operation in a degraded performance range.

**Claim 2.** A system for managing artificial intelligence agent sessions through file-based state persistence, the system comprising:

(a) a file protocol module that maintains a structured directory of persistent files serving as the agent's authoritative state, independent of conversation history;

(b) an output redirection module that intercepts agent output intended for conversational responses and writes said output to designated persistent files, replacing conversational output with abbreviated status references;

(c) a bridge module that captures agent working state to a bridge file upon session termination and restores agent state from said bridge file upon session resumption, enabling session continuity at a fraction of the token cost of re-sending conversation history;

(d) an idle engine module that maintains an active API session at near-zero token cost through a tiered holding pattern comprising at minimum a zero-cost wait state and a minimal-cost heartbeat operation;

(e) a context safety module that monitors context window utilization and enforces configurable threshold-based interventions comprising at minimum a warning tier, a handoff preparation tier, and a hard stop tier.

**Claim 3.** A computer-implemented method for reducing artificial intelligence API costs through structured file-based session management, the method comprising:

(a) redirecting AI agent output from an API response channel to persistent files, wherein the API response channel carries only status messages of configurable brevity;

(b) upon session termination, writing a bridge file containing complete agent working state at a cost of approximately 800-1,200 output tokens;

(c) upon session resumption, reading the bridge file and a working memory file at a cost of approximately 1,400-1,700 input tokens, rather than re-sending accumulated conversation history;

(d) maintaining active API sessions between tasks through a holding pattern consuming approximately 0-30 tokens per cycle, rather than terminating and restarting sessions at the cost of re-sending full conversation history;

(e) whereby the combined effect of (a) through (d) increases effective context window utilization from approximately 50% to approximately 85% and reduces session resume costs by approximately three orders of magnitude.

### Dependent Claims

**Claim 4.** The method of Claim 1, further comprising a compaction recovery protocol wherein, upon detection of a platform-initiated context compaction event, the agent recovers by re-reading its persistent file state rather than relying on the compacted conversation history, the persistent files serving as the authoritative source of truth.

**Claim 5.** The method of Claim 1, wherein the bidirectional communication channel further comprises a control file containing mode signals selected from at least: idle, continue, and autopilot, enabling asynchronous operational mode changes without consuming context window capacity for mode-change messages.

**Claim 6.** The method of Claim 1, further comprising drift detection patterns that monitor agent output for indicators of verbose conversational behavior and automatically redirect said output to the appropriate persistent file.

**Claim 7.** The system of Claim 2, wherein the idle engine module implements a tiered holding strategy comprising:
- a first tier (T0) of zero-cost wait pauses;
- a second tier (T1) of heartbeat micro-reads consuming approximately 30 tokens per cycle;
- a third tier (T2) of context summary operations consuming approximately 200 tokens; and
- a fourth tier (T3) of proactive validation checks consuming approximately 500 tokens;
wherein the system preferentially uses the lowest-cost tier that maintains session viability.

**Claim 8.** The system of Claim 2, wherein the idle engine module further comprises a signal file mechanism that enables external systems to inject tasks into a holding agent by writing task content to a designated signal file, the agent detecting said content during a heartbeat cycle and exiting the holding pattern to execute the injected task.

**Claim 9.** The system of Claim 2, further comprising a real-time context categorization module that classifies conversation content into prioritized category buckets as messages are exchanged, each category having a base priority weight, and wherein the categorized content is progressively pre-compacted at configurable utilization intervals.

**Claim 10.** The method of Claim 9, wherein the priority scoring for categorized items is computed as:

score = base_weight(category) x recency_factor x mention_count x override_penalty

wherein base_weight is determined by category type, recency_factor decays over time, mention_count increases for frequently referenced items, and override_penalty nullifies items superseded by later decisions.

**Claim 11.** The method of Claim 1, wherein the hierarchical directory further comprises:
- a knowledge subdirectory for persistent domain-specific knowledge files;
- an output subdirectory for completed work products;
- a progress subdirectory containing an append-only build log; and
- a settings subdirectory containing a configuration file with adjustable operational parameters.

**Claim 12.** The method of Claim 1, wherein the configurable thresholds of step (d) comprise:
- a first threshold (default 45% utilization) triggering a warning notification;
- a second threshold (default 47.5% utilization) triggering handoff preparation; and
- a third threshold (default 50% utilization) triggering a hard session stop;
wherein said thresholds are adjustable by an end user through the settings configuration file.

**Claim 13.** The method of Claim 3, further comprising generating an intelligent handoff package at the handoff preparation threshold, said handoff package being constructed from real-time categorized context items and comprising: active task description, decisions made, requirements with completion status, architectural decisions, code changes, open issues, pending ideas, and files to read first.

**Claim 14.** The system of Claim 2, wherein the output redirection module enforces a hard rule that any agent response exceeding a configurable sentence limit (default: 3 sentences) must be written to a persistent file, with only a file reference returned in the conversational response.

**Claim 15.** A method for preserving artificial intelligence agent context across session boundaries, the method comprising:

(a) during an active session, maintaining all agent working state in persistent files rather than relying on conversation history accumulation;

(b) upon detecting an imminent session termination, executing a bridge save sequence comprising writing current task state, progress, active context references, and next steps to a designated bridge file;

(c) upon starting a new session, executing a bridge restore sequence comprising reading the bridge file, a working memory file, and a master index file, then deleting the bridge file;

(d) whereby session continuity is achieved at a cost of approximately 2,500-3,000 tokens per bridge cycle, compared to re-sending the full conversation history which may cost 100,000-1,000,000 tokens depending on session length.

### Multi-Agent Filesystem Communication Claims

**Claim 16.** A method for coordinating a plurality of artificial intelligence agents through filesystem-based message routing, the method comprising:

(a) assigning each agent in a multi-agent system a designated mailbox directory on a shared filesystem, the mailbox comprising at minimum an inbox subdirectory for receiving messages and an outbox subdirectory for retaining copies of sent messages;

(b) enabling inter-agent communication by a sending agent writing a structured message file to a receiving agent's inbox directory, the message file comprising at minimum a sender identifier, recipient identifier, timestamp, message type, and message body;

(c) enabling message detection by each agent scanning its inbox directory at configurable intervals for new message files;

(d) implementing hierarchy-independent addressing whereby any agent may write a message to any other agent's inbox directory regardless of organizational position, task assignment, or logical hierarchy;

(e) enabling human operator participation as a first-class communication participant by granting the operator read access to all agent mailbox directories and write access to any agent's inbox directory, using the same message format as inter-agent messages.

**Claim 17.** A system for multi-agent artificial intelligence coordination through a filesystem communication fabric, the system comprising:

(a) a plurality of AI agents, each maintaining a private state directory for individual context window management through file-based state persistence as recited in Claim 2;

(b) a shared communication directory on the filesystem comprising a mailbox directory for each agent, a broadcast directory for system-wide messages, and a coordination directory for shared state;

(c) an agent registry file on the filesystem declaring the identity, capabilities, mailbox location, and current status of each active agent;

(d) a message protocol wherein inter-agent messages are individual structured files with metadata headers enabling message ordering, threading, priority routing, and state tracking through filesystem operations;

(e) whereby the filesystem serves simultaneously as the state persistence layer for individual agents (per Claims 1-15) and as the communication fabric between agents, requiring zero additional infrastructure beyond the filesystem.

**Claim 18.** The method of Claim 16, further comprising guaranteed delivery semantics implemented through message file state transitions, wherein each message file transitions through defined states comprising at minimum: pending (deposited in inbox, not yet read), read (recipient has opened and parsed the message), and acknowledged (recipient has confirmed processing), said state transitions effected by updating a status field within the message file header.

**Claim 19.** The method of Claim 16, further comprising crash recovery for inter-agent communications, wherein:

(a) upon an agent crash, unread messages remain persisted in the crashed agent's inbox directory as files on the filesystem;

(b) upon agent restart, the restarted agent scans its inbox directory for pending messages in addition to reading its bridge file for private state recovery;

(c) whereby inter-agent communications survive agent crashes, system restarts, and session boundaries without message loss, by virtue of messages being persistent files rather than in-memory objects or ephemeral API payloads.

**Claim 20.** The method of Claim 16, further comprising a broadcast communication mechanism wherein an agent writes a message file to a designated broadcast directory on the filesystem, said broadcast directory being monitored by all agents in the system, enabling one-to-many communication without the sending agent needing to enumerate or address each recipient individually.

**Claim 21.** The method of Claim 16, wherein the human operator participation of step (e) further comprises:

(a) operator observation of all inter-agent communications by reading inbox and outbox directories of any agent using standard filesystem tools;

(b) operator injection of instructions to a specific agent by writing a message file to that agent's inbox directory with a designated operator sender identifier;

(c) operator broadcast of instructions to all agents by writing to the broadcast directory;

(d) operator modification of an agent's status file to change its availability, pause its operation, or redirect its task assignment;

(e) whereby the operator maintains real-time observability and control over multi-agent coordination without requiring specialized monitoring tools, dashboards, or administrative APIs.

**Claim 22.** The system of Claim 17, further comprising a message validation module that verifies incoming messages by:

(a) confirming the sender identifier corresponds to an agent listed in the agent registry;

(b) validating the message file conforms to the expected structured format;

(c) rejecting messages from unknown or deregistered agents;

(d) rate-limiting message processing from any single source to prevent communication flooding;

(e) logging rejected messages for operator review.

**Claim 23.** The method of Claim 16, further comprising cross-session multi-agent continuity, wherein an agent's bridge file (as recited in Claim 15) additionally captures:

(a) a summary of pending inter-agent communications comprising messages sent but not yet acknowledged;

(b) correlation identifiers of active conversation threads with other agents;

(c) the current state of collaborative tasks involving multiple agents;

(d) whereby upon session resume, the agent reconstructs both its private state and its position in all ongoing inter-agent conversations, enabling multi-agent projects that span multiple session boundaries.

**Claim 24.** The method of Claim 16, wherein the structured message file further comprises:

(a) a correlation identifier linking a response message to the original message being replied to;

(b) a thread identifier grouping related messages into a conversation thread;

(c) a priority field selected from at least: critical, high, normal, and low;

(d) whereby agents can conduct multi-turn threaded conversations, prioritize urgent communications, and maintain conversational context across multiple message exchanges without consuming context window tokens for coordination overhead.

---

## ABSTRACT

A system and method for managing artificial intelligence agent context windows through structured file-based state persistence, output redirection, and multi-agent filesystem communication. The invention redirects substantive AI agent output from the conversational API response channel to persistent structured files on the filesystem, restricting conversational responses to brief status signals. A hierarchical file protocol provides the agent with persistent working memory, session continuity via a bridge mechanism, and bidirectional human-agent communication through designated files. A tiered context safety system monitors utilization and triggers progressive interventions at configurable thresholds. An idle engine maintains active sessions at near-zero cost through tiered holding patterns. Real-time context categorization enables intelligent handoff packages when session boundaries are reached. The combined effect increases effective context window utilization from approximately 50% to approximately 85%, reduces session resume costs by approximately three orders of magnitude, and renders platform-initiated context compaction events harmless by maintaining persistent files as the authoritative source of truth rather than conversation history. In an extended embodiment, the filesystem-based architecture is further leveraged as a multi-agent communication fabric, wherein each agent is assigned a mailbox directory on the shared filesystem. Agents communicate by writing structured message files to other agents' mailbox directories, enabling hierarchy-independent addressing, automatic crash recovery through message persistence, guaranteed delivery semantics through file-based state transitions, and human operator participation as a first-class communication participant with full read/write access to all inter-agent communications. The unified filesystem approach serves simultaneously as the state persistence layer for individual agent context management and as the zero-infrastructure message bus for multi-agent coordination.

---

## APPENDIX A: REFERENCE IMPLEMENTATION FILES

The following files constitute a working reference implementation of the described system:

**Single-Agent State Management (Sections 1-11):**
1. `.agent/system_prompt.md` — Core operating protocol with output redirection rules
2. `.agent/index.md` — Master navigation index
3. `.agent/working_memory.md` — Agent state file
4. `.agent/bridge.md` — Session continuity bridge file
5. `.agent/comms/to_human.md` — Agent-to-human communication channel
6. `.agent/comms/from_human.md` — Human-to-agent communication channel
7. `.agent/comms/control.md` — Operating mode control signal
8. `.agent/settings/config.yml` — Configurable operational parameters
9. `.agent/progress/build_log.md` — Append-only build history

**Multi-Agent Filesystem Communication (Sections 12-16):**
10. `.swarm/registry.yml` — Agent discovery registry with identity, capabilities, and mailbox locations
11. `.swarm/mailboxes/{agent-name}/inbox/` — Per-agent incoming message directory
12. `.swarm/mailboxes/{agent-name}/outbox/` — Per-agent sent message archive
13. `.swarm/mailboxes/{agent-name}/status.yml` — Per-agent status declaration
14. `.swarm/broadcast/` — System-wide broadcast message directory
15. `.swarm/coordination/task_board.md` — Shared task registry
16. `.swarm/coordination/decisions_log.md` — Cross-agent decision record
17. Example message file demonstrating the structured message format with YAML header

[NOTE TO INVENTOR: Include printed copies of these files with the provisional application. They strengthen the filing by showing a working implementation.]

---

## APPENDIX B: FILING INSTRUCTIONS

### How to File This Provisional Patent Application

**Step 1: Prepare Your Materials**
- This document (printed or as PDF)
- Drawings for Figures 1-10 (hand-drawn is acceptable, use plain white paper, label each figure)
- Printed copies of the reference implementation files listed in Appendix A
- Cover sheet (USPTO Form SB/16 — available at https://www.uspto.gov/patent/forms/forms-patent-applications-filed-or-after-september-16-2012)

**Step 2: File Online at USPTO**
1. Go to https://patentcenter.uspto.gov
2. Create an account if you don't have one
3. Select "New Provisional Application"
4. Upload this document as the specification
5. Upload figures separately
6. Fill in inventor information
7. Claim Micro Entity status (if applicable — annual gross income under $234,725 and not named on more than 4 previous patent applications)
8. Pay filing fee ($220 Micro Entity as of 2026)

**Step 3: What You Get**
- A filing receipt with an application number and filing date
- "Patent Pending" status for 12 months
- A priority date — if anyone else files a similar patent after your date, your filing date takes precedence

**Step 4: Within 12 Months**
- Consult with a patent attorney who specializes in software patents ($500-1,000 for initial consultation)
- Decide whether to convert to a full utility patent application ($8,000-15,000 with attorney)
- The provisional DOES NOT become a patent on its own — you must file a non-provisional within 12 months or the provisional expires

### Recommended Patent Attorneys (Software/AI Specialty)
- Search the USPTO's registered patent attorney database: https://oedci.uspto.gov/OEDCI/
- Look for attorneys with "computer science" or "electrical engineering" technical backgrounds
- Ask specifically about experience with AI/ML software patents

### Important Warnings
- DO NOT publicly disclose the invention before filing (no blog posts, no GitHub public repos, no conference talks)
- DO NOT discuss specifics with anyone outside of conversations protected by attorney-client privilege or NDA until after filing
- The provisional application IS confidential — USPTO does not publish provisional applications
- Keep all records of your development work (git commits, dated files, conversation logs) as evidence of invention dates

---

*This provisional patent application was prepared on [DATE OF FILING] and describes the invention as conceived and reduced to practice by the inventor.*

*[INVENTOR SIGNATURE]*
*[PRINTED NAME]*
*[DATE]*
