# Product Requirements Document Generator

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/prp-prd.md

## Overview

This is an interactive PRD generator that follows a problem-first, hypothesis-driven approach with structured questioning phases.

## Core Philosophy

The tool emphasizes starting with **problems, not solutions**, demanding evidence before building, and thinking in testable hypotheses rather than assumed specifications.

## Complete Process Flow

### Phase 1: INITIATE - Core Problem

- If no input: Ask "What do you want to build?"
- If input provided: Restate understanding and confirm
- **Gate**: Wait for user response

### Phase 2: FOUNDATION - Problem Discovery

Five foundational questions:

1. **Who** has this problem? (Specific roles/personas)
2. **What** problem are they facing? (Observable pain points)
3. **Why** can't they solve it today? (Current alternatives and gaps)
4. **Why now?** (What triggered the need)
5. **How** will you know if solved? (Success definition)

**Gate**: Wait for responses

### Phase 3: GROUNDING - Market & Context Research

- Find similar products/competitors
- Identify common patterns
- Explore codebase if available
- Summarize findings with citations
- **Gate**: Brief pause for user input

### Phase 4: DEEP DIVE - Vision & Users

Five questions:

1. **Vision**: One-sentence ideal end state
2. **Primary User**: Role, context, trigger
3. **Job to Be Done**: Situation/motivation/outcome format
4. **Non-Users**: Explicitly excluded segments
5. **Constraints**: Time, budget, technical, regulatory

**Gate**: Wait for responses

### Phase 5: GROUNDING - Technical Feasibility

- Explore existing infrastructure and patterns
- Analyze constraints and data flow
- Map integration points and dependencies
- Assess complexity against similar features
- Summarize feasibility assessment
- **Gate**: Brief pause for input

### Phase 6: DECISIONS - Scope & Approach

Five clarifying questions:

1. **MVP Definition**: Absolute minimum to test
2. **Must Have vs Nice to Have**: Priority ranking
3. **Key Hypothesis**: Testable belief statement
4. **Out of Scope**: What NOT to build
5. **Open Questions**: Unresolved uncertainties

**Gate**: Wait before generating

### Phase 7: GENERATE - Write PRD

Output path: `.claude/PRPs/prds/{kebab-case-name}.prd.md`

**PRD Template Structure:**

- Problem Statement (2-3 sentences)
- Evidence (quotes, data, or "assumption - needs validation")
- Proposed Solution
- Key Hypothesis
- What We're NOT Building
- Success Metrics (table format)
- Open Questions (checklist)
- Users & Context section
- Solution Detail with MoSCoW prioritization
- MVP Scope definition
- User Flow
- Technical Approach
- Implementation Phases (table with status, parallelism, dependencies)
- Decisions Log
- Research Summary

### Phase 8: OUTPUT - Summary

Reports:

- File location
- One-line problem/solution summary
- Validation status for each section
- Open questions count
- Recommended next step
- Implementation phases overview
- Command to start implementation: `/prp-plan {filename}`

## Key Rules & Anti-Patterns

**What to DO:**

- Start with problems
- Ask clarifying questions
- Acknowledge uncertainty honestly
- Mark missing info as "TBD - needs research"
- Think in hypotheses
- Demand evidence

**What NOT to DO:**

- Fill sections with fluff
- Invent plausible-sounding requirements
- Skip uncertainties
- Assume generic users

## Success Criteria

A complete PRD must have:

- Validated problem (or marked as assumption)
- Concrete primary user (not generic)
- Testable hypothesis with measurable outcomes
- Bounded scope with clear must-haves and out-of-scope items
- Acknowledged uncertainties
- Content a skeptic could understand

## Integration Points

- `/prp-plan`: Creates implementation plans from PRD phases
- `/plan`: Simpler planning without PRD structure
- `/save-session`: Preserves context across sessions
