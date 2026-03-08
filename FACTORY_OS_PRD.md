# Factory OS — The Complete Pipeline PRD

## The Big Picture

This is a factory. Not a tool, not a platform — a factory.

Raw materials come in one end (your ideas, rants, sketches, screenshots, competitor links). Finished products come out the other end (shipped, tested, deployed applications). In between, a series of automated stations do the work. You sit in Mission Control watching dashboards, and only step in at a few checkpoints to say "yep, looks good" or "nah, change this."

### The Factory Floor

```
 RAW MATERIALS                                                    FINISHED GOODS
 (ideas, rants)                                                   (shipped apps)
      │                                                                 ▲
      ▼                                                                 │
 ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
 │ INTAKE   │──▶│ PRD      │──▶│ PRD      │──▶│ BUILD    │──▶│ LAUNCH   │
 │ DOCK     │   │ MAKER    │   │ POLISHER │   │ FLOOR    │   │ BAY      │
 │          │   │          │   │          │   │          │   │          │
 │ Stage 0  │   │ Stg 1-8  │   │ 9 specs  │   │ AutoForge│   │ Deploy + │
 │          │   │          │   │          │   │ builds   │   │ ship     │
 └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
      │              │              │              │              │
      └──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       MISSION CONTROL        │
                    │                              │
                    │  Intake ........ ● READY     │
                    │  PRD Maker ..... ◌ idle      │
                    │  PRD Polisher .. ◌ idle      │
                    │  Build Floor ... ◌ idle      │
                    │  Launch Bay .... ◌ idle      │
                    │                              │
                    │  ⚑ NEEDS YOUR EYES: 0       │
                    │  ✓ SHIPPED TODAY:   0        │
                    │                              │
                    │  [ Approve ]  [ Pause All ]  │
                    └──────────────────────────────┘
```

## How It All Connects

| Station | What Happens | Human Checkpoint? | Your Time |
|---------|-------------|-------------------|-----------|
| **Intake Dock** | You dump files, rants, screenshots. System auto-tags them. | No — just dump and go | 2-5 min |
| **PRD Maker** | AI asks you clarifying questions, builds structured PRD (Standards → Product → Features → Specs) | Yes — review feature list | 15-30 min |
| **PRD Polisher** | 9 specialist agents analyze and perfect every angle of the PRD | Yes — review final report | 5 min scan |
| **Build Floor** | AutoForge agents build the actual code, feature by feature | No — fully automated | Hours (you're gone) |
| **Launch Bay** | Testing, docs, deployment, go-to-market prep | Yes — final approval | 5 min scan |

**Total human time per project: ~30-45 minutes of actual attention.**

Everything else runs while you do other stuff.

---

## Station 1: Intake Dock (Already Designed)

See AGENT_OS_PRD.md → "Project Intake Dock" section. Drag and drop files, auto-tagging, readiness checklist. This is Stage 0 — the loading dock where raw materials arrive.

## Station 2: PRD Maker (Already Designed)

See AGENT_OS_PRD.md → Stages 1-8. Takes raw input, asks questions, generates 3-layer context (Standards / Product / Specs). This is the first processing station — turns raw ideas into structured blueprints.

---

## Station 3: PRD Polisher — THE NEW SYSTEM

### Why This Exists

The PRD Maker gets you 80% there. It solidifies the idea, creates a starting point, structures everything into specs. But 80% isn't enough for a robotic build. Build agents need ZERO ambiguity. Every edge case covered. Every technical decision justified. Every dependency mapped. Every acceptance criterion testable.

The Polisher is a team of 9 specialist agents. Each one looks at the PRD through a different lens. Together, they catch everything a single generalist agent would miss.

Think of it like this: the PRD Maker is the architect who draws the blueprints. The Polisher is the review board — the structural engineer, the electrical engineer, the fire marshal, the accessibility inspector, the cost estimator — who all sign off before construction begins.

### The 9 Specialists

Each specialist runs as its own AI agent session. They read the entire PRD (all 3 layers: Standards, Product, Specs), analyze it from their domain expertise, and produce a report. Reports include:

- **PASS** items — things that are solid, no changes needed
- **FLAG** items — things that work but could be better (suggestions, non-blocking)
- **BLOCK** items — things that MUST be fixed before build (ambiguous, missing, or wrong)

After all 9 run, their reports merge into a single Polisher Report that you review in 5 minutes.

---

#### Specialist 1: Frontend Architect

**Domain:** Everything the user sees and touches.

**What they check:**
- Component hierarchy — are all UI components identified? Is the tree logical?
- State management — where does state live? Is it over-engineered or under-planned?
- Routing — all routes defined? Navigation flows make sense?
- Responsive design — are breakpoints specified? Mobile-first or desktop-first?
- Design system — consistent tokens, colors, typography across all specs?
- Accessibility — WCAG compliance baked into specs? Keyboard nav? Screen reader support?
- Performance — lazy loading? Code splitting? Bundle size concerns?
- Client-side validation — form validation rules specified?
- Component reuse — same pattern used in 3 places but specced differently?

**Output: Frontend Architecture Review**
- Component tree diagram
- State management map
- Route map with all paths
- Missing UI specs (things the build agent will have to guess without)
- Accessibility gaps
- Performance recommendations

**Common BLOCKs this specialist finds:**
- "Feature 5 spec says 'show a list of items' but doesn't specify: pagination or infinite scroll? Sorting? Filtering? Empty state?"
- "Features 3 and 7 both define a modal component with different behavior — which is correct?"
- "No loading states specified for any API call — build agent will either skip them or invent them"

---

#### Specialist 2: Backend Architect

**Domain:** APIs, server logic, everything behind the UI.

**What they check:**
- API design — RESTful? GraphQL? Consistent naming? Proper HTTP methods?
- Data models — all entities identified? Relationships mapped? Field types specified?
- Database design — normalization appropriate? Indexes needed? Migration strategy?
- Authentication & authorization — auth flow complete? Role-based access? Token management?
- Error handling — error response format? Error codes defined? Retry strategies?
- Rate limiting — needed? Where? What limits?
- Caching strategy — what gets cached? TTLs? Invalidation rules?
- Background jobs — any async work? Queue system? Retry logic?
- File uploads — if applicable, storage strategy? Size limits? Type validation?
- Webhooks — outbound notifications needed? Payload format? Retry logic?

**Output: Backend Architecture Review**
- Entity relationship diagram (text-based)
- API endpoint inventory (method, path, request body, response body, auth required)
- Missing backend specs
- Security gaps
- Scalability concerns

**Common BLOCKs this specialist finds:**
- "Auth spec says 'users can log in' but doesn't specify: email/password? OAuth? Both? Password requirements?"
- "Feature 8 needs to send emails but no email service is in the tech stack"
- "API returns 'user' object in 4 different shapes across 4 endpoints — which is the canonical shape?"

---

#### Specialist 3: Data & Schema Specialist

**Domain:** Database tables, fields, relationships, data integrity.

**What they check:**
- Data integrity — all fields have types? Required vs optional clear? Default values?
- Relationships — foreign keys? Cascade rules? Orphan prevention?
- Validation rules — min/max lengths? Regex patterns? Enum values listed?
- Data flow — where does data originate? How does it transform? Where does it end up?
- Seed data — does the app need initial data? Admin accounts? Config values?
- Migration path — if evolving existing schema, is migration safe?
- Search & filtering — which fields need indexes? Full-text search needed?
- Data privacy — PII fields identified? Encryption at rest? GDPR/CCPA compliance?
- Soft delete vs hard delete — what happens when things get "deleted"?
- Audit trail — do we need to track who changed what and when?

**Output: Data Architecture Review**
- Complete schema definition (every table, every field, every type, every constraint)
- Data flow diagram (where data comes from → where it goes)
- Validation rule inventory
- Privacy assessment
- Index recommendations

**Common BLOCKs this specialist finds:**
- "User.email has no uniqueness constraint specified — can two users share an email?"
- "Feature 4 references a 'status' field with values 'active, inactive' but Feature 9 adds 'suspended, banned' — need a unified enum"
- "No timestamps on any table — build agent won't know to add created_at/updated_at"

---

#### Specialist 4: Security Auditor

**Domain:** Everything that could go wrong from a security perspective.

**What they check:**
- Authentication — is the auth flow secure? Token rotation? Session management?
- Authorization — RBAC/ABAC defined? Privilege escalation paths blocked?
- Input validation — all user inputs sanitized? SQL injection? XSS? CSRF?
- API security — rate limiting? CORS config? API key management?
- Data protection — encryption in transit (TLS)? At rest? Key management?
- Dependency security — known vulnerable packages? Supply chain concerns?
- Secrets management — no hardcoded secrets? .env patterns correct?
- OWASP Top 10 — systematic check against all 10 categories
- Compliance — regulatory requirements met? (GDPR, HIPAA, SOC2, etc.)
- File upload security — if applicable, executable upload prevention? Virus scanning?

**Output: Security Assessment**
- Threat model (what could go wrong, ranked by severity)
- Vulnerability inventory (things to fix in PRD before build)
- Security requirements to add to specs
- Compliance checklist

**Common BLOCKs this specialist finds:**
- "Password reset flow not specified — this is a critical auth gap"
- "User-generated content displayed without sanitization spec — XSS risk"
- "Admin endpoints exist but no admin role is defined in the auth system"

---

#### Specialist 5: UX Flow Analyst

**Domain:** The human experience of using the app.

**What they check:**
- User journeys — are all critical paths mapped end-to-end?
- Edge cases — what happens on empty states? Errors? Timeout? No network?
- Onboarding — first-time user experience defined?
- Loading states — every async operation has a loading indicator?
- Error states — every failure has a user-friendly error message?
- Success states — confirmations for destructive/important actions?
- Navigation — can the user always get back? Breadcrumbs? Back buttons?
- Micro-interactions — hover states, transitions, feedback animations?
- Content strategy — placeholder text defined? Real content examples?
- Accessibility flows — can every journey be completed with keyboard only?
- Offline behavior — what happens when connection drops mid-action?

**Output: UX Flow Assessment**
- User journey maps (happy path + error paths for each feature)
- Missing states inventory (empty, loading, error, success)
- Usability risk assessment
- Content requirements list

**Common BLOCKs this specialist finds:**
- "What happens when a user tries to access a page they don't have permission for? No spec."
- "Delete action has no confirmation dialog specified — users will accidentally delete things"
- "First-time user sees an empty dashboard — no onboarding, no empty state, no guidance"

---

#### Specialist 6: Testing Strategist

**Domain:** How we verify the build actually works.

**What they check:**
- Test coverage plan — unit tests, integration tests, E2E tests for every feature
- Acceptance criteria — are they testable? Can a machine verify them?
- Edge case tests — boundary conditions, null inputs, concurrent access
- Performance tests — load testing plan? Benchmarks defined?
- Security tests — penetration test scenarios? Auth bypass attempts?
- Regression strategy — what gets re-tested when a feature changes?
- Test data — fixtures needed? Mock APIs? Seed databases?
- CI/CD integration — test pipeline defined? Quality gates?
- Browser/device matrix — which browsers? Which screen sizes?
- Flaky test prevention — async operations properly awaited? Race conditions handled?

**Output: Test Strategy Document**
- Test plan per feature (what gets tested, how, with what data)
- Test data requirements
- CI/CD pipeline recommendations
- Quality gate definitions (what must pass before deploy)

**Common BLOCKs this specialist finds:**
- "Acceptance criterion says 'page loads fast' — what's fast? Need a number (e.g., < 2 seconds)"
- "Feature 6 has no acceptance criteria at all — build agent can't verify it works"
- "12 features share the same database but no integration test verifies they don't corrupt each other's data"

---

#### Specialist 7: DevOps & Infrastructure Planner

**Domain:** Where the app runs and how it gets there.

**What they check:**
- Deployment target — where does this run? Cloud? VPS? Serverless? Edge?
- Environment setup — dev, staging, prod configs defined?
- CI/CD pipeline — build, test, deploy steps clear?
- Monitoring — what gets monitored? Alerts? Logging strategy?
- Scaling — horizontal? Vertical? Auto-scaling rules?
- Backup & recovery — database backups? Disaster recovery plan?
- Domain & SSL — domain configured? Certificates managed?
- Environment variables — all env vars documented? Secrets managed?
- Docker/container strategy — if containerized, Dockerfile specs?
- Cost estimation — expected infrastructure costs at launch? At scale?
- Health checks — how do we know the app is alive?

**Output: Infrastructure Plan**
- Deployment architecture diagram
- Environment configuration matrix (dev vs staging vs prod)
- CI/CD pipeline definition
- Monitoring and alerting plan
- Cost estimate (monthly at launch, monthly at 10x scale)

**Common BLOCKs this specialist finds:**
- "No deployment target specified anywhere — build agent can't write deploy configs"
- "App uses WebSockets but deployment target is a serverless platform that doesn't support them"
- "No logging strategy — when something breaks in prod, how do we debug?"

---

#### Specialist 8: Integration & Dependency Mapper

**Domain:** How pieces connect to each other and to the outside world.

**What they check:**
- Third-party APIs — all external services identified? Rate limits known? Fallback plans?
- Package dependencies — all npm/pip packages listed? Version constraints? License compliance?
- Internal dependencies — feature dependency graph valid? No circular deps? Build order optimal?
- Cross-feature interactions — do features that touch the same data models conflict?
- API versioning — if public API, versioning strategy defined?
- Webhook/event system — event-driven parts identified? Retry logic? Dead letter queues?
- Feature flags — any features that should be behind flags for gradual rollout?
- Migration from existing systems — data import? API compatibility? Transition plan?
- Environment compatibility — does everything work on the target OS/runtime?

**Output: Dependency & Integration Map**
- External service inventory (API name, auth method, rate limits, cost, fallback)
- Package manifest with versions and licenses
- Feature dependency graph (validated, no cycles, optimal build order)
- Integration risk assessment (what's most likely to break)

**Common BLOCKs this specialist finds:**
- "Feature 3 depends on Feature 7 which depends on Feature 3 — circular dependency"
- "Stripe integration referenced but no Stripe API version specified — breaking changes risk"
- "Feature 12 uses a package that's been deprecated for 2 years — suggest alternative"

---

#### Specialist 9: Go-to-Market Planner

**Domain:** Everything after "it works" — getting it to users.

**What they check:**
- Landing page — content defined? Value proposition clear? CTA obvious?
- Documentation — user docs? API docs? Developer guides?
- Onboarding flow — signup, first-use experience, tutorials?
- Analytics — what user events get tracked? Funnel defined?
- SEO — meta tags, sitemap, structured data defined?
- Social proof — testimonials, case studies, demo accounts?
- Pricing strategy — if monetized, pricing tiers defined? Payment integration?
- Launch checklist — what needs to be true before going live?
- Support system — how do users get help? FAQ? Chat? Email?
- Legal — terms of service? Privacy policy? Cookie consent?

**Output: Go-to-Market Plan**
- Launch readiness checklist
- Marketing asset requirements
- Analytics event plan (what to track, why)
- Documentation outline
- Legal requirements

**Common BLOCKs this specialist finds:**
- "App collects email addresses but no privacy policy exists — legal requirement"
- "No analytics plan — you won't know if users are actually using the features you built"
- "Pricing page exists in specs but no payment provider is in the tech stack"

---

### How the Polisher Pipeline Works

```
                    PRD from Maker
                         │
                         ▼
         ┌───────────────────────────────┐
         │     POLISHER ORCHESTRATOR     │
         │                               │
         │  Distributes PRD to all 9     │
         │  specialists in parallel      │
         └───────────┬───────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
   │ Batch 1 │ │ Batch 2 │ │ Batch 3 │
   │         │ │         │ │         │
   │Frontend │ │Security │ │Testing  │
   │Backend  │ │UX Flow  │ │DevOps   │
   │Data     │ │         │ │Integr.  │
   │         │ │         │ │GTM      │
   └────┬────┘ └────┬────┘ └────┬────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │      REPORT SYNTHESIZER      │
         │                               │
         │  Merges 9 reports into one    │
         │  Deduplicates findings        │
         │  Ranks by severity            │
         │  Groups by spec/feature       │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │       AUTO-FIX ENGINE        │
         │                               │
         │  BLOCK items with >90%        │
         │  confidence fix → auto-fix    │
         │  FLAG items → suggestions     │
         │  Remaining BLOCKs → human     │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │    ★ HUMAN CHECKPOINT ★      │
         │                               │
         │  "Here's the 5-min report"    │
         │                               │
         │  BLOCKs fixed: 12/14 auto     │
         │  BLOCKs need you: 2           │
         │  FLAGs: 23 (suggestions)      │
         │  PASSes: 89                   │
         │                               │
         │  [ View Details ] [ Approve ] │
         └───────────┬───────────────────┘
                     │
                     ▼
              Polished PRD → Build Floor
```

### The 5-Minute Report

This is what you actually see. Not 9 separate reports — one merged view:

```
┌─────────────────────────────────────────────────────────┐
│  PRD POLISHER REPORT — MyTaskApp                        │
│  ═══════════════════════════════════════════════════     │
│                                                         │
│  SCORECARD                                              │
│  ┌──────────────┬────────┬────────┬────────┐           │
│  │ Specialist   │ PASS   │ FLAG   │ BLOCK  │           │
│  ├──────────────┼────────┼────────┼────────┤           │
│  │ Frontend     │  12    │   3    │   0    │           │
│  │ Backend      │  15    │   2    │   1    │           │
│  │ Data/Schema  │   9    │   1    │   1    │           │
│  │ Security     │   8    │   4    │   0    │           │
│  │ UX Flow      │  11    │   3    │   0    │           │
│  │ Testing      │   7    │   2    │   0    │           │
│  │ DevOps       │   6    │   3    │   0    │           │
│  │ Integration  │  10    │   2    │   0    │           │
│  │ GTM          │  11    │   3    │   0    │           │
│  ├──────────────┼────────┼────────┼────────┤           │
│  │ TOTAL        │  89    │  23    │   2    │           │
│  └──────────────┴────────┴────────┴────────┘           │
│                                                         │
│  ⚠ 2 BLOCKS NEED YOUR INPUT:                           │
│                                                         │
│  1. [Backend] Auth spec doesn't specify password        │
│     reset flow. Options:                                │
│     a) Email-based reset (recommended)                  │
│     b) SMS-based reset                                  │
│     c) Both                                             │
│                                                         │
│  2. [Data] User.email has no uniqueness constraint.     │
│     Should it be unique?                                │
│     a) Yes, unique per account (recommended)            │
│     b) No, allow duplicates                             │
│                                                         │
│  ✅ 12 BLOCKS AUTO-FIXED:                               │
│  (click to expand and review)                           │
│                                                         │
│  💡 23 SUGGESTIONS:                                     │
│  (click to expand — non-blocking)                       │
│                                                         │
│  [ Apply Recommended & Approve ]  [ Review All ]        │
└─────────────────────────────────────────────────────────┘
```

You answer the 2 questions, hit approve, done. 5 minutes. The PRD is now build-ready.

### What the Auto-Fix Engine Does

Not every BLOCK needs a human. Many have obvious answers:

| BLOCK Type | Auto-Fix | Confidence |
|-----------|----------|------------|
| Missing timestamps on tables | Add created_at, updated_at to all tables | 99% |
| No loading states specified | Add loading state to every async operation | 95% |
| No error response format | Use standard `{ error: string, code: number }` | 93% |
| Missing 404 page | Add standard 404 page to route specs | 97% |
| No favicon specified | Use project name initial as placeholder | 91% |
| Password min length not set | Set to 8 characters minimum | 92% |
| No CSRF protection mentioned | Add CSRF tokens to all form submissions | 94% |
| Missing input max lengths | Add sensible defaults (255 for names, 5000 for text fields) | 90% |

The auto-fix engine applies fixes above the confidence threshold (default: 90%) and logs every fix so you can review them. If you don't like an auto-fix, you override it in the report.

### What Stays BLOCK (Needs You)

These are decisions only a human can make:

- Business logic choices ("Should free users see this feature?")
- Technology choices where trade-offs are close ("PostgreSQL vs MongoDB for this use case")
- Scope decisions ("Is this feature MVP or post-launch?")
- Design decisions ("What color scheme? What brand voice?")
- Legal/compliance choices ("Do we need HIPAA compliance?")
- Pricing decisions ("What should each tier include?")
- Content decisions ("What's the tagline? What's the hero text?")

---

### The Polisher's Secret Weapon: Cross-Specialist Conflict Detection

The Report Synthesizer doesn't just merge reports — it detects CONFLICTS between specialists:

| Conflict Type | Example | Resolution |
|--------------|---------|------------|
| Frontend ↔ Backend | Frontend spec says "paginated list" but backend API returns all items | BLOCK: align on pagination approach |
| Security ↔ UX | Security wants 2FA on every login, UX says that kills conversion | FLAG: suggest "remember device" compromise |
| DevOps ↔ Backend | Backend uses WebSockets but DevOps picked serverless (no WS support) | BLOCK: must change one or the other |
| Testing ↔ Scope | Testing wants 90% coverage but scope has 25 features for MVP | FLAG: suggest coverage tiers (critical > nice-to-have) |
| GTM ↔ Security | GTM wants public API docs, Security wants API keys on everything | FLAG: suggest authenticated docs portal |
| Data ↔ Backend | Data schema says User has `role` field, Backend spec never reads it | FLAG: dead field — remove or wire it up |
| Frontend ↔ UX | Frontend specifies a dropdown, UX says the list is too long for dropdowns | FLAG: suggest searchable combobox instead |
| Integration ↔ DevOps | External API has 99.5% uptime SLA but app promises 99.9% | BLOCK: can't promise higher uptime than your dependencies |

These cross-specialist conflicts are the things that cause expensive mid-build pivots. The Polisher catches them BEFORE a single line of code is written.

---

### Polisher Configuration

```yaml
polisher:
  # Which specialists to run (all by default)
  enabled_specialists:
    - frontend_architect
    - backend_architect
    - data_specialist
    - security_auditor
    - ux_analyst
    - testing_strategist
    - devops_planner
    - integration_mapper
    - gtm_planner

  # Parallelism — how many specialists run at once
  batch_size: 3
  max_concurrent: 3

  # Auto-fix behavior
  auto_fix_threshold: 90     # Confidence % needed to auto-fix a BLOCK
  auto_apply_flags: false    # Auto-apply FLAG suggestions? (default: no, just suggest)

  # Report format
  report_detail: summary     # summary | detailed | full
  group_by: specialist       # specialist | feature | severity

  # Smart skip — don't run specialists that don't apply
  skip_if_no_frontend:
    - frontend_architect     # Skip frontend review if no UI in the project
  skip_if_no_backend:
    - backend_architect      # Skip backend review if frontend-only app
    - data_specialist
  skip_for_prototype:        # Skip these in YOLO/prototype mode
    - security_auditor
    - devops_planner
    - gtm_planner
    - testing_strategist
```

---

## Station 4: Build Floor (Already Built)

This is AutoForge. Already exists and works. The Polished PRD feeds directly into the existing build pipeline:

- Features.db populated with perfect specs (zero ambiguity)
- Dependency graph validated (no cycles, optimal build order)
- Build agents execute feature by feature
- Mission Control shows real-time progress (passing/failing/in-progress)

The key difference: because the PRD went through the Polisher, the build agents almost never get stuck asking "what did they mean by this?" Every spec is clear enough for robotic execution.

---

## Station 5: Launch Bay

After the Build Floor finishes all features, the app enters the Launch Bay for final prep before shipping.

### Launch Bay Sub-Stations

#### 5a: Regression Testing
- Full test suite runs against the complete build
- All features verified against acceptance criteria from the polished specs
- Cross-feature integration tests
- Performance benchmarks checked
- Security scan (automated OWASP check)

#### 5b: Documentation Generator
Auto-generates from the codebase + specs:
- User documentation (how to use each feature)
- API documentation (endpoint reference)
- README with setup instructions
- Architecture decision records (from Polisher's decisions.log)
- Changelog (features built, in order)

#### 5c: Deployment Prep
Based on DevOps specialist's infrastructure plan:
- Dockerfile generated (if containerized)
- CI/CD pipeline configured (GitHub Actions, Vercel, etc.)
- Environment variables documented with example .env
- Domain/SSL setup instructions
- Health check endpoints verified

#### 5d: Go-to-Market Prep
Based on GTM specialist's plan:
- Landing page generated (if specced)
- Analytics events wired up
- SEO basics configured (meta tags, sitemap, robots.txt)
- Legal pages generated from templates (Terms of Service, Privacy Policy)
- Social sharing meta tags

#### 5e: Launch Readiness Report — Final Human Checkpoint

```
┌─────────────────────────────────────────────┐
│  LAUNCH READINESS — MyTaskApp               │
│  ═══════════════════════════════════════     │
│                                             │
│  ✅ All 22 features passing                 │
│  ✅ 147 tests passing, 0 failing            │
│  ✅ Security scan: no critical issues       │
│  ✅ Performance: p95 < 200ms                │
│  ✅ Docs generated: 12 pages                │
│  ✅ Deploy config ready                     │
│  ⚠️  Landing page: needs your review        │
│  ⚠️  Analytics: 3 events not wired yet      │
│                                             │
│  [ Preview App ]                            │
│  [ Preview Landing Page ]                   │
│  [ Deploy to Staging ]                      │
│  [ Ship to Production ]                     │
│                                             │
└─────────────────────────────────────────────┘
```

You scan it. Everything green? Hit "Ship to Production." Done.

---

## Mission Control — The NASA Room

### What You See

One screen. Everything on it. Multiple projects flowing through the factory simultaneously.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FACTORY OS — MISSION CONTROL                              10:42 AM   │
│  ═══════════════════════════════════════════════════════════════════    │
│                                                                       │
│  ACTIVE PROJECTS                                                      │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │ MyTaskApp       [■■■■■■■■░░] 78%  Build Floor  ● ACTIVE    │      │
│  │ FitnessTracker  [■■■■■░░░░░] 45%  PRD Polisher ● ACTIVE    │      │
│  │ InvoiceApp      [■■░░░░░░░░] 20%  PRD Maker    ⚑ REVIEW    │      │
│  │ ChatBot         [░░░░░░░░░░]  0%  Intake Dock  ◌ QUEUED    │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                       │
│  ⚑ NEEDS YOUR EYES: 1 (InvoiceApp — review feature list)             │
│                                                                       │
│  FACTORY THROUGHPUT                                                   │
│  ┌───────────────────────────────────┐                                │
│  │ Today:     2 projects in pipeline │                                │
│  │ This week: 5 projects shipped     │                                │
│  │ Avg time:  4.2 hours per project  │                                │
│  │ Success:   94% first-build pass   │                                │
│  └───────────────────────────────────┘                                │
│                                                                       │
│  STATION STATUS                                                       │
│  Intake Dock .... 1 queued                                            │
│  PRD Maker ...... 1 in review                                         │
│  PRD Polisher ... 1 running (specialist 5/9)                          │
│  Build Floor .... 1 building (feature 14/22)                          │
│  Launch Bay ..... 0                                                   │
│                                                                       │
│  [ New Project ]  [ View All ]  [ Settings ]                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mission Control Features

- **Multi-project pipeline** — see all projects at once, where they are in the factory
- **Review queue** — items that need your eyeballs float to the top with ⚑ flags
- **Throughput metrics** — how many projects shipped, average build time, success rate
- **Station status** — which stations are busy, idle, or blocked
- **One-click approve** — review items inline, approve without drilling in
- **Priority queue** — drag projects to reorder what builds next
- **Pause/resume** — pause any station or project without losing progress
- **Alerts** — browser notifications when something needs you (optional: mobile push, email)
- **History** — every project that ever went through the factory, searchable
- **Drill-down** — click any project to see detailed station view (features, logs, agent activity)

---

## The Complete Pipeline — End to End

Here's what happens when you have an idea at 9 AM:

| Time | What Happens | What You Do |
|------|-------------|-------------|
| 9:00 | You rant into the Intake Dock. Dump files. Hit process. | 3 minutes of talking/pasting |
| 9:03 | PRD Maker starts asking you questions | 15 min of back-and-forth |
| 9:18 | PRD Maker shows feature list for review | 2 min — "yep looks right" |
| 9:20 | PRD Maker generates detailed specs | Automatic — go refill coffee |
| 9:25 | PRD Polisher runs 9 specialists in parallel | Automatic — you're doing other stuff |
| 9:35 | Polisher Report ready | 5 min — answer 2 questions, hit approve |
| 9:40 | Build Floor starts — AutoForge agents building | You're completely free |
| 12:30 | Build complete, Launch Bay starts | Automatic |
| 1:00 | Launch Readiness Report | 5 min — scan report, hit "ship" |
| 1:05 | **App is live** | |

**Total elapsed: 4 hours. Your actual attention: ~30 minutes.**

---

## What Makes This Different

### vs. Other AI Coding Tools
**Other tools:** "Here's a prompt box. Write a good prompt. Good luck."
**Factory OS:** "Dump your brain. We'll structure it, validate it with 9 specialists, build it, test it, ship it."

### vs. Traditional Development
**Traditional:** 2-week sprint, 5-person team, daily standups, Jira tickets, code reviews, QA cycles.
**Factory OS:** One person, one dashboard, 4 hours, shipped.

### vs. No-Code Platforms
**No-code:** "Drag and drop blocks. Hit the ceiling when you need custom logic."
**Factory OS:** Real code, real architecture, no ceiling. But the human never touches code.

### vs. Cursor / Copilot / Windsurf
**Those tools:** Help you write code faster while you're coding.
**Factory OS:** You never write code. You describe what you want, review the plan, and approve the ship.

---

## Implementation Priority

### What Already Exists (in AutoForge)
- Intake Dock (designed in AGENT_OS_PRD.md, not built yet)
- PRD Maker stages 1-8 (designed in AGENT_OS_PRD.md, not built yet)
- Build Floor (AutoForge — fully built and working)
- Single-project Mission Control UI (partially built)

### What's New in This PRD
1. **PRD Polisher** — 9 specialists + orchestrator + report synthesizer + auto-fix engine
2. **Launch Bay** — post-build automation (testing, docs, deploy, GTM)
3. **Multi-project Mission Control** — seeing everything at once
4. **Factory throughput metrics** — how many shipped, success rates
5. **Review queue system** — items needing human eyes float to top
6. **Cross-specialist conflict detection** — catching contradictions before build

### Build Priority Order
1. **PRD Polisher** — highest-value new addition. This is what turns "okay builds" into "perfect builds."
2. **Multi-project Mission Control** — the factory experience. Without this, it's just a pipeline, not a factory.
3. **Launch Bay** — nice to have but not urgent. Builds can be manually deployed for now.

---

## Relationship to Other Documents

| Document | What It Contains | Relationship to Factory OS |
|----------|-----------------|---------------------------|
| **AGENT_OS_PRD.md** | Detailed design for Intake Dock + PRD Maker (Stations 1-2) | Factory OS wraps around it, adds Polisher + Launch Bay + Mission Control |
| **BASE_BUILD_PRD.md** | The build engine mechanics (12 mechanisms) | Station 4 (Build Floor) runs on this |
| **OPERATIONAL_TRUTH_v3.md** | Master architecture vision | Factory OS is the user-facing layer on top of everything |
| **Agent OS Integration Guide** | How users provide context to Claude Code sessions | The portable/manual version of what Factory OS automates |

---

## Appendix A: Specialist Agent Prompt Templates

Each specialist gets a system prompt that defines their domain, checklist, and output format. These prompts live at:

```
agent-os/pipeline/specialists/
├── 01-frontend-architect.md
├── 02-backend-architect.md
├── 03-data-specialist.md
├── 04-security-auditor.md
├── 05-ux-analyst.md
├── 06-testing-strategist.md
├── 07-devops-planner.md
├── 08-integration-mapper.md
└── 09-gtm-planner.md
```

Each prompt follows this structure:

```markdown
# You are the [Specialist Name]

## Your Domain
[What you're responsible for reviewing]

## Your Checklist
[Every item you must verify — the full list from this PRD]

## Your Output Format
For each checklist item, report:
- **PASS**: [item] — [why it's solid]
- **FLAG**: [item] — [what could be better] — [suggestion]
- **BLOCK**: [item] — [what's wrong/missing] — [recommended fix] — [confidence %]

## Cross-References
When you find something that affects another specialist's domain, note it as:
- **CROSS-REF → [Other Specialist]**: [what they should check]

## Your Constraints
- Do NOT suggest changes outside your domain — flag them as CROSS-REF instead
- Do NOT auto-fix anything — report findings only, the Auto-Fix Engine handles fixes
- Do NOT duplicate findings from the Standards layer — if the standard covers it, it's a PASS
- Be SPECIFIC — "could be better" is not useful. "Add pagination with 25 items per page default" is useful.
```

---

## Appendix B: Full Polisher Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    POLISHER DATA FLOW                            │
│                                                                 │
│  INPUT:                                                         │
│  ├── agent-os/standards/*.md          (Standards Layer)         │
│  ├── .agent/product/*.md              (Product Layer)           │
│  ├── .agent/specs/feature-*.md        (Specs Layer)             │
│  └── .agent/features.db              (Dependency Graph)         │
│                                                                 │
│  PROCESSING:                                                    │
│  ├── 9 Specialist Agents (parallel, 3 batches of 3)            │
│  ├── Report Synthesizer (merge + dedup + conflict detect)      │
│  └── Auto-Fix Engine (apply high-confidence fixes)             │
│                                                                 │
│  OUTPUT:                                                        │
│  ├── .agent/polisher/report.md        (Merged report)          │
│  ├── .agent/polisher/auto-fixes.md    (Applied auto-fixes)     │
│  ├── .agent/polisher/conflicts.md     (Cross-specialist)       │
│  ├── .agent/polisher/specialist-01.md (Individual reports)     │
│  ├── .agent/polisher/specialist-02.md                          │
│  ├── ...                                                        │
│  ├── .agent/specs/feature-*.md        (UPDATED with fixes)     │
│  └── .agent/progress/decisions.log    (APPENDED)               │
│                                                                 │
│  HUMAN REVIEW:                                                  │
│  ├── Scorecard (PASS/FLAG/BLOCK counts per specialist)         │
│  ├── Remaining BLOCKs (questions for human)                    │
│  ├── Auto-fix log (what was fixed automatically)               │
│  └── Suggestions (FLAGs, non-blocking improvements)            │
└─────────────────────────────────────────────────────────────────┘
```

---

*End of Factory OS PRD.*
