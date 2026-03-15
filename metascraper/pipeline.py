"""
MetaScraper Pipeline — the full chain from identity signal to personalized copy.

FLOW:
1. Identity signal arrives (OAuth login, email, or direct input)
2. Parallel scrape of all public surfaces (< 3 seconds)
3. Detect metaprograms from scraped text (< 100ms)
4. If confident on 3+ programs → done, use profile
5. If not → generate targeted questions (only for what's missing)
6. Rewrite any copy to match their profile (instant or AI-powered)

TOTAL TIME: 3-5 seconds from login to personalized first message.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

from metascraper.scraper import (
    IdentitySignal,
    ScrapedCorpus,
    scrape_all,
    extract_from_facebook_oauth,
    extract_from_google_oauth,
    extract_from_email,
)
from metascraper.detector import (
    MetaprogramProfile,
    detect_metaprograms,
    detect_from_short_text,
)
from metascraper.rewriter import (
    get_needed_questions,
    rewrite_message,
    instant_rewrite,
)


@dataclass
class PipelineResult:
    """Complete result from the metascraper pipeline."""
    identity: IdentitySignal
    profile: MetaprogramProfile
    corpus: Optional[ScrapedCorpus]
    needed_questions: list[dict]  # Questions still needed (if any)
    ready: bool  # True if profile is good enough to use
    total_time_ms: int

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "profile": self.profile.to_dict(),
            "profile_code": self.profile.profile_code,
            "detection_quality": self.profile.detection_quality,
            "sources_hit": self.corpus.source_names if self.corpus else [],
            "needed_questions": self.needed_questions,
            "total_time_ms": self.total_time_ms,
        }


async def run_pipeline(
    provider: Optional[str] = None,
    oauth_data: Optional[dict] = None,
    email: Optional[str] = None,
    hero_input: Optional[str] = None,
    scrape_timeout: float = 3.0,
) -> PipelineResult:
    """
    Full pipeline from any entry point.

    Entry points (pick one):
    - provider="facebook" + oauth_data={...} → Facebook login
    - provider="google" + oauth_data={...} → Google login
    - email="user@example.com" → Email capture
    - hero_input="I'm always broke" → Just the text they typed (minimum)

    The pipeline tries scraping first. If scraping gets enough signal,
    no questions needed. If not, it returns targeted questions for
    only the metaprograms it couldn't detect.
    """
    start = time.monotonic()

    # Step 1: Build identity signal
    if provider == "facebook" and oauth_data:
        identity = extract_from_facebook_oauth(oauth_data)
    elif provider == "google" and oauth_data:
        identity = extract_from_google_oauth(oauth_data)
    elif email:
        identity = extract_from_email(email)
    else:
        identity = IdentitySignal()

    # Step 2: Detect from hero input (immediate — no scraping needed)
    profile = MetaprogramProfile()
    if hero_input:
        profile = detect_from_short_text(hero_input)

    # Step 3: Scrape in parallel (if we have identity signals)
    corpus = None
    has_identity = identity.email or identity.full_name or identity.facebook_id
    if has_identity:
        corpus = await scrape_all(identity, timeout=scrape_timeout)

        if corpus.all_text:
            # Re-detect with full corpus (more signal = better detection)
            combined_text = hero_input + "\n" + corpus.all_text if hero_input else corpus.all_text
            profile = detect_metaprograms(
                combined_text,
                source_count=len(corpus.source_names),
            )

    # Step 4: Determine what questions we still need
    needed = get_needed_questions(profile)
    ready = len(needed) == 0  # Ready if core 3 are confident

    total_time = int((time.monotonic() - start) * 1000)

    return PipelineResult(
        identity=identity,
        profile=profile,
        corpus=corpus,
        needed_questions=needed,
        ready=ready,
        total_time_ms=total_time,
    )


def apply_question_answer(
    profile: MetaprogramProfile,
    metaprogram: str,
    answer: str,  # "a" or "b"
) -> MetaprogramProfile:
    """
    Apply a user's answer to a fallback question.
    Updates the profile with the confirmed metaprogram.

    Call this as each question is answered — the profile
    builds incrementally. Check get_needed_questions() after
    each answer to see if you need to ask more.
    """
    from metascraper.patterns import METAPROGRAMS
    from metascraper.detector import MetaprogramScore
    from metascraper.rewriter import FALLBACK_QUESTIONS

    if metaprogram not in FALLBACK_QUESTIONS:
        return profile

    q = FALLBACK_QUESTIONS[metaprogram]
    mp = METAPROGRAMS[metaprogram]

    if answer == "a":
        result = q["option_a"]["result"]
        score = MetaprogramScore(
            name=metaprogram,
            pole_a=mp["pole_a"]["name"],
            pole_b=mp["pole_b"]["name"],
            score_a=10.0,  # Strong confirmed signal
            score_b=0.0,
        )
    else:
        result = q["option_b"]["result"]
        score = MetaprogramScore(
            name=metaprogram,
            pole_a=mp["pole_a"]["name"],
            pole_b=mp["pole_b"]["name"],
            score_a=0.0,
            score_b=10.0,
        )

    profile.scores[metaprogram] = score
    return profile


# ═══════════════════════════════════════════════════════════════
# COLD EMAIL / COLD OUTREACH PIPELINE
# ═══════════════════════════════════════════════════════════════

async def profile_for_outreach(
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    twitter_handle: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    company: Optional[str] = None,
) -> PipelineResult:
    """
    Profile someone for cold outreach (email, DM, ad targeting).

    No OAuth — we only have external signals (email, name, handles).
    Scrape everything public, detect metaprograms, return profile.

    Use case: Before sending a cold email, run this on the lead.
    Then rewrite the email template in their frame.
    """
    identity = IdentitySignal(
        email=email,
        full_name=full_name,
        twitter_handle=twitter_handle,
        linkedin_url=linkedin_url,
    )

    start = time.monotonic()
    corpus = await scrape_all(identity, timeout=5.0)  # Longer timeout for outreach

    profile = MetaprogramProfile()
    if corpus.all_text:
        profile = detect_metaprograms(
            corpus.all_text,
            source_count=len(corpus.source_names),
        )

    total_time = int((time.monotonic() - start) * 1000)
    needed = get_needed_questions(profile)

    return PipelineResult(
        identity=identity,
        profile=profile,
        corpus=corpus,
        needed_questions=needed,
        ready=profile.detection_quality in ("excellent", "good"),
        total_time_ms=total_time,
    )


async def personalize_cold_email(
    template: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    twitter_handle: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    """
    Full pipeline: scrape a lead → detect metaprograms → rewrite email.

    Returns:
    {
        "original": "the template you sent",
        "personalized": "the rewritten email in their frame",
        "profile": {...metaprogram details...},
        "confidence": "excellent/good/partial/insufficient",
        "time_ms": 3200,
    }
    """
    result = await profile_for_outreach(
        email=email,
        full_name=full_name,
        twitter_handle=twitter_handle,
        linkedin_url=linkedin_url,
    )

    personalized = template  # Default to original

    if result.ready and api_key:
        personalized = await rewrite_message(
            original=template,
            profile=result.profile,
            api_key=api_key,
            context="cold_email",
        )

    return {
        "original": template,
        "personalized": personalized,
        "profile": result.profile.to_dict(),
        "confidence": result.profile.detection_quality,
        "time_ms": result.total_time_ms,
    }
