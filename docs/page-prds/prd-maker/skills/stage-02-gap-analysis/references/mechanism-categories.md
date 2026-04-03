# Mechanism Categories A-N — Condensed Reference

> Source: `mechanism-identification-framework.md`. Stage 2 uses this to scan raw_input and generate sub-questions.

## Category A: Data Input
**What it is:** How data enters the system.
**Sub-types:** Forms, File Upload, Voice/Audio, Camera/OCR, Drag-and-Drop, Sensors/IoT, Copy/Paste & Import.
**Key sub-questions:**
1. What data types do users input? (text, numbers, dates, files, rich text?)
2. Multi-step forms or wizards?
3. File types accepted? Size limits?
4. Real-time validation or on-submit?
5. Bulk input needed? (CSV import, batch creation?)
6. Draft/autosave requirements?

## Category B: Data Storage
**What it is:** How and where data persists.
**Sub-types:** Relational DB, NoSQL/Document, Blob/File Storage, Cache Layer, Search Index, Audit Trail.
**Key sub-questions:**
1. Main entities/objects? (users, products, orders?)
2. Relationships between entities?
3. Schema fixed or flexible?
4. Data volume? (hundreds, thousands, millions?)
5. Data isolated per user/tenant or shared?
6. Audit/history requirement?

## Category C: Data Processing
**What it is:** Transformations, calculations, and logic.
**Sub-types:** Validation, Calculations, AI/ML, Batch Processing, Format Conversion, Filtering/Sorting.
**Key sub-questions:**
1. What calculations or transformations?
2. Trigger? (user action, schedule, event?)
3. Real-time or background?
4. AI/ML components? What do they do?
5. What happens if processing fails?

## Category D: Data Output
**What it is:** How data is displayed or delivered.
**Sub-types:** Lists/Tables, Charts/Graphs, Maps, Timelines, Kanban/Board, Export, Real-time Feeds.
**Key sub-questions:**
1. Main views/pages users see?
2. List views? Columns? Sortable? Filterable?
3. Dashboard/analytics views? What metrics?
4. Export needed? What formats?
5. Real-time updating? (live counters, feeds?)
6. Pagination? Infinite scroll?

## Category E: Authentication
**What it is:** How users prove who they are.
**Sub-types:** Email/Password, OAuth/Social, SSO, MFA, Magic Link, API Keys, Session Management.
**Key sub-questions:**
1. How do users sign up? (email/password, social, invite-only?)
2. Which OAuth providers?
3. MFA required?
4. Session management? (JWT, cookies?)
5. Password requirements? Reset flow?
6. Account deletion? What happens to data?

## Category F: Authorization
**What it is:** What users are allowed to do.
**Sub-types:** RBAC, ABAC, Resource Ownership, Multi-tenancy, Feature Flags, Rate Limiting.
**Key sub-questions:**
1. What roles exist? (admin, user, moderator?)
2. What can each role do?
3. Data isolated per user? Per org/team?
4. Subscription tiers that unlock features?
5. Can users share access? (invite, transfer?)
6. Row-level security?

## Category G: Communication
**What it is:** System-to-user and user-to-user communication.
**Sub-types:** Email, Push Notifications, In-App Notifications, SMS, Chat/Messaging, Webhooks, Activity Feeds.
**Key sub-questions:**
1. What events trigger notifications?
2. Which channels? (email, push, in-app?)
3. User notification preferences configurable?
4. Real-time chat needed? (1:1, group, channels?)
5. Webhooks to external services?

## Category H: Integration
**What it is:** Connections to external services.
**Sub-types:** REST/GraphQL Consumption, REST/GraphQL Exposure, Web Scraping, Payment Gateways, File/Data Sync, Social Media, Email Services.
**Key sub-questions:**
1. Which external services?
2. What data sent/received?
3. What happens when external service is down?
4. Does the app expose its own API?
5. Payment processor? Which one? What flows?

## Category I: Workflow
**What it is:** Multi-step processes and automation.
**Sub-types:** State Machines, Approval Flows, Cron Jobs, Queues, Event Triggers, Wizards/Multi-step, Retry/Recovery.
**Key sub-questions:**
1. Multi-step processes? What states?
2. What triggers state transitions?
3. Time-based triggers? (expire, remind?)
4. Scheduled/automated tasks?
5. Undo/rollback capability?

## Category J: Search & Discovery
**What it is:** How users find things.
**Sub-types:** Full-text Search, Faceted Search, Autocomplete, Recommendations, Tags/Categories, Favorites, Recent/History.
**Key sub-questions:**
1. What is searchable?
2. Full-text or just field-based filtering?
3. Filters? (category, date, status?)
4. Autocomplete needed?
5. Recommendations? Based on what?
6. Browse/explore mode?

## Category K: Collaboration
**What it is:** How users interact with each other.
**Sub-types:** Comments, @Mentions, Sharing, Co-editing, Reactions, Following, Profiles.
**Key sub-questions:**
1. Can users comment? On what?
2. @mentioning?
3. Share content? How? (link, invite, public?)
4. Real-time co-editing?
5. Reactions/votes? (likes, upvotes?)
6. User profiles? What info shown?

## Category L: Monetization
**What it is:** How the app makes money.
**Sub-types:** Subscriptions, One-time Purchase, Freemium/Trials, Usage-based, Marketplace/Commission, Invoicing, Refunds.
**Key sub-questions:**
1. Revenue model? (subscription, one-time, freemium, marketplace?)
2. Plans/tiers? What does each include?
3. Free tier? Trial period?
4. Payment processor?
5. Refund handling?
6. Team/org billing?

## Category M: Admin/Ops
**What it is:** Back-office management tools.
**Sub-types:** Admin Dashboard, User Management, Content Moderation, Feature Flags, Analytics, Configuration.
**Key sub-questions:**
1. Admin panel? What can admins do?
2. User management? (view, edit, suspend?)
3. Content moderation?
4. Analytics dashboards? What metrics?
5. Audit log?

## Category N: Infrastructure
**What it is:** System-level concerns.
**Sub-types:** Caching, DB Migrations, Circuit Breakers, Auto-scaling, Logging, Monitoring/APM, CI/CD.
**Key sub-questions:**
1. Where hosted? (cloud, serverless, self-hosted?)
2. Expected traffic?
3. Caching strategy needed?
4. Deployment method?
5. Monitoring/alerting needs?
6. Compliance requirements?

## Quick Signal Map

| User Says | Primary | Secondary |
|-----------|---------|-----------|
| "sign up and log in" | E | F |
| "sends an email when..." | G | I |
| "search for..." | J | D |
| "scrapes data from websites" | H | C |
| "subscription plan" | L | F |
| "upload files" | A | B |
| "generates a PDF" | C | D |
| "dashboard showing..." | D | M |
| "orders go through stages" | I | B |
| "comment and like" | K | G |
| "admins can ban users" | M | F |
| "handle 10K users" | N | B |
| "share with a link" | K | F |
| "calculates a score" | C | D |
| "chat feature" | G | K |
