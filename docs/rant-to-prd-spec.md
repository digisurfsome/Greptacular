# Rant-to-PRD: Terminal-Powered System Specification

## Agent OS 3-Layer PRD Format

**Version:** 1.0.0
**Date:** 2026-02-22
**Status:** Implementation-Ready

---

# LAYER 1: STANDARDS — Universal Infrastructure

## 1.1 System Identity

| Field | Value |
|-------|-------|
| System Name | Rant-to-PRD Pipeline |
| Platform | Claude Code CLI (terminal-native) |
| Architecture | 7-stage sequential agent pipeline |
| Host System | Autoforge (optional bridge at Stage 7) |
| Input | Unstructured text file (the "rant") |
| Output | Complete PRD (Markdown + JSON) + optional Autoforge app_spec.txt |

## 1.2 Design Principles

1. **Zero Detail Loss** — Every mechanism, constraint, and preference the user mentions must appear in the final PRD. The system reformats but never summarizes away specifics.
2. **Terminal-Native** — No web UI, no browser, no GUI. Everything runs through Claude Code CLI with `claude -p` (headless) for automated stages and `claude` (TTY) for interactive stages.
3. **Deterministic Pipeline** — Given the same rant input, the pipeline produces the same output (temperature 0 for all non-interactive stages).
4. **Resumable** — Pipeline state is persisted after each stage. Interruptions resume from the last validated checkpoint.
5. **Auditable** — Every item in the final PRD traces back to its origin (user-specified, auto-filled, or user-decided) via provenance tags.

## 1.3 Architecture Pattern

```
Stage 1          Stage 2          Stage 3          Stage 4
Transcriber  --> Classifier   --> Gap Analyst  --> Decision Facilitator
(opus)           (sonnet)         (opus)           (sonnet, interactive)
                                                          |
Stage 7          Stage 6          Stage 5                 |
Autoforge    <-- PRD Compiler <-- Mechanism Analyst <-----+
(sonnet,opt)     (opus)           (opus)
```

## 1.4 Execution Model

Each stage runs as an independent Claude Code CLI invocation:

```bash
# Headless (automated) stages
claude -p "prompt here" \
  --agent ".claude/agents/rant-{stage}.md" \
  --output-format json \
  --max-tokens 32000

# Interactive stage (Stage 4 only)
claude --agent ".claude/agents/rant-decision-facilitator.md" \
  --resume  # TTY mode for user interaction
```

**Key properties:**
- Each stage reads from disk, writes to disk — no in-memory state between stages
- Stages are orchestrated by a bash script (rant-pipeline.sh), not by Claude
- The pipeline script handles retries, validation, and state management
- Claude agents are stateless workers; the script is the stateful coordinator

## 1.5 Directory Structure

```
rant-pipeline/                      # Created per pipeline run
  pipeline_state.json               # Pipeline progress tracker
  pipeline.log                      # Structured log (JSON lines)
  token_usage.json                  # Token consumption per stage
  input/
    rant.txt                        # Original rant (copied from user file)
    rant_hash.sha256                # Input hash for integrity
  stage1/
    raw_capture.json                # Transcriber output
    validation.json                 # Stage 1 validation results
  stage2/
    classified.json                 # Classifier output
    validation.json
  stage3/
    gap_report.json                 # Gap analysis output
    validation.json
  stage4/
    decisions.json                  # User/auto decisions
    validation.json
  stage5/
    mechanisms.json                 # Mechanism analysis output
    validation.json
  stage6/
    final_prd.md                    # The PRD (Markdown)
    final_prd.json                  # The PRD (structured JSON)
    tracking_matrix.json            # Item provenance tracking
    validation.json
  stage7/                           # Optional (--autoforge flag)
    app_spec.txt                    # Autoforge-compatible spec
    features.json                   # Feature metadata
    validation.json
```

## 1.6 Pipeline State Management

**File:** pipeline_state.json

```json
{
  "pipeline_id": "rant_20260222_143052",
  "status": "running",
  "created_at": "2026-02-22T14:30:52Z",
  "updated_at": "2026-02-22T14:35:12Z",
  "input_hash": "sha256:abc123...",
  "stages": {
    "1": {"status": "validated", "started_at": "...", "completed_at": "..."},
    "2": {"status": "validated", "started_at": "...", "completed_at": "..."},
    "3": {"status": "running", "started_at": "...", "completed_at": null},
    "4": {"status": "pending"},
    "5": {"status": "pending"},
    "6": {"status": "pending"},
    "7": {"status": "pending"}
  },
  "options": {
    "interactive": true,
    "include_autoforge": false,
    "non_interactive": false
  }
}
```

Stage status transitions: pending -> running -> complete -> validated (or failed)

---

# LAYER 2: PRODUCT — The Seven Stages

## 2.1 Stage 1: Transcriber Agent

**Purpose:** Transform the raw rant into structured, deduplicated bullets while preserving every detail.

**Agent file:** .claude/agents/rant-transcriber.md
**Model:** opus | **Temperature:** 0 | **Max tokens:** 32,000

### Input
- Raw rant text file (any length, any format)

### Processing Rules
1. Read the entire rant without summarizing
2. Identify every discrete mechanism, feature, constraint, preference, and vision statement
3. Cluster related items (e.g., all invoicing mentions go in one cluster)
4. For each item, preserve the original quote verbatim
5. Classify each item type: mechanism, behavior, constraint, negative_requirement, comparative, vision, edge_case, user_experience
6. Assign unique IDs: item_001, item_002, etc.
7. Extract global context: app type, target users, core value proposition, tone/vibe

### Output Schema

```json
{
  "metadata": {
    "stage": 1,
    "stage_name": "transcriber",
    "version": "1.0.0",
    "timestamp": "2026-02-22T14:31:00Z",
    "input_hash": "sha256:...",
    "input_word_count": 2847,
    "item_count": 47,
    "cluster_count": 8,
    "detail_density_ratio": 0.72,
    "token_usage": {"input_tokens": 15000, "output_tokens": 12000}
  },
  "data": {
    "global_context": {
      "app_type": "SaaS platform",
      "target_users": "Freelance designers",
      "core_value_proposition": "Visual-first business management",
      "tone": "Creative, fun, anti-corporate",
      "comparative_references": ["Slack threads", "Jira boards", "QuickBooks"]
    },
    "clusters": [
      {
        "cluster_id": "cluster_01",
        "cluster_name": "Visual Dashboard",
        "items": [
          {
            "item_id": "item_001",
            "type": "mechanism",
            "content": "Project tracker displayed as visual timeline with cards showing actual design work",
            "original_quotes": [
              "it should be like a visual timeline where you can see all your projects as these beautiful cards"
            ],
            "confidence": 0.95,
            "related_items": ["item_003", "item_015"]
          }
        ]
      }
    ]
  }
}
```

### Quality Gate
- Detail Density Ratio (DDR) >= 0.60
- Item count > 0
- All items have original_quotes (non-empty array)
- No empty content fields
- All item IDs are unique

---

## 2.2 Stage 2: Classifier Agent

**Purpose:** Place every item from Stage 1 into the correct Agent OS PRD section. Zero drops allowed.

**Agent file:** .claude/agents/rant-classifier.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 32,000

### Input
- stage1/raw_capture.json

### PRD Section Taxonomy

**Standards Layer:**
- STD-ARCH — Architecture and Infrastructure
- STD-AUTH — Authentication and Authorization
- STD-DATA — Data Management
- STD-API — API Design
- STD-ERR — Error Handling and Resilience
- STD-PERF — Performance
- STD-SEC — Security
- STD-TEST — Testing
- STD-OPS — Operations

**Product Layer:**
- PROD-UX — User Experience
- PROD-DESIGN — Design System and Visual Identity
- PROD-FLOW — User Flows and Journeys
- PROD-LEGAL — Legal and Compliance

**Specs Layer:**
- SPEC-FEAT — Feature Specifications
- SPEC-INTEG — Integrations
- SPEC-EDGE — Edge Cases and Error States

### Processing Rules
1. Read every item from Stage 1
2. Assign each item to exactly one primary section
3. Optionally assign up to 2 secondary sections (cross-references)
4. Preserve the original content verbatim — do NOT rewrite or summarize
5. Items spanning multiple sections get placed in the most specific section
6. Track placement with an unplaced_items array (must be empty at completion)

### Output Schema

```json
{
  "metadata": {
    "stage": 2,
    "stage_name": "classifier",
    "version": "1.0.0",
    "timestamp": "...",
    "input_hash": "sha256:...",
    "input_item_count": 47,
    "output_item_count": 47,
    "sections_used": 12,
    "token_usage": {"input_tokens": 18000, "output_tokens": 14000}
  },
  "data": {
    "sections": {
      "STD-ARCH": {
        "section_name": "Architecture and Infrastructure",
        "layer": "standards",
        "items": [
          {
            "item_id": "item_005",
            "original_content": "...",
            "placement_rationale": "Describes hosting and deployment preference",
            "secondary_sections": ["STD-PERF"],
            "confidence": 0.90
          }
        ]
      }
    },
    "cross_references": [
      {"item_id": "item_005", "primary": "STD-ARCH", "secondary": ["STD-PERF"]}
    ],
    "unplaced_items": []
  }
}
```

### Quality Gate
- input_item_count == output_item_count (zero drops)
- unplaced_items array is empty
- All original_content matches Stage 1 verbatim
- DDR >= 0.95

---

## 2.3 Stage 3: Gap Analyst Agent

**Purpose:** Compare classified items against a completeness checklist. Identify what is missing. Auto-fill obvious defaults, flag ambiguous gaps for user decisions.

**Agent file:** .claude/agents/rant-gap-analyst.md
**Model:** opus | **Temperature:** 0 | **Max tokens:** 16,384

### Input
- stage2/classified.json
- stage1/raw_capture.json (for global context)
- Built-in completeness checklist (embedded in agent prompt)

### Gap Types

| Type | Description | Action |
|------|-------------|--------|
| **Type A** | Covered — user explicitly mentioned it | No action needed |
| **Type B** | Auto-fillable — obvious default exists given context | Auto-fill with rationale |
| **Type C** | Ambiguous — multiple valid approaches, user decision needed | Generate decision question |

### Auto-Fill Rules (Type B)

Auto-fills are applied when:
1. There is an industry-standard default (e.g., HTTPS, CSRF protection)
2. The user context strongly implies a choice (e.g., "visual-first" implies responsive design)
3. The choice has no meaningful trade-off (e.g., input sanitization — always do it)

Each auto-fill includes:
- rationale: Why this default was chosen
- confidence: 0.0-1.0 confidence score
- override_hint: What the user might want instead

### Decision Questionnaire (Type C)

For each ambiguous gap, the analyst generates:
- A plain-language question (no jargon)
- 2-4 options with pros/cons
- A recommended option (used in --non-interactive mode)
- Grouping with related decisions

### Output Schema

```json
{
  "metadata": {
    "stage": 3,
    "stage_name": "gap_analyst",
    "version": "1.0.0",
    "timestamp": "...",
    "input_hash": "sha256:...",
    "checklist_items_total": 87,
    "type_a_count": 23,
    "type_b_count": 41,
    "type_c_count": 23,
    "coverage_percentage": 100,
    "token_usage": {"input_tokens": 22000, "output_tokens": 10000}
  },
  "data": {
    "coverage_summary": {
      "total_checklist_items": 87,
      "covered_by_user": 23,
      "auto_filled": 41,
      "needs_decision": 23,
      "not_applicable": 0
    },
    "auto_fills": [
      {
        "gap_id": "gap_001",
        "checklist_item": "CSRF protection",
        "section": "STD-SEC",
        "auto_fill_value": "CSRF tokens on all state-changing requests",
        "rationale": "Industry standard, no trade-off",
        "confidence": 0.98,
        "override_hint": "Could use SameSite cookies instead if API-only"
      }
    ],
    "decision_questionnaire": [
      {
        "decision_id": "dec_001",
        "group": "Authentication",
        "checklist_item": "Authentication method",
        "section": "STD-AUTH",
        "question": "How should users log in to the platform?",
        "options": [
          {
            "option_id": "opt_a",
            "label": "Email + Password",
            "description": "Traditional login. Simple to implement, familiar to users.",
            "pros": ["Simple", "No third-party dependency"],
            "cons": ["Users must remember another password"],
            "decide_for_me_maps_to": false
          },
          {
            "option_id": "opt_b",
            "label": "Magic Link (email-based)",
            "description": "User enters email, receives a login link. No password needed.",
            "pros": ["No passwords to manage", "Modern feel", "Matches creative vibe"],
            "cons": ["Requires email access to log in"],
            "decide_for_me_maps_to": true
          }
        ],
        "recommended": "opt_b",
        "recommendation_rationale": "Magic links align with the creative, modern vibe"
      }
    ]
  }
}
```

### Quality Gate
- All checklist items accounted for (Type A + B + C + N/A = total)
- Auto-fill confidence scores are reasonable (not all 1.0)
- Each Type C gap has 2-4 options
- Each Type C gap has a recommended option
- Recommendation rationale provided for all

---

## 2.4 Stage 4: Decision Facilitator Agent

**Purpose:** Present gap decisions to the user in plain language. Collect answers. In non-interactive mode, use recommended defaults.

**Agent file:** .claude/agents/rant-decision-facilitator.md
**Model:** sonnet | **Temperature:** 0.3 | **Max tokens:** 16,384

### Execution Modes

**Interactive (default):** Runs in TTY mode. Presents each decision group, collects responses.

**Non-interactive (--non-interactive):** Automatically selects the recommended option for every decision. All marked as auto_decided.

**Zero decisions:** If Stage 3 produced no Type C gaps, Stage 4 writes an empty decisions file and skips.

### Interactive Conversation Flow

```
DECISIONS NEEDED: Authentication (2 questions)

Question 1 of 2: How should users log in?

  A) Email + Password — Traditional login, simple and familiar
  B) Magic Link — No password, user gets an email link [recommended]
  C) Social Login — Google/GitHub, fast but third-party dependent

Your choice (A/B/C, or press Enter for recommended):
```

### Output Schema

```json
{
  "metadata": {
    "stage": 4,
    "stage_name": "decision_facilitator",
    "version": "1.0.0",
    "timestamp": "...",
    "total_decisions": 23,
    "user_decided": 15,
    "auto_decided": 8,
    "interaction_duration_seconds": 420,
    "token_usage": {"input_tokens": 8000, "output_tokens": 6000}
  },
  "data": {
    "decisions": [
      {
        "decision_id": "dec_001",
        "group": "Authentication",
        "question": "How should users log in?",
        "chosen_option": "opt_b",
        "chosen_label": "Magic Link",
        "decision_type": "user_decided",
        "user_comment": null
      }
    ],
    "decision_groups": [
      {"group": "Authentication", "decision_ids": ["dec_001", "dec_002"]}
    ],
    "auto_fill_overrides": []
  }
}
```

### Quality Gate
- Every Type C gap from Stage 3 has a corresponding decision
- All chosen_option values are valid option_ids from Stage 3
- decision_type is either user_decided or auto_decided

---

## 2.5 Stage 5: Mechanism Analyst Agent

**Purpose:** For every feature and mechanism, determine the implementation approach.

**Agent file:** .claude/agents/rant-mechanism-analyst.md
**Model:** opus | **Temperature:** 0 | **Max tokens:** 32,000

### Input
- stage2/classified.json (user items)
- stage3/gap_report.json (auto-fills)
- stage4/decisions.json (user decisions)

### Processing Rules
1. For each feature/mechanism, identify 1-3 implementation approaches
2. Evaluate each approach against project constraints and context
3. Recommend the best approach with detailed rationale
4. For multi-approach mechanisms, assign percentage weights (must sum to 100)
5. Cite research sources when referencing specific libraries or patterns
6. Consider inter-mechanism dependencies and conflicts

### Output Schema

```json
{
  "metadata": {
    "stage": 5,
    "stage_name": "mechanism_analyst",
    "version": "1.0.0",
    "timestamp": "...",
    "input_hash": "sha256:...",
    "total_mechanisms": 35,
    "total_features": 12,
    "token_usage": {"input_tokens": 25000, "output_tokens": 18000}
  },
  "data": {
    "mechanisms": [
      {
        "mechanism_id": "mech_001",
        "name": "Visual Project Timeline",
        "source_items": ["item_001", "item_003"],
        "section": "SPEC-FEAT",
        "approaches": [
          {
            "approach_id": "approach_a",
            "name": "CSS Grid + Custom Canvas",
            "description": "Build timeline with CSS Grid layout, HTML5 Canvas for card previews",
            "pros": ["Full control over visuals", "No library dependency"],
            "cons": ["More development time", "Accessibility requires extra work"],
            "complexity": "high",
            "weight": 30
          },
          {
            "approach_id": "approach_b",
            "name": "React Flow + Custom Nodes",
            "description": "Use React Flow library with custom-rendered nodes for project cards",
            "pros": ["Battle-tested library", "Built-in pan/zoom", "Good DX"],
            "cons": ["Bundle size", "Customization limits"],
            "complexity": "medium",
            "weight": 70
          }
        ],
        "recommended": "approach_b",
        "recommendation_rationale": "React Flow provides interactive timeline behavior out of box while allowing custom visual nodes.",
        "dependencies": ["mech_005"],
        "conflicts": []
      }
    ],
    "dependency_graph": {
      "nodes": ["mech_001", "mech_002"],
      "edges": [{"from": "mech_001", "to": "mech_005"}]
    }
  }
}
```

### Quality Gate
- All features have at least one mechanism
- Multi-approach percentage weights sum to 100 per mechanism
- All source_items reference valid item IDs from Stages 1-4
- Dependency graph is acyclic
- Research sources cited where applicable

---

## 2.6 Stage 6: PRD Compiler Agent

**Purpose:** Compile ALL stage outputs into the final, complete PRD document.

**Agent file:** .claude/agents/rant-prd-compiler.md
**Model:** opus | **Temperature:** 0 | **Max tokens:** 65,536

### Input
- ALL previous stage outputs (stages 1-5)

### Processing Rules
1. Read every stage output completely
2. Compile into Agent OS 3-layer PRD structure
3. Every item gets a provenance tag: [USER], [AUTO-FILL], [USER-DECIDED], [RECOMMENDED]
4. Cross-reference mechanisms with their source items
5. Generate table of contents
6. Include the tracking matrix as an appendix
7. Verify zero orphan items (every item from every stage appears in the final PRD)

### Provenance Tags

| Tag | Meaning |
|-----|---------|
| [USER] | Directly from the user rant |
| [AUTO-FILL] | System filled with obvious default |
| [USER-DECIDED] | User chose from options in Stage 4 |
| [RECOMMENDED] | System recommended, user accepted (non-interactive mode) |

### Markdown PRD Structure

```markdown
# {App Name} — Product Requirements Document

## Metadata
- Generated: {timestamp}
- Source: {rant file hash}
- Pipeline: {pipeline_id}

## Table of Contents

## Executive Summary

---

## LAYER 1: STANDARDS
### 1.1 Architecture and Infrastructure [STD-ARCH]
### 1.2 Authentication and Authorization [STD-AUTH]
...

## LAYER 2: PRODUCT
### 2.1 User Experience [PROD-UX]
...

## LAYER 3: SPECIFICATIONS
### 3.1 Feature Specifications [SPEC-FEAT]
...

## Appendix A: Provenance Tracking Matrix
## Appendix B: Decision Log
## Appendix C: Mechanism Details
```

### Verification Checkpoint Injection (Stage 6 Responsibility)

The PRD Compiler MUST inject verification checkpoints into the final PRD. This is automatic — no user input required.

**Process:**

1. **Tag every feature** in the PRD with one or more of: `[UI]`, `[DATA]`, `[API]`, `[WIRE]`, `[AUTH]`, `[PHASE-END]`
   - `[UI]` — Only visual/frontend changes
   - `[DATA]` — Creates or modifies database tables, schemas, or persistent storage
   - `[API]` — Adds or changes API endpoints or routes
   - `[WIRE]` — Connects two existing systems (frontend↔backend, service↔service)
   - `[AUTH]` — Involves authentication, authorization, permissions, or session management
   - `[PHASE-END]` — Last feature before a phase boundary

2. **Assign verification tier** based on tags:
   - `PULSE_CHECK` (default) — Lint + type check + run tests. 2-5 minutes. After every feature.
   - `SEAM_CHECK` — Pulse + test changed thing + test one dependency. 10-20 min. After `[DATA]`, `[API]`, `[WIRE]`, `[AUTH]`.
   - `FULL_VERIFY` — Complete protocol (all routes, all journeys, bug hunt, DB validation, edge cases, cross-feature, responsive). 30-60 min. After `[PHASE-END]`.

3. **Insert checkpoint markers** into the implementation phases section of the PRD:
   ```
   Phase 1: Foundation
     Feature: Database schema [DATA] → SEAM_CHECK
     Feature: Auth system [DATA][API][AUTH] → SEAM_CHECK
     Feature: Base layout [UI] → PULSE_CHECK
     Feature: Dashboard [UI][WIRE][PHASE-END] → FULL_VERIFY
   ```

4. **Add a verification_plan section** to the final PRD JSON output containing:
   - The three tier definitions (PULSE_CHECK, SEAM_CHECK, FULL_VERIFY)
   - A schedule of checkpoints (one FULL_VERIFY per phase minimum)
   - Feature-level tags and assigned tiers

5. **Add verification summary** to the PRD metadata:
   ```json
   "verification": {
     "pulse_checks": N,
     "seam_checks": N,
     "full_verifies": N,
     "total_checkpoints": N
   }
   ```

### Quality Gate
- Zero orphan items (every item from stages 1-5 appears)
- All provenance tags present
- Markdown renders correctly
- JSON validates against schema
- DDR >= 1.10 (output richer than inputs due to enrichment)
- `verification_plan` section exists in output with tier definitions and feature-level checkpoint assignments
- Every feature has at least one verification tag
- Every phase ends with at least one `FULL_VERIFY` checkpoint

---

## 2.7 Stage 7: Autoforge Bridge Agent (Optional)

**Purpose:** Transform the completed PRD into Autoforge app_spec.txt format with atomic features.

**Agent file:** .claude/agents/rant-autoforge-bridge.md
**Model:** sonnet | **Temperature:** 0 | **Max tokens:** 32,000

### Input
- stage6/final_prd.json

### Processing Rules
1. Read the complete PRD JSON
2. Break mechanisms into atomic features (implementable in 1-4 hours each)
3. Establish dependency order between features
4. Generate Autoforge XML format with feature elements
5. Include verification steps for each feature
6. Validate dependency graph is acyclic (Kahn algorithm)

### Output Files
- stage7/app_spec.txt — Autoforge-compatible XML spec
- stage7/features.json — Feature metadata with dependencies

### Quality Gate
- Dependency graph is acyclic
- All dependencies reference valid feature IDs
- XML is well-formed
- Each feature has name, description, steps, and verification criteria

---

# LAYER 3: SPECS — Implementation Details

## 3.1 Pipeline Orchestration Script

**File:** .claude/scripts/rant-pipeline.sh

### Usage

```bash
# Basic usage
bash .claude/scripts/rant-pipeline.sh my_rant.txt

# With options
bash .claude/scripts/rant-pipeline.sh my_rant.txt --non-interactive
bash .claude/scripts/rant-pipeline.sh my_rant.txt --autoforge
bash .claude/scripts/rant-pipeline.sh my_rant.txt --resume
bash .claude/scripts/rant-pipeline.sh my_rant.txt --stage 3

# Via slash command
/rant-to-prd my_rant.txt
```

### Core Functions

```bash
run_stage() {
    local stage="$1" prompt="$2" agent="$3" expected_output="$4"
    update_state "$stage" "running"
    run_hook "pre-stage-check" "$stage"

    local max_retries=3
    for attempt in $(seq 1 $max_retries); do
        claude -p "$prompt" \
            --agent "$agent" \
            --output-format json \
            --max-tokens 32000 \
            2>> "$PIPELINE_DIR/pipeline.log"

        if [[ -f "$expected_output" ]]; then
            if validate_stage_output "$stage" "$expected_output"; then
                update_state "$stage" "validated"
                run_hook "post-stage-log" "$stage"
                return 0
            else
                log "WARN" "$stage" "Validation failed (attempt $attempt/$max_retries)"
                if [[ $attempt -lt $max_retries ]]; then
                    prompt="$prompt\n\nCRITICAL: Previous attempt failed. Error: $(cat $PIPELINE_DIR/stage${stage}/validation.json)"
                fi
            fi
        fi
    done

    update_state "$stage" "failed"
    return 1
}

run_stage_interactive() {
    local stage="$1" agent="$2" initial_prompt="$3"
    update_state "$stage" "running"
    run_hook "pre-stage-check" "$stage"

    claude --agent "$agent" \
        --initial-prompt "$initial_prompt" \
        2>> "$PIPELINE_DIR/pipeline.log"

    local expected_output="$PIPELINE_DIR/stage${stage}/decisions.json"
    if [[ -f "$expected_output" ]] && validate_stage_output "$stage" "$expected_output"; then
        update_state "$stage" "validated"
        run_hook "post-stage-log" "$stage"
        return 0
    fi
    update_state "$stage" "failed"
    return 1
}

validate_stage_output() {
    local stage="$1" output_file="$2"
    local validation_file="$PIPELINE_DIR/stage${stage}/validation.json"

    # Structural: valid JSON, required fields
    if ! jq empty "$output_file" 2>/dev/null; then
        echo '{"valid":false,"error":"Invalid JSON"}' > "$validation_file"
        return 1
    fi
    if ! jq -e '.metadata and .data' "$output_file" > /dev/null 2>&1; then
        echo '{"valid":false,"error":"Missing metadata or data"}' > "$validation_file"
        return 1
    fi

    # Stage-specific semantic validation
    case "$stage" in
        1) validate_stage1 "$output_file" "$validation_file" ;;
        2) validate_stage2 "$output_file" "$validation_file" ;;
        3) validate_stage3 "$output_file" "$validation_file" ;;
        4) validate_stage4 "$output_file" "$validation_file" ;;
        5) validate_stage5 "$output_file" "$validation_file" ;;
        6) validate_stage6 "$output_file" "$validation_file" ;;
        7) validate_stage7 "$output_file" "$validation_file" ;;
    esac
}
```

### Resume Logic

```bash
find_resume_point() {
    local state_file="$PIPELINE_DIR/pipeline_state.json"
    for stage in 7 6 5 4 3 2 1; do
        local status
        status=$(jq -r ".stages[\"$stage\"].status" "$state_file")
        if [[ "$status" == "validated" ]]; then
            echo $((stage + 1))
            return
        fi
    done
    echo 1
}
```

### Main Pipeline Flow

```bash
main() {
    parse_args "$@"
    setup_directories
    prepare_input
    initialize_state

    local start_stage=1
    if [[ "$RESUME" = true ]]; then
        start_stage=$(find_resume_point)
        log "INFO" 0 "Resuming from Stage $start_stage"
    fi

    # Stage 1: Transcriber
    if [[ $start_stage -le 1 ]]; then
        run_stage 1 \
            "Read the rant at $PIPELINE_DIR/input/rant.txt. Extract every mechanism, feature, constraint, preference. Write to $PIPELINE_DIR/stage1/raw_capture.json." \
            ".claude/agents/rant-transcriber.md" \
            "$PIPELINE_DIR/stage1/raw_capture.json" \
            || { log "ERROR" 1 "Stage 1 failed."; exit 1; }
    fi

    # Stage 2: Classifier
    if [[ $start_stage -le 2 ]]; then
        run_stage 2 \
            "Read $PIPELINE_DIR/stage1/raw_capture.json. Classify every item into PRD sections. Write to $PIPELINE_DIR/stage2/classified.json. Zero drops." \
            ".claude/agents/rant-classifier.md" \
            "$PIPELINE_DIR/stage2/classified.json" \
            || { log "ERROR" 2 "Stage 2 failed."; exit 1; }
    fi

    # Stage 3: Gap Analyst
    if [[ $start_stage -le 3 ]]; then
        run_stage 3 \
            "Read $PIPELINE_DIR/stage2/classified.json and $PIPELINE_DIR/stage1/raw_capture.json. Analyze against completeness checklist. Write to $PIPELINE_DIR/stage3/gap_report.json." \
            ".claude/agents/rant-gap-analyst.md" \
            "$PIPELINE_DIR/stage3/gap_report.json" \
            || { log "ERROR" 3 "Stage 3 failed."; exit 1; }
    fi

    # Stage 4: Decision Facilitator
    if [[ $start_stage -le 4 ]]; then
        local questionnaire_count
        questionnaire_count=$(jq '.data.decision_questionnaire | length' "$PIPELINE_DIR/stage3/gap_report.json")

        if [[ "$questionnaire_count" -eq 0 ]]; then
            log "INFO" 4 "No decisions needed"
            # Write empty decisions file
            write_empty_decisions
            update_state 4 "validated"
        elif [[ "$INTERACTIVE" = true ]]; then
            run_stage_interactive 4 \
                ".claude/agents/rant-decision-facilitator.md" \
                "Read $PIPELINE_DIR/stage3/gap_report.json. Present each decision. Write to $PIPELINE_DIR/stage4/decisions.json." \
                || { log "ERROR" 4 "Stage 4 failed."; exit 1; }
        else
            run_stage 4 \
                "Read $PIPELINE_DIR/stage3/gap_report.json. Select recommended option for every decision. Write to $PIPELINE_DIR/stage4/decisions.json." \
                ".claude/agents/rant-decision-facilitator.md" \
                "$PIPELINE_DIR/stage4/decisions.json" \
                || { log "ERROR" 4 "Stage 4 failed."; exit 1; }
        fi
    fi

    # Stage 5: Mechanism Analyst
    if [[ $start_stage -le 5 ]]; then
        run_stage 5 \
            "Read $PIPELINE_DIR/stage2/classified.json, $PIPELINE_DIR/stage3/gap_report.json, $PIPELINE_DIR/stage4/decisions.json. Determine implementation approach for every mechanism. Write to $PIPELINE_DIR/stage5/mechanisms.json." \
            ".claude/agents/rant-mechanism-analyst.md" \
            "$PIPELINE_DIR/stage5/mechanisms.json" \
            || { log "ERROR" 5 "Stage 5 failed."; exit 1; }
    fi

    # Stage 6: PRD Compiler
    if [[ $start_stage -le 6 ]]; then
        run_stage 6 \
            "Read ALL stage outputs (stages 1-5). Compile the complete PRD. Write markdown to $PIPELINE_DIR/stage6/final_prd.md and JSON to $PIPELINE_DIR/stage6/final_prd.json." \
            ".claude/agents/rant-prd-compiler.md" \
            "$PIPELINE_DIR/stage6/final_prd.json" \
            || { log "ERROR" 6 "Stage 6 failed."; exit 1; }
    fi

    # Stage 7: Autoforge Bridge (optional)
    if [[ "$INCLUDE_AUTOFORGE" = true ]] && [[ $start_stage -le 7 ]]; then
        run_stage 7 \
            "Read $PIPELINE_DIR/stage6/final_prd.json. Transform to Autoforge app_spec.txt. Write to $PIPELINE_DIR/stage7/app_spec.txt and $PIPELINE_DIR/stage7/features.json." \
            ".claude/agents/rant-autoforge-bridge.md" \
            "$PIPELINE_DIR/stage7/features.json" \
            || { log "ERROR" 7 "Stage 7 failed."; exit 1; }
    fi

    # Pipeline Complete
    log "INFO" 0 "Pipeline complete"
    echo ""
    echo "================================================================"
    echo "  RANT-TO-PRD PIPELINE COMPLETE"
    echo "================================================================"
    echo "  PRD (Markdown):  $PIPELINE_DIR/stage6/final_prd.md"
    echo "  PRD (JSON):      $PIPELINE_DIR/stage6/final_prd.json"
    if [[ "$INCLUDE_AUTOFORGE" = true ]]; then
        echo "  Autoforge Spec:  $PIPELINE_DIR/stage7/app_spec.txt"
    fi
    echo "  Pipeline Log:    $PIPELINE_DIR/pipeline.log"
    echo "  Token Usage:     $PIPELINE_DIR/token_usage.json"
    echo "================================================================"
}
```

## 3.2 Slash Command Definition

**File:** .claude/commands/rant-to-prd.md

```markdown
---
description: Transform a stream-of-consciousness rant into a complete PRD
arguments:
  - name: rant_file
    description: Path to the rant text file
    required: true
---

Run the Rant-to-PRD pipeline on the provided rant file.
Execute: bash .claude/scripts/rant-pipeline.sh $ARGUMENTS

The pipeline will:
1. Transcribe and structure the rant
2. Classify items into PRD sections
3. Analyze gaps against completeness checklist
4. Present decisions for ambiguous gaps (interactive)
5. Analyze implementation mechanisms
6. Compile the final PRD

Output: rant-pipeline/stage6/final_prd.md

Flags: --autoforge, --non-interactive, --resume, --stage N
```

## 3.3 Hook Specifications

### Pre-Stage Hook (.claude/hooks/pre-stage-check.sh)

Verifies prerequisites before each stage:
- Stage 1: Rant input file exists and is non-empty
- Stage 2: Stage 1 output exists and is validated
- Stage 3: Stage 2 output exists and is validated
- Stage 4: Stage 3 output exists
- Stage 5: Stages 2, 3, 4 all validated
- Stage 6: Stages 1-5 all validated
- Stage 7: Stage 6 output exists

### Post-Stage Hook (.claude/hooks/post-stage-log.sh)

After each stage completes:
- Extracts token usage from output metadata
- Updates token_usage.json running totals
- Logs stage completion summary

### Post-Write Validation Hook (.claude/hooks/post-write-validate.sh)

Validates any JSON file written to the pipeline directory:
- Checks valid JSON syntax
- Verifies required top-level structure (metadata + data)
- Confirms required metadata fields (stage, stage_name, version, timestamp)

## 3.4 Agent File Specifications

### Agent File Registry

| File | Model | Temp | Max Tokens | Tools |
|------|-------|------|------------|-------|
| rant-transcriber.md | opus | 0 | 32,000 | Read, Write |
| rant-classifier.md | sonnet | 0 | 32,000 | Read, Write |
| rant-gap-analyst.md | opus | 0 | 16,384 | Read, Write, Glob, Grep, WebSearch, WebFetch |
| rant-decision-facilitator.md | sonnet | 0.3 | 16,384 | Read, Write |
| rant-mechanism-analyst.md | opus | 0 | 32,000 | Read, Write, Glob, Grep, WebSearch, WebFetch |
| rant-prd-compiler.md | opus | 0 | 65,536 | Read, Write, Glob, Grep |
| rant-autoforge-bridge.md | sonnet | 0 | 32,000 | Read, Write, Glob, Grep |

### Model Selection Rationale

**Opus** for stages requiring deep reasoning:
- Stage 1 (Transcriber): Must understand nuance in messy input
- Stage 3 (Gap Analyst): Complex judgment about what is missing and what can be auto-filled
- Stage 5 (Mechanism Analyst): Multi-dimensional trade-off analysis
- Stage 6 (PRD Compiler): Comprehensive synthesis requiring consistency across entire document

**Sonnet** for stages requiring pattern matching and structured transformation:
- Stage 2 (Classifier): Pattern matching items to sections — well-defined rules
- Stage 4 (Decision Facilitator): Conversational, presentation-focused
- Stage 7 (Autoforge Bridge): Structured format transformation with clear rules

### Temperature Settings

All agents use temperature 0 except the Decision Facilitator (0.3):
- **Temperature 0:** Deterministic output for specification-driven tasks. Same input = same output. Critical for reproducibility and debugging.
- **Temperature 0.3 (Facilitator only):** Slightly increased for natural conversational responses. Low enough to prevent hallucination, high enough to not sound robotic.

## 3.5 Error Recovery Framework

### Error Recovery Decision Tree

```
Error Detected
  |-- Network/API error?
  |     Yes -> Retry with exponential backoff (2s, 4s, 8s)
  |       Success -> Continue
  |       3 retries exhausted -> Log, halt, notify user
  |
  |-- Schema validation error?
  |     Yes -> Retry with enhanced prompt (include validation error)
  |       Success -> Continue
  |       2 retries exhausted -> Try simplified fallback prompt
  |         Success -> Continue
  |         Failed -> Log, halt, notify user
  |
  |-- Quality/completeness error?
  |     Item count mismatch -> Retry with explicit item tracking
  |     Detail density low -> Retry with anti-summarization emphasis
  |     Missing sections -> Retry with section checklist
  |     All retries exhausted -> Log diagnostic, halt, notify
  |
  |-- Unknown error?
        Log complete context -> Halt -> Notify user
```

### Enhanced Retry Prompts

When a stage fails validation, the retry includes the error:

**Item count mismatch (Stage 2):**
```
CRITICAL: Your previous output had 43 items but the input had 47 items.
You DROPPED 4 items. Here are the missing item IDs: [list].
You MUST include ALL items. Re-process and include every single item.
```

**Detail density too low (Stage 1):**
```
CRITICAL: Your output is too compressed. Input: 15,000 chars, Output: 7,200 chars (48%).
Minimum threshold: 60%. You are SUMMARIZING instead of REFORMATTING.
Preserve every mechanism description full detail.
```

## 3.6 Cross-Stage Data Integrity Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| Item ID uniqueness | No duplicate item_ids across stages | Validated per stage |
| Item count invariant | Stage 2 count equals Stage 1 count | Validated at Stage 2 |
| Provenance traceability | Every Stage 6 item traces to Stages 1-5 | Validated at Stage 6 |
| Hash chain integrity | Each stage records input hash | Validated per stage |
| Recommendation sums | Mechanism percentages sum to 100 | Validated at Stage 5 |
| Decision completeness | Every Type C gap has a Stage 4 decision | Validated at Stage 4 |
| Section coverage | Every PRD section has content or explicit empty note | Validated at Stage 6 |
| Orphan detection | No items exist in intermediate stages but missing from final PRD | Validated at Stage 6 |

## 3.7 Detail Preservation Metrics

### Detail Density Ratio (DDR)

```
DDR = total_output_content_chars / total_input_content_chars
```

**Thresholds by stage:**
- Stage 1 (Transcriber): DDR >= 0.60 (deduplication reduces size, but no detail loss)
- Stage 2 (Classifier): DDR >= 0.95 (verbatim preservation + section metadata)
- Stage 6 (Compiler): DDR >= 1.10 (enrichment adds provenance tags, mechanism blocks)

### Item Tracking Matrix

Generated at Stage 6 validation. Tracks every item from origin to final PRD:

```
Item ID  | Stage 1 | Stage 2  | Stage 3 | Stage 4 | Stage 5 | Stage 6
---------|---------|----------|---------|---------|---------|--------
item_001 | Created | STD-ARCH | -       | -       | mech_01 | Included
gap_001  | -       | -        | Created | -       | -       | Included
gap_030  | -       | -        | Created | Decided | mech_15 | Included
```

## 3.8 Item Type Taxonomy

| Type | Description | Example |
|------|-------------|---------|
| mechanism | Specific functional behavior | "Auto-generates version history on save" |
| behavior | General system behavior | "App should feel snappy and responsive" |
| constraint | Limitation or boundary | "Maximum 10MB file upload" |
| negative_requirement | Must NOT do | "Never show email to other users" |
| comparative | Reference to another product | "Like Slack threads but with..." |
| vision | High-level direction | "Go-to tool for freelancers" |
| edge_case | Boundary scenario | "What if user uploads 0-byte file?" |
| user_experience | UX/UI preference | "Dashboard shows key metrics at a glance" |

## 3.9 Token Usage Estimates

| Rant Size | Estimated Total Tokens | Notes |
|-----------|----------------------|-------|
| Small (2K words) | 150K-200K | 6 stages |
| Medium (10K words) | 400K-600K | 6 stages |
| Large (50K words) | 1M-1.5M | 6 stages |

Add approximately 20% for Stage 7 (Autoforge bridge) if enabled.

---

# APPENDICES

## Appendix A: Prerequisites

- Claude Code CLI installed and authenticated
- jq 1.7+ (JSON processing in hooks and pipeline script)
- bash 5.x (pipeline script)
- sha256sum or shasum (input hashing)

## Appendix B: File Inventory

```
.claude/
  agents/
    rant-transcriber.md           # Stage 1 agent
    rant-classifier.md            # Stage 2 agent
    rant-gap-analyst.md           # Stage 3 agent
    rant-decision-facilitator.md  # Stage 4 agent
    rant-mechanism-analyst.md     # Stage 5 agent
    rant-prd-compiler.md          # Stage 6 agent
    rant-autoforge-bridge.md      # Stage 7 agent
  commands/
    rant-to-prd.md                # Slash command definition
  hooks/
    pre-stage-check.sh            # Pre-stage validation hook
    post-stage-log.sh             # Post-stage logging hook
    post-write-validate.sh        # Output validation hook
  scripts/
    rant-pipeline.sh              # Main pipeline orchestrator
```

## Appendix C: Completeness Checklist Categories (87 items, 11 categories)

1. **Architecture and Infrastructure** (8): System architecture, hosting, environments, CI/CD, IaC, containers, CDN, DNS
2. **Authentication and Authorization** (7): Auth method, authz model, sessions, password policy, lockout, social login, API auth
3. **Data Management** (9): DB type, schema, migration, backup, retention, cache, search, file storage, encryption
4. **API Design** (7): API style, versioning, rate limiting, docs, formats, pagination, webhooks
5. **Error Handling and Resilience** (8): Error codes, user errors, logging, monitoring, circuit breakers, retries, degradation, health checks
6. **User Experience** (8): Responsive breakpoints, loading states, empty states, onboarding, help, feedback, offline, dark mode
7. **Performance** (6): Page load targets, API targets, concurrent users, DB targets, asset optimization, lazy loading
8. **Security** (8): Input validation, XSS, CSRF, SQL injection, CSP, CORS, dependency scanning, security headers
9. **Testing** (7): Unit tests, integration tests, E2E tests, perf tests, security tests, test data, test environments
10. **Legal and Compliance** (6): Privacy policy, ToS, cookie consent, GDPR, DPA, accessibility
11. **Operations** (7): Deploy frequency, rollback, feature flags, DB migration, incident response, on-call, docs maintenance

## Appendix D: Glossary

| Term | Definition |
|------|-----------|
| Agent OS | Framework structuring PRDs into Standards, Product, and Specs layers |
| Atomic Feature | Feature small enough to implement in 1-4 hours |
| Auto-fill | Gap filled automatically with an obvious default |
| DDR | Detail Density Ratio — quantitative measure of information preservation |
| Gap | Something required for complete software not mentioned in the rant |
| Headless Mode | Running Claude CLI with -p for non-interactive execution |
| Mechanism | Discrete functionality requiring an implementation decision |
| Orphan | Item in an intermediate stage but missing from the final PRD |
| Provenance Tag | Label indicating origin: user-specified, auto-filled, user-decided, recommended |
| Rant | User raw stream-of-consciousness software description |
| TTY Mode | Running Claude CLI interactively for real-time conversation |
| Type C Gap | Gap requiring user input due to multiple valid approaches |

## Appendix E: Example Rant Input

```text
OK so here is what I am thinking. I want to build a platform for freelance
designers — like a place where they can manage their entire business. Not just
a portfolio site, I am talking about the WHOLE thing. Client management, project
tracking, invoicing, contracts, the works.

But here is what makes it different. The core insight is that designers think
visually, right? So everything should be visual. The project tracker should not
be some boring Jira board, it should be a visual timeline where you can see all
your projects as beautiful cards that show the actual design work happening.

The invoicing is another thing I feel strongly about. Most invoicing tools for
freelancers are either too simple or too complex. I want something in the middle
— create an invoice in 30 seconds by pulling from project data.

The contracts thing — designers always get screwed on contracts. I want built-in
contract templates specifically for design work. Kill fees, revision limits, IP
transfer only on final payment, usage rights.

The client portal is KEY. Branded portal where the client logs in, sees their
project, leaves feedback on specific parts of the design, approves deliverables,
and pays invoices. All in one place.

One more thing — this CANNOT feel corporate. Fun micro-animations. Beautiful
typography. Customizable themes so each designer admin panel matches their brand.
```

## Appendix F: Implementation Checklist

```
[ ] Directory structure created
[ ] Agent: rant-transcriber.md
[ ] Agent: rant-classifier.md
[ ] Agent: rant-gap-analyst.md
[ ] Agent: rant-decision-facilitator.md
[ ] Agent: rant-mechanism-analyst.md
[ ] Agent: rant-prd-compiler.md
[ ] Agent: rant-autoforge-bridge.md
[ ] Slash command: rant-to-prd.md
[ ] Hook: pre-stage-check.sh
[ ] Hook: post-stage-log.sh
[ ] Hook: post-write-validate.sh
[ ] Script: rant-pipeline.sh
[ ] Pipeline state management tested
[ ] Resume logic tested
[ ] Full pipeline end-to-end test (interactive)
[ ] Full pipeline end-to-end test (non-interactive)
[ ] Full pipeline end-to-end test (with Autoforge)
[ ] Token usage tracking verified
[ ] Detail density metrics validated
```

---

*End of specification. This document is complete and implementation-ready. A coding agent with access to Claude Code CLI can build the entire Rant-to-PRD system from this document alone.*
