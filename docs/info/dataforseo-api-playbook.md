# DataForSEO API Playbook

Your permanent reference for every DataForSEO endpoint, what it returns, and what it costs. Built specifically around the AI-receptionist angle: find local businesses, pull reviews, find "no one answered" complaints, send authority-loaded custom outreach.

**Pricing model:** Pay-as-you-go. $50 minimum deposit (which you already have). No monthly fee. Charged per request; some endpoints also charge per row/review returned.

**Auth:** HTTP Basic Auth. Base URL: `https://api.dataforseo.com/v3/`. That's it — just `login` + `password` from your dashboard.

---

## Table of Contents

1. [The 30-Second Pricing Cheat Sheet](#pricing-cheat-sheet)
2. [The 8 API Categories — Full Menu](#the-8-api-categories)
3. [SERP API — full breakdown](#serp-api)
4. [Business Data API — the goldmine for your use case](#business-data-api)
5. [DataForSEO Labs API](#dataforseo-labs-api)
6. [Keywords Data API](#keywords-data-api)
7. [Backlinks, On-Page, Domain Analytics, Merchant, App Data](#the-rest)
8. [Reviews Deep Dive — the AI receptionist angle](#reviews-deep-dive)
9. [Recommended Pipeline for AI Receptionist Prospecting](#recommended-pipeline)
10. [Cost Math — Real Scenarios](#cost-math)
11. [Python Code — Bare Minimum to Get Going](#python-examples)
12. [Anti-Recommendations — Skip These For Your Use Case](#anti-recommendations)

---

## Pricing Cheat Sheet

Every DataForSEO endpoint has up to 3 tiers. Cheaper = slower.

| Tier | Speed | Multiplier | When to use |
|------|-------|-----------|-------------|
| Standard (queue) | up to 5 min | 1x (baseline) | Bulk overnight scraping. Cheapest. |
| Standard Priority | up to 1 min | 2x | Same as Standard but faster queue |
| Live | up to 6 sec | ~3x | Real-time, one-off lookups |
| Live Advanced | 6 sec | ~5x | Real-time + extra parsed fields |

**Base prices (per single request):**

| API | Standard | Live | Live Advanced |
|-----|----------|------|---------------|
| Google Organic SERP | $0.0006 | $0.0018 | $0.002 |
| Google Maps SERP (local pack, 100 businesses) | $0.002 | $0.005 | $0.006 |
| Google Local Finder SERP | $0.002 | $0.005 | $0.006 |
| Google My Business Info | $0.001 | $0.005 | — |
| Google Reviews (per 10 reviews) | $0.00075 | $0.002 | — |
| Google Extended Reviews (per 20 reviews) | $0.00075 base + params | $0.002 base + params | — |
| Trustpilot Reviews | $0.0002 per request + $0.0001 per review | Live varies | — |
| Tripadvisor Reviews | $0.0002 per request + $0.0001 per review | Live varies | — |
| Yelp Reviews | Standard queue | Live varies | — |
| Keywords Data (Google Ads search vol) | $0.05 per 1000 kw | $0.075 | — |
| DataForSEO Labs (any endpoint) | Live only, ~$0.01 per 1000 rows | — | — |
| Backlinks | $0.02 per request + $0.00003 per row | — | — |

*Verify at dataforseo.com/pricing-list before running big jobs — DataForSEO adjusts prices.*

**Rate limit:** 2000 API calls per minute across ALL endpoints. You will never hit this.

---

## The 8 API Categories

The whole DataForSEO surface. Use this to orient yourself:

| # | Category | What it's for | Relevant to you? |
|---|----------|---------------|------------------|
| 1 | **SERP API** | Scrape Google/Bing/Yahoo/YouTube search results, Maps, Local Pack, Google Reviews SERP feature | **YES — heavily** |
| 2 | **Business Data API** | Google My Business, Google Reviews, Trustpilot, Tripadvisor, Yelp, Social Media | **YES — this is the goldmine** |
| 3 | **Keywords Data API** | Google Ads search volume, CPC, competition, keyword suggestions, Bing/YouTube keyword data | Medium — for finding search terms per city |
| 4 | **DataForSEO Labs API** | In-house SEO database — keyword ideas, ranked keywords, competitor domains, SERP competitors, historical data | Low unless you sell SEO too |
| 5 | **Backlinks API** | Backlink profile of any domain — anchors, referring domains, history | Low for AI receptionist |
| 6 | **On-Page API** | Crawl a specific website — technical SEO audit, content, resources | Situational — use to audit prospect's site in outreach |
| 7 | **Domain Analytics** | WHOIS, technologies used on a site, subdomains | Situational |
| 8 | **Merchant API** | Amazon/Google Shopping product data | No |
| 9 | **App Data API** | Google Play, Apple App Store listings & reviews | No |
| 10 | **Content Analysis API** | Search brand mentions across the web | Maybe for reputation research |
| 11 | **Content Generation API** | AI text generation | No — you have Claude |

Categories 1 and 2 are 95% of what you need.

---

## SERP API

Scrapes actual search engine results pages. Every SERP endpoint has 3 modes: `task_post` + `task_get` (Standard queue), `live/regular`, `live/advanced`.

### Google Endpoints (the useful ones)

| Endpoint | What it returns | Base cost |
|----------|-----------------|-----------|
| `serp/google/organic/live/advanced` | Full parsed organic SERP for a keyword — 10 results per page, with featured snippets, people-also-ask, related searches, knowledge graph, images, videos | $0.002 |
| `serp/google/maps/live/advanced` | **The one you're using.** Up to 100 businesses for a keyword + city — each with name, address, phone, website, rating, review count, category, hours, place_id, CID, lat/lng | $0.006 (approx — you said you're seeing ~$0.003, that's the Standard tier) |
| `serp/google/local_finder/live/advanced` | The "See all results" local pack expansion — 20 local businesses w/ same fields as Maps | $0.006 |
| `serp/google/reviews/live/advanced` | **THE ONE YOU HEARD ABOUT.** Google Reviews SERP feature — returns the last N reviews shown on Google's reviews panel with full text, rating, date, reviewer name, reviewer avatar, owner response. Default depth 10, max ~4490. | ~$0.002 per 10 reviews |
| `serp/google/events/live/advanced` | Local events | Situational |
| `serp/google/jobs/live/advanced` | Google Jobs results | No |
| `serp/google/images/live/advanced` | Google Images | No |
| `serp/google/news/live/advanced` | Google News | Maybe for reputation checks |
| `serp/google/ads_advertisers/live/advanced` | Who's running Google Ads for a keyword | Maybe — shows which competitors are paying for ads (they might have budget for AI receptionist) |

### Google Maps SERP — field-by-field

For each of the ~100 businesses returned, you get:
- `title` — business name
- `place_id` — Google's unique ID (use this to chain into review endpoints)
- `cid` — customer ID (alternative identifier)
- `phone` — direct phone number
- `url` — website URL
- `main_image`
- `rating.value` + `rating.votes_count` — star rating + review count
- `snippet` — Google's blurb
- `address` + `address_info.borough`, `city`, `zip`, `region`, `country_code`
- `latitude`, `longitude`
- `is_claimed` — did the owner claim their GMB? (unclaimed = worse target)
- `hotel_rating`, `price_level`
- `categories` array
- `hours` object with open/close per day + special hours
- `attributes` — accessibility, amenities, etc.
- `rank_group`, `rank_absolute` — where it ranked for the keyword

**This is why you like it — one $0.006 call and you have a whole prospect list with phone, website, rating, review count.**

### Google Reviews SERP endpoint — the "last 20 reviews" one

`serp/google/reviews/task_post` → task_get, or `serp/google/reviews/live/advanced`

Fields returned per review:
- `review_text` — **the full text — this is what you filter for "no one answered"**
- `rating.value` — 1–5 stars
- `timestamp` — when review was posted
- `time_ago` — human readable ("3 weeks ago")
- `profile_name` — reviewer name
- `profile_image_url`
- `profile_url` — link to reviewer's Google profile
- `owner_answer` — if the business owner replied
- `owner_time_ago` — when owner replied (if ever)
- `images` array — any photos in the review
- Total review count for the business
- Overall rating

Costs: default depth 10 → billed as 10 reviews. Set `depth=20` → billed as 20. `depth=100` → billed as 100. Every increment of 10 = one billing unit.

**Sort options:** `newest`, `highest_rating`, `lowest_rating`, `most_relevant`. For "find missed call complaints" use `newest` or `lowest_rating`.

### Other SERP engines available

Bing, Yahoo, YouTube, Baidu, Naver, Seznam. Skip for your use case.

---

## Business Data API

**This is the goldmine.** Separate from SERP because it returns structured business data, not search results.

### Google endpoints

| Endpoint | What | Cost |
|----------|------|------|
| `business_data/google/my_business_info` | Full GMB profile for one business — name, categories, phone, website, hours, busy hours, service attributes, description, address, rating, review count, place_id, CID | $0.001 (queue) / $0.005 (live) |
| `business_data/google/my_business_updates` | Google Posts / updates the business publishes | Cheap |
| `business_data/google/hotel_info` | Hotel-specific data | N/A |
| `business_data/google/hotel_searches` | Hotel prices | N/A |
| `business_data/google/reviews` | **The primary review scraper.** Up to 4490 reviews per business. Full text, rating, timestamp, reviewer, owner response, images. | $0.00075 per 10 reviews (Standard) / $0.002 per 10 reviews (Live) |
| `business_data/google/extended_reviews` | Reviews from OTHER platforms (Yelp, Tripadvisor, etc.) that Google indexes and shows on a business's Google page | $0.00075 base + $0.00075 per 20 reviews (cid/place_id) or $0.0015 per 20 (keyword) |
| `business_data/google/questions_and_answers` | The Q&A section on Google Maps listings | Cheap |

**Google Reviews vs Google Extended Reviews:**
- Google Reviews = reviews left ON Google
- Google Extended Reviews = reviews from third-party sites that Google surfaces on the business page (Facebook, Yelp, Tripadvisor, industry sites). Gives you cross-platform coverage in one call.

### Trustpilot endpoints

| Endpoint | What | Cost |
|----------|------|------|
| `business_data/trustpilot/search` | Search Trustpilot for businesses by keyword | Cheap |
| `business_data/trustpilot/reviews` | All reviews for a Trustpilot-listed business — full text, rating, date, reviewer, images, owner reply | ~$0.0002/request + $0.0001/review |

### Tripadvisor endpoints

| Endpoint | What | Cost |
|----------|------|------|
| `business_data/tripadvisor/search` | Search Tripadvisor businesses by keyword | Cheap |
| `business_data/tripadvisor/reviews` | Full review text, rating, date, reviewer, images | ~$0.0002/request + $0.0001/review |

### Yelp endpoints

| Endpoint | What | Cost |
|----------|------|------|
| `business_data/yelp/search` | Find Yelp businesses by keyword + location | Cheap |
| `business_data/yelp/reviews` | Yelp review data with full text | ~$0.0002/request + $0.0001/review |

### Social Media endpoints

Facebook, Pinterest, Reddit follower/engagement counts — cheap but low signal for your use case.

---

## DataForSEO Labs API

DataForSEO's in-house database (not live scraped). Fast + cheap for keyword research.

| Endpoint | Use |
|----------|-----|
| `keywords_for_site` | Feed a domain, get every keyword it ranks for + search vol / CPC / competition |
| `related_keywords` | Google's "searches related to" element |
| `keyword_suggestions` | Long-tail variants |
| `keyword_ideas` | Semantically related keywords |
| `ranked_keywords` | All keywords a URL currently ranks for |
| `competitors_domain` | Who competes with a domain in Google |
| `serp_competitors` | Which sites hold the most rankings for keywords you specify |
| `keyword_overview` | Search vol + CPC + trends for one keyword |
| `historical_search_volume` | Search volume over time |
| `bulk_traffic_estimation` | Estimate traffic for a list of domains |

Pricing: Live only, cents per 1000 rows returned. Very cheap.

**For your use case:** occasionally useful to figure out which keywords to feed Google Maps SERP for a given city (e.g. "plumber austin", "hvac austin", "law firm austin"). Otherwise mostly SEO-agency work.

---

## Keywords Data API

Live Google Ads / Bing / YouTube keyword metrics. Different from Labs — sources data from Google Ads directly.

| Endpoint | What |
|----------|------|
| `keywords_data/google_ads/search_volume` | Search vol + CPC + competition — up to 1000 kw per request |
| `keywords_data/google_ads/keywords_for_site` | Keywords a URL is relevant to |
| `keywords_data/google_ads/keywords_for_keywords` | Related keyword ideas |
| `keywords_data/google_trends/explore` | Google Trends data |
| `keywords_data/bing/search_volume` | Bing version |
| `keywords_data/dataforseo_trends/explore` | DFS in-house trends |

Cost: $0.05 per 1000 keywords (Standard). Batch heavily.

---

## The Rest

Quick coverage — skip these for AI receptionist prospecting unless you branch into selling SEO too.

- **Backlinks API:** $0.02/request + $0.00003/row. `backlinks`, `history`, `anchors`, `summary`, `referring_domains`, `domain_pages`, `referring_networks`. $100 monthly minimum commitment (usable across all APIs, but locks you in).
- **On-Page API:** Crawl a target site. Get title tags, meta, resources, broken links, page speed. Useful to add "your site is missing X, Y, Z" as authority signals in cold outreach. Cost: cents per crawled page.
- **Domain Analytics API:** WHOIS + tech stack detection. Confirms domain age, hosting provider, CMS, analytics installed. Useful signal: no analytics = unsophisticated = AI receptionist prospect.
- **Merchant API:** Amazon/Google Shopping. Skip.
- **App Data API:** App Store / Play Store. Skip.
- **Content Analysis API:** Brand mention monitoring across the web. Useful for reputation angle.
- **Content Generation API:** Skip, you have Claude.

---

## Reviews Deep Dive

This is the section you actually care about. Everything below is for finding "no one answered / couldn't reach / voicemail / never returned my call" complaints in reviews.

### Which endpoint to use for review text

| Source | Endpoint | Cost per 20 reviews | Includes full text? |
|--------|----------|---------------------|---------------------|
| Google (last N reviews) | `business_data/google/reviews` | ~$0.0015 (Std) | YES |
| Google (last ~20 shown on SERP) | `serp/google/reviews/live/advanced` | ~$0.004 | YES |
| Google + cross-platform (Yelp, TripAdvisor, etc. via Google) | `business_data/google/extended_reviews` | ~$0.0015 + params | YES |
| Trustpilot | `business_data/trustpilot/reviews` | ~$0.002 | YES |
| Tripadvisor | `business_data/tripadvisor/reviews` | ~$0.002 | YES |
| Yelp | `business_data/yelp/reviews` | ~$0.002 | YES |

**Winner for AI receptionist prospecting: `business_data/google/reviews` (Standard mode).** Most local SMBs live on Google Reviews. Cheapest per review. Set `sort_by=newest` + `depth=20` → billed as 20 reviews, ~$0.0015. For 1000 businesses = $1.50.

### Keyword filters to run against review text (client-side, not API)

The API returns raw text. You grep it yourself. Focused phrase list for missed-call / AI-receptionist signals:

```
Called ~ / phoned ~ / tried to call
No one answered / nobody answered / never answered
Straight to voicemail / went to voicemail / voicemail
No answer / didn't answer / doesn't answer
Never called back / no callback / never got a call back
Rang and rang / kept ringing
Left a message / left multiple messages
Impossible to reach / couldn't reach / hard to get ahold of
Line was busy
After hours / closed early / hours online are wrong
Rude on the phone / hung up on me
Waited on hold / on hold for
No response to my inquiry
Contact form went nowhere / never heard back
```

Any review with a 1-2 star rating AND one of these phrases = ideal AI receptionist prospect.

### Rating count as a leading indicator

- **< 20 reviews total** — probably not sophisticated, may not have thought about after-hours calls. Warm lead.
- **20–100 reviews with 4.0–4.4 rating** — the sweet spot. Enough reviews to find negative signal, low enough rating that they know they have a problem.
- **4.7+ rating** — probably doesn't want to buy anything to improve.
- **< 3.5 rating** — desperate, might convert fast but might not have budget.

### Owner response signal

If `owner_answer` is populated on <20% of negative reviews → owner is not actively managing reviews → likely also not managing phones well → good AI receptionist prospect.

If owner responds to EVERY review → already sophisticated → harder sell.

---

## Recommended Pipeline

Concrete step-by-step for the AI receptionist prospecting workflow:

### Step 1 — Bulk-find local businesses per city + niche
Endpoint: `serp/google/maps/task_post` (Standard queue) or `serp/google/maps/live/advanced` (real-time)
Input: `keyword=plumber`, `location_name=Austin,Texas,United States`, `language_code=en`, `depth=100`
Output: ~100 businesses w/ place_id, phone, website, rating, review count
Cost: ~$0.002–$0.006 per keyword × city

### Step 2 — Filter locally (no API cost)
Keep only businesses with:
- 10 ≤ review_count ≤ 200 (enough signal, not a giant)
- 3.0 ≤ rating ≤ 4.5 (has problems, not hopeless)
- website is populated (need a contact form for outreach)

### Step 3 — Pull recent reviews per surviving business
Endpoint: `business_data/google/reviews/task_post` (Standard)
Input: `place_id=<from step 1>`, `sort_by=newest`, `depth=20`
Output: last 20 review texts with rating + date + owner response
Cost: ~$0.0015 per business

### Step 4 — Filter reviews client-side for missed-call signals
Grep against the phrase list above. Score each business: number of matched phrases in last 20 reviews.

### Step 5 (optional) — Enrich with site audit
Endpoint: `on_page/instant_pages` on their website
Output: page title, meta, tech stack, page speed
Use in email: "I noticed your site is on WordPress with no analytics — plus your last 3 negative reviews all mention nobody answering the phone..."

### Step 6 — Custom email/contact form message per lead
Feed Claude the JSON of {business_name, category, city, rating, recent_negative_reviews, missed_call_phrases_found}. Claude drafts a personalized email that quotes the actual reviews.

---

## Cost Math

Realistic scenario: prospect 1000 local businesses in one city for AI receptionist.

| Step | API call | Volume | Cost |
|------|----------|--------|------|
| 1. Bulk find | Google Maps SERP (Standard) | 10 keywords × 1 city × 100 results = 10 calls | 10 × $0.002 = **$0.02** |
| 2. Filter locally | none | 1000 → ~400 survivors | $0 |
| 3. Pull reviews | Google Reviews (Standard, depth=20) | 400 calls | 400 × $0.0015 = **$0.60** |
| 4. Filter locally | none | 400 → ~80 hot leads | $0 |
| 5. Enrich | On-Page instant_pages | 80 calls | 80 × ~$0.003 = **$0.24** |
| **Total** | | | **~$0.86 for 1000 businesses → 80 hot leads** |

Your $50 credit = ~58,000 businesses scanned this way. Or ~4,600 hot leads.

Live mode multiplies costs ~3–5x. Use Standard queue overnight, Live only for one-off spot checks.

---

## Python Examples

Bare minimum working code for the two endpoints you'll use most. Uses `requests`. Replace `LOGIN` and `PASSWORD` with your dashboard credentials.

### Local Pack (100 businesses per keyword+city)

```python
import requests
from requests.auth import HTTPBasicAuth

LOGIN = "your-login"
PASSWORD = "your-password"

payload = [{
    "keyword": "plumber",
    "location_name": "Austin,Texas,United States",
    "language_code": "en",
    "depth": 100,
}]

r = requests.post(
    "https://api.dataforseo.com/v3/serp/google/maps/live/advanced",
    auth=HTTPBasicAuth(LOGIN, PASSWORD),
    json=payload,
)
data = r.json()
for item in data["tasks"][0]["result"][0]["items"]:
    print(item["title"], item.get("phone"), item.get("rating", {}).get("value"),
          item.get("rating", {}).get("votes_count"), item.get("place_id"))
```

### Last 20 Google Reviews for a business

```python
payload = [{
    "place_id": "ChIJ....(from step above)",
    "sort_by": "newest",
    "depth": 20,
    "language_code": "en",
}]

r = requests.post(
    "https://api.dataforseo.com/v3/business_data/google/reviews/task_post",
    auth=HTTPBasicAuth(LOGIN, PASSWORD),
    json=payload,
)
task_id = r.json()["tasks"][0]["id"]

# Poll (wait ~30s to 5min for Standard queue), then:
r = requests.get(
    f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}",
    auth=HTTPBasicAuth(LOGIN, PASSWORD),
)
for review in r.json()["tasks"][0]["result"][0]["items"]:
    print(review["rating"]["value"], review["timestamp"],
          review["profile_name"], review["review_text"])
```

For real-time (skip the polling): use `business_data/google/reviews/live` — costs ~3x more.

---

## Anti-Recommendations

Endpoints that look relevant but AREN'T worth it for your specific AI-receptionist use case:

- **DataForSEO Labs `ranked_keywords`** — SEO agency tool, not a prospecting tool. Skip.
- **Backlinks API** — $100 monthly commitment. Only worth it if you also sell SEO services.
- **Domain Analytics WHOIS** — you already have place_id + website. WHOIS adds noise not signal.
- **App Data API** — you're not selling to app makers.
- **Merchant API** — you're not selling to Amazon sellers.
- **Content Generation API** — you have Claude.
- **Google Extended Reviews** — sounds cool but 90% of the time overlaps with plain Google Reviews. Use plain Google Reviews first; only add Extended if you need cross-platform coverage.
- **`serp/google/reviews`** vs **`business_data/google/reviews`** — they overlap. The `business_data` version is cheaper and cleaner. Only use the SERP one if you need to see reviews exactly as they appear on the SERP feature (rare).

---

## One-line rules to remember

- Standard queue for bulk overnight. Live only for one-offs.
- Always sort reviews `newest` when prospecting for missed calls.
- Filter locally, not with API params — API params cost extra.
- One Google Maps SERP call = 100 businesses = $0.002 = insanely cheap.
- One Google Reviews call = 20 reviews = $0.0015 = insanely cheap.
- Your $50 covers ~4600 hot leads with the pipeline above.
