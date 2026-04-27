# Outreach Playbook — AI Receptionist Pitch via Contact Forms

> Companion doc to `gohighlevel-mcp-langgraph-research.md` and `1prompt-os-comparison.md`. The cold-outreach + landing-page strategy for selling AI voice receptionists at 3–5 appointments/day.

## TL;DR

- **Niche v1:** Chiropractors or HVAC (high after-hours revenue intensity).
- **Custom data per business:** ~3¢/business via DataForSEO + Outscraper + Hunter.
- **Dual-purpose pitch:** SEO authority flex → voice-bot pivot → SEO fallback CTA.
- **Volume math:** 3000 contact forms/day → ~4 appointments/day.
- **Killer line:** "the same brain that wrote this email will be on the line if you call."

## Niche Ranking

| Niche | Pain | Job value | v1 fit |
|---|---|---|---|
| Chiropractor | High (pain calls) | $200/$2k LTV | ✅ Best for v1 |
| Emergency dental | Very high | $400/$2k LTV | ✅ |
| HVAC emergency | Very high | $300–$5k | ✅ |
| Plumber emergency | Very high | $200–$3k | ✅ |
| Locksmith | Very high (24/7 expectation) | $100–$500 | ✅ |
| Med spa | Medium (research-at-night) | $300/$3k LTV | v2 — premium |
| Roofing | Medium | $5k–$30k | v2 |
| Restaurants | Lower per-call value | $30 cover | Skip v1 |

## Per-Business Data Stack (~3¢/lead)

| Data | Source | Cost | Pitch use |
|---|---|---|---|
| Map pack rank + top 3 competitors | DataForSEO | $0.003 | Authority flex |
| GBP hours (open/close) | DataForSEO | (same) | "Closed 13 hrs/day" math |
| Review count + rating | DataForSEO | (same) | Pain math |
| **Recent review TEXT (last 20)** | Outscraper / SerpAPI | $0.01 | **Kill-shot quotes about "didn't answer"** |
| Phone number on listing | DataForSEO | (same) | Confirms target |
| Site has chat widget? | BuiltWith / scrape | $0 | "Competitors have one, you don't" |
| Owner first name | Hunter.io / Apollo | $0.05 | Personalization |
| Popular times data | Google Places | $0.017 | "Busiest hours = your closed hours" |

## Contact Form Message Template

**Subject:** `[Owner First Name], [Competitor 1] and [Competitor 2] are catching the calls you're missing after [Close Time]`

**Body:**

```
Hey [First Name],

Pulled your local rankings for "[Main Keyword]" this morning. You're 
#[Rank] in [City]. The map pack is locked up by [Comp 1] (#1, ~$[Rev]/mo 
from local search), [Comp 2] (#2), and [Comp 3] (#3).

That's not why I'm writing.

You close at [Close Time] and reopen at [Open Time] — that's [N] hours 
a day where calls go to voicemail. For [niche], [X]% of after-hours 
calls are revenue calls. They don't leave voicemail. They call [Comp 1] 
next.

[If review-text mining found a "couldn't reach" quote: 
 One of your recent reviews said: "[Quote]"]

At ~$[Avg Job Value] per [unit] and 3-4 missed calls a day, that's 
roughly $[Daily Loss]/day going to competitors. Per year: $[Annual Loss].

I built something that fixes this. An AI receptionist trained for 
[niche] businesses. Books straight into your calendar. Fair warning — 
it's so good the same brain wrote this email and will be on the line 
if you call.

Hear what yours would sound like: [yourdomain.com/[slug]]
30-day free trial. No card, no contract. $50 setup credit covers 
carrier fees during the trial.

Or if you'd rather talk SEO and outrank [Comp 1]: 
[yourdomain.com/[slug]/seo]

— [Your Name]

P.S. If you want to know how I built this for under a grand a month 
at [niche] businesses doing $50k+/mo, the call's free either way.
```

## Landing Page Structure

```
Hero: "[Business Name], here's what your AI receptionist would sound like."
       [Play button → custom audio recording per business]
       
Section 2 — The Math (filled from scrape):
       After-hours hours/day: [13]
       Calls missed/week: [21]
       Revenue at risk/month: $[X]

Section 3 — Live Chat Demo:
       Bot opens: "Hey [First Name], I'm the same brain behind that 
                  recording. Got 60 seconds? I'll show you how I'd 
                  handle a typical [niche] after-hours call."

Section 4 — Two CTAs:
       [BIG] Start 30-day free trial
       [smaller] I'd rather talk SEO

Section 5 — Existing edited demo video
```

## Hook Phrases for Chat / Page

- "Wait until you hear what this answers"
- "Knows your business better than the new person at your front desk on day one"
- "While your competitors' voicemails are silent at midnight, mine just booked an appointment"
- "Less than the cost of one missed call a day pays for the whole month"
- "30 years of sales experience packed into something that never has a bad day"
- "The smartest member of your team — never quits, never calls out sick"

**On "is it AI?" question:** Don't hide. "Yes, it's an AI receptionist. The voice is real-sounding because that tech is solved. The reason to use it isn't because it's AI — it's because it's better than what's answering your phone right now."

## Niche Math (memorize for the bot)

| Niche | Avg/LTV | After-hrs revenue % | Daily loss formula |
|---|---|---|---|
| Chiropractor | $200 / $2k LTV | 30% | 4 × 30% × $200 × 22 = $5,280/mo |
| Dental | $400 / $2k LTV | 40% | 3 × 40% × $2k × 22 = $52,800/mo (LTV) |
| HVAC emergency | $500 | 60% | 3 × 60% × $500 × 22 = $19,800/mo |
| Med spa | $300 / $3k LTV | 25% | 4 × 25% × $3k × 22 = $66,000/mo (LTV) |
| Restaurant catering | $1,500 catering | 10% of after-hours | 5 × 10% × $1500 × 22 = $16,500/mo |

Quote LTV math wherever applicable — single dental or chiro patient = $2k+, not $200.

## Conversion Funnel Math

| Stage | Rate | Daily |
|---|---|---|
| Contact forms sent | — | 3,000 |
| Engagement (custom-driven) | 5% | 150 |
| Landing page CTR | 30% | 45 |
| Chat/audio engage | 60% | 27 |
| Appointment booked | 15% | **4** ✅ |

Cost: ~$90/day scraping + GHL + LLM ≈ $5k/mo. 25% close at $497 MRR = $14k/mo new MRR/mo. Sustainable in 2 months.

## Sequence — How to Ship

1. Pick niche (chiropractor recommended for v1)
2. Build scrape pipeline: DataForSEO + Outscraper + Hunter
3. Generate 100 personalized landing pages (slug per business)
4. Voice bot configured + custom audio recordings auto-generated per business (TTS pre-render at scrape time)
5. Contact form template loaded, GSA campaign set
6. Send first 100 → measure
7. Iterate copy, scale to 500/day, then 3000/day
