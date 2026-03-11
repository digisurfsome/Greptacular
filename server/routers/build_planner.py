"""
Build Planner Router
====================

REST endpoint for AI-powered prompt generation in the Build Planner page.
Takes assembled prompts and processes them through Claude Sonnet.
"""

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/build-planner", tags=["build-planner"])


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "claude-sonnet-4-6-20250514"


def _get_api_key() -> str | None:
    """Retrieve the Anthropic API key from registry settings or environment."""
    try:
        from registry import get_effective_sdk_env
        sdk_env = get_effective_sdk_env()
        key = sdk_env.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("ANTHROPIC_API_KEY")


@router.post("/generate")
async def generate(request: GenerateRequest):
    """Process a prompt through Claude and return the result."""
    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="No Anthropic API key configured. Set ANTHROPIC_API_KEY in your environment or registry settings.",
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=request.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": request.prompt}],
        )
        return {"result": message.content[0].text}
    except anthropic.APIError as e:
        logger.error("Anthropic API error: %s", e)
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {e}")
    except Exception as e:
        logger.error("Build planner generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
