# Upstream Feature Watcher

## What This Is

An automated system built into AutoForge that monitors the upstream AutoForge repository (the original open-source repo by Leon) for new merged features, analyzes each one against your diverged fork, tells you what it does, whether it's worth porting, how hard it would be, and — if you approve — adapts and installs it into your codebase automatically.

Your fork has diverged significantly from upstream. You can't `git pull` anymore. But the upstream community is shipping good features, and you want the best of them without manually diffing PRs and hand-porting code. This system does that for you.

## The Problem

1. Upstream repo is actively developed — new features merged weekly
2. Your fork has diverged: modified files, new architecture, custom features
3. Manual approach: notice a PR → read the diff → figure out what files you'd need to change → rewrite it for your codebase → test it. This takes hours per feature.
4. Without monitoring, you miss features entirely until you stumble on them months later

## How It Works (4 Stages)

### Stage 1: Monitor

Poll the upstream GitHub repo for newly merged PRs to main. Run on a schedule (every 6 hours, or manual trigger from UI).

```
Upstream repo: https://github.com/autoforge-ai/autoforge (or whatever Leon's repo URL is)
Watch: Merged PRs to main branch
Frequency: Every 6 hours (configurable)
Storage: SQLite table tracking seen PRs
```

### Stage 2: Analyze

For each new merged PR, an agent reads:
- The PR title, description, and discussion
- The full diff (every file changed, every line added/removed)
- The SAME files in YOUR repo (current state)
- Your BLUEPRINT.md (to understand what you've already built)

Then produces an analysis:

```
Feature: "Add real-time progress streaming via SSE"
PR: #247 by contributor_x
Files touched upstream: 3 (server/routers/agent.py, ui/src/hooks/useWebSocket.ts, server/services/process_manager.py)

Divergence check:
  - server/routers/agent.py: HEAVILY DIVERGED (yours has 340 lines of custom code)
  - ui/src/hooks/useWebSocket.ts: MODERATELY DIVERGED (yours adds workspace support)
  - server/services/process_manager.py: LIGHTLY DIVERGED (minor changes)

What it does: Adds Server-Sent Events as an alternative to WebSocket for agent progress updates. Improves reliability on flaky connections.

Relevance to your fork: HIGH — your workspace chat would benefit from SSE fallback
Conflicts with your code: MODERATE — the WebSocket hook has your custom workspace additions
Adaptation effort: MODERATE — ~2 hours agent work to port and adapt

Recommendation: PORT — valuable feature, moderate effort, improves reliability
Confidence: 82%
```

### Stage 3: Present

Show the analysis in your AutoForge UI. A new section in the dashboard or a dedicated page:

```
┌─────────────────────────────────────────────────────────────┐
│ Upstream Feature Watcher                          [Refresh] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ NEW (3)                                                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ "Real-time progress streaming via SSE"                  │ │
│ │ PR #247 · merged 2 days ago · 3 files · Moderate effort │ │
│ │ Recommendation: PORT (82% confident)                    │ │
│ │ [View Analysis] [Approve Port] [Skip] [Bookmark]       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ "Batch feature reordering via drag-and-drop"            │ │
│ │ PR #251 · merged 1 day ago · 5 files · Heavy effort     │ │
│ │ Recommendation: SKIP (you already have this)            │ │
│ │ [View Analysis] [Approve Port] [Skip] [Bookmark]       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ "Fix: agent crash on empty features.db"                 │ │
│ │ PR #253 · merged 6 hours ago · 1 file · Clean drop-in  │ │
│ │ Recommendation: PORT (95% confident)                    │ │
│ │ [View Analysis] [Approve Port] [Skip] [Bookmark]       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ PORTED (12) · SKIPPED (8) · BOOKMARKED (2)                 │
└─────────────────────────────────────────────────────────────┘
```

### Stage 4: Execute

When you click "Approve Port":

1. Agent gets the upstream diff + your current file versions
2. Reads the analysis (what the feature does, where conflicts are)
3. Writes the adapted code into your codebase
4. Runs lint + type check to verify it compiles
5. Creates a git commit: `Port upstream PR #247: Real-time progress streaming via SSE`
6. Updates BLUEPRINT.md with what was ported and any adaptations made
7. Marks the PR as "ported" in the watcher database

If the port fails (lint errors, conflicts too complex), the agent reports back with what went wrong and you can decide to skip or manually intervene.

---

## Architecture

### Database Schema

Add to the main AutoForge database (or a dedicated `~/.autoforge/upstream_watcher.db`):

```sql
-- Upstream repo configuration
CREATE TABLE watched_repos (
    id INTEGER PRIMARY KEY,
    repo_url VARCHAR(500) NOT NULL,
    repo_owner VARCHAR(100) NOT NULL,
    repo_name VARCHAR(100) NOT NULL,
    branch VARCHAR(100) DEFAULT 'main',
    github_token_ref VARCHAR(100),  -- reference to encrypted token storage
    poll_interval_hours INTEGER DEFAULT 6,
    last_polled_at DATETIME,
    enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tracked PRs
CREATE TABLE upstream_prs (
    id INTEGER PRIMARY KEY,
    watched_repo_id INTEGER NOT NULL,
    pr_number INTEGER NOT NULL,
    pr_title VARCHAR(500),
    pr_author VARCHAR(100),
    pr_url VARCHAR(500),
    pr_description TEXT,
    merged_at DATETIME,
    files_changed TEXT,  -- JSON array of file paths
    diff_stats TEXT,  -- JSON: {additions: N, deletions: N, files: N}

    -- Analysis results (populated by Stage 2)
    analysis TEXT,  -- Full analysis markdown
    divergence_level VARCHAR(20),  -- 'clean', 'light', 'moderate', 'heavy'
    recommendation VARCHAR(20),  -- 'port', 'skip', 'bookmark', 'already_have'
    confidence INTEGER,  -- 0-100
    effort_estimate VARCHAR(20),  -- 'trivial', 'light', 'moderate', 'heavy'
    relevance_score INTEGER,  -- 0-100 how relevant to your fork
    conflict_summary TEXT,  -- Brief description of conflicts

    -- Status tracking
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'analyzing', 'analyzed', 'approved', 'porting', 'ported', 'skipped', 'bookmarked', 'failed'
    ported_at DATETIME,
    port_commit_hash VARCHAR(40),
    port_notes TEXT,  -- Any notes about adaptations made

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (watched_repo_id) REFERENCES watched_repos(id),
    UNIQUE(watched_repo_id, pr_number)
);

-- Analysis run log
CREATE TABLE watcher_runs (
    id INTEGER PRIMARY KEY,
    watched_repo_id INTEGER NOT NULL,
    run_type VARCHAR(20),  -- 'scheduled', 'manual'
    prs_found INTEGER DEFAULT 0,
    prs_analyzed INTEGER DEFAULT 0,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error TEXT,
    FOREIGN KEY (watched_repo_id) REFERENCES watched_repos(id)
);
```

### Backend Services

#### `server/services/upstream_watcher.py`

Core service that handles polling, analysis, and porting.

```python
class UpstreamWatcher:
    """
    Monitors upstream repos for merged PRs and manages the
    analyze → present → port pipeline.
    """

    async def poll(self, repo_id: int) -> list[dict]:
        """
        Check upstream for new merged PRs since last poll.

        Uses GitHub API: GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated
        Filter: only merged PRs, only since last_polled_at

        For each new PR:
        1. Fetch PR metadata (title, description, author, merge date)
        2. Fetch PR diff via GitHub API
        3. Store in upstream_prs table with status='new'

        Returns list of new PRs found.
        """
        pass

    async def analyze(self, pr_id: int) -> dict:
        """
        Analyze a single upstream PR against our fork.

        1. Read the PR diff from stored data
        2. For each file in the diff, read OUR version of that file
        3. Read BLUEPRINT.md for context on what we've built
        4. Send to Claude (Haiku for speed, Sonnet for complex PRs):

        Prompt:
        "You are analyzing an upstream PR to determine if it should be
        ported to a diverged fork. Here is the upstream diff, our current
        versions of the affected files, and our modification history.

        Analyze:
        1. What does this PR do? (2-3 sentences)
        2. For each file: divergence level (clean/light/moderate/heavy)
        3. Do we already have this feature? (check BLUEPRINT.md)
        4. How relevant is this to our fork? (0-100)
        5. Estimated effort to port (trivial/light/moderate/heavy)
        6. Recommendation: port, skip, or bookmark
        7. Confidence in recommendation (0-100)
        8. If porting: brief adaptation strategy"

        5. Store analysis results in upstream_prs table
        6. Update status to 'analyzed'
        """
        pass

    async def port(self, pr_id: int) -> dict:
        """
        Port an approved upstream PR into our codebase.

        1. Load PR diff + analysis + our current file versions
        2. Create a new git branch: upstream-port/pr-{number}
        3. Send to Claude (Opus for best code quality):

        Prompt:
        "Port this upstream feature into our diverged fork.

        Upstream diff: {diff}
        Our current files: {our_files}
        Analysis: {analysis}
        Our BLUEPRINT.md: {blueprint}

        Rules:
        - Adapt the code to fit our codebase patterns, not theirs
        - If a file has diverged heavily, rewrite the feature for our version
        - Preserve all our custom functionality
        - Add the feature, don't replace our implementations
        - Update BLUEPRINT.md with what was ported"

        4. Agent writes adapted code
        5. Run lint + type check
        6. If passing: commit and merge to main branch
        7. If failing: report errors, set status='failed'
        8. Update upstream_prs status and port_commit_hash
        """
        pass

    async def bulk_analyze(self, repo_id: int) -> int:
        """Analyze all 'new' PRs for a repo. Returns count analyzed."""
        pass

    async def get_summary(self, repo_id: int) -> dict:
        """Get counts by status for dashboard display."""
        pass
```

#### `server/services/upstream_scheduler.py`

Scheduled polling using APScheduler (already in AutoForge for agent scheduling):

```python
class UpstreamScheduler:
    """
    Runs upstream polling on a configurable schedule.
    Piggybacks on existing APScheduler infrastructure.
    """

    def start(self):
        """Register polling job with scheduler."""
        # Every N hours (from watched_repos.poll_interval_hours)
        # Job: poll() → bulk_analyze() for each enabled repo
        pass

    def trigger_now(self, repo_id: int):
        """Manual trigger from UI."""
        pass
```

#### `server/routers/upstream.py`

REST API for the UI:

```python
# Repo management
GET    /api/upstream/repos                     # List watched repos
POST   /api/upstream/repos                     # Add repo to watch
DELETE /api/upstream/repos/{id}                 # Remove watched repo
PATCH  /api/upstream/repos/{id}                # Update settings (interval, enabled)

# PR management
GET    /api/upstream/prs                        # List all tracked PRs (with filters)
GET    /api/upstream/prs/{id}                   # Get PR with full analysis
GET    /api/upstream/prs/summary                # Dashboard summary (counts by status)
POST   /api/upstream/prs/{id}/analyze           # Trigger analysis for one PR
POST   /api/upstream/prs/{id}/approve           # Approve for porting
POST   /api/upstream/prs/{id}/skip              # Mark as skipped
POST   /api/upstream/prs/{id}/bookmark          # Bookmark for later
POST   /api/upstream/prs/{id}/port              # Execute the port

# Watcher control
POST   /api/upstream/poll                       # Manual poll trigger
GET    /api/upstream/runs                       # Polling run history
GET    /api/upstream/status                     # Watcher service status
```

### Frontend Components

#### New page: `/#/upstream` (or tab in dashboard)

```
ui/src/components/upstream/
├── UpstreamDashboard.tsx        # Main page with summary stats + PR list
├── UpstreamPRCard.tsx           # Individual PR card with status, recommendation, actions
├── UpstreamPRDetail.tsx         # Full analysis view (modal or expandable)
├── UpstreamRepoSettings.tsx     # Add/configure watched repos
├── UpstreamDiffViewer.tsx       # Side-by-side diff view (upstream vs yours)
├── PortProgressModal.tsx        # Shows port progress (agent writing code, lint, commit)
└── UpstreamSummaryWidget.tsx    # Small widget for main dashboard ("3 new upstream features")
```

#### Dashboard Widget

A small card on the main AutoForge dashboard:

```
┌──────────────────────────────┐
│ Upstream Features        [→] │
│ 3 new · 2 recommended        │
│ Last checked: 2 hours ago    │
└──────────────────────────────┘
```

Click to go to full upstream page.

---

## Analysis Agent Prompt (Stage 2)

This is the core intelligence. The analysis prompt needs to be thorough:

```markdown
# Upstream PR Analysis

You are analyzing an upstream pull request to determine if it should be ported
to a heavily diverged fork of the same project.

## Upstream PR
- Title: {pr_title}
- Author: {pr_author}
- Description: {pr_description}
- Files changed: {file_count}

## Upstream Diff
{full_diff}

## Our Current Versions of Affected Files
{our_file_contents}

## Our Modification History (BLUEPRINT.md)
{blueprint_contents}

## Your Task

Analyze this PR and produce a structured assessment:

### 1. Feature Summary
What does this PR do? (2-3 sentences, plain language)

### 2. File-by-File Divergence
For each file in the diff, compare against our version:
- **File**: path/to/file
- **Upstream changes**: what they changed
- **Our version**: how our file differs from upstream
- **Divergence level**: CLEAN (we haven't modified this file) / LIGHT (minor changes) / MODERATE (significant restructuring) / HEAVY (completely rewritten)
- **Conflict risk**: what specifically would conflict

### 3. Already Have Check
Does our fork already have this feature (or something equivalent)?
Check BLUEPRINT.md and our file contents. If yes, note what we have and how it differs.

### 4. Relevance Score (0-100)
How relevant is this feature to our fork's direction?
Consider: our custom features, our architecture decisions, our roadmap.

### 5. Effort Estimate
- TRIVIAL: Clean drop-in, no conflicts, < 5 min
- LIGHT: Minor adaptations needed, < 30 min agent work
- MODERATE: Significant adaptation, 1-2 hours agent work
- HEAVY: Major rewrite needed, 2+ hours, may need human guidance

### 6. Recommendation
- **PORT**: Feature is valuable, effort is justified, go for it
- **SKIP**: Not relevant, we already have it, or too much effort for the value
- **BOOKMARK**: Interesting but not urgent, revisit later
- **ALREADY_HAVE**: We built this ourselves (note our equivalent)

### 7. Confidence (0-100)
How confident are you in this recommendation?

### 8. Adaptation Strategy (if recommending PORT)
Brief plan for how to adapt this to our codebase:
- Which files to modify
- Key changes needed vs upstream implementation
- What to watch out for (our custom code to preserve)
```

## Port Agent Prompt (Stage 4)

```markdown
# Port Upstream Feature

You are porting an upstream feature into a diverged fork. The feature has been
analyzed and approved for porting.

## Feature Being Ported
{analysis_summary}

## Upstream Diff
{full_diff}

## Our Current Files (that will be affected)
{our_file_contents}

## Adaptation Strategy
{adaptation_strategy_from_analysis}

## Our Modification History
{blueprint_contents}

## Rules

1. **Adapt to OUR patterns** — don't copy upstream code verbatim if our codebase
   has different patterns. Rewrite to fit our style.
2. **Preserve ALL our custom code** — if a file has our custom features, the port
   must keep them intact. Add the new feature alongside, don't replace.
3. **If a file is heavily diverged** — reimplement the feature's INTENT in our
   code rather than trying to merge the upstream diff.
4. **Clean files can take closer-to-verbatim ports** — if we haven't touched a
   file, the upstream changes can be applied more directly.
5. **Update BLUEPRINT.md** — append an entry documenting what was ported, from
   which PR, and any adaptations made.
6. **Run lint and type check** — ensure the code compiles cleanly after porting.

## Output

Write the adapted code to the appropriate files. Make minimal, surgical changes.
Do not refactor surrounding code. Do not "improve" things that aren't part of the port.
```

---

## Configuration

### Setting Up the Watcher

First-time setup in AutoForge UI (Settings or dedicated Upstream page):

1. **Add upstream repo URL** — `https://github.com/{owner}/{repo}`
2. **Add GitHub token** (for private repos or higher API rate limits) — stored encrypted, not in DB
3. **Set poll interval** — default 6 hours
4. **Enable/disable** — toggle watching on/off

### Auto-Port Rules (Optional, Phase 2)

For power users who trust the system:

```
Auto-port rules:
- If confidence >= 95% AND effort = TRIVIAL AND recommendation = PORT → auto-port
- If recommendation = ALREADY_HAVE → auto-skip
- Everything else → require manual approval
```

This lets bug fixes and trivial improvements flow in automatically while requiring your eyes on anything substantial.

---

## MVP Build Order

### Phase 1: Core Pipeline (Build First)

1. **Database tables** — `watched_repos`, `upstream_prs`, `watcher_runs`
2. **GitHub API polling** — fetch merged PRs, store metadata + diffs
3. **Analysis agent** — Claude analyzes each PR against your codebase
4. **Basic UI** — list of PRs with analysis, approve/skip buttons
5. **Manual port** — approved PRs handed off as a task description (not auto-coded yet)

**This alone gives you:** Automated monitoring with smart analysis. You see new upstream features as they land, with a recommendation and effort estimate. You still manually port, but you know WHAT to port.

### Phase 2: Auto-Port

6. **Port agent** — Claude writes adapted code, runs lint, commits
7. **Port progress UI** — shows the agent working, lint results, commit confirmation
8. **BLUEPRINT.md auto-update** — port agent documents what it ported

### Phase 3: Intelligence

9. **Auto-port rules** — trivial + high-confidence features port automatically
10. **Dashboard widget** — summary on main AutoForge dashboard
11. **Scheduled polling** — APScheduler integration for background monitoring
12. **Notification system** — notify when new features are found (in-app or webhook)

### Phase 4: Advanced

13. **Diff viewer** — side-by-side view of upstream vs your code
14. **Batch port** — approve and port multiple PRs at once
15. **Dependency detection** — flag when one upstream PR depends on another you skipped
16. **Reverse watch** — detect when upstream builds something similar to what you already have (track convergence)

---

## GitHub API Details

### Authentication

```python
# Use GitHub Personal Access Token for API access
# Stored encrypted at ~/.autoforge/workspace/.tokens (same as IdeaForge)
# Token needs 'repo' scope for private repos, 'public_repo' for public

headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github.v3+json"
}
```

### Key Endpoints

```python
# List merged PRs (paginated, sorted by updated date)
GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30

# Get PR details
GET /repos/{owner}/{repo}/pulls/{pr_number}

# Get PR diff
GET /repos/{owner}/{repo}/pulls/{pr_number}
Headers: Accept: application/vnd.github.v3.diff

# Get PR files (list of changed files with patch)
GET /repos/{owner}/{repo}/pulls/{pr_number}/files

# Check rate limits
GET /rate_limit
```

### Rate Limiting

GitHub API allows 5,000 requests/hour with authentication. At 6-hour polling with ~10 new PRs per check, you'll use maybe 50 requests per poll. Well within limits.

If using the `gh` CLI (already available in AutoForge), many of these calls simplify:

```bash
# List merged PRs
gh pr list --repo {owner}/{repo} --state merged --limit 30 --json number,title,author,mergedAt,files

# Get PR diff
gh pr diff {number} --repo {owner}/{repo}

# Get PR details
gh pr view {number} --repo {owner}/{repo} --json title,body,author,files,additions,deletions
```

Using `gh` CLI is simpler and handles auth automatically if the user has `gh auth login` configured.

---

## Integration with IdeaForge

Once the IdeaForge workspace chat is built, the upstream watcher becomes even more powerful:

- **Discuss upstream features in context** — open an IdeaForge chat about a specific upstream PR, with the diff and analysis already loaded
- **Iterate on the port** — if the auto-port needs tweaks, continue the conversation in the same context window
- **Track decisions** — your reasoning for skip/port decisions lives in persistent chat history

The watcher surfaces the features; IdeaForge gives you the space to think about them.

---

## Security Notes

- GitHub tokens stored encrypted, never in SQLite
- PR diffs cached locally to minimize API calls
- Port operations run in the same sandbox as AutoForge agents
- All ports create git commits (easily reversible with `git revert`)
- No auto-push — ported code stays local until you decide to push
