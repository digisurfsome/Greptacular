# Workflow Example

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/references/workflow-example.md

## Overview

Demonstrates the structured process for converting unstructured user input into actionable development specifications.

## Key Stages

### Intake and Exploration

Accept user ideas without judgment, then explore existing codebase patterns and architecture.

### Critical Analysis (Anti-Sycophancy)

Actively question assumptions. For example, push back on "tags might be better because folders are too rigid" -- ask whether users complained or if this is speculation.

### Iterative Clarification

Round-trip questioning ("What type of items are users bookmarking?") continues until confidence reaches approximately 96%, then proceed to contract generation.

### Phasing Strategy

Complex features broken into phases. Example:
- Phase 1: Core bookmarking with tags
- Phase 2: Search/filtering
- Phase 3: Offline support
- Phase 4: Sharing

### Specification and Feedback

Generated specs include explicit feedback strategies and confidence assessments (Strong/Adequate/Weak).

### Execution Model

Dependencies analyzed to determine if parallel agent teams can work simultaneously on independent phases.

### Implementation Approach

Fresh sessions per phase. Establish feedback environments first, then build incrementally with continuous checking and iteration.

## Core Principle

Prioritize clarity over speed -- question vague justifications like "people might be on planes" to separate actual user needs from hypothetical assumptions.
