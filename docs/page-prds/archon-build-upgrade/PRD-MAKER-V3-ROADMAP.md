# PRD Maker V3 — Concrete Solutions for All Weaknesses

> This is the fix plan. Every weakness identified in the audit gets a specific solution: what to add, where to add it, what the prompt/YAML/code looks like, and how it plugs into the existing pipeline.
>
> Goal: move PRD Maker from **7.5/10 → 9.5/10**. True paint-by-numbers. Close the 5% gap where hallucinations still slip through.

---

## Summary of Fixes

| # | Weakness | Solution (1-line) | Effort | Where It Plugs In |
|---|----------|-------------------|--------|-------------------|
| 1 | Paint-by-numbers 70% | Add I/O examples + failure modes block to every mechanism | Small | Stage 6 prompt |
| 2 | No acceptance test per deliverable | Add `verify:` block to every build item | Medium | Stage 7 + Stage 8 |
| 3 | No golden path trace | New stage: "Stage 8.5 — Trace one lead through whole system" | Medium | New stage between 8 and 9 |
| 4 | Reviewer redundancy | Replace 4 generalist reviewers with 2 specialists | Small | Build phase YAML |
| 5 | No red team / devil's advocate | New stage: "Stage 8.75 — Production Failure Red Team" | Small | New stage before phase-1 |
| 6 | No reproducibility | Add run hash + artifact cache + seed lock | Medium | Harness-level + context_packet |
| 7 | Hallucination safety net thin | Programmatic compile check after every phase | Small | New bash node per phase |
| 8 | Platform target buried | Stage 0.5 deployment router (systemd/docker/windows/cloud) | Small | New stage at start |
| 9 | Mechanism boundary blur | Mechanism contract file + boundary enforcement gate | Medium | Stage 6 + new gate |
| 10 | Cross-platform fragility | Replace all bash nodes with node-based cross-platform runners | Large | Harness refactor — defer |

---

## FIX 1 — Paint-by-Numbers: I/O Examples + Failure Modes Per Mechanism

### Problem
Stage 6 produces mechanism specs like "Kokoro TTS wrapper — calls /v1/audio/speech endpoint." A coder can still hallucinate the request body format, the response handling, and error cases. That's the 30% gap.

### Solution
Every mechanism block in Stage 6 output MUST include 3 new subsections:

```markdown
### Mechanism: Kokoro TTS Wrapper

**Inputs (with examples):**
```json
{
  "text": "Hello Mike, this is Sarah from CallPitch...",
  "voice": "af_bella",
  "speed": 1.0
}
```

**Outputs (with examples):**
```
HTTP 200 → binary audio/wav stream (~500KB for 30s speech)
HTTP 400 → {"error": "voice not found"} (caller's bug)
HTTP 500 → {"error": "model overloaded"} (retry after 10s)
HTTP 503 → (no body, service down, retry with backoff)
```

**Failure Modes (what goes wrong + what to do):**
| Failure | Symptom | Recovery |
|---------|---------|----------|
| Kokoro down | Connection refused | Retry 3x with 10s backoff, then fail row |
| Kokoro slow | Timeout after 60s | Kill request, mark row as "tts_timeout", retry in next batch |
| Empty audio | 0-byte response | Log, skip row, no retry (data bug) |
| Invalid voice | HTTP 400 | Hard fail — config error, halt batch |
```

### Implementation

**Update Stage 6 prompt** (`agent-os/prompts/06-mechanisms.md` or equivalent). Add this to the mechanism schema:

```
For EVERY mechanism you produce, you MUST include:
1. Inputs section — at least 1 concrete example as code/JSON block
2. Outputs section — all success responses + all error responses with bodies
3. Failure Modes table — columns: Failure | Symptom | Recovery
   Must cover: network error, timeout, invalid input, service down,
   partial failure (got some data but corrupt)

If you cannot produce these because the PRD lacks detail, FLAG the mechanism
as "INCOMPLETE: needs I/O examples from owner" in your output. Do NOT
proceed to next mechanism without these sections filled.
```

### Where It Plugs In
Stage 6 prompt only. No pipeline YAML changes.

### Effort
**Small.** 30 min of prompt editing + 1 test run to verify format.

---

## FIX 2 — Acceptance Test Per Deliverable

### Problem
Build phases say "create `mp3_generator/db.py`." Coder marks it done by writing any file with that name. No verification it actually works.

### Solution
Every build item in phase files gets a `verify:` block. Example:

```markdown
### Build Item: mp3_generator/db.py

**What to create:** Database wrapper module exposing `get_pending_leads()`,
`update_lead_status()`, `log_failure()`.

**verify:**
```bash
# Self-test: run from project root, must exit 0 with expected output
python -c "
from mp3_generator.db import get_pending_leads, update_lead_status, log_failure
assert callable(get_pending_leads), 'get_pending_leads not defined'
assert callable(update_lead_status), 'update_lead_status not defined'
assert callable(log_failure), 'log_failure not defined'
print('PASS: db.py interface contract met')
"
```
Expected stdout: `PASS: db.py interface contract met`
```

### Implementation

**Update Stage 7 prompt (phase planner)** to emit `verify:` blocks for every build item.

**Add a new bash node after each phase's build-execute:**

```yaml
- id: phase-1-verify-deliverables
  bash: |
    python3 .archon/scripts/verify-deliverables.py "$ARTIFACTS_DIR/phases/phase-1-enriched.md"
  depends_on: [phase-1-execute]
  timeout: 300000
```

**New script `verify-deliverables.py`:**
- Parses phase markdown for all `**verify:**` blocks
- Runs each one in sequence
- Writes `phase-N-verify-report.md` with PASS/FAIL per deliverable
- Exit 1 if any FAIL

### Where It Plugs In
1. Stage 7 prompt (emit verify blocks)
2. Stage 8 prompt (enrich phases with verify preserved)
3. New YAML node per phase (`phase-N-verify-deliverables`)
4. New script `.archon/scripts/verify-deliverables.py`

### Effort
**Medium.** 1 hour prompt work + 1 new script + 3 YAML nodes.

---

## FIX 3 — Golden Path Trace

### Problem
Mechanism specs describe components in isolation. Nobody has traced a single real piece of data through the WHOLE system end to end. That's where integration gaps hide.

### Solution
New stage inserted between stage 8 (phase planning) and stage 9 (codebase intelligence): **Stage 8.5 — Golden Path Trace**.

**What it produces:** A single markdown file `artifacts/golden-path-trace.md` that follows ONE concrete example through the whole system, touching every mechanism:

```markdown
# Golden Path: Lead #42 Journey

## 1. Input State
- Lead ID: 42
- Company: "Acme Plumbing"
- Industry: "home_services"
- Phone: "+15551234567"
- Status: "pending_mp3"

## 2. Mechanism: Batch Orchestrator
Picks up lead #42 because status=pending_mp3 AND priority>=5.
Queries DB with: `SELECT * FROM leads WHERE ... LIMIT 1`.
Row lock acquired: status transitions to "processing".

## 3. Mechanism: Template Engine
Industry "home_services" + tier "A" → selects template `home_services_A.json`.
Variables resolved:
- {{company}} → "Acme Plumbing"
- {{pain_point}} → "missed calls at night"
Renders 4 sections: intro, pain, offer, close.
Output: 4 text blobs, each 40-80 words.

## 4. Mechanism: Kokoro TTS Wrapper
For each of 4 sections, POST to localhost:8881/v1/audio/speech with voice=af_bella.
4 × ~500KB WAV buffers returned.

## 5. Mechanism: Audio Converter
4 WAVs → ffmpeg concat → single MP3 (~45s, ~400KB) at 64kbps mono.
Output path: /tmp/mp3_gen_42.mp3

## 6. Mechanism: R2 Uploader
PUT to bucket=callpitch-mp3, key=2026/04/24/lead-42-home_services-A.mp3.
Public URL returned: https://r2.callpitch.com/lead-42-home_services-A.mp3

## 7. Mechanism: DB Update
UPDATE leads SET status='mp3_ready', mp3_url='...', mp3_generated_at=NOW()
WHERE id=42.

## 8. Mechanism: Alert (skipped — success path)
No Telegram alert. Alert only fires on failure.

## 9. Final State
- Lead 42: status='mp3_ready', mp3_url set
- Log entry written: {"event":"generated","lead_id":42,"duration_ms":8234}
- Files written: 1 MP3 in R2, 0 in local storage (tmp cleaned)

## Questions This Trace Answers
- Does every mechanism know what input it gets? ✓
- Does every mechanism know what to output? ✓
- Are there format gaps between mechanisms? (e.g., template gives strings, TTS expects string — match)
- What happens if 3 sections succeed but 4th TTS fails? → Answered in failure trace below.

## Failure Trace: Lead #43 — Kokoro timeout on section 2
[second trace walks through the error path]
```

### Implementation

**New stage prompt** (`agent-os/prompts/08.5-golden-path-trace.md`):

```
You are tracing ONE specific example through the entire system to find
integration gaps.

INPUT: All mechanism specs + all phase files
TASK:
1. Pick the most representative happy-path example from the PRD
2. Walk it step-by-step through EVERY mechanism in sequence
3. For each mechanism, state: exact input received, exact output produced,
   exact DB/file/network side effects
4. After happy path, pick one failure mode and trace that too
5. Flag any step where you cannot determine the next step from the PRD
   (this is an integration gap — must be fixed)
OUTPUT: golden-path-trace.md

HARD RULES:
- Use real-looking data, not "{{placeholder}}"
- Every mechanism must appear in the trace
- Every trace step must state inputs AND outputs
- If you cannot trace a step, output "GAP: <specific question>" and HALT
```

**YAML node:**
```yaml
- id: golden-path-trace
  command: golden-path-trace
  depends_on: [build-phases]
  model: opus
  context: fresh
  idle_timeout: 600000
```

### Where It Plugs In
Between stage 8 and stage 9. New stage, not a replacement.

### Effort
**Medium.** 1 hour prompt design + 1 new command file + 1 YAML node.

---

## FIX 4 — Replace 4 Generalist Reviewers with 2 Specialists

### Problem
4 reviewers × 3 phases = 12 review passes. They overlap heavily. Each costs ~50K tokens + 3-5 min. Diminishing returns past 2.

### Solution
Replace the 4-reviewer block with 2 specialists:

| Current (4) | Replacement (2) |
|-------------|-----------------|
| review-correctness-logic | `review-correctness-and-contracts` (merged) |
| review-integration | `review-correctness-and-contracts` (merged) |
| review-style-polish | `review-production-readiness` (renamed, expanded) |
| review-security | `review-production-readiness` (merged) |

**Specialist 1: Correctness & Contracts** — catches logic bugs + integration mismatches + interface drift.

**Specialist 2: Production Readiness** — catches security issues + performance issues + logging/observability gaps + edge cases in deployment.

### Implementation

**Update YAML** — delete 2 review nodes per phase, rename 2:

```yaml
# ── BUILD: REVIEW (2 specialists in parallel) ──
- id: review-correctness-and-contracts
  command: review-correctness-and-contracts
  depends_on: [build-verify-compliance]
  model: sonnet
  context: fresh
  retry: { max_attempts: 3, on_error: all }

- id: review-production-readiness
  command: review-production-readiness
  depends_on: [build-verify-compliance]
  model: sonnet
  context: fresh
  retry: { max_attempts: 3, on_error: all }
```

**Create 2 new command prompts** consolidating the 4 existing ones.

### Where It Plugs In
Build phases (phase-1, phase-2, phase-3) in YAML.
Affects: 12 review nodes → 6 review nodes.

### Effort
**Small.** YAML edit + merge 4 prompts into 2.

**Expected time save:** 10-15 min per pipeline run.

---

## FIX 5 — Production Failure Red Team

### Problem
Reviewers play "critique" role. Nobody plays "attacker" role. Nobody asks "what's the dumbest way this could fail in production?"

### Solution
New stage before phase-1-baseline: **Stage 8.75 — Red Team**.

Opus agent, different system prompt:

```
You are a Site Reliability Engineer with 15 years of experience. You have
seen every production disaster. Your job is to predict how this system will
fail in production, NOT to validate the design.

For the PRD + phase plans, produce a ranked list of the 5 most likely
production failures. For each:
- Failure scenario (specific, not vague)
- Root cause chain (what triggers it)
- Blast radius (who/what is affected)
- Detection lag (how long until someone notices)
- Recovery difficulty (minutes/hours/days)
- Prevention (what to add to PRD to catch this before shipping)

HARD RULES:
- No "this looks great" energy. Assume every assumption will be wrong.
- Focus on production ONLY (not build, not dev).
- Rank by probability × impact.
- For each prevention, write the EXACT text to add to a phase file.
- If you cannot find 5 failure modes, go harder — every system has them.
```

Output: `red-team-report.md` with 5 predictions + exact PRD additions to prevent each.

### Implementation

**New command file** `red-team-production.md` (prompt above).

**New YAML node:**
```yaml
- id: red-team-production
  command: red-team-production
  depends_on: [golden-path-trace]
  model: opus
  context: fresh
  idle_timeout: 600000
```

**New gate:** After red-team runs, a Haiku agent reads the report and asks: "Are the prevention items already in phase files? If not, patch them in." Haiku = cheap.

### Where It Plugs In
Between golden-path-trace and codebase intelligence.

### Effort
**Small.** 1 prompt + 1 YAML node + 1 Haiku patch step.

---

## FIX 6 — Reproducibility (Run Hash + Artifact Cache + Seed Lock)

### Problem
Run the same PRD twice, get different output. Can't A/B test. Can't cache partial runs.

### Solution
Three changes:

**a) Seed lock.** Pipeline entry writes a `run-seed.json`:
```json
{
  "run_id": "abc123",
  "prd_input_hash": "sha256:...",
  "pipeline_version": "c-v1.2",
  "started_at": "2026-04-24T02:00:00Z",
  "model_versions": {"opus": "claude-opus-4-7", "sonnet": "claude-sonnet-4-5"}
}
```

**b) Stage output hashing.** After each stage completes, hash the output file and record in `run-ledger.jsonl`:
```json
{"stage": "stage-06-mechanisms", "output_hash": "sha256:...", "duration_ms": 124000}
```

**c) Artifact cache key.** If pipeline restarts after a failure, check ledger. If stage-06 already completed with same input hash, SKIP re-running.

### Implementation

**New script `.archon/scripts/seed-run.py`** — runs first, writes seed.

**Modify context_packet.json schema** — add `run_seed` field carrying the seed through all stages.

**New bash node at pipeline start:**
```yaml
- id: seed-run
  bash: |
    python3 .archon/scripts/seed-run.py "$ARTIFACTS_DIR" "$PRD_INPUT"
```

**New node at end of each stage:**
```yaml
- id: stage-06-checkpoint
  bash: |
    python3 .archon/scripts/record-stage.py "$ARTIFACTS_DIR" "stage-06" "$stage-06-output.file"
  depends_on: [stage-06-output-file-writer]
```

### Where It Plugs In
Every stage of the PRD pipeline. Harness-level integration.

### Effort
**Medium.** 2 new scripts + schema update + ~10 YAML nodes.

**Payoff:** Pipeline restart after failure skips completed stages. Huge time save.

---

## FIX 7 — Programmatic Compile Check (Hallucination Safety Net)

### Problem
Nothing checks that files the phase CLAIMED to create actually exist on disk, are syntactically valid, and export what they claim to export. Reviewer might miss this.

### Solution
After every phase's build-execute, run a compile-check script:

```python
# .archon/scripts/phase-compile-check.py
"""
After a phase runs, verify:
1. Every file listed in phase-N-enriched.md as 'to create' actually exists
2. Every Python file imports cleanly (python3 -c "import ast; ast.parse(open(f).read())")
3. Every function/class declared in the phase file is actually defined in code
4. No phantom imports (importing from a file that doesn't exist yet)
"""
```

### Implementation

**New script:** `.archon/scripts/phase-compile-check.py`

**New YAML node per phase:**
```yaml
- id: phase-1-compile-check
  bash: |
    python3 .archon/scripts/phase-compile-check.py "$ARTIFACTS_DIR" "phases/phase-1-enriched.md"
  depends_on: [phase-1-execute]
  timeout: 120000
```

**Fails pipeline early** if hallucinations detected. Cheaper than a 50K-token reviewer call.

### Where It Plugs In
After build-execute in every phase. Before reviewers. Fails fast.

### Effort
**Small.** 1 script + 3 YAML nodes.

---

## FIX 8 — Platform Deployment Router

### Problem
Current PRDs assume Linux+systemd. If user deploys Docker or Windows or cloud serverless, whole deployment section is wrong.

### Solution
New stage at very start: **Stage 0.5 — Deployment Target Selection**.

Asks (or inspects PRD for hint):
- Target: `linux-systemd` | `docker-compose` | `windows-service` | `aws-lambda` | `cloudflare-workers`
- Writes `deployment-target.json`:
```json
{
  "platform": "linux-systemd",
  "hostname": "server.callpitch.com",
  "runtime": "python3.11",
  "service_manager": "systemd",
  "cron": "systemd-timer"
}
```

**Downstream stages** read this file and emit deployment-specific artifacts:
- If systemd → generate `.service` + `.timer` units
- If docker-compose → generate `Dockerfile` + `docker-compose.yml`
- If cloud → generate terraform/cloudformation/wrangler config

### Implementation

**New stage prompt** `00.5-deployment-target.md` — parses PRD for deployment hints, falls back to asking owner.

**Update Stage 8 prompt** — branches on deployment target when generating deployment phase.

**New YAML node:**
```yaml
- id: deployment-target
  command: deployment-target
  depends_on: [stage-00]
  model: haiku
  context: fresh
```

### Where It Plugs In
Very start of pipeline. All downstream stages read `deployment-target.json`.

### Effort
**Small prompt + Medium downstream.** Prompt is 30 min. Updating stage 8 to branch on target adds ~1 hour.

---

## FIX 9 — Mechanism Boundary Enforcement

### Problem
Your framing is: "AI thinks in named mechanisms, not vague code." But current pipeline doesn't HARD enforce that code stays inside its mechanism. AI can leak mp3_generator logic into alerts.py.

### Solution
Two pieces:

**a) Mechanism contract file** — Stage 6 outputs `mechanism-contracts.json`:
```json
{
  "mechanisms": [
    {
      "name": "batch-orchestrator",
      "files": ["mp3_generator/batch.py", "mp3_generator/__main__.py"],
      "may_import": ["db", "template_engine", "tts_wrapper", "logger"],
      "may_not_import": ["alerts", "r2_uploader"]
    },
    {
      "name": "alerts",
      "files": ["mp3_generator/alerts.py"],
      "may_import": ["logger"],
      "may_not_import": ["db", "batch", "template_engine"]
    }
  ]
}
```

**b) Boundary gate** — new script checks that every file's imports match its mechanism's `may_import` list. Fails build if violated.

### Implementation

**Update Stage 6 prompt** to emit `mechanism-contracts.json`.

**New script:** `.archon/scripts/boundary-check.py`

**New YAML node per phase:**
```yaml
- id: phase-1-boundary-check
  bash: |
    python3 .archon/scripts/boundary-check.py "$ARTIFACTS_DIR"
  depends_on: [phase-1-compile-check]
```

### Where It Plugs In
Stage 6 (output contract) + after each phase (enforcement).

### Effort
**Medium.** Stage 6 prompt update + new script + 3 YAML nodes.

---

## FIX 10 — Cross-Platform Harness (defer)

### Problem
Archon bash nodes fail on Windows due to WSL path issues.

### Solution
Long-term: replace bash nodes with JavaScript runners (`node:` node type in YAML). Short-term: the `python3` swap + baseline fallback already landed in this session.

### Effort
**Large** — harness refactor. Defer. Current pipeline works with the fixes applied today.

---

## Implementation Order (ship-safe)

1. **Land today (cheap + big wins):** Fix 1, Fix 4, Fix 7 (prompt edit + YAML)
2. **Land this week (medium effort, high leverage):** Fix 2, Fix 3, Fix 5
3. **Land next (needs care):** Fix 9, Fix 6
4. **Land when planned:** Fix 8
5. **Defer:** Fix 10 (harness refactor)

---

## Expected Grade After Improvements

| Fix Package | PRD Grade | Paint-by-numbers Grade |
|-------------|-----------|------------------------|
| Today: 1 + 4 + 7 | 8.0/10 | 7.5/10 |
| This week: +2 +3 +5 | 9.0/10 | 8.5/10 |
| Next: +9 +6 | 9.5/10 | 9.0/10 |
| Full V3: all fixes | 9.7/10 | 9.5/10 |

To reach a true 10/10 would need a fundamentally different harness (not Archon) and first-class Windows + reproducibility from the ground up. Not this project.
