# AutoForge Features Build — Enhancements to AutoForge Itself

## What This Is

This is **Project B** — adding new features to AutoForge by pointing AutoForge at its own codebase. This is a completely separate AutoForge run from the website build (Project A).

**How to build:** Point AutoForge at the AutoForge codebase → feed these PRDs → AutoForge adds features to itself.

---

## Generated PRD Specs (Ready to Feed to AutoForge)

These XML specs are in `.claude/generated-prds/` and are ready to be used as `app_spec.txt` inputs for AutoForge runs. Each one is a self-contained set of features.

### 1. QA Pipeline
**Spec:** `.claude/generated-prds/qa-pipeline-spec.xml`
**Handoffs:** `qa-pipeline-handoff.md` + `computer-use-qa-handoff.md`
**BUILD THIS FIRST** — Other features depend on QA infrastructure.

What it adds:
- Generated Playwright test suite per feature
- Code Review Agent (new agent type: `reviewer`)
- Enhanced regression testing
- Final QA Agent (new agent type: `qa`)
- Computer Use QA (Claude vision-based testing)
- UI integration for QA controls
- Orchestrator wiring for 4-phase pipeline

### 2. Pre-Build Intelligence
**Spec:** `.claude/generated-prds/pre-build-intelligence-spec.xml`
**Handoff:** `pre-build-intelligence-handoff.md`

What it adds:
- Spec Analyzer Agent (scores PRD quality before building)
- Architecture Planner Agent (generates implementation plan)
- Dependency Auto-Detection (suggests feature dependencies)
- CLI flags: `--skip-spec-analysis`, `--min-spec-score`, `--force-build`, `--skip-architect`

### 3. Build Intelligence
**Spec:** `.claude/generated-prds/build-intelligence-spec.xml`
**Handoff:** `build-intelligence-handoff.md`

What it adds:
- Build History tracking (metrics per build in SQLite)
- PRD Quality Scoring (scores specs before building)
- Continuous Improvement Pipeline (learns from past builds)

### 4. Post-Build Reports
**Spec:** `.claude/generated-prds/post-build-reports-spec.xml`
**Handoff:** `post-build-reports-handoff.md`

What it adds:
- Docs Agent (auto-generates documentation)
- Performance Agent (profiling and optimization)
- Security Agent (audit, can block shipping)
- Orchestrator wiring + UI integration

### 5. DevOps Pipeline
**Spec:** `.claude/generated-prds/devops-pipeline-spec.xml`
**Handoff:** `devops-pipeline-handoff.md`

What it adds:
- CI/CD Pipeline Generator Agent (GitHub Actions, Docker)
- Monitoring Setup Agent (Sentry, health endpoints, analytics)
- Auto-Update Agent (recurring dependency maintenance)

### 6. Knowledge Base
**Spec:** `.claude/generated-prds/knowledge-base-spec.xml`
**Handoff:** `knowledge-base-tutorial-handoff.md`

What it adds:
- Knowledge Base Generator Agent (Markdown docs + screenshots)
- Tutorial Video Script Generator
- In-App Help System (embedded help sidebar)
- Three tiers: Basic, Full, Premium (no pricing — just feature levels)

### 7. Idea Code Integration
**Spec:** `.claude/generated-prds/idea-code-integration-spec.xml`
**Handoff:** `idea-code-integration-handoff.md`

What it adds:
- Mentor's "Idea Code" style extraction methodology
- `style_extractor.py` service with vision LLM analysis
- Extract styles from screenshots → same format as predefined styles

### 8. Style Features Bundle
**Spec:** `.claude/generated-prds/style-features-spec.xml`
**Handoffs:** `style-preview-grid-handoff.md` + `color-customization-handoff.md` + `color-picker-preview-task.md` + `style-mixing-handoff.md`

What it adds:
- UI realignment to locked-in design system
- Base + accent style mixing
- Per-project color customization (6 color overrides)
- Full-screen style preview engine (4 sample pages per style)
- Playwright screenshot generation (48 static previews)

---

## Direct Implementation Handoffs (No Generated Spec)

These handoffs are written as direct implementation instructions — they modify specific files in the AutoForge codebase. They don't go through the Initializer → Coding Agent pipeline. Give these directly to a Claude Code agent or developer.

### 9. Mentor Standards Integration
**Handoff:** `.claude/handoffs/mentor-standards-integration-handoff.md`

What it adds:
- STEP 4.5 coding standards (15 rules) to `coding_prompt.template.md`
- Universal design system to style guide generation
- Identity-first questions to spec creation flow
- Dual description format (technical + user action) for features

**Files modified:** `.claude/templates/coding_prompt.template.md`, `.claude/templates/initializer_prompt.template.md`, `server/services/style_manager.py`, `.claude/commands/create-spec.md`, `server/services/spec_chat_session.py`

### 10. UI Realignment
**Handoff:** `.claude/handoffs/ui-realignment-handoff.md`

What it adds:
- Standardized typography scale (text-2xl → text-xs)
- 8px spacing grid
- CSS variables for all colors (no more hardcoded hex/Tailwind colors)
- Consistent component patterns (Card, Button, Input)
- `ui/STYLE_GUIDE.md` documenting the design system

**Files modified:** `DependencyGraph.tsx`, `DebugLogViewer.tsx`, `FeatureCard.tsx`, `App.tsx`, `SettingsModal.tsx`, `AgentMissionControl.tsx`, `ProgressDashboard.tsx`, `KanbanBoard.tsx`, `ProjectSelector.tsx`, `NewProjectModal.tsx`, `globals.css`

### 11. Bridge Feature 10 (AutoForge Side)
**Handoff:** `.claude/handoffs/boilerplate-autoforge-bridge-handoff.md` (Feature 10 only)

What it adds:
- `BUILD_AUTH_TOKEN` middleware for SaaS mode
- `--callback-url` flag (worker → web app notifications)
- `--build-id` flag (links agent session to SaaS build record)
- Heartbeat sender (periodic health pings)
- SaaS mode detection (`AUTOFORGE_SAAS_MODE=1`)

**Files modified:** `client.py`, `autonomous_agent_demo.py`, `server/` middleware

---

## Recommended Build Order

**Phase 1 — Foundation (build these first):**
1. QA Pipeline (everything else benefits from QA)
2. Pre-Build Intelligence (improves all subsequent builds)
3. Mentor Standards Integration (direct implementation — improves code quality for everything after)

**Phase 2 — Intelligence Layer:**
4. Build Intelligence (learns from Phase 1 builds)
5. Post-Build Reports (docs, performance, security agents)

**Phase 3 — Style & UI:**
6. UI Realignment (direct implementation — clean up before adding more UI)
7. Style Features Bundle (preview grid, mixing, color customization)
8. Idea Code Integration (screenshot-to-style extraction)

**Phase 4 — Infrastructure:**
9. DevOps Pipeline (CI/CD, monitoring, auto-update)
10. Knowledge Base (post-build documentation)
11. Bridge Feature 10 (AutoForge side of SaaS bridge — only needed when website is ready)

---

## What's Stripped Out (For Later)

- **Credit pricing** — Was a separate handoff, removed
- **Marketplace** — Boilerplate/style/plugin marketplaces, separate project
- **Screenshot Style Extractor** — Removed from style features bundle (Idea Code integration covers this functionality)
- **Lead magnets** — StyleVault giveaway, Domain Finder, separate standalone apps
