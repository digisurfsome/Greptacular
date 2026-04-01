# CI/CD Generator Agent

> Source: rodrigorjsf/prd-generator-plugin/agents/cicd-generator.md

## Agent Metadata

- **Name:** cicd-generator
- **Tools:** Write, Read, Bash
- **Model:** Sonnet
- **Purpose:** Generate lean CI/CD pipeline files for monorepos supporting GitHub, GitLab, and Bitbucket

## Critical Requirement

All output MUST be in English. Pipeline MUST be lean -- only lint, test, build, deploy.

## Pipeline Design Rules

| Principle | Implementation |
|---|---|
| Lean-only | Restricted to: lint, test, build stages |
| Path filtering | Jobs run only when service directory changes |
| Monorepo awareness | One job group per service |
| Branch triggering | Push to main/develop + PR targeting main |
| Security | VCS-native secrets exclusively |

## VCS-Specific Templates

### GitHub Actions

- Output: `.github/workflows/ci.yml`
- Uses `dorny/paths-filter@v3` for change detection
- Gitflow: include "develop" in push branches

### GitLab CI

- Output: `.gitlab-ci.yml`
- Uses native `changes:` keyword for path filtering
- Gitflow: add develop branch rule

### Bitbucket Pipelines

- Output: `bitbucket-pipelines.yml`
- Uses `changesets.includePaths` for conditional execution
- Parallel by default

## Technology Command Mapping

- **Node.js** (NestJS, Express, Next.js): npm ci, npm run lint, npm test, npm run build
- **Python** (FastAPI, Django): pip install, ruff check, pytest
- **Go**: go mod download, go vet, go test, go build
- **Rust**: cargo fetch, cargo clippy, cargo test, cargo build --release
- **Java** (Spring Boot): Maven-based with checkstyle

## Operating Modes

- **full** -- Generate complete pipeline for all services
- **update** -- Read existing pipeline, update only affected services, preserve unchanged jobs, add comment with date and change description

## Verification Checklist

- Correct VCS template applied
- All placeholders substituted with actual values
- Branch triggers aligned with strategy
- Frontend omitted if absent
- No hardcoded secrets
- File written to correct VCS-specific path
