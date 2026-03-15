"""
Metaprogram Detector — analyzes text corpus and returns profile.

Speed target: <100ms for detection (scraping is the bottleneck, not this).

The detection is pure pattern matching + scoring. No AI API call needed.
This means it's FREE and INSTANT once we have the text.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from metascraper.patterns import METAPROGRAMS


@dataclass
class MetaprogramScore:
    """Score for a single metaprogram axis."""
    name: str  # e.g. "motivation"
    pole_a: str  # e.g. "toward"
    pole_b: str  # e.g. "away_from"
    score_a: float = 0.0
    score_b: float = 0.0

    @property
    def winner(self) -> str:
        if self.score_a > self.score_b:
            return self.pole_a
        elif self.score_b > self.score_a:
            return self.pole_b
        return "neutral"

    @property
    def confidence(self) -> float:
        """0.0 to 1.0 — how sure we are. Based on gap between scores."""
        total = self.score_a + self.score_b
        if total == 0:
            return 0.0
        gap = abs(self.score_a - self.score_b) / total
        return min(gap, 1.0)

    @property
    def strength(self) -> str:
        """Human-readable confidence level."""
        if self.confidence >= 0.6:
            return "strong"
        elif self.confidence >= 0.3:
            return "moderate"
        elif self.confidence > 0:
            return "weak"
        return "undetected"


@dataclass
class MetaprogramProfile:
    """Complete metaprogram profile for a person."""
    scores: dict[str, MetaprogramScore] = field(default_factory=dict)
    text_analyzed: int = 0  # chars of text analyzed
    detection_time_ms: int = 0
    source_count: int = 0

    @property
    def primary_profile(self) -> dict[str, str]:
        """The top-level profile — just the winners."""
        return {name: score.winner for name, score in self.scores.items()}

    @property
    def confident_profile(self) -> dict[str, str]:
        """Only metaprograms detected with moderate+ confidence."""
        return {
            name: score.winner
            for name, score in self.scores.items()
            if score.confidence >= 0.3
        }

    @property
    def profile_code(self) -> str:
        """
        Short code like "T-E-P" (Toward, External, Procedures).
        Only includes confident detections.
        """
        abbrev = {
            "toward": "T", "away_from": "AF",
            "internal": "I", "external": "E",
            "options": "O", "procedures": "P",
            "big_picture": "BP", "detail": "D",
            "proactive": "PR", "reactive": "RE",
            "neutral": "?",
        }
        parts = []
        for name in ["motivation", "reference", "work_style", "chunk_size", "action"]:
            if name in self.scores:
                winner = self.scores[name].winner
                parts.append(abbrev.get(winner, "?"))
        return "-".join(parts)

    @property
    def detection_quality(self) -> str:
        """Overall quality of the detection."""
        confident_count = sum(
            1 for s in self.scores.values() if s.confidence >= 0.3
        )
        if confident_count >= 3:
            return "excellent"
        elif confident_count >= 2:
            return "good"
        elif confident_count >= 1:
            return "partial"
        return "insufficient"

    def to_dict(self) -> dict:
        """JSON-serializable output."""
        return {
            "profile": self.primary_profile,
            "confident_profile": self.confident_profile,
            "profile_code": self.profile_code,
            "detection_quality": self.detection_quality,
            "details": {
                name: {
                    "result": score.winner,
                    "confidence": round(score.confidence, 2),
                    "strength": score.strength,
                    "score_a": round(score.score_a, 1),
                    "score_b": round(score.score_b, 1),
                }
                for name, score in self.scores.items()
            },
            "meta": {
                "text_analyzed_chars": self.text_analyzed,
                "detection_time_ms": self.detection_time_ms,
                "source_count": self.source_count,
            },
        }


# ═══════════════════════════════════════════════════════════════
# DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════

WEIGHTS = {"strong": 3.0, "medium": 2.0, "weak": 1.0}


def _score_patterns(text: str, patterns: dict[str, list[str]]) -> float:
    """Score text against a pattern set. Returns weighted score."""
    text_lower = text.lower()
    score = 0.0

    for strength, phrases in patterns.items():
        weight = WEIGHTS.get(strength, 1.0)
        for phrase in phrases:
            # Count occurrences (word boundary aware for short patterns)
            if len(phrase) <= 3:
                # Short patterns need word boundaries
                count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
            else:
                count = text_lower.count(phrase.lower())

            if count > 0:
                # Diminishing returns on repeat hits (log scale)
                # First hit = full weight, subsequent hits = less
                import math
                score += weight * (1 + math.log(count, 2))

    return score


def detect_metaprograms(
    text: str,
    source_count: int = 0,
    programs: Optional[list[str]] = None,
) -> MetaprogramProfile:
    """
    Detect metaprograms from text.

    Args:
        text: Combined text corpus to analyze
        source_count: How many sources contributed to the text
        programs: Optional list of specific metaprograms to detect.
                  Default: all 5. For speed, pass ["motivation", "reference", "work_style"]
                  to only detect the core 3.

    Returns:
        MetaprogramProfile with scores and profile code
    """
    import time
    start = time.monotonic()

    profile = MetaprogramProfile(
        text_analyzed=len(text),
        source_count=source_count,
    )

    if not text.strip():
        profile.detection_time_ms = 0
        return profile

    target_programs = programs or list(METAPROGRAMS.keys())

    for mp_name in target_programs:
        if mp_name not in METAPROGRAMS:
            continue

        mp = METAPROGRAMS[mp_name]
        score_a = _score_patterns(text, mp["pole_a"]["patterns"])
        score_b = _score_patterns(text, mp["pole_b"]["patterns"])

        profile.scores[mp_name] = MetaprogramScore(
            name=mp_name,
            pole_a=mp["pole_a"]["name"],
            pole_b=mp["pole_b"]["name"],
            score_a=score_a,
            score_b=score_b,
        )

    profile.detection_time_ms = int((time.monotonic() - start) * 1000)
    return profile


def detect_from_short_text(text: str) -> MetaprogramProfile:
    """
    Optimized detection for short text (one sentence, a bio, etc).
    Only detects the core 3 metaprograms since short text
    doesn't have enough signal for all 5.
    """
    return detect_metaprograms(
        text,
        source_count=1,
        programs=["motivation", "reference", "work_style"],
    )
