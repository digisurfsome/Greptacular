"""
generate_variants.py — One-time Claude call to generate spinner variant pools.

Run this ONCE per hook to create the JSON variant files.
Cost: ~$0.01-0.05 per hook (4 tiers × 5 blocks × 10 variants each).
After that: assemble_emails.py uses the JSON files at $0/email forever.

Usage:
  python generate_variants.py --hook seo_rankings
  python generate_variants.py --hook pagespeed
  python generate_variants.py --hook all

Output: spinner_variants/{hook}_tier_a.json (and b, c, d)
"""

import os
import sys
import json
import argparse
import anthropic
from pathlib import Path

VARIANTS_DIR = Path(__file__).parent / "spinner_variants"
VARIANTS_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ─── Hook definitions ──────────────────────────────────────────────────────────
# Each hook defines:
#   - available_vars: what columns exist in the enriched CSV for this hook
#   - tier_context: what the data situation looks like for each tier
#   - niche_description: who is the target (for tone)

HOOK_SPECS = {
    "seo_rankings": {
        "niche_description": "local service businesses (plumbers, roofers, HVAC, lawyers, dentists)",
        "available_vars": [
            "{business_name}", "{city}", "{niche}",
            "{kw1}", "{kw1_rank}", "{kw1_traffic}",
            "{kw2}", "{kw2_rank}", "{kw2_traffic}",
            "{kw3}", "{kw3_rank}", "{kw3_traffic}",
            "{top_competitor}", "{top_traffic}",
        ],
        "tiers": {
            "A": {
                "situation": "Business ranks #1-3 for at least one keyword. They're winning but could be stronger.",
                "angle": "Competitive — you're up there but your #1 competitor has X advantage. We sharpen the lead.",
                "tone": "Peer-to-peer, not salesy. Treat them as someone already doing well.",
            },
            "B": {
                "situation": "Business ranks #4-10. On page 1 but not getting the calls. Tantalizingly close.",
                "angle": "Page 1 gap — you're visible but #1 is getting all the calls. Here's the specific gap.",
                "tone": "Direct. Show the math. This is about real money being left on the table.",
            },
            "C": {
                "situation": "Business ranks #11-20. Page 2. Effectively invisible to most searchers.",
                "angle": "Page 2 burial — position 11-20 gets <1% of clicks. Competitor is mopping up.",
                "tone": "Urgent but not condescending. Show the data, not the drama.",
            },
            "D": {
                "situation": "Business is not in top 20 anywhere on Google. But AI Search (ChatGPT, Perplexity, AI Overviews) is a brand-new channel with zero competition yet.",
                "angle": "AI Search pivot — Google is lost, but AI Search citations are still unclaimed. Be first.",
                "tone": "Contrarian/opportunity framing. Google is crowded, AI is wide open right now.",
            },
        },
    },
    "pagespeed": {
        "niche_description": "any local business being targeted by web design or dev agencies",
        "available_vars": [
            "{business_name}", "{city}", "{niche}",
            "{website_url}", "{perf_score}", "{top_issue}",
            "{lcp_seconds}", "{cls_score}",
        ],
        "tiers": {
            "A": {
                "situation": "Site scores 90+/100. Strong performer. Angle is staying ahead of competitors as Google tightens scoring.",
                "angle": "You're strong — but the gap to competitors is shrinking and Google keeps moving the bar.",
                "tone": "Subtle urgency. Don't insult good work — offer to extend it.",
            },
            "B": {
                "situation": "Site scores 70-89. Decent but not competitive. Industry leaders are at 90+.",
                "angle": "Good isn't good enough — Google directly uses Core Web Vitals for local rankings.",
                "tone": "Factual. Show the benchmark gap without being harsh.",
            },
            "C": {
                "situation": "Site scores 50-69. Clearly slow on mobile. Losing visitors before they convert.",
                "angle": "Lost leads — real visitors are bouncing before they see your phone number.",
                "tone": "Concrete and specific. LCP seconds, bounce rate impact, phone call math.",
            },
            "D": {
                "situation": "Site scores below 50. Google penalizes this range. Competitor scores are likely 2x higher.",
                "angle": "Google penalty territory — sub-50 is actively suppressed in local results.",
                "tone": "Direct. This is hurting them right now, not theoretically.",
            },
        },
    },
}

# ─── Prompt builder ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You write cold outreach emails for marketing agencies targeting local service businesses.
Your emails:
- Are under 120 words total
- Sound like they were written by a human who did real research, not a template
- Lead with the specific data point (rank, score, number) — not a compliment
- Never use phrases like "I hope this finds you well", "I wanted to reach out", "synergy", "leverage", "game-changer"
- Have a single clear CTA — one question or one offer, not both
- Use first person but never "I just wanted to" or "I thought you might"
- Sound slightly informal — contractions are fine, full punctuation not required
- NEVER mention SEO, digital marketing, or your agency name in the email body
"""

def build_prompt(hook_name: str, tier: str, spec: dict) -> str:
    tier_spec = spec["tiers"][tier]
    vars_list = "\n".join(f"  {v}" for v in spec["available_vars"])

    return f"""Generate a spinner variant pool for cold outreach emails.

Hook: {hook_name}
Tier {tier} situation: {tier_spec['situation']}
Email angle: {tier_spec['angle']}
Tone: {tier_spec['tone']}
Target: {spec['niche_description']}

Available template variables (use these exactly, with curly braces):
{vars_list}

Generate a JSON object with these exact keys, each containing an array of 10 variants.
Every variant must use at least 2-3 of the template variables naturally.
Every variant in a block must convey the same core message but sound completely different.

JSON structure:
{{
  "subject_lines": [10 subject line variants — short, specific, data-driven, no clickbait],
  "opener": [10 opening sentence variants — leads with the data point, no pleasantries],
  "hook": [10 hook sentence variants — shows the competitor contrast or opportunity],
  "pain": [10 pain/consequence sentence variants — what this costs them in real terms],
  "pitch": [10 pitch sentence variants — one sentence, what you do, no fluff],
  "cta": [10 CTA variants — one question or one offer, casual, easy to reply to]
}}

Return ONLY valid JSON. No explanation, no markdown fences, no comments."""


# ─── Generator ─────────────────────────────────────────────────────────────────

def generate_tier_variants(hook_name: str, tier: str, spec: dict) -> dict:
    prompt = build_prompt(hook_name, tier, spec)

    print(f"  Generating Tier {tier} variants...")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Haiku is fine for generation, saves cost
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if model added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    try:
        data = json.loads(raw.strip())
        return data
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Raw response: {raw[:500]}")
        raise


def generate_hook_variants(hook_name: str):
    if hook_name not in HOOK_SPECS:
        print(f"Unknown hook '{hook_name}'. Available: {list(HOOK_SPECS.keys())}")
        return

    spec = HOOK_SPECS[hook_name]
    print(f"\nGenerating variants for hook: {hook_name}")

    for tier in ["A", "B", "C", "D"]:
        output_path = VARIANTS_DIR / f"{hook_name}_tier_{tier.lower()}.json"

        if output_path.exists():
            print(f"  Tier {tier}: already exists at {output_path} — skipping. Delete to regenerate.")
            continue

        variants = generate_tier_variants(hook_name, tier, spec)

        # Validate structure
        required_keys = ["subject_lines", "opener", "hook", "pain", "pitch", "cta"]
        missing = [k for k in required_keys if k not in variants]
        if missing:
            print(f"  WARNING: Missing keys in Tier {tier} response: {missing}")

        # Check variant counts
        for key in required_keys:
            count = len(variants.get(key, []))
            if count < 10:
                print(f"  WARNING: Only {count}/10 variants for '{key}' in Tier {tier}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(variants, f, indent=2)

        print(f"  Tier {tier}: saved {output_path}")

    print(f"\nDone. Run: python assemble_emails.py --input enriched_{hook_name}_*.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate spinner variant pools via Claude")
    parser.add_argument("--hook", required=True,
                        help=f"Hook name or 'all'. Available: {list(HOOK_SPECS.keys())}")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY env var")
        sys.exit(1)

    if args.hook == "all":
        for hook_name in HOOK_SPECS:
            generate_hook_variants(hook_name)
    else:
        generate_hook_variants(args.hook)
