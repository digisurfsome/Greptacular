# Phase 4: Spec Generation & Database Population

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Layer 3 Specs, Stage 6 Spec Generation, Stage 7 Database Population, Stage 8 Handoff
3. `server/services/agent_os_file_utils.py` — Phase 1 output. You use this for file I/O.
4. `server/services/agent_os_features.py` — Phase 3 output. You iterate over the feature list.
5. `server/services/agent_os_mechanism.py` — Phase 3 output. You use this for technical decisions during spec generation.
6. `api/database.py` — **CRITICAL.** This is the existing Feature model that you populate. Do NOT create a new schema.
7. `api/dependency_resolver.py` — **CRITICAL.** This is the existing cycle detection logic. Reuse it.
8. `mcp_server/feature_mcp.py` — Study how features.db is read by the build agent. Your handoff must produce data that this MCP server can consume.

---

## What You're Building

Two Python service modules:
1. **Spec generation** — Generate detailed spec documents from features, validate quality
2. **Handoff** — Populate features.db, build dependency graph, generate scope boundary, assemble handoff package

This is the critical bridge between Agent OS (the PRD creator) and DunkStack (the build engine). The specs you generate become the build agent's instructions. The features.db you populate is what the MCP server reads to track progress.

---

## Dependencies

From Phase 1:
```python
from .agent_os_file_utils import AgentOSFileUtils
```

From Phase 3:
```python
from .agent_os_features import AgentOSFeatures
from .agent_os_mechanism import AgentOSMechanism
```

From existing codebase:
```python
from api.database import Feature  # The SQLAlchemy model
from api.dependency_resolver import validate_dependencies, detect_cycles  # Cycle detection
```

**IMPORTANT:** Study `api/database.py` to understand the Feature model's fields:
- `id`, `priority`, `category`, `name`, `description`, `steps`, `passes` (status), `dependencies`

Your handoff must write data that exactly matches this schema. The MCP server (`mcp_server/feature_mcp.py`) reads from this table using these exact field names.

---

## Files to Create

### 1. `server/services/agent_os_specs.py` (~250 lines)

Spec document generation and validation.

```python
"""
Agent OS Spec Generation
=========================

Generates detailed feature specifications from the feature list.
Each spec is a self-contained markdown document that the build agent
consumes to implement one feature.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**The Spec Template:**

Every spec follows this exact format (from AGENT_OS_PRD.md Layer 3):

```python
SPEC_TEMPLATE = """# Feature {id}: {name}

## Overview
{overview}

## Requirements
### Functional
{functional_requirements}

### Technical
{technical_requirements}

## User Stories
{user_stories}

## Acceptance Criteria
{acceptance_criteria}

## Technical Specification
- **API Endpoints:** {api_endpoints}
- **Data Models:** {data_models}
- **Components:** {components}
- **Dependencies:** {dependencies}
- **Edge Cases:** {edge_cases}

## Standards References
{standards_references}

## Success Metrics
{success_metrics}
"""
```

**Class: `AgentOSSpecs`**

Constructor:
```python
def __init__(
    self,
    project_dir: Path,
    file_utils: "AgentOSFileUtils",
    features: "AgentOSFeatures",
    mechanism: "AgentOSMechanism",
    standards_summary: str = "",
    product_summary: str = "",
):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.features = features
    self.mechanism = mechanism
    self.standards_summary = standards_summary
    self.product_summary = product_summary
    self._generated_specs: dict[int, str] = {}  # feature_id -> spec file path
    self._quality_reports: dict[int, dict] = {}  # feature_id -> quality report
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_spec_generation_prompt` | `(feature: dict) -> str` | Returns a prompt for Claude to generate a complete spec for one feature. Includes: the feature dict, product summary, standards summary, list of all other features (for cross-referencing dependencies). Asks Claude to fill in every section of the spec template. |
| `process_generated_spec` | `(feature_id: int, spec_content: str) -> Path` | Takes Claude's generated spec content, writes it to `.agent/specs/feature-{id:03d}-{slug}.md` via `file_utils.write_spec_file()`. Stores the path in `self._generated_specs`. Returns path. The slug is derived from the feature name (lowercase, hyphens, max 30 chars). |
| `validate_spec` | `(feature_id: int) -> dict` | Validates a generated spec for quality. Checks: has at least 1 user story, has at least 2 acceptance criteria, lists dependencies, references at least 1 standards section, total length is reasonable (not too short < 20 lines, not too long > 200 lines). Returns `{"valid": bool, "issues": [{"severity": "...", "message": "..."}]}`. |
| `get_quality_report` | `(feature_id: int) -> dict` | Returns the quality report from validation. |
| `get_spec_content` | `(feature_id: int) -> Optional[str]` | Returns the generated spec content for a feature. |
| `get_all_specs` | `() -> dict[int, str]` | Returns all generated specs: `{feature_id: file_path}`. |
| `regenerate_spec` | `(feature_id: int, feedback: str) -> str` | Returns a prompt for Claude to regenerate a spec with user feedback. Includes the current spec content + the user's correction/addition. |
| `get_spec_filename` | `(feature_id: int, feature_name: str) -> str` | Returns the filename for a spec: `feature-{id:03d}-{slug}.md`. |

**Prompt template for spec generation:**

```python
SPEC_GENERATION_PROMPT = """Generate a detailed feature specification for the following feature.

## Feature
- ID: {feature_id}
- Name: {feature_name}
- Description: {feature_description}
- Priority: {feature_priority}
- Category: {feature_category}
- Dependencies: {feature_dependencies}

## Product Context
{product_summary}

## Standards
{standards_summary}

## All Features (for cross-referencing)
{all_features_summary}

Generate a COMPLETE spec using this exact format:

# Feature {feature_id}: {feature_name}

## Overview
[1-2 sentence description]

## Requirements
### Functional
1. [User-visible behavior requirement]
2. [...]

### Technical
1. [Architecture/data model/API requirement]
2. [...]

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]

## Technical Specification
- **API Endpoints:** [Routes, methods, request/response]
- **Data Models:** [Fields, types, relationships]
- **Components:** [UI components if applicable]
- **Dependencies:** [Features that must exist first]
- **Edge Cases:** [What to handle]

## Standards References
- See [standards file] for [relevant pattern]

## Success Metrics
[How to measure if this feature works]

Return the FULL spec as markdown. Be specific enough that a build agent can implement this without asking questions.
"""
```

---

### 2. `server/services/agent_os_handoff.py` (~200 lines)

Features.db population, dependency graph, scope boundary, and handoff assembly.

```python
"""
Agent OS Handoff
=================

Bridges Agent OS output (specs + features) to DunkStack build input
(features.db + dependency graph + scope boundary). This is the critical
translation layer between the PRD system and the build system.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Class: `AgentOSHandoff`**

Constructor:
```python
def __init__(
    self,
    project_dir: Path,
    file_utils: "AgentOSFileUtils",
    features: "AgentOSFeatures",
    specs: "AgentOSSpecs",
):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.features = features
    self.specs = specs
    self._build_order: list[int] = []
    self._handoff_complete: bool = False
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `populate_features_db` | `(db_path: Optional[Path] = None) -> int` | Creates features.db entries from the feature list. `db_path` defaults to `{project_dir}/.autoforge/features.db` (the standard DunkStack location). For EACH feature from `self.features.get_feature_list()`: creates a `Feature` row with: `priority` (mapped from must_have=1, should_have=2, nice_to_have=3), `category`, `name`, `description`, `steps` (from the spec's acceptance criteria, as a text list), `passes` = "pending". Returns count of features created. **Uses SQLAlchemy and the existing Feature model from `api/database.py`.** |
| `generate_dependency_graph` | `(db_path: Optional[Path] = None) -> dict` | Reads the feature list's dependency data and creates dependency entries in features.db. Uses the existing `dependency_resolver` patterns. Before writing, calls `detect_cycles()` to verify the graph is acyclic. Returns `{"edges": N, "valid": True/False, "cycle_info": None or cycle description}`. |
| `validate_dependency_graph` | `() -> dict` | Validates the dependency graph without writing it. Returns cycle detection results. |
| `calculate_build_order` | `() -> list[int]` | Topological sort of features by dependencies. Returns list of feature IDs in build order. Uses Kahn's algorithm (already in `api/dependency_resolver.py` — reuse it). Stores in `self._build_order`. |
| `generate_scope_boundary` | `() -> Path` | Generates `.agent/scope_boundary.md` from the feature list. MVP features (must_have) go in "IN SCOPE". should_have features go in "NEXT PHASE". nice_to_have go in "FUTURE". Follows the Mechanism 9 format from BASE_BUILD_PRD.md. Returns path written. |
| `assemble_handoff_package` | `() -> dict` | The final handoff. Verifies all pieces exist: standards files, product files, spec files, features.db, scope_boundary.md. Returns a status dict: `{"ready": True/False, "missing": [...], "feature_count": N, "build_order": [...], "estimated_sessions": N}`. `estimated_sessions` = ceil(feature_count / 3) based on typical batch size. |
| `get_build_plan_summary` | `() -> str` | Returns a human-readable build plan: feature order, estimated sessions, dependency visualization. Used by the UI to show the user what the build agent will do. |
| `get_handoff_status` | `() -> dict` | Returns current handoff state: `{"features_db_populated": bool, "dependencies_set": bool, "scope_boundary_generated": bool, "build_order_calculated": bool, "handoff_complete": bool}`. |

**features.db population details:**

Study `api/database.py` to get the exact field names. The mapping from Agent OS features to features.db:

```python
# Agent OS feature dict → features.db Feature row
def _feature_to_db_row(self, feature: dict, spec_content: Optional[str] = None) -> dict:
    """Map an Agent OS feature to a features.db row."""
    # Extract acceptance criteria from spec to use as 'steps'
    steps = ""
    if spec_content:
        # Parse acceptance criteria from spec markdown
        lines = spec_content.split("\n")
        criteria = []
        in_criteria = False
        for line in lines:
            if "## Acceptance Criteria" in line:
                in_criteria = True
                continue
            if in_criteria and line.startswith("##"):
                break
            if in_criteria and line.strip().startswith("- ["):
                criteria.append(line.strip()[6:])  # Strip "- [ ] "
        steps = "\n".join(f"- {c}" for c in criteria)

    return {
        "priority": {"must_have": 1, "should_have": 2, "nice_to_have": 3}.get(
            feature["priority"], 2
        ),
        "category": feature.get("category", "general"),
        "name": feature["name"],
        "description": feature["description"],
        "steps": steps,
        "passes": "pending",
    }
```

**Scope boundary template:**

```python
SCOPE_BOUNDARY_TEMPLATE = """# Scope Boundary
Generated: {timestamp}
Project: {project_name}

## IN SCOPE — Build These (MVP)
{mvp_features}

## NEXT PHASE — Build After MVP
{next_features}

## FUTURE — Don't Build Yet
{future_features}

## Build Order
{build_order}

## QUALITY BOUNDARY
- Code must work and pass lint. That's the bar for MVP.
- Don't add tests unless the spec requires them
- Don't add documentation beyond code comments
- Don't optimize for edge cases the spec doesn't mention

## STOP SIGNALS
If you find yourself doing any of these, STOP and return to the current task:
- Adding error handling for impossible scenarios
- Refactoring code that already works
- Building a utility/helper for something used once
- Adding configuration for something that has one value
- Writing more than 3 sentences in a chat response
"""
```

---

### 3. Spec File Template

Create at `server/templates/agent-os/specs/`:

**`feature-template.md`:**
```markdown
# Feature [ID]: [Name]

## Overview
[Not yet generated]

## Requirements
### Functional
1. [Not yet defined]

### Technical
1. [Not yet defined]

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] [Not yet defined]

## Technical Specification
- **API Endpoints:** [Not yet defined]
- **Data Models:** [Not yet defined]
- **Components:** [Not yet defined]
- **Dependencies:** [Not yet defined]
- **Edge Cases:** [Not yet defined]

## Standards References
[Not yet defined]

## Success Metrics
[Not yet defined]
```

---

### 4. Unit Tests: `test_agent_os_phase4.py` (~120 lines)

Place at project root.

```python
import pytest
from pathlib import Path

# Test AgentOSSpecs
class TestSpecs:
    def test_spec_generation_prompt_includes_feature(self):
        """Prompt includes feature name, description, and context."""

    def test_process_generated_spec_writes_file(self, tmp_path):
        """Spec is written to .agent/specs/ with correct filename."""

    def test_spec_filename_format(self):
        """Filename is feature-001-name-slug.md format."""

    def test_validate_spec_catches_missing_user_stories(self, tmp_path):
        """Validation flags specs without user stories."""

    def test_validate_spec_catches_missing_acceptance_criteria(self, tmp_path):
        """Validation flags specs with fewer than 2 acceptance criteria."""

    def test_validate_spec_catches_too_short(self, tmp_path):
        """Validation flags specs shorter than 20 lines."""

    def test_regenerate_prompt_includes_feedback(self, tmp_path):
        """Regeneration prompt includes original spec and user feedback."""


# Test AgentOSHandoff
class TestHandoff:
    def test_populate_features_db_creates_rows(self, tmp_path):
        """Features are created in the database with correct fields."""

    def test_populate_features_db_maps_priority(self, tmp_path):
        """must_have=1, should_have=2, nice_to_have=3."""

    def test_generate_dependency_graph_detects_cycles(self, tmp_path):
        """Cyclic dependencies are detected and reported."""

    def test_generate_dependency_graph_valid(self, tmp_path):
        """Valid acyclic graph is accepted."""

    def test_calculate_build_order_respects_deps(self, tmp_path):
        """Build order puts dependencies before dependents."""

    def test_generate_scope_boundary(self, tmp_path):
        """Scope boundary file is created with MVP/next/future sections."""

    def test_assemble_handoff_reports_missing(self, tmp_path):
        """Handoff reports missing components."""

    def test_assemble_handoff_complete(self, tmp_path):
        """With all pieces present, handoff reports ready."""

    def test_build_plan_summary_readable(self, tmp_path):
        """Build plan summary is non-empty human-readable text."""

    def test_steps_extracted_from_spec(self, tmp_path):
        """Acceptance criteria are parsed from spec markdown into steps field."""
```

---

## Completion Criteria

Phase 4 is DONE when:
- [ ] `server/services/agent_os_specs.py` exists with all methods implemented
- [ ] `server/services/agent_os_handoff.py` exists with all methods implemented
- [ ] Spec template exists at `server/templates/agent-os/specs/feature-template.md`
- [ ] `test_agent_os_phase4.py` exists and all tests pass
- [ ] Features.db population correctly uses the existing `Feature` model from `api/database.py`
- [ ] Dependency graph uses existing `api/dependency_resolver.py` for cycle detection
- [ ] Code passes `ruff check` and `mypy` (with `--ignore-missing-imports`)
- [ ] No modifications to existing `api/database.py` or `api/dependency_resolver.py`

---

## What Phase 5 Expects from You

Phase 5 will import everything from Phases 1-4 and expose them as REST + WebSocket endpoints. Phase 5 specifically needs:

- `AgentOSSpecs.get_spec_generation_prompt()` — Called during spec generation stage
- `AgentOSSpecs.process_generated_spec()` — Stores spec after Claude generates it
- `AgentOSSpecs.validate_spec()` — Quality check before presenting to user
- `AgentOSHandoff.populate_features_db()` — Triggered by "Create Build Plan" button
- `AgentOSHandoff.generate_dependency_graph()` — Called after DB population
- `AgentOSHandoff.calculate_build_order()` — Used to display build plan
- `AgentOSHandoff.assemble_handoff_package()` — Final readiness check
- `AgentOSHandoff.get_build_plan_summary()` — Displayed to user before starting build

---

*End of Phase 4 PRD.*
