# PRDM Maker — Full PRD (Agent OS 3-Layer Format)

> **Eating our own food.** This PRD was written using the exact format, protocols, and
> dependency system that the PRDM Maker itself will produce for its users.

**Version:** 1.0.0
**Date:** 2026-03-18
**Status:** Implementation-Ready
**Estimated Build:** ~255K tokens (single Opus phase)
**Boilerplate:** Web-BoilerPlate-D2D (Next.js 15 + Supabase + Stripe)
**Branch:** `claude/finish-prd-maker-3BL56`

---

# LAYER 1: STANDARDS — Universal Infrastructure

## 1.1 System Identity

| Field | Value |
|-------|-------|
| System Name | PRDM Maker |
| Tagline | "Idea to PRD in minutes, not days" |
| Platform | Web SaaS (Next.js) + future mobile (Flutter) |
| Architecture | Multi-stage AI pipeline with tiered access |
| AI Backend | AutoForge capsule/rocket connection (Claude subscription) |
| Input | Unstructured text (rants, ideas, specs), existing codebases |
| Output | Structured PRDs in Agent OS 3-layer format (Standards/Product/Specs) |
| Primary User | Solo developers, indie hackers, startup founders, product managers |
| Revenue Model | Tiered SaaS subscription + per-use credits + a la carte upsells |

## 1.2 Design Principles

1. **Zero Detail Loss** — Every mechanism, constraint, and preference the user mentions appears in the final PRD. The system reformats but never summarizes away specifics. [USER]
2. **Protocol-Driven Builds** — Light, Medium, and Heavy protocols determine how much human oversight each build gets. Users choose their level. [USER]
3. **Eat Our Own Food** — This product was designed, specced, and will be built using the exact same pipeline it sells. [USER]
4. **API-First** — Every feature is an API endpoint first, UI second. Mobile client plugs in later with zero backend changes. [USER]
5. **SaaS-Native Piping** — Tier gating, credits, usage tracking, and access control are built into the architecture from day one, not retrofitted. [USER]
6. **Capsule/Rocket Pattern** — Owner's personal instance connects to AutoForge via the capsule pattern for subscription-based AI. SaaS version uses API keys with credit metering. [USER]

## 1.3 Technology Stack

### Foundation: Web-BoilerPlate-D2D (Already Built)

| Layer | Technology | Status |
|-------|-----------|--------|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui | EXISTS in boilerplate |
| Backend | Supabase (PostgreSQL, Auth, Edge Functions, Realtime) | EXISTS in boilerplate |
| Payments | Stripe (subscriptions + one-time charges) | EXISTS in boilerplate |
| Auth | Supabase Auth (email/password, Google, GitHub OAuth) | EXISTS in boilerplate |
| Analytics | PostHog (frontend + backend unified) | EXISTS in boilerplate |
| Email | Loops.so (transactional emails) | EXISTS in boilerplate |
| Hosting | Vercel (Next.js) + Supabase Cloud | EXISTS in boilerplate |
| Mobile (future) | Flutter + Supabase + Riverpod | EXISTS in boilerplate (separate dir) |

### New Additions (Build Required)

| Layer | Technology | Why |
|-------|-----------|-----|
| AI Pipeline | Anthropic SDK (`anthropic` Python SDK via Edge Functions or serverless) | PRD generation stages |
| Dependency Graph | dagre + React Flow (pattern from AutoForge) | Build planning visualization |
| Credit System | Supabase + Stripe metered billing | Per-use charges + subscription limits |
| Real-time Updates | Supabase Realtime (already available) | Pipeline progress streaming |
| File Storage | Supabase Storage | PRD documents, uploaded specs, codebases |

### What We're Rebuilding from AutoForge (Reference Only)

These components exist as working models in AutoForge. We study the patterns and rebuild clean implementations — **zero imports, zero coupling**.

| AutoForge Component | What We Take | Our Implementation |
|--------------------|--------------|--------------------|
| `DependencyGraph.tsx` | dagre layout, node styling, status tracking | New component in Next.js with shadcn/ui |
| `dependency_resolver.py` | Kahn's algorithm, cycle detection, scheduling scores | TypeScript implementation in Edge Functions |
| `feature_mcp.py` | Atomic claiming, ready/blocked queries | Supabase RPC functions |
| `agent_os_mechanism.py` | 6-dimension scoring, Developer's Choice modes | TypeScript service |
| `agent_os_features.py` | Gap analysis, coverage assessment | TypeScript service |
| `agent_os_specs.py` | Per-feature spec generation | TypeScript service |

## 1.4 Protocol System

### What Protocols Are

Protocols define how much human oversight vs AI autonomy a build gets. They're the core differentiator — users pick their comfort level.

### Light Protocol (Speed Mode)
- **When:** User trusts the system. "Just build it."
- **Human touchpoints:** 0 during pipeline execution
- **AI decides:** All mechanism choices (Developer's Choice Mode 2)
- **Verification:** Automated only (Stage N.5 verifiers run, no human review)
- **Pulsing:** Status updates emitted at stage boundaries only
- **Seams:** None — stages flow without pause
- **Cost:** Lowest (fewest tokens, no interactive stages)
- **SaaS tier:** Available on all paid plans

### Medium Protocol (Balanced Mode)
- **When:** User wants input on close calls only
- **Human touchpoints:** 2-5 (only when score gap < 15%)
- **AI decides:** Clear winners automatically (Developer's Choice Mode 3)
- **Verification:** Automated + human reviews close-call mechanisms
- **Pulsing:** Status updates at every stage, detail on close calls
- **Seams:** Pause at close-call mechanisms for user input, auto-resume after
- **Cost:** Medium
- **SaaS tier:** Available on all paid plans

### Heavy Protocol (Full Control)
- **When:** User wants to review everything
- **Human touchpoints:** Every mechanism, every stage output
- **AI decides:** Nothing without approval (Developer's Choice Mode 1)
- **Verification:** Full automated + human review at every stage
- **Pulsing:** Continuous — every sub-step emits progress
- **Seams:** Pause between every stage for human review/edit
- **Cost:** Highest (most tokens, most interactive stages)
- **SaaS tier:** Pro and above

### Pulsing (Progress Emission)

"Pulsing" is the real-time progress system. Every stage in the pipeline emits structured progress events:

```typescript
interface PulseEvent {
  stage: string;           // "intake", "classify", "gap_analysis", etc.
  stage_number: number;    // 1, 1.5, 2, 2.5, etc.
  status: "started" | "processing" | "awaiting_input" | "complete" | "error";
  progress_pct: number;    // 0-100 within this stage
  detail: string;          // Human-readable status
  token_usage: {
    input: number;
    output: number;
    cumulative: number;
  };
  timestamp: string;
}
```

The frontend subscribes to Supabase Realtime and renders:
- Progress bar across all stages
- Current stage detail card
- Token/credit usage gauge
- Time elapsed per stage

### Seams (Pause Points)

"Seams" are intentional pause points where the pipeline stops and waits for human input before continuing. Protocol level determines which seams are active:

| Seam Point | Light | Medium | Heavy |
|------------|-------|--------|-------|
| After Intake (review extracted items) | skip | skip | PAUSE |
| After Classification (review sections) | skip | skip | PAUSE |
| After Gap Analysis (review questions) | skip | skip | PAUSE |
| Decision Facilitator (answer gaps) | auto-fill | auto-fill close calls only | PAUSE |
| After Mechanism Scoring (review choices) | skip | PAUSE on close calls | PAUSE all |
| After PRD Draft (review full PRD) | skip | skip | PAUSE |
| Quality Gate (review score) | auto-pass if ≥ 3.0 | auto-pass if ≥ 3.0 | PAUSE |

## 1.5 Capsule/Rocket Connection Pattern

### Owner's Personal Instance
```
┌─────────────────────┐     ┌──────────────────┐
│   PRDM Maker Web    │────▶│   AutoForge       │
│   (Next.js on       │     │   (localhost:8888) │
│    Vercel/local)     │     │                    │
│                      │     │   Claude SDK       │
│   "Capsule"         │     │   Subscription     │
│   Sends prompts     │◀────│   "Rocket"         │
│   Receives PRDs     │     │   Runs AI calls    │
└─────────────────────┘     └──────────────────┘
```
- Capsule = the PRDM Maker web app (sends structured prompts)
- Rocket = AutoForge backend (executes AI calls via Claude subscription)
- Connection = REST API or WebSocket between capsule and rocket
- Auth = shared secret / local network (owner's machine)
- Cost = $0 incremental (uses existing Claude Max subscription)

### SaaS Multi-Tenant Instance
```
┌─────────────────────┐     ┌──────────────────┐
│   PRDM Maker Web    │────▶│   Serverless AI   │
│   (Vercel)          │     │   (Edge Functions) │
│                      │     │                    │
│   User dashboard    │     │   Anthropic API    │
│   Credit system     │◀────│   Metered billing  │
│   Tier gating       │     │   Per-user keys    │
└─────────────────────┘     └──────────────────┘
```
- Each user's AI calls go through Supabase Edge Functions
- Usage tracked per-user in `credits` table
- Stripe metered billing for overages
- API key per tenant (or pooled with rate limiting)

## 1.6 SaaS Tier Architecture

### Tier Definitions

| Tier | Monthly | PRDs/mo | Feature Adds/mo | Boilerplate | Protocol | Credits |
|------|---------|---------|-----------------|-------------|----------|---------|
| Free | $0 | 1 | 0 | None | Light only | 0 |
| Starter | $29 | 5 | 10 | None | Light + Medium | 50 |
| Pro | $79 | Unlimited | Unlimited | 3 included | All protocols | 200 |
| Team | $199 | Unlimited | Unlimited | Unlimited | All + collaboration | 500 |

### Per-Use Charges (A La Carte)

| Item | Price | Description |
|------|-------|-------------|
| Boilerplate Use | $47 | Clone and configure a boilerplate repo |
| Extra Credits (50 pack) | $19 | For AI pipeline overages |
| Codebase Reality Scan | $29 | Reverse-engineer existing code into PRD |
| Priority Processing | $9/run | Skip queue, dedicated compute |

### Credit System

Every AI pipeline stage consumes credits based on token usage:

```
1 credit = ~10K tokens processed
Light protocol PRD ≈ 40-60 credits
Medium protocol PRD ≈ 50-70 credits
Heavy protocol PRD ≈ 65-100 credits
Feature addition ≈ 30-50 credits
Codebase reality scan ≈ 20-40 credits
```

Credits are:
- Included in monthly tier allocation
- Rollover: NO (use it or lose it)
- Overage: Charged at $0.38/credit via Stripe metered billing
- Tracked: Real-time in dashboard with usage gauge

### Tier Gating Implementation

```typescript
// middleware pattern for tier-gated features
interface TierGate {
  feature: string;
  required_tier: "free" | "starter" | "pro" | "team";
  credit_cost: number;
  check: (user: User) => { allowed: boolean; reason?: string };
}

const TIER_GATES: TierGate[] = [
  { feature: "prd_create", required_tier: "free", credit_cost: 50 },
  { feature: "feature_addition", required_tier: "starter", credit_cost: 35 },
  { feature: "heavy_protocol", required_tier: "pro", credit_cost: 0 },
  { feature: "codebase_reality", required_tier: "pro", credit_cost: 30 },
  { feature: "boilerplate_use", required_tier: "pro", credit_cost: 0 }, // separate charge
  { feature: "collaboration", required_tier: "team", credit_cost: 0 },
  { feature: "api_access", required_tier: "team", credit_cost: 0 },
];
```

---

# LAYER 2: PRODUCT — Application Definition

## 2.1 Core Pipeline (The PRD Machine)

The heart of the product. Takes unstructured input → produces structured PRD.

### Stage Map

```
Stage 0:   Intake Dock ............. File/text staging UI
Stage 1:   Intake .................. Classify + extract entities
Stage 1.5: Transcription Verifier .. [SEAM: Heavy only]
Stage 2:   Standards ............... Questionnaire or infer
Stage 3:   Product Discovery ....... 6 adaptive questions
Stage 3.5: Technical Refinement .... Babble → tech language
Stage 4:   Feature Extraction ...... Claude extracts features
Stage 4.5: Coverage Assessment ..... "You've described ~45%"
Stage 5:   Recalibration ........... Resolve contradictions
Stage 5.5: Gap Analysis ............ Cross-layer gaps
Stage 6:   Mechanism Analysis ...... 6-dim scoring + Dev Choice
Stage 6.5: Mechanism Verifier ...... [SEAM: Medium + Heavy]
Stage 7:   Spec Generation ......... Per-feature markdown specs
Stage 7.5: PRD Verifier ............ [SEAM: Heavy only]
Stage 8:   Final Blueprint ......... Companion sheet
Stage 9:   Golden Orange ........... Feature imagination
Stage 10:  Quality Gate ............ Score 1-5, block if < 2.0
Stage 11:  Handoff ................. Context primer + export
```

### Two Input Modes

**Questionnaire Mode:**
- Step-by-step guided form
- ~15 structured questions
- Best for: first-time users, people who like structure

**Rant Mode:**
- Free-form text dump
- "Just describe your idea however you want"
- AI extracts and organizes
- Best for: experienced users, stream-of-consciousness thinkers

### Developer's Choice (Mechanism Scoring)

Every technical decision gets scored on 6 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Implementation Speed | 20% | How fast to build |
| Maintainability | 20% | Long-term code health |
| User Experience | 20% | End-user quality |
| Security | 15% | Attack surface |
| Cost | 10% | Infrastructure costs |
| Brand Alignment | 15% | Fits product identity |

Three interaction modes:
1. **Full Control** — Review every mechanism (Heavy protocol)
2. **Developer's Choice** — Auto-accept all top-scored options (Light protocol)
3. **Exceptions Only** — Auto-select when gap > 15%, review close calls (Medium protocol)

### Provenance Tags

Every item in the PRD carries a tag showing its origin:

| Tag | Meaning |
|-----|---------|
| `[USER]` | Directly stated by user |
| `[AUTO_FILL]` | System inferred with high confidence |
| `[USER_DECIDED]` | User chose from options |
| `[RECOMMENDED]` | Developer's Choice, accepted |
| `[DETECTED]` | Reverse-engineered from code |
| `[INFERRED]` | System inferred from context |

## 2.2 Feature Addition Engine

Users don't just create PRDs — they evolve them. The Feature Addition Engine:

1. Takes new feature ideas (rant or structured)
2. Deduplicates against existing PRD
3. Checks compatibility with existing mechanisms
4. Scores new mechanisms with same 6 dimensions
5. Merges into existing PRD (living document, versioned)

```
Feature Rant + Existing PRD → F1: Transcribe → F2: Impact Classify →
F3: Gap Analysis → F4: Decisions → F5: Mechanism Score →
F6: PRD Merge → Updated PRD v1.x.0
```

## 2.3 Codebase Reality Engine

For users with existing software and no PRD:

**With Code Access:**
```
Codebase → R1: Code Scanner → R2: Architecture Extractor →
R3: AB-PRD Generator → R4: Drift Analyzer (if original PRD exists) →
Reconciled PRD (current state of truth)
```

**Without Code Access:**
```
User Description → D1: Transcribe → D2: Inference Engine →
D3: Descriptive AB-PRD → Reconciled PRD (lower confidence)
```

## 2.4 Dependency Graph & Build Planning

Rebuilt from AutoForge patterns. Shows the build order for features as an interactive graph.

### Data Model (Supabase)

```sql
CREATE TABLE prd_features (
  id SERIAL PRIMARY KEY,
  prd_id UUID REFERENCES prds(id),
  name TEXT NOT NULL,
  category TEXT,
  priority INTEGER DEFAULT 999,
  status TEXT DEFAULT 'pending', -- pending, in_progress, done, blocked
  dependencies JSONB DEFAULT '[]', -- array of feature IDs
  spec_content TEXT,
  provenance TEXT DEFAULT 'USER',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Graph Visualization

- React Flow + dagre layout (same pattern as AutoForge)
- Node colors by status: pending (gray), in_progress (blue), done (green), blocked (red)
- Click node to see spec, dependencies, and provenance
- Interactive: drag, zoom, pan, minimap
- Export as image or JSON

### Dependency Resolution

- Kahn's algorithm for topological sort with priority heap
- Cycle detection via DFS with depth limit (50)
- Scheduling scores: `(1000 * unblock_factor) + (100 * depth_score) + (10 * priority_factor)`
- Ready features: all dependencies in "done" status
- Blocked features: at least one dependency not "done"

## 2.5 Boilerplate System

Boilerplates are pre-configured starter repos that users can clone:

### Available Boilerplates (Phase 1)

| ID | Name | Stack | Price |
|----|------|-------|-------|
| `web-nextjs-supabase` | Web SaaS Starter | Next.js + Supabase + Stripe | $47/use |
| `web-nextjs-firebase` | Web Firebase Starter | Next.js + Firebase + Stripe | $47/use |

### Future Boilerplates (Phase 2 — Mobile)

| ID | Name | Stack | Price |
|----|------|-------|-------|
| `mobile-flutter-supabase` | Mobile Flutter Starter | Flutter + Supabase + RevenueCat | $47/use |
| `mobile-flutter-firebase` | Mobile Firebase Starter | Flutter + Firebase + RevenueCat | $47/use |

### Boilerplate Flow

1. User creates PRD
2. System recommends boilerplate based on PRD tech stack
3. User selects (or skips) boilerplate
4. Stripe charges $47 one-time
5. System clones repo into user's project directory
6. PRD context primer injected into `CLAUDE.md`
7. User runs AutoForge or builds manually

## 2.6 Dashboard & User Experience

### Main Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  PRDM Maker                    [Credits: 142] [Profile] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  My PRDs                              [+ New PRD]        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ App X    │ │ App Y    │ │ App Z    │                 │
│  │ v1.2.0   │ │ v1.0.0   │ │ Draft    │                │
│  │ 12 feats │ │ 8 feats  │ │ 45%      │                │
│  │ ✅ Done  │ │ 🔄 Build │ │ 📝 Edit  │                │
│  └──────────┘ └──────────┘ └──────────┘                │
│                                                          │
│  Recent Activity                                         │
│  • App X: Feature Addition complete (v1.2.0)            │
│  • App Y: Build started (Phase 3/7)                     │
│  • App Z: Gap Analysis in progress                      │
│                                                          │
│  Usage This Month                                        │
│  ██████████░░░░░░░░ 142/200 credits                     │
│  PRDs: 3/unlimited | Feature Adds: 7/unlimited           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### PRD Detail View

```
┌──────────────────────────────────────────────────────────┐
│  ← Back    App X PRD    v1.2.0    [Export] [Build]      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [Standards] [Product] [Specs] [Graph] [History]         │
│                                                          │
│  ┌─ Standards ──────────────────────────────────────┐   │
│  │  System: Task management SaaS                     │   │
│  │  Stack: Next.js + Supabase + Stripe              │   │
│  │  Auth: Magic Links [RECOMMENDED]                  │   │
│  │  DB: PostgreSQL [USER]                           │   │
│  │  ...                                              │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  [Dependency Graph]                                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  (Auth) ──▶ (Dashboard) ──▶ (Settings)           │   │
│  │     │                                             │   │
│  │     ▼                                             │   │
│  │  (API) ──▶ (Search) ──▶ (Export)                 │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Pipeline Progress View (During PRD Creation)

```
┌──────────────────────────────────────────────────────────┐
│  Creating PRD: App X    Protocol: Medium                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ████████████░░░░░░░░░░░░ Stage 6/11 (55%)             │
│                                                          │
│  ✅ Intake              ✅ Standards                     │
│  ✅ Product Discovery   ✅ Feature Extraction            │
│  ✅ Gap Analysis        🔄 Mechanism Scoring             │
│  ⬚ Spec Generation     ⬚ Blueprint                     │
│  ⬚ Golden Orange       ⬚ Quality Gate                  │
│  ⬚ Handoff                                              │
│                                                          │
│  ⚠️ CLOSE CALL — Your input needed:                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  UI-003: Timeline Visualization                   │   │
│  │  React Flow (78.5%) vs CSS Grid (72.1%)          │   │
│  │  Gap: 6.4% — Could go either way                 │   │
│  │                                                    │   │
│  │  [Accept React Flow] [Choose CSS Grid] [Details]  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Credits used: 34 | Elapsed: 4m 22s                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 2.7 Export & Integration

### PRD Export Formats

| Format | Description | Tier |
|--------|-------------|------|
| Markdown | Full 3-layer PRD as `.md` file | All |
| JSON | Machine-readable structured data | Starter+ |
| AutoForge `app_spec.txt` | Ready to drop into AutoForge and build | Pro+ |
| PDF | Professional formatted document | Pro+ |
| Notion | Import-ready Notion page | Team |

### AutoForge Bridge (Capsule → Rocket)

For Pro+ users, the PRD can be directly handed off to AutoForge:

1. PRD exports as `app_spec.txt` in AutoForge format
2. Features populate `features.db` with dependencies and specs
3. Context primer generated for the builder agent
4. User clicks "Build with AutoForge" → launches build session

## 2.8 Caveat Appendix System

When mechanism scores are close (gap < 15%), the losing option is preserved:

```markdown
## Appendix: Alternative Mechanisms

### UI-003: Timeline Visualization
- **Selected:** React Flow (78.5%) [RECOMMENDED]
- **Alternative:** CSS Grid + Canvas (72.1%)
- **Score Gap:** 6.4% (CLOSE)
- **Switch Trigger:** If React Flow bundle size impacts mobile load times
- **Switch Cost:** HIGH — 5-7 day refactor
- **Files Affected:** TimelineView.tsx, ProjectCard.tsx
```

This appendix is part of the PRD, not a separate document. It travels with the PRD forever.

---

# LAYER 3: SPECS — Feature Implementation Details

## Feature Inventory

### Phase 1: Foundation (Build on Boilerplate)

| ID | Feature | Priority | Dependencies | Credits | Tier |
|----|---------|----------|--------------|---------|------|
| F01 | Auth System (Supabase) | 1 | — | 0 | EXISTS |
| F02 | Stripe Subscription Integration | 1 | F01 | 0 | EXISTS |
| F03 | Credit System (DB + API) | 1 | F01, F02 | — | All |
| F04 | Tier Gating Middleware | 1 | F03 | — | All |
| F05 | Intake Dock UI | 2 | F01 | — | All |
| F06 | Rant Mode Pipeline (Stages 1-11) | 2 | F05 | — | All |
| F07 | Questionnaire Mode Pipeline | 2 | F05 | — | All |
| F08 | Developer's Choice Scoring Engine | 2 | F06 | — | All |
| F09 | Provenance Tag System | 2 | F06 | — | All |
| F10 | PRD Dashboard (List + Detail) | 2 | F01 | — | All |

### Phase 2: Core Experience

| ID | Feature | Priority | Dependencies | Credits | Tier |
|----|---------|----------|--------------|---------|------|
| F11 | Pipeline Progress UI (Pulsing) | 3 | F06 | — | All |
| F12 | Seam System (Pause Points) | 3 | F06, F11 | — | Medium+ |
| F13 | Protocol Selector (Light/Medium/Heavy) | 3 | F12 | — | All |
| F14 | PRD Export (Markdown + JSON) | 3 | F06 | — | All |
| F15 | Quality Gate (Score + Block) | 3 | F06 | — | All |
| F16 | Golden Orange (Feature Imagination) | 3 | F15 | — | Pro+ |
| F17 | Dependency Graph Visualization | 3 | F06 | — | All |
| F18 | Mechanism Report UI | 3 | F08 | — | All |
| F19 | Caveat Appendix Generator | 3 | F08 | — | All |
| F20 | Credit Usage Dashboard | 3 | F03 | — | All |

### Phase 3: Growth Features

| ID | Feature | Priority | Dependencies | Credits | Tier |
|----|---------|----------|--------------|---------|------|
| F21 | Feature Addition Engine | 4 | F06, F17 | 35 | Starter+ |
| F22 | Codebase Reality Engine (with code) | 4 | F06 | 30 | Pro+ |
| F23 | Codebase Reality Engine (no code) | 4 | F06 | 20 | Starter+ |
| F24 | PRD Versioning (Living Document) | 4 | F06, F21 | — | Starter+ |
| F25 | AutoForge Bridge Export | 4 | F14 | — | Pro+ |
| F26 | Boilerplate Selection + Clone | 4 | F02 | 47/use | Pro+ |
| F27 | Verification Agents (Stage N.5) | 4 | F06 | — | All |
| F28 | PDF Export | 5 | F14 | — | Pro+ |
| F29 | Notion Export | 5 | F14 | — | Team |
| F30 | API Access (Public REST API) | 5 | F04 | — | Team |

### Phase 4: Mobile Prep & Polish

| ID | Feature | Priority | Dependencies | Credits | Tier |
|----|---------|----------|--------------|---------|------|
| F31 | API Documentation (auto-generated) | 5 | F30 | — | Team |
| F32 | Collaboration (shared PRDs) | 5 | F01 | — | Team |
| F33 | Usage Analytics Dashboard (Admin) | 5 | F03 | — | Internal |
| F34 | Mobile API Endpoints (Flutter-ready) | 6 | F30 | — | Future |
| F35 | Webhook Notifications | 6 | F06 | — | Pro+ |

---

## Spec: F03 — Credit System

### Database Schema

```sql
-- User credit balance and usage tracking
CREATE TABLE user_credits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  balance INTEGER NOT NULL DEFAULT 0,
  lifetime_used INTEGER NOT NULL DEFAULT 0,
  tier TEXT NOT NULL DEFAULT 'free',
  tier_monthly_allocation INTEGER NOT NULL DEFAULT 0,
  last_refill_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Credit transaction log (append-only)
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL, -- positive = add, negative = consume
  balance_after INTEGER NOT NULL,
  reason TEXT NOT NULL, -- 'monthly_refill', 'prd_create', 'feature_add', 'purchase', 'boilerplate'
  reference_id UUID, -- PRD ID, purchase ID, etc.
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policies
ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own credits" ON user_credits
  FOR SELECT USING (auth.uid() = user_id);

ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own transactions" ON credit_transactions
  FOR SELECT USING (auth.uid() = user_id);
```

### API Endpoints

```
GET  /api/credits           → { balance, tier, monthly_allocation, usage_this_month }
POST /api/credits/consume   → { amount, reason, reference_id } → { new_balance, transaction_id }
POST /api/credits/purchase  → { pack_size } → Stripe checkout URL
GET  /api/credits/history   → [{ amount, reason, created_at, ... }]
```

### Monthly Refill Logic (Edge Function)

```typescript
// Triggered by Supabase cron job on 1st of each month
async function refillCredits() {
  const allocations = { free: 0, starter: 50, pro: 200, team: 500 };
  // Reset balance to tier allocation (no rollover)
  await supabase.rpc('refill_monthly_credits', { allocations });
}
```

---

## Spec: F06 — Rant Mode Pipeline

### Architecture

Each pipeline stage is a Supabase Edge Function that:
1. Receives the accumulated context from previous stages
2. Constructs a prompt for Claude
3. Calls the Anthropic API
4. Parses the structured JSON response
5. Stores results in the PRD record
6. Emits a pulse event via Supabase Realtime
7. Returns stage output for the next stage

### PRD Record Schema

```sql
CREATE TABLE prds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  version TEXT NOT NULL DEFAULT '1.0.0',
  status TEXT NOT NULL DEFAULT 'draft', -- draft, in_progress, complete, failed
  protocol TEXT NOT NULL DEFAULT 'light', -- light, medium, heavy
  input_mode TEXT NOT NULL DEFAULT 'rant', -- rant, questionnaire

  -- Stage outputs (JSONB for flexibility)
  intake_output JSONB,
  standards_output JSONB,
  product_output JSONB,
  features_output JSONB,
  gaps_output JSONB,
  mechanisms_output JSONB,
  specs_output JSONB,
  blueprint_output JSONB,
  golden_orange_output JSONB,
  quality_score REAL,

  -- Final PRD content
  prd_markdown TEXT,
  prd_json JSONB,

  -- Metadata
  total_tokens_used INTEGER DEFAULT 0,
  total_credits_used INTEGER DEFAULT 0,
  current_stage TEXT,
  current_stage_number REAL,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE prds ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own PRDs" ON prds
  FOR ALL USING (auth.uid() = user_id);
```

### Pipeline Orchestrator

```typescript
// Supabase Edge Function: /functions/pipeline/orchestrate
async function orchestratePipeline(prdId: string, protocol: Protocol) {
  const stages = getStagesForProtocol(protocol);

  for (const stage of stages) {
    // Emit pulse: stage started
    await emitPulse(prdId, stage, "started");

    // Check if this is a seam point that requires human input
    if (stage.isSeam && protocol !== "light") {
      await emitPulse(prdId, stage, "awaiting_input");
      // Wait for user input via Realtime channel
      const userInput = await waitForUserInput(prdId, stage);
      if (userInput.action === "skip") continue;
    }

    // Execute stage
    const result = await executeStage(prdId, stage);

    // Deduct credits
    await consumeCredits(prdId, stage.creditCost);

    // Emit pulse: stage complete
    await emitPulse(prdId, stage, "complete", result);

    // Store result
    await updatePrdStageOutput(prdId, stage.name, result);
  }

  // Final: compile full PRD markdown
  await compilePrd(prdId);
}
```

---

## Spec: F08 — Developer's Choice Scoring Engine

### Scoring Function

```typescript
interface MechanismOption {
  id: string;
  name: string;
  scores: {
    implementation_speed: number; // 0-100
    maintainability: number;
    user_experience: number;
    security: number;
    cost: number;
    brand_alignment: number;
  };
}

interface ScoringWeights {
  implementation_speed: number; // 0.20
  maintainability: number;     // 0.20
  user_experience: number;     // 0.20
  security: number;            // 0.15
  cost: number;                // 0.10
  brand_alignment: number;     // 0.15
}

function scoreOptions(
  options: MechanismOption[],
  weights: ScoringWeights
): ScoredMechanism {
  const scored = options.map(opt => ({
    ...opt,
    weighted_score: Object.entries(weights).reduce(
      (sum, [dim, weight]) => sum + (opt.scores[dim] * weight), 0
    ),
  }));

  scored.sort((a, b) => b.weighted_score - a.weighted_score);

  const gap = scored[0].weighted_score - scored[1].weighted_score;
  const gapCategory = gap > 15 ? "clear_winner" : gap > 5 ? "close_call" : "very_close";

  return {
    options: scored,
    developer_choice: scored[0].id,
    score_gap: gap,
    gap_category: gapCategory,
    worktree_candidate: gap < 10 && getSwitchCost(scored[1]) !== "low",
  };
}
```

---

## Spec: F17 — Dependency Graph Visualization

### Component Architecture

```
DependencyGraph.tsx
├── Uses: @xyflow/react (React Flow)
├── Uses: dagre (automatic layout)
├── Uses: shadcn/ui (tooltips, badges)
│
├── FeatureNode (custom node component)
│   ├── Status badge (color-coded)
│   ├── Feature name + category
│   ├── Priority number
│   └── Provenance tag
│
├── Controls
│   ├── Layout toggle (horizontal/vertical)
│   ├── Zoom controls
│   └── Export button (PNG/JSON)
│
└── Legend
    ├── Pending (gray)
    ├── In Progress (blue)
    ├── Done (green)
    └── Blocked (red)
```

### Layout Algorithm

```typescript
function getLayoutedElements(nodes, edges, direction = "LR") {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 100,
    marginx: 50,
    marginy: 50,
  });

  nodes.forEach(node => g.setNode(node.id, { width: 220, height: 80 }));
  edges.forEach(edge => g.setEdge(edge.source, edge.target));

  dagre.layout(g);

  return {
    nodes: nodes.map(node => {
      const pos = g.node(node.id);
      return { ...node, position: { x: pos.x - 110, y: pos.y - 40 } };
    }),
    edges,
  };
}
```

### Cycle Detection (TypeScript Port)

```typescript
function detectCycles(features: Feature[]): string[][] {
  const adj = new Map<number, number[]>();
  features.forEach(f => adj.set(f.id, f.dependencies || []));

  const visited = new Set<number>();
  const recStack = new Set<number>();
  const cycles: number[][] = [];

  function dfs(node: number, path: number[]): void {
    visited.add(node);
    recStack.add(node);
    path.push(node);

    for (const dep of adj.get(node) || []) {
      if (recStack.has(dep)) {
        // Found cycle
        const cycleStart = path.indexOf(dep);
        cycles.push(path.slice(cycleStart));
      } else if (!visited.has(dep)) {
        dfs(dep, [...path]);
      }
    }

    recStack.delete(node);
  }

  features.forEach(f => {
    if (!visited.has(f.id)) dfs(f.id, []);
  });

  return cycles.map(c => c.map(id =>
    features.find(f => f.id === id)?.name || String(id)
  ));
}
```

---

## Spec: F11 — Pipeline Progress UI (Pulsing)

### Supabase Realtime Channel

```typescript
// Subscribe to pipeline progress
const channel = supabase
  .channel(`prd:${prdId}`)
  .on("broadcast", { event: "pulse" }, (payload) => {
    const pulse: PulseEvent = payload.payload;
    updateProgressUI(pulse);
  })
  .subscribe();
```

### Progress Component

```typescript
function PipelineProgress({ prdId }: { prdId: string }) {
  const [stages, setStages] = useState<StageStatus[]>(INITIAL_STAGES);
  const [currentPulse, setCurrentPulse] = useState<PulseEvent | null>(null);

  useEffect(() => {
    const channel = supabase
      .channel(`prd:${prdId}`)
      .on("broadcast", { event: "pulse" }, ({ payload }) => {
        setCurrentPulse(payload);
        setStages(prev => updateStageStatus(prev, payload));
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [prdId]);

  return (
    <div>
      <ProgressBar stages={stages} />
      <StageList stages={stages} />
      {currentPulse?.status === "awaiting_input" && (
        <SeamInput pulse={currentPulse} prdId={prdId} />
      )}
      <CreditGauge prdId={prdId} />
    </div>
  );
}
```

---

## Spec: F12 — Seam System (Pause Points)

### Seam Configuration

```typescript
const SEAM_CONFIG: Record<Protocol, SeamPoint[]> = {
  light: [], // No seams
  medium: [
    { stage: 6.5, name: "mechanism_close_calls", condition: "has_close_calls" },
  ],
  heavy: [
    { stage: 1.5, name: "review_intake", condition: "always" },
    { stage: 3, name: "review_standards", condition: "always" },
    { stage: 5.5, name: "review_gaps", condition: "always" },
    { stage: 6.5, name: "review_mechanisms", condition: "always" },
    { stage: 7.5, name: "review_prd", condition: "always" },
    { stage: 10, name: "review_quality", condition: "always" },
  ],
};
```

### Seam Wait/Resume

```typescript
// Server side: wait for user input at seam
async function waitForUserInput(prdId: string, seam: SeamPoint): Promise<UserInput> {
  return new Promise((resolve) => {
    const channel = supabase
      .channel(`prd:${prdId}:seam`)
      .on("broadcast", { event: "seam_response" }, ({ payload }) => {
        resolve(payload);
        supabase.removeChannel(channel);
      })
      .subscribe();
  });
}

// Client side: respond to seam
async function respondToSeam(prdId: string, response: UserInput) {
  await supabase
    .channel(`prd:${prdId}:seam`)
    .send({ type: "broadcast", event: "seam_response", payload: response });
}
```

---

## Dependency Graph for This Build

```
F01 (Auth) ──────────────────┬──▶ F03 (Credits) ──▶ F04 (Tier Gate) ──▶ F20 (Usage Dashboard)
  │                          │                                    │
  ├──▶ F05 (Intake Dock) ───┤                                    │
  │       │                  │                                    │
  │       ├──▶ F06 (Rant Pipeline) ──┬──▶ F08 (Dev Choice) ──▶ F18 (Mechanism Report)
  │       │       │                  │                    │
  │       │       │                  │                    └──▶ F19 (Caveat Appendix)
  │       │       │                  │
  │       │       ├──▶ F09 (Provenance)
  │       │       │                  │
  │       │       ├──▶ F11 (Pulsing) ──▶ F12 (Seams) ──▶ F13 (Protocol Selector)
  │       │       │
  │       │       ├──▶ F14 (Export MD+JSON) ──▶ F25 (AutoForge Bridge)
  │       │       │                         ├──▶ F28 (PDF Export)
  │       │       │                         └──▶ F29 (Notion Export)
  │       │       │
  │       │       ├──▶ F15 (Quality Gate) ──▶ F16 (Golden Orange)
  │       │       │
  │       │       ├──▶ F17 (Dependency Graph)
  │       │       │
  │       │       ├──▶ F21 (Feature Addition) ──▶ F24 (Versioning)
  │       │       │
  │       │       ├──▶ F22 (Codebase Reality - Code)
  │       │       │
  │       │       └──▶ F23 (Codebase Reality - No Code)
  │       │
  │       └──▶ F07 (Questionnaire Pipeline)
  │
  ├──▶ F10 (PRD Dashboard)
  │
  └──▶ F32 (Collaboration)

F02 (Stripe) ──▶ F26 (Boilerplate Clone)

F27 (Verification Agents) depends on F06

F30 (API Access) ──▶ F31 (API Docs)
                  └──▶ F34 (Mobile Endpoints)

F06 ──▶ F35 (Webhooks)
```

### Build Order (Topological Sort with Priority)

```
Wave 1 (Foundation):     F01, F02 [EXISTS - already in boilerplate]
Wave 2 (Payment+Auth):   F03, F04
Wave 3 (Core Pipeline):  F05, F06, F07, F08, F09
Wave 4 (UI+UX):          F10, F11, F12, F13, F14, F15, F17, F18, F19, F20
Wave 5 (Advanced):       F16, F21, F22, F23, F24, F25, F26, F27
Wave 6 (Scale):          F28, F29, F30, F31, F32, F33, F34, F35
```

---

# APPENDIX A: Token Budget Estimate

| Component | Estimated Tokens | Notes |
|-----------|-----------------|-------|
| Foundation (F01-F04) | ~15K | Mostly wiring existing boilerplate |
| Core Pipeline (F05-F09) | ~80K | Heaviest: the 11-stage AI pipeline |
| UI/UX (F10-F20) | ~60K | Dashboard, progress, graph, reports |
| Advanced (F21-F27) | ~55K | Feature addition, codebase reality |
| Scale (F28-F35) | ~45K | Export, API, collaboration |
| **Total** | **~255K** | **Single Opus phase** |

# APPENDIX B: Files to Create/Modify

### New Files (Next.js App)

```
nextjs/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx                    # Main dashboard
│   │   └── [prdId]/
│   │       ├── page.tsx                # PRD detail view
│   │       ├── graph/page.tsx          # Dependency graph view
│   │       └── pipeline/page.tsx       # Pipeline progress view
│   ├── api/
│   │   ├── credits/route.ts            # Credit endpoints
│   │   ├── prds/route.ts               # PRD CRUD
│   │   ├── prds/[id]/route.ts          # PRD detail
│   │   ├── prds/[id]/export/route.ts   # Export endpoints
│   │   └── pipeline/
│   │       ├── orchestrate/route.ts    # Pipeline orchestrator
│   │       └── seam/route.ts           # Seam response handler
│   └── pricing/page.tsx                # Pricing page
├── components/
│   ├── pipeline/
│   │   ├── PipelineProgress.tsx        # Progress bar + stages
│   │   ├── SeamInput.tsx               # Seam pause UI
│   │   ├── CreditGauge.tsx             # Credit usage display
│   │   └── ProtocolSelector.tsx        # Light/Medium/Heavy
│   ├── prd/
│   │   ├── PrdCard.tsx                 # Dashboard card
│   │   ├── PrdDetail.tsx               # Full PRD view
│   │   ├── IntakeDock.tsx              # File/text input
│   │   ├── RantInput.tsx               # Free-form rant
│   │   ├── QuestionnaireInput.tsx      # Guided questions
│   │   └── MechanismReport.tsx         # Scoring display
│   ├── graph/
│   │   ├── DependencyGraph.tsx         # React Flow + dagre
│   │   └── FeatureNode.tsx             # Custom node component
│   └── billing/
│       ├── CreditDisplay.tsx           # Balance + usage
│       ├── TierBadge.tsx               # Current tier indicator
│       └── PricingTable.tsx            # Tier comparison
├── lib/
│   ├── pipeline/
│   │   ├── stages.ts                   # Stage definitions
│   │   ├── scoring.ts                  # Developer's Choice engine
│   │   ├── provenance.ts              # Tag system
│   │   └── dependency-resolver.ts      # Kahn's algorithm + cycle detection
│   ├── credits.ts                      # Credit helpers
│   └── tier-gates.ts                   # Tier gating logic
└── hooks/
    ├── usePipeline.ts                  # Pipeline state + realtime
    ├── useCredits.ts                   # Credit balance + consumption
    └── usePrd.ts                       # PRD CRUD operations
```

### Supabase Files

```
supabase/
├── migrations/
│   ├── 20260318_credits.sql            # Credit tables
│   ├── 20260318_prds.sql               # PRD tables
│   └── 20260318_features.sql           # Feature/dependency tables
├── functions/
│   ├── pipeline-stage/index.ts         # Generic stage executor
│   ├── pipeline-orchestrate/index.ts   # Pipeline coordinator
│   └── credits-refill/index.ts         # Monthly credit refill
└── seed.sql                            # Test data
```

### Modified Files (From Boilerplate)

```
nextjs/
├── app/layout.tsx                      # Add dashboard nav
├── app/page.tsx                        # Landing page → product landing
├── components/landing/Pricing.tsx      # Update with our tiers
├── components/landing/Hero.tsx         # Update with our copy
└── middleware.ts                       # Add tier gating
```

# APPENDIX C: Mobile Preparation Checklist

Everything built now must be mobile-ready. Checklist:

- [ ] All business logic in `/lib/` (pure TypeScript, no React)
- [ ] All API endpoints return JSON (no HTML, no server components)
- [ ] Auth tokens passed via headers (not cookies) on API routes
- [ ] File uploads via presigned URLs (not form POST)
- [ ] WebSocket channels use standard Supabase Realtime (Flutter SDK compatible)
- [ ] No server-side-only dependencies in shared logic
- [ ] Credit/tier checks happen server-side (API validates, not client)

When mobile time comes, the Flutter app just calls the same API endpoints.

# APPENDIX D: Protocol Applied to This Build

This PRD was created using **Medium Protocol**:

- **Pulsing:** Progress tracked in conversation (research → structure → write → review)
- **Seams:** Paused twice for owner input (SaaS pricing confirmation, mobile scope)
- **Developer's Choice:** Auto-selected most mechanism choices (technology, architecture)
- **Exceptions reviewed:** SaaS tier pricing (close call between $29/$39 starter)
- **Provenance:** Tags applied throughout (see `[USER]` and `[RECOMMENDED]` markers)
- **Quality Gate:** Self-assessed at 4.2/5.0 (deductions: mobile specs are intentionally thin for now, some Edge Function implementation details TBD during build)

---

*End of PRD. This document is the single source of truth for the PRDM Maker build.
All changes go through the Feature Addition Engine (F21) once the system is live.
Version history tracked in the `prds` table.*
