"""
PRD Archive (M10)
After every pipeline run, copies final artifacts into a chronologically-sorted
folder under docs/generated-prds/ and appends a row to the INDEX.md.

Usage: python archive-prd.py <artifacts_dir> <build_name> <status>
  build_name  — human-readable name for this build (e.g. "yt-strategy-lab-v2")
  status      — "shipped" | "failed" | "recovered"
Exit 0 = PASS, Exit 1 = FAIL

In prd-pipeline-c.yaml this script is wrapped in a bash node:
  bash: |
    python .archon/scripts/archive-prd.py \\
      "$ARTIFACTS_DIR" \\
      "$BASE_BRANCH" \\
      $recovery-status-summary.output
"""
import datetime
import os
import re
import shutil
import sys


# Files to copy from artifacts_dir root into the archive folder
COPY_FILES = [
    'context_packet.json',
    'CLAUDE.md',
    'BUILD_RULES.md',
    'README.md',
    'final-summary.md',
    'triage-report.md',
    'fix-prd.md',
]

# Subdirectories to copy recursively
COPY_DIRS = ['phases']


def safe_name(name: str) -> str:
    """Sanitize a build name for use as a directory component."""
    return re.sub(r'[^\w\-.]', '-', name).strip('-')


def ensure_index(index_path: str) -> None:
    """Create INDEX.md with header if it doesn't exist."""
    if not os.path.exists(index_path):
        with open(index_path, 'w', encoding='utf-8') as fh:
            fh.write("# PRD Archive Index\n\n")
            fh.write("| Date | Build Name | Status | Link |\n")
            fh.write("|------|-----------|--------|------|\n")


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: archive-prd.py <artifacts_dir> <build_name> <status>",
            file=sys.stderr,
        )
        sys.exit(1)

    artifacts_dir = sys.argv[1]
    build_name    = sys.argv[2].strip("'")   # strip Archon-added shell quotes
    status        = sys.argv[3].strip("'")

    if not os.path.isdir(artifacts_dir):
        print(f"FAIL: artifacts_dir does not exist: {artifacts_dir}", file=sys.stderr)
        sys.exit(1)

    date_str    = datetime.date.today().strftime('%Y-%m-%d')
    folder_name = f"{date_str}__{safe_name(build_name)}"
    archive_dir = os.path.join('docs', 'generated-prds', folder_name)
    index_path  = os.path.join('docs', 'generated-prds', 'INDEX.md')

    # ── Create archive directory ─────────────────────────────────────────────
    os.makedirs(archive_dir, exist_ok=True)

    # ── Copy flat files ───────────────────────────────────────────────────────
    for fname in COPY_FILES:
        src = os.path.join(artifacts_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, archive_dir)

    # ── Copy directories ──────────────────────────────────────────────────────
    for dirname in COPY_DIRS:
        src = os.path.join(artifacts_dir, dirname)
        if os.path.isdir(src):
            dst = os.path.join(archive_dir, dirname)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # ── Update INDEX.md ───────────────────────────────────────────────────────
    ensure_index(index_path)

    row = (
        f"| {date_str} | {build_name} | {status} | "
        f"[{folder_name}]({folder_name}/) |\n"
    )
    with open(index_path, 'a', encoding='utf-8') as fh:
        fh.write(row)

    print(f"PASS: archived to {archive_dir}")
    print(f"PASS: INDEX.md updated ({index_path})")
    sys.exit(0)


if __name__ == '__main__':
    main()
