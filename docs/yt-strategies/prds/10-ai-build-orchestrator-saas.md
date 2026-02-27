# PRD: AI Build Orchestrator (SaaS Product)

## Product Summary

A web application that automates the process of breaking down any app idea into AI-buildable chunks with proper prompts, orchestration plans, and foundation documents. Users fill in forms, the tool generates everything they need to build their app using AI agents.

**The pitch:** "Stop spending hours organizing prompts. Fill in three boxes, get a complete build plan with copy-paste-ready agent prompts."

**Target market:** Non-technical and semi-technical users who want to build apps with AI but struggle with prompt organization, token limits, and multi-agent coordination. The first wave of mainstream AI users (2026 onward) who will not use a CLI.

---

## Business Model

### Funnel Strategy

**Free tier (content marketing / list builder):**
The GUIDE.md content becomes free educational material. Blog posts, YouTube video series, social media content. Teaches users the system manually. The complexity of doing it manually is the pain point that sells the tool.

YouTube content map (12+ videos from existing documentation):
- "How I Build Apps 10x Faster With AI Agents"
- "Why Your AI Keeps Forgetting (And How To Fix It)"
- "Build Any App With AI -- The Simple Way"
- "Turn One AI Into a Dev Team (Wave Method)"
- "The Prompt Template That Changed Everything"
- "8 Mistakes Killing Your AI Builds"
- "The One Document Every AI Build Needs"
- "How to Stop AI From Guessing Your Architecture"
- "Why Your AI Makes The Wrong App (Bad PRDs)"
- "How to Run 8 AI Agents at Once"
- "Which AI Build Method Is Right For You?"
- "Build Your First AI App in 15 Minutes"

Each video teaches something real, pitches the next video in the series, and the entire series pitches the tool. Evergreen SEO content. Can be produced with AI-generated scripts and a character avatar (no camera required).

YouTube series can be packaged as a course using YouTube's course/playlist features. The series gets indexed by Google, creating passive inbound traffic.

**Paid tiers:**

| Tier | Name | Price Range | What They Get |
|------|------|-------------|---------------|
| Entry | **Single Agent Mode** | $ | Breaks PRD into chunked prompts, one agent at a time. Works with ANY AI tool (ChatGPT, Claude, Gemini, etc.) |
| Pro | **Sub-Agent Mode** | $$ | Everything in Single Agent + orchestrated waves with sub-agents. Generates master prompts that spawn specialized sub-agents. Claude Code Web specific. |
| Addon | **PRD Maker** | $$-$$$ | Standalone or bundled. Takes a rough app idea and generates a structured, detailed PRD. This is the upstream product that makes everything else work better. Arguably worth more than the orchestrator itself. |
| Premium | **Lifetime Bundle** | $$$ | Everything + future updates + template library + reverse-engineering mode |

**Pricing structure per tier:**
- Monthly subscription
- Annual subscription (discount)
- Lifetime access (one-time premium price)

**Bonuses (for irresistible offer packaging):**
- Chunking Mode vs Strategy Mode (both included at any paid tier)
- Template library (pre-built orchestration plans for common app types)
- Prompt packs (pre-written agent prompts for common features like auth, CRUD, dashboards)
- Reverse-engineering mode (drop in a crappy app, generate the PRD to rebuild it properly)

### Revenue Logic

The PRD Maker sits upstream of everything. Bad PRD = bad prompts = bad app. This is the foundation product. It commands equal or higher price than the orchestrator because it solves a more fundamental problem.

The funnel upsell chain:
1. Free content (YouTube/blog) -> builds email list
2. Single Agent Mode (entry product for normies)
3. Sub-Agent Mode (upgrade for Claude Code Web users)
4. PRD Maker (critical addon / separate purchase)
5. Lifetime Bundle (premium offer with all bonuses)

---

## Product Architecture

### Tech Stack

- **Frontend:** React + TypeScript + Tailwind CSS (neobrutalism design system, consistent with AutoForge)
- **Backend:** Python + FastAPI (consistent with AutoForge patterns)
- **Database:** PostgreSQL (production SaaS, not localStorage)
- **Auth:** Email/password + OAuth (Google, GitHub)
- **Payments:** Stripe (subscriptions + one-time purchases for lifetime tier)
- **Deployment:** Standard cloud hosting (Vercel/Railway/Fly.io frontend, containerized backend)

### Standalone vs Integrated

This is a **standalone SaaS product**, not a feature inside AutoForge. Reasons:
1. Different target market (normies vs developers)
2. Different pricing model (subscription SaaS vs one-time tool)
3. No dependency on Claude SDK or any specific AI provider
4. Can be marketed independently with its own domain, branding, and funnel
5. Avoids the gray area of selling software that uses the Claude SDK subscription model

The output is plain text (prompts, documents, orchestration plans). Users copy-paste into whatever AI tool they prefer. No API calls to any AI provider from the product itself (except the PRD Maker, which uses AI to generate PRDs -- this is a standard API usage, not subscription piping).

---

## Core Features

### Feature 1: Project Setup Wizard

**What it does:** User creates a new project by filling in a guided form. The form collects everything needed to generate foundation documents and agent prompts.

**Form fields:**

Step 1 -- The Basics:
- App name
- One-paragraph description (what it does, who it's for)
- Tech stack (dropdown presets: React+Python, React+Node, Next.js, Vue+Python, etc. + custom)

Step 2 -- Features:
- Feature list builder (add/remove/reorder features)
- Each feature: name, one-sentence description, size estimate (small/medium/large)
- Drag-and-drop to set dependencies between features ("Feature B depends on Feature A")

Step 3 -- Architecture Preferences:
- File naming convention (dropdown: kebab-case, camelCase, PascalCase, snake_case)
- API route pattern (dropdown: /api/resource, /api/v1/resource, etc.)
- Database pattern (dropdown: ORM, raw SQL, localStorage, etc.)
- Component pattern (dropdown: functional React, class-based, Vue SFC, etc.)
- Any custom rules (free text)

**Output:** Project saved to database. Ready for document generation.

### Feature 2: Foundation Document Generator

**What it does:** Generates the four foundation documents automatically based on project setup data.

**Documents generated:**
1. **Vision Document** -- Generated from app name, description, and architecture preferences
2. **Context Primer** -- Generated from tech stack, naming conventions, file patterns, and feature list
3. **PRDs** -- One per feature, generated from feature descriptions and dependency data
4. **Orchestration Guide** -- Generated from feature list, dependencies, and size estimates. Automatically calculates waves, parallel groups, and token budgets.

**User interaction:**
- Each document is generated and shown in an editor
- User can edit any document before finalizing
- "Regenerate" button to get a fresh version with different phrasing
- Documents are saved and versioned

**AI integration (for generation):**
- Uses Claude API or OpenAI API to generate documents from structured input
- System prompts are tuned for each document type
- This is a standard API call, not subscription piping -- the product pays for API usage as a cost of goods

### Feature 3: Agent Prompt Generator (Single Agent Mode)

**What it does:** Takes the foundation documents and generates copy-paste-ready agent prompts using the 5-step template.

**Tier:** Entry (Single Agent Mode)

**How it works:**
1. User selects which features to generate prompts for (or "all")
2. System generates one prompt per feature using the 5-step template
3. Each prompt includes the relevant sections of the foundation documents (not all of them -- only what that agent needs)
4. Token budget is calculated and displayed for each prompt
5. If a prompt exceeds 50% of the target model's context window, the system automatically suggests splitting it

**Output per agent prompt:**
- The complete prompt text (ready to copy-paste)
- Token count estimate
- Budget visualization (bar chart showing % of context window used)
- "Copy to Clipboard" button
- "Export as .md" button

**Build order view:**
- Visual display of which prompts to run first, second, third
- Dependency arrows showing which agents must complete before others start
- "Chunking Mode" -- linear order, one at a time
- "Parallel Mode" -- shows which agents can run simultaneously

### Feature 4: Sub-Agent Orchestration Generator (Pro Mode)

**What it does:** Generates master prompts that leverage sub-agents for Claude Code Web users.

**Tier:** Pro (Sub-Agent Mode)

**How it differs from Single Agent Mode:**
- Instead of one-prompt-per-feature, generates orchestrator prompts that spawn specialized sub-agents
- A single master prompt for each wave that creates: architect sub-agent, builder sub-agents, QA sub-agent
- Token budgets account for the orchestrator's overhead (5-10K per sub-agent managed)
- Includes sub-agent role definitions within the master prompt

**Generated roles per wave:**
- **Orchestrator** -- manages the wave, passes context between sub-agents, handles errors
- **Architect sub-agent** -- reads spec, outputs file structure and interfaces (spawned first, dies after delivering blueprint)
- **Builder sub-agent(s)** -- implements features following the architect's blueprint (parallel, one per feature or feature group)
- **QA sub-agent** -- tests the combined output (spawned after builders finish)

**Output:** One master prompt per wave, plus the orchestration guide showing wave order and merge points.

### Feature 5: PRD Maker (Addon)

**What it does:** Takes a rough app idea (plain English, bullet points, napkin sketch description) and generates a structured, detailed PRD.

**Tier:** Addon (sold separately or bundled)

**Input options:**
- Free text description ("I want an app that...")
- Bullet point list of features
- Existing crappy app code (reverse-engineering mode -- drop in code, get a PRD for rebuilding it)
- Voice memo transcript (for users who think out loud)

**Output:**
- Structured PRD with: overview, user stories, technical spec, API endpoints, database schema, UI components, edge cases, acceptance criteria
- Feature dependency graph
- Suggested tech stack (if not specified)
- Token budget estimates per feature

**AI integration:**
- Multi-step generation: first pass generates structure, second pass fills in detail, third pass adds edge cases and acceptance criteria
- User reviews and edits between passes
- "Deeper" button on any section to expand it with more detail

**Reverse-engineering mode:**
- User uploads or pastes code from an existing app
- AI analyzes the code structure, identifies features, maps the architecture
- Generates a PRD that describes what the app SHOULD be (cleaned up, properly structured)
- Generates the foundation documents needed to rebuild it with the orchestrator
- This is the "got a crappy vibe-coded app? Drop it in, we'll generate the rebuild plan" feature

### Feature 6: Template Library

**What it does:** Pre-built project setups for common app types that users can start from instead of building from scratch.

**Templates included:**
- SaaS Starter (auth + billing + dashboard + settings)
- E-commerce (products + cart + checkout + orders)
- Project Management (projects + tasks + boards + teams)
- Content Platform (posts + categories + comments + search)
- Marketplace (listings + messaging + payments + reviews)
- API Backend (auth + CRUD + webhooks + admin)
- Landing Page Builder (pages + sections + forms + analytics)

**Each template includes:**
- Pre-filled project setup data
- All four foundation documents (pre-written for that app type)
- Agent prompts for all features
- Orchestration plan with waves
- Token budget table

**User can:**
- Use template as-is
- Fork and customize (change features, add/remove, adjust architecture)
- Combine templates (e.g., start with SaaS Starter, add features from E-commerce)

### Feature 7: Prompt Pack Store

**What it does:** Pre-written agent prompts for common features that users can plug into any project.

**Packs available:**
- Authentication Pack (login, signup, password reset, OAuth, session management, role-based access)
- Dashboard Pack (stats cards, charts, activity feed, date range picker)
- Payment Pack (Stripe integration, subscription management, invoices, webhooks)
- Notification Pack (email, in-app, push, preference management)
- File Upload Pack (image upload, document upload, gallery, drag-and-drop)
- Search Pack (full-text search, filters, facets, saved searches)
- Admin Pack (user management, settings, audit log, feature flags)

**Each pack includes:**
- Agent prompts (single-agent and sub-agent versions)
- PRD for the feature
- Context Primer additions (patterns specific to this feature)
- Integration notes (how to connect with other features)

**Bonus content / premium tier inclusion.**

### Feature 8: Dashboard and Project Management

**What it does:** Central hub for managing all projects, tracking build progress, and accessing generated documents.

**Views:**
- **Projects list** -- all projects with status (setup, generating, ready, building, complete)
- **Project detail** -- all foundation documents, agent prompts, orchestration plan
- **Build tracker** -- checklist of agents with status (not started, prompt copied, building, done, verified)
- **Document editor** -- edit any generated document with auto-save
- **Export** -- download all documents as a ZIP, or individual files as .md

---

## User Flows

### Flow 1: New User (Entry Tier)

1. Signs up (email or OAuth)
2. Sees empty dashboard with "Create New Project" button
3. Fills in Project Setup Wizard (3 steps, ~10 minutes)
4. System generates foundation documents (~30 seconds)
5. System generates agent prompts in Single Agent Mode (~30 seconds)
6. User sees build plan: ordered list of agent prompts with token budgets
7. User copies first prompt, opens Claude/ChatGPT, pastes it
8. Agent builds the feature
9. User checks off "done" in build tracker
10. Repeats for each feature

### Flow 2: Upgrade to Pro

1. User has completed a project with Single Agent Mode
2. Sees "Unlock Sub-Agent Mode" prompt with explanation of benefits
3. Upgrades to Pro tier
4. Existing projects get "Generate Sub-Agent Prompts" button
5. System regenerates prompts as master orchestrator prompts with sub-agent roles
6. User copies one master prompt per wave instead of one prompt per feature
7. Faster builds, better coordination, higher quality output

### Flow 3: PRD Maker

1. User has a rough app idea
2. Opens PRD Maker
3. Types or pastes their idea (or uploads existing code for reverse-engineering)
4. AI generates structured PRD in three passes (user can edit between passes)
5. Final PRD is saved
6. "Send to Orchestrator" button auto-creates a new project with the PRD data pre-filled
7. User finishes setup wizard (tech stack, conventions), generates prompts

### Flow 4: Template Start

1. User browses template library
2. Picks "SaaS Starter"
3. Template pre-fills everything: project setup, foundation docs, PRDs, agent prompts
4. User customizes: changes app name, adjusts features, adds their own
5. Regenerates affected documents
6. Ready to build

---

## Technical Spec

### Database Models

```
User
  - id (uuid)
  - email
  - name
  - tier (free | entry | pro | premium)
  - stripe_customer_id
  - created_at

Project
  - id (uuid)
  - user_id (fk)
  - name
  - description
  - tech_stack (json)
  - conventions (json)
  - status (setup | generating | ready | building | complete)
  - created_at
  - updated_at

Feature
  - id (uuid)
  - project_id (fk)
  - name
  - description
  - size (small | medium | large)
  - order (int)
  - status (pending | prompt_generated | building | done | verified)
  - created_at

FeatureDependency
  - id (uuid)
  - feature_id (fk)
  - depends_on_feature_id (fk)

Document
  - id (uuid)
  - project_id (fk)
  - type (vision | context_primer | prd | orchestration | agent_prompt)
  - feature_id (fk, nullable -- null for project-level docs, set for feature-specific PRDs/prompts)
  - content (text)
  - token_count (int)
  - version (int)
  - created_at
  - updated_at

Template
  - id (uuid)
  - name
  - description
  - category
  - project_data (json -- serialized project setup)
  - documents (json -- serialized foundation docs)
  - is_premium (bool)

PromptPack
  - id (uuid)
  - name
  - description
  - category
  - prompts (json)
  - is_premium (bool)
```

### API Endpoints

```
Auth:
  POST   /api/auth/signup
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/auth/me

Projects:
  GET    /api/projects
  POST   /api/projects
  GET    /api/projects/:id
  PUT    /api/projects/:id
  DELETE /api/projects/:id

Features:
  GET    /api/projects/:id/features
  POST   /api/projects/:id/features
  PUT    /api/projects/:id/features/:fid
  DELETE /api/projects/:id/features/:fid
  PUT    /api/projects/:id/features/:fid/status

Dependencies:
  POST   /api/projects/:id/features/:fid/dependencies
  DELETE /api/projects/:id/features/:fid/dependencies/:did

Documents:
  GET    /api/projects/:id/documents
  GET    /api/projects/:id/documents/:did
  PUT    /api/projects/:id/documents/:did
  POST   /api/projects/:id/documents/generate     (generates all foundation docs)
  POST   /api/projects/:id/prompts/generate        (generates agent prompts)
  POST   /api/projects/:id/prompts/generate-pro    (generates sub-agent prompts, pro tier)

PRD Maker:
  POST   /api/prd/generate           (rough idea -> structured PRD)
  POST   /api/prd/reverse-engineer   (code upload -> PRD)
  POST   /api/prd/refine             (second/third pass refinement)

Templates:
  GET    /api/templates
  GET    /api/templates/:id
  POST   /api/projects/from-template/:id

Prompt Packs:
  GET    /api/prompt-packs
  GET    /api/prompt-packs/:id

Billing:
  POST   /api/billing/create-checkout
  POST   /api/billing/webhook
  GET    /api/billing/subscription
  POST   /api/billing/cancel
```

### Stripe Integration

Products:
- `orchestrator_entry_monthly` -- Single Agent Mode, monthly
- `orchestrator_entry_annual` -- Single Agent Mode, annual
- `orchestrator_pro_monthly` -- Sub-Agent Mode, monthly
- `orchestrator_pro_annual` -- Sub-Agent Mode, annual
- `prd_maker_monthly` -- PRD Maker, monthly
- `prd_maker_annual` -- PRD Maker, annual
- `lifetime_bundle` -- Everything, one-time purchase

Webhook events to handle:
- `checkout.session.completed` -- activate tier
- `customer.subscription.updated` -- tier changes
- `customer.subscription.deleted` -- downgrade to free
- `invoice.payment_failed` -- grace period handling

### AI Integration (for document/prompt generation)

The product uses AI APIs to generate documents. This is standard API usage (the product pays per token as COGS), not subscription piping.

**Provider options:**
- Primary: Claude API (Sonnet for generation, Haiku for quick tasks)
- Fallback: OpenAI API (GPT-4o for generation)
- User never needs their own API key -- the product handles it

**System prompts (one per document type):**
- Vision Document generator
- Context Primer generator
- PRD generator (from features)
- PRD generator (from rough idea -- PRD Maker)
- PRD generator (from code -- reverse engineering)
- Orchestration Guide generator (from feature dependency graph)
- Agent Prompt generator (single-agent, 5-step template)
- Agent Prompt generator (sub-agent, orchestrator format)

**Token counting:**
- All generated documents include a token count
- Budget visualization uses tiktoken (or equivalent) for accurate estimation
- Warnings when prompts exceed 50% of target model's context window

---

## Pages / UI

### Page 1: Landing / Marketing

- Hero section with value prop
- "See how it works" video embed (from YouTube series)
- Pricing table with tier comparison
- Testimonials / social proof
- CTA: "Start Free" / "Get Started"

### Page 2: Dashboard

- Project cards (name, status, feature count, last updated)
- "New Project" button
- Quick stats (total projects, features built, prompts generated)

### Page 3: Project Setup Wizard

- 3-step form (Basics -> Features -> Architecture)
- Progress bar
- Feature dependency builder (visual drag-and-drop)
- Live preview of what will be generated

### Page 4: Project Detail

- Tabs: Overview | Documents | Prompts | Build Tracker
- **Overview:** Project summary, tech stack, feature list with dependency graph
- **Documents:** All foundation documents in editable panels. Regenerate button per document.
- **Prompts:** List of agent prompts with token budgets, copy buttons, export buttons. Toggle between Single Agent and Sub-Agent view (pro tier).
- **Build Tracker:** Checklist of features with status. Progress bar. Estimated total tokens used.

### Page 5: PRD Maker

- Input area (free text / code upload / voice transcript)
- Multi-step generation with preview between steps
- Section-level "Go Deeper" buttons
- "Send to Orchestrator" button

### Page 6: Template Library

- Grid of template cards
- Category filter
- Preview modal (shows what you get)
- "Use This Template" button -> creates project

### Page 7: Prompt Pack Store

- Grid of pack cards
- Category filter
- Preview modal (shows included prompts)
- "Add to Project" button

### Page 8: Account / Billing

- Current tier
- Subscription management
- Invoice history
- Upgrade / downgrade options

---

## MVP Scope (V1)

Build these first, in this order:

1. **Auth + Billing** -- signup, login, Stripe integration, tier gating
2. **Project Setup Wizard** -- the 3-step form
3. **Foundation Document Generator** -- generates all 4 documents from setup data
4. **Single Agent Prompt Generator** -- generates copy-paste prompts using the 5-step template
5. **Dashboard + Project Management** -- project list, detail view, build tracker
6. **Document Editor** -- edit generated documents inline

**Deferred to V2:**
- Sub-Agent Mode (Pro tier)
- PRD Maker (Addon)
- Template Library
- Prompt Pack Store
- Reverse-engineering mode

**Rationale:** V1 delivers the core value proposition (fill in forms, get agent prompts) for the largest market segment (single-agent users on any AI tool). V2 adds the premium features and upsells.

---

## Success Metrics

- **Conversion:** Free content viewer -> signed up user (target: 5-10%)
- **Activation:** Signed up -> created first project (target: 60%)
- **Retention:** Created project -> copied at least 3 prompts (target: 40%)
- **Upgrade:** Entry tier -> Pro or PRD Maker (target: 15-20%)
- **Revenue per user:** Target $20-50/month blended across tiers

---

## Competitive Landscape

**Direct competitors:** None yet that specifically solve multi-agent orchestration for app building.

**Adjacent competitors:**
- Cursor / Windsurf / Bolt -- these are IDE-level tools, not orchestration tools. They complement this product.
- Generic prompt libraries (PromptBase, etc.) -- sell individual prompts, not coordinated build systems.
- AI code generators (v0, Lovable, etc.) -- generate code directly, don't teach users to build. Different market.

**Moat:** The methodology (wave-based orchestration, 5-step template, foundation documents) is the IP. The free content builds authority and trust. The tool automates the methodology. Competitors would need to replicate both the methodology and the tooling.

**Window of opportunity:** 9-18 months before frontier models (Opus 6.x, GPT-5.x) can build complete apps in a single session. During this window, orchestration is necessary for any non-trivial app. After this window, the tool evolves into a "build quality" tool (the difference between a quick AI app and a properly architected one will still require structure).
