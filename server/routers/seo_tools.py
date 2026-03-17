"""
SEO Tools Router
================

FastAPI router that provides keyword research and SEO analysis endpoints.
Ported from the standalone server at tools/keyword-research/server.py and
adapted to run as a router within the AutoForge server.

Features:
- DataForSEO Labs API integration (related keywords, suggestions, difficulty)
- Demo mode with sample data
- CSV import/export (Ahrefs, Semrush, generic)
- Nugget Hunter: automated low-KD/high-volume keyword discovery
- AI-powered keyword analysis via WebSocket (subscription auth)
"""

import asyncio
import csv
import io
import json
import logging
import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo-tools", tags=["seo-tools"])

# ---------------------------------------------------------------------------
# Database path — stored in the shared AutoForge config directory
# ---------------------------------------------------------------------------

DB_PATH = Path.home() / ".autoforge" / "seo_keywords.db"

# Path to the standalone HTML UI from the keyword-research tool
INDEX_PATH = Path(__file__).resolve().parent.parent.parent / "tools" / "keyword-research" / "index.html"

DATAFORSEO_BASE = "https://api.dataforseo.com/v3"

# Location codes for common countries
LOCATION_CODES = {
    "US": 2840,
    "UK": 2826,
    "CA": 2124,
    "AU": 2036,
    "DE": 2276,
    "FR": 2250,
    "ES": 2724,
    "IT": 2380,
    "BR": 2076,
    "IN": 2356,
    "JP": 2392,
    "MX": 2484,
    "NL": 2528,
}

# Supported language codes
LANGUAGE_CODES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "nl": "Dutch",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a connection with WAL mode and row factory enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS keywords (
                keyword          TEXT NOT NULL,
                volume           INTEGER DEFAULT 0,
                difficulty       INTEGER DEFAULT 0,
                cpc              REAL DEFAULT 0.0,
                competition      REAL DEFAULT 0.0,
                competition_level TEXT DEFAULT '',
                monthly_searches TEXT DEFAULT '[]',
                serp_features    TEXT DEFAULT '[]',
                search_intent    TEXT DEFAULT '',
                trend            TEXT DEFAULT 'stable',
                source           TEXT DEFAULT 'demo',
                seed_keyword     TEXT DEFAULT '',
                last_updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(keyword)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_keywords_difficulty
                ON keywords(difficulty);
            CREATE INDEX IF NOT EXISTS idx_keywords_volume
                ON keywords(volume);
            CREATE INDEX IF NOT EXISTS idx_keywords_seed
                ON keywords(seed_keyword);

            CREATE TABLE IF NOT EXISTS nugget_hunts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'pending',
                niches TEXT NOT NULL,
                suffixes TEXT NOT NULL DEFAULT '[]',
                settings TEXT DEFAULT '{}',
                total_combos INTEGER DEFAULT 0,
                completed_combos INTEGER DEFAULT 0,
                current_combo TEXT DEFAULT '',
                nuggets_found INTEGER DEFAULT 0,
                total_keywords_scanned INTEGER DEFAULT 0,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS nuggets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hunt_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                volume INTEGER DEFAULT 0,
                difficulty INTEGER DEFAULT 0,
                cpc REAL DEFAULT 0.0,
                competition REAL DEFAULT 0.0,
                competition_level TEXT DEFAULT '',
                monthly_searches TEXT DEFAULT '[]',
                serp_features TEXT DEFAULT '[]',
                trend TEXT DEFAULT 'stable',
                opportunity_score INTEGER DEFAULT 0,
                seed_combo TEXT DEFAULT '',
                niche TEXT DEFAULT '',
                suffix TEXT DEFAULT '',
                tier TEXT DEFAULT 'bronze',
                research_notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hunt_id, keyword)
            );

            CREATE INDEX IF NOT EXISTS idx_nuggets_hunt_id
                ON nuggets(hunt_id);
            CREATE INDEX IF NOT EXISTS idx_nuggets_tier
                ON nuggets(tier);

            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seed_keyword TEXT NOT NULL,
                mode TEXT,
                keywords_found INTEGER DEFAULT 0,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migrate existing tables: add new columns if missing
        existing_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(keywords)").fetchall()
        }
        migrations = {
            "competition_level": "TEXT DEFAULT ''",
            "monthly_searches": "TEXT DEFAULT '[]'",
            "serp_features": "TEXT DEFAULT '[]'",
            "search_intent": "TEXT DEFAULT ''",
            "trend": "TEXT DEFAULT 'stable'",
        }
        for col_name, col_def in migrations.items():
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE keywords ADD COLUMN {col_name} {col_def}")

        conn.commit()
    finally:
        conn.close()


# Initialise the database when the module is imported (router is loaded at
# server startup).  This is equivalent to the standalone server's lifespan
# handler calling init_db() + seed_demo_data().
init_db()


# ---------------------------------------------------------------------------
# In-memory search status (for progress reporting)
# ---------------------------------------------------------------------------

_search_status: dict[str, dict[str, Any]] = {}


def _schedule_status_cleanup(key: str, delay: float = 60.0) -> None:
    """Remove a _search_status entry after *delay* seconds to prevent memory leaks."""
    try:
        loop = asyncio.get_event_loop()
        loop.call_later(delay, _search_status.pop, key, None)
    except RuntimeError:
        # No running loop — skip cleanup (edge case during shutdown)
        pass


# ---------------------------------------------------------------------------
# Demo data generator
# ---------------------------------------------------------------------------

_DEMO_KEYWORDS: list[dict[str, Any]] = [
    {"keyword": "mortgage calculator", "volume": 49500, "difficulty": 78, "cpc": 3.40,
     "competition_level": "HIGH", "trend": "stable"},
    {"keyword": "bmi calculator", "volume": 40500, "difficulty": 62, "cpc": 1.20,
     "competition_level": "MEDIUM", "trend": "stable"},
    {"keyword": "calorie calculator", "volume": 33100, "difficulty": 55, "cpc": 0.90,
     "competition_level": "MEDIUM", "trend": "rising"},
    {"keyword": "tip calculator", "volume": 27100, "difficulty": 35, "cpc": 0.60,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "gpa calculator", "volume": 22200, "difficulty": 42, "cpc": 0.80,
     "competition_level": "MEDIUM", "trend": "stable"},
    {"keyword": "concrete calculator", "volume": 14800, "difficulty": 18, "cpc": 0.90,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "tile calculator", "volume": 8100, "difficulty": 12, "cpc": 0.70,
     "competition_level": "LOW", "trend": "rising"},
    {"keyword": "mulch calculator", "volume": 6600, "difficulty": 8, "cpc": 0.50,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "drywall calculator", "volume": 4400, "difficulty": 5, "cpc": 0.45,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "cubic yards calculator", "volume": 4400, "difficulty": 2, "cpc": 0.35,
     "competition_level": "LOW", "trend": "rising"},
    {"keyword": "board foot calculator", "volume": 3600, "difficulty": 1, "cpc": 0.40,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "stair calculator", "volume": 2900, "difficulty": 3, "cpc": 0.50,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "asphalt calculator", "volume": 2400, "difficulty": 0, "cpc": 0.45,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "paver calculator", "volume": 3600, "difficulty": 4, "cpc": 0.65,
     "competition_level": "LOW", "trend": "rising"},
    {"keyword": "ohms law calculator", "volume": 3600, "difficulty": 4, "cpc": 0.30,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "ai image generator free", "volume": 33100, "difficulty": 52, "cpc": 0.90,
     "competition_level": "HIGH", "trend": "rising"},
    {"keyword": "qr code generator free", "volume": 33100, "difficulty": 42, "cpc": 0.50,
     "competition_level": "MEDIUM", "trend": "stable"},
    {"keyword": "password generator", "volume": 18100, "difficulty": 35, "cpc": 0.30,
     "competition_level": "MEDIUM", "trend": "stable"},
    {"keyword": "website builder", "volume": 49500, "difficulty": 90, "cpc": 8.50,
     "competition_level": "HIGH", "trend": "declining"},
    {"keyword": "web hosting", "volume": 40500, "difficulty": 92, "cpc": 15.00,
     "competition_level": "HIGH", "trend": "declining"},
    {"keyword": "json formatter", "volume": 9900, "difficulty": 15, "cpc": 0.20,
     "competition_level": "LOW", "trend": "rising"},
    {"keyword": "regex tester", "volume": 6600, "difficulty": 18, "cpc": 0.25,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "wire gauge calculator", "volume": 1600, "difficulty": 0, "cpc": 0.35,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "voltage drop calculator", "volume": 2400, "difficulty": 2, "cpc": 0.40,
     "competition_level": "LOW", "trend": "stable"},
    {"keyword": "flow rate calculator", "volume": 2900, "difficulty": 5, "cpc": 0.40,
     "competition_level": "LOW", "trend": "stable"},
]


def seed_demo_data() -> None:
    """Insert demo keywords into the database if it is empty."""
    conn = get_db()
    try:
        count = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
        if count > 0:
            return

        now = datetime.now(timezone.utc).isoformat()
        conn.executemany(
            """INSERT OR IGNORE INTO keywords
               (keyword, volume, difficulty, cpc, competition, competition_level,
                monthly_searches, serp_features, trend, source, seed_keyword, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'demo', 'demo', ?)""",
            [
                (
                    kw["keyword"], kw["volume"], kw["difficulty"], kw["cpc"],
                    round(random.uniform(0.01, 0.95), 2),
                    kw.get("competition_level", "LOW"),
                    "[]", "[]",
                    kw.get("trend", "stable"),
                    now,
                )
                for kw in _DEMO_KEYWORDS
            ],
        )
        conn.commit()
        logger.info("Seeded %d demo keywords", len(_DEMO_KEYWORDS))
    finally:
        conn.close()


# Seed demo data on module load (after init_db)
seed_demo_data()


# ---------------------------------------------------------------------------
# Opportunity score
# ---------------------------------------------------------------------------

def compute_opportunity_scores(rows: list[dict]) -> list[dict]:
    """Add opportunity_score to each row based on the set's max volume."""
    if not rows:
        return rows
    max_vol = max(r["volume"] for r in rows) or 1
    for r in rows:
        r["opportunity_score"] = round(
            (r["volume"] / max_vol) * (1 - r["difficulty"] / 100) * 100
        )
    return rows


# ---------------------------------------------------------------------------
# Trend computation from monthly search data
# ---------------------------------------------------------------------------

def compute_trend(monthly_searches: list[dict]) -> str:
    """
    Compute trend direction from monthly_searches array.
    Compares the average of the last 3 months to the first 3 months.
    Returns 'rising', 'declining', or 'stable'.
    """
    if not monthly_searches or len(monthly_searches) < 6:
        return "stable"

    volumes = [m.get("search_volume", 0) or 0 for m in monthly_searches]

    if len(volumes) < 6:
        return "stable"

    # Recent = first 3 entries (newest), older = last 3 entries (oldest)
    recent_avg = sum(volumes[:3]) / 3
    older_avg = sum(volumes[-3:]) / 3

    if older_avg == 0:
        return "rising" if recent_avg > 0 else "stable"

    change_pct = (recent_avg - older_avg) / older_avg
    if change_pct > 0.15:
        return "rising"
    elif change_pct < -0.15:
        return "declining"
    return "stable"


# ---------------------------------------------------------------------------
# DataForSEO Labs API client
# ---------------------------------------------------------------------------

async def _dataforseo_related_keywords(
    seed: str, login: str, password: str,
    location_code: int, language_code: str,
) -> list[dict]:
    """
    Fetch related keywords using DataForSEO Labs Related Keywords endpoint.
    Returns keywords with volume, CPC, competition from keyword_info.
    """
    auth = (login, password)
    payload = [{
        "keyword": seed,
        "location_code": location_code,
        "language_code": language_code,
        "depth": 2,
        "limit": 500,
        "include_serp_info": True,
        "include_seed_keyword": True,
        "include_clickstream_data": False,
    }]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/related_keywords/live",
            json=payload,
            auth=auth,
        )
        resp.raise_for_status()
        data = resp.json()

    return _parse_labs_response(data)


async def _dataforseo_keyword_suggestions(
    seed: str, login: str, password: str,
    location_code: int, language_code: str,
) -> list[dict]:
    """
    Fetch keyword suggestions using DataForSEO Labs Keyword Suggestions endpoint.
    Uses autocomplete data for broader discovery.
    """
    auth = (login, password)
    payload = [{
        "keyword": seed,
        "location_code": location_code,
        "language_code": language_code,
        "limit": 500,
        "include_serp_info": True,
        "include_seed_keyword": True,
    }]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_suggestions/live",
            json=payload,
            auth=auth,
        )
        resp.raise_for_status()
        data = resp.json()

    logger.info("Keyword suggestions for '%s': tasks=%d, status=%s",
                seed, len(data.get("tasks", [])),
                [t.get("status_code") for t in data.get("tasks", [])])
    result = _parse_labs_response(data)
    logger.info("Keyword suggestions parsed: %d keywords", len(result))
    return result


def _parse_labs_response(data: dict) -> list[dict]:
    """Parse the response from related_keywords or keyword_suggestions endpoints."""
    results: list[dict] = []

    for task in data.get("tasks", []):
        if task.get("status_code") != 20000:
            error_msg = task.get("status_message", "Unknown error")
            logger.warning("DataForSEO task error: %s (code: %s)", error_msg, task.get("status_code"))
            continue

        task_results = task.get("result", []) or []
        logger.debug("DataForSEO task has %d result groups, total items: %s",
                      len(task_results),
                      sum(len((r or {}).get("items", []) or []) for r in task_results if r))

        for result in task_results:
            if result is None:
                continue
            for item in result.get("items", []) or []:
                if item is None:
                    continue
                kw_data = item.get("keyword_data") or item
                kw_info = kw_data.get("keyword_info") or {}
                # serp_info can be a sibling of keyword_data (related_keywords)
                # or nested inside kw_data (keyword_suggestions)
                serp_info = kw_data.get("serp_info") or item.get("serp_info") or {}

                kw_text = kw_data.get("keyword") or item.get("keyword", "")
                if not kw_text:
                    continue

                volume = kw_info.get("search_volume") or 0
                cpc_val = kw_info.get("cpc") or 0.0
                competition = kw_info.get("competition") or 0.0
                comp_level = kw_info.get("competition_level") or ""
                monthly = kw_info.get("monthly_searches") or []
                serp_types = serp_info.get("serp_item_types") or []

                trend = compute_trend(monthly)

                results.append({
                    "keyword": kw_text,
                    "volume": volume,
                    "cpc": round(cpc_val, 2),
                    "competition": round(competition, 4),
                    "competition_level": comp_level,
                    "monthly_searches": monthly,
                    "serp_features": serp_types,
                    "trend": trend,
                })

    return results


async def _dataforseo_bulk_keyword_difficulty(
    keywords: list[str], login: str, password: str,
    location_code: int, language_code: str,
) -> dict[str, int]:
    """
    Get keyword difficulty scores for a batch of keywords.
    Max 1000 keywords per call.
    Returns dict mapping keyword -> difficulty (0-100).
    """
    if not keywords:
        return {}

    auth = (login, password)
    diff_map: dict[str, int] = {}

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(keywords), 1000):
            batch = keywords[i:i + 1000]
            payload = [{
                "keywords": batch,
                "location_code": location_code,
                "language_code": language_code,
            }]
            resp = await client.post(
                f"{DATAFORSEO_BASE}/dataforseo_labs/google/bulk_keyword_difficulty/live",
                json=payload,
                auth=auth,
            )
            resp.raise_for_status()
            data = resp.json()

            for task in data.get("tasks", []):
                if task.get("status_code") != 20000:
                    continue
                for result in task.get("result", []) or []:
                    for item in result.get("items", []) or []:
                        kw_name = item.get("keyword", "")
                        kd = item.get("keyword_difficulty")
                        if kw_name and kd is not None:
                            diff_map[kw_name.lower()] = int(kd)

    return diff_map


async def _dataforseo_search_volume(
    keywords: list[str], login: str, password: str,
    location_code: int, language_code: str,
) -> list[dict]:
    """
    Get search volume, CPC, and competition for exact keywords using
    the Google Ads Search Volume endpoint. Returns a list of keyword dicts
    ready for storage.
    """
    if not keywords:
        return []

    auth = (login, password)
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        # API accepts up to 700 keywords per call
        for i in range(0, len(keywords), 700):
            batch = keywords[i:i + 700]
            payload = [{
                "keywords": batch,
                "location_code": location_code,
                "language_code": language_code,
            }]
            resp = await client.post(
                f"{DATAFORSEO_BASE}/keywords_data/google_ads/search_volume/live",
                json=payload,
                auth=auth,
            )
            resp.raise_for_status()
            data = resp.json()

            for task in data.get("tasks", []):
                if task.get("status_code") != 20000:
                    logger.warning("Search volume task error: %s", task.get("status_message"))
                    continue
                for result_item in task.get("result", []) or []:
                    if result_item is None:
                        continue
                    kw_text = result_item.get("keyword", "")
                    if not kw_text:
                        continue
                    volume = result_item.get("search_volume") or 0
                    cpc_val = result_item.get("cpc") or 0.0
                    competition = result_item.get("competition") or 0.0
                    comp_level = result_item.get("competition_level") or ""
                    monthly = result_item.get("monthly_searches") or []
                    trend = compute_trend(monthly)

                    results.append({
                        "keyword": kw_text,
                        "volume": volume,
                        "cpc": round(cpc_val, 2),
                        "competition": round(competition, 4),
                        "competition_level": comp_level,
                        "monthly_searches": monthly,
                        "serp_features": [],
                        "trend": trend,
                    })

    return results


async def dataforseo_search(
    seed: str, login: str, password: str,
    mode: str, location_code: int, language_code: str,
) -> list[dict]:
    """
    Main search function. Orchestrates the two-step enrichment flow:
    1. Fetch keywords via related_keywords and/or keyword_suggestions
    2. Enrich with bulk keyword difficulty scores
    """
    status_key = seed.lower()
    _search_status[status_key] = {"step": "fetching", "message": "Fetching keywords...", "done": False}

    all_keywords: list[dict] = []

    try:
        # Step 1: Fetch keywords based on mode
        if mode in ("related", "both"):
            _search_status[status_key]["message"] = "Fetching related keywords..."
            related = await _dataforseo_related_keywords(
                seed, login, password, location_code, language_code
            )
            all_keywords.extend(related)

        if mode in ("suggestions", "both"):
            _search_status[status_key]["message"] = "Fetching keyword suggestions..."
            suggestions = await _dataforseo_keyword_suggestions(
                seed, login, password, location_code, language_code
            )
            all_keywords.extend(suggestions)

        # Deduplicate by keyword text (keep the first occurrence)
        seen: set[str] = set()
        deduped: list[dict] = []
        for kw in all_keywords:
            key = kw["keyword"].lower()
            if key not in seen:
                seen.add(key)
                deduped.append(kw)
        all_keywords = deduped

        if not all_keywords:
            _search_status[status_key] = {
                "step": "done", "message": "No keywords found.", "done": True, "count": 0,
            }
            return []

        # Step 2: Enrich with bulk keyword difficulty
        _search_status[status_key]["message"] = (
            f"Getting difficulty scores for {len(all_keywords)} keywords..."
        )
        kw_texts = [kw["keyword"] for kw in all_keywords]
        diff_map = await _dataforseo_bulk_keyword_difficulty(
            kw_texts, login, password, location_code, language_code
        )

        # Merge difficulty scores into keyword data
        for kw in all_keywords:
            kd = diff_map.get(kw["keyword"].lower())
            if kd is not None:
                kw["difficulty"] = kd

        _search_status[status_key] = {
            "step": "done",
            "message": f"Done! Found {len(all_keywords)} keywords.",
            "done": True,
            "count": len(all_keywords),
        }
        # Clean up status entry after 60 seconds to prevent memory leak
        _schedule_status_cleanup(status_key)

    except Exception as exc:
        _search_status[status_key] = {
            "step": "error",
            "message": f"Error: {exc}",
            "done": True,
            "count": 0,
        }
        _schedule_status_cleanup(status_key)
        raise

    return all_keywords


# ---------------------------------------------------------------------------
# CSV parser  (Ahrefs, Semrush, or generic)
# ---------------------------------------------------------------------------

_COLUMN_ALIASES: dict[str, list[str]] = {
    "keyword": ["keyword", "query", "search query", "term", "keyphrase"],
    "volume": [
        "volume", "search volume", "avg. monthly searches",
        "avg monthly searches", "search_volume",
    ],
    "difficulty": [
        "difficulty", "keyword difficulty", "kd", "kd%",
        "keyword_difficulty", "seo difficulty",
    ],
    "cpc": ["cpc", "cost per click", "cpc (usd)", "cpc(usd)"],
    "competition": ["competition", "competitive density", "comp."],
}


def _normalise_header(header: str) -> str:
    return header.strip().lower().replace("_", " ")


def _map_columns(headers: list[str]) -> dict[str, int | None]:
    """Map canonical field names to column indices in the CSV."""
    mapping: dict[str, int | None] = {k: None for k in _COLUMN_ALIASES}
    normed = [_normalise_header(h) for h in headers]
    for field, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normed:
                mapping[field] = normed.index(alias)
                break
    return mapping


def parse_csv(content: str) -> list[dict]:
    """Parse a CSV string into keyword dicts, auto-detecting format."""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        return []

    col_map = _map_columns(rows[0])
    if col_map["keyword"] is None:
        return []

    keywords: list[dict] = []
    for row in rows[1:]:
        if not row:
            continue
        kw_idx = col_map["keyword"]
        if kw_idx is None or kw_idx >= len(row):
            continue
        kw_text = row[kw_idx].strip()
        if not kw_text:
            continue

        def _safe_int(idx: int | None) -> int:
            if idx is None or idx >= len(row):
                return 0
            val = row[idx].strip().replace(",", "").replace("%", "")
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return 0

        def _safe_float(idx: int | None) -> float:
            if idx is None or idx >= len(row):
                return 0.0
            val = row[idx].strip().replace(",", "").replace("$", "").replace("%", "")
            try:
                return round(float(val), 4)
            except (ValueError, TypeError):
                return 0.0

        keywords.append({
            "keyword": kw_text,
            "volume": _safe_int(col_map["volume"]),
            "difficulty": _safe_int(col_map["difficulty"]),
            "cpc": _safe_float(col_map["cpc"]),
            "competition": _safe_float(col_map["competition"]),
        })

    return keywords


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    seed_keyword: str
    mode: str = "related"  # 'related', 'suggestions', 'both', or 'exact'
    force_refresh: bool = False  # bypass DB deduplication


class EstimateCostRequest(BaseModel):
    seed_keyword: str
    mode: str = "related"


class SettingsPayload(BaseModel):
    data_source: str = "demo"           # demo | dataforseo
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    location_code: int = 2840
    language_code: str = "en"
    openai_api_key: str = ""


class NuggetHuntRequest(BaseModel):
    niches: list[str]  # e.g., ["mortgage", "fitness", "cooking"]
    suffixes: list[str] | None = None  # optional custom suffixes
    kd_max: int = 10  # max keyword difficulty to keep
    vol_min: int = 500  # min volume to keep
    mode: str = "related"  # search mode: related, suggestions, both


class NuggetHuntSettings(BaseModel):
    kd_max: int = 10
    vol_min: int = 500
    mode: str = "related"


# ---------------------------------------------------------------------------
# Nugget Hunter — default suffixes and background task state
# ---------------------------------------------------------------------------

DEFAULT_SUFFIXES = [
    "tool", "calculator", "checker", "generator", "converter",
    "maker", "finder", "planner", "tracker", "builder",
    "template", "tester", "analyzer", "estimator", "simulator",
]

# Track running hunt tasks so they can be awaited or cancelled
_active_hunts: dict[int, asyncio.Task] = {}  # hunt_id -> Task
_cancelled_hunts: set[int] = set()


def _classify_nugget_tier(difficulty: int, volume: int) -> str:
    """Assign a tier based on keyword difficulty and search volume."""
    if difficulty <= 2 and volume >= 1000:
        return "gold"
    if difficulty <= 5 and volume >= 500:
        return "silver"
    return "bronze"


async def _run_nugget_hunt(hunt_id: int) -> None:
    """
    Background pipeline that iterates every niche x suffix combo,
    calls DataForSEO, filters for low-KD / high-volume nuggets, and
    persists results to the nuggets table.
    """
    conn = get_db()
    try:
        hunt_row = conn.execute(
            "SELECT * FROM nugget_hunts WHERE id = ?", (hunt_id,)
        ).fetchone()
        if not hunt_row:
            logger.error("Nugget hunt %d not found", hunt_id)
            return

        niches: list[str] = json.loads(hunt_row["niches"])
        suffixes: list[str] = json.loads(hunt_row["suffixes"])
        settings: dict = json.loads(hunt_row["settings"])
        kd_max = settings.get("kd_max", 10)
        vol_min = settings.get("vol_min", 500)
        mode = settings.get("mode", "related")
    finally:
        conn.close()

    # Load DataForSEO credentials from the settings table
    app_settings = _get_settings()
    login = app_settings.get("dataforseo_login", "")
    password = app_settings.get("dataforseo_password", "")
    location_code = int(app_settings.get("location_code", "2840"))
    language_code = app_settings.get("language_code", "en")

    if not login or not password:
        _update_hunt_status(hunt_id, "failed", error="DataForSEO credentials not configured")
        return

    # Mark hunt as running
    conn = get_db()
    try:
        conn.execute(
            "UPDATE nugget_hunts SET status = 'running', started_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), hunt_id),
        )
        conn.commit()
    finally:
        conn.close()

    combos = [(niche, suffix) for niche in niches for suffix in suffixes]
    total_keywords_scanned = 0
    nuggets_found = 0

    for idx, (niche, suffix) in enumerate(combos):
        # Check for cancellation between combos
        if hunt_id in _cancelled_hunts:
            _cancelled_hunts.discard(hunt_id)
            _update_hunt_status(hunt_id, "cancelled")
            return

        combo_text = f"{niche} {suffix}"

        # Update progress in the DB
        conn = get_db()
        try:
            conn.execute(
                """UPDATE nugget_hunts
                   SET current_combo = ?, completed_combos = ?
                   WHERE id = ?""",
                (combo_text, idx, hunt_id),
            )
            conn.commit()
        finally:
            conn.close()

        try:
            results = await dataforseo_search(
                combo_text, login, password, mode, location_code, language_code
            )
        except Exception as exc:
            logger.warning("Nugget hunt %d: combo '%s' failed: %s", hunt_id, combo_text, exc)
            if idx < len(combos) - 1:
                await asyncio.sleep(2)
            continue

        total_keywords_scanned += len(results)

        # Filter for golden nuggets
        filtered = [
            kw for kw in results
            if kw.get("difficulty", 100) <= kd_max and kw.get("volume", 0) >= vol_min
        ]

        if filtered:
            filtered = compute_opportunity_scores(filtered)

            conn = get_db()
            try:
                for kw in filtered:
                    tier = _classify_nugget_tier(kw.get("difficulty", 0), kw.get("volume", 0))
                    try:
                        conn.execute(
                            """INSERT OR IGNORE INTO nuggets
                               (hunt_id, keyword, volume, difficulty, cpc, competition,
                                competition_level, monthly_searches, serp_features,
                                trend, opportunity_score, seed_combo, niche, suffix, tier)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                hunt_id,
                                kw["keyword"],
                                kw.get("volume", 0),
                                kw.get("difficulty", 0),
                                kw.get("cpc", 0.0),
                                kw.get("competition", 0.0),
                                kw.get("competition_level", ""),
                                json.dumps(kw.get("monthly_searches", [])),
                                json.dumps(kw.get("serp_features", [])),
                                kw.get("trend", "stable"),
                                kw.get("opportunity_score", 0),
                                combo_text,
                                niche,
                                suffix,
                                tier,
                            ),
                        )
                    except sqlite3.Error as db_err:
                        logger.warning("Nugget insert error: %s", db_err)

                conn.commit()

                # Recount nuggets for this hunt (INSERT OR IGNORE may skip dupes)
                actual_count = conn.execute(
                    "SELECT COUNT(*) FROM nuggets WHERE hunt_id = ?", (hunt_id,)
                ).fetchone()[0]
                nuggets_found = actual_count

                conn.execute(
                    """UPDATE nugget_hunts
                       SET nuggets_found = ?, total_keywords_scanned = ?
                       WHERE id = ?""",
                    (nuggets_found, total_keywords_scanned, hunt_id),
                )
                conn.commit()
            finally:
                conn.close()

        # Rate-limit delay between API calls (skip after last combo)
        if idx < len(combos) - 1:
            await asyncio.sleep(2)

    # Mark completed
    conn = get_db()
    try:
        conn.execute(
            """UPDATE nugget_hunts
               SET status = 'completed', completed_combos = ?, current_combo = '',
                   nuggets_found = ?, total_keywords_scanned = ?,
                   completed_at = ?
               WHERE id = ?""",
            (
                len(combos),
                nuggets_found,
                total_keywords_scanned,
                datetime.now(timezone.utc).isoformat(),
                hunt_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Clean up task reference
    _active_hunts.pop(hunt_id, None)


def _update_hunt_status(hunt_id: int, status: str, *, error: str = "") -> None:
    """Helper to set hunt status and optional error message."""
    conn = get_db()
    try:
        conn.execute(
            """UPDATE nugget_hunts
               SET status = ?, error_message = ?, completed_at = ?
               WHERE id = ?""",
            (status, error, datetime.now(timezone.utc).isoformat(), hunt_id),
        )
        conn.commit()
    finally:
        conn.close()
    _active_hunts.pop(hunt_id, None)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_settings() -> dict[str, str]:
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}
    finally:
        conn.close()


def _save_setting(key: str, value: str) -> None:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()


def _rows_to_dicts(rows: list) -> list[dict]:
    """Convert sqlite Row objects to dicts, parsing JSON fields."""
    result = []
    for r in rows:
        d = dict(r)
        for json_field in ("monthly_searches", "serp_features"):
            val = d.get(json_field, "[]")
            if isinstance(val, str):
                try:
                    d[json_field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    d[json_field] = []
        result.append(d)
    return result


def _generate_demo_search_results(seed: str) -> list[dict]:
    """Generate realistic-looking search results for demo mode."""
    results: list[dict] = []
    seed_lower = seed.lower()

    for kw in _DEMO_KEYWORDS:
        if seed_lower in kw["keyword"].lower():
            results.append(dict(kw))

    prefixes = ["best", "free", "online", "simple"]
    suffixes = ["online", "free", "tool", "app"]

    random.seed(hash(seed) + int(time.time() / 3600))
    for prefix in random.sample(prefixes, min(2, len(prefixes))):
        vol = random.randint(100, 5000)
        diff = random.randint(0, 60)
        results.append({
            "keyword": f"{prefix} {seed}",
            "volume": vol,
            "difficulty": diff,
            "cpc": round(random.uniform(0.1, 3.0), 2),
            "competition": round(random.uniform(0.01, 0.8), 2),
            "competition_level": "LOW" if diff < 30 else "MEDIUM",
            "trend": random.choice(["rising", "stable", "declining"]),
        })
    for suffix in random.sample(suffixes, min(2, len(suffixes))):
        vol = random.randint(50, 3000)
        diff = random.randint(0, 45)
        results.append({
            "keyword": f"{seed} {suffix}",
            "volume": vol,
            "difficulty": diff,
            "cpc": round(random.uniform(0.1, 2.5), 2),
            "competition": round(random.uniform(0.01, 0.7), 2),
            "competition_level": "LOW" if diff < 30 else "MEDIUM",
            "trend": random.choice(["rising", "stable", "stable"]),
        })

    results.append({
        "keyword": seed,
        "volume": random.randint(1000, 20000),
        "difficulty": random.randint(10, 50),
        "cpc": round(random.uniform(0.5, 4.0), 2),
        "competition": round(random.uniform(0.1, 0.9), 2),
        "competition_level": "MEDIUM",
        "trend": "stable",
    })

    return results


def _upsert_keywords(
    keywords: list[dict], *, source: str, seed: str
) -> None:
    """Insert or update keywords in the database."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.executemany(
            """INSERT INTO keywords
               (keyword, volume, difficulty, cpc, competition, competition_level,
                monthly_searches, serp_features, trend, source, seed_keyword, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(keyword) DO UPDATE SET
                 volume = excluded.volume,
                 difficulty = excluded.difficulty,
                 cpc = excluded.cpc,
                 competition = excluded.competition,
                 competition_level = excluded.competition_level,
                 monthly_searches = excluded.monthly_searches,
                 serp_features = excluded.serp_features,
                 trend = excluded.trend,
                 source = excluded.source,
                 seed_keyword = excluded.seed_keyword,
                 last_updated = excluded.last_updated
            """,
            [
                (
                    kw["keyword"],
                    kw.get("volume", 0),
                    kw.get("difficulty", 0),
                    kw.get("cpc", 0.0),
                    kw.get("competition", 0.0),
                    kw.get("competition_level", ""),
                    json.dumps(kw.get("monthly_searches", [])),
                    json.dumps(kw.get("serp_features", [])),
                    kw.get("trend", "stable"),
                    source, seed, now,
                )
                for kw in keywords
            ],
        )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# REST Endpoints
# ===========================================================================


# ---- Serve HTML frontend ---------------------------------------------------

@router.get("/app")
async def serve_seo_app():
    """Serve the standalone keyword research HTML frontend.

    Rewrites API URLs from /api/ to /api/seo-tools/ so the embedded
    frontend's fetch calls hit the correct router endpoints.
    """
    from fastapi.responses import HTMLResponse

    index_path = Path(__file__).resolve().parent.parent.parent / "tools" / "keyword-research" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="SEO tools frontend not found")

    html = index_path.read_text(encoding="utf-8")
    # Rewrite API paths so fetch('/api/...') hits fetch('/api/seo-tools/...')
    html = html.replace("'/api/", "'/api/seo-tools/")
    html = html.replace('"/api/', '"/api/seo-tools/')
    html = html.replace("`/api/", "`/api/seo-tools/")
    return HTMLResponse(content=html)


# ---- Settings --------------------------------------------------------------

@router.get("/settings")
async def get_settings():
    """Get current SEO tools settings (passwords masked)."""
    settings = _get_settings()
    masked: dict[str, str] = {}
    for k, v in settings.items():
        if any(secret in k for secret in ("password", "secret", "token", "api_key")):
            masked[k] = "***" + v[-4:] if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked


@router.post("/settings")
async def save_settings(payload: SettingsPayload):
    """Save SEO tools settings (data source, API credentials, location, language)."""
    for field_name, value in payload.model_dump().items():
        _save_setting(field_name, str(value))
    return {"status": "ok"}


# ---- API Balance -----------------------------------------------------------

@router.get("/balance")
async def get_balance():
    """Check DataForSEO API credit balance."""
    settings = _get_settings()
    login = settings.get("dataforseo_login", "")
    password = settings.get("dataforseo_password", "")

    if not login or not password:
        return {"connected": False, "balance": 0, "message": "No API credentials configured"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DATAFORSEO_BASE}/appendix/user_data",
                auth=(login, password),
            )

            if resp.status_code == 401:
                return {"connected": False, "balance": 0, "message": "Invalid credentials (401)"}
            if resp.status_code == 403:
                return {"connected": False, "balance": 0, "message": "Access denied (403)"}

            resp.raise_for_status()
            data = resp.json()

            balance = 0.0
            for task in data.get("tasks", []):
                for result in task.get("result", []) or []:
                    money_data = result.get("money", {})
                    balance = money_data.get("balance", 0.0)
                    break

            return {
                "connected": True,
                "balance": round(balance, 2),
                "message": f"${balance:.2f} remaining",
            }

    except httpx.HTTPStatusError as exc:
        return {"connected": False, "balance": 0, "message": f"API error: {exc.response.status_code}"}
    except Exception as exc:
        return {"connected": False, "balance": 0, "message": f"Connection error: {exc}"}


# ---- Search status (polling) -----------------------------------------------

@router.get("/search-status")
async def get_search_status(seed: str = Query("")):
    """Get the current status of an ongoing search."""
    status_key = seed.strip().lower()
    status = _search_status.get(status_key)
    if status is None:
        return {"step": "idle", "message": "", "done": True}
    return status


# ---- AI Seed Ordering (Phase 4) ---------------------------------------------

async def _ai_order_seeds(seeds: list[str], openai_key: str) -> list[str]:
    """Use a cheap AI model to order seeds from broadest to most specific.

    Broadest seeds are searched first so their results can cross-resolve
    more specific seeds, saving API calls.
    """
    if not openai_key or len(seeds) <= 2:
        return seeds

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You order keywords from broadest (most likely to encompass "
                                "other keywords in search results) to most specific. "
                                "Return ONLY a JSON array of strings, no other text."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Order these keywords from broadest to most specific: {json.dumps(seeds)}",
                        },
                    ],
                    "temperature": 0,
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            ordered = json.loads(content)
            # Validate all original seeds are present
            if set(s.lower() for s in ordered) == set(s.lower() for s in seeds):
                return [s.lower() for s in ordered]
            # AI missed some — append missing ones at the end
            ordered_lower = [s.lower() for s in ordered]
            for s in seeds:
                if s.lower() not in ordered_lower:
                    ordered_lower.append(s.lower())
            return ordered_lower
    except Exception as e:
        logger.warning("AI seed ordering failed, using original order: %s", e)
        return seeds


# ---- Cost Estimation --------------------------------------------------------

@router.post("/estimate-cost")
async def estimate_cost(req: EstimateCostRequest):
    """Estimate API cost before running a search, accounting for cached seeds."""
    raw_seeds = [s.strip().lower() for s in req.seed_keyword.split(",") if s.strip()]
    if not raw_seeds:
        return {"total_seeds": 0, "seeds_to_search": 0, "seeds_skipped": 0,
                "skipped_list": [], "estimated_cost": 0.0, "mode": req.mode}

    # Check which seeds already exist in the database
    conn = get_db()
    try:
        existing_seeds = set(row[0] for row in conn.execute(
            "SELECT DISTINCT seed_keyword FROM keywords"
        ).fetchall())
        existing_keywords = set(row[0] for row in conn.execute(
            "SELECT DISTINCT keyword FROM keywords"
        ).fetchall())
    finally:
        conn.close()

    seeds_to_search = [s for s in raw_seeds if s not in existing_seeds and s not in existing_keywords]
    seeds_skipped = [s for s in raw_seeds if s in existing_seeds or s in existing_keywords]

    n = len(seeds_to_search)
    mode = req.mode if req.mode in ("related", "suggestions", "both", "exact") else "related"
    # Approximate cost per seed by mode
    cost_per_seed = {"related": 0.06, "suggestions": 0.06, "both": 0.12, "exact": 0.005}
    api_cost = n * cost_per_seed.get(mode, 0.06)
    # Add bulk difficulty lookup cost (~$0.005 per seed)
    if mode != "exact" and n > 0:
        api_cost += 0.005 * n

    return {
        "total_seeds": len(raw_seeds),
        "seeds_to_search": n,
        "seeds_skipped": len(seeds_skipped),
        "skipped_list": seeds_skipped,
        "estimated_cost": round(api_cost, 3),
        "mode": mode,
    }


# ---- Search -----------------------------------------------------------------

@router.post("/search")
async def search_keywords(req: SearchRequest):
    """Search for keywords by seed. Supports comma-separated seeds."""
    raw_seeds = [s.strip().lower() for s in req.seed_keyword.split(",") if s.strip()]
    if not raw_seeds:
        return {"error": "Seed keyword is required", "keywords": [], "count": 0}

    mode = req.mode if req.mode in ("related", "suggestions", "both", "exact") else "related"
    settings = _get_settings()
    source = settings.get("data_source", "demo")

    all_new_keywords: list[dict] = []
    # Track per-seed results for multi-keyword progress reporting
    seed_results: dict[str, int] = {}
    cross_resolved: list[str] = []

    # --- Phase 1: DB Deduplication — skip seeds already in the database ---
    # (bypassed when force_refresh=True)
    seeds_to_search: list[str] = []
    seeds_skipped: list[str] = []
    if req.force_refresh:
        seeds_to_search = list(raw_seeds)
    else:
        conn = get_db()
        try:
            existing_seeds = set(row[0] for row in conn.execute(
                "SELECT DISTINCT seed_keyword FROM keywords"
            ).fetchall())
            existing_keywords = set(row[0] for row in conn.execute(
                "SELECT DISTINCT keyword FROM keywords"
            ).fetchall())
        finally:
            conn.close()

        for seed in raw_seeds:
            if seed in existing_seeds or seed in existing_keywords:
                seeds_skipped.append(seed)
            else:
                seeds_to_search.append(seed)

    # Set up progress tracking for the multi-seed search
    progress_key = raw_seeds[0] if raw_seeds else "search"
    total_to_search = len(seeds_to_search)

    if mode == "exact" and source == "dataforseo":
        # Exact mode: look up the exact keywords for volume/CPC/competition + KD
        login = settings.get("dataforseo_login", "")
        password = settings.get("dataforseo_password", "")
        if not login or not password:
            return {"error": "DataForSEO credentials not configured", "keywords": [], "count": 0}
        location_code = int(settings.get("location_code", "2840"))
        language_code = settings.get("language_code", "en")

        if seeds_to_search:
            try:
                # Get search volume data for new seeds only
                kws = await _dataforseo_search_volume(
                    seeds_to_search, login, password, location_code, language_code
                )
                # Get KD scores
                if kws:
                    kw_texts = [kw["keyword"] for kw in kws]
                    diff_map = await _dataforseo_bulk_keyword_difficulty(
                        kw_texts, login, password, location_code, language_code
                    )
                    for kw in kws:
                        kd = diff_map.get(kw["keyword"].lower())
                        if kd is not None:
                            kw["difficulty"] = kd
                all_new_keywords.extend(kws)

                # Map results back to seeds and persist per-seed
                kw_by_text = {kw["keyword"].lower(): kw for kw in kws}
                for seed in seeds_to_search:
                    if seed in kw_by_text:
                        seed_results[seed] = 1
                        _upsert_keywords([kw_by_text[seed]], source=source, seed=seed)
                    else:
                        seed_results[seed] = 0

            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                error_msgs = {
                    401: "Authentication failed. Check your DataForSEO credentials.",
                    403: "Access denied. Your account may not have access to this endpoint.",
                    402: "Insufficient balance. Please top up your DataForSEO account.",
                    429: "Rate limit exceeded. Please wait a moment and try again.",
                }
                return {"error": error_msgs.get(code, f"DataForSEO API error: {code}"), "keywords": [], "count": 0}
            except Exception as exc:
                return {"error": f"DataForSEO error: {exc}", "keywords": [], "count": 0}

    elif mode == "exact" and source != "dataforseo":
        # Exact mode in demo: generate minimal demo data for each seed as-is
        for seed in seeds_to_search:
            kws = _generate_demo_search_results(seed)
            # In exact mode, only keep the keyword that matches the seed exactly
            exact_match = [kw for kw in kws if kw["keyword"].lower() == seed]
            if exact_match:
                all_new_keywords.extend(exact_match)
                seed_results[seed] = len(exact_match)
                _upsert_keywords(exact_match, source=source, seed=seed)
            else:
                # Generate a single entry for the exact keyword
                demo_kw = kws[0] if kws else {
                    "keyword": seed, "volume": random.randint(50, 5000),
                    "cpc": round(random.uniform(0.10, 3.00), 2),
                    "competition": round(random.uniform(0.01, 0.95), 2),
                    "competition_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
                    "monthly_searches": [], "serp_features": [], "trend": "stable",
                }
                demo_kw["keyword"] = seed
                all_new_keywords.append(demo_kw)
                seed_results[seed] = 1
                _upsert_keywords([demo_kw], source=source, seed=seed)
    else:
        # Standard modes: related, suggestions, both
        # Phase 3: Sequential cross-check — after each seed, check if remaining
        # seeds appear in returned keywords (saving API calls)
        remaining_seeds = list(seeds_to_search)

        # Phase 4: AI seed ordering — order broadest-first for better cross-check
        if len(remaining_seeds) > 2:
            _search_status[progress_key] = {
                "step": "ordering", "done": False,
                "message": f"AI ordering {len(remaining_seeds)} seeds for optimal search order...",
                "searched": 0, "total": total_to_search, "cross_resolved": 0,
            }
            openai_key = settings.get("openai_api_key", "")
            remaining_seeds = await _ai_order_seeds(remaining_seeds, openai_key)

        searched_count = 0
        while remaining_seeds:
            seed = remaining_seeds.pop(0)
            searched_count += 1
            _search_status[progress_key] = {
                "step": "searching", "done": False,
                "message": f"Searching seed {searched_count}/{total_to_search}: \"{seed}\"",
                "searched": searched_count, "total": total_to_search,
                "cross_resolved": len(cross_resolved),
            }
            kws: list[dict] = []
            if source == "dataforseo":
                login = settings.get("dataforseo_login", "")
                password = settings.get("dataforseo_password", "")
                if not login or not password:
                    return {"error": "DataForSEO credentials not configured", "keywords": [], "count": 0}

                location_code = int(settings.get("location_code", "2840"))
                language_code = settings.get("language_code", "en")

                try:
                    kws = await dataforseo_search(
                        seed, login, password, mode, location_code, language_code
                    )
                    all_new_keywords.extend(kws)
                except httpx.HTTPStatusError as exc:
                    code = exc.response.status_code
                    error_msgs = {
                        401: "Authentication failed. Check your DataForSEO credentials.",
                        403: "Access denied. Your account may not have access to this endpoint.",
                        402: "Insufficient balance. Please top up your DataForSEO account.",
                        429: "Rate limit exceeded. Please wait a moment and try again.",
                    }
                    return {"error": error_msgs.get(code, f"DataForSEO API error: {code}"), "keywords": [], "count": 0}
                except Exception as exc:
                    return {"error": f"DataForSEO error: {exc}", "keywords": [], "count": 0}
            else:
                # Demo mode
                kws = _generate_demo_search_results(seed)
                all_new_keywords.extend(kws)

            seed_results[seed] = len(kws)
            # Persist this seed's keywords
            if kws:
                _upsert_keywords(kws, source=source, seed=seed)

            # Phase 3: Cross-check — see if remaining seeds appear in returned keywords
            if kws and remaining_seeds:
                returned_keywords = {kw["keyword"].lower() for kw in kws}
                still_remaining = []
                for rs in remaining_seeds:
                    if rs in returned_keywords:
                        cross_resolved.append(rs)
                        seed_results[rs] = 0  # resolved via cross-check, no API call needed
                    else:
                        still_remaining.append(rs)
                if len(still_remaining) < len(remaining_seeds):
                    resolved_now = len(remaining_seeds) - len(still_remaining)
                    _search_status[progress_key] = {
                        "step": "searching", "done": False,
                        "message": (
                            f"Cross-check resolved {resolved_now} seed(s)! "
                            f"{len(still_remaining)} remaining"
                        ),
                        "searched": searched_count, "total": total_to_search,
                        "cross_resolved": len(cross_resolved),
                    }
                remaining_seeds = still_remaining

    # Update progress: done
    _search_status[progress_key] = {
        "step": "done", "done": True,
        "message": f"Complete. Searched {total_to_search - len(cross_resolved)} seeds, {len(cross_resolved)} cross-resolved, {len(seeds_skipped)} cached.",
        "searched": total_to_search, "total": total_to_search,
        "cross_resolved": len(cross_resolved),
    }
    _schedule_status_cleanup(progress_key, delay=30)

    # Record search history for each seed
    conn = get_db()
    try:
        for seed in raw_seeds:
            seed_count = conn.execute(
                "SELECT COUNT(*) FROM keywords WHERE seed_keyword = ?", (seed,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO search_history (seed_keyword, mode, keywords_found) VALUES (?, ?, ?)",
                (seed, mode, seed_count),
            )
        conn.commit()
    finally:
        conn.close()

    # Return all keywords matching ANY of the seeds
    conn = get_db()
    try:
        placeholders = ",".join("?" for _ in raw_seeds)
        rows = conn.execute(
            f"""SELECT keyword, volume, difficulty, cpc, competition,
                      competition_level, monthly_searches, serp_features,
                      trend, source
               FROM keywords WHERE seed_keyword IN ({placeholders}) ORDER BY volume DESC""",
            raw_seeds,
        ).fetchall()
        result = _rows_to_dicts(rows)
        result = compute_opportunity_scores(result)
        return {
            "keywords": result,
            "count": len(result),
            "seed_results": seed_results,
            "seeds_skipped": seeds_skipped,
            "seeds_searched": len(seeds_to_search),
            "cross_resolved": cross_resolved,
        }
    finally:
        conn.close()


# ---- CSV Import -------------------------------------------------------------

@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """Import keywords from an uploaded CSV (Ahrefs, Semrush, or generic)."""
    content = (await file.read()).decode("utf-8-sig")
    keywords = parse_csv(content)
    if not keywords:
        return {"error": "Could not parse any keywords from the CSV. Check column headers.", "count": 0}

    _upsert_keywords(keywords, source="csv_import", seed="csv_import")

    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
        return {"status": "ok", "imported": len(keywords), "total": total}
    finally:
        conn.close()


# ---- CSV Export -------------------------------------------------------------

@router.get("/export-csv")
async def export_csv(
    difficulty_min: int = Query(0, ge=0, le=100),
    difficulty_max: int = Query(100, ge=0, le=100),
    volume_min: int = Query(0, ge=0),
    volume_max: int = Query(10_000_000, ge=0),
    seed: str = Query(""),
):
    """Export keywords as a downloadable CSV file."""
    conn = get_db()
    try:
        params: list[Any] = [difficulty_min, difficulty_max, volume_min, volume_max]
        query = """SELECT keyword, volume, difficulty, cpc, competition,
                          competition_level, trend, source
                   FROM keywords
                   WHERE difficulty >= ? AND difficulty <= ?
                     AND volume >= ? AND volume <= ?"""
        if seed:
            query += " AND seed_keyword = ?"
            params.append(seed)
        query += " ORDER BY volume DESC"

        rows = conn.execute(query, params).fetchall()
        result = [dict(r) for r in rows]
        result = compute_opportunity_scores(result)
    finally:
        conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["keyword", "volume", "difficulty", "cpc", "competition",
                     "competition_level", "trend", "opportunity_score", "source"],
    )
    writer.writeheader()
    for row in result:
        writer.writerow({
            "keyword": row["keyword"],
            "volume": row["volume"],
            "difficulty": row["difficulty"],
            "cpc": row["cpc"],
            "competition": row["competition"],
            "competition_level": row.get("competition_level", ""),
            "trend": row.get("trend", "stable"),
            "opportunity_score": row.get("opportunity_score", 0),
            "source": row.get("source", ""),
        })

    csv_bytes = output.getvalue().encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="keywords_export_{timestamp}.csv"',
        },
    )


# ---- Keywords list (with filtering) ----------------------------------------

@router.get("/keywords")
async def get_keywords(
    difficulty_min: int = Query(0, ge=0, le=100),
    difficulty_max: int = Query(100, ge=0, le=100),
    volume_min: int = Query(0, ge=0),
    volume_max: int = Query(10_000_000, ge=0),
    sort_by: str = Query("volume"),
    sort_order: str = Query("desc"),
    seeds: str = Query(""),
):
    """Get all cached keywords with filtering and sorting. Optionally filter by comma-separated seeds."""
    allowed_sort = {
        "volume", "difficulty", "cpc", "competition", "keyword",
        "opportunity_score", "trend", "competition_level",
    }
    if sort_by not in allowed_sort:
        sort_by = "volume"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    conn = get_db()
    try:
        params: list[Any] = [difficulty_min, difficulty_max, volume_min, volume_max]
        query = """SELECT keyword, volume, difficulty, cpc, competition,
                      competition_level, monthly_searches, serp_features,
                      trend, source
               FROM keywords
               WHERE difficulty >= ? AND difficulty <= ?
                 AND volume >= ? AND volume <= ?"""

        seed_list = [s.strip().lower() for s in seeds.split(",") if s.strip()] if seeds.strip() else []
        if seed_list:
            placeholders = ",".join("?" for _ in seed_list)
            query += f" AND seed_keyword IN ({placeholders})"
            params.extend(seed_list)

        query += " ORDER BY volume DESC"
        rows = conn.execute(query, params).fetchall()
        result = _rows_to_dicts(rows)
        result = compute_opportunity_scores(result)

        reverse = sort_order == "desc"
        try:
            result.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=reverse)
        except TypeError:
            result.sort(key=lambda r: str(r.get(sort_by, "")), reverse=reverse)

        return {"keywords": result, "count": len(result)}
    finally:
        conn.close()


# ---- Segments ---------------------------------------------------------------

@router.get("/segments")
async def get_segments():
    """Get keyword counts per difficulty segment."""
    segments = [
        {"label": "0", "min": 0, "max": 0},
        {"label": "1-5", "min": 1, "max": 5},
        {"label": "6-10", "min": 6, "max": 10},
        {"label": "11-20", "min": 11, "max": 20},
        {"label": "21-50", "min": 21, "max": 50},
        {"label": "51-100", "min": 51, "max": 100},
    ]
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
        for seg in segments:
            count = conn.execute(
                "SELECT COUNT(*) FROM keywords WHERE difficulty >= ? AND difficulty <= ?",
                (seg["min"], seg["max"]),
            ).fetchone()[0]
            seg["count"] = count
        return {"segments": segments, "total": total}
    finally:
        conn.close()


# ---- Clear database ---------------------------------------------------------

@router.post("/clear")
async def clear_keywords():
    """Clear all keywords from the database."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM keywords")
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


# ===========================================================================
# Nugget Hunter API endpoints
# ===========================================================================

@router.post("/nugget-hunt/start")
async def start_nugget_hunt(req: NuggetHuntRequest):
    """Start a new automated nugget hunt across niche x suffix combos."""
    niches = [n.strip().lower() for n in req.niches if n.strip()]
    if not niches:
        return {"error": "At least one niche is required"}

    suffixes = req.suffixes if req.suffixes else DEFAULT_SUFFIXES
    suffixes = [s.strip().lower() for s in suffixes if s.strip()]
    total_combos = len(niches) * len(suffixes)

    settings_json = json.dumps({
        "kd_max": req.kd_max,
        "vol_min": req.vol_min,
        "mode": req.mode,
    })

    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO nugget_hunts (status, niches, suffixes, settings, total_combos)
               VALUES ('pending', ?, ?, ?, ?)""",
            (json.dumps(niches), json.dumps(suffixes), settings_json, total_combos),
        )
        hunt_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    task = asyncio.create_task(_run_nugget_hunt(hunt_id))
    _active_hunts[hunt_id] = task

    return {"hunt_id": hunt_id, "status": "running", "total_combos": total_combos}


@router.get("/nugget-hunt/status")
async def get_nugget_hunt_status(hunt_id: int = Query(...)):
    """Get the current status and progress of a nugget hunt."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM nugget_hunts WHERE id = ?", (hunt_id,)
        ).fetchone()
        if not row:
            return {"error": "Hunt not found"}
        result = dict(row)
        for field in ("niches", "suffixes", "settings"):
            val = result.get(field, "[]")
            if isinstance(val, str):
                try:
                    result[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result
    finally:
        conn.close()


@router.post("/nugget-hunt/cancel")
async def cancel_nugget_hunt(hunt_id: int = Query(...)):
    """Cancel a running nugget hunt."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status FROM nugget_hunts WHERE id = ?", (hunt_id,)
        ).fetchone()
        if not row:
            return {"error": "Hunt not found"}
        if row["status"] not in ("pending", "running"):
            return {"error": f"Hunt is already {row['status']}"}
    finally:
        conn.close()

    _cancelled_hunts.add(hunt_id)

    if hunt_id not in _active_hunts:
        _update_hunt_status(hunt_id, "cancelled")

    return {"status": "cancelling", "hunt_id": hunt_id}


@router.get("/nugget-hunt/results")
async def get_nugget_hunt_results(
    hunt_id: int = Query(...),
    tier: str = Query("all"),
    sort_by: str = Query("volume"),
    sort_order: str = Query("desc"),
):
    """Get the nuggets found by a hunt, with optional tier filter and sorting."""
    allowed_sort = {"volume", "difficulty", "opportunity_score", "cpc", "keyword", "tier"}
    if sort_by not in allowed_sort:
        sort_by = "volume"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    conn = get_db()
    try:
        params: list[Any] = [hunt_id]
        query = """SELECT * FROM nuggets WHERE hunt_id = ?"""
        if tier and tier != "all":
            query += " AND tier = ?"
            params.append(tier)

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for json_field in ("monthly_searches", "serp_features"):
                val = d.get(json_field, "[]")
                if isinstance(val, str):
                    try:
                        d[json_field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        d[json_field] = []
            result.append(d)

        reverse = sort_order == "desc"
        try:
            result.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=reverse)
        except TypeError:
            result.sort(key=lambda r: str(r.get(sort_by, "")), reverse=reverse)

        return {"nuggets": result, "count": len(result)}
    finally:
        conn.close()


@router.get("/nugget-hunt/history")
async def get_nugget_hunt_history():
    """Get a list of all nugget hunts, most recent first."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM nugget_hunts ORDER BY created_at DESC"
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            for field in ("niches", "suffixes", "settings"):
                val = d.get(field, "[]")
                if isinstance(val, str):
                    try:
                        d[field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        pass
            results.append(d)
        return {"hunts": results, "count": len(results)}
    finally:
        conn.close()


@router.get("/nugget-hunt/export-csv")
async def export_nugget_hunt_csv(
    hunt_id: int = Query(...),
    tier: str = Query("all"),
):
    """Export nuggets from a hunt as a downloadable CSV file."""
    conn = get_db()
    try:
        params: list[Any] = [hunt_id]
        query = "SELECT * FROM nuggets WHERE hunt_id = ?"
        if tier and tier != "all":
            query += " AND tier = ?"
            params.append(tier)
        query += " ORDER BY volume DESC"

        rows = conn.execute(query, params).fetchall()
        result = [dict(r) for r in rows]
    finally:
        conn.close()

    output = io.StringIO()
    fieldnames = [
        "keyword", "volume", "difficulty", "cpc", "competition",
        "competition_level", "trend", "opportunity_score", "tier",
        "seed_combo", "niche", "suffix",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in result:
        writer.writerow(row)

    csv_bytes = output.getvalue().encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="nuggets_hunt_{hunt_id}_{timestamp}.csv"',
        },
    )


@router.delete("/nugget-hunt/delete")
async def delete_nugget_hunt(hunt_id: int = Query(...)):
    """Delete a hunt and all its associated nuggets."""
    if hunt_id in _active_hunts:
        _cancelled_hunts.add(hunt_id)
        task = _active_hunts.pop(hunt_id, None)
        if task and not task.done():
            task.cancel()

    conn = get_db()
    try:
        conn.execute("DELETE FROM nuggets WHERE hunt_id = ?", (hunt_id,))
        conn.execute("DELETE FROM nugget_hunts WHERE id = ?", (hunt_id,))
        conn.commit()
        return {"status": "ok", "hunt_id": hunt_id}
    finally:
        conn.close()


# ===========================================================================
# Search History endpoints
# ===========================================================================


@router.get("/search-history")
async def get_search_history():
    """Get all search history entries, most recent first."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, seed_keyword, mode, keywords_found, searched_at "
            "FROM search_history ORDER BY searched_at DESC"
        ).fetchall()
        history = [dict(r) for r in rows]
        # Enrich with current total keyword count per seed
        for entry in history:
            seed = entry.get("seed_keyword", "")
            if seed:
                total = conn.execute(
                    "SELECT COUNT(*) FROM keywords WHERE LOWER(seed_keyword) = LOWER(?)", (seed,)
                ).fetchone()[0]
                entry["total_keywords"] = total
            else:
                entry["total_keywords"] = 0
        return {"history": history, "count": len(history)}
    finally:
        conn.close()


@router.delete("/search-history/{history_id}")
async def delete_search_history_entry(history_id: int):
    """Delete a single search history entry."""
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM search_history WHERE id = ?", (history_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="History entry not found")
        return {"status": "ok"}
    finally:
        conn.close()


# ===========================================================================
# Domain availability bulk check (RDAP)
# ===========================================================================


class DomainCheckBulkRequest(BaseModel):
    keywords: list[str]
    tlds: list[str] = [".com", ".net"]


def _keyword_to_domain_base(keyword: str) -> str:
    """Convert a keyword phrase to a domain-safe base string."""
    base = keyword.lower().strip()
    base = re.sub(r"[^a-z0-9]+", "", base)
    return base


@router.get("/domain-check")
async def domain_check(keyword: str = Query(...)):
    """Check domain availability for a single keyword across common TLDs via RDAP."""
    base = _keyword_to_domain_base(keyword)
    if not base:
        raise HTTPException(status_code=400, detail="Keyword produces no valid domain base")

    tlds = [".com", ".net", ".org", ".io", ".co", ".ai", ".app", ".dev"]
    domains: list[dict] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(0, len(tlds), 3):
            batch = tlds[i : i + 3]
            tasks = [_check_rdap(client, keyword, tld, f"{base}{tld}") for tld in batch]
            batch_results = await asyncio.gather(*tasks)
            for _kw, tld, available in batch_results:
                domains.append({"domain": f"{base}{tld}", "tld": tld, "available": available})
            if i + 3 < len(tlds):
                await asyncio.sleep(0.5)

    return {"keyword": keyword, "domains": domains}


@router.post("/domain-check-bulk")
async def domain_check_bulk(req: DomainCheckBulkRequest):
    """Check domain availability for keyword+TLD combos via RDAP."""
    results: dict[str, dict[str, dict[str, bool]]] = {}

    # Build all (keyword, tld, domain) combos
    combos: list[tuple[str, str, str]] = []
    for kw in req.keywords:
        base = _keyword_to_domain_base(kw)
        if not base:
            continue
        results[kw] = {}
        for tld in req.tlds:
            tld_clean = tld if tld.startswith(".") else f".{tld}"
            domain = f"{base}{tld_clean}"
            combos.append((kw, tld_clean, domain))

    # Check in batches of 3
    async with httpx.AsyncClient(timeout=5.0) as client:
        for i in range(0, len(combos), 3):
            batch = combos[i : i + 3]
            tasks = []
            for kw, tld, domain in batch:
                tasks.append(_check_rdap(client, kw, tld, domain))
            batch_results = await asyncio.gather(*tasks)
            for kw, tld, available in batch_results:
                results[kw][tld] = {"available": available}
            if i + 3 < len(combos):
                await asyncio.sleep(0.5)

    return {"results": results}


async def _check_rdap(
    client: httpx.AsyncClient, keyword: str, tld: str, domain: str
) -> tuple[str, str, bool]:
    """Query RDAP for a single domain. 404 = available, 200 = taken."""
    try:
        resp = await client.get(f"https://rdap.org/domain/{domain}")
        available = resp.status_code == 404
    except Exception:
        # On timeout or error, report as unknown (treat as taken to be safe)
        available = False
    return keyword, tld, available


# ===========================================================================
# SERP Preview endpoint
# ===========================================================================


class SerpResult(BaseModel):
    rank: int
    title: str
    url: str
    domain: str
    description: str


@router.get("/serp-preview")
async def serp_preview(keyword: str = Query(...)):
    """Get top 10 SERP results for a keyword. Uses DataForSEO if configured, else demo."""
    settings = _get_settings()
    source = settings.get("data_source", "demo")
    base_domain = re.sub(r"[^a-z0-9]+", "", keyword.lower().strip())

    if source == "dataforseo":
        login = settings.get("dataforseo_login", "")
        password = settings.get("dataforseo_password", "")
        if login and password:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{DATAFORSEO_BASE}/serp/google/organic/live",
                        auth=(login, password),
                        json=[{
                            "keyword": keyword,
                            "location_code": int(settings.get("location_code", "2840")),
                            "language_code": settings.get("language_code", "en"),
                            "depth": 10,
                        }],
                    )
                    resp.raise_for_status()
                    data = resp.json()

                serp_results: list[dict] = []
                has_emd = False
                for task in data.get("tasks", []):
                    for res in task.get("result", []) or []:
                        for item in res.get("items", []) or []:
                            if item.get("type") != "organic":
                                continue
                            domain = item.get("domain", "")
                            serp_results.append({
                                "rank": item.get("rank_group", 0),
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "domain": domain,
                                "description": item.get("description", ""),
                            })
                            # EMD check: domain without TLD matches the base keyword
                            domain_base = re.sub(r"\.[a-z]+$", "", domain.lower())
                            domain_base = re.sub(r"[^a-z0-9]", "", domain_base)
                            if domain_base == base_domain:
                                has_emd = True

                return {
                    "results": serp_results[:10],
                    "base_domain": base_domain,
                    "has_exact_match": has_emd,
                }
            except Exception as exc:
                logger.warning("SERP preview DataForSEO error: %s", exc)
                # Fall through to demo

    # Demo mode — return mock results
    mock_results = [
        {"rank": i + 1, "title": f"Result {i + 1} for {keyword}", "url": f"https://example{i + 1}.com/{keyword.replace(' ', '-')}",
         "domain": f"example{i + 1}.com", "description": f"This is a sample search result about {keyword}."}
        for i in range(10)
    ]
    return {
        "results": mock_results,
        "base_domain": base_domain,
        "has_exact_match": False,
    }


# ===========================================================================
# Content Strategy endpoints
# ===========================================================================


class ContentStrategyRequest(BaseModel):
    url: str


class ContentStrategyKeywordsRequest(BaseModel):
    keywords: list[str]


@router.post("/content-strategy")
async def content_strategy(req: ContentStrategyRequest):
    """Generate a content strategy analysis for a URL. Currently demo mode only."""
    # Future: if OpenAI key is configured in settings, use it for real analysis
    _settings = _get_settings()
    _openai_key = _settings.get("openai_api_key", "")
    # For now, return demo data regardless of key presence
    return {
        "strategy": {
            "snapshot": {
                "url": req.url,
                "what_they_sell": "Software / SaaS product (demo data)",
                "icp": "Small-to-medium businesses looking for productivity tools",
                "primary_cta": "Start Free Trial",
                "pricing_motion": "Freemium with paid tiers",
                "differentiators": ["AI-powered features", "Easy onboarding", "Affordable pricing"],
                "estimated_traffic": random.randint(500, 50000),
                "domain_authority": random.randint(10, 80),
                "top_keyword_count": random.randint(5, 100),
            },
            "comparisons": [
                {"keyword": "vs competitor1", "volume": random.randint(100, 3000), "difficulty": random.randint(10, 50), "competitor": "competitor1.com"},
                {"keyword": "vs competitor2", "volume": random.randint(100, 3000), "difficulty": random.randint(10, 50), "competitor": "competitor2.com"},
            ],
            "alternatives": [
                {"keyword": "alternative keyword 1", "volume": random.randint(100, 5000), "difficulty": random.randint(0, 50)},
                {"keyword": "alternative keyword 2", "volume": random.randint(100, 5000), "difficulty": random.randint(0, 50)},
            ],
            "listicles": [
                {"keyword": "best tools for X", "volume": random.randint(200, 4000), "difficulty": random.randint(10, 40)},
                {"keyword": "top 10 X software", "volume": random.randint(200, 4000), "difficulty": random.randint(10, 40)},
            ],
            "integrations": [
                {"keyword": "X integration with Slack", "volume": random.randint(50, 1000), "difficulty": random.randint(5, 30)},
                {"keyword": "X integration with Zapier", "volume": random.randint(50, 1000), "difficulty": random.randint(5, 30)},
            ],
            "free_tools": [
                {"keyword": "free X calculator", "volume": random.randint(100, 3000), "difficulty": random.randint(5, 25)},
                {"keyword": "free X template", "volume": random.randint(100, 3000), "difficulty": random.randint(5, 25)},
            ],
            "pillars": [
                {
                    "title": "Complete Guide to X",
                    "keywords": [
                        {"keyword": "what is X", "volume": random.randint(500, 5000), "difficulty": random.randint(10, 40)},
                        {"keyword": "how to use X", "volume": random.randint(300, 3000), "difficulty": random.randint(10, 35)},
                    ],
                },
                {
                    "title": "X for Beginners",
                    "keywords": [
                        {"keyword": "X tutorial", "volume": random.randint(200, 2000), "difficulty": random.randint(10, 35)},
                        {"keyword": "X getting started", "volume": random.randint(100, 1000), "difficulty": random.randint(5, 30)},
                    ],
                },
            ],
        }
    }


@router.post("/content-strategy/research-keywords")
async def content_strategy_research_keywords(req: ContentStrategyKeywordsRequest):
    """Search each keyword via DataForSEO (or demo) and return keyword data."""
    settings = _get_settings()
    source = settings.get("data_source", "demo")
    all_keywords: list[dict] = []

    for kw in req.keywords:
        seed = kw.strip().lower()
        if not seed:
            continue
        if source == "dataforseo":
            login = settings.get("dataforseo_login", "")
            password = settings.get("dataforseo_password", "")
            if login and password:
                try:
                    results = await dataforseo_search(
                        seed, login, password, "related",
                        int(settings.get("location_code", "2840")),
                        settings.get("language_code", "en"),
                    )
                    all_keywords.extend(results)
                    if results:
                        _upsert_keywords(results, source=source, seed=seed)
                    continue
                except Exception as exc:
                    logger.warning("Content strategy keyword search error for '%s': %s", seed, exc)
        # Demo fallback
        results = _generate_demo_search_results(seed)
        all_keywords.extend(results)
        if results:
            _upsert_keywords(results, source="demo", seed=seed)

    all_keywords = compute_opportunity_scores(all_keywords)
    return {"results": all_keywords, "keywords": all_keywords, "count": len(all_keywords)}


# ===========================================================================
# AI-Powered Keyword Analysis WebSocket
# ===========================================================================
#
# Uses BackgroundSessionManager (same pattern as server/routers/workspace.py)
# so sessions survive WebSocket disconnects and viewers can reconnect.
# ===========================================================================

_SEO_SYSTEM_PROMPT = (
    "You are an SEO keyword research analyst with deep expertise in search engine "
    "optimization, keyword strategy, and content planning. You help users analyze "
    "keyword data, identify opportunities, plan content strategies, and understand "
    "search intent.\n\n"
    "When analyzing keywords, consider:\n"
    "- Search volume trends and seasonality\n"
    "- Keyword difficulty and competition levels\n"
    "- Commercial intent and CPC values\n"
    "- SERP feature opportunities (featured snippets, PAA, etc.)\n"
    "- Content gap analysis\n"
    "- Long-tail keyword opportunities\n"
    "- Topic clustering and content silos\n\n"
    "Provide actionable, data-driven recommendations. When the user shares keyword "
    "data, analyze it thoroughly and suggest specific strategies for ranking improvement."
)


@router.websocket("/ws")
async def seo_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for AI-powered SEO keyword analysis.

    Uses BackgroundSessionManager so sessions run independently of the
    WebSocket connection. Follows the viewer protocol from workspace.py.

    Client -> Server:
    - {"type": "start", "model": "opus"} - Create a new analysis session
    - {"type": "message", "content": "..."} - Send user message
    - {"type": "ping"} - Keep-alive ping

    Server -> Client:
    - {"type": "session_created", "session_id": "...", "conversation_id": int} - Session started
    - {"type": "text", "content": "..."} - AI response text
    - {"type": "tool_call", ...} - Tool usage events
    - {"type": "token_usage", ...} - Token usage stats
    - {"type": "session_completed"} - Session finished responding
    - {"type": "replay", "events": [...]} - Catch-up events on reconnect
    - {"type": "replay_done", "current_seq": int} - Replay complete
    - {"type": "pong"} - Keep-alive pong
    - {"type": "error", "content": "..."} - Error message
    """
    from ..services.background_session_manager import get_background_session_manager

    await websocket.accept()
    logger.info("SEO analysis WebSocket connected")

    manager = await get_background_session_manager()
    attached_session_id: Optional[str] = None

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                logger.debug("SEO chat received message type: %s", msg_type)

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "start":
                    # Create a new background session for SEO analysis.
                    model = message.get("model", "opus")
                    provider = "claude"

                    try:
                        bg_session = await manager.create_session(
                            conversation_id=None,
                            provider=provider,
                            model=model,
                            working_directory=None,
                            context_mode="200k",
                        )

                        # Detach from any previous session
                        if attached_session_id:
                            try:
                                await manager.detach_viewer(attached_session_id, websocket)
                            except KeyError:
                                pass

                        attached_session_id = bg_session.session_id
                        current_seq = await manager.attach_viewer(bg_session.session_id, websocket)

                        await websocket.send_json({
                            "type": "session_created",
                            "session_id": bg_session.session_id,
                            "conversation_id": bg_session.conversation_id,
                        })

                        # Replay events emitted between task start and viewer attachment
                        early_events = await bg_session.get_events_since(0)
                        if early_events:
                            replay_events = [
                                {**ev, "seq": seq}
                                for seq, ev in early_events
                                if seq <= current_seq
                            ]
                            if replay_events:
                                await websocket.send_json({
                                    "type": "replay",
                                    "events": replay_events,
                                })

                        # Send the SEO system prompt as the first message to
                        # prime the session with domain-specific context.
                        await manager.submit_message(
                            bg_session.session_id,
                            _SEO_SYSTEM_PROMPT
                            + "\n\nPlease acknowledge that you're ready to help "
                            "with SEO keyword analysis.",
                        )

                    except Exception as e:
                        logger.exception("Error starting SEO analysis session")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Failed to start session: {str(e)}",
                        })

                elif msg_type == "message":
                    if not attached_session_id:
                        await websocket.send_json({
                            "type": "error",
                            "content": "No active session. Send 'start' first.",
                        })
                        continue

                    user_content = message.get("content", "").strip()
                    if not user_content:
                        await websocket.send_json({"type": "error", "content": "Empty message"})
                        continue

                    try:
                        await manager.submit_message(attached_session_id, user_content)
                    except KeyError:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Session not found. It may have been cleaned up.",
                        })
                    except RuntimeError as e:
                        await websocket.send_json({
                            "type": "error",
                            "content": str(e),
                        })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown message type: {msg_type}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON",
                })

    except WebSocketDisconnect:
        logger.info("SEO analysis WebSocket disconnected")

    except Exception as e:
        logger.exception("SEO analysis WebSocket error")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Server error: {str(e)}",
            })
        except Exception:
            pass

    finally:
        # Detach viewer only; the session continues running in the background
        if attached_session_id:
            try:
                await manager.detach_viewer(attached_session_id, websocket)
            except Exception as e:
                logger.warning("Error detaching SEO viewer on disconnect: %s", e)
        logger.info("SEO analysis WebSocket cleaned up")


# ---------------------------------------------------------------------------
# Problem-Aware Discovery — generate keywords people search when they have
# a problem but don't know the product category or proper terminology
# ---------------------------------------------------------------------------

class ProblemAwareRequest(BaseModel):
    seed_keyword: str  # e.g. "ai agent sandbox" or "CageGuard"
    product_description: str = ""  # optional context about what the product does


class ProblemAwareKeyword(BaseModel):
    keyword: str
    category: str  # pain, question, panic, pre_awareness
    estimated_difficulty: int  # 1-10 scale, lower = easier
    estimated_competition: float  # 0.0-1.0
    search_type: str = "problem_aware"


class ProblemAwareResponse(BaseModel):
    keywords: list[ProblemAwareKeyword]
    seed: str
    count: int


class ProblemAwareResearchRequest(BaseModel):
    keywords: list[str]


def _extract_terms(seed: str, description: str) -> dict[str, list[str]]:
    """
    Decompose a seed keyword and optional description into semantic term buckets.
    Returns dict with keys: tool, category, action, threat, thing, problem.
    Each value is a list of term strings.
    """
    words = seed.lower().split()

    # Common tool/product indicators
    tool_indicators = {
        "ai", "agent", "bot", "tool", "app", "software", "platform",
        "cli", "api", "plugin", "extension", "service", "engine",
    }
    # Common category/solution indicators
    category_indicators = {
        "sandbox", "protection", "guard", "shield", "monitor", "filter",
        "blocker", "manager", "tracker", "analyzer", "scanner", "checker",
        "backup", "recovery", "vault", "lock", "firewall", "proxy",
    }
    # Common action verbs
    action_indicators = {
        "protect", "secure", "isolate", "restrict", "limit", "block",
        "prevent", "monitor", "scan", "check", "backup", "recover",
        "encrypt", "filter", "validate", "audit", "control", "manage",
    }
    # Common threat/problem terms
    threat_indicators = {
        "delete", "overwrite", "corrupt", "crash", "break", "leak",
        "expose", "steal", "modify", "destroy", "lose", "damage",
        "hack", "inject", "overflow", "bypass", "exploit", "spam",
    }

    tool_terms: list[str] = []
    category_terms: list[str] = []
    action_terms: list[str] = []
    threat_terms: list[str] = []
    thing_terms: list[str] = []  # what gets affected (files, code, data, etc.)
    problem_terms: list[str] = []  # general problem phrases

    # Extract tool terms — try bigrams first (e.g. "ai agent"), then singles
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i + 1]}"
        if words[i] in tool_indicators or words[i + 1] in tool_indicators:
            tool_terms.append(bigram)
    for w in words:
        if w in tool_indicators:
            tool_terms.append(w)
        if w in category_indicators:
            category_terms.append(w)
        if w in action_indicators:
            action_terms.append(w)

    # If no tool term found, use the full seed as the tool term
    if not tool_terms:
        tool_terms.append(seed.lower())

    # If no category found, use the full seed
    if not category_terms:
        category_terms.append(seed.lower())

    # Extract additional terms from product description
    if description:
        desc_words = re.findall(r'\b[a-z]+\b', description.lower())
        for w in desc_words:
            if w in action_indicators and w not in action_terms:
                action_terms.append(w)
            if w in threat_indicators and w not in threat_terms:
                threat_terms.append(w)

        # Extract noun phrases from description for "thing" terms
        thing_candidates = {"files", "code", "data", "project", "projects",
                           "database", "config", "configuration", "system",
                           "server", "website", "app", "application", "repo",
                           "repository", "folder", "directory", "settings",
                           "credentials", "keys", "secrets", "environment",
                           "documents", "images", "assets", "packages",
                           "dependencies", "modules", "components", "build"}
        for w in desc_words:
            if w in thing_candidates and w not in thing_terms:
                thing_terms.append(w)

    # Defaults if nothing extracted
    if not action_terms:
        action_terms = ["protect", "secure", "manage"]
    if not threat_terms:
        threat_terms = ["delete", "overwrite", "break", "crash", "corrupt"]
    if not thing_terms:
        thing_terms = ["files", "code", "data", "project"]
    if not problem_terms:
        problem_terms = ["not working", "error", "issue", "problem"]

    return {
        "tool": tool_terms,
        "category": category_terms,
        "action": action_terms,
        "threat": threat_terms,
        "thing": thing_terms,
        "problem": problem_terms,
    }


def _generate_problem_aware_keywords(seed: str, description: str) -> list[ProblemAwareKeyword]:
    """
    Generate problem-aware keyword variations from a seed using template expansion.
    Returns 40-80 unique keywords across 4 categories.
    """
    terms = _extract_terms(seed, description)
    tools = terms["tool"]
    categories = terms["category"]
    actions = terms["action"]
    threats = terms["threat"]
    things = terms["thing"]

    results: list[ProblemAwareKeyword] = []
    seen: set[str] = set()

    def _add(keyword: str, category: str, difficulty: int, competition: float) -> None:
        kw_lower = keyword.lower().strip()
        if kw_lower and kw_lower not in seen and len(kw_lower) > 5:
            seen.add(kw_lower)
            results.append(ProblemAwareKeyword(
                keyword=kw_lower,
                category=category,
                estimated_difficulty=difficulty,
                estimated_competition=competition,
            ))

    # ---- Category 1: Pain/Problem phrases ----
    for tool in tools:
        for thing in things:
            _add(f"how to fix {tool} {thing} issues", "pain", 3, 0.05)
            _add(f"{tool} {thing} not working", "pain", 4, 0.08)
            _add(f"{tool} broke my {thing}", "pain", 2, 0.03)
            _add(f"{tool} messed up my {thing}", "pain", 2, 0.02)
            _add(f"{tool} keeps changing my {thing}", "pain", 3, 0.04)
            _add(f"why did {tool} change my {thing}", "pain", 2, 0.03)
        for problem in ["not working", "error", "bug", "issue", "failing"]:
            _add(f"{tool} {problem}", "pain", 5, 0.10)
        _add(f"help with {tool}", "pain", 4, 0.06)
        _add(f"fix {tool} problems", "pain", 3, 0.05)
        _add(f"troubleshoot {tool}", "pain", 4, 0.07)
        _add(f"{tool} keeps failing", "pain", 3, 0.04)
        _add(f"{tool} doesn't work", "pain", 4, 0.06)

    for cat in categories:
        _add(f"{cat} not working", "pain", 4, 0.08)
        _add(f"why does {cat} fail", "pain", 3, 0.04)
        _add(f"problems with {cat}", "pain", 3, 0.05)
        _add(f"{cat} alternatives that work", "pain", 5, 0.12)

    # ---- Category 2: Question phrases ----
    for tool in tools:
        for action in actions:
            _add(f"how to {action} with {tool}", "question", 4, 0.07)
            _add(f"can {tool} {action} my {things[0]}", "question", 3, 0.05)
        _add(f"what is {tool}", "question", 6, 0.15)
        _add(f"how does {tool} work", "question", 5, 0.10)
        _add(f"is {tool} safe", "question", 4, 0.06)
        _add(f"is {tool} safe to use", "question", 3, 0.05)
        _add(f"do i need {tool}", "question", 3, 0.04)
        _add(f"{tool} vs manual", "question", 4, 0.08)
        _add(f"best {tool} settings", "question", 5, 0.10)
        _add(f"how to set up {tool}", "question", 5, 0.09)
        _add(f"{tool} tutorial", "question", 6, 0.12)
        _add(f"{tool} for beginners", "question", 5, 0.08)
        _add(f"how to use {tool} safely", "question", 3, 0.05)

    for cat in categories:
        _add(f"what is {cat}", "question", 6, 0.15)
        _add(f"do i need {cat}", "question", 3, 0.04)
        _add(f"is {cat} worth it", "question", 4, 0.07)
        _add(f"best {cat} tools", "question", 6, 0.15)
        _add(f"free {cat} tools", "question", 5, 0.10)
        _add(f"{cat} explained", "question", 4, 0.06)

    # ---- Category 3: Panic/Emergency phrases ----
    for tool in tools:
        for thing in things:
            _add(f"{tool} deleted my {thing}", "panic", 2, 0.02)
            _add(f"{tool} overwrote my {thing}", "panic", 2, 0.02)
            _add(f"{tool} destroyed my {thing}", "panic", 1, 0.01)
            _add(f"recover {thing} after {tool}", "panic", 3, 0.04)
            _add(f"undo {tool} changes to {thing}", "panic", 3, 0.03)
        _add(f"{tool} crashed", "panic", 3, 0.05)
        _add(f"{tool} won't stop", "panic", 2, 0.02)
        _add(f"how to stop {tool}", "panic", 3, 0.04)
        _add(f"{tool} ran out of control", "panic", 1, 0.01)
        _add(f"{tool} infinite loop", "panic", 2, 0.03)
        _add(f"emergency stop {tool}", "panic", 2, 0.02)

    for threat in threats:
        for thing in things:
            _add(f"recover {thing} after {threat}", "panic", 3, 0.04)
            _add(f"undo {threat} {thing}", "panic", 2, 0.03)

    # ---- Category 4: Pre-awareness natural language ----
    for tool in tools:
        for thing in things:
            _add(f"protect {thing} from {tool}", "pre_awareness", 3, 0.04)
            _add(f"stop {tool} from changing {thing}", "pre_awareness", 2, 0.03)
            _add(f"prevent {tool} from deleting {thing}", "pre_awareness", 2, 0.02)
            _add(f"keep {thing} safe from {tool}", "pre_awareness", 2, 0.03)
            _add(f"{tool} {thing} access control", "pre_awareness", 4, 0.07)
            _add(f"limit {tool} access to {thing}", "pre_awareness", 3, 0.04)
            _add(f"restrict {tool} {thing} permissions", "pre_awareness", 3, 0.05)

        _add(f"is it safe to use {tool}", "pre_awareness", 3, 0.05)
        _add(f"risks of using {tool}", "pre_awareness", 3, 0.04)
        _add(f"dangers of {tool}", "pre_awareness", 3, 0.04)
        _add(f"{tool} safety concerns", "pre_awareness", 3, 0.05)
        _add(f"{tool} security risks", "pre_awareness", 4, 0.06)
        _add(f"should i trust {tool}", "pre_awareness", 2, 0.03)
        _add(f"what can {tool} access", "pre_awareness", 3, 0.04)
        _add(f"{tool} file access risk", "pre_awareness", 3, 0.04)

    for action in actions:
        for thing in things:
            _add(f"how to {action} {thing}", "pre_awareness", 5, 0.10)
            _add(f"best way to {action} {thing}", "pre_awareness", 5, 0.09)
        _add(f"how to {action} automatically", "pre_awareness", 4, 0.07)

    for threat in threats:
        for thing in things:
            _add(f"prevent {threat} {thing}", "pre_awareness", 3, 0.04)
            _add(f"stop {thing} from being {threat}d", "pre_awareness", 2, 0.03)
            _add(f"{thing} keeps getting {threat}d", "pre_awareness", 2, 0.02)

    return results


@router.post("/problem-aware")
async def problem_aware_discovery(req: ProblemAwareRequest):
    """
    Generate problem-aware keywords — what people search when they have a
    problem but don't know the product category or proper terminology.

    This is a template-based generator (no AI calls, no API credits).
    Returns 40-80 unique long-tail keywords across 4 categories:
    pain, question, panic, pre_awareness.
    """
    if not req.seed_keyword.strip():
        raise HTTPException(status_code=400, detail="seed_keyword is required")

    keywords = _generate_problem_aware_keywords(
        req.seed_keyword.strip(),
        req.product_description.strip(),
    )

    return ProblemAwareResponse(
        keywords=keywords,
        seed=req.seed_keyword.strip(),
        count=len(keywords),
    )


@router.post("/problem-aware/research")
async def problem_aware_research(req: ProblemAwareResearchRequest):
    """
    Enrich problem-aware keywords with real DataForSEO volume/difficulty/CPC data.
    Uses bulk Search Volume ($0.005/call, up to 700 kws) + bulk Keyword Difficulty
    ($0.005/call, up to 1000 kws) instead of individual Related Keywords calls ($0.06 each).
    Old approach: 20 keywords = $1.20. New approach: 247 keywords = ~$0.01.
    """
    if not req.keywords:
        raise HTTPException(status_code=400, detail="keywords list is required")

    settings = _get_settings()
    login = settings.get("dataforseo_login", "")
    password = settings.get("dataforseo_password", "")
    location_code = int(settings.get("location_code", "2840"))
    language_code = settings.get("language_code", "en")

    if not login or not password:
        raise HTTPException(
            status_code=400,
            detail="DataForSEO credentials not configured. Set them in SEO Tools settings.",
        )

    # No cap needed — bulk endpoints handle hundreds cheaply
    keywords_to_research = req.keywords
    errors: list[dict[str, str]] = []

    try:
        # 1) Bulk search volume — gets volume, CPC, competition for all keywords at once
        vol_results = await _dataforseo_search_volume(
            keywords_to_research, login, password, location_code, language_code
        )
        vol_lookup: dict[str, dict] = {}
        for r in vol_results:
            vol_lookup[r["keyword"].lower()] = r

        # 2) Bulk keyword difficulty — gets KD scores for all keywords at once
        diff_map = await _dataforseo_bulk_keyword_difficulty(
            keywords_to_research, login, password, location_code, language_code
        )
    except Exception as exc:
        logger.error("PA research bulk API failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"DataForSEO API error: {exc}")

    enriched: list[dict[str, Any]] = []
    for kw in keywords_to_research:
        vol_data = vol_lookup.get(kw.lower(), {})
        difficulty = diff_map.get(kw.lower())

        enriched.append({
            "keyword": kw,
            "volume": vol_data.get("volume", 0),
            "cpc": vol_data.get("cpc", 0.0),
            "competition": vol_data.get("competition", 0.0),
            "competition_level": vol_data.get("competition_level", ""),
            "difficulty": difficulty,
            "trend": vol_data.get("monthly_searches", []),
            "found": bool(vol_data),
        })

    return {
        "results": enriched,
        "keywords": enriched,
        "count": len(enriched),
        "errors": errors,
        "truncated": False,
        "total_requested": len(req.keywords),
    }
