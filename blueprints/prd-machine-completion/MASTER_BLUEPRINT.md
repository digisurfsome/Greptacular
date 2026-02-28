# AutoForge Master Blueprint — The Complete System

> The end-to-end autonomous app builder: from idea to deployed product.
> Agent OS Blueprint Format | Standards + Product + Specs layers.

**Version**: 1.0.0
**Date**: 2026-02-27
**Status**: Master plan — the ultimate vision.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [The Complete Pipeline](#2-the-complete-pipeline)
3. [Feature Status Matrix](#3-feature-status-matrix)
4. [Phase Map](#4-phase-map)
5. [Phase A: Project Setup](#phase-a)
6. [Phase B: PRD Machine](#phase-b)
7. [Phase C: Build Intelligence](#phase-c)
8. [Phase D: Build Execution](#phase-d)
9. [Phase E: Session Infrastructure](#phase-e)
10. [Phase F: Post-Build Pipeline](#phase-f)
11. [Phase G: IdeaForge Workspace](#phase-g)
12. [Phase H: Intelligence & Learning](#phase-h)
13. [Phase I: Notifications & External](#phase-i)
14. [Repositioning Notes](#10-repositioning-notes)
15. [My Recommendations](#11-my-recommendations)

---

## 1. System Overview

AutoForge is an autonomous app builder. A user describes an idea (rant, spec,
or existing codebase) and the system produces a working, tested, styled application.

The system has **6 major subsystems** that execute in sequence:

```
┌─────────────────────────────────────────────────────────────────┐
│                     THE AUTOFORGE PIPELINE                       │
│                                                                   │
│  [A] PROJECT SETUP                                               │
│   Name → Directory → Boilerplate → UI Theme                     │
│                          ↓                                        │
│  [B] PRD MACHINE (Agent OS)                                      │
│   Intake → Refine → Discover → Features → Mechanisms →          │
│   Specs → Blueprint → Golden Orange → Quality Gate → Handoff    │
│                          ↓                                        │
│  [C] BUILD INTELLIGENCE                                          │
│   Spec Analyzer → Architecture Planner → Context Primer          │
│                          ↓                                        │
│  [D] BUILD EXECUTION                                             │
│   Initializer → Coding Agents → Testing → QA                    │
│                          ↓                                        │
│  [E] SESSION INFRASTRUCTURE (runs during D)                      │
│   Bridge → Walkie-Talkie → Holding Patterns → Context Safety    │
│                          ↓                                        │
│  [F] POST-BUILD PIPELINE                                         │
│   Docs Agent → Performance Agent → Security Agent → Reports     │
│                          ↓                                        │
│  DEPLOYED APPLICATION                                            │
└─────────────────────────────────────────────────────────────────┘
```

**Parallel subsystems** (run alongside everything):
- **[G] IdeaForge Workspace** — 1M-token coding workspace (standalone)
- **[H] Intelligence & Learning** — Cross-project learning, analytics, self-optimization
- **[I] Notifications** — Twilio/Pushover/Telegram for status updates

---

## 2. The Complete Pipeline (All Steps)

Every step a project goes through, from "I have an idea" to "here's your app":

```
 STEP 1:  Name the project
 STEP 2:  Choose directory (FolderBrowser)
 STEP 3:  Choose boilerplate (web/mobile/scratch)
 STEP 4:  Clone boilerplate repo → fresh git init
 STEP 5:  Choose UI style (12 styles, 25 palettes, 4 modifiers)
 STEP 6:  Customize style (colors, fonts, accent)
 STEP 7:  Preview style on 4 page types (auto-renderer)
 STEP 8:  Generate theme files (CSS tokens + style_guide.md)
          ─── PROJECT SETUP COMPLETE ───
 STEP 9:  Intake (rant/spec/paste/upload files)
 STEP 10: Classify input + extract entities
 STEP 11: Technical Refinement (babble → tech language)
 STEP 12: Standards questionnaire (or infer from codebase)
 STEP 13: Product Discovery (6 adaptive questions)
 STEP 14: Feature Extraction (Claude extracts from context)
 STEP 15: Coverage Assessment ("You've described ~45%")
 STEP 16: Recalibration (resolve contradictions)
 STEP 17: Gap Analysis (cross-layer: Standards ↔ Product ↔ Features)
 STEP 18: Mechanism Analysis (6-dim scoring, Developer's Choice)
 STEP 19: Spec Generation (one markdown per feature)
 STEP 20: Verification (Sonnet reviews each stage's output)
 STEP 21: Final Blueprint (companion sheet)
 STEP 22: Golden Orange (exhaustive feature imagination + utopia line)
 STEP 23: Quality Gate (score PRD 1-5, block if < 2.0)
          ─── PRD COMPLETE ───
 STEP 24: Spec Analyzer (completeness check, blocks if < 3/5)
 STEP 25: Architecture Planner (DB schema, API, component tree)
 STEP 26: Context Primer (build agent's first-read briefing)
 STEP 27: Populate features.db (priorities, deps, acceptance criteria)
 STEP 28: Validate dependency graph (cycle detection)
          ─── BUILD READY ───
 STEP 29: Initializer Agent (create features in DB)
 STEP 30: Coding Agents (implement features, 1-5 concurrent)
 STEP 31: Testing Agents (regression testing per feature)
 STEP 32: QA Verification
          ─── BUILD COMPLETE ───
 STEP 33: Docs Agent (generate documentation from code)
 STEP 34: Performance Agent (profile and benchmark)
 STEP 35: Security Agent (audit and penetration test)
 STEP 36: Build Report (summary of everything)
          ─── APP READY ───
```

**Running concurrently during Steps 29-32:**
- Bridge saves (session continuity)
- Walkie-Talkie (user ↔ agent mid-work messaging)
- Holding Patterns (zero-cost session persistence)
- Context Safety (3-tier protection)
- Decisions Log (append-only)
- Scope Boundary enforcement

---

## 3. Feature Status Matrix

Assessment of every feature against the current DunkStack.

### Legend
- **EXISTS** = Fully implemented, working
- **PARTIAL** = Some code exists, needs completion
- **MISSING** = Not implemented at all
- **IN PRD-BLUEPRINT** = Covered by `blueprints/prd-machine-completion/`

| # | Feature | Status | Where |
|---|---------|--------|-------|
| **PROJECT SETUP** |
| A1 | Project name + directory | EXISTS | `projects.py`, `NewProjectModal.tsx` |
| A2 | Boilerplate registry + clone | EXISTS | `boilerplate_manager.py` (web only, mobile planned) |
| A3 | Mobile boilerplate | MISSING | Placeholder in registry, `available: false` |
| A4 | Style selection (12 styles) | EXISTS | `style_manager.py` |
| A5 | Style customization (colors/fonts) | EXISTS | `NewProjectModal.tsx` step 4 |
| A6 | Auto-renderer (4 page previews) | EXISTS | `StylePreview.tsx` + `QuadViewPreview.tsx` (Landing, Dashboard, Settings, Feed) |
| A7 | Theme file generation | EXISTS | `generate_theme_files()` in projects router |
| A8 | Stylesheet/CSS export | MISSING | No CSS/Tailwind config export function |
| A9 | Design Guide AI chat (backend) | EXISTS | `design_guide_session.py` + WebSocket endpoint |
| A10 | Design Guide AI chat (UI wiring) | PARTIAL | `DesignGuidePanel.tsx` built, WebSocket not connected |
| A11 | Screenshot extraction | EXISTS | `style_extractor.py` (vision AI) |
| A12 | Accent compatibility matrix | PARTIAL | Documented in handoff, not in code |
| A13 | Action block parsing | PARTIAL | Regex exists, no executor |
| A14 | Fanned stack card animation | MISSING | Handoff exists, not implemented |
| A15 | Automated screenshot generation | MISSING | Playwright script not written |
| **PRD MACHINE** |
| B1 | Intake Dock (file staging) | EXISTS | `agent_os_intake_dock.py` |
| B2 | Intake (classify + extract) | EXISTS | `agent_os_intake.py` |
| B3 | Technical Refinement | MISSING | IN PRD-BLUEPRINT Phase 2 |
| B4 | Standards questionnaire | EXISTS | `agent_os_standards.py` |
| B5 | Product Discovery | EXISTS | `agent_os_product.py` |
| B6 | Feature Extraction | EXISTS | `agent_os_features.py` |
| B7 | Coverage Assessment | MISSING | IN PRD-BLUEPRINT Phase 2 |
| B8 | Recalibration | MISSING | IN PRD-BLUEPRINT Phase 2 |
| B9 | Gap Analysis | EXISTS | `agent_os_features.py` |
| B10 | Mechanism Analysis (4-dim) | EXISTS | `agent_os_mechanism.py` |
| B11 | Mechanism Analysis (6-dim) | MISSING | IN PRD-BLUEPRINT Phase 3 |
| B12 | N-way close calls | MISSING | IN PRD-BLUEPRINT Phase 3 |
| B13 | Caveat Appendix | MISSING | IN PRD-BLUEPRINT Phase 3 |
| B14 | Developer's Choice (3 modes) | PARTIAL | Base scoring exists, modes missing |
| B15 | Spec Generation | EXISTS | `agent_os_specs.py` |
| B16 | Verification Agents | MISSING | IN PRD-BLUEPRINT Phase 3 |
| B17 | Final Blueprint | MISSING | IN PRD-BLUEPRINT Phase 4 |
| B18 | Golden Orange | MISSING | IN PRD-BLUEPRINT Phase 4 |
| B19 | Quality Gate | MISSING | IN PRD-BLUEPRINT Phase 4 |
| B20 | LLM Orchestration | MISSING | IN PRD-BLUEPRINT Phase 1 |
| B21 | Provenance Tags | MISSING | IN PRD-BLUEPRINT Phase 1 |
| B22 | Handoff + Context Primer | EXISTS | `agent_os_handoff.py` |
| B23 | Codebase Reality Engine | EXISTS | `agent_os_codebase.py` |
| B24 | Feature Addition (Expand) | PARTIAL | `agent_os_expand.py` (basic, not F1-F7) |
| **BUILD INTELLIGENCE** |
| C1 | Spec Analyzer | MISSING | Template exists, no service |
| C2 | Architecture Planner | MISSING | Template exists, no service |
| C3 | Build History Intelligence | MISSING | No `build_metrics` table |
| C4 | Risk Flagging | MISSING | No implementation |
| C5 | Time Estimation | MISSING | No historical data |
| **BUILD EXECUTION** |
| D1 | Initializer Agent | EXISTS | `agent.py` + `autonomous_agent_demo.py` |
| D2 | Coding Agents (single) | EXISTS | `autonomous_agent_demo.py` |
| D3 | Parallel Agents (1-5) | EXISTS | `parallel_orchestrator.py` |
| D4 | Batch Features | EXISTS | `--batch-size` flag |
| D5 | YOLO Mode | EXISTS | `--yolo` flag |
| D6 | Feature MCP Server | EXISTS | `feature_mcp.py` |
| **SESSION INFRASTRUCTURE** |
| E1 | Bridge/Session Continuity | PARTIAL | `.agent/bridge.md` template + save endpoint |
| E2 | Walkie-Talkie | EXISTS | Full impl in workspace sessions |
| E3 | Holding Patterns | PARTIAL | Heartbeat exists, full hold loop missing |
| E4 | Context Gauge | PARTIAL | Token tracking, no real-time UI |
| E5 | Context Safety (3-tier) | PARTIAL | 48% hard stop, missing WARNING/HANDOFF tiers |
| E6 | Decisions Log | PARTIAL | Mechanism records, no persistent .log file |
| E7 | Scope Boundary | EXISTS | `generate_scope_boundary()` |
| E8 | Communications (.agent/comms/) | EXISTS | to_human, from_human, control + REST API |
| E9 | Idle/Pause Modes | PARTIAL | control.md exists, no auto-enforcement |
| **POST-BUILD** |
| F1 | Docs Agent | MISSING | No implementation |
| F2 | Performance Agent | MISSING | No implementation |
| F3 | Security Agent | MISSING | No implementation |
| F4 | Build Reports | MISSING | No implementation |
| **WORKSPACE** |
| G1 | IdeaForge Workspace (1M) | PARTIAL | Workspace exists, 1M context partial |
| G2 | Multi-conversation sidebar | PARTIAL | Some workspace UI exists |
| G3 | Context Budget Bar | MISSING | No UI component |
| G4 | Auto-Summary System | MISSING | No implementation |
| G5 | Chat Forking | MISSING | No implementation |
| G6 | File Library | MISSING | No implementation |
| G7 | GitHub Repo Connection | MISSING | No implementation |
| **INTELLIGENCE** |
| H1 | Build Analytics | MISSING | No metrics tables |
| H2 | Cross-Project Learning | MISSING | No implementation |
| H3 | Self-Optimization Engine | MISSING | No implementation |
| H4 | Prompt A/B Testing | MISSING | No implementation |
| H5 | Confidence-Scored Reads | MISSING | No implementation |
| **NOTIFICATIONS** |
| I1 | In-app Notifications | PARTIAL | REST endpoints, basic types |
| I2 | Twilio (SMS) | MISSING | No integration |
| I3 | Pushover (Push) | MISSING | No integration |
| I4 | Telegram (Bot) | MISSING | No integration |

**Summary**: 22 EXISTS, 17 PARTIAL, 32 MISSING (71 total items tracked)

---

## 4. Phase Map

Phases ordered by dependency and value:

```
Phase A: Project Setup Completion ......... 4 items (A3, A6, A8 + mobile)
Phase B: PRD Machine Completion ........... Covered by existing blueprint
Phase C: Build Intelligence ............... 5 items (C1-C5)
Phase D: Build Execution .................. Already exists (minor enhancements)
Phase E: Session Infrastructure ........... 8 items (E1, E3, E4, E5, E6, E9)
Phase F: Post-Build Pipeline .............. 4 items (F1-F4)
Phase G: IdeaForge Workspace .............. 7 items (G1-G7) — separate blueprint exists
Phase H: Intelligence & Learning .......... 5 items (H1-H5)
Phase I: Notifications .................... 3 items (I2-I4)
```

**What's already fully covered by existing blueprints:**
- Phase B → `blueprints/prd-machine-completion/` (4 phases, 16 items)
- Phase G → `blueprints/ideaforge-workspace/` (4 phases)

**What this document covers:** Phases A, C, E, F, H, I + repositioning + recommendations.

---

## Phase A: Project Setup Completion {#phase-a}

### What Exists (Impressive — ~80% Complete)

The project creation flow AND style system are substantial:

**Project Setup Pipeline**:
1. Name → Directory (FolderBrowser) → Boilerplate → Style → Customize → Spec → Build
2. `boilerplate_manager.py` — Registry with web SaaS starter (Supabase + Stripe), clone from GitHub
3. `prompts.py` — Scaffold `.autoforge/prompts/` with templates, inject boilerplate + style context
4. `registry.py` — SQLite at `~/.autoforge/registry.db`, cross-platform POSIX paths
5. `.claude/commands/create-spec.md` — 800+ line 7-phase interactive spec creation with gap analysis

**Style System** (12 styles, production-quality):
1. `style_manager.py` — 12 complete styles (Flat, Minimal, Neumorphism, Glassmorphism, Skeuomorphism,
   Neubrutalism, Bauhaus, Claymorphism, Retro-Futurism, Cyberpunk, Dark Mode, Warmer Shades).
   Each has full tokens: colors, typography, components, spacing, Tailwind config.
2. `StylePreview.tsx` — Live auto-renderer showing 4 page types (Landing, Dashboard, Settings, Feed)
3. `QuadViewPreview.tsx` — 2x2 grid showing all 4 pages at once
4. `StyleFullPreview.tsx` — Full-screen expanded view
5. `style_modifiers.py` — 4 accessibility modifiers (high-contrast buttons, large touch targets,
   high-contrast text, larger type scale). WCAG AA/AAA compliant.
6. `palettes.ts` — 24 curated color palettes (9 categories, free/premium tiers)
7. `ColorCustomizer.tsx` — Individual color picker + palette presets
8. Accent style mixing — base + accent styles, accent overrides only interactive elements
9. `style_extractor.py` — Vision AI extracts style from screenshots (Idea Code methodology)
10. `style_manager.py` — Recommendation engine with audience/vibe/age profiles
11. `design_guide_session.py` — AI design consultant chat (backend + WebSocket)
12. `DesignGuidePanel.tsx` — Chat UI sidebar (built, not wired)

### What's Missing (~20% Remaining)

#### A3: Mobile Boilerplate

**Status**: Placeholder in registry with `available: false`.

**What needs to happen**:
```python
# In boilerplate_manager.py, update mobile option:
{
    "id": "mobile-flutter-supabase",
    "name": "Flutter Starter (Supabase)",
    "description": "Cross-platform mobile app with auth, storage, real-time",
    "tech_summary": "Flutter 3.x + Dart + Supabase + Riverpod",
    "repo_url": "https://github.com/digisurfsome/{mobile-boilerplate-repo}",
    "available": True,
    "pre_built": [
        "Supabase authentication (email + OAuth)",
        "Supabase real-time subscriptions",
        "Local storage with Hive/Isar",
        "Navigation with go_router",
        "State management with Riverpod",
        "Theme system",
    ],
}
```

**Licensing note**: Flutter boilerplate has full commercial rights (per OPERATIONAL_TRUTH_v3).
Web boilerplate is personal use only. This distinction matters for the SaaS version.

#### A8: Stylesheet/CSS Export

**Status**: The style system generates CSS tokens and a style_guide.md, but
doesn't export a downloadable CSS file or Tailwind config extension.

**What needs to happen**:

```python
# In style_manager.py, add:
def export_stylesheet(
    style_id: str,
    accent_id: str | None,
    custom_colors: dict,
    modifiers: list[str],
    format: str = "css",  # "css" | "tailwind" | "both"
) -> dict:
    """Export the complete style as production files.

    Returns:
    {
        "css_variables": str,          # :root { --color-brand: #...; }
        "tailwind_extend": dict,       # Valid tailwind.config.js extend block
        "component_overrides": str,    # CSS for buttons, inputs, cards
        "style_guide_md": str,         # Human-readable guide
    }
    """
```

Add endpoint: `POST /api/styles/{style_id}/export`

#### A10: Wire Design Guide Chat

**Status**: `DesignGuidePanel.tsx` has full chat UI but line 88-99 shows a TODO:
"Send to WebSocket backend." Currently returns a dummy response after 1 second.

**What needs to happen**:
1. Connect to `/api/design-guide/ws` WebSocket endpoint
2. Parse action blocks from Claude responses (`select_style`, `set_color`, `set_font`)
3. Apply actions immediately (visual feedback as user talks to Claude)
4. The regex `ACTION_BLOCK_PATTERN` exists in `design_guide_session.py` — need executor

#### A12: Accent Compatibility Matrix

**Status**: Documented in `.claude/handoffs/style-mixing-handoff.md` but not in code.

**What needs to happen**:
1. Add `accent_compatibility` data to each style in `style_manager.py`
2. Add `get_accent_styles(base_id)` function
3. Add API endpoint to return compatible accents for a chosen base
4. UI filter to show only compatible accents after base style selection

#### A14-A15: Visual Polish (Lower Priority)

- **Fanned stack animation**: Grid cards show 4 page screenshots in a "fanned" stack.
  Hover fans out. Handoff exists at `.claude/handoffs/style-preview-grid-handoff.md`.
- **Automated screenshots**: Playwright script to generate 48 PNGs (12 styles × 4 pages)
  for fast-loading grid thumbnails. Same handoff document.

---

## Phase C: Build Intelligence {#phase-c}

### File: `server/services/build_intelligence.py` (NEW)

Pre-build analysis that runs AFTER the PRD is complete but BEFORE the builder starts.

#### C1: Spec Analyzer

```python
class SpecAnalyzer:
    """Analyze spec completeness and readiness for build.

    Scores 1-5 on completeness. Blocks build if < 3.
    """

    def analyze(self, features: list[dict], specs: dict[int, str]) -> dict:
        """Check each spec for:
        - Has acceptance criteria (testable)
        - Has technical details (not just description)
        - Dependencies are specified
        - Edge cases covered
        - Complexity estimate is reasonable

        Returns per-feature scores + overall readiness.
        """
        ...
```

**Template exists**: `.claude/templates/spec_analyzer_prompt.template.md`
**Service missing**: No Python class to use it.

#### C2: Architecture Planner

```python
class ArchitecturePlanner:
    """Generate ARCHITECTURE.md before build starts.

    Produces:
    - Database schema (tables, columns, relationships)
    - API endpoint plan (routes, methods, payloads)
    - Component tree (React/Flutter component hierarchy)
    - File structure plan (where each feature's code goes)
    - Integration points (which features share state/data)
    """

    def plan(self, features: list[dict], specs: dict, standards: str) -> dict:
        ...

    def generate_architecture_md(self) -> Path:
        """Write .agent/knowledge/ARCHITECTURE.md"""
        ...
```

**Template exists**: `.claude/templates/architect_prompt.template.md`
**Service missing**: No Python class.

#### C3: Build History Intelligence

```python
class BuildHistory:
    """Track build outcomes across projects for pattern detection.

    Database: ~/.autoforge/build_history.db

    Tables:
    - builds (id, project, started_at, completed_at, features_count,
              features_passed, tech_stack, duration_minutes, quality_score)
    - feature_patterns (tech_stack, feature_category, avg_duration,
                       failure_rate, common_issues)
    - pitfall_warnings (tech_stack, category, warning, severity, frequency)
    """
```

**Used for**: Injecting warnings into coding prompts ("React + Supabase auth:
watch for session token refresh race conditions — failed in 3 of last 7 builds").

#### C4: Risk Flagging

Based on build history, flag features as HIGH/MEDIUM/LOW risk:

```python
def assess_risk(self, feature: dict, tech_stack: str) -> dict:
    """Return risk level based on historical failure rate.

    High risk (>30% failure): Auth, payments, real-time sync
    Medium risk (15-30%): File uploads, search, notifications
    Low risk (<15%): Static pages, CRUD, settings
    """
```

#### C5: Time Estimation

```python
def estimate_time(self, feature: dict, tech_stack: str) -> dict:
    """Estimate implementation time from historical data.

    Returns:
    {
        "estimated_minutes": 45,
        "confidence": 0.7,
        "based_on_n_samples": 12,
        "range": {"low": 30, "high": 90},
    }
    """
```

---

## Phase E: Session Infrastructure Completion {#phase-e}

### E1: Bridge/Session Continuity (Complete Implementation)

**Status**: Template + save endpoint exist. Need automatic load on session start.

**What needs to happen**:

```python
# In agent.py or session startup:
async def resume_from_bridge(self, project_dir: Path) -> Optional[str]:
    """Check for bridge file and load if exists.

    Sequence:
    1. Read .agent/index.md (master navigation)
    2. Read .agent/working_memory.md (rolling context)
    3. Read .agent/bridge.md (last session's state)
    4. Delete bridge.md (consumed)
    5. Return resume context string

    If no bridge exists, return None (fresh session).
    """
```

**Auto-save on session end**:
```python
# In session cleanup:
async def save_bridge(self, project_dir: Path, context: dict):
    """Write bridge file with current state.

    Triggers:
    - Human says goodbye / session timeout
    - Context approaching limit (tier 2)
    - Explicit /checkpoint command
    """
```

### E3: Holding Patterns (Full Implementation)

**Status**: Heartbeat exists, full hold loop missing.

**What needs to happen**:

```python
class HoldingPattern:
    """Manage agent holding state between tasks.

    4-tier strategy:
    T0: [WAITING] pause (0 tokens, up to 300s)
    T1: Heartbeat micro-read (~30 tokens, read 1 line of status file)
    T2: Context summary (~200 tokens, brief checkpoint)
    T3: Proactive check (~500 tokens, lint/file changes)
    """

    def __init__(self, config: dict):
        self.strategy = config.get("hold_strategy", "auto")
        self.max_cycles = config.get("hold_max_cycles", 50)
        self.budget_tokens = config.get("hold_budget_tokens", 5000)
        self.signal_path: Optional[Path] = None

    async def enter_hold(self, session_id: str) -> Optional[str]:
        """Enter holding pattern. Returns new task if one arrives.

        Loop:
        1. Create .hold_signal file (empty = keep holding)
        2. Execute strategy tier
        3. Check .hold_signal for content (new task)
        4. If task found, return it
        5. If file deleted, return None (end session)
        6. If budget/cycles exceeded, return None
        """
        ...
```

**Hold signal file**: `~/.autoforge/sessions/{session_id}/.hold_signal`
- Empty file = keep holding
- File with content = new task
- File deleted = end session

### E4: Context Gauge (Real-Time UI)

**Status**: Token tracking exists backend, no frontend display.

**What needs to happen**:

New component: `ui/src/components/ContextGauge.tsx`

```typescript
interface ContextGaugeProps {
  inputTokens: number;
  outputTokens: number;
  maxTokens: number;  // 200000 or 1000000
  costEstimate: number;
}

// Visual bar with color zones:
// 0-45%: green
// 45-70%: yellow
// 70-90%: orange
// 90-100%: red (pulse animation)
// Shows: "127K / 200K tokens ($0.42)"
```

Wire to existing `token_usage` WebSocket events.

### E5: Context Safety (3-Tier)

**Status**: Only tier 3 (hard stop at 48%) exists.

**What needs to happen**:

```python
# In client.py PreCompact hook, add tiers:

CONTEXT_TIERS = {
    "warning": {
        "threshold": 0.45,  # 45% of context
        "action": "inject_awareness",
        "message": "Context at 45%. Prioritize completing current task."
    },
    "handoff": {
        "threshold": 0.475,  # 47.5%
        "action": "write_bridge",
        "message": "Context at 47.5%. Writing bridge file. Wrap up current work."
    },
    "hard_stop": {
        "threshold": 0.50,  # 50% (current 48% rounded)
        "action": "terminate",
        "message": "Context at 50%. Session ending. Bridge saved."
    }
}
```

### E6: Decisions Log (Persistent)

**Status**: Mechanism records decisions in memory. Need persistent file.

**What needs to happen**:

```python
# In agent_os_mechanism.py, modify record_decision():
def record_decision(self, analysis, chosen_option, reason=None):
    # ... existing logic ...

    # NEW: Append to persistent log
    log_path = self.project_dir / ".agent" / "progress" / "decisions.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"\n## {datetime.now().isoformat()} — {analysis.get('decision_point', 'Unknown')}\n")
        f.write(f"- Chose: {chosen_option}\n")
        f.write(f"- Score: {analysis.get('recommendation', {}).get('score', 'N/A')}\n")
        f.write(f"- Reason: {reason or 'Developer\\'s Choice'}\n")
        f.write(f"- Alternatives: {', '.join(a['name'] for a in analysis.get('options', []) if a['name'] != chosen_option)}\n")
```

---

## Phase F: Post-Build Pipeline {#phase-f}

### Overview

Three specialized agents that run IN PARALLEL after the build completes (all features passing).
Each produces a report. Combined into a final build report.

### File: `server/services/post_build_pipeline.py` (NEW)

```python
class PostBuildPipeline:
    """Run post-build analysis agents in parallel.

    Triggered when: all features in features.db have passes=True.
    """

    async def run(self, project_dir: Path) -> dict:
        """Run all 3 agents concurrently."""
        results = await asyncio.gather(
            self.run_docs_agent(project_dir),
            self.run_performance_agent(project_dir),
            self.run_security_agent(project_dir),
        )
        return self.generate_build_report(project_dir, results)
```

#### F1: Docs Agent

```python
async def run_docs_agent(self, project_dir: Path) -> dict:
    """Generate documentation from the built code.

    Produces:
    - README.md (if not exists)
    - API documentation (from route definitions)
    - Component documentation (from React components)
    - Database schema documentation (from models)
    - Setup/installation guide

    Uses Claude to read the code and generate docs.
    """
```

#### F2: Performance Agent

```python
async def run_performance_agent(self, project_dir: Path) -> dict:
    """Profile and benchmark the built application.

    Checks:
    - Bundle size analysis (if web app)
    - Lighthouse score estimation
    - Database query analysis (N+1, missing indices)
    - API response time estimation
    - Memory usage patterns

    Produces: performance-report.md in .agent/reports/
    """
```

#### F3: Security Agent

```python
async def run_security_agent(self, project_dir: Path) -> dict:
    """Security audit of the built application.

    Checks:
    - OWASP Top 10 vulnerability scan
    - Dependency vulnerability audit (npm audit / pip-audit)
    - Secrets detection (hardcoded keys, tokens)
    - Input validation coverage
    - Authentication/authorization patterns
    - CORS configuration
    - SQL injection potential

    Produces: security-report.md in .agent/reports/
    """
```

#### F4: Build Report

```python
def generate_build_report(self, project_dir: Path, results: list) -> dict:
    """Combine all agent reports into final build report.

    .agent/reports/build-report.md:
    - Build summary (features, duration, quality)
    - Documentation status
    - Performance analysis
    - Security findings
    - Recommendations
    """
```

---

## Phase H: Intelligence & Learning {#phase-h}

### H1: Build Analytics

**Database**: `~/.autoforge/analytics.db`

```sql
CREATE TABLE build_sessions (
    id INTEGER PRIMARY KEY,
    project_name TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    features_total INTEGER,
    features_passed INTEGER,
    features_failed INTEGER,
    tech_stack TEXT,        -- JSON
    total_tokens INTEGER,
    total_cost REAL,
    model TEXT,
    quality_score REAL      -- from quality gate
);

CREATE TABLE feature_outcomes (
    id INTEGER PRIMARY KEY,
    session_id INTEGER REFERENCES build_sessions(id),
    feature_name TEXT,
    feature_category TEXT,
    complexity TEXT,
    duration_minutes REAL,
    attempts INTEGER,
    passed BOOLEAN,
    failure_reason TEXT,
    tokens_used INTEGER
);
```

### H2: Cross-Project Learning

```python
class CrossProjectLearning:
    """Learn from past projects to reduce future questions.

    After 5-10 projects:
    - Track which gap analysis questions are always answered the same way
    - Auto-fill universally-answered questions
    - Only ask truly unique questions

    Target: reduce questions to ~13% of original set.
    """

    def get_common_answers(self) -> dict[str, str]:
        """Return questions that had the same answer in >80% of projects."""
        ...

    def should_auto_fill(self, question_id: str) -> Optional[str]:
        """If this question has a universal answer, return it."""
        ...
```

### H3: Self-Optimization Engine

```python
class SelfOptimizer:
    """Tune system parameters based on build outcomes.

    Lever registry:
    - batch_size: 1-3, target: throughput, constraint: quality > 3.0
    - parallel_agents: 1-5, target: speed, constraint: failure_rate < 20%
    - verification_enabled: bool, target: quality, constraint: cost < budget
    - hold_max_cycles: 10-100, target: session_continuity

    Algorithm: Conservative hill-climbing.
    Change ONE lever. Wait 3 sessions. Measure. Keep or revert.
    """
```

### H4: Prompt A/B Testing

```python
class PromptTester:
    """A/B test prompt variations.

    - Hash prompts for versioning
    - Assign builds to variant A or B
    - Track quality scores per variant
    - After N builds (statistical significance), declare winner
    """
```

### H5: Confidence-Scored File Reads

```python
class ReadConfidence:
    """Track how much of each file was actually read.

    Levels:
    - FULL: entire file read
    - SECTION: specific section/function read
    - SUMMARY: only index/TOC read
    - INDEX: only filename seen

    Tag downstream decisions with confidence level.
    When things go wrong, trace to decisions made on partial reads.
    """
```

---

## Phase I: Notifications & External {#phase-i}

### File: `server/services/notification_channels.py` (NEW)

```python
class NotificationChannels:
    """External notification delivery.

    Config stored in: ~/.autoforge/.env or settings UI

    Channels:
    - Twilio: SMS for blockers/emergencies
    - Pushover: App push notifications (normal + critical tiers)
    - Telegram: Bot messages with inline keyboards
    """

    async def send(self, channel: str, message: str, severity: str = "normal"):
        ...

    async def send_twilio_sms(self, message: str):
        """SMS via Twilio. For: build failures, security findings."""
        ...

    async def send_pushover(self, message: str, priority: int = 0):
        """Push notification. For: feature complete, build done."""
        ...

    async def send_telegram(self, message: str, parse_mode: str = "Markdown"):
        """Telegram bot message. For: progress updates, status."""
        ...
```

**Settings UI**: Add notification configuration section to SettingsModal:
- Channel enable/disable toggles
- API key / token input fields
- Severity threshold per channel
- Test notification button

---

## 10. Repositioning Notes {#10-repositioning-notes}

### Golden Orange: CONFIRMED — After PRD, Before Build

The Golden Orange was originally conceived as post-build ("what features could we add
after v1?"). We repositioned it to **after the PRD is complete but before the build starts**
(Step 22 in the pipeline, PRD-Blueprint Phase 4).

**Why this is better**:
- The user gets the full feature imagination BEFORE committing to a build
- They can promote Golden Orange features INTO the build before it starts
- It serves as both a "here's what you could build" preview AND a future roadmap
- The build agent doesn't need to run for the user to see possibilities
- If the user promotes features, they get properly specced and scored

**The original post-build version** still makes sense as a second pass:
after seeing the built app, Claude could generate MORE features based on what the
code actually looks like. But that's an enhancement for later (Phase F+ territory),
not the primary position.

### Other Repositioning

**Spec Analyzer + Architecture Planner**: Moved AFTER Quality Gate, BEFORE features.db population.

Originally these were vaguely "pre-build." Now they're explicitly Steps 24-25, between
the PRD being approved (Quality Gate pass) and the features.db being populated (Step 27).
This means the Architecture Planner's output (ARCHITECTURE.md) gets included in the
Context Primer that the builder reads.

**Scope Boundary**: Stays where it is (handoff stage) but gets enhanced with Golden Orange
features marked as "FUTURE" and Quality Gate warnings included.

---

## 11. My Recommendations — What's Missing {#11-my-recommendations}

Here's my honest assessment of what I think is missing or should be reconsidered
across the entire system:

### CRITICAL (Should build soon)

**1. Error Recovery Pipeline**

Right now if an agent fails (crashes, runs out of context, produces broken code),
the system doesn't have a structured recovery path. There should be:
- Automatic retry with the last feature's state restored
- "Rescue agent" that reads the broken state and decides: rollback, fix, or skip
- Git-based rollback to last known good state per feature
- Failure classification (transient vs permanent vs needs-human)

This is different from the bridge system (which handles normal session endings).
This handles abnormal termination. The parallel orchestrator does some of this
but it's not systematic.

**2. Regression Prevention During Build**

When Agent 2 implements Feature 5, it might break Feature 3 (which Agent 1 already
passed). The system needs:
- Automated regression testing after each feature (exists with `--batch-size` testing)
- But: a way to detect WHICH feature broke WHICH other feature
- Dependency-aware regression (only re-test features that share code paths)
- Automatic "who broke what" attribution

**3. The "Spec Drift" Problem**

The PRD says "use magic links for auth." The builder implements password auth because
it's faster. No one catches this until QA. There should be:
- Spec compliance checking (after each feature: does the code match the spec?)
- Deviation alerts (warn, not block — sometimes the builder's choice is better)
- Decision logging for deviations (WHY the builder chose differently)

### HIGH VALUE (Would differentiate AutoForge)

**4. Live Preview During Build**

The dev server exists (`DevServerControl.tsx`). But there's no automated preview
generation. After each feature completes:
- Take a screenshot of the relevant page
- Show it in the UI next to the feature card
- Build up a visual progress gallery
- User can see the app forming in real-time without opening a browser

This is a "wow" feature for demos and the SaaS product.

**5. User Feedback Loop During Build**

The walkie-talkie lets users talk to agents. But there's no structured way for
users to say "this feature looks wrong" and have it automatically:
- Create a revision task
- Pause the feature's "passing" status
- Queue a rework session with the feedback context

Think: a "thumbs down" button on each feature card that triggers a rework.

**6. Cost Dashboard**

Token tracking exists but isn't surfaced. Users should see:
- Cost per feature (how much did auth cost to build?)
- Cost per session (how much did this build run cost?)
- Cost projection (at this rate, remaining features will cost $X)
- Cost comparison across projects (are builds getting cheaper?)
- Break-even analysis (this project cost $47 to build vs $500 freelancer)

This is killer for the SaaS product's value proposition.

### NICE TO HAVE (Future enhancements)

**7. Multi-Agent Conversation View**

When 3 agents are running in parallel, the user sees interleaved logs. There should be:
- Per-agent conversation view (see what Agent 2 is doing)
- Cross-agent awareness view (what's each agent working on right now)
- "Architect's view" — the dependency graph animated with agent activity

**8. Template Marketplace**

Once the boilerplate + style system is solid:
- Users share their boilerplate + style combinations
- "Start from someone else's foundation"
- Community-contributed styles beyond the 12 built-in
- Rating/review system for templates

**9. Incremental Builds**

After v1 is built, adding features should be incremental:
- Don't re-run the full PRD
- Detect what changed, generate ONLY the new specs
- Re-test ONLY affected features
- Feature Addition Engine (F1-F7) is the start of this

**10. Export to Deployment**

After build + post-build pipeline:
- One-click deploy to Vercel/Netlify/Railway
- Docker container generation
- CI/CD pipeline generation (.github/workflows/)
- Environment variable management (.env template)

### ARCHITECTURAL CONCERN

**11. The Two-System Problem**

Right now there are two overlapping systems for interacting with Claude:
- **AutoForge project agents** (build features, use MCP servers, run in subprocesses)
- **IdeaForge Workspace** (general coding, WebSocket-based, use anthropic SDK)

These should eventually converge or at least share infrastructure. The workspace
uses `anthropic` SDK directly while AutoForge uses `claude_agent_sdk` via subprocess.
The walkie-talkie exists in workspace but not in AutoForge build agents (which use
MCP-based communication instead).

Long-term, the workspace should be able to "become" an AutoForge build session
and vice versa. A user starts chatting in the workspace, decides to build an app,
and the conversation seamlessly transitions into the PRD machine without losing
context. That's the ultimate UX.

---

## Build Order (Recommended)

If I were prioritizing what to build next after the current testing phase:

```
1. Phase B: PRD Machine Completion (blueprint exists, build it)
   └─ This IS the DunkStack building itself

2. Phase A: Project Setup (mobile boilerplate + theme completion)
   └─ Quick wins, user already has the boilerplate

3. Phase E: Session Infrastructure (bridge + holding + context safety)
   └─ Makes every build session more reliable

4. Phase C: Build Intelligence (spec analyzer + architecture planner)
   └─ Makes builds smarter from day 1

5. Phase F: Post-Build Pipeline (docs + security + performance)
   └─ Adds value after every build

6. Phase H: Intelligence & Learning (analytics + cross-project)
   └─ Gets better over time, needs data first

7. Phase I: Notifications (Twilio/Pushover/Telegram)
   └─ Nice to have, not critical path

8. Phase G: IdeaForge Workspace (separate blueprint, big scope)
   └─ Standalone product, parallel development track
```

**The DunkStack building itself out** (Phase B) is the obvious first move.
The PRD Machine blueprint is ready. Let it eat.
