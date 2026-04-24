# Automated Loom Video System

> Investigation + build plan for auto-generated screen-record videos (SEO reviews, site audits, personalized walkthroughs) that mimic a human Loom recording.
> Intended use: cold outreach at scale — "here's a free video audit of your site."

---

## 1. The Vision (What User Wants)

Mimic a 3-5 min Loom video. No talking head. Screen-record style:

1. Browser opens on their website (or GBP, or competitor site)
2. Cursor moves around naturally
3. Highlights / boxes / circles appear over things being discussed
4. Voice narration explains what's wrong + how to fix
5. Intro card w/ their logo, outro card w/ CTA
6. Fully automated from scraped biz data → finished MP4

**Competitor landscape:** Loom, Tella, Sendspark do manual recording. Vidyard has personalization but still manual. **Nobody is doing fully automated script + screen record + TTS at scale.** This is a real whitespace.

---

## 2. Feasibility Assessment

| Aspect | Difficulty | Confidence |
|--------|-----------|------------|
| Browser automation + recording | 3/10 | 95% |
| Custom cursor overlay | 4/10 | 90% |
| Element highlighting (boxes/circles) | 3/10 | 95% |
| Free TTS (quality + speed) | 2/10 | 99% |
| LLM script generation from scraped data | 5/10 | 85% |
| Voice + cursor + highlight timing sync | 6/10 | 75% |
| Final ffmpeg composite w/ intro/outro | 4/10 | 90% |
| Scalability to 1000/day | 7/10 | 60% |
| **Overall v1 to ship** | **6/10** | **80%** |

**Realistic read:** Prototype in a day of agent work. Production-polished SaaS-grade in 1-2 weeks including edge cases, CAPTCHA, anti-bot bypass, quality iteration.

---

## 3. Tech Stack (All Free / Open Source)

| Layer | Tool | Why |
|-------|------|-----|
| Browser automation | **Playwright** (Python) | Built-in video recording. Best API. Used by Microsoft. |
| Screen recording | Playwright's `context.new_page({recordVideo:...})` | No external recorder needed. Records viewport as WebM → ffmpeg to MP4. |
| Cursor rendering | **Custom JS injection** | Playwright headless = no visible OS cursor. Inject `<div>` + PNG, animate w/ JS. |
| Element highlighting | **Custom JS injection** | Box/circle/arrow overlays via injected DOM. |
| TTS | **Edge-TTS** (Python pkg) | FREE. Microsoft Edge's cloud TTS. 300+ natural voices. Azure-quality. Alt: Kokoro TTS (local, MIT). |
| Script generation | **Claude Haiku** or **Gemini Flash** | LLM generates timed script JSON from scraped data. |
| Intro/outro cards | **hyperframes** | HTML + GSAP motion graphics. Reuse from commercial pipeline. |
| Audio/video composite | **ffmpeg** | Standard. Already in pipeline. |
| Optional: anti-bot stealth | **playwright-stealth** | For when target sites block headless. |

**Zero runtime SaaS fees.** Only costs: LLM tokens for script generation (pennies per video), electricity/compute.

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT                                                           │
├─────────────────────────────────────────────────────────────────┤
│  business.json                                                   │
│    • name, phone, city, logo_url                                 │
│    • website_url                                                 │
│    • gbp_url (optional)                                          │
│    • seo_data (rank, keyword, competitors, metrics)              │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1 — Script Generator (LLM)                                │
├─────────────────────────────────────────────────────────────────┤
│  Prompt: "Generate SEO review video script from this data"       │
│  Output: timed_script.json                                       │
│    • beats[]: { start_s, end_s, action, voice_line, highlight }  │
│    • actions: open, scroll, click, navigate                      │
│    • highlights: {selector, type: box|circle|arrow|dim}          │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2 — TTS Generator                                         │
├─────────────────────────────────────────────────────────────────┤
│  Edge-TTS generates per-beat audio                               │
│  Output: audio/beat_001.mp3, beat_002.mp3, ...                   │
│  + master.mp3 (all stitched w/ silence gaps = total timing)      │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3 — Browser Recorder (Playwright)                         │
├─────────────────────────────────────────────────────────────────┤
│  Launch Chromium headed (bigger = cleaner video)                 │
│  Load target URL                                                 │
│  Inject cursor.js + highlight.js + timing-clock.js               │
│  For each beat:                                                  │
│    - Move cursor to position (animated)                          │
│    - Render highlight overlay                                    │
│    - Execute action (scroll/click/nav)                           │
│    - Hold for beat.duration                                      │
│  Stop recording → browser-recording.webm                         │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4 — Intro/Outro (hyperframes)                             │
├─────────────────────────────────────────────────────────────────┤
│  intro.html  — logo reveal + "Hey [Biz], here's your audit"      │
│  outro.html  — CTA card + phone + your branding                  │
│  Rendered via hyperframes → intro.mp4, outro.mp4                 │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5 — Final Composite (ffmpeg)                              │
├─────────────────────────────────────────────────────────────────┤
│  1. concat intro.mp4 + browser-recording.mp4 + outro.mp4         │
│  2. overlay master.mp3 audio track                               │
│  3. burn subtitles (optional, from script JSON)                  │
│  4. add persistent lower-third (biz name, your logo)             │
│  5. encode → final.mp4 (H.264, 1080p)                            │
└─────────────────────┬───────────────────────────────────────────┘
                      ↓
              ┌──────────────┐
              │ final.mp4    │
              │ → CDN upload │
              │ → landing pg │
              │ → GSA outreach│
              └──────────────┘
```

---

## 5. Key Technical Pieces

### 5.1 Custom Cursor Injection

Playwright headless has no rendered OS cursor. Inject our own:

```javascript
// cursor.js (injected via page.addInitScript)
(function() {
  const cursor = document.createElement('div');
  cursor.id = 'fake-cursor';
  cursor.style.cssText = `
    position: fixed;
    width: 24px;
    height: 24px;
    background: url(data:image/png;base64,...) no-repeat;
    pointer-events: none;
    z-index: 999999;
    transition: all 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
  `;
  document.body.appendChild(cursor);
  
  window.moveCursor = (x, y) => {
    cursor.style.left = x + 'px';
    cursor.style.top = y + 'px';
  };
  window.clickCursor = () => {
    cursor.classList.add('clicking');
    setTimeout(() => cursor.classList.remove('clicking'), 200);
  };
})();
```

Playwright drives via `page.evaluate('moveCursor(400, 200)')`.

### 5.2 Element Highlighting

```javascript
// highlight.js
window.highlightBox = (selector) => {
  const el = document.querySelector(selector);
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const box = document.createElement('div');
  box.className = 'fake-highlight';
  box.style.cssText = `
    position: fixed;
    left: ${rect.left - 8}px;
    top: ${rect.top - 8}px;
    width: ${rect.width + 16}px;
    height: ${rect.height + 16}px;
    border: 3px solid #FFD600;
    border-radius: 6px;
    pointer-events: none;
    z-index: 999998;
    animation: pulse 1.2s infinite;
  `;
  document.body.appendChild(box);
  setTimeout(() => box.remove(), 4000);
};
```

Variants for circle, arrow, dim-rest-of-page. All pure CSS/JS, no dependencies.

### 5.3 TTS — Edge-TTS (FREE, High Quality)

```python
import edge_tts
import asyncio

async def synthesize(text, voice="en-US-GuyNeural", rate="+0%", output="beat.mp3"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output)

# Cost: $0. Quality: indistinguishable from ElevenLabs for 90% of uses.
# Speed: ~1 second per sentence.
# Voices: 300+ including male/female, various accents.
```

**Recommended voices for this use case:**
- `en-US-GuyNeural` — professional male
- `en-US-JennyNeural` — professional female, warm
- `en-US-AriaNeural` — professional female, crisp
- `en-US-DavisNeural` — friendly male
- `en-GB-RyanNeural` — UK male (credibility boost for some industries)

**Alt: Kokoro TTS** — 82M-param local model, runs on CPU, MIT licensed. No network. Best for air-gapped / privacy-sensitive.

### 5.4 Timed Script JSON Schema

```json
{
  "video_id": "seo-audit-joes-plumbing-001",
  "target_url": "https://joesplumbing.com",
  "total_duration_s": 180,
  "voice_config": {
    "voice_id": "en-US-GuyNeural",
    "rate": "+0%",
    "pitch": "+0Hz"
  },
  "beats": [
    {
      "id": 1,
      "start_s": 0,
      "end_s": 6,
      "action": { "type": "load_url", "url": "https://joesplumbing.com" },
      "cursor": { "x": 640, "y": 360 },
      "highlight": null,
      "voice": "Hey Joe, it's [your name]. I pulled up your plumbing site to do a quick SEO review. Let me walk you through what I'm seeing."
    },
    {
      "id": 2,
      "start_s": 6,
      "end_s": 14,
      "action": { "type": "wait" },
      "cursor": { "x": 200, "y": 80 },
      "highlight": { "selector": "header .phone", "type": "box", "color": "#FFD600" },
      "voice": "Your phone number is in the header — that's good. But it's small. On mobile, Google and customers want this thumb-friendly."
    },
    {
      "id": 3,
      "start_s": 14,
      "end_s": 24,
      "action": { "type": "scroll", "to_selector": ".services" },
      "cursor": { "x": 500, "y": 600 },
      "highlight": { "selector": ".services h2", "type": "circle", "color": "#E53935" },
      "voice": "Your services section — I don't see any H1 or H2 tags with your city name. For local SEO this is costing you rank for 'plumber Denver'."
    },
    {
      "id": 4,
      "start_s": 24,
      "end_s": 34,
      "action": { "type": "navigate", "url": "https://www.google.com/maps/place/joes-plumbing" },
      "cursor": { "x": 640, "y": 400 },
      "highlight": { "selector": ".gbp-reviews-count", "type": "arrow" },
      "voice": "Switching to your Google Business Profile. You've got 12 reviews. Your top competitor Mike's Plumbing has 147. That's the single biggest gap between you and #1 rank."
    }
  ],
  "intro": {
    "business_name": "Joe's Plumbing",
    "logo_url": "https://.../joes-logo.png",
    "opener_text": "Free SEO Audit"
  },
  "outro": {
    "cta_text": "Want us to fix these? Call [your phone] or reply to this email.",
    "your_logo_url": "https://.../your-logo.png"
  }
}
```

### 5.5 Timing Sync Engine

The hardest part. Three clocks must align:
- Browser actions (scroll, navigate) execute at beat.start_s
- Cursor moves to beat.cursor_pos over ~400ms transition
- Highlights appear at beat.start_s + 500ms (slight delay = natural)
- Audio plays from master.mp3 aligned 1:1 with beats

Strategy:
1. Generate TTS audio ONCE per beat → know exact duration
2. Recalibrate beat.start_s / end_s from actual audio lengths (not LLM estimates)
3. Playwright recording runs a timer; at each beat.start_s, execute action
4. Browser clock = Playwright clock (sync via `page.waitForTimeout`)
5. Final ffmpeg overlay of audio = single-track, no per-beat sync needed (already baked in)

---

## 6. Browser-Use vs Playwright (Which to Use)

Two different projects:

| Project | What it does | Use here? |
|---------|-------------|-----------|
| **Playwright** (Microsoft) | Browser automation primitive | YES — this is the workhorse |
| **browser-use** (github.com/browser-use/browser-use) | LLM-driven natural-language browser control | NO for this — overkill. We have scripted beats, not "figure out how to book a flight" |
| **video-use** (github.com/browser-use/video-use) | Nate's video trimmer (on top of Playwright) | Partial reuse — its recording utilities, not its editing |

**Decision: pure Playwright.** browser-use adds LLM cost + latency we don't need. Our script is pre-generated; execution is deterministic.

---

## 7. Build Plan — Tokens + Time

| Component | Tokens | Notes |
|-----------|--------|-------|
| Playwright recorder module | 30k | Launch browser, record, save webm |
| cursor.js + injection handler | 20k | JS + Python wrapper |
| highlight.js (box/circle/arrow/dim) | 25k | 4 highlight types |
| Edge-TTS wrapper | 15k | Python async wrapper |
| Script generator (LLM prompt + caller) | 40k | Uses Haiku for cheap, Sonnet for quality |
| Timing sync engine | 40k | Recalibrates beats from TTS actual durations |
| hyperframes intro/outro integration | 25k | Template per video brand |
| ffmpeg composite pipeline | 30k | concat + audio + subs + lower-third |
| CLI + config + biz data loader | 25k | `loom.py --business X.json --template seo-audit` |
| Debug/iteration overhead (+50%) | 125k | Real build always needs fixes |
| **Total build** | **~375k tokens** | **~22 min Opus gen time** |

**Per-video runtime cost:**
- Script gen: ~2-5k tokens (Haiku) = ~$0.001
- TTS: FREE (Edge-TTS)
- Browser render: ~30-90 sec compute = ~$0.005 VPS
- ffmpeg: ~15 sec compute = ~$0.001
- **Total: ~$0.007 per video. Can charge $20-100/video. Margin: 99.9%+.**

---

## 8. Scaling Math

| Machine | Parallel browsers | Videos/day | Notes |
|---------|-------------------|------------|-------|
| 4 GB VPS (your current) | 2-3 | ~200-400 | Tight, workable |
| 8 GB VPS | 5-6 | ~700-1000 | Comfortable |
| 16 GB VPS | 10-12 | ~1500-2500 | Scale tier |
| 32 GB dedicated | 20-25 | ~3000-5000 | Enterprise tier |

**Time per video: ~30-90 sec real** (dominated by Playwright waits + page loads).

For 1000/day target: 8 GB VPS = $11-20/mo. Still pennies.

---

## 9. Quality Dials (v1 → v2 → v3)

### v1 (ship fast, crude but working)
- Generic script template w/ variable slots
- 3 fixed TTS voices (pick 1 per template)
- Box highlights only
- Single browser viewport
- Static intro/outro

### v2 (polish)
- LLM writes unique script per business (not template-fill)
- Voice variety (pick voice matching industry tone)
- All 4 highlight types (box/circle/arrow/dim)
- Smooth cursor animation w/ natural pause patterns
- Animated intro/outro via hyperframes
- Lower-third persistent overlay w/ biz name + your logo

### v3 (SaaS-grade)
- Voice cloning (your own voice via XTTS v2)
- Realistic mouse movement paths (not straight lines — add bezier curves, micro-pauses)
- Scroll/click timing that varies (not mechanical)
- Industry-specific script tone (warm for dentist, urgent for plumber emergency, formal for legal)
- A/B test engine: different script hooks per business, measure open rates
- Thumbnail generation (first frame branded)
- Captions burn-in w/ active-word highlighting (karaoke style)

---

## 10. Gotchas / Risks

| Risk | Mitigation |
|------|-----------|
| CAPTCHA / Cloudflare blocks headless browser | `playwright-stealth` pkg + residential proxy rotation |
| Target site slow / broken | 30-sec timeout → fallback to static screenshot + voice-over |
| TTS pronounces biz name weird | Phonetic override dict per-business if needed |
| Script sounds generic / AI-slop | Data-specific details mandatory (exact rank numbers, competitor names, unique page elements) |
| GBP scraping blocked by Google | Use Google Business Profile API (official) instead of scraping |
| Legal — false claims about their site | Disclaimer: "Automated review. Verify with human SEO before changes." |
| Ads platforms flag "deepfake personalization" | Clear labeling: "Personalized video by [You] for [Biz]". Not an impersonation. |
| Big render queue jams | Queue worker w/ retry + exponential backoff + dead-letter queue |

---

## 11. Integration w/ Existing Pipeline

This slots into your master video factory:

```
Scraper (existing) 
   ↓
business.json
   ↓
Router decides template family:
   ├── Commercial (Chaos Engine)       → hyperframes only
   ├── Data Shock (SEO pitch - motion) → hyperframes only
   └── Loom Audit (screen record)      → THIS SYSTEM
   ↓
Final MP4
   ↓
CDN upload
   ↓
Personalized landing page (video embed)
   ↓
GSA outreach → short link → landing page → conversion
```

**All three template families share:**
- Scraper input
- biz data schema
- CDN upload
- Landing page system
- GSA outreach system
- Mixpost posting layer

**Only difference = which rendering engine runs in the middle.** That's the architectural win.

---

## 12. Recommended Build Order

1. **Prototype** — Playwright records a page while cursor moves + highlight shows. No TTS yet. No LLM yet. Just prove the visual works. (~50k tokens, ~3 min gen)
2. **Add TTS** — Edge-TTS generates audio, ffmpeg overlays on the browser recording. Test voice quality. (~30k)
3. **Add LLM script generator** — Haiku writes a 5-beat script from fake biz data. Run end-to-end. (~40k)
4. **Smoke test w/ real business** — Pick ONE plumbing site, generate audit video. Review. Iterate. (~50k + real time)
5. **Add intro/outro via hyperframes** — Brand-matched opener + CTA. (~25k)
6. **Polish cursor animation + highlight variety** — box/circle/arrow/dim all working. (~30k)
7. **Wire into biz data pipeline + CDN + landing pages** — production flow. (~50k)
8. **Send 10 via GSA, measure conversion.** (~20k)
9. **v2 polish based on real data.** (~variable)

**MVP to first real send: ~195k tokens = ~12 min gen + iteration time.**

---

## 13. Business Model Implications

User nailed it casually but let me spell it out:

**This is a standalone SaaS.** Not just a feature of your outreach pipeline.

| Product Play | Target Customer | Price |
|--------------|----------------|-------|
| DFY video audits (sold direct) | Local biz owners | $99-$499/video |
| Agency reseller tool | Marketing agencies | $499-$1999/mo |
| White-label API | Other SaaS tools (CRM add-ons) | $0.50-$2/video API call |
| Free tier w/ watermark → upsell | Individual prospects | Free → $29/mo Pro |

**Adjacent competitors selling this manually:**
- **Tella** ($29/mo) — manual recording, personalization tokens
- **Sendspark** ($12/mo) — manual
- **Vidyard** ($19/mo) — manual
- **Loom** ($15/mo) — manual
- **Tavus** ($500/mo+) — AI avatar, not screen record

**No one is doing AUTOMATED screen-record w/ AI script.** Whitespace.

---

## 14. Decisions Locked (2026-04-23)

1. **Voice:** Interchangeable toggle — all 3 engines selectable at render time.
   - Edge-TTS (free, cloud, fast, high quality) = **default**
   - Kokoro TTS (free, local, MIT, slower but zero-cost-at-scale) = toggle option
   - XTTS voice clone (free, local, user's own voice) = toggle option, not default
   - Config: `voice_engine: edge | kokoro | xtts` in template.yaml
2. **First target industry:** Plumbers.
3. **Build priority:** Loom first (user will use it quickly on outreach), Chaos Engine next.
4. **Tool sandboxing:** Each pipeline process gets a whitelist of tools it's allowed to call. Shared tool pool, not free-roam. Pipelines declare their allowed_tools up front. (see §17)
5. **Slot variation everywhere:** Chaos Engine's 3-slot × N-option mechanic applies to EVERY template family — commercial AND loom. Each loom template ships w/ variation libraries so output varies across sends to same industry. (see §18)

---

## 15. Google Business Profile — Bot Detection Strategy

GBP aggressive on scraping bots. User raised valid concern. Answer:

### What's risky vs what's fine

| Action | Risk | Fix |
|--------|------|-----|
| Scraping GBP data at scale | HIGH — accounts/IPs blocked fast | Don't. Use existing scraper data. |
| Visiting public GBP listing page 1 time | LOW | Playwright-stealth plugin |
| Visiting 50+ GBP pages/hour from same IP | HIGH | Rate limit + residential proxy |
| Loading customer's own website | ZERO | Nothing special needed |
| Live Google SERP scraping | HIGH | Use pre-fetched DataForSEO data, render as overlay card |
| Logged-in Google actions | VERY HIGH | NEVER log in |

### Strategy baked into pipeline

- **Playwright-stealth plugin** (free npm `playwright-stealth`) — masks `navigator.webdriver`, fixes plugins array, humanizes fingerprint
- **Rate limit:** max 1 GBP page per 30 seconds per IP
- **User-agent + viewport rotation** per render
- **Human motion:** mouse moves in bezier curves, not straight lines (already in plan)
- **Typing:** 80-250ms per character random
- **No Google SERP scraping live** — use pre-fetched rank data from existing DataForSEO pipeline, render it as a hyperframes overlay chart **on top of** the GBP page
- **Residential proxy optional later** (~$50-100/mo) if scaling past ~50 loom videos/day hitting Google properties

### Rule

Every Google-property render must go through `gbp_safe_visit()` wrapper w/ stealth + rate limit + proxy (if configured). Never raw Playwright calls against Google domains.

---

## 16. Tool Sandboxing Rule (Cross-Cutting)

Every pipeline process (loom, commercial, memory daemon, scraper, render worker, etc) declares its **allowed_tools** in its config:

```yaml
# loom_pipeline.yaml
pipeline: loom_video
allowed_tools:
  - playwright
  - edge_tts
  - kokoro_tts
  - xtts
  - hyperframes
  - ffmpeg
  - claude_haiku_api
  - dataforseo_data_loader
denied_tools:
  - browser_use        # LLM-in-browser too expensive for this
  - veo3               # forbidden, kills margins
  - opus_api           # overkill for loom scripts
```

Runner refuses to call tools outside the whitelist. Prevents scope creep + accidental cost blowouts + contamination between pipelines.

---

## 17. Slot Variation in Loom Templates

Same mechanic as Chaos Engine — one base script → N variations. Applied to loom:

```yaml
# plumber-seo-audit.template.yaml
slots:
  opener:                              # 10 variations
    - "Hey [Owner], just pulled up [Business]..."
    - "Ran a quick audit on [Business]'s online presence..."
    - "[Business] — saw you come up for [keyword]..."
    - ... (10 total)
  problem_frame:                       # 15 variations per problem type
    missing_hours:
      - "Nobody can tell when you're open..."
      - "Your hours are blank — customers bouncing..."
      - ...
    no_photos:
      - "Zero photos — Google's penalizing you..."
      - ...
  solution_offer:                      # 8 variations
    - "30 min on our side fixes this..."
    - "Free video made by us, then $X/mo to actually do it..."
  closer:                              # 10 variations
    - "Reply if you want the full audit..."
    - ...
```

Result: same template, same business, **10 × 15 × 8 × 10 = 12,000 unique script variations**. Every outreach send gets a fresh spin. Algorithm can't flag as bulk template. Recipient can't compare w/ neighbor and see they got the same thing.

Same approach for Chaos Engine commercials (already specced).

Every template family MUST ship with slot variation libraries. Non-negotiable.

---

## 18. Next Steps

1. Pipeline install finishes (external drive path) → hyperframes + video-use live
2. Install Playwright + Edge-TTS + Kokoro + XTTS to same project dir
3. Ship SPEC-L1: Plumber SEO audit prototype (single business, hardcoded script) — proves the rig works
4. Ship SPEC-L2: Script generator (Haiku) + slot variation library
5. Ship SPEC-L3: Integration w/ existing scraper pipeline → end-to-end automated
6. Outreach test: 10 videos to real plumbers → measure reply rate

---

## 19. TL;DR

- **Feasible. 6/10 difficulty. 80% confidence.**
- **Zero SaaS costs.** Playwright + Edge-TTS + hyperframes + ffmpeg all free.
- **~375k tokens to build v1.** ~22 min Opus gen time + iteration.
- **~$0.007 per video runtime cost.** Massive margin.
- **Scales to 1000+/day on $20 VPS.**
- **Real SaaS potential** — no competitor doing fully auto screen-record audits.
- **Slots cleanly into existing pipeline** — shares scraper, CDN, landing pages, outreach.
- **GBP bot detection handled** — stealth plugin + rate limit + pre-fetched data, not live scraping.
- **Tool sandboxing** — each pipeline gets a whitelist, no free-roam.
- **Slot variation mandatory** — every template → 1000s of unique outputs.

Ready to prototype on green light.
