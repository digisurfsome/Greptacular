# Autonomous Loops

**Name**: autonomous-loops
**Description**: Patterns for running Claude Code autonomously in loops, from simple sequential pipelines to sophisticated RFC-driven multi-agent systems.
**Origin**: ECC

## Loop Pattern Spectrum

### 1. Sequential Pipeline (`claude -p`)

**Complexity:** Low | **Use for:** Daily dev steps, scripted workflows

Core principle: "If you can't figure out a loop like this, it means you can't even drive the LLM to fix your code in interactive mode."

**Key design principles:**
- Each step isolated with fresh context window
- Order matters — sequential execution
- Avoid negative instructions (use separate cleanup instead)
- Exit codes propagate with `set -e`

**Example structure:**
```bash
claude -p "Implement feature from spec"
claude -p "Review changes, remove unnecessary tests"
claude -p "Run full build, lint, type check, tests"
claude -p "Create conventional commit"
```

**Variations:** Model routing (different models per step), environment context via files, tool restrictions with `--allowedTools`.

### 2. NanoClaw REPL

**Complexity:** Low | **Use for:** Interactive persistent sessions

Session-aware REPL calling `claude -p` synchronously with full conversation history. Loads/saves conversation history from `~/.claude/claw/{session}.md`.

### 3. Infinite Agentic Loop

**Complexity:** Medium | **Use for:** Parallel content generation, spec-driven work

Two-prompt orchestrator system:
- **Prompt 1:** Orchestrator parses spec, scans output directory, plans iteration, assigns creative directions
- **Prompt 2:** Sub-agents receive full context, unique creative direction, iteration number

**Deployment:** Orchestrator launches N sub-agents in parallel waves (3-5 agents per wave for infinite mode).

### 4. Continuous Claude PR Loop

**Complexity:** Medium | **Use for:** Multi-day iterative projects with CI gates

Core loop: Create branch -> Run implementation -> Optional reviewer pass -> Commit -> Push PR -> Wait for CI -> Auto-fix failures -> Merge -> Repeat.

**Critical innovation:** `SHARED_TASK_NOTES.md` persists across iterations, bridging context gaps between independent invocations.

**Key configuration flags:**
- `--max-runs N`: Stop after N iterations
- `--max-cost $X`: Stop after spending X dollars
- `--max-duration 2h`: Stop after time elapsed
- `--merge-strategy`: squash/merge/rebase options
- `--worktree <name>`: Parallel execution via git worktrees
- `--ci-retry-max N`: Auto-fix CI failures
- `--completion-signal`: Magic phrase to signal completion

### 5. De-Sloppify Pattern

**Type:** Add-on pattern | **Use for:** Quality cleanup after implementer steps

Rather than constraining implementation with negative instructions, use a separate focused cleanup pass that removes:
- Tests verifying language/framework behavior
- Redundant type checks
- Over-defensive error handling
- Console.log statements
- Commented-out code

**Principle:** "Rather than adding negative instructions which have downstream quality effects, add a separate de-sloppify pass. Two focused agents outperform one constrained agent."

### 6. Ralphinho / RFC-Driven DAG Orchestration

**Complexity:** High | **Use for:** Large features, multi-unit parallel work with merge queue

Architecture includes:
- **RFC Decomposition:** AI breaks RFC into work units with dependency DAG
- **Quality Pipelines:** Tiered depth based on complexity (trivial/small/medium/large)
- **Separate context windows:** Each stage runs in isolated agent process
- **Merge queue:** Rebase onto main, run tests, land or evict with conflict context

**Worktree isolation:** Each unit runs in isolated worktree; stages for same unit share worktree preserving state.

**Complexity tiers:**
- Trivial: implement -> test
- Small: implement -> test -> code-review
- Medium: research -> plan -> implement -> test -> reviews -> review-fix
- Large: all above + final-review

**Eviction recovery:** When units conflict, full context captured and fed back to implementer on next pass.

## Decision Framework

- Single focused change -> Sequential Pipeline or NanoClaw
- Multiple interdependent units with spec -> Ralphinho
- Many variations of same thing -> Infinite Agentic Loop
- Multi-day iterative project -> Continuous Claude

## Anti-Patterns to Avoid

1. Infinite loops without exit conditions
2. No context bridge between iterations
3. Retrying same failure without capturing error context
4. Using negative instructions instead of cleanup passes
5. All agents in one context window
6. Ignoring file overlap in parallel work

## Key Principle

"Each stage in separate context window with separate agent. The reviewer should never be the author."
