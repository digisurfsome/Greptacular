# Phase 2: Product Discovery Engine

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Layer 2 Product, Stage 1 Intake, Stage 3 Product Discovery
3. `server/services/agent_os_file_utils.py` — Phase 1 output. You import this.
4. `server/services/agent_os_standards.py` — Phase 1 output. You check standards before starting.
5. `server/services/spec_chat_session.py` — Session pattern to follow for the product discovery flow.

---

## What You're Building

Two Python service modules that handle:
1. **Intake processing** — Classify raw user input, extract entities, detect gaps
2. **Product discovery** — Adaptive question flow that builds the Product layer documents

These services do NOT make Claude API calls directly. They provide the logic and data structures. The actual Claude calls happen in Phase 5 (the router's WebSocket session). What you build here is:
- The classification prompts (as string templates that Phase 5 sends to Claude)
- The entity extraction prompts
- The adaptive question flow (which question to ask next, based on what's already known)
- The document generation (turning extracted data into the 6 product markdown files)

---

## Dependencies (from Phase 1)

You import these from Phase 1:
```python
from .agent_os_file_utils import AgentOSFileUtils
from .agent_os_standards import AgentOSStandards
```

You need:
- `AgentOSFileUtils.ensure_agent_os_dirs()` — Creates `.agent/product/` directory
- `AgentOSFileUtils.write_product_file()` — Saves generated product documents
- `AgentOSFileUtils.read_standards_file()` — Checks if standards exist
- `AgentOSFileUtils.standards_exist()` — Quick check before starting discovery
- `AgentOSStandards.get_standards_summary()` — Provides standards context for discovery

---

## Files to Create

### 1. `server/services/agent_os_intake.py` (~200 lines)

The intake processing module. Classifies user input and extracts structured entities.

```python
"""
Agent OS Intake Processing
==========================

Classifies raw user input (ideas, rants, formal specs, reference docs)
and extracts structured entities (product name, target users, features,
constraints) for downstream processing.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**Data structures:**

```python
# Input classification types
INPUT_TYPES = [
    "casual_description",    # "I want to build a task app"
    "formal_spec",           # Structured PRD or spec document
    "reference_material",    # Competitor analysis, research, etc.
    "rant",                  # Stream-of-consciousness about the problem
    "mixed",                 # Combination of the above
]

# Entity types we extract
ENTITY_SCHEMA = {
    "product_name": str,           # Detected or inferred product name
    "product_description": str,    # 1-2 sentence summary
    "target_users": list[str],     # List of user types/personas
    "core_features": list[str],    # Feature ideas mentioned
    "constraints": list[str],      # Budget, timeline, tech constraints
    "tech_preferences": list[str], # Mentioned technologies
    "problem_statement": str,      # What problem this solves
    "competitive_refs": list[str], # Mentioned competitors or alternatives
}
```

**Class: `AgentOSIntake`**

Constructor:
```python
def __init__(self):
    self._classification: Optional[str] = None
    self._entities: dict[str, Any] = {}
    self._gaps: list[dict] = []
    self._raw_inputs: list[str] = []  # All inputs received so far
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_classification_prompt` | `(user_input: str) -> str` | Returns the prompt string to send to Claude for classifying the input. The prompt asks Claude to return JSON: `{"type": "casual_description", "confidence": 0.85, "reasoning": "..."}`. The caller (Phase 5 router) sends this to Claude and passes the result back via `process_classification()`. |
| `process_classification` | `(classification_json: dict) -> None` | Stores the classification result from Claude. Updates `self._classification`. |
| `get_extraction_prompt` | `(user_input: str) -> str` | Returns the prompt string to send to Claude for entity extraction. The prompt asks Claude to return JSON matching `ENTITY_SCHEMA`. The caller sends this to Claude and passes back via `process_extraction()`. |
| `process_extraction` | `(entities_json: dict) -> None` | Stores extracted entities. Merges with any previously extracted entities (for multi-input scenarios). Updates `self._entities`. |
| `detect_gaps` | `() -> list[dict]` | Analyzes `self._entities` for gaps. Returns list of gap dicts: `[{"field": "target_users", "severity": "blocking", "message": "No target users identified"}, ...]`. A gap is "blocking" if the field is essential for Product layer generation. A gap is "important" if it would improve quality. A gap is "minor" if it's nice-to-have. |
| `add_input` | `(user_input: str) -> None` | Appends to `self._raw_inputs`. Called for each chunk of user input. |
| `get_all_input` | `() -> str` | Returns all raw inputs concatenated with newlines. Used by the extraction prompt to process everything at once. |
| `get_entities` | `() -> dict[str, Any]` | Returns the current extracted entities. |
| `get_classification` | `() -> Optional[str]` | Returns the input type classification. |
| `has_minimum_input` | `() -> bool` | Returns `True` if enough entities are extracted to proceed to product discovery (at minimum: product description OR problem statement). |

**Prompt templates (embedded as constants in the module):**

```python
CLASSIFICATION_PROMPT = """Analyze the following user input and classify its type.

User input:
---
{user_input}
---

Classify as one of: casual_description, formal_spec, reference_material, rant, mixed

Return ONLY valid JSON:
{{"type": "<classification>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}}
"""

EXTRACTION_PROMPT = """Extract structured entities from the following user input about a software project.

User input:
---
{user_input}
---

Extract as many of these fields as you can find (leave empty array [] or empty string "" for fields not mentioned):

Return ONLY valid JSON:
{{
  "product_name": "<name or empty string if not mentioned>",
  "product_description": "<1-2 sentence summary>",
  "target_users": ["<user type 1>", "<user type 2>"],
  "core_features": ["<feature idea 1>", "<feature idea 2>"],
  "constraints": ["<constraint 1>", "<constraint 2>"],
  "tech_preferences": ["<technology 1>", "<technology 2>"],
  "problem_statement": "<what problem this solves>",
  "competitive_refs": ["<competitor or alternative 1>"]
}}
"""
```

---

### 2. `server/services/agent_os_product.py` (~250 lines)

The product discovery question flow and document generator.

```python
"""
Agent OS Product Discovery
===========================

Adaptive question flow that builds the Product layer from user input.
Generates the 6 product documents (vision, target-users, use-cases,
roadmap, constraints, competitive-context).
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
```

**The Question Flow Data Structure:**

```python
PRODUCT_QUESTIONS: list[dict] = [
    {
        "id": "vision",
        "question": "In one sentence, what does this product do for the user?",
        "purpose": "Forces clarity on the core value proposition",
        "maps_to_file": "vision.md",
        "maps_to_section": "Core Purpose",
        "skip_if_entity": "product_description",  # Skip if intake already extracted this
        "required": True,
    },
    {
        "id": "target_users",
        "question": "Who specifically uses this? Give me a real person or role.",
        "purpose": "Prevents vague 'everyone' answers",
        "maps_to_file": "target-users.md",
        "maps_to_section": "Primary Users",
        "skip_if_entity": "target_users",
        "required": True,
    },
    {
        "id": "core_problem",
        "question": "What's the #1 pain point this solves?",
        "purpose": "Forces prioritization of the core problem",
        "maps_to_file": "vision.md",
        "maps_to_section": "Problem Statement",
        "skip_if_entity": "problem_statement",
        "required": True,
    },
    {
        "id": "competitive_context",
        "question": "What do people use today instead? What's wrong with it?",
        "purpose": "Establishes differentiation",
        "maps_to_file": "competitive-context.md",
        "maps_to_section": "Current Alternatives",
        "skip_if_entity": "competitive_refs",
        "required": False,
    },
    {
        "id": "constraints",
        "question": "Any hard constraints? Budget, timeline, technology, regulatory?",
        "purpose": "Prevents impossible specs",
        "maps_to_file": "constraints.md",
        "maps_to_section": "Hard Constraints",
        "skip_if_entity": "constraints",
        "required": False,
    },
    {
        "id": "success_definition",
        "question": "If this works perfectly, what happens? What does success look like?",
        "purpose": "Establishes acceptance criteria at the product level",
        "maps_to_file": "vision.md",
        "maps_to_section": "Success Definition",
        "skip_if_entity": None,  # Always ask — no intake entity maps to this
        "required": True,
    },
]
```

**Class: `AgentOSProduct`**

Constructor:
```python
def __init__(self, project_dir: Path, file_utils: "AgentOSFileUtils", entities: dict[str, Any]):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.entities = entities  # From AgentOSIntake.get_entities()
    self._answers: dict[str, str] = {}
    self._generated_files: list[str] = []
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `get_next_question` | `() -> Optional[dict]` | Returns the next unanswered question, skipping questions where `skip_if_entity` matches a non-empty entity from intake. Returns `None` when all questions are answered or skipped. Returns the question dict without internal keys (just `id`, `question`, `purpose`). |
| `process_answer` | `(question_id: str, answer: str) -> dict` | Stores the answer. Returns `{"stored": True, "remaining": N}`. |
| `auto_fill_from_entities` | `() -> dict[str, str]` | For each question where `skip_if_entity` matches a non-empty entity, auto-fills the answer from the entity. Returns the auto-filled answers: `{"vision": "extracted product description...", ...}`. The caller can present these to the user for confirmation. |
| `get_summary_prompt` | `() -> str` | Returns a prompt to send to Claude that produces a "here's what I understand so far" summary. Includes all answers + entities so far. Used after every 3 questions. |
| `process_summary` | `(summary: str) -> None` | Stores the summary for reference. |
| `generate_product_docs` | `() -> list[Path]` | Generates all 6 product markdown files from accumulated answers + entities. Calls `self.file_utils.write_product_file()` for each. Returns list of paths written. |
| `get_doc_generation_prompt` | `(doc_name: str) -> str` | Returns a prompt to send to Claude that generates the content for one product document. Includes all context (entities, answers, summary). `doc_name` is one of: "vision", "target-users", "use-cases", "roadmap", "constraints", "competitive-context". |
| `process_generated_doc` | `(doc_name: str, content: str) -> Path` | Takes Claude's generated content and writes it to the product file. Returns path. |
| `get_product_summary` | `() -> str` | Returns a text summary of the current product layer state. Used by Phase 3 for feature extraction. |
| `get_progress` | `() -> dict` | Returns `{"total_questions": N, "answered": M, "auto_filled": K, "remaining": R}`. |

**Document generation templates (used by `generate_product_docs`):**

Each product file follows this pattern:
```markdown
# [Document Title]
Generated: [timestamp]
Project: [product_name]

## [Section from question mapping]
[Answer content or generated content]

## [Additional sections derived from entities and answers]
...
```

The 6 product files to generate:

| File | Sections | Sources |
|------|----------|---------|
| `vision.md` | Core Purpose, Problem Statement, Success Definition | vision answer, core_problem answer, success_definition answer, product_description entity |
| `target-users.md` | Primary Users, User Needs, User Context | target_users answer, target_users entity |
| `use-cases.md` | Core Use Cases, Secondary Use Cases | Derived from features + target users (Claude-generated) |
| `roadmap.md` | MVP Features, v1.1 Features, Future | Derived from core_features entity + priority assessment (Claude-generated) |
| `constraints.md` | Hard Constraints, Technical Constraints, Timeline | constraints answer, constraints entity, tech_preferences entity |
| `competitive-context.md` | Current Alternatives, Differentiators, Opportunities | competitive_context answer, competitive_refs entity |

---

### 3. Product Markdown Templates

Create these 6 empty template files at `server/templates/agent-os/product/`:

**`vision.md`:**
```markdown
# Product Vision

## Core Purpose
[Not yet defined]

## Problem Statement
[Not yet defined]

## Success Definition
[Not yet defined]
```

**`target-users.md`:**
```markdown
# Target Users

## Primary Users
[Not yet defined]

## User Needs
[Not yet defined]

## User Context
[Not yet defined]
```

**`use-cases.md`:**
```markdown
# Use Cases

## Core Use Cases
[Not yet defined]

## Secondary Use Cases
[Not yet defined]
```

**`roadmap.md`:**
```markdown
# Roadmap

## MVP Features
[Not yet defined]

## v1.1 Features
[Not yet defined]

## Future
[Not yet defined]
```

**`constraints.md`:**
```markdown
# Constraints

## Hard Constraints
[Not yet defined]

## Technical Constraints
[Not yet defined]

## Timeline
[Not yet defined]
```

**`competitive-context.md`:**
```markdown
# Competitive Context

## Current Alternatives
[Not yet defined]

## Differentiators
[Not yet defined]

## Opportunities
[Not yet defined]
```

---

### 4. Unit Tests: `test_agent_os_phase2.py` (~100 lines)

Place at project root.

Tests to write:

```python
import pytest
from pathlib import Path

# Test AgentOSIntake
class TestIntake:
    def test_classification_prompt_includes_input(self):
        """get_classification_prompt() includes the user input in the prompt."""

    def test_process_classification_stores_type(self):
        """process_classification() stores the classification."""

    def test_extraction_prompt_includes_input(self):
        """get_extraction_prompt() includes the user input in the prompt."""

    def test_process_extraction_stores_entities(self):
        """process_extraction() stores all entity fields."""

    def test_process_extraction_merges_multiple(self):
        """Multiple calls to process_extraction() merge entities (append lists, overwrite strings)."""

    def test_detect_gaps_finds_missing_required(self):
        """detect_gaps() identifies blocking gaps for missing required fields."""

    def test_has_minimum_input_false_when_empty(self):
        """has_minimum_input() returns False with no entities."""

    def test_has_minimum_input_true_with_description(self):
        """has_minimum_input() returns True with product_description."""

    def test_add_input_concatenates(self):
        """Multiple add_input() calls are concatenated by get_all_input()."""


# Test AgentOSProduct
class TestProduct:
    def test_get_next_question_returns_first(self, tmp_path):
        """First call returns the first question."""

    def test_skip_if_entity_skips_answered(self, tmp_path):
        """Questions are skipped when their entity is already extracted."""

    def test_auto_fill_from_entities(self, tmp_path):
        """auto_fill_from_entities() fills answers from extracted entities."""

    def test_process_answer_stores(self, tmp_path):
        """process_answer() stores the answer and decrements remaining."""

    def test_generate_product_docs_creates_files(self, tmp_path):
        """generate_product_docs() creates all 6 files in .agent/product/."""

    def test_get_progress_accurate(self, tmp_path):
        """Progress reflects answered, auto-filled, and remaining counts."""

    def test_get_product_summary_non_empty(self, tmp_path):
        """get_product_summary() returns non-empty string after answers provided."""
```

---

## Completion Criteria

Phase 2 is DONE when:
- [ ] `server/services/agent_os_intake.py` exists with all methods implemented
- [ ] `server/services/agent_os_product.py` exists with all methods implemented
- [ ] All 6 product templates exist at `server/templates/agent-os/product/`
- [ ] `test_agent_os_phase2.py` exists and all tests pass
- [ ] Code passes `ruff check` and `mypy` (with `--ignore-missing-imports`)
- [ ] Imports from Phase 1 (`agent_os_file_utils`, `agent_os_standards`) resolve correctly

---

## What Phase 3 Expects from You

Phase 3 will import:
```python
from server.services.agent_os_intake import AgentOSIntake
from server.services.agent_os_product import AgentOSProduct
```

Phase 3 specifically needs:
- `AgentOSIntake.get_entities()` — To get extracted entities for feature derivation
- `AgentOSProduct.get_product_summary()` — To get product context for gap analysis
- The product files written to `.agent/product/` — Phase 3 reads these to extract features
- The entity schema structure — Phase 3's feature extraction maps entity `core_features` to the feature list

---

*End of Phase 2 PRD.*
