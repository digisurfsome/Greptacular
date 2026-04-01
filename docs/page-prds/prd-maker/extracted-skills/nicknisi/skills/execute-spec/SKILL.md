# Execute-Spec Skill

> Source: nicknisi/claude-plugins/plugins/ideation/skills/execute-spec/SKILL.md

## Purpose

Transform ideation specs into working implementations through a structured workflow combining codebase exploration, incremental development, and multi-cycle code review.

## Core Workflow Phases

### Pre-Execution

**Specification Loading** (three-tier approach):
1. Direct file reading if path argument provided
2. Auto-detection via TaskList for pending phase tasks
3. Manual search through `./docs/ideation/*/spec-phase-*.md` as fallback

**Scout Codebase Invocation:**
- Activates read-only Scout subagent to map codebase structure
- Produces context map identifying patterns, dependencies, conventions, and risks
- Returns GO verdict (>= 70% confidence) or HOLD (<70%)
- Scout output persisted to `{project-directory}/context-map.md`

HOLD verdicts trigger user escalation with options: "Proceed anyway," "Update spec," or "Abort."

**Specification Structure Parsing** extracts:
- Technical approach documentation
- File changes (new, modified, deleted)
- Per-component implementation details
- Testing and validation requirements
- Feedback strategy with playground type and inner-loop command
- Pattern file references for reviewer phase

**Task Creation and Dependencies:**
- TaskCreate generates component tasks from Implementation Details
- TaskUpdate establishes blocking relationships
- Validation tasks blocked by all component tasks

**Feedback Environment Setup:**
- Test runners (Jest, Vitest, Mocha, pytest, go test)
- Dev servers (Vite, Next.js, Webpack)
- Storybook or custom harnesses
- Verification of inner-loop command operability

### Build Phase

**Per-Component Workflow:**
1. Claim task via TaskUpdate to in_progress
2. Read implementation details and pattern files
3. Create feedback loop artifacts (test files, harnesses)
4. Implement incrementally with check commands between chunks
5. Run component experiments for edge cases
6. Mark completed via TaskUpdate

**Parallel Execution Mode** (with --parallel flag):
- Detects multiple unblocked tasks
- Spawns subagents for independent components
- Prevents parallelization of components modifying identical files
- Runs unified review cycle post-completion on combined diff

### Post-Execution: Verify-Review-Fix Loop

**Verification Phase:**
- Type checking, linting, testing, build commands
- Validation failures trigger fixes before review

**Review Cycle** (maximum 3 iterations):
- Invokes Reviewer subagent with spec path and pattern file list
- PASS = zero critical/high findings
- FAIL = one or more critical/high findings

**Failure Handling:**
- Cycles 1-2: Apply suggested fixes, re-verify, re-review
- Cycle 3: Escalate to user ("Fix manually," "Accept with issues," "Abort")

**Commit Phase** (post-PASS or user acceptance):
- Stages modified files with specific names
- Descriptive messages following project conventions
- Includes cycle count in body if multi-cycle

**Completion Report:**
- Implemented components list
- File modification summary
- Review cycles and findings addressed
- Validation results
- Acceptance criteria checklist
- Next phase instructions

## Invocation Patterns

```bash
/ideation:execute-spec                                    # Auto-detect
/ideation:execute-spec docs/ideation/my-project/spec-phase-1.md  # Specific file
/ideation:execute-spec --parallel                          # Parallel components
```

## Cross-Session Execution

Multi-phase workflow (recommended):
```
/clear
/ideation:execute-spec         # Phase 1
# [commit]
/clear
/ideation:execute-spec         # Phase 2 (auto-detects)
```

## Foundational Principles

- Read before writing
- Establish rapid feedback loops before building
- Adhere strictly to specification guidance
- Match existing architectural patterns
- Maintain human oversight for uncertainty
- Complete phases sequentially
- Defer commits until review approval
- Escalate rather than iterate indefinitely
