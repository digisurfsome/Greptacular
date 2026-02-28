# PRD Machine Completion — Standards Layer

> Agent OS Standards Document | Referenced by all phase blueprints

---

## 1. Scope

This blueprint completes the PRD Machine (Agent OS) by adding the 16 missing items
identified in `docs/DUNKSTACK_FULL_INVENTORY.md` List 1. It does NOT add features
from List 2 (those are separate systems).

**What we're building INTO**: The existing 8-stage Agent OS pipeline in
`server/services/agent_os_*.py` and `server/routers/agent_os.py`.

**What we're NOT touching**: The IdeaForge Workspace, Universal Dashboard,
Walkie-Talkie, Holding Patterns, or any List 2 features.

---

## 2. Technology Stack (Inherited)

All technology choices are inherited from the existing Agent OS implementation.
No new packages required.

| Layer | Technology | Already In Use |
|-------|-----------|----------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite | Yes |
| Frontend | React 19, TypeScript, Vite 7, TanStack Query, Tailwind v4 | Yes |
| AI | Claude Agent SDK (`claude_agent_sdk`) | Yes |
| AI (lightweight) | `anthropic` Python SDK (for verification agents) | Yes (used in workspace auto-summary) |

---

## 3. Existing Pipeline (Current State)

```
Stage 0: Intake Dock ......... agent_os_intake_dock.py  (file staging)
Stage 1: Intake .............. agent_os_intake.py       (classify + extract)
Stage 2: Standards ........... agent_os_standards.py    (questionnaire)
Stage 3: Product Discovery ... agent_os_product.py      (6 questions)
Stage 4: Feature Extraction .. agent_os_features.py     (features + gaps)
Stage 5: Gap Analysis ........ agent_os_features.py     (cross-layer gaps)
Stage 6: Spec Generation ..... agent_os_specs.py        (per-feature specs)
Stage 7: Database Population . agent_os_handoff.py      (features.db)
Stage 8: Handoff ............. agent_os_handoff.py      (context primer)
```

**Cross-stage services:**
- `agent_os_mechanism.py` — Developer's Choice scoring (4 dimensions)
- `agent_os_expand.py` — Post-build feature addition
- `agent_os_codebase.py` — Retrofit from existing code
- `agent_os_file_utils.py` — 3-layer file I/O
- `agent_os_session.py` — WebSocket session orchestration

---

## 4. Target Pipeline (After Completion)

```
Stage 0:   Intake Dock ............. (exists)
Stage 1:   Intake .................. (exists, enhanced)
Stage 1.5: Transcription Verifier .. NEW
Stage 2:   Standards ............... (exists)
Stage 3:   Product Discovery ....... (exists)
Stage 3.5: Technical Refinement .... NEW
Stage 4:   Feature Extraction ...... (exists)
Stage 4.5: Coverage Assessment ..... NEW (metrics surfacing)
Stage 5:   Recalibration ........... NEW
Stage 5.5: Gap Analysis ............ (exists, renumbered)
Stage 6:   Mechanism Analysis ...... (exists, enhanced to 6 dimensions)
Stage 6.5: Mechanism Verifier ...... NEW
Stage 7:   Spec Generation ......... (exists, enhanced with provenance)
Stage 7.5: PRD Verifier ............ NEW
Stage 8:   Database Population ..... (exists)
Stage 9:   Final Blueprint ......... NEW (companion sheet)
Stage 10:  Golden Orange ........... NEW (feature imagination)
Stage 11:  Quality Gate ............ NEW (PRD scoring)
Stage 12:  Handoff ................. (exists, enhanced)
```

**New stages: 8** | **Enhanced stages: 4** | **Unchanged: 4**

---

## 5. File Naming Convention

All new files follow the existing pattern:

| Type | Pattern | Example |
|------|---------|---------|
| Service | `server/services/agent_os_{name}.py` | `agent_os_refinement.py` |
| Verifier | `server/services/agent_os_verify_{stage}.py` | `agent_os_verify_transcription.py` |
| Router | Added to existing `server/routers/agent_os.py` | N/A |
| Tests | `test_agent_os_{name}.py` | `test_agent_os_refinement.py` |

---

## 6. Constants & Configuration

### New config.yml Entries

```yaml
agent_os:
  # Existing (unchanged)
  mechanism_analysis:
    auto_select_threshold: 85
    present_alternatives_gap: 15
    min_viable_score: 60
  developers_choice:
    enabled: true
    bias_toward_standards: 0.3
    bias_toward_simplicity: 0.2
    bias_toward_adoption: 0.2
    bias_toward_docs: 0.1
  auto_select_threshold: 85
  max_features_per_expansion: 5

  # NEW — Verification
  verification:
    enabled: true                  # Master toggle for all verifiers
    max_retries: 1                 # Re-run worker on fail (0 = no retry)
    model: "sonnet"                # Verifiers always use Sonnet (cheaper)
    fail_on_critical: true         # Block pipeline if critical issues found

  # NEW — Technical Refinement
  refinement:
    preserve_original_quotes: true # Always show babble -> tech pairs
    require_user_confirmation: false # Auto-advance if no contradictions

  # NEW — Coverage Assessment
  coverage:
    show_percentage: true          # Display "You've described ~45% of the app"
    detailed_user_baseline: 0.65   # Expected for detailed input
    average_user_baseline: 0.20    # Expected for average input

  # NEW — Scoring Dimensions (6-dimension model)
  scoring_dimensions:
    implementation_speed: 0.20
    maintainability: 0.20
    user_experience: 0.20
    security: 0.15
    cost: 0.10
    brand_alignment: 0.15

  # NEW — Caveat Appendix
  caveat_appendix:
    max_alternatives: 3            # N-way close call support
    worktree_threshold: 10         # Score gap % below which worktrees created
    worktree_cost_threshold: "medium" # Minimum switch cost for worktree

  # NEW — PRD Quality Gate
  quality_gate:
    enabled: true
    minimum_score: 2.0             # Block build if below
    warning_score: 3.0             # Warn if below
    dimensions:
      completeness: 0.25
      clarity: 0.20
      consistency: 0.15
      feasibility: 0.15
      testability: 0.15
      scope: 0.10

  # NEW — Golden Orange
  golden_orange:
    enabled: true
    categories:
      - natural_extensions
      - cross_mechanism
      - competitive
      - scale
      - monetization
      - delight
    utopia_line: true              # Mark diminishing returns boundary

  # NEW — Provenance Tracking
  provenance:
    enabled: true
    tags:
      - USER
      - AUTO_FILL
      - USER_DECIDED
      - RECOMMENDED
      - DETECTED
      - DESCRIBED
      - INFERRED
```

---

## 7. Provenance Tag System

Every item in the pipeline carries a provenance tag from the moment it enters.
Tags propagate downstream and are preserved in the final PRD.

| Tag | Meaning | Set By |
|-----|---------|--------|
| `[USER]` | Directly stated by user in rant/input | Intake (Stage 1) |
| `[AUTO_FILL]` | System inferred with high confidence | Gap Analysis auto-resolve |
| `[USER_DECIDED]` | User chose from presented options | Gap Analysis manual resolve |
| `[RECOMMENDED]` | Developer's Choice, user accepted | Mechanism Analysis |
| `[DETECTED]` | Reverse-engineered from code | Codebase Analyzer |
| `[DESCRIBED]` | User described existing behavior | Intake (Stage 1) |
| `[INFERRED]` | System inferred from context | Feature Extraction |
| `[FEATURE_ADD_vN]` | Added in expansion round N | Expand service |

**Implementation**: Add `provenance: str` field to entity dicts, feature dicts,
gap dicts, and spec content. Propagate through all `process_*()` methods.

---

## 8. LLM Orchestration Pattern

The current pipeline generates prompts but never sends them to Claude.
The orchestration pattern is:

```python
async def _execute_llm_stage(self, prompt: str, model: str = "sonnet") -> dict:
    """Send prompt to Claude, parse JSON response."""
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    response = await client.messages.create(
        model=self._resolve_model(model),
        max_tokens=16384,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    # Extract JSON from markdown fences if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    return json.loads(text)
```

**Model resolution**: Uses `ANTHROPIC_DEFAULT_SONNET_MODEL` env var for Sonnet,
`ANTHROPIC_DEFAULT_OPUS_MODEL` for Opus. Verifiers always use Sonnet.

**Token tracking**: Every LLM call records `input_tokens` and `output_tokens`
from the API response for the Context Gauge and quality metrics.

---

## 9. Anti-Patterns

1. **DO NOT** add new npm packages — everything works with existing dependencies
2. **DO NOT** modify assistant_chat_session.py or any non-agent_os service files
3. **DO NOT** create a separate database — all Agent OS state uses the existing
   file-based approach (`.agent/` directory) plus config.yml
4. **DO NOT** use Agent SDK for verifiers — use the `anthropic` Python SDK directly
   for lightweight one-shot calls (same pattern as workspace auto-summary)
5. **DO NOT** change the existing stage numbering in the session — use sub-stages
   (1.5, 3.5, etc.) that are internal to the pipeline, not exposed to the session UI
6. **DO NOT** block the pipeline on optional stages — verification, golden orange,
   and quality gate should all be toggleable via config.yml
7. **DO NOT** hardcode scoring weights — all weights come from config.yml
8. **DO NOT** skip provenance tagging — every item must carry its tag from birth

---

## 10. Testing Strategy

Each new service gets a test file:

```
test_agent_os_refinement.py        # Technical Refinement
test_agent_os_recalibration.py     # Recalibration
test_agent_os_verify.py            # All verifiers (shared patterns)
test_agent_os_quality_gate.py      # PRD Quality scoring
test_agent_os_golden_orange.py     # Feature imagination
test_agent_os_blueprint.py         # Final Blueprint (companion sheet)
test_agent_os_provenance.py        # Provenance tag propagation
test_agent_os_orchestration.py     # LLM orchestration (mocked)
```

**Test pattern**: Mock the `anthropic` client, provide canned JSON responses,
verify that `process_*()` methods produce correct output.

---

## 11. Quick Reference Card

| Item | Value |
|------|-------|
| New service files | 8 |
| Modified service files | 4 (mechanism, features, specs, session) |
| New verifier files | 3 (transcription, mechanism, PRD) |
| Config sections added | 7 |
| Provenance tags | 8 |
| Scoring dimensions | 6 (up from 4) |
| Quality gate dimensions | 6 |
| Golden Orange categories | 6 |
| Max close-call alternatives | 3 (up from 2) |
| Verifier model | Sonnet (always) |
| Verifier temperature | 0 (always) |
| Pipeline stages (total) | 16 (was 9) |
| Pipeline stages (user-visible) | 12 (sub-stages are internal) |
