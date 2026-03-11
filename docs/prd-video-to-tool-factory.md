# Agent OS Blueprint: Video-to-Tool Factory (YT Lab → Google Sheets Tool Pipeline)

**Status:** Draft
**Date:** 2026-03-11
**Author:** Owner + Claude (Session 10)
**Depends on:** YT Lab (built — ingestion, processing, discovery), Style Extractor (built), Theme Factory (built)
**Implementation:** 8 phases, each under 50% context window

---

## STANDARDS LAYER

### Technology Stack

- **Backend:** Python 3.11+ with FastAPI, Pydantic models, async/await
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS v4, TanStack Query (React Query)
- **Data Storage:** SQLite via SQLAlchemy for tool registry + execution history; localStorage for in-flight UI state
- **Google Integration:** Google Sheets API v4 via `google-api-python-client` + `google-auth-oauthlib` (OAuth 2.0)
- **AI Models:** Claude Sonnet 4.6 (prompt conversion, blueprint generation), Claude Opus 4.6 (quality review of generated tools)
- **Real-time:** WebSocket events via existing `server/websocket.py` broadcast pattern + Server-Sent Events for generation progress
- **Theming:** `server/services/style_extractor.py` (image → theme) + `.claude/skills/theme-factory/` (10 preset themes + custom)

### Architecture Patterns

- **Services** live in `server/services/` — one file per domain:
  - `sheet_blueprint.py` — Transforms YTStrategyStep[] → Chain Config rows
  - `sheet_deployer.py` — Creates actual Google Sheet via Sheets API
  - `sheet_theme_engine.py` — Applies themes to generated sheets (colors, fonts, layout)
  - `tool_registry.py` — Tracks all generated tools, their configs, execution history
  - `style_extractor.py` — **Already built.** Image → Visual DNA → Tailwind config + style classification
- **Routers** live in `server/routers/` — thin REST layer, Pydantic request/response models:
  - `tool_factory.py` — CRUD + generation endpoints for the factory pipeline
  - `tool_themes.py` — Theme selection, preview, application endpoints
- **React hooks** in `ui/src/hooks/` — wrap TanStack Query for API calls:
  - `useToolFactory.ts` — Generation, listing, status polling
  - `useToolThemes.ts` — Theme browsing, preview, application
- **UI components** in `ui/src/components/tool-factory/` — colocated with YT Lab
- **Registration** — new routers registered in `server/routers/__init__.py` AND `server/main.py`

### Key Existing Code to Understand

| File | What It Does | Why It Matters |
|---|---|---|
| `ui/src/lib/types.ts` (lines 1411-1660) | YTStrategyStep, YTStrategySubStep, YTIngestResponse, YTProcessResponse types | **Source data model.** Every tool starts as YTStrategyStep[]. The blueprint generator reads these. |
| `server/services/yt_processor.py` | Sends transcript to Claude, extracts structured steps with prompts, expected outputs, model recommendations | **Upstream producer.** Its output is our input. Must match its schema exactly. |
| `server/routers/yt_processing.py` | POST /api/yt-lab/process and /process-stream endpoints | We chain after this — user processes video, then clicks "Generate Tool" |
| `server/services/yt_discovery.py` | Analyzes video for app opportunities with scoring | Optional enrichment — discovery data can inform tool descriptions and marketing copy |
| `server/routers/yt_ingestion.py` | Video ingestion — transcript, metadata, screenshots | Provides raw material; screenshot analysis feeds into tool documentation |
| `server/services/style_extractor.py` | **Already built.** Takes base64 image → Claude vision → extracts full Visual DNA (colors, typography, spacing, component patterns) → outputs Tailwind CSS theme JSON + style classification (12 styles) | **Image-to-theme path.** User screenshots any app/website, this extracts the design system and converts it to a reusable theme config. |
| `.claude/skills/theme-factory/SKILL.md` | 10 preset themes (Ocean Depths, Sunset Boulevard, etc.) + custom theme generation | **Preset theme path.** User picks a theme or generates custom one. Each theme has hex colors + font pairings. |
| `.claude/skills/theme-factory/themes/*.md` | Individual theme definitions (10 files: arctic-frost, botanical-garden, desert-rose, forest-canopy, golden-hour, midnight-galaxy, modern-minimalist, ocean-depths, sunset-boulevard, tech-innovation) | **Theme library.** Each file contains complete color palette + typography + visual identity specs. |
| `server/routers/__init__.py` | Registers all routers with FastAPI app | Must add tool_factory and tool_themes routers here |
| `server/main.py` | FastAPI app setup, includes all routers | Must include new routers here |
| `ui/src/lib/api.ts` | REST API client functions | Add tool factory + themes API functions here |

### Coding Conventions

- Python: ruff-clean, type hints on public methods, `logging.getLogger(__name__)`
- TypeScript: ESLint-clean, `interface` for data shapes, `type` for unions
- Tailwind: semantic tokens (`bg-card`, `text-foreground`, `border-border`), no hardcoded colors
- Pydantic: `BaseModel` for all request/response schemas, `Optional` with `Field` for validation
- File I/O: always handle missing dirs (`mkdir(parents=True, exist_ok=True)`), corrupted JSON (reset to default), OS errors (log and continue)
- Commits: conventional commits (`feat:`, `fix:`, `docs:`), directly to `main`
- Google API: all OAuth tokens stored in `~/.autoforge/google_credentials.json`, never in project dirs

### Quality Standards

- `cd ui && npm run build` must pass (TypeScript + build)
- `ruff check .` must pass (Python linting)
- No hardcoded paths — use `Path.home() / ".autoforge"` for global, `project_dir / ".autoforge"` for project
- All UI must work with existing themes (no custom colors, use semantic tokens)
- WebSocket events must follow existing `{"type": "...", "data": {...}}` pattern
- Google Sheets API calls must have proper error handling (quota, auth expiry, network)
- Generated sheets must be functional without any code changes — user only adds API keys

### Theming Architecture Standards

The theming system has two input paths that converge into a single `ThemeConfig` object:

```
Path A: Image-to-Theme (style_extractor.py)
  Screenshot/Image → Claude Vision → Visual DNA extraction → ThemeConfig

Path B: Preset Theme (theme-factory)
  User picks from 10 presets OR creates custom → ThemeConfig

                    ↓ Both paths produce ↓

              ThemeConfig (unified format)
                    ↓
        Applied to generated Google Sheet
          (cell colors, fonts, header styles,
           button colors, chart themes)
                    ↓
        Stored with tool in registry
          (can be swapped later, like WordPress themes)
```

**ThemeConfig** is the universal format:
```python
class ThemeConfig(BaseModel):
    """Universal theme config — every generated tool carries one."""
    theme_id: str                    # e.g. "ocean-depths" or "custom-abc123"
    theme_name: str                  # Display name
    source: Literal["preset", "extracted", "custom"]
    colors: ThemeColors              # brand, surface, text, border, status
    typography: ThemeTypography      # font families, size scale, weights
    components: ThemeComponents      # card radius, button style, input style
    tailwind_config: dict            # Raw Tailwind extension JSON (for web previews)
    style_classification: str | None # e.g. "neubrutalism", "glassmorphism" (from style_extractor)
```

**Key rule:** Tools are built theme-agnostic. The theme is a layer applied ON TOP of the structural layout. This means:
- Sheet structure (columns, formulas, chain logic) is theme-independent
- Theme only affects: cell background colors, font choices, header styling, conditional formatting colors
- Any tool can have its theme swapped at any time without breaking functionality
- Same architecture as WordPress/Astro themes — structure and style are separate concerns

---

## PRODUCT LAYER

### Vision

**Every YouTube strategy video becomes a working tool in under 10 minutes.**

The YT Lab already extracts video content into structured steps (YTStrategyStep[]). Google Sheets already works as a prompt-chain tool format — text boxes, API key slots, cell references, conditional formatting. The Video-to-Tool Factory bridges them: video in, working Google Sheet tool out.

The magic is the Google Sheets format. It's:
- **Free to run** — no hosting, no deployment, no server costs
- **Instantly shareable** — one link, anyone can use it
- **Already understood** — everyone knows spreadsheets
- **Extensible** — users add rows, tweak prompts, chain more steps
- **Themeable** — each tool gets its own visual identity, swappable like WordPress themes

At scale: hundreds of tools per day, each costing pennies on a Claude subscription. The SaaS model writes itself — free tier (5 tools/month), pro tier ($29/month unlimited), enterprise (white-label + custom themes).

### The Core Insight

YouTube strategy videos are just prompt chains described verbally. Every "Step 1: Research your ICP" is a prompt. Every "Step 2: Generate ad copy from that research" is a prompt that takes the previous output. The video IS the tool spec — it just needs to be reformatted.

Google Sheets is the perfect container because:
1. Each row = one prompt chain step
2. Cell references = `{{previousOutput}}` chaining
3. Named ranges = variable substitution
4. Conditional formatting = status indicators
5. Separate tabs = config, chain, output history, API keys
6. Apps Script = optional automation layer

### Target Users

1. **Tool Creators (Power Users)** — People who watch strategy videos and want to operationalize them immediately
2. **Tool Consumers (End Users)** — People who receive a shared Google Sheet tool, add their API keys, and run it
3. **The Owner (Platform Operator)** — Generates tools at scale, sells access via SaaS tiers

### The 5-Stage Pipeline

```
Stage 1: VIDEO INGESTION          (Already built — YT Lab)
  YouTube URL → transcript + metadata + screenshots
         ↓
Stage 2: STRATEGY EXTRACTION      (Already built — YT Lab)
  Transcript → YTStrategyStep[] (title, prompt, expectedOutput, model, subSteps)
         ↓
Stage 3: SHEET BLUEPRINT GEN      (NEW — this PRD)
  YTStrategyStep[] → ChainConfig rows + API key detection + theme selection
         ↓
Stage 4: SHEET DEPLOYMENT         (NEW — this PRD)
  ChainConfig → actual Google Sheet via Sheets API (5 tabs, formatted, themed)
         ↓
Stage 5: TOOL ACTIVATION          (User action)
  User adds API keys → runs the chain → gets output
```

### Use Cases

1. **Solo Creator** — Watches Cody Schneider's ad strategy video → clicks "Generate Tool" → gets a Google Sheet that runs the entire 10-step ad campaign workflow with prompt chaining
2. **Agency Scale** — Processes 20 marketing strategy videos overnight → wakes up to 20 ready-to-use tools, each themed differently for different clients
3. **SaaS Platform** — Users submit YouTube URLs on a web form → tools auto-generate → users get links to their Google Sheet tools → pay per tool or monthly subscription
4. **White Label** — Enterprise client gets tools generated with their brand colors (via image-to-theme extraction from their website screenshot)
5. **Tool Marketplace** — Generated tools are listed in a catalog, each with preview screenshots showing the theme, users browse and clone

### The Worked Example: Cody Schneider Ad Strategy (10 Steps → 9 Chain Rows)

This shows the exact transformation from video steps to working chain config:

| Video Step | Chain Row | Type | Input | Output | APIs Needed |
|---|---|---|---|---|---|
| 1. ICP Research | Row 1 | RESEARCH | `{niche}` keywords | Customer language, pain points, demographics | None (Claude only) |
| 2. Ad Copy Generation | Row 2 | GENERATION | Row 1 output + `{product}` | 40 ad copy variations | None (Claude only) |
| 3. Bulk Generate Creatives | Row 3 | GENERATION | Row 2 winners + templates | Image/video ad creatives | Canva API or manual |
| 4. Meta Upload | Row 4 | ACTION | Row 3 creatives + Row 2 copy | Campaign live on Meta | Meta Marketing API |
| 5. Winner Analysis | Row 5 | RESEARCH | Meta campaign data | Lowest CPC winners identified | Meta Marketing API |
| 6. Landing Pages | Row 6 | GENERATION | Row 5 winners + brand context | Landing page HTML/copy | None (Claude only) |
| 7. LinkedIn Pipeline | Row 7 | ACTION | Target criteria from Row 1 | Lead list + outreach sequences | PhantomBuster, Apollo, Instantly |
| 8. Email Sequences | Row 8 | GENERATION | Row 7 leads + Row 1 ICP data | Personalized email sequences | Instantly API |
| 9. Analytics Dashboard | Row 9 | RESEARCH | All campaign data | Performance summary + recommendations | Meta API, Google Analytics |
| 10. Scale Playbook | (Documentation) | MANUAL | All outputs | Documented SOP for repeating | None |

Step 10 becomes documentation in the sheet's "Guide" tab, not a chain row — it's a manual/reference step.

### Step Type Classification

Every YTStrategyStep gets classified into one of four types. This determines how the chain row behaves:

| Type | What It Does | Execution Model | Example |
|---|---|---|---|
| **RESEARCH** | Gathers/analyzes information | AI prompt only (no external API) | "Research ICP demographics" |
| **GENERATION** | Creates content from inputs | AI prompt, may use templates | "Generate 40 ad variations" |
| **ACTION** | Calls external APIs to do something | API call with structured payload | "Upload campaign to Meta" |
| **MANUAL** | Requires human judgment/action | Pauses chain, shows instructions | "Review and approve winners" |

Classification logic (in `sheet_blueprint.py`):
```python
def classify_step(step: YTStrategyStep) -> StepType:
    """Classify a video step into chain step type."""
    prompt_lower = step.prompt.lower()
    title_lower = step.title.lower()

    # ACTION: mentions specific APIs, uploading, sending, deploying
    action_signals = ["upload", "send", "deploy", "publish", "post to",
                      "push to", "submit", "create campaign", "launch"]
    if any(signal in prompt_lower or signal in title_lower for signal in action_signals):
        return StepType.ACTION

    # MANUAL: mentions review, approve, select, decide, choose
    manual_signals = ["review", "approve", "select", "decide", "choose",
                      "manually", "hand-pick", "curate"]
    if any(signal in prompt_lower or signal in title_lower for signal in manual_signals):
        return StepType.MANUAL

    # GENERATION: mentions create, generate, write, build, design, draft
    gen_signals = ["generate", "create", "write", "build", "design",
                   "draft", "compose", "produce", "make"]
    if any(signal in prompt_lower or signal in title_lower for signal in gen_signals):
        return StepType.GENERATION

    # Default: RESEARCH
    return StepType.RESEARCH
```

### API Key Auto-Detection

The blueprint generator scans each step's prompt text and auto-detects which external services are needed:

| Service | Detection Patterns | Signup URL |
|---|---|---|
| OpenAI | "gpt", "openai", "chatgpt", "dall-e" | https://platform.openai.com/api-keys |
| Anthropic (Claude) | "claude", "anthropic" | https://console.anthropic.com/ |
| Meta Marketing | "facebook ads", "meta ads", "instagram ads" | https://developers.facebook.com/ |
| Google Ads | "google ads", "adwords", "ppc" | https://ads.google.com/intl/en/home/tools/manager-accounts/ |
| PhantomBuster | "phantombuster", "phantom" | https://phantombuster.com/ |
| Apollo | "apollo.io", "apollo", "lead enrichment" | https://app.apollo.io/ |
| Instantly | "instantly", "cold email", "email warmup" | https://instantly.ai/ |
| Canva | "canva", "design template" | https://www.canva.com/developers/ |
| Airtable | "airtable", "base" | https://airtable.com/developers |
| Zapier | "zapier", "zap", "automation" | https://zapier.com/developer |
| Stripe | "stripe", "payment", "checkout" | https://dashboard.stripe.com/apikeys |
| Twilio | "twilio", "sms", "whatsapp" | https://www.twilio.com/console |
| SendGrid | "sendgrid", "transactional email" | https://app.sendgrid.com/settings/api_keys |

Detection is additive — if a step mentions "upload to Meta" and "track in Google Analytics", both Meta and Google get flagged.

### SaaS Tier Model

| Tier | Price | Tools/Month | Features |
|---|---|---|---|
| **Free** | $0 | 5 | Basic generation, 3 preset themes, no batch |
| **Pro** | $29/mo | Unlimited | All themes, image-to-theme, batch generation, priority queue |
| **Enterprise** | $99/mo | Unlimited | White-label, custom themes, API access, team sharing, analytics |

**Unit Economics:**
- Cost per tool generation: ~$0.02-0.05 (Sonnet tokens for blueprint + Sheets API call)
- Pro user generating 100 tools/month: $29 revenue vs ~$5 cost = 83% margin
- Break-even: 1 Pro subscriber covers infrastructure for ~580 free-tier users

### Theming: Two Paths to Unique Tools

Every generated tool gets a visual identity. Users choose from two paths:

**Path A: Preset Themes (Quick)**
Pick from 10 built-in themes. Each has tested color palettes and font pairings:
- Ocean Depths, Sunset Boulevard, Forest Canopy, Modern Minimalist, Golden Hour
- Arctic Frost, Desert Rose, Tech Innovation, Botanical Garden, Midnight Galaxy

**Path B: Image-to-Theme (Custom)**
Screenshot any app or website → `style_extractor.py` extracts the full Visual DNA:
- Color tokens (brand, surface, text, border, status)
- Typography system (font family, heading/body hierarchy, weights)
- Component patterns (card radius, button style, input style)
- Style classification (flat-design, neubrutalism, glassmorphism, etc.)

**Theme Swapping (Post-Creation)**
Tools are built structure-first, theme-second. Any tool can have its theme changed after creation:
- Same as changing a WordPress theme — content stays, visuals change
- Google Sheets conditional formatting rules, cell colors, font selections all update
- Tool registry stores both the structural config AND the current theme separately
- One API call: `PUT /api/tool-factory/{tool_id}/theme` with a new ThemeConfig

### Roadmap

- **Phase 1 (Foundation):** Data models, tool registry, ThemeConfig unified format
- **Phase 2 (Blueprint Engine):** YTStrategyStep[] → ChainConfig transformation + step classification + API detection
- **Phase 3 (Theme Integration):** Connect style_extractor + theme-factory → ThemeConfig pipeline, theme preview UI
- **Phase 4 (Sheet Deployer):** Google OAuth + Sheets API v4 → create actual sheets with 5 tabs, formatted and themed
- **Phase 5 (UI — Generation Flow):** "Generate Tool" button in YT Lab, progress tracking, preview before deploy
- **Phase 6 (UI — Tool Manager):** Tool listing, theme swapping, re-generation, sharing links
- **Phase 7 (Batch & Scale):** Batch generation from multiple videos, queue system, overnight processing
- **Phase 8 (SaaS Layer):** Usage tracking, tier enforcement, billing hooks, analytics dashboard

---

## SPECS LAYER

### Phase 1: Data Models, Tool Registry, ThemeConfig

**Goal:** Define all data structures and create the persistent tool registry.

#### 1.1 New Python Models — `server/models/tool_factory.py`

```python
"""Data models for the Video-to-Tool Factory."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StepType(str, Enum):
    RESEARCH = "research"
    GENERATION = "generation"
    ACTION = "action"
    MANUAL = "manual"


class ToolStatus(str, Enum):
    DRAFT = "draft"              # Blueprint generated, not yet deployed
    DEPLOYING = "deploying"      # Google Sheet creation in progress
    ACTIVE = "active"            # Deployed and ready to use
    ERROR = "error"              # Deployment failed
    ARCHIVED = "archived"        # Soft-deleted


class ThemeSource(str, Enum):
    PRESET = "preset"            # From theme-factory presets
    EXTRACTED = "extracted"      # From style_extractor.py (image → theme)
    CUSTOM = "custom"            # User-created custom theme


# ---------------------------------------------------------------------------
# Theme Models
# ---------------------------------------------------------------------------

class ThemeColors(BaseModel):
    """Color palette for a theme."""
    brand_light: str = Field(description="Light brand color hex")
    brand_default: str = Field(description="Primary brand color hex")
    brand_dark: str = Field(description="Dark brand color hex")
    surface_canvas: str = Field(description="Page background hex")
    surface_base: str = Field(description="Card/container background hex")
    surface_muted: str = Field(description="Input/subtle background hex")
    text_primary: str = Field(description="Main text color hex")
    text_secondary: str = Field(description="Muted/secondary text hex")
    text_tertiary: str = Field(description="Hint/placeholder text hex")
    border_subtle: str = Field(description="Border/divider color hex")
    status_success: str = Field(default="#22c55e", description="Success indicator hex")
    status_error: str = Field(default="#ef4444", description="Error indicator hex")
    status_warning: str = Field(default="#f59e0b", description="Warning indicator hex")


class ThemeTypography(BaseModel):
    """Typography configuration for a theme."""
    font_family_heading: str = Field(description="Google Font name for headings")
    font_family_body: str = Field(description="Google Font name for body text")
    font_weight_heading: int = Field(default=700, description="Heading weight (400-900)")
    font_weight_body: int = Field(default=400, description="Body weight (400-700)")
    base_size_px: int = Field(default=14, description="Base font size in pixels")


class ThemeComponents(BaseModel):
    """Component styling tokens."""
    card_radius_px: int = Field(default=8, description="Card border radius")
    button_radius_px: int = Field(default=6, description="Button border radius")
    input_radius_px: int = Field(default=4, description="Input border radius")
    shadow_card: str = Field(default="0 1px 3px rgba(0,0,0,0.1)", description="Card box shadow CSS")
    spacing_unit_px: int = Field(default=8, description="Base spacing unit (4, 8, or 10)")
    density: str = Field(default="cozy", description="'cozy' (whitespace-heavy) or 'compact' (data-dense)")


class ThemeConfig(BaseModel):
    """Universal theme config — every generated tool carries one.

    This is the convergence point for both theme paths:
    - Path A: style_extractor.py → ThemeConfig (source='extracted')
    - Path B: theme-factory presets → ThemeConfig (source='preset')
    - Path C: user creates custom → ThemeConfig (source='custom')
    """
    theme_id: str = Field(description="Unique theme identifier, e.g. 'ocean-depths' or 'custom-abc123'")
    theme_name: str = Field(description="Human-readable display name")
    source: ThemeSource = Field(description="How this theme was created")
    colors: ThemeColors
    typography: ThemeTypography
    components: ThemeComponents
    tailwind_config: dict = Field(default_factory=dict, description="Raw Tailwind extension JSON for web previews")
    style_classification: Optional[str] = Field(
        default=None,
        description="Style ID from style_extractor (e.g. 'neubrutalism', 'glassmorphism')"
    )
    source_image_path: Optional[str] = Field(
        default=None,
        description="Path to source image if extracted from screenshot"
    )


# ---------------------------------------------------------------------------
# Chain Config Models (what goes into the Google Sheet)
# ---------------------------------------------------------------------------

class DetectedAPI(BaseModel):
    """An external API/service detected from step prompt text."""
    service_name: str = Field(description="e.g. 'Meta Marketing API'")
    service_key: str = Field(description="e.g. 'meta_marketing'")
    detection_pattern: str = Field(description="What text triggered detection")
    signup_url: str = Field(description="URL where user gets API key")
    required_env_vars: list[str] = Field(description="e.g. ['META_APP_ID', 'META_APP_SECRET']")


class ChainConfigRow(BaseModel):
    """One row in the Chain Config tab of the generated Google Sheet.

    Each row represents one executable step in the prompt chain.
    """
    row_number: int = Field(description="1-indexed row position in chain")
    step_type: StepType
    title: str = Field(description="Short step title for the sheet")
    prompt_template: str = Field(description="The AI prompt with {{variables}} and {{previousOutput}}")
    expected_output: str = Field(description="What this step should produce")
    input_source: str = Field(description="'user_input', 'row_N', or 'row_N+row_M' for merged inputs")
    output_destination: str = Field(description="'row_N_output' cell reference")
    model_recommendation: str = Field(default="sonnet", description="Recommended AI model for this step")
    apis_required: list[str] = Field(default_factory=list, description="Service keys needed, e.g. ['meta_marketing']")
    is_gate: bool = Field(default=False, description="If True, chain pauses here for user review")
    max_retries: int = Field(default=1, description="Auto-retry on failure")
    timeout_seconds: int = Field(default=120, description="Max execution time per step")
    notes: str = Field(default="", description="Implementation notes from video extraction")

    # Populated from the original YTStrategyStep
    original_step_id: str = Field(description="ID of the source YTStrategyStep")
    original_step_order: int = Field(description="Original order in the video")


class SheetBlueprint(BaseModel):
    """Complete blueprint for a Google Sheet tool.

    This is the intermediate representation between video extraction
    and actual Google Sheet creation.
    """
    blueprint_id: str = Field(description="Unique ID for this blueprint")
    tool_name: str = Field(description="Name of the tool (derived from video title)")
    tool_description: str = Field(description="One-line description of what the tool does")
    source_video_id: str = Field(description="YouTube video ID that generated this")
    source_video_title: str = Field(description="Original video title")
    source_video_channel: str = Field(description="Channel name")
    source_project_id: str = Field(description="YT Lab project ID")

    chain_config: list[ChainConfigRow] = Field(description="The prompt chain rows")
    detected_apis: list[DetectedAPI] = Field(description="All APIs detected across all steps")
    user_input_variables: list[str] = Field(
        description="Variables the user must fill in before running, e.g. ['{niche}', '{product}', '{budget}']"
    )

    theme: Optional[ThemeConfig] = Field(default=None, description="Selected theme (can be set/changed later)")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Tool Registry (persisted)
# ---------------------------------------------------------------------------

class GeneratedTool(BaseModel):
    """A generated tool tracked in the registry.

    Lifecycle: DRAFT → DEPLOYING → ACTIVE (or ERROR) → ARCHIVED
    """
    tool_id: str = Field(description="Unique tool identifier")
    blueprint: SheetBlueprint = Field(description="The full blueprint used to create this tool")
    status: ToolStatus = Field(default=ToolStatus.DRAFT)

    # Google Sheet details (populated after deployment)
    sheet_id: Optional[str] = Field(default=None, description="Google Sheets document ID")
    sheet_url: Optional[str] = Field(default=None, description="Direct link to the sheet")
    sheet_title: Optional[str] = Field(default=None, description="Title as it appears in Google Drive")

    # Theme (separate from blueprint so it can be swapped independently)
    active_theme: Optional[ThemeConfig] = Field(default=None, description="Currently applied theme")

    # Execution tracking
    times_run: int = Field(default=0, description="How many times the chain has been executed")
    last_run_at: Optional[str] = Field(default=None)
    total_tokens_used: int = Field(default=0, description="Cumulative token usage across all runs")

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list[str] = Field(default_factory=list, description="User-assigned tags for organization")


class ToolRegistry(BaseModel):
    """Root model for the tool registry file."""
    tools: list[GeneratedTool] = Field(default_factory=list)
    total_tools_created: int = Field(default=0)
    total_tools_deployed: int = Field(default=0)
```

#### 1.2 New TypeScript Types — add to `ui/src/lib/types.ts`

```typescript
// === Tool Factory Types ===

export type StepType = 'research' | 'generation' | 'action' | 'manual'
export type ToolStatus = 'draft' | 'deploying' | 'active' | 'error' | 'archived'
export type ThemeSource = 'preset' | 'extracted' | 'custom'

export interface ThemeColors {
  brand_light: string
  brand_default: string
  brand_dark: string
  surface_canvas: string
  surface_base: string
  surface_muted: string
  text_primary: string
  text_secondary: string
  text_tertiary: string
  border_subtle: string
  status_success: string
  status_error: string
  status_warning: string
}

export interface ThemeTypography {
  font_family_heading: string
  font_family_body: string
  font_weight_heading: number
  font_weight_body: number
  base_size_px: number
}

export interface ThemeComponents {
  card_radius_px: number
  button_radius_px: number
  input_radius_px: number
  shadow_card: string
  spacing_unit_px: number
  density: 'cozy' | 'compact'
}

export interface ThemeConfig {
  theme_id: string
  theme_name: string
  source: ThemeSource
  colors: ThemeColors
  typography: ThemeTypography
  components: ThemeComponents
  tailwind_config: Record<string, unknown>
  style_classification: string | null
  source_image_path: string | null
}

export interface DetectedAPI {
  service_name: string
  service_key: string
  detection_pattern: string
  signup_url: string
  required_env_vars: string[]
}

export interface ChainConfigRow {
  row_number: number
  step_type: StepType
  title: string
  prompt_template: string
  expected_output: string
  input_source: string
  output_destination: string
  model_recommendation: string
  apis_required: string[]
  is_gate: boolean
  max_retries: number
  timeout_seconds: number
  notes: string
  original_step_id: string
  original_step_order: number
}

export interface SheetBlueprint {
  blueprint_id: string
  tool_name: string
  tool_description: string
  source_video_id: string
  source_video_title: string
  source_video_channel: string
  source_project_id: string
  chain_config: ChainConfigRow[]
  detected_apis: DetectedAPI[]
  user_input_variables: string[]
  theme: ThemeConfig | null
  created_at: string
}

export interface GeneratedTool {
  tool_id: string
  blueprint: SheetBlueprint
  status: ToolStatus
  sheet_id: string | null
  sheet_url: string | null
  sheet_title: string | null
  active_theme: ThemeConfig | null
  times_run: number
  last_run_at: string | null
  total_tokens_used: number
  created_at: string
  updated_at: string
  tags: string[]
}
```

#### 1.3 Tool Registry Service — `server/services/tool_registry.py`

**Responsibilities:**
- CRUD operations on `~/.autoforge/tool_registry.json`
- Atomic file writes (write to `.tmp`, then rename)
- Query tools by status, tags, source video
- Track aggregate stats (total created, deployed, tokens used)

**Methods:**
```python
class ToolRegistryService:
    def __init__(self, registry_path: Path | None = None): ...
    async def create_tool(self, blueprint: SheetBlueprint) -> GeneratedTool: ...
    async def get_tool(self, tool_id: str) -> GeneratedTool | None: ...
    async def list_tools(self, status: ToolStatus | None = None, limit: int = 50, offset: int = 0) -> list[GeneratedTool]: ...
    async def update_tool(self, tool_id: str, **updates) -> GeneratedTool: ...
    async def update_theme(self, tool_id: str, theme: ThemeConfig) -> GeneratedTool: ...
    async def archive_tool(self, tool_id: str) -> GeneratedTool: ...
    async def record_run(self, tool_id: str, tokens_used: int) -> None: ...
    async def get_stats(self) -> dict: ...
    def _load(self) -> ToolRegistry: ...
    def _save(self, registry: ToolRegistry) -> None: ...
```

**Storage:** `~/.autoforge/tool_registry.json` — JSON first, SQLite migration in a later phase if needed.

**File safety:** Same pattern as `rate_limit_logger.py` — write to `.tmp` file, `os.replace()` for atomic swap, catch `OSError` and log.

---

### Phase 2: Blueprint Engine (YTStrategyStep[] → ChainConfig)

**Goal:** The transformation engine that converts video extraction output into a deployable sheet blueprint.

#### 2.1 Blueprint Generator — `server/services/sheet_blueprint.py`

This is the brain of the factory. It takes an array of YTStrategyStep objects and produces a complete SheetBlueprint.

**Core Transformation Pipeline:**

```
YTStrategyStep[]
    ↓
[1] Filter & Validate — remove empty/invalid steps
    ↓
[2] Classify Steps — assign StepType (RESEARCH/GENERATION/ACTION/MANUAL)
    ↓
[3] Detect APIs — scan prompt text for service mentions
    ↓
[4] Extract Variables — find {variable} patterns in prompts
    ↓
[5] Build Chain — wire input_source → output_destination references
    ↓
[6] Convert Prompts — transform video-style prompts into chain-executable prompts
    ↓
[7] Assemble Blueprint — combine all into SheetBlueprint
    ↓
SheetBlueprint
```

**Field-by-Field Mapping (YTStrategyStep → ChainConfigRow):**

| YTStrategyStep Field | → | ChainConfigRow Field | Transformation |
|---|---|---|---|
| `order` | → | `row_number` | Direct map (1-indexed) |
| `title` | → | `title` | Truncate to 60 chars, strip markdown |
| `prompt` | → | `prompt_template` | Convert to chain format (see §2.2) |
| `expectedOutput` | → | `expected_output` | Direct map |
| `model` | → | `model_recommendation` | Normalize to "opus"/"sonnet"/"haiku" |
| `id` | → | `original_step_id` | Direct map |
| `order` | → | `original_step_order` | Direct map |
| _(computed)_ | → | `step_type` | Classification function (see §2.3) |
| _(computed)_ | → | `input_source` | Chaining logic (see §2.4) |
| _(computed)_ | → | `output_destination` | `"row_{N}_output"` |
| _(computed)_ | → | `apis_required` | API detection (see §2.5) |
| _(computed)_ | → | `is_gate` | True if step_type == MANUAL |
| `notes` | → | `notes` | Direct map |
| `subSteps` | → | _(expanded)_ | Each subStep becomes notes or a sub-row |

#### 2.2 Smart Prompt Conversion

Video prompts are conversational ("Now take that research and generate 40 ad copy variations"). Chain prompts need to be structured and self-contained.

**Conversion rules:**
1. **Add context header:** Every prompt gets: `"You are executing Step {N} of {total} in a {tool_name} workflow."`
2. **Replace references:** "that research" → `{{row_1_output}}`, "the previous results" → `{{row_{N-1}_output}}`
3. **Add output format:** Append `"\n\nFormat your output as: {expectedOutput}"` if not already specified
4. **Inject variables:** Replace niche-specific terms with `{{variable_name}}` placeholders
5. **Add constraints:** For GENERATION steps, add word/item count if mentioned in video

**Conversion is done by Claude (Sonnet)** — not regex. The prompt:
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

#### 2.3 Step Classification Logic

```python
# Classification priority (checked in order):
# 1. ACTION — mentions uploading, sending, API calls, deploying
# 2. MANUAL — mentions review, approval, human decision
# 3. GENERATION — mentions creating, writing, designing content
# 4. RESEARCH — everything else (default)

ACTION_SIGNALS = [
    "upload", "send", "deploy", "publish", "post to", "push to",
    "submit", "create campaign", "launch", "import to", "export to",
    "sync", "connect to", "integrate with", "call api", "webhook"
]

MANUAL_SIGNALS = [
    "review", "approve", "select", "decide", "choose", "manually",
    "hand-pick", "curate", "evaluate", "compare and pick", "sign off"
]

GENERATION_SIGNALS = [
    "generate", "create", "write", "build", "design", "draft",
    "compose", "produce", "make", "craft", "develop", "format"
]
```

#### 2.4 Chain Wiring (Input → Output References)

Each step's `input_source` is computed based on the chain position:

```python
def compute_input_source(row_number: int, step: YTStrategyStep, all_steps: list) -> str:
    if row_number == 1:
        return "user_input"  # First step always takes user variables

    # Check if step prompt references multiple prior steps
    references = detect_prior_references(step.prompt, row_number)
    if len(references) > 1:
        return "+".join(f"row_{r}" for r in references)  # e.g. "row_1+row_3"

    # Default: previous row
    return f"row_{row_number - 1}"
```

#### 2.5 API Detection Engine

```python
API_PATTERNS: dict[str, dict] = {
    "openai": {
        "patterns": ["gpt", "openai", "chatgpt", "dall-e", "whisper"],
        "service_name": "OpenAI",
        "signup_url": "https://platform.openai.com/api-keys",
        "env_vars": ["OPENAI_API_KEY"],
    },
    "anthropic": {
        "patterns": ["claude", "anthropic"],
        "service_name": "Anthropic (Claude)",
        "signup_url": "https://console.anthropic.com/",
        "env_vars": ["ANTHROPIC_API_KEY"],
    },
    "meta_marketing": {
        "patterns": ["facebook ads", "meta ads", "instagram ads", "meta campaign", "meta marketing"],
        "service_name": "Meta Marketing API",
        "signup_url": "https://developers.facebook.com/",
        "env_vars": ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN"],
    },
    "google_ads": {
        "patterns": ["google ads", "adwords", "ppc campaign"],
        "service_name": "Google Ads",
        "signup_url": "https://ads.google.com/",
        "env_vars": ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET"],
    },
    "phantombuster": {
        "patterns": ["phantombuster", "phantom"],
        "service_name": "PhantomBuster",
        "signup_url": "https://phantombuster.com/",
        "env_vars": ["PHANTOMBUSTER_API_KEY"],
    },
    "apollo": {
        "patterns": ["apollo.io", "apollo", "lead enrichment"],
        "service_name": "Apollo.io",
        "signup_url": "https://app.apollo.io/",
        "env_vars": ["APOLLO_API_KEY"],
    },
    "instantly": {
        "patterns": ["instantly", "cold email", "email warmup"],
        "service_name": "Instantly",
        "signup_url": "https://instantly.ai/",
        "env_vars": ["INSTANTLY_API_KEY"],
    },
    "canva": {
        "patterns": ["canva", "design template"],
        "service_name": "Canva",
        "signup_url": "https://www.canva.com/developers/",
        "env_vars": ["CANVA_API_KEY"],
    },
    "airtable": {
        "patterns": ["airtable", "airtable base"],
        "service_name": "Airtable",
        "signup_url": "https://airtable.com/developers",
        "env_vars": ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"],
    },
    "zapier": {
        "patterns": ["zapier", "zap", "automation webhook"],
        "service_name": "Zapier",
        "signup_url": "https://zapier.com/developer",
        "env_vars": ["ZAPIER_WEBHOOK_URL"],
    },
    "stripe": {
        "patterns": ["stripe", "payment processing", "checkout"],
        "service_name": "Stripe",
        "signup_url": "https://dashboard.stripe.com/apikeys",
        "env_vars": ["STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET"],
    },
    "twilio": {
        "patterns": ["twilio", "sms api", "whatsapp api"],
        "service_name": "Twilio",
        "signup_url": "https://www.twilio.com/console",
        "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
    },
    "sendgrid": {
        "patterns": ["sendgrid", "transactional email"],
        "service_name": "SendGrid",
        "signup_url": "https://app.sendgrid.com/settings/api_keys",
        "env_vars": ["SENDGRID_API_KEY"],
    },
}

def detect_apis(steps: list[YTStrategyStep]) -> list[DetectedAPI]:
    """Scan all step prompts and detect required external APIs."""
    detected: dict[str, DetectedAPI] = {}
    for step in steps:
        text = f"{step.title} {step.prompt} {step.expected_output}".lower()
        for service_key, config in API_PATTERNS.items():
            if service_key in detected:
                continue
            for pattern in config["patterns"]:
                if pattern in text:
                    detected[service_key] = DetectedAPI(
                        service_name=config["service_name"],
                        service_key=service_key,
                        detection_pattern=pattern,
                        signup_url=config["signup_url"],
                        required_env_vars=config["env_vars"],
                    )
                    break
    return list(detected.values())
```

#### 2.6 Variable Extraction

```python
import re

def extract_user_variables(steps: list[YTStrategyStep]) -> list[str]:
    """Find all {variable} placeholders across all step prompts."""
    variables: set[str] = set()
    pattern = re.compile(r'\{(\w+)\}')

    for step in steps:
        for match in pattern.finditer(step.prompt):
            var_name = match.group(1)
            # Skip system variables
            if var_name not in ("previousOutput", "row_number", "total_steps"):
                variables.add(var_name)

    return sorted(variables)
```

#### 2.7 Blueprint Assembly — Main Entry Point

```python
async def generate_blueprint(
    project: YTStrategyProject,
    steps: list[YTStrategyStep],
    video_metadata: dict | None = None,
    theme: ThemeConfig | None = None,
) -> SheetBlueprint:
    """Generate a complete SheetBlueprint from YT Lab extraction output.

    This is the main entry point. Orchestrates the full pipeline:
    filter → classify → detect APIs → extract vars → build chain → assemble.
    """
```

---

### Phase 3: Theme Integration

**Goal:** Connect the existing `style_extractor.py` and `theme-factory` to the ThemeConfig model, with a preview UI.

#### 3.1 Theme Adapter — `server/services/sheet_theme_engine.py`

Converts between the existing theme formats and the new unified ThemeConfig.

**From style_extractor output → ThemeConfig:**
```python
def style_extraction_to_theme_config(extraction: dict) -> ThemeConfig:
    """Convert style_extractor.py output to ThemeConfig.

    The extraction dict has:
    - identified_style: {primary, primary_confidence, accent, accent_confidence}
    - extracted_tokens: Tailwind config JSON
    - tailwind_config: Same as extracted_tokens
    - style_guide_markdown: Full markdown report

    We map the Tailwind config colors into ThemeColors,
    the font info into ThemeTypography, etc.
    """
```

**From theme-factory preset → ThemeConfig:**
```python
def preset_theme_to_theme_config(theme_name: str) -> ThemeConfig:
    """Load a theme-factory preset and convert to ThemeConfig.

    Reads from .claude/skills/theme-factory/themes/{theme_name}.md,
    parses the color/font definitions, returns ThemeConfig.
    """
```

**Apply ThemeConfig to Google Sheets formatting:**
```python
def theme_to_sheets_format(theme: ThemeConfig) -> dict:
    """Convert ThemeConfig into Google Sheets API formatting requests.

    Returns a dict of:
    - header_format: CellFormat for header rows
    - body_format: CellFormat for body rows
    - accent_format: CellFormat for highlighted cells
    - input_format: CellFormat for user-input cells
    - status_formats: dict of status → CellFormat for conditional formatting
    - chart_colors: list of hex colors for any charts
    """
```

#### 3.2 Theme Router — `server/routers/tool_themes.py`

```
GET  /api/tool-factory/themes                     → List all available themes (presets + user-created)
GET  /api/tool-factory/themes/{theme_id}          → Get single theme details
POST /api/tool-factory/themes/extract              → Upload image → style_extractor → ThemeConfig
POST /api/tool-factory/themes/preview              → Get preview of theme applied to sample sheet data
PUT  /api/tool-factory/{tool_id}/theme             → Swap theme on existing tool (re-applies formatting)
POST /api/tool-factory/themes/custom               → Create custom theme from user inputs
```

#### 3.3 Theme Preview

The preview endpoint returns a JSON representation of what the sheet would look like with the theme:
```python
class ThemePreview(BaseModel):
    theme: ThemeConfig
    sample_cells: list[dict]  # 5-6 sample cells with applied formatting
    color_swatches: list[dict]  # Visual palette for UI display
    font_preview: dict  # Heading + body font rendered examples
```

---

### Phase 4: Sheet Deployer (Google Sheets API)

**Goal:** Create actual Google Sheets from SheetBlueprint, fully formatted and themed.

#### 4.1 Google OAuth Setup — `server/services/google_auth.py`

```python
"""Google OAuth 2.0 for Sheets API access.

Credentials stored at ~/.autoforge/google_credentials.json
Token stored at ~/.autoforge/google_token.json
"""

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # Only files we create
]

class GoogleAuthService:
    def __init__(self): ...
    async def get_credentials(self) -> Credentials: ...
    async def start_oauth_flow(self) -> str: ...  # Returns auth URL
    async def handle_oauth_callback(self, code: str) -> bool: ...
    async def is_authenticated(self) -> bool: ...
    async def revoke(self) -> None: ...
```

**OAuth flow:**
1. User clicks "Connect Google" in UI
2. Backend generates OAuth URL, returns it
3. User authorizes in browser, gets redirected back
4. Backend stores token at `~/.autoforge/google_token.json`
5. Auto-refresh when token expires

#### 4.2 Sheet Deployer — `server/services/sheet_deployer.py`

Creates the actual Google Sheet from a SheetBlueprint.

**Generated Sheet Structure (5 Tabs):**

**Tab 1: "Guide"**
- Row 1: Tool name (large, themed header)
- Row 2: Description
- Row 3: Source video link
- Row 4-N: Step-by-step instructions for using the tool
- Row N+1: List of required API keys with signup links
- Row N+2: Credits/attribution

**Tab 2: "Setup"**
- Row 1: Header "Configuration"
- Row 2-N: One row per user variable — Label | Input Cell | Description
- Row N+1: Header "API Keys"
- Row N+2-M: One row per detected API — Service Name | API Key Cell | Signup URL | Status (formula: =IF(B{row}="","Missing","Ready"))

**Tab 3: "Chain Config"**
- Header row: Step # | Title | Type | Prompt Template | Expected Output | Input Source | Status | Output | Run Time
- One row per ChainConfigRow
- Prompt Template cells are wide (400px column width)
- Status column uses conditional formatting (Pending=yellow, Running=blue, Done=green, Error=red)
- Output column is where execution results go

**Tab 4: "Output History"**
- Header: Run # | Timestamp | Step | Input Summary | Output Summary | Tokens Used | Duration
- Appended to after each chain execution
- Protected (user can view but chain writes here)

**Tab 5: "Chain Runner" (Optional — Apps Script)**
- Contains the Apps Script trigger code (if user opts in)
- Button-triggered macro that executes the chain step by step
- Calls Claude API using keys from Setup tab
- Writes outputs to Chain Config tab and logs to Output History

**Deployment function:**
```python
async def deploy_sheet(
    blueprint: SheetBlueprint,
    theme: ThemeConfig | None = None,
    folder_id: str | None = None,  # Google Drive folder
) -> dict:
    """Create a complete Google Sheet from blueprint.

    Returns:
        {"sheet_id": "...", "sheet_url": "...", "sheet_title": "..."}
    """
```

**Sheet creation uses batch update** — one API call for structure, one for formatting:
1. `spreadsheets.create()` — Creates sheet with all 5 tabs and column headers
2. `spreadsheets.batchUpdate()` — Applies all formatting (column widths, colors, fonts, conditional formatting, protection, data validation)

#### 4.3 Theme Application to Sheets

```python
def build_theme_requests(theme: ThemeConfig, sheet_ids: dict[str, int]) -> list[dict]:
    """Build Google Sheets API batchUpdate requests for theme application.

    Maps ThemeConfig to Sheets formatting:
    - theme.colors.brand_default → header row background
    - theme.colors.surface_base → body row background
    - theme.colors.surface_canvas → alternate row background
    - theme.colors.text_primary → body text color
    - theme.colors.brand_light → input cell highlight
    - theme.typography.font_family_heading → header font
    - theme.typography.font_family_body → body font
    - theme.components.card_radius_px → N/A in Sheets (ignored)
    - theme.colors.status_success → "Done" conditional format
    - theme.colors.status_error → "Error" conditional format
    - theme.colors.status_warning → "Pending" conditional format
    """
```

**Color format conversion:**
```python
def hex_to_sheets_color(hex_color: str) -> dict:
    """Convert '#FF5733' to {'red': 1.0, 'green': 0.341, 'blue': 0.2}"""
```

---

### Phase 5: UI — Generation Flow

**Goal:** "Generate Tool" button in YT Lab, with progress tracking and preview.

#### 5.1 New Components — `ui/src/components/tool-factory/`

| Component | Purpose |
|---|---|
| `GenerateToolButton.tsx` | Button in YT Lab project detail view — triggers blueprint generation |
| `BlueprintPreview.tsx` | Shows the generated blueprint before deployment — chain visualization, detected APIs, variables |
| `ThemePicker.tsx` | Grid of preset themes + "Upload Screenshot" button for image-to-theme + custom option |
| `ThemePreviewCard.tsx` | Single theme card showing color swatches, font names, sample formatting |
| `GenerationProgress.tsx` | SSE-driven progress bar showing: classifying → detecting APIs → converting prompts → assembling |
| `DeployConfirmation.tsx` | Final confirmation before creating Google Sheet — shows sheet name, tabs, theme, API keys needed |
| `DeploymentSuccess.tsx` | Post-deploy screen with: sheet link, copy button, QR code for mobile access |

#### 5.2 Generation Flow UX

```
YT Lab Project Detail (existing page)
  ↓ User clicks "Generate Tool" button
ThemePicker modal
  ↓ User picks theme (preset, upload image, or skip)
GenerationProgress overlay
  ↓ SSE stream shows each pipeline step completing
BlueprintPreview full-screen
  ↓ User reviews chain, edits if needed (inline editing)
DeployConfirmation modal
  ↓ User confirms → Google OAuth if not connected
DeploymentSuccess screen
  ↓ Link to Google Sheet, option to generate another
```

#### 5.3 Integration Point in YT Lab

The "Generate Tool" button appears in `YTStrategyLabPage.tsx` when viewing a project that has completed processing (has steps). It's added to the project detail view's action bar, alongside existing buttons.

---

### Phase 6: UI — Tool Manager

**Goal:** Browse, manage, re-theme, and share generated tools.

#### 6.1 New Page — Tool Manager

Accessible from the sidebar (new nav item) or from YT Lab after generation.

| View | What It Shows |
|---|---|
| **Tool List** | Grid/list of all generated tools with status badges, theme preview thumbnails, last-run dates |
| **Tool Detail** | Full blueprint view, chain visualization, theme preview, execution history, sharing options |
| **Theme Swap** | ThemePicker re-opened for an existing tool — preview before applying |

#### 6.2 Tool Manager Components

| Component | Purpose |
|---|---|
| `ToolManagerPage.tsx` | Main page with list/detail views |
| `ToolCard.tsx` | Card showing tool name, status, theme thumbnail, stats (runs, tokens) |
| `ToolDetailView.tsx` | Full tool details with tabs: Blueprint, Theme, History, Settings |
| `ChainVisualizer.tsx` | Visual flow diagram showing step connections (similar to DependencyGraph.tsx but for chain steps) |
| `ExecutionHistory.tsx` | Table of past runs with expandable details |
| `ShareToolModal.tsx` | Copy link, generate embed code, export as JSON |

---

### Phase 7: Batch & Scale

**Goal:** Process multiple videos into tools in one batch.

#### 7.1 Batch Generation Service — `server/services/batch_tool_generator.py`

```python
class BatchToolGenerator:
    """Generate tools from multiple YT Lab projects in sequence."""

    async def generate_batch(
        self,
        project_ids: list[str],
        default_theme: ThemeConfig | None = None,
        on_progress: Callable | None = None,
    ) -> list[GeneratedTool]: ...
```

**Integrates with existing batch infrastructure:**
- Uses same SSE pattern as `yt_batch.py` for progress
- Sequential processing (one tool at a time to avoid Sheets API quota issues)
- Per-tool error handling — one failure doesn't stop the batch
- Default theme applied to all tools in batch (can be changed individually later)

#### 7.2 Batch Endpoints

```
POST /api/tool-factory/batch/generate    → Generate tools from list of project IDs
GET  /api/tool-factory/batch/{batch_id}  → Poll batch progress
POST /api/tool-factory/batch/deploy      → Deploy all draft tools in a batch
```

#### 7.3 Queue Integration

If the Factory Task Queue ("The Train") is built, batch tool generation can be queued as a task:
```python
# Task type: "tool_generation"
# Payload: {"project_ids": [...], "theme_id": "ocean-depths"}
```

---

### Phase 8: SaaS Layer

**Goal:** Usage tracking, tier enforcement, billing hooks.

#### 8.1 Usage Tracking — `server/services/tool_usage.py`

```python
class ToolUsageTracker:
    """Track tool generation and execution for SaaS tier enforcement."""

    async def record_generation(self, user_id: str, tool_id: str) -> None: ...
    async def record_execution(self, user_id: str, tool_id: str, tokens: int) -> None: ...
    async def get_monthly_usage(self, user_id: str) -> dict: ...
    async def check_tier_limit(self, user_id: str, tier: str) -> bool: ...
```

**Tier limits:**
```python
TIER_LIMITS = {
    "free": {"tools_per_month": 5, "themes": ["preset_only"], "batch": False},
    "pro": {"tools_per_month": -1, "themes": ["all"], "batch": True},
    "enterprise": {"tools_per_month": -1, "themes": ["all"], "batch": True, "api_access": True, "white_label": True},
}
```

#### 8.2 Analytics Dashboard Component

| Metric | Display |
|---|---|
| Tools generated (this month / all time) | Counter with sparkline |
| Tools deployed (active vs draft vs error) | Donut chart |
| Total chain executions | Counter |
| Token usage (by model) | Stacked bar chart |
| Most-used themes | Horizontal bar |
| Top tools by execution count | Leaderboard list |
| Average generation time | Single stat |

---

### API Endpoint Summary (All Phases)

| Method | Path | Phase | Purpose |
|---|---|---|---|
| `POST` | `/api/tool-factory/generate` | 2 | Generate blueprint from YT Lab project |
| `POST` | `/api/tool-factory/generate-stream` | 2 | Same with SSE progress |
| `GET` | `/api/tool-factory/tools` | 1 | List all tools (filterable) |
| `GET` | `/api/tool-factory/tools/{tool_id}` | 1 | Get single tool |
| `DELETE` | `/api/tool-factory/tools/{tool_id}` | 1 | Archive a tool |
| `GET` | `/api/tool-factory/stats` | 1 | Aggregate statistics |
| `GET` | `/api/tool-factory/themes` | 3 | List available themes |
| `GET` | `/api/tool-factory/themes/{theme_id}` | 3 | Get theme details |
| `POST` | `/api/tool-factory/themes/extract` | 3 | Image → ThemeConfig |
| `POST` | `/api/tool-factory/themes/preview` | 3 | Preview theme on sample data |
| `POST` | `/api/tool-factory/themes/custom` | 3 | Create custom theme |
| `PUT` | `/api/tool-factory/tools/{tool_id}/theme` | 3 | Swap theme on existing tool |
| `POST` | `/api/tool-factory/deploy/{tool_id}` | 4 | Deploy blueprint to Google Sheet |
| `GET` | `/api/tool-factory/google/auth-url` | 4 | Get OAuth URL |
| `POST` | `/api/tool-factory/google/callback` | 4 | Handle OAuth callback |
| `GET` | `/api/tool-factory/google/status` | 4 | Check auth status |
| `POST` | `/api/tool-factory/batch/generate` | 7 | Batch generate from project list |
| `GET` | `/api/tool-factory/batch/{batch_id}` | 7 | Batch progress |
| `POST` | `/api/tool-factory/batch/deploy` | 7 | Batch deploy all drafts |
| `GET` | `/api/tool-factory/usage` | 8 | Usage stats for SaaS |

---

### File Creation Summary (All Phases)

| Phase | File | Type | Purpose |
|---|---|---|---|
| 1 | `server/models/tool_factory.py` | New | All Pydantic data models |
| 1 | `server/services/tool_registry.py` | New | Tool CRUD + persistence |
| 1 | `ui/src/lib/types.ts` | Edit | Add TypeScript interfaces |
| 2 | `server/services/sheet_blueprint.py` | New | Blueprint generation engine |
| 3 | `server/services/sheet_theme_engine.py` | New | Theme adapter + Sheets formatting |
| 3 | `server/routers/tool_themes.py` | New | Theme REST endpoints |
| 3 | `ui/src/hooks/useToolThemes.ts` | New | React Query hooks for themes |
| 3 | `ui/src/components/tool-factory/ThemePicker.tsx` | New | Theme selection UI |
| 3 | `ui/src/components/tool-factory/ThemePreviewCard.tsx` | New | Theme preview card |
| 4 | `server/services/google_auth.py` | New | Google OAuth handler |
| 4 | `server/services/sheet_deployer.py` | New | Google Sheets creation |
| 4 | `server/routers/tool_factory.py` | New | Main factory REST endpoints |
| 4 | `ui/src/hooks/useToolFactory.ts` | New | React Query hooks for factory |
| 5 | `ui/src/components/tool-factory/GenerateToolButton.tsx` | New | Entry point in YT Lab |
| 5 | `ui/src/components/tool-factory/BlueprintPreview.tsx` | New | Blueprint review UI |
| 5 | `ui/src/components/tool-factory/GenerationProgress.tsx` | New | SSE progress display |
| 5 | `ui/src/components/tool-factory/DeployConfirmation.tsx` | New | Pre-deploy confirmation |
| 5 | `ui/src/components/tool-factory/DeploymentSuccess.tsx` | New | Post-deploy success screen |
| 6 | `ui/src/components/tool-factory/ToolManagerPage.tsx` | New | Tool browsing/management |
| 6 | `ui/src/components/tool-factory/ToolCard.tsx` | New | Tool list card |
| 6 | `ui/src/components/tool-factory/ToolDetailView.tsx` | New | Full tool detail view |
| 6 | `ui/src/components/tool-factory/ChainVisualizer.tsx` | New | Chain flow diagram |
| 6 | `ui/src/components/tool-factory/ExecutionHistory.tsx` | New | Run history table |
| 7 | `server/services/batch_tool_generator.py` | New | Batch processing |
| 8 | `server/services/tool_usage.py` | New | SaaS usage tracking |
| — | `server/routers/__init__.py` | Edit | Register new routers |
| — | `server/main.py` | Edit | Include new routers |
| — | `ui/src/lib/api.ts` | Edit | Add API client functions |

---

### Dependencies & Prerequisites

| Dependency | Phase Needed | Install |
|---|---|---|
| `google-api-python-client` | Phase 4 | `pip install google-api-python-client` |
| `google-auth-oauthlib` | Phase 4 | `pip install google-auth-oauthlib` |
| `google-auth-httplib2` | Phase 4 | `pip install google-auth-httplib2` |
| `anthropic` | Phase 2 | Already installed |
| All existing deps | All | Already in requirements.txt |

**Google Cloud Setup (one-time, done by owner):**
1. Create project in Google Cloud Console
2. Enable Google Sheets API + Google Drive API
3. Create OAuth 2.0 credentials (Desktop or Web app)
4. Download `client_secret.json` → save as `~/.autoforge/google_credentials.json`
5. First run triggers OAuth consent flow in browser

---

### Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Google Sheets API quota (100 requests/100sec/user) | Medium | Batch all formatting into single batchUpdate call; rate limit deploy operations |
| OAuth token expiry mid-batch | Low | Auto-refresh logic in google_auth.py; retry with fresh token on 401 |
| Claude prompt conversion quality | Medium | Use Sonnet (cheap) for conversion; show preview before deploy; allow manual editing |
| Theme extraction accuracy | Low | style_extractor.py already tested; fallback to "Modern Minimalist" if extraction fails |
| Generated sheets too complex for users | Medium | Guide tab with step-by-step instructions; keep chain under 15 steps; clear status indicators |
| SaaS tier enforcement bypass | Low | Server-side check on every generation; usage tracked in registry |

---

### Success Metrics

| Metric | Target | Measured By |
|---|---|---|
| Blueprint generation time | < 30 seconds | Server-side timer |
| Sheet deployment time | < 10 seconds | Sheets API response time |
| Theme swap time | < 5 seconds | Re-formatting API call |
| Chain accuracy (steps match video) | > 85% | User feedback / manual review |
| API detection accuracy | > 90% | Pattern matching coverage tests |
| Tools generated per day (at scale) | 100+ | Registry stats |
| End-to-end (video → working tool) | < 10 minutes | Includes user review time |
