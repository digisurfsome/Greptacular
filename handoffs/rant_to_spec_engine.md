# Handoff #1: Rant-to-Spec Engine (Core)

## Agent Instructions

You are building the core **Rant-to-Spec Engine** — a framework-agnostic Python module that takes raw, unstructured text (a "rant" — someone brain-dumping an app idea in stream-of-consciousness) and transforms it into a structured, decision-ready application specification.

This engine will be used in three different delivery modes (standalone app, AutoForge build integration, mobile/web admin), but **this handoff covers only the core engine**. Build it as a clean, importable Python package with no UI dependencies.

---

## Why This Exists

People don't think in structured specs. They think in bursts — mid-conversation, mid-build, mid-shower. The 12-24 hour window after an idea hits is when clarity is highest. This engine captures that raw output and transforms it into something buildable, without requiring the person to think like an engineer.

The key insight: **most technical decisions in an app have an obvious answer** (75%+ of developers would choose the same thing). The engine auto-resolves those and surfaces only the decisions that genuinely need human input — presented with full context so even a non-technical person can make an informed choice.

**The Developer's Choice principle:** Every single decision — Autopilot, Soft, AND Deep — comes with a pre-filled "Developer's Choice" recommendation, a confidence percentage, and a plain-English explanation of why. Users who want to go deep can read the full analysis and override. Users who trust the process can hit "Accept Developer's Choice for All" and the entire spec is done. The only prerequisite is that the user got their idea details out clearly enough for the engine to make informed recommendations. This collapses the spec creation process from days of research into minutes of review.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                 RANT-TO-SPEC ENGINE              │
│                                                  │
│  ┌───────────┐    ┌──────────────┐               │
│  │  1. PARSE │───>│ 2. CLASSIFY  │               │
│  │  Raw text │    │  Decision    │               │
│  │  → chunks │    │  buckets     │               │
│  └───────────┘    └──────┬───────┘               │
│                          │                       │
│              ┌───────────┼───────────┐           │
│              ▼           ▼           ▼           │
│        ┌──────────┐ ┌────────┐ ┌─────────┐      │
│        │AUTOPILOT │ │  SOFT  │ │  DEEP   │      │
│        │Auto-pick │ │Confirm │ │Template │      │
│        └──────────┘ └────────┘ └────┬────┘      │
│                                     │            │
│                          ┌──────────▼─────────┐  │
│                          │  3. RESEARCH       │  │
│                          │  Pros/cons/cost    │  │
│                          │  for each option   │  │
│                          └──────────┬─────────┘  │
│                                     │            │
│                          ┌──────────▼─────────┐  │
│                          │  4. WEIGHT         │  │
│                          │  Apply user        │  │
│                          │  priority profile  │  │
│                          └──────────┬─────────┘  │
│                                     │            │
│              ┌──────────────────────▼──────────┐ │
│              │  5. ASSEMBLE                    │ │
│              │  Merge all resolved decisions   │ │
│              │  → structured spec output       │ │
│              └────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## File Structure

```
rant_engine/
├── __init__.py              # Public API: RantEngine class
├── models.py                # All Pydantic data models
├── parser.py                # Stage 1: Raw text → structured chunks
├── classifier.py            # Stage 2: Chunks → Autopilot/Soft/Deep buckets
├── researcher.py            # Stage 3: Deep decisions → full analysis
├── weighter.py              # Stage 4: Apply priority profiles to recommendations
├── assembler.py             # Stage 5: Resolved decisions → spec output
├── templates.py             # Decision template definitions and rendering
├── prompts/                 # AI prompt templates for each stage
│   ├── parse_rant.md        # Extraction prompt
│   ├── classify_decision.md # Classification prompt
│   ├── research_deep.md     # Deep research prompt
│   └── assemble_spec.md     # Final assembly prompt
├── profiles.py              # Built-in priority profiles (cost-sensitive, speed, etc.)
└── serialization.py         # Save/load engine state (JSON) for resume capability
```

---

## Data Models (models.py)

Use Pydantic v2 for all models. Everything must be JSON-serializable for save/resume.

### Core Models

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


class DecisionBucket(str, Enum):
    """How much human input this decision needs."""
    AUTOPILOT = "autopilot"    # 75%+ obvious choice, auto-resolved
    SOFT = "soft"              # Clear winner but worth confirming
    DEEP = "deep"              # Real tradeoffs, needs full template


class DecisionCategory(str, Enum):
    """What domain this decision falls into."""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    HOSTING = "hosting"
    FRONTEND_FRAMEWORK = "frontend_framework"
    STYLING = "styling"
    STATE_MANAGEMENT = "state_management"
    API_DESIGN = "api_design"
    FILE_STORAGE = "file_storage"
    PAYMENTS = "payments"
    EMAIL = "email"
    SEARCH = "search"
    CACHING = "caching"
    REAL_TIME = "real_time"
    MONITORING = "monitoring"
    CI_CD = "ci_cd"
    THIRD_PARTY_API = "third_party_api"
    BUSINESS_LOGIC = "business_logic"
    DATA_MODEL = "data_model"
    UX_PATTERN = "ux_pattern"
    MONETIZATION = "monetization"
    OTHER = "other"


class Feature(BaseModel):
    """A distinct feature extracted from the rant."""
    id: str = Field(description="Unique identifier (auto-generated)")
    name: str = Field(description="Short feature name")
    description: str = Field(description="Technical description")
    user_story: str = Field(description="Plain English: what the user can do")
    complexity: int = Field(ge=1, le=5, description="1=trivial, 5=very complex")
    dependencies: list[str] = Field(default_factory=list, description="IDs of features this depends on")
    source_excerpt: str = Field(description="The part of the rant this came from")


class DecisionOption(BaseModel):
    """One possible choice for a decision."""
    name: str
    description: str
    pros: list[str]
    cons: list[str]
    cost_estimate: str = Field(description="Free / $X/mo / one-time $X / usage-based")
    industry_usage_pct: int = Field(ge=0, le=100, description="Estimated % of projects using this")
    time_to_implement: str = Field(description="Relative: hours / days / weeks")

    # Builder-layer dimensions (engine auto-populates relevant ones)
    vendor_lock_in: Optional[str] = Field(None, description="Risk level and switching cost")
    maintenance_burden: Optional[str] = Field(None, description="Ongoing maintenance requirements")
    scaling_ceiling: Optional[str] = Field(None, description="At what scale does this break?")
    data_portability: Optional[str] = Field(None, description="Can you export and leave?")
    integration_ecosystem: Optional[str] = Field(None, description="Compatibility with common tools")
    team_learning_curve: Optional[str] = Field(None, description="How hard for new devs to pick up?")
    security_implications: Optional[str] = Field(None, description="Security tradeoffs and risks")
    regulatory_compliance: Optional[str] = Field(None, description="GDPR/HIPAA/SOC2 implications")
    fallback_complexity: Optional[str] = Field(None, description="Recovery difficulty if this fails in prod")
    community_support: Optional[str] = Field(None, description="Docs, forums, active development")
    monetization_compatibility: Optional[str] = Field(None, description="Works with SaaS/freemium/one-time?")


class Decision(BaseModel):
    """A technical decision that needs to be made."""
    id: str
    title: str = Field(description="What's being decided, e.g. 'Authentication Strategy'")
    context: str = Field(description="Why this decision matters for this specific app")
    category: DecisionCategory
    bucket: DecisionBucket

    options: list[DecisionOption] = Field(default_factory=list)
    recommendation: Optional[str] = Field(None, description="Which option the engine recommends")
    recommendation_reasoning: Optional[str] = Field(None, description="Why this is recommended")
    confidence: int = Field(ge=0, le=100, description="How confident the engine is in its recommendation")

    # Developer's Choice — the pre-filled expert recommendation
    developers_choice: Optional[str] = Field(None, description="The option a senior developer would pick")
    developers_choice_confidence: int = Field(default=0, ge=0, le=100, description="Confidence % in dev choice")
    developers_choice_summary: Optional[str] = Field(None, description="1-2 sentence plain English: why this is the dev choice")
    developers_choice_deep_explanation: Optional[str] = Field(None, description="Full explanation: the reasoning, tradeoffs considered, why not the alternatives. Educational — teaches the user to think like a developer.")
    developers_choice_caveats: list[str] = Field(default_factory=list, description="When the dev choice might be WRONG for your specific case")

    # Which builder-layer dimensions are relevant for this decision type
    relevant_dimensions: list[str] = Field(default_factory=list)

    # User resolution
    resolved: bool = False
    chosen_option: Optional[str] = None
    user_notes: Optional[str] = None
    used_developers_choice: bool = Field(default=False, description="True if user accepted dev choice without modification")

    # Source tracking
    source_excerpt: str = Field(description="The part of the rant that triggered this decision")


class PriorityProfile(BaseModel):
    """User's weighted priorities for decision-making."""
    name: str = "default"

    # Weights from 0-10 (0 = don't care, 10 = critical)
    cost_sensitivity: int = Field(default=5, ge=0, le=10)
    speed_to_market: int = Field(default=5, ge=0, le=10)
    scalability: int = Field(default=5, ge=0, le=10)
    simplicity: int = Field(default=7, ge=0, le=10)
    security: int = Field(default=5, ge=0, le=10)
    vendor_independence: int = Field(default=3, ge=0, le=10)
    team_hire_ability: int = Field(default=3, ge=0, le=10)
    long_term_maintenance: int = Field(default=5, ge=0, le=10)
    compliance_requirements: int = Field(default=2, ge=0, le=10)

    # Auto-resolve threshold: decisions with confidence >= this get autopiloted
    auto_resolve_threshold: int = Field(default=75, ge=50, le=100)


class RantSession(BaseModel):
    """Complete state of a rant-to-spec session. Serializable for save/resume."""
    id: str
    created_at: datetime
    updated_at: datetime

    # Input
    raw_rant: str

    # Pipeline outputs
    features: list[Feature] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)

    # Configuration
    priority_profile: PriorityProfile = Field(default_factory=PriorityProfile)

    # Pipeline progress
    stage: str = Field(default="raw", description="raw|parsed|classified|researched|weighted|assembled")

    # Output
    spec_output: Optional[str] = Field(None, description="Final assembled spec (XML format)")

    # Stats
    autopilot_count: int = 0
    soft_count: int = 0
    deep_count: int = 0
    resolved_count: int = 0
```

---

## Stage 1: Parser (parser.py)

**Input:** Raw rant text (could be messy, stream-of-consciousness, voice-transcribed)

**Output:** List of `Feature` objects + list of `Decision` objects (unclassified)

**How it works:**
1. Send the raw rant to Claude with the `parse_rant.md` prompt
2. The prompt instructs Claude to:
   - Extract every distinct feature or capability mentioned
   - Identify every point where a technical decision is implied (even if the user didn't explicitly state it as a choice)
   - Infer features the user probably needs but didn't mention (e.g., if they mention "users can log in" → auth, user management, password reset are implied)
   - Preserve the original rant excerpt for each extracted item (for traceability)
3. Parse Claude's structured JSON response into Feature and Decision model instances

**Key AI prompt guidance for parse_rant.md:**
- Treat the input as potentially messy, repetitive, contradictory
- De-duplicate ideas that are stated multiple ways
- Infer the implicit technical stack from context clues
- Flag contradictions (e.g., "it should be free to host" + "needs real-time for 100k users")
- Extract the emotional intent — what does the user REALLY care about vs. throwaway comments

**The parser should also detect:**
- App type (SaaS, marketplace, tool, social, e-commerce, etc.)
- Target audience signals
- Revenue model hints
- Scale expectations
- Existing tech preferences mentioned

---

## Stage 2: Classifier (classifier.py)

**Input:** List of unclassified `Decision` objects + detected app context

**Output:** Each Decision gets its `bucket` set (Autopilot/Soft/Deep) + `relevant_dimensions` populated

**Classification logic:**

### Autopilot Rules (auto-resolve, 75%+ standard)
- Icon library for a React app → Lucide React (90%+ modern projects)
- CSS approach for a new app in 2026 → Tailwind CSS
- Package manager → npm (unless user mentioned pnpm/yarn)
- Linting → ESLint + Prettier
- Version control → Git
- API format for simple CRUD → REST (unless real-time heavy → GraphQL consideration)
- Date library → date-fns (unless heavy timezone → Luxon)
- Form library in React → React Hook Form
- ORM for Node → Prisma (unless edge deployment → Drizzle consideration)

### Soft Decision Rules (clear winner, quick confirm)
- Database for typical SaaS → PostgreSQL (recommend) vs MySQL vs SQLite
- Auth for standard app → NextAuth/Auth.js (recommend) vs Clerk vs custom
- Hosting for standard app → Vercel (recommend) vs Railway vs AWS
- State management → Zustand (recommend) vs Redux vs Jotai

### Deep Decision Rules (real tradeoffs, full template)
- Payment processing (Stripe vs Paddle vs LemonSqueezy vs custom) — cost/feature/compliance tradeoffs
- Real-time strategy (WebSocket vs SSE vs polling vs Liveblocks) — architecture implications
- Authentication for complex roles (custom RBAC vs Clerk vs Auth0 vs WorkOS)
- Database for high-scale (PostgreSQL vs CockroachDB vs PlanetScale vs Supabase)
- Mobile strategy (React Native vs Flutter vs Expo vs PWA vs native)
- Search implementation (PostgreSQL FTS vs Algolia vs Meilisearch vs Typesense vs ElasticSearch)
- File storage (S3 vs Cloudflare R2 vs Supabase Storage vs uploadthing)
- AI integration (OpenAI vs Anthropic vs self-hosted vs multiple)
- Monetization model (SaaS subscription vs usage-based vs freemium vs one-time)
- Multi-tenancy approach (shared DB vs schema-per-tenant vs DB-per-tenant)

### Dimension Relevance Mapping

The engine auto-selects which builder-layer dimensions matter for each decision category:

```python
DIMENSION_MAP = {
    DecisionCategory.DATABASE: [
        "vendor_lock_in", "scaling_ceiling", "data_portability",
        "maintenance_burden", "team_learning_curve", "community_support"
    ],
    DecisionCategory.AUTHENTICATION: [
        "security_implications", "vendor_lock_in", "regulatory_compliance",
        "scaling_ceiling", "integration_ecosystem", "team_learning_curve"
    ],
    DecisionCategory.HOSTING: [
        "vendor_lock_in", "scaling_ceiling", "cost_estimate",
        "maintenance_burden", "regulatory_compliance", "fallback_complexity"
    ],
    DecisionCategory.PAYMENTS: [
        "vendor_lock_in", "regulatory_compliance", "monetization_compatibility",
        "integration_ecosystem", "security_implications", "data_portability"
    ],
    # ... define for all categories
}
```

---

## Stage 3: Researcher (researcher.py)

**Input:** Decisions classified as `DEEP` (and optionally `SOFT` if user wants detail)

**Output:** Each Deep decision gets fully populated `options` with all relevant dimensions filled in

**How it works:**
1. For each Deep decision, send to Claude with the `research_deep.md` prompt
2. The prompt instructs Claude to:
   - Identify 2-5 realistic options (not 10 obscure ones)
   - For each option, research and fill in ALL relevant dimensions
   - Provide specific, current pricing (not "varies")
   - Give real industry usage percentages (not made up)
   - Include specific failure scenarios ("this breaks when...")
   - Rate confidence level in the recommendation
3. Parse response into `DecisionOption` objects

**Critical: the research prompt must emphasize:**
- Be specific, not generic. "PostgreSQL handles 10k concurrent connections" not "good for large scale"
- Include year-relevant pricing (2026 prices, not 2023)
- Mention real companies using each option at the user's target scale
- State the switching cost explicitly: "Migrating from X to Y typically takes N weeks for a team of N"
- Note breaking changes or sunset risks: "Google killed Firebase Realtime Database pricing tier in 2025"

**This stage benefits enormously from million-token context** — holding the full rant, all extracted features, the classification context, AND deep research for multiple options simultaneously produces far more coherent cross-cutting analysis than fragmented small-context calls.

---

## Stage 4: Weighter (weighter.py)

**Input:** Researched decisions + user's `PriorityProfile`

**Output:** Reranked options within each decision, updated recommendations

**How it works:**
1. For each decision, score each option against the priority profile
2. Scoring formula (per option):

```python
def score_option(option: DecisionOption, profile: PriorityProfile, decision: Decision) -> float:
    score = 0.0
    weights = {
        "cost_sensitivity": _score_cost(option.cost_estimate, profile.cost_sensitivity),
        "speed_to_market": _score_speed(option.time_to_implement, profile.speed_to_market),
        "scalability": _score_scaling(option.scaling_ceiling, profile.scalability),
        "simplicity": _score_simplicity(option.team_learning_curve, profile.simplicity),
        "security": _score_security(option.security_implications, profile.security),
        "vendor_independence": _score_lock_in(option.vendor_lock_in, profile.vendor_independence),
        "team_hire_ability": _score_hiring(option.team_learning_curve, profile.team_hire_ability),
        "long_term_maintenance": _score_maintenance(option.maintenance_burden, profile.long_term_maintenance),
        "compliance_requirements": _score_compliance(option.regulatory_compliance, profile.compliance_requirements),
    }
    # Weight by relevance — only dimensions relevant to this decision type count
    for dim, dim_score in weights.items():
        if dim in decision.relevant_dimensions or dim in ["cost_sensitivity", "speed_to_market", "simplicity"]:
            score += dim_score
    return score / len(weights)
```

3. Rerank options by score
4. If top option scores above `auto_resolve_threshold`, bump decision from SOFT → AUTOPILOT
5. Update recommendation and reasoning based on weighted scores

---

## Stage 5: Assembler (assembler.py)

**Input:** All features + all resolved decisions (autopilot auto-resolved, soft confirmed, deep answered)

**Output:** Structured spec in AutoForge-compatible XML format

**How it works:**
1. Gather all resolved decisions
2. Send to Claude with `assemble_spec.md` prompt along with all features
3. The prompt instructs Claude to:
   - Organize features by priority and dependency
   - Embed resolved technical decisions into the appropriate spec sections
   - Generate the `<app_spec>` XML structure that AutoForge expects
   - Include technology stack, data model, API design, UI components
   - Reference specific decisions made ("PostgreSQL was chosen because...")
4. Also output a human-readable summary document

**Output formats:**
- `app_spec.txt` — AutoForge-compatible XML spec
- `decisions_log.json` — Full audit trail of all decisions made and why
- `summary.md` — Human-readable overview with decision highlights

---

## Built-in Priority Profiles (profiles.py)

```python
PROFILES = {
    "bootstrapper": PriorityProfile(
        name="bootstrapper",
        cost_sensitivity=9,
        speed_to_market=8,
        scalability=3,
        simplicity=9,
        security=4,
        vendor_independence=2,
        team_hire_ability=2,
        long_term_maintenance=4,
        compliance_requirements=1,
    ),
    "funded_startup": PriorityProfile(
        name="funded_startup",
        cost_sensitivity=4,
        speed_to_market=9,
        scalability=7,
        simplicity=6,
        security=6,
        vendor_independence=3,
        team_hire_ability=7,
        long_term_maintenance=5,
        compliance_requirements=3,
    ),
    "enterprise": PriorityProfile(
        name="enterprise",
        cost_sensitivity=3,
        speed_to_market=4,
        scalability=9,
        simplicity=4,
        security=9,
        vendor_independence=7,
        team_hire_ability=8,
        long_term_maintenance=8,
        compliance_requirements=9,
    ),
    "solo_saas": PriorityProfile(
        name="solo_saas",
        cost_sensitivity=7,
        speed_to_market=7,
        scalability=5,
        simplicity=8,
        security=6,
        vendor_independence=5,
        team_hire_ability=3,
        long_term_maintenance=7,
        compliance_requirements=4,
    ),
    "prototype": PriorityProfile(
        name="prototype",
        cost_sensitivity=8,
        speed_to_market=10,
        scalability=1,
        simplicity=10,
        security=2,
        vendor_independence=1,
        team_hire_ability=1,
        long_term_maintenance=1,
        compliance_requirements=1,
    ),
}
```

---

## Serialization & Resume (serialization.py)

The entire `RantSession` must be saveable/loadable at any point:

```python
def save_session(session: RantSession, path: Path) -> None:
    """Save session state to JSON file."""
    path.write_text(session.model_dump_json(indent=2))

def load_session(path: Path) -> RantSession:
    """Load session from JSON file."""
    return RantSession.model_validate_json(path.read_text())
```

This enables:
- User rants 50%, saves, comes back 2 days later to finish
- Engine processes through Stage 2, user reviews classifications, adjusts, re-runs Stage 3
- Partial resolution: answer 3 of 8 deep decisions today, do the rest tomorrow
- Multiple rant sessions feeding into the same spec (additive)

---

## Public API (\_\_init\_\_.py)

```python
class RantEngine:
    """Main entry point for the Rant-to-Spec pipeline."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        """Initialize with Anthropic API key and model selection."""

    async def start_session(self, raw_rant: str, profile: PriorityProfile | str = "default") -> RantSession:
        """Create a new session from raw rant text. Returns parsed session."""

    async def resume_session(self, session_path: Path) -> RantSession:
        """Load and resume a saved session."""

    async def parse(self, session: RantSession) -> RantSession:
        """Stage 1: Extract features and decisions from rant."""

    async def classify(self, session: RantSession) -> RantSession:
        """Stage 2: Classify decisions into Autopilot/Soft/Deep buckets."""

    async def research(self, session: RantSession, decisions: list[str] | None = None) -> RantSession:
        """Stage 3: Deep research on specified decisions (or all Deep ones)."""

    async def weight(self, session: RantSession) -> RantSession:
        """Stage 4: Apply priority profile to rerank options."""

    async def assemble(self, session: RantSession) -> RantSession:
        """Stage 5: Generate final spec from resolved decisions."""

    async def run_full_pipeline(self, raw_rant: str, profile: PriorityProfile | str = "default") -> RantSession:
        """Run all stages end-to-end. Returns session with spec_output populated."""

    def resolve_decision(self, session: RantSession, decision_id: str, chosen_option: str, notes: str = "") -> RantSession:
        """User resolves a decision manually."""

    def accept_developers_choice(self, session: RantSession, decision_id: str) -> RantSession:
        """Accept the Developer's Choice for a single decision."""

    def accept_all_developers_choices(self, session: RantSession) -> RantSession:
        """Accept Developer's Choice for ALL unresolved decisions. The 'just build it' button."""

    def get_pending_decisions(self, session: RantSession) -> list[Decision]:
        """Get all unresolved Deep decisions (the ones the user needs to answer)."""

    def get_developers_choice_summary(self, session: RantSession) -> dict:
        """Get a summary of all Developer's Choice recommendations with confidence levels.
        Returns dict with 'high_confidence' (>85%), 'medium' (60-85%), 'review_recommended' (<60%) lists.
        Users can quickly scan which ones are safe to auto-accept vs which deserve a closer look."""

    def save(self, session: RantSession, path: Path) -> None:
        """Save session to disk."""
```

---

## AI Model Usage

- **Parser (Stage 1):** Sonnet — fast, good at extraction, cost-effective for initial pass
- **Classifier (Stage 2):** Sonnet — pattern matching against known categories
- **Researcher (Stage 3):** Opus with extended context — this is where depth matters, thorough analysis of options, cross-referencing against the full app context. **This is the million-token stage.** The entire rant, all features, all classification context, and deep research for each option should be in scope simultaneously
- **Weighter (Stage 4):** Local computation (no AI needed — pure math scoring)
- **Assembler (Stage 5):** Opus — needs to synthesize everything into a coherent spec

---

## Implementation Notes

- Use `anthropic` Python SDK (async client) for all AI calls
- All stages should be independently callable (user might re-run just classification after tweaking profiles)
- Error handling: if any stage fails, session state is preserved at the last successful stage
- Logging: use Python `logging` module, structured JSON logs for pipeline events
- Testing: write unit tests for the weighter (pure logic), integration tests for the full pipeline with mock AI responses

---

## What This Does NOT Include

- Any UI (that's the three connection modes in Handoff #2)
- Voice-to-text (input is assumed to be text — voice integration is a connection concern)
- User accounts or persistence beyond JSON files
- Real-time collaboration
- Payment or billing

This is purely the transformation engine: text in → structured spec out.
