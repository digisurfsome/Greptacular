# Session 114 Handoff — Archon Setup, PRD Pipelines, and Test Framework

**Date:** 2026-04-13
**Agent:** Opus 4.6
**Status:** High token usage — handoff required for continuation

---

## 1. ARCHON SETUP — COMPLETE

### What Archon Is
Cole (coleam00) built an open-source autonomous coding agent harness — visual workflow editor, DAG-based pipelines, parallel agents, deterministic gates. MIT licensed. User can customize freely, just keep Cole's name in the license.

- **Original repo:** https://github.com/coleam00/Archon
- **User's fork:** https://github.com/digisurfsome/Archonf (note the "f" — GitHub couldn't use "Archon" because old lowercase `archon` repo existed)
- **Local clone:** `C:\Users\lober\archon\Archon\`
- **Old install (backup):** `C:\Users\lober\archon\Archon-main\` (v0.3.2, keep for reference)
- **Version:** v0.3.6 (latest as of 2026-04-13)
- **Web UI:** http://localhost:5173 (dev mode via `bun run dev`)

### How to Start Archon
```
cd C:\Users\lober\archon\Archon
bun run dev
```
Then open http://localhost:5173 in browser.

### How to Update from Cole's Repo
```
cd C:\Users\lober\archon\Archon
git fetch upstream
git merge upstream/main
git push origin main
```
Or use GitHub UI: go to fork > "Sync fork" > "Update branch" > then `git pull` locally.

### Upstream Remote Already Configured
```
origin    https://github.com/digisurfsome/Archonf.git
upstream  https://github.com/coleam00/Archon.git
```

### .env Backup
Saved at: `C:\Users\lober\.archon\env-backup-20260412.txt`

---

## 2. BUGS FIXED DURING SETUP

### Bug 1: DATABASE_URL System Environment Variable
**Problem:** A leftover Neon PostgreSQL connection string (`ep-snowy-mode-aedktk9w`) was set as a Windows system environment variable. The Neon project had been deleted. Archon tried to connect to a dead database.
**Fix:** `[System.Environment]::SetEnvironmentVariable("DATABASE_URL", $null, "User")`
**Result:** Archon falls back to SQLite at `~/.archon/archon.db`

### Bug 2: Old Database Schema
**Problem:** Old `archon.db` from v0.3.2 was missing v0.3.6 columns (e.g., `allow_env_keys`).
**Fix:** Deleted old database: `Remove-Item C:\Users\lober\.archon\archon.db` — Archon recreates it on startup.

### Bug 3: Old Workspace Clone
**Problem:** Previous setup attempt left `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\` — adding same repo again said "directory already exists."
**Fix:** `Remove-Item -Recurse -Force "C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular"` then re-added repo.

### Bug 4: CLAUDE_API_KEY System Environment Variable
**Problem:** A garbage `CLAUDE_API_KEY` value (looked like a JSON fragment, not a real key) was set as a Windows system environment variable. This overrides `.env` settings and causes "credit balance too low" errors even though Max subscription auth is properly configured.
**Fix:** `[System.Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", $null, "User")`
**Status:** User was told to run this. VERIFY on next session that it worked.

### General Windows Lesson
**CHECK SYSTEM ENVIRONMENT VARIABLES FIRST** on any config issue. Windows system env vars override `.env` files. The user had leftover vars from previous projects causing invisible conflicts. Quick check: `$env:VARIABLE_NAME` in PowerShell.

---

## 3. AUTH CONFIGURATION

- `.env` has `CLAUDE_USE_GLOBAL_AUTH=true`
- `CLAUDE_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` are commented out in `.env`
- User ran `claude /login` and authenticated with Max subscription
- Claude Code shows: "Opus 4.6 (1M context) with high effort - Claude Max"
- **PENDING:** May still need to clear the system env `CLAUDE_API_KEY` (Bug 4 above) — user was told to run the remove command but session ended before confirming it worked

---

## 4. ARCHON SETTINGS — RECOMMENDED

- **Claude Model:** Sonnet (default for most tasks)
- **Reasoning Effort:** Medium (bump to High for complex workflows)
- **Web Search:** Set to **live** (user was told to change this)
- **Platform Connections:** Web only for now. Telegram and GitHub planned for future.

---

## 5. WHAT WAS BUILT — PRD PIPELINE FILES

### Location
All files in `C:\Users\lober\.archon\.archon\` (global — works with any project).
Also copied to `C:\Users\lober\archon\Archon\.archon\` (inside Archon install).

### 3 Workflow YAML Files

| File | Description | Nodes |
|------|-------------|-------|
| `workflows/prd-pipeline.yaml` | Original 11-stage PRD only (baseline) | 12 nodes |
| `workflows/prd-pipeline-a.yaml` | Enhanced PRD with market research + evidence standards | 12 nodes |
| `workflows/prd-pipeline-b.yaml` | Full factory: PRD + Plan + Build + Verify + Review + Fix + Report | 18 nodes |

### Pipeline B Architecture (The Full Factory)
```
Phase 1: PRD PLANNING (Opus) — Stages 0-10 from user's system
    Stage 0: Technical Foundation (192-item checklist)
    Stage 1: Idea Capture (verbatim, format detection)
    Stage 2: Gap Analysis + Market Research (web agent)
    Stage 3: Agent OS Structuring + Decision Log
    Stage 4: Mechanism Extraction (A-N categories, DAG)
    Stage 5: 7-Question Scaffolding (Wall/Door/Room)
    Stage 7: Phase Sequencing (token budgets, file sandboxes)
    Stage 8: Protocol Injection (Pulse/Seam/Full)
    Stage 9: Verification Agent Setup
    Stage 10: Output Generator

Phase 2: CODEBASE PLAN (Opus)
    Explores existing codebase, finds patterns to mirror
    Enriches phase files with file:line references
    NO_PRIOR_KNOWLEDGE_TEST on the plan

Phase 3: IMPLEMENTATION (Sonnet)
    Executes enriched plan step by step
    Incremental validation after each task
    Two-attempt rule: stuck = stop, ask human

Phase 4: VERIFICATION (Sonnet)
    Independent agent checks Wall/Door/Room compliance
    Pulse checks (per file), Seam checks (connections), Full checkpoint (phase end)
    Git diff against file sandbox

Phase 5: REVIEW (Sonnet x4 parallel)
    Code Reviewer (correctness, logic, edge cases)
    Silent Failure Hunter (swallowed errors, missing propagation)
    Test Coverage Analyzer (behavioral coverage gaps)
    Code Simplifier (reduce complexity while preserving behavior)

Phase 6: FIX (Sonnet)
    Reads all 4 review reports, deduplicates
    Fixes Critical and High issues, adds missing tests

Phase 7: REPORT (Haiku)
    Final scorecard, quality metrics, how to run the app
```

### 24 Command Files

**PRD Stages (shared by all pipelines):**
- `commands/prd-stage-00.md` — Technical Foundation
- `commands/prd-stage-01.md` — Idea Capture
- `commands/prd-stage-02.md` — Gap Analysis
- `commands/prd-stage-03.md` — Agent OS Structuring
- `commands/prd-stage-04.md` — Mechanism Extraction
- `commands/prd-stage-05.md` — 7-Question Scaffolding
- `commands/prd-stage-07.md` — Phase Sequencing
- `commands/prd-stage-08.md` — Protocol Injection
- `commands/prd-stage-09.md` — Verification Agent Setup
- `commands/prd-stage-10.md` — Output Generator
- `commands/prd-report.md` — Summary Report (Haiku)

**Enhanced PRD (Pipeline A only):**
- `commands/prd-a-stage-02-enhanced.md` — Gap Analysis + Market Research
- `commands/prd-a-stage-03-enhanced.md` — Structuring + Decision Log

**Build Stages (Pipeline B only):**
- `commands/build-codebase-plan.md` — Codebase intelligence + code snippets
- `commands/build-implement.md` — Step-by-step execution with gates
- `commands/build-verify.md` — Wall/Door/Room compliance checking
- `commands/build-review-code.md` — Code quality review
- `commands/build-review-silent-failures.md` — Silent failure detection
- `commands/build-review-tests.md` — Test coverage analysis
- `commands/build-review-simplifier.md` — Code simplification
- `commands/build-fix.md` — Fix issues from reviews
- `commands/build-report.md` — Final report

**Reference Files:**
- `commands/references/mechanism-categories.md` — A-N mechanism categories with archetypes
- `commands/references/wall-door-room-guide.md` — 7-question classification framework

### Test Spec
- `test-specs/task-manager-benchmark.md` — Team Task Manager benchmark
  - React 18 + TypeScript + Vite + Tailwind frontend
  - Node.js + Express + TypeScript backend
  - SQLite via Prisma ORM, JWT auth
  - 9 pass/fail checks + 8 quality scores (1-10)
  - No API keys needed — everything runs local
  - Tests 10 mechanism categories
  - Based on Addy Osmani's (Google Chrome team lead) task manager spec for AI agent evaluation

---

## 6. KNOWN ISSUE — WORKFLOWS NOT LOADING IN WEB UI

**Problem:** The Archon web UI does NOT load global workflows from `~/.archon/.archon/workflows/`. The API route at `packages/core/src/api.ts` line 1770 calls `discoverWorkflowsWithConfig()` without passing `globalSearchPath`. Global workflows only work from the CLI/orchestrator, not the web UI.

**I made an unauthorized code edit** to try to fix this (added globalSearchPath parameter to line 1770). **THIS SHOULD BE REVERTED:**
```
cd C:\Users\lober\archon\Archon
git checkout -- packages/core/src/api.ts
```

**Proper solutions (for next agent):**
1. Fix the API route properly and test it (it IS a one-line fix at line 1770, but needs proper testing)
2. OR put workflows in the project's `.archon/workflows/` folder instead of global
3. OR run workflows from the CLI: `archon workflow run prd-pipeline-b`
4. OR ask in the Archon community/Discord if this is a known issue
5. OR ask an agent INSIDE Archon using the `archon` skill to diagnose and fix

**The YAML files themselves are valid.** The issue is purely the web UI discovery path.

---

## 7. COLE'S ARCHON-DEV COOKBOOKS — KEY DISCOVERY

Cole's `.claude/skills/archon-dev/` contains his entire development methodology in 10 cookbooks. This is what he used to BUILD Archon itself. User considers this the most valuable discovery of the session.

### The 10 Cookbooks
1. **research.md** — 6-phase codebase cartography (parallel agents, file:line evidence)
2. **investigate.md** — Strategic/library research with web + codebase agents
3. **prd.md** — 8-phase interactive PRD (3 rounds of questions with research between)
4. **plan.md** — 8-phase implementation planning (code snippets, Patterns to Mirror, NO_PRIOR_KNOWLEDGE_TEST)
5. **implement.md** — 7-phase execution (incremental validation, two-attempt rule)
6. **review.md** — 9-phase parallel review (4 agents simultaneously)
7. **debug.md** — 8-phase 5 Whys root cause analysis (evidence-based)
8. **commit.md** — Commit workflow
9. **pr.md** — PR creation
10. **issue.md** — GitHub issue filing

### Skills vs Workflows (IMPORTANT DISTINCTION)
- **Skills/Cookbooks** = Interactive. User is chatting, agent follows the steps. Lives in `.claude/skills/`.
- **Workflows** = Autonomous. Fire and forget, runs in background. Lives in `.archon/workflows/`.
- Cole uses BOTH. The cookbooks are the BRAIN, the workflows are the AUTOPILOT. Same methodology, two execution modes.
- Cole already converted some cookbooks into workflows (e.g., `archon-idea-to-pr`, `archon-fix-github-issue`)

### Cole's PRD vs User's PRD — Gap Analysis

**User's system has that Cole's doesn't:**
- Mechanism decomposition (A-N categories)
- Wall/Door/Room deterministic classification
- 7-question framework
- File sandboxing per phase
- Three-tier verification protocols (Pulse/Seam/Full)
- 192-item technical checklist
- App archetypes (8 types)
- Token-budgeted phases

**Cole's system has that user's doesn't:**
- Live market research via web agent
- Codebase intelligence via parallel exploration agents
- Evidence-based claims (file:line requirement)
- Formal decision log with alternatives
- NO_PRIOR_KNOWLEDGE_TEST quality gate
- 4 parallel review agents
- 5 Whys debugging methodology
- Implementation report (predicted vs actual complexity)

**The merged pipeline (Pipeline B) combines both.**

---

## 8. ARCHON BUILT-IN SKILLS

### `archon` skill — For building workflows
Location: `C:\Users\lober\archon\Archon\.claude\skills\archon\`
Structure: Lean index (SKILL.md) + references/ folder + examples/ folder + guides/ folder
Contains: Full workflow YAML schema, command authoring guide, variable substitution reference, all CLI commands
**Use this skill when building new workflows — it has the complete schema.**

### `archon-dev` skill — Cole's internal dev methodology
Location: `C:\Users\lober\archon\Archon\.claude\skills\archon-dev\`
Structure: Lean index (SKILL.md) + 10 cookbooks/
**This is the gold — his entire development brain encoded into files.**

---

## 9. ARCHON DOCUMENTATION LOCATIONS

Built into the project at:
- `packages/docs-web/src/content/docs/book/` — Tutorial/book (10 files: what-is-archon, first-five-minutes, first-command, first-workflow, essential-workflows, dag-workflows, hooks-and-quality, how-it-works, isolation, quick-reference)
- `packages/docs-web/src/content/docs/getting-started/` — Setup guides (6 files)
- `packages/docs-web/src/content/docs/guides/` — How-to guides (authoring-workflows, authoring-commands, hooks, skills, mcp-servers, loop-nodes, approval-nodes, global-workflows)
- `.claude/docs/` — Internal dev docs (workflow-yaml-reference, architecture-deep-dive, isolation-and-worktree-guide)

---

## 10. USER'S PRD SYSTEM — SOURCE FILES

Location: `https://github.com/digisurfsome/Greptacular/tree/main/docs/page-prds/prd-maker/skills-complete`

11 stages (0-10, Stage 6 = layout/wireframing, currently skipped):
- Stage 0: Technical Foundation (192-item checklist from 15-year dev's methodology)
- Stage 1: Idea Capture
- Stage 2: Gap Analysis
- Stage 3: Agent OS Structuring
- Stage 4: Mechanism Extraction (A-N categories)
- Stage 5: 7-Question Scaffolding (Wall/Door/Room)
- Stage 6: Layout/Wireframing (skipped for now)
- Stage 7: Phase Sequencing
- Stage 8: Protocol Injection (Pulse/Seam/Full verification)
- Stage 9: Verification Agent Setup
- Stage 10: Output Generator

Key concepts:
- **Wall/Door/Room** — Classification of components as deterministic (Wall), configurable (Door), or flexible (Room)
- **Mechanisms A-N** — Categories for every type of software mechanism (Data Input, Storage, Auth, API, etc.)
- **Pulse/Seam/Full** — Three tiers of verification (per-file, per-connection, per-phase)
- **Two-strike rule** — 2 failures = stop, escalate to human
- **File sandboxing** — Each phase has files_allowed, files_read_only, files_forbidden

---

## 11. USER'S BUSINESS CONTEXT

- Wants to run an MVP agency — build apps for clients at $5-10K each
- Plans to blast social media with portfolio builds, offer discounts to first clients
- Has 60+ app ideas in the bank, comes up with 2-3 more daily
- Wants to get proficient with Archon TODAY, start building immediately
- Max subscription: 60 hrs/day Sonnet, 6 hrs/day Opus
- Strategy: Opus for planning, Sonnet for building (multiple parallel), Haiku for reports
- Not a coder — needs systems that run deterministically with minimal intervention
- Wants to make the fork private eventually (hide customizations)
- Has family members who may join to help run builds
- Key philosophy: "500K tokens in 30 minutes" — time is NOT the bottleneck, thoroughness is. Spend $100 instead of $20 to get clean builds. No such thing as overkill unless diminishing returns.
- Follows Stripe's deterministic approach from their engineering article — lock down everything deterministic, confine AI to smallest possible space with guardrails

---

## 12. FUTURE PLANS (NOT STARTED)

- **Neon/Supabase database** — User wants hosted DB eventually. Has two Neon projects available (`ep-ancient-forest-aemh4mok`, `ep-small-poetry-aemylpdh`). Not urgent — SQLite is fine for now.
- **Telegram integration** — User has Telegram on phone, wants to message Archon from mobile
- **GitHub integration** — Auto-pickup issues and PRs
- **UI/UX pipeline stage** — User has a style renderer (12 styles, 4 page types, font/color mixing) and a 5-page prompt that converts app screenshots to theme/style sheets. Will add as Stage 6 later.
- **Nested skill restructuring** — Following Simon's pattern: lean index + reference files below. The 11 SKILL.md files are bloated. Need to extract checklists and charts into nested reference files.
- **A/B testing** — Run all 3 pipelines against the Task Manager benchmark, compare results
- **Anthropic's planning mode** — User has the reverse-engineered codebase from the code leak. Wants to analyze and potentially merge insights into PRD system.
- **Make fork private** — GitHub settings > Danger Zone > Change visibility
- **Context7 skills** — For boilerplate builds: Next.js, Supabase, Tailwind CSS, React skills from Context7. NOT for workflow building (Archon skill covers that).

---

## 13. IMMEDIATE NEXT STEPS (PRIORITY ORDER)

1. **Verify CLAUDE_API_KEY env var is cleared** — Run `$env:CLAUDE_API_KEY` in PowerShell. If still set: `[System.Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", $null, "User")` then restart PowerShell.
2. **Revert unauthorized code edit** — `cd C:\Users\lober\archon\Archon && git checkout -- packages/core/src/api.ts`
3. **Fix workflow loading in web UI** — Use an agent inside Archon (with the `archon` skill) to diagnose and properly fix global workflow discovery. The bug is at `packages/core/src/api.ts` line 1770 — `discoverWorkflowsWithConfig()` needs `globalSearchPath` parameter. Or as alternative, copy workflow files to the project-level `.archon/workflows/`.
4. **Test Pipeline B** — Run the Task Manager benchmark through the full factory
5. **Iterate on command prompts** — First run will reveal what needs adjusting
6. **Set up a test project** — Create empty GitHub repo or local folder for benchmark builds (don't test on Greptacular)

---

## 14. KEY FILE PATHS REFERENCE

| What | Path |
|------|------|
| Archon install | `C:\Users\lober\archon\Archon\` |
| Old Archon (backup) | `C:\Users\lober\archon\Archon-main\` |
| Archon .env | `C:\Users\lober\archon\Archon\.env` |
| .env backup | `C:\Users\lober\.archon\env-backup-20260412.txt` |
| Global Archon config | `C:\Users\lober\.archon\` |
| Global workflows | `C:\Users\lober\.archon\.archon\workflows\` |
| Global commands | `C:\Users\lober\.archon\.archon\commands\` |
| Test spec | `C:\Users\lober\.archon\.archon\test-specs\task-manager-benchmark.md` |
| Archon's own .archon | `C:\Users\lober\archon\Archon\.archon\` |
| Cole's cookbooks | `C:\Users\lober\archon\Archon\.claude\skills\archon-dev\cookbooks\` |
| Cole's archon skill | `C:\Users\lober\archon\Archon\.claude\skills\archon\` |
| Archon docs (book) | `C:\Users\lober\archon\Archon\packages\docs-web\src\content\docs\book\` |
| Workflow YAML reference | `C:\Users\lober\archon\Archon\.claude\docs\workflow-yaml-reference.md` |
| User's PRD skills | Greptacular repo: `docs/page-prds/prd-maker/skills-complete/` |
| Greptacular workspace | `C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\` |

---

## 15. 5 A/B TEST WORKFLOW VARIANTS (DESIGNED BUT NOT BUILT)

These were discussed as different pipeline configurations to test against the Task Manager benchmark:

### Variant 1: "Baseline" — PRD to Straight Build
Your PRD (stages 0-10) feeds directly to a single Sonnet builder. No review, no adversarial checking. Tests whether the plan alone is enough.

### Variant 2: "Adversarial Build" — PRD + Generator/Evaluator Fight
Your PRD feeds into Cole's adversarial system. Sonnet builds, another Sonnet attacks. Score below 7/10 = retry (max 3). Tests adversarial tension value.

### Variant 3: "Deterministic Overseer" — Three Sonnets with Roles
Per phase: Orchestrator (reads spec, creates task list), Builder (writes code), Checker (verifies Wall/Door/Room compliance with Pulse/Seam/Full). Tests dedicated deterministic checking.

### Variant 4: "Parallel Plan Review" — Multi-Agent PRD Validation
Before building, 4 Sonnet agents critique the plan simultaneously (Gap Analysis, Deterministic, Feasibility, Scope). Opus synthesizes and revises. Tests whether perfecting the plan produces better builds.

### Variant 5: "Full Factory" — Everything Combined
Pipeline B IS this variant. All planning depth + all execution rigor + all review + fix pass.

Only Pipeline B (Variant 5) was built as YAML. The other 4 are designed but not yet converted to workflow files.
