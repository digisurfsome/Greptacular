# Rant-to-PRD: Enhanced Pipeline Addendum

## Additions to the Core Specification

**Version:** 1.1.0
**Date:** 2026-02-23
**Extends:** docs/rant-to-prd-spec.md v1.0.0

This document adds four major enhancements to the base Rant-to-PRD pipeline:

1. **Verification Agents** — Per-stage quality testing by a second AI
2. **Developer's Choice Scoring** — Unified mechanism report with scored recommendations
3. **Feature Addition Engine** — Adding features to an existing PRD/built software
4. **Codebase Reality Engine** — Reverse-engineering existing software into a PRD-equivalent

---

# ENHANCEMENT 1: Verification Agents

## The Problem

The base pipeline has structural validation (valid JSON, field counts, required keys) but no semantic validation. A classifier can put "user authentication" in the "Performance" section and the structural validator won't catch it — the JSON is valid, the item count matches, but the classification is wrong.

## The Solution: Stage N.5 Verifier Pattern

After each high-value stage, a separate agent reviews the worker's output against the input and quality criteria. The verifier is a different agent with a different prompt — it critiques rather than creates.

```
Worker Agent (Stage N) → Output → Verifier Agent (Stage N.5) → Pass/Fail
                                                                    |
                                                          Fail: Feed issues
                                                          back to Worker,
                                                          re-run with corrections
```

## Verifier Specifications

### Stage 1.5: Transcription Verifier

**Agent:** .claude/agents/rant-verify-transcription.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 16,384

**Prompt essence:**
```
You are a verification agent. You have two documents:
1. The original rant (raw input)
2. The transcription output (Stage 1 output)

Your job: verify that EVERY distinct idea, mechanism, feature, constraint,
preference, and vision in the original rant appears in the transcription.

For each item in the transcription, verify:
- The original_quote actually exists in the rant (not fabricated)
- The content accurately represents what the user said
- The item type classification is correct
- No detail was lost in the reformatting

Produce a verification report. For any issue found, cite the specific
rant passage and explain what was missed or misrepresented.
```

**Output:**
```json
{
  "metadata": {
    "stage": "1.5",
    "stage_name": "transcription_verifier",
    "verdict": "pass",  // or "fail"
    "issues_found": 2,
    "issues_critical": 0,
    "issues_minor": 2
  },
  "data": {
    "verification_results": [
      {
        "check": "item_completeness",
        "status": "pass",
        "detail": "All 47 items verified present in source"
      },
      {
        "check": "quote_accuracy",
        "status": "minor_issue",
        "detail": "item_023 quote truncated — missing 'and that is non-negotiable'",
        "rant_passage": "...the IP transfer only on final payment and that is non-negotiable...",
        "fix": "Extend original_quote to include full sentence"
      }
    ],
    "missing_from_transcription": [],
    "fabricated_content": [],
    "misclassified_items": []
  }
}
```

### Stage 2.5: Classification Verifier

**Agent:** .claude/agents/rant-verify-classification.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 16,384

**Verifies:**
- Each item is in the correct PRD section
- No item was placed based on a keyword match when the context suggests a different section
- Cross-references make sense (secondary sections are genuinely relevant)
- The item's content wasn't altered during classification

### Stage 5.5: Mechanism Verifier

**Agent:** .claude/agents/rant-verify-mechanisms.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 16,384

**Verifies:**
- Recommended approaches are consistent with project constraints from Stage 1
- Score percentages are justified by the pros/cons listed
- No approach contradicts a user-stated requirement
- Dependencies between mechanisms are correct
- Research sources (if cited) are plausible

### Stage 6.5: PRD Verifier

**Agent:** .claude/agents/rant-verify-prd.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 32,000

**Verifies:**
- Zero orphan items (every item from stages 1-5 appears in the PRD)
- Provenance tags are correct (USER items actually came from user, AUTO-FILL items were system-generated)
- Mechanism recommendations in the PRD match Stage 5 output
- The PRD is internally consistent (no section contradicts another)
- All sections have substantive content (not just headers)

## Verifier Integration in Pipeline

```bash
# Enhanced pipeline flow (inside rant-pipeline.sh)

# Stage 1 + Verification
run_stage 1 "..." ".claude/agents/rant-transcriber.md" "$PIPELINE_DIR/stage1/raw_capture.json"
run_verifier 1.5 "..." ".claude/agents/rant-verify-transcription.md" "$PIPELINE_DIR/stage1/verification_report.json"

# If verifier fails, re-run Stage 1 with corrections
if [[ "$(jq -r '.metadata.verdict' $PIPELINE_DIR/stage1/verification_report.json)" == "fail" ]]; then
    local issues=$(jq -c '.data' "$PIPELINE_DIR/stage1/verification_report.json")
    run_stage 1 "CORRECTION RUN. Previous issues: $issues. Fix all issues." \
        ".claude/agents/rant-transcriber.md" "$PIPELINE_DIR/stage1/raw_capture.json"
    run_verifier 1.5 "..." ".claude/agents/rant-verify-transcription.md" "$PIPELINE_DIR/stage1/verification_report.json"
fi
```

## Cost Impact

| Stage | Verifier Tokens (est.) | Cost Increase |
|-------|----------------------|---------------|
| 1.5 | 8K-12K | ~$0.15 |
| 2.5 | 10K-15K | ~$0.18 |
| 5.5 | 12K-18K | ~$0.22 |
| 6.5 | 20K-30K | ~$0.35 |
| **Total** | **50K-75K** | **~$0.90** |

Roughly 30-40% more tokens per run. For a $20-50 SaaS product, this is negligible.
For personal CLI use on a subscription, it's invisible.

---

# ENHANCEMENT 2: Developer's Choice — Unified Mechanism Scoring Report

## Concept

Developer's Choice is NOT a separate stage or a separate document. It's a **column in the unified mechanism report** that Stage 5 produces. Every mechanism gets scored, every mechanism gets a recommendation, and the user can accept all recommendations at once ("Developer's Choice for everything") or override individual mechanisms one by one.

## The Unified Mechanism Report

This replaces the simpler mechanism output from the base spec. Every mechanism now includes a multi-dimensional score:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ MECHANISM REPORT                                              Page 1/12 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ AUTH-001: User Authentication                                           │
│ ═══════════════════════════════                                         │
│                                                                         │
│                        Option A           Option B         Dev Choice   │
│                        Magic Links        Social Login     ◄────────   │
│ ─────────────────────  ───────────        ────────────                  │
│ Implementation Speed   85                 70                            │
│ Maintainability        90                 65                            │
│ User Experience        80                 85                            │
│ Security               88                 75                            │
│ Cost (infra)           95                 60                            │
│ Brand Alignment        92                 70                            │
│ ─────────────────────  ───────────        ────────────                  │
│ WEIGHTED SCORE         88.3%              71.2%            ● Option A   │
│                                                                         │
│ Score Gap: 17.1% — CLEAR WINNER                                        │
│                                                                         │
│ Key Differentiator: Magic links have zero third-party dependency        │
│ and align with the explicit "anti-corporate" brand requirement.         │
│                                                                         │
│ Why 88 vs 71: Social login scores higher on UX (faster click-through)  │
│ but loses significantly on maintainability (Google/GitHub API changes), │
│ cost (OAuth provider fees at scale), and brand alignment (corporate     │
│ feel). The 17-point gap makes this a clear recommendation.              │
│                                                                         │
│ Risk if wrong: LOW — switching from magic links to social login later   │
│ is a 1-2 day refactor. Not a bet-the-project decision.                 │
│                                                                         │
│ [✓ Accept Dev Choice] [○ Override: Choose Option B] [○ Override: Other] │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ UI-003: Project Timeline Visualization                                  │
│ ═══════════════════════════════════════                                  │
│                                                                         │
│                        Option A           Option B         Dev Choice   │
│                        React Flow         CSS Grid+Canvas  ◄────────   │
│ ─────────────────────  ───────────        ────────────                  │
│ Implementation Speed   82                 55                            │
│ Maintainability        85                 70                            │
│ User Experience        78                 83                            │
│ Security               N/A                N/A                           │
│ Cost (infra)           75                 90                            │
│ Brand Alignment        72                 80                            │
│ ─────────────────────  ───────────        ────────────                  │
│ WEIGHTED SCORE         78.5%              72.1%            ● Option A   │
│                                                                         │
│ Score Gap: 6.4% — CLOSE CALL ⚠️                                        │
│                                                                         │
│ Key Differentiator: React Flow is faster to implement with built-in     │
│ pan/zoom/interaction, but CSS Grid gives more visual control for the    │
│ "designer-first" brand promise.                                         │
│                                                                         │
│ Why close: Both are viable. React Flow wins on speed and maintenance.   │
│ CSS Grid wins on UX polish and brand alignment. The 6-point gap means  │
│ this could go either way depending on priorities.                       │
│                                                                         │
│ Risk if wrong: MEDIUM — switching timeline implementations mid-build    │
│ is a 5-7 day refactor. Worth getting right upfront.                    │
│                                                                         │
│ CLOSE CALL — Consider worktree branching (see Caveat Appendix)         │
│                                                                         │
│ [✓ Accept Dev Choice] [○ Override: Choose Option B] [○ Override: Other] │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Implementation Speed | 20% | How fast to build. Higher = faster. |
| Maintainability | 20% | Long-term code health, dependency stability |
| User Experience | 20% | End-user quality, polish, intuitiveness |
| Security | 15% | Attack surface, vulnerability risk |
| Cost | 10% | Infrastructure, licensing, API costs |
| Brand Alignment | 15% | How well it fits the product's stated identity/vibe |

Weights are defaults. The manifest or user preferences can adjust them (e.g., a security-focused product might weight Security at 30%).

## The Three Interaction Modes

### Mode 1: Full Control
User reviews every mechanism, sees scores, picks manually. Every mechanism has the checkboxes.

### Mode 2: Developer's Choice (One Click)
User clicks "Accept Developer's Choice for All Mechanisms." Every mechanism gets the top-scored option. Done in 2 seconds. The report is still generated — the user can review it later — but no per-mechanism decisions needed.

This is the power feature for SaaS. "I trust the system. Just build it."

### Mode 3: Review Exceptions Only
System auto-selects when score gap > 15%. Only presents close calls (gap < 15%) for user review. Best of both worlds — you make 3-4 decisions instead of 35.

```
Developer's Choice auto-selected 31 of 35 mechanisms (score gaps > 15%).
4 close calls need your input:

1. UI-003: Project Timeline (78.5% vs 72.1%) — 6.4% gap
2. DATA-007: Cache Strategy (71.2% vs 68.8%) — 2.4% gap
3. API-002: Pagination (75.1% vs 73.9%) — 1.2% gap
4. UX-011: Onboarding Flow (80.3% vs 76.7%) — 3.6% gap

Review these 4? Or accept Developer's Choice for all?
[Review 4 Close Calls] [Accept All Dev Choice]
```

## The Caveat Appendix

When mechanisms are close (gap < 15%), the losing option is preserved in a Caveat Appendix at the end of the PRD. This is NOT a separate document — it's part of the PRD itself.

```markdown
## Appendix: Alternative Mechanisms (Preserved)

These alternatives scored within 15% of the selected approach.
They are preserved because implementation complications may make
the alternative preferable. Each entry includes a switch trigger
and estimated switch cost.

### UI-003: Project Timeline Visualization
- **Selected:** React Flow (78.5%)
- **Alternative:** CSS Grid + Canvas (72.1%)
- **Score Gap:** 6.4% (CLOSE)
- **Switch Trigger:** If React Flow bundle size impacts mobile load times
  below the 2-second target, or if the design team needs pixel-level
  control that React Flow's node system can't provide.
- **Switch Cost:** HIGH — 5-7 day refactor
- **Files Affected:** TimelineView.tsx, ProjectCard.tsx, dashboard layout
- **Dependencies Affected:** None (self-contained component)
- **Git Worktree Available:** Yes — branch `alt/ui-003-css-grid` has a
  proof-of-concept implementation ready for evaluation.

### DATA-007: Cache Strategy
- **Selected:** Redis (71.2%)
- **Alternative:** In-Memory LRU (68.8%)
- **Score Gap:** 2.4% (VERY CLOSE)
- **Switch Trigger:** If deployment target doesn't support Redis (e.g.,
  serverless/edge), or if data volume stays under 100MB.
- **Switch Cost:** LOW — 1-2 day refactor
- **Files Affected:** cache.ts, api middleware
- **Dependencies Affected:** None
- **Git Worktree Available:** No — gap too small to warrant dual build
```

## Git Worktree Integration

For close-call mechanisms where the switch cost is HIGH:

```bash
# Pipeline creates worktree branches for close calls
git worktree add ../project-alt-ui-003 -b alt/ui-003-css-grid

# Both get built to proof-of-concept stage
# Evaluation agent (or user) compares working code
# Winner gets merged, loser stays as branch (not deleted)
```

**Worktree threshold:** Only created when:
1. Score gap < 10% AND
2. Switch cost is HIGH or MEDIUM AND
3. The mechanism is user-facing (not infrastructure)

This prevents wasting build time on every close call while protecting against expensive wrong choices.

## Stage 5 Output Schema (Enhanced)

```json
{
  "metadata": {
    "stage": 5,
    "stage_name": "mechanism_analyst",
    "version": "1.1.0",
    "total_mechanisms": 35,
    "clear_winners": 31,
    "close_calls": 4,
    "worktree_candidates": 1,
    "scoring_weights": {
      "implementation_speed": 0.20,
      "maintainability": 0.20,
      "user_experience": 0.20,
      "security": 0.15,
      "cost": 0.10,
      "brand_alignment": 0.15
    }
  },
  "data": {
    "mechanisms": [
      {
        "mechanism_id": "AUTH-001",
        "name": "User Authentication",
        "approaches": [
          {
            "approach_id": "opt_a",
            "name": "Magic Links",
            "scores": {
              "implementation_speed": 85,
              "maintainability": 90,
              "user_experience": 80,
              "security": 88,
              "cost": 95,
              "brand_alignment": 92
            },
            "weighted_score": 88.3
          },
          {
            "approach_id": "opt_b",
            "name": "Social Login",
            "scores": {
              "implementation_speed": 70,
              "maintainability": 65,
              "user_experience": 85,
              "security": 75,
              "cost": 60,
              "brand_alignment": 70
            },
            "weighted_score": 71.2
          }
        ],
        "score_gap": 17.1,
        "gap_category": "clear_winner",
        "developer_choice": "opt_a",
        "key_differentiator": "Zero third-party dependency, aligns with anti-corporate brand",
        "why_scores_differ": "Social login loses on maintainability and cost due to OAuth provider dependency",
        "risk_if_wrong": "low",
        "switch_cost_days": "1-2",
        "worktree_candidate": false
      }
    ],
    "close_calls": ["UI-003", "DATA-007", "API-002", "UX-011"],
    "worktree_candidates": ["UI-003"]
  }
}
```

---

# ENHANCEMENT 3: Feature Addition Engine

## The Problem

The base Rant-to-PRD pipeline creates a PRD from scratch. But software doesn't stop at v1. Users want to add features — sometimes one, sometimes ten at a time. They need a way to run new feature ideas through the same rigorous pipeline while respecting the existing PRD as the foundation.

Three scenarios:

1. **User has the original PRD** (made by our system) and wants to add features
2. **User has the original PRD** but the built software has drifted from the spec
3. **User has NO PRD** — they have existing software and want to start adding features properly

Scenarios 2 and 3 require the Codebase Reality Engine (Enhancement 4). Scenario 1 is handled here.

## Feature Addition Pipeline

When the user already has a PRD from our system:

```
Feature Rant (new ideas)
    ↓
Stage F1: Feature Transcriber (opus)
  → Same as Stage 1 but scoped: only extract NEW features/mechanisms
  → Input: feature rant + existing PRD (as context)
  → Deduplication: flag anything already covered by the existing PRD
    ↓
Stage F2: Impact Classifier (sonnet)
  → For each new feature, identify:
    - Which existing PRD sections it affects
    - Which existing mechanisms it depends on
    - Which existing mechanisms it might conflict with
    - Whether it requires new PRD sections
    ↓
Stage F3: Feature Gap Analyst (opus)
  → Same completeness checklist but SCOPED to the new features
  → What does THIS feature need that the existing PRD already covers? (free)
  → What does THIS feature need that requires new infrastructure? (gap)
  → Auto-fill where possible, flag decisions where needed
    ↓
Stage F4: Feature Decision Facilitator (sonnet, interactive)
  → Same as base Stage 4 but for feature-specific gaps only
    ↓
Stage F5: Feature Mechanism Analyst (opus)
  → Evaluate implementation approaches for new mechanisms
  → CRITICAL: Check compatibility with existing mechanism choices
  → Developer's Choice scoring with same 6 dimensions
  → Flag any new mechanisms that conflict with existing ones
    ↓
Stage F6: PRD Merger (opus)
  → Take the existing PRD + new feature analysis
  → Produce an UPDATED PRD (not a separate document)
  → New items get provenance tag [FEATURE-ADD-v2] (or v3, v4, etc.)
  → Caveat appendix is extended (not replaced)
  → Version number incremented
    ↓
Stage F7: Autoforge Bridge (sonnet, optional)
  → Generate new Autoforge features that integrate with existing feature set
  → Dependency graph extended (new features depend on existing ones)
```

## Key Design Decisions

### The PRD is a Living Document

The Feature Addition Engine doesn't create a second PRD. It **updates the original**. Version tracking keeps history:

```json
{
  "prd_version": "1.3.0",
  "version_history": [
    {"version": "1.0.0", "date": "2026-02-22", "type": "initial", "features_added": 12},
    {"version": "1.1.0", "date": "2026-03-01", "type": "feature_add", "features_added": 3},
    {"version": "1.2.0", "date": "2026-03-10", "type": "feature_add", "features_added": 7},
    {"version": "1.3.0", "date": "2026-03-15", "type": "feature_add", "features_added": 5}
  ]
}
```

### Batch Feature Addition

You mentioned you're a "features guy" — 10 at a time, not 1. The engine handles this natively. A feature rant with 10 ideas goes through the same pipeline as one with 1. The only difference is Stage F5 (Mechanism Analyst) checks for inter-feature conflicts within the batch:

```
New Feature A needs WebSocket support
New Feature B needs Server-Sent Events
→ Conflict detected: both solve real-time updates differently
→ Decision question generated: "Do you want WebSockets or SSE for real-time?"
→ One choice applies to both features
```

### Compatibility Checking

Stage F5 has an explicit compatibility check against the existing PRD:

```
Existing PRD: Authentication via Magic Links
New Feature: Team workspaces with role-based access

Compatibility check:
✅ Magic links work with multi-user (each user gets their own link)
⚠️ Role-based access requires a user model extension
   → New mechanism needed: role assignment during team invite
   → Depends on existing AUTH-001 (magic links)
   → No conflict, just extension
```

### The SaaS Subscription Angle

This is the killer feature for SaaS monetization:

```
FREE TIER:     1 PRD generation per month
PRO TIER:      Unlimited PRDs + 5 feature additions per month
TEAM TIER:     Unlimited everything + collaboration + codebase reality engine
ENTERPRISE:    API access + white-label + priority processing
```

The feature addition engine creates the recurring value. The initial PRD is a one-time sale. Features are forever. Every 2 months the user comes back with new ideas, runs them through the system, gets an updated PRD. The monthly subscription pays for itself.

---

# ENHANCEMENT 4: Codebase Reality Engine

## The Problem

Software drifts from its spec. Always. The developer chose a different auth method during implementation. The database schema evolved. A feature got cut, another got added. After the build, the original PRD is a historical document, not a current one.

Two users need this engine:

1. **PRD user, post-build:** "I made a PRD with your system, built the app, things changed. Now I want to add features but the PRD doesn't match reality anymore."

2. **No-PRD user:** "I have existing software. Never had a PRD. Now I want to start using your system for feature additions."

Both need the same thing: a **current-state specification** of what the software actually is right now. We call this the After-Build PRD (AB-PRD).

## Two Input Modes

### Mode A: With Code Access (Full Analysis)

The user provides access to their codebase. The engine performs deep analysis:

```
Codebase
    ↓
Stage R1: Code Scanner (opus)
  → Read project structure, key files, configs
  → Identify: framework, language, database, auth, API style
  → Map: routes, models, services, components
  → Extract: dependencies, environment vars, build config
    ↓
Stage R2: Architecture Extractor (opus)
  → From the code scan, determine:
    - System architecture pattern (monolith, microservices, serverless)
    - Data model and relationships
    - Authentication/authorization approach
    - API design and endpoints
    - Frontend component tree
    - Third-party integrations
    - Test coverage and strategy
    ↓
Stage R3: AB-PRD Generator (opus)
  → Compile findings into Agent OS 3-layer format
  → Same structure as a regular PRD but every item is tagged [DETECTED]
  → Completeness checklist run against findings to identify undocumented areas
    ↓
Stage R4: Drift Analyzer (if original PRD exists) (sonnet)
  → Compare original PRD to AB-PRD
  → For every mechanism: same, changed, added, or removed
  → Produce a drift report showing exactly what changed
    ↓
Output: After-Build PRD + Drift Report (if applicable)
```

### Mode B: Without Code Access (Descriptive Analysis)

The user describes their software but won't share code. Less precise but still valuable:

```
User Description (structured questionnaire)
    ↓
Stage D1: Description Transcriber (opus)
  → Same as Stage 1 but with guided questions:
    - What does the app do?
    - What tech stack? (framework, language, database)
    - How do users log in?
    - What are the main features?
    - What third-party services do you use?
    - How is it deployed?
    ↓
Stage D2: Inference Engine (opus)
  → From the description, infer what the user probably has:
    - "React + Node" → likely REST or GraphQL API
    - "Firebase auth" → likely social login + email
    - "Deployed on Vercel" → likely serverless functions
  → Each inference tagged with confidence score
  → Low-confidence inferences become questions for the user
    ↓
Stage D3: Descriptive AB-PRD Generator (opus)
  → Same output format but items tagged [DESCRIBED] or [INFERRED]
  → Completeness checklist has more gaps (expected — no code to scan)
  → Gaps tagged as [UNKNOWN] rather than auto-filled
    ↓
Output: Descriptive After-Build PRD (lower confidence, more unknowns)
```

## The Drift Report

When a user has both the original PRD and code access, the Drift Analyzer produces:

```markdown
## Drift Report: Original PRD v1.0.0 → Current Codebase

### Summary
- Mechanisms unchanged: 28/35 (80%)
- Mechanisms modified: 4/35 (11.4%)
- Mechanisms removed: 1/35 (2.9%)
- Mechanisms added (not in PRD): 2

### Modified Mechanisms

#### AUTH-001: User Authentication
- **PRD said:** Magic links via email
- **Code does:** Magic links via email + Google OAuth (added)
- **Drift type:** Extension (original preserved, new option added)
- **Impact on future features:** LOW — both auth methods work with user model

#### DATA-003: Primary Database
- **PRD said:** PostgreSQL with Prisma ORM
- **Code does:** PostgreSQL with Drizzle ORM
- **Drift type:** Substitution (same DB, different ORM)
- **Impact on future features:** MEDIUM — new features must use Drizzle patterns

### Removed Mechanisms

#### FEAT-012: Client Portal Comments
- **PRD said:** Annotation-based commenting on design mockups
- **Code does:** Not implemented (feature was cut)
- **Impact:** If future features reference this, they need adjustment

### Added Mechanisms (Not in Original PRD)

#### NEW-001: Rate Limiting
- **Code has:** Express rate-limit middleware on all API routes
- **Should add to PRD:** Yes — affects API design section

#### NEW-002: Dark Mode
- **Code has:** CSS custom properties with theme toggle
- **Should add to PRD:** Yes — affects design system section
```

## Connecting to Feature Addition

The flow for "I have software, I want to add features" is:

```
Existing Software
    ↓
Codebase Reality Engine → After-Build PRD (+ Drift Report if original PRD exists)
    ↓
Reconciled PRD (merges original + drift + AB-PRD findings)
    ↓
Feature Addition Engine → Updated PRD with new features
    ↓
Autoforge Bridge → Buildable feature specs
```

The Reconciled PRD is the "single source of truth" that reflects what the software ACTUALLY IS, not what it was supposed to be. New features are designed against reality, not the original plan.

## The SaaS Pitch

This is where the subscription really justifies itself:

**Without the Codebase Reality Engine:**
"I made a PRD, built the app, now the PRD is outdated, and adding features is guesswork."

**With it:**
"I built the app. The system scanned my code, found what changed, updated my PRD automatically. Now when I add features, they're designed against what my app actually is — not what it was supposed to be 6 months ago."

**For the no-PRD user:**
"I've been building for a year with no spec. The system scanned my codebase and reverse-engineered a complete PRD. Now I have documentation I never wrote, and I can add features through the same pipeline as everyone else."

That second user is a massive market. Most existing software has no PRD. Offering them a way to retroactively get one — and then immediately start adding features through a rigorous pipeline — that's the "I didn't know I needed this until I saw it" moment.

---

# ENHANCEMENT 5: Enhanced Pipeline — Full Architecture

## Complete Stage Map

Putting all four enhancements together with the base pipeline:

```
═══════════════════════════════════════════════════════════════
  RANT-TO-PRD: COMPLETE ENHANCED PIPELINE
═══════════════════════════════════════════════════════════════

PHASE A: NEW PRD (Base Pipeline + Verifiers + Developer's Choice)
─────────────────────────────────────────────────────────────────

  Rant Input
      ↓
  Stage 1:   Transcriber (opus)
  Stage 1.5: Transcription Verifier (sonnet)
      ↓
  Stage 2:   Classifier (sonnet)
  Stage 2.5: Classification Verifier (sonnet)
      ↓
  Stage 3:   Gap Analyst (opus)
      ↓
  Stage 4:   Decision Facilitator (sonnet, interactive)
      ↓
  Stage 5:   Mechanism Analyst (opus)
             → Multi-dimensional scoring (6 dimensions)
             → Developer's Choice recommendations
             → Close-call identification
  Stage 5.5: Mechanism Verifier (sonnet)
      ↓
  Stage 5.7: Developer's Choice Gate
             → Mode 1: Full Control (review all)
             → Mode 2: Dev Choice (auto-accept all)
             → Mode 3: Exceptions Only (auto + review close calls)
      ↓
  Stage 6:   PRD Compiler (opus)
             → Includes scoring report
             → Includes caveat appendix with alternatives
             → Includes worktree recommendations
  Stage 6.5: PRD Verifier (sonnet)
      ↓
  Stage 7:   Autoforge Bridge (sonnet, optional)
      ↓
  OUTPUT: Complete PRD v1.0.0

═════════════════════════════════════════════════════════════════

PHASE B: CODEBASE REALITY (When Adding Features to Existing Software)
─────────────────────────────────────────────────────────────────────

  Existing Codebase (or Description)
      ↓
  ┌─ With Code ─────────────────┐  ┌─ Without Code ──────────────┐
  │ Stage R1: Code Scanner      │  │ Stage D1: Description       │
  │ Stage R2: Architecture      │  │           Transcriber       │
  │           Extractor         │  │ Stage D2: Inference Engine  │
  │ Stage R3: AB-PRD Generator  │  │ Stage D3: Descriptive       │
  └─────────────────────────────┘  │           AB-PRD Generator  │
      ↓                            └──────────────────────────────┘
  Stage R4: Drift Analyzer              ↓
  (only if original PRD exists)         ↓
      ↓                                ↓
  Reconciled PRD ◄─────────────────────┘
  (current state of the software)

═════════════════════════════════════════════════════════════════

PHASE C: FEATURE ADDITION (Adding Features to Existing PRD)
────────────────────────────────────────────────────────────

  Feature Rant + Existing/Reconciled PRD
      ↓
  Stage F1: Feature Transcriber (opus)
            → Extract new features, deduplicate against existing PRD
  Stage F1.5: Feature Transcription Verifier (sonnet)
      ↓
  Stage F2: Impact Classifier (sonnet)
            → Map new features to existing PRD sections
            → Identify dependencies and conflicts
      ↓
  Stage F3: Feature Gap Analyst (opus)
            → Scoped completeness check for new features only
      ↓
  Stage F4: Feature Decision Facilitator (sonnet, interactive)
      ↓
  Stage F5: Feature Mechanism Analyst (opus)
            → Same scoring system, compatibility checked against existing
  Stage F5.5: Feature Mechanism Verifier (sonnet)
      ↓
  Stage F5.7: Developer's Choice Gate (same 3 modes)
      ↓
  Stage F6: PRD Merger (opus)
            → Updates existing PRD (not a new document)
            → Version incremented (v1.0.0 → v1.1.0)
  Stage F6.5: PRD Verifier (sonnet)
      ↓
  Stage F7: Autoforge Bridge (sonnet, optional)
      ↓
  OUTPUT: Updated PRD v1.x.0

═══════════════════════════════════════════════════════════════
```

## Pipeline Selection Logic

The system determines which phase to run based on what the user has:

```
User has...           | Run Phase A | Run Phase B | Run Phase C
──────────────────────|─────────────|─────────────|────────────
New idea, no software | ✅          | -           | -
PRD + code + features | -           | ✅          | ✅
Code only + features  | -           | ✅          | ✅
PRD only + features   | -           | -           | ✅
Description + features| -           | ✅ (Mode B) | ✅
```

## Manifest Integration

Each pipeline phase is a system in the Universal Dashboard. The manifest supports all three:

```yaml
# .swarm/manifest.yaml for the full Rant-to-PRD ecosystem
version: "1.0"
system:
  name: "Rant-to-PRD Ecosystem"
  id: "rant-to-prd-full"
  type: "sequential-pipeline"
  description: "Complete PRD lifecycle: create, maintain, extend"

# Multiple pipelines within one system
pipelines:
  new_prd:
    name: "New PRD"
    stages: [1, 1.5, 2, 2.5, 3, 4, 5, 5.5, 5.7, 6, 6.5, 7]
    description: "Create a PRD from a rant"

  codebase_reality:
    name: "Codebase Reality"
    stages: [R1, R2, R3, R4]
    description: "Reverse-engineer existing software into AB-PRD"

  feature_addition:
    name: "Add Features"
    stages: [F1, F1.5, F2, F3, F4, F5, F5.5, F5.7, F6, F6.5, F7]
    description: "Add features to an existing PRD"
    requires: ["new_prd OR codebase_reality"]

dashboard:
  layout: "pipeline-flow"
  primary_view: "pipeline-selector"
  ai_context: |
    You are assisting with the Rant-to-PRD ecosystem. Three pipelines:
    1. New PRD — create from scratch
    2. Codebase Reality — reverse-engineer existing software
    3. Feature Addition — extend an existing PRD
    Help the user choose the right pipeline and guide them through it.
```

---

# APPENDICES

## Appendix A: Updated File Inventory

New files added by this addendum:

```
.claude/agents/
  # Verifier agents
  rant-verify-transcription.md    # Stage 1.5
  rant-verify-classification.md   # Stage 2.5
  rant-verify-mechanisms.md       # Stage 5.5
  rant-verify-prd.md              # Stage 6.5

  # Feature addition agents
  rant-feature-transcriber.md     # Stage F1
  rant-feature-impact.md          # Stage F2
  rant-feature-gaps.md            # Stage F3
  rant-feature-decisions.md       # Stage F4
  rant-feature-mechanisms.md      # Stage F5
  rant-feature-merger.md          # Stage F6

  # Codebase reality agents
  rant-code-scanner.md            # Stage R1
  rant-arch-extractor.md          # Stage R2
  rant-abprd-generator.md         # Stage R3
  rant-drift-analyzer.md          # Stage R4
  rant-description-transcriber.md # Stage D1 (no-code mode)
  rant-inference-engine.md        # Stage D2 (no-code mode)
  rant-descriptive-abprd.md       # Stage D3 (no-code mode)

.claude/scripts/
  rant-pipeline.sh                # Updated with verifier + dev choice stages
  rant-feature-pipeline.sh        # Feature addition orchestrator
  rant-reality-pipeline.sh        # Codebase reality orchestrator
  rant-full-pipeline.sh           # Meta-orchestrator (selects which pipeline)
```

## Appendix B: Updated Token Estimates

| Pipeline | Stages | Est. Tokens (Medium Input) | Est. Cost |
|----------|--------|---------------------------|-----------|
| New PRD (base) | 7 | 400K-600K | $4-8 |
| + Verifiers | +4 | 50K-75K | +$0.90 |
| + Dev Choice scoring | +1 | 15K-25K | +$0.30 |
| **New PRD (enhanced)** | **12** | **465K-700K** | **$5-9** |
| Codebase Reality (with code) | 4 | 200K-400K | $3-6 |
| Codebase Reality (no code) | 3 | 100K-200K | $1.50-3 |
| Feature Addition | 11 | 300K-500K | $4-7 |
| **Full lifecycle (new + features)** | **23** | **765K-1.2M** | **$9-16** |

## Appendix C: SaaS Pricing Model Suggestion

```
FREE:       1 new PRD/month, no feature additions, no codebase reality
STARTER:    $29/mo — 3 PRDs + 10 feature additions + descriptive reality engine
PRO:        $79/mo — Unlimited PRDs + unlimited features + full code reality engine
TEAM:       $199/mo — Everything + collaboration + shared PRD library + API access
ENTERPRISE: Custom — White-label + priority + SLA + dedicated support
```

Value justification: A developer spending 3-5 days writing a PRD manually = $2,000-5,000 in opportunity cost. The Pro tier pays for itself in a single run.

## Appendix D: Implementation Priority

Build order (highest value first):

1. **Developer's Choice scoring** — Enhances Stage 5, biggest UX improvement, commercially differentiating
2. **Verification agents** — Quality guarantee, builds trust, prevents embarrassing outputs
3. **Feature Addition Engine** — The subscription driver, recurring revenue justification
4. **Codebase Reality Engine (with code)** — Opens the "existing software" market
5. **Codebase Reality Engine (no code)** — Expands addressable market to code-shy users
6. **Git worktree integration** — Power feature for serious users
7. **Drift analyzer** — Connects the whole lifecycle together

---

*End of addendum. These four enhancements transform the Rant-to-PRD pipeline from a one-shot PRD generator into a complete specification lifecycle platform: create PRDs, score and select mechanisms with Developer's Choice, reverse-engineer existing software, add features over time, and maintain a living document that evolves with the product.*
