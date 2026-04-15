# HANDOFF: YT Lab Execution Engine — Make Tools Actually Work

**Date:** 2026-04-15
**Context:** The YT Lab already creates incredible 8-12 step prompt chains from YouTube videos. The Tool Runner page exists (638 lines, full 3-panel UI). The component registry exists (337 lines, auto-detects capabilities). The execution engine exists (622 lines, dispatches to correct executor). But tools still can't fully execute because the actual execution handlers are incomplete — they dispatch to handlers that don't exist yet.

**Goal:** Fill in the missing execution nodes so that when a user hits "Run" on a tool, every step actually executes — API calls happen, web pages get scraped, files get created, emails get sent. Then build the "warehouse" system where each tool gets a standardized page with parameter inputs.

---

## WHAT EXISTS (DO NOT REBUILD)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Tool Runner UI | `ui/src/pages/ToolRunnerPage.tsx` | 638 | Built — 3-panel layout, SSE streaming, all execution modes |
| Tool Runner Backend | `server/services/tool_runner.py` | 622 | Built — orchestrates step execution, dispatches to handlers |
| Tool Runner Router | `server/routers/tool_runner.py` | 194 | Built — SSE streaming endpoint, run/cancel/state |
| Component Registry | `server/services/component_registry.py` | 337 | Built — auto-detects available components |
| Step Classifier | `server/services/sheet_blueprint.py` | 771 | Built — 7 step types (generation, research, action, manual, api_call, browser_action, file_create, webhook) |
| API Adapter Framework | `server/services/api_adapters/base.py` | Exists | Built — base adapter interface |
| File Creator Adapter | `server/services/api_adapters/file_creator.py` | Exists | Built — file writing handler |
| Webhook Adapter | `server/services/api_adapters/webhook.py` | Exists | Built — webhook POST handler |
| Tool Factory Routes | `server/routers/tool_factory.py` | 30+ endpoints | Built — CRUD, blueprint gen, deploy, batch, usage |
| Sheet Deployer | `server/services/sheet_deployer.py` | Large | Built — deploys to Google Sheets with Apps Script |
| Tool Analyzer PRD | `docs/prd-yt-lab-tool-analyzer.md` | 617 | Designed — self-improving component system |
| Execution Engine PRD | `docs/prd-tool-execution-engine.md` | 430 | Designed — hybrid execution architecture |
| YT Lab v2 PRD | `docs/prd-yt-lab-v2.md` | 313 | Designed — multi-video, game plan, revolver outputs |

---

## WHAT NEEDS TO BE BUILT

### Node 1: Full Web Scraper (Playwright + Fallback)

**Priority: HIGHEST — unblocks the most steps across all tools**

This is NOT a lightweight BeautifulSoup scraper. This is a full-capacity Playwright-powered scraping engine that handles everything from simple URL content extraction to JavaScript-rendered pages to authenticated scraping.

**Architecture — Tiered Scraper:**

```
Tier 1: Light Scrape (requests + BeautifulSoup)
  → Static pages, simple content extraction
  → Fastest, zero overhead
  → Falls through to Tier 2 if content is JS-rendered or empty

Tier 2: Playwright Headless
  → JavaScript-rendered pages (SPAs, React sites, dynamic content)
  → Pages behind light auth (cookies, basic login)
  → Content that requires scrolling/interaction to load
  → Full DOM access, can execute JS

Tier 3: Playwright Full Browser
  → Complex multi-step scraping (navigate → login → search → extract)
  → Sites with anti-bot protection
  → Screenshot capture during scrape for debugging
  → Cookie/session persistence across scrape jobs

Auto-tier selection:
  → Try Tier 1 first (instant)
  → If content < 100 chars or JS framework detected → escalate to Tier 2
  → If auth required or multi-step → Tier 3
  → User can force a tier via parameter
```

**Scraper Types to Support:**

| Type | Input | Output | Example |
|------|-------|--------|---------|
| URL Content | URL | Clean text + metadata | "Scrape this blog post" |
| Search Results | Query + engine | Top N results with titles/URLs/snippets | "Google 'best CRM for startups'" |
| Social Posts | Platform URL | Post text + comments + engagement data | Reddit thread, Twitter thread |
| Sitemap Crawl | Root URL + depth | All pages with extracted content | "Crawl competitor site" |
| Structured Data | URL + CSS selectors or schema | JSON structured data | "Get all product prices from this page" |
| Screenshot | URL | PNG image | "Screenshot this landing page" |
| PDF Extract | URL to PDF | Text content | "Extract text from this PDF" |

**Files to Create:**
```
server/services/execution/web_scraper.py     — Main scraper orchestrator (tiered)
server/services/execution/scraper_types.py   — URL, search, social, sitemap, structured, screenshot
server/services/execution/browser_pool.py    — Playwright browser instance management
```

**Integration Point:**
- `tool_runner.py` → when step needs scraping (keywords: "scrape", "extract from", "crawl", "search for", "get data from") → dispatch to web_scraper
- Register in component_registry.py as "web_scraper" with all tier capabilities

**Dependencies:**
```
pip install playwright beautifulsoup4 trafilatura requests lxml
playwright install chromium
```

**Difficulty: 5/10** (Playwright is well-documented, the tiered pattern is clean)

---

### Node 2: External API Executor (Generic + Known Adapters)

**What:** A generic HTTP client that can call ANY external API, plus pre-built adapters for the 13 most common APIs found across tool blueprints.

**Generic Adapter (handles unknown APIs):**
```python
class GenericAPIAdapter(BaseAdapter):
    """Calls any API with method, URL, headers, body."""
    async def execute(self, config: dict) -> dict:
        # config = {method, url, headers, body, auth_type, api_key_env_var}
        # Handles: API key in header, Bearer token, Basic auth, OAuth2
        # Returns: status_code, response_body, headers
```

**Pre-built Adapters (known APIs with helper methods):**

| Adapter | Service | Key Methods | Difficulty |
|---------|---------|-------------|------------|
| `meta_ads.py` | Facebook/Instagram Ads | create_campaign, upload_creative, get_metrics | 4/10 |
| `stripe_api.py` | Stripe | create_product, create_checkout, get_payments | 3/10 |
| `apollo_api.py` | Apollo.io | search_people, enrich_email, get_company | 3/10 |
| `instantly_api.py` | Instantly | add_leads, create_campaign, get_stats | 3/10 |
| `phantombuster_api.py` | PhantomBuster | launch_phantom, get_results | 2/10 |
| `sendgrid_api.py` | SendGrid | send_email, create_template | 2/10 |
| `airtable_api.py` | Airtable | create_record, list_records, update_record | 2/10 |
| `google_ads_api.py` | Google Ads | create_campaign, get_keywords | 4/10 |
| `canva_api.py` | Canva | create_design, export_png | 3/10 |
| `supabase_api.py` | Supabase | insert, select, update, rpc | 2/10 |
| `vercel_api.py` | Vercel | deploy_project, get_deployments | 3/10 |
| `railway_api.py` | Railway | deploy_service, get_logs | 3/10 |
| `openai_api.py` | OpenAI | chat_completion, embeddings, image_gen | 2/10 |

**Files to Create:**
```
server/services/api_adapters/generic.py        — Universal HTTP adapter
server/services/api_adapters/meta_ads.py       — Meta Marketing API
server/services/api_adapters/stripe_api.py     — Stripe
server/services/api_adapters/apollo_api.py     — Apollo.io
server/services/api_adapters/instantly_api.py  — Instantly
server/services/api_adapters/phantombuster_api.py
server/services/api_adapters/sendgrid_api.py
server/services/api_adapters/airtable_api.py
server/services/api_adapters/google_ads_api.py
server/services/api_adapters/canva_api.py
server/services/api_adapters/supabase_api.py
server/services/api_adapters/vercel_api.py
server/services/api_adapters/railway_api.py
server/services/api_adapters/openai_api.py
```

**Integration Point:**
- `tool_runner.py` → when step.type == "api_call" → read `apis_required` from step config → instantiate correct adapter → execute
- API keys read from tool's variables panel (user enters them in the Tool Runner UI right panel)

**Difficulty: 5/10 total** (each adapter is 2-4/10 individually, but there are 13+1 of them)

---

### Node 3: Browser Automation Handler (Playwright Interactive)

**Different from the scraper.** The scraper READS data. This DOES things — fills forms, clicks buttons, uploads files, navigates multi-step workflows.

**Use Cases:**
- "Upload these ad creatives to Meta Ads Manager"
- "Log into Stripe and create a product"
- "Fill out this form on competitor's site"
- "Deploy this app to Vercel via their dashboard"

**Architecture:**
```python
class BrowserAutomator:
    """Interactive browser automation for action steps."""
    
    async def execute_action(self, instruction: str, context: dict) -> dict:
        """
        1. Parse instruction into action sequence (AI-generated)
        2. Execute each action via Playwright
        3. Capture screenshots at each step
        4. Return result + screenshot audit trail
        """
    
    async def login_and_persist(self, service: str, credentials: dict):
        """Login once, save cookies for future steps."""
    
    async def multi_step_workflow(self, steps: list[dict]):
        """Execute a sequence of browser actions."""
```

**Playwright Session Management:**
- One browser instance per tool run (shared across steps)
- Cookie/session persistence across steps (login once, reuse)
- Screenshot capture at each action for audit trail
- Auto-retry on selector failures (wait + retry 3x)
- Error recovery: screenshot + HTML dump on failure

**Files to Create:**
```
server/services/execution/browser_automator.py  — Interactive browser actions
server/services/execution/browser_session.py    — Session/cookie management
```

**Integration Point:**
- `tool_runner.py` → when step.type == "browser_action" → dispatch to browser_automator
- Uses same Playwright browser pool as the scraper (shared resource)

**Difficulty: 6/10** (multi-step workflows with error recovery are complex)

---

### Node 4: Deployment Executor

**What:** Deploys generated code/apps to hosting platforms via their CLIs or APIs.

**Supported Targets:**
| Target | Method | What It Does |
|--------|--------|-------------|
| Vercel | CLI (`vercel deploy`) or API | Deploy frontend apps |
| Railway | CLI (`railway up`) or API | Deploy backend services |
| Cloudflare Pages | CLI (`wrangler pages deploy`) | Deploy static sites |
| Local filesystem | Direct write | Save files locally |
| Google Drive | Sheets API (already built) | Deploy to Sheets |

**Files to Create:**
```
server/services/execution/deployer.py  — Deployment orchestrator
```

**Difficulty: 4/10** (mostly CLI wrappers)

---

### Node 5: Email/Notification Sender

**What:** Sends emails, Slack messages, Discord messages, SMS.

**Channels:**
| Channel | Service | Method |
|---------|---------|--------|
| Email | SendGrid | API call via sendgrid adapter |
| Slack | Slack Webhooks | POST to webhook URL |
| Discord | Discord Webhooks | POST to webhook URL |
| SMS | Twilio | API call |

**Files to Create:**
```
server/services/execution/notification_sender.py  — Multi-channel notifications
```

**Difficulty: 2/10** (webhook POSTs + API calls, simple)

---

## THE WAREHOUSE: Standardized Tool Pages

### The Vision

Every tool gets the same standardized page — like rooms in a warehouse. Same layout, same structure, just different content/parameters. You're NOT building 50 custom pages. You're building ONE page template that loads any tool.

### How It Works

The Tool Runner page (`ToolRunnerPage.tsx`) already exists with 3 panels. It needs to be enhanced to be the "warehouse room":

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOOL: GTM Engineering Automation Dashboard                        │
│  Source: "Claude Code Replaced My 20-Person Marketing Team"        │
│  Steps: 10  |  Ready: 8/10  |  Est. Time: 45 min                 │
├──────────────┬──────────────────────────┬──────────────────────────┤
│              │                          │                          │
│  STEPS       │  CURRENT STEP            │  YOUR PARAMETERS         │
│              │                          │                          │
│  1. ✅ Done  │  Step 3: Build Bulk Ad   │  🏷 niche: ___________  │
│  2. ✅ Done  │  Creative Generator      │  🏷 product_name: ____  │
│  3. ▶ Run   │                          │  🏷 hex_codes: ________  │
│  4. ⏳ Wait  │  [Prompt Template]       │  🏷 landing_page_url: _ │
│  5. ⏳ Wait  │  ...                     │  🏷 strapi_url: _______  │
│  6. ⏳ Wait  │                          │  🔑 META_ACCESS_TOKEN: _ │
│  7. ⏳ Wait  │  [Output Area]           │  🔑 APOLLO_API_KEY: ____ │
│  8. ⏳ Wait  │  ...                     │  🔑 INSTANTLY_API_KEY: _ │
│  9. ⏳ Wait  │                          │                          │
│ 10. ⏳ Wait  │                          │  [Save Config]           │
│              │                          │  [Load Previous Run]     │
│              │                          │                          │
│  [Run All]   │  [Run This Step]         │                          │
│  [Pause]     │  [Skip]                  │                          │
│  [Stop]      │  [Retry]                 │                          │
│              │                          │                          │
├──────────────┴──────────────────────────┴──────────────────────────┤
│  Status: Step 3 executing... | Tokens: 2,340 | Duration: 0:42     │
└─────────────────────────────────────────────────────────────────────┘
```

### What Needs to Change in Tool Runner

| Current State | Needed State |
|--------------|-------------|
| Variables panel shows raw JSON | Variables panel shows labeled input fields with descriptions |
| No input validation | Validate required fields before run |
| No saved configurations | Save/load parameter configs per tool |
| No API key management | Dedicated API key section with masked inputs |
| Steps just show prompt text | Steps show prompt + what it will DO (execution mode label) |
| Output is raw text | Output formatted by type (text, JSON, file link, screenshot) |
| No run history | View previous runs and their outputs |

### The Tool Library (Warehouse Index)

A new page or section that shows all available tools as a grid:

```
┌──────────────────────────────────────────────────────────────────┐
│  🏭 TOOL WAREHOUSE                          [+ Import Video]    │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ GTM Engine  │ │ SEO Audit   │ │ Cold Email  │ │ LinkedIn   ││
│  │             │ │             │ │ Generator   │ │ Scraper    ││
│  │ 10 steps    │ │ 8 steps     │ │ 6 steps     │ │ 9 steps    ││
│  │ ✅ Ready    │ │ ✅ Ready    │ │ ⚠️ 1 gap   │ │ ✅ Ready   ││
│  │ [Run]       │ │ [Run]       │ │ [Fix Gaps]  │ │ [Run]      ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘│
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ Content     │ │ Ad Creative │ │ Competitor  │ │ Podcast    ││
│  │ Repurposer  │ │ Factory     │ │ Intel       │ │ to Blog    ││
│  │ 12 steps    │ │ 7 steps     │ │ 11 steps    │ │ 5 steps    ││
│  │ ✅ Ready    │ │ ✅ Ready    │ │ ⚠️ 2 gaps  │ │ ✅ Ready   ││
│  │ [Run]       │ │ [Run]       │ │ [Fix Gaps]  │ │ [Run]      ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘│
│                                                                   │
│  Coverage: 45/50 tools ready (90%)  |  Components: 14/14 built  │
└──────────────────────────────────────────────────────────────────┘
```

**Route:** `/#/tools` (already exists in App.tsx)
**Clicking [Run]** → navigates to `/#/tools/:toolId/run` (ToolRunnerPage)

---

## OUTPUT MODES (THE REVOLVER)

When a video is processed, the user should be able to choose what comes out:

| Mode | Output | Who It's For |
|------|--------|-------------|
| **Executable Tool** | Full chain config deployed to Tool Runner | Running the workflow end-to-end |
| **Step-by-Step Checklist** | Printable numbered checklist with human-readable instructions | Learning the process manually |
| **Skill/Prompt** | Claude skill file (SKILL.md format) | Reusable prompt template |
| **Hybrid Playbook** | Checklist with markers: ROBOT = automated, HUMAN = manual step | Deciding what to automate |
| **API Flow** | n8n/Activepieces flow definition | External automation platforms |

**Current state:** Hardcoded to produce one output (the chain config / tool).
**Needed:** A selector after video processing that lets user pick output mode, or generate all modes at once.

**Files to Modify:**
- `server/services/yt_processor.py` — Add output mode parameter
- `ui/src/pages/YTStrategyLabPage.tsx` — Add output mode selector after processing

---

## SELF-IMPROVING SYSTEM (FROM ANALYZER PRD)

Already fully designed in `docs/prd-yt-lab-tool-analyzer.md`. Key phases to build:

| Phase | What | Difficulty | Depends On |
|-------|------|------------|-----------|
| Quick Check | "Can this tool execute?" scan before Generate | 4/10 | Component Registry (built) |
| Gap Analysis | Detailed breakdown of missing components + PRD generation | 5/10 | Quick Check |
| Auto-Fix Loop | Execute → Fail → Diagnose → Fix → Retry | 6/10 | Tool Runner (built) |
| Self-Build | When gap found ≤5/10 difficulty, spawn agent to build it | 7/10 | Gap Analysis |

**The overnight factory vision:** Queue 10 videos before bed. System processes each, finds gaps, auto-builds missing components, and by morning all 10 tools are ready. Each video it can't process makes it smarter for the next one.

---

## BUILD ORDER (RECOMMENDED)

```
Session 1: Web Scraper Node (5/10)
  → Install Playwright, build tiered scraper
  → Register in component_registry
  → Test with 3 tool steps that need scraping

Session 2: API Adapter Expansion (5/10)
  → Generic adapter + 3 highest-impact specific adapters
  → (Meta, Stripe, Apollo — these appear most across tools)
  → Register all in component_registry

Session 3: Browser Automator (6/10)
  → Interactive Playwright for action steps
  → Session/cookie management
  → Screenshot audit trail

Session 4: Tool Runner UI Enhancement (4/10)
  → Parameter input fields (not raw JSON)
  → API key management section
  → Run history / saved configs
  → Output formatting by type

Session 5: Tool Warehouse Page (3/10)
  → Grid view of all tools
  → Readiness indicators
  → One-click run navigation

Session 6: Output Mode Revolver (4/10)
  → Add mode selector to YT Lab
  → Checklist mode, skill mode, hybrid mode
  → Generate all modes from same processing

Session 7: Remaining API Adapters (3/10)
  → Build out remaining 10 adapters
  → Each is 2-3/10, batch them

Session 8: Self-Improving System (7/10)
  → Quick Check integration into YT Lab UI
  → Gap Analysis with PRD generation
  → Auto-build trigger for easy components

Session 9: Deployment Executor + Notifications (4/10)
  → Vercel/Railway/Cloudflare deployment
  → Email/Slack/Discord notification sender
```

---

## KEY FILES REFERENCE

### Already Built (read these first to understand patterns):
```
server/services/tool_runner.py              — Execution engine (how steps dispatch)
server/services/component_registry.py       — Component detection (how to register new ones)
server/services/api_adapters/base.py        — Adapter interface (how to build new adapters)
server/services/api_adapters/file_creator.py — Example adapter implementation
server/services/api_adapters/webhook.py     — Example adapter implementation
server/services/sheet_blueprint.py          — Step classification (classify_step function)
ui/src/pages/ToolRunnerPage.tsx             — Tool Runner UI (3-panel layout)
server/routers/tool_runner.py               — Tool Runner API endpoints
```

### PRDs to Read (design decisions already made):
```
docs/prd-tool-execution-engine.md           — Full hybrid execution architecture
docs/prd-yt-lab-tool-analyzer.md            — Self-improving component system
docs/prd-yt-lab-v2.md                       — Multi-video pipeline + output modes
docs/prd-video-to-tool-factory.md           — Video-to-tool factory pipeline
```

### New Files to Create:
```
server/services/execution/web_scraper.py
server/services/execution/scraper_types.py
server/services/execution/browser_pool.py
server/services/execution/browser_automator.py
server/services/execution/browser_session.py
server/services/execution/deployer.py
server/services/execution/notification_sender.py
server/services/api_adapters/generic.py
server/services/api_adapters/meta_ads.py
server/services/api_adapters/stripe_api.py
server/services/api_adapters/apollo_api.py
server/services/api_adapters/instantly_api.py
server/services/api_adapters/phantombuster_api.py
server/services/api_adapters/sendgrid_api.py
server/services/api_adapters/airtable_api.py
server/services/api_adapters/google_ads_api.py
server/services/api_adapters/canva_api.py
server/services/api_adapters/supabase_api.py
server/services/api_adapters/vercel_api.py
server/services/api_adapters/railway_api.py
server/services/api_adapters/openai_api.py
server/services/tool_analyzer.py
server/routers/tool_analyzer.py
server/services/auto_builder.py
```

---

## SUBSCRIPTION AUTH REMINDER

ALL Claude API calls MUST use subscription auth (`force_subscription=True`). See `docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md`. The existing `tool_runner.py` already uses the correct SDK pattern from `yt_processor.py._call_via_sdk()`. New execution nodes that call Claude MUST follow the same pattern.

---

## THE BUSINESS MODEL

The warehouse fills up with 40-50+ tool workflows. Each one:
- Extracted from expert YouTube videos (the best strategies from the best creators)
- Fully executable with real API integrations
- Standardized page with fill-in-the-blank parameters
- Subscription model: businesses pay monthly to access the warehouse

**The moat:** The self-improving system means every new video makes the platform more capable. Competitors would need to rebuild the entire component library from scratch. You have a head start of every video you've already processed.

---

## WHAT THE CODER NEEDS TO KNOW

1. **Read the existing adapters first** — `base.py`, `file_creator.py`, `webhook.py` show the pattern
2. **Read tool_runner.py** — understand how `execute_step()` dispatches to handlers
3. **Read component_registry.py** — understand how to register new components
4. **Playwright must be installed on the server** — `pip install playwright && playwright install chromium`
5. **Don't modify existing working code** unless the handoff says to
6. **Each execution node is independent** — they can be built and tested in isolation
7. **Test each node against real tool steps** — use the existing 16 tools' chain configs as test cases
