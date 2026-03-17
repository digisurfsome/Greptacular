# PRD: SEO Smart Search Optimizer + AI Visibility Tracker

## Overview
Two-part system: (1) Intelligent keyword search that minimizes API costs through smart ordering, caching, and deduplication. (2) AI Visibility Tracker that monitors brand mentions across ChatGPT, Perplexity, Claude, and Google AI Overviews.

**Priority:** Cost optimizer first (immediate ROI), AI Visibility second (market opportunity).

---

## PART 1: Smart Search Cost Optimizer

### Problem
- User enters 23 comma-separated keywords → system fires 47 API calls → costs $0.54
- Same keywords searched individually as Related = $0.12 for 500 keywords
- No deduplication: system re-searches keywords that already exist in DB
- No intelligence: system doesn't know which seeds will overlap

### Solution: 3-Layer Smart Search Pipeline

#### Layer 1: DB Deduplication (Deterministic — Zero Cost)
Before ANY API call:
1. Check each seed keyword against the existing `keywords` table
2. If seed already exists as a `seed_keyword` with results → skip it entirely
3. If seed exists as a keyword (found via another search) → skip it
4. Show user: "Skipping 8/23 seeds (already in database). Searching 15 new seeds."

**Implementation:**
```python
# In search_keywords() before the API loop
conn = get_db()
existing_seeds = set(row[0] for row in conn.execute(
    "SELECT DISTINCT seed_keyword FROM keywords"
).fetchall())
existing_keywords = set(row[0] for row in conn.execute(
    "SELECT DISTINCT keyword FROM keywords"
).fetchall())

seeds_to_search = []
seeds_skipped = []
for seed in raw_seeds:
    if seed in existing_seeds or seed in existing_keywords:
        seeds_skipped.append(seed)
    else:
        seeds_to_search.append(seed)
```

#### Layer 2: AI-Powered Seed Ordering (AI — Cheap, One Call)
For the remaining seeds that DO need searching:
1. Send list to a cheap AI model (Haiku or GPT-4o-mini, ~$0.001)
2. Prompt: "Order these keywords from broadest (most likely to return related results covering the others) to most specific. Return as JSON array."
3. Run searches in that order
4. After EACH search, cross-check returned keywords against remaining seeds
5. If a remaining seed appears in the results → remove it from the queue

**Example flow:**
- Seeds to search: [openclaw sandbox, openclaw ai, openclaw security, ai agent safety]
- AI orders: [ai agent safety, openclaw ai, openclaw sandbox, openclaw security]
- Search "ai agent safety" → returns 300 keywords including "openclaw security" and "openclaw sandbox"
- Cross-check: 2 remaining seeds found in results → remove them
- Search "openclaw ai" → returns 150 keywords
- Done. Only 2 API calls instead of 4.

#### Layer 3: Cost Estimation + Confirmation (Deterministic)
Before executing:
1. Calculate: `seeds_to_search × $0.06 per mode + $0.005 bulk difficulty`
2. Show modal: "This will make ~X API calls. Estimated cost: $X.XX. Proceed?"
3. User confirms or cancels
4. After search, show actual cost in the cost log

### Mode Selection Intelligence
Add a recommendation system:
- "Related" mode: Best for brand-related searches, finding semantic connections
- "Suggestions" mode: Best for long-tail discovery, what people actually type
- "Both" mode: Gets the most keywords but costs 2x per seed
- "Exact" mode: Cheapest — just get volume/difficulty for specific keywords you already know

Show a suggestion: "For brand monitoring (openclaw), we recommend Related mode. For keyword discovery, use Suggestions."

### Competition/Ads Data Toggle
Add to Settings:
- Toggle: "Include Google Ads competition data" (default: OFF for SEO mode)
- When OFF: Skip competition-related API calls, show "SEO Mode" badge
- When ON: Include CPC/competition data, show "Ads Mode" badge
- Saves money when user only cares about organic SEO

### Phase Breakdown — Part 1

**Phase 1: DB Deduplication (Difficulty: 2/10)**
- Add dedup check before API loop in `search_keywords()`
- Return `seeds_skipped` count in response
- Frontend shows "Skipped X seeds (already cached)"
- Files: `seo_tools.py` (search_keywords function), `index.html` (progress display)

**Phase 2: Cost Estimation Modal (Difficulty: 2/10)**
- Calculate estimated cost before search
- Show confirmation modal with cost breakdown
- Add "Always skip confirmation for searches under $0.10" setting
- Files: `index.html` (new modal + JS logic)

**Phase 3: Sequential Search with Cross-Check (Difficulty: 3/10)**
- After each seed search, cross-check remaining seeds against returned keywords
- Remove matched seeds from queue
- Update progress: "Searched 2/15 seeds (8 auto-resolved from results)"
- Files: `seo_tools.py` (search loop logic), `index.html` (progress updates)

**Phase 4: AI Seed Ordering (Difficulty: 4/10)**
- Before search, call cheap AI to order seeds by broadness
- Use Haiku or GPT-4o-mini (< $0.001 per call)
- Falls back to alphabetical if AI call fails
- Files: `seo_tools.py` (new function `_ai_order_seeds()`)

**Phase 5: Competition Toggle (Difficulty: 2/10)**
- Add toggle to settings modal
- When off, hide Comp column, skip competition data in API calls
- Files: `seo_tools.py` (settings), `index.html` (toggle + column visibility)

---

## PART 2: AI Visibility Tracker

### What It Does
Monitor how your brand appears in AI-generated responses across ChatGPT, Perplexity, Claude, and Google AI Overviews.

### Core Features

#### 1. Prompt Library
- User creates prompts: "What are the best AI coding tools?", "How do I protect files from AI agents?"
- Organize by category: brand, competitor, industry, problem-aware
- Schedule: run daily, weekly, or monthly

#### 2. Multi-LLM Query Engine
For each prompt, query:
- **ChatGPT** (via OpenAI API) — user already has key configured
- **Perplexity** (via API — $5/month for 1000 queries)
- **Claude** (via subscription — already available)
- **Google AI Overview** (scraping or via Search API)

#### 3. Response Parser
Parse each response for:
- **Brand mentions**: Does "OpenClaw" or your URL appear?
- **Position**: In a listicle, what position are you? (1st, 5th, not mentioned)
- **Citation**: Does it link to your URL?
- **Sentiment**: Positive, neutral, negative mention?
- **Competitors**: Which competitors appear in the same response?

#### 4. Tracking Dashboard
- **Visibility Score**: % of prompts where your brand appears (0-100)
- **Average Position**: When mentioned, where do you rank in lists?
- **Citation Rate**: % of mentions that include your URL
- **Trend Charts**: All metrics over time (daily/weekly)
- **Competitor Comparison**: Side-by-side visibility scores

#### 5. Content Feedback Loop
- When you publish new content, mark it in the system
- System runs related prompts before and after publication
- Shows: "After publishing 'AI Agent Security Guide', your visibility for 'ai agent safety' went from position 8 to position 3 in 5 days"
- This is the pattern-finding engine the owner described

#### 6. Topical Authority Detection
- Track clusters of related prompts
- When visibility crosses a threshold across a topic cluster → flag "Topical Authority Achieved"
- Track the "wall falling down" moment where you suddenly rank for everything in a topic

### Phase Breakdown — Part 2

**Phase 1: Prompt Library + Storage (Difficulty: 2/10)**
- New SQLite table: `ai_prompts` (id, prompt, category, schedule, created_at)
- CRUD API endpoints
- UI: New "AI Visibility" tab with prompt management
- Files: `seo_tools.py` (new table + endpoints), `index.html` (new tab)

**Phase 2: Single-LLM Query (ChatGPT) (Difficulty: 3/10)**
- Run prompts against ChatGPT API (already have OpenAI key in settings)
- Parse response for brand mentions, listicle positions, URLs
- Store results: `ai_results` table (prompt_id, llm, response, mentions, position, citations, timestamp)
- Files: `seo_tools.py` (new query + parse functions)

**Phase 3: Results Dashboard (Difficulty: 4/10)**
- Visibility score calculation
- Position tracking over time
- Simple chart (use inline SVG or a lightweight chart library)
- Files: `index.html` (new dashboard UI)

**Phase 4: Multi-LLM Support (Difficulty: 3/10)**
- Add Perplexity API (they have a straightforward API)
- Add Claude API (already configured in AutoForge)
- Side-by-side comparison across LLMs
- Files: `seo_tools.py` (additional API clients)

**Phase 5: Content Feedback Loop (Difficulty: 4/10)**
- "I published content" marker with URL + date
- Auto-run related prompts on schedule
- Before/after comparison dashboard
- Pattern detection: "Publishing 3+ articles in a topic cluster increases visibility by X%"
- Files: `seo_tools.py` (content tracking), `index.html` (feedback UI)

**Phase 6: Competitive Benchmarking (Difficulty: 3/10)**
- Add competitor brands to monitor
- Run same prompts, compare who gets mentioned
- Share of voice chart: "You: 35%, Competitor A: 45%, Competitor B: 20%"
- Files: `seo_tools.py` (competitor tracking), `index.html` (comparison UI)

---

## Agent Assignment

### Agent 1: Smart Search Optimizer (Part 1, Phases 1-5)
- Estimated context: ~30-35%
- All changes in `seo_tools.py` + `index.html`
- Pure deterministic + one cheap AI call
- Should be done in one session

### Agent 2: AI Visibility Tracker (Part 2, Phases 1-3)
- Estimated context: ~35-40%
- New tables, endpoints, UI tab
- Core functionality only (ChatGPT first)

### Agent 3: AI Visibility Advanced (Part 2, Phases 4-6)
- Estimated context: ~30%
- Multi-LLM, content loop, competitive benchmarking
- Depends on Agent 2 completing first

---

## Key Files
- `server/routers/seo_tools.py` — Backend (all API endpoints, DB, business logic)
- `tools/keyword-research/index.html` — Frontend (single-file HTML/CSS/JS app)
- `server/main.py` — Router mounting (already done)

## Dependencies
- DataForSEO API (already integrated)
- OpenAI API key (already in settings for Content Strategy)
- Perplexity API key (Phase 4 — $5/month)
- Claude API (already available via subscription)

## Success Metrics
- API cost per search reduced by 80%+
- User can track AI visibility across 3+ LLMs
- Content feedback loop shows measurable ranking changes
