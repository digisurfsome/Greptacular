"""API Research Engine — static pricing DB + web research pipeline.

Two-layer pricing research for detected APIs in Tool Factory blueprints:
  Layer 1: Static pricing database (~20 common APIs, instant)
  Layer 2: Web research via Claude Sonnet + WebSearch (current pricing, 90s timeout)

Fallback order: web research -> static DB -> "not_found" stub.
"""

import asyncio
import json
import logging
import shutil
import tempfile
import time
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Models (from PRD data model section)
# ---------------------------------------------------------------------------

class APIAlternative(BaseModel):
    """A cheaper or comparable alternative to a detected API."""
    service_name: str = Field(description="e.g. 'Apify'")
    category: str = Field(description="e.g. 'Web Scraping'")
    pricing_summary: str = Field(description="e.g. 'Pay-per-use, ~$5/1000 page loads'")
    free_tier: str = Field(description="e.g. 'Yes - $5 free monthly credit'")
    monthly_cost: str = Field(description="e.g. '$49/mo for 100K results'")
    tradeoff: str = Field(description="e.g. 'Cheaper but requires more setup'")
    signup_url: str = Field(description="e.g. 'https://apify.com'")


class APIResearchResult(BaseModel):
    """Research results for a single detected API."""
    service_key: str = Field(description="Matches DetectedAPI.service_key (e.g. 'phantombuster')")
    service_name: str = Field(description="e.g. 'PhantomBuster'")
    category: str = Field(description="e.g. 'Web Scraping & Automation'")

    # Pricing
    pricing_summary: str = Field(description="One-line: 'Starts at $56/mo, no free API tier'")
    pricing_tiers: list[str] = Field(description="List of tier descriptions")
    free_tier: str = Field(description="'No - paid plan required' or 'Yes - 100 contacts/mo'")
    api_access_cost: str = Field(description="Cost just to GET API access (e.g. '$56/mo minimum')")
    per_unit_cost: str = Field(description="e.g. '$0.05 per execution' or 'N/A - flat rate'")

    # Alternatives
    alternatives: list[APIAlternative] = Field(default_factory=list)

    # Red flags
    red_flags: list[str] = Field(default_factory=list)

    # Metadata
    research_source: str = Field(description="'web_research', 'static_database', or 'not_found'")
    researched_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class BlueprintAPIResearch(BaseModel):
    """Complete API research for all detected APIs in a blueprint."""
    results: list[APIResearchResult] = Field(default_factory=list)
    total_estimated_monthly_cost: str = Field(
        default="Unknown",
        description="Sum of minimum API costs",
    )
    research_duration_seconds: float = Field(default=0.0)


# ---------------------------------------------------------------------------
# Static Pricing Database (~20 APIs from PRD)
# ---------------------------------------------------------------------------
# Each entry is keyed by service_key (matching API_PATTERNS in sheet_blueprint.py)
# and contains all fields needed to construct an APIResearchResult.
#
# last_verified dates reflect when these prices were manually confirmed.
# Prices change — web research (Layer 2) provides current data when available.

STATIC_API_PRICING: dict[str, dict] = {
    "openai": {
        "service_name": "OpenAI",
        "category": "AI / LLM",
        "pricing_summary": "Pay-per-token, generous free tier for new accounts",
        "pricing_tiers": [
            "Free: $5 credit for new accounts (expires after 3 months)",
            "Pay-as-you-go: GPT-4o ~$2.50/1M input, $10/1M output",
            "GPT-4o-mini: ~$0.15/1M input, $0.60/1M output",
        ],
        "free_tier": "Yes - $5 free credit for new accounts",
        "api_access_cost": "Free to start (credit card required after free tier)",
        "per_unit_cost": "~$2.50/1M input tokens (GPT-4o)",
        "red_flags": [],
        "alternatives": [
            {
                "service_name": "Anthropic (Claude)",
                "category": "AI / LLM",
                "pricing_summary": "Pay-per-token, subscription option available",
                "free_tier": "No free API tier (subscription covers Claude Code)",
                "monthly_cost": "~$3/1M input tokens (Sonnet)",
                "tradeoff": "Similar quality, different strengths per task",
                "signup_url": "https://console.anthropic.com/",
            },
            {
                "service_name": "Google Gemini",
                "category": "AI / LLM",
                "pricing_summary": "Free tier available, pay-per-token after",
                "free_tier": "Yes - free tier with rate limits",
                "monthly_cost": "~$1.25/1M input tokens (Gemini 2.0 Flash)",
                "tradeoff": "Cheaper for high volume, 1M context available",
                "signup_url": "https://aistudio.google.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "anthropic": {
        "service_name": "Anthropic (Claude)",
        "category": "AI / LLM",
        "pricing_summary": "Pay-per-token API or $20-200/mo subscription",
        "pricing_tiers": [
            "API: Sonnet ~$3/1M input, $15/1M output",
            "API: Opus ~$15/1M input, $75/1M output",
            "API: Haiku ~$0.25/1M input, $1.25/1M output",
            "Subscription: Pro $20/mo, Max $100-200/mo",
        ],
        "free_tier": "No free API tier (subscription includes Claude Code usage)",
        "api_access_cost": "Free to create account; API is pay-per-use",
        "per_unit_cost": "~$3/1M input tokens (Sonnet)",
        "red_flags": [],
        "alternatives": [
            {
                "service_name": "OpenAI",
                "category": "AI / LLM",
                "pricing_summary": "Pay-per-token, free credits for new accounts",
                "free_tier": "Yes - $5 free credit",
                "monthly_cost": "~$2.50/1M input tokens (GPT-4o)",
                "tradeoff": "Broader ecosystem, slightly cheaper per token",
                "signup_url": "https://platform.openai.com/api-keys",
            },
            {
                "service_name": "Google Gemini",
                "category": "AI / LLM",
                "pricing_summary": "Free tier with rate limits, pay-per-token after",
                "free_tier": "Yes - free tier available",
                "monthly_cost": "~$1.25/1M input tokens (Flash)",
                "tradeoff": "Cheapest option, 1M context, less coding strength",
                "signup_url": "https://aistudio.google.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "meta_marketing": {
        "service_name": "Meta Marketing API",
        "category": "Advertising",
        "pricing_summary": "Free API access with Facebook app, complex setup",
        "pricing_tiers": [
            "API access: Free (requires Facebook Developer account + app review)",
            "Ad spend: Billed separately through Meta Ads Manager",
        ],
        "free_tier": "Yes - API itself is free; ad spend is separate",
        "api_access_cost": "Free (but requires approved Facebook app)",
        "per_unit_cost": "N/A - ad spend billed separately",
        "red_flags": [
            "Complex setup: requires Facebook app, app review, and Business Manager",
            "Strict rate limits on read endpoints",
            "Token refresh required every 60 days (long-lived tokens)",
        ],
        "alternatives": [
            {
                "service_name": "Google Ads API",
                "category": "Advertising",
                "pricing_summary": "Free API, ad spend billed separately",
                "free_tier": "Yes - API is free",
                "monthly_cost": "Free (ad spend separate)",
                "tradeoff": "Different audience, search-based vs social-based",
                "signup_url": "https://ads.google.com/",
            },
            {
                "service_name": "TikTok Marketing API",
                "category": "Advertising",
                "pricing_summary": "Free API for ad management",
                "free_tier": "Yes - API is free",
                "monthly_cost": "Free (ad spend separate)",
                "tradeoff": "Younger demographic, video-first platform",
                "signup_url": "https://business-api.tiktok.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "google_ads": {
        "service_name": "Google Ads",
        "category": "Advertising",
        "pricing_summary": "Free API, spend-based billing through Google Ads",
        "pricing_tiers": [
            "API access: Free (requires Google Ads Developer Token)",
            "Ad spend: Billed through Google Ads account",
        ],
        "free_tier": "Yes - API itself is free",
        "api_access_cost": "Free (Developer Token required, takes ~1 week approval)",
        "per_unit_cost": "N/A - ad spend billed separately",
        "red_flags": [
            "Developer Token approval can take days-weeks",
            "Basic access has low daily request limits (15K/day)",
        ],
        "alternatives": [
            {
                "service_name": "Meta Marketing API",
                "category": "Advertising",
                "pricing_summary": "Free API for Facebook/Instagram ads",
                "free_tier": "Yes - API is free",
                "monthly_cost": "Free (ad spend separate)",
                "tradeoff": "Social media audience vs search audience",
                "signup_url": "https://developers.facebook.com/",
            },
            {
                "service_name": "Microsoft Advertising API",
                "category": "Advertising",
                "pricing_summary": "Free API for Bing ads",
                "free_tier": "Yes - API is free",
                "monthly_cost": "Free (ad spend separate)",
                "tradeoff": "Smaller audience, often cheaper CPC",
                "signup_url": "https://ads.microsoft.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "phantombuster": {
        "service_name": "PhantomBuster",
        "category": "Web Scraping & Automation",
        "pricing_summary": "Starts at $56/mo, no free API tier",
        "pricing_tiers": [
            "Starter: $56/mo (5 phantoms, 20h execution/mo)",
            "Pro: $128/mo (15 phantoms, 80h execution/mo)",
            "Team: $352/mo (50 phantoms, 300h execution/mo)",
        ],
        "free_tier": "No - paid plan required for API access",
        "api_access_cost": "$56/mo minimum (Starter plan)",
        "per_unit_cost": "~$0.05 per phantom execution (varies by plan)",
        "red_flags": [
            "No free tier - paid plan required for API access",
            "Limited to 5 phantoms on Starter plan",
            "LinkedIn scraping may violate LinkedIn ToS",
        ],
        "alternatives": [
            {
                "service_name": "Apify",
                "category": "Web Scraping",
                "pricing_summary": "Pay-per-use with free tier, 3-10 scraper options per site type",
                "free_tier": "Yes - $5 free monthly credit",
                "monthly_cost": "$49/mo for 100K results (or pay-per-use)",
                "tradeoff": "More setup required, but cheaper and covers most scraping needs",
                "signup_url": "https://apify.com/",
            },
            {
                "service_name": "ScrapingBee",
                "category": "Web Scraping",
                "pricing_summary": "Simple API, pay-per-request with free tier",
                "free_tier": "Yes - 1000 free API calls",
                "monthly_cost": "$49/mo for 150K API credits",
                "tradeoff": "Simpler API but fewer pre-built scrapers",
                "signup_url": "https://www.scrapingbee.com/",
            },
            {
                "service_name": "Bright Data",
                "category": "Web Scraping",
                "pricing_summary": "Enterprise-grade, starts at $500/mo",
                "free_tier": "Yes - free trial available",
                "monthly_cost": "$500+/mo (enterprise pricing)",
                "tradeoff": "Most powerful but very expensive, overkill for most use cases",
                "signup_url": "https://brightdata.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "apollo": {
        "service_name": "Apollo.io",
        "category": "Lead Enrichment",
        "pricing_summary": "Free tier available, paid starts at ~$49/mo",
        "pricing_tiers": [
            "Free: 10K records export/mo, limited enrichment",
            "Basic: $49/mo per user (unlimited emails, 300 mobile credits/mo)",
            "Professional: $79/mo per user (advanced filters, dialer)",
            "Organization: $119/mo per user (buying intent, AI)",
        ],
        "free_tier": "Yes - 10K records/mo, limited enrichment credits",
        "api_access_cost": "Free tier includes API access (rate limited)",
        "per_unit_cost": "~$0.03-0.05 per enrichment credit",
        "red_flags": [
            "Free tier has aggressive rate limits (50 requests/min)",
            "Mobile phone credits are separate and limited",
        ],
        "alternatives": [
            {
                "service_name": "Hunter.io",
                "category": "Email Finding",
                "pricing_summary": "Email lookup specialist, free tier available",
                "free_tier": "Yes - 25 searches/mo free",
                "monthly_cost": "$49/mo for 500 searches",
                "tradeoff": "Focused on email finding only, no full lead enrichment",
                "signup_url": "https://hunter.io/",
            },
            {
                "service_name": "Snov.io",
                "category": "Lead Enrichment",
                "pricing_summary": "Cheaper Apollo alternative with email tools",
                "free_tier": "Yes - 50 credits/mo free",
                "monthly_cost": "$39/mo for 1000 credits",
                "tradeoff": "Cheaper but smaller database, fewer integrations",
                "signup_url": "https://snov.io/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "instantly": {
        "service_name": "Instantly",
        "category": "Email Outreach",
        "pricing_summary": "Starts at ~$30/mo, API on Growth plan+",
        "pricing_tiers": [
            "Growth: $30/mo (1000 contacts, 5000 emails/mo)",
            "Hypergrowth: $77.60/mo (25K contacts, 75K emails/mo)",
            "Light Speed: $286.30/mo (500K contacts, unlimited emails)",
        ],
        "free_tier": "No - 14-day free trial only",
        "api_access_cost": "$30/mo minimum (Growth plan)",
        "per_unit_cost": "N/A - flat rate per plan",
        "red_flags": [
            "No permanent free tier",
            "API documentation is limited",
            "Email warmup requires separate add-on",
        ],
        "alternatives": [
            {
                "service_name": "Lemlist",
                "category": "Email Outreach",
                "pricing_summary": "Cold email + LinkedIn outreach combined",
                "free_tier": "No - 14-day free trial only",
                "monthly_cost": "$39/mo per user (Email Starter)",
                "tradeoff": "LinkedIn automation built in, slightly more expensive",
                "signup_url": "https://www.lemlist.com/",
            },
            {
                "service_name": "Mailgun",
                "category": "Transactional Email",
                "pricing_summary": "Developer-friendly email API with free tier",
                "free_tier": "Yes - 100 emails/day free (Flex plan)",
                "monthly_cost": "$35/mo for 50K emails",
                "tradeoff": "Transactional email API, not a cold outreach platform",
                "signup_url": "https://www.mailgun.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "canva": {
        "service_name": "Canva",
        "category": "Design",
        "pricing_summary": "Free tier exists, API access varies by plan",
        "pricing_tiers": [
            "Free: Basic design tools, limited templates",
            "Pro: $12.99/mo (brand kit, premium templates)",
            "Teams: $14.99/mo per person (collaboration features)",
            "Enterprise: Custom pricing",
        ],
        "free_tier": "Yes - free plan with limited templates and storage",
        "api_access_cost": "Connect API requires Canva Pro ($12.99/mo) or higher",
        "per_unit_cost": "N/A - flat rate per plan",
        "red_flags": [
            "Connect API is still in beta with limited endpoints",
            "API access requires Pro plan or higher",
            "Rate limits are strict (100 requests/min)",
        ],
        "alternatives": [
            {
                "service_name": "Figma API",
                "category": "Design",
                "pricing_summary": "Free tier with API access, developer-friendly",
                "free_tier": "Yes - free plan includes API",
                "monthly_cost": "$12/mo per editor (Professional)",
                "tradeoff": "More developer-friendly API but less template variety",
                "signup_url": "https://www.figma.com/developers",
            },
            {
                "service_name": "Adobe Express API",
                "category": "Design",
                "pricing_summary": "Free tier available, embed SDK",
                "free_tier": "Yes - free plan with limitations",
                "monthly_cost": "$9.99/mo (Premium)",
                "tradeoff": "Adobe ecosystem integration, steeper learning curve",
                "signup_url": "https://developer.adobe.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "airtable": {
        "service_name": "Airtable",
        "category": "Database",
        "pricing_summary": "Free tier, API included on all plans",
        "pricing_tiers": [
            "Free: 1000 records/base, 1GB attachments",
            "Team: $20/seat/mo (50K records/base, 20GB)",
            "Business: $45/seat/mo (125K records/base, 100GB)",
            "Enterprise: Custom pricing",
        ],
        "free_tier": "Yes - 1000 records per base, API included",
        "api_access_cost": "Free (API included on all plans including free)",
        "per_unit_cost": "N/A - record limits per plan",
        "red_flags": [
            "Free tier limited to 1000 records per base",
            "API rate limit: 5 requests/second per base",
        ],
        "alternatives": [
            {
                "service_name": "Supabase",
                "category": "Database",
                "pricing_summary": "Open-source Postgres with generous free tier",
                "free_tier": "Yes - 500MB database, 1GB file storage",
                "monthly_cost": "$25/mo (Pro, 8GB database)",
                "tradeoff": "More powerful but requires SQL knowledge, no spreadsheet UI",
                "signup_url": "https://supabase.com/",
            },
            {
                "service_name": "Notion API",
                "category": "Database",
                "pricing_summary": "Free for personal use, API included",
                "free_tier": "Yes - free for personal use",
                "monthly_cost": "$10/mo per user (Plus)",
                "tradeoff": "Less structured than Airtable, better for docs + databases combo",
                "signup_url": "https://developers.notion.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "zapier": {
        "service_name": "Zapier",
        "category": "Automation",
        "pricing_summary": "Free tier (limited), API on paid plans",
        "pricing_tiers": [
            "Free: 100 tasks/mo, 5 Zaps, single-step only",
            "Starter: $19.99/mo (750 tasks/mo, multi-step)",
            "Professional: $49/mo (2000 tasks/mo, advanced logic)",
            "Team: $69/mo (shared workspace, 2000 tasks/mo)",
        ],
        "free_tier": "Yes - 100 tasks/mo, 5 single-step Zaps",
        "api_access_cost": "Free tier includes basic API/webhook access",
        "per_unit_cost": "~$0.03-0.05 per task (varies by plan)",
        "red_flags": [
            "Free tier is very limited (100 tasks, single-step only)",
            "Costs scale fast with task volume",
        ],
        "alternatives": [
            {
                "service_name": "Make (Integromat)",
                "category": "Automation",
                "pricing_summary": "Cheaper Zapier alternative with visual builder",
                "free_tier": "Yes - 1000 operations/mo free",
                "monthly_cost": "$9/mo for 10K operations",
                "tradeoff": "More complex UI but much cheaper per operation",
                "signup_url": "https://www.make.com/",
            },
            {
                "service_name": "n8n",
                "category": "Automation",
                "pricing_summary": "Self-hosted free, cloud from $20/mo",
                "free_tier": "Yes - fully free if self-hosted",
                "monthly_cost": "$20/mo cloud (or free self-hosted)",
                "tradeoff": "Requires technical setup for self-hosting, most flexible option",
                "signup_url": "https://n8n.io/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "stripe": {
        "service_name": "Stripe",
        "category": "Payments",
        "pricing_summary": "Free API, percentage-based transaction fees",
        "pricing_tiers": [
            "Standard: 2.9% + $0.30 per transaction",
            "Custom: Volume discounts for $100K+/month",
        ],
        "free_tier": "Yes - no monthly fee, pay only per transaction",
        "api_access_cost": "Free (no monthly fee)",
        "per_unit_cost": "2.9% + $0.30 per successful card charge",
        "red_flags": [],
        "alternatives": [
            {
                "service_name": "PayPal Commerce",
                "category": "Payments",
                "pricing_summary": "Similar per-transaction pricing, broader consumer reach",
                "free_tier": "Yes - no monthly fee",
                "monthly_cost": "Free (2.99% + $0.49 per transaction)",
                "tradeoff": "Wider consumer adoption but worse developer experience",
                "signup_url": "https://developer.paypal.com/",
            },
            {
                "service_name": "Square",
                "category": "Payments",
                "pricing_summary": "Free API, competitive transaction fees",
                "free_tier": "Yes - no monthly fee",
                "monthly_cost": "Free (2.9% + $0.30 online)",
                "tradeoff": "Better for in-person + online combo, less dev tooling",
                "signup_url": "https://developer.squareup.com/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "twilio": {
        "service_name": "Twilio",
        "category": "SMS / Voice",
        "pricing_summary": "Pay-per-use, generous free trial credits",
        "pricing_tiers": [
            "Free trial: $15.50 credit (no credit card required)",
            "SMS: $0.0079/message (US)",
            "Voice: $0.0085/min (US)",
            "WhatsApp: $0.005/message + Meta fee",
        ],
        "free_tier": "Yes - $15.50 free trial credit",
        "api_access_cost": "Free to start (trial credit provided)",
        "per_unit_cost": "$0.0079/SMS, $0.0085/min voice (US)",
        "red_flags": [
            "Trial accounts send from Twilio number with '[Trial]' prefix",
            "Phone number costs $1.15/mo (US) on top of usage",
        ],
        "alternatives": [
            {
                "service_name": "Vonage (Nexmo)",
                "category": "SMS / Voice",
                "pricing_summary": "Similar pricing, strong international coverage",
                "free_tier": "Yes - free trial credit",
                "monthly_cost": "Pay-per-use (~$0.0068/SMS US)",
                "tradeoff": "Slightly cheaper SMS, less documentation quality",
                "signup_url": "https://developer.vonage.com/",
            },
            {
                "service_name": "Amazon SNS",
                "category": "SMS",
                "pricing_summary": "AWS-integrated SMS, pay-per-use",
                "free_tier": "Yes - 100 free SMS/mo (through AWS free tier)",
                "monthly_cost": "Pay-per-use (~$0.00645/SMS US)",
                "tradeoff": "Cheapest for AWS users, no voice, limited features",
                "signup_url": "https://aws.amazon.com/sns/",
            },
        ],
        "last_verified": "2025-03-01",
    },
    "sendgrid": {
        "service_name": "SendGrid",
        "category": "Email",
        "pricing_summary": "Free tier (100 emails/day), API included",
        "pricing_tiers": [
            "Free: 100 emails/day forever",
            "Essentials: $19.95/mo (50K emails/mo)",
            "Pro: $89.95/mo (100K emails/mo, dedicated IP)",
            "Premier: Custom pricing",
        ],
        "free_tier": "Yes - 100 emails/day, API included",
        "api_access_cost": "Free (API included on all plans)",
        "per_unit_cost": "~$0.0004/email on Essentials plan",
        "red_flags": [
            "Free tier limited to 100 emails/day (3000/month)",
            "Deliverability can suffer on shared IPs (free/essentials)",
        ],
        "alternatives": [
            {
                "service_name": "Mailgun",
                "category": "Email",
                "pricing_summary": "Developer-friendly email API with free tier",
                "free_tier": "Yes - 100 emails/day (Flex plan)",
                "monthly_cost": "$35/mo for 50K emails",
                "tradeoff": "Better developer docs, slightly more expensive at scale",
                "signup_url": "https://www.mailgun.com/",
            },
            {
                "service_name": "Amazon SES",
                "category": "Email",
                "pricing_summary": "Cheapest bulk email, AWS-integrated",
                "free_tier": "Yes - 62K free emails/mo (from EC2)",
                "monthly_cost": "$0.10 per 1000 emails",
                "tradeoff": "Cheapest at scale, more setup required, no marketing features",
                "signup_url": "https://aws.amazon.com/ses/",
            },
        ],
        "last_verified": "2025-03-01",
    },
}


# ---------------------------------------------------------------------------
# Web Research (Layer 2) — Claude Sonnet + WebSearch
# ---------------------------------------------------------------------------

API_RESEARCH_SYSTEM_PROMPT = (
    "You are an API pricing research assistant. Your job is to search the web "
    "for current, accurate pricing information for software APIs and services. "
    "Return ONLY valid JSON with no markdown fences, no explanation. "
    "If you cannot find pricing information, return an empty JSON object {}."
)


def _build_research_prompt(service_name: str, service_key: str, category: str = "") -> str:
    """Build the user prompt for a single API pricing research query."""
    return (
        f"Research the current pricing for **{service_name}** API.\n\n"
        f"Return a JSON object with these exact fields:\n"
        f'{{\n'
        f'  "pricing_summary": "one-line summary of pricing",\n'
        f'  "pricing_tiers": ["Tier 1: $X/mo (details)", "Tier 2: $Y/mo (details)"],\n'
        f'  "free_tier": "Yes - description" or "No - reason",\n'
        f'  "api_access_cost": "cost just to get API access",\n'
        f'  "per_unit_cost": "cost per operation/request",\n'
        f'  "red_flags": ["concern 1", "concern 2"],\n'
        f'  "alternatives": [\n'
        f'    {{\n'
        f'      "service_name": "Alternative Name",\n'
        f'      "category": "{category or "same category"}",\n'
        f'      "pricing_summary": "one-line pricing",\n'
        f'      "free_tier": "Yes/No - details",\n'
        f'      "monthly_cost": "$X/mo for Y",\n'
        f'      "tradeoff": "what you gain/lose vs {service_name}",\n'
        f'      "signup_url": "https://..."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}\n\n'
        f"Search for the latest {service_name} pricing page. "
        f"Include 2-3 cheaper alternatives for {category or 'this'} use cases. "
        f"Return ONLY the JSON, no markdown fences."
    )


async def _research_api_via_web(
    service_name: str,
    service_key: str,
    category: str = "",
) -> Optional[APIResearchResult]:
    """Research a single API's pricing via Claude Sonnet + WebSearch.

    Uses ClaudeSDKClient with force_subscription=True so no API credits
    are burned. Returns None on any error or timeout — the caller falls
    back to the static database.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    from registry import get_effective_sdk_env

    system_cli = shutil.which("claude")
    if not system_cli:
        logger.warning("Claude CLI not found — skipping web research for %s", service_name)
        return None

    sdk_env = get_effective_sdk_env(force_subscription=True)
    scratch = tempfile.mkdtemp(prefix="api_research_")

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            cli_path=system_cli,
            system_prompt=API_RESEARCH_SYSTEM_PROMPT,
            env=sdk_env,
            max_turns=4,  # search -> read -> synthesize -> format
            permission_mode="bypassPermissions",
            allowed_tools=["WebSearch"],
            cwd=scratch,
        )
    )

    user_message = _build_research_prompt(service_name, service_key, category)
    timeout_seconds = 90

    async def _run() -> Optional[APIResearchResult]:
        await client.__aenter__()
        await client.query(user_message)

        full_text = ""
        async for msg in client.receive_response():
            msg_type = type(msg).__name__
            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                        full_text += block.text

        if not full_text.strip():
            logger.warning("Web research for %s returned empty response", service_name)
            return None

        return _parse_research_response(full_text, service_key, service_name, category)

    try:
        result = await asyncio.wait_for(_run(), timeout=timeout_seconds)
        return result
    except asyncio.TimeoutError:
        logger.warning(
            "Web research for %s timed out after %ds", service_name, timeout_seconds
        )
        return None
    except Exception as e:
        logger.warning("Web research for %s failed: %s", service_name, e)
        return None
    finally:
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass


def _parse_research_response(
    raw_text: str,
    service_key: str,
    service_name: str,
    category: str,
) -> Optional[APIResearchResult]:
    """Parse Claude's JSON response into an APIResearchResult.

    Handles common response quirks: markdown fences, trailing commas, etc.
    Returns None if parsing fails entirely.
    """
    # Strip markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        # Remove opening fence (possibly with language tag)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    if not text or text == "{}":
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse web research JSON for %s: %.200s", service_name, text
        )
        return None

    if not isinstance(data, dict) or not data:
        return None

    # Build alternatives list
    alternatives: list[APIAlternative] = []
    for alt in data.get("alternatives", []):
        if isinstance(alt, dict) and alt.get("service_name"):
            alternatives.append(APIAlternative(
                service_name=alt.get("service_name", ""),
                category=alt.get("category", category),
                pricing_summary=alt.get("pricing_summary", ""),
                free_tier=alt.get("free_tier", "Unknown"),
                monthly_cost=alt.get("monthly_cost", "Unknown"),
                tradeoff=alt.get("tradeoff", ""),
                signup_url=alt.get("signup_url", ""),
            ))

    return APIResearchResult(
        service_key=service_key,
        service_name=service_name,
        category=category,
        pricing_summary=data.get("pricing_summary", ""),
        pricing_tiers=data.get("pricing_tiers", []),
        free_tier=data.get("free_tier", "Unknown"),
        api_access_cost=data.get("api_access_cost", "Unknown"),
        per_unit_cost=data.get("per_unit_cost", "Unknown"),
        alternatives=alternatives,
        red_flags=data.get("red_flags", []),
        research_source="web_research",
    )


# ---------------------------------------------------------------------------
# Static Database Lookup (Layer 1)
# ---------------------------------------------------------------------------

def _get_static_result(service_key: str) -> Optional[APIResearchResult]:
    """Look up a service in the static pricing database.

    Returns an APIResearchResult with research_source="static_database",
    or None if the service isn't in the database.
    """
    entry = STATIC_API_PRICING.get(service_key)
    if not entry:
        return None

    alternatives = [
        APIAlternative(**alt) for alt in entry.get("alternatives", [])
    ]

    return APIResearchResult(
        service_key=service_key,
        service_name=entry["service_name"],
        category=entry["category"],
        pricing_summary=entry["pricing_summary"],
        pricing_tiers=entry["pricing_tiers"],
        free_tier=entry["free_tier"],
        api_access_cost=entry["api_access_cost"],
        per_unit_cost=entry["per_unit_cost"],
        alternatives=alternatives,
        red_flags=entry.get("red_flags", []),
        research_source="static_database",
    )


def _make_not_found_result(service_key: str, service_name: str) -> APIResearchResult:
    """Create a minimal result for an API that was not found in either layer."""
    return APIResearchResult(
        service_key=service_key,
        service_name=service_name,
        category="Unknown",
        pricing_summary="Pricing information not available",
        pricing_tiers=[],
        free_tier="Unknown",
        api_access_cost="Unknown",
        per_unit_cost="Unknown",
        alternatives=[],
        red_flags=["Pricing data could not be retrieved - verify manually"],
        research_source="not_found",
    )


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def research_api_pricing(
    detected_apis: list,
    progress_callback: Optional[callable] = None,
) -> BlueprintAPIResearch:
    """Research pricing for all detected APIs.

    For each detected API:
      1. Try web research (Layer 2) — current data via Sonnet + WebSearch
      2. Fall back to static DB (Layer 1) — instant, may be slightly stale
      3. If neither works, return a "not_found" stub

    Args:
        detected_apis: List of DetectedAPI objects from detect_apis().
        progress_callback: Optional callable for progress messages (SSE).

    Returns:
        BlueprintAPIResearch with results for all detected APIs.
    """
    if not detected_apis:
        return BlueprintAPIResearch()

    start_time = time.monotonic()
    results: list[APIResearchResult] = []
    total = len(detected_apis)

    for i, api in enumerate(detected_apis):
        service_key = api.service_key
        service_name = api.service_name

        if progress_callback:
            progress_callback(
                f"Researching API pricing {i + 1}/{total}: {service_name}..."
            )

        # Layer 2: Try web research first (current pricing data)
        result = await _research_api_via_web(
            service_name=service_name,
            service_key=service_key,
            category=_get_category_for_key(service_key),
        )

        # Layer 1: Fall back to static database
        if result is None:
            result = _get_static_result(service_key)
            if result and progress_callback:
                progress_callback(
                    f"  Using cached pricing data for {service_name}"
                )

        # Layer 0: Not found stub
        if result is None:
            result = _make_not_found_result(service_key, service_name)
            if progress_callback:
                progress_callback(
                    f"  No pricing data found for {service_name}"
                )

        results.append(result)

    duration = time.monotonic() - start_time

    # Estimate total monthly cost from minimum API access costs.
    # This is a rough estimate — many APIs are free or pay-per-use.
    cost_parts: list[str] = []
    for r in results:
        cost = r.api_access_cost.lower()
        if "free" in cost or cost == "unknown":
            continue
        cost_parts.append(f"{r.service_name}: {r.api_access_cost}")

    if cost_parts:
        total_cost = "Minimum: " + " + ".join(cost_parts)
    else:
        total_cost = "All detected APIs have free tiers or free API access"

    return BlueprintAPIResearch(
        results=results,
        total_estimated_monthly_cost=total_cost,
        research_duration_seconds=round(duration, 2),
    )


def _get_category_for_key(service_key: str) -> str:
    """Get the category string for a service key from the static DB.

    Falls back to empty string if the key isn't in the static DB.
    """
    entry = STATIC_API_PRICING.get(service_key)
    return entry["category"] if entry else ""
