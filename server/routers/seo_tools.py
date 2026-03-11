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
import os
import random
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

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
    location_code: int = 2840
    language_code: str = "en"


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
        if any(secret in k for secret in ("password", "secret", "token")):
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


# ---- Search -----------------------------------------------------------------

@router.post("/search")
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
# AI-Powered Keyword Analysis WebSocket
# ===========================================================================
#
# Follows the same pattern as the assistant chat WebSocket
# (server/routers/assistant_chat.py) but scoped for SEO keyword analysis.
# Uses subscription auth (force_subscription=True) so it runs on the
# Claude subscription rather than consuming API credits.
# ===========================================================================

# Read-only built-in tools the SEO analyst can use
_SEO_BUILTIN_TOOLS = [
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
]

# Module-level session store: one active session at a time for simplicity
_seo_chat_session: Optional["_SEOChatSession"] = None


def _get_seo_system_prompt(model_id: str = "") -> str:
    """Build the system prompt for the SEO keyword analyst."""
    # Summarise the current keyword database for context
    db_summary = ""
    try:
        conn = get_db()
        try:
            total = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
            if total > 0:
                low_kd = conn.execute(
                    "SELECT COUNT(*) FROM keywords WHERE difficulty <= 10"
                ).fetchone()[0]
                avg_vol = conn.execute(
                    "SELECT AVG(volume) FROM keywords"
                ).fetchone()[0] or 0
                db_summary = (
                    f"\n## Current Keyword Database\n"
                    f"- Total keywords: {total}\n"
                    f"- Low-KD keywords (difficulty <= 10): {low_kd}\n"
                    f"- Average search volume: {int(avg_vol)}\n"
                )
        finally:
            conn.close()
    except Exception:
        pass

    model_block = ""
    if model_id:
        model_block = (
            f"\n## Your Model Identity\n\n"
            f"You are running as model **{model_id}**.\n"
        )

    return f"""You are an expert SEO keyword analyst and content strategist.

You help users analyze keyword data, identify content opportunities, develop
SEO strategies, and make data-driven decisions about which keywords to target.

## Your Capabilities

- Analyze keyword difficulty, search volume, and competition metrics
- Identify "golden nugget" keywords (low difficulty, decent volume)
- Suggest content strategies based on keyword clusters
- Evaluate SERP feature opportunities (featured snippets, PAA, etc.)
- Recommend keyword targeting priorities
- Analyze trends and seasonality patterns
- Compare keyword sets and identify gaps
- Use WebSearch to research current SERP landscapes for keywords
- Use WebFetch to analyze competitor pages ranking for target keywords

## Guidelines

- Always ground your analysis in the actual data when available
- Be specific with recommendations — include the keyword, volume, and difficulty
- When suggesting content, explain WHY a keyword is a good target
- Consider search intent (informational, transactional, navigational)
- Flag any risks (e.g., YMYL topics, high-authority competitors)
- Use tables and structured formatting for data comparisons
{db_summary}{model_block}"""


class _SEOChatSession:
    """
    Lightweight chat session for AI-powered SEO analysis.

    Wraps a ClaudeSDKClient with subscription auth and read-only tools.
    Streams responses back as async generator chunks matching the protocol
    used by the assistant chat.
    """

    def __init__(self) -> None:
        self.client: Optional[Any] = None
        self._client_entered: bool = False

    async def start(self) -> AsyncGenerator[dict, None]:
        """Initialise the Claude client and yield a ready event."""
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        system_cli = shutil.which("claude")

        try:
            from registry import DEFAULT_MODEL, get_effective_sdk_env

            # Force subscription auth so this does not consume API credits
            sdk_env = get_effective_sdk_env(force_subscription=True)
        except Exception as e:
            logger.exception("Failed to load SDK environment for SEO chat")
            yield {"type": "error", "content": f"Failed to load configuration: {e}"}
            return

        model = (
            sdk_env.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_MODEL)
        )

        system_prompt = _get_seo_system_prompt(model_id=model)

        # Write the system prompt to a scratch CLAUDE.md so the SDK reads it
        # via setting_sources=["project"] without polluting any real project.
        scratch_dir = Path.home() / ".autoforge" / ".seo_chat_scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        claude_md = scratch_dir / "CLAUDE.md"
        claude_md.write_text(system_prompt, encoding="utf-8")

        # Minimal security settings — read-only, no bash
        settings_data = {
            "sandbox": {"enabled": False},
            "permissions": {
                "defaultMode": "bypassPermissions",
                "allow": _SEO_BUILTIN_TOOLS,
            },
        }
        settings_file = scratch_dir / "settings.json"
        settings_file.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")

        try:
            self.client = ClaudeSDKClient(
                options=ClaudeAgentOptions(
                    model=model,
                    cli_path=system_cli,
                    setting_sources=["project"],
                    allowed_tools=_SEO_BUILTIN_TOOLS,
                    permission_mode="bypassPermissions",
                    max_turns=100,
                    cwd=str(scratch_dir.resolve()),
                    settings=str(settings_file.resolve()),
                    env=sdk_env,
                )
            )
            await self.client.__aenter__()
            self._client_entered = True
            logger.info("SEO chat session started (model=%s)", model)
        except Exception as e:
            logger.exception("Failed to create Claude client for SEO chat")
            yield {"type": "error", "content": f"Failed to initialize SEO analyst: {e}"}
            return

        greeting = (
            "Hello! I'm your SEO keyword analyst. I can help you analyze keywords, "
            "identify content opportunities, and develop targeting strategies. "
            "What would you like to explore?"
        )
        yield {"type": "text", "content": greeting}
        yield {"type": "response_done"}

    async def send_message(self, user_message: str) -> AsyncGenerator[dict, None]:
        """Send a user message and stream the response."""
        if not self.client:
            yield {"type": "error", "content": "Session not initialized. Send 'start' first."}
            return

        try:
            async for chunk in self._query_claude(user_message):
                yield chunk
            yield {"type": "response_done"}
        except Exception as e:
            logger.exception("Error during SEO chat query")
            yield {"type": "error", "content": f"Error: {e}"}

    async def _query_claude(self, message: str) -> AsyncGenerator[dict, None]:
        """Internal method to query Claude and stream responses."""
        if not self.client:
            return

        await self.client.query(message)

        async for msg in self.client.receive_response():
            msg_type = type(msg).__name__

            # Skip SDK informational events
            if msg_type in ("RateLimitEvent", "rate_limit_event"):
                continue

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        text = block.text
                        if text:
                            yield {"type": "text", "content": text}

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        tool_name = block.name
                        tool_input = getattr(block, "input", {})
                        yield {
                            "type": "tool_call",
                            "tool": tool_name,
                            "input": tool_input,
                        }

            elif msg_type == "ResultMessage" and hasattr(msg, "usage"):
                usage = msg.usage
                if usage:
                    yield {
                        "type": "token_usage",
                        "input_tokens": getattr(usage, "input_tokens", 0),
                        "output_tokens": getattr(usage, "output_tokens", 0),
                    }

    async def cleanup(self) -> None:
        """Clean up the Claude client."""
        if self.client and self._client_entered:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_entered = False
            self.client = None


@router.websocket("/ws")
async def seo_chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for AI-powered SEO keyword analysis.

    Uses subscription auth (force_subscription=True) so conversations
    run on the Claude subscription rather than consuming API credits.

    Client -> Server:
    - {"type": "start"} - Create a new analysis session
    - {"type": "message", "content": "..."} - Send user message
    - {"type": "ping"} - Keep-alive ping

    Server -> Client:
    - {"type": "text", "content": "..."} - Text chunk from Claude
    - {"type": "tool_call", "tool": "...", "input": {...}} - Tool being called
    - {"type": "token_usage", "input_tokens": int, "output_tokens": int} - Token usage
    - {"type": "response_done"} - Response complete
    - {"type": "error", "content": "..."} - Error message
    - {"type": "pong"} - Keep-alive pong
    """
    global _seo_chat_session

    await websocket.accept()
    logger.info("SEO chat WebSocket connected")

    session: Optional[_SEOChatSession] = None

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                logger.debug("SEO chat received message type: %s", msg_type)

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                elif msg_type == "start":
                    # Clean up any previous session
                    if _seo_chat_session is not None:
                        await _seo_chat_session.cleanup()
                        _seo_chat_session = None

                    session = _SEOChatSession()
                    _seo_chat_session = session

                    try:
                        async for chunk in session.start():
                            await websocket.send_json(chunk)
                    except Exception as e:
                        logger.exception("Error starting SEO chat session")
                        await websocket.send_json({
                            "type": "error",
                            "content": f"Failed to start session: {e}",
                        })

                elif msg_type == "message":
                    if session is None:
                        session = _seo_chat_session
                    if session is None:
                        await websocket.send_json({
                            "type": "error",
                            "content": "No active session. Send 'start' first.",
                        })
                        continue

                    user_content = message.get("content", "").strip()
                    if not user_content:
                        await websocket.send_json({
                            "type": "error",
                            "content": "Empty message",
                        })
                        continue

                    async for chunk in session.send_message(user_content):
                        await websocket.send_json(chunk)

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
        logger.info("SEO chat WebSocket disconnected")
    except Exception:
        logger.exception("SEO chat WebSocket error")
    finally:
        # Clean up session on disconnect
        if session is not None:
            await session.cleanup()
            if _seo_chat_session is session:
                _seo_chat_session = None
