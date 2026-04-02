# Phase 1A: Agnosticize Martin's Structural Checklist

## Your Mission

You are creating the **platform-agnostic version** of Martin's structural checklist. This is the DEFAULT checklist that every app built through the PRD Maker pipeline will use. Platform-specific versions (Firebase, Supabase, etc.) are derived from this agnostic version later -- you are creating the foundation.

Martin wrote 192 rules and 43 banned patterns for building React/Firebase apps. Many of those rules encode universal wisdom (e.g., "one component per file"), but they are expressed using Firebase-specific terminology (e.g., "serverTimestamp()"). Your job is to classify every single rule and rewrite the platform-specific ones into generic principles.

**This is not a mechanical find-and-replace.** Every rule requires a judgment call. Take your time.

---

## Files to Read FIRST

Read these files completely before making any changes:

1. **`docs/page-prds/prd-maker/trial-idea-1-structural-checklist.md`** -- The full checklist. 192 rules across 18 categories + 43 banned patterns. This is your primary input.

That is the only file you need. Do not read other files -- your entire job is to transform this one document.

---

## What to Produce

**Output file:** `docs/page-prds/prd-maker/martin-agnostic-checklist.md`

### Document Structure

1. **Theory section** (top of file) -- Rewrite the existing theory section to explain that this is the AGNOSTIC version. Explain:
   - This checklist captures structural best practices for building any web app
   - Rules are tagged as UNIVERSAL, STACK-SPECIFIC (rewritten to be generic), or PATTERN (principle extracted)
   - Rules are severity-rated as CRITICAL, STANDARD, or POLISH
   - Platform-specific preambles (e.g., `web-firebase.md`, `web-supabase.md`) are derived from this by filling in the "Boilerplate Match" column with platform details
   - Keep the explanation of the Structural-Mechanism split (still valid)
   - Keep the explanation of how the preamble system works (still valid)

2. **The checklist tables** -- Same 18 categories, same table structure, but with TWO new columns added to each table.

### Table Format

Each table currently has columns: `# | Rule | Martin Says | Technical Spec | Boilerplate Match`

Transform each table to: `# | Rule | Martin Says | Technical Spec | Boilerplate Match | Type | Severity`

### Classification Rules

**Type Column -- classify every rule as one of:**

- **UNIVERSAL** -- The rule applies to any tech stack with zero changes. Examples:
  - "One component per file" -- universal
  - "Every delete action requires confirmation" -- universal
  - "Loading states that are just the word 'Loading...' are banned" -- universal
  - "No `any` types -- define TypeScript interfaces" -- universal (for any TypeScript project)

- **STACK-SPECIFIC** -- The rule is tied to Firebase, Firestore, Gemini, or a specific library. For these rules, you MUST rewrite both the "Martin Says" and "Technical Spec" columns to be generic. Keep the original Firebase-specific text as a parenthetical note. Examples:
  - "serverTimestamp()" --> "Use the database's server-generated timestamp function (e.g., Firebase: `serverTimestamp()`, Supabase: `now()`, Prisma: `@default(now())`)"
  - "users/{uid}/{collectionName}" --> "User data stored under user-scoped paths/tables (e.g., Firebase: `users/{uid}/{collection}`, SQL: `WHERE user_id = ?`)"
  - "signInWithPopup" --> "Use the auth provider's popup/redirect login flow"
  - "Firestore security rules" --> "Use the database's server-side access control rules"

- **PATTERN** -- The principle is universal but the implementation example is Firebase-specific. For these rules, extract the universal principle into "Technical Spec" and note the Firebase implementation as one example. Examples:
  - "No Firestore calls in components" --> Principle: "Data access calls must go through a service layer, never directly in UI components." Example: "Firebase: `services/firestore.ts`"
  - "Helper for user collections" --> Principle: "Create utility functions that abstract database path construction." Example: "Firebase: `getUserCollection(uid, collectionName)`"

### Severity Column -- classify every rule as one of:

- **CRITICAL** (~40 rules) -- Security vulnerabilities, authentication/authorization flaws, data integrity issues, or build-breaking problems. If you skip this rule, the app is insecure, loses data, or won't compile. Examples:
  - Auth provider nesting order (wrong order = auth state lost)
  - Protected routes (skipping = unauthorized access)
  - No `any` types (skipping = type safety gone)
  - Timestamps on all writes (skipping = data integrity lost)
  - Delete requires confirmation (skipping = accidental data loss)

- **STANDARD** (~100 rules) -- UX quality, component patterns, responsive design, accessibility. The app works without these but users will notice the quality gap. Examples:
  - Mobile-first design
  - Loading skeleton states
  - Back navigation on sub-pages
  - CRUD view pattern (List > Detail > Create > Edit)
  - Focus states on interactive elements

- **POLISH** (~52 rules) -- Cosmetic details, animation timings, specific pixel values, nice-to-have refinements. The app is fully functional without these. Examples:
  - Card hover lift animation
  - Button press scale effect
  - Specific shadow values
  - Sidebar bottom help link styling
  - Typography scale pixel values

### Banned Patterns Section

The 43 banned patterns at the bottom of the file also need classification:

- Tag each as **UNIVERSAL** or **STACK-SPECIFIC**
- For STACK-SPECIFIC bans, rewrite to be generic (e.g., "No Firestore calls in components" --> "No database calls directly in UI components")
- Add a Severity column: **CRITICAL** (security/data), **STANDARD** (UX), **POLISH** (cosmetic)

---

## Rules for Your Work

1. **Read the entire checklist before starting.** Understand the full scope. Some rules appear in multiple categories (e.g., timestamps appear in "Firestore Data Structure", "Data/API Patterns", and "Miscellaneous Rules"). Handle duplicates consistently.

2. **When in doubt, classify as PATTERN, not STACK-SPECIFIC.** The goal is to preserve the WISDOM, not just the implementation. If a rule teaches something valuable even outside Firebase, it is at least a PATTERN.

3. **Never delete a rule.** Every one of the 192 rules and 43 banned patterns must appear in the output. You are transforming, not filtering.

4. **Rewritten rules must be implementable.** Don't write vague abstractions like "use proper database patterns." Write specific, actionable instructions like "All persistent data operations must go through a service layer module; UI components never import database client libraries directly."

5. **Preserve the original 3-column content** for UNIVERSAL rules. Only modify "Martin Says" and "Technical Spec" for STACK-SPECIFIC and PATTERN rules, and always note the original Firebase wording in parentheses.

6. **Count your output.** The output file must have exactly 192 rules (across 18 categories) + 43 banned patterns. If your count doesn't match, you missed something.

---

## Success Criteria

Your work is done when:

- [ ] The output file exists at `docs/page-prds/prd-maker/martin-agnostic-checklist.md`
- [ ] The theory section explains the agnostic version and the Type/Severity system
- [ ] Every rule has a Type column value (UNIVERSAL, STACK-SPECIFIC, or PATTERN)
- [ ] Every rule has a Severity column value (CRITICAL, STANDARD, or POLISH)
- [ ] All STACK-SPECIFIC rules have been rewritten to be platform-agnostic
- [ ] All PATTERN rules have the principle extracted and the Firebase example noted
- [ ] All UNIVERSAL rules are unchanged (original Martin Says + Technical Spec preserved)
- [ ] All 43 banned patterns are classified and rewritten where needed
- [ ] The total count matches: 192 rules + 43 banned patterns
- [ ] No rule has been deleted, merged, or invented
- [ ] Rewritten rules are specific and implementable, not vague abstractions
