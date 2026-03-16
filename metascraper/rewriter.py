"""
Message Rewriter — takes any copy and rewrites it to match a detected metaprogram profile.

This is the money maker. Same offer, same product — but spoken in THEIR frame.
Uses Claude API for intelligent rewriting (not templates — actual adaptive language).

Also contains the conversational fallback questions for when scraping
doesn't return enough signal. These questions are designed to feel
enticing and fun — not like a survey.
"""

import json
from typing import Optional

import anthropic

from metascraper.detector import MetaprogramProfile

# ═══════════════════════════════════════════════════════════════
# CONVERSATIONAL METAPROGRAM QUESTIONS
# ═══════════════════════════════════════════════════════════════
#
# These are the fallback when scraping can't get enough signal.
# Each question locks in one metaprogram.
# They're designed to feel like a personality quiz — enticing,
# not laborious. The user WANTS to answer because the options
# feel like they reveal something about themselves.
#
# Key: the FIRST question is already answered by whatever they
# typed in the hero input. So we detect from that, then only
# ask what we're still missing.

FALLBACK_QUESTIONS = {
    "motivation": {
        "question": "When you imagine next month going perfectly, is it more like...",
        "option_a": {
            "text": "Everything I want is falling into place",
            "result": "toward",
            "emoji": "✨",
        },
        "option_b": {
            "text": "Nothing is stressing me out anymore",
            "result": "away_from",
            "emoji": "😮‍💨",
        },
    },
    "reference": {
        "question": "When you're about to try something new, you usually...",
        "option_a": {
            "text": "Just go for it and figure it out",
            "result": "internal",
            "emoji": "🎯",
        },
        "option_b": {
            "text": "Check what other people say first",
            "result": "external",
            "emoji": "🔍",
        },
    },
    "work_style": {
        "question": "When someone's helping you with something, you'd rather they...",
        "option_a": {
            "text": "Give me options and let me pick",
            "result": "options",
            "emoji": "🎨",
        },
        "option_b": {
            "text": "Just tell me exactly what to do",
            "result": "procedures",
            "emoji": "📋",
        },
    },
    # Bonus questions (only if we need more signal)
    "chunk_size": {
        "question": "When someone's explaining something to you, you prefer...",
        "option_a": {
            "text": "Give me the bottom line",
            "result": "big_picture",
            "emoji": "🌍",
        },
        "option_b": {
            "text": "Give me all the details",
            "result": "detail",
            "emoji": "🔬",
        },
    },
    "action": {
        "question": "Honestly, which is more you?",
        "option_a": {
            "text": "I make things happen",
            "result": "proactive",
            "emoji": "⚡",
        },
        "option_b": {
            "text": "I handle things as they come",
            "result": "reactive",
            "emoji": "🌊",
        },
    },
}


def get_needed_questions(profile: MetaprogramProfile) -> list[dict]:
    """
    Given a partial profile (from scraping or hero input),
    return only the questions we still need to ask.

    Core 3 must be confident. Bonus 2 are optional.
    """
    needed = []
    core = ["motivation", "reference", "work_style"]

    for mp_name in core:
        if mp_name not in profile.scores or profile.scores[mp_name].confidence < 0.3:
            if mp_name in FALLBACK_QUESTIONS:
                needed.append({
                    "metaprogram": mp_name,
                    **FALLBACK_QUESTIONS[mp_name],
                })

    return needed


# ═══════════════════════════════════════════════════════════════
# MESSAGE REWRITER (AI-powered)
# ═══════════════════════════════════════════════════════════════

REWRITE_SYSTEM_PROMPT = """\
You are a communication calibration engine. You rewrite messages to match
a person's unconscious communication preferences (metaprograms).

You do NOT change the meaning, offer, or facts. You change HOW it's said
so it resonates with how this specific person processes information.

RULES:
- Same information, different frame
- Never mention metaprograms, NLP, or psychology — just rewrite naturally
- Keep the same length (don't make it longer)
- Match their energy level
- Sound like a human, not a marketer

METAPROGRAM GUIDE:

Toward: Frame benefits as gains, achievements, goals to reach
Away From: Frame benefits as problems solved, pain avoided, risks eliminated

Internal: Let them decide, present data, "you know best"
External: Show social proof, numbers, what others did, expert opinions

Options: Give choices, alternatives, "here are 3 ways"
Procedures: Give steps, sequence, "here's exactly what to do"

Big Picture: Keep it high level, bottom line, the gist
Detail: Include specifics, numbers, examples, breakdown

Proactive: Action language, "let's go", "starting now"
Reactive: Response language, "when X happens", "here's what to do if"
"""


async def rewrite_message(
    original: str,
    profile: MetaprogramProfile,
    api_key: str,
    context: str = "general",
) -> str:
    """
    Rewrite a message to match a person's metaprogram profile.

    Args:
        original: The original copy/message to rewrite
        profile: Detected metaprogram profile
        api_key: Anthropic API key
        context: Where this message appears ("email", "landing_page",
                 "notification", "chat", "ad", "general")

    Returns:
        Rewritten message in their frame
    """
    profile_desc = []
    for name, score in profile.scores.items():
        if score.confidence >= 0.2:
            profile_desc.append(
                f"- {name}: {score.winner} (confidence: {score.strength})"
            )

    if not profile_desc:
        return original  # No profile = no rewrite

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Haiku for speed + cost
        max_tokens=1024,
        system=REWRITE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Rewrite this {context} message to match this person's communication style:

THEIR PROFILE:
{chr(10).join(profile_desc)}

ORIGINAL MESSAGE:
{original}

REWRITTEN MESSAGE (same info, their frame):""",
        }],
    )

    return response.content[0].text.strip()


async def rewrite_batch(
    messages: dict[str, str],
    profile: MetaprogramProfile,
    api_key: str,
) -> dict[str, str]:
    """
    Rewrite multiple messages at once (more efficient than one at a time).

    Args:
        messages: {"welcome": "Welcome to...", "cta": "Sign up now", ...}
        profile: Detected profile

    Returns:
        {"welcome": "rewritten...", "cta": "rewritten...", ...}
    """
    profile_desc = []
    for name, score in profile.scores.items():
        if score.confidence >= 0.2:
            profile_desc.append(f"- {name}: {score.winner}")

    if not profile_desc:
        return messages

    messages_text = "\n\n".join(
        f"[{key}]\n{text}" for key, text in messages.items()
    )

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=REWRITE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Rewrite ALL of these messages to match this person's style.
Return as JSON with the same keys.

THEIR PROFILE:
{chr(10).join(profile_desc)}

MESSAGES:
{messages_text}

Return JSON only: {{"key": "rewritten text", ...}}""",
        }],
    )

    try:
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return messages


# ═══════════════════════════════════════════════════════════════
# TEMPLATE REWRITER (no API needed — instant, free)
# ═══════════════════════════════════════════════════════════════
#
# For when you need INSTANT rewrites without an API call.
# Uses pre-written templates for common messages.
# Less nuanced than AI rewriting but 0ms latency and $0 cost.

TEMPLATE_VARIANTS = {
    "welcome": {
        "toward-internal": "Welcome. Here's your dashboard — make it yours.",
        "toward-external": "Welcome! Join 50,000 people who already transformed their {area}.",
        "away_from-internal": "No more {problem}. You're in control now.",
        "away_from-external": "87% of people with your {problem} fixed it in the first week. You're next.",
        "toward-procedures": "Welcome! Here's your 3-step setup — takes 2 minutes.",
        "away_from-procedures": "Let's fix {problem}. Step 1 is already done — you showed up.",
        "toward-options": "Welcome! Three ways to get started — pick what excites you.",
        "away_from-options": "A few ways to tackle {problem} — pick whichever feels right.",
    },
    "cta": {
        "toward": "Let's build this →",
        "away_from": "Fix it now →",
        "procedures": "Start step 1 →",
        "options": "See your options →",
        "proactive": "Let's go →",
        "reactive": "I'm ready →",
    },
    "savings_notification": {
        "toward": "You saved ${amount} this month! That's ${amount} closer to your goal.",
        "away_from": "You avoided ${amount} in wasteful spending this month.",
        "internal": "Your ${amount} savings — your strategy is working.",
        "external": "You saved ${amount} — that's more than 73% of users this month.",
    },
}


def instant_rewrite(
    template_key: str,
    profile: MetaprogramProfile,
    variables: Optional[dict] = None,
) -> str:
    """
    Instant template-based rewrite. No API call. 0ms.

    Falls back to the first available variant if exact match not found.
    """
    variables = variables or {}
    templates = TEMPLATE_VARIANTS.get(template_key, {})

    if not templates:
        return ""

    # Try to find best matching template
    # Priority: most specific match first
    confident = profile.confident_profile

    # Build candidate keys from profile
    candidates = []
    values = list(confident.values())

    # Try pairs first (most specific)
    for i, v1 in enumerate(values):
        for v2 in values[i + 1:]:
            candidates.append(f"{v1}-{v2}")
            candidates.append(f"{v2}-{v1}")

    # Then singles
    candidates.extend(values)

    # Find first matching template
    for candidate in candidates:
        if candidate in templates:
            text = templates[candidate]
            for key, val in variables.items():
                text = text.replace(f"{{{key}}}", str(val))
            return text

    # Fallback: first template
    text = list(templates.values())[0]
    for key, val in variables.items():
        text = text.replace(f"{{{key}}}", str(val))
    return text
