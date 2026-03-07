# Elder Agent Architecture: Multi-Model Staggered Team System

## Mission Statement

Design and implement an autonomous agent team architecture that solves the fundamental problem of context window degradation while preserving accumulated knowledge across long-running software development projects. The system leverages multiple AI models (Claude Opus 4.6, GPT 5.4 Codex, Gemini 3.1) in staggered rotation with role-based responsibilities, enabling continuous 24/7 development operations within subscription-tier economics.

This architecture sits on top of AutoForge's existing orchestration platform (DunkStack, Workspace, queue system) and transforms it from a single-agent-at-a-time tool into a managed team operation.

---

## The Core Problem

A single agent's context window (typically ~200K tokens) is insufficient for full software projects. By the time an agent deeply understands a codebase, its architecture decisions, and the project goals, it's entering degradation territory. The knowledge peaks right as reliability starts declining — the "elder paradox."

### The Elder Paradox (Human Analogy)

- An elder has decades of accumulated wisdom and pattern recognition
- But cognitive decline introduces errors in recall and judgment
- The knowledge is incredibly valuable; the delivery mechanism becomes unreliable
- You don't fire the elder — you change their role

### The Agent Version

- At 0-40% context usage: Learning phase, building understanding, high accuracy
- At 40-60%: Peak performance — deep understanding + full reliability
- At 60-80%: Elder zone — vast knowledge, but increasing hallucination/drift risk
- At 80%+: Deep degradation — knowledge is there but output becomes unreliable

**The waste today:** When an agent hits degradation, all that accumulated knowledge is lost. The next agent starts from zero. Every. Single. Time.

---

## The Staggered Team Model

### Core Concept: Overlapping Generations

Instead of running agents to exhaustion and replacing them, stagger new agents into the team at regular intervals so there is always a "ripe" agent ready to assume the lead role.

```
Timeline (by context usage of original agent):

Agent A:  [====LEARNING====|====PEAK====|====ELDER====|===DEEP ELDER===]
Agent B:            [====LEARNING====|====PEAK====|====ELDER====|...]
Agent C:                      [====LEARNING====|====PEAK====|...]
Agent D:                                [====LEARNING====|...]

Leadership:   A leads         A leads    B leads      C leads
              B learning      B rising   A advises    B advises
                              C enters   C rising     D enters
```

### Rotation Trigger Points

- **~15-20% context**: New agent joins the team, begins onboarding
- **~40-50% context**: Agent enters peak zone, eligible for lead role
- **~50-60% context**: Leadership handoff to the next peak-zone agent
- **~60-80% context**: Transition to elder/advisory role (reduced activity, slower context burn)
- **~80%+ context**: Read-only elder — consulted on major decisions only, minimal context burn

### Role Definitions

**Lead Operator** (40-60% context range)
- Spawns and manages sub-agents for implementation tasks
- Makes architectural decisions
- Writes to the shared knowledge base
- Highest authority on current implementation decisions

**Rising Operator** (15-40% context range)
- Shadow-learns from the Lead by reading the shared knowledge base
- Takes on smaller implementation tasks to build understanding
- Asks clarifying questions (routed through knowledge base, not direct conversation)
- Prepares for leadership handoff

**Elder Advisor** (60-80% context range)
- No longer spawns sub-agents or does direct implementation
- Consulted on architectural decisions and big-picture questions
- Reviews major PRDs or plans (read-heavy, write-light = slower context burn)
- Contributes to knowledge base from historical perspective

**Deep Elder / Oracle** (80%+ context range)
- Read-only consultation on critical decisions
- Used sparingly — each interaction burns precious remaining context
- Best used for "does this align with the original vision?" type questions
- Graceful retirement when context is near limit

### Why Elders Burn Context Slower

Key insight: An agent that's only reading summaries and occasionally answering questions burns context at maybe 1/5th the rate of the lead operator who's reading code, spawning sub-agents, processing results, making decisions, and writing implementations. This means:

- An agent at 60% context might take 3-4x longer to reach 80% in an advisory role
- The elder stays useful much longer than expected because the burn rate drops dramatically
- This extends the overlap period, giving the team more collective wisdom for longer

---

## The Shared Knowledge Base ("Source of Truth")

### Purpose

A persistent, structured document (or set of documents) that captures the team's accumulated understanding. Every agent reads from it; active agents write to it.

### What Gets Recorded

**Always recorded:**
- Architectural decisions and their rationale
- Dependency relationships discovered during implementation
- Gotchas, edge cases, and hard-won lessons
- Current project state and what's been completed
- Active blockers and unresolved questions

**Judgment filter (record only if significant):**
- Research findings — only record if they change the approach or reveal constraints
- Sub-agent results — summarize outcomes, not process
- Failed approaches — brief note on what didn't work and why, so nobody repeats it

**Never recorded:**
- Raw code (that's in the repo)
- Verbose logs or full conversation transcripts
- Redundant information already in the codebase

### Format

Brief by default. Detailed only when the information is critical. The knowledge base should be readable by a fresh agent in under 5,000 tokens to get oriented, with deeper sections available for specific topics.

### Briefing Protocol

When sub-agents return from research or implementation tasks, their results go through a significance filter before being added to the knowledge base:

1. Did this change our understanding of the architecture? → Record
2. Did this reveal a constraint or limitation? → Record
3. Did this confirm what we already knew? → Skip
4. Was this routine implementation? → Record outcome only (1-2 lines)

---

## Multi-Model Team Composition

### The Trifecta

| Model | Strengths | Best Role | Context Window |
|-------|-----------|-----------|---------------|
| Claude Opus 4.6 | Deep reasoning, architecture, nuanced judgment | Lead Operator, Elder Advisor | 200K |
| GPT 5.4 Codex | Fast implementation, broad knowledge | Lead Operator, Builder | 200K |
| Gemini 3.1 | Large context, research synthesis | Research Lead, Knowledge Base Manager | 1M |
| Gemini 3.1 (1M) | Massive context retention | Super Elder, long-term oracle | 1M |
| Claude Opus (1M)* | Deep reasoning + massive context | Super Elder, architectural oracle | 1M |

*If/when available at reasonable cost

### Why Mix Models

- **Blind spot coverage**: Each model has different failure modes. Where one hallucinates, another catches it. Cross-model review is inherently more robust than same-model review.
- **Cost optimization**: Use expensive models (Opus, 1M-token) for high-leverage advisory roles. Use subscription-tier models for the bulk implementation work.
- **Specialization**: Some models are better at certain tasks. Let each do what it does best.

### Mixed Team Configurations

**Two-Builder Pattern:**
- GPT 5.4 and Opus 4.6 work as co-leads
- One proposes, the other critiques
- Human (you) breaks ties and sets direction
- Both feed into the shared knowledge base

**Research + Build Pattern:**
- Gemini handles research and documentation (its large context excels here)
- Opus/GPT handle implementation
- Research findings flow through the knowledge base to builders

**Full Team Pattern:**
- Gemini 3.1 (1M): Super Elder / Knowledge Base Oracle — reads everything, provides long-term continuity
- Opus 4.6: Lead Operator for complex architectural work
- GPT 5.4: Lead Operator for rapid implementation
- Staggered rotation among Opus/GPT agents with Gemini as the constant

---

## The Million-Token Super Elder

### Concept

A million-token model (Gemini 3.1, or future Claude/GPT 1M variants) operates as a persistent "super elder" that outlasts multiple generations of standard agents.

### The Math

If a standard 200K agent hits meaningful degradation at ~60% (120K tokens), a 1M agent doesn't hit that same threshold until ~600K tokens. That's 5x the useful lifespan. At a reduced elder burn rate (1/5th), it could theoretically persist through an entire large project.

### Role: The Living Memory

- Reads all knowledge base updates (low context cost)
- Reads sub-agent research summaries (low context cost)
- Maintains the deepest understanding of project history, decisions, and direction
- Consulted for: "Does this new direction align with the original vision?", "We tried something similar in phase 2, what happened?", "What are the implications of changing X on the rest of the system?"
- Does NOT do implementation (expensive per-token, wasteful for grunt work)

### Cost Strategy

At ~$5-20/day for the super elder's read-heavy advisory role, this is viable even at current economics. The value proposition: one entity that remembers the entire project history without degradation for weeks or months. Compare that to the cost of agents repeatedly re-learning context from scratch.

### The 250-Year-Old Elder Analogy

A human elder at 80 has ~60 years of adult experience but fading recall. A hypothetical 250-year-old has ~230 years but recall fades at 250. The million-token model is the 250-year-old — the degradation threshold is so far out that it functions as a near-permanent source of truth for any realistic project timeline.

---

## Team vs. Specialized Teams

### Option A: One Team Does Everything

Research → Planning → PRD → Coding → Testing → All handled by one staggered team.

**Pros:**
- Maximum shared context — everyone knows everything
- No knowledge transfer overhead between teams
- Simpler orchestration

**Cons:**
- Faster context burn (more diverse tasks = more tokens per agent)
- May accumulate elders faster than they're useful
- Harder to parallelize (team is one bottleneck)

### Option B: Specialized Teams

Separate teams for: Research, Planning/PRD, Implementation, Testing/QA

**Pros:**
- Each team's context is focused and efficient
- Teams can work in parallel on different phases
- Elders within each team have deep domain expertise

**Cons:**
- Knowledge transfer between teams burns context on both sides
- Information loss at team boundaries
- More complex orchestration
- Teams may miss cross-cutting concerns

### Option C: Hybrid (Recommended Starting Point)

One core team handles the full lifecycle but delegates specific tasks to short-lived specialist sub-agents that report back.

- Core team: 2-3 staggered agents + 1 super elder
- Sub-agents: Fresh, disposable agents for specific tasks (research a library, implement a component, run tests)
- Sub-agents report results through the briefing protocol → knowledge base
- Core team makes decisions, sub-agents execute

This preserves the shared context advantage while keeping the core team's context burn manageable.

---

## Consensus and Decision-Making

### The Problem with Large Groups

50 elders can't reach consensus. Even 5 agents debating takes tokens and time. The decision-making structure must be explicit.

### Proposed Hierarchy

1. **Human** (you): Final authority. Sets direction, breaks deadlocks, approves major decisions
2. **Lead Operator**: Day-to-day decisions within established direction. Doesn't need human approval for routine implementation choices
3. **Elder Council** (1-3 elders max active at once): Consulted on architectural decisions. Provide input, don't vote. Lead Operator synthesizes their input
4. **Super Elder** (million-token model): Consulted on strategic/directional questions. Provides historical context. One voice, not a committee

### Decision Flow

```
Routine implementation → Lead Operator decides alone
Architectural choice   → Lead Operator proposes → Elder Council reviews → Lead decides
Strategic direction    → Lead Operator proposes → Super Elder + Elder Council input → Human decides
```

### Active Elder Cap

No more than 2-3 elders should be active at any time. Older elders gracefully retire (their knowledge lives on in the knowledge base). This prevents the "50 elders" problem.

---

## Integration with AutoForge

### Where This Lives

This system operates ON TOP of AutoForge's existing infrastructure:

- **Queue System**: Projects line up in queue as today. The team system manages HOW each project gets built, not WHAT gets built
- **DunkStack**: Phase orchestration for individual projects. The team operates within each phase
- **Workspace**: Where active projects are managed. Team status would be visible here
- **Portable Widgets**: The modular UI components being built now would display team status, elder council state, knowledge base health

### New Components Needed

1. **Team Manager Service**: Tracks agent lifecycles, context usage, role assignments, rotation triggers
2. **Knowledge Base Service**: Persistent storage for the shared knowledge base, with read/write APIs
3. **Briefing Protocol Engine**: Filters sub-agent results for significance before writing to knowledge base
4. **Context Monitor**: Tracks each agent's estimated context usage and triggers rotation events
5. **Multi-Model Router**: Directs tasks to the appropriate model based on role and task type

### Phased Implementation

**Phase 0 (Now):** Finish the modular widget architecture so team UI components are portable
**Phase 1:** Knowledge base service + basic shared document system
**Phase 2:** Two-agent staggered rotation (one lead, one rising) with manual model selection
**Phase 3:** Elder role + context-based rotation triggers
**Phase 4:** Multi-model integration (Opus + GPT 5.4 + Gemini in coordinated roles)
**Phase 5:** Million-token super elder integration
**Phase 6:** Automated team management with queue-aware scheduling

---

## 24/7 Operations Model

### Current Constraints (Subscription Tier)

| Model | Daily Capacity | Best Use |
|-------|---------------|----------|
| Opus 4.6 | ~5.5 hours | Complex architecture, critical decisions |
| Sonnet 4.6 | ~67 hours | Bulk implementation, routine tasks |
| GPT 5.4 Codex | TBD (new) | Implementation, cross-model validation |
| Gemini 3.1 | TBD | Research, long-context advisory |

### Optimized 24-Hour Cycle

- Sonnet/GPT 5.4 handle the bulk implementation (sub-agent work)
- Opus reserved for lead operator and elder advisory roles
- Gemini as persistent super elder (low burn rate, always available)
- Human sets the queue before bed → agents execute overnight → review results in morning

### The Vision

With the queue system, modular phase builder, and team architecture:
1. Plan projects and create PRDs during the day
2. Queue them up with phase dependencies
3. Team executes overnight using optimized model allocation
4. Morning review: approve gates, adjust direction, queue more work
5. Repeat

---

## Open Questions for the Trifecta Discussion

1. **Rotation interval**: Is 15-20% context the right trigger for bringing on a new agent, or should it be task-based (after completing a phase)?
2. **Knowledge base format**: Structured JSON/YAML vs. natural language markdown? Trade-off between machine-parseable and human-readable
3. **Elder cap**: Is 2-3 active elders the right number, or should it flex based on project complexity?
4. **Cross-model pairing**: Which model combinations work best for the two-builder pattern? Does Opus + GPT 5.4 outperform two Opus instances?
5. **Sub-agent model selection**: Should sub-agents always be the cheapest viable model, or match the lead operator's model for consistency?
6. **Cost monitoring**: How granular should cost tracking be? Per-agent? Per-role? Per-phase?
7. **Failure handling**: When an elder gives advice that the lead operator suspects is degradation-influenced, what's the protocol?
8. **Knowledge base pruning**: As the project grows, does the knowledge base itself need summarization to prevent bloat?
9. **Million-token economics**: At what project size/value does the super elder ROI justify the cost?
10. **Human involvement ratio**: How much human oversight is optimal? Full approval gates? Spot checks? Trust the team after calibration?

---

*This document is the foundation for a trifecta discussion between Claude Opus 4.6, GPT 5.4 Codex, and Gemini 3.1. Each model should provide their perspective on feasibility, optimizations, blind spots, and recommended starting point.*

*Version: 1.0 — Initial formation of idea*
*Date: March 7, 2026*
*Author: Human + Claude Opus 4.6*
