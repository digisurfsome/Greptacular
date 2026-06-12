#!/usr/bin/env python3
"""
purge_video.py — Remove specific videos from call_miner output by video ID.

Uses the video registry (_video_registry.json) to identify videos, then
removes their exchanges from JSONL files, updates the registry, and
optionally re-renders the output.

Usage:
  python purge_video.py --config scripts/call_miner/connor-calls.json --list
  python purge_video.py --config scripts/call_miner/connor-calls.json --remove V003 V007
  python purge_video.py --config scripts/call_miner/connor-calls.json --remove V003 --dry-run
  python purge_video.py --config scripts/call_miner/connor-calls.json --remove V003 --force
  python purge_video.py --config scripts/call_miner/connor-calls.json --remove V003 --re-render

IMPORTANT: subscription auth. Run `claude login` before first use (only needed for --re-render).
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Pop at import — prevents CLAUDECODE=1 poisoning nested claude processes
os.environ.pop("CLAUDECODE", None)

# Shared utilities from channel_brain
sys.path.insert(0, str(Path(__file__).parent.parent / "channel_brain"))
from _claude import load_config

# Import registry + report helpers from call_miner (same directory)
sys.path.insert(0, str(Path(__file__).parent))
from call_miner import (
    load_video_registry,
    save_video_registry,
    write_video_report,
)


def print_registry_table(registry: dict) -> None:
    """Print the video registry as a formatted table."""
    if not registry:
        print("  (empty registry)")
        return

    print()
    print("  | ID   | Title                                                  | Confidence   | Exchanges |")
    print("  |------|--------------------------------------------------------|--------------|-----------|")

    for vid, entry in sorted(registry.items(), key=lambda kv: kv[0]):
        title = (entry.get("title") or entry.get("folder", ""))[:56].ljust(56)
        conf  = entry.get("confidence") or "pending"
        if conf == "uncertain":
            conf_display = "uncertain"
        else:
            conf_display = conf
        exch = entry.get("exchange_count", 0)
        print(f"  | {vid} | {title} | {conf_display:<12} | {exch:<9} |")

    print()
    total = len(registry)
    purged = sum(1 for e in registry.values() if e.get("confidence") == "purged")
    active = total - purged
    print(f"  {total} total videos ({active} active, {purged} purged)")


def count_exchanges_by_video(exchanges_dir: Path) -> dict[str, int]:
    """Count exchanges per video_id across all JSONL files."""
    counts: dict[str, int] = {}
    if not exchanges_dir.exists():
        return counts

    for jf in sorted(exchanges_dir.glob("*.jsonl")):
        for line in jf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
                vid = ex.get("video_id", "")
                if vid:
                    counts[vid] = counts.get(vid, 0) + 1
            except json.JSONDecodeError:
                pass
    return counts


def purge_exchanges(exchanges_dir: Path, remove_ids: set[str], dry_run: bool = False) -> dict[str, int]:
    """Remove exchanges matching video_ids from all JSONL files.

    Returns dict of {video_id: count_removed}.
    """
    removed_counts: dict[str, int] = {}
    if not exchanges_dir.exists():
        return removed_counts

    for jf in sorted(exchanges_dir.glob("*.jsonl")):
        original_lines = jf.read_text(encoding="utf-8", errors="replace").splitlines()
        kept: list[str] = []
        for line in original_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                ex = json.loads(stripped)
                vid = ex.get("video_id", "")
                if vid in remove_ids:
                    removed_counts[vid] = removed_counts.get(vid, 0) + 1
                    continue
            except json.JSONDecodeError:
                pass
            kept.append(stripped)

        if dry_run:
            continue

        if not kept:
            # File is now empty — delete it
            jf.unlink()
        else:
            jf.write_text("\n".join(kept) + "\n", encoding="utf-8")

    return removed_counts


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Purge videos from call_miner output by video ID"
    )
    ap.add_argument("--config", required=True, help="Path to config JSON")
    ap.add_argument("--list", action="store_true", help="Print registry table and exit")
    ap.add_argument("--remove", nargs="+", metavar="VID", help="Video IDs to remove (e.g. V003 V007)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be removed without changing files")
    ap.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    ap.add_argument("--re-render", action="store_true", help="Re-run Sweep 2+3 after purge")
    args = ap.parse_args()

    cfg = load_config(args.config)
    output_dir = Path(cfg["output_dir"])
    exchanges_dir = output_dir / "exchanges"

    registry = load_video_registry(output_dir)

    if not registry:
        print("ERROR: No video registry found. Run call_miner.py first.")
        sys.exit(1)

    # --list: print table and exit
    if args.list:
        print(f"\n  Video Registry — {cfg.get('project_name', 'unnamed')}")
        print_registry_table(registry)
        return

    # --remove: purge specified videos
    if not args.remove:
        print("ERROR: specify --list or --remove VID [VID ...]")
        sys.exit(1)

    # Normalize IDs to uppercase
    remove_ids = {vid.upper() for vid in args.remove}

    # Validate all IDs exist in registry
    unknown = remove_ids - set(registry.keys())
    if unknown:
        print(f"ERROR: unknown video IDs: {', '.join(sorted(unknown))}")
        print("  Use --list to see all video IDs")
        sys.exit(1)

    # Show what will be purged
    print(f"\n  Videos to purge ({len(remove_ids)}):")
    exchange_counts = count_exchanges_by_video(exchanges_dir)
    total_to_remove = 0
    for vid in sorted(remove_ids):
        entry = registry[vid]
        count = exchange_counts.get(vid, 0)
        total_to_remove += count
        title = (entry.get("title") or entry.get("folder", ""))[:60]
        conf = entry.get("confidence") or "pending"
        print(f"    {vid} - {title} ({conf}, {count} exchanges)")

    print(f"\n  Total exchanges to remove: {total_to_remove}")

    if args.dry_run:
        print("\n  DRY RUN — no files changed")
        # Still show per-file impact
        removed = purge_exchanges(exchanges_dir, remove_ids, dry_run=True)
        if removed:
            print("  Would remove:")
            for vid, count in sorted(removed.items()):
                print(f"    {vid}: {count} exchanges")
        return

    # Confirmation
    if not args.force:
        answer = input("\n  Confirm purge? (y/N) ").strip().lower()
        if answer != "y":
            print("  Cancelled.")
            return

    # Purge exchanges from JSONL files
    print("\n  Purging exchanges...", flush=True)
    removed = purge_exchanges(exchanges_dir, remove_ids)
    for vid, count in sorted(removed.items()):
        print(f"    {vid}: removed {count} exchanges")

    # Delete clusters.json (stale after removal)
    clusters_path = output_dir / "clusters.json"
    if clusters_path.exists():
        clusters_path.unlink()
        print("  Deleted clusters.json (stale after purge)")

    # Update registry: mark purged videos
    for vid in remove_ids:
        registry[vid]["confidence"] = "purged"
        registry[vid]["confidence_reason"] = "purged by purge_video.py"
        registry[vid]["exchange_count"] = 0
    save_video_registry(output_dir, registry)
    print("  Updated video registry")

    # Update video report
    write_video_report(cfg, registry)

    print(f"\n  Purge complete. Removed {sum(removed.values())} exchanges from {len(removed)} videos.")

    # Re-render if requested
    if args.re_render:
        print("\n  Re-rendering (Sweep 2 + 3)...")
        # Import and run sweeps — these need async
        from call_miner import sweep2_cluster, sweep3_render
        async def _rerender():
            clusters = await sweep2_cluster(cfg)
            if clusters:
                print(f"  Sweep 2: {clusters.get('cluster_count', 0)} clusters")
            result = sweep3_render(cfg)
            if result:
                print(f"  Sweep 3: {result.get('sections', 0)} interaction-type files")
        asyncio.run(_rerender())
        print("  Re-render complete.")


if __name__ == "__main__":
    main()
