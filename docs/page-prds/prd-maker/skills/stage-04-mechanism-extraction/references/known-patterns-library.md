# Known Patterns Library

Standard patterns for quick OBVIOUS classification. If a mechanism matches one of these patterns AND the boilerplate/stack supports it natively, classify as OBVIOUS and use the standard approach.

---

## Auth System
**Pattern:** Registration, login, password reset, session management, OAuth providers.
**Standard approach:** Use the boilerplate's auth provider (Supabase Auth, NextAuth, Firebase Auth, Clerk).
**When NEEDS_EVALUATION:** Custom auth flows, unusual session requirements, multi-tenant SSO, or boilerplate has no built-in auth.

## CRUD Operations
**Pattern:** Create, read, update, delete for any entity. Forms, lists, detail views.
**Standard approach:** Database table + ORM + REST/GraphQL endpoints + standard UI components.
**When NEEDS_EVALUATION:** Complex validation rules, multi-step creation wizards, optimistic updates with conflict resolution, or real-time collaborative editing.

## Dashboard
**Pattern:** Sidebar navigation + main content area + summary widgets/cards + charts.
**Standard approach:** Layout component + widget grid + charting library (Recharts, Chart.js).
**When NEEDS_EVALUATION:** Real-time streaming data, customizable widget layouts, complex drill-down analytics, or AI-generated insights.

## Settings Page
**Pattern:** Key-value preferences, toggles, dropdowns. User profile, notification preferences, theme.
**Standard approach:** Form with save button, stored in user profile table or key-value store.
**When NEEDS_EVALUATION:** Almost never. This is OBVIOUS in virtually all cases.

## Admin Panel
**Pattern:** User management (view/edit/ban), content moderation, system config, analytics.
**Standard approach:** Protected routes + admin role check + CRUD views for system entities.
**When NEEDS_EVALUATION:** Multi-tenant admin with org-level permissions, complex moderation workflows, or feature flag management systems.

## Search
**Pattern:** Text search across entities, filters, sorting, pagination.
**Standard approach:** Database full-text search (PostgreSQL `tsvector`, SQLite FTS5) or search service (Algolia, Meilisearch).
**When NEEDS_EVALUATION:** Semantic/vector search, faceted search across multiple entity types, search with AI-powered ranking, or search at >1M documents.

## Notifications
**Pattern:** In-app notifications (bell icon), email notifications, push notifications.
**Standard approach:** Database notification table + email service (Resend, SendGrid) + in-app polling or WebSocket.
**When NEEDS_EVALUATION:** Complex notification routing (different channels per event type), digest/batching logic, real-time push at scale, or notification preferences with granular controls.

## File Upload
**Pattern:** Single/multi file upload, image preview, progress bar, size/type validation.
**Standard approach:** Presigned URLs to S3/Supabase Storage + client-side validation + progress tracking.
**When NEEDS_EVALUATION:** Large file processing (video transcoding, PDF parsing), collaborative file editing, or complex file pipeline (upload → process → store → serve).

## Payment / Billing
**Pattern:** One-time payments, subscriptions, plan management, invoices.
**Standard approach:** Stripe integration with Checkout or Elements. Webhook for fulfillment.
**When NEEDS_EVALUATION:** Multiple payment processors, marketplace payments (split payouts), usage-based/metered billing, or cryptocurrency payments.

## Email System
**Pattern:** Transactional emails (welcome, reset, receipt), marketing emails, templates.
**Standard approach:** Email service (Resend, SendGrid, SES) + HTML templates.
**When NEEDS_EVALUATION:** Complex template engine, email builder UI, bulk sending with deliverability optimization, or multi-language email support.

## Credit / Token System
**Pattern:** Balance tracking, deduction on action, purchase/top-up, usage history.
**Standard approach:** Integer balance column + atomic decrement + purchase via Stripe + transaction log table.
**When NEEDS_EVALUATION:** Complex pricing tiers, expiring credits, shared team pools, or credits across multiple resource types with different costs.

## API / Integration Layer
**Pattern:** REST/GraphQL API for external consumers, webhook endpoints, third-party API consumption.
**Standard approach:** Standard API routes + API key auth + rate limiting middleware.
**When NEEDS_EVALUATION:** Multiple external APIs with fallback logic, complex data sync, real-time webhooks at scale, or building a public API platform.

---

## Decision Rule

1. Does the mechanism match a pattern above? → Likely OBVIOUS
2. Does the boilerplate handle it natively? → Definitely OBVIOUS
3. Does the "When NEEDS_EVALUATION" condition apply? → NEEDS_EVALUATION
4. Is the mechanism genuinely novel (no pattern match)? → NEEDS_EVALUATION
