"""
CLI Dashboard Server - Zero SDK, Pure Claude Code CLI

A lightweight server that:
1. Receives hook events from Claude Code CLI
2. Manages Claude Code processes (start/stop/pause/resume)
3. Serves a real-time dashboard via WebSocket
4. Tracks token usage and session history

This is NOT a third-party SDK client. It's a process manager
and event viewer for the official Claude Code CLI.
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="CLI Dashboard")

# ─── State ───────────────────────────────────────────────────────────

sessions: dict[str, dict] = {}  # session_id -> session info
active_connections: list[WebSocket] = []
event_log: list[dict] = []  # All hook events
MAX_EVENTS = 5000

# ─── Models ──────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    project_dir: str
    prompt: str = ""
    session_name: str = ""
    model: str = "sonnet"


class HookEvent(BaseModel):
    event_type: str  # tool_use, message, notification, session_end
    session_id: str = ""
    tool_name: str = ""
    message: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    timestamp: str = ""
    raw: dict = {}


# ─── WebSocket Hub ───────────────────────────────────────────────────

async def broadcast(data: dict):
    """Send event to all connected dashboard clients."""
    message = json.dumps(data)
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    # Send current state on connect
    await ws.send_text(json.dumps({
        "type": "init",
        "sessions": {sid: _session_summary(s) for sid, s in sessions.items()},
        "recent_events": event_log[-100:]
    }))
    try:
        while True:
            # Keep alive, receive commands from dashboard
            data = await ws.receive_text()
            msg = json.loads(data)
            await handle_ws_command(msg)
    except WebSocketDisconnect:
        active_connections.remove(ws)


async def handle_ws_command(msg: dict):
    """Handle commands from the dashboard UI."""
    cmd = msg.get("command")
    if cmd == "start":
        await start_session(StartSessionRequest(**msg.get("params", {})))
    elif cmd == "stop":
        await stop_session(msg.get("session_id", ""))
    elif cmd == "pause":
        await pause_session(msg.get("session_id", ""))
    elif cmd == "resume":
        await resume_session(msg.get("session_id", ""))
    elif cmd == "send_message":
        await send_to_session(msg.get("session_id", ""), msg.get("text", ""))


# ─── Hook Endpoint (CLI posts here) ─────────────────────────────────

@app.post("/hook")
async def receive_hook(event: HookEvent):
    """Receive events from Claude Code CLI hooks."""
    evt = event.model_dump()
    evt["received_at"] = datetime.now().isoformat()

    # Store event
    event_log.append(evt)
    if len(event_log) > MAX_EVENTS:
        event_log.pop(0)

    # Update session token counts
    sid = event.session_id
    if sid and sid in sessions:
        sessions[sid]["tokens_in"] += event.tokens_in
        sessions[sid]["tokens_out"] += event.tokens_out
        sessions[sid]["last_event"] = evt
        sessions[sid]["event_count"] += 1

        if event.event_type == "message" and event.message:
            sessions[sid]["messages"].append({
                "role": "assistant",
                "content": event.message[:2000],  # Truncate for dashboard
                "timestamp": evt["received_at"]
            })

        if event.event_type == "tool_use":
            sessions[sid]["tool_calls"].append({
                "tool": event.tool_name,
                "timestamp": evt["received_at"]
            })

    # Broadcast to all dashboard clients
    await broadcast({"type": "hook_event", "event": evt})
    return {"status": "ok"}


# ─── Session Lifecycle ───────────────────────────────────────────────

@app.post("/api/sessions/start")
async def start_session(req: StartSessionRequest):
    """Launch a new Claude Code CLI session."""
    session_id = str(uuid.uuid4())[:8]
    name = req.session_name or f"session-{session_id}"

    # Build claude command
    # -p "prompt" = print mode (non-interactive, single prompt, exits when done)
    # --output-format stream-json = structured JSON streaming output
    # --model = which model to use
    # --verbose = extra logging
    # On Windows, use shell=True or find claude.cmd
    claude_cmd = "claude"
    if sys.platform == "win32":
        # Try claude.cmd first (npm global install)
        import shutil
        claude_path = shutil.which("claude") or shutil.which("claude.cmd")
        if claude_path:
            claude_cmd = claude_path

    cmd = [claude_cmd]

    if req.model:
        cmd.extend(["--model", req.model])

    # Output format for structured parsing
    # stream-json requires --verbose when used with -p (print mode)
    cmd.extend(["--output-format", "stream-json", "--verbose"])

    # -p must come last with the prompt as its value
    if req.prompt:
        cmd.extend(["-p", req.prompt])

    # Set hook env vars so CLI knows where to POST
    env = os.environ.copy()
    env["CLI_DASHBOARD_SESSION_ID"] = session_id
    env["CLI_DASHBOARD_URL"] = "http://localhost:9111"

    # Use project directory as the working directory
    cwd = req.project_dir if req.project_dir else None

    cmd_str = " ".join(cmd)
    log_msg = f"[{session_id}] Launching: {cmd_str}"
    if cwd:
        log_msg += f"\n[{session_id}] Working dir: {cwd}"
    print(log_msg)

    # Launch the process
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            bufsize=1,
        )
    except FileNotFoundError:
        error_msg = "ERROR: 'claude' command not found. Is Claude Code CLI installed and on PATH?"
        print(f"[{session_id}] {error_msg}")
        await broadcast({
            "type": "log",
            "session_id": session_id,
            "text": error_msg,
            "level": "error"
        })
        return {"error": error_msg}
    except OSError as e:
        error_msg = f"ERROR launching process: {e}"
        print(f"[{session_id}] {error_msg}")
        await broadcast({
            "type": "log",
            "session_id": session_id,
            "text": error_msg,
            "level": "error"
        })
        return {"error": error_msg}

    sessions[session_id] = {
        "id": session_id,
        "name": name,
        "project_dir": req.project_dir,
        "prompt": req.prompt,
        "model": req.model,
        "cmd": cmd_str,
        "cwd": cwd,
        "pid": process.pid,
        "process": process,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "tokens_in": 0,
        "tokens_out": 0,
        "messages": [{"role": "user", "content": req.prompt, "timestamp": datetime.now().isoformat()}],
        "tool_calls": [],
        "logs": [f"CMD: {cmd_str}", f"PID: {process.pid}"],
        "event_count": 0,
        "last_event": None,
    }

    # Start async readers for stdout AND stderr
    asyncio.create_task(_read_process_output(session_id, process))
    asyncio.create_task(_read_process_stderr(session_id, process))

    await broadcast({
        "type": "session_started",
        "session": _session_summary(sessions[session_id])
    })

    return {"session_id": session_id, "pid": process.pid, "status": "running"}


async def _add_log(session_id: str, text: str, level: str = "info"):
    """Add a log entry and broadcast it."""
    if session_id in sessions:
        sessions[session_id]["logs"].append(text)
        # Keep max 500 log lines
        if len(sessions[session_id]["logs"]) > 500:
            sessions[session_id]["logs"] = sessions[session_id]["logs"][-500:]
    print(f"[{session_id}] {text}")
    await broadcast({
        "type": "log",
        "session_id": session_id,
        "text": text,
        "level": level,
        "timestamp": datetime.now().isoformat()
    })


async def _read_process_output(session_id: str, process):
    """Read Claude Code's stream-json output and broadcast."""
    loop = asyncio.get_event_loop()
    await _add_log(session_id, "stdout reader started")
    try:
        while True:
            line = await loop.run_in_executor(None, process.stdout.readline)
            if not line:
                break
            try:
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue

                await _add_log(session_id, f"OUT: {text[:200]}")

                # Try to parse as JSON (stream-json format)
                try:
                    data = json.loads(text)
                    msg_type = data.get("type", "")

                    # Extract useful info from stream-json events
                    if msg_type == "assistant" and "message" in data:
                        content = ""
                        for block in data["message"].get("content", []):
                            if block.get("type") == "text":
                                content += block.get("text", "")
                        if content and session_id in sessions:
                            sessions[session_id]["messages"].append({
                                "role": "assistant",
                                "content": content[:2000],
                                "timestamp": datetime.now().isoformat()
                            })

                    # Token usage
                    usage = data.get("message", {}).get("usage", {})
                    if usage and session_id in sessions:
                        sessions[session_id]["tokens_in"] += usage.get("input_tokens", 0)
                        sessions[session_id]["tokens_out"] += usage.get("output_tokens", 0)

                    await broadcast({
                        "type": "stream",
                        "session_id": session_id,
                        "data": data
                    })
                except json.JSONDecodeError:
                    # Raw text output — still show it as a message
                    if session_id in sessions:
                        sessions[session_id]["messages"].append({
                            "role": "assistant",
                            "content": text[:2000],
                            "timestamp": datetime.now().isoformat()
                        })
                    await broadcast({
                        "type": "output",
                        "session_id": session_id,
                        "text": text
                    })
            except Exception as e:
                await _add_log(session_id, f"ERROR reading stdout: {e}", "error")
    finally:
        # Wait for process to finish and get exit code
        exit_code = process.wait()
        await _add_log(session_id, f"Process exited with code: {exit_code}",
                       "error" if exit_code != 0 else "info")

        if session_id in sessions:
            sessions[session_id]["status"] = "completed" if exit_code == 0 else "error"
            sessions[session_id]["exit_code"] = exit_code
            sessions[session_id]["ended_at"] = datetime.now().isoformat()

            # If process failed with no messages, add the exit info as a message
            msgs = sessions[session_id]["messages"]
            if len(msgs) <= 1:  # Only the user prompt
                sessions[session_id]["messages"].append({
                    "role": "system",
                    "content": f"Process exited with code {exit_code}. Check the log panel for details.",
                    "timestamp": datetime.now().isoformat()
                })

        await broadcast({
            "type": "session_ended",
            "session_id": session_id
        })


async def _read_process_stderr(session_id: str, process):
    """Read stderr from the CLI process and broadcast as logs."""
    loop = asyncio.get_event_loop()
    try:
        while True:
            line = await loop.run_in_executor(None, process.stderr.readline)
            if not line:
                break
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                await _add_log(session_id, f"ERR: {text}", "error")
                # Also add errors as system messages so they show in chat
                if session_id in sessions:
                    sessions[session_id]["messages"].append({
                        "role": "system",
                        "content": text,
                        "timestamp": datetime.now().isoformat()
                    })
                await broadcast({
                    "type": "output",
                    "session_id": session_id,
                    "text": text
                })
    except Exception as e:
        await _add_log(session_id, f"ERROR reading stderr: {e}", "error")


@app.post("/api/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop a running session."""
    if session_id not in sessions:
        return {"error": "not found"}
    s = sessions[session_id]
    if s.get("process"):
        s["process"].terminate()
    s["status"] = "stopped"
    await broadcast({"type": "session_stopped", "session_id": session_id})
    return {"status": "stopped"}


@app.post("/api/sessions/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause (SIGSTOP) a running session."""
    if session_id not in sessions:
        return {"error": "not found"}
    s = sessions[session_id]
    pid = s.get("pid")
    if pid and sys.platform != "win32":
        os.kill(pid, signal.SIGSTOP)
        s["status"] = "paused"
    elif pid:
        # Windows: use subprocess to suspend
        subprocess.run(["powershell", "-Command",
                       f"(Get-Process -Id {pid}).Suspend()"], capture_output=True)
        s["status"] = "paused"
    await broadcast({"type": "session_paused", "session_id": session_id})
    return {"status": "paused"}


@app.post("/api/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume (SIGCONT) a paused session."""
    if session_id not in sessions:
        return {"error": "not found"}
    s = sessions[session_id]
    pid = s.get("pid")
    if pid and sys.platform != "win32":
        os.kill(pid, signal.SIGCONT)
        s["status"] = "running"
    elif pid:
        subprocess.run(["powershell", "-Command",
                       f"(Get-Process -Id {pid}).Resume()"], capture_output=True)
        s["status"] = "running"
    await broadcast({"type": "session_resumed", "session_id": session_id})
    return {"status": "running"}


async def send_to_session(session_id: str, text: str):
    """Send input to a running CLI session's stdin."""
    if session_id not in sessions:
        return
    s = sessions[session_id]
    proc = s.get("process")
    if proc and proc.stdin:
        proc.stdin.write(f"{text}\n".encode())
        proc.stdin.flush()
        s["messages"].append({
            "role": "user",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        await broadcast({
            "type": "user_message",
            "session_id": session_id,
            "text": text
        })


# ─── REST API ────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions():
    return {sid: _session_summary(s) for sid, s in sessions.items()}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        return {"error": "not found"}
    return _session_summary(sessions[session_id])


@app.get("/api/events")
async def get_events(limit: int = 100):
    return event_log[-limit:]


def _session_summary(s: dict) -> dict:
    """Return session info without the process object."""
    return {
        k: v for k, v in s.items()
        if k != "process"
    }


# ─── Static Files & Dashboard ────────────────────────────────────────

@app.get("/")
async def serve_dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


# ─── Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", "9111"))
    print(f"\n  CLI Dashboard running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
