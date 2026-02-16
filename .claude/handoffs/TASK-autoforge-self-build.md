# TASK: Build AutoForge Enhancements (Project B)

## What This Is

AutoForge is going to build features onto itself. You're running AutoForge pointed at its own codebase, feeding it PRD specs one at a time, and it adds capabilities to itself. There are also 3 direct implementation tasks that don't go through the AutoForge pipeline — those get handed to a Claude Code agent directly.

This document tells you exactly what to run, in what order, and what to watch out for.

---

## Before You Start: Key Files to Understand

Read these if you need context on how AutoForge works:

| File | What It Is | When To Read |
|------|-----------|--------------|
| `.claude/autoforge-prd-context.md` | Master reference for PRD format, coding standards, architecture | Read Section 3.3 "Handling AutoForge-Internal Handoffs" — explains how internal feature specs differ from standalone apps |
| `CLAUDE.md` | Project overview, commands, architecture | Skim the "Commands" and "Architecture" sections to understand how to run AutoForge |
| `.claude/autoforge-features-build.md` | Summary of all 11 items being built | Quick reference for what each spec/handoff does |

---

## The Two Types of Work

### Type 1: AutoForge Spec Runs (8 specs)

These are XML spec files that get fed to AutoForge as `app_spec.txt`. AutoForge's Initializer agent reads the spec, creates features in the SQLite database, then Coding agents implement them one by one.

**How to run each one:**

```bash
# 1. Copy the spec to the AutoForge project as app_spec.txt
cp .claude/generated-prds/[SPEC-FILE].xml .autoforge/prompts/app_spec.txt

# 2. Run AutoForge pointed at its own directory
python autonomous_agent_demo.py --project-dir .

# Or if using the npm CLI:
autoforge
```

AutoForge will detect that `.autoforge/features.db` is empty (first run with this spec) and run the Initializer agent to create features. Then it auto-continues with Coding agents to implement them.

**IMPORTANT:** Each spec is a SEPARATE run. After one spec completes, you copy the next spec in, clear the features.db (or use a fresh `.autoforge/` state), and run again. Do NOT try to feed all 8 specs at once.

### Type 2: Direct Implementation (3 handoffs)

These are written as "edit file X at line Y" instructions. They don't go through AutoForge's Initializer → Coding Agent pipeline. Give the handoff file directly to a Claude Code agent (or a developer) and say "implement this."

---

## BUILD ORDER: 4 Phases, 11 Items

### PHASE 1 — Foundation (Do These First)

These make everything that comes after work better. QA Pipeline gives AutoForge the ability to test its own builds. Pre-Build Intelligence scores specs before building. Mentor Standards improves the code quality of everything generated after.

---

#### RUN 1: QA Pipeline
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/qa-pipeline-spec.xml`
**Source handoffs:** `.claude/handoffs/qa-pipeline-handoff.md` + `.claude/handoffs/computer-use-qa-handoff.md`
**Why first:** Every subsequent build benefits from having QA infrastructure. Without this, AutoForge has no way to systematically test what it builds.

**What gets built:**
- 4-phase QA pipeline: Build → Review → Regression → Final QA
- New agent types: `reviewer` and `qa`
- New prompt templates: `reviewer_prompt.template.md`, `qa_prompt.template.md`
- New MCP tool: `feature_mark_reviewed`
- New database column: `reviewed` flag on Feature model
- Computer Use QA (Claude vision-based testing, optional phase 5)
- UI: QA Pipeline section in SettingsModal, review controls

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes, the `--agent-type reviewer` and `--agent-type qa` flags are recognized by `autonomous_agent_demo.py`.

---

#### RUN 2: Pre-Build Intelligence
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/pre-build-intelligence-spec.xml`
**Source handoff:** `.claude/handoffs/pre-build-intelligence-handoff.md`
**Why second:** Once this is built, it can score the remaining specs before AutoForge builds them, catching issues early.

**What gets built:**
- Spec Analyzer Agent (scores PRD quality 1-5 before building)
- Architecture Planner Agent (generates implementation plan)
- Dependency Auto-Detection (suggests feature dependencies from spec text)
- New agent types: `spec-analyzer`, `architect`
- New prompt templates: `spec_analyzer_prompt.template.md`, `architect_prompt.template.md`
- CLI flags: `--skip-spec-analysis`, `--min-spec-score`, `--force-build`, `--skip-architect`
- Modifies: `autonomous_agent_demo.py`, `client.py`, `parallel_orchestrator.py`, `prompts.py`, `agent.py`

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes, `python autonomous_agent_demo.py --help` shows the new flags.

---

#### RUN 3: Mentor Standards Integration
**Type:** Direct Implementation (NOT an AutoForge spec run)
**Handoff:** `.claude/handoffs/mentor-standards-integration-handoff.md`
**Why now:** Improves the coding standards in prompt templates BEFORE building more features. Everything built after this follows better patterns.

**How to run:** Give the handoff file to a Claude Code agent:
```
Read .claude/handoffs/mentor-standards-integration-handoff.md and implement everything it describes.
```

**What gets built:**
- STEP 4.5 coding standards (15 rules) added to `.claude/templates/coding_prompt.template.md`
- Updated STEP 5.5 verification checklist
- Universal design system added to style guide generation in `server/services/style_manager.py`
- Identity-first questions added to `.claude/commands/create-spec.md` and `server/services/spec_chat_session.py`
- Dual description format (technical + user action) added to `.claude/templates/initializer_prompt.template.md`

**Files modified (5 total):**
1. `.claude/templates/coding_prompt.template.md` — Add STEP 4.5 + update STEP 5.5
2. `.claude/templates/initializer_prompt.template.md` — Add dual description format
3. `server/services/style_manager.py` — Add universal design system to `get_style_guide_markdown()`
4. `.claude/commands/create-spec.md` — Add identity-first + MVP scoping
5. `server/services/spec_chat_session.py` — Add identity-first tracking

**What to verify after:** `ruff check .` passes, the template files contain the new sections (grep for "STEP 4.5" and "IDENTITY FIRST").

---

### PHASE 2 — Intelligence Layer

These add learning and quality infrastructure. Build Intelligence tracks metrics across builds. Post-Build Reports auto-generates docs, performance profiles, and security audits.

---

#### RUN 4: Build Intelligence
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/build-intelligence-spec.xml`
**Source handoff:** `.claude/handoffs/build-intelligence-handoff.md`

**What gets built:**
- Build History tracking (`build_metrics`, `feature_patterns` tables in SQLite)
- PRD Quality Scoring engine (`server/services/spec_scorer.py`)
- Continuous Improvement Pipeline (learns from past builds, suggests prompt improvements)
- Score thresholds: <2.0 blocks build, 2.0-3.0 warns, 3.0+ proceeds
- UI: Build history dashboard, spec score display

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes.

---

#### RUN 5: Post-Build Reports
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/post-build-reports-spec.xml`
**Source handoff:** `.claude/handoffs/post-build-reports-handoff.md`

**What gets built:**
- Docs Agent (auto-generates documentation after build)
- Performance Agent (profiling, optimization recommendations)
- Security Agent (audit — can mark features as failing and block shipping)
- New agent types: `docs`, `performance`, `security`
- New prompt templates for each agent type
- Orchestrator wiring: agents spawn after all features pass
- UI: Post-build report viewer, agent mascots

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes, `--agent-type docs`, `--agent-type performance`, `--agent-type security` flags recognized.

---

### PHASE 3 — Style & UI

UI Realignment cleans up the existing interface before adding new style features. Then Style Features adds the preview engine, mixing, and color customization. Idea Code adds screenshot-to-style extraction.

---

#### RUN 6: UI Realignment
**Type:** Direct Implementation (NOT an AutoForge spec run)
**Handoff:** `.claude/handoffs/ui-realignment-handoff.md`
**Why before Style Features:** Cleans up hardcoded colors, inconsistent spacing, and ad-hoc typography BEFORE the Style Features spec adds more UI. Otherwise the new UI would be built on top of inconsistent foundations.

**How to run:** Give the handoff file to a Claude Code agent:
```
Read .claude/handoffs/ui-realignment-handoff.md and implement everything it describes.
Do Priority 1 files first (DependencyGraph, DebugLogViewer, FeatureCard),
then Priority 2, then Priority 3.
Run "cd ui && npm run build && npm run lint" after each priority group.
```

**What gets built:**
- CSS variables in `globals.css` for graph, category, and log level colors (across all 6 themes)
- All hardcoded hex/Tailwind colors replaced with CSS variable references
- Standardized typography scale: text-2xl → text-xs with defined roles
- 8px spacing grid with symmetric padding
- Consistent Card/Button/Input component usage
- `ui/STYLE_GUIDE.md` documenting the locked-in design system

**Files modified (11 total):**
- Priority 1: `DependencyGraph.tsx`, `DebugLogViewer.tsx`, `FeatureCard.tsx`
- Priority 2: `App.tsx`, `SettingsModal.tsx`, `AgentMissionControl.tsx`, `ProgressDashboard.tsx`
- Priority 3: `KanbanBoard.tsx`, `ProjectSelector.tsx`, `NewProjectModal.tsx`
- CSS: `ui/src/styles/globals.css`
- New: `ui/STYLE_GUIDE.md`

**What to verify after:** `cd ui && npm run lint && npm run build` passes. Open the app and verify no visual regressions in both light and dark mode across all 6 themes.

---

#### RUN 7: Style Features Bundle
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/style-features-spec.xml`
**Source handoffs:** `style-preview-grid-handoff.md` + `color-customization-handoff.md` + `color-picker-preview-task.md` + `style-mixing-handoff.md`
**Depends on:** RUN 6 (UI Realignment) should be done first — this spec includes a `ui_realignment` section that overlaps. If UI Realignment was already done, those features will pass quickly.

**What gets built:**
- Full-screen style preview engine (StylePreview + StyleFullPreview components)
- 4 tabbed sample pages per style (Landing, Dashboard, Settings, Feed)
- Base + accent style mixing with compatibility validation
- Per-project color customization (6 color overrides via ColorCustomizer)
- Fanned card stack with Playwright-generated screenshot thumbnails
- Dedicated preview route: `/#/style-preview/:styleId/:page`
- API: full token data in GET /api/styles, accent-compatibility endpoints

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes.

---

#### RUN 8: Idea Code Integration
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/idea-code-integration-spec.xml`
**Source handoff:** `.claude/handoffs/idea-code-integration-handoff.md`

**What gets built:**
- Mentor's "Idea Code" style extraction methodology
- `server/services/style_extractor.py` with vision LLM analysis
- POST /api/styles/extract endpoint
- "Extract from Screenshot" option in style picker
- Extracted styles saved as custom style in project config
- Same output format as predefined styles

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes.

---

### PHASE 4 — Infrastructure & Polish

These are independent of each other. DevOps adds CI/CD and monitoring. Knowledge Base adds post-build documentation. Bridge Feature 10 only matters when the website (Project A) is ready.

---

#### RUN 9: DevOps Pipeline
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/devops-pipeline-spec.xml`
**Source handoff:** `.claude/handoffs/devops-pipeline-handoff.md`
**Note:** Depends on QA Pipeline (Run 1) being built — the CI/CD agent generates workflows that run test suites created by the QA pipeline.

**What gets built:**
- CI/CD Pipeline Generator Agent (GitHub Actions workflows, Dockerfiles)
- Monitoring Setup Agent (Sentry integration, health endpoints, analytics)
- Auto-Update Agent (recurring dependency maintenance, creates PRs)
- New agent types: `cicd`, `monitoring`, `auto-update`
- Maintenance scheduling via existing `scheduler_service.py`
- UI: Maintenance section in ScheduleModal or separate Maintenance tab

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes.

---

#### RUN 10: Knowledge Base
**Type:** AutoForge Spec Run
**Spec:** `.claude/generated-prds/knowledge-base-spec.xml`
**Source handoff:** `.claude/handoffs/knowledge-base-tutorial-handoff.md`

**What gets built:**
- Knowledge Base Generator Agent (Markdown docs + screenshots per feature)
- Tutorial Video Script Generator (Playwright commands + narrator text)
- In-App Help System (embedded help sidebar with contextual docs)
- New agent type: `knowledge-base` with Sage mascot
- Three tiers: Basic (docs), Full (docs + scripts), Premium (docs + scripts + in-app help)
- UI: Docs tab in project view, Knowledge Base section in SettingsModal
- Auto-spawns after all features pass (when enabled in settings)

**What to verify after:** `ruff check .` passes, `cd ui && npm run lint && npm run build` passes.

---

#### RUN 11: Bridge Feature 10 (AutoForge Side)
**Type:** Direct Implementation (NOT an AutoForge spec run)
**Handoff:** `.claude/handoffs/boilerplate-autoforge-bridge-handoff.md` — **Feature 10 ONLY**
**When to do this:** Only when the website (Project A) is being built or ready. This adds the hooks that let AutoForge run as a SaaS build worker. Useless without the website to call it.

**How to run:** Give a Claude Code agent these instructions:
```
Read .claude/handoffs/boilerplate-autoforge-bridge-handoff.md
Implement ONLY Feature 10: "AutoForge Server Modifications"
Do NOT implement Features 1-9 or 11 (those are for the website project).
```

**What gets built:**
- `BUILD_AUTH_TOKEN` environment variable + middleware that validates per-build JWTs
- `--callback-url` CLI flag (sends progress/completion/failure callbacks to web app)
- `--build-id` CLI flag (links agent session to SaaS build record)
- Heartbeat sender (periodic health pings to orchestrator)
- SaaS mode detection: `AUTOFORGE_SAAS_MODE=1` env var
- `AUTOFORGE_ALLOW_REMOTE=1` to accept non-localhost connections

**Files modified:** `client.py`, `autonomous_agent_demo.py`, new middleware in `server/`

**What to verify after:** `ruff check .` passes, `python autonomous_agent_demo.py --help` shows `--callback-url` and `--build-id` flags.

---

## Troubleshooting

### "Feature too large for one session"
If a Coding agent times out on a feature, the feature is probably too broad. Check the spec — if a single feature has more than 6-8 steps, it may need to be split. You can manually edit the features in the `.autoforge/features.db` SQLite database to break a large feature into two smaller ones.

### "Spec references files that don't exist"
The specs were generated from handoffs written at a point in time. If the AutoForge codebase has changed since then, some file paths or function names in the specs might be stale. The Coding agent should be able to adapt (it reads the actual codebase), but if it gets stuck, check the handoff for the intended behavior and guide the agent.

### "Dependency cycle detected"
The specs declare feature dependencies. If AutoForge's dependency resolver rejects a spec, check the `<dependencies>` tags in the XML. Foundation features (database, config) should have no dependencies. Remove any circular references.

### "Build fails lint/type check"
After each run, verify:
```bash
ruff check .                    # Python lint
cd ui && npm run lint           # TypeScript lint
cd ui && npm run build          # TypeScript compile + Vite build
```
If these fail, fix the issues before starting the next run. Accumulated lint errors from earlier runs will block later ones.

### Phase ordering
The phases are recommended, not required. Within a phase, the order matters (e.g., UI Realignment before Style Features). Across phases, there's flexibility — you could do DevOps Pipeline (Phase 4) right after QA Pipeline (Phase 1) if that's more useful to you.

---

## Quick Reference: All 11 Items at a Glance

| # | Name | Type | Spec/Handoff File | Phase | Status |
|---|------|------|-------------------|-------|--------|
| 1 | QA Pipeline | Spec Run | `qa-pipeline-spec.xml` | 1 | DONE (aligned) |
| 2 | Pre-Build Intelligence | Spec Run | `pre-build-intelligence-spec.xml` | 1 | DONE (backend; UI viewers pending) |
| 3 | Mentor Standards | Direct Impl | `mentor-standards-integration-handoff.md` | 1 | DONE |
| 4 | Build Intelligence | Spec Run | `build-intelligence-spec.xml` | 2 | NOT STARTED |
| 5 | Post-Build Reports | Spec Run | `post-build-reports-spec.xml` | 2 | NOT STARTED |
| 6 | UI Realignment | Direct Impl | `ui-realignment-handoff.md` | 3 | DONE (aligned) |
| 7 | Style Features | Spec Run | `style-features-spec.xml` | 3 | DONE (fanned cards + screenshots pending) |
| 8 | Idea Code Integration | Spec Run | `idea-code-integration-spec.xml` | 3 | PARTIAL (core extraction works; persistence + prompt injection pending) |
| 9 | DevOps Pipeline | Spec Run | `devops-pipeline-spec.xml` | 4 | NOT STARTED |
| 10 | Knowledge Base | Spec Run | `knowledge-base-spec.xml` | 4 | NOT STARTED |
| 11 | Bridge Feature 10 | Direct Impl | `boilerplate-autoforge-bridge-handoff.md` (F10 only) | 4 | NOT STARTED |

---

## Alignment Fixes Applied

The following consistency/alignment issues were identified and fixed:

1. **FeatureModal.tsx** — Category badge colors were hardcoded (`bg-pink-500`, `bg-purple-500`, etc.) while `FeatureCard.tsx` had already been migrated to CSS variables (`var(--color-category-N)`). Fixed to use the same CSS variable approach.

2. **ColorCustomizer.tsx** — Component docstring says "Collapsed by default" but `isOpen` was initialized to `true`. Fixed to `useState(false)`.

3. **prompts.py `_get_style_context()`** — When users customize colors via the UI `ColorCustomizer`, those custom colors were stored in `project_config.json` but never read by the prompt system. The coding agent received the default style colors even when the user had customized them. Fixed by reading `custom_colors` from config and calling `apply_custom_colors()` from `style_manager.py`.

4. **QA pipeline mascots** — Added three dedicated mascots for QA pipeline agent types: Lens (reviewer), Aegis (QA), Iris (computer_use). Added to `types.ts` (AgentMascot union), `mascotData.tsx` (color palettes + SVG components), and `ActivityFeed.tsx` (color lookup).

5. **PipelineStatusBadge.tsx** — Replaced hardcoded Tailwind classes (`bg-amber-400`, `bg-emerald-500`, `bg-blue-500`) with CSS variables (`--color-pipeline-*`), consistent with the STYLE_GUIDE.md design system. Added light and dark mode variants in `globals.css`.

## Remaining Known Gaps (Not Alignment — Future Work)

- **Item 1**: `v1.0-qa-passed` git tag on QA success not implemented; `_check_computer_use_ready()` orchestrator method missing
- **Item 2**: UI components for spec analysis viewer, architecture tab, and pipeline stepper not yet built (backend is complete)
- **Item 7**: Fanned card stack with static PNG thumbnails and screenshot generation script not implemented (live StylePreview components used instead)
- **Item 8**: No persistence layer for extracted styles (ephemeral only); CRUD APIs, normalization, and prompt injection pipeline not built
