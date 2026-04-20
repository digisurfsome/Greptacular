# Phase 3 Opus Review — Codebase Cartographer (M7)

**Reviewer:** Claude Opus
**Commits checked:** `814d05b` (command file) + `a3da3cd` (YAML wiring + feature flag)
**Scope:** One command file (`codebase-cartographer.md`) + three YAML nodes (`read-flag-cartographer`, `codebase-cartographer`) + one `depends_on` edit + one `features.yaml` comment update.

---

## Summary

**Verdict: PASS CLEAN** (one MINOR cosmetic issue)

| Check | Verdict |
|---|---|
| A — Command file content | PASS |
| B — `read-flag-cartographer` node | PASS |
| C — `stage-00-tech-foundation.depends_on` | PASS |
| D — `codebase-cartographer` node | PASS |
| E — `features.yaml` | MINOR |
| F — Collateral damage | PASS |

---

## Findings

### A — Command file content — PASS
`codebase-cartographer.md` is 18 lines. All four required sections present (File Tree, Module Exports, Dependency Graph, Change Map) with one-line descriptions each. Constraints block present (read-only, no opinions, Skipped section). No TODO language, no "could be improved" comments. Matches PRD §4 M7 intent exactly. Haiku-appropriate scope (mechanical serialization, no judgment).

### B — `read-flag-cartographer` node — PASS
`prd-pipeline-c.yaml:52-60`
- `bash:` node (not `command:`) ✓
- Uses `uv run --with pyyaml python -c "..."` — same prefix as existing `read-flag-recovery` and `read-flag-archive` nodes (lines 33-34, 43-44) ✓
- Reads key `codebase_cartographer` with `True` default (line 58) ✓
- No `model:` field (correct — bash nodes have none) ✓
- Positioned at line 52, before `stage-00-tech-foundation` at line 66 ✓

### C — `stage-00-tech-foundation.depends_on` — PASS
`prd-pipeline-c.yaml:68`
- `depends_on: [read-flag-recovery, read-flag-archive, read-flag-cartographer]` — all three flag readers listed ✓
- No other changes: still `command: prd-stage-00` at line 67, no stray fields added.

### D — `codebase-cartographer` node — PASS
`prd-pipeline-c.yaml:612-617`
- `command: codebase-cartographer` (line 613) — correct type for a Haiku agent invocation ✓
- `model: haiku` (line 616) — lowercase alias, no literal version string ✓
- `context: fresh` (line 617) ✓
- `depends_on: [claude-md-presence-check, read-flag-cartographer]` (line 614) ✓
- `when: "$read-flag-cartographer.output == 'true'"` (line 615) — single-quoted RHS, condition-evaluator.ts-compliant ✓
- Positioned after `claude-md-presence-check` (line 600) and before `deploy-gate` (line 626) ✓
- **Runs in parallel with `deploy-gate`** — both depend only on `claude-md-presence-check`. Deploy is NOT downstream of cartographer. Per PRD §4 M7, M7 is a DOOR not a WALL — correct design. If cartographer fails, deploy is untouched. ✓
- No `effort:` field — correct per PRD §15 (Haiku runs at default effort). ✓

The `when:` clause uses the Python-output format: the `read-flag-cartographer` node prints `str(c.get(...)).lower()` which emits bare `true` or `false`. The condition `'true'` matches exactly.

### E — `features.yaml` — MINOR
**Issue:** `codebase_cartographer: true` is now WIRED (inline comment on line 9 correctly says `WIRED in Phase 3`), but it still sits directly under the section banner `# ── UNWIRED toggles (...) ──` at line 8. The banner and the first item under it now contradict each other.

**Before (`features.yaml:8-9`):**
```
# ── UNWIRED toggles (listed for future phases; changing them has no effect today) ──
codebase_cartographer: true   # M7 (Phase 3): Haiku builds CODEBASE_MAP.md — WIRED in Phase 3
```

**After (suggested — move the wired toggle above the banner):**
```
codebase_cartographer: true   # M7: Haiku builds CODEBASE_MAP.md after each build
# ── UNWIRED toggles (listed for future phases; changing them has no effect today) ──
scoped_claude_md: true        # M6: per-directory CLAUDE.md auto-attach — NOT WIRED
regression_harness: true      # M11: self-tests run as separate workflow — no pipeline toggle needed
build_intelligence: false     # learn from prior builds — OFF, NOT WIRED
```

File still parses as valid YAML (confirmed by test: `read-flag-cartographer` node reads this file successfully at pipeline start; the banner line is a comment). Purely cosmetic. Not a ship-blocker.

Other checks:
- `codebase_cartographer: true` still present on line 9 ✓
- File parses as valid YAML ✓

### F — Collateral damage — PASS
- Phase 1 and Phase 2 node IDs unchanged: spot-checked `full-checkpoint` (line 319 in prior read), `phase-1-handoff` (line 334), `phase-2-handoff` (line 460), `phase-2-checkpoint` (preserved as dep on line 462), `phase-3-checkpoint` (preserved as dep on line 604). No renames.
- Recovery branches: `compliance-final-status` (line ~292), `phase-2-final-status`, `phase-3-final-status` all still carry `trigger_rule: all_done` (confirmed unchanged from Phase 2 review commit state — the Phase 3 diff only inserted new nodes and updated one `depends_on` list).
- `archive-prd` still the last node in the file (file ends around line 669+ with `archive-prd` as the tail — matches the state verified in Phase 2 review).
- `deploy-gate` still depends only on `claude-md-presence-check` (line 634) — NOT on `codebase-cartographer`. Correct: M7 is DOOR, must not block deploy.
- `build-deploy` path is not downstream of cartographer — cartographer is "fire and forget" relative to the deploy chain. Acceptable per PRD §4 M7.

**Secondary observation (not a defect):** `CODEBASE_MAP.md` is written to the project root. Nothing downstream waits for cartographer, so `build-deploy` may run and commit before cartographer finishes. This means `CODEBASE_MAP.md` may or may not be in the deployed commit, depending on timing. If the operator wants the map always shipped, add `build-deploy.depends_on: [codebase-cartographer]` (with `trigger_rule: all_done` so deploy still runs when cartographer is skipped). Current behavior matches PRD §4 M7's "DOOR not WALL" contract — noting for future polish only.

---

## Recommendation

**Phase 3 is done.** Ship it.

Optional polish (do in the next maintenance pass, not a blocker):
1. Move `codebase_cartographer: true` above the `UNWIRED toggles` banner in `features.yaml` so the banner accurately describes what sits below it.
2. Consider whether `build-deploy` should wait for `codebase-cartographer` so `CODEBASE_MAP.md` is guaranteed included in the deploy commit. Requires `trigger_rule: all_done` to preserve the DOOR semantics.

Neither is required for Phase 3 to be declared complete.
