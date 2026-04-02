# Phase 1D: Context Packet Schema

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Estimated effort:** Single session
> **Output:** `docs/page-prds/prd-maker/context-packet-schema.md`

---

## Your Mission

You are designing the data schema for the **context packet** -- the JSON data object that flows through all 10 stages of the PRD Maker pipeline. Every stage reads some fields, writes some fields, and passes the complete packet to the next stage. The context packet IS the pipeline's memory. Without a precise schema, stages will write data in formats the next stage cannot parse, fields will be missing, and the pipeline will break.

Think of it as designing the database schema for a 10-step assembly line. Every station on the line reads the card, adds its work, and passes it forward. Your job is to define exactly what is on that card at every step.

---

## Files to Read (In This Order)

Read ALL of these files completely before designing anything:

1. **`docs/page-prds/prd-maker/stage-extractions/stage-01-extraction.md`** -- Stage 1: Idea Capture
2. **`docs/page-prds/prd-maker/stage-extractions/stage-02-extraction.md`** -- Stage 2: Gap Analysis
3. **`docs/page-prds/prd-maker/stage-extractions/stage-03-extraction.md`** -- Stage 3: Agent OS Structuring
4. **`docs/page-prds/prd-maker/stage-extractions/stage-04-extraction.md`** -- Stage 4: Mechanism Extraction
5. **`docs/page-prds/prd-maker/stage-extractions/stage-05-extraction.md`** -- Stage 5: 7-Question Scaffolding
6. **`docs/page-prds/prd-maker/stage-extractions/stage-06-extraction.md`** -- Stage 6: Layout + Mockups + Style
7. **`docs/page-prds/prd-maker/stage-extractions/stage-07-extraction.md`** -- Stage 7: Phase Sequencing
8. **`docs/page-prds/prd-maker/stage-extractions/stage-08-extraction.md`** -- Stage 8: Protocol Injection
9. **`docs/page-prds/prd-maker/stage-extractions/stage-09-extraction.md`** -- Stage 9: Verification Agent Setup
10. **`docs/page-prds/prd-maker/stage-extractions/stage-10-extraction.md`** -- Stage 10: Output Generator

11. **`docs/page-prds/prd-maker/build-game-plan.md`** -- Read the sections on: "Context Packet Version Control," "Escape Hatch Protocol," "Confidence Gate," and the overview of the pipeline. Also read section "1E. Define Context Packet Schema" for confirmation.

12. **`docs/page-prds/prd-maker/research-reference.md`** -- Read "The 10-Stage Pipeline" overview and "The 30-Category Master Checklist" for additional structure.

13. **`docs/page-prds/prd-maker/mechanism-identification-framework.md`** -- The A-N mechanism categories. The context packet must have a place to store mechanism data (used by Stages 2, 4, 5).

---

## What You Are Designing

A complete schema specification for the `context_packet` object. This document defines:

1. The full JSON schema with every field, its type, whether it is required or optional, and validation rules
2. A stage-by-stage read/write map showing exactly which fields each stage reads and writes
3. Version control rules for how snapshots are saved between stages
4. The escape hatch data format for when a stage fails

---

## Schema Design Principles

Follow these principles when designing the schema:

### 1. Additive Only
Stages ONLY ADD data to the context packet. No stage is allowed to DELETE or OVERWRITE data written by a previous stage. If a stage needs to modify something, it writes a new field (e.g., `mechanisms_raw` from Stage 4 and `mechanisms_classified` from Stage 5) rather than overwriting `mechanisms`.

### 2. Namespaced by Stage
Each stage writes to its own namespace in the packet. This prevents collisions and makes it clear which stage produced which data.

```json
{
  "metadata": { ... },
  "stage_0": { ... },
  "stage_1": { ... },
  "stage_2": { ... },
  ...
  "stage_10": { ... }
}
```

### 3. Self-Describing
The packet always carries its own metadata: what pipeline version created it, what stage it is currently at, timestamps for each stage completion, and confidence scores.

### 4. Serializable
Everything in the packet must be JSON-serializable. No functions, no class instances, no circular references. Plain objects, arrays, strings, numbers, booleans, and null only.

### 5. Recoverable
If the pipeline crashes at Stage N, the packet saved after Stage N-1 must contain everything needed to restart Stage N from scratch.

---

## Required Schema Sections

### Section 1: `metadata`

This section exists from the very start (before Stage 0) and is updated by every stage:

```
metadata.pipeline_version    -- string, semver of the pipeline that created this packet
metadata.created_at          -- ISO 8601 timestamp, when the pipeline run started
metadata.updated_at          -- ISO 8601 timestamp, last modification
metadata.current_stage       -- integer 0-10, which stage is currently running or was last completed
metadata.status              -- enum: "in_progress" | "completed" | "failed" | "needs_human"
metadata.app_type            -- enum: "greenfield" | "existing" (future support)
metadata.archetype_matches   -- array of strings, matched archetypes from Stage 2
metadata.confidence_scores   -- object keyed by stage number, each value is {score: number, dimensions: {...}}
metadata.stage_timestamps    -- object keyed by stage number, each value is ISO 8601 completion timestamp
metadata.escape_hatches      -- array of escape hatch records (see Escape Hatch section below)
```

### Section 2: `stage_0` -- Technical Foundation (Stage 0)

Stage 0 establishes the platform context. This is the "preamble" data.

Design fields for:
- Selected platform/boilerplate (or "no boilerplate")
- Technology stack decisions (framework, database, auth provider, hosting)
- The agnostic checklist rules that apply (reference, not full content)
- Any project-specific command allowlist

### Section 3: `stage_1` -- Idea Capture

Design fields for:
- Raw user input (the complete, unedited brain dump)
- Input format (voice transcript, typed notes, etc.)
- Timestamp of capture
- Word count / length indicator
- Any explicit contradictions the user stated and then corrected

### Section 4: `stage_2` -- Gap Analysis

Design fields for:
- Matched archetype(s) and confidence
- Mechanism categories identified from the raw input (A-N, with which sub-types)
- Mechanism categories NOT mentioned (gaps)
- Questions asked to fill gaps
- User's answers to gap questions
- Combined raw input + gap answers (the complete picture, still unstructured)
- Confidence score for overall completeness

### Section 5: `stage_3` -- Agent OS Structuring

Design fields for the 4 output sections from Stage 3:
- Concept and Context (product identity, one-line description, name)
- Target User and Market (personas, market context, competitive landscape)
- Feasibility Assessment
- Problem Statement
- Any ambiguities that were resolved (what was ambiguous, how it was resolved)

### Section 6: `stage_4` -- Mechanism Extraction

Design fields for:
- List of discrete mechanisms extracted
- Each mechanism tagged as OBVIOUS (one standard approach) or NEEDS_EVALUATION
- For NEEDS_EVALUATION mechanisms: the competing approaches and their evaluation criteria
- For mechanisms within 15% performance parity: both approaches preserved for branch testing
- Dependencies between mechanisms

### Section 7: `stage_5` -- 7-Question Scaffolding

Design fields for:
- Each mechanism's 7-question answers
- Each step classified as WALL (deterministic), DOOR (constrained AI), or ROOM (creative freedom)
- Preconditions and outcome mappings
- Verification methods per step
- Skip conditions

### Section 8: `stage_6` -- Layout + Mockups + Style

Design fields for three sub-stages:
- 6a: Selected arrangement/wireframe pattern, app type classification
- 6b: Per-page mockup data (page name, layout, components, mechanism connections)
- 6c: Selected style (from curated options), design tokens, color palette, typography

### Section 9: `stage_7` -- Phase Sequencing

Design fields for:
- Token budget calculation (total spec tokens, phases needed)
- Phase list with: phase number, name, files included, estimated tokens, build order
- File sandbox assignments per phase (ALLOWED, READ-ONLY, FORBIDDEN)
- Mandatory build order constraints
- DO NOT CHANGE protections

### Section 10: `stage_8` -- Protocol Injection

Design fields for:
- Pulse check configuration (frequency, what to check)
- Seam check points (which components connect, what to verify)
- Full checkpoint configuration (what to run at phase boundaries)
- Violation handling rules (LOW/MEDIUM/HIGH/CRITICAL thresholds and responses)

### Section 11: `stage_9` -- Verification Agent Setup

Design fields for:
- Verification mode (automated Agent B or manual preamble merge)
- Checker configuration
- Git diff verification rules
- Two-strike rule configuration
- What gets checked per phase

### Section 12: `stage_10` -- Output Generator

Design fields for:
- Output file manifest (list of files to generate with paths)
- Generated file contents or references
- Build script configuration
- CLAUDE.md content
- BUILD_RULES.md content
- Final validation results

---

## Stage Read/Write Map

Create a table showing exactly which fields each stage READS and WRITES:

| Stage | Reads | Writes |
|-------|-------|--------|
| 0 | (none -- first stage) | `metadata`, `stage_0.*` |
| 1 | `stage_0.platform_profile` | `stage_1.*`, `metadata.current_stage`, `metadata.confidence_scores.1` |
| 2 | `stage_1.raw_input`, `stage_0.platform_profile` | `stage_2.*`, `metadata.archetype_matches`, `metadata.confidence_scores.2` |
| ... | ... | ... |

Every field that a stage reads must have been written by a PREVIOUS stage. If Stage 5 reads a field, that field must be written by Stage 0, 1, 2, 3, or 4. Never forward-reference.

---

## Version Control

Define the snapshot protocol:

- After each stage completes, save a snapshot: `context_packet_v{N}.json` where N is the stage number
- Snapshots are immutable -- never overwrite a snapshot
- If Stage N needs to be re-run, load `context_packet_v{N-1}.json` and re-run Stage N
- The "current" working copy is `context_packet.json` (always the latest)
- Include a `_snapshot_metadata` field in each snapshot with: stage number, timestamp, pipeline version, confidence score

---

## Escape Hatch Data Format

When a stage fails and triggers the escape hatch, it must save:

```json
{
  "escape_hatch": {
    "stage": 4,
    "timestamp": "2026-04-02T14:30:00Z",
    "status": "NEEDS_HUMAN",
    "progress": "Extracted 6 of 9 mechanisms. Stuck on mechanism #7.",
    "problem": "User described a 'smart matching algorithm' but provided no criteria for what 'smart' means. Cannot classify as OBVIOUS or NEEDS_EVALUATION without knowing the matching dimensions.",
    "attempted": ["Asked follow-up question about matching criteria", "Searched description for implicit criteria"],
    "partial_output": { ... },
    "suggested_actions": [
      "Ask user: What factors determine a good match?",
      "Ask user: Can you give an example of a good match and a bad match?"
    ],
    "resume_from": "mechanism_7_classification"
  }
}
```

Define the complete escape hatch schema with all required fields.

---

## Future Support: Existing App Path

The schema must support a future `app_type: "existing"` mode. For now, just include placeholder fields in `stage_0` for:
- Codebase analysis results (file tree, framework detection, dependency list)
- Existing feature inventory
- Martin's checklist in CHECK mode (which rules are already followed)
- Mechanisms that already exist vs new ones

Mark these as `optional` and note they are for future use.

---

## Output File Structure

Create: **`docs/page-prds/prd-maker/context-packet-schema.md`**

The file should contain:

1. **Overview** -- What the context packet is, design principles, how it flows through stages
2. **Full JSON Schema** -- Complete schema with types, required/optional, validation rules, descriptions
3. **Stage Read/Write Map** -- Table showing what each stage reads and writes
4. **Version Control Protocol** -- Snapshot naming, immutability rules, rollback procedure
5. **Escape Hatch Schema** -- Complete data format for stage failures
6. **Future: Existing App Support** -- Placeholder fields documented
7. **Example** -- A small example showing what the context packet looks like after Stage 2 completes (with realistic sample data for a "task manager app")

---

## Quality Checks Before You Finish

1. **No forward references:** For every field a stage READS, verify that a previous stage WRITES it. Draw the dependency chain.
2. **No orphan fields:** Every field that gets WRITTEN must be READ by at least one downstream stage (or be part of the final output). If nobody reads it, why is it there?
3. **Type consistency:** If a field is a string in Stage 2's output, it must still be a string when Stage 5 reads it. No implicit type changes.
4. **Escape hatch is complete:** The escape hatch schema must capture enough information for a human to understand what happened and for the pipeline to resume.
5. **Example validates schema:** The example context packet (after Stage 2) must conform to the schema you defined. Check every field against the schema.

---

## Success Criteria

- [ ] Output file exists at `docs/page-prds/prd-maker/context-packet-schema.md`
- [ ] Complete JSON schema with all fields, types, required/optional, and descriptions
- [ ] All 11 stages (0-10) have their own namespace in the schema
- [ ] Stage read/write map is complete for all stages with specific field names
- [ ] No forward references in the read/write map
- [ ] Version control protocol is defined (snapshot naming, immutability, rollback)
- [ ] Escape hatch schema is complete with all required fields
- [ ] Future "existing app" placeholder fields documented
- [ ] Example context packet (after Stage 2) included with realistic sample data
- [ ] metadata section tracks pipeline version, timestamps, confidence scores, and status
- [ ] Schema follows the 5 design principles (additive only, namespaced, self-describing, serializable, recoverable)
