"""
Lint Autofix (M6 / Standard S7)
Runs available autofix-capable linters before paying LLM tokens to fix style issues.
"If eslint-autofix can fix it, run autofix deterministically before paying LLM tokens to 'fix' it."

Usage: python lint-autofix.py [<project_dir>]
  project_dir — directory to run linters in (default: current working directory)

Exit 0 = autofix ran (or nothing to fix)
Exit 1 = autofix failed or a linter reported unfixable errors after autofix

Intended use: call this BEFORE the fix agent runs, so the fix agent
sees a clean slate and doesn't waste its budget on style issues.
"""
import os
import subprocess
import sys


def run(cmd: list[str], label: str, cwd: str) -> tuple[bool, str]:
    """Run a command, return (success, message)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if result.returncode == 0:
            return True, f"PASS: {label}"
        combined = (result.stdout + result.stderr).strip()
        return False, f"FAIL: {label}\n{combined[:800]}"
    except FileNotFoundError:
        return True, f"SKIP: {label} — command not found: {cmd[0]}"
    except OSError as e:
        return True, f"SKIP: {label} — OS error: {e}"


def main() -> None:
    project_dir = sys.argv[1] if len(sys.argv) >= 2 else os.getcwd()
    project_dir = os.path.abspath(project_dir)

    if not os.path.isdir(project_dir):
        print(f"FAIL: project_dir does not exist: {project_dir}", file=sys.stderr)
        sys.exit(1)

    has_node = os.path.exists(os.path.join(project_dir, 'package.json'))
    has_py   = (os.path.exists(os.path.join(project_dir, 'pyproject.toml')) or
                os.path.exists(os.path.join(project_dir, 'requirements.txt')))
    has_rust = os.path.exists(os.path.join(project_dir, 'Cargo.toml'))

    if not (has_node or has_py or has_rust):
        print("SKIP: no known project manifest — nothing to autofix")
        sys.exit(0)

    results: list[str] = []
    failures: list[str] = []

    # ── Node / ESLint autofix ────────────────────────────────────────────────
    if has_node:
        # Try npm run lint:fix first (project may define it)
        ok, msg = run(['npm', 'run', 'lint:fix', '--if-present'], 'eslint autofix (npm run lint:fix)', project_dir)
        if ok:
            results.append(msg)
        else:
            # Fallback: invoke eslint --fix directly
            ok2, msg2 = run(['npx', 'eslint', '--fix', '.'], 'eslint --fix', project_dir)
            (results if ok2 else failures).append(msg2)

        # Prettier autofix (non-blocking — many projects don't use it)
        ok, msg = run(['npx', 'prettier', '--write', '.'], 'prettier --write', project_dir)
        results.append(msg)  # always treat prettier as non-blocking

    # ── Python / Ruff autofix ────────────────────────────────────────────────
    if has_py:
        ok, msg = run(['ruff', 'check', '--fix', '.'], 'ruff --fix', project_dir)
        (results if ok else failures).append(msg)

        # Black formatting (non-blocking style)
        ok, msg = run(['black', '.'], 'black format', project_dir)
        results.append(msg)  # treat as non-blocking

    # ── Rust / cargo fmt ─────────────────────────────────────────────────────
    if has_rust:
        ok, msg = run(['cargo', 'fmt'], 'cargo fmt', project_dir)
        (results if ok else failures).append(msg)

    # Print summary
    for line in results:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)

    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
