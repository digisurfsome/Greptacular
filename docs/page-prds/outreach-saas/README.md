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
