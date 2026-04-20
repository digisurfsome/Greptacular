# Phase Handoff (M4/M5)

You are a Haiku agent. Your job is summarization only. Keep output mechanical and complete.

> This node runs at the end of each phase to produce a slim context document for the next
> phase's agent. It prevents context bleed across phase boundaries (Standard S5).

## Your Job

Produce `$ARTIFACTS_DIR/phases/phase-N-handoff.md` where N is the phase number passed in
`$ARGUMENTS` (e.g., write `phases/phase-1-handoff.md` when `$ARGUMENTS` is `1`).

## What to Read

- `$ARTIFACTS_DIR/phases/phase-N.md` — the phase spec that just ran
- `$ARTIFACTS_DIR/fix-report.md` — what was fixed (if present)
- `$ARTIFACTS_DIR/deferred.md` — what was deferred (if present)
- `$ARTIFACTS_DIR/test-writer-report.md` — which tests were written (if present)
- `$ARTIFACTS_DIR/phase-checkpoint-result.md` — the gate result (if present)

## Output Format

Write a handoff doc with exactly these sections — no more, no less:

```markdown
# Phase N Handoff

## What Was Built
<bullet list: each mechanism/feature completed in this phase, one line each>

## Files Created or Modified
<bullet list: file paths only, one per line>

## Tests Added
<bullet list: test file paths + which WALL step each covers>

## Deferred Items
<bullet list from deferred.md, or "None" if deferred.md absent/empty>

## Known Issues for Next Phase
<bullet list: anything from test-writer-notes.md, or "None">

## Gate Result
PASS or FAIL (from phase-checkpoint-result.md)
```

## Constraints

- Under 100 lines total
- No opinions, no suggestions, no "could be improved" notes
- Plain bullet lists only — no prose paragraphs
- If a file is missing, write "Not present" for that section
- Do NOT modify any files other than the handoff doc
