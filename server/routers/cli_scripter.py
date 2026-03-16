"""
CLI Scripter Router — AI-powered prompt generation via Claude CLI.
Uses subscription auth (claude -p) — zero API credits.

Endpoints:
  POST /api/cli-scripter/generate             — Single prompt generation
  POST /api/cli-scripter/generate-all         — Chained PRD → Phase Split → Build Scripts
  POST /api/cli-scripter/write-scripts        — Write generated scripts to disk
  POST /api/cli-scripter/queue                — Manage app build queue
  GET  /api/cli-scripter/queue                — Get current queue
  GET  /api/cli-scripter/project-info         — Directory listing + git log for a project path
  GET  /api/cli-scripter/configs              — List all saved build configs
  POST /api/cli-scripter/configs              — Save new build config
  GET  /api/cli-scripter/configs/{id}         — Load a specific build config
  PUT  /api/cli-scripter/configs/{id}         — Update a build config
  DELETE /api/cli-scripter/configs/{id}       — Delete a build config
  PUT  /api/cli-scripter/queue/reorder        — Reorder queue items
  POST /api/cli-scripter/start-build          — Start run_all.sh as subprocess
  GET  /api/cli-scripter/build-status         — Current phase, tokens, timing
  GET  /api/cli-scripter/build-log            — Last N lines of build output
  POST /api/cli-scripter/stop-build           — Kill the subprocess
"""
import asyncio
import json
import logging
import os
import re
import signal
import sqlite3
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cli-scripter", tags=["cli-scripter"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "sonnet"


class AgentRole(BaseModel):
    id: str
    name: str
    model: str
    enabled: bool
    prompt: str
    description: str
    runs_when: str  # once_before | per_phase | per_phase_after | once_after | once_final


class GenerateAllRequest(BaseModel):
    """Request for chained generation: PRD → Phase Split → Build Scripts."""
    prd_prompt: str
    phase_split_prompt_template: str
    build_scripts_prompt_template: str
    model: str = "sonnet"
    project_dir: str | None = None


class WriteScriptsRequest(BaseModel):
    """Write the full 5-role pipeline scripts to disk."""
    project_dir: str
    project_name: str
    build_rules: str
    phases: list[str]  # Phase descriptions
    agent_roles: list[AgentRole]
    include_verification: bool = True
    waves: list[list[int]] | None = None       # Parallel wave groups e.g. [[1], [2, 3], [4]]
    parallel_mode: bool = False                # Enable parallel execution in master script
    boilerplate_id: str | None = None          # If 'web-mobile-supabase', add Phase 0 prep


class QueueItem(BaseModel):
    """A single app in the build queue."""
    name: str
    project_dir: str
    scripts_dir: str | None = None
    status: str = "pending"  # pending | running | completed | failed


class QueueRequest(BaseModel):
    """Manage the build queue."""
    action: str  # add | remove | start | stop | clear | reorder
    item: QueueItem | None = None
    index: int | None = None


# ---------------------------------------------------------------------------
# Rule block persistence (~/.autoforge/cli_scripter_rules.json)
# ---------------------------------------------------------------------------

RULES_FILE = Path.home() / ".autoforge" / "cli_scripter_rules.json"


class RuleBlock(BaseModel):
    """A single named rule block in the library."""
    id: str
    name: str
    content: str
    tags: list[str] = []
    label: str = ""
    order: int = 0
    combiner_main: bool = False
    combiner_p1: bool = False
    combiner_p2plus: bool = False
    created_at: str = ""
    updated_at: str = ""


class RulesPayload(BaseModel):
    """Full rules state for save/load."""
    version: int = 1
    blocks: list[RuleBlock] = []
    last_phase_mode: str = "single"


def _load_rules() -> dict:
    """Load rules from disk, returning a raw dict."""
    if RULES_FILE.exists():
        try:
            return json.loads(RULES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 1, "blocks": [], "last_phase_mode": "single"}
    return {"version": 1, "blocks": [], "last_phase_mode": "single"}


def _save_rules(data: dict) -> None:
    """Save rules to disk."""
    RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Build config storage (~/.autoforge/cli_scripter_configs.db)
# ---------------------------------------------------------------------------

CONFIGS_DB = Path.home() / ".autoforge" / "cli_scripter_configs.db"


def _get_db_conn() -> sqlite3.Connection:
    """Get a SQLite connection, creating the DB and table if needed."""
    CONFIGS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CONFIGS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS build_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            config_json TEXT NOT NULL,
            scripts_dir TEXT,
            project_dir TEXT,
            total_tokens_used INTEGER,
            build_duration_seconds INTEGER,
            phase_count INTEGER,
            notes TEXT
        )
    """)
    conn.commit()
    return conn


class BuildConfigSave(BaseModel):
    """Request to save a build configuration."""
    name: str
    config_json: dict
    scripts_dir: str | None = None
    project_dir: str | None = None
    status: str = "draft"
    phase_count: int | None = None
    notes: str | None = None


class BuildConfigUpdate(BaseModel):
    """Request to update a build configuration."""
    name: str | None = None
    config_json: dict | None = None
    scripts_dir: str | None = None
    project_dir: str | None = None
    status: str | None = None
    phase_count: int | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# In-memory queue (persisted to ~/.autoforge/build_queue.json)
# ---------------------------------------------------------------------------

_queue: list[dict] = []
_queue_running = False
QUEUE_FILE = Path.home() / ".autoforge" / "build_queue.json"


def _load_queue():
    global _queue
    if QUEUE_FILE.exists():
        try:
            _queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _queue = []


def _save_queue():
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(_queue, indent=2), encoding="utf-8")


# Load on module init
_load_queue()


# ---------------------------------------------------------------------------
# Claude CLI subprocess helper
# ---------------------------------------------------------------------------

class CliResult:
    """Result from a Claude CLI call with token usage info."""
    __slots__ = ("text", "input_tokens", "output_tokens", "cache_creation_tokens",
                 "cache_read_tokens", "cost_usd", "duration_seconds", "model")

    def __init__(self, text: str, usage: dict | None = None,
                 cost_usd: float = 0.0, duration_seconds: float = 0.0,
                 model: str = "sonnet"):
        self.text = text
        self.model = model
        self.duration_seconds = duration_seconds
        self.cost_usd = cost_usd
        u = usage or {}
        self.input_tokens = u.get("input_tokens", 0) or 0
        self.output_tokens = u.get("output_tokens", 0) or 0
        self.cache_creation_tokens = u.get("cache_creation_input_tokens", 0) or 0
        self.cache_read_tokens = u.get("cache_read_input_tokens", 0) or 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_creation_tokens + self.cache_read_tokens


async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 600) -> CliResult:
    """Run Claude CLI in print mode using subscription auth. Zero API credits.

    Returns a CliResult with the text output and token usage from the JSON
    response.  Uses ``--output-format json`` so we can capture token counts
    for the token budget ledger.
    """
    # Build env that forces subscription auth (clears API key + auth token)
    from registry import get_effective_sdk_env
    sdk_env = get_effective_sdk_env(force_subscription=True)
    cli_env = {**os.environ, **sdk_env}

    # Prevent "nested session" detection when the server was launched
    # from inside a Claude Code session.  CLAUDECODE=1 causes the child
    # `claude` process to refuse to start.
    cli_env.pop("CLAUDECODE", None)
    cli_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    cli_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)

    logger.info(
        "_run_claude_cli: Starting claude -p (model=%s, timeout=%ds, prompt_len=%d)",
        model, timeout, len(prompt),
    )
    start_time = time.time()

    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", "--model", model, "--output-format", "json",
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

    elapsed = time.time() - start_time
    raw = stdout.decode().strip()

    # Parse JSON response — extract text + usage
    try:
        data = json.loads(raw)
        text = data.get("result", raw)
        usage = data.get("usage")
        cost_usd = data.get("total_cost_usd", 0.0)
    except (json.JSONDecodeError, KeyError):
        # Fallback: treat entire output as plain text (shouldn't happen)
        logger.warning("_run_claude_cli: Could not parse JSON, using raw output")
        text = raw
        usage = None
        cost_usd = 0.0

    result = CliResult(text=text, usage=usage, cost_usd=cost_usd,
                       duration_seconds=elapsed, model=model)
    logger.info(
        "_run_claude_cli: Completed in %.1fs — in=%d out=%d cache_create=%d cache_read=%d cost=$%.4f",
        elapsed, result.input_tokens, result.output_tokens,
        result.cache_creation_tokens, result.cache_read_tokens, result.cost_usd,
    )

    # Auto-log to token budget ledger
    try:
        from ..services import token_budget as tb
        tb.log_session(
            session_type="cli_scripter",
            model=model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cache_creation_tokens=result.cache_creation_tokens,
            cache_read_tokens=result.cache_read_tokens,
            cost_usd=result.cost_usd,
            duration_seconds=elapsed,
            source="autoforge",
        )
    except Exception as e:
        logger.warning("token_budget: failed to log session: %s", e)

    return result


# ---------------------------------------------------------------------------
# Script generation helpers
# ---------------------------------------------------------------------------

# Boilerplate repo URLs for template cloning
_BOILERPLATE_REPOS: dict[str, dict[str, str]] = {
    "web-supabase-stripe": {
        "owner": "digisurfsome",
        "repo": "Web-BoilerPlate-D2D",
    },
    "mobile-flutter-firebase": {
        "owner": "digisurfsome",
        "repo": "apparence-kit-firebase",
    },
}


def _generate_prep_script(project_name: str) -> str:
    """Generate Phase 0 prep script for dual builds (web + mobile).

    Clones both boilerplate repos and merges them into a single project directory.
    100% deterministic — bash script, no LLM.
    """
    web_repo = _BOILERPLATE_REPOS["web-supabase-stripe"]
    mobile_repo = _BOILERPLATE_REPOS["mobile-flutter-firebase"]

    return f'''#!/bin/bash
# ===========================================
# PHASE 0 — Boilerplate Prep (Dual Build)
# Project: {project_name}
# Merges web + mobile boilerplate repos
# 100% deterministic — no LLM
# ===========================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "============================================"
echo "  PHASE 0: Boilerplate Merge"
echo "  Combining web + mobile templates"
echo "============================================"
echo ""

# Clone web boilerplate if not already present
if [ ! -d "web" ]; then
  echo ">>> Cloning web boilerplate..."
  git clone https://github.com/{web_repo["owner"]}/{web_repo["repo"]}.git web
  echo ">>> Web boilerplate cloned to ./web/"
else
  echo ">>> Web directory already exists, skipping clone"
fi

# Clone mobile boilerplate if not already present
if [ ! -d "mobile" ]; then
  echo ">>> Cloning mobile boilerplate..."
  git clone https://github.com/{mobile_repo["owner"]}/{mobile_repo["repo"]}.git mobile
  echo ">>> Mobile boilerplate cloned to ./mobile/"
else
  echo ">>> Mobile directory already exists, skipping clone"
fi

# Create shared config directory
mkdir -p shared

# Create a shared .env template
if [ ! -f "shared/.env.example" ]; then
  cat > shared/.env.example <<'ENV_EOF'
# Shared configuration for web + mobile
# Supabase (used by both web and mobile)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Stripe (web payments)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=

# RevenueCat (mobile payments)
REVENUECAT_API_KEY_IOS=
REVENUECAT_API_KEY_ANDROID=

# Analytics
NEXT_PUBLIC_POSTHOG_KEY=
MIXPANEL_TOKEN=
ENV_EOF
  echo ">>> Created shared/.env.example"
fi

echo ""
echo "=== Phase 0 complete ==="
echo "Directory structure:"
echo "  ./web/     — Next.js web app"
echo "  ./mobile/  — Flutter mobile app"
echo "  ./shared/  — Shared configuration"
'''


def _generate_script_content(
    role_name: str,
    description: str,
    model: str,
    prompt: str,
    project_name: str,
) -> str:
    """Generate a bash script for a single agent role."""
    # We use a heredoc with a quoted delimiter so no expansion happens
    return f'''#!/bin/bash
# ===========================================
# {role_name.upper()} — {description}
# Model: {model}
# Project: {project_name}
# ===========================================
set -e

# Use Max subscription, not API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDECODE 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true
unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "============================================"
echo "  {role_name.upper()}: {description}"
echo "  Model: {model}"
echo "============================================"
echo ""

claude -p --model {model} --dangerously-skip-permissions <<'PROMPT_EOF'
{prompt}
PROMPT_EOF

echo ""
echo "=== {role_name} complete ==="
'''


def _generate_master_script(
    project_name: str,
    script_files: list[str],
    phase_count: int,
    waves: list[list[int]] | None = None,
    parallel_mode: bool = False,
    include_prep: bool = False,
) -> str:
    """Generate the run_all.sh master script.

    If waves is provided and parallel_mode is True, phases in the same wave
    run concurrently using bash background jobs + wait.
    If include_prep is True, adds Phase 0 prep step before the architect.
    """
    total = len(script_files)

    # Build the body
    steps = []

    # Phase 0: Boilerplate prep (dual builds only)
    if include_prep:
        steps.append('''# Phase 0: Boilerplate Prep (deterministic — no LLM)
if [ -f "$SCRIPT_DIR/phase0_prep.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Phase 0 — Boilerplate Prep..."
  bash "$SCRIPT_DIR/phase0_prep.sh"
  echo ">>> Phase 0 complete"
  echo ""
fi''')

    # Check for architect
    steps.append('''# Architect
if [ -f "$SCRIPT_DIR/architect.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Architect — Creating blueprint..."
  bash "$SCRIPT_DIR/architect.sh"
  echo ">>> Architect complete"
  echo ""
fi''')

    # Determine wave structure for phases
    if parallel_mode and waves and any(len(w) > 1 for w in waves):
        # Wave-based parallel execution
        wave_steps = []
        for wave_idx, wave_phases in enumerate(waves):
            wave_num = wave_idx + 1
            if len(wave_phases) == 1:
                # Sequential phase
                p = wave_phases[0]
                wave_steps.append(f'''# Wave {wave_num}: Phase {p} (sequential)
CURRENT=$((CURRENT + 1))
echo ">>> [$CURRENT/$TOTAL_STEPS] Wave {wave_num} — Phase {p} Build..."
bash "$SCRIPT_DIR/phase{p}_build.sh"
if [ -f "$SCRIPT_DIR/phase{p}_review.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Wave {wave_num} — Phase {p} Review..."
  bash "$SCRIPT_DIR/phase{p}_review.sh"
fi
echo ""''')
            else:
                # Parallel phases
                phase_list = ', '.join(str(p) for p in wave_phases)
                parallel_block = [f'echo "=== Wave {wave_num} (parallel: Phases {phase_list}) ==="']
                pid_vars = []
                for p in wave_phases:
                    pid_var = f"PID_phase{p}"
                    parallel_block.append(f'bash "$SCRIPT_DIR/phase{p}_build.sh" > "$SCRIPT_DIR/phase{p}.log" 2>&1 &')
                    parallel_block.append(f'{pid_var}=$!')
                    pid_vars.append((p, pid_var))
                # Wait for all
                status_checks = []
                for p, pid_var in pid_vars:
                    parallel_block.append(f'wait ${pid_var}')
                    parallel_block.append(f'STATUS{p}=$?')
                    status_checks.append(f'[ $STATUS{p} -ne 0 ]')
                # Check failures
                fail_check = ' || '.join(status_checks)
                phase_log_lines = ' '.join(f'"$SCRIPT_DIR/phase{p}.log"' for p, _ in pid_vars)
                parallel_block.append(f'''if {fail_check}; then
  echo "Wave {wave_num} failed — check logs: {phase_log_lines}"
  exit 1
fi
echo "Wave {wave_num} complete"
echo ""''')
                wave_steps.append('\n'.join(parallel_block))

        steps.append('\n\n'.join(wave_steps))
    else:
        # Standard sequential phase loop
        steps.append(f'''# Build + Review per phase
for i in $(seq 1 {phase_count}); do
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Phase $i — Build..."
  bash "$SCRIPT_DIR/phase${{i}}_build.sh"

  if [ -f "$SCRIPT_DIR/phase${{i}}_review.sh" ]; then
    CURRENT=$((CURRENT + 1))
    echo ">>> [$CURRENT/$TOTAL_STEPS] Phase $i — Review..."
    bash "$SCRIPT_DIR/phase${{i}}_review.sh"
  fi
  echo ""
done''')

    # Verifier
    steps.append('''# Post-build verification
if [ -f "$SCRIPT_DIR/verify.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Post-Build Verification..."
  bash "$SCRIPT_DIR/verify.sh"
  echo ""
fi''')

    # Cartographer
    steps.append('''# Documentation
if [ -f "$SCRIPT_DIR/cartographer.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Documenting codebase..."
  bash "$SCRIPT_DIR/cartographer.sh"
  echo ""
fi''')

    body = "\n\n".join(steps)

    parallel_note = " (parallel waves enabled)" if parallel_mode and waves else ""

    return f'''#!/bin/bash
# ===========================================
# CLI SCRIPTER — Master Build Pipeline
# Project: {project_name}
# Total steps: {total}{parallel_note}
# ===========================================
set -e

# Use Max subscription, not API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDECODE 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true
unset CLAUDE_CODE_OAUTH_TOKEN 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL_STEPS={total}
CURRENT=0

echo "=========================================="
echo "  BUILD PIPELINE — {project_name}"
echo "  {total} steps ({phase_count} phases + roles){parallel_note}"
echo "=========================================="
echo ""

{body}

echo "=========================================="
echo "  BUILD COMPLETE"
echo "  All steps finished"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. git log --oneline -10    # Check all commits"
echo "  2. git push origin main     # Push to remote"
echo "  3. Deploy to production     # Your deploy process"
'''


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate(request: GenerateRequest):
    """Process a single prompt through Claude CLI. Subscription auth — $0."""
    try:
        result = await _run_claude_cli(request.prompt, request.model)
        return {
            "result": result.text,
            "usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "total_tokens": result.total_tokens,
                "cost_usd": result.cost_usd,
                "duration_seconds": result.duration_seconds,
                "model": result.model,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CLI Scripter generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-all")
async def generate_all(request: GenerateAllRequest):
    """Chain generation steps: PRD → Phase Split.

    Step 3 (build scripts) is now DETERMINISTIC — use /write-scripts instead.
    build_scripts_prompt_template is kept for backwards compatibility but ignored.
    """
    results = {}

    try:
        # Step 1: Generate PRD
        logger.info("CLI Scripter: Step 1/2 — Generating PRD...")
        prd_cli = await _run_claude_cli(request.prd_prompt, request.model)
        results["prd"] = prd_cli.text

        # Step 2: Phase Split (inject PRD)
        logger.info("CLI Scripter: Step 2/2 — Splitting into phases...")
        phase_prompt = request.phase_split_prompt_template.replace(
            "{previous_output}", prd_cli.text
        )
        phase_cli = await _run_claude_cli(phase_prompt, request.model)
        results["phase_split"] = phase_cli.text

        # Step 3: Script generation is now DETERMINISTIC via /write-scripts endpoint.
        # No LLM call needed — scripts are pure string templates.
        results["build_scripts"] = (
            "Scripts are generated deterministically via the 'Save Scripts to Disk' button. "
            "No LLM tokens used for script assembly."
        )

        # Combine token usage from both CLI calls
        combined_usage = {
            "input_tokens": prd_cli.input_tokens + phase_cli.input_tokens,
            "output_tokens": prd_cli.output_tokens + phase_cli.output_tokens,
            "total_tokens": prd_cli.total_tokens + phase_cli.total_tokens,
            "cost_usd": prd_cli.cost_usd + phase_cli.cost_usd,
            "duration_seconds": prd_cli.duration_seconds + phase_cli.duration_seconds,
            "model": request.model,
            "steps": {
                "prd": {
                    "input_tokens": prd_cli.input_tokens,
                    "output_tokens": prd_cli.output_tokens,
                    "total_tokens": prd_cli.total_tokens,
                    "cost_usd": prd_cli.cost_usd,
                    "duration_seconds": prd_cli.duration_seconds,
                },
                "phase_split": {
                    "input_tokens": phase_cli.input_tokens,
                    "output_tokens": phase_cli.output_tokens,
                    "total_tokens": phase_cli.total_tokens,
                    "cost_usd": phase_cli.cost_usd,
                    "duration_seconds": phase_cli.duration_seconds,
                },
            },
        }

        return {"results": results, "steps_completed": 2, "usage": combined_usage}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("CLI Scripter generate-all failed: %s", e)
        results["error"] = str(e)
        raise HTTPException(status_code=500, detail={
            "message": str(e),
            "partial_results": results,
        })


@router.post("/write-scripts")
async def write_scripts(request: WriteScriptsRequest):
    """Write the full 5-role pipeline scripts to disk."""
    try:
        scripts_dir = Path(request.project_dir) / "scripts" / "cli-scripter"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        written_files = []
        all_script_names = []

        # Phase 0: Boilerplate prep for dual builds (web + mobile)
        if request.boilerplate_id == "web-mobile-supabase":
            prep_content = _generate_prep_script(request.project_name)
            prep_filename = "phase0_prep.sh"
            (scripts_dir / prep_filename).write_text(prep_content, encoding="utf-8")
            written_files.append(prep_filename)
            all_script_names.append(prep_filename)

        for role in request.agent_roles:
            if not role.enabled:
                continue

            if role.runs_when == "once_before":
                # Architect — single script
                filename = f"{role.id}.sh"
                prompt = role.prompt.replace("{build_rules}", request.build_rules)
                content = _generate_script_content(
                    role.name, role.description, role.model, prompt, request.project_name
                )
                (scripts_dir / filename).write_text(content, encoding="utf-8")
                written_files.append(filename)
                all_script_names.append(filename)

            elif role.runs_when == "per_phase":
                # Coder — one per phase
                for i, phase_spec in enumerate(request.phases, 1):
                    filename = f"phase{i}_build.sh"
                    prompt = (
                        role.prompt
                        .replace("{build_rules}", request.build_rules)
                        .replace("{phase_spec}", phase_spec)
                        .replace("{phase_number}", str(i))
                        .replace("{total_phases}", str(len(request.phases)))
                    )
                    content = _generate_script_content(
                        f"{role.name} (Phase {i})", role.description, role.model, prompt, request.project_name
                    )
                    (scripts_dir / filename).write_text(content, encoding="utf-8")
                    written_files.append(filename)
                    all_script_names.append(filename)

            elif role.runs_when == "per_phase_after":
                # Reviewer — one per phase
                for i in range(1, len(request.phases) + 1):
                    filename = f"phase{i}_review.sh"
                    prompt = (
                        role.prompt
                        .replace("{phase_number}", str(i))
                        .replace("{total_phases}", str(len(request.phases)))
                    )
                    content = _generate_script_content(
                        f"{role.name} (Phase {i})", role.description, role.model, prompt, request.project_name
                    )
                    (scripts_dir / filename).write_text(content, encoding="utf-8")
                    written_files.append(filename)
                    all_script_names.append(filename)

            elif role.runs_when == "once_after":
                # Verifier
                if not request.include_verification:
                    continue
                filename = "verify.sh"
                # Try to read verification template
                template_path = Path(request.project_dir) / ".claude" / "templates" / "e2e_verification_prompt.template.md"
                if template_path.exists():
                    verification_prompt = template_path.read_text(encoding="utf-8")
                else:
                    verification_prompt = role.prompt
                prompt = verification_prompt.replace("{verification_template}", role.prompt)
                content = _generate_script_content(
                    role.name, role.description, role.model, prompt, request.project_name
                )
                (scripts_dir / filename).write_text(content, encoding="utf-8")
                written_files.append(filename)
                all_script_names.append(filename)

            elif role.runs_when == "once_final":
                # Cartographer
                filename = f"{role.id}.sh"
                content = _generate_script_content(
                    role.name, role.description, role.model, role.prompt, request.project_name
                )
                (scripts_dir / filename).write_text(content, encoding="utf-8")
                written_files.append(filename)
                all_script_names.append(filename)

        # Generate master script
        master = _generate_master_script(
            request.project_name,
            all_script_names,
            len(request.phases),
            waves=request.waves,
            parallel_mode=request.parallel_mode,
            include_prep=request.boilerplate_id == "web-mobile-supabase",
        )
        (scripts_dir / "run_all.sh").write_text(master, encoding="utf-8")
        written_files.append("run_all.sh")

        return {
            "scripts_dir": str(scripts_dir),
            "files": written_files,
            "count": len(written_files),
        }

    except Exception as e:
        logger.error("Failed to write scripts: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Rule block endpoints
# ---------------------------------------------------------------------------

@router.get("/rules")
async def get_rules():
    """Load all rule blocks from disk."""
    data = _load_rules()
    return data


@router.post("/rules")
async def save_rules(payload: RulesPayload):
    """Save all rule blocks to disk (full replace)."""
    data = payload.model_dump()
    _save_rules(data)
    return {"status": "saved", "block_count": len(payload.blocks)}


@router.get("/rules/combined")
async def get_combined_rules(slot: str = Query("main", description="Slot to merge: main, p1, or p2plus")):
    """Get merged text for a specific combiner slot.

    Merges all blocks that have the corresponding combiner checkbox set,
    in order of their 'order' field.
    """
    if slot not in ("main", "p1", "p2plus"):
        raise HTTPException(status_code=400, detail="slot must be 'main', 'p1', or 'p2plus'")

    data = _load_rules()
    blocks = data.get("blocks", [])

    key_map = {"main": "combiner_main", "p1": "combiner_p1", "p2plus": "combiner_p2plus"}
    slot_key = key_map[slot]

    # Filter and sort by order
    checked = [b for b in blocks if b.get(slot_key, False) and b.get("content", "").strip()]
    checked.sort(key=lambda b: b.get("order", 0))

    merged = "\n\n".join(b["content"].strip() for b in checked)
    token_estimate = len(merged) // 4

    return {
        "slot": slot,
        "text": merged,
        "block_count": len(checked),
        "token_estimate": token_estimate,
    }


# ---------------------------------------------------------------------------
# Boilerplate analysis docs (Phase 10)
# ---------------------------------------------------------------------------

# Mapping from boilerplate ID to analysis doc filename
_BOILERPLATE_DOCS: dict[str, str] = {
    "web-supabase-stripe": "boilerplate-web-d2d.md",
    "mobile-flutter-firebase": "boilerplate-flutter-firebase.md",
    "web-mobile-supabase": "boilerplate-web-d2d.md",  # Full stack uses the web doc + flutter doc
}


@router.get("/boilerplate-context")
async def get_boilerplate_context(
    boilerplate_id: str = Query(..., description="Boilerplate template ID"),
):
    """Return the analysis doc content for a boilerplate, to inject into PRD generation.

    For 'web-mobile-supabase' (dual build), returns both web and flutter docs concatenated.
    For 'scratch', returns empty string (no boilerplate context needed).
    """
    if boilerplate_id == "scratch":
        return {"boilerplate_id": boilerplate_id, "content": "", "token_estimate": 0}

    # Locate docs directory (relative to the project root)
    docs_dir = Path(__file__).parent.parent.parent / "docs"

    contents: list[str] = []

    if boilerplate_id == "web-mobile-supabase":
        # Dual build: include both docs
        for doc_name in ["boilerplate-web-d2d.md", "boilerplate-flutter-firebase.md"]:
            doc_path = docs_dir / doc_name
            if doc_path.exists():
                contents.append(doc_path.read_text(encoding="utf-8"))
    else:
        doc_name = _BOILERPLATE_DOCS.get(boilerplate_id)
        if doc_name:
            doc_path = docs_dir / doc_name
            if doc_path.exists():
                contents.append(doc_path.read_text(encoding="utf-8"))

    combined = "\n\n---\n\n".join(contents)
    return {
        "boilerplate_id": boilerplate_id,
        "content": combined,
        "token_estimate": len(combined) // 4,
    }


# ---------------------------------------------------------------------------
# Project info endpoint (file listing + git log)
# ---------------------------------------------------------------------------

def _relative_time(dt: datetime) -> str:
    """Convert a datetime to a human-readable relative time string."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''} ago"


@router.get("/project-info")
async def project_info(path: str = Query(..., description="Absolute path to the project directory")):
    """Return top-level file listing and recent git commits for a project directory.

    Used by the ProjectFileBrowser component to show what's in the selected directory.
    """
    project_path = Path(path)

    if not project_path.is_absolute():
        raise HTTPException(status_code=400, detail="Path must be absolute")

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # List top-level entries
    files = []
    try:
        for entry in sorted(project_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            # Skip hidden files except .autoforge and .claude
            if entry.name.startswith('.') and entry.name not in ('.autoforge', '.claude'):
                continue
            try:
                stat = entry.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                files.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else None,
                    "modified": mtime.isoformat(),
                    "modified_relative": _relative_time(mtime),
                })
            except (OSError, PermissionError):
                # Skip entries we can't stat
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied reading directory")

    # Check for previous CLI Scripter builds
    scripts_dir = project_path / "scripts" / "cli-scripter"
    has_previous_builds = scripts_dir.exists() and scripts_dir.is_dir()

    # Get recent git commits (last 5)
    recent_commits: list[dict] = []
    git_dir = project_path / ".git"
    if git_dir.exists():
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--format=%H|%s|%ai", "-5"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split("|", 2)
                    if len(parts) >= 3:
                        commit_hash, message, date_str = parts
                        try:
                            commit_dt = datetime.fromisoformat(date_str.strip())
                            if commit_dt.tzinfo is None:
                                commit_dt = commit_dt.replace(tzinfo=timezone.utc)
                            recent_commits.append({
                                "hash": commit_hash[:8],
                                "message": message.strip(),
                                "date": commit_dt.isoformat(),
                                "date_relative": _relative_time(commit_dt),
                            })
                        except (ValueError, IndexError):
                            recent_commits.append({
                                "hash": commit_hash[:8],
                                "message": message.strip(),
                                "date": date_str.strip(),
                                "date_relative": "",
                            })
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # git not available or timeout — skip commits
            pass

    return {
        "path": str(project_path),
        "files": files,
        "recent_commits": recent_commits,
        "has_previous_builds": has_previous_builds,
        "is_git_repo": git_dir.exists(),
    }


# ---------------------------------------------------------------------------
# Queue endpoints
# ---------------------------------------------------------------------------

@router.get("/queue")
async def get_queue():
    """Get the current build queue."""
    _load_queue()
    return {"queue": _queue, "running": _queue_running}


@router.post("/queue")
async def manage_queue(request: QueueRequest):
    """Manage the build queue: add, remove, reorder, clear."""
    global _queue, _queue_running

    _load_queue()

    if request.action == "add" and request.item:
        _queue.append(request.item.model_dump())
        _save_queue()
        return {"queue": _queue, "added": request.item.name}

    elif request.action == "remove" and request.index is not None:
        if 0 <= request.index < len(_queue):
            removed = _queue.pop(request.index)
            _save_queue()
            return {"queue": _queue, "removed": removed}
        raise HTTPException(status_code=400, detail="Invalid queue index")

    elif request.action == "clear":
        _queue = []
        _save_queue()
        return {"queue": _queue, "cleared": True}

    elif request.action == "reorder" and request.index is not None and request.item:
        # Move item from current position to new index
        old_items = [q for q in _queue if q.get("name") != request.item.name]
        idx = min(request.index, len(old_items))
        old_items.insert(idx, request.item.model_dump())
        _queue = old_items
        _save_queue()
        return {"queue": _queue}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")


class QueueReorderRequest(BaseModel):
    """Reorder queue by providing a new ordered list of item names."""
    order: list[str]  # app names in desired order


@router.put("/queue/reorder")
async def reorder_queue(request: QueueReorderRequest):
    """Reorder the build queue by providing a new ordered list of names."""
    global _queue
    _load_queue()
    # Build a name -> item lookup
    lookup = {item.get("name", ""): item for item in _queue}
    # Reorder, preserving items not in the request order at the end
    new_order = [lookup[name] for name in request.order if name in lookup]
    remaining = [item for item in _queue if item.get("name", "") not in request.order]
    _queue = new_order + remaining
    _save_queue()
    return {"queue": _queue}


# ---------------------------------------------------------------------------
# Build config CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/configs")
async def list_configs():
    """List all saved build configurations."""
    conn = _get_db_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at, updated_at, status, scripts_dir, project_dir, phase_count, notes "
            "FROM build_configs ORDER BY updated_at DESC"
        ).fetchall()
        return {"configs": [dict(row) for row in rows]}
    except Exception as e:
        logger.error("Failed to list configs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/configs")
async def save_config(request: BuildConfigSave):
    """Save a new build configuration."""
    conn = _get_db_conn()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """INSERT INTO build_configs
               (name, created_at, updated_at, status, config_json, scripts_dir, project_dir, phase_count, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.name,
                now,
                now,
                request.status,
                json.dumps(request.config_json),
                request.scripts_dir,
                request.project_dir,
                request.phase_count,
                request.notes,
            ),
        )
        conn.commit()
        config_id = cursor.lastrowid
        return {"id": config_id, "name": request.name, "created_at": now}
    except Exception as e:
        logger.error("Failed to save config: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/configs/{config_id}")
async def load_config(config_id: int):
    """Load a saved build configuration by ID."""
    conn = _get_db_conn()
    try:
        row = conn.execute(
            "SELECT * FROM build_configs WHERE id = ?", (config_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Config not found")
        result = dict(row)
        # Parse config_json back to dict
        result["config_json"] = json.loads(result["config_json"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to load config %d: %s", config_id, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/configs/{config_id}")
async def update_config(config_id: int, request: BuildConfigUpdate):
    """Update an existing build configuration."""
    conn = _get_db_conn()
    try:
        row = conn.execute("SELECT * FROM build_configs WHERE id = ?", (config_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Config not found")

        now = datetime.now(timezone.utc).isoformat()
        updates: list[str] = ["updated_at = ?"]
        values: list = [now]

        if request.name is not None:
            updates.append("name = ?")
            values.append(request.name)
        if request.config_json is not None:
            updates.append("config_json = ?")
            values.append(json.dumps(request.config_json))
        if request.scripts_dir is not None:
            updates.append("scripts_dir = ?")
            values.append(request.scripts_dir)
        if request.project_dir is not None:
            updates.append("project_dir = ?")
            values.append(request.project_dir)
        if request.status is not None:
            updates.append("status = ?")
            values.append(request.status)
        if request.phase_count is not None:
            updates.append("phase_count = ?")
            values.append(request.phase_count)
        if request.notes is not None:
            updates.append("notes = ?")
            values.append(request.notes)

        values.append(config_id)
        conn.execute(f"UPDATE build_configs SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
        return {"id": config_id, "updated_at": now}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update config %d: %s", config_id, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/configs/{config_id}")
async def delete_config(config_id: int):
    """Delete a saved build configuration."""
    conn = _get_db_conn()
    try:
        result = conn.execute("DELETE FROM build_configs WHERE id = ?", (config_id,))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Config not found")
        return {"deleted": config_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete config %d: %s", config_id, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Build Process Manager — subprocess lifecycle + PID tracking (Phase 1)
# ---------------------------------------------------------------------------

# In-memory state for the active build process. Only one build can run at a time.
_build_process: subprocess.Popen | None = None
_build_pid: int | None = None
_build_status: str = "idle"  # idle | running | completed | failed | stopped
_build_start_time: float | None = None
_build_project_dir: str | None = None
_build_log_lines: deque[str] = deque(maxlen=500)
_build_log_file: Path | None = None

# Progress parser state (Phase 2) — extracted from build output
_build_current_phase: int = 0
_build_total_phases: int = 0
_build_phase_statuses: dict[int, str] = {}  # phase_num -> pending|active|completed|failed
_build_total_tokens: int = 0
_build_phase_timings: dict[int, dict[str, float]] = {}  # phase_num -> {start, end}


def _reset_build_state() -> None:
    """Reset all build tracking state to idle defaults."""
    global _build_process, _build_pid, _build_status, _build_start_time
    global _build_project_dir, _build_log_file
    global _build_current_phase, _build_total_phases, _build_phase_statuses
    global _build_total_tokens, _build_phase_timings
    _build_process = None
    _build_pid = None
    _build_status = "idle"
    _build_start_time = None
    _build_project_dir = None
    _build_log_file = None
    _build_log_lines.clear()
    _build_current_phase = 0
    _build_total_phases = 0
    _build_phase_statuses = {}
    _build_total_tokens = 0
    _build_phase_timings = {}


# ---------------------------------------------------------------------------
# Progress Parser — regex extraction from CLI stdout (Phase 2)
# ---------------------------------------------------------------------------

# Patterns to detect in build output:
#   ">>> [2/8] Phase 1 — Build..."  -> phase started
#   ">>> Architect complete"         -> architect done
#   "=== Phase 1 complete ==="      -> phase finished
#   "Total tokens: 12345"           -> token usage
#   "Error:" or non-zero exit       -> failure

_RE_STEP_START = re.compile(
    r">>>\s*\[(\d+)/(\d+)\]\s*(Wave\s+\d+\s*—\s*)?Phase\s+(\d+)\s*—?\s*(Build|Review)",
    re.IGNORECASE,
)
_RE_ARCHITECT_START = re.compile(
    r">>>\s*\[(\d+)/(\d+)\]\s*Architect",
    re.IGNORECASE,
)
_RE_PHASE_COMPLETE = re.compile(
    r"===\s*(Architect|Phase\s+(\d+))\s*complete\s*===",
    re.IGNORECASE,
)
_RE_BUILD_COMPLETE = re.compile(
    r"BUILD\s+COMPLETE",
    re.IGNORECASE,
)
_RE_TOKEN_COUNT = re.compile(
    r"Total\s+tokens?:?\s*([\d,]+)",
    re.IGNORECASE,
)
_RE_ERROR = re.compile(
    r"^(Error:|FATAL|Traceback|failed|BUILD FAILED)",
    re.IGNORECASE | re.MULTILINE,
)
_RE_STEP_COUNT = re.compile(
    r"(\d+)\s+steps?\s*\((\d+)\s+phases?",
    re.IGNORECASE,
)
_RE_VERIFICATION_START = re.compile(
    r">>>\s*\[\d+/\d+\]\s*Post-Build\s+Verification",
    re.IGNORECASE,
)
_RE_CARTOGRAPHER_START = re.compile(
    r">>>\s*\[\d+/\d+\]\s*Documenting",
    re.IGNORECASE,
)


def _parse_build_line(line: str) -> None:
    """Parse a single line of build output to update progress state.

    This is 100% deterministic — pure regex, no LLM.
    """
    global _build_current_phase, _build_total_phases, _build_total_tokens

    # Detect total step count from the build header
    m = _RE_STEP_COUNT.search(line)
    if m:
        _build_total_phases = int(m.group(2))
        return

    # Detect architect start
    m = _RE_ARCHITECT_START.search(line)
    if m:
        _build_phase_statuses[0] = "active"
        _build_phase_timings[0] = {"start": time.time()}
        return

    # Detect phase step start (build or review)
    m = _RE_STEP_START.search(line)
    if m:
        phase_num = int(m.group(4))
        step_type = m.group(5).lower()
        if step_type == "build":
            _build_current_phase = phase_num
            _build_phase_statuses[phase_num] = "active"
            if phase_num not in _build_phase_timings:
                _build_phase_timings[phase_num] = {"start": time.time()}
        return

    # Detect phase/architect complete
    m = _RE_PHASE_COMPLETE.search(line)
    if m:
        if m.group(1).lower().startswith("architect"):
            _build_phase_statuses[0] = "completed"
            if 0 in _build_phase_timings:
                _build_phase_timings[0]["end"] = time.time()
        elif m.group(2):
            phase_num = int(m.group(2))
            _build_phase_statuses[phase_num] = "completed"
            if phase_num in _build_phase_timings:
                _build_phase_timings[phase_num]["end"] = time.time()
        return

    # Detect verification start
    if _RE_VERIFICATION_START.search(line):
        _build_phase_statuses[-1] = "active"  # -1 = verifier
        _build_phase_timings[-1] = {"start": time.time()}
        return

    # Detect cartographer start
    if _RE_CARTOGRAPHER_START.search(line):
        _build_phase_statuses[-2] = "active"  # -2 = cartographer
        _build_phase_timings[-2] = {"start": time.time()}
        return

    # Detect build complete
    if _RE_BUILD_COMPLETE.search(line):
        # Mark any active special phases as completed
        for key in [-1, -2]:
            if _build_phase_statuses.get(key) == "active":
                _build_phase_statuses[key] = "completed"
                if key in _build_phase_timings:
                    _build_phase_timings[key]["end"] = time.time()
        return

    # Detect token count
    m = _RE_TOKEN_COUNT.search(line)
    if m:
        _build_total_tokens = int(m.group(1).replace(",", ""))
        return


async def _stream_build_output(proc: subprocess.Popen) -> None:
    """Read build stdout line-by-line in a background task, parsing progress."""
    global _build_status

    loop = asyncio.get_event_loop()

    def _read_lines():
        """Blocking reader for subprocess stdout."""
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n").rstrip("\r")
            _build_log_lines.append(line)
            _parse_build_line(line)
            # Also write to log file if configured
            if _build_log_file:
                try:
                    with open(_build_log_file, "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except OSError:
                    pass

    try:
        await loop.run_in_executor(None, _read_lines)
    except Exception as e:
        logger.error("Build output reader failed: %s", e)

    # Process has finished — check exit code
    proc.wait()
    if proc.returncode == 0:
        _build_status = "completed"
    elif _build_status != "stopped":
        _build_status = "failed"
        # Mark current active phase as failed
        for phase_num, status in list(_build_phase_statuses.items()):
            if status == "active":
                _build_phase_statuses[phase_num] = "failed"


class StartBuildRequest(BaseModel):
    """Request to start a build subprocess."""
    project_dir: str
    scripts_subdir: str = "scripts/cli-scripter"


@router.post("/start-build")
async def start_build(request: StartBuildRequest):
    """Start run_all.sh as a subprocess, tracking PID and streaming output."""
    global _build_process, _build_pid, _build_status, _build_start_time
    global _build_project_dir, _build_log_file

    # Prevent multiple concurrent builds
    if _build_process is not None and _build_process.poll() is None:
        raise HTTPException(
            status_code=409,
            detail="A build is already running. Stop it first.",
        )

    project_path = Path(request.project_dir)
    scripts_path = project_path / request.scripts_subdir / "run_all.sh"

    if not scripts_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Build script not found: {scripts_path}",
        )

    # Reset state for new build
    _reset_build_state()
    _build_project_dir = request.project_dir
    _build_start_time = time.time()
    _build_status = "running"

    # Create log file in the scripts directory
    _build_log_file = project_path / request.scripts_subdir / "build.log"

    try:
        # Build env that forces subscription auth for the build subprocess.
        # The generated bash scripts already `unset ANTHROPIC_API_KEY` as a
        # safety net, but stripping it from the env is the correct fix.
        from registry import get_effective_sdk_env
        build_env = {**os.environ, **get_effective_sdk_env(force_subscription=True), "PYTHONUNBUFFERED": "1"}
        build_env.pop("CLAUDECODE", None)
        build_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        build_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)

        # Start the build subprocess
        _build_process = subprocess.Popen(
            ["bash", str(scripts_path)],
            cwd=str(project_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line-buffered
            env=build_env,
            start_new_session=(os.name != "nt"),  # Separate process group on Linux so killpg doesn't kill the server
        )
        _build_pid = _build_process.pid

        # Start background output reader
        asyncio.create_task(_stream_build_output(_build_process))

        return {
            "status": "started",
            "pid": _build_pid,
            "project_dir": request.project_dir,
            "log_file": str(_build_log_file),
        }

    except Exception as e:
        _build_status = "failed"
        logger.error("Failed to start build: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/build-status")
async def build_status():
    """Return current build status, phase progress, tokens, and timing."""
    elapsed = 0.0
    if _build_start_time:
        elapsed = time.time() - _build_start_time

    # Compute per-phase timing summaries
    phase_timing_summary = {}
    for phase_num, timing in _build_phase_timings.items():
        start = timing.get("start", 0)
        end = timing.get("end", time.time() if _build_phase_statuses.get(phase_num) == "active" else start)
        phase_timing_summary[str(phase_num)] = {
            "elapsed_seconds": round(end - start, 1),
            "status": _build_phase_statuses.get(phase_num, "pending"),
        }

    return {
        "status": _build_status,
        "pid": _build_pid,
        "project_dir": _build_project_dir,
        "elapsed_seconds": round(elapsed, 1),
        "current_phase": _build_current_phase,
        "total_phases": _build_total_phases,
        "phase_statuses": {str(k): v for k, v in _build_phase_statuses.items()},
        "phase_timings": phase_timing_summary,
        "total_tokens": _build_total_tokens,
        "log_lines_count": len(_build_log_lines),
    }


@router.get("/build-log")
async def build_log(
    last_n: int = Query(100, ge=1, le=500, description="Number of recent log lines to return"),
):
    """Return the last N lines of build output."""
    lines = list(_build_log_lines)[-last_n:]
    return {
        "lines": lines,
        "total": len(_build_log_lines),
        "status": _build_status,
    }


@router.post("/stop-build")
async def stop_build():
    """Stop the currently running build subprocess."""
    global _build_status

    if _build_process is None or _build_process.poll() is not None:
        return {"status": "no_build_running", "build_status": _build_status}

    _build_status = "stopped"

    try:
        # Try SIGTERM first (graceful shutdown)
        if os.name == "nt":
            # Windows: use taskkill for process tree
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(_build_process.pid)],
                capture_output=True,
                timeout=5,
            )
        else:
            os.killpg(os.getpgid(_build_process.pid), signal.SIGTERM)

        # Wait briefly for graceful shutdown
        try:
            _build_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if still running
            _build_process.kill()
            _build_process.wait(timeout=3)

        # Mark any active phases as failed
        for phase_num, status in list(_build_phase_statuses.items()):
            if status == "active":
                _build_phase_statuses[phase_num] = "failed"

        return {
            "status": "stopped",
            "pid": _build_pid,
        }

    except Exception as e:
        logger.error("Failed to stop build: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
