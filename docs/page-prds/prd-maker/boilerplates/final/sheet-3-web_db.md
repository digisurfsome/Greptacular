# Exact Reality Sheet 3: web_db (Database ON, Auth/Payments Dormant)

> **Variant**: Database active -- Supabase PostgreSQL running and connected
> **Boilerplate**: DevToDollars Web-BoilerPlate-D2D (Next.js 16 + Supabase + Stripe + Tailwind v4 + PostHog)
> **What is active**: UI framework, styling, landing page, Supabase PostgreSQL (tables, RLS, queries, seed data)
> **What is dormant**: Auth (service running but not used by app), Payments (Stripe -- no keys), Analytics (PostHog -- no keys)
> **Use case**: Apps that need a database but handle auth differently or don't need auth yet. Internal tools, content apps, data-driven prototypes.
>
> This is a **DELTA document**. It inherits ALL statuses from Sheet 1 (web_base) and documents ONLY the rules
> whose status changes when `supabase start` activates the database layer. Every rule not listed below retains
> its Sheet 1 status exactly as documented in `sheet-1-web_base.md`.
>
> This document is part of the SINGLE SOURCE OF TRUTH system for what an AI coding agent gets for free from this
> boilerplate and what it must build from scratch. Read Sheet 1 first, then apply this delta.

---

## Boilerplate Identity

| Field | Value |
|-------|-------|
| **Base Sheet** | Sheet 1 (web_base) -- ALL statuses inherited |
| **Framework** | Next.js 16.1.6 (React 19, TypeScript, App Router) |
| **Styling** | Tailwind CSS v4.1.18 + tw-animate-css |
| **Component Library** | Radix UI primitives (dialog, accordion, avatar, toast, dropdown, navigation-menu, scroll-area, label) |
| **Icons** | Lucide React 0.562.0 + @icons-pack/react-simple-icons (GitHub, Google) |
| **Database** | Supabase PostgreSQL -- **ACTIVE via `supabase start`** |
| **Auth** | Supabase Auth -- **Service RUNNING (part of supabase start) but NOT USED by the app** |
| **Payments** | Stripe -- **DORMANT** (no keys configured) |
| **Analytics** | PostHog -- **DORMANT** (no keys configured) |
| **Hosting** | Vercel (configured via next.config.js) |
| **Package Manager** | pnpm (lockfile committed) |
| **Edge Functions** | Deno-based: `get_stripe_url`, `stripe_webhook`, `on_user_modify` -- **RUNNING but require Stripe keys** |

---

## What `supabase start` Activates

Running `supabase start` in the project directory spins up a local Supabase stack via Docker. Here is exactly what becomes available:

| Service | Port | Status in Sheet 3 | Notes |
|---------|------|-------------------|-------|
| **PostgreSQL** | 54322 | **ACTIVE** -- primary database engine | Same engine as production Supabase. Full SQL, RLS, triggers, functions. |
| **PostgREST** | 54321 | **ACTIVE** -- REST API layer over PostgreSQL | Automatically generates REST endpoints for all tables. RLS enforced on every request. |
| **Supabase Studio** | 54323 | **ACTIVE** -- admin GUI for DB management | Web UI for browsing tables, running SQL, inspecting RLS policies. Available at `http://localhost:54323`. |
| **Auth (GoTrue)** | 54321 | **RUNNING BUT DORMANT** | Starts automatically as part of the Supabase stack. Server is up and responding. The app does not use it in this variant -- no users created, no sign-in flows triggered. |
| **Realtime** | 54321 | **ACTIVE** -- WebSocket subscriptions available | `supabase_realtime` publication configured for products and prices tables. Frontend can subscribe via `supabase.channel()`. |
| **Storage** | 54321 | **RUNNING BUT DORMANT** | Object storage available but no buckets configured or used by the app. |
| **Edge Functions** | 54321 | **RUNNING BUT DORMANT** | Deno function runtime is up. Functions exist but require Stripe keys to do anything useful. |
| **Inbucket** | 54324 | **RUNNING BUT DORMANT** | Local email capture server. Would capture auth emails but no auth flows are triggered. |

**Key distinction**: Auth is a service that runs (you cannot disable it independently from `supabase start`), but no one is logging in, no sessions exist, and no auth tokens are being generated. RLS policies that reference `auth.uid()` will return NULL, meaning policies like `auth.uid() = id` match nothing -- effectively returning empty result sets for user-scoped tables. This is correct security behavior, not a bug.

---

## Database Tables (from schema.sql -- all ACTIVE)

| Table | Purpose | RLS | Queryable in Sheet 3? | Key Columns |
|-------|---------|-----|-----------------------|-------------|
| `users` | User profiles auto-created on signup | Owner-only (`auth.uid() = id` for select/update) | Returns empty -- no auth sessions exist | id (uuid), full_name, avatar_url, billing_address, payment_method |
| `customers` | Maps Supabase user ID to Stripe customer ID | Private (no policies) | Returns empty -- no permissive policies | id (uuid), stripe_customer_id |
| `products` | Stripe products synced via webhook | Public read-only | **YES -- returns seeded data** | id (text), active, name, description, image, metadata |
| `prices` | Stripe prices synced via webhook | Public read-only | **YES -- returns seeded data** | id (text), product_id, active, unit_amount, currency, type, interval |
| `subscriptions` | User subscriptions synced via webhook | Owner-only (`auth.uid() = user_id`) | Returns empty -- no auth sessions exist | id (text), user_id, status, price_id, quantity, created, current_period_start/end |
| `checkout_sessions` | Completed checkout records | Owner-only (`auth.uid() = user_id`) | Returns empty -- no auth sessions exist | id (text), user_id, mode, payment_status, status, price_id, quantity, created |

**Realtime**: Products and prices tables have realtime publication enabled.

**The Auth Paradox**: RLS is active but returns empty data for user-scoped queries. Public-read tables (products, prices) work normally. Owner-scoped tables (users, subscriptions, checkout_sessions) return zero rows because `auth.uid()` is NULL. Private tables (customers) return empty regardless. The database is useful for public/shared data, seed data, and schema validation -- not for per-user data flows without auth.

**Note**: The `users` table has NO `role` column. No `createdAt`/`updatedAt` columns on the users table (only `created` on subscriptions via `DEFAULT now()`). No `email` column on users (email lives in `auth.users` only).

---

## Boilerplate File Map

Same as Sheet 1 / Sheet 5. No files are added or removed by `supabase start`. The file map in Sheet 1 applies in full.

---

## Inheritance Declaration

**This sheet inherits ALL statuses from Sheet 1 (web_base).** The sections below document ONLY rules whose status changes. If a rule is not listed, its Sheet 1 status applies unchanged.

---

## PART 1: Martin's Structural Checklist -- Changed Rules Only

---

### Category: Stack (Mandatory) -- Rules S1-S10

**Unchanged from Sheet 1**: S1, S2, S3, S5, S6, S7, S8, S9, S10

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| S4 | Single database backend | STANDARD | All persistent data in a single configured database technology; do not mix multiple backends | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` (Supabase PostgreSQL), `nextjs/utils/supabase/queries.ts`, `nextjs/types_db.ts` | PostgreSQL is running via `supabase start`. Tables created from schema.sql via migrations. Queries execute against live DB. Single database backend is active and functional. Agent must not introduce a second database. |

---

### Category: File Structure -- Rules FS1-FS11

**All rules unchanged from Sheet 1.** Database activation does not change file structure statuses.

---

### Category: Configuration / Module System -- Rules CM1-CM10

**All rules unchanged from Sheet 1.** Database activation does not change configuration statuses.

---

### Category: Authentication Context -- Rules AC1-AC7

**Unchanged from Sheet 1**: AC1, AC2, AC4, AC6, AC7

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| AC3 | Profile created on first login | CRITICAL | On first auth where no DB profile exists, auto-create with default role and server timestamps | PRESENT_NOT_WIRED | PARTIAL | `nextjs/schema.sql` -- `handle_new_user()` trigger on `auth.users` insert | Trigger is DEPLOYED and ACTIVE in PostgreSQL. It will fire when a user signs up. However, no auth logins occur in this variant, so the trigger never fires. Mechanism is ready but untested. Agent does not need to build this -- it will activate automatically when auth is used. |
| AC5 | Service init order critical | CRITICAL | Backend service client initialized before dependent services | HANDLED | HANDLED | `nextjs/utils/supabase/client.ts`, `nextjs/utils/supabase/server.ts` | No functional change. Supabase SSR client creation pattern works regardless of which services are active. Supabase client now connects to a live local instance. |

---

### Category: Theme Context (Dark Mode) -- Rules TC1-TC4

**All rules unchanged from Sheet 1.** Database activation does not affect theme context.

---

### Category: Route Guards -- Rules RG1-RG5

**Unchanged from Sheet 1**: RG2, RG3, RG4, RG5

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| RG1 | ProtectedRoute for auth users | CRITICAL | Route guard checks auth state; redirects unauthenticated to login; spinner while loading | PRESENT_NOT_WIRED | PARTIAL | `nextjs/app/account/page.tsx` -- server-side auth check via `supabase.auth.getUser()` | Auth check now executes against the LIVE Supabase auth server (instead of failing to connect). It correctly identifies no active session and redirects to `/auth/signin`. The mechanism works per-page but is not DRY -- no reusable guard component exists. Agent must create reusable auth guard when building protected routes. |

---

### Category: Data Structure -- Rules DS1-DS4

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| DS1 | User data scoped to user | CRITICAL | All user-owned data scoped to authenticated user via RLS or user-specific paths | PRESENT_NOT_WIRED | PARTIAL | `nextjs/schema.sql` -- RLS policies on users (`auth.uid() = id`), subscriptions (`auth.uid() = user_id`), checkout_sessions (`auth.uid() = user_id`). Customers is private. | RLS policies are ACTIVE and ENFORCED in PostgreSQL. Without auth, `auth.uid()` returns NULL, so all user-scoped queries return empty result sets. The security mechanism works correctly -- it just blocks everything because no user identity exists. Public-read tables (products, prices) return data normally. Agent must maintain RLS on all new tables. |
| DS2 | Helper for user data access | STANDARD | Utility function that abstracts database path/query construction for user-scoped data | PRESENT_NOT_WIRED | PARTIAL | `nextjs/utils/supabase/queries.ts` -- getUser(), getSubscription(), getProducts(), getUserDetails() with React `cache()` wrapper | Query helpers now execute against a live database. `getProducts()` returns real seeded product data. `getUser()`, `getSubscription()`, `getUserDetails()` execute but return empty/null because they depend on auth session. No generic user-scoped query helper exists -- agent should create one or ensure all new queries follow the `queries.ts` pattern. RLS handles scoping automatically. |
| DS3 | Server timestamps on all writes | CRITICAL | Every record has createdAt/updatedAt using server-generated timestamps; never client-side dates | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` -- `DEFAULT timezone('utc'::text, now())` on timestamp columns. `handle_new_user()` trigger sets timestamps on user creation. | Server-side `DEFAULT now()` timestamps are ACTIVE in PostgreSQL. Any INSERT that omits a timestamp column gets the server-generated UTC timestamp automatically. This is database-level enforcement, independent of auth. **Caveat**: `users` table lacks explicit `created_at`/`updated_at` columns (only inherited from `auth.users`). Subscriptions and checkout_sessions have `created` with server default. Agent must add `created_at`/`updated_at` to `users` table and all new tables. |
| DS4 | Default sort newest first | POLISH | All list queries default to descending createdAt order | PRESENT_NOT_WIRED | HANDLED | `nextjs/utils/supabase/queries.ts` -- `getSubscription()` uses `.order('created', { ascending: false })`. `getProducts()` orders by `metadata->index`. | Sort queries execute against live database. ORDER BY clause works against real data. Pattern is established -- agent must maintain `order('created_at', { ascending: false })` for all new list queries. |

---

### Category: Data Service Layer -- Rules DSL1-DSL4

**Unchanged from Sheet 1**: DSL2, DSL4

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| DSL1 | No database calls in components | STANDARD | All DB operations through service layer; components never import DB client directly | PRESENT_NOT_WIRED | PARTIAL | `nextjs/utils/supabase/queries.ts` exists as query layer. BUT `Pricing.tsx` calls `supabase.from('products')` directly against the now-live DB | With the database active, the service layer violation in `Pricing.tsx` is now a REAL issue -- it executes direct Supabase calls against a live database, bypassing the `queries.ts` service layer. In Sheet 1 this was theoretical (no DB to query). Now it returns actual data. `AccountPage.tsx` also calls `supabase.functions.invoke()` directly. Agent must refactor: move all Supabase calls from components into `queries.ts` or a new `services/` module. |
| DSL3 | Realtime subscription pattern | STANDARD | Use DB's realtime subscription mechanism; return cleanup function | PRESENT_NOT_WIRED | PARTIAL | `nextjs/schema.sql` -- `supabase_realtime` publication for products and prices. Realtime service running via `supabase start` | Realtime service is ACTIVE. The publication is configured. Frontend can subscribe via `supabase.channel().on('postgres_changes', ...)`. No frontend subscription code exists yet -- DB-side infrastructure is fully operational, frontend implementation still needed. Agent must implement `useRealtimeSubscription` hook when features require live data updates. |

---

### Category: Routing Structure -- Rules RS1-RS4

**Unchanged from Sheet 1**: RS1, RS3, RS4

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| RS2 | Public vs protected routes | CRITICAL | Landing and login are public; dashboard, profile, CRUD pages are protected | PRESENT_NOT_WIRED | PARTIAL | `nextjs/app/page.tsx` (public landing), `nextjs/app/account/page.tsx` (checks auth server-side), `nextjs/app/auth/[id]/page.tsx` (public auth pages) | With database active, the account page's auth check actually executes against the live Supabase auth server. It correctly identifies no session and redirects to `/auth/signin`. The route protection mechanism WORKS, but only the server-side per-page pattern exists -- no middleware-level protection, no reusable guard. Agent must add route protection via Next.js middleware or shared layout for `app/(protected)/` route group. |

---

### Category: Data/API Patterns -- Rules DAP1-DAP9

**Unchanged from Sheet 1**: DAP1, DAP2, DAP4, DAP7, DAP8, DAP9

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| DAP3 | Realtime subscription pattern | STANDARD | Use DB's realtime subscription; map to normalized format; return cleanup function | PRESENT_NOT_WIRED | PARTIAL | `schema.sql` realtime publication active. Supabase Realtime service running. No frontend subscription code. | Same as DSL3 -- backend infrastructure is live, frontend implementation still needed. Agent must implement as needed per feature. |
| DAP5 | Records always include timestamps | CRITICAL | Every record has createdAt/updatedAt using server timestamps; never `new Date()` | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` -- `subscriptions.created`, `checkout_sessions.created` use `DEFAULT timezone('utc', now())`. PostgreSQL server generates timestamps on INSERT. | Server timestamps are ENFORCED at the database level. Active and functional. **Caveats**: (1) `users` table has NO `created_at` or `updated_at` columns, (2) no table has an `updated_at` column with auto-update trigger. Agent must add `created_at`/`updated_at` to `users` table, create an update trigger, and ensure all new tables include both timestamp columns with `DEFAULT now()`. |
| DAP6 | Default sort order | STANDARD | All lists default to descending createdAt (newest first) | PRESENT_NOT_WIRED | HANDLED | `queries.ts` -- `getSubscription()` sorts by `created` desc. Query executes against live DB. | Sort ordering works against real data. Agent must ensure all new list queries use `order('created_at', { ascending: false })` by default. |

---

### Category: Authentication/Security -- Rules AS1-AS7

**Unchanged from Sheet 1**: AS1, AS2, AS5, AS6

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| AS3 | No client-side role elevation | CRITICAL | No role system exists, so no risk of client-side elevation. RLS handles data access at DB level | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` -- RLS policies enforced at database level. No client-side data access can bypass server-side RLS. | RLS is now ACTIVE. Even if someone tried to access user data from the client, PostgreSQL would enforce the policies. Without auth, `auth.uid()` returns NULL, so no data is accessible -- the most restrictive possible state. Zero risk of elevation. |
| AS4 | Auth state listener | STANDARD | Supabase middleware calls `supabase.auth.getUser()` to refresh sessions | PRESENT_NOT_WIRED | PARTIAL | `nextjs/utils/supabase/middleware.ts` -- session refresh middleware. Auth server available at port 54321 via `supabase start`. | Middleware can now communicate with the auth server (it was unreachable in Sheet 1). It will find no active sessions and proceed without setting auth cookies. The mechanism works but does nothing useful without users. No client-side `onAuthStateChanged` listener exists. |
| AS7 | Protected data only accessible to owner | CRITICAL | RLS policies enforce `auth.uid() = id` on users, `auth.uid() = user_id` on subscriptions/checkout_sessions | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` -- RLS active and enforced | RLS policies are ACTIVE. Data protection is enforced at the database level. Without auth, the result is maximally restrictive: no user data is accessible to anyone. This is the correct security posture. |

---

### Category: Database/Storage -- Rules DBS1-DBS3

**Unchanged from Sheet 1**: DBS2, DBS3

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| DBS1 | User data scoped to owner | CRITICAL | All user-owned data scoped via user-specific paths or RLS policies | PRESENT_NOT_WIRED | HANDLED | `nextjs/schema.sql` -- RLS active on all tables with user data | RLS enforcement is LIVE. Data scoping works at the database level. Same caveat as DS1: without auth, user-scoped queries return empty sets. The SECURITY is handled; the DATA ACCESS requires auth. Agent must add RLS to all new tables containing user data. |

---

### Category: Error Handling -- Rules EH1-EH5

**All rules unchanged from Sheet 1.** Database activation does not change error handling statuses. EH3 (error feedback preserves form state) remains HANDLED. EH1, EH2, EH4 remain NOT_PRESENT. EH5 remains PARTIAL.

---

### Category: Performance -- Rules P1-P4

**All rules unchanged from Sheet 1.** Database activation does not change performance statuses.

---

### Category: UX Standards -- Rules UX1-UX23

**All rules unchanged from Sheet 1.** Database activation does not change UX statuses.

---

### Category: Mobile/Responsive -- Rules MR1-MR14

**All rules unchanged from Sheet 1.** Database activation does not change responsive design statuses.

---

### Category: Design System -- Rules DES1-DES7

**All rules unchanged from Sheet 1.** Database activation does not change design system statuses.

---

### Category: Testing -- Rules T1-T7

**All rules unchanged from Sheet 1.** Database activation does not change testing statuses.

---

### Category: Deployment/Hosting -- Rules DH1-DH5

**All rules unchanged from Sheet 1.** Database activation does not change deployment statuses.

---

### Category: Post-Generation Steps -- Rules PG1-PG5

**All rules unchanged from Sheet 1.** Database activation does not change post-generation steps.

---

### Category: Build Instructions -- Rules BI1-BI30

**All rules unchanged from Sheet 1.** Database activation does not change build instruction statuses.

---

### Category: Miscellaneous Rules -- Rules MISC1-MISC18

**Unchanged from Sheet 1**: MISC1, MISC2, MISC3, MISC4, MISC7, MISC8, MISC9, MISC10, MISC11, MISC12, MISC13, MISC14, MISC15, MISC16, MISC17, MISC18

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| MISC5 | Timestamps on all writes | CRITICAL | Every write includes createdAt/updatedAt with server timestamps | PRESENT_NOT_WIRED | HANDLED | `schema.sql` -- server-side `DEFAULT now()` active in PostgreSQL | Database defaults now FUNCTION. Writes to any table with timestamp defaults get server-generated timestamps. Same caveats as DS3: `users` table lacks explicit timestamp columns; no `updated_at` auto-trigger on any table. |
| MISC6 | User data scoped to owner | CRITICAL | All user data scoped via RLS | PRESENT_NOT_WIRED | HANDLED | `schema.sql` -- RLS active on all user-data tables | Same as DS1/DBS1. RLS enforced at database level. Agent must maintain for new tables. |

---

### Category: Banned Patterns -- Rules BAN1-BAN43

**Unchanged from Sheet 1**: BAN1-BAN11, BAN13-BAN32, BAN35-BAN43

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| BAN12 | No DB calls in components | STANDARD | Service layer only | HANDLED | PARTIAL | `Pricing.tsx` calls `supabase.from('products')` directly -- now executes against live DB and returns real product data | **DOWNGRADE.** In Sheet 1, this was HANDLED because no DB was running so the violation was theoretical. Now that the database is active, `Pricing.tsx` makes a real direct database call, bypassing the service layer. This is a live architectural violation. Agent must refactor to use `queries.ts`. |
| BAN33 | No writes without timestamps | CRITICAL | All DB writes include timestamps | HANDLED | HANDLED | `schema.sql` -- `DEFAULT now()` on timestamp columns | Server-side defaults handle this at the DB level. No change in status, but now these defaults are actively ENFORCED against real writes. Agent must ensure all new tables include timestamp columns with `DEFAULT now()`. |
| BAN34 | No unscoped user data | CRITICAL | RLS on all user data tables | HANDLED | HANDLED | `schema.sql` -- RLS enforced | RLS is active and enforced. No change in status, but now policies are actively executing against real queries. Agent must add RLS to all new tables. |

---

## PART 2: Industry Standards Supplement -- Changed Rules Only

---

### IS Category 1: Internationalization (i18n) -- Rules 200-207

**All rules unchanged from Sheet 1.** All NOT_PRESENT. Database activation does not affect i18n.

---

### IS Category 2: Config Externalization -- Rules 208-214

**Unchanged from Sheet 1**: 208, 210, 211, 212, 213, 214

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| 209 | Secrets never in source control | CRITICAL | No live secrets in repo; .env.example with placeholders; .gitignore blocks .env | PARTIAL | HANDLED | `.env.example` with placeholders. `.gitignore` blocks `.env`, `.env.local`. `supabase start` generates local keys automatically (displayed in terminal, not committed). | With `supabase start`, local Supabase keys are auto-generated and displayed in terminal output. Developer copies these to `.env.local` (gitignored). The PARTIAL in Sheet 1 was about the demo anon key in `.env.example` -- that is a public identifier, not a secret. With the local dev stack running, the actual service role key is generated dynamically and never committed. Secret management is correct. |

---

### IS Category 3: Environment Parity (Dev/Staging/Prod) -- Rules 215-220

**Unchanged from Sheet 1**: 217, 219

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| 215 | Same database technology across environments | CRITICAL | If prod uses PostgreSQL, dev uses PostgreSQL -- not SQLite | PRESENT_NOT_WIRED | HANDLED | `supabase start` runs local PostgreSQL 15 via Docker. Production Supabase uses PostgreSQL. Same engine, same version range. | **This is the single biggest upgrade in Sheet 3.** Dev environment now runs the same database engine as production. No SQLite substitution, no mocks, no file-based DB. Real PostgreSQL with real RLS, real triggers, real functions. Schema migrations, RLS policies, triggers, and functions all behave identically in dev and prod. Environment parity achieved for the database layer. |
| 216 | Same auth flow in all environments | CRITICAL | No mock auth in dev; same provider/flow as prod | PRESENT_NOT_WIRED | PARTIAL | Supabase Auth Emulator runs locally via `supabase start` with the same API contract as production GoTrue. Auth flows are not exercised in this variant. | Auth server is RUNNING and AVAILABLE. If the app were to use auth, it would use the same flow as production (same GoTrue API contract). Since auth is dormant in this variant, the "same flow" is verified at the infrastructure level but not tested at the application level. |
| 218 | Seed data strategy for development | STANDARD | Reproducible seed script; single command; consistent test data | PRESENT_NOT_WIRED | HANDLED | `supabase/seed.sql` runs automatically on `supabase db reset`. Also available via `pnpm supabase:reset`. | Seed data is now loadable into a running database. `supabase db reset` drops all tables, re-applies migrations from `supabase/migrations/`, and runs `seed.sql`. Reproducible, single-command, consistent test data. Agent must update `seed.sql` as new tables are added. |
| 220 | Reproducible dev environment setup | STANDARD | Single setup command for new developers | PARTIAL | PARTIAL | `pnpm install` + `supabase start` + `pnpm dev`. Three commands, well-documented in README. | Marginally improved: `supabase start` is a single command that brings up the entire local Supabase stack (PostgreSQL, Auth, Realtime, Studio, Storage, Edge Functions). Still requires multiple terminal commands for full setup but the database layer is now one step. Agent could create a `pnpm setup` script that chains all steps. |

---

### IS Category 4: Logging Strategy -- Rules 221-228

**Unchanged from Sheet 1**: 221, 222, 223, 224, 225, 227

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| 226 | Logs to stdout/stderr | STANDARD | App writes to stdout/stderr; environment handles routing | N/A | HANDLED | Next.js writes to stdout. Supabase services write to Docker container logs accessible via `supabase logs`. PostgreSQL query logs available via `supabase db logs`. | With Supabase running, database and service logs are available. All logging goes to stdout/stderr managed by Docker containers. `supabase logs` aggregates all service logs. Status changes from N/A to HANDLED because there are now server-side services producing logs. |
| 228 | Log retention and size limits | POLISH | Log rotation or managed log service; no unbounded buffers | N/A | HANDLED | Docker manages container log rotation for all Supabase services. PostgreSQL has built-in log rotation. No unbounded buffers. | With Supabase running via Docker, log retention is managed by Docker's log driver. Same as production where Supabase and Vercel manage retention. |

---

### IS Category 5: Dependency Management -- Rules 229-235

**Unchanged from Sheet 1**: 229, 230, 232, 233, 234, 235

| # | Rule | Severity | Martin's Spec | Sheet 1 Status | Sheet 3 Status | Boilerplate Location | What Changed |
|---|------|----------|--------------|----------------|----------------|---------------------|-------------|
| 231 | No floating version ranges | STANDARD | Production deps use exact or caret versions; never * or latest | PARTIAL | HANDLED | `package.json` uses caret (`^`) ranges for most deps with exact pins for critical ones (`@stripe/stripe-js: 4.0.0`, `lucide-react: 0.562.0`). `pnpm-lock.yaml` pins all resolved versions. | The PARTIAL in Sheet 1 was overly conservative. Caret ranges with a committed lockfile is the standard practice for pnpm projects. The lockfile ensures reproducible installs. No floating ranges, no `*`, no `latest`. This qualifies as HANDLED. |

---

### IS Category 6: Legal/Compliance -- Rules 236-243

**All rules unchanged from Sheet 1.** All NOT_PRESENT or PARTIAL. Database activation does not affect legal compliance. These pages and features must still be built from scratch.

---

### IS Category 7: Deep Accessibility (WCAG AA) -- Rules 244-253

**All rules unchanged from Sheet 1.** Database activation does not affect accessibility.

---

### IS Category 8: API Versioning -- Rules 254-258

**All rules unchanged from Sheet 1.** Database activation does not affect API versioning.

---

### IS Category 9: Architecture Decision Records (ADRs) -- Rules 259-263

**All rules unchanged from Sheet 1.** All NOT_PRESENT. Database activation does not affect ADRs.

---

### IS Category 10: Error Recovery / Retry Strategy -- Rules 264-270

**All rules unchanged from Sheet 1.** Database activation does not affect error recovery strategy.

---

## PART 3: Mechanism Categories (A-N) -- Changed Only

**Unchanged from Sheet 1**: A, C, E, G, I, J, K, L, M

| ID | Category | Sheet 1 Status | Sheet 3 Status | What Changed |
|----|----------|----------------|----------------|-------------|
| B | Data Storage | PRESENT_NOT_WIRED | HANDLED | PostgreSQL is running. Tables created from schema.sql via migrations. RLS active. Queries execute against real data. Seed data available via `supabase db reset`. Data storage is fully operational. |
| D | Data Output | PRESENT_NOT_WIRED | PARTIAL | Landing page components can now render real data from the database. `Pricing.tsx` queries products/prices tables and displays actual seeded product data. Other output patterns (list views, detail views, charts, dashboards) are still NOT_PRESENT -- those are app-specific and must be built. |
| F | Authorization | PRESENT_NOT_WIRED | PARTIAL | RLS policies are active and enforced at the database level. Data-level authorization works -- the database refuses unauthorized access. But role-based access control (admin/pro tiers, route guards, feature gating by subscription tier) still requires building a role system. RLS is the authorization floor; role-based UI gating is NOT_PRESENT. |
| H | Integration | PRESENT_NOT_WIRED | PARTIAL | Supabase integration is ACTIVE (DB queries work, realtime available, Studio accessible). Stripe integration still DORMANT (no API keys). PostHog still DORMANT (no keys). One of three integrations is functional. |
| N | Infrastructure | PRESENT_NOT_WIRED | PARTIAL | Supabase local infra is running: PostgreSQL, PostgREST, Realtime, Auth, Studio, Storage, Edge Functions, Inbucket. Vercel hosting still implied but not deployed. CI/CD for Next.js still not configured. GitHub Actions only runs Flutter web deploy. |

---

## SUMMARY: HANDLED Rules That Changed (Do Not Touch)

These rules flipped from PRESENT_NOT_WIRED to HANDLED in Sheet 3. They are now fully functional and the agent should NOT modify or rebuild them.

| # | Rule | Why It Is Now HANDLED |
|---|------|-----------------------|
| S4 | Single database backend | PostgreSQL running. Queries work. Single backend enforced. |
| DS3 | Server timestamps on writes | `DEFAULT now()` active in PostgreSQL. Server generates timestamps. |
| DS4 | Default sort newest first | `.order('created', { ascending: false })` works against live data. |
| DAP5 | Records include timestamps | Same as DS3. DB-level enforcement active. |
| DAP6 | Default sort order | Same as DS4. Sort queries execute. |
| AS3 | No client-side role elevation | RLS active. No client bypass possible. Most restrictive state. |
| AS7 | Protected data owner-only | RLS enforced. No unauthorized access. |
| DBS1 | User data scoped to owner | RLS active on all user-data tables. |
| MISC5 | Timestamps on all writes | DB defaults function. Server timestamps active. |
| MISC6 | User data scoped to owner | Same as DBS1. RLS enforced. |
| 209 | Secrets never in source control | Local keys auto-generated, gitignored. No secrets committed. |
| 215 | Same DB technology across envs | Local PostgreSQL matches production Supabase PostgreSQL. |
| 218 | Seed data strategy | `supabase db reset` runs migrations + seed.sql. Reproducible. |
| 226 | Logs to stdout/stderr | Docker manages service logs. `supabase logs` aggregates. |
| 228 | Log retention | Docker log driver handles rotation. |
| 231 | No floating version ranges | Lockfile pins all versions. Standard pnpm practice. |

**Total newly HANDLED in Sheet 3: 16 rules**

---

## SUMMARY: Rules That Downgraded

| # | Rule | Sheet 1 | Sheet 3 | Why |
|---|------|---------|---------|-----|
| BAN12 | No DB calls in components | HANDLED | PARTIAL | `Pricing.tsx` service layer violation is now a LIVE issue against a real database, not a theoretical one |

**Total downgrades: 1 rule**

---

## SUMMARY: Delta Statistics

### Aggregate Status Counts

| Status | Sheet 1 Count | Sheet 3 Count | Delta |
|--------|---------------|---------------|-------|
| HANDLED | 41 | 56 | +15 |
| PRESENT_NOT_WIRED | 40 | 15 | -25 |
| PARTIAL | 23 | 34 | +11 |
| NOT_PRESENT | 65 | 65 | 0 |
| N/A | 7 | 6 | -1 |

**Net effect**: 25 rules moved out of PRESENT_NOT_WIRED. Of those, 16 became HANDLED (fully resolved by database activation) and 10 became PARTIAL (DB-side works, but need auth or frontend code for full implementation). 1 rule moved from N/A to HANDLED (logging). 1 rule downgraded from HANDLED to PARTIAL (service layer violation now real).

### Status Distribution by Severity (Sheet 3)

| Severity | HANDLED | PARTIAL | NOT_PRESENT | PRESENT_NOT_WIRED | N/A |
|----------|---------|---------|-------------|-------------------|-----|
| CRITICAL | 18 | 8 | 15 | 4 | 0 |
| STANDARD | 28 | 18 | 35 | 8 | 4 |
| POLISH | 10 | 8 | 15 | 3 | 2 |

### What the Agent Gets for Free in Sheet 3 (vs Sheet 1)

1. **Working PostgreSQL database** with all tables, columns, constraints, indexes, and triggers
2. **Active RLS enforcement** at the database level (maximally restrictive without auth)
3. **Server-generated timestamps** on all writes (`DEFAULT now()` active)
4. **Seed data** loadable via `supabase db reset` -- reproducible test data
5. **Realtime infrastructure** ready for subscription-based features
6. **Environment parity** -- same PostgreSQL engine locally as in production
7. **Supabase Studio** for visual database administration at `http://localhost:54323`
8. **Working query helpers** in `queries.ts` that execute against real data
9. **Product/pricing data** visible on the landing page from seeded database
10. **Database migrations** that apply cleanly and can be extended

### Critical Items Still Missing (Same as Sheet 1 -- Database Does Not Fix These)

1. **Role system** (AC1, AC4, RG2, RG3, MISC17, MISC18) -- no `role` column on users table
2. **Account deletion** (DAP1, DSL4, AS1-AS3, DBS2, DBS3) -- no deletion flow
3. **Error boundary** (DH3, BI6) -- unhandled errors show blank white screen
4. **404 page** (RS3, UX23, BI19) -- no `not-found.tsx`
5. **i18n** (200-207) -- all strings hardcoded in English
6. **Legal compliance** (236-243) -- no privacy policy, terms, cookie consent, data deletion
7. **Logging** (221-225, 227) -- no structured logging, no error reporting
8. **CRUD patterns** (RS4, DAP4, DAP7-DAP9, UX5-UX7, DSL2) -- no list/detail/create/edit views
9. **Env var validation** (214) -- app crashes with cryptic error if vars missing
10. **Error recovery** (264-270) -- no retry logic, no circuit breaker, no graceful degradation
11. **Dependency audit in CI** (232) -- no CI for Next.js app
12. **ADRs** (259-263) -- no architecture decision records

---

## What an Agent Needs to Know

1. **Run `supabase start` first** -- this starts the entire local Supabase stack (PostgreSQL, Auth, Realtime, Studio, Storage, Edge Functions, Inbucket)
2. **Database is live** -- queries execute, tables exist, RLS is enforced, timestamps work, seed data available
3. **Auth is running but idle** -- The GoTrue server is up (part of `supabase start`) but no users exist, no sessions, no sign-in flows triggered. Auth-dependent code exists but is not exercised
4. **Stripe is fully dormant** -- no API keys configured. Edge functions `get_stripe_url` and `stripe_webhook` will fail. Stripe tables (products, prices) are populated from seed data, not from Stripe webhooks
5. **PostHog is fully dormant** -- no keys configured. `PHProvider` wraps the app but does nothing
6. **RLS returns empty for user tables** -- this is CORRECT behavior without auth. `auth.uid()` is NULL, so owner-only policies match nothing. Public tables (products, prices) return data normally
7. **Seed data is your friend** -- `supabase db reset` drops everything, re-applies migrations, runs seed.sql. Use it to get a clean starting point
8. **Supabase Studio at `http://localhost:54323`** -- use it to inspect tables, run SQL, verify RLS policies, manually insert test data for development
9. **Service layer violation is real** -- `Pricing.tsx` calling `supabase.from()` directly now executes against a live database. Agent should refactor to use `queries.ts`
10. **To add new tables**: create a migration in `supabase/migrations/`, run `supabase db reset`, regenerate types with `pnpm supabase:generate-types`
11. **All MUST_BUILD items from Sheet 1 still apply** -- database activation does not create new code, only activates existing code
12. **To work with user-specific data**, the developer must either: (a) advance to Sheet 4 by configuring auth, (b) insert test data directly via Supabase Studio / SQL, or (c) use the service role key (bypasses RLS) in server-side code during development
13. **Environment parity is the biggest win** -- same PostgreSQL version, same RLS, same triggers, same functions in dev and production. "Works on my machine" bugs related to database behavior are eliminated
