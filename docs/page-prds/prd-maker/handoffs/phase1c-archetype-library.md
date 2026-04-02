# Phase 1C: App Archetype Library

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Estimated effort:** Single session
> **Output:** `docs/page-prds/prd-maker/app-archetype-library.md`

---

## Your Mission

You are building the App Archetype Library -- a reference document that defines 8 common app archetypes and maps each one to the mechanism categories (A through N) it typically needs. This library is used during the PRD Maker pipeline's Stage 2 (Gap Analysis) to dramatically reduce the number of questions the system asks the user.

**The problem it solves:** Without archetypes, the gap analysis agent has to ask the user about ALL 14 mechanism categories (A-N), each with 5-7 sub-questions. That is 70-100 questions. Nobody will sit through that. With archetypes, the agent identifies what KIND of app the user is describing, loads the archetype's defaults, and only asks detailed questions about the categories that are ambiguous or unusual for that app type.

**Example:** If the user describes a "dashboard that shows my YouTube analytics," the system matches it to the Dashboard App archetype, which has Data Output (D) and Data Storage (B) as REQUIRED. The system does NOT need to ask "does your app need data output?" -- of course it does, it is a dashboard. Instead, it asks the SPECIFIC questions: "What metrics do you want to see?" and "Do you need real-time updates or is periodic refresh okay?"

---

## Files to Read

Read these files COMPLETELY before starting:

1. **`docs/page-prds/prd-maker/mechanism-identification-framework.md`** -- The full A-N mechanism category system with 14 categories, sub-types, and sub-questions for each. This is the system your archetypes will map to. You need to understand every category deeply to make accurate REQUIRED/OPTIONAL/UNLIKELY assignments.

2. **`docs/page-prds/prd-maker/research-reference.md`** -- Read the sections "The Periodic Table of App Mechanisms" and "The 30-Category Master Checklist" for additional context on how mechanisms and completeness categories work together.

3. **`docs/page-prds/prd-maker/build-game-plan.md`** -- Read section "1D. Create App Archetype Library" for confirmation of what you are building.

---

## The 8 Archetypes to Define

### 1. Dashboard App
Apps that display data, metrics, and analytics in a visual layout. The user primarily READS data, with limited write operations (filters, date ranges, settings).

### 2. Marketplace
Two-sided platforms connecting buyers and sellers (or providers and consumers). Involves listings, search, transactions, reviews, and trust systems.

### 3. Chat / Messaging App
Real-time communication between users. Could be 1:1, group, or channel-based. Core mechanic is sending and receiving messages with presence indicators.

### 4. CRUD / Tool
Utility apps focused on creating, reading, updating, and deleting structured data. Task managers, note apps, inventory trackers, CRM tools, spreadsheet-like apps.

### 5. Social Platform
Apps centered on user-generated content, social graphs (following/followers), feeds, and engagement (likes, comments, shares).

### 6. Wizard / Onboarding Flow
Step-by-step guided processes that collect information or walk users through a setup. Form-heavy, linear or branching progression, often with a final summary/confirmation.

### 7. Landing Page
Marketing or informational pages. Primarily static content with conversion-focused elements (CTAs, signup forms, pricing tables). Minimal backend logic.

### 8. SaaS Product
Subscription-based software with user accounts, feature tiers, admin panels, and ongoing usage. Combines multiple archetypes (usually CRUD + Dashboard + some unique value proposition).

---

## What to Define for Each Archetype

For each of the 8 archetypes, provide ALL of the following:

### a. One-Line Description
A single sentence that captures the essence. Used for quick matching during gap analysis.

### b. Mechanism Requirements (A-N)

For EACH of the 14 mechanism categories (A through N), classify it as:

| Classification | Meaning |
|----------------|---------|
| **REQUIRED** | This mechanism category is almost always needed for this archetype. If the user doesn't mention it, ASSUME it is needed and include the archetype's default sub-type. |
| **OPTIONAL** | This mechanism category is commonly but not always present. ASK the user if they need it. |
| **UNLIKELY** | This mechanism category is rarely needed for this archetype. Only include if the user specifically mentions it. Do NOT ask about it proactively. |

Present this as a table:

| Category | Name | Classification | Default Sub-type (if REQUIRED) | Notes |
|----------|------|---------------|-------------------------------|-------|
| A | Data Input | REQUIRED | Forms | Most dashboards need filter/config forms |
| B | Data Storage | REQUIRED | Relational DB or API | Data has to come from somewhere |
| ... | ... | ... | ... | ... |

**The "Default Sub-type" column is important.** When a category is REQUIRED, specify which sub-type is the archetype's default. This gives the gap analysis agent a starting point so it can ask "is standard form input enough, or do you also need file upload or voice input?" instead of asking about every sub-type from scratch.

**The "Notes" column is important.** Briefly explain WHY this classification makes sense for this archetype. One sentence max.

### c. Standard Pages

List the pages (routes/screens) that this archetype typically has. These are the DEFAULT pages -- the gap analysis agent uses this list to ask "which of these pages do you need, and what others?" instead of asking the user to invent pages from scratch.

Format as a bullet list:
- Page name -- one-sentence description of what this page does

### d. Example Apps

List 2-3 well-known real apps that fit this archetype. These serve as reference points the user can relate to.

Format:
- **App Name** -- 1-sentence description of what makes it fit this archetype

---

## The "How to Use" Section

After all 8 archetype definitions, include a section titled "## How to Use This Library" that explains the following process for an agent performing gap analysis:

1. **Match:** Read the user's raw idea description (from Stage 1). Identify which archetype(s) it most closely matches. An app can match MULTIPLE archetypes (e.g., a marketplace with a dashboard = Marketplace + Dashboard). If multiple match, union the REQUIRED categories from both.

2. **Load defaults:** For the matched archetype(s), load all REQUIRED mechanism categories with their default sub-types. These are pre-filled -- the user does NOT need to be asked about them unless their description contradicts the defaults.

3. **Ask about OPTIONAL:** For each OPTIONAL category, ask the user a single targeted question: "Does your app need [category name]? For example, [archetype-specific example]."

4. **Skip UNLIKELY:** Do NOT ask about UNLIKELY categories unless the user's description specifically mentions something that maps to one.

5. **Deep-dive on mentioned:** For any category the user DID mention in their rant (whether REQUIRED, OPTIONAL, or UNLIKELY), ask the sub-questions from the mechanism framework to get specifics.

6. **Handle no-match:** If the user's idea doesn't match any archetype well, fall back to asking about all 14 categories. Flag this as unusual and note it in the context packet.

7. **Handle hybrid:** If the user's idea matches 2+ archetypes, explain: "Your app looks like a combination of [Archetype A] and [Archetype B]. I am going to ask you about the areas where these archetypes overlap or conflict."

---

## Output File Structure

Create: **`docs/page-prds/prd-maker/app-archetype-library.md`**

```
# App Archetype Library

> Used during Stage 2 (Gap Analysis) to reduce questioning overhead.
> Match the user's description to an archetype, load defaults, ask only about gaps.
>
> 8 archetypes x 14 mechanism categories (A-N) = pre-mapped defaults for fast gap analysis.

---

## Archetype 1: Dashboard App

**One-line description:** [...]

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | ... | ... | ... |
[... all 14 categories ...]

### Standard Pages

- [page] -- [description]
- ...

### Example Apps

- **[App]** -- [description]
- ...

---

## Archetype 2: Marketplace

[same structure]

---

[... repeat for all 8 ...]

---

## How to Use This Library

[process described above]
```

---

## Rules for Your Work

1. **Every archetype must have ALL 14 categories classified.** Do not skip any category for any archetype. Even if a category is UNLIKELY, it must appear in the table marked as UNLIKELY.

2. **REQUIRED categories must have a default sub-type.** If something is required, specify which sub-type is the default starting point.

3. **Be honest about UNLIKELY.** Not everything is optional. A landing page does not need real-time chat. A CRUD tool does not need a marketplace commission system. Mark things as UNLIKELY when they genuinely are.

4. **Standard pages should be realistic.** List 4-8 pages per archetype. These should be pages that 80%+ of apps in this archetype actually have. Do not list every possible page -- list the STANDARD ones.

5. **Example apps should be well-known.** Use apps that a non-technical person would recognize. Avoid obscure developer tools.

6. **The "How to Use" section is for an AI agent, not a human.** Write it as clear instructions that another Claude agent can follow mechanically during gap analysis.

---

## Quality Checks Before You Finish

1. **Completeness:** 8 archetypes x 14 categories = 112 classification cells. Count them.
2. **Every REQUIRED has a default sub-type.** Scan all REQUIRED entries -- none should have an empty "Default Sub-type" column.
3. **Reasonable UNLIKELY count.** Each archetype should have at least 2-3 UNLIKELY categories. If an archetype has zero UNLIKELYs, you are being too permissive.
4. **No duplicate archetypes.** Each archetype should be clearly distinct from the others. If two archetypes have identical mechanism maps, one of them is redundant.
5. **Standard pages are specific.** "Dashboard" is too vague for a page name. "Analytics Dashboard" or "Revenue Overview" is specific.

---

## Success Criteria

- [ ] Output file exists at `docs/page-prds/prd-maker/app-archetype-library.md`
- [ ] All 8 archetypes are defined
- [ ] Each archetype has all 14 mechanism categories (A-N) classified as REQUIRED/OPTIONAL/UNLIKELY
- [ ] Every REQUIRED category has a default sub-type specified
- [ ] Each archetype has 4-8 standard pages listed
- [ ] Each archetype has 2-3 well-known example apps
- [ ] The "How to Use This Library" section is present with all 7 steps
- [ ] One-line descriptions are present for all 8 archetypes
- [ ] Notes column explains the reasoning for each classification
- [ ] The file header explains the purpose and relationship to Stage 2 gap analysis
