---
description: Convert Agent OS document into PRD pipeline context_packet.json
---

# PRD Prep — Convert Your Agent OS Document to Pipeline Format

You will read the user's Agent OS document and convert it into a `context_packet.json` that the PRD pipeline can process. Depending on how complete the document is, you will populate stages 0-2 OR stages 0-3, so the chain starts at the right point.

## Input

`$ARGUMENTS` is the path to the Agent OS markdown document.

Example: `/prd-prep prd-output/my-app/agent-os.md`

If `$ARGUMENTS` is empty, ask the user for the path to their Agent OS document.

## What You Do

1. **Read** the Agent OS document at the specified path.
2. **Create** the output directory next to the input file (if it doesn't exist).
3. **Assess document completeness** - does it already have structured sections (product identity, target users, feasibility, problem statement)? Or is it raw/unstructured?
4. **Extract and infer** the fields below from the document content.
5. **Write** `context_packet.json` to the same directory as the input file.
6. **Report** what you extracted, what you inferred, and any gaps.

## Stage 3 Decision: Skip or Include?

**If the document is a fully structured Agent OS document** (has product identity, target users/personas, feasibility assessment, problem statement, and especially if it has been through gap analysis and a second Agent OS pass):
- Populate stage_3 fields directly from the document
- Set `metadata.current_stage` to 3
- The chain will start at Stage 4 (Mechanism Extraction)

**If the document is raw/unstructured** (brain dump, idea notes, rough description without clear sections):
- Leave stage_3 empty
- Set `metadata.current_stage` to 2
- The chain will start at Stage 3 (Agent OS Structuring) which will structure the raw material

Tell the user which path you chose and why.

## Fields to Extract

### stage_0 — Technical Foundation

```json
{
  "platform_profile": {
    "boilerplate_id": "INFER from tech mentions - supabase_web | flutter_mobile | dual | no_boilerplate | raw_checklist",
    "boilerplate_name": "INFER - e.g. Supabase Web Starter",
    "description": "INFER - brief description of the platform choice"
  },
  "tech_stack": {
    "framework": "EXTRACT - e.g. React, Next.js, Flutter, etc.",
    "database": "EXTRACT - e.g. Supabase/Postgres, Firebase, SQLite, etc.",
    "auth_provider": "EXTRACT - e.g. Supabase Auth, Firebase Auth, Clerk, etc.",
    "hosting": "EXTRACT - e.g. Vercel, Railway, Fly.io, etc.",
    "additional": {}
  },
  "checklist_rule_ids": [],
  "command_allowlist": [],
  "resolved_rules": [],
  "structural_coverage": { "categories": [] },
  "mechanism_target": { "categories": [] },
  "assumptions": [],
  "question_budget": { "total": 0, "used": 0, "remaining": 0 }
}
```

If the document does NOT mention specific tech choices, make reasonable inferences based on the app type and note them as assumptions.

### stage_1 — Idea Capture

```json
{
  "raw_input": "THE FULL DOCUMENT TEXT - verbatim",
  "input_format": "pasted_notes",
  "captured_at": "CURRENT ISO 8601 TIMESTAMP",
  "word_count": "COUNT THE WORDS",
  "char_count": "COUNT THE CHARACTERS",
  "explicit_corrections": []
}
```

### stage_2 — Gap Analysis

This is the most important section. Read the document carefully and fill:

**archetype_matches** - Classify the app against these archetypes (include ALL that match with confidence scores):
- Dashboard / Control Panel
- Marketplace / Multi-sided Platform
- CRUD / Admin Tool
- SaaS / Subscription Service
- Social / Community Platform
- Content / Media Platform
- E-commerce / Storefront
- Analytics / Reporting Tool
- Workflow / Automation Tool
- Developer Tool / CLI
- Education / Learning Platform
- Communication / Messaging

**mechanisms_identified** - Scan the document for evidence of these mechanism categories:
- A: Data Input (forms, uploads, imports)
- B: Processing and Transformation (calculations, conversions, AI processing)
- C: Data Output (display, export, reports, downloads)
- D: User Management (auth, roles, profiles, permissions)
- E: Communication (notifications, email, chat, alerts)
- F: Navigation and Routing (pages, tabs, breadcrumbs, deep links)
- G: State Management (sessions, real-time sync, caching)
- H: Integration (APIs, webhooks, third-party services)
- I: Storage (files, media, documents, backups)
- J: Search and Discovery (search, filters, sorting, recommendations)
- K: Scheduling and Automation (cron jobs, triggers, queues)
- L: Monetization (payments, subscriptions, billing)
- M: Analytics and Tracking (usage metrics, dashboards, logging)
- N: Configuration and Settings (user prefs, admin config, feature flags)

For each found, cite the evidence from the document.

**mechanisms_gaps** - Any categories NOT mentioned. Mark as:
- `not_needed` - clearly irrelevant to this app
- `developers_choice` - could be needed but not specified

**combined_raw** - Same as the full document text (this is the primary input for stage 3).

**completeness_score** - Your honest estimate 0-100 of how complete the spec is.

**scope_contract** - Synthesize from the document:
```
IN SCOPE:
- [List everything explicitly described]

NOT IN SCOPE:
- [Things explicitly excluded or clearly irrelevant]

DEFERRED:
- [Things mentioned as later or nice to have]
```

### stage_3 — Agent OS Structuring (ONLY if document is fully structured)

If and only if the document already contains structured sections with product identity, personas, feasibility, and problem statement, extract:

```json
{
  "concept_and_context": {
    "product_name": "EXTRACT - the app name",
    "one_line_description": "EXTRACT - one sentence summary",
    "product_identity": "EXTRACT - paragraph describing what this product IS",
    "core_value_proposition": "EXTRACT - the main value it delivers"
  },
  "target_user_and_market": {
    "personas": [
      {
        "name": "EXTRACT - persona name",
        "description": "EXTRACT - who they are",
        "pain_points": ["EXTRACT"],
        "goals": ["EXTRACT"]
      }
    ],
    "market_context": "EXTRACT - competitive landscape, market positioning",
    "competitive_landscape": "EXTRACT - competitors and differentiation"
  },
  "feasibility_assessment": {
    "viability_summary": "INFER - overall build feasibility",
    "risks": ["EXTRACT any mentioned risks or challenges"]
  },
  "problem_statement": "EXTRACT - the core problem being solved, from user perspective",
  "ambiguity_resolutions": [],
  "drift_anchor": "SYNTHESIZE - a 2-3 sentence anchor statement that captures the essential identity of this product. This anchor is used by all downstream stages to prevent scope drift. It should answer: What is this? Who is it for? What makes it different?"
}
```

The drift_anchor is critical. It prevents every downstream stage from drifting away from the product's core identity. Write it carefully.

### metadata

```json
{
  "pipeline_version": "1.0.0",
  "created_at": "CURRENT ISO 8601",
  "updated_at": "CURRENT ISO 8601",
  "app_type": "greenfield",
  "status": "in_progress",
  "current_stage": "2 if raw document, 3 if fully structured",
  "archetype_matches": ["SHORTHAND LIST FROM stage_2"],
  "scope_contract_hash": "",
  "confidence_scores": {
    "0": { "score": 75, "gate_result": "flag", "note": "Inferred from document, not from formal Stage 0 process" },
    "1": { "score": 90, "gate_result": "pass", "note": "Full document captured as raw input" },
    "2": { "score": 75, "gate_result": "flag", "note": "Inferred from document, not from formal gap analysis Q&A" },
    "3": { "score": 80, "gate_result": "flag", "note": "Extracted from pre-structured Agent OS document (ONLY if stage_3 populated)" }
  },
  "stage_timestamps": {
    "0": "CURRENT ISO 8601",
    "1": "CURRENT ISO 8601",
    "2": "CURRENT ISO 8601",
    "3": "CURRENT ISO 8601 (ONLY if stage_3 populated)"
  },
  "escape_hatches": []
}
```

## Output

Write `context_packet.json` in the same directory as the input file. Then report:

1. **Document assessment** - raw/unstructured OR fully structured Agent OS
2. **Chain start point** - Stage 3 (needs structuring) or Stage 4 (already structured)
3. **App type detected** - what archetypes matched and at what confidence
4. **Mechanisms found** - which of the 14 categories (A-N) were identified
5. **Mechanisms missing** - which categories had no evidence in the document
6. **Completeness score** - your honest estimate
7. **Tech stack** - what was extracted vs. inferred
8. **Drift anchor** - if stage_3 was populated, show the drift anchor for user review
9. **Next step** - tell the user to run `/prd-chain [directory-path]` to start the automated pipeline
