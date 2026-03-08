#!/usr/bin/env python3
"""
Intake Engine - The brain of the App Factory Car Wash.

Reads raw ideas from factory/inbox/, analyzes each one using Claude,
and routes them to the correct pipeline stage(s).

Usage:
    python factory/engine/intake.py              # Dry run - show recommendations
    python factory/engine/intake.py --auto-mount  # Actually mount ideas to stages
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FACTORY_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = FACTORY_ROOT / "inbox"
PIPELINE_DIR = FACTORY_ROOT / "pipeline"
MOUNTED_DIR = FACTORY_ROOT / "mounted"

# Pipeline stages in order. The directory names are the source of truth.
STAGE_DIRS = sorted(
    [d for d in PIPELINE_DIR.iterdir() if d.is_dir() and d.name[0].isdigit()],
    key=lambda d: d.name,
)

STAGE_NAMES = [d.name for d in STAGE_DIRS]

# File extensions the engine will read from the inbox
READABLE_EXTENSIONS = {".txt", ".md", ".markdown", ".text", ".rst"}

# The Claude model to use for analysis
MODEL = "claude-sonnet-4-20250514"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MountedIdea:
    """An idea already mounted in a pipeline stage."""

    stage: str
    filename: str
    content: str


@dataclass
class Recommendation:
    """A routing recommendation for a single inbox item."""

    inbox_file: str
    core_concept: str
    target_stages: list[str]
    overlap_pct: int  # 0-100
    overlap_with: str | None  # filename of overlapping mounted idea
    new_gold: str  # what's actually new beyond the overlap
    action: str  # "mount", "merge", "split"
    merge_target: str | None  # filename to merge with, if action == "merge"
    split_parts: list[dict[str, str]] | None  # list of {stage, content} for splits
    reasoning: str


@dataclass
class IntakeReport:
    """Full report from running the intake engine."""

    inbox_count: int
    already_mounted_count: int
    recommendations: list[Recommendation] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)  # stages with nothing mounted


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


def read_inbox_items() -> dict[str, str]:
    """Read all files from the inbox directory. Returns {filename: content}."""
    items: dict[str, str] = {}
    if not INBOX_DIR.exists():
        return items

    for f in INBOX_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in READABLE_EXTENSIONS:
            try:
                items[f.name] = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"  [WARN] Could not read {f.name} - skipping (not valid UTF-8)")
    return items


def read_mounted_ideas() -> list[MountedIdea]:
    """Read everything already mounted in each pipeline stage's prompts/ folder."""
    mounted: list[MountedIdea] = []
    for stage_dir in STAGE_DIRS:
        prompts_dir = stage_dir / "prompts"
        if not prompts_dir.exists():
            continue
        for f in prompts_dir.iterdir():
            if f.is_file() and f.suffix.lower() in READABLE_EXTENSIONS:
                try:
                    content = f.read_text(encoding="utf-8")
                    mounted.append(MountedIdea(stage=stage_dir.name, filename=f.name, content=content))
                except UnicodeDecodeError:
                    pass
    return mounted


def find_gaps(mounted: list[MountedIdea]) -> list[str]:
    """Find pipeline stages that have no mounted ideas."""
    stages_with_content = {m.stage for m in mounted}
    return [name for name in STAGE_NAMES if name not in stages_with_content]


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------


def build_analysis_prompt(inbox_item: str, inbox_filename: str, mounted: list[MountedIdea]) -> str:
    """Build the prompt for Claude to analyze a single inbox item."""

    # Summarize what's already in each stage
    stage_summaries: list[str] = []
    for stage_name in STAGE_NAMES:
        stage_items = [m for m in mounted if m.stage == stage_name]
        if stage_items:
            items_text = "\n".join(
                f"  - {m.filename}: {m.content[:200]}{'...' if len(m.content) > 200 else ''}" for m in stage_items
            )
            stage_summaries.append(f"### {stage_name}\n{items_text}")
        else:
            stage_summaries.append(f"### {stage_name}\n  (empty - nothing mounted yet)")

    mounted_context = "\n\n".join(stage_summaries)

    return f"""You are the routing engine for an app factory pipeline. Your job is to analyze a raw idea
and decide where it belongs in the pipeline.

## The Pipeline Stages

{chr(10).join(f"- {name}" for name in STAGE_NAMES)}

## What's Already Mounted in Each Stage

{mounted_context}

## The New Idea to Analyze

**Filename:** {inbox_filename}

**Content:**
{inbox_item}

## Your Task

Analyze this idea and return a JSON object with these fields:

{{
    "core_concept": "One sentence describing the core concept or technique",
    "target_stages": ["stage-name-1", "stage-name-2"],
    "overlap_pct": 0-100,
    "overlap_with": "filename of overlapping mounted idea, or null",
    "new_gold": "What's genuinely new that isn't already captured",
    "action": "mount | merge | split",
    "merge_target": "filename to merge with (if action is merge), or null",
    "split_parts": [
        {{"stage": "stage-name", "summary": "What to mount at this stage"}}
    ],
    "reasoning": "Why you made this decision"
}}

Rules:
- "mount" = place as-is into the target stage(s)
- "merge" = combine with an existing mounted idea (specify merge_target)
- "split" = this idea contains parts for multiple stages (specify split_parts)
- overlap_pct is how much this overlaps with already-mounted content (0 = totally new)
- new_gold is the genuinely new insight even if there IS overlap
- target_stages must use exact stage directory names from the list above
- split_parts should only be provided when action is "split"

Return ONLY the JSON object, no markdown fences, no explanation outside the JSON."""


def analyze_idea(
    client: anthropic.Anthropic,
    inbox_content: str,
    inbox_filename: str,
    mounted: list[MountedIdea],
) -> Recommendation:
    """Use Claude to analyze a single inbox item and produce a routing recommendation."""

    prompt = build_analysis_prompt(inbox_content, inbox_filename, mounted)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the text response
    response_text = ""
    for block in response.content:
        if block.type == "text":
            response_text += block.text

    # Parse JSON from the response (handle potential markdown fences)
    json_text = response_text.strip()
    if json_text.startswith("```"):
        # Strip markdown fences
        lines = json_text.split("\n")
        json_text = "\n".join(lines[1:-1])

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        # If Claude didn't return clean JSON, create a fallback recommendation
        print(f"  [WARN] Could not parse Claude's response for {inbox_filename}: {e}")
        return Recommendation(
            inbox_file=inbox_filename,
            core_concept="(parse error - manual review needed)",
            target_stages=["01-idea-intake"],
            overlap_pct=0,
            overlap_with=None,
            new_gold=inbox_content[:200],
            action="mount",
            merge_target=None,
            split_parts=None,
            reasoning=f"Automatic fallback: Claude response could not be parsed. Raw: {response_text[:300]}",
        )

    return Recommendation(
        inbox_file=inbox_filename,
        core_concept=data.get("core_concept", ""),
        target_stages=data.get("target_stages", ["01-idea-intake"]),
        overlap_pct=data.get("overlap_pct", 0),
        overlap_with=data.get("overlap_with"),
        new_gold=data.get("new_gold", ""),
        action=data.get("action", "mount"),
        merge_target=data.get("merge_target"),
        split_parts=data.get("split_parts"),
        reasoning=data.get("reasoning", ""),
    )


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_report(report: IntakeReport) -> str:
    """Format the intake report for terminal output."""
    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("  APP FACTORY - INTAKE ENGINE REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"  Inbox items found:       {report.inbox_count}")
    lines.append(f"  Already mounted ideas:   {report.already_mounted_count}")
    lines.append(f"  Pipeline gaps:           {len(report.gaps)} stages empty")
    lines.append("")

    if report.gaps:
        lines.append("  EMPTY STAGES (gaps in your pipeline):")
        for gap in report.gaps:
            lines.append(f"    - {gap}")
        lines.append("")

    if not report.recommendations:
        lines.append("  No inbox items to process. Drop some ideas in factory/inbox/!")
        lines.append("=" * 70)
        return "\n".join(lines)

    lines.append("-" * 70)
    lines.append("  RECOMMENDATIONS")
    lines.append("-" * 70)

    for i, rec in enumerate(report.recommendations, 1):
        lines.append("")
        lines.append(f"  [{i}] {rec.inbox_file}")
        lines.append(f"      Concept:  {rec.core_concept}")
        lines.append(f"      Action:   {rec.action.upper()}")
        lines.append(f"      Target:   {', '.join(rec.target_stages)}")

        if rec.overlap_pct > 0:
            lines.append(f"      Overlap:  {rec.overlap_pct}% with '{rec.overlap_with}'")
            lines.append(f"      New gold: {rec.new_gold}")

        if rec.action == "merge" and rec.merge_target:
            lines.append(f"      Merge with: {rec.merge_target}")

        if rec.action == "split" and rec.split_parts:
            lines.append("      Split into:")
            for part in rec.split_parts:
                lines.append(f"        - {part.get('stage', '?')}: {part.get('summary', '?')}")

        lines.append(f"      Reasoning: {rec.reasoning}")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_intake(auto_mount: bool = False) -> IntakeReport:
    """
    Main entry point. Reads the inbox, analyzes each item, and produces a report.
    If auto_mount is True, also mounts the ideas using the mounter.
    """
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY environment variable is not set.")
        print("  Set it with: export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n  Reading inbox...")
    inbox_items = read_inbox_items()

    print("  Reading mounted ideas...")
    mounted = read_mounted_ideas()

    print(f"  Found {len(inbox_items)} inbox item(s), {len(mounted)} mounted idea(s)")

    gaps = find_gaps(mounted)

    report = IntakeReport(
        inbox_count=len(inbox_items),
        already_mounted_count=len(mounted),
        gaps=gaps,
    )

    if not inbox_items:
        print(format_report(report))
        return report

    # Analyze each inbox item
    for filename, content in inbox_items.items():
        print(f"  Analyzing: {filename}...")
        rec = analyze_idea(client, content, filename, mounted)
        report.recommendations.append(rec)

    # Print the report
    print(format_report(report))

    # Auto-mount if requested
    if auto_mount and report.recommendations:
        print("\n  AUTO-MOUNT: Mounting ideas to pipeline stages...")
        # Import mounter here to avoid circular imports
        from factory.engine.mounter import execute_recommendations

        execute_recommendations(report.recommendations)
        print("  Done! Check the pipeline stages for your mounted ideas.")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="App Factory Intake Engine - Analyze and route raw ideas to pipeline stages",
    )
    parser.add_argument(
        "--auto-mount",
        action="store_true",
        help="Actually mount ideas to pipeline stages (default is dry run / report only)",
    )
    args = parser.parse_args()
    run_intake(auto_mount=args.auto_mount)


if __name__ == "__main__":
    main()
