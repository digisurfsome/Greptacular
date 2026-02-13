# Build Intelligence - Handoff Document

## Status: Ready to Implement

## Overview

AutoForge builds hundreds of projects but throws away all the learning. Which features fail most often? Which architecture patterns work best? Which prompts produce the cleanest code? This data is gold and nobody is collecting it.

This handoff describes three interlocking systems that create a feedback loop where AutoForge gets measurably smarter with every project built:

1. **Build History Intelligence** -- Collects metrics across all builds and uses them to improve future builds via prompt injection, time estimation, and risk flagging.
2. **PRD Quality Scoring** -- Scores the user's app_spec.txt before building, with actionable feedback that directly predicts build quality. Doubles as a consulting upsell.
3. **Continuous Improvement Pipeline** -- Closes the loop between build outcomes and future build quality through automated prompt tuning, A/B testing, and pattern library generation.

The core thesis: the #1 predictor of build quality is spec quality, and the #2 predictor is whether the agent was warned about known pitfalls in advance. Both are addressable with data.

---

## Feature 1: Build History Intelligence

### The Problem

Every AutoForge build generates valuable data about what works and what does not. A CRUD feature using Supabase with RLS might pass on the first try 95% of the time. Payment integration might have a 40% rework rate. Authentication features might fail 30% of the time due to session token handling. But AutoForge does not track any of this. Every build starts from zero, repeating the same mistakes that hundreds of previous builds already encountered and solved.

### What It Does

Tracks metrics across ALL builds (anonymized) and uses them to improve future builds through four mechanisms: prompt enhancement, time estimation, risk flagging, and architecture recommendations.

### Data Model

Two new tables. For SaaS deployment these live in Supabase (central aggregation). For local/self-hosted installs they live in the project's `features.db` SQLite database (per-project only).

#### Table: `build_metrics`

Stored per-project, collected at build completion. One row per build session (an orchestrator run from start to all-features-complete).

```sql
create table build_metrics (
  id text primary key,                        -- UUID as text for SQLite compat
  project_id text,                            -- Anonymized project identifier (hash)
  created_at text default (datetime('now')),  -- ISO 8601 timestamp

  -- Spec metrics (captured at build start)
  spec_word_count integer,
  spec_feature_count integer,
  spec_complexity_score integer,              -- 1-5, computed by PRD scorer
  boilerplate_used text,                      -- Boilerplate option_id or null
  style_used text,                            -- Style ID or null

  -- Build metrics (captured at build end)
  total_coding_sessions integer,
  total_testing_sessions integer,
  total_review_sessions integer,              -- 0 until QA pipeline ships
  total_turns_used integer,                   -- Sum across all agent sessions
  build_duration_seconds integer,             -- Wall clock time

  -- Quality metrics (derived from feature status history)
  features_passed_first_try integer,
  features_needed_rework integer,
  review_issues_found integer,                -- From code review agent
  review_issues_by_severity text,             -- JSON: {"critical": 2, "high": 5, "medium": 10}
  qa_issues_found integer,                    -- From final QA agent
  regression_count integer,                   -- Features that regressed after passing

  -- Final scores (from QA pipeline, if enabled)
  qa_score text,                              -- A/B/C/D/F
  performance_score text,
  security_score text,

  -- Tech stack (detected from project files)
  tech_stack text,                            -- JSON: {"frontend": "react", "backend": "supabase"}

  -- Failure patterns (anonymized, no code snippets)
  common_failures text                        -- JSON: [{"category": "auth", "description": "...", "frequency": 3}]
);
```

#### Table: `feature_patterns`

Aggregated across builds. Updated incrementally after each build completes. For local installs this starts empty and grows with each project. For SaaS this is pre-seeded from the central database.

```sql
create table feature_patterns (
  id text primary key,                        -- UUID as text
  category text not null,                     -- "authentication", "crud", "payments", etc.
  pattern_name text not null,                 -- "email-password-auth", "oauth-social-login"
  success_rate real,                          -- Percentage (0.00-100.00)
  avg_turns_to_implement integer,
  avg_rework_cycles integer,
  common_pitfalls text,                       -- JSON array of strings
  recommended_approach text,                  -- Markdown text, injected into prompts
  sample_count integer not null default 0,    -- Number of builds contributing to this pattern
  updated_at text default (datetime('now')),

  unique(category, pattern_name)
);
```

### How It Improves Future Builds

#### 1.1 Prompt Enhancement (Highest Impact)

Before a coding agent starts a feature, the system queries `feature_patterns` for the feature's category and injects relevant intelligence into the prompt. This follows the existing pattern in `prompts.py` where `_get_style_context()` and `_get_boilerplate_context()` inject context.

New function: `_get_intelligence_context(project_dir, feature_category)`

Example injections:

- "Features in the 'authentication' category fail 30% of the time due to session token handling. Pay special attention to token refresh logic and ensure refresh tokens are stored securely."
- "CRUD features using Supabase have a 95% first-try success rate when you implement Row Level Security policies before writing any API routes."
- "Payment integration has a 40% rework rate. The most common pitfall is not handling webhook idempotency. Always check for duplicate event IDs before processing."

The injection is concise (3-5 sentences max per category) to avoid bloating the prompt. It targets the specific failure modes that historical data shows are most common.

#### 1.2 Time Estimation

Based on historical data, estimate build time per feature category. Shown in the UI during project creation and on the kanban board.

Formula:
```
estimated_hours = sum(
  feature_patterns[category].avg_turns_to_implement * TURN_DURATION_MINUTES
  for each feature
) / 60
```

Where `TURN_DURATION_MINUTES` is calibrated from `build_metrics.build_duration_seconds / build_metrics.total_turns_used` across recent builds.

Display in UI: "Estimated build time: 4.5 hours based on 847 similar projects."

When insufficient local data exists (new install), fall back to hardcoded estimates based on step count (the existing `_estimate_feature_turns()` logic in `parallel_orchestrator.py`).

#### 1.3 Risk Flagging

Before building, scan the feature list and flag high-risk features based on `feature_patterns.success_rate`:

- **High risk** (success_rate < 70%): Red badge, shown prominently
- **Medium risk** (success_rate 70-85%): Yellow badge
- **Low risk** (success_rate > 85%): Green badge or no badge

Flagged features get extra context in their prompt and are recommended for early implementation (so rework does not cascade).

#### 1.4 Architecture Recommendations

When `feature_patterns` has sufficient data (sample_count >= 50), surface architecture-level recommendations:

- "For React + Supabase projects with 100+ features, projects using Zustand for state management had 20% fewer regressions than those using Context API."
- "Projects that implement authentication before any other feature have 15% fewer blocked features."

These are computed from aggregated `build_metrics.tech_stack` and `build_metrics.regression_count` correlations. Shown as tips in the project creation wizard and on the dashboard.

### Implementation

#### 1.5 New Service: `server/services/build_intelligence.py`

Core service with these responsibilities:

```python
class BuildIntelligence:
    """Collects, stores, and queries build metrics for intelligence injection."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        # Uses the same features.db via create_database()

    def collect_build_start_metrics(self, spec_content: str, feature_count: int) -> str:
        """Record metrics at build start. Returns build_id for later completion."""
        # Parse spec for word count, complexity score
        # Record boilerplate, style from project_config.json
        # Insert partial build_metrics row

    def collect_build_end_metrics(self, build_id: str, feature_dicts: list[dict]) -> None:
        """Record metrics at build completion."""
        # Calculate: total sessions, turns, duration
        # Derive: first-try pass rate, rework count, regression count
        # Update the build_metrics row
        # Update feature_patterns aggregates

    def get_intelligence_context(self, feature_category: str) -> str:
        """Get prompt injection text for a feature category."""
        # Query feature_patterns for the category
        # Format as concise markdown section
        # Return empty string if insufficient data

    def get_build_estimate(self, feature_dicts: list[dict]) -> dict:
        """Estimate build time based on historical data."""
        # Sum estimated turns per category from feature_patterns
        # Convert to hours using calibrated turn duration
        # Return {estimated_hours, confidence, sample_count}

    def get_risk_assessment(self, feature_dicts: list[dict]) -> list[dict]:
        """Flag high-risk features based on historical success rates."""
        # Query feature_patterns for each feature's category
        # Return [{feature_id, risk_level, reason}]

    def update_feature_patterns(self, feature_dicts: list[dict]) -> None:
        """Update aggregated patterns from completed build data."""
        # Group features by category
        # Update success_rate, avg_turns, avg_rework incrementally
        # Extract common pitfalls from failure descriptions
```

#### 1.6 SQLAlchemy Models in `api/database.py`

Add two new models following the existing pattern (Feature, Schedule, ScheduleOverride):

```python
class BuildMetric(Base):
    """Build-level metrics for intelligence tracking."""
    __tablename__ = "build_metrics"

    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(String(64))  # Anonymized hash
    created_at = Column(DateTime, nullable=False, default=_utc_now)

    # Spec metrics
    spec_word_count = Column(Integer)
    spec_feature_count = Column(Integer)
    spec_complexity_score = Column(Integer)
    boilerplate_used = Column(String(50))
    style_used = Column(String(50))

    # Build metrics
    total_coding_sessions = Column(Integer)
    total_testing_sessions = Column(Integer)
    total_review_sessions = Column(Integer, default=0)
    total_turns_used = Column(Integer)
    build_duration_seconds = Column(Integer)

    # Quality metrics
    features_passed_first_try = Column(Integer)
    features_needed_rework = Column(Integer)
    review_issues_found = Column(Integer, default=0)
    review_issues_by_severity = Column(JSON)
    qa_issues_found = Column(Integer, default=0)
    regression_count = Column(Integer, default=0)

    # Final scores
    qa_score = Column(String(1))
    performance_score = Column(String(1))
    security_score = Column(String(1))

    # Tech stack and failure patterns
    tech_stack = Column(JSON)
    common_failures = Column(JSON)


class FeaturePattern(Base):
    """Aggregated feature patterns for intelligence injection."""
    __tablename__ = "feature_patterns"

    id = Column(String(36), primary_key=True)
    category = Column(String(100), nullable=False)
    pattern_name = Column(String(255), nullable=False)
    success_rate = Column(Integer)  # Stored as percentage * 100 for SQLite
    avg_turns_to_implement = Column(Integer)
    avg_rework_cycles = Column(Integer)
    common_pitfalls = Column(JSON)
    recommended_approach = Column(Text)
    sample_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=_utc_now)
```

Add a migration function following the existing pattern (`_migrate_add_dependencies_column`, `_migrate_add_schedules_tables`):

```python
def _migrate_add_intelligence_tables(engine) -> None:
    """Create build_metrics and feature_patterns tables if they don't exist."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "build_metrics" not in existing_tables:
        BuildMetric.__table__.create(bind=engine)

    if "feature_patterns" not in existing_tables:
        FeaturePattern.__table__.create(bind=engine)
```

Call this in `create_database()` after the existing migration calls.

#### 1.7 Prompt Injection in `prompts.py`

New function following the `_get_style_context()` / `_get_boilerplate_context()` pattern:

```python
def _get_intelligence_context(project_dir: Path | None, feature_category: str | None = None) -> str:
    """Generate intelligence context for injection into coding prompts.

    Queries historical build data to provide category-specific guidance
    that helps agents avoid known pitfalls.

    Args:
        project_dir: The project directory (for database access).
        feature_category: Optional category to get specific intelligence for.

    Returns:
        A markdown string with intelligence context, or empty string if
        insufficient data is available.
    """
    if not project_dir:
        return ""

    try:
        from server.services.build_intelligence import BuildIntelligence
        intel = BuildIntelligence(project_dir)
        return intel.get_intelligence_context(feature_category or "")
    except (ImportError, Exception):
        return ""
```

Inject into `get_coding_prompt()` and `get_single_feature_prompt()` alongside the existing style and boilerplate context.

For `get_single_feature_prompt()`, the feature category can be extracted from the feature data and passed to the intelligence context generator. This requires a small change: look up the feature's category from the database before building the prompt.

#### 1.8 Orchestrator Integration

In `parallel_orchestrator.py`, the `_on_agent_complete()` callback is the natural collection point. Currently it handles cleanup (clearing `in_progress`, tracking failures). Add metrics collection:

```python
def _on_agent_complete(self, feature_id, return_code, agent_type, proc):
    # ... existing cleanup logic ...

    # Collect metrics for intelligence (non-blocking, best-effort)
    if agent_type == "coding":
        try:
            from server.services.build_intelligence import BuildIntelligence
            intel = BuildIntelligence(self.project_dir)
            intel.record_agent_session(
                feature_id=feature_id,
                agent_type=agent_type,
                success=(return_code == 0),
                # Duration could be tracked via start time stored when agent was spawned
            )
        except Exception:
            pass  # Intelligence collection must never break the orchestrator
```

At the end of `run_loop()`, when all features are complete, collect the final build metrics:

```python
# After "All features complete!" print
try:
    from server.services.build_intelligence import BuildIntelligence
    intel = BuildIntelligence(self.project_dir)
    intel.collect_build_end_metrics(self._build_id, feature_dicts)
except Exception:
    pass  # Best-effort collection
```

#### 1.9 API Endpoints

New router: `server/routers/intelligence.py`

```python
router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

@router.get("/estimate/{project_name}")
async def get_build_estimate(project_name: str):
    """Return build time estimate based on historical data."""
    # Returns: {estimated_hours, confidence, sample_count, per_category_breakdown}

@router.get("/risks/{project_name}")
async def get_risk_assessment(project_name: str):
    """Flag high-risk features based on historical patterns."""
    # Returns: [{feature_id, feature_name, risk_level, reason, success_rate}]

@router.get("/patterns")
async def get_feature_patterns(category: str = None, min_samples: int = 10):
    """Get aggregated feature patterns for intelligence display."""
    # Returns: [{category, pattern_name, success_rate, avg_turns, common_pitfalls}]

@router.get("/metrics/{project_name}")
async def get_build_metrics(project_name: str):
    """Get build metrics for a specific project."""
    # Returns: build_metrics row or 404
```

#### 1.10 UI Widgets

**BuildEstimate.tsx** -- Shown during project creation (after spec analysis) and on the project dashboard:

```
+------------------------------------------+
|  Estimated Build Time: 4.5 hours         |
|  Based on 847 similar projects           |
|                                          |
|  Authentication (3 features)   ~45 min   |
|  CRUD Operations (8 features)  ~2.1 hrs  |
|  Payments (2 features)         ~1.2 hrs  |
|  UI Polish (5 features)        ~1.1 hrs  |
|                                          |
|  Risk: 2 high-risk features flagged      |
+------------------------------------------+
```

**RiskBadge.tsx** -- Small badge component shown on feature cards in the kanban board and dependency graph:

- Red shield icon for high-risk features
- Yellow shield for medium-risk
- No badge for low-risk (clean by default)

Hovering the badge shows the historical success rate and common pitfalls for that category.

#### 1.11 Privacy and Anonymization

All data stored locally by default. For SaaS users who opt in to central aggregation:

- `project_id` is a one-way hash of the project name + user ID (not reversible)
- No project names, file paths, or code snippets are ever transmitted
- Feature names are replaced with category + generic pattern name
- `common_failures` descriptions are generalized (e.g., "token refresh logic error" not "line 47 in auth.ts has a bug")
- Users can opt out entirely via settings
- The `feature_patterns` table is shared (aggregate statistics only)

---

## Feature 2: PRD Quality Scoring

### The Problem

The #1 predictor of build quality is spec quality. Bad specs produce bad builds. But users do not know how to write good specs, and AutoForge does not tell them their spec is weak until it is too late -- after hours of agent time have been consumed building something underspecified.

### What It Does

Scores the user's `app_spec.txt` on a 1-5 scale across six dimensions, with actionable feedback for each. The scoring runs before the build starts, giving users a chance to improve their spec.

### Scoring Dimensions

| Dimension | Weight | What It Measures |
|---|---|---|
| Completeness | 25% | Are all user flows defined? Auth? Error handling? Edge cases? |
| Clarity | 20% | Are requirements specific or vague? "Users can manage items" vs "Users can create, read, update, delete items with name, description, and category fields" |
| Consistency | 15% | Do features contradict each other? Are naming conventions consistent? |
| Feasibility | 15% | Are there technically impossible or extremely difficult requirements? |
| Testability | 15% | Can each feature be verified? Are there clear acceptance criteria? |
| Scope | 10% | Is the scope reasonable for the complexity? (20 features = small, 100 = medium, 400+ = large) |

### Score Output Format

The scoring produces a structured markdown report:

```markdown
## PRD Quality Score: 3.2 / 5.0

### Breakdown
- Completeness: 3/5 - Missing error handling flows, no offline behavior defined
- Clarity: 4/5 - Most features well-specified, 3 vague features flagged
- Consistency: 2/5 - Feature 12 contradicts Feature 45 (see details)
- Feasibility: 4/5 - All features technically achievable
- Testability: 3/5 - 15 features lack clear acceptance criteria
- Scope: 4/5 - 120 features, estimated 3-day build

### Critical Issues (must fix before building)
1. Feature 12 says "single profile" but Feature 45 says "switch profiles"
2. No authentication flow defined but 8 features require login

### Recommendations (improve quality)
1. Add error states for all form submissions
2. Specify field types and validation rules for data models
3. Add loading state descriptions for async operations

### Feature-Level Scores
| ID | Feature | Score | Issue |
|----|---------|-------|-------|
| 1 | User Registration | 5/5 | Clean |
| 2 | Dashboard | 3/5 | Vague: "show relevant data" -- what data? |
| ... | ... | ... | ... |
```

### Integration with Build Flow

The score determines how the build proceeds:

| Score Range | Behavior | UI Treatment |
|---|---|---|
| < 2.0 | Block build, require revisions | Red banner, "Fix Issues" button, build button disabled |
| 2.0 - 3.0 | Warning, recommend revisions, allow build with confirmation | Yellow banner, "Proceed Anyway" confirmation dialog |
| 3.0 - 4.0 | Good, show recommendations as optional improvements | Blue info panel, build proceeds normally |
| 4.0 - 5.0 | Excellent, proceed with confidence | Green checkmark, no friction |

The blocking threshold is configurable in settings (default: 2.0). Users who understand the risks can set it to 0 to disable blocking entirely.

### Monetization Tiers (SaaS Only)

This is a natural consulting upsell for the SaaS product:

| Tier | Price | What You Get |
|---|---|---|
| Free | $0 | Overall score (1-5), top 3 critical issues |
| Premium | $29-49 | Full detailed report with per-feature scoring, all recommendations |
| Concierge | $199-499 | AutoForge rewrites the spec for you (agent iterates until score >= 4.0) |

The Concierge tier runs a spec-improvement agent that takes the scoring feedback, rewrites vague features, resolves contradictions, and adds missing flows. It iterates until the score reaches 4.0 or the user approves the result. This is pure margin -- the agent runs on the user's Max subscription, the only cost is the scoring infrastructure.

### Implementation

#### 2.1 Scoring Engine

The scoring is performed by Claude via a structured prompt. This is NOT a rule-based system -- it requires understanding natural language requirements, detecting contradictions, and assessing feasibility. The prompt returns structured JSON that maps to the score format above.

The scoring prompt lives at `.claude/templates/spec_analyzer_prompt.template.md` and is invoked as a one-shot agent call (not a full coding session). It receives the raw `app_spec.txt` content and returns a JSON analysis.

```python
# server/services/spec_scorer.py

class SpecScorer:
    """Scores PRD quality using Claude analysis."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def score_spec(self, spec_content: str) -> SpecScore:
        """Run the spec through Claude for quality scoring.

        Returns a SpecScore dataclass with overall score, dimension
        breakdowns, critical issues, recommendations, and per-feature scores.
        """
        # 1. Load the spec analyzer prompt template
        # 2. Inject the spec content
        # 3. Call Claude (single turn, structured output)
        # 4. Parse the JSON response into SpecScore
        # 5. Store the result in project metadata

    def get_cached_score(self) -> SpecScore | None:
        """Return the most recent score for this project's spec, if any."""
        # Check .autoforge/spec_score.json
```

The `SpecScore` dataclass:

```python
@dataclass
class SpecScore:
    overall: float  # 1.0 - 5.0
    completeness: int  # 1-5
    clarity: int
    consistency: int
    feasibility: int
    testability: int
    scope: int
    critical_issues: list[dict]  # [{description, feature_ids, severity}]
    recommendations: list[str]
    feature_scores: list[dict]  # [{feature_id, name, score, issue}]
    spec_word_count: int
    feature_count: int
    estimated_complexity: int  # 1-5
```

#### 2.2 Spec Analyzer Prompt

`.claude/templates/spec_analyzer_prompt.template.md`:

This prompt instructs Claude to analyze the spec and return structured JSON. Key sections:

1. **Completeness check**: Does every feature define what happens on success AND failure? Are auth flows defined? Are data models specified with field types?
2. **Clarity check**: Flag features with vague language ("relevant data", "appropriate error", "etc.", "various options"). Score higher for specific field names, explicit validation rules, and clear user flow steps.
3. **Consistency check**: Cross-reference features for contradictions. Look for conflicting assumptions about user roles, data models, or navigation structure.
4. **Feasibility check**: Flag requirements that are technically very difficult (real-time collaboration, offline-first sync, complex animation systems) and ensure the spec accounts for the complexity.
5. **Testability check**: Can each feature be verified by an agent looking at a screenshot? Are acceptance criteria clear enough that a testing agent can determine pass/fail?
6. **Scope assessment**: Count features, estimate complexity based on categories, flag if scope is unusually large for the tech stack.

The prompt enforces JSON output format for reliable parsing.

#### 2.3 API Endpoint

```python
# In server/routers/intelligence.py

@router.post("/analyze-spec/{project_name}")
async def analyze_spec(project_name: str, force: bool = False):
    """Trigger spec quality scoring for a project.

    Args:
        project_name: The project to analyze
        force: If True, re-analyze even if a cached score exists

    Returns:
        SpecScore JSON with overall score, breakdowns, and recommendations
    """

@router.get("/spec-score/{project_name}")
async def get_spec_score(project_name: str):
    """Get the cached spec score for a project (if previously analyzed)."""
```

#### 2.4 UI Component: `SpecScoreCard.tsx`

Shown in two contexts:

1. **Project creation wizard** -- After the spec is written/imported, before the build starts. Full-width card with score breakdown, critical issues, and recommendations.
2. **Project dashboard** -- Compact card in the sidebar showing overall score and risk count.

Visual design (neobrutalism style, matching existing components):

```
+--------------------------------------------------+
|  PRD QUALITY SCORE                    3.2 / 5.0  |
|  ================================================|
|                                                   |
|  Completeness  [====------]  3/5                  |
|  Clarity       [======----]  4/5                  |
|  Consistency   [==--------]  2/5                  |
|  Feasibility   [======----]  4/5                  |
|  Testability   [====------]  3/5                  |
|  Scope         [======----]  4/5                  |
|                                                   |
|  ! 2 critical issues found                        |
|  > Feature 12 contradicts Feature 45              |
|  > No auth flow but 8 features require login      |
|                                                   |
|  [Analyze Again]  [View Full Report]              |
+--------------------------------------------------+
```

Color coding:
- Score 4-5: `--color-neo-done` (green) border and accent
- Score 3-4: `--color-neo-progress` (cyan) border and accent
- Score 2-3: `--color-neo-pending` (yellow) border and accent
- Score < 2: Red border and accent with bold warning text

#### 2.5 Score Storage

The score is saved to `.autoforge/spec_score.json` in the project directory:

```json
{
  "scored_at": "2026-02-13T10:30:00Z",
  "spec_hash": "sha256:abc123...",
  "overall": 3.2,
  "dimensions": {
    "completeness": 3,
    "clarity": 4,
    "consistency": 2,
    "feasibility": 4,
    "testability": 3,
    "scope": 4
  },
  "critical_issues": [...],
  "recommendations": [...],
  "feature_scores": [...]
}
```

The `spec_hash` allows detecting when the spec has changed since the last scoring (prompting re-analysis). The score also feeds into `build_metrics.spec_complexity_score` for the Build History Intelligence system.

---

## Feature 3: Continuous Improvement Pipeline

### What It Does

Closes the loop between build outcomes and future build quality. This is the system that makes AutoForge genuinely smarter over time, not just data-collecting.

### The Feedback Cycle

```
User writes spec
  -> PRD Score rates it (Feature 2)
  -> Build Intelligence provides context (Feature 1)
  -> Agents build with enhanced prompts
  -> QA pipeline verifies quality (qa-pipeline-handoff.md)
  -> Metrics collected back into Build Intelligence
  -> Next build is smarter
```

### 3.1 Automated Prompt Tuning

Track which prompt variations produce better outcomes. The key insight: the intelligence context injected by Feature 1 is itself a variable that can be optimized.

**Prompt versioning:**

Every prompt sent to an agent is hashed and stored alongside the build metrics. This creates a mapping: `{prompt_hash} -> {success_rate, avg_turns, rework_rate}`.

When the intelligence context changes (new patterns discovered, wording refined), the new prompt hash creates a natural A/B test against the previous version.

```python
# In prompts.py, add to get_coding_prompt():
import hashlib

def get_coding_prompt(project_dir=None, yolo_mode=False):
    prompt = load_prompt("coding_prompt", project_dir)
    # ... existing context injection ...

    # Version the final prompt for tracking
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

    # Store for later correlation with build outcomes
    # (non-blocking, best-effort)
    try:
        _record_prompt_version(project_dir, prompt_hash, prompt)
    except Exception:
        pass

    return prompt
```

**What gets tracked per prompt version:**

```python
@dataclass
class PromptVersion:
    hash: str              # First 16 chars of SHA-256
    template_name: str     # "coding_prompt", "testing_prompt", etc.
    intelligence_hash: str # Hash of just the intelligence context section
    created_at: str        # ISO 8601
    usage_count: int       # How many times this version was used
    avg_success_rate: float
    avg_turns: float
    avg_rework_rate: float
```

**A/B testing framework:**

`server/services/prompt_experiments.py` manages controlled experiments:

```python
class PromptExperiment:
    """A/B test for prompt variations."""

    def __init__(self, experiment_name: str):
        self.name = experiment_name
        # e.g., "auth_pitfall_wording_v2"

    def get_variant(self, project_id: str) -> str:
        """Deterministically assign a variant based on project ID.

        Uses consistent hashing so the same project always gets the
        same variant within an experiment. This prevents confounding
        from mid-build variant switches.
        """
        # Hash(experiment_name + project_id) mod num_variants

    def record_outcome(self, variant: str, metrics: dict) -> None:
        """Record build outcome for a variant."""

    def get_results(self) -> dict:
        """Get current experiment results with statistical significance."""
        # Returns: {variant_a: {n, success_rate, p_value}, variant_b: ...}
```

Experiments are defined in a simple YAML config:

```yaml
# .autoforge/experiments.yaml (owner/admin only)
experiments:
  - name: auth_pitfall_detail_level
    active: true
    variants:
      control: "Pay attention to token refresh logic."
      detailed: "Pay attention to token refresh logic. The most common failure is not handling the case where the refresh token itself has expired. Always implement a full re-authentication fallback."
    metric: first_try_success_rate
    min_sample_size: 50
```

This is a SaaS-only feature. Local installs do not have enough build volume for statistical significance.

### 3.2 Pattern Library Auto-Generation

When a feature category reaches a threshold of successful builds (configurable, default: 100), the system auto-generates a "best practices" document for that category.

`server/services/pattern_library.py`:

```python
class PatternLibrary:
    """Auto-generates best practice documents from build intelligence."""

    def generate_pattern_doc(self, category: str) -> str | None:
        """Generate a best practices markdown document for a category.

        Only generates when sample_count >= threshold. Returns None
        if insufficient data.

        The document includes:
        - Success rate and common pitfalls
        - Recommended implementation approach
        - Common mistakes to avoid
        - Example architecture patterns from successful builds
        """

    def get_pattern_doc(self, category: str) -> str | None:
        """Get the cached pattern document, or None if not yet generated."""
        # Stored at .autoforge/patterns/{category}.md

    def refresh_all_patterns(self) -> list[str]:
        """Regenerate all pattern docs that have sufficient data.
        Returns list of categories that were refreshed."""
```

The pattern docs are:
- Stored locally in `~/.autoforge/patterns/` (shared across all local projects)
- For SaaS: stored in Supabase, served to all users
- Injected into prompts via `_get_intelligence_context()` when the category matches
- Displayed in the UI as a "Knowledge Base" section (read-only)

Example generated pattern doc:

```markdown
# Authentication Best Practices
*Based on 523 successful builds*

## Recommended Approach
1. Implement email/password auth first, social login second
2. Always use Row Level Security (RLS) policies before writing API routes
3. Store refresh tokens in httpOnly cookies, not localStorage
4. Implement a full re-authentication fallback for expired refresh tokens

## Common Pitfalls (ordered by frequency)
1. **Token refresh race condition** (23% of failures) -- Multiple simultaneous
   requests can trigger multiple refresh attempts. Use a mutex/queue pattern.
2. **Missing auth middleware on API routes** (18%) -- Every new endpoint must
   check auth. Use a route-level middleware, not per-handler checks.
3. **Password validation too weak** (12%) -- Enforce minimum 8 chars, at least
   one uppercase, one number. Show requirements inline, not just on error.

## Architecture Patterns That Work
- Supabase + RLS: 95% first-try success rate (n=312)
- Custom JWT + Express: 78% first-try success rate (n=145)
- NextAuth.js: 89% first-try success rate (n=66)
```

### 3.3 Monthly Analysis Report (SaaS Admin Only)

A scheduled job that runs monthly (or on-demand for the admin):

```python
class IntelligenceReport:
    """Monthly analysis of build metrics and prompt performance."""

    def generate_monthly_report(self) -> str:
        """Produce a markdown report with:
        - Top 5 prompt improvements this month (based on A/B test results)
        - Categories with improving/declining success rates
        - New patterns that crossed the threshold for documentation
        - Total builds, average quality score, trends
        """
```

This report is shown on the admin dashboard (SaaS) and can be used to make manual prompt improvements informed by data.

### 3.4 Feedback Collection from Users

After a build completes, optionally prompt the user for a quality rating (1-5 stars) and a brief comment. This human signal is stored alongside the automated metrics and provides ground truth for whether the intelligence system is actually helping.

Simple UI: a small "How was this build?" card that appears after all features pass, with 5 star icons and an optional text field. Non-intrusive, dismissable, shown only once per build.

---

## File Changes Summary

| File | Change | Priority |
|---|---|---|
| `server/services/build_intelligence.py` | **NEW** -- Metrics collection, querying, intelligence injection | P1 |
| `server/services/spec_scorer.py` | **NEW** -- PRD quality scoring via Claude | P1 |
| `server/services/pattern_library.py` | **NEW** -- Auto-generated best practice documents | P3 |
| `server/services/prompt_experiments.py` | **NEW** -- A/B testing for prompt variations | P3 |
| `server/routers/intelligence.py` | **NEW** -- API endpoints for metrics, estimates, scores, patterns | P1 |
| `.claude/templates/spec_analyzer_prompt.template.md` | **NEW** -- Prompt for spec quality analysis | P1 |
| `api/database.py` | Add `BuildMetric` and `FeaturePattern` models, migration function | P1 |
| `prompts.py` | Add `_get_intelligence_context()` injection, prompt versioning | P1 |
| `parallel_orchestrator.py` | Collect metrics in `_on_agent_complete()` and `run_loop()` completion | P2 |
| `ui/src/components/SpecScoreCard.tsx` | **NEW** -- Visual spec quality display with score breakdown | P2 |
| `ui/src/components/BuildEstimate.tsx` | **NEW** -- Build time estimation widget | P2 |
| `ui/src/components/RiskBadge.tsx` | **NEW** -- Risk level badge for feature cards | P2 |
| `ui/src/components/BuildFeedback.tsx` | **NEW** -- Post-build quality rating card | P3 |
| `server/routers/settings.py` | Add intelligence opt-in settings, score blocking threshold | P2 |
| `ui/src/components/SettingsModal.tsx` | Add intelligence settings section | P2 |
| `ui/src/lib/types.ts` | Add `SpecScore`, `BuildEstimate`, `RiskAssessment` types | P1 |
| `ui/src/lib/api.ts` | Add API client methods for intelligence endpoints | P1 |
| `ui/src/hooks/useProjects.ts` | Add React Query hooks for intelligence data | P2 |

---

## Implementation Priority

Build these in order. Each phase is independently valuable.

### Phase 1: PRD Quality Scoring (Week 1)

**Why first:** Immediate user-facing value. Users see a score before their first build. No historical data required -- the scoring is per-spec, not aggregate.

1. Create `.claude/templates/spec_analyzer_prompt.template.md`
2. Create `server/services/spec_scorer.py`
3. Add `POST /api/intelligence/analyze-spec/{project_name}` endpoint
4. Add `GET /api/intelligence/spec-score/{project_name}` endpoint
5. Create `ui/src/components/SpecScoreCard.tsx`
6. Wire into project creation flow (show score after spec is written)
7. Store scores in `.autoforge/spec_score.json`

**Deliverable:** Users see a quality score with actionable feedback before every build.

### Phase 2: Build Metrics Collection (Week 2)

**Why second:** Starts accumulating data immediately. No visible user impact yet, but every build from this point forward contributes to the intelligence database.

1. Add `BuildMetric` and `FeaturePattern` models to `api/database.py`
2. Add migration function, wire into `create_database()`
3. Create `server/services/build_intelligence.py` (collection methods only)
4. Integrate collection into `parallel_orchestrator.py`:
   - `run_loop()` start: call `collect_build_start_metrics()`
   - `_on_agent_complete()`: call `record_agent_session()`
   - `run_loop()` completion: call `collect_build_end_metrics()`
5. Verify metrics are being written correctly with a test build

**Deliverable:** Every build silently records metrics. No user-facing changes yet.

### Phase 3: Intelligence Injection (Week 3)

**Why third:** Requires data from Phase 2. Even with just 5-10 builds of local data, the system can start providing useful intelligence. With SaaS aggregate data, it is useful immediately.

1. Implement `get_intelligence_context()` in `build_intelligence.py`
2. Add `_get_intelligence_context()` to `prompts.py`
3. Inject into `get_coding_prompt()` and `get_single_feature_prompt()`
4. Add build estimate and risk assessment methods to `build_intelligence.py`
5. Create `server/routers/intelligence.py` with estimate and risk endpoints
6. Create `ui/src/components/BuildEstimate.tsx`
7. Create `ui/src/components/RiskBadge.tsx`
8. Wire into project dashboard and kanban board

**Deliverable:** Agents receive historical intelligence. Users see build estimates and risk badges.

### Phase 4: Continuous Improvement (Week 4+)

**Why last:** Requires significant build volume to be useful. Start collecting prompt versions immediately but do not invest in A/B testing until there are 50+ builds in the system.

1. Add prompt versioning to `prompts.py`
2. Create `server/services/prompt_experiments.py` (framework only)
3. Create `server/services/pattern_library.py`
4. Create pattern doc generation logic
5. Create `ui/src/components/BuildFeedback.tsx`
6. Add intelligence settings to settings panel
7. Create admin intelligence dashboard (SaaS only)

**Deliverable:** The system improves its own prompts over time. Pattern docs are auto-generated.

---

## Cost Analysis

### Spec Scoring Cost

The spec scorer runs a single Claude call per analysis. At current pricing (Max subscription):

- One call per spec analysis: ~5,000-15,000 tokens (spec + prompt + response)
- Rate limit impact: Minimal (single call, not a full agent session)
- User-facing latency: 10-30 seconds for the analysis to complete
- Amortized: Users typically analyze 1-3 times per project (initial + revisions)

For the SaaS Concierge tier ($199-499), the spec improvement agent runs 3-5 iterations at ~10,000 tokens each. Total cost: negligible on Max subscription. Pure margin.

### Build Intelligence Cost

- Storage: ~1KB per build_metrics row, ~500 bytes per feature_patterns row
- For 1,000 builds: ~1.5 MB total (trivial for SQLite or Supabase)
- Compute: Pattern aggregation is simple arithmetic (no ML, no expensive queries)
- Prompt overhead: Intelligence context adds 100-300 tokens per coding prompt (~0.2% of total)
- No additional API calls -- all intelligence is pre-computed and injected into existing prompts

### Continuous Improvement Cost

- Prompt versioning: ~100 bytes per version entry (hash + metadata)
- A/B testing: No additional API calls -- uses natural build variance
- Pattern library generation: One Claude call per category when threshold is crossed (~monthly)
- Monthly report: One Claude call per month for SaaS admin

**Total incremental cost: Effectively zero.** The intelligence system piggybacks on existing build processes and adds negligible storage and compute overhead.

---

## Revenue Implications

### Direct Revenue (SaaS Only)

| Revenue Stream | Price | Est. Monthly Volume | Monthly Revenue |
|---|---|---|---|
| Premium spec reports | $29-49 | 50-100 reports | $1,450 - $4,900 |
| Concierge spec rewrites | $199-499 | 5-15 engagements | $995 - $7,485 |

Conservative estimate at 500 SaaS users: **$2,500 - $12,000/month** additional revenue from PRD scoring alone.

### Indirect Revenue (Retention + Conversion)

- **Reduced churn:** Builds succeed more often when agents are warned about pitfalls. Fewer "this tool doesn't work" cancellations.
- **Higher conversion:** Build time estimates and quality scores give users confidence to start. Removes the "will this actually work?" anxiety.
- **Word of mouth:** "AutoForge told me my spec had a contradiction before I wasted 4 hours" is a compelling story.
- **Competitive moat:** No competitor tracks build intelligence. This is proprietary data that gets more valuable with every user. Network effect: more users -> better patterns -> better builds -> more users.

### The Flywheel

```
More users
  -> more builds
    -> more intelligence data
      -> better prompts
        -> higher build quality
          -> more satisfied users
            -> more referrals
              -> more users (repeat)
```

This is the core strategic advantage. Build intelligence is a network effect that competitors cannot replicate without the build volume to train on.

---

## Integration with Existing Handoffs

### QA Pipeline (qa-pipeline-handoff.md)

The QA pipeline produces quality scores (`qa_score`, `performance_score`, `security_score`) that feed directly into `build_metrics`. The review agent's issue counts feed into `review_issues_found` and `review_issues_by_severity`. The QA agent's final report feeds into `qa_issues_found`.

Build Intelligence should be implemented BEFORE the QA pipeline ships, so that when QA data starts flowing, the intelligence system is ready to ingest it. Phase 2 (metrics collection) includes placeholder fields for QA data that will be populated once the QA pipeline is live.

### Self-Deploy VPS (self-deploy-vps-handoff.md)

For VPS deployments, build intelligence runs locally (SQLite in the project's features.db). No central aggregation. Users benefit from their own historical data only.

For the managed SaaS (Fly.io deployment), aggregate intelligence is shared across all users (anonymized). This is a key differentiator of the managed service vs. self-hosted.

### Style Picker (style-preview-grid-handoff.md)

The `style_used` field in `build_metrics` tracks which design style was selected. Over time, this reveals which styles produce the cleanest builds (fewer CSS-related regressions, fewer responsive design issues). This data can inform style recommendations: "Projects using Minimalism style had 12% fewer UI regressions than Glassmorphism."

---

## Technical Notes

### Database Compatibility

The new tables use the same SQLAlchemy patterns as `Feature`, `Schedule`, and `ScheduleOverride`. They share the same `features.db` file and benefit from the existing WAL mode, IMMEDIATE transactions, and busy timeout configuration.

The migration functions follow the established pattern: check if the table exists, create if missing, add columns if upgrading from a previous version. This ensures zero-downtime upgrades.

### Thread Safety

`BuildIntelligence` methods may be called from the orchestrator's output reader threads (via `_on_agent_complete`). All database operations use the existing `atomic_transaction()` context manager from `api/database.py`, which handles locking correctly.

Metrics collection is best-effort: failures are caught and logged but never propagate to the orchestrator. The intelligence system must never break the build process.

### Backwards Compatibility

Projects created before the intelligence system exists will work unchanged:
- The new tables are created by migration (not required at startup)
- `_get_intelligence_context()` returns empty string when no data exists
- Build estimates fall back to step-count heuristics (existing `_estimate_feature_turns()`)
- Risk badges are hidden when no pattern data is available
- Spec scoring is opt-in (triggered by user, not automatic)

### Data Seeding for New Installs

To provide value from day one (before any local builds have completed), ship a `seed_patterns.json` file with the package containing baseline feature patterns derived from aggregate SaaS data:

```json
[
  {
    "category": "authentication",
    "pattern_name": "email-password-auth",
    "success_rate": 82,
    "avg_turns_to_implement": 45,
    "common_pitfalls": ["Token refresh race condition", "Missing auth middleware on new routes"],
    "recommended_approach": "Implement RLS policies before writing any API routes...",
    "sample_count": 500
  }
]
```

This file is loaded on first run if `feature_patterns` is empty. Local build data overwrites the seed data as it accumulates (local data is weighted higher than seed data to reflect the user's actual patterns).
