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

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.services.meta_output_router import (
    CopyTag,
    OutputRouter,
)
from server.services.meta_training_ingestor import (
    AUDIO_EXTENSIONS,
    TEXT_EXTENSIONS,
    TRANSCRIPTS_DIR,
    VIDEO_EXTENSIONS,
    TrainingLibrary,
    ingest_source,
)
from server.services.meta_writing_engine import (
    WritingRequest,
    generate_all_combos,
    generate_copy,
)

router = APIRouter(prefix="/api/meta-training", tags=["meta-training"])
logger = logging.getLogger(__name__)

# Singleton output router
_output_router = OutputRouter()


# ═══════════════════════════════════════════════════════════════
# INGEST ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class IngestURLRequest(BaseModel):
    url: str = Field(..., description="YouTube URL to transcribe and ingest")


@router.post("/ingest/url")
async def ingest_url(
    request: IngestURLRequest,
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key"),
):
    """
    Ingest a YouTube URL.

    Fetches the transcript (free, no API key needed), extracts metaprogram
    training data using Claude, and adds it to the training library.
    """
    if x_openai_key:
        import os
        os.environ["OPENAI_API_KEY"] = x_openai_key
    try:
        result = await ingest_source(source=request.url, source_type="youtube")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload")
async def ingest_upload(
    file: UploadFile = File(...),
    x_openai_key: str | None = Header(None, alias="X-OpenAI-Key"),
):
    """
    Upload an audio, video, or text file for transcription and training extraction.

    Supported formats:
    - Audio: .mp3, .wav, .m4a, .ogg, .flac, .aac, .wma
    - Video: .mp4, .mov, .webm, .mkv, .avi, .wmv, .flv
    - Text: .txt, .md, .srt, .vtt, .json, .csv

    Audio/video files are transcribed using Whisper (OpenAI API or local).
    Text files are ingested directly.

    Pass X-OpenAI-Key header to use OpenAI Whisper API for transcription.
    """
    # If key provided via header, set it for this request
    if x_openai_key:
        import os
        os.environ["OPENAI_API_KEY"] = x_openai_key
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = Path(file.filename).suffix.lower()
    allowed = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TEXT_EXTENSIONS
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {sorted(allowed)}",
        )

    # Check file size (500MB max for audio/video, 10MB for text)
    content = await file.read()
    max_size = 500 * 1024 * 1024 if ext in (AUDIO_EXTENSIONS | VIDEO_EXTENSIONS) else 10 * 1024 * 1024
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
# SSE STREAMING INGEST ENDPOINTS
# ═══════════════════════════════════════════════════════════════
#
# These mirror the POST ingest endpoints above but stream progress
# messages to the client via Server-Sent Events. The on_progress
# callback pushes messages into an asyncio.Queue which the event
# generator yields from as SSE data frames.


def _sse_event(event_type: str, payload: dict) -> str:
    """Format a single SSE data frame."""
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


async def _stream_ingest(coro) -> StreamingResponse:
    """
    Run an ingest coroutine that feeds an asyncio.Queue via on_progress,
    and yield SSE events for each progress message plus the final result.
    """
    progress_queue: asyncio.Queue[str] = asyncio.Queue()

    def on_progress(msg: str) -> None:
        progress_queue.put_nowait(msg)

    async def event_generator():
        # Start the ingest work as a background task
        task = asyncio.create_task(coro(on_progress))

        # Yield progress messages while the task runs
        while not task.done():
            try:
                msg = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                yield _sse_event("progress", {"message": msg})
            except asyncio.TimeoutError:
                continue

        # Drain any remaining progress messages queued after task finished
        while not progress_queue.empty():
            msg = progress_queue.get_nowait()
            yield _sse_event("progress", {"message": msg})

        # Yield the final result or error
        try:
            result = task.result()
            yield _sse_event("done", {"result": result})
        except Exception as e:
            logger.exception("SSE ingest failed")
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ingest/url/stream")
async def ingest_url_stream(request: IngestURLRequest):
    """SSE endpoint for YouTube URL ingestion with real-time progress."""

    async def do_ingest(on_progress):
        return await ingest_source(
            source=request.url,
            source_type="youtube",
            on_progress=on_progress,
        )

    return await _stream_ingest(do_ingest)


@router.post("/ingest/upload/stream")
async def ingest_upload_stream(file: UploadFile = File(...)):
    """SSE endpoint for file upload ingestion with real-time progress."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = Path(file.filename).suffix.lower()
    allowed = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TEXT_EXTENSIONS
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Allowed: {sorted(allowed)}",
        )

    # Read file content upfront (before entering the SSE generator)
    content = await file.read()
    max_size = 100 * 1024 * 1024 if ext in (AUDIO_EXTENSIONS | VIDEO_EXTENSIONS) else 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {max_size // (1024 * 1024)}MB",
        )

    filename = file.filename

    async def do_ingest(on_progress):
        return await ingest_source(
            source="",
            uploaded_content=content,
            uploaded_filename=filename,
            on_progress=on_progress,
        )

    return await _stream_ingest(do_ingest)


@router.post("/ingest/text/stream")
async def ingest_text_stream(request: IngestTextRequest):
    """SSE endpoint for raw text ingestion with real-time progress."""

    async def do_ingest(on_progress):
        return await ingest_source(
            source=request.text,
            source_type="paste",
            on_progress=on_progress,
        )

    return await _stream_ingest(do_ingest)


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

        # Auto-route all variants through the output router
        for combo_key, variant in result.get("variants", {}).items():
            _output_router.route_writing_result(
                result=variant,
                topic=request.topic,
                channel=request.channel,
                copy_type="adapted",
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# OUTPUT ROUTER ENDPOINTS
# ═══════════════════════════════════════════════════════════════

class RouteRequest(BaseModel):
    content: str = Field(..., description="The copy to route")
    topic: str = Field(..., description="Topic this copy is about")
    channel: str = Field(default="general")
    copy_type: str = Field(default="custom", description="hook, detection, adapted, cta, etc")
    profile: dict = Field(default_factory=dict, description="Metaprogram profile")
    dominance_levels: dict = Field(default_factory=dict)
    sequence_position: int = Field(default=0)
    sequence_branch: str = Field(default="")
    is_leaf: bool = Field(default=False)
    destinations: list[str] = Field(
        default=["files", "manifest"],
        description='Where to send: "files", "manifest", "webhook:https://..."',
    )


@router.post("/route")
async def route_copy(request: RouteRequest):
    """
    Route a piece of copy to its destinations with proper tags.

    Every piece of output gets tagged with full metadata so any
    downstream system (email tool, social scheduler, CRM, ad manager,
    landing page builder) knows exactly what it's looking at.

    Destinations:
    - "files" — save to organized file structure
    - "manifest" — update master index for this topic
    - "webhook:https://..." — POST to external system
    """
    tags = CopyTag(
        topic=request.topic,
        copy_type=request.copy_type,
        channel=request.channel,
        profile=request.profile,
        dominance_levels=request.dominance_levels,
        sequence_position=request.sequence_position,
        sequence_branch=request.sequence_branch,
        is_leaf=request.is_leaf,
    )
    result = _output_router.route(request.content, tags, request.destinations)
    return result.to_dict()


class RouteSequenceRequest(BaseModel):
    sequence: dict = Field(..., description="Full sequence tree from /ingestion-sequences/generate")
    topic: str = Field(...)
    channel: str = Field(...)


@router.post("/route/sequence")
async def route_sequence(request: RouteSequenceRequest):
    """
    Route an entire decision tree through the output router.

    Takes the output from /api/ingestion-sequences/generate and saves
    every node as a properly tagged file. The full sequence is also
    saved as a single JSON file.
    """
    results = _output_router.route_sequence(request.sequence, request.topic, request.channel)
    return {
        "routed": len(results),
        "topic": request.topic,
        "channel": request.channel,
        "files": [r.file_path for r in results if r.file_path],
    }


# ─── TOPIC MANAGEMENT ───

@router.get("/output/topics")
async def list_output_topics():
    """List all topics that have routed output."""
    return {"topics": _output_router.list_topics()}


# NOTE: /output/find MUST come before /output/{topic_slug} to avoid
# FastAPI treating "find" as a topic_slug path parameter.
@router.get("/output/find")
async def find_copy(
    topic_slug: Optional[str] = None,
    channel: Optional[str] = None,
    profile_code: Optional[str] = None,
    copy_type: Optional[str] = None,
):
    """
    Find copy by tags. This is how downstream systems query.

    Examples:
    - Email tool: ?channel=email&profile_code=toward_external
    - CRM: ?copy_type=coach_prompt
    - Ad manager: ?channel=ad&topic_slug=keto_app
    - Social scheduler: ?channel=instagram
    """
    results = _output_router.find_copy(
        topic_slug=topic_slug,
        channel=channel,
        profile_code=profile_code,
        copy_type=copy_type,
    )
    return {"count": len(results), "results": results}


@router.get("/output/{topic_slug}")
async def get_topic_manifest(topic_slug: str):
    """Get the full manifest for a topic — all tagged copy pieces."""
    from server.services.meta_output_router import OUTPUT_BASE_DIR, OutputManifest
    manifest_path = OUTPUT_BASE_DIR / "by_topic" / topic_slug / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"No output found for topic: {topic_slug}")
    manifest = OutputManifest.load(manifest_path)
    return {
        "topic": manifest.topic,
        "total_pieces": manifest.total_pieces,
        "channels": manifest.channels,
        "profiles": manifest.profiles,
        "updated_at": manifest.updated_at,
        "pieces": manifest.pieces,
    }


@router.delete("/output/{topic_slug}")
async def delete_topic_output(topic_slug: str):
    """Delete all output for a topic."""
    deleted = _output_router.delete_topic(topic_slug)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No output found for topic: {topic_slug}")
    return {"status": "deleted", "topic_slug": topic_slug}


# ─── EXPORTS ───

@router.get("/output/{topic_slug}/export/csv")
async def export_csv(topic_slug: str):
    """Export all copy for a topic as CSV. Ready for spreadsheets, CRMs, email tools."""
    from fastapi.responses import PlainTextResponse
    try:
        csv_content = _output_router.export_csv(topic_slug)
        return PlainTextResponse(content=csv_content, media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/output/{topic_slug}/export/json")
async def export_json(topic_slug: str):
    """Export all copy as structured JSON. Organized by channel → profile."""
    try:
        return _output_router.export_json(topic_slug)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/output/{topic_slug}/export/html")
async def export_html(topic_slug: str):
    """Export all copy as a browseable HTML page. Open in browser to preview all variants."""
    from fastapi.responses import HTMLResponse
    try:
        html = _output_router.export_html(topic_slug)
        return HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
