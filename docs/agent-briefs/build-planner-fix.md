# Agent Brief: Build Planner — Fix & Finish (Single Agent)

> **Scope:** Fix the 2 critical bugs, add "Generate All", write scripts to disk.
> **Difficulty:** 3/10 — all patterns exist, no new architecture.
> **Estimated time:** ~15 minutes.

---

## ARCHITECTURE CONTEXT

### What Exists (KEEP — it works)
- `ui/src/pages/BuildPlannerPage.tsx` — 1089-line React form. 6 sections: Project Basics, Build Rules, Features, Build Settings, Phase Assignments, Generate. All form state is local useState. Prompt assembly logic is correct.
- `server/routers/build_planner.py` — 64-line FastAPI router with one endpoint (`POST /api/build-planner/generate`). **This is the broken part.**
- Route: `/#/build-planner` — already registered in `ui/src/main.tsx`
- Nav button already in App.tsx header

### What's Broken (FIX)
1. **Backend uses API key credits** — `anthropic.Anthropic(api_key=...)` burns pay-per-use API credits. Must switch to Claude CLI subprocess using subscription auth.
2. **No "Generate All" flow** — User must click 3 buttons manually (PRD → Phase Split → Build Scripts) and wait between each. Should have one button that chains all 3.
3. **Scripts are just text** — Generated bash scripts live only in a textarea. They should be written to actual .sh files on disk.

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS v4, Radix UI |
| Backend | FastAPI (Python 3.11+) |
| AI Calls | Claude CLI subprocess (`claude -p --model sonnet`) — subscription auth |
| State | Local React useState (no persistence needed for v1) |

### Auth Pattern (CRITICAL — read this)

The current backend does this (WRONG):
```python
import anthropic
client = anthropic.Anthropic(api_key=api_key)
message = client.messages.create(model=request.model, ...)
```

Replace with Claude CLI subprocess (CORRECT):
```python
import subprocess
import json

def generate_with_cli(prompt: str, model: str = "sonnet") -> str:
    """Call Claude CLI using subscription auth. Zero API credits."""
    result = subprocess.run(
        ["claude", "-p", "--model", model, "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr}")
    return result.stdout.strip()
```

Key points:
- `claude -p` = print mode (non-interactive, returns result to stdout)
- `--model sonnet` = uses subscription, NOT API key
- Pass prompt via stdin (`input=prompt`) to avoid shell escaping issues
- `--output-format text` = plain text output (no JSON wrapper)
- Timeout 300s = 5 minutes max per generation step
- The user is on a $200/month Max plan — this costs $0 per call

### Existing Patterns to Follow
- **API functions**: `ui/src/lib/api.ts` has `fetchJSON<T>()` — use this instead of raw `fetch()`
- **Backend routers**: See `server/routers/` for FastAPI patterns (lazy imports, Pydantic models, HTTPException)
- **Process management**: `server/services/factory_controller.py` shows subprocess patterns

---

## PHASE 1: Fix Backend Auth [ROBOT]

### Task
Rewrite `server/routers/build_planner.py` to use Claude CLI subprocess instead of Anthropic API.

### Changes

**File: `server/routers/build_planner.py`** (REWRITE)

Replace the entire `_get_api_key()` function and `generate()` endpoint:

```python
"""
Build Planner Router — AI-powered prompt generation via Claude CLI.
Uses subscription auth (claude -p) — zero API credits.
"""
import asyncio
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/build-planner", tags=["build-planner"])


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "sonnet"


class GenerateAllRequest(BaseModel):
    """Request for chained generation: PRD → Phase Split → Build Scripts."""
    prd_prompt: str
    phase_split_prompt_template: str
    build_scripts_prompt_template: str
    model: str = "sonnet"
    project_dir: str | None = None  # Where to write .sh files


class ScriptWriteRequest(BaseModel):
    """Write generated script content to disk."""
    project_dir: str
    filename: str
    content: str


async def _run_claude_cli(prompt: str, model: str = "sonnet", timeout: int = 300) -> str:
    """Run Claude CLI in print mode using subscription auth."""
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


@router.post("/generate")
async def generate(request: GenerateRequest):
    """Process a single prompt through Claude CLI. Subscription auth."""
    try:
        result = await _run_claude_cli(request.prompt, request.model)
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Build planner generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-all")
async def generate_all(request: GenerateAllRequest):
    """Chain all 3 generation steps: PRD → Phase Split → Build Scripts.

    Each step feeds its output into the next step's prompt template.
    The templates should contain {previous_output} as a placeholder.
    """
    results = {}

    try:
        # Step 1: Generate PRD
        logger.info("Build Planner: Step 1/3 — Generating PRD...")
        prd_result = await _run_claude_cli(request.prd_prompt, request.model)
        results["prd"] = prd_result

        # Step 2: Generate Phase Split (inject PRD result)
        logger.info("Build Planner: Step 2/3 — Splitting into phases...")
        phase_prompt = request.phase_split_prompt_template.replace(
            "{previous_output}", prd_result
        )
        phase_result = await _run_claude_cli(phase_prompt, request.model)
        results["phase_split"] = phase_result

        # Step 3: Generate Build Scripts (inject phase split result)
        logger.info("Build Planner: Step 3/3 — Generating build scripts...")
        build_prompt = request.build_scripts_prompt_template.replace(
            "{previous_output}", phase_result
        )
        build_result = await _run_claude_cli(build_prompt, request.model)
        results["build_scripts"] = build_result

        # Step 4: Write scripts to disk if project_dir provided
        if request.project_dir:
            scripts_dir = Path(request.project_dir) / "scripts" / "build-planner"
            scripts_dir.mkdir(parents=True, exist_ok=True)

            # Write the raw build script output
            output_file = scripts_dir / "generated_output.md"
            output_file.write_text(build_result, encoding="utf-8")
            results["scripts_dir"] = str(scripts_dir)
            logger.info("Build Planner: Scripts written to %s", scripts_dir)

        return {"results": results, "steps_completed": 3}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Build planner generate-all failed at step: %s", e)
        # Return partial results so the user doesn't lose progress
        results["error"] = str(e)
        results["steps_completed"] = len([k for k in results if k not in ("error", "steps_completed")])
        raise HTTPException(status_code=500, detail={
            "message": str(e),
            "partial_results": results,
        })


@router.post("/write-script")
async def write_script(request: ScriptWriteRequest):
    """Write a generated script to disk."""
    try:
        scripts_dir = Path(request.project_dir) / "scripts" / "build-planner"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        filepath = scripts_dir / request.filename
        filepath.write_text(request.content, encoding="utf-8")

        # Make .sh files executable
        if request.filename.endswith(".sh"):
            filepath.chmod(0o755)

        return {"path": str(filepath), "written": True}
    except Exception as e:
        logger.error("Failed to write script: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
```

### Test Plan
1. [ROBOT] Start the backend (`start_ui.bat` or `python -m uvicorn server.main:app`)
2. [ROBOT] `curl -X POST http://localhost:8888/api/build-planner/generate -H "Content-Type: application/json" -d '{"prompt":"Say hello","model":"sonnet"}'` — should return result without API key
3. [ROBOT] Verify no `anthropic` import in the file (subscription only)
4. [ROBOT] Verify timeout handling: send a very long prompt, confirm 504 after timeout

---

## PHASE 2: Add "Generate All" Button to UI [ROBOT]

### Task
Add a "Generate All" button that chains PRD → Phase Split → Build Scripts in one click, showing progress for each step.

### Changes

**File: `ui/src/pages/BuildPlannerPage.tsx`**

Add these pieces:

1. **New state variables** (add near the other output state):
```typescript
const [generateAllLoading, setGenerateAllLoading] = useState(false)
const [generateAllStep, setGenerateAllStep] = useState(0) // 0=idle, 1=PRD, 2=phase, 3=scripts
const [generateAllError, setGenerateAllError] = useState<string | null>(null)
```

2. **New handler function** (add after `runBuildWithAI`):
```typescript
const runGenerateAll = async () => {
  setGenerateAllLoading(true)
  setGenerateAllStep(1)
  setGenerateAllError(null)

  try {
    // Step 1: Generate PRD prompt text
    generatePRD()

    // Step 1: Run PRD with AI
    const prdResult = await callGenerate(/* assembled PRD prompt */, model)
    setPrdAiResult(prdResult)
    setGenerateAllStep(2)

    // Step 2: Generate phase split prompt (using PRD result)
    // Assemble the phase split prompt with prdResult injected
    const phasePromptText = `Split this PRD into ${phaseCount} build phases...
${prdResult}
...`
    const phaseResult = await callGenerate(phasePromptText, model)
    setPhaseAiResult(phaseResult)
    setGenerateAllStep(3)

    // Step 3: Generate build scripts (using phase result)
    const buildPromptText = `Generate bash scripts for a phased Claude Code build...
${phaseResult}
...`
    const buildResult = await callGenerate(buildPromptText, model)
    setBuildAiResult(buildResult)
    setGenerateAllStep(0)

  } catch (err) {
    setGenerateAllError(err instanceof Error ? err.message : 'Generation failed')
    setGenerateAllStep(0)
  } finally {
    setGenerateAllLoading(false)
  }
}
```

3. **New "Generate All" button** — Add above the 3 individual buttons in the Generate section:
```tsx
{/* Generate All button */}
<button
  onClick={runGenerateAll}
  disabled={generateAllLoading}
  className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-purple-600 via-cyan-500 to-green-500 rounded-xl px-6 py-4 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 mb-4"
>
  {generateAllLoading ? (
    <>
      <Loader2 size={20} className="animate-spin" />
      Step {generateAllStep} of 3: {generateAllStep === 1 ? 'Generating PRD...' : generateAllStep === 2 ? 'Splitting phases...' : 'Creating scripts...'}
    </>
  ) : (
    <>
      <Rocket size={20} />
      Generate All (PRD → Phases → Scripts)
    </>
  )}
</button>

{generateAllError && (
  <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2 mb-4">
    {generateAllError}
  </div>
)}

<p className="text-xs text-zinc-600 text-center mb-4">— or generate individually —</p>
```

4. **Update `callGenerate` function** to use proper API pattern:
Replace the existing `callGenerate` with a version that uses `fetchJSON` from `@/lib/api` if available, or at minimum keep the same fetch but ensure it handles the subscription backend.

### Test Plan
1. [ROBOT] Fill out form with test data (app name, description, 1 rule block, 2 features)
2. [ROBOT] Click "Generate All" — verify progress indicator shows Step 1, 2, 3
3. [ROBOT] Verify all 3 output areas populate with AI results
4. [ROBOT] Verify individual buttons still work independently
5. [ROBOT] Test error handling: disconnect backend, verify error message appears
6. [ROBOT] `npm run build` — TypeScript clean, no errors
7. [ROBOT] `npm run lint` — ESLint clean

---

## PHASE 3: Write Scripts to Disk [ROBOT]

### Task
After "Generate All" completes, parse the build scripts output and write actual .sh files to a project directory.

### Changes

**File: `server/routers/build_planner.py`** — Already has `/write-script` endpoint from Phase 1.

**File: `ui/src/pages/BuildPlannerPage.tsx`** — Add a "Save Scripts" button below the build scripts output:

1. After build scripts AI result renders, show a "Save to Disk" button
2. Button calls `POST /api/build-planner/write-script` with each script
3. Show success message with the file path

```tsx
{buildAiResult && (
  <div className="mt-3 flex gap-2">
    <Button
      onClick={async () => {
        // Write the full output as a markdown file
        const res = await fetch(`${API_BASE}/api/build-planner/write-script`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_dir: '/path/to/project', // TODO: get from form or folder browser
            filename: 'build_scripts.md',
            content: buildAiResult,
          }),
        })
        if (res.ok) {
          // Show success toast
        }
      }}
      size="sm"
      className="gap-1 bg-green-600 text-white hover:bg-green-500"
    >
      <Download size={14} />
      Save Scripts to Disk
    </Button>
  </div>
)}
```

### Test Plan
1. [ROBOT] Complete a full "Generate All" flow
2. [ROBOT] Click "Save Scripts to Disk"
3. [ROBOT] Verify files written to `{project_dir}/scripts/build-planner/`
4. [ROBOT] Verify .sh files have execute permission (chmod 755)
5. [ROBOT] `npm run build` — clean
6. [ROBOT] `ruff check server/routers/build_planner.py` — clean

---

## WHAT'S NOT IN SCOPE (save for v2)

- Breaking the monolith into sub-components (it works fine as-is at 1089 lines)
- Save/load plans to database
- Build rule presets
- Phase-scoped instruction blocks
- Drag-and-drop reordering
- Build queue
- Live dashboard
- WebSocket streaming
- Template library

These are all v2/v3 features. The PRD at `docs/prd-build-planner-v2.md` has the full 8-phase plan for those.

---

## COMMIT MESSAGE
```
fix(build-planner): switch to subscription auth + add Generate All button

- Replace Anthropic API key calls with Claude CLI subprocess (zero credits)
- Add "Generate All" button that chains PRD → Phase Split → Build Scripts
- Add /write-script endpoint to save generated scripts to disk
- Add /generate-all endpoint for chained generation
```
