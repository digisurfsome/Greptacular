"""
FastAPI Main Application
========================

Main entry point for the Autonomous Coding UI server.
Provides REST API, WebSocket, and static file serving.
"""

import asyncio
import logging
import os
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Fix for Windows subprocess support in asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import (
    actions_router,
    agent_os_router,
    agent_router,
    approvals_router,
    assistant_chat_router,
    boilerplate_router,
    captures_router,
    checkpoints_router,
    ci_status_router,
    cli_scripter_router,
    commits_router,
    design_guide_router,
    devserver_router,
    dunkstack_router,
    execution_router,
    execution_websocket,
    expand_project_router,
    factory_presets_router,
    factory_router,
    features_router,
    filesystem_router,
    github_router,
    notifications_router,
    projects_router,
    role_library_router,
    schedules_router,
    seo_tools_router,
    settings_router,
    spec_creation_router,
    styles_router,
    swarm_router,
    terminal_router,
    tool_factory_router,
    tool_themes_router,
    verifications_router,
    workspace_router,
    yt_batch_router,
    yt_ingestion_router,
    yt_processing_router,
)
from .schemas import SetupStatus
from .services.agent_os_session import cleanup_all_agent_os_sessions
from .services.assistant_chat_session import cleanup_all_sessions as cleanup_assistant_sessions
from .services.background_session_manager import cleanup_background_sessions
from .services.chat_constants import ROOT_DIR
from .services.ci_monitor import cleanup_all_monitors
from .services.computer_use_agent import cleanup_all_sessions
from .services.design_guide_session import cleanup_all_design_guide_sessions
from .services.dev_server_manager import (
    cleanup_all_devservers,
    cleanup_orphaned_devserver_locks,
)
from .services.expand_chat_session import cleanup_all_expand_sessions
from .services.process_manager import cleanup_all_managers, cleanup_orphaned_locks
from .services.scheduler_service import cleanup_scheduler, get_scheduler
from .services.screen_recorder import cleanup_all_capture_managers
from .services.swarm_orchestrator import cleanup_all_swarms
from .services.terminal_manager import cleanup_all_terminals
from .services.workspace_chat_session import cleanup_all_workspace_sessions
from .websocket import project_websocket

# Paths
UI_DIST_DIR = ROOT_DIR / "ui" / "dist"

# Module logger (used before the app logger is set up)
_startup_logger = logging.getLogger(__name__)


async def _recover_factory_sessions() -> None:
    """Recover factory sessions that were running before server restart.

    Scans registered projects for factory_state.json with status 'running'
    or 'waiting_rate_limit' and resumes them appropriately.
    """
    try:
        sys.path.insert(0, str(ROOT_DIR))
        from registry import list_registered_projects

        projects = list_registered_projects()
        for project_name, project_info in projects.items():
            project_dir = Path(project_info["path"])
            state_path = project_dir / ".autoforge" / "factory_state.json"
            if not state_path.exists():
                continue

            try:
                import json
                data = json.loads(state_path.read_text(encoding="utf-8"))
                status = data.get("status", "idle")

                if status == "running":
                    # Factory was running — agent likely crashed with server
                    from server.services.factory_controller import get_factory_controller
                    controller = get_factory_controller(project_name, project_dir)
                    current_phase = data.get("current_phase", 1)
                    _startup_logger.warning(
                        "Factory recovery: %s was running phase %d. Restarting.",
                        project_name, current_phase,
                    )
                    # Restart the current phase
                    asyncio.create_task(controller.start(
                        mode=data.get("mode", "continuous"),
                        model=data.get("model", "claude-opus-4-6"),
                        yolo_mode=data.get("yolo_mode", False),
                        auto_commit=data.get("auto_commit", True),
                        rate_limit_strategy=data.get("rate_limit_strategy", "wait"),
                        start_phase=current_phase,
                    ))

                elif status == "waiting_rate_limit":
                    # Factory was waiting for rate limit — recreate timer
                    rate_limit = data.get("rate_limit", {})
                    resumes_at = rate_limit.get("resumes_at")
                    queued_phase = rate_limit.get("queued_phase")

                    if resumes_at and queued_phase:
                        from datetime import datetime, timezone
                        resume_dt = datetime.fromisoformat(resumes_at)
                        now = datetime.now(timezone.utc)
                        remaining = (resume_dt - now).total_seconds()

                        if remaining <= 0:
                            # Rate limit expired — start the queued phase
                            from server.services.factory_controller import get_factory_controller
                            controller = get_factory_controller(project_name, project_dir)
                            _startup_logger.info(
                                "Factory recovery: %s rate limit expired. Starting phase %d.",
                                project_name, queued_phase,
                            )
                            asyncio.create_task(controller.start(
                                mode=data.get("mode", "continuous"),
                                model=data.get("model", "claude-opus-4-6"),
                                yolo_mode=data.get("yolo_mode", False),
                                auto_commit=data.get("auto_commit", True),
                                rate_limit_strategy=data.get("rate_limit_strategy", "wait"),
                                start_phase=queued_phase,
                            ))
                        else:
                            # Still waiting — recreate the timer
                            from server.services.factory_controller import get_factory_controller
                            controller = get_factory_controller(project_name, project_dir)
                            _startup_logger.info(
                                "Factory recovery: %s waiting %.0f more seconds for rate limit. Phase %d queued.",
                                project_name, remaining, queued_phase,
                            )
                            controller._rate_limit_timer = asyncio.create_task(
                                controller._rate_limit_countdown(int(remaining), queued_phase)
                            )

            except Exception as e:
                _startup_logger.error("Factory recovery failed for %s: %s", project_name, e)

    except Exception as e:
        _startup_logger.error("Factory session recovery scan failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup - clean up orphaned lock files from previous runs
    cleanup_orphaned_locks()
    cleanup_orphaned_devserver_locks()

    # Start the scheduler service
    scheduler = get_scheduler()
    await scheduler.start()

    # Run log compaction on startup (non-blocking — errors are logged, not raised)
    from .services.log_compaction import run_compaction_all_projects
    try:
        await run_compaction_all_projects()
    except Exception as e:
        _startup_logger.warning("Log compaction on startup failed: %s", e)

    # Schedule daily log compaction at 3 AM UTC via APScheduler
    try:
        from apscheduler.triggers.cron import CronTrigger
        scheduler.scheduler.add_job(
            run_compaction_all_projects,
            CronTrigger(hour=3, minute=0),
            id="log_compaction_daily",
            replace_existing=True,
        )
        _startup_logger.info("Scheduled daily log compaction at 03:00 UTC")
    except Exception as e:
        _startup_logger.warning("Failed to schedule daily log compaction: %s", e)

    # Recover any factory sessions that were running before server restart
    await _recover_factory_sessions()

    yield

    # Shutdown - cleanup scheduler first to stop triggering new starts
    await cleanup_scheduler()
    # Then cleanup all running agents, sessions, terminals, and dev servers
    await cleanup_all_managers()
    await cleanup_assistant_sessions()
    await cleanup_all_design_guide_sessions()
    await cleanup_all_expand_sessions()
    await cleanup_all_terminals()
    await cleanup_all_devservers()
    await cleanup_background_sessions()
    await cleanup_all_workspace_sessions()
    await cleanup_all_swarms()
    await cleanup_all_monitors()
    cleanup_all_agent_os_sessions()
    await cleanup_all_sessions()
    await cleanup_all_capture_managers()


# Create FastAPI app
app = FastAPI(
    title="Autonomous Coding UI",
    description="Web UI for the Autonomous Coding Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Module logger
logger = logging.getLogger(__name__)

# Check if remote access is enabled via environment variable
# Set by start_ui.py when --host is not 127.0.0.1
ALLOW_REMOTE = os.environ.get("AUTOFORGE_ALLOW_REMOTE", "").lower() in ("1", "true", "yes")

if ALLOW_REMOTE:
    logger.warning(
        "ALLOW_REMOTE is enabled. Terminal WebSocket is exposed without sandboxing. "
        "Only use this in trusted network environments."
    )

# CORS - allow all origins when remote access is enabled, otherwise localhost only
if ALLOW_REMOTE:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for remote access
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",      # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:8888",      # Production
            "http://127.0.0.1:8888",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ============================================================================
# Security Middleware
# ============================================================================

if not ALLOW_REMOTE:
    @app.middleware("http")
    async def require_localhost(request: Request, call_next):
        """Only allow requests from localhost (disabled when AUTOFORGE_ALLOW_REMOTE=1)."""
        client_host = request.client.host if request.client else None

        # Allow localhost connections
        if client_host not in ("127.0.0.1", "::1", "localhost", None):
            raise HTTPException(status_code=403, detail="Localhost access only")

        return await call_next(request)


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(ci_status_router)
app.include_router(projects_router)
app.include_router(boilerplate_router)
app.include_router(styles_router)
app.include_router(features_router)
app.include_router(agent_router)
app.include_router(schedules_router)
app.include_router(devserver_router)
app.include_router(spec_creation_router)
app.include_router(design_guide_router)
app.include_router(expand_project_router)
app.include_router(filesystem_router)
app.include_router(github_router)
app.include_router(assistant_chat_router)
app.include_router(settings_router)
app.include_router(terminal_router)
app.include_router(workspace_router)
app.include_router(notifications_router)
app.include_router(role_library_router)
app.include_router(seo_tools_router)
app.include_router(swarm_router)
app.include_router(dunkstack_router)
app.include_router(agent_os_router)
app.include_router(yt_ingestion_router)
app.include_router(yt_processing_router)
app.include_router(captures_router)
app.include_router(execution_router)
app.include_router(yt_batch_router)
app.include_router(factory_router)
app.include_router(factory_presets_router)
app.include_router(actions_router)
app.include_router(commits_router)
app.include_router(verifications_router)
app.include_router(approvals_router)
app.include_router(checkpoints_router)
app.include_router(cli_scripter_router)
app.include_router(tool_factory_router)
app.include_router(tool_themes_router)


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/projects/{project_name}")
async def websocket_endpoint(websocket: WebSocket, project_name: str):
    """WebSocket endpoint for real-time project updates."""
    await project_websocket(websocket, project_name)


@app.websocket("/ws/execution/{session_id}")
async def execution_ws_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time execution events."""
    await execution_websocket(websocket, session_id)


# ============================================================================
# Setup & Health Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/setup/status", response_model=SetupStatus)
async def setup_status():
    """Check system setup status."""
    # Check for Claude CLI
    claude_cli = shutil.which("claude") is not None

    # Check for CLI configuration directory
    # Note: CLI no longer stores credentials in ~/.claude/.credentials.json
    # The existence of ~/.claude indicates the CLI has been configured
    claude_dir = Path.home() / ".claude"
    has_claude_config = claude_dir.exists() and claude_dir.is_dir()

    # If GLM mode is configured via .env, we have alternative credentials
    glm_configured = bool(os.getenv("ANTHROPIC_BASE_URL") and os.getenv("ANTHROPIC_AUTH_TOKEN"))
    credentials = has_claude_config or glm_configured

    # Check for Node.js and npm
    node = shutil.which("node") is not None
    npm = shutil.which("npm") is not None

    return SetupStatus(
        claude_cli=claude_cli,
        credentials=credentials,
        node=node,
        npm=npm,
    )


# ============================================================================
# Static File Serving (Production)
# ============================================================================

# Serve React build files if they exist
if UI_DIST_DIR.exists():
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=UI_DIST_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        """Serve the React app index.html with no-cache to prevent stale builds."""
        return FileResponse(
            UI_DIST_DIR / "index.html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """
        Serve static files or fall back to index.html for SPA routing.
        """
        # Check if the path is an API route (shouldn't hit this due to router ordering)
        if path.startswith("api/") or path.startswith("ws/"):
            raise HTTPException(status_code=404)

        # Try to serve the file directly
        file_path = (UI_DIST_DIR / path).resolve()

        # Ensure resolved path is within UI_DIST_DIR (prevent path traversal)
        try:
            file_path.relative_to(UI_DIST_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=404)

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Fall back to index.html for SPA routing (no-cache to prevent stale builds)
        return FileResponse(
            UI_DIST_DIR / "index.html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",  # Localhost only for security
        port=8888,
        reload=True,
    )
