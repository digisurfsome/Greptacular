# Schema Alignment Log (Stages 6-10)

Cross-cutting schema alignment performed 2026-04-05. Producer output is source of truth for field names. Stage 6 output is the starting anchor (not modified).

---

## Stage 7 Output -> Stage 8 Input (SKILL-COMPLETE.md)

| Mismatch | Producer (Stage 7) Field | Consumer (Stage 8) Field | Fix Applied |
|----------|-------------------------|-------------------------|-------------|
| Phase name field | `phase_name` | `name` | Updated Stage 8 input to `phase_name` |
| Mechanisms list | `mechanisms_included` | `mechanism_ids` | Updated Stage 8 input to `mechanisms_included` |
| Token estimate | `estimated_content_tokens` + `estimated_total_tokens` | `estimated_tokens` | Updated Stage 8 input to both fields |
| File sandbox structure | Nested `file_sandbox.allowed/.read_only/.forbidden` | Flat `files_allowed`, `files_read_only`, `files_forbidden` | Updated Stage 8 input to nested `file_sandbox` structure |
| Token budget location | `total_estimated_tokens` and `phase_count` at top level | Inside `token_budget` as `total_spec_tokens` and `phases_needed` | Moved to top level; removed from `token_budget` |
| Process text (line 77) | `file_sandbox.allowed`, `mechanisms_included` | `files_allowed`, `mechanism_ids` | Updated process text |
| Budget validation (line 148) | `estimated_content_tokens` | `estimated_tokens` | Updated to `estimated_content_tokens` |

---

## Stage 8 Output -> Stage 9 Input (SKILL-COMPLETE.md)

| Mismatch | Producer (Stage 8) Field | Consumer (Stage 9) Field | Fix Applied |
|----------|-------------------------|-------------------------|-------------|
| Top-level array name | `instrumented_phases` | `protocol_injected_phases` | Updated all occurrences in Stage 9 |
| Pulse check array | `pulse_points` | `pulse_checks` | Updated in input JSON |
| Violation object name | `violation_handling` | `violation_rules` | Updated all occurrences in Stage 9 |
| Violation key casing | lowercase (`low`, `medium`, `high`, `critical`) | UPPERCASE (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) | Updated input JSON to lowercase |
| Violation value field | `response` | `action` | Updated input JSON to `response` |
| Violation value names | `review_and_decide`, `full_stop` | `review_change`, `full_stop_revert_flag` | Updated to match Stage 8 |
| Stage 7 file sandbox in input | `file_sandbox.allowed/.read_only/.forbidden` | flat `files_allowed` etc. | Updated input JSON to nested structure |
| "When to Use" text | `instrumented_phases` | `protocol_injected_phases` | Updated |
| Process Step 3 (line 91) | `file_sandbox.allowed` | `files_allowed` | Updated |
| Per-phase config (line 206) | `stage_7.phases[0].file_sandbox.allowed` | `stage_7.phases[0].files_allowed` | Updated |
| Agent B template (line 641) | `stage_7.phases[N].file_sandbox.allowed` | `stage_7.phases[N].files_allowed` | Updated |
| Confidence scoring (line 274) | `file_sandbox.allowed` | `files_allowed` | Updated |

---

## Stage 8 Output -> Stage 10 Input (SKILL-COMPLETE.md)

| Mismatch | Producer (Stage 8) Field | Consumer (Stage 10) Field | Fix Applied |
|----------|-------------------------|-------------------------|-------------|
| Pulse check array (lines 62, 1095) | `pulse_points` | `pulse_checks` | Updated to `pulse_points` |
| Violation object (lines 66, 1205) | `violation_handling` | `violation_rules` | Updated to `violation_handling` |
| Violation key casing in text | lowercase | UPPERCASE | Updated to lowercase |

Note: Stage 10 input format JSON already used `instrumented_phases` correctly. Only inline references were mismatched.

---

## stage-contracts.md vs SKILL-COMPLETE.md Reconciliation

| Stage | Contract Field | Skill Field | Resolution |
|-------|---------------|-------------|------------|
| 6 output | `arrangement` with `page_list` | `sub_6a`, `sub_6b`, `sub_6c` | Updated contract to match skill structure |
| 6 output | `style` with `style_id`, `color_tokens` | `sub_6c` with `selected_style_id`, `design_tokens` | Updated contract |
| 6 output | `all_mechanisms_mapped` at top | Under `sub_6b` | Updated contract |
| 6 "Done When" | `page_list`, `navigation_pattern` | `sub_6b.pages`, `sub_6a.selected_arrangement_id` | Updated criteria |
| 6 inputs | `blueprints` | `mechanism_blueprints` | Updated contract |
| 6 inputs | `concept_document` | `concept_and_context` | Updated contract |
| 6 inputs | `matched_archetype` | `archetype_matches` | Updated contract |
| 10 inputs | `stage_5.blueprints` | `stage_5.mechanism_blueprints` | Updated contract |
| 10 inputs | `stage_6.arrangement + style` | `stage_6.sub_6a + sub_6b + sub_6c` | Updated contract |
| 10 inputs | `stage_3.concept_document` | `stage_3.concept_and_context` | Updated contract |
| Alignment table row 5 | `blueprints` | `mechanism_blueprints` | Updated |
| Alignment table row 6 | `arrangement, style` | `sub_6a, sub_6b, sub_6c` | Updated |

---

## Not Changed (Already Aligned)

- Stage 6 output (SKILL-COMPLETE.md) -- anchor, not modified
- Stage 7 output fields -- already consistent between skill and contract
- Stage 8 output fields -- already consistent between skill and contract
- Stage 9 output fields -- already consistent
- Stage 10 input format JSON (lines 22-24) -- already used correct field names
