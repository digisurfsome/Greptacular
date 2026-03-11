"""
SEO Keyword Research Tool - Backend Server

Uses DataForSEO Labs API for fine-grained search volume data.
Three search modes: Related Keywords, Keyword Suggestions, or Both (merged).
Two-step enrichment: keyword data + bulk keyword difficulty scores.

Supports:
- DataForSEO Labs API (fine-grained volume, CPC, competition, KD, SERP features)
- Demo mode (works out of the box with sample data)
- CSV import (Ahrefs, Semrush, or generic format)
- CSV export of results
"""

import asyncio
import csv
import io
import json
import logging
import random
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "keywords.db"
INDEX_PATH = Path(__file__).parent / "index.html"

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


# ---------------------------------------------------------------------------
# In-memory search status (for progress reporting)
# ---------------------------------------------------------------------------

# Simple dict keyed by seed keyword to track multi-step search progress.
_search_status: dict[str, dict[str, Any]] = {}


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

    # monthly_searches is typically ordered newest-first from DataForSEO
    # Each item has {"year": 2024, "month": 1, "search_volume": 1234}
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
        "depth": 2,
        "limit": 500,
        "include_serp_info": True,
        "include_seed_keyword": True,
        "include_clickstream_data": False,
    }]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DATAFORSEO_BASE}/dataforseo_labs/google/keyword_suggestions/live",
            json=payload,
            auth=auth,
        )
        resp.raise_for_status()
        data = resp.json()

    return _parse_labs_response(data)


def _parse_labs_response(data: dict) -> list[dict]:
    """Parse the response from related_keywords or keyword_suggestions endpoints."""
    results: list[dict] = []

    for task in data.get("tasks", []):
        if task.get("status_code") != 20000:
            error_msg = task.get("status_message", "Unknown error")
            logger.warning("DataForSEO task error: %s", error_msg)
            continue

        for result in task.get("result", []) or []:
            for item in result.get("items", []) or []:
                kw_data = item.get("keyword_data", {})
                kw_info = kw_data.get("keyword_info", {})
                serp_info = kw_data.get("serp_info", {})

                kw_text = kw_data.get("keyword", "")
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
        # Batch in groups of 1000
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


async def dataforseo_search(
    seed: str, login: str, password: str,
    mode: str, location_code: int, language_code: str,
) -> list[dict]:
    """
    Main search function. Orchestrates the two-step enrichment flow:
    1. Fetch keywords via related_keywords and/or keyword_suggestions
    2. Enrich with bulk keyword difficulty scores

    Args:
        seed: The seed keyword to search for
        login: DataForSEO login email
        password: DataForSEO API password
        mode: 'related', 'suggestions', or 'both'
        location_code: Location code (e.g. 2840 for US)
        language_code: Language code (e.g. 'en')
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

    except Exception as exc:
        _search_status[status_key] = {
            "step": "error",
            "message": f"Error: {exc}",
            "done": True,
            "count": 0,
        }
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
    mode: str = "related"  # 'related', 'suggestions', or 'both'


class SettingsPayload(BaseModel):
    data_source: str = "demo"           # demo | dataforseo
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    openai_api_key: str = ""            # for Content Strategy AI
    location_code: int = 2840
    language_code: str = "en"


class NuggetHuntRequest(BaseModel):
    niches: list[str]  # e.g., ["mortgage", "fitness", "cooking"]
    suffixes: list[str] | None = None  # optional custom suffixes, defaults to built-in list
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
    # Caller already filtered for KD <= kd_max and vol >= vol_min
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
            # Continue to the next combo instead of aborting the whole hunt
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
            # Compute opportunity scores relative to this combo's result set
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
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_demo_data()
    yield


app = FastAPI(title="Keyword Golden Nugget Finder", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the single-file HTML frontend."""
    return HTMLResponse(content=INDEX_PATH.read_text(encoding="utf-8"))


# ---- Settings ----------------------------------------------------------

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


@app.get("/api/settings")
async def get_settings():
    settings = _get_settings()
    masked: dict[str, str] = {}
    for k, v in settings.items():
        if any(secret in k for secret in ("password", "secret", "token", "api_key")):
            masked[k] = "***" + v[-4:] if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked


@app.post("/api/settings")
async def save_settings(payload: SettingsPayload):
    for field_name, value in payload.model_dump().items():
        _save_setting(field_name, str(value))
    return {"status": "ok"}


# ---- API Balance -------------------------------------------------------

@app.get("/api/balance")
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

            # Extract balance from response
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


# ---- Domain Availability Check (RDAP - free, no API key needed) ----------

# TLDs to check, in SEO priority order
DOMAIN_TLDS = [".com", ".net", ".org", ".io", ".co", ".ai", ".app", ".dev", ".us", ".info"]

# RDAP bootstrap - maps TLDs to their RDAP servers
RDAP_BOOTSTRAP_URL = "https://rdap.org/domain/"


async def _check_single_domain(client: httpx.AsyncClient, domain: str) -> dict:
    """Check a single domain via RDAP. Returns availability info."""
    try:
        resp = await client.get(
            f"{RDAP_BOOTSTRAP_URL}{domain}",
            follow_redirects=True,
            timeout=10,
        )
        if resp.status_code == 404:
            # 404 = domain not found in registry = available
            return {"domain": domain, "available": True, "is_premium": False, "premium_price": None}
        elif resp.status_code == 200:
            # 200 = domain exists = taken
            return {"domain": domain, "available": False, "is_premium": False, "premium_price": None}
        else:
            # Other status codes - treat as unknown
            return {"domain": domain, "available": None, "is_premium": False, "premium_price": None, "error": f"HTTP {resp.status_code}"}
    except Exception:
        return {"domain": domain, "available": None, "is_premium": False, "premium_price": None, "error": "timeout"}


@app.get("/api/domain-check")
async def domain_check(keyword: str = Query(...)):
    """Check domain availability across TLDs via free RDAP protocol (no API key needed)."""
    # Build domain name from keyword (remove spaces, lowercase)
    base_domain = keyword.strip().lower().replace(" ", "").replace("-", "")
    if not base_domain:
        return {"error": "Invalid keyword", "domains": []}

    domain_list = [base_domain + tld for tld in DOMAIN_TLDS]

    try:
        async with httpx.AsyncClient() as client:
            # Check all TLDs concurrently for speed
            tasks = [_check_single_domain(client, domain) for domain in domain_list]
            results = await asyncio.gather(*tasks)

        return {"keyword": keyword, "base_domain": base_domain, "domains": list(results)}

    except Exception as exc:
        return {"error": f"Domain check error: {exc}", "domains": []}


@app.post("/api/domain-check-bulk")
async def domain_check_bulk(payload: dict):
    """Check domain availability for a list of keywords across specified TLDs."""
    keywords = payload.get("keywords", [])
    if not keywords:
        return {"results": {}}

    # Accept custom TLD list from frontend, default to .com/.net/.org
    check_tlds = payload.get("tlds", [".com", ".net", ".org"])
    # Sanitize: ensure they start with dot, limit to 10 TLDs
    check_tlds = [t if t.startswith(".") else "." + t for t in check_tlds][:10]

    # Limit keywords based on TLD count to keep RDAP calls reasonable
    max_kw = max(5, 50 // len(check_tlds))
    keywords = keywords[:max_kw]

    async with httpx.AsyncClient() as client:
        tasks = []
        for kw in keywords:
            base = kw.strip().lower().replace(" ", "").replace("-", "")
            for tld in check_tlds:
                tasks.append((kw, tld, _check_single_domain(client, base + tld)))

        gathered = await asyncio.gather(*[t[2] for t in tasks])
        results: dict[str, dict] = {}
        for (kw, tld, _), result in zip(tasks, gathered):
            if kw not in results:
                results[kw] = {}
            results[kw][tld] = {
                "domain": result["domain"],
                "available": result["available"],
            }

    return {"results": results}


# ---- SERP Preview (DataForSEO) ------------------------------------------

@app.get("/api/serp-preview")
async def serp_preview(keyword: str = Query(...)):
    """Fetch top 10 Google SERP results for a keyword. Costs ~$0.002 per call."""
    settings = _get_settings()
    login = settings.get("dataforseo_login", "")
    password = settings.get("dataforseo_password", "")

    if not login or not password:
        return {"error": "DataForSEO credentials not configured. Go to Settings.", "results": []}

    location_code = int(settings.get("location_code", "2840"))
    language_code = settings.get("language_code", "en")

    # Build the exact match domain from keyword for comparison
    base_domain = keyword.strip().lower().replace(" ", "").replace("-", "")

    payload = [{
        "keyword": keyword,
        "location_code": location_code,
        "language_code": language_code,
        "depth": 10,
        "device": "desktop",
    }]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DATAFORSEO_BASE}/serp/google/organic/live",
                json=payload,
                auth=(login, password),
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        has_exact_match = False

        for task in data.get("tasks", []):
            if task.get("status_code") != 20000:
                error_msg = task.get("status_message", "Unknown error")
                return {"error": f"DataForSEO: {error_msg}", "results": []}

            for result in task.get("result", []) or []:
                for item in result.get("items", []) or []:
                    item_type = item.get("type", "")
                    if item_type != "organic":
                        continue

                    domain = item.get("domain", "")
                    url = item.get("url", "")

                    # Check if this domain is an exact match for the keyword
                    domain_base = domain.split(".")[0].lower() if domain else ""
                    is_exact_match = domain_base == base_domain
                    if is_exact_match:
                        has_exact_match = True

                    results.append({
                        "rank": item.get("rank_absolute", 0),
                        "domain": domain,
                        "title": item.get("title", ""),
                        "url": url,
                        "description": item.get("description", ""),
                        "is_exact_match": is_exact_match,
                    })

        # EMD opportunity analysis
        emd_opportunity = "none"
        if not has_exact_match:
            emd_opportunity = "high"  # No exact match domain in top 10 = big opportunity

        return {
            "keyword": keyword,
            "base_domain": base_domain,
            "results": results,
            "has_exact_match": has_exact_match,
            "emd_opportunity": emd_opportunity,
            "cost": 0.002,
        }

    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code == 402:
            return {"error": "Insufficient DataForSEO balance", "results": []}
        return {"error": f"DataForSEO API error: {code}", "results": []}
    except Exception as exc:
        return {"error": f"SERP preview error: {exc}", "results": []}


# ---- Search status (polling) -------------------------------------------

@app.get("/api/search-status")
async def get_search_status(seed: str = Query("")):
    """Get the current status of an ongoing search."""
    status_key = seed.strip().lower()
    status = _search_status.get(status_key)
    if status is None:
        return {"step": "idle", "message": "", "done": True}
    return status


# ---- Search ------------------------------------------------------------

@app.post("/api/search")
async def search_keywords(req: SearchRequest):
    """Search for keywords by seed. Uses configured data source."""
    seed = req.seed_keyword.strip().lower()
    if not seed:
        return {"error": "Seed keyword is required", "keywords": []}

    mode = req.mode if req.mode in ("related", "suggestions", "both") else "related"
    settings = _get_settings()
    source = settings.get("data_source", "demo")

    new_keywords: list[dict] = []

    if source == "dataforseo":
        login = settings.get("dataforseo_login", "")
        password = settings.get("dataforseo_password", "")
        if not login or not password:
            return {"error": "DataForSEO credentials not configured", "keywords": []}

        location_code = int(settings.get("location_code", "2840"))
        language_code = settings.get("language_code", "en")

        try:
            new_keywords = await dataforseo_search(
                seed, login, password, mode, location_code, language_code
            )
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 401:
                return {"error": "Authentication failed. Check your DataForSEO credentials.", "keywords": []}
            elif code == 403:
                return {"error": "Access denied. Your account may not have access to this endpoint.", "keywords": []}
            elif code == 402:
                return {"error": "Insufficient balance. Please top up your DataForSEO account.", "keywords": []}
            elif code == 429:
                return {"error": "Rate limit exceeded. Please wait a moment and try again.", "keywords": []}
            return {"error": f"DataForSEO API error: {code}", "keywords": []}
        except Exception as exc:
            return {"error": f"DataForSEO error: {exc}", "keywords": []}

    else:
        # Demo mode
        new_keywords = _generate_demo_search_results(seed)

    # Persist to database
    if new_keywords:
        _upsert_keywords(new_keywords, source=source, seed=seed)

    # Return all keywords matching the seed
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT keyword, volume, difficulty, cpc, competition,
                      competition_level, monthly_searches, serp_features,
                      trend, source
               FROM keywords WHERE seed_keyword = ? ORDER BY volume DESC""",
            (seed,),
        ).fetchall()
        result = _rows_to_dicts(rows)
        result = compute_opportunity_scores(result)
        return {"keywords": result, "count": len(result)}
    finally:
        conn.close()


def _rows_to_dicts(rows: list) -> list[dict]:
    """Convert sqlite Row objects to dicts, parsing JSON fields."""
    result = []
    for r in rows:
        d = dict(r)
        # Parse JSON text fields
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


# ---- CSV Import --------------------------------------------------------

@app.post("/api/import-csv")
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


# ---- CSV Export --------------------------------------------------------

@app.get("/api/export-csv")
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

    # Build CSV in memory
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


# ---- Keywords list (with filtering) -----------------------------------

@app.get("/api/keywords")
async def get_keywords(
    difficulty_min: int = Query(0, ge=0, le=100),
    difficulty_max: int = Query(100, ge=0, le=100),
    volume_min: int = Query(0, ge=0),
    volume_max: int = Query(10_000_000, ge=0),
    sort_by: str = Query("volume"),
    sort_order: str = Query("desc"),
):
    """Get all cached keywords with filtering and sorting."""
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
        rows = conn.execute(
            """SELECT keyword, volume, difficulty, cpc, competition,
                      competition_level, monthly_searches, serp_features,
                      trend, source
               FROM keywords
               WHERE difficulty >= ? AND difficulty <= ?
                 AND volume >= ? AND volume <= ?
               ORDER BY volume DESC""",
            (difficulty_min, difficulty_max, volume_min, volume_max),
        ).fetchall()
        result = _rows_to_dicts(rows)
        result = compute_opportunity_scores(result)

        # Sort (opportunity_score is computed, so we sort in Python)
        reverse = sort_order == "desc"
        try:
            result.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=reverse)
        except TypeError:
            result.sort(key=lambda r: str(r.get(sort_by, "")), reverse=reverse)

        return {"keywords": result, "count": len(result)}
    finally:
        conn.close()


# ---- Segments ----------------------------------------------------------

@app.get("/api/segments")
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


# ---- Clear database ----------------------------------------------------

@app.post("/api/clear")
async def clear_keywords():
    """Clear all keywords from the database."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM keywords")
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Nugget Hunter API endpoints
# ---------------------------------------------------------------------------


@app.post("/api/nugget-hunt/start")
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

    # Launch the pipeline as a background task
    task = asyncio.create_task(_run_nugget_hunt(hunt_id))
    _active_hunts[hunt_id] = task

    return {"hunt_id": hunt_id, "status": "running", "total_combos": total_combos}


@app.get("/api/nugget-hunt/status")
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
        # Parse JSON fields for the response
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


@app.post("/api/nugget-hunt/cancel")
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

    # Signal cancellation; the pipeline checks this between combos
    _cancelled_hunts.add(hunt_id)

    # If the task is still in _active_hunts, let it self-cancel on the next
    # iteration.  If it somehow finished already, mark cancelled directly.
    if hunt_id not in _active_hunts:
        _update_hunt_status(hunt_id, "cancelled")

    return {"status": "cancelling", "hunt_id": hunt_id}


@app.get("/api/nugget-hunt/results")
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
            # Parse JSON text fields
            for json_field in ("monthly_searches", "serp_features"):
                val = d.get(json_field, "[]")
                if isinstance(val, str):
                    try:
                        d[json_field] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        d[json_field] = []
            result.append(d)

        # Sort in Python (opportunity_score may not be in SQL sort)
        reverse = sort_order == "desc"
        try:
            result.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=reverse)
        except TypeError:
            result.sort(key=lambda r: str(r.get(sort_by, "")), reverse=reverse)

        return {"nuggets": result, "count": len(result)}
    finally:
        conn.close()


@app.get("/api/nugget-hunt/history")
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


@app.get("/api/nugget-hunt/export-csv")
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


@app.delete("/api/nugget-hunt/delete")
async def delete_nugget_hunt(hunt_id: int = Query(...)):
    """Delete a hunt and all its associated nuggets."""
    # Cancel if still running
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


# ---------------------------------------------------------------------------
# Content Strategy Generator (AI-powered, uses OpenAI API)
# ---------------------------------------------------------------------------

CONTENT_STRATEGY_PROMPT = """You are an expert B2B SaaS SEO strategist. I'll give you ONE URL (a SaaS homepage). Your job is to generate a content map focused on fast wins first (comparisons, alternatives, listicles, integrations, free tools), then pillars/clusters for compounding growth.

Rules:
- Analyze the site (what they sell, who they serve, competitors, integrations, features)
- Infer realistic competitors and "vs/alternatives" targets based on category
- Assume B2B SaaS ICP unless clearly otherwise
- If something is unclear, make best-effort assumptions and label them
- EVERY listicle title MUST start with a number between 5 and 7 (only "5", "6", or "7")
- Focus on HIGH BUYING INTENT keywords — people ready to buy, switch, or compare

You MUST return valid JSON with this exact structure:
{
  "snapshot": {
    "what_they_sell": "...",
    "icp": "...",
    "primary_cta": "...",
    "pricing_motion": "...",
    "differentiators": ["...", "..."]
  },
  "comparisons": [
    {"title": "Product vs Competitor", "target_keyword": "product vs competitor", "priority": "P0", "notes": "..."}
  ],
  "alternatives": [
    {"title": "Top Competitor Alternatives", "target_keyword": "competitor alternatives", "priority": "P0", "notes": "..."}
  ],
  "listicles": [
    {"title": "7 Best Tools for X", "target_keyword": "best tools for x", "notes": "..."}
  ],
  "integrations": [
    {"title": "Product + Integration Name", "target_keyword": "product integration name", "notes": "..."}
  ],
  "free_tools": [
    {"title": "Free X Calculator", "target_keyword": "free x calculator", "tool_concept": "...", "output": "...", "cta": "..."}
  ],
  "pillars": [
    {
      "pillar": "Pillar Name",
      "clusters": [
        {"title": "Cluster Article Title", "target_keyword": "target keyword", "intent": "informational|commercial|transactional"}
      ]
    }
  ]
}

Return ONLY valid JSON. No markdown, no code fences, no explanations outside the JSON.

URL: """


@app.post("/api/content-strategy")
async def content_strategy(payload: dict):
    """Generate a content strategy for a SaaS URL using AI."""
    url = payload.get("url", "").strip()
    if not url:
        return {"error": "URL is required"}

    settings = _get_settings()
    api_key = settings.get("openai_api_key", "")
    if not api_key:
        return {"error": "OpenAI API key not configured. Go to Settings to add it."}

    prompt = CONTENT_STRATEGY_PROMPT + url

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Strip markdown fences if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()

            strategy = json.loads(content)
            return {"strategy": strategy}

    except httpx.HTTPStatusError as e:
        return {"error": f"OpenAI API error: {e.response.status_code} - {e.response.text[:200]}"}
    except json.JSONDecodeError:
        return {"error": "AI returned invalid JSON. Try again.", "raw": content[:500]}
    except Exception as e:
        return {"error": f"Failed: {str(e)}"}


@app.post("/api/content-strategy/research-keywords")
async def content_strategy_research(payload: dict):
    """Take generated content ideas and research their keywords via DataForSEO."""
    keywords = payload.get("keywords", [])
    if not keywords:
        return {"results": []}

    settings = _get_settings()
    login = settings.get("dataforseo_login", "")
    password = settings.get("dataforseo_password", "")
    location_code = int(settings.get("location_code", "2840"))
    language_code = settings.get("language_code", "en")

    if not login or not password:
        # Return demo data
        results = []
        for kw in keywords[:50]:
            results.append({
                "keyword": kw,
                "volume": random.randint(100, 5000),
                "difficulty": random.randint(5, 40),
                "cpc": round(random.uniform(0.5, 15.0), 2),
                "competition": round(random.uniform(0.1, 0.8), 2),
            })
        return {"results": results}

    # Use DataForSEO bulk keyword data
    auth = (login, password)
    all_results = []

    for i in range(0, len(keywords), 50):
        batch = keywords[i : i + 50]
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{DATAFORSEO_BASE}/keywords_data/google_ads/search_volume/live",
                    auth=auth,
                    json=[{
                        "keywords": batch,
                        "location_code": location_code,
                        "language_code": language_code,
                    }],
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("tasks") and data["tasks"][0].get("result"):
                    for item in data["tasks"][0]["result"]:
                        all_results.append({
                            "keyword": item.get("keyword", ""),
                            "volume": item.get("search_volume", 0) or 0,
                            "difficulty": 0,
                            "cpc": item.get("cpc", 0) or 0,
                            "competition": item.get("competition", 0) or 0,
                        })
        except Exception as e:
            logger.error("DataForSEO keyword research failed: %s", e)

    return {"results": all_results}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
