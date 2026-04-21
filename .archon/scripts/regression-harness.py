"""
Regression Harness (M11)
Self-test suite for the Archon pipeline. Runs Tests A/B/C against the
current state of .archon/scripts/ and fails if any gate behaves wrong.

Run via: archon workflow run regression-harness
  OR:    python .archon/scripts/regression-harness.py  (from project root)

Env vars (all have defaults relative to project root):
  FIXTURES   — path to test-fixtures dir  (default: .archon/test-fixtures)
  SCRIPTS_DIR — path to scripts dir       (default: .archon/scripts)
"""
import datetime
import os
import subprocess
import sys

# Force UTF-8 for stdout/stderr. Windows default is cp1252 which cannot
# encode Unicode chars like '→' used in test labels, so the first print
# raises UnicodeEncodeError and the harness crashes before any assertion
# runs. reconfigure() is available on 3.7+ and is a no-op if already UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        pass

# Use the same Python interpreter for all subprocesses — avoids PATH issues
# where 'python' may not be found in Archon's bash environment.
PYTHON = sys.executable

FIXTURES    = os.environ.get('FIXTURES',    '.archon/test-fixtures')
SCRIPTS_DIR = os.environ.get('SCRIPTS_DIR', '.archon/scripts')

PASS_COUNT = 0
FAIL_COUNT = 0


def expect(
    cmd: list[str],
    expected_code: int,
    label: str,
) -> bool:
    """
    Run cmd, assert exit code == expected_code.
    Prints PASS/FAIL. Returns True on pass.
    """
    global PASS_COUNT, FAIL_COUNT
    result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    if result.returncode == expected_code:
        print(f"  PASS: {label}")
        PASS_COUNT += 1
        return True
    else:
        print(
            f"  FAIL: {label}\n"
            f"        expected exit {expected_code}, got {result.returncode}"
        )
        if result.stdout.strip():
            print(f"        stdout: {result.stdout.strip()[:200]}")
        if result.stderr.strip():
            print(f"        stderr: {result.stderr.strip()[:200]}")
        FAIL_COUNT += 1
        return False


def expect_stderr_contains(
    cmd: list[str],
    expected_code: int,
    expected_text: str,
    label: str,
) -> bool:
    """
    Run cmd, assert exit code AND that stderr contains expected_text.
    """
    global PASS_COUNT, FAIL_COUNT
    result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    code_ok = result.returncode == expected_code
    text_ok = expected_text in result.stderr

    if code_ok and text_ok:
        print(f"  PASS: {label}")
        PASS_COUNT += 1
        return True

    reasons = []
    if not code_ok:
        reasons.append(f"expected exit {expected_code}, got {result.returncode}")
    if not text_ok:
        reasons.append(f"expected stderr to contain '{expected_text}'")
        reasons.append(f"actual stderr: {result.stderr.strip()[:300]}")

    print(f"  FAIL: {label}\n        " + "\n        ".join(reasons))
    FAIL_COUNT += 1
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Test A — Gate Script Unit Tests
# ═══════════════════════════════════════════════════════════════════════════════
print("=== Test A: Unit tests on gate scripts ===\n")

# ── A1: compliance-gate FAIL on YT Strategy Lab fixture ──────────────────────
expect_stderr_contains(
    [PYTHON, f'{SCRIPTS_DIR}/compliance-gate.py',
     f'{FIXTURES}/yt-strategy-lab-fail'],
    1,
    'issues unaddressed',
    'compliance-gate: yt-strategy-lab-fail → exit 1, stderr contains "issues unaddressed"',
)

# ── A2: compliance-gate PASS on clean fixture ─────────────────────────────────
expect(
    [PYTHON, f'{SCRIPTS_DIR}/compliance-gate.py',
     f'{FIXTURES}/task-manager-pass'],
    0,
    'compliance-gate: task-manager-pass → exit 0',
)

# ── A3: full-checkpoint FAIL on broken-phase fixture ─────────────────────────
# broken-phase/files_allowed.json = [] so any git diff changes are unauthorized.
# Get a real historical SHA where files changed.
git_result = subprocess.run(
    ['git', 'rev-parse', 'HEAD~1'],
    capture_output=True, text=True,
)
if git_result.returncode == 0 and git_result.stdout.strip():
    old_sha = git_result.stdout.strip()
    expect(
        [PYTHON, f'{SCRIPTS_DIR}/full-checkpoint.py',
         f'{FIXTURES}/broken-phase', old_sha],
        1,
        f'full-checkpoint: broken-phase with SHA HEAD~1 → exit 1 (unauthorized files)',
    )
else:
    print('  SKIP: full-checkpoint test — git history unavailable')

# ── A4: deploy-gate FAIL on YT Strategy Lab fixture ──────────────────────────
expect(
    [PYTHON, f'{SCRIPTS_DIR}/deploy-gate.py',
     f'{FIXTURES}/yt-strategy-lab-fail'],
    1,
    'deploy-gate: yt-strategy-lab-fail → exit 1 (remaining CRITICAL/HIGH)',
)

# ── A5: deploy-gate PASS on clean fixture ────────────────────────────────────
expect(
    [PYTHON, f'{SCRIPTS_DIR}/deploy-gate.py',
     f'{FIXTURES}/task-manager-pass'],
    0,
    'deploy-gate: task-manager-pass → exit 0',
)

# ── A6: archive-prd creates folder and appends to INDEX.md ───────────────────
date_str       = datetime.date.today().strftime('%Y-%m-%d')
test_build     = f'regression-test-{date_str}'
expected_dir   = os.path.join('docs', 'generated-prds', f'{date_str}__{test_build}')

archive_passed = expect(
    [PYTHON, f'{SCRIPTS_DIR}/archive-prd.py',
     f'{FIXTURES}/task-manager-pass', test_build, 'shipped'],
    0,
    'archive-prd: task-manager-pass → exit 0',
)

if archive_passed:
    # Verify the archive directory was actually created
    if os.path.isdir(expected_dir):
        print(f"  PASS: archive dir exists: {expected_dir}")
        PASS_COUNT += 1
    else:
        print(f"  FAIL: archive dir was not created: {expected_dir}")
        FAIL_COUNT += 1

    # Verify INDEX.md was updated
    index_path = os.path.join('docs', 'generated-prds', 'INDEX.md')
    if os.path.exists(index_path):
        with open(index_path, encoding='utf-8') as fh:
            content = fh.read()
        if test_build in content:
            print(f"  PASS: INDEX.md contains entry for {test_build}")
            PASS_COUNT += 1
        else:
            print(f"  FAIL: INDEX.md missing entry for {test_build}")
            FAIL_COUNT += 1
    else:
        print(f"  FAIL: INDEX.md was not created at {index_path}")
        FAIL_COUNT += 1

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
if FAIL_COUNT == 0:
    print(f"=== ALL REGRESSION TESTS PASS ({PASS_COUNT} checks) ===")
    sys.exit(0)
else:
    print(
        f"=== REGRESSION TESTS FAILED: {FAIL_COUNT} failed, {PASS_COUNT} passed ==="
    )
    sys.exit(1)
