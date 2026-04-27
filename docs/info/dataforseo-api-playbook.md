# DataForSEO API Playbook
## Complete Menu for Local Business Outreach + AI Receptionist Sales

> Last updated: 2026-04-27
> Credit on account: $50
> Primary use case: Identify local businesses with unanswered calls / reputation problems → sell AI receptionist

---

## TL;DR — The $0.005 Full Dossier

One complete business profile (discovery + deep profile + 20 reviews) costs **~$0.005**.
- $50 credit → **~10,000 fully profiled businesses**
- $50 credit → **2.5 million businesses** if you only run discovery (Maps SERP)

---

## The 4-Step Workflow

```
Step 1: Maps SERP        → discover 100 businesses for $0.002
Step 2: My Business Info → deep profile hot leads for $0.0015 each
Step 3: Google Reviews   → pull 20 newest/worst reviews for $0.0015 each
Step 4: Keywords (opt.)  → show search volume for $0.075/batch
```

---

## API Quick Reference Table

| Purpose | Endpoint | Cost | Use |
|---------|----------|------|-----|
| Discover 100 local businesses | `/v3/serp/google/maps/live/advanced/` | **$0.002/search** | PRIMARY |
| Full business profile | `/v3/business_data/google/my_business_info/live/` | **$0.0015/biz** | PRIMARY |
| Pull 20 newest/worst reviews | `/v3/business_data/google/reviews/task_post/` | **$0.0015/20 reviews** | PRIMARY |
| Filter database by rating/category | `/v3/business_data/business_listings/search/live/` | ~$0.0015/req | PRIMARY |
| Keyword search volume | `/v3/keywords_data/google_ads/search_volume/live/` | $0.075/task (1K kws) | SECONDARY |
| On-page SEO audit | `/v3/on_page/task_post/` | $0.000125/page | SECONDARY |
| Trustpilot reviews | `/v3/business_data/trustpilot/reviews/task_post/` | $0.00075/20 | OPTIONAL |
| Tripadvisor reviews | `/v3/business_data/tripadvisor/reviews/task_post/` | $0.00075/30 | OPTIONAL |
| Google Q&A | `/v3/business_data/google/questions_and_answers/live/` | ~$0.0015 | OPTIONAL |
| Backlinks | `/v3/backlinks/` | $0.02+/request | SKIP (requires $100/mo min) |

---

## Standard vs. Live Mode

| Mode | Cost | Speed | Use When |
|------|------|-------|----------|
| Standard (task_post + task_get) | **3x cheaper** | 5–45 min delay | Batch prospecting |
| Live | 3x more expensive | ~6 seconds | Real-time demos/dashboards |

**Rule:** Use standard for all batch scripts. Use live only if you need instant results.

---

## API #1 — Google Maps SERP (Your Bread and Butter)

**Endpoint:** `/v3/serp/google/maps/live/advanced/`

**Query format:** keyword like `"plumbers Austin"` + `location_name: "Austin,Texas,United States"`

**Cost:** $0.002 per search → 100 businesses → **$0.00002 per business**

### Fields You Get Per Business

| Field | What It Tells You |
|-------|------------------|
| `title` | Business name |
| `phone` | Phone number |
| `address` | Street address |
| `address_info` | Structured: city, zip, region, country |
| `domain` | Website domain |
| `url` | Website URL |
| `contact_url` | Their contact page |
| `book_online_url` | Booking/ordering page |
| `place_id` | Google Place ID → use to fetch reviews |
| `cid` | Google client ID → alternative key |
| `rating.value` | Star rating (e.g., 4.7) |
| `rating.votes_count` | Total review count |
| `rating_distribution` | **How many 1-star, 2-star, 3-star, 4-star, 5-star** |
| `category` | Primary category (e.g., "Plumber") |
| `additional_categories` | All secondary categories |
| `price_level` | Inexpensive / moderate / expensive |
| `work_hours` | Full weekly schedule |
| `work_hours.current_status` | Open or closed RIGHT NOW |
| `main_image` | Profile photo URL |
| `total_photos` | Photo count |
| `is_claimed` | Has owner verified the listing? |
| `latitude` / `longitude` | GPS coordinates |

**AI Receptionist signals from this call:**
- `rating_distribution` with high 1-star count → communication problems
- `is_claimed: false` → not managing online presence at all
- Low `total_photos` → minimal GMB management

---

## API #2 — Google My Business Info (Deep Profile)

**Endpoint:** `/v3/business_data/google/my_business_info/live/`

**Input:** `place_id` or `cid` from Maps SERP (or business name as keyword)

**Cost:** $0.0015 per business

### Extra Fields Beyond Maps SERP

| Field | What It Tells You |
|-------|------------------|
| `description` | Business overview text |
| `logo` | Logo image URL |
| `place_topics` | **Keywords from reviews with mention frequency** |
| `popular_times` | Hourly foot traffic index by day (0–100) |
| `attributes` | Services: wheelchair accessible, delivery, etc. |
| `current_status` | opened / closed / **temporarily_closed** / **closed_forever** |
| `local_business_links` | Reservation, ordering, menu URLs |
| `people_also_search` | Competing businesses with ratings |
| `snippet` | Additional business text |

### The `place_topics` Gold Mine

This field surfaces the most-mentioned keywords across ALL of a business's reviews. Examples:
- `"response time: 47 mentions"` → customers care about speed
- `"phone: 23 mentions"` → customers are calling frequently
- `"voicemail: 12 mentions"` → **calls going unanswered** ← your lead signal
- `"no answer: 8 mentions"` → **direct missed call evidence** ← your lead signal

### The `popular_times` Opportunity

Shows when a business is busiest by hour. If they're slammed 10am–2pm but only have 1 employee answering phones, that's your pitch: "You're losing calls during your peak hours."

---

## API #3 — Google Reviews (The "Last 20 Reviews" One You Heard About)

**Endpoint:** `/v3/business_data/google/reviews/task_post/` + `/v3/business_data/google/reviews/task_get/`

Or use extended reviews: `/v3/business_data/google/extended_reviews/task_post/`

**Cost:** $0.00075 per 10 reviews → **$0.0015 for 20 reviews**

**Key parameters:**
- `depth: 20` → pull 20 reviews (max 4,490)
- `sort_by: "newest"` → most recent first
- `sort_by: "lowest_rating"` → worst reviews first
- `sort_by: "highest_rating"` → best reviews first
- `sort_by: "relevant"` → Google's default sort

### Fields Per Review

| Field | What It Tells You |
|-------|------------------|
| `review_text` | Full review text |
| `original_review_text` | Original language (if translated) |
| `rating.value` | Star rating (1–5) |
| `time_ago` | "2 weeks ago", "a month ago" |
| `timestamp` | Exact date |
| `profile_name` | Reviewer name |
| `reviews_count` | How many reviews this person has written |
| `local_guide` | Is this a trusted Google Local Guide? |
| `owner_answer` | **Business owner's response text** |
| `owner_timestamp` | When owner responded |
| `images` | Photos attached to review |
| `review_highlights` | Structured ratings (e.g., "Service: 2/5") |

### AI Receptionist Lead Signals

**The formula:** 1-star review + `owner_answer: null` = business is not managing reputation.

Search review text for:
- "no answer" / "didn't answer"
- "went to voicemail" / "voicemail full"
- "never called back" / "couldn't reach"
- "no one picked up"
- "left a message, no return call"

Any of these = hard evidence of missed calls → perfect AI receptionist pitch.

---

## API #4 — Business Listings Search (Prospecting Database)

**Endpoint:** `/v3/business_data/business_listings/search/live/`

Unlike Maps SERP (which mimics a Google search), this queries DataForSEO's own database. Power-user prospecting tool.

**Cost:** ~$0.0015 per request

### What You Can Filter On

```
location_coordinate: { lat: 30.26, lng: -97.74, radius: 50000 }  ← 50km radius around Austin
categories: ["plumber"]
filters: [
  ["rating.value", "<", 4.0],        ← only businesses with problems
  ["rating.votes_count", ">", 10],   ← at least 10 reviews (real businesses)
  ["is_claimed", "=", true]          ← they're active enough to claim
]
order_by: ["rating.value,asc"]       ← worst rated first
limit: 1000                          ← up to 1,000 results
```

Returns same data as My Business Info (full profile). This is batch prospecting — no keyword needed.

---

## API #5 — Keywords Data (Optional, for Pitch Enhancement)

**Endpoint:** `/v3/keywords_data/google_ads/search_volume/live/`

**Cost:** $0.075 per task (up to 1,000 keywords)

**Returns:** Monthly search volume, CPC, competition level, 12-month trend data

**Pitch use:** "There are 2,400 people searching 'plumbers Austin' every month. Your competitors are bidding $47/click for those customers. How many of those calls are you missing?"

---

## API #6 — On-Page SEO Audit (Optional)

**Endpoint:** `/v3/on_page/task_post/`

**Cost:** $0.000125 per crawled page (cheap)

**Returns:** Meta tags, H1/H2s, page speed, broken links, duplicate content, HTTP status codes, readability.

**Pitch use:** "Your website has 14 broken links, no meta descriptions, and loads in 6.2 seconds. Google wants under 2.5."

---

## What $50 Buys You

| Scenario | Volume |
|----------|--------|
| Maps SERP discovery only | 25,000 searches × 100 businesses = **2.5M businesses** |
| Full dossier (profile + 20 reviews) | **~10,000 businesses** |
| Full dossier + keyword data | **~8,000 businesses** |
| Just the 20-review pull only | **~33,000 businesses** |

---

## Cost Per Email Campaign

To build a campaign targeting 500 qualified businesses:

| Step | Cost |
|------|------|
| Discovery (5 Maps SERP searches × $0.002) | $0.01 |
| Deep profile on 500 hot leads × $0.0015 | $0.75 |
| 20 reviews on 500 businesses × $0.0015 | $0.75 |
| Keyword data (1 batch) | $0.075 |
| **Total for 500 custom dossiers** | **~$1.59** |

That's about **$0.003 per personalized email** with full SEO + review + profile data.

---

## The AI Receptionist Email Formula

With this data you can auto-generate emails that say things like:

> "Hey [Business Name], I noticed you have 3 reviews from this month mentioning calls going to voicemail — one from [reviewer] who said '[exact quote]'. Based on your Google data, you're busiest on Thursdays between 10am–1pm. That's likely when those calls are coming in. Our AI receptionist answers every call, books appointments, and texts the customer back — all for less than $2/day. Want to see what that would have meant for those 3 missed leads?"

That level of specificity converts. Nobody has seen an email like that.

---

## Technical Notes

### Standard Pricing Tiers
- **Standard:** Task runs in background, poll for results. 3x cheaper.
- **Priority:** Faster queue, still async. 1.5x standard price.
- **Live:** Synchronous, instant. 3x standard price.

### Authentication
All requests use HTTP Basic Auth with your DataForSEO login/password.

### Rate Limits
- Standard: No hard limit, parallel task posting encouraged
- Live: Throttled, use concurrent connections carefully

### Python SDK
```python
pip install dataforseo-client
```
Or use raw `requests` with Basic Auth — simpler for scripts.

---

## Platforms DataForSEO Covers (Reviews)

| Platform | Supported | Notes |
|----------|-----------|-------|
| Google | ✅ Full | Primary. 4,490 reviews max per pull |
| Trustpilot | ✅ Full | B2C services |
| Tripadvisor | ✅ Full | Hospitality/restaurants |
| Google Play | ✅ | Apps only |
| App Store | ✅ | Apps only |
| Amazon | ✅ | Products only |
| Yelp | ❌ | Not available |
| Facebook | ❌ | Not available |

---

## Skip These (Not Worth It for Your Use Case)

| API | Why Skip |
|-----|----------|
| Backlinks | $100/month minimum |
| Domain Analytics | Overlap with On-Page |
| Content Analysis | Not relevant |
| AI Optimization (LLM Mentions) | Not relevant |
| App Data | Not relevant |
| Merchant (Amazon/Shopping) | Not relevant |
| Social Media (Pinterest/Reddit) | Not relevant |

---

## Next Steps — Python Scripts to Build

1. **`discover_businesses.py`** — Maps SERP for niche + city → CSV of 100 businesses
2. **`score_leads.py`** — Filter by rating_distribution, flag low-rating + unclaimed
3. **`profile_hot_leads.py`** — My Business Info for flagged businesses → extract place_topics
4. **`pull_reviews.py`** — Google Reviews (20 newest + 20 lowest) → extract missed call keywords
5. **`build_dossier.py`** — Combine all data into per-business JSON
6. **`generate_email.py`** — Template engine using dossier data → personalized outreach

Each script is modular — run steps 1–2 first, then only pay for steps 3–4 on qualified leads.
