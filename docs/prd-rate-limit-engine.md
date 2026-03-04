# PRD: Rate Limit Intelligence Engine

**Status:** Draft
**Date:** 2026-03-04
**Author:** Owner + Claude (Session 6)
**Depends on:** Factory Task Queue PRD

---

## Problem Statement

The Claude Pro/Max plan has rate limits — hit the ceiling and you're locked out for up to 5 hours. Right now this is handled reactively: hit the wall, wait, retry. There's no visibility into where you are relative to the limit, no way to pace usage, and no way to separate "daytime work" (owner needs the agent) from "nighttime automation" (factory can run full speed).

The owner has two goals:
1. **Never get locked out during work hours** — pace factory usage so there's always capacity for interactive work
2. **Max out nighttime hours** — factory runs full speed 10pm-10am, hitting limits is fine (just wait and resume)

## What We Can Track (Already Available)

| Data Point | Source | Status |
|---|---|---|
| Rate limit hit timestamp | agent.py logs + factory controller | Already captured, not persisted |
| Retry-after duration | HTTP 429 response headers | Parsed by rate_limit_utils.py |
| Tokens per session (in/out) | Claude Agent SDK response | Available but not tracked |
| Session duration | Factory controller history | Already in handoff_history |
| Time between rate limit hits | Derivable from timestamps | Need to persist events |

## What Anthropic Tells Us

Anthropic's developer console shows:
- Daily usage (tokens consumed today)
- Weekly rolling usage
- Monthly allocation
- Real-time capacity remaining

Their rate limits are based on:
- **Tokens per minute (TPM)** — burst limit
- **Messages per day** — daily cap
- **Rolling window** — usage decays over time (not a hard reset at midnight)

We can't query their API for current usage (no endpoint for that), BUT we can reconstruct it from our own tracking.

## Architecture

### 1. Rate Limit Event Log

Persistent log of every rate limit event:

```python
# ~/.autoforge/rate_limit_log.json (or SQLite)
{
  "events": [
    {
      "timestamp": "2026-03-04T02:15:00Z",
      "type": "rate_limit_hit",
      "tokens_used_session": 45000,
      "tokens_used_cumulative": 180000,  # since last reset
      "retry_after_seconds": 300,
      "session_duration_minutes": 12,
      "project": "my-app",
      "model": "claude-opus-4-6"
    },
    {
      "timestamp": "2026-03-04T02:20:00Z",
      "type": "rate_limit_cleared",
      "cooldown_actual_seconds": 300
    }
  ],
  "daily_stats": {
    "2026-03-04": {
      "tokens_input": 250000,
      "tokens_output": 80000,
      "sessions": 8,
      "rate_limit_hits": 2,
      "total_cooldown_minutes": 15
    }
  }
}
```

### 2. Token Usage Tracker

Track cumulative token usage across all sessions:

```python
class TokenTracker:
    """Tracks token consumption for rate limit prediction."""

    def record_session(self, input_tokens, output_tokens, duration_seconds):
        """Record a completed session's token usage."""

    def get_burn_rate(self, window_minutes=60) -> float:
        """Tokens per minute over recent window."""

    def get_remaining_estimate(self) -> dict:
        """Estimate remaining capacity before hitting limit."""
        # Based on historical limit thresholds
        return {
            "estimated_tokens_remaining": 150000,
            "estimated_minutes_remaining": 45,
            "confidence": 0.7,  # improves with more data points
        }

    def predict_limit_hit(self, planned_sessions=1) -> datetime | None:
        """Predict when we'll hit the rate limit if we keep going."""
```

### 3. Calibration System

The system learns from every rate limit event:

```
After 0 events:  No prediction (runs freely)
After 1 event:   Rough estimate (±50%)
After 3 events:  Decent estimate (±25%)
After 10 events: Accurate estimate (±10%)
After 20 events: Highly calibrated (±5%)
```

**Auto-calibration (no button needed):**
- When the factory hits a rate limit → log timestamp, tokens used, cooldown duration
- When the factory recovers from rate limit → log actual recovery time
- Over time, the system builds a model: "With opus on Pro plan, I can use ~X tokens per hour before hitting the limit"
- Each rate limit event refines the model

**The key insight:** We don't need to know Anthropic's exact formula. We just need to observe our own usage patterns. If we consistently hit the limit after ~200K tokens in 30 minutes, that's our effective limit. The model self-corrects with every event.

### 4. Throttle Controller

```python
class ThrottleController:
    """Controls factory pacing based on rate limit predictions."""

    def __init__(self, schedule: Schedule, tracker: TokenTracker):
        self.schedule = schedule
        self.tracker = tracker

    def should_start_next_session(self) -> tuple[bool, str]:
        """Decide whether to start another agent session."""

        estimate = self.tracker.get_remaining_estimate()
        current_hour = datetime.now().hour

        # Nighttime (10pm-10am): full speed, just handle limits reactively
        if self.schedule.is_nighttime(current_hour):
            return True, "nighttime — full speed"

        # Daytime: pace to preserve capacity for interactive use
        if estimate["estimated_minutes_remaining"] < 30:
            return False, f"daytime — only ~{estimate['estimated_minutes_remaining']}min capacity left, preserving for interactive use"

        # Daytime with good capacity: proceed but at moderate pace
        if estimate["estimated_minutes_remaining"] < 60:
            # Add delay between sessions to slow burn rate
            return True, "daytime — proceeding with pacing delay"

        return True, "daytime — plenty of capacity"

    def get_pacing_delay(self) -> int:
        """Extra delay between sessions during daytime to conserve capacity."""
        estimate = self.tracker.get_remaining_estimate()
        if estimate["estimated_minutes_remaining"] < 60:
            return 120  # 2 min delay between sessions
        return 0
```

### 5. Schedule Configuration

```python
# User-configurable schedule
{
    "nighttime_start": "22:00",  # 10 PM
    "nighttime_end": "10:00",    # 10 AM
    "nighttime_mode": "full_speed",  # no throttling, handle limits reactively
    "daytime_mode": "preserve",      # pace to keep capacity for interactive use
    "daytime_reserve_minutes": 30,   # always keep 30 min capacity in reserve
    "weekend_mode": "full_speed",    # weekends = factory time
    "timezone": "America/Chicago",   # user's timezone
}
```

### 6. Dashboard Widget

Small widget in the Workspace header or Factory panel:

```
┌──────────────────────────────────┐
│ ⚡ API Budget  ███████░░░  72%   │
│ ~45 min remaining · 3 hits today │
│ Mode: Daytime (preserving)       │
└──────────────────────────────────┘
```

Shows:
- Estimated capacity remaining (bar + percentage)
- Minutes of agent time remaining before predicted limit
- Rate limit hits today
- Current mode (nighttime full speed / daytime preserving)

## How It Integrates with Task Queue

The Queue Executor checks the Throttle Controller before starting each task:

```
Queue Executor loop:
1. Pull next task from queue
2. Ask ThrottleController: should_start_next_session()?
3. If NO → wait, check again in 5 minutes
4. If YES → start factory for this task
5. Between sessions within a task → add pacing_delay if daytime
6. On rate limit hit → log event, update tracker, wait for cooldown
7. On task complete → pull next task, go to step 2
```

## Data We Need to Start Collecting NOW

Even before building the full engine, we should start logging:

1. **Every rate limit event** — timestamp, tokens used, model, retry-after
2. **Every session completion** — tokens in, tokens out, duration, model
3. **Rate limit recovery** — when the cooldown actually ends

This data is the training set for the prediction engine. The more we have, the more accurate predictions become. We can start logging immediately (just append to a JSON file) and build the prediction logic later.

## Implementation Phases

### Phase 1: Event Logging (can do now)
- Add rate limit event logging to factory controller
- Log session token usage on completion
- Store in `~/.autoforge/rate_limit_log.json`
- No UI changes needed

### Phase 2: Tracker + Basic Prediction
- TokenTracker class that reads the log
- Simple prediction: "at current burn rate, ~X minutes until limit"
- Dashboard widget showing estimated capacity

### Phase 3: Throttle Controller
- Schedule configuration (night/day modes)
- ThrottleController integrates with Queue Executor
- Pacing delays during daytime
- Reserve capacity setting

### Phase 4: Calibration + Accuracy
- Auto-calibration from accumulated data
- Confidence scoring (how accurate are predictions?)
- Multi-model tracking (opus vs sonnet have different limits)
- Historical view: "last 7 days usage pattern"

### Phase 5: Partner Account Integration
- If primary account is depleted, route tasks to secondary API key
- Load balancing across accounts
- Per-account tracking and limits

## Quick Win: Start Logging Now

The single most valuable thing we can do right now is start persisting rate limit events. Every hit we log makes the future prediction engine more accurate. This is maybe 20 lines of code in the factory controller.

```python
def _log_rate_limit_event(self, event_type: str, tokens_used: int = 0, retry_after: int = 0):
    """Append a rate limit event to the persistent log."""
    log_path = Path.home() / ".autoforge" / "rate_limit_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    events = []
    if log_path.exists():
        events = json.loads(log_path.read_text()).get("events", [])

    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "tokens_used": tokens_used,
        "retry_after_seconds": retry_after,
        "project": self.project_name,
        "model": self.state.model,
    })

    # Keep last 1000 events
    events = events[-1000:]
    log_path.write_text(json.dumps({"events": events}, indent=2))
```
