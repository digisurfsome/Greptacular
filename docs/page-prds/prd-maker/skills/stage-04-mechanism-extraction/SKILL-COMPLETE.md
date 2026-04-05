---
name: stage-04-mechanism-extraction
description: Break structured concept into tagged mechanisms with evaluations, dependencies, and core mechanism ID.
---

## Purpose

Decompose the Stage 3 structured concept document into every discrete functional mechanism. Tag each as OBVIOUS or NEEDS_EVALUATION, run 10-step criteria evaluation on NEEDS_EVALUATION mechanisms, apply Developer's Choice routing and the 15% dual-design rule, identify the core mechanism, and map all dependencies as a DAG.

## When to Use

Activate when: `context_packet.stage_3.concept_and_context` exists AND `context_packet.stage_3.drift_anchor` exists (Stage 3 is complete). Trigger phrases: "mechanism extraction", "break into mechanisms", "identify moving parts", "extract features", "what are the parts".

Do NOT activate for: gap analysis (Stage 2), structuring/organizing ideas (Stage 3), scaffolding walls/doors/rooms (Stage 5), or any request to define HOW a mechanism works internally.

## Input Format

```json
{
  "stage_0": {
    "platform_profile": {
      "boilerplate_id": "string", "boilerplate_name": "string",
      "supported_mechanisms": ["string"]
    }
  },
  "stage_2": {
    "mechanisms_identified": [
      { "category_id": "A", "category_name": "string", "sub_types": ["string"] }
    ],
    "mechanisms_gaps": [
      { "category_id": "L", "resolution": "not_needed | asked | developers_choice" }
    ],
    "scope_contract": "string"
  },
  "stage_3": {
    "concept_and_context": { "name": "string", "description": "string", "identity_paragraph": "string", "core_value_proposition": "string" },
    "target_user_and_market": { "primary_persona": {}, "market_context": "string" },
    "problem_statement": "string",
    "drift_anchor": "string",
    "feasibility_assessment": {}
  },
  "metadata": { "current_stage": 3 }
}
```

## Process

### Step 1: Read and Internalize the Concept

Read all Stage 3 sections: `concept_and_context`, `target_user_and_market`, `feasibility_assessment`, `problem_statement`, and `drift_anchor`. Do NOT extract until you can answer: What is this product? Who is it for? What is the core value proposition? What problem does it solve?

### Step 2: Enumerate Every Discrete Mechanism

Scan the concept document for every distinct functional unit. A mechanism is a **functional unit with its own internal logic, its own inputs/outputs, and its own implementation decisions**.

**Sizing rules:**
- Too small: a single button, field, or CSS class → merge up
- Too big: "the whole dashboard" with multiple independent areas → split down
- Right-sized: auth system, payment flow, video engine, template library, notification engine

Cross-reference `stage_2.mechanisms_identified` (A-N categories) to ensure nothing is missed. For each mechanism:
1. Assign a unique ID: `mech_001`, `mech_002`, ...
2. Name it descriptively (e.g., "Auth System", "Payment Flow")
3. Write a 2-5 sentence description of what it does
4. Map to one or more A-N category IDs
5. **Scope check**: Is it within `scope_contract`? Does it relate to `drift_anchor`? If outside scope and potentially critical, flag — do not silently include or exclude

### Step 3: Match Against Known Patterns

Before classifying, compare each mechanism to the known patterns library (see `references/known-patterns-library.md`). Standard patterns — auth, CRUD, dashboard, settings, admin, search, notifications — are likely OBVIOUS unless the app's version is genuinely novel.

Reference `stage_0.platform_profile.supported_mechanisms` to identify mechanisms the boilerplate handles natively. If the boilerplate covers it, it is OBVIOUS.

### Step 4: Classify Every Mechanism

Tag each mechanism:
- **OBVIOUS**: One clear implementation path. Standard pattern or natively handled by boilerplate. Set `chosen_approach` directly with name, description, and rationale. Set `evaluation: null`.
- **NEEDS_EVALUATION**: Multiple viable approaches exist. Must proceed to Step 5.

Every mechanism MUST receive a classification. No untagged mechanisms.

### Step 5: Evaluate NEEDS_EVALUATION Mechanisms

For each NEEDS_EVALUATION mechanism, identify 2-3 competing approaches. Score each approach 0-100 using the 10-step criteria (see `references/10-step-evaluation-criteria.md`):

1. Technical Complexity, 2. Scalability, 3. Maintainability, 4. Performance, 5. Security, 6. User Experience, 7. Cost, 8. Time to Implement, 9. Ecosystem Fit, 10. Future Flexibility.

For each approach, list concrete pros and cons. Record all criteria names in `evaluation.criteria`.

### Step 6: Apply Developer's Choice Routing

**Developer's Choice is the default (the "92% route").** When one approach scores highest with >15 points margin over the next-best, select it automatically as `chosen_approach`. No user decision needed.

### Step 7: Apply the 15% Threshold Rule

If two approaches score within 15 points of each other (on the 0-100 scale):
- Record the higher-scoring as `chosen_approach`
- Record the other as `alternate_approach` with `score_delta` = actual point difference
- Both get fully designed — both proceed to Stage 5 scaffolding

If the user has said "go with developer's choice on all of it", skip the 15% rule and always pick the top scorer.

### Step 8: Identify the Core Mechanism

Mark exactly ONE mechanism as `is_core_mechanism: true`. This is the mechanism that:
- Directly addresses `problem_statement`
- Embodies `core_value_proposition`
- If removed, the app has nothing to sell
- Gets built first in Phase Sequencing (Stage 7)

All other mechanisms get `is_core_mechanism: false`.

### Step 9: Map Dependencies

Identify dependencies between mechanisms:
- `"requires"`: mechanism B cannot function without A
- `"uses_output_of"`: mechanism B consumes data produced by A
- `"shares_data_with"`: bidirectional data relationship

Record each as `{ from_id, to_id, relationship }`. **Verify the graph is a DAG** — no circular dependencies. If a cycle is detected, restructure the involved mechanisms (split or merge) to break the cycle. If the cycle cannot be resolved, trigger escape hatch.

### Step 10: Validate and Count

Before writing output, verify:
1. `mechanism_count` >= 3
2. Every REQUIRED category from `stage_2.mechanisms_identified` has at least one mechanism
3. Exactly one mechanism has `is_core_mechanism: true`
4. All NEEDS_EVALUATION mechanisms have >= 2 approaches with scores
5. Dependency graph is acyclic
6. All required fields are populated on every mechanism
7. Count mechanisms with `alternate_approach` and set `dual_design_count`

If any check fails, attempt one fix. If still failing, trigger escape hatch.

## Output Format

Written to `context_packet.stage_4`:

```json
{
  "mechanisms": [
    {
      "id": "mech_001",
      "name": "string",
      "description": "string (2-5 sentences)",
      "category_ids": ["E", "F"],
      "classification": "OBVIOUS | NEEDS_EVALUATION",
      "is_core_mechanism": false,
      "chosen_approach": {
        "name": "string",
        "description": "string",
        "rationale": "string"
      },
      "alternate_approach": null,
      "evaluation": null
    },
    {
      "id": "mech_002",
      "name": "string",
      "description": "string",
      "category_ids": ["C", "G"],
      "classification": "NEEDS_EVALUATION",
      "is_core_mechanism": true,
      "chosen_approach": {
        "name": "string",
        "description": "string",
        "rationale": "string"
      },
      "alternate_approach": {
        "name": "string",
        "description": "string",
        "score_delta": 12
      },
      "evaluation": {
        "approaches": [
          {
            "name": "string",
            "score": 85,
            "pros": ["string"],
            "cons": ["string"]
          }
        ],
        "criteria": [
          "Technical Complexity", "Scalability", "Maintainability",
          "Performance", "Security", "User Experience", "Cost",
          "Time to Implement", "Ecosystem Fit", "Future Flexibility"
        ]
      }
    }
  ],
  "mechanism_dependencies": [
    { "from_id": "mech_002", "to_id": "mech_001", "relationship": "requires" }
  ],
  "mechanism_count": 8,
  "dual_design_count": 1,
  "scope_creep_flags": [
    {
      "feature_name": "string — name of the mechanism or feature outside scope",
      "flag_reason": "string — why this was flagged (e.g., 'not in scope_contract but appears critical for core mechanism')",
      "severity": "critical | warning | info",
      "related_mechanism_id": "string | null — mech_NNN ID if it relates to an extracted mechanism",
      "recommendation": "string — suggested action (e.g., 'add to scope', 'defer to Phase 2', 'ask user')"
    }
  ]
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 4,
  "confidence_scores": {
    "4": {
      "score": 92,
      "dimensions": {
        "completeness": 19, "accuracy": 18, "consistency": 19,
        "specificity": 18, "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "4": "ISO-8601" }
}
```

**Field types and constraints:**
- `mechanisms[].id`: string, unique, format `mech_NNN`
- `mechanisms[].classification`: enum `"OBVIOUS"` | `"NEEDS_EVALUATION"`
- `mechanisms[].is_core_mechanism`: boolean, exactly one `true` in array
- `mechanisms[].evaluation`: object if NEEDS_EVALUATION, `null` if OBVIOUS
- `mechanisms[].alternate_approach`: object if 15% rule applies, `null` otherwise
- `mechanisms[].alternate_approach.score_delta`: number 0-15
- `mechanism_dependencies[].relationship`: enum `"requires"` | `"uses_output_of"` | `"shares_data_with"`
- `mechanism_count`: integer >= 3
- `dual_design_count`: integer >= 0
- `scope_creep_flags`: array of objects, may be empty `[]`
- `scope_creep_flags[].feature_name`: string, required
- `scope_creep_flags[].flag_reason`: string, required
- `scope_creep_flags[].severity`: enum `"critical"` | `"warning"` | `"info"` — `critical` = appears essential but out of scope; `warning` = potentially useful but unclear; `info` = noted for future consideration
- `scope_creep_flags[].related_mechanism_id`: string (format `mech_NNN`) or `null`
- `scope_creep_flags[].recommendation`: string, required

## Edge Cases

### Missing Input
- **`concept_and_context` missing or empty**: Trigger escape hatch immediately. Stage 3 must run first.
- **`drift_anchor` missing**: Proceed but disable scope-creep detection. Flag in confidence scoring (handoff_readiness -5).
- **`mechanisms_identified` missing**: Proceed without A-N cross-reference. Flag completeness dimension.

### Ambiguous Input
- **Mechanism too vague to classify**: If the concept description does not provide enough detail to determine OBVIOUS vs NEEDS_EVALUATION, default to NEEDS_EVALUATION and note in the description that the mechanism needs more detail from the user.
- **Two features that might be one mechanism or two**: If they share >50% of their inputs/outputs and internal logic, merge. If they have distinct decision paths, split.

### Scope Overflow
- **Discovering HOW details**: If you start defining walls/doors/rooms or internal step sequences, STOP. That is Stage 5. Record only WHAT the mechanism does, not the internal workflow.
- **New feature discovered not in scope**: If a mechanism emerges that is outside `scope_contract` but appears critical, do NOT silently include. Flag it in a `scope_creep_flags` array and note it in escape hatch if confidence drops.

### All Mechanisms OBVIOUS
- Valid if the app uses entirely standard patterns on a mature boilerplate. Set `dual_design_count: 0` and note in confidence scoring.

### Fewer Than 3 Mechanisms
- Trigger escape hatch. The concept may be too abstract (Stage 3 needs revision) or too simple for this pipeline.

### Circular Dependencies
- Attempt to restructure: split the entangled mechanism into sub-mechanisms or merge two circular dependencies into one mechanism. If the cycle cannot be broken, trigger escape hatch.

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All REQUIRED A-N categories represented? All mechanism fields populated? `mechanism_count` >= 3? Exactly one core mechanism? Dependency graph complete?
- 0-5: <3 mechanisms; REQUIRED categories missing; fields empty
- 6-10: 3+ mechanisms but 2+ REQUIRED categories unrepresented
- 11-15: All REQUIRED categories covered; all fields complete; 1-2 mechanisms may need splitting
- 16-20: All relevant categories covered; every mechanism properly sized; core identified; dependencies comprehensive

**2. Accuracy (0-20):** Every mechanism traces to concept document? No hallucinated mechanisms? Classifications defensible? Evaluation scores reflect real tradeoffs?
- 0-5: Mechanisms not in concept (hallucinated); classifications clearly wrong
- 6-10: Most match but 2-3 misidentified or misclassified
- 11-15: All match concept; classifications defensible; scores reasonable
- 16-20: Direct traceability; classifications obviously correct; evaluations reflect genuine engineering judgment

**3. Consistency (0-20):** No overlapping mechanisms? Dependency graph acyclic? Descriptions non-contradictory? Category mappings correct?
- 0-5: Same feature described twice; circular dependencies
- 6-10: Minor overlaps; mostly correct dependencies
- 11-15: No overlaps; valid DAG; consistent descriptions
- 16-20: Clean separation; comprehensive acyclic graph; each mechanism has unique non-overlapping scope

**4. Specificity (0-20):** Descriptions precise enough for Stage 5? Approach descriptions concrete?
- 0-5: Vague ("handles user stuff"); no clear boundaries
- 6-10: Names feature area but lacks I/O detail
- 11-15: Explains what it does, inputs, outputs, decisions involved
- 16-20: Stage 5 can immediately apply 7 questions without asking "what does this mechanism do?"

**5. Handoff Readiness (0-20):** Stage 5 can scaffold every mechanism? `chosen_approach` set for all? Dual-design mechanisms fully specified? Dependencies clear for Stage 7?
- 0-5: Stage 5 would ask "what are the mechanisms?"
- 6-10: Most scaffoldable but 2-3 too vague
- 11-15: All scaffoldable; 1-2 need minor clarification
- 16-20: Every mechanism immediately ready for 7-question framework

**Total = sum (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 5 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `concept_and_context` is missing or empty
- Fewer than 3 mechanisms identifiable after examining all context
- Circular dependencies that cannot be resolved by restructuring
- A mechanism is outside scope but appears critical — cannot decide without human input
- Confidence score < 70 after one retry

**Save:**
- Current `context_packet` with partial mechanism list
- Stage number (4) and step where halt occurred
- Which mechanisms were successfully extracted
- What was attempted and what failed
- Suggested questions for the human

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 4,
  "step": "string (e.g., mechanism_classification, dependency_validation)",
  "reason": "string",
  "suggested_questions": ["string"],
  "partial_output": {
    "mechanisms_extracted_so_far": [],
    "mechanisms_blocked": []
  }
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input summary:** A task manager app (from Stage 3). Concept: "TaskFlow — Kanban + list-based task manager for developer teams with workspaces, assignments, notifications, and analytics dashboard." Platform: Next.js + Supabase. Stage 2 identified A,B,C,D,E,F,G,K as present; L,M as gaps (resolved via questions: freemium SaaS model, admin role).

**Extraction result** (abbreviated):

```json
{
  "mechanisms": [
    {
      "id": "mech_001", "name": "Auth System",
      "description": "User registration, login (email + OAuth via Google/GitHub), password reset, session management. Handles team invitations via email link.",
      "category_ids": ["E"],
      "classification": "OBVIOUS",
      "is_core_mechanism": false,
      "chosen_approach": { "name": "Supabase Auth", "description": "Built-in Supabase Auth with OAuth providers.", "rationale": "Native to boilerplate. Zero custom auth code." },
      "alternate_approach": null, "evaluation": null
    },
    {
      "id": "mech_002", "name": "Task Management Engine",
      "description": "Core CRUD for tasks: create, read, update, delete. Tasks have title, description, due date, priority (high/med/low), assignee, status (todo/in-progress/done). Supports kanban drag-drop and list view with sorting/filtering.",
      "category_ids": ["A", "B", "D"],
      "classification": "OBVIOUS",
      "is_core_mechanism": true,
      "chosen_approach": { "name": "Supabase CRUD + React DnD", "description": "Supabase tables with RLS + React DnD for kanban.", "rationale": "Standard CRUD pattern. Drag-drop is a UI concern, not a novel mechanism." },
      "alternate_approach": null, "evaluation": null
    },
    {
      "id": "mech_003", "name": "Notification Engine",
      "description": "In-app and email notifications for task assignments, due date reminders, and workspace activity. User-configurable preferences.",
      "category_ids": ["G"],
      "classification": "NEEDS_EVALUATION",
      "is_core_mechanism": false,
      "chosen_approach": { "name": "Supabase Edge Functions + Resend", "description": "Edge Functions trigger on DB events, send via Resend.", "rationale": "Scored highest: native to stack, low cost, simple." },
      "alternate_approach": { "name": "Dedicated Queue + Worker", "description": "BullMQ queue with Node worker for async processing.", "score_delta": 11 },
      "evaluation": {
        "approaches": [
          { "name": "Supabase Edge Functions + Resend", "score": 82, "pros": ["Native to stack", "Low cost", "Simple setup"], "cons": ["Limited retry logic", "Cold start latency"] },
          { "name": "Dedicated Queue + Worker", "score": 71, "pros": ["Robust retry", "Scalable", "Full control"], "cons": ["Extra infrastructure", "More complex", "Higher cost"] }
        ],
        "criteria": ["Technical Complexity","Scalability","Maintainability","Performance","Security","User Experience","Cost","Time to Implement","Ecosystem Fit","Future Flexibility"]
      }
    }
  ],
  "mechanism_dependencies": [
    { "from_id": "mech_002", "to_id": "mech_001", "relationship": "requires" },
    { "from_id": "mech_003", "to_id": "mech_001", "relationship": "requires" },
    { "from_id": "mech_003", "to_id": "mech_002", "relationship": "uses_output_of" }
  ],
  "mechanism_count": 3,
  "dual_design_count": 1,
  "scope_creep_flags": []
}
```

No scope creep flags — all mechanisms trace to the concept document and scope contract.

Confidence: Completeness 18, Accuracy 18, Consistency 19, Specificity 17, Handoff Readiness 18 = **90. Gate: pass.**


---

## REFERENCE: 10-step-evaluation-criteria

# 10-Step Criteria Evaluation for NEEDS_EVALUATION Mechanisms

When a mechanism has multiple viable implementation approaches, score each approach 0-100 using these 10 criteria. Each criterion is worth 0-10 points. Sum all 10 for the total score.

---

## Criteria

### 1. Technical Complexity (0-10)
How hard is this approach to implement correctly?
- 0-3: Requires deep expertise, novel algorithms, or cutting-edge tech
- 4-6: Moderate complexity, well-documented but requires careful implementation
- 7-10: Straightforward, well-trodden path, ample examples and libraries

**Score HIGH for simpler approaches** (less complexity = better).

### 2. Scalability (0-10)
How well does this approach handle growth (10x users, 100x data)?
- 0-3: Will hit walls at moderate scale, requires rearchitecture
- 4-6: Scales with known effort (add caching, indexes, workers)
- 7-10: Scales naturally, horizontally, or has proven track record at scale

### 3. Maintainability (0-10)
How easy is this to maintain, debug, and modify over time?
- 0-3: Complex internals, poor observability, tightly coupled
- 4-6: Standard patterns but some hidden complexity
- 7-10: Clean separation, good logging, easy to understand and modify

### 4. Performance (0-10)
What are the latency, throughput, and resource characteristics?
- 0-3: Slow, resource-heavy, or creates bottlenecks
- 4-6: Acceptable performance with optimization
- 7-10: Fast, efficient, minimal resource usage

### 5. Security (0-10)
What are the security implications and attack surface?
- 0-3: Large attack surface, requires significant security hardening
- 4-6: Standard security concerns, handled by following best practices
- 7-10: Minimal attack surface, security built into the approach

### 6. User Experience (0-10)
How does this approach affect what the end user sees and feels?
- 0-3: Visible UX compromises (loading delays, limited features, workarounds)
- 4-6: Acceptable UX with minor tradeoffs
- 7-10: Seamless UX, no compromises visible to the user

### 7. Cost (0-10)
What are the infrastructure, service, and operational costs?
- 0-3: Expensive ongoing costs, paid APIs, dedicated infrastructure
- 4-6: Moderate costs, scales linearly with usage
- 7-10: Low cost, free tier sufficient, or included in existing stack

### 8. Time to Implement (0-10)
How long does this approach take from start to production-ready?
- 0-3: Weeks of development, significant integration work
- 4-6: Days of focused work, some integration required
- 7-10: Hours to days, drop-in solution or minimal wiring

### 9. Ecosystem Fit (0-10)
How well does this approach integrate with the chosen stack?
- 0-3: Foreign to the stack, requires adapters, bridges, or workarounds
- 4-6: Compatible but not native, some glue code needed
- 7-10: Native to the stack, first-party support, idiomatic usage

### 10. Future Flexibility (0-10)
How well does this approach accommodate future changes?
- 0-3: Locked in, hard to swap, creates vendor/architectural lock-in
- 4-6: Changeable with moderate refactoring
- 7-10: Easy to swap, extend, or replace without cascading changes

---

## Scoring Process

1. For each NEEDS_EVALUATION mechanism, list 2-3 competing approaches
2. Score each approach on all 10 criteria (0-10 per criterion)
3. Sum for total (0-100)
4. List 2-4 concrete pros and 2-4 concrete cons per approach
5. Apply Developer's Choice: if top score has >15 point margin, auto-select
6. Apply 15% rule: if top two scores are within 15 points, design both

## Score Interpretation

| Total Score | Meaning |
|-------------|---------|
| 80-100 | Strong approach — high confidence |
| 60-79 | Viable approach — acceptable with known tradeoffs |
| 40-59 | Weak approach — significant concerns |
| 0-39 | Poor approach — should not be selected |

## Example

**Mechanism:** Notification Engine
**Approaches:** (A) Supabase Edge Functions + Resend, (B) BullMQ Queue + Worker

| Criterion | Approach A | Approach B |
|-----------|-----------|-----------|
| Technical Complexity | 8 | 5 |
| Scalability | 6 | 9 |
| Maintainability | 8 | 6 |
| Performance | 7 | 8 |
| Security | 8 | 7 |
| User Experience | 8 | 8 |
| Cost | 9 | 5 |
| Time to Implement | 9 | 5 |
| Ecosystem Fit | 9 | 6 |
| Future Flexibility | 6 | 7 |
| **Total** | **78** | **66** |

Delta = 12 points (within 15) → **Design both. Record alternate_approach with score_delta: 12.**


---

## REFERENCE: known-patterns-library

# Known Patterns Library

Standard patterns for quick OBVIOUS classification. If a mechanism matches one of these patterns AND the boilerplate/stack supports it natively, classify as OBVIOUS and use the standard approach.

---

## Auth System
**Pattern:** Registration, login, password reset, session management, OAuth providers.
**Standard approach:** Use the boilerplate's auth provider (Supabase Auth, NextAuth, Firebase Auth, Clerk).
**When NEEDS_EVALUATION:** Custom auth flows, unusual session requirements, multi-tenant SSO, or boilerplate has no built-in auth.

## CRUD Operations
**Pattern:** Create, read, update, delete for any entity. Forms, lists, detail views.
**Standard approach:** Database table + ORM + REST/GraphQL endpoints + standard UI components.
**When NEEDS_EVALUATION:** Complex validation rules, multi-step creation wizards, optimistic updates with conflict resolution, or real-time collaborative editing.

## Dashboard
**Pattern:** Sidebar navigation + main content area + summary widgets/cards + charts.
**Standard approach:** Layout component + widget grid + charting library (Recharts, Chart.js).
**When NEEDS_EVALUATION:** Real-time streaming data, customizable widget layouts, complex drill-down analytics, or AI-generated insights.

## Settings Page
**Pattern:** Key-value preferences, toggles, dropdowns. User profile, notification preferences, theme.
**Standard approach:** Form with save button, stored in user profile table or key-value store.
**When NEEDS_EVALUATION:** Almost never. This is OBVIOUS in virtually all cases.

## Admin Panel
**Pattern:** User management (view/edit/ban), content moderation, system config, analytics.
**Standard approach:** Protected routes + admin role check + CRUD views for system entities.
**When NEEDS_EVALUATION:** Multi-tenant admin with org-level permissions, complex moderation workflows, or feature flag management systems.

## Search
**Pattern:** Text search across entities, filters, sorting, pagination.
**Standard approach:** Database full-text search (PostgreSQL `tsvector`, SQLite FTS5) or search service (Algolia, Meilisearch).
**When NEEDS_EVALUATION:** Semantic/vector search, faceted search across multiple entity types, search with AI-powered ranking, or search at >1M documents.

## Notifications
**Pattern:** In-app notifications (bell icon), email notifications, push notifications.
**Standard approach:** Database notification table + email service (Resend, SendGrid) + in-app polling or WebSocket.
**When NEEDS_EVALUATION:** Complex notification routing (different channels per event type), digest/batching logic, real-time push at scale, or notification preferences with granular controls.

## File Upload
**Pattern:** Single/multi file upload, image preview, progress bar, size/type validation.
**Standard approach:** Presigned URLs to S3/Supabase Storage + client-side validation + progress tracking.
**When NEEDS_EVALUATION:** Large file processing (video transcoding, PDF parsing), collaborative file editing, or complex file pipeline (upload → process → store → serve).

## Payment / Billing
**Pattern:** One-time payments, subscriptions, plan management, invoices.
**Standard approach:** Stripe integration with Checkout or Elements. Webhook for fulfillment.
**When NEEDS_EVALUATION:** Multiple payment processors, marketplace payments (split payouts), usage-based/metered billing, or cryptocurrency payments.

## Email System
**Pattern:** Transactional emails (welcome, reset, receipt), marketing emails, templates.
**Standard approach:** Email service (Resend, SendGrid, SES) + HTML templates.
**When NEEDS_EVALUATION:** Complex template engine, email builder UI, bulk sending with deliverability optimization, or multi-language email support.

## Credit / Token System
**Pattern:** Balance tracking, deduction on action, purchase/top-up, usage history.
**Standard approach:** Integer balance column + atomic decrement + purchase via Stripe + transaction log table.
**When NEEDS_EVALUATION:** Complex pricing tiers, expiring credits, shared team pools, or credits across multiple resource types with different costs.

## API / Integration Layer
**Pattern:** REST/GraphQL API for external consumers, webhook endpoints, third-party API consumption.
**Standard approach:** Standard API routes + API key auth + rate limiting middleware.
**When NEEDS_EVALUATION:** Multiple external APIs with fallback logic, complex data sync, real-time webhooks at scale, or building a public API platform.

---

## Decision Rule

1. Does the mechanism match a pattern above? → Likely OBVIOUS
2. Does the boilerplate handle it natively? → Definitely OBVIOUS
3. Does the "When NEEDS_EVALUATION" condition apply? → NEEDS_EVALUATION
4. Is the mechanism genuinely novel (no pattern match)? → NEEDS_EVALUATION


---

## REFERENCE: mechanism-categories-summary

# A-N Mechanism Categories — Quick Reference

Condensed from the Mechanism Identification Framework. Use for cross-referencing during extraction.

| ID | Category | What It Covers | Common Sub-types |
|----|----------|---------------|-----------------|
| A | Data Input | How data enters the system | Forms, file upload, voice/audio, camera/OCR, drag-and-drop, sensors, import |
| B | Data Storage | How and where data persists | Relational DB, NoSQL, blob storage, cache, search index, audit trail |
| C | Data Processing | Transformations and logic applied to data | Validation, calculations, AI/ML, batch processing, format conversion, filtering |
| D | Data Output | How data is displayed or delivered | Lists/tables, charts, maps, timelines, kanban, export, print, real-time feeds |
| E | Authentication | How users prove identity | Email/password, OAuth, SSO, MFA, magic link, API keys, session management |
| F | Authorization | What users are allowed to do | RBAC, ABAC, resource ownership, multi-tenancy, feature flags, rate limiting |
| G | Communication | How system communicates | Email, push notifications, in-app notifications, SMS, chat, webhooks, activity feeds |
| H | Integration | Connections to external services | REST/GraphQL APIs, scraping, payment gateways, file sync, social media, email services |
| I | Workflow | Multi-step processes and automation | State machines, approval flows, cron jobs, queues, event triggers, wizards, retry/recovery |
| J | Search & Discovery | How users find things | Full-text search, faceted search, autocomplete, recommendations, tags, favorites, history |
| K | Collaboration | How users interact with each other | Comments, @mentions, sharing, co-editing, reactions, following, profiles |
| L | Monetization | How the app makes money | Subscriptions, one-time purchase, freemium, usage-based, marketplace, invoicing, refunds |
| M | Admin/Ops | Back-office management tools | Admin dashboard, user management, moderation, feature flags, analytics, configuration |
| N | Infrastructure | System-level support concerns | Caching, DB migrations, circuit breakers, auto-scaling, logging, monitoring, CI/CD |

## Cross-Reference Rules

1. Every REQUIRED category from `stage_2.mechanisms_identified` must have at least one mechanism extracted for it
2. Categories in `stage_2.mechanisms_gaps` with `resolution: "not_needed"` can be skipped
3. Categories with `resolution: "developers_choice"` should have a mechanism with OBVIOUS classification using the default approach
4. A single mechanism can map to multiple categories (e.g., an auth system maps to E and potentially F)
5. If a mechanism spans 4+ categories, consider whether it should be split into smaller mechanisms
