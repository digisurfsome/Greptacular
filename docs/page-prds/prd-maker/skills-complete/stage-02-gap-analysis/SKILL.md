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


---

## REFERENCE: archetype-mechanism-maps

# Archetype Mechanism Maps

> Quick lookup: REQUIRED (R), OPTIONAL (O), UNLIKELY (U) per archetype per A-N category.
> Source: `app-archetype-library.md`. Used by Stage 2 to determine which gaps to ask about.

## Combined Matrix

| Cat | Name | Dashboard | Marketplace | Chat | CRUD/Tool | Social | Wizard | Landing | SaaS |
|-----|------|-----------|-------------|------|-----------|--------|--------|---------|------|
| A | Data Input | R | R | R | R | R | R | O | R |
| B | Data Storage | R | R | R | R | R | R | U | R |
| C | Data Processing | R | R | O | R | R | R | U | R |
| D | Data Output | R | R | R | R | R | R | R | R |
| E | Authentication | R | R | R | R | R | O | U | R |
| F | Authorization | O | R | O | O | R | U | U | R |
| G | Communication | O | R | R | O | R | O | O | R |
| H | Integration | O | R | O | O | O | O | O | O |
| I | Workflow | U | R | U | O | U | R | U | U |
| J | Search & Discovery | O | R | O | O | R | U | U | O |
| K | Collaboration | U | U | R | O | R | U | U | O |
| L | Monetization | U | R | U | U | U | U | U | R |
| M | Admin/Ops | O | R | O | U | R | U | U | R |
| N | Infrastructure | O | U | O | U | O | U | O | U |

## REQUIRED Category Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY | Total Active (R+O) |
|-----------|----------|----------|----------|-------------------|
| Dashboard | 5 (ABCDE) | 6 (FGHJMN) | 3 (IKL) | 11 |
| Marketplace | 12 (ABCDEFGHIJLM) | 0 | 2 (KN) | 12 |
| Chat | 6 (ABDEGK) | 6 (CFHJMN) | 2 (IL) | 12 |
| CRUD/Tool | 5 (ABCDE) | 6 (FGHIJK) | 3 (LMN) | 11 |
| Social | 10 (ABCDEFGJKM) | 2 (HN) | 2 (IL) | 12 |
| Wizard | 5 (ABCDI) | 3 (EGH) | 6 (FJKLMN) | 8 |
| Landing | 1 (D) | 4 (AGHN) | 9 (BCEFIJKLM) | 5 |
| SaaS | 9 (ABCDEFGLM) | 3 (HJK) | 2 (IN) | 12 |

## Default Sub-Types per Archetype (REQUIRED categories only)

### Dashboard
- A: Forms (filter controls, date pickers)
- B: Relational DB or API
- C: Calculations (aggregations, statistics)
- D: Charts/Graphs
- E: Email/Password

### Marketplace
- A: Forms (listing creation)
- B: Relational DB
- C: Validation (pricing, availability)
- D: Lists/Tables (browse listings)
- E: Email/Password + OAuth
- F: RBAC (buyer/seller/admin)
- G: In-App Notifications
- H: Payment Gateways (Stripe/PayPal)
- I: State Machines (order flow)
- J: Faceted Search
- L: Marketplace/Commission
- M: Content Moderation

### Chat / Messaging
- A: Forms (message composer)
- B: NoSQL/Document
- D: Real-time Feeds
- E: Email/Password
- G: Chat/Messaging + Push Notifications
- K: Profiles (presence, status)

### CRUD / Tool
- A: Forms (record creation/editing)
- B: Relational DB
- C: Validation
- D: Lists/Tables
- E: Email/Password

### Social Platform
- A: Forms + File Upload
- B: Relational DB + Blob Storage
- C: Filtering/Sorting (feed ranking)
- D: Real-time Feeds
- E: OAuth/Social
- F: Resource Ownership (privacy)
- G: In-App Notifications
- J: Full-text Search
- K: Comments + Reactions + Following
- M: Content Moderation

### Wizard / Onboarding
- A: Forms (multi-step)
- B: Relational DB (persist progress)
- C: Validation (per-step)
- D: Lists/Tables (summary/review)
- I: Wizards/Multi-step

### Landing Page
- D: Lists/Tables (feature tables, pricing)

### SaaS Product
- A: Forms (data entry, settings)
- B: Relational DB
- C: Calculations (business logic, metering)
- D: Lists/Tables + Charts
- E: Email/Password + OAuth
- F: RBAC + Feature Flags (tier gating)
- G: Email (transactional)
- L: Subscriptions
- M: Admin Dashboard

## Multi-Archetype Union Rules

When multiple archetypes match:
1. A category REQUIRED in ANY archetype -> REQUIRED in combined map.
2. A category OPTIONAL in one and UNLIKELY in another -> OPTIONAL wins.
3. For conflicting default sub-types, ask the user which fits.
4. SaaS always adds: F (RBAC + Feature Flags), G (Email), L (Subscriptions), M (Admin).


---

## REFERENCE: mechanism-categories

# Mechanism Categories A-N — Condensed Reference

> Source: `mechanism-identification-framework.md`. Stage 2 uses this to scan raw_input and generate sub-questions.

## Category A: Data Input
**What it is:** How data enters the system.
**Sub-types:** Forms, File Upload, Voice/Audio, Camera/OCR, Drag-and-Drop, Sensors/IoT, Copy/Paste & Import.
**Key sub-questions:**
1. What data types do users input? (text, numbers, dates, files, rich text?)
2. Multi-step forms or wizards?
3. File types accepted? Size limits?
4. Real-time validation or on-submit?
5. Bulk input needed? (CSV import, batch creation?)
6. Draft/autosave requirements?

## Category B: Data Storage
**What it is:** How and where data persists.
**Sub-types:** Relational DB, NoSQL/Document, Blob/File Storage, Cache Layer, Search Index, Audit Trail.
**Key sub-questions:**
1. Main entities/objects? (users, products, orders?)
2. Relationships between entities?
3. Schema fixed or flexible?
4. Data volume? (hundreds, thousands, millions?)
5. Data isolated per user/tenant or shared?
6. Audit/history requirement?

## Category C: Data Processing
**What it is:** Transformations, calculations, and logic.
**Sub-types:** Validation, Calculations, AI/ML, Batch Processing, Format Conversion, Filtering/Sorting.
**Key sub-questions:**
1. What calculations or transformations?
2. Trigger? (user action, schedule, event?)
3. Real-time or background?
4. AI/ML components? What do they do?
5. What happens if processing fails?

## Category D: Data Output
**What it is:** How data is displayed or delivered.
**Sub-types:** Lists/Tables, Charts/Graphs, Maps, Timelines, Kanban/Board, Export, Real-time Feeds.
**Key sub-questions:**
1. Main views/pages users see?
2. List views? Columns? Sortable? Filterable?
3. Dashboard/analytics views? What metrics?
4. Export needed? What formats?
5. Real-time updating? (live counters, feeds?)
6. Pagination? Infinite scroll?

## Category E: Authentication
**What it is:** How users prove who they are.
**Sub-types:** Email/Password, OAuth/Social, SSO, MFA, Magic Link, API Keys, Session Management.
**Key sub-questions:**
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers?
3. MFA required?
4. Session management? (JWT, cookies?)
5. Password requirements? Reset flow?
6. Account deletion? What happens to data?

## Category F: Authorization
**What it is:** What users are allowed to do.
**Sub-types:** RBAC, ABAC, Resource Ownership, Multi-tenancy, Feature Flags, Rate Limiting.
**Key sub-questions:**
1. What roles exist? (admin, user, moderator?)
2. What can each role do?
3. Data isolated per user? Per org/team?
4. Subscription tiers that unlock features?
5. Can users share access? (invite, transfer?)
6. Row-level security?

## Category G: Communication
**What it is:** System-to-user and user-to-user communication.
**Sub-types:** Email, Push Notifications, In-App Notifications, SMS, Chat/Messaging, Webhooks, Activity Feeds.
**Key sub-questions:**
1. What events trigger notifications?
2. Which channels? (email, push, in-app?)
3. User notification preferences configurable?
4. Real-time chat needed? (1:1, group, channels?)
5. Webhooks to external services?

## Category H: Integration
**What it is:** Connections to external services.
**Sub-types:** REST/GraphQL Consumption, REST/GraphQL Exposure, Web Scraping, Payment Gateways, File/Data Sync, Social Media, Email Services.
**Key sub-questions:**
1. Which external services?
2. What data sent/received?
3. What happens when external service is down?
4. Does the app expose its own API?
5. Payment processor? Which one? What flows?

## Category I: Workflow
**What it is:** Multi-step processes and automation.
**Sub-types:** State Machines, Approval Flows, Cron Jobs, Queues, Event Triggers, Wizards/Multi-step, Retry/Recovery.
**Key sub-questions:**
1. Multi-step processes? What states?
2. What triggers state transitions?
3. Time-based triggers? (expire, remind?)
4. Scheduled/automated tasks?
5. Undo/rollback capability?

## Category J: Search & Discovery
**What it is:** How users find things.
**Sub-types:** Full-text Search, Faceted Search, Autocomplete, Recommendations, Tags/Categories, Favorites, Recent/History.
**Key sub-questions:**
1. What is searchable?
2. Full-text or just field-based filtering?
3. Filters? (category, date, status?)
4. Autocomplete needed?
5. Recommendations? Based on what?
6. Browse/explore mode?

## Category K: Collaboration
**What it is:** How users interact with each other.
**Sub-types:** Comments, @Mentions, Sharing, Co-editing, Reactions, Following, Profiles.
**Key sub-questions:**
1. Can users comment? On what?
2. @mentioning?
3. Share content? How? (link, invite, public?)
4. Real-time co-editing?
5. Reactions/votes? (likes, upvotes?)
6. User profiles? What info shown?

## Category L: Monetization
**What it is:** How the app makes money.
**Sub-types:** Subscriptions, One-time Purchase, Freemium/Trials, Usage-based, Marketplace/Commission, Invoicing, Refunds.
**Key sub-questions:**
1. Revenue model? (subscription, one-time, freemium, marketplace?)
2. Plans/tiers? What does each include?
3. Free tier? Trial period?
4. Payment processor?
5. Refund handling?
6. Team/org billing?

## Category M: Admin/Ops
**What it is:** Back-office management tools.
**Sub-types:** Admin Dashboard, User Management, Content Moderation, Feature Flags, Analytics, Configuration.
**Key sub-questions:**
1. Admin panel? What can admins do?
2. User management? (view, edit, suspend?)
3. Content moderation?
4. Analytics dashboards? What metrics?
5. Audit log?

## Category N: Infrastructure
**What it is:** System-level concerns.
**Sub-types:** Caching, DB Migrations, Circuit Breakers, Auto-scaling, Logging, Monitoring/APM, CI/CD.
**Key sub-questions:**
1. Where hosted? (cloud, serverless, self-hosted?)
2. Expected traffic?
3. Caching strategy needed?
4. Deployment method?
5. Monitoring/alerting needs?
6. Compliance requirements?

## Quick Signal Map

| User Says | Primary | Secondary |
|-----------|---------|-----------|
| "sign up and log in" | E | F |
| "sends an email when..." | G | I |
| "search for..." | J | D |
| "scrapes data from websites" | H | C |
| "subscription plan" | L | F |
| "upload files" | A | B |
| "generates a PDF" | C | D |
| "dashboard showing..." | D | M |
| "orders go through stages" | I | B |
| "comment and like" | K | G |
| "admins can ban users" | M | F |
| "handle 10K users" | N | B |
| "share with a link" | K | F |
| "calculates a score" | C | D |
| "chat feature" | G | K |


---

## REFERENCE: question-templates

# Question Templates for Gap Analysis

> Reusable patterns for generating adaptive gap questions.
> Fill in {placeholders} with app-specific context from raw_input and platform_profile.

## Pattern 1: REQUIRED Gap (Archetype expects it, user didn't mention it)

**Template:**
> "{Archetype} apps typically need {category_name}. {Specific_need_description}. How will yours handle this? ({option_1}, {option_2}, {option_3}, or something else?)"

**Examples:**
- "Marketplace apps need payment processing. How will buyers pay sellers? (Stripe, PayPal, direct bank transfer, or something else?)"
- "SaaS products need subscription billing. Will you offer plan tiers? (free/pro/team, single paid plan, usage-based, or something else?)"
- "Social platforms need content moderation. How will you handle inappropriate posts? (automated filters, user reports + manual review, AI moderation, or something else?)"

## Pattern 2: OPTIONAL Inquiry (Archetype says optional, check if needed)

**Template:**
> "Does your app need {category_name}? For example, {example_relevant_to_their_app}."

**Examples:**
- "Does your app need search? For example, letting users search across all their tasks by keyword or filter by status?"
- "Does your app need integrations? For example, syncing tasks with Google Calendar or importing from Trello?"
- "Does your app need a notification system? For example, email alerts when a due date is approaching?"

## Pattern 3: Sub-Type Specifics (Category identified but details missing)

**Template:**
> "You mentioned {what_user_said}. {Specific_sub_question}? ({option_1}, {option_2}, or {option_3}?)"

**Examples:**
- "You mentioned users can upload photos. What file types and size limits? (JPEG/PNG only up to 5MB, any image type up to 20MB, or also video files?)"
- "You mentioned email login. Will you also support social login? (Google only, Google + GitHub, Google + Apple, or email-only?)"
- "You mentioned a dashboard with charts. What specific metrics? (task completion rates, team productivity, time tracking, or something else?)"

## Pattern 4: Stack-Aware Question (Use platform_profile for context)

**Template:**
> "Since you're using {tech_stack_component}, {stack_specific_question}? ({stack_option_1}, {stack_option_2}?)"

**Stack-specific examples by platform:**

### Supabase
- "Since you're using Supabase, will you use Row Level Security to isolate user data, or handle authorization in your application code?"
- "Since you're using Supabase, will you use Supabase Auth for login, or a separate auth provider?"
- "Since you're using Supabase, will you use Edge Functions for server-side logic, or a separate API server?"

### Firebase
- "Since you're using Firebase, will you use Firestore security rules for authorization, or Cloud Functions middleware?"
- "Since you're using Firebase, will file uploads go to Cloud Storage with Firebase SDK, or a separate storage service?"
- "Since you're using Firebase, will you use Firebase Hosting, or deploy elsewhere?"

### Next.js / Vercel
- "Since you're using Next.js, will data fetching happen server-side (RSC), client-side (SWR/React Query), or a mix?"
- "Since you're deploying to Vercel, will you use Vercel's built-in analytics and edge functions?"

### Flutter / Mobile
- "Since you're building a mobile app, which platforms? (iOS only, Android only, or both?)"
- "Since you're using Flutter, will you use Firebase for the backend, Supabase, or a custom API?"

### Generic (no specific stack)
- "Where do you plan to host this? (Vercel, AWS, self-hosted, or undecided?)"
- "Do you have a preference for the database? (PostgreSQL, MySQL, MongoDB, or whatever fits best?)"

## Pattern 5: Contradiction Clarifier

**Template:**
> "You mentioned '{statement_1}' but also '{statement_2}'. Which takes priority? ({interpretation_1}, {interpretation_2}, or both in different contexts?)"

**Examples:**
- "You mentioned 'it should be simple' but also listed 12 features. Should we prioritize a minimal MVP first, or include all features from the start?"
- "You mentioned 'free for everyone' but also 'team workspaces with billing'. Will there be a free tier alongside a paid team plan, or is the entire app free?"

## Pattern 6: Developer's Choice Confirmation

**Template:**
> "For {category_name}, the standard approach for {archetype} apps is {default_approach}. Works for you, or do you have something different in mind?"

**Examples:**
- "For data storage, the standard approach for CRUD apps is a relational database (PostgreSQL). Works for you, or do you need something different?"
- "For session management, the standard approach is JWT with refresh tokens. Works for you?"

## Grouping Rules

When presenting questions, group by topic area:

1. **Core functionality gaps** — REQUIRED categories missing (highest priority)
2. **Feature questions** — OPTIONAL categories to confirm/deny
3. **Implementation specifics** — Sub-type details for identified categories
4. **Stack-specific** — Platform-tailored questions

Within each group, order from most impactful to least. Lead with the question whose answer affects the most downstream decisions (e.g., monetization model before payment processor details).

## Anti-Patterns (NEVER do these)

- "Tell me more about your app." (too vague)
- "What about authentication?" (too broad — offer specific options)
- "Have you thought about scalability?" (generic, not actionable)
- "What's your budget?" (not a mechanism question)
- "Can you describe the user flow?" (Stage 3's job, not Stage 2)
- Asking about something the user already clearly described in raw_input.
- Asking the same category twice in different questions.
- Asking more than 15 questions regardless of input length.


---

## REFERENCE: App Archetype Library

# App Archetype Library

> Used during Stage 2 (Gap Analysis) to reduce questioning overhead.
> Match the user's description to an archetype, load defaults, ask only about gaps.
>
> 8 archetypes x 14 mechanism categories (A-N) = pre-mapped defaults for fast gap analysis.
>
> **Relationship to pipeline:** Stage 2 (Gap Analysis) reads this library to identify which archetype(s) the user's idea matches. REQUIRED categories get auto-filled with default sub-types. OPTIONAL categories get one targeted question each. UNLIKELY categories are skipped unless the user specifically mentioned them.

---

## Archetype 1: Dashboard App

**One-line description:** An app that displays data, metrics, and analytics in visual layouts where users primarily read information with limited write operations like filters and date ranges.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Dashboards need filter controls, date range pickers, and configuration forms |
| B | Data Storage | REQUIRED | Relational DB or API | Data has to come from somewhere — either a local database or external API endpoints |
| C | Data Processing | REQUIRED | Calculations | Aggregations, statistics, and metric computations are the core value of a dashboard |
| D | Data Output | REQUIRED | Charts/Graphs | Visualizing data is the entire purpose of a dashboard app |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to see their personalized data |
| F | Authorization | OPTIONAL | — | Some dashboards have role-based views (admin vs viewer), but many are single-role |
| G | Communication | OPTIONAL | — | Scheduled report emails or threshold alerts are common but not universal |
| H | Integration | OPTIONAL | — | Many dashboards pull data from external APIs, but some use only local data |
| I | Workflow | UNLIKELY | — | Dashboards are read-heavy; they display results of processes, not manage processes |
| J | Search & Discovery | OPTIONAL | — | Filtering and searching through data points is common in data-heavy dashboards |
| K | Collaboration | UNLIKELY | — | Dashboards are typically solo viewing experiences, not collaborative |
| L | Monetization | UNLIKELY | — | Most dashboards are internal tools or features within a larger product, not standalone paid products |
| M | Admin/Ops | OPTIONAL | — | Some dashboards have admin settings for data sources or user management |
| N | Infrastructure | OPTIONAL | — | Caching matters for performance with large datasets, but not critical for MVP |

### Standard Pages

- **Overview Dashboard** — Primary view showing key metrics, KPI cards, and summary charts
- **Analytics Detail** — Drill-down view for a specific metric category with granular charts and data tables
- **Data Explorer** — Table view with sortable columns, filters, and search for raw data inspection
- **Login / Signup** — Authentication page with email/password or OAuth options
- **Settings & Preferences** — User preferences for date ranges, default views, notification thresholds
- **Report Builder** — Configure and export custom reports as PDF or CSV

### Example Apps

- **Google Analytics** — The canonical dashboard app: metrics, charts, date ranges, drill-downs, and export
- **Shopify Admin Dashboard** — E-commerce metrics (sales, orders, traffic) in visual layouts with filter controls
- **Datadog** — Infrastructure monitoring dashboard with real-time charts, alerts, and configurable views

---

## Archetype 2: Marketplace

**One-line description:** A two-sided platform connecting buyers and sellers (or providers and consumers) with listings, search, transactions, reviews, and trust mechanisms.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Sellers create listings with structured forms (title, description, price, images) |
| B | Data Storage | REQUIRED | Relational DB | Listings, users, transactions, and reviews form a heavily relational data model |
| C | Data Processing | REQUIRED | Validation | Pricing calculations, availability checks, matching algorithms, and commission computation |
| D | Data Output | REQUIRED | Lists/Tables | Browsing listings, search results, and order history are core read operations |
| E | Authentication | REQUIRED | Email/Password + OAuth | Both buyers and sellers need accounts; social login reduces signup friction |
| F | Authorization | REQUIRED | RBAC | Distinct buyer, seller, and admin roles with different permissions and views |
| G | Communication | REQUIRED | In-App Notifications | Order updates, new messages, review requests — both sides need real-time alerts |
| H | Integration | REQUIRED | Payment Gateways | Transactions between buyers and sellers require Stripe/PayPal with escrow or split payments |
| I | Workflow | REQUIRED | State Machines | Orders flow through states: pending → paid → shipped → delivered → reviewed |
| J | Search & Discovery | REQUIRED | Faceted Search | Finding products/services by category, price, location, rating is a core user action |
| K | Collaboration | UNLIKELY | — | Reviews/ratings are feedback, not collaboration; co-editing, @mentions, and following are not marketplace mechanics |
| L | Monetization | REQUIRED | Marketplace/Commission | Platform takes a percentage of each transaction — this is the business model |
| M | Admin/Ops | REQUIRED | Content Moderation | Dispute resolution, listing approval, seller verification, and fraud detection are essential |
| N | Infrastructure | UNLIKELY | — | CDN and caching help at scale but MVP marketplaces run on basic hosting without special infra |

### Standard Pages

- **Home / Browse** — Featured listings, categories, and promotional sections
- **Search Results** — Filtered and sorted listings with faceted search sidebar
- **Listing Detail** — Full listing information with images, description, price, seller info, and reviews
- **Create / Edit Listing** — Multi-step form for sellers to create or update listings
- **Shopping Cart / Checkout** — Cart management and payment flow for buyers
- **Order Management** — Order history and status tracking for both buyers and sellers
- **Seller Dashboard** — Sales metrics, active listings, earnings, and payout information
- **User Profile** — Public profile showing ratings, reviews, and listing history

### Example Apps

- **Airbnb** — Two-sided marketplace connecting hosts and guests with listings, search, booking workflow, reviews, and platform commission
- **Etsy** — Seller storefronts, product search, cart/checkout, reviews, and transaction-based monetization
- **Uber** — Provider-consumer matching with real-time availability, pricing, payment processing, and rating system

---

## Archetype 3: Chat / Messaging App

**One-line description:** A real-time communication app where users send and receive messages in 1:1, group, or channel-based conversations with presence indicators and notifications.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Message composer is a text input with optional rich formatting, emoji, and attachments |
| B | Data Storage | REQUIRED | NoSQL/Document | Messages are append-heavy, nested in conversations — document store fits naturally |
| C | Data Processing | OPTIONAL | — | Media processing (image resizing, link previews) and message formatting are common but not universal |
| D | Data Output | REQUIRED | Real-time Feeds | Message streams update live as new messages arrive — this is the core display pattern |
| E | Authentication | REQUIRED | Email/Password | Users need accounts tied to their identity for messaging |
| F | Authorization | OPTIONAL | — | Channel permissions and admin roles exist in some chat apps but not all (1:1 apps skip this) |
| G | Communication | REQUIRED | Chat/Messaging + Push Notifications | Real-time messaging IS the app; push notifications alert users when they are not in the app |
| H | Integration | OPTIONAL | — | Bots, webhooks, and external service connections are common in team chat, rare in personal chat |
| I | Workflow | UNLIKELY | — | Messages are sent and received — there are no multi-step state machines in core messaging |
| J | Search & Discovery | OPTIONAL | — | Message search and people/channel discovery are common in larger chat apps |
| K | Collaboration | REQUIRED | Profiles | User presence (online/offline/away), status messages, and contact lists are core to messaging |
| L | Monetization | UNLIKELY | — | Most chat apps are free for users; monetization (if any) is enterprise pricing, not per-message |
| M | Admin/Ops | OPTIONAL | — | Team/workspace administration exists in business chat apps but not personal messaging |
| N | Infrastructure | OPTIONAL | — | WebSocket infrastructure and message caching matter for performance but are implementation details |

### Standard Pages

- **Login / Signup** — Authentication with phone number or email verification
- **Conversation List (Inbox)** — All active conversations sorted by recency with unread indicators
- **Chat Room / Conversation** — Message thread with real-time updates, typing indicators, and message input
- **Contact / People List** — User directory for starting new conversations or adding to groups
- **User Profile** — Avatar, display name, status, and contact information
- **Settings** — Notification preferences, privacy controls, account management

### Example Apps

- **WhatsApp** — 1:1 and group messaging with end-to-end encryption, media sharing, and presence indicators
- **Slack** — Channel-based team messaging with threads, search, integrations, and workspace administration
- **Discord** — Server/channel structure with voice chat, roles, and bot ecosystem for communities

---

## Archetype 4: CRUD / Tool

**One-line description:** A utility app focused on creating, reading, updating, and deleting structured data — task managers, note apps, inventory trackers, CRM tools, and spreadsheet-like apps.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Creating and editing records through structured forms is the primary user action |
| B | Data Storage | REQUIRED | Relational DB | Structured data with defined fields and relationships (tasks, contacts, inventory items) |
| C | Data Processing | REQUIRED | Validation | Input validation, business rule checks, and data consistency enforcement on every save |
| D | Data Output | REQUIRED | Lists/Tables | The main view is always a list or table of records with sorting and filtering |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to store and retrieve their data |
| F | Authorization | OPTIONAL | — | Resource ownership (users see only their own data) is common; team roles are less common |
| G | Communication | OPTIONAL | — | Email notifications for deadlines or changes are nice-to-have, not core |
| H | Integration | OPTIONAL | — | Import/export and API connections to other tools are common in mature CRUD apps |
| I | Workflow | OPTIONAL | — | Some tools have status workflows (to-do → in progress → done) but many are flat CRUD |
| J | Search & Discovery | OPTIONAL | — | Searching and filtering records becomes important as data volume grows |
| K | Collaboration | OPTIONAL | — | Sharing records and team collaboration exist in some tools but many are single-user |
| L | Monetization | UNLIKELY | — | Many CRUD tools are internal/personal utilities, not standalone paid products |
| M | Admin/Ops | UNLIKELY | — | Small-team tools rarely need admin panels or content moderation |
| N | Infrastructure | UNLIKELY | — | Simple CRUD apps run on basic hosting with no special infrastructure needs |

### Standard Pages

- **Login / Signup** — Authentication page
- **Item List** — Main view showing all records in a table or card grid with sort/filter controls
- **Item Detail** — Full record view with all fields, history, and related data
- **Create / Edit Form** — Form for creating new records or editing existing ones
- **Dashboard / Overview** — Summary statistics (total items, items by status, recent activity)
- **Settings** — User preferences, data export options, account management

### Example Apps

- **Todoist** — Task management CRUD with projects, priorities, due dates, and status tracking
- **Airtable** — Spreadsheet-database hybrid for structured data with views, filters, and formulas
- **Google Keep** — Minimal note-taking CRUD with labels, colors, and search

---

## Archetype 5: Social Platform

**One-line description:** An app centered on user-generated content, social graphs (following/followers), algorithmic or chronological feeds, and engagement mechanics like likes, comments, and shares.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms + File Upload | Users create posts with text, images, and video — both form fields and media upload |
| B | Data Storage | REQUIRED | Relational DB + Blob Storage | User data and relationships in a relational DB; media files in blob/object storage |
| C | Data Processing | REQUIRED | Filtering/Sorting | Feed ranking, content recommendations, and trending calculations are core to engagement |
| D | Data Output | REQUIRED | Real-time Feeds | The social feed — an infinite-scroll stream of content from followed users and recommendations |
| E | Authentication | REQUIRED | OAuth/Social | Social login (Google, Apple) is natural for social platforms and reduces signup friction |
| F | Authorization | REQUIRED | Resource Ownership | Users own their posts; privacy settings control who sees what (public, friends-only, private) |
| G | Communication | REQUIRED | In-App Notifications | "Someone liked your post" and "New follower" notifications are essential for engagement loops |
| H | Integration | OPTIONAL | — | Social sharing to other platforms and link embeds are common but not required for core function |
| I | Workflow | UNLIKELY | — | Social platforms are event-driven (post, like, comment), not process-driven with state machines |
| J | Search & Discovery | REQUIRED | Full-text Search | Finding people, hashtags, and content is a core navigation mechanism |
| K | Collaboration | REQUIRED | Comments + Reactions + Following | Likes, comments, shares, and follow relationships ARE the social platform |
| L | Monetization | UNLIKELY | — | Most social platforms defer monetization; MVP launches are free and ad-free |
| M | Admin/Ops | REQUIRED | Content Moderation | User-generated content requires moderation for spam, harassment, and policy violations |
| N | Infrastructure | OPTIONAL | — | CDN for media delivery and caching for feeds help at scale but are not MVP-critical |

### Standard Pages

- **Login / Signup** — Social login and email registration
- **Feed (Home Timeline)** — Scrollable stream of posts from followed users and recommendations
- **User Profile** — Bio, avatar, post history, follower/following counts, and follow button
- **Post Detail** — Single post with full comments thread and engagement buttons
- **Discover / Explore** — Trending content, recommended users, hashtag browsing
- **Notifications** — Activity feed showing likes, comments, follows, and mentions
- **Create Post** — Composer for text, images, video with preview
- **Settings** — Account, privacy, notification preferences, blocked users

### Example Apps

- **Instagram** — Photo/video sharing with feed, stories, explore, likes, comments, and follower graph
- **Twitter/X** — Short-form text posts with retweets, likes, threads, and trending topics
- **Reddit** — Community-based content with upvotes, comments, subreddits, and content discovery

---

## Archetype 6: Wizard / Onboarding Flow

**One-line description:** A step-by-step guided process that collects information or walks users through a setup, with linear or branching progression, validation at each step, and a final summary or confirmation.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Multi-step form input is the entire core mechanic — each step collects specific data |
| B | Data Storage | REQUIRED | Relational DB | Collected data must persist, including partial progress for resume-later capability |
| C | Data Processing | REQUIRED | Validation | Each step validates before allowing progression; final step may trigger calculations or decisions |
| D | Data Output | REQUIRED | Lists/Tables | Summary/review screen shows all collected data before final submission |
| E | Authentication | OPTIONAL | — | Some wizards are part of signup (pre-auth); others require login first — depends on context |
| F | Authorization | UNLIKELY | — | Wizards are typically single-path with no role differentiation |
| G | Communication | OPTIONAL | — | Confirmation emails after completion are common but not part of the core wizard flow |
| H | Integration | OPTIONAL | — | Wizard results often get sent to external systems (CRM, email service, payment processor) |
| I | Workflow | REQUIRED | Wizards/Multi-step | Step-by-step progression with branching logic IS a workflow by definition |
| J | Search & Discovery | UNLIKELY | — | Linear guided processes have no search — users are led through a fixed path |
| K | Collaboration | UNLIKELY | — | Wizards are solo experiences — one user filling out one flow |
| L | Monetization | UNLIKELY | — | Wizards collect data or configure settings; they do not sell anything directly |
| M | Admin/Ops | UNLIKELY | — | Simple flow with no admin layer needed |
| N | Infrastructure | UNLIKELY | — | Wizards are lightweight with no special infrastructure demands |

### Standard Pages

- **Welcome / Intro Screen** — Explains what the wizard does and what information will be needed
- **Step 1-N (Data Collection Steps)** — Each step focuses on one category of information with validation
- **Conditional Branch Screen** — Optional path that appears based on previous answers
- **Review / Summary** — Shows all collected data in a readable format for user confirmation
- **Confirmation / Success** — Final screen confirming submission with next steps or results

### Example Apps

- **TurboTax** — Step-by-step tax filing wizard that collects income, deductions, and credits through guided questions
- **Typeform** — Conversational form builder where each question is one step with smooth transitions
- **Wix Site Builder Setup** — Guided onboarding that asks about business type, goals, and preferences to generate a starter site

---

## Archetype 7: Landing Page

**One-line description:** A marketing or informational page focused on conversion with static content, CTAs, signup forms, pricing tables, and social proof — minimal backend logic.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | OPTIONAL | — | Signup forms and contact forms are common but not every landing page has them |
| B | Data Storage | UNLIKELY | — | Landing pages are mostly static; at most they store form submissions or email signups |
| C | Data Processing | UNLIKELY | — | Static content pages have no data processing requirements |
| D | Data Output | REQUIRED | Lists/Tables | Feature comparison tables, pricing tiers, testimonial cards — structured content display |
| E | Authentication | UNLIKELY | — | Landing pages are public; authentication belongs to the product they link to |
| F | Authorization | UNLIKELY | — | Everyone sees the same page — no roles or permissions |
| G | Communication | OPTIONAL | — | Newsletter signup and email capture are common conversion tactics |
| H | Integration | OPTIONAL | — | Analytics (Google Analytics), email services (Mailchimp), and CRM integrations are common |
| I | Workflow | UNLIKELY | — | Static pages have no multi-step processes |
| J | Search & Discovery | UNLIKELY | — | Landing pages are small enough that search is unnecessary |
| K | Collaboration | UNLIKELY | — | Landing pages are not collaborative experiences |
| L | Monetization | UNLIKELY | — | The landing page drives users TO a monetized product — it does not monetize itself |
| M | Admin/Ops | UNLIKELY | — | Static content with no admin layer needed |
| N | Infrastructure | OPTIONAL | — | CDN and caching improve load speed, which directly affects conversion rates |

### Standard Pages

- **Hero / Home** — Primary landing section with headline, value proposition, and main CTA
- **Features / Benefits** — Detailed breakdown of what the product offers with icons or illustrations
- **Pricing** — Plan comparison table with feature lists and signup buttons per tier
- **Testimonials / Social Proof** — Customer quotes, logos, case study snippets, and trust badges
- **FAQ** — Common questions and answers to reduce signup friction
- **Contact / Signup** — Form for leads, demo requests, or newsletter subscription

### Example Apps

- **Stripe's Homepage** — Clean, conversion-focused landing with product explanation, feature sections, pricing, and developer-friendly CTAs
- **Linear's Homepage** — Minimal, fast landing page with feature highlights, social proof, and clear signup flow
- **Notion's Homepage** — Template-rich landing page with use case sections, pricing comparison, and customer logos

---

## Archetype 8: SaaS Product

**One-line description:** A subscription-based software product with user accounts, feature tiers, team management, billing, and an admin layer — typically combines CRUD + Dashboard mechanics with a unique value proposition.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | User data entry, settings configuration, and content creation forms |
| B | Data Storage | REQUIRED | Relational DB | User data, subscription records, team structures, and product-specific data |
| C | Data Processing | REQUIRED | Calculations | Business logic specific to the SaaS value prop plus usage metering and billing calculations |
| D | Data Output | REQUIRED | Lists/Tables + Charts | Product-specific views plus usage dashboards and account overview |
| E | Authentication | REQUIRED | Email/Password + OAuth | Multiple auth methods reduce friction; enterprise customers may need SSO |
| F | Authorization | REQUIRED | RBAC + Feature Flags | Subscription tiers gate features; team roles control access within organizations |
| G | Communication | REQUIRED | Email | Transactional emails (welcome, invoice, password reset), onboarding sequences, and product updates |
| H | Integration | OPTIONAL | — | Many SaaS products integrate with other tools, but the core product may stand alone |
| I | Workflow | UNLIKELY | — | Default SaaS products are CRUD-based; complex state machines and approval flows are feature-specific, not archetype-standard |
| J | Search & Discovery | OPTIONAL | — | Depends on data volume — products with many records need search, simple tools may not |
| K | Collaboration | OPTIONAL | — | Team features (shared workspaces, comments, mentions) are common in B2B SaaS but not universal |
| L | Monetization | REQUIRED | Subscriptions | Monthly/annual billing with plan tiers is the defining characteristic of SaaS |
| M | Admin/Ops | REQUIRED | Admin Dashboard | System health, user management, subscription analytics, and feature flag controls |
| N | Infrastructure | UNLIKELY | — | Monitoring, auto-scaling, and CI/CD become important at scale but MVP SaaS runs on basic hosting |

### Standard Pages

- **Marketing / Landing Page** — Public-facing page explaining the product with pricing and signup CTA
- **Login / Signup** — Multi-method authentication with social login and SSO options
- **Main Workspace / Dashboard** — The core product experience where users spend most of their time
- **Account Settings** — Profile, password, notification preferences, and connected accounts
- **Billing / Subscription** — Current plan, usage metrics, payment method, invoice history, and upgrade options
- **Team Management** — Invite members, assign roles, manage permissions within an organization
- **Admin Panel** — Internal dashboard for system operators showing user metrics, health, and config

### Example Apps

- **Figma** — Design tool SaaS with team workspaces, subscription tiers (free/pro/org), real-time collaboration, and admin controls
- **Notion** — Workspace SaaS combining notes, databases, and docs with team plans, member management, and usage-based features
- **Canva** — Design SaaS with free/pro/team tiers, template marketplace, team brand kits, and asset management

---

## How to Use This Library

These instructions are for the Stage 2 (Gap Analysis) agent. Follow them mechanically.

### Step 1: Match

Read the user's raw idea description from Stage 1. Identify which archetype(s) it most closely matches.

**Matching rules:**
- An app can match MULTIPLE archetypes. Example: "a marketplace with analytics" = Marketplace + Dashboard.
- Match based on the PRIMARY user action described:
  - User views data/metrics → **Dashboard**
  - User buys/sells between two parties → **Marketplace**
  - User sends/receives messages in real time → **Chat / Messaging**
  - User creates/edits/deletes records → **CRUD / Tool**
  - User posts content and follows other users → **Social Platform**
  - User walks through a step-by-step process → **Wizard / Onboarding**
  - The output is a marketing/info page → **Landing Page**
  - User pays a subscription for ongoing software access → **SaaS Product**
- If the description mentions subscription billing or team management alongside another archetype, ALSO match **SaaS Product** and union the mechanism maps.
- If multiple archetypes match, union all REQUIRED categories from each. A category that is REQUIRED in ANY matched archetype becomes REQUIRED in the combined map.

### Step 2: Load Defaults

For the matched archetype(s), load all REQUIRED mechanism categories with their default sub-types. These are pre-filled into the context packet.

**Rules:**
- Do NOT ask the user about REQUIRED categories unless their description explicitly contradicts the default. Example: if their Dashboard description says "no user accounts needed," then E (Authentication) drops from REQUIRED to inapplicable despite the archetype default.
- If multiple archetypes matched, use the most specific default sub-type from whichever archetype is more relevant. Example: if both Dashboard (Forms) and Marketplace (Forms) mark A as REQUIRED, keep "Forms" as the default.

### Step 3: Ask About OPTIONAL

For each OPTIONAL category in the combined map, ask the user ONE targeted question. Use this format:

> "Does your app need **[category name]**? For example, [archetype-specific example relevant to their idea]."

**Rules:**
- Phrase the example in terms of THEIR app, not generic terms. Example: for a recipe-sharing app (Social archetype), ask "Does your app need **monetization**? For example, a premium tier that unlocks exclusive recipes?" — not "Does your app need monetization? For example, subscriptions."
- Ask all OPTIONAL questions in a single batch, not one at a time.
- If the user already mentioned something that maps to an OPTIONAL category in their rant, skip the question — mark it as needed and move to sub-questions.

### Step 4: Skip UNLIKELY

Do NOT ask about UNLIKELY categories. Period.

**Exception:** If the user's Stage 1 description specifically mentions something that maps to an UNLIKELY category, override the UNLIKELY classification and treat it as REQUIRED. Example: if a Dashboard user says "and it should have a chat feature," that maps to G (Communication) and K (Collaboration), which are UNLIKELY for Dashboards. Override them to REQUIRED and ask sub-questions.

### Step 5: Deep-Dive on Mentioned

For every category that is active (either REQUIRED by archetype, confirmed OPTIONAL by user, or mentioned in the rant), ask the sub-questions from the `mechanism-identification-framework.md` to get specifics.

**Rules:**
- For REQUIRED categories with default sub-types, start with a confirming question: "For data storage, the standard approach is a relational database. Does that work, or do you need something different?"
- For user-confirmed OPTIONAL categories, ask the full sub-question set.
- For rant-mentioned categories, ask only the sub-questions that the rant didn't already answer.

### Step 6: Handle No-Match

If the user's idea does not match ANY archetype:

1. State: "Your app doesn't fit a standard archetype, so I need to ask about all mechanism categories."
2. Fall back to asking about ALL 14 categories (A-N) one by one using the standard questions from the mechanism identification framework.
3. Flag `archetype_match: "none"` in the context packet so downstream stages know this was a full-coverage gap analysis.

### Step 7: Handle Hybrid

If the user's idea matches 2 or more archetypes:

1. State: "Your app looks like a combination of **[Archetype A]** and **[Archetype B]**. I'm loading the standard requirements for both."
2. Union the REQUIRED categories (anything REQUIRED in either archetype is REQUIRED in the combined map).
3. For categories where both archetypes have different default sub-types, ask: "For [category], [Archetype A] apps typically use [sub-type A] while [Archetype B] apps typically use [sub-type B]. Which fits your app better?"
4. For OPTIONAL categories, ask about any that are OPTIONAL in either archetype (even if UNLIKELY in the other).
5. Flag `archetype_match: ["Archetype A", "Archetype B"]` in the context packet.

---

## Quick Reference: Classification Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY |
|-----------|----------|----------|----------|
| Dashboard App | 5 (A, B, C, D, E) | 6 (F, G, H, J, M, N) | 3 (I, K, L) |
| Marketplace | 12 (A, B, C, D, E, F, G, H, I, J, L, M) | 0 | 2 (K, N) |
| Chat / Messaging | 6 (A, B, D, E, G, K) | 6 (C, F, H, J, M, N) | 2 (I, L) |
| CRUD / Tool | 5 (A, B, C, D, E) | 6 (F, G, H, I, J, K) | 3 (L, M, N) |
| Social Platform | 10 (A, B, C, D, E, F, G, J, K, M) | 2 (H, N) | 2 (I, L) |
| Wizard / Onboarding | 5 (A, B, C, D, I) | 3 (E, G, H) | 6 (F, J, K, L, M, N) |
| Landing Page | 1 (D) | 4 (A, G, H, N) | 9 (B, C, E, F, I, J, K, L, M) |
| SaaS Product | 9 (A, B, C, D, E, F, G, L, M) | 3 (H, J, K) | 2 (I, N) |

> **Note on Marketplace having 0 OPTIONAL:** Marketplaces are inherently complex — every mechanism is either definitely needed (REQUIRED) or genuinely irrelevant (UNLIKELY). This means the gap analysis agent asks zero OPTIONAL questions for a pure marketplace, but has 12 REQUIRED categories to deep-dive on. Expect a longer conversation.

---

## Archetype Complexity Ranking

For agent planning and user expectation-setting:

| Rank | Archetype | Active Categories | Build Complexity |
|------|-----------|-------------------|-----------------|
| 1 | Landing Page | 1 REQUIRED + 4 OPTIONAL = ~3-5 active | Low |
| 2 | Wizard / Onboarding | 5 REQUIRED + 3 OPTIONAL = ~6-7 active | Low-Medium |
| 3 | CRUD / Tool | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 4 | Dashboard App | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 5 | Chat / Messaging | 6 REQUIRED + 6 OPTIONAL = ~8-10 active | Medium-High |
| 6 | Social Platform | 10 REQUIRED + 2 OPTIONAL = ~10-11 active | High |
| 7 | SaaS Product | 9 REQUIRED + 3 OPTIONAL = ~10-11 active | High |
| 8 | Marketplace | 12 REQUIRED + 0 OPTIONAL = ~12 active | Very High |


---

## REFERENCE: Mechanism Identification Framework

# Mechanism Identification Framework

> The "Periodic Table of App Mechanisms" — used during Stage 2 (Gap Analysis) and Stage 4 (Mechanism Extraction) to systematically break down what an app DOES.
>
> When someone describes their app, map their description to these categories. Then ask the sub-questions for each identified mechanism. For categories they DIDN'T mention, ask if their app needs them.

---

## How to Use This

1. **Listen to the user's description** (rant, brain dump, whatever)
2. **Tag every feature/action they describe** with a mechanism category (A-N)
3. **For each tagged mechanism**, ask the sub-questions below
4. **For categories NOT mentioned**, ask: "Does your app need [category]?"
5. **Output**: A complete mechanism map with answers for each active category

---

## Category A: Data Input

**What it is:** How data enters the system from users or external sources.

| Sub-type | Examples |
|----------|----------|
| Forms | Text inputs, dropdowns, date pickers, multi-step wizards |
| File Upload | Images, documents, video, bulk CSV import |
| Voice/Audio | Speech-to-text, voice commands, audio recording |
| Camera/OCR | Photo capture, document scanning, barcode reading |
| Drag-and-Drop | Reordering lists, kanban boards, file drop zones |
| Sensors/IoT | GPS location, accelerometer, biometric input |
| Copy/Paste & Import | Clipboard, URL parsing, data import from other apps |

### Sub-Questions
1. What types of data do users input? (text, numbers, dates, files, rich text?)
2. Are there multi-step forms or wizards?
3. What file types are accepted? Size limits?
4. Is real-time validation needed (as-they-type) or on-submit?
5. Do users input data on behalf of others (admin entry)?
6. Is bulk input needed (CSV import, batch creation)?
7. Are there draft/autosave requirements?

---

## Category B: Data Storage

**What it is:** How and where data persists.

| Sub-type | Examples |
|----------|----------|
| Relational DB | PostgreSQL, MySQL, SQLite — structured, normalized |
| NoSQL/Document | MongoDB, Firestore — flexible schema, nested documents |
| Blob/File Storage | S3, Cloud Storage — media, attachments, exports |
| Cache Layer | Redis, Memcached — hot data, session state |
| Search Index | Elasticsearch, Algolia, pgvector — fast text/vector search |
| Audit Trail | Immutable log of all changes for compliance |

### Sub-Questions
1. What are the main entities/objects? (users, products, orders, etc.)
2. What are the relationships between entities? (one-to-many, many-to-many?)
3. Is the schema fixed or does it need to be flexible?
4. How much data will there be? (hundreds, thousands, millions of records?)
5. Is data isolated per user/tenant or shared?
6. What needs to be cached for performance?
7. Is there an audit/history requirement? (who changed what, when?)
8. Data retention — how long is data kept? Auto-delete rules?

---

## Category C: Data Processing

**What it is:** Transformations, calculations, and logic applied to data.

| Sub-type | Examples |
|----------|----------|
| Validation | Input sanitization, business rule checks |
| Calculations | Pricing, scoring, statistics, aggregations |
| AI/ML | Classification, generation, recommendations, embeddings |
| Batch Processing | Nightly reports, bulk updates, data migrations |
| Format Conversion | PDF generation, image resizing, data export formatting |
| Filtering/Sorting | Complex queries, faceted results, dynamic sorting |

### Sub-Questions
1. What calculations or transformations happen to the data?
2. What triggers the processing? (user action, schedule, event?)
3. Is it real-time (blocking) or background (async)?
4. What's the input and what's the expected output?
5. Are there AI/ML components? What do they do specifically?
6. What happens if processing fails? Retry? Fallback?
7. Are there rate limits or resource constraints?

---

## Category D: Data Output

**What it is:** How data is displayed or delivered to users.

| Sub-type | Examples |
|----------|----------|
| Lists/Tables | Paginated lists, sortable tables, infinite scroll |
| Charts/Graphs | Bar, line, pie, heatmaps, dashboards |
| Maps | Geographic data, location markers, route display |
| Timelines | Activity feeds, history views, changelog |
| Kanban/Board | Status columns, drag-to-reorder |
| Export | PDF, CSV, Excel, JSON download |
| Print | Print-optimized layouts, receipts |
| Real-time Feeds | Live updates, streaming data, websocket-driven |

### Sub-Questions
1. What are the main views/pages users see?
2. Are there list views? What columns/fields? Sortable? Filterable?
3. Are there dashboard/analytics views? What metrics?
4. Do users need to export data? What formats?
5. Is real-time updating needed? (live counters, streaming feeds?)
6. What does an empty state look like? (no data yet)
7. Is there pagination? Infinite scroll? Load-more?

---

## Category E: Authentication

**What it is:** How users prove who they are.

| Sub-type | Examples |
|----------|----------|
| Email/Password | Traditional signup/login |
| OAuth/Social | Google, GitHub, Apple, Facebook sign-in |
| SSO | SAML, enterprise single sign-on |
| MFA | Two-factor via SMS, authenticator app, hardware key |
| Magic Link | Passwordless email link login |
| API Keys | Machine-to-machine authentication |
| Session Management | JWT, cookies, refresh tokens, session timeout |

### Sub-Questions
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers are needed?
3. Is MFA required? For all users or just admins?
4. How are sessions managed? (JWT, cookies, refresh tokens?)
5. What's the session timeout?
6. Is there a "remember me" feature?
7. Password requirements? Reset flow?
8. Is there account deletion? What happens to user data?

---

## Category F: Authorization

**What it is:** What users are allowed to do once authenticated.

| Sub-type | Examples |
|----------|----------|
| RBAC | Admin, editor, viewer roles |
| ABAC | Attribute-based (department, location, subscription tier) |
| Resource Ownership | Users can only see/edit their own data |
| Multi-tenancy | Organizations/teams with isolated data |
| Feature Flags | Features enabled per user/plan/group |
| Rate Limiting | Per-user or per-plan API/action limits |

### Sub-Questions
1. What roles exist? (admin, user, moderator, viewer?)
2. What can each role do? (CRUD per entity)
3. Is data isolated per user? Per organization/team?
4. Are there subscription tiers that unlock features?
5. Can users share access with others? (invite, transfer ownership?)
6. Are there approval workflows? (request access, admin approves?)
7. Row-level security? (users see only their own records?)

---

## Category G: Communication

**What it is:** How the system communicates with users or external systems.

| Sub-type | Examples |
|----------|----------|
| Email | Transactional, marketing, digests |
| Push Notifications | Mobile push, browser notifications |
| In-App Notifications | Bell icon, notification center, badges |
| SMS | Verification codes, alerts |
| Chat/Messaging | Real-time chat, direct messages, channels |
| Webhooks | Outbound event notifications to other systems |
| Activity Feeds | "John liked your post" style updates |

### Sub-Questions
1. What events trigger notifications? (signup, purchase, mention, etc.)
2. Which channels? (email, push, in-app, SMS?)
3. Can users configure notification preferences?
4. Are there email templates? What content?
5. Is real-time chat needed? 1:1, group, or channels?
6. Are there digest/summary emails? (daily, weekly?)
7. Do you need to send webhooks to external services?

---

## Category H: Integration

**What it is:** Connections to external services and APIs.

| Sub-type | Examples |
|----------|----------|
| REST/GraphQL Consumption | Calling external APIs |
| REST/GraphQL Exposure | Providing APIs for others to call |
| Web Scraping | Extracting data from websites |
| Payment Gateways | Stripe, PayPal, Apple Pay |
| File/Data Sync | Dropbox, Google Drive, S3 sync |
| Social Media | Posting, reading feeds, sharing |
| Email Services | SendGrid, SES, Mailgun |

### Sub-Questions
1. Which external services does the app connect to?
2. What data is sent/received from each?
3. What authentication does each external API need?
4. What happens when an external service is down? Fallback?
5. Are there rate limits on external APIs?
6. Does the app expose its own API for others?
7. Is there a payment processor? Which one? What flows? (one-time, subscription, refunds?)

---

## Category I: Workflow

**What it is:** Multi-step processes, state machines, and automation.

| Sub-type | Examples |
|----------|----------|
| State Machines | Order status (pending → processing → shipped → delivered) |
| Approval Flows | Submit → review → approve/reject |
| Cron Jobs | Scheduled tasks (nightly cleanup, weekly reports) |
| Queues | Background job processing, retry logic |
| Event Triggers | "When X happens, do Y" automation |
| Wizards/Multi-step | Step-by-step guided processes |
| Retry/Recovery | Automatic retry on failure, dead letter queues |

### Sub-Questions
1. What multi-step processes exist? What are the states?
2. What triggers transitions between states?
3. Who can trigger each transition? (user, admin, system?)
4. Are there time-based triggers? (expire after 24h, send reminder after 3 days?)
5. What happens when a step fails?
6. Are there scheduled/automated tasks? How often?
7. Is there an undo/rollback capability?

---

## Category J: Search & Discovery

**What it is:** How users find things within the app.

| Sub-type | Examples |
|----------|----------|
| Full-text Search | Keyword search across content |
| Faceted Search | Filter by category, price range, date, etc. |
| Autocomplete | Type-ahead suggestions |
| Recommendations | "Similar items", "You might also like" |
| Tags/Categories | Taxonomy, tagging system |
| Favorites/Bookmarks | Save for later |
| Recent/History | Recently viewed, search history |

### Sub-Questions
1. What is searchable? (products, users, content, everything?)
2. Is full-text search needed or just field-based filtering?
3. What filters are available? (category, date, status, price range?)
4. Is autocomplete/type-ahead needed?
5. Are there recommendations? Based on what? (behavior, similarity, manual curation?)
6. Can users save/bookmark items?
7. Is there a browse/explore mode? (categories, trending, new?)

---

## Category K: Collaboration

**What it is:** How users interact with each other through the app.

| Sub-type | Examples |
|----------|----------|
| Comments | On items, documents, tasks |
| @Mentions | Notify specific users in content |
| Sharing | Share items via link, invite collaborators |
| Co-editing | Simultaneous editing (Google Docs style) |
| Reactions | Likes, upvotes, emoji reactions |
| Following | Follow users, topics, items for updates |
| Profiles | User profiles, avatars, bio |

### Sub-Questions
1. Can users comment on things? What things?
2. Is there @mentioning? Who can be mentioned?
3. Can users share content with others? How? (link, invite, public?)
4. Is real-time co-editing needed?
5. Are there reactions/votes? (likes, upvotes, stars?)
6. Can users follow other users or items?
7. Are there user profiles? What info is shown?

---

## Category L: Monetization

**What it is:** How the app makes money.

| Sub-type | Examples |
|----------|----------|
| Subscriptions | Monthly/annual plans, auto-renewal |
| One-time Purchase | Buy once, own forever |
| Freemium/Trials | Free tier with paid upgrades, time-limited trials |
| Usage-based/Metering | Pay per API call, per GB stored, per seat |
| Marketplace/Commission | Platform fee on transactions between users |
| Invoicing | B2B billing, custom invoices, net-30 terms |
| Refunds/Credits | Cancellation policy, prorated refunds |

### Sub-Questions
1. What's the revenue model? (subscription, one-time, freemium, marketplace?)
2. What plans/tiers exist? What does each include?
3. Is there a free tier? What's included?
4. Is there a trial period? How long?
5. What payment processor? (Stripe, PayPal, etc.)
6. How are refunds handled?
7. Is there usage metering? What's metered?
8. Are there team/organization billing features?

---

## Category M: Admin/Ops

**What it is:** Back-office tools for managing the system.

| Sub-type | Examples |
|----------|----------|
| Admin Dashboard | System overview, KPIs, health metrics |
| User Management | View/edit/ban users, impersonate |
| Content Moderation | Review flagged content, approve/reject |
| Feature Flags | Toggle features per user/group/environment |
| Analytics | Usage stats, funnel analysis, event tracking |
| Configuration | System settings, environment config |

### Sub-Questions
1. Is there an admin panel? What can admins do?
2. Can admins manage users? (view, edit, suspend, delete?)
3. Is there content moderation? What gets moderated?
4. Are there analytics dashboards? What metrics?
5. Can admins configure system settings?
6. Is there an audit log? (who did what, when?)
7. Are there feature flags or A/B testing needs?

---

## Category N: Infrastructure

**What it is:** System-level concerns that support the app.

| Sub-type | Examples |
|----------|----------|
| Caching | CDN, Redis, browser cache, service worker |
| Database Migrations | Schema versioning, zero-downtime migrations |
| Circuit Breakers | Graceful degradation when services fail |
| Auto-scaling | Handle traffic spikes, scale-to-zero |
| Logging | Structured logs, log aggregation |
| Monitoring/APM | Uptime checks, performance tracking, alerting |
| CI/CD | Automated testing, deployment pipelines |

### Sub-Questions
1. Where is the app hosted? (cloud, serverless, self-hosted?)
2. What's the expected traffic? (concurrent users, requests/sec?)
3. Is there a caching strategy needed?
4. How are deployments done? (CI/CD, manual, blue-green?)
5. What monitoring/alerting is needed?
6. What's the uptime requirement? (99.9%? 99.99%?)
7. Are there compliance requirements that affect infrastructure? (data residency, encryption at rest?)

---

## Quick Reference: Mechanism Identification Cheat Sheet

When the user says... → It maps to:

| User Says | Primary Mechanism | Secondary |
|-----------|------------------|-----------|
| "users can sign up and log in" | E (Auth) | F (Authorization) |
| "it sends you an email when..." | G (Communication) | I (Workflow) |
| "you can search for..." | J (Search) | D (Output) |
| "it scrapes data from websites" | H (Integration) | C (Processing) |
| "there's a subscription plan" | L (Monetization) | F (Authorization) |
| "users can upload files" | A (Input) | B (Storage) |
| "it generates a PDF report" | C (Processing) | D (Output) |
| "there's a dashboard showing..." | D (Output) | M (Admin) |
| "orders go through stages" | I (Workflow) | B (Storage) |
| "users can comment and like" | K (Collaboration) | G (Communication) |
| "admins can ban users" | M (Admin) | F (Authorization) |
| "it needs to handle 10K users" | N (Infrastructure) | B (Storage) |
| "users can share with a link" | K (Collaboration) | F (Authorization) |
| "it calculates a score based on..." | C (Processing) | D (Output) |
| "there's a chat feature" | G (Communication) | K (Collaboration) |
