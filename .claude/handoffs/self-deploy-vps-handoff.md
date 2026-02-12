# Self-Deploying VPS System for AutoForge

## Status: Ready to Implement

## Overview

One-click deploy: non-technical users click a button, pay, and get a running AutoForge
instance in 60 seconds. No terminal, no VPS setup, no SSH, no Docker commands. The entire
flow happens through a browser -- sign up, pick a tier, pay, wait for a progress bar, and
land on a fully running AutoForge dashboard.

This turns AutoForge from a developer tool into a SaaS product with recurring revenue.

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

**Marketing site + Dashboard:** React / Next.js on Vercel or Fly.io static hosting
**Auth and data:** Supabase (Auth, Postgres, Edge Functions)
**Billing:** Stripe Subscriptions with webhook handlers
**Instance hosting:** Fly.io Machines API (primary) or DigitalOcean Droplets API (power-user option)
**Each user gets:** An isolated Machine running the AutoForge Docker image with their own env vars

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

## Pricing Tiers

| Tier | Price | Your Cost | Specs | Limits |
|------|-------|-----------|-------|--------|
| Starter | $19/mo | ~$5/mo | Shared CPU, 256MB RAM | 1 concurrent agent, 10 projects |
| Pro | $39/mo | ~$10/mo | Dedicated CPU, 1GB RAM | 3 concurrent agents, unlimited projects |
| Team | $79/mo | ~$20/mo | 2 CPUs, 2GB RAM | 5 concurrent agents, unlimited projects, priority support |

Gross margins: 73% (Starter), 74% (Pro), 75% (Team).

These costs include Fly.io compute, volume storage, and bandwidth. They do not include
Anthropic API costs -- those are either BYO key or metered separately.

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

## Supabase Schema

### Core Tables

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
```

## Feature Breakdown (10 Features, AutoForge-Compatible)

These features are structured for the AutoForge two-agent pattern: the initializer creates
them in the features database, and coding agents implement them one by one.

### Feature 1: Project Scaffolding and Marketing Site

**Priority:** 1 (no dependencies)

React + Vite + Tailwind CSS project with TypeScript. Landing page with hero section,
features grid, pricing table (3 tiers), FAQ accordion, and footer. Supabase client
initialized and configured. Responsive layout (mobile-first). Navigation header with
"Launch AutoForge" CTA button. All content is static at this stage -- no auth or billing
integration yet.

**Steps:**
1. Initialize React + Vite + TypeScript + Tailwind project
2. Create landing page layout with hero, features, pricing, FAQ sections
3. Set up Supabase client configuration (env vars, client initialization)
4. Add responsive navigation with CTA button
5. Verify build passes and all sections render correctly

### Feature 2: Auth and User Dashboard

**Priority:** 1 | **Depends on:** Feature 1

Supabase Auth integration with email/password and Google OAuth. Protected dashboard route
showing instance status card (provisioning/running/suspended), settings panel for API key
entry and tier display, and a sidebar with navigation. Auth state management with automatic
redirects (unauthenticated users go to login, authenticated users go to dashboard). Logout
functionality.

**Steps:**
1. Set up Supabase Auth with email and Google OAuth providers
2. Create login/signup pages with form validation
3. Build protected dashboard layout with sidebar navigation
4. Add instance status card component (placeholder data)
5. Add settings panel for API key input and tier display
6. Implement auth state management and route guards

### Feature 3: Stripe Billing Integration

**Priority:** 2 | **Depends on:** Feature 2

Stripe Checkout integration for three subscription tiers. Pricing page links to Stripe
Checkout sessions. Webhook handler (Supabase Edge Function) processes:
`checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`,
`customer.subscription.deleted`. Billing portal link in dashboard for users to manage
their subscription. Support for promotional/discount codes at checkout.

**Steps:**
1. Create Stripe products and prices for three tiers
2. Build checkout session creation endpoint (Edge Function)
3. Implement webhook handler for all four event types
4. Add billing portal link to dashboard settings
5. Wire up pricing page buttons to checkout flow
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

### Feature 8: Admin Dashboard

**Priority:** 5 | **Depends on:** Feature 4, Feature 5, Feature 7

Admin-only dashboard (separate route, role-based access) showing: all instances with
status and health, total user count and growth, revenue metrics (MRR, churn rate, ARPU),
usage patterns across all instances, and support tools (restart instance, extend grace
period, change tier manually). Accessible only to users with `admin` role in Supabase.

**Steps:**
1. Add admin role to Supabase Auth (custom claim or profiles table)
2. Create admin layout with protected route
3. Build instances overview table with filters and search
4. Add revenue metrics cards (MRR, churn, ARPU) with calculations
5. Implement support tools (restart, extend grace, manual tier change)
6. Add user management view (search, view details, billing history)

### Feature 9: Onboarding Wizard

**Priority:** 5 | **Depends on:** Feature 3, Feature 4

Post-signup onboarding wizard that guides users through setup. Step 1: Choose API key
mode (BYO vs metered) with explanation of each. Step 2: If BYO, enter Anthropic API key
with validation check. Step 3: Choose tier with feature comparison. Step 4: Stripe
checkout. Step 5: Deploying animation (progress bar with status messages: "Creating
instance...", "Installing AutoForge...", "Running health checks...", "Almost ready...").
Step 6: "Your AutoForge is ready!" with link button. Welcome email sent on completion
with quick-start guide.

**Steps:**
1. Create multi-step wizard component with progress indicator
2. Build API key mode selection step with explanations
3. Add API key entry step with validation (test key against Anthropic API)
4. Build tier selection step with feature comparison table
5. Integrate Stripe checkout as a wizard step
6. Create deploying animation with real-time status from provisioner
7. Build completion step with instance link and welcome email trigger

### Feature 10: Landing Page and SEO

**Priority:** 6 | **Depends on:** Feature 1

Upgrade the initial landing page to a professional marketing site. Competitor comparison
section: AutoForge vs Lovable vs Bolt vs Cursor (feature matrix table). Social proof
section with testimonials (placeholder initially). Blog section with initial "What is
AutoForge?" and "AutoForge vs Cursor" posts. SEO meta tags on all pages (title,
description, Open Graph, Twitter cards). Structured data (JSON-LD) for the product.
Sitemap generation. Performance optimization (lazy loading images, preconnect hints).

**Steps:**
1. Add competitor comparison table (AutoForge vs Lovable vs Bolt vs Cursor)
2. Create testimonials section with placeholder content
3. Build blog layout with markdown rendering
4. Write initial blog posts (What is AutoForge, AutoForge vs Cursor)
5. Add SEO meta tags, Open Graph, and Twitter cards to all pages
6. Add JSON-LD structured data and generate sitemap
7. Optimize performance (lazy images, preconnect, Lighthouse audit)

## Revenue Projections

Assumes average revenue per user of ~$24/month (weighted across tiers) and average
hosting cost of ~$6/month per instance.

| Users | Monthly Revenue | Monthly Hosting Cost | Monthly Profit | Annual Profit |
|-------|----------------|---------------------|----------------|---------------|
| 100 | $2,400 | $600 | $1,800 | $21,600 |
| 500 | $12,000 | $3,000 | $9,000 | $108,000 |
| 1,000 | $24,000 | $6,000 | $18,000 | $216,000 |
| 5,000 | $120,000 | $30,000 | $90,000 | $1,080,000 |

These projections do not include Anthropic API revenue from metered key users, which
could add 20-40% on top if offered.

Additional costs not reflected: Supabase Pro ($25/mo), Vercel Pro ($20/mo), Stripe
fees (2.9% + $0.30 per transaction), domain and email services. These are fixed costs
that become negligible past ~50 users.

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
