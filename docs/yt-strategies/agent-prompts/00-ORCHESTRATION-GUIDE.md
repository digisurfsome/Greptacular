# YT Strategy Lab — Agent Orchestration Guide

## Overview

8 agents build and verify the entire YT Strategy Lab system across 3 waves. Each prompt is a self-contained, copy-paste-ready document for a fresh Claude Code session.

---

## Architecture

```
Phase 1 (DONE) — Core UI + YouTube Ingestion
    │
    ├── Phase 2  — Auto-Processor (video → project)     AGENT 1
    │   └── Phase 3  — Batch Import (multi-URL)          AGENT 4
    │
    ├── Phase 4  — Computer Use Engine (Docker+agent)    AGENT 3
    │   ├── Phase 5  — Live Execution Viewer              AGENT 5
    │   │   └── Phase 6  — Pause/Resume/Takeover          AGENT 5
    │   └── Phase 8  — Screen Recording                   AGENT 6
    │
    ├── Phase 7  — Model Routing & Roles (UI)             AGENT 4
    │
    └── Phase 9  — Screenshot Intelligence                AGENT 2
```

---

## Execution Plan

### Wave 1 — Start All 3 Simultaneously (No Dependencies Between Them)

| Agent | Prompt File | Phases | Est. Tokens | Notes |
|-------|-------------|--------|-------------|-------|
| **Agent 1** | `wave1-agent1-auto-processor.md` | Phase 2 | ~23K | Core value prop |
| **Agent 2** | `wave1-agent2-screenshot-intelligence.md` | Phase 9 | ~19K | Independent |
| **Agent 3** | `wave1-agent3-computer-use-engine.md` | Phase 4 | ~43K | Biggest build |

**Parallel:** Yes, all 3 can run at the same time.
**Duration:** Agent 3 will likely take longest (largest scope).

**After Wave 1:** Merge all three branches into main before starting Wave 2.

---

### Wave 2 — Start All 3 After Wave 1 Merges

| Agent | Prompt File | Phases | Est. Tokens | Depends On |
|-------|-------------|--------|-------------|------------|
| **Agent 4** | `wave2-agent4-batch-import-model-routing.md` | Phase 3 + 7 | ~39K | Agent 1 (Phase 2) |
| **Agent 5** | `wave2-agent5-live-viewer-pause-resume.md` | Phase 5 + 6 | ~47K | Agent 3 (Phase 4) |
| **Agent 6** | `wave2-agent6-screen-recording.md` | Phase 8 | ~20K | Agent 3 (Phase 4) |

**Parallel:** Yes, all 3 can run at the same time (after Wave 1 merges).
**Duration:** Agent 5 is the tightest budget (77% of available tokens).

**After Wave 2:** Merge all three branches into main before QA.

---

### Wave 3 — QA Verification (After All Builds Merge)

| Agent | Prompt File | Verifies | Notes |
|-------|-------------|----------|-------|
| **QA Agent A** | `wave3-qa-agent-a-features.md` | Phases 2, 9, 3, 7 | UI + backend features |
| **QA Agent B** | `wave3-qa-agent-b-execution.md` | Phases 4, 5, 6, 8 | Docker + execution stack |

**Parallel:** Yes, both QA agents can run simultaneously.
**Context budget:** QA agents can go up to 55-60% — they're fixing small bugs, not generating features.

---

## Quick Reference

### Total Agents: 8
### Total Serial Waves: 3
### Parallel Opportunities: 3 + 3 + 2 = 8 agents across 3 waves

### Context Budget Per Agent (200K model, 50% cap)

```
Available after fixed overhead: ~61K tokens

Agent 1:  23K / 61K = 38% ██████████░░░░░░░░░░░░░░░░ ← comfortable
Agent 2:  19K / 61K = 31% ████████░░░░░░░░░░░░░░░░░░ ← comfortable
Agent 3:  43K / 61K = 70% ██████████████████░░░░░░░░ ← tight but fits
Agent 4:  39K / 61K = 64% ████████████████░░░░░░░░░░ ← moderate
Agent 5:  47K / 61K = 77% ████████████████████░░░░░░ ← tightest
Agent 6:  20K / 61K = 33% ████████░░░░░░░░░░░░░░░░░░ ← comfortable
QA-A:     ~30K / 61K = 49% █████████████░░░░░░░░░░░░ ← with fixes ~60%
QA-B:     ~35K / 61K = 57% ███████████████░░░░░░░░░░ ← with fixes ~65%
```

---

## Merge Strategy

After each wave, merge agent branches into main:

```bash
# After Wave 1
git checkout main
git pull
git merge agent1-branch
git merge agent2-branch
git merge agent3-branch
git push

# After Wave 2 (same pattern)
# After Wave 3 (same pattern)
```

If merge conflicts occur, resolve them before starting the next wave. Conflicts are unlikely within waves (agents touch different files) but possible between waves.

---

## Files Each Agent Creates

### Agent 1 (Phase 2)
```
server/routers/yt_processing.py          (NEW)
server/services/yt_processor.py          (NEW)
server/routers/__init__.py               (MODIFY — add export)
server/main.py                           (MODIFY — include router)
ui/src/lib/api.ts                        (MODIFY — add processVideo())
ui/src/lib/types.ts                      (MODIFY — add Process types)
ui/src/pages/YTStrategyLabPage.tsx        (MODIFY — add Process button)
```

### Agent 2 (Phase 9)
```
server/services/screenshot_analyzer.py   (NEW)
server/routers/yt_ingestion.py           (MODIFY — enhanced detection)
ui/src/components/yt-lab/ScreenshotGallery.tsx (NEW)
ui/src/lib/types.ts                      (MODIFY — add Screenshot types)
ui/src/pages/YTStrategyLabPage.tsx        (MODIFY — add gallery to steps)
```

### Agent 3 (Phase 4)
```
docker/computer-use/Dockerfile           (NEW)
docker/computer-use/supervisord.conf     (NEW)
server/services/computer_use_agent.py    (NEW)
server/services/docker_manager.py        (NEW)
server/routers/execution.py              (NEW)
server/routers/__init__.py               (MODIFY)
server/main.py                           (MODIFY)
ui/src/lib/api.ts                        (MODIFY — execution API)
ui/src/lib/types.ts                      (MODIFY — execution types)
```

### Agent 4 (Phases 3 + 7)
```
server/routers/yt_batch.py               (NEW)
server/services/model_router.py          (NEW)
server/routers/__init__.py               (MODIFY)
server/main.py                           (MODIFY)
ui/src/components/yt-lab/BatchImportView.tsx (NEW)
ui/src/lib/api.ts                        (MODIFY — batch API)
ui/src/lib/types.ts                      (MODIFY — batch + routing types)
ui/src/pages/YTStrategyLabPage.tsx        (MODIFY — batch view + model/role dropdowns)
```

### Agent 5 (Phases 5 + 6)
```
ui/src/components/yt-lab/ExecutionViewer.tsx  (NEW)
ui/src/components/yt-lab/StepTracker.tsx      (NEW)
ui/src/components/yt-lab/AgentLog.tsx         (NEW)
ui/src/components/yt-lab/BrowserView.tsx      (NEW)
ui/src/components/yt-lab/ExecutionTopBar.tsx   (NEW)
ui/src/hooks/useExecutionWebSocket.ts         (NEW)
ui/src/lib/types.ts                           (MODIFY — execution event types)
ui/src/pages/YTStrategyLabPage.tsx             (MODIFY — execution view state)
```

### Agent 6 (Phase 8)
```
server/services/screen_recorder.py       (NEW)
ui/src/components/yt-lab/CaptureGallery.tsx (NEW)
ui/src/lib/api.ts                        (MODIFY — capture API)
ui/src/lib/types.ts                      (MODIFY — capture types)
ui/src/pages/YTStrategyLabPage.tsx        (MODIFY — gallery in step view)
```

---

## Conflict Risk Matrix

Files modified by multiple agents (potential merge conflicts):

| File | Agents | Risk | Notes |
|------|--------|------|-------|
| `ui/src/lib/types.ts` | 1,2,3,4,5,6 | **HIGH** | Each adds different types. Append-only, so conflicts are resolvable. |
| `ui/src/lib/api.ts` | 1,2,3,4,6 | **HIGH** | Each adds different functions. Append-only. |
| `ui/src/pages/YTStrategyLabPage.tsx` | 1,2,4,5,6 | **MEDIUM** | Different sections modified. May need manual merge. |
| `server/routers/__init__.py` | 1,3,4 | **LOW** | Just adding exports. |
| `server/main.py` | 1,3,4 | **LOW** | Just adding router includes. |

**Mitigation:** Within each wave, agents touch different sections of shared files. Merge between waves to establish a clean base for the next wave.
