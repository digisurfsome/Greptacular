# Landing Page Build — autoforge.com Website

## What This Is

This is **Project A** — building the autoforge.com website as a separate app using AutoForge with the Gen-Ai SaaS boilerplate. This is a completely separate AutoForge run from the AutoForge enhancements (Project B).

**How to build:** Run AutoForge → select Gen-Ai boilerplate → feed this project's PRDs → AutoForge builds autoforge.com.

---

## Source Handoffs

These are the handoff documents that define this project:

### 1. Self-Deploy VPS (The Core Website)
**File:** `.claude/handoffs/self-deploy-vps-handoff.md`
**Generated PRD:** `.claude/generated-prds/self-deploy-vps-spec.xml`

This is the main website definition. It describes:
- Landing page (hero, features, competitor comparison, SEO)
- User signup/login (Supabase Auth — already in boilerplate)
- Instance dashboard (status cards, health monitoring)
- Fly.io Machines API integration (provisioning, lifecycle)
- Custom domain support
- Usage tracking and metering
- Admin dashboard extensions
- Onboarding wizard (API key entry, deploy animation)

**What the Gen-Ai boilerplate already provides (DO NOT rebuild):**
- React 18 + TypeScript + Vite + Tailwind + shadcn/ui + Radix UI
- Supabase Auth (email/password, OAuth, protected routes)
- Stripe Integration (subscriptions, one-time purchases, credits, webhooks)
- Admin Dashboard (role-based access, user management)
- Row-Level Security (RLS policies)
- Resend Email (transactional emails)
- Credit System (per-user balances with deduction/top-up)

### 2. Boilerplate-AutoForge Bridge (Website Side)
**File:** `.claude/handoffs/boilerplate-autoforge-bridge-handoff.md`
**Generated PRD:** `.claude/generated-prds/bridge-website-spec.xml` — 18 features covering build orchestration, WebSocket proxy, artifact delivery, multi-tenant isolation, auth bridge, callbacks, health monitoring, build dashboard, spec creation chat, project expand/assistant, and admin tools. Ready to feed to AutoForge.

**Website-side features (Features 1-9, 11):**

| # | Feature | What It Does |
|---|---------|-------------|
| 1 | Build Orchestrator Service | VM pool management, build assignment, health monitoring, teardown, queue management |
| 2 | WebSocket Proxy | Real-time progress streaming from worker to browser client |
| 3 | Build Artifact Delivery | Package project files to cloud storage, generate download links |
| 4 | Multi-Tenant Isolation | Per-user build isolation, data separation, resource limits |
| 5 | Authentication Bridge | Supabase JWT validation, per-build auth tokens for workers |
| 6 | Build Dashboard | Frontend UI for build status, logs, progress, history |
| 7 | Build Callbacks | Worker-to-web-app notifications (progress, completion, failure) |
| 8 | Worker Health Monitoring | Detect crashed/stuck builds, auto-recovery, timeout handling |
| 9 | Spec Creation Chat | SaaS version of spec creation (WebSocket chat through proxy) |
| 11 | Project Expand & Assistant | SaaS version of expand/assistant (requires running worker) |

**NOT website-side (goes to Project B instead):**
- Feature 10: AutoForge Server Modifications (BUILD_AUTH_TOKEN, --callback-url, --build-id flags)

### Database Tables (Supabase — new tables alongside existing boilerplate tables)
- `builds` — Build records with worker assignment, status, timing
- `build_workers` — Worker VM pool with status, region, capacity
- `user_specs` — Saved app specifications per user
- `instances` — Deployed VPS instances with status, URLs, config
- `instance_usage` — Usage metrics per instance
- `billing_events` — Billing audit trail

---

## What's Stripped Out (For Later)

These were removed from scope and saved separately:
- **Pricing tiers** — The boilerplate already has full Stripe/credit infrastructure. Specific pricing ($19/$39/$79 tiers) can be configured later without code changes.
- **Credit pricing system** — Was a separate handoff, removed. Boilerplate credits already work.
- **Marketplace** — Platform marketplace for boilerplates/styles/plugins. Separate project for later.
- **Lead magnets** — StyleVault giveaway, Domain Finder tool. Separate standalone apps for later.

---

## Build Order Recommendation

1. **Landing page + auth** (boilerplate gives you 80% of this for free)
2. **Instance dashboard UI** (CRUD for instances)
3. **Fly.io provisioning** (the core "deploy" button)
4. **Build orchestrator + WebSocket proxy** (bridge Features 1-2)
5. **Artifact delivery + callbacks** (bridge Features 3, 7)
6. **Multi-tenant isolation + auth bridge** (bridge Features 4-5)
7. **Health monitoring** (bridge Feature 8)
8. **Build dashboard** (bridge Feature 6)
9. **Spec creation chat + expand/assistant** (bridge Features 9, 11)
10. **Custom domains, usage tracking, admin extensions** (polish)
