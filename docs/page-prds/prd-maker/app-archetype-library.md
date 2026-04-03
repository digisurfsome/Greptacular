# App Archetype Library

> Used during Stage 2 (Gap Analysis) to reduce questioning overhead.
> Match the user's description to an archetype, load defaults, ask only about gaps.
>
> 8 archetypes x 14 mechanism categories (A-N) = pre-mapped defaults for fast gap analysis.
>
> **Relationship to pipeline:** Stage 2 (Gap Analysis) reads this library to identify which archetype(s) the user's idea matches. REQUIRED categories get auto-filled with default sub-types. OPTIONAL categories get one targeted question each. UNLIKELY categories are skipped unless the user specifically mentioned them.

---

## Archetype 1: Dashboard App

**One-line description:** An app that displays data, metrics, and analytics in visual layouts where users primarily read information with limited write operations like filters and date ranges.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Dashboards need filter controls, date range pickers, and configuration forms |
| B | Data Storage | REQUIRED | Relational DB or API | Data has to come from somewhere — either a local database or external API endpoints |
| C | Data Processing | REQUIRED | Calculations | Aggregations, statistics, and metric computations are the core value of a dashboard |
| D | Data Output | REQUIRED | Charts/Graphs | Visualizing data is the entire purpose of a dashboard app |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to see their personalized data |
| F | Authorization | OPTIONAL | — | Some dashboards have role-based views (admin vs viewer), but many are single-role |
| G | Communication | OPTIONAL | — | Scheduled report emails or threshold alerts are common but not universal |
| H | Integration | OPTIONAL | — | Many dashboards pull data from external APIs, but some use only local data |
| I | Workflow | UNLIKELY | — | Dashboards are read-heavy; they display results of processes, not manage processes |
| J | Search & Discovery | OPTIONAL | — | Filtering and searching through data points is common in data-heavy dashboards |
| K | Collaboration | UNLIKELY | — | Dashboards are typically solo viewing experiences, not collaborative |
| L | Monetization | UNLIKELY | — | Most dashboards are internal tools or features within a larger product, not standalone paid products |
| M | Admin/Ops | OPTIONAL | — | Some dashboards have admin settings for data sources or user management |
| N | Infrastructure | OPTIONAL | — | Caching matters for performance with large datasets, but not critical for MVP |

### Standard Pages

- **Overview Dashboard** — Primary view showing key metrics, KPI cards, and summary charts
- **Analytics Detail** — Drill-down view for a specific metric category with granular charts and data tables
- **Data Explorer** — Table view with sortable columns, filters, and search for raw data inspection
- **Login / Signup** — Authentication page with email/password or OAuth options
- **Settings & Preferences** — User preferences for date ranges, default views, notification thresholds
- **Report Builder** — Configure and export custom reports as PDF or CSV

### Example Apps

- **Google Analytics** — The canonical dashboard app: metrics, charts, date ranges, drill-downs, and export
- **Shopify Admin Dashboard** — E-commerce metrics (sales, orders, traffic) in visual layouts with filter controls
- **Datadog** — Infrastructure monitoring dashboard with real-time charts, alerts, and configurable views

---

## Archetype 2: Marketplace

**One-line description:** A two-sided platform connecting buyers and sellers (or providers and consumers) with listings, search, transactions, reviews, and trust mechanisms.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Sellers create listings with structured forms (title, description, price, images) |
| B | Data Storage | REQUIRED | Relational DB | Listings, users, transactions, and reviews form a heavily relational data model |
| C | Data Processing | REQUIRED | Validation | Pricing calculations, availability checks, matching algorithms, and commission computation |
| D | Data Output | REQUIRED | Lists/Tables | Browsing listings, search results, and order history are core read operations |
| E | Authentication | REQUIRED | Email/Password + OAuth | Both buyers and sellers need accounts; social login reduces signup friction |
| F | Authorization | REQUIRED | RBAC | Distinct buyer, seller, and admin roles with different permissions and views |
| G | Communication | REQUIRED | In-App Notifications | Order updates, new messages, review requests — both sides need real-time alerts |
| H | Integration | REQUIRED | Payment Gateways | Transactions between buyers and sellers require Stripe/PayPal with escrow or split payments |
| I | Workflow | REQUIRED | State Machines | Orders flow through states: pending → paid → shipped → delivered → reviewed |
| J | Search & Discovery | REQUIRED | Faceted Search | Finding products/services by category, price, location, rating is a core user action |
| K | Collaboration | UNLIKELY | — | Reviews/ratings are feedback, not collaboration; co-editing, @mentions, and following are not marketplace mechanics |
| L | Monetization | REQUIRED | Marketplace/Commission | Platform takes a percentage of each transaction — this is the business model |
| M | Admin/Ops | REQUIRED | Content Moderation | Dispute resolution, listing approval, seller verification, and fraud detection are essential |
| N | Infrastructure | UNLIKELY | — | CDN and caching help at scale but MVP marketplaces run on basic hosting without special infra |

### Standard Pages

- **Home / Browse** — Featured listings, categories, and promotional sections
- **Search Results** — Filtered and sorted listings with faceted search sidebar
- **Listing Detail** — Full listing information with images, description, price, seller info, and reviews
- **Create / Edit Listing** — Multi-step form for sellers to create or update listings
- **Shopping Cart / Checkout** — Cart management and payment flow for buyers
- **Order Management** — Order history and status tracking for both buyers and sellers
- **Seller Dashboard** — Sales metrics, active listings, earnings, and payout information
- **User Profile** — Public profile showing ratings, reviews, and listing history

### Example Apps

- **Airbnb** — Two-sided marketplace connecting hosts and guests with listings, search, booking workflow, reviews, and platform commission
- **Etsy** — Seller storefronts, product search, cart/checkout, reviews, and transaction-based monetization
- **Uber** — Provider-consumer matching with real-time availability, pricing, payment processing, and rating system

---

## Archetype 3: Chat / Messaging App

**One-line description:** A real-time communication app where users send and receive messages in 1:1, group, or channel-based conversations with presence indicators and notifications.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Message composer is a text input with optional rich formatting, emoji, and attachments |
| B | Data Storage | REQUIRED | NoSQL/Document | Messages are append-heavy, nested in conversations — document store fits naturally |
| C | Data Processing | OPTIONAL | — | Media processing (image resizing, link previews) and message formatting are common but not universal |
| D | Data Output | REQUIRED | Real-time Feeds | Message streams update live as new messages arrive — this is the core display pattern |
| E | Authentication | REQUIRED | Email/Password | Users need accounts tied to their identity for messaging |
| F | Authorization | OPTIONAL | — | Channel permissions and admin roles exist in some chat apps but not all (1:1 apps skip this) |
| G | Communication | REQUIRED | Chat/Messaging + Push Notifications | Real-time messaging IS the app; push notifications alert users when they are not in the app |
| H | Integration | OPTIONAL | — | Bots, webhooks, and external service connections are common in team chat, rare in personal chat |
| I | Workflow | UNLIKELY | — | Messages are sent and received — there are no multi-step state machines in core messaging |
| J | Search & Discovery | OPTIONAL | — | Message search and people/channel discovery are common in larger chat apps |
| K | Collaboration | REQUIRED | Profiles | User presence (online/offline/away), status messages, and contact lists are core to messaging |
| L | Monetization | UNLIKELY | — | Most chat apps are free for users; monetization (if any) is enterprise pricing, not per-message |
| M | Admin/Ops | OPTIONAL | — | Team/workspace administration exists in business chat apps but not personal messaging |
| N | Infrastructure | OPTIONAL | — | WebSocket infrastructure and message caching matter for performance but are implementation details |

### Standard Pages

- **Login / Signup** — Authentication with phone number or email verification
- **Conversation List (Inbox)** — All active conversations sorted by recency with unread indicators
- **Chat Room / Conversation** — Message thread with real-time updates, typing indicators, and message input
- **Contact / People List** — User directory for starting new conversations or adding to groups
- **User Profile** — Avatar, display name, status, and contact information
- **Settings** — Notification preferences, privacy controls, account management

### Example Apps

- **WhatsApp** — 1:1 and group messaging with end-to-end encryption, media sharing, and presence indicators
- **Slack** — Channel-based team messaging with threads, search, integrations, and workspace administration
- **Discord** — Server/channel structure with voice chat, roles, and bot ecosystem for communities

---

## Archetype 4: CRUD / Tool

**One-line description:** A utility app focused on creating, reading, updating, and deleting structured data — task managers, note apps, inventory trackers, CRM tools, and spreadsheet-like apps.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Creating and editing records through structured forms is the primary user action |
| B | Data Storage | REQUIRED | Relational DB | Structured data with defined fields and relationships (tasks, contacts, inventory items) |
| C | Data Processing | REQUIRED | Validation | Input validation, business rule checks, and data consistency enforcement on every save |
| D | Data Output | REQUIRED | Lists/Tables | The main view is always a list or table of records with sorting and filtering |
| E | Authentication | REQUIRED | Email/Password | Users need accounts to store and retrieve their data |
| F | Authorization | OPTIONAL | — | Resource ownership (users see only their own data) is common; team roles are less common |
| G | Communication | OPTIONAL | — | Email notifications for deadlines or changes are nice-to-have, not core |
| H | Integration | OPTIONAL | — | Import/export and API connections to other tools are common in mature CRUD apps |
| I | Workflow | OPTIONAL | — | Some tools have status workflows (to-do → in progress → done) but many are flat CRUD |
| J | Search & Discovery | OPTIONAL | — | Searching and filtering records becomes important as data volume grows |
| K | Collaboration | OPTIONAL | — | Sharing records and team collaboration exist in some tools but many are single-user |
| L | Monetization | UNLIKELY | — | Many CRUD tools are internal/personal utilities, not standalone paid products |
| M | Admin/Ops | UNLIKELY | — | Small-team tools rarely need admin panels or content moderation |
| N | Infrastructure | UNLIKELY | — | Simple CRUD apps run on basic hosting with no special infrastructure needs |

### Standard Pages

- **Login / Signup** — Authentication page
- **Item List** — Main view showing all records in a table or card grid with sort/filter controls
- **Item Detail** — Full record view with all fields, history, and related data
- **Create / Edit Form** — Form for creating new records or editing existing ones
- **Dashboard / Overview** — Summary statistics (total items, items by status, recent activity)
- **Settings** — User preferences, data export options, account management

### Example Apps

- **Todoist** — Task management CRUD with projects, priorities, due dates, and status tracking
- **Airtable** — Spreadsheet-database hybrid for structured data with views, filters, and formulas
- **Google Keep** — Minimal note-taking CRUD with labels, colors, and search

---

## Archetype 5: Social Platform

**One-line description:** An app centered on user-generated content, social graphs (following/followers), algorithmic or chronological feeds, and engagement mechanics like likes, comments, and shares.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms + File Upload | Users create posts with text, images, and video — both form fields and media upload |
| B | Data Storage | REQUIRED | Relational DB + Blob Storage | User data and relationships in a relational DB; media files in blob/object storage |
| C | Data Processing | REQUIRED | Filtering/Sorting | Feed ranking, content recommendations, and trending calculations are core to engagement |
| D | Data Output | REQUIRED | Real-time Feeds | The social feed — an infinite-scroll stream of content from followed users and recommendations |
| E | Authentication | REQUIRED | OAuth/Social | Social login (Google, Apple) is natural for social platforms and reduces signup friction |
| F | Authorization | REQUIRED | Resource Ownership | Users own their posts; privacy settings control who sees what (public, friends-only, private) |
| G | Communication | REQUIRED | In-App Notifications | "Someone liked your post" and "New follower" notifications are essential for engagement loops |
| H | Integration | OPTIONAL | — | Social sharing to other platforms and link embeds are common but not required for core function |
| I | Workflow | UNLIKELY | — | Social platforms are event-driven (post, like, comment), not process-driven with state machines |
| J | Search & Discovery | REQUIRED | Full-text Search | Finding people, hashtags, and content is a core navigation mechanism |
| K | Collaboration | REQUIRED | Comments + Reactions + Following | Likes, comments, shares, and follow relationships ARE the social platform |
| L | Monetization | UNLIKELY | — | Most social platforms defer monetization; MVP launches are free and ad-free |
| M | Admin/Ops | REQUIRED | Content Moderation | User-generated content requires moderation for spam, harassment, and policy violations |
| N | Infrastructure | OPTIONAL | — | CDN for media delivery and caching for feeds help at scale but are not MVP-critical |

### Standard Pages

- **Login / Signup** — Social login and email registration
- **Feed (Home Timeline)** — Scrollable stream of posts from followed users and recommendations
- **User Profile** — Bio, avatar, post history, follower/following counts, and follow button
- **Post Detail** — Single post with full comments thread and engagement buttons
- **Discover / Explore** — Trending content, recommended users, hashtag browsing
- **Notifications** — Activity feed showing likes, comments, follows, and mentions
- **Create Post** — Composer for text, images, video with preview
- **Settings** — Account, privacy, notification preferences, blocked users

### Example Apps

- **Instagram** — Photo/video sharing with feed, stories, explore, likes, comments, and follower graph
- **Twitter/X** — Short-form text posts with retweets, likes, threads, and trending topics
- **Reddit** — Community-based content with upvotes, comments, subreddits, and content discovery

---

## Archetype 6: Wizard / Onboarding Flow

**One-line description:** A step-by-step guided process that collects information or walks users through a setup, with linear or branching progression, validation at each step, and a final summary or confirmation.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | Multi-step form input is the entire core mechanic — each step collects specific data |
| B | Data Storage | REQUIRED | Relational DB | Collected data must persist, including partial progress for resume-later capability |
| C | Data Processing | REQUIRED | Validation | Each step validates before allowing progression; final step may trigger calculations or decisions |
| D | Data Output | REQUIRED | Lists/Tables | Summary/review screen shows all collected data before final submission |
| E | Authentication | OPTIONAL | — | Some wizards are part of signup (pre-auth); others require login first — depends on context |
| F | Authorization | UNLIKELY | — | Wizards are typically single-path with no role differentiation |
| G | Communication | OPTIONAL | — | Confirmation emails after completion are common but not part of the core wizard flow |
| H | Integration | OPTIONAL | — | Wizard results often get sent to external systems (CRM, email service, payment processor) |
| I | Workflow | REQUIRED | Wizards/Multi-step | Step-by-step progression with branching logic IS a workflow by definition |
| J | Search & Discovery | UNLIKELY | — | Linear guided processes have no search — users are led through a fixed path |
| K | Collaboration | UNLIKELY | — | Wizards are solo experiences — one user filling out one flow |
| L | Monetization | UNLIKELY | — | Wizards collect data or configure settings; they do not sell anything directly |
| M | Admin/Ops | UNLIKELY | — | Simple flow with no admin layer needed |
| N | Infrastructure | UNLIKELY | — | Wizards are lightweight with no special infrastructure demands |

### Standard Pages

- **Welcome / Intro Screen** — Explains what the wizard does and what information will be needed
- **Step 1-N (Data Collection Steps)** — Each step focuses on one category of information with validation
- **Conditional Branch Screen** — Optional path that appears based on previous answers
- **Review / Summary** — Shows all collected data in a readable format for user confirmation
- **Confirmation / Success** — Final screen confirming submission with next steps or results

### Example Apps

- **TurboTax** — Step-by-step tax filing wizard that collects income, deductions, and credits through guided questions
- **Typeform** — Conversational form builder where each question is one step with smooth transitions
- **Wix Site Builder Setup** — Guided onboarding that asks about business type, goals, and preferences to generate a starter site

---

## Archetype 7: Landing Page

**One-line description:** A marketing or informational page focused on conversion with static content, CTAs, signup forms, pricing tables, and social proof — minimal backend logic.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | OPTIONAL | — | Signup forms and contact forms are common but not every landing page has them |
| B | Data Storage | UNLIKELY | — | Landing pages are mostly static; at most they store form submissions or email signups |
| C | Data Processing | UNLIKELY | — | Static content pages have no data processing requirements |
| D | Data Output | REQUIRED | Lists/Tables | Feature comparison tables, pricing tiers, testimonial cards — structured content display |
| E | Authentication | UNLIKELY | — | Landing pages are public; authentication belongs to the product they link to |
| F | Authorization | UNLIKELY | — | Everyone sees the same page — no roles or permissions |
| G | Communication | OPTIONAL | — | Newsletter signup and email capture are common conversion tactics |
| H | Integration | OPTIONAL | — | Analytics (Google Analytics), email services (Mailchimp), and CRM integrations are common |
| I | Workflow | UNLIKELY | — | Static pages have no multi-step processes |
| J | Search & Discovery | UNLIKELY | — | Landing pages are small enough that search is unnecessary |
| K | Collaboration | UNLIKELY | — | Landing pages are not collaborative experiences |
| L | Monetization | UNLIKELY | — | The landing page drives users TO a monetized product — it does not monetize itself |
| M | Admin/Ops | UNLIKELY | — | Static content with no admin layer needed |
| N | Infrastructure | OPTIONAL | — | CDN and caching improve load speed, which directly affects conversion rates |

### Standard Pages

- **Hero / Home** — Primary landing section with headline, value proposition, and main CTA
- **Features / Benefits** — Detailed breakdown of what the product offers with icons or illustrations
- **Pricing** — Plan comparison table with feature lists and signup buttons per tier
- **Testimonials / Social Proof** — Customer quotes, logos, case study snippets, and trust badges
- **FAQ** — Common questions and answers to reduce signup friction
- **Contact / Signup** — Form for leads, demo requests, or newsletter subscription

### Example Apps

- **Stripe's Homepage** — Clean, conversion-focused landing with product explanation, feature sections, pricing, and developer-friendly CTAs
- **Linear's Homepage** — Minimal, fast landing page with feature highlights, social proof, and clear signup flow
- **Notion's Homepage** — Template-rich landing page with use case sections, pricing comparison, and customer logos

---

## Archetype 8: SaaS Product

**One-line description:** A subscription-based software product with user accounts, feature tiers, team management, billing, and an admin layer — typically combines CRUD + Dashboard mechanics with a unique value proposition.

### Mechanism Requirements

| Category | Name | Classification | Default Sub-type | Notes |
|----------|------|---------------|-----------------|-------|
| A | Data Input | REQUIRED | Forms | User data entry, settings configuration, and content creation forms |
| B | Data Storage | REQUIRED | Relational DB | User data, subscription records, team structures, and product-specific data |
| C | Data Processing | REQUIRED | Calculations | Business logic specific to the SaaS value prop plus usage metering and billing calculations |
| D | Data Output | REQUIRED | Lists/Tables + Charts | Product-specific views plus usage dashboards and account overview |
| E | Authentication | REQUIRED | Email/Password + OAuth | Multiple auth methods reduce friction; enterprise customers may need SSO |
| F | Authorization | REQUIRED | RBAC + Feature Flags | Subscription tiers gate features; team roles control access within organizations |
| G | Communication | REQUIRED | Email | Transactional emails (welcome, invoice, password reset), onboarding sequences, and product updates |
| H | Integration | OPTIONAL | — | Many SaaS products integrate with other tools, but the core product may stand alone |
| I | Workflow | UNLIKELY | — | Default SaaS products are CRUD-based; complex state machines and approval flows are feature-specific, not archetype-standard |
| J | Search & Discovery | OPTIONAL | — | Depends on data volume — products with many records need search, simple tools may not |
| K | Collaboration | OPTIONAL | — | Team features (shared workspaces, comments, mentions) are common in B2B SaaS but not universal |
| L | Monetization | REQUIRED | Subscriptions | Monthly/annual billing with plan tiers is the defining characteristic of SaaS |
| M | Admin/Ops | REQUIRED | Admin Dashboard | System health, user management, subscription analytics, and feature flag controls |
| N | Infrastructure | UNLIKELY | — | Monitoring, auto-scaling, and CI/CD become important at scale but MVP SaaS runs on basic hosting |

### Standard Pages

- **Marketing / Landing Page** — Public-facing page explaining the product with pricing and signup CTA
- **Login / Signup** — Multi-method authentication with social login and SSO options
- **Main Workspace / Dashboard** — The core product experience where users spend most of their time
- **Account Settings** — Profile, password, notification preferences, and connected accounts
- **Billing / Subscription** — Current plan, usage metrics, payment method, invoice history, and upgrade options
- **Team Management** — Invite members, assign roles, manage permissions within an organization
- **Admin Panel** — Internal dashboard for system operators showing user metrics, health, and config

### Example Apps

- **Figma** — Design tool SaaS with team workspaces, subscription tiers (free/pro/org), real-time collaboration, and admin controls
- **Notion** — Workspace SaaS combining notes, databases, and docs with team plans, member management, and usage-based features
- **Canva** — Design SaaS with free/pro/team tiers, template marketplace, team brand kits, and asset management

---

## How to Use This Library

These instructions are for the Stage 2 (Gap Analysis) agent. Follow them mechanically.

### Step 1: Match

Read the user's raw idea description from Stage 1. Identify which archetype(s) it most closely matches.

**Matching rules:**
- An app can match MULTIPLE archetypes. Example: "a marketplace with analytics" = Marketplace + Dashboard.
- Match based on the PRIMARY user action described:
  - User views data/metrics → **Dashboard**
  - User buys/sells between two parties → **Marketplace**
  - User sends/receives messages in real time → **Chat / Messaging**
  - User creates/edits/deletes records → **CRUD / Tool**
  - User posts content and follows other users → **Social Platform**
  - User walks through a step-by-step process → **Wizard / Onboarding**
  - The output is a marketing/info page → **Landing Page**
  - User pays a subscription for ongoing software access → **SaaS Product**
- If the description mentions subscription billing or team management alongside another archetype, ALSO match **SaaS Product** and union the mechanism maps.
- If multiple archetypes match, union all REQUIRED categories from each. A category that is REQUIRED in ANY matched archetype becomes REQUIRED in the combined map.

### Step 2: Load Defaults

For the matched archetype(s), load all REQUIRED mechanism categories with their default sub-types. These are pre-filled into the context packet.

**Rules:**
- Do NOT ask the user about REQUIRED categories unless their description explicitly contradicts the default. Example: if their Dashboard description says "no user accounts needed," then E (Authentication) drops from REQUIRED to inapplicable despite the archetype default.
- If multiple archetypes matched, use the most specific default sub-type from whichever archetype is more relevant. Example: if both Dashboard (Forms) and Marketplace (Forms) mark A as REQUIRED, keep "Forms" as the default.

### Step 3: Ask About OPTIONAL

For each OPTIONAL category in the combined map, ask the user ONE targeted question. Use this format:

> "Does your app need **[category name]**? For example, [archetype-specific example relevant to their idea]."

**Rules:**
- Phrase the example in terms of THEIR app, not generic terms. Example: for a recipe-sharing app (Social archetype), ask "Does your app need **monetization**? For example, a premium tier that unlocks exclusive recipes?" — not "Does your app need monetization? For example, subscriptions."
- Ask all OPTIONAL questions in a single batch, not one at a time.
- If the user already mentioned something that maps to an OPTIONAL category in their rant, skip the question — mark it as needed and move to sub-questions.

### Step 4: Skip UNLIKELY

Do NOT ask about UNLIKELY categories. Period.

**Exception:** If the user's Stage 1 description specifically mentions something that maps to an UNLIKELY category, override the UNLIKELY classification and treat it as REQUIRED. Example: if a Dashboard user says "and it should have a chat feature," that maps to G (Communication) and K (Collaboration), which are UNLIKELY for Dashboards. Override them to REQUIRED and ask sub-questions.

### Step 5: Deep-Dive on Mentioned

For every category that is active (either REQUIRED by archetype, confirmed OPTIONAL by user, or mentioned in the rant), ask the sub-questions from the `mechanism-identification-framework.md` to get specifics.

**Rules:**
- For REQUIRED categories with default sub-types, start with a confirming question: "For data storage, the standard approach is a relational database. Does that work, or do you need something different?"
- For user-confirmed OPTIONAL categories, ask the full sub-question set.
- For rant-mentioned categories, ask only the sub-questions that the rant didn't already answer.

### Step 6: Handle No-Match

If the user's idea does not match ANY archetype:

1. State: "Your app doesn't fit a standard archetype, so I need to ask about all mechanism categories."
2. Fall back to asking about ALL 14 categories (A-N) one by one using the standard questions from the mechanism identification framework.
3. Flag `archetype_match: "none"` in the context packet so downstream stages know this was a full-coverage gap analysis.

### Step 7: Handle Hybrid

If the user's idea matches 2 or more archetypes:

1. State: "Your app looks like a combination of **[Archetype A]** and **[Archetype B]**. I'm loading the standard requirements for both."
2. Union the REQUIRED categories (anything REQUIRED in either archetype is REQUIRED in the combined map).
3. For categories where both archetypes have different default sub-types, ask: "For [category], [Archetype A] apps typically use [sub-type A] while [Archetype B] apps typically use [sub-type B]. Which fits your app better?"
4. For OPTIONAL categories, ask about any that are OPTIONAL in either archetype (even if UNLIKELY in the other).
5. Flag `archetype_match: ["Archetype A", "Archetype B"]` in the context packet.

---

## Quick Reference: Classification Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY |
|-----------|----------|----------|----------|
| Dashboard App | 5 (A, B, C, D, E) | 6 (F, G, H, J, M, N) | 3 (I, K, L) |
| Marketplace | 12 (A, B, C, D, E, F, G, H, I, J, L, M) | 0 | 2 (K, N) |
| Chat / Messaging | 6 (A, B, D, E, G, K) | 6 (C, F, H, J, M, N) | 2 (I, L) |
| CRUD / Tool | 5 (A, B, C, D, E) | 6 (F, G, H, I, J, K) | 3 (L, M, N) |
| Social Platform | 10 (A, B, C, D, E, F, G, J, K, M) | 2 (H, N) | 2 (I, L) |
| Wizard / Onboarding | 5 (A, B, C, D, I) | 3 (E, G, H) | 6 (F, J, K, L, M, N) |
| Landing Page | 1 (D) | 4 (A, G, H, N) | 9 (B, C, E, F, I, J, K, L, M) |
| SaaS Product | 9 (A, B, C, D, E, F, G, L, M) | 3 (H, J, K) | 2 (I, N) |

> **Note on Marketplace having 0 OPTIONAL:** Marketplaces are inherently complex — every mechanism is either definitely needed (REQUIRED) or genuinely irrelevant (UNLIKELY). This means the gap analysis agent asks zero OPTIONAL questions for a pure marketplace, but has 12 REQUIRED categories to deep-dive on. Expect a longer conversation.

---

## Archetype Complexity Ranking

For agent planning and user expectation-setting:

| Rank | Archetype | Active Categories | Build Complexity |
|------|-----------|-------------------|-----------------|
| 1 | Landing Page | 1 REQUIRED + 4 OPTIONAL = ~3-5 active | Low |
| 2 | Wizard / Onboarding | 5 REQUIRED + 3 OPTIONAL = ~6-7 active | Low-Medium |
| 3 | CRUD / Tool | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 4 | Dashboard App | 5 REQUIRED + 6 OPTIONAL = ~7-9 active | Medium |
| 5 | Chat / Messaging | 6 REQUIRED + 6 OPTIONAL = ~8-10 active | Medium-High |
| 6 | Social Platform | 10 REQUIRED + 2 OPTIONAL = ~10-11 active | High |
| 7 | SaaS Product | 9 REQUIRED + 3 OPTIONAL = ~10-11 active | High |
| 8 | Marketplace | 12 REQUIRED + 0 OPTIONAL = ~12 active | Very High |
