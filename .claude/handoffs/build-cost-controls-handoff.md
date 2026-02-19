# Handoff: Build Cost Controls, Budget Safety Cap, and Adaptive Cost Learning

## Background

AutoForge currently has **zero cost controls** for build agents. The workspace chat has rich cost settings (effort, max_tokens, max_turns, history_budget, library_cap) with per-session configuration, but build agents only have `max_turns` as a guardrail. Build agent usage data is captured from the SDK (`ResultMessage` with `total_cost_usd`, `input_tokens`, `output_tokens`) but printed to console and discarded — never stored.

Both systems share the same API credentials via `get_effective_sdk_env()` from `registry.py`, meaning build agent API usage and workspace chat usage compete for the same rate limit windows.

**Three features to implement:**
1. **Build Budget Presets** — Economy/Balanced/Quality per-agent-type cost profiles
2. **Max Budget Safety Cap** — Hard dollar limit per build session (text input)
3. **Adaptive Cost Learning** — Store usage data, analyze patterns, suggest optimal presets

---

## Feature 1: Build Budget Presets

### What It Does

A single preset selector (Economy / Balanced / Quality) in the Settings modal that controls per-agent-type parameters for build agents. Each preset maps to different values of:
- `effort` — thinking effort ("low", "medium", "high")
- `max_tokens` — output token cap per response (4096-65536)
- `max_turns` — max agent turns per session (25-200)

### Preset Definitions

These are starting points — the adaptive learning system (Feature 3) will refine them over time.

```python
BUILD_PRESETS = {
    "economy": {
        "initializer": {"effort": "medium", "max_tokens": 16384, "max_turns": 200},
        "coding":      {"effort": "low",    "max_tokens": 8192,  "max_turns": 50},
        "testing":     {"effort": "low",    "max_tokens": 8192,  "max_turns": 50},
        "reviewer":    {"effort": "low",    "max_tokens": 8192,  "max_turns": 50},
        "qa":          {"effort": "low",    "max_tokens": 8192,  "max_turns": 75},
    },
    "balanced": {
        "initializer": {"effort": "medium", "max_tokens": 16384, "max_turns": 200},
        "coding":      {"effort": "low",    "max_tokens": 16384, "max_turns": 75},
        "testing":     {"effort": "low",    "max_tokens": 8192,  "max_turns": 75},
        "reviewer":    {"effort": "medium", "max_tokens": 16384, "max_turns": 75},
        "qa":          {"effort": "medium", "max_tokens": 16384, "max_turns": 100},
    },
    "quality": {
        "initializer": {"effort": "high",   "max_tokens": 33000, "max_turns": 200},
        "coding":      {"effort": "medium", "max_tokens": 16384, "max_turns": 150},
        "testing":     {"effort": "low",    "max_tokens": 16384, "max_turns": 75},
        "reviewer":    {"effort": "medium", "max_tokens": 16384, "max_turns": 100},
        "qa":          {"effort": "high",   "max_tokens": 16384, "max_turns": 250},
    },
}
```

**Key design choice:** The initializer always gets `max_turns=200` regardless of preset because it needs room for bulk feature creation. The savings come from `effort` and `max_tokens` on the high-volume coding/testing agents.

### Files to Modify

#### 1. `server/schemas.py` — Add preset field

**`SettingsResponse`** (line ~872): Add:
```python
build_cost_preset: str = "balanced"  # "economy", "balanced", "quality"
```

**`SettingsUpdate`** (line ~896): Add:
```python
build_cost_preset: str | None = None

@field_validator('build_cost_preset')
@classmethod
def validate_build_cost_preset(cls, v: str | None) -> str | None:
    if v is not None and v not in ("economy", "balanced", "quality"):
        raise ValueError("build_cost_preset must be 'economy', 'balanced', or 'quality'")
    return v
```

#### 2. `server/routers/settings.py` — Store/retrieve preset

**`get_settings()`** (line ~108): Add to return:
```python
build_cost_preset=all_settings.get("build_cost_preset", "balanced"),
```

**`update_settings()`** (line ~145): Add:
```python
if update.build_cost_preset is not None:
    set_setting("build_cost_preset", update.build_cost_preset)
```

Also add to the second `SettingsResponse(...)` return at bottom of `update_settings()`.

#### 3. `ui/src/lib/types.ts` — TypeScript types

**`Settings`** (line 872): Add:
```typescript
build_cost_preset: string  // "economy" | "balanced" | "quality"
```

**`SettingsUpdate`** (line 896): Add:
```typescript
build_cost_preset?: string
```

#### 4. `ui/src/components/SettingsModal.tsx` — UI control

Add a 3-button preset selector (same pattern as batch_size at lines 448-468):

```tsx
const handleBuildPresetChange = (preset: string) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ build_cost_preset: preset })
  }
}

{/* Build Cost Preset */}
<div className="space-y-2">
  <Label className="font-medium">Build Cost Profile</Label>
  <p className="text-sm text-muted-foreground">
    Controls thinking effort and output limits for build agents.
    Economy saves tokens; Quality maximizes reliability.
  </p>
  <div className="flex gap-2">
    {[
      { key: "economy", label: "Economy", desc: "~$5-15/build" },
      { key: "balanced", label: "Balanced", desc: "~$15-30/build" },
      { key: "quality", label: "Quality", desc: "~$30-60/build" },
    ].map((preset) => (
      <Button
        key={preset.key}
        variant={(settings.build_cost_preset ?? "balanced") === preset.key ? "default" : "outline"}
        size="sm"
        onClick={() => handleBuildPresetChange(preset.key)}
        disabled={isSaving}
        className="flex-1"
      >
        <div className="text-center">
          <div>{preset.label}</div>
          <div className="text-xs opacity-70">{preset.desc}</div>
        </div>
      </Button>
    ))}
  </div>
</div>
```

#### 5. `client.py` — Apply preset to agent configuration

The preset needs to feed into `ClaudeAgentOptions` when creating the client.

**Current state (line ~669):** `ClaudeAgentOptions` is created with `max_turns` from a hardcoded map.

**Change:** Read the preset from settings and apply `effort`, `max_tokens`, and `max_turns`.

```python
# In create_client(), BEFORE the ClaudeAgentOptions construction:

from registry import get_setting

# Read build cost preset
build_preset = get_setting("build_cost_preset", "balanced")

# Preset definitions (same as BUILD_PRESETS above)
BUILD_PRESETS = { ... }  # Define at module level

# Get settings for this agent type
preset_settings = BUILD_PRESETS.get(build_preset, BUILD_PRESETS["balanced"])
agent_settings = preset_settings.get(agent_type, preset_settings.get("coding"))

# Apply to ClaudeAgentOptions:
max_turns = agent_settings["max_turns"]
# Also pass effort and max_tokens:
```

**SDK parameters that accept these values** (confirmed from workspace chat at `workspace_chat_session.py` lines 376-407):
```python
ClaudeAgentOptions(
    max_turns=agent_settings["max_turns"],      # Already exists, change source
    max_tokens=agent_settings["max_tokens"],     # NEW - add this parameter
    effort=agent_settings["effort"],             # NEW - add this parameter
    # ... rest unchanged
)
```

**Important:** `effort` and `max_tokens` are confirmed valid `ClaudeAgentOptions` parameters — workspace chat already uses them at `workspace_chat_session.py:395-396`.

---

## Feature 2: Max Budget Safety Cap

### What It Does

A text input in Settings where the user enters a dollar amount (e.g., "$15.00"). If a build session's cumulative API cost exceeds this threshold, the agent session is aborted immediately.

### Why We Can't Use `max_budget_usd`

The Claude Agent SDK v0.1.x does **NOT** support `max_budget_usd` as a parameter on `ClaudeAgentOptions`. This was confirmed — the parameter doesn't exist in the SDK. We must implement cost checking ourselves using the per-step usage data we're already capturing.

### Implementation Approach

Use the `total_cost_usd` from `ResultMessage` and/or cumulative per-step tracking from `AssistantMessage.usage` to check cost during a session.

**The challenge:** `total_cost_usd` only arrives at session END (in `ResultMessage`). For mid-session enforcement, we need to estimate cost from per-step `AssistantMessage.usage` data.

**Cost estimation formula** (same as workspace chat uses at `workspace_database.py:1609-1655`):
```python
# Opus pricing
INPUT_RATE = 15.0    # $/MTok for first 200K
PREMIUM_RATE = 22.5  # $/MTok above 200K (1.5x)
OUTPUT_RATE = 75.0   # $/MTok
CACHE_READ_RATE = 1.5  # $/MTok
CACHE_CREATE_RATE = 18.75  # $/MTok

# Per-step cost estimate from AssistantMessage.usage:
cost = (input_tokens / 1_000_000 * INPUT_RATE +
        output_tokens / 1_000_000 * OUTPUT_RATE +
        cache_read / 1_000_000 * CACHE_READ_RATE +
        cache_create / 1_000_000 * CACHE_CREATE_RATE)
```

### Files to Modify

#### 1. `server/schemas.py` — Add setting

```python
# SettingsResponse:
max_build_budget_usd: float = 0.0  # 0 = no limit

# SettingsUpdate:
max_build_budget_usd: float | None = None

@field_validator('max_build_budget_usd')
@classmethod
def validate_max_build_budget_usd(cls, v: float | None) -> float | None:
    if v is not None and v < 0:
        raise ValueError("max_build_budget_usd cannot be negative")
    return v
```

#### 2. `server/routers/settings.py` — Store/retrieve

```python
# GET:
max_build_budget_usd=float(all_settings.get("max_build_budget_usd", "0.0")),

# PATCH:
if update.max_build_budget_usd is not None:
    set_setting("max_build_budget_usd", str(update.max_build_budget_usd))
```

#### 3. `ui/src/lib/types.ts` and `SettingsModal.tsx`

```typescript
// types.ts Settings:
max_build_budget_usd: number  // 0 = no limit

// SettingsModal.tsx:
<div className="space-y-2">
  <Label className="font-medium">Max Build Budget (USD)</Label>
  <p className="text-sm text-muted-foreground">
    Stop any build session if estimated API cost exceeds this amount. 0 = no limit.
  </p>
  <Input
    type="number"
    min={0}
    step={0.50}
    value={settings.max_build_budget_usd ?? 0}
    onChange={(e) => updateSettings.mutate({ max_build_budget_usd: Number(e.target.value) })}
    disabled={isSaving}
    className="w-32"
    placeholder="0.00"
  />
</div>
```

#### 4. `agent.py` — Mid-session cost check (the critical part)

In `run_agent_session()`, after capturing per-step `AssistantMessage.usage`, check cumulative cost against the budget cap.

**Current location:** `agent.py` lines 140-177 (the AssistantMessage handler inside the receive loop).

**Add after the existing per-step usage tracking (line ~155):**

```python
# Mid-session cost estimation and budget enforcement
if latest_input_tokens > 0 and max_budget_usd > 0:
    step_output = step_usage.get("output_tokens", 0)
    step_cache_read = step_usage.get("cache_read_input_tokens", 0)
    step_cache_create = step_usage.get("cache_creation_input_tokens", 0)
    estimated_cost = (
        latest_input_tokens / 1_000_000 * 15.0 +
        step_output / 1_000_000 * 75.0 +
        step_cache_read / 1_000_000 * 1.5 +
        step_cache_create / 1_000_000 * 18.75
    )
    if estimated_cost >= max_budget_usd:
        print(f"\n[BUDGET CAP] Estimated cost ${estimated_cost:.2f} >= "
              f"limit ${max_budget_usd:.2f} - STOPPING SESSION")
        # Break out of the receive loop
        break
```

**New parameter on `run_agent_session()`:**
```python
async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
    agent_type: str = "coding",
    context_window: int | None = None,
    max_budget_usd: float = 0.0,        # NEW - 0 = no limit
) -> tuple[str, str, dict]:
```

**Read the setting in the main loop** (`run_autonomous_agent`):
```python
from registry import get_setting
max_budget_str = get_setting("max_build_budget_usd", "0.0")
try:
    max_budget_usd = float(max_budget_str)
except ValueError:
    max_budget_usd = 0.0

# Pass to run_agent_session:
status, response, _usage = await run_agent_session(
    client, prompt, project_dir,
    agent_type=agent_type,
    context_window=session_context_window,
    max_budget_usd=max_budget_usd,
)
```

**Also:** After the session ends, if `ResultMessage.total_cost_usd` is available, print the **actual** cost vs. the estimated cost so the user can see how accurate the estimation was:
```python
if usage_data.get("total_cost_usd") is not None:
    print(f"  Actual cost: ${usage_data['total_cost_usd']:.4f} "
          f"(estimated: ${estimated_cost:.4f})")
```

### Important Notes

- The cost estimation uses **Opus pricing**. If the user switches to Sonnet via model settings, the rates need to adjust. Consider reading the model from settings and selecting the right rate table.
- The `break` from the receive loop after hitting the budget cap means the agent stops mid-session. The usage data from `ResultMessage` may not arrive (since we broke the loop). Handle this gracefully — use the estimated cost if actual cost is unavailable.
- Cost estimation from `AssistantMessage.usage` is cumulative (not per-step), so input_tokens grows over the session as context fills. The estimate naturally accounts for growing context costs.

---

## Feature 3: Adaptive Cost Learning System

### What It Does

1. **Store** every build session's usage data in a database table (currently discarded)
2. **Analyze** patterns: which preset was used, what agent type, how many features, actual cost, success/failure
3. **Suggest** optimal preset adjustments via a learning model
4. **Display** suggestions in the UI — "Based on your last 10 builds, switching coding agents to Economy would save ~$12/build with no quality loss"

### Phase 3A: Store Build Usage Data

#### New Database Table

Add to `api/database.py` or create a new `server/services/build_usage_database.py`:

```python
class BuildSessionUsage(Base):
    """Records usage data for every build agent session."""
    __tablename__ = "build_session_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Session identification
    project_name = Column(String(255), nullable=False)
    agent_type = Column(String(50), nullable=False)  # initializer, coding, testing, etc.
    session_id = Column(String(100), nullable=True)   # From ResultMessage

    # Build context
    feature_count = Column(Integer, nullable=True)     # Total features in project
    feature_id = Column(Integer, nullable=True)        # Specific feature worked on
    build_cost_preset = Column(String(50), nullable=True)  # economy, balanced, quality

    # Token usage (from ResultMessage)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cache_read_tokens = Column(Integer, nullable=False, default=0)
    cache_create_tokens = Column(Integer, nullable=False, default=0)

    # Context
    context_window = Column(Integer, nullable=False, default=200000)  # 200K or 1M
    context_pct = Column(Integer, nullable=False, default=0)          # % of window used

    # Cost and duration
    total_cost_usd = Column(Float, nullable=True)       # From ResultMessage (actual)
    estimated_cost_usd = Column(Float, nullable=True)    # Our estimation
    duration_ms = Column(Integer, nullable=False, default=0)
    duration_api_ms = Column(Integer, nullable=False, default=0)
    num_turns = Column(Integer, nullable=False, default=0)

    # Settings used (snapshot of what was configured for this session)
    effort = Column(String(20), nullable=True)    # low, medium, high
    max_tokens = Column(Integer, nullable=True)
    max_turns = Column(Integer, nullable=True)

    # Outcome
    status = Column(String(20), nullable=False, default="unknown")  # success, error, budget_cap
    feature_passed = Column(Boolean, nullable=True)  # Did the feature pass after this session?
```

#### Storage Point

In `agent.py`, the `_usage` variable is currently discarded (prefixed with underscore at lines 354, 365, 460). Change it to store:

```python
# Instead of:
status, response, _usage = await run_agent_session(...)

# Do:
status, response, usage_data = await run_agent_session(...)

# Store to database:
if usage_data:
    _store_build_usage(
        project_name=project_dir.name,
        agent_type=agent_type,
        feature_id=feature_id,
        feature_count=total_features,
        build_cost_preset=get_setting("build_cost_preset", "balanced"),
        usage_data=usage_data,
        status=status,
    )
```

The `_store_build_usage()` function writes to the `BuildSessionUsage` table. It should be fire-and-forget (wrapped in try/except so a DB failure doesn't crash the build).

#### Where to Put the Database

Option A: Add the table to the project's `features.db` — keeps data with the project but is per-project only.

Option B: Add the table to `~/.autoforge/registry.db` — global across all projects, enables cross-project analysis. **This is the better choice** since the learning system needs data across multiple builds and projects to learn effectively.

Use `registry.py`'s existing SQLAlchemy engine and `_get_session()` pattern.

### Phase 3B: Analysis and Suggestions

#### Analysis Functions

Create `server/services/build_cost_analyzer.py`:

```python
def get_build_cost_summary(project_name: str = None, days: int = 30) -> dict:
    """Aggregate build costs by agent type and preset over a time period."""
    # Returns:
    # {
    #     "total_cost": 45.23,
    #     "total_sessions": 142,
    #     "by_agent_type": {
    #         "coding": {"sessions": 80, "avg_cost": 0.22, "avg_context_pct": 18, "success_rate": 0.95},
    #         "testing": {"sessions": 40, "avg_cost": 0.15, "avg_context_pct": 12, "success_rate": 0.98},
    #         "initializer": {"sessions": 5, "avg_cost": 2.50, "avg_context_pct": 35, "success_rate": 1.0},
    #     },
    #     "by_preset": {
    #         "economy": {"sessions": 50, "total_cost": 12.00, "success_rate": 0.92},
    #         "balanced": {"sessions": 92, "total_cost": 33.23, "success_rate": 0.97},
    #     }
    # }

def get_optimization_suggestions() -> list[dict]:
    """Analyze usage patterns and suggest cost optimizations."""
    # Logic:
    # 1. For each agent type, check success rate at each preset level
    # 2. If success_rate at Economy >= 90% for coding agents, suggest:
    #    "Coding agents succeed 94% of the time on Economy. Consider switching from Balanced."
    # 3. If a specific agent type always uses < 30% context, suggest:
    #    "Testing agents average 12% context usage. Current max_turns=75 could be reduced to 40."
    # 4. If initializer cost is >$5 but feature count is <50, suggest:
    #    "Initializer used $6.20 for 18 features. Economy preset would likely work."
    # 5. Calculate estimated savings for each suggestion

    # Returns:
    # [
    #     {
    #         "type": "preset_downgrade",
    #         "agent_type": "coding",
    #         "current": "balanced",
    #         "suggested": "economy",
    #         "confidence": 0.94,  # success rate on economy
    #         "estimated_monthly_savings": 18.50,
    #         "reason": "94% success rate on Economy over 50 sessions"
    #     },
    #     {
    #         "type": "turns_reduction",
    #         "agent_type": "testing",
    #         "current_max_turns": 75,
    #         "suggested_max_turns": 40,
    #         "avg_turns_used": 22,
    #         "reason": "Average testing session uses 22 turns out of 75"
    #     }
    # ]
```

#### The Learning Logic

The suggestions improve over time because:

1. **More data = higher confidence.** With 5 sessions, suggestions are tentative. With 50, they're reliable.
2. **Failure tracking.** If a coding agent fails at Economy but succeeds at Balanced on retry, that feature/project gets tagged as "needs Balanced." Future similar features default higher.
3. **Project complexity fingerprinting.** Over time, the system learns that projects with >100 features tend to need Quality for the initializer, while <30 feature projects work fine on Economy.
4. **Seasonal patterns.** Rate limit calibration data from the workspace chat's `WorkspaceRateLimitEvent` table can inform when to prefer subscription (hitting API rate limits) vs. API billing (hitting subscription limits).

### Phase 3C: API Endpoint for Suggestions

#### New Router

Create `server/routers/build_usage.py`:

```python
@router.get("/build-usage/summary")
async def get_build_usage_summary(project_name: str = None, days: int = 30):
    """Get aggregated build cost data."""
    return get_build_cost_summary(project_name, days)

@router.get("/build-usage/suggestions")
async def get_optimization_suggestions_endpoint():
    """Get AI-powered cost optimization suggestions."""
    return get_optimization_suggestions()

@router.get("/build-usage/history")
async def get_build_usage_history(
    project_name: str = None,
    agent_type: str = None,
    limit: int = 50,
):
    """Get recent build session usage records."""
    # Returns list of BuildSessionUsage records with filters
```

### Phase 3D: UI Display

Add a "Build Costs" section or tab in the UI that shows:

1. **Summary cards** — Total cost this week/month, sessions count, avg cost per build
2. **Suggestions panel** — Active optimization suggestions with "Apply" buttons
3. **History table** — Recent sessions with agent_type, cost, context%, status
4. **Trend chart** — Cost per build over time (are we getting more efficient?)

This could be a new page route (e.g., `/#/build-costs`) or a panel within the existing settings/dashboard area.

---

## Implementation Order

### Phase 1 (Quick wins, protect against overspend)
1. Max Budget Safety Cap (Feature 2) — **Do this first.** It's the smallest change and prevents runaway costs immediately.
2. Build Budget Presets (Feature 1) — Gives the user Economy/Balanced/Quality control.

### Phase 2 (Data collection)
3. Build Usage Storage (Feature 3A) — Start storing every session's data. Even before analysis exists, the data accumulates.

### Phase 3 (Intelligence)
4. Analysis functions (Feature 3B) — Once you have 20-30 builds of data, the patterns become clear.
5. API endpoints (Feature 3C) — Expose the analysis.
6. UI display (Feature 3D) — Show suggestions and history.

---

## Shared Infrastructure Notes

### Both Chat and Build Share API Credentials

**Confirmed:** `get_effective_sdk_env()` in `registry.py` (lines 700-788) is the single source of truth for both:
- Build agents: `client.py` line 546
- Workspace chat: `workspace_chat_session.py` line 288
- Assistant chat: `assistant_chat_session.py` line 271

**Rate limit implication:** A heavy build session and a workspace chat session running simultaneously consume from the same rate limit pool. The daily/weekly/monthly usage tracking in workspace chat (`WorkspaceRateLimitEvent`, `get_calibrated_limits()`) does NOT currently account for build agent usage. Feature 3A's storage would enable unified rate limit tracking across both systems.

### Workspace Chat Already Has the Lever Infrastructure

The exact same levers in the user's dashboard already exist in workspace chat:

| User's Dashboard Lever | Workspace Chat Equivalent | Location |
|------------------------|---------------------------|----------|
| Thinking Effort | `cost_settings["effort"]` | `workspace_chat_session.py:81` |
| Max Response Length | `cost_settings["max_tokens"]` | `workspace_chat_session.py:82` |
| Max Turns | `cost_settings["max_turns"]` | `workspace_chat_session.py:83` |
| History Budget | `cost_settings["history_budget"]` | `workspace_chat_session.py:84` |
| Library File Cap | `cost_settings["library_cap"]` | `workspace_chat_session.py:85` |

The validation function `validate_cost_settings()` at `workspace_chat_session.py:99-117` handles clamping and defaults. The build agent presets should use the same validation pattern for consistency.

### Model-Specific Pricing for Cost Estimation

The cost estimation formula needs to account for different models. Current pricing (Feb 2026):

| Model | Input ($/MTok) | Output ($/MTok) | Cache Read | Cache Create |
|-------|---------------|-----------------|------------|--------------|
| Opus 4.6 | $15.00 | $75.00 | $1.50 | $18.75 |
| Sonnet 4.5 | $3.00 | $15.00 | $0.30 | $3.75 |
| Haiku 4.5 | $0.80 | $4.00 | $0.08 | $1.00 |

Store these as a pricing table that can be updated. The model is already available in settings (`registry.py` `DEFAULT_MODEL`), so the cost estimator can select the right rates.

---

## Key File Reference

| File | What Changes | Feature |
|------|-------------|---------|
| `server/schemas.py` | New fields: `build_cost_preset`, `max_build_budget_usd` | 1, 2 |
| `server/routers/settings.py` | Store/retrieve new settings | 1, 2 |
| `ui/src/lib/types.ts` | New TS fields | 1, 2 |
| `ui/src/components/SettingsModal.tsx` | Preset selector + budget text box | 1, 2 |
| `client.py` | Apply preset (effort, max_tokens, max_turns) per agent type | 1 |
| `agent.py` | Budget cap enforcement mid-session + store usage data | 2, 3 |
| `registry.py` | New `BuildSessionUsage` table in registry.db | 3 |
| `server/services/build_cost_analyzer.py` | **NEW** — Analysis and suggestion logic | 3 |
| `server/routers/build_usage.py` | **NEW** — API endpoints for usage data | 3 |

---

## Gotchas

1. **`max_budget_usd` does NOT exist in the SDK.** We must implement cost checking ourselves in the `run_agent_session` loop using per-step `AssistantMessage.usage`. The `break` from the receive loop is the mechanism to stop the agent.

2. **`effort` and `max_tokens` DO exist in `ClaudeAgentOptions`** — confirmed from workspace chat usage at `workspace_chat_session.py:395-396`. These are valid parameters the build agents aren't currently using.

3. **Build usage data is currently discarded.** The variable is prefixed with underscore (`_usage`) at `agent.py` lines 354, 365, 460. Rename to `usage_data` and pass to storage function.

4. **Build agents run as subprocesses.** Database writes from the agent subprocess need their own SQLAlchemy session (the server's session won't be accessible). Use `registry.py`'s `_get_session()` pattern which creates independent sessions.

5. **The cost estimation is an approximation.** `AssistantMessage.usage` gives cumulative input tokens but may not break down cache vs. non-cache perfectly. The `ResultMessage.total_cost_usd` at session end is authoritative. Log both (estimated and actual) so the estimation model can self-calibrate over time.

6. **Rate limit window conflict.** Both chat and build share the same Max plan limits. The learning system should eventually factor in "time of day" and "concurrent chat usage" when suggesting whether to use subscription vs. API billing for the initializer.
