# Architecture Decision Records

**Name**: architecture-decision-records
**Origin**: ECC
**Purpose**: Capture architectural decisions during Claude Code sessions as structured ADRs.

## Core Description

Capture architectural decisions as they happen during coding sessions. Instead of decisions living only in Slack threads, PR comments, or someone's memory, this skill produces structured ADR documents that live alongside the code.

## Activation Triggers

- Explicitly requesting decision recording ("let's record this decision")
- Choosing between significant alternatives (framework, library, pattern, database, API design)
- Using decision language ("we decided to...")
- Asking about past decisions ("why did we choose X?")
- Planning phases discussing architectural trade-offs

## ADR Document Structure

Standard format adapted from Michael Nygard's proposal:

```markdown
# ADR-NNNN: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: proposed | accepted | deprecated | superseded by ADR-NNNN
**Deciders**: [who was involved]

## Context
[2-5 sentences describing situation, constraints, forces]

## Decision
[1-3 sentences stating decision clearly]

## Alternatives Considered

### Alternative 1: [Name]
- **Pros**: [benefits]
- **Cons**: [drawbacks]
- **Why not**: [rejection reason]

### Alternative 2: [Name]
- **Pros**: [benefits]
- **Cons**: [drawbacks]
- **Why not**: [rejection reason]

## Consequences

### Positive
- [benefit 1]
- [benefit 2]

### Negative
- [trade-off 1]
- [trade-off 2]

### Risks
- [risk and mitigation]
```

## Workflow: Capturing New ADRs

1. **Initialize** (first time): Create `docs/adr/` directory with user confirmation. Seed with `README.md` containing index table header and blank `template.md`
2. **Identify decision**: Extract core architectural choice
3. **Gather context**: Document problem prompting decision and constraints
4. **Document alternatives**: Record rejected options and rationales
5. **State consequences**: Identify trade-offs and impact
6. **Assign number**: Scan existing ADRs and increment sequentially
7. **Confirm and write**: Present draft for review before writing. Only proceed with explicit approval
8. **Update index**: Append entry to `docs/adr/README.md`

## Workflow: Reading Existing ADRs

1. Check for `docs/adr/` existence
2. If missing, respond: "No ADRs found in this project. Would you like to start recording architectural decisions?"
3. Scan `docs/adr/README.md` index for relevant entries
4. Read matching files and present Context and Decision sections
5. If no match found, offer to record a new ADR

## Directory Structure

```
docs/
└── adr/
    ├── README.md              <- index of all ADRs
    ├── 0001-use-nextjs.md
    ├── 0002-postgres-over-mongo.md
    ├── 0003-rest-over-graphql.md
    └── template.md            <- blank template for manual use
```

## ADR Index Format

```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-use-nextjs.md) | Use Next.js as frontend framework | accepted | 2026-01-15 |
| [0002](0002-postgres-over-mongo.md) | PostgreSQL over MongoDB for primary datastore | accepted | 2026-01-20 |
| [0003](0003-rest-over-graphql.md) | REST API over GraphQL | accepted | 2026-02-01 |
```

## Decision Detection Signals

**Explicit signals:**
- "Let's go with X"
- "We should use X instead of Y"
- "The trade-off is worth it because..."
- "Record this as an ADR"

**Implicit signals** (suggest recording without auto-creation):
- Framework or library comparisons reaching conclusions
- Database schema design choices with rationale
- Architectural pattern choices (monolith vs microservices, REST vs GraphQL)
- Authentication/authorization strategy decisions
- Infrastructure selection after evaluation

## Best Practices

**Recommended:**
- Specify decisions precisely ("Use Prisma ORM" rather than generic terms)
- Emphasize rationale over mechanics
- Include rejected alternatives and reasoning
- Honestly state trade-offs
- Maintain brevity (readable in ~2 minutes)
- Use present tense descriptions

**Avoid:**
- Recording trivial choices (variable naming, formatting)
- Excessive length (context exceeding ~10 lines indicates scope creep)
- Omitting alternatives as explanation
- Leaving outdated ADRs uncurated
- Recording without dating past decisions

## ADR Lifecycle States

```
proposed -> accepted -> [deprecated | superseded by ADR-NNNN]
```

- **proposed**: Under discussion, uncommitted
- **accepted**: In effect and active
- **deprecated**: No longer relevant
- **superseded**: Replaced by newer ADR (with link reference)

## Decision Categories

| Category | Examples |
|----------|---------|
| Technology choices | Framework, language, database, cloud provider |
| Architecture patterns | Monolith vs microservices, event-driven, CQRS |
| API design | REST vs GraphQL, versioning strategy, auth mechanism |
| Data modeling | Schema design, normalization decisions, caching strategy |
| Infrastructure | Deployment model, CI/CD pipeline, monitoring stack |
| Security | Auth strategy, encryption approach, secret management |
| Testing | Test framework, coverage targets, E2E vs integration balance |
| Process | Branching strategy, review process, release cadence |

## Integration Points

- **Planner agent**: Suggest ADR creation when architecture changes proposed
- **Code reviewer agent**: Flag PRs introducing architectural changes without corresponding ADRs
