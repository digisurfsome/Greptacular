# API Research Engine — Agent 1: Backend

## Read First
- `docs/prd-api-research-engine.md` — Full PRD with data models, pipeline order, static DB entries
- `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md` — Auth rules (use `force_subscription=True`)
- `docs/SONNET_OPUS_OPTIMIZATION.md` — Build optimization rules

## What You're Building

**Phase 1: Backend** — `api_research.py` + pipeline integration into `sheet_blueprint.py`

## Tasks (in order)

### 1. Create `server/services/api_research.py`

New file. Contains:

- **Pydantic models**: `APIAlternative`, `APIResearchResult`, `BlueprintAPIResearch` (exact schemas in PRD)
- **Static pricing database**: Python dict covering all 20+ APIs listed in the PRD (both the main 13 and the 10 alternatives). Each entry matches the `APIResearchResult` schema with `research_source: "static_database"`.
- **`research_api_pricing(detected_apis: list) -> BlueprintAPIResearch`**: Main function that:
  1. Takes list of detected APIs from `detect_apis()`
  2. For each API, tries web research first (Layer 2), falls back to static DB (Layer 1)
  3. Returns `BlueprintAPIResearch` with all results + `total_estimated_monthly_cost` + `research_duration_seconds`
- **Web research function**: Uses `ClaudeSDKClient` with `WebSearchTool` (check exact tool name), Sonnet, `force_subscription=True`, 90-second timeout, `max_turns=4`
- **Fallback logic**: web search fails/times out -> use static DB entry -> if not in DB, return minimal entry with "No pricing data available"
- **Progress callback**: Accept optional callback to emit "Researching API pricing 1/{total}: {service_name}..." messages

### 2. Update `server/services/sheet_blueprint.py`

- Add `research_api_pricing()` call to the `generate_blueprint()` pipeline
- Insert it as step 4 (after `detect_apis`, before `extract_user_variables`) — see PRD pipeline diagram
- Pass detected APIs list to the research function
- Thread progress messages through to SSE
- Add `api_research` field to the blueprint output model: `api_research: Optional[BlueprintAPIResearch] = None`
- Handle errors gracefully — if research fails entirely, blueprint still generates with `api_research=None`

### 3. Verify

- Run `cd ui && npm run build` — zero TypeScript errors (even though you're only touching Python, verify nothing breaks)
- Check that `sheet_blueprint.py` still imports correctly
- Verify the Pydantic models serialize to JSON properly

## Critical Rules

- Use `force_subscription=True` for ALL Claude calls — see subscription guide
- Match existing code patterns in `sheet_blueprint.py`
- Don't modify any existing API detection logic — only ADD the research step
- Stage only files you created or modified — do NOT use `git add -A`
- Commit after completing all tasks with a clear message
