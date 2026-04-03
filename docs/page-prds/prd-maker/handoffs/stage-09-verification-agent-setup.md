# Build Stage 9 Skill: Verification Agent Setup

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-09-verification-agent-setup/SKILL.md`

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

**You are building Stage 9: Verification Agent Setup.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Verification Agent Setup

### Purpose

Sets up an independent verification agent (Agent B) that audits the builder agent's work after each phase. The core principle: **the checker is NEVER the same agent as the builder.** The builder cannot be trusted to check its own work -- a separate agent with no loyalty to the builder's output, no sunk cost, and clean context makes the pass/fail determination. Stage 9 supports two delivery approaches: automated (bash/CLI with a dedicated Agent B) and manual (web-based, where Phase N+1's agent checks Phase N's output as a 30-second preamble).

### Inputs (What This Stage Receives)

From the context packet, this stage reads:

- `stage_8.protocol_injected_phases` -- Array of protocol-injected phase objects, each with pulse_checks, seam_checks, full_checkpoint, violation_rules, and overhead_tokens
- `stage_7.phases` -- Original phase definitions with file sandboxes (files_allowed, files_read_only, files_forbidden), build orders, and mechanism assignments
- `stage_0.tech_stack` -- Platform profile (framework, database, auth, hosting) used to determine which functional checks are applicable (e.g., npm run build for Node, cargo build for Rust)

### Outputs (What This Stage Produces)

Written to `context_packet.stage_9`:

- `verification_mode` (string, enum): "automated_agent_b" or "manual_preamble_merge" -- which approach to use. Both are always configured; this field indicates the PRIMARY mode based on the user's platform choice.

- `two_strike_rule` (object):
  - `max_retries` (integer) -- 2. Always 2.
  - `on_second_failure` (string) -- "stop_for_human_review"
  - `rationale` (string) -- "If two fresh agents fail the same phase, the problem is the phase spec, not the agents. Human must intervene."

- `verification_protocol` (object) -- the 4-step end-of-phase verification:
  - `step_1_self_report` (object):
    - `description` (string) -- "Agent lists every file it created or modified"
    - `compare_against` (string) -- "files_allowed list from phase spec"
  - `step_2_diff_check` (object):
    - `command` (string) -- "git diff PHASE_N_BASELINE..HEAD --name-only"
    - `compare_against` (array of strings) -- ["self_report from step 1", "files_allowed from phase spec"]
    - `mismatch_is_violation` (boolean) -- true. If self-report and diff do not match, that itself is a violation.
  - `step_3_violation_response` (object):
    - `decision_tree_reference` (string) -- "stage_8.protocol_injected_phases[N].violation_rules"
    - `applies_to` (string) -- "any file in diff that is NOT in files_allowed"
  - `step_4_functional_checks` (object):
    - `compile_check` (string) -- tech-stack-appropriate build command
    - `test_check` (string) -- tech-stack-appropriate test command (if tests exist)
    - `render_check` (string) -- "do new pages/components render without errors"
    - `route_check` (string) -- "can you navigate to expected routes"

- `per_phase_checker_config` (array of objects, one per phase):
  - `phase_number` (integer) -- matches phase_number from Stages 7/8
  - `baseline_snapshot` (string) -- "git commit hash before agent starts this phase"
  - `allowed_files` (array of strings) -- copied from stage_7.phases[N].files_allowed
  - `functional_checks` (array of strings) -- specific commands to run for this phase
  - `expected_outcomes` (array of strings) -- what "pass" looks like for each functional check
  - `overrides` (object, optional) -- any phase-specific deviations from the standard protocol (e.g., Phase 1 may have no pre-existing tests to run)

- `agent_b_config` (object) -- configuration for the automated verifier agent:
  - `context_tokens` (integer) -- ~10,000. Agent B is lean: it reads the allowed file list, the diff output, the functional check results, and the violation tree. That is all.
  - `clean_context` (boolean) -- true. Agent B starts with NO knowledge of what Agent A did or why. It only sees evidence.
  - `persistent_across_phases` (boolean) -- true. One Agent B instance lives across the entire build. It accumulates context -- "Phase 1 was clean, Phase 2 had minor drift on a types file, Phase 3..." By Phase 4 it has a PATTERN. If the builder keeps drifting toward the same files, Agent B flags a systemic issue.
  - `receives` (array of strings) -- ["allowed_files_list", "git_diff_output", "functional_check_results", "violation_decision_tree"]
  - `produces` (string) -- "classification: CLEAN | LOW | MEDIUM | HIGH | CRITICAL"
  - `on_high_or_critical` (string) -- "git reset --hard $PHASE_BASELINE, retry with fresh Agent A, apply two_strike_rule"

- `manual_preamble_config` (object) -- configuration for the manual/web approach:
  - `preamble_template` (string) -- the text that opens Phase N+1's prompt, instructing the agent to validate Phase N's deliverables before starting its own work
  - `check_duration_estimate` (string) -- "30 seconds"
  - `agent_count` (string) -- "same as phase count, NOT doubled"
  - `on_issues_found` (string) -- "fix inline before proceeding with Phase N+1 work"

### Process

**Step 1: Determine Verification Mode**

Read `stage_0.tech_stack` to determine the user's platform context. The verification mode depends on how the user will run the build:

- If the user has a bash/CLI automated pipeline (detected from tech stack or explicitly configured): set `verification_mode = "automated_agent_b"`. The dedicated verifier agent runs automatically with zero human intervention.
- If the user will paste prompts into Claude Code web/desktop (manual): set `verification_mode = "manual_preamble_merge"`. The verification check is merged as a preamble into the next phase's prompt.

BOTH configurations are always generated regardless of mode. The mode flag tells Stage 10 which wrapper to use for the output files.

**Step 2: Configure the 4-Step Verification Protocol**

Define the standard 4-step end-of-phase verification that applies to ALL phases regardless of verification mode:

1. **Self-Report**: Agent lists every file it created or modified. Compares against the allowed files list from the phase spec.
2. **Diff Check**: Run `git diff PHASE_N_BASELINE..HEAD --name-only`. Compare this output against BOTH the self-report AND the allowed files list. If self-report and diff disagree, that is itself a violation -- the agent either forgot to mention a file or hallucinated one.
3. **Violation Response**: For any file that appears in the diff but NOT in the allowed list, apply the violation decision tree from Stage 8 (LOW/MEDIUM/HIGH/CRITICAL).
4. **Functional Checks**: Run compile, test, render, and route checks appropriate to the tech stack. ALL FOUR STEPS MUST PASS BEFORE THE NEXT PHASE BEGINS.

**Step 3: Configure Per-Phase Checker Details**

For each phase from Stages 7/8, create a checker config entry:

- Copy the phase's `files_allowed` list as the verification baseline
- Define the git baseline snapshot mechanism (commit hash before phase starts)
- Specify which functional checks apply to this phase (Phase 1 may only have compile; later phases add route checks and test checks as more features exist)
- Define what "pass" looks like for each check (e.g., "npm run build exits with code 0", "route /sign-in returns 200")
- Add any phase-specific overrides (e.g., Phase 1 has no prior features to regression-test)

**Step 4: Configure Agent B (Automated Verifier)**

Define the automated verifier agent's parameters:

- **Context budget**: ~10,000 tokens. Agent B is intentionally lean. It receives ONLY the allowed file list, the git diff output, the functional check results, and the violation decision tree. Nothing else. No mechanism blueprints, no design tokens, no user requirements.
- **Clean context**: Agent B starts fresh with no knowledge of the builder's reasoning or struggles. This is the point -- no sunk cost bias, no sympathy for "but I had to change that file because..."
- **Persistent across phases**: One Agent B lives through the entire build. It accumulates a pattern log. If the builder keeps drifting toward the same unauthorized files across multiple phases, Agent B flags this as a systemic issue, not just individual violations.
- **Decision output**: Agent B produces a single classification per phase: CLEAN, LOW, MEDIUM, HIGH, or CRITICAL.
- **On HIGH or CRITICAL**: Trigger `git reset --hard $PHASE_BASELINE` to revert the entire phase. Start a fresh Agent A (new context, no memory of the failed attempt) to retry the phase. Apply the two-strike rule.

**Step 5: Configure Two-Strike Rule**

The auto-retry logic:

1. Phase fails verification (HIGH or CRITICAL).
2. Revert to baseline. Spawn fresh Agent A. Retry the phase.
3. If the retry ALSO fails verification (HIGH or CRITICAL): STOP FOR HUMAN REVIEW.
4. Rationale: 9 out of 10 agents build correctly. If the first goes rogue, a fresh second agent almost certainly will not. If TWO fresh agents fail the same phase, the problem is the phase specification itself -- the phase is ambiguous, impossible, or contradictory. That is a human problem, not an agent problem.

Do NOT allow 3 or more retries. Two strikes is the limit. More retries waste tokens and almost never succeed when two have already failed.

**Step 6: Configure Manual Preamble (Web Approach)**

For users who paste prompts into a web interface:

- Write a preamble template that opens Phase N+1's prompt. The preamble says: "Before starting Phase N+1, validate Phase N's deliverables: [checklist]. Flag any issues. If issues are found, fix them before proceeding."
- The check is a 30-second preamble, not a separate 10-minute agent run.
- Agent count stays the same as phase count. NEVER double the agent count for manual users. This was a key design decision -- doubling agents means doubling idle time and breaks the user's workflow.
- If the preamble check finds issues, the agent fixes them inline and then proceeds with its own phase's work.

**Step 7: Validate Consistency with Stage 8**

Verify that the verification protocol does not contradict Stage 8's protocol injection:

- Every violation severity level in the checker's decision tree matches Stage 8's violation_rules
- Every functional check references a real command for the tech stack
- The gate condition from Stage 8's full_checkpoint aligns with the 4-step verification protocol
- No checker rule asks the builder to do something the builder's phase spec forbids

### Rules and Constraints

1. **The checker is NEVER the same agent as the builder** (for bash/CLI). The builder cannot be trusted to audit its own work. A separate agent with no loyalty, no sunk cost, and clean context is the only reliable auditor.

2. **Git diff is ground truth**, not agent self-reporting. The diff is deterministic -- it cannot be fooled, cannot hallucinate, cannot miss anything. Self-reporting is a courtesy check; the diff is the real verification.

3. **Two strikes and stop.** If two consecutive fresh agents fail the same phase, the problem is the phase spec, not the agents. Human must intervene. Do not allow 3+ retries.

4. **Detection over prevention.** You do not physically prevent the agent from touching files (that would require OS-level sandboxing, which is overkill and fragile). You DETECT violations immediately at the phase boundary. The alarm + rollback approach is simpler and equally effective.

5. **Blast radius is contained.** Because verification happens at each phase boundary, violations only affect one phase worth of work, not the entire project. This is why per-phase verification exists.

6. **For manual/web users, NEVER double the agent count.** The verification check is merged as a 30-second preamble into the next phase's prompt. Users who paste prompts manually cannot afford to double their agent sessions -- it turns a 90-minute build into a 4-5 hour ordeal with idle gaps.

7. **Stages 8 and 9 are tightly coupled.** Stage 8 defines WHAT to check (pulse, seam, full checkpoint, violation tree). Stage 9 defines WHO checks it (separate Agent B or merged preamble), WHAT HAPPENS when violations are found (two-strike rule, revert, human review), and HOW the checker agent is configured.

8. **Both verification approaches use the same core protocol.** The 4-step verification (self-report, diff check, violation response, functional checks) is identical for automated and manual modes. Only the delivery wrapper changes.

9. **Agent B is lean.** ~10K tokens per verification. It receives ONLY evidence (file list, diff, check results, decision tree). No context about user requirements, design decisions, or mechanism logic. This keeps it fast, cheap, and unbiased.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-09-extraction.md`** -- The full extraction dossier for this stage. This is your primary source of truth. Contains the two verification approaches, the 4-step end-of-phase verification, the two-strike rule, Agent B configuration, and the manual preamble pattern.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 9's namespace. Understand exactly which fields you read and write.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 9's contract. Your skill must produce output that meets all "Done When" criteria and passes the confidence scoring.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist. The verification agent checks compliance against build rules that originate from this checklist. Understand what the build rules contain.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format and pass Nate's Prompt 3 agent-readiness criteria.

6. **`docs/page-prds/prd-maker/extracted-skills/nicknisi/agents/reviewer.md`** -- The reviewer agent pattern from Nick Nisi's skill set. Contains patterns for how an independent reviewer agent is configured: what it receives, what authority it has, how it communicates findings. Use this as a structural reference for Agent B's configuration.

7. **`docs/page-prds/prd-maker/extracted-skills/affaan-m/skills/verification-loop.md`** -- The verification loop pattern from Affaan's skill set. Contains patterns for iterative verification (check -> fix -> re-check), escalation rules, and when to stop retrying. Use this for the two-strike rule and the auto-retry logic.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT stage output looks like. A great Stage 9 output clearly separates the two verification approaches, has a concrete Agent B configuration with specific token budgets, defines the two-strike rule with no ambiguity, and produces a per-phase checker config that Stage 10 can render into build scripts.

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- Structural patterns (two approaches with shared core protocol, per-phase checker config, Agent B as a lean auditor)
- Decision patterns (when to use automated vs manual, when to revert vs proceed, when to stop for human review)
- Quality signals (Agent B has clean context, git diff is ground truth not self-report, two-strike limit is firm)
- Edge cases (what if Phase 1 has no prior features to test? what if all phases pass clean -- does Agent B still accumulate context? what if the user switches from manual to automated mid-build?)

**Step 3: Build the SKILL.md.** Write the complete skill file following the format below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases? Is it specific enough to avoid false matches? Does it specify what the skill PRODUCES?

2. **Output Format Completeness** -- Is the output format completely specified with exact sections, exact fields, exact structure? Could a downstream agent parse this output programmatically?

3. **Explicit Edge Case Handling** -- What happens when required data is missing? When input is ambiguous? When the request is partially out of scope? Are failure modes machine-readable?

4. **Composability** -- Could another skill (Stage 10) consume this skill's output cleanly? Does output contain ONLY the structured deliverable (no conversational preamble)?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-09-verification-agent-setup
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
   - `references/agent-b-config-template.md` -- complete Agent B configuration template with all fields, token budget, and decision output format
   - `references/manual-preamble-template.md` -- the preamble text template that opens Phase N+1's prompt for manual/web users
   - `references/two-strike-bash-script.md` -- the bash script pattern for automated retry with two-strike escalation
   - `references/four-step-verification.md` -- detailed walkthrough of the 4-step end-of-phase verification protocol

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for Stage 10, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
protocol_injected_phases = context_packet["stage_8"]["protocol_injected_phases"]
phases = context_packet["stage_7"]["phases"]
tech_stack = context_packet["stage_0"]["tech_stack"]
metadata = context_packet["metadata"]
```

Only read from stages BEFORE yours. Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_9"] = {
    "verification_mode": str,  # "automated_agent_b" or "manual_preamble_merge"
    "two_strike_rule": {
        "max_retries": 2,
        "on_second_failure": "stop_for_human_review",
        "rationale": str
    },
    "verification_protocol": {
        "step_1_self_report": {"description": str, "compare_against": str},
        "step_2_diff_check": {"command": str, "compare_against": [str], "mismatch_is_violation": True},
        "step_3_violation_response": {"decision_tree_reference": str, "applies_to": str},
        "step_4_functional_checks": {"compile_check": str, "test_check": str, "render_check": str, "route_check": str}
    },
    "per_phase_checker_config": [
        {
            "phase_number": int,
            "baseline_snapshot": str,
            "allowed_files": [str],
            "functional_checks": [str],
            "expected_outcomes": [str],
            "overrides": {}  # optional
        }
    ],
    "agent_b_config": {
        "context_tokens": 10000,
        "clean_context": True,
        "persistent_across_phases": True,
        "receives": [str],
        "produces": str,
        "on_high_or_critical": str
    },
    "manual_preamble_config": {
        "preamble_template": str,
        "check_duration_estimate": "30 seconds",
        "agent_count": "same as phase count, NOT doubled",
        "on_issues_found": str
    }
}
context_packet["metadata"]["current_stage"] = 9
context_packet["metadata"]["confidence_scores"]["9"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    }
}
context_packet["metadata"]["stage_timestamps"]["9"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify verification_mode is one of the two allowed values
2. Verify two_strike_rule.max_retries is exactly 2 (not configurable)
3. Verify all 4 steps of the verification_protocol are defined
4. Verify per_phase_checker_config has one entry for every phase from Stage 7
5. Verify agent_b_config.receives lists exactly 4 items (allowed files, diff, check results, violation tree)
6. Verify manual_preamble_config.preamble_template is non-empty
7. Verify functional checks reference real commands for the tech stack in stage_0
8. Verify violation severity levels in the checker config match Stage 8's violation_rules
9. Run the confidence scoring
10. If score < 70, trigger escape hatch instead of writing
11. If score 70-89, write but flag in metadata
12. If score >= 90, write normally

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~50,000-70,000 tokens (Stages 0-8 have accumulated the most content by this point)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- Required input fields are missing (no protocol_injected_phases from Stage 8, no phases from Stage 7, no tech_stack from Stage 0)
- Tech stack is unrecognized (cannot determine appropriate compile/test commands)
- Violation rules from Stage 8 are incomplete or contradictory
- The checker configuration would contradict the builder's phase spec (e.g., checker expects a file to exist that the phase spec does not create)
- Confidence score is below 70 after one retry

What to save:
- Current context_packet (with whatever checker config exists)
- Stage number (9) and step where the halt occurred
- Which phases have checker configs and which do not
- What was attempted and what failed
- Suggested questions for the human (e.g., "Tech stack X is not recognized -- what compile command should the checker use?")

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

1. Completeness (0-20): Are both verification approaches configured (automated AND manual)?
   Does every phase have a per_phase_checker_config entry? Are all 4 verification protocol
   steps defined? Is the two-strike rule configured with max_retries=2?

2. Accuracy (0-20): Do functional checks reference real commands for the tech stack (not
   placeholder commands)? Does the Agent B configuration match the extraction's spec (~10K
   tokens, clean context, persistent across phases)? Do violation severity levels match
   Stage 8's definitions exactly?

3. Consistency (0-20): Does the checker's allowed_files list match Stage 7's files_allowed
   for each phase? Does the verification protocol align with Stage 8's full_checkpoint gate
   condition? Do the two approaches use the same core protocol with only the wrapper differing?

4. Specificity (0-20): Are git commands exact (not "run a diff" but "git diff PHASE_N_BASELINE
   ..HEAD --name-only")? Is the preamble template concrete text (not "validate the previous
   phase" but specific checklist items)? Are expected_outcomes specific (not "tests pass" but
   "npm run test exits with code 0")?

5. Handoff Readiness (0-20): Could Stage 10 (Output Generator) immediately render this into
   build scripts and phase files? Is the bash retry logic complete enough to copy into a
   build.sh? Is the preamble template ready to paste into Phase N+1's prompt?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 10
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-09-verification-agent-setup/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-09-verification-agent-setup/references/
```

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases and specifies what the skill produces
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent could parse the output with zero guessing.
- [ ] **Edge cases explicit:** Missing input, ambiguous input, and scope overflow all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 10 can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions
- [ ] **Escape hatch included:** The trigger conditions, save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic example showing both automated and manual verification flows
- [ ] **Context packet fields match schema:** Every field read/written matches the context-packet-schema.md
- [ ] **Two verification approaches present:** Both automated (Agent B) and manual (preamble merge) are fully configured
- [ ] **Two-strike rule is firm:** max_retries=2, no configurability, human review on second failure
- [ ] **4-step verification complete:** Self-report, diff check, violation response, functional checks -- all defined
- [ ] **Agent B is lean:** ~10K tokens, clean context, receives only evidence (4 items), produces single classification
- [ ] **Manual approach does NOT double agent count:** Preamble merged into next phase, same agent count as phase count

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-09-verification-agent-setup/SKILL.md`
- [ ] YAML frontmatter has `name` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document
- [ ] Contract criteria from stage-contracts.md are achievable by following the skill's process
- [ ] Reference files (if any) are in the `references/` subfolder and total under 20K tokens
- [ ] Both verification approaches (automated Agent B and manual preamble) are fully defined
- [ ] Two-strike rule is concrete: max_retries=2, stop_for_human_review on second failure
- [ ] 4-step verification protocol is complete with git diff as ground truth
- [ ] Agent B config specifies ~10K token budget, clean context, persistent across phases
- [ ] Manual preamble does not double agent count -- same number of agents as phases
- [ ] Checker configuration does not contradict builder's phase spec from Stages 7/8
- [ ] Example shows both automated flow (Agent A -> diff -> Agent B -> classify -> proceed or revert) and manual flow (Phase N+1 opens with Phase N validation preamble)
