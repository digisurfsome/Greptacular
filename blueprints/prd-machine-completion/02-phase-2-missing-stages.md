# Phase 2: Missing Pipeline Stages

> Technical Refinement, Recalibration, Coverage Assessment.

**Priority**: HIGH — these fill gaps in the core pipeline flow.
**Depends on**: Phase 1 (LLM Orchestration + Provenance).

---

## Overview

Three stages that were in OPERATIONAL_TRUTH_v3 but never implemented.
They slot into the existing pipeline between Product Discovery and Feature Extraction.

Current flow:
```
Intake → Standards → Product → [GAP] → Features → Gaps → Specs → Handoff
```

After this phase:
```
Intake → Standards → Product → Refinement → Coverage → Features → Recalibration → Gaps → Specs → Handoff
```

---

## 2.1 Technical Refinement (Stage 3.5)

### File: `server/services/agent_os_refinement.py` (NEW)

**Class**: `AgentOSRefinement`

**Purpose**: Translate casual/babble descriptions into precise technical language
while preserving the original quote for verification.

**Why this matters**: Users say "I want the thing to be fast." The builder needs
"Response time < 200ms at p95 for API endpoints." Without this stage, ambiguous
language propagates into features and specs, causing implementation confusion.

```python
class AgentOSRefinement:
    """Translate casual descriptions to precise technical language.

    Produces original_quote -> technical_translation pairs with provenance.
    """

    def __init__(self, project_dir: Path, provenance: ProvenanceTracker):
        self.project_dir = project_dir
        self.provenance = provenance
        self.refinements: list[dict] = []

    def get_refinement_prompt(self, entities: dict, product_docs: dict) -> str:
        """Generate prompt for technical translation.

        Prompt instructs Claude to:
        1. Read all entities and product docs
        2. For each vague/casual statement, produce:
           - original_quote: exact text from user
           - technical_translation: precise technical equivalent
           - confidence: 0.0-1.0 (how sure is the translation)
           - ambiguity_flag: bool (true if multiple interpretations possible)
           - alternatives: list[str] (if ambiguous, what are the options)
        3. Flag contradictions between statements
        4. Preserve statements that are already technical as-is
        """
        ...

    def process_refinements(self, refinements_json: list[dict]) -> list[dict]:
        """Process Claude's refinement output.

        - Assign IDs
        - Tag provenance (INFERRED for translations, USER for preserved)
        - Flag ambiguous items for user review
        - Detect contradictions between translations
        """
        ...

    def get_ambiguous_items(self) -> list[dict]:
        """Return items that need user clarification."""
        ...

    def resolve_ambiguity(self, item_id: int, chosen_translation: str) -> dict:
        """User picks the correct interpretation."""
        ...

    def get_contradictions(self) -> list[dict]:
        """Return detected contradictions between refined statements."""
        ...

    def resolve_contradiction(self, item_id: int, resolution: str) -> dict:
        """User resolves a contradiction."""
        ...

    def get_refined_context(self) -> str:
        """Return all refinements as text context for downstream stages."""
        ...

    def export_refinement_pairs(self) -> list[dict]:
        """Export for inclusion in Final Blueprint."""
        ...
```

**Refinement Output Schema**:
```json
{
  "refinements": [
    {
      "id": 1,
      "original_quote": "I want the thing to be fast",
      "technical_translation": "API response time < 200ms at p95 under 1000 concurrent users",
      "confidence": 0.7,
      "ambiguity_flag": true,
      "alternatives": [
        "Page load time < 1s on 3G networks",
        "Database query execution < 50ms"
      ],
      "source_stage": "intake",
      "source_entity": "constraints",
      "provenance": "INFERRED"
    }
  ],
  "contradictions": [
    {
      "id": 1,
      "statement_a": "Keep it simple, no frameworks",
      "statement_b": "Use React for the frontend",
      "conflict_type": "direct_contradiction",
      "suggested_resolution": "User likely means 'minimal dependencies' while accepting React as necessary"
    }
  ]
}
```

### Session Integration

In `agent_os_session.py`, add `_handle_refinement()` between product discovery
and feature extraction:

```python
async def _handle_refinement(self, message: str):
    """Stage 3.5: Technical Refinement."""
    if not self.config["agent_os"].get("refinement", {}).get("enabled", True):
        # Skip if disabled
        yield {"type": "stage_change", "stage": "coverage_assessment", ...}
        return

    prompt = self.refinement.get_refinement_prompt(
        entities=self.intake.entities,
        product_docs=self._get_product_context()
    )
    result = await self.orchestrator.execute(prompt, stage_name="refinement")
    refinements = self.refinement.process_refinements(result.get("refinements", []))

    # Check for ambiguities that need user input
    ambiguous = self.refinement.get_ambiguous_items()
    if ambiguous:
        yield {
            "type": "refinement_review",
            "refinements": refinements,
            "ambiguous": ambiguous,
            "contradictions": self.refinement.get_contradictions()
        }
        # Wait for user resolution...
    else:
        yield {"type": "message", "content": f"Refined {len(refinements)} items. No ambiguities."}
        # Auto-advance
```

---

## 2.2 Coverage Assessment (Stage 4.5)

### Modify: `server/services/agent_os_features.py`

**New method on `AgentOSFeatures`**:

```python
def calculate_coverage(self) -> dict:
    """Calculate how much of the app the user has described.

    Returns percentage based on:
    - Entity completeness (8 fields, weighted)
    - Product doc completeness (6 docs)
    - Feature count vs expected (based on app complexity)
    - Standards completeness (6 files)

    Reference baselines:
    - Detailed user: 65-70%
    - Average user: 10-30%
    """
    ...

def get_coverage_prompt(self) -> str:
    """Claude assesses coverage with reasoning.

    Prompt asks Claude to:
    1. Review all accumulated context
    2. Estimate what percentage of the total app is described
    3. Identify the biggest uncovered areas
    4. Estimate app complexity (simple/medium/complex)
    5. Suggest number of features likely needed vs described
    """
    ...

def process_coverage(self, coverage_json: dict) -> dict:
    """Process coverage assessment.

    Returns:
    {
        "overall_percentage": 45,
        "breakdown": {
            "entities": 60,
            "product": 50,
            "features": 35,
            "standards": 70
        },
        "uncovered_areas": [
            {"area": "Error handling strategy", "importance": "high"},
            {"area": "Offline behavior", "importance": "medium"}
        ],
        "estimated_complexity": "medium",
        "estimated_total_features": 25,
        "described_features": 9,
        "user_level": "average"  # or "detailed"
    }
    """
    ...
```

### Session Integration

After feature extraction, before gap analysis:

```python
async def _handle_coverage_assessment(self, message: str):
    """Stage 4.5: Coverage Assessment."""
    # Local calculation (fast, no LLM)
    local_coverage = self.features.calculate_coverage()

    # LLM-enhanced assessment
    prompt = self.features.get_coverage_prompt()
    result = await self.orchestrator.execute(prompt, stage_name="coverage_assessment")
    coverage = self.features.process_coverage(result)

    yield {
        "type": "coverage_report",
        "coverage": coverage,
        "message": f"You've described approximately {coverage['overall_percentage']}% of the app. "
                   f"({coverage['described_features']} of ~{coverage['estimated_total_features']} features)"
    }
    # Always auto-advance (informational only)
```

---

## 2.3 Recalibration (Stage 5 — Before Gap Analysis)

### File: `server/services/agent_os_recalibration.py` (NEW)

**Class**: `AgentOSRecalibration`

**Purpose**: Review the assembled picture as a whole. Identify and resolve
contradictions BEFORE gap analysis. This prevents contradictions from being
surfaced as "gaps" (wrong classification).

```python
class AgentOSRecalibration:
    """Review assembled context, find contradictions, resolve before gaps."""

    def __init__(self, project_dir: Path, provenance: ProvenanceTracker):
        self.project_dir = project_dir
        self.provenance = provenance
        self.contradictions: list[dict] = []
        self.resolutions: list[dict] = []

    def get_recalibration_prompt(
        self,
        entities: dict,
        standards_summary: str,
        product_summary: str,
        features: list[dict],
        refinements: list[dict],
    ) -> str:
        """Generate prompt for holistic review.

        Claude receives ALL accumulated context and looks for:
        1. Direct contradictions (A says X, B says not-X)
        2. Implicit contradictions (A implies X, B implies not-X)
        3. Scope inconsistencies (feature claims vs constraints)
        4. Priority conflicts (must-have vs nice-to-have on same thing)
        5. Technical impossibilities (requirements that can't coexist)
        """
        ...

    def process_recalibration(self, recalibration_json: dict) -> dict:
        """Process recalibration results.

        Returns:
        {
            "contradictions": [...],  # Items that conflict
            "auto_resolvable": [...], # System can resolve (confidence > 85%)
            "needs_user": [...],      # User must decide
            "coherence_score": 0.82,  # 0-1, how internally consistent
            "summary": "Found 3 contradictions, 2 auto-resolved, 1 needs input"
        }
        """
        ...

    def resolve_contradiction(self, contradiction_id: int, resolution: str) -> dict:
        """User resolves a contradiction. Updates all affected items."""
        ...

    def auto_resolve(self) -> list[dict]:
        """Auto-resolve high-confidence contradictions."""
        ...

    def get_calibrated_context(self) -> str:
        """Return cleaned context with contradictions resolved."""
        ...
```

### Contradiction Schema

```json
{
  "contradictions": [
    {
      "id": 1,
      "type": "direct",
      "statement_a": {
        "text": "No external dependencies",
        "source": "intake:constraints",
        "provenance": "USER"
      },
      "statement_b": {
        "text": "Use Stripe for payments",
        "source": "product:use-cases",
        "provenance": "USER"
      },
      "severity": "blocking",
      "auto_resolvable": false,
      "suggested_resolution": "Stripe is an external dependency. Clarify: does 'no external dependencies' mean no frontend frameworks, or literally no third-party services?",
      "resolution_options": [
        "Stripe is acceptable (constraint means no frontend frameworks)",
        "Implement custom payment processing (no Stripe)",
        "Use Stripe but wrap it for easy replacement"
      ]
    }
  ]
}
```

### Session Integration

```python
async def _handle_recalibration(self, message: str):
    """Stage 5: Recalibration (before gap analysis)."""
    prompt = self.recalibration.get_recalibration_prompt(
        entities=self.intake.entities,
        standards_summary=self.standards.get_standards_summary(),
        product_summary=self.product.get_product_summary(),
        features=self.features.get_feature_list(),
        refinements=self.refinement.refinements if hasattr(self, 'refinement') else [],
    )
    result = await self.orchestrator.execute(prompt, stage_name="recalibration")
    recalibration = self.recalibration.process_recalibration(result)

    # Auto-resolve what we can
    auto_resolved = self.recalibration.auto_resolve()

    if recalibration["needs_user"]:
        yield {
            "type": "recalibration_review",
            "contradictions": recalibration["needs_user"],
            "auto_resolved": auto_resolved,
            "coherence_score": recalibration["coherence_score"],
        }
        # Wait for user resolution...
    else:
        yield {
            "type": "message",
            "content": f"Recalibration complete. Coherence: {recalibration['coherence_score']:.0%}. "
                       f"{len(auto_resolved)} items auto-resolved."
        }
```

---

## Phase 2 Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | Technical Refinement service | `server/services/agent_os_refinement.py` |
| 2 | Recalibration service | `server/services/agent_os_recalibration.py` |
| 3 | Coverage methods on Features | `server/services/agent_os_features.py` (modify) |
| 4 | Session handlers for 3 new stages | `server/services/agent_os_session.py` (modify) |
| 5 | New WebSocket event types | `refinement_review`, `coverage_report`, `recalibration_review` |
| 6 | Tests | `test_agent_os_refinement.py`, `test_agent_os_recalibration.py` |

**Estimated complexity**: Medium-High. Refinement and Recalibration are new LLM-powered
stages. Coverage is mostly arithmetic with one LLM call.
