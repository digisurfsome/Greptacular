"""
Market Scraper Service
======================

Scrapes Reddit threads for user phrasings about pain points, desires,
and feature requests. Categorizes them for ad copy, social media content,
and app idea validation.

Uses Reddit's public JSON API (append .json to any thread URL) — no
OAuth or API keys required.
"""

import json
import logging
import re
import sqlite3
from collections import Counter
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

        CREATE TABLE IF NOT EXISTS research_projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            niche       TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            status      TEXT NOT NULL DEFAULT 'draft',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS project_angles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
            angle_type      TEXT NOT NULL,
            custom_keywords TEXT NOT NULL DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'pending',
            search_queries  TEXT NOT NULL DEFAULT '[]',
            scrape_ids      TEXT NOT NULL DEFAULT '[]',
            total_phrases   INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_angles_project ON project_angles(project_id);
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


# ---------------------------------------------------------------------------
# Reddit topic search
# ---------------------------------------------------------------------------

# Popular subreddits for app/SaaS/startup market research
DEFAULT_SUBREDDITS = [
    "SaaS", "startups", "Entrepreneur", "SideProject", "indiehackers",
    "ClaudeAI", "ChatGPT", "artificial", "MachineLearning",
    "webdev", "programming", "software",
]

# Research angle types — each generates search queries based on niche + keywords
ANGLE_TYPES: dict[str, dict[str, Any]] = {
    "discovery": {
        "label": "Discovery",
        "description": "What tools, automations, and frameworks people ARE using",
        "seed_phrases": [
            "using {niche} for", "my {niche} setup", "{niche} automation",
            "{niche} tools I use", "{niche} stack", "{niche} workflow",
            "built a {niche}", "{niche} with Claude", "{niche} with AI",
        ],
    },
    "desire": {
        "label": "Desire",
        "description": "What tools and automations people WANT",
        "seed_phrases": [
            "{niche} looking for", "{niche} wish there was",
            "{niche} need a tool", "anyone know {niche}",
            "{niche} recommendation", "best {niche} tool",
            "{niche} alternative", "help me find {niche}",
        ],
    },
    "pain_point": {
        "label": "Pain Point",
        "description": "Frustrations, complaints, and broken things",
        "seed_phrases": [
            "{niche} frustrated", "{niche} hate", "{niche} broken",
            "{niche} waste of time", "{niche} terrible", "{niche} struggling",
            "{niche} complaint", "{niche} problem with",
        ],
    },
    "validation": {
        "label": "Validation",
        "description": "Purchase intent and willingness to pay",
        "seed_phrases": [
            "{niche} would pay for", "{niche} take my money",
            "{niche} game changer", "{niche} worth it",
            "{niche} best investment", "{niche} subscription",
            "pay for {niche}", "{niche} pricing",
        ],
    },
    "workflow": {
        "label": "Workflow",
        "description": "Step-by-step processes and frameworks people share",
        "seed_phrases": [
            "{niche} my workflow", "{niche} step by step",
            "{niche} how I automate", "{niche} my process",
            "{niche} framework", "{niche} system I built",
            "{niche} SOP", "how I run {niche}",
        ],
    },
    "education": {
        "label": "Education",
        "description": "Learning resources, tutorials, and courses discussed",
        "seed_phrases": [
            "{niche} tutorial", "{niche} course", "{niche} guide",
            "learn {niche}", "{niche} for beginners", "{niche} training",
            "{niche} certification", "{niche} bootcamp",
        ],
    },
}

SORT_OPTIONS = ("relevance", "hot", "top", "new", "comments")
TIME_FILTERS = ("all", "year", "month", "week", "day", "hour")


async def search_reddit(
    query: str,
    subreddits: Optional[list[str]] = None,
    sort: str = "relevance",
    time_filter: str = "week",
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Search Reddit for threads matching a topic query.

    Args:
        query: Search terms (e.g., "app maker frustrations")
        subreddits: List of subreddits to search in, or None for all of Reddit
        sort: One of relevance, hot, top, new, comments
        time_filter: One of all, year, month, week, day, hour
        limit: Max results per subreddit (Reddit caps at 100)

    Returns a list of thread summaries with url, title, subreddit, score,
    num_comments, and created_utc.
    """
    if sort not in SORT_OPTIONS:
        sort = "relevance"
    if time_filter not in TIME_FILTERS:
        time_filter = "week"
    limit = min(limit, 100)

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(30.0),
        headers={"User-Agent": REDDIT_USER_AGENT},
    ) as client:
        # Build list of search URLs
        search_urls: list[str] = []
        if subreddits:
            for sub in subreddits:
                sub = sub.strip().strip("/")
                search_urls.append(
                    f"https://www.reddit.com/r/{sub}/search.json"
                )
        else:
            search_urls.append("https://www.reddit.com/search.json")

        for search_url in search_urls:
            params: dict[str, Any] = {
                "q": query,
                "sort": sort,
                "t": time_filter,
                "limit": limit,
                "type": "link",
            }
            # restrict_sr=on when searching within a subreddit
            if "/r/" in search_url:
                params["restrict_sr"] = "on"

            try:
                resp = await client.get(search_url, params=params)
                resp.raise_for_status()
                data = resp.json()

                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    post_id = post.get("id", "")
                    if post_id in seen_ids:
                        continue
                    seen_ids.add(post_id)

                    # Only include self-posts and discussions (skip link-only posts with no comments)
                    num_comments = post.get("num_comments", 0)
                    if num_comments < 2:
                        continue

                    permalink = post.get("permalink", "")
                    url = f"https://www.reddit.com{permalink}" if permalink else ""

                    results.append({
                        "id": post_id,
                        "url": url,
                        "title": post.get("title", ""),
                        "subreddit": post.get("subreddit", ""),
                        "score": post.get("score", 0),
                        "num_comments": num_comments,
                        "selftext_preview": (post.get("selftext", "") or "")[:200],
                        "created_utc": post.get("created_utc", 0),
                        "is_self": post.get("is_self", False),
                    })

            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Reddit search failed for %s (HTTP %d)", search_url, exc.response.status_code
                )
            except Exception:
                logger.exception("Error searching %s", search_url)

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    logger.info("Reddit search for '%s' found %d threads", query, len(results))
    return results


async def search_and_scrape(
    query: str,
    subreddits: Optional[list[str]] = None,
    sort: str = "relevance",
    time_filter: str = "week",
    max_threads: int = 5,
    search_limit: int = 25,
) -> dict[str, Any]:
    """Search Reddit for a topic, then scrape the top threads and categorize everything.

    Returns a combined result with all threads' phrases merged and categorized.
    """
    # Step 1: Search for matching threads
    threads = await search_reddit(
        query=query,
        subreddits=subreddits,
        sort=sort,
        time_filter=time_filter,
        limit=search_limit,
    )

    if not threads:
        return {
            "query": query,
            "subreddits": subreddits or [],
            "threads_found": 0,
            "threads_scraped": 0,
            "scrape_ids": [],
            "total_phrases": 0,
            "category_counts": {},
        }

    # Step 2: Scrape the top N threads
    threads_to_scrape = threads[:max_threads]
    scrape_ids: list[int] = []
    total_phrases = 0
    all_category_counts: dict[str, int] = {}
    scraped_count = 0

    for thread in threads_to_scrape:
        url = thread.get("url", "")
        if not url:
            continue

        try:
            thread_data = await scrape_reddit_thread(url)
            categorized = categorize_comments(
                thread_data["comments"],
                thread_data["subreddit"],
            )

            # Also categorize OP post body
            post_body = thread_data.get("post_body", "")
            if post_body and len(post_body) >= MIN_COMMENT_LENGTH:
                post_as_comment = [{
                    "author": "OP",
                    "body": post_body,
                    "score": thread.get("score", 0),
                    "created_utc": thread.get("created_utc", 0),
                }]
                categorized_post = categorize_comments(post_as_comment, thread_data["subreddit"])
                categorized = categorized_post + categorized

            result = save_scrape(
                url=url,
                subreddit=thread_data["subreddit"],
                title=thread_data["title"],
                categorized_comments=categorized,
            )

            if result:
                scrape_ids.append(result["id"])
                total_phrases += result.get("total_phrases", 0)
                for cat, count in result.get("category_counts", {}).items():
                    all_category_counts[cat] = all_category_counts.get(cat, 0) + count
                scraped_count += 1

        except Exception:
            logger.exception("Failed to scrape thread: %s", url)
            continue

    return {
        "query": query,
        "subreddits": subreddits or [],
        "threads_found": len(threads),
        "threads_scraped": scraped_count,
        "scrape_ids": scrape_ids,
        "total_phrases": total_phrases,
        "category_counts": all_category_counts,
        "threads": threads[:max_threads],  # Include thread summaries for the UI
    }


# ---------------------------------------------------------------------------
# Phrase frequency analysis
# ---------------------------------------------------------------------------

# Common stop words to skip in n-gram extraction
_STOP_WORDS = frozenset({
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her",
    "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for", "with",
    "about", "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
    "t", "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o", "re",
    "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn", "haven",
    "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn", "weren",
    "won", "wouldn", "also", "like", "would", "could", "much", "get", "got", "go",
    "going", "really", "thing", "things", "think", "know", "still", "even", "way",
    "one", "use", "using", "used", "make", "makes", "made", "well", "want",
    "need", "something", "anything", "everything", "nothing", "someone", "anyone",
    "everyone", "lot", "lots", "many", "every", "right", "good", "new", "try",
    "trying", "tried", "see", "look", "looking", "say", "said", "come", "back",
    "take", "give", "people", "been", "done", "yeah", "yes", "sure",
    "http", "https", "www", "com", "org", "reddit", "deleted", "removed",
})

# Regex to clean text for n-gram extraction
_CLEAN_RE = re.compile(r"[^a-z0-9\s'-]")
_MULTI_SPACE_RE = re.compile(r"\s+")


def _tokenize(text: str) -> list[str]:
    """Clean and tokenize text into lowercase words, filtering stop words."""
    text = text.lower()
    text = _CLEAN_RE.sub(" ", text)
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return [w for w in text.split() if w not in _STOP_WORDS and len(w) > 1]


def _extract_ngrams(tokens: list[str], n: int) -> list[str]:
    """Extract n-grams from a token list."""
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def get_phrase_frequencies(
    scrape_ids: Optional[list[int]] = None,
    min_ngram: int = 2,
    max_ngram: int = 4,
    top_n: int = 50,
    category: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Extract the most frequently used multi-word phrases from scraped comments.

    Analyzes all raw_text in the phrases table, extracts 2-4 word n-grams,
    counts their frequency, and returns the top phrases ranked by count.

    Args:
        scrape_ids: Limit to specific scrapes, or None for all
        min_ngram: Minimum n-gram size (default 2)
        max_ngram: Maximum n-gram size (default 4)
        top_n: Number of top phrases to return (default 50)
        category: Filter by category (e.g., "pain_point", "desire")

    Returns a list of dicts: {phrase, count, ngram_size, sample_texts, categories}
    """
    conn = _init_db()
    try:
        conditions: list[str] = []
        params: list[Any] = []

        if scrape_ids:
            placeholders = ",".join("?" * len(scrape_ids))
            conditions.append(f"scrape_id IN ({placeholders})")
            params.extend(scrape_ids)
        if category:
            conditions.append("category = ?")
            params.append(category)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = conn.execute(
            f"SELECT raw_text, category FROM phrases {where}",
            params,
        ).fetchall()

        # Count n-grams across all comments
        ngram_counter: Counter[str] = Counter()
        # Track which categories each phrase appears in
        ngram_categories: dict[str, Counter[str]] = {}
        # Track sample texts for each phrase
        ngram_samples: dict[str, list[str]] = {}

        for row in rows:
            text = row["raw_text"]
            cat = row["category"]
            tokens = _tokenize(text)

            for n in range(min_ngram, max_ngram + 1):
                for ngram in _extract_ngrams(tokens, n):
                    ngram_counter[ngram] += 1

                    if ngram not in ngram_categories:
                        ngram_categories[ngram] = Counter()
                    ngram_categories[ngram][cat] += 1

                    if ngram not in ngram_samples:
                        ngram_samples[ngram] = []
                    if len(ngram_samples[ngram]) < 3:
                        # Store a short preview of the source text
                        preview = text[:150] + ("..." if len(text) > 150 else "")
                        if preview not in ngram_samples[ngram]:
                            ngram_samples[ngram].append(preview)

        # Filter out phrases that only appear once (not a pattern)
        meaningful = {k: v for k, v in ngram_counter.items() if v >= 2}

        # Deduplicate: if a longer phrase contains a shorter one with similar count,
        # prefer the longer one. We do this by sorting by count desc, then length desc.
        sorted_phrases = sorted(meaningful.items(), key=lambda x: (-x[1], -len(x[0])))

        # Remove sub-phrases that are subsumed by a higher-ranked longer phrase
        seen_text: set[str] = set()
        filtered: list[tuple[str, int]] = []
        for phrase, count in sorted_phrases:
            # Check if this phrase is a substring of an already-selected phrase
            is_subphrase = False
            for selected in seen_text:
                if phrase in selected and count <= meaningful.get(selected, 0) * 1.2:
                    is_subphrase = True
                    break
            if not is_subphrase:
                filtered.append((phrase, count))
                seen_text.add(phrase)
            if len(filtered) >= top_n:
                break

        results: list[dict[str, Any]] = []
        for phrase, count in filtered:
            word_count = len(phrase.split())
            cats = dict(ngram_categories.get(phrase, {}))
            samples = ngram_samples.get(phrase, [])
            results.append({
                "phrase": phrase,
                "count": count,
                "ngram_size": word_count,
                "categories": cats,
                "sample_texts": samples,
            })

        logger.info(
            "Phrase frequency analysis: %d unique n-grams, returning top %d",
            len(meaningful), len(results),
        )
        return results
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


# ---------------------------------------------------------------------------
# Research Project — query generation
# ---------------------------------------------------------------------------


def generate_search_queries(niche: str, angle_type: str, custom_keywords: str = "") -> list[str]:
    """Generate Reddit search queries for a niche + angle combination.

    Takes the niche (e.g., "SEO agency"), the angle type, and optional
    custom keywords, and produces a list of search queries.
    """
    angle = ANGLE_TYPES.get(angle_type)
    if not angle:
        return []

    queries: list[str] = []
    niche_clean = niche.strip()

    for template in angle["seed_phrases"]:
        query = template.format(niche=niche_clean)
        queries.append(query)

    # Add custom keywords as additional queries
    if custom_keywords.strip():
        for kw in custom_keywords.split(","):
            kw = kw.strip()
            if kw:
                queries.append(f"{niche_clean} {kw}")

    return queries


# ---------------------------------------------------------------------------
# Research Project — CRUD
# ---------------------------------------------------------------------------


def create_research_project(
    name: str,
    niche: str,
    description: str = "",
    angles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a new research project with selected angles."""
    conn = _init_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        cur = conn.execute(
            "INSERT INTO research_projects (name, niche, description, status, created_at, updated_at) VALUES (?, ?, ?, 'draft', ?, ?)",
            (name, niche, description, now, now),
        )
        project_id = cur.lastrowid

        # Create angles if provided
        if angles:
            for angle in angles:
                angle_type = angle.get("type", "")
                custom_kw = angle.get("custom_keywords", "")
                queries = generate_search_queries(niche, angle_type, custom_kw)
                conn.execute(
                    "INSERT INTO project_angles (project_id, angle_type, custom_keywords, search_queries, created_at) VALUES (?, ?, ?, ?, ?)",
                    (project_id, angle_type, custom_kw, json.dumps(queries), now),
                )

        conn.commit()
        return get_research_project(project_id)  # type: ignore[return-value]
    finally:
        conn.close()


def list_research_projects() -> list[dict[str, Any]]:
    """List all research projects with angle counts."""
    conn = _init_db()
    try:
        rows = conn.execute("SELECT * FROM research_projects ORDER BY updated_at DESC").fetchall()
        results = []
        for row in rows:
            project = dict(row)
            angle_count = conn.execute(
                "SELECT COUNT(*) as count FROM project_angles WHERE project_id = ?",
                (row["id"],),
            ).fetchone()
            project["angle_count"] = angle_count["count"] if angle_count else 0

            # Total phrases across all angles
            total = conn.execute(
                "SELECT SUM(total_phrases) as total FROM project_angles WHERE project_id = ?",
                (row["id"],),
            ).fetchone()
            project["total_phrases"] = total["total"] or 0 if total else 0
            results.append(project)
        return results
    finally:
        conn.close()


def get_research_project(project_id: int) -> Optional[dict[str, Any]]:
    """Get a project with all its angles and their details."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT * FROM research_projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return None
        project = dict(row)

        angles = conn.execute(
            "SELECT * FROM project_angles WHERE project_id = ? ORDER BY id",
            (project_id,),
        ).fetchall()
        project["angles"] = []
        for a in angles:
            angle_dict = dict(a)
            angle_dict["search_queries"] = json.loads(angle_dict["search_queries"] or "[]")
            angle_dict["scrape_ids"] = json.loads(angle_dict["scrape_ids"] or "[]")
            project["angles"].append(angle_dict)

        return project
    finally:
        conn.close()


def update_research_project(
    project_id: int,
    name: Optional[str] = None,
    niche: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Update a research project's basic info."""
    conn = _init_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        existing = conn.execute("SELECT * FROM research_projects WHERE id = ?", (project_id,)).fetchone()
        if not existing:
            return None

        conn.execute(
            "UPDATE research_projects SET name=?, niche=?, description=?, updated_at=? WHERE id=?",
            (
                name if name is not None else existing["name"],
                niche if niche is not None else existing["niche"],
                description if description is not None else existing["description"],
                now, project_id,
            ),
        )

        # If niche changed, regenerate all angle queries
        new_niche = niche if niche is not None else existing["niche"]
        if niche is not None and niche != existing["niche"]:
            angles = conn.execute("SELECT * FROM project_angles WHERE project_id = ?", (project_id,)).fetchall()
            for a in angles:
                queries = generate_search_queries(new_niche, a["angle_type"], a["custom_keywords"])
                conn.execute(
                    "UPDATE project_angles SET search_queries=? WHERE id=?",
                    (json.dumps(queries), a["id"]),
                )

        conn.commit()
        return get_research_project(project_id)
    finally:
        conn.close()


def delete_research_project(project_id: int) -> bool:
    """Delete a project and all its angles."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT id FROM research_projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM research_projects WHERE id = ?", (project_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def add_project_angle(project_id: int, angle_type: str, custom_keywords: str = "") -> Optional[dict[str, Any]]:
    """Add a new angle to an existing project."""
    conn = _init_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        project = conn.execute("SELECT niche FROM research_projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            return None

        queries = generate_search_queries(project["niche"], angle_type, custom_keywords)
        conn.execute(
            "INSERT INTO project_angles (project_id, angle_type, custom_keywords, search_queries, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, angle_type, custom_keywords, json.dumps(queries), now),
        )
        conn.commit()
        return get_research_project(project_id)
    finally:
        conn.close()


def remove_project_angle(angle_id: int) -> bool:
    """Remove an angle from a project."""
    conn = _init_db()
    try:
        row = conn.execute("SELECT id FROM project_angles WHERE id = ?", (angle_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM project_angles WHERE id = ?", (angle_id,))
        conn.commit()
        return True
    finally:
        conn.close()


async def run_project_angle(
    angle_id: int,
    max_threads: int = 5,
    subreddits: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Run a single angle — execute its search queries and scrape results.

    Updates the angle's scrape_ids and total_phrases in the DB.
    """
    conn = _init_db()
    try:
        angle = conn.execute("SELECT * FROM project_angles WHERE id = ?", (angle_id,)).fetchone()
        if not angle:
            raise ValueError(f"Angle {angle_id} not found")

        project = conn.execute("SELECT * FROM research_projects WHERE id = ?", (angle["project_id"],)).fetchone()
        if not project:
            raise ValueError(f"Project not found for angle {angle_id}")

        queries = json.loads(angle["search_queries"] or "[]")
        if not queries:
            raise ValueError("No search queries for this angle")

        # Mark as running
        conn.execute("UPDATE project_angles SET status='running' WHERE id=?", (angle_id,))
        conn.execute(
            "UPDATE research_projects SET status='running', updated_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), project["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    # Run searches (outside DB connection)
    all_scrape_ids: list[int] = []
    total_phrases = 0

    for query in queries[:10]:  # Cap at 10 queries per angle to avoid rate limits
        try:
            result = await search_and_scrape(
                query=query,
                subreddits=subreddits,
                sort="relevance",
                time_filter="month",
                max_threads=max_threads,
                search_limit=10,
            )
            if result.get("scrape_ids"):
                all_scrape_ids.extend(result["scrape_ids"])
                total_phrases += result.get("total_phrases", 0)
        except Exception:
            logger.exception("Failed query for angle %d: %s", angle_id, query)
            continue

    # Update angle with results
    conn = _init_db()
    try:
        # Merge with existing scrape_ids
        existing = conn.execute("SELECT scrape_ids FROM project_angles WHERE id = ?", (angle_id,)).fetchone()
        existing_ids = json.loads(existing["scrape_ids"] or "[]") if existing else []
        merged_ids = list(set(existing_ids + all_scrape_ids))

        conn.execute(
            "UPDATE project_angles SET status='complete', scrape_ids=?, total_phrases=? WHERE id=?",
            (json.dumps(merged_ids), total_phrases, angle_id),
        )

        # Check if all angles are complete
        project_id = angle["project_id"]
        pending = conn.execute(
            "SELECT COUNT(*) as count FROM project_angles WHERE project_id=? AND status != 'complete'",
            (project_id,),
        ).fetchone()
        if pending and pending["count"] == 0:
            conn.execute(
                "UPDATE research_projects SET status='complete', updated_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), project_id),
            )
        else:
            conn.execute(
                "UPDATE research_projects SET updated_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), project_id),
            )

        conn.commit()
    finally:
        conn.close()

    return {
        "angle_id": angle_id,
        "queries_run": min(len(queries), 10),
        "scrape_ids": all_scrape_ids,
        "total_phrases": total_phrases,
    }
