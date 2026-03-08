#!/usr/bin/env python3
"""
Sorter - Deduplication, overlap detection, and gap analysis.

Scans all mounted ideas across pipeline stages and finds:
- Duplicates (same idea mounted in multiple stages)
- Overlaps (ideas that should be combined)
- Gaps (stages with nothing mounted)

Usage:
    python factory/engine/sorter.py                # Full analysis report
    python factory/engine/sorter.py --gaps-only    # Just show empty stages
    python factory/engine/sorter.py --json         # Output as JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field

import anthropic

from factory.engine.intake import (
    MODEL,
    STAGE_NAMES,
    MountedIdea,
    find_gaps,
    read_mounted_ideas,
)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DuplicateGroup:
    """A group of mounted ideas that appear to be duplicates or near-duplicates."""

    concept: str
    items: list[MountedIdea]
    similarity_pct: int  # 0-100
    recommendation: str  # "merge", "keep-both", "remove-one"


@dataclass
class OverlapPair:
    """Two mounted ideas that have significant overlap."""

    idea_a: MountedIdea
    idea_b: MountedIdea
    overlap_pct: int
    shared_concept: str
    recommendation: str


@dataclass
class SorterReport:
    """Full report from the sorter."""

    total_mounted: int
    stages_with_content: int
    stages_empty: int
    gaps: list[str] = field(default_factory=list)
    duplicates: list[DuplicateGroup] = field(default_factory=list)
    overlaps: list[OverlapPair] = field(default_factory=list)
    stage_summary: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def build_dedup_prompt(mounted: list[MountedIdea]) -> str:
    """Build a prompt for Claude to find duplicates and overlaps among mounted ideas."""

    items_text = ""
    for i, m in enumerate(mounted):
        items_text += f"\n### Item {i + 1}: [{m.stage}] {m.filename}\n"
        # Truncate long content to keep the prompt manageable
        content = m.content[:500] + ("..." if len(m.content) > 500 else "")
        items_text += content + "\n"

    return f"""You are analyzing mounted ideas in an app factory pipeline for duplicates and overlaps.

## All Mounted Ideas

{items_text}

## Your Task

Find any duplicates (same idea in different stages) and overlaps (ideas that share significant content).

Return a JSON object:

{{
    "duplicates": [
        {{
            "concept": "The shared concept",
            "items": [
                {{"stage": "stage-name", "filename": "file.md"}},
                {{"stage": "stage-name", "filename": "file.md"}}
            ],
            "similarity_pct": 85,
            "recommendation": "merge | keep-both | remove-one"
        }}
    ],
    "overlaps": [
        {{
            "idea_a": {{"stage": "stage-name", "filename": "file.md"}},
            "idea_b": {{"stage": "stage-name", "filename": "file.md"}},
            "overlap_pct": 40,
            "shared_concept": "What they share",
            "recommendation": "merge | keep-both"
        }}
    ]
}}

Rules:
- duplicates = 70%+ similarity (essentially the same idea)
- overlaps = 20-69% similarity (share some content but are distinct)
- If there are no duplicates or overlaps, return empty arrays
- Use exact stage names and filenames from the items above

Return ONLY the JSON object."""


def analyze_duplicates(client: anthropic.Anthropic, mounted: list[MountedIdea]) -> tuple[list[DuplicateGroup], list[OverlapPair]]:
    """Use Claude to find duplicates and overlaps among mounted ideas."""

    if len(mounted) < 2:
        return [], []

    prompt = build_dedup_prompt(mounted)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = ""
    for block in response.content:
        if block.type == "text":
            response_text += block.text

    # Parse JSON
    json_text = response_text.strip()
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        json_text = "\n".join(lines[1:-1])

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"  [WARN] Could not parse Claude's dedup response: {e}")
        return [], []

    # Build DuplicateGroup objects
    duplicates: list[DuplicateGroup] = []
    for dup_data in data.get("duplicates", []):
        items = []
        for item_ref in dup_data.get("items", []):
            # Find the matching MountedIdea
            for m in mounted:
                if m.stage == item_ref.get("stage") and m.filename == item_ref.get("filename"):
                    items.append(m)
                    break
        if len(items) >= 2:
            duplicates.append(DuplicateGroup(
                concept=dup_data.get("concept", ""),
                items=items,
                similarity_pct=dup_data.get("similarity_pct", 0),
                recommendation=dup_data.get("recommendation", "keep-both"),
            ))

    # Build OverlapPair objects
    overlaps: list[OverlapPair] = []
    for ov_data in data.get("overlaps", []):
        idea_a = idea_b = None
        a_ref = ov_data.get("idea_a", {})
        b_ref = ov_data.get("idea_b", {})
        for m in mounted:
            if m.stage == a_ref.get("stage") and m.filename == a_ref.get("filename"):
                idea_a = m
            if m.stage == b_ref.get("stage") and m.filename == b_ref.get("filename"):
                idea_b = m
        if idea_a and idea_b:
            overlaps.append(OverlapPair(
                idea_a=idea_a,
                idea_b=idea_b,
                overlap_pct=ov_data.get("overlap_pct", 0),
                shared_concept=ov_data.get("shared_concept", ""),
                recommendation=ov_data.get("recommendation", "keep-both"),
            ))

    return duplicates, overlaps


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_report(report: SorterReport) -> str:
    """Format the sorter report for terminal output."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("  APP FACTORY - SORTER REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Total mounted ideas:     {report.total_mounted}")
    lines.append(f"  Stages with content:     {report.stages_with_content}")
    lines.append(f"  Empty stages (gaps):     {report.stages_empty}")
    lines.append("")

    # Stage summary
    lines.append("  STAGE BREAKDOWN:")
    for stage_name in STAGE_NAMES:
        count = report.stage_summary.get(stage_name, 0)
        bar = "#" * count if count > 0 else "(empty)"
        lines.append(f"    {stage_name}: {bar} ({count})")
    lines.append("")

    # Gaps
    if report.gaps:
        lines.append("  GAPS - These stages need attention:")
        for gap in report.gaps:
            lines.append(f"    - {gap}")
        lines.append("")

    # Duplicates
    if report.duplicates:
        lines.append("-" * 70)
        lines.append("  DUPLICATES FOUND")
        lines.append("-" * 70)
        for i, dup in enumerate(report.duplicates, 1):
            lines.append(f"\n  [{i}] {dup.concept}")
            lines.append(f"      Similarity: {dup.similarity_pct}%")
            lines.append(f"      Recommendation: {dup.recommendation}")
            lines.append("      Items:")
            for item in dup.items:
                lines.append(f"        - [{item.stage}] {item.filename}")
        lines.append("")

    # Overlaps
    if report.overlaps:
        lines.append("-" * 70)
        lines.append("  OVERLAPS FOUND")
        lines.append("-" * 70)
        for i, ov in enumerate(report.overlaps, 1):
            lines.append(f"\n  [{i}] {ov.shared_concept}")
            lines.append(f"      Overlap: {ov.overlap_pct}%")
            lines.append(f"      A: [{ov.idea_a.stage}] {ov.idea_a.filename}")
            lines.append(f"      B: [{ov.idea_b.stage}] {ov.idea_b.filename}")
            lines.append(f"      Recommendation: {ov.recommendation}")
        lines.append("")

    if not report.duplicates and not report.overlaps:
        lines.append("  No duplicates or overlaps found. Pipeline is clean!")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def report_to_json(report: SorterReport) -> str:
    """Serialize the report to JSON."""
    return json.dumps(
        {
            "total_mounted": report.total_mounted,
            "stages_with_content": report.stages_with_content,
            "stages_empty": report.stages_empty,
            "gaps": report.gaps,
            "stage_summary": report.stage_summary,
            "duplicates": [
                {
                    "concept": d.concept,
                    "similarity_pct": d.similarity_pct,
                    "recommendation": d.recommendation,
                    "items": [{"stage": item.stage, "filename": item.filename} for item in d.items],
                }
                for d in report.duplicates
            ],
            "overlaps": [
                {
                    "shared_concept": o.shared_concept,
                    "overlap_pct": o.overlap_pct,
                    "recommendation": o.recommendation,
                    "idea_a": {"stage": o.idea_a.stage, "filename": o.idea_a.filename},
                    "idea_b": {"stage": o.idea_b.stage, "filename": o.idea_b.filename},
                }
                for o in report.overlaps
            ],
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_sorter(gaps_only: bool = False, output_json: bool = False) -> SorterReport:
    """Main entry point. Scans mounted ideas and produces a dedup/gap report."""

    mounted = read_mounted_ideas()
    gaps = find_gaps(mounted)

    # Count per stage
    stage_summary: dict[str, int] = {}
    for stage_name in STAGE_NAMES:
        stage_summary[stage_name] = sum(1 for m in mounted if m.stage == stage_name)

    stages_with_content = sum(1 for count in stage_summary.values() if count > 0)

    report = SorterReport(
        total_mounted=len(mounted),
        stages_with_content=stages_with_content,
        stages_empty=len(gaps),
        gaps=gaps,
        stage_summary=stage_summary,
    )

    # If only checking gaps, skip the Claude-based dedup analysis
    if not gaps_only and len(mounted) >= 2:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("[ERROR] ANTHROPIC_API_KEY not set. Use --gaps-only to skip AI analysis.")
            sys.exit(1)

        client = anthropic.Anthropic(api_key=api_key)
        print("  Analyzing mounted ideas for duplicates and overlaps...")
        report.duplicates, report.overlaps = analyze_duplicates(client, mounted)

    if output_json:
        print(report_to_json(report))
    else:
        print(format_report(report))

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="App Factory Sorter - Find duplicates, overlaps, and gaps in the pipeline",
    )
    parser.add_argument(
        "--gaps-only",
        action="store_true",
        help="Only show empty pipeline stages (no AI analysis needed)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )
    args = parser.parse_args()
    run_sorter(gaps_only=args.gaps_only, output_json=args.json)


if __name__ == "__main__":
    main()
