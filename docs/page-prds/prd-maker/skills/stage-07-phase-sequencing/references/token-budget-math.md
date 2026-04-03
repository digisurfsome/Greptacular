# Token Budget Math — Phase Sequencing Reference

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| Total context window | 1,000,000 tokens | Claude 1M context |
| Total budget for spec content | 500,000 tokens | 50% of context — other 50% is agent working memory, tools, system prompts |
| Overhead per phase | 25,000 tokens | Fixed templated content (see breakdown below) |
| Content budget per phase | 325,000 tokens | 350,000 target minus 25,000 overhead |
| Target per phase (total) | 350,000 tokens | 35% of context — significant headroom below the 50% ceiling |

## Overhead Breakdown (Per Phase)

| Component | Tokens | Purpose |
|-----------|--------|---------|
| Build rules preamble | ~8,000 | Martin's structural rules, DO NOT CHANGE protections |
| File sandbox declaration | ~2,000 | ALLOWED / READ-ONLY / FORBIDDEN lists |
| Build order with pulse points | ~3,000 | Forced linear sequence with pulse check markers |
| Seam check definitions | ~2,000 | Connection-point verification rules |
| Full checkpoint at end | ~5,000 | End-of-phase pattern + functional verification |
| Pattern verification prompt | ~3,000 | Instructions for verifying build patterns |
| Violation handling | ~2,000 | Severity rules and escalation protocol |
| **Total** | **~25,000** | |

This overhead is predictable because it is templated. The preamble is the same text every time (with project-specific file lists swapped in). This allows advance calculation — account for overhead BEFORE splitting, not after.

## Phase Count Formula

```
phases_needed = ceil(total_spec_tokens / budget_per_phase_content)
             = ceil(total_spec_tokens / 325,000)
```

## Token Estimation Heuristics

### Per-Mechanism Estimates

| Complexity | Characteristics | Token Range |
|------------|----------------|-------------|
| Simple | 1–2 files, WALL-dominant, single concern | 15,000–25,000 |
| Medium | 3–5 files, mixed W/D/R, 2–3 connected components | 30,000–60,000 |
| Complex | 6+ files, DOOR/ROOM-heavy, integrations, multi-page | 60,000–120,000 |

### Per-Page UI Estimates (from Stage 6b)

| Page Type | Token Range |
|-----------|-------------|
| Simple static page (about, settings) | 5,000–8,000 |
| Form page (sign in, create item) | 8,000–12,000 |
| Dashboard / data-heavy page | 12,000–20,000 |
| Complex interactive page (editor, kanban) | 20,000–40,000 |

### Additional Content Estimates

| Content Type | Token Range |
|-------------|-------------|
| Database schema / migration | 3,000–8,000 per table |
| API route / endpoint | 5,000–10,000 per route |
| Shared utility / helper library | 3,000–6,000 per file |
| Type definitions | 2,000–5,000 per domain area |

## Worked Examples

### Example 1: Small App (1 Phase)

```
Mechanisms:
  M1 Auth (simple):     20,000 tokens
  M2 Profile (simple):  18,000 tokens
  M3 Settings (simple): 15,000 tokens
Total:                  53,000 tokens

phases_needed = ceil(53,000 / 325,000) = 1

Phase 1: 53,000 content + 25,000 overhead = 78,000 total
78,000 ≤ 350,000 ✓
```

### Example 2: Medium App (2 Phases)

```
Mechanisms:
  M1 Auth (medium):         45,000 tokens
  M2 Tasks CRUD (complex):  90,000 tokens
  M3 Dashboard (complex):   80,000 tokens
  M4 Notifications (medium):50,000 tokens
  M5 Search (medium):       40,000 tokens
  M6 Settings (simple):     20,000 tokens
Total:                     325,000 tokens

phases_needed = ceil(325,000 / 325,000) = 1

But check fit: 325,000 + 25,000 = 350,000 ≤ 350,000 ✓ (exactly at limit)
Keep as 1 phase, OR split to 2 for safety margin.

If split to 2:
  Phase 1 (M1+M2+M3): 215,000 + 25,000 = 240,000 ≤ 350,000 ✓
  Phase 2 (M4+M5+M6): 110,000 + 25,000 = 135,000 ≤ 350,000 ✓
```

### Example 3: Large App (3 Phases)

```
Mechanisms:
  M1 Auth (complex):           100,000 tokens
  M2 Payments (complex):       110,000 tokens
  M3 Content Editor (complex): 120,000 tokens
  M4 Analytics (complex):       95,000 tokens
  M5 Social (medium):           60,000 tokens
  M6 Admin Panel (complex):     80,000 tokens
  M7 Notifications (medium):    45,000 tokens
  M8 Search (medium):           40,000 tokens
Total:                         650,000 tokens

phases_needed = ceil(650,000 / 325,000) = 2

Check fit with 2 phases:
  Best split: M1+M2+M3 = 330,000 → 330,000 + 25,000 = 355,000 > 350,000 ✗
  Adjusted: M1+M2 = 210,000 → 210,000 + 25,000 = 235,000 ✓
            M3+M4+M5+M6+M7+M8 = 440,000 → 440,000 + 25,000 = 465,000 > 350,000 ✗

Need 3 phases:
  Phase 1 (M1+M2):       210,000 + 25,000 = 235,000 ✓
  Phase 2 (M3+M4):       215,000 + 25,000 = 240,000 ✓
  Phase 3 (M5+M6+M7+M8): 225,000 + 25,000 = 250,000 ✓

All phases ≤ 350,000 ✓
```

## Verification Checklist

After calculating phases:
- [ ] Every phase: `estimated_tokens + 25,000 ≤ 350,000`
- [ ] `sum(all phase estimated_tokens)` ≈ `total_spec_tokens` (±10%)
- [ ] `phases.length` ≈ `ceil(total_spec_tokens / 325,000)` (±1 for boundary adjustments)
- [ ] No mechanism split across phases
- [ ] No mechanism dropped (all mechanism IDs from Stage 4 appear in exactly one phase)
