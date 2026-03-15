"""
Metaprogram Training Material Ingestor
=======================================

Upload ANYTHING — YouTube URL, audio file, video file, text transcript —
and this pipeline:

1. TRANSCRIBES it (YouTube API for URLs, Whisper for audio/video)
2. EXTRACTS metaprogram training data (examples, patterns, questions, how types talk)
3. ORGANIZES into structured training material the detection engine can learn from
4. Feeds the WRITING ENGINE so it generates adapted copy per profile combo

The training material is the "manual" — real examples of how toward people talk,
how away-from people talk, what questions to ask, what the dominance spectrum
sounds like in practice. Feed it enough examples and the system nails detection
AND copy generation without templates.

Upload sources:
- YouTube URLs → youtube-transcript-api (free, no key)
- Audio files (.mp3, .wav, .m4a, .ogg, .flac) → Whisper transcription
- Video files (.mp4, .mov, .webm, .mkv) → extract audio → Whisper
- Text files (.txt, .md, .srt) → direct ingest
- Paste raw text → direct ingest
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# STORAGE — where training material lives
# ═══════════════════════════════════════════════════════════════

TRAINING_DATA_DIR = Path.home() / ".autoforge" / "meta_training"
TRANSCRIPTS_DIR = TRAINING_DATA_DIR / "transcripts"
EXTRACTIONS_DIR = TRAINING_DATA_DIR / "extractions"
TRAINING_LIBRARY_FILE = TRAINING_DATA_DIR / "training_library.json"

for _dir in [TRAINING_DATA_DIR, TRANSCRIPTS_DIR, EXTRACTIONS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# SOURCE TYPES
# ═══════════════════════════════════════════════════════════════

class SourceType(str, Enum):
    YOUTUBE = "youtube"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    PASTE = "paste"


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".wmv", ".flv"}
TEXT_EXTENSIONS = {".txt", ".md", ".srt", ".vtt", ".json", ".csv"}

YOUTUBE_PATTERNS = [
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
]


@dataclass
class TranscriptResult:
    """Output of the transcription step."""
    source_type: SourceType
    source_name: str          # filename or URL
    transcript: str           # the full text
    duration_seconds: float = 0.0
    word_count: int = 0
    language: str = "en"
    metadata: dict = field(default_factory=dict)  # title, channel, etc.
    transcript_path: Optional[str] = None  # where it's saved

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "transcript_preview": self.transcript[:500] + "..." if len(self.transcript) > 500 else self.transcript,
            "transcript_length": len(self.transcript),
            "word_count": self.word_count,
            "duration_seconds": self.duration_seconds,
            "language": self.language,
            "metadata": self.metadata,
            "transcript_path": self.transcript_path,
        }


@dataclass
class TrainingExtraction:
    """Structured training data extracted from a transcript."""
    source_name: str
    metaprogram_examples: list[dict] = field(default_factory=list)
    # Each example: {metaprogram, pole, dominance_level, quote, context, why_this_indicates}
    detection_questions: list[dict] = field(default_factory=list)
    # Each: {question, option_a, option_b, detects_metaprogram, authenticity_note}
    language_patterns: list[dict] = field(default_factory=list)
    # Each: {metaprogram, pole, phrases[], strength, context}
    type_descriptions: list[dict] = field(default_factory=list)
    # Each: {metaprogram, pole, description, how_they_talk, what_they_respond_to}
    coaching_scenarios: list[dict] = field(default_factory=list)
    # Each: {scenario, detected_profile, what_to_say, why_it_works}
    raw_insights: list[str] = field(default_factory=list)
    # Anything else useful that doesn't fit the above

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "stats": {
                "metaprogram_examples": len(self.metaprogram_examples),
                "detection_questions": len(self.detection_questions),
                "language_patterns": len(self.language_patterns),
                "type_descriptions": len(self.type_descriptions),
                "coaching_scenarios": len(self.coaching_scenarios),
                "raw_insights": len(self.raw_insights),
            },
            "metaprogram_examples": self.metaprogram_examples,
            "detection_questions": self.detection_questions,
            "language_patterns": self.language_patterns,
            "type_descriptions": self.type_descriptions,
            "coaching_scenarios": self.coaching_scenarios,
            "raw_insights": self.raw_insights,
        }


# ═══════════════════════════════════════════════════════════════
# STEP 1: TRANSCRIPTION
# ═══════════════════════════════════════════════════════════════

def detect_source_type(source: str) -> SourceType:
    """Detect whether input is YouTube URL, file path, or raw text."""
    # YouTube URL?
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, source):
            return SourceType.YOUTUBE

    # File path?
    path = Path(source)
    if path.exists() and path.is_file():
        ext = path.suffix.lower()
        if ext in AUDIO_EXTENSIONS:
            return SourceType.AUDIO
        elif ext in VIDEO_EXTENSIONS:
            return SourceType.VIDEO
        elif ext in TEXT_EXTENSIONS:
            return SourceType.TEXT

    # If it looks like a file path but doesn't exist
    if "/" in source or "\\" in source or source.endswith(tuple(AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TEXT_EXTENSIONS)):
        raise FileNotFoundError(f"File not found: {source}")

    # Raw text paste
    return SourceType.PASTE


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def transcribe_youtube(url: str, on_progress: Optional[Callable] = None) -> TranscriptResult:
    """Transcribe a YouTube video using the transcript API."""
    video_id = extract_youtube_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from: {url}")

    if on_progress:
        on_progress(f"Fetching transcript for YouTube video {video_id}...")

    # Get transcript
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_data = YouTubeTranscriptApi().fetch(video_id)
        segments = [
            {"text": seg.text, "start": seg.start, "duration": seg.duration}
            for seg in transcript_data
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to fetch YouTube transcript: {e}")

    # Combine into full text
    full_text = " ".join(seg["text"] for seg in segments)
    duration = max((seg["start"] + seg["duration"]) for seg in segments) if segments else 0

    # Get metadata via yt-dlp
    metadata = {}
    try:
        if on_progress:
            on_progress("Fetching video metadata...")
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", "--no-warnings", "--no-playlist", url],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            info = json.loads(result.stdout)
            metadata = {
                "title": info.get("title", ""),
                "channel": info.get("channel", info.get("uploader", "")),
                "duration": info.get("duration", 0),
                "publish_date": info.get("upload_date", ""),
                "description": info.get("description", "")[:500],
            }
    except Exception:
        metadata = {"title": f"YouTube video {video_id}"}

    # Save transcript
    safe_name = re.sub(r'[^\w\-]', '_', metadata.get("title", video_id))[:80]
    transcript_path = TRANSCRIPTS_DIR / f"yt_{safe_name}_{video_id}.txt"
    transcript_path.write_text(full_text, encoding="utf-8")

    if on_progress:
        on_progress(f"Transcript ready: {len(full_text)} chars, {len(full_text.split())} words")

    return TranscriptResult(
        source_type=SourceType.YOUTUBE,
        source_name=metadata.get("title", url),
        transcript=full_text,
        duration_seconds=duration,
        word_count=len(full_text.split()),
        metadata=metadata,
        transcript_path=str(transcript_path),
    )


async def transcribe_audio(
    file_path: str,
    on_progress: Optional[Callable] = None,
) -> TranscriptResult:
    """
    Transcribe an audio file using Whisper.

    Tries in order:
    1. OpenAI Whisper API (if OPENAI_API_KEY set) — fast, accurate, cheap
    2. Local whisper CLI (if installed) — free, slower
    3. yt-dlp + ffmpeg extraction as fallback for weird formats
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    if on_progress:
        on_progress(f"Transcribing {path.name}...")

    transcript = ""

    # Method 1: OpenAI Whisper API
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            transcript = await _transcribe_openai_whisper(file_path, openai_key, on_progress)
        except Exception as e:
            logger.warning(f"OpenAI Whisper failed, falling back: {e}")

    # Method 2: Local whisper CLI
    if not transcript:
        try:
            transcript = await _transcribe_local_whisper(file_path, on_progress)
        except Exception as e:
            logger.warning(f"Local whisper failed: {e}")

    # Method 3: ffmpeg to wav + retry
    if not transcript:
        try:
            wav_path = await _convert_to_wav(file_path)
            transcript = await _transcribe_local_whisper(wav_path, on_progress)
            os.unlink(wav_path)  # clean up temp wav
        except Exception as e:
            raise RuntimeError(
                f"All transcription methods failed for {path.name}. "
                f"Install whisper (`pip install openai-whisper`) or set OPENAI_API_KEY. "
                f"Last error: {e}"
            )

    # Save
    safe_name = re.sub(r'[^\w\-]', '_', path.stem)[:80]
    transcript_path = TRANSCRIPTS_DIR / f"audio_{safe_name}.txt"
    transcript_path.write_text(transcript, encoding="utf-8")

    if on_progress:
        on_progress(f"Transcript ready: {len(transcript)} chars, {len(transcript.split())} words")

    return TranscriptResult(
        source_type=SourceType.AUDIO,
        source_name=path.name,
        transcript=transcript,
        word_count=len(transcript.split()),
        transcript_path=str(transcript_path),
    )


async def transcribe_video(
    file_path: str,
    on_progress: Optional[Callable] = None,
) -> TranscriptResult:
    """Transcribe a video file by extracting audio then running Whisper."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    if on_progress:
        on_progress(f"Extracting audio from {path.name}...")

    # Extract audio with ffmpeg
    audio_path = await _extract_audio_from_video(file_path)

    # Transcribe the extracted audio
    result = await transcribe_audio(audio_path, on_progress)
    result.source_type = SourceType.VIDEO
    result.source_name = path.name

    # Clean up temp audio
    try:
        os.unlink(audio_path)
    except Exception:
        pass

    return result


async def ingest_text(
    text: str,
    source_name: str = "pasted_text",
    on_progress: Optional[Callable] = None,
) -> TranscriptResult:
    """Ingest raw text or text file content directly."""
    if on_progress:
        on_progress(f"Ingesting text: {len(text)} chars...")

    safe_name = re.sub(r'[^\w\-]', '_', source_name)[:80]
    transcript_path = TRANSCRIPTS_DIR / f"text_{safe_name}_{int(time.time())}.txt"
    transcript_path.write_text(text, encoding="utf-8")

    return TranscriptResult(
        source_type=SourceType.TEXT if source_name != "pasted_text" else SourceType.PASTE,
        source_name=source_name,
        transcript=text,
        word_count=len(text.split()),
        transcript_path=str(transcript_path),
    )


async def ingest_text_file(
    file_path: str,
    on_progress: Optional[Callable] = None,
) -> TranscriptResult:
    """Ingest a text/SRT/VTT file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    text = path.read_text(encoding="utf-8")

    # If SRT/VTT, strip the timecodes
    if path.suffix.lower() in (".srt", ".vtt"):
        text = _strip_subtitle_timecodes(text)

    return await ingest_text(text, source_name=path.name, on_progress=on_progress)


# ═══════════════════════════════════════════════════════════════
# TRANSCRIPTION HELPERS
# ═══════════════════════════════════════════════════════════════

def _split_audio_into_chunks(file_path: str, max_chunk_mb: int = 24) -> list[str]:
    """Split a large audio file into chunks small enough for the Whisper API (25MB limit).

    Uses ffmpeg to split by duration. Returns list of temp file paths.
    Caller is responsible for cleaning up the temp files.
    """
    file_size = os.path.getsize(file_path)
    max_bytes = max_chunk_mb * 1024 * 1024

    if file_size <= max_bytes:
        return [file_path]  # No splitting needed

    # Get duration via ffprobe
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        capture_output=True, text=True, timeout=30,
    )
    if probe.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {probe.stderr}")

    total_duration = float(probe.stdout.strip())
    num_chunks = max(2, int(file_size / max_bytes) + 1)
    chunk_duration = total_duration / num_chunks

    chunk_paths = []
    ext = Path(file_path).suffix
    try:
        for i in range(num_chunks):
            start = i * chunk_duration
            chunk_path = tempfile.mktemp(suffix=f"_chunk{i}{ext}")
            result = subprocess.run(
                [
                    "ffmpeg", "-i", file_path,
                    "-ss", str(start),
                    "-t", str(chunk_duration),
                    "-c", "copy",  # fast, no re-encoding
                    "-y", chunk_path,
                ],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg chunk split failed: {result.stderr}")
            chunk_paths.append(chunk_path)
    except Exception:
        # Clean up any chunks created so far on failure
        for p in chunk_paths:
            if os.path.exists(p):
                os.unlink(p)
        raise

    return chunk_paths


async def _transcribe_openai_whisper(
    file_path: str,
    api_key: str,
    on_progress: Optional[Callable] = None,
) -> str:
    """Use OpenAI's Whisper API for transcription. Auto-chunks files > 24MB."""
    import asyncio

    if on_progress:
        on_progress("Using OpenAI Whisper API...")

    def _call_api():
        import httpx

        chunk_paths = _split_audio_into_chunks(file_path)
        is_chunked = chunk_paths[0] != file_path

        try:
            transcripts = []
            for idx, chunk in enumerate(chunk_paths):
                if is_chunked and on_progress:
                    on_progress(f"Transcribing chunk {idx + 1}/{len(chunk_paths)}...")
                with open(chunk, "rb") as f:
                    response = httpx.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        files={"file": (Path(chunk).name, f, "audio/mpeg")},
                        data={"model": "whisper-1", "response_format": "text"},
                        timeout=300,
                    )
                    response.raise_for_status()
                    transcripts.append(response.text)

            return " ".join(transcripts)
        finally:
            if is_chunked:
                for p in chunk_paths:
                    if os.path.exists(p):
                        try:
                            os.unlink(p)
                        except Exception:
                            pass

    return await asyncio.get_event_loop().run_in_executor(None, _call_api)


async def _transcribe_local_whisper(
    file_path: str,
    on_progress: Optional[Callable] = None,
) -> str:
    """Use locally installed whisper CLI."""
    import asyncio

    if on_progress:
        on_progress("Using local Whisper model...")

    def _run():
        # Try whisper CLI first
        for cmd in ["whisper", "python -m whisper"]:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    result = subprocess.run(
                        cmd.split() + [
                            file_path,
                            "--model", "base",
                            "--output_format", "txt",
                            "--output_dir", tmpdir,
                            "--language", "en",
                        ],
                        capture_output=True, text=True, timeout=600,
                    )
                    if result.returncode == 0:
                        # Find the output txt file
                        txt_files = list(Path(tmpdir).glob("*.txt"))
                        if txt_files:
                            return txt_files[0].read_text(encoding="utf-8")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        raise RuntimeError("Local whisper not found. Install: pip install openai-whisper")

    return await asyncio.get_event_loop().run_in_executor(None, _run)


async def _convert_to_wav(file_path: str) -> str:
    """Convert any audio format to WAV using ffmpeg."""
    import asyncio

    output = tempfile.mktemp(suffix=".wav")

    def _run():
        result = subprocess.run(
            ["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1", "-y", output],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
        return output

    return await asyncio.get_event_loop().run_in_executor(None, _run)


async def _extract_audio_from_video(file_path: str) -> str:
    """Extract audio track from video using ffmpeg."""
    import asyncio

    output = tempfile.mktemp(suffix=".wav")

    def _run():
        result = subprocess.run(
            [
                "ffmpeg", "-i", file_path,
                "-vn",  # no video
                "-ar", "16000",  # 16kHz sample rate (Whisper optimal)
                "-ac", "1",  # mono
                "-y",  # overwrite
                output,
            ],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
        return output

    return await asyncio.get_event_loop().run_in_executor(None, _run)


def _strip_subtitle_timecodes(text: str) -> str:
    """Strip SRT/VTT timecodes, leaving just the text."""
    # Remove VTT header
    text = re.sub(r'^WEBVTT\n.*?\n\n', '', text, flags=re.DOTALL)
    # Remove timecodes (00:00:00.000 --> 00:00:00.000)
    text = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', text)
    # Remove sequence numbers
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════
# STEP 2: METAPROGRAM TRAINING EXTRACTION (AI-powered)
# ═══════════════════════════════════════════════════════════════
#
# Takes a transcript and extracts structured training data:
# - How each type talks (real quotes)
# - Detection questions (what to ask)
# - Language patterns (phrases that indicate each pole)
# - Coaching scenarios (what to say when)
#
# Uses Claude to do the extraction — this is the "brain" that
# understands NLP/metaprograms and can identify examples in
# natural conversation.

EXTRACTION_SYSTEM_PROMPT = """\
You are a metaprogram training data extraction specialist. You analyze
transcripts of NLP, sales, persuasion, and communication content to extract
structured training material for a metaprogram detection and messaging system.

METAPROGRAMS YOU KNOW:
1. MOTIVATION: Toward (gains, goals, aspiration) vs Away From (pain, problems, avoidance)
2. REFERENCE: Internal (trust own judgment) vs External (look to others/experts)
3. WORK STYLE: Options (flexibility, choices) vs Procedures (steps, structure)
4. CHUNK SIZE: Big Picture (overview, gist) vs Detail (specifics, numbers)
5. ACTION: Proactive (make it happen) vs Reactive (handle as it comes)

4-LEVEL DOMINANCE SPECTRUM (per metaprogram):
- Level 1: PURE pole_a (85%+) — only speak in that frame
- Level 2: DOMINANT pole_a (60-85%) — LEAD with pole_a, FOLLOW with pole_b
- Level 3: DOMINANT pole_b (60-85%) — LEAD with pole_b, FOLLOW with pole_a
- Level 4: PURE pole_b (85%+) — only speak in that frame

WHAT TO EXTRACT:

1. **metaprogram_examples** — Real quotes from the transcript that demonstrate
   a specific metaprogram pole. Include the quote, which metaprogram/pole it
   shows, estimated dominance level, and WHY it indicates that pole.

2. **detection_questions** — Questions mentioned or implied that could detect
   metaprograms. Must follow ZERO-PRESSURE rules: both options equally valid,
   about their life not about buying, no "right" answer. Include which
   metaprogram it detects and an authenticity note.

3. **language_patterns** — Specific phrases or sentence structures that indicate
   a metaprogram pole. Group by strength (strong/medium/weak signal).

4. **type_descriptions** — How each type TALKS, what they RESPOND to, what
   they VALUE. Real behavioral descriptions, not theory.

5. **coaching_scenarios** — Specific situations where knowing the metaprogram
   changes what you should say. Include the scenario, detected profile,
   what to say, and why it works.

6. **raw_insights** — Anything else useful about metaprograms, persuasion,
   detection, or adapted communication that doesn't fit the above categories.

CRITICAL: Only extract what's ACTUALLY in the transcript. Don't invent examples.
If the transcript doesn't discuss metaprograms directly, extract implicit examples
(how the speaker talks reveals THEIR metaprogram profile, and any advice they
give about communication/sales likely maps to metaprogram concepts even if they
don't use that terminology).

Return a single JSON object matching the schema. No markdown, no code fences.
Start with { and end with }.
"""

EXTRACTION_OUTPUT_SCHEMA = """\
{
  "metaprogram_examples": [
    {
      "metaprogram": "motivation",
      "pole": "toward",
      "dominance_level": 2,
      "quote": "exact quote from transcript",
      "context": "what was being discussed",
      "why_this_indicates": "explanation of why this shows toward motivation"
    }
  ],
  "detection_questions": [
    {
      "question": "the question text",
      "option_a": {"text": "first option", "detects": "toward"},
      "option_b": {"text": "second option", "detects": "away_from"},
      "detects_metaprogram": "motivation",
      "authenticity_note": "why this question gets honest answers"
    }
  ],
  "language_patterns": [
    {
      "metaprogram": "motivation",
      "pole": "toward",
      "phrases": ["phrase 1", "phrase 2"],
      "strength": "strong",
      "context": "when people use these phrases"
    }
  ],
  "type_descriptions": [
    {
      "metaprogram": "motivation",
      "pole": "toward",
      "description": "how this type thinks and acts",
      "how_they_talk": "speech patterns and word choices",
      "what_they_respond_to": "messaging that resonates with them"
    }
  ],
  "coaching_scenarios": [
    {
      "scenario": "description of the situation",
      "detected_profile": {"motivation": "toward", "reference": "external"},
      "what_to_say": "exact phrase or approach",
      "why_it_works": "explanation"
    }
  ],
  "raw_insights": [
    "insight 1",
    "insight 2"
  ]
}
"""


async def extract_training_data(
    transcript: str,
    source_name: str,
    on_progress: Optional[Callable] = None,
) -> TrainingExtraction:
    """
    Extract metaprogram training data from a transcript using Claude.

    Uses subscription auth (force_subscription=True) per CLAUDE.md rules.
    """
    if on_progress:
        on_progress(f"Extracting training data from {source_name}...")

    # Truncate very long transcripts to fit context
    max_chars = 150000  # ~37K tokens, well within limits
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[TRANSCRIPT TRUNCATED]"

    user_message = f"""Analyze this transcript and extract metaprogram training data.

TRANSCRIPT SOURCE: {source_name}

TRANSCRIPT:
{transcript}

OUTPUT SCHEMA (return JSON matching this exactly):
{EXTRACTION_OUTPUT_SCHEMA}

Remember: Only extract what's ACTUALLY in the transcript. Real quotes, real examples.
If the content doesn't discuss metaprograms by name, extract IMPLICIT examples —
the speaker's own communication style reveals their metaprograms, and any sales/
persuasion/communication advice maps to these concepts."""

    try:
        from registry import get_effective_sdk_env
        env = get_effective_sdk_env(force_subscription=True)
    except ImportError:
        env = {}

    import anthropic
    client = anthropic.Anthropic()

    if on_progress:
        on_progress("Calling Claude for extraction (this takes 30-60 seconds)...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text.strip()

    # Parse JSON
    try:
        # Handle potential markdown wrapping
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            data = json.loads(json_match.group())
        else:
            logger.error(f"Failed to parse extraction output: {raw_text[:500]}")
            data = {}

    extraction = TrainingExtraction(
        source_name=source_name,
        metaprogram_examples=data.get("metaprogram_examples", []),
        detection_questions=data.get("detection_questions", []),
        language_patterns=data.get("language_patterns", []),
        type_descriptions=data.get("type_descriptions", []),
        coaching_scenarios=data.get("coaching_scenarios", []),
        raw_insights=data.get("raw_insights", []),
    )

    # Save extraction
    safe_name = re.sub(r'[^\w\-]', '_', source_name)[:80]
    extraction_path = EXTRACTIONS_DIR / f"extraction_{safe_name}_{int(time.time())}.json"
    extraction_path.write_text(json.dumps(extraction.to_dict(), indent=2), encoding="utf-8")

    if on_progress:
        stats = extraction.to_dict()["stats"]
        on_progress(
            f"Extracted: {stats['metaprogram_examples']} examples, "
            f"{stats['detection_questions']} questions, "
            f"{stats['language_patterns']} patterns, "
            f"{stats['coaching_scenarios']} scenarios"
        )

    return extraction


# ═══════════════════════════════════════════════════════════════
# STEP 3: TRAINING LIBRARY — accumulates all extractions
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrainingLibrary:
    """
    Accumulated training material from all sources.

    This is the "brain" — the complete knowledge base of how each
    metaprogram type talks, what questions to ask, what patterns
    to look for, and what copy to write for each combo.

    Fed into the writing engine to generate adapted copy.
    """
    sources: list[str] = field(default_factory=list)
    all_examples: list[dict] = field(default_factory=list)
    all_questions: list[dict] = field(default_factory=list)
    all_patterns: list[dict] = field(default_factory=list)
    all_type_descriptions: list[dict] = field(default_factory=list)
    all_coaching_scenarios: list[dict] = field(default_factory=list)
    all_insights: list[str] = field(default_factory=list)
    last_updated: str = ""

    def add_extraction(self, extraction: TrainingExtraction):
        """Merge a new extraction into the library."""
        if extraction.source_name not in self.sources:
            self.sources.append(extraction.source_name)

        self.all_examples.extend(extraction.metaprogram_examples)
        self.all_questions.extend(extraction.detection_questions)
        self.all_patterns.extend(extraction.language_patterns)
        self.all_type_descriptions.extend(extraction.type_descriptions)
        self.all_coaching_scenarios.extend(extraction.coaching_scenarios)
        self.all_insights.extend(extraction.raw_insights)
        self.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")

    def get_examples_for(self, metaprogram: str, pole: Optional[str] = None) -> list[dict]:
        """Get all examples for a specific metaprogram/pole."""
        results = [e for e in self.all_examples if e.get("metaprogram") == metaprogram]
        if pole:
            results = [e for e in results if e.get("pole") == pole]
        return results

    def get_patterns_for(self, metaprogram: str, pole: Optional[str] = None) -> list[dict]:
        """Get all language patterns for a metaprogram/pole."""
        results = [p for p in self.all_patterns if p.get("metaprogram") == metaprogram]
        if pole:
            results = [p for p in results if p.get("pole") == pole]
        return results

    def get_type_description(self, metaprogram: str, pole: str) -> Optional[dict]:
        """Get the most complete description for a metaprogram pole."""
        descs = [d for d in self.all_type_descriptions
                 if d.get("metaprogram") == metaprogram and d.get("pole") == pole]
        # Return the longest/most detailed one
        return max(descs, key=lambda d: len(str(d)), default=None)

    def get_coaching_for_profile(self, profile: dict) -> list[dict]:
        """Get coaching scenarios that match a detected profile."""
        results = []
        for scenario in self.all_coaching_scenarios:
            detected = scenario.get("detected_profile", {})
            # Check if any metaprograms overlap
            for mp, pole in detected.items():
                if profile.get(mp) == pole:
                    results.append(scenario)
                    break
        return results

    def stats(self) -> dict:
        return {
            "sources": len(self.sources),
            "examples": len(self.all_examples),
            "questions": len(self.all_questions),
            "patterns": len(self.all_patterns),
            "type_descriptions": len(self.all_type_descriptions),
            "coaching_scenarios": len(self.all_coaching_scenarios),
            "insights": len(self.all_insights),
            "last_updated": self.last_updated,
        }

    def save(self):
        """Persist to disk."""
        data = {
            "sources": self.sources,
            "all_examples": self.all_examples,
            "all_questions": self.all_questions,
            "all_patterns": self.all_patterns,
            "all_type_descriptions": self.all_type_descriptions,
            "all_coaching_scenarios": self.all_coaching_scenarios,
            "all_insights": self.all_insights,
            "last_updated": self.last_updated,
        }
        TRAINING_LIBRARY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "TrainingLibrary":
        """Load from disk or create empty."""
        lib = cls()
        if TRAINING_LIBRARY_FILE.exists():
            try:
                data = json.loads(TRAINING_LIBRARY_FILE.read_text(encoding="utf-8"))
                lib.sources = data.get("sources", [])
                lib.all_examples = data.get("all_examples", [])
                lib.all_questions = data.get("all_questions", [])
                lib.all_patterns = data.get("all_patterns", [])
                lib.all_type_descriptions = data.get("all_type_descriptions", [])
                lib.all_coaching_scenarios = data.get("all_coaching_scenarios", [])
                lib.all_insights = data.get("all_insights", [])
                lib.last_updated = data.get("last_updated", "")
            except (json.JSONDecodeError, KeyError):
                pass
        return lib


# ═══════════════════════════════════════════════════════════════
# MASTER PIPELINE — upload anything, get training data out
# ═══════════════════════════════════════════════════════════════

async def ingest_source(
    source: str,
    source_type: Optional[str] = None,
    uploaded_content: Optional[bytes] = None,
    uploaded_filename: Optional[str] = None,
    on_progress: Optional[Callable] = None,
) -> dict:
    """
    Master ingest function. Handles everything.

    Args:
        source: YouTube URL, file path, or raw text
        source_type: Override auto-detection ("youtube", "audio", "video", "text", "paste")
        uploaded_content: Raw bytes from file upload (FastAPI UploadFile)
        uploaded_filename: Original filename of upload
        on_progress: Callback for progress updates

    Returns:
        {
            "transcript": TranscriptResult dict,
            "extraction": TrainingExtraction dict,
            "library_stats": current library stats,
        }
    """
    # Handle file uploads — save to temp, then process
    temp_path = None
    if uploaded_content and uploaded_filename:
        ext = Path(uploaded_filename).suffix.lower()
        temp_path = tempfile.mktemp(suffix=ext)
        Path(temp_path).write_bytes(uploaded_content)
        source = temp_path
        if not source_type:
            if ext in AUDIO_EXTENSIONS:
                source_type = "audio"
            elif ext in VIDEO_EXTENSIONS:
                source_type = "video"
            elif ext in TEXT_EXTENSIONS:
                source_type = "text"

    try:
        # Auto-detect source type
        if source_type:
            stype = SourceType(source_type)
        else:
            stype = detect_source_type(source)

        if on_progress:
            on_progress(f"Source type: {stype.value}")

        # Step 1: Transcribe
        if stype == SourceType.YOUTUBE:
            transcript_result = await transcribe_youtube(source, on_progress)
        elif stype == SourceType.AUDIO:
            transcript_result = await transcribe_audio(source, on_progress)
        elif stype == SourceType.VIDEO:
            transcript_result = await transcribe_video(source, on_progress)
        elif stype == SourceType.TEXT:
            transcript_result = await ingest_text_file(source, on_progress)
        elif stype == SourceType.PASTE:
            transcript_result = await ingest_text(source, on_progress=on_progress)
        else:
            raise ValueError(f"Unknown source type: {stype}")

        # Step 2: Extract training data
        extraction = await extract_training_data(
            transcript=transcript_result.transcript,
            source_name=transcript_result.source_name,
            on_progress=on_progress,
        )

        # Step 3: Add to training library
        library = TrainingLibrary.load()
        library.add_extraction(extraction)
        library.save()

        if on_progress:
            on_progress(f"Training library updated. Total sources: {len(library.sources)}")

        return {
            "transcript": transcript_result.to_dict(),
            "extraction": extraction.to_dict(),
            "library_stats": library.stats(),
        }

    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
