# Mechanism Categories (A-N)

Every app can be decomposed into these 14 functional categories. Use these to identify gaps in the user's idea.

| ID | Category | Examples | Required For |
|----|----------|----------|-------------|
| A | Data Input | Forms, file uploads, API ingestion, voice input | All apps |
| B | Data Storage | Database schemas, file storage, caching, session state | All apps |
| C | Data Processing | Business logic, calculations, transforms, validation | All apps |
| D | Data Output | Views, reports, exports, downloads, API responses | All apps |
| E | Authentication | Login, signup, OAuth, magic links, MFA | Most apps |
| F | Authorization | Roles, permissions, RLS, access control | Most apps |
| G | Communication | Email, SMS, push notifications, in-app messaging | Many apps |
| H | Integration | Third-party APIs, webhooks, OAuth providers | Many apps |
| I | Workflow | Multi-step processes, approval chains, state machines | Complex apps |
| J | Search & Discovery | Full-text search, filtering, sorting, recommendations | Data-heavy apps |
| K | Collaboration | Shared workspaces, real-time editing, comments | Multi-user apps |
| L | Monetization | Payments, subscriptions, billing, invoicing | Commercial apps |
| M | Admin/Ops | Admin panels, moderation, analytics dashboards | Production apps |
| N | Infrastructure | Hosting, CI/CD, monitoring, logging, error tracking | All apps |

## App Archetypes and Required Categories

| Archetype | Required Categories | Common Optional |
|-----------|-------------------|-----------------|
| Dashboard | A, B, C, D, E, F | J, M, N |
| Marketplace | A, B, C, D, E, F, L | G, H, J, K |
| Chat/Social | A, B, D, E, G, K | F, H, J |
| CRUD/Tool | A, B, C, D, E | F, J, N |
| SaaS | A, B, C, D, E, F, L | G, H, I, J, M |
| Wizard/Form | A, B, C, D | E, G, I |
| Landing Page | D | A, G, H, L |
| Social Network | A, B, D, E, F, G, K | H, J, L, M |
