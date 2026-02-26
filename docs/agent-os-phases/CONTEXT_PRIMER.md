# Agent OS — Context Primer for Build Agents

## What This Document Is

This is the mental model document. If you are a build agent about to implement one phase of Agent OS, read this BEFORE your phase PRD. This document explains how the whole system connects, why decisions were made, and what vocabulary means. Your phase PRD tells you WHAT to build. This document tells you HOW it all fits together.

---

## The Big Picture in 30 Seconds

Agent OS is the front door to DunkStack builds. It takes a human's unstructured input (ideas, rants, reference docs) and transforms it into a 3-layer structured context that build agents consume. The three layers are:

1. **Standards** — Persistent coding conventions, architecture patterns, tech stack prefs (reused across all projects)
2. **Product** — Vision, users, use cases, roadmap for one specific project
3. **Specs** — Detailed feature specifications, one per feature, with acceptance criteria

Agent OS creates these layers through an interactive workflow (Stages 1-8), then hands them off to the DunkStack build agent which implements features using the 12 base mechanisms from BASE_BUILD_PRD.md.

---

## The 12 Base Mechanisms (What They Are and Where They Live)

Agent OS runs ON TOP of these. Every phase PRD may reference them. Here's the quick reference:

| # | Mechanism | What It Does | Key File(s) |
|---|-----------|-------------|-------------|
| 1 | System Prompt Redirect | Tells agent to write to files, not chat | `.agent/system_prompt.md`, `CLAUDE.md` |
| 2 | File Structure | The `.agent/` directory tree | `index.md`, `working_memory.md`, etc. |
| 3 | Walkie-Talkie Comms | Human↔Agent communication via files | `.agent/comms/to_human.md`, `from_human.md` |
| 4 | Idle/Pause | Keeps session alive during human thinking | `.agent/comms/control.md` |
| 5 | Bridge Save | Session continuity across restarts | `.agent/bridge.md` |
| 6 | Context Gauge | Real-time token tracking | API response `input_tokens`/`output_tokens` |
| 7 | Safety System | 3-tier auto-protection (warn/handoff/stop) | `.agent/settings/config.yml` thresholds |
| 8 | Decisions Log | Why choices were made | `.agent/progress/decisions.log` |
| 9 | Scope Boundary | What's in/out of scope | `.agent/scope_boundary.md` |
| 10 | Change Tracking | Semantic diffs (what changed + why) | `.agent/progress/changes.md` |
| 11 | Analytics | Measurement system for every build session | `.agent/analytics/session_*.json` |
| 12 | Self-Optimization | Lever tuning from analytics data | `.agent/analytics/lever_registry.yml` |

---

## The Phase Dependency Chain

This is the critical section. Each phase produces output that later phases consume. If you're building Phase N, you need to know what Phase N-1 built and what Phase N+1 expects.

```
Phase 1 (Standards)       → produces: agent_os_file_utils.py, agent_os_standards.py
Phase 2 (Product)         → produces: agent_os_intake.py, agent_os_product.py
Phase 3 (Features & Gaps) → produces: agent_os_features.py, agent_os_mechanism.py
Phase 4 (Specs & DB)      → produces: agent_os_specs.py, agent_os_handoff.py
Phase 5 (Router)          → produces: server/routers/agent_os.py (consumes ALL of Phases 1-4)
Phase 6a (Intake Dock UI) → produces: IntakeDock.tsx, useAgentOS.ts (consumes Phase 5 endpoints)
Phase 6b (Chat & Panels)  → produces: AgentOSChat.tsx, StandardsPanel.tsx, etc. (consumes Phase 5 endpoints)
Phase 7 (Expand + CRE)    → produces: agent_os_expand.py, agent_os_codebase.py (consumes Phase 5 router)
```

### What Each Phase Produces → What Consumes It

**Phase 1 outputs (consumed by Phases 2, 3, 4, 5):**
- `agent_os_file_utils.py` — Functions: `read_standards_file()`, `write_standards_file()`, `read_product_file()`, `write_product_file()`, `read_spec_file()`, `write_spec_file()`, `ensure_agent_os_dirs()`, `list_files_in_layer()`. Every other phase uses these for file I/O.
- `agent_os_standards.py` — Functions: `get_standards_questions()`, `process_standards_answer()`, `infer_standards_from_codebase()`, `validate_standards()`, `get_standards_summary()`. Phase 5 (router) exposes these as endpoints. Phase 3 (gap analysis) cross-references standards.
- Standards markdown templates — The 6 empty templates at `agent-os/standards/*.md`. Phase 2 references these when checking if standards exist.

**Phase 2 outputs (consumed by Phases 3, 4, 5):**
- `agent_os_intake.py` — Functions: `classify_input()`, `extract_entities()`, `detect_gaps()`. Phase 3 uses the extracted entities to derive features. Phase 5 calls these during the WebSocket workflow.
- `agent_os_product.py` — Functions: `get_next_question()`, `process_answer()`, `generate_product_docs()`, `get_product_summary()`. Phase 3 reads the generated product docs to extract features. Phase 5 exposes the question flow as a WebSocket conversation.
- Product markdown templates — The 6 empty templates at `.agent/product/*.md`. Phase 3 reads these to extract features.

**Phase 3 outputs (consumed by Phases 4, 5):**
- `agent_os_features.py` — Functions: `extract_features_from_product()`, `run_gap_analysis()`, `rank_gaps()`, `resolve_gap()`, `get_feature_list()`. Phase 4 takes the feature list and generates specs. Phase 5 exposes gap analysis as an endpoint.
- `agent_os_mechanism.py` — Functions: `analyze_options()`, `score_option()`, `apply_developers_choice()`, `record_decision()`. Phase 4 uses this during spec generation when technical decisions arise. Phase 5 exposes mechanism analysis as an endpoint.

**Phase 4 outputs (consumed by Phases 5, 6):**
- `agent_os_specs.py` — Functions: `generate_spec()`, `validate_spec()`, `get_spec_quality_report()`. Phase 5 exposes spec generation as endpoints. Phase 6b displays spec cards in the UI.
- `agent_os_handoff.py` — Functions: `populate_features_db()`, `generate_dependency_graph()`, `generate_scope_boundary()`, `calculate_build_order()`, `assemble_handoff_package()`. Phase 5 exposes the handoff trigger as an endpoint.

**Phase 5 outputs (consumed by Phases 6a, 6b, 7):**
- `server/routers/agent_os.py` — REST endpoints for all CRUD operations + WebSocket endpoint for interactive PRD creation. Phase 6 UI components call these endpoints via React Query hooks. Phase 7 adds expand endpoints to this router.

---

## Vocabulary / Glossary

These terms have specific meanings in this system. Use them consistently.

| Term | Meaning |
|------|---------|
| **Standards** | Layer 1. Persistent coding conventions. Live at `agent-os/standards/` (project-level) or `~/.autoforge/agent-os/standards/` (global). |
| **Product** | Layer 2. Per-project vision/users/use-cases. Live at `.agent/product/`. |
| **Specs** | Layer 3. Per-feature detailed specifications. Live at `.agent/specs/`. |
| **Intake** | The initial processing stage where raw user input is classified and entities are extracted. |
| **Intake Dock** | The UI file staging area (Stage 0) where users drag-drop files and tag them before the workflow starts. |
| **Gap Analysis** | Cross-referencing Standards ↔ Product ↔ Features to find missing info, contradictions, unstated dependencies. |
| **Mechanism Analysis** | Scoring competing technical approaches (e.g., WebSocket vs SSE vs polling) against criteria. |
| **Developer's Choice** | A tiebreaker heuristic for close technical decisions. Biases toward existing patterns, simplicity, adoption, docs. |
| **Handoff** | The final stage where specs → features.db entries + dependency graph + scope boundary. Build agent starts after this. |
| **Codebase Reality Engine (CRE)** | Analyzes an existing codebase to infer Standards, Product, and Specs. For retrofitting Agent OS onto existing projects. |
| **Feature Addition Engine** | The workflow for adding new features to an existing project post-initial-PRD. |

---

## Existing Codebase Patterns (Follow These Exactly)

### Server Services Pattern

All Agent OS services live at `server/services/agent_os_*.py`. Follow the exact pattern of existing services:

```python
"""
Agent OS [Name]
===============

[Brief description of what this service does.]
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AgentOS[Name]:
    """
    [One-line description.]
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        # ... initialization
```

**Real examples to study:** `spec_chat_session.py`, `expand_chat_session.py`, `workspace_chat_session.py`

### Router Pattern

Agent OS router lives at `server/routers/agent_os.py`. Follow the DunkStack router pattern exactly:

```python
"""
Agent OS Router
===============

REST and WebSocket endpoints for Agent OS.
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-os", tags=["agent-os"])
```

**Real example to study:** `server/routers/dunkstack.py` — this is the closest analog.

### Router Registration

After creating the router, it must be registered in `server/main.py`:
```python
from .routers import agent_os_router  # Add to existing imports
app.include_router(agent_os_router)   # Add to router includes
```

And exported from `server/routers/__init__.py`.

### React Hook Pattern

Agent OS hooks live at `ui/src/hooks/useAgentOS.ts`. Follow the existing React Query hook pattern:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

// Query key factory
export const agentOSKeys = {
  all: ['agent-os'] as const,
  standards: () => [...agentOSKeys.all, 'standards'] as const,
  product: (projectName: string) => [...agentOSKeys.all, 'product', projectName] as const,
  // ...
};
```

**Real example to study:** `ui/src/hooks/useDunkStack.ts`

### UI Component Pattern

Agent OS UI components live at `ui/src/components/appbuilder/`. Follow the existing component patterns:
- Tailwind CSS v4 with neobrutalism design tokens
- React 19 with TypeScript
- `@radix-ui` for primitives (Dialog, Select, etc.)
- Import design tokens from `globals.css`

---

## File Locations (Complete Map)

### What Gets Created (by phase)

```
server/services/
├── agent_os_file_utils.py      # Phase 1
├── agent_os_standards.py       # Phase 1
├── agent_os_intake.py          # Phase 2
├── agent_os_product.py         # Phase 2
├── agent_os_features.py        # Phase 3
├── agent_os_mechanism.py       # Phase 3
├── agent_os_specs.py           # Phase 4
├── agent_os_handoff.py         # Phase 4
├── agent_os_intake_dock.py     # Phase 6a
├── agent_os_expand.py          # Phase 7
├── agent_os_codebase.py        # Phase 7

server/routers/
├── agent_os.py                 # Phase 5 (extended by Phase 6a, 7)

ui/src/hooks/
├── useAgentOS.ts               # Phase 6a

ui/src/components/appbuilder/
├── IntakeDock.tsx              # Phase 6a
├── AgentOSChat.tsx            # Phase 6b
├── StandardsPanel.tsx         # Phase 6b
├── ProductPanel.tsx           # Phase 6b
├── SpecCards.tsx              # Phase 6b
├── GapAnalysisPanel.tsx       # Phase 6b
├── ExpandPanel.tsx            # Phase 7
```

### What Already Exists (study these for patterns)

```
server/services/spec_chat_session.py     # Chat session pattern (for Phase 5 WebSocket)
server/services/expand_chat_session.py   # Expand workflow pattern (for Phase 7)
server/routers/dunkstack.py              # Router pattern (for Phase 5)
server/routers/features.py               # Features CRUD pattern (for Phase 5)
api/database.py                          # SQLAlchemy models (for Phase 4 features.db)
api/dependency_resolver.py               # Dependency logic (for Phase 4 graph)
ui/src/hooks/useDunkStack.ts             # React Query hook pattern (for Phase 6a)
ui/src/components/DependencyGraph.tsx     # Graph component (reuse in Phase 6b)
```

---

## Architectural Decisions (The WHYs)

These were deliberate choices. Don't second-guess them in your phase.

1. **Why SQLite for features.db?** — The feature MCP server (`mcp_server/feature_mcp.py`) already uses SQLite via SQLAlchemy. One query interface, no additional dependencies.

2. **Why files instead of a database for Standards/Product/Specs?** — Build agents read files via Read/Glob/Grep tools. They can't query databases. The markdown files ARE the agent's interface.

3. **Why separate services per concern?** — Each service maps to one Agent OS stage. This allows phases to be built independently and tested in isolation.

4. **Why a single router for all Agent OS endpoints?** — The DunkStack router follows this pattern. One router, multiple endpoint groups, prefixed consistently. Keeps `main.py` import list manageable.

5. **Why WebSocket for the interactive workflow?** — The PRD creation is a multi-turn conversation (intake → questions → generation → review). REST would require the client to poll. WebSocket allows server-push of questions, progress, and generated content. Same pattern as `spec_creation.py`.

6. **Why Claude-powered classification/extraction?** — The intake classifier and entity extractor are NOT regex/ML. They send the user's input to Claude with a classification prompt. This means the "logic" is a prompt, not code. The code is just the orchestration around the Claude call.

7. **Why `agent-os/standards/` at project level?** — Standards can be global (`~/.autoforge/agent-os/standards/`) OR project-local (`{project_dir}/agent-os/standards/`). Project-local overrides global. The `agent_os_file_utils.py` handles this lookup chain.

---

## Integration Points Across Phases

### Phase 1 → Phase 2 Integration

Phase 2's `agent_os_product.py` calls:
```python
from .agent_os_file_utils import read_standards_file, ensure_agent_os_dirs
from .agent_os_standards import get_standards_summary
```
The product discovery checks if standards exist before starting. If they don't, it can trigger the standards questionnaire first.

### Phase 2 → Phase 3 Integration

Phase 3's `agent_os_features.py` calls:
```python
from .agent_os_file_utils import read_product_file, read_standards_file, list_files_in_layer
from .agent_os_intake import extract_entities
```
Feature extraction reads all product documents and uses the entity extractor's output to identify implied features.

### Phase 3 → Phase 4 Integration

Phase 4's `agent_os_specs.py` calls:
```python
from .agent_os_features import get_feature_list
from .agent_os_mechanism import analyze_options, record_decision
from .agent_os_file_utils import write_spec_file, read_standards_file
```
Spec generation iterates over the feature list, generating one spec document per feature. When technical decisions arise, it uses the mechanism analysis engine.

### Phase 4 → Existing DunkStack Integration

Phase 4's `agent_os_handoff.py` calls:
```python
from api.database import Feature  # Existing SQLAlchemy model
from api.dependency_resolver import validate_dependencies  # Existing cycle detection
```
The handoff populates the EXISTING features.db schema. It does NOT create a new database schema. It writes to the same table that `mcp_server/feature_mcp.py` reads from.

### Phase 5 → All Phases Integration

Phase 5's router instantiates services from all phases:
```python
from ..services.agent_os_file_utils import AgentOSFileUtils
from ..services.agent_os_standards import AgentOSStandards
from ..services.agent_os_intake import AgentOSIntake
from ..services.agent_os_product import AgentOSProduct
from ..services.agent_os_features import AgentOSFeatures
from ..services.agent_os_mechanism import AgentOSMechanism
from ..services.agent_os_specs import AgentOSSpecs
from ..services.agent_os_handoff import AgentOSHandoff
```

---

## Config Structure

Agent OS settings live in `.agent/settings/config.yml` under the `agent_os` key:

```yaml
agent_os:
  auto_select_threshold: 85        # Auto-pick technical decisions above this confidence
  present_alternatives_gap: 15     # Show alternatives if top two are within this gap
  min_viable_score: 60             # Flag for human input if all options below this
  max_features_per_expansion: 5    # Cap on features per expand operation
  standards_location: global       # global | project
  infer_standards_from_code: true  # Analyze existing code for standards
  gap_analysis_severity: blocking  # blocking | all

mechanism_analysis:
  auto_select_threshold: 85
  present_alternatives_gap: 15
  min_viable_score: 60
  max_options_to_evaluate: 4

developers_choice:
  enabled: true
  bias_toward_standards: 0.3
  bias_toward_simplicity: 0.2
  bias_toward_adoption: 0.2
  bias_toward_docs: 0.1
```

---

## Testing Strategy

Each phase includes unit tests. The pattern:

```python
# test_agent_os_[phase_name].py at project root

import pytest
from pathlib import Path
from server.services.agent_os_file_utils import AgentOSFileUtils

@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory for testing."""
    return tmp_path

def test_ensure_dirs_creates_structure(tmp_project):
    utils = AgentOSFileUtils(tmp_project)
    utils.ensure_agent_os_dirs()
    assert (tmp_project / "agent-os" / "standards").is_dir()
    assert (tmp_project / ".agent" / "product").is_dir()
    assert (tmp_project / ".agent" / "specs").is_dir()
```

Tests go at the project root following the existing pattern (`test_security.py`, `test_client.py`, etc.).

---

## What NOT to Do

1. **Don't modify existing DunkStack code** — Agent OS is additive. New files only (except registering the router in `main.py` and `__init__.py`).
2. **Don't create new database schemas** — Use the existing `Feature` model in `api/database.py`. The handoff writes to the existing `features.db`.
3. **Don't put Claude API calls in services directly** — The interactive workflow uses WebSocket → the router manages the Claude session. Services are pure logic (file I/O, data transformation, scoring). The Claude call happens at the router/session level, same as `spec_chat_session.py`.
4. **Don't add new npm dependencies without checking** — The UI already has TanStack Query, Radix UI, Tailwind v4, dagre, xterm.js. Use what's there.
5. **Don't over-engineer the questionnaire** — Adaptive questions start as if/else logic. The "AI" part is Claude processing the answers, not a complex state machine in Python.

---

*This document is the companion to the 8 phase PRDs. Read it first, then read your specific phase PRD, then build.*
