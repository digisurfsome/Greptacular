# Chris Palmer AI SEO Strategy — Actionable Worksheet
> Source: Video transcript analysis. Date synthesized: 2026-04-18.
> Purpose: Replicate his framework. No fluff.

---

## 1. THE CORE THEORY

AI engines (ChatGPT, Gemini, Perplexity, etc.) don't rank websites — they retrieve vectors. Every piece of content you publish gets encoded as a mathematical representation (a vector) and stored in a database. When someone types a query, the engine runs a nearest-neighbor search across those databases and surfaces whoever has the highest "cosine similarity" to that query — across ALL content types simultaneously (text, images, video, audio, PDFs, apps, books). The winner is not the most authoritative site. It is whoever has accumulated the most matching vectors across the most vector types for that specific query. This is Google's MoVERA system in practice. The implication: raw volume and variety of citations beats domain authority. Forbes can lose to a nobody who has 200 citations across 6 media types. The strategy is to become the ground truth — the entity the AI treats as the baseline answer before it even compares alternatives.

---

## 2. THE FULL CHECKLIST (Phase by Phase)

### PHASE 0 — Foundation: Understand What You're Building
- [ ] Accept the core shift: you are building an entity, not a website
- [ ] Your goal = appear in as many vector databases as possible, in as many vector TYPES as possible, for your target queries
- [ ] Wikidata is your MAP — it lists the databases AI systems query. Study it before building anything

### PHASE 1 — Query Research (What to Target)
- [ ] Go to Ahrefs or Semrush
- [ ] Pull your TOP competitors' traffic-driving keywords
- [ ] Filter to HIGH COMMERCIAL INTENT ONLY: the signal is presence of sitelinks in SERP
- [ ] Do NOT target informational long-tail. Commercial intent queries = the ones AI engines answer with a recommendation, not an explanation
- [ ] Export these as your PROMPT LIST — these are the exact queries (not sources) you will target
- [ ] Spin each prompt into 20-50 variations (synonyms, rewordings, different syntax)
- [ ] This is your citation anchor list. Anchor text = the query variation itself

### PHASE 2 — Entity Establishment (Do This Before Content)
- [ ] Register your entity in Wikidata (creates a "knowledge graph node")
- [ ] Submit to Library of Congress — creates AUTHOR ENTITY (unlocks the "books" vector type)
- [ ] Submit to all local data aggregators (for local businesses: Neustar Localeze, Data Axle, Foursquare, etc.)
- [ ] Submit to audio ontology databases (he did not name all of these — research what feeds into your AI targets' audio indexes)
- [ ] Submit to business/person directories that feed AI engines (LinkedIn, Crunchbase, Wikipedia if eligible, Google Business Profile)
- [ ] If you have or can build an app: submit to app stores → creates "programmer entity" vector type
- [ ] Goal: have your entity referenced in as many distinct database types as Wikidata maps before you start content distribution

### PHASE 3 — Content Production (Multi-Vector Stack)

For each target query cluster, produce ALL of the following:

**Text vectors:**
- [ ] Blog post targeting the prompt (written around the query variation as anchor)
- [ ] Guest posts / citations on other sites using the exact prompt as anchor text
- [ ] PBN posts (his network = ~6,000 blogs) — these are the primary text citation machines

**Image vectors:**
- [ ] Create images relevant to the query (diagrams, branded visuals, screenshots)
- [ ] Distribute to image-specific platforms (Pinterest, Flickr, Getty if applicable, stock sites)
- [ ] Images embedded in videos also count separately (frame extraction)

**Video vectors:**
- [ ] Create a YouTube video for each major query cluster
- [ ] YouTube creates THREE sub-vectors automatically: video itself + frame images + auto-transcript (text)
- [ ] Optimize title/description with the exact query prompt
- [ ] YouTube RSS feed can feed into podcast distribution automatically

**Audio vectors:**
- [ ] Use 11Labs to convert existing blog text to audio (text-to-speech)
- [ ] Package as a podcast episode with an RSS feed
- [ ] Distribute RSS feed to: Apple Podcasts, Spotify, Google Podcasts, Amazon Music, and any audio-specific ontology DB
- [ ] Use Grok (or equivalent) to transcribe audio back to text → creates ANOTHER text citation
- [ ] Result: one blog post → audio → podcast listing → transcript = 4 vectors from one piece of content

**PDF vectors:**
- [ ] Convert key content to PDF format
- [ ] Distribute to PDF/document hosting sites (Scribd, SlideShare, Academia.edu, etc.)
- [ ] PDFs have their own retrieval pathway in AI engines

**Book vectors:**
- [ ] Compile related content into a short ebook or guide
- [ ] Publish via Library of Congress route (requires author entity from Phase 2)
- [ ] Self-publishing on Amazon KDP also creates a vector (ISBN = entity anchor)

### PHASE 4 — Citation Distribution

**Tier 1 — PBN (Primary citation engine):**
- [ ] Post target-query content to your PBN (~6,000 blogs if replicating his setup)
- [ ] PBN sites should be on fast HTML cloud hosting (speed is a hard factor — see Section 3)
- [ ] Each PBN post uses a query variation as anchor text pointing back to your money site

**Tier 2 — GSA (Blast distribution):**
- [ ] Set up GSA (Global SEO Autocomplete) or buy his $20 service
- [ ] GSA distributes to ~240,000 blog comment sites
- [ ] These are secondary citation signals, not primary content
- [ ] Anchor text = your prompt variations

**Tier 3 — Organic citation building:**
- [ ] PR campaigns that generate named citations
- [ ] Podcast guest appearances (audio vector + text transcript + potential backlink)
- [ ] Forum participation where your entity/brand name appears in context

### PHASE 5 — Speed Optimization (New Hard Factor)

- [ ] Move PBN sites and money site to fast HTML cloud hosting
- [ ] Target sub-100ms TTFB for all content-serving URLs
- [ ] This is NOT optional — see Section 3 for why speed is now a hard ranking factor in AI retrieval
- [ ] Minimize JavaScript rendering on pages that need to be bot-crawled into vector DBs
- [ ] Static HTML pages get retrieved and encoded faster than JS-heavy pages

### PHASE 6 — Monitoring & Iteration

- [ ] Track which queries you appear in across AI engines (ChatGPT, Perplexity, Gemini)
- [ ] When you rank for a query in one AI engine, push more citations to replicate in others
- [ ] Use competitor prompt research (Phase 1) on an ongoing basis — find new query gaps
- [ ] The strategy compounds: more citations → higher cosine similarity → AI uses you as ground truth → even more citations accumulate because you're the cited source

---

## 3. THE SPEED QUESTION — ANSWERED

Chris mentions "speed" in three distinct contexts. They are different things:

**Context A — TTFB / Technical page speed (ongoing, hard factor)**
This is new. He states explicitly that for the first time in SEO, page load speed is a HARD factor, not a soft one. Here is why: AI vector databases are populated by bots that retrieve and encode your content. If your page is slow (high TTFB, JS-rendered, heavy), the bot either times out, retrieves a partial render, or deprioritizes your content in the crawl queue. Fast HTML pages on cloud hosting get crawled more completely, more frequently, and therefore get encoded into vector DBs faster and with higher fidelity. His PBN sites run on static HTML for exactly this reason.

**Context B — First-mover temporal advantage (one-time, urgent)**
This is a "do it NOW" warning. AI systems are still building their ground truth baselines. The entity that accumulates the most citations for a query cluster FIRST becomes the baseline — the thing all other answers are measured against. Once you are the ground truth, competitors have to overcome your embedded position, not just match it. He says the window to establish this is narrow. Systems are solidifying. Every month you wait, someone else in your niche is potentially establishing their ground truth position.

**Context C — Retrieval tie-breaking (edge case)**
When two entities have near-identical citation counts and cosine similarity scores for a query, the AI engine defaults to the faster-retrieving source at inference time. This is MIPS (Maximum Inner Product Search) in action — it has a time budget per query, and the faster server wins the tie. This matters only when you're in a competitive race with a near-equal competitor.

**Summary:** Speed = (1) keep TTFB fast always, (2) start building citations NOW before the window closes, (3) fast hosting is a tie-breaker at inference time.

---

## 4. WHAT CAN BE AUTOMATED

| Task | Tool Mentioned | Cost |
|------|---------------|------|
| Prompt research (scraping competitor queries) | Ahrefs / Semrush API | ~$99-$399/mo |
| Prompt spinning (query variations) | Any LLM (GPT-4, Claude) | Cheap |
| GSA distribution (~240k blog comments) | GSA (Global SEO Autocomplete) | $20 via his service |
| PBN posting | Custom scripts / he has his own system | Not specified |
| Blog text → audio | 11Labs API | ~$5-$22/mo depending on volume |
| Audio → transcript (text citation) | Grok / Whisper API | Near-zero |
| YouTube RSS → podcast feed | RSS bridge tools (no-code) | Free |
| Image creation + distribution | Midjourney + distribution scripts | ~$10/mo + dev time |
| PDF generation from posts | Puppeteer / wkhtmltopdf | Free |
| PDF distribution to hosting sites | Custom scripts or Zapier | Low |
| Entity database submissions | Manual first time, then automate re-submissions | Dev time |

**The fully automated pipeline would look like:**
1. Scrape competitor prompts → 2. Spin into variations → 3. Generate blog post per cluster → 4. Auto-convert to audio (11Labs) → 5. Auto-distribute audio as podcast → 6. Auto-transcribe back to text → 7. Generate images → 8. Auto-post to image sites → 9. Convert to PDF → 10. Distribute to PDF sites → 11. Post to PBN with query anchors → 12. Run GSA blast → 13. Monitor AI engine appearances

Steps 3-13 are all automatable with existing tools.

---

## 5. CAVEATS & UNCLEAR PARTS

**The word he kept reaching for:**
He blanked on a specific ML term multiple times. Based on context ("the thing that AI engines use as the baseline answer before comparing others"), that word is almost certainly "ground truth" — the ML term for a known-correct baseline that a model is calibrated against. Secondary possibility: "benchmark."

**Biggest unverified claim — GSA comment spam:**
He treats GSA blog comment distribution as a legitimate citation signal for AI vector databases. This is unproven. Blog comments are low-quality, often noindexed, and may not be crawled by AI engine bots the same way primary content is. His claim appears to rest on the volume argument (240k citations = signal regardless of quality), but there is no public evidence AI engines weight comment-section citations the same as primary content citations. Treat this as the highest-risk tactic in the stack.

**No specific citation threshold:**
He never gives a number. "How many citations do you need to win?" is unanswered. He implies "more than your competitor" but gives no baseline. For a new market with no established entity, the number could be low. For a competitive market with an entrenched entity, you may need thousands.

**Wikidata as a complete map — assumption:**
He treats Wikidata as if it maps ALL vector databases AI engines query. It maps many, but AI companies (OpenAI, Anthropic, Google) use proprietary training and retrieval pipelines that are not fully documented. Wikidata is a useful proxy, not a definitive list.

**PBN legality/risk in 2026:**
He discusses a PBN of 6,000 blogs casually. Google's stance on PBNs remains "link scheme = penalty." Whether Google's penalties translate to AI engine citation penalties is an open question, but if your PBN gets deindexed from Google, those citations disappear from the text vector pool.

**Traditional vs. AI SEO overlap:**
He implies this strategy works for BOTH traditional Google ranking AND AI engine ranking. The overlap is real (citations, speed, entity authority all matter in both), but the two systems are not identical. Some tactics (GSA blasts) that may help AI citations could actively hurt traditional rankings if they trigger spam filters.

---

## 6. TOOL / APP BLUEPRINT

What a tool that automates his strategy would look like:

**Module 1 — Query Intelligence**
- Input: competitor domain(s)
- Process: pull ranking queries via Ahrefs/Semrush API, filter by commercial intent signal (sitelinks), deduplicate
- Output: ranked prompt list with intent scores

**Module 2 — Prompt Spinner**
- Input: prompt list
- Process: LLM generates 20-50 syntactic/semantic variations per prompt
- Output: expanded anchor text library

**Module 3 — Content Factory**
- Input: prompt cluster + anchor library
- Process: LLM generates blog post, auto-creates images (Midjourney/DALL-E API), generates PDF, sends text to 11Labs for audio
- Output: blog post + images + PDF + audio file per cluster

**Module 4 — Multi-Vector Distributor**
- Input: content package per cluster
- Process: 
  - Post to CMS/PBN (API or headless browser)
  - Upload to YouTube (YouTube Data API)
  - Distribute audio as podcast (RSS feed auto-update)
  - Submit images to image platforms
  - Upload PDF to document sites
  - Trigger GSA blast with anchor text list
- Output: distribution log with URLs per vector type

**Module 5 — AI Appearance Monitor**
- Input: target query list
- Process: query ChatGPT, Perplexity, Gemini APIs with each prompt, check if your entity is cited in response
- Output: citation score per query, per AI engine, over time

**Module 6 — Entity Database Manager**
- Input: your entity profile (name, description, properties)
- Process: submit/update entity to Wikidata, Library of Congress, local aggregators, audio ontology DBs
- Output: submission log + entity ID per database

**Stack to build this:**
- Backend: Python (existing server pattern in this repo)
- Queue: Redis or simple DB-backed job queue
- APIs: Ahrefs/Semrush, OpenAI/Anthropic, 11Labs, YouTube Data API, Perplexity API
- Difficulty to build the full stack: 8/10
- Difficulty to build Modules 1-2 only (query intel + spinning): 3/10
- Difficulty to build Module 5 only (AI appearance monitor): 4/10

The highest-value starting point with lowest difficulty is Module 5 (monitor) + Module 1 (query intel). Those two together tell you where you stand and what to target. The distribution modules (3-4) are the complex engineering work.
