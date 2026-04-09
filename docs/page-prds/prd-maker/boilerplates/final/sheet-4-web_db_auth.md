# Exact Reality Sheet 4: web_db_auth (Database + Auth ON, Payments dormant)

> **Variant**: Database + Auth active -- Payments dormant
> **Boilerplate**: DevToDollars Web-BoilerPlate-D2D (Next.js 16 + Supabase + Stripe + Tailwind v4 + PostHog)
> **What is active**: UI framework, styling, landing page, Supabase PostgreSQL, Supabase Auth (email/password + Google OAuth + GitHub OAuth)
> **What is dormant**: Payments/Stripe (code present, no keys configured), PostHog Analytics (code present, no keys configured)
> **Use case**: Apps that need user accounts and data persistence but no monetization yet
>
> This document is the SINGLE SOURCE OF TRUTH for what an AI coding agent gets for free from this boilerplate
> and what it must build from scratch. Every rule from Martin's 192-rule checklist and every rule from the
> 71-rule Industry Standards supplement is listed below with its exact status.

---

## Delta Inheritance

**This sheet inherits ALL statuses from Sheet 3 (web_db) and then applies the auth-activation changes documented below.**

What is new in Sheet 4 vs Sheet 3:
- Supabase Auth is fully operational (was dormant)
- Auth methods: email/password, Google OAuth, GitHub OAuth
- Auth flows: signup, signin, forgot password, update password, email verification, signout
- User profiles auto-created via `handle_new_user()` trigger (was present but never fired)
- Session management via `middleware.ts` (was present but returned null)
- Protected routes enforced (account page redirects if not logged in)
- OAuth callback route processes real redirects
- **URGENCY FLAGS**: Legal compliance becomes critical with users creating accounts

What is still dormant:
- Payments (Stripe) = code present, no keys, checkout will fail
- Analytics (PostHog) = code present, no keys, not tracking

---

## Boilerplate Identity

| Field | Value |
|-------|-------|
| **Framework** | Next.js 16.1.6 (React 19, TypeScript, App Router) |
| **Styling** | Tailwind CSS v4.1.18 + tw-animate-css |
| **Component Library** | Radix UI primitives (dialog, accordion, avatar, toast, dropdown, navigation-menu, scroll-area, label) |
| **Icons** | Lucide React 0.562.0 + @icons-pack/react-simple-icons (GitHub, Google) |
| **Auth** | Supabase Auth (email/password + Google OAuth + GitHub OAuth) -- **ACTIVE** |
| **Database** | Supabase PostgreSQL (RLS enabled) -- **ACTIVE** |
| **Payments** | Stripe (checkout, webhooks, billing portal via Supabase Edge Functions) -- **DORMANT (no keys)** |
| **Analytics** | PostHog (page views, auth events, checkout events) -- **DORMANT (no keys)** |
| **Hosting** | Vercel (configured via next.config.js) |
| **Package Manager** | pnpm (lockfile committed) |
| **Edge Functions** | Deno-based: `get_stripe_url`, `stripe_webhook`, `on_user_modify` |

---

## Boilerplate File Map

```
nextjs/
  app/
    layout.tsx              -- Root layout (ThemeProvider, PHProvider, Toaster)
    page.tsx                -- Landing page
    providers.tsx           -- PostHog provider (dormant without keys)
    PostHogPageView.tsx     -- Page view tracking (dormant without keys)
    account/page.tsx        -- Account page (server component, auth-gated) -- ACTIVE
    auth/[id]/page.tsx      -- Auth pages (signin, signup, forgot_password, update_password, verify_email) -- ACTIVE
    api/
      auth_callback/route.ts   -- OAuth callback handler -- ACTIVE
      og/route.tsx             -- OG image generation
      reset_password/route.ts  -- Password reset callback -- ACTIVE
  components/
    icons/                  -- GitHub.tsx, Logo.tsx
    landing/                -- Navbar, Hero, Pricing, FAQ, Footer, Stats, Logos, Cta, Items, Icons, mode-toggle
    misc/                   -- AccountPage.tsx, AuthForm.tsx, PostHogPageViewWrapper.tsx
    ui/                     -- accordion, avatar, badge, breadcrumb, button, card, dialog, dropdown-menu,
                               glow, input, item, label, navigation-menu, scroll-area, section, sheet,
                               skeleton, toast, toaster, use-toast.ts
  utils/
    cn.ts                   -- className merge utility
    helpers.ts              -- URL helpers
    types.ts                -- AuthState enum, StateInfo, SubscriptionWithPriceAndProduct
    supabase/
      admin.ts              -- Supabase admin client (service role)
      api.ts                -- Auth API client (signup, signin, oauth, signout, password reset) -- ACTIVE
      client.ts             -- Browser Supabase client -- ACTIVE
      middleware.ts          -- Session refresh middleware -- ACTIVE
      queries.ts            -- getUser, getSubscription, getProducts, getUserDetails -- ACTIVE
      server.ts             -- Server-side Supabase client -- ACTIVE
  lib/utils.ts              -- cn() utility
  styles/
    main.css                -- Tailwind v4 theme (CSS variables, light/dark, animations)
    utils.css               -- Utility styles
  types_db.ts               -- Auto-generated Supabase types
  schema.sql                -- Full database schema
  package.json              -- Dependencies locked with pnpm
  pnpm-lock.yaml            -- Lockfile committed
  tsconfig.json             -- TypeScript config
  next.config.js            -- Next.js config
  postcss.config.js         -- PostCSS config
  .prettierrc.json          -- Prettier config

supabase/
  config.toml               -- Supabase project config
  seed.sql                  -- Seed data
  migrations/
    20240717231009_init.sql  -- Initial migration (users, customers, products, prices, subscriptions, checkout_sessions)
  functions/
    _shared/
      loops.ts              -- Loops.so email client
      posthog.ts            -- PostHog client (dormant)
      request.ts            -- Request handler with auth
      stripe.ts             -- Stripe client (dormant -- no keys)
      supabase.ts           -- Supabase admin client, upsert/delete helpers, customer management
      utils.ts              -- Shared utilities
    get_stripe_url/index.ts  -- Checkout session / billing portal URL (dormant)
    stripe_webhook/index.ts  -- Stripe event processing (dormant)
    on_user_modify/index.ts  -- PostHog events on user lifecycle (dormant)
    types_db.ts              -- Shared DB types for edge functions

.env.example                -- All required env vars with placeholders
.gitignore                  -- .env ignored
```

---

## Database Tables (from schema.sql)

| Table | Purpose | RLS | Key Columns |
|-------|---------|-----|-------------|
| `users` | User profiles auto-created on signup | Owner-only (select/update where `auth.uid() = id`) | id (uuid), full_name, avatar_url, billing_address, payment_method |
| `customers` | Maps Supabase user ID to Stripe customer ID | Private (no policies) | id (uuid), stripe_customer_id |
| `products` | Stripe products synced via webhook | Public read-only | id (text), active, name, description, image, metadata |
| `prices` | Stripe prices synced via webhook | Public read-only | id (text), product_id, active, unit_amount, currency, type, interval |
| `subscriptions` | User subscriptions synced via webhook | Owner-only (`auth.uid() = user_id`) | id (text), user_id, status, price_id, quantity, created, current_period_start/end |
| `checkout_sessions` | Completed checkout records | Owner-only (`auth.uid() = user_id`) | id (text), user_id, mode, payment_status, status, price_id, quantity, created |

**Realtime**: Products and prices tables have realtime publication enabled.

**Note**: The `users` table has NO `role` column. No `createdAt`/`updatedAt` columns on the users table (only `created` on subscriptions via `DEFAULT now()`). No `email` column on users (email lives in `auth.users` only).

**Auth-specific note**: With auth active, the `handle_new_user()` trigger fires on every signup, creating rows in the `users` table. RLS policies now enforce real user scoping (not just blocking anonymous access as in Sheet 3).

---

## URGENCY FLAGS -- Legal/Compliance Items Critical with Auth ON

These items were acceptable when dormant but become **legally risky** once users can create accounts:

| Rule | Urgency | Risk | Why It Matters Now |
|------|---------|------|--------------------|
| Privacy policy page (#236) | **HIGH** | Legal liability | Collecting email, name, avatar via signup without a privacy policy. GDPR/CCPA violation. |
| Terms of service page (#237) | **HIGH** | No legal agreement | Users creating accounts without accepting terms. No liability protection. |
| Data deletion capability (#240) | **HIGH** | GDPR Article 17 | Users can sign up but cannot delete their data. Right to erasure violated. |
| Cookie consent (#238) | **MEDIUM** | GDPR cookie rules | Supabase sets auth cookies (essential -- may be exempt). PostHog dormant, so no tracking cookies yet. Risk increases when PostHog activated. |
| Data export capability (#239) | **MEDIUM** | GDPR Article 20 | Right to data portability. Users have profile data they cannot export. |
| Consent tracking (#241) | **MEDIUM** | Audit trail | No record of what users consented to during signup. |
| Account deletion confirmation (#AS1-AS3) | **MEDIUM** | UX safety | When deletion is built, it must have typed confirmation flow. |

---

## PART 1: Martin's Structural Checklist (Rules 1-192 across 22 categories + 43 banned patterns)

---

### Category: Stack (Mandatory) -- Rules S1-S10

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| S1 | Framework with type safety | STANDARD | Use the project's chosen UI framework with strict type checking enabled; all code must be statically typed | HANDLED | `nextjs/package.json` (Next.js 16 + React 19 + TypeScript 5.5), `nextjs/tsconfig.json` | None -- already implemented |
| S2 | Single styling solution | STANDARD | All styling via a single, consistent CSS methodology; no mixing approaches; no inline styles | HANDLED | `nextjs/styles/main.css` (Tailwind CSS v4), `nextjs/package.json` (tailwindcss 4.1.18) | None -- already implemented |
| S3 | Authentication provider | CRITICAL | Use the configured auth provider's sign-in flow with designated OAuth provider; restrict to approved sign-in methods | HANDLED | `nextjs/utils/supabase/api.ts` (email/password + Google + GitHub OAuth), `nextjs/components/misc/AuthForm.tsx`. Auth callback at `/api/auth_callback/route.ts`. Session refresh via `middleware.ts` | None -- **fully operational**. Was PRESENT_NOT_WIRED in Sheet 3, now HANDLED |
| S4 | Single database backend | STANDARD | All persistent data in a single configured database technology; do not mix multiple backends | HANDLED | `nextjs/schema.sql` (Supabase PostgreSQL), `nextjs/utils/supabase/queries.ts` | None -- already implemented |
| S5 | Built-in state management | STANDARD | Auth and feature state via framework's built-in state management primitives | HANDLED | `nextjs/app/providers.tsx` (React Context for PostHog), `next-themes` (ThemeProvider), Supabase SSR handles auth state via cookies/middleware | None -- already implemented |
| S6 | No external state libraries | STANDARD | No Redux, Zustand, Jotai, MobX, etc. unless explicitly approved | HANDLED | No external state libraries in `package.json`. Uses React state + `next-themes` + Supabase client | None -- already implemented |
| S7 | No containerization | STANDARD | No Dockerfiles, no docker-compose; deployment via configured hosting platform | HANDLED | No Docker files present. Vercel deployment configured | None -- already implemented |
| S8 | No custom backend | STANDARD | No custom server-side code; all backend via BaaS or serverless | HANDLED | Supabase Edge Functions (Deno serverless) handle Stripe webhooks and checkout -- serverless, not custom backend | None -- already implemented |
| S9 | Single icon library | POLISH | Use a single, consistent icon library for all icons; define a standard icon size | PARTIAL | `nextjs/package.json` has `lucide-react` (primary) AND `@icons-pack/react-simple-icons` (for Google/GitHub brand icons) AND `@radix-ui/react-icons` | Agent should standardize on Lucide React for all non-brand icons. Brand icons (Google, GitHub) in AuthForm are acceptable exceptions. Remove `@radix-ui/react-icons` if unused |
| S10 | Dependency management locked | STANDARD | All dependencies managed through package manager; versions locked | HANDLED | `nextjs/pnpm-lock.yaml` committed, `package.json` uses caret ranges with lockfile | None -- already implemented |

---

### Category: File Structure -- Rules FS1-FS11

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| FS1 | One component per file | STANDARD | Each file exports exactly one UI component as its default/primary export | HANDLED | All components in `nextjs/components/` follow this pattern | None -- already implemented |
| FS2 | Feature folders for grouping | STANDARD | Related components in `components/[FeatureName]/` directories | HANDLED | `nextjs/components/landing/`, `nextjs/components/misc/`, `nextjs/components/ui/`, `nextjs/components/icons/` | None -- already implemented. Agent must create new feature folders for app-specific features |
| FS3 | Centralized type definitions | STANDARD | All shared types centralized in a dedicated types file | HANDLED | `nextjs/utils/types.ts` (app types), `nextjs/types_db.ts` (auto-generated DB types) | None -- already implemented. Agent adds new types to `utils/types.ts` |
| FS4 | Custom hooks per feature | POLISH | Extract shared stateful logic into reusable hook files | PARTIAL | `nextjs/components/ui/use-toast.ts` exists. No hooks directory | Agent must create `nextjs/hooks/` directory and extract reusable hooks as features are built |
| FS5 | Required directory structure | STANDARD | Source organized into config/, state-management/, hooks/, components/ui/, pages/, services/, utils/, types/ | PARTIAL | Has: `components/ui/`, `utils/`, `app/` (pages). Missing: dedicated `hooks/`, `services/`, `config/` directories | Agent must create `hooks/` and `services/` directories. Service layer is in `utils/supabase/` which serves the purpose but doesn't match the naming convention |
| FS6 | Config folder for service credentials | CRITICAL | Service configuration in a dedicated `config/` directory | PARTIAL | Supabase config accessed via env vars in `utils/supabase/client.ts`, `utils/supabase/server.ts`. No dedicated `config/` folder | Current pattern is acceptable for Next.js (env vars loaded by framework). No action needed unless agent wants strict folder convention |
| FS7 | State management folder | STANDARD | All global state providers in a dedicated directory | PARTIAL | `nextjs/app/providers.tsx` (PostHog provider), `next-themes` (ThemeProvider in layout.tsx). No dedicated `contexts/` or `stores/` directory | Agent must create global state files in a consistent location as app features require state management |
| FS8 | Services folder for data access | CRITICAL | All database operations in dedicated `services/` directory; components never import DB client directly | PARTIAL | `nextjs/utils/supabase/queries.ts` serves as the query layer. But components like `Pricing.tsx` call `supabase.from()` directly | Agent must enforce service layer pattern: create `services/` directory, move all DB queries there, refactor components to never import Supabase client directly |
| FS9 | Utils folder | STANDARD | Helper functions in `utils/` directory; date formatting and pluralization utilities at minimum | PARTIAL | `nextjs/utils/cn.ts`, `nextjs/utils/helpers.ts` exist. No date formatting or pluralization utilities | Agent must add `utils/formatDate.ts` and `utils/pluralize.ts` |
| FS10 | Pages folder with naming convention | STANDARD | Page components follow `[Entity][Action]Page` naming; one page per route | PARTIAL | `nextjs/app/page.tsx` (landing), `nextjs/app/account/page.tsx`, `nextjs/app/auth/[id]/page.tsx`. Uses Next.js App Router convention (folder-based routing), not explicit naming | Next.js App Router uses folder-based routing which is the standard. Naming is fine. Agent creates new pages as `app/{route}/page.tsx` |
| FS11 | UI components folder | STANDARD | All reusable UI primitives in `components/ui/` | HANDLED | `nextjs/components/ui/` contains accordion, avatar, badge, breadcrumb, button, card, dialog, dropdown-menu, glow, input, item, label, navigation-menu, scroll-area, section, sheet, skeleton, toast, toaster | None -- already implemented |

---

### Category: Configuration / Module System -- Rules CM1-CM10

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| CM1 | Dependency versions locked | STANDARD | Dependency versions locked; no changes without explicit approval | HANDLED | `nextjs/pnpm-lock.yaml` committed, `package.json` with locked versions, pnpm overrides for React types | None -- already implemented |
| CM2 | No redundant sub-imports | STANDARD | Do not add redundant or conflicting entries to dependency config | HANDLED | `nextjs/package.json` has clean dependency list, no redundant entries | None -- already implemented |
| CM3 | CSS framework loading | STANDARD | CSS framework loaded via standard method with inline configuration | HANDLED | `nextjs/postcss.config.js` + `nextjs/styles/main.css` (@import 'tailwindcss') | None -- already implemented |
| CM4 | Typography font loaded | POLISH | Load chosen font family with required weights via CDN or local files | MUST_BUILD | N/A | Agent must add a font (e.g., Inter, Geist) via `next/font` in `layout.tsx`. No custom font is currently loaded -- browser default is used |
| CM5 | CSS variables for theming | STANDARD | Light mode values in `:root`; dark mode overrides in toggled class; reference via CSS custom properties | HANDLED | `nextjs/styles/main.css` defines `:root` (light) and `.dark` (dark) with full oklch color tokens (background, foreground, card, primary, secondary, muted, accent, destructive, border, input, ring, chart-1 through chart-5) | None -- already implemented |
| CM6 | Dark mode via class strategy | STANDARD | Dark mode toggled via CSS class on root element | HANDLED | `nextjs/styles/main.css` (`@custom-variant dark (&:where(.dark, .dark *))`) + `nextjs/app/layout.tsx` (ThemeProvider attribute="class") | None -- already implemented |
| CM7 | Semantic color tokens | STANDARD | Colors defined as semantic tokens, not raw values | HANDLED | `nextjs/styles/main.css` uses semantic tokens: brand, background, foreground, card, popover, primary, secondary, muted, accent, destructive, border, input, ring | None -- already implemented |
| CM8 | Custom border radius token | POLISH | Define reusable border radius token for cards | HANDLED | `nextjs/styles/main.css` defines `--radius: 0.625rem` with computed `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-2xl` | None -- already implemented |
| CM9 | Custom card shadow token | POLISH | Define reusable card shadow token with subtle dual-shadow | HANDLED | `nextjs/styles/main.css` defines `--shadow-md`, `--shadow-xl`, `--shadow-2xl` with `var(--shadow)` base | None -- already implemented |
| CM10 | Optional AI SDK import | STANDARD | If using AI SDK, add via standard dependency management | N/A | N/A | Only relevant if the app uses AI features. Agent adds via `pnpm add` if needed |

---

### Category: Authentication Context -- Rules AC1-AC7

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| AC1 | UserProfile interface with role | STANDARD | User profile includes `role` field with defined values (user, pro, admin) | PARTIAL | `nextjs/schema.sql` `users` table exists and is **populated by signups** via `handle_new_user()` trigger, but has NO role column | Agent must: (1) Add `role text DEFAULT 'user' CHECK (role IN ('user', 'pro', 'admin'))` column to users table via migration, (2) Add RLS policy preventing users from modifying their own role, (3) Update `types_db.ts` |
| AC2 | Auth context provides full interface | STANDARD | Auth state provider exposes: user, profile, loading, sign-in/out, isAdmin, isPro | HANDLED | `nextjs/utils/supabase/api.ts` provides **fully operational** auth functions: `passwordSignin`, `passwordSignup`, `passwordReset`, `passwordUpdate`, `oauthSignin`, `signOut`, `resendEmailVerification`. Server-side: `supabase.auth.getUser()` returns user object. Client-side: `createClient()` provides full auth API. Missing: role convenience booleans (isAdmin, isPro) -- requires role column first | Mostly handled. Agent must add role convenience booleans (isAdmin, isPro) after adding role column (AC1). Consider creating a unified auth hook |
| AC3 | Profile created on first login | CRITICAL | On first auth where no DB profile exists, auto-create with default role and server timestamps | HANDLED | `nextjs/schema.sql` has `handle_new_user()` trigger that fires on `auth.users` insert, creating a `users` row with id, full_name, avatar_url from metadata. **Now actively firing on real signups** | None -- already implemented and **operational** |
| AC4 | Default role is 'user' | CRITICAL | New profiles get lowest-privilege role; elevation only through admin tools | MUST_BUILD | N/A -- no role column exists | Agent must add role column with `DEFAULT 'user'` and RLS policy preventing self-modification. See AC1 |
| AC5 | Service init order critical | CRITICAL | Backend service client initialized before dependent services | HANDLED | `nextjs/utils/supabase/client.ts` and `server.ts` use `createBrowserClient()` / `createServerClient()` from `@supabase/ssr` which handles initialization order | None -- Supabase SSR handles this correctly |
| AC6 | Popup/redirect sign-in flow | CRITICAL | Use auth provider's popup or redirect flow; catch errors with user-friendly feedback | HANDLED | `nextjs/utils/supabase/api.ts` `oauthSignin()` uses `signInWithOAuth` with `redirectTo: getURL('/api/auth_callback')`. Password flows use direct API calls. `AuthForm.tsx` catches errors and shows toast. **Fully operational** | None -- already implemented and **operational** |
| AC7 | Loading state during auth check | STANDARD | App shows loading state while initial auth check resolves; prevents flash of wrong content | HANDLED | Server components resolve auth before rendering -- no FOUC. `AuthForm.tsx` has `loading` state during submissions. Auth page redirects logged-in users to `/`. **Functional with real auth sessions** | None -- already implemented. Server-side auth check prevents flash of unauthenticated content |

---

### Category: Theme Context (Dark Mode) -- Rules TC1-TC4

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| TC1 | localStorage persistence | STANDARD | Read theme preference from localStorage on mount; save on toggle | HANDLED | `next-themes` package handles localStorage persistence automatically | None -- already implemented |
| TC2 | System preference fallback | STANDARD | If no saved preference, check `prefers-color-scheme: dark` | HANDLED | `nextjs/app/layout.tsx` ThemeProvider has `enableSystem` and `defaultTheme="system"` | None -- already implemented |
| TC3 | Class on html element | STANDARD | Dark mode class toggled on root HTML element | HANDLED | `nextjs/app/layout.tsx` ThemeProvider `attribute="class"` + `<html suppressHydrationWarning>` | None -- already implemented |
| TC4 | ThemeToggle component required | STANDARD | Toggle button that switches light/dark; shows icon of opposite mode | HANDLED | `nextjs/components/landing/mode-toggle.tsx` | None -- already implemented |

---

### Category: Route Guards -- Rules RG1-RG5

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| RG1 | ProtectedRoute for auth users | CRITICAL | Route guard checks auth state; redirects unauthenticated to login; spinner while loading | HANDLED | `nextjs/app/account/page.tsx` checks auth server-side via `supabase.auth.getUser()` and redirects to `/auth/signin` if not authenticated. Auth page redirects authenticated users to `/`. **Functionally guards routes with real auth sessions**. Not a reusable wrapper component, but the pattern works | Pattern works but is not DRY. Agent should create a reusable auth guard (either as middleware route matcher or a wrapper component) for all new protected routes |
| RG2 | AdminRoute for admin only | CRITICAL | Extends auth guard; checks role is admin; redirects non-admins to dashboard | MUST_BUILD | N/A -- no role system exists | Agent must build after adding role column (AC1). Create AdminRoute guard that checks `role === 'admin'` |
| RG3 | ProRoute for pro/admin | STANDARD | Checks role is pro or admin; redirects others to dashboard or upgrade page | MUST_BUILD | N/A -- no role system exists | Agent must build after adding role column. Create ProRoute guard checking `role IN ('pro', 'admin')` |
| RG4 | Route wrapping order | STANDARD | RouteGuard > Layout > Page | PARTIAL | Next.js App Router uses `layout.tsx` files. Account page checks auth in its server component. But no explicit guard wrapping pattern | Agent should establish a consistent layout pattern with auth checking in layout.tsx for protected route groups (e.g., `app/(protected)/layout.tsx`) |
| RG5 | Provider nesting order | STANDARD | ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router | PARTIAL | `nextjs/app/layout.tsx` has ThemeProvider > PHProvider > Toaster. No ErrorBoundary wrapping the app. No explicit AuthProvider (auth handled via Supabase SSR server-side) | Agent must add ErrorBoundary as outermost wrapper in layout.tsx. Auth is handled via Supabase SSR (server-side), so an AuthProvider is optional but recommended for client-side convenience |

---

### Category: Data Structure -- Rules DS1-DS4

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DS1 | User data scoped to user | CRITICAL | All user-owned data scoped to authenticated user via RLS or user-specific paths | HANDLED | `nextjs/schema.sql` -- all tables with user data have RLS: `users` (auth.uid() = id), `subscriptions` (auth.uid() = user_id), `checkout_sessions` (auth.uid() = user_id). `customers` is private (no access). **Now enforced against real user sessions** | None -- already implemented. Agent must maintain RLS on all new tables |
| DS2 | Helper for user data access | STANDARD | Utility function that abstracts database path/query construction for user-scoped data | HANDLED | `nextjs/utils/supabase/queries.ts` provides `getUser()`, `getSubscription()`, `getProducts()`, `getUserDetails()` with React cache. **Now returning real data for authenticated users** | Agent should create a generic helper or ensure all new queries follow the pattern in `queries.ts`. RLS handles scoping automatically in Supabase |
| DS3 | Server timestamps on all writes | CRITICAL | Every record has `createdAt`/`updatedAt` using server-generated timestamps; never client-side dates | PARTIAL | `nextjs/schema.sql` -- `subscriptions.created`, `checkout_sessions.created` use `DEFAULT timezone('utc', now())`. But `users` table has NO `created_at` or `updated_at` columns. Timestamps set by DB triggers, not by app code | Agent must: (1) Add `created_at` and `updated_at` columns to `users` table, (2) Create a trigger to auto-update `updated_at` on updates, (3) Ensure all new tables include both timestamp columns with defaults |
| DS4 | Default sort newest first | POLISH | All list queries default to descending `createdAt` order | HANDLED | `nextjs/utils/supabase/queries.ts` `getSubscription()` orders by `created` descending. `getProducts()` orders by `metadata->index`. Queries execute against live data | Agent must ensure all new list queries use `order('created_at', { ascending: false })` by default |

---

### Category: Data Service Layer -- Rules DSL1-DSL4

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DSL1 | No database calls in components | STANDARD | All DB operations through service layer; components never import DB client directly | PARTIAL | `nextjs/utils/supabase/queries.ts` exists as query layer. BUT `Pricing.tsx` calls `supabase.from('products')` directly. `AccountPage.tsx` calls `supabase.functions.invoke()` directly | Agent must refactor: move all Supabase calls from components into `queries.ts` or a new `services/` module. Components should only call service functions |
| DSL2 | CRUD helper functions | STANDARD | Four base CRUD functions wrapping DB operations with automatic timestamp injection | PARTIAL | No generic CRUD helpers exist. `queries.ts` has read-only helpers. Auth API wrapper (`api.ts`) provides complete auth CRUD: `passwordSignup`, `passwordSignin`, `passwordReset`, `passwordUpdate`, `oauthSignin`, `signOut`, `resendEmailVerification` | Agent must create generic CRUD helpers: `createRecord(table, data)`, `updateRecord(table, id, data)`, `deleteRecord(table, id)`, `getRecords(table, filters)` that auto-inject `updated_at` on writes |
| DSL3 | Realtime subscription pattern | STANDARD | Use DB's realtime subscription mechanism; return cleanup function | PARTIAL | `nextjs/schema.sql` enables realtime publication for `products` and `prices`. But no frontend code subscribes to realtime updates | Agent must implement realtime subscription hook if any feature needs live data updates. The DB-side is ready; frontend needs `supabase.channel().on('postgres_changes', ...)` pattern |
| DSL4 | Delete account function | CRITICAL | Account deletion removes all user-owned data before removing user profile; cascading delete explicit | MUST_BUILD | N/A -- no account deletion function exists anywhere. `AccountPage.tsx` only has sign-out, no delete. **With auth active, users exist in the DB and cannot delete their accounts** | Agent must build: (1) Account deletion UI with typed confirmation, (2) Server-side function that deletes from `checkout_sessions`, `subscriptions`, `customers`, `users` WHERE user_id matches, (3) Call Supabase `auth.admin.deleteUser()` via edge function. **URGENCY: HIGH -- see Urgency Flags** |

---

### Category: Routing Structure -- Rules RS1-RS4

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| RS1 | Router wraps all routes | STANDARD | Router component wraps all route definitions; public vs protected separated | HANDLED | Next.js App Router handles this via folder structure. `nextjs/app/` is the router | None -- App Router is the standard for Next.js |
| RS2 | Public vs protected routes | CRITICAL | Landing and login are public; dashboard, profile, CRUD pages are protected | HANDLED | `nextjs/app/page.tsx` (landing) is public. `nextjs/app/auth/` is public but redirects authenticated users. `nextjs/app/account/page.tsx` checks auth and redirects unauthenticated users. **Clear separation enforced with real auth sessions** | None for existing routes. Agent must add auth checks to all new protected routes |
| RS3 | 404 catch-all | STANDARD | Last route catches unmatched paths and renders Not Found page | MUST_BUILD | N/A -- no `not-found.tsx` file exists | Agent must create `nextjs/app/not-found.tsx` with a styled Not Found page including a link back to home |
| RS4 | CRUD route pattern | STANDARD | Standard CRUD routes: `/items`, `/items/new`, `/items/:id`, `/items/:id/edit` | MUST_BUILD | N/A -- no CRUD routes exist. Only landing, auth, and account pages | Agent must create CRUD routes as features require them, following App Router convention: `app/{entity}/page.tsx` (list), `app/{entity}/new/page.tsx` (create), `app/{entity}/[id]/page.tsx` (detail), `app/{entity}/[id]/edit/page.tsx` (edit) |

---

### Category: Data/API Patterns -- Rules DAP1-DAP9

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DAP1 | Delete account removes all user data | CRITICAL | Iterate all user-data categories, delete all records, then delete user profile | MUST_BUILD | N/A. **With auth active, users exist and cannot be deleted** | See DSL4. Agent must build cascading delete covering all user-owned tables. **URGENCY: HIGH** |
| DAP2 | Data category list is explicit | STANDARD | Pass explicit list of data category names to deletion function; no dynamic discovery | MUST_BUILD | N/A | Agent must maintain an explicit list of tables containing user data and update it as new tables are added |
| DAP3 | Realtime subscription pattern | STANDARD | Use DB's realtime subscription; map to normalized format; return cleanup function | PARTIAL | DB-side realtime enabled for products/prices. No frontend subscription code | Agent must implement as needed per feature. Create a `useRealtimeSubscription` hook |
| DAP4 | CRUD helper layer | STANDARD | All DB operations through service module with CRUD helpers; auto timestamps | MUST_BUILD | N/A | See DSL2. Create generic service layer |
| DAP5 | Records always include timestamps | CRITICAL | Every record has `createdAt`/`updatedAt` using server timestamps; never `new Date()` | PARTIAL | Subscriptions and checkout_sessions have `created` with DB default. Users table has no timestamps. No `updated_at` on any table | Agent must add `created_at`/`updated_at` to all existing tables via migration and ensure all new tables include them with `DEFAULT now()` and an update trigger |
| DAP6 | Default sort order | STANDARD | All lists default to descending createdAt (newest first) | HANDLED | `getSubscription()` sorts by `created` desc. Queries execute against live data | Agent must enforce this pattern on all new list queries |
| DAP7 | List pagination is mandatory | STANDARD | Every list view implements pagination, load-more, or infinite scroll. Pick ONE strategy | MUST_BUILD | N/A -- no list views with pagination exist | Agent must implement pagination for all list views. Choose one strategy (e.g., offset pagination with `.range()` in Supabase) and use consistently |
| DAP8 | Pagination controls pattern | POLISH | ITEMS_PER_PAGE constant, page state, Previous/Next buttons, "Page X of Y" | MUST_BUILD | N/A | Agent must build a reusable Pagination component |
| DAP9 | Load-more shows remaining count | POLISH | Load-more button displays remaining count; initial limit 10, increment by 10 | MUST_BUILD | N/A | Agent must build if choosing load-more strategy instead of pagination |

---

### Category: Authentication/Security -- Rules AS1-AS6

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| AS1 | Delete account requires typed confirmation | CRITICAL | User types "DELETE" to confirm; submit disabled until exact match | MUST_BUILD | N/A -- no account deletion exists. **Users exist and cannot delete accounts** | Agent must build: ConfirmModal with text input, submit disabled until input === 'DELETE'. **URGENCY: HIGH** |
| AS2 | Delete button disabled during operation | STANDARD | Check both confirmation text match AND in-progress state; show "Deleting..." | MUST_BUILD | N/A | Agent must build as part of account deletion flow |
| AS3 | Logout after account deletion | CRITICAL | After successful deletion, clear auth session before showing success | MUST_BUILD | N/A | Agent must call `supabase.auth.signOut()` after deletion completes |
| AS4 | Protected routes wrap layout | STANDARD | All authenticated pages: RouteGuard > Layout > Page; public pages no auth wrapper | HANDLED | Account page checks auth server-side. Auth pages redirect authenticated users. **Pattern works with real sessions** | Agent should create `app/(protected)/layout.tsx` for consistency on all new protected routes |
| AS5 | Auth/theme/toast providers wrap router | STANDARD | Provider nesting: ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router | PARTIAL | layout.tsx has ThemeProvider > PHProvider > main > Toaster. No ErrorBoundary | Agent must add ErrorBoundary as outermost wrapper |
| AS6 | Admin-only nav items conditional | CRITICAL | Navigation conditionally renders admin links based on role | MUST_BUILD | N/A -- no role system, no admin nav items | Agent must implement after adding role system: conditionally render admin navigation items |

---

### Category: Database/Storage -- Rules DBS1-DBS3

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DBS1 | User data scoped to owner | CRITICAL | All user-owned data scoped via user-specific paths or RLS policies | HANDLED | All tables with user data have RLS enabled in `schema.sql`. **Enforced against real user sessions** | None -- already implemented. Maintain for new tables |
| DBS2 | Delete cascades to all user data | CRITICAL | Account deletion removes all records in every user-data category BEFORE deleting user profile | MUST_BUILD | N/A. **Users exist in DB and cannot delete their data** | Agent must build cascading delete function. **URGENCY: HIGH** |
| DBS3 | Batch deletes for efficiency | STANDARD | Bulk deletion fetches all, maps to deletes, awaits concurrently | MUST_BUILD | N/A | Agent must implement using Supabase `.delete().eq('user_id', uid)` per table (SQL handles batch natively) |

---

### Category: Error Handling -- Rules EH1-EH5

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| EH1 | Delete failure keeps modal open | STANDARD | On delete error: show error toast, reset loading, do NOT close modal, do NOT navigate | MUST_BUILD | N/A -- no delete modal exists | Agent must build as part of account deletion and all CRUD delete flows |
| EH2 | Success feedback is toast + navigate | STANDARD | Every successful mutation: toast with message, then navigate to next logical view | PARTIAL | `AuthForm.tsx` shows toasts on auth success/error. `AccountPage.tsx` shows toast on sign-out and billing errors. **Auth toasts now showing for real user actions** | Agent must ensure all new mutations follow this pattern |
| EH3 | Error feedback preserves form state | STANDARD | On error: show toast, stay on current view, do NOT clear form data | HANDLED | `AuthForm.tsx` preserves form state on error (email, password fields not cleared). **Working with real auth errors** | None -- pattern exists. Agent must follow it for all new forms |
| EH4 | Delete flow is 6-step | STANDARD | Click > confirmation dialog > confirm > loading state + disabled > success toast + redirect OR error toast + close modal | MUST_BUILD | N/A | Agent must implement this exact flow for all delete operations |
| EH5 | Loading states match content shape | STANDARD | Lists show skeleton cards, detail views show skeleton matching layout, buttons show inline spinner | PARTIAL | `nextjs/components/ui/skeleton.tsx` exists. `Pricing.tsx` uses `<Skeleton className="h-9 w-16" />` for price loading. But no skeleton patterns for lists or detail views | Agent must create skeleton patterns for each new view type (list skeleton cards, detail skeleton layout) |

---

### Category: Performance -- Rules P1-P4

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| P1 | Animations use short durations | POLISH | Modal: 200ms. Toast: 300ms. Card hover: 200ms. Button press: 150ms. Never exceed 300ms | PARTIAL | `nextjs/styles/main.css` defines `accordion-down/up` at 0.2s, `appear` at 0.6s, `appear-zoom` at 0.6s. `tw-animate-css` provides additional animations. But 0.6s appear animations exceed the 300ms guideline | Agent should reduce appear/appear-zoom animations to 300ms max for UI transitions |
| P2 | Card hover uses translate | POLISH | Card hover: elevated shadow + slight upward translate; 200ms transition | MUST_BUILD | N/A -- no card hover effects defined in the boilerplate | Agent must add `hover:shadow-md hover:-translate-y-0.5 transition-all duration-200` to card components |
| P3 | Button press uses scale | POLISH | Buttons have scale-down on press (0.98) with 150ms transition | MUST_BUILD | N/A -- no press animation on buttons | Agent must add `active:scale-[0.98] transition-transform duration-150` to the Button component |
| P4 | Choose one pagination strategy | STANDARD | Pick one (pagination/load-more/infinite scroll) and use consistently across ALL lists | MUST_BUILD | N/A | Agent must choose one strategy before building any list views |

---

### Category: UX Standards -- Rules UX1-UX23

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| UX1 | Six required UI components | STANDARD | Modal, ConfirmModal, Toast, ToastContext, Skeleton, EmptyState | PARTIAL | Has: `dialog.tsx` (Modal), `toast.tsx` + `toaster.tsx` + `use-toast.ts` (Toast system), `skeleton.tsx`. Missing: ConfirmModal, EmptyState | Agent must create: (1) ConfirmModal component (destructive action confirmation with typed confirmation), (2) EmptyState component (icon + message + CTA button) |
| UX2 | Browser dialogs banned | STANDARD | Never use alert(), confirm(), prompt(), console.log for user feedback | HANDLED | `AuthForm.tsx` uses toast for all feedback. No alert/confirm/prompt found | None -- already followed. Agent must maintain this pattern |
| UX3 | Text-only empty states banned | STANDARD | Empty states need icon + descriptive message + CTA button | MUST_BUILD | N/A -- no EmptyState component exists | Agent must create EmptyState component and use it wherever lists can be empty |
| UX4 | Loading text banned | STANDARD | Never display bare "Loading..." text; use Skeleton components | PARTIAL | `Pricing.tsx` uses Skeleton for price loading. But no systematic skeleton usage | Agent must use Skeleton components for all loading states |
| UX5 | List-Detail-Create-Edit flow | STANDARD | All user data CRUD: List (cards + "Create New"), Detail (read-only + Edit/Delete), Create (form > Detail), Edit (pre-filled form > Detail) | MUST_BUILD | N/A -- no CRUD views exist in the boilerplate | Agent must implement this 4-view pattern for every user data entity |
| UX6 | No edit-first pattern | STANDARD | Items always open in read-only Detail view; Create and Edit are separate views | MUST_BUILD | N/A | Agent must follow this pattern: clicking an item opens Detail (read-only), Edit is a separate route |
| UX7 | Delete always requires confirmation | STANDARD | Every delete through confirmation dialog; no silent deletes | MUST_BUILD | N/A | Agent must build ConfirmModal and use it for all delete actions |
| UX8 | Every action needs user feedback | POLISH | Every mutation shows success or error notification | PARTIAL | Auth actions show toasts. Billing actions show toasts (even though Stripe is dormant) | Agent must ensure all new mutations show toast feedback |
| UX9 | Cancel-edit returns to detail | POLISH | Cancel in Edit view navigates to Detail view of same item | MUST_BUILD | N/A | Agent must implement this navigation pattern |
| UX10 | Cancel-create returns to list | POLISH | Cancel in Create view navigates to List view | MUST_BUILD | N/A | Agent must implement this navigation pattern |
| UX11 | Never show raw timestamps | STANDARD | Date formatting utility: "Just now", "5m ago", "2h ago", "Yesterday", etc. | MUST_BUILD | N/A -- no date formatting utility | Agent must create `utils/formatDate.ts` with relative time formatting |
| UX12 | Text truncation mandatory | STANDARD | Sidebar items: ~30 chars. Card descriptions: 2 lines. Table cells: ~20 chars. Always with max-width | MUST_BUILD | N/A | Agent must apply truncation CSS (`truncate`, `line-clamp-2`) to all text that can overflow |
| UX13 | Back navigation on every sub-page | STANDARD | Detail and Edit pages must have back button at top | MUST_BUILD | N/A | Agent must add back navigation to all detail/edit pages |
| UX14 | Five required animations | POLISH | Modal backdrop fade + content scale, toast slide-in, card hover lift, button press scale, sidebar mobile slide-in | PARTIAL | Toast has animations via Radix Toast. Sheet (mobile sidebar) has slide animation. Modal (dialog) has animations. Missing: card hover lift, button press scale | Agent must add card hover lift and button press scale animations |
| UX15 | Danger zone styling | POLISH | Account deletion section: extra top spacing, separator, red heading, red button. "Danger Zone" label | MUST_BUILD | N/A -- no danger zone section exists (no delete account feature) | Agent must build as part of account deletion feature |
| UX16 | Modal overlay pattern | STANDARD | Fixed full-screen overlay, semi-transparent black, flex centering, high z-index | HANDLED | `nextjs/components/ui/dialog.tsx` (Radix Dialog) provides this pattern | None -- already implemented via Radix Dialog |
| UX17 | Focus states on all interactive elements | STANDARD | Every button, link, input has visible focus indicators | HANDLED | `nextjs/components/ui/button.tsx` and `input.tsx` include focus ring styles. Tailwind v4 provides `focus-visible` utilities | None -- already implemented |
| UX18 | Escape key closes modals | STANDARD | Every modal listens for Escape and closes | HANDLED | Radix Dialog handles Escape key automatically | None -- already implemented |
| UX19 | Focus trap in modals | STANDARD | Modals trap keyboard focus; Tab cycles within modal only | HANDLED | Radix Dialog handles focus trapping automatically | None -- already implemented |
| UX20 | Icon buttons need aria-label | STANDARD | Every icon-only button has aria-label describing the action | PARTIAL | `Navbar.tsx` hamburger Menu button is wrapped in `<Button variant="ghost" size="icon">` but has no aria-label. Theme toggle may or may not have aria-label | Agent must audit all icon-only buttons and add `aria-label` attributes. Add to Navbar hamburger menu at minimum |
| UX21 | Screen reader loading states | POLISH | Add sr-only text alongside visual loading indicators | MUST_BUILD | N/A | Agent must add `<span className="sr-only">Loading...</span>` alongside all visual loading indicators |
| UX22 | Status updates use aria-live | POLISH | Dynamic status messages use `role="status"` and `aria-live="polite"` | PARTIAL | Radix Toast uses aria-live regions automatically | Agent must add aria-live regions for other dynamic content (form errors, status changes) |
| UX23 | 404 catch-all route | STANDARD | Router includes catch-all for unmatched URLs | MUST_BUILD | N/A -- no `not-found.tsx` | Agent must create `app/not-found.tsx` |

---

### Category: Mobile/Responsive -- Rules MR1-MR14

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| MR1 | Mobile-first design | STANDARD | Default styles for mobile; breakpoint prefixes for tablet/desktop | HANDLED | Landing page components use responsive classes. Tailwind v4 mobile-first by default | None -- already implemented |
| MR2 | Three breakpoints | STANDARD | Mobile (<640px default), tablet (sm:640px+), desktop (lg:1024px+) | HANDLED | Tailwind v4 default breakpoints. Components use `md:` and `lg:` prefixes | None -- already implemented |
| MR3 | Sidebar hidden on mobile | STANDARD | Sidebar hidden by default on mobile; visible on desktop; hamburger toggles | PARTIAL | Navbar has mobile hamburger menu using Sheet component (`hidden md:flex` for desktop nav, `flex md:hidden` for mobile). But this is a top nav, not a sidebar | If app needs a sidebar layout, agent must build one. Current Navbar mobile pattern is acceptable for landing-page style apps |
| MR4 | Sidebar is overlay on mobile | STANDARD | Mobile sidebar slides over content, closes on outside click or nav item click | HANDLED | `Navbar.tsx` uses Radix Sheet (slide-over) with `onOpenChange` for close. Nav items have `onClick={() => setIsOpen(false)}` | None -- already implemented for the mobile nav sheet |
| MR5 | Cards stack vertically on mobile | STANDARD | Single column mobile, 2 columns tablet, 3 columns desktop | HANDLED | `Pricing.tsx` uses `grid md:grid-cols-2 lg:grid-cols-3 gap-8` | None -- pattern exists. Agent must follow it for new card grids |
| MR6 | Forms full width on mobile | STANDARD | Form inputs full width mobile, constrained max-width desktop | HANDLED | `AuthForm.tsx` card has `w-96` with `mx-4` margin. Inputs are `w-full` | None -- already implemented |
| MR7 | Primary buttons full width on mobile | STANDARD | Primary buttons full width mobile, auto width desktop | PARTIAL | `AuthForm.tsx` buttons are `w-full` always. No responsive width change | Agent should make primary buttons `w-full md:w-auto` in app pages (current landing page pattern is acceptable) |
| MR8 | Modals nearly full screen on mobile | STANDARD | Modals full-screen on mobile; centered max-w-md on desktop | HANDLED | Radix Dialog + Sheet components handle responsive modal sizing | None -- already implemented |
| MR9 | Minimum 16px text on mobile | STANDARD | Body text at least 16px on mobile to prevent iOS zoom | HANDLED | Tailwind v4 default font-size is 1rem (16px). No text smaller than 14px (`text-sm`) in main content | None -- already implemented |
| MR10 | 44px minimum touch targets | STANDARD | All clickable elements 44x44px minimum on mobile; padding for small icons | PARTIAL | Buttons have adequate size via padding. But icon buttons like the theme toggle and hamburger may be under 44px | Agent must audit touch targets and add padding where needed |
| MR11 | Responsive visibility patterns | POLISH | Use responsive utility classes for desktop-only/mobile-only content | HANDLED | `Navbar.tsx` uses `hidden md:flex` and `flex md:hidden` patterns | None -- already implemented |
| MR12 | Layout structure dimensions | POLISH | Sidebar ~240px, header ~64px, main flex-1 scrollable padded | PARTIAL | Navbar header is `h-14` (56px). No sidebar. Main content varies per page. AccountPage uses `p-4 md:gap-8 md:p-10` | Agent should standardize layout dimensions for the app shell |
| MR13 | Sidebar has bottom help link | POLISH | Pinned bottom section with separator and Help & Support link | MUST_BUILD | N/A -- no sidebar with help link | Agent must build if app has a sidebar layout |
| MR14 | Padding scales with breakpoint | POLISH | Main content: 16px mobile, 32px desktop | HANDLED | `AccountPage.tsx` uses `p-4 md:gap-8 md:p-10`. Landing page sections use responsive padding | None -- pattern exists |

---

### Category: Design System -- Rules DES1-DES7

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DES1 | Typography scale | STANDARD | 5-level scale: Page Title (24px semi-bold), Section Header (18px semi-bold), Card Title (16px medium), Body (14px regular), Small/Meta (12px regular) | PARTIAL | Components use various text sizes. `AccountPage.tsx` has `text-3xl font-semibold`. Card components use CardTitle/CardDescription. But no defined/documented typography scale | Agent should define a typography scale in CSS or a constants file and apply consistently |
| DES2 | Spacing scale | POLISH | Card padding: 24px. Section gaps: 24px. Element gaps: 16px | HANDLED | Cards use Radix Card with built-in padding. Sections use `gap-4` (16px) and `gap-6` (24px). Pricing grid uses `gap-8` (32px) | None -- spacing is reasonable. Agent should maintain consistency |
| DES3 | Card component class | STANDARD | Themed background, border radius, subtle border, shadow, padding | HANDLED | `nextjs/components/ui/card.tsx` exists with proper styling. Used in Pricing, AuthForm, AccountPage | None -- already implemented |
| DES4 | Primary button class | STANDARD | Brand color, darker on hover, primary text, medium weight, padding, rounded, transition | HANDLED | `nextjs/components/ui/button.tsx` with variant system (default, destructive, outline, secondary, ghost, link) | None -- already implemented |
| DES5 | Input field class | STANDARD | Muted background, primary text, tertiary placeholder, padding, rounded, full width, brand focus ring | HANDLED | `nextjs/components/ui/input.tsx` with proper styling and focus ring | None -- already implemented |
| DES6 | Sidebar nav item classes | POLISH | Vertical stack, small text, secondary color, primary on hover | PARTIAL | `AccountPage.tsx` has `nav` with `text-sm text-muted-foreground` links. `Navbar.tsx` desktop nav uses button variants | Agent must define sidebar nav styles if a sidebar layout is built |
| DES7 | Sidebar recent items section | POLISH | Top margin, extra-small heading, "Recent Items" section | MUST_BUILD | N/A | Agent must build if app has a sidebar layout |

---

### Category: Testing -- Rules T1-T7

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| T1 | Console clean before deploy | STANDARD | Zero console errors/warnings in production | MUST_BUILD | N/A -- no testing setup. `api.ts` line 29 has `console.log(res)` | Agent must remove all console.log statements and verify clean console before deploy |
| T2 | No console.log statements | STANDARD | Remove all console.log; use proper error handling | PARTIAL | `nextjs/utils/supabase/api.ts` line 29 has `console.log(res)`. Supabase edge functions use `console.log` for debugging | Agent must remove `console.log(res)` from `api.ts`. Edge function console.log is acceptable for server-side logging |
| T3 | No framework list key warnings | STANDARD | Every list provides unique key; never use array index for dynamic lists | PARTIAL | `Pricing.tsx` uses `key={tier.title}` (good). `Navbar.tsx` uses `key={i}` (bad -- uses array index) | Agent must fix `Navbar.tsx` to use `key={route.href}` instead of array index |
| T4 | No missing dependency warnings | POLISH | All reactive hooks have complete dependency declarations | PARTIAL | `AuthForm.tsx` has `useEffect(() => {...}, [])` with `toast` and `searchParams` not in deps | Agent should fix dependency arrays or add eslint-disable comments with justification |
| T5 | No unused variables | POLISH | Zero unused variable warnings | MUST_BUILD | N/A -- not verified. ESLint is configured but `npm run lint` status unknown | Agent must run `pnpm lint` and fix all unused variable warnings |
| T6 | No type errors | CRITICAL | Type checker passes with zero errors; no type-ignore without reason | HANDLED | TypeScript 5.5 configured. `types_db.ts` auto-generated for type safety | None -- agent must maintain zero type errors |
| T7 | Full app navigation test | STANDARD | Before deploy, manually click through every route, form, modal | MUST_BUILD | N/A -- no automated or manual test procedure | Agent must verify all routes work before declaring features complete |

---

### Category: Deployment/Hosting -- Rules DH1-DH5

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DH1 | Config uses placeholder values | CRITICAL | Service config ships with placeholder values; never hardcode real credentials | HANDLED | `.env.example` has `YOUR_*` placeholders for all secrets. `.gitignore` blocks `.env` | None -- already implemented |
| DH2 | Favicon required | POLISH | Favicon with app's initial letter and brand color | PARTIAL | `nextjs/public/favicon.ico` exists (referenced in layout.tsx metadata). But it's the default, not branded | Agent should replace with a branded favicon using the app's initial letter and brand color |
| DH3 | Error boundary wraps app | CRITICAL | Top-level error boundary wraps entire app; shows "Something went wrong" + Refresh button | MUST_BUILD | N/A -- no error boundary in layout.tsx or anywhere | Agent must create an ErrorBoundary component and wrap the app in `layout.tsx`. Next.js has `error.tsx` convention -- create `app/error.tsx` and `app/global-error.tsx` |
| DH4 | Dependency config locked | STANDARD | Do not change dependency versions without approval | HANDLED | pnpm lockfile committed | None -- already implemented |
| DH5 | No redundant package entries | STANDARD | No redundant sub-package entries | HANDLED | Clean package.json | None -- already implemented |

---

### Category: Post-Generation Steps -- Rules PG1-PG5

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| PG1 | Replace service config placeholders | STANDARD | Replace all `YOUR_*` placeholders with real values | PARTIAL | `.env.example` has placeholders. Agent must copy to `.env.local` and fill in real values. **Auth-specific vars MUST be set:** `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Agent must provide instructions or prompt for required env vars. Auth env vars must be configured for auth to work |
| PG2 | Replace favicon letter | POLISH | Change favicon letter to app initial, background to brand color | MUST_BUILD | N/A -- default favicon | Agent must create branded favicon |
| PG3 | Replace app name in title | STANDARD | Change app name in page title utility | PARTIAL | `layout.tsx` has `title: 'DevToDollars'` hardcoded. No page title hook | Agent must replace 'DevToDollars' with the actual app name and create a `usePageTitle` hook or use Next.js metadata API consistently |
| PG4 | Set data category names for delete | STANDARD | Update deletion handler with every user-data table | MUST_BUILD | N/A -- no deletion handler exists. **Now critical with real users in DB** | Agent must build deletion handler with explicit table list |
| PG5 | Set help email | STANDARD | Replace placeholder email in Help & Support link | PARTIAL | `AccountPage.tsx` has `<Link href="mailto:">Support</Link>` -- mailto is empty | Agent must set the actual support email address |

---

### Category: Build Instructions -- Rules BI1-BI30

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| BI1 | Complete file structure | STANDARD | Generate all files; one component per file; feature folders | HANDLED | File structure exists and follows conventions | None -- agent extends as needed |
| BI2 | Follow exact patterns | STANDARD | Use provided patterns for auth, theme, route guards, error boundary, service layer, UI | PARTIAL | Auth and theme patterns exist and are **operational**. Route guards, error boundary, and full service layer are missing | Agent must build missing patterns following Martin's specs |
| BI3 | Build Section 2 features | STANDARD | Implement core features using CRUD view pattern | MUST_BUILD | N/A -- only landing, auth, account exist | Agent builds app-specific features |
| BI4 | Apply design system styling | STANDARD | Use design tokens, typography scale, spacing, card styles, color tokens | HANDLED | CSS variables, semantic tokens, component library all configured | None -- agent uses existing design tokens |
| BI5 | Auth and data access working | CRITICAL | Sign-in, protected routes, CRUD through service layer, role-based access all functional end-to-end | PARTIAL | Sign-in works. Account page is auth-gated. **Auth is fully operational.** No CRUD service layer. No role-based access | Agent must build service layer and role system. Auth foundation is solid |
| BI6 | Production ready | CRITICAL | ErrorBoundary, toast on all actions, ConfirmModal on destructive actions, skeleton loading, offline handling, session expiry | PARTIAL | Toast system works. Skeleton component exists. Missing: ErrorBoundary, ConfirmModal, offline handling, session expiry handling | Agent must build ErrorBoundary, ConfirmModal, offline banner, session expiry detection |
| BI7 | Single icon library | POLISH | All icons from one library; consistent standard size; spinner icon | PARTIAL | Uses Lucide React (primary) + react-simple-icons (brand icons) | Acceptable -- agent uses Lucide React for all new icons |
| BI8 | Dynamic page titles | POLISH | Every page updates document.title via shared hook | PARTIAL | layout.tsx sets static metadata. No per-page dynamic titles | Agent must use Next.js `generateMetadata()` or `metadata` export in each page |
| BI9 | Autofocus on forms | POLISH | Focus first input on page/modal mount | MUST_BUILD | N/A -- AuthForm does not autofocus | Agent must add `autoFocus` to the first input in AuthForm and all new forms |
| BI10 | Pluralization helper | POLISH | `pluralize(count, singular, plural?)` utility | MUST_BUILD | N/A | Agent must create `utils/pluralize.ts` |
| BI11 | Search/filter for lists | POLISH | Lists >5 items need search input filtering by title and description | MUST_BUILD | N/A -- no list views | Agent must add search/filter to all list views expected to exceed 5 items |
| BI12 | Retry on error states | STANDARD | Every error display has "Try Again" button re-invoking the failed operation | MUST_BUILD | N/A -- error displays don't have retry | Agent must add retry buttons to all error states |
| BI13 | Network/offline handling | STANDARD | Catch network errors with friendly messages; show offline banner via navigator.onLine | MUST_BUILD | N/A | Agent must implement offline detection and banner |
| BI14 | Session expiry handling | CRITICAL | Catch auth expiry in data access; show "Session expired" toast; redirect to login | PARTIAL | `nextjs/utils/supabase/middleware.ts` refreshes session on each request. **Middleware now actively refreshing real sessions.** But no explicit expiry handling in client-side code | Agent must add session expiry detection in the API client layer and redirect to login with toast |
| BI15 | Loading button pattern | POLISH | Button accepts `loading` prop; shows spinner, updates text, sets disabled | PARTIAL | `AuthForm.tsx` uses `disabled={loading}` on buttons. But no inline spinner or text change | Agent must enhance Button component or create LoadingButton variant with spinner icon |
| BI16 | User avatar with fallback | POLISH | Avatar shows profile image with onError fallback to initials | PARTIAL | `nextjs/components/ui/avatar.tsx` exists (Radix Avatar with fallback). But not used in the app UI | Agent must use Avatar component in Navbar/AccountPage with initials fallback. **Auth provides avatar_url from OAuth metadata** |
| BI17 | Form field states | STANDARD | Every input handles 6 states: default, focused, filled, error, disabled, helper text | PARTIAL | Input component handles default, focused (ring), disabled. `AuthForm.tsx` handles error via toast (not inline). No helper text pattern | Agent must create a FormField wrapper component with inline error messages and helper text |
| BI18 | Unsaved changes warning | STANDARD | beforeunload event for browser nav; confirmation dialog for in-app nav | MUST_BUILD | N/A | Agent must implement `useUnsavedChanges` hook with beforeunload + router guard |
| BI19 | 404 / not found handling | STANDARD | Catch-all route; detail pages show EmptyState for missing data | MUST_BUILD | N/A -- no not-found.tsx, no EmptyState | Agent must create `app/not-found.tsx` and handle missing data in detail pages |
| BI20 | Hover states on all interactives | POLISH | Cards: shadow + translate. Buttons: darker shade. Links: underline. Icon buttons: muted bg | PARTIAL | Button component has hover variants. No card hover effects | Agent must add hover states to cards and icon buttons |
| BI21 | Date formatting | STANDARD | Utility returning relative time strings | MUST_BUILD | N/A | Agent must create `utils/formatDate.ts` |
| BI22 | Text truncation | STANDARD | Sidebar: max-width truncate. Cards: line-clamp-2. Tables: truncate | MUST_BUILD | N/A | Agent must apply truncation as views are built |
| BI23 | Back navigation | STANDARD | Back button at top of every detail/edit page | MUST_BUILD | N/A | Agent must add to all detail/edit pages |
| BI24 | Transitions and animations | POLISH | Modal fade/scale, toast slide-in, card hover lift, button press scale, sidebar slide | PARTIAL | Modal and toast animations exist. Missing: card hover lift, button press scale | Agent must add card hover and button press animations |
| BI25 | Accessibility - focus states | STANDARD | Focus ring on all buttons, inputs, links | HANDLED | Tailwind v4 + Radix components handle focus states | None -- already implemented |
| BI26 | Accessibility - keyboard nav | STANDARD | Escape closes modals; focus trap in modals | HANDLED | Radix Dialog handles both | None -- already implemented |
| BI27 | Accessibility - icon buttons | STANDARD | Icon-only buttons need aria-label | PARTIAL | Some icon buttons lack aria-label | Agent must audit and add aria-labels |
| BI28 | Accessibility - screen reader | STANDARD | sr-only text for loading indicators; aria-live for status | PARTIAL | Radix Toast handles aria-live. No sr-only loading text | Agent must add sr-only text to loading states |
| BI29 | Pagination or load-more | STANDARD | Choose ONE approach, implement consistently, 10-20 items per page | MUST_BUILD | N/A | Agent must implement when building list views |
| BI30 | CSS variables for dark mode | STANDARD | Light in :root, dark in .dark class; reference via var(--color-*) | HANDLED | `nextjs/styles/main.css` implements exactly this pattern | None -- already implemented |

---

### Category: Miscellaneous Rules -- Rules MISC1-MISC18

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| MISC1 | No database calls in components | STANDARD | All DB ops through service layer | PARTIAL | `Pricing.tsx` and `AccountPage.tsx` call Supabase directly | Agent must refactor to use service layer |
| MISC2 | No unprotected auth routes | CRITICAL | Every authenticated route must be wrapped in route guard | HANDLED | Account page checks auth server-side and redirects. Auth pages redirect authenticated users. **Pattern works with real sessions.** Not middleware-level but functionally guarded | Agent must add consistent auth checking to all new protected routes |
| MISC3 | No inline styles | STANDARD | All styling via Tailwind; no style attributes | HANDLED | No inline styles found in boilerplate components | None -- agent must maintain |
| MISC4 | No `any` types | STANDARD | Define typed interfaces for all data shapes | PARTIAL | `types_db.ts` auto-generated. `utils/types.ts` has app types. `Pricing.tsx` has `as unknown as ProductWithPrices[]` type cast | Agent should minimize type casts and ensure all new code is fully typed |
| MISC5 | Timestamps on all writes | CRITICAL | Every write includes createdAt/updatedAt with server timestamps | PARTIAL | DB tables use `DEFAULT now()` for `created`. No `updated_at` column or trigger | Agent must add `updated_at` columns and triggers to all tables |
| MISC6 | User data scoped to owner | CRITICAL | All user data scoped via RLS | HANDLED | RLS enabled on all tables. **Enforced against real user sessions** | None -- agent must maintain for new tables |
| MISC7 | Detail view separate from edit | STANDARD | Detail is read-only; Edit is a separate route | MUST_BUILD | N/A -- no CRUD views | Agent must implement when building features |
| MISC8 | Validate before submit | CRITICAL | Client-side validation on all required fields before backend call | PARTIAL | `AuthForm.tsx` validates password match before signup. But no inline validation errors shown per field | Agent must implement form validation with per-field inline errors for all new forms |
| MISC9 | One component per file | STANDARD | Each component in its own file | HANDLED | All components follow this | None -- already implemented |
| MISC10 | Feature folders for grouping | STANDARD | Related components in feature directories | HANDLED | `components/landing/`, `components/misc/`, `components/ui/`, `components/icons/` | None -- agent creates new feature folders as needed |
| MISC11 | Interfaces for all data types | STANDARD | Every data shape has a type definition | PARTIAL | `types_db.ts` covers DB types. `utils/types.ts` covers app types. `Pricing.tsx` has inline `PricingTier` and `ProductWithPrices` interfaces | Agent should move inline interfaces to central types file |
| MISC12 | Custom hooks for reusable logic | POLISH | Extract shared stateful logic into hooks | PARTIAL | `use-toast.ts` exists. No other custom hooks | Agent must create custom hooks as reusable patterns emerge |
| MISC13 | No pinned AI SDK versions | POLISH | Don't pin optional AI SDK versions | N/A | No AI SDK in the boilerplate | Only relevant if app uses AI features |
| MISC14 | Mobile-first responsive | STANDARD | Default styles target mobile; breakpoint prefixes for larger | HANDLED | Tailwind v4 mobile-first approach used throughout | None -- already implemented |
| MISC15 | Touch targets 44px minimum | STANDARD | Add padding to meet 44px minimum tap target | PARTIAL | Most buttons are large enough. Icon buttons may be under 44px | Agent must audit and fix |
| MISC16 | Service init order | CRITICAL | Backend client initialized before dependent services | HANDLED | Supabase SSR handles initialization order | None -- already implemented |
| MISC17 | Role only editable via admin tools | CRITICAL | RLS prevents users from modifying their own role | MUST_BUILD | N/A -- no role column | Agent must add role column with RLS policy blocking self-modification |
| MISC18 | Default role is lowest privilege | CRITICAL | New users get 'user' role; enforced server-side on create | MUST_BUILD | N/A -- no role column | Agent must add `DEFAULT 'user'` constraint on role column |

---

### Category: Banned Patterns -- Rules BAN1-BAN43

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| BAN1 | No alert() | STANDARD | Use Toast instead | HANDLED | No alert() in codebase | None -- agent must never use alert() |
| BAN2 | No confirm() | STANDARD | Use ConfirmModal instead | HANDLED | No confirm() in codebase | None -- agent must never use confirm() |
| BAN3 | No prompt() | STANDARD | Use Modal with form instead | HANDLED | No prompt() in codebase | None -- agent must never use prompt() |
| BAN4 | No console.log for user feedback | POLISH | Use Toast for feedback | PARTIAL | `api.ts` line 29 has `console.log(res)` (debugging, not feedback). Edge functions use console.log for server logging | Agent must remove client-side console.log. Server-side logging is acceptable |
| BAN5 | No text-only empty states | POLISH | Use EmptyState with icon + CTA | MUST_BUILD | N/A -- no EmptyState component | Agent must create EmptyState and use it |
| BAN6 | No browser default dialogs | STANDARD | Replace all native dialogs with custom UI | HANDLED | Uses Radix Dialog and Sheet | None -- already implemented |
| BAN7 | No external state libraries | STANDARD | Use built-in state only | HANDLED | No Redux/Zustand/etc. | None -- already implemented |
| BAN8 | No containerization | STANDARD | No Docker files | HANDLED | No Docker files | None -- already implemented |
| BAN9 | No custom backend | STANDARD | BaaS/serverless only | HANDLED | Supabase Edge Functions (serverless) | None -- already implemented |
| BAN10 | No inline styles | STANDARD | Tailwind only | HANDLED | No inline styles | None -- already implemented |
| BAN11 | No `any` types | STANDARD | Define interfaces for all types | PARTIAL | One type cast in Pricing.tsx | Agent must avoid `any` and minimize type casts |
| BAN12 | No DB calls in components | STANDARD | Service layer only | PARTIAL | Pricing.tsx and AccountPage.tsx call Supabase directly | Agent must refactor |
| BAN13 | No unprotected auth routes | CRITICAL | Route guards on all auth routes | HANDLED | Account page checks auth server-side. Auth pages redirect authenticated users. **Functional with real sessions** | Agent must maintain pattern for new routes |
| BAN14 | No hardcoded theme colors | STANDARD | Use var(--color-*) references | HANDLED | All colors via CSS custom properties | None -- already implemented |
| BAN15 | No modifying locked dependencies | STANDARD | Versions locked | HANDLED | pnpm lockfile committed | None -- already implemented |
| BAN16 | No redundant sub-package entries | STANDARD | Clean package.json | HANDLED | Clean dependencies | None -- already implemented |
| BAN17 | No pinned AI SDK versions | POLISH | Let package manager resolve | N/A | No AI SDK | N/A |
| BAN18 | No edit-first pattern | STANDARD | Items open in read-only detail view first | MUST_BUILD | N/A -- no CRUD views | Agent must follow this pattern |
| BAN19 | No reusing Create form as Edit | STANDARD | Separate Create and Edit views | MUST_BUILD | N/A | Agent must create separate views |
| BAN20 | No view-only impossible | STANDARD | Users can view without editing | MUST_BUILD | N/A | Agent must implement read-only detail views |
| BAN21 | No combined view+edit component | STANDARD | Separate Detail and Edit components | MUST_BUILD | N/A | Agent must implement as separate components |
| BAN22 | No delete without confirmation | STANDARD | ConfirmModal required | MUST_BUILD | N/A | Agent must build ConfirmModal |
| BAN23 | No silent operations | POLISH | Toast on every mutation | PARTIAL | Auth and billing show toasts | Agent must maintain for all new mutations |
| BAN24 | No dead-end empty lists | POLISH | EmptyState with icon + CTA | MUST_BUILD | N/A | Agent must create EmptyState |
| BAN25 | No bare loading text | POLISH | Use Skeleton or spinner | PARTIAL | Pricing uses Skeleton | Agent must use Skeleton for all loading states |
| BAN26 | No raw timestamps | POLISH | Relative time formatting | MUST_BUILD | N/A | Agent must create formatDate utility |
| BAN27 | No untruncated long text | POLISH | truncate or line-clamp | MUST_BUILD | N/A | Agent must apply truncation |
| BAN28 | No missing back navigation | POLISH | Back button on detail/edit pages | MUST_BUILD | N/A | Agent must add to all sub-pages |
| BAN29 | No list key warnings | POLISH | Unique keys in lists | PARTIAL | Navbar uses array index as key | Agent must fix to use stable keys |
| BAN30 | No missing dependency warnings | POLISH | Complete useEffect deps | PARTIAL | AuthForm has incomplete deps | Agent should fix or document suppression |
| BAN31 | No unused variables | POLISH | Zero unused warnings | MUST_BUILD | Not verified | Agent must lint and fix |
| BAN32 | No type errors in production | CRITICAL | Zero TS errors | HANDLED | TypeScript configured | None -- agent must maintain |
| BAN33 | No writes without timestamps | CRITICAL | All DB writes include timestamps | PARTIAL | DB defaults provide `created`. No `updated_at` | Agent must add updated_at columns and triggers |
| BAN34 | No unscoped user data | CRITICAL | RLS on all user data tables | HANDLED | RLS enabled. **Enforced against real sessions** | None -- agent must maintain for new tables |
| BAN35 | No unvalidated form submissions | CRITICAL | Validate before submit | PARTIAL | Password match validated. No per-field inline validation | Agent must add inline validation to all forms |
| BAN36 | No buttons without loading state | POLISH | Spinner + disabled during async | PARTIAL | Buttons disabled during loading. No spinner icon | Agent must add spinner to loading buttons |
| BAN37 | No avatars without fallback | POLISH | Initials fallback on image error | PARTIAL | Avatar component with fallback exists but is unused. **OAuth now provides avatar_url** | Agent must use Avatar with initials fallback, especially with OAuth avatar data available |
| BAN38 | No pages without dynamic title | POLISH | usePageTitle hook on every page | PARTIAL | Static metadata in layout.tsx | Agent must add per-page metadata |
| BAN39 | No forms without autofocus | POLISH | Autofocus first input | MUST_BUILD | N/A | Agent must add autoFocus |
| BAN40 | No growable lists without search | POLISH | Search/filter for lists >5 items | MUST_BUILD | N/A | Agent must add to list views |
| BAN41 | No error dead ends | POLISH | Retry button on all errors | MUST_BUILD | N/A | Agent must add retry buttons |
| BAN42 | No mixed icon libraries | POLISH | Single icon library | PARTIAL | Lucide React (primary) + react-simple-icons (brand) + radix-icons | Agent should remove @radix-ui/react-icons if unused |
| BAN43 | No console errors in production | STANDARD | Zero console errors when deployed | MUST_BUILD | Not verified | Agent must test before deploy |

---

## PART 2: Industry Standards Supplement (Rules 200-270)

---

### IS Category 1: Internationalization (i18n) -- Rules 200-207

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 200 | Externalize all user-facing strings | STANDARD | All strings from translation resource file; no hardcoded text in components | MUST_BUILD | N/A -- all strings hardcoded in English in components | Agent must set up i18n library (e.g., `next-intl` or `react-i18next`), create `messages/en.json`, externalize all user-facing strings |
| 201 | Translation key naming convention | STANDARD | Dot-notation keys: `{page}.{section}.{element}` | MUST_BUILD | N/A | Agent must follow `dashboard.header.title` convention when creating translation keys |
| 202 | Locale-aware date formatting | STANDARD | Use Intl.DateTimeFormat; no hardcoded date format strings | MUST_BUILD | N/A -- no date formatting exists | Agent must use `Intl.DateTimeFormat` or date library with locale support in formatDate utility |
| 203 | Locale-aware number/currency formatting | STANDARD | Use Intl.NumberFormat; no hardcoded decimal separators or currency symbols | PARTIAL | `Pricing.tsx` hardcodes `$` symbol. Uses `unitAmount / 100` raw division | Agent must use `Intl.NumberFormat` for all price/number display instead of hardcoded `$` |
| 204 | RTL layout readiness | POLISH | CSS uses logical properties (margin-inline-start, not margin-left) | MUST_BUILD | N/A -- Tailwind uses physical properties (ml-, mr-, pl-, pr-) | Agent should use logical property equivalents (ms-, me-, ps-, pe-) in Tailwind v4 for RTL readiness |
| 205 | Pluralization handling | POLISH | ICU MessageFormat; no inline ternary for plurals | MUST_BUILD | N/A -- no pluralization utility | Agent must create pluralize utility using proper plural rules |
| 206 | Language detection and fallback chain | POLISH | Priority: user setting > browser preference > default. Missing keys fall back to default language | MUST_BUILD | N/A | Agent must implement if adding i18n support |
| 207 | Translation file completeness check | POLISH | CI step verifies all translation files have same keys | MUST_BUILD | N/A | Agent must add if multiple languages are supported |

---

### IS Category 2: Config Externalization -- Rules 208-214

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 208 | No hardcoded environment URLs | CRITICAL | All URLs from env vars; grep for http:// should only find env configs, tests, comments | HANDLED | `nextjs/utils/helpers.ts` uses `process.env.NEXT_PUBLIC_SITE_URL`. Supabase URL from `NEXT_PUBLIC_SUPABASE_URL`. **Auth callback URL uses `getURL()` for dynamic resolution** | None -- already implemented |
| 209 | Secrets never in source control | CRITICAL | No live secrets in repo; .env.example with placeholders; .gitignore blocks .env | HANDLED | `.env.example` has `YOUR_*` placeholders. `.gitignore` blocks `.env`. Stripe keys not needed (dormant). **Supabase anon key is public, not a secret** | None -- already implemented |
| 210 | Secrets never in client bundles | CRITICAL | No secret env vars in client-side code; only public identifiers | HANDLED | Client uses only `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (both public). Stripe secret key only in edge functions (Deno, server-side). Next.js `NEXT_PUBLIC_` prefix convention enforced | None -- already implemented |
| 211 | Configuration hierarchy | STANDARD | Config precedence: defaults < config files < env vars < runtime overrides; documented | PARTIAL | Uses env vars. `.env.example` documents variables. But no documentation of precedence hierarchy | Agent should document config hierarchy in README or CLAUDE.md |
| 212 | Feature flags as config | STANDARD | Feature toggles via env var `FEATURE_{NAME}_ENABLED=true\|false`; not code branches | MUST_BUILD | N/A -- no feature flag system | Agent must implement feature flags via env vars for any toggleable features |
| 213 | Build-time vs runtime config separation | STANDARD | Clear separation; no runtime decision depends on stale build-time value | HANDLED | Next.js handles this: `NEXT_PUBLIC_*` vars are baked into build, server env vars are runtime. Standard Next.js pattern | None -- already implemented by framework convention |
| 214 | Env var validation at startup | STANDARD | App validates all required env vars on startup; exits with clear error if missing | MUST_BUILD | N/A -- no startup validation. App will crash with cryptic error if env vars missing. `middleware.ts` has try/catch that silently swallows missing config | Agent must create `utils/config.ts` that validates all required env vars on app startup and provides clear error messages |

---

### IS Category 3: Environment Parity (Dev/Staging/Prod) -- Rules 215-220

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 215 | Same database technology across environments | CRITICAL | If prod uses PostgreSQL, dev uses PostgreSQL | HANDLED | Supabase local dev uses PostgreSQL (via `supabase start`). Production uses Supabase cloud (PostgreSQL). Same engine | None -- already implemented |
| 216 | Same auth flow in all environments | CRITICAL | No mock auth in dev; same provider/flow as prod | HANDLED | Supabase local dev includes Auth emulator with same API contract. **Same OAuth flow in dev and prod.** Email auth works against local Supabase | None -- **fully operational** |
| 217 | Config via env vars only, not code branches | STANDARD | No `if (environment === 'development')` in app logic | HANDLED | No environment checks in application code. Next.js handles env differences via build tooling | None -- already implemented |
| 218 | Seed data strategy for development | STANDARD | Reproducible seed script; single command; consistent test data | HANDLED | `supabase/seed.sql` exists. `pnpm supabase:reset` resets DB and runs seed | None -- already implemented. Agent must update seed.sql as new tables are added |
| 219 | Production data never in development | CRITICAL | No production data copies to dev; synthetic data only | HANDLED | Seed data is synthetic. No production data sync scripts | None -- already implemented |
| 220 | Reproducible dev environment setup | STANDARD | Single setup command for new developers | PARTIAL | `supabase start` + `pnpm install` + `pnpm dev` + configure OAuth providers. Documented in README. Not a single command but well-documented | Agent could create a `pnpm setup` script that chains all setup steps. Current multi-step documentation is acceptable |

---

### IS Category 4: Logging Strategy -- Rules 221-228

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 221 | Structured log format | STANDARD | JSON logs with timestamp, level, message, service. Not string concatenation | MUST_BUILD | N/A -- edge functions use `console.log()` with string messages | Agent must implement structured logging utility for edge functions |
| 222 | Log level usage guidelines | STANDARD | ERROR/WARN/INFO/DEBUG with consistent definitions | MUST_BUILD | N/A -- no log level system | Agent must define and document log levels |
| 223 | No raw console output in production | STANDARD | Server code uses structured logger, not console.log | PARTIAL | Edge functions use `console.log()`. Client-side `api.ts` has `console.log(res)` | Agent must replace with structured logger (server) and remove from client |
| 224 | Request correlation ID | STANDARD | UUID per request, propagated through logs and downstream calls | MUST_BUILD | N/A | Agent must add correlation ID middleware if building custom API routes |
| 225 | Sensitive data never logged | CRITICAL | No passwords, tokens, PII in logs; sanitization middleware | PARTIAL | Edge functions log event types but not sensitive data. No explicit sanitization | Agent must ensure no sensitive data is logged; add sanitization to logging utility |
| 226 | Logs to stdout/stderr | STANDARD | App writes to stdout/stderr; environment handles routing | HANDLED | Edge functions write to Deno stdout (Supabase captures). Next.js writes to stdout. Vercel handles log routing | None -- standard behavior for serverless |
| 227 | Client-side error reporting | STANDARD | Global error boundary catches uncaught exceptions; sends to error reporting endpoint | MUST_BUILD | N/A -- no error boundary, no error reporting. **PostHog dormant, so cannot use it for error reporting yet** | Agent must create error boundary + error reporting. Consider a lightweight reporting endpoint or store errors for when PostHog is activated |
| 228 | Log retention and size limits | POLISH | Log rotation or managed log service; no unbounded buffers | HANDLED | Supabase and Vercel manage log retention for edge functions and Next.js respectively | None -- managed by hosting platforms |

---

### IS Category 5: Dependency Management -- Rules 229-235

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 229 | Lockfile committed | CRITICAL | Lockfile in source control; CI uses `npm ci` equivalent | HANDLED | `nextjs/pnpm-lock.yaml` is committed. `pnpm install --frozen-lockfile` in CI | None -- already implemented |
| 230 | Dependencies explicitly declared | STANDARD | No reliance on global packages; all in package.json | HANDLED | All dependencies in `package.json`. System tools (Node, pnpm) listed in README | None -- already implemented |
| 231 | No floating version ranges | STANDARD | Production deps use exact or caret (^) versions; never * or latest | HANDLED | All deps use caret (^) ranges with lockfile pinning. `@stripe/stripe-js: 4.0.0` uses exact. `lucide-react: 0.562.0` uses exact | None -- already implemented |
| 232 | Dependency security audit in CI | CRITICAL | CI runs audit on every push; HIGH/CRITICAL fail the build | MUST_BUILD | N/A -- `.github/workflows/flutter-web.yml` exists but is for Flutter web, not Next.js. No CI for the Next.js app | Agent must create `.github/workflows/nextjs.yml` with `pnpm audit` step |
| 233 | Peer dependency conflicts resolved | STANDARD | Zero peer dependency warnings on install | HANDLED | `package.json` has pnpm overrides for `@types/react` and `@types/react-dom` to resolve conflicts | None -- already implemented |
| 234 | Dependency age monitoring | POLISH | Quarterly check for deps older than 18 months | MUST_BUILD | N/A -- no automated dependency age check | Agent could add `pnpm outdated` to CI as an informational step |
| 235 | Minimal dependency principle | POLISH | No dep for <20 lines of code; verify downloads, license, no duplicates | PARTIAL | Most deps are justified. `classnames` AND `clsx` both exist (duplicates -- both do the same thing). `tailwind-merge` exists alongside them | Agent should remove `classnames` since `clsx` and `tailwind-merge` (via `cn()`) cover the same need |

---

### IS Category 6: Legal/Compliance -- Rules 236-243

**NOTE: With auth active, users are creating accounts and storing personal data. Legal/compliance rules that were low-priority in Sheet 3 are now URGENT. See Urgency Flags section above.**

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 236 | Privacy policy page | CRITICAL | `/privacy` route with data collection, storage, sharing, retention, deletion info. Linked from signup and footer | MUST_BUILD | N/A -- no privacy policy page. **Collecting user email, name, avatar on signup without privacy policy. Legal liability.** | Agent must create `app/privacy/page.tsx` with comprehensive privacy policy. Link from Footer and signup flow. **URGENCY: HIGH** |
| 237 | Terms of service page | STANDARD | `/terms` route with acceptable use, termination, liability, jurisdiction. Checkbox on signup. Acceptance timestamp stored | MUST_BUILD | N/A -- no terms of service page. **Users creating accounts without accepting terms** | Agent must create `app/terms/page.tsx`. Add acceptance checkbox to AuthForm signup. Store acceptance timestamp in users table. **URGENCY: HIGH** |
| 238 | Cookie consent mechanism | CRITICAL | Consent banner before non-essential cookies. Accept/Reject buttons. Cookie preferences respected | MUST_BUILD | N/A -- **Supabase auth cookies are essential (may be exempt). PostHog dormant (no tracking cookies yet). Risk is MEDIUM now, becomes HIGH when PostHog activated** | Agent must build cookie consent banner. Essential auth cookies exempt. Prepare to gate PostHog when activated |
| 239 | Data export capability | STANDARD | User can export their personal data as JSON/CSV download | MUST_BUILD | N/A. **Users have profile data they cannot export** | Agent must build: button in account settings that generates downloadable JSON of all user data (profile, subscriptions) |
| 240 | Data deletion capability | CRITICAL | User can delete account and all data. Deletion within 30 days. Retain only legally required data | MUST_BUILD | N/A -- **no account deletion exists. Users can sign up but cannot delete their data. GDPR Article 17 violation** | Agent must build account deletion flow: typed confirmation > delete user data from all tables > delete auth user > sign out. **URGENCY: HIGH** |
| 241 | Consent tracking | STANDARD | `user_consents` table storing user_id, consent_type, document_version, timestamp, IP | MUST_BUILD | N/A. **No record of user consent during signup** | Agent must create `user_consents` table via migration and record consent on signup and cookie preferences |
| 242 | Third-party data sharing disclosure | STANDARD | Privacy policy lists every third party receiving data | MUST_BUILD | N/A -- **sharing data with Supabase (backend/auth) without disclosure. Stripe dormant. PostHog dormant** | Agent must include third-party disclosure section in privacy policy listing Supabase at minimum |
| 243 | Open-source license compliance | CRITICAL | All dependency licenses compatible with project license. License audit in CI. THIRD_PARTY_LICENSES file | PARTIAL | Project uses MIT license. All major deps (React, Next.js, Supabase, Tailwind) are MIT. No automated license audit or THIRD_PARTY_LICENSES file | Agent must: (1) Run `npx license-checker` to verify all licenses, (2) Add license audit to CI, (3) Generate THIRD_PARTY_LICENSES file |

---

### IS Category 7: Deep Accessibility (WCAG AA) -- Rules 244-253

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 244 | Color contrast ratios | CRITICAL | Normal text: 4.5:1 minimum. Large text: 3:1. UI components: 3:1 | PARTIAL | Color tokens defined with oklch values. Brand colors (orange tones) likely meet contrast but not verified. `muted-foreground` on dark bg may be borderline | Agent must run contrast audit on all color token combinations and fix any failures |
| 245 | Semantic HTML structure | STANDARD | h1-h6 hierarchical, nav, main, button (not div onClick), a href (not span onClick) | PARTIAL | `layout.tsx` has `<main>`. `Navbar.tsx` uses proper `<nav>`. `<button>` used for buttons. Landing page uses `<h2>`. But no `<h1>` on many pages, no `<header>`/`<footer>` landmarks | Agent must add proper heading hierarchy and landmark elements to all pages |
| 246 | Skip navigation link | STANDARD | "Skip to main content" as first focusable element; visible on focus | PARTIAL | `layout.tsx` has `<main id="skip">` target. But no skip link exists that links to `#skip` | Agent must add `<a href="#skip" className="sr-only focus:not-sr-only ...">Skip to main content</a>` before Navbar in layout |
| 247 | Reduced motion support | STANDARD | Animations check `prefers-reduced-motion: reduce`; disable or reduce to opacity fade | PARTIAL | `tw-animate-css` may respect reduced motion. Custom CSS animations in `main.css` do NOT check `prefers-reduced-motion` | Agent must add `@media (prefers-reduced-motion: reduce)` overrides in `main.css` to disable/reduce animations |
| 248 | Color scheme preference support | POLISH | Default to OS preference; explicit user choice overrides and persists | HANDLED | `layout.tsx` ThemeProvider has `defaultTheme="system"` and `enableSystem`. User choice persisted via localStorage by next-themes | None -- already implemented |
| 249 | ARIA live regions for dynamic content | STANDARD | Toast uses aria-live. Form errors announced. Search results updates announced | PARTIAL | Radix Toast has built-in aria-live. Other dynamic content (form errors, loading states) lacks aria-live | Agent must add `aria-live="polite"` regions for form validation errors and dynamic content updates |
| 250 | Touch target minimum size | STANDARD | All interactive elements 44x44px minimum; 8px spacing between adjacent targets | PARTIAL | Most buttons meet 44px via padding. Small icon buttons (theme toggle, hamburger) may be under 44px | Agent must audit and add padding to achieve 44px minimum |
| 251 | Image alt text policy | STANDARD | Non-decorative images have descriptive alt. Decorative images have alt="" | PARTIAL | Logo SVG inline (no alt needed). OG image route exists. No `<img>` tags with missing alt found | Agent must ensure all new images have proper alt text |
| 252 | Form error association | STANDARD | Errors linked via aria-describedby; input marked aria-invalid="true"; focus moves to first error | MUST_BUILD | N/A -- errors shown via toast only, not linked to fields | Agent must add `aria-describedby` linking errors to inputs, `aria-invalid="true"` on errored fields, focus first error on submit |
| 253 | Focus visible indicator | STANDARD | No `outline: none` without alternative; focus indicator 3:1 contrast; use `:focus-visible` | HANDLED | Tailwind v4 and Radix components use `focus-visible` ring styles. No `outline: none` without replacement | None -- already implemented |

---

### IS Category 8: API Versioning -- Rules 254-258

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 254 | API version identifier | STANDARD | All routes include version prefix `/api/v1/` or version header | N/A | Next.js API routes (`/api/auth_callback`, `/api/og`, `/api/reset_password`) are internal. Supabase Edge Functions are internal. No public API | N/A for internal APIs. If agent builds a public API, must version it |
| 255 | Deprecation notice period | STANDARD | Deprecated endpoints remain functional for 90 days with headers | N/A | No public API | N/A unless public API is built |
| 256 | Backward compatibility for minor changes | STANDARD | New response fields are non-breaking; removing/renaming fields are breaking | N/A | No public API | N/A unless public API is built |
| 257 | Breaking change documentation | POLISH | Migration guide for breaking API changes in CHANGELOG.md | N/A | No public API | N/A unless public API is built |
| 258 | API response envelope consistency | STANDARD | Consistent response structure across all endpoints | PARTIAL | Edge functions return `{ redirect_url }`. Auth callback returns redirects. No consistent envelope | If agent builds API routes, must use consistent envelope: `{ data, error }` |

---

### IS Category 9: Architecture Decision Records (ADRs) -- Rules 259-263

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 259 | ADR template exists | STANDARD | `docs/adr/template.md` with Status, Context, Decision, Consequences sections | MUST_BUILD | N/A -- no ADR system | Agent must create `docs/adr/template.md` and `docs/adr/README.md` |
| 260 | ADR trigger threshold | POLISH | ADR required for new deps, 5+ file changes across 2+ dirs, new patterns, disagreements | MUST_BUILD | N/A | Agent should document the ADR threshold in the ADR README |
| 261 | ADR numbering and storage | POLISH | `docs/adr/NNNN-short-title.md`, zero-padded sequential numbers, index file | MUST_BUILD | N/A | Agent must follow this convention when creating ADRs |
| 262 | Superseded ADRs link forward | POLISH | Old ADR status changed to "Superseded by [NNNN]" with link | MUST_BUILD | N/A | Agent must follow this convention |
| 263 | ADRs part of onboarding | POLISH | Onboarding docs include step to read ADRs; ADRs written in plain language | MUST_BUILD | N/A | Agent should add ADR reading step to README |

---

### IS Category 10: Error Recovery / Retry Strategy -- Rules 264-270

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 264 | Transient failure detection | STANDARD | Classify 502/503/504/429 as transient (retry); 400/401/403/404/422 as permanent (no retry) | PARTIAL | Edge functions have try/catch. Auth API calls handle errors. But no systematic classification | Agent must create an HTTP client utility that classifies errors as transient vs permanent |
| 265 | Exponential backoff with jitter | STANDARD | `min(base_delay * 2^attempt + jitter, max_delay)` in shared retry utility | MUST_BUILD | N/A | Agent must create a shared retry utility with exponential backoff + jitter |
| 266 | Maximum retry count | CRITICAL | No operation retries more than 5 times; clear error after max retries | MUST_BUILD | N/A -- no retry logic in the codebase | Agent must implement max retry with clear user-facing error message |
| 267 | Circuit breaker for external services | POLISH | After N consecutive failures, stop sending requests; cooldown; half-open test | MUST_BUILD | N/A | Agent should implement for external API calls if reliability is a concern |
| 268 | Graceful degradation | STANDARD | Critical vs non-critical service classification; non-critical shows fallback, not crash | PARTIAL | If Stripe call fails, error shows in UI (not crash). Auth failure redirects cleanly. But no formal classification. **Stripe is dormant so degradation is naturally present** | Agent should classify services and implement fallback states |
| 269 | Retry state visible to user | STANDARD | UI shows "Retrying..." during retries; "Try again" button after max retries | MUST_BUILD | N/A | Agent must show retry state to users during transient failures |
| 270 | Idempotency for retried operations | CRITICAL | Write operations safe to execute multiple times; idempotency keys for payments | PARTIAL | Supabase handles upsert-style operations. Auth operations are inherently idempotent (sign in again = same session). No explicit idempotency keys for other writes | Agent must add idempotency keys for any write operations that might be retried. **Stripe dormant, so payment idempotency not yet needed** |

---

## PART 3: Mechanism Categories (A-N) Status

| ID | Category | Status | Rationale |
|----|----------|--------|-----------|
| A | Data Input | MUST_BUILD | Forms exist for auth only (AuthForm). App-specific input patterns (CRUD forms, file upload, etc.) must be built |
| B | Data Storage | HANDLED | Supabase PostgreSQL configured with tables, RLS, migrations, seed data. **Active and serving real queries** |
| C | Data Processing | MUST_BUILD | App-specific processing logic must be built. No validation, calculation, or transformation utilities |
| D | Data Output | PARTIAL | Landing page sections (Hero, Pricing, FAQ, Stats). Account page displays user info. No list views, detail views, charts, or dashboards |
| E | Authentication | HANDLED | **Fully operational.** Email/password + Google/GitHub OAuth + email verification + password reset + session management. Was PRESENT_NOT_WIRED in Sheet 3 |
| F | Authorization | PARTIAL | RLS policies on all tables enforced with real user sessions. But no role column, no role-based route guards, no feature gating by subscription tier. **Stripe dormant so no subscription-based gating** |
| G | Communication | PARTIAL | **Supabase sends auth emails automatically** (verification, password reset). Loops.so referenced in edge functions but not integrated in Next.js. No custom notifications, no in-app notifications |
| H | Integration | PARTIAL | **Supabase fully connected.** Stripe code present but dormant (no keys). PostHog code present but dormant (no keys). Was PRESENT_NOT_WIRED in Sheet 3 for Stripe/PostHog |
| I | Workflow | MUST_BUILD | No workflow engine, state machines, or automation. DB trigger for user profile creation is the only automated workflow, and it is **now actively firing** |
| J | Search & Discovery | MUST_BUILD | No search, no filtering, no autocomplete. Postgres full-text search available but not configured |
| K | Collaboration | MUST_BUILD | No collaboration features |
| L | Monetization | PRESENT_NOT_WIRED | Stripe code present (checkout, webhook sync, subscription tracking, billing portal) but **dormant -- no Stripe keys configured**. `handleBillingPortal()` in AccountPage will error |
| M | Admin/Ops | MUST_BUILD | No admin panel, no user management, no content moderation |
| N | Infrastructure | PARTIAL | Supabase (DB + Auth + Edge Functions + Realtime) active. Stripe dormant. PostHog dormant. Vercel hosting configured. No CI for Next.js app |

---

## SUMMARY: HANDLED -- Do Not Touch

These rules are already implemented by the boilerplate. The agent should NOT modify or rebuild them.

**Stack**: S1, S2, S3, S4, S5, S6, S7, S8, S10
**File Structure**: FS1, FS2, FS3, FS11
**Configuration**: CM1, CM2, CM3, CM5, CM6, CM7, CM8, CM9
**Auth Context**: AC2, AC3, AC5, AC6, AC7
**Theme Context**: TC1, TC2, TC3, TC4
**Route Guards**: RG1
**Data Structure**: DS1, DS2, DS4
**Routing Structure**: RS1, RS2
**Data/API Patterns**: DAP6
**Authentication/Security**: AS4
**Database/Storage**: DBS1
**Error Handling**: EH3
**Deployment/Hosting**: DH1, DH4, DH5
**Build Instructions**: BI1, BI4, BI25, BI26, BI30
**Miscellaneous**: MISC2, MISC3, MISC6, MISC9, MISC10, MISC14, MISC16
**Banned Patterns**: BAN1, BAN2, BAN3, BAN6, BAN7, BAN8, BAN9, BAN10, BAN13, BAN14, BAN15, BAN16, BAN34
**Industry Standards**: 208, 209, 210, 213, 215, 216, 217, 218, 219, 226, 228, 229, 230, 231, 233, 248, 253
**Mechanism Categories**: B, E

**Total HANDLED: ~78 rules**

---

## SUMMARY: MUST_BUILD -- Agent Checklist

These rules have NO implementation in the boilerplate. The agent must build them from scratch.

| # | Rule | One-Line Action |
|---|------|----------------|
| AC1 | UserProfile with role | Add `role` column to users table via migration with `DEFAULT 'user'` and RLS preventing self-modification |
| AC4 | Default role is 'user' | Same migration as AC1 -- enforce via DB constraint |
| RG2 | AdminRoute | Create admin route guard checking `role === 'admin'` |
| RG3 | ProRoute | Create pro/admin route guard checking `role IN ('pro', 'admin')` |
| RS3 | 404 catch-all | Create `app/not-found.tsx` with styled "Page Not Found" and link home |
| RS4 | CRUD route pattern | Create `app/{entity}/`, `app/{entity}/new/`, `app/{entity}/[id]/`, `app/{entity}/[id]/edit/` for each entity |
| DAP1 | Delete account removes data | Build cascading delete function covering all user-owned tables |
| DAP2 | Explicit data category list | Maintain hardcoded list of tables for deletion |
| DAP4 | CRUD helper layer | Create generic CRUD service with auto-timestamps |
| DAP7 | List pagination | Choose one pagination strategy and implement consistently |
| DAP8 | Pagination controls | Build reusable Pagination component |
| DAP9 | Load-more remaining count | Build if choosing load-more strategy |
| DSL2 | CRUD helpers | Create `createRecord`, `updateRecord`, `deleteRecord`, `getRecords` in services/ |
| DSL4 | Delete account function | Build edge function or server action for complete account deletion. **URGENCY: HIGH** |
| AS1 | Delete with typed confirmation | Build ConfirmModal with text input disabled until "DELETE" typed. **URGENCY: HIGH** |
| AS2 | Delete button disabled during op | Add double-check: confirmation text match AND isDeleting state |
| AS3 | Logout after deletion | Call signOut() after successful deletion |
| AS6 | Admin-only nav conditional | Conditionally render admin links based on role |
| DBS2 | Delete cascades all data | Build ordered deletion across all user-data tables. **URGENCY: HIGH** |
| DBS3 | Batch deletes | Use Supabase `.delete().eq('user_id', uid)` per table |
| EH1 | Delete failure keeps modal | On error: toast, reset loading, keep modal open |
| EH4 | Delete flow 6-step | Implement full delete workflow |
| P4 | One pagination strategy | Choose and document before building lists |
| UX3 | EmptyState component | Create EmptyState with icon + message + CTA button |
| UX5 | List-Detail-Create-Edit | Implement 4-view CRUD pattern for every data entity |
| UX6 | No edit-first | Items open read-only; Edit is separate route |
| UX7 | Delete confirmation | Use ConfirmModal for all deletes |
| UX11 | Date formatting utility | Create `utils/formatDate.ts` with relative time strings |
| UX12 | Text truncation | Apply truncate/line-clamp to all overflowable text |
| UX13 | Back navigation | Add back button to all detail/edit pages |
| UX23 | 404 route | Create `app/not-found.tsx` |
| BI3 | Build app features | Implement app-specific features with CRUD pattern |
| BI9 | Autofocus on forms | Add autoFocus to first input in all forms |
| BI10 | Pluralization helper | Create `utils/pluralize.ts` |
| BI11 | Search/filter for lists | Add search input to list views >5 items |
| BI12 | Retry on error states | Add "Try Again" button to all error displays |
| BI13 | Network/offline handling | Monitor `navigator.onLine`; show offline banner |
| BI18 | Unsaved changes warning | Create `useUnsavedChanges` hook with beforeunload + router guard |
| BI19 | 404 / not-found handling | Create not-found page + EmptyState for missing data |
| DH3 | Error boundary | Create `app/error.tsx` and `app/global-error.tsx` |
| MISC7 | Detail separate from edit | Implement as separate routes/components |
| MISC17 | Role only via admin tools | RLS policy blocking self-role-modification |
| MISC18 | Default role lowest privilege | `DEFAULT 'user'` column constraint |
| 200 | Externalize strings | Set up i18n library, create translation files |
| 201 | Translation key convention | Use `{page}.{section}.{element}` dot-notation |
| 202 | Locale-aware dates | Use Intl.DateTimeFormat in formatDate utility |
| 204 | RTL layout readiness | Use Tailwind logical properties (ms-, me-, ps-, pe-) |
| 205 | Pluralization handling | ICU MessageFormat or equivalent in pluralize utility |
| 206 | Language detection | Implement if adding multi-language support |
| 207 | Translation completeness | CI check if multiple languages |
| 212 | Feature flags | Implement `FEATURE_{NAME}_ENABLED` env var pattern |
| 214 | Env var validation at startup | Create config validation module that checks all required vars |
| 221 | Structured logging | Create structured JSON logger for edge functions |
| 222 | Log level guidelines | Define and document ERROR/WARN/INFO/DEBUG usage |
| 224 | Request correlation ID | Add UUID correlation ID middleware to API routes |
| 227 | Client error reporting | Create error boundary + reporting endpoint |
| 232 | Dependency audit in CI | Add `pnpm audit` to GitHub Actions workflow |
| 234 | Dependency age monitoring | Add `pnpm outdated` informational CI step |
| 236 | Privacy policy page | **URGENCY: HIGH** -- Create `/privacy` route. Required for GDPR with user accounts |
| 237 | Terms of service page | **URGENCY: HIGH** -- Create `/terms` route with acceptance tracking |
| 238 | Cookie consent | Build consent banner. Essential cookies exempt; prepare for PostHog |
| 239 | Data export | Build user data export as JSON download |
| 240 | Data deletion | **URGENCY: HIGH** -- Build complete account deletion flow |
| 241 | Consent tracking | Create `user_consents` table and record all consent events |
| 242 | Third-party data disclosure | Document Supabase in privacy policy (Stripe/PostHog dormant) |
| 243 | License compliance | Run license audit, create THIRD_PARTY_LICENSES file |
| 246 | Skip navigation link | Add "Skip to main content" link before Navbar |
| 252 | Form error association | Link errors to inputs via aria-describedby + aria-invalid |
| 259 | ADR template | Create `docs/adr/template.md` |
| 260-263 | ADR system | Set up full ADR numbering, storage, and onboarding docs |
| 265 | Exponential backoff | Create shared retry utility with backoff + jitter |
| 266 | Maximum retry count | Cap retries at 5 with clear error message |
| 267 | Circuit breaker | Implement for external API calls |
| 269 | Retry state visible | Show "Retrying..." UI during transient failures |

**Total MUST_BUILD: ~76 rules**

---

## SUMMARY: Delta from Sheet 3

### Rules that CHANGED status (Sheet 3 -> Sheet 4)

| # | Rule | Sheet 3 Status | Sheet 4 Status | What Changed |
|---|------|---------------|---------------|-------------|
| S3 | Authentication provider | PRESENT_NOT_WIRED | **HANDLED** | Supabase Auth fully operational. Email/password + OAuth working. Auth callback processes redirects |
| AC2 | Auth context provides full interface | PRESENT_NOT_WIRED | **HANDLED** | `api.ts` provides complete auth API. Server/client auth methods functional |
| AC3 | Profile created on first login | PRESENT_NOT_WIRED | **HANDLED** | `handle_new_user()` trigger now actively fires on real signups |
| AC6 | Popup/redirect sign-in flow | PRESENT_NOT_WIRED | **HANDLED** | `oauthSignin()` uses redirect flow with real OAuth providers |
| AC7 | Loading state during auth check | PRESENT_NOT_WIRED | **HANDLED** | Server components resolve auth before rendering. Loading state during form submissions |
| RG1 | ProtectedRoute for auth users | PRESENT_NOT_WIRED | **HANDLED** | Account page server-side auth check redirects unauthenticated users |
| RS2 | Public vs protected routes | PRESENT_NOT_WIRED | **HANDLED** | Clear public/protected separation enforced with real sessions |
| AS4 | Protected routes wrap layout | PRESENT_NOT_WIRED | **HANDLED** | Auth check pattern works with real sessions |
| MISC2 | No unprotected auth routes | PRESENT_NOT_WIRED | **HANDLED** | Route guards functional with real auth |
| BAN13 | No unprotected auth routes | PRESENT_NOT_WIRED | **HANDLED** | Auth routes protected with real session checks |
| 216 | Same auth flow in all environments | PRESENT_NOT_WIRED | **HANDLED** | Same OAuth/email flow in local dev and production |
| Mechanism E | Authentication | PRESENT_NOT_WIRED | **HANDLED** | Full auth flow active |
| Mechanism G | Communication | NOT_PRESENT | **PARTIAL** | Supabase sends auth emails (verification, password reset) |
| Mechanism L | Monetization | PRESENT_NOT_WIRED | PRESENT_NOT_WIRED | No change -- Stripe still dormant |

---

## SUMMARY: Statistics

| Status | Count | Percentage |
|--------|-------|-----------|
| HANDLED | ~78 | ~30% |
| PARTIAL | ~46 | ~18% |
| MUST_BUILD | ~76 | ~29% |
| N/A | ~8 | ~3% |
| Banned (HANDLED) | ~15 | ~6% |
| Banned (PARTIAL) | ~10 | ~4% |
| Banned (MUST_BUILD) | ~30 | ~11% |

### Delta from Sheet 3

| Metric | Sheet 3 | Sheet 4 | Delta |
|--------|---------|---------|-------|
| HANDLED | ~51 | ~78 | **+27** |
| PRESENT_NOT_WIRED | ~32 | ~20 | **-12** |
| PARTIAL | ~25 | ~46 | **+21** |
| MUST_BUILD/NOT_PRESENT | ~61 | ~76 | **+15** (reclassified from PRESENT_NOT_WIRED) |
| N/A | ~7 | ~8 | +1 |

Auth activation flips ~12 rules from PRESENT_NOT_WIRED to HANDLED and reclassifies several rules into more precise statuses (Sheet 5 format uses finer granularity than Sheet 3's delta format).

### Critical Items Still Missing (MUST FIX Before Accepting Real Users)

1. **Privacy policy page (#236)** -- Collecting user data without privacy policy. GDPR/CCPA violation
2. **Data deletion capability (#240)** -- GDPR Article 17 right to erasure. Users have data and cannot delete accounts
3. **Terms of service page (#237)** -- No legal agreement between user and service
4. **Error boundary (#DH3 / #BI6)** -- Unhandled errors show blank white screen
5. **Role system (#AC1, AC4, MISC17, MISC18)** -- No role column, no role-based access, no admin/pro guards
6. **Account deletion flow (#DSL4, AS1-AS3, DBS2)** -- No way to delete an account
7. **Env var validation (#214)** -- App crashes with cryptic errors if env vars missing
8. **Maximum retry count (#266)** -- No retry logic; operations either succeed or fail silently
9. **Dependency security audit in CI (#232)** -- No CI for the Next.js app at all
10. **Open-source license compliance (#243)** -- No THIRD_PARTY_LICENSES file or audit
11. **Form validation (#MISC8, BAN35)** -- Auth forms validate passwords but no per-field inline validation
12. **Cookie consent (#238)** -- Auth cookies may be exempt, but needs mechanism for when PostHog is activated

---

## What an Agent Needs to Know

1. **Auth is fully live** -- users can sign up, sign in, sign out, reset passwords, verify emails. OAuth (Google, GitHub) requires provider configuration in Supabase Dashboard
2. **The boilerplate is a LANDING PAGE with auth** -- it is NOT an app. There are no CRUD features, no dashboard, no admin panel, no sidebar layout. The agent builds the actual application on top of this foundation
3. **User profiles auto-create** -- the `handle_new_user()` trigger creates a `users` row on every signup with `full_name` and `avatar_url` from OAuth metadata
4. **No role system** -- all users are equal. No admin, no pro, no tiers. Must add `role` column if needed
5. **No account deletion** -- users can sign up but cannot delete their accounts. **This is a legal liability with auth ON**
6. **Legal compliance is the BIGGEST gap** -- privacy policy, terms, cookie consent, data deletion are ALL missing. These become urgent the moment users start creating accounts
7. **Stripe is still OFF** -- `handleBillingPortal()` in AccountPage will error. The Pricing component will render but checkout won't work. No Stripe keys configured
8. **PostHog is still OFF** -- no tracking, no analytics, no error reporting. Code is present and will activate when keys are set
9. **Middleware refreshes sessions** -- every request through Next.js middleware refreshes the Supabase auth session. This is actively running
10. **Server components check auth** -- pages like Account call `supabase.auth.getUser()` and redirect if not authenticated. This pattern is functional and proven
11. **The "service layer" is `utils/supabase/queries.ts`** -- it is minimal (4 functions). Components like Pricing.tsx bypass it and call Supabase directly. Agent must enforce service layer discipline
12. **Next.js App Router conventions** -- this boilerplate uses the App Router (not Pages Router). Routes are folders in `app/`. Server Components are default. Client Components need `'use client'` directive. Middleware in `middleware.ts` at project root
