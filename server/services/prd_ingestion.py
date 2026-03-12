"""PRD Ingestion Service — upload PRD documents, extract structured steps.

Alternative entry point to YouTube ingestion. User uploads a PRD (markdown/text),
Claude extracts structured steps, and the same blueprint engine processes them.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..models.tool_factory import PRDExtractionResult, PRDUpload

logger = logging.getLogger(__name__)

# Minimum content length to be a useful PRD
MIN_PRD_LENGTH = 50

PRD_EXTRACTION_SYSTEM = (
    "You are a PRD analysis specialist. You extract structured implementation "
    "plans from Product Requirements Documents. Return ONLY valid JSON, "
    "no markdown fences, no explanation."
)

PRD_EXTRACTION_USER_TEMPLATE = """You are analyzing a Product Requirements Document (PRD). Extract a structured implementation plan.

PRD Content:
{content}

User Context (optional):
{user_context}

Return a JSON object with:
{{
  "project_name": "short name for this project",
  "project_description": "one paragraph summary",
  "niche": "industry/domain",
  "tags": ["tag1", "tag2"],
  "steps": [
    {{
      "order": 1,
      "title": "Step title",
      "description": "What this step does",
      "prompt": "Detailed prompt for executing this step",
      "expectedOutput": "What the step should produce",
      "notes": "Implementation notes",
      "model": "sonnet"
    }}
  ]
}}

Rules:
- Extract 5-20 actionable steps
- Each step should be independently executable
- Order steps by dependency (earlier steps feed later ones)
- Use "opus" model only for steps requiring deep reasoning
- Use "sonnet" for everything else"""


def _prd_uploads_dir() -> Path:
    return Path.home() / ".autoforge" / "prd_uploads"


# ---------------------------------------------------------------------------
# [ROBOT] Functions
# ---------------------------------------------------------------------------

def validate_prd_content(content: str) -> bool:
    """[ROBOT] Check minimum length, not empty, not binary."""
    if not content or not content.strip():
        return False
    if len(content.strip()) < MIN_PRD_LENGTH:
        return False
    # Check for binary content (high ratio of non-printable chars)
    non_printable = sum(1 for c in content[:1000] if not c.isprintable() and c not in "\n\r\t")
    if non_printable > len(content[:1000]) * 0.1:
        return False
    return True


def normalize_prd_steps(raw_steps: list[dict]) -> list[dict]:
    """[ROBOT] Convert Claude output to same format as YT Lab steps.

    Ensures each step has: order, title, description, prompt, expectedOutput, notes, model, id.
    """
    normalized = []
    for i, step in enumerate(raw_steps):
        normalized.append({
            "id": step.get("id", uuid.uuid4().hex[:8]),
            "order": step.get("order", i + 1),
            "title": step.get("title", f"Step {i + 1}"),
            "description": step.get("description", ""),
            "prompt": step.get("prompt", ""),
            "expectedOutput": step.get("expectedOutput", step.get("expected_output", "")),
            "notes": step.get("notes", ""),
            "model": step.get("model", "sonnet"),
        })
    return normalized


def save_prd_upload(filename: str, content: str) -> PRDUpload:
    """[ROBOT] Persist PRD to ~/.autoforge/prd_uploads/."""
    uploads_dir = _prd_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    prd_id = f"prd_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # Save the raw content
    file_path = uploads_dir / f"{prd_id}.md"
    file_path.write_text(content, encoding="utf-8")

    # Save metadata
    meta_path = uploads_dir / f"{prd_id}.meta.json"
    meta = {
        "prd_id": prd_id,
        "filename": filename,
        "uploaded_at": now,
        "content_length": len(content),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    logger.info("Saved PRD upload: %s (%d chars)", prd_id, len(content))

    return PRDUpload(
        prd_id=prd_id,
        filename=filename,
        content=content,
        uploaded_at=now,
    )


# ---------------------------------------------------------------------------
# [AGENT] PRD Step Extraction
# ---------------------------------------------------------------------------

async def extract_steps_from_prd(
    content: str,
    user_context: str = "",
) -> PRDExtractionResult:
    """[AGENT] Claude reads PRD, outputs structured steps.

    Uses Claude Sonnet for cost efficiency. Includes retry logic.
    """
    from ..services.yt_processor import YTProcessor

    if not validate_prd_content(content):
        raise ValueError("PRD content is too short or invalid")

    user_message = PRD_EXTRACTION_USER_TEMPLATE.format(
        content=content[:50000],  # Cap at 50k chars
        user_context=user_context or "None provided",
    )

    processor = YTProcessor(model="claude-sonnet-4-6")
    start_time = time.time()

    raw_text = ""
    try:
        raw_text = await processor._call_via_sdk(
            PRD_EXTRACTION_SYSTEM,
            user_message,
            "claude-sonnet-4-6",
            timeout=120,
        )
    except Exception as sdk_err:
        logger.warning("SDK call failed for PRD extraction: %s, trying API", sdk_err)
        try:
            raw_text = await processor._call_via_api(
                PRD_EXTRACTION_SYSTEM,
                user_message,
                "claude-sonnet-4-6",
            )
        except Exception as api_err:
            raise RuntimeError(f"PRD extraction failed: SDK={sdk_err}, API={api_err}")

    elapsed = time.time() - start_time

    if not raw_text.strip():
        raise ValueError("Claude returned empty response for PRD extraction")

    # Parse JSON response
    try:
        parsed = processor._parse_ai_response(raw_text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Could not parse PRD extraction response: {e}")

    # Normalize steps
    raw_steps = parsed.get("steps", [])
    if not raw_steps:
        raise ValueError("No steps extracted from PRD")

    normalized_steps = normalize_prd_steps(raw_steps)

    return PRDExtractionResult(
        project_name=parsed.get("project_name", "Untitled PRD"),
        project_description=parsed.get("project_description", ""),
        niche=parsed.get("niche", ""),
        tags=parsed.get("tags", []),
        steps=normalized_steps,
        extraction_model="claude-sonnet-4-6",
        extraction_time=round(elapsed, 2),
    )
