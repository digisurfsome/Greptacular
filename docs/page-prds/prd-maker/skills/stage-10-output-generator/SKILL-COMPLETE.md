---
name: stage-10-output-generator
description: Render Stages 0-9 output into deliverable build package — phase files, build.sh, CLAUDE.md, BUILD_RULES.md, and README.md.
---

## Purpose

Serialize all decisions from Stages 0-9 into a copy-paste-ready file package that a coding agent or human developer can execute without asking any questions. This stage is pure rendering — zero design decisions, zero open questions. Every ambiguity was resolved upstream.

## When to Use

Activate when the context packet contains completed data from stages 0, 3, 4, 5, 6, 7, 8, and 9. Trigger phrases: "output generator", "render build files", "serialize phase documents", "generate phase files", "produce output package". This skill PRODUCES a deliverable file package: `phases/phase-N.md` files + `build.sh` + `CLAUDE.md` + `BUILD_RULES.md` + `README.md`.

## Input Format

```json
{
  "stage_0": { "platform_profile": {...}, "tech_stack": {...}, "command_allowlist": [...] },
  "stage_3": { "concept_and_context": {...}, "drift_anchor": "string" },
  "stage_4": { "mechanisms": [...], "mechanism_dependencies": [...] },
  "stage_5": { "mechanism_blueprints": [...], "build_rules_applied": [...] },
  "stage_6": { "sub_6a": {...}, "sub_6b": {...}, "sub_6c": {...} },
  "stage_7": { "phases": [...], "token_budget": {...}, "mandatory_build_order": [...] },
  "stage_8": { "instrumented_phases": [...], "total_overhead_tokens": 0, "budget_verified": true },
  "stage_9": {
    "verifier_config": {
      "approach": "automated | manual",
      "verifier_prompt": "string",
      "verifier_inputs": ["string"],
      "verifier_token_budget": 10000,
      "retry_config": { "max_retries": 2, "retry_action": "string", "escalation_action": "string" },
      "persistent_verifier": true
    },
    "checker_builder_consistency": true,
    "verification_overhead_total": 40000,
    "verification_mode": "automated_agent_b | manual_preamble_merge",
    "two_strike_rule": {...}, "verification_protocol": {...},
    "per_phase_checker_config": [...], "agent_b_config": {...}
  },
  "metadata": { "app_type": "string", "archetype_matches": [...], "confidence_scores": {...} }
}
```

## Process

### Step 1: Build Output Manifest

Enumerate every file to generate. For each, record `file_path`, `file_type`, and `estimated_tokens`:

- `phases/phase-N.md` (one per phase from `stage_7.phases`) — type: `"phase"`, tokens: `stage_7.phases[N].estimated_content_tokens` + `stage_8.instrumented_phases[N].overhead_tokens`
- `build.sh` — type: `"build_script"`, tokens: ~2,000
- `CLAUDE.md` — type: `"claude_md"`, tokens: ~3,000 (must stay under 500 lines)
- `BUILD_RULES.md` — type: `"build_rules"`, tokens: ~8,000
- `README.md` — type: `"readme"`, tokens: ~1,500

### Step 2: Render Phase Files

For each phase in `stage_8.instrumented_phases`, compile a standalone `phase-N.md` with exactly 9 sections in order. Use the template in `references/phase-file-template.md`. Each section's source:

1. **Build Rules Preamble** (~8K tokens): From `stage_5.build_rules_applied` + `stage_3.drift_anchor`. Distribute Martin's rules as architecture principles — NEVER as a standalone "Martin's Rules" block.
2. **File Sandbox Declaration** (~2K tokens): From `stage_7.phases[N].file_sandbox.allowed`, `.read_only`, `.forbidden`.
3. **Build Order with Pulse Points** (~3K tokens): From `stage_7.mandatory_build_order` + `stage_8.instrumented_phases[N].pulse_points`.
4. **Seam Check Definitions** (~2K tokens): From `stage_8.instrumented_phases[N].seam_checks`.
5. **Objective and Feature Requirements**: From `stage_7.phases[N].features` cross-referenced with `stage_4.mechanisms` and `stage_6.sub_6b`.
6. **Pattern References**: From `stage_5.mechanism_blueprints` — file:line references for patterns to follow, informed by Wall/Door/Room classifications.
7. **Violation Handling Instructions** (~2K tokens): From `stage_8.instrumented_phases[N].violation_handling`. Decision tree: low (log+continue), medium (fix first), high (rollback to pulse), critical (stop+human).
8. **Full Checkpoint at End** (~5K tokens): From `stage_8.instrumented_phases[N].full_checkpoint`. 4-step check: self-report, diff check, violation response, functional verification.
9. **Gate Condition**: "ALL FOUR STEPS MUST PASS BEFORE PHASE [N+1] BEGINS" (or "PIPELINE COMPLETE" for last phase).

**Critical**: Each phase file MUST be self-contained — executable in a fresh agent context without cross-file references (except READ-ONLY codebase files).

### Step 3: Generate build.sh

Create the deterministic bash wrapper using the template in `references/build-sh-template.md`:

- `set -e` — stop on ANY error
- Per-phase block: git snapshot (`SNAPSHOT=$(git rev-parse HEAD)`), pre-build validation, agent work marker, post-build validation, forbidden file detection via `git diff --name-only $SNAPSHOT`, commit
- Phase chaining with `&&` (NEVER `;`)
- Two-strike retry from `stage_9.two_strike_rule`: fail → rollback → retry with fresh agent → second fail → stop for human
- Platform-adaptive commands from `stage_0.tech_stack` (build, lint, test commands)
- Forbidden file detection: `git diff --name-only $SNAPSHOT | grep -E "forbidden_pattern"` built from each phase's `file_sandbox.forbidden`

Set `build_script_config`:
```json
{
  "snapshot_enabled": true,
  "rollback_enabled": true,
  "forbidden_file_detection": true,
  "two_strike_retry": true,
  "chaining_operator": "&&"
}
```

### Step 4: Generate CLAUDE.md

Create quick-reference guardrails file using `references/claude-md-template.md`. MUST be under 500 lines. Contents:

- **Architecture Principles**: Distilled from `stage_5.mechanism_blueprints` and `stage_5.build_rules_applied`. Single-responsibility, state placement, file size limits, import direction.
- **Modification Rules**: Read before edit, don't refactor uninstructed, match existing style.
- **Testing Protocol**: Compile check, render check, regression check.
- **File Structure Map**: Generated from `stage_6.sub_6a` (page arrangement) and `stage_7.phases` (file sandboxes).
- **Pointers to BUILD_RULES.md**: Section references for debugging, feature addition, code review protocols.

CLAUDE.md is distilled. BUILD_RULES.md has depth. They never contradict.

### Step 5: Generate BUILD_RULES.md

Create detailed reference playbook using `references/build-rules-sections.md`. Map Martin's modules to sections adapted for `stage_0.tech_stack`:

| Martin Module | BUILD_RULES.md Section |
|---------------|----------------------|
| 08 (Bug Fix) | "Debugging Protocol" |
| 09 (Feature Add) | "Feature Addition Protocol" |
| 10 (Debug) | "Trace-First Debugging" |
| 13 (Testing) | "Testing & Verification" |
| 03 (Data Layer) | "Data Access Patterns" |
| 05 (CRUD Flow) | "Entity CRUD Pattern" |

Other modules (01 Scaffold, 02 Auth, 04 UI Kit, 06 Polish, 07 Style, 11 Clean Room, 12 PRD Generator) are handled by phase files or the UI style system — no separate sections needed.

### Step 6: Generate README.md

Document the build package:

- Product name + description (from `stage_3.concept_and_context`)
- Tech stack (from `stage_0.tech_stack`)
- How to run the build (platform-specific from `platform_target`)
- Phase overview (what each phase builds, from `stage_7.phases`)
- How to add features post-build (pointer to BUILD_RULES.md)

### Step 7: Platform Picker Rendering

Set `platform_target` based on user's chosen platform. Adapt wrapper instructions per `references/platform-wrappers.md`:

| Platform | Method | Automation |
|----------|--------|-----------|
| `claude_cli` | `bash build.sh` | Fully automatic |
| `claude_web` | Copy-paste `phase-N.md` | Manual |
| `codex_cli` / `gemini_cli` | Platform CLI commands | Fully automatic |
| `cursor` / `windsurf` | Terminal, semi-auto | Semi-automatic |
| `bolt` / `lovable` | No terminal | Manual export |
| `generic` | Copy-paste anywhere | Fully manual |

Phase file CONTENT is identical across platforms. Only execution wrapper changes.

### Step 8: Internal Consistency Verification

Before writing output, verify ALL of the following:

1. Every file path in every sandbox declaration exists in a build order
2. Every mechanism in `stage_4.mechanisms` appears in at least one phase
3. Every page in `stage_6.sub_6b` appears in at least one phase
4. Every import/pattern reference points to a file that gets created or exists as READ-ONLY
5. `open_questions_count` == 0 (scan all feature requirements for question marks or TBD markers)
6. Every phase's total tokens (content + overhead) fits within budget
7. No phase file references content from another phase file (self-containment check)

Write results to `final_validation`. If ANY check fails, attempt auto-fix (reorder, reassign). If unfixable, trigger escape hatch.

## Output Format

```json
{
  "stage_10": {
    "output_manifest": [
      { "file_path": "phases/phase-1.md", "file_type": "phase", "estimated_tokens": 45000 }
    ],
    "generated_files": {
      "phases/phase-1.md": "full markdown content...",
      "build.sh": "#!/bin/bash\nset -e\n...",
      "CLAUDE.md": "# Build Rules\n...",
      "BUILD_RULES.md": "# Build Rules Reference\n...",
      "README.md": "# Product Name\n..."
    },
    "build_script_config": {
      "snapshot_enabled": true,
      "rollback_enabled": true,
      "forbidden_file_detection": true,
      "two_strike_retry": true,
      "chaining_operator": "&&"
    },
    "platform_target": "claude_cli",
    "claude_md_content": "string (under 500 lines)",
    "build_rules_content": "string",
    "final_validation": {
      "open_questions_count": 0,
      "all_phases_fit_budget": true,
      "all_mechanisms_covered": true,
      "all_pages_covered": true
    }
  }
}
```

Metadata updates:
```json
{
  "metadata.current_stage": 10,
  "metadata.status": "completed",
  "metadata.confidence_scores.10": { "score": 0, "dimensions": {...}, "gate_result": "pass" },
  "metadata.stage_timestamps.10": "ISO-8601",
  "metadata.updated_at": "ISO-8601"
}
```

## Edge Cases

### Missing Input

| Missing Field | Action |
|---------------|--------|
| `stage_7.phases` is null or empty | FAIL — escape hatch. No phases = no output. |
| `stage_8.instrumented_phases` missing | FAIL — escape hatch. Cannot render phase files without protocols. |
| `stage_9` missing entirely | WARN — generate build.sh without verification/retry. Flag in confidence (Completeness -10). |
| `stage_0.tech_stack` missing | WARN — default to Node/npm. Flag in confidence (Accuracy -5). |
| `stage_5.build_rules_applied` empty | Generate minimal preamble from universal rules only. Flag in confidence (Specificity -5). |

### Ambiguous Input

| Ambiguity | Resolution |
|-----------|------------|
| Mechanism assigned to no phase | FAIL — triggers consistency check failure. Escape hatch with suggestion to re-run Stage 7. |
| Page in `stage_6.sub_6b` has no phase | FAIL — triggers consistency check failure. Escape hatch with suggestion to re-run Stage 7. |
| Token budget exceeded for a phase | Attempt split: move last feature to next phase. If still over, escape hatch. |
| Platform is `bolt`/`lovable` (no terminal) | Generate build.sh anyway for documentation, but set primary wrapper to manual copy-paste. |

### Scope Overflow

| Discovery | Action |
|-----------|--------|
| Feature requirement contains open question (TBD, "to be decided") | Do NOT render. Set `open_questions_count` > 0. Escape hatch with pointer to originating stage. |
| Phase spec needs design changes to be renderable | Do NOT redesign. Flag as `NEEDS_HUMAN`: "Phase N requires restructuring — re-run Stage 7 with constraint X." |
| Missing pattern reference (file doesn't exist yet) | Check if another phase creates it. If yes, mark as cross-phase dependency (allowed as READ-ONLY in later phase). If no, flag. |

## Confidence Scoring

Score each dimension 0-20 after producing output:

1. **Completeness**: All files in manifest generated? Every phase file has all 9 sections? build.sh has verification + retry? CLAUDE.md + BUILD_RULES.md present and populated? No skeletal sections?

2. **Accuracy**: Every reference resolves? build.sh commands valid for platform? CLAUDE.md rules match project architecture? Zero dangling references to nonexistent files/mechanisms/patterns?

3. **Consistency**: Phase sandbox rules respected across phases? build.sh verification matches phase checkpoints? CLAUDE.md and BUILD_RULES.md complement without contradiction? No phase modifies files another phase forbids?

4. **Specificity**: Phase requirements specify exact file paths, exports, patterns? Not vague ("build the auth system")? build.sh uses real paths and commands?

5. **Handoff Readiness**: Can a coding agent execute ALL phases without asking a single question? The output package IS the complete instruction set. If any question would need to be asked, score < 16.

**Total /100: >= 90 PASS (deliver) | 70-89 WARN (deliver with warning) | < 70 FAIL (escape hatch)**

## Escape Hatch

**Trigger when:**
- Required input namespace missing (`stage_7`, `stage_8` null)
- `stage_7.phases` is empty
- Open question detected in any feature requirement
- Mechanism from `stage_4` has no phase assignment
- Page from `stage_6.sub_6b` has no phase assignment
- Token budget exceeded for any phase after attempted rebalance
- Internal consistency check fails (dangling references)
- Confidence score < 70 after one retry

**Save:** Current `context_packet` with partial `stage_10` output, stage number (10), step where halt occurred, list of specific validation failures, partial `generated_files`.

**Signal:**
```json
{
  "metadata.status": "needs_human",
  "metadata.escape_hatches": [{
    "stage": 10,
    "step": "step_name",
    "reason": "description",
    "details": { "uncovered_mechanisms": [], "dangling_refs": [], "budget_overflow": [] },
    "suggested_actions": ["Re-run Stage 7 with constraint X", "Resolve open question in Stage Y"]
  }]
}
```

## Example

**Input** (abbreviated):
```json
{
  "stage_0": { "tech_stack": { "framework": "react", "database": "supabase", "build_command": "npm run build", "lint_command": "npm run lint" } },
  "stage_3": { "concept_and_context": { "name": "TaskFlow", "description": "Team task management app" }, "drift_anchor": "Task management for small teams" },
  "stage_7": { "phases": [{ "phase_number": 1, "features": ["auth", "db-setup"], "file_sandbox": { "allowed": ["src/lib/supabase.ts"] } }, { "phase_number": 2, "features": ["task-board"], "file_sandbox": { "allowed": ["src/components/Board.tsx"] } }], "token_budget": { "budget_per_phase_content": 325000 } }
}
```

**Output** (abbreviated):
```json
{
  "stage_10": {
    "output_manifest": [
      { "file_path": "phases/phase-1.md", "file_type": "phase", "estimated_tokens": 45000 },
      { "file_path": "phases/phase-2.md", "file_type": "phase", "estimated_tokens": 50000 },
      { "file_path": "build.sh", "file_type": "build_script", "estimated_tokens": 2000 },
      { "file_path": "CLAUDE.md", "file_type": "claude_md", "estimated_tokens": 3000 },
      { "file_path": "BUILD_RULES.md", "file_type": "build_rules", "estimated_tokens": 8000 },
      { "file_path": "README.md", "file_type": "readme", "estimated_tokens": 1500 }
    ],
    "generated_files": {
      "phases/phase-1.md": "# Phase 1: Foundation\n\n## Build Rules Preamble\n...[9 sections]...\n## Gate Condition\nALL FOUR STEPS MUST PASS BEFORE PHASE 2 BEGINS",
      "phases/phase-2.md": "# Phase 2: Task Board\n...[9 sections]...\n## Gate Condition\nPIPELINE COMPLETE",
      "build.sh": "#!/bin/bash\nset -e\n\nrun_phase() {\n  SNAPSHOT=$(git rev-parse HEAD)\n  npm run build || { echo 'ABORT'; exit 1; }\n  # ... agent work ...\n  npm run build && npm run lint || { git reset --hard $SNAPSHOT; exit 1; }\n}\n\nrun_phase 1 && run_phase 2",
      "CLAUDE.md": "# Build Rules\n## Architecture Principles\n- Components do ONE thing...",
      "BUILD_RULES.md": "# Build Rules Reference\n## Debugging Protocol\n...",
      "README.md": "# TaskFlow\nTeam task management app..."
    },
    "build_script_config": { "snapshot_enabled": true, "rollback_enabled": true, "forbidden_file_detection": true, "two_strike_retry": true, "chaining_operator": "&&" },
    "platform_target": "claude_cli",
    "claude_md_content": "# Build Rules\n...",
    "build_rules_content": "# Build Rules Reference\n...",
    "final_validation": { "open_questions_count": 0, "all_phases_fit_budget": true, "all_mechanisms_covered": true, "all_pages_covered": true }
  }
}
```

The output contains ONLY the structured file package. No conversational text. Each phase file is independently consumable. The build.sh chains them with `&&` and includes two-strike retry.


---
## REFERENCE: build-rules-sections

# BUILD_RULES.md — Section Templates

> Detailed reference playbook. Lives alongside CLAUDE.md in repo root.
> CLAUDE.md points to specific sections here for deeper protocols.
> Derived from Martin's 13 modules, adapted to the user's tech stack.

---

## Section Map

| Section | Source Module | Purpose |
|---------|-------------|---------|
| Debugging Protocol | Martin Module 08 (Bug Fix) | Step-by-step bug fixing methodology |
| Trace-First Debugging | Martin Module 10 (Debug) | Deep debugging with tracing |
| Feature Addition Protocol | Martin Module 09 (Feature Add) | How to add features safely |
| Testing & Verification | Martin Module 13 (Testing) | Testing standards and checklist |
| Data Access Patterns | Martin Module 03 (Data Layer) | Database and data layer conventions |
| Entity CRUD Pattern | Martin Module 05 (CRUD Flow) | Standard CRUD implementation pattern |

---

## Section Templates

### Debugging Protocol

```markdown
## Debugging Protocol

When you encounter a bug, follow this sequence. Do NOT skip steps.

### 1. Reproduce
- Identify the exact steps that trigger the bug
- Note the expected vs actual behavior
- Check if the bug is consistent or intermittent

### 2. Read the Error
- Read the FULL error message and stack trace
- Identify the file and line number
- Note any relevant variable values

### 3. Trace the Path
- Start at the error location
- Trace backwards through the call stack
- Identify where the data becomes incorrect
- Map the flow: {source} → {transform} → {destination} → {error}

### 4. Isolate
- Determine the smallest change that causes the bug
- Check: is this a data problem, logic problem, or timing problem?
- Check recent changes: `git log --oneline -10`

### 5. Fix
- Fix the ROOT CAUSE, not the symptom
- Make the minimal change needed
- Don't refactor while fixing — that's a separate task

### 6. Verify
```bash
# Run build
{build_command}

# Run tests
{test_command}

# Verify the specific bug is fixed
{manual_verification_step}

# Verify nothing else broke
{lint_command}
```

### 7. Document
- If the bug was non-obvious, add a comment explaining WHY the fix works
- If it could happen again, consider adding a test
```

---

### Trace-First Debugging

```markdown
## Trace-First Debugging

For complex bugs where the Debugging Protocol didn't find the root cause.

### Approach
1. Add logging at EVERY step of the suspected code path
2. Log inputs, outputs, and intermediate values
3. Run the reproduction steps
4. Read the trace from start to finish
5. The bug is where the trace diverges from expectations

### Trace Template
```{language}
// At function entry
console.log('[{function_name}] INPUT:', JSON.stringify({params}));

// At decision points
console.log('[{function_name}] BRANCH:', {condition} ? 'true-path' : 'false-path');

// At function exit
console.log('[{function_name}] OUTPUT:', JSON.stringify({result}));
```

### When to Use
- The bug only appears with specific data
- The error message doesn't point to the real cause
- Multiple components interact and you're unsure which one is wrong
- The bug is timing-related (race condition, async ordering)

### Clean Up
After finding the bug, REMOVE all trace logging before committing.
```

---

### Feature Addition Protocol

```markdown
## Feature Addition Protocol

When adding a new feature, follow this sequence to avoid breaking existing code.

### 1. Understand Context
- Read ALL files that will be affected by the feature
- Identify existing patterns for similar features
- Check if a similar feature already exists (extend it, don't duplicate)

### 2. Plan the Changes
- List every file that needs modification
- List every new file to create
- Identify which existing tests need updating
- Check: does this feature touch any shared/critical files?

### 3. Implement
- Create new files FIRST (types, interfaces, utilities)
- Modify existing files SECOND (add imports, wire up)
- Follow existing patterns — if the codebase uses {pattern}, you use {pattern}
- Keep changes minimal — don't refactor while adding

### 4. Wire Up
- Update route definitions if adding a page
- Update navigation if adding a user-facing feature
- Update exports/imports in index files
- Update types if adding new data shapes

### 5. Verify
```bash
{build_command}
{lint_command}
{test_command}
```

### 6. Self-Check
- [ ] Does the feature match the requirement exactly (no more, no less)?
- [ ] Did I modify only the files that needed changing?
- [ ] Did I follow existing patterns?
- [ ] Did I update all imports and exports?
- [ ] Is error handling present at boundaries?
```

---

### Testing & Verification

```markdown
## Testing & Verification

### After Every Change
```bash
# Compile check — does it build?
{build_command}

# Lint check — does it meet code standards?
{lint_command}

# Test check — do existing tests pass?
{test_command}
```

### When to Write Tests
- New utility functions: ALWAYS
- New API endpoints: ALWAYS
- Complex business logic: ALWAYS
- Simple UI components: ONLY if they have conditional rendering logic
- Configuration changes: NEVER (just verify the build)

### Test Structure
```{language}
describe('{ComponentOrFunction}', () => {
  it('should {expected_behavior} when {condition}', () => {
    // Arrange: set up test data
    // Act: call the function / render the component
    // Assert: verify the expected outcome
  });

  it('should handle {edge_case}', () => {
    // Test the boundary condition
  });

  it('should throw/return error when {invalid_input}', () => {
    // Test error handling
  });
});
```

### Regression Checklist
After any change, manually verify:
- [ ] The changed feature works as expected
- [ ] Adjacent features still work (anything sharing state, routes, or data)
- [ ] No console errors in browser (for UI changes)
- [ ] No new lint warnings
```

---

### Data Access Patterns

```markdown
## Data Access Patterns

### Single Source of Truth
All database access goes through a dedicated data layer.
- {Database access file path from stage_0/stage_7}
- Components NEVER query the database directly
- All queries are typed and return typed results

### Query Pattern
```{language}
// GOOD: centralized, typed, reusable
export async function get{Entity}ById(id: string): Promise<{Entity}> {
  const { data, error } = await {db_client}.from('{table}').select('*').eq('id', id).single();
  if (error) throw new {EntityError}(error.message);
  return data;
}

// BAD: inline query in component
const { data } = await supabase.from('items').select('*');  // NEVER do this
```

### Mutation Pattern
```{language}
export async function create{Entity}(input: Create{Entity}Input): Promise<{Entity}> {
  // Validate input
  // Execute mutation
  // Return typed result
  // Handle errors at this layer
}
```

### Rules
- Every query function returns a typed result
- Error handling happens in the data layer, not the UI
- Queries include only the fields needed (no `select('*')` in production)
- Mutations validate input before executing
```

---

### Entity CRUD Pattern

```markdown
## Entity CRUD Pattern

When building CRUD for any entity, follow this standard pattern.

### File Structure
```
{entity_directory}/
├── {entity}.types.ts     # Types and interfaces
├── {entity}.queries.ts   # Data access (read operations)
├── {entity}.mutations.ts # Data access (write operations)
├── {entity}.list.tsx     # List/table view component
├── {entity}.detail.tsx   # Detail/single view component
├── {entity}.form.tsx     # Create/edit form component
└── {entity}.test.ts      # Tests
```

### Implementation Order
1. Types first — define the entity shape
2. Queries — read operations (list, getById, search)
3. Mutations — write operations (create, update, delete)
4. List view — display all entities
5. Detail view — display single entity
6. Form — create and edit
7. Wire up routes and navigation

### Standard Operations
| Operation | Function | Route |
|-----------|----------|-------|
| List | `get{Entity}List()` | `/{entities}` |
| Detail | `get{Entity}ById(id)` | `/{entities}/:id` |
| Create | `create{Entity}(input)` | `/{entities}/new` |
| Update | `update{Entity}(id, input)` | `/{entities}/:id/edit` |
| Delete | `delete{Entity}(id)` | N/A (action on detail page) |

### Rules
- Always include loading states
- Always include error states
- Always include empty states (no data)
- Delete requires confirmation
- Forms validate before submission
- Optimistic updates where appropriate (list operations)
```

---

## Rendering Rules

1. Replace ALL `{placeholders}` with actual values from `stage_0.tech_stack`
2. Replace `{language}` with the stack's primary language (typescript, python, etc.)
3. Replace `{build_command}`, `{lint_command}`, `{test_command}` with actual commands
4. Replace `{db_client}` with the actual database client name
5. If a section is not applicable to the tech stack (e.g., "Entity CRUD Pattern" for a CLI tool), omit it entirely
6. Martin's name NEVER appears. Rules are presented as project conventions.
7. Keep each section focused — no cross-references between BUILD_RULES.md sections
8. CLAUDE.md references these sections by exact name — section headings must be stable


---
## REFERENCE: build-sh-template

# build.sh Template

> Deterministic bash wrapper that chains phase execution with verification.
> Uses `&&` chaining (NEVER `;`). Failure in any phase stops the pipeline.

---

## Template

```bash
#!/bin/bash
set -e

# ============================================================
# {PRODUCT_NAME} — Automated Build Script
# Generated by PRD Maker Pipeline (Stage 10)
# Platform: {platform_target}
# Phases: {phase_count}
# ============================================================

# --- Configuration ---
BUILD_CMD="{stage_0.tech_stack.build_command}"    # e.g., "npm run build"
LINT_CMD="{stage_0.tech_stack.lint_command}"       # e.g., "npm run lint"
TEST_CMD="{stage_0.tech_stack.test_command}"       # e.g., "npm run test"
PHASE_DIR="./phases"
MAX_RETRIES=2  # Two-strike rule: 2 failures = stop for human

# --- Helper Functions ---

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

take_snapshot() {
  git rev-parse HEAD
}

validate_build() {
  log "Running build validation..."
  $BUILD_CMD || return 1
  $LINT_CMD || return 1
  log "Build validation passed."
}

check_forbidden_files() {
  local SNAPSHOT=$1
  local PHASE_NUM=$2
  local FORBIDDEN_PATTERN=$3

  if [ -z "$FORBIDDEN_PATTERN" ]; then
    return 0
  fi

  FORBIDDEN_CHANGES=$(git diff --name-only "$SNAPSHOT" | grep -E "$FORBIDDEN_PATTERN" || true)
  if [ -n "$FORBIDDEN_CHANGES" ]; then
    log "FAIL: Phase $PHASE_NUM modified forbidden files:"
    echo "$FORBIDDEN_CHANGES"
    return 1
  fi
  return 0
}

run_phase() {
  local PHASE_NUM=$1
  local PHASE_FILE="$PHASE_DIR/phase-${PHASE_NUM}.md"
  local FORBIDDEN_PATTERN=$2  # Regex of forbidden file paths

  if [ ! -f "$PHASE_FILE" ]; then
    log "ERROR: $PHASE_FILE not found"
    exit 1
  fi

  log "=========================================="
  log "PHASE $PHASE_NUM: Starting"
  log "=========================================="

  # --- DETERMINISTIC: Snapshot ---
  local SNAPSHOT
  SNAPSHOT=$(take_snapshot)
  log "Snapshot: $SNAPSHOT"

  # --- DETERMINISTIC: Pre-build validation ---
  validate_build || {
    log "ABORT: Build broken BEFORE phase $PHASE_NUM started"
    exit 1
  }

  # --- AI AGENT: Creative work ---
  log "Phase $PHASE_NUM: Executing agent with $PHASE_FILE"
  # {PLATFORM_SPECIFIC_AGENT_COMMAND}
  # For claude_cli:  claude --print "$PHASE_FILE"
  # For codex_cli:   codex --file "$PHASE_FILE"
  # For gemini_cli:  gemini --file "$PHASE_FILE"
  # For manual:      echo "Paste contents of $PHASE_FILE into your agent"

  # --- DETERMINISTIC: Post-build validation ---
  validate_build || {
    log "FAIL: Build broken after phase $PHASE_NUM"
    git reset --hard "$SNAPSHOT"
    log "Rolled back to $SNAPSHOT"
    return 1
  }

  # --- DETERMINISTIC: Forbidden file detection ---
  check_forbidden_files "$SNAPSHOT" "$PHASE_NUM" "$FORBIDDEN_PATTERN" || {
    git reset --hard "$SNAPSHOT"
    log "Rolled back to $SNAPSHOT due to forbidden file modification"
    return 1
  }

  # --- DETERMINISTIC: Commit ---
  git add -A
  git commit -m "Phase $PHASE_NUM complete"
  log "Phase $PHASE_NUM: PASSED"
}

run_phase_with_retry() {
  local PHASE_NUM=$1
  local FORBIDDEN_PATTERN=$2
  local ATTEMPT=1

  while [ $ATTEMPT -le $MAX_RETRIES ]; do
    log "Phase $PHASE_NUM — Attempt $ATTEMPT of $MAX_RETRIES"

    if run_phase "$PHASE_NUM" "$FORBIDDEN_PATTERN"; then
      return 0
    fi

    log "Phase $PHASE_NUM failed on attempt $ATTEMPT"
    ATTEMPT=$((ATTEMPT + 1))

    if [ $ATTEMPT -le $MAX_RETRIES ]; then
      log "Retrying with fresh agent..."
    fi
  done

  log "============================================"
  log "STOPPED: Phase $PHASE_NUM failed $MAX_RETRIES times."
  log "The problem is likely in the phase spec, not the agent."
  log "Human review required."
  log "============================================"
  exit 1
}

# --- Main Execution ---

log "Starting build: {PRODUCT_NAME}"
log "Phases: {phase_count}"
log "Platform: {platform_target}"

# {PHASE_EXECUTION_BLOCK}
# Generated per phase. Example for 3 phases:

run_phase_with_retry 1 "{phase_1_forbidden_pattern}" && \
run_phase_with_retry 2 "{phase_2_forbidden_pattern}" && \
run_phase_with_retry 3 "{phase_3_forbidden_pattern}"

log "============================================"
log "BUILD COMPLETE: All {phase_count} phases passed."
log "============================================"
```

---

## Rendering Rules

1. Replace `{PRODUCT_NAME}` with `stage_3.concept_and_context.name`
2. Replace `{platform_target}` with the chosen platform enum
3. Replace `{phase_count}` with length of `stage_7.phases`
4. Replace `BUILD_CMD`, `LINT_CMD`, `TEST_CMD` with actual values from `stage_0.tech_stack`
5. Generate one `run_phase_with_retry N "pattern"` call per phase, chained with `&&`
6. Build `FORBIDDEN_PATTERN` per phase from `stage_7.phases[N].file_sandbox.forbidden` as a grep-compatible regex (pipe-separated paths, escaped dots)
7. The agent command inside `run_phase()` is platform-specific — see `platform-wrappers.md` for the correct command per platform
8. `MAX_RETRIES` is always 2 (from `stage_9.two_strike_rule.max_retries`)
9. If `stage_9.verification_mode` is `automated_agent_b`, add Agent B verification call between agent work and commit (see Stage 9 output for the exact command)
10. If platform is `bolt` or `lovable`, replace `run_phase` body with manual instructions (no bash automation available)

## Platform-Specific Agent Commands

| Platform | Command in `run_phase()` |
|----------|-------------------------|
| `claude_cli` | `claude --print "$(cat $PHASE_FILE)"` |
| `codex_cli` | `codex run --prompt-file "$PHASE_FILE"` |
| `gemini_cli` | `gemini code --prompt-file "$PHASE_FILE"` |
| `cursor` | `echo "Open terminal in Cursor, paste contents of $PHASE_FILE"` |
| `windsurf` | `echo "Open terminal in Windsurf, paste contents of $PHASE_FILE"` |
| `bolt` / `lovable` | `echo "Manual: Copy $PHASE_FILE content into platform chat"` |
| `generic` | `echo "Paste contents of $PHASE_FILE into your coding agent"` |


---
## REFERENCE: claude-md-template

# CLAUDE.md Template

> Quick-reference guardrails file. Lives in repo root FOREVER.
> Read by EVERY agent interaction — even "fix this button color."
> MUST be under 500 lines. Tight, fast, actionable.
> Points to BUILD_RULES.md for deeper protocols.

---

## Template

```markdown
# {PRODUCT_NAME}

> {One-line product description from stage_3.concept_and_context}

## Architecture Principles

{Distilled from stage_5.build_rules_applied. 10-15 rules max.}

- Components do ONE thing. If it does two things, split it.
- State lives at the lowest possible level. Don't hoist unless required.
- No file over 300 lines. Split at 250.
- Imports flow downward. Never circular.
- UI components don't contain business logic.
- Every function has a single responsibility.
- Error handling at boundaries, not everywhere.
- {Stack-specific: e.g., "All Supabase queries go through src/lib/db.ts"}
- {Stack-specific: e.g., "Auth state managed exclusively in AuthContext"}
- {Stack-specific: e.g., "Server actions in app/actions/, never in components"}

## Modification Rules

- Before editing ANY file, read it completely first.
- Don't refactor code you didn't write unless explicitly asked.
- Don't add features that weren't requested.
- Don't "improve" working code while fixing a bug.
- Keep existing patterns. Match the style that's there.
- When in doubt, check how similar code is written elsewhere in the project.

## Testing Protocol

After ANY change, verify:

```bash
# 1. Does it compile?
{build_command}

# 2. Does it lint?
{lint_command}

# 3. Do tests pass? (if tests exist)
{test_command}

# 4. Do existing features still work? (manual check for UI changes)
```

Don't delete tests. Don't skip tests. Don't modify tests to make them pass.

## Tech Stack

{From stage_0.tech_stack — concise reference.}

| Layer | Technology |
|-------|-----------|
| Framework | {framework} |
| Language | {language} |
| Database | {database} |
| Auth | {auth_provider} |
| Hosting | {hosting} |
| Styling | {styling} |

## File Structure

{Generated from stage_6.sub_6a (page arrangement) + stage_7.phases (file sandboxes).}

```
{project_root}/
├── src/
│   ├── components/     # UI components ({component_list})
│   ├── lib/            # Shared utilities ({utility_list})
│   ├── contexts/       # State management ({context_list})
│   ├── pages/          # Page components ({page_list})
│   └── types/          # TypeScript types
├── {api_directory}/    # API routes / server functions
├── {db_directory}/     # Database schema / migrations
├── CLAUDE.md           # This file (guardrails)
├── BUILD_RULES.md      # Detailed protocols
└── {config_files}      # Config (DO NOT MODIFY without reason)
```

## Key Files (Don't Break These)

{Critical files that should rarely be modified. From stage_7 sandbox forbidden lists.}

- `{auth_file}` — Authentication setup. Modify ONLY if auth feature is explicitly requested.
- `{db_config_file}` — Database connection. Almost never needs changes.
- `{env_file}` — Environment variables. NEVER commit secrets.
- `{config_files}` — Build config. Change only if build is broken.

## When Debugging

Follow the debugging protocol in BUILD_RULES.md Section "Debugging Protocol."

1. Read the error message completely
2. Find the actual file and line causing the error
3. Trace the data flow from source to error
4. Fix the root cause, not the symptom
5. Verify the fix doesn't break anything else

Do NOT guess at fixes. Trace the actual error path first.

## When Adding Features

Follow the feature addition protocol in BUILD_RULES.md Section "Feature Addition Protocol."

1. Read all connected files before modifying any of them
2. Check if a similar feature already exists (follow its pattern)
3. Create new files for new features — don't bloat existing files
4. Update imports and exports
5. Run the full testing protocol

## When Reviewing Code

Check BUILD_RULES.md Section "Testing & Verification" for the full review checklist.

Quick checks:
- Does it compile and lint?
- Does it match existing patterns?
- Are there any hardcoded values that should be config?
- Is error handling present at boundaries?
- Are there any security concerns (exposed secrets, missing auth checks)?
```

---

## Rendering Rules

1. Replace `{PRODUCT_NAME}` with `stage_3.concept_and_context.name`
2. Replace `{build_command}`, `{lint_command}`, `{test_command}` from `stage_0.tech_stack`
3. Generate "Architecture Principles" from `stage_5.build_rules_applied` — pick the 10-15 most impactful rules, adapted to the tech stack
4. Generate "File Structure" tree from `stage_6.sub_6a` page arrangement and `stage_7.phases` file sandbox declarations — show the actual project structure
5. Generate "Key Files" from the union of all phases' `file_sandbox.forbidden` lists
6. Keep all BUILD_RULES.md section references accurate — section names must match what Step 5 generates
7. Martin's rules are EMBEDDED as architecture principles — NEVER reference "Martin" by name
8. Total output MUST be under 500 lines. If approaching the limit, remove examples rather than removing rules
9. Every bash command must be copy-paste ready (no placeholders in the final output)


---
## REFERENCE: phase-file-template

# Phase File Template — 9-Section Format

> Each `phase-N.md` is a standalone, copy-paste-ready build document.
> A fresh agent receiving ONLY this file can execute the phase without additional context.

---

## Template

```markdown
# Phase {N}: {Phase Title}

> **Product**: {product_name} — {one-line description from stage_3.drift_anchor}
> **Phase**: {N} of {total_phases}
> **Token Budget**: {content_tokens} content + {overhead_tokens} overhead = {total_tokens} total

---

## 1. Build Rules Preamble

{~8,000 tokens. The agent's operating manual for HOW to behave.}

### Architecture Principles

{Derived from stage_5.build_rules_applied. Adapt to stage_0.tech_stack.}

- Components do ONE thing. If it does two things, split it.
- State lives at the lowest possible level. Don't hoist unless required.
- No file over 300 lines. Split at 250.
- Imports flow downward. Never circular.
- UI components don't contain business logic.
- {Stack-specific rules based on stage_0.tech_stack.framework}

### Modification Rules

- Read every file completely before editing it.
- Don't refactor code you didn't write unless explicitly instructed.
- Don't add features that weren't requested in this phase.
- Don't "improve" working code while fixing a bug.
- Match existing patterns. If the codebase uses X, you use X.

### Coding Standards

{From stage_5.build_rules_applied — stack-specific.}

- {Language-specific rules: TypeScript strict mode, Python type hints, etc.}
- {Import ordering convention}
- {Error handling convention}
- {Naming conventions}

### Product Context

{From stage_3.drift_anchor — keeps agent centered on the original vision.}

This phase is part of building **{product_name}**: {drift_anchor_text}.
Do NOT drift from this vision. If a feature seems to contradict the product
concept, flag it rather than improvising.

---

## 2. File Sandbox Declaration

{~2,000 tokens. Three explicit lists.}

### Files You CAN Modify (Create or Edit)

{From stage_7.phases[N].file_sandbox.allowed}

```
{file_path_1}
{file_path_2}
...
```

### Files You CAN Read (But NOT Modify)

{From stage_7.phases[N].file_sandbox.read_only}

```
{file_path_1}
{file_path_2}
...
```

### Files You CANNOT Touch

{From stage_7.phases[N].file_sandbox.forbidden}

```
{file_path_1}
{file_path_2}
...
```

**Rule**: If `git diff` at the end shows ANY file not in the "CAN Modify" list
was changed, the phase FAILS verification.

---

## 3. Build Order with Pulse Points

{~3,000 tokens. Numbered implementation sequence with verification triggers.}

{From stage_7.mandatory_build_order + stage_8.instrumented_phases[N].pulse_points}

### Implementation Sequence

1. **{Feature/Task 1}**: {description}
   - Files: `{file_1}`, `{file_2}`
   - Expected: {what should exist after this step}

{PULSE CHECK after step 1}:
- [ ] `{build_command}` exits 0
- [ ] `{lint_command}` exits 0
- [ ] Created files exist and export expected symbols

2. **{Feature/Task 2}**: {description}
   - Files: `{file_3}`, `{file_4}`
   - Expected: {what should exist after this step}

3. **{Feature/Task 3}**: {description}
   - Files: `{file_5}`
   - Expected: {what should exist after this step}

{PULSE CHECK after step 3}:
- [ ] All prior checks still pass
- [ ] New components render without errors
- [ ] {Feature-specific check}

{Continue for all features in this phase...}

---

## 4. Seam Check Definitions

{~2,000 tokens. Integration verification points where components meet.}

{From stage_8.instrumented_phases[N].seam_checks}

| Seam | Components | Verification |
|------|-----------|-------------|
| {seam_1_name} | `{component_A}` ↔ `{component_B}` | {How to verify the integration works} |
| {seam_2_name} | `{component_C}` ↔ `{component_D}` | {How to verify} |

### Seam Verification Commands

```bash
# Seam 1: {name}
{verification_command_1}

# Seam 2: {name}
{verification_command_2}
```

---

## 5. Objective and Feature Requirements

{Variable tokens. The actual implementation instructions — WHAT to build.}

{Cross-reference: stage_7.phases[N].features + stage_4.mechanisms + stage_6.sub_6b}

### Phase Objective

{One paragraph: what this phase accomplishes in the overall build.}

### Feature: {feature_name_1}

**Mechanism**: {mechanism_id} — {mechanism_name} from Stage 4
**Classification**: {WALL | DOOR | ROOM} from Stage 5
**Page**: {page_name} from Stage 6b (if applicable)

**Requirements**:
1. {Specific, actionable requirement with file path and expected behavior}
2. {Specific requirement}
3. {Specific requirement}

**Acceptance Criteria**:
- [ ] {Testable criterion}
- [ ] {Testable criterion}

### Feature: {feature_name_2}

{Same structure...}

---

## 6. Pattern References

{From stage_5.mechanism_blueprints — file:line references.}

When implementing features in this phase, follow these existing patterns:

| Pattern | Reference | Used For |
|---------|-----------|----------|
| {pattern_name_1} | `{file_path}:{line_range}` | {Which feature/mechanism} |
| {pattern_name_2} | `{file_path}:{line_range}` | {Which feature/mechanism} |

**Wall patterns** (deterministic — implement exactly as shown):
- {pattern reference}

**Door patterns** (constrained — follow the structure, adapt the specifics):
- {pattern reference}

**Room patterns** (creative — use as inspiration, not prescription):
- {pattern reference}

---

## 7. Violation Handling Instructions

{~2,000 tokens. Decision tree for when rules are broken.}

{From stage_8.instrumented_phases[N].violation_handling}

| Severity | Trigger | Action |
|----------|---------|--------|
| **LOW** | Style inconsistency, minor naming deviation | Log the issue. Continue building. Fix in cleanup pass. |
| **MEDIUM** | Modified a read-only file, missing an export | Stop current feature. Fix the violation. Then continue. |
| **HIGH** | Modified a forbidden file, broke existing tests | Rollback to last pulse point. Re-implement from that checkpoint. |
| **CRITICAL** | Security violation, deleted required files, data loss risk | Full stop. Rollback entire phase. Flag for human review. |

### Self-Detection Protocol

After each pulse check, verify:
1. Run `git diff --name-only {BASELINE}` — are all changed files in the "CAN Modify" list?
2. Run `{build_command}` — does it still pass?
3. Run `{test_command}` (if tests exist) — do they still pass?

If any check fails, classify the violation using the table above and take the
prescribed action.

---

## 8. Full Checkpoint at End

{~5,000 tokens. The final verification gate for this phase.}

{From stage_8.instrumented_phases[N].full_checkpoint}

### Step 1: Self-Report

List every file you created or modified in this phase:

```
{Expected to be filled by the agent during execution}
```

### Step 2: Diff Check

Run:
```bash
git diff {PHASE_N_BASELINE}..HEAD --name-only
```

Compare the output against:
- Your self-report (Step 1) — every file in the diff must be in your report
- The "CAN Modify" list (Section 2) — every file in the diff must be allowed
- **Mismatch between self-report and diff is itself a violation.**

### Step 3: Violation Response

For any file in the diff NOT in the allowed list:
- Apply the violation severity table from Section 7
- Take the prescribed action
- Document: "Violation detected: {file} — severity: {level} — action: {taken}"

### Step 4: Functional Verification

```bash
# Compile check
{build_command}

# Lint check
{lint_command}

# Test check (if applicable)
{test_command}

# Render check (if UI phase)
{render_check_command}
```

ALL FOUR STEPS must produce exit code 0.

---

## 9. Gate Condition

**ALL FOUR CHECKPOINT STEPS MUST PASS BEFORE PHASE {N+1} BEGINS.**

{For the final phase, replace with: "ALL FOUR CHECKPOINT STEPS MUST PASS. PIPELINE COMPLETE."}

If any step fails:
1. Classify the failure severity
2. Apply violation handling (Section 7)
3. Re-run the checkpoint
4. If it fails again, stop for human review (two-strike rule)
```

---

## Rendering Rules

1. Replace ALL `{placeholders}` with actual values from the context packet
2. Martin's rules appear as architecture principles and coding standards — NEVER reference "Martin" by name
3. Each phase file is 100% self-contained — no `See phase-1.md` references
4. Every feature requirement must be specific enough to implement without asking questions
5. File paths in sandbox lists are exact (no globs unless the phase spec uses globs)
6. Pulse check commands use the actual build/lint/test commands from `stage_0.tech_stack`
7. Overhead tokens (~25,000 per phase) are the sections 1-4 + 7-9. Section 5-6 tokens come from the phase's content budget.


---
## REFERENCE: platform-wrappers

# Platform Wrappers — Execution Instructions Per Platform

> Phase file CONTENT is identical across all platforms.
> Only the execution method and wrapper instructions change.
> This file provides per-platform instructions included in README.md.

---

## Platform Matrix

| Platform | Enum Value | Terminal? | Automation | Agent Command |
|----------|-----------|-----------|-----------|---------------|
| Claude Code CLI | `claude_cli` | Yes | Full | `claude --print "$(cat phase-N.md)"` |
| Claude Code Web | `claude_web` | No | Manual | Copy-paste phase-N.md content |
| Codex CLI | `codex_cli` | Yes | Full | `codex run --prompt-file phase-N.md` |
| Gemini CLI | `gemini_cli` | Yes | Full | `gemini code --prompt-file phase-N.md` |
| Cursor | `cursor` | Yes | Semi | Paste into Cursor terminal/chat |
| Windsurf | `windsurf` | Yes | Semi | Paste into Windsurf terminal/chat |
| Bolt | `bolt` | No | Manual | Paste into Bolt chat interface |
| Lovable | `lovable` | No | Manual | Paste into Lovable chat interface |
| Generic | `generic` | Varies | Manual | Paste into any coding agent |

---

## Per-Platform README Instructions

### claude_cli

```markdown
## How to Build

### Automated (Recommended)
```bash
chmod +x build.sh
bash build.sh
```

The build script will:
1. Take a git snapshot before each phase
2. Run pre-build validation (build + lint)
3. Execute the phase via Claude Code CLI
4. Run post-build validation
5. Check for forbidden file modifications
6. Commit and continue to the next phase
7. Auto-retry failed phases (2 attempts max)

### Manual (If build.sh fails)
If the script stops at Phase N:
1. Open `phases/phase-N.md`
2. Run: `claude --print "$(cat phases/phase-N.md)"`
3. After completion, run build + lint manually
4. Continue with Phase N+1

### Hybrid
Run `build.sh`. If it crashes at Phase 3, open `phases/phase-3.md`
and pick up manually from there. Each phase is self-contained.
```

---

### claude_web

```markdown
## How to Build

1. Open Claude Code in your browser
2. Open `phases/phase-1.md`
3. Copy the ENTIRE contents and paste into the chat
4. Wait for the agent to complete Phase 1
5. Verify: run `{build_command}` and `{lint_command}` in your terminal
6. If both pass, proceed to Phase 2
7. Repeat for each phase in order

**Important**: Each phase is self-contained. The agent does not need
context from previous phases — each phase file includes everything needed.

**Between phases**: Wait 2-3 minutes for rate limits to reset.
```

---

### codex_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
codex run --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
codex run --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### gemini_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
gemini code --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
gemini code --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### cursor

```markdown
## How to Build

1. Open the project in Cursor
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Cursor's AI chat (Cmd+L / Ctrl+L)
4. Let the agent implement Phase 1
5. Open terminal (Ctrl+`) and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase

**Tip**: Use Cursor's terminal to run verification commands between phases.
```

---

### windsurf

```markdown
## How to Build

1. Open the project in Windsurf
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Windsurf's Cascade chat
4. Let the agent implement Phase 1
5. Open terminal and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase
```

---

### bolt

```markdown
## How to Build

Bolt does not have terminal access. Follow these steps:

1. Open Bolt and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Bolt's chat
4. Wait for the agent to complete Phase 1
5. Download the project and verify locally:
   ```bash
   {build_command} && {lint_command}
   ```
6. If verification passes, go back to Bolt
7. Open `phases/phase-2.md` and paste into chat
8. Repeat for each phase

**Important**: Since Bolt has no terminal, you must download and
verify locally between phases. Do NOT skip verification.
```

---

### lovable

```markdown
## How to Build

Lovable does not have terminal access. Follow these steps:

1. Open Lovable and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Lovable's prompt
4. Wait for the agent to complete Phase 1
5. Use Lovable's preview to visually verify the output
6. Export to GitHub and verify locally:
   ```bash
   git clone {repo_url}
   cd {project_name}
   {build_command} && {lint_command}
   ```
7. If verification passes, continue to Phase 2
8. Repeat for each phase

**Important**: Export and verify locally between phases.
```

---

### generic

```markdown
## How to Build

This build package works with any coding agent.

### Steps
1. Open `phases/phase-1.md` in a text editor
2. Copy the ENTIRE contents
3. Paste into your coding agent of choice
4. Wait for completion
5. Verify in terminal:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, continue to Phase 2
7. Repeat for each phase in order

### Key Points
- Each phase file is self-contained (no cross-references)
- Phases must be executed in order (1, 2, 3...)
- Verify build + lint between every phase
- If a phase fails, re-run it from scratch (don't try to fix partial work)
- `CLAUDE.md` stays in the repo forever — any future agent interaction will read it
```

---

## Rendering Rules

1. Replace `{build_command}` and `{lint_command}` with actual commands from `stage_0.tech_stack`
2. Replace `{project_name}` with `stage_3.concept_and_context.name`
3. Include ONLY the section matching `platform_target` in the final README.md
4. For automated platforms (`claude_cli`, `codex_cli`, `gemini_cli`), always include BOTH automated and manual fallback instructions
5. For no-terminal platforms (`bolt`, `lovable`), emphasize local verification between phases
6. The `build.sh` file is always generated regardless of platform (serves as documentation even if not executable on the target platform)

