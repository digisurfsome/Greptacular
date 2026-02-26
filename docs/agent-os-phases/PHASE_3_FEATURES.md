# Phase 3: Feature Extraction & Gap Analysis

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Stage 4 Feature Extraction, Stage 5 Gap Analysis, Mechanism Analysis System, Developer's Choice System
3. `server/services/agent_os_file_utils.py` — Phase 1 output. You import this for file I/O.
4. `server/services/agent_os_intake.py` — Phase 2 output. You use entities from this.
5. `server/services/agent_os_product.py` — Phase 2 output. You read product files via this.
6. `.agent/settings/config.yml` — The mechanism_analysis and developers_choice config sections.

---

## What You're Building

Two Python service modules:
1. **Feature extraction & gap analysis** — Analyze product docs to derive features, cross-reference layers to find gaps
2. **Mechanism analysis** — Score competing technical approaches, apply Developer's Choice tiebreaker

These services produce data structures (feature lists, gap lists, scored options). They provide prompt templates for Claude-powered analysis. The actual Claude calls happen in Phase 5.

---

## Dependencies (from Phase 1 and 2)

```python
from .agent_os_file_utils import AgentOSFileUtils
from .agent_os_standards import AgentOSStandards
from .agent_os_intake import AgentOSIntake
from .agent_os_product import AgentOSProduct
```

You need:
- `AgentOSFileUtils.read_product_file()` — Read product docs for feature extraction
- `AgentOSFileUtils.read_standards_file()` — Read standards for gap cross-referencing
- `AgentOSFileUtils.list_files_in_layer()` — List what product/standards files exist
- `AgentOSStandards.get_standards_summary()` — Standards context for gap analysis
- `AgentOSIntake.get_entities()` — Extracted entities (especially `core_features`)
- `AgentOSProduct.get_product_summary()` — Product context

---

## Files to Create

### 1. `server/services/agent_os_features.py` (~300 lines)

Feature extraction from the Product layer and cross-layer gap analysis.

```python
"""
Agent OS Feature Extraction & Gap Analysis
============================================

Extracts features from the Product layer, categorizes by priority,
identifies dependencies, and runs cross-layer gap analysis between
Standards, Product, and Features.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Data structures:**

```python
# Feature priority levels
PRIORITY_LEVELS = ["must_have", "should_have", "nice_to_have"]

# Feature complexity estimates
COMPLEXITY_LEVELS = ["small", "medium", "large"]

# Gap severity levels
GAP_SEVERITIES = ["blocking", "important", "minor"]

# A single feature as extracted
FeatureDict = dict  # TypedDict would be ideal but dict for simplicity
# {
#     "id": int,
#     "name": str,
#     "description": str,
#     "priority": str,            # must_have | should_have | nice_to_have
#     "complexity": str,          # small | medium | large
#     "category": str,            # e.g., "auth", "ui", "data", "api"
#     "dependencies": list[int],  # IDs of features this depends on
#     "source": str,              # Where this feature was derived from
# }

# A single gap
GapDict = dict
# {
#     "id": int,
#     "type": str,         # missing_detail | contradiction | unstated_dep | standards_conflict | scope_creep
#     "severity": str,     # blocking | important | minor
#     "message": str,      # Human-readable description
#     "layers": list[str], # Which layers are involved: ["standards", "product", "features"]
#     "recommendation": str,            # What to do about it
#     "confidence": float,              # 0.0-1.0 confidence in the recommendation
#     "auto_fillable": bool,            # True if confidence > threshold (from config)
#     "resolved": bool,                 # Whether the gap has been resolved
#     "resolution": Optional[str],      # How it was resolved
# }
```

**Class: `AgentOSFeatures`**

Constructor:
```python
def __init__(
    self,
    project_dir: Path,
    file_utils: "AgentOSFileUtils",
    entities: dict[str, Any],
    config: dict[str, Any],
):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.entities = entities
    self.config = config  # The agent_os section of config.yml
    self._features: list[dict] = []
    self._gaps: list[dict] = []
    self._next_feature_id: int = 1
    self._next_gap_id: int = 1
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_feature_extraction_prompt` | `() -> str` | Returns a prompt to send to Claude for feature extraction. Includes: all product file contents, extracted entities, standards summary. Asks Claude to return JSON array of features matching `FeatureDict` schema (without id — those are assigned by `process_extracted_features`). |
| `process_extracted_features` | `(features_json: list[dict]) -> list[dict]` | Takes Claude's extracted features, assigns IDs, validates structure, stores in `self._features`. Returns the processed feature list. |
| `add_feature` | `(feature: dict) -> dict` | Manually add a feature (from user). Assigns ID, stores, returns. |
| `remove_feature` | `(feature_id: int) -> bool` | Remove a feature by ID. Also removes it from any other feature's dependencies. Returns success. |
| `update_feature` | `(feature_id: int, updates: dict) -> Optional[dict]` | Update a feature's fields (priority, description, etc.). Returns updated feature or `None`. |
| `get_feature_list` | `() -> list[dict]` | Returns the current feature list, sorted by priority (must_have first) then by ID. |
| `get_feature_by_id` | `(feature_id: int) -> Optional[dict]` | Returns a single feature by ID. |
| `get_gap_analysis_prompt` | `() -> str` | Returns a prompt for Claude to run gap analysis. Includes: standards summary, product summary, feature list. Asks Claude to identify gaps matching `GapDict` schema. Instructs Claude to check for: missing technical details, contradictions, unstated dependencies, standards conflicts, scope creep signals. |
| `process_gap_analysis` | `(gaps_json: list[dict]) -> list[dict]` | Takes Claude's gap analysis output, assigns IDs, applies config thresholds (auto_fillable if confidence > `auto_select_threshold`). Stores in `self._gaps`. Returns processed gaps. |
| `get_blocking_gaps` | `() -> list[dict]` | Returns only unresolved blocking gaps. |
| `get_all_gaps` | `() -> list[dict]` | Returns all gaps, sorted by severity (blocking first). |
| `resolve_gap` | `(gap_id: int, resolution: str) -> Optional[dict]` | Marks a gap as resolved with the given resolution text. Returns updated gap or `None`. |
| `auto_resolve_gaps` | `() -> list[dict]` | Auto-resolves all gaps where `auto_fillable` is `True`. Uses the gap's own recommendation as the resolution. Returns list of auto-resolved gaps. |
| `has_blocking_gaps` | `() -> bool` | Returns `True` if any unresolved blocking gaps exist. |
| `get_feature_count_by_priority` | `() -> dict[str, int]` | Returns `{"must_have": N, "should_have": M, "nice_to_have": K}`. |

**Prompt template for feature extraction:**

```python
FEATURE_EXTRACTION_PROMPT = """Analyze the following product context and extract a complete feature list.

## Product Context
{product_summary}

## Extracted Entities
{entities_json}

## Product Documents
{product_files_content}

## Standards Summary
{standards_summary}

For each feature, determine:
1. A clear, concise name
2. A 1-2 sentence description
3. Priority: must_have (MVP), should_have (v1.1), nice_to_have (future)
4. Complexity: small (< 1 hour agent work), medium (1-3 hours), large (3+ hours)
5. Category: auth, ui, data, api, infrastructure, integration, etc.
6. Dependencies: which other features (by name) must exist first
7. Source: which product document or entity this feature derives from

Return ONLY valid JSON array:
[
  {{
    "name": "<feature name>",
    "description": "<1-2 sentences>",
    "priority": "<must_have|should_have|nice_to_have>",
    "complexity": "<small|medium|large>",
    "category": "<category>",
    "dependencies": ["<dependency feature name>"],
    "source": "<which document/entity>"
  }}
]

Order features by build priority (must_have first, dependencies before dependents).
"""
```

**Prompt template for gap analysis:**

```python
GAP_ANALYSIS_PROMPT = """Analyze the following project context for gaps, contradictions, and missing information.

## Standards Summary
{standards_summary}

## Product Summary
{product_summary}

## Feature List
{features_json}

Check for these gap types:
1. **missing_detail** — A feature references something not fully defined
2. **contradiction** — Two pieces of context conflict with each other
3. **unstated_dep** — A feature implicitly requires something not in the feature list
4. **standards_conflict** — A feature conflicts with the defined standards
5. **scope_creep** — The feature set is overly ambitious for MVP

For each gap found, provide:
- type: one of the types above
- severity: blocking (must fix before specs), important (should fix), minor (note but don't block)
- message: clear description of the gap
- layers: which layers are involved ["standards", "product", "features"]
- recommendation: what to do about it
- confidence: 0.0-1.0 how confident you are in the recommendation

Return ONLY valid JSON array:
[
  {{
    "type": "<gap type>",
    "severity": "<blocking|important|minor>",
    "message": "<description>",
    "layers": ["<layer1>", "<layer2>"],
    "recommendation": "<what to do>",
    "confidence": <0.0-1.0>
  }}
]
"""
```

---

### 2. `server/services/agent_os_mechanism.py` (~200 lines)

Technical decision analysis and Developer's Choice tiebreaker.

```python
"""
Agent OS Mechanism Analysis
============================

Evaluates competing technical approaches for features.
Scores options against criteria and applies Developer's Choice
tiebreaker for close decisions.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Data structures:**

```python
# A technical option being evaluated
OptionDict = dict
# {
#     "name": str,           # e.g., "WebSocket"
#     "scores": dict,        # e.g., {"complexity": 0.7, "scalability": 0.9, ...}
#     "overall_score": float, # Weighted average
#     "pros": list[str],
#     "cons": list[str],
# }

# An analysis result
AnalysisDict = dict
# {
#     "decision_point": str,     # What the decision is about
#     "feature_id": Optional[int], # Which feature triggered this
#     "options": list[OptionDict],
#     "recommended": str,          # Name of recommended option
#     "confidence": float,         # Overall confidence
#     "auto_selected": bool,       # True if above auto_select_threshold
#     "reasoning": str,
#     "timestamp": str,
# }
```

**Class: `AgentOSMechanism`**

Constructor:
```python
def __init__(self, config: dict[str, Any], standards_summary: str = ""):
    self.config = config  # mechanism_analysis + developers_choice sections
    self.standards_summary = standards_summary
    self._analyses: list[dict] = []
    self._decisions: list[dict] = []
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_analysis_prompt` | `(decision_point: str, options: list[str], context: str) -> str` | Returns a prompt for Claude to analyze competing options. `decision_point` is like "Real-time update mechanism for feature #5". `options` is like ["WebSocket", "SSE", "Polling"]. `context` includes relevant feature description + standards. Asks Claude to score each option against criteria (complexity, standards_match, scalability, maintainability) and return JSON. |
| `process_analysis` | `(analysis_json: dict, feature_id: Optional[int] = None) -> dict` | Takes Claude's analysis output, applies Developer's Choice biases if scores are close, determines recommendation, checks against config thresholds. Returns `AnalysisDict`. Stores in `self._analyses`. |
| `apply_developers_choice` | `(options: list[dict]) -> list[dict]` | Applies the Developer's Choice weighted biases to option scores. Reads bias weights from `self.config["developers_choice"]`. Modifies `overall_score` for each option. Returns re-sorted options. Only applies if enabled in config AND top two options are within `present_alternatives_gap`. |
| `should_auto_select` | `(analysis: dict) -> bool` | Returns `True` if the top option's score exceeds `auto_select_threshold` from config. |
| `should_present_alternatives` | `(analysis: dict) -> bool` | Returns `True` if the gap between top two options is less than `present_alternatives_gap` from config. |
| `needs_human_input` | `(analysis: dict) -> bool` | Returns `True` if all options score below `min_viable_score` from config. |
| `record_decision` | `(analysis: dict, chosen_option: str, reason: str = "") -> dict` | Records the final decision. Returns a decision dict ready to be appended to `decisions.log`. Format matches Mechanism 8 from BASE_BUILD_PRD.md. |
| `get_decision_log_entry` | `(decision: dict) -> str` | Formats a decision as a markdown entry for `decisions.log`. |
| `get_all_analyses` | `() -> list[dict]` | Returns all analyses performed. |
| `get_all_decisions` | `() -> list[dict]` | Returns all recorded decisions. |

**Prompt template for mechanism analysis:**

```python
MECHANISM_ANALYSIS_PROMPT = """Evaluate the following technical options for this decision point.

## Decision Point
{decision_point}

## Options to Evaluate
{options_list}

## Context
{context}

## Standards
{standards_summary}

Score each option on these criteria (0.0 to 1.0):
- complexity: How simple is this to implement? (1.0 = very simple)
- standards_match: How well does it match the project's standards? (1.0 = perfect match)
- scalability: How well does it scale? (1.0 = highly scalable)
- maintainability: How easy is it to maintain long-term? (1.0 = very maintainable)

Return ONLY valid JSON:
{{
  "options": [
    {{
      "name": "<option name>",
      "scores": {{
        "complexity": <0.0-1.0>,
        "standards_match": <0.0-1.0>,
        "scalability": <0.0-1.0>,
        "maintainability": <0.0-1.0>
      }},
      "overall_score": <weighted average>,
      "pros": ["<pro 1>", "<pro 2>"],
      "cons": ["<con 1>", "<con 2>"]
    }}
  ],
  "reasoning": "<brief explanation of scoring>"
}}
"""
```

**Developer's Choice Implementation:**

The `apply_developers_choice()` method works like this:

```python
def apply_developers_choice(self, options: list[dict]) -> list[dict]:
    dc_config = self.config.get("developers_choice", {})
    if not dc_config.get("enabled", True):
        return options

    bias_standards = dc_config.get("bias_toward_standards", 0.3)
    bias_simplicity = dc_config.get("bias_toward_simplicity", 0.2)
    bias_adoption = dc_config.get("bias_toward_adoption", 0.2)
    bias_docs = dc_config.get("bias_toward_docs", 0.1)
    raw_weight = 1.0 - bias_standards - bias_simplicity - bias_adoption - bias_docs

    for option in options:
        scores = option.get("scores", {})
        adjusted = (
            scores.get("standards_match", 0.5) * bias_standards +
            scores.get("complexity", 0.5) * bias_simplicity +  # Higher complexity score = simpler
            scores.get("maintainability", 0.5) * bias_adoption +  # Proxy for adoption
            scores.get("maintainability", 0.5) * bias_docs +     # Proxy for docs quality
            option.get("overall_score", 0.5) * raw_weight
        )
        option["adjusted_score"] = adjusted

    return sorted(options, key=lambda o: o.get("adjusted_score", 0), reverse=True)
```

Note: In this initial version, `maintainability` proxies for both adoption and docs quality. A future version could add explicit scoring criteria for these. Keep it simple.

---

### 3. Unit Tests: `test_agent_os_phase3.py` (~120 lines)

Place at project root.

```python
import pytest
from pathlib import Path

# Test AgentOSFeatures
class TestFeatures:
    def test_feature_extraction_prompt_includes_context(self):
        """Prompt includes product summary, entities, and standards."""

    def test_process_extracted_features_assigns_ids(self):
        """Features get sequential IDs starting from 1."""

    def test_add_feature_manual(self):
        """Manually added features get IDs and are stored."""

    def test_remove_feature_cleans_dependencies(self):
        """Removing a feature also removes it from others' dependency lists."""

    def test_update_feature(self):
        """Updating a feature modifies only specified fields."""

    def test_get_feature_list_sorted_by_priority(self):
        """must_have features come before should_have."""

    def test_gap_analysis_prompt_includes_all_layers(self):
        """Prompt includes standards, product, and features."""

    def test_process_gap_analysis_applies_threshold(self):
        """Gaps with confidence > threshold are marked auto_fillable."""

    def test_resolve_gap(self):
        """Resolving a gap marks it resolved with resolution text."""

    def test_auto_resolve_gaps(self):
        """auto_resolve_gaps() resolves all auto_fillable gaps."""

    def test_has_blocking_gaps(self):
        """Returns True when unresolved blocking gaps exist."""

    def test_feature_count_by_priority(self):
        """Correctly counts features per priority level."""


# Test AgentOSMechanism
class TestMechanism:
    def test_analysis_prompt_includes_options(self):
        """Prompt includes all option names and context."""

    def test_process_analysis_determines_recommendation(self):
        """Highest-scoring option becomes the recommendation."""

    def test_developers_choice_adjusts_scores(self):
        """Developer's Choice modifies scores based on biases."""

    def test_developers_choice_disabled_no_change(self):
        """When disabled, scores are not modified."""

    def test_should_auto_select_above_threshold(self):
        """Returns True when top score > auto_select_threshold."""

    def test_should_present_alternatives_close_scores(self):
        """Returns True when top two are within gap threshold."""

    def test_needs_human_input_all_low(self):
        """Returns True when all options below min_viable_score."""

    def test_record_decision_format(self):
        """Decision log entry matches Mechanism 8 format."""

    def test_get_decision_log_entry_markdown(self):
        """Produces valid markdown for decisions.log."""
```

---

## Completion Criteria

Phase 3 is DONE when:
- [ ] `server/services/agent_os_features.py` exists with all methods implemented
- [ ] `server/services/agent_os_mechanism.py` exists with all methods implemented
- [ ] `test_agent_os_phase3.py` exists and all tests pass
- [ ] Code passes `ruff check` and `mypy` (with `--ignore-missing-imports`)
- [ ] Imports from Phase 1 and Phase 2 resolve correctly
- [ ] No modifications to Phase 1 or Phase 2 files

---

## What Phase 4 Expects from You

Phase 4 will import:
```python
from server.services.agent_os_features import AgentOSFeatures
from server.services.agent_os_mechanism import AgentOSMechanism
```

Phase 4 specifically needs:
- `AgentOSFeatures.get_feature_list()` — The feature list to generate specs from
- `AgentOSFeatures.get_feature_by_id()` — Individual features for spec generation
- `AgentOSFeatures.has_blocking_gaps()` — Check that all blocking gaps are resolved before spec generation
- `AgentOSMechanism.get_analysis_prompt()` — When spec generation encounters a technical decision
- `AgentOSMechanism.process_analysis()` — To process the analysis result
- `AgentOSMechanism.record_decision()` — To log the decision

---

*End of Phase 3 PRD.*
