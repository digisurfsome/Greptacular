# Open Source CRM Comparison — For Affiliate Offer Management

> **Goal:** Find a self-hosted, customizable open-source CRM to organize affiliate offers, agency partnerships, email campaigns, and offer layering pipelines. Must be code-customizable so we can build exactly what we need without monthly fees.

---

## The Top 6 Contenders

### 1. Twenty CRM — THE FRONTRUNNER

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/twentyhq/twenty |
| **Stars** | 40,400+ |
| **License** | AGPL v3 (free to self-host, modify, and use commercially) |
| **Tech Stack** | React + Node.js + TypeScript + PostgreSQL |
| **Deploy** | Docker Compose (1-click setup) |
| **Backed By** | Y Combinator, HubSpot founder, Runa Capital, Automattic. $5M raised. |
| **Contributors** | 300+ |

**Why It's #1 for This Use Case:**
- Modern UI inspired by Notion/Airtable/Linear — not clunky like old CRMs
- **Custom Objects** — Create any data type (Affiliate Offers, Agency Partners, Email Sequences, etc.) with the same first-class treatment as built-in objects
- **Full API** — REST + GraphQL, auto-generated for YOUR custom data model. Batch operations (60 records/call)
- **Webhooks** — Real-time notifications when CRM events happen. Push data to your email system, automation tools, etc.
- **Pipeline Visualization** — Kanban boards for tracking offers through stages
- **Email Integration** — IMAP support (behind feature flag), SMTP coming
- **Self-hosted** — Full data ownership. No monthly fees. No vendor lock-in.
- Clean, well-documented codebase. Easy to extend.

**Limitations:**
- AGPL license (if you redistribute modified code, you must open-source it — fine for internal use)
- Still growing — not as feature-complete as Salesforce (but that's the point)
- No built-in affiliate tracking (but custom objects solve this)
- No offline mode

---

### 2. EspoCRM — THE MATURE WORKHORSE

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/espocrm/espocrm |
| **Stars** | ~2,800 |
| **License** | AGPL v3 |
| **Tech Stack** | PHP + MySQL/MariaDB + JavaScript (Backbone.js frontend) |
| **Deploy** | Docker or traditional LAMP stack |

**Strengths:**
- **Most mature & feature-complete** of the bunch — contacts, pipelines, email, cases, quotes, campaigns all built-in
- **No-code customization** — Entity Manager lets you create custom entities, fields, relationships, and layouts WITHOUT coding
- **Formula scripting** — Built-in scripting for business logic
- **BPM & Workflow engine** — Visual workflow builder for automation
- **Integrations** — REST API + Zapier + Make + Google + Outlook + VoIP
- **Role-based security** — Field-level permissions, GDPR tools, 2FA
- **Kanban boards** — Pipeline visualization out of the box
- Huge community, tons of extensions available

**Limitations:**
- PHP-based (older stack, but very stable)
- UI feels more traditional compared to Twenty
- No built-in affiliate module (but easy to build with Entity Manager)

---

### 3. Krayin CRM — THE MIT LICENSE PICK

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/krayin/laravel-crm |
| **Stars** | Growing |
| **License** | MIT (most permissive — do anything you want) |
| **Tech Stack** | Laravel (PHP) + Vue.js |
| **Deploy** | Standard Laravel deployment |

**Strengths:**
- **MIT License** — Only CRM on this list with truly permissive licensing. No copyleft restrictions.
- Clean Laravel codebase — easy to customize at the core level
- Lead management, email campaigns, sales pipelines, activity tracking
- Plugin architecture for extensions
- Free forever with free updates

**Limitations:**
- Smaller community than Twenty or EspoCRM
- Limited documentation
- Basic reporting tools
- No official mobile app
- Fewer integrations out of the box

---

### 4. Atomic CRM — THE LIGHTWEIGHT OPTION

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/marmelab/atomic-crm |
| **Stars** | Growing |
| **License** | Check repo (contaminating license noted in benchmarks) |
| **Tech Stack** | React + shadcn/ui + Supabase + PostgreSQL |
| **Deploy** | Docker (Vite + Supabase + Postgres) |

**Strengths:**
- Only **15,000 lines of code** — extremely easy to understand and modify
- Built with modern React + shadcn/ui (beautiful UI out of the box)
- Supabase backend = built-in auth, real-time subscriptions, and REST/GraphQL API
- Custom fields, theming, component replacement all supported
- Great starting point if you want to build something very custom on top

**Limitations:**
- Minimal features compared to others — it's a starting skeleton
- Small team/community
- You'd need to build more yourself
- License concerns

---

### 5. ERPNext / Frappe CRM — THE ENTERPRISE OPTION

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/frappe/crm (CRM) / github.com/frappe/erpnext (ERP) |
| **Stars** | ERPNext: 22,000+ / Frappe CRM: 2,400+ |
| **License** | GPL v3 (ERPNext) / AGPL v3 (Frappe CRM) |
| **Tech Stack** | Python (Frappe Framework) + MariaDB + JavaScript |
| **Deploy** | Docker or Frappe Bench |

**Strengths:**
- **Full ERP** — CRM + accounting + invoicing + inventory + HR + project management
- Low-code customization — drag-and-drop data models and workflows
- Frappe CRM is lightweight and focused if you just want CRM
- Huge community (22K+ stars)
- AI extensions being built on the framework

**Limitations:**
- ERPNext is overkill if you just need CRM
- Frappe framework has a learning curve
- Heavier resource requirements

---

### 6. NocoBase — THE NO-CODE BUILDER

| Attribute | Details |
|-----------|---------|
| **GitHub** | github.com/nocobase/nocobase |
| **Stars** | 15,000+ |
| **License** | AGPL v3 (with commercial license option) |
| **Tech Stack** | Node.js + React + PostgreSQL |
| **Deploy** | Docker |

**Strengths:**
- **Not just a CRM — it's a platform to BUILD any business app**
- Visual data modeling — define your own structures, workflows, forms, permissions
- Plugin architecture for everything
- Could build CRM + affiliate tracker + email pipeline manager all in one
- AI-enabled features

**Limitations:**
- Not a CRM out of the box — you build one on top of it
- Steeper learning curve
- More suited if you want total control over every aspect

---

## Head-to-Head Comparison

| Feature | Twenty | EspoCRM | Krayin | Atomic | ERPNext | NocoBase |
|---------|--------|---------|--------|--------|---------|----------|
| **License** | AGPL v3 | AGPL v3 | **MIT** | Mixed | GPL v3 | AGPL v3 |
| **Language** | TypeScript/React | PHP/JS | PHP/Vue | React/Supabase | Python/JS | Node/React |
| **GitHub Stars** | **40K+** | 2.8K | Growing | Small | 22K+ | 15K+ |
| **Modern UI** | ★★★★★ | ★★★ | ★★★★ | ★★★★★ | ★★★ | ★★★★ |
| **Custom Objects** | ★★★★★ | ★★★★★ | ★★★ | ★★★ | ★★★★★ | ★★★★★ |
| **API Quality** | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★★ | ★★★★ |
| **Webhooks** | ★★★★★ | ★★★★ | ★★ | ★★★ | ★★★★ | ★★★★ |
| **Pipeline/Kanban** | ★★★★★ | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★★ |
| **Email Built-in** | ★★★★ | ★★★★★ | ★★★★ | ★★ | ★★★★ | ★★★ |
| **Ease of Setup** | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★ | ★★★ |
| **Code Customization** | ★★★★★ | ★★★★ | ★★★★★ | ★★★★★ | ★★★★ | ★★★★★ |
| **Community Size** | ★★★★★ | ★★★★ | ★★ | ★★ | ★★★★★ | ★★★★ |
| **Self-Host Docker** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **No Monthly Fees** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## My Recommendation

### For YOUR use case (affiliate offer management + pipeline + email + API integrations):

**Pick: Twenty CRM**

Why:
1. **Custom Objects** — Create "Affiliate Offers," "Agency Partners," "Email Sequences," "Lead Magnets" as first-class objects with full API support
2. **Webhooks** — Connect to your cold email system, Make.com automations, and other tools in real-time
3. **Pipeline Boards** — Visualize offers moving through your funnel stages
4. **API-first** — REST + GraphQL means you can connect ANYTHING to it
5. **Modern stack** (React + Node + TypeScript + PostgreSQL) — easy to customize if you know JavaScript
6. **Docker 1-click deploy** — Up and running in minutes
7. **Massive community** — 40K stars, 300+ contributors, YC-backed, active development
8. **Looks good** — Notion/Linear-inspired UI. Not clunky enterprise software.

**Runner-up: EspoCRM** — If you want MORE features out of the box (workflows, BPM, email campaigns, formula scripting) and don't mind PHP. Better for "just works" without coding.

**Runner-up: NocoBase** — If you want to build a completely custom system from scratch (CRM + affiliate tracker + pipeline + anything else) and want maximum flexibility.

---

## What We'd Build in Twenty CRM

### Custom Objects to Create:
1. **Affiliate Offers** — Tool name, category (AI/SEO/Marketing), commission %, cookie duration, program URL, status
2. **Agency Partners** — Agency name, service type, referral terms, reputation score, contact info
3. **Email Sequences** — Sequence name, target segment, offers included, stage (draft/active/paused)
4. **Lead Magnets** — Content name, type (guide/quiz/assessment), associated offers, download URL
5. **Contacts/Leads** — Business name, industry, size, pain points, tags, funnel stage
6. **Campaigns** — Campaign name, channel (cold email/content/social), offers layered, performance metrics

### Pipeline Stages:
```
Offer Pipeline:     Research → Approved → Active → Content Created → In Sequence → Performing → Paused
Lead Pipeline:      Cold → Opened Email → Engaged → Clicked Offer → Converted → Repeat Buyer
Agency Pipeline:    Identified → Contacted → Terms Agreed → Active → Sending Leads → Earning
```

### API Connections:
- Instantly.ai (cold email) ↔ Twenty (lead/contact sync)
- Make.com (workflow automation) ↔ Twenty (offer routing, tagging)
- Email platform ↔ Twenty (sequence triggers)
- Scraping tools ↔ Twenty (new offer ingestion)

---

*Research compiled: March 15, 2026*
