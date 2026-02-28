# Complete Inventory: Every Adjustable Lever in the System

> Every pure number, percentage, weight, threshold, limit, and timing value
> that could theoretically have a slider, dial, or config toggle.
> Organized by subsystem. "Configurable?" = YES means it reads from config today.

---

## Category A: PRD Machine / Mechanism Analysis

These are the "brain" of the Developer's Choice engine. They decide when to auto-pick,
when to show alternatives, and when to ask the human.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| A1 | `auto_select_threshold` | 85% | agent_os_mechanism.py:133 | Score above this → auto-pick without asking | YES (config.yml) |
| A2 | `present_alternatives_gap` | 15% | agent_os_mechanism.py:124 | Top two within this gap → show both options | YES (config.yml) |
| A3 | `min_viable_score` | 60% | agent_os_mechanism.py:196 | All below this → must ask human | YES (config.yml) |
| A4 | `bias_toward_standards` | 0.30 | agent_os_mechanism.py:159 | DC weight for standards alignment | YES (config.yml) |
| A5 | `bias_toward_simplicity` | 0.20 | agent_os_mechanism.py:160 | DC weight for simpler implementation | YES (config.yml) |
| A6 | `bias_toward_adoption` | 0.20 | agent_os_mechanism.py:161 | DC weight for ecosystem adoption | YES (config.yml) |
| A7 | `bias_toward_docs` | 0.10 | agent_os_mechanism.py:162 | DC weight for documentation quality | YES (config.yml) |
| A8 | `auto_select_threshold` (features) | 85% | agent_os_features.py:324 | Gap analysis auto-fill confidence | YES (config.yml) |

**Self-tuning potential**: HIGH — these are the prime targets for the learning loop.
Every build produces signal on whether these were set right.

---

## Category B: Context Safety / Session Management

These control when the agent gets warned, forced to hand off, or hard-stopped
due to context window exhaustion.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| B1 | `warning_threshold_pct` | 45% | config.yml:28 | Tier 1: agent gets a warning | YES (config.yml) |
| B2 | `handoff_threshold_pct` | 47.5% | config.yml:29 | Tier 2: stop coding, write handoff | YES (config.yml) |
| B3 | `hard_stop_threshold_pct` | 50% | config.yml:30 | Tier 3: kill session | YES (config.yml) |
| B4 | `post_stop_review` | true | config.yml:31 | Run code review after hard stop | YES (config.yml) |
| B5 | `model_limit` | 200,000 | config.yml:32 | Context window size in tokens | YES (config.yml) |
| B6 | `utilization_target` | 85% | config.yml:18 | % of context window to use | YES (config.yml) |
| B7 | `working_memory_frequency` | 3 | config.yml:19 | Update working memory every N turns | YES (config.yml) |
| B8 | `file_read_budget` | 4,000 | config.yml:20 | Max tokens per turn on file reads | YES (config.yml) |
| B9 | `api_response_max_sentences` | 3 | config.yml:21 | Max sentences in chat response | YES (config.yml) |
| B10 | `idle_cycle_seconds` | 300 | config.yml:24 | Wait between heartbeats (5 min) | YES (config.yml) |
| B11 | `bridge_on_end` | true | config.yml:25 | Auto-save state on session end | YES (config.yml) |

**Self-tuning potential**: MEDIUM — B1/B2/B3 could shift based on observed context exhaustion
rates. If builds consistently crash at 48%, maybe lower the warning earlier.

---

## Category C: Build Agent Session Control

These control how many turns agents get, context budgets, and auto-continue delays.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| C1 | `max_turns` (coding) | 150 | client.py:354 | Max turns for coding agent | NO (hardcoded map) |
| C2 | `max_turns` (testing) | 75 | client.py:355 | Max turns for testing agent | NO (hardcoded map) |
| C3 | `max_turns` (initializer) | 200 | client.py:356 | Max turns for initializer | NO (hardcoded map) |
| C4 | `max_turns` (reviewer) | 100 | client.py:357 | Max turns for review agent | NO (hardcoded map) |
| C5 | `max_turns` (QA) | 250 | client.py:358 | Max turns for QA agent | NO (hardcoded map) |
| C6 | `max_turns` (spec-analyzer) | 75 | client.py:359 | Max turns for spec analyzer | NO (hardcoded map) |
| C7 | `max_turns` (architect) | 100 | client.py:360 | Max turns for architect | NO (hardcoded map) |
| C8 | `AUTO_CONTINUE_DELAY_SECONDS` | 3 | agent.py:53 | Delay between auto-continue sessions | NO (hardcoded) |
| C9 | `MAX_CODING_TURNS` | 150 | agent.py:60 | Hard ceiling on coding turns | NO (hardcoded) |
| C10 | `BUDGET_USABLE_TURNS` | 120 | parallel_orchestrator.py:143 | Turns available for implementation | NO (hardcoded) |
| C11 | `TURNS_PER_STEP` | 10 | parallel_orchestrator.py:144 | Est. turns per feature step | NO (hardcoded) |
| C12 | `MIN_FEATURE_TURNS` | 30 | parallel_orchestrator.py:145 | Min turns even for tiny features | NO (hardcoded) |
| C13 | Context budget target | 45% | client.py:348 | Target context usage per session | NO (hardcoded in comments/prompt) |
| C14 | Context hard stop | 48% | client.py:561 | Emergency wrap-up threshold | NO (hardcoded) |

**Self-tuning potential**: HIGH — C1-C7 could absolutely be tuned per project type.
A simple CRUD app doesn't need 150 turns. A complex app might need more.
C10-C12 directly affect batch quality.

---

## Category D: Parallel Orchestration

These control concurrency limits, process caps, retries, and timeouts.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| D1 | `MAX_PARALLEL_AGENTS` | 5 | parallel_orchestrator.py:131 | Max concurrent coding agents | NO (hardcoded) |
| D2 | `MAX_TOTAL_AGENTS` | 10 | parallel_orchestrator.py:132 | Hard limit on total processes | NO (hardcoded) |
| D3 | `DEFAULT_CONCURRENCY` | 3 | parallel_orchestrator.py:133 | Default coding agent concurrency | YES (CLI arg) |
| D4 | `DEFAULT_TESTING_BATCH_SIZE` | 3 | parallel_orchestrator.py:134 | Features per testing batch | YES (CLI arg) |
| D5 | `POLL_INTERVAL` | 5 sec | parallel_orchestrator.py:135 | Seconds between ready-feature checks | NO (hardcoded) |
| D6 | `MAX_FEATURE_RETRIES` | 3 | parallel_orchestrator.py:136 | Max times to retry a failed feature | NO (hardcoded) |
| D7 | `INITIALIZER_TIMEOUT` | 1800 sec (30 min) | parallel_orchestrator.py:137 | Timeout for initializer agent | NO (hardcoded) |
| D8 | `batch_size` | 3 | parallel_orchestrator.py:165 | Max features per coding batch | YES (CLI arg, clamped 1-3) |
| D9 | `review_batch_size` | 5 | parallel_orchestrator.py:167 | Features per review batch | YES (CLI arg, clamped 1-10) |
| D10 | `testing_agent_ratio` | (varies) | parallel_orchestrator.py | Ratio of testing to coding agents | YES (CLI) |

**Self-tuning potential**: MEDIUM — D3, D6, D8 could tune based on observed success rates.
If batch_size=3 leads to lower quality, drop to 2. If retries rarely succeed, stop wasting turns.

---

## Category E: Style Recommendation Engine

These weights control how audience, vibe, and age group affect style recommendations.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| E1 | Audience recommended boost | +3.0 | style_manager.py:110 | How much a "recommended for audience" boosts score | NO (hardcoded) |
| E2 | Audience avoid penalty | -2.0 | style_manager.py:113 | How much "avoid for audience" penalizes | NO (hardcoded) |
| E3 | Vibe boost | +2.0 | style_manager.py:119 | How much matching vibe boosts score | NO (hardcoded) |
| E4 | Age boost | +1.5 | style_manager.py:125 | How much matching age group boosts score | NO (hardcoded) |
| E5 | Age penalize | -1.5 | style_manager.py:128 | How much wrong age group penalizes | NO (hardcoded) |
| E6 | Score cutoff | > 0 | style_manager.py:135 | Only return styles with positive score | NO (hardcoded) |

**Self-tuning potential**: LOW-MEDIUM — these are more design decisions than performance knobs.
But if users consistently override style recommendations, the weights could adjust.

---

## Category F: Playwright / Browser Testing

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| F1 | `PLAYWRIGHT_HEADLESS` | true | client.py:27 | Run browser in headless mode | YES (env var) |
| F2 | `PLAYWRIGHT_BROWSER` | firefox | client.py:32 | Which browser to use | YES (env var) |

**Self-tuning potential**: NONE — these are environment toggles, not performance knobs.

---

## Category G: Outcome Tracking (NEW - just added to config)

These control the self-learning feedback loop itself.

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| G1 | `outcome_tracking.enabled` | true | config.yml:52 | Whether to log outcomes at all | YES (config.yml) |
| G2 | `min_samples_before_suggest` | 5 | config.yml:53 | N outcomes before suggesting changes | YES (config.yml) |
| G3 | `rework_penalty` | 2.0 | config.yml:54 | How much a rework weighs vs success | YES (config.yml) |
| G4 | `suggestion_cooldown_days` | 7 | config.yml:55 | Don't re-suggest same thing within N days | YES (config.yml) |

**Self-tuning potential**: META — these control the tuner itself. Adjust with care.

---

## Category H: Build Quality (config.yml)

| # | Parameter | Default | File:Line | What It Controls | Configurable? |
|---|-----------|---------|-----------|------------------|---------------|
| H1 | `test_after_feature` | true | config.yml:35 | Run tests after each feature built | YES (config.yml) |

**Self-tuning potential**: LOW — this is a yes/no, not a dial.

---

## Category I: Planned but NOT YET BUILT (from blueprints)

These are in the Phase 3/4 blueprints and have no code yet:

| # | Parameter | Planned Default | Blueprint | What It Would Control |
|---|-----------|-----------------|-----------|----------------------|
| I1 | 6 scoring dimensions (weighted) | 0.20/0.20/0.20/0.15/0.10/0.15 | Phase 3 | Replace 4-dim equal-weight scoring |
| I2 | `gap_category` thresholds | clear>20%, close<15%, very_close<5% | Phase 3 | Finer gap classification |
| I3 | Quality Gate score threshold | 2.0 out of 5.0 | Phase 4 | Block build if PRD quality < threshold |
| I4 | Quality Gate dimensions | 6 weighted | Phase 4 | completeness/clarity/consistency/feasibility/testability/scope |
| I5 | Verification agent model | sonnet | Phase 3 | Which model runs N.5 verifiers |
| I6 | Interaction mode | developers_choice | Phase 3 | full_control / developers_choice / review_exceptions |
| I7 | Golden Orange utopia line | (dynamic) | Phase 4 | Where diminishing returns boundary sits |
| I8 | Cross-project learning enabled | false | Future | Aggregate outcomes across all projects |
| I9 | Coverage assessment threshold | ~45% | Phase 2 | "You've described X% of the app" cutoff |

---

## Summary by Adjustability

| Status | Count | Categories |
|--------|-------|------------|
| **Already configurable** (config.yml/CLI/env) | 28 | A1-A8, B1-B11, D3-D4, D8-D10, F1-F2, G1-G4, H1 |
| **Hardcoded — should be configurable** | 22 | C1-C14, D1-D2, D5-D7, E1-E6 |
| **Planned but not built** | 9 | I1-I9 |
| **Total tunables** | **59** | |

---

## The Learning Loop: What Can Be Auto-Tuned?

Based on build outcomes, the self-learning system should analyze and suggest adjustments for:

### Tier 1: Direct Build Quality Signal (tune after every build)
- **A1-A3** — Mechanism thresholds (did auto-picks need rework? were close-calls useful?)
- **A4-A7** — DC bias weights (which bias correlates with good/bad outcomes?)
- **C10-C12** — Turn budgets (did features finish or run out of turns?)
- **D6** — Feature retries (do retries ever succeed? are 3 enough?)
- **D8** — Batch size (does cramming 3 features into one session hurt quality?)

### Tier 2: Cross-Build Pattern Signal (tune after ~5 builds)
- **C1-C7** — Max turns per agent type (which agent types are turn-starved?)
- **D3** — Default concurrency (does more parallelism hurt quality?)
- **B1-B3** — Safety thresholds (are builds crashing before the agent can hand off?)

### Tier 3: Long-Term Preference Signal (tune after ~10+ builds)
- **E1-E5** — Style recommendation weights (do users override style picks?)
- **G2-G4** — Meta-tuning of the learning system itself
- **I1** — 6-dimension scoring weights (once built)

### NOT auto-tunable (human-only toggles)
- B4, B5, B11, F1, F2, G1, H1 — These are on/off or environment-specific choices
