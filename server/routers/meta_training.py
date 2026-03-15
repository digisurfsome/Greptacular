"""
Meta Training API — upload, transcribe, extract, write.

Upload anything → transcribe → extract metaprogram training data →
use it to generate adapted copy through the writing engine.

Endpoints:
    POST /api/meta-training/ingest/url         — Ingest YouTube URL
    POST /api/meta-training/ingest/upload       — Upload audio/video/text file
    POST /api/meta-training/ingest/text         — Paste raw text
    GET  /api/meta-training/library             — View training library stats
    GET  /api/meta-training/library/examples    — Get examples (filterable)
    GET  /api/meta-training/library/patterns    — Get patterns (filterable)
    DELETE /api/meta-training/library           — Clear training library

    POST /api/meta-training/write/generate      — Generate fresh copy for a profile
    POST /api/meta-training/write/rewrite       — Rewrite existing copy for a profile
    POST /api/meta-training/write/coach         — Get real-time coaching prompt
    POST /api/meta-training/write/all-combos    — Generate copy for every combo

    GET  /api/meta-training/transcripts         — List saved transcripts
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from server.services.meta_training_ingestor import (
    AUDIO_EXTENSIONS,
    TRANSCRIPTS_DIR,
    TrainingLibrary,
    VIDEO_EXTENSIONS,
    TEXT_EXTENSIONS,
    ingest_source,
)
from server.services.meta_writing_engine import (
    WritingRequest,
    generate_all_combos,
    generate_copy,
)

router = APIRouter(prefix="/api/meta-training", tags=["meta-training"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# INGEST ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class IngestURLRequest(BaseModel):
    url: str = Field(..., description="YouTube URL to transcribe and ingest")


@router.post("/ingest/url")
async def ingest_url(request: IngestURLRequest):
    """
    Ingest a YouTube URL.

    Fetches the transcript (free, no API key needed), extracts metaprogram
    training data using Claude, and adds it to the training library.
    """
    try:
        result = await ingest_source(source=request.url, source_type="youtube")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)):
    """
    Upload an audio, video, or text file for transcription and training extraction.

    Supported formats:
    - Audio: .mp3, .wav, .m4a, .ogg, .flac, .aac, .wma
    - Video: .mp4, .mov, .webm, .mkv, .avi, .wmv, .flv
    - Text: .txt, .md, .srt, .vtt, .json, .csv

    Audio/video files are transcribed using Whisper (OpenAI API or local).
    Text files are ingested directly.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = Path(file.filename).suffix.lower()
    allowed = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TEXT_EXTENSIONS
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {sorted(allowed)}",
        )

    # Check file size (100MB max for audio/video, 10MB for text)
    content = await file.read()
    max_size = 100 * 1024 * 1024 if ext in (AUDIO_EXTENSIONS | VIDEO_EXTENSIONS) else 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {max_size // (1024*1024)}MB",
        )

    try:
        result = await ingest_source(
            source="",
            uploaded_content=content,
            uploaded_filename=file.filename,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=50, description="Raw text to ingest (min 50 chars)")
    source_name: str = Field(default="pasted_text", description="Label for this source")


@router.post("/ingest/text")
async def ingest_text(request: IngestTextRequest):
    """
    Ingest raw pasted text.

    Paste a transcript, notes, or any text content about metaprograms,
    NLP, sales techniques, communication patterns — anything that contains
    examples of how different types talk or what works with them.
    """
    try:
        result = await ingest_source(
            source=request.text,
            source_type="paste",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# TRAINING LIBRARY ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/library")
async def get_library_stats():
    """Get training library stats — how much data has been ingested."""
    library = TrainingLibrary.load()
    return {
        "stats": library.stats(),
        "sources": library.sources,
    }


@router.get("/library/examples")
async def get_library_examples(
    metaprogram: Optional[str] = None,
    pole: Optional[str] = None,
):
    """Get metaprogram examples from the training library, optionally filtered."""
    library = TrainingLibrary.load()
    examples = library.get_examples_for(metaprogram, pole) if metaprogram else library.all_examples
    return {
        "count": len(examples),
        "examples": examples,
    }


@router.get("/library/patterns")
async def get_library_patterns(
    metaprogram: Optional[str] = None,
    pole: Optional[str] = None,
):
    """Get language patterns from the training library, optionally filtered."""
    library = TrainingLibrary.load()
    patterns = library.get_patterns_for(metaprogram, pole) if metaprogram else library.all_patterns
    return {
        "count": len(patterns),
        "patterns": patterns,
    }


@router.get("/library/coaching")
async def get_library_coaching():
    """Get all coaching scenarios from the training library."""
    library = TrainingLibrary.load()
    return {
        "count": len(library.all_coaching_scenarios),
        "scenarios": library.all_coaching_scenarios,
    }


@router.get("/library/insights")
async def get_library_insights():
    """Get all raw insights from the training library."""
    library = TrainingLibrary.load()
    return {
        "count": len(library.all_insights),
        "insights": library.all_insights,
    }


@router.delete("/library")
async def clear_library():
    """Clear the entire training library. This is irreversible."""
    library = TrainingLibrary()
    library.save()
    return {"status": "cleared", "message": "Training library has been cleared."}


# ═══════════════════════════════════════════════════════════════
# TRANSCRIPTS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/transcripts")
async def list_transcripts():
    """List all saved transcripts."""
    transcripts = []
    if TRANSCRIPTS_DIR.exists():
        for f in sorted(TRANSCRIPTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix == ".txt":
                content = f.read_text(encoding="utf-8")
                transcripts.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "word_count": len(content.split()),
                    "preview": content[:200] + "..." if len(content) > 200 else content,
                })
    return {"count": len(transcripts), "transcripts": transcripts}


# ═══════════════════════════════════════════════════════════════
# WRITING ENGINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    profile: dict = Field(
        ...,
        description='Metaprogram profile, e.g. {"motivation": "toward", "reference": "external"}',
    )
    topic: str = Field(..., description="What the copy is about")
    channel: str = Field(default="general", description="instagram, email, landing_page, etc")
    tone: str = Field(default="conversational", description="conversational, professional, casual, urgent")
    length: str = Field(default="medium", description="short, medium, long")
    include_cta: bool = Field(default=True)
    cta_action: str = Field(default="check it out", description="The CTA action")


@router.post("/write/generate")
async def write_generate(request: GenerateRequest):
    """
    Generate fresh copy adapted to a metaprogram profile.

    The writing engine uses the training library to understand how each type
    talks and what they respond to, then generates copy in their exact frame.

    More training data = better copy. First upload = decent. 10+ = scary good.
    """
    try:
        wr = WritingRequest(
            mode="generate",
            profile=request.profile,
            topic=request.topic,
            channel=request.channel,
            tone=request.tone,
            length=request.length,
            include_cta=request.include_cta,
            cta_action=request.cta_action,
        )
        result = await generate_copy(wr)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RewriteRequest(BaseModel):
    existing_copy: str = Field(..., min_length=10, description="The copy to rewrite")
    profile: dict = Field(..., description="Target metaprogram profile")
    channel: str = Field(default="general")


@router.post("/write/rewrite")
async def write_rewrite(request: RewriteRequest):
    """
    Rewrite existing copy to match a metaprogram profile.

    Same information, same facts, same length — but framed in their language.
    The lead/follow dominance order is applied automatically.
    """
    try:
        wr = WritingRequest(
            mode="rewrite",
            profile=request.profile,
            topic="",
            channel=request.channel,
            existing_copy=request.existing_copy,
        )
        result = await generate_copy(wr)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CoachRequest(BaseModel):
    profile: dict = Field(..., description="Detected metaprogram profile")
    topic: str = Field(..., description="What you're talking about")
    scenario: str = Field(default="", description="Optional: describe the situation")


@router.post("/write/coach")
async def write_coach(request: CoachRequest):
    """
    Get a real-time coaching prompt for a live conversation.

    Returns:
    - SAY: exact phrase to say right now
    - WHY: one-sentence explanation
    - LEAD/FOLLOW: dominance order
    - DON'T: what would break rapport

    Short enough to read mid-conversation.
    """
    try:
        wr = WritingRequest(
            mode="coach",
            profile=request.profile,
            topic=request.topic,
            scenario=request.scenario,
        )
        result = await generate_copy(wr)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AllCombosRequest(BaseModel):
    topic: str = Field(..., description="What the copy is about")
    channel: str = Field(default="general")
    cta: str = Field(default="check it out")
    metaprograms: list[str] = Field(
        default=["motivation", "reference"],
        description="Which metaprograms to generate combos for (2 = 4 variants, 3 = 8)",
    )


@router.post("/write/all-combos")
async def write_all_combos(request: AllCombosRequest):
    """
    Generate copy for EVERY metaprogram combination.

    With 2 metaprograms: 4 variants (toward×internal, toward×external, etc.)
    With 3 metaprograms: 8 variants

    Returns a complete copy library for the topic, ready to deploy
    across any channel with profile-based routing.
    """
    try:
        result = await generate_all_combos(
            topic=request.topic,
            channel=request.channel,
            cta=request.cta,
            metaprograms=request.metaprograms,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
