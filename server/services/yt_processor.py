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
import re
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

CRITICAL OUTPUT FORMAT: Your ENTIRE response must be a single JSON object. No explanations, no markdown, no code fences, no preamble, no "here is the result" text. Start your response with { and end with }. This overrides any other formatting instructions you may have received.

The JSON must match this exact schema:

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

# Default model for transcript processing (Opus on subscription billing)
DEFAULT_PROCESSING_MODEL = "claude-opus-4-6"


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

    # Known key misspellings/variants the model has produced.
    # NOTE: Do NOT map "title" → "name" here — steps use "title" as a real field.
    # The project-level "title"→"name" fix is handled in _fix_project_title().
    _KEY_ALIASES: dict[str, str] = {
        "frame": "name",
        "project_name": "name",
        "step_name": "title",
        "desc": "description",
        "summary": "description",
    }

    @staticmethod
    def _fix_project_title(result: dict) -> dict:
        """If the project dict has 'title' instead of 'name', rename it."""
        project = result.get("project")
        if isinstance(project, dict) and "title" in project and "name" not in project:
            project["name"] = project.pop("title")
        return result

    @staticmethod
    def _repair_json(text: str) -> str:
        """Best-effort repair of common LLM JSON mistakes."""
        # Fix trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # Fix "key","nextkey" pattern (missing colon + value)
        text = re.sub(r'"([^"]+)"\s*,\s*"([^"]+)"\s*:', r'"\1": null, "\2":', text)
        # Replace single-quoted strings with double-quoted
        # (only outside of already double-quoted strings)
        text = re.sub(r"(?<![\\])'\s*:", '":', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
        # Fix unescaped newlines inside string values (common in LLM output)
        text = re.sub(r'(?<=": ")(.*?)(?=")', lambda m: m.group(0).replace("\n", "\\n"), text)
        # Fix missing comma between objects in arrays: }{ -> },{
        text = re.sub(r"}\s*{", "},{", text)
        # Fix JavaScript-style comments (// and /* */)
        text = re.sub(r"//[^\n]*", "", text)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
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

    @staticmethod
    def _extract_balanced_json(text: str) -> str | None:
        """Extract the first balanced JSON object from text using brace-depth counting.

        Walks forward from the first ``{`` and tracks brace depth, respecting
        quoted strings so that braces inside string values are not counted.
        Returns the balanced substring or ``None`` if no balanced object is found.
        """
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return None

    def _parse_ai_response(self, raw_text: str) -> dict:
        """Parse JSON from the AI response, handling various wrapper formats.

        The response may arrive as:
        - Pure JSON: ``{"project": ...}``
        - Markdown-fenced: ````json\\n{...}\\n````
        - Text + JSON: ``Here is the result:\\n{...}``
        - Any combination of the above

        Includes JSON repair for trailing commas, missing values, and
        key normalization for common misspellings.

        Strategies attempted in order:
        1. Direct parse
        2. Markdown code fence extraction
        3. First-brace / last-brace substring extraction
        4. Brace-depth balanced extraction (handles unbalanced trailing text)
        5. JSON repair + brace extraction
        6. JSON repair + balanced extraction
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
                fenced = fence_match.group(1).strip()
                try:
                    result = json.loads(fenced)
                    logger.info("Parse strategy: markdown fence")
                    return self._normalize_keys(result)
                except (json.JSONDecodeError, ValueError):
                    pass
                # Markdown fence content might itself need brace extraction
                balanced = self._extract_balanced_json(fenced)
                if balanced:
                    try:
                        result = json.loads(balanced)
                        logger.info("Parse strategy: markdown fence + balanced extraction")
                        return self._normalize_keys(result)
                    except (json.JSONDecodeError, ValueError):
                        pass

        # Try 3: strip everything before first { and after last } (aggressive)
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            json_candidate = text[first_brace:last_brace + 1]
            if first_brace > 0 or last_brace < len(text) - 1:
                stripped_prefix = text[:first_brace].strip()
                stripped_suffix = text[last_brace + 1:].strip()
                if stripped_prefix or stripped_suffix:
                    logger.info(
                        "Stripped preamble (%d chars) and suffix (%d chars) from response",
                        len(stripped_prefix), len(stripped_suffix),
                    )
            try:
                result = json.loads(json_candidate)
                logger.info("Parse strategy: brace extraction (first/last)")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try 4: brace-depth balanced extraction (handles cases where last }
        # is NOT the correct closing brace — e.g., trailing commentary with braces)
        balanced = self._extract_balanced_json(text)
        if balanced:
            try:
                result = json.loads(balanced)
                logger.info("Parse strategy: balanced brace-depth extraction")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try 5: repair common LLM JSON mistakes then re-extract via first/last
        if first_brace is not None and first_brace >= 0 and last_brace > first_brace:
            repaired = self._repair_json(text[first_brace:last_brace + 1])
            try:
                result = json.loads(repaired)
                logger.info("Parse strategy: JSON repair (first/last)")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Try 6: repair + balanced extraction (repair the whole text then balance)
        repaired_full = self._repair_json(text)
        balanced_repaired = self._extract_balanced_json(repaired_full)
        if balanced_repaired:
            try:
                result = json.loads(balanced_repaired)
                logger.info("Parse strategy: JSON repair + balanced extraction")
                return self._normalize_keys(result)
            except (json.JSONDecodeError, ValueError):
                pass

        # Nothing worked — log full response for debugging and raise
        logger.error("All 6 parse strategies failed. Full response:\n%s", text)
        preview = text[:500] if text else "(empty)"
        raise ValueError(f"Could not extract valid JSON from AI response (length={len(text)}). Preview: {preview}")

    # SDK timeout: 5 minutes handles Opus on 50KB+ payloads (typical: 90-180s)
    SDK_TIMEOUT_SECONDS = 300

    async def _call_via_sdk(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        timeout: float | None = None,
    ) -> str:
        """Call Claude via the Agent SDK using subscription auth.

        Uses ``ClaudeSDKClient`` -- the same pattern used by workspace chat,
        assistant chat, spec chat, and all AutoForge coding agents.  The SDK
        handles subscription OAuth internally so we never burn API credits.

        Args:
            system_prompt: System prompt for the conversation.
            user_message: User message content.
            model: Model identifier (e.g. ``claude-opus-4-6``).
            timeout: Maximum seconds to wait for a response. Defaults to
                ``SDK_TIMEOUT_SECONDS`` (300s / 5 minutes).

        Returns the raw text response from Claude.
        Raises RuntimeError if the CLI is not available or the call fails.
        Raises asyncio.TimeoutError if the SDK does not respond in time.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        from registry import get_effective_sdk_env

        system_cli = shutil.which("claude")
        if not system_cli:
            raise RuntimeError("Claude CLI not found on PATH")

        sdk_env = get_effective_sdk_env(force_subscription=True)

        # Use a temp directory as cwd -- we don't need file access
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

        effective_timeout = timeout if timeout is not None else self.SDK_TIMEOUT_SECONDS
        logger.info(
            "SDK call starting: model=%s, payload=%d chars, timeout=%ds",
            model, len(user_message), effective_timeout,
        )

        async def _run_sdk() -> str:
            await client.__aenter__()
            await client.query(user_message)

            full_text = ""
            msg_types_seen = []
            sdk_error: str | None = None
            async for msg in client.receive_response():
                msg_type = type(msg).__name__
                msg_types_seen.append(msg_type)
                if msg_type in ("RateLimitEvent", "rate_limit_event"):
                    continue  # Skip SDK informational events
                elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock" and hasattr(block, "text"):
                            full_text += block.text
                        else:
                            logger.debug("YT processor SDK: non-text block type=%s", block_type)
                elif msg_type == "ResultMessage":
                    is_error = getattr(msg, "is_error", False)
                    if is_error:
                        sdk_error = f"SDK ResultMessage reported an error (model={model})"
                    logger.info(
                        "YT processor SDK ResultMessage: is_error=%s, model=%s",
                        is_error, getattr(msg, "model", "unknown"),
                    )

            logger.info(
                "YT processor SDK response: %d chars, msg_types=%s, preview=%.200s",
                len(full_text), msg_types_seen, full_text[:200],
            )

            if sdk_error:
                raise RuntimeError(sdk_error)

            if not full_text.strip():
                raise RuntimeError(
                    f"Claude SDK returned empty response. Message types seen: {msg_types_seen}"
                )
            return full_text.strip()

        try:
            return await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
        except asyncio.TimeoutError:
            logger.error(
                "SDK call timed out after %ds (model=%s, payload=%d chars)",
                effective_timeout, model, len(user_message),
            )
            raise RuntimeError(
                f"Claude SDK timed out after {effective_timeout}s. "
                f"Large payloads may need the API fallback."
            )
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass

    async def _call_via_api(self, system_prompt: str, user_message: str, model: str) -> str:
        """Call Claude via the Anthropic API (uses API key, costs money).

        This is a lightweight fallback used for short retry prompts (e.g., JSON
        repair) where the SDK proved too slow. For small payloads the API
        responds in seconds and costs fractions of a cent.

        Returns the raw text response.
        Raises RuntimeError if the anthropic package is missing or the call fails.
        """
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "The anthropic package is required for API fallback. "
                "Install it with: pip install anthropic"
            )

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
            logger.debug("Could not load SDK env from registry for API retry, using env vars")

        client = anthropic.Anthropic(**client_kwargs)
        logger.info("API retry call: model=%s, payload=%d chars", model, len(user_message))

        def _call_api():
            return client.messages.create(
                model=model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _call_api)
        raw = response.content[0].text if response.content else ""
        if not raw.strip():
            raise RuntimeError("Anthropic API returned empty response during retry")
        return raw.strip()

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

        # Use Claude SDK with subscription auth — never falls back to API key.
        # This matches how tool-factory/generate works. No API credits burned.
        log("Using Claude SDK (subscription billing)...")
        raw_text = await self._call_via_sdk(STRATEGY_EXTRACTION_PROMPT, user_message, use_model)
        log("Claude SDK responded successfully (subscription billing)")
        logger.info("Video %s: used Claude SDK (subscription billing)", video_id)

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
            # Use SDK for retry too — subscription billing, no API credits.
            try:
                log("Retrying via SDK (subscription billing)...")
                retry_text = await self._call_via_sdk(
                    "You are a JSON repair assistant. Output ONLY valid JSON, nothing else.",
                    retry_prompt,
                    use_model,
                    timeout=120,  # Shorter timeout — retry prompt is small
                )
                result = self._parse_ai_response(retry_text)
                log("Retry succeeded — parsed repaired JSON")
                logger.info("JSON retry succeeded for video %s (via SDK)", video_id)
            except Exception as sdk_retry_exc:
                logger.error("SDK retry also failed: %s", sdk_retry_exc)
                raise ValueError(
                    "The AI response had formatting issues that couldn't be automatically repaired. "
                    "This sometimes happens with complex videos. Please try again — "
                    "the next response will likely be formatted correctly."
                ) from first_exc

        # Fix project-level "title" → "name" (can't do it in _KEY_ALIASES
        # because steps legitimately use "title").
        result = self._fix_project_title(result)

        # Detect API error responses — the SDK or Anthropic API may return
        # a valid JSON object with {error, type, request_id} instead of
        # the expected strategy schema.
        if "error" in result and "type" in result and len(result) <= 4:
            error_detail = result.get("error", {})
            if isinstance(error_detail, dict):
                error_msg = error_detail.get("message", str(error_detail))
                error_type = error_detail.get("type", "unknown")
            else:
                error_msg = str(error_detail)
                error_type = result.get("type", "unknown")
            logger.error(
                "AI returned an API error instead of strategy results: type=%s message=%s",
                error_type, error_msg,
            )
            raise RuntimeError(
                f"Claude API error ({error_type}): {error_msg}. "
                "Check your subscription status, model availability, or try again."
            )

        # Validate structure — SDK agent context may cause the model to wrap
        # the response under a top-level key or use different names.
        if "project" not in result or "steps" not in result:
            logger.warning(
                "Strategy response has unexpected keys. Got: %s, Expected: project, steps",
                sorted(result.keys()),
            )
            # Try unwrapping: check if the real data is nested under a wrapper key
            for wrapper_key in result:
                if isinstance(result[wrapper_key], dict):
                    inner = result[wrapper_key]
                    if "project" in inner or "steps" in inner:
                        logger.info("Found strategy data under key '%s'", wrapper_key)
                        result = inner
                        break

        if "project" not in result or "steps" not in result:
            raise ValueError(
                f"AI response missing required 'project' or 'steps' keys. "
                f"Got keys: {sorted(result.keys())}"
            )

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
