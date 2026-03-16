"""
Ingestion Sequence Generator API — REST endpoints for building
channel-specific metaprogram detection funnels.

Endpoints:
    GET  /api/ingestion-sequences/channels       — List available channels
    GET  /api/ingestion-sequences/metaprograms    — List available metaprograms + questions
    GET  /api/ingestion-sequences/authenticity     — Get authenticity rules
    POST /api/ingestion-sequences/generate         — Generate a full decision tree
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.ingestion_sequence_generator import (
    DOMINANCE_LEVELS,
    Channel,
    IngestionSequenceGenerator,
    generate_coach_prompt,
)

router = APIRouter(prefix="/api/ingestion-sequences", tags=["ingestion-sequences"])

# Singleton generator
_generator = IngestionSequenceGenerator()


# ═══════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    channel: str = Field(
        ...,
        description="Platform: instagram, email, landing_page, shorts, x",
    )
    topic: str = Field(
        ...,
        description="What you're promoting (e.g., 'keto app', 'vibe coding course')",
    )
    primary_meta: str = Field(
        default="motivation",
        description="First metaprogram to detect (motivation, reference, work_style)",
    )
    secondary_meta: str = Field(
        default="reference",
        description="Second metaprogram to detect",
    )
    cta: str = Field(
        default="check it out",
        description="The action you want them to take",
    )
    tertiary_meta: Optional[str] = Field(
        default="work_style",
        description="Optional third metaprogram to detect (set to null to skip)",
    )
    question_variant: Optional[int] = Field(
        default=None,
        description="Specific question variant index (null = random)",
    )


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/channels")
async def list_channels():
    """List available channels with their constraints and detection flows."""
    return {"channels": _generator.list_channels()}


@router.get("/metaprograms")
async def list_metaprograms():
    """List available metaprograms and their zero-pressure question variants."""
    return {"metaprograms": _generator.list_metaprograms()}


@router.get("/authenticity")
async def get_authenticity_rules():
    """Get the authenticity rules that govern question design."""
    return _generator.get_authenticity_rules()


@router.post("/generate")
async def generate_sequence(request: GenerateRequest):
    """
    Generate a complete ingestion sequence (decision tree) for a channel + topic.

    Returns the full tree with:
    - Hook post (the initial question that detects meta #1)
    - Branching replies (each branch detects meta #2)
    - Fully adapted CTAs at each leaf (personalized per metaprogram combo)
    - Authenticity notes explaining why each node is genuine
    - Channel-specific implementation notes

    The tree can be 2-deep (primary + secondary) or 3-deep (+ tertiary).
    2-deep = 4 endpoint CTAs. 3-deep = 8 endpoint CTAs.
    """
    # Validate channel
    valid_channels = [c.value for c in Channel]
    if request.channel not in valid_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel '{request.channel}'. Valid: {valid_channels}",
        )

    # Validate metaprograms
    available_metas = list(_generator.questions.keys())
    for meta_name, meta_value in [
        ("primary_meta", request.primary_meta),
        ("secondary_meta", request.secondary_meta),
    ]:
        if meta_value not in available_metas:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {meta_name} '{meta_value}'. Available: {available_metas}",
            )

    if request.tertiary_meta and request.tertiary_meta not in available_metas:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tertiary_meta '{request.tertiary_meta}'. Available: {available_metas}",
        )

    try:
        sequence = _generator.generate(
            channel=request.channel,
            topic=request.topic,
            primary_meta=request.primary_meta,
            secondary_meta=request.secondary_meta,
            cta=request.cta,
            tertiary_meta=request.tertiary_meta,
            question_variant=request.question_variant,
        )
        return sequence.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# Dominance Spectrum & Real-Time Coach
# ═══════════════════════════════════════════════════════════════

@router.get("/dominance-levels")
async def get_dominance_levels():
    """
    Get the 4-level dominance spectrum.

    Most people aren't pure one pole or the other. They're dominant one
    way with a secondary lean. The 4 levels determine HOW you frame
    your message — specifically, what you LEAD with and what you FOLLOW with.
    """
    return {"levels": DOMINANCE_LEVELS}


class CoachRequest(BaseModel):
    metaprogram: str = Field(
        ...,
        description="Which metaprogram was detected (motivation, reference, work_style)",
    )
    detected_pole: str = Field(
        ...,
        description="Detected pole (toward, away_from, internal, external, options, procedures)",
    )
    dominance_level: int = Field(
        ...,
        ge=1,
        le=4,
        description="1=pure primary, 2=dominant primary, 3=dominant secondary, 4=pure secondary",
    )
    topic: str = Field(
        ...,
        description="What you're talking about",
    )


@router.post("/coach")
async def get_coach_prompt(request: CoachRequest):
    """
    Get a real-time coaching prompt for a detected metaprogram.

    This is what the earpiece would tell you during a live call:
    short, direct, actionable. "Lead with X, follow with Y. Say this."

    Use this to train yourself to speak in metaprogram frames in real time.
    After a few weeks of practice, your brain starts doing it automatically.
    """
    prompt = generate_coach_prompt(
        metaprogram=request.metaprogram,
        detected_pole=request.detected_pole,
        dominance_level=request.dominance_level,
        topic=request.topic,
    )
    return {
        "detected": prompt.detected,
        "dominance_level": prompt.dominance_level,
        "instruction": prompt.instruction,
        "example_phrase": prompt.example_phrase,
        "lead_with": prompt.lead_with,
        "follow_with": prompt.follow_with,
    }
