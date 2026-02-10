# Build Prompt - Supabase + Stripe App Builder

Personal build reference for Claude Code sessions. Drop this into any new project as `CLAUDE.md` when building apps on top of the [Gen-Ai boilerplate](https://github.com/digisurfsome/Gen-Ai).

## How to Use

1. Copy this file as `CLAUDE.md` into your new project root
2. Fill in Section 1 (App Identity) and Section 2 (Features)
3. Optionally generate a style guide with `STYLE_GUIDE_GENERATOR.md` and paste into Section 3
4. Start a Claude Code session - it reads this automatically

---

## SECTION 1: APP IDENTITY [FILL THIS IN]

**App Name:** [YOUR_APP_NAME]
**One-Line Description:** [What does this app do in one sentence?]
**Target User:** [Who is this for?]
**Core Problem:** [What pain point does this eliminate?]

---

## SECTION 2: FEATURES [FILL THIS IN]

**Core Features (3-5 max):**
1. [Feature 1 - be specific]
2. [Feature 2]
3. [Feature 3]

**What Users Can Do:**
- [Main action 1]
- [Main action 2]
- [Main action 3]

---

## SECTION 3: STYLE GUIDE [FILL IN OR PASTE FROM STYLE GENERATOR]

**Visual Style:** [Modern/Minimal/Playful/Corporate]
**Primary Brand Color:** [e.g., #DFFF5E]
**Secondary Color:** [e.g., #10B981]
**Personality/Tone:** [Friendly/Professional/Casual]
**Design Inspiration:** [e.g., "Like Linear" or "Clean SaaS dashboard"]

> When pasting a generated style guide, integrate tokens into the existing Tailwind + shadcn/ui theme config rather than creating a new one from scratch.

---

## SECTION 4: TECHNICAL STANDARDS [DO NOT MODIFY]

### Stack

- React 19 + TypeScript + Vite
- Tailwind CSS + shadcn/ui (49 components pre-installed)
- Supabase (auth, database, realtime, RLS)
- Stripe (checkout, webhooks, portal, credits)
- TanStack React Query for data fetching
- React Hook Form + Zod for forms
- Lucide React for icons

### What the Boilerplate Already Provides

**DO NOT rebuild these. Build ON TOP of them:**

- **Auth**: `AuthContext`, `ProtectedRoute`, sign-in/up/reset pages, Supabase client, Google + GitHub + email/password providers
- **Payments**: Stripe checkout, webhooks, customer portal, credit purchase flow
- **Credits**: `CreditContext`, `deductCredits`/`addCredits`, atomic DB operations
- **Admin**: 11-tab `AdminDashboard` (user management, audit logs, plan management)
- **Layouts**: `PublicLayout`, `AuthLayout`, `DashboardLayout` with `Sidebar` + `Header`
- **Theme**: `ThemeProvider` + `ThemeToggle` (dark/light/system) - already wired
- **Email**: Resend integration with invitation templates
- **UI Components**: All 49 shadcn/ui components in `src/components/ui/`
- **Database**: 13+ tables with RLS policies, triggers, stored functions
- **Profiles**: User profile management with avatar upload

### Where You Build

- New routes: `src/App.tsx`
- New pages: `src/pages/`
- New components: `src/components/` (feature-grouped folders)
- New API/DB functions: `src/api/` or `src/lib/`
- New migrations: `supabase/migrations/`
- Navigation: Update `Sidebar` component

### File Organization

```
src/
  components/
    ui/              # shadcn/ui (pre-built, don't touch)
    [FeatureName]/   # Group by feature
  pages/             # Route-level components
  hooks/             # Custom hooks
  api/               # Supabase query functions
  lib/               # Utilities, helpers, Supabase client
  types/             # TypeScript interfaces
  contexts/          # React contexts (auth, credits, theme pre-built)
```

One component per file. Group related components in feature folders. Define TypeScript interfaces for all data types.

### Supabase Patterns

**Client (already configured in boilerplate):**
```ts
import { supabase } from '@/lib/supabase'
```

**Queries - always use the service layer, never call Supabase from components:**
```ts
// api/items.ts
export const getItems = async (userId: string) => {
  const { data, error } = await supabase
    .from('items')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
  if (error) throw error
  return data
}

export const createItem = async (userId: string, item: Omit<Item, 'id' | 'created_at'>) => {
  const { data, error } = await supabase
    .from('items')
    .insert({ ...item, user_id: userId })
    .select()
    .single()
  if (error) throw error
  return data
}

export const updateItem = async (id: string, updates: Partial<Item>) => {
  const { data, error } = await supabase
    .from('items')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single()
  if (error) throw error
  return data
}

export const deleteItem = async (id: string) => {
  const { error } = await supabase.from('items').delete().eq('id', id)
  if (error) throw error
}
```

**Use TanStack Query for data fetching in components:**
```ts
const { data: items, isLoading, error } = useQuery({
  queryKey: ['items', userId],
  queryFn: () => getItems(userId),
})
```

**Realtime subscriptions:**
```ts
useEffect(() => {
  const channel = supabase
    .channel('items-changes')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'items',
      filter: `user_id=eq.${userId}`,
    }, (payload) => {
      queryClient.invalidateQueries({ queryKey: ['items', userId] })
    })
    .subscribe()
  return () => { supabase.removeChannel(channel) }
}, [userId])
```

**RLS policies - every new table needs these:**
```sql
-- Migration file: supabase/migrations/YYYYMMDDHHMMSS_create_items.sql
create table items (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  title text not null,
  description text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

alter table items enable row level security;

create policy "Users can view own items"
  on items for select using (auth.uid() = user_id);
create policy "Users can insert own items"
  on items for insert with check (auth.uid() = user_id);
create policy "Users can update own items"
  on items for update using (auth.uid() = user_id);
create policy "Users can delete own items"
  on items for delete using (auth.uid() = user_id);
```

**Auth (pre-built - use the existing context):**
```ts
import { useAuth } from '@/contexts/AuthContext'

const { user, userProfile, isAdmin, signOut } = useAuth()
```

**Credits (pre-built - use the existing context):**
```ts
import { useCredits } from '@/contexts/CreditContext'

const { credits, deductCredits, hasEnoughCredits } = useCredits()

// Before expensive operations
if (!hasEnoughCredits(cost)) {
  toast.error('Not enough credits')
  return
}
await deductCredits(cost)
```

### UI/UX Standards

#### Banned - Never Use
- `alert()`, `confirm()`, `prompt()` - use Toast/Dialog/AlertDialog from shadcn
- `console.log` for user feedback - use Toast
- Text-only empty states - use icon + message + CTA
- Browser default dialogs

#### Required Components (use shadcn/ui versions)
- **Dialog** - for confirmations, forms
- **AlertDialog** - for destructive action confirmations
- **Toast** (via sonner) - success/error notifications
- **Skeleton** - loading placeholders
- **Button** - with loading state (disabled + spinner)
- **Avatar** - with fallback initials

#### Page Pattern for User Data

Every data type needs four views as **separate routes**:

| View | Route | Purpose |
|------|-------|---------|
| List | `/items` | Cards/table, "Create New" button, search/filter |
| Detail | `/items/:id` | Read-only display, Edit/Delete buttons |
| Create | `/items/new` | Form, Save -> Detail, Cancel -> List |
| Edit | `/items/:id/edit` | Pre-filled form, Save -> Detail, Cancel -> Detail |

**Anti-patterns - never do these:**
- Clicking item opens edit mode directly (must open Detail first)
- Using Create form as Edit form by pre-loading data
- Single component that handles both view and edit
- Delete without AlertDialog confirmation
- Success/error without Toast feedback
- Empty lists with just "No items" text

#### Feedback Protocol

| Event | Action |
|-------|--------|
| Success | Toast + navigate to appropriate view |
| Error | Toast + stay on current view + keep form data |
| Delete | AlertDialog -> loading state -> Toast + redirect to List |
| Loading lists | Skeleton cards (not spinner) |
| Loading detail | Skeleton matching content shape |
| Button during action | Spinner inside button + disabled |

### Polish Requirements

All of these are mandatory. Not optional.

**Dates**: Never show raw timestamps. Use relative time: "Just now", "5m ago", "2h ago", "Yesterday", "3d ago", "Jan 15".

**Text truncation**: Long text uses `truncate` (single line) or `line-clamp-2` (multi-line) with `max-w-` set.

**Back navigation**: Every detail/edit page has a back button/link at top.

**Hover states**: Every clickable element has visual hover feedback.

**Focus states**: All interactive elements have `focus-visible:ring-2 focus-visible:ring-ring`.

**Escape key**: Dialogs/modals close on Escape.

**Aria labels**: Icon-only buttons have `aria-label`.

**Screen reader text**: Loading states have `<span className="sr-only">`.

**Form labels**: Every input has a visible label.

**Autofocus**: First input focused when form/dialog opens.

**Pluralization**: Never "1 items". Handle singular/plural: `${count} ${count === 1 ? 'item' : 'items'}`.

**Search/filter**: Any list that can grow beyond 5 items needs search.

**Retry on error**: Error states show a retry button, not a dead end.

**Unsaved changes**: Forms with changes warn before navigation (`beforeunload`).

**404 handling**: Route-level `*` catch-all + data-level "not found" empty state.

**Touch targets**: Minimum 44px x 44px for all clickable elements on mobile.

**Page titles**: Every page sets `document.title` via a `usePageTitle` hook.

**Console clean**: Zero errors or warnings in production.

### Responsive Design

Build mobile-first. Design for mobile, then scale up.

| Breakpoint | Width | Use |
|------------|-------|-----|
| default | < 640px | Mobile styles |
| `sm:` | >= 640px | Tablet |
| `lg:` | >= 1024px | Desktop |

**Layout behavior:**
- Mobile: Sidebar hidden, hamburger toggle, full-width content
- Desktop: Sidebar visible (240px), content fills remaining space

**Component rules:**
- Cards: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`
- Forms: Full width mobile, `max-w-md` desktop
- Primary buttons: Full width mobile, auto width desktop
- Dialogs: Nearly full screen mobile, centered `max-w-md` desktop
- Text: Minimum 16px on mobile

### Design System

**Typography:**

| Element | Class |
|---------|-------|
| Page Title | `text-2xl font-semibold` |
| Section Header | `text-lg font-semibold` |
| Card Title | `text-base font-medium` |
| Body Text | `text-sm text-muted-foreground` |
| Small/Meta | `text-xs text-muted-foreground` |

**Spacing:**
- Base unit: 4px (Tailwind default)
- Card padding: `p-6`
- Section gaps: `gap-6`
- Element gaps: `gap-4`

**Cards:**
```
rounded-lg border bg-card text-card-foreground shadow-sm p-6
```

**Animations (subtle):**
- Dialogs: fade backdrop + scale content
- Toasts: slide from top-right
- Cards: `hover:shadow-md hover:-translate-y-0.5 transition-all`
- Buttons: `active:scale-[0.98] transition-all`

### Coding Standards

- **TypeScript**: Define interfaces for all data. No `any`. No `@ts-ignore`.
- **One component per file**: Name matches export.
- **Service layer**: All Supabase calls in `api/` files, never in components.
- **React Query**: Use for all server state. Invalidate after mutations.
- **Error handling**: Wrap Supabase calls, throw meaningful errors. Catch in components, show Toast.
- **No inline styles**: Tailwind only.
- **No unprotected routes**: Wrap authenticated pages in `ProtectedRoute`.

### Error Handling Pattern

```ts
// In API layer
try {
  const { data, error } = await supabase.from('items').select()
  if (error) throw error
  return data
} catch (error: any) {
  if (error.code === 'PGRST116') throw new Error('Item not found')
  if (error.code === '42501') throw new Error('Permission denied')
  throw new Error('Something went wrong. Please try again.')
}

// In components
const mutation = useMutation({
  mutationFn: createItem,
  onSuccess: () => {
    toast.success('Item created')
    queryClient.invalidateQueries({ queryKey: ['items'] })
    navigate(`/items/${data.id}`)
  },
  onError: (error) => {
    toast.error(error.message)
  },
})
```

### Checklist Before Shipping

- [ ] All routes protected appropriately
- [ ] RLS policies on every new table
- [ ] Loading states (Skeleton) on all data-dependent views
- [ ] Empty states with icon + CTA on all lists
- [ ] Toast feedback on all mutations
- [ ] AlertDialog on all destructive actions
- [ ] Search/filter on lists
- [ ] Back navigation on detail/edit pages
- [ ] Mobile responsive (test at 375px width)
- [ ] Dark mode works (test toggle)
- [ ] Zero console errors
- [ ] All forms validate before submit
- [ ] Credits deducted for paid features (if applicable)
