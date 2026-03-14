# CLAUDE.md

## What Is This

Mission Control connects Plane (project management) to Claude AI agents.
When an issue is assigned to AI in Plane, this system picks it up, runs Claude, and posts results back.

## Auth: Subscription Only

This project uses subscription auth (force_subscription pattern). No API keys.

- `sdk_wrapper.py` has `get_subscription_env()` which clears `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN`
- The CLI then falls back to `~/.claude/.credentials.json` (subscription OAuth)
- You must have run `claude login` at least once

## SDK Pattern

The SDK wrapper in `sdk_wrapper.py` is the proven pattern. Copy it for any new module that needs to call Claude.

### Rules (learned the hard way in AutoForge):

1. **NEVER use `permission_mode="bypassPermissions"`** -- it crashes the CLI (exit code 3, Bun runtime crash on Windows). ALWAYS use `"acceptEdits"` with a settings file.

2. **ALWAYS wrap `receive_response()` in try/except** -- the SDK throws `"Unknown message type: rate_limit_event"` as an exception AFTER the full response is collected. Without the try/except, you lose the entire response.

3. **ALWAYS log to both logger and on_progress callback** -- SDK calls take 2+ minutes. Without real-time logs, it looks like the app is frozen.

## Key Files

| File | Purpose |
|------|---------|
| `sdk_wrapper.py` | Core SDK wrapper (subscription auth + error recovery) |
| `plane_bridge.py` | FastAPI webhook listener for Plane events (placeholder) |
| `docker-compose.plane.yml` | Plane self-hosted setup (placeholder) |
