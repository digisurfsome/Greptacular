# BLUEPRINT.md - Modification History & Specifications

This is a living document. Every agent that adds features to this codebase MUST append
their changes here so future agents know exactly what was built and why.

---

## Base System: AutoForge

AutoForge is an autonomous coding agent system that builds complete applications from a
specification file (`app_spec.txt`). It uses a two-agent pattern:

1. **Initializer Agent** -- reads the spec, creates features in SQLite, scaffolds the project
2. **Coding Agents** -- implement features one-by-one (or in batches) across multiple sessions

The system auto-continues: when one session ends, a fresh agent picks up with a clean
context window. State persists via SQLite (`features.db`), git history, and `claude-progress.txt`.

**Key files (base system):**
- `agent.py` -- session loop, auto-continue logic
- `client.py` -- ClaudeSDKClient configuration, hooks, MCP servers
- `prompts.py` -- prompt loading with fallback chain, YOLO stripping, batch headers
- `parallel_orchestrator.py` -- concurrent agent execution, dependency-aware scheduling
- `mcp_server/feature_mcp.py` -- MCP tools for feature management (claim, mark, skip, etc.)
- `api/database.py` -- SQLAlchemy Feature model (SQLite)
- `api/dependency_resolver.py` -- Kahn's algorithm, cycle detection, scheduling scores
- `.claude/templates/` -- prompt templates (initializer, coding, testing)

---

## Modification 1: Context Budget Management System

**Date:** 2026-02-10
**Branch:** `claude/study-looper-codebase-NgAc4`
**Commit:** `dccea81`

### Problem

Agents had no awareness of context window usage. They would fill context to 80-90%+,
causing quality degradation -- wrong variable names, broken imports, incomplete logic.
The system had `max_turns=300` for coding and no budget tracking. The only instruction
was a vague "before context fills up" in the coding prompt.

### Solution

Three-layer context budget system targeting **45% context usage per session** with a
**48% hard stop**. This keeps every agent session in the high-quality zone.

### Layer 1: Prompt Instructions

**What agents are told (the exact language):**

The coding prompt now starts with a `CONTEXT BUDGET MANAGEMENT (ABSOLUTE RULE)` section:
- 45% target, 48% hard stop, 50% = degradation
- Turn-based tracking: 135 turns total, wrap up by turn 120, done by 135
- Phase gates: Orient (1-10), Implement (11-100), Verify (100-120), Wrap-up (120-135)
- `[Budget]` checkpoint messages printed every 30 turns
- If PreCompact fires = emergency, stop immediately
- Golden rules: small features fit easily, large features get split via `feature_split`
- "Incomplete-but-solid beats complete-but-buggy"

The initializer prompt now has a `FEATURE SIZING FOR CONTEXT BUDGET` section:
- Small (2-5 steps): batch 2-3 per session
- Medium (6-10 steps): one per session
- Large (10+ steps): must be split into sequential features with dependencies
- No single feature should need >120 turns
- Examples of good splits provided

Single-feature and batch-feature headers in `prompts.py` now include:
- Budget reminder: "45% target, 48% hard stop"
- Batch workflow adds "CHECK YOUR BUDGET" step after each feature
- "It is OK to not finish all assigned features"

**Files changed:**
- `.claude/templates/coding_prompt.template.md` -- new section at top, updated Step 9, updated final reminder
- `.claude/templates/initializer_prompt.template.md` -- new sizing section after feature requirements
- `prompts.py` -- updated `get_single_feature_prompt()` and `get_batch_feature_prompt()` headers

### Layer 2: Code Guardrails

**max_turns reduction** (`client.py`):
- Coding: 300 -> 150 (safety net, prompt says wrap up earlier)
- Testing: 100 -> 75
- Initializer: 300 -> 200

**Turn counting** (`agent.py`):
- Counts `AssistantMessage` events in `run_agent_session()`
- Prints `[Budget] Turn N/150 (~X% context used)` every 30 turns
- Warning at turn 120: "WRAP UP NOW"
- Hard stop message at turn 135+
- Constants: `BUDGET_TARGET_TURNS=135`, `BUDGET_WARN_TURNS=120`, `BUDGET_CHECKPOINT_INTERVAL=30`

**PreCompact emergency signal** (`client.py`):
- When auto-compaction fires, prints a loud `CONTEXT BUDGET EXCEEDED - EMERGENCY WRAP-UP REQUIRED` banner
- Compaction guidance now starts with `CRITICAL: CONTEXT BUDGET EXCEEDED - SESSION MUST END`
- Tells the summarizer to instruct the agent to commit and stop

**Files changed:**
- `client.py` -- max_turns_map values, PreCompact hook output, compaction guidance, added `feature_split` to `CODING_AGENT_TOOLS`
- `agent.py` -- new constants, turn counting logic in `run_agent_session()`

### Layer 3: Smart Batching + Feature Splitting

**Budget-aware batch building** (`parallel_orchestrator.py`):
- New `_estimate_feature_turns()` static method: `max(len(steps) * 10, 30)` turns per feature
- `build_feature_batches()` now tracks `batch_turns` and stops adding features when budget is reached
- Both chain extension and same-category fill phases respect the turn budget
- Constants: `BUDGET_USABLE_TURNS=120`, `TURNS_PER_STEP=10`, `MIN_FEATURE_TURNS=30`

**Feature split tool** (`mcp_server/feature_mcp.py`):
- New `feature_split(feature_id, split_after_step, part2_name)` MCP tool
- Splits a feature at a step boundary: Part 1 keeps steps 1..N, Part 2 gets the rest
- Part 1 gets " (Part 1)" appended to name
- Part 2 is created as a new feature depending on Part 1 + all of Part 1's original deps
- Validates: feature exists, not already passing, has 2+ steps, valid split point

**Files changed:**
- `parallel_orchestrator.py` -- new constants, `_estimate_feature_turns()`, modified `build_feature_batches()`
- `mcp_server/feature_mcp.py` -- new `feature_split` tool (100 lines)
- `client.py` -- added `mcp__features__feature_split` to `CODING_AGENT_TOOLS`

### How It All Works Together

```
Initializer creates right-sized features (sizing guidance)
              |
Orchestrator builds budget-aware batches (step count estimation)
              |
Agent starts session with budget instructions (prompt)
              |
Turn counter prints [Budget] checkpoints (agent.py)
              |
Agent wraps up by turn 120-135 (prompt discipline)
              |
If agent ignores budget: max_turns=150 hard ceiling (client.py)
              |
If context fills anyway: PreCompact fires emergency stop (client.py)
              |
If feature too big: agent uses feature_split tool (feature_mcp.py)
              |
Fresh agent picks up remaining work with full context
```

---

<!-- NEXT MODIFICATION GOES HERE -->
<!-- Copy the template below and fill it in:

## Modification N: [Title]

**Date:** YYYY-MM-DD
**Branch:** `branch-name`
**Commit:** `hash`

### Problem
What was wrong or missing.

### Solution
What was built and why.

### Files Changed
- `file.py` -- what changed

### How It Works
Brief explanation of the mechanism.

---

-->
