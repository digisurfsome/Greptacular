"""
CLI Scripter Router — AI-powered prompt generation via Claude CLI.
Uses subscription auth (claude -p) — zero API credits.

Endpoints:
  POST /api/cli-scripter/generate       — Single prompt generation
  POST /api/cli-scripter/generate-all   — Chained PRD → Phase Split → Build Scripts
  POST /api/cli-scripter/write-scripts  — Write generated scripts to disk
  POST /api/cli-scripter/queue          — Manage app build queue
  GET  /api/cli-scripter/queue          — Get current queue
  GET  /api/cli-scripter/project-info   — Directory listing + git log for a project path
"""
import asyncio
import json
import logging
import os
import subprocess
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

# Use Max subscription, not API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true

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

# Use Max subscription, not API credits
unset ANTHROPIC_API_KEY 2>/dev/null || true

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
