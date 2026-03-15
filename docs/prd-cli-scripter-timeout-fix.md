# PRD: Fix CLI Scripter "Run with AI" Timeout

## Problem

The CLI Scripter's "Run with AI" and "Generate All" buttons always time out after 300 seconds with: `Claude CLI timed out after 300s`. This blocks the entire CLI Scripter workflow.

## Root Cause (Confirmed)

**`CLAUDECODE=1` env var leaks into the subprocess and prevents `claude -p` from starting.**

When the server is started from a terminal that has Claude Code env vars set, ALL of them leak into every subprocess. The Claude CLI checks for `CLAUDECODE=1` at startup and blocks (it thinks it's being nested inside another interactive session). The subprocess sits doing nothing for 300 seconds, then gets killed by the timeout.

**Two other places in this codebase already fixed this exact bug:**

1. `server/services/workspace_chat_session.py` line 859:
```python
os.environ.pop("CLAUDECODE", None)
```

2. `.claude/skills/skill-creator/scripts/run_eval.py` lines 80-83:
```python
env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
```

**The CLI Scripter never got this fix.**

### Secondary Issue: Missing `--dangerously-skip-permissions`

Every working build script in the codebase uses `--dangerously-skip-permissions`:
- `scripts/run-api-research-build.sh` — uses it
- `scripts/run-cli-scripter-build.sh` — uses it
- The CLI Scripter's OWN generated bash scripts use it (line 393 of cli_scripter.py)

But `_run_claude_cli()` does NOT include it. Without it, the CLI might prompt for permission with no TTY to answer.

### Tertiary Issue: `CLAUDE_CODE_OAUTH_TOKEN` Leaks

This OAuth token from the parent session leaks through and may conflict with the subscription auth that `get_effective_sdk_env(force_subscription=True)` tries to set up. The `env_constants.py` API_ENV_VARS list does NOT include this var, so it passes through untouched.

## File to Modify

**Only one file:** `server/routers/cli_scripter.py`

**Only one function:** `_run_claude_cli()` starting at line 229

## Exact Changes (4 total)

### Change 1: Clean environment variables (MOST IMPORTANT)

After this line (~line 239):
```python
cli_env = {**os.environ, **sdk_env}
```

ADD these lines:
```python
# Prevent "nested session" detection when the server was launched
# from inside a Claude Code session.  CLAUDECODE=1 causes the child
# `claude` process to refuse to start.
cli_env.pop("CLAUDECODE", None)
cli_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
cli_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
```

### Change 2: Add --dangerously-skip-permissions flag

Change the subprocess command from:
```python
"claude", "-p", "--model", model, "--output-format", "text",
```
To:
```python
"claude", "-p", "--model", model, "--output-format", "text",
"--dangerously-skip-permissions",
```

This is safe because the CLI Scripter only uses `claude -p` for text generation (PRDs, phase splits). No tool calls, no file edits, no bash commands.

### Change 3: Increase default timeout from 300s to 600s

Change:
```python
async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 300) -> str:
```
To:
```python
async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 600) -> str:
```

### Change 4: Add logging

Add `import time` at top of file if not already imported.

Add BEFORE the `proc = await asyncio.create_subprocess_exec(...)` line:
```python
logger.info(
    "_run_claude_cli: Starting claude -p (model=%s, timeout=%ds, prompt_len=%d)",
    model, timeout, len(prompt),
)
start_time = time.time()
```

Add AFTER the `return stdout.decode().strip()` at the end of the function, change it to:
```python
result = stdout.decode().strip()
logger.info(
    "_run_claude_cli: Completed in %.1fs, output_len=%d",
    time.time() - start_time, len(result),
)
return result
```

## Complete Fixed Function (for reference)

```python
async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 600) -> str:
    """Run Claude CLI in print mode using subscription auth. Zero API credits."""
    from registry import get_effective_sdk_env
    sdk_env = get_effective_sdk_env(force_subscription=True)
    cli_env = {**os.environ, **sdk_env}

    # Prevent "nested session" detection when the server was launched
    # from inside a Claude Code session.
    cli_env.pop("CLAUDECODE", None)
    cli_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    cli_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)

    logger.info(
        "_run_claude_cli: Starting claude -p (model=%s, timeout=%ds, prompt_len=%d)",
        model, timeout, len(prompt),
    )
    start_time = time.time()

    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", "--model", model, "--output-format", "text",
        "--dangerously-skip-permissions",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=cli_env,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=504, detail=f"Claude CLI timed out after {timeout}s")

    if proc.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown CLI error"
        logger.error("Claude CLI failed (rc=%d): %s", proc.returncode, error_msg)
        raise HTTPException(status_code=502, detail=f"Claude CLI error: {error_msg}")

    result = stdout.decode().strip()
    logger.info(
        "_run_claude_cli: Completed in %.1fs, output_len=%d",
        time.time() - start_time, len(result),
    )
    return result
```

## Verification

1. Apply changes to `server/routers/cli_scripter.py`
2. Restart server: kill python, run `start_ui.bat` from `C:\Users\lober\Greptacular`
3. Go to `http://localhost:8888/#/cli-scripter`
4. Fill in any app name/description
5. Click "Run with AI" on the PRD Prompt
6. Should complete in 30-120 seconds (not timeout)
7. Check server logs for the new `_run_claude_cli: Starting...` and `_run_claude_cli: Completed...` lines
8. Test "Generate All" too (chains 2 calls)

## Difficulty: 2/10 — One function, one file, four small changes

## Deploy Chain After Fix
1. `cd ui && npm run build` (dev repo — even though this is Python-only, verify nothing breaks)
2. `git push origin main`
3. `cd C:\Users\lober\Greptacular && git pull origin main --no-edit`
4. Kill python, restart `start_ui.bat`
5. Ctrl+Shift+R in browser
