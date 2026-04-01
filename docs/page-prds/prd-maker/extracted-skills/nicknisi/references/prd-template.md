# PRD Template

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/prd-template.md

## Purpose

Standardized format for creating phase-specific product requirement documents (prd-phase-{n}.md).

## Structure

### Header

- Contract reference location
- Phase identification (e.g., "Phase N of total phases")
- Single-line phase focus statement

### Phase Overview

2-3 paragraphs covering:
- What the phase accomplishes
- Sequencing rationale
- User value delivered
- Key dependencies

### User Stories

Numbered stories following: "As a [user type], I want [capability] so that [benefit]"

### Functional Requirements

Organized by feature groups with uniquely-identified requirements (FR-{N}.{sequence number})

### Non-Functional Requirements

Four standard categories:
- Performance
- Security
- Accessibility
- Scalability

### Dependencies

Two subsections:
- Prerequisites needed before phase start
- Outputs required by subsequent phases

### Acceptance Criteria

Checkbox-formatted, verifiable completion indicators including testing requirements.

### Open Questions

Optional section for unresolved items requiring decisions.

## Key Guidance

- User-centric story writing rather than technical implementation details
- Explicit traceability through unique requirement identifiers
- Clear QA-testable acceptance criteria
- Transparent dependency mapping
- Surface uncertainties proactively
