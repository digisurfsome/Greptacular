"""
YT Discovery Service
====================

AI-powered discovery & evaluation phase that analyzes YouTube video transcripts
to identify key insights, app opportunities, and strategic recommendations
BEFORE jumping into strategy extraction / build steps.

This is the "think first" layer — it presents the user with a ranked set of
opportunities so they can make an informed decision about what to build.

Returns structured findings matching the YTDiscoveryResponse schema.
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
# System prompt for opportunity discovery
# ---------------------------------------------------------------------------

DISCOVERY_PROMPT = """You are an expert business analyst and app strategist. You analyze video content from entrepreneurs, business leaders, and creators to identify actionable opportunities.

Given a video transcript, metadata, and optional user context, you must:

1. **Extract Key Insights** — The most important lessons, principles, or frameworks from the video. Focus on wisdom that could be applied to building products or businesses.

2. **Identify App Opportunities** — Concrete app ideas that emerge from the content. These could be:
   - **Companion apps**: Simple tools that help the viewer apply what they learned (e.g., a pain-point journaling app from a video about finding product ideas)
   - **Direct implementations**: Apps the speaker describes or demonstrates
   - **Derivative ideas**: Products inspired by the strategies discussed
   - **Teaching/delivery apps**: Apps that package the video's knowledge into an interactive learning experience

3. **Evaluate Each Opportunity** — For each app idea, provide:
   - How simple it is to build (1-5, where 1 = weekend project, 5 = months of work)
   - Strategic value: Does it get you on someone's phone? Create recurring engagement? Enable upselling?
   - Market potential: Is there real demand? What's the competitive landscape?
   - Why it's a good or bad idea — honest reasoning, not hype

4. **Recommend a Path** — Which opportunity should they pursue first and why. Consider:
   - Start simple (get something in users' hands fast)
   - Think about the "phone real estate" advantage (an app on someone's phone = gold)
   - Consider how the app can grow (teach → engage → monetize)
   - Identify if opportunities can be combined or sequenced

IMPORTANT: Be honest. Not every video has great app opportunities. If the content is purely theoretical with no actionable angles, say so. The user needs your real assessment, not forced enthusiasm.

You MUST respond with ONLY valid JSON matching this exact schema — no markdown fences, no extra text:

{
  "video_context": {
    "speaker": "string - who is speaking and why they matter (credibility context)",
    "core_topic": "string - the main subject of the video in one sentence",
    "target_audience": "string - who would benefit most from this content"
  },
  "key_insights": [
    {
      "insight": "string - the key lesson or principle",
      "quote": "string - relevant quote from the transcript (approximate is fine)",
      "timestamp_approx": "string - approximate timestamp like '12:30'",
      "applicability": "string - how this insight can be applied practically"
    }
  ],
  "app_opportunities": [
    {
      "name": "string - descriptive app name",
      "type": "companion | direct | derivative | teaching",
      "one_liner": "string - one sentence description",
      "description": "string - 2-3 sentence detailed description",
      "why_this_works": "string - honest strategic reasoning for why this is a good idea",
      "concerns": "string - potential issues, risks, or reasons it might not work",
      "complexity": 1,
      "strategic_value": "string - explanation of strategic positioning (phone real estate, engagement loops, etc.)",
      "market_signal": "string - evidence of demand from the video or general market knowledge",
      "features": ["string array of 3-5 core features"],
      "growth_path": "string - how this simple app could evolve over time",
      "score": 85
    }
  ],
  "recommendation": {
    "top_pick_index": 0,
    "reasoning": "string - detailed explanation of why this is the best starting point",
    "sequence": "string - suggested order if multiple opportunities should be pursued",
    "quick_win": "string - what could be built in a weekend to validate the idea"
  }
}

SCORING GUIDE for app_opportunities[].score (0-100):
- 90-100: No-brainer — simple to build, clear demand, strong strategic positioning
- 70-89: Strong opportunity — good idea with some complexity or market uncertainty
- 50-69: Worth considering — decent idea but significant concerns
- 30-49: Weak — probably not worth the effort unless the user has unique advantages
- 0-29: Skip — too complex, no clear demand, or better alternatives exist"""

# Default model for discovery (Sonnet for speed/cost balance)
DEFAULT_DISCOVERY_MODEL = "claude-sonnet-4-6"


class YTDiscovery:
    """Analyzes YouTube video content to discover and evaluate app opportunities."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv(
            "YT_LAB_DEFAULT_DISCOVERY_MODEL", DEFAULT_DISCOVERY_MODEL
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
        """Parse JSON from the AI response, handling markdown fences if present."""
        text = raw_text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
            if text.endswith("```"):
                text = text[:-3].strip()

        return json.loads(text)

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
        scratch = tempfile.mkdtemp(prefix="yt_discovery_")

        client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=model,
                cli_path=system_cli,
                system_prompt=system_prompt,
                env=sdk_env,
                max_turns=1,
                permission_mode="bypassPermissions",
                allowed_tools=[],
                cwd=scratch,
            )
        )

        try:
            await client.__aenter__()
            await client.query(user_message)

            full_text = ""
            async for msg in client.receive_response():
                if type(msg).__name__ == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text

            if not full_text.strip():
                raise RuntimeError("Claude SDK returned empty response")
            return full_text.strip()
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass

    async def discover(
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
        Analyze video content to discover and evaluate app opportunities.

        Args:
            video_id: YouTube video ID
            transcript: List of transcript segment dicts (text, start, duration)
            metadata: Video metadata dict (title, channel, duration, description)
            user_context: User-provided context about their goals/interests
            extracted_urls: URLs found in the video description
            screenshot_suggestions: Screenshot-worthy moments from transcript analysis
            model: Override model for this request
            on_progress: Optional callback invoked with a status message string
                at each phase of processing (for real-time streaming updates).

        Returns:
            Dict with 'video_context', 'key_insights', 'app_opportunities',
            and 'recommendation' keys.

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
            "Discovering opportunities for video %s with model %s (transcript: %d segments, %d chars)",
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
            raw_text = await self._call_via_sdk(DISCOVERY_PROMPT, user_message, use_model)
            log("Claude SDK responded successfully (subscription billing)")
            logger.info("Video %s: used Claude SDK (subscription billing)", video_id)
        except Exception as cli_err:
            logger.info("Claude SDK unavailable (%s), falling back to Anthropic SDK", cli_err)
            log("SDK unavailable — falling back to API key billing...")

            try:
                import anthropic
            except ImportError:
                raise RuntimeError(
                    "The anthropic package is required for video discovery. "
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
                    system=DISCOVERY_PROMPT,
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
            logger.error("Failed to parse AI discovery response as JSON: %s", exc)
            logger.debug("Raw AI response: %s", raw_text[:2000])
            raise ValueError(f"AI response was not valid JSON: {exc}")

        # Validate structure
        required_keys = {"video_context", "key_insights", "app_opportunities", "recommendation"}
        missing = required_keys - set(result.keys())
        if missing:
            raise ValueError(f"AI response missing required keys: {missing}")

        log(f"Done! Found {len(result.get('key_insights', []))} insights, {len(result.get('app_opportunities', []))} opportunities")

        logger.info(
            "Video %s discovery completed in %.1fs: %d insights, %d opportunities",
            video_id,
            elapsed,
            len(result.get("key_insights", [])),
            len(result.get("app_opportunities", [])),
        )

        return {
            "video_context": result["video_context"],
            "key_insights": result["key_insights"],
            "app_opportunities": result["app_opportunities"],
            "recommendation": result["recommendation"],
            "discovery_time": round(elapsed, 2),
        }
