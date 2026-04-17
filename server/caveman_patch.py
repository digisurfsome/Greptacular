"""
Caveman Mode Global Patch
=========================

Monkey-patches ``ClaudeAgentOptions`` so every SDK client spawned anywhere in
the server automatically gets caveman mode prepended to its system prompt.

Why a monkey-patch: AutoForge builds ``ClaudeAgentOptions(system_prompt=...)``
in ~40 places across routers and services. Rather than editing every call
site, we wrap the constructor once, at startup, so every agent (main + every
sub-agent spawned via the SDK) inherits the rules. The rules live in a single
file (``server/prompts/caveman.md``), read once and cached in memory.

Prompt caching: the prepended block is stable across turns, so Anthropic's
prompt cache covers it after the first call — effective per-turn cost is
near zero.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CAVEMAN_PATH = Path(__file__).parent / "prompts" / "caveman.md"
_caveman_text: str | None = None
_patched = False


def _load_caveman() -> str:
    global _caveman_text
    if _caveman_text is None:
        try:
            _caveman_text = _CAVEMAN_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            logger.warning("caveman.md not found at %s — caveman mode disabled", _CAVEMAN_PATH)
            _caveman_text = ""
    return _caveman_text


def _prepend_caveman(system_prompt):
    """Prepend caveman rules to whatever system_prompt was passed.

    Handles the three forms the SDK accepts: None, str, or dict (preset).
    For dict form with an ``append`` key we extend that; otherwise we only
    prepend when system_prompt is a string or None.
    """
    rules = _load_caveman()
    if not rules:
        return system_prompt

    if system_prompt is None or system_prompt == "":
        return rules
    if isinstance(system_prompt, str):
        return f"{rules}\n\n---\n\n{system_prompt}"
    if isinstance(system_prompt, dict):
        existing_append = system_prompt.get("append", "")
        system_prompt = dict(system_prompt)
        system_prompt["append"] = f"{rules}\n\n---\n\n{existing_append}" if existing_append else rules
        return system_prompt
    return system_prompt


def apply_caveman_patch() -> None:
    """Install the patch. Safe to call multiple times."""
    global _patched
    if _patched:
        return

    try:
        from claude_agent_sdk import ClaudeAgentOptions
    except ImportError:
        logger.warning("claude_agent_sdk not importable — caveman patch skipped")
        return

    original_init = ClaudeAgentOptions.__init__

    def patched_init(self, *args, **kwargs):
        if "system_prompt" in kwargs:
            kwargs["system_prompt"] = _prepend_caveman(kwargs["system_prompt"])
        original_init(self, *args, **kwargs)
        # Dataclass / attrs style: also handle post-init mutation if the SDK
        # stores system_prompt as an attribute and args came positionally.
        if hasattr(self, "system_prompt") and "system_prompt" not in kwargs:
            current = getattr(self, "system_prompt", None)
            wrapped = _prepend_caveman(current)
            if wrapped != current:
                try:
                    object.__setattr__(self, "system_prompt", wrapped)
                except Exception:
                    pass

    ClaudeAgentOptions.__init__ = patched_init
    _patched = True
    logger.info("Caveman mode patch applied to ClaudeAgentOptions")
