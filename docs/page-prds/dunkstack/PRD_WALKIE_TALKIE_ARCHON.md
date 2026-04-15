# PRD: File-Based Context System for Archon (Tim Con)

## What This Document Is

This is the complete build PRD for adding a file-based context management system to Archon. This system replaces the standard AI chat pattern (where every message resends full conversation history) with a file-based approach where the agent communicates through files, the conversation history stays thin, and agent memory extends across 10-15 chained agents with full context continuity.

This PRD is designed to be fed directly into Archon's build workflow. Every mechanism is specified. Every file is named. Every behavior is defined.

---

## Why This Matters

### The Problem (What Every AI Chat Does Today)

Every AI chat platform works the same way:
1. You send message #1 (1,000 tokens sent to the model)
2. You send message #2 (message #1 + #2 = 3,000 tokens resent)
3. You send message #3 (messages #1 + #2 + #3 = 6,000 tokens resent)
4. By message #50, you're resending 200,000+ tokens every single message
5. At 60-70% context utilization, the model starts degrading — losing track of details, contradicting itself, forgetting decisions

This is like having a phone conversation where every time you speak, you have to repeat the ENTIRE conversation from the beginning before saying your new thing. It's expensive, wasteful, and the listener gets overwhelmed.

### The Solution (What We're Building)

One API call starts the conversation. After that, the human communicates through files (walkie-talkie injection via hooks). The agent writes all substantive output to files instead of the chat response. The chat channel carries only 1-2 sentence status messages.

Result:
- **90-97% token cost reduction** on conversation overhead
- **85-90% effective context utilization** instead of 50-60% (the model stays sharp because its context window isn't cluttered)
- **10-15 agent chains** with full context continuity (each new agent reads previous agents' files at ~12-20K token cost)
- **Real-time human-to-agent communication** during active sessions without new API calls

### The Three Capabilities This Enables

**Capability 1 — Extended Memory Without Degradation:**
Because the agent's knowledge lives in organized files (not piled in the context window), it can work through 900K tokens of a 1M context model and still have clarity. The context window only holds the current task. Everything else is in the filing cabinet, pulled out only when needed.

**Capability 2 — Agent Chaining With Full Context:**
When Agent 1 hits its context limit, Agent 2 starts and reads Agent 1's file system (~12-20K token "cab ride"). Agent 2 has FULL knowledge of everything Agent 1 did. Chain 10-15 agents and you have 10-15 million tokens of continuous, fully-contextualized work.

**Capability 3 — Cross-Pollination Between Projects:**
A background Haiku agent monitors all conversations. When something relevant to another project comes up, it tags and copies the insight to that project's file system. Next time you open that project, the agent already knows the insight without you repeating it.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARCHON (Tim Con)                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LEVEL 1: Subject List (Left Sidebar)                    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │AutoForge │ │ SaaS App │ │ Research │ │ General  │   │    │
│  │  │ Project  │ │ Project  │ │  & Plan  │ │   Chat   │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                    (click into one)                               │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LEVEL 2: Agent Chain (Token Log / Agent History)        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                │    │
│  │  │ Agent 1  │ │ Agent 2  │ │ Agent 3  │  ...           │    │
│  │  │ 0-900K   │ │900K-1.8M │ │1.8M-2.7M│                │    │
│  │  │ tokens   │ │ tokens   │ │ tokens   │                │    │
│  │  └──────────┘ └──────────┘ └──────────┘                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                    (active agent)                                 │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  CHAT INTERFACE                                          │    │
│  │  - First message = API call (starts session)             │    │
│  │  - All subsequent messages = walkie-talkie (file inject) │    │
│  │  - Agent responses appear in chat (1-2 sentences)        │    │
│  │  - Full output written to files                          │    │
│  │  - Proof logging panel showing savings in real-time      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  BACKGROUND: Cross-Pollination Agent (Haiku)             │    │
│  │  Monitors all conversations → tags relevant insights →   │    │
│  │  copies to other project file systems automatically       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  EXISTING: YAML Workflows (unchanged, still work)        │    │
│  │  Everything above is ADDITIVE. Existing Archon features   │    │
│  │  remain untouched and fully functional.                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scope: The 10 Mechanisms To Build

### Mechanism 1: Two-Level Page Navigation
### Mechanism 2: File-Based Chat Protocol (System Prompt)
### Mechanism 3: Walkie-Talkie Communication Through Files
### Mechanism 4: Deterministic Enforcement Via Hooks
### Mechanism 5: Agent Chaining With Cab Ride Context Loading
### Mechanism 6: Chat Input Mode Switch (API → Walkie-Talkie)
### Mechanism 7: Cross-Pollination Agent (Haiku Background Router)
### Mechanism 8: Proof Logging Dashboard
### Mechanism 9: Extensible Nesting (Future Third Level)
### Mechanism 10: YAML Workflow Compatibility

---

## Mechanism 1: Two-Level Page Navigation

### What It Does

Creates a two-level navigation structure where:
- **Level 1 (Subject List):** Left sidebar showing all subject/project categories. Each subject is a separate workspace with its own file system. Examples: "AutoForge", "SaaS Product", "Research", "General Chat"
- **Level 2 (Agent Chain):** Inside each subject, a collapsible panel (like the existing token log) showing all agents in the chain. Agent 1, Agent 2, Agent 3, etc. Each with its token usage. Click any agent to see its conversation history.

Each subject is actually a SEPARATE page (to avoid SSE/WebSocket conflicts), but the surrounding UI stays static so it appears as one continuous interface. The user sees a smooth experience — the page boundary is invisible.

### Technical Specification

**Database schema additions:**

```sql
-- New table: subjects (Level 1)
CREATE TABLE subjects (
  id TEXT PRIMARY KEY,           -- UUID
  name TEXT NOT NULL,            -- Display name ("AutoForge", "SaaS Product")
  description TEXT,              -- Optional description
  icon TEXT,                     -- Optional emoji or icon identifier
  file_system_path TEXT NOT NULL,-- Path to this subject's .agent/ directory
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sort_order INTEGER DEFAULT 0  -- For manual reordering
);

-- New table: agent_chains (Level 2)
CREATE TABLE agent_chains (
  id TEXT PRIMARY KEY,           -- UUID
  subject_id TEXT NOT NULL,      -- Foreign key to subjects
  agent_number INTEGER NOT NULL, -- Sequential: 1, 2, 3...
  conversation_id TEXT,          -- Links to existing Archon conversations table
  session_id TEXT,               -- Links to existing Archon sessions table
  tokens_used INTEGER DEFAULT 0, -- Total tokens consumed by this agent
  status TEXT DEFAULT 'active',  -- active | completed | archived
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  bridge_file TEXT,              -- Path to bridge.md if agent was bridged
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);
```

**Level 1 UI — Subject sidebar:**

The left sidebar shows all subjects. Each entry displays:
- Subject name
- Agent count ("3 agents, 2.7M tokens")
- Last active timestamp
- Color indicator (active = green, stale = gray)

Actions:
- [+ New Subject] button at bottom
- Right-click to rename or delete
- Drag to reorder

Clicking a subject loads that subject's chat interface. The URL changes (actual page navigation) but the sidebar stays rendered, giving the appearance of a single-page app.

**Level 2 UI — Agent chain panel:**

Inside each subject's chat view, a collapsible panel (position: below the chat header or as a secondary sidebar) shows:
- List of all agents in the chain
- Each agent shows: number, token count, status (active/completed), date range
- The active agent is highlighted
- Clicking a completed agent loads its conversation in read-only mode
- The active agent's conversation is live and interactive

When the active agent approaches the context limit (configurable, default 85% of model context), the system:
1. Triggers an auto-bridge (Mechanism 5)
2. Creates a new agent_chain entry
3. Starts a new conversation for the new agent
4. The new agent reads bridge + file system on startup

**File system per subject:**

Each subject gets its own directory:

```
.archon/subjects/{subject-id}/
├── .agent/
│   ├── index.md
│   ├── working_memory.md
│   ├── bridge.md
│   ├── comms/
│   │   ├── to_human.md
│   │   ├── from_human.md
│   │   └── control.md
│   ├── knowledge/
│   │   └── (topic files created by agent)
│   ├── output/
│   │   └── (deliverables created by agent)
│   ├── progress/
│   │   └── build_log.md
│   └── archive/
│       ├── index.md        (one-line summaries per past agent)
│       ├── session_001/    (Agent 1's archived files)
│       ├── session_002/    (Agent 2's archived files)
│       └── session_003/
└── cross-refs/
    └── (files written by cross-pollination agent)
```

### Navigation Behavior

- Browser URL: `/subjects/{subject-id}` — each subject is its own route
- The sidebar component is rendered at the layout level (above the route), so it persists across navigation
- SSE connections are per-subject — when you navigate away from a subject, the SSE connection closes; when you navigate to one, a new one opens
- This avoids the "multiple SSE on one page" problem entirely

---

## Mechanism 2: File-Based Chat Protocol (System Prompt)

### What It Does

The system prompt is the prime directive that overrides the agent's default behavior. Instead of returning everything through the API response (which fills the context window), the agent writes ALL substantive output to designated files and uses the API response only for brief status signals.

### Technical Specification

This system prompt is stored as a command file and loaded for every walkie-talkie-enabled session:

**File: `.archon/commands/walkie-talkie-protocol.md`**

```markdown
## Core Operating Protocol

You operate in file-based mode. ALL substantive output is written to designated
files using the Write tool, NEVER returned as conversation response.

Your conversation responses contain ONLY:
- Status confirmations (1-2 sentences maximum)
- Questions requiring immediate human input (keep under 3 sentences)
- Error notifications requiring human decision (keep under 3 sentences)

HARD RULE: Before generating ANY response longer than 3 sentences, STOP.
Write it to the appropriate file instead. Then respond with a 1-sentence
status update referencing the file.

Example CORRECT behavior:
- You complete analysis -> Write to .agent/output/analysis.md -> Respond: "Analysis complete. Written to output/analysis.md"
- You have a question -> Write detailed context to .agent/comms/to_human.md -> Respond: "Question posted to comms/to_human.md"

Example INCORRECT behavior:
- Writing a 500-word explanation in the chat response
- Providing code snippets in the chat instead of writing to files
- Summarizing findings in chat instead of writing a structured file

## File Structure

All files live under the subject's .agent/ directory:

.agent/
  index.md          - Master index of all files. YOU maintain this. Read FIRST every session.
  working_memory.md - Your current task, state, and context. Update after every major action.
  bridge.md         - Session continuity data. Read on startup if exists, then clear it.

  comms/
    to_human.md     - YOUR messages to the human. Append new entries, never overwrite.
    from_human.md   - Human's messages to you. READ ONLY. Never modify this file.
    control.md      - Mode signals. Values: idle | continue | autopilot

  knowledge/
    [topic].md      - One file per knowledge domain. Create as needed.

  output/
    [deliverable].md - Completed work products. Create as needed.

  progress/
    build_log.md    - Append-only log of what was done and decisions made.

  archive/
    index.md        - One-line summary per previous agent session.
    session_NNN/    - Archived files from previous agents in the chain.

## Every Turn Behavior

1. If this is the FIRST turn of the session:
   a. Read .agent/index.md (your file map)
   b. Read .agent/working_memory.md (your state)
   c. If .agent/bridge.md exists, read it and incorporate its context, then delete it
   d. Read .agent/comms/from_human.md for any new human input
   e. Read .agent/archive/index.md if it exists (previous agents' summaries)

2. For EVERY turn:
   a. Do your work (code, analyze, research, etc.)
   b. Write ALL substantive output to the appropriate file
   c. If you created new files, update .agent/index.md
   d. Update .agent/working_memory.md with current state after major actions
   e. Respond in chat with status ONLY (1-2 sentences max)

3. If you need human input:
   a. Write your full question with context to .agent/comms/to_human.md
   b. Respond in chat: "Question posted. See comms/to_human.md"

## Selective Reading

NEVER read an entire large file when you only need part of it.

Reading strategy:
1. Read .agent/index.md FIRST (your map of what exists)
2. For any file you need, read the heading structure first (first 20 lines)
3. Then read ONLY the specific section you need
4. Budget: aim to spend under 4,000 tokens on file reads per turn

If a file is under 50 lines, read the whole thing.
If a file is over 50 lines, use targeted line-range reads.

## Compaction Recovery

If your conversation history seems shorter than expected, or you feel
you have lost context about what you were doing, a compaction event
has occurred. This is normal.

DO NOT attempt to reconstruct from memory. Trust the files.
Immediately re-read:
1. .agent/index.md
2. .agent/working_memory.md
3. .agent/comms/from_human.md

These files contain everything you need. Resume work from the state
described in working_memory.md.

## Protocol Compliance

These rules are non-negotiable. If you notice yourself writing longer
chat responses, STOP and redirect to a file. Common drift patterns:

- "Let me explain..." -> Write to a file, respond with file reference
- "Here's what I found..." -> Write to a file
- Providing code snippets in chat -> Write to output/ file
- Answering with more than 3 sentences -> Write to comms/to_human.md
```

### File Templates

**File: `.agent/index.md` (created on subject creation)**

```markdown
# Agent Index
Last updated: [auto-populated timestamp]

## System Files
- index.md - THIS FILE. Master map of all files. Read first every session.
- working_memory.md - Current task, state, and recent context.
- bridge.md - Session continuity data (temporary, deleted after loading).

## Communication
- comms/to_human.md - Agent's messages to human (append-only)
- comms/from_human.md - Human's messages to agent (read-only for agent)
- comms/control.md - Session mode control (idle/continue/autopilot)

## Knowledge
[Empty - files added as knowledge is created]

## Output
[Empty - files added as deliverables are produced]

## Progress
- progress/build_log.md - Append-only log with timestamps

## Archive
- archive/index.md - One-line summaries of previous agent sessions
```

**File: `.agent/working_memory.md`**

```markdown
# Working Memory
Last updated: [timestamp]

## Current Task
[No active task]

## What Was Just Completed
[Nothing yet - new session]

## What To Do Next
[Awaiting first task assignment]

## Key Context
[No context yet]

## Open Questions
[None]
```

**File: `.agent/comms/to_human.md`**

```markdown
# Agent Messages
> Append new messages at the bottom. Never delete previous entries.
> Format: ## [timestamp] Category - Brief Title

[No messages yet]
```

**File: `.agent/comms/from_human.md`**

```markdown
# Human Messages
> Human writes messages here. Agent reads only, never modifies.
> Format: ## [timestamp] Message Title

[No messages yet]
```

**File: `.agent/comms/control.md`**

```markdown
mode: idle
```

**File: `.agent/progress/build_log.md`**

```markdown
# Build Log
> Append-only. Each entry includes timestamp, what was done, and why.

[No entries yet]
```

**File: `.agent/archive/index.md`**

```markdown
# Agent Chain Archive
> One-line summary per previous agent session.
> Format: ## Session NNN (date) - Summary

[No previous sessions]
```

---

## Mechanism 3: Walkie-Talkie Communication Through Files

### What It Does

Establishes bidirectional communication between human and agent through files instead of API calls. The human writes to `from_human.md`. The agent writes to `to_human.md`. A PreToolUse hook checks for new human messages before every tool call and injects them into the agent's context.

### Technical Specification

**Human -> Agent flow:**

1. Human types a message in the chat input (after the first API call)
2. Instead of creating a new API call, the frontend writes the message to `.agent/comms/from_human.md` via a REST endpoint
3. The message is appended (not overwritten) with a timestamp header
4. The PreToolUse hook (Mechanism 4) detects the new content on the next tool call
5. The hook injects the message into the agent's context
6. The agent reads it and responds (writing substantive response to `to_human.md`, brief status to chat)

**Agent -> Human flow:**

1. Agent has something to communicate (question, status, finding)
2. Agent appends to `.agent/comms/to_human.md` with timestamp header
3. A file watcher (or polling endpoint) detects the new content
4. The frontend displays the new message in the chat interface
5. Agent sends brief status in chat: "Update posted to comms/to_human.md"

**REST endpoint for human messages:**

```
POST /api/subjects/{subject-id}/walkie-talkie
Body: { "message": "Your message text here" }

Response: { "success": true, "written_to": ".agent/comms/from_human.md" }
```

This endpoint:
1. Reads the current `from_human.md`
2. Appends the new message with timestamp header
3. Updates a hash file (`.agent/comms/.from_human_hash`) for change detection
4. Returns success

**REST endpoint for reading agent messages:**

```
GET /api/subjects/{subject-id}/walkie-talkie/agent-messages
Query: ?since={timestamp}

Response: {
  "messages": [
    { "timestamp": "2026-04-14T14:23:01Z", "content": "Analysis complete..." }
  ]
}
```

This endpoint:
1. Reads `to_human.md`
2. Parses entries by timestamp headers
3. Returns only entries newer than the `since` parameter
4. The frontend polls this every 2-3 seconds (or uses SSE channel for push)

**Chat channel rules (both directions):**
- Maximum 3 sentences per message in the chat stream
- No code in chat
- No detailed explanations in chat
- Chat is ONLY: "Done. See [file]." or "Question in [file]." or "Ready for input."

---

## Mechanism 4: Deterministic Enforcement Via Hooks

### What It Does

Uses Archon's existing PreToolUse hook system to ENFORCE the file-based protocol with deterministic code, not just prompt instructions. The agent CANNOT bypass these rules because they are executed as TypeScript code before every tool call.

### Why This Is Critical

Previous attempts to build this system failed because agents drifted back to verbose chat responses and ignored the file protocol. Prompt-based instructions are suggestions. Hook-based enforcement is law. The agent literally cannot produce output that violates the rules because the enforcement layer operates outside the agent's control.

### Technical Specification

**New file: `packages/workflows/src/hooks/walkie-talkie-hooks.ts`**

This file exports hook callback functions used by the walkie-talkie workflow:

**Hook 1: Message Injection Hook (PreToolUse)**

```typescript
// Pseudocode - exact implementation depends on Archon's hook callback signature

interface WalkieTalkieHookConfig {
  subjectId: string;
  fromHumanPath: string;      // Path to from_human.md
  lastHashPath: string;       // Path to .from_human_hash
}

function createMessageInjectionHook(config: WalkieTalkieHookConfig) {
  let lastKnownHash: string = '';

  return async (event: PreToolUseEvent) => {
    // Read current from_human.md
    const content = await readFile(config.fromHumanPath);
    const currentHash = md5(content);

    // If content changed, inject the new message
    if (currentHash !== lastKnownHash) {
      const newMessages = extractNewMessages(content, lastKnownHash);
      lastKnownHash = currentHash;

      // Return the new messages to be injected into agent context
      return {
        decision: 'block',
        reason: `[WALKIE-TALKIE MESSAGE FROM USER]\n${newMessages}\n[END WALKIE-TALKIE MESSAGE]\n\nAcknowledge this message, then continue with your tool call.`
      };
    }

    // No new messages - let tool call proceed normally
    return undefined;  // or { decision: 'allow' }
  };
}
```

**Hook 2: Response Length Enforcer (PostToolUse or output interceptor)**

This hook monitors agent output and enforces the 3-sentence maximum:

```typescript
function createResponseEnforcerHook(config: WalkieTalkieHookConfig) {
  return async (event: PostToolUseEvent) => {
    // If the agent just produced a text response
    if (event.type === 'assistant_message') {
      const responseText = event.content;
      const sentenceCount = countSentences(responseText);

      if (sentenceCount > 3) {
        // Auto-write overflow to file
        const overflowPath = `${config.agentDir}/output/overflow_${Date.now()}.md`;
        await writeFile(overflowPath, responseText);

        // Truncate the chat response
        const truncated = getFirstNSentences(responseText, 2);
        return {
          modifiedContent: `${truncated} (Full response written to ${overflowPath})`
        };
      }
    }
    return undefined;
  };
}
```

**Hook 3: Working Memory Enforcer (PreToolUse)**

Tracks tool call count and forces working_memory.md updates:

```typescript
function createWorkingMemoryEnforcer(config: WalkieTalkieHookConfig) {
  let toolCallsSinceUpdate = 0;
  const UPDATE_FREQUENCY = 5;  // Force update every 5 tool calls

  return async (event: PreToolUseEvent) => {
    toolCallsSinceUpdate++;

    if (toolCallsSinceUpdate >= UPDATE_FREQUENCY) {
      toolCallsSinceUpdate = 0;
      return {
        decision: 'block',
        reason: 'PROTOCOL ENFORCEMENT: Update .agent/working_memory.md with current state before continuing. This is a mandatory checkpoint.'
      };
    }
    return undefined;
  };
}
```

**Integration with Archon's hook system:**

The `buildSDKHooksFromYAML` function in `packages/workflows/src/dag-executor.ts` currently only supports static hook responses. It needs to be extended to support dynamic hook types:

```typescript
// Extension to existing buildSDKHooksFromYAML function
// Add a new case for 'file_check' hook type alongside existing static hooks

case 'walkie_talkie':
  // Instead of returning a static response, call the dynamic hook function
  const hookFn = createMessageInjectionHook({
    subjectId: node.metadata.subjectId,
    fromHumanPath: `${agentDir}/comms/from_human.md`,
    lastHashPath: `${agentDir}/comms/.from_human_hash`
  });
  hookCallbacks.push({
    event: 'PreToolUse',
    callback: hookFn
  });
  break;
```

**YAML hook configuration:**

```yaml
# In a walkie-talkie workflow definition
nodes:
  - id: walkie-chat
    type: prompt
    command: walkie-talkie-protocol
    hooks:
      pre_tool_use:
        - type: walkie_talkie
          config:
            subject_id: "${subject_id}"
            enforce_response_length: true
            enforce_working_memory: true
            working_memory_frequency: 5
```

---

## Mechanism 5: Agent Chaining With Cab Ride Context Loading

### What It Does

When the active agent approaches its context limit, the system automatically:
1. Saves all current state to files (bridge save)
2. Archives the current agent's files
3. Creates a new agent
4. The new agent reads the archive index + bridge file to resume with full context

This enables 10-15 agent chains where each agent has complete knowledge of everything that came before, at a cost of only ~12-20K tokens per chain link ("cab ride").

### Technical Specification

**Auto-bridge trigger:**

The system monitors the active agent's token usage (from SSE stream events). When usage crosses the configurable threshold (default: 85% of model context), the bridge process begins:

```typescript
interface BridgeConfig {
  triggerThresholdPercent: number;  // Default: 85
  modelContextSize: number;         // e.g., 1000000 for Claude 1M
}

// Token tracking from SSE events
function onTokenUpdate(currentTokens: number, config: BridgeConfig) {
  const percentUsed = (currentTokens / config.modelContextSize) * 100;

  if (percentUsed >= config.triggerThresholdPercent) {
    triggerBridgeSave();
  }
}
```

**Bridge save sequence:**

When triggered, the system injects a bridge instruction to the agent via walkie-talkie:

```
[BRIDGE SAVE REQUIRED]

Your context is at {X}% capacity. Write a bridge file NOW.

Write to .agent/bridge.md:
1. Current task and progress percentage
2. Key decisions made this session (bullet list)
3. What to do next (specific, actionable steps)
4. Any open questions for the human
5. Files modified this session (list with brief descriptions)

After writing bridge.md, update .agent/working_memory.md with final state.
Then respond: "Bridge saved. Ready for agent transition."

This is mandatory. Do it now before your next task.
```

**Archive sequence (after bridge save):**

The system (server-side, deterministic code — not the agent):
1. Creates `.agent/archive/session_NNN/` directory
2. Copies key files from `.agent/` to the archive:
   - `working_memory.md`
   - `comms/to_human.md`
   - `comms/from_human.md`
   - `knowledge/*.md` (all knowledge files)
   - `progress/build_log.md`
3. Appends a one-line summary to `.agent/archive/index.md`:
   ```
   ## Session 3 (2026-04-14) - Built authentication system, decided on JWT tokens, 
   implemented login/register endpoints. Open: need to add password reset flow.
   ```
4. Clears comms files (fresh for next agent)
5. Leaves `index.md`, `working_memory.md`, and `bridge.md` in place

**New agent startup sequence:**

When the new agent starts:
1. System prompt includes the walkie-talkie protocol (Mechanism 2)
2. Agent reads `.agent/index.md` → `.agent/working_memory.md` → `.agent/bridge.md`
3. Agent reads `.agent/archive/index.md` (one-line summaries of all previous agents)
4. If the agent needs detail from a specific previous session, it reads files from `.agent/archive/session_NNN/`
5. Bridge.md is deleted after consumption
6. New agent_chains entry is created in the database

**Cab ride token budget:**

```
index.md:              ~500 tokens
working_memory.md:     ~800 tokens
bridge.md:             ~1,000 tokens
archive/index.md:      ~200 tokens per previous agent (15 agents = ~3,000 tokens)
Selective archive reads: ~5,000-10,000 tokens (only if needed)

TOTAL CAB RIDE: ~12,000 - 20,000 tokens (1.2-2% of 1M context)
```

---

## Mechanism 6: Chat Input Mode Switch

### What It Does

Makes the chat input transparently switch from API call mode to walkie-talkie mode after the first message. The user sees no difference — same input box, same send button, same experience. Behind the scenes, message #1 creates an API call and messages #2+ write to `from_human.md` for hook injection.

### Technical Specification

**Frontend state machine:**

```typescript
type ChatMode = 'api' | 'walkie-talkie';

interface ChatState {
  mode: ChatMode;
  sessionActive: boolean;
  messageCount: number;
}

function handleSendMessage(text: string, state: ChatState) {
  if (state.mode === 'api' || !state.sessionActive) {
    // First message or no active session: use regular API call
    sendAPIMessage(text);
    state.mode = 'walkie-talkie';  // Switch for all future messages
    state.sessionActive = true;
    state.messageCount = 1;
  } else {
    // All subsequent messages: write to file via REST endpoint
    sendWalkieTalkie(text);
    state.messageCount++;
  }
}
```

**User-visible behavior:**
- The input box is always the same
- Send button always looks the same
- Messages always appear in the chat in the same format
- The ONLY visible difference: a small indicator showing "Mode: API" or "Mode: Walkie-Talkie" (or just a colored dot — green for walkie-talkie, blue for API)
- File attachments and images work in both modes (in walkie-talkie mode, files are saved to `.agent/intake/` and the message references them)

**Session resumption:**
- If the user navigates away and comes back, `sessionActive` is checked against the server
- If the agent subprocess is still running (turn is alive), mode stays walkie-talkie
- If the subprocess has ended, mode resets to API (next message starts a new API call)
- The new API call is cheap because conversation history is thin (only status messages)

---

## Mechanism 7: Cross-Pollination Agent (Haiku Background Router)

### What It Does

A lightweight Haiku agent runs in the background, monitoring active conversations. When it detects content relevant to another subject/project, it tags the insight and writes a cross-reference to that project's file system. The next time you open that project, its agent already knows the insight.

### Technical Specification

**Trigger:** The cross-pollination agent runs after each significant exchange (configurable: every message, every 5 messages, or on-demand). It reads the recent content from the active subject's `to_human.md` and `from_human.md`.

**Process:**

1. Haiku reads the latest conversation entries from the active subject
2. Haiku reads a master list of all subjects and their descriptions (`.archon/subjects/subject-registry.json`)
3. Haiku determines if any content is relevant to other subjects
4. If yes, Haiku writes a cross-reference file to the target subject's directory

**Subject registry file: `.archon/subjects/subject-registry.json`**

```json
{
  "subjects": [
    {
      "id": "subj-001",
      "name": "AutoForge",
      "description": "AI coding agent platform with React UI and Claude Agent SDK",
      "tags": ["autoforge", "coding", "agents", "react", "ui"]
    },
    {
      "id": "subj-002",
      "name": "SaaS Product",
      "description": "Commercial SaaS product for selling AI agent tools",
      "tags": ["saas", "pricing", "business", "customers", "revenue"]
    }
  ]
}
```

**Cross-reference format:**

Written to: `.archon/subjects/{target-subject-id}/.agent/cross-refs/from-{source-subject}-{date}.md`

```markdown
---
source_subject: AutoForge
source_agent: Agent 3
timestamp: 2026-04-14T14:23:00Z
relevance: high
tags: [pricing, subscription]
---

## Cross-Reference: Subscription Pricing Discussion

In AutoForge Agent 3, the following was discussed that relates to this project:

"Tiered pricing at $29/$79/$199 was decided. Annual billing with monthly option preferred.
This pricing structure should be consistent across all products."

Source: AutoForge/.agent/archive/session_003/comms/to_human.md, entry at 14:23
```

**Haiku prompt for cross-pollination:**

```markdown
You are a knowledge router. Your ONLY job is to identify when information 
from one project is relevant to another project.

You will receive:
1. Recent conversation content from the active project
2. A list of all other projects with their descriptions and tags

For each piece of relevant information:
1. Identify which other project(s) it relates to
2. Write a brief cross-reference (3-5 sentences max) explaining what was discussed and why it's relevant
3. Tag it with relevant keywords

Rules:
- Only flag genuinely relevant cross-references (not every mention of a shared word)
- Keep cross-references brief — the target project's agent will read the source if it needs more detail
- Never modify the source project's files
- Write cross-references as new files, never overwrite existing ones
```

**Cost per cross-pollination check:**
- Haiku reading recent conversation: ~2,000-3,000 tokens
- Haiku reading subject registry: ~500 tokens
- Haiku writing cross-reference: ~500-1,000 tokens
- Total per check: ~3,000-4,500 tokens
- At Haiku pricing: ~$0.001-0.002 per check
- Running 20 times per session: ~$0.02-0.04 per session

**Agent startup integration:**

When any agent starts up (first turn behavior from Mechanism 2), it ALSO reads:
```
.agent/cross-refs/*.md  (any new cross-references from other projects)
```

This is added to the startup sequence in the system prompt. The agent incorporates any new cross-references into its understanding before starting work.

**Routing rules (optional, for power users):**

File: `.archon/cross-pollination-rules.yaml`

```yaml
rules:
  - tag_pattern: "pricing|revenue|cost"
    route_to: ["saas-product", "business-plan"]
  - tag_pattern: "architecture|design-pattern"
    route_to: ["all"]
  - tag_pattern: "personal|private"
    route_to: ["none"]

settings:
  auto_approve: false           # If false, cross-refs go to pending queue
  check_frequency: 5            # Check every N messages
  max_cross_refs_per_check: 3   # Don't spam other projects
```

---

## Mechanism 8: Proof Logging Dashboard

### What It Does

A collapsible panel in the chat interface that shows real-time proof the walkie-talkie system is working. Makes the invisible visible. Shows exactly what's happening: which messages went through API, which went through files, how many tokens were saved, and live file system activity.

### Why This Is Critical

This system has been a black box through multiple build attempts. The proof dashboard eliminates all ambiguity — you can SEE it working (or not working) in real time. No more guessing.

### Technical Specification

**Dashboard components:**

**Component 1: API Call Counter**

A prominent number display:
```
API Calls This Session: 1
```
If the system works, this stays at 1 for the entire session. If it climbs, something is wrong.

Implementation: Increment a counter in the frontend state every time `sendAPIMessage()` is called. Display it prominently.

**Component 2: Message Route Log**

A scrollable log showing every message and its route:

```
14:23:01  [API #1]      You -> Agent: "Build me a login page"     (8,200 input tokens)
14:23:45  [FILE WRITE]  Agent -> to_human.md: "Need DB choice"    (0 API tokens)
14:25:12  [WALKIE]      You -> from_human.md: "Use PostgreSQL"    (0 API tokens)
14:25:13  [HOOK INJECT] from_human.md -> Agent context             (0 API tokens)
14:28:00  [FILE WRITE]  Agent -> output/login.tsx                  (0 API tokens)
14:28:01  [POLL]        Hook check: no new messages                (~50 tokens)
14:29:00  [WALKIE]      You -> from_human.md: "Add dark mode"     (0 API tokens)
14:29:01  [HOOK INJECT] from_human.md -> Agent context             (0 API tokens)
```

Color coding:
- Red rows = API calls (expensive)
- Green rows = file-based (free/cheap)
- Gray rows = hook checks (negligible cost)
- Blue rows = file writes by agent

Implementation: The server emits SSE events for each action type. The frontend renders them as log entries. Event types: `api_call`, `walkie_talkie_sent`, `walkie_talkie_injected`, `file_write`, `file_read`, `hook_check`.

**Component 3: Token Cost Comparison**

Two columns showing actual cost vs. hypothetical cost without walkie-talkie:

```
┌─────────────────────────────┬──────────────────────────────┐
│  ACTUAL (walkie-talkie)     │  WITHOUT (normal chat)       │
│                             │                              │
│  API calls: 1               │  API calls: 14               │
│  Input tokens: 12,400       │  Input tokens: 287,000       │
│  Output tokens: 3,200       │  Output tokens: 28,000       │
│  Est. cost: $0.04           │  Est. cost: $0.86            │
│                             │                              │
│        SAVINGS: 95.3%       │                              │
└─────────────────────────────┴──────────────────────────────┘
```

The "without" column is calculated by simulating what each walkie-talkie message would have cost as a full API call with accumulated history. Formula:

```
hypothetical_cost_per_message[n] = system_prompt_tokens + sum(all_previous_messages[0..n-1]) + message[n]
```

This number grows with every message, making the savings gap visually dramatic.

**Component 4: File Activity Monitor**

Live view of file system activity:

```
14:28:00  READ   .agent/comms/from_human.md     (hash: a3f2c1)  No change
14:28:01  WRITE  .agent/output/login.tsx         (2,340 bytes)   NEW
14:28:01  WRITE  .agent/index.md                 (updated)
14:28:30  READ   .agent/comms/from_human.md     (hash: a3f2c1)  No change
14:29:00  READ   .agent/comms/from_human.md     (hash: b7e4d2)  NEW MESSAGE
14:29:01  WRITE  .agent/working_memory.md        (updated)
```

Implementation: The PreToolUse hook emits SSE events for every file operation it observes. The frontend renders them as a live activity stream.

**Component 5: API Lock Toggle**

A toggle switch labeled "Lock API Input":

- When ON: the chat input is disabled for API calls. ONLY walkie-talkie works. If the agent keeps working and responding, this PROVES the file system is the communication channel.
- When OFF: normal behavior (first message = API, rest = walkie-talkie)

This is the ultimate proof test. Lock the API, keep talking through files. If it works, the system is proven.

**Dashboard UI layout:**

The dashboard is a collapsible panel. When collapsed, it shows a one-line summary:

```
Session: 1 API call | 14 walkie-talkies | 95% savings | Agent 3 of chain
```

When expanded (click to expand), it shows all 5 components in a scrollable panel. Position: below the chat header or as a slide-out panel from the right edge.

**SSE event types to add:**

```typescript
type ProofLogEvent =
  | { type: 'api_call'; tokens_in: number; tokens_out: number; cost: number }
  | { type: 'walkie_sent'; message_length: number }
  | { type: 'walkie_injected'; message_length: number }
  | { type: 'file_read'; path: string; hash: string; changed: boolean }
  | { type: 'file_write'; path: string; bytes: number; is_new: boolean }
  | { type: 'hook_check'; has_message: boolean }
  | { type: 'bridge_triggered'; tokens_used: number; threshold: number }
  | { type: 'agent_chain_created'; agent_number: number };
```

---

## Mechanism 9: Extensible Nesting (Future Third Level)

### What It Does

Provides the structural ability to add a third navigation level in the future, without requiring architectural changes. This is NOT built now — it's a design consideration that ensures the two-level system doesn't paint us into a corner.

### Technical Specification

The subject system uses a simple parent-child model that supports nesting:

```sql
-- The subjects table already supports nesting via parent_id
ALTER TABLE subjects ADD COLUMN parent_id TEXT REFERENCES subjects(id);
```

When `parent_id` is NULL, the subject is top-level (Level 1). When `parent_id` references another subject, it's nested under that subject (Level 2 becomes a container for Level 3 subjects).

The UI rendering logic uses a recursive component:
- If a subject has children, clicking it shows its children (sub-subjects) instead of a chat
- If a subject has NO children, clicking it shows the agent chain + chat interface

**This column is added to the schema now but NO UI is built for it.** It's a one-line schema addition that costs nothing but prevents a future migration.

**To activate a third level later:** Add a [+] button inside a subject that creates a child subject. The sidebar renders recursively. Estimated future cost: ~20-30K tokens.

---

## Mechanism 10: YAML Workflow Compatibility

### What It Does

Ensures all existing Archon YAML workflows continue to function exactly as they do today. The walkie-talkie system is purely additive — it adds new capabilities alongside existing ones without modifying or breaking anything.

### Technical Specification

**What stays the same:**
- All existing YAML workflow definitions work unchanged
- The DAG executor processes nodes identically
- Static hook configurations remain supported
- All existing commands, adapters, and providers are untouched
- The existing chat/conversation system works as before

**What's added:**
- New `walkie_talkie` hook type in the hook schema (alongside existing types)
- New `WalkieTalkieProvider` that wraps `ClaudeProvider` with file-based protocol
- New REST endpoints for walkie-talkie operations (under `/api/subjects/`)
- New SSE event types for proof logging
- New database tables for subjects and agent chains

**Integration point — using walkie-talkie in YAML workflows:**

Existing workflows can OPTIONALLY use walkie-talkie hooks:

```yaml
# Existing workflow - unchanged, still works
workflow:
  name: code-review
  nodes:
    - id: reviewer
      type: prompt
      command: review-code
      model: opus

# New workflow using walkie-talkie - opt-in
workflow:
  name: interactive-session
  nodes:
    - id: chat-agent
      type: prompt
      command: walkie-talkie-protocol    # Uses the new system prompt
      model: sonnet
      hooks:
        pre_tool_use:
          - type: walkie_talkie          # New hook type
            config:
              subject_id: "${subject_id}"
```

The `type: walkie_talkie` hook is the ONLY new addition to the workflow schema. Everything else is backward compatible.

**Swarm workflows with walkie-talkie:**

Multiple agents in a YAML workflow can use the file system for inter-agent communication:

```yaml
workflow:
  name: coding-swarm
  nodes:
    # These run in parallel (same layer, no depends_on between them)
    - id: sonnet-coder-1
      type: prompt
      model: sonnet
      command: walkie-talkie-protocol
      hooks:
        pre_tool_use:
          - type: walkie_talkie
            config:
              inbox: ".agent/swarm/coder-1/inbox.md"

    - id: sonnet-coder-2
      type: prompt
      model: sonnet
      command: walkie-talkie-protocol
      hooks:
        pre_tool_use:
          - type: walkie_talkie
            config:
              inbox: ".agent/swarm/coder-2/inbox.md"

    - id: quality-checker
      type: prompt
      model: opus
      command: walkie-talkie-protocol
      hooks:
        pre_tool_use:
          - type: walkie_talkie
            config:
              inbox: ".agent/swarm/quality/inbox.md"

    # Orchestrator waits for all parallel nodes
    - id: merge-results
      type: prompt
      model: opus
      depends_on: [sonnet-coder-1, sonnet-coder-2, quality-checker]
      command: merge-swarm-results
```

Each parallel node has its own inbox. They can write to each other's inboxes through the file system. The orchestrator node runs after all parallel nodes complete.

---

## File Map: Every File Created or Modified

### New Files to Create

```
packages/workflows/src/hooks/walkie-talkie-hooks.ts    -- Hook callback functions
packages/workflows/src/schemas/walkie-talkie.ts        -- Zod schema for walkie-talkie config
packages/server/src/routes/subjects.ts                 -- REST endpoints for subjects + walkie-talkie
packages/server/src/routes/proof-logging.ts            -- REST endpoints for proof log events
packages/web/src/components/SubjectSidebar.tsx          -- Level 1 sidebar component
packages/web/src/components/AgentChainPanel.tsx         -- Level 2 agent chain component
packages/web/src/components/ProofDashboard.tsx          -- Proof logging dashboard component
packages/web/src/components/ChatModeIndicator.tsx       -- API/Walkie-talkie mode indicator
packages/web/src/hooks/useWalkieTalkie.ts              -- Frontend hook for walkie-talkie messaging
packages/web/src/hooks/useProofLogging.ts              -- Frontend hook for proof log events
packages/web/src/hooks/useSubjects.ts                  -- Frontend hook for subject CRUD
packages/web/src/hooks/useAgentChain.ts                -- Frontend hook for agent chain management
.archon/commands/walkie-talkie-protocol.md             -- System prompt command file
.archon/subjects/subject-registry.json                 -- Subject list for cross-pollination
.archon/cross-pollination-rules.yaml                   -- Routing rules for cross-pollination
```

### Existing Files to Modify

```
packages/workflows/src/dag-executor.ts                 -- Add 'walkie_talkie' case to buildSDKHooksFromYAML
packages/workflows/src/schemas/hooks.ts                -- Add walkie_talkie hook type to schema
packages/server/src/routes/api.ts                      -- Register new route modules
packages/server/src/db/schema.ts                       -- Add subjects + agent_chains tables
packages/server/src/db/migrations/                     -- Add migration for new tables
packages/web/src/App.tsx (or equivalent router)        -- Add subject routes
packages/web/src/layouts/MainLayout.tsx (or equivalent)-- Add SubjectSidebar to layout
```

### Per-Subject Files (created dynamically)

```
.archon/subjects/{subject-id}/.agent/index.md
.archon/subjects/{subject-id}/.agent/working_memory.md
.archon/subjects/{subject-id}/.agent/comms/to_human.md
.archon/subjects/{subject-id}/.agent/comms/from_human.md
.archon/subjects/{subject-id}/.agent/comms/control.md
.archon/subjects/{subject-id}/.agent/progress/build_log.md
.archon/subjects/{subject-id}/.agent/archive/index.md
.archon/subjects/{subject-id}/.agent/cross-refs/
```

---

## Build Sequence

### Phase 1: Foundation (Session 1)

**Step 1.1:** Create database migration for `subjects` and `agent_chains` tables.

**Step 1.2:** Create REST endpoints for subject CRUD (`/api/subjects/`).

**Step 1.3:** Create the Subject Sidebar component (Level 1 navigation). Wire it to the REST endpoints. Support: create, rename, delete, reorder subjects.

**Step 1.4:** Create the file system initialization — when a new subject is created, auto-create the `.agent/` directory with all template files from Mechanism 2.

**Step 1.5:** Create the walkie-talkie REST endpoint (`POST /api/subjects/{id}/walkie-talkie`) that writes to `from_human.md`.

**Step 1.6:** Create the dynamic PreToolUse hook (`walkie-talkie-hooks.ts`) with the message injection function.

**Step 1.7:** Extend `buildSDKHooksFromYAML` in `dag-executor.ts` to support the `walkie_talkie` hook type.

**Step 1.8:** Create the walkie-talkie system prompt command file (`.archon/commands/walkie-talkie-protocol.md`).

**Validation after Phase 1:**
- Can create subjects in the sidebar
- Can open a subject and start a chat
- First message goes through API (agent starts working)
- Can send walkie-talkie message that writes to from_human.md
- Agent's PreToolUse hook detects the message and injects it
- Agent responds briefly in chat, writes details to files

### Phase 2: Intelligence (Session 2)

**Step 2.1:** Build the chat input mode switch (Mechanism 6). After the first API message, the input transparently switches to walkie-talkie mode.

**Step 2.2:** Build the Agent Chain Panel (Level 2). Show agent history within each subject. Display token usage per agent.

**Step 2.3:** Implement auto-bridge trigger — when token usage hits threshold, inject bridge save instruction via walkie-talkie hook.

**Step 2.4:** Implement the archive sequence — server-side code that copies files to `archive/session_NNN/`, updates `archive/index.md`, and creates a new agent_chain entry.

**Step 2.5:** Implement the deterministic response enforcer hook (truncate responses > 3 sentences, auto-write to file).

**Step 2.6:** Implement the working memory enforcer hook (force update every N tool calls).

**Validation after Phase 2:**
- Chat input seamlessly switches from API to walkie-talkie after first message
- Agent chain panel shows all agents in the chain
- When context hits 85%, bridge save triggers automatically
- New agent starts with full context from previous agent's files
- Agent responses are deterministically limited to 3 sentences
- Working memory updates are enforced

### Phase 3: Visibility & Cross-Pollination (Session 3)

**Step 3.1:** Build the Proof Logging Dashboard (Mechanism 8). All 5 components: API counter, message route log, cost comparison, file activity monitor, API lock toggle.

**Step 3.2:** Add SSE event emissions for all proof log event types throughout the server code.

**Step 3.3:** Create the subject registry file and cross-pollination rules config.

**Step 3.4:** Build the cross-pollination Haiku agent — a lightweight workflow that reads recent conversation, checks subject registry, writes cross-references.

**Step 3.5:** Add cross-reference reading to the agent startup sequence (reads `.agent/cross-refs/` on first turn).

**Step 3.6:** Add the `parent_id` column to subjects table (Mechanism 9 — future nesting support, schema only, no UI).

**Validation after Phase 3:**
- Proof dashboard shows real-time system activity
- API call counter stays at 1 for entire sessions
- Cost comparison shows savings percentage growing with each message
- Cross-pollination agent detects and routes relevant insights between projects
- API lock toggle proves the system works without any API calls after the first one

---

## Configuration & Settings

**File: `.archon/walkie-talkie-config.yaml`**

```yaml
# Walkie-Talkie System Configuration

context_management:
  working_memory_frequency: 5     # Force update every N tool calls
  max_chat_sentences: 3           # Max sentences in chat response
  file_read_budget: 4000          # Suggested max tokens per turn on file reads

agent_chaining:
  bridge_threshold_percent: 85    # Trigger bridge save at this % of context
  model_context_size: 1000000     # Current model's context window
  max_chain_length: 15            # Maximum agents in a chain
  cab_ride_budget: 20000          # Max tokens for cab ride context loading

cross_pollination:
  enabled: true
  check_frequency: 5              # Check every N messages
  model: haiku                    # Model for cross-pollination checks
  auto_approve: false             # If false, cross-refs go to pending queue
  max_refs_per_check: 3

proof_logging:
  enabled: true
  emit_file_activity: true        # SSE events for file reads/writes
  emit_hook_checks: true          # SSE events for hook checks
  calculate_hypothetical_cost: true  # Show "would have cost" comparison

ui:
  collapsed_dashboard_default: true  # Dashboard starts collapsed
  show_mode_indicator: true          # Show API/Walkie-Talkie indicator
  agent_chain_position: 'header'     # 'header' | 'sidebar' | 'bottom'
```

---

## What This Does NOT Change

To be explicitly clear about what is NOT modified:

1. **Existing YAML workflows** — all work identically, no changes
2. **Existing commands** — all work identically
3. **Existing adapters** (Telegram, Slack, Discord, CLI) — unchanged
4. **Existing database tables** (conversations, sessions, messages, etc.) — unchanged
5. **Existing SSE transport** — unchanged, new events are additive
6. **Existing chat functionality** — still works for users who don't use walkie-talkie subjects
7. **Git worktree isolation** — unchanged
8. **The `claude` CLI subprocess model** — unchanged; walkie-talkie hooks work within the existing subprocess lifecycle

---

## Success Criteria

The system is working when:

1. **API call count stays at 1** for an entire multi-message session
2. **Agent responses are consistently 1-2 sentences** with details in files
3. **Walkie-talkie messages are injected within one tool call** (~seconds, not minutes)
4. **Token cost comparison shows 85%+ savings** over hypothetical normal chat
5. **Agent chain transition is seamless** — new agent picks up exactly where previous left off
6. **Cross-pollination creates accurate cross-references** between projects
7. **The API lock test passes** — system works with API input disabled
8. **Existing YAML workflows are unaffected** — all pass their existing tests

---

## Notes for the Build Agent

1. **Read this entire document before creating any files.** Understand the full system before implementing any part.

2. **Do NOT modify existing Archon core files** unless explicitly listed in the "Existing Files to Modify" section. This system is additive.

3. **Follow Archon's existing patterns.** Read `CLAUDE.md` in the Archon repo for coding standards (strict TypeScript, Zod schemas, YAGNI principle). Match existing code style.

4. **The hook extension in `dag-executor.ts` is the most critical change.** The `buildSDKHooksFromYAML` function must support dynamic hook callbacks (not just static responses). Get this right and everything else flows from it.

5. **Test each mechanism independently** before integrating. Start with the PreToolUse hook (can it inject a message?), then the file system (do templates create correctly?), then the UI (does the sidebar work?).

6. **The proof logging dashboard is NOT optional.** It is how we verify the system works. Build it alongside the core system, not as an afterthought.

7. **Use Archon's existing database patterns** for the new tables. Check `packages/server/src/db/` for existing schema and migration patterns.

8. **The cross-pollination agent is a lightweight workflow,** not a persistent background process. It runs on-demand (triggered after every N messages) as a quick Haiku call. Do not build it as a daemon.
