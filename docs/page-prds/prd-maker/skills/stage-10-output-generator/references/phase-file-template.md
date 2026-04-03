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

{From stage_7.phases[N].files_allowed}

```
{file_path_1}
{file_path_2}
...
```

### Files You CAN Read (But NOT Modify)

{From stage_7.phases[N].files_read_only}

```
{file_path_1}
{file_path_2}
...
```

### Files You CANNOT Touch

{From stage_7.phases[N].files_forbidden}

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

{From stage_7.mandatory_build_order + stage_8.protocol_injected_phases[N].pulse_checks}

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

{From stage_8.protocol_injected_phases[N].seam_checks}

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

{From stage_8.protocol_injected_phases[N].violation_rules}

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

{From stage_8.protocol_injected_phases[N].full_checkpoint}

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
