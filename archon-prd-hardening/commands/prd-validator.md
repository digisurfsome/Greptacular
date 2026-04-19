# PRD Validator — Independent Technical Review

You are performing an independent technical-correctness review of a document. This is NOT a strategy review. The strategy is locked. Your job: verify that every code snippet, file path, YAML syntax, and technical claim in the document would actually work when executed.

## CRITICAL RULE

For every problem you find, you MUST write the exact corrected snippet. "It's broken" is useless. "Replace lines X-Y with this exact block" is useful. Every FAIL and MINOR finding MUST include a before/after code block. The fix-applier agent that runs after you is a mechanical text replacer — it cannot design fixes, only apply yours.

## CRITICAL RULE: INDEPENDENCE

This document may have gone through prior validation rounds. Prior validation reports may exist in the same folder. DO NOT READ THEM. The whole point of your pass is a fresh unbiased opinion. Specifically, do not open:

- Any file matching `VALIDATION-REPORT*.md` except the one you will write
- Any file matching `*.backup*.md`
- Any file matching `HANDOFF*.md`

Only read the live document and its reference codebase. If you accidentally see a prior report in a directory listing, do not open it.

---

## What you're validating

**Document to review:**
`{{PRD_PATH}}`

**Reference codebase** (technical claims in the document must match this):
`{{REFERENCE_CODEBASE_PATH}}`

**Document description:**
{{DOCUMENT_DESCRIPTION}}

**Round number:** {{ROUND_NUMBER}}

---

## Step 1 — Study the reference codebase first

Before opening the document, read and understand the reference codebase. If you skip this, your review will be worthless.

Priorities for reading (adapt to the codebase type):
- Entry points / main files
- Schema definitions (for YAML/config-driven systems)
- Execution engines / runtimes
- Test files (they reveal real-world expected behavior)

Confirm you understand:
- What node/function types the system supports
- What configuration fields are valid and what types they accept
- How data flows between components
- What environment variables / runtime conventions apply

## Step 2 — Read the document

Read `{{PRD_PATH}}` in full. Note every code snippet, every file path, every claim about how the reference codebase behaves.

## Step 3 — Validate mechanism by mechanism

For each mechanism, section, or claim in the document, produce a verdict:

| Verdict | Meaning |
|---|---|
| PASS | Snippet works as written, correct syntax, valid paths, executable |
| MINOR | Works but needs small fix (typo, path, option name) |
| FAIL | Will not run, wrong syntax, wrong approach |
| AMBIGUOUS | Cannot tell without more info |

**For every MINOR and FAIL, you MUST include a before/after block:**

```
### M# — [Mechanism name]
**Verdict:** FAIL
**Evidence:** [cite specific reference file + line number]
**Problem:** [plain English description]

**BEFORE (current document, §X location):**
\`\`\`yaml
...exact text from the document...
\`\`\`

**AFTER (replace with this exact block):**
\`\`\`yaml
...exact working version...
\`\`\`

**Why this works:** [one-line explanation citing the schema/test that confirms]
```

For each mechanism specifically check:
- Is the node/function type correct?
- Does the syntax match the real schema?
- Are file paths real or creatable?
- Do cross-references point to real targets?
- Do shell commands work on the target OS? (flag POSIX-only tools when running on Windows)
- Do variable substitutions use the real conventions?

## Step 4 — Validate cross-cutting concerns

Beyond per-mechanism checks, verify system-level claims. Same rule: every broken thing gets a before/after fix. Typical things to check:

- Naming and file-placement conventions
- How configuration is read at runtime
- Error handling and failure modes
- How iteration / looping / branching is expressed
- Per-node overrides (model, timeout, context)

## Step 5 — Validate the test plan

If the document has a test plan:
- Are the commands real and executable?
- Are fixture locations sensible?
- Would pass/fail criteria actually be measurable by the described method?

Show corrected commands if any are wrong.

## Step 6 — Write your report

Write a single file to: `$ARTIFACTS_DIR/VALIDATION-REPORT-round-{{ROUND_NUMBER}}.md`

Format exactly:

```markdown
# PRD Validation Report — Round {{ROUND_NUMBER}}

## Summary
- Total items validated: X
- PASS: X
- MINOR: X
- FAIL: X
- AMBIGUOUS: X
- Overall verdict: READY / NEEDS REVISION / BLOCKED

## Top 3 blockers (if any)
1. ...
2. ...
3. ...

## Per-item findings

### M1 — [name]
**Verdict:** ...
**Evidence:** ...
**Problem (if any):** ...
**BEFORE:** ...
**AFTER:** ...
**Why this works:** ...

### M2 — ...
... (continue for every item)

## Cross-cutting findings
(same format)

## Test plan findings
(same format)

## Consolidated apply-these-edits
(if 3+ fixes exist, produce a numbered list of edits grouped by document section, so the fix-applier can process them in one pass)

## Recommendation
One paragraph: is the document ready to execute as written, with what specific edits? Or does it need rework?
```

---

## Report structure rule — CRITICAL for the fix-applier

The fix-applier agent reads your report and applies edits to the document. For it to work, your report MUST:

1. **Use exact BEFORE and AFTER labels in code blocks** — not "original" / "fixed" or any synonym
2. **Preserve exact whitespace and indentation** in BEFORE blocks (so the fix-applier can find them)
3. **Consolidate all fixes into a numbered "apply-these-edits" section** at the end if there are 3 or more, grouped by document section
4. **Never describe a fix without showing it** — "change X to Y" with no block means the fix-applier skips it

If your report doesn't follow these rules, the fix-applier will silently fail to apply your findings and the whole round is wasted.

---

## Verdict emission rule — CRITICAL for the gate

The clean-check gate that runs after you parses the first line that begins with `Overall verdict:` in your report. You MUST emit exactly one of these three strings as the verdict:

- `Overall verdict: READY` (only if 0 FAIL and 0 MINOR)
- `Overall verdict: NEEDS REVISION` (if any FAIL or MINOR found)
- `Overall verdict: BLOCKED` (if the document is so broken you cannot review it)

No other text on that line. No trailing punctuation.

---

## Rules

- Every FAIL or MINOR MUST include the before/after fix
- Be thorough. Accuracy beats speed. 30-60 minutes is expected.
- Cite evidence: source file path + line number, always
- Don't rewrite strategy. Only verify technical correctness.
- Don't execute anything. No commits. No script runs. Only the report file.
- Plain English in prose, but code blocks must be 100% accurate and copy-pasteable
- If the document is mostly right, say so clearly. A clean report is a valid outcome.
- If you cannot find something the document claims is in the reference codebase, that is a FAIL — not AMBIGUOUS.

---

## Context

This is round {{ROUND_NUMBER}} of iterative hardening. Prior rounds (if any) have already applied their fixes to the document. You are checking whether the CURRENT state holds up — not re-validating the original. Find what is broken NOW.
