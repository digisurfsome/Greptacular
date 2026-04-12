"""
Market Scraper Router
=====================

FastAPI router for scraping Reddit threads and categorizing user
phrasings into pain points, desires, feature requests, validation
signals, and social proof — useful for ad copy, social media content,
and product validation.
"""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.market_scraper_service import (
    ANGLE_TYPES,
    DEFAULT_SUBREDDITS,
    SORT_OPTIONS,
    TIME_FILTERS,
    add_project_angle,
    categorize_comments,
    create_research_project,
    delete_research_project,
    delete_scrape,
    export_phrases_csv,
    get_phrase_frequencies,
    get_research_project,
    get_scrape,
    list_research_projects,
    list_scrapes,
    query_phrases,
    remove_project_angle,
    run_project_angle,
    save_scrape,
    scrape_reddit_thread,
    search_and_scrape,
    search_reddit,
    update_research_project,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market-scraper", tags=["market-scraper"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Request body for topic-based Reddit search + scrape."""
    query: str = Field(..., description="Search terms (e.g., 'app maker frustrations')")
    subreddits: list[str] = Field(default=[], description="Subreddits to search (empty = all of Reddit)")
    sort: str = Field(default="relevance", description="Sort: relevance, hot, top, new, comments")
    time_filter: str = Field(default="week", description="Time: all, year, month, week, day, hour")
    max_threads: int = Field(default=5, ge=1, le=20, description="Max threads to scrape")


class ScrapeRequest(BaseModel):
    """Request body for scraping a Reddit thread."""
    url: str = Field(..., description="Full Reddit thread URL")


class PhraseOut(BaseModel):
    """A single categorized phrase from a Reddit comment."""
    id: int
    scrape_id: int
    raw_text: str
    author: str
    score: int
    category: str
    subcategory: str
    ad_hook: str
    social_post_idea: str
    validation_signal: int
    created_at: str


class ScrapeOut(BaseModel):
    """A scrape record with its phrases and summary stats."""
    id: int
    url: str
    subreddit: str
    title: str
    scraped_at: str
    phrases: list[PhraseOut] = []
    category_counts: dict[str, int] = {}
    total_phrases: int = 0


class ScrapeSummaryOut(BaseModel):
    """A scrape listing without full phrase details."""
    id: int
    url: str
    subreddit: str
    title: str
    scraped_at: str
    category_counts: dict[str, int] = {}
    total_phrases: int = 0


class PhraseQueryOut(BaseModel):
    """A phrase result with scrape context attached."""
    id: int
    scrape_id: int
    raw_text: str
    author: str
    score: int
    category: str
    subcategory: str
    ad_hook: str
    social_post_idea: str
    validation_signal: int
    created_at: str
    scrape_url: str = ""
    subreddit: str = ""
    scrape_title: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/search-options")
async def get_search_options():
    """Return available sort options, time filters, and default subreddits."""
    return {
        "sort_options": list(SORT_OPTIONS),
        "time_filters": list(TIME_FILTERS),
        "default_subreddits": DEFAULT_SUBREDDITS,
    }


@router.post("/search")
async def search_topics(req: SearchRequest):
    """Search Reddit for threads matching a topic, without scraping.

    Returns thread summaries so the user can pick which ones to scrape.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    try:
        results = await search_reddit(
            query=req.query.strip(),
            subreddits=req.subreddits or None,
            sort=req.sort,
            time_filter=req.time_filter,
            limit=25,
        )
    except Exception:
        logger.exception("Search failed for '%s'", req.query)
        raise HTTPException(status_code=500, detail="Reddit search failed")

    return {"query": req.query, "threads": results}


@router.post("/search-and-scrape")
async def search_and_scrape_topics(req: SearchRequest):
    """Search Reddit for a topic, auto-scrape the top threads, and categorize everything.

    This is the "one-click" topic research endpoint.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")

    try:
        result = await search_and_scrape(
            query=req.query.strip(),
            subreddits=req.subreddits or None,
            sort=req.sort,
            time_filter=req.time_filter,
            max_threads=req.max_threads,
        )
    except Exception:
        logger.exception("Search-and-scrape failed for '%s'", req.query)
        raise HTTPException(status_code=500, detail="Search and scrape failed")

    return result


@router.post("/scrape", response_model=ScrapeOut)
async def scrape_thread(req: ScrapeRequest):
    """Scrape a Reddit thread, categorize all comments, and store results."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Basic URL validation
    if "reddit.com" not in url.lower():
        raise HTTPException(status_code=400, detail="URL must be a Reddit thread URL")

    try:
        thread_data = await scrape_reddit_thread(url)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 404:
            raise HTTPException(status_code=404, detail="Reddit thread not found")
        elif status == 429:
            raise HTTPException(status_code=429, detail="Reddit rate limit hit — try again in a minute")
        else:
            logger.error("Reddit HTTP error %d for %s", status, url)
            raise HTTPException(status_code=502, detail=f"Reddit returned HTTP {status}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Reddit request timed out")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error scraping %s", url)
        raise HTTPException(status_code=500, detail="Failed to scrape thread")

    # Categorize all extracted comments
    categorized = categorize_comments(
        thread_data["comments"],
        thread_data["subreddit"],
    )

    # Also categorize the post body if substantial
    post_body = thread_data.get("post_body", "")
    if post_body and len(post_body) >= 20:
        post_as_comment = [{
            "author": "OP",
            "body": post_body,
            "score": 0,
            "created_utc": 0,
        }]
        categorized_post = categorize_comments(post_as_comment, thread_data["subreddit"])
        categorized = categorized_post + categorized

    # Save to database
    result = save_scrape(
        url=thread_data["url"],
        subreddit=thread_data["subreddit"],
        title=thread_data["title"],
        categorized_comments=categorized,
    )

    logger.info(
        "Scrape complete: r/%s — %d phrases categorized",
        thread_data["subreddit"],
        len(categorized),
    )

    return result


@router.get("/scrapes", response_model=list[ScrapeSummaryOut])
async def get_all_scrapes():
    """List all past scrapes with summary stats."""
    return list_scrapes()


@router.get("/scrapes/{scrape_id}", response_model=ScrapeOut)
async def get_scrape_detail(scrape_id: int):
    """Get a specific scrape with all its categorized phrases."""
    result = get_scrape(scrape_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scrape not found")
    return result


@router.get("/phrases", response_model=list[PhraseQueryOut])
async def get_phrases(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_score: Optional[int] = Query(None, description="Minimum Reddit score"),
    min_validation: Optional[int] = Query(None, description="Minimum validation signal (1-5)"),
):
    """Query phrases across all scrapes with optional filters."""
    return query_phrases(
        category=category,
        min_score=min_score,
        min_validation=min_validation,
    )


@router.delete("/scrapes/{scrape_id}")
async def remove_scrape(scrape_id: int):
    """Delete a scrape and all its phrases."""
    deleted = delete_scrape(scrape_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scrape not found")
    return {"status": "deleted", "scrape_id": scrape_id}


@router.get("/export/{scrape_id}")
async def export_scrape_csv(scrape_id: int):
    """Export all phrases for a scrape as a downloadable CSV file."""
    csv_content = export_phrases_csv(scrape_id)
    if csv_content is None:
        raise HTTPException(status_code=404, detail="Scrape not found")

    import io

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=market_scrape_{scrape_id}.csv"},
    )


@router.get("/phrase-frequency")
async def get_phrase_frequency(
    scrape_ids: Optional[str] = Query(None, description="Comma-separated scrape IDs (empty = all)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    top_n: int = Query(50, ge=1, le=200, description="Number of top phrases to return"),
    min_ngram: int = Query(2, ge=2, le=5, description="Min words per phrase"),
    max_ngram: int = Query(4, ge=2, le=6, description="Max words per phrase"),
):
    """Get the most frequently used multi-word phrases across scraped comments.

    Returns phrases ranked by frequency — the exact language your market uses.
    Useful for ad copy, social media messaging, and understanding how real
    people describe their problems.
    """
    parsed_ids: Optional[list[int]] = None
    if scrape_ids:
        try:
            parsed_ids = [int(x.strip()) for x in scrape_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="scrape_ids must be comma-separated integers")

    results = get_phrase_frequencies(
        scrape_ids=parsed_ids,
        min_ngram=min_ngram,
        max_ngram=max_ngram,
        top_n=top_n,
        category=category,
    )
    return {"phrases": results, "total": len(results)}


# ---------------------------------------------------------------------------
# Research Project models
# ---------------------------------------------------------------------------


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name")
    niche: str = Field(..., description="Target niche (e.g., 'SEO agency')")
    description: str = Field(default="", description="Optional description")
    angles: list[dict] = Field(default=[], description="List of {type, custom_keywords}")


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    niche: Optional[str] = None
    description: Optional[str] = None


class AngleAddRequest(BaseModel):
    angle_type: str = Field(..., description="Angle type: discovery, desire, pain_point, validation, workflow, education")
    custom_keywords: str = Field(default="", description="Comma-separated custom keywords")


class RunAngleRequest(BaseModel):
    max_threads: int = Field(default=3, ge=1, le=10, description="Max threads to scrape per query")
    subreddits: list[str] = Field(default=[], description="Subreddits to search (empty = all)")


# ---------------------------------------------------------------------------
# Research Project endpoints
# ---------------------------------------------------------------------------


@router.get("/angle-types")
async def get_angle_types():
    """Get all available angle types with descriptions and seed phrases."""
    return {
        "angle_types": {
            k: {"label": v["label"], "description": v["description"]}
            for k, v in ANGLE_TYPES.items()
        }
    }


@router.post("/projects")
async def create_project(req: ProjectCreateRequest):
    """Create a new research project with optional angles."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    if not req.niche.strip():
        raise HTTPException(status_code=400, detail="Niche is required")
    result = create_research_project(
        name=req.name.strip(),
        niche=req.niche.strip(),
        description=req.description,
        angles=req.angles,
    )
    return result


@router.get("/projects")
async def get_projects():
    """List all research projects."""
    return list_research_projects()


@router.get("/projects/{project_id}")
async def get_project_detail(project_id: int):
    """Get a research project with all angles."""
    result = get_research_project(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.patch("/projects/{project_id}")
async def update_project(project_id: int, req: ProjectUpdateRequest):
    """Update a research project."""
    result = update_research_project(
        project_id=project_id,
        name=req.name,
        niche=req.niche,
        description=req.description,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a research project and all its angles."""
    deleted = delete_research_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted", "project_id": project_id}


@router.post("/projects/{project_id}/angles")
async def add_angle(project_id: int, req: AngleAddRequest):
    """Add a new angle to a project."""
    if req.angle_type not in ANGLE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid angle type. Must be one of: {', '.join(ANGLE_TYPES.keys())}",
        )
    result = add_project_angle(project_id, req.angle_type, req.custom_keywords)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.delete("/angles/{angle_id}")
async def delete_angle(angle_id: int):
    """Remove an angle from a project."""
    deleted = remove_project_angle(angle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Angle not found")
    return {"status": "deleted", "angle_id": angle_id}


@router.post("/angles/{angle_id}/run")
async def run_angle(angle_id: int, req: RunAngleRequest):
    """Execute a single angle — runs its search queries and scrapes results."""
    try:
        result = await run_project_angle(
            angle_id=angle_id,
            max_threads=req.max_threads,
            subreddits=req.subreddits or None,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        logger.exception("Failed to run angle %d", angle_id)
        raise HTTPException(status_code=500, detail="Failed to run angle")


@router.post("/projects/{project_id}/run-all")
async def run_all_angles(project_id: int, req: RunAngleRequest):
    """Run ALL angles for a project sequentially."""
    project = get_research_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = []
    for angle in project.get("angles", []):
        try:
            result = await run_project_angle(
                angle_id=angle["id"],
                max_threads=req.max_threads,
                subreddits=req.subreddits or None,
            )
            results.append(result)
        except Exception:
            logger.exception("Failed angle %d in project %d", angle["id"], project_id)
            results.append({"angle_id": angle["id"], "error": "failed"})

    return {"project_id": project_id, "results": results}
