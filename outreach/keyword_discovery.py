"""
keyword_discovery.py — Generate buyer-intent keyword sets for a niche + city.

Input:  niche string (e.g. "plumber"), city string (e.g. "Austin TX")
Output: list of 3 high-intent keywords to use for SERP searches

No API calls — pure logic. DataForSEO costs money per search, so we generate
the right keywords here and only then fire searches.
"""

from typing import List

# Buyer-intent modifiers by service type — closest to phone call / purchase
INTENT_MODIFIERS = [
    "{niche} near me",
    "best {niche} in {city}",
    "{niche} {city}",
    "emergency {niche} {city}",
    "{niche} company {city}",
    "local {niche} {city}",
    "top rated {niche} {city}",
    "hire {niche} {city}",
    "affordable {niche} {city}",
    "{niche} service {city}",
]

# Niche-specific overrides: some niches have standard high-value keywords
NICHE_OVERRIDES = {
    "plumber":        ["{niche} {city}", "emergency plumber {city}", "water heater repair {city}"],
    "hvac":           ["{niche} {city}", "ac repair {city}", "furnace repair {city}"],
    "roofer":         ["roofing company {city}", "roof repair {city}", "roof replacement {city}"],
    "electrician":    ["{niche} {city}", "electrical contractor {city}", "emergency electrician {city}"],
    "dentist":        ["dentist {city}", "dental office {city}", "teeth cleaning {city}"],
    "lawyer":         ["personal injury lawyer {city}", "attorney {city}", "law firm {city}"],
    "chiropractor":   ["chiropractor {city}", "back pain {city}", "chiro {city}"],
    "landscaper":     ["landscaping {city}", "lawn care {city}", "lawn mowing {city}"],
    "pest control":   ["pest control {city}", "exterminator {city}", "termite treatment {city}"],
    "locksmith":      ["locksmith {city}", "emergency locksmith {city}", "car lockout {city}"],
    "cleaning":       ["house cleaning {city}", "cleaning service {city}", "maid service {city}"],
    "garage door":    ["garage door repair {city}", "garage door {city}", "garage door company {city}"],
    "painter":        ["painting contractor {city}", "house painters {city}", "interior painter {city}"],
    "concrete":       ["concrete contractor {city}", "concrete company {city}", "concrete repair {city}"],
    "tree service":   ["tree removal {city}", "tree trimming {city}", "arborist {city}"],
    "window":         ["window replacement {city}", "window company {city}", "window installation {city}"],
    "flooring":       ["flooring company {city}", "floor installation {city}", "hardwood floors {city}"],
    "remodeling":     ["home remodeling {city}", "kitchen remodel {city}", "bathroom remodel {city}"],
    "moving":         ["moving company {city}", "movers {city}", "local movers {city}"],
    "pool":           ["pool company {city}", "pool service {city}", "pool repair {city}"],
}


def get_keywords(niche: str, city: str, count: int = 3) -> List[str]:
    """
    Return `count` buyer-intent keywords for this niche + city.
    Uses niche-specific overrides first, falls back to generic intent modifiers.
    """
    niche_lower = niche.lower().strip()
    city_clean = city.strip()

    # Check for override
    for key, templates in NICHE_OVERRIDES.items():
        if key in niche_lower or niche_lower in key:
            keywords = [t.format(niche=niche_lower, city=city_clean) for t in templates]
            return keywords[:count]

    # Generic fallback: use top modifiers
    keywords = []
    for template in INTENT_MODIFIERS:
        kw = template.format(niche=niche_lower, city=city_clean)
        keywords.append(kw)
        if len(keywords) == count:
            break

    return keywords


if __name__ == "__main__":
    # Quick test
    test_cases = [
        ("plumber", "Austin TX"),
        ("dentist", "Denver CO"),
        ("landscaper", "Phoenix AZ"),
        ("auto mechanic", "Seattle WA"),  # No override — generic fallback
    ]

    for niche, city in test_cases:
        kws = get_keywords(niche, city)
        print(f"\n{niche} / {city}:")
        for i, kw in enumerate(kws, 1):
            print(f"  kw{i}: {kw}")
