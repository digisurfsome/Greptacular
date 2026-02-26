#!/usr/bin/env python3
"""
Patent Prior Art Search Tool
=============================

Searches the PatentsView API for patents related to a given invention description,
then saves and summarizes the results. Falls back to generating Google Patents
search URLs when the API is unavailable.

Usage:
    python tools/patent_search.py "description of invention"
    python tools/patent_search.py --file path/to/description.txt
    python tools/patent_search.py --file desc.txt --claims-file tools/my_claims.txt

Environment:
    PATENTSVIEW_API_KEY  - Required for PatentsView API access (free, request at
                           https://patentsview.org/apis/keyrequest)
    LENS_API_TOKEN       - Optional token for Lens.org API fallback
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Try to use 'requests' for cleaner HTTP handling; fall back to urllib
# ---------------------------------------------------------------------------
try:
    import requests as _requests_lib

    _HAS_REQUESTS = True
except ImportError:
    _requests_lib = None  # type: ignore[assignment]
    _HAS_REQUESTS = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PATENTSVIEW_V1_URL = "https://search.patentsview.org/api/v1/patent/"
LENS_API_URL = "https://api.lens.org/patent/search"
GOOGLE_PATENTS_URL = "https://patents.google.com/"

# Fields to request from PatentsView
PATENTSVIEW_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_date",
    "patent_abstract",
    "patent_type",
]

# Default output path (relative to this script)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "patent_results.json"

# Maximum results per query
RESULTS_PER_QUERY = 100

# Delay between API calls to respect rate limits (45 req/min for PatentsView)
API_DELAY_SECONDS = 1.5

# Search queries: each tuple is (label, search_terms).
# Designed to cast a wide net around AI context window management concepts.
SEARCH_QUERIES: list[tuple[str, str]] = [
    ("context window + file system + language model",
     "context window file system language model"),
    ("token reduction + AI agent + file",
     "token reduction AI agent file output"),
    ("session persistence + language model",
     "session persistence language model continuity"),
    ("output redirection + artificial intelligence",
     "output redirection artificial intelligence agent"),
    ("context management + LLM",
     "context management large language model token"),
    ("context window + state persistence",
     "context window state persistence structured file"),
    ("AI agent + bridge + session continuity",
     "AI agent bridge session continuity handoff"),
    ("idle engine + API session + holding pattern",
     "idle engine API session holding pattern token cost"),
    ("context compaction + recovery + language model",
     "context compaction recovery language model summarization"),
    ("bidirectional communication + AI agent + file protocol",
     "bidirectional communication AI agent file protocol"),
    ("context window degradation + attention",
     "context window degradation attention dilution token"),
    ("file-based memory + AI agent",
     "file-based memory AI agent persistent working memory"),
]


# ---------------------------------------------------------------------------
# HTTP helpers — support both 'requests' and stdlib 'urllib'
# ---------------------------------------------------------------------------

def _build_ssl_context() -> ssl.SSLContext:
    """
    Build an SSL context that tries system certs first, then falls back to
    an unverified context if CA bundles are missing (common in sandboxes).
    """
    ctx = ssl.create_default_context()
    try:
        # Test if we can actually verify anything
        ctx.load_default_certs()
    except Exception:
        pass
    return ctx


def _post_with_requests(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any]:
    """POST using the requests library."""
    assert _requests_lib is not None
    resp = _requests_lib.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


def _post_with_urllib(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> dict[str, Any]:
    """POST using urllib from the standard library."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    ctx = _build_ssl_context()
    with urlopen(req, timeout=30, context=ctx) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)  # type: ignore[no-any-return]


def post_json(
    url: str,
    payload: dict[str, Any],
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Send a POST request with a JSON body. Uses 'requests' if available,
    otherwise falls back to urllib.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    if _HAS_REQUESTS:
        return _post_with_requests(url, payload, headers)
    return _post_with_urllib(url, payload, headers)


# ---------------------------------------------------------------------------
# PatentsView v1 API
# ---------------------------------------------------------------------------

def search_patentsview(
    terms: str,
    api_key: str,
    size: int = RESULTS_PER_QUERY,
) -> dict[str, Any]:
    """
    Search the PatentsView v1 API for patents whose abstract matches the
    given terms (using _text_any for broad matching).

    Requires an API key (free, request at https://patentsview.org/apis/keyrequest).
    """
    payload: dict[str, Any] = {
        "q": {"_text_any": {"patent_abstract": terms}},
        "f": PATENTSVIEW_FIELDS,
        "o": {"size": size},
        "s": [{"patent_date": "desc"}],
    }
    return post_json(
        PATENTSVIEW_V1_URL,
        payload,
        extra_headers={"X-Api-Key": api_key},
    )


def normalize_patentsview_result(patent: dict[str, Any]) -> dict[str, Any]:
    """Normalize a PatentsView result into the common output schema."""
    return {
        "patent_id": patent.get("patent_id", ""),
        "title": patent.get("patent_title", ""),
        "date": patent.get("patent_date", ""),
        "abstract": patent.get("patent_abstract", ""),
        "type": patent.get("patent_type", ""),
        "source": "patentsview",
        "url": f"https://patents.google.com/patent/US{patent.get('patent_id', '')}",
    }


# ---------------------------------------------------------------------------
# Lens.org API (fallback)
# ---------------------------------------------------------------------------

def search_lens(
    terms: str,
    token: str,
    size: int = RESULTS_PER_QUERY,
) -> dict[str, Any]:
    """
    Search the Lens.org patent API. Requires an access token (free for
    non-commercial/academic use; request at https://www.lens.org/lens/api).
    """
    payload: dict[str, Any] = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": terms,
                            "fields": ["title", "abstract", "claims"],
                            "default_operator": "or",
                        }
                    }
                ],
                "filter": [
                    {"term": {"jurisdiction": "US"}},
                ],
            }
        },
        "size": size,
        "sort": [{"date_published": "desc"}],
        "include": ["lens_id", "doc_number", "title", "abstract", "date_published", "publication_type"],
    }
    return post_json(
        LENS_API_URL,
        payload,
        extra_headers={"Authorization": f"Bearer {token}"},
    )


def normalize_lens_result(patent: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Lens.org result into the common output schema."""
    # Lens returns title as an object with 'text' key in some responses
    title = patent.get("title", "")
    if isinstance(title, dict):
        title = title.get("text", "")
    elif isinstance(title, list) and title:
        title = title[0].get("text", "") if isinstance(title[0], dict) else str(title[0])

    abstract = patent.get("abstract", "")
    if isinstance(abstract, dict):
        abstract = abstract.get("text", "")
    elif isinstance(abstract, list) and abstract:
        abstract = abstract[0].get("text", "") if isinstance(abstract[0], dict) else str(abstract[0])

    doc_number = patent.get("doc_number", "")
    lens_id = patent.get("lens_id", "")
    date_published = patent.get("date_published", "")

    return {
        "patent_id": doc_number or lens_id,
        "title": title,
        "date": date_published,
        "abstract": abstract,
        "type": patent.get("publication_type", ""),
        "source": "lens",
        "url": f"https://www.lens.org/lens/patent/{lens_id}" if lens_id else "",
    }


# ---------------------------------------------------------------------------
# Google Patents URL generation (no-API fallback)
# ---------------------------------------------------------------------------

def generate_google_patents_urls(queries: list[tuple[str, str]]) -> list[dict[str, str]]:
    """
    Generate Google Patents search URLs for each query. These can be opened
    in a browser when no API access is available.
    """
    urls: list[dict[str, str]] = []
    for label, terms in queries:
        encoded = quote_plus(terms)
        url = f"{GOOGLE_PATENTS_URL}?q={encoded}&oq={encoded}"
        urls.append({"label": label, "terms": terms, "url": url})
    return urls


# ---------------------------------------------------------------------------
# Search dispatcher — tries PatentsView, then Lens, then Google URLs
# ---------------------------------------------------------------------------

def run_single_search(
    label: str,
    terms: str,
    api_key: str | None = None,
    lens_token: str | None = None,
) -> list[dict[str, Any]]:
    """
    Execute one search query against the best available API and return
    normalized patent results. Handles errors gracefully so one failing
    query does not abort the entire batch.
    """
    print(f"  [{label}]", end=" ", flush=True)

    # Attempt 1: PatentsView v1 (preferred)
    if api_key:
        try:
            data = search_patentsview(terms, api_key)
            patents = data.get("patents", [])
            total = data.get("total_hits", len(patents))
            normalized = [normalize_patentsview_result(p) for p in patents]
            print(f"PatentsView OK ({len(normalized)} results, {total} total)")
            return normalized
        except Exception as exc:
            print(f"PatentsView failed ({_short_error(exc)})", end=" ", flush=True)

    # Attempt 2: Lens.org
    if lens_token:
        try:
            data = search_lens(terms, lens_token)
            patents = data.get("data", [])
            total = data.get("total", len(patents))
            normalized = [normalize_lens_result(p) for p in patents]
            print(f"Lens OK ({len(normalized)} results, {total} total)")
            return normalized
        except Exception as exc:
            print(f"Lens failed ({_short_error(exc)})", end=" ", flush=True)

    # No API available or all attempts failed
    print("SKIPPED (no API key)")
    return []


def _short_error(exc: Exception) -> str:
    """Return a short string representation of an error for log output."""
    msg = str(exc)
    if len(msg) > 120:
        msg = msg[:117] + "..."
    return f"{type(exc).__name__}: {msg}"


def run_all_searches(
    extra_queries: list[tuple[str, str]] | None = None,
    api_key: str | None = None,
    lens_token: str | None = None,
) -> list[dict[str, Any]]:
    """
    Run all configured search queries plus any extras, deduplicate results,
    and return the merged list sorted by date descending.
    """
    queries = list(SEARCH_QUERIES)
    if extra_queries:
        queries.extend(extra_queries)

    # Keyed by patent_id to deduplicate across queries
    all_patents: dict[str, dict[str, Any]] = {}
    total_raw = 0

    for i, (label, terms) in enumerate(queries):
        results = run_single_search(label, terms, api_key=api_key, lens_token=lens_token)
        total_raw += len(results)
        for patent in results:
            pid = patent.get("patent_id", "")
            if pid and pid not in all_patents:
                all_patents[pid] = patent

        # Rate-limit politeness (skip delay after the last query)
        if i < len(queries) - 1 and (api_key or lens_token):
            time.sleep(API_DELAY_SECONDS)

    # Sort by date descending (most recent first)
    merged = sorted(
        all_patents.values(),
        key=lambda p: p.get("date", ""),
        reverse=True,
    )

    print(f"\n  Raw results: {total_raw}  |  After dedup: {len(merged)}")
    return merged


# ---------------------------------------------------------------------------
# Query generation from description text
# ---------------------------------------------------------------------------

def generate_extra_queries(description: str) -> list[tuple[str, str]]:
    """
    Generate additional search queries by extracting key concept groups from
    the user-supplied description. Builds pairwise combinations of detected
    concepts to supplement the hardcoded queries.
    """
    text = " ".join(description.split()).lower()

    # Keyword groups relevant to AI context management patents.
    # Each group has a canonical label and trigger phrases.
    keyword_groups: list[tuple[str, list[str]]] = [
        ("context window", ["context window", "context length", "token limit", "token window"]),
        ("file system", ["file system", "filesystem", "file-based", "persistent file"]),
        ("language model", ["language model", "llm", "large language model", "neural network"]),
        ("session", ["session persistence", "session continuity", "session management"]),
        ("output", ["output redirection", "output redirect", "response redirect"]),
        ("memory", ["working memory", "persistent memory", "state persistence"]),
        ("bridge", ["bridge mechanism", "bridge file", "handoff", "session handoff"]),
        ("idle", ["idle engine", "holding pattern", "heartbeat", "keep alive"]),
        ("compaction", ["compaction", "summarization", "context compression"]),
        ("token", ["token reduction", "token cost", "token budget", "token saving"]),
    ]

    found_groups: list[str] = []
    for group_name, keywords in keyword_groups:
        for kw in keywords:
            if kw in text:
                found_groups.append(group_name)
                break

    # Build pairwise queries from detected keyword groups
    extra: list[tuple[str, str]] = []
    for i in range(len(found_groups)):
        for j in range(i + 1, min(i + 3, len(found_groups))):
            label = f"(auto) {found_groups[i]} + {found_groups[j]}"
            terms = f"{found_groups[i]} {found_groups[j]} artificial intelligence"
            extra.append((label, terms))

    return extra[:8]  # Cap to keep runtime reasonable


# ---------------------------------------------------------------------------
# Output and display
# ---------------------------------------------------------------------------

def save_results(
    patents: list[dict[str, Any]],
    google_urls: list[dict[str, str]],
    output_path: Path,
    metadata: dict[str, Any],
) -> None:
    """Save the full results, Google Patents fallback URLs, and metadata to JSON."""
    payload = {
        "search_metadata": metadata,
        "result_count": len(patents),
        "patents": patents,
        "google_patents_urls": google_urls,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def print_summary(patents: list[dict[str, Any]], max_display: int = 25) -> None:
    """Print a human-readable summary of the search results."""
    if not patents:
        print("\n  No patents found via API.")
        return

    print(f"\n{'=' * 80}")
    print(f"  PRIOR ART SEARCH RESULTS  ({len(patents)} unique patents)")
    print(f"{'=' * 80}")

    # Date range
    dates = [p.get("date", "") for p in patents if p.get("date")]
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")

    # Source breakdown
    sources: dict[str, int] = {}
    for p in patents:
        src = p.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    if sources:
        breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(sources.items()))
        print(f"  Sources: {breakdown}")

    # Type breakdown
    types: dict[str, int] = {}
    for p in patents:
        ptype = p.get("type", "unknown")
        if ptype:
            types[ptype] = types.get(ptype, 0) + 1
    if types:
        breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(types.items()))
        print(f"  Types: {breakdown}")

    print(f"\n  Showing top {min(max_display, len(patents))} results:\n")

    for i, patent in enumerate(patents[:max_display], 1):
        pid = patent.get("patent_id", "N/A")
        title = patent.get("title", "No title")
        date = patent.get("date", "N/A")
        abstract = patent.get("abstract", "")
        url = patent.get("url", "")

        # Truncate abstract for display
        if abstract and len(abstract) > 200:
            abstract = abstract[:197] + "..."

        print(f"  [{i:>3}] {pid}  ({date})")
        print(f"        {title}")
        if abstract:
            wrapped = textwrap.fill(
                abstract, width=72,
                initial_indent="        ",
                subsequent_indent="        ",
            )
            print(wrapped)
        if url:
            print(f"        {url}")
        print()

    if len(patents) > max_display:
        remaining = len(patents) - max_display
        print(f"  ... and {remaining} more (see JSON output for full list)")


def print_google_urls(google_urls: list[dict[str, str]]) -> None:
    """Print Google Patents search URLs for manual searching."""
    print(f"\n{'=' * 80}")
    print("  GOOGLE PATENTS SEARCH URLS (open in browser)")
    print(f"{'=' * 80}")
    print("  Use these links to search Google Patents manually:\n")
    for i, entry in enumerate(google_urls, 1):
        print(f"  [{i:>2}] {entry['label']}")
        print(f"       {entry['url']}")
        print()


def print_claims_context(claims_text: str) -> None:
    """Print the user's claims for reference alongside results."""
    print(f"\n{'=' * 80}")
    print("  YOUR PATENT CLAIMS (for comparison)")
    print(f"{'=' * 80}")
    lines = claims_text.strip().splitlines()
    for line in lines[:40]:
        print(f"  {line}")
    if len(lines) > 40:
        print(f"\n  ... ({len(lines) - 40} more lines in claims file)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search for prior art patents related to an invention description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python tools/patent_search.py "AI context window management via file-based persistence"
              python tools/patent_search.py --file docs/invention.txt
              python tools/patent_search.py --file docs/invention.txt --claims-file tools/my_claims.txt
              python tools/patent_search.py --file docs/invention.txt --output results.json
              python tools/patent_search.py --file docs/invention.txt --api-key YOUR_KEY

            API keys:
              PatentsView (free): https://patentsview.org/apis/keyrequest
                Set PATENTSVIEW_API_KEY env var or use --api-key

              Lens.org (free for research): https://www.lens.org/lens/api
                Set LENS_API_TOKEN env var or use --lens-token

              No key? The tool still generates Google Patents search URLs
              you can open in a browser.
        """),
    )
    parser.add_argument(
        "description",
        nargs="?",
        default=None,
        help="Inline description of the invention to search for",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Path to a text file containing the invention description",
    )
    parser.add_argument(
        "--claims-file",
        type=str,
        default=None,
        help="Path to a file containing patent claims for comparison context",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help=f"Output path for JSON results (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="PatentsView API key (or set PATENTSVIEW_API_KEY env var)",
    )
    parser.add_argument(
        "--lens-token",
        type=str,
        default=None,
        help="Lens.org API token (or set LENS_API_TOKEN env var)",
    )
    parser.add_argument(
        "--max-display",
        type=int,
        default=25,
        help="Maximum number of results to display in terminal (default: 25)",
    )

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Resolve invention description
    # -----------------------------------------------------------------------
    description: str | None = args.description

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        description = file_path.read_text(encoding="utf-8")
        print(f"Read description from: {file_path} ({len(description)} chars)")

    if not description:
        parser.print_help()
        print("\nError: Provide a description as an argument or via --file.", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Resolve API credentials
    # -----------------------------------------------------------------------
    api_key = args.api_key or os.environ.get("PATENTSVIEW_API_KEY")
    lens_token = args.lens_token or os.environ.get("LENS_API_TOKEN")

    has_any_api = bool(api_key or lens_token)

    if api_key:
        print(f"PatentsView API key: {'(from --api-key)' if args.api_key else '(from env)'}")
    if lens_token:
        print(f"Lens.org API token: {'(from --lens-token)' if args.lens_token else '(from env)'}")
    if not has_any_api:
        print("No API keys provided.")
        print("  - PatentsView: set PATENTSVIEW_API_KEY or use --api-key")
        print("  - Lens.org:    set LENS_API_TOKEN or use --lens-token")
        print("  Falling back to Google Patents URL generation.\n")

    # -----------------------------------------------------------------------
    # Optionally load and display claims
    # -----------------------------------------------------------------------
    claims_text: str | None = None
    if args.claims_file:
        claims_path = Path(args.claims_file)
        if not claims_path.exists():
            print(f"Warning: Claims file not found: {claims_path}", file=sys.stderr)
        else:
            claims_text = claims_path.read_text(encoding="utf-8")
            print(f"Loaded claims from: {claims_path} ({len(claims_text)} chars)")

    # -----------------------------------------------------------------------
    # Generate extra queries from the description text
    # -----------------------------------------------------------------------
    extra_queries = generate_extra_queries(description)
    all_queries = list(SEARCH_QUERIES) + extra_queries
    total_queries = len(all_queries)
    print(f"\nPrepared {total_queries} search queries "
          f"({len(SEARCH_QUERIES)} built-in + {len(extra_queries)} auto-generated)")

    # -----------------------------------------------------------------------
    # Always generate Google Patents URLs (useful regardless of API access)
    # -----------------------------------------------------------------------
    google_urls = generate_google_patents_urls(all_queries)

    # -----------------------------------------------------------------------
    # Execute API searches (if credentials available)
    # -----------------------------------------------------------------------
    patents: list[dict[str, Any]] = []
    elapsed = 0.0

    if has_any_api:
        print(f"\nRunning {total_queries} API searches...\n")
        start_time = time.time()
        patents = run_all_searches(
            extra_queries=extra_queries,
            api_key=api_key,
            lens_token=lens_token,
        )
        elapsed = time.time() - start_time
        print(f"  Search completed in {elapsed:.1f}s")
    else:
        print("\nSkipping API searches (no credentials). See Google Patents URLs below.")

    # -----------------------------------------------------------------------
    # Save results (always includes Google URLs even if no API results)
    # -----------------------------------------------------------------------
    output_path = Path(args.output)
    metadata: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "description_length": len(description),
        "description_preview": description[:500] + ("..." if len(description) > 500 else ""),
        "queries_run": total_queries,
        "patentsview_key_used": bool(api_key),
        "lens_token_used": bool(lens_token),
        "elapsed_seconds": round(elapsed, 1),
    }
    save_results(patents, google_urls, output_path, metadata)

    # -----------------------------------------------------------------------
    # Display results
    # -----------------------------------------------------------------------
    if claims_text:
        print_claims_context(claims_text)

    if patents:
        print_summary(patents, max_display=args.max_display)

    # Always show Google Patents URLs as a supplement / fallback
    print_google_urls(google_urls)

    # -----------------------------------------------------------------------
    # Next steps guidance
    # -----------------------------------------------------------------------
    print(f"{'=' * 80}")
    print("  NEXT STEPS")
    print(f"{'=' * 80}")
    if patents:
        print(f"  1. Review the full JSON output: {output_path}")
        print("  2. Look for patents that describe:")
        print("     - File-based output redirection for AI agents")
        print("     - Context window management through persistent state")
        print("     - Session bridge/handoff mechanisms for LLMs")
        print("     - Idle/holding patterns for API session reuse")
        print("     - Tiered context safety thresholds")
        print("  3. For each relevant patent, examine its full claims at the URL shown")
    else:
        print("  1. Open the Google Patents URLs above in your browser")
        print("  2. Review the results for relevance to your claims")
        print("  3. For programmatic searching, get a free API key:")
        print("     PatentsView: https://patentsview.org/apis/keyrequest")
        print("     Lens.org:    https://www.lens.org/lens/api")
    print(f"  \n  Results file: {output_path}")
    print()


if __name__ == "__main__":
    main()
