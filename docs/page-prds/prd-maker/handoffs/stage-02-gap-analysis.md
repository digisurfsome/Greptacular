# Build Stage 2 Skill: Gap Analysis

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Output:** `docs/page-prds/prd-maker/skills/stage-02-gap-analysis/SKILL.md`

---

## System Overview: The 10-Stage PRD Maker Pipeline

You are building one skill for a 10-stage pipeline that transforms a non-coder's messy app description into a complete, buildable technical specification. Each stage is a separate Claude Code skill. The stages run in sequence, passing a JSON data object (the "context packet") from one to the next.

### The Pipeline at a Glance

| Stage | Name | Purpose | Key Output |
|-------|------|---------|------------|
| 0 | Technical Foundation | Establish platform context (framework, DB, auth, hosting) before any idea-specific work | Platform profile + agnostic checklist reference |
| 1 | Idea Capture | Capture the user's raw brain dump with zero filtering or structure | Raw text, preserved contradictions, word count |
| **2** | **Gap Analysis** | **Match to archetype, identify missing mechanism categories (A-N), ask targeted questions** | **Complete mechanism map, archetype match, gap answers** |
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

**You are building Stage 2: Gap Analysis.** It reads from stages before it and writes to its own namespace in the context packet.

---

## Your Stage: Gap Analysis

### Purpose

Gap Analysis takes the raw idea from Stage 1 and identifies everything missing, ambiguous, or incomplete -- then generates intelligent questions to fill those gaps BEFORE the information enters any structuring or processing downstream. It matches the idea to known app archetypes, compares against A-N mechanism categories, and asks only the questions needed to achieve completeness. The MORE the user said in Stage 1, the FEWER questions Stage 2 asks.

Gap Analysis exists because every downstream stage assumes its input is COMPLETE. If holes pass through Stage 2 undetected, they compound: a missing payment concept means Stage 4 extracts no payment mechanism, Stage 5 builds no scaffolding for it, Stage 6 generates no wireframe for it, and the entire output PRD is structurally deficient. Stage 2 is the first major ambiguity-reduction pass in the pipeline.

### Inputs (What This Stage Receives)

From `context_packet.stage_1`:

| Field | Type | Description |
|-------|------|-------------|
| `raw_input` | `string` | The user's complete, unfiltered brain dump from Stage 1 |
| `word_count` | `integer` | Word count of `raw_input` -- used to calibrate questioning depth |
| `explicit_corrections` | `array` (optional) | Contradictions the user stated and then corrected |

From `context_packet.stage_0`:

| Field | Type | Description |
|-------|------|-------------|
| `platform_profile` | `object` | Selected platform/boilerplate configuration (framework, database, auth, hosting) |
| `checklist_rule_ids` | `string[]` | List of agnostic checklist rule IDs that apply to this stack |

From `context_packet.metadata`:

| Field | Type | Description |
|-------|------|-------------|
| `app_type` | `string` | `"greenfield"` or `"existing"` |

### Outputs (What This Stage Produces)

Written to `context_packet.stage_2`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `archetype_matches` | `array` | Yes | Matched app archetypes with confidence and rationale |
| `archetype_matches[].archetype` | `string` | Yes | Archetype name (e.g., `"dashboard"`, `"marketplace"`, `"chat"`, `"crud_tool"`, `"social"`, `"wizard"`, `"landing"`, `"saas"`) |
| `archetype_matches[].confidence` | `number` | Yes | Match confidence 0-100 |
| `archetype_matches[].rationale` | `string` | Yes | Why this archetype was matched, with evidence from `raw_input` |
| `mechanisms_identified` | `array` | Yes | A-N mechanism categories found in the raw input |
| `mechanisms_identified[].category_id` | `string` | Yes | Category letter A-N |
| `mechanisms_identified[].category_name` | `string` | Yes | Human-readable name (e.g., `"Data Input"`, `"Authentication"`) |
| `mechanisms_identified[].sub_types` | `string[]` | Yes | Which sub-types within the category were mentioned |
| `mechanisms_identified[].evidence` | `string` | Yes | Quote or paraphrase from raw input that triggered this match |
| `mechanisms_gaps` | `array` | Yes | A-N categories NOT mentioned in raw input |
| `mechanisms_gaps[].category_id` | `string` | Yes | Category letter A-N |
| `mechanisms_gaps[].category_name` | `string` | Yes | Human-readable name |
| `mechanisms_gaps[].resolution` | `string` | Yes | Enum: `"asked"`, `"not_needed"`, `"developers_choice"` |
| `gap_questions` | `array` | Yes | Questions asked to fill gaps |
| `gap_questions[].id` | `string` | Yes | Unique question identifier (format: `gq_001`, `gq_002`, ...) |
| `gap_questions[].category_id` | `string` | Yes | Which A-N category this question addresses |
| `gap_questions[].question_text` | `string` | Yes | The question asked |
| `gap_questions[].source` | `string` | Yes | Enum: `"mechanism_framework"`, `"master_checklist"`, `"archetype_specific"` |
| `gap_answers` | `array` | Yes | User's answers to gap questions |
| `gap_answers[].question_id` | `string` | Yes | References `gap_questions[].id` |
| `gap_answers[].answer_text` | `string` | Yes | User's answer (or `"developers_choice"` if user said "I don't know") |
| `gap_answers[].is_default` | `boolean` | Yes | True if the system used a Developer's Choice default |
| `combined_raw` | `string` | Yes | Stage 1 `raw_input` + all gap answers merged into one text blob. Complete but still unstructured. |
| `completeness_score` | `number` | Yes | 0-100 score for how complete the information set is |
| `checklist_coverage` | `object` | Yes | Coverage of the 30-category structural checklist |
| `checklist_coverage.covered` | `string[]` | Yes | Checklist category names that are covered |
| `checklist_coverage.not_applicable` | `string[]` | Yes | Categories explicitly marked N/A |
| `checklist_coverage.deferred` | `string[]` | Yes | Categories deferred to Developer's Choice |
| `scope_contract` | `string` | Yes | A summary of what IS and IS NOT in scope, used by scope creep detector in later stages |

Additionally, the skill writes to `context_packet.metadata`:

| Field | Path | Description |
|-------|------|-------------|
| `archetype_matches` | `metadata.archetype_matches` | String array of matched archetype names (duplicated from `stage_2` for quick lookup) |
| `scope_contract_hash` | `metadata.scope_contract_hash` | SHA-256 hash of the `scope_contract` string |
| `current_stage` | `metadata.current_stage` | Set to `2` |
| `confidence_scores["2"]` | `metadata.confidence_scores` | Stage 2 confidence object |
| `stage_timestamps["2"]` | `metadata.stage_timestamps` | ISO 8601 completion timestamp |

### Process

#### Step 1: Read and Assess Raw Input

Read `stage_1.raw_input`. Assess the detail level using `stage_1.word_count`:

| Word Count | Detail Level | Expected Question Count |
|------------|-------------|------------------------|
| < 50 | Minimal | 8-15 questions |
| 50-150 | Moderate | 5-10 questions |
| 150-300 | Detailed | 3-7 questions |
| 300+ | Comprehensive | 2-5 questions |

These are guidelines, not hard rules. The actual question count depends on what the user covered, not just how much they wrote.

#### Step 2: Match to App Archetypes

Compare the raw input against the 8 known archetypes from the App Archetype Library. Determine the match using the primary user action described:

- User views data/metrics --> **Dashboard**
- User buys/sells between two parties --> **Marketplace**
- User sends/receives messages in real time --> **Chat / Messaging**
- User creates/edits/deletes records --> **CRUD / Tool**
- User posts content and follows other users --> **Social Platform**
- User walks through a step-by-step process --> **Wizard / Onboarding**
- The output is a marketing/info page --> **Landing Page**
- User pays a subscription for ongoing software access --> **SaaS Product**

**Matching rules:**
- An app can match MULTIPLE archetypes. Example: "a marketplace with analytics" = Marketplace + Dashboard.
- If subscription billing or team management is mentioned alongside another archetype, ALSO match **SaaS Product** and union the mechanism maps.
- If multiple archetypes match, union all REQUIRED categories. A category that is REQUIRED in ANY matched archetype becomes REQUIRED in the combined map.
- Record each match with a confidence score (0-100) and a rationale citing evidence from the raw input.
- If NO archetype matches, set `archetype_matches` to `[{"archetype": "none", "confidence": 100, "rationale": "App does not fit standard archetypes; full A-N scan required"}]`.

#### Step 3: Scan for A-N Mechanism Categories

Read the raw input against all 14 mechanism categories (A through N) from the Mechanism Identification Framework:

| ID | Category |
|----|----------|
| A | Data Input |
| B | Data Storage |
| C | Data Processing |
| D | Data Output |
| E | Authentication |
| F | Authorization |
| G | Communication |
| H | Integration |
| I | Workflow |
| J | Search & Discovery |
| K | Collaboration |
| L | Monetization |
| M | Admin/Ops |
| N | Infrastructure |

For each category:
1. Search the raw input for any mention (direct or implied) of this category.
2. If found, record in `mechanisms_identified` with the specific sub-types mentioned and an evidence quote from the raw input.
3. If NOT found, record in `mechanisms_gaps` with resolution status `"asked"` (will ask about it), `"not_needed"` (archetype says UNLIKELY and user did not mention it), or `"developers_choice"` (user said "I don't know").

**Classification logic using archetype defaults:**
- If the archetype says REQUIRED for this category AND the raw input does not mention it: the category is a gap. Ask about it.
- If the archetype says REQUIRED AND the raw input does mention it: the category is identified. Ask only about sub-types not covered.
- If the archetype says OPTIONAL: ask ONE targeted question about whether the user needs it.
- If the archetype says UNLIKELY AND the raw input does NOT mention it: mark `resolution: "not_needed"` and skip.
- If the archetype says UNLIKELY BUT the raw input DOES mention it: override to REQUIRED and ask sub-questions.

#### Step 4: Check Against the Structural Checklist

Check the 30-category structural checklist (Martin's agnostic checklist + Industry Standards Supplement) for coverage. Most structural categories are handled by the Stage 0 platform profile and preamble. Stage 2 only flags structural gaps that affect mechanism identification:

- Is auth mentioned but no auth method specified? Flag.
- Is data storage implied but no strategy stated? Flag.
- Is monetization mentioned but no pricing model given? Flag.

Record coverage in `checklist_coverage.covered`, `.not_applicable`, and `.deferred`.

#### Step 5: Generate Adaptive Gap Questions

Generate questions targeting ONLY the identified gaps. Follow these rules:

1. **REQUIRED gaps from archetype**: Ask a specific question referencing what the archetype typically needs. Example: "Marketplaces need payment processing. How will buyers pay sellers? (Stripe, PayPal, crypto, other?)"
2. **OPTIONAL categories from archetype**: Ask ONE question per category. Example: "Does your app need real-time chat between users?"
3. **UNLIKELY categories**: Do NOT ask unless the user already mentioned them.
4. **Sub-type gaps within identified categories**: If the user mentioned "users can upload files" but did not specify types or size limits, ask about the specifics.
5. **Stack-aware questions**: Use `stage_0.platform_profile` to make questions relevant. Example: if the stack is Supabase, ask "Will you use Supabase Row Level Security for data isolation?"

**Question formatting rules:**
- Each question must be specific, not generic. Never ask "tell me more about X."
- Each question should offer 2-3 concrete options when possible. Example: "How will users authenticate? (email/password, Google OAuth, magic link, or something else?)"
- Reference what the user ALREADY said to show the system is listening. Example: "You mentioned users can upload photos. What file types and size limits? (JPEG/PNG only, up to 10MB? Or also video?)"
- Group related questions together. Do not ask about auth, then payments, then auth again.
- Limit to the MINIMUM number of questions that achieve completeness.

Each question is recorded in `gap_questions` with a unique ID, the A-N category it addresses, the question text, and the source (mechanism framework, master checklist, or archetype-specific).

#### Step 6: Present Questions and Collect Answers

Present all gap questions to the user in a single batch, grouped by category. For each answer:
- Record in `gap_answers` with the matching question ID.
- If the user says "I don't know" or "you decide" or "whatever works": set `answer_text: "developers_choice"`, `is_default: true`, and use the archetype's default sub-type for that category.
- If the user gives a partial answer, record what they said and mark any remaining sub-gaps for Developer's Choice.

#### Step 7: Merge into Combined Raw

Concatenate Stage 1 `raw_input` with all gap answers into `combined_raw`. Format:

```
--- ORIGINAL IDEA (from Stage 1) ---
{stage_1.raw_input}

--- GAP ANALYSIS ANSWERS ---
Q: {question_text}
A: {answer_text}

Q: {question_text}
A: {answer_text}

[...repeat for all answered questions...]
```

This is still UNSTRUCTURED text. Stage 2 does NOT organize, clean up, or rewrite anything. The combined_raw is raw material for Stage 3.

#### Step 8: Calculate Completeness Score

Score the completeness of the combined information set (0-100):

| Score Range | Meaning |
|-------------|---------|
| 0-30 | Critical gaps remain -- multiple REQUIRED categories have no coverage |
| 31-60 | Major gaps -- 2-3 REQUIRED categories are thin or missing |
| 61-80 | Moderate -- all REQUIRED categories mentioned but some lack specifics |
| 81-90 | Good -- all REQUIRED and most OPTIONAL categories covered with specifics |
| 91-100 | Excellent -- comprehensive coverage across all relevant categories |

Completeness is scored by counting: (REQUIRED categories with substantive coverage) / (total REQUIRED categories) * 70 + (OPTIONAL categories resolved) / (total OPTIONAL categories) * 30.

#### Step 9: Write Scope Contract

Produce a `scope_contract` string that clearly states:

```
IN SCOPE:
- [List of features, mechanisms, and capabilities that ARE being built]

NOT IN SCOPE:
- [List of features, mechanisms, and capabilities that are explicitly EXCLUDED]
- [Categories marked not_needed or deferred]

DEFERRED:
- [Items marked as Developer's Choice -- system will decide the best approach]
```

The scope contract is used by downstream stages as a scope creep detector. If a later stage tries to introduce something not listed in the IN SCOPE section, it is flagged as potential scope creep.

### Rules and Constraints

1. **Adaptive questioning is mandatory.** A detailed rant (300+ words) covering most mechanism categories should produce only 2-5 targeted questions. A vague 2-sentence description should produce 8-15 questions. NEVER use a fixed question list.

2. **Leverage known app archetypes to minimize questions.** If the user describes a marketplace, do NOT ask "does your app need data storage?" -- the archetype already tells you it does. Only ask about GAPS between what the user said and what the archetype requires.

3. **"Fewer questions is better" -- as long as completeness is achieved.** The user explicitly stated: "You're now breaking it down to the fewest amount of questions needed." Every question must target a specific, identifiable gap. No padding, no generic exploration.

4. **Stage 2 does NOT structure.** Output is still messy human language. The `combined_raw` field is a text blob, not organized sections. Structuring is Stage 3's job. If you find yourself creating headers, bullet points, or organized sections in `combined_raw`, you are overstepping.

5. **Questions target specific ambiguities, not broad categories.** Instead of "Tell me about authentication," ask "Will users sign in with email/password, Google OAuth, or magic links?" Instead of "What about payments?", ask "Will you take a commission on each transaction? If so, what percentage?"

6. **Gap Analysis prevents rework downstream.** Its primary function is catching missing concepts early. If a concept passes through Stage 2 undetected, every downstream stage inherits the gap. Err on the side of asking one extra question over letting a gap through.

7. **Developer's Choice is a valid answer.** When a user says "I don't know," the system uses the archetype's default. This is not a failure -- it is the system working as designed. Record it honestly with `is_default: true`.

8. **Minimum question counts by input length.** If `word_count < 50`, ask at least 5 questions. If `word_count >= 50`, ask at least 2 questions. Even detailed rants have gaps worth catching.

9. **Handle contradictions from Stage 1.** If `explicit_corrections` is present, the corrected version takes precedence. If the raw input contains unresolved contradictions (user said two conflicting things without correcting), ask a clarifying question rather than guessing.

10. **Use platform profile for stack-aware questions.** If the user chose Supabase in Stage 0, ask Supabase-specific questions (Row Level Security, Edge Functions). If they chose Firebase, ask about Firestore rules and Cloud Functions. Generic questions are a last resort.

---

## Files to Read Before Building

Read ALL of these files completely before writing any skill content:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-02-extraction.md`** -- The full extraction dossier for Stage 2. This is your primary source of truth for what the stage does, including the design philosophy behind adaptive questioning, the preformed scaffolding concept, and the relationship between gap analysis and downstream stages.

2. **`docs/page-prds/prd-maker/context-packet-schema.md`** -- The data schema. Find Stage 2's namespace (section 2.4). Understand exactly which fields you read and write. Every field name, type, and validation rule in your SKILL.md must match this document.

3. **`docs/page-prds/prd-maker/stage-contracts.md`** -- Find Stage 2's contract (section "Stage 2: Gap Analysis"). Your skill must produce output that meets all 7 "Done When" criteria and passes the 5-dimension confidence scoring.

4. **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`** -- The structural checklist (~192 rules across 22 categories). Stage 2 does not enforce these rules, but it checks coverage to identify structural gaps that affect mechanism identification.

5. **`docs/page-prds/prd-maker/nate-jones-skill-kit.md`** -- The skill-building methodology. Your SKILL.md must follow Nate's Prompt 2 output format (extract methodology from examples, specify output completely) and pass Nate's Prompt 3 agent-readiness criteria (trigger routing, output completeness, edge case handling, composability).

6. **Stage-specific reference files:**
   - **`docs/page-prds/prd-maker/extracted-skills/nicknisi/references/confidence-rubric.md`** -- Confidence scoring pattern with 5 dimensions, thresholds, and question best practices. Stage 2's questioning engine should follow the "Question Best Practices" section (be specific, offer options, reference context, limit quantity, prioritize, chain logically).
   - **`docs/page-prds/prd-maker/mechanism-identification-framework.md`** -- The "Periodic Table of App Mechanisms" with all 14 categories (A-N), their sub-types, and sub-questions. This is the primary reference for what to scan for in the raw input and what sub-questions to ask for each identified mechanism.
   - **`docs/page-prds/prd-maker/app-archetype-library.md`** -- The 8 app archetypes with their mechanism requirement maps (REQUIRED/OPTIONAL/UNLIKELY per category), standard pages, and the 7-step usage instructions for Stage 2. This is the core reference for adaptive questioning -- it tells you which categories to ask about and which to skip.

7. **`docs/page-prds/prd-maker/industry-standards-checklist.md`** -- The Industry Standards Supplement (71 rules across 10 gap areas). Together with Martin's checklist, this forms the complete "30-category structural checklist" referenced in the outputs. Scan for structural coverage gaps.

---

## Skill Building Instructions

You are building a Claude Code skill using the **Nate B. Jones Output-Extraction Method** (Prompt 2). This means you do NOT write a vague process description -- you reverse-engineer what GREAT output looks like and encode that into the skill.

### The Build Process

**Step 1: Understand the output.** Read the stage extraction dossier. Understand what a PERFECT Stage 2 output looks like. A perfect output has:
- Archetype matches with high confidence and evidence-backed rationale
- Complete A-N mechanism scan with no categories left unclassified
- Adaptive questions that are specific, offer options, and reference the user's own words
- All gap answers recorded with honest Developer's Choice flagging
- A `combined_raw` that contains ALL raw material (Stage 1 + gap answers) without any structuring
- A completeness score that honestly reflects coverage
- A scope contract that clearly delineates boundaries

**Step 2: Extract the methodology.** From the extraction dossier and reference skills, identify:
- **Structural patterns:** Archetype matching happens first, then mechanism scanning, then question generation. Questions are grouped by category and presented in a single batch.
- **Decision patterns:** REQUIRED/OPTIONAL/UNLIKELY classification drives question generation. Word count calibrates depth. Archetype defaults serve as Developer's Choice fallback.
- **Quality signals:** Great output has minimal questions that achieve maximum completeness. Questions reference the user's words. No generic "tell me more" questions. Every REQUIRED category has coverage.
- **Edge cases:** No archetype match triggers full A-N scan. Multiple archetype matches trigger category union. User declines to answer triggers Developer's Choice. Contradictions in raw input trigger clarifying questions.

**Step 3: Build the SKILL.md.** Write the complete skill file following the format in the "Skill Format Requirements" section below.

**Step 4: Self-audit against the 4 Agent-Readiness Criteria** (Nate's Prompt 3):

1. **Trigger Description as Routing Table** -- Does your description contain specific trigger phrases like "gap analysis", "identify missing mechanisms", "archetype matching"? Is it specific enough to avoid false matches with Stage 4 (Mechanism Extraction)? Does it specify that the skill PRODUCES archetype matches, mechanism maps, gap questions, combined raw, and a scope contract?

2. **Output Format Completeness** -- Is every output field specified with exact name, type, and description? Could Stage 3 parse `combined_raw` programmatically? Could a validator check that every REQUIRED category has coverage?

3. **Explicit Edge Case Handling** -- What happens when `raw_input` is under 20 words? When no archetype matches? When the user declines to answer all questions? When the raw input contradicts itself? Each case must have a defined, machine-readable behavior.

4. **Composability** -- Can Stage 3 consume `combined_raw` without any human interpretation? Does the output contain ONLY structured data (no "Here is what I found" preamble)? Could a validator confirm all `gap_answers[].question_id` values match entries in `gap_questions[].id`?

If ANY criterion fails, revise the skill before finalizing.

---

## Skill Format Requirements

### SKILL.md Structure

```markdown
---
name: stage-2-gap-analysis
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

{{One realistic example showing input -> process -> output for this stage}}
```

### Critical Format Rules

1. **YAML frontmatter `description` MUST be a single line.** Multi-line descriptions silently fail in Claude Code. Keep it under 120 characters.

2. **Total SKILL.md body MUST be under 500 lines / 5,000 tokens.** This is a hard limit from Claude Code's context window management. After compaction, skills are truncated to 5K tokens.

3. **Large reference material goes in a `references/` subfolder**, NOT in the SKILL.md body. Create files like:
   - `references/archetype-mechanism-maps.md` -- Extracted subset of the App Archetype Library showing REQUIRED/OPTIONAL/UNLIKELY per archetype for quick lookup during gap analysis
   - `references/mechanism-categories.md` -- Condensed A-N category list with sub-types and key sub-questions for each category
   - `references/question-templates.md` -- Template question patterns for each gap type (REQUIRED gap, OPTIONAL inquiry, sub-type specifics, stack-aware)
   - `references/example-output.md` -- Extended example if the inline example is too large

4. **Output must be structured data (JSON or strict Markdown).** No free-form prose in the output section. Every field must have a name, type, and description.

5. **No conversational text in output.** The skill's output is data for the next stage, not a message for a human. No "Here is what I found:" or "I analyzed the following:".

---

## Context Packet Integration

### Reading Input

Your skill reads from the context packet like this:

```python
# Pseudocode -- the skill receives the full context_packet JSON
stage_1 = context_packet["stage_1"]
raw_input = stage_1["raw_input"]
word_count = stage_1["word_count"]
explicit_corrections = stage_1.get("explicit_corrections", [])

stage_0 = context_packet["stage_0"]
platform_profile = stage_0["platform_profile"]
checklist_rule_ids = stage_0["checklist_rule_ids"]

app_type = context_packet["metadata"]["app_type"]
```

Only read from stages BEFORE yours (stage_0, stage_1). Never read from stages after yours (they do not exist yet).

### Writing Output

Your skill writes to its own namespace:

```python
context_packet["stage_2"] = {
    "archetype_matches": [...],
    "mechanisms_identified": [...],
    "mechanisms_gaps": [...],
    "gap_questions": [...],
    "gap_answers": [...],
    "combined_raw": "...",
    "completeness_score": 85,
    "checklist_coverage": {
        "covered": [...],
        "not_applicable": [...],
        "deferred": [...]
    },
    "scope_contract": "..."
}

context_packet["metadata"]["current_stage"] = 2
context_packet["metadata"]["archetype_matches"] = ["marketplace", "saas"]
context_packet["metadata"]["scope_contract_hash"] = "sha256_of_scope_contract"
context_packet["metadata"]["confidence_scores"]["2"] = {
    "score": total_score,
    "dimensions": {
        "completeness": score_1,
        "accuracy": score_2,
        "consistency": score_3,
        "specificity": score_4,
        "handoff_readiness": score_5
    },
    "gate_result": "pass"  # or "flag" or "fail"
}
context_packet["metadata"]["stage_timestamps"]["2"] = "ISO-8601-timestamp"
```

### Validation Before Writing

Before writing output, the skill MUST:
1. Verify all required output fields are populated (no null or empty arrays where content is expected)
2. Verify every `gap_answers[].question_id` matches an entry in `gap_questions[].id`
3. Verify every REQUIRED category (per matched archetype) has at least one sentence of coverage in `combined_raw`
4. Verify `archetype_matches` has at least one entry with confidence >= 70 (or the "none" fallback)
5. Run the confidence scoring
6. If score < 70, trigger escape hatch instead of writing
7. If score 70-89, write but flag in metadata with `gate_result: "flag"`
8. If score >= 90, write normally with `gate_result: "pass"`

---

## Token Budget

Your skill will run within a Claude Code session with approximately 400,000-450,000 total tokens available (after accounting for system prompts, tools, and the context packet itself).

Budget allocation:
- SKILL.md: ~5,000 tokens (hard limit)
- References (combined): ~20,000 tokens max
- Context packet input: ~10,000-30,000 tokens (Stage 0 + Stage 1 data; Stage 1 raw_input can be large for detailed rants)
- Working space for the agent: remaining tokens

Keep your skill lean. Do not repeat information available in the context packet. Reference it by field name instead.

The mechanism identification framework (A-N categories) and archetype library are large documents. In your `references/` subfolder, extract ONLY the information the skill needs at runtime:
- Archetype mechanism maps (the REQUIRED/OPTIONAL/UNLIKELY table for each archetype)
- Category names and their key sub-questions (not the full sub-type tables)
- Question templates (not the full examples and theory text)

---

## Escape Hatch Pattern

Every stage uses this standard escape hatch. Include it in your SKILL.md:

```
When to trigger:
- stage_1.raw_input is missing or empty
- stage_1.word_count < 20 (minimum viable input not met)
- No archetype can be matched AND the user's description is too vague to perform a full A-N scan (< 10 words describing the app concept)
- Confidence score is below 70 after one retry
- The user refuses to answer ALL gap questions and the raw input alone is insufficient for Stage 3

What to save:
- Current context_packet (with whatever partial output exists -- archetype matches, partial mechanism scan, questions generated so far)
- Stage number (2) and step where the halt occurred
- What was attempted and what failed
- Suggested questions for the human (specific questions to ask the user to unblock)

How to signal:
- Set metadata.status = "needs_human"
- Add an entry to metadata.escape_hatches array:
  {
    "stage": 2,
    "step": "the step that failed",
    "reason": "specific reason",
    "suggested_actions": ["specific action 1", "specific action 2"],
    "partial_output": { ... whatever was completed ... }
  }
- Save context_packet snapshot to disk
- Output a structured NEEDS_HUMAN message with the specific problem and suggested actions
```

---

## Confidence Gate Pattern

Include this self-scoring process in your SKILL.md:

```
After producing output, score each dimension 0-20:

1. Completeness: Are ALL 14 A-N categories classified (identified, gap with resolution, or not_needed)?
   Is archetype_matches populated? Are all gap_questions answered or declined? Is combined_raw present
   and non-empty? Is checklist_coverage populated? Is scope_contract present?

2. Accuracy: Does the archetype match actually fit what the user described? Are mechanism categories
   correctly identified (evidence quotes match the category)? Are categories not falsely marked as
   "not_needed" when the user implied them?

3. Consistency: Do gap_answers align with raw_input (no contradictions introduced)? Does the scope
   contract match the mechanisms identified? Do archetype matches align with mechanisms_identified?

4. Specificity: Are gap questions precise (offering options, referencing user's words) rather than
   generic ("tell me more")? Are mechanism evidence quotes actual phrases from raw_input, not
   paraphrases? Do gap_answers contain concrete details, not vague acknowledgments?

5. Handoff Readiness: Could Stage 3 start immediately from combined_raw without needing any
   additional information? Is combined_raw comprehensive enough that Stage 3 can produce a full
   concept document covering all four sections (concept_and_context, target_user_and_market,
   feasibility_assessment, problem_statement)?

Total = sum of all 5 dimensions (/100)

>= 90: PASS -- proceed to Stage 3
70-89: WARN -- flag low dimensions, proceed with warning
< 70:  FAIL -- trigger escape hatch, do NOT pass output forward
```

---

## Stage 2 Contract Criteria (from stage-contracts.md)

Your skill must produce output that satisfies ALL of these "Done When" criteria:

1. Every mechanism category (A-N) has a classification (REQUIRED, OPTIONAL, or UNLIKELY) in the mechanism map -- realized through `mechanisms_identified` and `mechanisms_gaps` arrays covering all 14 categories.
2. `archetype_matches` has at least one entry with confidence >= 0.7 (70%).
3. All questions in `gap_questions` have corresponding entries in `gap_answers` with status resolved -- none remain unanswered.
4. `combined_raw` contains both the original `raw_input` AND all gap answers combined into a single text block.
5. If `word_count` from Stage 1 was < 50, at least 5 gap questions were asked; if >= 50, at least 2 gap questions were asked.
6. For every category classified as REQUIRED (per archetype mapping), at least one sentence in `combined_raw` addresses that category.
7. `mechanisms_gaps` explicitly lists any categories where the user declined to answer, with the Developer's Choice default noted via the `resolution` field.

---

## Output Location

Save the completed skill to:

```
docs/page-prds/prd-maker/skills/stage-02-gap-analysis/SKILL.md
```

If you need reference files, save them to:

```
docs/page-prds/prd-maker/skills/stage-02-gap-analysis/references/
```

Expected reference files for Stage 2:

- `references/archetype-mechanism-maps.md` -- REQUIRED/OPTIONAL/UNLIKELY matrix for all 8 archetypes (extracted from app-archetype-library.md)
- `references/mechanism-categories.md` -- Condensed A-N category reference with key sub-questions
- `references/question-templates.md` -- Reusable question patterns for different gap types

---

## Agent-Readiness Checklist (Must Pass ALL)

Before finalizing your SKILL.md, verify:

- [ ] **Trigger routing:** The `description` field in YAML frontmatter contains specific trigger phrases ("gap analysis", "archetype matching", "mechanism gap identification") and specifies that the skill produces archetype matches, mechanism maps, gap questions/answers, combined raw text, and a scope contract
- [ ] **Output completeness:** Every output field has a name, type, and description. A downstream agent (Stage 3) could parse `combined_raw` and every structured field with zero guessing.
- [ ] **Edge cases explicit:** Missing input (empty raw_input, word_count < 20), no archetype match, user declines all questions, contradictory input, and scope overflow all have defined behaviors with machine-readable responses
- [ ] **Composability:** The output contains ONLY structured data. No conversational text, no preamble, no "Here is what I found." Stage 3 can consume the output as-is.
- [ ] **Under 500 lines:** The SKILL.md body (excluding frontmatter) is under 500 lines
- [ ] **Single-line description:** The YAML `description` field is exactly one line, under 120 characters
- [ ] **Confidence gate included:** The self-scoring process is documented with all 5 dimensions specific to Stage 2
- [ ] **Escape hatch included:** The trigger conditions (missing input, vague input, user refusal, low confidence), save protocol, and signal method are documented
- [ ] **Example included:** At least one realistic input/output example showing a user's raw idea being matched to an archetype, gaps identified, questions generated, answers collected, and combined_raw produced
- [ ] **Context packet fields match schema:** Every field read (stage_0, stage_1) and written (stage_2, metadata) matches the context-packet-schema.md exactly
- [ ] **Contract criteria achievable:** Following the skill's process step-by-step will produce output meeting all 7 "Done When" criteria from the stage contract
- [ ] **Reference files created:** archetype-mechanism-maps.md, mechanism-categories.md, and question-templates.md are in the references/ subfolder and total under 20K tokens combined

---

## Success Criteria

- [ ] SKILL.md exists at `docs/page-prds/prd-maker/skills/stage-02-gap-analysis/SKILL.md`
- [ ] YAML frontmatter has `name: stage-2-gap-analysis` and single-line `description`
- [ ] SKILL.md body is under 500 lines
- [ ] All sections present: Purpose, When to Use, Input Format, Process, Output Format, Edge Cases, Confidence Scoring, Escape Hatch, Example
- [ ] Passes all 4 agent-readiness criteria (trigger routing, output completeness, edge cases, composability)
- [ ] Context packet fields match the schema document (section 2.4 for stage_2 outputs)
- [ ] All 7 "Done When" contract criteria from stage-contracts.md are achievable by following the skill's process
- [ ] Reference files (archetype-mechanism-maps.md, mechanism-categories.md, question-templates.md) are in the `references/` subfolder and total under 20K tokens
- [ ] The skill encodes ADAPTIVE questioning (not a fixed checklist) with clear word-count-to-question-depth calibration
- [ ] The skill handles all edge cases: no archetype match, multiple archetype match, user "I don't know" answers, contradictory input, minimal input (< 50 words), comprehensive input (300+ words)
