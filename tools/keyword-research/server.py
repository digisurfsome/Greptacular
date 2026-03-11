"""
SEO Keyword Research Tool - Backend Server

A FastAPI server that helps find "golden nugget" keywords:
high search volume but low competition/difficulty.

Supports multiple data sources:
- Demo mode (works out of the box)
- DataForSEO API (volume + keyword difficulty)
- Google Ads API (volume + PPC competition)
- CSV import (Ahrefs, Semrush, or generic format)
"""

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
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "keywords.db"
INDEX_PATH = Path(__file__).parent / "index.html"


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
                keyword     TEXT NOT NULL,
                volume      INTEGER DEFAULT 0,
                difficulty  INTEGER DEFAULT 0,
                cpc         REAL DEFAULT 0.0,
                competition REAL DEFAULT 0.0,
                source      TEXT DEFAULT 'demo',
                seed_keyword TEXT DEFAULT '',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Demo data generator
# ---------------------------------------------------------------------------

# Realistic seed data organised by niche so the output feels genuine.
_DEMO_KEYWORDS: list[dict[str, Any]] = [
    # Calculators (generally mid-high volume, mixed difficulty)
    {"keyword": "mortgage calculator", "volume": 49500, "difficulty": 78, "cpc": 3.40},
    {"keyword": "bmi calculator", "volume": 40500, "difficulty": 62, "cpc": 1.20},
    {"keyword": "calorie calculator", "volume": 33100, "difficulty": 55, "cpc": 0.90},
    {"keyword": "tip calculator", "volume": 27100, "difficulty": 35, "cpc": 0.60},
    {"keyword": "gpa calculator", "volume": 22200, "difficulty": 42, "cpc": 0.80},
    {"keyword": "body fat calculator", "volume": 18100, "difficulty": 48, "cpc": 1.10},
    {"keyword": "age calculator", "volume": 14800, "difficulty": 28, "cpc": 0.30},
    {"keyword": "pregnancy due date calculator", "volume": 12100, "difficulty": 52, "cpc": 1.50},
    {"keyword": "subnet calculator", "volume": 9900, "difficulty": 22, "cpc": 0.70},
    {"keyword": "percentage calculator", "volume": 8100, "difficulty": 38, "cpc": 0.40},
    {"keyword": "compound interest calculator", "volume": 6600, "difficulty": 45, "cpc": 2.80},
    {"keyword": "loan calculator", "volume": 40500, "difficulty": 72, "cpc": 4.20},
    {"keyword": "paycheck calculator", "volume": 33100, "difficulty": 58, "cpc": 2.10},
    {"keyword": "tax calculator", "volume": 27100, "difficulty": 65, "cpc": 3.50},
    {"keyword": "ovulation calculator", "volume": 22200, "difficulty": 50, "cpc": 1.30},
    {"keyword": "concrete calculator", "volume": 14800, "difficulty": 18, "cpc": 0.90},
    {"keyword": "tile calculator", "volume": 8100, "difficulty": 12, "cpc": 0.70},
    {"keyword": "mulch calculator", "volume": 6600, "difficulty": 8, "cpc": 0.50},
    {"keyword": "gravel calculator", "volume": 5400, "difficulty": 10, "cpc": 0.60},
    {"keyword": "drywall calculator", "volume": 4400, "difficulty": 5, "cpc": 0.45},
    {"keyword": "roofing calculator", "volume": 3600, "difficulty": 15, "cpc": 2.30},
    {"keyword": "deck cost calculator", "volume": 2900, "difficulty": 7, "cpc": 1.80},
    {"keyword": "fence calculator", "volume": 2400, "difficulty": 4, "cpc": 1.20},
    {"keyword": "wallpaper calculator", "volume": 1900, "difficulty": 3, "cpc": 0.35},
    {"keyword": "paint calculator", "volume": 3600, "difficulty": 9, "cpc": 0.55},

    # Marketing tools
    {"keyword": "email subject line generator", "volume": 5400, "difficulty": 25, "cpc": 1.80},
    {"keyword": "headline analyzer", "volume": 4400, "difficulty": 30, "cpc": 1.50},
    {"keyword": "meta description generator", "volume": 3600, "difficulty": 18, "cpc": 1.20},
    {"keyword": "blog title generator", "volume": 6600, "difficulty": 22, "cpc": 1.00},
    {"keyword": "hashtag generator", "volume": 8100, "difficulty": 32, "cpc": 0.80},
    {"keyword": "utm builder", "volume": 2900, "difficulty": 15, "cpc": 0.60},
    {"keyword": "social media post generator", "volume": 3600, "difficulty": 28, "cpc": 1.40},
    {"keyword": "ad copy generator", "volume": 2400, "difficulty": 20, "cpc": 2.50},
    {"keyword": "landing page builder free", "volume": 4400, "difficulty": 45, "cpc": 5.80},
    {"keyword": "email template builder", "volume": 2900, "difficulty": 35, "cpc": 3.20},
    {"keyword": "seo title generator", "volume": 1900, "difficulty": 12, "cpc": 0.90},
    {"keyword": "keyword density checker", "volume": 2400, "difficulty": 16, "cpc": 0.70},
    {"keyword": "readability score checker", "volume": 1600, "difficulty": 14, "cpc": 0.50},
    {"keyword": "word counter online", "volume": 9900, "difficulty": 20, "cpc": 0.25},
    {"keyword": "character counter", "volume": 6600, "difficulty": 18, "cpc": 0.20},

    # AI tools
    {"keyword": "ai prompt generator", "volume": 12100, "difficulty": 35, "cpc": 1.80},
    {"keyword": "chatbot builder", "volume": 9900, "difficulty": 55, "cpc": 4.50},
    {"keyword": "ai writing assistant", "volume": 8100, "difficulty": 60, "cpc": 3.80},
    {"keyword": "ai image generator free", "volume": 33100, "difficulty": 52, "cpc": 0.90},
    {"keyword": "ai logo maker", "volume": 14800, "difficulty": 42, "cpc": 2.20},
    {"keyword": "text to speech free", "volume": 22200, "difficulty": 48, "cpc": 0.70},
    {"keyword": "ai resume builder", "volume": 12100, "difficulty": 50, "cpc": 3.50},
    {"keyword": "ai essay writer", "volume": 18100, "difficulty": 45, "cpc": 1.20},
    {"keyword": "ai code generator", "volume": 9900, "difficulty": 38, "cpc": 2.00},
    {"keyword": "ai voice cloner free", "volume": 6600, "difficulty": 30, "cpc": 0.80},
    {"keyword": "ai background remover", "volume": 14800, "difficulty": 40, "cpc": 0.60},
    {"keyword": "ai video generator", "volume": 8100, "difficulty": 42, "cpc": 1.50},
    {"keyword": "ai music generator", "volume": 5400, "difficulty": 35, "cpc": 0.90},
    {"keyword": "ai paraphrasing tool", "volume": 12100, "difficulty": 38, "cpc": 0.70},
    {"keyword": "ai grammar checker", "volume": 6600, "difficulty": 55, "cpc": 1.80},

    # Golden nuggets (low difficulty, decent volume) -- the ones users want to find
    {"keyword": "cubic yards calculator", "volume": 4400, "difficulty": 2, "cpc": 0.35},
    {"keyword": "board foot calculator", "volume": 3600, "difficulty": 1, "cpc": 0.40},
    {"keyword": "stair calculator", "volume": 2900, "difficulty": 3, "cpc": 0.50},
    {"keyword": "asphalt calculator", "volume": 2400, "difficulty": 0, "cpc": 0.45},
    {"keyword": "rebar calculator", "volume": 1900, "difficulty": 0, "cpc": 0.55},
    {"keyword": "sand calculator", "volume": 2400, "difficulty": 1, "cpc": 0.30},
    {"keyword": "paver calculator", "volume": 3600, "difficulty": 4, "cpc": 0.65},
    {"keyword": "insulation calculator", "volume": 2900, "difficulty": 3, "cpc": 0.75},
    {"keyword": "wire gauge calculator", "volume": 1600, "difficulty": 0, "cpc": 0.35},
    {"keyword": "voltage drop calculator", "volume": 2400, "difficulty": 2, "cpc": 0.40},
    {"keyword": "air duct calculator", "volume": 1300, "difficulty": 0, "cpc": 0.50},
    {"keyword": "heat load calculator", "volume": 1900, "difficulty": 1, "cpc": 0.60},
    {"keyword": "cfm calculator", "volume": 1600, "difficulty": 2, "cpc": 0.45},
    {"keyword": "pipe size calculator", "volume": 2400, "difficulty": 3, "cpc": 0.55},
    {"keyword": "bolt torque calculator", "volume": 1300, "difficulty": 1, "cpc": 0.30},
    {"keyword": "gear ratio calculator", "volume": 2900, "difficulty": 5, "cpc": 0.35},
    {"keyword": "pulley calculator", "volume": 1600, "difficulty": 2, "cpc": 0.25},
    {"keyword": "spring constant calculator", "volume": 1300, "difficulty": 0, "cpc": 0.20},
    {"keyword": "ohms law calculator", "volume": 3600, "difficulty": 4, "cpc": 0.30},
    {"keyword": "resistor color code calculator", "volume": 2900, "difficulty": 3, "cpc": 0.25},

    # Medium difficulty, varied volume
    {"keyword": "free invoice generator", "volume": 14800, "difficulty": 38, "cpc": 2.80},
    {"keyword": "qr code generator free", "volume": 33100, "difficulty": 42, "cpc": 0.50},
    {"keyword": "barcode generator", "volume": 9900, "difficulty": 28, "cpc": 0.60},
    {"keyword": "color palette generator", "volume": 8100, "difficulty": 25, "cpc": 0.40},
    {"keyword": "password generator", "volume": 18100, "difficulty": 35, "cpc": 0.30},
    {"keyword": "lorem ipsum generator", "volume": 6600, "difficulty": 22, "cpc": 0.15},
    {"keyword": "random name generator", "volume": 12100, "difficulty": 30, "cpc": 0.20},
    {"keyword": "meme generator", "volume": 22200, "difficulty": 50, "cpc": 0.25},
    {"keyword": "gif maker", "volume": 9900, "difficulty": 40, "cpc": 0.35},
    {"keyword": "pdf to word converter", "volume": 27100, "difficulty": 55, "cpc": 0.80},
    {"keyword": "image compressor", "volume": 8100, "difficulty": 32, "cpc": 0.30},
    {"keyword": "video compressor online", "volume": 6600, "difficulty": 28, "cpc": 0.40},
    {"keyword": "json formatter", "volume": 9900, "difficulty": 15, "cpc": 0.20},
    {"keyword": "cron expression generator", "volume": 4400, "difficulty": 8, "cpc": 0.30},
    {"keyword": "regex tester", "volume": 6600, "difficulty": 18, "cpc": 0.25},
    {"keyword": "base64 encoder", "volume": 3600, "difficulty": 10, "cpc": 0.15},
    {"keyword": "html to markdown converter", "volume": 2400, "difficulty": 6, "cpc": 0.20},
    {"keyword": "svg to png converter", "volume": 4400, "difficulty": 12, "cpc": 0.25},
    {"keyword": "yaml validator", "volume": 1900, "difficulty": 5, "cpc": 0.15},
    {"keyword": "css minifier", "volume": 2900, "difficulty": 8, "cpc": 0.10},

    # High competition (hard to rank for)
    {"keyword": "website builder", "volume": 49500, "difficulty": 90, "cpc": 8.50},
    {"keyword": "crm software", "volume": 27100, "difficulty": 85, "cpc": 12.00},
    {"keyword": "project management tool", "volume": 22200, "difficulty": 82, "cpc": 9.80},
    {"keyword": "accounting software", "volume": 18100, "difficulty": 88, "cpc": 11.50},
    {"keyword": "email marketing software", "volume": 14800, "difficulty": 80, "cpc": 7.20},
    {"keyword": "web hosting", "volume": 40500, "difficulty": 92, "cpc": 15.00},
    {"keyword": "vpn service", "volume": 33100, "difficulty": 88, "cpc": 6.50},
    {"keyword": "antivirus software", "volume": 22200, "difficulty": 85, "cpc": 5.80},
    {"keyword": "online course platform", "volume": 9900, "difficulty": 75, "cpc": 8.90},
    {"keyword": "ecommerce platform", "volume": 12100, "difficulty": 82, "cpc": 10.20},

    # More low difficulty gems
    {"keyword": "thread pitch calculator", "volume": 1300, "difficulty": 0, "cpc": 0.25},
    {"keyword": "rpm to rad/s converter", "volume": 880, "difficulty": 0, "cpc": 0.10},
    {"keyword": "hydraulic cylinder calculator", "volume": 720, "difficulty": 1, "cpc": 0.40},
    {"keyword": "sheet metal bend allowance calculator", "volume": 590, "difficulty": 0, "cpc": 0.35},
    {"keyword": "weld strength calculator", "volume": 480, "difficulty": 0, "cpc": 0.30},
    {"keyword": "pneumatic cylinder force calculator", "volume": 390, "difficulty": 1, "cpc": 0.25},
    {"keyword": "belt length calculator", "volume": 880, "difficulty": 2, "cpc": 0.20},
    {"keyword": "chain length calculator", "volume": 720, "difficulty": 1, "cpc": 0.15},
    {"keyword": "thermal expansion calculator", "volume": 1300, "difficulty": 3, "cpc": 0.30},
    {"keyword": "pressure drop calculator", "volume": 1600, "difficulty": 2, "cpc": 0.35},
    {"keyword": "flow rate calculator", "volume": 2900, "difficulty": 5, "cpc": 0.40},
    {"keyword": "pump head calculator", "volume": 590, "difficulty": 0, "cpc": 0.30},
    {"keyword": "venturi flow calculator", "volume": 320, "difficulty": 0, "cpc": 0.20},
    {"keyword": "orifice plate calculator", "volume": 480, "difficulty": 1, "cpc": 0.25},
    {"keyword": "catenary calculator", "volume": 390, "difficulty": 0, "cpc": 0.15},
    {"keyword": "moment of inertia calculator", "volume": 2400, "difficulty": 4, "cpc": 0.20},
    {"keyword": "deflection calculator beam", "volume": 1600, "difficulty": 3, "cpc": 0.30},
    {"keyword": "column buckling calculator", "volume": 720, "difficulty": 0, "cpc": 0.25},
    {"keyword": "fatigue life calculator", "volume": 390, "difficulty": 0, "cpc": 0.20},
    {"keyword": "stress concentration factor calculator", "volume": 590, "difficulty": 1, "cpc": 0.15},
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
               (keyword, volume, difficulty, cpc, competition, source, seed_keyword, last_updated)
               VALUES (?, ?, ?, ?, ?, 'demo', 'demo', ?)""",
            [
                (kw["keyword"], kw["volume"], kw["difficulty"], kw["cpc"],
                 round(random.uniform(0.01, 0.95), 2), now)
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
# DataForSEO client
# ---------------------------------------------------------------------------

async def dataforseo_search(seed: str, login: str, password: str) -> list[dict]:
    """
    Fetch related keywords with volume and difficulty from DataForSEO.
    Uses the Keywords Data API (Google Ads) for volume and
    DataForSEO Labs for keyword difficulty.
    """
    results: list[dict] = []
    auth = (login, password)
    base = "https://api.dataforseo.com/v3"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1 -- get related keywords with volume via Keywords Data
        payload = [{"keyword": seed, "language_code": "en", "location_code": 2840}]
        resp = await client.post(
            f"{base}/keywords_data/google_ads/keywords_for_keywords/live",
            json=payload,
            auth=auth,
        )
        resp.raise_for_status()
        data = resp.json()

        kw_list: list[dict] = []
        for task in data.get("tasks", []):
            for result in task.get("result", []) or []:
                kw_text = result.get("keyword", "")
                vol = result.get("search_volume") or 0
                cpc_val = result.get("cpc") or 0.0
                comp = result.get("competition") or 0.0
                if kw_text:
                    kw_list.append({
                        "keyword": kw_text,
                        "volume": vol,
                        "cpc": round(cpc_val, 2),
                        "competition": round(comp, 4),
                    })

        if not kw_list:
            return results

        # Step 2 -- get difficulty scores via DataForSEO Labs
        # Batch in groups of 100
        for i in range(0, len(kw_list), 100):
            batch = kw_list[i : i + 100]
            diff_payload = [{
                "keywords": [k["keyword"] for k in batch],
                "language_code": "en",
                "location_code": 2840,
            }]
            diff_resp = await client.post(
                f"{base}/dataforseo_labs/google/keyword_suggestions/live",
                json=diff_payload,
                auth=auth,
            )
            diff_resp.raise_for_status()
            diff_data = diff_resp.json()

            # Build a difficulty lookup
            diff_map: dict[str, int] = {}
            for task in diff_data.get("tasks", []):
                for result in task.get("result", []) or []:
                    for item in result.get("items", []) or []:
                        kd = item.get("keyword_info", {}).get("keyword_difficulty")
                        kw_name = item.get("keyword")
                        if kw_name and kd is not None:
                            diff_map[kw_name.lower()] = int(kd)

            for kw in batch:
                kw["difficulty"] = diff_map.get(kw["keyword"].lower(), 0)

        results = kw_list

    return results


# ---------------------------------------------------------------------------
# CSV parser  (Ahrefs, Semrush, or generic)
# ---------------------------------------------------------------------------

# Column name mappings for common SEO tool exports
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
    """Map our canonical field names to column indices in the CSV."""
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


class SettingsPayload(BaseModel):
    data_source: str = "demo"           # demo | dataforseo | google_ads
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_developer_token: str = ""
    google_ads_refresh_token: str = ""
    google_ads_customer_id: str = ""


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
    # Mask sensitive values
    masked = {}
    for k, v in settings.items():
        if any(secret in k for secret in ("password", "secret", "token")):
            masked[k] = "***" + v[-4:] if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked


@app.post("/api/settings")
async def save_settings(payload: SettingsPayload):
    for field_name, value in payload.model_dump().items():
        _save_setting(field_name, str(value))
    return {"status": "ok"}


# ---- Search ------------------------------------------------------------

@app.post("/api/search")
async def search_keywords(req: SearchRequest):
    """Search for keywords by seed. Uses configured data source."""
    seed = req.seed_keyword.strip().lower()
    if not seed:
        return {"error": "Seed keyword is required", "keywords": []}

    settings = _get_settings()
    source = settings.get("data_source", "demo")

    new_keywords: list[dict] = []

    if source == "dataforseo":
        login = settings.get("dataforseo_login", "")
        password = settings.get("dataforseo_password", "")
        if not login or not password:
            return {"error": "DataForSEO credentials not configured", "keywords": []}
        try:
            new_keywords = await dataforseo_search(seed, login, password)
        except httpx.HTTPStatusError as exc:
            return {"error": f"DataForSEO API error: {exc.response.status_code}", "keywords": []}
        except Exception as exc:
            return {"error": f"DataForSEO error: {exc}", "keywords": []}

    elif source == "google_ads":
        # Google Ads integration would go here; for now return an info message
        return {
            "error": "Google Ads integration is not yet implemented. Use DataForSEO or CSV import.",
            "keywords": [],
        }

    else:
        # Demo mode -- filter demo data by seed substring and generate related variants
        new_keywords = _generate_demo_search_results(seed)

    # Persist to database
    if new_keywords:
        _upsert_keywords(new_keywords, source=source, seed=seed)

    # Return all keywords matching the seed
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT keyword, volume, difficulty, cpc, competition, source "
            "FROM keywords WHERE seed_keyword = ? ORDER BY volume DESC",
            (seed,),
        ).fetchall()
        result = [dict(r) for r in rows]
        result = compute_opportunity_scores(result)
        return {"keywords": result, "count": len(result)}
    finally:
        conn.close()


def _generate_demo_search_results(seed: str) -> list[dict]:
    """Generate realistic-looking search results for demo mode."""
    results: list[dict] = []
    seed_lower = seed.lower()

    # Include exact matches from demo data
    for kw in _DEMO_KEYWORDS:
        if seed_lower in kw["keyword"].lower():
            results.append(dict(kw))

    # Generate some plausible variations
    prefixes = ["best", "free", "online", "simple", "easy", "quick"]
    suffixes = ["online", "free", "tool", "app", "2024", "for beginners"]

    random.seed(hash(seed) + int(time.time() / 3600))  # stable within the hour
    for prefix in random.sample(prefixes, min(3, len(prefixes))):
        vol = random.randint(100, 5000)
        diff = random.randint(0, 60)
        results.append({
            "keyword": f"{prefix} {seed}",
            "volume": vol,
            "difficulty": diff,
            "cpc": round(random.uniform(0.1, 3.0), 2),
            "competition": round(random.uniform(0.01, 0.8), 2),
        })
    for suffix in random.sample(suffixes, min(3, len(suffixes))):
        vol = random.randint(50, 3000)
        diff = random.randint(0, 45)
        results.append({
            "keyword": f"{seed} {suffix}",
            "volume": vol,
            "difficulty": diff,
            "cpc": round(random.uniform(0.1, 2.5), 2),
            "competition": round(random.uniform(0.01, 0.7), 2),
        })

    # Add the seed keyword itself
    results.append({
        "keyword": seed,
        "volume": random.randint(1000, 20000),
        "difficulty": random.randint(10, 50),
        "cpc": round(random.uniform(0.5, 4.0), 2),
        "competition": round(random.uniform(0.1, 0.9), 2),
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
               (keyword, volume, difficulty, cpc, competition, source, seed_keyword, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(keyword) DO UPDATE SET
                 volume = excluded.volume,
                 difficulty = excluded.difficulty,
                 cpc = excluded.cpc,
                 competition = excluded.competition,
                 source = excluded.source,
                 seed_keyword = excluded.seed_keyword,
                 last_updated = excluded.last_updated
            """,
            [
                (
                    kw["keyword"], kw.get("volume", 0), kw.get("difficulty", 0),
                    kw.get("cpc", 0.0), kw.get("competition", 0.0),
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
    content = (await file.read()).decode("utf-8-sig")  # Handle BOM
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
    allowed_sort = {"volume", "difficulty", "cpc", "competition", "keyword", "opportunity_score"}
    if sort_by not in allowed_sort:
        sort_by = "volume"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT keyword, volume, difficulty, cpc, competition, source
               FROM keywords
               WHERE difficulty >= ? AND difficulty <= ?
                 AND volume >= ? AND volume <= ?
               ORDER BY volume DESC""",
            (difficulty_min, difficulty_max, volume_min, volume_max),
        ).fetchall()
        result = [dict(r) for r in rows]
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8765)
