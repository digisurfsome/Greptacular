# PRD: Self-Learning Mechanism Tuning System

> The Developer's Choice engine makes good decisions out of the box — but it should
> get *better* the more projects it runs. This PRD defines the feedback loop that
> tracks decision outcomes, suggests threshold adjustments, and gives humans a
> dashboard to manually override or accept those suggestions.

**Status**: PLANNED
**Phase**: Builds on existing `AgentOSMechanism` (4-dim scoring, 3 thresholds, Developer's Choice biases)
**Priority**: HIGH — this is what turns a static scoring engine into an adaptive one

---

## 1. Problem Statement

The mechanism analysis engine has three key thresholds that control when it auto-decides
vs. asks the human:

| Threshold | Default | What It Does |
|---|---|---|
| `auto_select_threshold` | 85% | Score above this → pick automatically |
| `present_alternatives_gap` | 15% | Top two within this gap → show both options |
| `min_viable_score` | 60% | All options below this → must ask human |

Plus 4 Developer's Choice bias weights that tilt close-call decisions toward standards,
simplicity, adoption, or documentation quality.

**The problem**: These numbers are educated guesses. After running 20+ projects, the system
should know whether 85% is too aggressive (auto-picking things that need rework) or too
conservative (asking the human about obvious wins). Today it has no memory of past outcomes.

---

## 2. Solution Overview

Three connected pieces:

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Outcome      │────▶│  Self-Tuning     │────▶│  Tuning Dashboard  │
│  Tracker      │     │  Engine          │     │  (UI Panel)        │
│              │     │                  │     │                    │
│ Logs every    │     │ Analyzes outcomes │     │ Shows current vals │
│ mechanism     │     │ Suggests new      │     │ + suggestions +    │
│ decision +    │     │ thresholds with   │     │ manual sliders     │
│ build result  │     │ confidence        │     │                    │
└──────────────┘     └──────────────────┘     └────────────────────┘
```

### 2.1 Outcome Tracker

Every time the mechanism engine makes a decision, log it. Every time a feature build
finishes (pass/fail/rework), link it back to the decision that chose its approach.

### 2.2 Self-Tuning Engine

After enough samples accumulate (configurable, default 5), analyze the outcomes:
- If auto-selected decisions have a high rework rate → suggest lowering auto_select_threshold
- If human-asked decisions were almost always "just pick the top one" → suggest raising it
- If close-call presentations always result in "pick #1 anyway" → suggest narrowing the gap
- If Developer's Choice bias toward X correlates with rework → suggest reducing that bias

### 2.3 Tuning Dashboard

A UI panel where the human can:
- See current threshold values and what they mean
- See the system's suggestions with reasoning
- Accept suggestions (one-click)
- Manually drag sliders to override
- View the outcome history that drove the suggestions

---

## 3. Data Model

### 3.1 Decision Outcome Record

Stored in `.agent/analytics/mechanism_outcomes.jsonl` (append-only, one JSON per line):

```json
{
  "id": "uuid",
  "timestamp": "2026-02-28T12:00:00Z",
  "project": "my-app",
  "feature_id": 7,
  "decision_point": "Authentication: JWT vs Session Cookies",

  "decision": {
    "chosen": "JWT",
    "confidence": 0.82,
    "auto_selected": false,
    "close_call": true,
    "gap": 0.08,
    "runner_up": "Session Cookies",
    "thresholds_at_time": {
      "auto_select": 85,
      "alternatives_gap": 15,
      "min_viable": 60
    },
    "dc_biases_at_time": {
      "standards": 0.3,
      "simplicity": 0.2,
      "adoption": 0.2,
      "docs": 0.1
    }
  },

  "outcome": null
}
```

When the build finishes, the outcome field gets updated:

```json
{
  "outcome": {
    "timestamp": "2026-02-28T14:30:00Z",
    "result": "passed",
    "rework_needed": false,
    "rework_reason": null,
    "human_override": false,
    "human_override_to": null
  }
}
```

Possible `result` values: `"passed"`, `"failed"`, `"reworked"`, `"skipped"`

### 3.2 Tuning Suggestion Record

Stored in `.agent/analytics/tuning_suggestions.jsonl`:

```json
{
  "id": "uuid",
  "timestamp": "2026-02-28T15:00:00Z",
  "parameter": "auto_select_threshold",
  "current_value": 85,
  "suggested_value": 88,
  "direction": "increase",
  "confidence": 0.72,
  "reasoning": "3 of 12 auto-selected decisions needed rework (25% rework rate). Raising threshold to 88 would have caught 2 of those 3.",
  "sample_size": 12,
  "accepted": null,
  "accepted_at": null
}
```

---

## 4. Backend Implementation

### 4.1 New File: `server/services/agent_os_outcome_tracker.py`

```python
class MechanismOutcomeTracker:
    """Tracks mechanism decisions and their build outcomes for self-tuning."""

    def __init__(self, project_dir: Path, config: dict):
        self.outcomes_file = project_dir / ".agent" / "analytics" / "mechanism_outcomes.jsonl"
        self.suggestions_file = project_dir / ".agent" / "analytics" / "tuning_suggestions.jsonl"
        self.config = config.get("outcome_tracking", {})

    # ── Recording ─────────────────────────────────────────────────

    def record_decision(self, decision: dict, thresholds: dict, biases: dict) -> str:
        """Log a mechanism decision. Returns the outcome ID for later linking."""

    def record_outcome(self, outcome_id: str, result: str,
                       rework_needed: bool = False, rework_reason: str = "",
                       human_override: bool = False, human_override_to: str = "") -> None:
        """Link a build outcome back to a mechanism decision."""

    # ── Analysis ──────────────────────────────────────────────────

    def analyze_outcomes(self) -> list[dict]:
        """Analyze all recorded outcomes and generate tuning suggestions.

        Returns a list of suggestion dicts, one per parameter that should change.
        Only generates suggestions when:
        - sample_size >= min_samples_before_suggest (default 5)
        - enough time since last suggestion (suggestion_cooldown_days)
        """

    def _analyze_auto_select(self, outcomes: list[dict]) -> Optional[dict]:
        """Should auto_select_threshold go up or down?

        Logic:
        - Count auto-selected decisions that needed rework
        - rework_rate = reworks / auto_selects (weighted by rework_penalty)
        - If rework_rate > 15%: suggest raising threshold by (rework_rate * 10) points
        - If rework_rate < 5% AND sample >= 10: suggest lowering by 2 points
        """

    def _analyze_alternatives_gap(self, outcomes: list[dict]) -> Optional[dict]:
        """Should present_alternatives_gap get wider or narrower?

        Logic:
        - Of decisions where alternatives were presented, how often did human pick #1?
        - always_picked_first_rate = picked_first / presented
        - If > 80%: suggest narrowing gap by 3 points (showing options was wasted effort)
        - If < 50%: suggest widening gap by 3 points (close calls genuinely needed human)
        """

    def _analyze_human_required(self, outcomes: list[dict]) -> Optional[dict]:
        """Should min_viable_score go up or down?

        Logic:
        - Of decisions flagged needs_human, how complex was the final answer?
        - If human usually just picked from the presented options: lower threshold
        - If human often said "none of these, do X instead": keep or raise
        """

    def _analyze_dc_biases(self, outcomes: list[dict]) -> list[dict]:
        """Should any Developer's Choice bias weight change?

        Logic:
        - For close-call decisions where DC tiebreaker was applied:
        - Group by which bias contributed most to the winner
        - If that bias-dominant group has high rework: suggest reducing it
        - If low rework: suggest slightly increasing it
        """

    # ── Suggestions ───────────────────────────────────────────────

    def get_pending_suggestions(self) -> list[dict]:
        """Return suggestions that haven't been accepted or rejected."""

    def accept_suggestion(self, suggestion_id: str) -> dict:
        """Accept a suggestion — updates config.yml with the new value."""

    def reject_suggestion(self, suggestion_id: str, reason: str = "") -> None:
        """Reject a suggestion — marks it and logs the reason."""

    # ── Stats ─────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Summary stats for the tuning dashboard."""
        # Returns:
        # {
        #   "total_decisions": 42,
        #   "auto_selected": 28,
        #   "close_calls": 9,
        #   "human_required": 5,
        #   "outcomes_recorded": 35,
        #   "rework_rate": 0.12,
        #   "auto_select_rework_rate": 0.07,
        #   "close_call_first_pick_rate": 0.67,
        #   "pending_suggestions": 2,
        # }
```

### 4.2 Integration Points

**Where decisions get recorded** — `AgentOSMechanism.process_analysis()`:
After computing the analysis result, call `tracker.record_decision()` to log it.

**Where outcomes get linked** — Two places:
1. `feature_mark_passing` MCP tool → `tracker.record_outcome(id, "passed")`
2. `feature_mark_failing` MCP tool → `tracker.record_outcome(id, "failed", rework_needed=True)`

**Where suggestions get generated** — New periodic trigger:
- After every Nth outcome (configurable, default: every 5)
- On explicit "analyze now" API call from dashboard
- On project completion (all features done)

### 4.3 New API Endpoints

Add to `server/routers/dunkstack.py` (or new `mechanism_tuning.py` router):

```
GET  /api/dunkstack/mechanism/thresholds?project={name}
     → Current threshold values + defaults + last-modified timestamp

GET  /api/dunkstack/mechanism/outcomes?project={name}&limit=50
     → Paginated list of decision outcomes

GET  /api/dunkstack/mechanism/stats?project={name}
     → Summary stats for dashboard

GET  /api/dunkstack/mechanism/suggestions?project={name}
     → Pending tuning suggestions

POST /api/dunkstack/mechanism/suggestions/{id}/accept
     → Accept suggestion, update config.yml

POST /api/dunkstack/mechanism/suggestions/{id}/reject
     → Reject suggestion with optional reason

POST /api/dunkstack/mechanism/analyze?project={name}
     → Trigger fresh analysis of outcomes → new suggestions

PATCH /api/dunkstack/config  (already exists, now accepts agent_os section)
     → Manual threshold override via sliders
```

---

## 5. Frontend Implementation

### 5.1 New Component: `MechanismTuningPanel.tsx`

Location: `ui/src/components/dunkstack/MechanismTuningPanel.tsx`

Layout (fits in DunkStack page as a collapsible panel):

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙ Mechanism Tuning                              [Analyze Now] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Thresholds                          Decision Stats             │
│  ┌──────────────────────────────┐   ┌─────────────────────────┐│
│  │ Auto-Select    [====|==] 85% │   │ 42 total decisions      ││
│  │ Close-Call Gap [===|===] 15% │   │ 28 auto-selected (67%)  ││
│  │ Human Required [==|====] 60% │   │  9 close calls (21%)    ││
│  └──────────────────────────────┘   │  5 human required (12%) ││
│                                     │                         ││
│  Developer's Choice Biases          │ Rework rate: 12%        ││
│  ┌──────────────────────────────┐   │ Auto-select rework: 7%  ││
│  │ Standards  [======|==] 0.30  │   │ Close-call #1 pick: 67% ││
│  │ Simplicity [====|====] 0.20  │   └─────────────────────────┘│
│  │ Adoption   [====|====] 0.20  │                               │
│  │ Docs       [==|======] 0.10  │                               │
│  └──────────────────────────────┘                               │
│                                                                 │
│  💡 Suggestions (2 pending)                                     │
│  ┌──────────────────────────────────────────────────────────────┤
│  │ ▲ auto_select_threshold: 85% → 88%                          │
│  │   "3 of 12 auto-selects needed rework (25%). Raising to     │
│  │    88% would have caught 2 of those 3."                     │
│  │   Based on 12 samples · Confidence: 72%                     │
│  │   [Accept] [Reject]                                         │
│  ├──────────────────────────────────────────────────────────────┤
│  │ ▼ present_alternatives_gap: 15% → 12%                       │
│  │   "8 of 9 close calls resulted in picking option #1 anyway. │
│  │    Narrowing the gap saves human review time."              │
│  │   Based on 9 samples · Confidence: 65%                      │
│  │   [Accept] [Reject]                                         │
│  └──────────────────────────────────────────────────────────────┘
│                                                                 │
│  Recent Outcomes (last 10)                          [View All]  │
│  ┌────┬────────────────────────┬───────┬──────────┬───────────┐│
│  │ #  │ Decision               │ Score │ Auto?    │ Outcome   ││
│  ├────┼────────────────────────┼───────┼──────────┼───────────┤│
│  │ 7  │ Auth: JWT vs Sessions  │  82%  │ Close    │ ✅ Passed ││
│  │ 6  │ DB: Postgres vs SQLite │  91%  │ Auto ✓   │ ✅ Passed ││
│  │ 5  │ CSS: Tailwind vs MUI   │  78%  │ Close    │ 🔄 Rework ││
│  │ 4  │ API: REST vs tRPC      │  88%  │ Auto ✓   │ ✅ Passed ││
│  └────┴────────────────────────┴───────┴──────────┴───────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Slider Behavior

- Sliders update via `PATCH /api/dunkstack/config` with the `agent_os` section
- Changes take effect immediately for the next mechanism analysis
- Slider shows the default value as a subtle marker on the track
- If a suggestion was accepted, show "(was X, adjusted to Y)" annotation

### 5.3 Suggestion Cards

- Each suggestion shows: parameter, current → proposed, reasoning, sample size, confidence
- [Accept] writes new value to config via API, marks suggestion as accepted
- [Reject] opens a small text input for optional reason, marks as rejected
- Suggestions with confidence < 50% show a "low confidence" badge

---

## 6. Self-Tuning Algorithm Details

### 6.1 Auto-Select Threshold Adjustment

```
INPUT: all outcomes where auto_selected == true
COMPUTE: rework_rate = (reworks * rework_penalty) / total_auto
IF rework_rate > 0.15:
    suggested_delta = +round(rework_rate * 10)  # e.g., 25% rework → +3
    new_threshold = min(95, current + suggested_delta)
    confidence = min(0.9, sample_size / 20)
ELIF rework_rate < 0.05 AND sample_size >= 10:
    new_threshold = max(70, current - 2)
    confidence = min(0.7, sample_size / 30)
ELSE:
    no suggestion (current value is working)
```

### 6.2 Alternatives Gap Adjustment

```
INPUT: all outcomes where close_call == true
COMPUTE: first_pick_rate = picked_option_1 / total_close_calls
IF first_pick_rate > 0.80 AND sample_size >= 5:
    new_gap = max(5, current_gap - 3)   # Narrow: showing alternatives is noise
    confidence = min(0.8, sample_size / 15)
ELIF first_pick_rate < 0.50 AND sample_size >= 5:
    new_gap = min(30, current_gap + 3)  # Widen: human input is valuable
    confidence = min(0.8, sample_size / 15)
```

### 6.3 Developer's Choice Bias Adjustment

```
INPUT: all outcomes where dc_applied == true, grouped by dominant_bias
FOR EACH bias:
    rework_rate_when_dominant = reworks / decisions_where_this_bias_won
    IF rework_rate_when_dominant > 0.25:
        suggest reducing bias by 0.05
    ELIF rework_rate_when_dominant < 0.05 AND sample >= 8:
        suggest increasing bias by 0.05
CONSTRAINT: all biases must sum to <= 1.0 (remainder goes to raw_weight)
```

### 6.4 Cross-Project Learning (Future)

Currently scoped to per-project learning. Future enhancement:
- Aggregate outcomes across all projects in the registry
- Weight recent projects higher than old ones
- New projects start with the global learned values instead of hardcoded defaults
- Config key: `outcome_tracking.cross_project_learning: true`

---

## 7. Config Schema (Already Added)

The `agent_os:` section in `.agent/settings/config.yml`:

```yaml
agent_os:
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
  outcome_tracking:
    enabled: true
    min_samples_before_suggest: 5
    rework_penalty: 2.0
    suggestion_cooldown_days: 7
```

---

## 8. Implementation Phases

### Phase 1: Outcome Tracking (Foundation)
- `MechanismOutcomeTracker` class with record/read methods
- Wire into `AgentOSMechanism.process_analysis()` to log decisions
- Wire into feature MCP tools to log outcomes
- JSONL storage in `.agent/analytics/`
- **Effort**: ~200 lines Python

### Phase 2: Self-Tuning Engine
- `analyze_outcomes()` with the 4 analysis methods
- Suggestion generation and storage
- Accept/reject flow that writes back to config.yml
- **Effort**: ~300 lines Python

### Phase 3: API Endpoints
- 7 new endpoints on the dunkstack router
- Suggestion accept/reject with config write-back
- **Effort**: ~150 lines Python

### Phase 4: Tuning Dashboard UI
- `MechanismTuningPanel.tsx` component
- Sliders wired to `PATCH /api/dunkstack/config`
- Suggestion cards with accept/reject
- Outcome history table
- Stats summary
- **Effort**: ~400 lines TSX

### Phase 5: Cross-Project Learning (Future)
- Global outcome aggregation across registry
- New project inherits global learned values
- **Effort**: ~200 lines Python + config migration

---

## 9. Success Metrics

After 10+ projects:
- Auto-select rework rate drops below 10%
- Human override rate on close calls drops below 30%
- Average time spent on mechanism review per feature drops by 40%
- System suggests at least 3 threshold adjustments that get accepted

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Too few samples to learn from | `min_samples_before_suggest` prevents premature suggestions |
| Overfitting to one project type | Cross-project learning (Phase 5) with recency weighting |
| User ignores suggestions | Suggestions are non-blocking; system works fine on defaults |
| Runaway threshold drift | Hard limits: auto_select 70-95, gap 5-30, viable 40-80 |
| Rework detection is imprecise | Start with binary pass/fail from MCP tools; refine later |

---

## 11. Dependencies

- **EXISTS**: `AgentOSMechanism` with 3 thresholds + DC biases (agent_os_mechanism.py)
- **JUST ADDED**: `agent_os:` section in config.yml + `ConfigUpdate.agent_os` field
- **JUST FIXED**: Unified `auto_select_threshold` config path in agent_os_features.py
- **NEEDED**: Feature MCP tools emitting outcome events (minor hook addition)

---

## 12. Open Questions

1. Should the dashboard show per-project or global stats by default?
2. Should accepted suggestions trigger a WebSocket notification to connected UIs?
3. Should there be an "undo" for accepted suggestions (revert to previous value)?
4. Should the system auto-accept high-confidence suggestions (>90%) without human approval?
