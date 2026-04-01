# Mechanism Identification Framework

> The "Periodic Table of App Mechanisms" — used during Stage 2 (Gap Analysis) and Stage 4 (Mechanism Extraction) to systematically break down what an app DOES.
>
> When someone describes their app, map their description to these categories. Then ask the sub-questions for each identified mechanism. For categories they DIDN'T mention, ask if their app needs them.

---

## How to Use This

1. **Listen to the user's description** (rant, brain dump, whatever)
2. **Tag every feature/action they describe** with a mechanism category (A-N)
3. **For each tagged mechanism**, ask the sub-questions below
4. **For categories NOT mentioned**, ask: "Does your app need [category]?"
5. **Output**: A complete mechanism map with answers for each active category

---

## Category A: Data Input

**What it is:** How data enters the system from users or external sources.

| Sub-type | Examples |
|----------|----------|
| Forms | Text inputs, dropdowns, date pickers, multi-step wizards |
| File Upload | Images, documents, video, bulk CSV import |
| Voice/Audio | Speech-to-text, voice commands, audio recording |
| Camera/OCR | Photo capture, document scanning, barcode reading |
| Drag-and-Drop | Reordering lists, kanban boards, file drop zones |
| Sensors/IoT | GPS location, accelerometer, biometric input |
| Copy/Paste & Import | Clipboard, URL parsing, data import from other apps |

### Sub-Questions
1. What types of data do users input? (text, numbers, dates, files, rich text?)
2. Are there multi-step forms or wizards?
3. What file types are accepted? Size limits?
4. Is real-time validation needed (as-they-type) or on-submit?
5. Do users input data on behalf of others (admin entry)?
6. Is bulk input needed (CSV import, batch creation)?
7. Are there draft/autosave requirements?

---

## Category B: Data Storage

**What it is:** How and where data persists.

| Sub-type | Examples |
|----------|----------|
| Relational DB | PostgreSQL, MySQL, SQLite — structured, normalized |
| NoSQL/Document | MongoDB, Firestore — flexible schema, nested documents |
| Blob/File Storage | S3, Cloud Storage — media, attachments, exports |
| Cache Layer | Redis, Memcached — hot data, session state |
| Search Index | Elasticsearch, Algolia, pgvector — fast text/vector search |
| Audit Trail | Immutable log of all changes for compliance |

### Sub-Questions
1. What are the main entities/objects? (users, products, orders, etc.)
2. What are the relationships between entities? (one-to-many, many-to-many?)
3. Is the schema fixed or does it need to be flexible?
4. How much data will there be? (hundreds, thousands, millions of records?)
5. Is data isolated per user/tenant or shared?
6. What needs to be cached for performance?
7. Is there an audit/history requirement? (who changed what, when?)
8. Data retention — how long is data kept? Auto-delete rules?

---

## Category C: Data Processing

**What it is:** Transformations, calculations, and logic applied to data.

| Sub-type | Examples |
|----------|----------|
| Validation | Input sanitization, business rule checks |
| Calculations | Pricing, scoring, statistics, aggregations |
| AI/ML | Classification, generation, recommendations, embeddings |
| Batch Processing | Nightly reports, bulk updates, data migrations |
| Format Conversion | PDF generation, image resizing, data export formatting |
| Filtering/Sorting | Complex queries, faceted results, dynamic sorting |

### Sub-Questions
1. What calculations or transformations happen to the data?
2. What triggers the processing? (user action, schedule, event?)
3. Is it real-time (blocking) or background (async)?
4. What's the input and what's the expected output?
5. Are there AI/ML components? What do they do specifically?
6. What happens if processing fails? Retry? Fallback?
7. Are there rate limits or resource constraints?

---

## Category D: Data Output

**What it is:** How data is displayed or delivered to users.

| Sub-type | Examples |
|----------|----------|
| Lists/Tables | Paginated lists, sortable tables, infinite scroll |
| Charts/Graphs | Bar, line, pie, heatmaps, dashboards |
| Maps | Geographic data, location markers, route display |
| Timelines | Activity feeds, history views, changelog |
| Kanban/Board | Status columns, drag-to-reorder |
| Export | PDF, CSV, Excel, JSON download |
| Print | Print-optimized layouts, receipts |
| Real-time Feeds | Live updates, streaming data, websocket-driven |

### Sub-Questions
1. What are the main views/pages users see?
2. Are there list views? What columns/fields? Sortable? Filterable?
3. Are there dashboard/analytics views? What metrics?
4. Do users need to export data? What formats?
5. Is real-time updating needed? (live counters, streaming feeds?)
6. What does an empty state look like? (no data yet)
7. Is there pagination? Infinite scroll? Load-more?

---

## Category E: Authentication

**What it is:** How users prove who they are.

| Sub-type | Examples |
|----------|----------|
| Email/Password | Traditional signup/login |
| OAuth/Social | Google, GitHub, Apple, Facebook sign-in |
| SSO | SAML, enterprise single sign-on |
| MFA | Two-factor via SMS, authenticator app, hardware key |
| Magic Link | Passwordless email link login |
| API Keys | Machine-to-machine authentication |
| Session Management | JWT, cookies, refresh tokens, session timeout |

### Sub-Questions
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers are needed?
3. Is MFA required? For all users or just admins?
4. How are sessions managed? (JWT, cookies, refresh tokens?)
5. What's the session timeout?
6. Is there a "remember me" feature?
7. Password requirements? Reset flow?
8. Is there account deletion? What happens to user data?

---

## Category F: Authorization

**What it is:** What users are allowed to do once authenticated.

| Sub-type | Examples |
|----------|----------|
| RBAC | Admin, editor, viewer roles |
| ABAC | Attribute-based (department, location, subscription tier) |
| Resource Ownership | Users can only see/edit their own data |
| Multi-tenancy | Organizations/teams with isolated data |
| Feature Flags | Features enabled per user/plan/group |
| Rate Limiting | Per-user or per-plan API/action limits |

### Sub-Questions
1. What roles exist? (admin, user, moderator, viewer?)
2. What can each role do? (CRUD per entity)
3. Is data isolated per user? Per organization/team?
4. Are there subscription tiers that unlock features?
5. Can users share access with others? (invite, transfer ownership?)
6. Are there approval workflows? (request access, admin approves?)
7. Row-level security? (users see only their own records?)

---

## Category G: Communication

**What it is:** How the system communicates with users or external systems.

| Sub-type | Examples |
|----------|----------|
| Email | Transactional, marketing, digests |
| Push Notifications | Mobile push, browser notifications |
| In-App Notifications | Bell icon, notification center, badges |
| SMS | Verification codes, alerts |
| Chat/Messaging | Real-time chat, direct messages, channels |
| Webhooks | Outbound event notifications to other systems |
| Activity Feeds | "John liked your post" style updates |

### Sub-Questions
1. What events trigger notifications? (signup, purchase, mention, etc.)
2. Which channels? (email, push, in-app, SMS?)
3. Can users configure notification preferences?
4. Are there email templates? What content?
5. Is real-time chat needed? 1:1, group, or channels?
6. Are there digest/summary emails? (daily, weekly?)
7. Do you need to send webhooks to external services?

---

## Category H: Integration

**What it is:** Connections to external services and APIs.

| Sub-type | Examples |
|----------|----------|
| REST/GraphQL Consumption | Calling external APIs |
| REST/GraphQL Exposure | Providing APIs for others to call |
| Web Scraping | Extracting data from websites |
| Payment Gateways | Stripe, PayPal, Apple Pay |
| File/Data Sync | Dropbox, Google Drive, S3 sync |
| Social Media | Posting, reading feeds, sharing |
| Email Services | SendGrid, SES, Mailgun |

### Sub-Questions
1. Which external services does the app connect to?
2. What data is sent/received from each?
3. What authentication does each external API need?
4. What happens when an external service is down? Fallback?
5. Are there rate limits on external APIs?
6. Does the app expose its own API for others?
7. Is there a payment processor? Which one? What flows? (one-time, subscription, refunds?)

---

## Category I: Workflow

**What it is:** Multi-step processes, state machines, and automation.

| Sub-type | Examples |
|----------|----------|
| State Machines | Order status (pending → processing → shipped → delivered) |
| Approval Flows | Submit → review → approve/reject |
| Cron Jobs | Scheduled tasks (nightly cleanup, weekly reports) |
| Queues | Background job processing, retry logic |
| Event Triggers | "When X happens, do Y" automation |
| Wizards/Multi-step | Step-by-step guided processes |
| Retry/Recovery | Automatic retry on failure, dead letter queues |

### Sub-Questions
1. What multi-step processes exist? What are the states?
2. What triggers transitions between states?
3. Who can trigger each transition? (user, admin, system?)
4. Are there time-based triggers? (expire after 24h, send reminder after 3 days?)
5. What happens when a step fails?
6. Are there scheduled/automated tasks? How often?
7. Is there an undo/rollback capability?

---

## Category J: Search & Discovery

**What it is:** How users find things within the app.

| Sub-type | Examples |
|----------|----------|
| Full-text Search | Keyword search across content |
| Faceted Search | Filter by category, price range, date, etc. |
| Autocomplete | Type-ahead suggestions |
| Recommendations | "Similar items", "You might also like" |
| Tags/Categories | Taxonomy, tagging system |
| Favorites/Bookmarks | Save for later |
| Recent/History | Recently viewed, search history |

### Sub-Questions
1. What is searchable? (products, users, content, everything?)
2. Is full-text search needed or just field-based filtering?
3. What filters are available? (category, date, status, price range?)
4. Is autocomplete/type-ahead needed?
5. Are there recommendations? Based on what? (behavior, similarity, manual curation?)
6. Can users save/bookmark items?
7. Is there a browse/explore mode? (categories, trending, new?)

---

## Category K: Collaboration

**What it is:** How users interact with each other through the app.

| Sub-type | Examples |
|----------|----------|
| Comments | On items, documents, tasks |
| @Mentions | Notify specific users in content |
| Sharing | Share items via link, invite collaborators |
| Co-editing | Simultaneous editing (Google Docs style) |
| Reactions | Likes, upvotes, emoji reactions |
| Following | Follow users, topics, items for updates |
| Profiles | User profiles, avatars, bio |

### Sub-Questions
1. Can users comment on things? What things?
2. Is there @mentioning? Who can be mentioned?
3. Can users share content with others? How? (link, invite, public?)
4. Is real-time co-editing needed?
5. Are there reactions/votes? (likes, upvotes, stars?)
6. Can users follow other users or items?
7. Are there user profiles? What info is shown?

---

## Category L: Monetization

**What it is:** How the app makes money.

| Sub-type | Examples |
|----------|----------|
| Subscriptions | Monthly/annual plans, auto-renewal |
| One-time Purchase | Buy once, own forever |
| Freemium/Trials | Free tier with paid upgrades, time-limited trials |
| Usage-based/Metering | Pay per API call, per GB stored, per seat |
| Marketplace/Commission | Platform fee on transactions between users |
| Invoicing | B2B billing, custom invoices, net-30 terms |
| Refunds/Credits | Cancellation policy, prorated refunds |

### Sub-Questions
1. What's the revenue model? (subscription, one-time, freemium, marketplace?)
2. What plans/tiers exist? What does each include?
3. Is there a free tier? What's included?
4. Is there a trial period? How long?
5. What payment processor? (Stripe, PayPal, etc.)
6. How are refunds handled?
7. Is there usage metering? What's metered?
8. Are there team/organization billing features?

---

## Category M: Admin/Ops

**What it is:** Back-office tools for managing the system.

| Sub-type | Examples |
|----------|----------|
| Admin Dashboard | System overview, KPIs, health metrics |
| User Management | View/edit/ban users, impersonate |
| Content Moderation | Review flagged content, approve/reject |
| Feature Flags | Toggle features per user/group/environment |
| Analytics | Usage stats, funnel analysis, event tracking |
| Configuration | System settings, environment config |

### Sub-Questions
1. Is there an admin panel? What can admins do?
2. Can admins manage users? (view, edit, suspend, delete?)
3. Is there content moderation? What gets moderated?
4. Are there analytics dashboards? What metrics?
5. Can admins configure system settings?
6. Is there an audit log? (who did what, when?)
7. Are there feature flags or A/B testing needs?

---

## Category N: Infrastructure

**What it is:** System-level concerns that support the app.

| Sub-type | Examples |
|----------|----------|
| Caching | CDN, Redis, browser cache, service worker |
| Database Migrations | Schema versioning, zero-downtime migrations |
| Circuit Breakers | Graceful degradation when services fail |
| Auto-scaling | Handle traffic spikes, scale-to-zero |
| Logging | Structured logs, log aggregation |
| Monitoring/APM | Uptime checks, performance tracking, alerting |
| CI/CD | Automated testing, deployment pipelines |

### Sub-Questions
1. Where is the app hosted? (cloud, serverless, self-hosted?)
2. What's the expected traffic? (concurrent users, requests/sec?)
3. Is there a caching strategy needed?
4. How are deployments done? (CI/CD, manual, blue-green?)
5. What monitoring/alerting is needed?
6. What's the uptime requirement? (99.9%? 99.99%?)
7. Are there compliance requirements that affect infrastructure? (data residency, encryption at rest?)

---

## Quick Reference: Mechanism Identification Cheat Sheet

When the user says... → It maps to:

| User Says | Primary Mechanism | Secondary |
|-----------|------------------|-----------|
| "users can sign up and log in" | E (Auth) | F (Authorization) |
| "it sends you an email when..." | G (Communication) | I (Workflow) |
| "you can search for..." | J (Search) | D (Output) |
| "it scrapes data from websites" | H (Integration) | C (Processing) |
| "there's a subscription plan" | L (Monetization) | F (Authorization) |
| "users can upload files" | A (Input) | B (Storage) |
| "it generates a PDF report" | C (Processing) | D (Output) |
| "there's a dashboard showing..." | D (Output) | M (Admin) |
| "orders go through stages" | I (Workflow) | B (Storage) |
| "users can comment and like" | K (Collaboration) | G (Communication) |
| "admins can ban users" | M (Admin) | F (Authorization) |
| "it needs to handle 10K users" | N (Infrastructure) | B (Storage) |
| "users can share with a link" | K (Collaboration) | F (Authorization) |
| "it calculates a score based on..." | C (Processing) | D (Output) |
| "there's a chat feature" | G (Communication) | K (Collaboration) |
