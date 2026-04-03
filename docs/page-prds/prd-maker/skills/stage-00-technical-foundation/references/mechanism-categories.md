# Mechanism Categories Reference (A-N)

> 14 mechanism categories from the Mechanism Identification Framework.
> Stage 0 instantiates these as a target model. Each category is tagged with boilerplate coverage status.

---

## Categories

| ID | Name | Description |
|----|------|-------------|
| A | Data Input | How data enters the system (forms, file upload, voice, camera, drag-and-drop, sensors, import) |
| B | Data Storage | How and where data persists (relational DB, NoSQL, blob storage, cache, search index, audit trail) |
| C | Data Processing | Transformations and logic applied to data (validation, calculations, AI/ML, batch, format conversion) |
| D | Data Output | How data is displayed or delivered (lists, charts, maps, timelines, kanban, export, print, real-time feeds) |
| E | Authentication | How users prove who they are (email/password, OAuth, SSO, MFA, magic link, API keys, sessions) |
| F | Authorization | What users are allowed to do (RBAC, ABAC, resource ownership, multi-tenancy, feature flags, rate limiting) |
| G | Communication | How the system communicates (email, push, in-app notifications, SMS, chat, webhooks, activity feeds) |
| H | Integration | Connections to external services (REST/GraphQL, web scraping, payment gateways, file sync, social media) |
| I | Workflow | Multi-step processes and automation (state machines, approval flows, cron jobs, queues, event triggers) |
| J | Search & Discovery | How users find things (full-text search, faceted search, autocomplete, recommendations, tags, favorites) |
| K | Collaboration | How users interact with each other (comments, @mentions, sharing, co-editing, reactions, following, profiles) |
| L | Monetization | How the app makes money (subscriptions, one-time, freemium, usage-based, marketplace, invoicing, refunds) |
| M | Admin/Ops | Back-office tools (admin dashboard, user management, content moderation, feature flags, analytics, config) |
| N | Infrastructure | System-level concerns (caching, DB migrations, circuit breakers, auto-scaling, logging, monitoring, CI/CD) |

---

## Default Status by Profile

### `supabase_web`

| ID | Status | Rationale |
|----|--------|-----------|
| A | needs_user_input | Input patterns depend entirely on the app idea |
| B | covered_by_boilerplate | Supabase/Postgres + Supabase Storage are pre-configured |
| C | needs_user_input | Processing logic is app-specific |
| D | needs_user_input | Display patterns depend on the app idea |
| E | covered_by_boilerplate | Supabase Auth handles email/password + OAuth |
| F | covered_by_boilerplate | Supabase Row Level Security (RLS) is available |
| G | needs_user_input | No notification system in base boilerplate |
| H | needs_user_input | No external integrations in base |
| I | needs_user_input | No workflow engine in base |
| J | needs_user_input | Postgres full-text search available but needs app-specific setup |
| K | needs_user_input | No collaboration features in base |
| L | needs_user_input | No payment integration in base |
| M | needs_user_input | No admin panel in base |
| N | covered_by_boilerplate | Vercel hosting + Supabase managed infra |

### `flutter_mobile`

| ID | Status | Rationale |
|----|--------|-----------|
| A | needs_user_input | Mobile-specific input patterns depend on app |
| B | covered_by_boilerplate | Supabase/Postgres backend |
| C | needs_user_input | App-specific |
| D | needs_user_input | App-specific |
| E | covered_by_boilerplate | Supabase Auth mobile SDK |
| F | covered_by_boilerplate | Supabase RLS |
| G | needs_user_input | Push notifications need platform-specific setup |
| H | needs_user_input | App-specific |
| I | needs_user_input | App-specific |
| J | needs_user_input | App-specific |
| K | needs_user_input | App-specific |
| L | needs_user_input | In-app purchases need platform-specific setup |
| M | needs_user_input | App-specific |
| N | covered_by_boilerplate | Supabase managed backend |

### `dual`

Same as `supabase_web` coverage. Both web and mobile clients share the Supabase backend, so B, E, F, and N are covered.

### `no_boilerplate`

All categories: `needs_user_input`. No boilerplate assumptions.

### `raw_checklist`

All categories: `needs_user_input`. Existing app analysis not yet supported.
