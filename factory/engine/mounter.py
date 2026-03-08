#!/usr/bin/env python3
"""
Mounter - Places ideas into the correct pipeline stage folders.

Handles:
- Mounting ideas to stage prompts/ directories
- Combining/merging ideas when they overlap
- Creating and updating manifest.json in each stage
- Manual mounting of a specific idea to a specific stage

Usage:
    python factory/engine/mounter.py --idea "my_idea.md" --stage 03-architecture
    python factory/engine/mounter.py --show-manifests
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from factory.engine.intake import (
    INBOX_DIR,
    STAGE_DIRS,
    STAGE_NAMES,
    Recommendation,
)

# ---------------------------------------------------------------------------
# Manifest management
# ---------------------------------------------------------------------------

MANIFEST_FILENAME = "manifest.json"


def load_manifest(stage_dir: Path) -> dict:
    """Load the manifest.json for a pipeline stage, creating it if it doesn't exist."""
    manifest_path = stage_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # Default manifest structure
    return {
        "stage": stage_dir.name,
        "last_updated": None,
        "items": [],
    }


def save_manifest(stage_dir: Path, manifest: dict) -> None:
    """Write the manifest.json for a pipeline stage."""
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    manifest_path = stage_dir / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def add_manifest_entry(
    stage_dir: Path,
    filename: str,
    source_file: str | None,
    action: str,
    reasoning: str,
    merged_with: str | None = None,
) -> None:
    """Add an entry to the stage manifest tracking what was mounted and why."""
    manifest = load_manifest(stage_dir)
    entry = {
        "filename": filename,
        "source": source_file,
        "action": action,
        "reasoning": reasoning,
        "mounted_at": datetime.now(timezone.utc).isoformat(),
    }
    if merged_with:
        entry["merged_with"] = merged_with
    manifest["items"].append(entry)
    save_manifest(stage_dir, manifest)


# ---------------------------------------------------------------------------
# Stage resolution
# ---------------------------------------------------------------------------


def resolve_stage_dir(stage_name: str) -> Path | None:
    """
    Find the pipeline stage directory matching a stage name.
    Accepts partial matches like '03' or '03-architecture'.
    """
    for stage_dir in STAGE_DIRS:
        if stage_dir.name == stage_name:
            return stage_dir
        # Allow matching by number prefix (e.g., "03" matches "03-architecture")
        if stage_dir.name.startswith(stage_name):
            return stage_dir
    return None


# ---------------------------------------------------------------------------
# Mounting operations
# ---------------------------------------------------------------------------


def mount_file_to_stage(
    source_path: Path,
    stage_dir: Path,
    reasoning: str = "Manual mount",
    action: str = "mount",
) -> Path:
    """
    Copy a file into a stage's prompts/ directory and update the manifest.
    Returns the path of the mounted file.
    """
    prompts_dir = stage_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    dest_path = prompts_dir / source_path.name

    # If a file with the same name already exists, add a suffix
    if dest_path.exists():
        stem = source_path.stem
        suffix = source_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = prompts_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.copy2(source_path, dest_path)
    add_manifest_entry(
        stage_dir=stage_dir,
        filename=dest_path.name,
        source_file=source_path.name,
        action=action,
        reasoning=reasoning,
    )

    print(f"    Mounted: {source_path.name} -> {stage_dir.name}/prompts/{dest_path.name}")
    return dest_path


def mount_content_to_stage(
    content: str,
    filename: str,
    stage_dir: Path,
    source_file: str | None = None,
    reasoning: str = "Generated from split",
    action: str = "split",
) -> Path:
    """
    Write content directly into a stage's prompts/ directory and update the manifest.
    Used for split operations where we create new files from parts of an idea.
    """
    prompts_dir = stage_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    dest_path = prompts_dir / filename

    # Handle name collisions
    if dest_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix or ".md"
        counter = 1
        while dest_path.exists():
            dest_path = prompts_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    dest_path.write_text(content, encoding="utf-8")
    add_manifest_entry(
        stage_dir=stage_dir,
        filename=dest_path.name,
        source_file=source_file,
        action=action,
        reasoning=reasoning,
    )

    print(f"    Mounted: {dest_path.name} -> {stage_dir.name}/prompts/")
    return dest_path


def merge_with_existing(
    source_path: Path,
    target_filename: str,
    stage_dir: Path,
    reasoning: str = "Merged with existing idea",
) -> Path | None:
    """
    Merge new content with an existing mounted file by appending.
    Returns the path of the merged file, or None if the target wasn't found.
    """
    prompts_dir = stage_dir / "prompts"
    target_path = prompts_dir / target_filename

    if not target_path.exists():
        # Try to find it in any stage
        for sd in STAGE_DIRS:
            candidate = sd / "prompts" / target_filename
            if candidate.exists():
                target_path = candidate
                stage_dir = sd
                break

    if not target_path.exists():
        print(f"    [WARN] Merge target '{target_filename}' not found. Mounting as new file instead.")
        return mount_file_to_stage(source_path, stage_dir, reasoning=reasoning, action="mount")

    # Read existing and new content
    existing_content = target_path.read_text(encoding="utf-8")
    new_content = source_path.read_text(encoding="utf-8")

    # Append with a clear separator
    merged = (
        existing_content.rstrip()
        + "\n\n"
        + "---\n"
        + f"## Merged from: {source_path.name}\n"
        + f"## Merged at: {datetime.now(timezone.utc).isoformat()}\n\n"
        + new_content
    )

    target_path.write_text(merged, encoding="utf-8")
    add_manifest_entry(
        stage_dir=stage_dir,
        filename=target_filename,
        source_file=source_path.name,
        action="merge",
        reasoning=reasoning,
        merged_with=target_filename,
    )

    print(f"    Merged: {source_path.name} into {stage_dir.name}/prompts/{target_filename}")
    return target_path


# ---------------------------------------------------------------------------
# Execute recommendations from the intake engine
# ---------------------------------------------------------------------------


def execute_recommendations(recommendations: list[Recommendation]) -> None:
    """
    Execute a list of recommendations from the intake engine.
    This is the auto-mount pathway.
    """
    for rec in recommendations:
        inbox_file = INBOX_DIR / rec.inbox_file
        if not inbox_file.exists():
            print(f"    [WARN] Inbox file '{rec.inbox_file}' not found, skipping.")
            continue

        if rec.action == "mount":
            # Mount to each target stage
            for stage_name in rec.target_stages:
                stage_dir = resolve_stage_dir(stage_name)
                if stage_dir:
                    mount_file_to_stage(
                        source_path=inbox_file,
                        stage_dir=stage_dir,
                        reasoning=rec.reasoning,
                        action="mount",
                    )
                else:
                    print(f"    [WARN] Unknown stage '{stage_name}', skipping.")

        elif rec.action == "merge":
            if rec.merge_target:
                # Find which stage the merge target is in
                stage_dir = resolve_stage_dir(rec.target_stages[0]) if rec.target_stages else None
                if stage_dir:
                    merge_with_existing(
                        source_path=inbox_file,
                        target_filename=rec.merge_target,
                        stage_dir=stage_dir,
                        reasoning=rec.reasoning,
                    )
                else:
                    print(f"    [WARN] No target stage for merge, skipping {rec.inbox_file}.")
            else:
                print(f"    [WARN] Merge action but no merge_target for {rec.inbox_file}, mounting instead.")
                for stage_name in rec.target_stages:
                    stage_dir = resolve_stage_dir(stage_name)
                    if stage_dir:
                        mount_file_to_stage(inbox_file, stage_dir, reasoning=rec.reasoning)

        elif rec.action == "split":
            if rec.split_parts:
                for part in rec.split_parts:
                    stage_name = part.get("stage", "")
                    summary = part.get("summary", "")
                    stage_dir = resolve_stage_dir(stage_name)
                    if stage_dir and summary:
                        # Create a file from the summary content
                        safe_name = rec.inbox_file.rsplit(".", 1)[0]
                        part_filename = f"{safe_name}_{stage_name.split('-', 1)[0]}.md"
                        mount_content_to_stage(
                            content=f"# Split from: {rec.inbox_file}\n\n{summary}",
                            filename=part_filename,
                            stage_dir=stage_dir,
                            source_file=rec.inbox_file,
                            reasoning=rec.reasoning,
                            action="split",
                        )
                    else:
                        print(f"    [WARN] Unknown stage '{stage_name}' in split, skipping part.")
            else:
                print(f"    [WARN] Split action but no split_parts for {rec.inbox_file}, mounting as-is.")
                for stage_name in rec.target_stages:
                    stage_dir = resolve_stage_dir(stage_name)
                    if stage_dir:
                        mount_file_to_stage(inbox_file, stage_dir, reasoning=rec.reasoning)


# ---------------------------------------------------------------------------
# Show manifests
# ---------------------------------------------------------------------------


def show_manifests() -> None:
    """Print the manifest for each pipeline stage."""
    print("=" * 70)
    print("  PIPELINE STAGE MANIFESTS")
    print("=" * 70)

    for stage_dir in STAGE_DIRS:
        manifest = load_manifest(stage_dir)
        items = manifest.get("items", [])
        print(f"\n  {stage_dir.name}")
        print(f"  Last updated: {manifest.get('last_updated', 'never')}")
        if items:
            for item in items:
                print(f"    - {item.get('filename', '?')} [{item.get('action', '?')}]")
                print(f"      Reason: {item.get('reasoning', 'N/A')[:80]}")
        else:
            print("    (no items mounted)")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Manual mount CLI
# ---------------------------------------------------------------------------


def manual_mount(idea_path: str, stage_name: str) -> None:
    """Mount a specific file to a specific stage via CLI."""
    source = Path(idea_path)

    # Try as relative to inbox first, then as absolute/relative path
    if not source.exists():
        inbox_candidate = INBOX_DIR / idea_path
        if inbox_candidate.exists():
            source = inbox_candidate
        else:
            print(f"[ERROR] File not found: {idea_path}")
            print(f"  Looked in: {source} and {inbox_candidate}")
            return

    stage_dir = resolve_stage_dir(stage_name)
    if not stage_dir:
        print(f"[ERROR] Unknown stage: {stage_name}")
        print(f"  Available stages: {', '.join(STAGE_NAMES)}")
        return

    mount_file_to_stage(
        source_path=source,
        stage_dir=stage_dir,
        reasoning=f"Manually mounted via CLI to {stage_name}",
        action="mount",
    )
    print("  Done!")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="App Factory Mounter - Mount ideas to pipeline stages",
    )
    parser.add_argument(
        "--idea",
        type=str,
        help="Path to the idea file to mount (relative to inbox or absolute)",
    )
    parser.add_argument(
        "--stage",
        type=str,
        help="Target pipeline stage (e.g., '03-architecture' or just '03')",
    )
    parser.add_argument(
        "--show-manifests",
        action="store_true",
        help="Show the manifest for each pipeline stage",
    )
    args = parser.parse_args()

    if args.show_manifests:
        show_manifests()
    elif args.idea and args.stage:
        manual_mount(args.idea, args.stage)
    elif args.idea or args.stage:
        print("[ERROR] Both --idea and --stage are required for manual mounting.")
        print("  Example: python factory/engine/mounter.py --idea my_idea.md --stage 03-architecture")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
