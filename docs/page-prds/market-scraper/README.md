# Market Scraper — PRD & File Map

## What It Does
Reddit scraper that finds pain points, desires, validation signals, and exact user phrasings for ad copy, social media posts, and app idea validation. Free, no API keys, runs locally.

## Access
`/#/market-scraper` in the AutoForge UI

---

## All Files

### Backend
| File | Purpose |
|------|---------|
| `server/services/market_scraper_service.py` | Core logic — Reddit scraping, categorization, phrase frequency, project builder, community/user discovery |
| `server/routers/market_scraper.py` | API endpoints — all REST routes for scraping, search, projects, angles, community, user |
| `server/routers/__init__.py` | Router registration (1 line: `market_scraper_router`) |
| `server/main.py` | App registration (1 line: `app.include_router(market_scraper_router)`) |

### Frontend
| File | Purpose |
|------|---------|
| `ui/src/pages/MarketScraperPage.tsx` | Full page UI — scraper view, projects view, wizard, phrase cards, top phrases |
| `ui/src/hooks/useMarketScraper.ts` | All TanStack Query hooks for the page |
| `ui/src/lib/api.ts` | API fetch functions (appended to shared file) |
| `ui/src/lib/types.ts` | TypeScript interfaces (appended to shared file) |
| `ui/src/main.tsx` | Route registration (1 line: `/#/market-scraper`) |

### Database
- `~/.autoforge/market_scraper.db` (SQLite, created at runtime)
- Tables: `scrapes`, `phrases`, `research_projects`, `project_angles`

---

## Features

### 1. URL Scraper
- Paste any Reddit thread URL
- Scrapes all comments recursively
- Categorizes into: pain_point, desire, feature_request, validation, social_proof
- Generates ad hooks and social post ideas per phrase
- Validation signal scoring (1-5)

### 2. Topic Search
- Type a topic (e.g., "SEO agency automation")
- Pick subreddits or search all of Reddit
- Auto-scrapes top N threads
- All Apify-level parameters:
  - Search type: posts, comments, communities, users
  - Sort: relevance, hot, top, new, comments
  - Time filter: hour, day, week, month, year, all
  - NSFW toggle
  - Min comments threshold
  - Max comments per post
  - Skip comments option
  - After date filter

### 3. Top Phrases (Frequency Analysis)
- Extracts 2-4 word n-grams from all scraped comments
- Ranks by frequency (most repeated = market language)
- Deduplicates sub-phrases
- Shows category breakdown per phrase
- Expandable sample quotes
- One-click copy for ad copy

### 4. Research Project Builder
- Create reusable research projects (name + niche)
- 6 angle types (scrape nodes):
  - **Discovery** — tools/automations people ARE using
  - **Desire** — tools people WANT
  - **Pain Point** — frustrations and complaints
  - **Validation** — purchase intent signals
  - **Workflow** — step-by-step processes shared
  - **Education** — learning resources discussed
- Each angle auto-generates search queries from niche + seed phrases
- Run individually or all at once
- Custom keywords per angle

### 5. Community & User Discovery
- `GET /discover-subreddits?query=` — find relevant subreddits for any niche
- `GET /community/{subreddit}` — member count, description, active users, category
- `GET /user/{username}` — karma, recent posts, activity for power user identification

---

## API Endpoints

| Method | Path | What It Does |
|--------|------|-------------|
| POST | `/api/market-scraper/scrape` | Scrape a single Reddit thread by URL |
| POST | `/api/market-scraper/search` | Search Reddit by topic (no scraping) |
| POST | `/api/market-scraper/search-and-scrape` | Search + auto-scrape top threads |
| GET | `/api/market-scraper/scrapes` | List all past scrapes |
| GET | `/api/market-scraper/scrapes/{id}` | Get scrape with all phrases |
| DELETE | `/api/market-scraper/scrapes/{id}` | Delete a scrape |
| GET | `/api/market-scraper/export/{id}` | Export phrases as CSV |
| GET | `/api/market-scraper/phrases` | Query phrases with filters |
| GET | `/api/market-scraper/phrase-frequency` | Top phrases ranked by frequency |
| GET | `/api/market-scraper/search-options` | Available sort/time/type options |
| GET | `/api/market-scraper/discover-subreddits` | Find subreddits for a niche |
| GET | `/api/market-scraper/community/{sub}` | Subreddit metadata |
| GET | `/api/market-scraper/user/{username}` | User profile + recent activity |
| GET | `/api/market-scraper/angle-types` | Available research angle types |
| POST | `/api/market-scraper/projects` | Create research project |
| GET | `/api/market-scraper/projects` | List all projects |
| GET | `/api/market-scraper/projects/{id}` | Get project with angles |
| PATCH | `/api/market-scraper/projects/{id}` | Update project |
| DELETE | `/api/market-scraper/projects/{id}` | Delete project |
| POST | `/api/market-scraper/projects/{id}/angles` | Add angle to project |
| DELETE | `/api/market-scraper/angles/{id}` | Remove angle |
| POST | `/api/market-scraper/angles/{id}/run` | Run a single angle |
| POST | `/api/market-scraper/projects/{id}/run-all` | Run all angles |

---

## Categorization Engine

### Categories (regex pattern matching)
- **validation** — "I'd pay", "take my money", "game changer", "instant buy"
- **social_proof** — "I switched to", "best tool", "changed my life", "can't go back"
- **pain_point** — "I hate", "I wish", "why can't", "drives me crazy", "waste of time"
- **desire** — "I want", "I need", "would love", "looking for", "desperately need"
- **feature_request** — "should have", "needs to", "please add", "missing feature"

### Subcategories
pricing, ux, speed, features, support, reliability, integration, security

### Scoring
Validation signal (1-5) based on: Reddit upvotes + category weight + emotional intensity words

---

## Rate Limits (Reddit JSON API)
- No API key: ~10 requests/minute
- Free Reddit API key: 60 requests/minute
- No daily cap
- Each thread = 1 request, each search = 1 request per subreddit

## Competitive Comparison
- Apify charges $4/1000 results — we're free
- PainOnSocial charges monthly — we're free
- We have AI categorization + phrase frequency that they don't
- We have research project builder that most don't
