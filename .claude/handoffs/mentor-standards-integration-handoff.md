# Handoff: Integrate Mentor's Build Standards into AutoForge

## Overview

AutoForge has a coding prompt template that guides the AI agent when building apps. It already has some quality checks (STEP 5.5 verification checklist), but it's missing about 15 specific rules from a professional build standards system. These rules need to be added to the coding prompt and related files so that EVERY app AutoForge builds follows professional standards automatically.

Additionally, the spec creation flow needs to incorporate identity-first questioning and MVP scoping rules.

This is NOT a UI redesign. This is adding rules and standards to the PROMPTS and TEMPLATES that AutoForge uses when building apps.

---

## Part 1: Add Missing Rules to Coding Prompt Template

**File: `.claude/templates/coding_prompt.template.md`**

### What Already Exists (STEP 5.5 Verification Checklist, ~line 142)

The checklist already covers:
- Security (auth, permissions, cross-user data)
- Real Data (no mocks, persistence)
- Navigation (routes, 404s, back button)
- Integration (console errors, network, loading/error states)
- UI Polish (no alert(), skeletons, confirmation modals, toasts, empty states, relative dates, truncation)
- Accessibility (focus rings, aria-labels, escape key, labels)

### What's MISSING — Add These Rules

**Add a new section between STEP 4 (Implement) and STEP 5 (Verify). Call it "STEP 4.5: CODING STANDARDS (MANDATORY)":**

```markdown
### STEP 4.5: CODING STANDARDS (MANDATORY)

Follow these rules for ALL code you write:

**Architecture:**
1. NO database calls in components — create a service layer (`src/services/`) for all backend operations. Components call services, never databases directly.
2. ALL database writes must include `createdAt` and `updatedAt` timestamps.
3. ALL user data must be scoped to the authenticated user (filter by userId in queries).
4. Wrap the app root in an ErrorBoundary component that catches and displays errors gracefully.

**TypeScript:**
5. NO `any` types — define explicit TypeScript interfaces in `src/types/`.
6. ALL shared types go in `src/types/index.ts`, not scattered across files.

**Styling:**
7. NO inline styles — use Tailwind CSS classes only.
8. Use CSS variables for dark/light mode (dark-first approach).
9. Use Lucide React for ALL icons (import from `lucide-react`).

**UI Components (create these if they don't exist):**
10. Detail View (read-only) SEPARATE from Edit View — never combine them.
11. All pages set the document title via a `usePageTitle` hook:
    ```typescript
    // src/hooks/usePageTitle.ts
    export function usePageTitle(title: string) {
      useEffect(() => {
        document.title = title ? `${title} - AppName` : 'AppName';
      }, [title]);
    }
    ```
12. All forms autofocus the first input field.
13. All lists with more than 5 expected items must have search/filter.
14. All error states must include a retry action (not just "Error occurred").
15. Unsaved form changes must trigger a `beforeunload` warning.

**Navigation Pattern:**
Follow this flow for all CRUD features:
```
LIST → click item → DETAIL (read-only) → click edit → EDIT → save → DETAIL
LIST → click new  → CREATE → save → DETAIL
DETAIL → delete (with ConfirmModal) → LIST
```
All detail pages must have back navigation.
```

### Also Update STEP 5.5 Verification Checklist

Add these checks to the existing checklist at ~line 142:

```markdown
- **Architecture:** No database calls in components (only in services/); ErrorBoundary wraps app root; all DB writes have createdAt/updatedAt; user data scoped by userId
- **TypeScript:** No `any` types in src/ (grep for `: any` and `as any`); interfaces in src/types/
- **Forms:** First input autofocused; beforeunload warning for unsaved changes; validation before submit
- **Lists:** Search/filter present when list could have > 5 items
- **Navigation:** Detail View separate from Edit View; back navigation on all detail pages; List→Detail→Edit flow
- **Page Titles:** Every page calls usePageTitle with a descriptive title
```

---

## Part 2: Add Design System to Style Guide Generation

**File: `server/services/style_manager.py`**

The style guide generator creates `.autoforge/style_guide.md` for each project. It already includes color tokens, typography, and component patterns per style. BUT it doesn't include the universal design system rules that apply regardless of which style is chosen.

### What to Add

Find the function `get_style_guide_markdown()` (around line 1200+). After the style-specific content, add a new section to the generated markdown:

```markdown
## Universal Design Standards

### Typography Scale
| Element | Size | Weight | Usage |
|---------|------|--------|-------|
| Page Title | 24px (text-2xl) | Semi-bold | One per page, top of content area |
| Section Header | 18px (text-lg) | Semi-bold | Group related content |
| Card Title | 16px (text-base) | Medium | Card headers, list item titles |
| Body Text | 14px (text-sm) | Regular | Default readable text |
| Small/Meta | 12px (text-xs) | Regular | Timestamps, counts, labels |

### Spacing System (8px grid)
- Card padding: p-6 (24px)
- Section gaps: gap-6 (24px)
- Element gaps within sections: gap-4 (16px)
- Tight gaps (icon + text): gap-2 (8px)

### Layout Structure
- Sidebar: 240px wide, bg-surface-base, border-r border-border-subtle
- Header: Full width, h-16, bg-surface-base, border-b border-border-subtle
- Main content: flex-1, overflow-y-auto, p-8
- Max content width: max-w-7xl mx-auto (for wide layouts)

### Responsive Breakpoints (mobile-first)
- Default: Mobile (< 640px)
- sm: Tablet (640px+)
- lg: Desktop (1024px+)
- All touch targets: minimum 44x44px

### Component Patterns
Cards:
```html
<div class="bg-surface-base rounded-xl border border-border-subtle shadow-sm p-6">
```

Primary Button:
```html
<button class="bg-brand hover:bg-brand-dark text-white font-medium px-6 py-3 rounded-lg transition-colors">
```

Input:
```html
<input class="bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand" />
```
```

---

## Part 3: Add Identity-First Questions to Spec Creation

**Files:**
- `.claude/commands/create-spec.md` — the slash command prompt
- `server/services/spec_chat_session.py` — the WebSocket chat for spec creation
- `server/routers/spec_creation.py` — the spec creation router

### What to Change

The spec creation flow currently asks the user to describe their app and then generates features. It needs to REQUIRE four identity fields before allowing feature definition:

1. **App Name** — short, memorable
2. **One-Line Description** — what it does in one sentence
3. **Target User** — who is this for? (specific about their situation)
4. **Core Problem** — what pain point does this eliminate?

### In `create-spec.md`

Add to the system prompt for the spec creation agent:

```markdown
## IDENTITY FIRST (MANDATORY)

Before discussing ANY features, you MUST establish these 4 fields:

1. **App Name**: Ask for a short, memorable name
2. **One-Line Description**: What does this app do in one sentence?
3. **Target User**: Who specifically is this for? (not just "users" — be specific about their situation, age, profession, pain level)
4. **Core Problem**: What specific pain point does this eliminate?

Do NOT proceed to features until all 4 are answered. If the user jumps ahead to features, gently redirect: "Love the feature ideas! But first, let's nail down who exactly this is for..."

## MVP SCOPING RULES

- Maximum 5 core features for the MVP
- Each feature must be ONE clear thing (not bundled)
- Don't list infrastructure (auth, responsive, dark mode) — those are built into the boilerplate automatically
- If the user lists more than 5 features, help them prioritize: "These are all great — which 5 are the MUST-HAVES for launch?"
- Focus on what makes the app UNIQUE, not table-stakes features
```

### In `spec_chat_session.py`

Find the system prompt that initializes the chat session. Add the identity-first and MVP scoping instructions to it. The chat session should track whether the 4 identity fields have been established and include them in the final `app_spec.txt` output:

```xml
<app_overview>
  <name>AppName</name>
  <description>One-line description</description>
  <target_user>Specific target user</target_user>
  <core_problem>Pain point being solved</core_problem>
  ...
</app_overview>
```

---

## Part 4: Add Feature Description Dual Format

**File: `.claude/templates/coding_prompt.template.md`**

When the initializer creates features, each feature should have BOTH:
1. **Technical description**: What the system does
2. **User action description**: What the user can do (plain English)

This improves the coding agent's understanding of the feature's purpose.

### What to Change

In the initializer prompt template (`.claude/templates/initializer_prompt.template.md`), add to the feature creation instructions:

```markdown
For each feature, provide TWO descriptions:
- **description**: Technical capability (e.g., "Scale recipe servings with auto-calculated ingredient quantities")
- **user_action**: Plain English (e.g., "Users can adjust serving sizes and see updated measurements instantly")

The coding agent uses the technical description for implementation and the user_action for verification — it tests whether a real user could actually do what's described.
```

---

## Files to Modify (Summary)

| File | Change |
|---|---|
| `.claude/templates/coding_prompt.template.md` | Add STEP 4.5 with 15 coding standards + update STEP 5.5 checklist |
| `.claude/templates/initializer_prompt.template.md` | Add dual description format for features |
| `server/services/style_manager.py` | Add universal design system to generated style guides |
| `.claude/commands/create-spec.md` | Add identity-first questions + MVP scoping rules |
| `server/services/spec_chat_session.py` | Add identity-first tracking to chat session |

## What NOT To Do

- Do NOT change any existing UI components in `ui/src/components/` — this handoff is about the TEMPLATES and PROMPTS, not AutoForge's own UI
- Do NOT modify the style definitions in `style_manager.py` (STYLE_REGISTRY) — only add to the generated markdown output
- Do NOT remove any existing checklist items from STEP 5.5 — only ADD new ones
- Do NOT change the feature database schema — the dual description goes in the existing `description` field as structured text
- Keep all changes backward-compatible — existing projects should still work fine
