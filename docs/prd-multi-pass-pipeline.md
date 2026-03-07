# PRD: Multi-Pass Pipeline with Adaptive Tuning

**Status:** Draft
**Date:** 2026-03-04
**Author:** Owner + Claude (Session 7)
**Depends on:** Factory Task Queue PRD, Rate Limit Intelligence Engine PRD

---

## Standards Layer

### Technology Stack
- **Backend:** Python 3.11+ (FastAPI, SQLAlchemy, asyncio)
- **Frontend:** React 19 + TypeScript + Vite 7 + Tailwind CSS v4 + TanStack Query
- **Agent SDK:** Claude Agent SDK (claude-code CLI)
- **Models:** Claude Opus 4.6 (architect/reviewer), Claude Sonnet 4.6 (builder/tester)
- **Data:** JSON files for config/levers, SQLite for metrics/history (via SQLAlchemy)
- **Real-time:** WebSocket for status updates + React Query polling

### Architecture Patterns
- Services live in `server/services/` — one service per domain concern
- API routers live in `server/routers/` — thin REST layer calling services
- React hooks in `ui/src/hooks/` wrap TanStack Query for API calls
- UI components in `ui/src/components/` — follow workspace standards
- Config stored in `~/.autoforge/` for global, `.autoforge/` per project
- All new features must follow existing patterns in the codebase (see CLAUDE.md)

### Coding Conventions
- Python: ruff linting, line length 120, type hints on public methods
- TypeScript: ESLint + strict TypeScript, functional components with hooks
- File naming: snake_case for Python, PascalCase for React components
- Commits: conventional commits to main branch, descriptive messages
- No over-engineering — minimal viable implementation per phase

### Quality Standards
- `npm run build` must pass (TypeScript + Vite build)
- `ruff check .` must pass (Python linting)
- No new security vulnerabilities (OWASP top 10)
- UI must work across all existing themes (semantic Tailwind tokens)

---

## Product Layer

### Vision

**The 24/7 Autonomous Software Factory**

AutoForge already has a factory that runs agents in a loop with handoffs between sessions. The next evolution is a multi-model pipeline where Sonnet (cheap, abundant — 68+ hours/day) does the bulk work in multiple passes, and Opus (expensive, limited — 5.7 hours/day) provides quality gates at critical checkpoints. The system learns from every task, auto-tunes its own parameters, and evolves distinct "personalities" for different types of work.

The goal: queue up tasks across 60-70 software projects, hit go, and the factory runs 24/7 — producing Opus-quality output at Sonnet-level cost.

### The Core Insight

Sonnet has 3x more daily compute hours than there are hours in a day. So instead of running once and hoping, you run Sonnet 2-3 times on everything. Each pass reduces the work remaining. By the time Opus touches it, 80%+ of the work is done.

Opus doesn't come in at the end as one big review. It's interleaved — small checkpoints between each major stage. Nothing moves forward on a bad foundation.

### Target Users
- The owner (non-coder) who manages 60-70 software projects
- Uses Anthropic's $200 Max plan (one account, partner has a second)
- Schedule: works ~10am onward, factory runs overnight autonomously

### Rate Limit Budget (One Account, $200 Max Plan)

| Model | Weekly Hours | Daily Hours | % of 24hr Day |
|---|---|---|---|
| Opus 4.6 | ~40 | ~5.7 | 24% |
| Sonnet 4.6 | ~480 | ~68.6 | unlimited (3x headroom) |

With two accounts: 11.4 hrs Opus + unlimited Sonnet = comfortable 24/7.

### Use Cases
1. **Software Build** — New app from app_spec, phased construction with PRD, code, test, review
2. **Bug Fix Campaign** — Scan 20 repos for bugs, fix them all overnight
3. **QA Sweep** — Test every button and function across multiple apps
4. **Refactor Pass** — Clean up legacy spaghetti code from early vibe-coding days
5. **Feature Addition** — Add features to existing apps with detailed PRDs
6. **Reverse Engineering** — Understand and document poorly-built codebases

### Roadmap

- **Phase 1 (Foundation):** Task pipeline stages, data model, basic metrics collection
- **Phase 2 (Multi-Model):** Sonnet/Opus routing per stage, interleaved checkpoints
- **Phase 3 (Levers):** Configurable parameters, lever storage, basic dashboard
- **Phase 4 (Data Pipeline):** Full outcome metrics, per-stage tracking, daily aggregation
- **Phase 5 (Dashboard):** Tuning dashboard with sliders, recommendations display
- **Phase 6 (Suggestions):** Calculation engine that analyzes data and suggests lever changes
- **Phase 7 (Auto-Tuning):** AI agent adjusts levers within safe bounds
- **Phase 8 (Learned Presets):** Task-type profiles with proven optimal settings

---

## Specs Layer

### 1. Pipeline Architecture

Every task flows through a configurable pipeline of stages. Each stage has a model assignment (Sonnet or Opus), a role, and configurable parameters.

#### Default Pipeline Template (Software Build)

```
TASK ENTERS QUEUE
       │
       ▼
┌──────────────────────┐
│ Stage 1: PRD Draft   │  Model: Sonnet  │  Role: Architect
│ Stage 2: PRD Review  │  Model: Sonnet  │  Role: Reviewer
│ Stage 3: PRD Approve │  Model: Opus    │  Role: Quality Gate
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Stage 4: Code Build  │  Model: Sonnet  │  Role: Builder
│ Stage 5: Code Review │  Model: Sonnet  │  Role: Reviewer
│ Stage 6: Code Approve│  Model: Opus    │  Role: Quality Gate
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Stage 7: QA Test     │  Model: Sonnet  │  Role: Tester
│ Stage 8: Bug Fix     │  Model: Sonnet  │  Role: Fixer
│ Stage 9: Final Sign  │  Model: Opus    │  Role: Quality Gate
└──────────┬───────────┘
           ▼
       TASK COMPLETE ✓
```

#### Alternative Pipeline Templates

**Bug Fix Pipeline** (simpler — no PRD stage):
- Stage 1: Bug Scan (Sonnet) — find and document bugs
- Stage 2: Bug Fix (Sonnet) — fix each bug
- Stage 3: Verify Fixes (Sonnet) — re-test
- Stage 4: Approve (Opus) — review critical fixes

**QA Sweep Pipeline** (test-focused):
- Stage 1: Generate Test Script (Sonnet) — create comprehensive test plan
- Stage 2: Execute Tests (Sonnet) — test every button/function
- Stage 3: Document Issues (Sonnet) — detailed bug reports
- Stage 4: Fix Issues (Sonnet) — fix what it can
- Stage 5: Review & Fix Hard Bugs (Opus) — handle the rest

**Quick Fix Pipeline** (minimal — Sonnet only):
- Stage 1: Fix (Sonnet) — do the work
- Stage 2: Verify (Sonnet) — check it
- No Opus checkpoint (simple tasks don't need it)

### 2. Pipeline Stage Data Model

```python
class PipelineStage:
    stage_id: str           # e.g. "prd_draft", "code_build"
    stage_type: str         # "draft", "review", "approve", "build", "test", "fix"
    display_name: str       # "PRD Draft", "Code Build"
    model: str              # "sonnet" or "opus"
    role: str               # "architect", "reviewer", "builder", "tester", "fixer", "quality_gate"
    prompt_template: str    # Base prompt for this stage's agent
    status: str             # "pending", "running", "completed", "failed", "skipped"

    # Configurable levers (per-stage)
    sonnet_passes: int      # How many Sonnet runs (1-5, default 2)
    opus_depth: str         # "quick", "standard", "deep" (for Opus stages)
    prompt_detail: str      # "brief", "detailed", "surgical"
    quality_threshold: int  # 0-100, minimum to pass to next stage
    auto_retry: bool        # Retry on failure
    max_retries: int        # Max retry attempts (default 2)

    # Metrics (filled after completion)
    started_at: datetime
    completed_at: datetime
    tokens_input: int
    tokens_output: int
    duration_seconds: float
    pass_number: int        # Which Sonnet pass (1, 2, 3...)
    changes_made: int       # For review/approve stages
    change_severity: str    # "none", "minor", "moderate", "major"
    errors_found: int       # For test stages
    errors_fixed: int       # For fix stages
```

### 3. Task with Pipeline

Extends the existing Task model from the Task Queue PRD:

```python
class Task:
    # ... existing fields from Task Queue PRD ...

    # Pipeline fields (new)
    pipeline_template: str          # "software_build", "bug_fix", "qa_sweep", "quick_fix", "custom"
    pipeline_stages: list[PipelineStage]  # Ordered list of stages
    current_stage_index: int        # Which stage is active

    # Lever overrides (task-level, overrides defaults)
    lever_overrides: dict           # Any lever values that differ from preset defaults

    # Outcome metrics
    outcome: TaskOutcome            # Filled on completion
```

### 4. Lever Configuration System

Levers are stored in `~/.autoforge/pipeline_config.json`:

```json
{
  "version": 1,

  "global_levers": {
    "opus_daily_hours": 5.7,
    "sonnet_daily_hours": 68.6,
    "opus_reserve_pct": 20,
    "nighttime_mode": "full_speed",
    "quality_vs_speed": 0.6,
    "max_concurrent_tasks": 3,
    "nighttime_start": "22:00",
    "nighttime_end": "10:00",
    "timezone": "America/Chicago"
  },

  "stage_defaults": {
    "prd_draft":    { "sonnet_passes": 2, "prompt_detail": "detailed" },
    "prd_review":   { "sonnet_passes": 1, "prompt_detail": "detailed" },
    "prd_approve":  { "opus_depth": "standard" },
    "code_build":   { "sonnet_passes": 2, "prompt_detail": "surgical" },
    "code_review":  { "sonnet_passes": 1, "prompt_detail": "detailed" },
    "code_approve": { "opus_depth": "standard" },
    "qa_test":      { "sonnet_passes": 2, "prompt_detail": "detailed" },
    "bug_fix":      { "sonnet_passes": 1, "prompt_detail": "surgical" },
    "final_approve":{ "opus_depth": "quick" }
  },

  "task_type_presets": {
    "software_build": {
      "pipeline_template": ["prd_draft", "prd_review", "prd_approve", "code_build", "code_review", "code_approve", "qa_test", "bug_fix", "final_approve"],
      "opus_budget_pct": 30,
      "description": "Full build cycle with PRD, code, test, review"
    },
    "bug_fix": {
      "pipeline_template": ["bug_scan", "bug_fix", "verify_fixes", "approve"],
      "opus_budget_pct": 15,
      "description": "Find and fix bugs with Opus review on critical fixes"
    },
    "qa_sweep": {
      "pipeline_template": ["gen_test_script", "execute_tests", "document_issues", "fix_issues", "review_hard_bugs"],
      "opus_budget_pct": 20,
      "description": "Comprehensive testing with Opus handling hard bugs"
    },
    "quick_fix": {
      "pipeline_template": ["fix", "verify"],
      "opus_budget_pct": 0,
      "description": "Simple fix, Sonnet only, no Opus checkpoint needed"
    }
  }
}
```

### 5. Outcome Metrics Collection

Every completed task produces a TaskOutcome record stored in `~/.autoforge/pipeline_metrics.json` (later SQLite):

```python
class TaskOutcome:
    task_id: str
    task_type: str          # software_build, bug_fix, etc.
    project: str
    complexity_estimate: str  # "simple", "moderate", "complex"

    stage_metrics: list[StageMetric]  # Per-stage data

    # Aggregates
    total_time_minutes: float
    opus_time_minutes: float
    sonnet_time_minutes: float
    total_tokens_input: int
    total_tokens_output: int
    rework_count: int           # Stages that had to retry
    final_quality_score: int    # 0-100 from final sign-off
    bugs_found_post: int        # Bugs found AFTER task "complete"

    # Lever snapshot (what settings were active)
    lever_snapshot: dict

    completed_at: datetime

class StageMetric:
    stage_id: str
    model: str
    tokens_input: int
    tokens_output: int
    duration_seconds: float
    pass_number: int
    changes_made: int       # Opus: how many edits at checkpoint
    change_severity: str    # none/minor/moderate/major
    errors_found: int       # QA stages
    errors_fixed: int       # Fix stages
    quality_score: int      # Self-assessed or from next stage
    retries: int            # How many times this stage retried
```

### 6. Key Signals That Drive Lever Adjustments

| Signal | What It Means | Lever to Adjust |
|---|---|---|
| Opus makes many changes at PRD checkpoint | Sonnet PRDs not good enough | ↑ sonnet_passes for PRD, or ↑ prompt_detail |
| Opus makes zero changes at a checkpoint | That Opus gate is wasted | Turn off opus checkpoint for this task type |
| High rework_count in code stage | Code quality low | ↑ sonnet_passes for code, or ↑ prompt_detail to surgical |
| bugs_found_post > 0 | QA missed things | ↑ sonnet_passes for QA, or add Opus deep review |
| Opus has idle hours | Over-allocated | ↓ opus_reserve_pct, or add more Opus checkpoints |
| Sonnet fails quality_threshold repeatedly | Task too hard for Sonnet | Route stage to Opus directly |
| Stage duration consistently under estimate | Over-allocated time | Reduce passes or depth |
| Stage duration consistently over estimate | Under-allocated | Add passes or increase depth |

### 7. Dashboard UI Design

Add a new "Pipeline Tuning" page/panel in the Workspace. Shows:

**Section 1: Today's Metrics**
- Tasks completed, in progress, queued
- Opus utilization % (hours used / hours available)
- Sonnet utilization %
- Average quality score
- Rework rate (% of stages that needed retry)
- Post-completion bug rate

**Section 2: Lever Controls**
- Per-stage sliders for sonnet_passes (1-5)
- Per-stage toggle for opus checkpoint (on/off)
- Per-stage dropdown for opus_depth (quick/standard/deep)
- Per-stage dropdown for prompt_detail (brief/detailed/surgical)
- Global quality_vs_speed slider

**Section 3: Task Type Presets**
- List of presets with their pipeline template and lever defaults
- Edit button to modify presets
- "Create Custom" for new presets

**Section 4: Recommendations**
- System-generated suggestions based on accumulated data
- Each suggestion shows: what to change, why, expected impact
- "Apply" button per suggestion, or "Apply All"

**Section 5: Opus Budget**
- Visual bar: hours used / hours available today
- Reserve % indicator
- Forecast: "At current pace, Opus runs out at 2:30 PM"

### 8. Evolution Path

**Phase A — Manual (0-20 tasks):**
Owner and agent review metrics together. Owner adjusts levers via dashboard. Learning what works.

**Phase B — Assisted (20-50 tasks):**
System shows recommendations panel. "Based on 30 tasks, suggest increasing Sonnet QA passes from 2 to 3." Owner approves or rejects.

**Phase C — Semi-Auto (50-200 tasks):**
System auto-applies non-critical adjustments (pass counts, depth levels). Owner approves critical changes (model routing, checkpoint removal). System auto-reverts if quality drops.

**Phase D — Autonomous (200+ tasks):**
AI agent monitors outcomes and adjusts levers within configured bounds. Owner gets daily summary. Emergency rollback if metrics degrade beyond threshold.

**Phase E — Learned Presets (500+ tasks):**
Distinct profiles emerge per task type + project type. New tasks auto-match to closest profile. Profiles evolve independently based on their own outcome data.

### 9. Integration Points

**With Task Queue (already PRD'd):**
- Each task in the queue gets a `pipeline_template` field
- Queue Executor calls Pipeline Executor instead of Factory Controller directly
- Pipeline Executor runs stages sequentially, switching models as needed

**With Rate Limit Engine (already PRD'd + Phase 1 built):**
- Pipeline Executor checks rate limit budget before starting Opus stages
- If Opus budget depleted, queues Opus stages and continues with Sonnet-only stages
- Rate limit events feed into pipeline metrics

**With Factory Controller (already built):**
- Pipeline stages map to factory sessions (each stage = one agent session)
- Handoff data flows through the same handoff_watcher mechanism
- Factory preset system extended with pipeline templates

**With DunkStack (existing):**
- Token tracking feeds into pipeline metrics
- Safety tiers trigger stage transitions (tier 2 = handoff, tier 3 = stop)

### 10. Implementation Phases

Each phase should be completable by ONE agent session staying under 50% context window.

**Phase 1: Pipeline Stage Data Model + Config**
- Create `server/services/pipeline_config.py` — lever storage, defaults, read/write
- Create `server/models/pipeline.py` — PipelineStage, TaskOutcome, StageMetric models
- Store in `~/.autoforge/pipeline_config.json`
- API endpoints: GET/PUT pipeline config, GET pipeline templates
- Estimated context: ~35-40% (new files, ~8 files touched)

**Phase 2: Pipeline Executor Service**
- Create `server/services/pipeline_executor.py` — runs stages sequentially
- Model switching between Sonnet/Opus per stage
- Stage status tracking (pending → running → completed)
- Integrates with existing Factory Controller for agent lifecycle
- WebSocket events for stage transitions
- Estimated context: ~35-40% (complex service, ~6 files touched)

**Phase 3: Task Queue Integration**
- Extend task model with pipeline_template and pipeline_stages
- Queue Executor calls Pipeline Executor
- Pipeline template selection in task creation UI
- Stage progress visible in queue list
- Estimated context: ~30-35% (extending existing code, ~8 files touched)

**Phase 4: Metrics Collection**
- Stage metrics recorded on every stage completion
- TaskOutcome recorded on task completion
- Lever snapshot captured with each outcome
- Storage in `~/.autoforge/pipeline_metrics.json`
- API endpoints: GET metrics summary, GET metrics by task type
- Estimated context: ~30% (data collection, ~5 files touched)

**Phase 5: Dashboard UI — Metrics Display**
- New React component: PipelineDashboard
- Today's metrics section (cards with numbers)
- Opus/Sonnet utilization bars
- Per-stage metrics table
- Estimated context: ~35% (new UI component, ~4 files touched)

**Phase 6: Dashboard UI — Lever Controls**
- Slider components for sonnet_passes
- Toggle/dropdown for opus settings
- Save lever changes to config
- Task type preset editor
- Quality vs speed global slider
- Estimated context: ~35% (UI forms, ~4 files touched)

**Phase 7: Recommendation Engine**
- Analyze accumulated metrics against signal table
- Generate plain-English suggestions
- Store suggestions, display in dashboard
- "Apply" action per suggestion
- Estimated context: ~30% (analysis logic, ~4 files touched)

**Phase 8: Auto-Tuning Logic**
- Agent-driven lever adjustment within bounds
- Auto-revert on quality degradation
- Daily summary generation
- Owner notification on adjustments
- Estimated context: ~35% (autonomous logic, ~5 files touched)

**Phase 9: Learned Presets**
- Cluster task outcomes by type + project characteristics
- Generate preset profiles from outcome data
- Auto-match new tasks to closest preset
- Preset evolution over time
- Estimated context: ~30% (data analysis + matching, ~4 files touched)

**Phase 10: Integration Testing + Polish**
- End-to-end test: task enters queue → pipeline runs → metrics collected → recommendations generated
- Fix edge cases and race conditions
- Dashboard polish and responsive layout
- Documentation update
- Estimated context: ~25% (testing + fixes, ~6 files touched)

### 11. Success Metrics

- Owner can queue 10+ tasks overnight and wake up to completed work
- Each task processes through multi-model pipeline without manual intervention
- Opus utilization stays under 90% (reserve maintained)
- Post-completion bug rate below 10% after 50+ tasks
- Lever adjustments measurably improve quality or speed (A/B tracking)
- System generates useful recommendations by task #50
- After 200+ tasks, auto-tuning maintains quality without manual intervention

### 12. Out of Scope (For Now)

- Parallel stage execution within a task (stages are sequential)
- Third-party model support (only Claude Opus + Sonnet)
- Cloud/remote execution (local only)
- Cost tracking in dollars (just tokens and hours)
- Multi-user access to the dashboard
- Git branching strategies per task (uses main)
