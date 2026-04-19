# PRD Hardening Loop — Archon Skill

**What it does:** Runs a document (PRD, spec, handoff, plan) through multiple independent validator agents, auto-applies fixes between each round, and stops when the document is clean or after 3 rounds — whichever comes first.

**When to use it:** Any time you have an important document that needs to be technically correct before you execute on it, and you want more than one set of eyes on it without doing it manually.

**Invented from:** Manual iterative PRD hardening of `docs/page-prds/archon-build-upgrade/README.md` on 2026-04-19. Round 1 found 12 architectural issues. Round 2 (post-fix) found 9 deeper bugs. Pattern was clear: independent validators find progressively smaller problems until they stop finding any.

---

## How to use it — push-button version

### Step 1: Copy these 3 files into your Archon project

```
your-project/
  .archon/
    workflows/
      prd-hardening-loop.yaml    ← from archon-prd-hardening/workflows/
    commands/
      prd-validator.md           ← from archon-prd-hardening/commands/
      prd-fix-applier.md         ← from archon-prd-hardening/commands/
```

### Step 2: Edit the top of `prd-hardening-loop.yaml`

You only change 3 things (marked with `# <-- EDIT ME`):

```yaml
# <-- EDIT ME: full path to the document you want hardened
prd_path: docs/page-prds/your-feature/README.md

# <-- EDIT ME: what the validators should check your document against
# (e.g., a source codebase for technical accuracy, or "none" for logic-only review)
reference_codebase_path: C:\Users\lober\archon\Archon\

# <-- EDIT ME: short description for the validator (what the doc is)
document_description: |
  This is a PRD for upgrading the Archon build-half pipeline.
  Validate every YAML snippet against Archon's real schema at the path above.
```

### Step 3: Run the workflow

From Archon's UI or CLI:
```
archon run prd-hardening-loop
```

### Step 4: Read the final status

Outputs go to `$ARTIFACTS_DIR/`:
- `VALIDATION-REPORT-round-1.md`
- `VALIDATION-REPORT-round-2.md` (if round 1 wasn't clean)
- `VALIDATION-REPORT-round-3.md` (if round 2 wasn't clean)
- `FINAL-STATUS.md` — human-readable summary

Backups of each revision live next to the PRD itself:
- `README.backup-pre-hardening.md`
- `README.backup-post-round-1.md`
- `README.backup-post-round-2.md`

---

## What each round does

Every round is identical:

1. **Validator** — fresh agent, no memory of prior rounds, reads the PRD and the reference codebase, produces a report with verdicts (PASS / MINOR / FAIL) and copy-pasteable before/after code for every problem
2. **Clean-check gate** — reads the report, extracts the verdict string, emits `CLEAN` or `DIRTY`
3. **Fix-applier** (only runs on `DIRTY`) — mechanically applies every before/after fix from the report to the PRD
4. **Commit** (only runs on `DIRTY`) — commits the round's changes to git with a receipt message
5. **Round aggregator** — short-circuits remaining rounds if `CLEAN`

---

## Why 3 rounds and not infinite

Infinite loops in validation tend to oscillate once you're past the real bugs — validators start finding stylistic nits or disagreeing with each other on trivial things. Based on the original manual run, the useful signal is in rounds 1 and 2. Round 3 is your safety net. If round 3 is still dirty, the document has a problem a human needs to look at — not another agent.

You can extend to 5 or 7 rounds by copy-pasting a round-block in the YAML. Don't bother with 10+.

---

## When NOT to use this

- **For short docs** (under 200 lines). Overkill.
- **For docs with no external reference** to validate against. Validators need something objective to check claims against — source code, an API spec, a standards doc. Without a reference, they're just rewriting prose.
- **When you already know the doc is broken.** Fix the known problems first, then run this to catch what you missed.

---

## Cost envelope (rough)

Per round, approximately:
- Validator: Opus, ~100K tokens (reads reference codebase + PRD, writes report)
- Fix-applier: Sonnet, ~40K tokens (reads report + PRD, applies edits)
- Gate + aggregator: trivial

3 full rounds (worst case): ~420K tokens total, ~$8-12 at current Claude pricing.
Typical (2 rounds before clean): ~280K tokens, ~$6-8.

Cheaper than you spending 30-60 minutes shepherding this manually, and produces a paper trail.

---

## What makes this work

Three principles the workflow enforces:

1. **Independence between validators** — no validator reads prior reports. Each one produces a fresh opinion. Otherwise they anchor to each other.
2. **Before/after fixes, not descriptions** — a report that says "M7 is broken" is useless to the fix-applier. A report that says "replace lines X-Y with this exact block" is mechanical to apply. The validator prompt enforces this.
3. **Commit after every round** — even if round 2 makes things worse (rare), you can always revert. The paper trail IS the safety net.

---

## Files in this package

| File | Purpose |
|---|---|
| `README.md` | This file. |
| `workflows/prd-hardening-loop.yaml` | The Archon workflow. 3 rounds + aggregator. |
| `commands/prd-validator.md` | Generic validator prompt template. Uses `{{PRD_PATH}}`, `{{REFERENCE_CODEBASE_PATH}}`, `{{ROUND_NUMBER}}` substitutions. |
| `commands/prd-fix-applier.md` | Generic fix-applier prompt template. Reads a validation report and applies every before/after fix found in it. |
