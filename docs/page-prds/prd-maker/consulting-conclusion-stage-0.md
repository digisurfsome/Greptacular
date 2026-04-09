# Stage 0 Consulting Conclusion

Date: 2026-04-02
Scope: Documentation only. No build/code execution.

## Decision: Use The Current Trial Checklist Now

Verdict: **Yay, use it now** as the working baseline.

Rationale:
- Your current direction is structurally correct.
- Waiting for perfect coverage will slow the system-level validation you need.
- The pipeline quality will improve faster by running one full end-to-end pass, then tightening weak stages.

Constraint:
- Stage 0 must add explicit contracts and default behaviors before broad testing.

## What Stage 0 Must Do

Stage 0 is a deterministic preamble and targeting layer that runs before Idea Capture/Gap Analysis.

Stage 0 objective:
- Constrain scope.
- Load known technical truths.
- Separate "already handled structure" from "unknown app mechanisms".
- Emit a contract for Stage 1 and Stage 2.

## Stage 0 Canonical Order

1. **Context Intake**
- Capture: greenfield vs existing app, web/mobile/dual, target stack, repo source, deployment target.
- Capture confidence score for each field (`known`, `inferred`, `assumed`).

2. **Boilerplate/Profile Resolution**
- Select one profile:
  - `web-supabase`
  - `mobile-flutter-supabase`
  - `dual-web-mobile-supabase`
  - `no-boilerplate`
  - `bring-your-own`
- If profile unknown, assign deterministic default profile and mark assumption.

3. **Martin Rules Preamble Injection**
- Load checklist version of Martin guidance, not narrative.
- For each rule: mark `MATCH`, `REPLACE`, `ENHANCE`, or `HANDLED`.
- Produce resolved rule pack for this run.

4. **Structural Target Model (30 Categories)**
- Instantiate full target map of required app-spec categories.
- Mark each category coverage status (`covered by preamble`, `provided by user`, `missing`).

5. **Mechanism Target Model (A-N Categories)**
- Map user idea text into mechanism categories.
- Identify mechanism gaps and unresolved decisions.

6. **Question Budget + Clarification Strategy**
- If user gives full detail: ask only blocking questions.
- If user gives 1-3 sentences: run deterministic fill using defaults + assumption log.
- Enforce maximum question rounds before fallback inference.

7. **Stage Contracts Emission**
- Emit `Stage-0-Contract` and `Stage-1 Input Pack`.
- Include stop/go criteria and unresolved blockers.

## Required Stage 0 Artifacts

1. `stage-0-context.json`
- Resolved stack, platform, profile, confidence levels, assumptions.

2. `stage-0-rules-preamble.md`
- Martin checklist resolved for this profile (`MATCH/REPLACE/ENHANCE/HANDLED`).

3. `stage-0-coverage-matrix.md`
- 30 structural categories x coverage status.
- A-N mechanism categories x evidence status.

4. `stage-0-open-questions.md`
- Ranked list of blocking unknowns only.

5. `stage-0-contract.md`
- Definition of done for Stage 0 and entry criteria for Stage 1/2.

## Contract System (Must Add)

Every stage should have the same contract shape:

1. **Goal**
- What this stage must produce.

2. **Inputs**
- Required artifacts and assumptions.

3. **Process Constraints**
- What the agent is forbidden to reinvent or change.

4. **Exit Artifacts**
- Exact files/objects that must exist.

5. **Quality Gates**
- Deterministic checks (pass/fail).

6. **Failure Modes**
- What to do if gate fails.

7. **Handoff Conditions**
- What next stage is allowed to consume.

## Defaults For Low-Input Users (3-Sentence Mode)

When user input is minimal, Stage 0 should auto-fill with explicit assumptions:

- Assistant/tooling default: `Claude Code` (if run internally).
- Data layer default: `Supabase`.
- Payments default: `Stripe` (only if monetization signal present).
- Auth default: boilerplate-native auth stack.
- UI source default priority:
  1. Image-derived style system (if image provided)
  2. Style picker (if user selects)
  3. Martin clean baseline style rules

Rule:
- Defaults must be logged as assumptions with confidence and reversal cost.

## What To Keep From Martin vs What To Relax

Keep as hard constraints:
- Build hygiene, structure, naming discipline, anti-pattern bans.
- Security, auth boundaries, state/data handling consistency.
- Deterministic component and testing standards.

Make soft guidance:
- "Only 5 features" becomes recommendation, not hard blocker.
- Provider-specific assumptions (Gemini/Firebase) become provider-agnostic mappings.

## Critical Additions You Were Missing (Add Now)

1. **Non-Functional Requirement Budgets**
- Latency, reliability, cost, scale, security, maintainability targets.

2. **Data Governance/Compliance Lens**
- PII handling, retention/deletion, auditability, regional constraints.

3. **Observability Requirements**
- Required logs, metrics, traces, alert thresholds per mechanism.

4. **Change Risk + Rollback Plan**
- Migration safety, rollback path, feature flags, blast radius notes.

5. **Decision Log**
- Every inferred decision tagged with source and confidence.

6. **Assumption Burn-Down**
- Track assumptions to resolve in later stages.

7. **Verification Harness Definition**
- Define exactly what Stage 9 verifier checks against (contract-linked assertions).

8. **Out-of-Scope Guardrail**
- Explicitly state what this build pass will not include.

## Recommended Mapping Logic For Martin Checklist

For each Martin checklist item:
- `MATCH`: carry unchanged.
- `REPLACE`: swap provider-specific implementation.
- `ENHANCE`: keep rule + add boilerplate file pointers.
- `HANDLED`: lock as "do not recreate".
- `N/A`: not relevant to selected profile.

Add fields:
- `priority` (`critical`, `important`, `nice`)
- `enforcement` (`hard`, `soft`)
- `evidence` (file path, config, or test artifact)

## Stage 0 Success Criteria

Stage 0 is complete only when:
- Profile is resolved (or defaulted with assumptions logged).
- Rules preamble is resolved and provider-agnostic where needed.
- 30-category structural coverage map exists.
- A-N mechanism map exists with missing items highlighted.
- Blocking questions are isolated from non-blocking questions.
- Stage contract is emitted with pass/fail gates.

## Immediate Next Action (Documentation-Only)

1. Freeze this as `v0.1` baseline.
2. Run one full 10-stage dry run on a single app idea.
3. Score each stage against its contract (pass/fail + defect notes).
4. Patch only the lowest-performing stage contracts first.

---

This conclusion is optimized for deterministic execution first, then iterative refinement.

## Pipeline Crosswalk (0-10) With Skill Anchors

Use this as the first-pass mapping for where each skill pattern belongs.

0. **Technical Framing + Preamble Resolution**
- Sources: Martin checklist transform + boilerplate matcher + assumptions/contracts.
- Output: `stage-0-*` artifacts listed above.

1. **Idea Capture (Rant Intake)**
- Best pattern: high-tolerance intake flow similar to ideation pipelines.
- Requirement: preserve user language verbatim before normalization.

2. **Gap Analysis**
- Best pattern: confidence-scored questioning (ask only what is blocking).
- Requirement: compare against structural + mechanism target matrices.

3. **Agent OS Structuring**
- Best pattern: strict section templates and immutable required headings.
- Requirement: no unscoped creativity; enforce canonical document layout.

4. **Mechanism Extraction**
- Best pattern: mechanism category mapping (A-N) with evidence lines.
- Requirement: each mechanism must map to at least one user statement or explicit inference.

5. **7-Question Scaffolding**
- Best pattern: deterministic question packet per mechanism.
- Requirement: unanswered items become explicit assumptions, not hidden guesses.

6a. **Arrangement Selection**
- Best pattern: finite option set with tradeoff scoring.
- Requirement: one selected arrangement + rejected alternatives with reason.

6b. **Page Mockups**
- Best pattern: page-by-page component intent, not implementation details.
- Requirement: each page ties to one or more mechanisms.

6c. **Style Selection**
- Best pattern: style source precedence (image -> picker -> baseline).
- Requirement: produce reusable style token set, not only narrative.

7. **Phase Sequencing**
- Best pattern: dependency-aware ordering and sandbox boundaries.
- Requirement: every phase has clear scope and deliverable.

8. **Protocol Injection**
- Best pattern: checkpoints/pulse/seam controls bound to phase gates.
- Requirement: protocol checks must reference stage contracts.

9. **Verification Agent Setup**
- Best pattern: independent verifier with assertions, no author bias.
- Requirement: verifier checks contracts, not subjective quality.

10. **Output Packaging**
- Best pattern: deterministic output tree + runnable sequence docs.
- Requirement: publish artifacts with provenance and version tags.

## Skill-Creation Operating Standard (Reference Baseline)

Use your selected `skill-creator` approach as the build discipline for each stage skill:
- Intent capture and interview flow
- Draft SKILL spec creation
- Evaluation with assertions
- Grading and iteration loop
- Description optimization for trigger precision
- Packaging/versioning

Definition:
- A stage skill is "ready" only when it passes its assertion suite at agreed threshold and has low trigger ambiguity.

## Multi-Agent Comparison Rubric (For Consensus Runs)

When multiple agents review the same stage, score each proposal on:

1. Determinism (0-5)
- Does it minimize open-ended behavior?

2. Coverage (0-5)
- Does it cover structural + mechanism needs for that stage?

3. Boilerplate Awareness (0-5)
- Does it correctly reuse handled systems instead of recreating?

4. Contract Clarity (0-5)
- Are entry/exit gates objective and testable?

5. Low-Input Robustness (0-5)
- Does it still work when user provides only 1-3 sentences?

6. Operational Cost (0-5)
- Is token/time/question overhead controlled?

Decision rule:
- Choose highest weighted total.
- If tie, prefer higher determinism + contract clarity.
