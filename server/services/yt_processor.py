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
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Call Claude via the Agent SDK using SUBSCRIPTION auth ONLY.

        Uses ``ClaudeSDKClient`` with ``force_subscription=True`` — clears
        API key so the CLI falls back to ``~/.claude/.credentials.json``
        (subscription OAuth).  NO API CREDITS BURNED.

        IMPORTANT: Uses ``permission_mode="acceptEdits"`` to match ALL
        working SDK clients in this codebase (workspace_chat_session.py,
        spec_chat_session.py, client.py).  ``"bypassPermissions"`` caused
        exit code 3 (Bun runtime crash) on Windows.

        AGENTS: DO NOT add an API key fallback here or anywhere that calls
        this method.  If this fails, the caller should let it fail — not
        silently switch to ``anthropic.Anthropic(api_key=...)``.
        See ``docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md``.
        """
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

        from registry import get_effective_sdk_env

        t0 = time.time()

        def _log(msg: str) -> None:
            """Log to BOTH server terminal AND browser UI log panel."""
            logger.info(msg)
            if on_progress:
                on_progress(msg)

        # CRITICAL: Remove CLAUDECODE env var — it blocks nested Claude CLI sessions.
        os.environ.pop("CLAUDECODE", None)

        system_cli = shutil.which("claude")
        if not system_cli:
            raise RuntimeError("Claude CLI not found on PATH")
        _log(f"[SDK] CLI binary: {system_cli}")

        sdk_env = get_effective_sdk_env(force_subscription=True)
        sdk_env.pop("CLAUDECODE", None)

        # Subscription verification
        api_key_val = sdk_env.get("ANTHROPIC_API_KEY", "(NOT SET)")
        auth_token_val = sdk_env.get("ANTHROPIC_AUTH_TOKEN", "(NOT SET)")
        has_api_key = bool(api_key_val and api_key_val not in ("", "(NOT SET)"))

        if has_api_key:
            _log(f"🚨 BUG: API key present despite force_subscription=True! Key starts with: {api_key_val[:10]}...")
        else:
            _log(f"✅ Subscription auth: API_KEY='{api_key_val}' AUTH_TOKEN='{auth_token_val}' (both cleared = subscription)")

        import pathlib
        creds_path = pathlib.Path.home() / ".claude" / ".credentials.json"
        if creds_path.exists():
            # Check if credentials file has content
            creds_size = creds_path.stat().st_size
            _log(f"✅ Credentials file: {creds_path} ({creds_size} bytes)")
        else:
            _log(f"⚠️ NO credentials file at {creds_path} — run 'claude login' first!")

        t1 = time.time()
        _log(f"[SDK] Auth setup: {t1 - t0:.1f}s")

        # Use a temp directory as cwd
        scratch = tempfile.mkdtemp(prefix="yt_processor_")

        # Create settings file matching the working pattern
        import pathlib as _pl
        settings_file = _pl.Path(scratch) / ".claude-yt-settings.json"
        settings_file.write_text(json.dumps({
            "permissions": {
                "defaultMode": "acceptEdits",
                "allow": [],
            },
        }))

        client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model=model,
                cli_path=system_cli,
                system_prompt=system_prompt,
                env=sdk_env,
                max_turns=2,
                permission_mode="acceptEdits",
                allowed_tools=[],
                cwd=scratch,
                settings=str(settings_file.resolve()),
                setting_sources=["user"],
            )
        )

        t2 = time.time()
        _log(f"[SDK] Client created: {t2 - t1:.1f}s | model={model} | mode=acceptEdits")

        effective_timeout = timeout if timeout is not None else self.SDK_TIMEOUT_SECONDS
        _log(f"[SDK] Timeout: {effective_timeout}s | Payload: {len(user_message):,} chars")

        async def _run_sdk() -> str:
            sdk_t0 = time.time()
            _log("[SDK] Spawning CLI subprocess...")

            try:
                await client.__aenter__()
            except Exception as enter_err:
                err_str = str(enter_err)
                _log(f"🚨 CLI FAILED TO START: {err_str}")
                _log(f"🚨 CLI path: {system_cli} | model: {model} | cwd: {scratch}")
                if "exit code" in err_str.lower():
                    _log("🚨 Exit code 1 = nested session block | Exit code 3 = Bun crash")
                raise RuntimeError(
                    f"Claude CLI failed to start (model={model}): {err_str}"
                ) from enter_err

            sdk_t1 = time.time()
            _log(f"[SDK] CLI subprocess ready: {sdk_t1 - sdk_t0:.1f}s")

            _log(f"[SDK] Sending query ({len(user_message):,} chars)...")
            await client.query(user_message)
            sdk_t2 = time.time()
            _log(f"[SDK] Query sent: {sdk_t2 - sdk_t1:.1f}s — now waiting for {model} to respond...")

            full_text = ""
            msg_count = 0
            msg_types_seen: list[str] = []
            sdk_error: str | None = None
            first_content_time: float | None = None
            rate_limit_count = 0
            last_progress_time = time.time()

            # The SDK may THROW "Unknown message type: rate_limit_event"
            # instead of yielding it.  If we already have content, catch
            # the exception and use what we collected.
            try:
                async for msg in client.receive_response():
                    now = time.time()
                    elapsed = now - sdk_t2
                    msg_type = type(msg).__name__
                    msg_types_seen.append(msg_type)
                    msg_count += 1

                    # Periodic heartbeat every 15s so user knows it's alive
                    if now - last_progress_time >= 15:
                        _log(
                            f"[SDK] Still waiting... {elapsed:.0f}s elapsed | "
                            f"{msg_count} msgs | {len(full_text):,} chars received | "
                            f"rate_limits: {rate_limit_count}"
                        )
                        last_progress_time = now

                    if msg_type in ("RateLimitEvent", "rate_limit_event"):
                        rate_limit_count += 1
                        rl_detail = ""
                        for attr in ("retry_after", "retry_after_seconds", "message", "error"):
                            val = getattr(msg, attr, None)
                            if val is not None:
                                rl_detail += f" {attr}={val}"
                        _log(
                            f"⚠️ RATE LIMIT #{rate_limit_count} at {elapsed:.0f}s{rl_detail} "
                            f"— SDK will retry automatically"
                        )
                        continue

                    elif msg_type == "SystemMessage" or msg_type == "system":
                        sys_text = ""
                        if hasattr(msg, "message"):
                            sys_text = str(msg.message)[:300]
                        elif hasattr(msg, "content"):
                            sys_text = str(msg.content)[:300]
                        elif hasattr(msg, "text"):
                            sys_text = str(msg.text)[:300]
                        _log(f"📢 SYSTEM MSG at {elapsed:.0f}s: {sys_text or '(no text)'}")

                    elif msg_type == "AssistantMessage" and hasattr(msg, "content"):
                        if first_content_time is None:
                            first_content_time = now
                            _log(f"🟢 FIRST CONTENT at {elapsed:.0f}s (time-to-first-token)")
                        for block in msg.content:
                            block_type = type(block).__name__
                            if block_type == "TextBlock" and hasattr(block, "text"):
                                chunk_len = len(block.text)
                                full_text += block.text
                                _log(f"[SDK] Received {chunk_len:,} chars (total: {len(full_text):,}) at {elapsed:.0f}s")
                            elif block_type == "ToolUseBlock":
                                tool_name = getattr(block, "name", "unknown")
                                _log(f"⚠️ Tool call attempted: {tool_name} at {elapsed:.0f}s (tools disabled, will be rejected)")
                            else:
                                _log(f"[SDK] Non-text block: {block_type} at {elapsed:.0f}s")

                    elif msg_type == "ResultMessage":
                        is_error = getattr(msg, "is_error", False)
                        result_model = getattr(msg, "model", "unknown")
                        if is_error:
                            result_text = ""
                            if hasattr(msg, "result") and msg.result:
                                result_text = str(msg.result)[:500]
                            elif hasattr(msg, "content"):
                                for block in getattr(msg, "content", []):
                                    if hasattr(block, "text"):
                                        result_text += block.text
                            sdk_error = (
                                f"SDK error (model={model}): {result_text}"
                                if result_text
                                else f"SDK ResultMessage error (model={model})"
                            )
                            _log(f"🚨 ERROR RESULT at {elapsed:.0f}s: {sdk_error}")
                        else:
                            _log(f"✅ DONE at {elapsed:.0f}s | model={result_model} | {len(full_text):,} chars total")
                    else:
                        attrs = {k: str(v)[:100] for k, v in vars(msg).items() if not k.startswith("_")} if hasattr(msg, "__dict__") else {}
                        _log(f"❓ UNKNOWN MSG TYPE '{msg_type}' at {elapsed:.0f}s | attrs: {attrs}")
            except Exception as stream_exc:
                # The SDK throws "Unknown message type: rate_limit_event"
                # instead of yielding it. If we already collected text,
                # treat this as a successful (albeit noisy) completion.
                exc_str = str(stream_exc)
                _log(f"⚠️ SDK stream exception: {exc_str}")
                if full_text.strip() and "unknown message type" in exc_str.lower():
                    _log(f"✅ Recovered: already have {len(full_text):,} chars — using collected text despite SDK error")
                elif full_text.strip():
                    _log(f"⚠️ Stream error after receiving {len(full_text):,} chars — attempting to use collected text")
                else:
                    raise

            sdk_done = time.time()
            total = sdk_done - sdk_t0
            _log(
                f"[SDK] Stream ended: {len(full_text):,} chars in {total:.1f}s | "
                f"{msg_count} messages | {rate_limit_count} rate limits | "
                f"types: {msg_types_seen}"
            )

            if sdk_error:
                raise RuntimeError(sdk_error)

            if not full_text.strip():
                _log(f"🚨 EMPTY RESPONSE! {msg_count} messages received but no text content. Types: {msg_types_seen}")
                raise RuntimeError(
                    f"Claude SDK returned empty response after {total:.0f}s. "
                    f"Messages: {msg_count}, Types: {msg_types_seen}, "
                    f"Rate limits: {rate_limit_count}"
                )
            return full_text.strip()

        try:
            return await asyncio.wait_for(_run_sdk(), timeout=effective_timeout)
        except asyncio.TimeoutError:
            elapsed = time.time() - t0
            _log(f"🚨 TIMEOUT after {elapsed:.0f}s (limit: {effective_timeout}s) | model={model}")
            raise RuntimeError(
                f"Claude SDK timed out after {effective_timeout}s. "
                f"The model may be overloaded or rate-limited — try again."
            )
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass
            try:
                shutil.rmtree(scratch, ignore_errors=True)
            except Exception:
                pass

    # ==================================================================
    # NO _call_via_api METHOD — REMOVED ON PURPOSE
    # ==================================================================
    # There used to be a _call_via_api() here that used anthropic.Anthropic()
    # with an API key. It was REMOVED because it burns API credits.
    #
    # AGENTS: DO NOT re-add a _call_via_api method. DO NOT add any code
    # that creates anthropic.Anthropic(api_key=...). ALL calls go through
    # _call_via_sdk() which uses subscription billing (force_subscription=True).
    # See docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md
    # ==================================================================

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

        # =====================================================================
        # SUBSCRIPTION ONLY — NO API KEY FALLBACK — DO NOT ADD ONE
        # =====================================================================
        # AGENTS: Do NOT add a try/except here that falls back to API key.
        # See the giant warning in _call_via_api's tombstone above.
        # See docs/SUBSCRIPTION_AND_WEBSOCKET_GUIDE.md
        # =====================================================================
        log("SUBSCRIPTION BILLING: Calling Claude SDK (no API key, no fallback)...")
        log(f"Using {use_model} via subscription (force_subscription=True)")
        logger.info(
            ">>> SUBSCRIPTION BILLING: Processing video %s via SDK (force_subscription=True). "
            "If this fails, it fails — NO API key fallback. <<<",
            video_id,
        )
        sdk_start = time.time()
        raw_text = await self._call_via_sdk(STRATEGY_EXTRACTION_PROMPT, user_message, use_model, on_progress=log)
        sdk_elapsed = time.time() - sdk_start
        log(f"SUBSCRIPTION BILLING: Claude SDK responded in {sdk_elapsed:.1f}s — $0 API cost")
        logger.info(
            ">>> SUBSCRIPTION BILLING: Video %s complete in %.1fs — $0 API cost <<<",
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
            # Retry also uses SDK — SUBSCRIPTION ONLY, no API key.
            try:
                log("SUBSCRIPTION BILLING: Retrying JSON repair via SDK (no API key)...")
                retry_text = await self._call_via_sdk(
                    "You are a JSON repair assistant. Output ONLY valid JSON, nothing else.",
                    retry_prompt,
                    use_model,
                    timeout=120,  # Shorter timeout — retry prompt is small
                    on_progress=log,
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
