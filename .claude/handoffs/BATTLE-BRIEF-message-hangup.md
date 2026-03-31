# BATTLE BRIEF: WebSocket Message Hang-Up Bug

## THE PROBLEM — PLAIN ENGLISH

When the AI agent responds to the user in the Workspace chat, the response text gets STUCK. The user sees nothing. Then when the user sends ANOTHER message, all the stuck responses flood in at once. This makes the chat unusable.

**This bug has survived 8 fix attempts by different agents.** Every single one diagnosed it as "sync DB calls blocking the async event loop" and wrapped them in `asyncio.to_thread()`. The bug persists. That theory is either incomplete or wrong.

## EXACT SYMPTOMS

1. User sends a message in the Workspace chat
2. Agent starts processing (user sees "Waiting for Opus response...")
3. Agent generates a full response
4. Response does NOT appear in the user's browser
5. User sends another message (or walkie-talkie)
6. Immediately, all stuck responses flood in at once
7. This happens EVERY TIME, not intermittently

## WHAT HAS BEEN TRIED (ALL FAILED)

1. Wrapped `add_message()` in `asyncio.to_thread()` — still hangs
2. Wrapped `estimate_tokens()` in `asyncio.to_thread()` — still hangs
3. Wrapped `get_message_count()` in `asyncio.to_thread()` — still hangs
4. Wrapped `get_conversation_token_total()` in `asyncio.to_thread()` — still hangs
5. Wrapped `log_premium_usage()` in `asyncio.to_thread()` — still hangs
6. Wrapped all 4 `add_token_log_entry()` calls in `asyncio.to_thread()` — still hangs
7. Added `await asyncio.sleep(0)` after `websocket.send_json()` — just committed, untested
8. Multiple agents over weeks have applied the same "sync DB blocking" theory — none fixed it

## THE ARCHITECTURE (READ THIS CAREFULLY)

### Server Side (Python/FastAPI/Uvicorn on Windows)

**File: `server/routers/workspace.py`** — The WebSocket endpoint

The main WebSocket handler has TWO concurrent things running:
- **Main loop**: sits at `await websocket.receive_text()` waiting for user input
- **Background task**: `asyncio.create_task(_stream_to_ws(gen))` streams response chunks

```python
# Main loop (line ~1247):
while True:
    data = await websocket.receive_text()  # BLOCKS here waiting for user
    # ... process message, create background task ...

# Background task (line ~1216):
async def _stream_to_ws(gen):
    async for chunk in gen:
        await websocket.send_json(chunk)
        await asyncio.sleep(0)  # flush attempt (just added)
```

**File: `server/services/workspace_chat_session.py`** — The session logic

- `send_message()` is an async generator that yields dict chunks
- It calls `_query_claude()` which is also an async generator
- `_query_claude()` wraps the Claude SDK's subprocess-based streaming
- Between SDK messages, it does DB logging (ALL now wrapped in `asyncio.to_thread()`)
- At the end, it yields `token_usage` and the parent yields `response_done`

### Client Side (React 19 / TypeScript)

**File: `ui/src/hooks/useWorkspaceChat.ts`** — The WebSocket hook

- Standard `new WebSocket(url)` connection
- `ws.onmessage` handler parses JSON, calls `setMessages()` to update React state
- 30-second ping interval keeps connection alive
- `connectionGenerationRef` guards against stale connections (line 310)

**File: `ui/src/components/workspace/WorkspaceChat.tsx`** — ~2000 line chat component

## THEORIES TO INVESTIGATE (BE CREATIVE — DO NOT JUST REDO THE DB FIX)

### Theory A: TCP Nagle's Algorithm on Windows
Uvicorn on Windows may not set `TCP_NODELAY` on the WebSocket socket. Nagle's algorithm coalesces small TCP packets, waiting up to 200ms for more data. If the response finishes and no more data comes, the last frame(s) sit in the kernel buffer until the next incoming packet (user's message) triggers a flush.

**How to test:** Find where uvicorn creates the socket and check/set `TCP_NODELAY`. Or add timestamps to server sends and client receives to measure the gap.

**How to fix:** Set `socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)` on the server socket. Or find uvicorn's socket creation and patch it.

### Theory B: ASGI Transport Buffering in Uvicorn
Starlette's `websocket.send_json()` writes to an internal ASGI transport buffer. The actual network send happens when the event loop cycles back to the transport's write callback. If something prevents that cycle (even briefly), frames buffer up.

**How to test:** Add `print(f"SEND {chunk['type']} at {time.time()}")` right after `send_json` and `console.log('RECV', data.type, Date.now())` in the browser's onmessage. Compare timestamps.

**How to fix:** Try `await asyncio.sleep(0.01)` (not just 0) after sends. The non-zero sleep might give uvicorn's transport time to process. Or try `websocket.send_text(json.dumps(chunk))` instead of `send_json` (might have different buffering). Or try a different ASGI server (hypercorn).

### Theory C: Claude SDK Subprocess Blocking the Event Loop
The Claude SDK spawns `claude` as a subprocess. Reading from its stdout pipe via `client.receive_response()` might have synchronous internals that block the entire event loop thread. Even if DB calls are async, the SDK iteration itself might block.

**How to test:** Wrap timing around individual iterations: `t0 = time.time(); async for msg in ...: elapsed = time.time() - t0; if elapsed > 0.1: logger.warning(f"SDK iteration took {elapsed}s")`

**How to fix:** Run the entire SDK interaction in a separate thread, communicating results via a queue. Or use `loop.run_in_executor()` for the blocking parts.

### Theory D: React State Batching / Rendering Deadlock
React 19 batches ALL state updates by default. The `onmessage` handler calls `setMessages()` multiple times rapidly. React batches them and commits later. But if the component is expensive to render (~2000 lines), React's scheduler might defer the commit until user interaction (like typing) forces a flush.

**How to test:** Add `console.log('WS RECEIVED:', data.type, Date.now())` at the VERY TOP of the `onmessage` handler (line 309 of useWorkspaceChat.ts), before any state updates. If these logs appear in the browser console while the UI shows nothing, it's a React rendering issue. If they DON'T appear, messages aren't arriving at the browser.

**How to fix:** Use `flushSync` from `react-dom` for the `response_done` message handler. Or use `requestAnimationFrame` to force a paint after critical state updates.

### Theory E: `connectionGenerationRef` Silently Dropping Messages
Line 310 of useWorkspaceChat.ts:
```javascript
if (connectionGenerationRef.current !== thisGeneration) return;
```
If the WebSocket reconnected (bumping the generation), ALL messages from the old connection are SILENTLY dropped — no error, no log, nothing. The old connection might still be receiving buffered data.

**How to test:** Add logging: `console.log('GEN CHECK:', connectionGenerationRef.current, thisGeneration)` before the guard. If they ever differ, this is the bug.

**How to fix:** Explicitly close old WebSocket connections. Don't rely on generation guards — they silently eat messages.

### Theory F: Windows ProactorEventLoop Issues
Windows Python uses `ProactorEventLoop` by default, which has known quirks with async I/O, especially pipe reading (which the Claude SDK uses for subprocess communication). This could cause the SDK streaming to block.

**How to test:** Check: `import asyncio; print(type(asyncio.get_event_loop_policy()))`. If ProactorEventLoop, try switching.

**How to fix:** Add before uvicorn starts: `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`. Or pass `--loop asyncio` to uvicorn.

### Theory G: The Response Task Finishes But WebSocket Frames Are Still Buffered
The `_stream_to_ws` task completes (all chunks yielded and send_json called), but the actual TCP frames haven't been flushed to the network. The task is done, nothing triggers a flush, frames sit in buffer until user's next message.

**How to test:** After `_stream_to_ws` completes, send a ping from the server. If the ping arrives but the response chunks don't, it's a buffering issue.

**How to fix:** At the end of `_stream_to_ws`, send a dummy ping/flush frame. Or keep the task alive briefly: `await asyncio.sleep(0.5)` at the end to let the transport drain.

## KEY FILES

| File | Lines | What's There |
|------|-------|-------------|
| `server/routers/workspace.py` | 1216-1245 | `_stream_to_ws()` — the streaming function |
| `server/routers/workspace.py` | 1246-1450 | Main WebSocket loop |
| `server/services/workspace_chat_session.py` | 1480-1600 | `send_message()` async generator |
| `server/services/workspace_chat_session.py` | 1723-2170 | `_query_claude()` SDK streaming |
| `ui/src/hooks/useWorkspaceChat.ts` | 206-550 | Client WebSocket handler |
| `ui/src/components/workspace/WorkspaceChat.tsx` | entire file | Chat component |
| `start_ui.bat` | — | How uvicorn is launched (check flags) |

## INSTRUCTIONS

1. **DO NOT just wrap more DB calls in asyncio.to_thread().** That has been done 8 times. It doesn't work.
2. **START by adding diagnostic logging with timestamps** on both server sends AND client receives. Figure out WHERE the message gets stuck BEFORE writing any fix.
3. **Think creatively.** The obvious answer has failed 8 times. Consider TCP, OS-level, ASGI transport, React rendering, race conditions, event loop policy.
4. **Test your theory before implementing.** Diagnostics first, then fix.
5. **The fix MUST work on Windows 11** with Python 3.11+ and uvicorn.
6. **Leave the diagnostic logging in place** (behind a flag or at debug level) so we can verify it worked.
7. **After fixing, also check `start_ui.bat`** to see how uvicorn is started — there may be flags or configuration that matters.

## HOW TO VERIFY

1. Start a new Workspace chat
2. Send a message to the agent
3. The response should appear IMMEDIATELY — not after sending another message
4. Do 3-4 back-and-forth exchanges. Every response must appear on its own.
5. Check browser console for `[WS]` logs showing message arrival timing
