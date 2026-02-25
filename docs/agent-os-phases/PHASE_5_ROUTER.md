# Phase 5: Router & WebSocket Integration

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Interactive PRD Creation Workflow (Stages 1-8), UI Components section
3. All Phase 1-4 service files (the services you're exposing):
   - `server/services/agent_os_file_utils.py`
   - `server/services/agent_os_standards.py`
   - `server/services/agent_os_intake.py`
   - `server/services/agent_os_product.py`
   - `server/services/agent_os_features.py`
   - `server/services/agent_os_mechanism.py`
   - `server/services/agent_os_specs.py`
   - `server/services/agent_os_handoff.py`
4. `server/routers/spec_creation.py` — **CRITICAL.** This is the WebSocket + REST pattern you follow.
5. `server/routers/dunkstack.py` — Additional REST pattern reference.
6. `server/services/spec_chat_session.py` — Chat session management pattern.
7. `server/main.py` — Where you register the new router.
8. `server/routers/__init__.py` — Where you export the new router.

---

## What You're Building

One router file and one WebSocket session manager that:
1. **REST endpoints** — CRUD for standards, product docs, specs, features, gaps, handoff
2. **WebSocket endpoint** — The interactive PRD creation workflow (Stages 1-8 as a real-time conversation)
3. **Session management** — Track active Agent OS sessions per project

This is the hub that connects the UI (Phase 6) to all backend logic (Phases 1-4). Every Phase 1-4 service gets exposed through this router.

---

## Dependencies

All Phase 1-4 services:
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

Existing utilities:
```python
from ..utils.project_helpers import get_project_path
from ..utils.validation import is_valid_project_name
```

---

## Files to Create

### 1. `server/services/agent_os_session.py` (~150 lines)

The WebSocket session manager for the interactive Agent OS workflow.

```python
"""
Agent OS Session Manager
=========================

Manages interactive Agent OS PRD creation sessions.
Each project has at most one active session.
Uses Claude Agent SDK for the conversational workflow.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)

# Module-level session store (same pattern as spec_chat_session.py)
_sessions: dict[str, "AgentOSSession"] = {}


def get_session(project_name: str) -> Optional["AgentOSSession"]:
    return _sessions.get(project_name)


def create_session(project_name: str, project_dir: Path) -> "AgentOSSession":
    session = AgentOSSession(project_name, project_dir)
    _sessions[project_name] = session
    return session


def list_sessions() -> list[str]:
    return list(_sessions.keys())


async def remove_session(project_name: str) -> None:
    if project_name in _sessions:
        del _sessions[project_name]
```

**Class: `AgentOSSession`**

This class orchestrates the full Stage 1-8 workflow over WebSocket. It maintains state about which stage the user is in and coordinates between all Phase 1-4 services.

```python
class AgentOSSession:
    """
    Manages one interactive Agent OS PRD creation session for a project.

    Stages:
    0. Intake Dock (handled by UI + REST, not this session)
    1. Intake — classify input, extract entities
    2. Standards Check — verify/create standards
    3. Product Discovery — adaptive question flow
    4. Feature Extraction — derive features from product
    5. Gap Analysis — cross-layer gap detection
    6. Spec Generation — generate spec per feature
    7. Database Population — populate features.db
    8. Handoff — assemble and verify handoff package
    """

    STAGES = [
        "intake", "standards", "product_discovery",
        "feature_extraction", "gap_analysis", "spec_generation",
        "database_population", "handoff"
    ]

    def __init__(self, project_name: str, project_dir: Path):
        self.project_name = project_name
        self.project_dir = project_dir
        self.created_at = datetime.now()
        self.current_stage: str = "intake"
        self.current_stage_index: int = 0
        self.messages: list[dict] = []

        # Initialize all services
        self.file_utils = AgentOSFileUtils(project_dir)
        self.file_utils.ensure_agent_os_dirs()
        self.standards = AgentOSStandards(project_dir, self.file_utils)
        self.intake = AgentOSIntake()
        self.product: Optional[AgentOSProduct] = None  # Created after intake
        self.features: Optional[AgentOSFeatures] = None  # Created after product
        self.mechanism: Optional[AgentOSMechanism] = None
        self.specs: Optional[AgentOSSpecs] = None
        self.handoff: Optional[AgentOSHandoff] = None

        self.complete: bool = False
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `process_message` | `(message: str) -> AsyncGenerator[dict, None]` | The main message handler. Takes user input and yields response events. Routes to the appropriate stage handler. Yields dicts like: `{"type": "message", "content": "..."}`, `{"type": "question", "question": {...}}`, `{"type": "stage_change", "stage": "...", "index": N}`, `{"type": "progress", "stage": "...", "progress": {...}}`, `{"type": "complete", "handoff": {...}}`. |
| `advance_stage` | `() -> str` | Moves to the next stage. Returns the new stage name. |
| `get_stage` | `() -> str` | Returns the current stage name. |
| `get_progress` | `() -> dict` | Returns overall progress: `{"current_stage": "...", "stage_index": N, "total_stages": 8, "stage_progress": {...}}`. |
| `is_complete` | `() -> bool` | Returns True after handoff is assembled. |
| `get_messages` | `() -> list[dict]` | Returns conversation history. |

**Stage handler pattern:**

Each stage has a handler method that `process_message` dispatches to:

```python
async def _handle_intake(self, message: str) -> AsyncGenerator[dict, None]:
    """Stage 1: Process user input, classify, extract entities."""
    self.intake.add_input(message)

    # Send classification prompt to Claude
    prompt = self.intake.get_classification_prompt(message)
    # ... send to Claude, get response ...
    # self.intake.process_classification(response)

    # Send extraction prompt
    prompt = self.intake.get_extraction_prompt(self.intake.get_all_input())
    # ... send to Claude, get response ...
    # self.intake.process_extraction(response)

    # Check if we have enough to proceed
    if self.intake.has_minimum_input():
        gaps = self.intake.detect_gaps()
        if not any(g["severity"] == "blocking" for g in gaps):
            yield {"type": "stage_change", "stage": "standards", "index": 1}
            self.advance_stage()
        else:
            yield {"type": "message", "content": "I need a bit more info..."}
            # Ask about blocking gaps
    else:
        yield {"type": "message", "content": "Tell me more about what you want to build..."}

async def _handle_standards(self, message: str) -> AsyncGenerator[dict, None]:
    """Stage 2: Check/create standards."""
    if self.file_utils.standards_exist():
        summary = self.standards.get_standards_summary()
        yield {"type": "message", "content": f"Found existing standards. {summary}"}
        yield {"type": "stage_change", "stage": "product_discovery", "index": 2}
        self.advance_stage()
    else:
        # Ask next standards question
        question = self.standards.get_next_question()
        if question:
            if message:  # Process previous answer first
                # Find which question this answers...
                self.standards.process_answer(question["id"], message)
            next_q = self.standards.get_next_question()
            if next_q:
                yield {"type": "question", "question": next_q}
            else:
                # All questions answered, generate files
                self.standards.generate_standards_files()
                yield {"type": "stage_change", "stage": "product_discovery", "index": 2}
                self.advance_stage()

# ... similar handlers for stages 3-8 ...
```

**Claude integration pattern:**

The session uses the Claude Agent SDK for Claude-powered steps (classification, extraction, doc generation, spec generation). Follow the same pattern as `spec_chat_session.py`:

```python
async def _call_claude(self, prompt: str) -> str:
    """Send a prompt to Claude and return the response text."""
    # Use the same Claude SDK client pattern as spec_chat_session.py
    # The client is created once per session
    if not self.client:
        self.client = self._create_client()

    response = ""
    async for event in self.client.process_message(prompt):
        if hasattr(event, "text"):
            response += event.text
    return response
```

---

### 2. `server/routers/agent_os.py` (~350 lines)

The main Agent OS router with REST + WebSocket endpoints.

```python
"""
Agent OS Router
===============

REST and WebSocket endpoints for the Agent OS PRD creation system.

Provides:
- Standards CRUD (read, write, list, infer from codebase)
- Product document CRUD
- Spec document CRUD
- Feature list management
- Gap analysis trigger
- Mechanism analysis trigger
- Handoff trigger
- Interactive PRD creation WebSocket session
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..services.agent_os_session import (
    AgentOSSession,
    create_session,
    get_session,
    list_sessions,
    remove_session,
)
from ..utils.project_helpers import get_project_path
from ..utils.validation import is_valid_project_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-os", tags=["agent-os"])
```

**Pydantic Models:**

```python
class StandardsFileContent(BaseModel):
    filename: str
    content: str
    location: str = "project"  # "project" or "global"

class ProductFileContent(BaseModel):
    filename: str
    content: str

class SpecFileContent(BaseModel):
    feature_id: int
    content: str

class FeatureCreate(BaseModel):
    name: str
    description: str
    priority: str = "should_have"
    complexity: str = "medium"
    category: str = "general"
    dependencies: list[int] = []

class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[str] = None
    category: Optional[str] = None

class GapResolution(BaseModel):
    gap_id: int
    resolution: str

class SessionStatus(BaseModel):
    project_name: str
    is_active: bool
    is_complete: bool
    current_stage: str
    stage_index: int
    message_count: int
```

**REST Endpoints — organized by group:**

#### Standards Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/standards/{project_name}` | `list_standards` | List all standards files (project + global) |
| GET | `/standards/{project_name}/{filename}` | `get_standard` | Read one standards file |
| PUT | `/standards/{project_name}/{filename}` | `update_standard` | Write/update one standards file |
| POST | `/standards/{project_name}/infer` | `infer_standards` | Trigger codebase inference, return inferred answers |
| GET | `/standards/{project_name}/summary` | `get_standards_summary` | Get text summary of all standards |

#### Product Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/product/{project_name}` | `list_product_files` | List all product documents |
| GET | `/product/{project_name}/{filename}` | `get_product_file` | Read one product document |
| PUT | `/product/{project_name}/{filename}` | `update_product_file` | Write/update one product document |
| GET | `/product/{project_name}/summary` | `get_product_summary` | Get text summary of product layer |

#### Specs Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/specs/{project_name}` | `list_specs` | List all spec files |
| GET | `/specs/{project_name}/{feature_id}` | `get_spec` | Read one spec by feature ID |
| GET | `/specs/{project_name}/{feature_id}/quality` | `get_spec_quality` | Get quality report for one spec |

#### Features Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/features/{project_name}` | `list_features` | Get feature list with priorities and dependencies |
| POST | `/features/{project_name}` | `add_feature` | Manually add a feature |
| PUT | `/features/{project_name}/{feature_id}` | `update_feature` | Update a feature |
| DELETE | `/features/{project_name}/{feature_id}` | `remove_feature` | Remove a feature |

#### Gap Analysis Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/gaps/{project_name}` | `list_gaps` | Get all gaps (optionally filter by severity) |
| POST | `/gaps/{project_name}/{gap_id}/resolve` | `resolve_gap` | Resolve a gap with explanation |
| POST | `/gaps/{project_name}/auto-resolve` | `auto_resolve_gaps` | Auto-resolve all high-confidence gaps |

#### Handoff Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| POST | `/handoff/{project_name}/populate-db` | `populate_db` | Populate features.db from specs |
| POST | `/handoff/{project_name}/build-order` | `calculate_build_order` | Calculate and return build order |
| GET | `/handoff/{project_name}/status` | `get_handoff_status` | Get current handoff status |
| POST | `/handoff/{project_name}/assemble` | `assemble_handoff` | Final handoff assembly + validation |
| GET | `/handoff/{project_name}/build-plan` | `get_build_plan` | Get human-readable build plan |

#### Session Endpoints

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/sessions` | `list_agent_os_sessions` | List active sessions |
| GET | `/sessions/{project_name}` | `get_session_status` | Get session status |
| DELETE | `/sessions/{project_name}` | `cancel_session` | Cancel and remove session |

#### WebSocket Endpoint

| Path | Handler | What It Does |
|------|---------|-------------|
| `/ws/{project_name}` | `agent_os_websocket` | Interactive PRD creation session |

**WebSocket message protocol:**

Client → Server:
```json
{"type": "message", "content": "I want to build a task app"}
{"type": "answer", "question_id": "tech_frontend", "answer": "React"}
{"type": "approve", "target": "feature_list"}
{"type": "skip_stage", "stage": "standards"}
```

Server → Client:
```json
{"type": "message", "content": "Got it. Let me analyze that..."}
{"type": "question", "question": {"id": "vision", "question": "...", "type": "text"}}
{"type": "stage_change", "stage": "product_discovery", "index": 2, "total": 8}
{"type": "progress", "stage": "spec_generation", "current": 3, "total": 12}
{"type": "features", "features": [...]}
{"type": "gaps", "gaps": [...]}
{"type": "spec_preview", "feature_id": 1, "content": "..."}
{"type": "handoff_ready", "status": {...}}
{"type": "error", "message": "..."}
```

**WebSocket handler implementation:**

```python
@router.websocket("/ws/{project_name}")
async def agent_os_websocket(websocket: WebSocket, project_name: str):
    """Interactive Agent OS PRD creation session."""
    await websocket.accept()

    if not is_valid_project_name(project_name):
        await websocket.send_json({"type": "error", "message": "Invalid project name"})
        await websocket.close()
        return

    project_dir = get_project_path(project_name)
    if not project_dir:
        await websocket.send_json({"type": "error", "message": "Project not found"})
        await websocket.close()
        return

    # Get or create session
    session = get_session(project_name)
    if not session:
        session = create_session(project_name, project_dir)

    # Send initial state
    await websocket.send_json({
        "type": "stage_change",
        "stage": session.get_stage(),
        "index": session.current_stage_index,
        "total": len(session.STAGES),
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                async for event in session.process_message(data.get("content", "")):
                    await websocket.send_json(event)

            elif msg_type == "answer":
                # Process a questionnaire answer
                async for event in session.process_message(data.get("answer", "")):
                    await websocket.send_json(event)

            elif msg_type == "approve":
                # Approve current stage output and advance
                async for event in session.process_message("__approve__"):
                    await websocket.send_json(event)

            elif msg_type == "skip_stage":
                session.advance_stage()
                await websocket.send_json({
                    "type": "stage_change",
                    "stage": session.get_stage(),
                    "index": session.current_stage_index,
                    "total": len(session.STAGES),
                })

    except WebSocketDisconnect:
        logger.info(f"Agent OS WebSocket disconnected for {project_name}")
    except Exception as e:
        logger.error(f"Agent OS WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
```

---

### 3. Router Registration

**Modify `server/routers/__init__.py`** — Add:
```python
from .agent_os import router as agent_os_router
```

**Modify `server/main.py`** — Add to the imports and router includes:
```python
from .routers import agent_os_router
# ...
app.include_router(agent_os_router)
```

These are the ONLY modifications to existing files. Everything else is new files.

---

### 4. Integration Tests: `test_agent_os_phase5.py` (~100 lines)

Place at project root.

```python
import pytest
from fastapi.testclient import TestClient

# Test REST endpoints
class TestAgentOSRouter:
    def test_list_standards_empty(self, client):
        """Empty project returns empty standards list."""

    def test_list_sessions_empty(self, client):
        """No sessions returns empty list."""

    def test_get_session_not_found(self, client):
        """Unknown project returns 404."""

    def test_list_features_empty(self, client):
        """No features returns empty list."""

    def test_add_feature(self, client):
        """POST feature creates and returns it with ID."""

    def test_get_handoff_status_initial(self, client):
        """Initial handoff status shows nothing populated."""

    def test_invalid_project_name_rejected(self, client):
        """Invalid project names return 400."""


# Test WebSocket (basic connection)
class TestAgentOSWebSocket:
    def test_connect_and_receive_stage(self, client):
        """WebSocket connects and receives initial stage_change event."""

    def test_send_message_receives_response(self, client):
        """Sending a message yields at least one response event."""
```

Note: WebSocket tests use FastAPI's `TestClient.websocket_connect()`. Study the existing test patterns in the project.

---

## Completion Criteria

Phase 5 is DONE when:
- [ ] `server/services/agent_os_session.py` exists with session management
- [ ] `server/routers/agent_os.py` exists with all REST + WebSocket endpoints
- [ ] Router is registered in `server/routers/__init__.py`
- [ ] Router is included in `server/main.py`
- [ ] `test_agent_os_phase5.py` exists and tests pass
- [ ] WebSocket endpoint connects and sends/receives JSON
- [ ] REST endpoints return correct responses for CRUD operations
- [ ] Code passes `ruff check` and `mypy` (with `--ignore-missing-imports`)
- [ ] Only `__init__.py` and `main.py` are modified in existing files — everything else is new

---

## What Phase 6 Expects from You

Phase 6 (UI) calls your endpoints via React Query hooks. Phase 6 needs:

- All REST endpoints returning JSON that matches the Pydantic models above
- The WebSocket endpoint accepting and sending the message protocol documented above
- Consistent error responses: `{"detail": "..."}` with appropriate HTTP status codes
- The `/api/agent-os` prefix on all routes (React hooks will use this prefix)

Phase 6a (Intake Dock) specifically needs:
- Standards CRUD endpoints working
- Session creation endpoint working

Phase 6b (Chat & Panels) specifically needs:
- WebSocket endpoint working for the interactive workflow
- All feature/gap/spec endpoints working for panel display
- Handoff endpoints working for the build plan view

---

*End of Phase 5 PRD.*
