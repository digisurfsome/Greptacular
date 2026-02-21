# Computer Use Exploratory QA — Handoff Document

## Overview

This is **Feature 8** of the AutoForge QA Pipeline (see `qa-pipeline-handoff.md` for Features 1-7). It adds Claude's Computer Use capability as the final "human-like" testing layer that runs AFTER Playwright-based testing is complete.

**Why this exists:** Playwright tests what the DOM says. Computer Use tests what the user SEES. These are different things. A button can exist in the DOM and pass a Playwright selector check while being visually clipped behind a modal, invisible due to z-index issues, or technically clickable but off-screen. Computer Use catches these because it operates on screenshots — exactly like a real human looking at the screen.

**When it runs:** After Phase 4 (Final QA Agent) completes and produces a passing QA report. This is the absolute last step before the project ships. It's optional and can be toggled on/off via CLI flag.

**Cost model:** This is the ONE piece of the QA pipeline that does NOT run on the Max subscription. Computer Use runs through the Claude API with per-token billing. A typical exploratory sweep costs $0.50-2.00 depending on app complexity. On a $10-20K client build, this is negligible. For personal prototyping, skip it.

---

## What Computer Use Catches That Playwright Misses

| Bug Category | Playwright | Computer Use |
|---|---|---|
| Button not clickable (DOM exists but visually hidden) | MISS | CATCH |
| Modal stacking / z-index chaos | MISS | CATCH |
| Element clipped by overflow:hidden parent | MISS | CATCH |
| Button looks disabled but isn't (or vice versa) | MISS | CATCH |
| Text truncated / overlapping | MISS | CATCH |
| Focus trap in modal (can't tab out) | PARTIAL | CATCH |
| Keyboard navigation broken | PARTIAL | CATCH |
| "It just looks wrong" visual regressions | MISS (without visual regression setup) | CATCH |
| Canvas/WebGL rendering issues | MISS | CATCH |
| Scroll behavior broken (sticky headers overlapping content) | MISS | CATCH |
| Toast notifications blocking interactive elements | MISS | CATCH |
| Mobile viewport layout breaks (content off-screen) | PARTIAL | CATCH |

---

## Architecture

### The Pipeline Position

```
Phase 1: BUILD ──→ Phase 2: REVIEW ──→ Phase 3: REGRESSION ──→ Phase 4: FINAL QA
                                                                        │
                                                                        ↓ (if --computer-use flag)
                                                                Phase 5: COMPUTER USE SWEEP
                                                                        │
                                                                        ↓
                                                                Phase 5b: CONVERT FINDINGS → PLAYWRIGHT TESTS
                                                                        │
                                                                        ↓
                                                                    SHIP IT
```

### Sandboxed Environment

Computer Use MUST run in an isolated environment. The agent can click anything and type anything — it has full mouse/keyboard control. Safety requirements:

1. **Docker container** — Run the app's dev server inside a Docker container with a virtual display (Xvfb + noVNC or similar)
2. **No personal data** — The container has no saved passwords, no browser profiles, no SSH keys
3. **Network restricted** — Container can only access localhost (the app) and the Claude API
4. **Time-limited** — Maximum 15 minutes per exploratory run (prevents runaway cost)
5. **Budget cap** — Hard limit on API spend per run (configurable, default $5)

### The Practical Minimum (Phase 1 Implementation)

For the initial implementation, skip Docker and run against the local dev server. The app under test is already sandboxed in the sense that it's a new project with no real data. Add Docker isolation in a future pass.

Minimum viable setup:
1. Start the app's dev server (`npm run dev` or equivalent)
2. Call Claude API with Computer Use tools enabled
3. Give it scenario prompts (see below)
4. Capture screenshots and findings
5. Shut down when done

---

## Scenario Scripts

Computer Use runs against predefined user journey scenarios. Each scenario has a goal, a set of actions to attempt, and things to watch for.

### Scenario 1: New User Onboarding
```
Goal: Complete the app's signup/onboarding flow as a brand new user.

Actions:
- Open the app at the root URL
- Look for a signup/register button or link
- Fill out all required fields with test data
- Submit the form
- Follow any onboarding steps that appear
- Navigate to the main dashboard/home page

Watch for:
- Is the signup flow obvious? Can you find it without instructions?
- Do form fields have visible labels?
- Do error messages appear for invalid input?
- Does the success state make sense?
- Any console errors visible in the UI?
```

### Scenario 2: Core Happy Path
```
Goal: Complete the primary use case of the app (CRUD, purchase, etc.)

Actions:
- Login or navigate to the main feature area
- Create a new item/record/entry
- View the item you created
- Edit the item
- Delete the item
- Verify deletion

Watch for:
- Does create → read → update → delete work smoothly?
- Are there confirmation dialogs for destructive actions?
- Does the UI update after each action (no stale data)?
- Is loading state shown during operations?
```

### Scenario 3: Navigation Stress Test
```
Goal: Visit every page and click every navigation element.

Actions:
- Click every item in the sidebar/nav menu
- Click every link on each page
- Use the browser back button frequently
- Try to navigate to pages via URL bar (type random routes)
- Resize the window to mobile width (375px) and repeat navigation

Watch for:
- Any 404 or error pages?
- Does back button work correctly?
- Any broken links?
- Does mobile nav work (hamburger menu, etc.)?
- Any pages that take too long to load?
```

### Scenario 4: Chaos Monkey (Try to Break It)
```
Goal: Intentionally try to cause errors and unexpected behavior.

Actions:
- Submit forms with empty fields
- Submit forms with extremely long text (500+ chars)
- Submit forms with special characters (<script>, ' OR 1=1, etc.)
- Double-click submit buttons rapidly
- Open the same page in two tabs and make conflicting edits
- Disconnect from network briefly and try to submit
- Refresh the page mid-operation

Watch for:
- Does the app crash or show a white screen?
- Are error messages helpful (not just "Error")?
- Can you cause duplicate submissions?
- Does the app recover gracefully from errors?
- Any data corruption?
```

### Scenario 5: Visual Sanity Check
```
Goal: Look at every page and identify visual issues.

Actions:
- Navigate to each page
- Take a screenshot at desktop width (1280px)
- Take a screenshot at mobile width (375px)
- Scroll to the bottom of each page

Watch for:
- Any text overlapping other text?
- Any buttons or inputs cut off or hidden?
- Any horizontal scrollbar appearing (overflow)?
- Consistent spacing and alignment?
- Dark mode toggle works if present?
- Images loading correctly?
- Icons displaying (not showing □ squares)?
```

---

## Implementation

### 8.1 New CLI Flag

Add to `autonomous_agent_demo.py`:

```python
parser.add_argument("--computer-use", action="store_true", default=False,
                    help="Enable Computer Use exploratory QA after final QA pass")
parser.add_argument("--computer-use-budget", type=float, default=5.0,
                    help="Maximum API spend in dollars for Computer Use sweep (default: $5)")
parser.add_argument("--computer-use-scenarios", type=str, default="all",
                    help="Comma-separated scenario list: onboarding,happy-path,navigation,chaos,visual (default: all)")
```

### 8.2 Computer Use Runner Module

Create `computer_use_qa.py`:

```python
"""
Computer Use Exploratory QA Module

Runs Claude Computer Use against a live app to find bugs that
Playwright-based testing misses. This is the final testing layer
before an app ships.

Requires:
- ANTHROPIC_API_KEY environment variable (API billing, not Max subscription)
- A running dev server for the app under test
- Screen resolution of at least 1280x720

Usage:
    from computer_use_qa import run_exploratory_qa

    results = await run_exploratory_qa(
        app_url="http://localhost:5173",
        scenarios=["onboarding", "happy-path", "navigation", "chaos", "visual"],
        budget_limit=5.0,
        project_dir=Path("/path/to/project"),
    )
"""
```

**Module responsibilities:**
1. Start a Computer Use session via Claude API (beta headers required)
2. Feed each scenario prompt to the model one at a time
3. The model takes screenshots, clicks, types, navigates — fully autonomous
4. Capture all screenshots to `{project_dir}/.autoforge/qa-screenshots/computer-use/`
5. After each scenario, extract findings (bugs found, screenshots of issues)
6. Track API spend and stop if budget exceeded
7. Return structured results

### 8.3 Computer Use API Integration

The Claude Computer Use API requires:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",  # Computer Use works best with Sonnet
    max_tokens=4096,
    tools=[
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": 1280,
            "display_height_px": 720,
            "display_number": 1,
        }
    ],
    messages=[{
        "role": "user",
        "content": scenario_prompt
    }],
    betas=["computer-use-2025-01-24"]
)
```

**Key implementation details:**
- Use **Sonnet** (not Opus) for Computer Use — it's faster, cheaper, and specifically tuned for this
- The model returns `tool_use` blocks with `type: "computer_20250124"` containing actions (click, type, screenshot, etc.)
- You need to execute these actions in the real environment and return screenshots
- The loop continues until the model says it's done or budget is exceeded
- Each screenshot is a base64-encoded PNG sent back to the model

### 8.4 Screenshot Execution Backend

The Computer Use model sends action commands. Something needs to execute them. Options:

**Option A: PyAutoGUI (simplest, local-only)**
```python
import pyautogui
import subprocess

def execute_computer_action(action):
    if action["type"] == "click":
        pyautogui.click(action["x"], action["y"])
    elif action["type"] == "type":
        pyautogui.typewrite(action["text"])
    elif action["type"] == "screenshot":
        return pyautogui.screenshot()
    elif action["type"] == "key":
        pyautogui.press(action["key"])
    elif action["type"] == "scroll":
        pyautogui.scroll(action["clicks"])
```

**Option B: Playwright-based execution (hybrid, recommended)**
Use Playwright's browser to execute Computer Use actions. This avoids needing a real display:
```python
# The model sees screenshots from Playwright
# Actions are translated to Playwright commands
# Best of both worlds: browser sandbox + visual testing
```

This is the **recommended approach** for Phase 1:
- Start a Playwright browser with the app loaded
- Take screenshots via `page.screenshot()` and send to Computer Use model
- Translate the model's click/type/scroll actions into Playwright commands
- The model "sees" the real rendered page but actions execute in a controlled browser
- No need for Docker, Xvfb, or PyAutoGUI

### 8.5 Bug Report Generation

After all scenarios complete, generate `computer-use-qa-report.md`:

```markdown
# Computer Use Exploratory QA Report
Generated: [date]
Scenarios Run: [count]
Total API Cost: $[amount]
Bugs Found: [count]

## Scenario Results

### 1. New User Onboarding
Status: PASS / FAIL / PARTIAL
Duration: [X] steps, [Y] screenshots
Findings:
- [Description of any issues found]
- Screenshot: qa-screenshots/computer-use/scenario1-step12.png

### 2. Core Happy Path
...

## Bug Summary

| # | Severity | Description | Screenshot | Scenario |
|---|----------|-------------|------------|----------|
| 1 | HIGH | Submit button hidden behind modal overlay | step12.png | onboarding |
| 2 | MEDIUM | Text truncated on mobile viewport | step23.png | visual |
| 3 | LOW | Focus ring not visible on dark background | step31.png | navigation |

## Recommended Playwright Tests

The following bugs should be converted to permanent Playwright regression tests:

### Bug #1 → Playwright Test
```typescript
test('submit button is visible and clickable on signup page', async ({ page }) => {
  await page.goto('/signup');
  const submitBtn = page.getByRole('button', { name: /sign up|submit|register/i });
  await expect(submitBtn).toBeVisible();
  await expect(submitBtn).toBeEnabled();
  const box = await submitBtn.boundingBox();
  expect(box).not.toBeNull();
  // Verify not obscured by checking it's within viewport
  expect(box!.y + box!.height).toBeLessThan(720);
});
```
```

### 8.6 Auto-Convert Findings to Playwright Tests

This is the "killer move" — when Computer Use finds a bug, automatically generate a Playwright `.spec.ts` test so the bug can never return.

**Process:**
1. Computer Use finds bug and records: page URL, action attempted, expected vs actual behavior, screenshot
2. A conversion function takes each bug and generates a test:
   - Navigate to the page
   - Assert the element is visible and in viewport
   - Assert the element is clickable/interactable
   - Assert the expected behavior occurs
3. New test files are written to `tests/e2e/computer-use-regression/`
4. These tests become part of the permanent regression suite

**File: `computer_use_qa.py` → `generate_regression_test(bug)`**

```python
def generate_regression_test(bug: dict) -> str:
    """Generate a Playwright test from a Computer Use bug finding."""
    return f"""
import {{ test, expect }} from '@playwright/test';

// Auto-generated from Computer Use QA - Bug #{bug['id']}
// {bug['description']}
// Original scenario: {bug['scenario']}
// Screenshot: {bug['screenshot']}

test('{bug['test_name']}', async ({{ page }}) => {{
  await page.goto('{bug['url']}');
  {bug['generated_assertions']}
}});
"""
```

### 8.7 Integration with Orchestrator

In `parallel_orchestrator.py`, add the Computer Use sweep as the final step:

```python
async def _check_computer_use_ready(self):
    """Spawn Computer Use QA if all features are QA-verified and flag is set."""
    if not self.args.computer_use:
        return

    stats = get_feature_stats()
    if stats["qa_verified"] == stats["total"] and stats["total"] > 0:
        if not self._computer_use_running:
            self._computer_use_running = True
            await self._run_computer_use_sweep()
```

### 8.8 UI Integration

Add to the AutoForge UI (minimal):

1. **Settings panel**: Toggle "Enable Computer Use QA" checkbox + budget slider ($1-10)
2. **Agent Mission Control**: Show Computer Use agent as a 6th mascot when running
3. **QA report viewer**: Tab to view computer-use-qa-report.md alongside the main qa-report.md
4. **Screenshot gallery**: Grid view of Computer Use screenshots with bug annotations

---

## Feature State Machine Update

Extends the state machine from Feature 7:

```
REVIEWED ──→ QA_VERIFIED ──→ CU_VERIFIED (new final state)
                  │
                  ↓ (if --computer-use)
            COMPUTER_USE_SWEEP
                  │
                  ├── bugs found → FAILING (back to coding agent with bug notes)
                  │                    → after fix, re-run Computer Use on that scenario
                  │
                  └── no bugs → CU_VERIFIED
```

Add to `api/database.py`:
- `cu_verified` boolean column on Feature table
- Or simpler: just use the existing `qa_verified` and run Computer Use as part of that phase

**Recommended:** Don't add a new state. Computer Use is part of the QA phase. If it finds bugs, mark features as FAILING with the computer-use findings in the notes. After fix, the QA agent re-verifies, then Computer Use re-checks just the affected scenarios.

---

## Cost Analysis

### Per-Build Cost Estimates

| Scenario | Screenshots | API Tokens | Est. Cost |
|---|---|---|---|
| Onboarding (5 min) | ~15 | ~50K | $0.15 |
| Happy Path (5 min) | ~20 | ~70K | $0.20 |
| Navigation (5 min) | ~25 | ~80K | $0.25 |
| Chaos Monkey (5 min) | ~20 | ~70K | $0.20 |
| Visual Check (5 min) | ~30 | ~100K | $0.30 |
| **Total** | **~110** | **~370K** | **~$1.10** |

At $1-2 per build:
- 100 builds/month = $100-200/month
- On $10-20K client projects, this is 0.01% of revenue
- For personal prototyping, just skip it (it's optional)

### Why Sonnet, Not Opus

Computer Use is a vision + action task, not deep reasoning. Sonnet is:
- 5x cheaper per token than Opus
- Faster response times (critical for screenshot loops)
- Specifically tuned for Computer Use workflows
- Opus is overkill for "click this button and tell me what you see"

---

## Files to Create/Modify

| File | Action | Description |
|---|---|---|
| `computer_use_qa.py` | CREATE | Main module: scenario runner, API integration, bug capture |
| `autonomous_agent_demo.py` | MODIFY | Add `--computer-use`, `--computer-use-budget`, `--computer-use-scenarios` CLI flags |
| `parallel_orchestrator.py` | MODIFY | Add `_check_computer_use_ready()` to the orchestrator loop |
| `client.py` | MODIFY | Add Anthropic API client configuration for Computer Use (separate from Max subscription) |
| `server/routers/settings.py` | MODIFY | Add Computer Use toggle + budget to settings API |
| `ui/src/components/SettingsModal.tsx` | MODIFY | Add Computer Use toggle + budget slider to UI |
| `requirements.txt` | MODIFY | Add `pyautogui` (only if using Option A execution backend) |

## Dependencies

- Requires Feature 4 (Final QA Agent) to be built first — Computer Use runs after QA
- Requires Feature 7 (Orchestrator Wiring) for automated triggering
- Requires `ANTHROPIC_API_KEY` environment variable for API billing
- Does NOT require Features 1-3 or 5-6 (can work independently once QA agent exists)

## What NOT To Do

- Don't try to replace Playwright with Computer Use — they serve different purposes
- Don't run Computer Use on every feature — only at the end of the full build
- Don't use Opus for Computer Use — Sonnet is better and 5x cheaper
- Don't skip the budget cap — runaway Computer Use sessions can get expensive
- Don't run Computer Use without a dev server running — it needs a live app to test
- Don't store screenshots in git — use `.gitignore` for `qa-screenshots/computer-use/`
- Don't make this a hard requirement — it's always optional (toggle off by default)
