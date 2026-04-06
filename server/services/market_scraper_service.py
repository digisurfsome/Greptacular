"""
Market Scraper Service
======================

Scrapes Reddit threads for user phrasings about pain points, desires,
and feature requests. Categorizes them for ad copy, social media content,
and app idea validation.

Uses Reddit's public JSON API (append .json to any thread URL) — no
OAuth or API keys required.
"""

import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DB_PATH = Path.home() / ".autoforge" / "market_scraper.db"

# Reddit JSON API requires a descriptive User-Agent to avoid 429s.
REDDIT_USER_AGENT = "Greptacular:MarketScraper/1.0 (research tool; +https://github.com/Greptacular)"

# Minimum comment length to consider "substantial"
MIN_COMMENT_LENGTH = 20

# ---------------------------------------------------------------------------
# Category keyword patterns
# ---------------------------------------------------------------------------

# Each category maps to a list of regex patterns (case-insensitive).
# Order matters — first match wins.
CATEGORY_PATTERNS: dict[str, list[str]] = {
    "validation": [
        r"i'?d pay",
        r"take my money",
        r"shut up and take",
        r"this is what i need",
        r"game[ -]?changer",
        r"instant buy",
        r"worth every",
        r"i'?d subscribe",
        r"day one purchase",
    ],
    "social_proof": [
        r"i switched to",
        r"best tool",
        r"changed my life",
        r"finally found",
        r"been using .+ for",
        r"can'?t go back",
        r"never going back",
        r"can'?t live without",
        r"life[ -]?saver",
        r"holy grail",
    ],
    "pain_point": [
        r"i hate",
        r"i wish",
        r"why can'?t",
        r"so frustrat",
        r"drives me crazy",
        r"pisses me off",
        r"annoying",
        r"broken",
        r"terrible",
        r"worst",
        r"can'?t stand",
        r"sick of",
        r"fed up",
        r"deal[ -]?breaker",
        r"waste of time",
        r"struggling with",
    ],
    "desire": [
        r"i want",
        r"i need",
        r"would love",
        r"looking for",
        r"hoping for",
        r"dream feature",
        r"if only",
        r"desperately need",
        r"dying for",
        r"wish there was",
        r"anyone know .+ that",
    ],
    "feature_request": [
        r"should have",
        r"needs to",
        r"would be nice",
        r"please add",
        r"feature request",
        r"it should",
        r"they need to",
        r"missing feature",
        r"when will .+ support",
        r"they should",
        r"can we get",
    ],
}

# Subcategory detection based on topic keywords
SUBCATEGORY_PATTERNS: dict[str, list[str]] = {
    "pricing": [r"price", r"cost", r"expensive", r"cheap", r"free", r"subscription", r"pay", r"afford"],
    "ux": [r"ui\b", r"ux\b", r"interface", r"design", r"layout", r"confusing", r"intuitive", r"clunky"],
    "speed": [r"slow", r"fast", r"speed", r"performance", r"lag", r"loading", r"responsive"],
    "features": [r"feature", r"functionality", r"capability", r"option", r"setting", r"tool"],
    "support": [r"support", r"help", r"customer service", r"response time", r"documentation", r"docs"],
    "reliability": [r"bug", r"crash", r"error", r"broken", r"stable", r"reliable", r"downtime"],
    "integration": [r"integrat", r"plugin", r"extension", r"api\b", r"connect", r"sync"],
    "security": [r"security", r"privacy", r"encrypt", r"safe", r"data", r"breach"],
}

# Compiled patterns (built once at import time)
_COMPILED_CATEGORIES: dict[str, list[re.Pattern[str]]] = {
    cat: [re.compile(p, re.IGNORECASE) for p in patterns]
    for cat, patterns in CATEGORY_PATTERNS.items()
}

_COMPILED_SUBCATEGORIES: dict[str, list[re.Pattern[str]]] = {
    sub: [re.compile(p, re.IGNORECASE) for p in patterns]
    for sub, patterns in SUBCATEGORY_PATTERNS.items()
}


def _init_db() -> sqlite3.Connection:
    """Create tables if they don't exist and return a connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scrapes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT NOT NULL,
            subreddit   TEXT NOT NULL DEFAULT '',
            title       TEXT NOT NULL DEFAULT '',
            scraped_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS phrases (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            scrape_id           INTEGER NOT NULL REFERENCES scrapes(id) ON DELETE CASCADE,
            raw_text            TEXT NOT NULL,
            author              TEXT NOT NULL DEFAULT '',
            score               INTEGER NOT NULL DEFAULT 0,
            category            TEXT NOT NULL DEFAULT 'uncategorized',
            subcategory         TEXT NOT NULL DEFAULT '',
            ad_hook             TEXT NOT NULL DEFAULT '',
            social_post_idea    TEXT NOT NULL DEFAULT '',
            validation_signal   INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_phrases_scrape ON phrases(scrape_id);
        CREATE INDEX IF NOT EXISTS idx_phrases_category ON phrases(category);
        CREATE INDEX IF NOT EXISTS idx_phrases_validation ON phrases(validation_signal);
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Reddit scraping
# ---------------------------------------------------------------------------


def _normalize_reddit_url(url: str) -> str:
    """Normalize a Reddit URL to the canonical www.reddit.com form and append .json."""
    url = url.strip().rstrip("/")

    # Replace old.reddit.com with www.reddit.com
    url = re.sub(r"https?://old\.reddit\.com", "https://www.reddit.com", url)
    # Replace bare reddit.com with www.reddit.com
    url = re.sub(r"https?://reddit\.com", "https://www.reddit.com", url)

    # Strip any existing .json suffix so we don't double it
    if url.endswith(".json"):
        url = url[:-5]

    return url + ".json"


def _extract_subreddit(url: str) -> str:
    """Pull the subreddit name from a Reddit URL."""
    match = re.search(r"/r/([^/]+)", url)
    return match.group(1) if match else ""


def _flatten_comments(children: list[dict[str, Any]], depth: int = 0) -> list[dict[str, Any]]:
    """Recursively flatten the Reddit comment tree into a flat list."""
    results: list[dict[str, Any]] = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child.get("data", {})
        body = data.get("body", "")
        # Skip deleted/removed/bot comments and very short comments
        if body in ("[deleted]", "[removed]", "") or len(body) < MIN_COMMENT_LENGTH:
            continue

        results.append({
            "author": data.get("author", "[unknown]"),
            "body": body,
            "score": data.get("score", 0),
            "created_utc": data.get("created_utc", 0),
        })

        # Recurse into replies
        replies = data.get("replies")
        if isinstance(replies, dict):
            reply_children = replies.get("data", {}).get("children", [])
            results.extend(_flatten_comments(reply_children, depth + 1))

    return results


async def scrape_reddit_thread(url: str) -> dict[str, Any]:
    """Fetch a Reddit thread's JSON and extract the post + all comments.

    Returns a dict with keys: url, subreddit, title, post_body, comments.
    Raises httpx.HTTPStatusError or ValueError on failure.
    """
    json_url = _normalize_reddit_url(url)
    subreddit = _extract_subreddit(url)

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(30.0),
        headers={"User-Agent": REDDIT_USER_AGENT},
    ) as client:
        resp = await client.get(json_url)
        resp.raise_for_status()

    data = resp.json()

    # Reddit thread JSON is a 2-element list:
    # [0] = the post listing, [1] = the comment listing
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Unexpected Reddit JSON structure — expected a 2-element list")

    post_data = data[0]["data"]["children"][0]["data"]
    title = post_data.get("title", "")
    post_body = post_data.get("selftext", "")

    comment_children = data[1]["data"]["children"]
    comments = _flatten_comments(comment_children)

    logger.info("Scraped r/%s — %d comments from '%s'", subreddit, len(comments), title)

    return {
        "url": url,
        "subreddit": subreddit,
        "title": title,
        "post_body": post_body,
        "comments": comments,
    }


# ---------------------------------------------------------------------------
# Categorization engine
# ---------------------------------------------------------------------------


def _classify_category(text: str) -> str:
    """Return the best-fit category for a piece of text."""
    lower = text.lower()
    for category, patterns in _COMPILED_CATEGORIES.items():
        for pat in patterns:
            if pat.search(lower):
                return category
    return "uncategorized"


def _classify_subcategory(text: str) -> str:
    """Return the best-fit subcategory (topic area) for a piece of text."""
    lower = text.lower()
    for subcategory, patterns in _COMPILED_SUBCATEGORIES.items():
        for pat in patterns:
            if pat.search(lower):
                return subcategory
    return "general"


def _generate_ad_hook(text: str, category: str) -> str:
    """Generate a punchy ad-copy hook from the user's raw phrasing.

    This is a rule-based rewrite for v1 — no AI call needed.
    """
    # Truncate to a reasonable length for a hook
    snippet = text[:150].strip()

    # Remove markdown formatting
    snippet = re.sub(r"[*_~`#>\[\]]", "", snippet).strip()

    prefix_map = {
        "pain_point": "Tired of this?",
        "desire": "You're not alone.",
        "feature_request": "People are asking for this.",
        "validation": "They'd pay for this.",
        "social_proof": "Real users are saying this.",
        "uncategorized": "From the community:",
    }
    prefix = prefix_map.get(category, "From the community:")

    return f'{prefix} "{snippet}..."'


def _generate_social_post_idea(text: str, category: str, subreddit: str) -> str:
    """Generate a social media post angle from the raw phrasing."""
    snippet = text[:100].strip()
    snippet = re.sub(r"[*_~`#>\[\]]", "", snippet).strip()

    angle_map = {
        "pain_point": f'r/{subreddit} users are frustrated: "{snippet}..." — Here\'s how we solve this.',
        "desire": f'Spotted on r/{subreddit}: "{snippet}..." — Sounds like a product opportunity.',
        "feature_request": f'Feature request trending on r/{subreddit}: "{snippet}..." — Should builders pay attention?',
        "validation": f'Reddit user would pay for this: "{snippet}..." — Market signal from r/{subreddit}.',
        "social_proof": f'Real feedback from r/{subreddit}: "{snippet}..." — Social proof gold.',
        "uncategorized": f'Interesting take from r/{subreddit}: "{snippet}..."',
    }
    return angle_map.get(category, angle_map["uncategorized"])


def _compute_validation_signal(score: int, text: str, category: str) -> int:
    """Compute a 1-5 validation strength score.

    Factors: Reddit upvotes, phrase intensity (strong language),
    and category weight (validation/social_proof rank higher).
    """
    # Base score from upvotes
    if score >= 100:
        signal = 4
    elif score >= 50:
        signal = 3
    elif score >= 10:
        signal = 2
    else:
        signal = 1

    # Category bonus — validation and social_proof are inherently stronger signals
    if category in ("validation", "social_proof"):
        signal = min(5, signal + 1)

    # Intensity bonus — strong emotional language
    intensity_words = [
        r"absolutely", r"definitely", r"100%", r"without a doubt",
        r"game[ -]?changer", r"life[ -]?saver", r"incredible", r"amazing",
        r"terrible", r"horrible", r"unbearable", r"desperate",
    ]
    lower = text.lower()
    for word_pat in intensity_words:
        if re.search(word_pat, lower):
            signal = min(5, signal + 1)
            break  # Only one bonus from intensity

    return signal


def categorize_comments(
    comments: list[dict[str, Any]],
    subreddit: str,
) -> list[dict[str, Any]]:
    """Categorize a list of extracted Reddit comments.

    Returns enriched comment dicts with category, subcategory,
    ad_hook, social_post_idea, and validation_signal fields.
    """
    results: list[dict[str, Any]] = []
    for comment in comments:
        body = comment["body"]
        category = _classify_category(body)
        subcategory = _classify_subcategory(body)
        ad_hook = _generate_ad_hook(body, category)
        social_post_idea = _generate_social_post_idea(body, category, subreddit)
        validation_signal = _compute_validation_signal(comment["score"], body, category)

        results.append({
            **comment,
            "category": category,
            "subcategory": subcategory,
            "ad_hook": ad_hook,
            "social_post_idea": social_post_idea,
            "validation_signal": validation_signal,
        })

    return results


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


def save_scrape(
    url: str,
    subreddit: str,
    title: str,
    categorized_comments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist a scrape and its phrases to the database.

    Returns the full scrape record including all phrases.
    """
    conn = _init_db()
    now = datetime.now(timezone.utc).isoformat()

    try:
        cur = conn.execute(
            "INSERT INTO scrapes (url, subreddit, title, scraped_at) VALUES (?, ?, ?, ?)",
            (url, subreddit, title, now),
        )
        scrape_id = cur.lastrowid

        for comment in categorized_comments:
            created_at = datetime.fromtimestamp(
                comment.get("created_utc", 0), tz=timezone.utc
            ).isoformat() if comment.get("created_utc") else now

            conn.execute(
                """INSERT INTO phrases
                   (scrape_id, raw_text, author, score, category, subcategory,
                    ad_hook, social_post_idea, validation_signal, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scrape_id,
                    comment["body"],
                    comment.get("author", ""),
                    comment.get("score", 0),
                    comment["category"],
                    comment["subcategory"],
                    comment["ad_hook"],
                    comment["social_post_idea"],
                    comment["validation_signal"],
                    created_at,
                ),
            )

        conn.commit()

        # Return the full record
        return get_scrape(scrape_id)  # type: ignore[return-value]
    finally:
        conn.close()


def list_scrapes() -> list[dict[str, Any]]:
    """List all scrapes with summary stats (phrase count by category)."""
    conn = _init_db()
    try:
        rows = conn.execute(
            "SELECT * FROM scrapes ORDER BY scraped_at DESC"
        ).fetchall()

        results = []
        for row in rows:
            scrape = dict(row)

            # Attach category counts
            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as count FROM phrases WHERE scrape_id = ? GROUP BY category",
                (row["id"],),
            ).fetchall()
            scrape["category_counts"] = {r["category"]: r["count"] for r in cat_rows}

            total = conn.execute(
                "SELECT COUNT(*) as total FROM phrases WHERE scrape_id = ?",
                (row["id"],),
            ).fetchone()
            scrape["total_phrases"] = total["total"] if total else 0

            results.append(scrape)

        return results
    finally:
        conn.close()


def get_scrape(scrape_id: int) -> Optional[dict[str, Any]]:
    """Get a single scrape with all its phrases."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT * FROM scrapes WHERE id = ?", (scrape_id,)).fetchone()
        if not row:
            return None

        scrape = dict(row)

        phrases = conn.execute(
            "SELECT * FROM phrases WHERE scrape_id = ? ORDER BY validation_signal DESC, score DESC",
            (scrape_id,),
        ).fetchall()
        scrape["phrases"] = [dict(p) for p in phrases]

        # Category counts
        cat_rows = conn.execute(
            "SELECT category, COUNT(*) as count FROM phrases WHERE scrape_id = ? GROUP BY category",
            (scrape_id,),
        ).fetchall()
        scrape["category_counts"] = {r["category"]: r["count"] for r in cat_rows}
        scrape["total_phrases"] = len(phrases)

        return scrape
    finally:
        conn.close()


def query_phrases(
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    min_validation: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Query phrases across all scrapes with optional filters."""
    conn = _init_db()
    try:
        conditions: list[str] = []
        params: list[Any] = []

        if category:
            conditions.append("p.category = ?")
            params.append(category)
        if min_score is not None:
            conditions.append("p.score >= ?")
            params.append(min_score)
        if min_validation is not None:
            conditions.append("p.validation_signal >= ?")
            params.append(min_validation)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = conn.execute(
            f"""SELECT p.*, s.url as scrape_url, s.subreddit, s.title as scrape_title
                FROM phrases p
                JOIN scrapes s ON p.scrape_id = s.id
                {where}
                ORDER BY p.validation_signal DESC, p.score DESC""",
            params,
        ).fetchall()

        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_scrape(scrape_id: int) -> bool:
    """Delete a scrape and all its phrases. Returns True if found and deleted."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT id FROM scrapes WHERE id = ?", (scrape_id,)).fetchone()
        if not row:
            return False
        # CASCADE takes care of phrases
        conn.execute("DELETE FROM scrapes WHERE id = ?", (scrape_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def export_phrases_csv(scrape_id: int) -> Optional[str]:
    """Export all phrases for a scrape as a CSV string. Returns None if scrape not found."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT id FROM scrapes WHERE id = ?", (scrape_id,)).fetchone()
        if not row:
            return None

        phrases = conn.execute(
            "SELECT * FROM phrases WHERE scrape_id = ? ORDER BY validation_signal DESC, score DESC",
            (scrape_id,),
        ).fetchall()

        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "raw_text", "author", "score", "category", "subcategory",
            "ad_hook", "social_post_idea", "validation_signal", "created_at",
        ])
        for p in phrases:
            writer.writerow([
                p["id"], p["raw_text"], p["author"], p["score"],
                p["category"], p["subcategory"], p["ad_hook"],
                p["social_post_idea"], p["validation_signal"], p["created_at"],
            ])

        return output.getvalue()
    finally:
        conn.close()
