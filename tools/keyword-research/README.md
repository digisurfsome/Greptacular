# Keyword Golden Nugget Finder

Find high-volume, low-competition keywords -- the "golden nuggets" that are easiest to rank for.

## Quick Start

```bash
cd tools/keyword-research
pip install -r requirements.txt
python server.py
```

Open http://localhost:8765 in your browser. The app ships with ~200 realistic demo keywords so it works immediately with no API keys.

## What It Does

- **Difficulty segmentation bar** -- one click to see all keywords at difficulty 0, 1-5, 6-10, etc.
- **Opportunity score** -- combines volume and difficulty into a single "how good is this" number
- **Sortable, filterable table** -- sort by any column, filter by volume/difficulty/opportunity ranges
- **CSV import** -- drop in an Ahrefs or Semrush export and it just works
- **DataForSEO integration** -- plug in API keys for real keyword data

## Data Sources

| Source | Setup | What You Get |
|--------|-------|-------------|
| **Demo** | Nothing, works out of the box | ~200 realistic keywords |
| **DataForSEO** | API login + password in Settings | Real volume + keyword difficulty |
| **Google Ads** | Not yet implemented | -- |
| **CSV Import** | Upload any Ahrefs/Semrush CSV | Whatever the CSV contains |

## The Golden Nugget Workflow

1. Start the app (demo data loads automatically)
2. Click the green "0" or "1-5" segment in the difficulty bar
3. Sort by Volume (descending) -- these are your golden nuggets
4. Keywords with high volume AND low difficulty = easy wins

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend |
| `POST` | `/api/search` | Search by seed keyword |
| `POST` | `/api/import-csv` | Upload a CSV file |
| `GET` | `/api/keywords` | Get keywords with filtering |
| `GET` | `/api/segments` | Get counts per difficulty segment |
| `GET` | `/api/settings` | Get current settings (keys masked) |
| `POST` | `/api/settings` | Save settings |

### Filtering Parameters (`GET /api/keywords`)

- `difficulty_min` / `difficulty_max` (0-100)
- `volume_min` / `volume_max`
- `sort_by` -- volume, difficulty, cpc, opportunity_score, keyword
- `sort_order` -- asc, desc

## Files

- `server.py` -- FastAPI backend with SQLite database
- `index.html` -- Single-file frontend (no build step)
- `requirements.txt` -- Python dependencies
- `keywords.db` -- Created automatically on first run (gitignored)
