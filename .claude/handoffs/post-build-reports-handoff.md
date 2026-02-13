# AutoForge Post-Build Reports Handoff

## Overview

This handoff describes three post-build agent types that run after the QA pipeline (see `qa-pipeline-handoff.md`) completes successfully. These agents produce deliverables that increase the value of every AutoForge build beyond "working code" into "shippable product with documentation, performance baseline, and security clearance."

**The core problem today:** AutoForge builds working software, and the QA pipeline verifies it works. But a "done" project still ships without documentation, performance data, or security analysis. Users must produce these artifacts manually -- or skip them entirely.

**The solution:** Three parallel post-build agents that automatically generate documentation, performance profiles, and security audits. They run after the QA agent signs off, consuming rate limit budget that would otherwise sit idle. The output is committed directly to the project as markdown reports and supporting assets.

---

## Post-Build Pipeline Position

```
Phase 1: BUILD (coding agents)
Phase 2: REVIEW (review agents)
Phase 3: REGRESSION (testing agents)
Phase 4: FINAL QA (QA agent) -- project declared "done"
Phase 5: POST-BUILD REPORTS (new -- this handoff)
  ├── Docs Agent      (generates documentation)
  ├── Performance Agent (profiles and benchmarks)
  └── Security Agent   (audits and penetration tests)
  All three run in parallel after QA passes.
```

### How It Fits Under Max Subscription

All agents run through Claude Code under the user's Max subscription. Zero additional API cost. The post-build phase uses budget after the main build is complete, so there is no contention with coding or testing agents.

| Agent Type | Turns | Playwright Needed | Rate Limit Impact |
|---|---|---|---|
| Docs agent | 50-75 | Yes (screenshots) | Medium |
| Performance agent | 40-60 | Yes (timing + CDP) | Medium |
| Security agent | 40-60 | Yes (auth testing) | Medium |

Running all three in parallel: ~60 turns total wall-clock time (they overlap).

---

## Feature 1: Auto-Generated Documentation Agent

### What It Does

A new agent type (`--agent-type docs`) that produces a complete documentation package for the built application. It scans code for API endpoints, takes Playwright screenshots of every page, generates user guides organized by user flow, and writes a changelog from git history. All output is committed to a `docs/` directory in the project.

### Output Files

```
my-project/
  docs/
    api.md              # OpenAPI/Swagger-style API documentation
    user-guide.md       # Step-by-step instructions with screenshots
    changelog.md        # Generated from git history, organized by feature
    screenshots/        # Playwright screenshots referenced by user-guide.md
      page-home.png
      page-dashboard.png
      page-settings.png
      flow-login-step-1.png
      flow-login-step-2.png
      ...
  README.md             # Setup, env vars, tech stack, deployment guide
```

### Implementation

#### 1.1 New Agent Type: `docs`

Add to `autonomous_agent_demo.py` CLI args:

```python
choices=["initializer", "coding", "testing", "docs", "performance", "security"]
```

#### 1.2 Docs Prompt Template

Create `.claude/templates/docs_prompt.template.md`:

```markdown
## YOUR ROLE - DOCUMENTATION AGENT

You are a **documentation agent** responsible for generating comprehensive
documentation for a completed application. The QA pipeline has verified that
all features work correctly. Your job is to document everything so that
developers and users can understand, deploy, and use the application.

You have access to Playwright for taking screenshots and Bash/Read/Grep for
analyzing code. You do NOT modify application code -- you only create
documentation files.

## PHASE 1: ANALYZE THE CODEBASE

Before writing any documentation, thoroughly analyze the project:

1. **Identify the tech stack** - Read `package.json`, config files, and
   entry points to understand frameworks, libraries, and tools used
2. **Map all routes/pages** - Check router configuration (React Router,
   Next.js pages, etc.) to find every navigable page
3. **Find all API endpoints** - Search for route handlers, API definitions,
   Express/FastAPI/Next.js API routes
4. **Read the app_spec** - Check `.autoforge/prompts/app_spec.txt` for the
   original specification
5. **Review git log** - Run `git log --oneline` to understand the build
   history and feature progression

## PHASE 2: API DOCUMENTATION (`docs/api.md`)

For each API endpoint found:

1. Document the HTTP method and path
2. Describe the purpose
3. List request parameters (path, query, body) with types
4. Show example request bodies (read from code or tests)
5. Document response format with example JSON
6. Note authentication requirements
7. Document error responses

**Format:**

```markdown
# API Documentation

## Authentication
[Describe auth mechanism if any]

## Endpoints

### POST /api/users
Create a new user account.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | Minimum 8 characters |
| name | string | No | Display name |

**Example Request:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Jane Doe"
}
\`\`\`

**Success Response (201):**
\`\`\`json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Jane Doe",
  "createdAt": "2025-01-15T10:30:00Z"
}
\`\`\`

**Error Responses:**
- `400` - Invalid email format or password too short
- `409` - Email already registered
```

## PHASE 3: USER GUIDE (`docs/user-guide.md`)

For each major user flow in the application:

1. **Start the dev server** if not already running
2. **Navigate to the starting page** using Playwright
3. **Take a screenshot** at each significant step using `browser_screenshot`
4. **Save screenshots** to `docs/screenshots/` with descriptive names
5. **Write step-by-step instructions** referencing the screenshots

Organize the guide by user flows, not by pages:
- "Getting Started" (first-time setup, registration/login)
- "Core Workflows" (the main things users do)
- "Settings and Configuration"
- "Advanced Features"

**Each step must include:**
- A numbered instruction ("Click the 'New Project' button")
- A screenshot (`![Step 1](screenshots/flow-create-project-step-1.png)`)
- Any notes about expected behavior

**Screenshot naming convention:** `{flow-name}-step-{N}.png` or `page-{name}.png`

## PHASE 4: README.md (Project Root)

Generate a comprehensive README.md at the project root:

```markdown
# [Project Name]

[One-paragraph description from app_spec]

## Screenshots

[2-3 key screenshots showing the application]

## Tech Stack

- **Frontend:** [framework, UI library, styling]
- **Backend:** [framework, database, ORM]
- **Testing:** [test framework, e2e tools]

## Getting Started

### Prerequisites
- Node.js [version]
- [other requirements]

### Installation
\`\`\`bash
git clone [repo]
cd [project]
npm install
\`\`\`

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | Database connection string | sqlite:./db.sqlite |
| ... | ... | ... |

### Running Locally
\`\`\`bash
npm run dev
\`\`\`

Open http://localhost:3000

### Running Tests
\`\`\`bash
npm test                    # Unit tests
npx playwright test         # E2E tests
\`\`\`

## Deployment

### Production Build
\`\`\`bash
npm run build
npm start
\`\`\`

### Docker (if applicable)
[Docker instructions if Dockerfile exists]

### Environment-Specific Notes
[Any deployment caveats]

## Project Structure
[Key directories and their purpose]

## License
[License info if found]
```

## PHASE 5: CHANGELOG (`docs/changelog.md`)

Generate from git history:

1. Run `git log --oneline --all` to get full history
2. Cross-reference commits with feature IDs from `.autoforge/features.db`
3. Group changes by feature
4. Organize chronologically with most recent first

**Format:**

```markdown
# Changelog

## [Build Date]

### Features
- **User Registration (#1)** - Email/password registration with validation
- **Dashboard (#3)** - Interactive dashboard with real-time data
- ...

### Infrastructure
- Project scaffolding and initial setup
- Database schema and migrations
- Test suite configuration

### Quality Assurance
- End-to-end test suite (X test files, Y test cases)
- QA verification completed
```

## PHASE 6: COMMIT AND VERIFY

After generating all documentation:

1. Verify all screenshot files exist and are referenced correctly
2. Verify all markdown renders correctly (no broken links)
3. Commit everything:

```bash
git add docs/ README.md
git commit -m "docs: auto-generated documentation package"
```

## MCP TOOLS AVAILABLE

### Feature Management (read-only)
- `feature_get_stats` - Progress overview
- `feature_get_summary` - Get all features summary

### Browser Automation (Playwright)
All standard Playwright tools for taking screenshots.

## IMPORTANT REMINDERS

- You are creating documentation, NOT modifying application code
- Every page must have at least one screenshot
- Screenshots must be taken at a consistent viewport size (1280x720)
- Use descriptive alt text for all images
- API docs must include real example payloads (read from code/tests)
- The README must be self-contained -- a new developer should be able to
  set up the project using only the README
```

#### 1.3 Client Configuration for Docs Agent

In `client.py`, add docs agent type handling. The docs agent gets:
- Feature MCP tools (read-only: `feature_get_stats`, `feature_get_summary`)
- Playwright MCP server (for screenshots)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)

```python
DOCS_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
]
```

The docs agent needs Write/Edit access to create documentation files but should be scoped to only create files within `docs/` and `README.md`. This is enforced by the prompt, not technically restricted (same trust model as other agents).

#### 1.4 Orchestrator Integration

In `parallel_orchestrator.py`, add post-build agent management. Post-build agents spawn after the QA agent completes successfully:

```python
def _check_post_build_ready(self):
    """Check if QA is complete and spawn post-build agents."""
    if not self._qa_completed or self._post_build_started:
        return

    print("\n=== QA COMPLETE - SPAWNING POST-BUILD AGENTS ===\n")
    self._post_build_started = True

    # All three can run in parallel -- no dependencies between them
    if self._docs_enabled:
        self._spawn_post_build_agent("docs")
    if self._performance_enabled:
        self._spawn_post_build_agent("performance")
    if self._security_enabled:
        self._spawn_post_build_agent("security")


def _spawn_post_build_agent(self, agent_type: str) -> tuple[bool, str]:
    """Spawn a post-build agent subprocess.

    Post-build agents run independently and don't compete with coding/testing
    agents since the main build is already complete.
    """
    cmd = [
        sys.executable, "-u",
        str(AUTOFORGE_ROOT / "autonomous_agent_demo.py"),
        "--project-dir", str(self.project_dir),
        "--max-iterations", "1",
        "--agent-type", agent_type,
    ]
    if self.model:
        cmd.extend(["--model", self.model])

    # Spawn with same popen_kwargs pattern as _spawn_testing_agent
    # Register in new dict: self.running_post_build_agents[agent_type] = proc
    ...
```

**New state tracking:**

```python
# In __init__:
self._post_build_started = False
self._post_build_completed: set[str] = set()  # {"docs", "performance", "security"}
self.running_post_build_agents: dict[str, subprocess.Popen] = {}

# Config flags
self._docs_enabled = True
self._performance_enabled = True
self._security_enabled = True
```

#### 1.5 Prompt Loading in `prompts.py`

Add a new prompt loader for the docs agent:

```python
def get_docs_prompt(project_dir: Path) -> str:
    """Load the documentation agent prompt."""
    prompt = load_prompt("docs_prompt", project_dir)
    # Inject app spec context so the agent knows what was built
    app_spec = _load_app_spec(project_dir)
    if app_spec:
        prompt = prompt.replace("{{APP_SPEC}}", app_spec)
    return prompt
```

#### 1.6 File Changes

| File | Change |
|---|---|
| `.claude/templates/docs_prompt.template.md` | NEW -- documentation agent prompt |
| `autonomous_agent_demo.py` | Add `docs` to `--agent-type` choices |
| `client.py` | Add docs agent tool filtering (read-only features + Playwright) |
| `parallel_orchestrator.py` | Add `_check_post_build_ready()`, `_spawn_post_build_agent()`, post-build state tracking |
| `prompts.py` | Add `get_docs_prompt()` for loading docs template with app spec injection |
| `agent.py` | Handle `docs` agent type in `run_autonomous_agent()` |

---

## Feature 2: Performance Profiling Agent

### What It Does

A new agent type (`--agent-type performance`) that benchmarks the built application and produces a comprehensive performance report. It measures page load times via the Navigation Timing API, analyzes bundle sizes, profiles API response times, tests under throttled network conditions, and scans code for common performance anti-patterns. The output is a graded `performance-report.md` committed to the project.

### Output Files

```
my-project/
  docs/
    performance-report.md    # Full performance analysis with grade
```

### Implementation

#### 2.1 New Agent Type: `performance`

Added to `autonomous_agent_demo.py` alongside `docs` (see Feature 1, section 1.1).

#### 2.2 Performance Prompt Template

Create `.claude/templates/performance_prompt.template.md`:

```markdown
## YOUR ROLE - PERFORMANCE PROFILING AGENT

You are a **performance profiling agent** responsible for benchmarking a
completed application and producing a detailed performance report. The QA
pipeline has verified that all features work. Your job is to measure how
well they perform and identify optimization opportunities.

You have access to Playwright (for page load timing and network throttling),
Bash (for build analysis), and Read/Grep (for code analysis). You do NOT
modify application code -- you only measure and report.

## PHASE 1: PAGE LOAD PERFORMANCE

For each page in the application:

1. **Navigate to the page** using Playwright
2. **Measure initial load time** using the Navigation Timing API:

```javascript
// Execute via browser_evaluate after page load
const timing = performance.getEntriesByType('navigation')[0];
const metrics = {
  dns: timing.domainLookupEnd - timing.domainLookupStart,
  tcp: timing.connectEnd - timing.connectStart,
  ttfb: timing.responseStart - timing.requestStart,
  download: timing.responseEnd - timing.responseStart,
  domInteractive: timing.domInteractive - timing.fetchStart,
  domComplete: timing.domComplete - timing.fetchStart,
  loadComplete: timing.loadEventEnd - timing.fetchStart,
};
JSON.stringify(metrics);
```

3. **Measure subsequent load** (navigate away then back -- tests caching)
4. **Record Core Web Vitals** if available:

```javascript
// LCP, FID, CLS via PerformanceObserver
const lcp = performance.getEntriesByType('largest-contentful-paint');
const cls = performance.getEntriesByType('layout-shift');
JSON.stringify({ lcp: lcp.pop()?.startTime, cls: cls.reduce((s, e) => s + e.value, 0) });
```

5. **Record the results** in a table for the report

### Throttled Network Testing

Simulate slow 3G conditions using Chrome DevTools Protocol:

```javascript
// Via browser_evaluate or CDP session
// Simulate slow 3G: 500kb/s download, 500kb/s upload, 400ms RTT
await page.context().newCDPSession(page).then(client =>
  client.send('Network.emulateNetworkConditions', {
    offline: false,
    downloadThroughput: 500 * 1024 / 8,
    uploadThroughput: 500 * 1024 / 8,
    latency: 400
  })
);
```

Re-measure page load times under throttled conditions. Record separately.

## PHASE 2: BUNDLE ANALYSIS

Analyze the production build:

1. **Run the production build:**
```bash
npm run build 2>&1
```

2. **Measure total bundle size:**
```bash
du -sh dist/
find dist/ -name "*.js" -exec ls -lh {} \;
find dist/ -name "*.css" -exec ls -lh {} \;
```

3. **Identify largest chunks:**
```bash
find dist/ -name "*.js" -exec wc -c {} \; | sort -rn | head -20
```

4. **Check for tree-shaking opportunities:**
   - Look for barrel exports (`index.ts` files that re-export everything)
   - Check for large library imports that could be narrowed
     (e.g., `import _ from 'lodash'` vs `import debounce from 'lodash/debounce'`)
   - Grep for dynamic imports that could be code-split

5. **Analyze dependencies:**
```bash
# Check for large dependencies
cat package.json | grep -E '"dependencies"' -A 100 | head -50
# If node_modules exists, find largest packages
du -sh node_modules/*/ 2>/dev/null | sort -rh | head -20
```

## PHASE 3: API RESPONSE TIMES

For each API endpoint:

1. **Start the dev server** if not running
2. **Hit each endpoint** and measure response time:

```bash
# Use curl with timing
curl -o /dev/null -s -w "time_total: %{time_total}s\ntime_connect: %{time_connect}s\ntime_starttransfer: %{time_starttransfer}s\n" http://localhost:3000/api/endpoint
```

3. **Test with payload** for POST/PUT endpoints (use example data from API docs or tests)
4. **Hit each endpoint 3 times** and average the results
5. **Flag any endpoint taking >500ms** as needing investigation

## PHASE 4: CODE ANTI-PATTERN SCAN

Search the codebase for common performance anti-patterns:

### Database / Data Fetching
- **N+1 queries** - Grep for database calls inside loops
  (`for.*await.*find`, `map.*await.*query`, `.forEach.*await.*get`)
- **Missing pagination** - API endpoints that return unbounded arrays
  (`findAll()`, `find({})` without `.limit()`)
- **Unbounded queries** - SELECT without LIMIT/WHERE on large tables
- **Missing indexes** - Check schema definitions for commonly queried
  fields without indexes

### Frontend
- **Large bundle imports** - `import X from 'large-library'` instead
  of `import { specific } from 'large-library/specific'`
- **Missing lazy loading** - Large components imported synchronously
  that could use `React.lazy()` or dynamic `import()`
- **Inline styles in loops** - Creating new style objects on every render
- **Missing memoization** - Expensive computations without `useMemo`
  or `React.memo` on frequently-rendered components
- **Unoptimized images** - Large images without width/height attributes,
  missing lazy loading attribute

### General
- **Synchronous file I/O** in request handlers
- **Missing caching headers** on static assets
- **Console.log in production** - Debug logging left in build

Record each finding with file path, line number, and severity.

## PHASE 5: GENERATE REPORT

Create `docs/performance-report.md`:

```markdown
# Performance Report

Generated: [date]
Application: [project name]

## Overall Score: [A/B/C/D/F]

Scoring criteria:
- **A**: All pages <1s load, bundle <500KB, no critical anti-patterns
- **B**: All pages <2s load, bundle <1MB, minor anti-patterns only
- **C**: Some pages >2s, bundle <2MB, some anti-patterns
- **D**: Pages >3s or bundle >2MB or critical anti-patterns
- **F**: Pages >5s or bundle >5MB or severe anti-patterns

## Page Load Times

### Normal Network
| Page | URL | Initial Load | Subsequent Load | DOM Interactive | Status |
|------|-----|-------------|-----------------|-----------------|--------|
| Home | / | 850ms | 320ms | 450ms | GOOD |
| Dashboard | /dashboard | 1200ms | 500ms | 800ms | OK |
| ... | ... | ... | ... | ... | ... |

### Throttled Network (Slow 3G)
| Page | URL | Initial Load | DOM Interactive | Status |
|------|-----|-------------|-----------------|--------|
| Home | / | 3200ms | 1800ms | ACCEPTABLE |
| ... | ... | ... | ... | ... |

## Core Web Vitals
| Page | LCP | CLS | Status |
|------|-----|-----|--------|
| Home | 1.2s | 0.05 | GOOD |
| ... | ... | ... | ... |

LCP targets: Good <2.5s, Needs Improvement <4s, Poor >4s
CLS targets: Good <0.1, Needs Improvement <0.25, Poor >0.25

## Bundle Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Total dist/ size | 1.2 MB | OK |
| Largest JS chunk | 450 KB (vendor.js) | WARNING |
| Total JS | 890 KB | OK |
| Total CSS | 120 KB | GOOD |

### Largest Files
| File | Size | Notes |
|------|------|-------|
| dist/assets/vendor-abc123.js | 450 KB | Contains React + dependencies |
| dist/assets/index-def456.js | 280 KB | Application code |
| ... | ... | ... |

### Tree-Shaking Opportunities
1. `lodash` imported as full library (450KB) -- import specific functions instead
2. ...

## API Response Times

| Endpoint | Method | Avg Response | Status |
|----------|--------|-------------|--------|
| /api/users | GET | 45ms | GOOD |
| /api/users | POST | 120ms | GOOD |
| /api/dashboard/stats | GET | 890ms | WARNING |
| ... | ... | ... | ... |

Response time targets: Good <200ms, OK <500ms, Warning <1000ms, Critical >1000ms

## Performance Anti-Patterns Found

### Critical
| Issue | File | Line | Description |
|-------|------|------|-------------|
| N+1 Query | src/api/users.ts | 45 | Database query inside forEach loop |

### Warning
| Issue | File | Line | Description |
|-------|------|------|-------------|
| Missing pagination | src/api/posts.ts | 23 | findAll() without limit |
| Large import | src/utils/helpers.ts | 1 | Full lodash import |

### Info
| Issue | File | Line | Description |
|-------|------|------|-------------|
| Console.log | src/pages/Home.tsx | 112 | Debug logging in production |

## Recommendations (Prioritized)

1. **[CRITICAL]** Fix N+1 query in users API -- use eager loading or batch query
2. **[HIGH]** Add pagination to /api/posts endpoint (currently returns all records)
3. **[MEDIUM]** Replace full lodash import with specific function imports
4. **[LOW]** Remove console.log statements from production code
```

## PHASE 6: COMMIT

```bash
git add docs/performance-report.md
git commit -m "perf: auto-generated performance report - Grade [X]"
```

## MCP TOOLS AVAILABLE

### Feature Management (read-only)
- `feature_get_stats` - Progress overview
- `feature_get_summary` - Get all features summary

### Browser Automation (Playwright)
All standard Playwright tools for page load testing and CDP access.

## IMPORTANT REMINDERS

- You are profiling, NOT optimizing -- do not change application code
- Measure each page at least 3 times and average the results
- Always test with a warm server (navigate once before measuring)
- Use consistent viewport (1280x720) for all measurements
- The performance grade should be honest -- don't inflate scores
- If the dev server crashes during testing, restart it and continue
```

#### 2.3 Client Configuration for Performance Agent

In `client.py`, add performance agent type handling. The performance agent gets:
- Feature MCP tools (read-only: `feature_get_stats`, `feature_get_summary`)
- Playwright MCP server (for page load measurement, CDP network throttling)
- Built-in tools (Read, Bash, Grep, Glob -- no Write/Edit for app code)

```python
PERFORMANCE_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
]
```

The performance agent needs Write access only for `docs/performance-report.md`. Enforce via prompt.

#### 2.4 File Changes

| File | Change |
|---|---|
| `.claude/templates/performance_prompt.template.md` | NEW -- performance profiling agent prompt |
| `autonomous_agent_demo.py` | Add `performance` to `--agent-type` choices |
| `client.py` | Add performance agent tool filtering (read-only features + Playwright) |
| `parallel_orchestrator.py` | Handled by `_spawn_post_build_agent()` (see Feature 1) |
| `prompts.py` | Add `get_performance_prompt()` for loading performance template |
| `agent.py` | Handle `performance` agent type in `run_autonomous_agent()` |

---

## Feature 3: Security Audit Agent

### What It Does

A new agent type (`--agent-type security`) that performs a comprehensive security audit of the built application. It runs `npm audit`, scans code for OWASP Top 10 vulnerabilities, tests authentication bypass via Playwright, checks for IDOR vulnerabilities, inspects HTTP security headers, and reviews dependency versions for known CVEs. The output is a graded `security-report.md`. If CRITICAL vulnerabilities are found, the agent marks the relevant features as failing to prevent shipping insecure code.

### Output Files

```
my-project/
  docs/
    security-report.md    # Full security audit with grade
```

### Implementation

#### 3.1 New Agent Type: `security`

Added to `autonomous_agent_demo.py` alongside `docs` and `performance` (see Feature 1, section 1.1).

#### 3.2 Security Prompt Template

Create `.claude/templates/security_prompt.template.md`:

```markdown
## YOUR ROLE - SECURITY AUDIT AGENT

You are a **security audit agent** responsible for performing a comprehensive
security review of a completed application. The QA pipeline has verified that
all features work. Your job is to find vulnerabilities, test attack vectors,
and produce a security report with remediation recommendations.

You have access to Playwright (for auth and IDOR testing), Bash (for npm audit
and dependency analysis), and Read/Grep (for code analysis). You do NOT modify
application code -- you audit and report. The ONE exception: if you find
CRITICAL vulnerabilities, you mark affected features as failing.

## PHASE 1: DEPENDENCY AUDIT

### npm audit

Run the built-in Node.js security audit:

```bash
npm audit --json 2>&1
npm audit 2>&1
```

Record:
- Total vulnerabilities by severity (critical, high, moderate, low)
- Specific package names and versions affected
- Whether fixes are available (`npm audit fix --dry-run`)
- Any vulnerabilities that require major version bumps

### Outdated Dependencies

```bash
npm outdated 2>&1
```

Flag any dependencies more than 2 major versions behind. Cross-reference
with known CVE databases for the installed versions.

### Lock File Integrity

Verify that `package-lock.json` exists and is consistent:

```bash
npm ci --dry-run 2>&1
```

## PHASE 2: OWASP TOP 10 CODE SCAN

Systematically scan the codebase for each OWASP Top 10 category:

### A01: Broken Access Control
- Grep for routes/endpoints without auth middleware
- Check if admin routes have proper role checks
- Look for direct object references in URL parameters (`/api/users/:id`)
- Verify that file upload paths are validated

```bash
# Find routes without auth middleware
grep -rn "router\.\(get\|post\|put\|delete\|patch\)" --include="*.ts" --include="*.js" src/
# Cross-reference with middleware usage
grep -rn "authenticate\|requireAuth\|isAuthenticated\|protect" --include="*.ts" --include="*.js" src/
```

### A02: Cryptographic Failures
- Check for hardcoded secrets, API keys, or passwords
- Verify password hashing (bcrypt/argon2, NOT MD5/SHA1)
- Check JWT configuration (algorithm, expiration, secret strength)
- Look for sensitive data in localStorage/sessionStorage

```bash
# Find potential hardcoded secrets
grep -rn "password\s*=\s*['\"]" --include="*.ts" --include="*.js" --include="*.env*" .
grep -rn "api[_-]?key\s*=\s*['\"]" --include="*.ts" --include="*.js" .
grep -rn "secret\s*=\s*['\"]" --include="*.ts" --include="*.js" .
# Check for sensitive data in client-side storage
grep -rn "localStorage\|sessionStorage" --include="*.ts" --include="*.tsx" --include="*.js" src/
```

### A03: Injection
- **SQL Injection**: Look for string concatenation in queries
- **XSS**: Look for `dangerouslySetInnerHTML`, unsanitized user input rendered in HTML
- **Command Injection**: Look for `exec()`, `spawn()` with unsanitized input
- **NoSQL Injection**: Look for `$where`, `$regex` with user input

```bash
# SQL injection vectors
grep -rn "query.*\+.*req\.\|query.*\`.*\$\{" --include="*.ts" --include="*.js" src/
# XSS vectors
grep -rn "dangerouslySetInnerHTML\|innerHTML\s*=" --include="*.ts" --include="*.tsx" --include="*.js" src/
# Command injection vectors
grep -rn "exec(\|execSync(\|spawn(" --include="*.ts" --include="*.js" src/
```

### A04: Insecure Design
- Check for rate limiting on login/registration endpoints
- Verify CAPTCHA or similar on public forms
- Look for business logic that can be abused (e.g., negative quantities)
- Check for proper input validation on all forms

### A05: Security Misconfiguration
- Check CORS configuration
- Verify CSP (Content Security Policy) headers
- Check for debug mode enabled in production
- Look for default credentials or test accounts
- Verify error messages don't leak stack traces

```bash
# CORS configuration
grep -rn "cors\|Access-Control" --include="*.ts" --include="*.js" src/
# Debug mode
grep -rn "debug\s*[:=]\s*true\|NODE_ENV.*development" --include="*.ts" --include="*.js" src/
```

### A06: Vulnerable and Outdated Components
- Covered by Phase 1 (npm audit + outdated check)

### A07: Identification and Authentication Failures
- Check session management (timeout, regeneration after login)
- Verify password policy enforcement
- Look for authentication bypass paths
- Check for secure cookie flags (httpOnly, secure, sameSite)

```bash
# Cookie configuration
grep -rn "cookie\|session" --include="*.ts" --include="*.js" src/
# Password policy
grep -rn "password.*length\|password.*min\|passwordPolicy\|validatePassword" --include="*.ts" --include="*.js" src/
```

### A08: Software and Data Integrity Failures
- Check for `eval()`, `Function()`, or `new Function()`
- Look for `JSON.parse()` on unsanitized user input
- Verify that deserialization uses allowlists

```bash
grep -rn "eval(\|new Function(\|Function(" --include="*.ts" --include="*.js" src/
```

### A09: Security Logging and Monitoring Failures
- Check if authentication events are logged
- Verify error logging captures security-relevant events
- Look for sensitive data in logs (passwords, tokens)

### A10: Server-Side Request Forgery (SSRF)
- Check for user-controlled URLs in fetch/axios/http calls
- Verify URL validation on server-side requests

```bash
grep -rn "fetch(\|axios\.\|http\.\|https\." --include="*.ts" --include="*.js" src/api/ src/server/
```

## PHASE 3: ACTIVE SECURITY TESTING (Playwright)

### Authentication Bypass Testing

1. **Identify protected pages** (pages that require login)
2. **Navigate directly to each protected page** without logging in
3. **Verify redirect to login** -- if the page loads instead of redirecting, flag as CRITICAL

```
For each protected route:
1. Navigate to the URL directly (no prior login)
2. Check if the page content loads or redirects to login
3. Check if API calls from the page return 401/403
4. Record result: PASS (redirected) or FAIL (content visible)
```

### IDOR Testing (Insecure Direct Object References)

If the app has user-specific data:

1. **Create or log in as User A** via Playwright
2. **Note User A's data identifiers** (user ID, resource IDs)
3. **Log in as User B** (or create a second account)
4. **Try to access User A's data as User B**:
   - Navigate to `/api/users/{userA_id}` as User B
   - Try `/api/resources/{userA_resource_id}` as User B
5. **Record results**: PASS (403 returned) or FAIL (data exposed)

If the app doesn't have multi-user support, skip this phase and note it.

### HTTP Security Headers

After navigating to the main page, check response headers:

```javascript
// Via browser_evaluate after page load
const entries = performance.getEntriesByType('navigation');
JSON.stringify(entries[0]?.serverTiming || 'N/A');
```

Also check headers via curl:

```bash
curl -sI http://localhost:3000 | grep -iE "x-frame-options|content-security-policy|x-content-type-options|strict-transport-security|x-xss-protection|referrer-policy|permissions-policy"
```

**Expected headers:**
- `X-Frame-Options: DENY` or `SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: ...` (any reasonable policy)
- `Referrer-Policy: strict-origin-when-cross-origin` or stricter
- `X-XSS-Protection: 0` (deprecated, CSP is preferred)

### Form Security

For each form in the application:
1. Check for CSRF tokens on state-changing forms
2. Test with XSS payloads in text inputs:
   - `<script>alert(1)</script>`
   - `"><img src=x onerror=alert(1)>`
   - `javascript:alert(1)`
3. Check if payloads are sanitized or escaped in the response
4. Record results

## PHASE 4: GENERATE REPORT

Create `docs/security-report.md`:

```markdown
# Security Audit Report

Generated: [date]
Application: [project name]

## Overall Security Score: [A/B/C/D/F]

Scoring criteria:
- **A**: No critical/high issues, all security headers present, auth solid
- **B**: No critical issues, minor high issues, most headers present
- **C**: No critical issues, some high issues, missing security headers
- **D**: Critical issues found but limited in scope
- **F**: Critical issues found with wide exposure, auth bypass, or data exposure

## Vulnerability Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | - |
| High | 2 | Needs Fix |
| Medium | 5 | Advisory |
| Low | 8 | Informational |

## Dependency Audit (`npm audit`)

### Vulnerabilities Found
| Package | Version | Severity | Description | Fix Available |
|---------|---------|----------|-------------|---------------|
| example-lib | 1.2.3 | High | Prototype pollution | Yes (2.0.0) |
| ... | ... | ... | ... | ... |

### Outdated Packages
| Package | Current | Latest | Versions Behind |
|---------|---------|--------|-----------------|
| react | 18.2.0 | 19.1.0 | 1 major |
| ... | ... | ... | ... |

## OWASP Top 10 Findings

### A01: Broken Access Control
| Finding | File | Line | Severity | Details |
|---------|------|------|----------|---------|
| Unprotected admin route | src/routes/admin.ts | 15 | HIGH | No auth middleware on /admin/users |
| ... | ... | ... | ... | ... |

### A03: Injection
| Finding | File | Line | Severity | Details |
|---------|------|------|----------|---------|
| Potential XSS | src/components/Comment.tsx | 42 | MEDIUM | Uses dangerouslySetInnerHTML |
| ... | ... | ... | ... | ... |

[Continue for each OWASP category with findings or "No issues found"]

## Authentication Testing Results

| Test | URL | Expected | Actual | Status |
|------|-----|----------|--------|--------|
| Auth bypass - Dashboard | /dashboard | Redirect to /login | Redirected | PASS |
| Auth bypass - Admin | /admin | Redirect to /login | Page loaded | FAIL |
| ... | ... | ... | ... | ... |

## IDOR Testing Results

| Test | Endpoint | Expected | Actual | Status |
|------|----------|----------|--------|--------|
| User B accesses User A profile | GET /api/users/1 | 403 Forbidden | 200 OK | FAIL |
| ... | ... | ... | ... | ... |

## HTTP Security Headers

| Header | Expected | Actual | Status |
|--------|----------|--------|--------|
| X-Frame-Options | DENY | Missing | FAIL |
| X-Content-Type-Options | nosniff | nosniff | PASS |
| Content-Security-Policy | Present | Missing | FAIL |
| Referrer-Policy | strict-origin-when-cross-origin | Missing | FAIL |

## Remediation Recommendations (Prioritized)

### Critical (Fix Before Shipping)
1. **Auth bypass on admin routes** - Add authentication middleware to all /admin/* routes
   - File: `src/routes/admin.ts`, line 15
   - Fix: Add `requireAuth('admin')` middleware

### High (Fix Soon)
2. **IDOR on user profiles** - Add ownership verification to user endpoints
   - File: `src/api/users.ts`, line 42
   - Fix: Check `req.user.id === params.id` before returning data

### Medium (Should Fix)
3. **Missing security headers** - Add helmet middleware
   - File: `src/server.ts`
   - Fix: `app.use(helmet())` with appropriate CSP

### Low (Nice to Have)
4. **Console.log with sensitive data** - Remove debug logging
   - File: `src/auth/login.ts`, line 28
   - Fix: Remove `console.log(user)` statement

## Features Marked as Failing

If CRITICAL vulnerabilities were found, the following features were marked
as failing to prevent shipping insecure code:

| Feature ID | Feature Name | Reason |
|------------|-------------|--------|
| #12 | Admin Dashboard | Auth bypass -- no middleware on admin routes |
| ... | ... | ... |

These features must be fixed by a coding agent before the project ships.
```

## PHASE 5: MARK FEATURES FAILING (IF CRITICAL ISSUES FOUND)

If you find CRITICAL severity issues:

1. Identify which feature(s) are responsible for the vulnerable code
2. Mark those features as failing via `feature_mark_failing`
3. Include the security finding in the failure reason

This ensures the orchestrator will reassign these features to a coding
agent for remediation. The project will NOT be declared complete until
the security issues are resolved.

**Only mark features as failing for CRITICAL issues.** High/medium/low
issues are documented in the report as recommendations but do not block
shipping.

## PHASE 6: COMMIT

```bash
git add docs/security-report.md
git commit -m "security: auto-generated security audit - Grade [X]"
```

## MCP TOOLS AVAILABLE

### Feature Management
- `feature_get_stats` - Progress overview
- `feature_get_summary` - Get all features summary
- `feature_get_by_id` - Get feature details (to identify which feature owns vulnerable code)
- `feature_mark_failing` - Mark feature as failing (only for CRITICAL vulnerabilities)

### Browser Automation (Playwright)
All standard Playwright tools for authentication and IDOR testing.

## IMPORTANT REMINDERS

- You are auditing, NOT fixing -- do not change application code
- The ONE exception: mark features as failing for CRITICAL vulnerabilities
- Be thorough but avoid false positives -- only flag real issues
- Include exact file paths and line numbers for every finding
- Test all attack vectors systematically, don't skip categories
- The security grade should be honest -- do not inflate scores
- If the app has no auth system, skip auth-specific tests and note that
- IDOR testing requires at least two user accounts -- create them if possible
```

#### 3.3 Client Configuration for Security Agent

In `client.py`, add security agent type handling. The security agent gets:
- Feature MCP tools (read + mark_failing for critical issues)
- Playwright MCP server (for auth bypass and IDOR testing)
- Built-in tools (Read, Bash, Grep, Glob -- no Write/Edit for app code, Write for report only)

```python
SECURITY_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_summary",
    "mcp__features__feature_get_by_id",
    "mcp__features__feature_mark_failing",
]
```

The security agent is the only post-build agent that can mark features as failing. This is intentional -- a CRITICAL security vulnerability should block the project from shipping.

#### 3.4 Feature Failing Flow

When the security agent marks a feature as failing:

1. The feature re-enters the build pipeline (coding agent picks it up)
2. The coding agent fixes the security issue
3. The feature goes through review and regression testing again
4. Once all features pass again, the QA agent re-runs
5. After QA passes, the security agent re-runs to verify the fix

To prevent infinite loops, the orchestrator tracks security audit runs:

```python
# In orchestrator
self._security_audit_count = 0
MAX_SECURITY_AUDIT_RUNS = 3  # Prevent infinite security -> fix -> security loops
```

If the security agent still finds CRITICAL issues after 3 runs, the project is declared complete with a warning in the report, and the remaining issues are documented as "unresolved."

#### 3.5 File Changes

| File | Change |
|---|---|
| `.claude/templates/security_prompt.template.md` | NEW -- security audit agent prompt |
| `autonomous_agent_demo.py` | Add `security` to `--agent-type` choices |
| `client.py` | Add security agent tool filtering (features with mark_failing + Playwright) |
| `parallel_orchestrator.py` | Handled by `_spawn_post_build_agent()`, plus security re-run logic |
| `prompts.py` | Add `get_security_prompt()` for loading security template |
| `agent.py` | Handle `security` agent type in `run_autonomous_agent()` |

---

## Feature 4: Orchestrator Wiring and CLI Flags

### New CLI Flags

```bash
python autonomous_agent_demo.py --project-dir my-app \
  --concurrency 3 \
  --auto-post-build \                # NEW: auto-run post-build agents (default: true)
  --skip-docs \                      # NEW: skip documentation agent
  --skip-performance \               # NEW: skip performance profiling agent
  --skip-security \                  # NEW: skip security audit agent
  --post-build-only \                # NEW: run only post-build agents (skip build/QA)
  --agent-type docs \                # NEW: run docs agent directly
  --agent-type performance \         # NEW: run performance agent directly
  --agent-type security              # NEW: run security agent directly
```

Add to `autonomous_agent_demo.py`:

```python
parser.add_argument(
    "--auto-post-build",
    action="store_true",
    default=True,
    help="Automatically run post-build agents after QA passes (default: true)",
)
parser.add_argument(
    "--skip-docs",
    action="store_true",
    default=False,
    help="Skip the documentation agent in post-build phase",
)
parser.add_argument(
    "--skip-performance",
    action="store_true",
    default=False,
    help="Skip the performance profiling agent in post-build phase",
)
parser.add_argument(
    "--skip-security",
    action="store_true",
    default=False,
    help="Skip the security audit agent in post-build phase",
)
parser.add_argument(
    "--post-build-only",
    action="store_true",
    default=False,
    help="Run only post-build agents (assumes build and QA already complete)",
)

# Update agent-type choices
parser.add_argument(
    "--agent-type",
    choices=["initializer", "coding", "testing", "docs", "performance", "security"],
    default=None,
    help="Agent type (used by orchestrator to spawn specialized subprocesses)",
)
```

### Orchestrator Loop Changes

The main `run_loop()` in `parallel_orchestrator.py` gets a new check after QA completion:

```python
# Existing (from QA pipeline handoff)
self._check_qa_ready()

# New: After QA completes, spawn post-build agents
self._check_post_build_ready()

# New: Check if post-build is complete
if self._check_post_build_complete():
    self._finalize_project()
    break
```

### Post-Build Completion Flow

```python
def _check_post_build_complete(self) -> bool:
    """Check if all enabled post-build agents have finished."""
    if not self._post_build_started:
        return False

    expected = set()
    if self._docs_enabled:
        expected.add("docs")
    if self._performance_enabled:
        expected.add("performance")
    if self._security_enabled:
        expected.add("security")

    return self._post_build_completed >= expected


def _finalize_project(self):
    """Called when all post-build agents complete successfully."""
    print("\n=== ALL POST-BUILD REPORTS COMPLETE ===")
    print("=== PROJECT FINALIZED ===\n")

    # Create final git tag
    # git tag -a v1.0-complete -m "Build complete with docs, performance, and security reports"

    # Emit project_complete WebSocket event with report paths
    if self.on_status:
        self.on_status(-1, "project_finalized")
```

### Post-Build Agent Process Limits

Post-build agents do NOT count toward `MAX_TOTAL_AGENTS` because they only run after all coding and testing agents have finished. They have their own limit:

```python
MAX_POST_BUILD_AGENTS = 3  # One of each type, all running in parallel
```

### Security Agent Re-Run Logic

If the security agent marks features as failing, the orchestrator must:

1. Re-enter the build loop (coding agents fix the failing features)
2. After features pass again, re-run QA
3. After QA passes, re-run ONLY the security agent (not docs/performance)
4. Cap at `MAX_SECURITY_AUDIT_RUNS` to prevent infinite loops

```python
def _handle_security_failures(self):
    """Handle security agent finding critical issues."""
    self._security_audit_count += 1

    if self._security_audit_count >= MAX_SECURITY_AUDIT_RUNS:
        print("WARNING: Security issues persist after max audit runs. Completing with warnings.")
        return

    # Reset QA and post-build state to re-enter the pipeline
    self._qa_completed = False
    self._qa_running = False
    self._post_build_started = False
    self._post_build_completed.discard("security")

    # Re-enter the build loop -- coding agents will pick up failing features
    print(f"Security audit #{self._security_audit_count}: Critical issues found. Re-entering build pipeline.")
```

### File Changes

| File | Change |
|---|---|
| `autonomous_agent_demo.py` | Add new CLI flags, post-build agent types, pass config to orchestrator |
| `parallel_orchestrator.py` | Add `_check_post_build_ready()`, `_check_post_build_complete()`, `_finalize_project()`, `_handle_security_failures()`, post-build state tracking, security re-run logic |
| `agent.py` | Handle new agent types in `run_autonomous_agent()` dispatch |
| `prompts.py` | Add `get_docs_prompt()`, `get_performance_prompt()`, `get_security_prompt()` |

---

## Feature 5: UI Integration

### What Changes in the UI

The UI needs to show the post-build phase and display the generated reports.

#### 5.1 Post-Build Status Display

Add a new section to the project dashboard after "QA Verified":

```
Pipeline: BUILD → REVIEW → TEST → QA → POST-BUILD
                                        ├── Docs: Generating... / Complete
                                        ├── Performance: Grade B
                                        └── Security: Grade A
```

Visual indicators:
- Post-build not started: Gray with clock icon
- Post-build in progress: Cyan with spinner animation
- Post-build complete: Green with checkmark and grade badge

#### 5.2 Agent Mission Control Updates

Add new mascots/icons for the post-build agent types. Following the existing pattern in `AgentMissionControl.tsx` (Spark, Fizz, Octo, Hoot, Buzz):

- Docs Agent: "Quill" (quill pen mascot) -- writing documentation
- Performance Agent: "Bolt" (lightning bolt mascot) -- speed testing
- Security Agent: "Lock" (padlock mascot) -- security auditing

Show post-build agents in the AgentMissionControl dashboard in a separate "Post-Build" section below the main build agents.

#### 5.3 Report Viewer Panel

When reports are generated, show them in the UI:

- New tab group: "Reports" (alongside existing tabs)
- Three sub-tabs: "Documentation", "Performance", "Security"
- Each tab renders the corresponding markdown report with:
  - Grade badge (A/B/C/D/F) with color coding
  - Collapsible sections for each report phase
  - Tables rendered as proper HTML tables
  - Syntax-highlighted code blocks
  - Pass/fail badges on individual findings

Use an existing markdown renderer or render the tables natively. The reports are markdown files read from the project filesystem via the existing filesystem API.

#### 5.4 Settings Panel Additions

Add to the Settings modal (`SettingsModal.tsx`):

- **Auto Post-Build Reports** toggle (default: on)
- **Documentation Agent** toggle (default: on)
- **Performance Agent** toggle (default: on)
- **Security Agent** toggle (default: on)

These map to the `--skip-docs`, `--skip-performance`, `--skip-security` CLI flags.

#### 5.5 WebSocket Events

New WebSocket event types for post-build phase:

```typescript
// Post-build agent status
type PostBuildStatus = {
  type: "post_build_status";
  agent: "docs" | "performance" | "security";
  status: "running" | "completed" | "failed";
  grade?: string;  // "A" | "B" | "C" | "D" | "F" -- only on completed
};

// Project finalized (all post-build complete)
type ProjectFinalized = {
  type: "project_finalized";
  reports: {
    docs: boolean;
    performance: { grade: string } | null;
    security: { grade: string; criticalCount: number } | null;
  };
};
```

#### 5.6 File Changes

| File | Change |
|---|---|
| `ui/src/lib/types.ts` | Add `PostBuildStatus`, `ProjectFinalized` event types, post-build agent types |
| `ui/src/hooks/useWebSocket.ts` | Handle `post_build_status` and `project_finalized` events |
| `ui/src/components/AgentMissionControl.tsx` | Add Quill, Bolt, Lock mascots for post-build agents |
| `ui/src/components/SettingsModal.tsx` | Add post-build report toggles |
| `ui/src/App.tsx` | Add Reports tab group with sub-tabs |
| `ui/src/components/ReportViewer.tsx` | NEW -- markdown report renderer with grade badges |
| `server/routers/settings.py` | Expose post-build settings (docs/performance/security enabled) |
| `server/routers/agent.py` | Support post-build agent types, emit post-build WebSocket events |

---

## Implementation Priority

Build these in order:

1. **Feature 4: Orchestrator Wiring** -- Wire the post-build phase into the orchestrator loop. This is the foundation that all three agents depend on. Includes CLI flags, state tracking, and the `_spawn_post_build_agent()` pattern.

2. **Feature 1: Documentation Agent** -- Highest standalone value. Produces the most immediately useful artifacts (README, user guide, API docs). Good first agent to test the post-build spawning flow end-to-end.

3. **Feature 3: Security Audit Agent** -- Second priority because it can mark features as failing, which requires the security re-run logic in the orchestrator. This is the most architecturally complex of the three agents.

4. **Feature 2: Performance Profiling Agent** -- Third priority because it is purely advisory (no feature-failing logic). Straightforward to implement once the post-build framework is in place.

5. **Feature 5: UI Integration** -- Visual polish. Can be done any time after the backend features. Start with the Settings toggles and agent status display, then add the Report Viewer panel.

---

## Cost Analysis (Max Subscription)

### Post-Build Cost for a Typical Project

| Agent | Turns | Duration (est.) | Runs Once? |
|---|---|---|---|
| Docs agent | 50-75 | ~15-20 min | Yes |
| Performance agent | 40-60 | ~10-15 min | Yes |
| Security agent | 40-60 | ~10-15 min | Usually once, up to 3x if critical issues found |
| **Total (parallel)** | **~60-75** (wall clock) | **~20 min** | - |

### Compared to Manual Effort

| Task | Human Time | Agent Turns | Agent Wall-Clock |
|---|---|---|---|
| Write API docs | 2-4 hours | ~20 turns | 5 min |
| Screenshot every page + write user guide | 3-6 hours | ~30 turns | 10 min |
| Write README with setup instructions | 1-2 hours | ~15 turns | 4 min |
| Run npm audit + analyze results | 30 min | ~10 turns | 3 min |
| OWASP code scan | 2-4 hours | ~20 turns | 5 min |
| Auth/IDOR testing | 1-2 hours | ~15 turns | 4 min |
| Performance profiling | 2-3 hours | ~40 turns | 10 min |
| **Total** | **12-21 hours** | **~150 turns** | **~20 min (parallel)** |

The post-build phase costs ~150 total turns across all three agents (only ~60-75 wall-clock turns since they run in parallel). For a project that consumed ~13,000 turns during build, this is an additional ~1% cost for deliverables that would take a human 12-21 hours.

### Full Pipeline Cost (Build + QA + Post-Build)

For a typical project with 100 features:

| Phase | Turns | Wall-Clock Impact |
|---|---|---|
| Build (coding agents) | ~11,000 | Hours |
| Review agents | ~500 | Overlaps with build |
| Testing agents | ~1,650 | Overlaps with build |
| QA agent | ~200 | After build |
| **Post-build agents** | **~150** | **After QA, parallel** |
| **Grand Total** | **~13,500** | - |

---

## Competitive Positioning

### What Bolt/Lovable Give You
- Generated code
- No documentation
- No performance data
- No security audit
- "Hope it works, hope it's fast, hope it's secure"

### What AutoForge Gives You (with Post-Build Reports)
- Generated code
- Permanent test suite
- Code review pass
- Regression testing
- QA sweep with report
- **API documentation with request/response examples**
- **User guide with screenshots of every page**
- **Professional README with setup instructions**
- **Changelog organized by feature**
- **Performance report with page load times and bundle analysis**
- **Security audit with OWASP Top 10 coverage**
- **Performance and security grades (A/B/C/D/F)**
- **Critical security issues block shipping automatically**

**The expanded tagline:** "AutoForge doesn't just build your app. It ships it with documentation, performance benchmarks, and a security clearance."

---

## Notes for Implementation

- All three post-build agents run through Claude Code under Max subscription -- zero additional API cost
- Post-build agents run in parallel after QA completes, so they don't contend with build agents
- The docs agent needs Playwright for screenshots -- reuse the same Playwright MCP server config as the QA agent
- The performance agent uses CDP (Chrome DevTools Protocol) for network throttling -- this works via the existing Playwright MCP server's `browser_evaluate` tool
- The security agent is the only post-build agent that can fail features -- this is intentional and prevents shipping critical vulnerabilities
- YOLO mode should skip post-build agents entirely (no QA phase means no post-build trigger)
- Consider adding a `--post-build-only` flag for re-running reports on an already-built project without rebuilding
- The `post-build-only` flag should verify that all features are passing before running reports
- Reports are committed to git, so they are versioned alongside the code they describe
- If the user has already built a project and wants to add reports retroactively, `--post-build-only` handles this
- The security agent's ability to mark features as failing creates a feedback loop with the build pipeline -- the `MAX_SECURITY_AUDIT_RUNS` cap prevents infinite loops
- For the performance agent's throttled network testing, the CDP approach requires Chromium (not Firefox) -- the agent should use `--browser chromium` for this phase if the default is Firefox
