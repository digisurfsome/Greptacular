# Codebase Plan: Enrich PRD with Implementation Intelligence

Based on Cole's Plan cookbook. You take the PRD output and enrich it with codebase-specific patterns, code snippets, and a file-by-file implementation plan.

## Input

Read `$ARTIFACTS_DIR/context_packet.json` — you need all stages.
Read all phase files in `$ARTIFACTS_DIR/phases/` using Glob.
Read `$ARTIFACTS_DIR/CLAUDE.md` and `$ARTIFACTS_DIR/BUILD_RULES.md`.

## Process

### Step 1: Explore the Codebase
Use Glob, Grep, and Read tools to explore the target project codebase:
- Find similar features already implemented
- Identify naming conventions with actual examples
- Map error handling and logging patterns
- Find type definitions and test patterns
- Document configuration and dependencies

### Step 2: Build Discovery Table

| Category | File:Lines | Pattern Description | Code Snippet |
|----------|-----------|---------------------|--------------|
| NAMING | `path:10-15` | Convention used | `actual code` |
| ERRORS | `path:5-20` | Error pattern | `actual code` |
| TESTS | `path:1-30` | Test structure | `actual code` |
| TYPES | `path:1-10` | Type definitions | `actual code` |

### Step 3: Create Patterns to Mirror
For each phase, identify 2-5 code patterns from the existing codebase that the builder should copy. Include ACTUAL code snippets with file:line references.

```
PATTERN: {name}
SOURCE: {file}:{lines}
{actual code from the codebase}
```

### Step 4: Enrich Phase Files
For each phase file from the PRD output:
- Add "Patterns to Mirror" section with actual code snippets
- Add "Mandatory Reading" with P0/P1/P2 priority files
- Add per-file implementation details referencing existing patterns
- Add "Gotchas" — known issues to avoid based on codebase patterns

### Step 5: NO_PRIOR_KNOWLEDGE_TEST
Review each enriched phase file and ask: "Could an agent unfamiliar with this codebase implement using ONLY this plan?" If not, add more context.

### Step 6: Decision Log
Document every implementation decision:
| Decision | Choice | Alternatives | Rationale |

## Output

Write enriched phase files to `$ARTIFACTS_DIR/phases/phase-N-enriched.md`.
Write the discovery table to `$ARTIFACTS_DIR/discovery-table.md`.
Update context_packet.json with `codebase_plan` section including patterns found and confidence score.
