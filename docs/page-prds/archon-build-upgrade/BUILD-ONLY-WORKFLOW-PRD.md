# Build-Only Workflow (prd-pipeline-BUILD) — PRD

> User asked: split the PRD pipeline in two. Pipeline A = PRD maker only. Pipeline B = Build only. Feed a PRD in, get code out.
>
> Why: if the PRD is already done, don't re-run 45 min of planning. Also useful when you hand a PRD to a different builder (Sonnet, new AutoForge, Claude Code, etc.).

---

## What It Is

A standalone DAG workflow that takes a completed PRD artifact bundle as input and executes ONLY the build phases. Skips stages 0 through 10. Starts at codebase intelligence and goes through phase-1, phase-2, phase-3, deploy, archive.

---

## Inputs (required)

The workflow takes a single directory path as input. That directory must contain:

| File | Purpose | Required? |
|------|---------|-----------|
| `context_packet.json` | Serial state carrier from PRD side | YES |
| `phases/phase-1.md` | Phase 1 plan | YES |
| `phases/phase-2.md` | Phase 2 plan | Only if 2+ phases |
| `phases/phase-3.md` | Phase 3 plan | Only if 3+ phases |
| `CLAUDE.md` | Root rules | YES |
| `BUILD_RULES.md` | Build-specific rules | YES |
| `README.md` | Human-readable summary | YES |
| `build.sh` | One-shot rebuild script | YES |
| `.env.example` | Env var template | YES |
| `files_allowed.json` | List of allowed file paths per phase | Recommended |
| `mechanism-contracts.json` | Mechanism boundaries (V3 only) | Optional |

Minimum viable input: the 8 files + phase(s). If missing, workflow halts at input-validation with a clear error.

---

## Outputs

Same as current pipeline build section:
- Built source code in `source/`
- Per-phase compliance reports
- Final build-report.md
- Deploy artifacts (if deployment target set)
- Archived PRD + build in `docs/generated-prds/<date>__<name>/`

---

## Workflow Design (DAG)

```
                    input-validation (bash)
                            ↓
                    build-codebase-intelligence
                            ↓
                    phase-1-baseline (bash)
                            ↓
                    phase-1-execute (sonnet)
                            ↓
                    phase-1-compile-check (bash)          ← V3 Fix 7
                            ↓
                    phase-1-verify-deliverables (bash)    ← V3 Fix 2
                            ↓
                    phase-1-boundary-check (bash)         ← V3 Fix 9
                            ↓
            ┌───────────────┴───────────────┐
    review-correctness-contracts    review-production-readiness    ← V3 Fix 4
            └───────────────┬───────────────┘
                            ↓
                    build-fix-issues
                            ↓
                    phase-1-compliance-gate
                            ↓
                    phase-1-final-status
                            ↓
                    phase-1-full-checkpoint
                            ↓
                  [repeat for phase-2, phase-3 if present]
                            ↓
                    deploy-gate
                            ↓
                    build-deploy (conditional)
                            ↓
                    archive-prd
```

---

## Key YAML Structure

```yaml
name: prd-pipeline-BUILD
description: Takes a completed PRD bundle and builds code. No planning phase.

inputs:
  - name: PRD_BUNDLE_DIR
    type: string
    required: true
    description: Absolute path to directory containing PRD artifacts

steps:
  # ── VALIDATION ─────────────────────────────────────────────────
  - id: validate-prd-bundle
    bash: |
      python3 .archon/scripts/validate-prd-bundle.py "$PRD_BUNDLE_DIR"
    # Exits 1 if required files missing
    timeout: 30000

  # ── IMPORT INTO ARTIFACTS DIR ──────────────────────────────────
  - id: import-bundle
    bash: |
      cp -r "$PRD_BUNDLE_DIR"/* "$ARTIFACTS_DIR/"
    depends_on: [validate-prd-bundle]

  # ── DETECT PHASE COUNT ─────────────────────────────────────────
  - id: detect-phase-count
    bash: |
      ls "$ARTIFACTS_DIR/phases/" | grep -c 'phase-[0-9]*\.md'
    depends_on: [import-bundle]

  # ── CODEBASE INTELLIGENCE ──────────────────────────────────────
  - id: build-codebase-intelligence
    command: build-codebase-intelligence
    depends_on: [import-bundle]
    model: sonnet
    context: fresh

  # ── PHASE 1 (always runs) ──────────────────────────────────────
  - id: phase-1-baseline
    bash: |
      git rev-parse HEAD 2>/dev/null || echo "HEAD-fallback-phase1"
    depends_on: [build-codebase-intelligence]

  - id: phase-1-execute
    command: build-implement
    depends_on: [phase-1-baseline]
    model: sonnet
    context: fresh
    idle_timeout: 900000

  # [V3 gates + reviewers + compliance...]

  # ── PHASE 2 (conditional) ──────────────────────────────────────
  - id: phase-2-execute
    command: build-execute-v2
    depends_on: [phase-1-checkpoint, detect-phase-count]
    when: "$detect-phase-count.output >= '2'"
    model: sonnet
    context: fresh

  # ── PHASE 3 (conditional) ──────────────────────────────────────
  - id: phase-3-execute
    command: build-execute-v2
    depends_on: [phase-2-checkpoint, detect-phase-count]
    when: "$detect-phase-count.output >= '3'"
    model: sonnet
    context: fresh

  # ── DEPLOY + ARCHIVE (unchanged from pipeline-c) ───────────────
```

---

## Dynamic Phase Dispatch (the fix for "hardcoded 3 phases")

Current pipeline-c has phase-1, phase-2, phase-3 as rigid nodes. If only 2 phases planned, phase-3 still fires and fails.

Build-only pipeline uses `when:` conditional on `detect-phase-count.output`. If PRD says 2 phases, phase-3 skips. If it says 5 phases... well, pipeline still caps at 3 but emits a warning. True N-phase dispatch needs programmatic YAML generation (defer).

**Mid-term improvement (V3 Fix 8-adjacent):** Generate workflow YAML dynamically from `context_packet.json` phase count, so pipeline has exactly N phase nodes. Not in this PRD. Defer.

---

## Entry Point Script

User runs:

```powershell
cd "C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular"
.\.archon\bin\archon.exe run prd-pipeline-BUILD --input "C:\path\to\existing\prd\bundle"
```

Or via Archon web UI: select `prd-pipeline-BUILD`, enter bundle path, click run.

---

## Validation Script

`.archon/scripts/validate-prd-bundle.py`:

```python
"""
Validate that a PRD bundle dir contains the minimum files required
for build-only pipeline to run.
"""
REQUIRED_FILES = [
    'context_packet.json',
    'CLAUDE.md',
    'BUILD_RULES.md',
    'README.md',
    'build.sh',
    '.env.example',
]
REQUIRED_DIRS = ['phases']

def validate(bundle_dir: str) -> tuple[bool, list[str]]:
    missing = []
    for f in REQUIRED_FILES:
        if not os.path.exists(os.path.join(bundle_dir, f)):
            missing.append(f)
    for d in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(bundle_dir, d)):
            missing.append(f"{d}/")
    phase_dir = os.path.join(bundle_dir, 'phases')
    if os.path.isdir(phase_dir):
        phase_files = [f for f in os.listdir(phase_dir) if f.startswith('phase-')]
        if len(phase_files) == 0:
            missing.append("phases/phase-1.md")
    return (len(missing) == 0, missing)
```

---

## How to Use Right Now (before the workflow exists)

You already have a completed PRD bundle from tonight's run. Path:
`C:\Users\lober\.archon\workspaces\digisurfsome\audio-recorder-scaled\artifacts\runs\0087c45cd7da9fc15fad9193f3277946\`

Once build-only pipeline is implemented, you can point it at that directory and build WITHOUT re-running 45 min of PRD stages.

---

## Relationship to PRD Maker V3 Fixes

Build-only pipeline is **not** independent of V3 improvements. It reuses V3 gates (compile check, verify deliverables, boundary check, 2-specialist review). If V3 fixes haven't landed yet, build-only pipeline uses current 4-reviewer setup.

**Rollout order:**
1. Ship V3 Fixes 1+4+7 in pipeline-c (current pipeline)
2. Create pipeline-BUILD as a fork that includes V3 fixes
3. After both mature, deprecate pipeline-c → pipeline-FULL (PRD + build) and pipeline-BUILD (build only)

---

## Effort

| Piece | Effort |
|-------|--------|
| YAML file (copy from pipeline-c, strip stages 0-10) | Small (~1 hour) |
| Validation script | Small |
| Dynamic phase dispatch via `when:` | Small |
| Testing against existing bundle | Medium (1 run = 30-45 min) |
| **Total** | **Half day of focused work** |

---

## Success Criteria

- Given a valid PRD bundle, pipeline builds code in ~20-30 min (vs 60-90 for full pipeline)
- Given an invalid bundle (missing files), pipeline fails in <30 sec with clear error
- Phase dispatch is dynamic — 1 phase PRD runs 1 phase, 3 phase PRD runs 3
- Built code passes same compliance gates as full pipeline
- Can feed same bundle to new AutoForge for A/B comparison
