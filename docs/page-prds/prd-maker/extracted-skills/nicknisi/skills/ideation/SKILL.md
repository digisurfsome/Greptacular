# Ideation Skill

> Source: nicknisi/claude-plugins/plugins/ideation/skills/ideation/SKILL.md

## Purpose

Transform unstructured brain dumps into actionable implementation artifacts through a confidence-gated workflow that produces contracts and specs.

## Critical Tool Requirement

Always use `AskUserQuestion` tool when asking clarifications, not plain text. This ensures structured user responses at decision points.

## Five-Phase Pipeline

### Phase 1: Intake

Accept messy input as-is -- voice transcripts, scattered bullets, contradictions, vague descriptions. Begin analysis immediately without requiring organization.

**Anti-Sycophancy Rules:**
- Avoid phrases like "interesting approach" or "you might consider"
- Take definitive positions on strengths and weaknesses
- Challenge vague demands with specifics ("What evidence supports this?")
- Name undefined terms ("What does 'better' mean?")
- Flag hypothetical users lacking concrete evidence
- Score conservatively when pushback reveals gaps

### Phase 2: Codebase Exploration

Before scoring confidence, understand existing systems unless building greenfield. Map:
- Project structure and frameworks
- Relevant existing code and modules
- Implementation conventions and patterns
- Testing infrastructure
- Build and CI/CD configuration
- Feedback infrastructure (test runners, dev servers, Storybook, API scripts)

Match spec feedback mechanisms to infrastructure. If Storybook exists, prefer it as UI playground; if watch-mode test runner exists, use it for inner-loop commands.

Do not write exploration findings to files -- retain as context only.

### Phase 3: Contract Formation

**3.1 Extract Signals:**
- Problem signals (pain point, need)
- Goal signals (desired outcome)
- Success signals (validation approach)
- Scope signals (in/out boundaries)
- Contradictions requiring resolution
- Codebase constraints

**3.2 Confidence Scoring (5 dimensions, 0-20 each):**

| Dimension | Criterion |
|-----------|-----------|
| Problem Clarity | Understanding problem and its importance |
| Goal Definition | Specific, measurable objectives |
| Success Criteria | Testable validation steps |
| Scope Boundaries | Clear in/out items |
| Consistency | Contradiction resolution |

Score conservatively. When uncertain between levels, choose lower.

**3.3 Thresholds:**

| Score | Action |
|-------|--------|
| <70 | Ask 5+ questions targeting lowest dimensions |
| 70-84 | Ask 3-5 targeted questions |
| 85-94 | Ask 1-2 specific questions |
| >= 95 | Generate contract |

**3.4 Question Strategy via AskUserQuestion:**
- Target lowest-scoring dimension first
- Offer 2-4 options when choices are clear
- Use multiSelect: true for multiple answers
- Keep headers under 12 characters
- Iterate until >= 95%

**3.5 Contract Generation:**
1. Confirm project name (convert to kebab-case for directory)
2. Create `./docs/ideation/{project-name}/`
3. Check for prior contract -- if exists, rename to `contract-{date}.md` and add Supersedes field
4. Write contract.md using template
5. Request approval via AskUserQuestion
6. Revise if needed -- do not re-score unless fundamental misunderstanding
7. Do not proceed until explicitly approved

### Phase 4: Phasing and Specification

**4.1 Workflow Choice (via AskUserQuestion):**
- "Straight to specs" -- faster, technical projects
- "PRDs then specs" -- larger scope, cross-functional teams

**4.2 Determine Phases:**
- Small projects shortcut: Single phase for 1-3 components touching <10 files
- Multi-phase criteria: Dependencies, risk, value delivery, complexity balance
- Detect repeatable patterns: 3+ phases with same structure = template + delta approach

**4.3 Generate PRDs (if chosen):**
For each phase, create `prd-phase-{n}.md` with overview, user stories, functional requirements, non-functional requirements, dependencies, acceptance criteria. Request approval before proceeding to specs.

**4.4 Generate Implementation Specs:**

For unique phases, full `spec-phase-{n}.md` includes:
- Technical approach
- File changes (new and modified)
- Implementation details with code patterns
- Testing requirements
- Error handling and failure modes
- Validation commands
- Feedback strategy (inner-loop command, playground type)
- Per-component feedback loops

For repeatable phases (3+):
1. Generate one full `spec-template-{pattern-name}.md` with placeholders
2. Generate lightweight `spec-phase-{n}.md` delta files

**4.5 Feedback Quality Self-Review:**
- Strong: All iterative components have loops, inner-loop defined, trivial components skipped
- Adequate: Most components covered but some gaps
- Weak: Missing Feedback Strategy or complex components without loops

If weak, revise before presenting.

**4.6 Present for Approval (via AskUserQuestion):**
Options: "Approved," "Adjust approach," "Missing components," "Revisit phases"

### Phase 5: Execution Handoff

**5.1 Analyze Orchestration:**
- Detect parallelizable phases (2+ blocked only by same predecessor)
- Detect sequential chains
- Strategy: sequential, agent team, or hybrid

**5.2 Write Execution Plan to Contract:**
Append `## Execution Plan` with ASCII dependency graph, ordered execution steps, agent team prompt (if parallelizable).

**5.3 Present Handoff Summary:**
- State artifacts written to `./docs/ideation/{project-name}/`
- Show first execution step
- Reference contract's Execution Plan for agent teams

**5.4 Why Fresh Sessions:**
- Ideation consumes context; execution benefits from clean focus
- Human review between phases catches issues early
- Each phase independently committable

## Output Artifacts

```
./docs/ideation/{project-name}/
├── contract.md
├── prd-phase-1.md (if PRD chosen)
├── spec-phase-1.md (always full)
├── spec-template-{pattern}.md (if repeatable)
└── spec-phase-{n}.md (delta files if repeatable)
```

## Failure Modes Section

Each spec includes a failure modes table:

| Column | Purpose |
|--------|---------|
| Component | Which component |
| Failure Mode | Named failure (not generic "error") |
| Trigger | What causes it |
| Impact | Effect on user/system |
| Mitigation | Handling or acknowledgment |

Trivial components (config, types, constants) skip failure mode enumeration.

## Critical Rules Summary

- Always use AskUserQuestion for decisions
- Explore codebase before confidence scoring (unless greenfield)
- Score conservatively
- Write all artifacts to files
- Reference existing code patterns explicitly
- Use template + delta for repeatable phases
- Keep contracts lean
- Don't force phases on small projects
- Evaluate spec feedback quality before presenting
