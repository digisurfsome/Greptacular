# Sonnet/Opus Build Optimization — The Golden Rule

**Status:** Active — All builds and agents MUST follow this
**Date:** 2026-03-12
**Authors:** Owner + Claude (Session 10)

---

## The Rule

**Sonnet does all the building. Opus only does targeted checkpoints.**

Opus is not 10x better than Sonnet at writing code. It's maybe 10-15% better. But it burns tokens 10x faster. The math is simple:

- **Opus budget:** ~5.7 hours/day on Max plan
- **Sonnet budget:** ~68 hours/day on Max plan
- **Ratio:** Sonnet has 12x more capacity

If you let Opus build AND review every phase, a 10-phase build eats your entire daily Opus budget. One build. Done for the day.

If Sonnet builds and Opus only checkpoints, that same build uses ~30 minutes of Opus. You can run 10 builds per day instead of 1.

---

## Two Pipeline Formats

### Format A: Standard (use for 95% of phases)

```
Sonnet builds it
    ↓
Robot tests it (lint, type check, build — zero tokens)
    ↓
Sonnet reviews it (reads own code, fixes issues)
    ↓
Next phase
    ↓
... repeat ...
    ↓
Every 3-4 phases: Opus batch checkpoint
    ↓
Sonnet fixes what Opus found
```

**Opus time per build:** ~30 minutes total (3-4 checkpoints)

**Use for:** UI components, CRUD endpoints, styling, forms, API routes, documentation, boilerplate, config files, migrations, simple business logic — basically everything.

### Format B: Opus-Bookended (use for ~5% of phases)

```
Opus designs the approach first (5 min — architecture only, no code)
    ↓
Sonnet builds it (implements Opus's design)
    ↓
Robot tests it (lint, type check, build — zero tokens)
    ↓
Sonnet reviews it
    ↓
Opus verifies this specific phase (5 min — targeted check)
```

**Opus time per phase:** ~10 minutes (design + verify)

**Use ONLY for these triggers:**

| Keyword in Phase | Why Opus Goes First |
|---|---|
| auth, login, session, password, OAuth | Security patterns — bad auth looks correct but has holes |
| payment, stripe, billing, transaction | Money code — one bug = real damage |
| encrypt, token, secret, API key | Crypto is subtle — wrong looks identical to right |
| database schema, data model, migration | Foundation — bad schema breaks everything on top |
| real-time, websocket, concurrent, race | Timing bugs — Sonnet misses race conditions |
| multi-service, microservice, orchestration | Service communication — wrong design = cascading failures |

**Everything else = Format A. No exceptions.**

---

## Three Presets

For any build tool (CLI Scripter, AutoForge, manual builds):

### `sonnet_blitz` — Zero Opus
- Sonnet builds, Sonnet reviews, robot tests
- Opus time: 0
- Use for: prototypes, throwaway code, simple CRUD apps, styling-only changes

### `sonnet_opus_light` — DEFAULT for all production builds
- Sonnet builds, Sonnet reviews, Opus batch checkpoint every 3-4 phases
- Format B for tagged phases (auth, payments, etc.)
- Opus time: ~30 min per 10-phase build

### `opus_led` — Full Opus (use sparingly)
- Opus designs architecture, Opus reviews every phase
- Opus time: 2-3 hours per build
- Use for: core infrastructure only (payment system, auth system, database layer)
- NEVER use for UI, styling, or standard features

---

## Role-to-Model Mapping

| Role | Default Model | When Opus Instead |
|---|---|---|
| Architect (designs structure) | Sonnet | Format B phases only |
| Coder (writes code) | Sonnet | Never — Sonnet always codes |
| Reviewer (reads code for bugs) | Sonnet | Opus batch checkpoint every 3-4 phases |
| Verifier (integration testing) | Sonnet first pass | Opus final sign-off (5 min) |
| Cartographer (documents codebase) | Sonnet | Never — documentation doesn't need Opus |

---

## Robot Steps (Zero Tokens, Always Run)

These happen automatically after every phase regardless of model:

1. `npm run lint` / `ruff check` — catches syntax and style issues
2. `npm run build` / `mypy` — catches type errors
3. `npm test` / `pytest` — runs existing test suites
4. `git diff --stat` — verify changes are scoped to the phase

Robot steps are deterministic. They cost nothing. They run every time. Never skip them.

---

## The Math

**Old way (Opus reviews every phase):**
- 10-phase build: 1 Architect + 10 Reviews + 1 Verify = 12 Opus sessions
- 12 sessions × 20 min = 240 min = 4 hours Opus
- Daily Opus budget: 5.7 hours
- Builds per day: **1** (with 1.7 hours left for chat)

**New way (Sonnet builds, Opus checkpoints):**
- 10-phase build: 3 batch checkpoints + 1 final sign-off = 4 Opus sessions
- 4 sessions × 8 min average = 32 min Opus
- Daily Opus budget: 5.7 hours
- Builds per day: **10** (with hours left for chat)

**10x improvement. Same quality. Same subscription cost.**

---

## Token Tracking Requirements

Every build MUST log:
- Model used per agent/phase (sonnet/opus/haiku)
- Session duration per agent/phase
- Token count per session (input + output) if available
- Running daily total per model
- Percentage of daily budget consumed

This data feeds the rate limit dashboard and helps optimize preset selection over time.

---

## For PRD Makers

When creating a PRD with phased builds:

1. Default every phase to Format A
2. Scan phase descriptions for Format B trigger keywords (see table above)
3. Tag matching phases with `pipeline: B`
4. Include this in the PRD output so the CLI Scripter or build runner knows which format to use

---

## For Agents Reading This

If you are a coding agent working on AutoForge, CLI Scripter, or any build pipeline:

- **NEVER default Opus for the Reviewer role.** Use Sonnet.
- **NEVER run Opus on every phase.** Batch checkpoint every 3-4 phases.
- **ALWAYS run robot steps** (lint, type check, test) after every phase — they're free.
- **Tag security/payment/schema phases** as Format B so Opus designs first.
- **Log token usage.** Every build must track how much of each model was consumed.

This is not a suggestion. This is the standard.
