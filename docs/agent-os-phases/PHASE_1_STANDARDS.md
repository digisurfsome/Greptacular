# Phase 1: Foundation & Standards Management

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Full system PRD (focus on: Layer 1 Standards, Standards Creation Sub-Flow, Phase A)
3. `BASE_BUILD_PRD.md` — Mechanism 2 (File Structure) for the `.agent/` directory layout
4. `server/services/spec_chat_session.py` — Service class pattern to follow
5. `server/routers/dunkstack.py` — Router pattern to follow (for understanding, not to build router yet — that's Phase 5)

---

## What You're Building

Two Python service modules and markdown templates that handle:
1. **File I/O** for the 3-layer Agent OS file structure (Standards, Product, Specs)
2. **Standards creation** via interactive questionnaire logic
3. **Standards inference** from an existing codebase (scan files, detect patterns)

This is the foundation that every other phase depends on for file operations.

---

## Files to Create

### 1. `server/services/agent_os_file_utils.py` (~150 lines)

The universal file I/O layer for Agent OS. Every other Agent OS service imports this.

```python
"""
Agent OS File Utilities
=======================

File I/O for the Agent OS 3-layer context system.
Handles reading, writing, and managing files across:
- Standards layer (agent-os/standards/)
- Product layer (.agent/product/)
- Specs layer (.agent/specs/)
- Intake layer (.agent/intake/)
- Knowledge layer (.agent/knowledge/)
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
```

**Class: `AgentOSFileUtils`**

Constructor:
```python
def __init__(self, project_dir: Path, global_standards_dir: Optional[Path] = None):
    self.project_dir = project_dir
    self.global_standards_dir = global_standards_dir or Path.home() / ".autoforge" / "agent-os" / "standards"
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `ensure_agent_os_dirs` | `() -> None` | Creates the full directory tree: `agent-os/standards/`, `.agent/product/`, `.agent/specs/`, `.agent/intake/`, `.agent/knowledge/`, `.agent/progress/`, `.agent/settings/`, `.agent/comms/`, `.agent/output/`, `.agent/analytics/`, `.agent/analytics/reports/`. Uses `mkdir(parents=True, exist_ok=True)`. |
| `read_standards_file` | `(filename: str) -> Optional[str]` | Reads from project-level `agent-os/standards/{filename}`. Falls back to `self.global_standards_dir/{filename}`. Returns `None` if neither exists. |
| `write_standards_file` | `(filename: str, content: str, location: str = "project") -> Path` | Writes to `agent-os/standards/{filename}` (if location="project") or `self.global_standards_dir/{filename}` (if location="global"). Creates parent dirs. Returns the path written to. |
| `read_product_file` | `(filename: str) -> Optional[str]` | Reads from `.agent/product/{filename}`. Returns `None` if not found. |
| `write_product_file` | `(filename: str, content: str) -> Path` | Writes to `.agent/product/{filename}`. Creates parent dir. Returns path. |
| `read_spec_file` | `(filename: str) -> Optional[str]` | Reads from `.agent/specs/{filename}`. Returns `None` if not found. |
| `write_spec_file` | `(filename: str, content: str) -> Path` | Writes to `.agent/specs/{filename}`. Creates parent dir. Returns path. |
| `list_files_in_layer` | `(layer: str) -> list[dict]` | Lists all files in a layer. `layer` is one of: "standards", "product", "specs", "intake", "knowledge". Returns `[{"name": "coding-conventions.md", "path": "/abs/path/...", "size": 1234, "modified": "2026-02-25T..."}]`. For standards, lists both project-level and global files, marking which is which. |
| `read_file` | `(layer: str, filename: str) -> Optional[str]` | Generic read dispatcher. Routes to the appropriate read method based on layer. |
| `write_file` | `(layer: str, filename: str, content: str) -> Path` | Generic write dispatcher. |
| `get_layer_path` | `(layer: str) -> Path` | Returns the absolute path for a layer directory. |
| `standards_exist` | `() -> bool` | Returns `True` if ANY standards files exist (project-level or global). |
| `product_exists` | `() -> bool` | Returns `True` if ANY product files exist. |
| `specs_exist` | `() -> bool` | Returns `True` if ANY spec files exist. |

**Important:** All path operations must use `Path` objects. All reads/writes use `utf-8` encoding. All methods handle `FileNotFoundError` gracefully.

---

### 2. `server/services/agent_os_standards.py` (~200 lines)

The standards creation and management logic.

```python
"""
Agent OS Standards Management
==============================

Standards creation via questionnaire, inference from codebase,
validation, and summary generation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Class: `AgentOSStandards`**

Constructor:
```python
def __init__(self, project_dir: Path, file_utils: "AgentOSFileUtils"):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self._answers: dict[str, Any] = {}  # Accumulated questionnaire answers
```

**The Questionnaire Data Structure:**

```python
STANDARDS_QUESTIONS: list[dict] = [
    # Technology Stack
    {
        "id": "tech_languages",
        "category": "Technology Stack",
        "question": "What programming language(s) will this project use?",
        "type": "text",
        "standards_file": "technology-stack.md",
        "section": "Languages",
        "required": True,
    },
    {
        "id": "tech_frontend",
        "category": "Technology Stack",
        "question": "Frontend framework preference?",
        "type": "choice",
        "options": ["React", "Vue", "Svelte", "Next.js", "None", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Frontend",
        "skip_if": lambda answers: "frontend" not in answers.get("tech_languages", "").lower()
                                    and answers.get("tech_languages", "").lower() not in ["javascript", "typescript"],
        "required": False,
    },
    {
        "id": "tech_backend",
        "category": "Technology Stack",
        "question": "Backend framework?",
        "type": "choice",
        "options": ["Express", "FastAPI", "Django", "Rails", "None", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Backend",
        "required": False,
    },
    {
        "id": "tech_database",
        "category": "Technology Stack",
        "question": "Database?",
        "type": "choice",
        "options": ["PostgreSQL", "SQLite", "MongoDB", "MySQL", "None yet", "Other"],
        "standards_file": "technology-stack.md",
        "section": "Database",
        "required": False,
    },
    {
        "id": "tech_other",
        "category": "Technology Stack",
        "question": "Any other tools or libraries you always use?",
        "type": "text",
        "standards_file": "technology-stack.md",
        "section": "Other Tools",
        "required": False,
    },
    # Coding Style
    {
        "id": "style_guide",
        "category": "Coding Style",
        "question": "Do you follow a specific style guide?",
        "type": "choice",
        "options": ["Airbnb", "PEP 8", "Google", "Standard", "Custom", "None"],
        "standards_file": "coding-conventions.md",
        "section": "Style Guide",
        "required": False,
    },
    {
        "id": "style_components",
        "category": "Coding Style",
        "question": "Functional or class-based components?",
        "type": "choice",
        "options": ["Functional", "Class-based", "Mixed", "N/A"],
        "standards_file": "coding-conventions.md",
        "section": "Component Style",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "style_file_org",
        "category": "Coding Style",
        "question": "How do you organize files?",
        "type": "choice",
        "options": ["By feature", "By type", "Hybrid", "No preference"],
        "standards_file": "coding-conventions.md",
        "section": "File Organization",
        "required": False,
    },
    {
        "id": "style_naming",
        "category": "Coding Style",
        "question": "Naming conventions?",
        "type": "choice",
        "options": ["camelCase", "snake_case", "kebab-case for files", "Mixed by language convention"],
        "standards_file": "coding-conventions.md",
        "section": "Naming",
        "required": False,
    },
    # Quality
    {
        "id": "quality_testing",
        "category": "Quality",
        "question": "Testing requirements?",
        "type": "multi_choice",
        "options": ["Unit tests", "Integration tests", "E2E tests", "None for MVP"],
        "standards_file": "quality-standards.md",
        "section": "Testing",
        "required": False,
    },
    {
        "id": "quality_docs",
        "category": "Quality",
        "question": "Documentation requirements?",
        "type": "multi_choice",
        "options": ["JSDoc/docstrings", "Inline comments", "README per module", "None for MVP"],
        "standards_file": "quality-standards.md",
        "section": "Documentation",
        "required": False,
    },
    # UI/UX (conditional on frontend)
    {
        "id": "ui_design_system",
        "category": "UI/UX",
        "question": "Design system or component library?",
        "type": "choice",
        "options": ["Tailwind", "MUI", "Shadcn/ui", "Custom", "None"],
        "standards_file": "ui-ux-standards.md",
        "section": "Design System",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "ui_responsive",
        "category": "UI/UX",
        "question": "Mobile responsive required?",
        "type": "choice",
        "options": ["Yes", "No", "Mobile-first"],
        "standards_file": "ui-ux-standards.md",
        "section": "Responsive",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    # Architecture
    {
        "id": "arch_api_style",
        "category": "Architecture",
        "question": "API style?",
        "type": "choice",
        "options": ["REST", "GraphQL", "tRPC", "None/Not applicable"],
        "standards_file": "architecture-patterns.md",
        "section": "API Style",
        "required": False,
    },
    {
        "id": "arch_state",
        "category": "Architecture",
        "question": "State management?",
        "type": "choice",
        "options": ["Redux", "Zustand", "Context API", "None", "Other"],
        "standards_file": "architecture-patterns.md",
        "section": "State Management",
        "skip_if": lambda answers: answers.get("tech_frontend") == "None",
        "required": False,
    },
    {
        "id": "arch_auth",
        "category": "Architecture",
        "question": "Authentication pattern?",
        "type": "choice",
        "options": ["JWT", "Sessions", "OAuth", "None", "Other"],
        "standards_file": "architecture-patterns.md",
        "section": "Authentication",
        "required": False,
    },
    {
        "id": "arch_deploy",
        "category": "Architecture",
        "question": "Deployment target?",
        "type": "choice",
        "options": ["Vercel", "AWS", "Self-hosted", "Docker", "Don't know yet"],
        "standards_file": "architecture-patterns.md",
        "section": "Deployment",
        "required": False,
    },
]
```

**Note on `skip_if`:** The lambda functions above reference previous answers. When serializing questions for the API (Phase 5), the `skip_if` logic is evaluated server-side — the client never sees questions that should be skipped based on prior answers. For JSON serialization, strip the `skip_if` key.

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_next_question` | `() -> Optional[dict]` | Returns the next unanswered question that isn't skipped. Returns `None` if all questions answered. Evaluates `skip_if` lambdas against `self._answers`. Returns the question dict (without `skip_if` key — strip it for serialization). |
| `process_answer` | `(question_id: str, answer: str) -> dict` | Stores the answer in `self._answers[question_id]`. Returns `{"stored": True, "remaining": N}` where N is how many questions remain. |
| `generate_standards_files` | `() -> list[Path]` | Takes all accumulated answers and generates the 6 standards markdown files. Groups answers by `standards_file`. Renders each file using the template + filled sections. Writes via `self.file_utils.write_standards_file()`. Returns list of paths written. |
| `infer_standards_from_codebase` | `() -> dict[str, Any]` | Scans `self.project_dir` for: `package.json` (detect Node framework, deps), `requirements.txt`/`pyproject.toml` (detect Python framework, deps), `tsconfig.json` (TypeScript config), `.eslintrc*`/`ruff.toml` (linter config), file structure patterns (src/components = React, app/models = Rails/Django). Returns a dict of inferred answers in the same format as `self._answers`. Does NOT write files — the caller decides whether to accept/modify the inferences before writing. |
| `validate_standards` | `() -> list[dict]` | Checks the generated standards for internal consistency. Returns a list of issues: `[{"severity": "warning", "message": "...", "file": "..."}]`. Example issues: tech stack says React but no React in package.json; style guide says PEP 8 but project is JavaScript. |
| `get_standards_summary` | `() -> str` | Returns a brief text summary of all current standards (1-2 lines per file). Used by Phase 3 for gap analysis cross-referencing. |
| `get_progress` | `() -> dict` | Returns `{"total_questions": N, "answered": M, "skipped": K, "remaining": R, "current_category": "..."}`. |

---

### 3. Standards Markdown Templates

Create these 6 empty template files. They live at `server/templates/agent-os/standards/`. At runtime, `ensure_agent_os_dirs()` copies them to the project if standards files don't exist yet.

**`coding-conventions.md`:**
```markdown
# Coding Conventions

## Style Guide
[Not yet defined]

## Component Style
[Not yet defined]

## File Organization
[Not yet defined]

## Naming
[Not yet defined]
```

**`architecture-patterns.md`:**
```markdown
# Architecture Patterns

## API Style
[Not yet defined]

## State Management
[Not yet defined]

## Authentication
[Not yet defined]

## Deployment
[Not yet defined]
```

**`ui-ux-standards.md`:**
```markdown
# UI/UX Standards

## Design System
[Not yet defined]

## Responsive
[Not yet defined]

## Accessibility
[Not yet defined]

## Mandatory Patterns
[Not yet defined]
```

**`quality-standards.md`:**
```markdown
# Quality Standards

## Testing
[Not yet defined]

## Documentation
[Not yet defined]

## Performance
[Not yet defined]
```

**`security-requirements.md`:**
```markdown
# Security Requirements

## Authentication
[Not yet defined]

## Input Validation
[Not yet defined]

## Data Protection
[Not yet defined]
```

**`technology-stack.md`:**
```markdown
# Technology Stack

## Languages
[Not yet defined]

## Frontend
[Not yet defined]

## Backend
[Not yet defined]

## Database
[Not yet defined]

## Other Tools
[Not yet defined]
```

**Where to store templates:** Create the directory `server/templates/agent-os/standards/` and place these files there. The `AgentOSFileUtils.ensure_agent_os_dirs()` method should check whether the project's `agent-os/standards/` directory is empty, and if so, copy templates from the templates directory.

---

### 4. Unit Tests: `test_agent_os_phase1.py` (~100 lines)

Place at project root: `/home/user/Greptacular/test_agent_os_phase1.py`

Tests to write:

```python
import pytest
from pathlib import Path

# Test AgentOSFileUtils
class TestFileUtils:
    def test_ensure_dirs_creates_all_directories(self, tmp_path):
        """All expected directories are created."""

    def test_read_standards_falls_back_to_global(self, tmp_path):
        """If project standards don't exist, reads from global dir."""

    def test_write_standards_to_project(self, tmp_path):
        """Writing with location='project' goes to agent-os/standards/."""

    def test_write_standards_to_global(self, tmp_path):
        """Writing with location='global' goes to ~/.autoforge/agent-os/standards/."""

    def test_list_files_includes_both_project_and_global(self, tmp_path):
        """list_files_in_layer('standards') includes files from both locations."""

    def test_read_product_file(self, tmp_path):
        """Read/write product files at .agent/product/."""

    def test_read_spec_file(self, tmp_path):
        """Read/write spec files at .agent/specs/."""

    def test_standards_exist_false_when_empty(self, tmp_path):
        """standards_exist() returns False when no files present."""

    def test_standards_exist_true_with_files(self, tmp_path):
        """standards_exist() returns True when files present."""

# Test AgentOSStandards
class TestStandards:
    def test_get_next_question_returns_first(self, tmp_path):
        """First call returns the first question."""

    def test_process_answer_stores_and_decrements(self, tmp_path):
        """Processing an answer stores it and decrements remaining count."""

    def test_skip_logic_skips_frontend_when_no_frontend(self, tmp_path):
        """Questions with skip_if are skipped when condition is met."""

    def test_generate_standards_files_creates_all(self, tmp_path):
        """With all answers provided, all 6 standards files are created."""

    def test_infer_from_package_json(self, tmp_path):
        """Detects React, TypeScript from package.json."""

    def test_infer_from_requirements_txt(self, tmp_path):
        """Detects FastAPI, SQLAlchemy from requirements.txt."""

    def test_get_progress_accurate(self, tmp_path):
        """Progress reflects answered, skipped, and remaining counts."""
```

---

## Completion Criteria

Phase 1 is DONE when:
- [ ] `server/services/agent_os_file_utils.py` exists with all methods implemented
- [ ] `server/services/agent_os_standards.py` exists with all methods implemented
- [ ] All 6 standards templates exist at `server/templates/agent-os/standards/`
- [ ] `test_agent_os_phase1.py` exists and all tests pass
- [ ] Code passes `ruff check` and `mypy` (with `--ignore-missing-imports`)
- [ ] No modifications to any existing files (this phase is purely additive)

---

## What Phase 2 Expects from You

Phase 2 will import:
```python
from server.services.agent_os_file_utils import AgentOSFileUtils
from server.services.agent_os_standards import AgentOSStandards
```

Phase 2 specifically needs:
- `AgentOSFileUtils.ensure_agent_os_dirs()` to create the `.agent/product/` directory
- `AgentOSFileUtils.write_product_file()` to save generated product documents
- `AgentOSFileUtils.read_standards_file()` to check if standards exist before starting product discovery
- `AgentOSStandards.get_standards_summary()` to provide standards context during product discovery

Make sure these methods work correctly — Phase 2 cannot function without them.

---

*End of Phase 1 PRD.*
