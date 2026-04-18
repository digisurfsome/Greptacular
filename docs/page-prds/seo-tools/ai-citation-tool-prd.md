# PRD: AI Citation Dominator Tool
> Status: Draft v1 — 2026-04-18
> Purpose: Test and replicate Chris Palmer's multi-vector AI citation strategy for local niches.
> Scope: Minimum viable tool to find a winnable market, measure the gap, manufacture citations, and verify AI appearance.

---

## The One-Sentence Version

Find a local niche where the leader has weak AI citations, manufacture 2-3x their citation count across multiple content types, and verify you show up in ChatGPT/Perplexity/Gemini for the money phrases.

---

## Core Philosophy

You are not doing SEO. You are manufacturing "ground truth" for AI engines.
- AI engines rank by cosine similarity (nearest neighbor) — whoever has the most matching mentions wins.
- Authority does not matter. Volume does.
- You only target HIGH COMMERCIAL INTENT queries. Everything else is wasted effort.
- The goal is to be cited more times, in more content types, than your competitor — for the specific phrases that lead to sales.

---

## The 6-Step Workflow

### Step 1 — Market Scanner
Find a niche + city where the gap between leader and zero is small.

**Inputs:**
- Target city (population 100k–400k recommended for testing)
- Target niche / service category

**Process:**
- Query Perplexity, ChatGPT, and Gemini: "best [service] in [city]"
- Check if a confident named entity is returned or a vague generic answer
- Vague answer = wide open market. Confident named entity = has a leader (now audit them)

**Output:**
- AI confidence score per engine (named entity present = competitive, vague = open)
- Named competitor if one exists

---

### Step 2 — Competitor Citation Audit
How many citations does the current leader have, and in which vector types?

**Process:**
- Pull competitor domain into Ahrefs or Semrush (API)
- Count referring domains
- Manually check or scrape: do they have YouTube videos? A podcast? Images on image platforms? PDFs on document sites? An app? A book?
- Cross-check their entity in Wikidata — are they listed? In how many databases?

**Output per competitor:**
| Vector Type | Their Count | Your Target (2x) |
|-------------|-------------|-----------------|
| Text citations (backlinks/mentions) | X | 2X |
| Video (YouTube) | X | 2X |
| Audio/Podcast | X | 2X |
| Images on image platforms | X | 2X |
| PDFs on doc sites | X | 2X |
| Entity DB listings (Wikidata map) | X | 2X |

**Decision gate:** If their total is under ~200 across all types, this is a winnable test market. If over 500, skip and find a softer niche.

---

### Step 3 — Query Intelligence (Prompt Engine)
Find the exact money phrases you need to own.

**Process:**
- Pull competitor's ranking queries from Ahrefs/Semrush API
- Filter: HIGH COMMERCIAL INTENT ONLY
  - Signal: query returns a sitelink in Google SERP (local pack, direct answer, or site link under result)
  - Examples: "best [service] [city]", "[service] near me", "top [service] [city]", "[service] reviews [city]"
  - Exclude: "how to", "what is", "DIY", informational queries
- Take top 10 money phrases
- Spin each into 40–50 variations:
  - Synonyms ("best" / "top" / "top-rated" / "leading" / "most reliable")
  - Location variations ("in [city]" / "near [city]" / "[city] area" / "[county]")
  - Intent variations ("for hire" / "services" / "company" / "contractor")

**Output:**
- 10 core money phrases
- 400–500 spun variations (the citation anchor library)

---

### Step 4 — Content Factory
Generate content in all applicable vector types for your target queries.

**For each query cluster (run in batch):**

**Text:**
- [ ] Generate a blog post targeting the query cluster (LLM-generated, ~600 words)
- [ ] Use spun anchor variations as internal link text and in the body
- [ ] Produce one post per major query cluster (not per variation — one post covers all 50 variations of the same intent)

**Audio:**
- [ ] Send blog text to 11Labs API → returns MP3
- [ ] Package MP3 with title/description/cover art → upload as podcast episode
- [ ] RSS feed auto-distributes to Apple Podcasts, Spotify, Amazon Music
- [ ] Transcribe audio with Whisper API → produces a second text citation document

**Images:**
- [ ] Generate 3–5 images per query cluster (DALL-E or Midjourney API)
- [ ] Filename and alt text = core money phrase
- [ ] Upload to: Pinterest, Flickr, Imgur, relevant niche image boards

**PDF:**
- [ ] Convert blog post to PDF (Puppeteer headless render)
- [ ] Upload to: Scribd, SlideShare, Academia.edu, Issuu

**Video (optional for Phase 1 test — include if possible):**
- [ ] Screen record or use AI avatar tool to create a short video version
- [ ] Upload to YouTube with money phrase as title
- [ ] YouTube auto-creates: frame images + transcript = 3 vectors from one upload

---

### Step 5 — Distribution
Push citations to as many indexed locations as possible.

**Option A — Buy PBN access (recommended for testing):**
- Purchase posts on an existing blog network service
- See Section: "What to Look for in a PBN Network" below for speed requirements
- Use spun anchor text variations from Step 3
- Target: 50–150 PBN posts per query cluster for a test (not 6,000 — that's for national/competitive markets)

**Option B — Build your own micro-network (300 sites):**
- Register ~300 domains ($600–900/yr at $2–3/domain)
- Build on Astro (static site generator — sub-50ms TTFB, zero JS overhead)
- Host on Cloudflare Pages (free tier, global CDN, edge-served)
- Automate posting via existing content pipeline
- Each site = one themed niche blog, posts targeting your anchor variations
- Deployment: Astro + GitHub Actions + Cloudflare Pages = fully automated push-to-deploy

**Option C — GSA service:**
- Use Chris Palmer's $20 GSA service or equivalent
- Distributes to ~240k blog comment sites
- Treat as Tier 2 signal (volume booster, not primary citation source)
- Risk: comment links may not be crawled into AI vector DBs at same weight as primary content

---

### Step 6 — AI Appearance Monitor
Verify you're showing up. This is the entire point.

**Process:**
- Query ChatGPT, Perplexity, and Gemini with each of your 10 core money phrases (API calls)
- Parse response: is your target entity named? Is it the primary recommendation?
- Score: 0 = not mentioned, 1 = mentioned, 2 = primary recommendation
- Run weekly. Track score over time.

**Output:**
- Dashboard: per-engine, per-phrase citation score
- Trend line: are scores improving after citation campaigns?
- This IS your ranking tracker. No third-party tool needed. You're measuring directly.

---

## What to Look for in a PBN Network (Speed Factor)

Chris Palmer's insight: bots retrieve and encode fast pages faster. Slow sites get deprioritized in crawl queues. The PBN sites that are getting their citations picked up by AI vector databases are the FAST ones.

**When evaluating a PBN network's sales page, look for:**

| Term | What It Means | Good Sign? |
|------|--------------|-----------|
| "Static HTML sites" | No WordPress, no database queries, pure HTML files | ✅ Best |
| "Hosted on Cloudflare CDN" | Global edge network, files served from nearest server | ✅ Best |
| "Sub-100ms TTFB" | Time to First Byte under 100 milliseconds — this is the metric | ✅ Best |
| "Cloudflare Pages / Vercel / Netlify" | Static hosting platforms = very fast | ✅ Good |
| "No CMS overhead" | Not WordPress, not Drupal | ✅ Good |
| "Edge-hosted" | Served from CDN edge nodes globally | ✅ Good |
| "Built on Astro / Hugo / Jekyll / 11ty" | Static site generators = near-instant TTFB | ✅ Excellent |
| "AWS CloudFront" | Amazon's CDN — fast | ✅ Good |
| "WordPress blogs" | Database-driven, typically 300ms–2s TTFB | ⚠️ Avoid |
| No speed claims at all | Probably WordPress | ⚠️ Avoid |

**The magic phrase to search for:** "static site" + "CDN" + "TTFB" or ask directly: "What is the average TTFB of your network?" If they don't know what TTFB means, their network is WordPress. Move on.

**The technical name for what you want:** A PBN running on a **JAMstack architecture** (JavaScript/APIs/Markup — static pre-rendered files served via CDN). That's the industry term. If they use JAMstack or "static site generator" anywhere in their copy, that's the right type.

---

## Build Phases

### Phase 1 — Proof of Concept (Build This First)
- Module: Market Scanner (Step 1) — manual or semi-automated
- Module: Competitor Citation Audit (Step 2) — Ahrefs/Semrush API
- Module: Query Intelligence + Spinner (Step 3) — LLM-powered
- Module: AI Appearance Monitor (Step 6) — API calls to ChatGPT/Perplexity/Gemini
- **Difficulty: 4/10**
- **Goal: Prove the gap exists and you can measure it BEFORE building content factory**

### Phase 2 — Content + Distribution
- Module: Content Factory (Step 4) — text + audio pipeline (11Labs, Whisper, PDF)
- Module: PBN Distribution (Step 5A — buy access first, build own later)
- **Difficulty: 6/10**

### Phase 3 — Full Automation
- Own micro-network (300 Astro sites on Cloudflare Pages)
- Automated posting pipeline
- GSA integration
- **Difficulty: 8/10**
- **Don't build Phase 3 until Phase 1 proves the strategy works in a test niche**

---

## Recommended Test Plan

1. Pick a test niche using the Perplexity "vague answer" method
2. Run Steps 1–3 manually to identify the gap and build your anchor library
3. Generate 5–10 text posts targeting the query clusters
4. Buy 50 PBN posts on a fast static network
5. Distribute PDFs, images, and audio for the same clusters
6. Run the AI Appearance Monitor weekly for 4 weeks
7. If scores move → strategy confirmed → scale and build the full tool
8. If scores don't move → re-examine citation volume and vector type coverage before abandoning

---

## Tech Stack (Existing Greptacular Repo)

- Backend: Python (FastAPI — already in repo)
- Queue: existing job infrastructure
- APIs needed: Ahrefs or Semrush, OpenAI/Anthropic (content + spinning), 11Labs (audio), Whisper (transcription), Perplexity API, OpenAI API, Gemini API (monitoring)
- Frontend: new page in existing React UI following new-page-standards.md
- Page name: `AICitationPage` or extend existing `SEOToolsPage`
