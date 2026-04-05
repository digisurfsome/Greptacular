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

<!-- STOP: This is the end of the first half. Another agent will append the design system, UI standards, polish details, critical rules, and post-generation sections below this line. -->
