# Build Planner — Script Assembly Handoff

## What You're Building
Bash scripts that call `claude` CLI to build the Build Planner page in phases. Each script is one phase of development.

## The 3-Layer System (every phase gets layers 1-2)

### Layer 1: Standards (goes in EVERY phase)
This is the "how to code" context. Copy the STANDARDS section from:
`.claude/specs/build-planner-one-pager.md`

### Layer 2: Product (goes in EVERY phase)
This is the "what we're building and why" context. Copy the PRODUCT section from:
`.claude/specs/build-planner-one-pager.md`

### Layer 3: Specs (gets DIVIDED across phases)
This is the "what to build in THIS phase" context. The SPECS section from:
`.claude/specs/build-planner-one-pager.md`
...gets sliced into chunks, one per phase.

## The Extra Rules (from the user)

### Phase 1 Extra Rules (~1,000 lines)
The user will provide ~1,000 lines of additional rules/standards. These go ONLY in the Phase 1 script, appended after the Standards + Product sections but before the Specs chunk.

### Phase 2+ Extra Rules (~350 lines)
The user will provide ~350 lines of additional rules. These go in EVERY phase EXCEPT Phase 1, appended after Standards + Product but before the Specs chunk.

## Token Budget
- **Target: under 100,000 tokens per phase script**
- Rule of thumb: 1 line ≈ 30-40 tokens, 1,000 lines ≈ 30-40k tokens
- Standards section: ~50 lines ≈ 2k tokens
- Product section: ~40 lines ≈ 1.5k tokens
- Phase 1 extra rules: ~1,000 lines ≈ 35k tokens
- Phase 2+ extra rules: ~350 lines ≈ 12k tokens

### Phase 1 budget math:
- Standards (~2k) + Product (~1.5k) + Extra Rules (~35k) = ~38.5k tokens of context
- That leaves ~61.5k tokens for the Specs chunk
- ~61.5k tokens ≈ 1,800 lines of spec content

### Phase 2+ budget math:
- Standards (~2k) + Product (~1.5k) + Extra Rules (~12k) = ~15.5k tokens of context
- That leaves ~84.5k tokens for the Specs chunk
- ~84.5k tokens ≈ 2,500 lines of spec content

### How many phases?
Look at the total SPECS section length. Phase 1 can hold ~1,800 lines of spec. Phase 2+ can each hold ~2,500 lines. Divide accordingly. The current spec is ~250 lines, so with the extra rules factored in, **it likely fits in 2-3 phases total**. But the user may expand the spec — size the phases based on actual content.

## Bash Script Template

Each phase script should look like this:

```bash
#!/bin/bash
# ===========================================
# Build Planner — Phase N of M
# ===========================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== Phase N of M: [Phase Summary] ==="
echo ""

claude --model sonnet --max-turns 25 --print "
# STANDARDS
[Paste Standards section here]

# PRODUCT
[Paste Product section here]

# RULES
[Phase 1: paste the 1,000-line rules here]
[Phase 2+: paste the 350-line rules here]

# SPECS — Phase N of M
[Paste this phase's slice of the Specs section here]

# TASK
You are building Phase N of M for the Build Planner feature in AutoForge/Greptacular.
Build ONLY what is specified in the SPECS section above. Do not skip ahead to later phases.
Read existing code before modifying anything. Follow patterns already established.

The project is at: $PROJECT_DIR
The UI source is at: $PROJECT_DIR/ui/src/
"

echo ""
echo "=== Phase N complete ==="
```

## Master Run Script

Also generate `run_all.sh`:

```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Build Planner: Full Build ==="
echo "Phases: M total"
echo ""

for i in $(seq 1 M); do
  echo ">>> Starting Phase $i of M"
  bash "$SCRIPT_DIR/phase${i}.sh"
  echo ">>> Phase $i complete"
  echo ""

  if [ "$1" != "--auto" ]; then
    read -p "Review Phase $i output, then press Enter to continue (or Ctrl+C to stop)..."
  fi
done

echo "=== All phases complete ==="
```

## Phase-Specific Rules (bake these into each script)

### Phase 1 rules (add to the prompt):
- "Create all new files listed in the spec's File Structure section"
- "Set up routing, navigation button, and page skeleton FIRST before building components"
- "Do NOT build backend/API — that's a later phase"
- "Every component must compile — no placeholder imports for things that don't exist yet"
- "Use mock data / local state for now — API integration comes later"

### Phase 2+ rules (add to the prompt):
- "Read ALL existing code from Phase 1 before writing anything"
- "Do NOT refactor or restructure Phase 1 code unless it's broken"
- "Follow the patterns and component structure already established"
- "Import from existing files — do not create duplicates"

## What the assembling agent should do:
1. Read `.claude/specs/build-planner-one-pager.md` for Standards, Product, and Specs
2. Receive the user's 1,000-line and 350-line rule documents
3. Calculate how many phases are needed to stay under 100k tokens each
4. Slice the Specs section at logical boundaries (the spec has natural section breaks)
5. Assemble each phase script using the template above
6. Generate `run_all.sh`
7. Save scripts to `scripts/build-planner/` directory
