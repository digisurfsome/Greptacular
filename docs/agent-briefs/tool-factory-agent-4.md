# Agent Brief 4: Batch Processing + SaaS Layer

**Phases:** 7 + 8 from `docs/prd-video-to-tool-factory.md`
**Scope:** Backend Python + one React dashboard component
**Estimated Tokens:** ~35-45k
**Dependencies:** Agents 1, 2, and 3 must be complete
**Runs Last:** Needs blueprint engine, deployer, tool registry, and UI all working

---

## ARCHITECTURE CONTEXT (read this first)

### What This System Is
A pipeline that turns YouTube video strategies (or PRDs) into Google Sheets automation tools. Agents 1-3 built the core: data models, blueprint engine, theme integration, Google Sheets deployer, and the full React UI. **This agent adds batch processing** (generate multiple tools at once) **and SaaS usage tracking** (tier limits, analytics).

### Where This Agent Fits
```
[1-2] Ingest + Extract    ← BUILT (YT Lab)
[3]   Blueprint Engine     ← Agent 1 BUILT
[4]   Theme + Deploy       ← Agent 2 BUILT
[5-6] UI                   ← Agent 3 BUILT
[7]   Batch Processing     ← THIS AGENT
[8]   SaaS Layer           ← THIS AGENT
```

### Batch Processing Context
- Single tool generation works end-to-end (Agents 1+2)
- Batch = run that same pipeline for multiple projects sequentially
- **Google Sheets API quota: 100 requests per 100 seconds per user** — this is why batch is sequential, not parallel
- Each tool deployment uses 3-4 API calls, so ~25 tools per 100-second window is safe
- Follow the same pattern as existing `server/routers/yt_batch.py` — in-memory batch state, progress callbacks, per-item error isolation

### SaaS Tier Model
| Tier | Price | Tools/Month | Features |
|------|-------|-------------|----------|
| **Free** | $0 | 5 | Basic generation, 3 preset themes, no batch |
| **Pro** | $29/mo | Unlimited | All themes, image-to-theme, batch generation |
| **Enterprise** | $99/mo | Unlimited | White-label, custom themes, API access, team sharing |

Unit economics: ~$0.02-0.05 per tool generation (Sonnet tokens + Sheets API). Pro user at 100 tools/month = $29 revenue vs ~$5 cost = 83% margin.

### Storage Pattern
All data persists to JSON files in `~/.autoforge/` with atomic writes (write `.tmp`, `os.replace()` for swap). Same pattern used by:
- `tool_registry.py` (Agent 1) → `~/.autoforge/tool_registry.json`
- `rate_limit_logger.py` (existing) → `~/.autoforge/rate_limit_log.json`
- This agent adds `tool_usage.py` → `~/.autoforge/tool_usage.json`

### Services Available From Other Agents
- **`server/services/sheet_blueprint.py`** (Agent 1) — `generate_blueprint()` takes project + steps → SheetBlueprint
- **`server/services/sheet_deployer.py`** (Agent 2) — `deploy_sheet()` takes blueprint + theme → Google Sheet
- **`server/services/tool_registry.py`** (Agent 1) — tool CRUD, `record_run()`, `get_stats()`
- **`ui/src/components/tool-factory/ToolManagerPage.tsx`** (Agent 3) — add Analytics tab/section here
- **`ui/src/hooks/useToolFactory.ts`** (Agent 3) — add usage + batch hooks here

### Note on user_id
This is currently a single-user local app. Use `user_id = "local"` as default everywhere. The data model supports multi-user for future SaaS deployment, but don't build auth infrastructure — just make the field exist.

---

## STRIPE MINIONS CONTEXT

- **[ROBOT]** = Deterministic Python code. No LLM calls. Zero tokens. Must work perfectly every time.
- **[AGENT]** = Requires Claude API call. Has hallucination risk. Needs error handling, retries, output validation.

**This entire agent is [ROBOT].** Batch processing is orchestration logic. SaaS tracking is counter arithmetic. The analytics dashboard is pure React. Zero LLM calls.

---

## WHAT TO BUILD

### Phase 7: Batch Processing

#### 7.1 Batch Tool Generator — `server/services/batch_tool_generator.py` — [ROBOT] (entire file)

Orchestrates generating multiple tools from a list of YT Lab project IDs (or PRD uploads).

```python
class BatchToolGenerator:
    """[ROBOT] Generate tools from multiple projects in sequence.

    Sequential processing to avoid Google Sheets API quota issues.
    One failure doesn't stop the batch — errors are logged per-tool.
    """

    def __init__(
        self,
        blueprint_service: SheetBlueprintService,  # From Agent 1
        deployer: SheetDeployer,                    # From Agent 2
        registry: ToolRegistryService,              # From Agent 1
    ): ...
```

**Methods (all [ROBOT]):**

| Method | What It Does | Robot/Agent |
|--------|-------------|-------------|
| `generate_batch(project_ids, default_theme, auto_deploy, on_progress)` | Main entry. Loops through projects, generates blueprint for each, optionally deploys. Returns list of GeneratedTool. | [ROBOT] |
| `_process_single(project_id, theme) → GeneratedTool` | Generate blueprint + optionally deploy for one project. Catches errors per-tool. | [ROBOT] (orchestration) |
| `get_batch_status(batch_id) → BatchStatus` | Returns current progress of a running batch. | [ROBOT] |
| `cancel_batch(batch_id) → bool` | Sets cancel flag, current tool finishes but no more start. | [ROBOT] |

**Batch state model:**
```python
class BatchStatus(BaseModel):
    batch_id: str
    total: int
    completed: int
    failed: int
    current_tool: str | None        # Name of tool currently being processed
    status: Literal["running", "completed", "cancelled", "error"]
    results: list[BatchToolResult]   # Per-tool results
    started_at: str
    completed_at: str | None

class BatchToolResult(BaseModel):
    project_id: str
    tool_id: str | None             # None if failed
    tool_name: str
    status: Literal["success", "error", "skipped"]
    error: str | None
    sheet_url: str | None           # None if not auto-deployed
    duration_seconds: float
```

**Processing rules:**
1. Sequential — one tool at a time (Google Sheets API quota: 100 req/100sec)
2. Per-tool error isolation — one failure logs the error, continues to next
3. Progress callback fires after each tool completes (for SSE streaming)
4. Default theme applied to all tools unless individually overridden
5. Auto-deploy is optional — can generate blueprints only, deploy later
6. Batch state stored in-memory (like existing `yt_batch.py` pattern)

#### 7.2 Batch Endpoints — add to `server/routers/tool_factory.py` — [ROBOT]

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `POST` | `/api/tool-factory/batch/generate` | Start batch generation from project IDs | [ROBOT] |
| `GET` | `/api/tool-factory/batch/{batch_id}` | Poll batch progress | [ROBOT] |
| `POST` | `/api/tool-factory/batch/deploy` | Deploy all draft tools in a batch | [ROBOT] |
| `POST` | `/api/tool-factory/batch/cancel/{batch_id}` | Cancel a running batch | [ROBOT] |

**Request/Response models:**
```python
class BatchGenerateRequest(BaseModel):
    project_ids: list[str]          # 1-50 project IDs
    default_theme_id: str | None    # Applied to all tools
    auto_deploy: bool = False       # If True, deploy each tool after generation

class BatchGenerateResponse(BaseModel):
    batch_id: str
    total: int
    status: str                     # "running"
```

#### 7.3 Queue Integration (Optional) — [ROBOT]

If the Factory Task Queue ("The Train") exists, batch generation integrates as a task type:

```python
# Only implement this if task queue infrastructure exists
# Check for: server/services/task_queue.py or similar

TOOL_GENERATION_TASK_TYPE = "tool_generation"

def create_batch_task(project_ids: list[str], theme_id: str | None) -> dict:
    """[ROBOT] Create a task queue entry for batch tool generation."""
    return {
        "type": TOOL_GENERATION_TASK_TYPE,
        "payload": {"project_ids": project_ids, "theme_id": theme_id},
    }
```

If the task queue doesn't exist yet, skip this — the direct batch endpoint is sufficient.

---

### Phase 8: SaaS Layer

#### 8.1 Usage Tracker — `server/services/tool_usage.py` — [ROBOT] (entire file)

Tracks tool generation and execution counts for future SaaS tier enforcement.

```python
class ToolUsageTracker:
    """[ROBOT] Track per-user tool usage for SaaS tier limits.

    Storage: ~/.autoforge/tool_usage.json
    Same atomic file pattern as tool_registry.py and rate_limit_logger.py.
    """
```

**Methods (all [ROBOT]):**

| Method | What It Does | Robot/Agent |
|--------|-------------|-------------|
| `record_generation(user_id, tool_id)` | Increment monthly generation count | [ROBOT] |
| `record_execution(user_id, tool_id, tokens)` | Increment execution count + token total | [ROBOT] |
| `get_monthly_usage(user_id) → MonthlyUsage` | Returns current month's counts | [ROBOT] |
| `get_all_time_usage(user_id) → AllTimeUsage` | Returns lifetime totals | [ROBOT] |
| `check_tier_limit(user_id, tier) → bool` | Returns True if under limit | [ROBOT] |
| `get_usage_history(user_id, months) → list[MonthlyUsage]` | Historical monthly data | [ROBOT] |

**Tier limits:**
```python
TIER_LIMITS = {
    "free":       {"tools_per_month": 5,  "themes": ["preset_only"], "batch": False,  "api_access": False},
    "pro":        {"tools_per_month": -1, "themes": ["all"],         "batch": True,   "api_access": False},
    "enterprise": {"tools_per_month": -1, "themes": ["all"],         "batch": True,   "api_access": True},
}
```

**Usage data model:**
```python
class MonthlyUsage(BaseModel):
    month: str                      # "2026-03"
    tools_generated: int
    tools_deployed: int
    chain_executions: int
    tokens_used: int
    themes_extracted: int           # Image-to-theme uses

class AllTimeUsage(BaseModel):
    total_tools_generated: int
    total_tools_deployed: int
    total_chain_executions: int
    total_tokens_used: int
    first_generation_at: str | None
    last_generation_at: str | None

class UsageRecord(BaseModel):
    user_id: str
    tier: str
    monthly_history: list[MonthlyUsage]
    all_time: AllTimeUsage
```

**Storage:** `~/.autoforge/tool_usage.json` — same atomic write pattern as everything else.

**Note:** For now, `user_id` defaults to `"local"` since this is a single-user app. The data model supports multi-user for future SaaS deployment.

#### 8.2 Usage Endpoint — add to `server/routers/tool_factory.py` — [ROBOT]

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `GET` | `/api/tool-factory/usage` | Get current user's usage stats | [ROBOT] |
| `GET` | `/api/tool-factory/usage/history?months=6` | Monthly usage history | [ROBOT] |

#### 8.3 Analytics Dashboard Component — `ui/src/components/tool-factory/AnalyticsDashboard.tsx` — [ROBOT]

One React component that displays usage metrics. Added as a tab or section in the ToolManagerPage.

**Metrics displayed:**

| Metric | Display Type | Data Source |
|--------|-------------|-------------|
| Tools generated (this month / all time) | Counter with trend arrow | `usage.monthly.tools_generated` / `usage.all_time.total_tools_generated` |
| Tools by status (active / draft / error / archived) | Horizontal bar chart or donut | `/api/tool-factory/stats` |
| Chain executions this month | Counter | `usage.monthly.chain_executions` |
| Token usage by month | Simple bar chart (last 6 months) | `usage.history` |
| Most-used themes | Horizontal bars | `/api/tool-factory/stats` |
| Top tools by execution count | Ranked list | `/api/tool-factory/tools?sort=times_run` |
| Average generation time | Single stat | `/api/tool-factory/stats` |
| Tier usage gauge | Progress bar (X of Y tools this month) | `usage.monthly` vs `TIER_LIMITS` |

**Chart library:** Use simple CSS bars or inline SVG. Don't add a heavy charting library — keep it lightweight. If the project already uses a chart library, use that.

**Layout:** Dashboard grid following `WORKSPACE_STANDARDS.md` patterns. 2-3 columns on desktop, 1 column on mobile.

#### 8.4 Analytics Hook — `ui/src/hooks/useToolFactory.ts` — [ROBOT] (add to existing)

```typescript
// Add to existing useToolFactory.ts
export function useToolUsage()                          // GET /api/tool-factory/usage
export function useToolUsageHistory(months?: number)    // GET /api/tool-factory/usage/history
```

#### 8.5 API Client Functions — Edit `ui/src/lib/api.ts` — [ROBOT]

```typescript
// Add to existing api.ts
export async function fetchToolUsage(): Promise<UsageStats>
export async function fetchToolUsageHistory(months?: number): Promise<MonthlyUsage[]>
export async function startBatchGeneration(request: BatchGenerateRequest): Promise<BatchGenerateResponse>
export async function fetchBatchStatus(batchId: string): Promise<BatchStatus>
export async function cancelBatch(batchId: string): Promise<void>
export async function deployBatch(batchId: string): Promise<void>
```

---

## FILES TO CREATE/MODIFY

| File | Action | Phase |
|------|--------|-------|
| `server/services/batch_tool_generator.py` | **Create** | 7 |
| `server/services/tool_usage.py` | **Create** | 8 |
| `ui/src/components/tool-factory/AnalyticsDashboard.tsx` | **Create** | 8 |
| `server/routers/tool_factory.py` | **Edit** (add batch + usage endpoints) | 7+8 |
| `ui/src/hooks/useToolFactory.ts` | **Edit** (add usage + batch hooks) | 8 |
| `ui/src/lib/api.ts` | **Edit** (add batch + usage API functions) | 7+8 |
| `ui/src/components/tool-factory/ToolManagerPage.tsx` | **Edit** (add Analytics tab/section) | 8 |

---

## TEST PLAN

### Unit Tests — `tests/test_batch_tool_generator.py` — [ROBOT]

| Test | What It Validates |
|------|-------------------|
| `test_batch_single_project` | One project → one tool generated |
| `test_batch_multiple_projects` | 3 projects → 3 tools, all in registry |
| `test_batch_with_error` | 1 of 3 projects fails → other 2 succeed, failed one logged |
| `test_batch_cancel` | Cancel mid-batch → remaining projects skipped |
| `test_batch_progress_callback` | Progress callback fires after each tool |
| `test_batch_auto_deploy` | auto_deploy=True → tools deployed to Sheets |
| `test_batch_default_theme` | Default theme applied to all tools in batch |
| `test_batch_status` | Status updates correctly: running → completed |
| `test_batch_max_50` | Rejects request with > 50 project IDs |

### Unit Tests — `tests/test_tool_usage.py` — [ROBOT]

| Test | What It Validates |
|------|-------------------|
| `test_record_generation` | Monthly count increments |
| `test_record_execution` | Execution count + tokens increment |
| `test_monthly_usage` | Returns current month's data |
| `test_all_time_usage` | Lifetime totals aggregate correctly |
| `test_check_tier_free_under` | 3 of 5 → returns True |
| `test_check_tier_free_at_limit` | 5 of 5 → returns False |
| `test_check_tier_pro_unlimited` | Pro tier → always True |
| `test_usage_history` | Returns last N months in order |
| `test_month_rollover` | New month starts fresh count |
| `test_atomic_save` | File not corrupted on concurrent writes |

### Build + Lint Tests — [ROBOT]

```bash
cd ui && npm run lint && npm run build
```

### Integration Tests — `tests/test_batch_integration.py` — [ROBOT]

| Test | What It Validates |
|------|-------------------|
| `test_batch_endpoint_start` | POST /batch/generate returns batch_id |
| `test_batch_endpoint_status` | GET /batch/{id} returns progress |
| `test_usage_endpoint` | GET /usage returns valid UsageStats |
| `test_usage_history_endpoint` | GET /usage/history returns monthly data |

### How to Run Tests
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
python -m pytest tests/test_batch_tool_generator.py tests/test_tool_usage.py tests/test_batch_integration.py -v
cd ui && npm run lint && npm run build
```

---

## EXISTING CODE REFERENCES

| File | Why |
|------|-----|
| `server/services/batch_tool_generator.py` needs → | |
| `server/services/sheet_blueprint.py` | Agent 1 built this — blueprint generation |
| `server/services/sheet_deployer.py` | Agent 2 built this — Google Sheets deployment |
| `server/services/tool_registry.py` | Agent 1 built this — tool CRUD |
| `server/routers/yt_batch.py` | Existing batch pattern — same in-memory state approach |
| `server/services/rate_limit_logger.py` | Atomic file write pattern for tool_usage.py |
| `ui/src/components/tool-factory/ToolManagerPage.tsx` | Agent 3 built this — add Analytics tab here |
| `ui/src/hooks/useToolFactory.ts` | Agent 3 built this — add usage hooks here |
| `ui/WORKSPACE_STANDARDS.md` | Dashboard layout patterns |

---

## ACCEPTANCE CRITERIA

1. Batch generation processes 3 test projects sequentially without errors
2. Per-tool error isolation: one failure doesn't stop the batch
3. Batch status endpoint returns accurate progress
4. Usage tracker records generations and executions correctly
5. Tier limit check enforces free tier (5/month) and unlimited pro
6. Analytics dashboard renders with mock data (counters, bars, ranked list)
7. All unit tests pass
8. `ruff check .` passes on all new Python files
9. `npm run build` succeeds with analytics component
10. Month rollover creates fresh counters
