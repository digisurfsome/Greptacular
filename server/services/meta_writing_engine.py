"""
Metaprogram Writing Engine
===========================

Takes a detected metaprogram profile + the training library and generates
adapted copy for any channel, topic, and scenario.

This is NOT template-based. The training library gives the AI real examples
of how each type talks, what they respond to, and what language patterns
indicate each pole. The AI uses this as a "manual" to write copy that
speaks each person's exact language.

The more training material you feed it, the better the copy gets.
First upload = decent. 10 uploads = scary good. 50 uploads = Tony Robbins.

The engine has three modes:
1. GENERATE — write fresh copy for a profile + topic + channel
2. REWRITE — take existing copy and adapt it to a specific profile
3. COACH — generate real-time coaching prompts for a live conversation

All three draw from the same training library.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# WRITING ENGINE
# ═══════════════════════════════════════════════════════════════

WRITING_SYSTEM_PROMPT = """\
You are a metaprogram-adaptive copywriter. You write messages that speak to people
in THEIR unconscious communication frame — not generic marketing, but language
calibrated to how they process information.

You have been trained on real examples of how each metaprogram type talks,
what they respond to, and what language patterns signal each pole.

METAPROGRAMS AND 4-LEVEL DOMINANCE:

Each person has a position on each axis. Most are level 2 or 3 (dominant one
way with a secondary lean). The messaging rule:

Level 1 (Pure): Talk ONLY in that frame. No mixing.
Level 2 (Dominant): LEAD with dominant pole, FOLLOW with secondary.
Level 3 (Dominant other): LEAD with that pole, FOLLOW with the first.
Level 4 (Pure other): Talk ONLY in that frame. No mixing.

The ORDER matters more than the words. Same information, different sequence =
completely different feeling.

AXES:
- Motivation: Toward (gains/goals) vs Away From (pain/problems)
- Reference: Internal (own judgment) vs External (social proof/experts)
- Work Style: Options (choices/flexibility) vs Procedures (steps/structure)
- Chunk Size: Big Picture (overview/gist) vs Detail (specifics/numbers)
- Action: Proactive (make it happen) vs Reactive (handle as it comes)

RULES:
1. Never mention metaprograms, NLP, or psychology — just write naturally
2. Match their energy — don't write toward copy in away-from energy
3. The lead/follow order is CRITICAL — get it right or the copy feels off
4. Sound like a human who genuinely understands them, not a marketer
5. Use the training examples as reference — match the real patterns
6. Keep the same length unless asked otherwise
7. Adapt framing, not facts — same information, different frame

AUTHENTICITY RULES FOR DETECTION CONTENT:
- Both options must be equally socially desirable
- No "right" answer — both options are valid
- Questions about THEIR life, not about buying
- Past tense preferred (harder to fake than hypotheticals)
- Self-deprecating humor in both options equalizes status
"""


@dataclass
class WritingRequest:
    """What to write and for whom."""
    mode: str                           # "generate", "rewrite", "coach"
    profile: dict                       # {motivation: "toward", reference: "external", ...}
    topic: str                          # what it's about
    channel: str = "general"            # instagram, email, landing_page, etc
    existing_copy: str = ""             # for rewrite mode
    scenario: str = ""                  # for coach mode
    tone: str = "conversational"        # conversational, professional, casual, urgent
    length: str = "medium"              # short, medium, long
    include_cta: bool = True
    cta_action: str = "check it out"


@dataclass
class WritingResult:
    """Output from the writing engine."""
    copy: str                           # the generated text
    profile_used: dict                  # the profile that shaped the copy
    dominance_instructions: list[str]   # what lead/follow rules were applied
    training_examples_used: int         # how many training examples informed this
    mode: str
    channel: str

    def to_dict(self) -> dict:
        return {
            "copy": self.copy,
            "profile_used": self.profile_used,
            "dominance_instructions": self.dominance_instructions,
            "training_examples_used": self.training_examples_used,
            "mode": self.mode,
            "channel": self.channel,
        }


def _build_training_context(library_data: dict, profile: dict) -> str:
    """
    Build a training context string from the library that's relevant
    to the target profile.

    This is the "manual" the AI reads before writing.
    """
    sections = []

    # Get relevant examples
    examples = library_data.get("all_examples", [])
    relevant_examples = []
    for ex in examples:
        mp = ex.get("metaprogram", "")
        pole = ex.get("pole", "")
        if mp in profile and profile.get(mp) == pole:
            relevant_examples.append(ex)
        # Also include opposite pole examples so the AI knows what NOT to do
        elif mp in profile:
            relevant_examples.append(ex)

    if relevant_examples:
        sections.append("=== REAL EXAMPLES FROM TRAINING DATA ===")
        for ex in relevant_examples[:20]:  # Cap at 20
            sections.append(
                f"[{ex.get('metaprogram', '?')}: {ex.get('pole', '?')} "
                f"(level {ex.get('dominance_level', '?')})] "
                f'Quote: "{ex.get("quote", "")}" '
                f"— {ex.get('why_this_indicates', '')}"
            )
        sections.append("")

    # Get relevant type descriptions
    type_descs = library_data.get("all_type_descriptions", [])
    relevant_descs = [d for d in type_descs
                      if d.get("metaprogram") in profile
                      and d.get("pole") == profile.get(d.get("metaprogram"))]
    if relevant_descs:
        sections.append("=== HOW THIS TYPE TALKS AND WHAT THEY RESPOND TO ===")
        for desc in relevant_descs[:6]:
            sections.append(
                f"[{desc.get('metaprogram', '?')}: {desc.get('pole', '?')}]\n"
                f"  How they talk: {desc.get('how_they_talk', 'unknown')}\n"
                f"  What they respond to: {desc.get('what_they_respond_to', 'unknown')}"
            )
        sections.append("")

    # Get relevant language patterns
    patterns = library_data.get("all_patterns", [])
    relevant_patterns = [p for p in patterns
                         if p.get("metaprogram") in profile
                         and p.get("pole") == profile.get(p.get("metaprogram"))]
    if relevant_patterns:
        sections.append("=== LANGUAGE PATTERNS TO USE ===")
        for pat in relevant_patterns[:10]:
            phrases = ", ".join(pat.get("phrases", [])[:8])
            sections.append(
                f"[{pat.get('metaprogram', '?')}: {pat.get('pole', '?')} "
                f"({pat.get('strength', '?')})] "
                f"Phrases: {phrases}"
            )
        sections.append("")

    # Get relevant coaching scenarios
    scenarios = library_data.get("all_coaching_scenarios", [])
    relevant_scenarios = []
    for s in scenarios:
        detected = s.get("detected_profile", {})
        for mp, pole in detected.items():
            if profile.get(mp) == pole:
                relevant_scenarios.append(s)
                break
    if relevant_scenarios:
        sections.append("=== COACHING SCENARIOS (WHAT WORKS) ===")
        for s in relevant_scenarios[:8]:
            sections.append(
                f"Scenario: {s.get('scenario', '')}\n"
                f"  Say: {s.get('what_to_say', '')}\n"
                f"  Why: {s.get('why_it_works', '')}"
            )
        sections.append("")

    # Get raw insights
    insights = library_data.get("all_insights", [])
    if insights:
        sections.append("=== RAW INSIGHTS FROM TRAINING ===")
        for insight in insights[:10]:
            sections.append(f"- {insight}")

    return "\n".join(sections) if sections else "(No training data yet — using base knowledge)"


def _build_dominance_instructions(profile: dict) -> list[str]:
    """Build lead/follow instructions from profile dominance levels."""
    instructions = []

    # Map of metaprograms to their pole names
    pole_map = {
        "motivation": ("toward", "away_from"),
        "reference": ("internal", "external"),
        "work_style": ("options", "procedures"),
        "chunk_size": ("big_picture", "detail"),
        "action": ("proactive", "reactive"),
    }

    for mp, detected_pole in profile.items():
        if mp not in pole_map:
            continue
        pole_a, pole_b = pole_map[mp]
        level = profile.get(f"{mp}_level", 2 if detected_pole == pole_a else 3)

        if level == 1:
            instructions.append(f"{mp.upper()}: PURE {detected_pole} — only use {detected_pole} framing")
        elif level == 2:
            other = pole_b if detected_pole == pole_a else pole_a
            instructions.append(f"{mp.upper()}: LEAD with {detected_pole}, FOLLOW with {other}")
        elif level == 3:
            other = pole_a if detected_pole == pole_b else pole_b
            instructions.append(f"{mp.upper()}: LEAD with {detected_pole}, FOLLOW with {other}")
        elif level == 4:
            instructions.append(f"{mp.upper()}: PURE {detected_pole} — only use {detected_pole} framing")

    return instructions


async def generate_copy(request: WritingRequest) -> WritingResult:
    """
    Generate adapted copy using the training library.

    This is the main writing function. It:
    1. Loads the training library
    2. Builds a context of relevant examples/patterns for this profile
    3. Sends it to Claude with the writing system prompt
    4. Returns copy that speaks the target's exact language
    """
    from server.services.meta_training_ingestor import TrainingLibrary

    # Load training library
    library = TrainingLibrary.load()
    library_data = {
        "all_examples": library.all_examples,
        "all_type_descriptions": library.all_type_descriptions,
        "all_patterns": library.all_patterns,
        "all_coaching_scenarios": library.all_coaching_scenarios,
        "all_insights": library.all_insights,
    }

    # Build training context
    training_context = _build_training_context(library_data, request.profile)
    dominance_instructions = _build_dominance_instructions(request.profile)
    training_examples_used = sum(
        1 for section in training_context.split("\n")
        if section.startswith("[")
    )

    # Build the user prompt based on mode
    if request.mode == "generate":
        user_prompt = _build_generate_prompt(request, dominance_instructions, training_context)
    elif request.mode == "rewrite":
        user_prompt = _build_rewrite_prompt(request, dominance_instructions, training_context)
    elif request.mode == "coach":
        user_prompt = _build_coach_prompt(request, dominance_instructions, training_context)
    else:
        raise ValueError(f"Unknown mode: {request.mode}. Use 'generate', 'rewrite', or 'coach'.")

    # Call Claude
    import anthropic
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=WRITING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    copy = response.content[0].text.strip()

    return WritingResult(
        copy=copy,
        profile_used=request.profile,
        dominance_instructions=dominance_instructions,
        training_examples_used=training_examples_used,
        mode=request.mode,
        channel=request.channel,
    )


def _build_generate_prompt(
    request: WritingRequest,
    dominance_instructions: list[str],
    training_context: str,
) -> str:
    """Build prompt for fresh copy generation."""
    channel_notes = {
        "instagram": "Instagram post/DM. Keep it conversational. Emoji OK. Under 2200 chars.",
        "email": "Email. Include subject line. Professional but warm.",
        "landing_page": "Landing page section. Headline + body + CTA button text.",
        "shorts": "YouTube Shorts/TikTok script. Under 60 seconds. Hook in first 3 seconds.",
        "x": "Tweet or X thread. Under 280 chars per tweet. Punchy.",
        "dm": "Direct message. Casual, personal, like texting a friend.",
        "ad": "Ad copy. Hook → agitate → solve → CTA.",
        "general": "General purpose. Conversational tone.",
    }

    return f"""Write {request.length} {request.channel} copy about "{request.topic}"
for a person with this metaprogram profile:

PROFILE: {json.dumps(request.profile)}

DOMINANCE RULES (CRITICAL — get the order right):
{chr(10).join(f'- {inst}' for inst in dominance_instructions)}

CHANNEL: {channel_notes.get(request.channel, request.channel)}
TONE: {request.tone}
{"INCLUDE CTA: " + request.cta_action if request.include_cta else "NO CTA"}

TRAINING DATA (real examples and patterns — use these as reference):
{training_context}

Write the copy now. Just the copy, no explanations or labels."""


def _build_rewrite_prompt(
    request: WritingRequest,
    dominance_instructions: list[str],
    training_context: str,
) -> str:
    """Build prompt for rewriting existing copy."""
    return f"""Rewrite this copy to match the target profile.
Same information, same length, same facts — but framed in THEIR language.

ORIGINAL COPY:
{request.existing_copy}

TARGET PROFILE: {json.dumps(request.profile)}

DOMINANCE RULES (CRITICAL — get the order right):
{chr(10).join(f'- {inst}' for inst in dominance_instructions)}

CHANNEL: {request.channel}

TRAINING DATA (real examples and patterns — match these):
{training_context}

Rewritten copy (same info, their frame):"""


def _build_coach_prompt(
    request: WritingRequest,
    dominance_instructions: list[str],
    training_context: str,
) -> str:
    """Build prompt for real-time coaching output."""
    return f"""You're an earpiece coach feeding real-time instructions during a live conversation.

SITUATION: {request.scenario or f"Talking about {request.topic}"}
THEIR PROFILE: {json.dumps(request.profile)}

DOMINANCE RULES:
{chr(10).join(f'- {inst}' for inst in dominance_instructions)}

TRAINING DATA:
{training_context}

Give me:
1. ONE sentence of what to say RIGHT NOW (the exact phrase)
2. ONE sentence of why (so I learn the pattern)
3. What to lead with and what to follow with
4. A warning of what NOT to say (what would break rapport)

Keep it SHORT — I'm mid-conversation. No paragraphs.
Format:

SAY: "..."
WHY: ...
LEAD: ... → FOLLOW: ...
DON'T: ..."""


# ═══════════════════════════════════════════════════════════════
# BATCH GENERATION — write for ALL combos at once
# ═══════════════════════════════════════════════════════════════

async def generate_all_combos(
    topic: str,
    channel: str = "general",
    cta: str = "check it out",
    metaprograms: Optional[list[str]] = None,
    on_progress: Optional[callable] = None,
) -> dict:
    """
    Generate copy for every metaprogram combination.

    With 2 metaprograms × 4 dominance levels each = 16 variants.
    With 3 metaprograms × 2 poles each = 8 basic combos.

    Returns a dict keyed by profile code (e.g., "toward_internal_options").
    """
    if metaprograms is None:
        metaprograms = ["motivation", "reference", "work_style"]

    pole_map = {
        "motivation": ["toward", "away_from"],
        "reference": ["internal", "external"],
        "work_style": ["options", "procedures"],
        "chunk_size": ["big_picture", "detail"],
        "action": ["proactive", "reactive"],
    }

    # Build all combinations
    combos = [{}]
    for mp in metaprograms:
        if mp not in pole_map:
            continue
        new_combos = []
        for combo in combos:
            for pole in pole_map[mp]:
                new_combo = {**combo, mp: pole}
                new_combos.append(new_combo)
        combos = new_combos

    results = {}
    total = len(combos)

    for i, profile in enumerate(combos):
        combo_key = "_".join(f"{v}" for v in profile.values())

        if on_progress:
            on_progress(f"Generating {i+1}/{total}: {combo_key}")

        request = WritingRequest(
            mode="generate",
            profile=profile,
            topic=topic,
            channel=channel,
            cta_action=cta,
        )

        result = await generate_copy(request)
        results[combo_key] = result.to_dict()

    return {
        "topic": topic,
        "channel": channel,
        "total_variants": len(results),
        "metaprograms_used": metaprograms,
        "variants": results,
    }
