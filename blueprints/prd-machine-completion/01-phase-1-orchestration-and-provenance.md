# Phase 1: LLM Orchestration Engine + Provenance System

> Connect the engine. Tag everything.

**Priority**: CRITICAL — nothing else works without this.
**Depends on**: Nothing (first phase).

---

## Overview

The Agent OS pipeline currently generates beautiful prompts and can ingest JSON
responses, but nothing actually calls Claude. This phase connects the engine.

It also adds provenance tagging from the ground up, because retrofitting provenance
after 7 more phases would be painful.

---

## 1.1 LLM Orchestration Engine

### File: `server/services/agent_os_orchestrator.py` (NEW)

**Class**: `AgentOSOrchestrator`

```python
class AgentOSOrchestrator:
    """Sends prompts to Claude and returns parsed JSON responses.

    Uses the anthropic Python SDK directly (not Agent SDK) for
    deterministic, one-shot completions with temperature=0.
    """

    def __init__(self, project_dir: Path, config: dict):
        self.project_dir = project_dir
        self.config = config
        self.token_log: list[dict] = []  # Per-call token tracking
        self._client: Optional[AsyncAnthropic] = None

    async def execute(
        self,
        prompt: str,
        model: str = "sonnet",
        max_tokens: int = 16384,
        temperature: float = 0,
        stage_name: str = "",
    ) -> dict:
        """Send prompt to Claude, parse JSON response, log tokens."""
        ...

    async def execute_with_retry(
        self,
        prompt: str,
        model: str = "sonnet",
        max_retries: int = 2,
        stage_name: str = "",
    ) -> dict:
        """Execute with retry on JSON parse failure."""
        ...

    def get_token_summary(self) -> dict:
        """Return total input/output tokens and estimated cost."""
        ...

    def get_token_log(self) -> list[dict]:
        """Return per-call token log for Context Gauge."""
        ...

    def _resolve_model(self, model: str) -> str:
        """Map 'sonnet'/'opus'/'haiku' to actual model ID from env vars."""
        ...

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from response text (handles markdown fences)."""
        ...
```

**Key behaviors**:
- Uses `anthropic.AsyncAnthropic()` (reads `ANTHROPIC_API_KEY` from env)
- Supports Vertex AI via `CLAUDE_CODE_USE_VERTEX` env var
- Every call logged to `self.token_log` with:
  `{stage, model, input_tokens, output_tokens, cost_estimate, timestamp}`
- JSON extraction handles: raw JSON, ```json fenced, mixed text+JSON
- Retry on `json.JSONDecodeError` re-sends with "Your previous response was not
  valid JSON. Please respond with ONLY a JSON object."

### Integration into `agent_os_session.py`

The session creates an orchestrator instance and passes it to each stage handler:

```python
class AgentOSSession:
    def __init__(self, project_name, project_dir):
        ...
        self.orchestrator = AgentOSOrchestrator(
            project_dir=self.project_dir,
            config=self._load_config()
        )
```

Each `_handle_*()` method gains the pattern:

```python
async def _handle_feature_extraction(self, message):
    ...
    # Get prompt from service (already works)
    prompt = self.features.get_feature_extraction_prompt()

    # NEW: Actually call Claude
    result = await self.orchestrator.execute(
        prompt=prompt,
        model="sonnet",
        stage_name="feature_extraction"
    )

    # Process response (already works)
    features = self.features.process_extracted_features(result.get("features", []))

    yield {"type": "features", "features": features}
```

**Stages that gain LLM calls**:

| Stage | Method | Prompt Source | Response Handler |
|-------|--------|--------------|-----------------|
| 1 | `_handle_intake` | `intake.get_classification_prompt()` | `intake.process_classification()` |
| 1 | `_handle_intake` | `intake.get_extraction_prompt()` | `intake.process_extraction()` |
| 3 | `_handle_product_discovery` | `product.get_doc_generation_prompt()` | `product.process_generated_doc()` |
| 4 | `_handle_feature_extraction` | `features.get_feature_extraction_prompt()` | `features.process_extracted_features()` |
| 5 | `_handle_gap_analysis` | `features.get_gap_analysis_prompt()` | `features.process_gap_analysis()` |
| 6 | `_handle_spec_generation` | `specs.get_spec_generation_prompt()` | `specs.process_generated_spec()` |
| cross | mechanism analysis | `mechanism.get_analysis_prompt()` | `mechanism.process_analysis()` |

---

## 1.2 Provenance Tag System

### File: `server/services/agent_os_provenance.py` (NEW)

**Class**: `AgentOSProvenance`

```python
from enum import Enum

class ProvenanceTag(str, Enum):
    USER = "USER"
    AUTO_FILL = "AUTO_FILL"
    USER_DECIDED = "USER_DECIDED"
    RECOMMENDED = "RECOMMENDED"
    DETECTED = "DETECTED"
    DESCRIBED = "DESCRIBED"
    INFERRED = "INFERRED"
    FEATURE_ADD = "FEATURE_ADD"  # Appended with _vN

class ProvenanceTracker:
    """Track provenance of every item through the pipeline."""

    def __init__(self):
        self.items: dict[str, list[dict]] = {}  # item_key -> history

    def tag(self, item_key: str, tag: ProvenanceTag, source: str = "") -> None:
        """Add a provenance tag to an item."""
        ...

    def get_tag(self, item_key: str) -> Optional[ProvenanceTag]:
        """Get the current (most recent) tag for an item."""
        ...

    def get_history(self, item_key: str) -> list[dict]:
        """Get full provenance history for an item."""
        ...

    def get_all_by_tag(self, tag: ProvenanceTag) -> list[str]:
        """Get all item keys with a given tag."""
        ...

    def get_provenance_summary(self) -> dict[str, int]:
        """Count items per tag (for reporting)."""
        ...

    def export_matrix(self) -> list[dict]:
        """Export full provenance matrix for PRD inclusion."""
        ...
```

### Integration Points

**Stage 1 (Intake)**: Tag every extracted entity.
```python
# In process_extraction():
for entity_key, value in entities.items():
    if value:
        self.provenance.tag(f"entity:{entity_key}", ProvenanceTag.USER)
```

**Stage 4 (Features)**: Tag feature sources.
```python
# In process_extracted_features():
for feature in features:
    tag = ProvenanceTag.USER if feature.get("source") == "intake" else ProvenanceTag.INFERRED
    self.provenance.tag(f"feature:{feature['id']}", tag)
```

**Stage 5 (Gap Analysis)**: Tag resolutions.
```python
# In resolve_gap():
tag = ProvenanceTag.AUTO_FILL if gap["auto_fillable"] else ProvenanceTag.USER_DECIDED
self.provenance.tag(f"gap:{gap_id}", tag)
```

**Stage 6 (Mechanism)**: Tag decisions.
```python
# In record_decision():
self.provenance.tag(f"mechanism:{analysis['mechanism_id']}", ProvenanceTag.RECOMMENDED)
```

**Spec Generation**: Embed provenance tags in generated spec markdown.
```markdown
## Requirements
- User authentication via magic links `[RECOMMENDED]`
- Email verification required `[USER]`
- Session timeout after 30 minutes `[AUTO_FILL]`
```

**Persistence**: Provenance data written to `.agent/progress/provenance.json`
and reloaded on session resume.

---

## 1.3 Token Tracking Events

New WebSocket event type for the session:

```python
yield {
    "type": "token_usage",
    "stage": "feature_extraction",
    "input_tokens": 2847,
    "output_tokens": 1203,
    "cost_estimate": 0.012,
    "cumulative_input": 8941,
    "cumulative_output": 3672,
    "cumulative_cost": 0.041,
}
```

The frontend can display this in the Agent OS UI to show pipeline cost as it runs.

---

## 1.4 Configuration Loading

### Modify: `agent_os_session.py`

Add config loading from `.agent/settings/config.yml`:

```python
def _load_config(self) -> dict:
    """Load Agent OS config with defaults."""
    config_path = self.project_dir / ".agent" / "settings" / "config.yml"
    defaults = {
        "agent_os": {
            "verification": {"enabled": True, "max_retries": 1, "model": "sonnet"},
            "scoring_dimensions": {
                "implementation_speed": 0.20,
                "maintainability": 0.20,
                "user_experience": 0.20,
                "security": 0.15,
                "cost": 0.10,
                "brand_alignment": 0.15,
            },
            "provenance": {"enabled": True},
            "quality_gate": {"enabled": True, "minimum_score": 2.0},
            "golden_orange": {"enabled": True},
        }
    }
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
        # Deep merge user_config over defaults
        return self._deep_merge(defaults, user_config)
    return defaults
```

---

## Phase 1 Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | LLM Orchestrator class | `server/services/agent_os_orchestrator.py` |
| 2 | Provenance Tracker class | `server/services/agent_os_provenance.py` |
| 3 | Session wiring (orchestrator + provenance) | `server/services/agent_os_session.py` (modify) |
| 4 | Config loading with defaults | `server/services/agent_os_session.py` (modify) |
| 5 | Token tracking WebSocket events | `server/services/agent_os_session.py` (modify) |
| 6 | Tests | `test_agent_os_orchestrator.py`, `test_agent_os_provenance.py` |

**Estimated complexity**: Medium. The orchestrator is straightforward (wrap anthropic SDK).
Provenance is threading a new field through existing data structures.
