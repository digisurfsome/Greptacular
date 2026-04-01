# Agentic Engineering

**Name**: agentic-engineering
**Description**: Framework for AI-driven engineering with human quality oversight.
**Origin**: ECC

## Operating Principles (4 Rules)

1. Define completion criteria before execution
2. Decompose work into agent-sized units
3. Route model tiers by task complexity
4. Measure with evals and regression checks

## Eval-First Loop (4 Phases)

1. Define capability and regression evaluations
2. Run baseline and document failure patterns
3. Execute implementation
4. Re-run evaluations and analyze improvements

## Task Decomposition: 15-Minute Unit Rule

Each unit should have:
- Independent verification capability
- Single dominant risk per unit
- Clear done condition

## Model Routing Guidelines

| Model | Use For |
|-------|---------|
| **Haiku** | Classification, boilerplate transforms, narrow edits |
| **Sonnet** | Implementation and refactors |
| **Opus** | Architecture decisions, root-cause analysis, multi-file invariants |

## Session Strategy (3 Rules)

- Continue for interdependent units
- Start fresh after major phase transitions
- Compact after milestones, not during debugging

## Review Priorities

Focus review on:
- Invariants and edge cases
- Error boundaries
- Security and authentication assumptions
- Hidden coupling and rollout risk

## Cost Discipline Tracking

Monitor per task:
- Model selection
- Token estimates
- Retry count
- Execution time
- Outcome status
