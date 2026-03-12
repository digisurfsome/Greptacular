# Agent Brief: Build Planner — 5-Role Pipeline + Script Generation

> **What this does:** Upgrades the Build Planner to generate bash scripts that use 5 specialized agent roles instead of just "coder per phase." The result is dramatically better build quality because each role does one job well.
>
> **Prerequisite:** The Build Planner fix brief (`build-planner-fix.md`) must be completed first — that switches the backend to subscription auth and adds "Generate All."
>
> **Difficulty:** 4/10 — It's mostly prompt engineering + script generation. The UI changes are small (add a section to the form). No new architecture.

---

## THE 5-ROLE PIPELINE (What We're Building)

This is the optimal autonomous build pipeline. Each role is a separate Claude CLI call with a specific model and prompt. The Build Planner generates all the scripts automatically.

### The Roles

| # | Role | Model | When | Purpose |
|---|------|-------|------|---------|
| 1 | **Architect** | Opus | Once, before any coding | Reads PRD + build rules. Creates `ARCHITECTURE.md` — file structure, data models, API contracts, component tree. Every coder agent reads this so they all build against the same blueprint. |
| 2 | **Coder** | Sonnet | Per phase | Builds features for that phase. Reads `ARCHITECTURE.md` + build rules + phase-specific spec. This is what the existing phase scripts already do. |
| 3 | **Reviewer** | Opus | After each coder phase | Light check: lint, type check, run tests, quick code scan. Fixes dumb mistakes before the next coder starts. Prevents errors from compounding across phases. |
| 4 | **Verifier** | Opus | Once, after ALL phases | Full post-build verification protocol (Cole Medin). Integration testing, bug hunting, DB validation, edge cases, cross-feature testing. Reads template from `.claude/templates/e2e_verification_prompt.template.md`. |
| 5 | **Cartographer** | Sonnet | Once, after verifier | Creates/updates codebase documentation — `ARCHITECTURE.md`, `CONVENTIONS.md`, dependency map. This is the "memory" that makes future edits faster because agents don't have to re-read everything. |

### Why This Order

- **Architect FIRST** — Without this, every coder agent independently invents the file structure, API shapes, and naming conventions. That's exactly why we had 23 integration bugs in the Tool Factory build — 4 agents disagreed on the API contract. One Architect deciding the structure upfront prevents this.
- **Reviewer after EACH coder** — Catches lint errors, type errors, and obvious bugs early. If Phase 2 introduces a bug, the reviewer fixes it before Phase 3 builds on top of it. Without this, bugs compound and the final verifier finds a pile of 20+ issues instead of 3-4.
- **Verifier at the END** — Cross-phase integration testing. This is the only place you can catch bugs like "frontend calls endpoint X but backend named it Y" because both sides need to exist first. Uses Opus because it needs deep reasoning.
- **Cartographer LAST** — Documents what was actually built (not what was planned). This becomes the starting context for any future agent that touches this codebase. Massive time saver for maintenance and feature additions.

### The Generated Script Flow

```
architect.sh          ← Opus creates ARCHITECTURE.md
    ↓
phase1_build.sh       ← Sonnet codes Phase 1
phase1_review.sh      ← Opus reviews Phase 1
    ↓
phase2_build.sh       ← Sonnet codes Phase 2
phase2_review.sh      ← Opus reviews Phase 2
    ↓
phase3_build.sh       ← Sonnet codes Phase 3
phase3_review.sh      ← Opus reviews Phase 3
    ↓
verify.sh             ← Opus runs full verification protocol
    ↓
cartographer.sh       ← Sonnet documents the codebase
    ↓
run_all.sh            ← Master script chains everything
```

---

## ARCHITECTURE CONTEXT

### What Exists
- `ui/src/pages/BuildPlannerPage.tsx` — The Build Planner form (1089 lines)
- `server/routers/build_planner.py` — Backend with `/generate` and `/generate-all` endpoints
- `.claude/templates/e2e_verification_prompt.template.md` — Cole Medin verification protocol
- The Build Planner already has: Project Basics, Build Rules, Features, Build Settings, Phase Assignments, Generate section

### What We're Adding
- A new **"Agent Roles"** section in the Build Planner form (between Build Settings and Phase Assignments)
- Updated script generation logic that produces all 5 role scripts
- The roles are **configurable, not hardcoded** — user can edit prompts, change models, toggle roles on/off

### Tech Stack (same as Build Planner)
| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.11+ |
| AI Calls | Claude CLI subprocess (`claude -p --model {model}`) |

---

## PHASE 1: Agent Roles Section in UI [ROBOT]

### Task
Add an "Agent Roles" section to the Build Planner form. This shows the 5 roles as configurable cards.

### UI Design

Add a new `SectionCard` between Build Settings and Phase Assignments:

```tsx
{/* Section: Agent Roles */}
<SectionCard
  icon={<Users size={18} className="text-orange-400" />}
  title="Agent Roles"
>
  <p className="text-sm text-zinc-500 mb-4">
    Each build uses specialized agents. Toggle roles on/off and customize their prompts.
    The pipeline runs in order: Architect → Coder (per phase) → Reviewer (per phase) → Verifier → Cartographer.
  </p>

  {agentRoles.map((role, i) => (
    <AgentRoleCard key={role.id} role={role} onUpdate={...} />
  ))}
</SectionCard>
```

### Agent Role Card Component

Each role is a collapsible card showing:
- **Toggle** (on/off) — left side
- **Role name** — e.g., "Architect"
- **Model badge** — e.g., "Opus" in purple, "Sonnet" in cyan
- **One-line description** — what this role does
- **Expandable prompt area** — click to expand and edit the role's prompt template
- **Model dropdown** — change which model this role uses

### State Shape

```typescript
interface AgentRole {
  id: string           // 'architect' | 'coder' | 'reviewer' | 'verifier' | 'cartographer'
  name: string         // Display name
  model: string        // 'opus' | 'sonnet' | 'haiku'
  enabled: boolean     // Toggle on/off
  prompt: string       // The prompt template (editable)
  description: string  // One-line tooltip
  runsWhen: string     // 'once_before' | 'per_phase' | 'per_phase_after' | 'once_after' | 'once_final'
}
```

### Default Roles (pre-populated)

```typescript
const DEFAULT_AGENT_ROLES: AgentRole[] = [
  {
    id: 'architect',
    name: 'Architect',
    model: 'opus',
    enabled: true,
    runsWhen: 'once_before',
    description: 'Creates ARCHITECTURE.md before coding starts — file structure, API contracts, data models',
    prompt: `You are a senior software architect. Read the PRD and build rules below, then create ARCHITECTURE.md in the project root.

ARCHITECTURE.md must contain:
1. **File Structure** — every file that will be created, organized by directory
2. **Data Models** — every database table/model with fields and types
3. **API Contracts** — every endpoint with method, path, request body, response body
4. **Component Tree** — every React component with props and parent-child relationships
5. **Shared Constants** — enums, config values, type names that multiple files reference
6. **Naming Conventions** — how files, functions, variables, and endpoints are named

This document is the single source of truth. Every coding agent will read it before writing code. If two agents disagree, ARCHITECTURE.md wins.

Be exhaustive. Every file. Every endpoint. Every type. No ambiguity.

{build_rules}

{prd_content}`,
  },
  {
    id: 'coder',
    name: 'Coder',
    model: 'sonnet',
    enabled: true,
    runsWhen: 'per_phase',
    description: 'Implements features for each phase — reads ARCHITECTURE.md to stay aligned',
    prompt: `You are building Phase {phase_number} of {total_phases}.

FIRST: Read ARCHITECTURE.md in the project root. Follow its file structure, API contracts, data models, and naming conventions EXACTLY. Do not deviate.

{build_rules}

{phase_spec}

BEFORE YOU FINISH:
1. Run ruff check on all Python files you created/modified
2. Run npm run build in ui/ to verify TypeScript compiles
3. Run npm run lint in ui/ to verify ESLint passes
4. Run any tests you wrote — all must pass
5. Fix any failures before committing
6. Commit your work with a descriptive message`,
  },
  {
    id: 'reviewer',
    name: 'Reviewer',
    model: 'opus',
    enabled: true,
    runsWhen: 'per_phase_after',
    description: 'Reviews code after each phase — catches bugs before the next phase starts',
    prompt: `You are a code reviewer. Phase {phase_number} of {total_phases} was just completed.

Review ALL code written in this phase:
1. Run ruff check on all Python files
2. Run npm run build to check TypeScript
3. Run npm run lint for ESLint
4. Run all tests
5. Read every new/modified file and check for:
   - Logic errors, missing null checks, off-by-one
   - Missing error handling (try/catch, error states)
   - Integration mismatches with ARCHITECTURE.md (wrong endpoint names, wrong request/response shapes)
   - Security issues (path traversal, injection, missing auth)
   - Unused imports, dead code

Fix any Critical or High issues you find. Commit fixes with message: "review(phase-{phase_number}): [description]"

Do NOT refactor working code for style. Only fix actual bugs and issues.`,
  },
  {
    id: 'verifier',
    name: 'Verifier',
    model: 'opus',
    enabled: true,
    runsWhen: 'once_after',
    description: 'Full post-build verification protocol — integration testing, bug hunting, edge cases',
    prompt: `{verification_template}`,
    // Note: This reads from .claude/templates/e2e_verification_prompt.template.md at generation time.
    // The {verification_template} placeholder gets replaced with the file contents.
    // If the file doesn't exist, falls back to a basic verification prompt.
  },
  {
    id: 'cartographer',
    name: 'Cartographer',
    model: 'sonnet',
    enabled: true,
    runsWhen: 'once_final',
    description: 'Documents the codebase after build — creates the map for future agents',
    prompt: `You are a technical documentation specialist. The build is complete and verified. Your job is to create comprehensive codebase documentation so that any future agent can understand this project without reading every file.

Create or update these files in the project root:

1. **ARCHITECTURE.md** — Update the architect's original plan with what was ACTUALLY built (may differ from plan). Include:
   - Final file structure with line counts
   - All API endpoints with real request/response examples
   - Database schema as-built
   - Component hierarchy as-built
   - Key design decisions and why they were made

2. **CONVENTIONS.md** — Document the patterns used in this codebase:
   - Naming patterns (files, functions, variables, CSS classes)
   - Import patterns
   - Error handling patterns
   - State management patterns
   - Testing patterns

3. **CLAUDE.md** — If it doesn't exist, create it. If it exists, add a section called "## Codebase Map" with:
   - One-paragraph project summary
   - Key directories and what they contain
   - How to run the project (install, dev server, tests)
   - Common gotchas and things to watch out for

Read every source file to build accurate documentation. Do NOT guess or copy from the PRD — document what's actually in the code.`,
  },
]
```

### Test Plan
1. [ROBOT] Agent Roles section renders with 5 default roles
2. [ROBOT] Each role can be toggled on/off
3. [ROBOT] Each role's prompt can be expanded and edited
4. [ROBOT] Model dropdown changes the model for each role
5. [ROBOT] `npm run build` — clean
6. [ROBOT] `npm run lint` — clean

---

## PHASE 2: Script Generation with Roles [ROBOT + AGENT]

### Task
Update the script generation logic so that when "Generate All" runs and scripts are saved to disk, it generates the full 5-role pipeline.

### Script Generation Logic

The backend's `/generate-all` endpoint (or a new `/generate-scripts` endpoint) should:

1. Read the form data: project basics, build rules, features, build settings, phase assignments, **agent roles**
2. For each enabled role, generate the appropriate script(s):

```python
scripts = []

# 1. Architect (if enabled)
if roles['architect'].enabled:
    scripts.append({
        'filename': 'architect.sh',
        'content': generate_architect_script(roles['architect'], build_rules, prd),
    })

# 2-3. Coder + Reviewer per phase
for i, phase in enumerate(phases, 1):
    scripts.append({
        'filename': f'phase{i}_build.sh',
        'content': generate_coder_script(roles['coder'], build_rules, phase, i, len(phases)),
    })
    if roles['reviewer'].enabled:
        scripts.append({
            'filename': f'phase{i}_review.sh',
            'content': generate_reviewer_script(roles['reviewer'], i, len(phases)),
        })

# 4. Verifier (if enabled)
if roles['verifier'].enabled:
    scripts.append({
        'filename': 'verify.sh',
        'content': generate_verifier_script(roles['verifier']),
    })

# 5. Cartographer (if enabled)
if roles['cartographer'].enabled:
    scripts.append({
        'filename': 'cartographer.sh',
        'content': generate_cartographer_script(roles['cartographer']),
    })

# Master script
scripts.append({
    'filename': 'run_all.sh',
    'content': generate_master_script(scripts),
})
```

### Script Template

Each role script follows this template:

```bash
#!/bin/bash
# ===========================================
# {ROLE_NAME} — {description}
# Model: {model}
# ===========================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "=== {ROLE_NAME}: {description} ==="
echo "Model: {model}"
echo ""

claude -p --model {model} --dangerously-skip-permissions "{assembled_prompt}"

echo ""
echo "=== {ROLE_NAME} complete ==="
```

### Master Script (`run_all.sh`)

```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL_STEPS={count}
CURRENT=0

echo "=========================================="
echo "  BUILD PIPELINE — {project_name}"
echo "  {count} steps ({phases} phases + roles)"
echo "=========================================="

# Architect
if [ -f "$SCRIPT_DIR/architect.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Architect..."
  bash "$SCRIPT_DIR/architect.sh"
  echo ">>> Architect complete"
fi

# Phase loop (build + review)
for i in $(seq 1 {phases}); do
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Phase $i — Build..."
  bash "$SCRIPT_DIR/phase${i}_build.sh"

  if [ -f "$SCRIPT_DIR/phase${i}_review.sh" ]; then
    CURRENT=$((CURRENT + 1))
    echo ">>> [$CURRENT/$TOTAL_STEPS] Phase $i — Review..."
    bash "$SCRIPT_DIR/phase${i}_review.sh"
  fi
done

# Verifier
if [ -f "$SCRIPT_DIR/verify.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Post-Build Verification..."
  bash "$SCRIPT_DIR/verify.sh"
fi

# Cartographer
if [ -f "$SCRIPT_DIR/cartographer.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Documenting codebase..."
  bash "$SCRIPT_DIR/cartographer.sh"
fi

echo ""
echo "=========================================="
echo "  BUILD COMPLETE"
echo "  All $TOTAL_STEPS steps finished"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. git log --oneline -10    # Check all commits"
echo "  2. git push origin main     # Push to remote"
echo "  3. Deploy to production     # Your deploy process"
```

### Test Plan
1. [ROBOT] Generate scripts with all 5 roles enabled — verify all .sh files are created
2. [ROBOT] Generate scripts with Reviewer disabled — verify no `phase*_review.sh` files
3. [ROBOT] Generate scripts with Architect disabled — verify no `architect.sh`
4. [ROBOT] Verify `run_all.sh` only references scripts that exist
5. [ROBOT] Verify all .sh files have execute permission
6. [ROBOT] Verify the assembled prompts contain the build rules and phase specs
7. [ROBOT] `npm run build` — clean
8. [ROBOT] `ruff check` — clean

---

## IMPORTANT IMPLEMENTATION NOTES

### Don't Hardcode — Keep It Flexible
- Agent roles are stored in React state, not in a config file
- The default roles are just starting values — user can edit everything
- When the user edits a role's prompt, that edit is used for script generation
- Model selection per role is a dropdown, not hardcoded
- Future: save role configurations as presets (v2 feature, not in this brief)

### Prompt Template Variables
These placeholders get replaced during script generation:
- `{build_rules}` — the combined build rules from the form
- `{prd_content}` — the PRD text
- `{phase_spec}` — the specific phase's content from Phase Assignments
- `{phase_number}` — current phase number (1, 2, 3...)
- `{total_phases}` — total number of phases
- `{verification_template}` — contents of `.claude/templates/e2e_verification_prompt.template.md`

### The Verifier's Special Case
The Verifier role's prompt is special — it reads from a template file at generation time, NOT from the form's prompt field. This is because:
1. The verification protocol is 1000+ words — too long for a textarea
2. The user updates it separately (from mentors, new techniques)
3. The form shows a note: "Reads from .claude/templates/e2e_verification_prompt.template.md"
4. The user CAN override by typing a custom prompt in the textarea

### The `--continue` Flag Consideration
Claude CLI's `--continue` flag lets the reviewer pick up where the coder left off (same context window). This is more efficient than a fresh session because the reviewer already knows what was built. The master script can use this:

```bash
# phase1_build.sh runs, then:
# phase1_review.sh uses --continue to keep the context
claude --continue -p --model opus "Now review everything you just built..."
```

However, `--continue` may not work between separate script invocations. If it doesn't, the reviewer just reads the files (which is fine — that's what the Tool Factory verifier did successfully). The scripts should TRY `--continue` but fall back to fresh session.

---

## COMMIT MESSAGE
```
feat(build-planner): add 5-role agent pipeline to script generation

- Architect (Opus): creates ARCHITECTURE.md before coding
- Coder (Sonnet): builds features per phase, reads architecture doc
- Reviewer (Opus): checks code after each phase, fixes bugs early
- Verifier (Opus): full post-build verification protocol
- Cartographer (Sonnet): documents codebase for future agents

All roles configurable in the Build Planner form:
- Toggle each role on/off
- Change model per role (Opus/Sonnet/Haiku)
- Edit each role's prompt template
- Verification reads from .claude/templates/ (user-updatable)

Script generation produces: architect.sh, phaseN_build.sh,
phaseN_review.sh, verify.sh, cartographer.sh, run_all.sh
```

---

## WHAT'S NOT IN SCOPE
- Saving role configurations as presets (v2)
- Parallel execution of phases (v2 — needs dependency analysis)
- Live dashboard showing which role is running (v2)
- Custom roles beyond the 5 defaults (v2)
- The `--continue` flag optimization (nice-to-have, test manually first)
