# Contract Template

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/contract-template.md

## Purpose

Standardized framework for generating project contracts (contract.md) when confidence reaches >= 95%.

## Structure

### Header Fields

- Project Name
- Creation date
- Confidence score
- Status (Draft/Approved)
- Supersedes reference (for revisions)

### Problem Statement

1-3 paragraphs identifying:
- The pain point
- Affected parties
- Why it matters
- Consequences of inaction

### Goals

3-5 numbered, measurable objectives answering "what does success look like?"

Use specific, measurable targets: "reduce p95 latency from 2s to 500ms" rather than "improve performance."

### Success Criteria

Testable acceptance checklist items that are verifiable and specific. Should read like test cases with pass/fail verification.

### Scope Boundaries

Three subsections:
- **In Scope**: Included features/capabilities
- **Out of Scope**: Excluded items with rationale
- **Future Considerations**: Deferred items for later phases

When uncertain, default to out-of-scope classification.

### Execution Plan

Added during Phase 5 handoff, enabling cold-start execution:
- **Dependency Graph** (ASCII showing phase blocking relationships)
- **Execution Steps** (ordered commands, marked sequential vs. parallel)
- **Agent Team Prompt** (if 2+ phases parallelizable)

## Versioning

Contract versioning uses `contract-{date}.md` naming convention, creating revision chains through the Supersedes field.
