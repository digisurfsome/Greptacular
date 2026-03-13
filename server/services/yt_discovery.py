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
import re
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

CRITICAL OUTPUT FORMAT: Your ENTIRE response must be a single JSON object. No explanations, no markdown, no code fences, no preamble, no "here is the result" text. Start your response with { and end with }. This overrides any other formatting instructions you may have received.

The JSON must match this exact schema:

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

# Default model for discovery (Opus on subscription billing)
DEFAULT_DISCOVERY_MODEL = "claude-opus-4-6"


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

    # Known key misspellings/variants the model has produced
    _KEY_ALIASES: dict[str, str] = {
        "frame": "name",
        "project_name": "name",
        "title": "name",
        "step_name": "name",
        "desc": "description",
        "summary": "description",
        "context": "video_context",
        "insights": "key_insights",
        "opportunities": "app_opportunities",
        "recommendations": "recommendation",
    }

    @staticmethod
    def _repair_json(text: str) -> str:
        """Best-effort repair of common LLM JSON mistakes."""
        # Fix trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # Fix "key","nextkey" pattern (missing colon + value)
        text = re.sub(r'"([^"]+)"\s*,\s*"([^"]+)"\s*:', r'"\1": null, "\2":', text)
        # Replace single-quoted strings with double-quoted
        text = re.sub(r"(?<![\\])'\s*:", '":', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
        return text

    @classmethod
    def _normalize_keys(cls, obj: object) -> object:
        """Recursively lowercase keys and apply alias mappings."""
        if isinstance(obj, dict):
            normalized: dict = {}
            for key, value in obj.items():
                lower_key = key.lower().strip()
                mapped_key = cls._KEY_ALIASES.get(lower_key, lower_key)
                normalized[mapped_key] = cls._normalize_keys(value)
            return normalized
        if isinstance(obj, list):
            return [cls._normalize_keys(item) for item in obj]
        return obj

    def _parse_ai_response(self, raw_text: str) -> dict:
        """Parse JSON from the AI response, handling various wrapper formats.

        The response may arrive as:
        - Pure JSON: ``{"video_context": ...}``
        - Markdown-fenced: ````json\\n{...}\\n````
        - Text + JSON: ``Here is the result:\\n{...}``
        - Any combination of the above

        Includes JSON repair for trailing commas, missing values, and
        key normalization for common misspellings.
        """
        text = raw_text.strip()
        logger.info(
            "Parsing AI response: %d chars, preview=%.500s",
            len(text), text[:500],
        )

        # Try 1: direct parse (fastest path)
        try:
            result = json.loads(text)
            logger.info("Parse strategy: direct")
            return self._normalize_keys(result)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try 2: strip markdown code fences
        if "```" in text:
            fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if fence_match:
                try:
                    result = json.loads(fence_match.group(1).strip())
                    logger.info("Parse strategy: markdown fence")
                    return self._normalize_keys(result)
                except (json.JSONDecodeError, ValueError):
                    pass

        # Try 3: find the outermost JSON object { ... }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            json_candidate = text[first_brace:last_brace + 1]
            try:
                result = json.loads(json_candidate)
                logger.info("Parse strategy: brace extraction")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try 4: repair common LLM JSON mistakes then re-extract
        if first_brace is not None and first_brace >= 0 and last_brace > first_brace:
            repaired = self._repair_json(text[first_brace:last_brace + 1])
            try:
                result = json.loads(repaired)
                logger.info("Parse strategy: JSON repair")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Nothing worked — log full response for debugging and raise
        logger.error("All parse strategies failed. Full response:\n%s", text)
        preview = text[:500] if text else "(empty)"
        raise ValueError(f"Could not extract valid JSON from AI response (length={len(text)}). Preview: {preview}")

    async def _call_via_sdk(self, system_prompt: str, user_message: str, model: str) -> str:
        """Call Claude via the Agent SDK using SUBSCRIPTION auth ONLY.

        Uses ``ClaudeSDKClient`` with ``force_subscription=True`` — clears
        API key so the CLI falls back to ``~/.claude/.credentials.json``
        (subscription OAuth).  NO API CREDITS BURNED.

        AGENTS: DO NOT add an API key fallback here or anywhere that calls
        this method.  If this fails, the caller should let it fail — not
        silently switch to ``anthropic.Anthropic(api_key=...)``.
        See ``docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md``.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        from registry import get_effective_sdk_env

        t0 = time.time()

        # CRITICAL: Remove CLAUDECODE env var — it blocks nested Claude CLI sessions.
        # If the server was started from a Claude Code terminal, this var leaks into
        # subprocess spawns and causes "Cannot launch inside another session" (exit code 1).
        # workspace_chat_session.py already does this (line 857). This was MISSING here.
        os.environ.pop("CLAUDECODE", None)

        system_cli = shutil.which("claude")
        if not system_cli:
            raise RuntimeError("Claude CLI not found on PATH")

        sdk_env = get_effective_sdk_env(force_subscription=True)
        # Belt-and-suspenders: also clear it from the env dict passed to subprocess
        sdk_env.pop("CLAUDECODE", None)

        # ============================================================
        # SUBSCRIPTION BILLING VERIFICATION — SCREAMING LOUD ON PURPOSE
        # ============================================================
        api_key_val = sdk_env.get("ANTHROPIC_API_KEY", "(NOT SET)")
        auth_token_val = sdk_env.get("ANTHROPIC_AUTH_TOKEN", "(NOT SET)")
        has_api_key = bool(api_key_val and api_key_val not in ("", "(NOT SET)"))
        has_auth_token = bool(auth_token_val and auth_token_val not in ("", "(NOT SET)"))

        if has_api_key:
            logger.error(
                "🚨🚨🚨 BUG! force_subscription=True but ANTHROPIC_API_KEY='%s' "
                "— THIS WILL BURN API CREDITS! get_effective_sdk_env() is broken! 🚨🚨🚨",
                api_key_val[:10] + "..." if api_key_val else "(empty)",
            )
        else:
            logger.info(
                "✅ SUBSCRIPTION VERIFIED: ANTHROPIC_API_KEY='%s' (cleared=good), "
                "ANTHROPIC_AUTH_TOKEN='%s' (cleared=good). "
                "CLI will use ~/.claude/.credentials.json → $0 cost.",
                api_key_val, auth_token_val,
            )

        # Check credentials file exists
        import pathlib
        creds_path = pathlib.Path.home() / ".claude" / ".credentials.json"
        if creds_path.exists():
            logger.info("✅ Credentials file found: %s", creds_path)
        else:
            logger.warning(
                "⚠️ ~/.claude/.credentials.json NOT FOUND — "
                "subscription auth may fail! Run 'claude login' first."
            )

        t1 = time.time()
        logger.info(
            "⏱️ Auth setup took %.1fs | API key present: %s | Auth token present: %s",
            t1 - t0, has_api_key, has_auth_token,
        )

        # Use a temp directory as cwd — we don't need file access
        scratch = tempfile.mkdtemp(prefix="yt_discovery_")

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

        t2 = time.time()
        logger.info("⏱️ ClaudeSDKClient created in %.1fs", t2 - t1)

        try:
            sdk_t0 = time.time()
            logger.info("⏱️ [SDK] Entering client context (spawning CLI subprocess)...")
            await client.__aenter__()
            sdk_t1 = time.time()
            logger.info("⏱️ [SDK] CLI subprocess ready in %.1fs", sdk_t1 - sdk_t0)

            logger.info("⏱️ [SDK] Sending query (%d chars)...", len(user_message))
            await client.query(user_message)
            sdk_t2 = time.time()
            logger.info("⏱️ [SDK] Query sent in %.1fs", sdk_t2 - sdk_t1)

            logger.info("⏱️ [SDK] Waiting for response from %s (subscription billing)...", model)
            full_text = ""
            msg_types_seen: list[str] = []
            sdk_error: str | None = None
            first_content_time: float | None = None

            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                msg_types_seen.append(msg_type)

                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    logger.info("⏱️ [SDK] Rate limit event at %.1fs (informational, skipping)", time.time() - sdk_t2)
                    continue  # Skip SDK informational events
                elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    if first_content_time is None:
                        first_content_time = time.time()
                        logger.info(
                            "⏱️ [SDK] First content arrived in %.1fs (time-to-first-token from query)",
                            first_content_time - sdk_t2,
                        )
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
                        else:
                            logger.debug("YT discovery SDK: non-text block type=%s", block_type)
                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        sdk_error = f"SDK ResultMessage reported an error (model={model})"
                    logger.info(
                        "⏱️ [SDK] ResultMessage: is_error=%s, model=%s, total_time=%.1fs",
                        is_error, getattr(msg, "model", "unknown"), time.time() - sdk_t0,
                    )

            sdk_done = time.time()
            logger.info(
                "✅ [SDK] DONE: %d chars in %.1fs total | "
                "Subprocess start: %.1fs | Query send: %.1fs | "
                "Time-to-first-token: %.1fs | Streaming: %.1fs | "
                "msg_types=%s",
                len(full_text),
                sdk_done - sdk_t0,
                sdk_t1 - sdk_t0,
                sdk_t2 - sdk_t1,
                (first_content_time - sdk_t2) if first_content_time else -1,
                (sdk_done - first_content_time) if first_content_time else -1,
                msg_types_seen,
            )

            if sdk_error:
                raise RuntimeError(sdk_error)

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

        # =====================================================================
        # SUBSCRIPTION ONLY — NO API KEY FALLBACK — DO NOT ADD ONE
        # =====================================================================
        # This uses ClaudeSDKClient with force_subscription=True.
        # If it fails, it FAILS. We do NOT silently fall back to API key.
        # See docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md
        #
        # AGENTS: If you are reading this and thinking about adding an API key
        # fallback "just in case" — DO NOT. The owner pays $200/month for
        # subscription. Falling back to API key burns EXTRA money on top of
        # that. Every previous agent who added a fallback here created a bug.
        # =====================================================================
        log("SUBSCRIPTION BILLING: Calling Claude SDK (no API key, no fallback)...")
        log(f"Using {use_model} via subscription (force_subscription=True)")
        logger.info(
            ">>> SUBSCRIPTION BILLING: Discovery for video %s via SDK (force_subscription=True). "
            "If this fails, it fails — NO API key fallback. <<<",
            video_id,
        )
        sdk_start = time.time()
        raw_text = await self._call_via_sdk(DISCOVERY_PROMPT, user_message, use_model)
        sdk_elapsed = time.time() - sdk_start
        log(f"SUBSCRIPTION BILLING: Claude SDK responded in {sdk_elapsed:.1f}s — $0 API cost")
        logger.info(
            ">>> SUBSCRIPTION BILLING: Video %s discovery complete in %.1fs — $0 API cost <<<",
            video_id, sdk_elapsed,
        )

        elapsed = time.time() - start_time

        if not raw_text:
            raise ValueError("AI returned an empty response")

        log("Parsing AI response...")

        try:
            result = self._parse_ai_response(raw_text)
        except (json.JSONDecodeError, ValueError) as first_exc:
            logger.warning("First parse attempt failed: %s — retrying with stricter prompt", first_exc)
            log("Response had formatting issues — asking Claude to fix it...")
            retry_prompt = (
                "Your previous response was not valid JSON. "
                "Respond with ONLY a valid JSON object — no markdown fences, no commentary, no text before or after. "
                "Here is the malformed response to fix:\n\n"
                + raw_text[:6000]
            )
            try:
                retry_text = await self._call_via_sdk(
                    "You are a JSON repair assistant. Output ONLY valid JSON, nothing else.",
                    retry_prompt,
                    use_model,
                )
                result = self._parse_ai_response(retry_text)
                log("Retry succeeded — parsed repaired JSON")
                logger.info("JSON retry succeeded for video %s", video_id)
            except Exception as retry_exc:
                logger.error("Retry also failed: %s", retry_exc)
                raise ValueError(
                    "The AI response had formatting issues that couldn't be automatically repaired. "
                    "This sometimes happens with complex videos. Please try again — "
                    "the next response will likely be formatted correctly."
                ) from first_exc

        # Detect API error responses — the SDK or Anthropic API may return
        # a valid JSON object with {error, type, request_id} instead of
        # the expected discovery schema.
        if "error" in result and "type" in result and len(result) <= 4:
            error_detail = result.get("error", {})
            if isinstance(error_detail, dict):
                error_msg = error_detail.get("message", str(error_detail))
                error_type = error_detail.get("type", "unknown")
            else:
                error_msg = str(error_detail)
                error_type = result.get("type", "unknown")
            logger.error(
                "AI returned an API error instead of discovery results: type=%s message=%s",
                error_type, error_msg,
            )
            raise RuntimeError(
                f"Claude API error ({error_type}): {error_msg}. "
                "Check your subscription status, model availability, or try again."
            )

        # Validate structure — the SDK agent context may cause the model to wrap
        # the response differently (e.g. nested under a key, different key names).
        required_keys = {"video_context", "key_insights", "app_opportunities", "recommendation"}
        missing = required_keys - set(result.keys())
        if missing:
            # Log what we actually got for debugging
            logger.warning(
                "Discovery response has unexpected keys. Got: %s, Expected: %s",
                sorted(result.keys()), sorted(required_keys),
            )
            # Try common wrapper patterns: the model may nest the real data
            # under a top-level key like "response", "result", "discovery", etc.
            for wrapper_key in result:
                if isinstance(result[wrapper_key], dict):
                    inner = result[wrapper_key]
                    inner_missing = required_keys - set(inner.keys())
                    if len(inner_missing) < len(missing):
                        logger.info("Found better match under key '%s'", wrapper_key)
                        result = inner
                        missing = inner_missing
                        break

        if missing:
            raise ValueError(
                f"AI response missing required keys: {missing}. "
                f"Got keys: {sorted(result.keys())}"
            )

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
