# Hook Framework — Pluggable Data Sources for Email Personalization

## The Concept

Every personalized email in this system is powered by a "hook" — a data source that pulls
specific competitive intelligence about the target business and injects it into the email.

The SEO hook (DataForSEO rankings + traffic values) is hook #1. But the system is designed
so that any data source can become a hook by following the same interface. Add a new API key,
implement the interface, generate a spinner variant pool, and you have a new niche unlocked.

---

## The Hook Interface (What Every Hook Must Do)

Every hook module is a Python file that implements these five things:

```python
class HookModule:
    name = "hook_name"                    # Unique identifier
    required_env_vars = ["API_KEY_NAME"]  # Env vars this hook needs
    required_input_columns = ["col1"]     # Columns it needs from the business list CSV
    output_columns = ["field1", "field2"] # Columns it adds to the enriched CSV

    def fetch_data(self, row: dict) -> dict:
        """
        Given a business row from the CSV, call the API and return
        a dict of output_columns populated with real data.
        Return empty dict on failure.
        """
        raise NotImplementedError

    def assign_tier(self, data: dict) -> str:
        """
        Given the fetched data, return tier label: 'A', 'B', 'C', or 'D'
        """
        raise NotImplementedError

    TIER_ANGLES = {
        'A': "Description of email angle for this tier",
        'B': "...",
        'C': "...",
        'D': "...",
    }
```

The orchestrator calls `fetch_data()` per business row, calls `assign_tier()`, and the
assembled CSV feeds directly into the email assembler and form submitter unchanged.

---

## Hook Registry (hooks/registry.py)

```python
from hooks.seo_rankings import SEORankingsHook
from hooks.pagespeed import PageSpeedHook
from hooks.reviews import ReviewsHook
from hooks.ad_spend import AdSpendHook
from hooks.social_presence import SocialPresenceHook
from hooks.citations import CitationsHook
from hooks.tech_stack import TechStackHook
from hooks.ecommerce_traffic import EcommerceTrafficHook

HOOKS = {
    'seo_rankings':       SEORankingsHook,
    'pagespeed':          PageSpeedHook,
    'reviews':            ReviewsHook,
    'ad_spend':           AdSpendHook,
    'social_presence':    SocialPresenceHook,
    'citations':          CitationsHook,
    'tech_stack':         TechStackHook,
    'ecommerce_traffic':  EcommerceTrafficHook,
}
```

To add a new hook: create the class file, add it here. Everything else is automatic.

---

## The 8 Hooks (Wiring + Angles)

---

### Hook 1: SEO Rankings (Already Designed — Reference)
**File:** `hooks/seo_rankings.py`
**API:** DataForSEO
**Niche:** Local service businesses (plumbers, roofers, HVAC, lawyers, dentists...)
**Input columns:** `niche`, `city`
**Output columns:** `kw1`, `kw1_rank`, `kw1_traffic`, `kw2`, `kw2_rank`, `kw2_traffic`, `kw3`, `kw3_rank`, `kw3_traffic`, `top_competitor`, `top_traffic`

**Tier logic:**
- A = Ranked 1-3 on any keyword
- B = Ranked 4-10 on any keyword
- C = Ranked 11-20 on any keyword
- D = Not in top 20 anywhere → pivot to AI Search

**Subject line examples:**
- A: `"{comp} owns {kw2} ($X/mo) — {business} can too"`
- D: `"{comp1}, {comp2}, {comp3} own {kw} in {city} — AI Search is wide open"`

---

### Hook 2: Google PageSpeed / Web Performance
**File:** `hooks/pagespeed.py`
**API:** Google PageSpeed Insights API (free, no key needed for basic use)
**Niche:** Web design agencies, dev shops selling to any local business
**Input columns:** `website_url`
**Output columns:** `perf_score`, `comp1_score`, `comp2_score`, `comp3_score`, `top_issue`, `lcp_seconds`, `cls_score`

```python
import requests

class PageSpeedHook:
    name = "pagespeed"
    required_env_vars = []  # Free API, no key needed
    required_input_columns = ["website_url"]
    output_columns = ["perf_score", "comp1_score", "comp2_score", "comp3_score", "top_issue"]

    def fetch_data(self, row):
        url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={row['website_url']}&strategy=mobile"
        try:
            r = requests.get(url, timeout=15).json()
            score = int(r['lighthouseResult']['categories']['performance']['score'] * 100)
            audits = r['lighthouseResult']['audits']
            # Find worst audit
            top_issue = max(
                [a for a in audits.values() if a.get('score') is not None and a['score'] < 0.5],
                key=lambda a: a.get('details', {}).get('overallSavingsMs', 0),
                default={'title': 'page speed'}
            ).get('title', 'page speed')
            return {'perf_score': score, 'top_issue': top_issue}
        except Exception:
            return {}

    def assign_tier(self, data):
        score = data.get('perf_score', 50)
        if score >= 90: return 'A'   # Great score — upsell advanced features
        if score >= 70: return 'B'   # Decent but beatable
        if score >= 50: return 'C'   # Clearly slow
        return 'D'                   # Embarrassingly bad — easy close
```

**Tier angles:**
- A: "Your site scores 91 — strong. Your #1 competitor just hit 97 and Google's gap scoring is tightening."
- B: "You're at [score]/100. Industry leaders are at 90+. Google measures this directly."
- C: "Your site loads in [X] seconds on mobile. You're losing [est]% of visitors before they see your phone number."
- D: "Your site scores [score]/100. Google actively penalizes scores below 50. Your competitor is at [comp_score]."

**Subject line:** `"[Business] site: [score]/100 — [Comp] is at [comp_score] (Google penalizes the gap)"`

---

### Hook 3: Google Reviews / Reputation Gap
**File:** `hooks/reviews.py`
**API:** SerpAPI (Google Places results) or DataForSEO Places API
**Niche:** Reputation management agencies, local service businesses
**Input columns:** `business_name`, `city`, `niche`
**Output columns:** `review_count`, `avg_rating`, `comp1_reviews`, `comp1_rating`, `comp2_reviews`, `comp3_reviews`, `review_gap`

```python
class ReviewsHook:
    name = "reviews"
    required_env_vars = ["SERPAPI_KEY"]
    required_input_columns = ["business_name", "city", "niche"]
    output_columns = ["review_count", "avg_rating", "comp1_reviews", "comp1_rating", "review_gap"]

    def fetch_data(self, row):
        # Search Google Maps for business + competitors
        # Return review counts and ratings
        pass  # SerpAPI Google Maps search

    def assign_tier(self, data):
        count = data.get('review_count', 0)
        comp_max = max(data.get('comp1_reviews', 0), data.get('comp2_reviews', 0))
        ratio = count / comp_max if comp_max > 0 else 0
        if ratio >= 0.8: return 'A'   # Competitive — fine-tune
        if ratio >= 0.4: return 'B'   # Notable gap
        if ratio >= 0.1: return 'C'   # Significant gap
        return 'D'                     # Almost no reviews vs competition
```

**Tier angles:**
- A: "You're close in reviews — but your competitor's 4.9 vs your 4.6 is costing you clicks at the decision moment."
- C: "You have [X] reviews. [Comp] has [Y]. First thing customers check before calling. That gap costs phone calls."
- D: "You have [X] reviews. [Comp] has [Y]. When someone searches [niche] in [city], they call the one that looks trusted."

**Subject line:** `"[Comp] has [Y] reviews, [Business] has [X] — that's who gets called first"`

---

### Hook 4: Competitor Ad Spend (PPC Intelligence)
**File:** `hooks/ad_spend.py`
**API:** SpyFu API or SimilarWeb API
**Niche:** PPC management agencies, Google Ads consultants
**Input columns:** `website_url`, `niche`, `city`
**Output columns:** `comp1_ad_spend`, `comp1_keywords`, `comp2_ad_spend`, `target_missing_keywords`, `est_monthly_leads_lost`

**Tier angles:**
- A: "You're running ads — but [Comp] is outspending you on [keyword] 3:1. We plug that gap."
- B: "You're spending [X]/mo. [Comp] is at [Y]/mo targeting [keyword] you're not on."
- C: "You're running minimal ads. [Comp1] + [Comp2] are spending [$Z] combined on [keyword] in [city]."
- D: "You have no ads running. [Comp] spent $[X] last month on the exact keywords your customers search."

**Subject line:** `"[Comp] spent $[X]/mo on Google Ads for [keyword] in [city] — [Business] isn't running any"`

---

### Hook 5: Social Media Presence Gap
**File:** `hooks/social_presence.py`
**API:** Apify scraper (Instagram, Facebook, Google Business posts)
**Niche:** Social media agencies, content marketing
**Input columns:** `business_name`, `city`, `niche`
**Output columns:** `posts_per_week`, `followers`, `comp1_posts`, `comp1_followers`, `engagement_rate`, `comp1_engagement`

**Tier angles:**
- A: "You post consistently — but [Comp]'s engagement rate is [X]% vs your [Y]%. Content strategy issue."
- C: "You post [X]x/week. [Comp] posts [Y]x/week and has [Z]x your followers. Algorithm rewards frequency."
- D: "Last post on your Google Business Profile: [X] weeks ago. [Comp] posts 4x/week. Google ranks active profiles higher."

**Subject line:** `"[Comp] posts [X]x/week, [Business] posts [Y]x — Google notices that gap"`

---

### Hook 6: Local Citations / Directory Presence
**File:** `hooks/citations.py`
**API:** BrightLocal API or Moz Local API
**Niche:** Local SEO agencies, directory management services
**Input columns:** `business_name`, `website_url`, `city`
**Output columns:** `citation_count`, `comp1_citations`, `missing_directories`, `nap_issues`

**Tier angles:**
- A: "You're in [X] directories — solid. But [Y] of them have inconsistent phone numbers. Google flags that."
- C: "You're in [X] directories. [Comp] is in [Y]. Google uses citation volume as a trust signal for local rankings."
- D: "You're listed in [X] directories. Industry average for top-ranked [niche] is 60+. [Comp] is in [Y]."

**Subject line:** `"[Business] is in [X] directories. [Comp] is in [Y]. Google ranks citation volume."`

---

### Hook 7: Website Technology Stack
**File:** `hooks/tech_stack.py`
**API:** BuiltWith API or Wappalyzer API
**Niche:** Web dev agencies selling modernization, CMS migrations, Shopify migrations
**Input columns:** `website_url`
**Output columns:** `cms`, `cms_version`, `analytics_tool`, `missing_tools`, `comp1_cms`, `tech_debt_score`

**Tier angles:**
- A: "You're on [modern CMS] — good foundation. But you're missing [tool] that [Comp] uses for [benefit]."
- C: "You're still running [old CMS version]. [Comp] migrated to [modern stack] last year. Page speed difference alone is [X]s."
- D: "Your site is on [old tech] with no analytics installed. [Comp] is running [modern stack] with full conversion tracking."

**Subject line:** `"[Business] is on [old CMS] — [Comp] migrated to [modern] and their rankings jumped"`

---

### Hook 8: E-commerce Traffic Gap
**File:** `hooks/ecommerce_traffic.py`
**API:** SimilarWeb API
**Niche:** E-commerce SEO, Shopify/WooCommerce agencies, DTC brands
**Input columns:** `website_url`, `comp1_url`, `comp2_url`, `comp3_url`
**Output columns:** `monthly_visits`, `comp1_visits`, `comp2_visits`, `bounce_rate`, `top_traffic_source`, `comp1_top_source`

**Tier angles:**
- A: "You're getting [X] visits/month — respectable. But [Comp] converts at [Y]% vs your [Z]%. Traffic isn't the problem."
- C: "[Comp] gets [X] visits/month. You get [Y]. Most of their traffic comes from organic search you're not capturing."
- D: "[Comp] gets [X] visits/month. You're at [Y]. [Comp2] gets [Z]. All three are winning on channels you're not on."

**Subject line:** `"[Comp] gets [X] visits/month — [Business] gets [Y] (and we know why)"`

---

## Adding A New Hook (The Repeatable Process)

1. **Identify the data source** — what API has the competitive gap data for this niche?
2. **Map the output fields** — what 4-6 numbers make the pain visible?
3. **Define 4 tier thresholds** — what separates A/B/C/D for this data?
4. **Write the hook class** (implement `fetch_data` + `assign_tier`)
5. **Register it** in `hooks/registry.py`
6. **Generate spinner variants** — run `generate_variants.py` with Tier A/B/C/D descriptions for this hook
7. **Define subject line templates** — 2-3 variants per tier

That's the full process. Steps 4-7 are roughly 100-200 tokens of code + one $0.10 variant pool generation.

---

## Coverage Map (What These 8 Hooks Cover)

| Hook | Niche Served | API Cost | Difficulty |
|------|-------------|----------|------------|
| SEO Rankings | Local services (any) | ~$0.10/city | Low |
| PageSpeed | Web design | Free | Very Low |
| Reviews | Reputation mgmt | ~$0.05/business | Low |
| Ad Spend | PPC agencies | ~$0.10/business | Medium |
| Social Presence | Social media mgmt | ~$0.05/business | Medium |
| Citations | Local SEO | ~$0.02/business | Low |
| Tech Stack | Web dev/migrations | ~$0.01/business | Very Low |
| E-commerce Traffic | DTC/ecomm SEO | ~$0.05/business | Low |

These 8 hooks cover roughly 70-80% of agency niches that do outreach to local/regional businesses.
The remaining 20% are specialty niches (healthcare, legal, finance) where data is harder to get
or regulations around outreach apply.

---

## Multi-Hook Emails (Power Feature)

For the same target business, you can run 2-3 hooks and combine the data into one email.

Example for a local plumber:
- Hook 1 (SEO): They're ranking #14 for emergency plumber
- Hook 2 (Reviews): They have 8 reviews vs competitor's 312
- Hook 3 (PageSpeed): Their site scores 41/100

Email: *"[Business] is at #14 for emergency plumber in [city], has 8 reviews vs [Comp]'s 312,
and your site scores 41/100. Any one of those alone costs you phone calls. All three together
explains why [Comp] is getting $10k/mo and you're not."*

That email is nearly impossible to ignore. Multi-hook = the premium tier of the SaaS.

---

## File Structure

```
hooks/
  __init__.py
  registry.py              # Hook registry
  base.py                  # HookModule base class
  seo_rankings.py          # Hook 1
  pagespeed.py             # Hook 2
  reviews.py               # Hook 3
  ad_spend.py              # Hook 4
  social_presence.py       # Hook 5
  citations.py             # Hook 6
  tech_stack.py            # Hook 7
  ecommerce_traffic.py     # Hook 8

spinner_variants/
  seo_rankings_tier_a.json
  seo_rankings_tier_b.json
  seo_rankings_tier_c.json
  seo_rankings_tier_d.json
  pagespeed_tier_a.json
  ... (4 files per hook)
```

Each hook owns its own spinner variant files. The email assembler loads the right file based on `hook_name + tier`.
