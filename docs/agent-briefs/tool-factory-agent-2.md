# Agent Brief 2: Theme Integration + Google Sheets Deployer

**Phases:** 3 + 4 from `docs/prd-video-to-tool-factory.md`
**Scope:** Backend Python + Google API integration
**Estimated Tokens:** ~55-65k
**Dependencies:** Agent 1 must be complete (needs data models + tool_registry)
**Can Run Parallel With:** Agent 3 (they don't touch the same files)

---

## ARCHITECTURE CONTEXT (read this first)

### What This System Is
A pipeline that converts strategy steps (from YouTube videos or PRDs) into deployable Google Sheets automation tools. Agent 1 already built the data models and blueprint engine that produces a `SheetBlueprint`. **This agent takes that blueprint and deploys it as a real Google Sheet with visual theming.**

### Where This Agent Fits
```
[1] Ingest    → YouTube/PRD → steps                                ← BUILT
[2] Extract   → steps → YTStrategyStep[]                           ← BUILT
[3] Blueprint → YTStrategyStep[] → SheetBlueprint                  ← Agent 1 BUILT THIS
[4] Theme     → ThemeConfig applied to SheetBlueprint              ← THIS AGENT (Phase 3)
[5] Deploy    → SheetBlueprint + Theme → real Google Sheet         ← THIS AGENT (Phase 4)
```

### Theming Architecture: Two Paths → One Format
Every tool gets a visual theme. Users choose from two paths that converge into the same `ThemeConfig` object:

```
Path A: Preset Themes                    Path B: Image-to-Theme
(10 built-in themes in                   (screenshot any app →
.claude/skills/theme-factory/)           style_extractor.py extracts
                                         colors, fonts, patterns)
        ↓                                          ↓
   preset_theme_to_theme_config()      style_extraction_to_theme_config()
        ↓                                          ↓
        └──────────── ThemeConfig ────────────────┘
                          ↓
              theme_to_sheets_format()
                          ↓
              Google Sheets API formatting
```

**Key rule:** Tools are structure-first, theme-second. The sheet's columns, formulas, and chain logic are theme-independent. Theme only touches colors, fonts, and formatting. Swap themes anytime without breaking anything.

### Google Sheet Structure (5 Tabs)
Each deployed tool is a Google Sheet with these tabs:
1. **Guide** — tool name, description, usage instructions, required API keys
2. **Setup** — user variables (input cells) + API key configuration with status formulas
3. **Chain Config** — the prompt chain rows (Step # | Title | Type | Prompt | Expected Output | Input Source | Status | Output)
4. **Output History** — execution log (appended after each chain run)
5. **Chain Runner** — optional Apps Script macro for auto-execution

### Google API Constraints
- Sheets API quota: 100 requests per 100 seconds per user
- Solution: Batch ALL formatting into a single `batchUpdate` call (3-4 API calls total per sheet)
- OAuth 2.0 with scopes: `spreadsheets` + `drive.file` (only files we create)
- Credentials stored at `~/.autoforge/google_credentials.json`, token at `~/.autoforge/google_token.json`

### Existing Code This Agent Connects To
- **`server/services/style_extractor.py`** — Already built. Takes an image, returns `{identified_style, extracted_tokens, tailwind_config, style_guide_markdown}`. This agent wraps its output into ThemeConfig format.
- **`.claude/skills/theme-factory/themes/`** — 10 preset theme `.md` files (Ocean Depths, Sunset Boulevard, etc.). This agent parses them into ThemeConfig format.
- **`server/models/tool_factory.py`** — Agent 1 created ThemeConfig, SheetBlueprint, GeneratedTool models
- **`server/services/tool_registry.py`** — Agent 1 created tool CRUD. This agent updates tool status after deployment.

---

## STRIPE MINIONS CONTEXT

- **[ROBOT]** = Deterministic Python code. No LLM calls. Zero tokens. Must work perfectly every time.
- **[AGENT]** = Requires Claude API call. Has hallucination risk. Needs error handling, retries, output validation.

**This agent is almost entirely [ROBOT].** The theme integration and Google Sheets deployment are pure API calls and data transformation. The only [AGENT] step is the already-built `style_extractor.py` (which this agent connects to, not rebuilds).

---

## WHAT TO BUILD

### Phase 3: Theme Integration

#### 3.1 Theme Adapter — `server/services/sheet_theme_engine.py` — [ROBOT] (entire file)

Converts between existing theme formats and the new unified `ThemeConfig` model (from Agent 1).

**Functions:**

| Function | Robot/Agent | What It Does |
|----------|-------------|-------------|
| `style_extraction_to_theme_config(extraction: dict) → ThemeConfig` | [ROBOT] | Maps style_extractor.py output → ThemeConfig. Extracts colors from Tailwind config, fonts from style guide. |
| `preset_theme_to_theme_config(theme_name: str) → ThemeConfig` | [ROBOT] | Loads `.claude/skills/theme-factory/themes/{name}.md`, parses color/font defs → ThemeConfig. |
| `list_preset_themes() → list[ThemeConfig]` | [ROBOT] | Scans theme-factory directory, returns all 10 presets as ThemeConfig objects. |
| `theme_to_sheets_format(theme: ThemeConfig) → dict` | [ROBOT] | Converts ThemeConfig → Google Sheets API formatting requests (CellFormat objects for headers, body, accent, input, status). |
| `hex_to_sheets_color(hex_color: str) → dict` | [ROBOT] | Pure math: "#FF5733" → {"red": 1.0, "green": 0.341, "blue": 0.2}. |
| `build_theme_requests(theme: ThemeConfig, sheet_ids: dict) → list[dict]` | [ROBOT] | Assembles full batchUpdate request list for applying theme to all 5 sheet tabs. |
| `create_custom_theme(colors: dict, typography: dict, components: dict) → ThemeConfig` | [ROBOT] | User-provided values → ThemeConfig with source="custom". |

**Key mapping rules (ThemeConfig → Google Sheets):**
```
theme.colors.brand_default    → header row background
theme.colors.surface_base     → body row background
theme.colors.surface_canvas   → alternate row background
theme.colors.text_primary     → body text color
theme.colors.brand_light      → input cell highlight
theme.typography.font_family_heading → header font
theme.typography.font_family_body    → body font
theme.colors.status_success   → "Done" conditional format
theme.colors.status_error     → "Error" conditional format
theme.colors.status_warning   → "Pending" conditional format
```

**Existing code to read:**
- `server/services/style_extractor.py` — understand its output format (identified_style, extracted_tokens, tailwind_config, style_guide_markdown)
- `.claude/skills/theme-factory/themes/` — understand preset .md file format

#### 3.2 Theme Preview Model — [ROBOT]

```python
class ThemePreview(BaseModel):
    """Preview of what a theme looks like applied to sample data."""
    theme: ThemeConfig
    sample_cells: list[dict]    # 5-6 cells with applied formatting (for UI preview)
    color_swatches: list[dict]  # {"name": "Brand", "hex": "#FF5733"} for palette display
    font_preview: dict          # {"heading": {"font": "Inter", "weight": 700}, "body": {...}}
```

#### 3.3 Theme Router — `server/routers/tool_themes.py` — [ROBOT] (all endpoints)

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `GET` | `/api/tool-factory/themes` | List all themes (10 presets + user-created) | [ROBOT] |
| `GET` | `/api/tool-factory/themes/{theme_id}` | Get single theme details | [ROBOT] |
| `POST` | `/api/tool-factory/themes/extract` | Upload image → call style_extractor → return ThemeConfig | [AGENT] (calls existing style_extractor) |
| `POST` | `/api/tool-factory/themes/preview` | Generate preview of theme on sample data | [ROBOT] |
| `PUT` | `/api/tool-factory/tools/{tool_id}/theme` | Swap theme on existing tool, re-apply formatting | [ROBOT] (+ Sheets API call if deployed) |
| `POST` | `/api/tool-factory/themes/custom` | Create custom theme from user inputs | [ROBOT] |

**Note on `/themes/extract`:** This calls the already-built `style_extractor.py`. This agent does NOT rebuild that service — it just connects to it and converts the output to ThemeConfig format.

---

### Phase 4: Sheet Deployer (Google Sheets API)

#### 4.1 Google OAuth Service — `server/services/google_auth.py` — [ROBOT] (entire file)

Standard OAuth 2.0 flow. No LLM calls — just HTTP redirects and token storage.

**Config:**
```python
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # Only files we create
]
# Credentials: ~/.autoforge/google_credentials.json (user downloads from GCP console)
# Token: ~/.autoforge/google_token.json (auto-generated after OAuth flow)
```

**Methods (all [ROBOT]):**

| Method | What It Does |
|--------|-------------|
| `get_credentials() → Credentials` | Load token, auto-refresh if expired |
| `start_oauth_flow() → str` | Generate OAuth URL for user to visit |
| `handle_oauth_callback(code: str) → bool` | Exchange auth code for token, save to file |
| `is_authenticated() → bool` | Check if valid token exists |
| `revoke() → None` | Delete stored token |

**OAuth flow (all [ROBOT]):**
1. User clicks "Connect Google" in UI
2. Backend generates OAuth URL → returns it
3. User authorizes in browser → gets redirected back with code
4. Backend exchanges code → stores token at `~/.autoforge/google_token.json`
5. Auto-refresh when token expires (Google library handles this)

#### 4.2 Sheet Deployer — `server/services/sheet_deployer.py` — [ROBOT] (entire file)

Creates actual Google Sheets from a `SheetBlueprint`. ALL functions are [ROBOT] — pure Sheets API calls.

**Generated Sheet Structure (5 Tabs):**

| Tab | Purpose | Contents |
|-----|---------|----------|
| **Guide** | User instructions | Tool name, description, source link, step-by-step usage guide, required API keys list |
| **Setup** | Configuration | User variables (one row each with Label \| Input Cell \| Description), API keys (Service \| Key Cell \| Signup URL \| Status formula) |
| **Chain Config** | The prompt chain | Step # \| Title \| Type \| Prompt Template \| Expected Output \| Input Source \| Status \| Output \| Run Time |
| **Output History** | Execution log | Run # \| Timestamp \| Step \| Input Summary \| Output Summary \| Tokens Used \| Duration |
| **Chain Runner** | Apps Script (optional) | Macro code to execute the chain step by step |

**Functions (all [ROBOT]):**

| Function | What It Does |
|----------|-------------|
| `deploy_sheet(blueprint, theme, folder_id) → dict` | Main entry. Creates sheet, populates all 5 tabs, applies theme. Returns `{sheet_id, sheet_url, sheet_title}`. |
| `_create_sheet_structure(service, blueprint) → str` | `spreadsheets.create()` — creates sheet with 5 tabs and column headers. Returns sheet_id. |
| `_populate_guide_tab(service, sheet_id, blueprint)` | Writes guide content to first tab. |
| `_populate_setup_tab(service, sheet_id, blueprint)` | Writes user variables + API key rows with formulas. |
| `_populate_chain_tab(service, sheet_id, blueprint)` | Writes chain config rows from blueprint.chain_config. |
| `_setup_output_history_tab(service, sheet_id)` | Creates headers for output tracking. |
| `_apply_formatting(service, sheet_id, theme, tab_ids)` | Single batchUpdate with all formatting (column widths, colors, fonts, conditional formatting, protection). |
| `_build_conditional_formatting(theme, chain_tab_id) → list` | Status column: Pending=yellow, Running=blue, Done=green, Error=red. |
| `_build_data_validation(chain_tab_id) → list` | Dropdown for Status column, Step Type column. |
| `redeploy_theme(sheet_id, theme) → bool` | Re-apply theme to existing sheet (for theme swapping). |

**Google Sheets API pattern:**
```python
# Step 1: Create structure (one API call)
sheet = service.spreadsheets().create(body=sheet_body).execute()

# Step 2: Populate data (one API call per tab, or batch)
service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=data).execute()

# Step 3: Apply formatting (one batchUpdate call)
service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": format_requests}).execute()
```

**Rate limit safety:** Google Sheets API allows 100 requests per 100 seconds per user. By batching all formatting into a single `batchUpdate`, we use only 3-4 API calls per sheet deployment. Well within limits.

#### 4.3 Google Auth + Deploy Endpoints — add to `server/routers/tool_factory.py`

| Method | Path | What It Does | Robot/Agent |
|--------|------|-------------|-------------|
| `GET` | `/api/tool-factory/google/auth-url` | Get OAuth URL | [ROBOT] |
| `POST` | `/api/tool-factory/google/callback` | Handle OAuth callback | [ROBOT] |
| `GET` | `/api/tool-factory/google/status` | Check if authenticated | [ROBOT] |
| `POST` | `/api/tool-factory/deploy/{tool_id}` | Deploy blueprint → Google Sheet | [ROBOT] |
| `POST` | `/api/tool-factory/deploy/{tool_id}/redeploy-theme` | Re-apply theme to deployed sheet | [ROBOT] |

---

## FILES TO CREATE/MODIFY

| File | Action | Phase |
|------|--------|-------|
| `server/services/sheet_theme_engine.py` | **Create** | 3 |
| `server/routers/tool_themes.py` | **Create** | 3 |
| `server/services/google_auth.py` | **Create** | 4 |
| `server/services/sheet_deployer.py` | **Create** | 4 |
| `server/routers/tool_factory.py` | **Edit** (add deploy + Google auth endpoints) | 4 |
| `server/main.py` | **Edit** (register tool_themes router) | 3 |
| `requirements.txt` | **Edit** (add google-api-python-client, google-auth-oauthlib, google-auth-httplib2) | 4 |

---

## DEPENDENCIES TO INSTALL

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Add to `requirements.txt`:
```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
```

**Google Cloud Setup (owner does this once, not the agent):**
1. Create project in Google Cloud Console
2. Enable Google Sheets API + Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `client_secret.json` → save as `~/.autoforge/google_credentials.json`

---

## TEST PLAN

### Unit Tests — `tests/test_sheet_theme_engine.py`

| Test | What It Validates |
|------|-------------------|
| `test_hex_to_sheets_color` | "#FF5733" → {"red": 1.0, "green": 0.341, "blue": 0.2} |
| `test_hex_to_sheets_color_black` | "#000000" → all zeros |
| `test_hex_to_sheets_color_white` | "#FFFFFF" → all ones |
| `test_preset_theme_loads` | "ocean-depths" loads from theme-factory directory |
| `test_all_presets_load` | All 10 presets load without error |
| `test_preset_to_theme_config` | Preset → ThemeConfig has all required fields |
| `test_theme_to_sheets_format` | ThemeConfig → dict with header_format, body_format, etc. |
| `test_build_theme_requests` | Returns valid Sheets API batchUpdate requests |
| `test_custom_theme_creation` | User inputs → ThemeConfig with source="custom" |
| `test_style_extraction_to_theme_config` | Mock style_extractor output → ThemeConfig |

### Unit Tests — `tests/test_google_auth.py`

| Test | What It Validates |
|------|-------------------|
| `test_is_authenticated_no_token` | Returns False when no token file |
| `test_is_authenticated_valid_token` | Returns True with valid mock token |
| `test_start_oauth_flow` | Returns valid URL string |
| `test_handle_callback_saves_token` | Token file created after successful callback |

### Unit Tests — `tests/test_sheet_deployer.py`

| Test | What It Validates |
|------|-------------------|
| `test_build_guide_tab_data` | Guide tab has tool name, description, steps |
| `test_build_setup_tab_data` | Setup tab has variables + API keys with formulas |
| `test_build_chain_tab_data` | Chain tab rows match blueprint.chain_config |
| `test_build_conditional_formatting` | Status column has 4 conditional format rules |
| `test_build_data_validation` | Dropdown for Status and Step Type columns |
| `test_deploy_sheet_mock` | Full deploy with mocked Sheets API — returns sheet_id, url, title |
| `test_redeploy_theme_mock` | Theme swap with mocked Sheets API — batchUpdate called with new formatting |

### Integration Test — `tests/test_theme_integration.py`

| Test | What It Validates |
|------|-------------------|
| `test_theme_endpoint_list` | GET /themes returns 10+ themes |
| `test_theme_endpoint_get` | GET /themes/ocean-depths returns valid ThemeConfig |
| `test_theme_endpoint_preview` | POST /themes/preview returns sample cells + swatches |
| `test_google_status_not_authed` | GET /google/status returns authenticated=false initially |

### How to Run Tests
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular"
python -m pytest tests/test_sheet_theme_engine.py tests/test_google_auth.py tests/test_sheet_deployer.py tests/test_theme_integration.py -v
```

---

## EXISTING CODE REFERENCES

| File | Why |
|------|-----|
| `server/services/style_extractor.py` | Understand its output format — this agent wraps it |
| `.claude/skills/theme-factory/` | Understand preset theme .md files — this agent parses them |
| `server/models/tool_factory.py` | Created by Agent 1 — ThemeConfig, SheetBlueprint, GeneratedTool |
| `server/services/tool_registry.py` | Created by Agent 1 — used to update tool status after deployment |
| `server/routers/tool_factory.py` | Created by Agent 1 — add new endpoints here |

---

## ACCEPTANCE CRITERIA

1. All 10 preset themes load and convert to ThemeConfig without error
2. `theme_to_sheets_format()` produces valid Google Sheets API formatting
3. `hex_to_sheets_color()` handles all valid hex codes
4. Google OAuth flow works end-to-end (manual test with real credentials)
5. `deploy_sheet()` creates a 5-tab Google Sheet from a SheetBlueprint (test with mock API)
6. Theme swapping re-applies formatting without recreating the sheet
7. All unit tests pass
8. `ruff check .` passes on all new files
9. New pip dependencies added to requirements.txt
