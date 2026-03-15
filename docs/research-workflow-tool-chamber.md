# Research: The Tool Chamber — Modular Execution Layer for YT Lab Flows

**Created: 2026-03-15**
**Status: Research complete — ready for decision**
**Purpose: Find/build the missing "tool chamber" that lets YT Lab steps actually execute**

---

## The Problem in One Sentence

YT Lab creates beautiful 8-12 step workflow chains from YouTube videos, but there's no standardized execution layer to actually DO each step. We need a "revolver chamber" of tools that spins to the right one for each step type.

---

## What We Already Have

### YT Lab Pipeline (Working)
```
YouTube URL → Ingest → Discovery → Strategy Extraction → Steps[]
```

Each step has: `title, description, prompt, expectedOutput, notes, model`

### Tool Analyzer PRD (Ready to Build)
- Component Registry — catalog of what tools exist
- Quick Check — "can we make this?"
- Gap Analysis — "what's missing?"
- Self-Building — spawns agents to build missing components

### PRD Shredder (Partially Built)
- Queue PRDs → Analyze → Execute → Commit → Push
- Already working: Phases 1-3

### Stripe Minion Build Rules (Documented)
- Blueprint Pattern: deterministic [ROBOT] steps + creative [AGENT] steps
- Quality Gates: shift feedback left, lint locally before CI
- Bounded iteration: max 2 retries, then hand off
- Tool curation: ~15 tools per agent, not 500

---

## The Missing Piece: The Tool Chamber

Each YT Lab step needs to be executed by one or more tools. The "chamber" metaphor is perfect — it's a revolver with N chambers, each loaded with a different execution capability. The system spins to the right tool based on what the step needs.

### Step Types We Need to Handle

From analyzing YT Lab output patterns:

| Step Type | Example | Tool Needed |
|---|---|---|
| AI Generation | "Write a brand guide" | Claude API (subscription) |
| Web Research | "Research competitor ads" | Web search + scraping |
| Browser Action | "Log into Meta Ads Manager" | Playwright or Computer Use |
| File Creation | "Export as PDF/CSV/HTML" | File writer |
| API Call | "Post to WordPress" | HTTP client + auth |
| Data Transform | "Merge all results into one doc" | Code execution |
| Human Review | "Review and approve copy" | Pause + notification |
| Deploy | "Push to Google Sheets" | Sheets API |
| Email/Notify | "Send results to client" | SMTP/SendGrid |
| Schedule | "Run this every Monday" | Cron/scheduler |

### The "Deterministic Hallway" Concept

From Stripe's Minion blog articles — this is the key insight:

> "The walls matter more than the model."

**What this means for the tool chamber:**
- Each step in a YT Lab flow is a HALLWAY — the AI can choose left or right at decision points, but it can't go through walls
- The "walls" are the tool options available for that step type
- The AI picks which tool to use (Playwright vs Computer Use vs API), but the tool itself executes deterministically
- This is the hybrid: **AI decides WHICH tool, tool executes DETERMINISTICALLY**

```
Step: "Upload ads to Meta"
                |
    AI Decision: How to do this?
                |
        ┌───────┼───────┐
        │       │       │
   Playwright  Computer  Meta API
   (known UI)   Use     (if exists)
        │     (unknown)     │
        │       │           │
   [ROBOT]   [ROBOT]    [ROBOT]
   Click,    See screen,  POST
   fill,     click what   /ads
   submit    looks right  endpoint
```

The trick: **sleeve the deterministic around the AI**. The overall flow is deterministic (step 1 → step 2 → step 3). Within each step, the AI picks the tool. But the tool itself runs as a robot step. This is the "hallway theory" — options are constrained, outcomes are predictable.

---

## MIT/Apache-2.0 Workflow Frameworks Ranked for Our Use Case

After extensive research, here are the frameworks ranked by fit for the "tool chamber" concept. The key criteria: (1) can execute workflows, not just plan them, (2) modular node architecture, (3) MIT or Apache-2.0, (4) can be embedded/scripted, not just used via UI.

### TIER 1: Best Fit — Could Use Directly

#### 1. Activepieces — MIT License
- **GitHub:** [activepieces/activepieces](https://github.com/activepieces/activepieces) — ~20K stars
- **License:** MIT
- **What it is:** Open-source Zapier alternative with 500+ "pieces" (connectors)
- **Why it fits:**
  - Each "piece" is an npm package — you can literally pull individual connectors out
  - 280+ pieces already work as MCP servers (Claude Desktop, Cursor compatible)
  - TypeScript-native, type-safe piece framework
  - Visual flow builder + code steps
  - Human-in-the-loop (approval gates, delays)
  - Self-hosted via Docker
- **The play:** Don't use the full Activepieces platform. Pull individual PIECES out as standalone tool modules. Each piece = one chamber in the revolver. Gmail piece, Sheets piece, Slack piece, HTTP piece — they're all isolated npm packages.
- **Fit score: 9/10** — MIT license, modular pieces architecture, can extract individual connectors

#### 2. Temporal — MIT License
- **GitHub:** [temporalio/temporal](https://github.com/temporalio/temporal) — ~12K stars
- **License:** MIT
- **What it is:** Durable execution engine for workflows that survive failures
- **Why it fits:**
  - Steps are "activities" — isolated, retryable, timeout-aware
  - Workflows are code (Python, TypeScript, Go) — maximum flexibility
  - Built-in retry logic, state persistence, failure recovery
  - Perfect for long-running multi-step agent workflows
  - Self-hosted, production-grade
- **The play:** Each YT Lab step becomes a Temporal activity. The workflow orchestrator sequences them. If step 3 fails, Temporal retries only step 3. State persists across restarts.
- **Fit score: 8/10** — MIT license, battle-tested at Uber/Netflix, but requires more setup than Activepieces

#### 3. LangGraph — MIT License
- **GitHub:** [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) — ~15K stars
- **License:** MIT
- **What it is:** Agent orchestration as directed graphs with tool calling
- **Why it fits:**
  - BUILT for exactly this: AI agent + tool use workflows
  - Graph-based: nodes are tools, edges are decisions
  - Native tool calling — the AI decides which tool, the graph executes it
  - Durable execution, checkpointing, human-in-the-loop
  - Used by Uber, LinkedIn, GitLab
  - Python-native, works with any LLM
- **The play:** Each YT Lab step is a LangGraph node. The graph routes between tool options (Playwright, API call, Computer Use) based on AI decision. State persists. Can pause for human approval.
- **Fit score: 9/10** — MIT license, purpose-built for AI+tool workflows, Python-native matches our stack

#### 4. Hatchet — MIT License
- **GitHub:** [hatchet-dev/hatchet](https://github.com/hatchet-dev/hatchet) — ~4K stars
- **License:** MIT
- **What it is:** Distributed task queue + workflow engine
- **Why it fits:**
  - Fully MIT, fully self-hostable (unlike Inngest)
  - Worker-based: each tool type runs as a worker
  - Concurrency controls, rate limiting built in
  - TypeScript + Python SDKs
  - Lightweight compared to Temporal
- **The play:** Each tool type (Playwright worker, API worker, Claude worker) is a Hatchet worker. Steps route to the right worker. Simpler than Temporal, still durable.
- **Fit score: 7/10** — MIT license, simpler than Temporal, but smaller ecosystem

### TIER 2: Good Fit — Need Some Adaptation

#### 5. Node-RED — Apache 2.0
- **GitHub:** [node-red/node-red](https://github.com/node-red/node-red) — ~20K stars
- **License:** Apache 2.0
- **What it is:** Flow-based visual programming for wiring APIs, hardware, and services
- **Why it fits:**
  - 5,000+ community nodes for every service imaginable
  - Visual flow editor — the AI could programmatically create flows
  - Subflows for reusable tool patterns
  - Message-passing architecture matches step-to-step data flow
  - Lightweight, runs on anything
- **The play:** Each YT Lab step type maps to a Node-RED node or subflow. The AI constructs a Node-RED flow from the step list. Node-RED executes it. Visual debugging.
- **Caution:** Node-RED is JavaScript-only (our backend is Python). Would need a bridge.
- **Fit score: 7/10** — Massive node library, visual editing, but JS-only is a friction point

#### 6. Kestra — Apache 2.0
- **GitHub:** [kestra-io/kestra](https://github.com/kestra-io/kestra) — ~18K stars
- **License:** Apache 2.0
- **What it is:** Event-driven orchestration platform, 600+ plugins
- **Why it fits:**
  - YAML-defined workflows — easy to generate programmatically
  - 600+ plugins covering databases, cloud, messaging, APIs
  - Supports Python, Node.js, Go, Shell within workflows
  - Event triggers, scheduling, retry logic
  - Self-hosted via Docker
- **The play:** YT Lab generates a Kestra YAML workflow from the step list. Each step maps to a Kestra task/plugin. Kestra handles execution, retries, scheduling.
- **Caution:** Java-based (heavier resource footprint). YAML can get complex.
- **Fit score: 7/10** — Huge plugin library, declarative YAML, but Java overhead

#### 7. Trigger.dev — Apache 2.0
- **GitHub:** [triggerdotdev/trigger.dev](https://github.com/triggerdotdev/trigger.dev) — ~10K stars
- **License:** Apache 2.0
- **What it is:** Background job/workflow engine with durable execution
- **Why it fits:**
  - v3 runs long-running tasks with checkpointing
  - Built-in integrations (OpenAI, Slack, Airtable, etc.)
  - Self-hosted via Docker, unlimited runs
  - Real-time monitoring dashboard
- **The play:** Each tool type is a Trigger.dev task. Steps chain together. Checkpointing means long browser automation tasks survive failures.
- **Caution:** TypeScript-only. Our backend is Python.
- **Fit score: 6/10** — Great DX, Apache 2.0, but TypeScript-only

#### 8. Prefect — Apache 2.0
- **GitHub:** [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) — ~18K stars
- **License:** Apache 2.0
- **What it is:** Python-native workflow orchestration
- **Why it fits:**
  - Any Python function becomes an orchestrated task with `@task` decorator
  - Async execution, concurrent tasks, complex flow patterns
  - Self-hosted server option
  - Dashboard for monitoring
  - Python-native = zero friction with our stack
- **The play:** Each tool is a Prefect task. Flows are Python functions with `@flow` decorator. The Tool Analyzer generates Prefect flow code from YT Lab steps.
- **Fit score: 7/10** — Python-native, Apache 2.0, but more data-pipeline focused than general automation

### TIER 3: Worth Knowing — Different Angle

#### 9. CrewAI — MIT License
- **GitHub:** [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) — ~46K stars
- **License:** MIT (open-source core)
- **What it is:** Multi-agent orchestration framework with 100+ built-in tools
- **Why it fits:**
  - Role-based agent teams — each "crew member" has specific tools
  - 100+ open-source tools out of the box
  - Python-native, model-agnostic
  - The "revolver chamber" is built in — agents have tool lists
- **The play:** Each YT Lab step becomes a CrewAI task assigned to an agent with the right tools. The crew executes the step chain collaboratively.
- **Caution:** More agent-framework than workflow-engine. Might be too opinionated.
- **Fit score: 6/10** — Massive community, good tools, but agent-centric rather than workflow-centric

#### 10. Dagster — Apache 2.0
- **GitHub:** [dagster-io/dagster](https://github.com/dagster-io/dagster) — ~12K stars
- **License:** Apache 2.0
- **What it is:** Data orchestration platform with asset-centric approach
- **Why it fits:**
  - Python-native, strong typing, great DevX
  - "Software-defined assets" — each step output is a tracked asset
  - Built-in scheduling, retries, partitioning
  - Excellent observability
- **The play:** Each step output is a Dagster asset. The step chain is a Dagster graph. Strong for data-heavy workflows.
- **Caution:** Very data-pipeline focused. Less suited for browser automation / API interaction steps.
- **Fit score: 5/10** — Great Python orchestration, but designed for data, not general automation

---

## The Recommendation: A Hybrid Approach

After studying everything — the YT Lab pipeline, the Stripe Minion patterns, the PRDs, and these 10 frameworks — here's what I think is the right move:

### The Architecture: "Deterministic Hallway with Tool Chambers"

```
┌─────────────────────────────────────────────────────────────┐
│                    YT LAB STEP EXECUTOR                       │
│                                                               │
│  Step Chain: [1] → [2] → [3] → [4] → ... → [N]             │
│              ↓      ↓      ↓      ↓            ↓             │
│           ┌──┴──┐┌──┴──┐┌──┴──┐┌──┴──┐    ┌──┴──┐          │
│           │TOOL ││TOOL ││TOOL ││TOOL │    │TOOL │          │
│           │CHAM ││CHAM ││CHAM ││CHAM │    │CHAM │          │
│           │BER  ││BER  ││BER  ││BER  │    │BER  │          │
│           └─────┘└─────┘└─────┘└─────┘    └─────┘          │
│                                                               │
│  Each chamber has 2-5 tool options:                           │
│  ┌─────────────────────┐                                      │
│  │ TOOL CHAMBER        │                                      │
│  │                     │                                      │
│  │  [1] Claude API  ←──── Default for AI generation          │
│  │  [2] Playwright  ←──── For known/scripted web actions     │
│  │  [3] Computer Use ←─── For unknown/dynamic web actions    │
│  │  [4] HTTP Client  ←─── For direct API calls               │
│  │  [5] File Writer  ←─── For creating outputs               │
│  │                     │                                      │
│  │  AI SELECTS → Tool executes DETERMINISTICALLY             │
│  └─────────────────────┘                                      │
│                                                               │
│  ORCHESTRATOR: LangGraph (MIT) — graph-based routing          │
│  CONNECTORS: Activepieces Pieces (MIT) — pre-built tools      │
│  DURABILITY: Temporal patterns — retry, persist, recover      │
│  RULES: Stripe Blueprint — [ROBOT] + [AGENT] interleaving    │
└─────────────────────────────────────────────────────────────┘
```

### Why This Combination

1. **LangGraph for the Orchestrator** — It's MIT, Python-native (matches our stack), purpose-built for AI+tool workflows. The graph structure naturally maps to YT Lab step chains with conditional routing. It handles the "which tool?" decision.

2. **Activepieces Pieces for Pre-Built Connectors** — MIT license, 280+ pieces available as standalone npm packages. Instead of building a Gmail connector, Sheets connector, Slack connector from scratch, we pull them from Activepieces. Each piece = one tool option in the chamber.

3. **Stripe Blueprint Pattern for Execution Control** — Already documented in our codebase. Each step alternates [ROBOT] (deterministic tool execution) and [AGENT] (AI decision-making). Bounded iteration (max 2 retries). Shift feedback left.

4. **Temporal Patterns for Durability** — Not necessarily running full Temporal, but adopting its patterns: durable execution, activity-level retries, state persistence. LangGraph already has checkpointing that covers most of this.

### Why NOT Just Use One Framework

No single framework does everything:
- LangGraph: Great orchestration, no pre-built connectors
- Activepieces: Great connectors, not designed for AI agent routing
- Temporal: Great durability, overkill for simple steps
- Node-RED: Great visual editing, wrong language (JS vs Python)

The hybrid takes the best of each:
- **Decision layer**: LangGraph (AI routing)
- **Connector layer**: Activepieces pieces (pre-built tools)
- **Execution layer**: Python + Playwright + Computer Use
- **Control layer**: Stripe Blueprint rules (deterministic structure)

---

## The "Something New Nobody Has Thought Of" — Skill-Sleeved Determinism

Here's the creative synthesis you asked me to think about:

### The Insight

Stripe says "put the AI in a hallway with walls." But what if the WALLS themselves are AI-generated, and then FROZEN into deterministic structure?

**The idea: Skills as Frozen Hallways**

1. First time a step type is encountered: AI figures out how to do it (expensive, creative, might fail)
2. The successful execution path is CAPTURED as a skill — a deterministic sequence of tool calls
3. Next time that step type appears: the SKILL runs, not the AI
4. The AI only activates when the skill fails (fallback) or when there's no skill yet

```
Step: "Upload video to YouTube"

First time (no skill exists):
  [AGENT] → Decides: use Computer Use → navigates YouTube Studio → uploads → succeeds
  [CAPTURE] → Records the exact sequence as a skill:
    1. Open youtube.com/studio
    2. Click "Create" button
    3. Click "Upload videos"
    4. Select file from path
    5. Fill title field with {title}
    6. Fill description with {description}
    7. Click "Next" 3 times
    8. Click "Publish"
  [FREEZE] → Skill saved as "youtube_upload_v1"

Second time:
  [ROBOT] → Runs "youtube_upload_v1" skill → deterministic, fast, no AI tokens
  [FALLBACK] → If skill fails (YouTube redesigned?), fall back to [AGENT] mode
  [LEARN] → If agent succeeds with new approach, update skill to v2
```

### Why This Is New

- **Stripe** freezes the hallway at BUILD TIME (engineers write blueprints)
- **This** freezes the hallway at RUNTIME (AI writes the blueprint on first success)
- The system literally **learns its own deterministic structure** over time
- After 20-30 video workflows, 90% of steps run as frozen skills — fast, cheap, predictable
- The remaining 10% are genuinely new step types that trigger AI exploration

### The Compound Effect

```
Week 1:  AI runs 100% of steps   → Expensive, slow, sometimes fails
Week 2:  AI runs 60% of steps    → 40% are now frozen skills
Week 4:  AI runs 20% of steps    → 80% are frozen skills
Week 8:  AI runs 5% of steps     → 95% are frozen skills, near-zero cost
```

**This is the "micro reality" concept** — each skill is a micro-deterministic-reality within the larger AI-flexible system. The AI creates the micro-realities, then lives within them. It's not AI OR deterministic. It's AI CREATING determinism, then RUNNING within it.

### Implementation Pattern

```python
class ToolChamber:
    """The revolver. Spins to the right tool for each step."""

    def execute_step(self, step: YTStrategyStep) -> StepResult:
        # 1. Check if we have a frozen skill for this step type
        skill = self.skill_registry.find_skill(step)

        if skill and skill.confidence > 0.8:
            # [ROBOT] Run the frozen skill
            result = skill.execute(step)
            if result.success:
                return result
            # Skill failed — fall through to AI

        # 2. No skill or skill failed — AI decides
        # [AGENT] Which tool to use?
        tool_choice = self.ai_router.select_tool(step, self.available_tools)

        # 3. [ROBOT] Execute the chosen tool
        result = tool_choice.tool.execute(step)

        # 4. [CAPTURE] If successful, freeze as skill
        if result.success:
            self.skill_registry.capture_skill(
                step_type=step.type,
                tool_used=tool_choice.tool,
                execution_trace=result.trace,
                version=skill.version + 1 if skill else 1
            )

        return result
```

---

## The 5 Frameworks to Test (Ranked Priority)

Based on everything above, here are the 5 to actually test over the next 1-2 days:

### 1. LangGraph (MIT) — Test as the orchestrator
- `pip install langgraph`
- Build a simple 3-step flow: AI generation → web search → file output
- Test tool routing: can it pick between Playwright and Computer Use?
- Test state persistence: does it survive restarts?

### 2. Activepieces Pieces (MIT) — Test as the connector library
- Pull 3-4 pieces: Gmail, Sheets, HTTP, Slack
- Test: can we use them as standalone npm packages outside Activepieces?
- Test: can Python call them via subprocess or bridge?

### 3. Temporal (MIT) — Test as the durability layer
- `pip install temporalio`
- Build a 3-step workflow with activities
- Test: does it retry failed steps correctly?
- Test: does state persist if we kill the process?

### 4. Node-RED (Apache 2.0) — Test as the visual editor
- `npm install node-red`
- Build a flow that chains API calls
- Test: can we programmatically create flows (REST API)?
- Test: can an AI construct a Node-RED flow from a step list?

### 5. CrewAI (MIT) — Test as the agent-tool layer
- `pip install crewai`
- Build a crew with 3 agents, each with different tools
- Test: does tool selection work well?
- Test: can we feed YT Lab steps as CrewAI tasks?

---

## How This Connects to Everything

```
YT Lab extracts steps from YouTube video
        ↓
Tool Analyzer checks: do we have tools for each step?
        ↓ YES → Generate tool
        ↓ NO  → Gap Analysis → which tools are missing?
                     ↓
              PRD Shredder builds missing tool/connector
                     ↓
              Tool Chamber gets new capability
                     ↓
              Re-check → now passes → Generate tool
                     ↓
              Tool executes step chain:
                LangGraph routes each step
                Skill Registry checks for frozen skills
                Tool Chamber spins to right tool
                Stripe Blueprint controls execution
                     ↓
              Step output feeds next step
                     ↓
              All steps complete → Tool is built and deployed
                     ↓
              Skill captures successful execution paths
                     ↓
              NEXT video benefits from captured skills
```

**The full loop is:**
1. YT Lab finds what to build
2. Tool Analyzer checks if we CAN build it
3. PRD Shredder builds what's missing
4. Tool Chamber executes the build
5. Skills capture what worked
6. Everything gets faster and cheaper over time

---

## NEW INPUT: Karpathy Auto-Research Loop Applied to Skills

### The Source

Andrej Karpathy (OpenAI founding team, ex-head of AI at Tesla) published a pattern called **"auto research"** — give an AI system something to improve, one clear way to measure if it got better, and let it loop all night. A Claude Code creator applied this exact pattern to skill self-improvement.

### The Pattern (3 Files)

Karpathy's original:
1. `program.md` — Instructions for the agent (what to test, how to loop)
2. `data.csv` — Fixed data file for recording results
3. `train.py` — The script the agent edits and re-runs

Applied to skills:
1. `skill.md` — The skill instructions (what the agent edits)
2. `eval/eval.json` — Binary assertions (the measurement)
3. The loop prompt — "Keep going until perfect score or I stop you"

### The Loop

```
READ skill.md
    ↓
MAKE ONE CHANGE to skill instructions
    ↓
RUN 5 test prompts through the skill
    ↓
CHECK 25 binary assertions (true/false)
    ↓
CALCULATE pass rate (e.g., 23/25 = 92%)
    ↓
├── Score improved? → git commit, keep change
└── Score dropped?  → git reset, try different change
    ↓
REPEAT until perfect score or human interrupts
```

### Why Binary Assertions Are Everything

**Binary (automatable):**
- "First line is a standalone sentence, not part of a paragraph" → true/false
- "Contains at least one specific number or statistic" → true/false
- "Final line is NOT a question" → true/false
- "Total word count under 300" → true/false
- "Does not contain em-dashes" → true/false

**NOT binary (requires human judgment):**
- "Does it have a compelling subject line?" → subjective, can't automate
- "Is the tone of voice right?" → two people disagree
- "Is it creative enough?" → unmeasurable

The key insight: **structural quality can be fully automated. Creative quality still needs human review.** But structural quality is 70-80% of what makes a skill reliable.

### Two Layers of Self-Improvement

**Layer 1: Skill Activation** (does the skill TRIGGER at the right time?)
- Built into Anthropic's skill creator already
- Tests: "Given these queries, does the skill activate? Yes/No?"
- Improves the YAML description until trigger accuracy is high
- Already automated — no work needed

**Layer 2: Skill Output Quality** (does the skill PRODUCE good results?)
- This is the Karpathy loop applied to skills
- Tests: "Given these prompts, does output pass 25 binary assertions?"
- Improves the skill.md instructions until pass rate is 100%
- Runs overnight, autonomous, no human input needed

### How This Changes the Tool Chamber Architecture

This is the third dimension we were missing. The original architecture was:

```
v1: AI executes step → succeeds → freeze as skill (one-time capture)
```

With the Karpathy loop, it becomes:

```
v2: AI executes step → succeeds → freeze as skill v1
    → overnight: run binary assertions against skill v1
    → assertions fail? → modify skill, retest → skill v2
    → repeat until perfect score → skill vN (battle-tested)
```

**The compound effect is now THREE layers deep:**

1. **Tool Chamber** spins to the right tool for each step type
2. **Skill Capture** freezes successful execution paths into deterministic skills
3. **Karpathy Loop** autonomously refines those skills overnight using binary assertions

```
Week 1:  AI runs steps raw          → Expensive, unreliable
Week 2:  Skills captured from v1    → Cheaper, somewhat reliable
Week 4:  Skills refined to v3-v5    → Near-free, highly reliable
Week 8:  Skills at v10+             → Near-perfect structural quality
```

### The Eval.json Structure for Tool Chamber Steps

Adapting the binary assertion pattern to YT Lab step types:

```json
{
  "skill_name": "youtube_upload",
  "tests": [
    {
      "prompt": "Upload a video titled 'AI SEO Guide' to YouTube with description from {context}",
      "expected_output": "Video successfully uploaded to YouTube",
      "assertions": [
        {"check": "navigated_to_youtube_studio", "type": "boolean"},
        {"check": "clicked_upload_button", "type": "boolean"},
        {"check": "file_was_selected", "type": "boolean"},
        {"check": "title_field_matches_input", "type": "boolean"},
        {"check": "description_contains_context", "type": "boolean"},
        {"check": "publish_button_clicked", "type": "boolean"},
        {"check": "no_error_messages_shown", "type": "boolean"},
        {"check": "completion_time_under_120_seconds", "type": "boolean"}
      ]
    }
  ]
}
```

For each step TYPE in the tool chamber, we'd have an eval.json with binary assertions. The Karpathy loop refines the skill until all assertions pass consistently across multiple runs.

### The Overnight Factory v2

The original overnight vision:
```
Queue 10 YouTube videos → extract steps → build tools → sleep → wake up to 10 tools
```

With the Karpathy loop added:
```
Queue 10 YouTube videos → extract steps → build tools
    ↓
Tool Analyzer checks readiness → gaps found → PRD Shredder builds missing components
    ↓
Tool Chamber executes step chains → skills captured from successes
    ↓
OVERNIGHT: Karpathy loop runs on ALL captured skills
    - Each skill runs 5 test prompts × 25 assertions = 125 binary checks
    - Failed assertions → skill.md modified → retest → keep or revert
    - Loops until perfect or morning
    ↓
MORNING: 10 tools built + skills refined to v3-v5 + component library expanded
```

**The system now has THREE self-improving feedback loops running simultaneously:**
1. **Component Library** grows as the Tool Analyzer discovers and builds missing tools
2. **Skill Registry** captures successful execution paths and freezes them
3. **Karpathy Loop** refines frozen skills overnight using binary assertions

Each loop makes the others more effective. More components → more skills get captured → more skills get refined → higher pass rates → more reliable tool execution → fewer gaps → fewer new components needed.

### Implementation: The Skill Self-Improvement Agent

```python
class SkillRefiner:
    """Karpathy auto-research loop applied to tool chamber skills."""

    def __init__(self, skill_registry, eval_dir):
        self.registry = skill_registry
        self.eval_dir = eval_dir

    async def run_overnight(self):
        """Run until all skills hit perfect score or human interrupts."""
        while True:
            for skill in self.registry.get_all_skills():
                eval_file = self.eval_dir / f"{skill.name}/eval.json"
                if not eval_file.exists():
                    continue

                # Run assertions
                score = await self.evaluate(skill, eval_file)

                if score.pass_rate == 1.0:
                    continue  # Perfect — skip

                # Save current state
                old_content = skill.read_md()
                old_score = score.pass_rate

                # AI makes ONE change to skill.md based on failed assertions
                await self.improve_skill(skill, score.failed_assertions)

                # Re-evaluate
                new_score = await self.evaluate(skill, eval_file)

                if new_score.pass_rate > old_score:
                    # Keep the change
                    skill.increment_version()
                    git_commit(f"Skill refined: {skill.name} v{skill.version} "
                              f"({old_score:.0%} → {new_score.pass_rate:.0%})")
                else:
                    # Revert
                    skill.write_md(old_content)
                    git_reset()

                # Rate limit awareness
                await self.check_rate_limits()

    async def evaluate(self, skill, eval_file):
        """Run all test prompts through skill, check binary assertions."""
        evals = json.loads(eval_file.read_text())
        results = []

        for test in evals["tests"]:
            # Run the skill with the test prompt
            output = await self.run_skill(skill, test["prompt"])

            # Check each binary assertion
            for assertion in test["assertions"]:
                passed = self.check_assertion(output, assertion)
                results.append({"assertion": assertion, "passed": passed})

        pass_count = sum(1 for r in results if r["passed"])
        return Score(
            pass_rate=pass_count / len(results),
            failed_assertions=[r for r in results if not r["passed"]]
        )
```

### The Key Insight for Our System

The video creator said something important: **"Triggering reliably and producing great outputs are different problems."**

In our tool chamber context:
- **Triggering** = the Tool Analyzer correctly matching a step type to a tool (Layer 1)
- **Output quality** = the tool actually executing the step correctly (Layer 2)
- **Self-improvement** = the skill getting better at execution overnight (Layer 3)

All three can be automated. All three use the same core pattern: **measure with binary assertions, loop until perfect, keep or revert each change.**

This is the Stripe Blueprint pattern (deterministic hallways) PLUS Karpathy's auto-research loop (self-improving hallways). The hallways don't just exist — they get smoother overnight.

---

## ACTION ITEM: SkillForge Loop — Build This First

### What It Is

A single-command tool that takes a `skill.md` + `eval.json` and autonomously runs the Karpathy improvement loop until the skill hits target pass rate. No invention required — the architecture is fully specified by the video. Just clean implementation of a proven loop.

### Why Build This Before the Tool Chamber

The tool chamber is a multi-week effort (orchestrator + connectors + skill capture + execution layer). SkillForge is a **few-day build** that delivers immediate value:

- **Every skill in AutoForge's stack becomes self-maintaining** — from 18 skills today to 50+ tomorrow, maintenance cost stays flat
- **Direct ROI on every skill** — the marketing copywriting skill went from 95.8% to 100% in 2 runs
- **Infrastructure, not a utility** — this is the refinement engine that the tool chamber's skill capture layer feeds INTO

### The Full Pipeline

```
INPUT:
  skill.md          — the skill instructions to improve
  eval.json         — binary assertions (true/false) across test prompts

LOOP:
  1. Read skill.md
  2. Run N test prompts through the live skill (e.g., 5 prompts)
  3. Check M binary assertions per prompt (e.g., 5 assertions × 5 prompts = 25 checks)
  4. Calculate pass rate (e.g., 23/25 = 92%)
  5. If pass_rate == target → DONE, log success
  6. If pass_rate < target:
     a. AI analyzes failed assertions
     b. Makes ONE targeted change to skill.md
     c. Reruns all tests
     d. If score improved → git commit, continue loop
     e. If score dropped → git reset, try different change
  7. NEVER stop. NEVER ask human. Keep looping until target or interrupted.

OUTPUT:
  - Improved skill.md (committed per improvement)
  - run_log.json — per-iteration scores, diffs, assertion results
  - Summary: v1 score → vN score, total iterations, time elapsed
```

### Eval.json Format

```json
{
  "skill_name": "marketing-copywriting",
  "target_pass_rate": 1.0,
  "max_iterations": 20,
  "tests": [
    {
      "prompt": "Write a LinkedIn post about why simple automations beat complex ones",
      "expected_output_type": "linkedin_post",
      "assertions": [
        {"id": "standalone_first_line", "check": "First line is a standalone sentence, not part of a paragraph", "type": "binary"},
        {"id": "has_statistic", "check": "Contains at least one specific number or statistic", "type": "binary"},
        {"id": "no_question_ending", "check": "Final line is NOT a question", "type": "binary"},
        {"id": "under_300_words", "check": "Total word count is under 300", "type": "binary"},
        {"id": "no_em_dashes", "check": "Does not contain em-dashes (—)", "type": "binary"}
      ]
    },
    {
      "prompt": "Write email subject lines for a product launch campaign",
      "expected_output_type": "email_subjects",
      "assertions": [
        {"id": "under_60_chars", "check": "Each subject line is under 60 characters", "type": "binary"},
        {"id": "no_all_caps", "check": "No subject line is in ALL CAPS", "type": "binary"},
        {"id": "has_urgency", "check": "At least one subject line creates urgency", "type": "binary"},
        {"id": "has_curiosity", "check": "At least one subject line uses an open loop or curiosity gap", "type": "binary"},
        {"id": "count_is_five_plus", "check": "At least 5 subject lines provided", "type": "binary"}
      ]
    }
  ]
}
```

### Implementation Plan

**Where it lives:** `server/services/skill_forge.py` + `server/routers/skill_forge.py`

**How it runs:**
- Option A: CLI command — `python -m skill_forge --skill path/to/skill.md --evals path/to/eval.json`
- Option B: API endpoint — `POST /api/skill-forge/run` with skill path + eval path
- Option C: UI page — queue skills for overnight refinement (like PRD Shredder)

**All three options use the same core loop.** Start with CLI (Option A) for testing, add API + UI later.

**Dependencies:**
- Claude subscription auth (same pattern as YT Lab — `force_subscription=True`)
- Git for commit/reset (already available)
- The skill must be runnable via Claude Code

**Rate limit awareness:**
- Each iteration = 1 Claude call (run skill) + 1 Claude call (analyze failures + suggest change)
- 20 iterations = ~40 Claude calls
- Space iterations with rate limit checks (same pattern as PRD Shredder)
- Schedule for overnight when rate limits are less constrained

### Strategic Compound Value

```
Today:     18 skills × manual improvement = weeks of tweaking per skill
SkillForge: 18 skills × overnight loop = all refined by morning
Next month: 50 skills × overnight loop = zero additional maintenance cost

When Tool Chamber ships:
  Tool executes step → captures skill → SkillForge refines skill overnight
  → next execution uses refined skill → faster, cheaper, more reliable
  → SkillForge is the REFINEMENT ENGINE for the entire tool chamber
```

This is the first thing to build because it's:
1. **Proven pattern** — Karpathy validated it, the video validated it for skills
2. **Immediate ROI** — every existing skill gets better overnight
3. **Foundation** — the tool chamber's skill capture layer feeds directly into it
4. **Few days** — fully specified, no design decisions needed

---

### Stripe Minion Blog Articles
- [Part 1: Minions: Stripe's one-shot, end-to-end coding agents](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents)
- [Part 2: Minions Part 2](https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2)
- [Analysis: The Walls Matter More Than the Model](https://www.anup.io/stripes-coding-agents-the-walls-matter-more-than-the-model/)

### Frameworks Researched
- [Activepieces](https://github.com/activepieces/activepieces) — MIT, ~20K stars
- [LangGraph](https://github.com/langchain-ai/langgraph) — MIT, ~15K stars
- [Temporal](https://github.com/temporalio/temporal) — MIT, ~12K stars
- [Hatchet](https://github.com/hatchet-dev/hatchet) — MIT
- [CrewAI](https://github.com/crewAIInc/crewAI) — MIT, ~46K stars
- [Node-RED](https://nodered.org/) — Apache 2.0, ~20K stars
- [Kestra](https://github.com/kestra-io/kestra) — Apache 2.0, ~18K stars
- [Trigger.dev](https://github.com/triggerdotdev/trigger.dev) — Apache 2.0, ~10K stars
- [Prefect](https://github.com/PrefectHQ/prefect) — Apache 2.0, ~18K stars
- [Dagster](https://github.com/dagster-io/dagster) — Apache 2.0, ~12K stars

### Internal Documents Referenced
- `/docs/prd-yt-lab-tool-analyzer.md` — Tool Analyzer PRD (the self-building flywheel)
- `/docs/prd-prd-shredder.md` — PRD Shredder (drop PRD in, code comes out)
- `/docs/stripe-minions-build-rules.md` — Stripe patterns adapted for our agents
- `/docs/prd-yt-lab-v2.md` — YT Lab v2 vision
