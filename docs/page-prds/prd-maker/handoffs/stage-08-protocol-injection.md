# Build Stage 8 Skill: Protocol Injection

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-08-protocol-injection/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | Idea Capture | Capture the user's raw brain dump with zero filtering or structure | Raw text, preserved contradictions, word count |
| 2 | Gap Analysis | Match to archetype, identify missing mechanism categories (A-N), ask targeted questions | Complete mechanism map, archetype match, gap answers |
| 3 | Agent OS Structuring | Transform messy raw material into organized concept document | Product identity, problem statement, target users, feasibility |
| 4 | Mechanism Extraction | Break structured app into discrete moving parts tagged OBVIOUS or NEEDS_EVALUATION | Mechanism list with dependencies and evaluation tags |
| 5 | 7-Question Scaffolding | Classify every process step as WALL (deterministic) / DOOR (constrained AI) / ROOM (creative) | Per-mechanism W/D/R classification with verification methods |
| 6 | Layout + Mockups + Style | Define page layouts, wireframe patterns, and design system | Per-page component specs, style tokens, typography |
| 7 | Phase Sequencing | Split the spec into buildable phases within token budgets | Phase list with token estimates, file sandbox, build order |
| 8 | Protocol Injection | Configure verification system (pulse/seam/full checks) | Check configurations, violation thresholds, escalation rules |
| 9 | Verification Agent Setup | Configure separate checker agent with git diff rules | Checker config, two-strike rule, verification mode |
| 10 | Output Generator | Produce copy-paste-ready build files | Phase files, build script, CLAUDE.md, BUILD_RULES.md |

### How Stages Connect

Every stage reads from the context packet (a JSON object) and writes its output back to the packet. The packet is saved as a snapshot after each stage. If a stage fails, the pipeline rolls back to the previous snapshot and retries or asks a human for help.

**You are building Stage 8: Protocol Injection.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Protocol Injection

### Purpose

Takes the phases defined in Stage 7 (with their file sandboxes and build orders) and injects testing/verification checkpoints INTO them. This stage does not bolt checks on as a separate document -- it REWRITES the phases to embed protocols inline. The result: each phase becomes a self-contained, self-verifying build unit where pulse checks live inside the build order, seam checks live at connection points, and a full checkpoint gates the phase boundary.

### Inputs (What This Stage Receives)

From the context packet, this stage reads:

- `stage_7.phases` -- Array of phase objects, each with phase_number, name, mechanism_ids, estimated_tokens, build_order, files_allowed, files_read_only, files_forbidden, depends_on, do_not_change
- `stage_7.token_budget` -- Token budget calculations (total_spec_tokens, budget_per_phase_content, overhead_per_phase, total_budget, phases_needed)
- `stage_5.mechanism_blueprints` -- Complete mechanism definitions with Wall/Door/Room classifications (used to determine what verification is appropriate for each step)
- `stage_4.mechanism_dependencies` -- Dependency graph between mechanisms (used to determine where seam checks go -- at mechanism interface points)

### Outputs (What This Stage Produces)

Written to `context_packet.stage_8`:

- `protocol_injected_phases` (array of objects, one per phase):
  - `phase_number` (integer) -- matches Stage 7's phase_number
  - `pulse_checks` (array of objects) -- per-file lightweight checks:
    - `after_file` (string) -- file path this check runs after
    - `checks` (array of strings) -- what to verify (e.g., "file exists", "exports expected functions", "no syntax errors")
    - `cycle_position` (integer) -- position in the 3-file pulse cycle (1, 2, or 3)
  - `seam_checks` (array of objects) -- checks at mechanism connection points:
    - `after_file` (string) -- file path that triggers this seam check
    - `connection_point` (string) -- what is being connected (e.g., "SignIn.tsx <-> AuthContext")
    - `checks` (array of strings) -- what to verify (e.g., "does A import from B?", "are props passed correctly?", "are the doors connected?")
  - `full_checkpoint` (object) -- end-of-phase gate:
    - `pattern_checks` (array of strings) -- sandbox compliance checks (list files modified, compare against allowed list, flag unauthorized changes, flag incomplete build order)
    - `functional_checks` (array of strings) -- runtime checks (does app compile, do pages render, do routes work)
    - `gate_condition` (string) -- pass/fail criteria that must be met before next phase starts
  - `violation_rules` (object) -- severity-based response rules:
    - `LOW` (object): `triggers` (array of strings), `response` (string)
    - `MEDIUM` (object): `triggers` (array of strings), `response` (string)
    - `HIGH` (object): `triggers` (array of strings), `response` (string)
    - `CRITICAL` (object): `triggers` (array of strings), `response` (string)
  - `overhead_tokens` (integer) -- actual overhead for this phase after protocol injection

- `overhead_breakdown` (object) -- standard overhead template:
  - `build_rules_preamble` (integer) -- ~8,000 tokens
  - `file_sandbox` (integer) -- ~2,000 tokens
  - `build_order_with_pulse` (integer) -- ~3,000 tokens
  - `seam_checks` (integer) -- ~2,000 tokens
  - `full_checkpoint` (integer) -- ~5,000 tokens
  - `pattern_verification` (integer) -- ~3,000 tokens
  - `violation_handling` (integer) -- ~2,000 tokens

### Process

**Step 1: Load Phases from Stage 7**

Read `stage_7.phases`. Each phase already has a build order (file sequence) and file sandbox (allowed/read-only/forbidden). Your job is to inject verification protocols INTO these structures.

**Step 2: Insert Pulse Checks**

For each file in each phase's build order, insert a PULSE check after it:
- Does the file exist?
- Does it export the expected functions/components?
- No syntax errors?

Pulse checks are lightweight -- they run after EVERY file. Every 3 files completes a pulse cycle. The cycle is a natural rhythm that keeps the agent honest without being heavy.

**Step 3: Insert Seam Checks at Connection Points**

Examine `stage_4.mechanism_dependencies` and the phase's mechanism_ids. Where two mechanisms interface (one imports from another, one provides data to another), insert a SEAM check:
- Does component A import from component B correctly?
- Do routes point to actual page components?
- Are the doors between rooms properly connected?
- Do data flows match the expected types?

Seam checks are placed at SPECIFIC points in the build order where two mechanisms or components interface. They are tag-triggered, not periodic like pulse checks.

**Step 4: Define Full Checkpoint at Phase Boundary**

At the end of each phase, insert a FULL checkpoint that acts as a GATE:

*Pattern Verification:*
- List every file created or modified (agent self-reports)
- Run `git diff --name-only $SNAPSHOT` to get ground truth
- Compare against FILES ALLOWED list
- FLAG any file touched that was not in the sandbox
- FLAG any file in BUILD ORDER that was not completed
- FLAG any unexpected imports or dependencies

*Functional Checks:*
- Does the app compile? (npm run build / equivalent)
- Do existing features still work? (npm run test if tests exist)
- Do the new pages/components render without errors?
- Can you navigate to expected routes?

*Gate Condition:*
- ALL pattern checks must pass (no unauthorized file modifications)
- ALL functional checks must pass (app compiles, renders, routes work)
- If gate fails, fix issues before next phase starts

**Step 5: Embed Violation Decision Tree**

For each phase, embed the violation response rules directly into the phase text:

- **LOW** -- Touched shared types/config file, added an import to an existing utility
  - Triggers: Modification to a shared types file, addition of an export to a utility
  - Response: Log it. Note it in the phase report. Proceed.

- **MEDIUM** -- Modified a file from a different phase's domain
  - Triggers: Modification to a file listed in another phase's FILES ALLOWED
  - Response: STOP. Review the change. If additive (added export, added prop) -- log and proceed with caution. If destructive (renamed something, changed logic) -- revert that specific file to baseline and re-run with constraint "do NOT modify [file]." If unclear -- flag for human review.

- **HIGH** -- Deleted files, modified core config, changed auth logic outside auth phase
  - Triggers: File deletion, modification of core config files, changes to auth outside the auth phase
  - Response: REVERT ENTIRE PHASE. Re-run with tighter constraints or break the phase smaller.

- **CRITICAL** -- Modified CLAUDE.md, .env, build config, environment files
  - Triggers: Any change to CLAUDE.md, .env, package.json scripts, build configuration, CI/CD config
  - Response: FULL STOP. REVERT. FLAG. Human must intervene. This is either a prompt injection attempt or a catastrophically confused agent.

**Step 6: Calculate Actual Overhead**

For each phase, calculate the actual token overhead after injection. It should be close to the ~25,000 estimate from Stage 7:
- Build rules preamble: ~8,000 tokens
- File sandbox declaration: ~2,000 tokens
- Build order with pulse points: ~3,000 tokens
- Seam check definitions: ~2,000 tokens
- Full checkpoint: ~5,000 tokens
- Pattern verification prompt: ~3,000 tokens
- Violation handling instructions: ~2,000 tokens

If actual overhead exceeds 30,000 tokens for any phase, trim the verbose descriptions. The violation tree and check definitions should be as concise as possible while remaining unambiguous.

**Step 7: Validate Token Budget Fit**

For each phase: estimated_tokens (from Stage 7) + actual overhead_tokens <= 350,000. If any phase exceeds this, signal back to Stage 7 that the split needs adjustment. In practice, the 25K estimate is conservative enough that this rarely happens.

### Rules and Constraints

1. **Protocols are EMBEDDED inline, not separate documents.** Pulse checks live INSIDE the build order. Seam checks live at connection points WITHIN the phase. The full checkpoint lives at the phase boundary. They are not appendices -- they are part of the build sequence.

2. **Pulse after EVERY file.** Not every 3 files, not at end of phase. After EVERY file. The 3-file cycle is a grouping concept, not a frequency limiter.

3. **Seam checks at CONNECTION POINTS.** Not periodic, not random. Placed where two mechanisms interface. If mechanism A provides data to mechanism B, the seam check goes after the file where B imports from A.

4. **Full checkpoint is a GATE.** The next phase CANNOT start until the full checkpoint passes. This is non-negotiable. A failed gate means fix-before-proceed, not log-and-continue.

5. **Pattern verification uses git diff, not agent self-reporting.** The self-report (Step 1 of the 4-step verification) is a first pass. The git diff (Step 2) is ground truth. If they do not match, THAT ITSELF IS A VIOLATION.

6. **Overhead is predictable (~25K tokens).** Because the protocol templates are standardized. Do not over-engineer individual phase protocols. Use the same structure with project-specific values swapped in.

7. **Stages 7 and 8 are tightly coupled but separate.** Stage 7 is about STRUCTURE (what goes where, in what order). Stage 8 is about ENFORCEMENT (how do we verify it was followed). In the final output (Stage 10), they merge into a single integrated phase spec.

8. **The seven enforcement mechanisms map across stages:**
   - A: Pulse checks (Stage 8)
   - B: Seam checks (Stage 8)
   - C: Full checkpoints (Stage 8)
   - D: File sandboxing (Stage 7)
   - E: Build order within phase (Stage 7)
   - F: Post-build pattern verification (Stage 8)
   - G: Martin's structural rules (Stage 5, as the lens)

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-08-extraction.md`** -- The full extraction dossier for this stage. This is your primary source of truth for what the stage does. Contains the three protocol tiers, violation decision tree, git diff verification process, and per-phase overhead budget.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 8's namespace. Understand exactly which fields you read and write.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 8's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. The build rules preamble (~8K tokens) that opens every phase originates from these rules. Understand what the preamble contains.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/commands/verify.md`** -- The verification command pattern from Affaan's skill set. Contains patterns for how verification checks are structured, what constitutes a pass/fail, and how to chain verification steps. Use these patterns for structuring pulse, seam, and full checkpoint definitions.

7. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/commands/quality-gate.md`** -- The quality gate pattern from Affaan's skill set. Contains patterns for gate conditions (pass/fail criteria), escalation rules, and how to define thresholds. Use these patterns for the full checkpoint gate condition and the violation severity thresholds.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. A great Stage 8 output is a set of phases where every build order entry has a pulse check, every mechanism interface has a seam check, every phase boundary has a gate, and the violation tree is embedded inline -- not appended.

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns (three-tier protocol hierarchy: pulse < seam < full)
- Decision patterns (where do seam checks go? at mechanism interface points, not arbitrary positions)
- Quality signals (protocols are embedded, not separate; overhead stays within budget; violation tree has 4 severity levels with specific triggers and responses)
- Edge cases (what if a phase has only 1-2 files? pulse cycle is still every file. What if no mechanism interfaces exist within a phase? no seam checks needed, only pulse and full)

**Step 3: Build the SKILL.md.** Write the complete skill file following the format below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** -- Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** -- What happens when required data is missing? When input is ambiguous? When the request is partially out of scope? Are failure modes machine-readable?

4. **Composability** -- Could another skill (Stage 9) consume this skill's output cleanly? Does output contain ONLY the structured deliverable (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-08-protocol-injection
description: {{SINGLE LINE DESCRIPTION -- this is a YAML field, multi-line SILENTLY FAILS}}
---

## Purpose

{{1-2 sentences}}

## When to Use

{{Trigger conditions -- what input or request activates this skill}}

## Input Format

{{Exact JSON structure this skill expects from the context packet}}

## Process

### Step 1: {{Name}}
{{Detailed instructions with decision criteria}}

### Step 2: {{Name}}
{{...}}

[... as many steps as needed ...]

## Output Format

{{Exact JSON structure this skill writes to the context packet -- field names, types, validation rules}}

## Edge Cases

### Missing Input
{{What to do when required fields are empty or missing}}

### Ambiguous Input
{{What to do when input can be interpreted multiple ways}}

### Scope Overflow
{{What to do when the stage discovers work that belongs to a different stage}}

## Confidence Scoring

{{The 5 scoring dimensions from the stage contract, with self-scoring instructions}}

## Escape Hatch

{{When to trigger, what to save, how to signal NEEDS_HUMAN}}

## Example

{{One realistic example showing input --> process --> output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/protocol-tier-templates.md` -- templates for pulse, seam, and full checkpoint definitions with fill-in-the-blank structure
   - `references/violation-decision-tree.md` -- the complete 4-level violation tree with all triggers and responses
   - `references/overhead-budget-breakdown.md` -- the per-component overhead estimates with examples

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for Stage 9, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
phases = context_packet["stage_7"]["phases"]
token_budget = context_packet["stage_7"]["token_budget"]
mechanism_blueprints = context_packet["stage_5"]["mechanism_blueprints"]
mechanism_dependencies = context_packet["stage_4"]["mechanism_dependencies"]
metadata = context_packet["metadata"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_8"] = {
    "protocol_injected_phases": [
        {
            "phase_number": int,
            "pulse_checks": [
                {
                    "after_file": str,
                    "checks": [str],
                    "cycle_position": int
                }
            ],
            "seam_checks": [
                {
                    "after_file": str,
                    "connection_point": str,
                    "checks": [str]
                }
            ],
            "full_checkpoint": {
                "pattern_checks": [str],
                "functional_checks": [str],
                "gate_condition": str
            },
            "violation_rules": {
                "LOW": {"triggers": [str], "response": str},
                "MEDIUM": {"triggers": [str], "response": str},
                "HIGH": {"triggers": [str], "response": str},
                "CRITICAL": {"triggers": [str], "response": str}
            },
            "overhead_tokens": int
        }
    ],
    "overhead_breakdown": {
        "build_rules_preamble": 8000,
        "file_sandbox": 2000,
        "build_order_with_pulse": 3000,
        "seam_checks": 2000,
        "full_checkpoint": 5000,
        "pattern_verification": 3000,
        "violation_handling": 2000
    }
}
context_packet["metadata"]["current_stage"] = 8
context_packet["metadata"]["confidence_scores"]["8"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    }
}
context_packet["metadata"]["stage_timestamps"]["8"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify every phase from Stage 7 has a corresponding protocol_injected_phase
2. Verify every file in every phase's build order has a pulse check
3. Verify seam checks exist at every mechanism interface point within each phase
4. Verify every phase has a full checkpoint with both pattern_checks and functional_checks
5. Verify violation_rules has all four severity levels (LOW, MEDIUM, HIGH, CRITICAL) for every phase
6. Verify overhead_tokens for each phase does not exceed 30,000
7. Verify estimated_tokens (from Stage 7) + overhead_tokens <= 350,000 for each phase
8. Run the confidence scoring
9. If score < 70, trigger escape hatch instead of writing
10. If score 70-89, write but flag in metadata
11. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~40,000-60,000 tokens (Stages 0-7 have accumulated the most content by this point)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- Required input fields are missing (no phases from Stage 7, no mechanism dependencies from Stage 4)
- Phase build order has zero files (cannot inject pulse checks into an empty build order)
- Mechanism dependencies are circular or unresolvable (cannot determine seam check placement)
- Overhead exceeds 30,000 tokens for any phase after injection (protocols are too verbose)
- Confidence score is below 70 after one retry

What to save:
- Current context_packet (with whatever protocol-injected phases exist)
- Stage number (8) and step where the halt occurred
- Which phases were successfully injected and which were not
- The overhead calculations for each phase
- Suggested questions for the human (e.g., "Phase 3 has no mechanism interfaces -- should it have seam checks?")

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness (0-20): Does every phase have pulse checks for every file, seam checks at
   every mechanism interface, and a full checkpoint? Are all four violation severity levels
   defined with specific triggers and responses?

2. Accuracy (0-20): Are seam checks placed at actual mechanism interface points (not arbitrary
   positions)? Do functional checks match the tech stack (npm run build for Node projects,
   cargo build for Rust, etc.)? Are violation triggers realistic and specific?

3. Consistency (0-20): Do the protocol-injected phases match Stage 7's phases exactly (same
   phase numbers, same files, same build order)? Do seam check connection points align with
   Stage 4's mechanism dependency graph?

4. Specificity (0-20): Are pulse checks specific to each file (not generic "does file exist"
   for every file)? Are seam checks specific to the connection (not generic "does A import B")?
   Are functional checks concrete commands (not "verify it works")?

5. Handoff Readiness (0-20): Could Stage 9 (Verification Agent Setup) immediately use these
   protocols to configure an independent checker agent? Is the violation decision tree
   unambiguous enough for automated processing? Are gate conditions binary (pass/fail)?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 9
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-08-protocol-injection/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-08-protocol-injection/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing.
- [ ] **Edge cases explicit:** Missing input, ambiguous input, and scope overflow all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 9 can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions
- [ ] **Escape hatch included:** The trigger conditions, save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic example showing a protocol-injected phase with pulse, seam, and full checkpoint inline in the build order
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md
- [ ] **Three protocol tiers present:** Pulse (every file), Seam (connection points), Full (phase boundary gate)
- [ ] **Violation tree has 4 levels:** LOW, MEDIUM, HIGH, CRITICAL with specific triggers and responses
- [ ] **Overhead stays within budget:** Example shows ~25K overhead per phase, never exceeding 30K
- [ ] **Protocols are inline, not separate:** Example shows checks embedded within the build order, not as an appendix

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-08-protocol-injection/SKILL.md`
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document
- [ ] Contract criteria from stage-contracts.md are achievable by following the skill's process
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] All three protocol tiers (pulse, seam, full) have clear definitions with concrete check examples
- [ ] Violation decision tree has all 4 severity levels with specific triggers and specific responses
- [ ] Full checkpoint includes both pattern checks (git diff) and functional checks (compile/test)
- [ ] Gate condition is explicitly defined as a binary pass/fail
- [ ] Overhead breakdown accounts for all 7 components totaling ~25K tokens
- [ ] Example shows a complete protocol-injected phase with checks embedded inline in the build order
