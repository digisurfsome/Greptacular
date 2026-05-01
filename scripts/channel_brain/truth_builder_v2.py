#!/usr/bin/env python3
"""
truth_builder_v2.py — Channel Brain Builder (v2)
=================================================
Single-command 4-sweep pipeline:

  Sweep 0: Taxonomy Discovery  → taxonomy.json
  Sweep 1: Verbatim Extraction → extractions/*.jsonl  (1 per video)
  Sweep 2: Dual-Method Cluster → clusters.json
  Sweep 3: Render              → truth_document.md + sections/

Usage:
  # Connor channel (full run):
  python truth_builder_v2.py --config scripts/channel_brain/connor.json

  # Smoke test (5 videos only):
  python truth_builder_v2.py --config scripts/channel_brain/connor.json --limit 5

  # Dry run (no API calls):
  python truth_builder_v2.py --config scripts/channel_brain/connor.json --dry-run

  # Run only one sweep:
  python truth_builder_v2.py --config scripts/channel_brain/connor.json --sweep 0
  python truth_builder_v2.py --config scripts/channel_brain/connor.json --sweep 1

  # Reset and start over:
  python truth_builder_v2.py --config scripts/channel_brain/connor.json --reset

Setup (new channel):
  1. Copy scripts/channel_brain/config.example.json → scripts/channel_brain/my-channel.json
  2. Set "videos_dir" and "output_dir" in the JSON
  3. python truth_builder_v2.py --config scripts/channel_brain/my-channel.json

First run pauses after Sweep 0 (Taxonomy Gate) so you can review/edit taxonomy.json
before extraction starts. Disable with "taxonomy_gate": false in config.

IMPORTANT: uses subscription auth (no API key). Run: claude login  before first use.
"""

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

# Add directory to path for sibling imports
sys.path.insert(0, str(Path(__file__).parent))

from _claude import load_config, cleanup_scratch

import sweep0_taxonomy as s0
import sweep1_extract  as s1
import sweep2_cluster  as s2
import sweep3_render   as s3


# =============================================================================
# BANNER
# =============================================================================

def print_banner(cfg: dict) -> None:
    w = 68
    name    = cfg.get("project_name", "unnamed")
    videos  = cfg.get("videos_dir", "?")
    output  = cfg.get("output_dir", "?")
    cmode   = cfg.get("cluster_mode", "dual")
    tmode   = cfg.get("taxonomy_mode", "auto")
    tgate   = "yes" if cfg.get("taxonomy_gate", True) else "no"
    print("─" * w)
    print(f"  Channel Brain Builder v2  —  {name}")
    print(f"  Videos:   {videos}")
    print(f"  Output:   {output}")
    print(f"  Cluster:  {cmode}  |  Taxonomy: {tmode}  |  Gate: {tgate}")
    print("─" * w)


# =============================================================================
# MAIN
# =============================================================================

async def main() -> None:
    ap = argparse.ArgumentParser(
        description="Channel Brain Builder v2 — 4-sweep pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--config",   required=True,    help="Path to config JSON (copy config.example.json)")
    ap.add_argument("--sweep",    type=int, default=None, choices=[0, 1, 2, 3],
                    help="Run only this sweep (0-3). Skips others.")
    ap.add_argument("--limit",    type=int, default=None,
                    help="Limit Sweep 1 to first N pending videos (smoke test)")
    ap.add_argument("--dry-run",  action="store_true",
                    help="Show what would run — no API calls, no file writes")
    ap.add_argument("--reset",    action="store_true",
                    help="Delete all output for this project and start over")
    args = ap.parse_args()

    cfg        = load_config(args.config)
    output_dir = Path(cfg["output_dir"])

    if args.reset:
        if output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"Reset: wiped {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    print_banner(cfg)
    full_run = args.sweep is None  # True = run all 4 sweeps

    try:
        # ── Sweep 0: Taxonomy Discovery ──────────────────────────────────────
        if full_run or args.sweep == 0:
            print("\n[SWEEP 0]  Taxonomy Discovery")
            taxonomy = await s0.run(cfg, dry_run=args.dry_run)
            cats = taxonomy.get("categories", [])
            print(f"  → {len(cats)} categories:")
            for c in cats:
                print(f"      {c['name']}")

            # Taxonomy gate: pause before Sweep 1 so user can review/edit
            gate_flag = output_dir / "_sweep0_gate_passed"
            if (
                full_run
                and not args.dry_run
                and cfg.get("taxonomy_gate", True)
                and not gate_flag.exists()
            ):
                taxonomy_path = output_dir / "taxonomy.json"
                print()
                print("  ┌─ TAXONOMY GATE ───────────────────────────────────────────────────────────┐")
                print("  │  Sweep 0 complete. Open taxonomy.json, review the category list above.    │")
                print("  │  You can ADD, REMOVE, or RENAME categories before extraction starts.      │")
                print("  │  Each category becomes a section in your final truth document.            │")
                print(f"  │  File: {str(taxonomy_path)}  │")
                print("  │  Press Enter when ready to begin extraction (Sweep 1).                   │")
                print("  └───────────────────────────────────────────────────────────────────────────┘")
                input("  > ")
                gate_flag.write_text("passed", encoding="utf-8")
                # Reload taxonomy in case user edited it
                if taxonomy_path.exists():
                    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))

        else:
            # Need taxonomy for Sweep 1+
            taxonomy_path = output_dir / "taxonomy.json"
            if taxonomy_path.exists():
                taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
            else:
                print("ERROR: taxonomy.json not found — run Sweep 0 first.")
                print(f"  Expected: {taxonomy_path}")
                sys.exit(1)

        # ── Sweep 1: Verbatim Extraction ─────────────────────────────────────
        if full_run or args.sweep == 1:
            print("\n[SWEEP 1]  Verbatim Extraction")
            count = await s1.run(cfg, taxonomy, limit=args.limit, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"  → {count} total extractions")

        # ── Sweep 2: Dual-Method Clustering ──────────────────────────────────
        if full_run or args.sweep == 2:
            print("\n[SWEEP 2]  Clustering")
            clusters = await s2.run(cfg, dry_run=args.dry_run)
            if not args.dry_run and clusters:
                print(
                    f"  → {clusters.get('cluster_count', 0)} clusters, "
                    f"{clusters.get('singleton_count', 0)} singletons"
                )

        # ── Sweep 3: Render ───────────────────────────────────────────────────
        if full_run or args.sweep == 3:
            print("\n[SWEEP 3]  Render")
            result = s3.run(cfg)
            if result:
                print(f"  → {result.get('sections', 0)} sections rendered")

        # ── Done ──────────────────────────────────────────────────────────────
        print()
        print("─" * 68)
        if args.dry_run:
            print("  DRY RUN complete — no changes made")
        else:
            print(f"  DONE  —  output at: {output_dir}")
            truth_doc = output_dir / "truth_document.md"
            if truth_doc.exists():
                size_kb = truth_doc.stat().st_size // 1024
                print(f"  Truth doc: {truth_doc}  ({size_kb} KB)")
        print("─" * 68)

    finally:
        cleanup_scratch()


if __name__ == "__main__":
    asyncio.run(main())
