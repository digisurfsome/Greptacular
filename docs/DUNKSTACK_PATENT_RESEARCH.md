# DunkStack Patent Research & Strategy

> **Status**: Active research — 7 inventions identified, 3-patent grouping recommended ($660 total)
> **Date**: March 2026

---

## The Drone Swarm Connection

Drone light show choreography maps 1:1 to AI agent swarm orchestration. Nobody has connected these two domains in a patent before. The drone choreography prior art actually **strengthens** the filing — it establishes the problem space (swarm coordination) as well-understood while the filesystem-based approach for AI agents is the novel solution.

### Architecture Mapping

| Drone Show | Agent System |
|---|---|
| config.csv (role assignment) | task_assignments/ (feature files) |
| swarm.csv (dependency graph) | dependencies.json (feature deps) |
| trajectory_N.csv (per-drone) | prompts/feature_N.md (per-agent) |
| .hwID file (drone identity) | agent process ID |
| trigger_time (sync start) | orchestrator launch |
| TrajectoryPlayer (progress) | feature_get_stats (progress) |
| groupMask (sub-fleet commands) | agent groups in parallel mode |
| safety filter (collision avoid) | file locks + dep checking |

### Key Prior Art References
- **Bitcraze Crazyflie Swarm Examples** — step-synchronized loop pattern
- **Skybrush Open-Source Drone Show Software** — storyboard concept (formations + transitions)
- **Skybrush Studio for Blender** — visual choreography design
- **Skybrush Studio Architecture (DeepWiki)** — formation-based coordination
- **SwarmGPT-Primitive Paper** — LLM composing choreographies from motion primitives (closest prior art, but for PHYSICAL drones, not AI coding agents)
- **Crazyswarm2 Documentation** — distributed swarm control
- **Bitcraze Swarm Show Blog / Synchronized Swarm Blog** — practical implementation

### What To Steal From Drone Choreography

**1. The Storyboard Pattern**
Skybrush's storyboard concept maps directly: define formations (which agents are doing what) and transitions (how to hand off context). The filesystem already does this — the formation IS the set of task assignment files, the transition IS the index file update.

**2. The Step-Synchronized Loop**
Crazyflie's STEP_TIME pattern — all drones execute their step, wait, advance together. Agents could have phases: "Phase 1: all agents implement their features. Phase 2: all agents run tests. Phase 3: integration." The filesystem coordination files ARE the step synchronization.

**3. Motion Primitives**
SwarmGPT's primitive library is exactly what coding agents need — instead of "implement feature X from scratch," give agents primitives: scaffold_component, add_api_endpoint, write_tests, integrate_with_auth. The agent picks the right sequence of primitives.

**4. The Safety Filter**
SwarmGPT's distributed model predictive control = agent checking "will my change conflict with another agent's work?" before committing. The filesystem lock files and dependency graph ARE the safety filter.

### Patent Language Angle
"Multi-agent orchestration using formation-based task assignment with filesystem-mediated synchronization, analogous to drone swarm choreography systems."

Prior art HELPS the patent — shows the problem space (swarm coordination) is established. The innovation is the specific solution: filesystem as the coordination fabric rather than radio packets.

---

## The 7 Inventions

| # | Invention | Standalone Strength | Why |
|---|-----------|-------------------|-----|
| 1 | Continuous session hold + tiered cost escalation | **STRONG** | Clear mechanism, measurable savings, no prior art |
| 2 | Tool-injected message checking | **MEDIUM** | It's the mechanism that enables #1 and #3 — hard to use alone |
| 3 | Unlimited peer-to-peer agent hierarchy | **STRONG** | Anthropic's 1+5 limitation is your proof |
| 4 | Progressive hierarchical file indexing | **STRONG** | Novel context management, measurable improvement |
| 5 | Context-aware task scheduling | **MEDIUM** | Needs #4 or #6 to make sense — it's a strategy for managing context |
| 6 | User-controlled selective compaction | **MEDIUM-STRONG** | Could stand alone but way stronger paired with #4 and #5 |
| 7 | Filesystem as unified fabric | **WEAK** | This is architectural glue — it's HOW #2, #3, #4 work, not a separate thing |

---

## Recommended Patent Grouping: 3 Patents ($660 Total)

### Patent A: The Context Engine (Inventions #1 + #2)
- Continuous session hold with tiered cost escalation
- Tool-injected message checking as the enabling mechanism
- **This is the "cheaper + sharper" patent**

### Patent B: The Agent Hierarchy (Inventions #3 + #7)
- Unlimited peer-to-peer agent hierarchy
- Filesystem as unified coordination fabric
- **This is the "multi-agent communication" patent**
- Strengthened by drone swarm analogy

### Patent C: The Memory System (Inventions #4 + #5 + #6)
- Progressive hierarchical file indexing
- Context-aware task scheduling
- User-controlled selective compaction
- **This is the "longer effective context" patent**

---

## The 25-Agent Dream Team

Optimal agent configuration for a full software build:

### Tier 1: Command (1-2 agents, million-token models)
- **Orchestrator**: Holds the full project vision, assigns tasks, reviews integration
- **Architect**: Designs system architecture, makes tech decisions, resolves conflicts

### Tier 2: Builders (8-10 agents, 200K models — the "chefs")
- **Frontend specialists** (2-3): Component builders, each owning a page/section
- **Backend specialists** (2-3): API endpoints, database, business logic
- **Integration specialist** (1): Connects frontend to backend, handles auth flow
- **Infrastructure specialist** (1): DevOps, CI/CD, deployment configs

### Tier 3: Quality (4-6 agents, 200K models — the "prep cooks")
- **Code reviewer** (1-2): Reviews every PR before merge, catches issues early
- **Test writer** (1-2): Writes tests for code the builders produce
- **Security auditor** (1): Checks for vulnerabilities, OWASP compliance
- **Performance checker** (1): Watches for N+1 queries, bundle size, memory leaks

### Tier 4: Documentation & Marketing (4-6 agents, 200K models)
- **Technical writer** (1): API docs, architecture docs, developer guides
- **Knowledge base builder** (1): User-facing help articles, tutorials
- **Landing page builder** (1): Marketing site, feature descriptions, benefit framing
- **Content strategist** (1): Feature value ranking, marketing angles, unique positioning

### Tier 5: Meta (2-3 agents, 200K models)
- **Patent documenter** (1): Captures innovations as they happen, maintains patent docs
- **Roadmap planner** (1): Feature prioritization, value-add analysis, diminishing returns detection
- **Tutorial/video script writer** (1): Creates tutorial content, video scripts

### Key Insight: Prep Cooks vs. Chefs
Don't burn 200K context windows on testing — have dedicated quality agents that ONLY check work. The builder's context stays clean for building. The reviewer's context stays clean for reviewing. File-based communication means they don't pollute each other's context.

---

## Scaling Possibilities

| Scale | Configuration | Use Case |
|---|---|---|
| Solo | 1 × 1M agent | Small app, one-shot build |
| Small team | 3 × 1M agents | Medium app, architect + builder + reviewer |
| Full team | 1M orchestrator + 10 × 200K workers | Large app with specialized roles |
| Enterprise | 2 × 1M command + 25 × 200K workers | Complex multi-domain application |
| Insane | 5 × 1M + 20 × 200K | Building the next Amazon |

The file system protocol scales to all of these. The only thing that changes is orchestration logic.

---

## What Needs To Be Proven (Tests)

Each patent claim needs evidence. Tests mapped to patents:

| Patent | What To Prove | Test |
|---|---|---|
| A (Context Engine) | Cheaper API calls, sustained quality | Benchmark Protocol: Cost + Sharpness tests |
| B (Agent Hierarchy) | Agents communicate through files | Benchmark Protocol: Communication test (15 min) |
| C (Memory System) | Constraints remembered deep in session | Benchmark Protocol: Memory Recall test |

All test protocols are in `docs/DUNKSTACK_BENCHMARK_PROTOCOL.md`.

---

## Files Reference

| What | Where |
|---|---|
| Test & development plan | `docs/DUNKSTACK_TEST_PLAN.md` |
| Benchmark protocol (exact tests) | `docs/DUNKSTACK_BENCHMARK_PROTOCOL.md` |
| File system architecture | `docs/DUNKSTACK_FILE_SYSTEM_TRUTH.md` |
| Full operator's manual | `DUNKSTACK_MANUAL.md` |
| This patent research doc | `docs/DUNKSTACK_PATENT_RESEARCH.md` |
