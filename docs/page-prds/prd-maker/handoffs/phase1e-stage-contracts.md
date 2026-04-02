# Phase 1E: Stage Contracts (Completion Criteria)

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Estimated effort:** Single session, judgment required
> **Output:** `docs/page-prds/prd-maker/stage-contracts.md`

---

## Your Mission

You are writing the completion contracts for every stage (0 through 10) of the PRD Maker pipeline. A "contract" defines exactly what "done" means for each stage -- what artifacts must exist, what quality bar must be met, and what happens if the bar is not met. Without contracts, there is no way to know if a stage succeeded or failed. The pipeline just passes garbage forward and hopes for the best.

Every stage in the pipeline will check its own output against its contract before passing data to the next stage. If the contract is not met, the stage either retries, asks a human for help, or triggers the escape hatch. Contracts are the quality gates that prevent bad data from cascading downstream.

---

## Files to Read (In This Order)

Read ALL of these files completely:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-01-extraction.md`** through **`stage-10-extraction.md`** -- All 10 stage extraction dossiers. Each describes what the stage does, what it inputs, what it outputs, and its core logic. You need to understand every stage deeply to write its contract.

   Full paths:
   - `docs/page-prds/prd-maker/stage-extractions/stage-01-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-02-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-03-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-04-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-05-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-06-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-07-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-08-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-09-extraction.md`
   - `docs/page-prds/prd-maker/stage-extractions/stage-10-extraction.md`

2. **`docs/page-prds/prd-maker/extracted-skills/nicknisi/references/confidence-rubric.md`** -- The confidence scoring pattern. Uses 5 dimensions scored 0-20 each, totaling /100. Study this pattern -- you will adapt it for stage contracts.

3. **`docs/page-prds/prd-maker/extracted-skills/nicknisi/references/contract-template.md`** -- The contract template format. Has sections for Problem Statement, Goals, Success Criteria, Scope Boundaries. Study this for the overall project contract.

4. **`docs/page-prds/prd-maker/build-game-plan.md`** -- Read the sections on "Confidence Gate" (every stage, threshold 90), "Escape Hatch Protocol," and "1F. Write Stage Contracts."

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- Read for the 4 agent-readiness criteria (Prompt 3) which inform what "done" means for each stage's skill.

---

## What You Are Producing

A single file: **`docs/page-prds/prd-maker/stage-contracts.md`**

This file contains:
1. An overall project contract (the PRD Maker pipeline as a whole)
2. Individual contracts for each of the 11 stages (Stage 0 through Stage 10)

---

## Overall Project Contract

At the top of the file, write an overall project contract using the nicknisi contract template format:

### Problem Statement
The PRD Maker pipeline takes a non-coder's messy app description and produces a complete, buildable technical specification. Without this pipeline, non-coders either (a) try to explain their idea to a developer and lose critical details, (b) use an AI chatbot that produces vague, unbuildable specs, or (c) give up. The pipeline must produce specs that are detailed enough for a coding agent to build from with zero human interpretation.

### Goals
Define 3-5 measurable goals for the overall pipeline. These should be about the QUALITY of the final output, not the process of building the pipeline. Examples:
- Every generated spec must pass a buildability check (a coding agent can start building from it without asking clarifying questions)
- The pipeline must handle input from users who provide as little as 2-3 sentences or as much as 50+ sentences
- The final spec must cover all 30 categories from the master checklist (no gaps)

### Success Criteria
Checkboxes that can be verified after the pipeline runs.

### Scope Boundaries
In Scope / Out of Scope / Future Considerations.

---

## Per-Stage Contracts

For EACH stage (0 through 10), write a contract with these sections:

### Stage N: [Name]

#### Purpose
One sentence: what this stage does and why it matters.

#### Inputs
What this stage receives. Be specific about field names from the context packet.

#### Outputs
What this stage must produce. Be specific about field names.

#### "Done When..." Criteria

A numbered list of specific, measurable conditions that must ALL be true for the stage to be considered complete. These must be checkable by code or by another agent -- no subjective criteria.

**Good criteria:**
- "Every mechanism category (A-N) has a classification (REQUIRED/OPTIONAL/UNLIKELY) in the context packet"
- "The raw input field contains at least 50 words"
- "All 7 questions have been answered for every extracted mechanism"
- "Each phase has a token estimate and the total does not exceed 500,000"

**Bad criteria:**
- "The output is good" -- What does "good" mean?
- "The user is satisfied" -- Not measurable by an agent
- "The spec feels complete" -- Subjective

Aim for 4-8 criteria per stage. Not too few (gaps in verification) or too many (bureaucratic overhead).

#### Confidence Scoring

Define 5 scoring dimensions specific to this stage, each scored 0-20 (total /100):

1. **Completeness** (0-20): Are all required fields populated? Specific to what THIS stage produces.
2. **Accuracy** (0-20): Is the data correct and consistent with inputs? Specific to what THIS stage transforms.
3. **Consistency** (0-20): Does the output align with previous stages' data? No contradictions.
4. **Specificity** (0-20): Are the outputs precise enough for the next stage to parse without ambiguity?
5. **Handoff Readiness** (0-20): Could the next stage start immediately from this output without needing clarification?

For each dimension, provide a brief rubric showing what 0-5, 6-10, 11-15, and 16-20 look like FOR THIS SPECIFIC STAGE. Do not use generic descriptions -- tailor each rubric to the stage's actual outputs.

#### Threshold and Failure Handling

- **Score >= 90:** Pass to next stage automatically.
- **Score 70-89:** Flag concerns. Present the low-scoring dimensions to the human with the question: "These areas scored below 18. Should I proceed or revise?" If no human available, retry the stage once. If retry still scores 70-89, proceed with a warning flag in the context packet.
- **Score < 70:** Do NOT proceed. Trigger the escape hatch. Save the context packet, log what went wrong, and signal NEEDS_HUMAN.

#### What the Next Stage Expects

One paragraph describing what the NEXT stage will do with this stage's output. This helps the contract writer understand why certain fields matter. For Stage 10, describe what the final consumer (a coding agent or human developer) expects.

---

## Stage-Specific Guidance

Here is additional context for writing each stage's contract. Use this alongside the stage extractions:

### Stage 0: Technical Foundation
- Must establish platform context BEFORE any idea-specific work
- Key output: platform profile (framework, database, auth, hosting)
- Failure mode: user picks a stack the pipeline doesn't have a boilerplate for

### Stage 1: Idea Capture
- Must preserve EVERYTHING, including contradictions
- Key output: raw text, word count, input format
- Failure mode: user provides too little input (under 20 words)
- The contract should define a MINIMUM viable input size

### Stage 2: Gap Analysis
- Must match archetype(s), identify gaps, ask targeted questions
- Key output: complete mechanism map (A-N with classifications)
- Failure mode: user refuses to answer questions, gives contradictory answers
- The contract should define what "complete enough" means

### Stage 3: Agent OS Structuring
- Must transform messy input into organized concept document
- Key output: 4 sections (Concept, Target User, Feasibility, Problem Statement)
- Failure mode: ambiguity that cannot be resolved without the user
- The contract should require that ALL ambiguities are explicitly resolved or flagged

### Stage 4: Mechanism Extraction
- Must break the app into discrete mechanisms tagged OBVIOUS or NEEDS_EVALUATION
- Key output: mechanism list with tags and dependency graph
- Failure mode: mechanism is too vague to classify
- The contract should define what "one mechanism" is (granularity)

### Stage 5: 7-Question Scaffolding
- THE ENGINE -- must classify every step as WALL/DOOR/ROOM
- Key output: 7-question answers for every mechanism, W/D/R classification
- Failure mode: a mechanism has steps that resist classification
- The contract should require that EVERY step has a classification (no "TBD")

### Stage 6: Layout + Mockups + Style
- Must produce per-page layout specifications and a design system
- Key output: page list with components, wireframe pattern, style tokens
- Failure mode: the mechanism→page mapping has gaps (mechanisms not represented in any page)
- The contract should verify every mechanism appears on at least one page

### Stage 7: Phase Sequencing
- Must split the spec into buildable phases that fit token budgets
- Key output: phase list with token estimates, file sandbox, build order
- Failure mode: a phase exceeds token budget, circular dependencies in build order
- The contract should verify token math (no phase exceeds 325,000 usable tokens)

### Stage 8: Protocol Injection
- Must configure the verification system (pulse/seam/full checks)
- Key output: check configurations, violation thresholds, escalation rules
- Failure mode: checks are too strict (everything fails) or too loose (nothing caught)
- The contract should verify that every phase has at least one check configured

### Stage 9: Verification Agent Setup
- Must configure the separate checker agent
- Key output: checker config, git diff rules, two-strike rule
- Failure mode: checker and builder have conflicting rules
- The contract should verify checker rules do not contradict builder rules from Stage 8

### Stage 10: Output Generator
- Must produce copy-paste-ready build files
- Key output: phase files, build script, CLAUDE.md, BUILD_RULES.md
- Failure mode: generated files reference things not defined in the spec
- The contract should verify internal consistency (every reference resolves)

---

## Output File Structure

Create: **`docs/page-prds/prd-maker/stage-contracts.md`**

```markdown
# PRD Maker Pipeline — Stage Contracts

> Completion criteria for every stage in the 10-stage pipeline.
> Each contract defines what "done" means, how to score confidence,
> and what happens when the threshold is not met.
>
> Scoring: 5 dimensions x 20 points = /100 per stage. Threshold: 90 to proceed.

---

## Overall Project Contract

### Problem Statement
[...]

### Goals
[...]

### Success Criteria
[...]

### Scope Boundaries
[...]

---

## Stage 0: Technical Foundation

### Purpose
[...]

### Inputs
[...]

### Outputs
[...]

### "Done When..." Criteria
1. [...]
2. [...]
...

### Confidence Scoring

| Dimension | 0-5 | 6-10 | 11-15 | 16-20 |
|-----------|-----|------|-------|-------|
| Completeness | [...] | [...] | [...] | [...] |
| Accuracy | [...] | [...] | [...] | [...] |
| Consistency | [...] | [...] | [...] | [...] |
| Specificity | [...] | [...] | [...] | [...] |
| Handoff Readiness | [...] | [...] | [...] | [...] |

### Threshold and Failure Handling
[...]

### What the Next Stage Expects
[...]

---

## Stage 1: Idea Capture

[same structure]

---

[... repeat for all stages through Stage 10 ...]
```

---

## Quality Checks Before You Finish

1. **Every stage covered:** Count your stage sections. Must be 11 (Stage 0 through Stage 10).
2. **"Done When" criteria are measurable:** For each criterion, ask: "Could a script or another AI agent verify this?" If the answer is no, rewrite it.
3. **Confidence rubrics are stage-specific:** Read each rubric. If you could swap two stages' rubrics and they would still make sense, they are too generic. Rewrite with stage-specific details.
4. **Input/output alignment:** For consecutive stages, verify that Stage N's OUTPUTS match Stage N+1's INPUTS. If Stage 3 outputs "concept_document" but Stage 4 expects "structured_concept," there is a mismatch.
5. **Threshold math works:** With 5 dimensions at 0-20 each, verify the total is /100 and the threshold of 90 means scoring at least 18/20 on average across all dimensions.
6. **Overall contract is complete:** Verify it has all 4 sections (Problem Statement, Goals, Success Criteria, Scope Boundaries).

---

## Success Criteria

- [ ] Output file exists at `docs/page-prds/prd-maker/stage-contracts.md`
- [ ] Overall project contract present with Problem Statement, Goals, Success Criteria, Scope Boundaries
- [ ] All 11 stages (0-10) have individual contracts
- [ ] Each stage contract has: Purpose, Inputs, Outputs, "Done When" criteria, Confidence Scoring, Threshold/Failure Handling, Next Stage Expectations
- [ ] Each stage has 4-8 measurable "Done When" criteria
- [ ] Each stage has 5 confidence dimensions with stage-specific rubrics
- [ ] All rubrics have 4 score bands (0-5, 6-10, 11-15, 16-20) with specific descriptions
- [ ] Threshold is consistently 90 across all stages
- [ ] Failure handling is defined for all three tiers (>=90, 70-89, <70)
- [ ] Input/output alignment verified between consecutive stages
- [ ] No subjective or unmeasurable criteria (no "feels good," "seems right," "user is happy")
