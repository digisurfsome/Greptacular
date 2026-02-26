# Agent OS Fix Pass — Surgical Bug Fixes

> **Purpose:** This document is the complete context primer for a fresh agent to fix 9 bugs
> in the Agent OS backend. Every fix is scoped to exact files, exact lines, and exact
> code changes. No exploration required — just read this, fix, verify.

---

## Architecture Context (Minimum Viable)

The Agent OS is a WebSocket-driven PRD creation system built on FastAPI. It has:

- **Session manager** (`server/services/agent_os_session.py`) — orchestrates an 8-stage workflow
- **Intake** (`server/services/agent_os_intake.py`) — classifies user input, extracts entities
- **Standards** (`server/services/agent_os_standards.py`) — questionnaire-driven standards creation
- **Product** (`server/services/agent_os_product.py`) — questionnaire-driven product discovery
- **Features** (`server/services/agent_os_features.py`) — feature extraction and management
- **Handoff** (`server/services/agent_os_handoff.py`) — bridges PRD output to build system
- **Agent OS Router** (`server/routers/agent_os.py`) — REST + WebSocket endpoints
- **DunkStack Router** (`server/routers/dunkstack.py`) — file-based context mechanism endpoints

The WebSocket flow: User connects → intake stage → standards stage → product discovery → feature extraction → gap analysis → spec generation → database population → handoff.

---

## Fix 1 (CRITICAL): Intake stage never extracts entities — workflow stalls at Stage 1

### Problem

`_handle_intake()` in `agent_os_session.py` calls `self.intake.add_input(message)` to accumulate text, then calls `self.intake.detect_gaps()` and `self.intake.get_entities()`. But `AgentOSIntake` only populates `_entities` when `process_extraction()` is called with Claude's JSON response. Since `_handle_intake` never calls `process_extraction()`, `get_entities()` always returns `{}` (empty dict). Empty dict is falsy, so the check `if entities and not blocking:` on line 148 is always False. Users are stuck in an infinite "Tell me more" loop.

### File & Lines

`server/services/agent_os_session.py`, lines 126-161

### Current Code (Broken)

```python
async def _handle_intake(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
    """Stage 1: Accumulate input, classify, extract entities."""
    if message == "__approve__":
        self.advance_stage()
        yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
        return

    self.intake.add_input(message)

    yield {
        "type": "message",
        "content": "Processing your input...",
    }

    # Run entity gap detection
    gaps = self.intake.detect_gaps()
    entities = self.intake.get_entities()

    blocking = [g for g in gaps if g["severity"] == "blocking"]

    if entities and not blocking:
        yield {
            "type": "message",
            "content": "I've captured your initial input. Moving to standards check.",
        }
        yield {"type": "progress", "stage": "intake", "entities": entities, "gaps": gaps}
        self.advance_stage()
        yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
    else:
        yield {
            "type": "message",
            "content": "Tell me more about what you want to build. I need at least a description of the product or the problem it solves.",
        }
        yield {"type": "progress", "stage": "intake", "entities": entities, "gaps": gaps}
```

### Fix

After `add_input(message)`, do a local keyword-based extraction from the accumulated raw text to populate entities. This doesn't require an LLM call — it uses the raw text directly. The idea: treat the concatenated user input as a minimal product description and problem statement so `detect_gaps()` has something to work with.

**In `server/services/agent_os_intake.py`**, add a new method `extract_from_raw_input()`:

```python
def extract_from_raw_input(self) -> None:
    """Populate entities from accumulated raw input text (no LLM needed).

    This is a best-effort local extraction that treats the user's raw text
    as a product description. It ensures detect_gaps() has data to work with
    so the intake stage can auto-advance when minimum info is present.
    """
    combined = self.get_all_input().strip()
    if not combined:
        return

    # Always set product_description from the raw input if not already set
    if not _is_non_empty(self._entities.get("product_description")):
        # Use first 500 chars as the product description
        self._entities["product_description"] = combined[:500]

    # Use the full text as problem_statement too if not set
    if not _is_non_empty(self._entities.get("problem_statement")):
        self._entities["problem_statement"] = combined[:500]

    logger.debug(
        "Local extraction: %d fields populated from raw input",
        sum(1 for v in self._entities.values() if _is_non_empty(v)),
    )
```

**In `server/services/agent_os_session.py`**, in `_handle_intake()`, call the new method after `add_input`:

Change:

```python
self.intake.add_input(message)

# Return classification and extraction prompts for the caller to process
yield {
    "type": "message",
    "content": "Processing your input...",
}

# Run entity gap detection
gaps = self.intake.detect_gaps()
```

To:

```python
self.intake.add_input(message)

# Extract entities from accumulated raw input (local, no LLM)
self.intake.extract_from_raw_input()

# Return classification and extraction prompts for the caller to process
yield {
    "type": "message",
    "content": "Processing your input...",
}

# Run entity gap detection
gaps = self.intake.detect_gaps()
```

### Verification

After fix, sending any non-empty message to the intake stage should:
1. Populate `_entities["product_description"]` and `_entities["problem_statement"]`
2. `detect_gaps()` should no longer report those two as "blocking"
3. The `if entities and not blocking:` check should pass
4. Stage should auto-advance to "standards"

---

## Fix 2 (HIGH): Standards & Product question off-by-one — first question answered with wrong text

### Problem

When `_handle_standards()` receives its first message (the text that triggered the stage transition), it:
1. Gets Q1 via `get_next_question()`
2. Records the incoming message as Q1's answer via `process_answer(next_q["id"], message)`
3. Gets Q2 and shows it to the user

The problem: the user has never **seen** Q1. Their intake text gets silently recorded as the answer to "What programming language(s) will this project use?" Same bug exists in `_handle_product_discovery()`.

### File & Lines

`server/services/agent_os_session.py`:
- Lines 178-193 (standards handler)
- Lines 210-223 (product discovery handler)

### Fix

Track whether the user has been shown the current question before accepting an answer. Add a `_stage_entry` flag per questionnaire stage.

**In `agent_os_session.py` `__init__`**, add tracking flags:

```python
# Track whether the user has been shown the first question in questionnaire stages
self._standards_question_shown: bool = False
self._product_question_shown: bool = False
```

**In `_handle_standards()`**, replace lines 178-186 with:

```python
# On first entry, show the first question without consuming the message as an answer
if not self._standards_question_shown:
    self._standards_question_shown = True
    next_q = self.standards.get_next_question()
    if next_q:
        yield {"type": "question", "question": next_q}
        yield {"type": "progress", "stage": "standards", **self.standards.get_progress()}
    else:
        # No questions to ask — generate files and advance
        self.standards.generate_standards_files()
        yield {"type": "message", "content": "Standards files generated."}
        self.advance_stage()
        yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
    return

# Process the answer to the previously shown question
next_q = self.standards.get_next_question()
if message and next_q:
    self.standards.process_answer(next_q["id"], message)

# Get the next question
next_q = self.standards.get_next_question()
if next_q:
    yield {"type": "question", "question": next_q}
    yield {"type": "progress", "stage": "standards", **self.standards.get_progress()}
else:
    # All questions answered — generate files
    self.standards.generate_standards_files()
    yield {"type": "message", "content": "Standards files generated."}
    self.advance_stage()
    yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
```

**In `_handle_product_discovery()`**, apply the same pattern. Replace lines 210-223 with:

```python
# On first entry, show the first question without consuming the message as an answer
if not self._product_question_shown:
    self._product_question_shown = True
    next_q = self.product.get_next_question()
    if next_q:
        yield {"type": "question", "question": next_q}
        yield {"type": "progress", "stage": "product_discovery", **self.product.get_progress()}
    else:
        self.product.generate_product_docs()
        yield {"type": "message", "content": "All product questions answered. Documents generated."}
        self.advance_stage()
        yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
    return

# Process the answer to the previously shown question
next_q = self.product.get_next_question()
if message and next_q:
    self.product.process_answer(next_q["id"], message)

next_q = self.product.get_next_question()
if next_q:
    yield {"type": "question", "question": next_q}
    yield {"type": "progress", "stage": "product_discovery", **self.product.get_progress()}
else:
    self.product.generate_product_docs()
    yield {"type": "message", "content": "All product questions answered. Documents generated."}
    self.advance_stage()
    yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
```

### Verification

After fix:
- First message to standards stage should show Q1 ("What programming language(s)...") without recording any answer
- User's reply to Q1 should be recorded as Q1's answer, then show Q2
- Same for product discovery stage

---

## Fix 3 (HIGH): REST features cache disconnected from WebSocket session features

### Problem

`_project_features` in `agent_os.py` (line 294) is a module-level dict that caches `AgentOSFeatures` instances. The WebSocket session creates its OWN `AgentOSFeatures` inside `AgentOSSession`. These two are never synchronized. Features added via WebSocket don't appear in REST endpoints, and vice versa.

### File & Lines

`server/routers/agent_os.py`, lines 293-304

### Fix

When a session exists for a project, the REST endpoints should use the session's features instance instead of creating a separate one. Modify `_get_features_service()`:

```python
def _get_features_service(project_name: str, project_dir: Path) -> AgentOSFeatures:
    """Get the features service for a project.

    Prefers the active session's features instance to stay in sync
    with the WebSocket workflow. Falls back to a standalone instance.
    """
    # If there's an active session, use its features (keeps REST and WS in sync)
    session = get_session(project_name)
    if session is not None and session.features is not None:
        return session.features

    # Fallback: standalone instance for REST-only usage
    if project_name not in _project_features:
        fu = _get_file_utils(project_dir)
        _project_features[project_name] = AgentOSFeatures(
            project_dir, fu, entities={}, config={},
        )
    return _project_features[project_name]
```

### Verification

After fix:
- Start a WebSocket session, add features through the session workflow
- Call `GET /api/agent-os/features/{project_name}` — should return the same features
- If no session exists, REST endpoints still work with standalone instance

---

## Fix 4 (HIGH): `populate_features_db` crashes on second call (duplicate primary keys)

### Problem

`populate_features_db()` in `agent_os_handoff.py` uses `session.add()` with explicit `id` values. If the table already has rows (from a previous populate call or from the standard AutoForge initializer), it raises `IntegrityError` on duplicate primary keys. The `_features_db_populated` flag is per-instance and not persisted, so a new `AgentOSHandoff` instance will try to re-populate.

### File & Lines

`server/services/agent_os_handoff.py`, lines 119-169

### Fix

Clear existing rows before inserting. Add a `DELETE FROM features` before the insert loop:

```python
def populate_features_db(self, db_path: Optional[Path] = None) -> int:
    """Create features.db entries from the feature list.

    Returns count of features created.
    Idempotent: clears existing rows before inserting.
    """
    from api.database import Base, Feature, create_database

    if db_path is not None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    else:
        _engine, SessionLocal = create_database(self.project_dir)

    feature_list = self.features.get_feature_list()
    count = 0

    session = SessionLocal()
    try:
        # Clear existing rows for idempotent re-population
        session.query(Feature).delete()
        session.flush()

        for feature in feature_list:
            row_data = self._feature_to_db_row(feature)
            db_feature = Feature(
                id=feature["id"],
                priority=row_data["priority"],
                category=row_data["category"],
                name=row_data["name"],
                description=row_data["description"],
                steps=row_data["steps"],
                passes=False,
                in_progress=False,
                dependencies=feature.get("dependencies", []) or None,
            )
            session.add(db_feature)
            count += 1

        session.commit()
        self._features_db_populated = True
        self._dependencies_set = True
        logger.info("Populated features.db with %d features", count)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return count
```

### Verification

After fix:
- Call `POST /api/agent-os/handoff/{project}/populate-db` once — succeeds
- Call it again — succeeds (no IntegrityError), returns same count
- Features in DB match the latest feature list

---

## Fix 5 (MEDIUM): DunkStack router uses hardcoded ROOT_DIR, not project-scoped

### Problem

All DunkStack endpoints operate on `ROOT_DIR / ".agent"` where `ROOT_DIR` is the Greptacular repo root. Multi-project support is broken — all projects share one `.agent` directory.

### File & Lines

`server/routers/dunkstack.py`, lines 31-36

### Fix

Add an optional `project_name` query parameter to all DunkStack endpoints. When provided, resolve the `.agent` directory relative to the project's registered path. When not provided, fall back to the current ROOT_DIR behavior for backward compatibility.

**Replace the ROOT_DIR / helper functions (lines 31-43) with:**

```python
# Root of the project (parent of server/) — used as fallback
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _agent_dir(project_name: Optional[str] = None) -> Path:
    """Return the .agent directory path, optionally scoped to a project."""
    if project_name:
        from ..utils.project_helpers import get_project_path
        project_dir = get_project_path(project_name)
        if project_dir and project_dir.exists():
            return project_dir / ".agent"
    return ROOT_DIR / ".agent"


def _ensure_agent_dir(project_name: Optional[str] = None):
    """Ensure .agent directory structure exists."""
    agent = _agent_dir(project_name)
    for subdir in ["comms", "knowledge", "output", "progress", "settings"]:
        (agent / subdir).mkdir(parents=True, exist_ok=True)
```

**Then update every endpoint** to accept `project_name: Optional[str] = None` as a query parameter and pass it to `_agent_dir()` and `_ensure_agent_dir()`. For example:

```python
@router.get("/comms/to-human")
async def read_to_human(project_name: Optional[str] = None):
    """Read the agent's messages to the human."""
    path = _agent_dir(project_name) / "comms" / "to_human.md"
    if not path.exists():
        return {"content": "", "exists": False}
    return {"content": path.read_text(encoding="utf-8"), "exists": True}
```

Apply this pattern to ALL DunkStack endpoints (comms read/write, control, working memory, index, bridge, config, tokens, build log). The `Optional[str] = None` default ensures backward compatibility.

### Verification

After fix:
- `GET /api/dunkstack/comms/to-human` (no param) — uses ROOT_DIR/.agent (backward compat)
- `GET /api/dunkstack/comms/to-human?project_name=myapp` — uses myapp's .agent directory
- All other endpoints behave the same way

---

## Fix 6 (MEDIUM): Blocking sync file I/O in async handlers

### Problem

Both routers define endpoints as `async def` but do synchronous file I/O (`Path.read_text()`, `Path.write_text()`, `open()`, `yaml.safe_load()`). This blocks the event loop.

### File & Lines

- `server/routers/dunkstack.py` — every endpoint
- `server/routers/agent_os.py` — lines 696, 710, and all endpoints that do file reads

### Fix

The simplest fix: change `async def` to `def` on endpoints that only do synchronous file I/O. FastAPI automatically runs plain `def` endpoints in a thread pool. This is a one-word change per endpoint.

**In `dunkstack.py`**, change all endpoint functions from `async def` to `def`:

```python
# BEFORE:
@router.get("/comms/to-human")
async def read_to_human():

# AFTER:
@router.get("/comms/to-human")
def read_to_human():
```

**Exception:** Keep `async def` on endpoints that call `await _broadcast(...)` since broadcast needs async. For those endpoints (the POST handlers that write AND broadcast), wrap the broadcast in a background task instead:

```python
from fastapi import BackgroundTasks

@router.post("/comms/from-human")
async def write_from_human(msg: CommsMessage):
    # ... sync file I/O done via run_in_executor ...
```

Actually, the cleaner approach: keep the POST handlers as `async def` (they need `await _broadcast`) and only change the GET handlers to `def`:

**GET endpoints to change to `def`:**
- `read_to_human`, `read_from_human`, `read_control`, `read_working_memory`, `read_index`, `read_bridge`, `read_config`, `get_token_state`, `get_token_log`, `read_build_log`

**In `agent_os.py`**, change these GET endpoints to `def`:
- `get_context_primer` (line 690)

**Leave as `async def`:** Any endpoint that calls `await` on something (WebSocket handlers, POST handlers calling `_broadcast`).

### Verification

After fix:
- All GET endpoints still return correct data
- No `RuntimeWarning` about `coroutine was never awaited`
- Under concurrent load, GET requests don't block each other

---

## Fix 7 (MEDIUM): `cache_read_tokens` overwritten instead of accumulated

### Problem

In `dunkstack.py` line 428:
```python
cum["cache_read_tokens"] = snapshot.cache_read_tokens  # Latest, not cumulative
```
This overwrites the cumulative value with just the latest snapshot, while all other token fields use `+=`.

### File & Lines

`server/routers/dunkstack.py`, line 428

### Fix

Change the assignment to accumulation:

```python
# BEFORE:
cum["cache_read_tokens"] = snapshot.cache_read_tokens  # Latest, not cumulative

# AFTER:
cum["cache_read_tokens"] += snapshot.cache_read_tokens
```

### Verification

After fix:
- Record three snapshots with cache_read_tokens = 100 each
- `GET /api/dunkstack/tokens` should show cumulative cache_read_tokens = 300 (not 100)

---

## Fix 8 (MEDIUM): Prompt templates with unescaped JSON braces (maintenance hazard)

### Problem

`EXTRACTION_PROMPT` and `CLASSIFICATION_PROMPT` in `agent_os_intake.py` contain literal `{` / `}` in their JSON templates. They use `.replace()` instead of `.format()` to avoid crashing, but this is fragile — if anyone refactors to `.format()` for consistency, it'll raise `KeyError`.

### File & Lines

`server/services/agent_os_intake.py`, lines 44-77

### Fix

Escape the JSON braces as `{{` / `}}` and switch to `.format()`:

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

Then update the methods to use `.format()`:

```python
def get_classification_prompt(self, user_input: str) -> str:
    """Return the prompt string for Claude to classify the input."""
    return CLASSIFICATION_PROMPT.format(user_input=user_input)

def get_extraction_prompt(self, user_input: str) -> str:
    """Return the prompt string for Claude to extract entities."""
    return EXTRACTION_PROMPT.format(user_input=user_input)
```

**Note:** If user_input itself contains `{` or `}`, it could still break `.format()`. To be safe, escape user input too:

```python
def get_classification_prompt(self, user_input: str) -> str:
    """Return the prompt string for Claude to classify the input."""
    safe_input = user_input.replace("{", "{{").replace("}", "}}")
    return CLASSIFICATION_PROMPT.format(user_input=safe_input)

def get_extraction_prompt(self, user_input: str) -> str:
    """Return the prompt string for Claude to extract entities."""
    safe_input = user_input.replace("{", "{{").replace("}", "}}")
    return EXTRACTION_PROMPT.format(user_input=safe_input)
```

### Verification

After fix:
- `get_classification_prompt("I want to build {a thing}")` returns valid string (no KeyError)
- `get_extraction_prompt("Build app")` returns valid string with properly formatted JSON template

---

## Fix 9 (LOW): `remove_session` is async but has no await points

### Problem

`remove_session` in `agent_os_session.py` (line 424) is declared `async def` but only does synchronous operations (acquires a `threading.Lock`). The `async` keyword is misleading.

### File & Lines

`server/services/agent_os_session.py`, lines 424-426

### Fix

Change to a plain synchronous function:

```python
# BEFORE:
async def remove_session(project_name: str) -> None:
    with _sessions_lock:
        _sessions.pop(project_name, None)

# AFTER:
def remove_session(project_name: str) -> None:
    with _sessions_lock:
        _sessions.pop(project_name, None)
```

Also update the caller in `agent_os.py` line 751:

```python
# BEFORE:
await remove_session(project_name)

# AFTER:
remove_session(project_name)
```

And `cleanup_all_agent_os_sessions` (line 434):

```python
# BEFORE:
async def cleanup_all_agent_os_sessions() -> None:

# AFTER:
def cleanup_all_agent_os_sessions() -> None:
```

**Check the caller** in `server/main.py` — if it does `await cleanup_all_agent_os_sessions()`, change to just `cleanup_all_agent_os_sessions()` or keep it async-compatible. If the shutdown hook requires async, keep the `async def` wrapper but note it has no real await.

### Verification

After fix:
- `DELETE /api/agent-os/sessions/{project}` still works
- Server shutdown still cleans up sessions
- No `RuntimeWarning` about unawaited coroutines

---

## Execution Order

Fix them in this order (dependencies flow downward):

1. **Fix 1** (CRITICAL) — Intake extraction. Unblocks the entire workflow.
2. **Fix 2** (HIGH) — Question off-by-one. Depends on intake working to test.
3. **Fix 8** (MEDIUM) — Prompt template braces. Same file as Fix 1, do together.
4. **Fix 4** (HIGH) — Idempotent populate_features_db. Independent.
5. **Fix 3** (HIGH) — Features cache sync. Independent.
6. **Fix 7** (MEDIUM) — Token accumulation. One-line change.
7. **Fix 5** (MEDIUM) — DunkStack project scoping. Larger but isolated.
8. **Fix 6** (MEDIUM) — async/sync endpoints. Mechanical, low risk.
9. **Fix 9** (LOW) — remove_session async. Trivial.

## Verification Commands

After all fixes:

```bash
# Compile check
python -m py_compile server/services/agent_os_session.py
python -m py_compile server/services/agent_os_intake.py
python -m py_compile server/services/agent_os_handoff.py
python -m py_compile server/routers/agent_os.py
python -m py_compile server/routers/dunkstack.py

# Lint
cd /home/user/Greptacular && ruff check server/services/agent_os_session.py server/services/agent_os_intake.py server/services/agent_os_handoff.py server/routers/agent_os.py server/routers/dunkstack.py

# Import check
python -c "from server.services.agent_os_session import create_session, get_session, remove_session, cleanup_all_agent_os_sessions; print('session imports OK')"
python -c "from server.services.agent_os_intake import AgentOSIntake; i = AgentOSIntake(); i.add_input('test'); i.extract_from_raw_input(); print('entities:', i.get_entities()); print('intake OK')"
python -c "from server.routers.agent_os import router; print('agent_os router OK')"
python -c "from server.routers.dunkstack import router; print('dunkstack router OK')"
```

---

## Context Primer vs Build Primer — Why This Is Different

A **build primer** says: "Here's the vision, here's the patterns, go create."
A **fix primer** says: "Here's the exact bug, here's the exact line, here's the exact fix."

This document is structured so the fix agent:
1. Never needs to explore or search — every file path and line number is given
2. Never needs to understand the full architecture — only the relevant code paths
3. Never needs to make design decisions — the fix strategy is prescribed
4. Can verify each fix independently before moving to the next

The fix agent should read this document top-to-bottom and execute fixes in the prescribed order. Each fix includes before/after code and a verification step.
