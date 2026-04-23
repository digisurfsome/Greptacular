# Skill-Guided Audit Report — prd-pipeline-c.yaml

**Date:** 2026-04-22
**Reviewer:** Opus, with archon + archon-dev skills loaded as ground truth
**Authoritative source read:** Archon `dag-executor.ts`, `condition-evaluator.ts`, `workflow-dag.md`, `variables.md`, `dag-advanced.md`, PRD README.md §15
**Scope:** deep audit of `prd-pipeline-c.yaml`; light pass on 11 sibling workflows

---

## TL;DR

**Verdict: APPLIED — pipeline polished, not restructured**

The pipeline is structurally solid. Scary things (compound `when:`, hyphenated IDs in bash, trigger_rule on join nodes, recovery wiring) — all correct against source. Prior Opus reviews earned their keep.

### Changes applied this pass

1. **Reviewer retries (the "bench" pattern)** — added `retry: { max_attempts: 3, on_error: all }` to all 12 review nodes (4 reviewers × 3 phases). If a reviewer crashes/times out/errors, Archon auto-spawns a fresh agent and retries up to 3 times before declaring dead.
2. **Safety net on fix aggregators** — added `trigger_rule: none_failed_min_one_success` to `build-fix-issues`, `phase-2-fix`, `phase-3-fix`. If despite 3 retries a reviewer still can't finish, fix runs with whoever survived. Downstream compliance + recovery still catch garbage.
3. **Sibling `idle_timeout`** — added `idle_timeout: 600000` (10 min) to `plan` and `synthesize-review` in `ce-add-feature--see-results-first.yaml` and `ce-add-feature--sonnet-backup.yaml`. Matches the 10-min ceiling pattern used in `stage-05` / `stage-10`.

### Changes NOT applied (by owner decision)

- **Workflow-level `model: opus` is intentional.** PRD maker stages are paint-by-numbers output for downstream Sonnet builders; Opus on PRD-generation is by design. The PRD §15 model table (`README.md` line 1066) is stale vs. actual design intent and should be updated in a separate pass.

### Open / deferred

- **Post-Stage-10 PRD self-check mechanism.** Owner confirmed this is a planned M13-class feature (validates the finished PRD before build starts, proposes edits, re-checks). Not documented yet — owner pulling context from prior chat. Deferred until current pipeline is proven running.

---

## Authoritative Copy Location

Two copies exist on disk; **identical** (SHA-256 match, 31,124 bytes both).

| Path | Role | Status |
|---|---|---|
| `C:\Users\lober\.autoforge\workspace\repos\digisurfsome__Greptacular\.archon\workflows\prd-pipeline-c.yaml` | **Authoritative (repo-tracked)** | Edit this one |
| `C:\Users\lober\.archon\workspaces\digisurfsome\Greptacular\source\.archon\workflows\prd-pipeline-c.yaml` | Runtime mirror (Archon workspace) | Regenerated from repo — do NOT edit |

The expected third copy at `C:\Users\lober\archon\Archon\.archon\workflows\prd-pipeline-c.yaml` does NOT exist. The pipeline lives in the Greptacular repo, not the Archon fork.

---

## prd-pipeline-c.yaml — Deep Findings

### What Passed (verified against source, not just docs)

| Check | Result | Evidence |
|---|---|---|
| Schema: exactly one of `command` / `prompt` / `bash` / `loop` per node | PASS | All 44 nodes comply |
| `depends_on` references exist | PASS | No dangling refs |
| No cycles | PASS | Topologically valid |
| Compound `&&` / `||` in `when:` clauses work | PASS | `condition-evaluator.ts:152-170` confirms `splitOutsideQuotes` on `\|\|` then `&&`. Skill docs `workflow-dag.md` line 139 understates the grammar — source supports compounds. |
| Hyphenated node IDs like `$compliance-gate.output` substitute in bash | PASS | `dag-executor.ts:288` regex allows `[a-zA-Z0-9_-]*` after `$` |
| stdout auto-trim | PASS | `dag-executor.ts:1275` strips one trailing newline. `echo "PASS"` → `"PASS"` is a valid comparison |
| Shell-quoting of substituted values in bash | PASS | `shellQuote` at `dag-executor.ts:270` — `$compliance-gate.output` → `'PASS'` safely |
| `trigger_rule: all_done` on `compliance-final-status` (line 319), `phase-2-final-status` (460), `phase-3-final-status` (586), `build-final-report` (647), `recovery-status-summary` (684) | PASS | Correctly applied wherever upstream branches may be skipped |
| `context: fresh` on parallel review layers and heavy sequential generators | PASS | Applied consistently from stage-03 onward and on all phase execute/review/fix nodes |
| `idle_timeout: 600000` (10 min) on `stage-05`, `stage-10`, `build-codebase-intelligence`; `900000` (15 min) on `build-execute`, `phase-2-execute`, `phase-3-execute` | PASS | Sensible ceilings for heavy generation |
| Recovery branch shape: `when` + `depends_on` + aggregator `trigger_rule: all_done` | PASS | Phases 1, 2, 3 all wire recovery correctly |
| `build-fix-v2` and recovery-* use `model: opus` + `effort` field | PASS | Matches PRD §15 exactly (`effort: medium` for fix, `effort: high` for recovery) |
| Loop nodes | N/A | No loop nodes in this pipeline |
| No `retry` on loop nodes (would be hard error) | N/A | |

### Finding 1 — MODEL DEFAULT MISMATCHES PRD §15 [MAJOR / cost]

**Severity:** MAJOR (cost impact, not functional)
**Skill rule:** model assignments must match design intent; workflow-level `model:` is inherited by every node without an explicit override
**PRD rule:** §15 model table (lines 1064–1079 of `docs/page-prds/archon-build-upgrade/README.md`)

**Current (line 22):**
```yaml
provider: claude
model: opus
```

**Problem.** The workflow defaults every command/prompt node to Opus. These nodes have no explicit `model:` and therefore silently inherit `opus`:

| Node | Line | PRD §15 intent | Currently running on |
|---|---|---|---|
| `stage-00-tech-foundation` | 66 | sonnet | **opus** ❌ |
| `stage-01-idea-capture` | 74 | sonnet | **opus** ❌ |
| `stage-02-gap-analysis` | 82 | sonnet | **opus** ❌ |
| `stage-03-agent-os` | 90 | sonnet | **opus** ❌ |
| `stage-04-mechanism-extraction` | 99 | sonnet | **opus** ❌ |
| `stage-05-wall-door-room` | 108 | sonnet | **opus** ❌ |
| `stage-07-phase-sequencing` | 118 | sonnet | **opus** ❌ |
| `stage-08-protocol-injection` | 127 | sonnet | **opus** ❌ |
| `stage-09-verification-setup` | 136 | sonnet | **opus** ❌ |
| `stage-10-output-generator` | 147 | sonnet | **opus** ❌ |
| `build-codebase-intelligence` | 157 | (not in table — code-reading, should be sonnet) | **opus** ❌ |

That's **11 command nodes** paying 5–6× the intended cost every pipeline run (PRD line 1060: "Opus is 5–6× the cost of Sonnet").

**Before (single line change at the top of file):**
```yaml
provider: claude
model: opus
```

**After:**
```yaml
provider: claude
model: sonnet
```

**Why this is safe.** Every node that should be Opus already has an explicit `model: opus` override (the 3 recovery-* nodes, build-fix-issues, phase-2-fix, phase-3-fix, and their per-phase recovery copies). Every node that should be Haiku has an explicit `model: haiku`. Every node that should be Sonnet and currently has `model: sonnet` stays unchanged. Only the 11 unmarked PRD-stage + cartographer nodes change — and they change to what PRD §15 says they should have always been.

**Why prior reviews missed this.** The pipeline was built without the skill loaded, the workflow-level default was set once early in the build and never revisited when the PRD §15 model table was finalized.

---

### Finding 2 — AGGREGATOR TRIGGER_RULE ON FIX NODES [MINOR / policy]

**Severity:** MINOR (policy decision)
**Skill rule:** `workflow-dag.md` § Trigger Rules — pick the rule that matches your intent when an aggregator has multiple predecessors

**Current (line 236, 392, 518):**
```yaml
- id: build-fix-issues
  command: build-fix-v2
  depends_on: [review-correctness-logic, review-silent-failures, review-test-coverage, review-simplify-code, phase-1-lint-autofix]
  model: opus
  effort: medium
  context: fresh
```

No `trigger_rule:` → defaults to `all_success`. If ONE of the 5 review nodes fails (crash, timeout, model error), the entire fix node is blocked and the pipeline halts at compliance-gate with no fix applied.

**Option A (recommended — forgiving):** fix runs as long as at least one review produced usable output:
```yaml
  trigger_rule: none_failed_min_one_success
```

**Option B (strict — current):** keep `all_success`. Any review failure halts the branch. Pro: you never ship code that wasn't fully reviewed. Con: flaky model calls block the pipeline.

**Option C (aggressive):** `one_success` — run fix the moment any review completes. Don't recommend — some reviews might still be generating.

**My call:** this is a **judgment call, not a bug.** Owner picks.

Same issue in 3 places: `build-fix-issues` (236), `phase-2-fix` (392), `phase-3-fix` (518).

---

### Finding 3 — CONTEXT INHERITANCE ON EARLY PRD STAGES [INFO / by design?]

**Severity:** INFO (likely intentional, documenting anyway)

Stages 00, 01, 02 have NO `context: fresh`. Sequential nodes default to inherited context (`workflow-dag.md` node-fields table). So stages 01 and 02 inherit from 00 — stage-01 sees the tech-foundation output, stage-02 sees both. From stage-03 onward, every stage has `context: fresh`.

This looks intentional — early stages share early decisions; mid/late stages get clean slates to avoid token bloat. Flagging only so you confirm it's by design, not an oversight. **No change recommended.**

---

### Finding 4 — SKILL DOCS GAP (not a pipeline issue) [INFO]

`workflow-dag.md` line 139 documents the `when:` grammar as `$nodeId.output OPERATOR 'value'` with `==` and `!=` only. Source file `condition-evaluator.ts` actually supports:
- Operators `==`, `!=`, `<`, `<=`, `>`, `>=` (numeric comparisons)
- Compound `&&` (AND) and `||` (OR) with precedence (AND > OR, no parens)

The pipeline uses compound `&&` in 8 places — those ARE valid, despite docs being silent. This is an **Archon skill-documentation issue**, not a pipeline issue. Consider filing upstream.

---

## Light Pass — Sibling Workflows (11 files)

| File | Verdict | Issue (if any) |
|---|---|---|
| `prd-pipeline-a.yaml` | PASS | Schema clean, linear command chain |
| `prd-pipeline-b.yaml` | PASS | Parallel reviewers + aggregator correct |
| `ce-add-feature--fully-autonomous.yaml` | PASS | `synthesize-review` has `trigger_rule: one_success` — appropriate |
| `ce-add-feature--see-results-first.yaml` | MINOR | Missing `idle_timeout` on `plan` node (loop/heavy AI) |
| `ce-add-feature--sonnet-backup.yaml` | MINOR | Missing `idle_timeout` on `plan` + `synthesize-review` |
| `ce-existing-code--fully-autonomous.yaml` | PASS | Pattern mirrors add-feature |
| `ce-existing-code--see-results-first.yaml` | PASS | Loop nodes correctly structured |
| `ce-existing-code--sonnet-backup.yaml` | PASS | Loop gates configured |
| `ce-pre-build--fully-autonomous.yaml` | PASS | Matches add-feature pattern |
| `ce-pre-build--see-results-first.yaml` | PASS | |
| `ce-pre-build--sonnet-backup.yaml` | PASS | |

**Sibling pattern verdict:** consistent, well-normalized template across the ce-* family. No cycles, invalid `when:`, retries on loops, or missing required fields. Fix opportunities are the two MINOR `idle_timeout` gaps on the backup/see-results variants.

---

## Opportunities Prior Reviews Missed

1. **Model-default cost leak (Finding 1).** Prior Opus reviews never looked at the workflow-level model in the context of PRD §15. The skill + source re-reading catches it immediately.
2. **`trigger_rule` policy on fix aggregators (Finding 2).** Prior reviews saw `depends_on: [5 nodes]` and moved on. Having the skill's trigger_rule matrix loaded makes the policy question obvious.
3. **Compound `&&` validation.** Prior reviews probably flagged `&&` as suspect because the skill docs don't mention it. Source reading resolves the ambiguity definitively (it works).

---

## Recommendation — Final State

**Finding 1 — REJECTED by owner.** Workflow-level `model: opus` is intentional design. PRD maker = Opus (judgment-heavy), builder = Sonnet (paint-by-numbers execution). PRD §15 table in `README.md` is stale vs. actual design; flag for a future doc pass.

**Finding 2 — APPLIED with upgraded pattern.** Instead of just loosening the trigger rule, implemented belt-and-suspenders: reviewer retries (the "bench") + trigger rule safety net. If a reviewer flakes, another agent gets called up to replace it automatically. If that genuinely fails 3 times, fix runs with survivors; compliance gate + recovery pipeline handle any resulting problems.

**Finding 3 — DEFERRED (by design).** Context inheritance on stages 0/1/2 is intentional.

**Finding 4 — UPSTREAM.** Archon skill docs gap on compound `&&`/`||` grammar. File with cole if desired. Not our pipeline issue.

**Sibling polish — APPLIED.** `idle_timeout` added to the two ce-add-feature variants' heavy AI nodes.

**Status:** SHIP. Pipeline is polished, resilient, and matches owner design intent.

---

*Report written by Opus with archon + archon-dev skills as ground truth. Three pipeline files modified (prd-pipeline-c.yaml, ce-add-feature--see-results-first.yaml, ce-add-feature--sonnet-backup.yaml). Committed as a single cohesive change.*
