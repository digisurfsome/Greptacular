"""
Full Checkpoint (M2)
End-of-phase gate. Runs lint + typecheck + tests + files_allowed diff.
Replaces the agent-enforced checkpoint that Stage 8 embeds as markdown.

Usage: python full-checkpoint.py <artifacts_dir> <baseline_sha>
Exit 0 = PASS, Exit 1 = FAIL (one or more checks failed)

In prd-pipeline-c.yaml this script is wrapped in a bash node:
  bash: |
    set +e
    python .archon/scripts/full-checkpoint.py "$ARTIFACTS_DIR" $phase-N-baseline.output
    code=$?
    if [ $code -eq 0 ]; then echo "PASS"; else echo "FAIL"; fi
    exit 0
"""
import json
import os
import subprocess
import sys


def run_check(cmd: list[str], label: str, cwd: str | None = None) -> tuple[bool, str]:
    """Run a shell command, return (passed, message)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode == 0:
            return True, f"PASS: {label}"
        combined = (result.stdout + result.stderr).strip()
        return False, f"FAIL: {label}\n{combined[:500]}"
    except FileNotFoundError:
        return False, f"FAIL: {label} — command not found: {cmd[0]}"
    except OSError as e:
        return False, f"FAIL: {label} — OS error: {e}"


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: full-checkpoint.py <artifacts_dir> <baseline_sha>",
            file=sys.stderr,
        )
        sys.exit(1)

    artifacts_dir = sys.argv[1]
    baseline_sha  = sys.argv[2].strip("'")  # strip single quotes Archon may add

    if not os.path.isdir(artifacts_dir):
        print(f"FAIL: artifacts_dir does not exist: {artifacts_dir}", file=sys.stderr)
        sys.exit(1)

    # Load files_allowed — if absent, skip that check (non-blocking)
    files_allowed_path = os.path.join(artifacts_dir, 'files_allowed.json')
    files_allowed: set[str] | None = None
    if os.path.exists(files_allowed_path):
        try:
            with open(files_allowed_path, 'r', encoding='utf-8') as fh:
                raw = json.load(fh)
            files_allowed = set(raw) if isinstance(raw, list) else None
        except (json.JSONDecodeError, OSError):
            pass

    results: list[str] = []
    failures: list[str] = []

    # ── Detect project language(s) from files at cwd ─────────────────────────
    has_node  = os.path.exists('package.json')
    has_py    = os.path.exists('pyproject.toml') or os.path.exists('requirements.txt')
    has_rust  = os.path.exists('Cargo.toml')

    if not (has_node or has_py or has_rust):
        results.append("SKIP: no known project manifest (package.json/pyproject.toml/Cargo.toml) — skipping lint/typecheck/test")
    else:
        # ── 1. Lint ──────────────────────────────────────────────────────────
        if has_node:
            passed, msg = run_check(['npm', 'run', 'lint'], 'lint (npm)')
            (results if passed else failures).append(msg)
        if has_py:
            passed, msg = run_check(['ruff', 'check', '.'], 'lint (ruff)')
            (results if passed else failures).append(msg)
        if has_rust:
            passed, msg = run_check(['cargo', 'clippy', '--', '-D', 'warnings'], 'lint (clippy)')
            (results if passed else failures).append(msg)

        # ── 2. Typecheck ─────────────────────────────────────────────────────
        if has_node:
            passed, msg = run_check(['npm', 'run', 'typecheck'], 'typecheck (npm)')
            if not passed:
                passed2, msg2 = run_check(['npx', 'tsc', '--noEmit'], 'typecheck (tsc)')
                (results if passed2 else failures).append(msg2)
            else:
                results.append(msg)
        if has_py:
            passed, msg = run_check(['mypy', '.'], 'typecheck (mypy)')
            (results if passed else failures).append(msg)
        if has_rust:
            passed, msg = run_check(['cargo', 'check'], 'typecheck (cargo check)')
            (results if passed else failures).append(msg)

        # ── 3. Tests ─────────────────────────────────────────────────────────
        if has_node:
            passed, msg = run_check(['npm', 'test'], 'tests (npm)')
            (results if passed else failures).append(msg)
        if has_py:
            passed, msg = run_check(['pytest'], 'tests (pytest)')
            (results if passed else failures).append(msg)
        if has_rust:
            passed, msg = run_check(['cargo', 'test'], 'tests (cargo test)')
            (results if passed else failures).append(msg)

    # ── 4. files_allowed diff ────────────────────────────────────────────────
    if files_allowed is not None:
        try:
            git_result = subprocess.run(
                ['git', 'diff', '--name-only', baseline_sha],
                capture_output=True,
                text=True,
            )
            if git_result.returncode != 0:
                failures.append(
                    f"FAIL: git diff failed (sha={baseline_sha})\n{git_result.stderr.strip()}"
                )
            else:
                changed = {
                    f.strip()
                    for f in git_result.stdout.splitlines()
                    if f.strip()
                }
                unauthorized = changed - files_allowed
                if unauthorized:
                    failures.append(
                        f"FAIL: {len(unauthorized)} unauthorized file(s) modified: "
                        + ', '.join(sorted(unauthorized))
                    )
                else:
                    results.append(
                        f"PASS: files_allowed ({len(changed)} changed file(s) all authorized)"
                    )
        except OSError as e:
            failures.append(f"FAIL: git diff — OS error: {e}")
    else:
        results.append("SKIP: files_allowed.json not found — skipping diff check")

    # ── Write result file ────────────────────────────────────────────────────
    result_path = os.path.join(artifacts_dir, 'phase-checkpoint-result.md')
    try:
        with open(result_path, 'w', encoding='utf-8') as fh:
            fh.write("# Full Checkpoint Result\n\n")
            for line in results:
                fh.write(f"- {line}\n")
            for line in failures:
                fh.write(f"- {line}\n")
    except OSError:
        pass

    if failures:
        for msg in failures:
            print(msg, file=sys.stderr)
        sys.exit(1)

    for msg in results:
        print(msg)
    sys.exit(0)


if __name__ == '__main__':
    main()
