# Build and Ship Client Apps with Claude Code — The Full Delivery Framework

## What You'll Build

A complete client project delivery system — from first call to monthly maintenance. This framework covers scoping, building with Claude Code, testing, deploying, handing off, and maintaining client applications. You'll have templates for every phase so you can deliver professional apps in days instead of weeks.

## Prerequisites

- Claude Pro subscription ($20/mo)
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ installed
- GitHub account
- Vercel account (free tier)
- Supabase account (free tier)
- Basic understanding of web apps (you'll learn the rest through Claude Code)

## Estimated Time

- **Per client project:** 2-14 days depending on complexity
- **Framework setup (one-time):** 2-3 hours to customize templates
- **Typical build session:** 3-6 hours of focused Claude Code work

## The 7 Phases

```
Client Call → Scope → Build → Test → Deploy → Handoff → Maintain
```

Every project follows this exact sequence. Skip a phase and you'll pay for it later — either in revision cycles, deployment issues, or client confusion.

---

## Phase 1: Client Call

The discovery call determines whether this project is a fit and gathers everything you need to scope it.

### Must-Ask Questions

Ask these in order. Each one builds on the previous answer.

1. **"What problem are you trying to solve?"** — Not "what do you want built" but what's the actual pain. They might say "I need a CRM" but the real problem is "I'm losing track of leads in spreadsheets."

2. **"Who uses this?"** — How many users? What roles? Technical or non-technical? This determines auth complexity and UI simplicity requirements.

3. **"Show me your current tool or process."** — Screen share their spreadsheet, their current janky tool, their manual workflow. This is the spec they don't know how to write. Screenshot everything.

4. **"If this tool could only do ONE thing perfectly, what would it be?"** — This is your MVP scope. Everything else is Phase 2.

5. **"What's your timeline?"** — "Yesterday" means they're in pain (good). "Sometime this quarter" means low urgency (risky — they may deprioritize).

### Green Flags

- They have a clear problem and can describe the current pain
- They've tried other solutions and can tell you what didn't work
- They have budget allocated (not "exploring options")
- Single decision-maker on the call
- Timeline is under 4 weeks

### Red Flags

- "We need something like Salesforce but custom" (scope creep guaranteed)
- Committee of 5+ people on the call (decisions will take forever)
- "We don't have a budget yet" (you're doing free consulting)
- Can't articulate the core problem clearly
- "Can you also add..." more than 3 times on the first call

---

## Phase 2: Scope

After the call, you produce a one-page scope document. Not a 20-page proposal — a single page that both of you can reference.

### One-Page Spec Template

```markdown
# [Project Name] — Scope

## Summary
[2-3 sentences: what we're building, who it's for, what problem it solves]

## Pages / Screens
1. [Page name] — [what it does]
2. [Page name] — [what it does]
3. [Page name] — [what it does]

## Data Model
- [Entity]: [key fields]
- [Entity]: [key fields]
- [Relationships: e.g., "Each project has many tasks"]

## Core Actions (what users DO)
1. [Action — e.g., "Create a new project"]
2. [Action — e.g., "Assign task to team member"]
3. [Action — e.g., "View dashboard with project status"]
4. [Action — e.g., "Export report as CSV"]

## Integrations
- [Service] — [what for, e.g., "Stripe for payments"]
- [Service] — [what for, e.g., "Resend for email notifications"]

## NOT Included (important — prevents scope creep)
- [Feature they mentioned but isn't in v1]
- [Feature they mentioned but isn't in v1]
- [Mobile app — web only for v1]

## Timeline
- Build: [X days]
- Testing: [X days]
- Total: [X days]

## Investment
- [Price]
- 50% upfront, 50% on delivery
- Includes 2 rounds of revisions
- Maintenance: $[X]/month (optional)
```

### Recommended Stack

For 90% of client projects, use this stack:

| Layer | Tool | Why |
|---|---|---|
| Frontend | Next.js 14+ (App Router) | Full-stack React, great DX, Vercel deploy |
| Styling | Tailwind CSS | Fast iteration, consistent design |
| Database | Supabase (Postgres) | Free tier, auth built-in, real-time |
| Auth | Supabase Auth | Email/password, OAuth, magic links |
| Hosting | Vercel | Free tier, automatic deploys, edge network |
| Email | Resend | Simple API, free tier (100 emails/day) |
| Payments | Stripe | When needed, best-in-class |

This stack is free to run (until the client outgrows free tiers), deploys in one command, and Claude Code knows it deeply.

---

## Phase 3: Build

### Claude Code Setup

```bash
# Install Claude Code globally (if not already)
npm install -g @anthropic-ai/claude-code

# Create project directory
mkdir client-project-name && cd client-project-name

# Initialize the project
npx create-next-app@latest . --typescript --tailwind --app --src-dir

# Start Claude Code
claude
```

### Your First Prompt

This is the prompt structure that produces the best results for a new project. Example for a project management app:

```
I'm building a project management app for a small construction company.

USERS:
- Project managers (3-5 people) who create and manage projects
- Field workers (10-15 people) who update task status from mobile

CORE FEATURES (v1 only):
1. Dashboard showing all active projects with status (on track / delayed / completed)
2. Project detail page with task list, timeline, and team assignment
3. Task creation and status updates (To Do → In Progress → Done)
4. Simple auth — email/password login

STACK:
- Next.js 14 App Router with TypeScript
- Tailwind CSS for styling
- Supabase for database and auth

DATA MODEL:
- projects: id, name, client_name, status, start_date, due_date, created_by
- tasks: id, project_id, title, description, status, assigned_to, due_date
- profiles: id (matches auth.users), full_name, role (manager/worker)

START WITH:
1. Set up Supabase tables and RLS policies
2. Build the auth flow (login/signup pages)
3. Build the dashboard page
4. Build the project detail page with task management

Design should be clean and professional. Dark sidebar navigation, white content area.
Use shadcn/ui components where appropriate.
```

### The Build Loop

This is the core rhythm of building with Claude Code:

```
Describe → Build → Preview → Refine → Repeat
```

1. **Describe** what you want (be specific about behavior, not implementation)
2. **Build** — Claude Code writes the code
3. **Preview** — Run `npm run dev` and check in the browser
4. **Refine** — Tell Claude what to fix ("The task cards should show the assignee avatar" or "The loading state is missing on the dashboard")
5. **Repeat** until the feature is solid, then move to the next one

### Project CLAUDE.md

Create a `CLAUDE.md` in the project root so Claude Code maintains consistency:

```markdown
# [Project Name]

## Stack
- Next.js 14 App Router, TypeScript, Tailwind CSS
- Supabase (database + auth)
- Deployed on Vercel

## Conventions
- Use server components by default, client components only when needed
- All database queries go through lib/supabase.ts
- Use Tailwind only — no CSS modules or styled-components
- Error handling: try/catch with user-friendly error messages
- Loading states on every async operation

## File Structure
- src/app/ — pages and layouts
- src/components/ — shared components
- src/lib/ — utilities, supabase client, types
- src/types/ — TypeScript interfaces

## Current Status
- [x] Auth flow
- [x] Dashboard
- [ ] Project detail page
- [ ] Task management
```

### Build Order

Always build in this order:

1. **Layout** — Navigation, sidebar, page structure
2. **Auth** — Login, signup, session management, protected routes
3. **Core feature** — The ONE thing the app must do (from the client call)
4. **Secondary features** — Supporting functionality
5. **Integrations** — Email notifications, payments, third-party APIs
6. **Polish** — Loading states, error handling, empty states, responsive design

---

## Phase 4: Test

Before showing the client anything, run through these checks.

### User Flow Testing

Test every path a real user would take:

```
[ ] Sign up with email and password
[ ] Log in with those credentials
[ ] Perform the core action (create project, add task, etc.)
[ ] Edit something you just created
[ ] Delete something
[ ] Navigate to every page using the nav/sidebar
[ ] Log out and back in — verify data persists
[ ] Sign up as a second user — verify data isolation (if multi-tenant)
```

### Mobile Check

```
[ ] Open in Chrome DevTools mobile view (375px width)
[ ] Text is readable without horizontal scrolling
[ ] All tap targets are at least 44px x 44px
[ ] Forms are usable — labels visible, inputs not cut off
[ ] Navigation works (hamburger menu, back buttons)
[ ] Tables scroll horizontally or stack vertically
```

### Edge Cases

```
[ ] Wrong password — shows clear error, doesn't crash
[ ] Empty form submission — shows validation errors
[ ] Double-click submit button — doesn't create duplicates
[ ] Paste very long text in text fields — handles gracefully
[ ] Slow connection (Chrome DevTools → Network → Slow 3G) — loading states show
[ ] Refresh the page on any route — doesn't 404 or crash
[ ] Browser back button — works as expected
[ ] Empty states — what shows when there's no data yet?
```

### Performance

```
[ ] Pages load in under 2 seconds on desktop
[ ] No console errors in browser DevTools
[ ] Images are optimized (use next/image)
[ ] No unnecessary re-renders (React DevTools profiler)
```

---

## Phase 5: Deploy

### Push to GitHub

```bash
# Initialize git (if not already)
cd /path/to/project
git init
git add .
git commit -m "Initial build — [project name] v1"

# Create private repo and push
gh repo create client-project-name --private --push
```

### Deploy to Vercel

```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy
npx vercel --prod
```

On first deploy, Vercel will ask you to link to a project. Follow the prompts.

### Environment Variables

Add these in Vercel dashboard (Settings → Environment Variables):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Add any other project-specific vars:
RESEND_API_KEY=re_your-key
STRIPE_SECRET_KEY=sk_live_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret
```

After adding env vars, redeploy:

```bash
npx vercel --prod
```

### Custom Domain

```bash
# Add client's domain
npx vercel domains add clientdomain.com

# Vercel will give you DNS records to add
# Client updates their DNS, SSL is automatic
```

---

## Phase 6: Handoff

### Record a Walkthrough

Record a 5-10 minute Loom video covering:

```
1. Login and dashboard overview (1-2 min)
2. Walk through every core feature — show don't tell (3-5 min)
3. Common tasks they'll do daily (1-2 min)
4. Where to find help / how to contact you (30 sec)
```

Keep it casual and practical. Don't explain the technology — show the workflow.

### Transfer Credentials

Send the client a secure document (use 1Password shared vault or similar) with:

```
Vercel:
- Project URL: https://project.vercel.app
- Custom domain: https://clientdomain.com
- Vercel team invite: [send invite from Vercel dashboard]

GitHub:
- Repository: https://github.com/you/project-name
- Add client as collaborator (if they want code access)

Database (Supabase):
- Dashboard: https://supabase.com/dashboard/project/xxxxx
- Organization invite sent to: client@email.com

Domain:
- Registrar: [where their domain is managed]
- DNS records: [what was configured]

API Keys / Services:
- Resend: [account details if client owns the account]
- Stripe: [dashboard link, webhook endpoint URL]
- Any other third-party services
```

---

## Phase 7: Maintain

### What Maintenance Covers

Set clear expectations in a maintenance agreement:

**Included ($200-500/month):**
- Bug fixes (response within 24-48 hours)
- Small UI updates (text changes, color tweaks, adding content)
- Dependency updates and security patches
- Uptime monitoring and alerts
- Monthly backup verification

**Not included (quoted separately):**
- New features or pages
- Integrations with new services
- Major redesigns
- Performance optimization projects

### Maintenance Workflow

```
1. Client reports issue via email (or a shared channel)
2. You acknowledge within 24 hours
3. Assess: bug fix (included) vs feature request (quoted separately)
4. Fix bugs in a branch, test, deploy
5. Feature requests: scope → quote → approve → build → deploy
6. Monthly: check for dependency updates, review error logs, verify backups
```

---

## Pricing Guide

| Tier | What's Included | Price Range | Build Time | Your API Cost |
|---|---|---|---|---|
| **Starter** | Landing page, contact form, basic CMS | $1,000 - $2,500 | 1-2 days | $5-15 |
| **Mid** | Dashboard + integrations, auth, CRUD | $3,000 - $5,000 | 2-4 days | $15-30 |
| **Premium** | Multi-user SaaS, roles, payments, API | $5,000 - $10,000+ | 1-2 weeks | $30-50 |
| **Maintenance** | Bug fixes, updates, monitoring | $200 - $500/mo | 2-4 hrs/mo | $5-10 |

Your actual cost per project is $20-50 in API credits. The rest is margin.

### How to Price

- Never price by the hour — price by the value delivered
- A lead tracking tool that helps a sales team close 2 more deals/month is worth $5K+
- A scheduling system that saves 10 hours/week of admin work is worth $3K+
- Always anchor high: "Projects like this typically run $8-12K. Because of the focused scope, I can do this for $5K."

---

## Environment Variables

Every client project will need some combination of these:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Vercel (for CLI deploys)
VERCEL_TOKEN=your-vercel-token
VERCEL_ORG_ID=your-org-id
VERCEL_PROJECT_ID=your-project-id

# Email (Resend)
RESEND_API_KEY=re_your-key

# Payments (Stripe)
STRIPE_SECRET_KEY=sk_live_your-key
STRIPE_PUBLISHABLE_KEY=pk_live_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret

# AI features (if applicable)
ANTHROPIC_API_KEY=sk-ant-your-key

# Analytics (if applicable)
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=clientdomain.com
```

---

## Example Builds with Prompt Templates

### Example 1: Customer Support AI Agent

```
Build a customer support dashboard for a SaaS company.

CORE FEATURES:
1. Incoming ticket list with status (Open / In Progress / Resolved)
2. Ticket detail page with conversation thread
3. AI auto-reply: when a new ticket comes in, Claude analyzes it against a
   knowledge base and suggests a reply. Agent can approve, edit, or write their own.
4. Simple analytics: tickets/day, avg resolution time, AI suggestion acceptance rate

STACK: Next.js, Supabase, Tailwind, Claude API for AI replies

DATA MODEL:
- tickets: id, subject, customer_email, status, priority, created_at
- messages: id, ticket_id, sender (customer/agent/ai), content, created_at
- knowledge_base: id, title, content, category

Auth: Email/password for support agents only. Customers interact via email.
```

### Example 2: Lead Capture Landing Page

```
Build a high-converting lead capture page for a B2B SaaS company.

WHAT IT DOES:
- Hero section with headline, subheadline, and email capture form
- When someone submits their email: save to Supabase, send welcome email via Resend,
  redirect to a thank-you page
- Admin dashboard (password-protected) showing all captured leads with date,
  email, and source (UTM parameters)

STACK: Next.js, Supabase, Tailwind, Resend

DESIGN: Dark theme, modern SaaS aesthetic. Reference Linear.app.
Blue accent (#3B82F6). Inter font.

Must track UTM parameters (source, medium, campaign) from the URL.
```

### Example 3: Content Generator Dashboard

```
Build a content generation dashboard for a marketing team.

CORE FEATURES:
1. Input form: topic, target audience, tone, content type (blog/social/email)
2. Generate content using Claude API with customized system prompts per content type
3. Save generated content to a library (Supabase)
4. Edit generated content inline with a rich text editor
5. Export as markdown or copy to clipboard

STACK: Next.js, Supabase, Tailwind, Claude API

DATA MODEL:
- content: id, title, type, topic, audience, tone, body, status (draft/final), created_at
- templates: id, name, type, system_prompt, user_prompt_template

Auth: Email/password. Each user sees only their own content.

Design: Clean, minimal. Left sidebar with content library, main area for
generation and editing. Light theme, subtle gray borders.
```

---

## Testing Steps

1. **Auth flow:** Create account, log in, log out, forgot password, session persistence across refresh
2. **Core feature:** Complete the primary user action end-to-end — verify data saves and displays correctly
3. **CRUD operations:** Create, read, update, delete for every entity — verify at the database level
4. **Mobile responsiveness:** Test at 375px, 768px, 1024px, 1440px viewports
5. **Edge cases:** Empty states, validation errors, long text, double submissions, unauthorized access attempts
6. **Performance:** Page loads under 2 seconds, no console errors, Lighthouse score 80+
7. **Deploy test:** Deploy to Vercel, verify all env vars are set, test every feature on the live URL
8. **Client walkthrough:** Share the live URL with the client, watch them use it (screenshare), note any confusion

## Success Criteria

- Client can use the app without asking you how (the Loom covers onboarding)
- All core actions from the scope doc work correctly on desktop and mobile
- No console errors in production
- Page load time under 2 seconds
- App handles edge cases gracefully (no crashes, clear error messages)
- Client has access to all credentials and accounts
- Maintenance plan is documented and agreed upon
- You shipped in the timeline you quoted (or communicated early if delayed)
