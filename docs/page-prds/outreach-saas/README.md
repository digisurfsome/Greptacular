# PRD: Contact Form Outreach SaaS

## The One-Line Pitch

Everything cold email promises, none of what it demands — working on day one, personalized with live competitor data, under $5 per 100 sends.

---

## The Problem It Solves (Cold Email's Full List Of Failures)

Every agency and marketer doing cold outreach deals with this stack of pain:

| Cold Email Problem | This Product |
|-------------------|--------------|
| 30-day domain warming before first send | Gone. No domains. No warming. Ever. |
| Multiple email accounts + infrastructure | Gone. One reply inbox. |
| SPF/DKIM/DMARC setup | Gone. Their server sends the notification. |
| Deliverability constantly breaking | Gone. You're not the sender. |
| 1% open rate on generic blasts | 8-12%+ with data-powered subject lines |
| Tools cost $100-200/month before it even works | Under $10/month in API costs to run |
| Month to set up, weeks to see results | Works today |

This doesn't compete with cold email. It makes cold email look like fax machines.

---

## What It Is

A SaaS where a user picks a niche and a city, and the system:

1. Pulls the top businesses in that niche from local search results
2. Scrapes competitor rankings and traffic values (SEO data)
3. Filters the list — finds contact form URLs, flags blockers
4. Generates a personalized email for each business showing them exactly what their competitors are making in free traffic
5. Submits every email through their contact forms automatically
6. Replies land in the user's inbox

**One dashboard. Three inputs. Everything else automated.**

---

## The Three Tiers (Product Structure)

### Tier 1 — The Sender (Baseline Product)
Just the contact form submitter. User uploads a CSV, writes their own email, system sends it via contact forms.

- No warming, no domains, no deliverability issues
- Works on any list, any niche, any email
- Still better than cold email for setup time alone
- Price point: **$29-49/month**

This alone is a sellable product. Agencies who already write their own emails just want the sending mechanism.

### Tier 2 — The SEO Hook (The Killer App)
Everything in Tier 1 plus the full automated pipeline:
- User picks niche + city
- System does the SEO search automatically (no Ahrefs needed — built in)
- Generates the list
- Writes the personalized email with competitor data injected
- Sends it all

Subject line goes out looking like:
> *"Joe's Plumbing is getting $10,400/mo free — [Their Business] is at #14"*

Open rate estimated 8-12%+. Conversion estimated 3-5x standard cold email.

- Price point: **$97-197/month**
- Or: **$49/campaign** (one city, one niche = one campaign) for lower-volume users

### Tier 3 — Multi-Hook (Future)
Same system with hooks beyond SEO:

| Niche | Hook | Data Source |
|-------|------|-------------|
| Web design | Their PageSpeed score vs top 3 | Google PageSpeed API (free) |
| Reputation mgmt | Their review count vs competitors | Google Maps scrape |
| PPC management | Estimated competitor ad spend | SimilarWeb/SpyFu |
| Social media mgmt | Posting frequency gap | Social scraper |

Each new hook = new niche unlocked. Same engine underneath.

- Price point: **$197-297/month** for full multi-hook access

---

## Target Market (In Order)

### Phase 1: SEO Agencies
They already:
- Have Ahrefs or SEMrush (or we do the search for them)
- Do cold outreach to get clients
- Understand keywords, rankings, traffic values — the hook lands immediately
- Are already spending $100-200/month on cold email tools that don't work as well

This is the easiest sell. You're not teaching them a new concept. You're showing them a better version of what they already do.

**Pitch:** *"You're already doing cold outreach. This version shows prospects their competitors' traffic values in the subject line and sends through contact forms — no warming, works today. 4-12x better open rate."*

### Phase 2: Local Service Agencies (Broader)
Web design, reputation management, PPC, social media management. Same system, different hook per niche.

### Phase 3: Any Business Doing B2B Outreach
The Tier 1 sender (no SEO hook) works for any business reaching out to other businesses. Generic market.

---

## The Flywheel

This product isn't just revenue. It's a relationship engine.

Every business that responds to an outreach email is a potential:
- **Paying client** for SEO/web services
- **Beta tester** for the next product you build
- **Case study** for the SaaS itself

The goal isn't just to sell the SaaS. It's to build a network of 20-30 local business relationships who trust you enough to try new software when you release it. That's a distribution channel that costs nothing to maintain once it's running.

Flywheel:
```
SaaS users do outreach → they get clients → you get testimonials + case studies
        ↓
Case studies attract more SaaS users
        ↓
You use the same tool for your own outreach → you get business relationships
        ↓
Those relationships become beta testers for future products
        ↓
Beta testers give feedback → better products → more case studies
```

---

## The City-By-City Strategy (Built Into The Product)

**Why you don't flood one city:**
If you help 10 plumbers in Chicago rank higher, they're all competing with each other. You're fighting yourself. You want 1-2 clients per niche per city, max.

**So the product is designed to:**
- Let user set a "per city cap" (e.g., only contact 25 of 50 results)
- Track which cities/niches have been contacted
- Suggest the next city automatically

**The scale math:**
- 300 cities with plumbers in the US (rough count of mid-to-large markets)
- 1 Ahrefs search per city = 300 searches for the entire plumber niche
- 25 contacts per city × 300 cities = 7,500 targeted personalized outreach emails
- All from ONE niche. Then do roofers. Then HVAC. Then electricians.

The TAM for just local home service niches is enormous and completely automated once the system is built.

---

## The Spinner (Cost Structure For Users)

Users don't write emails. They don't use a spinning service. The system handles it.

**One-time per niche:**
- System generates 25 variant sentences for each section of the email template (~$0.10 in API cost)
- Stored forever, never regenerated

**Per email assembly:**
- Pure Python random selection from variant pool
- $0 per email, forever

**What changes per email:**
- Business name, contact name
- Their ranking, competitor names, competitor traffic values
- Everything else is spun variants — looks unique every time

**What the user actually pays for:**
- Monthly subscription to the SaaS
- Under the hood: Haiku API (~$0.01-0.03/send) + optional 2captcha for CAPTCHA sites (~$0.002/send)
- User sees none of this — it's baked into the subscription margin

---

## Unit Economics

**Cost to run per user per month (500 sends/day, ~15,000/month):**

| Item | Monthly Cost |
|------|-------------|
| Haiku API (15k sends × $0.02 avg) | ~$300 |
| 2captcha (assume 30% hit CAPTCHAs × $0.002) | ~$9 |
| Hosting/infrastructure | ~$20-50 |
| **Total to serve heavy user** | **~$330-360/month** |

At $197/month Tier 2 pricing, heavy users eat into margin. Solutions:
- Cap sends at 200/day included, charge overages ($5 per 100 extra sends)
- Or price Tier 2 at $297+ for unlimited

**Light user (100 sends/day, ~3,000/month):**
- API cost: ~$60-90/month
- Hosted for $50/month = $110-140/month cost
- At $97/month: thin, but marketing tool for their business justifies it
- At $197/month: solid margin

**The pricing model that works:**
- $97/month: 100 sends/day included (3,000/month)
- $197/month: 300 sends/day included (9,000/month)
- $297/month: unlimited + multi-hook access
- Overage: $5 per 100 sends above cap

---

## What Makes This Hard To Copy

1. **The contact form filter is non-obvious.** Most people think you just submit forms. The blocker detection (CAPTCHA types, Cloudflare, honeypots, JS-only forms) is the real IP that took research to figure out.

2. **The SEO data pipeline.** Pulling ranking data + calculating traffic value from CPC estimates is a built system, not a CSV import.

3. **The spinner + data injection combo.** Everyone knows spinners exist. No one has combined it with live competitor data as the hook. That's the angle.

4. **No warming required as a feature.** This is the marketing hook itself. Incumbents (Instantly, Smartlead) can't claim this — their entire product is built around the warming problem.

---

## Build Phases

### Phase 0 (Already Partially Done)
- Contact form filter script (V1 PRD)
- Browser-use form submitter (V1 PRD)
- SEO data tool (already built separately)

### Phase 1 — Working Internal Tool
- Wire filter + assembler + runner into one script
- Test on real lists, measure actual success rate and cost
- Use it for your own outreach before selling it

### Phase 2 — Tier 1 SaaS (MVP)
- Simple dashboard: upload CSV + write email + send
- No SEO hook yet, just the sending mechanism
- Get 5-10 paying beta users, measure results

### Phase 3 — Tier 2 (The Real Product)
- Niche + city input
- SEO data pulled automatically
- Email assembled automatically
- Full pipeline in one click
- Charge $97-197/month

### Phase 4 — Multi-Hook + Scale
- Add hooks for other niches (PageSpeed, reviews, ad spend)
- Each hook = new market segment

---

## Files (Technical, See Linked PRDs)

The technical build lives in:
- `docs/page-prds/contact-outreach/README.md` — V1 build (filter + browser-use, clean sites)
- `docs/page-prds/contact-outreach/README-v2-full.md` — V2 build (+ 2captcha + proxies)

This document is the product/business layer on top of those builds.

---

## Why This Is The Right Moment

- browser-use hit 79k GitHub stars in under 2 years — the underlying tech just became reliable enough
- Haiku 4.5 now supports computer use — the cost floor just dropped
- Cold email tools are getting more expensive and more restricted (Google/Yahoo 2024 sender requirements killed a lot of setups)
- Local businesses are drowning in generic outreach — a personalized email showing them their competitors' exact traffic value is genuinely novel
- Nobody has packaged this into a product yet. The window is open.

---

## Full Pipeline Wiring (SEO Niche Outreach)

This section describes exactly how the data flows from user input to contact form submission — every step, every decision, every file.

---

### Step 1 — Keyword Discovery (Once Per Niche, City-Agnostic)

**Input:** Niche name (e.g., "plumber")
**Output:** Top 3 buyer-intent, phone-call-inducing keywords for that niche

These keywords do not change by city. "Emergency plumber" works in Chicago, Dallas, and Phoenix. Run this once per niche, store the result, reuse it forever for every city campaign.

**How to get them:**

Option A — DataForSEO keyword data (deterministic, preferred):
Pull top keywords for the niche by search volume × CPC. High CPC = high commercial intent = phone calls. Filter for local intent keywords (include city/location modifiers or "near me").

Option B — LLM judgment (fallback if DataForSEO doesn't have it):
Prompt: *"What are the top 3 buyer-intent keywords a local plumber would want to rank for in Google Maps that would generate emergency/high-intent phone calls? Return only the keywords, no city included."*
Haiku handles this reliably for common local service niches.

**Storage:** JSON file or database table keyed by niche name.
```json
{
  "plumber": ["emergency plumber", "plumber near me", "24 hour plumber"],
  "roofer": ["roof repair", "emergency roof repair", "roofing contractor"],
  "hvac": ["ac repair", "emergency hvac", "furnace repair near me"]
}
```

**Cost:** ~$0.01 LLM call or pennies of DataForSEO credit. Done once per niche ever.

---

### Step 2 — SERP Search (Per City, 3 Searches)

**Input:** 3 keywords from Step 1 + city name
**Output:** Top 20 rankings per keyword with traffic value estimates

Run each keyword through DataForSEO (or equivalent SEO API) for that city. Each search returns:
- Business name
- Website URL
- Rank position (1-20)
- Estimated monthly traffic value (based on CPC × estimated clicks at that rank position)

**Cost:** ~$0.03-0.05 per search × 3 keywords = ~$0.10-0.15 per city total.

**Storage:** Intermediate CSV or in-memory dict keyed by website URL.
```
keyword, rank, business_name, website_url, traffic_value
emergency plumber, 1, Joe's Plumbing, joesplumbing.com, 10400
emergency plumber, 2, City Plumbers, cityplumbers.com, 5200
...
```

---

### Step 3 — Business List + Cross-Reference

**Input:** All plumbers in that city (scraped from Google Maps or provided list) + SERP results from Step 2
**Output:** Master CSV with every business + their rank position for each of the 3 keywords

**Process:**
1. Get full list of businesses in niche + city (Google Maps scrape, or user uploads list)
2. For each business, look up their URL against the 3 SERP result sets
3. Record their rank on each keyword (or "not ranked" if outside top 20)
4. Pull the top 3 competitors from each keyword for use in email hook

**Output CSV shape:**
```
website_url, business_name,
kw1, kw1_rank, kw1_traffic,
kw2, kw2_rank, kw2_traffic,
kw3, kw3_rank, kw3_traffic,
comp1_name, comp1_kw, comp1_rank, comp1_traffic,
comp2_name, comp2_kw, comp2_rank, comp2_traffic,
comp3_name, comp3_kw, comp3_rank, comp3_traffic,
top_competitor, top_traffic,
email_tier
```

---

### Step 4 — Segmentation Logic (Assign Email Tier)

Every business gets assigned one of three email tiers based on their ranking across the 3 keywords.

```python
def assign_tier(kw1_rank, kw2_rank, kw3_rank):
    ranks = [r for r in [kw1_rank, kw2_rank, kw3_rank] if r is not None]

    if not ranks:
        return 'D'  # Not in top 20 on any keyword — AI Search pivot

    best_rank = min(ranks)

    if best_rank <= 3:
        return 'A'  # Already in top 3 on at least one keyword
    elif best_rank <= 10:
        return 'B'  # In top 10 on at least one keyword, not yet top 3
    else:
        return 'C'  # In top 11-20 somewhere — ranked but buried
```

**What each tier means strategically:**

**Tier A — Ranked 1-3 (Hottest Lead)**
They already believe in SEO. Getting results. Know the value.
Email angle: *"You're dominating [keyword1] — great. But [Competitor] owns [keyword2] and [keyword3] worth $X/mo combined. We can get you there too."*
Expected response rate: Highest. They get it immediately.

**Tier B — Ranked 4-10 (Easiest Close)**
Close enough to smell the top. One push.
Email angle: *"You're at #[rank] for [keyword] — almost there. [Competitor] at #1 is pulling $X/mo. One campaign gets you there."*
Expected response rate: High. The gap feels closeable.

**Tier C — Ranked 11-20 (Buried In Results)**
In the results but invisible to anyone who doesn't scroll. Most people never get past the top 3.
Email angle: *"You're ranking #[rank] for [keyword] — that's page 2 territory. [Competitor] at #1 gets $X/mo. Nobody calls #[rank]."*
Expected response rate: Medium. Pain is real but less urgent than D.

**Tier D — Not In Top 20 On Any Keyword (AI Search Pivot)**
Completely off the map for traditional search. Different pitch entirely.
Email angle: *"Traditional Google Maps rankings take months to move — and you're starting from scratch. But Google AI Search, ChatGPT local results, and Ask AI Maps just launched. Almost nobody in [city] has claimed their spot yet. We can get [Business Name] there fast while everyone else is still fighting over the old results."*
Expected response rate: Unique — you're not selling them on a long climb, you're showing them a new lane.
This tier is also the direct pipeline into your AIO SaaS when it launches.

---

### Step 5 — Email Assembly Per Tier

Each tier has its own spinner variant pool (generated once per niche, stored forever).

**Four variant pools:**
- `spinner_tier_a.json` — Already ranking top 3, expand to other keywords
- `spinner_tier_b.json` — Almost there (4-10), push to top 3
- `spinner_tier_c.json` — Buried (11-20), make the gap feel real
- `spinner_tier_d.json` — Off the map, pivot to AI Search opportunity

**Subject line strategy by tier:**

Tier A: *"You rank #1 for [keyword1] — [Competitor] owns [keyword2] ($X/mo)"*
Tier B: *"[Business] is at #[rank] for [keyword] — [Competitor] at #1 gets $X/mo"*
Tier C: *"[Comp1] $X, [Comp2] $X, [Comp3] $X — [Business] is at #[rank] on all three"*
Tier D: *"[Comp1], [Comp2], [Comp3] own [keyword] in [city] — but AI Search is wide open"*

Tier C with dollar amounts + their buried rank is extremely strong. Tier D's AI Search angle is a pattern interrupt — nobody else is sending that email.

**Assembly logic:**
```python
def assemble_email(row):
    tier = row['email_tier']
    variants = load_variants(f'spinner_tier_{tier.lower()}.json')
    
    # Same spinner assembly as base system
    # Injects: business_name, kw1/kw2/kw3 rankings,
    #          competitor names, traffic values, city
    return build_from_variants(variants, row)
```

---

### Step 6 — Contact Form Filter + Send

Same as V1/V2 technical PRDs. The assembled `ready_to_send.csv` feeds directly into `filter.py` then `runner.py` or `orchestrator_v2.py`.

No changes needed to the sending layer. The data enrichment above just fills more columns.

---

### Full Wiring Diagram

```
User Input: Niche + City
        |
        v
Step 1: keyword_discovery.py
  → Checks niche cache (JSON)
  → If not cached: DataForSEO or LLM → get top 3 keywords → cache
  → Output: [kw1, kw2, kw3]
        |
        v
Step 2: serp_search.py
  → DataForSEO API × 3 keywords for this city
  → Output: serp_results.csv (top 20 per keyword + traffic values)
        |
        v
Step 3: build_list.py
  → Get all businesses in niche + city (Maps scrape or upload)
  → Cross-reference each against serp_results.csv
  → Assign kw1_rank, kw2_rank, kw3_rank per business
  → assign_tier() → email_tier column
  → Output: enriched_list.csv
        |
        v
Step 4: assemble_emails.py (same script, reads tier for variant pool selection)
  → Spinner picks tier-appropriate variants
  → Injects all custom data
  → Output: ready_to_send.csv
        |
        v
Step 5: filter.py
  → Finds contact URL, detects blockers
  → Output: routed_list.csv (with blocker_type)
        |
        v
Step 6: runner.py (V1) or orchestrator_v2.py (V2)
  → Submits each form
  → Logs results
```

---

### Cost Per City Campaign (Full 3-Keyword SEO Pipeline)

| Step | Cost |
|------|------|
| Keyword discovery (once per niche, cached) | ~$0.01 |
| 3 SERP searches via DataForSEO | ~$0.10-0.15 |
| Business list scrape (Google Maps) | ~$0 (if self-scraped) |
| Email assembly (50 businesses) | $0 |
| Contact form sends — V1 clean only (~30 of 50) | ~$0.45 |
| Contact form sends — V2 full list (~45 of 50) | ~$1.35 |
| **Total per city — V1** | **~$0.60** |
| **Total per city — V2** | **~$1.50** |

One city. One niche. Under $1.50. Then next city.

---

### What's City-Agnostic vs City-Specific

| Item | Scope | Run How Often |
|------|-------|--------------|
| Top 3 keywords per niche | Global (same everywhere) | Once per niche, ever |
| Spinner variant pools (per tier) | Global (same everywhere) | Once per niche, ever |
| SERP search results | Per city | Once per city campaign |
| Business list | Per city | Once per city campaign |
| Email assembly | Per business | Each campaign |
| Contact form send | Per business | Each campaign |

The global assets (keywords, spinner pools) are built once. The city-level work is a few API calls and a Python script. This is why the per-city cost is under $2 even for the full V2 pipeline.
