"""
Pre-Deploy Gate (M8)
Final mechanical gate before build-deploy. Reads cumulative deferred.md files,
caps total deferrals at 5, verifies no CRITICAL/HIGH issues remain unfixed.

Usage: python deploy-gate.py <artifacts_dir>
Exit 0 = PASS, Exit 1 = FAIL

In prd-pipeline-c.yaml this script is wrapped in a bash node:
  bash: |
    set +e
    python .archon/scripts/deploy-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
"""
import re
import sys
import glob
import os

DEFERRED_CAP = 5


def collect_files(artifacts_dir: str, sub_pattern: str) -> list[str]:
    """
    Collect files matching sub_pattern under artifacts_dir.
    Checks both flat (artifacts_dir/pattern) and nested (artifacts_dir/runs/*/pattern).
    """
    flat    = glob.glob(os.path.join(artifacts_dir, sub_pattern))
    nested  = glob.glob(os.path.join(artifacts_dir, 'runs', '*', sub_pattern))
    return flat + nested


def count_remaining(artifacts_dir: str) -> int:
    """Count total CRITICAL and HIGH issues across all review-*.md files."""
    pattern = re.compile(
        r'^[*\-]\s+\*\*\[(CRITICAL|HIGH)\]', re.MULTILINE
    )
    total = 0
    for filepath in collect_files(artifacts_dir, 'review-*.md'):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                total += len(pattern.findall(fh.read()))
        except OSError:
            pass
    return total


def count_fixed(artifacts_dir: str) -> int:
    """Count total fix entries across all fix-report.md files."""
    pattern = re.compile(r'^###\s+Fix\s+\d+:', re.MULTILINE)
    total = 0
    for filepath in collect_files(artifacts_dir, 'fix-report.md'):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                total += len(pattern.findall(fh.read()))
        except OSError:
            pass
    return total


def count_deferred(artifacts_dir: str) -> int:
    """Count total bullet-line entries across all deferred.md files."""
    pattern = re.compile(r'^[*\-]\s+', re.MULTILINE)
    total = 0
    for filepath in collect_files(artifacts_dir, 'deferred.md'):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                total += len(pattern.findall(fh.read()))
        except OSError:
            pass
    return total


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: deploy-gate.py <artifacts_dir>", file=sys.stderr)
        sys.exit(1)

    artifacts_dir = sys.argv[1]

    if not os.path.isdir(artifacts_dir):
        print(f"FAIL: artifacts_dir does not exist: {artifacts_dir}", file=sys.stderr)
        sys.exit(1)

    remaining      = count_remaining(artifacts_dir)
    fixed          = count_fixed(artifacts_dir)
    deferred_count = count_deferred(artifacts_dir)

    failures: list[str] = []

    if remaining > fixed:
        unaddressed = remaining - fixed
        failures.append(
            f"FAIL: {unaddressed} CRITICAL/HIGH item(s) not in fix-report "
            f"(found {remaining}, fixed {fixed})"
        )

    if deferred_count > DEFERRED_CAP:
        failures.append(
            f"FAIL: {deferred_count} deferrals exceeds budget of {DEFERRED_CAP}"
        )

    if failures:
        for msg in failures:
            print(msg, file=sys.stderr)
        sys.exit(1)

    print(
        f"PASS: {fixed}/{remaining} issues fixed, "
        f"{deferred_count}/{DEFERRED_CAP} deferrals used"
    )
    sys.exit(0)


if __name__ == '__main__':
    main()
