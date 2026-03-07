# AI Coding Agent Harness Systems: The Complete Playbook

**Source:** Nate B Jones — "The harness vs. the model" (2026)
**Purpose:** Study sheet for understanding how Anthropic (Claude Code) and OpenAI (Codex) architect their agent harnesses, and how AutoForge/DunkStack compares.

---

## TL;DR — The Big Insight

The **model** (Claude, GPT, Gemini) is just a brain in a jar. The **harness** is everything else — where the agent works, what it remembers, what tools it can reach, how it coordinates multiple tasks. Same model inside Claude Code's harness scored **78%** on the CORE benchmark vs. **42%** in a different harness (Small Agents). Same brain, different body, nearly double the performance. The harness is a performance multiplier, not just a wrapper.

---

## Part 1: Side-by-Side Comparison

| Dimension | Claude Code (Anthropic) | Codex (OpenAI) |
|---|---|---|
| **Where it runs** | Your local machine — your terminal, your shell, your env vars, your SSH keys | Isolated cloud container — your code is cloned in, internet disabled by default |
| **Analogy** | Collaborator at the desk next to you | Contractor in a clean room, slides finished work under the door |
| **Execution philosophy** | "Bash is all you need" — Unix primitives (grep, git, npm) chained with pipes | Custom built-in tools — Chrome DevTools protocol, ephemeral observability stack, RPC endpoints |
| **Tool cost strategy** | Store tools as files on filesystem, agent retrieves just-in-time. Only loads tool name + short description (~50-100 tokens), not full instructions (thousands of tokens) | Bidirectional JSON-RPC harness (app server) exposes tools as RPC endpoints; agent calls them programmatically |
| **Memory approach** | "Make the agent remember" — structured artifacts (progress files, JSON task lists, git history) that persist across sessions | "Make the codebase remember" — everything lives in the repo; anything not in the repo doesn't exist to the agent |
| **Cross-session continuity** | Progress file (e.g. `cloud-progress.txt`) + feature list JSON + git commits = institutional memory trail | Architecture docs, alignment threads, product principles all encoded in repo documentation |
| **Context management** | Compacts context window + delegates to sub-agents (each gets own window) | Each task runs in clean sandbox; tasks don't compete for context space |
| **Multi-agent coordination** | Orchestrated collaboration — sub-agents share task lists, can message each other, coordinator manages workflow | Isolated parallelism — each task in own sandbox, coordination through git branches that get merged |
| **Sub-agent model** | Opus for decisions, Haiku for fast exploration/processing large code volumes | Experimental sub-agent support, parallelism "not quite there yet" compared to Claude |
| **Security model** | Trust boundary = your entire workstation. Risk managed through incrementalism + human oversight | Trust boundary = sealed container. Risk managed through isolation + mechanical enforcement |
| **Context file approach** | `CLAUDE.md` files — compounding asset that improves every session | One big `agents.md` failed; switched to progressive disclosure system of focused cross-linked docs |
| **Code quality control** | Incrementalism — one feature per session, forced verification with browser automation (Puppeteer MCP) | Layered architecture with validated dependency directions + linters (written by Codex itself). Linter errors double as remediation instructions |
| **Best for** | Deep understanding of one codebase, planning, orchestration, creative suggestions | Independent parallel tasks, fewer bugs in output code, autonomous operation |
| **MCP support** | Built around MCP from day one; MCP is Anthropic's open standard | Supports MCP but integration philosophy is different — needed custom proxy adapters for Figma/Jira MCPs |

---

## Part 2: Claude Code Harness — Deep Dive

### Core Architecture

- **Runs locally** on your machine with full environment access
- Your terminal, shell, environment variables, SSH keys — all available to the agent
- Trust boundary is your entire workstation

### The Two-Agent Pattern

1. **Initializer Agent** (first session):
   - Reads the app spec
   - Creates a structured feature list
   - Writes an initiation script
   - Creates a progress log
   - Makes a clean commit
   - Sets up the project scaffold

2. **Coding Agent** (every subsequent session):
   - Reads the progress log first
   - Checks git history
   - Runs basic tests to confirm nothing is broken
   - Picks the **next single feature** and implements it
   - Updates progress artifacts
   - Leaves structured artifacts for the next session

### Why One Feature Per Session

- Left alone, models try to build everything at once ("one-shotting")
- They run out of context mid-implementation
- Leave half-finished work the next session has to guess at
- The harness **forces incrementalism** by structuring the task list and prompting for exactly one feature per session

### The JSON Task List (Not Markdown)

- Feature list stored as **JSON**, not markdown
- The model is **less likely to corrupt structured data formats** like JSON
- This is a deliberate harness design choice — format selection affects reliability

### Execution: "Bash Is All You Need"

- Instead of building dozens of specialized tools with long descriptions, the agent uses **composable Unix primitives**:
  - `grep`, `git`, `npm`, pipes, redirects
  - A single line of bash can query a database, filter results, write to a file
- **Why this matters for context window:**
  - GitHub MCP server's 38 tools consume **15,000 tokens** just for tool descriptions
  - GitHub CLI achieves the same functionality with **far fewer tokens**
  - The agent creatively chains Unix primitives to replace many specialized tools
- This keeps the context window **lean** while giving the agent access to everything a human engineer would have

### File-System Tool Storage (KEY INSIGHT)

- **Tools and skills are stored as files on the local file system**
- The agent does NOT load all tool descriptions into the system prompt upfront
- Instead, a **"tool search" tool** lets the agent semantically search available capabilities
- Agent only sees the **short name + description** (~50-100 tokens per skill)
- Full skill definition (potentially thousands of tokens) is read **only when the agent decides to use it**
- This is **"context management as harness design"** — deliberately stingy about tokens
- Skills are essentially **markdown files and scripts** sitting on disk

### Memory and State

- **Progress file** (e.g., `cloud-progress.txt`): read at start, updated at end of every session
- **Feature list JSON**: structured task tracking
- **Git commits**: each session creates commits that form an audit trail
- **CLAUDE.md files**: developer-maintained context that compounds over time
  - The more context accumulates, the better every subsequent session works
  - This is a **compounding asset**

### Context Management

- **Automatic compaction**: summarizes older context to free up window space
- **Sub-agent delegation**: spins up parallel agents, each with their own context window
- **Explore sub-tool**: uses fast/cheap model (Haiku) to process large code volumes, hands results back to Opus for decision-making
- Better when one task needs **deep understanding** of a codebase

### Multi-Agent Coordination

- Sub-agents share task lists and dependency tracking
- Each sub-agent gets a **dedicated context window**
- One builds API, another builds frontend, third writes tests — they can **message each other**
- **Orchestrated collaboration model** with a coordinator managing workflow
- Human stays in the loop as strategic overseer

### Verification

- Uses browser automation (Puppeteer MCP server) to test features end-to-end
- Tests the way a human would — catches bugs that unit tests miss
- Forces verification as part of the harness, not optional

---

## Part 3: OpenAI Codex Harness — Deep Dive

### Core Architecture

- **Runs in isolated cloud containers**
- Your code is **cloned** into the container
- **Internet access disabled** by default
- Agent works independently, slides finished results back
- Trust boundary is the sealed container — inherently safer for autonomous operation

### Origin Story: The Million-Line Product

- OpenAI built a million-line internal product over 5 months using **only Codex agents**
- **Zero lines** of manually written code
- ~1,500 pull requests
- Initially driven by just 3 engineers
- Key lesson: early progress was **slower than expected** — not because Codex couldn't code, but because the **environment was underspecified**
- Agent lacked structure, tools, and feedback mechanisms for high-level goals

### The Repository IS the System of Record

- **Everything lives in the repo**: architecture decisions, alignment threads, product principles
- Anything **not in the repo** is illegible to the agent and therefore **does not exist**
- This is the fundamental philosophy: make the codebase remember

### Why One Big agents.md Failed

- They tried putting everything in one big `agents.md` file
- When everything is marked as important, **nothing is**
- The file "rots immediately in a graveyard of rules"
- Solution: **progressive disclosure system** of focused, cross-linked documentation the agent can navigate

### Execution: Built-In Custom Tools

- **Chrome DevTools Protocol** wired directly into the agent at runtime
  - DOM snapshots, screenshots, navigation
  - Can reproduce UI bugs and validate fixes by actually driving the application
- **Ephemeral observability stack** per agent:
  - Victoria Logs + Victoria Metrics spin up per git worktree
  - Disappear when work is done
  - Agent can query logs and metrics in-session
  - "Make the service start in under 800ms" becomes a **testable acceptance criterion**
- **Bidirectional JSON-RPC harness** (app server):
  - Exposes tools like git, test runners, Chrome dev tools, app logs, metrics as RPC endpoints
  - Agent calls into these programmatically
  - Can spin up per-worktree instances, capture screenshots, DOM snapshots

### Code Quality: The Entropy Problem

- Codex **replicates whatever patterns exist** in the repo, including bad ones
- This leads to inevitable drift — "AI slop"
- Initially tried **"Slop Fridays"**: manual cleanup every Friday — didn't scale
- Scalable solution:
  - Encoded **golden principles** into the repo
  - Built **automated cleanup processes**: background Codex tasks scan for deviations
  - These tasks open **targeted refactoring PRs**
  - The repo eventually **polices itself**

### Linters as Teaching Tools

- Enforced rigid layered architecture with validated dependency directions
- Limited permissible edges between layers
- **Linters written by Codex itself**
- Linter error messages **double as remediation instructions**
- When agent violates an architectural rule, the error tells it exactly how to fix it

### Context Management

- Each task runs in a **clean sandbox** — tasks don't compete for context space
- Better when running **independent parallel tasks**
- Can burn tokens on individual tasks without polluting a central context window

### Multi-Agent Coordination

- Each task runs in its **own isolated sandbox**
- Coordination happens through the **codebase itself** — git branches that get merged
- Agents **can't interfere** with each other
- Can't access each other's state
- **Cannot cascade failures**
- Experimental sub-agent support improving but not yet at Claude Code's level

### Security

- Isolation model is **inherently safer** for autonomous operation
- No access to your local machine
- No access to your SSH keys, env vars, etc.
- The sandbox is the security model

---

## Part 4: File System as Tool Storage — The Pattern That Matters

This is the pattern Nate describes that directly relates to what AutoForge/DunkStack is doing. Here's every mention of using the file system for tools or context:

### Anthropic's Approach

1. **Skills as filesystem files**: Claude Code stores tools and skills as **markdown files and scripts on the local file system**. The agent doesn't load them all into the system prompt.

2. **Just-in-time retrieval**: A "tool search" tool lets the agent **semantically search** available capabilities. It only sees short names/descriptions (~50-100 tokens). Full definitions load only on use.

3. **Why this works**: Tool descriptions are **expensive in context window**. The GitHub MCP server's 38 tools eat 15,000 tokens just sitting there. By storing tools as files and loading on demand, the harness stays lean.

4. **CLAUDE.md as persistent context**: Developer-maintained files that accumulate project knowledge. Compounding asset — every session benefits from everything written before.

5. **Progress files as state**: Structured text files (`cloud-progress.txt`) that maintain cross-session memory without burning context window.

### OpenAI's Approach

1. **Repo as system of record**: Everything that matters lives as files in the repo. Architecture docs, principles, alignment threads — all files.

2. **Progressive disclosure documentation**: Instead of one big file, a network of focused, cross-linked docs the agent navigates. Agent reads only what it needs.

3. **Linter configs as behavioral rules**: Architectural rules encoded as linter configurations (files in the repo). Error messages serve double duty as instructions.

4. **Golden principles as repo files**: Quality standards encoded as documentation in the repo that background agents scan against.

### What AutoForge/DunkStack Is Doing Differently

Both Claude Code and Codex use the file system to hold tools and context. But they use it primarily for **storage and retrieval** — the file system is a library the agent checks out books from.

AutoForge's DunkStack goes further: **the file system IS the operating system for the agent**. It's not just holding tools there — it's:
- Running the entire agent orchestration through file-based state
- Using file-based progress tracking (features.db, progress files)
- Storing prompts as file templates with fallback chains
- Managing multi-agent coordination through file-based locks and state
- Using the file system as the communication layer between agents

This is the same principle (files are cheap for context, tools are expensive) taken to its logical extreme: if files are the most context-efficient way to give agents capabilities, then build the entire system around file-based state management.

---

## Part 5: The Lock-In Problem

### How Lock-In Compounds

Example from Calvin French-Owen's workflow evolution:
1. Started with `/commit` — consistent commit and push
2. Added `/worktree` — agents in separate work trees
3. Added `/implement` — planning first, then implementing
4. Started chaining implement calls
5. Added `/implement-all` — batch implementation
6. **6+ layers of workflow automation**, each built on the previous one

Each layer is **specific to Claude Code's harness** — its skill system, context forking, sub-agent model. Moving to a different harness means **rebuilding the entire chain from scratch** in an architecture that may not support the same abstractions.

### What Transfers and What Doesn't

| Asset | Transfers? | Why |
|---|---|---|
| CLAUDE.md files | No | Codex looks at repo docs, not CLAUDE.md |
| Custom skills/commands | No | Architecture-specific abstractions |
| MCP server configs | Partially | Protocol is shared, integration depth differs |
| Repo documentation | Partially | Both use it but navigate it differently |
| Git history | Yes | Universal |
| Team habits & processes | No | Built around specific harness patterns |

### The Cloud Wars Analogy

- 2010: AWS and Azure "both offer VMs and object storage" — technically correct, strategically wrong
- 2026: Claude Code and Codex "both write code with AI" — same mistake
- Organizations that understood AWS Lambda vs Azure Functions made better decisions
- Same fluency needed now for AI harness architectures

---

## Part 6: Practical Routing — Who Uses What and When

### Calvin French-Owen's Hybrid Workflow

| Phase | Tool | Why |
|---|---|---|
| Planning | Claude Code | More creative, suggests things developer forgot |
| Orchestration | Claude Code | Sub-agents, terminal access, codebase exploration |
| Understanding code | Claude Code | Deep codebase comprehension |
| Implementation | Codex | "The code just straight up has fewer bugs" |
| Review | Codex reviewing Claude's work | Catches mistakes Claude missed |

### When to Use Which (General Guidance)

| Scenario | Better Harness | Reason |
|---|---|---|
| Deep codebase understanding | Claude Code | Context management, sub-agent exploration |
| Creative problem solving | Claude Code | Multi-agent collaboration, orchestration |
| Parallel independent tasks | Codex | Isolation prevents context pollution |
| Autonomous long-running work | Codex | Sandbox is inherently safer |
| Working with local tools/env | Claude Code | Full machine access |
| Security-sensitive operations | Codex | Sealed container, no local access |
| Cross-checking work | Use both | Different architectures catch different bugs |

---

## Part 7: Key Takeaways for AutoForge Strategy

1. **File-system-as-tool-storage is validated by both major players.** You're not doing something weird — you're doing something both Anthropic and OpenAI independently arrived at. The difference is you're taking it further.

2. **The harness matters more than the model.** Same model, 78% vs 42% performance. Your harness innovations (DunkStack, multi-provider support, custom orchestration) are the real competitive advantage.

3. **You're in a unique position** because you're bringing Claude, Codex, AND Gemini into one system. Neither Anthropic nor OpenAI is building for multi-provider orchestration — they're each optimizing for their own model. You're building the harness that works across all three.

4. **Context window frugality is the game.** Both companies learned that cramming tools into the system prompt is wasteful. File-based just-in-time loading is the winning pattern. Your DunkStack approach of running the entire system through files is the aggressive version of this same insight.

5. **Incrementalism wins.** Both harnesses force one-feature-at-a-time work. Your feature-by-feature approach with features.db is aligned with what both companies found works best.

6. **The repo-as-memory vs agent-as-memory split doesn't have to be either/or.** You can do both — let the agent remember (progress files, CLAUDE.md) AND make the codebase remember (repo docs, linter configs). AutoForge already does elements of both.

7. **Multi-agent coordination is where Claude Code leads.** If you're routing creative/planning work to Claude and implementation to Codex/Gemini, you're doing what the power users are doing.

---

*Document created: 2026-03-07*
*Source: Nate B Jones — AI Harness Systems Analysis*
*For: AutoForge/DunkStack development strategy*
