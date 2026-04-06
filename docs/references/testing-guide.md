# Testing Guide

## Python

```bash
ruff check .                                    # Lint
mypy .                                          # Type check
python test_security.py                         # Security unit tests (12 tests)
python test_security_integration.py             # Integration tests (9 tests)
python -m pytest test_client.py                 # Client tests (20 tests)
python -m pytest test_dependency_resolver.py    # Dependency resolver tests (12 tests)
python -m pytest test_rate_limit_utils.py       # Rate limit tests (22 tests)
```

## React UI

```bash
cd ui
npm run lint          # ESLint
npm run build         # Type check + build (Vite 7)
npm run test:e2e      # Playwright end-to-end tests
npm run test:e2e:ui   # Playwright tests with UI
```

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to master:
- **Python job**: ruff lint + security tests
- **UI job**: ESLint + TypeScript build

## Code Quality

Config in `pyproject.toml`:
- ruff: Line length 120, Python 3.11 target
- mypy: Strict return type checking, ignores missing imports

## Workspace UI Build Standards

All new pages must follow `ui/WORKSPACE_STANDARDS.md` — layout patterns, CRUD flows, state patterns, design tokens, backend patterns.
