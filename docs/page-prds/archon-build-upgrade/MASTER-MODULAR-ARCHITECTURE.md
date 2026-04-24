# Master Design — Modular Build Architecture for the Archon PRD Pipeline

**Status:** Design spec, not yet implemented. This is the consolidated architecture decision for how the pipeline handles different build shapes. Supersedes M13 / M14 / M15 drafts (those remain as reference but this is canonical).

**Author context:** Owner is building multi-mechanism apps (CallPitch = 5-tool lead-gen system). Realized the pipeline needs to support modular builds, not just monolithic ones. This doc captures that architecture so it survives context loss.

---

## 1. Executive summary

The pipeline currently assumes every build is a `standalone-app`. In reality, builds fall into 6 shapes. Supporting all 6 requires:

1. An **intake classifier** that picks the build mode.
2. A **`build_mode` flag** that propagates through every stage.
3. A **conditional preamble block** in every stage command file that reads `build_mode` and injects the right context.
4. A **standardized module contract** that every module must conform to, so modules built in isolation can assemble cleanly later.
5. A **per-build custom contract layer** that defines what the specific assembly looks like (which modules, how wired).

Net effect: modules become reusable tools on a workshop wall. Built once, mixed-and-matched into any number of apps. No rebuild, no translation, no glue code hell.

---

## 2. The 6 build modes

| Mode | What's being built | Boilerplate? | UI? | Intended use |
|---|---|---|---|---|
| `standalone-app` | Small self-contained app, no modules | Yes | Yes | Small utilities, one-off tools, anything too small to benefit from modularity |
| `module` | One mechanism, headless, API/CLI only | No | Minimal admin only | Reusable tool — scraper, MP3 generator, detection bot, anything that's big enough to be a named mechanism |
| `module-host` | Empty shell — boilerplate + dashboard + shared DB + auth + module registration surface | Yes | Yes (shell) | Container app that modules bolt into |
| `assembly` | Wire N pre-existing modules into a pre-existing host | Uses existing host | Uses host UI | "Take CallPitch shell + Scraper + MP3 Gen + Landing. Wire them up." |
| `feature-add` | Add a feature to an existing app | Existing | Existing | M13 mode — adding search to your app, adding a tab, extending a page |
| `contract-spec` | Produce shared DB schema + module interface contracts for an upcoming multi-module build | None — it outputs a spec | None | Pre-flight for `module` builds that will later assemble |

### Decision heuristic

```
Is it a reusable mechanism I'll use in multiple apps? → module
Is it the empty shell of a new multi-module app? → module-host
Is it wiring pre-built things together? → assembly
Am I pre-planning schemas for multi-module build? → contract-spec
Am I extending something that already runs? → feature-add
None of the above, just build it? → standalone-app
```

### Typical multi-module build sequence (e.g., CallPitch)

1. **`contract-spec`** — one run. Produces shared DB schema + 5 module interface contracts.
2. **`module-host`** — one run. Produces CallPitch shell matching the contract.
3. **`module` × 5** — five parallel runs. Each implements one module against the contract.
4. **`assembly`** — one run. Wires the 5 modules into the shell, adds integration tests.

Total: **8 pipeline runs** for a 5-tool app. Sounds like more than "one big build" but each run is narrower = faster + higher quality + modules are reusable afterwards.

---

## 3. The unified preamble mechanism

Every stage command file gets a **preamble block** at the top that reads `$build_mode` and injects mode-appropriate context. Bare-bones stage content follows underneath.

### Template for every stage

```
# Stage NN: [Stage Name]

## CONTEXT PREAMBLE — READ FIRST

You are running in build_mode = $build_mode.

IF build_mode == "module":
  You are designing ONE isolated mechanism.
  - No UI, no boilerplate, no dashboard.
  - Must conform to the Standard Module Contract (§4 of master design).
  - Define input contract (what columns/events it reads).
  - Define output contract (what columns/events it writes).
  - Include minimal test harness with mock data.
  - Scope is STRICTLY this mechanism. Do not design surrounding infra.
  - Context below describes the larger system this module fits into — use it
    for decision-making, but do NOT expand scope to build other pieces.

IF build_mode == "module-host":
  You are designing an EMPTY shell for modules to bolt into.
  - Include: boilerplate, shared DB schema (from contract-spec), auth,
    dashboard with module-registration UI, shared env/config, worker queue.
  - Do NOT design any specific module's internals.
  - Design the registration surface so new modules can be added later without
    host changes.

IF build_mode == "assembly":
  You are wiring N pre-built modules into a pre-built host.
  - Read each module's interface contract.
  - Read the host's registration surface.
  - Design only the wiring: routes, worker jobs, shared state, event bus,
    cross-module flows, integration tests.
  - Do NOT redesign any module's internals.

IF build_mode == "feature-add":
  (See M13 existing-app-mode context)

IF build_mode == "contract-spec":
  You are producing schemas + contracts only, no code.
  - Output: shared DB schema (every table, every column, every constraint).
  - Output: per-module input/output contracts.
  - Output: shared event bus spec (if any).
  - Output: shared auth/config surface.
  - This spec becomes the hard constraint for all subsequent module builds.

IF build_mode == "standalone-app":
  Default behavior. Build the whole thing as one app.
  No special constraints.

## SYSTEM CONTEXT (provided by intake classifier)

Why this exists: $why_exists
Who operates it: $operator
Target end-user: $end_target
Larger system this fits into: $system_context
Other modules in the system (if applicable): $sibling_modules

## BARE-BONES STAGE CONTENT (unchanged)

[... normal stage prompt here, unchanged ...]
```

### Rules

- Preamble block is identical across all stages. Edit once, copy everywhere. (Ideally factored into a shared include if Archon supports it.)
- `build_mode` is set by the intake classifier BEFORE stage 00 runs.
- System context variables (`$why_exists`, etc.) are also set by the classifier from the intake doc.
- Stage prompts below the preamble stay bare-bones. No mode logic in the stage itself. All mode logic lives in the preamble.

---

## 4. The Standardized Module Contract

**Every module that ever gets built must conform to this contract.** This is what lets modules mix-and-match.

### 4.1 What every module must expose

| Surface | Requirement |
|---|---|
| **CLI entrypoint** | `python -m <module_name> [args]` or equivalent. Manual trigger must be possible. |
| **Config schema** | Declared in `module.yaml` (§4.2). Lists every env var / config key the module reads. |
| **Health check** | Either HTTP `/health` endpoint (if module has a server) or CLI `--health` flag. Returns OK + version + ready/not-ready. |
| **Logs** | Structured JSON logs to a standard path (e.g., `logs/<module_name>/YYYY-MM-DD.jsonl`). Never prints to stdout in production. |
| **Failure table** | Writes unrecoverable errors to shared `module_failures` table with module name + row ID + error + timestamp. |
| **Test harness** | `tests/` folder with at minimum a smoke test that runs on mock inputs and does not require upstream modules. |
| **No direct calls to other modules** | Modules communicate ONLY through DB or event bus. Never import each other's code. |

### 4.2 Module manifest — `module.yaml` (lives at module root)

```yaml
name: mp3-generator
version: 1.0.0
description: Turns DB rows into personalized MP3 files

# What this module reads
inputs:
  db_tables:
    - name: businesses
      columns_read:
        - detection_result
        - detection_transcript
        - biz_name
        - niche
        - city
        - owner_first_name    # optional
        - google_rating        # optional
      filter: "detection_result IS NOT NULL AND mp3_url IS NULL"
  events_subscribed: []        # if any
  env_vars:
    - KOKORO_ENDPOINT
    - R2_ACCESS_KEY
    - R2_SECRET_KEY
    - R2_BUCKET
    - DATABASE_URL
  external_services:
    - kokoro-tts (localhost:8881)
    - cloudflare-r2

# What this module writes
outputs:
  db_tables:
    - name: businesses
      columns_written:
        - mp3_url
        - mp3_generated_at
        - mp3_script_version
        - mp3_script_text
        - mp3_voice_used
        - mp3_duration_seconds
        - mp3_offer_type
        - mp3_generation_attempts
    - name: mp3_history
      columns_written: [all]  # owns this table
    - name: module_failures
      columns_written: [name, row_id, error, timestamp]  # shared failure surface
  events_emitted:
    - mp3.generated  (payload: { biz_id, mp3_url })
  files_written:
    - R2 bucket: leads-mp3s/<niche>/<city>/<biz_id>.mp3
  logs:
    - logs/mp3-generator/YYYY-MM-DD.jsonl

# How this module gets triggered
triggers:
  - type: cron
    schedule: "0 2 * * *"    # 2 AM daily
  - type: cli
    command: "python -m mp3_generator"
  - type: event
    on: detection.completed   # if subscribing

# Module dependencies (MUST already be in DB when this runs)
depends_on_modules:
  - scraper         # must have populated biz data
  - detection-bot   # must have populated detection fields

# Shared resources used
shared_resources:
  - database        # uses shared Postgres
  - event_bus       # uses shared event bus
  - auth            # uses shared auth (if any)
```

Every host reads every module's `module.yaml` to wire up registration, scheduling, routing.

### 4.3 DB ownership rules

- **Each module owns its write columns.** No other module writes those columns.
- **Modules read freely from other modules' columns** (documented in `inputs.db_tables.columns_read`).
- **Shared tables** (e.g., `module_failures`, `module_events`, `users`) are owned by the host, not any module.
- **Schema migrations** live in the contract-spec output. Modules don't run their own migrations.

### 4.4 Event bus rules (if used)

- Single shared event bus (Postgres LISTEN/NOTIFY, or Redis, or whatever host provides).
- Event names are `<module>.<action>` (e.g., `detection.completed`).
- Payload schema declared in `module.yaml`.
- Modules subscribe by declaring in `inputs.events_subscribed`.

### 4.5 Config/env rules

- Every env var a module needs is declared in `module.yaml`.
- Host validates all modules' env vars are present on startup — refuses to start if any missing.
- Shared secrets (DB creds, etc.) set once at host level; modules read via shared config loader.

### 4.6 Test harness requirements

Every module MUST ship with:
- A `tests/mock_data/` folder containing synthetic input rows.
- A `tests/smoke_test.py` that runs the module end-to-end against mock data without real DB, real APIs, or upstream modules.
- Tests must pass in CI before the module can be declared "done."

---

## 5. Per-build custom contract layer

The Standardized Module Contract (§4) is **structural** — every module everywhere follows it. But each specific multi-module app also has **custom contract details** — what the specific DB schema is, which modules are in this build, how they wire.

This is what `contract-spec` mode produces per-build:

- **Shared DB schema** for this specific app (e.g., `businesses` table with all columns across all 5 modules).
- **Module roster** for this app (which modules, which versions).
- **Wire-up map** — which module feeds which, which events fire, which cron schedules.
- **Offer rotation config** (CallPitch-specific) — which MP3 offer type runs on which night.
- **Auth/tenancy model** — is this single-user? Multi-user? Multi-tenant?

This custom contract is read by `module-host` and `module` and `assembly` runs, all three, as a hard constraint.

---

## 6. Phased rollout plan (REVISED — aligned with no-bash rebuild)

The original rollout plan assumed we were adding build modes on top of the existing bash-fragile pipeline-c. That plan is **rescinded**. The current sequence is a 4-pass plan where the modular build system is built into pipeline-d from the start.

| Pass | What it does | Handoff PRD |
|------|--------------|-------------|
| **Pass 0** | Audit every stage prompt in `.archon/commands/`. Strip mode assumptions. Author per-stage preamble blocks with IF branches for all 6 modes. Zero YAML changes. | `PASS-0-PREAMBLE-AUDIT-HANDOFF.md` |
| **Pass 1** | Rebuild `prd-pipeline-c.yaml` as `prd-pipeline-d.yaml` — zero bash, single-file-with-switches. Three preflight nodes at top: `model-select` (Opus 4.6/4.7 + effort), `mode-select` (full/prd-only/build-only), `build-type-select` (6 build modes). Consumes Pass 0's mode-agnostic prompts. | `PIPELINE-REBUILD-NO-BASH-HANDOFF.md` |
| **Pass 2** | V3 paint-by-numbers layer — 5 new nodes (deploy router, golden-path trace, red-team, compile-check per phase, boundary gate), updated stage prompts (I/O examples, verify blocks), reproducibility (run hash + seed lock). Lifts quality from 7.5/10 → 9.5/10. | `PRD-MAKER-V3-ROADMAP.md` |
| **Pass 3** | Module contract enforcement. `module.yaml` validator. Module cert script. Only needed once multi-module apps like CallPitch are being built. | TBD |

**Adding a 7th build mode later** = one new preamble branch per stage + one line in the `build-type-select` enum. No other changes. See `ADD-NEW-BUILD-STYLE-HANDOFF.md` for the recipe.

The original 4 phases of this section still describe the intended capability sequence (validate → module mode → full 6 modes → PRD self-check revision loop), but the implementation path now runs through the 4 passes above.

---

## 7. Relationship to M13 / M14 / M15

This master doc **supersedes and consolidates** the three separate M-docs:

- **M13 (existing-app mode)** → becomes `build_mode == "feature-add"` path in this model.
- **M14 (PRD self-check + revision loop)** → revision is a SEPARATE orthogonal flag (`revision_mode`) that layers on top of build_mode. M14 still applies as a standalone concern.
- **M15 (intake classifier)** → becomes the mechanism that SETS `build_mode` at pipeline start. Still needs to be built.

The three M-docs stay on disk as reference but all net-new planning happens in this master doc.

---

## 8. Open questions (defer to implementation)

- **Module versioning.** If CallPitch uses `mp3-generator v1.0.0` and a future app wants `v2.0.0`, how does the host specify? (Probably version pin in host's module roster config.)
- **Module discovery.** How does the host find installed modules? File-system scan of `modules/*/module.yaml`? Explicit registration call? Start with file-system scan — simplest.
- **Host-module communication for UI.** If a module has an admin sub-UI (e.g., "show batch runs" page for MP3 gen), how does it register that with the host dashboard? Iframe? Route declaration in module.yaml? Start with route declaration.
- **Module isolation at runtime.** Same Python process? Separate processes? Separate containers? Start with same process, separate modules as Python packages. Scale up later if needed.
- **Contract-spec revision.** If you add a 6th module to CallPitch after launch, does contract-spec re-run and migrate the DB? Or is it manual? Probably manual for v1, automated later.
- **Module certification.** Before a module is declared "reusable," should it pass a certification check (all manifest fields present, test harness passes, no direct imports of other modules)? Yes — write a `module-cert` script that validates.

---

## 9. Example: Full CallPitch walkthrough

**User intake:** "Build me CallPitch — a 5-module lead-gen system that calls small businesses, detects if they have a phone problem, generates a personalized MP3 demo, hosts a landing page, and blasts outreach."

**Classifier output:** `build_mode = multi-module-project`, routes to contract-spec first.

**Run 1 — contract-spec (1 pipeline run):**
- Output: shared DB schema (businesses table with 40+ columns, mp3_history table, module_failures table, module_events table).
- Output: 5 module contracts (scraper, detection-bot, mp3-generator, landing-pages, outreach).
- Output: event bus spec.
- Output: wire-up map.

**Run 2 — module-host (1 pipeline run):**
- Input: contract-spec output.
- Output: CallPitch shell. Astro boilerplate + dashboard with 5 empty module slots + Postgres migration + shared auth + worker queue + event bus.

**Runs 3-7 — 5 × module builds (5 parallel pipeline runs):**
- Each input: contract-spec output (just its own contract section) + SYSTEM CONTEXT (this module is part of CallPitch, here's the bigger picture).
- Each output: a standalone module with manifest + CLI + tests + admin UI stub.

**Run 8 — assembly (1 pipeline run):**
- Input: CallPitch shell + 5 completed modules.
- Output: wired-up app. Cron schedules registered. Event subscriptions wired. Dashboard populated. Integration tests passing.

**Result:** CallPitch running in production. 5 modules in the `modules/` folder. Any of them can be lifted out and plugged into a future app.

---

## 10. Why this design matters

**Without this architecture:** owner hand-codes 5 tools in one app. Spaghetti. When mp3-generator logic needs to power a different app six months later, he rebuilds it from memory. No standards = drift. When one module breaks, diagnosing means grep across 5 tangled features.

**With this architecture:** modules are workshop tools on the wall. Each one is tested in isolation, versioned, reusable. New apps = pick modules + assemble. Broken module = replace the module, not the app. The pipeline itself becomes a tool factory, not a one-off code generator.

This is the compounding asset play. Every module built is a permanent workshop addition.
