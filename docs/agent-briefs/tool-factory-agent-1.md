# Agent Brief 1: Data Models + Blueprint Engine + PRD Input Path

**Phases:** 1 + 2 from `docs/prd-video-to-tool-factory.md`
**Scope:** All backend Python — no React, no UI
**Estimated Tokens:** ~55-65k
**Dependencies:** None (this agent goes first)
**Must Complete Before:** Agents 2, 3, and 4

---

## ARCHITECTURE CONTEXT (read this first)

### What This System Is
A pipeline that turns YouTube video strategies (or uploaded PRDs) into deployable Google Sheets automation tools. The existing **YT Lab** (already built) handles stages 1-2: ingesting YouTube videos and extracting strategy steps. **This agent builds stage 3**: transforming those extracted steps into a deployable blueprint.

### 5-Stage Pipeline
```
[1] Ingest    → YouTube URL → transcript, metadata, screenshots     ← BUILT (yt_ingestion.py)
[2] Extract   → transcript → YTStrategyStep[] (structured steps)    ← BUILT (yt_processor.py)
[3] Blueprint → YTStrategyStep[] → SheetBlueprint (chain config)    ← THIS AGENT BUILDS THIS
[4] Deploy    → SheetBlueprint → actual Google Sheet (5 tabs)       ← Agent 2
[5] Manage    → browse, re-theme, batch, analytics                  ← Agents 3+4
```

### Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic models, async/await
- **AI:** Claude Sonnet 4.6 for prompt conversion (the ONE agent step in this brief)
- **Storage:** JSON files at `~/.autoforge/` (tool_registry.json, prd_uploads/)
- **Existing patterns to follow:** `server/services/rate_limit_logger.py` (atomic file writes), `server/routers/yt_processing.py` (SSE streaming), `server/services/yt_processor.py` (Claude API calls)

### How YTStrategyStep[] Becomes a Tool
Each video step gets classified (RESEARCH/GENERATION/ACTION/MANUAL), scanned for APIs, wired into a chain (step 1 output feeds step 2 input), and prompts get converted from conversational ("now take that research and...") to structured chain format ("You are executing Step 2 of 9..."). The result is a `SheetBlueprint` that Agent 2's deployer can turn into a real Google Sheet.

### The Cody Schneider Example (how it works in practice)
A YouTube video "How to Set Up a Meta Ads Pipeline" has 10 steps extracted by YT Lab. This agent's blueprint engine:
1. Filters out step 10 (documentation, not executable) → 9 chain rows
2. Classifies: steps 1-3 = RESEARCH, steps 4-7 = GENERATION, step 8 = ACTION (upload to Meta), step 9 = MANUAL (review results)
3. Detects APIs: Meta Marketing API (from "facebook ads" in prompts), OpenAI (from "gpt" mentions)
4. Extracts variables: {niche}, {budget}, {target_audience}
5. Wires chain: row 1 input = user_input, row 2 input = row_1, etc.
6. Converts prompts: "Now take that ICP data and generate ad copy" → "You are executing Step 4 of 9. Using the ICP research from {{row_3_output}}, generate 40 ad copy variations for {{niche}}..."
7. Assembles SheetBlueprint with all 9 rows + detected APIs + variables

### PRD Input Path (NEW addition)
The original pipeline only accepts YouTube videos. This agent adds a second entry point: upload a PRD document (markdown/text), Claude extracts structured steps, and the same blueprint engine processes them. One [AGENT] call to parse the PRD, then all [ROBOT] steps from there.

---

## STRIPE MINIONS CONTEXT

Every function in this brief is labeled **[ROBOT]** or **[AGENT]**.

- **[ROBOT]** = Deterministic Python code. No LLM calls. Zero tokens. Must work perfectly every time.
- **[AGENT]** = Requires Claude API call. Has hallucination risk. Needs error handling, retries, output validation.

The goal: maximize [ROBOT] steps. LLM calls are expensive and non-deterministic. Use them only where creative judgment is required.

---

## WHAT TO BUILD

### Phase 1: Data Models + Tool Registry

#### 1.1 `server/models/tool_factory.py` — [ROBOT] (entire file)

Create all Pydantic data models. This is pure Python — no AI, no API calls.

**Enums:**
```python
class StepType(str, Enum):        # research, generation, action, manual
class ToolStatus(str, Enum):      # draft, deploying, active, error, archived
class ThemeSource(str, Enum):     # preset, extracted, custom
class IngestionSource(str, Enum): # youtube, prd_upload, manual  ← NEW for PRD input path
```

**Theme Models:**
```python
class ThemeColors(BaseModel):       # 13 color fields (brand_light → status_warning)
class ThemeTypography(BaseModel):   # 5 fields (font families, weights, base size)
class ThemeComponents(BaseModel):   # 6 fields (radii, shadow, spacing, density)
class ThemeConfig(BaseModel):       # Universal theme — convergence point for all theme paths
```

**Chain Config Models:**
```python
class DetectedAPI(BaseModel):       # service_name, service_key, detection_pattern, signup_url, env_vars
class ChainConfigRow(BaseModel):    # One row in the generated Google Sheet's chain tab
class SheetBlueprint(BaseModel):    # Complete blueprint for a Google Sheet tool
```

**Tool Registry Models:**
```python
class GeneratedTool(BaseModel):     # A generated tool with status, sheet details, theme, stats
class ToolRegistry(BaseModel):      # Root model — list of tools + aggregate stats
```

**PRD Input Models (NEW — not in original PRD):**
```python
class PRDUpload(BaseModel):
    """A PRD document uploaded directly instead of YouTube video."""
    prd_id: str                     # Unique ID
    filename: str                   # Original filename
    content: str                    # Raw markdown/text content
    source: Literal["upload"] = "upload"
    uploaded_at: str

class PRDExtractionResult(BaseModel):
    """Result of extracting steps from a PRD document."""
    project_name: str
    project_description: str
    niche: str
    tags: list[str]
    steps: list[dict]               # Same shape as YTStrategyStep for pipeline compatibility
    extraction_model: str           # Which Claude model did the extraction
    extraction_time: float          # Seconds
```

Copy ALL model code from the PRD (§1.1, lines 319-518). The PRD has the complete Pydantic code ready to paste.

**Add `IngestionSource` to `SheetBlueprint`:**
```python
class SheetBlueprint(BaseModel):
    # ... existing fields from PRD ...
    ingestion_source: IngestionSource = IngestionSource.YOUTUBE  # NEW
    source_prd_id: str | None = None  # NEW — set when source is PRD upload
```

#### 1.2 TypeScript Types — Edit `ui/src/lib/types.ts` — [ROBOT]

Add all TypeScript interfaces from PRD §1.2 (lines 520-630). Pure type definitions, no logic.

Add these extra types for PRD input:
```typescript
export type IngestionSource = 'youtube' | 'prd_upload' | 'manual'

export interface PRDUpload {
  prd_id: string
  filename: string
  content: string
  source: 'upload'
  uploaded_at: string
}

export interface PRDExtractionResult {
  project_name: string
  project_description: string
  niche: string
  tags: string[]
  steps: YTProcessStepData[]  // Same shape — pipeline compatibility
  extraction_model: string
  extraction_time: number
}
```

#### 1.3 Tool Registry Service — `server/services/tool_registry.py` — [ROBOT] (entire file)

All CRUD operations on `~/.autoforge/tool_registry.json`. Pure file I/O, no LLM calls.

**Methods (all [ROBOT]):**
| Method | What It Does | Robot/Agent |
|--------|-------------|-------------|
| `__init__(registry_path)` | Set file path, create if missing | [ROBOT] |
| `create_tool(blueprint)` | Generate ID, add to registry, save | [ROBOT] |
| `get_tool(tool_id)` | Lookup by ID | [ROBOT] |
| `list_tools(status, limit, offset)` | Filter and paginate | [ROBOT] |
| `update_tool(tool_id, **updates)` | Partial update, save | [ROBOT] |
| `update_theme(tool_id, theme)` | Swap theme on tool | [ROBOT] |
| `archive_tool(tool_id)` | Set status=archived | [ROBOT] |
| `record_run(tool_id, tokens_used)` | Increment counters | [ROBOT] |
| `get_stats()` | Aggregate counts | [ROBOT] |
| `_load()` | Read JSON, parse to ToolRegistry | [ROBOT] |
| `_save(registry)` | Atomic write (.tmp → rename) | [ROBOT] |

**File safety pattern:** Same as `rate_limit_logger.py` — write to `.tmp`, `os.replace()` for atomic swap.

#### 1.4 Tool Factory Router (Registry Endpoints Only) — `server/routers/tool_factory.py` — [ROBOT]

Thin REST layer. 4 endpoints for Phase 1:

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `GET` | `/api/tool-factory/tools` | List tools (filterable by status) | [ROBOT] |
| `GET` | `/api/tool-factory/tools/{tool_id}` | Get single tool | [ROBOT] |
| `DELETE` | `/api/tool-factory/tools/{tool_id}` | Archive a tool | [ROBOT] |
| `GET` | `/api/tool-factory/stats` | Aggregate statistics | [ROBOT] |

Register router in `server/main.py`.

---

### Phase 2: Blueprint Engine

#### 2.1 Blueprint Generator — `server/services/sheet_blueprint.py`

This is the brain. It transforms `YTStrategyStep[]` (or PRD-extracted steps) → `SheetBlueprint`.

**Pipeline:**
```
Input (YTStrategyStep[] or PRD steps)
    ↓
[1] filter_and_validate()        [ROBOT] — remove empty/invalid steps
    ↓
[2] classify_step()              [ROBOT] — assign StepType via keyword matching
    ↓
[3] detect_apis()                [ROBOT] — scan prompts for service mentions
    ↓
[4] extract_user_variables()     [ROBOT] — regex for {variable} patterns
    ↓
[5] compute_input_source()       [ROBOT] — wire step-to-step references
    ↓
[6] convert_prompts()            [AGENT] — Claude Sonnet rewrites video-style → chain format
    ↓
[7] assemble_blueprint()         [ROBOT] — combine all into SheetBlueprint
    ↓
Output: SheetBlueprint
```

**Function-by-function breakdown:**

| Function | Robot/Agent | Token Cost | Details |
|----------|-------------|------------|---------|
| `filter_and_validate(steps)` | [ROBOT] | 0 | Remove steps with empty title/prompt, validate required fields |
| `classify_step(step) → StepType` | [ROBOT] | 0 | Keyword matching: ACTION > MANUAL > GENERATION > RESEARCH. Code in PRD §2.3 |
| `detect_apis(steps) → list[DetectedAPI]` | [ROBOT] | 0 | Pattern matching against 13 service configs. Code in PRD §2.5 |
| `extract_user_variables(steps) → list[str]` | [ROBOT] | 0 | Regex `\{(\w+)\}` across all prompts. Code in PRD §2.6 |
| `compute_input_source(row, step, all_steps) → str` | [ROBOT] | 0 | Chain wiring logic. Code in PRD §2.4 |
| `detect_prior_references(prompt, row_number) → list[int]` | [ROBOT] | 0 | Find "step N", "row N", "previous" references in text |
| `convert_single_prompt(original, context) → str` | [AGENT] | ~1-2k/step | Claude Sonnet converts video-style prompt → chain-executable prompt. PRD §2.2 |
| `convert_prompts(steps, tool_name) → list[str]` | [AGENT] | ~10-20k total | Batch wrapper — calls convert_single_prompt for each step |
| `assemble_blueprint(project, steps, ...) → SheetBlueprint` | [ROBOT] | 0 | Combine all computed fields into final SheetBlueprint |
| `generate_blueprint(project, steps, ...) → SheetBlueprint` | Mixed | ~10-20k | Main entry point — orchestrates the full pipeline |

**API Detection Patterns (13 services) — [ROBOT]:**
Copy the full `API_PATTERNS` dict from PRD §2.5 (lines 784-863). Pure Python dict, zero tokens.

**Step Classification Signals — [ROBOT]:**
Copy `ACTION_SIGNALS`, `MANUAL_SIGNALS`, `GENERATION_SIGNALS` from PRD §2.3 (lines 746-761).

#### 2.2 Smart Prompt Conversion — [AGENT]

This is the ONE function that needs Claude. Use Sonnet (cheap, fast).

```python
async def convert_single_prompt(
    original_prompt: str,
    step_number: int,
    total_steps: int,
    tool_name: str,
    expected_output: str,
) -> str:
    """[AGENT] Convert a video-style prompt to a chain-executable prompt.

    Uses Claude Sonnet. ~1-2k tokens per call.
    Includes retry logic (max 2 retries) and output validation.
    """
```

**System prompt for conversion** (from PRD §2.2):
```
Given this video-extracted step prompt:
"{original_prompt}"

Convert it to a structured chain prompt that:
1. Is self-contained (doesn't reference "the video" or "what we just did")
2. Uses {{previousOutput}} to reference the prior step's result
3. Uses {{variable_name}} for user-configurable inputs
4. Specifies the expected output format clearly
5. Is under 500 words

Return ONLY the converted prompt, no explanation.
```

**Error handling:**
- If Claude returns empty → retry once with "Please provide the converted prompt"
- If Claude returns > 500 words → truncate and add format instruction
- If API error → return original prompt with `[UNCONVERTED]` prefix (don't block the pipeline)

#### 2.3 Blueprint Generation Endpoints — add to `server/routers/tool_factory.py`

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `POST` | `/api/tool-factory/generate` | Generate blueprint from YT Lab project ID | Mixed (calls [AGENT] for prompt conversion) |
| `POST` | `/api/tool-factory/generate-stream` | Same with SSE progress events | Mixed |
| `POST` | `/api/tool-factory/generate-from-prd` | Generate blueprint from uploaded PRD | Mixed |

#### 2.4 PRD Input Path (NEW — "From PRD" Direct Input) — `server/services/prd_ingestion.py`

This is the alternative to YouTube ingestion. User uploads a PRD document, Claude extracts structured steps.

| Function | Robot/Agent | Token Cost | Details |
|----------|-------------|------------|---------|
| `validate_prd_content(content) → bool` | [ROBOT] | 0 | Check minimum length, not empty, not binary |
| `extract_steps_from_prd(content, user_context) → PRDExtractionResult` | [AGENT] | ~3-5k | Claude reads PRD, outputs structured steps |
| `normalize_prd_steps(raw_steps) → list[YTStrategyStep-compatible]` | [ROBOT] | 0 | Convert Claude output to same format as YT Lab steps |
| `save_prd_upload(filename, content) → PRDUpload` | [ROBOT] | 0 | Persist to `~/.autoforge/prd_uploads/` |

**PRD extraction prompt for Claude:**
```
You are analyzing a Product Requirements Document (PRD). Extract a structured implementation plan.

PRD Content:
{content}

User Context (optional):
{user_context}

Return a JSON object with:
{
  "project_name": "short name for this project",
  "project_description": "one paragraph summary",
  "niche": "industry/domain",
  "tags": ["tag1", "tag2"],
  "steps": [
    {
      "order": 1,
      "title": "Step title",
      "description": "What this step does",
      "prompt": "Detailed prompt for executing this step",
      "expectedOutput": "What the step should produce",
      "notes": "Implementation notes",
      "model": "sonnet"
    }
  ]
}

Rules:
- Extract 5-20 actionable steps
- Each step should be independently executable
- Order steps by dependency (earlier steps feed later ones)
- Use "opus" model only for steps requiring deep reasoning
- Use "sonnet" for everything else
```

#### 2.5 PRD Upload Endpoint — add to `server/routers/tool_factory.py`

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `POST` | `/api/tool-factory/upload-prd` | Upload PRD file, extract steps, return structured result | Mixed |

Accepts `multipart/form-data` with a `.md` or `.txt` file. Also accepts raw JSON body with `content` field for paste-in PRDs.

---

## FILES TO CREATE/MODIFY

| File | Action | Phase |
|------|--------|-------|
| `server/models/tool_factory.py` | **Create** | 1 |
| `server/services/tool_registry.py` | **Create** | 1 |
| `server/services/sheet_blueprint.py` | **Create** | 2 |
| `server/services/prd_ingestion.py` | **Create** | 2 |
| `server/routers/tool_factory.py` | **Create** | 1+2 |
| `ui/src/lib/types.ts` | **Edit** (append TS interfaces) | 1 |
| `server/main.py` | **Edit** (register new router) | 1 |
| `requirements.txt` | **No changes** (all deps already installed) | — |

---

## TEST PLAN

Every test is a [ROBOT] — pure Python assertions, no LLM calls in tests.

### Unit Tests — `tests/test_tool_factory_models.py`

| Test | What It Validates |
|------|-------------------|
| `test_step_type_enum_values` | All 4 StepType values exist |
| `test_tool_status_lifecycle` | Status transitions are valid |
| `test_theme_config_creation` | ThemeConfig from both preset and extracted sources |
| `test_chain_config_row_defaults` | Default values (max_retries=1, timeout=120, is_gate=False) |
| `test_sheet_blueprint_serialization` | Blueprint → JSON → Blueprint roundtrip |
| `test_generated_tool_defaults` | New tool starts as DRAFT with zero stats |
| `test_prd_upload_model` | PRDUpload model validates correctly |
| `test_ingestion_source_enum` | All 3 sources (youtube, prd_upload, manual) |

### Unit Tests — `tests/test_tool_registry.py`

| Test | What It Validates |
|------|-------------------|
| `test_create_tool` | Creates tool, assigns ID, persists to file |
| `test_get_tool_exists` | Returns correct tool by ID |
| `test_get_tool_missing` | Returns None for unknown ID |
| `test_list_tools_all` | Returns all tools |
| `test_list_tools_by_status` | Filters by status correctly |
| `test_list_tools_pagination` | limit/offset work |
| `test_update_tool` | Partial update works, updated_at changes |
| `test_update_theme` | Theme swap persists |
| `test_archive_tool` | Status changes to ARCHIVED |
| `test_record_run` | times_run increments, last_run_at updates |
| `test_get_stats` | Aggregates match manual count |
| `test_atomic_save` | File isn't corrupted on concurrent writes |

### Unit Tests — `tests/test_sheet_blueprint.py`

| Test | What It Validates |
|------|-------------------|
| `test_classify_step_action` | "upload to Meta" → ACTION |
| `test_classify_step_manual` | "review and approve" → MANUAL |
| `test_classify_step_generation` | "generate 40 ad variations" → GENERATION |
| `test_classify_step_default_research` | "analyze competitors" → RESEARCH (default) |
| `test_detect_apis_meta` | "facebook ads" triggers Meta detection |
| `test_detect_apis_multiple` | Step mentioning 3 services detects all 3 |
| `test_detect_apis_none` | Generic step returns empty list |
| `test_extract_variables` | "{niche}" and "{budget}" found in prompts |
| `test_extract_variables_skips_system` | "{previousOutput}" not included |
| `test_compute_input_source_first` | Row 1 → "user_input" |
| `test_compute_input_source_chain` | Row 3 → "row_2" |
| `test_compute_input_source_multi` | Step referencing rows 1+3 → "row_1+row_3" |
| `test_filter_and_validate` | Empty steps removed, valid steps kept |
| `test_assemble_blueprint` | All fields populated correctly |

### Unit Tests — `tests/test_prd_ingestion.py`

| Test | What It Validates |
|------|-------------------|
| `test_validate_prd_too_short` | Content under 50 chars rejected |
| `test_validate_prd_valid` | Normal markdown passes |
| `test_normalize_prd_steps` | Raw dict → YTStrategyStep-compatible format |
| `test_save_prd_upload` | File persisted to correct path |

### Integration Test — `tests/test_blueprint_integration.py`

| Test | What It Validates |
|------|-------------------|
| `test_full_pipeline_mock_steps` | 5 mock YTStrategyStep objects → SheetBlueprint with correct chain wiring |
| `test_blueprint_from_prd_mock` | Mock PRD content → extraction → blueprint (uses mock Claude response) |
| `test_registry_endpoint_crud` | FastAPI TestClient: create → list → get → archive |

### How to Run Tests
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
python -m pytest tests/test_tool_factory_models.py tests/test_tool_registry.py tests/test_sheet_blueprint.py tests/test_prd_ingestion.py tests/test_blueprint_integration.py -v
```

---

## EXISTING CODE REFERENCES

The agent should read these files to understand patterns:

| File | Why |
|------|-----|
| `server/services/rate_limit_logger.py` | Same atomic file write pattern for tool_registry.py |
| `server/routers/yt_processing.py` | Same SSE streaming pattern for generate-stream endpoint |
| `server/services/yt_processor.py` | Same Claude API call pattern for prompt conversion |
| `server/models/` (any existing) | Pydantic model conventions used in this project |
| `ui/src/lib/types.ts` | Where to append TypeScript interfaces (look for existing patterns) |
| `server/main.py` | Where to register the new router |

---

## ACCEPTANCE CRITERIA

1. All [ROBOT] functions work with zero LLM calls
2. `generate_blueprint()` takes mock YTStrategyStep[] and returns valid SheetBlueprint
3. PRD upload endpoint accepts markdown, returns structured steps
4. Tool registry persists across server restarts (JSON file)
5. All unit tests pass
6. `ruff check .` passes on all new files
7. TypeScript types added to `ui/src/lib/types.ts` without breaking existing types
8. Router registered and server starts without errors
