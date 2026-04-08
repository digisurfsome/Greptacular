---
name: stage-03-agent-os-structuring
description: Structure raw idea into concept document with product identity, personas, feasibility, and drift anchor.
---

## Purpose

Transform the complete raw information from Stages 1+2 into a structured four-section concept document — product identity, target users, feasibility assessment, and problem statement. This is the normalization step: raw clay into a shaped block. No mechanism extraction, no "how" — only "what" and "why." The output persists as a drift anchor throughout the entire build.

## When to Use

Activate when: `context_packet.stage_2.combined_raw` exists AND `context_packet.stage_1` exists AND `context_packet.stage_0.platform_profile` exists (Stages 0-2 complete). Trigger phrases: "structure the idea", "agent os structuring", "organize concept", "create concept document", "structure into sections", "format the raw material".

Do NOT activate for: raw idea capture (Stage 1), gap analysis (Stage 2), mechanism extraction (Stage 4), scaffolding (Stage 5), or any request to "break into parts" or "extract mechanisms".

## Input Format

```json
{
  "stage_0": {
    "platform_profile": { "boilerplate_id": "string", "boilerplate_name": "string", "description": "string" },
    "tech_stack": { "framework": "string", "database": "string", "auth_provider": "string", "hosting": "string" }
  },
  "stage_1": {
    "raw_input": "string",
    "explicit_corrections": [{ "original": "string", "correction": "string", "context": "string" }]
  },
  "stage_2": {
    "combined_raw": "string — primary input, Stage 1 raw + all gap answers merged",
    "archetype_matches": [{ "archetype": "string", "confidence": 85, "rationale": "string" }],
    "mechanisms_identified": [{ "category_id": "A", "category_name": "string", "sub_types": ["string"], "evidence": "string" }],
    "checklist_coverage": { "covered": ["string"], "not_applicable": ["string"], "deferred": ["string"] },
    "scope_contract": "string"
  },
  "metadata": { "app_type": "greenfield | existing", "current_stage": 2 }
}
```

## Process

### Step 1: Ingest and Inventory Raw Material

Read `stage_2.combined_raw` in full. Also read `stage_1.explicit_corrections`. Before structuring, make a mental inventory answering five questions:

1. **What product is being described?** — Name, core functionality
2. **Who is it for?** — Target users, personas
3. **What problem does it solve?** — Pain point from user's perspective
4. **What market context is mentioned?** — Competitors, landscape, timing
5. **What has the user explicitly corrected?** — Contradictions, corrections

Cross-reference `stage_2.mechanisms_identified` to ensure every mentioned mechanism category appears in your inventory. Cross-reference `stage_2.checklist_coverage` for completeness awareness. Do NOT skip any information — every piece must appear in the structured output.

### Step 2: Resolve Ambiguities

Scan `combined_raw` for overlapping, contradictory, or duplicate concepts. Apply resolution rules (see `references/ambiguity-resolution-rules.md`):

- **Later overrides earlier**: If user said "for enterprises" then "actually for freelancers" → resolution is "freelancers"
- **Explicit corrections win**: Apply all entries from `stage_1.explicit_corrections` — corrected version takes precedence
- **Merge duplicates**: Same feature described two ways → unify into one description, note both phrasings
- **Separate bundles**: Two distinct concepts lumped together → acknowledge both, keep logically separate

Log every resolution in the `ambiguity_resolutions` array. If an ambiguity CANNOT be resolved without user input, still log it with `source: "unresolvable — needs human input"` and include the specific question needed.

### Step 3: Structure into Four Sections

Apply the Agent OS five-lens framework (see `references/agent-os-framework.md`) to organize all material into four output sections:

**Section 1 — Concept & Context** (`concept_and_context`):
- `product_name`: Clear, concrete name (use what user stated, or derive from the core concept)
- `one_line_description`: Single sentence a stranger can understand
- `product_identity`: 1-2 paragraph identity description — what this product IS
- `core_value_proposition`: Why this product matters — the unique value

**Section 2 — Target User & Market** (`target_user_and_market`):
- `personas`: 1-4 concrete personas (NOT "users" — specific types: "freelance designer", "startup CTO"). Each has name, description, pain_points[], goals[]
- `market_context`: Market landscape, timing, trends
- `competitive_landscape`: Named competitors with specific differentiators (optional — only if user mentioned competitors or if obvious from context)

**Section 3 — Feasibility Assessment** (`feasibility_assessment`):
- `viability_summary`: Is this buildable and viable? Overall assessment
- `risks`: Identified risks with severity (low/medium/high) and mitigation strategies (optional — only if real risks exist)

**Section 4 — Problem Statement** (`problem_statement`):
- Clear, user-centric statement of the PAIN. Not the solution, not features — the problem.

**Writing rules:**
- Organized, readable prose — not stream-of-consciousness
- Each section must have 50+ words of substantive content
- Contains ONLY "what" and "why" — zero "how" (no architecture, no tech choices, no implementation)
- Do NOT decompose into mechanisms (no "auth system", "payment flow" as discrete units)
- Reference features in context but do not classify or break them apart

### Step 4: Create the Drift Anchor

Write `drift_anchor`: a 2-4 sentence canonical product description capturing the ESSENCE. This persists throughout the entire build as the reference point for scope creep detection.

**Good drift anchor criteria:**
- Specific enough that adding an unrelated feature would be flagged
- General enough that legitimate feature decisions aren't blocked
- Written in plain language a non-coder can read
- Covers: what it is, who it's for, what problem it solves

### Step 5: Validate Completeness

Before writing output, verify:

1. Every piece of information from `combined_raw` appears in at least one section
2. All `mechanisms_identified` categories from Stage 2 are referenced (not decomposed) in the output
3. All gap answers from Stage 2 are incorporated
4. No information was invented — organize only, do not add
5. Output contains ONLY "what" and "why" — zero "how"
6. Each section has 50+ words of substantive content
7. `drift_anchor` is present and meets the criteria above

If any check fails, revise the relevant section before proceeding to scoring.

### Step 6: Score and Gate

Run the confidence scoring (see Confidence Scoring section below). Based on total:
- **>= 90**: Write output normally
- **70-89**: Write output with warning flag in metadata
- **< 70**: Trigger escape hatch — do NOT write output

## Output Format

Written to `context_packet.stage_3`:

```json
{
  "concept_and_context": {
    "product_name": "string",
    "one_line_description": "string — single sentence",
    "product_identity": "string — 1-2 paragraphs",
    "core_value_proposition": "string"
  },
  "target_user_and_market": {
    "personas": [
      {
        "name": "string — e.g., Freelance Designer",
        "description": "string — who this person is",
        "pain_points": ["string"],
        "goals": ["string"]
      }
    ],
    "market_context": "string",
    "competitive_landscape": [
      { "name": "string — competitor name", "differentiator": "string — how this product differs" }
    ]
  },
  "feasibility_assessment": {
    "viability_summary": "string",
    "risks": [
      { "risk": "string", "severity": "low | medium | high", "mitigation": "string" }
    ]
  },
  "problem_statement": "string — user-centric pain statement",
  "ambiguity_resolutions": [
    { "ambiguity": "string", "resolution": "string", "source": "string — what info drove the resolution" }
  ],
  "drift_anchor": "string — 2-4 sentence canonical product description"
}
```

Written to `context_packet.metadata`:

```json
{
  "current_stage": 3,
  "confidence_scores": {
    "3": {
      "score": 92,
      "dimensions": {
        "completeness": 19,
        "accuracy": 18,
        "consistency": 19,
        "specificity": 18,
        "handoff_readiness": 18
      },
      "gate_result": "pass | flag | fail"
    }
  },
  "stage_timestamps": { "3": "ISO 8601 timestamp" }
}
```

**Validation before writing:**
1. All four sections populated with 50+ words each
2. `drift_anchor` is 2-4 sentences
3. `ambiguity_resolutions` logged for every resolved ambiguity
4. No fields are null or empty where required
5. Confidence score computed and gate_result set
6. `product_name` is not empty or generic ("My App")
7. At least 1 persona in `personas` array with all required sub-fields

## Edge Cases

### Missing Input
- **`combined_raw` missing or empty**: Trigger escape hatch immediately. Stage 2 must have failed.
- **`combined_raw` under 20 words**: Trigger escape hatch — insufficient material to structure.
- **`explicit_corrections` missing**: Proceed normally — field is optional.
- **`archetype_matches` missing**: Proceed but note reduced framing context in confidence scoring.

### Ambiguous Input
- **Unresolvable contradictions** (user said two conflicting things, no later correction): Log in `ambiguity_resolutions` with `source: "unresolvable — needs human input: [specific question]"`. If more than 3 unresolvable ambiguities exist AND they affect core identity (product name, target user, or primary problem), trigger escape hatch.
- **Vague product description** (cannot determine even the product name): Trigger escape hatch with suggested question: "What is the core thing you are building?"
- **Multiple products described** (user described 2+ distinct apps): Structure the PRIMARY product (most detail). Log the secondary as an ambiguity: "Input describes multiple products. Structured [X]; deferred [Y]."

### Scope Overflow
- **Discovering mechanism-level details**: If you find yourself listing discrete moving parts (auth system, payment flow, notification engine) and classifying them — STOP. You have crossed into Stage 4. Mention features in context but do not decompose them.
- **Technical implementation details surfacing**: Do not include architecture, database schemas, API designs, or technology choices. These belong to later stages.
- **User asks to break into features**: Decline: "This stage structures the concept. Feature extraction happens in the next stage."

## Confidence Scoring

Score each dimension 0-20 after producing output:

**1. Completeness (0-20):** All four sections populated with 50+ words? Every piece of `combined_raw` represented? All Stage 2 mechanisms referenced?
- 0-5: 2+ sections empty or placeholder
- 6-10: All sections exist but 1-2 under 50 words
- 11-15: All sections substantive; minor raw material gaps
- 16-20: Thorough; every concept from `combined_raw` represented

**2. Accuracy (0-20):** Faithfully represents user's idea? No invented features? No assumptions beyond what was stated?
- 0-5: Describes a different app than user intended
- 6-10: Core idea captured but details embellished
- 11-15: Faithful representation; no invented features
- 16-20: Precise structuring with clear sourcing; nothing added, nothing lost

**3. Consistency (0-20):** Sections align with each other? Problem matches personas? Risks align with market? Ambiguities resolved consistently?
- 0-5: Sections contradict each other
- 6-10: Minor inconsistencies between sections
- 11-15: Consistent; ambiguity resolutions documented
- 16-20: Perfect alignment; thorough ambiguity log

**4. Specificity (0-20):** Precise enough that two readers draw the same conclusions? Personas concrete? Value proposition specific?
- 0-5: Vague generalizations ("helps people")
- 6-10: References the app but broad language
- 11-15: Names specific users, features, value props
- 16-20: Two readers would identify the same product, users, and problem

**5. Handoff Readiness (0-20):** Could Stage 4 extract every mechanism without ambiguity? Overlapping concepts resolved? Feature boundaries clear?
- 0-5: Stage 4 would ask "what is this app?"
- 6-10: Some mechanisms identifiable, others unclear
- 11-15: Clean extraction possible; 1-2 edge cases
- 16-20: Every mechanism extractable without ambiguity

**Total = sum of all 5 (/100)**

| Score | Gate | Action |
|-------|------|--------|
| >= 90 | `"pass"` | Proceed to Stage 4 |
| 70-89 | `"flag"` | Proceed with warning; flag low dimensions |
| < 70 | `"fail"` | Trigger escape hatch |

## Escape Hatch

**Trigger when:**
- `combined_raw` missing, empty, or under 20 words
- Product name cannot be determined from the raw material
- More than 3 unresolvable ambiguities affecting core identity
- Confidence score < 70 after one revision attempt

**Save:**
- Current `context_packet` with partial output
- Stage number (3), step where halt occurred, what failed

**Signal:**
- Set `metadata.status = "needs_human"`
- Append to `metadata.escape_hatches[]`:

```json
{
  "stage": 3,
  "step": "string — step that failed",
  "reason": "string — specific reason",
  "suggested_questions": ["string — specific questions for the human"],
  "partial_output": {}
}
```

- Save context_packet snapshot. Output structured NEEDS_HUMAN message.

## Example

**Input** (abbreviated): `combined_raw` describes a task manager for developer teams with projects, tasks, kanban board, list view, email/Google/GitHub auth, notifications, team workspaces, dark mode, dashboard with charts. Archetype: CRUD/Tool + SaaS. Platform: Next.js + Supabase.

**Output** (abbreviated — full example in `references/example-output.json`):

```json
{
  "concept_and_context": {
    "product_name": "TaskFlow",
    "one_line_description": "A clean, developer-focused task manager with kanban boards, team workspaces, and real-time notifications.",
    "product_identity": "TaskFlow is a project management tool designed specifically for developer teams who want Todoist-level simplicity without the clutter of enterprise tools like Jira. It organizes work into projects with tasks that have priorities, due dates, and assignees, displayed through kanban boards and sortable list views. Teams operate within shared workspaces with member invitations and role-based access.",
    "core_value_proposition": "Developer teams get a focused, uncluttered task management experience with the kanban and notification features they need, without the complexity of enterprise project management tools."
  },
  "target_user_and_market": {
    "personas": [
      {
        "name": "Small Dev Team Lead",
        "description": "Leads a 3-10 person development team, needs visibility into task status without micromanaging",
        "pain_points": ["Jira is too complex for small teams", "Todoist lacks team features", "No single tool handles kanban + assignments + notifications"],
        "goals": ["See team progress at a glance", "Assign and track tasks without overhead", "Keep the team aligned on priorities"]
      }
    ],
    "market_context": "The task management space is crowded but developer-specific tools that balance simplicity with team features are underserved. Jira dominates enterprise; Todoist dominates personal. The gap is small-team developer workflows.",
    "competitive_landscape": [
      { "name": "Todoist", "differentiator": "TaskFlow adds team workspaces, kanban boards, and developer-specific auth (GitHub)" },
      { "name": "Jira", "differentiator": "TaskFlow is radically simpler — no sprints, no epics, no configuration overhead" }
    ]
  },
  "feasibility_assessment": {
    "viability_summary": "Highly feasible. All components (kanban, tasks, auth, notifications) are well-understood patterns with existing libraries. Supabase handles auth and real-time out of the box. Primary risk is differentiation in a crowded market.",
    "risks": [
      { "risk": "Crowded market with established competitors", "severity": "medium", "mitigation": "Laser focus on developer teams; GitHub auth and clean UX as differentiators" }
    ]
  },
  "problem_statement": "Developer teams working on small-to-medium projects are stuck choosing between personal task apps that lack team features and enterprise tools that drown small teams in configuration and complexity. They need a way to organize, assign, and track work across their team without the overhead.",
  "ambiguity_resolutions": [
    { "ambiguity": "Auth methods: user first said 'Google' then corrected to 'not just Google — also GitHub'", "resolution": "Both Google and GitHub OAuth supported alongside email/password", "source": "Explicit correction in raw_input" }
  ],
  "drift_anchor": "TaskFlow is a task management tool for small developer teams. It provides kanban boards, task assignments with priorities and due dates, team workspaces, and real-time notifications — all with a clean, uncluttered interface. It is simpler than Jira but more team-capable than Todoist."
}
```


---

## REFERENCE: agent-os-framework

# Agent OS Framework — Five Lenses

> Origin: 15-year software veteran's framework that cut build time from 1.5 days to 0.5 days with fewer bugs.
> Function: Guardrailing system that adds walls and doors to keep agents centered on concept and context.

## The Five Lenses

Every raw idea is processed through five questions. Together they produce the four output sections.

### Lens 1: What Is the Product?

- **Name it.** Use whatever the user called it, or derive from the core concept.
- **Define it in one sentence.** A stranger reads this sentence and knows what it does.
- **Describe its identity.** 1-2 paragraphs covering what it is, how it presents itself, what makes it distinctive.

→ Maps to: `concept_and_context.product_name`, `one_line_description`, `product_identity`

### Lens 2: What Is It Solving?

- **Identify the pain.** What frustration, inefficiency, or gap does the user experience?
- **State it from the user's perspective.** Not "the system will..." but "users currently struggle with..."
- **Be specific.** Not "it helps people" but "freelance designers waste 3 hours per week manually tracking invoices."

→ Maps to: `problem_statement`

### Lens 3: Market Feasibility

- **Is this viable?** Does the market exist? Are people paying for solutions in this space?
- **What exists already?** Name competitors. Be specific.
- **What are the risks?** Technical, market, adoption risks with severity levels.
- **How does this product differ?** What's the actual differentiator — not aspirational, but real.

→ Maps to: `feasibility_assessment`, `target_user_and_market.competitive_landscape`

### Lens 4: Who Is It For?

- **Define specific personas.** Not "users" — specific types of people.
- **What are their pain points?** Real frustrations they experience.
- **What are their goals?** What they want to achieve (related to the product domain).
- **What is the market context?** Landscape, timing, trends.

→ Maps to: `target_user_and_market.personas`, `market_context`

### Lens 5: What Exists Already?

- **Name competitors.** Real products, not categories.
- **State differentiators.** For each competitor, how does THIS product differ?
- **Identify the gap.** What's the underserved niche?

→ Maps to: `target_user_and_market.competitive_landscape`

## Lens-to-Section Mapping

| Lens | Output Section |
|------|---------------|
| 1 (What is it?) | `concept_and_context` |
| 2 (What's it solving?) | `problem_statement` |
| 3 (Feasibility) | `feasibility_assessment` + `competitive_landscape` |
| 4 (Who's it for?) | `target_user_and_market` |
| 5 (What exists?) | `competitive_landscape` (overlaps with Lens 3) |

## Critical Boundaries

- **No "how":** The five lenses produce "what" and "why" only. Architecture, databases, APIs, implementation details are deferred.
- **No mechanism extraction:** Features may be mentioned in context but not decomposed into discrete units.
- **No invention:** The lenses organize what the user said. They do not add features, assumptions, or embellishments.
- **Persistent output:** The structured document serves as a drift anchor — agents reference it throughout the entire build.


---

## REFERENCE: ambiguity-resolution-rules

# Ambiguity Resolution Rules

> Stage 3 must resolve or flag every ambiguity before passing output to Stage 4.
> Unresolved ambiguity causes downstream mechanism extraction to split or miss concepts.

## Rule 1: Later Statements Override Earlier Ones

If the user said something, then later contradicted it, the LATER statement wins.

**Example:**
- Early: "This is for enterprise teams"
- Later: "Actually, I'm targeting freelancers"
- Resolution: Target user is freelancers

**Log as:**
```json
{
  "ambiguity": "Target user: 'enterprise teams' vs 'freelancers'",
  "resolution": "Freelancers — later statement overrides earlier",
  "source": "Chronological ordering in combined_raw"
}
```

## Rule 2: Explicit Corrections Always Win

Entries in `stage_1.explicit_corrections` are pre-identified contradictions. Always apply the corrected version.

**Log as:**
```json
{
  "ambiguity": "[original statement]",
  "resolution": "[corrected statement]",
  "source": "Explicit correction from Stage 1"
}
```

## Rule 3: Merge Duplicate Concepts

If the user described the same feature two different ways, unify them into one description that captures both phrasings.

**Example:**
- "Users can drag tasks between columns" AND "There's a board where you move items through stages"
- Resolution: One concept — kanban board with drag-and-drop task movement

**Log as:**
```json
{
  "ambiguity": "Two descriptions of the same feature: drag-between-columns and board-with-stages",
  "resolution": "Unified as kanban board with drag-and-drop task movement between status columns",
  "source": "Both descriptions reference the same UI pattern"
}
```

## Rule 4: Separate Bundled Concepts

If the user lumped two distinct things together, acknowledge both but keep them logically separate in the structured output.

**Example:**
- "I want a dashboard with charts and also a way to export reports"
- These are two separate concepts: dashboard visualization and report export

**Do NOT merge them. Do NOT decompose them into mechanisms (that's Stage 4). Mention both in the relevant section as related but distinct capabilities.**

## Rule 5: Unresolvable Ambiguities

If an ambiguity CANNOT be resolved from available information:

1. Do NOT guess
2. Log it with a specific question for the human
3. Use the most conservative interpretation for structuring

**Log as:**
```json
{
  "ambiguity": "User mentions both B2B and B2C use cases with equal emphasis",
  "resolution": "Cannot resolve — both appear equally intended. Structured with B2B as primary based on team features, but this needs confirmation.",
  "source": "unresolvable — needs human input: Is your primary market B2B (teams/companies) or B2C (individual users)?"
}
```

**Threshold:** If more than 3 unresolvable ambiguities affect core identity (product name, target user, or primary problem), trigger the escape hatch.

## Rule 6: Gap Answers Override Raw Input

If a gap question in Stage 2 asked about something vague in the raw input, and the user gave a specific answer, the gap answer is authoritative.

**Example:**
- Raw: "Some kind of login"
- Gap answer: "Email/password and Google OAuth"
- Resolution: Auth is email/password + Google OAuth

## Priority Order

When rules conflict:
1. Explicit corrections (Rule 2) — highest priority
2. Gap answers (Rule 6)
3. Later statements (Rule 1)
4. Merge duplicates (Rule 3)
5. Separate bundles (Rule 4)
6. Flag unresolvable (Rule 5) — last resort


---

## REFERENCE: example-output

{
  "stage_3": {
    "concept_and_context": {
      "product_name": "TaskFlow",
      "one_line_description": "A clean, developer-focused task manager with kanban boards, team workspaces, and real-time notifications.",
      "product_identity": "TaskFlow is a project management tool designed specifically for developer teams who want Todoist-level simplicity without the clutter of enterprise tools like Jira. It organizes work into projects containing tasks with priorities (high/medium/low), due dates, and assignees. Work is visualized through both kanban boards with drag-and-drop between status columns (To Do, In Progress, Done) and sortable list views ordered by due date. Teams operate within shared workspaces where they can invite members and manage access. The interface is clean, modern, and uncluttered, with dark mode support. A simple dashboard provides at-a-glance progress visibility through charts showing completed vs. pending task ratios.",
      "core_value_proposition": "Developer teams get a focused, uncluttered task management experience with the kanban boards, task assignments, and notification features they need — without the sprint planning, epic hierarchies, and configuration overhead of enterprise project management tools."
    },
    "target_user_and_market": {
      "personas": [
        {
          "name": "Small Dev Team Lead",
          "description": "Leads a 3-10 person development team at a startup or small company. Makes tooling decisions for the team. Values simplicity and low configuration overhead.",
          "pain_points": [
            "Jira requires hours of configuration and training before the team can use it",
            "Personal task apps like Todoist lack team features — no shared workspaces or assignment",
            "No single tool handles kanban, assignments, and notifications without bloat",
            "Switching between multiple tools fragments the team's workflow"
          ],
          "goals": [
            "See the team's progress at a glance without running reports",
            "Assign and track tasks with minimal process overhead",
            "Keep the team aligned on priorities without daily standups for status updates",
            "Onboard new team members to the tool in under 5 minutes"
          ]
        },
        {
          "name": "Individual Developer on the Team",
          "description": "A developer who receives task assignments and needs to manage their own workload within the team context. Uses the tool daily.",
          "pain_points": [
            "Gets assigned tasks through Slack messages that get buried",
            "Loses track of due dates across multiple projects",
            "Has to check multiple places to find what they should work on next"
          ],
          "goals": [
            "See all assigned tasks in one place with clear priorities",
            "Get notified when assigned new tasks or when deadlines approach",
            "Quickly update task status without navigating complex interfaces"
          ]
        }
      ],
      "market_context": "The task management market is crowded at the extremes — enterprise tools (Jira, Asana, Monday.com) dominate large teams while personal productivity apps (Todoist, Notion, Things) serve individuals. The gap is small-to-medium developer teams (3-15 people) who need team features without enterprise complexity. Developer-specific affordances like GitHub OAuth and clean, distraction-free interfaces serve this niche. The trend toward remote development teams increases demand for lightweight async coordination tools.",
      "competitive_landscape": [
        {
          "name": "Todoist",
          "differentiator": "TaskFlow adds team workspaces, shared kanban boards, task assignment, and developer-specific auth (GitHub OAuth) — features Todoist lacks for team workflows"
        },
        {
          "name": "Jira",
          "differentiator": "TaskFlow is radically simpler — no sprints, no epics, no story points, no configuration wizards. A team can start using it in minutes, not days"
        },
        {
          "name": "Linear",
          "differentiator": "TaskFlow targets a broader developer workflow (general task management) rather than Linear's focus on issue tracking and engineering cycle management"
        }
      ]
    },
    "feasibility_assessment": {
      "viability_summary": "Highly feasible. All core components — kanban boards, task CRUD, authentication, real-time notifications, team workspaces — are well-understood patterns with mature libraries and frameworks. The chosen stack (Next.js + Supabase) natively supports auth (email, Google, GitHub), real-time subscriptions (for notifications and live board updates), and row-level security (for team isolation). No novel technical challenges. Primary risk is market differentiation, not technical execution.",
      "risks": [
        {
          "risk": "Crowded market with well-funded established competitors (Todoist, Linear, Asana)",
          "severity": "medium",
          "mitigation": "Laser focus on the small dev team niche. GitHub auth, clean UX, zero-config setup as differentiators. Avoid feature creep into enterprise territory."
        },
        {
          "risk": "Scope creep toward enterprise features (sprints, epics, time tracking) based on user requests",
          "severity": "low",
          "mitigation": "The drift anchor explicitly defines TaskFlow as simpler-than-Jira. Any feature addition must pass the simplicity test."
        }
      ]
    },
    "problem_statement": "Developer teams working on small-to-medium projects are stuck choosing between personal task apps that lack team features (no shared workspaces, no assignments, no team notifications) and enterprise tools that drown small teams in configuration complexity, mandatory process overhead, and features they will never use. They need a way to organize, assign, and track work across their team — seeing who is working on what, when things are due, and what is blocked — without spending hours setting up the tool or training the team to use it.",
    "ambiguity_resolutions": [
      {
        "ambiguity": "Auth methods: user initially said 'email or Google' then corrected to 'not just Google — also GitHub login since this is for developer teams'",
        "resolution": "Three auth methods supported: email/password, Google OAuth, and GitHub OAuth",
        "source": "Explicit correction in raw_input — later statement adds GitHub, does not remove Google"
      },
      {
        "ambiguity": "Notification channels: user said 'Maybe email and in-app notifications' — the word 'maybe' introduces uncertainty",
        "resolution": "Both email and in-app notifications are included. 'Maybe' was used as a speech filler introducing the list, not expressing doubt — the user then specified both channels concretely.",
        "source": "Contextual interpretation of 'maybe' as conversational hedge, not conditional"
      },
      {
        "ambiguity": "Dashboard scope: user said 'maybe a chart' — unclear if dashboard is a core feature or nice-to-have",
        "resolution": "Dashboard with task completion charts is included as a feature. The user described it as part of the core concept ('there should be a simple dashboard showing how many tasks are done vs pending').",
        "source": "User's phrasing 'there should be' indicates intent, despite 'maybe a chart' hedging on chart specifics"
      }
    ],
    "drift_anchor": "TaskFlow is a task management tool for small developer teams. It provides kanban boards, task assignments with priorities and due dates, team workspaces with member invitations, and real-time notifications — all with a clean, uncluttered interface. It is simpler than Jira but more team-capable than Todoist, targeting the underserved gap between personal productivity apps and enterprise project management tools."
  },
  "metadata": {
    "current_stage": 3,
    "confidence_scores": {
      "3": {
        "score": 92,
        "dimensions": {
          "completeness": 19,
          "accuracy": 18,
          "consistency": 19,
          "specificity": 18,
          "handoff_readiness": 18
        },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "3": "2026-04-03T14:30:00Z"
    }
  }
}
