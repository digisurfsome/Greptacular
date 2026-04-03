---
name: stage-2-gap-analysis
description: Match idea to app archetypes, scan A-N mechanism gaps, ask targeted questions, produce combined_raw + scope contract.
---

## Purpose

Take the raw idea from Stage 1, match it to known app archetypes, scan for missing mechanism categories (A-N), ask the minimum targeted questions needed to fill gaps, and produce a complete information set (`combined_raw`) plus a `scope_contract` for downstream stages. Stage 2 is the first ambiguity-reduction pass — if gaps pass through here, every downstream stage inherits them.

## When to Use

Activate when: `context_packet.stage_1.raw_input` exists AND `context_packet.stage_0.platform_profile` exists (Stages 0 and 1 are complete). Trigger phrases: "gap analysis", "archetype matching", "identify missing mechanisms", "fill gaps", "what's missing from the idea".

Do NOT activate for: raw idea capture (Stage 1), structuring/organizing ideas (Stage 3), breaking into mechanisms (Stage 4), or any request to "build" or "scaffold" features.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": { "boilerplate_id": "string", "boilerplate_name": "string", "description": "string" },
    "tech_stack": { "framework": "string", "database": "string", "auth_provider": "string", "hosting": "string", "additional": {} },
    "checklist_rule_ids": ["string"]
  },
  "stage_1": {
    "raw_input": "string",
    "input_format": "typed | voice_transcript | pasted_notes | mixed",
    "captured_at": "ISO 8601",
    "word_count": 168,
    "char_count": 892,
    "explicit_corrections": [{ "original": "string", "correction": "string" }]
  },
  "metadata": { "app_type": "greenfield | existing", "current_stage": 1 }
}
```

## Process

### Step 1: Assess Detail Level

Read `stage_1.raw_input` and `stage_1.word_count`. Determine expected question depth:

| Word Count | Detail Level | Target Questions |
|------------|-------------|-----------------|
| < 50 | Minimal | 8-15 (minimum 5) |
| 50-150 | Moderate | 5-10 (minimum 2) |
| 150-300 | Detailed | 3-7 (minimum 2) |
| 300+ | Comprehensive | 2-5 (minimum 2) |

If `explicit_corrections` is present, apply corrections: the corrected version takes precedence. If unresolved contradictions exist (user said two conflicting things without correcting), note them for clarifying questions.

### Step 2: Match to App Archetypes

Compare `raw_input` against the 8 archetypes (see `references/archetype-mechanism-maps.md`). Match based on primary user action:

- Views data/metrics -> **Dashboard**
- Buys/sells between parties -> **Marketplace**
- Sends/receives messages -> **Chat**
- Creates/edits/deletes records -> **CRUD/Tool**
- Posts content, follows users -> **Social**
- Walks through step-by-step -> **Wizard**
- Marketing/info page -> **Landing**
- Pays subscription for software -> **SaaS**

**Rules:**
- An app can match MULTIPLE archetypes. Union all REQUIRED categories.
- If subscription billing or team management is mentioned alongside another archetype, ALSO match **SaaS** and union maps.
- Record each match with `confidence` (0-100) and `rationale` citing evidence from `raw_input`.
- If NO archetype matches, set `archetype_matches` to `[{"archetype": "none", "confidence": 100, "rationale": "App does not fit standard archetypes; full A-N scan required"}]`.

### Step 3: Scan A-N Mechanism Categories

Read `raw_input` against all 14 categories from `references/mechanism-categories.md`:

A=Data Input, B=Data Storage, C=Data Processing, D=Data Output, E=Authentication, F=Authorization, G=Communication, H=Integration, I=Workflow, J=Search & Discovery, K=Collaboration, L=Monetization, M=Admin/Ops, N=Infrastructure.

For each category:
1. Search `raw_input` for direct or implied mentions.
2. **Found**: Record in `mechanisms_identified` with sub-types and evidence quote.
3. **Not found**: Record in `mechanisms_gaps` and classify using archetype defaults:

| Archetype Says | User Mentioned? | Action |
|---------------|----------------|--------|
| REQUIRED | No | Gap. Ask about it. `resolution: "asked"` |
| REQUIRED | Yes | Identified. Ask only about uncovered sub-types. |
| OPTIONAL | No | Ask ONE targeted question. |
| OPTIONAL | Yes | Identified. Skip question. |
| UNLIKELY | No | Skip. `resolution: "not_needed"` |
| UNLIKELY | Yes | Override to REQUIRED. Ask sub-questions. |

If no archetype matched, treat ALL 14 categories as potential gaps and ask about each.

### Step 4: Check Structural Checklist

Scan the 30-category structural checklist (Martin's 22 + Industry Standards 10) for coverage gaps that affect mechanism identification:

- Auth mentioned but no auth method specified? Flag.
- Data storage implied but no strategy stated? Flag.
- Monetization mentioned but no pricing model? Flag.

Record in `checklist_coverage`: `.covered` (addressed), `.not_applicable` (explicitly N/A), `.deferred` (Developer's Choice).

### Step 5: Generate Adaptive Questions

Generate questions targeting ONLY identified gaps. Follow `references/question-templates.md` patterns:

1. **REQUIRED gaps**: Ask specific questions with archetype context and 2-3 options.
2. **OPTIONAL categories**: Ask ONE question per category.
3. **UNLIKELY categories**: Do NOT ask unless user mentioned them.
4. **Sub-type gaps in identified categories**: Ask about missing specifics.
5. **Stack-aware**: Use `stage_0.tech_stack` to tailor questions (e.g., Supabase -> ask about Row Level Security).

**Question rules:**
- Be specific, never generic ("tell me more").
- Offer 2-3 concrete options per question.
- Reference what the user ALREADY said.
- Group related questions by category.
- Minimize count while maximizing information gained.

Each question gets a unique ID (`gq_001`, `gq_002`, ...), the A-N category it addresses, and source (`"mechanism_framework"`, `"master_checklist"`, `"archetype_specific"`).

### Step 6: Present Questions and Collect Answers

Present all questions in a single batch, grouped by category. For each answer:
- Record in `gap_answers` with matching `question_id`.
- If user says "I don't know" / "you decide" / "whatever works": set `answer_text: "developers_choice"`, `is_default: true`, and use the archetype's default sub-type.
- If user gives a partial answer: record what they said, mark remaining sub-gaps as Developer's Choice.

### Step 7: Merge into Combined Raw

Concatenate into `combined_raw`:

```
--- ORIGINAL IDEA (from Stage 1) ---
{stage_1.raw_input}

--- GAP ANALYSIS ANSWERS ---
Q: {question_text}
A: {answer_text}

[...repeat for all answered questions...]
```

**Do NOT organize, restructure, or rewrite.** `combined_raw` is raw material for Stage 3.

### Step 8: Calculate Completeness Score

Score 0-100: `(REQUIRED categories with substantive coverage / total REQUIRED) * 70 + (OPTIONAL categories resolved / total OPTIONAL) * 30`.

| Range | Meaning |
|-------|---------|
| 0-30 | Critical gaps — multiple REQUIRED categories missing |
| 31-60 | Major gaps — 2-3 REQUIRED categories thin |
| 61-80 | Moderate — all REQUIRED mentioned, some lack specifics |
| 81-90 | Good — all REQUIRED + most OPTIONAL covered with specifics |
| 91-100 | Excellent — comprehensive coverage |

### Step 9: Write Scope Contract

Produce `scope_contract` string:

```
IN SCOPE:
- [Features, mechanisms, capabilities being built]

NOT IN SCOPE:
- [Explicitly excluded features]
- [Categories marked not_needed]

DEFERRED:
- [Items marked Developer's Choice — system decides approach]
```

## Output Format

Written to `context_packet.stage_2`:

```json
{
  "archetype_matches": [
    { "archetype": "string", "confidence": 85, "rationale": "string" }
  ],
  "mechanisms_identified": [
    { "category_id": "A", "category_name": "Data Input", "sub_types": ["Forms"], "evidence": "quote from raw_input" }
  ],
  "mechanisms_gaps": [
    { "category_id": "L", "category_name": "Monetization", "resolution": "not_needed | asked | developers_choice" }
  ],
  "gap_questions": [
    { "id": "gq_001", "category_id": "H", "question_text": "string", "source": "mechanism_framework | master_checklist | archetype_specific" }
  ],
  "gap_answers": [
    { "question_id": "gq_001", "answer_text": "string", "is_default": false }
  ],
  "combined_raw": "string — Stage 1 raw_input + all gap answers merged",
  "completeness_score": 85,
  "checklist_coverage": {
    "covered": ["category names"],
    "not_applicable": ["category names"],
    "deferred": ["category names"]
  },
  "scope_contract": "IN SCOPE:\n- ...\nNOT IN SCOPE:\n- ...\nDEFERRED:\n- ..."
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 2,
  "archetype_matches": ["marketplace", "saas"],
  "scope_contract_hash": "sha256 hex string",
  "confidence_scores": {
    "2": {
      "score": 88,
      "dimensions": { "completeness": 18, "accuracy": 17, "consistency": 18, "specificity": 17, "handoff_readiness": 18 },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "2": "ISO 8601 timestamp" }
}
```

**Validation before writing:**
1. All required fields populated (no null/empty where content expected)
2. Every `gap_answers[].question_id` matches an entry in `gap_questions[].id`
3. Every REQUIRED category (per archetype) has coverage in `combined_raw`
4. `archetype_matches` has at least one entry with confidence >= 70 (or "none" fallback)
5. All 14 A-N categories classified across `mechanisms_identified` + `mechanisms_gaps`
6. If `word_count < 50`: at least 5 questions asked. If `>= 50`: at least 2.
7. Confidence score computed; gate_result set per thresholds.

## Edge Cases

### Missing Input
- **`raw_input` missing or empty**: Trigger escape hatch immediately.
- **`word_count < 20`**: Trigger escape hatch — minimum viable input not met.

### No Archetype Match
- Set `archetype_matches` to `[{"archetype": "none", "confidence": 100, "rationale": "..."}]`.
- Fall back to full A-N scan — ask about all 14 categories.

### Multiple Archetype Match
- Union all REQUIRED categories from matched archetypes.
- For conflicting default sub-types, ask user which fits better.
- Record all matches in `archetype_matches` array.

### User Declines All Questions
- Set all `gap_answers[].answer_text` to `"developers_choice"`, `is_default: true`.
- Use archetype defaults for all REQUIRED categories.
- If `raw_input` alone has enough detail for Stage 3 (completeness >= 70), proceed with warning.
- If completeness < 70, trigger escape hatch.

### Contradictory Input
- If `explicit_corrections` exists, use corrected version.
- If unresolved contradictions remain in `raw_input`, generate a clarifying question targeting each contradiction.

### Scope Overflow
- If the user asks to structure, organize, or build features: decline. Say: "I'm identifying what's missing from your idea. Structuring happens in the next stage."
- Capture any new information they provide but do not change scope.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All 14 A-N categories classified? `archetype_matches` populated? All questions answered or declined? `combined_raw` present? `checklist_coverage` populated? `scope_contract` present?
- 0-5: >4 categories unclassified; archetype missing
- 6-10: 2-4 unclassified; archetype low confidence (<50)
- 11-15: All classified; 1-2 REQUIRED categories thin
- 16-20: All classified; every REQUIRED category has substantive coverage

**2. Accuracy (0-20):** Archetype match fits the description? Categories correctly identified with valid evidence? Nothing falsely marked "not_needed"?
- 0-5: Archetype clearly wrong
- 6-10: Archetype plausible but not best fit; 2-3 misclassified categories
- 11-15: Archetype matches well; at most 1 borderline classification
- 16-20: Archetype is obvious best match; all classifications defensible

**3. Consistency (0-20):** `gap_answers` align with `raw_input`? Scope contract matches mechanisms? Archetype aligns with identified mechanisms?
- 0-5: Contradictions between answers and raw_input not flagged
- 6-10: Some contradictions partially noted
- 11-15: Minor inconsistencies documented
- 16-20: Internally consistent; all contradictions resolved or flagged

**4. Specificity (0-20):** Questions precise with options and user references? Evidence quotes actual phrases? Answers contain concrete details?
- 0-5: Generic "tell me more" questions
- 6-10: Targeted but broad ("What about authentication?")
- 11-15: Specific gaps with options ("Will auth use email/password, OAuth, or magic links?")
- 16-20: Precise, references user's words, 2-3 options, minimized count

**5. Handoff Readiness (0-20):** Could Stage 3 start immediately from `combined_raw`? Comprehensive enough for all 4 concept document sections?
- 0-5: Stage 3 would need "what is this app?"
- 6-10: Concept identifiable but 3+ sections would struggle
- 11-15: Structured doc possible but 1-2 sections thin
- 16-20: Full concept document producible without additional info

**Total = sum of all 5 (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 3 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `stage_1.raw_input` missing or empty
- `stage_1.word_count < 20`
- No archetype matchable AND description < 10 words about the app concept
- Confidence < 70 after one retry
- User refuses ALL questions AND raw_input alone insufficient for Stage 3

**Save:**
- Current `context_packet` with partial output (archetype matches, partial mechanism scan, questions generated)
- Stage number (2), step where halt occurred, what failed

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 2,
  "step": "step that failed",
  "reason": "specific reason",
  "suggested_actions": ["action 1", "action 2"],
  "partial_output": {}
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input** (`stage_1.raw_input`, 168 words, typed):

> I want to build a task manager app. Like Todoist but simpler. Users can create projects and add tasks to them. Tasks have due dates, priorities (high/medium/low), and you can assign them to other people on your team. I want a kanban board view where you drag tasks between columns like To Do, In Progress, and Done. Also a regular list view sorted by due date. Users need to sign up with email or Google. Oh wait, not just Google — also GitHub login since this is for developer teams. There should be notifications when someone assigns you a task or when a due date is coming up. Maybe email and in-app notifications. I want it to look clean and modern, not cluttered. Dark mode would be nice. Teams should be able to create workspaces and invite members. Oh and I forgot — there should be a simple dashboard showing how many tasks are done vs pending, maybe a chart.

**Step 2 result:** Archetypes matched: CRUD/Tool (confidence: 90, "create projects and add tasks, kanban board, list view") + SaaS (confidence: 75, "teams, workspaces, invite members"). Union REQUIRED: A, B, C, D, E, F, G, L, M.

**Step 3 result:** Mechanisms identified from raw_input: A (Forms, Drag-and-Drop — "create projects and add tasks", "drag tasks between columns"), B (Relational DB — "projects, tasks, due dates, priorities"), C (Validation — "priorities high/medium/low"), D (Lists/Tables, Charts, Kanban — "list view sorted by due date", "kanban board", "chart"), E (Email/Password, OAuth — "sign up with email or Google, GitHub"), F (RBAC — "assign to team"), G (In-App Notifications, Email — "notifications when someone assigns you a task"), K (Profiles — "teams, workspaces, invite members"). Gaps: H (Integration — OPTIONAL, not mentioned), I (Workflow — OPTIONAL for CRUD, "kanban columns" partially covers), J (Search — OPTIONAL, not mentioned), L (Monetization — REQUIRED by SaaS, not mentioned), M (Admin — REQUIRED by SaaS, not mentioned), N (Infrastructure — UNLIKELY, skip).

**Step 5 result — 5 questions generated:**

1. `gq_001` (L): "You mentioned teams and workspaces. Will this be a paid product with subscription tiers (free/pro/team), or free for everyone?"
2. `gq_002` (M): "Will there be an admin role who can manage workspace settings, billing, and member permissions beyond just inviting people?"
3. `gq_003` (H): "Does the app need to integrate with external tools like Slack, GitHub issues, or a calendar app?"
4. `gq_004` (J): "As tasks grow, will users need to search across projects? Full-text search, or just filtering by status/priority/assignee?"
5. `gq_005` (I): "Beyond kanban columns (To Do / In Progress / Done), are there other workflow states or automations? E.g., auto-assign when moved to In Progress?"

**Answers collected, combined_raw produced, completeness score: 88. Confidence: 90/100. Gate: pass.**
