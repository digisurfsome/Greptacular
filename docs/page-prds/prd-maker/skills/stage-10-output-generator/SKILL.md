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
  "stage_8": { "protocol_injected_phases": [...], "overhead_breakdown": {...} },
  "stage_9": {
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

- `phases/phase-N.md` (one per phase from `stage_7.phases`) — type: `"phase"`, tokens: `stage_7.token_budget.per_phase[N]` + `stage_8.overhead_breakdown.per_phase[N]`
- `build.sh` — type: `"build_script"`, tokens: ~2,000
- `CLAUDE.md` — type: `"claude_md"`, tokens: ~3,000 (must stay under 500 lines)
- `BUILD_RULES.md` — type: `"build_rules"`, tokens: ~8,000
- `README.md` — type: `"readme"`, tokens: ~1,500

### Step 2: Render Phase Files

For each phase in `stage_8.protocol_injected_phases`, compile a standalone `phase-N.md` with exactly 9 sections in order. Use the template in `references/phase-file-template.md`. Each section's source:

1. **Build Rules Preamble** (~8K tokens): From `stage_5.build_rules_applied` + `stage_3.drift_anchor`. Distribute Martin's rules as architecture principles — NEVER as a standalone "Martin's Rules" block.
2. **File Sandbox Declaration** (~2K tokens): From `stage_7.phases[N].files_allowed`, `files_read_only`, `files_forbidden`.
3. **Build Order with Pulse Points** (~3K tokens): From `stage_7.mandatory_build_order` + `stage_8.protocol_injected_phases[N].pulse_checks`.
4. **Seam Check Definitions** (~2K tokens): From `stage_8.protocol_injected_phases[N].seam_checks`.
5. **Objective and Feature Requirements**: From `stage_7.phases[N].features` cross-referenced with `stage_4.mechanisms` and `stage_6.sub_6b`.
6. **Pattern References**: From `stage_5.mechanism_blueprints` — file:line references for patterns to follow, informed by Wall/Door/Room classifications.
7. **Violation Handling Instructions** (~2K tokens): From `stage_8.protocol_injected_phases[N].violation_rules`. Decision tree: LOW (log+continue), MEDIUM (fix first), HIGH (rollback to pulse), CRITICAL (stop+human).
8. **Full Checkpoint at End** (~5K tokens): From `stage_8.protocol_injected_phases[N].full_checkpoint`. 4-step check: self-report, diff check, violation response, functional verification.
9. **Gate Condition**: "ALL FOUR STEPS MUST PASS BEFORE PHASE [N+1] BEGINS" (or "PIPELINE COMPLETE" for last phase).

**Critical**: Each phase file MUST be self-contained — executable in a fresh agent context without cross-file references (except READ-ONLY codebase files).

### Step 3: Generate build.sh

Create the deterministic bash wrapper using the template in `references/build-sh-template.md`:

- `set -e` — stop on ANY error
- Per-phase block: git snapshot (`SNAPSHOT=$(git rev-parse HEAD)`), pre-build validation, agent work marker, post-build validation, forbidden file detection via `git diff --name-only $SNAPSHOT`, commit
- Phase chaining with `&&` (NEVER `;`)
- Two-strike retry from `stage_9.two_strike_rule`: fail → rollback → retry with fresh agent → second fail → stop for human
- Platform-adaptive commands from `stage_0.tech_stack` (build, lint, test commands)
- Forbidden file detection: `git diff --name-only $SNAPSHOT | grep -E "forbidden_pattern"` built from each phase's `files_forbidden`

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
| `stage_8.protocol_injected_phases` missing | FAIL — escape hatch. Cannot render phase files without protocols. |
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
  "stage_7": { "phases": [{ "phase_number": 1, "features": ["auth", "db-setup"], "files_allowed": ["src/lib/supabase.ts"] }, { "phase_number": 2, "features": ["task-board"], "files_allowed": ["src/components/Board.tsx"] }], "token_budget": { "per_phase": { "1": 20000, "2": 25000 } } }
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
