# Phase 7: Feature Addition & Codebase Reality Engine

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Feature Addition Engine section, Codebase Reality Engine section
3. All Phase 1-4 service files (you build on top of these):
   - `server/services/agent_os_file_utils.py` — File I/O
   - `server/services/agent_os_features.py` — Feature management
   - `server/services/agent_os_specs.py` — Spec generation
   - `server/services/agent_os_handoff.py` — Database + dependency graph
4. `server/routers/agent_os.py` — Phase 5 router (you add endpoints to this)
5. `server/services/expand_chat_session.py` — **CRITICAL.** The existing expand workflow. Study its pattern for the feature addition engine.
6. `server/routers/expand_project.py` — Existing expand router pattern.

---

## What You're Building

Two Python service modules and one UI component:
1. **Feature Addition Engine** — Add features to existing projects, check conflicts, update deps
2. **Codebase Reality Engine (CRE)** — Scan an existing codebase, infer Standards/Product/Specs
3. **ExpandPanel UI** — Simple UI for the feature addition workflow
4. **Router additions** — Expand + CRE endpoints added to `server/routers/agent_os.py`

---

## Dependencies

From Phases 1-4:
```python
from .agent_os_file_utils import AgentOSFileUtils
from .agent_os_standards import AgentOSStandards
from .agent_os_features import AgentOSFeatures
from .agent_os_specs import AgentOSSpecs
from .agent_os_handoff import AgentOSHandoff
```

---

## Files to Create

### 1. `server/services/agent_os_expand.py` (~200 lines)

Feature addition engine for existing projects.

```python
"""
Agent OS Feature Expansion
===========================

Adds features to existing Agent OS projects. Cross-references new
features against existing ones, checks for conflicts, updates
dependency graph, and generates specs for new features.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Class: `AgentOSExpand`**

Constructor:
```python
def __init__(
    self,
    project_dir: Path,
    file_utils: "AgentOSFileUtils",
    features: "AgentOSFeatures",
    specs: "AgentOSSpecs",
    handoff: "AgentOSHandoff",
    config: dict[str, Any],
):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.features = features
    self.specs = specs
    self.handoff = handoff
    self.config = config
    self.max_features_per_expansion = config.get("max_features_per_expansion", 5)
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_expansion_prompt` | `(user_input: str) -> str` | Returns a prompt for Claude to extract new features from user's natural language input. Includes: existing feature list (so Claude doesn't duplicate), product summary, standards summary. Asks Claude to return JSON array of new features. |
| `process_expansion` | `(new_features_json: list[dict]) -> dict` | Validates new features: checks count against `max_features_per_expansion`, checks for name conflicts with existing features. Assigns IDs continuing from existing max ID. Returns `{"added": [...], "conflicts": [...], "warnings": [...]}`. |
| `get_conflict_check_prompt` | `(new_features: list[dict]) -> str` | Returns a prompt for Claude to check new features against existing: Does this conflict with anything? Does this require changes to existing specs? What existing features does this depend on? |
| `process_conflict_check` | `(conflict_json: dict) -> dict` | Processes Claude's conflict analysis. Returns `{"conflicts": [...], "required_changes": [...], "new_dependencies": [...]}`. |
| `add_features` | `(features: list[dict]) -> list[dict]` | Adds validated features via `self.features.add_feature()`. Returns the added features with IDs. |
| `generate_new_specs` | `(feature_ids: list[int]) -> list[str]` | Returns a list of spec generation prompts for each new feature. Caller sends to Claude and processes via `self.specs.process_generated_spec()`. |
| `update_dependency_graph` | `() -> dict` | Regenerates the dependency graph to include new features. Calls `self.handoff.generate_dependency_graph()`. Returns result. |
| `update_scope_boundary` | `() -> Path` | Regenerates scope boundary with new features included. Calls `self.handoff.generate_scope_boundary()`. Returns path. |
| `recalculate_build_order` | `() -> list[int]` | Recalculates build order with new features. Calls `self.handoff.calculate_build_order()`. Returns new order. |
| `get_expansion_summary` | `() -> str` | Returns human-readable summary of what was added: N new features, updated dependencies, new build order. |

**Safeguards (from AGENT_OS_PRD.md):**
- New features CANNOT modify existing specs without explicit approval
- If a new feature would require changing a BUILT feature (passes="passing"), flag it prominently
- Maximum features per expansion is enforced (default 5, configurable)
- Name conflicts are detected and reported, not silently overwritten

---

### 2. `server/services/agent_os_codebase.py` (~250 lines)

Codebase Reality Engine — scans existing code to infer Agent OS context.

```python
"""
Agent OS Codebase Reality Engine
==================================

Analyzes an existing codebase to infer Standards, Product, and Specs.
Enables retrofitting Agent OS onto projects that already have code.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Class: `AgentOSCodebaseAnalyzer`**

Constructor:
```python
def __init__(self, project_dir: Path, file_utils: "AgentOSFileUtils"):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self._analysis: dict[str, Any] = {}
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `scan_codebase` | `() -> dict` | Master scan method. Calls all detection methods below. Returns a comprehensive analysis dict with all findings. |
| `detect_tech_stack` | `() -> dict` | Scans for: `package.json` (node deps, scripts), `requirements.txt`/`pyproject.toml` (python deps), `Cargo.toml` (rust), `go.mod` (go), `Gemfile` (ruby), `pom.xml` (java). Returns `{"languages": [...], "frameworks": [...], "databases": [...], "tools": [...]}`. |
| `detect_file_structure` | `() -> dict` | Analyzes directory layout: `src/components/` = React, `app/models/` = Rails/Django, `src/routes/` = route-based framework, `tests/` or `__tests__/` = test dir. Returns `{"pattern": "by-feature|by-type|flat", "key_directories": [...], "file_count": N}`. |
| `detect_code_patterns` | `() -> dict` | Reads a sample of source files (up to 10, largest by size) and detects: naming convention (camelCase/snake_case/PascalCase), component style (functional/class), indentation (tabs/spaces, 2/4), import style (ES modules/CommonJS/Python). Returns pattern summary. |
| `detect_linter_config` | `() -> dict` | Looks for: `.eslintrc*`, `.prettierrc*`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.editorconfig`, `tsconfig.json`. Returns detected configs and their settings. |
| `detect_test_patterns` | `() -> dict` | Looks for test files (`*.test.*`, `*.spec.*`, `test_*`), test frameworks (`jest`, `pytest`, `vitest`, `playwright`), test configuration. Returns `{"framework": "...", "pattern": "...", "coverage": bool}`. |
| `get_standards_inference_prompt` | `() -> str` | Returns a prompt for Claude to generate standards files from the scan results. Includes all detection results. Asks Claude to return JSON with content for each of the 6 standards files. |
| `process_standards_inference` | `(standards_json: dict) -> list[Path]` | Takes Claude's generated standards and writes them via `file_utils.write_standards_file()`. Returns paths written. |
| `get_product_inference_prompt` | `() -> str` | Returns a prompt for Claude to infer the Product layer from README, code comments, and file analysis. Asks Claude to return JSON with content for each of the 6 product files. |
| `process_product_inference` | `(product_json: dict) -> list[Path]` | Writes inferred product files. Returns paths. |
| `get_feature_inference_prompt` | `() -> str` | Returns a prompt for Claude to reverse-engineer features from the codebase. Includes: file list, detected routes/endpoints, detected components, detected models. Asks Claude to return a feature list. |
| `process_feature_inference` | `(features_json: list[dict]) -> list[dict]` | Creates features from inferred list. All features are marked with `passes: "passing"` since they already exist in code. Returns feature list. |
| `get_analysis_summary` | `() -> str` | Human-readable summary of what was detected. |

**Detection implementation notes:**

For `detect_tech_stack`, read specific config files:
```python
def detect_tech_stack(self) -> dict:
    result = {"languages": [], "frameworks": [], "databases": [], "tools": []}

    # Node.js detection
    pkg_json = self.project_dir / "package.json"
    if pkg_json.exists():
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        result["languages"].append("JavaScript/TypeScript" if "typescript" in deps else "JavaScript")
        # Detect frameworks from deps
        framework_map = {
            "react": "React", "vue": "Vue", "svelte": "Svelte",
            "next": "Next.js", "express": "Express", "fastify": "Fastify",
            "tailwindcss": "Tailwind CSS",
        }
        for dep_name, framework_name in framework_map.items():
            if dep_name in deps:
                result["frameworks"].append(framework_name)

    # Python detection
    for req_file in ["requirements.txt", "pyproject.toml"]:
        req_path = self.project_dir / req_file
        if req_path.exists():
            content = req_path.read_text(encoding="utf-8")
            result["languages"].append("Python")
            py_frameworks = {
                "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
                "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic",
            }
            for pkg_name, fw_name in py_frameworks.items():
                if pkg_name in content.lower():
                    result["frameworks"].append(fw_name)
            break

    return result
```

For `detect_file_structure`, use `Path.rglob()` but limit depth to 3 levels and exclude `node_modules`, `.git`, `venv`, `__pycache__`, `dist`, `build`.

For `detect_code_patterns`, read up to 10 source files (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`), only first 50 lines each to detect patterns without consuming too much memory.

---

### 3. `ui/src/components/appbuilder/ExpandPanel.tsx` (~100 lines)

UI for the feature expansion workflow.

```typescript
/**
 * ExpandPanel Component
 *
 * Simple panel for adding features to an existing Agent OS project.
 * User describes new features in natural language, system analyzes
 * conflicts and generates specs.
 */
```

**Props:**
```typescript
interface ExpandPanelProps {
  projectName: string
  onExpansionComplete: () => void
}
```

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  ADD FEATURES                                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Describe the features you want to add:             │
│  ┌───────────────────────────────────────────────┐  │
│  │                                               │  │
│  │  [Multi-line textarea]                        │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
│  [Analyze & Add →]                                  │
│                                                     │
│  ──── Results ────                                  │
│                                                     │
│  ✅ Added 3 new features:                           │
│  • Feature #15: User notifications (MVP, Medium)    │
│  • Feature #16: Email templates (v1.1, Small)       │
│  • Feature #17: Push notifications (Future, Large)  │
│                                                     │
│  ⚠ Conflicts:                                      │
│  • Feature #16 may require changes to Feature #3    │
│                                                     │
│  Dependencies updated. New build order calculated.  │
│  [View Updated Build Plan]                          │
└─────────────────────────────────────────────────────┘
```

**Behavior:**
1. User types feature descriptions in textarea
2. "Analyze & Add" calls the expand endpoint
3. Results show added features, conflicts, and warnings
4. "View Updated Build Plan" links to the build plan view

Uses the `useAgentOS` hooks for API calls. Create an `useExpandFeatures` mutation hook if not already in `useAgentOS.ts`.

---

### 4. Router Additions

Add these endpoints to `server/routers/agent_os.py`:

#### Expand Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| POST | `/expand/{project_name}/analyze` | `analyze_expansion` | Takes user input, extracts and conflict-checks new features |
| POST | `/expand/{project_name}/add` | `add_expanded_features` | Adds approved features, generates specs, updates deps |
| GET | `/expand/{project_name}/summary` | `get_expansion_summary` | Get summary of last expansion |

#### CRE Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| POST | `/cre/{project_name}/scan` | `scan_codebase` | Trigger full codebase scan |
| GET | `/cre/{project_name}/analysis` | `get_analysis` | Get scan results |
| POST | `/cre/{project_name}/apply-standards` | `apply_inferred_standards` | Write inferred standards |
| POST | `/cre/{project_name}/apply-product` | `apply_inferred_product` | Write inferred product layer |
| POST | `/cre/{project_name}/apply-features` | `apply_inferred_features` | Create features from inferred list |
| GET | `/cre/{project_name}/summary` | `get_cre_summary` | Get human-readable scan summary |

**Pydantic models:**

```python
class ExpandRequest(BaseModel):
    description: str  # Natural language feature description

class ExpandResult(BaseModel):
    added: list[dict]
    conflicts: list[dict]
    warnings: list[str]
    new_build_order: list[int]
```

---

### 5. Unit Tests: `test_agent_os_phase7.py` (~100 lines)

```python
import pytest
from pathlib import Path

# Test AgentOSExpand
class TestExpand:
    def test_expansion_prompt_includes_existing_features(self):
        """Prompt includes existing feature list to prevent duplication."""

    def test_process_expansion_enforces_max(self):
        """Cannot add more than max_features_per_expansion."""

    def test_process_expansion_detects_name_conflicts(self):
        """Duplicate feature names are flagged as conflicts."""

    def test_add_features_assigns_continuing_ids(self):
        """New features get IDs continuing from existing max."""

    def test_safeguard_built_features(self):
        """Changing a feature with passes='passing' is flagged."""


# Test AgentOSCodebaseAnalyzer
class TestCodebaseAnalyzer:
    def test_detect_node_project(self, tmp_path):
        """Detects Node.js/React from package.json."""
        pkg = tmp_path / "package.json"
        pkg.write_text('{"dependencies": {"react": "^19.0.0", "typescript": "^5.0.0"}}')
        # ... assert detection

    def test_detect_python_project(self, tmp_path):
        """Detects Python/FastAPI from requirements.txt."""
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.100.0\nsqlalchemy==2.0.0\n")
        # ... assert detection

    def test_detect_file_structure_by_feature(self, tmp_path):
        """Detects feature-based file organization."""
        (tmp_path / "src" / "auth").mkdir(parents=True)
        (tmp_path / "src" / "dashboard").mkdir(parents=True)
        # ... assert pattern = "by-feature"

    def test_detect_file_structure_by_type(self, tmp_path):
        """Detects type-based file organization."""
        (tmp_path / "src" / "components").mkdir(parents=True)
        (tmp_path / "src" / "hooks").mkdir(parents=True)
        (tmp_path / "src" / "services").mkdir(parents=True)
        # ... assert pattern = "by-type"

    def test_excludes_node_modules(self, tmp_path):
        """node_modules is not included in file structure analysis."""

    def test_scan_summary_non_empty(self, tmp_path):
        """Scan summary returns non-empty text."""
```

---

## Completion Criteria

Phase 7 is DONE when:
- [ ] `server/services/agent_os_expand.py` exists with all methods
- [ ] `server/services/agent_os_codebase.py` exists with all methods
- [ ] `ui/src/components/appbuilder/ExpandPanel.tsx` exists and renders
- [ ] Expand + CRE router endpoints added to `server/routers/agent_os.py`
- [ ] `test_agent_os_phase7.py` exists and all tests pass
- [ ] CRE correctly detects Node.js and Python projects
- [ ] Expansion safeguards prevent over-adding and conflict with built features
- [ ] Code passes `ruff check`, `mypy`, `npm run lint`, `npm run build`

---

*End of Phase 7 PRD. End of all phase PRDs.*
