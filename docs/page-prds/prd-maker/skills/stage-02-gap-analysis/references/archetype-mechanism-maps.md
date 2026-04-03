# Archetype Mechanism Maps

> Quick lookup: REQUIRED (R), OPTIONAL (O), UNLIKELY (U) per archetype per A-N category.
> Source: `app-archetype-library.md`. Used by Stage 2 to determine which gaps to ask about.

## Combined Matrix

| Cat | Name | Dashboard | Marketplace | Chat | CRUD/Tool | Social | Wizard | Landing | SaaS |
|-----|------|-----------|-------------|------|-----------|--------|--------|---------|------|
| A | Data Input | R | R | R | R | R | R | O | R |
| B | Data Storage | R | R | R | R | R | R | U | R |
| C | Data Processing | R | R | O | R | R | R | U | R |
| D | Data Output | R | R | R | R | R | R | R | R |
| E | Authentication | R | R | R | R | R | O | U | R |
| F | Authorization | O | R | O | O | R | U | U | R |
| G | Communication | O | R | R | O | R | O | O | R |
| H | Integration | O | R | O | O | O | O | O | O |
| I | Workflow | U | R | U | O | U | R | U | U |
| J | Search & Discovery | O | R | O | O | R | U | U | O |
| K | Collaboration | U | U | R | O | R | U | U | O |
| L | Monetization | U | R | U | U | U | U | U | R |
| M | Admin/Ops | O | R | O | U | R | U | U | R |
| N | Infrastructure | O | U | O | U | O | U | O | U |

## REQUIRED Category Counts

| Archetype | REQUIRED | OPTIONAL | UNLIKELY | Total Active (R+O) |
|-----------|----------|----------|----------|-------------------|
| Dashboard | 5 (ABCDE) | 6 (FGHJMN) | 3 (IKL) | 11 |
| Marketplace | 12 (ABCDEFGHIJLM) | 0 | 2 (KN) | 12 |
| Chat | 6 (ABDEGK) | 6 (CFHJMN) | 2 (IL) | 12 |
| CRUD/Tool | 5 (ABCDE) | 6 (FGHIJK) | 3 (LMN) | 11 |
| Social | 10 (ABCDEFGJKM) | 2 (HN) | 2 (IL) | 12 |
| Wizard | 5 (ABCDI) | 3 (EGH) | 6 (FJKLMN) | 8 |
| Landing | 1 (D) | 4 (AGHN) | 9 (BCEFIJKLM) | 5 |
| SaaS | 9 (ABCDEFGLM) | 3 (HJK) | 2 (IN) | 12 |

## Default Sub-Types per Archetype (REQUIRED categories only)

### Dashboard
- A: Forms (filter controls, date pickers)
- B: Relational DB or API
- C: Calculations (aggregations, statistics)
- D: Charts/Graphs
- E: Email/Password

### Marketplace
- A: Forms (listing creation)
- B: Relational DB
- C: Validation (pricing, availability)
- D: Lists/Tables (browse listings)
- E: Email/Password + OAuth
- F: RBAC (buyer/seller/admin)
- G: In-App Notifications
- H: Payment Gateways (Stripe/PayPal)
- I: State Machines (order flow)
- J: Faceted Search
- L: Marketplace/Commission
- M: Content Moderation

### Chat / Messaging
- A: Forms (message composer)
- B: NoSQL/Document
- D: Real-time Feeds
- E: Email/Password
- G: Chat/Messaging + Push Notifications
- K: Profiles (presence, status)

### CRUD / Tool
- A: Forms (record creation/editing)
- B: Relational DB
- C: Validation
- D: Lists/Tables
- E: Email/Password

### Social Platform
- A: Forms + File Upload
- B: Relational DB + Blob Storage
- C: Filtering/Sorting (feed ranking)
- D: Real-time Feeds
- E: OAuth/Social
- F: Resource Ownership (privacy)
- G: In-App Notifications
- J: Full-text Search
- K: Comments + Reactions + Following
- M: Content Moderation

### Wizard / Onboarding
- A: Forms (multi-step)
- B: Relational DB (persist progress)
- C: Validation (per-step)
- D: Lists/Tables (summary/review)
- I: Wizards/Multi-step

### Landing Page
- D: Lists/Tables (feature tables, pricing)

### SaaS Product
- A: Forms (data entry, settings)
- B: Relational DB
- C: Calculations (business logic, metering)
- D: Lists/Tables + Charts
- E: Email/Password + OAuth
- F: RBAC + Feature Flags (tier gating)
- G: Email (transactional)
- L: Subscriptions
- M: Admin Dashboard

## Multi-Archetype Union Rules

When multiple archetypes match:
1. A category REQUIRED in ANY archetype -> REQUIRED in combined map.
2. A category OPTIONAL in one and UNLIKELY in another -> OPTIONAL wins.
3. For conflicting default sub-types, ask the user which fits.
4. SaaS always adds: F (RBAC + Feature Flags), G (Email), L (Subscriptions), M (Admin).
