# Phase 4: Final Blueprint, Golden Orange, Quality Gate

> The three finishing stages that turn a PRD into a build-ready package.

**Priority**: HIGH — these are the crown jewels that differentiate from any other PRD tool.
**Depends on**: Phase 1-3 (all upstream stages feed into these).

---

## Overview

Three entirely new stages that come AFTER spec generation but BEFORE handoff:

```
... → Specs → [Final Blueprint] → [Golden Orange] → [Quality Gate] → Handoff
```

- **Final Blueprint** = the companion sheet (build learnings, backup briefs, concern flags)
- **Golden Orange** = exhaustive feature imagination with utopia line
- **Quality Gate** = score the PRD on 6 dimensions, block build if score too low

---

## 4.1 Final Blueprint / Companion Sheet (Stage 9)

### File: `server/services/agent_os_blueprint.py` (NEW)

**Class**: `AgentOSBlueprint`

**Purpose**: Generate the companion document that goes alongside the PRD. This is
NOT the PRD — it's the meta-document about the PRD. Build learnings, backup plans,
concern flags, opportunity flags, contextual build notes.

```python
class AgentOSBlueprint:
    """Generate the Final Blueprint companion sheet.

    This document contains everything the builder needs to know BEYOND
    the feature specs: what the scoring revealed, what to watch for,
    what opportunities emerged, and implementation hints.
    """

    def __init__(self, project_dir: Path, provenance: ProvenanceTracker):
        self.project_dir = project_dir
        self.provenance = provenance

    def get_blueprint_prompt(
        self,
        features: list[dict],
        mechanism_decisions: list[dict],
        caveat_appendix: str,
        refinement_pairs: list[dict],
        recalibration_results: dict,
        coverage: dict,
        specs_summary: dict,
    ) -> str:
        """Generate prompt for Final Blueprint.

        Claude produces:
        1. Mechanism Learnings — what the scoring revealed about the app's nature
        2. Backup Briefs — for each close-call, what to do if primary fails
        3. Concern Flags — things that could go wrong during implementation
        4. Opportunity Flags — things that emerged that could add unexpected value
        5. Contextual Build Notes — implementation hints the builder should know
        6. Provenance Summary — where each decision came from
        7. Architecture DNA — the architectural philosophy that emerged
        """
        ...

    def process_blueprint(self, blueprint_json: dict) -> dict:
        """Process Claude's blueprint output."""
        ...

    def generate_blueprint_file(self, blueprint: dict) -> Path:
        """Write .agent/knowledge/final-blueprint.md"""
        ...

    def get_mechanism_learnings(self, mechanism_decisions: list[dict]) -> str:
        """Analyze patterns in mechanism scores.

        Examples of learnings:
        - "This app consistently scores highest on simplicity over feature-richness"
        - "Security scores were uniformly high — this is a security-conscious product"
        - "Brand alignment drove 4 of 7 close-call decisions"
        """
        ...
```

### Blueprint Output Schema

```json
{
  "mechanism_learnings": [
    {
      "pattern": "simplicity_bias",
      "description": "This app consistently favors simple solutions over feature-rich ones. 8 of 12 mechanisms chose the simpler option.",
      "implication": "Builder should resist over-engineering. If in doubt, choose fewer features over more."
    }
  ],
  "backup_briefs": [
    {
      "mechanism_id": "UI-003",
      "primary": "React Flow",
      "backup": "CSS Grid + Canvas",
      "switch_trigger": "If bundle size exceeds 200KB or mobile performance drops below 2s load",
      "switch_steps": [
        "Replace ReactFlow import with custom Canvas component",
        "Migrate node definitions to CSS Grid positions",
        "Update tests from ReactFlow selectors to canvas queries"
      ],
      "estimated_switch_time": "5-7 days"
    }
  ],
  "concern_flags": [
    {
      "severity": "high",
      "area": "Authentication",
      "concern": "Magic links require reliable email delivery. If using a free SMTP tier, delivery rates may be <90%.",
      "mitigation": "Test with at least 2 email providers. Have a fallback to password login."
    }
  ],
  "opportunity_flags": [
    {
      "value": "high",
      "area": "API Design",
      "opportunity": "The REST API structure naturally supports a mobile app. Consider exposing it as a public API from day 1.",
      "effort": "Low — just add CORS headers and rate limiting"
    }
  ],
  "build_notes": [
    {
      "category": "dependency_order",
      "note": "Features 1-3 (auth, database, API) are foundational. Features 4-8 can be parallelized after those complete."
    },
    {
      "category": "tech_debt_risk",
      "note": "The user said 'no tests for MVP' but 6 features have complex edge cases. Recommend at least integration tests for auth and payments."
    }
  ],
  "architecture_dna": {
    "philosophy": "Simple-first, security-conscious, mobile-ready",
    "key_patterns": ["Server-rendered with client hydration", "SQLite for simplicity, PostgreSQL migration path"],
    "anti_patterns": ["Don't add caching until proven needed", "Don't abstract database layer prematurely"]
  },
  "provenance_summary": {
    "USER": 23,
    "AUTO_FILL": 8,
    "USER_DECIDED": 5,
    "RECOMMENDED": 12,
    "INFERRED": 7
  }
}
```

### Generated File: `.agent/knowledge/final-blueprint.md`

```markdown
# Final Blueprint — {Project Name}

## Architecture DNA
{philosophy, key patterns, anti-patterns}

## Mechanism Learnings
{patterns discovered during scoring}

## Backup Briefs
{for each close call: primary, backup, switch trigger, switch steps}

## Concern Flags
{high > medium > low severity, with mitigations}

## Opportunity Flags
{high > medium > low value, with effort estimates}

## Build Notes
{implementation hints by category}

## Provenance Summary
{count of items per provenance tag}

## Appendix: Caveat Appendix
{full caveat appendix from mechanism analysis}
```

---

## 4.2 Golden Orange Feature Extraction (Stage 10)

### File: `server/services/agent_os_golden_orange.py` (NEW)

**Class**: `AgentOSGoldenOrange`

**Purpose**: Exhaustive feature imagination. Generate every possible feature the
app could have, organized by category, with a clear "Utopia Line" marking where
practical value ends and diminishing returns begin.

This is the feature backlog generator. Users get a complete picture of what
their app COULD become, not just what they described.

```python
class AgentOSGoldenOrange:
    """Exhaustive feature imagination engine.

    Takes the current feature list + product context and generates
    every possible additional feature, organized by category.
    """

    CATEGORIES = [
        "natural_extensions",    # Obvious next features from what exists
        "cross_mechanism",       # Features combining multiple technical choices
        "competitive",           # What competitors have that this doesn't
        "scale",                 # What you need when you grow 10x/100x
        "monetization",          # Revenue opportunities
        "delight",               # Things that make users love it (not just use it)
    ]

    def __init__(self, project_dir: Path, config: dict):
        self.project_dir = project_dir
        self.config = config
        self.generated_features: list[dict] = []
        self.utopia_line_index: int = -1  # Features above this: build. Below: nice to dream.

    def get_extraction_prompt(
        self,
        existing_features: list[dict],
        product_summary: str,
        mechanism_decisions: list[dict],
        blueprint: dict,
    ) -> str:
        """Generate prompt for exhaustive feature imagination.

        Claude is instructed to:
        1. Review everything that exists
        2. For EACH category, generate 5-15 feature ideas
        3. Score each on value (1-10) and effort (1-10)
        4. Mark the Utopia Line — the point where effort/value ratio inverts
        5. Deduplicate against existing features
        6. Flag features that would require architectural changes
        """
        ...

    def process_extraction(self, extraction_json: dict) -> dict:
        """Process Golden Orange output.

        Returns:
        {
            "categories": {
                "natural_extensions": [
                    {
                        "name": "Bulk import from CSV",
                        "description": "...",
                        "value_score": 8,
                        "effort_score": 3,
                        "ratio": 2.67,
                        "above_utopia_line": true,
                        "requires_architecture_change": false,
                        "related_existing_features": [2, 5]
                    }
                ],
                ...
            },
            "utopia_line": {
                "index": 23,  # Features 1-23 are above the line
                "total": 47,
                "above_count": 23,
                "below_count": 24,
                "rationale": "Features below this point have effort/value ratio > 3:1"
            },
            "highlight_features": [
                # Top 5 across all categories by value/effort ratio
            ],
            "architectural_impacts": [
                # Features that would require changes to existing architecture
            ]
        }
        """
        ...

    def get_feature_list(self, above_utopia_only: bool = False) -> list[dict]:
        """Return generated features, optionally filtered to above utopia line."""
        ...

    def promote_to_roadmap(self, feature_ids: list[int]) -> list[dict]:
        """User promotes Golden Orange features to the actual feature list.

        Returns features formatted for AgentOSFeatures.add_feature().
        Tagged with provenance FEATURE_ADD.
        """
        ...

    def generate_golden_orange_file(self) -> Path:
        """Write .agent/knowledge/golden-orange.md"""
        ...
```

### Golden Orange Output File: `.agent/knowledge/golden-orange.md`

```markdown
# Golden Orange — Feature Imagination Report

## Summary
- {total} features imagined across {len(categories)} categories
- {above_count} above the Utopia Line (practical value)
- {below_count} below the Utopia Line (diminishing returns)

## Highlight Features (Top 5 Value/Effort)
{top 5 with brief descriptions}

---

## Natural Extensions
{features sorted by value/effort ratio}

## Cross-Mechanism Features
{features that combine multiple technical choices}

## Competitive Features
{what competitors have}

## Scale Features
{growth requirements}

## Monetization Features
{revenue opportunities}

## Delight Features
{user love features}

---

═══════════════════════════════════════════════
                UTOPIA LINE
  Everything above: practical value
  Everything below: diminishing returns
═══════════════════════════════════════════════

---

## Below the Line
{remaining features, still documented but marked as diminishing returns}

---

## Architectural Impacts
{features that would require architecture changes, with details}
```

### Session Integration

```python
async def _handle_golden_orange(self, message: str):
    """Stage 10: Golden Orange Feature Extraction."""
    if not self.config["agent_os"]["golden_orange"]["enabled"]:
        yield {"type": "stage_change", "stage": "quality_gate", ...}
        return

    prompt = self.golden_orange.get_extraction_prompt(
        existing_features=self.features.get_feature_list(),
        product_summary=self.product.get_product_summary(),
        mechanism_decisions=self.mechanism.decisions,
        blueprint=self.blueprint_data,
    )
    result = await self.orchestrator.execute(
        prompt=prompt,
        model="sonnet",
        max_tokens=32000,  # Larger output for exhaustive list
        stage_name="golden_orange"
    )
    golden = self.golden_orange.process_extraction(result)
    self.golden_orange.generate_golden_orange_file()

    yield {
        "type": "golden_orange",
        "summary": golden["utopia_line"],
        "highlights": golden["highlight_features"],
        "categories": {k: len(v) for k, v in golden["categories"].items()},
        "total": sum(len(v) for v in golden["categories"].values()),
    }

    # User can optionally promote features
    if message == "__approve__":
        # Continue to quality gate
        ...
```

---

## 4.3 Quality Gate (Stage 11)

### File: `server/services/agent_os_quality_gate.py` (NEW)

**Class**: `AgentOSQualityGate`

**Purpose**: Score the complete PRD on 6 quality dimensions. Block the build if
the score is too low. This is the final check before handoff.

```python
class AgentOSQualityGate:
    """Score the PRD and gate the build on quality.

    6 dimensions, weighted, producing a 1.0-5.0 overall score.
    Build gating: <2.0 blocks, 2.0-3.0 warning, 3.0+ proceed.
    """

    DIMENSIONS = {
        "completeness": 0.25,  # Are all features fully specified?
        "clarity": 0.20,       # Is the language unambiguous?
        "consistency": 0.15,   # Do sections agree with each other?
        "feasibility": 0.15,   # Can this actually be built as described?
        "testability": 0.15,   # Can acceptance criteria be verified?
        "scope": 0.10,         # Is scope appropriate (not too big/small)?
    }

    def __init__(self, project_dir: Path, config: dict):
        self.project_dir = project_dir
        self.config = config
        self.scores: Optional[dict] = None

    def get_scoring_prompt(
        self,
        features: list[dict],
        specs: dict[int, str],
        standards_summary: str,
        product_summary: str,
        blueprint: dict,
        provenance_summary: dict,
    ) -> str:
        """Generate prompt for PRD quality scoring.

        Claude scores each dimension 1-5 with detailed reasoning:
        - 1: Critical gaps, blocks build
        - 2: Significant issues, build at risk
        - 3: Adequate, some improvements possible
        - 4: Good, minor polish needed
        - 5: Excellent, production-ready

        Plus per-feature scores for completeness and testability.
        """
        ...

    def process_scores(self, scores_json: dict) -> dict:
        """Process quality scores.

        Returns:
        {
            "overall_score": 3.7,
            "overall_grade": "good",  # excellent/good/warning/blocked
            "dimensions": {
                "completeness": {
                    "score": 4,
                    "weight": 0.25,
                    "weighted_score": 1.0,
                    "reasoning": "All 12 features have specs with acceptance criteria. 2 features missing edge case coverage.",
                    "improvement_suggestions": [
                        "Add error state handling to feature 7",
                        "Define offline behavior for features 3 and 9"
                    ]
                },
                ...
            },
            "per_feature_scores": {
                1: {"completeness": 4, "testability": 5},
                2: {"completeness": 3, "testability": 4},
                ...
            },
            "build_recommendation": "proceed",  # "proceed" | "proceed_with_warnings" | "blocked"
            "blocking_issues": [],  # Empty if not blocked
            "warnings": [
                "Feature 7 has no error handling spec",
                "Feature 3's offline behavior is undefined"
            ]
        }
        """
        ...

    def is_build_ready(self) -> bool:
        """True if overall score >= minimum_score from config."""
        ...

    def get_improvement_plan(self) -> list[dict]:
        """Return prioritized improvements to increase score."""
        ...

    def generate_quality_report(self) -> Path:
        """Write .agent/knowledge/quality-report.md"""
        ...
```

### Session Integration

```python
async def _handle_quality_gate(self, message: str):
    """Stage 11: Quality Gate."""
    if not self.config["agent_os"]["quality_gate"]["enabled"]:
        yield {"type": "stage_change", "stage": "handoff", ...}
        return

    prompt = self.quality_gate.get_scoring_prompt(
        features=self.features.get_feature_list(),
        specs=self.specs.get_all_specs(),
        standards_summary=self.standards.get_standards_summary(),
        product_summary=self.product.get_product_summary(),
        blueprint=self.blueprint_data,
        provenance_summary=self.provenance.get_provenance_summary(),
    )
    result = await self.orchestrator.execute(prompt, stage_name="quality_gate")
    scores = self.quality_gate.process_scores(result)
    self.quality_gate.generate_quality_report()

    if scores["build_recommendation"] == "blocked":
        yield {
            "type": "quality_gate_blocked",
            "scores": scores,
            "blocking_issues": scores["blocking_issues"],
            "improvement_plan": self.quality_gate.get_improvement_plan(),
        }
        # Session stays at this stage until issues are fixed
    elif scores["build_recommendation"] == "proceed_with_warnings":
        yield {
            "type": "quality_gate_warning",
            "scores": scores,
            "warnings": scores["warnings"],
        }
        # User can proceed or fix
    else:
        yield {
            "type": "quality_gate_passed",
            "scores": scores,
            "overall_score": scores["overall_score"],
            "grade": scores["overall_grade"],
        }
        # Auto-advance to handoff
```

---

## 4.4 Enhanced Handoff (Stage 12)

### Modify: `server/services/agent_os_handoff.py`

The handoff stage gains new artifacts from Phases 2-4:

```python
def assemble_handoff_package(self) -> dict:
    """Enhanced handoff package with new artifacts.

    Now includes:
    - features.db (existing)
    - scope_boundary.md (existing)
    - context_primer.md (existing, enhanced)
    - final-blueprint.md (NEW from Phase 4)
    - golden-orange.md (NEW from Phase 4)
    - quality-report.md (NEW from Phase 4)
    - provenance.json (NEW from Phase 1)
    - caveat-appendix (NEW from Phase 3, embedded in blueprint)
    """
    ...

def generate_context_primer(self) -> Path:
    """Enhanced context primer now includes:

    - Standards Summary
    - Product Vision
    - Feature Overview
    - Build Order
    - Key Decisions (mechanism analysis)
    - Spec Index
    - Blueprint Highlights (NEW)
    - Quality Score (NEW)
    - Provenance Summary (NEW)
    - Concern Flags (NEW, from blueprint)
    """
    ...
```

---

## 4.5 New Router Endpoints

### Modify: `server/routers/agent_os.py`

```python
# Golden Orange
@router.get("/golden-orange/{project_name}")
async def get_golden_orange(project_name: str):
    """Get Golden Orange feature imagination results."""
    ...

@router.post("/golden-orange/{project_name}/promote")
async def promote_golden_orange_features(project_name: str, feature_ids: list[int]):
    """Promote Golden Orange features to actual feature list."""
    ...

# Quality Gate
@router.get("/quality/{project_name}")
async def get_quality_scores(project_name: str):
    """Get PRD quality scores."""
    ...

@router.get("/quality/{project_name}/improvements")
async def get_improvement_plan(project_name: str):
    """Get prioritized improvement plan."""
    ...

# Blueprint
@router.get("/blueprint/{project_name}")
async def get_final_blueprint(project_name: str):
    """Get the Final Blueprint companion sheet."""
    ...

# Provenance
@router.get("/provenance/{project_name}")
async def get_provenance_summary(project_name: str):
    """Get provenance summary (counts per tag)."""
    ...

@router.get("/provenance/{project_name}/matrix")
async def get_provenance_matrix(project_name: str):
    """Get full provenance matrix."""
    ...
```

---

## Phase 4 Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | Final Blueprint service | `server/services/agent_os_blueprint.py` |
| 2 | Golden Orange service | `server/services/agent_os_golden_orange.py` |
| 3 | Quality Gate service | `server/services/agent_os_quality_gate.py` |
| 4 | Enhanced handoff | `server/services/agent_os_handoff.py` (modify) |
| 5 | Session handlers (3 new stages) | `server/services/agent_os_session.py` (modify) |
| 6 | Router endpoints (7 new) | `server/routers/agent_os.py` (modify) |
| 7 | Tests | `test_agent_os_blueprint.py`, `test_agent_os_golden_orange.py`, `test_agent_os_quality_gate.py` |

**Estimated complexity**: High. Blueprint and Golden Orange require sophisticated
prompt engineering to get useful, non-generic output. Quality Gate is straightforward
scoring logic with clear pass/fail criteria.

---

## Implementation Order (Within Phase 4)

1. **Quality Gate first** — simplest, immediate value, gates the build
2. **Final Blueprint second** — depends on mechanism data being complete
3. **Golden Orange last** — most creative, least critical to pipeline integrity
4. **Enhanced Handoff** — wire everything together

---

## Full Pipeline (After All 4 Phases)

```
Stage 0:   Intake Dock ............. agent_os_intake_dock.py
Stage 1:   Intake .................. agent_os_intake.py
  └─ 1.5:  Transcription Verify .... agent_os_verify.py
Stage 2:   Standards ............... agent_os_standards.py
Stage 3:   Product Discovery ....... agent_os_product.py
  └─ 3.5:  Technical Refinement .... agent_os_refinement.py
Stage 4:   Feature Extraction ...... agent_os_features.py
  └─ 4.5:  Coverage Assessment ..... agent_os_features.py
Stage 5:   Recalibration ........... agent_os_recalibration.py
Stage 6:   Gap Analysis ............ agent_os_features.py
Stage 7:   Mechanism Analysis ...... agent_os_mechanism.py (6-dim)
  └─ 7.5:  Mechanism Verify ........ agent_os_verify.py
Stage 8:   Spec Generation ......... agent_os_specs.py
  └─ 8.5:  PRD Verify .............. agent_os_verify.py
Stage 9:   Final Blueprint ......... agent_os_blueprint.py
Stage 10:  Golden Orange ........... agent_os_golden_orange.py
Stage 11:  Quality Gate ............ agent_os_quality_gate.py
Stage 12:  Database Population ..... agent_os_handoff.py
Stage 13:  Handoff ................. agent_os_handoff.py

Cross-stage:
  Orchestrator .................. agent_os_orchestrator.py
  Provenance .................... agent_os_provenance.py
  Verifier ...................... agent_os_verify.py
  File Utils .................... agent_os_file_utils.py
  Expand ........................ agent_os_expand.py
  Codebase Analyzer ............. agent_os_codebase.py
```

**Total service files**: 16 (was 10) — 6 new, 10 existing (4 modified).
**Total pipeline stages**: 17 (including sub-stages) | 13 user-visible.
**Total router endpoints**: ~40 (was ~25) | ~15 new.
