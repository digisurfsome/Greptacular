# CI Pipeline + Notification Widget — Setup Guide

Drop this into any new project to get the full automated CI pipeline: push, auto-fix on failure (3 retries), auto-merge on success (with 30s veto window), git pull, and a non-intrusive blinking notification in your UI header. Never steals focus. Never takes over your screen.

---

## Prerequisites

- GitHub repo with GitHub Actions enabled
- `gh` CLI installed and authenticated (`gh auth login`)
- `ANTHROPIC_API_KEY` added as a GitHub Actions secret
- React + TypeScript frontend (adaptable to other frameworks)
- Python FastAPI backend (adaptable to Express/other)

---

## Quick Start Checklist

1. Copy the auto-fix workflow YAML into `.github/workflows/ci-auto-fix.yml`
2. Customize the CI check commands for your project type
3. Add `ANTHROPIC_API_KEY` as a GitHub Actions secret
4. Copy the CI monitor service into your backend
5. Copy the CI router and register it
6. Copy the TypeScript types and API functions
7. Copy the widget component
8. Place the widget in your header bar
9. Push and watch it work

---

## Step 1: GitHub Actions Auto-Fix Workflow

Create `.github/workflows/ci-auto-fix.yml`. This triggers when your main CI workflow fails on a `claude/` branch, dispatches a Claude agent to fix the code, and retries up to 3 times.

```yaml
name: Auto-fix CI Failures

on:
  workflow_run:
    workflows: ["CI"]  # <-- CHANGE THIS to match your CI workflow name
    types: [completed]

jobs:
  auto-fix:
    runs-on: ubuntu-latest
    if: >
      github.event.workflow_run.conclusion == 'failure' &&
      startsWith(github.event.workflow_run.head_branch, 'claude/')
    permissions:
      contents: write
      actions: read
      pull-requests: write
    steps:
      - name: Count previous autofix attempts
        id: check-loop
        uses: actions/github-script@v7
        with:
          script: |
            const branch = '${{ github.event.workflow_run.head_branch }}';
            const MAX_RETRIES = 3;
            const commits = await github.rest.repos.listCommits({
              owner: context.repo.owner,
              repo: context.repo.repo,
              sha: branch,
              per_page: MAX_RETRIES + 1
            });
            let autofixCount = 0;
            for (const commit of commits.data) {
              if (commit.commit.message.includes('[autofix]')) {
                autofixCount++;
              } else {
                break;
              }
            }
            if (autofixCount >= MAX_RETRIES) {
              core.setOutput('skip', 'true');
              core.setOutput('attempt', String(autofixCount));
            } else {
              core.setOutput('skip', 'false');
              core.setOutput('attempt', String(autofixCount + 1));
            }

      - name: Checkout failing branch
        if: steps.check-loop.outputs.skip == 'false'
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_branch }}
          fetch-depth: 0

      - name: Get failure details
        if: steps.check-loop.outputs.skip == 'false'
        id: failures
        uses: actions/github-script@v7
        with:
          script: |
            const runId = ${{ github.event.workflow_run.id }};
            const jobs = await github.rest.actions.listJobsForWorkflowRun({
              owner: context.repo.owner,
              repo: context.repo.repo,
              run_id: runId,
              filter: 'latest'
            });
            let errorDetails = [];
            for (const job of jobs.data.jobs) {
              if (job.conclusion === 'failure') {
                try {
                  const log = await github.rest.actions.downloadJobLogsForWorkflowRun({
                    owner: context.repo.owner,
                    repo: context.repo.repo,
                    job_id: job.id
                  });
                  const lines = log.data.split('\n');
                  const trimmed = lines.slice(-200).join('\n');
                  errorDetails.push(`=== Job: ${job.name} ===\n${trimmed}`);
                } catch (e) {
                  const failedSteps = job.steps
                    .filter(s => s.conclusion === 'failure')
                    .map(s => s.name);
                  errorDetails.push(`=== Job: ${job.name} ===\nFailed steps: ${failedSteps.join(', ')}`);
                }
              }
            }
            const fs = require('fs');
            fs.writeFileSync('/tmp/ci-errors.txt', errorDetails.join('\n\n'));

      # CUSTOMIZE THESE STEPS for your project's language/toolchain
      - name: Setup Python
        if: steps.check-loop.outputs.skip == 'false'
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup Node
        if: steps.check-loop.outputs.skip == 'false'
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install project dependencies
        if: steps.check-loop.outputs.skip == 'false'
        run: |
          pip install -r requirements.txt
          cd ui && npm ci

      - name: Install Claude Code
        if: steps.check-loop.outputs.skip == 'false'
        run: npm install -g @anthropic-ai/claude-code

      - name: Configure git
        if: steps.check-loop.outputs.skip == 'false'
        run: |
          git config user.name "Claude Autofix"
          git config user.email "autofix@claude.ai"

      - name: Run Claude to fix failures
        if: steps.check-loop.outputs.skip == 'false'
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          ERRORS=$(cat /tmp/ci-errors.txt)
          ATTEMPT="${{ steps.check-loop.outputs.attempt }}"

          # CUSTOMIZE the verification commands below for your project
          claude -p "CI checks failed on this branch (auto-fix attempt ${ATTEMPT} of 3). Here are the error logs:

          $ERRORS

          Please:
          1. Read the failing files and understand what went wrong
          2. Fix the code so the CI checks pass
          3. Run the checks locally to verify:
             - ruff check .
             - cd ui && npm run lint && npm run build
          4. Git add and commit your fixes with a message starting with '[autofix] attempt ${ATTEMPT}:'

          Only fix what's broken. Don't refactor or change anything else." \
            --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
            --max-turns 25

      - name: Push fixes
        if: steps.check-loop.outputs.skip == 'false'
        run: |
          if git diff --name-only origin/${{ github.event.workflow_run.head_branch }} HEAD | grep -q .; then
            git push origin HEAD:${{ github.event.workflow_run.head_branch }}
          fi

      - name: Comment on PR (fix applied)
        if: steps.check-loop.outputs.skip == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            const branch = '${{ github.event.workflow_run.head_branch }}';
            const attempt = '${{ steps.check-loop.outputs.attempt }}';
            const prs = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              head: `${context.repo.owner}:${branch}`,
              state: 'open'
            });
            if (prs.data.length > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: prs.data[0].number,
                body: `**Auto-fix attempt ${attempt}/3 applied.** CI is re-running now.`
              });
            }

      - name: Comment on PR (max retries reached)
        if: steps.check-loop.outputs.skip == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const branch = '${{ github.event.workflow_run.head_branch }}';
            const runUrl = `https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${{ github.event.workflow_run.id }}`;
            const prs = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              head: `${context.repo.owner}:${branch}`,
              state: 'open'
            });
            if (prs.data.length > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: prs.data[0].number,
                body: `**Auto-fix exhausted (3 attempts).** Manual fix needed.\n\n[View CI logs](${runUrl})`
              });
            }
```

### Customizing for your project type

**Node.js only project:**
```yaml
- name: Install dependencies
  run: npm ci

# In the Claude prompt:
# - npm run lint
# - npm run build
# - npm test
```

**Go project:**
```yaml
- name: Setup Go
  uses: actions/setup-go@v5
  with:
    go-version: '1.22'

# In the Claude prompt:
# - go vet ./...
# - go build ./...
# - go test ./...
```

**Rust project:**
```yaml
- name: Setup Rust
  uses: dtolnay/rust-toolchain@stable

# In the Claude prompt:
# - cargo clippy
# - cargo build
# - cargo test
```

---

## Step 2: Backend CI Monitor Service

This is the brain. It polls GitHub Actions via `gh` CLI every 15 seconds. State machine:

```
idle → running → passed → (30s veto window) → merging → merged
                → failed → fixing (auto-fix agent) → running → ...
```

**Key config you can change:**
- `POLL_INTERVAL = 15` — seconds between GitHub API checks
- `VETO_SECONDS = 30` — countdown before auto-merge

**The service file:** Copy `server/services/ci_monitor.py` into your backend's services directory.

Core functions your router will call:
- `start_monitoring(working_directory, veto_seconds)` — begins polling
- `stop_monitoring(working_directory)` — stops polling
- `get_state(working_directory)` — returns current status
- `veto_merge(working_directory)` — cancels auto-merge during countdown
- `cleanup_all_monitors()` — call on server shutdown

**For Express/non-FastAPI backends:** The service is pure Python with asyncio. For Node.js, rewrite the `gh` CLI calls using `child_process.execSync` and replace `asyncio.sleep` with `setInterval`. The state machine logic stays identical.

---

## Step 3: Backend REST Router

Endpoints to expose:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/ci/monitor/start` | Start monitoring a directory |
| POST | `/api/ci/monitor/stop` | Stop monitoring |
| GET | `/api/ci/status?working_directory=...` | Get current status |
| POST | `/api/ci/veto` | Cancel auto-merge |
| GET | `/api/ci/all` | All monitored directories |

**The router file:** Copy `server/routers/ci_status.py` and register it in your app:

```python
from .routers.ci_status import router as ci_status_router
app.include_router(ci_status_router)
```

Don't forget cleanup on shutdown:
```python
from .services.ci_monitor import cleanup_all_monitors
# In your lifespan/shutdown handler:
await cleanup_all_monitors()
```

---

## Step 4: Frontend Types

Add to your types file:

```typescript
export type CIPipelineStatus =
  | 'idle' | 'running' | 'passed' | 'failed' | 'fixing'
  | 'merging' | 'merged' | 'veto' | 'exhausted' | 'error'

export interface CIRunInfo {
  run_id: number
  status: string
  conclusion: string | null
  branch: string
  commit_sha: string
  commit_message: string
  url: string
  started_at: string | null
  autofix_attempt: number
}

export interface CIEvent {
  type: string
  message: string
  timestamp: string
}

export interface CIStatusResponse {
  working_directory: string
  owner: string
  repo: string
  branch: string
  status: CIPipelineStatus
  latest_run: CIRunInfo | null
  veto_deadline: number | null
  veto_remaining: number | null
  pr_number: number | null
  pr_url: string | null
  autofix_attempt: number
  error_message: string | null
  history: CIEvent[]
}
```

## Step 5: Frontend API Functions

```typescript
export async function startCIMonitor(workingDirectory: string, vetoSeconds = 30) {
  return fetchJSON('/ci/monitor/start', {
    method: 'POST',
    body: JSON.stringify({ working_directory: workingDirectory, veto_seconds: vetoSeconds }),
  })
}

export async function getCIStatus(workingDirectory: string) {
  return fetchJSON(`/ci/status?working_directory=${encodeURIComponent(workingDirectory)}`)
}

export async function vetoCIMerge(workingDirectory: string) {
  return fetchJSON('/ci/veto', {
    method: 'POST',
    body: JSON.stringify({ working_directory: workingDirectory }),
  })
}
```

---

## Step 6: The Widget Component

Copy `ui/src/components/workspace/CIStatusWidget.tsx` into your project.

**Dependencies:** React, TanStack Query, Lucide React icons. Swap Lucide for any icon library — the component uses: `Loader2` (spinner), `Check`, `X`, `Wrench`, `GitMerge`, `AlertTriangle`, `Ban`, `CircleDot`.

**Design principles (DO NOT violate these):**
1. NEVER steal focus or open a new tab
2. NEVER refresh the user's screen
3. Compact by default — just a tiny colored pill in the header
4. Blinks to get attention, click to expand for details
5. Success toast slides in top-right, auto-dismisses after 8s
6. Veto button (X) is always visible during countdown

**Where to place it:** In your app's header bar, near other status indicators. Example:

```tsx
<header className="flex items-center gap-2 px-4 h-12">
  <Logo />
  <nav>{/* your nav */}</nav>
  <div className="ml-auto flex items-center gap-2">
    <CIStatusWidget workingDirectory={projectPath} />
    <UserMenu />
  </div>
</header>
```

---

## Customization

| Setting | Default | Where to change |
|---------|---------|-----------------|
| Veto countdown | 30s | `VETO_SECONDS` in ci_monitor.py, or pass via API |
| Poll interval | 15s | `POLL_INTERVAL` in ci_monitor.py |
| Max auto-fix retries | 3 | `MAX_RETRIES` in ci-auto-fix.yml |
| Success toast duration | 8s | `setTimeout` in CIStatusWidget.tsx |
| Branch prefix filter | `claude/` | `startsWith` in ci-auto-fix.yml |
| Widget poll interval | 5s | `refetchInterval` in CIStatusWidget.tsx |

---

## The Flow

```
You push code
    │
    ▼
CI runs ──────────────── Widget shows: spinning cyan "CI RUNNING"
    │
    ├─ PASS ──────────── Widget blinks green "28s" countdown
    │   │                 You can hit X to cancel
    │   │
    │   ▼ (30s passes)
    │   Auto-merge PR ── Widget: "MERGING"
    │   git pull ──────── Widget: "Deployed" toast (top-right, fades in 8s)
    │                     You never left what you were doing.
    │
    └─ FAIL ──────────── Widget blinks amber "FIX 1/3"
        │                 Auto-fix agent dispatched via GitHub Actions
        │
        ├─ Fix works ──── CI re-runs → back to PASS flow above
        └─ 3 fails ────── Widget blinks red "NEEDS HELP"
                          Manual intervention needed
```

---

## Step 7: Git Activity Widget

A compact git commit tracker that sits alongside the CI Status Widget.

**What it does:**
- Small square button with a git icon
- Polls every 10s for the last 10 commits via `GET /api/ci/commits`
- Badge in the corner shows unseen commit count
- Blinks cyan when new commits arrive
- Click: dropdown shows commits with SHA, message, author, relative time
- Clicking marks all as seen, badge resets to 0
- "Processing Log" button in dropdown opens the slide-out panel

**Backend endpoint** (in `ci_status.py` router):
```python
@router.get("/commits", response_model=list[GitCommitResponse])
async def get_git_commits(working_directory: str, limit: int = 10):
    # Runs: git log -{limit} --format=%H|%h|%s|%an|%aI
```

**Frontend component:** `GitActivityWidget.tsx`
- Props: `workingDirectory: string | null`, `onOpenProcessingLog?: () => void`
- Place in header bar of any page that needs commit visibility

---

## Step 8: Processing Log (CI Event Timeline)

A slide-out panel showing the full lifecycle of each commit through CI.

**What it does:**
- Shows last 10 commits, each expandable to reveal CI events
- Events are persisted to SQLite (`ci_events.db`) — survives restarts
- Timeline per commit: pushed → CI started → passed/failed → auto-fix → merged → deployed
- "Stuck" detection: flags commits in progress for >1 hour with amber warning
- Duration calculation for completed commits

**Backend:**
- SQLite table `ci_events` in `.autoforge/ci_events.db` per project
- Every `_add_event()` call in the CI monitor persists to SQLite
- `GET /api/ci/timeline?working_directory=...&commit_sha=...` — returns timeline events
- Events include: `commit_sha`, `event_type`, `message`, `timestamp`, `metadata`

**Frontend component:** `ProcessingLogPanel.tsx`
- Props: `workingDirectory`, `open`, `onClose`
- Slide-out from right, backdrop overlay, closes on Escape
- Groups events by commit SHA with status badges (DEPLOYED / FAILED / IN PROGRESS / POSSIBLY STUCK)

---

## Error Handling: Anthropic API Key Auto-Fix Retry

The `ci-auto-fix.yml` workflow handles CI failures automatically:

1. CI fails on a `claude/` branch
2. GitHub Actions workflow triggers, checks retry count (max 3)
3. Downloads failure logs from the failed run
4. Invokes Claude Code with the error context and verification commands
5. Claude fixes the code, commits with `[autofix] attempt N:` prefix
6. Pushes the fix, CI re-runs
7. If all 3 attempts fail, comments "exhausted" on the PR

**Key configuration:**
- `ANTHROPIC_API_KEY` must be set as a GitHub Actions secret
- Only triggers on branches matching `claude/` prefix
- Max 25 Claude turns per fix attempt
- Verification commands must match your CI checks exactly

**Handling API key errors:**
- If the Anthropic API key is invalid/expired, the auto-fix workflow will fail at the Claude invocation step
- The CI monitor will show "NEEDS HELP" (exhausted) status
- Check GitHub Actions logs for "authentication" or "invalid API key" errors
- Rotate the key in GitHub Settings → Secrets → `ANTHROPIC_API_KEY`

**Handling terminal shutdown (computer goes to sleep):**
- The CI monitor runs server-side — if your dev server stops, monitoring pauses
- Events are persisted to SQLite, so no data is lost
- When the server restarts, monitoring resumes automatically on the next page load
- Commits pushed while offline will be picked up on the next poll cycle
- If a merge was in the veto window when shutdown occurred, it will NOT auto-merge (safe behavior)

---

## Prompt for Claude Code

When you're ready to set this up in a new project, paste this:

> Set up the CI pipeline notification system from my Greptacular project. Use the guide at `docs/CI-PIPELINE-SETUP-GUIDE.md` as reference. I need:
> 1. The GitHub Actions auto-fix workflow (customize CI commands for this project)
> 2. The backend CI monitor service and router (including SQLite event persistence)
> 3. The frontend CI Status Widget in my header bar (blinking indicator)
> 4. The Git Activity Widget (commit badge + dropdown) in the same header
> 5. The Processing Log slide-out panel (CI event timeline per commit)
> 6. Wire everything up so it polls and shows status
>
> Key requirements:
> - Widget must NEVER steal focus, NEVER open new tabs, NEVER refresh my screen
> - Just a blinking indicator I check when I'm ready
> - Git activity shows unseen commit count with badge
> - Processing log shows full timeline: commit → CI → fix → merge → deploy
> - Events persist to SQLite so I never lose history
> - Auto-fix retries up to 3 times using Anthropic API key in GitHub secrets
> - If my machine goes to sleep, no data loss — picks back up on restart
