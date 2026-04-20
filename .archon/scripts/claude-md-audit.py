"""
CLAUDE.md Audit (M6)
Soft check: after a build phase completes, report which new directories are missing a CLAUDE.md.
Exits 0 always (DOOR, not WALL). Writes an audit report to artifacts_dir.

Usage: python claude-md-audit.py <artifacts_dir> [<baseline_sha>]
  artifacts_dir  — path to the build artifacts directory
  baseline_sha   — optional git SHA; if given, only inspect directories that received new files
                   since that commit. If omitted, inspects all tracked directories.

Exit 0 always (soft check — does not fail the pipeline).
"""
import os
import subprocess
import sys


def get_new_dirs_since(baseline_sha: str) -> list[str]:
    """Return unique parent directories of files changed since baseline_sha."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', baseline_sha],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
        dirs: set[str] = set()
        for line in result.stdout.splitlines():
            f = line.strip()
            if f:
                d = os.path.dirname(f)
                if d:
                    dirs.add(d)
        return sorted(dirs)
    except OSError:
        return []


def get_all_tracked_dirs() -> list[str]:
    """Return unique parent directories of all git-tracked files."""
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
        dirs: set[str] = set()
        for line in result.stdout.splitlines():
            f = line.strip()
            if f:
                d = os.path.dirname(f)
                if d:
                    dirs.add(d)
        return sorted(dirs)
    except OSError:
        return []


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: claude-md-audit.py <artifacts_dir> [<baseline_sha>]", file=sys.stderr)
        sys.exit(0)  # soft check — never fail on usage error

    artifacts_dir = sys.argv[1]
    baseline_sha = sys.argv[2].strip("'") if len(sys.argv) >= 3 else None

    # Determine which directories to audit
    if baseline_sha:
        dirs_to_check = get_new_dirs_since(baseline_sha)
        scope_note = f"directories with changes since {baseline_sha[:8]}"
    else:
        dirs_to_check = get_all_tracked_dirs()
        scope_note = "all tracked directories"

    missing: list[str] = []
    present: list[str] = []

    for d in dirs_to_check:
        claude_md_path = os.path.join(d, 'CLAUDE.md')
        if os.path.exists(claude_md_path):
            present.append(d)
        else:
            missing.append(d)

    # Write audit report
    report_path = os.path.join(artifacts_dir, 'claude-md-audit.md')
    try:
        os.makedirs(artifacts_dir, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as fh:
            fh.write("# CLAUDE.md Audit Report (M6)\n\n")
            fh.write(f"**Scope:** {scope_note}\n")
            fh.write(f"**Checked:** {len(dirs_to_check)} directories\n")
            fh.write(f"**With CLAUDE.md:** {len(present)}\n")
            fh.write(f"**Missing CLAUDE.md:** {len(missing)}\n\n")

            if missing:
                fh.write("## Directories Missing CLAUDE.md\n\n")
                fh.write("> These directories received new files but have no CLAUDE.md.\n")
                fh.write("> This is a soft warning — the pipeline continues.\n")
                fh.write("> Add a CLAUDE.md to each directory on the next build pass.\n\n")
                for d in missing:
                    fh.write(f"- `{d}/`\n")
                fh.write("\n")
            else:
                fh.write("## Result\n\nAll checked directories have a CLAUDE.md. ✓\n\n")

            if present:
                fh.write("## Directories With CLAUDE.md\n\n")
                for d in present:
                    fh.write(f"- `{d}/`\n")
    except OSError as e:
        print(f"WARN: could not write audit report: {e}", file=sys.stderr)

    # Print summary to stdout (captured by Archon as node output)
    if missing:
        print(f"WARN: {len(missing)} director(ies) missing CLAUDE.md — see claude-md-audit.md")
    else:
        print(f"PASS: all {len(present)} checked directories have CLAUDE.md")

    sys.exit(0)  # always exit 0 — this is a DOOR, not a WALL


if __name__ == '__main__':
    main()
