# PROVISIONAL PATENT APPLICATION

## United States Patent and Trademark Office
## Provisional Application for Patent

---

## TITLE OF THE INVENTION

**System and Method for Managing Artificial Intelligence Agent Context Windows Through Structured File-Based State Persistence and Output Redirection**

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

The present invention relates generally to artificial intelligence systems, and more specifically to methods and systems for managing context window utilization in large language model (LLM)-based AI agents through structured file-based state persistence, output redirection, and session continuity mechanisms.

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

The combined effect of these mechanisms is that the effective utilizable capacity of a given context window increases from approximately 50% (conventional operation) to approximately 85% (file-based operation), representing a 70% increase in effective working capacity using the same model at the same cost. Session persistence costs are reduced by approximately 6,000x compared to conventional cold-start session resumption.

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

---

## ABSTRACT

A system and method for managing artificial intelligence agent context windows through structured file-based state persistence and output redirection. The invention redirects substantive AI agent output from the conversational API response channel to persistent structured files on the filesystem, restricting conversational responses to brief status signals. A hierarchical file protocol provides the agent with persistent working memory, session continuity via a bridge mechanism, and bidirectional human-agent communication through designated files. A tiered context safety system monitors utilization and triggers progressive interventions at configurable thresholds. An idle engine maintains active sessions at near-zero cost through tiered holding patterns. Real-time context categorization enables intelligent handoff packages when session boundaries are reached. The combined effect increases effective context window utilization from approximately 50% to approximately 85%, reduces session resume costs by approximately three orders of magnitude, and renders platform-initiated context compaction events harmless by maintaining persistent files as the authoritative source of truth rather than conversation history.

---

## APPENDIX A: REFERENCE IMPLEMENTATION FILES

The following files constitute a working reference implementation of the described system:

1. `.agent/system_prompt.md` — Core operating protocol with output redirection rules
2. `.agent/index.md` — Master navigation index
3. `.agent/working_memory.md` — Agent state file
4. `.agent/bridge.md` — Session continuity bridge file
5. `.agent/comms/to_human.md` — Agent-to-human communication channel
6. `.agent/comms/from_human.md` — Human-to-agent communication channel
7. `.agent/comms/control.md` — Operating mode control signal
8. `.agent/settings/config.yml` — Configurable operational parameters
9. `.agent/progress/build_log.md` — Append-only build history

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
