"""
Compliance Gate (M1)
Mechanically verifies that every CRITICAL and HIGH issue flagged by reviewers
has a corresponding fix entry in fix-report.md.

Usage: python compliance-gate.py <artifacts_dir>
Exit 0 = PASS, Exit 1 = FAIL

In prd-pipeline-c.yaml this script is wrapped in a bash node:
  bash: |
    set +e
    python .archon/scripts/compliance-gate.py "$ARTIFACTS_DIR"
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
"""
import re
import sys
import glob
import os


def count_issues(artifacts_dir: str, severity: str) -> int:
    """Count issues of a given severity across all review-*.md files."""
    pattern = re.compile(
        r'^[*\-]\s+\*\*\[' + re.escape(severity) + r'\]', re.MULTILINE
    )
    review_files = glob.glob(os.path.join(artifacts_dir, 'review-*.md'))
    total = 0
    for filepath in review_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                total += len(pattern.findall(fh.read()))
        except OSError:
            pass
    return total


def count_fixes(artifacts_dir: str, severity: str) -> int:
    """Count fix entries for a given severity in fix-report.md."""
    fix_report = os.path.join(artifacts_dir, 'fix-report.md')
    if not os.path.exists(fix_report):
        return 0
    pattern = re.compile(
        r'^###\s+Fix\s+\d+:.*\[' + re.escape(severity) + r'\]', re.MULTILINE
    )
    try:
        with open(fix_report, 'r', encoding='utf-8', errors='replace') as fh:
            return len(pattern.findall(fh.read()))
    except OSError:
        return 0


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: compliance-gate.py <artifacts_dir>", file=sys.stderr)
        sys.exit(1)

    artifacts_dir = sys.argv[1]

    if not os.path.isdir(artifacts_dir):
        print(f"FAIL: artifacts_dir does not exist: {artifacts_dir}", file=sys.stderr)
        sys.exit(1)

    critical_issues = count_issues(artifacts_dir, 'CRITICAL')
    high_issues     = count_issues(artifacts_dir, 'HIGH')
    critical_fixes  = count_fixes(artifacts_dir, 'CRITICAL')
    high_fixes      = count_fixes(artifacts_dir, 'HIGH')

    unaddressed_critical = max(0, critical_issues - critical_fixes)
    unaddressed_high     = max(0, high_issues - high_fixes)
    total_unaddressed    = unaddressed_critical + unaddressed_high

    if total_unaddressed > 0:
        print(
            f"FAIL: {total_unaddressed} issues unaddressed "
            f"(CRITICAL: {unaddressed_critical}, HIGH: {unaddressed_high}) — "
            f"found {critical_issues} CRITICAL/{high_issues} HIGH, "
            f"fixed {critical_fixes} CRITICAL/{high_fixes} HIGH",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write result file for downstream nodes
    result_path = os.path.join(artifacts_dir, 'compliance-gate-result.md')
    try:
        with open(result_path, 'w', encoding='utf-8') as fh:
            fh.write(
                f"# Compliance Gate Result: PASS\n\n"
                f"- CRITICAL: {critical_issues} issues, {critical_fixes} fixed\n"
                f"- HIGH: {high_issues} issues, {high_fixes} fixed\n"
            )
    except OSError:
        pass  # Non-fatal — result file is informational only

    print(
        f"PASS: all issues addressed "
        f"(CRITICAL {critical_fixes}/{critical_issues}, HIGH {high_fixes}/{high_issues})"
    )
    sys.exit(0)


if __name__ == '__main__':
    main()
