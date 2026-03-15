"""
Ingestion Sequence Generator — builds complete channel-specific decision trees
that detect metaprograms through GENUINE conversation, not qualification funnels.

THE CORE PROBLEM THIS SOLVES:
If someone feels like they're being sold to, they answer with their SALES
DEFENSE metaprogram — not their real one. Your entire funnel is then built on
a fake profile. Every "personalized" message feels MORE generic than random
guessing because you're speaking toward-language to someone who's actually
away-from but told you toward because that's what they thought you wanted.

THE SOLUTION: Zero-Pressure Detection Environments
Every question must:
1. Feel like genuine curiosity or helpful conversation
2. Have NO "right" answer — both options are equally valid and appealing
3. Be about THEM and their real life — not about buying anything
4. Never reference the product, the sale, or what you want them to do
5. Detect a metaprogram from WHICHEVER answer they give

The kicker: either answer is correct. As long as they answer TRUTHFULLY,
you get the real metaprogram. But if the environment triggers their
"I'm being qualified" alarm, the data is garbage.

CHANNEL ADAPTERS:
Each channel has different constraints (char limits, reply mechanics, etc.)
but the same underlying detection tree. The adapter formats the tree for
that platform while preserving the zero-pressure environment.

USAGE:
    generator = IngestionSequenceGenerator()
    sequence = generator.generate(
        channel="instagram",
        topic="keto app",
        primary_meta="motivation",      # Toward / Away From
        secondary_meta="reference",     # Internal / External
        cta="download the app",
    )
    # Returns: full decision tree with pre-written copy at every node
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# AUTHENTICITY RULES — The engine's immune system against fake data
# ═══════════════════════════════════════════════════════════════

AUTHENTICITY_RULES = {
    "environment_rules": [
        "Question must feel like a conversation between friends, not an interview",
        "Never reference the product or service in the detection question",
        "Both answer options must be equally socially desirable — no 'right' answer",
        "Frame questions about THEIR life, not about buying decisions",
        "Use past tense ('what did you do when...') — harder to fake than hypotheticals",
        "Include a relatable scenario they've ACTUALLY experienced",
        "The question should make them WANT to answer because it's interesting",
        "Never use marketing language (exclusive, limited, amazing opportunity)",
        "Questions should feel like a personality quiz, not a sales funnel",
        "If either answer would make someone feel judged, the question is bad",
    ],
    "red_flags": [
        "Question mentions the product or service",
        "One answer is clearly 'better' or more aspirational",
        "Question uses future tense about buying/signing up",
        "Question is about preferences for receiving marketing",
        "Question feels like a survey or form",
        "The 'real' answer is obvious (social desirability bias)",
        "Question references money, price, or budget",
        "Question asks them to rank or rate something",
    ],
    "truth_amplifiers": [
        "Use 'honestly, which is more you?' framing",
        "Reference specific daily scenarios they'll recognize",
        "Make both options equally funny/relatable",
        "Ask about what they ACTUALLY DO, not what they SHOULD do",
        "Include a small self-deprecating element in both options",
        "Frame as 'there's no wrong answer, we're just curious'",
        "Make the question something they'd screenshot and share",
        "Use 'this or that' format — fast, low commitment, fun",
    ],
}


# ═══════════════════════════════════════════════════════════════
# ZERO-PRESSURE DETECTION QUESTIONS
# ═══════════════════════════════════════════════════════════════
#
# These are the REAL questions — designed using the authenticity rules.
# Each question detects one metaprogram without the person knowing
# they're being profiled. Both answers are genuine. Neither is "better."
#
# The key: these are about LIFE, not about BUYING.
# They detect how someone processes information by asking about
# experiences everyone has had.
#
# Multiple variants per metaprogram so we can rotate and match
# to the channel/topic context without repeating.

ZERO_PRESSURE_QUESTIONS = {
    "motivation": {
        "description": "Toward vs Away From — are they pulled toward goals or pushed from pain?",
        "variants": [
            {
                "id": "morning_win",
                "hook": "Honest question —",
                "question": "When your morning goes perfectly, is it more like...",
                "option_a": {
                    "text": "Everything I planned is actually happening",
                    "subtext": "the stars aligned",
                    "detects": "toward",
                    "emoji": "✨",
                },
                "option_b": {
                    "text": "Nothing went wrong for once",
                    "subtext": "blessed silence",
                    "detects": "away_from",
                    "emoji": "😮‍💨",
                },
                "why_authentic": "Both are real experiences. Neither is aspirational. "
                                 "The toward person genuinely FEELS the first one. "
                                 "The away-from person genuinely FEELS the second. "
                                 "No one is performing.",
            },
            {
                "id": "weekend_energy",
                "hook": "Quick one —",
                "question": "When you have a free weekend with zero plans, you feel...",
                "option_a": {
                    "text": "Excited — so many things I COULD do",
                    "subtext": "possibility overload",
                    "detects": "toward",
                    "emoji": "🤩",
                },
                "option_b": {
                    "text": "Relieved — finally nothing I HAVE to do",
                    "subtext": "sweet freedom",
                    "detects": "away_from",
                    "emoji": "😌",
                },
                "why_authentic": "Same scenario, two genuine emotional responses. "
                                 "No one would judge either answer. Both are relatable.",
            },
            {
                "id": "friend_advice",
                "hook": "Be real —",
                "question": "When a friend asks for life advice, you usually say something like...",
                "option_a": {
                    "text": "Here's what you should try next",
                    "subtext": "forward motion",
                    "detects": "toward",
                    "emoji": "🚀",
                },
                "option_b": {
                    "text": "Here's what you should stop doing",
                    "subtext": "cut the dead weight",
                    "detects": "away_from",
                    "emoji": "✂️",
                },
                "why_authentic": "This is about what they ALREADY DO with friends. "
                                 "Past behavior, not hypothetical buying. "
                                 "Both are valid advice-giving styles.",
            },
            {
                "id": "new_year",
                "hook": "Real talk —",
                "question": "Your New Year's energy is usually more...",
                "option_a": {
                    "text": "This is MY year, let's build something",
                    "subtext": "vision board energy",
                    "detects": "toward",
                    "emoji": "🔥",
                },
                "option_b": {
                    "text": "Last year was rough, this year I'm protecting my peace",
                    "subtext": "boundary setting era",
                    "detects": "away_from",
                    "emoji": "🛡️",
                },
                "why_authentic": "Both are culturally valid. 'Boundary setting era' is "
                                 "just as socially celebrated as 'vision board energy.' "
                                 "Neither answer makes you look bad.",
            },
        ],
    },
    "reference": {
        "description": "Internal vs External — do they trust their own judgment or look to others?",
        "variants": [
            {
                "id": "restaurant_pick",
                "hook": "Settle this —",
                "question": "When picking a restaurant you've never been to, you...",
                "option_a": {
                    "text": "Look at the menu and vibe and just know",
                    "subtext": "trust the gut",
                    "detects": "internal",
                    "emoji": "🎯",
                },
                "option_b": {
                    "text": "Check the reviews and what people ordered",
                    "subtext": "due diligence",
                    "detects": "external",
                    "emoji": "⭐",
                },
                "why_authentic": "Universal experience. Everyone picks restaurants. "
                                 "Both approaches are smart. Neither is 'better.' "
                                 "People answer this honestly because it's low stakes.",
            },
            {
                "id": "haircut",
                "hook": "Honestly —",
                "question": "Before a haircut or style change, you usually...",
                "option_a": {
                    "text": "Just tell them what I want, I already know",
                    "subtext": "I see the vision",
                    "detects": "internal",
                    "emoji": "💇",
                },
                "option_b": {
                    "text": "Save 47 Pinterest pics and ask friends",
                    "subtext": "research mode activated",
                    "detects": "external",
                    "emoji": "📌",
                },
                "why_authentic": "Self-deprecating humor in option B (47 pins) makes "
                                 "external feel fun, not weak. Option A isn't arrogant. "
                                 "Both are how real people actually behave.",
            },
            {
                "id": "big_purchase",
                "hook": "Which one are you —",
                "question": "When buying something you've never bought before...",
                "option_a": {
                    "text": "I'll figure it out, how hard can it be",
                    "subtext": "confidence or delusion, either way",
                    "detects": "internal",
                    "emoji": "😎",
                },
                "option_b": {
                    "text": "I've watched 6 YouTube reviews already",
                    "subtext": "knowledge is power",
                    "detects": "external",
                    "emoji": "🎓",
                },
                "why_authentic": "The self-deprecating subtexts make BOTH answers "
                                 "equally funny. 'Confidence or delusion' normalizes "
                                 "the internal answer. '6 YouTube reviews' normalizes "
                                 "the external answer. No judgment either way.",
            },
        ],
    },
    "work_style": {
        "description": "Options vs Procedures — do they want choices or steps?",
        "variants": [
            {
                "id": "cooking",
                "hook": "This says everything about a person —",
                "question": "When you're cooking something new, you...",
                "option_a": {
                    "text": "Read the recipe then improvise based on vibes",
                    "subtext": "recipe is a suggestion",
                    "detects": "options",
                    "emoji": "🎨",
                },
                "option_b": {
                    "text": "Follow the recipe exactly, measure everything",
                    "subtext": "precision is love",
                    "detects": "procedures",
                    "emoji": "⚖️",
                },
                "why_authentic": "Cooking is universal and low-stakes. People KNOW "
                                 "which type they are and are usually proud of it. "
                                 "Chefs improvise. Bakers measure. Both are valid. "
                                 "This is a question people already debate with friends.",
            },
            {
                "id": "ikea",
                "hook": "Tell me I'm wrong —",
                "question": "IKEA furniture instructions, you...",
                "option_a": {
                    "text": "Look at the picture, wing it, fix mistakes later",
                    "subtext": "instructions are for quitters",
                    "detects": "options",
                    "emoji": "🔨",
                },
                "option_b": {
                    "text": "Step 1, then step 2, then step 3, no skipping",
                    "subtext": "chaos is the enemy",
                    "detects": "procedures",
                    "emoji": "📋",
                },
                "why_authentic": "IKEA is a meme everyone shares. This is already "
                                 "a conversation people have. The subtexts are funny "
                                 "enough that people WANT to claim their type. "
                                 "Neither answer is embarrassing.",
            },
            {
                "id": "learning",
                "hook": "Quick personality check —",
                "question": "When learning a new skill, you'd rather...",
                "option_a": {
                    "text": "Play around and figure it out by breaking stuff",
                    "subtext": "trial and error and error and error",
                    "detects": "options",
                    "emoji": "💥",
                },
                "option_b": {
                    "text": "Take the course, follow the curriculum, do it right",
                    "subtext": "there's a reason experts exist",
                    "detects": "procedures",
                    "emoji": "🎯",
                },
                "why_authentic": "Both are valid learning styles backed by research. "
                                 "The self-deprecating subtexts equalize status.",
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# CHANNEL ADAPTERS
# ═══════════════════════════════════════════════════════════════

class Channel(str, Enum):
    INSTAGRAM = "instagram"
    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    SHORTS = "shorts"           # YouTube Shorts / TikTok / Reels
    X = "x"                     # Twitter/X


@dataclass
class ChannelConstraints:
    """Platform-specific limits and mechanics."""
    name: str
    max_hook_length: int        # Characters for the initial hook post
    max_reply_length: int       # Characters for each reply/DM
    capture_method: str         # How you capture the response
    reply_format: str           # How replies work
    supports_emoji: bool
    supports_images: bool
    dm_available: bool
    thread_available: bool
    detection_flow: str         # How detection works on this platform
    notes: list[str] = field(default_factory=list)


CHANNEL_SPECS = {
    Channel.INSTAGRAM: ChannelConstraints(
        name="Instagram",
        max_hook_length=2200,
        max_reply_length=1000,
        capture_method="DM trigger — 'DM me X'",
        reply_format="DM sequence after trigger word",
        supports_emoji=True,
        supports_images=True,
        dm_available=True,
        thread_available=False,
        detection_flow=(
            "Post/Reel with 2-option CTA → user DMs trigger word → "
            "auto-reply with detection question → detect from answer → "
            "adapted DM sequence → CTA"
        ),
        notes=[
            "The trigger word itself can be a detection moment — "
            "offer two trigger words that map to metaprogram poles",
            "Stories polls are PERFECT zero-pressure detection — "
            "people tap without thinking (honest responses)",
            "Reels comments are public — keep detection in DMs for privacy",
        ],
    ),
    Channel.EMAIL: ChannelConstraints(
        name="Email",
        max_hook_length=5000,
        max_reply_length=5000,
        capture_method="Reply or click-through link",
        reply_format="Reply chain or click-tracked links",
        supports_emoji=True,
        supports_images=True,
        dm_available=False,
        thread_available=True,
        detection_flow=(
            "Subject line A/B (toward vs away) → open = initial signal → "
            "email body with 2 click options → click = detection → "
            "adapted email sequence based on detected profile"
        ),
        notes=[
            "Subject line open rate IS a detection signal — "
            "toward subjects ('unlock X') vs away ('stop X')",
            "Click behavior is the most honest signal in email — "
            "they click what genuinely interests them, not what sounds good",
            "Can use 2-link detection: both links go to same page but "
            "the URL tracks which framing they preferred",
        ],
    ),
    Channel.LANDING_PAGE: ChannelConstraints(
        name="Landing Page",
        max_hook_length=10000,
        max_reply_length=10000,
        capture_method="Button/form choice",
        reply_format="Routed to adapted page variant",
        supports_emoji=True,
        supports_images=True,
        dm_available=False,
        thread_available=False,
        detection_flow=(
            "Hero with 2 CTA buttons (each detects a metaprogram) → "
            "clicked button routes to adapted page → second choice on "
            "page 2 detects meta #2 → final page is fully adapted → CTA"
        ),
        notes=[
            "Button text IS the detection — 'Show me how' (procedures) "
            "vs 'What are my options' (options)",
            "Scroll depth + time-on-section is passive detection data",
            "Interactive quiz format works best — feels like a tool, not a funnel",
            "Each 'page' in the flow can be a modal or accordion — "
            "doesn't need actual page navigation",
        ],
    ),
    Channel.SHORTS: ChannelConstraints(
        name="YouTube Shorts / TikTok / Reels",
        max_hook_length=300,
        max_reply_length=300,
        capture_method="Comment trigger → DM sequence",
        reply_format="Comment reply → bio link or DM",
        supports_emoji=True,
        supports_images=False,
        dm_available=True,
        thread_available=False,
        detection_flow=(
            "Video with 2-option CTA ('comment A or B') → "
            "comment itself is detection → auto-DM or bio link → "
            "adapted landing page or DM sequence"
        ),
        notes=[
            "Short-form video CTA: 'Are you team A or team B? "
            "Comment and I'll send you the version that fits'",
            "The comment itself IS the honest answer — "
            "people comment fast without overthinking",
            "Video script should present both options as equally cool",
        ],
    ),
    Channel.X: ChannelConstraints(
        name="X (Twitter)",
        max_hook_length=280,
        max_reply_length=280,
        capture_method="Reply or poll vote",
        reply_format="Reply thread → DM",
        supports_emoji=True,
        supports_images=True,
        dm_available=True,
        thread_available=True,
        detection_flow=(
            "Tweet with poll or 'reply A or B' → poll/reply = detection → "
            "DM sequence adapted to their profile → CTA"
        ),
        notes=[
            "X polls are IDEAL zero-pressure detection — anonymous, fast, fun",
            "Quote-tweet the poll with the detection question for reach",
            "Reply threads let you do multi-step detection publicly "
            "(each reply is a new detection question)",
            "280 char limit forces concise questions — actually better "
            "for authenticity (no room for sales language)",
        ],
    ),
}


# ═══════════════════════════════════════════════════════════════
# SEQUENCE TREE — The decision tree structure
# ═══════════════════════════════════════════════════════════════

@dataclass
class SequenceNode:
    """A single node in the decision tree."""
    id: str
    node_type: str                  # "hook", "detection", "adapted_message", "cta"
    content: str                    # The actual copy for this node
    detects_metaprogram: Optional[str] = None  # Which metaprogram this detects
    detected_value: Optional[str] = None       # What was detected ("toward", "away_from", etc)
    children: list[SequenceNode] = field(default_factory=list)
    channel_notes: str = ""        # Channel-specific implementation notes
    authenticity_score: str = ""   # Why this node is authentic
    profile_so_far: dict = field(default_factory=dict)  # Cumulative profile at this point

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "type": self.node_type,
            "content": self.content,
        }
        if self.detects_metaprogram:
            result["detects"] = self.detects_metaprogram
        if self.detected_value:
            result["detected_value"] = self.detected_value
        if self.channel_notes:
            result["channel_notes"] = self.channel_notes
        if self.authenticity_score:
            result["authenticity_note"] = self.authenticity_score
        if self.profile_so_far:
            result["profile_so_far"] = self.profile_so_far
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        return result


@dataclass
class IngestionSequence:
    """Complete decision tree for a channel + topic combo."""
    channel: Channel
    topic: str
    primary_meta: str
    secondary_meta: str
    cta: str
    root: SequenceNode
    total_nodes: int = 0
    total_endpoints: int = 0     # How many unique adapted CTAs
    metaprograms_detected: list[str] = field(default_factory=list)
    channel_constraints: Optional[ChannelConstraints] = None

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.value,
            "topic": self.topic,
            "primary_meta": self.primary_meta,
            "secondary_meta": self.secondary_meta,
            "cta": self.cta,
            "total_nodes": self.total_nodes,
            "total_endpoints": self.total_endpoints,
            "metaprograms_detected": self.metaprograms_detected,
            "channel_constraints": {
                "name": self.channel_constraints.name,
                "max_hook_length": self.channel_constraints.max_hook_length,
                "capture_method": self.channel_constraints.capture_method,
                "detection_flow": self.channel_constraints.detection_flow,
            } if self.channel_constraints else None,
            "tree": self.root.to_dict(),
            "authenticity_rules": AUTHENTICITY_RULES,
        }


# ═══════════════════════════════════════════════════════════════
# ADAPTED COPY TEMPLATES
# ═══════════════════════════════════════════════════════════════
#
# Pre-written copy for each metaprogram combo.
# The topic gets inserted at generation time.
# These are the REAL messages people see after detection.

def _get_adapted_cta(profile: dict, topic: str, cta: str) -> str:
    """
    Generate adapted CTA copy based on detected profile.

    Uses the 4-level dominance spectrum:
    - Pure: speak ONLY in that frame
    - Dominant: LEAD with dominant, FOLLOW with secondary
    The order of framing matters more than the words.
    """
    motivation = profile.get("motivation", "toward")
    reference = profile.get("reference", "internal")
    # dominance_level is included when available (from detection engine)
    # If not available (from simple question answers), default to level 2/3 (dominant)
    motivation_level = profile.get("motivation_level", 2 if motivation == "toward" else 3)

    # ─── MOTIVATION × REFERENCE MATRIX WITH DOMINANCE ───
    # Pure toward (level 1): only gains, no pain mention
    # Dominant toward (level 2): lead gains, follow with "and you won't have to deal with..."
    # Dominant away (level 3): lead pain, follow with "and you'll end up with..."
    # Pure away (level 4): only pain/problems, no aspirational language

    if motivation_level == 1:
        # PURE TOWARD — aspirational only
        if reference == "internal":
            return (
                f"You see the vision. "
                f"Here's the {topic} approach that puts you in the driver's seat — "
                f"{cta} and build it your way."
            )
        else:
            return (
                f"Thousands of people are already hitting their goals with this {topic} system. "
                f"Here's what's working — {cta} and join them."
            )

    elif motivation_level == 2:
        # DOMINANT TOWARD — lead with gains, follow with pain avoided
        if reference == "internal":
            return (
                f"You've got a clear picture of what you want. "
                f"Here's the {topic} approach that puts you in control — "
                f"and you'll never have to deal with the old way again. "
                f"{cta} and make it yours."
            )
        else:
            return (
                f"People are using this {topic} system to hit their goals — "
                f"and leaving behind the frustration they used to deal with. "
                f"Here's what's working — {cta} and join them."
            )

    elif motivation_level == 3:
        # DOMINANT AWAY — lead with pain, follow with what they gain
        if reference == "internal":
            return (
                f"You already know what's not working. "
                f"Here's the {topic} fix that gets rid of that headache — "
                f"and puts you in a much better position going forward. "
                f"{cta} and take it from here."
            )
        else:
            return (
                f"87% of people dealing with the same {topic} frustration fixed it in the first week — "
                f"and ended up ahead of where they started. "
                f"Here's exactly what they did — {cta} to see the breakdown."
            )

    else:
        # PURE AWAY (level 4) — pain/problems only, no aspirational
        if reference == "internal":
            return (
                f"You know what's broken. "
                f"Here's the {topic} fix — no fluff, just the solution. "
                f"{cta} and stop dealing with it."
            )
        else:
            return (
                f"87% of people with this exact {topic} problem fixed it in under a week. "
                f"Here's how they stopped the bleeding — {cta} to see the breakdown."
            )


def _get_adapted_dm_opener(profile: dict, topic: str) -> str:
    """Generate the first DM message after detection."""
    motivation = profile.get("motivation", "toward")

    if motivation == "toward":
        return (
            f"Hey! Love that you're interested in {topic}. "
            f"Quick question to make sure I send you the right thing — "
        )
    else:
        return (
            f"Hey! Glad you reached out about {topic}. "
            f"Want to make sure I help with the right thing — "
        )


def _get_adapted_followup(profile: dict, topic: str) -> str:
    """
    Generate follow-up message after second detection.

    Uses lead/follow dominance pattern:
    - Dominant toward + secondary away: "Here's what you'll build... and you won't
      have to deal with X anymore"
    - Dominant away + secondary toward: "Stop dealing with X... and start building Y"
    """
    motivation = profile.get("motivation", "toward")
    reference = profile.get("reference", "internal")
    work_style = profile.get("work_style", "options")
    motivation_level = profile.get("motivation_level", 2 if motivation == "toward" else 3)

    # ─── LEAD/FOLLOW MOTIVATION FRAMING ───
    if motivation_level in (1, 2):  # Pure or dominant toward
        if reference == "internal":
            if motivation_level == 1:
                base = f"You clearly know what you want. "
            else:
                base = f"You know what you want — and what you're done putting up with. "
        else:
            if motivation_level == 1:
                base = f"Here's what people like you are building right now. "
            else:
                base = f"Here's what people like you are building — and what they left behind. "
    else:  # Pure or dominant away
        if reference == "internal":
            if motivation_level == 4:
                base = f"You know exactly what's not working. Let's fix it. "
            else:
                base = f"You know what's bugging you — and you're ready for something better. "
        else:
            if motivation_level == 4:
                base = f"Most people with this exact problem solved it like this. "
            else:
                base = f"Most people with this problem solved it — and ended up ahead. "

    # ─── WORK STYLE FRAMING ───
    if work_style == "options":
        base += f"I've got 3 different {topic} approaches — pick the one that fits your style."
    else:
        base += f"Here's the exact {topic} process, step by step. Ready?"

    return base


# ═══════════════════════════════════════════════════════════════
# THE GENERATOR — builds the full decision tree
# ═══════════════════════════════════════════════════════════════

class IngestionSequenceGenerator:
    """
    Builds complete channel-specific decision trees for metaprogram detection.

    The tree is a conversation disguised as a decision tree.
    Each node looks like a normal human interaction but is actually:
    1. A detection step (reveals a metaprogram from their answer)
    2. An adapted message (speaks in their detected frame)

    Both packed into one natural exchange.
    """

    def __init__(self):
        self.questions = ZERO_PRESSURE_QUESTIONS
        self.channel_specs = CHANNEL_SPECS

    def generate(
        self,
        channel: str | Channel,
        topic: str,
        primary_meta: str = "motivation",
        secondary_meta: str = "reference",
        cta: str = "check it out",
        tertiary_meta: Optional[str] = "work_style",
        question_variant: Optional[int] = None,
    ) -> IngestionSequence:
        """
        Generate a complete ingestion sequence.

        Args:
            channel: Which platform (instagram, email, landing_page, shorts, x)
            topic: What you're selling/promoting (e.g., "keto app", "vibe coding course")
            primary_meta: First metaprogram to detect (default: motivation)
            secondary_meta: Second metaprogram to detect (default: reference)
            cta: What you want them to do (e.g., "download the app", "book a call")
            tertiary_meta: Optional third metaprogram to detect
            question_variant: Which question variant to use (index). Random if None.

        Returns:
            IngestionSequence with the full decision tree
        """
        if isinstance(channel, str):
            channel = Channel(channel)

        constraints = self.channel_specs[channel]

        # Pick question variants
        import random
        primary_q = self._pick_question(primary_meta, question_variant)
        secondary_q = self._pick_question(secondary_meta, question_variant)

        # Build the tree
        root = self._build_hook_node(channel, topic, primary_q, constraints)

        # Branch on primary metaprogram (2 branches)
        for pole_key in ["option_a", "option_b"]:
            pole = primary_q[pole_key]
            profile_so_far = {primary_meta: pole["detects"]}

            # Detection acknowledgment + second question
            detection_node = self._build_detection_node(
                channel=channel,
                topic=topic,
                detected_meta=primary_meta,
                detected_value=pole["detects"],
                next_question=secondary_q,
                profile_so_far=profile_so_far,
                constraints=constraints,
            )

            # Branch on secondary metaprogram (2 branches each = 4 total)
            for secondary_pole_key in ["option_a", "option_b"]:
                secondary_pole = secondary_q[secondary_pole_key]
                full_profile = {
                    primary_meta: pole["detects"],
                    secondary_meta: secondary_pole["detects"],
                }

                # Build adapted message + CTA for this combo
                adapted_node = self._build_adapted_node(
                    channel=channel,
                    topic=topic,
                    profile=full_profile,
                    cta=cta,
                    constraints=constraints,
                )

                # If we have a tertiary meta, add one more branch level
                if tertiary_meta and tertiary_meta in self.questions:
                    tertiary_q = self._pick_question(tertiary_meta, question_variant)
                    # The adapted node becomes a bridge to the tertiary question
                    for t_pole_key in ["option_a", "option_b"]:
                        t_pole = tertiary_q[t_pole_key]
                        deep_profile = {
                            **full_profile,
                            tertiary_meta: t_pole["detects"],
                        }

                        final_node = self._build_final_cta_node(
                            channel=channel,
                            topic=topic,
                            profile=deep_profile,
                            cta=cta,
                            constraints=constraints,
                        )
                        adapted_node.children.append(final_node)

                detection_node.children.append(adapted_node)

            root.children.append(detection_node)

        # Count nodes
        total_nodes = self._count_nodes(root)
        total_endpoints = self._count_endpoints(root)
        detected_metas = [primary_meta, secondary_meta]
        if tertiary_meta:
            detected_metas.append(tertiary_meta)

        return IngestionSequence(
            channel=channel,
            topic=topic,
            primary_meta=primary_meta,
            secondary_meta=secondary_meta,
            cta=cta,
            root=root,
            total_nodes=total_nodes,
            total_endpoints=total_endpoints,
            metaprograms_detected=detected_metas,
            channel_constraints=constraints,
        )

    def _pick_question(self, metaprogram: str, variant_idx: Optional[int] = None) -> dict:
        """Pick a question variant for a metaprogram."""
        import random
        if metaprogram not in self.questions:
            raise ValueError(f"Unknown metaprogram: {metaprogram}. "
                             f"Available: {list(self.questions.keys())}")
        variants = self.questions[metaprogram]["variants"]
        if variant_idx is not None and 0 <= variant_idx < len(variants):
            return variants[variant_idx]
        return random.choice(variants)

    def _build_hook_node(
        self,
        channel: Channel,
        topic: str,
        primary_question: dict,
        constraints: ChannelConstraints,
    ) -> SequenceNode:
        """Build the initial hook post/message."""
        q = primary_question

        if channel == Channel.INSTAGRAM:
            content = (
                f"{q['hook']}\n\n"
                f"{q['question']}\n\n"
                f"{q['option_a']['emoji']} {q['option_a']['text']}\n"
                f"{q['option_b']['emoji']} {q['option_b']['text']}\n\n"
                f"DM me '{q['option_a']['emoji']}' or '{q['option_b']['emoji']}' "
                f"and I'll send you something cool about {topic} "
                f"that actually matches how YOU think."
            )
            channel_notes = (
                "Post as a carousel, Reel, or Story with poll sticker. "
                "The DM trigger word is the detection moment. "
                "Stories polls are the MOST authentic — people tap without overthinking."
            )
        elif channel == Channel.EMAIL:
            content = (
                f"Subject: {q['hook']} {q['question']}\n\n"
                f"Hey,\n\n"
                f"Quick question (for real, I'm curious):\n\n"
                f"{q['question']}\n\n"
                f"[BUTTON A] {q['option_a']['emoji']} {q['option_a']['text']}\n"
                f"[BUTTON B] {q['option_b']['emoji']} {q['option_b']['text']}\n\n"
                f"Click one — I'll send you {topic} stuff that actually "
                f"matches your style. Not generic advice."
            )
            channel_notes = (
                "Both buttons link to the same page but with different URL params "
                "(?meta=toward vs ?meta=away_from). The click IS the detection. "
                "No form. No quiz. Just a click."
            )
        elif channel == Channel.LANDING_PAGE:
            content = (
                f"<hero>\n"
                f"<h1>{q['hook']} {q['question']}</h1>\n"
                f"<button data-detects='{q['option_a']['detects']}'>"
                f"{q['option_a']['emoji']} {q['option_a']['text']}</button>\n"
                f"<button data-detects='{q['option_b']['detects']}'>"
                f"{q['option_b']['emoji']} {q['option_b']['text']}</button>\n"
                f"<p class='subtext'>Pick one — we'll show you {topic} "
                f"content that actually fits how you think.</p>\n"
                f"</hero>"
            )
            channel_notes = (
                "Interactive hero section. Both buttons route to different page variants. "
                "No form yet — just a choice. Feels like a tool, not a funnel. "
                "The subtext establishes value exchange: 'you tell me about you, "
                "I give you better stuff.'"
            )
        elif channel == Channel.SHORTS:
            content = (
                f"[VIDEO SCRIPT]\n\n"
                f"{q['hook']}\n\n"
                f"{q['question']}\n\n"
                f"Comment {q['option_a']['emoji']} if {q['option_a']['text'].lower()}\n"
                f"Comment {q['option_b']['emoji']} if {q['option_b']['text'].lower()}\n\n"
                f"I'll DM you something about {topic} that matches your answer.\n\n"
                f"[END SCRIPT]"
            )
            channel_notes = (
                "Keep the video under 60 seconds. Present both options "
                "as equally cool — no favoritism in tone or screen time. "
                "The comment is the most honest response: people comment fast."
            )
        elif channel == Channel.X:
            # Respect 280 char limit
            content = (
                f"{q['hook']} {q['question']}\n\n"
                f"{q['option_a']['emoji']} {q['option_a']['text']}\n"
                f"{q['option_b']['emoji']} {q['option_b']['text']}\n\n"
                f"Reply and I'll DM you something about {topic} "
                f"that actually fits."
            )
            channel_notes = (
                "Use X poll feature if possible — most honest responses. "
                "Polls are anonymous so people answer genuinely. "
                "280 char limit actually HELPS authenticity — no room for sales language."
            )
        else:
            content = f"{q['hook']} {q['question']}"
            channel_notes = ""

        return SequenceNode(
            id=f"hook_{channel.value}",
            node_type="hook",
            content=content,
            detects_metaprogram=q.get("detects_metaprogram", primary_question.get("id", "")),
            channel_notes=channel_notes,
            authenticity_score=q.get("why_authentic", ""),
        )

    def _build_detection_node(
        self,
        channel: Channel,
        topic: str,
        detected_meta: str,
        detected_value: str,
        next_question: dict,
        profile_so_far: dict,
        constraints: ChannelConstraints,
    ) -> SequenceNode:
        """Build the node that acknowledges first detection and asks the second question."""
        opener = _get_adapted_dm_opener(profile_so_far, topic)
        q = next_question

        content = (
            f"{opener}\n\n"
            f"{q['question']}\n\n"
            f"{q['option_a']['emoji']} {q['option_a']['text']}\n"
            f"{q['option_b']['emoji']} {q['option_b']['text']}"
        )

        return SequenceNode(
            id=f"detect_{detected_meta}_{detected_value}",
            node_type="detection",
            content=content,
            detects_metaprogram=detected_meta,
            detected_value=detected_value,
            profile_so_far=profile_so_far,
            authenticity_score=(
                f"At this point we know their {detected_meta} is '{detected_value}'. "
                f"The opener is already adapted to their frame. "
                f"The second question continues the conversational tone — "
                f"still zero pressure, still about them, not about buying."
            ),
        )

    def _build_adapted_node(
        self,
        channel: Channel,
        topic: str,
        profile: dict,
        cta: str,
        constraints: ChannelConstraints,
    ) -> SequenceNode:
        """Build a fully adapted message for a 2-meta profile combo."""
        followup = _get_adapted_followup(profile, topic)

        meta_keys = list(profile.keys())
        meta_values = list(profile.values())
        combo_id = "_".join(f"{k}_{v}" for k, v in profile.items())

        return SequenceNode(
            id=f"adapted_{combo_id}",
            node_type="adapted_message",
            content=followup,
            profile_so_far=profile,
            authenticity_score=(
                f"This message is fully adapted to profile: {profile}. "
                f"The language, framing, and structure all match their "
                f"detected communication preferences. They don't know "
                f"why this message feels right — it just does."
            ),
        )

    def _build_final_cta_node(
        self,
        channel: Channel,
        topic: str,
        profile: dict,
        cta: str,
        constraints: ChannelConstraints,
    ) -> SequenceNode:
        """Build the final CTA node adapted to the full profile."""
        cta_copy = _get_adapted_cta(profile, topic, cta)
        combo_id = "_".join(f"{k}_{v}" for k, v in profile.items())

        return SequenceNode(
            id=f"cta_{combo_id}",
            node_type="cta",
            content=cta_copy,
            profile_so_far=profile,
            authenticity_score=(
                f"Final CTA adapted to full profile: {profile}. "
                f"By this point we have 2-3 metaprograms detected from "
                f"GENUINE responses. The CTA speaks their exact language. "
                f"It feels like this was written for them specifically — "
                f"because it was."
            ),
        )

    def _count_nodes(self, node: SequenceNode) -> int:
        """Count total nodes in the tree."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _count_endpoints(self, node: SequenceNode) -> int:
        """Count leaf nodes (final CTAs)."""
        if not node.children:
            return 1
        count = 0
        for child in node.children:
            count += self._count_endpoints(child)
        return count

    def list_channels(self) -> list[dict]:
        """Return available channels and their constraints."""
        return [
            {
                "id": ch.value,
                "name": spec.name,
                "max_hook_length": spec.max_hook_length,
                "capture_method": spec.capture_method,
                "detection_flow": spec.detection_flow,
                "dm_available": spec.dm_available,
                "notes": spec.notes,
            }
            for ch, spec in self.channel_specs.items()
        ]

    def list_metaprograms(self) -> list[dict]:
        """Return available metaprograms and their question variants."""
        result = []
        for mp_name, mp_data in self.questions.items():
            result.append({
                "id": mp_name,
                "description": mp_data["description"],
                "variant_count": len(mp_data["variants"]),
                "variants": [
                    {
                        "id": v["id"],
                        "question": v["question"],
                        "option_a": v["option_a"]["text"],
                        "option_b": v["option_b"]["text"],
                    }
                    for v in mp_data["variants"]
                ],
            })
        return result

    def get_authenticity_rules(self) -> dict:
        """Return the authenticity rules for reference."""
        return AUTHENTICITY_RULES


# ═══════════════════════════════════════════════════════════════
# 4-LEVEL DOMINANCE SPECTRUM
# ═══════════════════════════════════════════════════════════════
#
# People are rarely 100% one pole. The 4 levels per metaprogram:
#
#   Level 1: PURE pole_a       → Talk ONLY in pole_a frame
#   Level 2: DOMINANT pole_a   → LEAD pole_a, FOLLOW pole_b
#   Level 3: DOMINANT pole_b   → LEAD pole_b, FOLLOW pole_a
#   Level 4: PURE pole_b       → Talk ONLY in pole_b frame
#
# Most people are levels 2 or 3. The messaging pattern:
#
#   Level 2 (dominant toward, secondary away):
#     "Here's what you'll build [toward] — and you'll never
#      deal with X again [away]"
#
#   Level 3 (dominant away, secondary toward):
#     "Stop dealing with X [away] — and start building Y [toward]"
#
# Same words. Different order. Completely different feeling.
#
# The extremes (levels 1 and 4) are rare but EASY to close
# because you just hammer one frame. Like the glass mismatcher
# story — pure mismatcher (level 4), so you just tell them
# they CAN'T have it and let them convince you.
#
# The magic is in levels 2 and 3 — the lead/follow sequence.
# That's where real skill comes in, and that's what the
# real-time coach (earpiece) trains you on.

DOMINANCE_LEVELS = {
    1: {
        "name": "pure_primary",
        "description": "Extreme — 85%+ one direction. Talk ONLY in that frame.",
        "messaging_pattern": "Single frame only. No mixing.",
        "coaching_tip": (
            "This person processes EVERYTHING through one lens. "
            "Don't add the other side — it'll feel off to them. "
            "Like the glass mismatcher: just say 'you can't have it' "
            "and let them convince you. Pure frames are easy once spotted."
        ),
    },
    2: {
        "name": "dominant_primary",
        "description": "Most common — 60-85% primary with secondary lean. Lead/follow pattern.",
        "messaging_pattern": "LEAD with primary frame, FOLLOW with secondary.",
        "coaching_tip": (
            "This is where most people live. The KEY is the ORDER. "
            "Say the primary thing FIRST — that's what hooks them. "
            "Then add the secondary angle — that's what seals it. "
            "Same words in reverse order would feel wrong to them."
        ),
    },
    3: {
        "name": "dominant_secondary",
        "description": "Common — 60-85% the other direction. Reverse lead/follow.",
        "messaging_pattern": "LEAD with secondary (now dominant), FOLLOW with primary.",
        "coaching_tip": (
            "Same skill as level 2 but reversed. "
            "The secondary pole is actually their dominant. "
            "Lead with THAT, follow with the other. "
            "Practice: say the away thing first, then the toward thing."
        ),
    },
    4: {
        "name": "pure_secondary",
        "description": "Extreme — 85%+ the other direction. Single frame only.",
        "messaging_pattern": "Single frame only. No mixing.",
        "coaching_tip": (
            "Same as level 1 but the other pole. "
            "Pure frames are the easiest to execute once you spot them. "
            "The challenge is spotting them — most people aren't extreme."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════
# REAL-TIME COACH — earpiece prompts for live conversation
# ═══════════════════════════════════════════════════════════════
#
# This is the system that listens to a live call, detects
# metaprograms in real time, and feeds you what to say next
# through an earpiece. After a few weeks of this, your brain
# starts doing it automatically.
#
# The coach output is SHORT — just enough to steer you.
# You're mid-conversation, you can't read paragraphs.

@dataclass
class CoachPrompt:
    """What the earpiece tells you in real time."""
    detected: str              # What was just detected
    dominance_level: int       # 1-4
    instruction: str           # Short coaching instruction (< 20 words)
    example_phrase: str        # Exact phrase to say or paraphrase
    lead_with: str             # The frame to open with
    follow_with: Optional[str] # The frame to add after (None for pure)


def generate_coach_prompt(
    metaprogram: str,
    detected_pole: str,
    dominance_level: int,
    topic: str,
) -> CoachPrompt:
    """
    Generate a real-time earpiece coaching prompt.

    This is what you'd hear through the earpiece while on a call:
    short, direct, actionable. No theory. Just "say this."
    """
    coach_phrases = {
        # MOTIVATION: Toward / Away From
        ("motivation", "toward", 1): CoachPrompt(
            detected="Pure toward",
            dominance_level=1,
            instruction="ALL gains. No problems. Only talk about what they'll build.",
            example_phrase=f"Imagine having {topic} completely dialed in.",
            lead_with="toward",
            follow_with=None,
        ),
        ("motivation", "toward", 2): CoachPrompt(
            detected="Dominant toward, secondary away",
            dominance_level=2,
            instruction="Lead with the goal, then mention what goes away.",
            example_phrase=f"Here's what {topic} gets you — and what you'll stop dealing with.",
            lead_with="toward",
            follow_with="away_from",
        ),
        ("motivation", "away_from", 3): CoachPrompt(
            detected="Dominant away, secondary toward",
            dominance_level=3,
            instruction="Lead with the pain point, then show the upside.",
            example_phrase=f"Let's fix the {topic} problem — and you'll end up way ahead.",
            lead_with="away_from",
            follow_with="toward",
        ),
        ("motivation", "away_from", 4): CoachPrompt(
            detected="Pure away",
            dominance_level=4,
            instruction="ALL pain/problems. No aspirational. Just fix it.",
            example_phrase=f"This {topic} issue? Here's how to make it stop.",
            lead_with="away_from",
            follow_with=None,
        ),
        # REFERENCE: Internal / External
        ("reference", "internal", 1): CoachPrompt(
            detected="Pure internal",
            dominance_level=1,
            instruction="Let THEM decide everything. Present data, not recommendations.",
            example_phrase=f"Here's the {topic} info — you'll know what's right for you.",
            lead_with="internal",
            follow_with=None,
        ),
        ("reference", "internal", 2): CoachPrompt(
            detected="Dominant internal, secondary external",
            dominance_level=2,
            instruction="Let them decide, then mention what others did.",
            example_phrase=f"You know your {topic} situation best — and others in your spot did X.",
            lead_with="internal",
            follow_with="external",
        ),
        ("reference", "external", 3): CoachPrompt(
            detected="Dominant external, secondary internal",
            dominance_level=3,
            instruction="Show social proof first, then hand them the reins.",
            example_phrase=f"87% of people chose this {topic} approach — but ultimately it's your call.",
            lead_with="external",
            follow_with="internal",
        ),
        ("reference", "external", 4): CoachPrompt(
            detected="Pure external",
            dominance_level=4,
            instruction="ALL social proof. Numbers, reviews, what experts say.",
            example_phrase=f"Everyone's using this {topic} system — rated 4.9 stars.",
            lead_with="external",
            follow_with=None,
        ),
        # WORK STYLE: Options / Procedures
        ("work_style", "options", 1): CoachPrompt(
            detected="Pure options",
            dominance_level=1,
            instruction="Only give choices. Never prescribe steps.",
            example_phrase=f"3 ways to approach {topic} — which feels right?",
            lead_with="options",
            follow_with=None,
        ),
        ("work_style", "options", 2): CoachPrompt(
            detected="Dominant options, secondary procedures",
            dominance_level=2,
            instruction="Give choices first, then offer a recommended path.",
            example_phrase=f"Here are your {topic} options — and here's the path most people take.",
            lead_with="options",
            follow_with="procedures",
        ),
        ("work_style", "procedures", 3): CoachPrompt(
            detected="Dominant procedures, secondary options",
            dominance_level=3,
            instruction="Give the steps first, then mention alternatives exist.",
            example_phrase=f"Here's the {topic} process step by step — and there are other ways if you want.",
            lead_with="procedures",
            follow_with="options",
        ),
        ("work_style", "procedures", 4): CoachPrompt(
            detected="Pure procedures",
            dominance_level=4,
            instruction="Only give steps. Don't offer choices — they want the answer.",
            example_phrase=f"Step 1 for {topic}: do this. Step 2: do that. Done.",
            lead_with="procedures",
            follow_with=None,
        ),
    }

    key = (metaprogram, detected_pole, dominance_level)
    if key in coach_phrases:
        return coach_phrases[key]

    # Fallback for unknown combos
    return CoachPrompt(
        detected=f"{detected_pole} (level {dominance_level})",
        dominance_level=dominance_level,
        instruction=f"Match their {detected_pole} frame for {topic}.",
        example_phrase=f"Let's talk about {topic} in a way that works for you.",
        lead_with=detected_pole,
        follow_with=None,
    )


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE — generate and dump to JSON
# ═══════════════════════════════════════════════════════════════

def generate_sequence_json(
    channel: str,
    topic: str,
    primary_meta: str = "motivation",
    secondary_meta: str = "reference",
    cta: str = "check it out",
    tertiary_meta: Optional[str] = "work_style",
) -> str:
    """Generate a sequence and return as JSON string."""
    gen = IngestionSequenceGenerator()
    seq = gen.generate(
        channel=channel,
        topic=topic,
        primary_meta=primary_meta,
        secondary_meta=secondary_meta,
        cta=cta,
        tertiary_meta=tertiary_meta,
    )
    return json.dumps(seq.to_dict(), indent=2)
