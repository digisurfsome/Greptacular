# Default Assumptions Reference

> Complete set of defaults for zero-input users. Every default is logged as an assumption with confidence level and reversal cost.

---

## Zero-Input Default Set

When the user provides no answers or says "I don't know" / "just build something," ALL of the following are applied:

| # | Field | Default Value | Confidence | Reversal Cost | Source |
|---|-------|--------------|------------|---------------|--------|
| 1 | `metadata.app_type` | `greenfield` | assumed | high | No existing codebase indicated |
| 2 | `platform_profile.boilerplate_id` | `supabase_web` | assumed | medium | Lowest-risk, highest-coverage default for web apps |
| 3 | `tech_stack.framework` | `Next.js 14` | assumed | medium | Default web framework for supabase_web profile |
| 4 | `tech_stack.database` | `Supabase/Postgres` | assumed | high | Core data layer for supabase_web profile |
| 5 | `tech_stack.auth_provider` | `Supabase Auth` | assumed | medium | Native auth for supabase_web profile |
| 6 | `tech_stack.hosting` | `Vercel` | assumed | low | Default hosting for Next.js apps |
| 7 | Platform target | Web only | assumed | medium | Web is the most common starting platform |
| 8 | Repo source | New repo | assumed | low | Greenfield implies new repo |
| 9 | CSS/Styling | Tailwind CSS | assumed | low | Included in supabase_web boilerplate |
| 10 | Payment processor | Stripe (deferred) | assumed | low | Only activated if monetization signal appears in later stages |
| 11 | AI/Tooling | Claude Code | assumed | low | Running within this pipeline |
| 12 | `question_budget.mode` | `zero_input` | assumed | low | No user input provided |

---

## Reversal Cost Definitions

| Cost | Meaning | Examples |
|------|---------|----------|
| `low` | Can change later with minimal rework. Affects config or tooling only. | Hosting provider, CSS framework, repo setup |
| `medium` | Changing requires moderate rework. Affects code patterns and file structure. | Framework change (Next.js → SvelteKit), auth provider swap |
| `high` | Changing requires significant rework. Affects data model, auth, or core architecture. | Database engine change, greenfield → existing app, platform target change |

---

## Partial-Input Inference Rules

When the user answers some questions but not others, use these inference rules:

| User Says | Inference | Confidence |
|-----------|-----------|------------|
| "Web app" (no framework preference) | Framework: Next.js 14 | inferred |
| "Mobile app" (no framework preference) | Framework: Flutter | inferred |
| "Both web and mobile" | Profile: dual | known |
| "I want to use React" | Framework: Next.js 14 (React-based) | inferred |
| "I want to use Vue" | Profile: no_boilerplate, Framework: Nuxt.js | inferred |
| "I want to use Firebase" | Profile: no_boilerplate, Database: Firebase/Firestore, Auth: Firebase Auth | known |
| "Deploy to AWS" | Hosting: AWS | known |
| "I have an existing app" | Profile: raw_checklist, app_type: existing | known |
| "I don't care about the stack" | Apply full zero-input defaults | assumed |

---

## Question Budget Defaults

| Mode | Max Rounds | Blocking Only | Downstream Behavior |
|------|------------|---------------|---------------------|
| `full_detail` | 2 | true | Stages 2-9 ask only questions that block progress |
| `minimal_input` | 3 | false | Stages 2-9 fill gaps with defaults, ask 1-3 rounds |
| `zero_input` | 0 | true | Stages 2-9 fill ALL gaps with defaults, ask 0 questions |

After `max_rounds` of unanswered questions across the entire pipeline, the system auto-fills remaining gaps with deterministic defaults and proceeds.
