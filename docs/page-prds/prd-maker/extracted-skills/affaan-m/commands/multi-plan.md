# Multi-Plan - Multi-Model Collaborative Planning Protocol

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/multi-plan.md

## Overview

A comprehensive "Multi-model collaborative planning" framework combining context retrieval with dual-model analysis (Codex + Gemini) to generate implementation strategies. Claude serves as the synthesizer and sole writer.

## Essential Protocols

**Language & Communication**: "Use **English** when interacting with tools/models, communicate with user in their language"

**Parallel Processing Requirement**: All Codex/Gemini calls mandate `run_in_background: true` to prevent thread blocking

**Access Control**: "External models have **zero filesystem write access**, all modifications by Claude"

**Validation Gate**: Plans advance only after current-phase output validation

**Scope Limitation**: The planning command permits reading context and writing to `.claude/plan/*` files exclusively; production code remains untouched

## Multi-Model Call Architecture

The protocol specifies a bash wrapper syntax employing `~/.claude/bin/codeagent-wrapper` with backend selection (codex or gemini). Key elements include:

- **Timeout specification**: 3600000ms for model calls
- **Role file mapping**: Distinct analyzer and architect prompts per model
- **Session persistence**: Each call returns SESSION_ID for subsequent `/ccg:execute` reference
- **Background task polling**: Requires `timeout: 600000` (10-minute maximum)

## Execution Workflow: Three Primary Phases

### Phase 1: Context Retrieval

**Step 1.1 - Prompt Enhancement**: If ace-tool MCP availability exists, invoke `mcp__ace-tool__enhance_prompt` using conversation history and project root path

**Step 1.2 - Context Assembly**: Employ `mcp__ace-tool__search_context` with semantic queries; fallback uses Glob, Grep, Read, or Explore agent tools

**Step 1.3 - Completeness Verification**: "Must obtain **complete definitions and signatures** for relevant classes, functions, variables"

**Step 1.4 - Requirement Clarity**: Generate guiding questions if ambiguities persist

### Phase 2: Multi-Model Analysis

**Step 2.1 - Distributed Analysis**: Parallel Codex (backend/architecture focus) and Gemini (frontend/UX focus) execution

**Step 2.2 - Cross-Validation**: Integrate perspectives identifying consensus and divergence points

**Step 2.3 - Optional Dual Plan Drafts**: Both models generate step-by-step plans with pseudo-code

**Step 2.4 - Claude Synthesis**: Final implementation plan synthesizing both analyses

### Phase 3: Plan Delivery

The protocol mandates:

1. Present complete implementation plan with pseudo-code
2. Save to `.claude/plan/<feature-name>.md`
3. Display the bolded instruction prompt showing the saved file path
4. **Terminate immediately** -- no further tool calls

## Critical Restrictions

The document explicitly prohibits:

- Asking "Y/N" then auto-executing
- Production code modifications
- Automatic `/ccg:execute` invocation
- Model calls without explicit user request for modifications

## Plan Artifact Requirements

Implementation plans must include:

- Task type classification (Frontend/Backend/Fullstack)
- Technical solution synthesis
- Numbered implementation steps with expected deliverables
- Key files table with line references and operations
- Risk/mitigation analysis matrix
- SESSION_ID preservation for execution handoff

## File Management Strategy

- **Initial planning**: `.claude/plan/<feature-name>.md`
- **Iterations**: `.claude/plan/<feature-name>-v2.md`, `-v3.md`, etc.

The protocol emphasizes plan modification responsiveness: adjust content per feedback, update the file, re-present, prompt for approval or execution.

## Execution Boundary

`/ccg:plan` responsibilities conclude at plan presentation. Users manually invoke `/ccg:execute .claude/plan/<feature-name>.md` for implementation phase initiation.
