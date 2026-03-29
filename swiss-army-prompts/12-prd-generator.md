# MODULE 12: PRD GENERATOR PROMPT

## Turn an Idea Into a Structured Product Requirements Document

**What this does:** Takes a rough app idea (even just a sentence) and produces a structured PRD that can feed directly into the build modules (01-07). This replaces the mentor's "Idea Prompt" but goes further — it forces you to make decisions about scope, users, and data before any code is written.

**When to use:** Before starting ANY new app. Before Module 01. This is step zero.

**Why this matters:** The #1 reason vibe-coded apps fail is vague requirements. "Build me a task manager" will produce garbage. "Build me a task manager where freelancers track billable hours per client with weekly invoicing" will produce something useful. This prompt bridges that gap.

---

## --- START PROMPT ---

## TASK: Help Me Turn This Idea Into a Build-Ready PRD

I have an app idea. Help me refine it into a structured document I can use to build it. Ask me questions if my answers are vague. Push back if I'm adding too much scope. The goal is an MVP — the smallest version that's actually useful.

---

## SECTION 1: THE RAW IDEA [FILL THIS IN]

**My idea in one sentence:**
[Describe it however you want — even a rough sentence is fine]

**Who is this for?**
[Who would use this? Be as specific as possible. "Everyone" is not an answer.]

**What problem does it solve?**
[What pain point, annoyance, or need does this address?]

**How do people solve this today?**
[Spreadsheets? A different app? Pen and paper? They don't?]

**Why would someone use YOUR app instead?**
[What makes your version better or different?]

---

## SECTION 2: SCOPE RAZOR (CRITICAL)

Before listing features, answer these scope questions:

**What is the ONE thing this app must do perfectly?**
[One sentence. This is the core. Everything else is secondary.]

**What are you EXPLICITLY not building in v1?**
[List at least 3 things people might expect but you're cutting from MVP]
1. NOT building: [feature]
2. NOT building: [feature]
3. NOT building: [feature]

**MVP test:** If someone downloaded this app and it only did [the one thing], would they still find it useful?
- If YES: good scope
- If NO: you need to add one more core feature, but only one

---

## SECTION 3: USER STORIES

For each feature, write it as a user story:

**"As a [user type], I want to [action], so that [benefit]."**

### Core (Must Have — app doesn't work without these)
1. As a [user], I want to [action], so that [benefit]
2. As a [user], I want to [action], so that [benefit]
3. As a [user], I want to [action], so that [benefit]

### Important (Should Have — significantly improves the experience)
4. As a [user], I want to [action], so that [benefit]
5. As a [user], I want to [action], so that [benefit]

### Nice to Have (Add later)
6. As a [user], I want to [action], so that [benefit]

**Cap it at 5-7 user stories for MVP.** If you have more than 7, you're building too much.

---

## SECTION 4: DATA MODEL

What "things" does the app store? Think in terms of nouns.

For each entity:

```
ENTITY: [Name] (e.g., "Project", "Recipe", "Workout")
  FIELDS:
    - [field_name]: [type] (required/optional) — [brief description]
    - [field_name]: [type] (required/optional) — [brief description]
  BELONGS TO: [user / another entity]
  HAS MANY: [child entities, if any]
  DEFAULT SORT: [how should a list of these be ordered?]
```

Common field types:
- `string` — text (title, name, description)
- `text` — long text (body, notes, content)
- `number` — integers or decimals
- `boolean` — true/false (is_active, is_complete)
- `enum` — fixed options (status: draft/active/archived)
- `date` — dates (due_date, start_date)
- `url` — links
- `json` — flexible structured data

---

## SECTION 5: PAGE MAP

List every page the app needs:

```
PUBLIC (no login required):
  /                — Landing page (what the app is, CTA to sign up)
  /login           — Sign in with Google

AUTHENTICATED (login required):
  /dashboard       — Main view after login (summary + quick actions)
  /[entities]      — List all [entities]
  /[entities]/new  — Create a new [entity]
  /[entities]/:id  — View a [entity] (read-only detail)
  /[entities]/:id/edit — Edit a [entity]
  /profile         — User profile + account settings

ADMIN (if applicable):
  /admin           — Admin dashboard
```

For each page, note:
- What data does it show?
- What actions can the user take?
- What's the primary CTA?

---

## SECTION 6: KEY DECISIONS

Make these decisions now, not during development:

| Decision | Options | Your Choice |
|----------|---------|-------------|
| Auth method | Google only / Email + Google / Magic link | |
| Data visibility | Private (per-user) / Shared (team) / Public | |
| Primary list display | Cards / Table / List | |
| Mobile priority | Mobile-first / Desktop-first / Equal | |
| Monetization | Free / Freemium / Paid | |
| Role system | Single role / User+Admin / User+Pro+Admin | |
| Dark mode | Yes / No / Later | |
| Real-time updates | Yes (live) / No (manual refresh) | |
| File uploads | Yes / No | |
| Notifications | None / In-app toast / Email (later) | |

---

## SECTION 7: OUTPUT — BUILD-READY SPEC

Compile everything above into this format that feeds directly into Modules 01-07:

```markdown
# [APP_NAME] — Product Requirements Document

## App Identity
- **Name:** [App name]
- **One-liner:** [One sentence description]
- **Target user:** [Specific user persona]
- **Core problem:** [What it solves]

## Features (for Module 01, Section 2)
1. [Feature 1 — specific description of what users can do]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4] (if needed)
5. [Feature 5] (if needed)

## Data Entities (for Module 03)
[Entity definitions from Section 4]

## Pages (for Module 05)
[Page map from Section 5]

## Style Direction (for Module 07)
- Visual feel: [from Section 1 context]
- Personality: [professional / casual / playful / premium]
- Color preference: [if any]
- Inspiration: [apps they admire, if any]

## Out of Scope for v1
- [Not building X]
- [Not building Y]
- [Not building Z]
```

**This output becomes the input for Module 01 (Scaffold).** The user copies the features into Section 2, the style direction into Section 3, and starts building.

---

## --- END PROMPT ---
