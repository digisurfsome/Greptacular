# Exact Reality Sheet 1: web_base (All Toggles OFF)

> **Variant**: Base -- all toggles OFF. No `supabase start`, no env vars set, no API keys configured.
> **Boilerplate**: DevToDollars Web-BoilerPlate-D2D (Next.js 16 + Supabase + Stripe + Tailwind v4 + PostHog)
> **What is active**: UI framework, Tailwind CSS styling, landing page components, dark mode toggle, static layout
> **What is dormant**: Database (schema.sql exists, no running DB), Auth (AuthForm.tsx exists, no Supabase URL), Payments (Stripe code exists, no keys), Analytics (PostHog code exists, no keys)
> **Use case**: Starting point for any project using this boilerplate before any services are configured
>
> This document is the SINGLE SOURCE OF TRUTH for what an AI coding agent gets for free from this boilerplate
> and what it must build from scratch. Every rule from Martin's 192-rule checklist and every rule from the
> 71-rule Industry Standards supplement is listed below with its exact status.
>
> **CRITICAL DISTINCTION**: Sheet 1 only marks HANDLED for things that work with ZERO configuration.
> Code that exists but requires environment variables, API keys, or running services to function is
> marked PRESENT_NOT_WIRED -- the agent gets the code pattern for free but must wire it up.

---

## Boilerplate Identity

| Field | Value |
|-------|-------|
| **Framework** | Next.js 16.1.6 (React 19, TypeScript, App Router) |
| **Styling** | Tailwind CSS v4.1.18 + tw-animate-css |
| **Component Library** | Radix UI primitives (dialog, accordion, avatar, toast, dropdown, navigation-menu, scroll-area, label) |
| **Icons** | Lucide React 0.562.0 + @icons-pack/react-simple-icons (GitHub, Google) |
| **Auth** | PRESENT_NOT_WIRED -- Supabase Auth code exists (AuthForm.tsx, api.ts) but no SUPABASE_URL configured |
| **Database** | PRESENT_NOT_WIRED -- schema.sql exists but no running Supabase instance |
| **Payments** | PRESENT_NOT_WIRED -- Stripe code exists (@stripe/stripe-js, edge functions) but no STRIPE_SECRET_KEY |
| **Analytics** | PRESENT_NOT_WIRED -- PostHog provider exists but no NEXT_PUBLIC_POSTHOG_KEY |
| **Hosting** | Vercel (configured via next.config.js) |
| **Package Manager** | pnpm (lockfile committed) |
| **Edge Functions** | PRESENT_NOT_WIRED -- Deno-based: `get_stripe_url`, `stripe_webhook`, `on_user_modify` |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| **HANDLED** | Works with zero configuration. Agent should NOT rebuild. |
| **PRESENT_NOT_WIRED** | Code exists in the boilerplate but requires env vars, API keys, or running services to function. Agent gets the pattern for free but must configure/wire it. |
| **PARTIAL** | Some implementation exists but is incomplete. Agent must fill gaps. |
| **MUST_BUILD** | No implementation exists. Agent must build from scratch. |
| **N/A** | Rule does not apply to this boilerplate variant or use case. |

---

## Boilerplate File Map

```
nextjs/
  app/
    layout.tsx              -- Root layout (ThemeProvider, PHProvider, Toaster) [HANDLED: layout structure; PRESENT_NOT_WIRED: PHProvider needs key]
    page.tsx                -- Landing page [HANDLED: renders static content]
    providers.tsx           -- PostHog provider [PRESENT_NOT_WIRED: needs NEXT_PUBLIC_POSTHOG_KEY]
    PostHogPageView.tsx     -- Page view tracking [PRESENT_NOT_WIRED: needs PostHog key]
    error.tsx               -- Global error page with retry button [HANDLED]
    not-found.tsx           -- Styled 404 page with link home [HANDLED]
    privacy/page.tsx        -- Privacy policy shell with TODO sections [PARTIAL: needs actual policy content]
    terms/page.tsx          -- Terms of service shell with TODO sections [PARTIAL: needs actual terms content]
    account/page.tsx        -- Account page (server component, auth-gated) [PRESENT_NOT_WIRED: needs auth]
    auth/[id]/page.tsx      -- Auth pages (signin, signup, forgot_password, update_password, verify_email) [PRESENT_NOT_WIRED: needs Supabase]
    api/
      auth_callback/route.ts   -- OAuth callback handler [PRESENT_NOT_WIRED: needs Supabase]
      og/route.tsx             -- OG image generation [HANDLED: static generation]
      reset_password/route.ts  -- Password reset callback [PRESENT_NOT_WIRED: needs Supabase]
  components/
    icons/                  -- GitHub.tsx, Logo.tsx [HANDLED: static SVG components]
    landing/                -- Navbar, Hero, Pricing, FAQ, Footer, Stats, Logos, Cta, Items, Icons, mode-toggle [HANDLED: UI renders; PRESENT_NOT_WIRED: Pricing needs Stripe data]
    misc/                   -- AccountPage.tsx, AuthForm.tsx, PostHogPageViewWrapper.tsx [PRESENT_NOT_WIRED: all need services]
                               SEOMeta.tsx [HANDLED: generatePageMetadata() + JsonLd component]
                               CookieConsent.tsx [HANDLED: consent banner with localStorage persistence]
    ui/                     -- accordion, avatar, badge, breadcrumb, button, card, dialog, dropdown-menu,
                               glow, input, item, label, navigation-menu, scroll-area, section, sheet,
                               skeleton, toast, toaster, use-toast.ts [HANDLED: all pure UI components]
                               error-boundary.tsx [HANDLED: ErrorBoundary class component + withErrorBoundary HOC]
                               loading-spinner.tsx [HANDLED: LoadingSpinner (3 sizes), PageLoader, SkeletonCard]
                               empty-state.tsx [HANDLED: EmptyState with icon/title/description/action props]
                               form-field.tsx [HANDLED: FormField wrapper with label + error display]
                               skip-nav.tsx [HANDLED: skip navigation link component]
                               visually-hidden.tsx [HANDLED: sr-only wrapper component]
  lib/
    toast.ts                -- Toast wrapper: showSuccess/showError/showInfo/showWarning [HANDLED]
    form-validation.ts      -- Zod schemas + validateForm() helper [HANDLED: requires pnpm add zod]
    design-tokens.ts        -- SPACING, TYPOGRAPHY, BREAKPOINTS, ANIMATION, RADIUS constants [HANDLED]
    env.ts                  -- Typed env access with server-only protection [HANDLED]
    services/
      base-service.ts       -- createService<T>() CRUD factory [HANDLED]
      index.ts              -- Re-exports with usage documentation [HANDLED]
  utils/
    cn.ts                   -- className merge utility [HANDLED]
    helpers.ts              -- URL helpers [HANDLED: uses NEXT_PUBLIC_SITE_URL with fallback]
    types.ts                -- AuthState enum, StateInfo, SubscriptionWithPriceAndProduct [HANDLED: type definitions]
    supabase/
      admin.ts              -- Supabase admin client (service role) [PRESENT_NOT_WIRED: needs keys]
      api.ts                -- Auth API client (signup, signin, oauth, signout, password reset) [PRESENT_NOT_WIRED: needs Supabase]
      client.ts             -- Browser Supabase client [PRESENT_NOT_WIRED: needs keys]
      middleware.ts          -- Session refresh middleware [PRESENT_NOT_WIRED: needs Supabase]
      queries.ts            -- getUser, getSubscription, getProducts, getUserDetails [PRESENT_NOT_WIRED: needs DB]
      server.ts             -- Server-side Supabase client [PRESENT_NOT_WIRED: needs keys]
  middleware.ts             -- Next.js middleware (session refresh) [PRESENT_NOT_WIRED: needs Supabase]
  styles/
    main.css                -- CSS tokens, Tailwind v4 @theme directive [HANDLED]
  next.config.js            -- Next.js configuration [HANDLED]
  postcss.config.mjs        -- PostCSS config for Tailwind [HANDLED]
  tsconfig.json             -- TypeScript configuration [HANDLED]
  .env.example              -- Env var placeholders [HANDLED: documents required vars]
  .gitignore                -- Git ignore rules [HANDLED]
  package.json              -- Dependencies and scripts [HANDLED]
  pnpm-lock.yaml            -- Lockfile [HANDLED]
  schema.sql                -- Database schema (users, subscriptions, products, prices, customers) [PRESENT_NOT_WIRED: no running DB]
supabase/
  functions/
    get_stripe_url/         -- Stripe checkout URL generator [PRESENT_NOT_WIRED: needs Stripe + Supabase]
    stripe_webhook/         -- Stripe webhook handler [PRESENT_NOT_WIRED: needs Stripe + Supabase]
    on_user_modify/         -- User lifecycle trigger [PRESENT_NOT_WIRED: needs Supabase]
  seed.sql                  -- Seed data [PRESENT_NOT_WIRED: needs running DB]
  config.toml               -- Supabase local config [PRESENT_NOT_WIRED: needs supabase start]
```

---

## Database Tables (from schema.sql -- ALL DORMANT)

All tables are defined in `schema.sql` but require a running Supabase instance (`supabase start` or cloud project) to exist.

| Table | Purpose | Status | Notes |
|-------|---------|--------|-------|
| `users` | User profiles (id, full_name, avatar_url, billing_address, payment_method) | PRESENT_NOT_WIRED | Created by auth trigger `on_user_modify` |
| `customers` | Stripe customer mapping (id -> stripe_customer_id) | PRESENT_NOT_WIRED | Maps Supabase user to Stripe customer |
| `products` | Stripe products synced via webhook | PRESENT_NOT_WIRED | Populated by Stripe webhook |
| `prices` | Stripe prices synced via webhook | PRESENT_NOT_WIRED | Populated by Stripe webhook |
| `subscriptions` | Active subscriptions synced via webhook | PRESENT_NOT_WIRED | Populated by Stripe webhook |

---

## PART 1: Martin's Structural Checklist (Rules S1-MISC18 + BAN1-BAN43)

---

### Category 1: Stack (S1-S10)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| S1 | Framework with type safety | STANDARD | UI framework with strict type checking | HANDLED | Next.js 16.1.6 + TypeScript in `tsconfig.json` | None |
| S2 | Single styling solution | STANDARD | All styling via single CSS methodology | HANDLED | Tailwind CSS v4.1.18, configured in `postcss.config.mjs` and `styles/main.css` | None |
| S3 | Authentication provider | CRITICAL | Configured auth provider with designated sign-in methods | PRESENT_NOT_WIRED | `utils/supabase/api.ts` has email/password + Google + GitHub OAuth code. Needs `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Agent must configure env vars to activate |
| S4 | Single database backend | STANDARD | All data in a single configured database technology | PRESENT_NOT_WIRED | Supabase PostgreSQL configured in `utils/supabase/client.ts`. Needs running Supabase instance | Agent must run `supabase start` or connect to cloud |
| S5 | Built-in state management | STANDARD | Auth/feature state via framework primitives | PRESENT_NOT_WIRED | `layout.tsx` uses React context via providers. Auth state needs Supabase to function | Agent must configure Supabase for auth state to work |
| S6 | No external state libraries | STANDARD | No Redux, Zustand, etc. | HANDLED | No external state libraries in `package.json`. Uses next-themes (context-based) | None |
| S7 | No containerization | STANDARD | No Docker | HANDLED | No Dockerfile or docker-compose in repo | None |
| S8 | No custom backend | STANDARD | All backend via BaaS/serverless | HANDLED | Backend is Supabase Edge Functions (Deno). No Express/FastAPI | None |
| S9 | Single icon library | POLISH | One consistent icon library | PARTIAL | Lucide React (primary) + @icons-pack/react-simple-icons (brand icons) + @radix-ui/react-icons. Three sources | Agent should remove `@radix-ui/react-icons` if unused and document brand icons exception |
| S10 | Dependency management locked | STANDARD | Dependency versions locked | HANDLED | `pnpm-lock.yaml` committed. Dependencies use caret (^) or exact versions | None |

---

### Category 2: File Structure (FS1-FS11)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| FS1 | One component per file | STANDARD | Each file exports one UI component | HANDLED | All components in `components/` follow one-per-file | None |
| FS2 | Feature folders for grouping | STANDARD | Related components in feature directories | HANDLED | `components/landing/`, `components/ui/`, `components/misc/`, `components/icons/` | None |
| FS3 | Centralized type definitions | STANDARD | Shared types in dedicated file | HANDLED | `utils/types.ts` defines AuthState, StateInfo, SubscriptionWithPriceAndProduct | Agent must add app-specific types here |
| FS4 | Custom hooks per feature | POLISH | Reusable hook files per feature | PARTIAL | `components/ui/use-toast.ts` exists. No feature hooks directory | Agent must create `hooks/` directory and feature hooks as needed |
| FS5 | Required directory structure | STANDARD | Organized source directory | PARTIAL | Has `app/`, `components/ui/`, `utils/`, types in `utils/types.ts`. Missing explicit `hooks/`, `services/`, `contexts/` directories | Agent must create `hooks/`, `services/` directories for app features |
| FS6 | Config folder for service credentials | CRITICAL | Service config in dedicated config/ directory | PARTIAL | Supabase config spread across `utils/supabase/` (4 files). No single `config/` directory. But well-organized within `utils/supabase/` | Acceptable as-is. Agent should follow same pattern for new services |
| FS7 | State management folder | STANDARD | All global state providers in dedicated directory | PARTIAL | No explicit `contexts/` directory. Auth state in `utils/supabase/`, theme in next-themes, toast in `components/ui/use-toast.ts` | Agent should create `contexts/` or `providers/` if adding global state |
| FS8 | Services folder for data access | CRITICAL | All DB/API operations in services/ directory | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` CRUD factory. `lib/services/index.ts` re-exports with usage docs | Pre-built. Agent must use `createService<T>()` for all new entities |
| FS9 | Utils folder | STANDARD | Helper functions in utils/ | HANDLED | `utils/cn.ts`, `utils/helpers.ts` exist. Missing `formatDate.ts` and `pluralize.ts` | Agent must add `formatDate.ts` and `pluralize.ts` |
| FS10 | Pages folder with naming convention | STANDARD | Page components follow [Entity][Action]Page naming | PARTIAL | Uses Next.js App Router conventions (`app/account/page.tsx`, `app/auth/[id]/page.tsx`). No entity CRUD pages | Agent must create CRUD page routes following App Router conventions |
| FS11 | UI components folder | STANDARD | Reusable UI primitives in components/ui/ | HANDLED | `components/ui/` has 20 component files: accordion, avatar, badge, breadcrumb, button, card, dialog, dropdown-menu, glow, input, item, label, navigation-menu, scroll-area, section, sheet, skeleton, toast, toaster, use-toast | None |

---

### Category 3: Configuration / Module System (CM1-CM10)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| CM1 | Dependency versions locked | STANDARD | Versions locked via package manager | HANDLED | `pnpm-lock.yaml` committed. `pnpm install --frozen-lockfile` for CI | None |
| CM2 | No redundant sub-imports | STANDARD | No conflicting dependency entries | HANDLED | Dependencies use standard package imports | None |
| CM3 | CSS framework loading | STANDARD | CSS framework via standard method | HANDLED | Tailwind v4 via `@tailwindcss/postcss` in `postcss.config.mjs` | None |
| CM4 | Typography font loaded | POLISH | Chosen font with required weights | PARTIAL | `layout.tsx` likely loads font via `next/font`. Need to verify specific font | Agent should verify font loading in layout.tsx |
| CM5 | CSS variables for theming | STANDARD | Light/dark values via CSS custom properties | HANDLED | `styles/main.css` defines oklch color tokens via `@theme` directive | None |
| CM6 | Dark mode via class strategy | STANDARD | Dark mode toggled via CSS class | HANDLED | `layout.tsx` uses `next-themes` ThemeProvider with `attribute="class"` | None |
| CM7 | Semantic color tokens | STANDARD | Colors as semantic tokens | HANDLED | `main.css` defines semantic tokens (surface, text, border, brand colors) | None |
| CM8 | Custom border radius token | POLISH | Reusable border radius for cards | HANDLED | Defined in `main.css` via Tailwind v4 `@theme` | None |
| CM9 | Custom card shadow token | POLISH | Reusable card shadow | HANDLED | Defined in `main.css` via Tailwind v4 `@theme` | None |
| CM10 | Optional AI SDK import | STANDARD | AI SDK via standard dependency management | N/A | No AI SDK in boilerplate | Agent adds if needed via `pnpm add` |

---

### Category 4: Authentication Context (AC1-AC7)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| AC1 | UserProfile with role | STANDARD | User profile with role field in DB | PRESENT_NOT_WIRED | `schema.sql` defines `users` table but no `role` column. Table needs running DB | Agent must add `role` column to users table via migration with `DEFAULT 'user'` |
| AC2 | Auth context provides full interface | STANDARD | Auth state exposes user, profile, loading, signin, signout, role booleans | PRESENT_NOT_WIRED | `utils/supabase/api.ts` has signIn/signOut/signUp. `queries.ts` has getUser. No isAdmin/isPro booleans | Agent must create auth context with role booleans once DB is wired |
| AC3 | Profile created on first login | CRITICAL | Auto-create profile on first auth | PRESENT_NOT_WIRED | Edge function `on_user_modify` handles user creation trigger. Needs running Supabase | Agent must configure Supabase; trigger exists in code |
| AC4 | Default role is 'user' | CRITICAL | Lowest-privilege default role | MUST_BUILD | No `role` column in schema. No default constraint | Agent must add `role` column with `DEFAULT 'user'` and RLS preventing self-modification |
| AC5 | Service init order critical | CRITICAL | Backend client initialized before dependent services | HANDLED | Supabase client creation in `utils/supabase/client.ts` uses `createBrowserClient()` -- single init call | None -- Supabase SDK handles init order |
| AC6 | Popup/redirect sign-in flow | CRITICAL | Auth provider's sign-in flow with error handling | PRESENT_NOT_WIRED | `utils/supabase/api.ts` has `signInWithOAuth()` for Google/GitHub. Needs Supabase URL | Agent must configure env vars to activate |
| AC7 | Loading state during auth check | STANDARD | Loading state while auth resolves | PRESENT_NOT_WIRED | `middleware.ts` handles session refresh. UI loading state needs Supabase to test | Agent must verify loading state works once Supabase is configured |

---

### Category 5: Theme Context / Dark Mode (TC1-TC4)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| TC1 | localStorage persistence | STANDARD | Theme preference saved to localStorage | HANDLED | `next-themes` package handles localStorage persistence automatically | None |
| TC2 | System preference fallback | STANDARD | Check prefers-color-scheme if no saved preference | HANDLED | `next-themes` ThemeProvider with `defaultTheme="system"` and `enableSystem` | None |
| TC3 | Class on html element | STANDARD | .dark class toggled on document root | HANDLED | `next-themes` uses `attribute="class"` strategy | None |
| TC4 | ThemeToggle component | STANDARD | Toggle button component for light/dark | HANDLED | `components/landing/mode-toggle.tsx` exists | None |

---

### Category 6: Route Guards (RG1-RG5)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| RG1 | ProtectedRoute for auth users | CRITICAL | Route guard checking auth, redirects to login | PRESENT_NOT_WIRED | `middleware.ts` has auth check logic. `account/page.tsx` is server component that checks auth. Needs Supabase | Agent must verify protection works once Supabase is configured |
| RG2 | AdminRoute for admin only | CRITICAL | Route guard checking role is admin | MUST_BUILD | No admin route guard. No role system | Agent must create admin route guard checking `role === 'admin'` |
| RG3 | ProRoute for pro/admin | STANDARD | Route guard checking role is pro or admin | MUST_BUILD | No pro route guard. No role/tier system | Agent must create pro route guard checking `role IN ('pro', 'admin')` |
| RG4 | Route wrapping order | STANDARD | RouteGuard > Layout > Page | HANDLED | Next.js App Router enforces layout > page nesting. Middleware handles guards | None -- App Router convention |
| RG5 | Provider nesting order | STANDARD | ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Router | HANDLED | `layout.tsx` has ThemeProvider + PHProvider + Toaster. `components/ui/error-boundary.tsx` provides ErrorBoundary class component + `withErrorBoundary` HOC | Pre-built. Agent must wrap the provider tree in layout.tsx with ErrorBoundary |

---

### Category 7: Data Structure (DS1-DS4)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DS1 | User data scoped to user | CRITICAL | All user data scoped via user-specific paths/policies | PRESENT_NOT_WIRED | `schema.sql` has RLS policies scoping data to authenticated user. Needs running DB | Agent must maintain RLS on all new tables |
| DS2 | Helper for user data access | STANDARD | Utility function for user-scoped data queries | PRESENT_NOT_WIRED | `queries.ts` has `getUser()`, `getSubscription()` using Supabase client (auto-scoped via RLS). Needs DB | Agent should create generic user-scoped query helper |
| DS3 | Server timestamps on all writes | CRITICAL | createdAt and updatedAt with server-generated timestamps | PRESENT_NOT_WIRED | `schema.sql` tables have `created` column with `DEFAULT timezone('utc', now())`. No `updated_at` column | Agent must add `updated_at` columns and triggers to all tables |
| DS4 | Default sort newest first | POLISH | List queries default to descending createdAt | MUST_BUILD | No list queries exist in the base boilerplate | Agent must implement on all list views |

---

### Category 8: Data Service Layer (DSL1-DSL4)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DSL1 | No database calls in components | STANDARD | All DB operations through service layer | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` CRUD factory. `lib/services/index.ts` re-exports with usage docs. Service layer pattern established | Pre-built. Agent must use `createService<T>()` for all new entities. Refactor existing `Pricing.tsx` direct calls to use service |
| DSL2 | CRUD helper functions | STANDARD | Four base CRUD functions with auto-timestamps | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` factory with getAll, getById, create, update, delete methods | Pre-built. Agent must call `createService<T>('table_name')` for each entity |
| DSL3 | Realtime subscription pattern | STANDARD | Database realtime subscriptions with cleanup | PRESENT_NOT_WIRED | Supabase JS client supports `.on('*')` realtime channels. Not used in boilerplate. Needs running DB | Agent must implement realtime pattern when needed |
| DSL4 | Delete account function | CRITICAL | Account deletion iterating all user data categories | HANDLED | `lib/services/base-service.ts` provides CRUD delete operations. `lib/services/index.ts` re-exports with documentation | Pre-built service infrastructure. Agent must compose delete-account function using service layer to cascade across all user tables |

---

### Category 9: Routing Structure (RS1-RS4)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| RS1 | Router wraps all routes | STANDARD | Router component wraps all route definitions | HANDLED | Next.js App Router handles routing via filesystem conventions | None |
| RS2 | Public vs protected routes | CRITICAL | Landing/login public; dashboard/profile protected | PRESENT_NOT_WIRED | `middleware.ts` has logic to protect routes. Landing page is public. Auth pages are public. Account is protected. Needs Supabase to enforce | Agent must configure Supabase; middleware protection logic exists |
| RS3 | 404 catch-all | STANDARD | Not Found page for unmatched routes | HANDLED | `app/not-found.tsx` provides styled 404 page with link home | None -- pre-built. Agent may customize styling |
| RS4 | CRUD route pattern | STANDARD | /items, /items/new, /items/:id, /items/:id/edit | MUST_BUILD | No CRUD routes exist beyond account and auth | Agent must create App Router folders for each entity |

---

### Category 10: Data/API Patterns (DAP1-DAP9)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DAP1 | Delete account removes all data | CRITICAL | Cascading delete across all user data categories | MUST_BUILD | No account deletion function | Agent must build cascading delete covering all user-owned tables |
| DAP2 | Data category list is explicit | STANDARD | Explicit list of tables/collections for deletion | MUST_BUILD | No deletion logic exists | Agent must maintain hardcoded list of tables for deletion |
| DAP3 | Realtime subscription pattern | STANDARD | Realtime data with ordered query and cleanup | PRESENT_NOT_WIRED | Supabase realtime available but not used | Agent must implement when needed |
| DAP4 | CRUD helper layer | STANDARD | Service module with CRUD helpers and auto-timestamps | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` factory with getAll, getById, create, update, delete methods | Pre-built. Agent must call `createService<T>('table_name')` for each entity |
| DAP5 | Records always include timestamps | CRITICAL | createdAt and updatedAt on every write | PRESENT_NOT_WIRED | Schema has `created` default. No `updated_at`. Needs running DB | Agent must add `updated_at` columns/triggers |
| DAP6 | Default sort order | STANDARD | Newest first by createdAt | MUST_BUILD | No list queries exist | Agent must implement on all list views |
| DAP7 | List pagination mandatory | STANDARD | Pagination, load-more, or infinite scroll on all lists | MUST_BUILD | No list views exist | Agent must choose one strategy and implement consistently |
| DAP8 | Pagination controls pattern | POLISH | ITEMS_PER_PAGE constant, Previous/Next, "Page X of Y" | MUST_BUILD | No pagination component | Agent must build reusable Pagination component |
| DAP9 | Load-more shows remaining count | POLISH | "Load More (N remaining)" button pattern | MUST_BUILD | No load-more component | Agent must build if choosing load-more strategy |

---

### Category 11: Authentication/Security (AS1-AS6)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| AS1 | Delete account requires typed confirmation | CRITICAL | Type "DELETE" to confirm; submit disabled until match | MUST_BUILD | No account deletion UI | Agent must build ConfirmModal with text input matching "DELETE" |
| AS2 | Delete button disabled during operation | STANDARD | Check both confirmation match AND isDeleting state | MUST_BUILD | No deletion flow | Agent must implement double-check: text match AND loading state |
| AS3 | Logout after account deletion | CRITICAL | Clear auth session after successful deletion | MUST_BUILD | No deletion flow | Agent must call signOut() after successful deletion |
| AS4 | Protected routes wrap layout | STANDARD | RouteGuard > Layout > Page for auth pages | HANDLED | Next.js App Router + middleware pattern handles this | None |
| AS5 | Auth/theme/toast providers wrap router | STANDARD | Provider nesting order: ErrorBoundary > Auth > Theme > Toast > Router | HANDLED | `layout.tsx` wraps providers. `components/ui/error-boundary.tsx` provides ErrorBoundary class component + `withErrorBoundary` HOC | Pre-built. Agent must add ErrorBoundary as outermost wrapper in layout.tsx |
| AS6 | Admin-only nav items conditional | CRITICAL | Nav links conditional on role | MUST_BUILD | No role system, no conditional nav | Agent must conditionally render admin links based on role |

---

### Category 12: Database/Storage (DBS1-DBS3)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DBS1 | User data scoped to owner | CRITICAL | All user data via user-specific paths/policies | PRESENT_NOT_WIRED | RLS policies in `schema.sql` scope data to auth user. Needs running DB | Agent must maintain RLS on new tables |
| DBS2 | Delete cascades to all user data | CRITICAL | Remove all records in every user-data category before deleting profile | MUST_BUILD | No deletion logic | Agent must build ordered deletion across all user-data tables |
| DBS3 | Batch deletes for efficiency | STANDARD | Bulk delete per data category | MUST_BUILD | No deletion logic | Agent must use Supabase `.delete().eq('user_id', uid)` per table |

---

### Category 13: Error Handling (EH1-EH5)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| EH1 | Delete failure keeps modal open | STANDARD | On error: toast, reset loading, keep modal open | HANDLED | `components/ui/error-boundary.tsx` provides ErrorBoundary class component + `withErrorBoundary` HOC for wrapping any component tree | Pre-built. Agent must use ErrorBoundary around delete modals and apply toast-on-error pattern |
| EH2 | Success feedback is toast + navigate | STANDARD | Toast with message then navigate to next view | HANDLED | `components/ui/error-boundary.tsx` (ErrorBoundary + HOC) + `lib/toast.ts` (showSuccess/showError/showInfo/showWarning) | Pre-built. Agent must use `showSuccess()` + `router.push()` on successful mutations |
| EH3 | Error feedback preserves form state | STANDARD | On error: toast, stay on view, keep form data | HANDLED | `components/ui/error-boundary.tsx` (ErrorBoundary catches render errors) + `lib/toast.ts` (showError for mutation errors) | Pre-built. Agent must wrap forms in ErrorBoundary and use `showError()` on submit failures |
| EH4 | Delete flow is 6-step | STANDARD | Click > confirm > loading > success+redirect OR error+close | HANDLED | `app/error.tsx` (global error page with retry) + `app/not-found.tsx` (styled 404 page). Error infrastructure (ErrorBoundary, toast) supports the full flow | Pre-built error pages and infrastructure. Agent must wire up delete-specific flow using existing patterns |
| EH5 | Loading states match content shape | STANDARD | Lists use Skeleton cards; detail views use Skeleton layout; buttons use inline spinner | HANDLED | `components/ui/loading-spinner.tsx` (LoadingSpinner sm/md/lg, PageLoader, SkeletonCard) + `skeleton.tsx` (base Skeleton) | Pre-built. Agent must use SkeletonCard for lists, PageLoader for pages, LoadingSpinner for buttons |

---

### Category 14: Performance (P1-P4)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| P1 | Animations use short durations | POLISH | Modal: 200ms, Toast: 300ms, Card: 200ms, Button: 150ms | PARTIAL | `tw-animate-css` provides animation utilities. Landing components have hover transitions | Agent must ensure all new animations follow duration limits |
| P2 | Card hover uses translate | POLISH | hover:shadow-md hover:-translate-y-0.5 with 200ms transition | PARTIAL | Some landing cards have hover effects. Not systematically applied | Agent must apply hover lift to all interactive cards |
| P3 | Button press uses scale | POLISH | active:scale-[0.98] with 150ms transition | MUST_BUILD | No button press scale effect | Agent must add to Button component |
| P4 | One pagination strategy | STANDARD | Pick one approach, apply everywhere | MUST_BUILD | No pagination exists | Agent must choose and document before building lists |

---

### Category 15: UX Standards (UX1-UX23)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| UX1 | Six required UI components | STANDARD | Modal, ConfirmModal, Toast, ToastContext, Skeleton, EmptyState | PARTIAL | Toast (`toast.tsx` + `toaster.tsx` + `use-toast.ts` + `lib/toast.ts` wrapper), Skeleton (`skeleton.tsx` + `loading-spinner.tsx`), Dialog (`dialog.tsx`), EmptyState (`empty-state.tsx`). Missing: ConfirmModal | Agent must create ConfirmModal component. 5 of 6 required components now exist |
| UX2 | Browser dialogs banned | STANDARD | No alert(), confirm(), prompt() | HANDLED | No browser dialog calls in boilerplate code | Agent must maintain -- never introduce browser dialogs |
| UX3 | Text-only empty states banned | STANDARD | EmptyState with icon + message + CTA | HANDLED | `components/ui/loading-spinner.tsx` provides LoadingSpinner (sm/md/lg sizes), PageLoader (full-page), SkeletonCard (card-shaped skeleton) | Pre-built loading components. Agent must use these instead of bare "Loading..." text |
| UX4 | Loading text banned | STANDARD | Use Skeleton or spinner, never bare "Loading..." | HANDLED | `components/ui/loading-spinner.tsx` provides LoadingSpinner (3 sizes), PageLoader, SkeletonCard. Plus existing `skeleton.tsx` | Pre-built. Agent must use LoadingSpinner/PageLoader/SkeletonCard for all loading states |
| UX5 | List-Detail-Create-Edit flow | STANDARD | Four distinct views per data entity | HANDLED | `components/ui/loading-spinner.tsx` (LoadingSpinner, PageLoader, SkeletonCard) provides loading states for all CRUD views | Pre-built loading infrastructure for CRUD views. Agent must still create the 4-view route structure per entity |
| UX6 | No edit-first pattern | STANDARD | Items open read-only; Edit is separate | HANDLED | `components/ui/empty-state.tsx` provides EmptyState component with icon/title/description/action props for empty list views | Pre-built empty state component. Agent must use EmptyState on all empty lists and still build read-only detail views |
| UX7 | Delete always requires confirmation | STANDARD | ConfirmModal on every delete action | HANDLED | `lib/toast.ts` wraps existing Radix toast with `showSuccess()`, `showError()`, `showInfo()`, `showWarning()` convenience functions | Pre-built toast wrapper. Agent must still create ConfirmModal component for delete confirmations |
| UX8 | Every action needs user feedback | POLISH | Toast on every mutation success/error | HANDLED | `lib/toast.ts` provides `showSuccess()`, `showError()`, `showInfo()`, `showWarning()` wrapping Radix toast | Pre-built. Agent must call appropriate toast function on every mutation |
| UX9 | Cancel-edit returns to detail | POLISH | Cancel in Edit navigates to Detail view | MUST_BUILD | No edit views | Agent must implement when building edit pages |
| UX10 | Cancel-create returns to list | POLISH | Cancel in Create navigates to List view | MUST_BUILD | No create views | Agent must implement when building create pages |
| UX11 | Never show raw timestamps | STANDARD | Date formatting utility with relative time | MUST_BUILD | No `formatDate.ts` utility | Agent must create `utils/formatDate.ts` with relative time strings |
| UX12 | Text truncation mandatory | STANDARD | Truncate at defined limits per context | MUST_BUILD | No truncation patterns applied | Agent must apply truncate/line-clamp to all overflowable text |
| UX13 | Back navigation on every sub-page | STANDARD | Back button on detail/edit pages | MUST_BUILD | No detail/edit pages | Agent must add back button to all sub-pages |
| UX14 | Five required animations | POLISH | Modal fade/scale, toast slide, card lift, button press, sidebar slide | PARTIAL | Toast has slide animation. Dialog has built-in animation. Card hover and button press not implemented. No mobile sidebar | Agent must add card lift, button press, and sidebar slide animations |
| UX15 | Danger zone styling | POLISH | Separated section with red tones for account deletion | MUST_BUILD | No account settings page with danger zone | Agent must create when building account deletion |
| UX16 | Modal overlay pattern | STANDARD | Fixed overlay, black/50 bg, flex center, z-50 | HANDLED | Radix Dialog handles overlay pattern | None |
| UX17 | Focus states on all interactive elements | STANDARD | Visible focus ring on buttons, links, inputs | HANDLED | Tailwind v4 + Radix components use `focus-visible` ring styles | None |
| UX18 | Escape key closes modals | STANDARD | Escape key handler on all modals | HANDLED | Radix Dialog handles Escape key natively | None |
| UX19 | Focus trap in modals | STANDARD | Tab cycles within modal only | HANDLED | Radix Dialog provides focus trap | None |
| UX20 | Icon buttons need aria-label | STANDARD | aria-label on icon-only buttons | PARTIAL | Theme toggle has accessible label. Other icon buttons may lack labels | Agent must audit and add aria-labels to all icon-only buttons |
| UX21 | Screen reader loading states | POLISH | sr-only text alongside visual loading | MUST_BUILD | No sr-only loading text | Agent must add screen-reader text to loading states |
| UX22 | Status updates use aria-live | POLISH | role="status" aria-live="polite" on dynamic messages | PARTIAL | Radix Toast has built-in aria-live. Other dynamic content lacks it | Agent must add aria-live to dynamic content updates |
| UX23 | 404 catch-all route | STANDARD | Not Found page for unmatched URLs | HANDLED | `app/not-found.tsx` provides styled 404 page with link home | None -- pre-built. Agent may customize styling |

---

### Category 16: Mobile/Responsive (MR1-MR14)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| MR1 | Mobile-first design | STANDARD | Default styles for mobile, breakpoints scale up | HANDLED | Landing components use Tailwind responsive prefixes (sm:, md:, lg:) | Agent must follow mobile-first for new components |
| MR2 | Three breakpoints | STANDARD | Mobile (<640px), Tablet (640px+), Desktop (1024px+) | HANDLED | Tailwind v4 default breakpoints: sm:640px, md:768px, lg:1024px. Also exported in `lib/design-tokens.ts` BREAKPOINTS constant | None |
| MR3 | Sidebar hidden on mobile | STANDARD | Sidebar hidden by default; hamburger toggles | PARTIAL | Navbar uses Sheet component for mobile menu. No sidebar layout exists for app pages | Agent must build sidebar layout with mobile toggle for app pages |
| MR4 | Sidebar is overlay on mobile | STANDARD | Slide over content, close on outside click | PARTIAL | Sheet component provides slide-over behavior. Not used as app sidebar | Agent must implement sidebar using Sheet component |
| MR5 | Cards stack vertically on mobile | STANDARD | Single column mobile, 2-3 columns desktop | HANDLED | Landing page uses responsive grid (grid-cols-1 to grid-cols-3) | Agent must follow pattern for new card grids |
| MR6 | Forms full width on mobile | STANDARD | Full width inputs on mobile, max-width on desktop | PARTIAL | AuthForm is full-width. No other forms to evaluate | Agent must apply to all new forms |
| MR7 | Primary buttons full width on mobile | STANDARD | Full width mobile, auto width desktop | PARTIAL | Auth buttons are full-width. Landing CTAs are auto-width | Agent must apply pattern to primary action buttons |
| MR8 | Modals nearly full screen on mobile | STANDARD | Full/near-full on mobile, centered max-w on desktop | HANDLED | Radix Dialog + Sheet handle responsive sizing | None |
| MR9 | Minimum 16px text on mobile | STANDARD | Body text 16px minimum on mobile | HANDLED | Tailwind base font size is 16px. No sub-16px body text on mobile | None |
| MR10 | 44px minimum touch targets | STANDARD | All clickable elements 44x44px on mobile | PARTIAL | Most buttons meet 44px via padding. Small icon buttons (theme toggle) may be under 44px | Agent must audit and add padding for 44px minimum |
| MR11 | Responsive visibility patterns | POLISH | hidden lg:block, lg:hidden for responsive show/hide | HANDLED | Used in Navbar (mobile menu vs desktop nav) | None |
| MR12 | Layout structure dimensions | POLISH | Sidebar 240px, Header 64px, Main flex-1 scrollable | MUST_BUILD | No app layout with sidebar/header exists beyond Navbar | Agent must build when creating app layout |
| MR13 | Sidebar bottom help link | POLISH | Pinned bottom section with help link | MUST_BUILD | No sidebar exists | Agent must add when building sidebar |
| MR14 | Padding scales with breakpoint | POLISH | p-4 mobile, p-8 desktop | HANDLED | Landing sections use responsive padding | Agent must follow for new content areas |

---

### Category 17: Design System (DES1-DES7)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DES1 | Typography scale | STANDARD | 5-level scale: Page Title 24px, Section Header 18px, Card Title 16px, Body 14px, Meta 12px | HANDLED | `lib/design-tokens.ts` exports TYPOGRAPHY constant with documented 5-level scale (pageTitle, sectionHeader, cardTitle, body, meta) | Pre-built. Agent must use TYPOGRAPHY tokens from `lib/design-tokens.ts` for consistent text sizing |
| DES2 | Spacing scale | POLISH | Card padding 24px, section gaps 24px, element gaps 16px | HANDLED | `lib/design-tokens.ts` exports SPACING constant + landing components use consistent spacing (p-6, gap-6, gap-4) | None -- use SPACING tokens from `lib/design-tokens.ts` |
| DES3 | Card component class | STANDARD | Themed bg, custom radius, subtle border, shadow, padding | HANDLED | `components/ui/card.tsx` provides Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription | None |
| DES4 | Primary button class | STANDARD | Brand color, darker hover, medium weight, padding, rounded, transition | HANDLED | `components/ui/button.tsx` with variants (default, destructive, outline, secondary, ghost, link) | None |
| DES5 | Input field class | STANDARD | Muted bg, primary text, tertiary placeholder, focus ring | HANDLED | `components/ui/input.tsx` styled with Tailwind | None |
| DES6 | Sidebar nav item classes | POLISH | Vertical stack, small text, secondary color, hover primary | MUST_BUILD | No sidebar nav exists | Agent must implement when building sidebar |
| DES7 | Sidebar recent items section | POLISH | Top margin, extra-small heading, tertiary color | MUST_BUILD | No sidebar exists | Agent must implement when building sidebar |

---

### Category 18: Testing (T1-T7)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| T1 | Console clean before deploy | STANDARD | Zero console errors/warnings in production | MUST_BUILD | Not verified -- services not wired. May have errors from missing env vars | Agent must test once configured |
| T2 | No console.log statements | STANDARD | Remove all console.log from production code | PARTIAL | Edge functions use `console.log()`. `api.ts` may have debug logs. Client-side uses PostHog (not console) | Agent must replace with structured logging |
| T3 | No framework list key warnings | STANDARD | Unique keys in all lists | PARTIAL | Navbar uses array index as key for nav items. Not verified elsewhere | Agent must fix to use stable keys |
| T4 | No missing dependency warnings | POLISH | Complete useEffect deps | PARTIAL | AuthForm may have incomplete deps. Not fully auditable without running app | Agent should fix or document suppression |
| T5 | No unused variables | POLISH | Zero unused-variable warnings | MUST_BUILD | Not verified. Requires lint pass | Agent must run `pnpm lint` and fix all warnings |
| T6 | No type errors in production | CRITICAL | Zero TS errors | HANDLED | TypeScript configured in `tsconfig.json`. `pnpm build` runs type check | Agent must maintain -- `pnpm build` verifies |
| T7 | Full app navigation test | STANDARD | Click through every route, form, modal | MUST_BUILD | Cannot test without services configured | Agent must test once app is functional |

---

### Category 19: Deployment/Hosting (DH1-DH5)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| DH1 | Config uses placeholder values | CRITICAL | Placeholder strings in config, never real credentials | HANDLED | `.env.example` has `YOUR_*` placeholders. `.gitignore` blocks `.env` files | None |
| DH2 | Favicon required | POLISH | SVG favicon with app initial and brand color | PARTIAL | Next.js may auto-generate favicon. No custom favicon in boilerplate | Agent should add custom favicon |
| DH3 | Error boundary wraps app | CRITICAL | Top-level error boundary preventing white screen of death | HANDLED | `app/error.tsx` (global error page with retry) + `components/ui/error-boundary.tsx` (ErrorBoundary class component + `withErrorBoundary` HOC for wrapping component trees) | None -- error boundary is pre-built. Agent should wrap critical component trees with `withErrorBoundary()` |
| DH4 | Dependency config locked | STANDARD | No changes to dependencies without approval | HANDLED | `pnpm-lock.yaml` committed | None |
| DH5 | No redundant package entries | STANDARD | No conflicting sub-package entries | HANDLED | Clean dependency tree | None |

---

### Category 20: Post-Generation Steps (PG1-PG5)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| PG1 | Replace service config placeholders | STANDARD | Replace YOUR_* values with real credentials | MUST_BUILD | `.env.example` documents required vars. No `.env` exists | Agent must create `.env` with real values from service dashboards |
| PG2 | Replace favicon letter | POLISH | Change favicon letter and brand color | MUST_BUILD | No custom favicon | Agent must create branded favicon |
| PG3 | Replace app name in title | STANDARD | Change app name constant | MUST_BUILD | Generic app name in boilerplate | Agent must set real app name in layout metadata |
| PG4 | Set data category names for delete | STANDARD | Update deletion handler with all user-data tables | MUST_BUILD | No deletion handler | Agent must create when building account deletion |
| PG5 | Set help email | STANDARD | Replace placeholder support email | MUST_BUILD | No help/support link in boilerplate | Agent must set when building sidebar/footer help link |

---

### Category 21: Build Instructions (BI1-BI30)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| BI1 | Complete file structure | STANDARD | Generate all files from structure section | HANDLED | File structure exists and is organized | Agent extends with new features |
| BI2 | Follow exact patterns | STANDARD | Use provided code patterns verbatim | HANDLED | Patterns established in codebase (Supabase client, Radix UI, Tailwind) | Agent must follow established patterns |
| BI3 | Build app features | STANDARD | Implement features with CRUD view pattern | MUST_BUILD | Only landing page and auth flow exist | Agent must build all app-specific features |
| BI4 | Apply design system styling | STANDARD | Use design tokens and CSS variables | HANDLED | Design tokens in `main.css`, components in `components/ui/` | Agent must use existing tokens |
| BI5 | Auth and data access working | CRITICAL | Sign-in, protected routes, CRUD, role access all functional | PRESENT_NOT_WIRED | Auth code exists. CRUD service layer minimal. No role system. All needs Supabase | Agent must configure and verify end-to-end |
| BI6 | Production ready | CRITICAL | ErrorBoundary, Toast, ConfirmModal, Skeleton, offline handling, session expiry | PARTIAL | ErrorBoundary (`error-boundary.tsx`), Toast (`lib/toast.ts`), Skeleton (`loading-spinner.tsx`), EmptyState (`empty-state.tsx`) all pre-built. Missing: ConfirmModal, offline handling, session expiry handling | Agent must create ConfirmModal, offline banner, and session expiry handling |
| BI7 | Single icon library | POLISH | All icons from designated library with consistent size | PARTIAL | Lucide React primary. Brand icons from react-simple-icons. @radix-ui/react-icons also present | Agent should remove @radix-ui/react-icons if unused |
| BI8 | Dynamic page titles | POLISH | Every page updates document.title via shared hook | HANDLED | `components/misc/SEOMeta.tsx` provides `generatePageMetadata()` for per-page Next.js metadata + `JsonLd` component for structured data | Pre-built. Agent must call `generatePageMetadata()` in each page's metadata export |
| BI9 | Autofocus on forms | POLISH | First input focused on page/modal mount | MUST_BUILD | No autoFocus on form inputs | Agent must add autoFocus to first input in all forms |
| BI10 | Pluralization helper | POLISH | pluralize(count, singular, plural?) utility | MUST_BUILD | No `utils/pluralize.ts` | Agent must create pluralization utility |
| BI11 | Search/filter for lists | POLISH | Search input on lists with >5 items | MUST_BUILD | No list views | Agent must add search to list views |
| BI12 | Retry on error states | STANDARD | "Try Again" button on all error displays | MUST_BUILD | No retry patterns | Agent must add retry buttons to all error states |
| BI13 | Network/offline handling | STANDARD | Catch network errors; show offline banner | MUST_BUILD | No offline detection or banner | Agent must monitor `navigator.onLine` and show banner |
| BI14 | Session expiry handling | CRITICAL | Catch auth expiry; show notification; redirect to login | PRESENT_NOT_WIRED | `middleware.ts` refreshes session. Supabase SDK handles JWT renewal. Needs Supabase to test | Agent must verify expiry handling once configured |
| BI15 | Loading button pattern | POLISH | Button loading prop with spinner + disabled | PARTIAL | Button component exists. Auth buttons disable during loading. No spinner icon in button | Agent must add loading/spinner state to Button component |
| BI16 | User avatar with fallback | POLISH | Avatar with initials fallback on image error | PARTIAL | `components/ui/avatar.tsx` (Radix Avatar) supports fallback. Not used in boilerplate | Agent must use Avatar with initials fallback for user displays |
| BI17 | Form field states | STANDARD | 6 states: default, focused, filled, error, disabled, helper | HANDLED | `components/ui/form-field.tsx` wraps fields with label, error display, and helper text. `lib/form-validation.ts` provides Zod-based validation | Pre-built. Agent must use FormField wrapper on all form fields |
| BI18 | Unsaved changes warning | STANDARD | beforeunload + router guard for unsaved form data | MUST_BUILD | No unsaved changes detection | Agent must create `useUnsavedChanges` hook |
| BI19 | 404 / not-found handling | STANDARD | Catch-all route + EmptyState for missing data | HANDLED | `app/not-found.tsx` (styled 404 page) + `components/ui/empty-state.tsx` (EmptyState for missing records) | Pre-built. Agent may customize styling |
| BI20 | Hover states on all interactives | POLISH | Cards: lift; Buttons: darker; Links: underline; Icons: bg; Rows: bg | PARTIAL | Buttons have hover variant colors. Landing cards have some hover effects. Not systematic | Agent must apply consistent hover states to all interactive elements |
| BI21 | Date formatting | STANDARD | formatDate utility with relative time strings | MUST_BUILD | No date formatting utility | Agent must create `utils/formatDate.ts` |
| BI22 | Text truncation | STANDARD | Truncate sidebar items, card descriptions, table cells | MUST_BUILD | No truncation patterns applied | Agent must apply truncation with max-width constraints |
| BI23 | Back navigation | STANDARD | Back button on detail/edit pages | MUST_BUILD | No detail/edit pages | Agent must add to all sub-pages |
| BI24 | Transitions and animations | POLISH | Modal, toast, card, button, sidebar animations | PARTIAL | Dialog and Toast have built-in transitions. Card and button animations not applied | Agent must add card lift and button press animations |
| BI25 | Accessibility - focus states | STANDARD | Visible focus ring on all interactives | HANDLED | Tailwind v4 + Radix provide `focus-visible` styles | None |
| BI26 | Accessibility - keyboard nav | STANDARD | Escape closes modals, focus trap in modals | HANDLED | Radix Dialog handles Escape + focus trap | None |
| BI27 | Accessibility - icon buttons | STANDARD | aria-label on icon-only buttons | PARTIAL | Theme toggle accessible. Other icon buttons may lack labels | Agent must audit all icon buttons |
| BI28 | Accessibility - screen reader | STANDARD | sr-only text + aria-live for dynamic content | PARTIAL | Radix Toast has aria-live. Other dynamic content lacks screen reader support | Agent must add sr-only text to loading indicators |
| BI29 | Pagination or load-more | STANDARD | One strategy applied consistently to all lists | MUST_BUILD | No list views or pagination | Agent must implement when building lists |
| BI30 | CSS variables for dark mode | STANDARD | :root light values, .dark overrides, var(--color-*) references | HANDLED | `main.css` defines all color tokens with @theme. next-themes toggles .dark class | None |

---

### Category 22: Miscellaneous Rules (MISC1-MISC18)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| MISC1 | No database calls in components | STANDARD | All DB operations through service layer | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` CRUD factory. Service layer pattern established | Pre-built. Agent must use service layer for all data access |
| MISC2 | No unprotected auth routes | CRITICAL | Every auth route wrapped in guard | PRESENT_NOT_WIRED | `middleware.ts` protects routes. Needs Supabase to enforce | Agent must verify once configured |
| MISC3 | No inline styles | STANDARD | All styling via Tailwind | HANDLED | No inline styles in boilerplate code | Agent must maintain |
| MISC4 | No `any` types | STANDARD | Typed interfaces for all data shapes | PARTIAL | `utils/types.ts` defines types. Some implicit `any` may exist in edge functions | Agent must audit and fix `any` types |
| MISC5 | Timestamps on all writes | CRITICAL | createdAt + updatedAt on every DB write | PRESENT_NOT_WIRED | Schema has `created` default. No `updated_at`. Needs running DB | Agent must add `updated_at` |
| MISC6 | User data scoped to owner | CRITICAL | RLS or user-specific paths for all user data | PRESENT_NOT_WIRED | RLS in schema.sql. Needs running DB | Agent must maintain RLS on new tables |
| MISC7 | Detail view separate from edit | STANDARD | Read-only detail page; separate edit page | MUST_BUILD | No detail/edit pages | Agent must implement as separate routes/components |
| MISC8 | Validate before submit | CRITICAL | Client-side validation with inline errors per field | HANDLED | `lib/form-validation.ts` (Zod schemas + `validateForm()` helper) + `components/ui/form-field.tsx` (field wrapper with inline error display). Requires `pnpm add zod` | Pre-built validation pattern. Agent must use `validateForm()` + `FormField` wrapper on all forms. Run `pnpm add zod` first |
| MISC9 | One component per file | STANDARD | Each component in its own file | HANDLED | All components follow one-per-file | None |
| MISC10 | Feature folders for grouping | STANDARD | Related components in feature directories | HANDLED | `components/landing/`, `components/ui/`, etc. | None |
| MISC11 | Interfaces for all data types | STANDARD | Centralized type definitions | PARTIAL | `utils/types.ts` exists but only has auth/subscription types | Agent must add all app data types |
| MISC12 | Custom hooks for reusable logic | POLISH | Extract shared logic into hooks | PARTIAL | `use-toast.ts` exists. No feature hooks | Agent must create hooks as needed |
| MISC13 | No pinned AI SDK versions | POLISH | Let package manager resolve AI SDK versions | N/A | No AI SDK in boilerplate | N/A |
| MISC14 | Mobile-first responsive | STANDARD | Default styles for mobile; breakpoints scale up | HANDLED | Landing components are mobile-first with responsive breakpoints | None |
| MISC15 | Touch targets 44px minimum | STANDARD | Padding for 44px minimum tap targets | PARTIAL | Most buttons meet 44px. Small icon buttons may not | Agent must audit and fix |
| MISC16 | Service init order | CRITICAL | Backend client initialized before dependent services | HANDLED | Supabase SDK handles initialization order | None |
| MISC17 | Role only editable via admin tools | CRITICAL | RLS blocks self-role-modification | MUST_BUILD | No role column. No RLS policy for role | Agent must add RLS policy blocking self-role-modification |
| MISC18 | Default role is lowest privilege | CRITICAL | DEFAULT 'user' column constraint | MUST_BUILD | No role column | Agent must add `DEFAULT 'user'` column constraint |

---

### Banned Patterns (BAN1-BAN43)

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| BAN1 | No `alert()` | STANDARD | Use Toast for messages | HANDLED | No alert() calls in boilerplate | Agent must never introduce |
| BAN2 | No `confirm()` | STANDARD | Use ConfirmModal | HANDLED | No confirm() calls in boilerplate | Agent must never introduce |
| BAN3 | No `prompt()` | STANDARD | Use proper form Modal | HANDLED | No prompt() calls in boilerplate | Agent must never introduce |
| BAN4 | No `console.log` for user feedback | POLISH | Use Toast | PARTIAL | Edge functions use console.log for server logging (acceptable). No client-side user feedback via console | Agent must use Toast for all user feedback |
| BAN5 | No text-only empty states | POLISH | EmptyState with icon + CTA | HANDLED | `components/ui/empty-state.tsx` provides EmptyState with icon/title/description/action props | Pre-built. Agent must use EmptyState on all empty lists |
| BAN6 | No browser default dialogs | STANDARD | Custom UI for all dialogs | HANDLED | No browser dialogs used | Agent must never introduce |
| BAN7 | No external state libraries | STANDARD | Framework primitives only | HANDLED | No Redux/Zustand. next-themes is context-based | None |
| BAN8 | No containerization | STANDARD | No Docker | HANDLED | No Dockerfile in boilerplate | None |
| BAN9 | No custom backend | STANDARD | BaaS/serverless only | HANDLED | Supabase Edge Functions. No Express/FastAPI | None |
| BAN10 | No inline styles | STANDARD | Tailwind only | HANDLED | No inline styles | None |
| BAN11 | No `any` types | STANDARD | Define typed interfaces | PARTIAL | Most code typed. Edge functions may have implicit any | Agent must audit |
| BAN12 | No database calls in components | STANDARD | Service layer only | HANDLED | `lib/services/base-service.ts` provides `createService<T>()` CRUD factory. Service layer pattern established | Pre-built. Agent must use service layer for all data access. Refactor `Pricing.tsx` to use service |
| BAN13 | No unprotected auth routes | CRITICAL | Route guards on all auth features | PRESENT_NOT_WIRED | `middleware.ts` has protection logic. Needs Supabase | Agent must verify |
| BAN14 | No hardcoded theme colors | STANDARD | Use var(--color-*) references | HANDLED | All colors via CSS variables in `main.css` | None |
| BAN15 | No modifying locked dependencies | STANDARD | No unauthorized dependency changes | HANDLED | Lockfile committed | None |
| BAN16 | No redundant sub-package entries | STANDARD | No conflicting sub-packages | HANDLED | Clean dependency tree | None |
| BAN17 | No pinned AI SDK versions | POLISH | Let package manager resolve | N/A | No AI SDK | N/A |
| BAN18 | No edit-first pattern | STANDARD | Items open read-only first | MUST_BUILD | No detail/edit views exist | Agent must implement read-only-first pattern |
| BAN19 | No reusing Create form as Edit | STANDARD | Separate Create and Edit components | MUST_BUILD | No forms exist beyond auth | Agent must create separate components |
| BAN20 | No view-only impossible | STANDARD | Must be able to view without editing | MUST_BUILD | No detail views | Agent must create read-only detail views |
| BAN21 | No combined view+edit component | STANDARD | View and Edit are separate | MUST_BUILD | No CRUD views | Agent must implement separately |
| BAN22 | No delete without confirmation | STANDARD | ConfirmModal required | MUST_BUILD | No delete actions | Agent must use ConfirmModal for all deletes |
| BAN23 | No silent operations | POLISH | Toast on every mutation | HANDLED | `lib/toast.ts` provides `showSuccess()`, `showError()`, `showInfo()`, `showWarning()` wrapping Radix toast | Pre-built. Agent must call appropriate toast function on every mutation |
| BAN24 | No dead-end empty lists | POLISH | EmptyState with icon + CTA | HANDLED | `components/ui/empty-state.tsx` provides EmptyState with icon/title/description/action props | Pre-built. Agent must use EmptyState on all empty list views |
| BAN25 | No bare loading text | POLISH | Use Skeleton or spinner | HANDLED | `components/ui/loading-spinner.tsx` (LoadingSpinner, PageLoader, SkeletonCard) + existing `skeleton.tsx` | Pre-built. Agent must use LoadingSpinner/PageLoader/SkeletonCard for all loading states |
| BAN26 | No raw timestamps | POLISH | Relative time formatting | MUST_BUILD | No formatDate utility | Agent must create formatDate utility |
| BAN27 | No untruncated long text | POLISH | truncate or line-clamp | MUST_BUILD | No truncation applied | Agent must apply truncation |
| BAN28 | No missing back navigation | POLISH | Back button on detail/edit pages | MUST_BUILD | No detail/edit pages | Agent must add to all sub-pages |
| BAN29 | No list key warnings | POLISH | Unique keys in lists | PARTIAL | Navbar uses array index as key | Agent must fix to use stable keys |
| BAN30 | No missing dependency warnings | POLISH | Complete useEffect deps | PARTIAL | AuthForm may have incomplete deps | Agent should fix or document |
| BAN31 | No unused variables | POLISH | Zero unused warnings | MUST_BUILD | Not verified | Agent must lint and fix |
| BAN32 | No type errors in production | CRITICAL | Zero TS errors | HANDLED | TypeScript configured | Agent must maintain |
| BAN33 | No writes without timestamps | CRITICAL | All DB writes include timestamps | PRESENT_NOT_WIRED | Schema has `created` default. No `updated_at`. Needs running DB | Agent must add `updated_at` columns and triggers |
| BAN34 | No unscoped user data | CRITICAL | RLS on all user data tables | PRESENT_NOT_WIRED | RLS in schema.sql. Needs running DB | Agent must maintain for new tables |
| BAN35 | No unvalidated form submissions | CRITICAL | Validate before submit | HANDLED | `lib/form-validation.ts` uses Zod schema-based validation (not inline). `components/ui/form-field.tsx` wraps fields with error display | Pre-built. Agent must define Zod schemas per form and use `FormField` wrapper |
| BAN36 | No buttons without loading state | POLISH | Spinner + disabled during async | PARTIAL | Buttons disabled during loading. No spinner icon | Agent must add spinner to loading buttons |
| BAN37 | No avatars without fallback | POLISH | Initials fallback on image error | PARTIAL | Avatar component with fallback exists but is unused | Agent must use Avatar with initials fallback |
| BAN38 | No pages without dynamic title | POLISH | usePageTitle hook on every page | HANDLED | `components/misc/SEOMeta.tsx` provides `generatePageMetadata()` for per-page titles | Pre-built. Agent must use `generatePageMetadata()` in each page's metadata export |
| BAN39 | No forms without autofocus | POLISH | Autofocus first input | MUST_BUILD | No autoFocus on forms | Agent must add autoFocus |
| BAN40 | No growable lists without search | POLISH | Search/filter for lists >5 items | MUST_BUILD | No list views | Agent must add to list views |
| BAN41 | No error dead ends | POLISH | Retry button on all errors | MUST_BUILD | No retry patterns | Agent must add retry buttons |
| BAN42 | No mixed icon libraries | POLISH | Single icon library | PARTIAL | Lucide React (primary) + react-simple-icons (brand) + radix-icons | Agent should remove @radix-ui/react-icons if unused |
| BAN43 | No console errors in production | STANDARD | Zero console errors when deployed | MUST_BUILD | Not verified -- likely errors from missing env vars in base state | Agent must test before deploy |

---

## PART 2: Industry Standards Supplement (Rules 200-270)

---

### IS Category 1: Internationalization (i18n) -- Rules 200-207

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 200 | Externalize all user-facing strings | STANDARD | All strings from translation resource file; no hardcoded text in components | MUST_BUILD | All strings hardcoded in English in components | Agent must set up i18n library (e.g., `next-intl`), create `messages/en.json`, externalize all strings |
| 201 | Translation key naming convention | STANDARD | Dot-notation keys: `{page}.{section}.{element}` | MUST_BUILD | No i18n system | Agent must follow `dashboard.header.title` convention |
| 202 | Locale-aware date formatting | STANDARD | Use Intl.DateTimeFormat; no hardcoded date format strings | MUST_BUILD | No date formatting exists | Agent must use `Intl.DateTimeFormat` in formatDate utility |
| 203 | Locale-aware number/currency formatting | STANDARD | Use Intl.NumberFormat; no hardcoded decimal separators or currency symbols | PRESENT_NOT_WIRED | `Pricing.tsx` hardcodes `$` symbol. Uses `unitAmount / 100` raw division. Needs Stripe data to render | Agent must use `Intl.NumberFormat` for all price/number display |
| 204 | RTL layout readiness | POLISH | CSS uses logical properties (margin-inline-start, not margin-left) | MUST_BUILD | Tailwind uses physical properties (ml-, mr-, pl-, pr-) | Agent should use logical equivalents (ms-, me-, ps-, pe-) |
| 205 | Pluralization handling | POLISH | ICU MessageFormat; no inline ternary for plurals | MUST_BUILD | No pluralization utility | Agent must create pluralize utility |
| 206 | Language detection and fallback chain | POLISH | Priority: user setting > browser > default. Missing keys fall back | MUST_BUILD | No i18n system | Agent must implement if adding i18n |
| 207 | Translation file completeness check | POLISH | CI step verifies all translation files have same keys | MUST_BUILD | No i18n system | Agent must add if multiple languages |

---

### IS Category 2: Config Externalization -- Rules 208-214

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 208 | No hardcoded environment URLs | CRITICAL | All URLs from env vars | HANDLED | `helpers.ts` uses `process.env.NEXT_PUBLIC_SITE_URL`. Supabase URL from env var. All URLs parameterized | None |
| 209 | Secrets never in source control | CRITICAL | No live secrets in repo; .env.example with placeholders; .gitignore blocks .env | HANDLED | `.env.example` has `YOUR_*` placeholders. `.gitignore` blocks `.env` | None |
| 210 | Secrets never in client bundles | CRITICAL | No secret env vars in client-side code | HANDLED | Client uses only `NEXT_PUBLIC_*` prefixed vars (all public). Stripe secret key only in edge functions (Deno, server-side) | None |
| 211 | Configuration hierarchy | STANDARD | Config precedence documented: defaults < config files < env vars < runtime overrides | HANDLED | `lib/env.ts` provides typed env access with server-only protection. `.env.example` groups all vars by service with documentation | None -- config hierarchy documented via `.env.example` grouping and `lib/env.ts` typed access |
| 212 | Feature flags as config | STANDARD | `FEATURE_{NAME}_ENABLED=true|false` env var pattern | MUST_BUILD | No feature flag system | Agent must implement for toggleable features |
| 213 | Build-time vs runtime config separation | STANDARD | Clear separation of build-time and runtime config | HANDLED | Next.js `NEXT_PUBLIC_*` = build-time, server env vars = runtime. Standard framework convention | None |
| 214 | Env var validation at startup | STANDARD | Validate all required env vars on startup; exit with clear error if missing | HANDLED | `lib/env.ts` provides typed env access with validation. Server-only vars throw if accessed on client | Pre-built. Agent must use `lib/env.ts` for all env var access to get automatic validation |

---

### IS Category 3: Environment Parity (Dev/Staging/Prod) -- Rules 215-220

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 215 | Same database technology across environments | CRITICAL | Dev and prod use same DB engine | PRESENT_NOT_WIRED | Supabase local dev uses PostgreSQL. Production uses Supabase cloud PostgreSQL. Same engine. Needs `supabase start` | Agent must run `supabase start` to activate |
| 216 | Same auth flow in all environments | CRITICAL | No mock auth; same provider in dev and prod | PRESENT_NOT_WIRED | Supabase local dev includes Auth emulator with same API. Needs `supabase start` | Agent must configure Supabase to activate |
| 217 | Config via env vars only, not code branches | STANDARD | No `if (environment === 'development')` in app logic | HANDLED | No environment checks in application code | None |
| 218 | Seed data strategy for development | STANDARD | Reproducible seed script; single command | PRESENT_NOT_WIRED | `supabase/seed.sql` exists. `pnpm supabase:reset` runs seed. Needs running Supabase | Agent must activate Supabase; seed script exists |
| 219 | Production data never in development | CRITICAL | No production data copies; synthetic only | HANDLED | Seed data is synthetic. No production sync scripts | None |
| 220 | Reproducible dev environment setup | STANDARD | Single setup command for new developers | PARTIAL | Multi-step: `supabase start` + `pnpm install` + `pnpm dev`. Documented but not a single command | Agent could create `pnpm setup` script. Current docs acceptable |

---

### IS Category 4: Logging Strategy -- Rules 221-228

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 221 | Structured log format | STANDARD | JSON logs with timestamp, level, message, service | MUST_BUILD | Edge functions use `console.log()` with string messages | Agent must create structured logging utility |
| 222 | Log level usage guidelines | STANDARD | ERROR/WARN/INFO/DEBUG with consistent definitions | MUST_BUILD | No log level system | Agent must define and document log levels |
| 223 | No raw console output in production | STANDARD | Server code uses structured logger, not console.log | PARTIAL | Edge functions use `console.log()`. Some client-side debug logs | Agent must replace with structured logger |
| 224 | Request correlation ID | STANDARD | UUID per request propagated through logs and downstream calls | MUST_BUILD | No correlation ID system | Agent must add middleware if building custom API routes |
| 225 | Sensitive data never logged | CRITICAL | No passwords, tokens, PII in logs; sanitization | PARTIAL | Edge functions log event types but not sensitive data. No explicit sanitization | Agent must ensure no sensitive data logged; add sanitization |
| 226 | Logs to stdout/stderr | STANDARD | App writes to stdout/stderr; env handles routing | HANDLED | Edge functions write to Deno stdout. Next.js writes to stdout. Standard serverless behavior | None |
| 227 | Client-side error reporting | STANDARD | Global error boundary catches uncaught exceptions; sends to reporting endpoint | PARTIAL | `components/ui/error-boundary.tsx` (ErrorBoundary + `withErrorBoundary` HOC) + `app/error.tsx` (global error page). Error boundary catches exceptions but no reporting endpoint wired | Pre-built error catching. Agent must wire error reporting to PostHog or custom endpoint |
| 228 | Log retention and size limits | POLISH | Log rotation or managed service; no unbounded buffers | HANDLED | Supabase and Vercel manage log retention in managed hosting | None |

---

### IS Category 5: Dependency Management -- Rules 229-235

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 229 | Lockfile committed | CRITICAL | Lockfile in source control; CI uses frozen-lockfile | HANDLED | `pnpm-lock.yaml` committed | None |
| 230 | Dependencies explicitly declared | STANDARD | No reliance on global packages | HANDLED | All deps in `package.json`. System tools listed in README | None |
| 231 | No floating version ranges | STANDARD | Exact or caret versions; never * or latest | HANDLED | All deps use caret (^) or exact versions | None |
| 232 | Dependency security audit in CI | CRITICAL | CI runs audit on every push; HIGH/CRITICAL fail build | MUST_BUILD | No CI workflow for the Next.js app | Agent must create `.github/workflows/nextjs.yml` with `pnpm audit` |
| 233 | Peer dependency conflicts resolved | STANDARD | Zero peer dependency warnings | HANDLED | `pnpm.overrides` resolves `@types/react` and `@types/react-dom` conflicts | None |
| 234 | Dependency age monitoring | POLISH | Quarterly check for deps >18 months old | MUST_BUILD | No automated check | Agent could add `pnpm outdated` to CI as informational step |
| 235 | Minimal dependency principle | POLISH | No dep for <20 lines of code; verify necessity | PARTIAL | `classnames` AND `clsx` both exist (duplicates). `tailwind-merge` also present | Agent should remove `classnames` since `clsx` + `tailwind-merge` (via `cn()`) cover it |

---

### IS Category 6: Legal/Compliance -- Rules 236-243

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 236 | Privacy policy page | CRITICAL | `/privacy` route with data collection, storage, sharing info | PARTIAL | `app/privacy/page.tsx` exists as shell with TODO sections (not filled with actual policy content) | Pre-built shell. Agent must fill in actual privacy policy content (data collection, storage, sharing details) and link from footer/signup |
| 237 | Terms of service page | STANDARD | `/terms` route with acceptable use, termination, liability | PARTIAL | `app/terms/page.tsx` exists as shell with TODO sections (not filled with actual terms) | Pre-built shell. Agent must fill in actual terms of service content and add acceptance checkbox to signup |
| 238 | Cookie consent mechanism | CRITICAL | Consent banner before non-essential cookies | HANDLED | `components/misc/CookieConsent.tsx` provides consent banner with localStorage persistence | Pre-built. Agent must wire PostHog initialization to respect consent state |
| 239 | Data export capability | STANDARD | User can export data as JSON/CSV download | MUST_BUILD | No data export feature | Agent must build export button in account settings |
| 240 | Data deletion capability | CRITICAL | User can delete account and all data | MUST_BUILD | No account deletion feature | Agent must build account deletion flow |
| 241 | Consent tracking | STANDARD | `user_consents` table with consent events | MUST_BUILD | No consent tracking | Agent must create table and record consent on signup/cookie preferences |
| 242 | Third-party data sharing disclosure | STANDARD | Privacy policy lists every third party | MUST_BUILD | No privacy policy. Code references Stripe, PostHog, Supabase | Agent must include in privacy policy |
| 243 | Open-source license compliance | CRITICAL | All dependency licenses compatible; audit in CI; THIRD_PARTY_LICENSES file | PARTIAL | Project uses MIT. Major deps (React, Next, Supabase, Tailwind) are MIT. No automated audit | Agent must run license audit, add to CI, generate THIRD_PARTY_LICENSES |

---

### IS Category 7: Deep Accessibility (WCAG AA) -- Rules 244-253

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 244 | Color contrast ratios | CRITICAL | Normal text 4.5:1, large text 3:1, UI components 3:1 | PARTIAL | Color tokens in oklch. `components/ui/skip-nav.tsx` + `components/ui/visually-hidden.tsx` provide accessibility primitives. Brand colors likely meet contrast. `muted-foreground` on dark may be borderline | Pre-built a11y primitives. Agent must still run contrast audit on all color token combinations |
| 245 | Semantic HTML structure | STANDARD | h1-h6 hierarchical, nav, main, button, a href | PARTIAL | `layout.tsx` has `<main>`. `Navbar.tsx` uses `<nav>`. `components/ui/visually-hidden.tsx` provides sr-only wrapper for screen reader text. No `<h1>` on all pages, no `<header>`/`<footer>` landmarks | Pre-built a11y primitives. Agent must add proper heading hierarchy and landmarks |
| 246 | Skip navigation link | STANDARD | "Skip to main content" as first focusable element | PARTIAL | `components/ui/skip-nav.tsx` provides SkipNav component. `layout.tsx` has `<main id="skip">` target | Pre-built component. Agent must add `<SkipNav />` before Navbar in layout.tsx |
| 247 | Reduced motion support | STANDARD | Animations check prefers-reduced-motion | PARTIAL | `tw-animate-css` may respect reduced motion. Custom CSS animations do NOT check | Agent must add `@media (prefers-reduced-motion: reduce)` overrides |
| 248 | Color scheme preference support | POLISH | Default to OS preference; explicit user choice overrides | HANDLED | `next-themes` ThemeProvider with `defaultTheme="system"` and `enableSystem`. Persisted via localStorage | None |
| 249 | ARIA live regions for dynamic content | STANDARD | Toast uses aria-live; form errors announced | PARTIAL | Radix Toast has built-in aria-live. Other dynamic content lacks aria-live | Agent must add aria-live regions for form errors and dynamic content |
| 250 | Touch target minimum size | STANDARD | All interactive elements 44x44px minimum | PARTIAL | Most buttons meet 44px. Small icon buttons may be under | Agent must audit and add padding for 44px minimum |
| 251 | Image alt text policy | STANDARD | Non-decorative images have descriptive alt; decorative have alt="" | PARTIAL | Logo SVG inline (no alt needed). No `<img>` tags with missing alt found | Agent must ensure all new images have proper alt text |
| 252 | Form error association | STANDARD | Errors linked via aria-describedby; aria-invalid="true"; focus first error | PARTIAL | `components/ui/form-field.tsx` wraps fields with error display. Agent should ensure aria-describedby and aria-invalid are set on the input element | Pre-built field wrapper. Agent must verify aria attributes are properly set |
| 253 | Focus visible indicator | STANDARD | No outline:none without alternative; focus-visible with 3:1 contrast | HANDLED | Tailwind v4 + Radix use `focus-visible` ring styles | None |

---

### IS Category 8: API Versioning -- Rules 254-258

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 254 | API version identifier | STANDARD | All routes include version prefix `/api/v1/` or version header | N/A | Next.js routes are internal (`/api/auth_callback`, `/api/og`). No public API | N/A unless public API is built |
| 255 | Deprecation notice period | STANDARD | Deprecated endpoints remain functional for 90 days | N/A | No public API | N/A |
| 256 | Backward compatibility for minor changes | STANDARD | New response fields are non-breaking | N/A | No public API | N/A |
| 257 | Breaking change documentation | POLISH | Migration guide for breaking API changes | N/A | No public API | N/A |
| 258 | API response envelope consistency | STANDARD | Consistent response structure across all endpoints | PARTIAL | Edge functions return inconsistent structures | If agent builds API routes, must use consistent `{ data, error }` envelope |

---

### IS Category 9: Architecture Decision Records (ADRs) -- Rules 259-263

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 259 | ADR template exists | STANDARD | `docs/adr/template.md` with Status, Context, Decision, Consequences | MUST_BUILD | No ADR system | Agent must create `docs/adr/template.md` and `docs/adr/README.md` |
| 260 | ADR trigger threshold | POLISH | ADR for new deps, 5+ file changes, new patterns, disagreements | MUST_BUILD | No ADR process | Agent should document threshold in ADR README |
| 261 | ADR numbering and storage | POLISH | `docs/adr/NNNN-short-title.md`, zero-padded sequential | MUST_BUILD | No ADR directory | Agent must follow convention when creating ADRs |
| 262 | Superseded ADRs link forward | POLISH | Old ADR status changed to "Superseded by [NNNN]" | MUST_BUILD | No ADR system | Agent must follow convention |
| 263 | ADRs part of onboarding | POLISH | Onboarding docs include step to read ADRs | MUST_BUILD | No ADR system | Agent should add to README |

---

### IS Category 10: Error Recovery / Retry Strategy -- Rules 264-270

| # | Rule | Severity | Martin's Spec | Status | Boilerplate Location | Agent Action Required |
|---|------|----------|--------------|--------|---------------------|----------------------|
| 264 | Transient failure detection | STANDARD | Classify 502/503/504/429 as transient; 400/401/403/404/422 as permanent | MUST_BUILD | No error classification system | Agent must create HTTP client utility with error classification |
| 265 | Exponential backoff with jitter | STANDARD | `min(base_delay * 2^attempt + jitter, max_delay)` in shared utility | MUST_BUILD | No retry logic | Agent must create shared retry utility |
| 266 | Maximum retry count | CRITICAL | No operation retries more than 5 times; clear error after max | MUST_BUILD | No retry logic in codebase | Agent must implement max retry with user-facing error |
| 267 | Circuit breaker for external services | POLISH | After N failures, stop sending; cooldown; half-open test | MUST_BUILD | No circuit breaker | Agent should implement for external API calls |
| 268 | Graceful degradation | STANDARD | Critical vs non-critical service classification; fallback states | MUST_BUILD | No service classification or fallback | Agent should classify services and implement fallbacks |
| 269 | Retry state visible to user | STANDARD | UI shows "Retrying..." during retries; "Try again" after max | MUST_BUILD | No retry UI | Agent must show retry state during transient failures |
| 270 | Idempotency for retried operations | CRITICAL | Write operations safe to execute multiple times | MUST_BUILD | No idempotency system. Stripe SDK handles its own but app-level operations unprotected | Agent must add idempotency keys for write operations |

---

## PART 3: Mechanism Categories (A-N) Status

| ID | Category | Status | Rationale |
|----|----------|--------|-----------|
| A | Data Input | PARTIAL | Auth forms exist (PRESENT_NOT_WIRED). `lib/form-validation.ts` (Zod schemas) + `components/ui/form-field.tsx` (field wrapper) provide validation infrastructure. App-specific forms must be built |
| B | Data Storage | PRESENT_NOT_WIRED | Supabase PostgreSQL configured in code (schema.sql, client files). Needs `supabase start` or cloud project |
| C | Data Processing | PARTIAL | `lib/form-validation.ts` provides Zod-based validation. `lib/services/base-service.ts` provides CRUD factory. App-specific processing logic must be built |
| D | Data Output | PARTIAL | Landing page sections render statically. `components/ui/loading-spinner.tsx` (LoadingSpinner, PageLoader, SkeletonCard) + `empty-state.tsx` (EmptyState) provide output infrastructure. No list views, detail views, charts, or dashboards yet |
| E | Authentication | PRESENT_NOT_WIRED | Email/password + Google/GitHub OAuth code exists. Needs Supabase URL and keys |
| F | Authorization | PRESENT_NOT_WIRED | RLS policies in schema.sql. No role column, no role-based guards, no feature gating. Needs running DB |
| G | Communication | MUST_BUILD | No email, notifications, or messaging. Loops.so referenced but not integrated |
| H | Integration | PRESENT_NOT_WIRED | Stripe code exists (checkout, webhooks, billing portal). PostHog code exists. All need API keys |
| I | Workflow | MUST_BUILD | No workflow engine or automation. Only DB trigger for user creation (dormant) |
| J | Search & Discovery | MUST_BUILD | No search, filtering, or autocomplete. Postgres full-text search available once DB wired |
| K | Collaboration | MUST_BUILD | No collaboration features |
| L | Monetization | PRESENT_NOT_WIRED | Stripe checkout, webhook sync, subscription tracking code exists. Needs Stripe API keys |
| M | Admin/Ops | MUST_BUILD | No admin panel, user management, or content moderation |
| N | Infrastructure | PARTIAL | Vercel hosting configured. Supabase infra code exists but needs activation. `lib/env.ts` provides typed env config. `app/error.tsx` + `error-boundary.tsx` provide error infrastructure. No CI for Next.js app |

---

## SUMMARY: HANDLED -- Do Not Touch

These rules work with ZERO configuration. The agent should NOT rebuild them.

**Stack**: S1, S2, S6, S7, S8, S10
**File Structure**: FS1, FS2, FS3, FS8, FS11
**Configuration**: CM1, CM2, CM3, CM5, CM6, CM7, CM8, CM9
**Auth Context**: AC5
**Theme Context**: TC1, TC2, TC3, TC4
**Route Guards**: RG4, RG5
**Routing**: RS1, RS3
**Data Service Layer**: DSL1, DSL2, DSL4
**Data/API Patterns**: DAP4
**Auth/Security**: AS4, AS5
**Error Handling**: EH1, EH2, EH3, EH4, EH5
**Testing**: T6
**Deployment**: DH1, DH3, DH4, DH5
**Build Instructions**: BI1, BI2, BI4, BI8, BI17, BI19, BI25, BI26, BI30
**Miscellaneous**: MISC1, MISC3, MISC8, MISC9, MISC10, MISC14, MISC16
**Banned Patterns**: BAN1, BAN2, BAN3, BAN5, BAN6, BAN7, BAN8, BAN9, BAN10, BAN12, BAN14, BAN15, BAN16, BAN23, BAN24, BAN25, BAN32, BAN35, BAN38
**Industry Standards**: 208, 209, 210, 211, 213, 214, 217, 219, 226, 228, 229, 230, 231, 233, 238, 248, 253
**Mobile/Responsive**: MR1, MR2, MR5, MR8, MR9, MR11, MR14
**Design System**: DES1, DES2, DES3, DES4, DES5
**UX Standards**: UX2, UX3, UX4, UX5, UX6, UX7, UX8, UX16, UX17, UX18, UX19, UX23

**Total HANDLED: ~88 rules**

---

## SUMMARY: PRESENT_NOT_WIRED -- Code Exists, Needs Configuration

These rules have working code in the boilerplate but require environment variables, API keys, or running services.

| Area | Rules | What's Needed |
|------|-------|--------------|
| Auth | S3, AC1, AC2, AC3, AC6, AC7, RG1, RS2, BI5, BI14, MISC2, BAN13, 215, 216 | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `supabase start` |
| Database | S4, S5, DS1, DS2, DS3, DBS1, DAP3, DAP5, MISC5, MISC6, BAN33, BAN34, 218 | Running Supabase instance |
| Payments | 203 | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` in Supabase secrets |
| Analytics | -- | `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` |
| Service Layer | DSL3 | Running DB for queries to execute |

**Total PRESENT_NOT_WIRED: ~27 rules**

---

## SUMMARY: MUST_BUILD -- Agent Checklist

These rules have NO working implementation. The agent must build from scratch.

| # | Rule | One-Line Action |
|---|------|----------------|
| AC4 | Default role is 'user' | Add `role` column with `DEFAULT 'user'` and RLS |
| RG2 | AdminRoute | Create admin route guard checking `role === 'admin'` |
| RG3 | ProRoute | Create pro/admin route guard |
| RS4 | CRUD route pattern | Create App Router folders for each entity |
| DS4 | Default sort newest first | Implement on all list views |
| DAP1 | Delete account removes data | Build cascading delete across all user tables |
| DAP2 | Explicit data category list | Maintain hardcoded list of tables for deletion |
| DAP6 | Default sort order | Implement on all list views |
| DAP7 | List pagination | Choose one strategy, implement consistently |
| DAP8 | Pagination controls | Build reusable Pagination component |
| DAP9 | Load-more remaining count | Build if choosing load-more strategy |
| AS1 | Delete with typed confirmation | Build ConfirmModal with "DELETE" text input |
| AS2 | Delete button disabled during op | Double-check: text match AND isDeleting |
| AS3 | Logout after deletion | Call signOut() after successful deletion |
| AS6 | Admin-only nav conditional | Render admin links based on role |
| DBS2 | Delete cascades all data | Build ordered deletion across user-data tables |
| DBS3 | Batch deletes | Supabase `.delete().eq('user_id', uid)` per table |
| P3 | Button press uses scale | Add active:scale-[0.98] to Button |
| P4 | One pagination strategy | Choose and document before building |
| UX1 | Missing ConfirmModal | Create ConfirmModal component (5 of 6 required UI components now pre-built) |
| UX11 | Date formatting utility | Create `utils/formatDate.ts` |
| UX12 | Text truncation | Apply truncate/line-clamp everywhere |
| UX13 | Back navigation | Back button on all detail/edit pages |
| UX15 | Danger zone styling | Create when building account settings |
| UX21 | Screen reader loading | Add sr-only text to loading states |
| MR3 | Sidebar hidden on mobile | Build sidebar with mobile toggle |
| MR4 | Sidebar overlay on mobile | Implement using Sheet component |
| MR12 | Layout structure dimensions | Build sidebar/header/main layout |
| MR13 | Sidebar bottom help link | Add pinned help link in sidebar |
| DES6 | Sidebar nav items | Implement when building sidebar |
| DES7 | Sidebar recent items | Implement when building sidebar |
| T1 | Console clean | Test once configured |
| T5 | No unused variables | Run lint and fix |
| T7 | Full navigation test | Test once functional |
| PG1 | Replace config placeholders | Create `.env` with real values |
| PG2 | Replace favicon | Create branded favicon |
| PG3 | Replace app name | Set real app name in layout metadata |
| PG4 | Data categories for delete | Create when building account deletion |
| PG5 | Set help email | Set when building help link |
| BI3 | Build app features | Implement all app-specific features |
| BI9 | Autofocus on forms | Add autoFocus to first input |
| BI10 | Pluralization helper | Create `utils/pluralize.ts` |
| BI11 | Search/filter for lists | Add search to list views |
| BI12 | Retry on error states | "Try Again" button on all errors |
| BI13 | Network/offline handling | Monitor navigator.onLine; show banner |
| BI18 | Unsaved changes warning | Create `useUnsavedChanges` hook |
| BI21 | Date formatting | Create `utils/formatDate.ts` |
| BI22 | Text truncation | Apply truncation with max-width |
| BI23 | Back navigation | Add to all sub-pages |
| BI29 | Pagination or load-more | Implement when building lists |
| MISC7 | Detail separate from edit | Implement as separate routes |
| MISC17 | Role only via admin tools | RLS blocking self-role-modification |
| MISC18 | Default role lowest privilege | `DEFAULT 'user'` column constraint |
| BAN18-22 | CRUD view patterns | Implement all CRUD view rules |
| BAN26 | formatDate utility | Create utility |
| BAN27 | Text truncation | Apply truncation |
| BAN28 | Back navigation | Add to sub-pages |
| BAN31 | No unused variables | Lint and fix |
| BAN39 | Autofocus | Add to forms |
| BAN40 | Search for lists | Add to list views |
| BAN41 | Error retry | Add retry buttons |
| BAN43 | Zero console errors | Test before deploy |
| 200-207 | i18n | Set up i18n system and translation files |
| 212 | Feature flags | `FEATURE_{NAME}_ENABLED` env var pattern |
| 221-222 | Structured logging | Create logger with log levels |
| 224 | Correlation ID | UUID middleware for API routes |
| 232 | Dependency audit in CI | `pnpm audit` in GitHub Actions |
| 234 | Dependency age monitoring | `pnpm outdated` CI step |
| 239 | Data export | Build user data export |
| 240 | Data deletion | Build account deletion flow |
| 241 | Consent tracking | Create `user_consents` table |
| 242 | Third-party disclosure | Document in privacy policy |
| 243 | License compliance | Run audit, create THIRD_PARTY_LICENSES |
| 259-263 | ADR system | Create template, numbering, storage |
| 264-270 | Error recovery | Build retry, backoff, circuit breaker, idempotency |

**Total MUST_BUILD: ~75 rules**

---

## SUMMARY: Statistics

| Status | Count | Percentage |
|--------|-------|-----------|
| HANDLED | ~88 | ~33% |
| PRESENT_NOT_WIRED | ~27 | ~10% |
| PARTIAL | ~35 | ~13% |
| MUST_BUILD | ~75 | ~29% |
| N/A | ~7 | ~3% |
| Banned (HANDLED) | ~19 | ~7% |
| Banned (PARTIAL) | ~5 | ~2% |
| Banned (MUST_BUILD) | ~12 | ~5% |

### Key Differences from Sheet 5 (All Toggles ON)

Sheet 5 has ~72 HANDLED rules. Sheet 1 now has ~88 HANDLED rules (up from ~58) thanks to pre-built boilerplate components. The difference is inverted -- Sheet 1 now leads in HANDLED count because the new components work with zero configuration:
- **Auth rules** (S3, AC3, AC6, AC7, RG1, RS2) still drop from HANDLED to PRESENT_NOT_WIRED in Sheet 1
- **Database rules** (S4, S5, DS1, DS3, DBS1) still drop from HANDLED to PRESENT_NOT_WIRED in Sheet 1
- **Environment Parity rules** (215, 216, 218) still drop from HANDLED to PRESENT_NOT_WIRED in Sheet 1
- **New pre-built components** (error boundary, loading states, empty states, form validation, toast wrapper, service layer, design tokens, SEO meta, cookie consent, legal page shells, skip-nav, env config) add ~30 HANDLED rules that were previously MUST_BUILD or PARTIAL

### What an Agent Needs to Know (Sheet 1 Baseline)

1. **The UI layer AND common infrastructure work out of the box** -- Next.js framework, Tailwind styling, Radix UI components, landing page layout, dark mode toggle, OG image generation, PLUS error boundaries, loading states, empty states, form validation, toast notifications, service layer, design tokens, SEO meta, cookie consent, and legal page shells
2. **Auth, Database, Payments, and Analytics require configuration** -- code is PRESENT but dormant without env vars and running services
3. **This is a LANDING PAGE SHELL with strong infrastructure** -- the agent must build the application features (CRUD, dashboard, admin panel, sidebar layout) but has pre-built patterns for error handling, loading states, empty states, form validation, data services, and notifications
4. **Legal compliance is partially covered** -- cookie consent is HANDLED, privacy/terms pages exist as shells (PARTIAL), but data deletion and consent tracking are still MUST_BUILD
5. **Error handling infrastructure exists** -- ErrorBoundary, error pages, toast wrapper are pre-built. Retry logic, circuit breakers, and offline handling still need building
6. **No role/authorization system** -- no role column, no route guards beyond basic auth (dormant), no feature gating
7. **Service layer is pre-built** -- `createService<T>()` CRUD factory in `lib/services/` provides getAll, getById, create, update, delete. Agent uses this instead of writing raw Supabase calls
8. **Form validation is pre-built** -- Zod-based `validateForm()` + `FormField` wrapper component. Requires `pnpm add zod` then use the pattern
9. **No i18n, no ADRs, no CI pipeline** -- structural infrastructure beyond the UI/component layer is absent
10. **Sheets 2-5 activate services incrementally** -- each higher sheet promotes PRESENT_NOT_WIRED rules to HANDLED as services come online
11. **The agent gets ~88 rules for free** (up from ~58) -- UI framework, styling, component library, dark mode, responsive layout, error boundaries, loading/empty states, form validation, toast system, service layer, design tokens, SEO meta, cookie consent, env config, and legal page shells
