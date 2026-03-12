# PRD: API Research Engine for Tool Factory Blueprint Generation

## Overview

When the Tool Factory generates a blueprint from YouTube strategy steps, it detects which external APIs/services are needed (e.g., PhantomBuster, Apollo, Meta Marketing API). Currently it just lists them with "Get API key" links. This PRD adds a **real-time research step** that evaluates each detected API's pricing, finds cheaper alternatives, and flags red flags — so the user can make an informed cost/performance decision before committing to a toolset.

## Problem

- User sees "PhantomBuster — Get API key" but doesn't know it costs $56-69/month minimum
- No visibility into whether cheaper alternatives exist (e.g., Apify covers most scraping use cases at a fraction of the cost)
- Some APIs require paid plans just to access the API ($85/month minimums, etc.) — these are red flags the user needs before investing time building a tool around them
- User plans to generate 5-10 tools/day from 20 YouTube videos — uninformed API choices at scale = wasted money

## Solution

Two-layer system:

### Layer 1: Static Pricing Database (Option C)

A Python dict of the ~20 most common APIs with known pricing data. Loads instantly, serves as fallback when web research fails or times out.

**For each API entry:**
- `service_name` — Display name
- `pricing_summary` — One-line summary (e.g., "Starts at $56/mo, no free API tier")
- `free_tier` — Boolean + description (e.g., "Yes — 100 contacts/month free" or "No — paid plan required for API access")
- `api_access_cost` — Monthly cost just to GET API access (the red flag number)
- `per_unit_cost` — Cost per operation if usage-based
- `alternatives` — List of 2-3 alternatives with name, pricing, and tradeoff description
- `red_flags` — List of strings (e.g., "Requires $85/month minimum plan for API access", "Rate limited to 100 requests/hour on free tier")
- `last_verified` — Date string for when this data was last checked
- `category` — What type of service (scraping, enrichment, email, ads, CMS, etc.)

**Initial APIs to cover (from the current API_REGISTRY):**

| Service | Category | Key Pricing Facts |
|---------|----------|-------------------|
| OpenAI | AI/LLM | Pay-per-token, generous free tier |
| Anthropic (Claude) | AI/LLM | Pay-per-token or subscription |
| Meta Marketing API | Advertising | Free with Facebook app, complex setup |
| Google Ads | Advertising | Free API, spend-based billing |
| PhantomBuster | Scraping/Automation | $56-69/mo minimum, no free API tier |
| Apollo.io | Lead Enrichment | Free tier (limited), paid starts ~$49/mo |
| Instantly | Email Outreach | Starts ~$30/mo, API on Growth plan+ |
| Canva | Design | Free tier exists, API access varies |
| Airtable | Database | Free tier, API included on all plans |
| Zapier | Automation | Free tier (limited), API on paid plans |
| Stripe | Payments | Free API, percentage-based fees |
| Twilio | SMS/Voice | Pay-per-use, generous free trial credits |
| SendGrid | Email | Free tier (100 emails/day), API included |

**Additional alternatives to include in database (not in current API_REGISTRY but should be suggested):**

| Service | Category | Why It's Notable |
|---------|----------|------------------|
| Apify | Scraping | Cheap alternative to PhantomBuster, covers most scraping with 3-10 options per site type |
| ScrapingBee | Scraping | Simple API, pay-per-request |
| Bright Data | Scraping | Enterprise-grade, expensive but powerful |
| Hunter.io | Email Finding | Alternative to Apollo for email lookup |
| Snov.io | Lead Enrichment | Cheaper Apollo alternative |
| Lemlist | Email Outreach | Alternative to Instantly |
| Mailgun | Email | Alternative to SendGrid, generous free tier |
| Supabase | Database | Free alternative to Airtable for structured data |
| Make (Integromat) | Automation | Cheaper Zapier alternative |
| n8n | Automation | Self-hosted, free alternative to Zapier |

### Layer 2: Real-Time Web Research (Option B)

For each detected API, use Claude (Sonnet) with web search enabled to get current pricing. This is the primary source — static DB is the fallback.

**Implementation:**

1. After `detect_apis()` returns the list of detected services, add a new pipeline step: `research_api_pricing(detected_apis)`
2. For each detected API, make a Claude call with `WebSearchTool` enabled:
   - System prompt: "You are an API pricing research assistant. Search the web for current, accurate pricing information."
   - User prompt: "Research the current pricing for {service_name} ({signup_url}). Return: 1) Pricing tiers, 2) Free tier availability and limits, 3) Monthly cost for API access, 4) Per-unit costs, 5) Two cheaper alternatives for {category} use cases with pricing comparison, 6) Any red flags (minimum spend, annual contracts, API access restrictions). Return as JSON."
3. Parse the response into the `APIResearchResult` data structure
4. Fall back to static DB entry if web research fails or times out

**Claude SDK configuration for research calls:**
```python
ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        cli_path=system_cli,
        system_prompt=API_RESEARCH_SYSTEM_PROMPT,
        env=get_effective_sdk_env(force_subscription=True),
        max_turns=4,  # search → read → synthesize → format
        permission_mode="bypassPermissions",
        allowed_tools=["WebSearchTool"],
        cwd=scratch_dir,
    )
)
```

**Timeout:** 90 seconds per API (web search takes longer than direct prompts).

**Progress messages:**
- "Researching API pricing 1/{total}: {service_name}..."
- "Researching API pricing 2/{total}: {service_name}..."
- etc.

### Pipeline Integration

Current pipeline order:
```
1. filter_and_validate      [ROBOT]
2. classify_step             [ROBOT]
3. detect_apis               [ROBOT]
4. extract_user_variables    [ROBOT]
5. convert_prompts           [AGENT — Sonnet]
6. assemble_blueprint        [ROBOT]
```

New pipeline order:
```
1. filter_and_validate      [ROBOT]
2. classify_step             [ROBOT]
3. detect_apis               [ROBOT]
4. research_api_pricing      [AGENT — Sonnet + WebSearch]  ← NEW
5. extract_user_variables    [ROBOT]
6. convert_prompts           [AGENT — Sonnet]
7. assemble_blueprint        [ROBOT]
```

Step 4 runs AFTER API detection so it knows which APIs to research. It runs BEFORE prompt conversion because knowing the alternatives might influence which APIs end up in the final blueprint.

### Data Model

**New Pydantic models (in `api_research.py`):**

```python
class APIAlternative(BaseModel):
    """A cheaper or comparable alternative to a detected API."""
    service_name: str          # e.g., "Apify"
    category: str              # e.g., "Web Scraping"
    pricing_summary: str       # e.g., "Pay-per-use, ~$5/1000 page loads"
    free_tier: str             # e.g., "Yes — $5 free monthly credit"
    monthly_cost: str          # e.g., "$49/mo for 100K results"
    tradeoff: str              # e.g., "Cheaper but requires more setup, fewer pre-built scrapers"
    signup_url: str            # e.g., "https://apify.com"


class APIResearchResult(BaseModel):
    """Research results for a single detected API."""
    service_key: str           # Matches DetectedAPI.service_key (e.g., "phantombuster")
    service_name: str          # e.g., "PhantomBuster"
    category: str              # e.g., "Web Scraping & Automation"

    # Pricing
    pricing_summary: str       # One-line: "Starts at $56/mo, no free API tier"
    pricing_tiers: list[str]   # ["Starter: $56/mo (5 phantoms)", "Pro: $128/mo (15 phantoms)", ...]
    free_tier: str             # "No — paid plan required for API access" or "Yes — 100 contacts/mo"
    api_access_cost: str       # "$56/mo minimum" — the cost just to GET API access
    per_unit_cost: str         # "$0.05 per phantom execution" or "N/A — flat rate"

    # Alternatives
    alternatives: list[APIAlternative]  # 2-3 alternatives

    # Red flags
    red_flags: list[str]       # ["No free tier", "Annual contract required for best pricing", etc.]

    # Metadata
    research_source: str       # "web_search" or "static_database"
    researched_at: str         # ISO timestamp


class BlueprintAPIResearch(BaseModel):
    """Complete API research for all detected APIs in a blueprint."""
    results: list[APIResearchResult]
    total_estimated_monthly_cost: str   # Sum of minimum API costs
    research_duration_seconds: float
```

**Blueprint model update:**

Add to `TFSheetBlueprint` (both Python and TypeScript):
```python
api_research: Optional[BlueprintAPIResearch] = None  # None if research was skipped/failed
```

### Frontend: API Analysis Section

On the `BlueprintPreview.tsx` page, add a new collapsible section between the chain visualization and the "Required APIs" links section.

**Layout per API:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 PhantomBuster                                    Web Scraping│
│                                                                  │
│ Pricing: Starts at $56/mo, no free API tier                     │
│ API Access: $56/mo minimum (Starter plan)                       │
│ Per-use: ~$0.05 per phantom execution                           │
│                                                                  │
│ ⚠️ Red Flags:                                                   │
│   • No free tier — paid plan required for API access            │
│   • Limited to 5 phantoms on Starter plan                       │
│                                                                  │
│ 💡 Cheaper Alternatives:                                        │
│ ┌───────────────┬──────────────┬───────────────────────────────┐│
│ │ Apify         │ ~$49/mo      │ More setup, but covers most   ││
│ │               │ (free tier!) │ scraping with 3-10 options     ││
│ ├───────────────┼──────────────┼───────────────────────────────┤│
│ │ ScrapingBee   │ Pay-per-req  │ Simpler API, $0.01/request    ││
│ │               │ (free tier!) │ Less pre-built, more flexible  ││
│ └───────────────┴──────────────┴───────────────────────────────┘│
│                                                                  │
│ [Get API key →]  [Use Apify instead →]  [Use ScrapingBee →]    │
└─────────────────────────────────────────────────────────────────┘
```

**Key UI elements:**
- Collapsible accordion per API (expanded by default if red flags exist)
- Red flag badges with warning icons
- Alternatives table with direct comparison
- "Use {alternative} instead" buttons (future: could swap the API in the blueprint)
- Total estimated monthly cost summary at the top of the section
- Research source badge ("Live research" vs "Cached data")

### Cost/Performance Notes

- **Sonnet + WebSearch per API**: ~15-30 seconds, uses Sonnet capacity (67 hrs/day)
- **6 APIs × 30s = ~3 minutes** added to blueprint generation
- **For 5-10 tools/day with ~5 APIs each**: 25-50 API research calls/day = ~25 minutes of Sonnet time. Well within the 67-hour daily budget.
- **Static DB fallback** ensures research never blocks blueprint generation — if web search fails, static data shows immediately with a "Last verified: {date}" badge

### File Changes

| File | Change |
|------|--------|
| `server/services/api_research.py` | **NEW** — Static DB, research function, Pydantic models |
| `server/services/sheet_blueprint.py` | Add `research_api_pricing()` call to pipeline, pass results to blueprint |
| `ui/src/lib/types.ts` | Add `APIResearchResult`, `APIAlternative`, `BlueprintAPIResearch` interfaces, add `api_research` to `TFSheetBlueprint` |
| `ui/src/components/tool-factory/BlueprintPreview.tsx` | Add API Analysis accordion section |
| `ui/src/components/tool-factory/GenerationProgress.tsx` | No changes needed — already handles dynamic progress messages |

### Implementation Phases

**Phase 1: Backend (api_research.py + pipeline integration)**
- Static pricing database with all 20+ APIs
- Web research function using Claude + WebSearch
- Fallback logic (web → static → empty)
- Wire into `generate_blueprint()` pipeline with progress messages
- Add `api_research` field to blueprint Pydantic model

**Phase 2: Frontend (types + BlueprintPreview)**
- TypeScript types for API research data
- API Analysis section on BlueprintPreview
- Collapsible cards per API with pricing, alternatives, red flags
- Total estimated monthly cost summary

**Phase 3: Polish**
- "Use alternative instead" button that swaps API references in the blueprint
- Cache research results per API for 24 hours (avoid re-researching the same API across multiple tools)
- Static DB auto-refresh reminder (flag entries older than 30 days)

### Notes

- **Apify** should always be suggested as an alternative for scraping tasks (PhantomBuster, ScrapingBee, Bright Data). User specifically called this out — "super cheap for decent size runs and covers most every type of scrape with 3-10 options."
- The `allowed_tools=["WebSearchTool"]` parameter in ClaudeSDKClient enables web search. The tool name might need to be `"WebSearch"` or `"web_search"` — check the Claude Agent SDK docs for the exact tool name.
- All research calls use `force_subscription=True` to avoid burning API credits.
- The 90-second timeout per API is generous but necessary — web search can be slow.
- If the user cancels blueprint generation, any in-progress research calls should be abandoned (the SSE cancel flow already handles this).
