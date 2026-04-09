"""
Pipeline Chat Router
====================

Handles the interactive PRD pipeline stages 0-2 (conversation with the user),
then fires the completed context packet into the Activepieces pipeline for
stages 3-10.

Stages:
  - Stage 0: Technical Foundation (5 platform/stack questions)
  - Stage 1: Idea Capture (raw brain-dump of the app idea)
  - Stage 2: Gap Analysis (fill missing pieces via targeted questions)

After Stage 2 completes, the accumulated context packet is POSTed to the
Activepieces webhook for automated processing through stages 3-10.

Session state is held in-memory (dict) — sufficient for MVP since this is
single-user on localhost.
"""

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .pipeline_proxy import _call_claude_sdk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline-chat", tags=["pipeline-chat"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Activepieces webhook URL — replace PLACEHOLDER after publishing the flow
ACTIVEPIECES_WEBHOOK_URL = os.environ.get(
    "ACTIVEPIECES_WEBHOOK_URL",
    "http://localhost:8080/api/v1/webhooks/qmWm4lyxgWnZZDVY1ikNt",
)

# Model for conversational stages — Sonnet is fast enough for back-and-forth
CHAT_MODEL = "claude-sonnet-4-6"

# Generous timeout: these are interactive calls, but rate-limit retries can add up
SDK_TIMEOUT_SECONDS = 300

# Max turns for the SDK client (1 user message → 1 assistant reply)
SDK_MAX_TURNS = 2

# ---------------------------------------------------------------------------
# Stage Skill Files — loaded from disk on every call so edits are immediate
# ---------------------------------------------------------------------------

# Path to the skills-complete directory containing SKILL.md files per stage.
# Resolved relative to this file: server/routers/pipeline_chat.py
#   .parent = server/routers/
#   .parent = server/
#   .parent = project root (where docs/ lives)
SKILLS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "docs" / "page-prds" / "prd-maker" / "skills"
)

STAGE_FOLDER_NAMES: dict[int, str] = {
    0: "stage-00-technical-foundation",
    1: "stage-01-idea-capture",
    2: "stage-02-gap-analysis",
    3: "stage-03-agent-os-structuring",
    4: "stage-04-mechanism-extraction",
    5: "stage-05-seven-question-scaffolding",
    6: "stage-06-layout-mockups-style",
    7: "stage-07-phase-sequencing",
    8: "stage-08-protocol-injection",
    9: "stage-09-verification-agent-setup",
    10: "stage-10-output-generator",
}


def load_stage_prompt(stage: int) -> str:
    """Load the SKILL.md content for a given stage from disk.

    Reads fresh on every call so edits to skill files are picked up
    without restarting the server.

    Raises:
        ValueError: If the stage number is not in STAGE_FOLDER_NAMES.
        FileNotFoundError: If the SKILL.md file does not exist on disk.
    """
    folder = STAGE_FOLDER_NAMES.get(stage)
    if folder is None:
        raise ValueError(f"Unknown stage: {stage}")
    skill_path = SKILLS_DIR / folder / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")
    return skill_path.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# In-Memory Session Store
# ---------------------------------------------------------------------------

sessions: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class StartResponse(BaseModel):
    """Response from POST /start — new session with Claude's opening message."""
    session_id: str
    current_stage: int
    assistant_message: str


class MessageRequest(BaseModel):
    """Request body for POST /message."""
    session_id: str
    message: str


class MessageResponse(BaseModel):
    """Response from POST /message — Claude's reply plus stage metadata."""
    session_id: str
    current_stage: int | str  # int for 0-2, or "pipeline_triggered"
    assistant_message: str
    stage_advanced: bool
    stage_output: Optional[dict] = None
    pipeline_triggered: bool


class StatusResponse(BaseModel):
    """Response from GET /status/{session_id}."""
    session_id: str
    current_stage: int | str
    conversation_length: int
    pipeline_triggered: bool
    pipeline_flow_run_id: Optional[str] = None
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_stage_complete(response_text: str) -> tuple[bool, dict | None]:
    """Check if Claude's response contains a stage completion JSON block.

    Looks for fenced ```json blocks with ``"stage_complete": true``.
    Returns (is_complete, parsed_data) — data is None when not complete.
    """
    json_matches = re.findall(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
    for match in json_matches:
        try:
            data = json.loads(match)
            if data.get("stage_complete") is True:
                return True, data
        except json.JSONDecodeError:
            continue
    return False, None


def _build_user_message_with_history(
    conversation_history: list[dict],
    new_user_message: str | None = None,
) -> str:
    """Format conversation history into a single user-message string.

    The Claude SDK's ``_call_claude_sdk`` accepts one system_prompt and one
    user_message. To simulate multi-turn conversation we serialize the full
    history into the user message, clearly delimiting each turn so Claude can
    follow the thread.
    """
    parts: list[str] = []

    for msg in conversation_history:
        role_label = "USER" if msg["role"] == "user" else "ASSISTANT"
        parts.append(f"[{role_label}]\n{msg['content']}")

    if new_user_message is not None:
        parts.append(f"[USER]\n{new_user_message}")

    # Instruct Claude to continue the conversation naturally
    parts.append(
        "\n---\nContinue the conversation as the assistant. "
        "Respond naturally to the latest user message above."
    )

    return "\n\n".join(parts)


def _build_stage_context_prefix(session: dict) -> str:
    """Build a context prefix summarizing completed stages.

    When advancing to a new stage, Claude needs to know what was decided
    in prior stages so it can ask informed follow-up questions.
    """
    stage = session["current_stage"]
    if stage == 0:
        return ""

    parts = ["Here is the context gathered from previous pipeline stages:\n"]
    for i in range(stage):
        stage_data = session["context_packet"].get(f"stage_{i}")
        if stage_data:
            parts.append(f"--- Stage {i} Output ---")
            parts.append(json.dumps(stage_data, indent=2))
            parts.append("")

    return "\n".join(parts)


def _check_force_advance(message: str) -> bool:
    """Check if user wants to force-advance past the current stage.

    Matches phrases like 'I'm done', 'move on', 'let's go', 'skip', 'next stage',
    'that's enough', 'good enough', 'let's move on', etc.
    Returns True if the user wants to skip ahead.
    """
    lower = message.strip().lower()
    # Exact short phrases
    force_phrases = [
        "i'm done", "im done", "i am done",
        "move on", "lets move on", "let's move on",
        "lets go", "let's go",
        "skip", "next", "next stage",
        "that's enough", "thats enough",
        "good enough", "close enough",
        "just go", "just run it", "run it",
        "send it", "ship it", "fire it",
        "done", "enough", "move forward",
        "proceed", "continue", "advance",
    ]
    for phrase in force_phrases:
        if phrase in lower:
            return True
    return False


def _get_session_or_404(session_id: str) -> dict:
    """Retrieve a session by ID or raise 404."""
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found")
    return session


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/start", response_model=StartResponse)
async def start_session():
    """Create a new pipeline chat session and return Claude's opening message.

    Initializes the context packet, loads the Stage 0 system prompt, and
    calls Claude to produce an opening greeting that walks the user through
    the 5 foundation questions.
    """
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    session: dict = {
        "session_id": session_id,
        "current_stage": 0,
        "context_packet": {
            "metadata": {
                "session_id": session_id,
                "created_at": now,
                "pipeline_version": "1.0",
            },
            "stage_0": None,
            "stage_1": None,
            "stage_2": None,
        },
        "conversation_history": [],
        "created_at": now,
        "pipeline_triggered": False,
        "pipeline_flow_run_id": None,
    }

    # Get Stage 0's system prompt and call Claude for the opening message
    system_prompt = load_stage_prompt(0)
    opening_prompt = (
        "This is the very start of the conversation. "
        "The user just opened the PRD pipeline. "
        "Greet them briefly and begin Stage 0 by asking the Technical Foundation questions."
    )

    t0 = time.time()
    try:
        assistant_text = await _call_claude_sdk(
            system_prompt=system_prompt,
            user_message=opening_prompt,
            model=CHAT_MODEL,
            max_turns=SDK_MAX_TURNS,
            timeout=SDK_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.exception("Failed to generate opening message for session %s", session_id)
        raise HTTPException(
            status_code=502,
            detail=f"Claude SDK call failed: {exc}",
        )

    duration = time.time() - t0
    logger.info(
        "[pipeline-chat] Session %s started — opening message in %.1fs",
        session_id, duration,
    )

    # Record the assistant's opening in the conversation history
    session["conversation_history"].append({
        "role": "assistant",
        "content": assistant_text,
    })

    sessions[session_id] = session

    return StartResponse(
        session_id=session_id,
        current_stage=0,
        assistant_message=assistant_text,
    )


@router.post("/message", response_model=MessageResponse)
async def send_message(body: MessageRequest):
    """Send a user message and get Claude's response for the current stage.

    Core conversation loop:
    1. Append user message to history
    2. Call Claude with the current stage's system prompt + full history
    3. Check if Claude signaled stage completion (JSON with stage_complete: true)
    4. If advancing: save stage output, move to next stage, reset conversation
       history (but inject prior context)
    5. If Stage 2 completes: fire context packet to Activepieces webhook
    """
    session = _get_session_or_404(body.session_id)

    # Guard: pipeline already triggered — no more messages accepted
    if session["pipeline_triggered"]:
        raise HTTPException(
            status_code=409,
            detail="Pipeline already triggered for this session. Start a new session.",
        )

    current_stage = session["current_stage"]

    # Append the user's message
    session["conversation_history"].append({
        "role": "user",
        "content": body.message,
    })

    # ---------------------------------------------------------------
    # FORCE-ADVANCE: If user says "I'm done" / "move on" / etc.,
    # skip Claude and advance to the next stage immediately.
    # Builds a best-effort stage output from whatever we have so far.
    # ---------------------------------------------------------------
    if _check_force_advance(body.message):
        logger.info(
            "[pipeline-chat] Session %s: user force-advancing from stage %d",
            body.session_id, current_stage,
        )

        # Build a minimal stage output from conversation so far
        convo_text = "\n".join(
            m["content"] for m in session["conversation_history"] if m["role"] == "user"
        )
        force_output = {
            "stage_complete": True,
            "force_advanced": True,
            "raw_conversation": convo_text,
        }

        # Store it
        session["context_packet"][f"stage_{current_stage}"] = force_output

        if current_stage < 2:
            next_stage = current_stage + 1
            session["current_stage"] = next_stage
            session["conversation_history"] = []

            # Generate transition greeting for next stage
            next_system = load_stage_prompt(next_stage)
            next_ctx = _build_stage_context_prefix(session)
            if next_ctx:
                next_system = f"{next_ctx}\n\n{next_system}"

            try:
                transition_text = await _call_claude_sdk(
                    system_prompt=next_system,
                    user_message=(
                        f"The user just force-advanced from Stage {current_stage}. "
                        f"They said: '{body.message}'. Begin Stage {next_stage} now. "
                        f"Work with whatever context is available from previous stages."
                    ),
                    model=CHAT_MODEL,
                    max_turns=SDK_MAX_TURNS,
                    timeout=SDK_TIMEOUT_SECONDS,
                )
            except Exception:
                transition_text = f"Got it — moving to Stage {next_stage}. Let's keep going."

            session["conversation_history"].append({
                "role": "assistant",
                "content": transition_text,
            })

            return MessageResponse(
                session_id=body.session_id,
                current_stage=next_stage,
                assistant_message=transition_text,
                stage_advanced=True,
                stage_output=force_output,
                pipeline_triggered=False,
            )
        else:
            # Force-advancing from Stage 2 — fire the pipeline
            session["current_stage"] = "pipeline_triggered"
            session["pipeline_triggered"] = True

            logger.info(
                "[pipeline-chat] Session %s: force-advanced Stage 2 — firing pipeline",
                body.session_id,
            )
            await _fire_activepieces_pipeline(session)

            return MessageResponse(
                session_id=body.session_id,
                current_stage="pipeline_triggered",
                assistant_message="Got it — sending everything to the pipeline now. Stages 3-10 will run automatically.",
                stage_advanced=True,
                stage_output=force_output,
                pipeline_triggered=True,
            )

    # Build the system prompt with prior-stage context
    base_system_prompt = load_stage_prompt(current_stage)
    context_prefix = _build_stage_context_prefix(session)
    if context_prefix:
        system_prompt = f"{context_prefix}\n\n{base_system_prompt}"
    else:
        system_prompt = base_system_prompt

    # Build the serialized conversation as the user_message
    user_message = _build_user_message_with_history(session["conversation_history"])

    t0 = time.time()
    try:
        assistant_text = await _call_claude_sdk(
            system_prompt=system_prompt,
            user_message=user_message,
            model=CHAT_MODEL,
            max_turns=SDK_MAX_TURNS,
            timeout=SDK_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        # Remove the user message we just appended so the session stays consistent
        session["conversation_history"].pop()
        logger.exception(
            "[pipeline-chat] SDK call failed for session %s stage %d",
            body.session_id, current_stage,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Claude SDK call failed: {exc}",
        )

    duration = time.time() - t0
    logger.info(
        "[pipeline-chat] Session %s stage %d reply in %.1fs (%d chars)",
        body.session_id, current_stage, duration, len(assistant_text),
    )

    # Record assistant reply
    session["conversation_history"].append({
        "role": "assistant",
        "content": assistant_text,
    })

    # Check for stage advancement
    stage_advanced = False
    stage_output: dict | None = None
    pipeline_triggered = False

    is_complete, completion_data = check_stage_complete(assistant_text)

    if is_complete and completion_data is not None:
        stage_advanced = True
        stage_output = completion_data

        # Store the stage output in the context packet
        session["context_packet"][f"stage_{current_stage}"] = completion_data

        if current_stage < 2:
            # Advance to next stage — reset conversation but keep context
            next_stage = current_stage + 1
            session["current_stage"] = next_stage
            session["conversation_history"] = []

            logger.info(
                "[pipeline-chat] Session %s advanced: stage %d → %d",
                body.session_id, current_stage, next_stage,
            )

            # Generate an opening message for the next stage so the user
            # sees a smooth transition without needing to send another message
            next_system_prompt = load_stage_prompt(next_stage)
            next_context = _build_stage_context_prefix(session)
            if next_context:
                next_system_prompt = f"{next_context}\n\n{next_system_prompt}"

            transition_prompt = (
                f"Stage {current_stage} just completed. The user is now entering Stage {next_stage}. "
                f"Acknowledge the transition briefly and begin Stage {next_stage}."
            )

            try:
                transition_text = await _call_claude_sdk(
                    system_prompt=next_system_prompt,
                    user_message=transition_prompt,
                    model=CHAT_MODEL,
                    max_turns=SDK_MAX_TURNS,
                    timeout=SDK_TIMEOUT_SECONDS,
                )
                # Append the completion message AND the transition to the response
                assistant_text = f"{assistant_text}\n\n---\n\n{transition_text}"
                session["conversation_history"].append({
                    "role": "assistant",
                    "content": transition_text,
                })
            except Exception as exc:
                # Non-fatal: the stage advanced, we just couldn't get the transition greeting
                logger.warning(
                    "[pipeline-chat] Transition greeting failed for session %s stage %d: %s",
                    body.session_id, next_stage, exc,
                )

        else:
            # Stage 2 completed — fire the pipeline
            session["current_stage"] = "pipeline_triggered"
            session["pipeline_triggered"] = True
            pipeline_triggered = True

            logger.info(
                "[pipeline-chat] Session %s: Stage 2 complete — firing Activepieces pipeline",
                body.session_id,
            )

            await _fire_activepieces_pipeline(session)

    return MessageResponse(
        session_id=body.session_id,
        current_stage=session["current_stage"],
        assistant_message=assistant_text,
        stage_advanced=stage_advanced,
        stage_output=stage_output,
        pipeline_triggered=pipeline_triggered,
    )


class BulkSubmitRequest(BaseModel):
    """Request body for POST /bulk-submit — skip stages 0-2 entirely."""
    tech_stack: Optional[dict] = None
    app_idea: str
    additional_context: Optional[str] = None


class BulkSubmitResponse(BaseModel):
    """Response from POST /bulk-submit."""
    session_id: str
    pipeline_triggered: bool
    message: str


@router.post("/bulk-submit", response_model=BulkSubmitResponse)
async def bulk_submit(body: BulkSubmitRequest):
    """Skip the interactive stages entirely — dump everything in one shot.

    Use this when you've already thought through the idea and just want to
    feed it directly into the pipeline without back-and-forth.

    The handler builds a context packet from your input, then fires it
    straight into Activepieces for stages 3-10.
    """
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Build default tech stack if not provided
    tech_stack = body.tech_stack or {
        "framework": "React + Vite",
        "database": "PostgreSQL",
        "auth_provider": "undecided",
        "hosting": "self-hosted",
    }

    context_packet = {
        "metadata": {
            "session_id": session_id,
            "created_at": now,
            "pipeline_version": "1.0",
            "bulk_submit": True,
        },
        "stage_0": {
            "stage_complete": True,
            "platform_profile": {"boilerplate_id": "custom", "boilerplate_name": "User Provided"},
            "tech_stack": tech_stack,
            "checklist_rule_ids": [],
        },
        "stage_1": {
            "stage_complete": True,
            "raw_input": body.app_idea,
            "input_format": "typed",
            "word_count": len(body.app_idea.split()),
            "char_count": len(body.app_idea),
            "explicit_corrections": [],
        },
        "stage_2": {
            "stage_complete": True,
            "combined_raw": body.app_idea + ("\n\n" + body.additional_context if body.additional_context else ""),
            "archetype_matches": [],
            "mechanisms_identified": [],
            "scope_contract": "User-provided bulk submission — no interactive gap analysis performed.",
        },
    }

    session = {
        "session_id": session_id,
        "current_stage": "pipeline_triggered",
        "context_packet": context_packet,
        "conversation_history": [],
        "created_at": now,
        "pipeline_triggered": True,
        "pipeline_flow_run_id": None,
    }
    sessions[session_id] = session

    logger.info(
        "[pipeline-chat] Bulk submit session %s: %d words, firing pipeline",
        session_id, len(body.app_idea.split()),
    )

    await _fire_activepieces_pipeline(session)

    return BulkSubmitResponse(
        session_id=session_id,
        pipeline_triggered=True,
        message=f"Submitted {len(body.app_idea.split())} words directly to the pipeline. Stages 3-10 running.",
    )


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """Return current state of a pipeline chat session."""
    session = _get_session_or_404(session_id)

    return StatusResponse(
        session_id=session_id,
        current_stage=session["current_stage"],
        conversation_length=len(session["conversation_history"]),
        pipeline_triggered=session["pipeline_triggered"],
        pipeline_flow_run_id=session.get("pipeline_flow_run_id"),
        created_at=session["created_at"],
    )


@router.get("/skills")
async def list_skills():
    """List all stage skill files and their status (exists, path, size).

    Useful for inspecting which SKILL.md files are available on disk and
    verifying that the skills directory is correctly resolved.
    """
    results = {}
    for stage, folder in STAGE_FOLDER_NAMES.items():
        skill_path = SKILLS_DIR / folder / "SKILL.md"
        exists = skill_path.exists()
        results[f"stage_{stage}"] = {
            "folder": folder,
            "path": str(skill_path),
            "exists": exists,
            "size_bytes": skill_path.stat().st_size if exists else 0,
        }
    return {"skills_dir": str(SKILLS_DIR), "stages": results}


# ---------------------------------------------------------------------------
# Activepieces Integration
# ---------------------------------------------------------------------------

async def _fire_activepieces_pipeline(session: dict) -> None:
    """POST the context packet to the Activepieces webhook.

    If the webhook URL is still the placeholder, we log the packet and skip
    the HTTP call — this lets development proceed before the flow is published.
    """
    context_packet = session["context_packet"]
    session_id = session["session_id"]

    # Always log the full packet for debugging / manual recovery
    logger.info(
        "[pipeline-chat] Context packet for session %s:\n%s",
        session_id,
        json.dumps(context_packet, indent=2),
    )

    if "PLACEHOLDER" in ACTIVEPIECES_WEBHOOK_URL:
        logger.warning(
            "[pipeline-chat] Webhook URL contains PLACEHOLDER — skipping HTTP POST. "
            "Set ACTIVEPIECES_WEBHOOK_URL env var to the real URL after publishing the flow."
        )
        return

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ACTIVEPIECES_WEBHOOK_URL,
                json=context_packet,
            )
            resp.raise_for_status()

        # Activepieces returns the flow run ID in the response
        try:
            result = resp.json()
            flow_run_id = result.get("id") or result.get("flowRunId")
            if flow_run_id:
                session["pipeline_flow_run_id"] = flow_run_id
                logger.info(
                    "[pipeline-chat] Activepieces flow run started: %s",
                    flow_run_id,
                )
        except Exception:
            # Response might not be JSON — that's fine
            logger.info(
                "[pipeline-chat] Activepieces webhook returned status %d",
                resp.status_code,
            )

    except httpx.HTTPStatusError as exc:
        logger.error(
            "[pipeline-chat] Activepieces webhook returned %d: %s",
            exc.response.status_code,
            exc.response.text[:500],
        )
    except Exception as exc:
        logger.error(
            "[pipeline-chat] Failed to POST to Activepieces webhook: %s", exc,
        )
