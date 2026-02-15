# Self-Deploying VPS System for AutoForge

## Status: Ready to Implement

## Overview

One-click deploy: non-technical users click a button, pay, and get a running AutoForge
instance in 60 seconds. No terminal, no VPS setup, no SSH, no Docker commands. The entire
flow happens through a browser -- sign up, pick a tier, pay, wait for a progress bar, and
land on a fully running AutoForge dashboard.

This turns AutoForge from a developer tool into a SaaS product with recurring revenue.

## CRITICAL: Use Gen-Ai Boilerplate (DO NOT Build From Scratch)

The marketing site, auth, billing, and admin dashboard are built on top of the **Gen-Ai
boilerplate** (`https://github.com/digisurfsome/Gen-Ai`), which is already installed as
AutoForge's web application boilerplate.

### What the Boilerplate Already Provides (DO NOT rebuild these):
- **React 18 + TypeScript + Vite 6 + Tailwind CSS + shadcn/ui + Radix UI** — Full frontend stack
- **Supabase Auth** — Email/password login, password reset, auth state management, protected routes
- **Stripe Integration** — Subscriptions, one-time purchases, credit system, webhook handlers, billing portal
- **Admin Dashboard** — Role-based access, user management, admin-only routes
- **Row-Level Security** — RLS policies already configured in Supabase
- **Resend Email** — Transactional email (welcome, password reset, notifications)
- **Vercel Deployment** — Pre-configured for Vercel (also works on other hosts)
- **Credit System** — Per-user credit balances with deduction and top-up

### What YOU Build On Top of the Boilerplate:
- Fly.io Machines API integration (provisioning, lifecycle management)
- Instance management UI (status cards, health monitoring)
- AutoForge-specific onboarding wizard (API key entry, tier selection, deploy animation)
- Custom domain support
- Usage tracking and metering
- AutoForge-specific landing page content (hero, features, pricing, competitor comparison)

### Integration Approach:
1. Clone the Gen-Ai boilerplate as the project base
2. Configure Supabase project with the additional `instances`, `instance_usage`, and `billing_events` tables (auth, Stripe tables already exist)
3. Add Fly.io provisioning Edge Functions alongside existing Stripe webhook handlers
4. Customize the existing dashboard layout for instance management
5. Customize the existing admin dashboard for instance oversight
6. Add AutoForge-specific landing page content to the existing layout

## User Flow

1. Visit autoforge.com marketing site
2. Click "Launch AutoForge"
3. Sign up (email or Google OAuth)
4. Pick a tier (Starter $19/mo, Pro $39/mo, Team $79/mo)
5. Complete Stripe checkout
6. Backend provisions a Fly.io Machine with the AutoForge Docker image
7. 60 seconds later: "Your AutoForge is ready at **yourname.autoforge.app**"
8. User clicks through to their running instance

No terminal. No SSH keys. No `docker run`. No `apt-get`. Just a button and a credit card.

## Architecture

```
                  autoforge.com
                  (Next.js / React)
                       |
          +------------+------------+
          |            |            |
      Supabase      Stripe      Fly.io
      (Auth +       (Billing)   (Hosting)
       Database)       |            |
          |        Webhooks    Machines API
          |            |            |
          +-----+------+------+----+
                |              |
           Dashboard      Provisioner
           (user-facing)  (Edge Function)
```

**Marketing site + Dashboard:** Gen-Ai boilerplate (React 18 + Vite 6 + Tailwind + shadcn/ui) deployed on Vercel
**Auth and data:** Supabase (Auth, Postgres, Edge Functions) — already configured in Gen-Ai boilerplate
**Billing:** Stripe (subscriptions, one-time, credits) — already configured in Gen-Ai boilerplate
**Instance hosting:** Fly.io Machines API (primary) or DigitalOcean Droplets API (power-user option)
**Each user gets:** An isolated Machine running the AutoForge Docker image with their own env vars

## Cross-Platform Architecture (4 Clients, 1 Supabase)

AutoForge is accessible through FOUR different clients. All four connect to the SAME
Supabase project — one database, one source of truth for users, credits, ideas, and builds.

```
                              SUPABASE
                         (One Database For All)
                                 |
            +----------+---------+---------+----------+
            |          |                   |          |
     autoforge.com   Flutter App       VPS Instance   Local Install
     (Web App)       (Mobile)          (Cloud)        (Desktop)
     Gen-Ai          Flutter           AutoForge      AutoForge
     Boilerplate     Boilerplate       Docker Image   Downloaded
```

### Client 1: autoforge.com (Web — Gen-Ai Boilerplate)
- Landing page, sign up, buy credits, manage account
- View/create/edit app ideas and PRDs
- Provision a VPS instance OR download desktop version
- Stripe checkout (ALL purchases happen here)
- **This is the "home base" for every user regardless of how they use AutoForge**
- Deployed on Vercel

### Client 2: Flutter Companion App (Mobile — Flutter Boilerplate)
- Same Supabase login (same email/password, same account)
- Jot down app ideas on the go (voice-to-text friendly)
- Fill in PRD details: app name, features, target audience, design preferences
- View build history, credit balance, instance status
- Push notifications when builds complete
- **Does NOT run builds** — planning, monitoring, and idea capture only
- Shares Supabase backend with the web app (dual boilerplate pattern)

### Client 3: VPS Instance (yourname.autoforge.app)
- The actual AutoForge app builder running in the cloud
- For non-technical users who don't want to install anything
- Pulls ideas/PRDs from Supabase that user entered on mobile or web
- No auth of its own — validates JWT tokens from Supabase (SSO)
- No billing of its own — checks entitlements via API to autoforge.com
- Deducts credits via API call before each build starts
- Mobile-friendly UI — user can monitor builds and answer spec questions from their phone

### Client 4: Local Install (Desktop Download)
- Same AutoForge, running on the user's own computer
- For technical users who want full control
- Still connects to Supabase for auth, credits, ideas, entitlements
- Same credit system — local doesn't mean free
- Build results logged to Supabase so they appear in web dashboard and mobile app
- Downloaded from autoforge.com/download

### How Data Flows Between Clients

All four clients read/write the same Supabase tables:

| Data | Written By | Read By |
|------|-----------|---------|
| User account | Web (signup) | All clients |
| App ideas/PRDs | Web, Flutter | VPS, Local (to start builds) |
| Credit balance | Web (purchase), VPS/Local (deduct) | All clients |
| Build history | VPS, Local (during builds) | Web, Flutter (monitoring) |
| Instance status | Provisioner (Edge Function) | Web, Flutter (dashboard) |

**Key pattern:** Ideas flow FROM web/mobile TO build engines. Build results flow FROM
build engines BACK TO web/mobile. Credits are purchased on web and consumed by build engines.

## Why Fly.io Over DigitalOcean

Fly.io is the recommended primary hosting backend for user instances:

- **No server management.** Fly handles infrastructure, networking, TLS certificates, and
  health checks. There is no SSH, no systemd, no nginx config to maintain.
- **API-first.** Programmatic instance creation, start, stop, destroy -- all through a
  clean REST API. Perfect for automated provisioning.
- **Auto-scaling and global regions.** Machines can run in 30+ regions. Users get low
  latency without any extra configuration.
- **Cost efficiency.** Shared CPU Machines cost roughly $3-5/month. Charging $19-29/month
  yields 75-85% gross margin.
- **Built-in SSL and load balancing.** Every app gets HTTPS with automatic certificate
  management. No Let's Encrypt cron jobs.
- **Scales to thousands.** The Machines API handles thousands of instances without
  requiring an ops team. No Ansible playbooks, no Terraform state files.

## DigitalOcean as "Power User" Option

For technical users who want full control:

- Full VPS with SSH access
- $4-6/month per Droplet (1 vCPU, 512MB-1GB RAM)
- More control over the environment
- More management overhead (user or us must handle updates, SSL, firewalls)
- Positioned as a premium "self-hosted" tier for agencies and enterprises

This can be offered alongside Fly.io, not instead of it.

## Fly.io Machines API

### Create an App

Each user instance gets its own Fly app. App names are globally unique on Fly.io, so
prefix with `autoforge-` and append a short user identifier.

```
POST https://api.machines.dev/v1/apps
Authorization: Bearer <FLY_API_TOKEN>
Content-Type: application/json

{
  "app_name": "autoforge-user123",
  "org_slug": "your-org"
}
```

### Create a Machine

After the app exists, create a Machine inside it. This is the actual compute instance
running AutoForge.

```
POST https://api.machines.dev/v1/apps/autoforge-user123/machines
Authorization: Bearer <FLY_API_TOKEN>
Content-Type: application/json

{
  "config": {
    "image": "registry.fly.io/autoforge:latest",
    "env": {
      "ANTHROPIC_API_KEY": "user-provided-or-platform-key",
      "AUTOFORGE_ALLOW_REMOTE": "1",
      "AUTOFORGE_INSTANCE_ID": "user123",
      "AUTOFORGE_TIER": "starter"
    },
    "guest": {
      "cpu_kind": "shared",
      "cpus": 1,
      "memory_mb": 256
    },
    "services": [
      {
        "ports": [
          { "port": 443, "handlers": ["tls", "http"] },
          { "port": 80, "handlers": ["http"] }
        ],
        "internal_port": 8080,
        "protocol": "tcp"
      }
    ]
  }
}
```

### Stop, Start, and Destroy

```
POST https://api.machines.dev/v1/apps/autoforge-user123/machines/{machine_id}/stop
POST https://api.machines.dev/v1/apps/autoforge-user123/machines/{machine_id}/start
DELETE https://api.machines.dev/v1/apps/autoforge-user123/machines/{machine_id}
```

All three are idempotent. Stop preserves the Machine and its attached volume (no compute
charges while stopped). Delete is permanent.

### Health Check

After creating a Machine, poll until the instance responds:

```
GET https://autoforge-user123.fly.dev/api/health
```

Timeout after 90 seconds. If the health check fails, log the error and notify the user
with a retry option.

## Instance Lifecycle

### Provision (happy path)

1. Stripe `checkout.session.completed` webhook fires
2. Edge Function creates Fly app + Machine with user's env vars
3. Attach a Fly Volume for persistent project data (survives Machine restarts)
4. Poll health endpoint until 200 OK
5. Write instance record to Supabase with status `running`
6. Return instance URL to the dashboard
7. Send welcome email with link

### Suspend (payment failure)

1. Stripe `invoice.payment_failed` webhook fires
2. Send warning email: "Payment failed, instance will suspend in 3 days"
3. After grace period, call `POST .../machines/{id}/stop`
4. Update instance status to `suspended` in Supabase
5. Dashboard shows "Suspended -- update payment to resume"
6. Volume data is preserved (user does not lose work)

### Resume (payment received)

1. Stripe `invoice.paid` webhook fires for a previously-suspended instance
2. Call `POST .../machines/{id}/start`
3. Poll health endpoint
4. Update instance status to `running`
5. Send "Welcome back" email

### Upgrade / Downgrade

1. User changes tier in dashboard
2. Stripe subscription updated via proration
3. Call Fly Machines API to resize (change `guest.cpus`, `guest.memory_mb`)
4. Machine restarts with new specs
5. Update tier in Supabase

### Destroy

1. User clicks "Delete instance" or cancels subscription
2. Update status to `destroying`
3. Start 30-day grace period (user can reactivate)
4. After 30 days: delete Machine, delete Volume, delete Fly app
5. Update status to `destroyed`
6. Send confirmation email

## Pricing Model: Credit-Based with Optional Monthly Plans

AutoForge uses a **credit-based pricing model**. Every build consumes credits. Monthly
plans give a discounted bundle of credits with a cap — they are NOT unlimited. Users can
also buy credits a la carte without a subscription.

**Design goal:** Prevent abuse. Building enterprise-quality apps should cost real money.
If someone wants to crank out 100 apps a month as an agency, they pay for 100 builds worth
of credits. The credit system ensures costs scale linearly with usage.

### How Credits Work

Each build consumes credits based on which **build components** are enabled. Users can
toggle components on/off to control cost per build:

| Build Component | Credit Cost | Description |
|----------------|-------------|-------------|
| Core Build | Base cost | App scaffolding + feature implementation (always required) |
| QA Pipeline | +credits | Code review, regression testing, final QA |
| Computer Use Testing | +credits | Claude Computer Use exploratory QA |
| Pre-Build Intelligence | +credits | Spec validation and recommendations before building |
| Post-Build Report | +credits | Quality report, security audit, performance analysis |
| Premium Boilerplate | +credits | Using a premium boilerplate vs basic template |

**Example:** A full build with everything enabled might cost 10 credits. Skip QA and
Computer Use testing and it drops to 7. Use the basic template instead of premium
boilerplate and it's 6. A bare-minimum build (just core + basic template) might be 4 credits.

**Exact credit costs TBD** — the numbers above are illustrative. Final pricing will be
set before launch based on actual Anthropic API costs per build component.

### Subscription Plans (Monthly/Yearly/Lifetime)

Monthly plans give a bundle of credits at a discount. Credits DO NOT roll over.
There is a hard cap — subscriptions are NOT unlimited.

| Tier | Monthly | Yearly | Lifetime | Credits/Month | Agents | VPS Specs |
|------|---------|--------|----------|---------------|--------|-----------|
| Starter | TBD | TBD | TBD | TBD | 1 | Shared CPU, 256MB |
| Pro | TBD | TBD | TBD | TBD | 3 | Dedicated CPU, 1GB |
| Agency | TBD | TBD | TBD | TBD | 5 | 2 CPUs, 2GB |

**Note:** Exact prices are TBD. The subscription fee covers VPS hosting + a bundle of
build credits. The monthly price will be higher than just hosting cost to include the
credit bundle, with a slight per-credit discount vs buying a la carte.

### A La Carte Credits (Buy More Anytime)

Users can buy credits without a subscription. Purchased credits do not expire.

| Pack | Price | Per-Credit Cost |
|------|-------|----------------|
| Single | TBD | Full price |
| 5-Pack | TBD | Slight discount |
| 10-Pack | TBD | Best per-credit rate |

### Boilerplate Fees (Per-Build, Separate from Credits)

Boilerplates have a **flat fee per build** on top of the credit cost. This is a separate
charge, not deducted from credits.

| Boilerplate | Per-Build Fee | Notes |
|-------------|--------------|-------|
| Basic Template | Free | Simple scaffolding, included with all tiers |
| Web SaaS (Gen-Ai) | ~$199-299 | Full Supabase + Stripe + Admin boilerplate |
| Dual Web + Mobile | ~$299-399 | Web boilerplate + Flutter companion app |
| E-Commerce | TBD | Specialized e-commerce template |
| Enterprise Suite | TBD | Full enterprise boilerplate |

**Exact boilerplate prices TBD.** The premium boilerplates include pre-built auth, billing,
admin dashboards, etc. — the user is paying for the massive head start, not just a template.

### VPS Hosting Cost (Separate from Credits)

The VPS hosting fee is part of the subscription or a standalone monthly charge:

| Tier | Hosting Cost (Our Cost) | Specs |
|------|------------------------|-------|
| Starter | ~$5/mo | Shared CPU, 256MB RAM |
| Pro | ~$10/mo | Dedicated CPU, 1GB RAM |
| Agency | ~$20/mo | 2 CPUs, 2GB RAM |

Users who run AutoForge locally (desktop download) skip the VPS hosting cost entirely
but still pay credits per build and boilerplate fees.

### Anti-Abuse Design

- **Every build costs credits.** No unlimited plans. No "build as much as you want."
- **Credits have real monetary value** tied to actual Anthropic API costs per build.
- **Agencies pay agency prices.** 100 builds = 100x credit cost. Period.
- **Monthly caps** prevent subscription abuse (even Agency tier has a credit limit).
- **Boilerplate fees** add cost to high-value builds using premium templates.

## Entitlements API

AutoForge instances (VPS and local) do NOT have their own billing or auth systems.
They check what a user can do by calling the Entitlements API on autoforge.com.

### How It Works

1. User opens their AutoForge instance (VPS or local)
2. AutoForge validates their JWT token against Supabase
3. Before any expensive operation (starting a build), AutoForge calls the Entitlements API
4. The API returns what the user can do, how many credits they have, which boilerplates they own
5. AutoForge enables/disables features accordingly
6. When a build starts, AutoForge calls a "deduct credits" endpoint
7. If the user runs out of credits mid-session, AutoForge shows a "Buy More Credits" button
   that redirects them to autoforge.com/credits

### Entitlements Endpoint

```
GET autoforge.com/api/entitlements
Authorization: Bearer <user-jwt-token>

Response:
{
  "user_id": "uuid",
  "tier": "pro",
  "credits_remaining": 7,
  "subscription_active": true,
  "max_concurrent_agents": 3,
  "available_boilerplates": ["basic", "saas-starter", "ecommerce"],
  "available_components": {
    "core_build": true,
    "qa_pipeline": true,
    "computer_use_qa": true,
    "pre_build_intelligence": true,
    "post_build_report": true
  },
  "instance_limits": {
    "max_projects": 50,
    "max_parallel_agents": 3
  }
}
```

### Credit Deduction Endpoint

```
POST autoforge.com/api/credits/deduct
Authorization: Bearer <user-jwt-token>
Content-Type: application/json

{
  "build_id": "uuid",
  "components": ["core_build", "qa_pipeline", "computer_use_qa"],
  "boilerplate": "saas-starter"
}

Response:
{
  "authorized": true,
  "credits_deducted": 8,
  "credits_remaining": 2,
  "boilerplate_charge_cents": 29900
}
```

If the user doesn't have enough credits, the response returns `authorized: false` with
the deficit amount and a checkout URL for buying more credits.

### "Buy More" Redirect Flow

When a VPS or local AutoForge instance detects insufficient credits:
1. Show modal: "You need X more credits to start this build"
2. Show options: "Buy 1 Credit", "Buy 5-Pack", "Buy 10-Pack", "Upgrade Plan"
3. Each button links to `autoforge.com/checkout?product=X&redirect=instance`
4. After purchase on autoforge.com, user is redirected back to their instance
5. AutoForge re-checks entitlements and proceeds with the build

## API Key Models

### Option 1: BYO Key (Bring Your Own)

User enters their own Anthropic API key during onboarding. The key is stored encrypted in
the instance environment variables.

- **Pros:** Lower subscription price, no token cost risk for us, user has full control
- **Cons:** Higher friction (user must have an Anthropic account), key management complexity

### Option 2: Metered Key (Platform-Provided)

AutoForge provides a shared Anthropic API key. Usage is tracked per instance and billed
as an add-on or included in a higher subscription price.

- **Pros:** Simpler UX (no key needed), one-click from signup to running
- **Cons:** Token cost risk, need usage tracking and overage billing, higher price point

### Recommendation

Default to **BYO key** for launch. It eliminates token cost risk and simplifies billing.
Add metered key as a premium option once usage tracking (Feature 7) is built.

## Supabase Schema (Additional Tables — Added to Existing Boilerplate Schema)

**NOTE: The Gen-Ai boilerplate already includes Supabase tables for auth (users, profiles),
Stripe (customers, subscriptions, prices, products), and credits (user_credits). The tables
below are ADDITIONS to the existing schema for AutoForge instance management.**

### AutoForge-Specific Tables

```sql
-- User instances (one per subscription)
create table instances (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  fly_app_id text unique not null,
  fly_machine_id text,
  fly_volume_id text,
  instance_url text,
  custom_domain text,
  tier text not null check (tier in ('starter', 'pro', 'team')),
  status text not null default 'provisioning'
    check (status in ('provisioning', 'running', 'suspended', 'destroying', 'destroyed')),
  stripe_subscription_id text,
  api_key_mode text not null default 'byo'
    check (api_key_mode in ('byo', 'metered')),
  region text default 'iad',
  created_at timestamptz not null default now(),
  suspended_at timestamptz,
  destroyed_at timestamptz
);

-- Index for dashboard queries
create index idx_instances_user_id on instances(user_id);
create index idx_instances_status on instances(status);

-- Usage tracking (daily rollups per instance)
create table instance_usage (
  id uuid primary key default gen_random_uuid(),
  instance_id uuid references instances(id) on delete cascade not null,
  date date not null,
  agent_minutes integer not null default 0,
  api_tokens_used bigint not null default 0,
  projects_created integer not null default 0,
  features_built integer not null default 0,
  unique(instance_id, date)
);

-- Billing event log (immutable audit trail)
create table billing_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  instance_id uuid references instances(id),
  event_type text not null,
  amount_cents integer,
  stripe_event_id text unique,
  metadata jsonb default '{}',
  created_at timestamptz not null default now()
);

-- Index for billing history queries
create index idx_billing_events_user_id on billing_events(user_id);
create index idx_billing_events_created_at on billing_events(created_at);

-- App ideas (shared across web, mobile, VPS, and local install)
-- Users create ideas on web or Flutter app, then build them on VPS or local
create table app_ideas (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  name text not null,                          -- "My Restaurant App"
  description text,                            -- Brief description of the app
  target_audience text,                        -- "Restaurant owners"
  features jsonb default '[]',                 -- Array of feature ideas (name, description)
  design_preferences text,                     -- "Modern, clean, dark mode"
  boilerplate_preference text,                 -- "saas-starter", "ecommerce", etc.
  prd_data jsonb default '{}',                 -- Full PRD details when fleshed out
  status text not null default 'draft'
    check (status in ('draft', 'ready', 'building', 'completed', 'archived')),
  build_id uuid,                               -- Links to builds table when building starts
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_app_ideas_user_id on app_ideas(user_id);
create index idx_app_ideas_status on app_ideas(status);

-- Build log (every build across ALL platforms — VPS and local)
-- Tracks credit consumption and links back to the idea that spawned the build
create table builds (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  idea_id uuid references app_ideas(id),       -- Which idea spawned this build (nullable for manual builds)
  instance_type text not null
    check (instance_type in ('vps', 'local')),
  instance_id uuid references instances(id),   -- Which VPS instance (null for local)
  boilerplate_used text,                       -- Which boilerplate template was used
  credits_consumed integer not null default 0,  -- Total credits this build cost
  components_used jsonb default '[]',          -- Which build components were enabled
  status text not null default 'started'
    check (status in ('started', 'building', 'completed', 'failed', 'cancelled')),
  features_total integer default 0,
  features_passing integer default 0,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create index idx_builds_user_id on builds(user_id);
create index idx_builds_status on builds(status);
```

### Row Level Security

```sql
-- Users can only see their own instances
alter table instances enable row level security;
create policy "Users can view own instances"
  on instances for select using (auth.uid() = user_id);
create policy "Users can update own instances"
  on instances for update using (auth.uid() = user_id);

-- Usage visible to instance owner
alter table instance_usage enable row level security;
create policy "Users can view own usage"
  on instance_usage for select using (
    instance_id in (select id from instances where user_id = auth.uid())
  );

-- Billing visible to user
alter table billing_events enable row level security;
create policy "Users can view own billing"
  on billing_events for select using (auth.uid() = user_id);

-- App ideas: users can CRUD their own ideas
alter table app_ideas enable row level security;
create policy "Users can view own ideas"
  on app_ideas for select using (auth.uid() = user_id);
create policy "Users can create ideas"
  on app_ideas for insert with check (auth.uid() = user_id);
create policy "Users can update own ideas"
  on app_ideas for update using (auth.uid() = user_id);
create policy "Users can delete own ideas"
  on app_ideas for delete using (auth.uid() = user_id);

-- Builds: users can view their own builds (inserts are done by Edge Functions)
alter table builds enable row level security;
create policy "Users can view own builds"
  on builds for select using (auth.uid() = user_id);
```

## Feature Breakdown (10 Features, AutoForge-Compatible)

These features are structured for the AutoForge two-agent pattern: the initializer creates
them in the features database, and coding agents implement them one by one.

### Feature 1: Customize Boilerplate for AutoForge Landing Page

**Priority:** 1 (no dependencies)

**NOTE: Uses Gen-Ai boilerplate as the project base.** The React + Vite + TypeScript +
Tailwind + shadcn/ui + Supabase client are ALREADY configured. This feature customizes
the existing boilerplate landing page with AutoForge-specific content: hero section,
features grid, pricing table (3 tiers), FAQ accordion, and footer. Responsive layout
is already built into the boilerplate.

**Steps:**
1. Clone the Gen-Ai boilerplate and configure environment variables for this project
2. Customize the existing landing page with AutoForge hero, features grid, pricing table (3 tiers), FAQ accordion
3. Update navigation header with "Launch AutoForge" CTA button
4. Add the `instances`, `instance_usage`, and `billing_events` tables to the Supabase schema (see SQL below)
5. Verify build passes and all sections render correctly

### Feature 2: Instance Dashboard (Auth Already in Boilerplate)

**Priority:** 1 | **Depends on:** Feature 1

**NOTE: Supabase Auth (email/password, password reset), protected routes, login/signup
pages, auth state management, and route guards are ALREADY built in the Gen-Ai boilerplate.
Do NOT rebuild these.** This feature adds AutoForge-specific dashboard content on top of
the existing protected dashboard: instance status card (provisioning/running/suspended),
settings panel for API key entry and tier display. Google OAuth can be enabled in Supabase
dashboard settings if desired.

**Steps:**
1. Verify existing boilerplate auth flow works (login, signup, password reset, logout)
2. Customize the existing protected dashboard layout for AutoForge branding
3. Add instance status card component (placeholder data for now)
4. Add settings panel for Anthropic API key input and tier display
5. Enable Google OAuth in Supabase dashboard settings (optional)

### Feature 3: Configure Stripe for AutoForge Tiers (Stripe Already in Boilerplate)

**Priority:** 2 | **Depends on:** Feature 2

**NOTE: Stripe integration (subscriptions, one-time purchases, credit system, webhook
handlers, billing portal) is ALREADY built in the Gen-Ai boilerplate. Do NOT rebuild
the Stripe checkout flow, webhook handling, or billing portal.** This feature configures
the existing Stripe integration with AutoForge-specific products: three subscription tiers
(Starter $19/mo, Pro $39/mo, Team $79/mo). Add the provisioning trigger to the existing
webhook handler so that `checkout.session.completed` also fires Fly.io instance creation.

**Steps:**
1. Create Stripe products and prices for the three AutoForge tiers in Stripe Dashboard
2. Update the existing boilerplate pricing page with AutoForge tier names, prices, and feature lists
3. Add provisioning trigger to the existing `checkout.session.completed` webhook handler (calls Feature 4's provisioner)
4. Add `invoice.payment_failed` handler extension for instance suspension (calls Feature 5)
5. Verify existing billing portal link works in dashboard settings
6. Test full payment flow with Stripe test mode

### Feature 4: Fly.io Provisioning Service

**Priority:** 2 | **Depends on:** Feature 2, Feature 3

Supabase Edge Function that provisions a complete Fly.io instance when payment is
confirmed. Creates Fly app with unique name, creates Machine with AutoForge Docker image,
attaches a Fly Volume for persistent storage, sets environment variables (API key, tier,
instance ID), polls health endpoint until the instance responds, and returns the instance
URL. Full error handling: if any step fails, roll back all previously-created resources
(delete Machine, delete app) and report the error.

**Steps:**
1. Create Edge Function with Fly.io API client
2. Implement app creation with unique naming (`autoforge-{userId}`)
3. Add Machine creation with tier-based resource allocation
4. Attach Fly Volume for persistent project data
5. Implement health check polling with 90-second timeout
6. Add rollback logic for partial provisioning failures
7. Wire webhook to trigger provisioning on `checkout.session.completed`

### Feature 5: Instance Lifecycle Management

**Priority:** 3 | **Depends on:** Feature 4

Full lifecycle management for user instances. Suspend: stop Machine on payment failure
(3-day grace period, warning email, then stop). Resume: restart Machine when payment is
received. Upgrade/downgrade: resize Machine specs when tier changes (Stripe proration
handled automatically). Destroy: 30-day grace period after cancellation, then delete
Machine + Volume + app. Health monitoring: periodic check that running instances are
healthy, auto-restart if unresponsive. Dashboard reflects current status in real time.

**Steps:**
1. Implement suspend flow (webhook -> grace period -> stop Machine)
2. Implement resume flow (webhook -> start Machine -> health check)
3. Implement upgrade/downgrade (resize Machine on tier change)
4. Implement destroy flow (30-day grace -> delete all resources)
5. Add health monitoring with periodic checks and auto-restart
6. Update dashboard to show live instance status

### Feature 6: Custom Domain Support

**Priority:** 4 | **Depends on:** Feature 4

Users can attach a custom domain to their AutoForge instance. Dashboard UI for entering
a domain name, displaying CNAME instructions (point `autoforge.yourdomain.com` to
`autoforge-user123.fly.dev`), triggering Fly.io certificate provisioning, and showing
domain verification status. The certificate is provisioned via the Fly.io Certificates
API. Verification polling checks DNS propagation and certificate issuance.

**Steps:**
1. Add custom domain input to dashboard settings
2. Display CNAME setup instructions with copy button
3. Implement Fly.io certificate creation via API
4. Add DNS verification polling
5. Show domain status (pending/verified/active/error)
6. Update instance URL in Supabase after domain is verified

### Feature 7: Usage Tracking and Metering

**Priority:** 4 | **Depends on:** Feature 4, Feature 5

Instances periodically report usage metrics to the central system. Tracked metrics:
agent minutes consumed, API tokens used (for metered key users), projects created,
features built. Supabase Edge Function receives usage reports and writes to
`instance_usage` table. Dashboard displays usage charts (daily/weekly/monthly). Overage
alerts for metered key users approaching their included token budget. Usage data is
aggregated daily.

**Steps:**
1. Add usage reporting endpoint to AutoForge Docker image
2. Create Edge Function to receive and store usage reports
3. Build usage dashboard with charts (agent minutes, tokens, projects)
4. Implement daily usage aggregation
5. Add overage alert emails for metered key users
6. Display usage summary on instance card in dashboard

### Feature 8: Extend Admin Dashboard for Instance Management (Admin Already in Boilerplate)

**Priority:** 5 | **Depends on:** Feature 4, Feature 5, Feature 7

**NOTE: The Gen-Ai boilerplate ALREADY includes an admin dashboard with role-based access,
admin-only routes, and user management. Do NOT rebuild the admin layout, role system, or
route protection.** This feature extends the existing admin dashboard with AutoForge-specific
views: all instances with status and health, revenue metrics (MRR, churn rate, ARPU),
usage patterns, and support tools (restart instance, extend grace period, change tier).

**Steps:**
1. Add instances overview table to existing admin dashboard (with filters and search)
2. Add revenue metrics cards (MRR, churn, ARPU) with calculations from `billing_events` table
3. Add instance health status column with live data from Fly.io
4. Implement support tools (restart instance, extend grace period, manual tier change)
5. Add usage analytics view (aggregate data from `instance_usage` table)

### Feature 9: Onboarding Wizard

**Priority:** 5 | **Depends on:** Feature 3, Feature 4

Post-signup onboarding wizard that guides new users through AutoForge-specific setup after
they've signed up via the boilerplate's existing auth flow. Step 1: Choose API key mode
(BYO vs metered) with explanation of each. Step 2: If BYO, enter Anthropic API key with
validation check. Step 3: Choose tier with feature comparison. Step 4: Stripe checkout
(uses the boilerplate's existing Stripe checkout flow). Step 5: Deploying animation
(progress bar with real-time status: "Creating instance...", "Installing AutoForge...",
"Running health checks...", "Almost ready..."). Step 6: "Your AutoForge is ready!" with
link button. Welcome email sent via the boilerplate's existing Resend integration.

**Steps:**
1. Create multi-step wizard component with progress indicator (using shadcn/ui components from boilerplate)
2. Build API key mode selection step with explanations
3. Add API key entry step with validation (test key against Anthropic API)
4. Build tier selection step with feature comparison table
5. Wire wizard's checkout step to the boilerplate's existing Stripe checkout flow
6. Create deploying animation with real-time status from provisioner
7. Build completion step with instance link and trigger welcome email via existing Resend integration

### Feature 10: Landing Page Polish and SEO

**Priority:** 6 | **Depends on:** Feature 1

Upgrade the AutoForge landing page (customized from boilerplate in Feature 1) to a
professional marketing site. Competitor comparison section: AutoForge vs Lovable vs Bolt
vs Cursor (feature matrix table). Social proof section with testimonials (placeholder
initially). Blog section with initial "What is AutoForge?" and "AutoForge vs Cursor"
posts. SEO meta tags on all pages (title, description, Open Graph, Twitter cards).
Structured data (JSON-LD) for the product. Sitemap generation. Performance optimization.

**Steps:**
1. Add competitor comparison table (AutoForge vs Lovable vs Bolt vs Cursor)
2. Create testimonials section with placeholder content
3. Build blog layout with markdown rendering
4. Write initial blog posts (What is AutoForge, AutoForge vs Cursor)
5. Add SEO meta tags, Open Graph, and Twitter cards to all pages
6. Add JSON-LD structured data and generate sitemap
7. Optimize performance (lazy images, preconnect, Lighthouse audit)

## Revenue Projections (Credit-Based Model)

Revenue comes from THREE streams: subscriptions (hosting + credit bundles), a la carte
credit purchases, and per-build boilerplate fees.

**Exact prices TBD.** The projections below use placeholder numbers to illustrate the
model. Replace with actual prices once finalized.

### Revenue Streams

1. **Subscriptions** — Recurring monthly/yearly for VPS hosting + credit bundles
2. **A la carte credits** — One-time purchases for additional builds
3. **Boilerplate fees** — Per-build charge for premium templates ($199-399 per build)

### Cost Structure Per Build

- Anthropic API cost per full build: ~$5-15 (varies by feature count and components used)
- Fly.io hosting per user: ~$5-10/month
- Fixed costs: Supabase Pro ($25/mo), Vercel Pro ($20/mo), Stripe fees (2.9% + $0.30)

At premium per-build pricing ($199-499 per build with boilerplate), margins are very high.
Even accounting for API costs and hosting, gross margin per build should be 80%+.

### Anti-Commoditization Note

The premium pricing ($199-499 per build) is intentional. AutoForge produces enterprise-
quality apps with QA, testing, and professional boilerplates. This is NOT a vibe-coding
toy — it's a professional app factory. Pricing it high keeps the output quality perception
high and prevents market flooding.

## Flutter Companion App (Dual Boilerplate Pattern)

The Flutter boilerplate (`https://github.com/digisurfsome/Gen-Ai` — Flutter variant)
shares the SAME Supabase project as the web app. This is the "dual boilerplate" pattern:
one backend, two frontends (web + mobile).

### What the Flutter App Does

1. **Idea Capture** — Jot down app ideas on the go. Voice-to-text friendly. Fill in name,
   description, features, target audience, design preferences. Saves to `app_ideas` table
   in Supabase — instantly visible on web dashboard and inside AutoForge instances.

2. **PRD Builder** — Expand a draft idea into a full PRD. Conversational flow (like the
   spec creation chat in AutoForge) but running on mobile. Can use voice input to describe
   features. The PRD data is stored in `app_ideas.prd_data` JSON column.

3. **Build Monitoring** — View active builds across all instances (VPS and local). See
   feature progress, agent status, logs. Push notifications when builds complete or fail.

4. **Account Management** — View credit balance, subscription tier, build history. Quick
   link to buy more credits (opens autoforge.com in mobile browser for Stripe checkout).

5. **Instance Status** — See if your VPS instance is running, suspended, or provisioning.
   Quick actions: restart instance, view instance URL.

### What the Flutter App Does NOT Do

- Does NOT run builds (no Claude agent, no CLI, no coding)
- Does NOT process payments (redirects to autoforge.com for Stripe checkout)
- Does NOT manage instance lifecycle (that's the web dashboard + Edge Functions)

### Shared Supabase Tables

Both the web app and Flutter app read/write the same tables:

```
Gen-Ai Web Boilerplate          Flutter Boilerplate
        |                               |
        |       SAME SUPABASE           |
        +----------- PROJECT ----------+
        |                               |
   auth.users (login)            auth.users (login)
   user_credits (balance)        user_credits (balance)
   app_ideas (create/edit)       app_ideas (create/edit)
   builds (view history)         builds (view history)
   instances (manage)            instances (view status)
```

Create an idea on your phone at 7am on the train. Open your laptop at 9am and it's already
there in your AutoForge dashboard, ready to build.

## Idea Capture: Web + Mobile (Separate from Build Engine)

The idea/PRD creation flow does NOT need the AutoForge CLI or VPS. It's a standalone
feature that lives in the web dashboard and Flutter app:

### Where Ideas Can Be Created
- **Flutter app** — Quick capture with voice-to-text. Best for on-the-go brainstorming.
- **Web dashboard** (autoforge.com) — Full-featured idea editor. Best for fleshing out PRDs.
- **Inside AutoForge** (VPS/local) — The existing spec creation chat. Best when ready to build immediately.

### Idea Lifecycle

```
DRAFT → READY → BUILDING → COMPLETED
  |       |         |          |
Phone   Laptop    VPS/Local   Done
```

1. **DRAFT** — User creates an idea (phone or web). Just a name and rough description.
2. **READY** — User has fleshed out features, design preferences, boilerplate choice. Marked as "ready to build."
3. **BUILDING** — User clicks "Build This" on their VPS or local install. Credits are deducted. AutoForge pulls the idea's PRD data and uses it as the app spec.
4. **COMPLETED** — Build finished. Linked to the `builds` table with full results.

### Voice-First Design

The Flutter app and web dashboard should support **voice input** for idea capture:
- Large microphone button for recording thoughts
- Whisper API (or device speech-to-text) transcribes voice to text
- AI assistant cleans up transcription into structured fields (name, features, audience)
- User reviews and edits before saving
- Especially important because the founder (and likely many users) prefers talking over typing

## Key Decisions to Make Before Building

### 1. Free trial

**Recommendation:** 7-day free trial, no credit card required. Provision a Starter-tier
instance immediately on signup. Convert to paid or suspend after 7 days. Free trials
drive signups and let users experience the product before committing.

### 2. Default API key mode

**Recommendation:** Default to BYO key for launch. It eliminates token cost risk and
keeps the subscription price low. The onboarding wizard explains how to get an Anthropic
key. Add metered key as a premium convenience option in a later phase.

### 3. Data persistence

Fly Volumes provide persistent block storage attached to a Machine. Each instance gets a
volume for project files, the features database, and the project registry. Volumes survive
Machine restarts and stops. They do NOT survive Machine deletion -- this is intentional
for the 30-day destroy grace period.

For backups: periodic snapshots of the volume to object storage (Fly Tigris or S3) can be
added later as a premium feature.

### 4. Railway as alternative

Railway has an affiliate program. Offer a "Deploy to Railway" button on the AutoForge
GitHub repo as a self-hosted alternative. This serves technical users who want to manage
their own infrastructure and generates affiliate revenue. It does not compete with the
managed Fly.io offering because the target audiences are different.

### 5. White-labeling for agencies

Future consideration. Agencies could get a white-labeled version of AutoForge running on
their own domain with their branding. This would be a separate "Enterprise" tier at
$199+/month. Not needed for launch.

## Affiliate Opportunities

Three affiliate integrations that complement the product:

1. **Railway affiliate.** "Deploy to Railway" button on the GitHub repo and docs site.
   Serves the self-hosted crowd. Railway pays a percentage of referred customer revenue.

2. **Hostinger affiliate.** For users who want a traditional VPS with full control.
   Link from a "Self-Host Guide" documentation page. Hostinger pays per signup.

3. **Namecheap affiliate.** Ties directly into the custom domain feature (Feature 6).
   When a user enters a domain they do not own yet, show a "Need a domain? Get one from
   Namecheap" link with the affiliate code. Natural upsell moment.

## Implementation Notes

### Docker Image

The existing AutoForge Dockerfile (multi-stage: Node 20 for UI build, Python 3.11-slim
for runtime) is already suitable for Fly.io deployment. The key environment variable
`AUTOFORGE_ALLOW_REMOTE=1` enables remote access. The image should be pushed to the
Fly.io container registry (`registry.fly.io/autoforge:latest`) as part of CI/CD.

### Security Considerations

- User API keys must be encrypted at rest (Supabase Vault or encrypted columns)
- Each instance is fully isolated (separate Fly app, separate network)
- The provisioning Edge Function must validate that the requesting user owns the
  subscription before creating or modifying any resources
- Rate limit provisioning requests to prevent abuse
- The admin dashboard must use a separate auth check, not just a frontend route guard

### Monitoring

- Fly.io provides built-in metrics (CPU, memory, network) per Machine
- Set up alerts for: instance health check failures, high error rates in Edge Functions,
  Stripe webhook failures, provisioning timeouts
- Log all provisioning events for debugging and audit

## What NOT To Do

- Do NOT scaffold a new React + Vite + TypeScript project — use the Gen-Ai boilerplate
- Do NOT build Supabase Auth from scratch — it's already in the boilerplate
- Do NOT build Stripe checkout/webhooks/billing portal from scratch — already in the boilerplate
- Do NOT build an admin dashboard from scratch — extend the existing one in the boilerplate
- Do NOT build a credit system from scratch — the boilerplate already has per-user credit balances
- Do NOT build email sending from scratch — use the boilerplate's existing Resend integration
- Do NOT create new UI components when shadcn/ui + Radix UI components exist in the boilerplate
- Do NOT put auth or billing logic inside AutoForge VPS instances — they check entitlements via API
- Do NOT build a separate backend for the Flutter app — it shares the same Supabase project
- DO add the `instances`, `instance_usage`, `billing_events`, `app_ideas`, and `builds` tables to Supabase
- DO build the Fly.io Machines API integration (this is entirely new)
- DO build the instance lifecycle management (suspend/resume/upgrade/destroy)
- DO build the onboarding wizard for API key entry and deploy animation
- DO build the Entitlements API for VPS/local instances to check credits and permissions
- DO build the credit deduction flow (AutoForge calls API before each build starts)
