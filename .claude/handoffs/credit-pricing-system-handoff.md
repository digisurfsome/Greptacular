# Credit-Based Pricing & Billing System for AutoForge

## Status: Ready to Implement

## Overview

AutoForge is transitioning from a free developer tool to a premium SaaS product with credit-based billing. The pricing strategy is deliberately high-end -- this is NOT a $9/month mass-market tool. The goal is a barrier to entry that ensures only serious builders use the platform, while maximizing revenue per build.

**Core business decisions:**
- $219/build minimum for a single-platform web app
- Credit-based system, not unlimited subscription
- Premium add-ons (QA pipeline, knowledge base, security audit) sold separately
- No flat monthly fee that enables unlimited builds (prevents agency arbitrage)
- Bulk credit bundles for power users with many ideas
- Dual pricing model: "we provide the AI" (full price) and "bring your own key" (platform fee only)

**Why credits instead of subscriptions:**
- Each build costs real money in AI compute ($50-250 in API calls)
- Unlimited subscriptions would hemorrhage money on heavy users
- Credits create a clear value exchange: 1 credit = 1 complete app
- Bulk discounts reward commitment without creating unlimited risk
- Credits never expire, building trust and reducing purchase anxiety

---

## Feature 1: Credit System Core

### Credit Types

| Credit Type | What It Does | Price |
|---|---|---|
| Standard Build (Web) | 1 full app build, web only, standard testing | $219 |
| Standard Build (Dual) | 1 full app build, web + mobile, standard testing | $299 |
| Pro Build (Web) | Web build + full QA pipeline + review agent | $399 |
| Pro Build (Dual) | Dual build + full QA pipeline + review agent | $599 |
| Enterprise Build | Full pipeline + security audit + performance report + docs | $799 |
| Knowledge Base Add-on | Auto-generated docs + tutorial scripts for 1 project | $79 |
| Security Audit Add-on | Dedicated security audit agent for 1 project | $49 |
| Performance Report Add-on | Performance profiling agent for 1 project | $49 |
| Maintenance Credit | 1 month auto-update maintenance for 1 project | $19/mo |

### Credit Bundles (Bulk Discount)

| Bundle | Credits | Discount | Price |
|---|---|---|---|
| 5-Pack Standard Web | 5 Standard Build (Web) | 10% | $985 (vs $1,095) |
| 10-Pack Standard Web | 10 Standard Build (Web) | 15% | $1,861 (vs $2,190) |
| 5-Pack Pro Dual | 5 Pro Build (Dual) | 10% | $2,695 (vs $2,995) |
| Agency Pack | 25 Standard Build (Web) | 20% | $4,380 (vs $5,475) |
| Enterprise Annual | 12 Enterprise Builds + all add-ons | 25% | $7,192 (vs $9,588+) |

### Credit Lifecycle

```
1. User purchases credits via Stripe Checkout
2. Stripe webhook fires → credits added to account balance
3. User starts a build → system checks credit balance
4. Credit consumed immediately when build starts (not on completion)
5. Build runs through the agent pipeline
6. If SYSTEM error (crash, infra failure) → automatic refund
7. If BAD SPEC (agent can't complete) → no refund
8. If partial completion (some features done) → no refund
```

**Key rules:**
- Credits never expire (critical for user trust and reducing purchase anxiety)
- Credits are non-transferable (prevents a secondary resale market)
- Credits are tied to a specific build type (no mixing Standard credits for Pro builds)
- Refunds are automatic for system errors, manual review for all other cases

### Database Schema (Supabase)

```sql
-- User credit balance
-- Each column tracks the count of that credit type the user owns.
-- This is a materialized balance -- the source of truth is credit_transactions,
-- but this table is the fast-read cache for gating build starts.
create table credit_balances (
  user_id uuid primary key references auth.users,
  standard_web integer default 0 check (standard_web >= 0),
  standard_dual integer default 0 check (standard_dual >= 0),
  pro_web integer default 0 check (pro_web >= 0),
  pro_dual integer default 0 check (pro_dual >= 0),
  enterprise integer default 0 check (enterprise >= 0),
  knowledge_base integer default 0 check (knowledge_base >= 0),
  security_audit integer default 0 check (security_audit >= 0),
  performance_report integer default 0 check (performance_report >= 0),
  maintenance_months integer default 0 check (maintenance_months >= 0),
  updated_at timestamptz default now()
);

-- Enable RLS: users can only read their own balance
alter table credit_balances enable row level security;
create policy "Users read own balance"
  on credit_balances for select using (auth.uid() = user_id);

-- Transaction history (immutable audit log)
-- This is the source of truth. credit_balances is derived from this.
create table credit_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users,
  type text not null check (type in ('purchase', 'consume', 'refund', 'bonus', 'grant')),
  credit_type text not null,
  quantity integer not null,
  stripe_payment_id text,
  stripe_checkout_session_id text,
  project_id uuid,
  build_id uuid,
  description text,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Index for fast user transaction history lookups
create index idx_credit_transactions_user on credit_transactions(user_id, created_at desc);
create index idx_credit_transactions_stripe on credit_transactions(stripe_payment_id);

-- Enable RLS: users can only read their own transactions
alter table credit_transactions enable row level security;
create policy "Users read own transactions"
  on credit_transactions for select using (auth.uid() = user_id);

-- Stripe subscription tracking
create table subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users,
  stripe_subscription_id text unique not null,
  stripe_customer_id text not null,
  plan text not null check (plan in (
    'starter_annual', 'pro_annual', 'agency_annual', 'maintenance_monthly'
  )),
  status text not null check (status in (
    'active', 'canceled', 'past_due', 'trialing', 'incomplete'
  )),
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index idx_subscriptions_user on subscriptions(user_id);
create index idx_subscriptions_stripe on subscriptions(stripe_subscription_id);

alter table subscriptions enable row level security;
create policy "Users read own subscriptions"
  on subscriptions for select using (auth.uid() = user_id);
```

### Credit Balance Update Logic

When credits are purchased or consumed, both the `credit_transactions` table AND `credit_balances` table must be updated atomically. Use a Supabase Edge Function or Postgres function to ensure consistency:

```sql
-- Atomic credit consumption (called when a build starts)
create or replace function consume_credit(
  p_user_id uuid,
  p_credit_type text,
  p_project_id uuid,
  p_build_id uuid
) returns boolean as $$
declare
  v_balance integer;
begin
  -- Lock the row to prevent race conditions
  execute format(
    'select %I from credit_balances where user_id = $1 for update',
    p_credit_type
  ) into v_balance using p_user_id;

  if v_balance is null or v_balance < 1 then
    return false;
  end if;

  -- Deduct the credit
  execute format(
    'update credit_balances set %I = %I - 1, updated_at = now() where user_id = $1',
    p_credit_type, p_credit_type
  ) using p_user_id;

  -- Log the transaction
  insert into credit_transactions (user_id, type, credit_type, quantity, project_id, build_id, description)
  values (p_user_id, 'consume', p_credit_type, -1, p_project_id, p_build_id,
          'Credit consumed for build');

  return true;
end;
$$ language plpgsql security definer;
```

---

## Feature 2: Annual Platform Subscriptions

For users who want ongoing access to the AutoForge platform (not just per-build credits).

### Platform Tiers

| Tier | Annual Price | What's Included |
|---|---|---|
| Starter | $999/yr | Platform access + 3 Standard Web credits + style picker + 1 boilerplate |
| Pro | $2,499/yr | Platform access + 5 Pro Dual credits + all styles + all boilerplates + priority queue |
| Agency | $4,999/yr | Platform access + 15 Pro Dual credits + all add-ons + white-label option + API access |

### What "Platform Access" Includes

- Access to the AutoForge web interface (hosted instance)
- Project management dashboard
- Style picker and live preview
- Boilerplate selection
- Build history and metrics
- Support tier: email (Starter), priority (Pro), dedicated Slack channel (Agency)

### What Platform Access Does NOT Include (Requires Credits)

- Actual app builds (each build consumes a credit)
- Add-on agents (knowledge base, security audit, performance report)
- Maintenance subscriptions (monthly per-project charge)
- Additional credits beyond the ones included in the tier

### Why Annual Only (No Monthly)

- **Prevents churn gaming.** A monthly plan lets someone sign up, burn through 10 builds, and cancel. Annual commitment filters for serious users.
- **Higher upfront commitment.** Users who pay $999+ upfront are invested in the platform and more likely to succeed.
- **Better cash flow.** Annual payments provide predictable revenue for infrastructure planning.
- **The included credits make it a deal.** Starter includes $657 worth of credits for $999/yr -- the platform access is effectively $342/yr, which is reasonable.

### Subscription Credit Grant Logic

When an annual subscription is created or renewed:

```
Starter renewal → grant 3 standard_web credits
Pro renewal     → grant 5 pro_dual credits
Agency renewal  → grant 15 pro_dual credits + 5 knowledge_base + 5 security_audit + 5 performance_report
```

These credits are granted via a `credit_transactions` entry with type `grant` and the subscription ID in metadata. They are added to `credit_balances` atomically.

---

## Feature 3: BYOK (Bring Your Own Key) Model

For power users who already have an Anthropic API key or Max subscription and want to reduce per-build cost.

### How It Works

1. User navigates to Settings and enters their Anthropic API key
2. AutoForge validates the key (makes a small test API call)
3. Key is encrypted and stored in Supabase (never logged, never exposed in UI after entry)
4. When starting a build, user chooses "Use my API key" or "Use AutoForge AI"
5. If BYOK: AutoForge charges a reduced platform fee (no AI compute cost to us)
6. If managed: AutoForge charges the full credit price (we pay for AI compute)

### BYOK Pricing

| Build Type | Full Price (We Provide AI) | BYOK Price (You Provide AI) | Our Margin (BYOK) |
|---|---|---|---|
| Standard Web | $219 | $49 | $49 (100% margin, zero AI cost) |
| Standard Dual | $299 | $79 | $79 |
| Pro Web | $399 | $99 | $99 |
| Pro Dual | $599 | $149 | $149 |
| Enterprise | $799 | $199 | $199 |

### Why This Works for Everyone

**For power users:**
- Users on Max plan ($200/mo) can build multiple apps per month at $49-199 each
- Developers who already have API credits save 75-80% per build
- Attracts the Anthropic power-user community who are already invested in the ecosystem

**For AutoForge:**
- Pure platform margin with zero AI cost risk
- $49-199 per build is still significant revenue
- Expands the addressable market (people who would never pay $219 might pay $49)
- Users who start with BYOK may upgrade to managed when they realize the convenience

### Implementation Details

**API key storage:**
- Key encrypted at rest using Supabase Vault (or AES-256 with a server-side secret)
- Key never returned to the frontend after initial entry (only a masked preview like `sk-ant-...****`)
- Key deleted immediately when user removes it from settings

**API key validation:**
- On entry, make a minimal API call (e.g., `messages.create` with a tiny prompt)
- Check that the key has sufficient permissions
- Display the associated account/org name if available

**Build-time key selection:**
- `client.py` already supports configurable API keys via environment variables
- When BYOK is active, the build process injects the user's key instead of the system key
- The key is passed via environment variable to the subprocess, never written to disk

**Stripe integration:**
- Separate Stripe Price IDs for BYOK vs managed builds
- The checkout flow detects whether the user has a valid BYOK key configured
- If BYOK key is present, show the reduced pricing automatically

### Database Addition

```sql
-- BYOK API key storage (encrypted)
create table user_api_keys (
  user_id uuid primary key references auth.users,
  encrypted_key bytea not null,
  key_preview text not null,           -- "sk-ant-...7f3a" (last 4 chars)
  provider text default 'anthropic',
  validated_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table user_api_keys enable row level security;
create policy "Users manage own keys"
  on user_api_keys for all using (auth.uid() = user_id);
```

---

## Feature 4: Usage Metering & Rate Limiting

### Per-Build Usage Metering

Track actual AI usage per build for margin analysis and future pricing optimization.

```sql
create table build_usage (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  user_id uuid not null references auth.users,
  build_id uuid not null,
  credit_type text not null,
  is_byok boolean default false,

  -- AI usage metrics
  total_input_tokens bigint default 0,
  total_output_tokens bigint default 0,
  total_turns integer default 0,
  total_agent_sessions integer default 0,
  cache_read_tokens bigint default 0,
  cache_write_tokens bigint default 0,

  -- Feature tracking
  features_total integer default 0,
  features_completed integer default 0,
  features_failed integer default 0,

  -- Timing
  build_start timestamptz not null,
  build_end timestamptz,
  build_duration_minutes integer,

  -- Cost tracking (internal, not shown to users)
  estimated_ai_cost_cents integer default 0,
  credit_value_cents integer not null,
  margin_cents integer default 0,

  -- Status
  status text check (status in ('running', 'completed', 'failed', 'refunded')),

  created_at timestamptz default now()
);

create index idx_build_usage_user on build_usage(user_id, created_at desc);
create index idx_build_usage_project on build_usage(project_id);

alter table build_usage enable row level security;
create policy "Users read own usage"
  on build_usage for select using (auth.uid() = user_id);
```

### Rate Limiting

Rate limits prevent abuse and ensure fair resource allocation across the platform.

**Managed users (AutoForge provides AI):**

| Limit | Starter | Pro | Agency |
|---|---|---|---|
| Max concurrent builds | 1 | 2 | 5 |
| Max builds per day | 3 | 10 | 30 |
| Max builds per month | 15 | 50 | unlimited |

**BYOK users (user provides AI):**

| Limit | Starter | Pro | Agency |
|---|---|---|---|
| Max concurrent builds | 2 | 5 | 10 |
| Max builds per day | 5 | 15 | unlimited |
| Max builds per month | 30 | 100 | unlimited |

BYOK users get higher limits because they are not consuming our AI compute resources. The limits exist purely to prevent platform infrastructure abuse.

### Build Queue System

When the system is at capacity (all agent slots occupied), builds are queued:

```
Priority order: Agency > Pro > Starter
Within same tier: FIFO (first in, first out)
```

**Queue UX:**
- "Your build is #3 in queue, estimated start: ~5 minutes"
- Real-time position updates via WebSocket
- User can cancel a queued build and get their credit back instantly
- If a build stays queued for more than 30 minutes, alert the admin

### Rate Limit Database Table

```sql
create table rate_limits (
  user_id uuid primary key references auth.users,
  tier text not null check (tier in ('starter', 'pro', 'agency')),
  concurrent_builds integer default 0,
  builds_today integer default 0,
  builds_this_month integer default 0,
  last_build_started_at timestamptz,
  today_reset_at date default current_date,
  month_reset_at date default date_trunc('month', current_date),
  updated_at timestamptz default now()
);
```

---

## Feature 5: Stripe Integration

### Stripe Products to Create

| Product | Type | Stripe Object |
|---|---|---|
| Individual credits (9 types) | One-time | `Price` (one-time) |
| Credit bundles (5 bundles) | One-time | `Price` (one-time) with metadata |
| BYOK credits (5 types) | One-time | `Price` (one-time) with `byok: true` metadata |
| Annual platform subscriptions (3 tiers) | Recurring | `Subscription` (annual) |
| Maintenance subscription | Recurring | `Subscription` (monthly, per-project) |

### Webhook Events to Handle

| Event | Action |
|---|---|
| `checkout.session.completed` | Add credits to balance (for one-time purchases) |
| `invoice.paid` | Renew subscription + grant monthly/annual credits |
| `invoice.payment_failed` | Mark subscription `past_due`, send notification email |
| `customer.subscription.updated` | Update subscription status (upgrade/downgrade) |
| `customer.subscription.deleted` | Revoke platform access (in-progress builds continue to completion) |
| `charge.refunded` | Deduct credits if unused, log refund transaction |
| `charge.dispute.created` | Flag account, pause builds, alert admin |

### Stripe Checkout Flow

```
1. User clicks "Buy Credits" or "Subscribe" in AutoForge UI
2. Frontend calls POST /api/billing/create-checkout with:
   - credit_type or subscription_plan
   - quantity (for credits)
   - is_byok (boolean)
3. Backend creates a Stripe Checkout Session:
   - Sets success_url and cancel_url
   - Attaches user_id and credit_type as metadata
   - Applies bundle discounts via Stripe Coupons or pre-calculated Prices
4. Frontend redirects to Stripe Checkout (hosted, PCI-compliant)
5. User completes payment on Stripe's page
6. Stripe fires checkout.session.completed webhook
7. Webhook handler:
   a. Validates webhook signature (STRIPE_WEBHOOK_SECRET)
   b. Extracts metadata (user_id, credit_type, quantity)
   c. Calls add_credits() to update balance + log transaction
   d. Returns 200 to Stripe
8. User redirected back to AutoForge success page
9. Frontend polls or receives WebSocket update showing new credit balance
```

### Supabase Edge Functions

**`create-checkout` Edge Function:**

```typescript
// POST /functions/v1/create-checkout
// Body: { credit_type: string, quantity: number, is_byok: boolean }
// OR: { plan: 'starter_annual' | 'pro_annual' | 'agency_annual' }

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import Stripe from 'https://esm.sh/stripe@14.0.0'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!)

serve(async (req) => {
  const { credit_type, quantity, plan, is_byok } = await req.json()
  const user = await getAuthenticatedUser(req) // Supabase JWT validation

  // Map credit_type to Stripe Price ID
  const priceId = getPriceId(credit_type, is_byok, plan)

  const session = await stripe.checkout.sessions.create({
    customer_email: user.email,
    line_items: [{ price: priceId, quantity: quantity || 1 }],
    mode: plan ? 'subscription' : 'payment',
    success_url: `${Deno.env.get('APP_URL')}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${Deno.env.get('APP_URL')}/billing/cancel`,
    metadata: {
      user_id: user.id,
      credit_type: credit_type || plan,
      quantity: String(quantity || 1),
      is_byok: String(is_byok || false),
    },
  })

  return new Response(JSON.stringify({ url: session.url }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

**`stripe-webhook` Edge Function:**

```typescript
// POST /functions/v1/stripe-webhook
// Stripe sends events here. Verify signature, process event.

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import Stripe from 'https://esm.sh/stripe@14.0.0'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY')!)
const endpointSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')!

serve(async (req) => {
  const body = await req.text()
  const sig = req.headers.get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, endpointSecret)
  } catch (err) {
    return new Response('Invalid signature', { status: 400 })
  }

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')! // Service role for admin writes
  )

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session
      const { user_id, credit_type, quantity } = session.metadata!
      await addCredits(supabase, user_id, credit_type, parseInt(quantity), session.payment_intent as string)
      break
    }
    case 'invoice.paid': {
      const invoice = event.data.object as Stripe.Invoice
      const subscription = await stripe.subscriptions.retrieve(invoice.subscription as string)
      await renewSubscription(supabase, subscription)
      break
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice
      await markSubscriptionPastDue(supabase, invoice.subscription as string)
      break
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription
      await cancelSubscription(supabase, sub.id)
      break
    }
  }

  return new Response('OK', { status: 200 })
})
```

---

## Feature 6: Build Gating

The mechanism that checks credit balance before allowing a build to start.

### Build Start Flow

```
User clicks "Start Build" in AutoForge UI
  │
  ├─ Is user authenticated?
  │   └─ No → redirect to login
  │
  ├─ Does user have an active platform subscription?
  │   └─ No → show "Subscribe to AutoForge" page
  │
  ├─ What build type is selected?
  │   └─ Determine credit_type from project config (web/dual, standard/pro/enterprise)
  │
  ├─ Does user have sufficient credits for this build type?
  │   ├─ No → show "Purchase Credits" modal with:
  │   │       - Current balance
  │   │       - Required credit type
  │   │       - One-click purchase button (→ Stripe Checkout)
  │   │       - Bundle options for bulk discount
  │   └─ Yes → proceed
  │
  ├─ Is user within rate limits?
  │   ├─ No → show "Rate limit reached. Upgrade to Pro/Agency for higher limits."
  │   └─ Yes → proceed
  │
  ├─ Is build queue at capacity?
  │   ├─ Yes → add to queue, show position and ETA
  │   └─ No → proceed
  │
  └─ Consume credit (atomic operation)
      ├─ Deduct from credit_balances
      ├─ Log to credit_transactions
      ├─ Create build_usage entry (status: running)
      └─ Start the agent pipeline
```

### Refund Policy

| Scenario | Refund? | How |
|---|---|---|
| System crash / infrastructure error | Yes, automatic | Webhook or health check detects failure, triggers `refund_credit()` |
| Bad spec (agent fails to complete) | No | User's spec was insufficient; they can retry with better spec |
| Partial completion (some features built) | No | Partial work was delivered |
| User cancels mid-build | No | Work was already started; AI tokens consumed |
| Build queued and user cancels before start | Yes, automatic | No work was done; credit returned instantly |
| Duplicate charge (Stripe error) | Yes, manual | Support reviews and processes via Stripe dashboard |

### Grace Period

When a credit is consumed, the user has **48 hours** to start the actual build (click "Run Agent"). If the build is not started within 48 hours, the credit is automatically returned to their balance. This prevents accidental credit consumption from exploratory clicking.

Implementation: A Supabase cron job runs hourly, checks for `credit_transactions` with type `consume` that have no matching `build_usage` entry and are older than 48 hours, then issues an automatic refund.

---

## Feature 7: Admin Dashboard (Owner Only)

### Metrics to Display

**Revenue:**
- Total revenue: daily, weekly, monthly, all-time
- Revenue by credit type (which builds sell most)
- Revenue by purchase type (individual vs bundle vs subscription)
- MRR (Monthly Recurring Revenue) from subscriptions
- ARR (Annual Recurring Revenue) projection

**Credits:**
- Credits sold vs credits consumed (velocity)
- Outstanding credit balance across all users (liability)
- Average time from purchase to consumption
- Credits consumed by build type breakdown

**Margin Analysis:**
- Average AI cost per build type (from `build_usage.estimated_ai_cost_cents`)
- Average margin per build type
- BYOK vs managed build ratio
- BYOK margin (should be ~100% since no AI cost)

**Users:**
- Total registered users
- Active users (built something in last 30 days)
- Top 10 users by credit consumption
- Top 10 users by revenue
- Conversion rate: free trial → first purchase
- BYOK adoption rate

**Platform Health:**
- Active builds right now
- Queue depth and average wait time
- Build success rate (completed vs failed vs refunded)
- Average build duration by type
- Refund rate (should be under 5%)

### Implementation

For initial launch, use Supabase Studio (free, built-in) to run admin queries directly. The admin dashboard UI is a nice-to-have for later.

When building the admin UI:
- New route: `/admin` (hidden, requires admin role)
- Admin role check: `auth.users.raw_app_meta_data->>'role' = 'admin'`
- RLS policy: admin users can read all tables
- Charts: use a lightweight charting library (e.g., Recharts, already common in React)

---

## Cost Analysis

### Per-Build AI Cost Estimates (Managed Builds)

| Build Type | Features | Agent Sessions | Est. AI Cost | Credit Price | Margin | Margin % |
|---|---|---|---|---|---|---|
| Standard Web | ~100 | 30-50 | $50-80 | $219 | $139-169 | 63-77% |
| Standard Dual | ~150 | 45-75 | $80-120 | $299 | $179-219 | 60-73% |
| Pro Web | ~100 + QA + review | 50-70 | $70-110 | $399 | $289-329 | 72-82% |
| Pro Dual | ~150 + QA + review | 70-100 | $120-180 | $599 | $419-479 | 70-80% |
| Enterprise | everything | 90-130 | $150-250 | $799 | $549-649 | 69-81% |

**Notes:**
- Estimates assume Opus 4.6 API pricing at current rates
- When running on the owner's Max subscription ($200/mo), AI cost is fixed -- every managed build at Max effectively has 100% margin minus the monthly subscription
- BYOK builds have 100% margin (zero AI cost to us)
- Margins improve as the model gets cheaper over time (API prices trend downward)

### Revenue Projections

**Conservative (10 paying users in month 1):**
- 10 users x 2 builds/month x $219 average = $4,380/mo
- + 3 annual subscriptions x $999/12 = $250/mo
- Total: ~$4,630/mo

**Growth (50 paying users by month 6):**
- 50 users x 3 builds/month x $300 average = $45,000/mo
- + 20 subscriptions (mixed tiers) = $4,000/mo
- Total: ~$49,000/mo

**Scale (200 paying users by month 12):**
- 200 users x 3 builds/month x $350 average = $210,000/mo
- + 100 subscriptions = $20,000/mo
- Total: ~$230,000/mo

---

## Implementation Priority

### Phase 1: MVP Billing (Week 1-2)
**Goal:** Users can buy credits and credits are required to start builds.

1. Set up Stripe account with products and prices
2. Create Supabase tables: `credit_balances`, `credit_transactions`
3. Implement `create-checkout` Edge Function
4. Implement `stripe-webhook` Edge Function
5. Add credit balance display in the AutoForge UI header
6. Add "Purchase Credits" button and modal
7. Add build gating: check balance before starting agent

### Phase 2: Build Gating + Refunds (Week 3)
**Goal:** Robust credit consumption with automatic refunds for system errors.

1. Implement `consume_credit()` Postgres function
2. Add credit consumption to the build start flow
3. Implement automatic refund on system crash detection
4. Add 48-hour grace period cron job
5. Add transaction history page in UI

### Phase 3: BYOK Support (Week 4)
**Goal:** Power users can use their own API keys at reduced pricing.

1. Add API key input to settings UI
2. Implement key validation endpoint
3. Implement encrypted key storage (Supabase Vault)
4. Modify `client.py` to support user-provided keys
5. Add BYOK pricing to Stripe and checkout flow

### Phase 4: Annual Subscriptions (Week 5-6)
**Goal:** Recurring revenue with tiered platform access.

1. Create Stripe subscription products
2. Implement subscription webhook handling
3. Add subscription management UI (subscribe, cancel, upgrade)
4. Implement annual credit grants on renewal
5. Add platform access gating (subscription required to access UI)

### Phase 5: Usage Metering (Week 7)
**Goal:** Track actual AI costs per build for margin analysis.

1. Create `build_usage` table
2. Instrument the agent pipeline to track tokens, turns, sessions
3. Calculate and store estimated AI cost per build
4. Add margin tracking to admin queries

### Phase 6: Rate Limiting + Queue (Week 8)
**Goal:** Prevent abuse and manage capacity.

1. Create `rate_limits` table
2. Implement concurrent build limits
3. Implement daily/monthly build limits
4. Add build queue with priority ordering
5. Add queue position UI (WebSocket updates)

### Phase 7: Admin Dashboard (Week 9-10)
**Goal:** Business intelligence for the owner.

1. Create admin route with role-based access
2. Revenue dashboard (daily/weekly/monthly)
3. Credit velocity charts
4. Margin analysis per build type
5. User analytics (top users, conversion, churn)

---

## File Changes Summary

| File | Change |
|---|---|
| **Supabase** | |
| `supabase/migrations/001_credit_system.sql` | NEW -- `credit_balances`, `credit_transactions`, `subscriptions` tables + RLS |
| `supabase/migrations/002_build_usage.sql` | NEW -- `build_usage`, `rate_limits`, `user_api_keys` tables |
| `supabase/migrations/003_credit_functions.sql` | NEW -- `consume_credit()`, `refund_credit()`, `add_credits()` Postgres functions |
| `supabase/functions/create-checkout/index.ts` | NEW -- Stripe Checkout session creation |
| `supabase/functions/stripe-webhook/index.ts` | NEW -- Stripe event handler |
| `supabase/functions/cron-grace-period/index.ts` | NEW -- 48-hour grace period refund job |
| **Backend** | |
| `server/routers/billing.py` | NEW -- REST endpoints: `GET /api/billing/balance`, `POST /api/billing/checkout`, `GET /api/billing/transactions`, `POST /api/billing/consume` |
| `server/services/billing_service.py` | NEW -- Credit logic: balance checks, consumption, refunds, rate limiting |
| `server/services/byok_service.py` | NEW -- BYOK key validation, storage, retrieval |
| `server/routers/admin.py` | NEW -- Admin-only endpoints for revenue/usage metrics |
| `server/routers/settings.py` | MODIFY -- Add BYOK API key configuration endpoints |
| `client.py` | MODIFY -- Support BYOK API key passthrough to agent subprocess |
| `parallel_orchestrator.py` | MODIFY -- Add credit check before build start, write `build_usage` on completion |
| `agent.py` | MODIFY -- Track token usage and session counts for metering |
| **Frontend** | |
| `ui/src/components/PricingPage.tsx` | NEW -- Plan comparison grid with purchase CTAs |
| `ui/src/components/CreditBalance.tsx` | NEW -- Header component showing current credit counts |
| `ui/src/components/PurchaseModal.tsx` | NEW -- Credit purchase flow (select type + quantity, redirect to Stripe) |
| `ui/src/components/TransactionHistory.tsx` | NEW -- Paginated table of credit transactions |
| `ui/src/components/BYOKSettings.tsx` | NEW -- API key input with validation and masked preview |
| `ui/src/components/AdminDashboard.tsx` | NEW -- Revenue, margin, and user analytics (admin only) |
| `ui/src/components/BuildQueue.tsx` | NEW -- Queue position display with real-time updates |
| `ui/src/lib/billing-api.ts` | NEW -- API client functions for billing endpoints |
| `ui/src/lib/types.ts` | MODIFY -- Add billing-related TypeScript types |
| `ui/src/hooks/useBilling.ts` | NEW -- React Query hooks for billing data |
| `ui/src/App.tsx` | MODIFY -- Add billing routes, credit balance to header |

---

## Environment Variables

```bash
# Stripe (required for billing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (created in Stripe Dashboard)
STRIPE_PRICE_STANDARD_WEB=price_...
STRIPE_PRICE_STANDARD_DUAL=price_...
STRIPE_PRICE_PRO_WEB=price_...
STRIPE_PRICE_PRO_DUAL=price_...
STRIPE_PRICE_ENTERPRISE=price_...
STRIPE_PRICE_KNOWLEDGE_BASE=price_...
STRIPE_PRICE_SECURITY_AUDIT=price_...
STRIPE_PRICE_PERFORMANCE_REPORT=price_...
STRIPE_PRICE_MAINTENANCE=price_...

# BYOK variants (reduced pricing)
STRIPE_PRICE_BYOK_STANDARD_WEB=price_...
STRIPE_PRICE_BYOK_STANDARD_DUAL=price_...
STRIPE_PRICE_BYOK_PRO_WEB=price_...
STRIPE_PRICE_BYOK_PRO_DUAL=price_...
STRIPE_PRICE_BYOK_ENTERPRISE=price_...

# Subscriptions
STRIPE_PRICE_STARTER_ANNUAL=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_AGENCY_ANNUAL=price_...

# Bundles
STRIPE_PRICE_BUNDLE_5_STANDARD=price_...
STRIPE_PRICE_BUNDLE_10_STANDARD=price_...
STRIPE_PRICE_BUNDLE_5_PRO_DUAL=price_...
STRIPE_PRICE_BUNDLE_AGENCY=price_...
STRIPE_PRICE_BUNDLE_ENTERPRISE_ANNUAL=price_...

# Supabase (for billing backend)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# BYOK encryption
BYOK_ENCRYPTION_KEY=... # 256-bit key for encrypting stored API keys
```

---

## Security Considerations

1. **Stripe webhook signature verification** is mandatory. Never process a webhook without validating `stripe-signature` against `STRIPE_WEBHOOK_SECRET`.

2. **Credit balance updates** must be atomic. Use Postgres transactions (the `consume_credit()` function uses `FOR UPDATE` row locking) to prevent race conditions where two concurrent builds consume the same credit.

3. **BYOK API keys** must be encrypted at rest. Never store plaintext keys. Never log keys. Never return full keys to the frontend.

4. **Admin endpoints** must check the user's role. Use Supabase RLS with an admin role check, not just a frontend route guard.

5. **Rate limit checks** must happen server-side. Never trust the frontend to enforce rate limits.

6. **Stripe Price IDs** should be stored as environment variables, not hardcoded. This allows switching between test and live mode without code changes.

7. **Idempotency** in webhook handlers: Stripe may send the same event multiple times. Use `stripe_payment_id` or `stripe_checkout_session_id` as an idempotency key to prevent duplicate credit grants.

---

## Open Questions

1. **Free trial?** Should new users get 1 free Standard Web credit to try the platform? This reduces friction but costs $50-80 in AI compute per trial user. Could gate it behind email verification + credit card on file.

2. **Referral program?** "Give a friend 1 free credit, get 1 free credit when they purchase." Low cost ($50-80 per referral) with high potential upside.

3. **Credit upgrades?** If a user has a Standard Web credit but wants to do a Pro build, can they pay the difference ($180) to upgrade the credit? Or must they buy a new Pro credit?

4. **Team/org accounts?** Should credits be shareable within a team? This adds complexity (team management, permission roles) but is expected for Agency tier.

5. **Maintenance auto-renewal?** Should Maintenance Credits auto-renew monthly via Stripe Subscription, or should users manually re-purchase each month? Auto-renewal is better for revenue but may feel aggressive.
