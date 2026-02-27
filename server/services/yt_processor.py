"""
YT Processor Service
====================

AI processing pipeline that takes raw YouTube ingestion data (transcript,
metadata, screenshot suggestions) plus user-provided context and sends it to
the Claude API for strategy extraction.

Returns a structured project + steps matching YTStrategyProject /
YTStrategyStep schemas for client-side localStorage persistence.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for strategy extraction
# ---------------------------------------------------------------------------

STRATEGY_EXTRACTION_PROMPT = """You are a strategy extraction specialist. You analyze video transcripts and extract actionable, repeatable business workflows.

Given a video transcript and user context, you must:
1. Identify the core strategy or workflow being demonstrated
2. Break it into numbered, sequential steps
3. For each step, provide:
   - A clear title (action-oriented)
   - What to do (detailed description)
   - The prompt to give a computer-use AI agent to execute this step
   - What the expected output looks like
   - Enhancement notes (what would make this step even better)
   - Recommended AI model (claude-opus-4-6 for complex visual/reasoning tasks, claude-sonnet-4-6 for balanced tasks, claude-haiku-4-5 for simple tasks)

Focus on making steps REPEATABLE for any niche, not just the specific one in the video.
Use {variables} for niche-specific details (e.g., {niche}, {business_name}, {target_audience}).

You MUST respond with ONLY valid JSON matching this exact schema — no markdown fences, no extra text:

{
  "project": {
    "name": "string - descriptive project name",
    "niche": "string - industry/niche identified",
    "description": "string - 1-2 sentence project description",
    "tags": ["string array of relevant tags"]
  },
  "steps": [
    {
      "order": 1,
      "title": "string - action-oriented step title",
      "description": "string - detailed what-to-do description",
      "prompt": "string - the prompt for a computer-use AI agent",
      "expectedOutput": "string - what the result should look like",
      "notes": "string - enhancement suggestions",
      "model": "claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5"
    }
  ]
}"""

# Default model for transcript processing (Sonnet for speed/cost balance)
DEFAULT_PROCESSING_MODEL = "claude-sonnet-4-6"


class YTProcessor:
    """Processes YouTube transcript data through Claude AI for strategy extraction."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv(
            "YT_LAB_DEFAULT_PROCESSING_MODEL", DEFAULT_PROCESSING_MODEL
        )

    def _build_user_message(
        self,
        transcript_text: str,
        metadata: dict,
        user_context: str,
        extracted_urls: list[str],
        screenshot_suggestions: list[dict],
    ) -> str:
        """Build the user message payload for the AI."""
        parts = []

        if user_context:
            parts.append(f"## User Context\n{user_context}")

        parts.append(f"## Video Metadata\nTitle: {metadata.get('title', 'Unknown')}")
        parts.append(f"Channel: {metadata.get('channel', 'Unknown')}")
        parts.append(f"Duration: {metadata.get('duration', 0)} seconds")

        if metadata.get("description"):
            desc = metadata["description"][:2000]
            parts.append(f"Description: {desc}")

        if extracted_urls:
            parts.append("## Links from Description\n" + "\n".join(f"- {u}" for u in extracted_urls[:20]))

        if screenshot_suggestions:
            moments = "\n".join(
                f"- {s.get('timestamp', 0):.0f}s: {s.get('reason', '')}"
                for s in screenshot_suggestions[:15]
            )
            parts.append(f"## Screenshot-Worthy Moments\n{moments}")

        parts.append(f"## Full Transcript\n{transcript_text}")

        return "\n\n".join(parts)

    def _format_transcript(self, transcript: list[dict]) -> str:
        """Join transcript segments into a single text block with timestamps."""
        lines = []
        for seg in transcript:
            start = seg.get("start", 0)
            minutes = int(start) // 60
            seconds = int(start) % 60
            lines.append(f"[{minutes}:{seconds:02d}] {seg.get('text', '')}")
        return "\n".join(lines)

    def _parse_ai_response(self, raw_text: str) -> dict:
        """Parse JSON from the AI response, handling various wrapper formats.

        The response may arrive as:
        - Pure JSON: ``{"project": ...}``
        - Markdown-fenced: ````json\\n{...}\\n````
        - Text + JSON: ``Here is the result:\\n{...}``
        - Any combination of the above
        """
        text = raw_text.strip()

        # Try 1: direct parse (fastest path)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try 2: strip markdown code fences
        if "```" in text:
            import re
            fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if fence_match:
                try:
                    return json.loads(fence_match.group(1).strip())
                except (json.JSONDecodeError, ValueError):
                    pass

        # Try 3: find the outermost JSON object { ... }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            json_candidate = text[first_brace:last_brace + 1]
            try:
                return json.loads(json_candidate)
            except (json.JSONDecodeError, ValueError):
                pass

        # Nothing worked — raise with helpful debug info
        preview = text[:500] if text else "(empty)"
        raise ValueError(f"Could not extract JSON from response. Preview: {preview}")

    async def _call_via_sdk(self, system_prompt: str, user_message: str, model: str) -> str:
        """Call Claude via the Agent SDK using subscription auth.

        Uses ``ClaudeSDKClient`` — the same pattern used by workspace chat,
        assistant chat, spec chat, and all AutoForge coding agents.  The SDK
        handles subscription OAuth internally so we never burn API credits.

        Returns the raw text response from Claude.
        Raises RuntimeError if the CLI is not available or the call fails.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        from registry import get_effective_sdk_env

        system_cli = shutil.which("claude")
        if not system_cli:
            raise RuntimeError("Claude CLI not found on PATH")

        sdk_env = get_effective_sdk_env(force_subscription=True)

        # Use a temp directory as cwd — we don't need file access
        scratch = tempfile.mkdtemp(prefix="yt_processor_")

        client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=model,
                cli_path=system_cli,
                system_prompt=system_prompt,
                env=sdk_env,
                max_turns=2,
                permission_mode="bypassPermissions",
                allowed_tools=[],
                cwd=scratch,
            )
        )

        try:
            await client.__aenter__()
            await client.query(user_message)

            full_text = ""
            msg_types_seen = []
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                msg_types_seen.append(msg_type)
                if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
                        else:
                            logger.debug("YT processor SDK: non-text block type=%s", block_type)

            logger.info(
                "YT processor SDK response: %d chars, msg_types=%s, preview=%.200s",
                len(full_text), msg_types_seen, full_text[:200],
            )

            if not full_text.strip():
                raise RuntimeError(
                    f"Claude SDK returned empty response. Message types seen: {msg_types_seen}"
                )
            return full_text.strip()
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass

    async def process(
        self,
        video_id: str,
        transcript: list[dict],
        metadata: dict,
        user_context: str,
        extracted_urls: list[str],
        screenshot_suggestions: list[dict],
        model: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """
        Process video data through Claude AI and return structured project + steps.

        Args:
            video_id: YouTube video ID
            transcript: List of transcript segment dicts (text, start, duration)
            metadata: Video metadata dict (title, channel, duration, description)
            user_context: User-provided context about what to extract
            extracted_urls: URLs found in the video description
            screenshot_suggestions: Screenshot-worthy moments from transcript analysis
            model: Override model for this request
            on_progress: Optional callback invoked with a status message string
                at each phase of processing (for real-time streaming updates).

        Returns:
            Dict with 'project' and 'steps' keys matching the frontend schema.

        Raises:
            RuntimeError: If the anthropic package is missing or the API call fails.
            ValueError: If the AI response cannot be parsed as valid JSON.
        """

        def log(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        use_model = model or self.model
        log(f"Formatting transcript ({len(transcript)} segments)...")
        transcript_text = self._format_transcript(transcript)

        user_message = self._build_user_message(
            transcript_text=transcript_text,
            metadata=metadata,
            user_context=user_context,
            extracted_urls=extracted_urls,
            screenshot_suggestions=screenshot_suggestions,
        )
        log(f"Building message payload ({len(transcript_text):,} chars)...")

        logger.info(
            "Processing video %s with model %s (transcript: %d segments, %d chars)",
            video_id,
            use_model,
            len(transcript),
            len(transcript_text),
        )

        start_time = time.time()

        log(f"Sending to Claude AI ({use_model})...")

        # Try Claude CLI first (uses subscription auth, no API credits).
        # Falls back to Anthropic SDK if CLI is not available.
        raw_text = ""
        try:
            log("Using Claude SDK (subscription billing)...")
            raw_text = await self._call_via_sdk(STRATEGY_EXTRACTION_PROMPT, user_message, use_model)
            log("Claude SDK responded successfully (subscription billing)")
            logger.info("Video %s: used Claude SDK (subscription billing)", video_id)
        except Exception as cli_err:
            logger.info("Claude SDK unavailable (%s), falling back to Anthropic SDK", cli_err)
            log("SDK unavailable — falling back to API key billing...")

            try:
                import anthropic
            except ImportError:
                raise RuntimeError(
                    "The anthropic package is required for video processing. "
                    "Install it with: pip install anthropic"
                )

            # Build client using the shared auth system (respects Settings UI + .env)
            client_kwargs: dict = {}
            try:
                from registry import get_effective_sdk_env
                sdk_env = get_effective_sdk_env()
                api_key = sdk_env.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
                base_url = sdk_env.get("ANTHROPIC_BASE_URL")
                if api_key:
                    client_kwargs["api_key"] = api_key
                if base_url:
                    client_kwargs["base_url"] = base_url
            except Exception:
                logger.debug("Could not load SDK env from registry, falling back to env vars")

            client = anthropic.Anthropic(**client_kwargs)

            key_source = "API key" if client_kwargs.get("api_key") else "environment"
            log(f"Calling Anthropic API ({key_source}) — this takes 60-90s...")

            # Run the synchronous Anthropic API call in a thread pool
            def _call_api():
                return client.messages.create(
                    model=use_model,
                    max_tokens=8192,
                    system=STRATEGY_EXTRACTION_PROMPT,
                    messages=[{"role": "user", "content": user_message}],
                )

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, _call_api)
            raw_text = response.content[0].text if response.content else ""
            log("Anthropic SDK responded")

        elapsed = time.time() - start_time

        if not raw_text:
            raise ValueError("AI returned an empty response")

        log("Parsing AI response...")

        try:
            result = self._parse_ai_response(raw_text)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("Failed to parse AI response as JSON: %s", exc)
            logger.debug("Raw AI response: %s", raw_text[:2000])
            raise ValueError(f"AI response was not valid JSON: {exc}")

        # Validate structure
        if "project" not in result or "steps" not in result:
            raise ValueError("AI response missing required 'project' or 'steps' keys")

        log(f"Done! Extracted {len(result.get('steps', []))} steps")

        logger.info(
            "Video %s processed in %.1fs: %d steps extracted",
            video_id,
            elapsed,
            len(result.get("steps", [])),
        )

        return {
            "project": result["project"],
            "steps": result["steps"],
            "processing_time": round(elapsed, 2),
        }
