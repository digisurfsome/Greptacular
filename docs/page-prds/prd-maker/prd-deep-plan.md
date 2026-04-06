# PRD: Deep Plan — Multi-Agent Planning Service

> **Status:** Draft
> **Author:** Claude Opus 4.6
> **Date:** 2026-04-06
> **Scope:** Standalone reusable service + PRD Maker integration + immediate availability for workspace/spec chat
> **Difficulty:** 5/10
> **Confidence:** 85%

---

## 1. Problem Statement

AutoForge's current planning flows (spec creation, workspace chat, PRD Maker pipeline) use a single-agent, single-pass approach. The agent reads the codebase, thinks linearly, and produces a plan. This is the equivalent of one person doing everything alone.

Claude Code's Ultra Plan feature demonstrated that a **multi-agent parallel exploration + multi-perspective design** approach produces significantly better plans, faster. Their architecture:

- **Phase 1:** 3 lightweight Explore agents scan the codebase in parallel (different angles)
- **Phase 2:** 1-3 Plan agents design solutions from different perspectives simultaneously
- **Phase 3:** Main agent consolidates, checks alignment
- **Phase 4:** Write structured plan
- **Phase 5:** Present for user approval

We now have the exact prompts, agent configurations, and orchestration logic from their source code. This PRD describes building our own version as a reusable service.

---

## 2. Goals

1. **Build a `DeepPlanService`** — a backend service that orchestrates multi-agent planning for any input
2. **Expose it immediately** in workspace chat and spec creation as an optional "Deep Plan" toggle
3. **Design it for PRD Maker integration** — when PRD Maker UI is built, Deep Plan slots in as a stage
4. **Match Ultra Plan's agent pattern** — 3 parallel Explore agents (Haiku) + 1-3 parallel Plan agents (Sonnet/Opus)
5. **Keep it optional** — simple mode (current single-agent) remains the default. Deep Plan is opt-in.

---

## 3. Non-Goals

1. **NOT replicating Ultra Plan's web review interface** — no inline commenting on individual words/phrases. Section-level approve/revise is sufficient.
2. **NOT building a separate "cloud" execution environment** — everything runs locally against the user's subscription.
3. **NOT replacing existing planning flows** — this augments them. The toggle is off by default.
4. **NOT handling git bundle teleportation** — that's specific to Claude Code's CLI-to-cloud pattern. We don't need it.

---

## 4. Architecture

### 4.1 Service Layer

```
server/services/deep_plan_service.py     ← Core orchestration
server/services/deep_plan_agents.py      ← Agent prompt templates
server/routers/deep_plan.py              ← REST + SSE endpoints
```

### 4.2 The 5-Phase Pipeline

#### Phase 1: Parallel Exploration (3x Haiku agents)

**What:** Spawn 3 Explore agents simultaneously. Each gets a different search focus:

| Agent | Focus | Example Prompt Angle |
|-------|-------|---------------------|
| Explorer A | **Structure** — directory layout, file organization, entry points, build system | "Map the project structure, entry points, and build pipeline" |
| Explorer B | **Patterns** — existing code patterns, conventions, shared utilities, state management | "Find recurring patterns, shared utilities, and architectural conventions" |
| Explorer C | **Integration Points** — APIs, data flow, external dependencies, boundaries | "Map external dependencies, API boundaries, and data flow between components" |

**Model:** Haiku (fast, cheap — matches Claude Code's approach)
**Mode:** Read-only (Glob, Grep, Read only — no writes)
**Timeout:** 60 seconds per agent
**Output:** Structured findings in JSON format:

```json
{
  "agent": "structure",
  "files_examined": 47,
  "findings": [
    {
      "category": "entry_point",
      "path": "server/main.py",
      "summary": "FastAPI server with router registration"
    }
  ],
  "critical_files": ["server/main.py", "ui/src/App.tsx"],
  "duration_seconds": 12
}
```

#### Phase 2: Parallel Design (1-3x Plan agents)

**What:** Spawn Plan agents with different perspectives based on the task type:

| Task Type | Perspective A | Perspective B | Perspective C |
|-----------|--------------|--------------|--------------|
| **New feature** | Simplicity-first | Performance-first | Maintainability-first |
| **Bug fix** | Root cause fix | Pragmatic workaround | Prevention/hardening |
| **Refactoring** | Minimal change | Clean architecture | Progressive migration |

**Model:** User's configured model (Sonnet or Opus via subscription)
**Mode:** Read-only
**Input:** User's original request + all Phase 1 findings merged
**Timeout:** 120 seconds per agent
**Output:** Structured plan in markdown with required sections:

```markdown
## Approach: [Perspective Name]

### Summary
[1-2 sentence approach description]

### Implementation Steps
1. [Step with file path]
2. [Step with file path]
...

### Critical Files
- path/to/file.py — [what changes and why]

### Risks
- [Risk 1]
- [Risk 2]

### Estimated Complexity
[X/10]
```

**Agent Count Logic:**
- Quick mode (default): 1 Plan agent
- Deep mode (toggled): 3 Plan agents with different perspectives
- Configurable via `DEEP_PLAN_AGENT_COUNT` env var (1-5)

#### Phase 3: Consolidation (Main agent)

**What:** The service's main agent (not a sub-agent) reads:
1. All Phase 1 exploration findings
2. All Phase 2 plan proposals
3. The user's original request

Then produces a consolidated plan that:
- Picks the best approach (or merges elements from multiple)
- Resolves conflicts between perspectives
- Verifies alignment with the original request
- Flags any gaps or risks

**Model:** User's configured model
**Output:** Single structured plan document

#### Phase 4: Plan Document

**What:** Write the final plan to a structured markdown document with these sections:

```markdown
# Deep Plan: [Task Title]

## Context
[What exists today, key findings from exploration]

## Approach
[The chosen approach with rationale]

## Implementation Plan

### Step 1: [Description]
- **File:** path/to/file
- **Change:** [What to add/modify/remove]
- **Why:** [Rationale]

### Step 2: ...

## Files to Modify
| File | Action | Description |
|------|--------|-------------|
| ... | Create/Modify/Delete | ... |

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| ... | Low/Medium/High | ... |

## Verification
- [ ] [How to verify step 1]
- [ ] [How to verify step 2]

## Rejected Alternatives
| Alternative | Why Rejected |
|------------|-------------|
| [Perspective B approach] | [Reason] |
```

#### Phase 5: User Approval

**What:** Present the plan to the user. Three actions:
- **Approve** — proceed with execution (or feed into next pipeline stage)
- **Revise** — user provides section-level feedback, re-run Phase 3-4 with feedback
- **Reject** — discard and start over (or fall back to simple mode)

**Revision loop:** Max 3 iterations. After 3, auto-approve with user's latest feedback incorporated.

---

### 4.3 Backend Implementation

```python
# server/services/deep_plan_service.py

class DeepPlanService:
    """Multi-agent planning service using Claude Code's 5-phase pattern."""

    def __init__(self, project_dir: str, model: str = None):
        self.project_dir = project_dir
        self.model = model or "sonnet"  # Default to Sonnet
        self.explore_model = "haiku"     # Always Haiku for exploration
        self.plan_agent_count = 3        # Configurable
        self.explore_agent_count = 3     # Configurable

    async def run_deep_plan(
        self,
        user_request: str,
        context: dict = None,        # Optional pre-existing context (from PRD Maker stages)
        on_progress: Callable = None, # Real-time progress callback
        task_type: str = "feature",   # feature | bugfix | refactor
    ) -> DeepPlanResult:
        """Execute the full 5-phase deep plan pipeline."""

        # Phase 1: Parallel Exploration
        explore_results = await self._run_explore_phase(user_request, on_progress)

        # Phase 2: Parallel Design
        plan_proposals = await self._run_design_phase(
            user_request, explore_results, task_type, on_progress
        )

        # Phase 3: Consolidation
        consolidated = await self._run_consolidation(
            user_request, explore_results, plan_proposals, context, on_progress
        )

        # Phase 4: Document
        plan_doc = self._format_plan_document(consolidated)

        return DeepPlanResult(
            plan=plan_doc,
            explore_results=explore_results,
            proposals=plan_proposals,
            consolidated=consolidated,
            phase_durations={...}
        )

    async def _run_explore_phase(self, request, on_progress):
        """Spawn 3 Explore agents in parallel."""
        agents = [
            self._spawn_explore_agent("structure", request),
            self._spawn_explore_agent("patterns", request),
            self._spawn_explore_agent("integration", request),
        ]
        results = await asyncio.gather(*agents, return_exceptions=True)
        # Filter out failures, merge findings
        return self._merge_explore_results(results)

    async def _run_design_phase(self, request, explore_results, task_type, on_progress):
        """Spawn 1-3 Plan agents in parallel with different perspectives."""
        perspectives = PERSPECTIVE_MAP[task_type][:self.plan_agent_count]
        agents = [
            self._spawn_plan_agent(perspective, request, explore_results)
            for perspective in perspectives
        ]
        results = await asyncio.gather(*agents, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    async def _spawn_explore_agent(self, focus: str, request: str):
        """Single explore agent using Haiku via SDK."""
        # Uses _call_via_sdk() pattern from yt_processor.py
        # permission_mode="acceptEdits" + settings file
        # Wrapped in try/except for rate_limit_event recovery
        ...

    async def _spawn_plan_agent(self, perspective: str, request: str, context: str):
        """Single plan agent using user's configured model via SDK."""
        ...
```

### 4.4 Agent Prompts

Adapted directly from Claude Code's source with modifications for AutoForge context:

#### Explore Agent Prompt

```
You are a codebase exploration specialist. You excel at rapidly finding and
understanding code structure.

=== READ-ONLY MODE — NO FILE MODIFICATIONS ===

Your assigned focus: {focus_area}

## Task
Explore this codebase to answer: {user_request}

Focus specifically on: {focus_description}

## Instructions
1. Use Glob to find relevant files by pattern
2. Use Grep to search for keywords and patterns
3. Use Read to examine critical files (use offset/limit for large files)
4. Be FAST — you are optimized for speed, not thoroughness
5. Spawn parallel tool calls wherever possible

## Output Format
Return a structured JSON with your findings:
{
  "focus": "{focus_area}",
  "files_examined": <count>,
  "findings": [
    {"category": "...", "path": "...", "summary": "..."}
  ],
  "critical_files": ["path1", "path2", ...],
  "key_patterns": ["pattern1", "pattern2", ...],
  "duration_note": "..."
}
```

#### Plan Agent Prompt

```
You are a software architect designing an implementation plan.

=== READ-ONLY MODE — NO FILE MODIFICATIONS ===

Your assigned perspective: {perspective_name}
Perspective guidance: {perspective_description}

## Context from Codebase Exploration
{merged_explore_results}

## User's Request
{user_request}

## Your Process
1. Understand requirements through your perspective lens
2. Explore specific files if needed (you have read access)
3. Design a solution optimized for {perspective_name}
4. Produce a detailed, step-by-step implementation plan

## Required Output

### Approach: {perspective_name}

#### Summary
[1-2 sentences]

#### Implementation Steps
[Numbered list with specific file paths]

#### Critical Files
[List with what changes and why]

#### Risks
[What could go wrong with this approach]

#### Estimated Complexity
[X/10 with justification]
```

### 4.5 Perspective Definitions

```python
# server/services/deep_plan_agents.py

PERSPECTIVE_MAP = {
    "feature": [
        {
            "name": "Simplicity-First",
            "description": "Minimize new code. Reuse existing patterns. Fewest files changed. "
                          "Prefer composition over new abstractions. Ship fast.",
        },
        {
            "name": "Performance-First",
            "description": "Optimize for speed and resource efficiency. Consider caching, "
                          "lazy loading, pagination, parallel execution. Measure what matters.",
        },
        {
            "name": "Maintainability-First",
            "description": "Optimize for long-term code health. Clean abstractions, clear "
                          "separation of concerns, comprehensive error handling, easy to test.",
        },
    ],
    "bugfix": [
        {
            "name": "Root Cause",
            "description": "Find and fix the actual source of the bug. No band-aids. "
                          "Trace the full call chain. Fix it properly even if it takes longer.",
        },
        {
            "name": "Pragmatic Fix",
            "description": "Get it working with minimal risk. Targeted change, maximum safety. "
                          "Add guardrails to prevent recurrence without large refactors.",
        },
        {
            "name": "Prevention",
            "description": "Fix the bug AND harden the system. Add validation, tests, "
                          "type guards. Make this class of bug impossible going forward.",
        },
    ],
    "refactor": [
        {
            "name": "Minimal Change",
            "description": "Smallest possible refactor that achieves the goal. Preserve "
                          "existing APIs. Minimize blast radius. Ship incrementally.",
        },
        {
            "name": "Clean Architecture",
            "description": "Do it right. Proper separation of concerns, clear interfaces, "
                          "testable components. Accept more churn now for a better codebase.",
        },
        {
            "name": "Progressive Migration",
            "description": "Build the new alongside the old. Migrate callers one at a time. "
                          "Both old and new work simultaneously during transition.",
        },
    ],
}
```

---

### 4.6 Frontend Integration

#### Workspace Chat Integration (Immediate)

Add a "Deep Plan" toggle button to the workspace chat input area:

```tsx
// ui/src/components/workspace/DeepPlanToggle.tsx

function DeepPlanToggle({ enabled, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={cn(
        "flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-bold",
        "border-2 border-black transition-all",
        enabled
          ? "bg-violet-400 text-black shadow-neo-sm"
          : "bg-muted text-muted-foreground hover:bg-violet-100"
      )}
      title="Deep Plan: Multi-agent parallel planning (uses more tokens, better plans)"
    >
      <Brain className="h-3.5 w-3.5" />
      Deep Plan
    </button>
  )
}
```

When enabled, the chat sends `{ deep_plan: true, task_type: "feature" }` alongside the message. The backend routes through `DeepPlanService` instead of direct SDK call.

#### Plan Review Component (Shared)

```tsx
// ui/src/components/deep-plan/DeepPlanReview.tsx

function DeepPlanReview({ plan, onApprove, onRevise, onReject }) {
  // Renders the structured plan document
  // Each section has an approve/revise indicator
  // Revise opens an inline text input for that section
  // Bottom bar: [Approve Plan] [Request Revision] [Reject]
}
```

#### Progress Indicator

During Deep Plan execution, show a phase indicator:

```
[✓ Exploring] → [● Designing] → [ Consolidating] → [ Ready]
     12s              ...
```

Each phase shows:
- Agent count (e.g., "3 agents exploring")
- Elapsed time
- Key findings as they stream in

---

### 4.7 PRD Maker Integration (Future)

When PRD Maker is built, Deep Plan integrates as follows:

**Insertion Point:** Between **Stage 4 (Mechanism Extraction)** and **Stage 6a (Arrangement Selection)**

The Deep Plan stage would:
1. **Input:** Context packet with extracted mechanisms, Wall/Door/Room classifications, structural analysis
2. **Explore Phase:** Agents scan for existing code that maps to mechanisms (if expanding an existing project) or scan boilerplate for relevant patterns (if greenfield)
3. **Design Phase:** Agents propose architectural arrangements from different perspectives, informed by the mechanism map
4. **Output:** Feeds into Stage 6a (Arrangement Selection) with pre-analyzed options

This replaces the need for the user to manually think through arrangements — the agents have already explored options.

**Context Packet Fields Added:**

```json
{
  "deep_plan": {
    "enabled": true,
    "task_type": "feature",
    "explore_results": {...},
    "proposals": [...],
    "consolidated_plan": "...",
    "selected_perspective": "simplicity-first",
    "phase_durations": {...}
  }
}
```

---

## 5. Token Budget

| Phase | Model | Estimated Tokens (In) | Estimated Tokens (Out) | Cost on Subscription |
|-------|-------|-----------------------|------------------------|---------------------|
| Phase 1 (3x Explore) | Haiku | ~15K each = 45K total | ~3K each = 9K total | Minimal |
| Phase 2 (3x Plan) | Sonnet/Opus | ~30K each = 90K total | ~5K each = 15K total | Moderate |
| Phase 3 (Consolidation) | Sonnet/Opus | ~50K (all inputs merged) | ~5K | Low |
| **Total** | | **~185K** | **~29K** | **~1-2% of hourly quota** |

For comparison, Claude Code's Ultra Plan uses roughly similar token counts but on cloud compute. Our version runs against the user's subscription quota.

**Quick mode (1 Plan agent):** ~95K in, ~17K out — about half the cost.

---

## 6. Configuration

```python
# Environment variables (optional overrides)
DEEP_PLAN_EXPLORE_COUNT=3       # Number of explore agents (1-5)
DEEP_PLAN_AGENT_COUNT=3         # Number of plan agents (1-5)
DEEP_PLAN_EXPLORE_TIMEOUT=60    # Seconds per explore agent
DEEP_PLAN_DESIGN_TIMEOUT=120    # Seconds per plan agent
DEEP_PLAN_MODEL=sonnet          # Override plan agent model
DEEP_PLAN_EXPLORE_MODEL=haiku   # Override explore agent model
```

Also configurable in Settings UI:
- Toggle: Deep Plan enabled/disabled (global default)
- Slider: Plan agent count (1-3)
- Dropdown: Default task type (feature/bugfix/refactor)

---

## 7. Differences from Claude Code's Ultra Plan

| Aspect | Ultra Plan | Our Deep Plan |
|--------|-----------|---------------|
| **Runs on** | Anthropic's cloud containers | User's local machine via subscription |
| **Explore model** | Haiku | Haiku (same) |
| **Plan model** | Always Opus 4.6 | User's choice (Sonnet or Opus) |
| **Review interface** | Rich web UI with inline commenting | Section-level approve/revise in AutoForge UI |
| **Requires git repo** | Yes (syncs via git bundle) | No (reads filesystem directly) |
| **Pre-existing context** | None — starts cold from codebase | Can receive PRD Maker context packet, past chat history, etc. |
| **Teleport** | Plan ships between cloud ↔ terminal | N/A — everything stays in AutoForge |
| **Cost visibility** | Hidden (uses cloud quota) | Visible (standard subscription usage) |

**Our advantage:** We can feed Deep Plan rich pre-existing context from PRD Maker stages (rant extraction, mechanism map, Wall/Door/Room classifications). Ultra Plan always starts cold.

---

## 8. Implementation Phases

### Phase 1: Core Service (2 days)
- [ ] `server/services/deep_plan_service.py` — orchestration engine
- [ ] `server/services/deep_plan_agents.py` — agent prompts and perspective maps
- [ ] `server/routers/deep_plan.py` — REST endpoints (`POST /api/deep-plan/run`, `GET /api/deep-plan/{id}/status`, `GET /api/deep-plan/{id}/stream`)
- [ ] SSE streaming for real-time progress
- [ ] Integration with `_call_via_sdk()` pattern (all 3 bug fixes)

### Phase 2: Workspace Chat Integration (1 day)
- [ ] Deep Plan toggle button in chat input area
- [ ] Backend routing: when `deep_plan=true`, use DeepPlanService
- [ ] Phase progress indicator in chat
- [ ] Plan review inline in chat thread

### Phase 3: Plan Review Component (1 day)
- [ ] `ui/src/components/deep-plan/DeepPlanReview.tsx` — structured plan display
- [ ] Section-level approve/revise controls
- [ ] Revision submission → re-run Phase 3-4
- [ ] Plan diff view (if revision changes the plan)

### Phase 4: Settings & Polish (1 day)
- [ ] Settings UI: agent count slider, model selection, default task type
- [ ] Token usage display per Deep Plan run
- [ ] Error handling: partial results if agents fail
- [ ] Logging: full progress to both logger and on_progress callback

### Phase 5: PRD Maker Integration (When PRD Maker is Built)
- [ ] Wire Deep Plan into context packet flow
- [ ] Feed mechanism map as pre-context to Plan agents
- [ ] Output feeds into Stage 6a (Arrangement Selection)

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Subscription rate limits from 6+ parallel agents | Medium | High | Sequential fallback: if rate limited, run agents one at a time |
| Haiku Explore agents miss important context | Low | Medium | Merge all findings; main consolidation agent can do supplemental reads |
| Plan agents propose conflicting architectures | Expected | Low | That's the point — consolidation phase resolves conflicts |
| Total runtime exceeds user patience (>5 min) | Low | Medium | Show real-time progress; allow cancellation at any phase |
| Token cost surprises on subscription | Low | Medium | Show estimated token usage before starting; configurable agent count |

---

## 10. Success Criteria

1. Deep Plan produces a structured plan with specific file paths, implementation steps, and risk assessment
2. Multi-agent exploration finds relevant code that a single-agent pass would miss (measurable by comparing findings)
3. Multi-perspective design surfaces tradeoffs the user wouldn't have considered
4. Total execution time < 3 minutes for a typical single-feature plan
5. User can approve, revise (up to 3x), or reject the plan without restarting
6. Service is reusable — workspace chat, spec creation, and future PRD Maker all use the same backend

---

## 11. Source References

Architecture derived from Claude Code source (commit snapshot 2026-04):
- `src/commands/ultraplan.tsx` — Ultra Plan command entry point
- `src/utils/planModeV2.ts` — Agent count configuration, phase gating
- `src/utils/messages.ts` lines 3227-3292 — 5-phase plan mode system message
- `src/tools/AgentTool/built-in/exploreAgent.ts` — Explore agent prompt
- `src/tools/AgentTool/built-in/planAgent.ts` — Plan agent prompt
- `src/utils/teleport.tsx` — Session teleport mechanics (not replicated, reference only)
