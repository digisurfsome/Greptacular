# PRP Plan - PRD-to-Implementation Planning Framework

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/prp-plan.md

## Overview

A comprehensive PRP Plan (PRD-to-Implementation) workflow for creating detailed feature implementation plans through systematic codebase analysis.

## Core Phases (0-6)

### Phase 0 - DETECT

Determines input type and routes accordingly:

| Input Pattern | Action |
|---|---|
| `.prd.md` file path | Parse PRD, locate pending phases |
| `.md` with "Implementation Phases" | Extract phases, find next eligible |
| Any other file | Read for context |
| Free-form text | Proceed to Phase 1 |
| Empty input | Request feature description |

**PRD Parsing**: Read file -> find pending phases -> check dependencies -> extract phase details.

### Phase 1 - PARSE

Extracts and clarifies requirements:

- **What**: Concrete deliverable
- **Why**: User value proposition
- **Who**: Target user/system
- **Where**: Codebase location

Includes user story format and complexity assessment (Small/Medium/Large/XL).

**Ambiguity Gate**: Stops if core deliverable, success criteria, or technical approach remains unclear.

### Phase 2 - EXPLORE

Conducts deep codebase intelligence gathering across eight categories:

1. Similar Implementations
2. Naming Conventions
3. Error Handling
4. Logging Patterns
5. Type Definitions
6. Test Patterns
7. Configuration
8. Dependencies

Also traces five key elements:
- Entry Points
- Data Flow
- State Changes
- Contracts
- Patterns

Results compile into "Unified Discovery Table" with columns: Category | File:Lines | Pattern | Key Snippet.

### Phase 3 - RESEARCH

Addresses external libraries, APIs, or unfamiliar technology via web documentation, usage examples, and best practices.

Format: KEY_INSIGHT, APPLIES_TO, GOTCHA.

Skip if using only established internal patterns.

### Phase 4 - DESIGN

Documents UX transformation with before/after diagrams (or "N/A - internal change").

Includes interaction changes table mapping touchpoints across states.

### Phase 5 - ARCHITECT

Defines strategic design approach, alternatives considered, explicit scope boundaries, and "NOT Building" list (prevents scope creep).

### Phase 6 - GENERATE

Produces final plan document saved to `.claude/PRPs/plans/{kebab-case-feature-name}.plan.md`.

## Plan Template Structure

**Required Sections:**

- **Summary**: 2-3 sentence overview
- **User Story**: Standard format (As a [user], I want [capability], so that [benefit])
- **Problem -> Solution**: Current state to desired state
- **Metadata**: Complexity, source PRD, phase name, estimated files
- **UX Design**: Before/After ASCII diagrams, interaction changes table
- **Mandatory Reading**: Priority-ordered critical files with line ranges
- **External Documentation**: External resources table
- **Patterns to Mirror**: Code snippets with SOURCE references showing:
  - NAMING_CONVENTION
  - ERROR_HANDLING
  - LOGGING_PATTERN
  - REPOSITORY_PATTERN
  - SERVICE_PATTERN
  - TEST_STRUCTURE
- **Files to Change**: Action table (CREATE/UPDATE) with justifications
- **NOT Building**: Explicit out-of-scope items
- **Step-by-Step Tasks**: Each with ACTION, IMPLEMENT, MIRROR, IMPORTS, GOTCHA, VALIDATE
- **Testing Strategy**: Unit tests table and edge cases checklist
- **Validation Commands**: Type checking, unit tests, full suite, database (if applicable), browser (if applicable), manual steps
- **Acceptance Criteria**: Completion checklist
- **Risks**: Likelihood/Impact/Mitigation table
- **Notes**: Additional context

## Critical Rules

**Golden Rule**: "A great plan contains everything needed to implement without asking further questions."

**No Prior Knowledge Test**: "A developer unfamiliar with this codebase should be able to implement the feature using ONLY this plan, without searching the codebase or asking questions."

**Pattern Authenticity**: Code snippets must be actual codebase examples with real file paths and line numbers -- never invented patterns.

**Ambiguity Gate**: "If any of these are unclear, STOP and ask the user before proceeding: core deliverable vague, success criteria undefined, multiple interpretations, major technical unknowns."

## Output Deliverables

Plan saved to `.claude/PRPs/plans/{kebab-case-feature-name}.plan.md` with completion report including:
- File path
- Source PRD
- Phase
- Complexity
- Scope
- Key patterns
- External research status
- Risks
- Confidence score (1-10)

## Verification Checklist

Five validation domains:
1. Context Completeness
2. Implementation Readiness
3. Pattern Faithfulness
4. Validation Coverage
5. UX Clarity
