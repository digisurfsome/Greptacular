# SDK Client Pattern — The 3-Bug Fix

> **20+ agents failed to fix this. Read before touching ANY SDK client code.**

## Bug 1: bypassPermissions Crashes the CLI

`permission_mode="bypassPermissions"` causes exit code 3 (Bun runtime crash on Windows).

**Fix:** Use `permission_mode="acceptEdits"` + a settings file:
```json
{"permissions": {"defaultMode": "acceptEdits", "allow": []}}
```

Copy the exact pattern from `workspace_chat_session.py` line ~565 or `client.py`.

## Bug 2: No Logging = Blind Debugging

Every `_call_via_sdk()` MUST have a `_log()` helper that writes to BOTH `logger.info()` AND the `on_progress()` callback. The SDK call takes 120-200 seconds. Without logs streaming to the browser, nobody can diagnose failures.

## Bug 3: rate_limit_event Kills the Response Loop

The SDK throws `"Unknown message type: rate_limit_event"` as an **EXCEPTION**, not a yielded message. This kills the `async for msg in client.receive_response()` loop AFTER the full response has been collected.

**Fix:** Always wrap in try/except and recover:
```python
try:
    async for msg in client.receive_response():
        # ... collect full_text ...
except Exception as exc:
    if full_text.strip() and "unknown message type" in str(exc).lower():
        pass  # Use the text we already have
    elif full_text.strip():
        pass  # Try to use what we have
    else:
        raise  # No text — re-raise
```

## Reference Implementations (WORKING)

- `server/services/yt_processor.py` — `_call_via_sdk()` with full logging + recovery
- `server/services/yt_discovery.py` — Same pattern
- `server/services/workspace_chat_session.py` — Original working SDK client

**If you are about to create a new SDK client, copy `yt_processor.py._call_via_sdk()` — it has every fix.**

Full report: `docs/fix-report-yt-lab-subscription.md`
