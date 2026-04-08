# D2D Boilerplate: App Builder Prompt Template

> Adapted from Martin's original build prompt for the D2D (Next.js + Supabase + Stripe) boilerplate.
> The original targets vanilla React + Firebase via importmaps.
> This version targets the D2D stack: Next.js 16+, Supabase, shadcn/ui, Stripe, pnpm.


## How To Use This Template


**Step 1: Clarify Your App Idea (Optional)**
- Have a rough idea but not sure how to describe it?
- Use the **App Idea Generator Prompt** (separate file) to structure it
- Paste the output into Sections 1 & 2 below


**Step 2: Generate Your Style Guide (Optional but Recommended)**
- Find a screenshot of an app/website whose visual style you love
- Use the **Style Guide Generator Prompt** (separate file) with that image
- Paste the output into Section 3 below


**Step 3: Fill In Any Remaining Details**
- Review Sections 1, 2, and 3
- Fill in anything that's still blank


**Step 4: Generate Your App**
- Copy everything below "THE PROMPT" line
- Paste into Claude Code
- Clone the D2D boilerplate first


**DO NOT MODIFY Section 4** - these are the technical guardrails that make it work.


---


# THE PROMPT (Copy Everything Below This Line)


---


## SECTION 1: APP IDENTITY [FILL THIS IN]


**App Name:** [YOUR_APP_NAME]


**One-Line Description:** [What does this app do in one sentence?]


**Target User:** [Who is this for? Be specific]


**Core Problem It Solves:** [What pain point does this eliminate?]


---


## SECTION 2: FEATURES [FILL THIS IN]


**Core Features (3-5 max):**
1. [Feature 1 - be specific about what it does]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4 - optional]
5. [Feature 5 - optional]


**What Users Can Do:**
- [Main action 1 - e.g., "Create and save recipes"]
- [Main action 2 - e.g., "Organize recipes into collections"]
- [Main action 3 - e.g., "Search their saved recipes"]


---


## SECTION 3: STYLE GUIDE [FILL THIS IN OR PASTE FROM STYLE GENERATOR]


*Tip: Use the Style Guide Generator Prompt with a screenshot of an app you like, then paste the output here.*


**Visual Style:** [Modern/Minimal/Playful/Corporate]


**Primary Brand Color:** [e.g., #DFFF5E or "electric lime"]


**Secondary Color:** [e.g., #10B981 or "emerald green"]


**Personality/Tone:** [Friendly/Professional/Casual/Serious]


**Design Inspiration:** [Optional - "Like Notion" or "Like Linear" or "Clean SaaS dashboard"]


---


## SECTION 4: TECHNICAL REQUIREMENTS [DO NOT MODIFY]


### STACK (MANDATORY)

```
- Next.js 16+ with App Router and TypeScript
- React 19 with Server Components
- Tailwind CSS v4 for all styling (OKLCH color tokens)
- Supabase Auth (email/password, Google OAuth, GitHub OAuth)
- Supabase PostgreSQL for database (with Row Level Security)
- shadcn/ui (New York style) for all UI components
- Lucide React for all icons
- next-themes for dark mode
- Supabase Edge Functions for backend logic
- Stripe for payments (checkout, subscriptions, billing portal)
- NO custom Express/FastAPI/Django servers
- NO Redux, Zustand, Jotai, or external state libraries
- NO Docker
```

You are building ON TOP of an existing boilerplate. The auth, payments, landing page, and account management already work. Your job is to add the app-specific features described in Sections 1 and 2 without breaking what already exists.


### FILE STRUCTURE (D2D BOILERPLATE - EXPAND AS NEEDED)

```
nextjs/
├── app/
│   ├── api/
│   │   ├── auth_callback/route.ts
│   │   ├── og/route.tsx
│   │   └── reset_password/route.ts
│   ├── auth/[id]/page.tsx
│   ├── account/page.tsx
│   ├── dashboard/              # ADD: Main authenticated view
│   │   └── page.tsx
│   ├── [items]/                # ADD: CRUD routes per entity
│   │   ├── page.tsx            # List view
│   │   ├── new/page.tsx        # Create view
│   │   └── [id]/
│   │       ├── page.tsx        # Detail view
│   │       └── edit/page.tsx   # Edit view
│   ├── layout.tsx
│   ├── page.tsx
│   ├── not-found.tsx           # 404 page
│   ├── error.tsx               # Error boundary
│   ├── PostHogPageView.tsx
│   └── providers.tsx
├── components/
│   ├── icons/
│   ├── landing/
│   ├── misc/
│   ├── ui/                     # shadcn/ui (ALREADY EXISTS)
│   │   ├── dialog.tsx          # Modal replacement
│   │   ├── alert-dialog.tsx    # ConfirmModal replacement
│   │   ├── toast.tsx           # Toast notifications
│   │   ├── button.tsx          # With loading state
│   │   ├── avatar.tsx          # With fallback
│   │   ├── skeleton.tsx        # Loading placeholders
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── sheet.tsx           # Mobile sidebar
│   ├── [FeatureName]/          # ADD: Feature-specific components
│   └── layout/                 # ADD: Layout components
│       ├── Sidebar.tsx
│       ├── MobileNav.tsx
│       └── EmptyState.tsx      # ADD: Not in shadcn
├── lib/
│   ├── utils.ts
│   ├── formatDate.ts           # ADD: Date formatting
│   └── pluralize.ts            # ADD: Pluralization helper
├── utils/
│   ├── supabase/               # ALREADY EXISTS - DO NOT MODIFY
│   │   ├── server.ts
│   │   ├── client.ts
│   │   ├── middleware.ts
│   │   ├── api.ts
│   │   ├── admin.ts
│   │   └── queries.ts
│   ├── types.ts
│   └── helpers.ts
├── styles/main.css
├── types_db.ts                 # AUTO-GENERATED - DO NOT EDIT
├── middleware.ts               # Auth redirect - DO NOT MODIFY
└── components.json

supabase/
├── config.toml
├── migrations/
│   ├── 20240717231009_init.sql
│   └── [YYYYMMDD]_[name].sql  # ADD: New migrations per feature
└── functions/
    ├── _shared/
    ├── get_stripe_url/
    ├── stripe_webhook/
    └── on_user_modify/
```

**File rules:** One component per file. Group related components in feature folders under `components/[FeatureName]/`. Create TypeScript interfaces for all data types. Add utility functions to `lib/` for reusable logic. Server Components by default; add `'use client'` only when you need interactivity.

⚠️ **Files marked "ALREADY EXISTS" or "DO NOT MODIFY" are part of the boilerplate. Touching them will break auth, payments, or both. If you think you need to modify them, you are wrong. Build around them.**


### DEPENDENCY MANAGEMENT

pnpm manages all dependencies. The `pnpm-lock.yaml` is the lockfile.

⚠️ **CRITICAL: DO NOT add dependencies without explicit approval.**
⚠️ **DO NOT modify pnpm-lock.yaml manually.**
⚠️ **To add a shadcn component:** `npx shadcn@latest add [component-name]`
⚠️ **To add an npm package:** `pnpm add [package-name]`

The boilerplate already includes everything you need for auth, payments, theming, and UI primitives. Before reaching for a new package, check if shadcn/ui or the existing utilities already solve it. Nine times out of ten, they do.


### SUPABASE CLIENT CONFIGURATION

The D2D boilerplate provides four Supabase client utilities. Each one exists for a specific execution context. Using the wrong one will cause auth failures, hydration mismatches, or security holes.

```typescript
// ⚠️ CRITICAL: DO NOT create Supabase clients directly.
// Use the appropriate utility for your context:

// Server Components (data fetching):
import { createClient } from '@/utils/supabase/server'
const supabase = await createClient()

// Client Components (interactive):
import { createClient } from '@/utils/supabase/client'
const supabase = createClient()

// Middleware (session refresh) — ALREADY CONFIGURED, DO NOT TOUCH:
// utils/supabase/middleware.ts

// Auth operations (signin, signup, etc.):
import { createApiClient } from '@/utils/supabase/api'

// Admin/service role (server-to-server, webhooks):
import { createAdminClient } from '@/utils/supabase/admin'
```

⚠️ **NEVER `import { createClient } from '@supabase/supabase-js'` directly.** Always go through the utility wrappers. They handle cookie-based auth, server-side token refresh, and SSR hydration. If you bypass them, auth will silently break — users will appear logged out on refresh, or worse, see each other's data.

⚠️ **Server vs. Client is not optional.** `@/utils/supabase/server` uses `cookies()` and only works in Server Components, Route Handlers, and Server Actions. `@/utils/supabase/client` uses the browser's cookie jar. Mixing them up will crash at runtime.


### AUTH PATTERN

The D2D boilerplate handles auth through Supabase's middleware-based session management. There is no AuthContext. There is no client-side auth state wrapper. The middleware refreshes the session on every request, and you read the user from the server.

**Middleware-based session refresh (already exists — DO NOT MODIFY):**

`middleware.ts` at the project root intercepts every request, refreshes the Supabase session cookie, and redirects unauthenticated users away from protected routes. This is the single source of truth for "is this user logged in."

**Server Component session check (this is how you protect pages):**

```typescript
import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'

export default async function ProtectedPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/signin')

  return <YourPageContent user={user} />
}
```

That's it. No loading spinners. No context providers. No `useEffect` dance. The page either renders with a user or redirects. Server Components make auth checks synchronous from the user's perspective.

**Client-side reactivity (only when you need real-time auth changes):**

For the rare case where you need to react to auth state changes in the browser (e.g., sign-out across tabs), use `onAuthStateChange`:

```typescript
'use client'
import { createClient } from '@/utils/supabase/client'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function AuthListener() {
  const supabase = createClient()
  const router = useRouter()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event) => {
        if (event === 'SIGNED_OUT') router.push('/auth/signin')
        if (event === 'SIGNED_IN') router.refresh()
      }
    )
    return () => subscription.unsubscribe()
  }, [supabase, router])

  return null
}
```

**AuthForm component (already exists at `components/misc/AuthForm.tsx`):**

The boilerplate ships with a complete auth form that handles all auth states. Do not rebuild it. The supported states are:

- `signin` — Email/password login + OAuth buttons (Google, GitHub)
- `signup` — Registration with email confirmation
- `forgot_password` — Password reset email
- `update_password` — New password form (after reset link)
- `verify_email` — Email verification pending screen

These are routed via `/auth/[id]` where `[id]` is the state name (e.g., `/auth/signin`, `/auth/signup`).

**User profile type:**

```typescript
// From types_db.ts (auto-generated from your Supabase schema)
interface UserProfile {
  id: string;           // uuid, FK to auth.users
  full_name: string | null;
  avatar_url: string | null;
  billing_address: Json | null;
  payment_method: Json | null;
  role?: 'user' | 'pro' | 'admin';  // ADD this column via migration
}
```

**Adding the role column:**

The boilerplate's `users` table does not include a `role` column out of the box. Add it via migration:

```sql
-- supabase/migrations/[timestamp]_add_user_roles.sql
ALTER TABLE users ADD COLUMN role text NOT NULL DEFAULT 'user'
  CHECK (role IN ('user', 'pro', 'admin'));

-- RLS: Users cannot change their own role
CREATE POLICY "Users cannot update own role" ON users
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (role = (SELECT role FROM users WHERE id = auth.uid()));
```

After creating the migration, run `pnpm supabase:generate-types` to update `types_db.ts`. The role column will then appear in the auto-generated types.

⚠️ **Roles are managed server-side only.** Users cannot promote themselves. Role changes happen via Supabase Dashboard, admin API route, or Edge Function — never from the client.


### THEME (DARK MODE)

The boilerplate uses `next-themes`. It is already configured. Do not create a ThemeContext. Do not write your own dark mode toggle from scratch. Do not add `dark:` variant classes manually for basic theming — that's what the CSS variables are for.

```tsx
// Already configured in providers.tsx:
import { ThemeProvider } from 'next-themes'

<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>

// Theme toggle already exists at components/landing/mode-toggle.tsx
// Uses shadcn DropdownMenu with Sun/Moon icons
```

When you need to reference the current theme in a Client Component:

```tsx
'use client'
import { useTheme } from 'next-themes'

export function MyComponent() {
  const { theme, setTheme } = useTheme()
  // ...
}
```

shadcn/ui components already respect the theme via CSS variables. If you add custom components, use the same CSS variable tokens defined in `styles/main.css` so they automatically adapt to light/dark mode.


### PROTECTED ROUTES

There are no `<ProtectedRoute>` wrapper components in Next.js App Router. Route protection happens in two places, both of which already exist:

**1. Middleware (already configured — DO NOT MODIFY):**

`middleware.ts` handles the broad strokes: if the user has no session and hits a protected path, they get redirected to `/auth/signin`. This catches 95% of unauthorized access attempts before the page even starts rendering.

**2. Server-side checks in page components (this is what you write):**

For fine-grained access control — role checks, ownership verification, feature gating — do it in the Server Component:

```typescript
// In any protected page (Server Component):
import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/signin')

  // For role-based access:
  const { data: profile } = await supabase
    .from('users')
    .select('role')
    .eq('id', user.id)
    .single()

  if (profile?.role !== 'admin') redirect('/dashboard')

  return <AdminDashboard />
}
```

**Layout-level protection (for groups of routes):**

If every page under `/dashboard/*` requires auth, put the check in the layout:

```typescript
// app/dashboard/layout.tsx
import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/signin')

  return (
    <div className="flex min-h-screen">
      <Sidebar user={user} />
      <main className="flex-1">{children}</main>
    </div>
  )
}
```

Every child page under `app/dashboard/` inherits this auth check. No wrapper components. No HOCs. No client-side redirects that flash the wrong page for 200ms before bouncing the user.

**Conditional UI based on role:**

```tsx
// In a Server Component
const { data: profile } = await supabase
  .from('users')
  .select('role')
  .eq('id', user.id)
  .single()

const isAdmin = profile?.role === 'admin'
const isPro = profile?.role === 'pro' || profile?.role === 'admin'

// Show admin-only section
{isAdmin && <AdminPanel />}

// Show upgrade prompt for free users
{!isPro && (
  <Card className="border-brand bg-brand/10">
    <p>Upgrade to Pro for unlimited access</p>
    <Button>Upgrade Now</Button>
  </Card>
)}
```


### SUPABASE DATA STRUCTURE

The D2D boilerplate ships with 6 existing tables that handle auth, billing, and subscriptions. Do not modify them.

**Existing tables (DO NOT TOUCH):**
- `users` — User profiles (synced from `auth.users`)
- `customers` — Stripe customer mapping
- `prices` — Stripe price objects
- `products` — Stripe product catalog
- `subscriptions` — Active subscription state
- `invoices` — Stripe invoice history (if present)

**Adding new tables for your app:**

Every app-specific table follows the same pattern: create a migration, add RLS policies, and regenerate types. Here is the exact pattern:

```sql
-- supabase/migrations/[timestamp]_create_items.sql

CREATE TABLE items (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title text NOT NULL,
  description text,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

-- RLS: Users can only access their own items
ALTER TABLE items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own items" ON items
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own items" ON items
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own items" ON items
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own items" ON items
  FOR DELETE USING (auth.uid() = user_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_updated_at
  BEFORE UPDATE ON items
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

After creating any migration: `pnpm supabase:generate-types` to update `types_db.ts`.

⚠️ **Every user-owned table MUST have `user_id` with `ON DELETE CASCADE` and RLS policies.** No exceptions. If you skip RLS, users can read each other's data. If you skip `ON DELETE CASCADE`, deleting a user leaves orphaned rows forever.

⚠️ **DO NOT use Firestore-style subcollections.** Supabase uses relational tables with foreign keys. User data scoping happens through RLS policies that check `auth.uid() = user_id`, not through document paths.


### SUPABASE DATA SERVICE PATTERN

There is no `services/firestore.ts` equivalent. Supabase queries go directly in your components. Server Components fetch data at render time. Client Components mutate data in event handlers.

**Server Component data fetching (preferred for all reads):**

```typescript
import { createClient } from '@/utils/supabase/server'

export default async function ItemsPage() {
  const supabase = await createClient()
  const { data: items } = await supabase
    .from('items')
    .select('*')
    .order('created_at', { ascending: false })

  return <ItemList items={items} />
}
```

No loading states. No useEffect. No `useState` for data. The page renders with data already loaded. This is the primary advantage of Server Components — use it.

**Client Component mutations:**

```typescript
'use client'
import { createClient } from '@/utils/supabase/client'

const supabase = createClient()

// Create
const { data, error } = await supabase
  .from('items')
  .insert({ title, description, user_id: user.id })
  .select()
  .single()

// Update
const { error } = await supabase
  .from('items')
  .update({ title, description })
  .eq('id', itemId)

// Delete
const { error } = await supabase
  .from('items')
  .delete()
  .eq('id', itemId)
```

After any mutation, call `router.refresh()` to re-render the Server Component with fresh data. This is the Next.js pattern — mutate on the client, refresh from the server.

**Realtime subscriptions (only when you need live updates):**

```typescript
'use client'
import { createClient } from '@/utils/supabase/client'
import { useEffect } from 'react'

export function RealtimeItems({ userId }: { userId: string }) {
  const supabase = createClient()

  useEffect(() => {
    const channel = supabase
      .channel('items-changes')
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'items',
        filter: `user_id=eq.${userId}`
      }, (payload) => {
        // Handle change
      })
      .subscribe()

    // Cleanup
    return () => { supabase.removeChannel(channel) }
  }, [userId, supabase])

  return null // or render live data
}
```

⚠️ **Do not use realtime subscriptions for basic CRUD pages.** Server Component fetching + `router.refresh()` after mutations is simpler, faster, and uses zero WebSocket connections. Reserve realtime for genuinely live features: collaborative editing, chat, live dashboards.


### DELETE ACCOUNT

The boilerplate has an account page at `/account`. For account deletion, use the admin client to bypass RLS and clean up everything:

```typescript
// Server Action or API route
import { createAdminClient } from '@/utils/supabase/admin'

async function deleteAccount(userId: string) {
  const supabase = createAdminClient()

  // Delete user data from all tables (RLS bypassed with admin client)
  await supabase.from('items').delete().eq('user_id', userId)
  await supabase.from('subscriptions').delete().eq('user_id', userId)
  // ... delete from all app-specific tables

  // Delete user profile
  await supabase.from('users').delete().eq('id', userId)

  // Delete auth user
  await supabase.auth.admin.deleteUser(userId)
}
```

⚠️ **Always use `createAdminClient` for account deletion.** The regular client respects RLS, which means it cannot delete across tables that the user doesn't have DELETE policies on (like `subscriptions` or `customers`). The admin client bypasses RLS entirely.

⚠️ **Delete app-specific tables FIRST, then `users`, then `auth.users`.** Foreign key constraints enforce this order. If you delete the auth user first, cascade deletes may not fire on your app tables depending on how they reference `auth.users`.


### ROUTING STRUCTURE

Next.js App Router uses the filesystem for routing. There is no `<BrowserRouter>`, no `<Routes>`, no `<Route>` components. The file path IS the route.

```
nextjs/app/
├── page.tsx                    # / — Landing (public)
├── auth/[id]/page.tsx          # /auth/signin, /auth/signup (public)
├── account/page.tsx            # /account (protected)
├── dashboard/page.tsx          # /dashboard (protected)
├── [items]/
│   ├── page.tsx                # /items — List (protected)
│   ├── new/page.tsx            # /items/new — Create (protected)
│   └── [id]/
│       ├── page.tsx            # /items/:id — Detail (protected)
│       └── edit/page.tsx       # /items/:id/edit — Edit (protected)
├── admin/                      # Admin-only routes
│   └── page.tsx                # /admin (admin role required)
├── layout.tsx                  # Root layout with providers
├── not-found.tsx               # 404 catch-all
└── error.tsx                   # Error boundary
```

**Page titles via metadata export (NOT a usePageTitle hook):**

```typescript
// In any page.tsx (static):
export const metadata = { title: 'Dashboard | AppName' }

// Or dynamic (when the title depends on data):
export async function generateMetadata({ params }: { params: { id: string } }) {
  const item = await getItem(params.id)
  return { title: `${item.name} | AppName` }
}
```

`generateMetadata` runs on the server before the page renders. It has full access to `params`, `searchParams`, and can make database queries. No client-side `document.title` hacks. No `useEffect` to set the title after render.

⚠️ **Do not create a `usePageTitle` hook.** Next.js metadata API handles this natively. A client-side title hook causes a flash of the wrong title on navigation and breaks SEO.

---

### DESIGN SYSTEM


**Typography:**
| Element | Size | Weight | Class |
|---------|------|--------|-------|
| Page Title | 24px | Semi-bold | `text-2xl font-semibold text-foreground` |
| Section Header | 18px | Semi-bold | `text-lg font-semibold text-foreground` |
| Card Title | 16px | Medium | `text-base font-medium text-foreground` |
| Body Text | 14px | Regular | `text-sm text-muted-foreground` |
| Small/Meta | 12px | Regular | `text-xs text-muted-foreground` |


**Spacing:**
- Card padding: `p-6` (24px)
- Section gaps: `gap-6` (24px)
- Element gaps: `gap-4` (16px)


**Cards (use shadcn Card component):**
```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

If hand-styling: `bg-card rounded-xl border border-border shadow-sm p-6`


**Primary Button (use shadcn Button):**
```tsx
import { Button } from '@/components/ui/button'

<Button>Save Changes</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Back</Button>
```


**Inputs (use shadcn Input):**
```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input id="email" placeholder="you@example.com" />
</div>
```


**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│ HEADER: Logo          User Avatar | Sign Out    │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│   SIDEBAR    │         MAIN CONTENT             │
│   (240px)    │         (scrollable)             │
│              │                                  │
│   - Nav      │         Cards, forms,            │
│   - [Items]  │         data display             │
│   - Help     │                                  │
└──────────────┴──────────────────────────────────┘
```

- Sidebar: 240px wide, `bg-card`, `border-r`
- Header: Full width, `bg-card`, `border-b`, `h-16`
- Main: `flex-1`, `overflow-y-auto`, `p-8`
- Mobile sidebar: Use **shadcn Sheet** component (slide-in overlay)


---


### RESPONSIVE DESIGN (MANDATORY)


Build mobile-first. Design for mobile, then scale up for larger screens.


**Breakpoints (Tailwind defaults):**
- Mobile: < 640px (default styles, no prefix)
- Tablet: `sm:640px` and up
- Desktop: `lg:1024px` and up


**Layout Behavior:**

```
MOBILE (< 640px):
┌─────────────────────┐
│ HEADER    [☰] [👤]  │  ← Hamburger menu, compact header
├─────────────────────┤
│                     │
│    MAIN CONTENT     │  ← Full width, no sidebar visible
│    (scrollable)     │
│                     │
└─────────────────────┘

DESKTOP (≥ 1024px):
┌─────────────────────────────────────────────────┐
│ HEADER: Logo          User Avatar | Sign Out    │
├──────────────┬──────────────────────────────────┤
│   SIDEBAR    │         MAIN CONTENT             │
│   (240px)    │         (scrollable)             │
└──────────────┴──────────────────────────────────┘
```


**Mobile Navigation:**
- Sidebar hidden on mobile, use shadcn **Sheet** for slide-in overlay
- Hamburger icon in header toggles Sheet
- Clicking nav item closes Sheet


**Component Responsive Rules:**

| Component | Mobile | Desktop |
|-----------|--------|---------|
| Sidebar | Hidden, Sheet overlay | Always visible, 240px |
| Cards | Full width, stack vertical | Grid 2-3 columns |
| Forms | Full width inputs | Max-width container |
| Buttons | Full width primary | Auto width |
| Modals | Full screen / nearly full | Centered, max-w-md |
| Text | 16px minimum | Can be smaller |


**Touch Targets:** Minimum 44px × 44px for all clickable elements on mobile.


**Responsive Classes:**
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
<div className="hidden lg:block">      // Desktop only
<div className="lg:hidden">            // Mobile only
<div className="w-full lg:max-w-md">   // Full mobile, contained desktop
<div className="p-4 lg:p-8">           // Responsive padding
```


---


### UI/UX STANDARDS (MANDATORY)


#### REQUIRED UI COMPONENTS

You MUST use or create these. They are NOT optional:

1. **Dialog** — shadcn Dialog (`components/ui/dialog.tsx`) — for confirmations, forms, information display
2. **AlertDialog** — shadcn AlertDialog (`components/ui/alert-dialog.tsx`) — for destructive action confirmation ("Are you sure?")
3. **Toast** — shadcn Toast or Sonner — success/error/info notifications
4. **Skeleton** — shadcn Skeleton (`components/ui/skeleton.tsx`) — animated loading placeholders
5. **EmptyState** — **CREATE THIS** (not in shadcn) — icon + message + CTA button for empty lists
6. **Button with loading** — shadcn Button with disabled + spinner during async

⚠️ **EmptyState does not exist in shadcn. You must create it:**
```tsx
// components/ui/empty-state.tsx
import { Button } from '@/components/ui/button'
import Link from 'next/link'

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
  action?: { label: string; href: string }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 text-muted-foreground">{icon}</div>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
      {action && (
        <Button asChild className="mt-4">
          <Link href={action.href}>{action.label}</Link>
        </Button>
      )}
    </div>
  )
}
```


#### BANNED — DO NOT USE

These are strictly forbidden:

- ❌ `alert()` — Use Toast for messages
- ❌ `confirm()` — Use AlertDialog for confirmations
- ❌ `prompt()` — Use Dialog with a form
- ❌ `console.log` for user feedback — Use Toast
- ❌ Text-only empty states — Use EmptyState component with icon and CTA
- ❌ Browser default dialogs of any kind


#### PAGE TYPES FOR USER DATA

Any data the user creates/saves MUST follow this pattern:

**List View** (`app/[items]/page.tsx`)
- Shows all items as cards or rows
- Clicking an item navigates to Detail View
- Has "Create New" button

**Detail View** (`app/[items]/[id]/page.tsx`)
- Read-only display of single item
- Action buttons: Edit, Delete, Share
- Delete opens AlertDialog, then redirects to List on success

**Create View** (`app/[items]/new/page.tsx`)
- Form to create new item
- Save navigates to Detail View of new item
- Cancel returns to List View

**Edit View** (`app/[items]/[id]/edit/page.tsx`)
- Form pre-filled with existing data
- Save navigates back to Detail View
- Cancel returns to Detail View (not List)


#### NAVIGATION FLOW

```
┌──────────┐     click item      ┌──────────────┐
│   LIST   │ ─────────────────▶  │    DETAIL    │
│   VIEW   │                     │     VIEW     │
└──────────┘                     └──────────────┘
     │                                  │
     │ click "New"              click "Edit"
     ▼                                  │
┌──────────┐                           ▼
│  CREATE  │                     ┌──────────────┐
│   VIEW   │                     │     EDIT     │
└──────────┘                     │     VIEW     │
     │                           └──────────────┘
     │ save                            │
     ▼                                 │ save
┌──────────────┐ ◀─────────────────────┘
│    DETAIL    │
│     VIEW     │
└──────────────┘
```


#### ANTI-PATTERNS — DO NOT DO THESE

- ❌ Clicking saved item opens it in edit mode directly
- ❌ Using Create form as Edit form by pre-loading data
- ❌ No way to view an item without editing it
- ❌ Single "smart" component that handles both view and edit
- ❌ Delete with no confirmation
- ❌ Success/error with no feedback to user
- ❌ Empty lists with just "No items" text (needs icon + CTA)
- ❌ Loading states that are just the word "Loading..."


#### FEEDBACK PATTERNS

**On Success:** Toast notification + navigate to appropriate view
**On Error:** Toast notification + stay on current view + keep form data intact
**On Delete:** Click → AlertDialog → Confirm → Button loading → Success: Toast + redirect to List. Error: Toast + close dialog.
**On Loading:** Lists: Skeleton cards. Detail: Skeleton layout. Buttons: Spinner inside, disabled.


---


### POLISH & UX DETAILS (MANDATORY)


#### DATE & TIME FORMATTING

Never show raw timestamps. Create a helper:

```typescript
// lib/formatDate.ts
export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 172800) return 'Yesterday'
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
```


#### TEXT TRUNCATION

```tsx
<span className="truncate max-w-[200px]">{title}</span>     // Sidebar
<p className="line-clamp-2">{description}</p>                 // Cards
<td className="truncate max-w-[150px]">{content}</td>        // Tables
```


#### BACK NAVIGATION

Every detail/edit page MUST have back navigation:
```tsx
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

<Link href="/items" className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6">
  <ArrowLeft className="w-4 h-4" />
  Back to Items
</Link>
```


#### TRANSITIONS & ANIMATIONS

```css
/* Cards: hover lift */
.card-hover { @apply transition-all duration-200 hover:shadow-md hover:-translate-y-0.5; }
/* Buttons: press */
.btn { @apply transition-all duration-150 active:scale-[0.98]; }
```

Required animations:
- Modals: Fade backdrop, scale content (shadcn handles this)
- Toasts: Slide in (shadcn handles this)
- Cards: Subtle lift on hover
- Buttons: Slight scale on press
- Sidebar: Slide in on mobile (shadcn Sheet handles this)


#### ACCESSIBILITY

**Focus States:** `focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`
**Escape closes modals:** shadcn Dialog/AlertDialog handles this automatically
**Icon buttons:** `<button aria-label="Delete item">...</button>`
**Screen reader:** `<span className="sr-only">Loading...</span>`


#### PAGINATION

Choose ONE and use consistently:

```tsx
// Option 1: Pagination with Supabase .range()
const ITEMS_PER_PAGE = 10
const { data } = await supabase
  .from('items')
  .select('*', { count: 'exact' })
  .order('created_at', { ascending: false })
  .range((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE - 1)
```


#### FORM FIELD STATES

Handle: Default, Focused (ring), Filled, Error (red border + message), Disabled, Helper text. shadcn Input handles base states. Add error state:

```tsx
<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input id="email" className={error ? 'border-destructive' : ''} />
  {error && <p className="text-sm text-destructive">{error}</p>}
</div>
```


#### UNSAVED CHANGES WARNING

```tsx
'use client'
import { useEffect } from 'react'

function useUnsavedChanges(hasChanges: boolean) {
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (hasChanges) { e.preventDefault(); e.returnValue = '' }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [hasChanges])
}
```


#### 404 / NOT FOUND

**Route-level:** `app/not-found.tsx` (Next.js convention)
```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
      <p className="text-xl text-muted-foreground mt-4">Page not found</p>
      <Link href="/dashboard" className="mt-6 text-primary hover:underline">
        ← Back to Dashboard
      </Link>
    </div>
  )
}
```

**Data-level:** In detail pages when item doesn't exist, use EmptyState.


#### ERROR BOUNDARY

Next.js `error.tsx` convention (NOT React class component):

```tsx
// app/error.tsx
'use client'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center p-8">
        <h1 className="text-2xl font-semibold mb-2">Something went wrong</h1>
        <p className="text-muted-foreground mb-4">Please try again.</p>
        <button onClick={reset} className="bg-primary text-primary-foreground px-6 py-3 rounded-lg">
          Try Again
        </button>
      </div>
    </div>
  )
}
```


#### HOVER STATES

Every clickable element needs hover feedback:
```tsx
// Cards
className="hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer"
// Links
className="hover:text-foreground hover:underline"
// Icon buttons
className="hover:bg-muted rounded-lg p-2 transition-colors"
// Table rows
className="hover:bg-muted transition-colors"
```


#### NETWORK / ERROR HANDLING

```typescript
// Wrap Supabase calls for user-friendly errors
async function safeQuery<T>(query: Promise<{ data: T | null; error: any }>) {
  const { data, error } = await query
  if (error) {
    if (error.code === 'PGRST301') throw new Error('You don\'t have permission.')
    if (error.code === '23505') throw new Error('This item already exists.')
    throw new Error('Something went wrong. Please try again.')
  }
  return data
}
```


#### SESSION EXPIRY

Supabase middleware auto-refreshes tokens on every request. If a token expires mid-session:
```typescript
// Client-side: listen for auth changes
supabase.auth.onAuthStateChange((event) => {
  if (event === 'SIGNED_OUT' || event === 'TOKEN_REFRESHED') {
    router.refresh() // Re-run Server Components
  }
})
```


#### ICONS — LUCIDE REACT

Already installed via pnpm. Usage:
```tsx
import { Home, Settings, Trash2, Plus, Loader2, Search, ArrowLeft } from 'lucide-react'

<Home className="w-5 h-5" />                           // Standard
<Loader2 className="w-4 h-4 animate-spin" />           // Spinner
<button><Plus className="w-4 h-4 mr-2" /> New Item</button>
```


#### LOADING BUTTON PATTERN

```tsx
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

<Button disabled={isLoading} onClick={handleSubmit}>
  {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
  {isLoading ? 'Saving...' : 'Save Changes'}
</Button>
```


#### AVATAR (shadcn — already in boilerplate)

```tsx
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

<Avatar>
  <AvatarImage src={user.avatar_url} alt={user.full_name} />
  <AvatarFallback>{user.full_name?.slice(0, 2).toUpperCase() || '?'}</AvatarFallback>
</Avatar>
```


#### SEARCH / FILTER FOR LISTS

Any list that can grow needs search:
```tsx
'use client'
const [search, setSearch] = useState('')
const filtered = items.filter(i =>
  i.title.toLowerCase().includes(search.toLowerCase())
)

<div className="relative mb-6">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
  <Input placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10" />
</div>
```


---


### STRIPE INTEGRATION PATTERN


The boilerplate includes complete Stripe integration. **DO NOT rebuild this.** Use what exists:

**Checkout Flow:**
1. User clicks a pricing tier
2. Frontend calls `get_stripe_url` edge function with price ID
3. Edge function creates/retrieves Stripe customer → creates checkout session → returns URL
4. User completes payment on Stripe
5. `stripe_webhook` edge function syncs subscription data to database

**Check Subscription Status:**
```typescript
const { data: subscription } = await supabase
  .from('subscriptions')
  .select('status, price_id')
  .eq('user_id', user.id)
  .in('status', ['active', 'trialing'])
  .single()

const isPro = !!subscription
```

**Billing Portal:**
```typescript
// Send no price param to get_stripe_url → returns billing portal URL
const { data } = await supabase.functions.invoke('get_stripe_url')
window.location.href = data.url
```

**Adding/Modifying Pricing:** Edit `fixtures/stripe-fixtures.json`, run `pnpm stripe:fixtures`. Products and prices sync to DB via webhooks automatically.


---


### DATABASE MIGRATIONS


**To add a new table:**
1. Make changes in local Supabase Studio (`http://localhost:54323`)
2. `pnpm supabase:generate-migration` — creates SQL file in `supabase/migrations/`
3. Review the generated SQL
4. `pnpm supabase:generate-types` — updates `types_db.ts`
5. `pnpm supabase:push` — push to production

**Or write migration SQL directly:**
```sql
-- supabase/migrations/[timestamp]_create_[table].sql
CREATE TABLE [table_name] (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  -- your columns here
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

ALTER TABLE [table_name] ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users crud own data" ON [table_name]
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
```

Then: `pnpm supabase:generate-types`


---


### SERVER vs CLIENT COMPONENTS


**Default to Server Components.** Only add `'use client'` when you need:
- `useState`, `useEffect`, `useRef`
- `onClick`, `onChange`, `onSubmit`
- Browser APIs (`window`, `localStorage`)
- Supabase realtime subscriptions

**Data fetching = Server Components:**
```tsx
// app/items/page.tsx (Server Component — NO 'use client')
export default async function ItemsPage() {
  const supabase = await createClient()
  const { data: items } = await supabase.from('items').select('*')
  return <ItemList items={items} />
}
```

**Interactive UI = Client Components:**
```tsx
// components/items/item-form.tsx
'use client'
export function ItemForm() {
  const [title, setTitle] = useState('')
  // ... interactive form
}
```

⚠️ **Do NOT use `useEffect` to fetch data on page load.** That's a Client Component pattern. Use Server Components to fetch data, then pass it to Client Components as props.


---


### ENVIRONMENT VARIABLES


**Next.js `.env.local` (local development):**
```
NEXT_PUBLIC_SITE_URL="http://localhost:3000"
NEXT_PUBLIC_SUPABASE_URL="http://127.0.0.1:54321"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJ..."
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
NEXT_PUBLIC_POSTHOG_HOST="https://app.posthog.com"
NEXT_PUBLIC_POSTHOG_KEY="phc_..."
```

**Supabase `.env` (edge function secrets):**
```
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SIGNING_SECRET="whsec_..."
POSTHOG_CLIENT_KEY="phc_..."
LOOPS_API_KEY="..."
GOOGLE_CLIENT_ID="..."
GOOGLE_SECRET="..."
GITHUB_CLIENT_ID="..."
GITHUB_SECRET="..."
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
```

⚠️ **`NEXT_PUBLIC_` prefix = exposed to browser.** Never prefix secret keys with `NEXT_PUBLIC_`.
⚠️ **`SUPABASE_SERVICE_ROLE_KEY` bypasses RLS.** Never expose to client. Server-side only.


---


### CRITICAL RULES


**Technical:**
1. Supabase config via `utils/supabase/` client files + `.env.local` — never hardcode credentials
2. NO direct Supabase client creation in components — use the 4 utility files
3. NO unprotected routes for authenticated features — middleware + Server Component checks
4. NO inline styles — Tailwind only
5. NO `any` types — use `types_db.ts` generated types for all DB operations
6. ALL new tables include `created_at`/`updated_at` with PostgreSQL defaults + update trigger
7. ALL user data scoped via RLS policies (`auth.uid() = user_id`)
8. Error handling via Next.js `error.tsx` convention
9. ALL new tables use `ON DELETE CASCADE` on `user_id` foreign key

**UI/UX:**
10. NO `alert()`, `confirm()`, `prompt()` — use shadcn Dialog/AlertDialog/Toast
11. ALL destructive actions require AlertDialog confirmation
12. ALL async operations show loading state (Skeleton for lists, spinner in buttons)
13. ALL empty lists use EmptyState component with icon and CTA
14. ALL success/error actions show Toast feedback
15. ALL saved items have Detail View (read-only) separate from Edit View
16. ALL forms validate before submission
17. ALL buttons show loading state during async actions
18. ALL avatars use shadcn Avatar with AvatarFallback
19. ALL pages set title via Next.js `metadata` or `generateMetadata` export
20. ALL forms autofocus first input
21. ALL lists have search/filter when > 5 items expected
22. ALL error states have retry action
23. ALL dates formatted as relative time (not raw timestamps)
24. ALL long text truncated with ellipsis
25. ALL detail pages have back navigation
26. Use Lucide React for all icons — consistent `w-5 h-5` default size
27. Zero console errors in production


---


## BUILD THIS APP NOW


Using all the information above:

1. **Clone** the D2D boilerplate: `git clone https://github.com/devtodollars/startup-boilerplate.git YOUR_APP_NAME`
2. **Install:** `cd YOUR_APP_NAME/nextjs && pnpm install`
3. **Set up Supabase:** Create project at supabase.com, then `supabase link`
4. **Configure:** Copy `.env.example` to `.env.local`, fill in your Supabase URL + keys
5. **Create migrations** for your app-specific tables (follow the migration pattern above)
6. **Generate types:** `pnpm supabase:generate-types`
7. **Push migrations:** `supabase db push`
8. **Deploy edge functions:** `supabase functions deploy --import-map supabase/functions/deno.json`
9. **Build the features** described in Section 2 using the CRUD view pattern
10. **Apply the styling** from Section 3 using the design system
11. **Test** all auth flows, CRUD operations, and Stripe integration
12. Make it **production-ready** with proper error handling

Generate the complete, working application on top of the existing boilerplate.


---


## POST-GENERATION STEPS


1. **Supabase project:** Create at supabase.com → `supabase link` from project root
2. **Push schema:** `supabase db push` (applies all migrations)
3. **Deploy functions:** `supabase functions deploy --import-map supabase/functions/deno.json`
4. **Set secrets:** `supabase secrets set --env-file .env`
5. **Configure OAuth:** In Supabase Dashboard → Auth → Providers → enable Google + GitHub with your client IDs
6. **Set redirect URLs:** Auth → URL Config → add your production domain + `http://localhost:3000`
7. **Stripe setup:** Create products in Stripe → configure webhook URL (your `stripe_webhook` edge function URL) → select all events → copy signing secret to `.env`
8. **Sync Stripe:** `deno run --env -A supabase/functions/_scripts/sync-stripe.ts`
9. **Deploy to Vercel:** Connect GitHub repo → add all env vars from `.env.local` + `SUPABASE_SERVICE_ROLE_KEY`
10. **Favicon:** Replace the letter and color in the SVG favicon with your app's initial and brand color
11. **App name:** Update the `name` in `package.json` and the site metadata in `layout.tsx`
12. **Help email:** Replace placeholder email in the Help & Support link
