# Nate B. Jones — Skill Building Prompt Kit

> **Source:** Nate B. Jones skill-making methodology
> **Purpose:** Reference for building each PRD Maker stage skill
> **Usage:** Prompt 2 (Builder) is the core methodology. Prompt 3 (Agent-Readiness) is the quality gate.

---

## How This Kit Maps to Our Pipeline

| Prompt | Our Usage | When |
|---|---|---|
| Prompt 1 (Backlog Audit) | SKIP — we know our skills (Stages 0-10) | N/A |
| Prompt 2 (Skill Builder) | Core build methodology for every stage skill | Phase 2: Building skills |
| Prompt 3 (Agent-Readiness Audit) | Quality gate after each skill is built | Phase 2: Post-build audit |
| Prompt 4 (Team Deployment) | SaaS rollout planning | Phase 7+ (future) |

---

## Prompt 2: Skill Builder (Output-Extraction Method)

### The Core Insight

> "What people think they do and what they actually do are different. Expertise lives in decisions made so many times they've become automatic and invisible."

Build skills from ACTUAL BEST OUTPUT, not from stated intentions. The AI analyzes examples of great work to reverse-engineer the implicit methodology.

### The Process

**Phase 1: Define scope** — What does the skill do? Who calls it? What does great output look like?

**Phase 2: Extract methodology from examples** — Analyze 3-5+ examples for:
- Structural patterns (sections, order, what's always included)
- Decision patterns (judgment calls, criteria driving them)
- Quality signals (what separates best from adequate)
- Framework patterns (comparison structures, evaluation criteria, analytical sequences)
- Voice and tone patterns

**Phase 3: Interview to refine** — Ask 3-5 targeted follow-up questions about the decisions identified. Surface the WHY behind patterns.

**Phase 4: Build the SKILL.md** — Complete file with:
- YAML frontmatter (name, description on SINGLE LINE — multi-line silently fails)
- Methodology as principles and frameworks, not mechanical steps
- Completely specified output format (exact sections, exact order, exact structure)
- Explicit edge case handling (specific behaviors, not vague guidance)
- At least one concrete example of good output
- Quality criteria

**Phase 5: Validate** — Test with realistic, vague requests. Iterate until output matches quality bar.

### Key Rules

- Description field MUST be a single line in YAML frontmatter (technical requirement)
- Keep skill body under 500 lines
- Move reference material to references/ subfolder if complex
- Never produce vague output format instructions ("produce a summary")
- Never include placeholder text
- If agent will call this skill: JSON or strict Markdown output, explicit error codes, composable structure

---

## Prompt 3: Agent-Readiness Audit — The 4 Criteria

Every skill we build MUST pass these before going into the pipeline:

### Criterion 1: Trigger Description as Routing Table
- Does the description contain specific trigger phrases?
- Specific enough to avoid false matches?
- Broad enough to catch legitimate matches?
- Specifies what the skill PRODUCES, not just what domain it's in?

### Criterion 2: Output Format Completeness
- Is output format completely specified? (Exact sections, exact fields, exact structure)
- Could a downstream agent parse this output programmatically?
- Are field types, lengths, and structures explicit?

### Criterion 3: Explicit Edge Case Handling
- What happens when required data is missing?
- What happens when input is ambiguous?
- What happens when request is partially out of scope?
- Are failure modes machine-readable (error codes, structured responses)?

### Criterion 4: Composability
- Could another skill consume this skill's output cleanly?
- Does output contain ONLY the structured deliverable (no conversational preamble)?
- If chained with other skills, where would handoff break?

### The Test

> "What happens when this skill runs at 2am with no one watching?"

If the answer involves "well, a human would notice and fix it" — the skill isn't agent-ready.

---

## For Our Pipeline Specifically

Each stage skill must:
1. Accept the `context_packet` JSON as input
2. Read only its relevant sections
3. Write its output to its designated section
4. Pass the complete packet forward
5. Handle missing/incomplete upstream data gracefully (escape hatch, not crash)
6. Produce output that the NEXT stage can parse without human interpretation
