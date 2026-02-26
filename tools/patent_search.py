#!/usr/bin/env python3
"""
Patent Prior Art Search Tool
=============================

Searches the PatentsView API for patents related to a given invention description,
then saves and summarizes the results.

Usage:
    python tools/patent_search.py "description of invention"
    python tools/patent_search.py --file path/to/description.txt
    python tools/patent_search.py --file desc.txt --claims-file tools/my_claims.txt

Environment:
    PATENTSVIEW_API_KEY  - API key for PatentsView (optional; tries without key first)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Try to use 'requests' for cleaner HTTP handling; fall back to urllib
# ---------------------------------------------------------------------------
try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PATENTSVIEW_V1_URL = "https://search.patentsview.org/api/v1/patent/"

# Fields to request from the API
PATENT_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_date",
    "patent_abstract",
    "patent_type",
]

# Default output path (relative to this script)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "patent_results.json"

# Maximum results per query (API cap is 1000)
RESULTS_PER_QUERY = 100

# Delay between API calls to stay under the 45 req/min rate limit
API_DELAY_SECONDS = 1.5

# Search queries: each tuple is (label, search_terms)
# These are designed to cast a wide net around the patent's core concepts.
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
# HTTP helpers
# ---------------------------------------------------------------------------

def _post_requests(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    """POST using the requests library."""
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()  # type: ignore[no-any-return]


def _post_urllib(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    """POST using urllib from the standard library."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)  # type: ignore[no-any-return]


def post_json(url: str, payload: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
    """
    Send a POST request with JSON body. Uses requests if available, otherwise urllib.
    Adds the PatentsView API key header when provided.
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-Api-Key"] = api_key

    if _HAS_REQUESTS:
        return _post_requests(url, payload, headers)
    return _post_urllib(url, payload, headers)


# ---------------------------------------------------------------------------
# PatentsView API interaction
# ---------------------------------------------------------------------------

def search_patents_v1(
    terms: str,
    api_key: str | None = None,
    size: int = RESULTS_PER_QUERY,
) -> dict[str, Any]:
    """
    Search the PatentsView v1 API for patents whose abstract matches the
    given terms (using _text_any for broad matching).
    """
    payload: dict[str, Any] = {
        "q": {"_text_any": {"patent_abstract": terms}},
        "f": PATENT_FIELDS,
        "o": {"size": size},
        "s": [{"patent_date": "desc"}],
    }
    return post_json(PATENTSVIEW_V1_URL, payload, api_key=api_key)


def run_single_search(
    label: str,
    terms: str,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """
    Execute one search query and return the list of patent results.
    Handles errors gracefully so one failing query does not abort the batch.
    """
    print(f"  Searching: {label} ...", end=" ", flush=True)
    try:
        data = search_patents_v1(terms, api_key=api_key)
        patents = data.get("patents", [])
        total = data.get("total_hits", len(patents))
        print(f"OK  ({len(patents)} returned, {total} total hits)")
        return patents
    except (requests.RequestException if _HAS_REQUESTS else Exception) as exc:
        print(f"FAILED ({exc})")
        return []
    except (HTTPError, URLError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"FAILED ({exc})")
        return []


def run_all_searches(
    extra_queries: list[tuple[str, str]] | None = None,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """
    Run all configured search queries plus any extras, deduplicate results,
    and return the merged list sorted by date descending.
    """
    queries = list(SEARCH_QUERIES)
    if extra_queries:
        queries.extend(extra_queries)

    all_patents: dict[str, dict[str, Any]] = {}  # keyed by patent_id to deduplicate
    total_raw = 0

    for i, (label, terms) in enumerate(queries):
        results = run_single_search(label, terms, api_key=api_key)
        total_raw += len(results)
        for patent in results:
            pid = patent.get("patent_id", "")
            if pid and pid not in all_patents:
                all_patents[pid] = patent

        # Rate-limit politeness (skip delay after the last query)
        if i < len(queries) - 1:
            time.sleep(API_DELAY_SECONDS)

    # Sort by date descending (most recent first)
    merged = sorted(
        all_patents.values(),
        key=lambda p: p.get("patent_date", ""),
        reverse=True,
    )

    print(f"\n  Raw results: {total_raw}  |  After dedup: {len(merged)}")
    return merged


# ---------------------------------------------------------------------------
# Query generation from description text
# ---------------------------------------------------------------------------

def generate_extra_queries(description: str) -> list[tuple[str, str]]:
    """
    Generate additional search queries by extracting key phrases from the
    user-supplied description. This is a simple keyword extraction approach
    that supplements the hardcoded queries.
    """
    # Normalize whitespace
    text = " ".join(description.split()).lower()

    # Keyword groups relevant to AI context management patents
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

    extra: list[tuple[str, str]] = []
    found_groups: list[str] = []

    for group_name, keywords in keyword_groups:
        for kw in keywords:
            if kw in text:
                found_groups.append(group_name)
                break

    # Build pairwise queries from detected keyword groups
    for i in range(len(found_groups)):
        for j in range(i + 1, min(i + 3, len(found_groups))):
            label = f"(auto) {found_groups[i]} + {found_groups[j]}"
            terms = f"{found_groups[i]} {found_groups[j]} artificial intelligence"
            extra.append((label, terms))

    return extra[:8]  # Cap at 8 additional queries to keep runtime reasonable


# ---------------------------------------------------------------------------
# Output and display
# ---------------------------------------------------------------------------

def save_results(patents: list[dict[str, Any]], output_path: Path, metadata: dict[str, Any]) -> None:
    """Save the full results and metadata to a JSON file."""
    payload = {
        "search_metadata": metadata,
        "result_count": len(patents),
        "patents": patents,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def print_summary(patents: list[dict[str, Any]], max_display: int = 25) -> None:
    """Print a human-readable summary of the search results."""
    if not patents:
        print("\n  No patents found.")
        return

    print(f"\n{'=' * 80}")
    print(f"  PRIOR ART SEARCH RESULTS  ({len(patents)} unique patents)")
    print(f"{'=' * 80}")

    # Date range
    dates = [p.get("patent_date", "") for p in patents if p.get("patent_date")]
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")

    # Type breakdown
    types: dict[str, int] = {}
    for p in patents:
        ptype = p.get("patent_type", "unknown")
        types[ptype] = types.get(ptype, 0) + 1
    if types:
        breakdown = ", ".join(f"{k}: {v}" for k, v in sorted(types.items()))
        print(f"  Types: {breakdown}")

    print(f"\n  Showing top {min(max_display, len(patents))} results:\n")

    for i, patent in enumerate(patents[:max_display], 1):
        pid = patent.get("patent_id", "N/A")
        title = patent.get("patent_title", "No title")
        date = patent.get("patent_date", "N/A")
        abstract = patent.get("patent_abstract", "")

        # Truncate abstract for display
        if abstract and len(abstract) > 200:
            abstract = abstract[:197] + "..."

        print(f"  [{i:>3}] Patent {pid}  ({date})")
        print(f"        {title}")
        if abstract:
            # Indent wrapped abstract text
            wrapped = textwrap.fill(abstract, width=72, initial_indent="        ", subsequent_indent="        ")
            print(wrapped)
        print()

    if len(patents) > max_display:
        print(f"  ... and {len(patents) - max_display} more (see JSON output for full list)")


def print_claims_context(claims_text: str) -> None:
    """Print the user's claims for reference alongside results."""
    print(f"\n{'=' * 80}")
    print("  YOUR PATENT CLAIMS (for comparison)")
    print(f"{'=' * 80}")
    # Show first ~40 lines to keep terminal output manageable
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
        description="Search PatentsView for prior art related to an invention description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python tools/patent_search.py "AI context window management through file-based persistence"
              python tools/patent_search.py --file docs/invention.txt
              python tools/patent_search.py --file docs/invention.txt --claims-file tools/my_claims.txt
              python tools/patent_search.py --file docs/invention.txt --output results.json
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
    # Resolve API key
    # -----------------------------------------------------------------------
    api_key = args.api_key or os.environ.get("PATENTSVIEW_API_KEY")
    if api_key:
        print("Using PatentsView API key from", "argument" if args.api_key else "environment")
    else:
        print("No API key provided. Attempting requests without authentication.")
        print("  (Set PATENTSVIEW_API_KEY or use --api-key if you get 401/403 errors)\n")

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
    # Generate extra queries from the description
    # -----------------------------------------------------------------------
    extra_queries = generate_extra_queries(description)
    total_queries = len(SEARCH_QUERIES) + len(extra_queries)
    print(f"\nRunning {total_queries} search queries ({len(SEARCH_QUERIES)} built-in + {len(extra_queries)} auto-generated)...\n")

    # -----------------------------------------------------------------------
    # Execute searches
    # -----------------------------------------------------------------------
    start_time = time.time()
    patents = run_all_searches(extra_queries=extra_queries, api_key=api_key)
    elapsed = time.time() - start_time
    print(f"  Search completed in {elapsed:.1f}s")

    # -----------------------------------------------------------------------
    # Save results
    # -----------------------------------------------------------------------
    output_path = Path(args.output)
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "description_length": len(description),
        "description_preview": description[:500] + ("..." if len(description) > 500 else ""),
        "queries_run": total_queries,
        "api_key_used": bool(api_key),
        "elapsed_seconds": round(elapsed, 1),
    }
    save_results(patents, output_path, metadata)

    # -----------------------------------------------------------------------
    # Display results
    # -----------------------------------------------------------------------
    if claims_text:
        print_claims_context(claims_text)

    print_summary(patents, max_display=args.max_display)

    # -----------------------------------------------------------------------
    # Quick relevance notes
    # -----------------------------------------------------------------------
    if patents:
        print(f"{'=' * 80}")
        print("  NEXT STEPS")
        print(f"{'=' * 80}")
        print("  1. Review the JSON output for full abstracts and details")
        print(f"     {output_path}")
        print("  2. Look for patents that describe:")
        print("     - File-based output redirection for AI agents")
        print("     - Context window management through persistent state")
        print("     - Session bridge/handoff mechanisms for LLMs")
        print("     - Idle/holding patterns for API session reuse")
        print("     - Tiered context safety thresholds")
        print("  3. For each relevant patent, check its claims at:")
        print("     https://patents.google.com/patent/US{patent_id}")
        print()


if __name__ == "__main__":
    main()
