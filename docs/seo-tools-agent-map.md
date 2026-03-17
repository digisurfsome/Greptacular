# SEO Tools — Agent Navigation Map

## READ THIS FIRST
This map tells you where everything is in the SEO keyword tool so you don't waste time searching.

## Architecture (Simple)
- **One backend file**: `server/routers/seo_tools.py` (~2600 lines, FastAPI router)
- **One frontend file**: `tools/keyword-research/index.html` (~4020 lines, single HTML/CSS/JS)
- **Database**: SQLite at `~/.autoforge/seo_keywords.db`
- **Mounting**: Router at `/api/seo-tools/` prefix. HTML served at `/api/seo-tools/app` with URL rewriting (`/api/` → `/api/seo-tools/`)

## Backend Map (seo_tools.py)

### Database Schema (lines 85-190)
| Table | Purpose |
|-------|---------|
| `keywords` | All keyword data (keyword, volume, difficulty, cpc, competition, seed_keyword, etc.) |
| `settings` | DataForSEO creds, location, language, OpenAI key |
| `nugget_hunts` | Nugget Hunter hunt history |
| `nuggets` | Individual nuggets found by hunts |
| `search_history` | Record of every search (seed, mode, count, timestamp) |

### Key Functions (in order of importance)
| Function | Line | What it does |
|----------|------|-------------|
| `search_keywords()` | ~1199 | Main search endpoint. Splits comma-separated seeds, searches each via DataForSEO, upserts results |
| `dataforseo_search()` | ~536 | Orchestrates Related + Suggestions + Bulk Difficulty enrichment |
| `_parse_labs_response()` | ~438 | Parses DataForSEO API response into keyword dicts |
| `_dataforseo_related_keywords()` | ~371 | Calls DataForSEO Labs Related Keywords endpoint |
| `_dataforseo_keyword_suggestions()` | ~403 | Calls DataForSEO Labs Keyword Suggestions endpoint |
| `_dataforseo_bulk_keyword_difficulty()` | ~492 | Batch difficulty lookup (up to 1000 keywords) |
| `_dataforseo_search_volume()` | ~NEW | Batch search volume lookup for exact mode |
| `_upsert_keywords()` | ~1090 | Insert/update keywords in DB |
| `_rows_to_dicts()` | ~975 | Convert SQLite rows to dicts, parse JSON fields |
| `compute_opportunity_scores()` | ~322 | Calculate opportunity scores relative to max volume |
| `_generate_demo_search_results()` | ~991 | Generate fake data for demo mode |
| `get_keywords()` | ~1370 | GET /keywords with filtering, sorting, seed filtering |
| `_check_rdap()` | ~find it | RDAP domain availability check |
| `serve_seo_app()` | ~1172 | Serves the HTML file with URL rewriting |

### API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/app` | Serve frontend HTML |
| GET | `/settings` | Get settings |
| POST | `/settings` | Save settings |
| GET | `/balance` | DataForSEO balance check |
| POST | `/search` | **Main search** — accepts `{seed_keyword, mode}` |
| GET | `/search-status` | Poll search progress |
| GET | `/search-history` | List past searches |
| DELETE | `/search-history/{id}` | Delete a search |
| GET | `/keywords` | Get all keywords (with filters, seed filter) |
| GET | `/segments` | KD segment counts |
| POST | `/clear` | Clear all keywords |
| POST | `/import-csv` | Upload CSV file |
| GET | `/export-csv` | Download keywords CSV |
| GET | `/domain-check` | Single keyword domain availability |
| POST | `/domain-check-bulk` | Bulk domain check for table |
| GET | `/serp-preview` | Top 10 Google results for a keyword |
| POST | `/content-strategy` | AI content strategy generation |
| POST | `/content-strategy/research-keywords` | Bulk keyword research for CS |
| POST | `/problem-aware` | Generate problem-aware keywords |
| POST | `/problem-aware/research` | Research PA keywords via DataForSEO |
| POST | `/nugget-hunt/start` | Start automated nugget hunt |
| GET | `/nugget-hunt/status` | Poll hunt progress |
| GET | `/nugget-hunt/results` | Get hunt results |
| GET | `/nugget-hunt/history` | List past hunts |
| POST | `/nugget-hunt/cancel` | Cancel active hunt |
| DELETE | `/nugget-hunt/delete` | Delete a hunt |
| GET | `/nugget-hunt/export-csv` | Export nuggets |
| WS | `/ws` | AI Keyword Analyst chat |

## Frontend Map (index.html)

### Structure
```
Lines 1-962:      CSS styles
Lines 964-1634:   HTML structure
Lines 1635-4020:  JavaScript
```

### HTML Sections
| Section | Lines | Element ID |
|---------|-------|-----------|
| Header + API status | 968-1001 | `apiStatus`, `costTracker` |
| Mode tabs (4 tabs) | 1005-1010 | `.mode-tab` buttons |
| Keyword Research panel | 1013-1168 | `keywordResearchPanel` |
| Search bar | 1024-1034 | `searchInput`, `searchMode`, `searchBtn` |
| Search History | 1044-1056 | `searchHistoryPanel` |
| Segment bar | 1058-1059 | `segmentBar` |
| Filters sidebar | 1064-1120 | `filtersPanel` |
| Keywords table | 1122-1165 | `kwBody`, `emptyState`, `pagination` |
| Nugget Hunter panel | 1171-1313 | `nuggetHunterPanel` |
| Content Strategy panel | 1316-1368 | `contentStrategyPanel` |
| Problem-Aware panel | 1371-1458 | `problemAwarePanel` |
| Cost Log panel | 1461-1494 | `costLogPanel` |
| Settings modal | 1499-1559 | `settingsModal` |
| Niche Explorer modal | 1562-1591 | `nicheModal` |
| SERP Preview modal | 1594-1610 | `serpModal` |
| Domain Check modal | 1613-1630 | `domainModal` |

### Key JavaScript Functions
| Function | Line | Purpose |
|----------|------|---------|
| `searchKeywords()` | ~2478 | Main search — sends to API, displays results |
| `loadKeywords()` | ~2475 | Load ALL keywords from DB |
| `applyFilters()` | ~2640 | Apply all sidebar filters + text chips |
| `renderTable()` | ~2928 | Render keyword table with pagination |
| `filterBySearches()` | ~2778 | Filter to keywords from selected search history |
| `addFilterChip()` | ~2704 | Add text filter chip |
| `sortTable()` | ~2846 | Column sorting |
| `checkDomainsForPage()` | ~1849 | Trigger domain availability checks |
| `autoCheckDomainsForPage()` | ~1865 | Auto-check domains for visible keywords |
| `serpPreview()` | ~1978 | Open SERP analysis modal |
| `checkDomain()` | ~1911 | Open domain check modal |
| `switchMode()` | ~3105 | Switch between 4 tabs |
| `openSettings()` | ~3044 | Open settings modal |
| `generateProblemAware()` | ~3778 | Generate problem-aware keywords |
| `generateContentStrategy()` | ~3546 | Generate content strategy |
| `startNuggetHunt()` | ~3130 | Start nugget hunt |
| `renderCostLog()` | ~1755 | Render cost log table |
| `loadSearchHistory()` | ~2742 | Load search history panel |
| `openNicheExplorer()` | ~2154 | Open niche explorer modal |

### State Variables
| Variable | Purpose |
|----------|---------|
| `allKeywords` | All keywords currently loaded |
| `filteredKeywords` | After sidebar filters applied |
| `displayedKeywords` | After text filter chips applied |
| `filterChips` | Active text filter terms |
| `currentSort` | Current sort column + direction |
| `currentPage` | Current pagination page |
| `domainCache` | Cached domain availability results |
| `activeTlds` | Which TLD chips are active |
| `costLog` | Search cost history (localStorage) |
| `paKeywords` | Problem-aware keyword results |
| `nuggetResults` | Nugget hunt results |
| `csStrategy` | Content strategy results |

## Common Pitfalls
1. **API URLs**: Frontend uses `/api/...` but backend routes are `/api/seo-tools/...`. The `serve_seo_app()` function rewrites URLs when serving the HTML. Don't add `/seo-tools/` to frontend code.
2. **Competition field**: Stored as 0-1.0 float in DB. Frontend multiplies by 100 for display.
3. **seed_keyword**: Stored lowercase in DB. Always lowercase when querying.
4. **Mode strings**: Backend uses `"related"`, `"suggestions"`, `"both"`, `"exact"`. NOT `"merged"` or `"keyword_suggestions"`.
5. **JSON fields**: `monthly_searches` and `serp_features` are stored as JSON strings in SQLite, parsed by `_rows_to_dicts()`.
