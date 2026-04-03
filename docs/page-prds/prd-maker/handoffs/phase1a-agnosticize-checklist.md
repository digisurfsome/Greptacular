# Phase 1A: Agnosticize Martin's Structural Checklist

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Estimated effort:** Single session, full thinking required
> **Output:** `docs/page-prds/prd-maker/martin-agnostic-checklist.md`

---

## Your Mission

You are creating the technology-agnostic version of Martin's Structural Checklist. This checklist contains 192 rules across 18 categories plus 43 banned patterns, currently written for a specific stack (React 19 + Firebase + Firestore + Google Auth + Lucide React + importmap). Your job is to classify every single rule and rewrite the platform-specific ones into generic principles that apply to ANY technology stack.

This is the foundation that the entire PRD Maker pipeline builds on. Every stage downstream inherits this checklist as a "preamble" -- a set of pre-decided structural rules so the agent only has to figure out what the app DOES, not how the code is organized. If you rush this or make sloppy judgment calls, every app spec produced by the pipeline will inherit those mistakes.

**This is not a mechanical find-and-replace.** Every rule requires a judgment call. Read the entire checklist first. Understand what each rule is trying to achieve. Then classify and rewrite.

---

## Files to Read (In This Order)

Read these files COMPLETELY before starting any work:

1. **`docs/page-prds/prd-maker/trial-idea-1-structural-checklist.md`** -- The source file. 192 rules across 18 categories + 43 banned patterns. Read the ENTIRE file. Understand the theory section at the top, the table format, every category, and every individual rule.

2. **`docs/page-prds/prd-maker/research-reference.md`** -- Read the sections titled "The Two Halves of the Puzzle" and "The Preamble System." These explain WHY this checklist exists and how it will be used in the pipeline. The structural half (this checklist) handles how code is organized; the mechanism half (separate document) handles what the app does.

3. **`docs/page-prds/prd-maker/build-game-plan.md`** -- Read sections "1A. Agnosticize Martin's Checklist" and "1B. Add Severity Column" for confirmation of what you are building.

---

## What You Are Producing

A single new file: **`docs/page-prds/prd-maker/martin-agnostic-checklist.md`**

This file transforms the original checklist. Every rule is preserved, but stack-specific rules are rewritten so they apply to any stack. Two new columns are added to every table.

---

## The Two New Columns

### Column 1: Type

Every rule gets exactly ONE of these three tags:

| Tag | Meaning | Action Required |
|-----|---------|-----------------|
| **UNIVERSAL** | The rule applies to any technology stack as written. Nothing about it is Firebase/React/Google-specific. | Keep the rule exactly as written in both "Martin Says" and "Technical Spec" columns. No changes needed. |
| **STACK-SPECIFIC** | The rule is tied to Firebase, Firestore, Google Auth, importmap, Lucide React, or another specific technology. | REWRITE the "Technical Spec" column to use generic language. Preserve the original "Martin Says" column verbatim. |
| **PATTERN** | The underlying principle is universal, but the example or implementation is stack-specific. | Extract the universal principle into "Technical Spec." Note the Firebase implementation as a parenthetical example. Preserve "Martin Says" verbatim. |

### Column 2: Verification

Every rule gets a testable assertion — a way to CHECK if the rule is being followed. This directly feeds Stage 9 (Verification Agent) so it has an actual test suite, not subjective judgments.

| Check Type | When to Use | Example |
|---|---|---|
| **AUTOMATED** | Can be verified with grep, lint, or a script | `grep -r "alert(" src/ --include="*.tsx"` — expect 0 results |
| **BUILD** | Verified by the build/compile process | `npm run build` succeeds with zero errors |
| **MANUAL** | Requires visual or functional inspection | "Navigate to each page and verify sidebar is hidden on mobile viewport" |

**Rules for writing verification assertions:**
- ~100 of the 191 rules can be checked with AUTOMATED assertions (grep, lint, AST checks)
- ~40 can be checked via BUILD (TypeScript compiler, linter configs)
- ~50 require MANUAL verification (visual, UX, behavioral checks)
- Be SPECIFIC. Not "check the code" but `grep -r "console\.log" src/ --include="*.tsx" | wc -l` — expect 0
- For MANUAL checks, describe exactly what to look for and where
- Some rules may have BOTH an automated partial check AND a manual full check — include both

**Examples of good verification assertions:**

| Rule | Verification |
|---|---|
| No `alert()` | AUTOMATED: `grep -rn "alert(" src/ --include="*.tsx" --include="*.ts"` — expect 0 results |
| One component per file | AUTOMATED: For each `.tsx` file in `src/components/`: count `export default` — expect exactly 1 per file |
| All inputs have focus ring | AUTOMATED: `grep -rn "focus:ring" src/ --include="*.tsx"` — expect ≥ 1 result per input/button component. MANUAL: Tab through all form inputs and verify visible focus indicator |
| Timestamps on all writes | AUTOMATED: `grep -rn "createdAt\|updatedAt\|timestamp" src/services/` — expect presence in every write/update function |
| Mobile-first design | MANUAL: Open app at 375px width. Every page should render without horizontal scroll. All text readable, all buttons tappable |
| Delete requires confirmation | MANUAL: Click every delete button in the app. Each one should show a confirmation dialog before executing |
| Skeleton loading states | MANUAL: Throttle network to Slow 3G. Navigate to each page with data. Should show skeleton placeholders, never bare "Loading..." text |

### Column 3: Severity

Every rule gets exactly ONE of these three tags:

| Tag | Meaning | Approximate Count |
|-----|---------|-------------------|
| **CRITICAL** | Security vulnerability, data integrity issue, authentication bypass, build-breaking error, or production crash if violated. Non-negotiable for any production app. | ~40 rules |
| **STANDARD** | UX quality, component patterns, mobile responsiveness, state management, code organization. Violating these produces a working but sloppy app. | ~100 rules |
| **POLISH** | Cosmetic refinements, naming preferences, animation smoothness, spacing consistency. Nice to have but the app works fine without them. | ~52 rules |

---

## How to Rewrite Rules

### STACK-SPECIFIC Rules

Replace the specific technology with a GENERIC description of the capability needed. Be specific about WHAT is needed, not vague.

**Examples of good rewrites:**

| Original (Firebase-specific) | Agnostic Rewrite |
|------------------------------|------------------|
| "Use `serverTimestamp()` for all date fields" | "Use the database's server-generated timestamp function for all date fields -- never use client-side date generation (`new Date()`) for timestamps that need to be consistent across clients" |
| "Firebase Auth with `signInWithPopup` and `GoogleAuthProvider`" | "Use the authentication provider's popup or redirect sign-in flow with the configured OAuth provider" |
| "All persistent data in Cloud Firestore; no Realtime Database, no external DB" | "All persistent data stored in a single configured database technology; do not mix multiple database backends" |
| "Locked importmap in index.html" | "All dependencies managed through the project's configured module/build system; dependency versions locked" |
| "Use Lucide React for all icons" | "Use a single, consistent icon library for all icons throughout the app; do not mix icon sources" |
| "users/{uid}/{collectionName}" | "User data scoped to user-owned paths or rows (e.g., in document DBs: `users/{uid}/{collection}`, in SQL: `WHERE user_id = ?`)" |

**Bad rewrites (too vague -- do NOT do this):**
- "Handle auth properly" -- What does "properly" mean?
- "Use a good database" -- Not actionable
- "Follow best practices for icons" -- Which practices?

### PATTERN Rules

Extract the universal principle. Note the Firebase example.

**Examples:**

| Original | Agnostic Principle + Example |
|----------|------------------------------|
| "No Firestore calls in components" | "Data access calls must go through a service layer module -- UI components never import or call database client libraries directly. (e.g., in Firebase projects: all Firestore calls go through `services/firestore.ts`)" |
| "Create a helper for user collections" | "Create utility functions that abstract database path/query construction so collection names and access patterns are defined in one place. (e.g., in Firebase: `getUserCollection(uid, collectionName)` returns a Firestore collection reference)" |
| "Firestore security rules must mirror client-side auth checks" | "Server-side data access rules must mirror client-side authorization checks -- never rely solely on client-side guards. (e.g., Firebase: Firestore security rules; Supabase: RLS policies; custom backend: middleware authorization guards)" |

### UNIVERSAL Rules

Keep exactly as written. Just add the Type and Severity columns.

---

## Banned Patterns Section

The original file has 43 banned patterns. Apply the same classification:
- Tag each as **UNIVERSAL** or **STACK-SPECIFIC**
- For STACK-SPECIFIC bans, rewrite to describe the generic PATTERN being banned
  - Example: "No `alert()`/`confirm()`/`prompt()`" is UNIVERSAL
  - Example: "No Firebase Realtime Database" becomes "No mixing database backends within one project"
- Add a **Severity** column (CRITICAL / STANDARD / POLISH)

---

## Output File Structure

### 0. Version Header

At the very top of the file, before the theory section, add:

```
---
version: "1.0"
source: trial-idea-1-structural-checklist.md
based_on: "Martin's 1,500-line Build PRD prompt"
date_created: 2026-04-02
---
```

This enables version tracking so when Martin updates his prompt, the checklist can be updated without breaking existing preambles.

### 1. Updated Theory Section

Rewrite the theory section at the top of the file:
- Explain this is the AGNOSTIC version of Martin's checklist
- It captures the same 192 rules but written to apply to any technology stack
- Platform-specific preambles (e.g., `web-firebase.md`, `web-supabase.md`) are DERIVED from this by filling in the "Boilerplate Match" column with platform-specific details
- The agnostic version is the DEFAULT and the source of truth
- Preserve the Structural-Mechanism split explanation (still valid and important)
- Preserve the Preamble System explanation (still valid)

### 2. Table Format

Each category table must have these columns:

| # | Rule | Martin Says | Technical Spec (Agnostic) | Verification | Boilerplate Match | Type | Severity |
|---|------|-------------|---------------------------|--------------|-------------------|------|----------|

- **#** -- Original rule number (preserve exactly)
- **Rule** -- Short rule name (preserve from original)
- **Martin Says** -- Original quote (preserve VERBATIM, even if Firebase-specific)
- **Technical Spec (Agnostic)** -- Your agnostic rewrite (or original text if UNIVERSAL)
- **Verification** -- AUTOMATED/BUILD/MANUAL check with specific command or inspection steps
- **Boilerplate Match** -- Keep as `_[to be filled]_` (filled by a later agent)
- **Type** -- UNIVERSAL / STACK-SPECIFIC / PATTERN
- **Severity** -- CRITICAL / STANDARD / POLISH

### 3. All 18 Categories Preserved

Keep every category heading and every rule. Do not skip, merge, split, or reorder categories. The original structure must be preserved exactly so downstream agents can reference rules by category and number.

### 4. Banned Patterns Table

| # | Banned Pattern | Martin Says | Why Banned (Agnostic) | Verification | Type | Severity |
|---|----------------|-------------|----------------------|--------------|------|----------|

---

## Quality Checks Before You Finish

Run these checks on your output BEFORE considering the work done:

1. **Count check:** Count every rule row across all 18 category tables. Must equal ~192. Count every banned pattern row. Must equal ~43. If counts don't match the original, find what you missed.

2. **No orphaned stack references in Technical Spec column:** Search your "Technical Spec (Agnostic)" column for these terms: Firebase, Firestore, Google Auth, Google Sign-In, importmap, Lucide, `signInWithPopup`, `GoogleAuthProvider`, `serverTimestamp`, Cloud Functions, Realtime Database. NONE of these should appear in the Technical Spec column EXCEPT as parenthetical examples in PATTERN rules.

3. **Severity distribution sanity check:** Count your CRITICALs, STANDARDs, and POLISHes. Roughly 40/100/52. If the distribution is wildly different (e.g., 80 CRITICALs), re-examine your severity assignments -- you are probably being too aggressive with CRITICAL.

4. **No vague rewrites:** Search your Technical Spec column for these phrases: "handle properly," "manage appropriately," "use best practices," "as needed," "when necessary," "consider using." If any appear, rewrite with specific, implementable language.

5. **Every PATTERN rule has an example:** Every rule tagged PATTERN must include a "(e.g., ...)" with at least one specific implementation example showing how the abstract principle maps to a concrete technology.

---

## Success Criteria

Your output is complete when ALL of these are true:

- [ ] Output file exists at `docs/page-prds/prd-maker/martin-agnostic-checklist.md`
- [ ] Version header present at top (version: "1.0", source, date_created)
- [ ] Theory section updated to explain the agnostic version, Type/Severity/Verification system
- [ ] All ~192 rules present with original numbering preserved
- [ ] All ~43 banned patterns present
- [ ] Every rule has a Type tag (UNIVERSAL / STACK-SPECIFIC / PATTERN)
- [ ] Every rule has a Severity tag (CRITICAL / STANDARD / POLISH)
- [ ] Every rule has a Verification assertion (AUTOMATED / BUILD / MANUAL with specific check)
- [ ] ~100 rules have AUTOMATED verification (grep/lint commands)
- [ ] ~40 rules have BUILD verification (compiler/linter checks)
- [ ] ~50 rules have MANUAL verification (specific visual/functional inspection steps)
- [ ] All STACK-SPECIFIC rules rewritten to generic language in Technical Spec column
- [ ] All PATTERN rules have universal principle extracted + implementation example
- [ ] All UNIVERSAL rules preserved exactly as-is in both Martin Says and Technical Spec
- [ ] "Martin Says" column preserves original quotes verbatim for ALL rules
- [ ] No Firebase/Firestore/Google-specific terms in Technical Spec column (except as parenthetical examples in PATTERN rules)
- [ ] Severity distribution is approximately 40 CRITICAL / 100 STANDARD / 52 POLISH
- [ ] No vague or un-implementable language in any Technical Spec cell
- [ ] No vague verification assertions ("check the code" — must be specific commands or inspection steps)
- [ ] No rules deleted, merged, or invented -- exact same set as the original
