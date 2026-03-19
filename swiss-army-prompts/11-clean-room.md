# MODULE 11: CLEAN ROOM / REVERSE ENGINEERING PROMPT

## Rebuild an Existing App's Functionality in Your Stack

**What this does:** When you find an app or website that does exactly what you want, this module helps you analyze its functionality and rebuild it from scratch using your stack (Claude Code + Supabase + React). This is a clean room approach — you study WHAT it does, not HOW it's coded, and build your own implementation.

**When to use:**
- You see an app and want to build something similar
- You want to migrate from one tech stack to another
- You're studying a competitor and want to build a better version
- You have an old app and want to rebuild it modern

**Legal note:** Clean room reverse engineering studies the external behavior and functionality, not the source code. You're building an original implementation inspired by functionality, which is standard industry practice.

---

## --- START PROMPT ---

## TASK: Analyze an Existing App and Build My Own Version

I want to study an existing app's functionality and build my own version using our standard stack (Supabase + React + TypeScript + Tailwind). This is a clean room approach — analyze WHAT it does, then build it from scratch.

---

## SECTION 1: THE APP TO STUDY [FILL THIS IN]

**App name or URL:** [Name or link]

**What it does (in your words):**
[Describe the main purpose in 2-3 sentences]

**What I love about it:**
[What specific features or UX patterns do you want to recreate?]

**What I'd change:**
[Anything you want to do differently?]

**Screenshots available?** [Yes — I'll share them / No — I'll describe it]

---

## SECTION 2: FUNCTIONAL ANALYSIS

For the app described above, break down its functionality into these categories:

### 2A: Core User Actions

List every distinct action a user can take, organized by importance:

**Must Have (core functionality — the app is useless without these):**
1. [Action — e.g., "Create a new project"]
2. [Action — e.g., "Add tasks to a project"]
3. [Action — e.g., "Mark tasks complete"]

**Should Have (important but not critical for MVP):**
1. [Action — e.g., "Filter tasks by status"]
2. [Action — e.g., "Drag to reorder tasks"]

**Nice to Have (polish — add later):**
1. [Action — e.g., "Keyboard shortcuts"]
2. [Action — e.g., "Export to CSV"]

### 2B: Data Model

What "things" (entities) does the app manage?

For each entity:
- What fields does it have?
- How does it relate to other entities?
- Who owns it? (per-user or shared)
- How is it sorted/organized?

```
Entity: [Name]
  Fields: [list]
  Belongs to: [user / other entity]
  Has many: [child entities]
  Sorted by: [default ordering]
```

### 2C: Page Map

What screens/pages exist?

```
PUBLIC:
  / — Landing page
  /login — Sign in
  /pricing — (if applicable)

AUTHENTICATED:
  /dashboard — Main view after login
  /[entity] — List of [entities]
  /[entity]/:id — Detail view
  /[entity]/new — Create new
  /[entity]/:id/edit — Edit existing
  /settings — User settings
  /profile — User profile
```

### 2D: Key UX Patterns

What notable UX patterns does the app use?

- Navigation: sidebar / top nav / tabs / breadcrumbs?
- List display: cards / table / list / kanban?
- Forms: inline editing / modal forms / separate pages?
- Feedback: toasts / inline messages / modals?
- Search/filter: search bar / faceted filters / tags?
- Sorting: dropdown / clickable headers / drag?
- Real-time updates: yes / no?

---

## SECTION 3: MAP TO OUR STACK

Now translate each element to our standard stack:

| App Feature | Our Implementation |
|---|---|
| Authentication | Supabase Auth + Google OAuth (Module 02) |
| Database | Supabase PostgreSQL + RLS (Module 03) |
| [Feature X] | [How we'd build it] |
| [Feature Y] | [How we'd build it] |
| Real-time updates | Supabase Realtime subscriptions |
| File uploads (if any) | Supabase Storage |
| Search | Supabase `.ilike()` or full-text search |
| Payments (if any) | Stripe + Supabase Edge Functions |

### Data Model Translation

Create the Supabase SQL for each entity identified in 2B. Follow Module 03 patterns exactly (RLS, triggers, indexes).

### Page Map Translation

Map each screen to a React route. Follow Module 05 patterns for CRUD.

---

## SECTION 4: BUILD PLAN

Create a phased build plan:

**Phase 1: Foundation**
- [ ] Scaffold (Module 01)
- [ ] Auth (Module 02)
- [ ] Data layer for core entities (Module 03)
- [ ] UI Kit (Module 04)

**Phase 2: Core Functionality (Must Have)**
- [ ] CRUD for Entity 1 (Module 05)
- [ ] CRUD for Entity 2 (Module 05)
- [ ] [Core feature specific to this app]

**Phase 3: Important Features (Should Have)**
- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] Polish pass (Module 06)

**Phase 4: Visual Identity**
- [ ] Style & theme (Module 07)
- [ ] Landing page

**Phase 5: Nice to Have**
- [ ] [Feature 1]
- [ ] [Feature 2]

**Tell me this plan before starting. I'll prioritize and we'll go phase by phase.**

---

## SECTION 5: WHAT MAKES YOUR VERSION DIFFERENT

For each feature you're rebuilding, note what you want to keep, change, or add:

| Original Feature | Keep / Change / Drop | Your Version |
|---|---|---|
| [Feature 1] | Keep | Same functionality |
| [Feature 2] | Change | [What you'd do differently] |
| [Feature 3] | Drop | Not needed for my use case |
| [New Feature] | Add | [Something the original doesn't have] |

---

## SECTION 6: EXECUTE

Execute the build plan phase by phase. For each phase:
1. Use the appropriate module prompt (01-07)
2. Verify the phase works before moving to the next
3. Commit at the end of each phase

---

## --- END PROMPT ---
