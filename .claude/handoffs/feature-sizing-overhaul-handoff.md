# Feature Sizing System Overhaul — Context-Budget-First Architecture

## Status: Ready for Deep Analysis and Implementation

## Your Mission

You are a fresh agent with a full context window. Your job is to **deeply analyze** the feature sizing system in AutoForge, understand two competing philosophies, and implement a merged approach that takes the best of both. Read EVERYTHING referenced in this document. Ruminate on it. Check for edge cases. Make sure every change is consistent across all files. This is the most critical architectural change to the system.

**Take your time.** You have an entire context window. Use it to think deeply, not to rush.

---

## The Two Philosophies

### Philosophy A: "Granularity-First" (Original Creator)

The original AutoForge creator designed the system around **many tiny features** (165-405 per project). Each feature is a single testable behavior (e.g., "User can create a todo"). The Initializer agent creates ALL features upfront, and coding agents pick them up one by one (or in batches of 1-3).

**The reasoning:** Small features are easy to test, easy to retry, and enable parallel execution. If one fails, the blast radius is tiny.

**The problem:** This approach doesn't explicitly enforce context budget limits. It HOPES features stay small enough. And with 200+ features, you get massive session overhead — each agent session spends ~30 turns on orientation and wrap-up, producing zero code.

### Philosophy B: "Budget-First" (Current Owner)

The current owner added a **hard 45% context window cap** (turn 120 wrap-up, turn 135 done, SDK max_turns=150 hard stop). This is NON-NEGOTIABLE. The owner spent 3 weeks debugging issues caused by agents exceeding 50% context, and will never allow that again.

**The reasoning:** Agent quality degrades past 50% context usage. By capping at 45%, every feature gets implemented correctly the first time. Quality over quantity.

**The problem:** With 200+ tiny features, many sessions waste 70-80% of their context budget on features that only need 20-30% of it. The batch size cap of 3 doesn't help enough.

### The Goal: Merge Both

Create features that are:
1. **Independently testable** (from Philosophy A)
2. **Sized to fill the 45% budget** (from Philosophy B)
3. **Wide dependency graphs** (from Philosophy A — enables parallel agents)
4. **Minimizing session overhead** (from Philosophy B — fewer sessions needed)

---

## What Needs to Change

### Change 1: Initializer Prompt — Feature Sizing Rules

**File:** `.claude/templates/initializer_prompt.template.md`

**Current state (lines 65-83):** The sizing guidelines say:
- Small features: 2-5 steps (orchestrator may batch 2-3)
- Medium features: 6-10 steps (one per session)
- Large features: 10+ steps (must be split if 15+ complex steps)
- Rule: No feature should require more than ~120 turns

**What's wrong:** These guidelines create features that are SMALLER than the budget allows. A 2-step feature uses ~30 turns of a 120-turn budget (25%). Even batching 3 of these only fills 75%. The guidelines optimize for granularity, not budget utilization.

**What to change:** Rewrite the sizing section to be **context-budget-first**. Key principles:
- Target feature size: 40-80 estimated turns (33-67% of the 120-turn budget)
- This leaves room for batching 1-2 features per session, or running a medium feature solo
- Group related small behaviors into single features when they share the same code paths
- Split only when a feature would exceed 100 estimated turns
- Keep each feature independently testable — the feature's steps must define a complete, verifiable behavior

**Specific rewrite needed for the sizing guidelines section:**

Replace the current "Small/Medium/Large" tiers with a budget-aware approach:
- **Compact features (3-5 steps, ~30-50 turns):** These are quick wins. The orchestrator will batch 2-3 of these together to fill the budget. Good for: form validation, empty states, navigation tests, responsive checks.
- **Standard features (6-10 steps, ~60-100 turns):** The sweet spot. One per session. These should be the MAJORITY of features. Good for: full CRUD on an entity, a complete UI page with interactions, an API endpoint with validation and error handling.
- **Maximum features (11-12 steps, ~100-120 turns):** Use sparingly. These fill the entire budget solo. Good for: complex multi-step workflows, integration features that touch many parts of the stack.
- **NEVER create features over 12 steps.** If a behavior needs more, split it into two features with a dependency. Each part must be independently testable.

**Also update the feature count tiers (lines 54-57):**

Current:
```
- Simple apps: ~165 tests
- Medium apps: ~265 tests
- Advanced apps: ~405+ tests
```

Replace with budget-aware tiers:
```
- Simple apps: 30-55 features
- Medium apps: 55-80 features
- Advanced apps: 80-120 features
```

The total number of features is LOWER because each feature is LARGER (but still within budget). The same total work gets done in fewer sessions with less overhead.

**Critical:** The mandatory infrastructure features (indices 0-4) stay exactly as they are. The 20 mandatory test categories stay exactly as they are. The dependency rules stay exactly as they are. We are ONLY changing how features are SIZED, not how they are structured or categorized.

### Change 2: Initializer Prompt — Feature Grouping Rules (NEW)

**File:** `.claude/templates/initializer_prompt.template.md`

**Add a new section** after the sizing guidelines that teaches the Initializer HOW to group small behaviors into budget-efficient features without losing testability.

**Content for new "Feature Grouping" section:**

```markdown
### FEATURE GROUPING (Maximize Budget Utilization)

Small behaviors that share code paths should be GROUPED into a single feature.
Each grouped feature must still be independently testable — the steps must
define a complete verification sequence.

**When to group:**
- Same entity, same page (e.g., "Create todo" + "form validates required fields"
  + "success toast appears" = one feature: "User can create a todo with
  validation and feedback")
- Same API endpoint, multiple validations (e.g., "returns 401 for no auth" +
  "returns 400 for invalid body" + "returns 201 for valid request" = one feature:
  "API validates and processes todo creation requests")
- Same UI component, multiple states (e.g., "shows loading skeleton" +
  "shows empty state" + "shows populated list" = one feature: "Todo list
  displays correct state for loading, empty, and populated conditions")

**When NOT to group:**
- Different entities (don't combine user CRUD with todo CRUD)
- Different pages (don't combine dashboard tests with settings tests)
- Unrelated concerns (don't combine accessibility with performance)
- Features that have different dependency requirements

**Grouping examples:**

BAD (3 tiny features, each wastes 75% of budget):
  Feature A: "User can create a todo" (2 steps, ~30 turns)
  Feature B: "Create form validates required fields" (2 steps, ~30 turns)
  Feature C: "Success toast appears on create" (2 steps, ~30 turns)

GOOD (1 standard feature, uses ~60% of budget):
  Feature A: "User can create a todo with validation and feedback" (6 steps, ~60 turns)
    Step 1: Navigate to todo list, click "New Todo"
    Step 2: Submit empty form, verify validation errors on required fields
    Step 3: Fill in valid data, submit
    Step 4: Verify success toast appears
    Step 5: Verify todo appears in the list
    Step 6: Verify todo persists after page refresh
```

### Change 3: Parallel Orchestrator — Batch Size Limits

**File:** `parallel_orchestrator.py`

**Current state (line 208):**
```python
self.batch_size = min(max(batch_size, 1), 3)  # Clamp 1-3
```

**What's wrong:** The cap of 3 is too restrictive for budget-efficient batching. If you have 3 compact features (30 turns each = 90 turns total), there's room for a 4th. The current cap prevents this.

**What to change:** Increase the clamp to 5:
```python
self.batch_size = min(max(batch_size, 1), 5)  # Clamp 1-5
```

**Also update the CLI argument validation** in `autonomous_agent_demo.py` (around line 183-187):
```python
# Current: parser.add_argument('--batch-size', type=int, default=3, choices=range(1, 4))
# Change to: parser.add_argument('--batch-size', type=int, default=3, choices=range(1, 6))
```

**Why 5 and not unlimited:** The orchestrator's batch builder still respects the 120-turn budget limit (`BUDGET_USABLE_TURNS`). Even with batch_size=5, it won't add more features than fit in the budget. The cap prevents pathological cases where many trivial features (1-step each) get batched into an unmanageable set.

**Note:** The default of 3 stays the same. This just raises the CEILING for power users who want more aggressive batching.

### Change 4: Parallel Orchestrator — Turn Estimation Enhancement

**File:** `parallel_orchestrator.py`

**Current state (lines 403-419):**
```python
@staticmethod
def _estimate_feature_turns(feature: dict) -> int:
    steps = feature.get("steps") or []
    step_count = len(steps) if isinstance(steps, list) else 0
    return max(step_count * TURNS_PER_STEP, MIN_FEATURE_TURNS)
```

**What's wrong:** All steps are treated as equal complexity. "Create a database table" and "Implement full WebSocket proxy with event translation, buffering, and reconnection handling" both count as 10 turns.

**What to change:** Use step text length as an additional signal:
```python
@staticmethod
def _estimate_feature_turns(feature: dict) -> int:
    steps = feature.get("steps") or []
    if not isinstance(steps, list) or not steps:
        return MIN_FEATURE_TURNS

    total = 0
    for step in steps:
        step_text = str(step) if step else ""
        # Base cost per step
        step_turns = TURNS_PER_STEP
        # Complex steps (long descriptions) get a multiplier
        if len(step_text) > 200:
            step_turns = int(step_turns * 1.5)  # 15 turns for complex steps
        elif len(step_text) > 400:
            step_turns = int(step_turns * 2.0)  # 20 turns for very complex steps
        total += step_turns

    return max(total, MIN_FEATURE_TURNS)
```

**Why step text length:** A step that says "Create users table with id, name, email columns" is 50 chars and simple. A step that says "Implement WebSocket proxy that validates JWT from Authorization header, looks up worker URL from builds table, opens proxied connection, translates event formats, persists key events back to database, and handles reconnection with event replay" is 250+ chars and complex. Length correlates with complexity.

**Consider also:** Adding a `complexity_hint` field to the Feature model in `api/database.py` — but this is a larger change that affects the MCP server and Initializer. The text-length approach is simpler and doesn't require schema changes.

### Change 5: Coding Prompt — Batch Workflow Clarity

**File:** `.claude/templates/coding_prompt.template.md`

**Current state:** The batch workflow (injected by `get_batch_feature_prompt()` in `prompts.py`) says "process features IN ORDER" and "check your budget after each."

**What to add:** Make the budget-awareness more explicit:

After completing each feature in a batch, the agent should estimate remaining budget:
```
After marking a feature passing, estimate your remaining budget:
- Count your approximate turn number (each tool call + response ≈ 1 turn)
- If under turn 90: proceed to next feature
- If between turn 90-110: proceed only if next feature is compact (≤ 5 steps)
- If over turn 110: skip remaining features, begin wrap-up
- If over turn 120: wrap up immediately, no new implementation
```

### Change 6: The Spec Format — Feature Count Guidance

**File:** `.claude/autoforge-prd-context.md`

**Current state (Appendix B):**
```
Feature count reference:
- Simple: 25-55 features (expanded to ~165 test cases by Initializer)
- Medium: ~105 features (expanded to ~265 test cases)
- Advanced: 155-205 features (expanded to ~405 test cases)
```

**What's wrong:** This implies the Initializer EXPANDS features. But reading the actual code, the Initializer creates EXACTLY the number specified in `feature_count`. There is no expansion. The Initializer prompt says "You must create exactly [FEATURE_COUNT] features." So the context doc is misleading.

**What to change:**
```
Feature count reference (budget-aware sizing):
- Simple apps (utility, calculator, notes): 30-55 features
- Medium apps (blog, task manager with auth): 55-80 features
- Advanced apps (e-commerce, CRM, SaaS): 80-120 features

Each feature should be sized to use 30-100 estimated agent turns (of 120 usable).
The Initializer creates EXACTLY the number specified — it does not expand them.
```

**Also update Section 1.4 "Feature Writing Rules" (around line 296-299):**
Remove the "expanded to N test cases" language. Replace with:
```
The Initializer creates exactly the number of features specified in <feature_count>.
Each feature must be independently testable and sized to fit within one coding agent's
45% context budget (~120 usable turns).
```

---

## Files to Modify (Complete List)

| # | File | What Changes | Priority |
|---|------|-------------|----------|
| 1 | `.claude/templates/initializer_prompt.template.md` | Feature sizing rules, feature count tiers, add grouping rules | CRITICAL |
| 2 | `parallel_orchestrator.py` | Batch size clamp (3→5), turn estimation enhancement | HIGH |
| 3 | `autonomous_agent_demo.py` | CLI batch-size choices (1-4 → 1-6) | HIGH |
| 4 | `.claude/templates/coding_prompt.template.md` | Budget-awareness in batch workflow | MEDIUM |
| 5 | `.claude/autoforge-prd-context.md` | Feature count tiers, remove "expansion" language | MEDIUM |
| 6 | `prompts.py` | get_batch_feature_prompt() — enhance budget instructions | LOW |

---

## What NOT to Change

These parts of the system are solid and should be preserved exactly:

1. **The 45% context budget cap** — Non-negotiable. Turn 120 wrap-up, turn 135 done, SDK max_turns=150.
2. **Budget checkpoint messages** in `agent.py` — Every 30 turns, the agent sees its estimated usage.
3. **The 5 mandatory infrastructure features** — Indices 0-4, no dependencies, run first.
4. **The 20 mandatory test categories** — All 20 must be covered in every project.
5. **The `feature_split` MCP tool** — Runtime escape valve for features that turn out too large.
6. **The dependency system** — DAG enforcement, wide graphs, no cycles.
7. **The `feature_create_bulk` tool** — Features are created in SQLite, immutable after creation.
8. **Parallel orchestrator core logic** — Agent spawning, process management, crash recovery.
9. **The Feature model schema** in `api/database.py` — Don't add fields unless absolutely necessary.

---

## Verification Checklist

After making all changes, verify:

- [ ] Read the initializer prompt end-to-end — does the sizing section make sense with the budget?
- [ ] Read the coding prompt end-to-end — does the batch workflow make sense with larger features?
- [ ] Trace a hypothetical build: 60-feature advanced app, batch_size=3, 3 parallel agents. How many sessions? How much context wasted on overhead?
- [ ] Compare to current: 265-feature advanced app, batch_size=3, 3 parallel agents. How many sessions? How much overhead?
- [ ] Check: can the Initializer still create features across all 20 mandatory test categories with 80-120 features instead of 265?
- [ ] Check: does the turn estimation enhancement work correctly for features with no steps (returns MIN_FEATURE_TURNS)?
- [ ] Check: does increasing batch_size clamp to 5 cause any issues in the batch builder's turn budget logic?
- [ ] Check: is the `feature_count` placeholder still handled correctly in the spec → prompt flow?
- [ ] Check: does the context doc's guidance match the initializer prompt's rules? No contradictions?
- [ ] Run existing tests: `python -m pytest test_client.py`, `python -m pytest test_dependency_resolver.py`
- [ ] Run security tests: `python test_security.py`, `python test_security_integration.py`
- [ ] Run linting: `ruff check .`

---

## Edge Cases to Think About

1. **A feature with 1 step but that step is extremely complex** — The text-length heuristic should catch this, but verify.

2. **A project where ALL features are compact (3-4 steps)** — With batch_size=5, the builder should pack 3-4 per session. Does this work correctly?

3. **A project with a very linear dependency chain** — Even with wide graph instructions, some domains are inherently linear (auth → profile → settings). Does the batch builder handle chains well?

4. **The Initializer creating exactly 80 features** — Is 80 enough to cover all 20 test categories? The minimum distribution per category would need to average 4 features per category. Some categories (like Infrastructure at exactly 5) are fixed, leaving 75 for 19 categories ≈ 4 each. That's tight but workable for a medium app.

5. **Backward compatibility** — Existing projects with 200+ features should still work. The batch builder doesn't care how many features there are, just how big each one is. So this change is backward-compatible.

6. **The `--batch-features` CLI flag** — This lets users specify exact feature IDs for a batch. Does the turn budget still apply? Check `parallel_orchestrator.py` for how `batch_features` mode interacts with the budget.

---

## The Big Picture

The original system was designed by someone who didn't enforce context budget limits — he relied on feature granularity to implicitly keep sessions manageable. The current owner added explicit budget enforcement (45% cap) which is the RIGHT call, but the feature sizing was never updated to match.

This handoff aligns them: features are sized TO the budget, not hoping to fit within it. The result is:
- Same quality guarantees (45% cap preserved)
- Same testability (each feature independently verifiable)
- Same parallelism (wide dependency graphs)
- Fewer sessions (40-80 features instead of 165-405)
- Less overhead (each session does more productive work)
- Better budget utilization (features fill 50-80% of budget instead of 15-25%)

This is the final piece that makes the two systems work as one.
