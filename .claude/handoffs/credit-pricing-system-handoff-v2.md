# Credit-Based Pricing & Billing System for AutoForge (v2 — Boilerplate-Aware)

## Status: Ready to Implement

## IMPORTANT: Gen-Ai Boilerplate Is Already Set Up

This PRD assumes the Gen-Ai SaaS boilerplate (https://github.com/digisurfsome/Gen-Ai) is already deployed and running as the autoforge.com web application. The boilerplate provides a complete foundation that this system EXTENDS — do NOT rebuild any of the following:

### Already Provided by Boilerplate (DO NOT REBUILD)

| Capability | Boilerplate Implementation |
|---|---|
| **Auth** | Supabase Auth — email/password + Google/GitHub/Discord OAuth, protected routes, admin routes |
| **Supabase connection** | Client initialized with auto-refresh, session persistence, RLS |
| **Stripe checkout** | `api/stripe-checkout.ts` — creates Checkout Sessions, handles redirects |
| **Stripe webhooks** | `api/stripe-webhook.ts` — signature validation, event routing |
| **Generic credit system** | `user_credits` table (single balance integer), `credit_transactions` ledger, `deduct_credits()` / `add_credits()` RPC functions |
| **Credit packages** | `credit_packages` table with Stripe price IDs, one-time purchase flow |
| **Subscription plans** | `subscription_plans` table, `user_subscriptions` tracking, renewal webhook handling |
| **Stripe customer mapping** | `stripe_customers` table linking user_id to stripe_customer_id |
| **User profiles & roles** | `profiles`, `user_roles` (admin/user/moderator), `user_metadata` tables |
| **Admin dashboard** | 11-tab admin panel: users, invitations, settings, API keys, audit logs, subscription plans, credit packages, revenue, test mode, sync status |
| **User billing dashboard** | Subscription management, credit top-up, invoice download |
| **Transaction history** | `credit_transactions` table + UI with filters |
| **Payment audit trail** | `payment_transactions` table |
| **Rate limiting** | In-memory rate limiter per endpoint |
| **Email** | Resend integration with React Email templates |
| **Test mode** | Full test/production data separation with `is_test` columns |
| **RLS policies** | Row-level security on all tables |
| **UI components** | 50+ shadcn/ui primitives, dark mode, responsive layouts |
| **User API keys** | `user_api_keys` table (currently for Resend config) |

### What This PRD Adds On Top

This PRD covers ONLY the AutoForge-specific billing logic that does not exist in the boilerplate:

1. **Typed credit system** — Replace single-balance credits with 9 typed credit columns
2. **AutoForge-specific Stripe products** — 9 credit types, 5 bundles, BYOK variants
3. **BYOK (Bring Your Own Key)** — Anthropic API key storage and build-time injection
4. **Build gating** — Credit check before agent pipeline starts, grace period, auto-refund
5. **Usage metering** — Per-build token/cost/margin tracking
6. **Tier-based rate limiting** — Concurrent/daily/monthly limits by subscription tier
7. **Build queue** — Priority ordering with real-time position updates
8. **Annual platform subscriptions** — 3 AutoForge-specific tiers with credit grants
9. **Admin dashboard extensions** — Margin analysis, credit velocity, build health tabs
10. **AutoForge pricing page** — Custom page showing typed credits and bundles

---

## Overview

AutoForge is transitioning from a free developer tool to a premium SaaS product with credit-based billing. The pricing strategy is deliberately high-end — this is NOT a $9/month mass-market tool. The goal is a barrier to entry that ensures only serious builders use the platform, while maximizing revenue per build.

**Core business decisions:**
- $219/build minimum for a single-platform web app
- Credit-based system, not unlimited subscription
- Premium add-ons (QA pipeline, knowledge base, security audit) sold separately
- No flat monthly fee that enables unlimited builds (prevents agency arbitrage)
- Bulk credit bundles for power users with many ideas
- Dual pricing model: "we provide the AI" (full price) and "bring your own key" (platform fee only)

**Why typed credits instead of the boilerplate's fungible credits:**
- Each build costs real money in AI compute ($50-250 in API calls)
- Different build types have different costs and capabilities
- Credits are tied to a specific build type (no mixing Standard credits for Pro builds)
- The boilerplate's single `balance` integer cannot represent 9 different credit types
- Need per-type tracking for margin analysis and revenue reporting

---

## Feature 1: Typed Credit System (Extends Boilerplate)

### What Changes From Boilerplate

The boilerplate has a `user_credits` table with a single `balance` integer. AutoForge needs 9 separate credit type columns because each credit type maps to a different build capability and price point.

**Migration approach:** Create a new `credit_balances` table alongside the boilerplate's existing `user_credits`. The boilerplate's generic credit system continues to work for any future non-build features. The typed `credit_balances` table is specifically for build credits.

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
1. User purchases credits via Stripe Checkout (boilerplate handles redirect + webhook)
2. Webhook handler maps to typed credit column and calls typed add_build_credits()
3. User starts a build -> system checks typed credit balance
4. Credit consumed immediately when build starts (not on completion)
5. Build runs through the agent pipeline
6. If SYSTEM error (crash, infra failure) -> automatic refund
7. If BAD SPEC (agent can't complete) -> no refund
8. If partial completion (some features done) -> no refund
```

**Key rules:**
- Credits never expire (critical for user trust)
- Credits are non-transferable (prevents secondary resale market)
- Credits are tied to a specific build type (no mixing)
- Refunds are automatic for system errors, manual review for all other cases

### New Database Table (Supabase Migration)

```sql
-- NEW TABLE: Typed credit balances for AutoForge builds
-- Runs alongside the boilerplate's generic user_credits table
create table credit_balances (
  user_id uuid primary key references auth.users on delete cascade,
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

alter table credit_balances enable row level security;
create policy "Users read own balance"
  on credit_balances for select using (auth.uid() = user_id);
```

### New Postgres Functions

```sql
-- Typed credit consumption (called when a build starts)
create or replace function consume_build_credit(
  p_user_id uuid,
  p_credit_type text,
  p_project_id uuid,
  p_build_id uuid
) returns boolean as $$
declare
  v_balance integer;
begin
  execute format(
    'select %I from credit_balances where user_id = $1 for update',
    p_credit_type
  ) into v_balance using p_user_id;

  if v_balance is null or v_balance < 1 then
    return false;
  end if;

  execute format(
    'update credit_balances set %I = %I - 1, updated_at = now() where user_id = $1',
    p_credit_type, p_credit_type
  ) using p_user_id;

  -- Log to EXISTING boilerplate credit_transactions with extended columns
  insert into credit_transactions (user_id, type, amount, description, reference_type, reference_id)
  values (p_user_id, 'deduction', -1,
          'Build credit consumed: ' || p_credit_type,
          'build', p_build_id::text);

  return true;
end;
$$ language plpgsql security definer;

-- Typed credit addition (called from webhook on typed credit purchase)
create or replace function add_build_credits(
  p_user_id uuid,
  p_credit_type text,
  p_quantity integer,
  p_stripe_payment_id text
) returns void as $$
begin
  insert into credit_balances (user_id)
  values (p_user_id)
  on conflict (user_id) do nothing;

  execute format(
    'update credit_balances set %I = %I + $2, updated_at = now() where user_id = $1',
    p_credit_type, p_credit_type
  ) using p_user_id, p_quantity;

  insert into credit_transactions (user_id, type, amount, description, stripe_payment_intent_id)
  values (p_user_id, 'purchase', p_quantity,
          'Purchased ' || p_quantity || ' ' || p_credit_type || ' credit(s)',
          p_stripe_payment_id);
end;
$$ language plpgsql security definer;

-- Typed credit refund
create or replace function refund_build_credit(
  p_user_id uuid,
  p_credit_type text,
  p_build_id uuid,
  p_reason text
) returns void as $$
begin
  execute format(
    'update credit_balances set %I = %I + 1, updated_at = now() where user_id = $1',
    p_credit_type, p_credit_type
  ) using p_user_id;

  insert into credit_transactions (user_id, type, amount, description, reference_type, reference_id)
  values (p_user_id, 'refund', 1, 'Refund: ' || p_reason, 'build', p_build_id::text);
end;
$$ language plpgsql security definer;
```

### Extend Boilerplate's credit_transactions Table

```sql
-- ADD columns to existing credit_transactions for build tracking
alter table credit_transactions add column if not exists credit_type text;
alter table credit_transactions add column if not exists build_id uuid;
alter table credit_transactions add column if not exists project_id uuid;
alter table credit_transactions add column if not exists metadata jsonb default '{}';
```

---

## Feature 2: Annual Platform Subscriptions (Extends Boilerplate)

### What Changes From Boilerplate

The boilerplate has `subscription_plans` and `user_subscriptions` tables with Stripe recurring billing. AutoForge adds 3 annual-only plans with typed credit grants.

**Migration approach:** Add 3 new rows to existing `subscription_plans` table. Extend boilerplate's `invoice.paid` webhook to call `add_build_credits()` for AutoForge annual plans.

### Platform Tiers

| Tier | Annual Price | Included Credits |
|---|---|---|
| Starter | $999/yr | 3 Standard Web + style picker + 1 boilerplate |
| Pro | $2,499/yr | 5 Pro Dual + all styles + all boilerplates + priority queue |
| Agency | $4,999/yr | 15 Pro Dual + 5 each add-on + white-label + API access |

### Credit Grant Logic

```
Starter renewal -> grant 3 standard_web
Pro renewal     -> grant 5 pro_dual
Agency renewal  -> grant 15 pro_dual + 5 knowledge_base + 5 security_audit + 5 performance_report
```

### Why Annual Only

- Prevents churn gaming (sign up, burn 10 builds, cancel)
- Higher commitment = invested users
- Starter includes $657 worth of credits for $999/yr — platform access is effectively $342/yr

---

## Feature 3: BYOK (Bring Your Own Key)

### What Changes From Boilerplate

The boilerplate's `user_api_keys` stores Resend email config. BYOK stores an **Anthropic API key** for build-time injection. Separate table to avoid conflicts.

### BYOK Pricing

| Build Type | Full Price | BYOK Price | Our Margin |
|---|---|---|---|
| Standard Web | $219 | $49 | $49 (100%) |
| Standard Dual | $299 | $79 | $79 |
| Pro Web | $399 | $99 | $99 |
| Pro Dual | $599 | $149 | $149 |
| Enterprise | $799 | $199 | $199 |

### New Database Table

```sql
create table byok_keys (
  user_id uuid primary key references auth.users on delete cascade,
  encrypted_key bytea not null,
  key_preview text not null,           -- "sk-ant-...7f3a"
  provider text default 'anthropic',
  validated_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table byok_keys enable row level security;
create policy "Users manage own keys"
  on byok_keys for all using (auth.uid() = user_id);
```

### Implementation

- **Encryption:** AES-256 with `BYOK_ENCRYPTION_KEY` env var
- **Validation:** Minimal `messages.create` call to Anthropic API on save
- **Masking:** Only return `sk-ant-...XXXX` after save
- **Build injection:** Decrypted key passed via env var to agent subprocess
- **Stripe:** Separate Price IDs for BYOK; checkout auto-detects BYOK key presence

---

## Feature 4: Build Gating (New)

Not in boilerplate. Integrates typed credits into AutoForge's agent pipeline start flow.

### Build Start Flow

```
User clicks "Start Build"
  |-- Authenticated? (boilerplate handles)
  |-- Active subscription? -> if no, show subscribe page
  |-- Sufficient typed credits? -> if no, show purchase modal
  |-- Within rate limits? -> if no, show upgrade CTA
  |-- Queue at capacity? -> if yes, add to queue with position
  |-- Consume credit atomically via consume_build_credit()
  |-- Create build_usage record (status: running)
  |-- Start agent pipeline
```

### Refund Policy

| Scenario | Refund? |
|---|---|
| System crash / infra error | Yes, automatic |
| Bad spec | No |
| Partial completion | No |
| User cancels mid-build | No |
| Queue cancel before start | Yes, automatic |

### Grace Period

48 hours to start build after credit consumed. Supabase cron job checks hourly for unconsumed credits and auto-refunds.

---

## Feature 5: Usage Metering (New)

### New Database Table

```sql
create table build_usage (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null,
  user_id uuid not null references auth.users on delete cascade,
  build_id uuid not null,
  credit_type text not null,
  is_byok boolean default false,
  total_input_tokens bigint default 0,
  total_output_tokens bigint default 0,
  total_turns integer default 0,
  total_agent_sessions integer default 0,
  cache_read_tokens bigint default 0,
  cache_write_tokens bigint default 0,
  features_total integer default 0,
  features_completed integer default 0,
  features_failed integer default 0,
  build_start timestamptz not null,
  build_end timestamptz,
  build_duration_minutes integer,
  estimated_ai_cost_cents integer default 0,
  credit_value_cents integer not null,
  margin_cents integer default 0,
  status text check (status in ('running', 'completed', 'failed', 'refunded')),
  created_at timestamptz default now()
);

create index idx_build_usage_user on build_usage(user_id, created_at desc);
create index idx_build_usage_project on build_usage(project_id);

alter table build_usage enable row level security;
create policy "Users read own usage"
  on build_usage for select using (auth.uid() = user_id);
```

---

## Feature 6: Tier-Based Rate Limiting (Extends Boilerplate)

Boilerplate has basic in-memory rate limiting. AutoForge adds persistent tier-aware limits for builds.

### Managed Users

| Limit | Starter | Pro | Agency |
|---|---|---|---|
| Concurrent builds | 1 | 2 | 5 |
| Daily builds | 3 | 10 | 30 |
| Monthly builds | 15 | 50 | unlimited |

### BYOK Users (higher limits, no AI cost to us)

| Limit | Starter | Pro | Agency |
|---|---|---|---|
| Concurrent builds | 2 | 5 | 10 |
| Daily builds | 5 | 15 | unlimited |
| Monthly builds | 30 | 100 | unlimited |

### New Database Table

```sql
create table rate_limits (
  user_id uuid primary key references auth.users on delete cascade,
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

### Build Queue

Priority: Agency > Pro > Starter, FIFO within tier. WebSocket position updates. Cancel before start = instant credit refund. Alert admin if queued > 30 minutes.

---

## Feature 7: Admin Dashboard Extensions (Extends Boilerplate)

Add 3 new tabs to boilerplate's existing 11-tab admin dashboard:

**Tab: Margin Analysis** — AI cost vs revenue per build type, BYOK vs managed ratio, BYOK margin

**Tab: Credit Velocity** — Credits sold vs consumed chart, outstanding balance (liability), avg purchase-to-consumption time

**Tab: Build Health** — Active builds, queue depth, success rate, avg duration, refund rate

---

## Feature 8: Stripe Product Configuration (New)

Create AutoForge products in Stripe Dashboard. Boilerplate handles all Stripe infrastructure.

| Product | Type |
|---|---|
| 9 individual credit types | One-time Price |
| 5 credit bundles | One-time Price with metadata |
| 5 BYOK credit variants | One-time Price with `byok: true` metadata |
| 3 annual platform plans | Subscription (annual) |
| Maintenance subscription | Subscription (monthly) |

Extend boilerplate webhook handlers to detect AutoForge metadata and call typed credit functions.

---

## New API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/billing/build-balance` | GET | Typed credit_balances (9 columns) |
| `/api/billing/build-checkout` | POST | Stripe Checkout for typed credits |
| `/api/billing/consume-credit` | POST | Atomically consume typed credit |
| `/api/billing/refund-credit` | POST | Refund typed credit |
| `/api/byok/key` | POST | Validate + save encrypted Anthropic key |
| `/api/byok/key` | GET | Masked key preview + validation status |
| `/api/byok/key` | DELETE | Delete stored key |
| `/api/billing/rate-limits` | GET | Current usage counts and tier limits |
| `/api/admin/margins` | GET | Cost/revenue/margin per build type |
| `/api/admin/credit-velocity` | GET | Credits sold vs consumed |
| `/api/admin/build-health` | GET | Active builds, queue, success rate |

---

## New UI Components

| Component | Description |
|---|---|
| `BuildCreditBalance.tsx` | Typed credit counts in header |
| `BuildPricingPage.tsx` | Credit types, bundles, BYOK pricing |
| `BuildPurchaseModal.tsx` | Credit type + quantity -> Stripe Checkout |
| `BYOKSettings.tsx` | API key input in existing settings page |
| `BuildQueue.tsx` | Queue position with WebSocket updates |
| `AdminMarginTab.tsx` | New admin tab: margin analysis |
| `AdminCreditVelocityTab.tsx` | New admin tab: credit velocity |
| `AdminBuildHealthTab.tsx` | New admin tab: build health |

---

## New Environment Variables (additions to boilerplate's existing vars)

```bash
# AutoForge Stripe Price IDs
STRIPE_PRICE_STANDARD_WEB=price_...
STRIPE_PRICE_STANDARD_DUAL=price_...
STRIPE_PRICE_PRO_WEB=price_...
STRIPE_PRICE_PRO_DUAL=price_...
STRIPE_PRICE_ENTERPRISE=price_...
STRIPE_PRICE_KNOWLEDGE_BASE=price_...
STRIPE_PRICE_SECURITY_AUDIT=price_...
STRIPE_PRICE_PERFORMANCE_REPORT=price_...
STRIPE_PRICE_MAINTENANCE=price_...

# BYOK variants
STRIPE_PRICE_BYOK_STANDARD_WEB=price_...
STRIPE_PRICE_BYOK_STANDARD_DUAL=price_...
STRIPE_PRICE_BYOK_PRO_WEB=price_...
STRIPE_PRICE_BYOK_PRO_DUAL=price_...
STRIPE_PRICE_BYOK_ENTERPRISE=price_...

# Annual subscriptions
STRIPE_PRICE_STARTER_ANNUAL=price_...
STRIPE_PRICE_PRO_ANNUAL=price_...
STRIPE_PRICE_AGENCY_ANNUAL=price_...

# Bundles
STRIPE_PRICE_BUNDLE_5_STANDARD=price_...
STRIPE_PRICE_BUNDLE_10_STANDARD=price_...
STRIPE_PRICE_BUNDLE_5_PRO_DUAL=price_...
STRIPE_PRICE_BUNDLE_AGENCY=price_...
STRIPE_PRICE_BUNDLE_ENTERPRISE_ANNUAL=price_...

# BYOK encryption
BYOK_ENCRYPTION_KEY=...  # 256-bit AES key
```

---

## Implementation Priority

### Phase 1: Typed Credits + Stripe Products (Week 1-2)
1. Supabase migration: `credit_balances` table + typed Postgres functions
2. Extend `credit_transactions` with `credit_type`, `build_id`, `project_id`
3. Create AutoForge Stripe products (9 types + bundles)
4. Extend boilerplate webhook for typed credit purchases
5. Build `BuildCreditBalance`, `BuildPricingPage`, `BuildPurchaseModal`

### Phase 2: Build Gating + Refunds (Week 3)
1. Integrate `consume_build_credit()` into build start flow
2. Subscription check before build start
3. Auto-refund on system crash
4. 48-hour grace period cron
5. Queue cancellation refund

### Phase 3: BYOK Support (Week 4)
1. `byok_keys` table migration
2. BYOK validation endpoint
3. AES-256 encryption
4. `BYOKSettings` component
5. BYOK pricing in Stripe + checkout
6. Agent subprocess key injection

### Phase 4: Annual Subscriptions (Week 5)
1. 3 annual plans in Stripe
2. Extend subscription webhook for credit grants
3. Platform access gating
4. Subscription comparison on pricing page

### Phase 5: Rate Limiting + Queue (Week 6)
1. `rate_limits` table migration
2. Concurrent/daily/monthly checks in build flow
3. Build queue with priority ordering
4. `BuildQueue` component with WebSocket
5. Automatic counter resets

### Phase 6: Usage Metering (Week 7)
1. `build_usage` table migration
2. Instrument agent pipeline for token tracking
3. Cost + margin calculation per build

### Phase 7: Admin Extensions (Week 8)
1. `AdminMarginTab`, `AdminCreditVelocityTab`, `AdminBuildHealthTab`
2. Admin API endpoints for aggregate queries
3. Integrate into boilerplate's existing admin dashboard

---

## Cost Analysis

| Build Type | Est. AI Cost | Credit Price | Margin % |
|---|---|---|---|
| Standard Web | $50-80 | $219 | 63-77% |
| Standard Dual | $80-120 | $299 | 60-73% |
| Pro Web | $70-110 | $399 | 72-82% |
| Pro Dual | $120-180 | $599 | 70-80% |
| Enterprise | $150-250 | $799 | 69-81% |

BYOK builds have 100% margin (zero AI cost to us).

---

## Security Considerations

1. **Stripe webhook signatures** — boilerplate already validates; ensure extensions preserve this
2. **Typed credit operations** — `FOR UPDATE` row locking prevents double-spend
3. **BYOK keys** — AES-256 at rest, never logged, never returned in full
4. **Admin endpoints** — reuse boilerplate's admin role check
5. **Rate limits** — server-side only
6. **Idempotency** — `stripe_payment_intent_id` prevents duplicate grants

---

## Open Questions

1. **Free trial?** 1 free Standard Web credit? Costs $50-80 per trial user.
2. **Referral program?** Give/get 1 free credit on purchase.
3. **Credit upgrades?** Pay difference to upgrade Standard -> Pro?
4. **Team accounts?** Shared credits within org? Expected for Agency tier.
5. **Maintenance auto-renewal?** Monthly Stripe Subscription or manual re-purchase?
