# YT Lab Infrastructure Framework: The Modular Tool Engine

> **Status**: Foundational Design Document
> **Date**: March 13, 2026
> **Purpose**: Operational framework for evolving YT Lab from a single-tool builder into a modular, self-growing infrastructure system

---

## Mission Statement

Turn YT Lab from "video in → tool out" into a **modular tool engine** where every tool it builds becomes a connectable piece of a larger system. Tools chain front-to-back, share data sideways, improve themselves over time, and wrap existing open-source software instead of rebuilding from scratch. The human sees a clear dashboard. The AI does the wiring. The result: feed in ideas, get back a growing army of interconnected tools that operate on autopilot.

---

## What We Proved (Current State)

YT Lab today works like this:

1. **Input**: YouTube video URL → transcript extraction → metadata capture
2. **Processing**: Claude Opus extracts strategy steps from the transcript
3. **Blueprint**: Steps get classified (research/generation/action/manual), APIs detected, prompts rewritten
4. **Output**: Google Sheet with a chain config — each row is a step with a prompt template
5. **Deploy**: Sheet gets themed, formatted, and published to Google Drive

**What works incredibly well:**
- Video transcripts are essentially curated, step-by-step process descriptions
- 80% of the tool gets built right from the video because good creators walk through their exact process
- The chain config model (step → prompt → input source → output) is clean and proven
- Batch processing lets you pump multiple videos through at once

**What's missing:**
- Tools are islands — no way to connect Tool A's output to Tool B's input
- No auto-research to fill the remaining 20% the video didn't cover
- No ongoing improvement — tool is frozen at build time
- No GitHub/open-source integration — building prompts when real software already exists
- No dashboard showing how tools connect and interact

---

## The Paradigm Shift

### From: Single Tool Builder
Video → Process Steps → Prompt Chain → Google Sheet (done)

### To: Modular Infrastructure Engine
Video → Research-Enhanced Blueprint → Connectable Module → Wired Into System → Self-Improving Over Time

The key insight: **these aren't standalone tools, they're LEGO pieces**. The value isn't one tool — it's 10-20 tools wired together into a system that does what no single tool can.

---

## Architecture: The Five Layers

### Layer 1: Enhanced Ingestion (The Research Engine)

**Current**: Video transcript → immediate tool build
**New**: Video transcript → deep research → gap analysis → human approval → enriched build

#### How it works:

1. **Video comes in** — transcript extracted as usual
2. **Research Engine activates** — instead of immediately building, it:
   - Searches the web for related tools, techniques, alternatives
   - Scours GitHub for open-source repos that do parts of what the video describes
   - Finds competing approaches and newer technologies
   - Cross-references against our existing tool registry
3. **Gap Report generated** — presented to the human:
   - "The video covered X, Y, Z"
   - "Research found these additional components: A, B, C"
   - "GitHub has these repos that already do parts of this: [repo1], [repo2]"
   - "Recommendation: Use [repo] for the heavy lifting, build wrapper for the rest"
4. **Human reviews quickly** — short descriptions, checkboxes, approve/reject in seconds
5. **Enriched blueprint built** — includes everything the video said PLUS the approved additions

#### Research Depth Levels:
- **Quick** (default for batch): 1 web search, 1 GitHub search, compare against registry
- **Standard** (default for single): 3-5 searches, deep GitHub scan, API pricing research
- **Deep** (on request): 10+ searches, academic papers, patent search, full competitive landscape

### Layer 2: The Connection System (Front-Back + Sideways)

This is the hard part and the most valuable part. Three connection types:

#### Type A: Chain Connections (Front-to-Back) ← EASY
Tool A finishes → output feeds into Tool B as input

```
[Content Generator] → [Content Formatter] → [Social Media Publisher] → [Ad Campaign Creator]
```

**Implementation**: Already basically works with the chain config model. Each tool's final output column becomes the next tool's input. We just need:
- Standardized output format per tool (JSON schema)
- A "chain definition" that says "Tool A output → Tool B input"
- A runner that executes the chain sequentially

**Data model addition to ChainConfigRow:**
```
output_schema: {}        # What this tool produces
accepts_input_from: []   # Tool IDs that can feed into this
feeds_output_to: []      # Tool IDs this can feed into
```

#### Type B: Sideways Connections (Data Sharing) ← THE HARD ONE
Tool C needs a piece of data from Tool A, but Tool C isn't in Tool A's chain. It's running independently but needs to pull from Tool A's results.

```
[Content Generator] → [Formatter] → [Publisher]
        ↓ (sideways)
[Analytics Dashboard] pulls content topics
        ↓ (sideways)
[Ad Campaign Creator] pulls performing topics from Analytics
```

**Implementation options:**

1. **Shared Data Bus** (recommended)
   - Central key-value store where tools publish named outputs
   - Any tool can subscribe to any named output
   - Tools declare what they publish and what they consume
   - Like an internal API but simpler — just read/write named data

2. **Event-Driven**
   - Tools emit events when they produce output
   - Other tools listen for specific event types
   - More complex but more real-time

3. **Endpoint Registry**
   - Each tool exposes REST-like endpoints
   - Tools call each other's endpoints
   - Most flexible but most complex

**Recommendation**: Start with Shared Data Bus. It's the simplest, covers 90% of use cases, and the human can see exactly what data is flowing where. Event-driven can be added later for real-time needs.

**Data Bus schema:**
```json
{
  "bus_id": "workspace_123",
  "channels": {
    "content_topics": {
      "producer": "tool_content_gen_001",
      "data_type": "string[]",
      "last_updated": "2026-03-13T10:00:00Z",
      "value": ["AI productivity", "code automation", "tool building"]
    },
    "top_performing_ads": {
      "producer": "tool_ad_analytics_002",
      "data_type": "object[]",
      "last_updated": "2026-03-13T09:00:00Z",
      "value": [{"topic": "AI productivity", "ctr": 0.045}]
    }
  },
  "subscriptions": {
    "tool_ad_creator_003": ["content_topics", "top_performing_ads"],
    "tool_analytics_002": ["content_topics"]
  }
}
```

#### Type C: Component Injection (Parts of Tools Sharing)
Not the whole tool's output — just a specific component or sub-step result needs to be shared.

**Implementation**: Each step in a chain config can optionally publish its individual output to the data bus, not just the final output. This means any step in any tool can be a data source for any other tool.

### Layer 3: The GitHub Integration Layer (CLI Wrapping)

This is the game-changer. Instead of building everything from prompt chains, **find existing open-source software and wrap it**.

#### The Flow:

1. **Video describes a process** (e.g., "here's how to obfuscate JavaScript code")
2. **Research Engine finds GitHub repos** that already do this (e.g., `javascript-obfuscator`)
3. **CLI Wrapper Generator** creates a controller around the repo:
   - Installs the tool (npm install / pip install / etc.)
   - Maps video steps to CLI commands
   - Creates preset configurations based on the video's recommendations
   - Builds an AI controller that runs the tool with the right flags/options
4. **Result**: Instead of a prompt chain that talks about obfuscation, you get **actual obfuscation software controlled by AI templates**

#### CLI Wrapper Architecture:
```
┌─────────────────────────────────┐
│  AI Controller Layer            │
│  (prompts + decision logic)     │
├─────────────────────────────────┤
│  CLI Wrapper                    │
│  (maps commands, handles I/O)   │
├─────────────────────────────────┤
│  Open Source Tool               │
│  (the actual software)          │
└─────────────────────────────────┘
```

#### Tool Type Classification:
After research, each tool gets classified:

- **Prompt-Only**: No existing software — build with prompt chains (current behavior)
- **Wrapper**: Good open-source tool exists — wrap it with CLI controller
- **Hybrid**: Some parts have software, some need prompts — combine both
- **Orchestrator**: Multiple tools need to be coordinated — build a conductor

#### GitHub Scraping Engine:
- Searches GitHub for repos matching tool requirements
- Evaluates: stars, recent activity, documentation quality, CLI support
- Checks if a CLI wrapper tool exists (like the Hong Kong tool you mentioned)
- Presents top 3-5 options to human for selection
- Caches results in the tool registry for cross-reference

### Layer 4: The Continuous Improvement Engine (The Loop)

Tools shouldn't be frozen at build time. They should get better.

#### Auto-Improvement Loop:
```
┌─→ Tool runs normally
│   ↓
│   Monitor results + new tech landscape
│   ↓
│   Scraper finds: new technique / better library / updated API
│   ↓
│   Cross-reference: "This would improve Tool X"
│   ↓
│   Generate improvement proposal
│   ↓
│   Human approves (quick checkbox)
│   ↓
│   Auto-apply improvement
│   ↓
└── Tool runs better
```

#### Components:

1. **Tech Radar Scraper**
   - Runs daily/weekly
   - Searches GitHub trending, Hacker News, Product Hunt, ArXiv
   - Focuses on: new tools, new APIs, new techniques, updated libraries
   - Stores findings in a knowledge base

2. **Cross-Reference Engine**
   - Knows every tool in the registry: what it does, what tech it uses, what its weaknesses are
   - When new tech comes in, checks: "Does this improve any existing tool?"
   - Generates match reports: "New library X could replace Step 3 in Tool Y, making it 2x faster"

3. **Improvement Queue**
   - Prioritized list of proposed improvements
   - Each entry: which tool, what change, expected benefit, effort level
   - Human reviews and approves in batch

4. **Auto-Patcher**
   - For approved improvements: updates the tool's chain config / CLI wrapper / prompts
   - Creates a new version (tools are versioned)
   - Runs basic validation before deploying

### Layer 5: The Dashboard (Human Sees, AI Executes)

The dashboard serves two audiences:
- **Human**: Needs to see the big picture, make quick decisions, understand connections
- **AI**: Needs to know what tools exist, how they connect, what needs work

#### Dashboard Views:

1. **System Map** (Primary View)
   - Visual graph of all tools and their connections
   - Chains shown as left-to-right flows
   - Sideways connections shown as dotted lines
   - Color coding: green = running, yellow = needs attention, red = broken
   - Click any tool to see details, click any connection to see data flowing

2. **Tool Registry**
   - List of all tools with status, last run, improvement proposals
   - Filter by: type (prompt/wrapper/hybrid), status, category
   - Quick actions: run, edit, connect, archive

3. **Connection Builder**
   - Drag-and-drop interface to wire tools together
   - Shows available outputs from each tool
   - Shows required inputs for each tool
   - Auto-suggests connections based on data type matching

4. **Improvement Feed**
   - Stream of proposed improvements from the Loop engine
   - Quick approve/reject interface
   - Shows impact estimates

5. **Execution Monitor**
   - Live view of running chains
   - Data flowing between tools in real-time
   - Error highlighting and recovery options

---

## The First 10 Tools (Foundation Set)

These are the tools that build and protect the system itself:

| # | Tool | Type | Purpose |
|---|------|------|---------|
| 1 | **App Shield** (Obfuscator) | Wrapper | Protect every built app from reverse engineering. Wraps `javascript-obfuscator`. Every app that comes out of YT Lab gets this applied automatically. |
| 2 | **Research Engine** | Hybrid | The deep-research component from Layer 1. Scours web + GitHub for every new tool build. |
| 3 | **GitHub Scout** | Wrapper | Finds and evaluates open-source repos. Wraps GitHub API + `gh` CLI. |
| 4 | **CLI Wrapper Factory** | Prompt-Only | Generates CLI wrappers for open-source tools. The meta-tool that makes other tools. |
| 5 | **Data Bus Manager** | Prompt-Only | Creates and manages the shared data bus for sideways connections. |
| 6 | **Chain Builder** | Prompt-Only | Wires tools together into front-to-back chains. |
| 7 | **Tech Radar** | Hybrid | Daily scraper for new technologies, libraries, tools. Feeds the improvement engine. |
| 8 | **Cross-Reference Engine** | Prompt-Only | Matches new tech findings against existing tools for improvement opportunities. |
| 9 | **Blueprint Enhancer** | Prompt-Only | Takes a basic video blueprint and enriches it with research findings before build. |
| 10 | **System Dashboard Generator** | Wrapper | Builds and maintains the visual dashboard for the tool network. |

**Build order**: 1 (protect everything) → 2+3 (better research) → 4 (wrap open source) → 5+6 (connections) → 7+8 (self-improvement) → 9 (better builds) → 10 (visibility)

---

## Implementation: Data Models

### Tool Module (extended from current GeneratedTool)

```python
class ToolModule:
    tool_id: str
    tool_name: str
    tool_type: str          # "prompt_only" | "wrapper" | "hybrid" | "orchestrator"
    status: str             # "draft" | "active" | "improving" | "archived"
    version: int

    # Current fields
    chain_config: list[ChainConfigRow]
    detected_apis: list[str]
    theme: ThemeConfig

    # NEW: Connection interface
    input_schema: dict      # What this tool accepts
    output_schema: dict     # What this tool produces
    published_channels: list[str]   # Data bus channels this tool writes to
    subscribed_channels: list[str]  # Data bus channels this tool reads from

    # NEW: CLI wrapper (if type is "wrapper" or "hybrid")
    wrapped_repo: str       # GitHub repo URL
    install_command: str    # How to install the wrapped tool
    cli_mappings: list[dict]  # Maps steps to CLI commands
    presets: dict           # Preset configurations from video recommendations

    # NEW: Lineage
    source_video_id: str
    research_findings: list[dict]  # What research added beyond the video
    improvement_history: list[dict]  # Changes made by the loop engine

    # NEW: Connection metadata
    chain_memberships: list[str]  # Which chains this tool belongs to
    upstream_tools: list[str]     # Tools that feed into this
    downstream_tools: list[str]   # Tools this feeds into
    sideways_connections: list[dict]  # Sideways data sharing
```

### Chain Definition

```python
class ToolChain:
    chain_id: str
    chain_name: str
    description: str
    tools: list[str]        # Ordered list of tool_ids
    connections: list[dict]  # How each tool connects to the next
    trigger: str            # "manual" | "scheduled" | "event"
    schedule: str           # Cron expression if scheduled
    status: str             # "active" | "paused" | "draft"
```

### Data Bus Channel

```python
class DataBusChannel:
    channel_name: str
    data_type: str          # JSON schema reference
    producer_tool_id: str
    subscriber_tool_ids: list[str]
    last_value: Any
    last_updated: datetime
    retention: str          # "latest" | "all" | "last_n"
    history: list[dict]     # Past values if retention != "latest"
```

### Improvement Proposal

```python
class ImprovementProposal:
    proposal_id: str
    target_tool_id: str
    source: str             # "tech_radar" | "cross_reference" | "manual"
    finding: str            # What was found
    proposed_change: str    # What would change
    expected_benefit: str   # Why it's worth doing
    effort: str             # "trivial" | "small" | "medium" | "large"
    status: str             # "proposed" | "approved" | "applied" | "rejected"
    created_at: datetime
    reviewed_at: datetime
```

---

## Implementation: New Endpoints Needed

### Connection Management
```
POST   /api/tools/{tool_id}/connections          # Create connection
GET    /api/tools/{tool_id}/connections          # List connections
DELETE /api/tools/{tool_id}/connections/{conn_id} # Remove connection
```

### Chain Management
```
POST   /api/chains                # Create chain
GET    /api/chains                # List chains
GET    /api/chains/{chain_id}     # Get chain detail
POST   /api/chains/{chain_id}/run # Execute chain
DELETE /api/chains/{chain_id}     # Delete chain
```

### Data Bus
```
GET    /api/bus/channels                    # List all channels
GET    /api/bus/channels/{name}             # Get channel value
POST   /api/bus/channels/{name}/subscribe   # Subscribe tool to channel
DELETE /api/bus/channels/{name}/subscribe    # Unsubscribe
```

### Research Engine
```
POST   /api/research/deep-scan     # Full research for a video/topic
GET    /api/research/github-scan   # Search GitHub repos
POST   /api/research/gap-report    # Generate gap analysis
POST   /api/research/approve       # Human approves research findings
```

### Improvement Engine
```
GET    /api/improvements                        # List proposals
POST   /api/improvements/{id}/approve           # Approve proposal
POST   /api/improvements/{id}/reject            # Reject proposal
POST   /api/improvements/scan                   # Trigger manual scan
```

---

## The Human Workflow (Speed is Everything)

Every interaction is designed for speed because the owner has limited time:

### Building a New Tool (Enhanced Flow)
1. **Paste YouTube URL** → same as today, 30 seconds
2. **Research runs automatically** → 60-90 seconds in background
3. **Gap Report appears** → short bullet points with checkboxes
4. **Owner scans and checks** → 15-30 seconds
5. **"Build It" button** → enriched tool builds with everything included
6. **Tool auto-registers** in the system with connection interfaces defined

### Connecting Tools
1. **Open System Map** → see all tools visually
2. **Drag connection** from Tool A output to Tool B input
3. **System validates** data types match (or suggests transformation)
4. **Connection saved** → tools are now wired

### Reviewing Improvements
1. **Improvement Feed** shows new proposals (badge count on dashboard)
2. **Each proposal**: one-line summary + "Approve" / "Reject" button
3. **Batch approve** for obvious wins
4. **Auto-applied** overnight or on next run

---

## Priority Order for Building This

### Phase 1: Foundation (Build First)
- [ ] Tool Module data model (extend GeneratedTool)
- [ ] App Shield obfuscation wrapper (protects everything from day 1)
- [ ] Basic chain connections (front-to-back)
- [ ] Tool registry with connection metadata

### Phase 2: Research Enhancement
- [ ] Research Engine (web + GitHub scanning before build)
- [ ] Gap Report generation and human approval UI
- [ ] GitHub Scout for open-source repo evaluation
- [ ] Blueprint Enhancer (merge research into builds)

### Phase 3: CLI Wrapping
- [ ] CLI Wrapper Factory (generate wrappers for GitHub repos)
- [ ] Wrapper template system (install → map commands → presets)
- [ ] Hybrid tool support (prompt steps + CLI steps in same chain)

### Phase 4: Sideways Connections
- [ ] Data Bus implementation
- [ ] Channel publish/subscribe system
- [ ] Connection Builder UI (drag and drop)
- [ ] System Map visualization

### Phase 5: Self-Improvement
- [ ] Tech Radar scraper (daily GitHub/HN/PH monitoring)
- [ ] Cross-Reference Engine (match findings to tools)
- [ ] Improvement proposal queue + approval UI
- [ ] Auto-patcher for approved improvements

### Phase 6: Dashboard & Polish
- [ ] Full System Map with live data flow
- [ ] Execution monitor for running chains
- [ ] Analytics: which tools run most, which connections carry most data
- [ ] Export/share tool networks

---

## Key Technical Decisions

### Why Shared Data Bus over Event-Driven
- Simpler to implement and debug
- Human can see exactly what data exists
- No race conditions or message ordering issues
- Can add event-driven later as an optimization
- SQLite-backed for persistence (consistent with existing patterns)

### Why CLI Wrappers over Rebuilding
- Open source tools have years of development, edge case handling, community support
- CLI wrapping takes minutes vs days of prompt engineering
- Real software produces real results (actual obfuscation vs prompts about obfuscation)
- Updates come free from the open source community
- The Hong Kong CLI-wrapper tool makes this nearly automatic now

### Why Human-in-the-Loop on Research
- AI finds 10 things, 7 are gold, 3 are noise — human picks in seconds
- Prevents bloat from auto-adding everything
- Owner maintains creative control over tool design
- Speed: scanning a checklist is faster than writing requirements

### Why Tools Should Self-Register Connection Interfaces
- When a tool is built, the AI can infer what it produces and what it needs
- This metadata makes the Connection Builder possible
- Auto-suggestions become possible: "Tool X produces content — connect to Tool Y?"
- The system gets smarter as more tools are added

---

## The Vision: 10 Tools That Build 100

The first 10 tools are the foundation. They include:
- Tools that **protect** other tools (App Shield)
- Tools that **find raw materials** for other tools (Research Engine, GitHub Scout)
- Tools that **build** other tools faster (CLI Wrapper Factory, Blueprint Enhancer)
- Tools that **connect** other tools (Data Bus, Chain Builder)
- Tools that **improve** other tools (Tech Radar, Cross-Reference Engine)
- Tools that **visualize** the whole system (Dashboard Generator)

Once these 10 are running, every new idea becomes:
1. Feed it in (video, description, whatever)
2. Research auto-enriches it
3. GitHub Scout finds existing software
4. CLI Wrapper or prompt chain gets generated
5. Connection interfaces are auto-defined
6. Human drags it into the right place in the system
7. Improvement engine keeps it current

That's the factory. That's how 10 tools become 100 tools become an unstoppable system.

---

## Appendix: Connection Patterns Reference

### Pattern 1: Simple Chain
```
A → B → C
```
Output of each step feeds next. Already supported by chain config.

### Pattern 2: Fan-Out
```
A → B
A → C
A → D
```
One tool feeds multiple. Data Bus channel with multiple subscribers.

### Pattern 3: Fan-In
```
A → D
B → D
C → D
```
Multiple tools feed one. Tool D subscribes to multiple channels.

### Pattern 4: Sideways Tap
```
A → B → C
     ↓
     D (reads B's output without being in the chain)
```
Data Bus: B publishes to a channel, D subscribes. B doesn't need to know about D.

### Pattern 5: Feedback Loop
```
A → B → C → (results fed back to improve A's prompts)
```
Improvement engine pattern. C's results become training data for A's next run.

### Pattern 6: Conditional Branch
```
A → [if condition] → B
                   → C
```
Orchestrator tool evaluates output and routes to different tools.

### Pattern 7: Parallel Execution
```
    → B →
A →       → D
    → C →
```
A's output goes to B and C simultaneously, both feed D. Chain runner handles parallel execution.

---

*This document is the operational framework of truth. Everything built from here follows these patterns.*
