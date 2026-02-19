# Handoff: Configurable Initializer Context Window Threshold

## Background

We just implemented smart billing routing for the initializer agent (`client.py`, `agent.py`). Previously, the initializer **always** used 1M context with API billing. Now it checks the project's `<feature_count>` from app_spec.txt and routes:

- **<=80 features** → 200K context (subscription billing, free)
- **>80 features** → 1M context (API billing)

The threshold of 80 is currently hardcoded. The user wants two UI controls in the Settings modal:

1. **A number input** for the feature threshold (default: 80) — so they can adjust where the cutoff is
2. **A toggle switch** to force 1M context always — an "override" that reverts to the old behavior where the initializer always uses 1M, regardless of feature count

## What Needs to Change

### Files to Modify (7 files)

| File | What to Add |
|------|-------------|
| `server/schemas.py` | Two new fields in `SettingsResponse` and `SettingsUpdate` |
| `server/routers/settings.py` | Read/write the two new settings in GET and PATCH endpoints |
| `ui/src/lib/types.ts` | Two new fields in `Settings` and `SettingsUpdate` interfaces |
| `ui/src/components/SettingsModal.tsx` | Number input + toggle switch UI |
| `client.py` | Replace hardcoded `80` with setting from registry |
| `agent.py` | Replace hardcoded `80` with setting from registry |
| `registry.py` | Nothing — uses existing key-value Settings table, no schema changes needed |

---

## Detailed Changes Per File

### 1. `server/schemas.py` — Pydantic Models

**`SettingsResponse`** (line ~872-894): Add two fields:

```python
initializer_context_threshold: int = 80       # Feature count threshold (default 80)
force_1m_context: bool = False                 # When True, always use 1M for initializer
```

**`SettingsUpdate`** (line ~896-916): Add two optional fields + validators:

```python
initializer_context_threshold: int | None = None
force_1m_context: bool | None = None

@field_validator('initializer_context_threshold')
@classmethod
def validate_initializer_context_threshold(cls, v: int | None) -> int | None:
    if v is not None and (v < 10 or v > 500):
        raise ValueError("initializer_context_threshold must be between 10 and 500")
    return v
```

The range 10-500 covers everything from tiny apps to the "advanced tier" (405 features).

### 2. `server/routers/settings.py` — API Endpoints

**`get_settings()`** (line ~108-142): Add to the `SettingsResponse(...)` return:

```python
initializer_context_threshold=_parse_int(all_settings.get("initializer_context_threshold"), 80),
force_1m_context=_parse_bool(all_settings.get("force_1m_context"), False),
```

`_parse_int` and `_parse_bool` already exist in this file (lines 81-95).

**`update_settings()`** (line ~145-250): Add to the update logic:

```python
if update.initializer_context_threshold is not None:
    set_setting("initializer_context_threshold", str(update.initializer_context_threshold))
if update.force_1m_context is not None:
    set_setting("force_1m_context", "true" if update.force_1m_context else "false")
```

Also add the same two fields to the **second** `SettingsResponse(...)` return at the bottom of `update_settings()` (lines ~226-250).

### 3. `ui/src/lib/types.ts` — TypeScript Types

**`Settings` interface** (line 872-894): Add:

```typescript
initializer_context_threshold: number  // Feature count threshold for 200K→1M switch
force_1m_context: boolean              // Override: always use 1M context for initializer
```

**`SettingsUpdate` interface** (line 896-916): Add:

```typescript
initializer_context_threshold?: number
force_1m_context?: boolean
```

### 4. `ui/src/components/SettingsModal.tsx` — UI Controls

**Add handlers** (after the existing handlers around lines 43-83):

```typescript
const handleInitializerThresholdChange = (value: number) => {
  if (!updateSettings.isPending) {
    updateSettings.mutate({ initializer_context_threshold: value })
  }
}

const handleForce1MToggle = () => {
  if (settings && !updateSettings.isPending) {
    updateSettings.mutate({ force_1m_context: !settings.force_1m_context })
  }
}
```

**Add UI controls.** These should go in the settings content area. The existing pattern for toggles is a switch/checkbox (see `handleYoloToggle` at line 43). For the number input, the user specifically asked for a **text box** where they can type any number, not preset buttons. Something like:

```tsx
{/* Context Window Settings */}
<div className="space-y-4">
  <h3 className="font-semibold">Initializer Context Window</h3>

  {/* Force 1M toggle */}
  <div className="flex items-center justify-between">
    <div>
      <Label className="font-medium">Always Use 1M Context</Label>
      <p className="text-sm text-muted-foreground">
        Override smart routing — always use 1M context (API billing) for initializer
      </p>
    </div>
    <Switch
      checked={settings.force_1m_context}
      onCheckedChange={handleForce1MToggle}
      disabled={isSaving}
    />
  </div>

  {/* Threshold input — disabled when force_1m is on */}
  <div className="space-y-2">
    <Label className="font-medium">Feature Count Threshold</Label>
    <p className="text-sm text-muted-foreground">
      Projects with fewer features than this use 200K context (subscription).
      Projects with more use 1M context (API billing). Default: 80.
    </p>
    <Input
      type="number"
      min={10}
      max={500}
      value={settings.initializer_context_threshold ?? 80}
      onChange={(e) => handleInitializerThresholdChange(Number(e.target.value))}
      disabled={isSaving || settings.force_1m_context}
      className="w-24"
    />
  </div>
</div>
```

When `force_1m_context` is on, the threshold input should be visually disabled since it's irrelevant.

### 5. `client.py` — Read Setting Instead of Hardcoded Value

**Current code at line 530:**

```python
INITIALIZER_200K_FEATURE_THRESHOLD = 80
```

**Replace with:**

```python
from registry import get_setting

# Read user-configurable threshold (default: 80 features)
force_1m = get_setting("force_1m_context", "false").lower() == "true"

if force_1m:
    # User wants 1M always — skip feature count check
    use_api_billing = True
    print("   - Initializer routing: forced 1M context (override enabled)")
else:
    threshold_str = get_setting("initializer_context_threshold", "80")
    try:
        threshold = int(threshold_str)
    except ValueError:
        threshold = 80

    feature_count = _extract_feature_count_from_spec(project_dir)
    if feature_count is not None and feature_count <= threshold:
        use_api_billing = False
        print(f"   - Initializer routing: {feature_count} features <= {threshold} threshold")
        # ... existing estimation print ...
    else:
        use_api_billing = True
        # ... existing print ...
```

**Note:** `get_setting()` is already importable from `registry.py` (line 555). It returns `str | None` with a default. The `from registry import get_effective_sdk_env` import already exists on line 527, so just add `get_setting` to it.

### 6. `agent.py` — Read Setting for Context Window Detection

**Current code at line 342-343:**

```python
_fc = _extract_feature_count_from_spec(project_dir)
session_context_window = CONTEXT_1M if (_fc is None or _fc > 80) else CONTEXT_200K
```

**Replace with:**

```python
from registry import get_setting

force_1m = get_setting("force_1m_context", "false").lower() == "true"
if force_1m:
    session_context_window = CONTEXT_1M
else:
    threshold_str = get_setting("initializer_context_threshold", "80")
    try:
        threshold = int(threshold_str)
    except ValueError:
        threshold = 80
    _fc = _extract_feature_count_from_spec(project_dir)
    session_context_window = CONTEXT_1M if (_fc is None or _fc > threshold) else CONTEXT_200K
```

This must stay in sync with the `client.py` logic — both files need to agree on the context window size.

---

## How Settings Flow (Reference)

The existing pattern for settings:

1. **User clicks in UI** → `updateSettings.mutate({ key: value })`
2. **React Query** → `PATCH /api/settings` with JSON body
3. **FastAPI endpoint** → calls `set_setting(key, str(value))` from registry.py
4. **SQLite** → stored in `settings` table as key-value pair
5. **Agent startup** → `client.py` calls `get_setting(key)` from registry.py
6. **Applied** → routing decision uses the value

Settings are read fresh on every agent session start (every `create_client()` call), so changes take effect on the next session without restart.

---

## Testing

1. **API test:** `curl -X PATCH http://localhost:8080/api/settings -H 'Content-Type: application/json' -d '{"initializer_context_threshold": 100}'`
2. **API test:** `curl -X PATCH http://localhost:8080/api/settings -H 'Content-Type: application/json' -d '{"force_1m_context": true}'`
3. **Verify GET:** `curl http://localhost:8080/api/settings | jq '.initializer_context_threshold, .force_1m_context'`
4. **Run initializer with small project** — should see `Billing: Subscription (200K context)` in logs
5. **Toggle force_1m on** — re-run, should see `Billing: API key (1M context)` regardless of feature count
6. **Change threshold to 10** — a project with 15 features should now route to 1M

---

## Key Gotcha

Both `client.py` and `agent.py` independently determine the context window size. They **must** use the same logic and the same settings, otherwise the real-time token alerts in `agent.py` will fire at wrong thresholds relative to what `client.py` actually configured.
