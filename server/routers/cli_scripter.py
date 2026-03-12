"""
CLI Scripter Router — AI-powered prompt generation via Claude CLI.
Uses subscription auth (claude -p) — zero API credits.

Endpoints:
  POST /api/cli-scripter/generate      — Single prompt generation
  POST /api/cli-scripter/generate-all   — Chained PRD → Phase Split → Build Scripts
  POST /api/cli-scripter/write-scripts  — Write generated scripts to disk
  POST /api/cli-scripter/queue          — Manage app build queue
  GET  /api/cli-scripter/queue          — Get current queue
"""
import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
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

async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 300) -> str:
    """Run Claude CLI in print mode using subscription auth. Zero API credits."""
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", "--model", model, "--output-format", "text",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
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

    return stdout.decode().strip()


# ---------------------------------------------------------------------------
# Script generation helpers
# ---------------------------------------------------------------------------

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
) -> str:
    """Generate the run_all.sh master script."""
    total = len(script_files)

    # Build the body
    steps = []

    # Check for architect
    steps.append('''# Architect
if [ -f "$SCRIPT_DIR/architect.sh" ]; then
  CURRENT=$((CURRENT + 1))
  echo ">>> [$CURRENT/$TOTAL_STEPS] Architect — Creating blueprint..."
  bash "$SCRIPT_DIR/architect.sh"
  echo ">>> Architect complete"
  echo ""
fi''')

    # Phase loop
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

    return f'''#!/bin/bash
# ===========================================
# CLI SCRIPTER — Master Build Pipeline
# Project: {project_name}
# Total steps: {total}
# ===========================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOTAL_STEPS={total}
CURRENT=0

echo "=========================================="
echo "  BUILD PIPELINE — {project_name}"
echo "  {total} steps ({phase_count} phases + roles)"
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
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CLI Scripter generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-all")
async def generate_all(request: GenerateAllRequest):
    """Chain all 3 generation steps: PRD → Phase Split → Build Scripts.

    Each step feeds its output into the next step's prompt template.
    Templates should contain {previous_output} as a placeholder.
    """
    results = {}

    try:
        # Step 1: Generate PRD
        logger.info("CLI Scripter: Step 1/3 — Generating PRD...")
        prd_result = await _run_claude_cli(request.prd_prompt, request.model)
        results["prd"] = prd_result

        # Step 2: Phase Split (inject PRD)
        logger.info("CLI Scripter: Step 2/3 — Splitting into phases...")
        phase_prompt = request.phase_split_prompt_template.replace(
            "{previous_output}", prd_result
        )
        phase_result = await _run_claude_cli(phase_prompt, request.model)
        results["phase_split"] = phase_result

        # Step 3: Build Scripts (inject phases)
        logger.info("CLI Scripter: Step 3/3 — Generating build scripts...")
        build_prompt = request.build_scripts_prompt_template.replace(
            "{previous_output}", phase_result
        )
        build_result = await _run_claude_cli(build_prompt, request.model)
        results["build_scripts"] = build_result

        return {"results": results, "steps_completed": 3}

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
            request.project_name, all_script_names, len(request.phases)
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
