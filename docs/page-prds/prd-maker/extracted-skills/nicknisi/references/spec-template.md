# Spec Template

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/spec-template.md

## Purpose

Template for generating implementation specifications (spec-phase-{n}.md) for approved project phases.

## Structure

### Header

- Project name
- Phase number
- Contract reference
- PRD link
- Effort estimate (S/M/L/XL sizing)

### Technical Approach

2-3 paragraphs covering:
- Overall architecture approach
- Key technical decisions and rationale
- Patterns or frameworks to use
- Any spikes or research needed

### Feedback Strategy

- Inner-loop command
- Playground environment
- Reasoning for chosen validation mechanism

### File Changes

Three tables:
- New files (with purposes)
- Modified files (with justifications)
- Deletions (with reasons)

### Implementation Details

Component-by-component breakdowns:
- Pattern references ("Pattern to follow: path/file.ts")
- Key code interfaces
- Design decisions
- Implementation steps
- Feedback loops (playground, experiments, check commands)

### Data Model

Database schema changes, indexes, state shape definitions (when applicable).

### API Design

New endpoints table and request/response examples.

### Testing Requirements

- Unit tests with key test cases
- Integration tests
- Manual testing checklist
- Edge cases

### Error Handling

Scenario-based table mapping failure conditions to strategies.

### Failure Modes

Non-trivial component analysis:
- Named failures (not generic "error")
- Triggers
- Impact
- Mitigation approaches

### Validation Commands

Copy-paste-ready commands for type checking, linting, testing, and builds.

### Rollout Considerations

Feature flags, monitoring, alerting, rollback plans.

### Open Items

Checklist for remaining decisions during implementation.

## Key Guidance

- Exhaustive file listings
- Referenced existing patterns
- Actual code snippets for complex areas
- Schema plus indexes approach
- Explicit error strategies
- Fast feedback loops
- Skip trivial components from feedback loops and failure analysis
