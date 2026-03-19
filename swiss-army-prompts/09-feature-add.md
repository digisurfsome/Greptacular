# MODULE 09: FEATURE ADD PROMPT

## Adding Features to an Existing App

**What this does:** A repeatable prompt for adding any new feature to an app that's already built. Whether it's a new entity, a new page, an integration, a filter system, export functionality — this prompt ensures the new feature follows the existing patterns instead of creating an inconsistent mess.

**When to use:** Any time you want to add something to a working app. This is the prompt you'll use the most after the initial build.

---

## --- START PROMPT ---

## TASK: Add a New Feature to This Existing App

You are adding a feature to an existing, working application. Your #1 priority is **consistency with what already exists.** Do not introduce new patterns, new libraries, new file structures, or new conventions. Match what's already there.

---

## SECTION 1: FEATURE DESCRIPTION [FILL THIS IN]

**What I want to add:**
[Describe the feature in plain language. Be specific about what the user should be able to do.]

**Where it fits in the app:**
[New page? New section on existing page? New button? New modal? Sidebar item?]

**What data does it need?**
[New database table? New fields on existing table? No new data? Uses existing data differently?]

**Who can access it?**
[All users / Pro only / Admin only / Public (no auth)]

---

## SECTION 2: PRE-FLIGHT CHECKLIST (DO THIS FIRST)

Before writing a single line of code, research the existing codebase:

### 2A: Understand the Architecture

Read and list the patterns used in:

1. **File structure** — Where do pages go? Components? Hooks? Services?
2. **Routing** — How are routes defined in App.tsx? What's the URL pattern?
3. **Data fetching** — How do existing pages fetch data? Direct Supabase calls or service layer?
4. **State management** — React Context? Local state? What pattern?
5. **Component library** — What reusable components exist in `components/ui/`?
6. **Styling** — What design tokens are used? What's the card/button/input pattern?
7. **Error handling** — How do existing pages handle errors? Toast? Inline?
8. **Loading states** — Skeleton? Spinner? What pattern?

**List each pattern with the file that exemplifies it.** This is your reference for building the new feature.

### 2B: Check for Conflicts

- Will this feature affect any existing routes?
- Will it modify any shared components?
- Does it need new dependencies? (If yes, justify why an existing dependency can't do it)
- Does it need new database tables? (If yes, we follow Module 03 patterns)
- Does it conflict with any existing feature?

### 2C: Plan the Changes

List every file you'll create or modify:

```
CREATE:
- src/pages/NewFeaturePage.tsx
- src/components/NewFeature/FeatureCard.tsx
- ...

MODIFY:
- src/App.tsx (add route)
- src/components/Sidebar.tsx (add nav link)
- src/services/database.ts (add service functions)
- src/types/index.ts (add types)
- ...
```

**Tell me this plan before you start coding.** I want to approve the approach.

---

## SECTION 3: IMPLEMENTATION RULES

### Rule 1: Match Existing Patterns EXACTLY

If existing pages fetch data like this:
```typescript
const [items, setItems] = useState<Item[]>([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  getItems(user.id).then(setItems).finally(() => setLoading(false))
}, [user])
```

Then your new page fetches data the SAME way. Not with React Query. Not with SWR. Not with a custom hook (unless custom hooks already exist). The same way.

### Rule 2: Use Existing Components

Check `src/components/ui/` before building anything new:

- Need a modal? Use `Modal.tsx`
- Need a confirmation? Use `ConfirmModal.tsx`
- Need a button? Use `Button.tsx`
- Need a card? Use `Card.tsx`
- Need loading states? Use `Skeleton.tsx`
- Need empty state? Use `EmptyState.tsx`
- Need to show a toast? Use `useToast()` hook

**NEVER** recreate a component that already exists, even if you'd make it "slightly different." Use what's there.

### Rule 3: Follow the CRUD Pattern (If Applicable)

If the feature involves creating/viewing/editing/deleting something, follow the exact flow from Module 05:

```
List Page → Detail Page → Create Page → Edit Page
```

Don't combine these. Don't skip the detail page. Don't make create and edit the same component.

### Rule 4: Database Changes Follow Module 03

If the feature needs new tables:
1. Write the SQL (CREATE TABLE, RLS policies, triggers)
2. Print it for me to run in Supabase SQL Editor
3. Update `src/types/supabase.ts` and `src/types/index.ts`
4. Add service functions to `src/services/database.ts`

### Rule 5: No New Dependencies Without Justification

If you think a new npm package is needed, you must:
1. Explain what it does
2. Explain why the feature can't be built without it
3. Confirm it's well-maintained (>1000 GitHub stars, updated within 6 months)
4. Get my approval before installing

### Rule 6: Mobile First

New UI must work on mobile (375px), tablet (768px), and desktop (1280px).

### Rule 7: Dark Mode

New UI must work in both light and dark mode. Use design token classes, never hardcoded colors.

---

## SECTION 4: IMPLEMENTATION ORDER

Build the feature in this order:

1. **Types** — Add interfaces to `types/index.ts`
2. **Database** — SQL + service functions (if needed)
3. **Core logic** — Hooks, context (if needed)
4. **UI components** — Feature-specific components
5. **Pages** — The actual pages
6. **Routing** — Add to App.tsx
7. **Navigation** — Add to Sidebar, update Dashboard
8. **Polish** — Loading states, error states, empty states, hover effects
9. **Verify** — Build check, console check, responsive check, dark mode check

---

## SECTION 5: VERIFY

1. `npm run build` — zero errors
2. `npm run dev` — test the new feature end-to-end
3. Test existing features — make sure nothing broke
4. DevTools Console — zero new errors
5. Mobile layout — new pages work at 375px
6. Dark mode — new pages look correct

---

## COMMIT

```bash
git add -A
git commit -m "feat: add [feature name] — [brief description of what it does]"
```

---

## --- END PROMPT ---
