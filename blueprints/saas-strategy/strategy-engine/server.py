"""
FastAPI web server for the SaaS Strategy Engine.
Serves the chat UI and handles strategy session state via REST API.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from engine import StrategyEngine, format_game_plan
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="SaaS Strategy Engine", version="1.0.0")

# In-memory session store (single-user tool — no DB needed)
sessions: dict[str, StrategyEngine] = {}

SESSIONS_DIR = Path(__file__).parent / "saved_sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


class StartRequest(BaseModel):
    session_id: str | None = None


class InputRequest(BaseModel):
    session_id: str
    user_input: str


class SessionResponse(BaseModel):
    session_id: str
    step: str
    step_index: int
    total_steps: int
    message: str
    options: list[str]
    input_type: str
    complete: bool = False
    game_plan_md: str | None = None


# ─── API Routes ─────────────────────────────────────────────────────────────

@app.post("/api/start", response_model=SessionResponse)
def start_session(req: StartRequest):
    """Start a new strategy session."""
    engine = StrategyEngine()
    sid = req.session_id or f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    engine.session.id = sid
    sessions[sid] = engine

    prompt = engine.get_current_prompt()
    return SessionResponse(
        session_id=sid,
        step=engine.session.current_step.value,
        step_index=engine.session.step_index,
        total_steps=10,
        message=prompt["message"],
        options=prompt.get("options", []),
        input_type=prompt.get("input_type", "freeform"),
    )


@app.post("/api/input", response_model=SessionResponse)
def process_input(req: InputRequest):
    """Process user input and advance the engine."""
    engine = sessions.get(req.session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    result = engine.process_input(req.user_input)
    is_complete = result.get("complete", False)

    game_plan_md = None
    if is_complete and engine.session.game_plan:
        game_plan_md = format_game_plan(engine.session)
        # Auto-save completed sessions
        save_path = SESSIONS_DIR / f"{req.session_id}.json"
        engine.save_session(str(save_path))
        plan_path = SESSIONS_DIR / f"{req.session_id}_game_plan.md"
        plan_path.write_text(game_plan_md)

    return SessionResponse(
        session_id=req.session_id,
        step=engine.session.current_step.value,
        step_index=engine.session.step_index,
        total_steps=10,
        message=result["message"],
        options=result.get("options", []),
        input_type=result.get("input_type", "freeform"),
        complete=is_complete,
        game_plan_md=game_plan_md,
    )


@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    """Get current session state."""
    engine = sessions.get(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    prompt = engine.get_current_prompt()
    return SessionResponse(
        session_id=session_id,
        step=engine.session.current_step.value,
        step_index=engine.session.step_index,
        total_steps=10,
        message=prompt["message"],
        options=prompt.get("options", []),
        input_type=prompt.get("input_type", "freeform"),
        complete=engine.session.completed,
        game_plan_md=format_game_plan(engine.session) if engine.session.completed else None,
    )


@app.get("/api/sessions")
def list_sessions():
    """List all saved sessions."""
    saved = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            saved.append({
                "id": data.get("id", f.stem),
                "created_at": data.get("created_at", ""),
                "completed": data.get("completed", False),
                "step": data.get("current_step", ""),
            })
        except Exception:
            pass
    return {"sessions": saved}


# ─── Serve the frontend ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the single-page app."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>SaaS Strategy Engine</h1><p>Build the static/index.html frontend.</p>")


# Mount static files last
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
