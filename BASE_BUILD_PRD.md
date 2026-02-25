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

## Mechanism 8: Decisions Log (decisions.log)

### What It Does
An append-only file where the agent logs every non-obvious decision with reasoning. Unlike working_memory.md (which tracks current state) or build_log.md (which tracks what was built), decisions.log tracks WHY choices were made.

### Why It's Critical
The single most wasteful behavior in long agent sessions is revisiting settled questions. The agent picks library X in turn 5, then by turn 40 has forgotten why it picked X over Y and either re-evaluates (wasting tokens) or picks Y instead (creating inconsistency). Decisions.log prevents this by being a quick-reference file the agent checks before making any architectural or tooling choice.

For swarm architecture (future): this file becomes the shared brain. When Agent B needs to make a decision that Agent A already made, it reads decisions.log instead of re-analyzing from scratch. One agent's learning becomes every agent's learning.

### Technical Specification

**File: `.agent/progress/decisions.log`**

```markdown
# Decisions Log
> Append-only. One entry per decision. Agent checks this before making architectural choices.
> Format: ## [timestamp] CATEGORY: Brief Decision Title

## [2026-02-24 14:15] DATABASE: SQLite over PostgreSQL for MVP
**Choice:** SQLite
**Alternatives considered:** PostgreSQL, MongoDB
**Reasoning:** MVP doesn't need concurrent multi-user access. SQLite is zero-config, embedded, and sufficient for single-agent builds. Migrate to PostgreSQL when/if multi-user support is added.
**Confidence:** High
**Revisit if:** Requirements change to multi-user or concurrent agent writes to same DB

## [2026-02-24 15:30] ARCHITECTURE: Server-side rendering over SPA
**Choice:** Next.js SSR
**Alternatives considered:** Vite SPA, Remix
**Reasoning:** SEO requirements from spec section 3.2. SPA would require separate SSR layer later.
**Confidence:** Medium - depends on whether SEO requirement is hard or soft
**Revisit if:** SEO requirement is dropped or changed to optional
```

**System prompt addition:**

```markdown
## Decision Logging

Before making any non-trivial choice (library selection, architecture pattern,
data model design, API structure), FIRST check .agent/progress/decisions.log
to see if this decision was already made.

If it was: follow the existing decision unless the circumstances have explicitly changed.
If it wasn't: make the decision, then immediately append an entry to decisions.log.

A "non-trivial choice" is anything where a reasonable developer might pick
a different option. If there's only one obvious answer, don't log it.
```

**Integration:** Add `decisions.log` to the file structure in Mechanism 2 and to the index.md template.

---

## Mechanism 9: Scope Boundary File (scope_boundary.md)

### What It Does
A file that explicitly defines what IS and IS NOT in scope for the current build phase. The agent reads this to prevent scope creep, gold-plating, and feature drift.

### Why It's Critical
By feature 15 of a 30-feature build, agents reliably start drifting. They gold-plate feature 3 instead of moving forward. They add error handling for scenarios that can't happen. They refactor working code that isn't part of the current task. They add "nice to have" features that weren't in the spec. This costs tokens, introduces bugs, and slows the build.

The working_memory.md tracks WHAT the agent is doing. The scope_boundary.md tracks what it SHOULD and SHOULDN'T be doing. These are different concerns.

### Technical Specification

**File: `.agent/scope_boundary.md`**

```markdown
# Scope Boundary
Last updated: [timestamp]
Phase: Base Build MVP

## IN SCOPE - Build These
- [Feature list from the current build phase]
- [Specific deliverables expected]
- [Quality standards that apply]

## OUT OF SCOPE - Do NOT Build These
- Full PRD machine pipeline (future phase)
- Swarm multi-agent coordination (future phase)
- Marketing/GIF automation (future phase)
- SaaS authentication/billing (future phase)
- Performance optimization beyond "it works" (future phase)

## DEFER - Note But Don't Act
- If you discover a needed improvement, log it to decisions.log but don't implement it
- If you see code that could be refactored, note it in progress/build_log.md but leave it
- If a feature would be "nice to have," add it to .agent/output/backlog.md

## QUALITY BOUNDARY
- Code must work and pass lint. That's the bar for MVP.
- Don't add tests unless the spec requires them for this phase
- Don't add documentation beyond code comments
- Don't optimize for edge cases that the spec doesn't mention

## STOP SIGNALS
If you find yourself doing any of these, STOP and return to the current task:
- Adding error handling for impossible scenarios
- Refactoring code that already works
- Building a utility/helper for something used once
- Adding configuration for something that has one value
- Writing more than 3 sentences in a chat response
```

**System prompt addition:**

```markdown
## Scope Awareness

Read .agent/scope_boundary.md at the start of every session and after every
bridge resume. Before starting any new sub-task, verify it's listed in the
IN SCOPE section. If it's not, check if it's in OUT OF SCOPE or DEFER.

If you catch yourself working on something not in scope, STOP immediately.
Log what you noticed in progress/build_log.md and return to the current
in-scope task.
```

**Integration:** Add `scope_boundary.md` to the file structure in Mechanism 2 and to the index.md template. The human populates this file when defining a build phase. The agent reads it but only modifies the DEFER section (to log deferred items).

---

## Mechanism 10: Structured Change Tracking (changes.md)

### What It Does
A per-session log that records not just WHAT files changed, but WHY and HOW. Goes beyond git diff by capturing the semantic intent behind each change. This is the structured diff system that makes bridge resumes and multi-agent handoffs dramatically more efficient.

### Why It's Critical
When an agent resumes from a bridge or another agent picks up work, the first thing it needs to understand is "what changed since I last looked?" Git diff tells you the WHAT — lines added, lines removed. But it doesn't tell you the WHY — "I added JWT validation because feature 7 requires persistent sessions" or "I changed the User model to add a refresh_token field so the auth middleware can validate tokens without a database round-trip."

Without semantic change tracking, the resuming agent has to READ the changed files and INFER the reasoning. That's expensive (tokens) and error-prone (might misinterpret the intent). With structured changes, the agent reads a 10-line summary and knows exactly what happened and why.

### Technical Specification

**File: `.agent/progress/changes.md`**

```markdown
# Change Log
> Append-only. One entry per significant change. Written immediately after each change.

## [2026-02-24 14:30] Modified: src/models/user.py
**What changed:** Added `refresh_token` field to User model
**Why:** Feature #7 (persistent sessions) requires token refresh without re-auth
**Impact:** Migration needed. Auth middleware (src/middleware/auth.py) will need updating next.
**Decision ref:** See decisions.log [2026-02-24 14:15] AUTH pattern

## [2026-02-24 14:45] Created: src/middleware/auth.py
**What changed:** New JWT validation middleware with refresh token support
**Why:** Feature #7 - validates both access and refresh tokens
**Impact:** Must be registered in app.py route configuration
**Depends on:** User model refresh_token field (done), JWT_SECRET env var (configured in .env.example)

## [2026-02-24 15:10] Modified: src/app.py
**What changed:** Registered auth middleware, added /api/auth/* routes
**Why:** Wiring up feature #7 components
**Impact:** All /api/* routes now require authentication except /api/auth/login and /api/auth/register
**Testing note:** Existing tests will fail until test fixtures include auth tokens
```

**System prompt addition:**

```markdown
## Change Tracking

After EVERY file creation or significant modification, append an entry
to .agent/progress/changes.md with:
- What file changed and what was modified
- Why the change was made (link to feature or decision)
- What other files are impacted by this change
- Any testing implications

Skip logging for trivial changes (fixing a typo, updating a comment).
Log everything else. When in doubt, log it.

On bridge resume, read changes.md BEFORE reading any source files.
The change log tells you what to focus on without re-reading everything.
```

**Integration:** Add `changes.md` to the file structure in Mechanism 2 and to the index.md template. The bridge resume sequence (Mechanism 5) should read changes.md as step 2 (after index.md, before working_memory.md) so the agent knows what's different before re-reading state.

---

## Updated File Structure (Mechanisms 2 + 8 + 9 + 10)

With the three new mechanisms, the complete `.agent/` directory structure becomes:

```
.agent/
├── index.md
├── working_memory.md
├── scope_boundary.md          ← NEW: What's in/out of scope
├── bridge.md                  (temporary, created by bridge mechanism)
├── system_prompt.md
├── comms/
│   ├── to_human.md
│   ├── from_human.md
│   └── control.md
├── knowledge/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── progress/
│   ├── build_log.md
│   ├── decisions.log          ← NEW: Why choices were made
│   └── changes.md             ← NEW: Semantic change tracking
├── settings/
│   └── config.yml
└── features.db                (created by dependency system)
```

---

## Future Version: Ultimate System Additions

> These additions are NOT part of the base build. They are documented here for reference
> when building the full version of the system after the base mechanism is proven.

### Addition 1: Semantic Compression on Working Memory

**Problem:** As projects grow, working_memory.md and changes.md get long. Reading them consumes more tokens each session.

**Solution:** Implement time-based compression. Recent entries (last 2-3 sessions) stay in full detail. Older entries auto-compress to one-line summaries. Entries older than N sessions compress to category-level summaries.

**Example:**
```markdown
## Recent (full detail)
- [2026-02-25 14:30] Added refresh_token to User model for feature #7...

## Earlier (compressed)
- Session 4: Completed features #5-#7 (auth system). Key files: auth.py, user.py, middleware.
- Session 3: Completed features #3-#4 (database layer). Chose SQLite (see decisions.log).

## History (category summary)
- Sessions 1-2: Project setup, dependency installation, base configuration.
```

**Implementation:** A compression function runs at session start, before bridge load. It reads the full files, applies time-based rules, and writes compressed versions. Original content preserved in a `.agent/archive/` directory if needed for deep review.

### Addition 2: Agent Self-Verification Loops

**Problem:** Agents drift from actual state over time. They THINK the code is structured one way, but it's actually different. This causes bugs that compound.

**Solution:** Before each major action (starting a new feature, making an architectural change), the agent writes a "state assertion" file: "I believe the current state is X." Then it reads the actual files to verify. If there's a mismatch, it stops and reconciles before proceeding.

**Example flow:**
```
Agent thinks: "The User model has fields: id, name, email"
Agent writes assertion to .agent/progress/state_check.md
Agent reads src/models/user.py
Actual: "User model has fields: id, name, email, refresh_token, created_at"
Mismatch detected → Agent updates its understanding before modifying the model
```

**Cost:** ~200-400 tokens per verification. Worth it for preventing compound errors.

### Addition 3: Swarm Role Specialization with Shared Context

**Problem:** Multiple agents doing the same general task duplicate context loading. Each agent reads the full project state, does some work, writes results. Context efficiency is no better than a single agent.

**Solution:** Specialize agents by role, each with optimized context loading:

| Role | Reads | Writes | Context Budget |
|------|-------|--------|---------------|
| **Librarian** | All files, full index | index.md, knowledge/ | 60K focused on file organization |
| **Builder** | Current feature + deps only | Source code, changes.md | 60K focused on implementation |
| **Critic** | Changed files + test results | progress/review.md | 40K focused on quality |

The Librarian answers "where is X?" questions so the Builder never wastes context on file discovery. The Critic never holds build context — it only sees diffs and test output. Each agent's context window is optimized for their role.

**Communication:** Via the shared `.agent/` file structure. Builder writes changes.md → Critic reads changes.md. Critic writes review.md → Builder reads review feedback. Librarian updates index.md → everyone benefits.

### Addition 4: Confidence Scoring on File Reads

**Problem:** The agent reads a file summary and makes a decision based on it. Later, the full file reveals the summary missed something critical. The decision was wrong, and now there's cascading damage.

**Solution:** Track read depth for every file access. Tag downstream decisions with the confidence level they were made at.

**Levels:**
- `FULL` — Read the entire file, line by line
- `SECTION` — Read specific sections (used heading structure)
- `SUMMARY` — Read a compressed/summarized version
- `INDEX` — Only saw the file name and description in index.md

**Example in decisions.log:**
```markdown
## [2026-02-25 10:00] API: REST over GraphQL
**Read depth:** FULL on requirements.md, SECTION on existing_api.py (lines 1-50 only)
**Confidence adjustment:** Medium — didn't read full existing API, may miss compatibility issues
**Revisit trigger:** If integration tests fail on existing API endpoints
```

**Benefit:** When something goes wrong, the system can trace back to decisions made on partial reads and flag them for re-evaluation with full reads. Prevents the expensive "re-read everything and start over" pattern.

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
