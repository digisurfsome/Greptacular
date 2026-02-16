# Configurable Agent Budget Levers — Settings UI + Dynamic Context Management

## Status: Ready for Implementation

## Your Mission

Add 9 configurable levers to AutoForge that control how coding agents manage their context budget, how features get batched, and how turn estimation works. These replace hardcoded constants scattered across 4 Python files with dynamic values stored in the settings database and controllable from the Settings modal in the React UI.

**The core principle:** Keep the original creator's granular feature system exactly as-is (small atomic features, 165-405 per project, 20 mandatory test categories, wide dependency graphs). What changes is the SESSION MANAGEMENT — how much of the context window each agent uses, how many features get packed per session, and how aggressively the system batches work. These become tunable levers the owner adjusts per project to find the sweet spot between quality and throughput.

**Read these files FIRST before writing any code:**
1. `registry.py` — Settings key-value store (SQLite), `get_setting()`, `set_setting()`, `get_all_settings()`
2. `server/routers/settings.py` — GET/PATCH `/api/settings` endpoints, `SettingsResponse`/`SettingsUpdate` models
3. `server/schemas.py` — Pydantic models for `SettingsResponse` (line ~429) and `SettingsUpdate` (line ~462)
4. `ui/src/components/SettingsModal.tsx` — React settings UI, existing patterns for toggles/buttons/dropdowns
5. `ui/src/lib/types.ts` — TypeScript type definitions for settings
6. `ui/src/hooks/useProjects.ts` — `useSettings()` and `useUpdateSettings()` hooks
7. `agent.py` — Lines 55-107: budget constants and checkpoint logic
8. `parallel_orchestrator.py` — Lines 139-146 and 200-216: budget/batch constants and constructor
9. `client.py` — Lines 347-362: `max_turns_map` per agent type
10. `autonomous_agent_demo.py` — CLI args and settings flow to orchestrator
11. `prompts.py` — `get_batch_feature_prompt()` and `get_single_feature_prompt()` functions
12. `.claude/templates/coding_prompt.template.md` — The coding agent prompt with budget instructions

**Match existing patterns exactly.** The settings system already has toggles, button groups, and dropdowns. New controls must look and behave identically to existing ones.

---

## The 9 Levers

### Primary Controls (adjust per project — shown prominently in UI)

| # | Lever | Key | Type | Range | Default | What It Controls |
|---|-------|-----|------|-------|---------|------------------|
| 1 | Context Budget Target | `context_budget_pct` | int | 15-50 | 30 | % of context window before agent starts wrapping up |
| 2 | Max Batch Size | `batch_size` | int | 1-7 | 3 | Max features packed per coding agent session |
| 3 | Max Parallel Agents | (already exists) | int | 1-5 | 3 | Concurrent coding agents |

### Advanced Controls (tune over time — collapsed/expandable section in UI)

| # | Lever | Key | Type | Range | Default | What It Controls |
|---|-------|-----|------|-------|---------|------------------|
| 4 | Hard Stop Buffer | `hard_stop_buffer_pct` | int | 3-15 | 5 | % above target before forced stop |
| 5 | Turns Per Step Estimate | `turns_per_step` | int | 5-20 | 10 | Base turn cost per feature step (for batch packing) |
| 6 | Min Feature Turns | `min_feature_turns` | int | 15-50 | 30 | Floor turn estimate even for tiny features |
| 7 | Checkpoint Interval | `budget_checkpoint_interval` | int | 10-40 | 30 | How often agent sees budget warning messages |
| 8 | Max Feature Retries | `max_feature_retries` | int | 1-5 | 3 | Retry attempts before marking feature failed |
| 9 | Max Total Agents | `max_total_agents` | int | 5-15 | 10 | Hard ceiling on all agent processes (coding + testing + review) |

### Derived Values (auto-calculated, shown read-only in UI)

These are NOT stored in settings. They're computed from the primary/advanced levers and displayed so the user sees what their settings mean in practice.

| Derived Value | Formula | Example at 30% budget |
|---|---|---|
| Budget Target Turn | `context_budget_pct / 100 * 300` | Turn 90 |
| Hard Stop Turn | `(context_budget_pct + hard_stop_buffer_pct) / 100 * 300` | Turn 105 |
| Max Turns (SDK) | `hard_stop_turn + 10` | 115 |
| Usable Turns | `target_turn - 20` (orientation overhead) | 70 |
| Est. Features/Session | `usable_turns / (turns_per_step * avg_steps)` | ~2-3 |

The `300` constant represents the full context capacity in turns. The current system uses 150 max_turns as a hard ceiling, but that maps to roughly 50% of the context window. Full capacity is ~300 turns.

---

## Implementation: File-by-File

### File 1: `server/schemas.py` — Add to Pydantic Models

**Add to `SettingsResponse`** (around line 429, after existing fields):

```python
# Agent Budget Settings
context_budget_pct: int = 30
hard_stop_buffer_pct: int = 5
turns_per_step: int = 10
min_feature_turns: int = 30
budget_checkpoint_interval: int = 30
max_feature_retries: int = 3
max_total_agents: int = 10
```

**Add to `SettingsUpdate`** (around line 462, after existing fields):

```python
# Agent Budget Settings
context_budget_pct: int | None = None
hard_stop_buffer_pct: int | None = None
turns_per_step: int | None = None
min_feature_turns: int | None = None
budget_checkpoint_interval: int | None = None
max_feature_retries: int | None = None
max_total_agents: int | None = None
```

**Add validators** to `SettingsUpdate`:

```python
@field_validator('context_budget_pct')
@classmethod
def validate_context_budget(cls, v: int | None) -> int | None:
    if v is not None and (v < 15 or v > 50):
        raise ValueError("context_budget_pct must be between 15 and 50")
    return v

@field_validator('hard_stop_buffer_pct')
@classmethod
def validate_hard_stop_buffer(cls, v: int | None) -> int | None:
    if v is not None and (v < 3 or v > 15):
        raise ValueError("hard_stop_buffer_pct must be between 3 and 15")
    return v

@field_validator('turns_per_step')
@classmethod
def validate_turns_per_step(cls, v: int | None) -> int | None:
    if v is not None and (v < 5 or v > 20):
        raise ValueError("turns_per_step must be between 5 and 20")
    return v

@field_validator('min_feature_turns')
@classmethod
def validate_min_feature_turns(cls, v: int | None) -> int | None:
    if v is not None and (v < 15 or v > 50):
        raise ValueError("min_feature_turns must be between 15 and 50")
    return v

@field_validator('budget_checkpoint_interval')
@classmethod
def validate_checkpoint_interval(cls, v: int | None) -> int | None:
    if v is not None and (v < 10 or v > 40):
        raise ValueError("budget_checkpoint_interval must be between 10 and 40")
    return v

@field_validator('max_feature_retries')
@classmethod
def validate_max_retries(cls, v: int | None) -> int | None:
    if v is not None and (v < 1 or v > 5):
        raise ValueError("max_feature_retries must be between 1 and 5")
    return v

@field_validator('max_total_agents')
@classmethod
def validate_max_total_agents(cls, v: int | None) -> int | None:
    if v is not None and (v < 5 or v > 15):
        raise ValueError("max_total_agents must be between 5 and 15")
    return v
```

### File 2: `server/routers/settings.py` — Read/Write Settings

**In GET handler** (around line 118, add to SettingsResponse constructor):

```python
context_budget_pct=_parse_int(all_settings.get("context_budget_pct"), 30),
hard_stop_buffer_pct=_parse_int(all_settings.get("hard_stop_buffer_pct"), 5),
turns_per_step=_parse_int(all_settings.get("turns_per_step"), 10),
min_feature_turns=_parse_int(all_settings.get("min_feature_turns"), 30),
budget_checkpoint_interval=_parse_int(all_settings.get("budget_checkpoint_interval"), 30),
max_feature_retries=_parse_int(all_settings.get("max_feature_retries"), 3),
max_total_agents=_parse_int(all_settings.get("max_total_agents"), 10),
```

**In PATCH handler** (around line 145, add after existing update blocks):

```python
if update.context_budget_pct is not None:
    set_setting("context_budget_pct", str(update.context_budget_pct))

if update.hard_stop_buffer_pct is not None:
    set_setting("hard_stop_buffer_pct", str(update.hard_stop_buffer_pct))

if update.turns_per_step is not None:
    set_setting("turns_per_step", str(update.turns_per_step))

if update.min_feature_turns is not None:
    set_setting("min_feature_turns", str(update.min_feature_turns))

if update.budget_checkpoint_interval is not None:
    set_setting("budget_checkpoint_interval", str(update.budget_checkpoint_interval))

if update.max_feature_retries is not None:
    set_setting("max_feature_retries", str(update.max_feature_retries))

if update.max_total_agents is not None:
    set_setting("max_total_agents", str(update.max_total_agents))
```

**In PATCH response** (around line 226, add to SettingsResponse constructor):
Same as GET handler above — repeat the `_parse_int()` calls.

### File 3: `ui/src/lib/types.ts` — Add TypeScript Types

**Add to the Settings interface** (find the existing Settings type):

```typescript
// Agent Budget Settings
context_budget_pct: number
hard_stop_buffer_pct: number
turns_per_step: number
min_feature_turns: number
budget_checkpoint_interval: number
max_feature_retries: number
max_total_agents: number
```

### File 4: `ui/src/components/SettingsModal.tsx` — UI Controls

**Add a new section** in the settings modal. Place it AFTER the existing "Build Settings" section and BEFORE "API Provider". Use an expandable/collapsible pattern for the advanced controls.

**Handlers** (add near existing handlers):

```typescript
const handleContextBudgetChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ context_budget_pct: value })
  }
}

const handleHardStopBufferChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ hard_stop_buffer_pct: value })
  }
}

const handleTurnsPerStepChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ turns_per_step: value })
  }
}

const handleMinFeatureTurnsChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ min_feature_turns: value })
  }
}

const handleCheckpointIntervalChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ budget_checkpoint_interval: value })
  }
}

const handleMaxFeatureRetriesChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ max_feature_retries: value })
  }
}

const handleMaxTotalAgentsChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ max_total_agents: value })
  }
}
```

**Add state for advanced section toggle:**

```typescript
const [showAdvancedBudget, setShowAdvancedBudget] = useState(false)
```

**UI Layout for the section:**

```
Agent Context Budget
├── Context Budget Target: [20%] [25%] [30%] [35%] [40%] [45%]   ← button group
├── Max Batch Size: [1] [2] [3] [5] [7]                          ← button group (update existing)
├── Derived values (read-only display):
│   ├── Target Turn: 90 / Hard Stop Turn: 105 / Max Turns: 115
│   └── Usable Turns: 70 / Est. Features/Session: ~2-3
│
└── [▶ Advanced Budget Controls]                                   ← collapsible
    ├── Hard Stop Buffer: [3%] [5%] [8%] [10%] [15%]             ← button group
    ├── Turns Per Step: [5] [8] [10] [15] [20]                   ← button group
    ├── Min Feature Turns: [15] [20] [30] [40] [50]              ← button group
    ├── Checkpoint Interval: [10] [15] [20] [30] [40]            ← button group
    ├── Max Feature Retries: [1] [2] [3] [4] [5]                 ← button group
    └── Max Total Agents: [5] [8] [10] [12] [15]                 ← button group
```

**Derived values display** (compute in the component):

```typescript
const budgetPct = settings?.context_budget_pct ?? 30
const bufferPct = settings?.hard_stop_buffer_pct ?? 5
const targetTurn = Math.round(budgetPct / 100 * 300)
const hardStopTurn = Math.round((budgetPct + bufferPct) / 100 * 300)
const maxTurns = hardStopTurn + 10
const usableTurns = targetTurn - 20
const turnsPerStep = settings?.turns_per_step ?? 10
const estFeaturesPerSession = Math.max(1, Math.round(usableTurns / (turnsPerStep * 5)))  // Assume avg 5 steps
```

**For the existing batch_size control**, update the button options from `[1, 2, 3]` to `[1, 2, 3, 5, 7]`.

### File 5: `agent.py` — Read Budget Settings Dynamically

**Current hardcoded constants (lines 55-60):**

```python
BUDGET_TARGET_TURNS = 135
BUDGET_WARN_TURNS = 120
BUDGET_CHECKPOINT_INTERVAL = 30
MAX_CODING_TURNS = 150
```

**Replace with dynamic loading.** Add an import and helper function:

```python
from registry import get_setting

def _get_budget_constants() -> tuple[int, int, int, int]:
    """Calculate budget constants from settings."""
    budget_pct = int(get_setting("context_budget_pct", "30"))
    buffer_pct = int(get_setting("hard_stop_buffer_pct", "5"))
    checkpoint = int(get_setting("budget_checkpoint_interval", "30"))

    target_turn = round(budget_pct / 100 * 300)
    hard_stop_turn = round((budget_pct + buffer_pct) / 100 * 300)
    max_turns = hard_stop_turn + 10
    # Warn 15 turns before target
    warn_turn = max(target_turn - 15, checkpoint)

    return target_turn, warn_turn, checkpoint, max_turns
```

**In `run_agent_session()`**, replace the hardcoded constants with the dynamic values:

```python
async def run_agent_session(...):
    budget_target, budget_warn, checkpoint_interval, max_coding_turns = _get_budget_constants()
    # ... rest of function uses these local variables instead of module constants ...
```

**Keep the module-level constants as FALLBACK defaults** in case `get_setting()` fails:

```python
# Fallback defaults (overridden by settings from registry.db)
DEFAULT_BUDGET_TARGET_TURNS = 90   # 30% of 300
DEFAULT_BUDGET_WARN_TURNS = 75     # 15 turns before target
DEFAULT_BUDGET_CHECKPOINT_INTERVAL = 30
DEFAULT_MAX_CODING_TURNS = 115     # hard stop (35%) + 10 buffer
```

### File 6: `parallel_orchestrator.py` — Read Budget Settings Dynamically

**Current hardcoded constants (lines 139-145):**

```python
BUDGET_USABLE_TURNS = 120
TURNS_PER_STEP = 10
MIN_FEATURE_TURNS = 30
```

**Replace with settings-aware loading in the constructor.** Add to `__init__()`:

```python
from registry import get_setting

# In __init__, after existing assignments:
budget_pct = int(get_setting("context_budget_pct", "30"))
target_turn = round(budget_pct / 100 * 300)
self._budget_usable_turns = target_turn - 20  # Subtract orientation overhead
self._turns_per_step = int(get_setting("turns_per_step", "10"))
self._min_feature_turns = int(get_setting("min_feature_turns", "30"))
self._max_feature_retries = int(get_setting("max_feature_retries", "3"))

# Also read max_total_agents
max_total = int(get_setting("max_total_agents", "10"))
# Replace the hardcoded MAX_TOTAL_AGENTS constant usage
```

**Update `_estimate_feature_turns()`** to use instance variables instead of module constants. Change from `@staticmethod` to a regular method:

```python
def _estimate_feature_turns(self, feature: dict) -> int:
    steps = feature.get("steps") or []
    if not isinstance(steps, list) or not steps:
        return self._min_feature_turns

    total = 0
    for step in steps:
        step_text = str(step) if step else ""
        step_turns = self._turns_per_step
        # Complex steps (long descriptions) get a multiplier
        if len(step_text) > 400:
            step_turns = int(step_turns * 2.0)
        elif len(step_text) > 200:
            step_turns = int(step_turns * 1.5)
        total += step_turns

    return max(total, self._min_feature_turns)
```

**Update batch_size clamp (line 208):**

```python
# Current: self.batch_size = min(max(batch_size, 1), 3)
# Change to: self.batch_size = min(max(batch_size, 1), 7)
```

**Update `build_feature_batches()`** to use `self._budget_usable_turns` instead of the module constant `BUDGET_USABLE_TURNS`. Search for all references to the constant and replace.

**Keep module-level constants as documentation defaults:**

```python
# Default values (overridden by settings from registry.db in __init__)
DEFAULT_BUDGET_USABLE_TURNS = 70   # 30% budget: turn 90 - 20 orientation
DEFAULT_TURNS_PER_STEP = 10
DEFAULT_MIN_FEATURE_TURNS = 30
```

### File 7: `client.py` — Dynamic max_turns

**Current (lines 353-362):**

```python
max_turns_map = {
    "coding": 150,
    "testing": 75,
    ...
}
```

**Change coding agent max_turns to be dynamic:**

```python
from registry import get_setting

# Calculate coding max_turns from budget settings
budget_pct = int(get_setting("context_budget_pct", "30"))
buffer_pct = int(get_setting("hard_stop_buffer_pct", "5"))
hard_stop_turn = round((budget_pct + buffer_pct) / 100 * 300)
coding_max_turns = hard_stop_turn + 10

max_turns_map = {
    "coding": coding_max_turns,
    "testing": 75,          # Testing doesn't use budget settings
    "initializer": 200,     # Initializer doesn't use budget settings
    "reviewer": 100,        # Reviewer doesn't use budget settings
    "qa": 250,              # QA doesn't use budget settings
    "spec-analyzer": 75,
    "architect": 100,
}
```

### File 8: `autonomous_agent_demo.py` — Update CLI Args

**Update `--batch-size` argument:**

```python
# Current:
parser.add_argument('--batch-size', type=int, default=3, help="...(1-3, default: 3)")

# Change to:
parser.add_argument('--batch-size', type=int, default=3, help="Max features per coding agent batch (1-7, default: 3)")
```

Remove the `choices=range(1, 4)` constraint if present — the orchestrator handles clamping.

### File 9: `prompts.py` — Dynamic Budget in Prompts

**In `get_single_feature_prompt()`** (around line 364), replace the hardcoded "45%" text:

```python
from registry import get_setting

budget_pct = int(get_setting("context_budget_pct", "30"))
buffer_pct = int(get_setting("hard_stop_buffer_pct", "5"))
target_turn = round(budget_pct / 100 * 300)
hard_stop_pct = budget_pct + buffer_pct
warn_turn = max(target_turn - 15, 30)

single_feature_header = f"""## ASSIGNED FEATURE: #{feature_id}

**Context Budget: {budget_pct}% target, {hard_stop_pct}% hard stop.** Wrap up by turn {warn_turn}, done by turn {target_turn}.

Work ONLY on this feature. ...
```

**In `get_batch_feature_prompt()`** (around line 399), same dynamic replacement:

```python
budget_pct = int(get_setting("context_budget_pct", "30"))
buffer_pct = int(get_setting("hard_stop_buffer_pct", "5"))
target_turn = round(budget_pct / 100 * 300)
hard_stop_pct = budget_pct + buffer_pct
warn_turn = max(target_turn - 15, 30)

batch_header = f"""## ASSIGNED FEATURES (BATCH): {ids_str}

**Context Budget: {budget_pct}% target, {hard_stop_pct}% hard stop.** Wrap up by turn {warn_turn}, done by turn {target_turn}.
...
### Budget-Aware Workflow for each feature:
...
6. **CHECK YOUR BUDGET** - if you are past turn {warn_turn}, wrap up and stop
...
```

### File 10: `.claude/templates/coding_prompt.template.md` — Placeholders

**Replace hardcoded budget numbers with placeholders** that `prompts.py` fills in. In the "CONTEXT BUDGET MANAGEMENT" section (lines 8-35):

Replace:
```
Your target is **45% context usage** per session with a **hard stop at 48%**.
```

With:
```
Your target is **[BUDGET_TARGET_PCT]% context usage** per session with a **hard stop at [HARD_STOP_PCT]%**.
```

Replace:
```
- **Turn count**: You have approximately **135 turns** total (45% of your capacity). Wrap-up should begin by **turn 120**. You MUST be committed and done by **turn 135**.
```

With:
```
- **Turn count**: You have approximately **[BUDGET_TARGET_TURN] turns** total ([BUDGET_TARGET_PCT]% of your capacity). Wrap-up should begin by **turn [BUDGET_WARN_TURN]**. You MUST be committed and done by **turn [BUDGET_TARGET_TURN]**.
```

**Then in `prompts.py`, `get_coding_prompt()`** (or wherever the template is loaded), replace these placeholders:

```python
budget_pct = int(get_setting("context_budget_pct", "30"))
buffer_pct = int(get_setting("hard_stop_buffer_pct", "5"))
target_turn = round(budget_pct / 100 * 300)
hard_stop_pct = budget_pct + buffer_pct
warn_turn = max(target_turn - 15, 30)

prompt = prompt.replace("[BUDGET_TARGET_PCT]", str(budget_pct))
prompt = prompt.replace("[HARD_STOP_PCT]", str(hard_stop_pct))
prompt = prompt.replace("[BUDGET_TARGET_TURN]", str(target_turn))
prompt = prompt.replace("[BUDGET_WARN_TURN]", str(warn_turn))
```

---

## What NOT to Change

1. **The feature creation system** — Keep the Initializer's granular features (165-405 per project). Keep the 20 mandatory test categories. Keep the 5 infrastructure features. Keep the wide dependency graphs. Keep `feature_create_bulk`. Keep `feature_split`. All of this stays exactly as-is.

2. **The feature count tiers in the Initializer prompt** — Keep Simple: ~165, Medium: ~265, Advanced: ~405. These define feature GRANULARITY, not session management.

3. **The `autoforge-prd-context.md`** — Leave the reference tiers as they are. The user now understands these correctly and wants to keep the granular approach.

4. **Testing/review/QA agent max_turns** — Only coding agent max_turns is dynamic. Testing (75), Initializer (200), Reviewer (100), QA (250) stay hardcoded.

5. **The `feature_split` MCP tool** — Still available as a runtime escape valve.

6. **The dependency system** — DAG enforcement, wide graphs, no cycles.

---

## Verification Checklist

After implementing all changes:

- [ ] Set context_budget_pct to 30 in the UI. Verify: agent.py prints budget messages referencing turn 90 (not 135)
- [ ] Set context_budget_pct to 45 in the UI. Verify: behavior matches the CURRENT system exactly (backward compatible)
- [ ] Set context_budget_pct to 20 in the UI. Verify: max_turns in client.py calculates to ~85 (25% of 300 + 10)
- [ ] Set batch_size to 5 in the UI. Verify: orchestrator accepts it (no clamp to 3)
- [ ] Set batch_size to 10 in the UI. Verify: orchestrator clamps to 7
- [ ] Verify derived values in UI update live when sliders change
- [ ] Verify advanced section is collapsed by default, expandable
- [ ] Run tests: `python -m pytest test_client.py`
- [ ] Run tests: `python -m pytest test_dependency_resolver.py`
- [ ] Run security tests: `python test_security.py`
- [ ] Run linting: `ruff check .`
- [ ] Run UI lint: `cd ui && npm run lint`
- [ ] Run UI build: `cd ui && npm run build`
- [ ] Start the server and open the Settings modal — all new controls appear and save correctly
- [ ] Start a build with non-default settings — verify the coding agent sees the correct budget numbers in its prompt

---

## Edge Cases

1. **Settings not yet saved** — If a setting key doesn't exist in registry.db, `get_setting(key, default)` returns the default. All new settings have safe defaults that match (or improve upon) the current behavior.

2. **Budget so low the agent can't do anything** — At 15% budget: target turn 45, usable turns 25. A feature with 3 steps (30 min turns) barely fits. The batch builder won't pack more than 1 feature. This is intentional — 15% is the "maximum quality, minimum throughput" extreme.

3. **Budget at 50% (maximum)** — Target turn 150, hard stop turn 165, max turns 175. This exceeds the current max_turns of 150. The system works but operates in the zone where quality starts degrading. The UI should show a warning when budget exceeds 40%: "Higher budgets risk quality degradation."

4. **Changing settings mid-build** — Settings are read at agent session START (in `create_client()` and `run_agent_session()`). Changing settings mid-build affects the NEXT agent session, not currently running ones. This is the correct behavior.

5. **The `_estimate_feature_turns` change from @staticmethod to method** — This affects all callers in parallel_orchestrator.py. Search for `_estimate_feature_turns(` and update each call from `ParallelOrchestrator._estimate_feature_turns(feature)` to `self._estimate_feature_turns(feature)`.

6. **Import cycles** — `agent.py` and `parallel_orchestrator.py` both import from `registry.py`. Verify no circular imports exist. `registry.py` should not import from either of them.

---

## Per-Project Override (Future Enhancement)

The current implementation uses global settings only. A natural next step is per-project overrides stored in `.autoforge/agent_config.yaml`:

```yaml
# .autoforge/agent_config.yaml (optional, overrides global settings)
context_budget_pct: 20
batch_size: 2
max_feature_retries: 5
```

This is NOT part of this implementation. Mention it in a code comment for future reference, but do not build it now. Global settings are sufficient for the first iteration.

---

## Summary

This implementation turns 6 hardcoded constants scattered across 4 Python files into 9 configurable levers accessible from the Settings UI. The feature creation system stays exactly as the original creator designed it. What changes is how aggressively the system utilizes each coding agent's context window.

The owner can now dial in their preferred quality/throughput tradeoff per project: 20% for mission-critical apps (maximum quality, more sessions), 40% for quick prototypes (fast builds, good-enough quality). The default of 30% provides excellent quality with reasonable throughput.
