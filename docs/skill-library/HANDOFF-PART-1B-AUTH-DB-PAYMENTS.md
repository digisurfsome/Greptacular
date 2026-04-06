# Skill Generation Handoff — Part 1B: Auth, Database, Payments (Skills 14-23)

> Run `npx ctx7 skills generate`, paste the prompt, save output to the listed path.
> See Part 1A for setup instructions.

---

## AUTH

### 14. supabase-auth
- **Save to:** `skills/auth/supabase-auth.md`
- **Library:** Supabase Auth + @supabase/ssr | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Supabase Auth with SSR patterns including: @supabase/ssr package for server-side auth, PKCE flow for secure authentication, createServerClient for server components and route handlers, createBrowserClient for client components, middleware.ts for cookie refresh and session management, protected route patterns, social OAuth providers (Google, GitHub, etc.), email/password signup and login, magic link authentication, password reset flow, and auth state change listeners.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- Auth package? → "@supabase/ssr, not the old @supabase/auth-helpers"
- Session strategy? → "PKCE flow with cookie-based sessions"

**Must include these patterns:**
- `createServerClient(url, key, { cookies })` for server
- `createBrowserClient(url, key)` for client components
- Middleware cookie refresh with `supabase.auth.getUser()`
- `supabase.auth.signInWithOAuth({ provider: 'google' })`
- `supabase.auth.signUp({ email, password })` and `signInWithPassword`

---

### 15. clerk-auth
- **Save to:** `skills/auth/clerk-auth.md`
- **Library:** Clerk | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Clerk authentication patterns including: ClerkProvider wrapper setup, pre-built SignIn and SignUp components, clerkMiddleware() for route protection, auth() helper for server-side user access, currentUser() for full user data, useUser() and useAuth() client hooks, organization management with useOrganization, user metadata (publicMetadata, privateMetadata), webhook handling for user sync, and custom sign-in/sign-up pages.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- Components? → "Pre-built Clerk components and custom UI"
- Webhooks? → "Include webhook setup for database sync"

**Must include these patterns:**
- `clerkMiddleware()` in middleware.ts with `createRouteMatcher`
- `auth()` in server components/route handlers
- `currentUser()` for full user profile server-side
- `useUser()` and `useAuth()` in client components
- Webhook handler for `user.created` / `user.updated` events

---

### 16. auth-js
- **Save to:** `skills/auth/auth-js.md`
- **Library:** Auth.js v5 / NextAuth | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Auth.js v5 (NextAuth) patterns including: auth.ts configuration with providers array, Google/GitHub/Credentials provider setup, callbacks (signIn, session, jwt) for customization, session strategy (JWT vs database sessions), database adapters (Prisma, Drizzle, Supabase), middleware.ts for route protection with auth export, getServerSession and auth() for server-side access, useSession() client hook, and custom sign-in/sign-out pages.

**When the wizard asks:**
- Version? → "Auth.js v5, not NextAuth v4"
- Session? → "JWT strategy by default"
- Database? → "Adapter-agnostic, show Prisma and Drizzle examples"

**Must include these patterns:**
- `auth.ts` with `NextAuth({ providers, callbacks })` config
- `export { auth as middleware }` in middleware.ts
- `auth()` function for server-side session access
- `signIn()` and `signOut()` server actions
- JWT callback for adding custom claims to token

---

### 17. firebase-auth
- **Save to:** `skills/auth/firebase-auth.md`
- **Library:** Firebase Auth | **Boilerplate:** mobile, universal

**Paste this prompt into ctx7:**
> Firebase Authentication patterns including: client SDK signInWithEmailAndPassword and createUserWithEmailAndPassword, OAuth providers with signInWithPopup and signInWithRedirect (Google, Apple, GitHub), onAuthStateChanged listener for auth state, getIdToken for JWT access, Admin SDK verifyIdToken for server-side verification, session cookies for SSR, custom claims for role-based access, phone auth with RecaptchaVerifier, and password reset with sendPasswordResetEmail.

**When the wizard asks:**
- Platform? → "Web and Flutter"
- Server verification? → "Admin SDK for server-side token verification"
- SSR? → "Session cookies for server-side rendering"

**Must include these patterns:**
- `signInWithEmailAndPassword(auth, email, password)` client-side
- `signInWithPopup(auth, new GoogleAuthProvider())` OAuth
- `onAuthStateChanged(auth, (user) => { })` state listener
- `admin.auth().verifyIdToken(token)` server verification
- `admin.auth().setCustomUserClaims(uid, { role: 'admin' })` custom claims

---

## DATABASE / ORM

### 18. supabase-database
- **Save to:** `skills/database/supabase-database.md`
- **Library:** Supabase JS Client (PostgreSQL) | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Supabase database patterns including: JavaScript client queries with from().select().eq().single(), insert/update/upsert/delete operations, Row Level Security (RLS) policies using auth.uid() and auth.jwt(), database functions (plpgsql), triggers for automated actions, foreign key joins with select('*, table(*)'), filter methods (.eq, .in, .like, .gte, .lte, .order, .limit, .range), real-time subscriptions on table changes, and type generation with supabase gen types typescript.

**When the wizard asks:**
- Client? → "JavaScript/TypeScript @supabase/supabase-js"
- Security? → "RLS policies are critical, include detailed patterns"
- Types? → "Generated TypeScript types with CLI"

**Must include these patterns:**
- `supabase.from('table').select('*').eq('id', id).single()`
- `supabase.from('table').insert({ ... }).select()` with return
- RLS: `CREATE POLICY ... USING (auth.uid() = user_id)`
- Foreign key joins: `.select('*, profiles(*), comments(*)')`
- `supabase gen types typescript --local > types_db.ts`

---

### 19. drizzle-orm
- **Save to:** `skills/database/drizzle-orm.md`
- **Library:** Drizzle ORM | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Drizzle ORM patterns including: schema definition with pgTable/mysqlTable/sqliteTable, column types (text, integer, boolean, timestamp, uuid), drizzle-kit for migrations (generate, migrate, push), query builder with db.select().from().where(), insert/update/delete operations, relations with one-to-many and many-to-many, prepared statements for performance, PostgreSQL/MySQL/SQLite dialect differences, and integration with connection pools (postgres-js, @planetscale/database, better-sqlite3).

**When the wizard asks:**
- Database? → "PostgreSQL primary, show all dialects"
- Migration tool? → "drizzle-kit with generate and migrate"
- Connection? → "postgres-js for PostgreSQL"

**Must include these patterns:**
- `pgTable('users', { id: uuid('id').primaryKey(), ... })` schema
- `drizzle-kit generate` and `drizzle-kit migrate` commands
- `db.select().from(users).where(eq(users.id, id))`
- `db.insert(users).values({ ... }).returning()`
- Relations: `relations(users, ({ many }) => ({ posts: many(posts) }))`

---

### 20. prisma
- **Save to:** `skills/database/prisma.md`
- **Library:** Prisma | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Prisma ORM patterns including: schema.prisma model definitions with field types and relations, prisma migrate dev for development migrations, prisma db push for rapid prototyping, client queries with findMany/findUnique/create/update/delete, nested writes and includes, select and include for field selection, middleware for logging and soft deletes, seeding with prisma db seed, transaction API, and raw SQL with prisma.$queryRaw.

**When the wizard asks:**
- Database? → "PostgreSQL primary"
- Client generation? → "prisma generate after schema changes"
- TypeScript? → "Full type safety from schema"

**Must include these patterns:**
- `model User { id String @id @default(cuid()) ... }` schema
- `prisma migrate dev --name init` for migrations
- `prisma.user.findMany({ where: {}, include: { posts: true } })`
- `prisma.user.create({ data: { ... } })` with nested creates
- `prisma.$transaction([...])` for atomic operations

---

### 21. convex
- **Save to:** `skills/database/convex.md`
- **Library:** Convex | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Convex patterns including: defineSchema with table definitions and validators, query functions with ctx.db.query() for reads, mutation functions with ctx.db.insert/patch/delete for writes, action functions for external API calls, Zod-like validators (v.string(), v.number(), v.object()), React hooks useQuery and useMutation for client integration, scheduled functions for background jobs, file storage with ctx.storage, and auth integration with Clerk or Auth0.

**When the wizard asks:**
- Framework? → "React with Next.js"
- Auth? → "Clerk integration"
- Real-time? → "Yes, Convex is real-time by default"

**Must include these patterns:**
- `defineSchema({ users: defineTable({ name: v.string() }) })`
- `query({ handler: async (ctx) => { return await ctx.db.query('users').collect() } })`
- `mutation({ args: { name: v.string() }, handler: async (ctx, args) => { await ctx.db.insert('users', args) } })`
- `useQuery(api.users.list)` and `useMutation(api.users.create)` hooks
- `action` for external API calls (non-deterministic operations)

---

## PAYMENTS

### 22. stripe-payments
- **Save to:** `skills/payments/stripe-payments.md`
- **Library:** Stripe | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Stripe integration patterns including: Checkout Sessions with stripe.checkout.sessions.create for one-time and subscription payments, Customer Portal for self-service billing management, webhook signature verification with stripe.webhooks.constructEvent, subscription lifecycle events (customer.subscription.created/updated/deleted), client-side with loadStripe and Elements (PaymentElement, AddressElement), pricing models (flat rate, per-seat, metered/usage-based), usage record reporting for metered billing, and customer creation and management.

**When the wizard asks:**
- Integration type? → "Checkout Sessions for payments, not custom forms"
- Webhooks? → "Critical — include signature verification"
- Subscriptions? → "Yes, full subscription lifecycle"

**Must include these patterns:**
- `stripe.checkout.sessions.create({ mode: 'subscription', ... })`
- `stripe.webhooks.constructEvent(body, sig, endpointSecret)` verification
- Webhook handlers for `checkout.session.completed`, `customer.subscription.*`
- `loadStripe(publishableKey)` and `<Elements>` client-side
- Customer Portal: `stripe.billingPortal.sessions.create({ customer })`

---

### 23. lemonsqueezy
- **Save to:** `skills/payments/lemonsqueezy.md`
- **Library:** LemonSqueezy | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> LemonSqueezy payment integration patterns including: checkout overlay with lemon.js script and LemonSqueezy.Url.Open(), webhook payload verification with X-Signature header and HMAC, subscription management (create, update, cancel, resume), license key validation for software licensing, API client with @lemonsqueezy/lemonsqueezy.js, variant and product management, customer portal URL generation, and discount code creation.

**When the wizard asks:**
- Integration style? → "Checkout overlay, not hosted page"
- Webhooks? → "Include signature verification with HMAC"
- Use case? → "SaaS subscriptions and digital product licensing"

**Must include these patterns:**
- `LemonSqueezy.Url.Open(checkoutUrl)` overlay checkout
- HMAC webhook verification with `X-Signature` header
- `getSubscription(id)` and `updateSubscription(id, { ... })`
- `validateLicense(licenseKey, instanceId)` for software licensing
- API setup: `lemonSqueezySetup({ apiKey, onError })`
