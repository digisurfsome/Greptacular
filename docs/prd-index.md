# PRD Index

> **Master list of every PRD in the repo.** Sorted by page/system. Updated: 2026-04-03
>
> **Rules for agents:** When you create a new PRD, ADD IT TO THIS INDEX. No exceptions.
> Use the format: `| PRD Name | Page | Status | Path |`

---

## Status Key
- **ACTIVE** — Currently being built or recently completed
- **PLANNED** — Designed, waiting for implementation
- **IDEA** — Concept stage, needs more thought
- **DONE** — Fully implemented
- **STALE** — Outdated, may need refresh

---

## Page-Specific PRDs

### Workspace
| PRD | Status | Path |
|-----|--------|------|
| Optimization Support Agents & Dashboard | PLANNED | `docs/page-prds/workspace/prd-optimization-agents.md` |
| Workspace Chat UX | DONE | `docs/prd-workspace-chat-ux.md` |
| Workspace Rebuild | DONE | `docs/prd-workspace-rebuild.md` |
| Workspace Session Persistence | DONE | `PRD_WORKSPACE_SESSION_PERSISTENCE.md` |
| Pre-PRD Workspace V2 | STALE | `docs/pre-prd-workspace-v2.md` |
| Walkie-Talkie System | PLANNED | `docs/PRD_WALKIE_TALKIE_SYSTEM.md` |
| Session Data Layer (Phase 1) | DONE | `docs/PRD_SESSION1_DATA_LAYER.md` |
| Interactive Layer (Phase 2) | DONE | `docs/PRD_SESSION2_INTERACTIVE_LAYER.md` |

### Dashboard
| PRD | Status | Path |
|-----|--------|------|
| Mission Control Phase 3-4 | PLANNED | `PRD_MISSION_CONTROL_PHASE_3_4.md` |
| Dependency Graph Component | DONE | `docs/prd-dependency-graph-component.md` |

### DunkStack
| PRD | Status | Path |
|-----|--------|------|
| DunkStack Multi-Provider | PLANNED | `docs/PRD_DUNKSTACK_MULTI_PROVIDER.md` |
| DunkStack Super Agent | PLANNED | `docs/prd-dunkstack-super-agent.md` |

### YT Strategy Lab
| PRD | Status | Path |
|-----|--------|------|
| YT Lab V2 | PLANNED | `docs/prd-yt-lab-v2.md` |
| YT Lab Tool Analyzer | PLANNED | `docs/prd-yt-lab-tool-analyzer.md` |
| Video-to-Tool Factory | PLANNED | `docs/prd-video-to-tool-factory.md` |
| Opus/Sonnet Model Toggle | PLANNED | `docs/page-prds/yt-strategy-lab/prd-opus-sonnet-model-toggle.md` |

### CLI Scripter
| PRD | Status | Path |
|-----|--------|------|
| CLI Scripter V2 | PLANNED | `docs/prd-cli-scripter-v2.md` |
| CLI Scripter Timeout Fix | PLANNED | `docs/prd-cli-scripter-timeout-fix.md` |

### PRD Shredder
| PRD | Status | Path |
|-----|--------|------|
| PRD Shredder | DONE | `docs/prd-prd-shredder.md` |

### SEO Tools
| PRD | Status | Path |
|-----|--------|------|
| SEO Smart Search Optimizer | PLANNED | `docs/prd-seo-smart-search-optimizer.md` |

### Token Budget
| PRD | Status | Path |
|-----|--------|------|
| Token Budget System | DONE | `docs/prd-token-budget-system.md` |

### Tool Runner / Tool Factory
| PRD | Status | Path |
|-----|--------|------|
| Tool Execution Engine | PLANNED | `docs/prd-tool-execution-engine.md` |

---

## System-Wide PRDs (Not Page-Specific)

| PRD | Category | Status | Path |
|-----|----------|--------|------|
| Automated Holding Patterns | Agent System | PLANNED | `docs/PRD_AUTOMATED_HOLDING_PATTERNS.md` |
| Orchestrator State Completion | Agent System | PLANNED | `docs/PRD_ORCHESTRATOR_STATE_COMPLETION.md` |
| Prompt Assembly Agent Orchestrator | Agent System | PLANNED | `docs/PRD_PROMPT_ASSEMBLY_AGENT_ORCHESTRATOR.md` |
| API Research Engine | Integration | PLANNED | `docs/prd-api-research-engine.md` |
| Autonomous Factory | Build System | PLANNED | `docs/prd-autonomous-factory.md` |
| Build Planner V2 | Build System | PLANNED | `docs/prd-build-planner-v2.md` |
| Multi-Pass Pipeline | Build System | PLANNED | `docs/prd-multi-pass-pipeline.md` |
| Factory Task Queue | Build System | PLANNED | `docs/prd-factory-task-queue.md` |
| Task Queue Agent OS | Agent System | PLANNED | `docs/prd-task-queue-agent-os.md` |
| Rate Limit Engine | Infrastructure | PLANNED | `docs/prd-rate-limit-engine.md` |
| Image Calibration System | Utility | IDEA | `docs/prd-image-calibration-system.md` |
| Reverse Engineering Scanner | Utility | IDEA | `docs/prd-reverse-engineering-scanner.md` |
| Cold Email Engine | External | IDEA | `docs/prd-cold-email-engine.md` |
| Timonacci Labs | External | IDEA | `docs/prd-timonacci-labs.md` |
| PRD Maker Reference Systems | PRD Maker | DONE | `docs/PRD_MAKER_REFERENCE_SYSTEMS.md` |
| Mechanism Self-Tuning | PRD Maker | PLANNED | `blueprints/mechanism-tuning/PRD-mechanism-self-tuning.md` |
| Rant-to-PRD Spec | PRD Maker | DONE | `docs/rant-to-prd-spec.md` |
| Rant-to-PRD Addendum | PRD Maker | DONE | `docs/rant-to-prd-addendum.md` |

---

## Bug Fix / Quick Fix PRDs

| PRD | Page | Status | Path |
|-----|------|--------|------|
| Fix User Context Limit | Workspace | PLANNED | `docs/agent-briefs/PRD-fix-user-context-limit.md` |
| JSON Parsing Robustness | Workspace | PLANNED | `docs/agent-briefs/PRD-json-parsing-robustness.md` |

---

## Other Reference Files (Not PRDs But Related)

| File | What It Is | Path |
|------|-----------|------|
| PRD Plans Library | Index of planned PRDs | `PRD-plans-library.md` |
| PRD Generation Scripts | Scripts for generating PRDs | `.claude/prd-generation-scripts.md` |

---

## Where PRDs Should Go

| PRD Type | Location | Example |
|----------|----------|---------|
| Page-specific feature | `docs/page-prds/{page-name}/prd-{feature}.md` | `docs/page-prds/workspace/prd-optimization-agents.md` |
| System-wide feature | `docs/prd-{feature-name}.md` | `docs/prd-rate-limit-engine.md` |
| Bug fix / quick fix | `docs/agent-briefs/PRD-{fix-name}.md` | `docs/agent-briefs/PRD-fix-user-context-limit.md` |
| Blueprint (multi-phase) | `blueprints/{feature-name}/` | `blueprints/mechanism-tuning/` |

**When creating a new PRD, always:**
1. Put it in the right location per the table above
2. Add an entry to this index
3. Set the status (IDEA, PLANNED, ACTIVE, DONE)
4. Note which page it relates to (or "System" if general)
