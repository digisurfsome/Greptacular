# Model Selection Guide — Which Opus for Which Build

> Quick reference for picking `@model` and effort level at build time. Use this when you're about to kick off a pipeline-d run and aren't sure which setting fits.

---

## Model Naming Translation (the one table you'll keep coming back to)

Preferred name (what you type in `@model` tag) → actual Archon YAML values:

| Your name | Archon `model:` | Archon `effort:` |
|-----------|-----------------|-------------------|
| `opus-4.6-medium` (**default**) | `claude-opus-4-6` | `medium` |
| `opus-4.6-high` | `claude-opus-4-6` | `high` |
| `opus-4.6-extrahigh` | `claude-opus-4-6` | `max` |
| `opus-4.7-medium` | `claude-opus-4-7` | `medium` |
| `opus-4.7-high` | `claude-opus-4-7` | `high` |
| `opus-4.7-extrahigh` | `claude-opus-4-7` | `max` |

`extrahigh` maps to Archon's internal `effort: max` (confirmed in `packages/workflows/src/dag-executor.test.ts:5100`).

Default when no `@model` tag present: `opus-4.6-medium`.

---

## The Three Axes That Drive the Choice

Score your upcoming build on these three. They tell you where to land.

| Axis | Low → High |
|------|------------|
| **Complexity** | One small mechanism → multi-system assembled product |
| **Novelty / ambiguity** | Well-trodden pattern (CRUD, API wrapper) → genuinely new (novel algorithm, unusual integration) |
| **Cost of being wrong** | Cheap re-run, throwaway → production launch, foundation for 10 other builds |

Then:
- **Model (4.6 vs 4.7):** driven mostly by novelty + cost-of-being-wrong. 4.7 is sharper on long-horizon reasoning and new territory. 4.6 is great at well-trodden work.
- **Effort (medium / high / extrahigh):** driven mostly by complexity + ambiguity. Higher effort = more planning budget = better decisions on hard tradeoffs.

---

## The Matrix — What to Actually Pick

| Scenario | Model | Why |
|----------|-------|-----|
| PRD-only run (just want bundle to review) | `opus-4.6-medium` | Structured extraction. 4.6 handles it. Cheap. |
| Build-only re-run with proven PRD | `opus-4.6-medium` | Deterministic work. Don't overpay. |
| Small `feature-add` (one file, clear scope) | `opus-4.6-medium` | Minimal reasoning needed. |
| Single-mechanism `module` (CSV→JSON, one API wrapper) | `opus-4.6-medium` | Clear contract, one job. |
| Multi-mechanism `module` (TTS + R2 + DB + retry) | `opus-4.6-high` | Several moving parts. Needs planning budget. |
| `standalone-app` with UI + DB + auth | `opus-4.6-high` | Moderate complexity. 4.6 handles well with more thinking. |
| `assembly` mode (wiring N modules into a host) | `opus-4.7-medium` | Precision matters. 4.7 sharper at contract-matching. |
| `module-host` build (defining the shell) | `opus-4.7-high` | Shell is foundation for every module. Wrong shell = wrong everything. |
| Complex `feature-add` on big existing codebase | `opus-4.7-high` | Reasoning across code it didn't write. 4.7 is better. |
| First-ever run of a new build mode | `opus-4.7-high` | Stress-testing the preambles. Want high-fidelity signal. |
| `contract-spec` for multi-module system | `opus-4.7-extrahigh` | Output is a permanent constraint on N module builds. One-shot, high-stakes. |
| Novel domain PRD (first telephony app, first ML pipeline, etc.) | `opus-4.7-extrahigh` | 4.7's edge shows up most on unfamiliar territory. |
| Production launch build (real users will use this) | `opus-4.7-high` minimum | Do not cheap out on what ships. |
| Pipeline rebuild work itself (Passes 0/1/2) | `opus-4.7-high` | Architectural, long-horizon, high cost of being wrong. |

---

## Rules of Thumb

1. **Default is `opus-4.6-medium`.** 80% of builds run here. Step up only when you can name a specific reason.
2. **Step up model (4.6 → 4.7) for NOVELTY.** New domain, new integration, unfamiliar pattern.
3. **Step up effort (medium → high → extrahigh) for COMPLEXITY.** More moving parts = more planning budget.
4. **Step up BOTH for CONTRACTS.** Anything whose output locks in future decisions — `contract-spec`, `module-host` shell, shared DB schema. Cost of extrahigh is a coffee. Cost of rebuilding 5 modules against a bad contract is a weekend.
5. **Don't step up for SIZE ALONE.** A 50-file standalone CRUD app is still a CRUD app. 4.6-high handles it.

---

## Rough Cost Framing

Not exact pricing — mental model only. Useful for "is it worth it?" decisions.

| Setting | Relative cost |
|---------|---------------|
| 4.6-medium | baseline (1x) |
| 4.6-high | 1.5–2x |
| 4.6-extrahigh | 3–4x |
| 4.7-medium | 2–3x |
| 4.7-high | 4–6x |
| 4.7-extrahigh | 8–12x |

A run costing $2 at 4.6-medium is $20–25 at 4.7-extrahigh. For a one-shot `contract-spec` that locks in 5 modules, that's a bargain. For the 50th re-run of a debugged module, it's lunacy.

---

## Known Caveat: 4.7 Stability

At time of writing, Opus 4.7 is freshly released and behavior can be inconsistent day-to-day. When it's unstable, fall back to 4.6 at the appropriate effort level — 4.6-high often matches or beats flaky 4.7-medium. Once 4.7 stabilizes (days to weeks post-release), use this guide normally.

---

## Future Enhancement (not implemented yet)

Right now one model is chosen for the whole run. But the PRD phase and Build phase have different needs:
- **PRD phase** = analytical, structured extraction. Usually 4.6-medium is fine.
- **Build phase** = code writing, architectural decisions. Often wants 4.7 or higher effort.

A future V3 enhancement would split into `@prd-model` and `@build-model` tags — pay the premium only where it matters. This would be a small addition to the `model-select` preflight node. Worth adding to the V3 Roadmap if cost becomes a pain point.
