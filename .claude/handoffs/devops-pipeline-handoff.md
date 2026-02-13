# DevOps Pipeline Handoff: CI/CD, Monitoring, and Auto-Update Agents

## Status: Ready to Implement

## Overview

AutoForge builds complete applications and verifies them through QA, but the story ends there. Once a project is "done," there is no deployment infrastructure, no production monitoring, and no ongoing maintenance. The user is handed working code with zero DevOps.

This handoff specifies three new post-build agent types that close the gap between "code that works locally" and "code that runs reliably in production with ongoing maintenance":

1. **CI/CD Pipeline Generator Agent** -- Generates GitHub Actions workflows, Dockerfiles, and deployment configs tailored to the project's tech stack and deployment target
2. **Monitoring Setup Agent** -- Adds error tracking, health endpoints, structured logging, and uptime monitoring to the existing codebase
3. **Auto-Update Agent** -- Runs on a recurring schedule to update dependencies, fix security vulnerabilities, and verify nothing broke

These three agents are complementary to the self-deploy VPS system (see `self-deploy-vps-handoff.md`). The VPS system handles provisioning infrastructure; these agents handle what runs on that infrastructure and keeping it healthy over time.

**Why this matters for the business:** The CI/CD and monitoring agents are one-time value-adds that justify a higher initial price. The auto-update agent is a recurring service that generates monthly revenue even after the build is complete -- the customer keeps paying because the agent keeps maintaining their app.

---

## Feature 1: CI/CD Pipeline Generator Agent

### Problem

After AutoForge builds an application, deploying it requires manual DevOps work. The user must write GitHub Actions workflows, create Dockerfiles, configure staging and production environments, and set up security scanning. Most AutoForge users are not DevOps engineers -- they chose AutoForge specifically to avoid this kind of work.

### Solution

A new agent type (`--agent-type cicd`) that reads the completed project, detects its tech stack, and generates a complete CI/CD pipeline. This is pure file generation -- no browser, no running servers, no Playwright. The agent reads code and writes configuration files.

### What It Generates

#### GitHub Actions Workflows

**`.github/workflows/ci.yml`** -- Continuous integration on every PR:
- Checkout code
- Install dependencies (`npm ci` / `pip install`)
- Run lint (`eslint` / `ruff`)
- Run type check (`tsc --noEmit` / `mypy`)
- Run generated Playwright test suite from `tests/e2e/`
- Run generated API tests from `tests/api/`
- Block merge if any step fails
- Upload test results and screenshots as artifacts

**`.github/workflows/deploy-staging.yml`** -- Auto-deploy to staging on merge to `main`:
- Triggered by push to `main` branch
- Build the project
- Run smoke tests against staging after deploy
- Post deployment status to Slack/Discord webhook (if configured)

**`.github/workflows/deploy-production.yml`** -- Deploy to production on release tag:
- Triggered by tag creation matching `v*`
- Build the project with production env vars
- Deploy to production target
- Run production smoke tests
- Create GitHub release with changelog
- Rollback on failure (if supported by platform)

**`.github/workflows/security.yml`** -- Weekly security scanning:
- Scheduled via cron (`0 9 * * 1` -- Monday at 9 AM)
- `npm audit` / `pip-audit` for dependency vulnerabilities
- SAST scan using CodeQL or semgrep
- Create GitHub issue if vulnerabilities found
- Send notification via webhook

#### Container Configuration

**`Dockerfile`** -- Multi-stage build optimized for the detected tech stack:
- Stage 1: Install dependencies and build
- Stage 2: Production image with only runtime artifacts
- Non-root user for security
- Health check instruction
- Proper `.dockerignore` to exclude dev files

**`docker-compose.yml`** -- Local development and deployment:
- Application service
- Database service (PostgreSQL/SQLite) if detected
- Redis for caching (if detected in dependencies)
- Volume mounts for persistent data
- Environment variable configuration

#### Supporting Files

**`.env.example`** -- Documented template of all required environment variables:
- Every `process.env.X` / `os.environ["X"]` reference extracted from the codebase
- Grouped by category (database, auth, API keys, feature flags)
- Comments explaining each variable's purpose and valid values
- Clearly marked secrets vs non-secrets

**`Makefile`** or **`scripts/`** directory with common commands:
- `make setup` -- Install all dependencies and create env file
- `make dev` -- Start development server
- `make test` -- Run full test suite
- `make build` -- Production build
- `make deploy` -- Deploy to configured target
- `make rollback` -- Rollback last deployment
- `make logs` -- Tail production logs

### Platform-Specific Deployment Configs

The agent detects the deployment target from project config or the `--deployment-target` CLI flag and generates platform-specific files:

| Target | Generated Files | Auto-Detected When |
|---|---|---|
| Vercel | `vercel.json` | `next.config` found (Next.js project) |
| Railway | `railway.toml`, `Procfile` | Generic Node.js project |
| Fly.io | `fly.toml`, `Dockerfile` | Docker-based or explicitly selected |
| AWS (ECS/Fargate) | `task-definition.json`, `appspec.yml`, `buildspec.yml` | AWS env vars detected |
| Generic Docker | `Dockerfile`, `docker-compose.yml`, `nginx.conf` | Fallback / explicit |

If no target is specified and cannot be auto-detected, the agent defaults to Generic Docker (most portable).

### Implementation

#### 1.1 New Agent Type: `cicd`

Add to `autonomous_agent_demo.py` CLI args:

```python
choices=["initializer", "coding", "testing", "cicd", "monitoring", "auto-update"]
```

New CLI flag:

```python
parser.add_argument(
    "--deployment-target",
    choices=["vercel", "railway", "flyio", "aws", "docker"],
    default=None,
    help="Deployment platform for CI/CD pipeline generation (auto-detected if not specified)",
)
```

#### 1.2 New Prompt Template: `cicd_prompt.template.md`

Create `.claude/templates/cicd_prompt.template.md`:

```markdown
## YOUR ROLE - CI/CD PIPELINE GENERATOR

You are a **DevOps agent** responsible for generating a complete CI/CD pipeline
for a project that has been built and verified by AutoForge.

## PROJECT ANALYSIS

Before generating any files, analyze the project:

1. Read `package.json` (or `pyproject.toml` / `requirements.txt`) for dependencies
2. Identify the framework: Next.js, Vite+React, FastAPI, Express, etc.
3. Check for existing test files in `tests/e2e/` and `tests/api/`
4. Look for database configuration (Prisma, Drizzle, SQLAlchemy, etc.)
5. Check for environment variable usage throughout the codebase
6. Detect the deployment target: {{DEPLOYMENT_TARGET}}

## GENERATED FILES

Generate ALL of the following files. Each must be production-ready, not a
skeleton or placeholder.

### 1. `.github/workflows/ci.yml`
[Full CI workflow spec -- see above]

### 2. `.github/workflows/deploy-staging.yml`
[Staging deployment -- platform-specific]

### 3. `.github/workflows/deploy-production.yml`
[Production deployment -- platform-specific]

### 4. `.github/workflows/security.yml`
[Weekly security scan]

### 5. `Dockerfile` (if applicable)
[Multi-stage build for the detected tech stack]

### 6. `docker-compose.yml` (if applicable)
[Development and deployment compose file]

### 7. `.env.example`
[Document every environment variable used in the project]

### 8. `Makefile` or `scripts/` directory
[Common operational commands]

### 9. Platform-specific config
[vercel.json / railway.toml / fly.toml / task-definition.json]

## QUALITY REQUIREMENTS

- Workflows must use pinned action versions (e.g., `actions/checkout@v4`)
- Secrets must use GitHub Secrets, never hardcoded
- Dockerfile must use specific base image tags, not `latest`
- All generated files must include comments explaining non-obvious decisions
- Test the generated workflows by checking for syntax errors
- Ensure the CI workflow would actually pass given the current project state

## MCP TOOLS AVAILABLE

- `feature_get_stats` - Check project completion status
- `feature_get_summary` - Understand what the project does

You do NOT have browser automation tools. This is pure file generation.
```

#### 1.3 Client Configuration for CI/CD Agent

In `client.py`, add cicd agent type handling. The CI/CD agent gets:
- Feature MCP tools (read-only: `feature_get_stats`, `feature_get_summary`)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
- NO Playwright MCP server (pure file generation)

```python
CICD_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
]
```

#### 1.4 Prompt Loading in `prompts.py`

Add a `get_cicd_prompt()` function that:
1. Loads the `cicd_prompt` template via the standard fallback chain
2. Replaces `{{DEPLOYMENT_TARGET}}` with the detected or specified target
3. Injects project-specific context (tech stack detection results)

```python
def get_cicd_prompt(project_dir: Path, deployment_target: str | None = None) -> str:
    """Load and configure the CI/CD pipeline generation prompt."""
    prompt = load_prompt("cicd_prompt", project_dir)
    target = deployment_target or _detect_deployment_target(project_dir)
    prompt = prompt.replace("{{DEPLOYMENT_TARGET}}", target)
    return prompt


def _detect_deployment_target(project_dir: Path) -> str:
    """Auto-detect the likely deployment target from project files."""
    if (project_dir / "next.config.js").exists() or (project_dir / "next.config.mjs").exists():
        return "vercel"
    if (project_dir / "fly.toml").exists():
        return "flyio"
    if (project_dir / "railway.toml").exists():
        return "railway"
    # Default to generic Docker
    return "docker"
```

#### 1.5 Orchestrator Integration

In `parallel_orchestrator.py`, the CI/CD agent spawns after all features pass QA (or after the QA agent completes, if the QA pipeline is enabled):

```python
def _check_post_build_ready(self):
    """Check if the build is complete and spawn post-build agents."""
    if self._cicd_completed or self._cicd_running:
        return

    stats = get_feature_stats(self.db_path)
    if stats['passing'] == stats['total'] and stats['total'] > 0:
        if not self._cicd_running:
            self._spawn_cicd_agent()
```

The CI/CD agent runs as a single-turn subprocess (no loop, no continuation). It spawns once, generates files, and exits.

#### 1.6 File Changes

| File | Change |
|---|---|
| `.claude/templates/cicd_prompt.template.md` | NEW -- CI/CD generation prompt |
| `autonomous_agent_demo.py` | Add `cicd` to `--agent-type` choices, add `--deployment-target` flag |
| `client.py` | Add CI/CD agent tool filtering (no Playwright, read-only feature tools) |
| `parallel_orchestrator.py` | Add `_check_post_build_ready()`, `_spawn_cicd_agent()` |
| `prompts.py` | Add `get_cicd_prompt()` and `_detect_deployment_target()` |
| `server/routers/settings.py` | Expose `deployment_target` in settings API |
| `server/routers/agent.py` | Support `cicd` agent type in start/stop |
| `ui/src/components/SettingsModal.tsx` | Add deployment target dropdown |

---

## Feature 2: Monitoring Setup Agent

### Problem

AutoForge-built applications ship with zero observability. When something breaks in production, the user has no error tracking, no health endpoint to check, no structured logs to search, and no uptime alerts. They discover problems when customers complain.

### Solution

A new agent type (`--agent-type monitoring`) that adds production monitoring to the existing codebase. Unlike the CI/CD agent (which generates new files), the monitoring agent modifies existing files -- adding Sentry wrappers around the app entry point, injecting health check routes into the API, and adding logging middleware to the request pipeline.

### What It Sets Up

#### 2.1 Error Tracking (Sentry)

**For React frontends:**
- Install `@sentry/react` (or `@sentry/nextjs` for Next.js)
- Wrap the app root with `Sentry.ErrorBoundary`
- Add `Sentry.init()` in the entry point with DSN from env var
- Configure source map upload in the build step (Vite plugin or webpack plugin)
- Add `SENTRY_DSN` and `SENTRY_AUTH_TOKEN` to `.env.example`

**For Node.js/Express backends:**
- Install `@sentry/node`
- Add `Sentry.init()` before other middleware
- Add `Sentry.setupExpressErrorHandler(app)` after routes
- Capture unhandled rejections and uncaught exceptions

**For Python/FastAPI backends:**
- Install `sentry-sdk[fastapi]`
- Add `sentry_sdk.init()` with FastAPI integration
- Configure `traces_sample_rate` for performance monitoring
- Add `SENTRY_DSN` to environment configuration

#### 2.2 Health Check Endpoint

Add `/api/health` (or `/health`) endpoint that returns:

```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 86400,
  "timestamp": "2026-02-13T10:30:00Z",
  "checks": {
    "database": { "status": "healthy", "latency_ms": 12 },
    "memory": { "status": "healthy", "used_mb": 128, "total_mb": 512 },
    "disk": { "status": "healthy", "used_percent": 45 }
  }
}
```

The health endpoint:
- Returns 200 when healthy, 503 when degraded
- Checks database connectivity with a simple query
- Reports memory and disk usage
- Reads version from `package.json` or equivalent
- Has no authentication requirement (for load balancer and uptime monitor probes)
- Includes a `/api/health/ready` variant for Kubernetes readiness probes

#### 2.3 Analytics (Optional, Configurable)

Add a privacy-friendly analytics snippet. The user chooses during setup:

**Option A: Plausible Analytics**
- Lightweight script tag in the HTML head
- No cookies, GDPR-compliant by default
- Self-hosted or cloud option
- Tracks page views, referrers, and goals

**Option B: PostHog**
- Client-side SDK installation
- Feature flags and session replay capability
- Self-hosted or cloud option
- More powerful but heavier than Plausible

**Option C: None**
- Skip analytics entirely

The agent adds the chosen snippet to the HTML template and documents the configuration in `.env.example`.

#### 2.4 Uptime Monitoring

Generate `scripts/uptime-check.sh` (or `.ts`) that:
- Hits the `/api/health` endpoint at a configurable interval
- Parses the response for degraded checks
- Sends notifications via webhook on failure:
  - Slack webhook (if `SLACK_WEBHOOK_URL` is set)
  - Discord webhook (if `DISCORD_WEBHOOK_URL` is set)
  - Email via SMTP (if email config is set)
- Logs results to `logs/uptime.log`
- Can run as a cron job or systemd timer

Also generates configuration for UptimeRobot or Better Uptime (free tier):
- `monitoring/uptimerobot-config.json` with the health endpoint URL
- Instructions in README for one-click setup

#### 2.5 Structured Logging

**For Node.js/Express:**
- Install `pino` (or `winston`) for structured JSON logging
- Add request/response logging middleware:
  - HTTP method, URL, status code, response time
  - Request ID (via `X-Request-Id` header)
  - User agent and IP (anonymized)
  - Body size (not content) for POST/PUT requests
- Error logging with full stack traces
- Log rotation via `pino-rotate` or `logrotate` config

**For Python/FastAPI:**
- Configure `structlog` or Python's `logging` with JSON formatter
- Add `RequestLoggingMiddleware`:
  - Logs each request with method, path, status, duration
  - Assigns a unique request ID via `X-Request-Id`
  - Redacts sensitive headers (Authorization, Cookie)
- Error logging with traceback formatting
- Log rotation via `logging.handlers.RotatingFileHandler`

**Log output format:**
```json
{
  "timestamp": "2026-02-13T10:30:00.123Z",
  "level": "info",
  "request_id": "req_abc123",
  "method": "POST",
  "path": "/api/users",
  "status": 201,
  "duration_ms": 45,
  "user_agent": "Mozilla/5.0..."
}
```

### Implementation

#### 2.6 New Agent Type: `monitoring`

Add to `autonomous_agent_demo.py`:

```python
choices=["initializer", "coding", "testing", "cicd", "monitoring", "auto-update"]
```

New CLI flags:

```python
parser.add_argument(
    "--monitoring-features",
    type=str,
    default="sentry,health,logging",
    help="Comma-separated monitoring features to enable (sentry,health,analytics,uptime,logging)",
)
parser.add_argument(
    "--analytics-provider",
    choices=["plausible", "posthog", "none"],
    default="none",
    help="Analytics provider to integrate (default: none)",
)
```

#### 2.7 Prompt Template: `monitoring_prompt.template.md`

Create `.claude/templates/monitoring_prompt.template.md`:

```markdown
## YOUR ROLE - MONITORING SETUP AGENT

You are a **production monitoring agent** responsible for adding observability
to a project built by AutoForge. You will modify existing files to add error
tracking, health checks, logging, and optional analytics.

## PROJECT ANALYSIS

Before modifying any code:

1. Identify the tech stack (React, Next.js, Express, FastAPI, etc.)
2. Find the app entry point(s) (main.tsx, app.ts, main.py, etc.)
3. Find the API router setup (where routes are registered)
4. Check for existing logging or monitoring (do not duplicate)
5. Read the existing `.env.example` if present

## MONITORING FEATURES TO ENABLE

{{MONITORING_FEATURES}}

## IMPORTANT RULES

- DO NOT break existing functionality. Run lint and type-check after every change.
- DO NOT add monitoring to test files.
- All monitoring configuration must use environment variables, never hardcoded values.
- All new dependencies must be added to package.json / requirements.txt.
- The health endpoint must work without any external service configuration.
- Sentry must degrade gracefully if DSN is not configured (no crashes).
- Logging must not log sensitive data (passwords, tokens, PII).

## MCP TOOLS AVAILABLE

- `feature_get_stats` - Check project status
- `feature_get_summary` - Understand project structure

You do NOT have browser automation tools.
You DO have Edit tool access to modify existing files.
```

#### 2.8 Client Configuration for Monitoring Agent

The monitoring agent gets:
- Feature MCP tools (read-only: `feature_get_stats`, `feature_get_summary`)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
- NO Playwright MCP server
- Full write access to the project directory (unlike the review agent)

```python
MONITORING_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
]
```

#### 2.9 Orchestrator Integration

The monitoring agent runs in parallel with the CI/CD agent after the build completes. Both are post-build agents that do not conflict (CI/CD writes new files, monitoring modifies existing ones in different locations).

```python
def _spawn_post_build_agents(self):
    """Spawn CI/CD and monitoring agents in parallel after build completion."""
    if not self._cicd_completed and not self._cicd_running:
        self._spawn_cicd_agent()
    if not self._monitoring_completed and not self._monitoring_running:
        self._spawn_monitoring_agent()
```

#### 2.10 File Changes

| File | Change |
|---|---|
| `.claude/templates/monitoring_prompt.template.md` | NEW -- monitoring setup prompt |
| `autonomous_agent_demo.py` | Add `monitoring` to `--agent-type` choices, add `--monitoring-features` and `--analytics-provider` flags |
| `client.py` | Add monitoring agent tool filtering (no Playwright, read-only feature tools, full write access) |
| `parallel_orchestrator.py` | Add `_spawn_monitoring_agent()`, run parallel with CI/CD |
| `prompts.py` | Add `get_monitoring_prompt()` with feature injection |
| `server/routers/settings.py` | Expose monitoring feature toggles in settings API |
| `ui/src/components/SettingsModal.tsx` | Add monitoring feature checkboxes, analytics provider dropdown |

---

## Feature 3: Auto-Update Agent (Scheduled Maintenance)

### Problem

Dependencies rot. NPM packages release security patches weekly. Frameworks ship breaking changes quarterly. An app built today will have 10+ known vulnerabilities within 6 months if nobody updates it. AutoForge users do not want to do this maintenance manually, and most do not know how.

### Solution

A new agent type (`--agent-type auto-update`) that runs on a recurring schedule, updates dependencies safely, verifies nothing broke, and creates a PR with the changes. If tests fail, it rolls back everything and files an issue.

This is the recurring revenue engine: $9-19/month per project for "managed maintenance." Even after the initial build is complete and paid for, the customer keeps paying because the agent keeps their app current and secure.

### What It Does Each Run

#### Step 1: Security Audit

```bash
npm audit --json > /tmp/audit-before.json
# or: pip-audit --format=json > /tmp/audit-before.json
```

Record the current vulnerability count and severity breakdown.

#### Step 2: Safe Fixes

```bash
npm audit fix
# or: pip-audit --fix
```

Apply automatic fixes that respect semver constraints. These are low-risk updates (patch versions only).

#### Step 3: Outdated Check

```bash
npm outdated --json > /tmp/outdated.json
# or: pip list --outdated --format=json > /tmp/outdated.json
```

Identify all packages with newer versions available.

#### Step 4: Update Dependencies

For each outdated package:
1. Check if the update is within semver range (patch/minor) -- apply automatically
2. If it is a major version bump -- apply only if configured to do so (`--update-strategy conservative` vs `aggressive`)
3. Update one package at a time (to isolate which update causes a failure)

```bash
# Conservative (default): only semver-compatible updates
npm update

# Aggressive: update to latest, including major versions
npx npm-check-updates -u && npm install
```

#### Step 5: Run Full Test Suite

```bash
# Lint
npm run lint

# Type check
npx tsc --noEmit

# E2E tests
cd tests/e2e && npx playwright test --reporter=json

# API tests
cd tests/api && npx vitest run --reporter=json
```

All four checks must pass. Results are captured as JSON for the report.

#### Step 6a: All Tests Pass

If every check passes:

```bash
# Create a maintenance branch
git checkout -b maintenance/2026-02-13

# Commit the updates
git add -A
git commit -m "chore(deps): scheduled dependency update 2026-02-13

Updated packages:
- react: 19.0.0 -> 19.1.0
- typescript: 5.7.0 -> 5.7.2
- @sentry/react: 8.5.0 -> 8.6.1

Security fixes: 3 vulnerabilities resolved
All tests passing."

# Push and create PR
git push -u origin maintenance/2026-02-13
gh pr create \
  --title "chore(deps): scheduled maintenance 2026-02-13" \
  --body "$(cat maintenance-report.md)" \
  --label "maintenance,dependencies"

# Tag the commit
git tag maintenance/2026-02-13
```

#### Step 6b: Tests Fail

If any check fails:

```bash
# Roll back ALL changes
git checkout .
git clean -fd

# Create a GitHub issue documenting the failure
gh issue create \
  --title "Maintenance failure: 2026-02-13" \
  --body "$(cat maintenance-failure-report.md)" \
  --label "maintenance,bug"
```

Send notification to the project owner via configured webhook (Slack, Discord, or email).

#### Step 7: Generate Maintenance Report

Whether tests pass or fail, produce `maintenance-report.md`:

```markdown
# Maintenance Report: 2026-02-13

## Summary
- Status: PASS / FAIL
- Duration: 12 minutes
- Dependencies updated: 8
- Security vulnerabilities fixed: 3
- Breaking changes detected: 0

## Dependencies Updated

| Package | Old Version | New Version | Type |
|---------|------------|-------------|------|
| react | 19.0.0 | 19.1.0 | minor |
| typescript | 5.7.0 | 5.7.2 | patch |
| @sentry/react | 8.5.0 | 8.6.1 | patch |

## Security Audit

| Severity | Before | After |
|----------|--------|-------|
| Critical | 0 | 0 |
| High | 1 | 0 |
| Moderate | 2 | 0 |
| Low | 3 | 3 |

## Test Results

| Suite | Tests | Passed | Failed | Duration |
|-------|-------|--------|--------|----------|
| Lint | - | PASS | - | 3.2s |
| Type Check | - | PASS | - | 5.1s |
| E2E (Playwright) | 24 | 24 | 0 | 45s |
| API (Vitest) | 18 | 18 | 0 | 8s |

## Next Scheduled Maintenance
2026-02-20 at 09:00 UTC
```

### Scheduling Integration

The auto-update agent integrates with AutoForge's existing scheduler service (`server/services/scheduler_service.py`) and Schedule model (`api/database.py`).

#### 3.1 New Schedule Type

Extend the `Schedule` model to support maintenance schedules:

```python
class Schedule(Base):
    # ... existing fields ...

    # Schedule type: "agent" (existing) or "maintenance" (new)
    schedule_type = Column(String(20), nullable=False, default="agent")
    # For maintenance schedules: update strategy
    update_strategy = Column(String(20), nullable=True)  # "conservative" / "aggressive"
```

The `schedule_type` field differentiates between agent run schedules (existing) and maintenance schedules (new). This is backward-compatible -- existing schedules default to `"agent"`.

#### 3.2 Scheduler Service Extension

Add maintenance-specific job handling in `scheduler_service.py`:

```python
async def _handle_scheduled_maintenance(self, project_name: str, schedule_id: int, project_dir: str):
    """Handle a scheduled maintenance window start."""
    logger.info(f"Starting scheduled maintenance for '{project_name}'")

    # Spawn the auto-update agent as a subprocess
    cmd = [
        sys.executable, str(AUTOFORGE_ROOT / "autonomous_agent_demo.py"),
        "--project-dir", project_dir,
        "--agent-type", "auto-update",
        "--max-iterations", "1",
    ]

    # Add update strategy from schedule config
    schedule = self._get_schedule(schedule_id)
    if schedule and schedule.update_strategy:
        cmd.extend(["--update-strategy", schedule.update_strategy])

    process = subprocess.Popen(cmd, ...)
    # Track the process for crash recovery
```

#### 3.3 Maintenance Frequency Presets

Rather than requiring users to configure cron expressions, offer simple frequency presets:

| Preset | Schedule | Best For |
|---|---|---|
| Weekly (default) | Every Monday at 09:00 UTC | Active projects, frequent releases |
| Biweekly | Every other Monday at 09:00 UTC | Stable projects, moderate activity |
| Monthly | First Monday of month at 09:00 UTC | Low-maintenance projects |

These map to the existing `Schedule` model fields (`start_time`, `days_of_week`, `duration_minutes`). The UI translates the preset into the appropriate schedule configuration.

### Implementation

#### 3.4 New Agent Type: `auto-update`

Add to `autonomous_agent_demo.py`:

```python
choices=["initializer", "coding", "testing", "cicd", "monitoring", "auto-update"]
```

New CLI flags:

```python
parser.add_argument(
    "--update-strategy",
    choices=["conservative", "aggressive"],
    default="conservative",
    help="Dependency update strategy: conservative (semver-safe) or aggressive (latest)",
)
parser.add_argument(
    "--maintenance-frequency",
    choices=["weekly", "biweekly", "monthly"],
    default="weekly",
    help="How often to run maintenance (used when creating the schedule)",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    default=False,
    help="For auto-update: check for updates but do not apply them",
)
```

#### 3.5 Prompt Template: `auto_update_prompt.template.md`

Create `.claude/templates/auto_update_prompt.template.md`:

```markdown
## YOUR ROLE - AUTO-UPDATE MAINTENANCE AGENT

You are a **maintenance agent** responsible for keeping a project's dependencies
up to date and secure. You run on a recurring schedule. Your job is to:

1. Audit dependencies for security vulnerabilities
2. Update dependencies safely
3. Verify nothing broke
4. Create a PR if everything passes, or roll back and file an issue if not

## UPDATE STRATEGY

{{UPDATE_STRATEGY}}

- **Conservative**: Only apply semver-compatible updates (patch and minor versions).
  Do not update major versions. This is the safe default.
- **Aggressive**: Update to latest versions including major bumps. Higher risk but
  keeps the project on the cutting edge.

## DRY RUN MODE

{{DRY_RUN}}

If dry run is enabled, perform the audit and outdated check, but do NOT apply
any updates. Generate the report showing what WOULD be updated.

## WORKFLOW

### Phase 1: Audit
1. Create a clean branch: `git checkout -b maintenance/{{DATE}}`
2. Run `npm audit --json` (or equivalent) and save results
3. Record current vulnerability count by severity

### Phase 2: Update
4. Run `npm audit fix` for automatic security patches
5. Run `npm outdated --json` to identify available updates
6. Apply updates according to the update strategy
7. Run `npm install` to ensure lockfile is consistent

### Phase 3: Verify
8. Run lint: `npm run lint`
9. Run type check: `npx tsc --noEmit` (or equivalent)
10. Run E2E tests: `cd tests/e2e && npx playwright test --reporter=json`
11. Run API tests: `cd tests/api && npx vitest run --reporter=json`

### Phase 4: Report
12. Generate `maintenance-report.md` with full results

### Phase 5: Commit or Rollback
13. If ALL checks pass:
    - `git add -A && git commit -m "chore(deps): scheduled maintenance {{DATE}}"`
    - `git push -u origin maintenance/{{DATE}}`
    - Create PR via `gh pr create`
    - Tag: `git tag maintenance/{{DATE}}`
14. If ANY check fails:
    - `git checkout . && git clean -fd`
    - `git checkout main && git branch -D maintenance/{{DATE}}`
    - Create issue via `gh issue create` documenting the failure

## IMPORTANT RULES

- NEVER force-push or rebase. Only clean commits on a maintenance branch.
- NEVER update packages one at a time in separate commits -- batch all updates
  into a single commit so the PR is clean and easy to review.
- ALWAYS run ALL test suites before declaring success. Partial test runs are
  not acceptable.
- ALWAYS generate the maintenance report, even on failure.
- If the project has no test suite (no `tests/` directory), run lint and type
  check only. Note the lack of test coverage in the report.
- If `gh` CLI is not available, skip PR/issue creation and note it in the report.

## MCP TOOLS AVAILABLE

- `feature_get_stats` - Check project status
- `feature_get_summary` - Understand project scope

You do NOT have browser automation tools.
```

#### 3.6 Client Configuration for Auto-Update Agent

The auto-update agent gets:
- Feature MCP tools (read-only: `feature_get_stats`, `feature_get_summary`)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
- NO Playwright MCP server (runs tests via CLI, not browser automation)
- Full write access to the project directory (for updating packages and generating reports)

```python
AUTO_UPDATE_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
]
```

#### 3.7 Maintenance History Model

Add a new table to track maintenance run history in `api/database.py`:

```python
class MaintenanceRun(Base):
    """Record of an auto-update maintenance run."""

    __tablename__ = "maintenance_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(50), nullable=False, index=True)
    run_date = Column(DateTime, nullable=False, default=_utc_now)
    status = Column(String(20), nullable=False)  # "success", "failure", "dry_run"
    strategy = Column(String(20), nullable=False)  # "conservative", "aggressive"
    packages_updated = Column(Integer, nullable=False, default=0)
    vulnerabilities_fixed = Column(Integer, nullable=False, default=0)
    tests_passed = Column(Boolean, nullable=True)
    pr_url = Column(Text, nullable=True)
    issue_url = Column(Text, nullable=True)
    report_path = Column(Text, nullable=True)  # Path to maintenance-report.md
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
```

#### 3.8 Maintenance API Router

Create `server/routers/maintenance.py`:

```python
router = APIRouter(
    prefix="/api/projects/{project_name}/maintenance",
    tags=["maintenance"]
)

@router.get("/history")
async def get_maintenance_history(project_name: str, limit: int = 20):
    """Get maintenance run history for a project."""

@router.get("/next-run")
async def get_next_maintenance_run(project_name: str):
    """Get the next scheduled maintenance run date/time."""

@router.post("/trigger")
async def trigger_maintenance(project_name: str, dry_run: bool = False):
    """Manually trigger a maintenance run."""

@router.get("/report/{run_id}")
async def get_maintenance_report(project_name: str, run_id: int):
    """Get the full maintenance report for a specific run."""
```

#### 3.9 UI: Maintenance Tab

Add a "Maintenance" tab to the project view that shows:

**Summary card:**
- Last maintenance run: date, status (green check / red X), packages updated
- Next scheduled run: date/time with countdown
- Update strategy: conservative / aggressive (toggle)
- "Run Now" button for manual trigger

**History table:**
- Date, status, packages updated, vulnerabilities fixed, duration
- Expandable row showing the full maintenance report
- Link to PR or issue (if created)

**Schedule configuration:**
- Frequency dropdown: Weekly / Biweekly / Monthly
- Day of week selector
- Time picker (in user's local timezone, stored as UTC)
- Enable/disable toggle

#### 3.10 File Changes

| File | Change |
|---|---|
| `.claude/templates/auto_update_prompt.template.md` | NEW -- maintenance agent prompt |
| `autonomous_agent_demo.py` | Add `auto-update` to `--agent-type` choices, add `--update-strategy`, `--maintenance-frequency`, `--dry-run` flags |
| `client.py` | Add auto-update agent tool filtering (no Playwright, read-only feature tools) |
| `prompts.py` | Add `get_auto_update_prompt()` with strategy and date injection |
| `api/database.py` | Add `MaintenanceRun` model, extend `Schedule` with `schedule_type` and `update_strategy` columns |
| `server/routers/maintenance.py` | NEW -- maintenance history, trigger, and report API |
| `server/services/scheduler_service.py` | Add `_handle_scheduled_maintenance()`, maintenance schedule support |
| `server/main.py` | Register maintenance router |
| `ui/src/components/MaintenanceTab.tsx` | NEW -- maintenance history, schedule config, run trigger |
| `ui/src/components/MaintenanceReport.tsx` | NEW -- rendered maintenance report viewer |
| `ui/src/lib/types.ts` | Add `MaintenanceRun` type, extend `Schedule` type |
| `ui/src/hooks/useProjects.ts` | Add maintenance API hooks |
| `ui/src/lib/api.ts` | Add maintenance API client functions |
| `ui/src/App.tsx` | Add Maintenance tab to project view |

---

## Implementation Priority

Build these in the following order. Each feature is independently useful, so partial implementation still delivers value.

### Priority 1: CI/CD Pipeline Generator (Feature 1)

**Why first:** Generates standalone files with no dependency on the other two features. Immediate value for every project -- even without monitoring or auto-updates, having a CI/CD pipeline is a massive upgrade. This is the simplest of the three because it only generates new files and never modifies existing code.

**Estimated effort:** 2-3 days. The prompt template is the bulk of the work. Client configuration and orchestrator wiring are straightforward since they follow the same pattern as the QA agent.

### Priority 2: Monitoring Setup Agent (Feature 2)

**Why second:** Modifies existing code, which is more complex than pure file generation. But the monitoring agent needs to run before the auto-update agent because the auto-update agent benefits from having structured logging and health endpoints already in place (it can check `/api/health` as part of its verification).

**Estimated effort:** 3-4 days. The Sentry and logging integrations require careful editing of existing files. The health endpoint is straightforward.

### Priority 3: Auto-Update Agent (Feature 3)

**Why third:** Depends on the scheduler service (already exists), but also benefits from the CI/CD pipeline (the auto-update agent creates PRs that the CI workflow validates) and monitoring (health checks provide another verification signal). This is also the most complex agent because it has a rollback path and creates external artifacts (PRs, issues, tags).

**Estimated effort:** 4-5 days. The agent prompt is complex with branching logic. The maintenance history model, API router, and UI tab are new infrastructure.

---

## Cost Analysis (Max Subscription)

All agents run through Claude Code under the user's Max subscription. The cost is measured in rate limit usage (turns), not dollars.

### CI/CD Pipeline Generator

| Metric | Value |
|---|---|
| Turns per run | 30-50 |
| Playwright needed | No |
| Runs per project | Once (after build) |
| Rate limit impact | Light |

The CI/CD agent reads the project structure (~10 turns), generates 6-8 files (~20-30 turns), and verifies syntax (~5 turns). This is a one-shot agent with no continuation loop.

### Monitoring Setup Agent

| Metric | Value |
|---|---|
| Turns per run | 30-40 |
| Playwright needed | No |
| Runs per project | Once (after build) |
| Rate limit impact | Light |

The monitoring agent reads the project structure (~10 turns), modifies 5-8 existing files (~15-20 turns), and runs lint/type-check to verify (~5-10 turns). Also one-shot, no continuation loop.

### Auto-Update Agent

| Metric | Value |
|---|---|
| Turns per run | 20-30 |
| Playwright needed | No |
| Runs per project | Weekly/biweekly/monthly (recurring) |
| Rate limit impact | Light per run, cumulative over time |

The auto-update agent runs audit commands (~5 turns), applies updates (~5-10 turns), runs test suites (~5 turns), generates the report (~5 turns), and creates a PR or rolls back (~5 turns). Each run is cheap, but it recurs.

### Total Post-Build Cost

For a single project with all three agents:

| Agent | Turns | Frequency | Monthly Turns |
|---|---|---|---|
| CI/CD generator | 40 | Once | 40 (one-time) |
| Monitoring setup | 35 | Once | 35 (one-time) |
| Auto-update (weekly) | 25 | 4x/month | 100 |
| **Total first month** | | | **175** |
| **Total ongoing** | | | **100** |

For context, a single coding agent session is 100-150 turns. The entire post-build pipeline costs about the same as building one feature, and the ongoing maintenance is cheaper than building one feature per month.

---

## Revenue and Pricing

### One-Time Agents (CI/CD + Monitoring)

These run once after the build and are included in the project build price. They increase the perceived value of AutoForge without adding significant cost:

- "AutoForge doesn't just build your app. It deploys it."
- Justifies a $50-100 price increase on the build tier
- Zero ongoing cost after the initial run

### Auto-Update Agent (Recurring Revenue)

This is the SaaS play. The auto-update agent creates a recurring maintenance relationship:

| Tier | Price | Frequency | What's Included |
|---|---|---|---|
| Basic | $9/mo | Monthly | Security patches, semver-compatible updates, maintenance report |
| Standard | $14/mo | Biweekly | Above + aggressive updates, PR creation, failure notifications |
| Premium | $19/mo | Weekly | Above + priority scheduling, Slack/Discord alerts, rollback support |

**Unit economics per project:**

| Metric | Value |
|---|---|
| Revenue per project | $9-19/mo |
| Claude Max subscription cost (amortized) | ~$2-4/mo per project (100 turns/mo out of ~10,000/mo budget) |
| Infrastructure cost | $0 (runs on user's machine or existing VPS) |
| **Gross margin** | **75-90%** |

**Scale projections:**

| Projects | Monthly Revenue | Monthly Cost | Monthly Profit |
|---|---|---|---|
| 50 | $700 | $150 | $550 |
| 200 | $2,800 | $600 | $2,200 |
| 500 | $7,000 | $1,500 | $5,500 |
| 1,000 | $14,000 | $3,000 | $11,000 |

The key insight: each maintenance run is ~25 turns (very cheap), but the customer pays $9-19/month for the peace of mind that their dependencies are current and their app is not accumulating security debt. The margin is enormous because the work is trivial for an agent.

---

## Security Considerations

### CI/CD Agent

- Generated workflows must use GitHub Secrets for all credentials
- Docker images must not bake in secrets -- use runtime env vars
- The agent must not generate workflows that push to `main` without review
- Deployment credentials must be documented in `.env.example` but never committed

### Monitoring Agent

- Sentry DSN must be an environment variable, never hardcoded
- Request logging must redact `Authorization` headers, `Cookie` values, and request bodies containing passwords
- Health endpoint must not expose internal implementation details (no stack traces, no dependency versions beyond the app version)
- Analytics must be privacy-friendly (no PII tracking, no cookies without consent)

### Auto-Update Agent

- The agent must NEVER force-push to `main`
- The agent must NEVER merge its own PRs (human review required)
- The agent must NEVER run `npm audit fix --force` without explicit `aggressive` strategy
- Rollback must be a hard `git checkout .` -- no partial state
- The maintenance branch must be clearly labeled to distinguish from human work
- GitHub token permissions must be minimal: `contents: write`, `pull-requests: write`, `issues: write`

---

## Integration with Existing Systems

### Relationship to QA Pipeline (`qa-pipeline-handoff.md`)

The CI/CD agent generates workflows that run the same test suites created by the QA pipeline:
- `tests/e2e/*.spec.ts` (generated by coding agents, verified by QA agent)
- `tests/api/*.test.ts` (generated by coding agents, verified by QA agent)

The auto-update agent also runs these test suites to verify updates.

Dependency: The QA pipeline should be implemented first. Without generated test files, the CI workflow has nothing to run and the auto-update agent cannot verify safety.

### Relationship to Self-Deploy VPS (`self-deploy-vps-handoff.md`)

The CI/CD agent generates deployment configs for the VPS target. If the project was deployed via the self-deploy system, the generated `deploy-production.yml` workflow targets that same VPS.

The monitoring agent adds health endpoints that the VPS health check polling uses.

The auto-update agent can be scheduled on the VPS instance itself, running maintenance during off-peak hours.

### Relationship to Existing Scheduler Service

The auto-update agent reuses the existing `scheduler_service.py` and `Schedule` model. The new `schedule_type` column distinguishes maintenance schedules from agent run schedules. No changes to the APScheduler integration are needed -- maintenance jobs use the same `CronTrigger` mechanism.

The `ScheduleModal.tsx` UI is extended with a "Maintenance" section, or a separate "Maintenance" tab is added to the project view (preferred, to keep the schedule modal focused on agent runs).

---

## Notes for Implementation

- All three agents run through Claude Code under the Max subscription -- zero additional API cost beyond rate limit usage
- None of the three agents need Playwright. They are all "headless" agents that read code, write files, and run CLI commands
- The CI/CD and monitoring agents are one-shot (run once after build). The auto-update agent is recurring
- The auto-update agent is the revenue play. Prioritize getting it reliable and well-tested because customers will be paying monthly for it
- All three agents should be configurable via the Settings modal in the UI -- which features to enable, which platform to target, which monitoring tools to use
- The `--dry-run` flag for the auto-update agent is essential for testing. Let users see what would happen before enabling automatic updates
- Consider a "DevOps Report" that combines the CI/CD, monitoring, and first maintenance run into a single deliverable the user can review
