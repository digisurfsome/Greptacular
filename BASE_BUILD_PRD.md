# Base Build PRD: File-Based Context Mechanism

## What This Document Is

This is the PRD for building the MINIMUM VIABLE mechanism that enables file-based context management for AI coding agents. This mechanism replaces the default behavior where AI agents dump all output through the API response (consuming context window and costing money) with a system where agents write substantive output to files and use the API response only for brief status signals.

Once this base mechanism works, it becomes the foundation for building everything else: the full PRD machine, the swarm architecture, the marketing pipeline, and the commercial tool.

## Why This Matters

**The problem:** AI coding agents degrade in quality as their context window fills up. At 50% utilization (~100K tokens on a 200K model), attention dilution causes errors. The conventional approach is to cap usage at 50% and restart sessions frequently, losing context each time.

**The solution:** Redirect all substantive agent output to structured files instead of the API response. The context window stays clean because it only carries: the system prompt, the current file reads (targeted/selective), and brief status messages. Working state persists in files across sessions. The agent reads what it needs, works, writes results to files, and the context window never accumulates stale reasoning.

**The result:** 85%+ effective context utilization instead of 50%. Quality stays high throughout the entire session because the context is curated, not accumulated. Sessions can end and restart seamlessly because all state lives in files.

---

## Scope: The 7 Core Mechanisms

### 1. System Prompt That Redirects Output to Files
### 2. File Structure (index.md, working_memory.md, constitution files)
### 3. Walkie-Talkie Communication Through Files
### 4. Idle/Pause Mechanism for Back-and-Forth Sessions
### 5. Bridge Save on Session End
### 6. Context Gauge (Real-Time Token Tracking)
### 7. Context Safety System (Warning / Handoff / Hard Stop)

Everything else (PRD machine, golden orange feature extraction, GIF automation, marketing pipeline, swarm architecture, notification system) is OUT OF SCOPE for this build. Those are built ON TOP of this mechanism once it proves out.

---

## Mechanism 1: System Prompt That Redirects Output to Files

### What It Does
The system prompt is the agent's prime directive. It overrides the agent's default behavior of returning everything through the API response. Instead, all substantive output (analysis, code, plans, research, decisions, documentation) gets written to designated files. The API response contains ONLY brief status signals.

### Why It's Critical
Without this, the agent reverts to default behavior and dumps everything into the chat. The context window fills with accumulated responses. The entire file-based architecture is bypassed. This single instruction is the foundation everything else depends on.

### Technical Specification

The system prompt must include these sections:

**Section A: Core Operating Protocol**

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
- You complete analysis → Write to .agent/output/analysis.md → Respond: "Analysis complete. See .agent/output/analysis.md"
- You have a question → Write detailed context to .agent/comms/to_human.md → Respond: "Question posted to comms/to_human.md"

Example INCORRECT behavior:
- Writing a 500-word explanation in the chat response
- Providing code snippets in the chat instead of writing to files
- Summarizing findings in chat instead of writing a structured file
```

**Section B: File Map Declaration**

```markdown
## File Structure

All files live under the project's .agent/ directory:

.agent/
  index.md          - Master index of all files. YOU maintain this. Read FIRST every session.
  working_memory.md - Your current task, state, and context. Update after significant work.
  bridge.md         - Session continuity data. Read on startup if it exists, then clear it.

  comms/
    to_human.md     - YOUR messages to the human. Append new entries, never overwrite.
    from_human.md   - Human's messages to you. READ ONLY. Never modify this file.
    control.md      - Mode signals. Check after each idle cycle. Values: idle | continue | autopilot

  knowledge/
    [topic].md      - One file per knowledge domain. Create as needed.

  output/
    [deliverable].md - Completed work products. Create as needed.

  progress/
    build_log.md    - Append-only log of what was built, when, and decisions made.
```

**Section C: Per-Turn Behavior**

```markdown
## Every Turn Behavior

1. If this is the FIRST turn of the session:
   a. Read .agent/index.md (your file map)
   b. Read .agent/working_memory.md (your state)
   c. If .agent/bridge.md exists, read it and incorporate its context, then delete it
   d. Read .agent/comms/from_human.md for any new human input
   e. Read .agent/comms/control.md for mode signal

2. For EVERY turn:
   a. Do your work (code, analyze, research, etc.)
   b. Write ALL substantive output to the appropriate file
   c. If you created new files, update .agent/index.md
   d. Every 3 turns, update .agent/working_memory.md with current state
   e. Respond in chat with status ONLY (1-2 sentences max)

3. If you need human input:
   a. Write your full question with context to .agent/comms/to_human.md
   b. Respond in chat: "Question posted. See comms/to_human.md"
   c. Enter idle mode (see Mechanism 4)
```

**Section D: Selective Reading Rules**

```markdown
## Selective Reading

NEVER read an entire large file when you only need part of it.

Reading strategy:
1. Read .agent/index.md FIRST (your map of what exists and where)
2. For any file you need, read the heading structure first (first 20 lines)
3. Then read ONLY the specific section you need
4. Budget: aim to spend under 4,000 tokens on file reads per turn

If a file is under 50 lines, read the whole thing.
If a file is over 50 lines, use targeted line-range reads.
```

**Section E: Compaction Recovery**

```markdown
## Compaction Recovery

If your conversation history seems shorter than expected, or you feel
you have lost context about what you were doing, a compaction event
has occurred. This is normal and NOT a problem.

DO NOT attempt to reconstruct from memory. Trust the files.
Immediately re-read:
1. .agent/index.md
2. .agent/working_memory.md
3. .agent/comms/from_human.md (for any recent human input)

These files contain everything you need. Resume work from the state
described in working_memory.md. The files are your source of truth,
not your conversation history.
```

**Section F: Compliance Reinforcement**

```markdown
## Protocol Compliance

These rules are non-negotiable. If you notice yourself writing longer
chat responses, STOP and redirect to a file. Common drift patterns
to catch yourself on:

- "Let me explain..." → Write to a file instead, respond with file reference
- "Here's what I found..." → Write to a file instead
- "The code looks like..." → Write to a file instead
- Providing code snippets in chat → Write to output/ file instead
- Answering a question with more than 3 sentences → Write to comms/to_human.md

If the human tells you "file mode" or "back to protocol" or "too long",
immediately return to strict file-based operation.
```

### Files to Create

1. **The system prompt file itself** - stored as `.agent/system_prompt.md` so it can be versioned, iterated, and loaded programmatically
2. **A loader/injector mechanism** - how the system prompt gets loaded into the agent session. For Claude Code CLI: this goes into `CLAUDE.md` at the project root. For API usage: this is the system message parameter.

### Integration with CLAUDE.md

For Claude Code (the current environment), the system prompt content should be placed in `CLAUDE.md` at the project root. Claude Code automatically loads this file as context for every session. This is the simplest deployment path for testing.

---

## Mechanism 2: File Structure

### What It Does
Creates the directory structure and initial file templates that the agent reads from and writes to. These files replace the conversation history as the agent's persistent memory.

### Technical Specification

**Directory structure to create:**

```
.agent/
├── index.md
├── working_memory.md
├── bridge.md              (empty initially, created by bridge mechanism)
├── comms/
│   ├── to_human.md
│   ├── from_human.md
│   └── control.md
├── knowledge/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── progress/
│   └── build_log.md
└── settings/
    └── config.yml
```

**File: `.agent/index.md`**

```markdown
# Agent Index
Last updated: [timestamp]

## System Files
- index.md - THIS FILE. Master map of all project files. Read first every session.
- working_memory.md - Agent's current task, state, and recent context.
- bridge.md - Session continuity data (temporary, deleted after loading).

## Communication
- comms/to_human.md - Agent's messages to human (append-only)
- comms/from_human.md - Human's messages to agent (read-only for agent)
- comms/control.md - Session mode control (idle/continue/autopilot)

## Knowledge
[Empty - files added here as knowledge is created]

## Output
[Empty - files added here as deliverables are produced]

## Progress
- progress/build_log.md - Append-only build log with timestamps
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
# Session Control
mode: idle
message: none
```

**File: `.agent/progress/build_log.md`**

```markdown
# Build Log
> Append-only. Each entry includes timestamp, what was done, and why.

[No entries yet]
```

**File: `.agent/settings/config.yml`**

```yaml
# Agent Settings - Adjustable Levers
version: 1

mode:
  type: subscription              # subscription | api
  model_family: claude-sonnet     # claude-sonnet | claude-opus
  # Subscription mode: system prompt via CLAUDE.md, token tracking estimates,
  #   compaction will occur, no API key needed
  # API mode: system prompt via API system message, exact token tracking
  #   from response headers, no compaction, API key required

api:
  key_env_var: ANTHROPIC_API_KEY  # Environment variable name for API key
  model_id: claude-sonnet-4-6     # Model ID for API calls
  max_tokens_output: 16000        # Max output tokens per call

context_management:
  utilization_target: 85          # % of context window to use
  working_memory_frequency: 3     # Update every N turns
  file_read_budget: 4000          # Max tokens per turn on file reads
  api_response_max_sentences: 3   # Max sentences in chat response

session:
  idle_cycle_seconds: 300         # Wait between heartbeats (5 min)
  bridge_on_end: true             # Auto-save state on session end

safety:
  warning_threshold_pct: 45       # Tier 1: warning notification to agent
  handoff_threshold_pct: 47.5     # Tier 2: stop coding, write handoff
  hard_stop_threshold_pct: 50     # Tier 3: kill session
  post_stop_review: true          # Run code review after hard stop
  model_limit: 200000             # Current model context window size

build:
  test_after_feature: true        # Run tests after each feature built
```

---

## Mechanism 3: Walkie-Talkie Communication Through Files

### What It Does
Establishes bidirectional communication between human and agent through files instead of the API chat. The human writes to `from_human.md`. The agent writes to `to_human.md`. The chat channel becomes a thin notification layer.

### Why It Matters
Every message sent through the API chat consumes context tokens permanently. A detailed human message explaining a requirement might be 500-1000 tokens. Ten such messages = 5,000-10,000 tokens of context permanently consumed. By moving substantive communication to files, the context window carries only brief status signals.

### Technical Specification

**Agent → Human flow:**

1. Agent needs to communicate something substantive (question, status report, deliverable summary)
2. Agent appends to `.agent/comms/to_human.md`:
```markdown
## [2026-02-24 14:23] Question - Database Choice
Need your input on database selection for user data storage.

Options analyzed:
1. PostgreSQL (Score: 87%) - Best for relational data, strong ecosystem
2. SQLite (Score: 72%) - Simpler, no server needed, good for MVP
3. MongoDB (Score: 61%) - Flexible schema but adds complexity

Developer's Choice: Option 1 (PostgreSQL)
Confidence: 87%

If you agree with the recommendation, just confirm. If you prefer
a different option, let me know which and why.
```
3. Agent sends brief chat message: "Question about database posted to comms/to_human.md"

**Human → Agent flow:**

1. Human has input to provide (answer to question, new requirement, feedback)
2. Human writes to `.agent/comms/from_human.md`:
```markdown
## [2026-02-24 14:28] Answer - Database Choice
Go with PostgreSQL. Also: make sure we use connection pooling
from day one, don't want to retrofit that later.
```
3. Human sends brief chat message: "Answer in from_human.md"

**Human → Agent flow (for large documents/PRDs/reference material):**

1. Human places file in `.agent/intake/` directory with a tagged header:
```markdown
---
type: reference
relates_to: architecture
priority: must_read
---
[Large document content here]
```
2. Human sends brief chat message: "New reference doc in intake/"
3. Agent reads the file, processes it, updates index.md

**The chat channel rules (both directions):**
- Maximum 3 sentences per message
- No code in chat
- No detailed explanations in chat
- No questions with multiple options in chat (those go to files)
- Chat is ONLY: "Done. See [file]." or "Question in [file]." or "Ready for input."

### Existing Implementation

The current walkie-talkie system in this project already uses a tool-based approach for passing messages through files. The mechanism described here extends that pattern to be the PRIMARY communication channel, not a supplement to chat.

---

## Mechanism 4: Idle/Pause for Back-and-Forth Sessions

### What It Does
Keeps the agent session alive during periods where the human is thinking, writing, or away. Uses lightweight tool calls to prevent session timeout without consuming significant tokens.

### Why It Matters
The human-AI interaction is asymmetric: the agent responds in seconds, the human needs 5-10 minutes (or longer) to formulate thoughts. Without an idle mechanism, the session times out during human thinking time, requiring a restart.

### Technical Specification

**The idle loop:**

```
Agent completes output →
  Writes substantive content to appropriate files →
  Sends brief chat status →
  Reads comms/control.md for mode signal →
  IF mode = "idle":
    Call wait tool (5 minute timeout, configurable) →
    After wait completes:
      Read comms/control.md again →
      Read comms/from_human.md for new content →
      IF new content: process it, resume working →
      IF no new content AND mode still "idle": repeat wait cycle →
      IF mode changed to "continue": resume current task →
      IF mode changed to "autopilot": work through task list independently
  IF mode = "continue":
    Proceed with current task without waiting
  IF mode = "autopilot":
    Work through full task list, only pause for blocking questions
```

**Mode transitions:**
- `idle` → default after agent completes a response and is waiting for human
- `continue` → human signals "keep going, don't wait for me"
- `autopilot` → human signals "do everything, only stop if you absolutely need my input"

**Human controls:**
- Write to `comms/control.md` to change mode
- Send a brief chat message at any time to override idle wait
- The chat message itself acts as an interrupt signal

**Token cost of idling:**
- Each wait cycle: ~100 tokens (tool call overhead)
- Per hour of idling: ~1,200 tokens
- This is negligible (~1.2% of 100K working budget per hour)

**Implementation note for Claude Code:**
In Claude Code, the idle mechanism is implemented by the agent reading a file, then the human taking their time to respond. There isn't a programmatic "wait" tool in the standard toolset. The natural pause happens between agent output and human input. The key mechanism here is ensuring the agent CHECKS the control file and from_human.md at the start of each turn, and that the session doesn't timeout prematurely.

For the API-based version (future SaaS), a proper wait/poll mechanism would be implemented server-side.

---

## Mechanism 5: Bridge Save on Session End

### What It Does
Automatically saves the agent's complete working state to files before a session ends. On the next session start, the agent reads these files and resumes exactly where it left off. The goal: session boundaries become invisible.

### Why It Matters
Sessions end for many reasons: timeout, human leaves, emergency, deliberate restart for clean context. Without bridge saving, the agent loses any context that exists only in the conversation and wasn't yet written to files. With bridge saving, nothing is lost.

### Technical Specification

**When to trigger bridge save:**
- Human signals they're leaving ("I need to go", "wrapping up", "save state")
- Session approaching timeout (if detectable)
- Before any deliberate session restart
- Agent should also do periodic working_memory updates (every 3 turns) as an ongoing micro-bridge

**The bridge save sequence:**

1. Agent writes to `.agent/bridge.md`:
```markdown
# Bridge State
Saved: [timestamp]
Reason: [human departing | timeout approaching | deliberate restart]

## Current Task
[Exact description of what was in progress]

## Progress on Current Task
[Percentage complete, what's done, what remains]

## Active Context Not Yet in Files
[Any reasoning, decisions, or understanding from recent conversation
that hasn't been written to knowledge/ or progress/ files yet]

## Immediate Next Steps
[Exactly what the agent should do first when resuming]

## Open Questions
[Any unanswered questions for the human]

## Files Modified This Session
[List of files created or modified, for quick orientation on resume]
```

2. Update `.agent/working_memory.md` with final state
3. Update `.agent/index.md` if any new files were created
4. Append session summary to `.agent/progress/build_log.md`
5. Send brief chat message: "State saved. Safe to end session."

**On next session start (the resume sequence):**

1. Read `.agent/index.md` (~500 tokens)
2. Read `.agent/working_memory.md` (~400 tokens)
3. IF `.agent/bridge.md` exists:
   a. Read it (~500-800 tokens)
   b. Incorporate context into current understanding
   c. Delete bridge.md (it's been consumed)
4. Read `.agent/comms/from_human.md` for any messages posted while agent was offline
5. Read `.agent/comms/control.md` for current mode
6. Resume work from where bridge.md indicated

**Total bridge cost:**
- Saving: ~800-1,200 output tokens (writing bridge.md + updating other files)
- Restoring: ~1,400-1,700 input tokens (reading bridge + working memory + index)
- Combined: ~2,500-3,000 tokens per bridge cycle
- On 100K working budget: 2.5-3% per bridge
- Recommendation: bridge only on session end, not proactively (unless testing shows quality benefit)

---

## Mechanism 6: Context Gauge (Real-Time Token Tracking)

### What It Does
Displays real-time token usage throughout the session. Shows a visual gauge of how much of the context window has been consumed, a running log of individual API call token counts, and cumulative cost tracking.

### Why It Matters
Without visibility into token usage, there's no way to know if the file-based system is actually working as designed. The gauge provides immediate feedback: is context accumulating slowly (good - the system is working) or quickly (bad - something is bypassing the file system)? It also prevents surprise overruns.

### Technical Specification

**Data source:** The Anthropic API returns exact token usage in every response:
- `input_tokens` - tokens sent to the model
- `output_tokens` - tokens generated by the model
- `cache_creation_input_tokens` - tokens written to cache
- `cache_read_input_tokens` - tokens read from cache

These values are EXACT (not estimates). The gauge reads them from each API response and accumulates.

**Display components:**

1. **Context Gauge Bar** - Visual progress bar showing current cumulative token usage as percentage of model's context window limit. Color-coded:
   - Green: 0-70% (safe zone)
   - Yellow: 70-85% (operating zone for file-based system)
   - Orange: 85-90% (approaching warning threshold)
   - Red: 90-100% (warning/danger zone)
   - Model limit selector: 200K or 1M (changes the denominator)

2. **Token Log Panel** - Scrollable list of individual API calls showing:
   - Timestamp
   - Input tokens for that call
   - Output tokens for that call
   - Cache tokens (creation + read)
   - Cost for that call
   - Running cumulative total

3. **Session Summary** - Top-level stats:
   - Total tokens used this session
   - Total cost this session
   - Number of API calls
   - Average tokens per call (useful for detecting if calls are getting bloated)

**Implementation reference:** The existing workspace in this project already has a working token tracking gauge. The build agent should examine that implementation for the UI pattern and data flow. Look for the token log component, the gauge bar component, and how they read usage data from API responses.

**Calibration:** For maximum accuracy, the human can pull actual usage logs from the Anthropic dashboard and compare against the gauge readings. Any discrepancy can be used to calibrate the tracking logic.

---

## Mechanism 7: Context Safety System (Warning / Handoff / Hard Stop)

### What It Does
A three-tier automatic protection system that prevents context window overruns. Uses the token data from Mechanism 6 to trigger warnings, forced handoffs, and hard stops at configurable thresholds.

### Why It Matters
If the file-based system malfunctions or a task turns out to be much larger than expected, the agent could blow past the safe context limit. Without automatic protection, this means degraded code quality, errors, and potentially wasted tokens. The safety system ensures the agent either finishes cleanly or hands off to a fresh agent before quality degrades.

### Technical Specification

**Three tiers with configurable thresholds:**

**Tier 1 - WARNING (default: 90K tokens on 200K model / 45%)**
- Trigger: cumulative token usage crosses the warning threshold
- Action: inject an internal message to the agent:
  ```
  CONTEXT WARNING: You are at [X]K tokens ([Y]% of limit).
  [Z]K tokens remaining. If your current task cannot complete
  within [Z]K tokens, begin handoff preparation immediately.
  ```
- The agent continues working but is now aware of the constraint
- Visual: gauge bar turns orange

**Tier 2 - HANDOFF (default: 95K tokens on 200K model / 47.5%)**
- Trigger: cumulative token usage crosses the handoff threshold
- Action: agent STOPS current coding work and writes a handoff file:
  ```markdown
  # Handoff State
  Saved: [timestamp]
  Reason: Context safety - approaching limit
  Tokens used: [X]K / [limit]K

  ## What Was Being Built
  [Current task description]

  ## Completed Work
  [What's done, what files were created/modified]

  ## Remaining Work
  [What still needs to be done to finish the current task]

  ## Code State
  [Is the current code in a working state? Any half-finished functions?
   Any files that need cleanup before continuing?]

  ## Critical Context for Next Agent
  [Decisions made, patterns established, gotchas discovered]

  ## Files to Review Before Continuing
  [List of files modified in this session that should be checked]
  ```
- This file goes to `.agent/handoff.md`
- Also updates working_memory.md and index.md
- Visual: gauge bar turns red, handoff indicator displays

**Tier 3 - HARD STOP (default: 100K tokens on 200K model / 50%)**
- Trigger: cumulative token usage crosses the hard stop threshold
- Action: session terminates. No more API calls.
- The handoff file from Tier 2 should already exist (Tier 2 fires before Tier 3)
- If Tier 2 was somehow skipped, an emergency state dump is attempted
- Visual: gauge bar full red, session ended indicator

**Post-stop code review:**
When `post_stop_review` is enabled in config, before the next agent continues building, a lightweight review agent (can use Haiku - cheap and fast) reads:
1. The handoff file
2. All files modified in the stopped session
3. Checks for: syntax errors, half-finished functions, inconsistencies, quality degradation signs
4. Writes review results to `.agent/progress/safety_review.md`
5. The next build agent reads the safety review before continuing

**Threshold scaling by model:**
Thresholds in config.yml are specified as absolute token counts but should scale with the selected model:

| Model | Warning | Handoff | Hard Stop |
|-------|---------|---------|-----------|
| 200K  | 90,000  | 95,000  | 100,000   |
| 1M    | 450,000 | 475,000 | 500,000   |

Or thresholds can be set as percentages of the model limit for automatic scaling.

**Config settings:**

```yaml
safety:
  warning_threshold_pct: 45       # % of model limit for Tier 1 warning
  handoff_threshold_pct: 47.5     # % of model limit for Tier 2 handoff
  hard_stop_threshold_pct: 50     # % of model limit for Tier 3 kill
  post_stop_review: true          # Run code review after hard stop
  model_limit: 200000             # Current model's context window size
```

---

## Integration with Martin's Build Standards

Martin's platform-agnostic App Builder prompt contains UI/UX standards that should be loaded as part of the constitution files when building applications. These standards go into `agent-os/standards/` and include:

- Mandatory UI components (Modal, ConfirmModal, Toast, Skeleton, EmptyState)
- Banned patterns (no alert(), no confirm(), no console.log for feedback)
- Navigation flow (List → Detail → Create → Edit, never edit-first)
- Responsive design requirements (mobile-first, 44px touch targets)
- Loading states (Skeleton for lists, spinner in buttons)
- Error handling (ErrorBoundary, retry patterns, offline detection)
- Design system tokens (typography, spacing, card patterns)
- File structure conventions
- Polish standards (animations, hover states, accessibility)

**For the base build:** These standards are NOT loaded into the system prompt (that would bloat it). They are stored as files in `agent-os/standards/ui-ux-standards.md` and the system prompt's selective reading rules tell the agent to load them ONLY when doing UI work.

---

## Build Sequence

### Step 1: Create the directory structure
Create all directories and template files listed in Mechanism 2. This is just creating folders and writing markdown files.

### Step 2: Write the system prompt into CLAUDE.md
For Claude Code testing, the system prompt (Mechanism 1) goes into the project's `CLAUDE.md` file. This is what Claude Code automatically loads for context.

### Step 3: Write Martin's standards to agent-os/standards/
Store the UI/UX build standards in the Agent OS standards directory for selective loading during build phases.

### Step 4: Build the context gauge UI component
Reference the existing token tracking implementation in the current workspace for patterns. Build a gauge component that reads API response usage data and displays: visual progress bar (color-coded by zone), token log panel, and session summary stats.

### Step 5: Build the context safety system
Implement the three-tier safety system (warning at 45%, handoff at 47.5%, hard stop at 50%). Wire it to the gauge data. Implement the handoff file writer for Tier 2. Ensure Tier 3 terminates cleanly.

### Step 6: Test the mechanism
Give the agent a small task (build a simple component, write a utility function). Verify:
- Does it write output to files instead of chat?
- Does it keep chat responses under 3 sentences?
- Does it update working_memory.md?
- Does it update index.md when creating new files?
- Does the bridge save work when ending the session?
- Does the resume sequence work on the next session?
- Does the context gauge display accurate token counts?
- Do the safety thresholds trigger at the correct levels?

### Step 7: Iterate
Based on test results, adjust the system prompt language, file formats, settings, and safety thresholds. The config.yml levers allow tuning without code changes.

---

## What This Enables

Once the base mechanism is proven:

1. **The full PRD Machine** can be built using this mechanism (the agent building it has file-based context, so it builds better)
2. **Multi-agent coordination** becomes possible (agents share the same .agent/ file structure)
3. **The commercial SaaS** can be built on top of this foundation
4. **All future features** (notifications, GIF automation, marketing pipeline, swarm) layer on top of this base

The base mechanism IS the product. Everything else is features on top of it.

---

## Notes for the Build Agent

If a fresh agent is executing this build:

1. **Read this entire document first** before creating any files
2. **Create the directory structure** before writing any file contents
3. **The system prompt (Mechanism 1) is the most critical file** - get this exactly right
4. **Test after building** - run through the verification checklist in Step 4
5. **Do not add features beyond what's specified here** - this is an MVP mechanism, not the full system
6. **The file templates should be clean and minimal** - no placeholder content beyond what's specified
7. **Martin's standards go in agent-os/standards/, NOT in the system prompt** - they're loaded selectively

## Relationship to Existing Project

This base build creates files alongside the existing Greptacular project. The `.agent/` directory is new. The `agent-os/` directory is new. The existing project code is not modified except for CLAUDE.md which gets the system prompt additions.
