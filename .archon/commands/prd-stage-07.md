# Stage 7: Phase Sequencing

You are a phase sequencing specialist. Your job is to split the complete spec into buildable phases with token budgets, file sandboxes, and forced build orders.

## Input

Read `$ARTIFACTS_DIR/context_packet.json`. You need `stage_4.mechanisms`, `stage_4.mechanism_dependencies`, `stage_5.mechanism_blueprints`, and `stage_0.token_budget`.

## Process

### Step 1: Estimate Token Count Per Mechanism

Use these sizing guidelines:
- Simple mechanism (basic CRUD, auth with standard provider): 15K-25K tokens
- Medium mechanism (search with filters, payment flow): 30K-60K tokens
- Complex mechanism (real-time collaboration, ML pipeline): 60K-120K tokens
- Per-page UI tokens: 5K-15K depending on complexity

### Step 2: Calculate Phase Count

```
total_budget = 500K tokens (50% of 1M context)
overhead_per_phase = 25K tokens
budget_per_phase_content = 325K tokens
phases_needed = ceil(total_estimated / 325K)
```

Minimum 2 phases. Maximum 10 phases.

### Step 3: Find Natural Break Points

Topological sort by mechanism dependencies. Walk the graph and accumulate tokens. Rules:
- NEVER split a mechanism across phases
- Keep tightly-coupled mechanisms together
- Phase 1 is always foundation: project setup, core data models, basic UI shell
- Each subsequent phase builds on the previous

### Step 4: Assign File Sandboxes Per Phase

Three tiers per phase:
- `files_allowed`: Files this phase creates or modifies
- `files_read_only`: Files this phase can reference but not change
- `files_forbidden`: Everything else — touching these is a violation

Global `do_not_change` files (never modified by any phase): `CLAUDE.md`, `.env`, `BUILD_RULES.md`

### Step 5: Define Build Order Per Phase

Four-layer forced sequence within each phase:
1. Core logic (models, schemas, services)
2. State management (stores, context, hooks)
3. UI components (pages, components, layouts)
4. Integration (API routes, webhooks, connections)

Every file gets a build order number and a rationale.

### Step 6: Define Phase Dependencies

Phase 1 always has `depends_on: []`. Default is sequential (Phase 2 depends on Phase 1). Parallel only if zero shared dependencies.

### Step 7: Verify Fit

Confirm: `estimated_tokens + 25K overhead <= 350K` per phase. If any phase exceeds, split it.

## Output

Update `$ARTIFACTS_DIR/context_packet.json` — add `stage_7`:

```json
{
  "stage_7": {
    "total_estimated_tokens": 0,
    "phase_count": 0,
    "phases": [
      {
        "phase_number": 1,
        "name": "Foundation",
        "mechanism_ids": ["mech_001", "mech_002"],
        "estimated_tokens": 0,
        "depends_on": [],
        "build_order": [
          {"file": "src/lib/db/schema.ts", "order": 1, "layer": "core_logic", "rationale": "..."}
        ],
        "files_allowed": [],
        "files_read_only": [],
        "files_forbidden": ["*"]
      }
    ],
    "global_do_not_change": ["CLAUDE.md", ".env", "BUILD_RULES.md"],
    "stage_contract": "pass"
  }
}
```

IMPORTANT: Read existing context_packet.json, merge stage_7, increment version to 7, write back.
