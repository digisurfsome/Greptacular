# Boilerplate Analysis: Web-BoilerPlate-D2D

> **Source:** `github.com/digisurfsome/Web-BoilerPlate-D2D`
> **Stack:** Next.js + TypeScript + Supabase + Stripe + PostHog + Loops.so + Netlify
> **Purpose:** Pre-built foundation for SaaS web applications

---

## What's Already Built

### Authentication (Supabase Auth)
- Email/password signup + login
- OAuth providers (Google, GitHub) via Supabase Auth
- Protected route middleware
- Session management with Supabase client
- Password reset flow
- Email verification

### Database (Supabase / PostgreSQL)
- Supabase client configuration
- Row Level Security (RLS) policies
- User profiles table with metadata
- Migration scripts

### Payments (Stripe)
- Stripe Checkout integration
- Subscription management (create, cancel, update)
- Webhook handler for payment events
- Price/product sync from Stripe dashboard
- Customer portal redirect
- Billing page with plan selection

### Analytics (PostHog)
- PostHog client initialization
- Page view tracking
- Custom event tracking helpers
- Feature flags integration

### Email (Loops.so)
- Transactional email sending
- Contact sync (user signup triggers)
- Email template management via Loops dashboard

### Deployment (Netlify)
- `netlify.toml` configuration
- Build settings for Next.js
- Environment variable setup
- Preview deployments on PR

---

## File Structure

```
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   └── reset-password/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx        # Protected layout with sidebar
│   │   ├── page.tsx          # Dashboard home
│   │   ├── billing/page.tsx  # Stripe subscription management
│   │   └── settings/page.tsx # User settings
│   ├── api/
│   │   ├── webhooks/stripe/route.ts
│   │   ├── auth/callback/route.ts
│   │   └── checkout/route.ts
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Landing page
├── components/
│   ├── ui/                   # Reusable UI primitives
│   ├── auth/                 # Login/signup forms
│   ├── billing/              # Pricing cards, plan selector
│   └── layout/               # Navbar, sidebar, footer
├── lib/
│   ├── supabase/
│   │   ├── client.ts         # Browser Supabase client
│   │   ├── server.ts         # Server Supabase client
│   │   └── middleware.ts     # Auth middleware
│   ├── stripe/
│   │   ├── client.ts         # Stripe instance
│   │   ├── config.ts         # Price IDs, plan definitions
│   │   └── helpers.ts        # Checkout, portal helpers
│   ├── posthog/
│   │   └── client.ts         # PostHog initialization
│   └── loops/
│       └── client.ts         # Loops.so API client
├── supabase/
│   ├── migrations/           # SQL migration files
│   └── config.toml           # Supabase project config
├── public/
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── netlify.toml
```

---

## Database Schema (Supabase)

### `profiles` table
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | References auth.users(id) |
| email | text | Synced from auth |
| full_name | text | |
| avatar_url | text | |
| stripe_customer_id | text | Created on first checkout |
| subscription_status | text | active, canceled, past_due |
| subscription_id | text | Stripe subscription ID |
| plan | text | free, pro, enterprise |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### RLS Policies
- Users can only read/update their own profile
- Service role can read all profiles (for webhooks)

---

## API Endpoints Already Built

| Method | Path | What |
|--------|------|------|
| POST | /api/checkout | Creates Stripe Checkout session |
| POST | /api/webhooks/stripe | Handles Stripe webhook events |
| GET | /api/auth/callback | Supabase OAuth callback handler |

---

## Auth Flow

1. User visits `/signup` -> fills email/password form
2. Supabase creates user + sends verification email
3. User clicks verification link -> redirected to `/api/auth/callback`
4. Callback exchanges code for session -> redirects to `/dashboard`
5. Middleware checks session on every protected route request
6. No session -> redirect to `/login`

---

## What Needs Connecting (for dual builds)

When merging with the Flutter mobile app:
1. **Shared Supabase project** — both apps use the same database, same auth
2. **Stripe webhooks** — mobile purchases go through RevenueCat but still need Supabase profile updates
3. **PostHog** — separate project IDs for web vs mobile, but same user identity
4. **API layer** — if mobile needs custom endpoints, add them to the Next.js API routes
5. **Real-time subscriptions** — Supabase Realtime works for both web and mobile clients

---

## Environment Variables Required

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
NEXT_PUBLIC_POSTHOG_KEY=
NEXT_PUBLIC_POSTHOG_HOST=
LOOPS_API_KEY=
```
