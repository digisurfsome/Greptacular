# A-N Mechanism Categories — Quick Reference

Condensed from the Mechanism Identification Framework. Use for cross-referencing during extraction.

| ID | Category | What It Covers | Common Sub-types |
|----|----------|---------------|-----------------|
| A | Data Input | How data enters the system | Forms, file upload, voice/audio, camera/OCR, drag-and-drop, sensors, import |
| B | Data Storage | How and where data persists | Relational DB, NoSQL, blob storage, cache, search index, audit trail |
| C | Data Processing | Transformations and logic applied to data | Validation, calculations, AI/ML, batch processing, format conversion, filtering |
| D | Data Output | How data is displayed or delivered | Lists/tables, charts, maps, timelines, kanban, export, print, real-time feeds |
| E | Authentication | How users prove identity | Email/password, OAuth, SSO, MFA, magic link, API keys, session management |
| F | Authorization | What users are allowed to do | RBAC, ABAC, resource ownership, multi-tenancy, feature flags, rate limiting |
| G | Communication | How system communicates | Email, push notifications, in-app notifications, SMS, chat, webhooks, activity feeds |
| H | Integration | Connections to external services | REST/GraphQL APIs, scraping, payment gateways, file sync, social media, email services |
| I | Workflow | Multi-step processes and automation | State machines, approval flows, cron jobs, queues, event triggers, wizards, retry/recovery |
| J | Search & Discovery | How users find things | Full-text search, faceted search, autocomplete, recommendations, tags, favorites, history |
| K | Collaboration | How users interact with each other | Comments, @mentions, sharing, co-editing, reactions, following, profiles |
| L | Monetization | How the app makes money | Subscriptions, one-time purchase, freemium, usage-based, marketplace, invoicing, refunds |
| M | Admin/Ops | Back-office management tools | Admin dashboard, user management, moderation, feature flags, analytics, configuration |
| N | Infrastructure | System-level support concerns | Caching, DB migrations, circuit breakers, auto-scaling, logging, monitoring, CI/CD |

## Cross-Reference Rules

1. Every REQUIRED category from `stage_2.mechanisms_identified` must have at least one mechanism extracted for it
2. Categories in `stage_2.mechanisms_gaps` with `resolution: "not_needed"` can be skipped
3. Categories with `resolution: "developers_choice"` should have a mechanism with OBVIOUS classification using the default approach
4. A single mechanism can map to multiple categories (e.g., an auth system maps to E and potentially F)
5. If a mechanism spans 4+ categories, consider whether it should be split into smaller mechanisms
