# Stage 10: Output Generator

You are the output rendering engine. Your job is pure serialization — take all decisions from Stages 0-9 and render them into a copy-paste-ready file package. Zero design decisions remain at this point.

## Input

Read `$ARTIFACTS_DIR/context_packet.json`. You need ALL stages (0-5, 7-9).

## Process

### Step 1: Generate Phase Files

Create `$ARTIFACTS_DIR/phases/phase-N.md` for each phase. Each file has exactly 9 sections:

1. **Build Rules Preamble** (~8K tokens): Core engineering rules, forbidden patterns, required patterns
2. **File Sandbox Declaration** (~2K): `files_allowed`, `files_read_only`, `files_forbidden` lists
3. **Build Order with Pulse Points** (~3K): Ordered file list with verification checks after each
4. **Seam Check Definitions** (~2K): Cross-mechanism connection validations
5. **Objective and Feature Requirements**: What this phase builds, derived from mechanism blueprints
6. **Pattern References**: Wall/Door/Room classifications for each mechanism step in this phase. For each WALL, include the exact verification method. For each DOOR, include the constraints. For each ROOM, include the boundaries.
7. **Violation Handling Instructions** (~2K): The 4-level severity table for this phase
8. **Full Checkpoint at End** (~5K): The 4-step verification protocol
9. **Gate Condition**: "ALL FOUR STEPS MUST PASS BEFORE PROCEEDING TO NEXT PHASE"

### Step 2: Generate build.sh

Create `$ARTIFACTS_DIR/build.sh`:
- `set -e` (stop on any error)
- Per-phase block: git snapshot → pre-build validation → agent work placeholder → post-build validation → forbidden file detection via git diff → commit
- Two-strike retry logic
- Phase chaining with `&&` (never `;`)

### Step 3: Generate CLAUDE.md

Create `$ARTIFACTS_DIR/CLAUDE.md`:
- Product name and one-line description
- Tech stack summary
- Architecture principles (from structural rules)
- File structure map
- Modification rules (what can/cannot be changed)
- Testing protocol summary
- Under 500 lines total

### Step 4: Generate BUILD_RULES.md

Create `$ARTIFACTS_DIR/BUILD_RULES.md`:
- Debugging protocol (trace-first approach)
- Feature addition protocol
- Testing and verification rules
- Data access patterns
- Entity CRUD patterns
- Error handling standards

### Step 5: Generate README.md

Create `$ARTIFACTS_DIR/README.md`:
- Product name and description
- Tech stack
- How to install and run
- Phase overview (what each phase builds)
- Post-build checklist
- Deploy instructions (Railway/Vercel/Render)

### Step 5b: Generate .gitignore

Create `$ARTIFACTS_DIR/.gitignore`:
```
node_modules/
dist/
.env
*.db
*.sqlite
.DS_Store
```

### Step 5c: Generate .env.example

Create `$ARTIFACTS_DIR/.env.example` listing ALL required environment variables with placeholder values. Example:
```
DATABASE_URL=file:./dev.db
JWT_SECRET=change-me-to-a-random-string
PORT=3001
CORS_ORIGIN=http://localhost:5173
```

Derive the variable list from the tech stack and mechanisms. Auth mechanisms need JWT_SECRET. Database mechanisms need DATABASE_URL. Server mechanisms need PORT.

### Step 6: Final Validation

Before finishing, verify:
- Every mechanism from stage_4 appears in at least one phase file
- Every file in build orders resolves to a real path
- Every import reference between files is accounted for
- No phase exceeds token budget
- No open questions remain
- Zero references to content from other phases

## Output

Write all files to `$ARTIFACTS_DIR/`:
- `phases/phase-1.md` through `phases/phase-N.md`
- `build.sh`
- `CLAUDE.md`
- `BUILD_RULES.md`
- `README.md`
- `.gitignore`
- `.env.example`

Also update `$ARTIFACTS_DIR/context_packet.json` — add `stage_10`:

```json
{
  "stage_10": {
    "deliverables": {
      "phase_files": ["phases/phase-1.md", "..."],
      "build_script": "build.sh",
      "claude_md": "CLAUDE.md",
      "build_rules": "BUILD_RULES.md",
      "readme": "README.md"
    },
    "phase_count": 0,
    "total_files_in_build_orders": 0,
    "validation_passed": true,
    "stage_contract": "pass"
  }
}
```

IMPORTANT: This is the final production stage. Every file must be complete and self-contained. A builder agent should be able to pick up phase-1.md and start building with zero additional context.
