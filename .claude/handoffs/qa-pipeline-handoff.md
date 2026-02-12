# AutoForge QA Pipeline Handoff

## Overview

This handoff describes a comprehensive quality assurance pipeline that transforms AutoForge from "code that Claude says works" into "code with a permanent test suite and verified QA report." This is AutoForge's key differentiator against Bolt, Lovable, and every other AI code generator.

**The core problem today:** AutoForge's testing agents verify features by looking at Playwright screenshots and deciding subjectively whether something works. These tests are ephemeral -- done once, never saved, never re-runnable. There are zero programmatic assertions. A "dud" agent instance can mark broken code as passing with no safety net.

**The solution:** A 4-phase build pipeline where every feature gets a permanent test file, a code review pass, and a final QA sweep before the project is declared "done."

---

## The 4-Phase Pipeline

```
Phase 1: BUILD (existing, enhanced)
  Coding Agent builds feature + tests via Playwright
  NEW: Also generates a persistent .spec.ts test file
  Marks feature as passing

Phase 2: REVIEW (new agent type)
  Review Agent reads the code (no browser needed)
  Checks for bugs, security, logic errors, patterns
  If problems found → marks feature failing with notes
  Coding agent picks it back up and fixes
  Light and fast -- 15-30 turns, no Playwright

Phase 3: REGRESSION (existing, enhanced)
  Testing Agents run regression tests via Playwright
  NEW: Also run the generated .spec.ts files programmatically
  Catches regressions introduced by other features

Phase 4: FINAL QA (new agent type, runs once at the end)
  QA Agent runs ALL .spec.ts files end-to-end
  Exploratory testing: every page, every button, every form
  Production build verification
  Produces a QA report with pass/fail for each flow
  Fixes any issues found
```

### How It All Runs Under Max Subscription

All agents run through Claude Code, which runs under the user's Max subscription ($100/mo or $200/mo). There is zero additional API cost. The "cost" is rate limit usage:

| Agent Type | Turns/Feature | Playwright Needed | Rate Limit Impact |
|---|---|---|---|
| Coding agent | 100-150 | Yes | Heavy |
| Review agent | 15-30 | No | Light |
| Testing agent | 20-40 | Yes | Medium |
| QA agent (final) | 50-100 | Yes | Medium |

The review agent is ~20% the cost of a coding agent because it only reads -- no writing, no browser.

---

## Feature 1: Generated Playwright Test Scripts

### What Changes

The coding agent's prompt is enhanced to require generating a persistent Playwright test file for each feature it implements. Instead of ephemeral "navigate and screenshot" verification, the agent writes a proper `.spec.ts` file with real assertions.

### Implementation

#### 1.1 New Directory Convention

Every AutoForge project gets a `tests/e2e/` directory for generated test files:

```
my-project/
  tests/
    e2e/
      feature-001-user-registration.spec.ts
      feature-002-login-form.spec.ts
      feature-003-dashboard-layout.spec.ts
      playwright.config.ts          # Auto-generated config
      package.json                  # Playwright dependency
```

#### 1.2 Coding Prompt Addition (New Step 5.8)

Add after STEP 5.7 in `coding_prompt.template.md`:

```markdown
### STEP 5.8: GENERATE PERSISTENT TEST FILE (MANDATORY)

After verifying the feature manually, you MUST create a permanent Playwright test file.

**File location:** `tests/e2e/feature-{ID}-{slug}.spec.ts`

**The test file must:**
1. Import from `@playwright/test`
2. Navigate to the relevant page(s)
3. Perform the same actions you just verified manually
4. Include REAL assertions (`expect()`) -- not just screenshots
5. Test the happy path AND at least one error/edge case
6. Be completely self-contained (no shared state between tests)

**Example structure:**

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature #12: User Registration', () => {
  test('should register a new user successfully', async ({ page }) => {
    await page.goto('/register');
    await page.fill('[name="email"]', 'test-unique-12345@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.fill('[name="confirmPassword"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // Assert redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Assert welcome message
    await expect(page.locator('.welcome-message')).toContainText('Welcome');

    // Assert no console errors
    const messages = [];
    page.on('console', msg => { if (msg.type() === 'error') messages.push(msg.text()); });
    expect(messages).toHaveLength(0);
  });

  test('should show error for duplicate email', async ({ page }) => {
    await page.goto('/register');
    await page.fill('[name="email"]', 'existing@example.com');
    await page.fill('[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toBeVisible();
  });
});
```

**Quality requirements for test files:**
- Use `expect()` assertions, not just `toBeVisible()` -- assert text content, URLs, counts
- Test data should use unique identifiers (timestamps or UUIDs) to avoid collisions
- Clean up test data at the end of each test (or use test fixtures)
- Each test must be independently runnable (no ordering dependencies)
- Include at least 2 test cases per feature: happy path + one edge case

**DO NOT mark the feature as passing until the test file exists and runs successfully.**
```

#### 1.3 Playwright Config Auto-Generation

The initializer agent (or the first coding agent) generates a `tests/e2e/playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
```

And a `tests/e2e/package.json`:

```json
{
  "name": "e2e-tests",
  "private": true,
  "devDependencies": {
    "@playwright/test": "^1.50.0"
  },
  "scripts": {
    "test": "npx playwright test",
    "test:report": "npx playwright show-report"
  }
}
```

#### 1.4 Prompt Changes in `prompts.py`

The STEP 5.8 section is injected into the coding prompt. In YOLO mode, this step is NOT stripped -- even YOLO mode should generate test files (they just aren't run during YOLO). This means when you switch from YOLO to standard mode, you already have tests waiting to be executed.

#### 1.5 File Changes

| File | Change |
|---|---|
| `.claude/templates/coding_prompt.template.md` | Add STEP 5.8 after STEP 5.7 |
| `.claude/templates/initializer_prompt.template.md` | Add instruction to create `tests/e2e/` scaffold in Feature 1 |
| `prompts.py` | Keep STEP 5.8 in YOLO mode (don't strip it) |
| `client.py` | No change -- Playwright MCP already available |

---

## Feature 2: Code Review Agent

### What It Does

A lightweight agent that reads code without launching a browser. It reviews the implementation for bugs, security vulnerabilities, logic errors, and bad patterns. Runs after a coding agent marks a feature as passing, before the feature goes to regression testing.

### Why It's Cheap

The review agent:
- Does NOT use Playwright (no browser MCP server)
- Does NOT write code (read-only pass, unless it finds issues)
- Uses 15-30 turns (vs 100-150 for coding)
- Checks code quality via static analysis (lint, type-check) and manual review
- On Max subscription, this is ~20% the rate limit impact of a coding agent

### Implementation

#### 2.1 New Agent Type: `reviewer`

Add to `autonomous_agent_demo.py` CLI args:

```python
choices=["initializer", "coding", "testing", "reviewer"]
```

#### 2.2 Review Prompt Template

Create `.claude/templates/reviewer_prompt.template.md`:

```markdown
## YOUR ROLE - CODE REVIEW AGENT

You are a **code review agent** responsible for reviewing features that have been
implemented and marked as passing by a coding agent. Your job is to find bugs,
security issues, logic errors, and bad patterns BEFORE the feature goes to
regression testing.

## ASSIGNED FEATURES FOR REVIEW

You are assigned to review: {{REVIEW_FEATURE_IDS}}

### Workflow for EACH feature:

1. Call `feature_get_by_id` to get feature details
2. Identify which files were changed for this feature (check recent git commits)
3. Read every changed file thoroughly
4. Run lint and type-check on the project
5. Check the generated test file in `tests/e2e/`
6. If issues found → mark feature as failing with detailed notes
7. If clean → leave as passing (do nothing)

### What to Check

**Code Quality:**
- Logic errors, off-by-one bugs, null/undefined handling
- Race conditions in async code
- Memory leaks (event listeners not cleaned up, intervals not cleared)
- Proper error handling (try/catch, error boundaries)

**Security:**
- SQL injection, XSS, command injection
- Auth bypass (missing middleware, unchecked permissions)
- Sensitive data exposure (logging passwords, API keys in client code)
- CSRF protection on state-changing endpoints

**Data Integrity:**
- Database queries match the schema
- Foreign key references are valid
- Unique constraints are enforced
- Input validation at API boundaries

**Test Quality:**
- Review the generated `.spec.ts` file
- Are assertions meaningful? (not just `toBeVisible()`)
- Are edge cases covered?
- Would the test actually catch a regression?

### If Issues Found

Mark the feature as failing with a detailed description:

```
Use the feature_mark_failing tool with feature_id={id}
```

Then update `claude-progress.txt` with:
- Feature ID and name
- Exact file and line of each issue
- Severity (CRITICAL / HIGH / MEDIUM)
- What needs to be fixed

The orchestrator will reassign this feature to a coding agent for fixes.

**DO NOT fix the code yourself.** Your job is review only. Fixing introduces
the same "single point of judgment" problem we're trying to solve. A fresh
coding agent with full context should do the fix.

### If Feature is Clean

Leave it as passing. Move to the next assigned feature. Update
`claude-progress.txt` with a brief "Reviewed feature #X - clean" note.

## MCP TOOLS AVAILABLE

- `feature_get_stats` - Progress overview
- `feature_get_by_id` - Get feature details
- `feature_mark_failing` - Mark feature as failing (when you find issues)

You do NOT have browser automation tools. You do NOT have feature_mark_passing
(features are already passing -- you can only fail them).
```

#### 2.3 Client Configuration for Reviewer

In `client.py`, add reviewer agent type handling:

```python
REVIEWER_FEATURE_TOOLS = [
    "mcp__features__feature_get_stats",
    "mcp__features__feature_get_by_id",
    "mcp__features__feature_mark_failing",
]
```

The reviewer gets:
- Feature MCP tools (read + mark_failing only, NO mark_passing)
- Built-in tools (Read, Write, Edit, Bash, Grep, Glob)
- NO Playwright MCP server (saves resources, forces code-level review)

#### 2.4 Orchestrator Integration

In `parallel_orchestrator.py`, add review agent management similar to `_maintain_testing_agents()`:

```python
def _maintain_review_agents(self, feature_dicts):
    """Spawn review agents for recently-passed features that haven't been reviewed."""

    # Skip if review is disabled
    if self.yolo_mode or self.review_agent_ratio == 0:
        return

    # Find features that are passing but not yet reviewed
    # Track reviewed features in a set (similar to _recently_tested)
    unreviewed = [f for f in feature_dicts
                  if f['passes'] and f['id'] not in self._reviewed_features]

    if not unreviewed:
        return

    # Spawn review agent with batch of unreviewed feature IDs
    batch = [f['id'] for f in unreviewed[:self.review_batch_size]]
    self._spawn_review_agent(batch)
```

**New CLI flags:**

```python
parser.add_argument("--review-agent-ratio", type=int, default=1,
                    help="Number of review agents to maintain (0-3, default: 1)")
parser.add_argument("--review-batch-size", type=int, default=5,
                    help="Features per review agent batch (1-10, default: 5)")
```

**Review happens between coding and testing:**

```
Feature flow:
  coding agent marks passing
    → review agent checks code (new)
      → if fails: back to coding agent
      → if passes: available for regression testing
        → testing agent verifies via Playwright
```

#### 2.5 Database Change: `reviewed` Flag

Add a `reviewed` column to the Feature model in `api/database.py`:

```python
reviewed = Column(Integer, default=0)  # 0 = not reviewed, 1 = reviewed and clean
```

When a review agent finishes checking a feature and finds no issues, it sets `reviewed = 1`. When a coding agent modifies the feature (after a failing review), `reviewed` resets to 0. This prevents re-reviewing already-clean features.

New MCP tool: `feature_mark_reviewed` -- sets reviewed flag without changing pass status.

#### 2.6 File Changes

| File | Change |
|---|---|
| `.claude/templates/reviewer_prompt.template.md` | NEW -- review agent prompt |
| `autonomous_agent_demo.py` | Add `reviewer` to agent-type choices |
| `client.py` | Add reviewer tool filtering (no Playwright, limited feature tools) |
| `parallel_orchestrator.py` | Add `_maintain_review_agents()`, review batch selection, `--review-agent-ratio` flag |
| `api/database.py` | Add `reviewed` column to Feature model |
| `mcp_server/feature_mcp.py` | Add `feature_mark_reviewed` tool |
| `prompts.py` | Add `get_review_prompt()` for loading reviewer template |
| `server/routers/settings.py` | Expose review_agent_ratio in settings API |
| `ui/src/components/SettingsModal.tsx` | Add review agent ratio slider |

---

## Feature 3: Enhanced Testing Agents (Run Generated Tests)

### What Changes

Current testing agents only do manual Playwright verification (navigate, click, screenshot, judge). Enhanced testing agents ALSO run the generated `.spec.ts` files programmatically, getting deterministic pass/fail results.

### Implementation

#### 3.1 Testing Prompt Update

Add to `testing_prompt.template.md` before the manual verification step:

```markdown
### STEP 1.5: RUN GENERATED TEST FILE

Before manual verification, check if a test file exists for this feature:

```bash
ls tests/e2e/feature-{ID}-*.spec.ts
```

If the test file exists, run it:

```bash
cd tests/e2e && npx playwright test feature-{ID}-*.spec.ts --reporter=list
```

**If the test file passes:** Proceed with manual verification as a second check.
**If the test file fails:** The feature has a regression. Mark as failing immediately
and investigate. The test output tells you exactly what broke.

**If no test file exists:** Note this in claude-progress.txt as a gap. Proceed
with manual verification only.
```

#### 3.2 What This Gives You

Two layers of verification:
1. **Deterministic:** The `.spec.ts` file runs real assertions (`expect(page).toHaveURL(...)`)
2. **Exploratory:** The manual Playwright check catches visual regressions and edge cases the test file doesn't cover

If the deterministic test passes but the manual check fails, the testing agent should update the test file to cover the new failure case.

#### 3.3 File Changes

| File | Change |
|---|---|
| `.claude/templates/testing_prompt.template.md` | Add STEP 1.5 for running generated tests |

---

## Feature 4: Final QA Agent

### What It Does

A new agent type that runs once after ALL features are passing and reviewed. It performs a comprehensive end-to-end sweep of the entire application:

1. Runs the full test suite (`npx playwright test`)
2. Exploratory testing of every page, every form, every button
3. Production build verification
4. Cross-cutting checks (responsive, accessibility, performance)
5. Produces a QA report

### Implementation

#### 4.1 New Agent Type: `qa`

Add to `autonomous_agent_demo.py` CLI args:

```python
choices=["initializer", "coding", "testing", "reviewer", "qa"]
```

#### 4.2 QA Prompt Template

Create `.claude/templates/qa_prompt.template.md`:

```markdown
## YOUR ROLE - QA AGENT (FINAL PASS)

You are the **final quality assurance agent**. ALL features have been implemented,
reviewed, and regression-tested. Your job is to perform a comprehensive sweep of
the entire application before it ships.

You are the last line of defense. Nothing gets past you.

## PHASE 1: RUN THE FULL TEST SUITE

Run all generated test files:

```bash
cd tests/e2e && npx playwright test --reporter=list 2>&1
```

**Record the results.** If any tests fail:
1. Mark those features as failing via `feature_mark_failing`
2. Investigate and fix the issue
3. Re-run the failing test to confirm the fix
4. Commit the fix
5. Continue with the full sweep

## PHASE 2: EXPLORATORY TESTING

Navigate every page in the application. For each page:

1. **Navigate to the page** - verify it loads without errors
2. **Check console** - zero JavaScript errors (use `browser_console_messages`)
3. **Check network** - no failing API calls (use `browser_network_requests`)
4. **Click every button** - verify each action works
5. **Fill every form** - submit with valid data, verify success
6. **Test empty states** - what happens with no data?
7. **Test error states** - submit invalid data, verify error messages
8. **Test navigation** - back button works, links go to correct pages
9. **Take screenshots** - document the state of every page

### Systematic Page Checklist

To find all pages, check:
- The router configuration (React Router, Next.js pages, etc.)
- Navigation menus and sidebar links
- URLs referenced in code (`href`, `navigate()`, `push()`)

For EACH page found:
- [ ] Page loads without console errors
- [ ] All interactive elements are clickable
- [ ] Forms submit correctly
- [ ] Data displays correctly
- [ ] Responsive at 1280px, 768px, and 375px widths
- [ ] Loading states work (not just "Loading..." text)
- [ ] Error states are handled gracefully

## PHASE 3: PRODUCTION BUILD VERIFICATION

```bash
# Build for production
npm run build

# Serve the production build locally
npx serve dist -p 4000 &

# Run the full test suite against the production build
cd tests/e2e
BASE_URL=http://localhost:4000 npx playwright test --reporter=list

# Kill the serve process
kill %1
```

If anything breaks in the production build that worked in dev:
1. Investigate (usually env vars, tree-shaking, or SSR issues)
2. Fix the issue
3. Rebuild and re-test
4. Commit the fix

## PHASE 4: CROSS-CUTTING CHECKS

### Responsive Design
For each major page, resize the browser to test:
- Desktop (1280x720)
- Tablet (768x1024)
- Mobile (375x667)

Use `browser_resize` tool to change viewport. Take screenshots at each size.

### Accessibility Quick Check
For each page:
- Tab through all interactive elements (use `browser_press_key` with Tab)
- Verify focus indicators are visible
- Check that images have alt text (use `browser_snapshot` for accessibility tree)
- Verify form inputs have labels
- Check color contrast on critical text

### Data Persistence
1. Create test data through the UI
2. Note what was created
3. Restart the dev server
4. Verify all data persists

### Security Spot Check
- Try accessing auth-protected pages without logging in
- Try manipulating URLs to access other users' data
- Check that sensitive operations require confirmation
- Verify no API keys or secrets in client-side code

## PHASE 5: QA REPORT

After completing all phases, create `qa-report.md` in the project root:

```markdown
# QA Report
Generated: [date]
Total Features: [count]
Tests Passing: [count]/[total]

## Test Suite Results
- Total test files: [count]
- Total test cases: [count]
- Passing: [count]
- Failing: [count]
- Skipped: [count]

## Pages Tested
| Page | URL | Console Errors | Network Errors | Status |
|------|-----|---------------|----------------|--------|
| ...  | ... | 0             | 0              | PASS   |

## Production Build
- Build successful: Yes/No
- All tests pass against prod build: Yes/No
- Issues found: [list]

## Responsive Design
| Page | Desktop | Tablet | Mobile |
|------|---------|--------|--------|
| ...  | PASS    | PASS   | PASS   |

## Issues Found & Fixed
1. [Description] - Fixed in commit [hash]
2. ...

## Remaining Issues (if any)
1. [Description] - Severity: [HIGH/MEDIUM/LOW]
2. ...

## Overall Assessment
[SHIP IT / NEEDS WORK]
```

Commit the QA report:
```bash
git add qa-report.md
git commit -m "Add QA report - all features verified"
```

## MCP TOOLS AVAILABLE

### Feature Management
- `feature_get_stats` - Progress overview
- `feature_get_by_id` - Get feature details
- `feature_get_summary` - Get all features summary
- `feature_mark_failing` - Mark feature as failing
- `feature_mark_passing` - Mark feature as passing (after fixing issues)

### Browser Automation (Playwright)
All standard Playwright tools for comprehensive testing.

## IMPORTANT REMINDERS

- You are the LAST AGENT before the project ships
- EVERY page must be visited and tested
- EVERY form must be submitted
- EVERY button must be clicked
- Zero console errors is the bar
- The production build MUST work
- Your QA report is the proof that this app is ready
- If you find issues, FIX THEM -- don't just report them
```

#### 4.3 Orchestrator Integration: Auto-Trigger QA

The orchestrator detects when all features are passing and reviewed, then auto-spawns the QA agent:

```python
def _check_qa_ready(self):
    """Check if all features are passing and reviewed, trigger QA if so."""
    if self._qa_completed or self._qa_running:
        return

    stats = get_feature_stats(self.db_path)
    if stats['passing'] == stats['total'] and stats['total'] > 0:
        # All features passing -- check if all reviewed
        if self._all_features_reviewed():
            print("\n=== ALL FEATURES PASSING AND REVIEWED ===")
            print("=== SPAWNING FINAL QA AGENT ===\n")
            self._spawn_qa_agent()
```

**QA completion signals project done:**

When the QA agent finishes successfully (exit code 0), the orchestrator:
1. Emits a `project_complete` WebSocket event
2. Triggers a celebration in the UI
3. Stops all other agents
4. Creates a final git tag: `git tag -a v1.0-qa-passed -m "QA verified"`

#### 4.4 QA Agent Gets More Turns

The QA agent needs more context budget than a coding or testing agent because it's testing the ENTIRE app in one session:

```python
# In the QA agent subprocess command
if agent_type == "qa":
    max_turns = 250  # vs 150 for coding, 75 for testing
```

#### 4.5 File Changes

| File | Change |
|---|---|
| `.claude/templates/qa_prompt.template.md` | NEW -- final QA agent prompt |
| `autonomous_agent_demo.py` | Add `qa` to agent-type choices |
| `client.py` | Add QA agent tool filtering (full feature tools + Playwright) |
| `parallel_orchestrator.py` | Add `_check_qa_ready()`, `_spawn_qa_agent()`, QA completion handling |
| `mcp_server/feature_mcp.py` | Ensure `feature_get_summary` is available to QA agent |

---

## Feature 5: UI Integration

### What Changes in the UI

The UI needs to reflect the new pipeline stages and show the QA report.

#### 5.1 Feature Status Pipeline Display

Currently features show: Pending → In Progress → Passing/Failing

New display: Pending → In Progress → Passing → Reviewed → QA Verified

Add visual indicators:
- Passing (no review): Blue checkmark
- Reviewed (clean): Green checkmark with shield icon
- QA Verified: Gold checkmark with star icon

#### 5.2 Agent Mission Control Updates

Add new mascots/icons for the new agent types:
- Review Agent: "Lens" (magnifying glass mascot) -- reading code
- QA Agent: "Shield" (shield mascot) -- final defense

Show review and QA agents in the AgentMissionControl dashboard alongside coding and testing agents.

#### 5.3 QA Report Viewer

When the QA agent produces `qa-report.md`, show it in the UI:
- New tab/panel: "QA Report"
- Render the markdown with pass/fail badges
- Highlight any remaining issues
- Show the "SHIP IT" or "NEEDS WORK" assessment prominently

#### 5.4 Settings Panel Additions

Add to the Settings modal:
- **Review Agent Ratio** slider (0-3, default: 1)
- **Review Batch Size** slider (1-10, default: 5)
- **Auto QA** toggle (automatically run QA when all features pass, default: on)
- **QA Thoroughness** dropdown: Standard / Thorough (affects turn budget)

#### 5.5 File Changes

| File | Change |
|---|---|
| `ui/src/lib/types.ts` | Add `reviewed` field to Feature type, new agent types |
| `ui/src/components/AgentMissionControl.tsx` | Add Lens and Shield mascots |
| `ui/src/components/SettingsModal.tsx` | Add review and QA settings |
| `ui/src/App.tsx` | Add QA Report panel/tab |
| `server/routers/settings.py` | Expose new settings |
| `server/routers/agent.py` | Support new agent types in start/stop |

---

## Feature 6: API-Level Test Generation (Backend Endpoints)

### What It Does

For features that involve API endpoints, the coding agent also generates API-level tests using a lightweight test runner. These catch backend bugs that don't manifest visually.

### Implementation

#### 6.1 Coding Prompt Addition (Part of STEP 5.8)

Add to the test generation step:

```markdown
**For features with API endpoints**, also generate an API test file at
`tests/api/feature-{ID}-{slug}.test.ts`:

```typescript
import { describe, test, expect } from 'vitest';

describe('Feature #15: User API', () => {
  const BASE = 'http://localhost:3000/api';

  test('POST /users creates a user', async () => {
    const res = await fetch(`${BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com', name: 'Test User' }),
    });
    expect(res.status).toBe(201);
    const user = await res.json();
    expect(user.email).toBe('test@example.com');
  });

  test('POST /users rejects invalid email', async () => {
    const res = await fetch(`${BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'not-an-email', name: 'Bad' }),
    });
    expect(res.status).toBe(400);
  });

  test('GET /users/:id returns 401 without auth', async () => {
    const res = await fetch(`${BASE}/users/1`);
    expect(res.status).toBe(401);
  });
});
```

Use `vitest` for API tests (fast, no browser needed). The QA agent runs these
during Phase 1 alongside the Playwright tests.
```

#### 6.2 Test Runner Setup

The initializer creates `tests/api/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    dir: '.',
    globals: true,
    testTimeout: 10000,
  },
});
```

#### 6.3 File Changes

| File | Change |
|---|---|
| `.claude/templates/coding_prompt.template.md` | Extend STEP 5.8 with API test guidance |
| `.claude/templates/initializer_prompt.template.md` | Create `tests/api/` scaffold |
| `.claude/templates/qa_prompt.template.md` | Add API test execution to Phase 1 |

---

## Feature 7: Orchestrator Wiring and CLI Flags

### New CLI Flags

```bash
python autonomous_agent_demo.py --project-dir my-app \
  --parallel \
  --max-concurrency 3 \
  --review-agent-ratio 1 \          # NEW: 0-3 review agents (default: 1)
  --review-batch-size 5 \           # NEW: features per review batch (default: 5)
  --auto-qa \                       # NEW: auto-spawn QA when all pass (default: true)
  --qa-thoroughness standard        # NEW: standard or thorough (default: standard)
```

### Orchestrator Loop Changes

The main loop in `run_loop()` gets two new maintenance calls:

```python
# Existing
self._maintain_testing_agents(feature_dicts)

# New
self._maintain_review_agents(feature_dicts)
self._check_qa_ready()
```

### Agent Priority Order

When rate limits are tight, agents should be prioritized:

1. **Coding agents** (highest -- they produce new features)
2. **Review agents** (second -- fast and cheap, unblock features)
3. **Testing agents** (third -- catch regressions)
4. **QA agent** (only spawns when everything else is done)

The orchestrator should defer review/testing agent spawning if coding agents are at the rate limit.

### Feature State Machine

```
┌─────────┐     ┌─────────────┐     ┌──────────┐     ┌──────────┐
│ PENDING │────→│ IN_PROGRESS │────→│ PASSING  │────→│ REVIEWED │
└─────────┘     └─────────────┘     └──────────┘     └──────────┘
                      ↑                   │                │
                      │                   ↓                ↓
                      │              ┌──────────┐    ┌──────────┐
                      └──────────────│ FAILING  │    │QA VERIFIED│
                                     └──────────┘    └──────────┘
```

- `PENDING` → `IN_PROGRESS`: Coding agent claims feature
- `IN_PROGRESS` → `PASSING`: Coding agent verifies and marks passing
- `PASSING` → `REVIEWED`: Review agent finds no issues
- `PASSING` → `FAILING`: Review agent or testing agent finds issues
- `FAILING` → `IN_PROGRESS`: Coding agent picks up failed feature
- `REVIEWED` → `QA VERIFIED`: QA agent confirms in final pass
- `REVIEWED` → `FAILING`: Testing agent finds regression

### File Changes

| File | Change |
|---|---|
| `autonomous_agent_demo.py` | Add new CLI flags, pass to orchestrator |
| `parallel_orchestrator.py` | Add `_maintain_review_agents()`, `_check_qa_ready()`, priority logic |
| `api/database.py` | Add `reviewed`, `qa_verified` columns |
| `mcp_server/feature_mcp.py` | Add `feature_mark_reviewed`, `feature_mark_qa_verified` tools |

---

## Implementation Priority

Build these in order:

1. **Feature 1: Generated Test Scripts** -- Prompt change only, immediate impact. Every feature gets a permanent test file. This alone is transformative.

2. **Feature 2: Code Review Agent** -- New agent type, moderate effort. Adds the "second pair of eyes" without needing Playwright.

3. **Feature 7: Orchestrator Wiring** -- Wire review agents into the orchestrator loop. Required for Features 2 and 4 to work in the automated pipeline.

4. **Feature 3: Enhanced Testing Agents** -- Small prompt change to run generated test files. Quick win once Feature 1 is producing test files.

5. **Feature 4: Final QA Agent** -- The crown jewel. Run once at the end, produce the QA report. Requires all other pieces to be in place.

6. **Feature 6: API-Level Tests** -- Enhancement to test generation. Adds backend coverage.

7. **Feature 5: UI Integration** -- Visual polish. Can be done any time after the backend features.

---

## Cost Analysis (Max Subscription)

For a typical project with 100 features:

### Current System (No QA Pipeline)
- 100 coding agent sessions x 100-150 turns = ~12,500 turns
- ~33 testing agent sessions x 40 turns = ~1,300 turns
- **Total: ~13,800 turns**

### With QA Pipeline
- 100 coding agent sessions x 110 turns (slightly more for test generation) = ~11,000 turns
- 20 review agent sessions x 25 turns = ~500 turns
- ~33 testing agent sessions x 50 turns (running test files too) = ~1,650 turns
- 1 QA agent session x 200 turns = ~200 turns
- **Total: ~13,350 turns**

The QA pipeline is **roughly the same total cost** because:
- Test generation adds ~10 turns per coding session
- Review agents are very cheap (25 turns, no Playwright)
- Enhanced testing adds ~10 turns (running test files)
- QA agent is a one-time 200-turn cost
- BUT: fewer features fail late, reducing rework cycles

The real savings are in **reduced rework** -- catching bugs at the review stage (cheap) instead of the QA stage (expensive) or after delivery (very expensive).

---

## Competitive Positioning

### What Bolt/Lovable Give You
- Generated code
- "Hope it works"
- No tests
- No verification
- No QA report

### What AutoForge Gives You
- Generated code
- Permanent Playwright test suite for every feature
- API test suite for every endpoint
- Independent code review pass
- Continuous regression testing during build
- Final QA sweep of the entire app
- Production build verification
- Responsive design verification
- Accessibility check
- QA report with pass/fail evidence
- Git tag marking QA-verified release

**The tagline:** "AutoForge doesn't just build your app. It ships it with proof that it works."

---

## Notes for Implementation

- All agents run through Claude Code under Max subscription -- zero additional API cost
- The review agent is the key "cheap insurance" -- 20% the cost of a build agent, catches bugs early
- YOLO mode should still generate test files (they're just not run until you switch to standard mode)
- The QA agent should only run once, after all features pass and are reviewed
- The QA report (`qa-report.md`) is the deliverable that proves the app is ready
- Consider adding a `--skip-qa` flag for when users want to iterate without the final sweep
- The `reviewed` flag resets when code is modified, ensuring re-review after fixes
