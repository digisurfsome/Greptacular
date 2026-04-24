# Video Studio Setup — Resume Plan

**Status:** Paused mid-setup. Disk full on C: (2.4 GB free). User going to bed, will use external drive in AM.

---

## What's Already Done

- [x] Prereqs verified: Python 3.13.5, Node 22.17.1, npm 10.9.2, git 2.50.0, ffmpeg (Gyan build)
- [x] AutoForge permissions added for ffmpeg / node / npm / npx / yt-dlp / where / mkdir / Test-Path / Get-Command (see `.autoforge/allowed_commands.yaml`)
- [x] Cheat sheet written: `docs/info/hyperframes-video-use-cheatsheet.md`
- [x] Attempted clone to `C:\Users\lober\VideoStudio` → failed (disk full). Partial `video-use` clone left behind.

---

## What's NOT Done (Blocker = Disk Space)

- [ ] External drive not plugged in or cleaned
- [ ] Hyperframes clone failed mid-way
- [ ] Video-use install (pip deps) never ran
- [ ] Hyperframes install (npm) never ran
- [ ] Whisper model not downloaded
- [ ] No `.env` file
- [ ] No test render yet

---

## User's Prep (before morning session)

1. Plug external drive into USB 3.0 port (blue). Erase/clean enough space — **target 40+ GB free**.
2. Note drive letter (e.g. E:, F:, H:).
3. Note free space after cleanup.

---

## Tomorrow's Plan — What the Agent Will Do

### Step 1 — Detect drive
```powershell
powershell -Command "Get-Volume | Select-Object DriveLetter, FileSystemLabel, DriveType, SizeRemaining, Size"
```
Confirm new drive + free space ≥ 40 GB.

### Step 2 — Clean up failed C: clone
Delete `C:\Users\lober\VideoStudio\` (contains broken partial).

### Step 3 — Create structure on external
Example using `E:`:
```
E:\VideoStudio\
  hyperframes\         (clone target)
  video-use\           (clone target)
  video-projects\      (user's raw files + renders live here)
    commercials\
    socials\
    templates\
  assets\              (logos, music, b-roll)
  .env                 (11labs or openai key later, optional)
```

### Step 4 — Clone both repos
```bash
cd "E:/VideoStudio"
git clone https://github.com/HeyGen-com/hyperframes.git
git clone https://github.com/browser-use/video-use.git
```

### Step 5 — Install hyperframes
```bash
cd "E:/VideoStudio/hyperframes"
npm install
```

### Step 6 — Install video-use
```bash
cd "E:/VideoStudio/video-use"
pip install -e .
```

### Step 7 — Wire as Claude Code skills
Copy skill definitions from each repo into `C:\Users\lober\.claude\skills\` so Claude (AutoForge OR Claude Desktop) can invoke them by name.

### Step 8 — Transcription config
Default: **local Whisper** (free, no key). Download model ~500 MB on first run.
Optional: OpenAI Whisper API or 11 Labs Scribe (needs API key in `.env`).

### Step 9 — Smoke test
- Drop a short (30 sec) test clip into `E:\VideoStudio\video-projects\test\raw.mp4`.
- Run trim pass via video-use.
- Confirm `edited.mp4` + word-timestamp JSON land in project folder.
- If pass → run a tiny hyperframes beat render. Confirm preview works.

### Step 10 — Preview/localhost
Hyperframes dev server runs on `http://localhost:3000` (or similar). Open in Chrome on same PC. External drive does NOT break localhost — server runs on C:/Windows, just reads/writes files on E:.

---

## User's Real Goal (Remember This)

- Automate commercials + social media videos for businesses
- Build **reusable templates per format** (commercial / testimonial / explainer / short)
- After 5 same-format videos → have Claude build `{format}-style.md` philosophy doc → new raw file auto-applies template

---

## Key Decisions Already Made

| Decision | Choice | Why |
|----------|--------|-----|
| Install location | External drive (letter TBD) | C: too full, external keeps local preview workflow |
| Transcription | Local Whisper default | Free, 11 Labs free tier too small for real work |
| Claude interface | AutoForge can continue to drive | User prefers it over Claude Desktop for now |
| Repo approach | Clone both + pull in skills | Matches Nate's tutorial |

---

## Reference Docs

- Cheat sheet: `docs/info/hyperframes-video-use-cheatsheet.md`
- Nate's tutorial (transcript source): user's original request
- Hyperframes repo: https://github.com/HeyGen-com/hyperframes
- Video-use repo: https://github.com/browser-use/video-use

---

## Red Flags Tomorrow Needs to Check

1. **USB speed** — if drive is USB 2.0, renders will be slow. Move to USB 3.0 port (blue).
2. **C: drive still tight** — 2.4 GB free on Windows drive = dangerous. Suggest user clean C: even after moving pipeline to external (Windows needs ~10 GB headroom for updates, pagefile, temp).
3. **Drive letter stability** — Windows may assign different letter next plug-in. If so, update paths or assign a permanent letter via Disk Management.
4. **Whisper model cache location** — by default caches to `C:\Users\lober\.cache\whisper`. Redirect to external to save C: space.

---

**Next session prompt to give the agent:**

> Read `docs/info/video-studio-setup-plan.md` and continue from Step 1. My external drive is plugged in now, letter is **[X:]** with **[N] GB free**. Proceed.

---

## Phase 2 — Commercial Template Factory (after pipeline works)

User's real goal = automated custom commercials per business. Pipeline feeds an existing scrape → outreach system (already scraping Google Biz + DataForSEO, sending 1000 custom emails/day + 1000 voice-bot audio samples/day + 200-300 websites/day).

### Architecture — 100% hyperframes + ffmpeg, ZERO per-video cost

**No Veo. No paid video gen APIs. Everything free.**

Every ad = motion-graphic commercial (think Apple, Stripe, Airbnb style — no live actors). hyperframes renders HTML+GSAP scenes as MP4. ffmpeg stitches beats. Data injected from scraped business JSON.

**One-time per template (free assets):**
- Generate character art (Fixer silhouette, AI Slop blob) via free Nano Banana / Gemini image gen → PNG/SVG layers in hyperframes
- Pull royalty-free stock clips from Pexels / Pixabay / Coverr for background b-roll
- Pull Lottie motion graphic packs for transitions
- Build library of 10-15 "destruction" scenes as GSAP animations (particle shatter, glitch, explode)

**Per business (mass, cheap, fast):**
- Inject business_name, logo_url, seo_rank, competitors from scraped JSON into hyperframes template variables
- Render each beat → MP4
- ffmpeg stitches [intro] + [problem] + [slot variation] + [destruction] + [CTA]
- Cost: pennies of electricity per video
- Time: 1-3 min per render (on render box)
- Scale: 300/day realistic

**Character consistency solved:** Fixer/AI Slop are STATIC image layers animated by GSAP. They look identical every render. No Veo drift problem because nothing is regenerated.

### Template Folder Structure

```
E:\VideoStudio\templates\
  hardware-hack-commercial\
    prd.md                   (description + slot logic)
    base-footage\            (Veo 3 one-time assets)
    destruction-library\     (10-15 clips, pick random)
    slot-variations\
      slot-1\                (15 options)
      slot-2\                (15 options)
      slot-3\                (15 options)
    hyperframes-overlays\    (data injection templates)
    render-config.json       (slot combo rules + ffmpeg chain)
  testimonial-template\
  explainer-template\
  roadrunner-short\
```

### Data Injection Pipeline

Input (per business, from existing scraper):
```json
{
  "business_name": "Joe's Plumbing",
  "business_city": "Denver",
  "seo_rank": 14,
  "competitors": ["ABC Plumbers", "XYZ Services"],
  "competitor_revenue": "$850k/yr",
  "business_phone": "555-1234",
  "business_logo_url": "..."
}
```

Output: 30-sec commercial with business data injected into overlays + slot-machine variations picked pseudo-randomly + destruction clip chosen. Filename `{business_slug}_commercial_v1.mp4`.

### Budget Reality

Pipeline runs on hyperframes + ffmpeg = **FREE per video**. Only cost = electricity + render box compute. No API fees. No Veo. No external paid video gen.

Asset sources (all free, commercial-use):
- Pexels / Pixabay / Coverr — stock video
- Lottie Files — motion graphics
- Nano Banana / Gemini 3 image gen — character art (one-time)
- GSAP (MIT license via hyperframes) — all animation logic

### Phase 2 First Milestones

1. Pick ONE template to build first (recommend: simple data-driven format)
2. Build hyperframes composition w/ data-injection slots
3. Wire ffmpeg stitch chain
4. Run ONE test with one business from scraper DB — time the render
5. Iterate until visually clean
6. Batch run — 10 businesses, review outputs
7. Scale to 50/day → 300/day

### Phase 3 — Distribution + Outreach Layer

User already has **GSA Website Contact Form blaster** working for cold outreach at 1000s/day. The video factory feeds into it as the payload.

**Outreach pipeline:**
```
Scraper (Google Biz + DataForSEO) → business JSON
        ↓
Render factory (hyperframes + ffmpeg) → custom MP4 per biz
        ↓
Upload MP4 → CDN (Cloudflare R2 or S3) → short URL per biz
        ↓
Generate personalized landing page per biz (slug-based URL)
        ├── Business name embedded
        ├── Video autoplay
        ├── Email capture for "4 more free videos"
        ├── Pricing CTA
        └── Analytics pixel (track visits, retarget)
        ↓
GSA form submit → message w/ landing page link (NOT raw MP4)
        ↓
Tracking: who visited, how long, did they click pricing
        ↓
Nurture: email sequence, retarget ads, upsell posting service
```

**Supplement channels (parallel rails, same landing page link):**
- Direct email from scraped biz emails
- Instagram DM drip (50-100/day/account)
- LinkedIn cold connect for B2B verticals
- SMS (opt-in only)

### Posting Layer = Mixpost Pro (self-hosted)

**Decision:** Using Mixpost Pro as the social posting backbone.

| Attribute | Value |
|-----------|-------|
| License | $299 ONE-TIME (Pro) |
| Host | Hetzner CX23 VPS (already owned) |
| Workspaces | Unlimited (1 per client business) |
| Accounts | Unlimited |
| Posts | Unlimited |
| Platforms | 11: FB Pages, IG (post/reel/story), X, LinkedIn (profiles + pages), YouTube (video + shorts), TikTok, Pinterest, Threads, Bluesky, GMB, Mastodon |
| API | Bearer token auth, full CRUD for accounts/media/posts/tags |
| Queue | Laravel Horizon built-in |
| Scheduling | Native |
| Approval workflow | Built-in |
| n8n node | Community-maintained |

**Per-client cost at scale (1000 clients): $0.30 LIFETIME.** Plus shared VPS cost.

**Upgrade path:** Mixpost Enterprise ($1199 one-time) adds billing/subscriptions/white-label for fully self-serve customer portals. Do this only after proving model w/ Pro + 50+ clients.

### Mixpost Deployment Plan (Phase 3 add-on)

**A. Deploy Mixpost (30 min, ~20k tokens to script):**
1. Buy Mixpost Pro license
2. SSH into Hetzner VPS
3. Install PHP 8.1+, MySQL 8, Redis, Nginx
4. Upload Mixpost → run installer wizard
5. Point subdomain → VPS IP
6. Let's Encrypt SSL
7. Laravel Horizon as systemd service
8. Admin login → generate API token

**B. Wire render worker to Mixpost (~25k tokens):**
```
mixpost_client.py:
  - get_or_create_workspace(business_name)
  - connect_account(ws_id, provider, oauth_payload)
  - upload_media(ws_id, video_path)   # chunked
  - create_post(ws_id, media_ids, caption, accounts, schedule_at)
  - approve_post(ws_id, post_id)
```

After MP4 render done → pipeline calls `create_post()` → Mixpost queues + pushes to each client's connected platforms.

**C. Platform developer app approvals (DAY 1 — don't wait):**
- Meta (FB/IG) app review — 1-3 weeks
- TikTok Content Posting API — 2-4 weeks
- YouTube Data API quota — 1-7 days
- LinkedIn Marketing API — 3-7 days
- Pinterest API — 1-3 days
- X (Twitter) API — 1-2 days
- Bluesky — instant (no approval)
- Threads — via FB/IG approval
- Mastodon — instant
- Google Business Profile — 1-2 weeks

Fire ALL applications simultaneously on day 1. Don't sequence them.

**D. Client onboarding (Option 1 = MVP):**
- Client buys plan → email them OAuth links for their accounts
- They authorize → workspace populated
- Machine auto-posts from then on

Upgrade to Option 2 (Enterprise self-serve) when manual onboarding becomes bottleneck (~50 clients).

**Conversion math (realistic, not optimistic):**

| Stage | Rate | Per 1000 GSA attempts |
|-------|------|----------------------|
| Form submit success | 10-20% (recaptcha/cloudflare) | 100-200 delivered |
| Form-to-landing click | 10-30% | 10-60 visits |
| Visit-to-paid (cold) | 1-5% | 0-3 sales/day early |

At $200 avg plan = ~$400/day new MRR at steady state = ~$12k MRR added per month. Scales as templates + landing page iterate.

**Split test metrics to track from day 1:**
- Template → conversion rate
- Hook (first 3 sec) variants
- Landing page variants
- Industry vertical conversion
- Price point ($79 vs $99 vs $149)

Rule: one change per test. Data in Airtable or Google Sheet.

### Phase 4 — Self-Serve E-Commerce

Eventually: public website where biz owners browse templates, order, pay via Stripe, video auto-delivers.

| Layer | Effort |
|-------|--------|
| Template gallery site | 2-3 days |
| Render queue worker (job = template_id + business_id) | 1-2 days |
| Stripe checkout + subscription billing | 1 day |
| Social posting API (Meta, TikTok, YouTube, X, LinkedIn OAuth) | 4-7 days |
| Customer dashboard | 2-3 days |
| Template production workflow (YOUR grind) | 1-2 days to design |

Total v1: ~3 weeks focused build after pipeline works.

### Core Constraint

Template production velocity. 100 templates = ~3/day for a month. Each needs concept + script + hyperframes comp + QA. **Building the template-making workflow is the actual unlock.** Everything else automates.

**Day 1 priority after install: make ONE template end-to-end w/ one business. Time it. That number calibrates the whole business model.**

---

## Token Budget for Full Stack (no human-week estimates — token math only)

Reminder: agent outputs ~500k tokens per 30 min of straight coding. Time = tokens / 500k × 30 min.

| Component | Tokens | Gen time | External wait |
|-----------|--------|----------|---------------|
| First hyperframes template | 40k | ~2.5 min | 0 |
| Each additional template | 20k | ~1.2 min | 0 |
| Dynamic landing page system | 120k | ~7 min | 30 min DNS/domain |
| Render queue worker | 60k | ~3.5 min | 0 |
| CDN upload (R2/S3) | 25k | ~1.5 min | 10 min CDN signup |
| GSA payload + short link | 30k | ~2 min | 0 |
| Stripe checkout + subs | 80k | ~5 min | 15 min Stripe setup |
| Customer dashboard | 150k | ~9 min | 0 |
| Social posting (5 platforms) | 250k | ~15 min | days-weeks API approvals |
| Analytics + pixel | 45k | ~3 min | 0 |
| Admin template manager | 75k | ~4.5 min | 0 |
| Debug/iteration overhead (+50%) | 450k | ~27 min | 0 |
| **TOTAL** | **~1.3M** | **~80 min** | **~1 hr user + weeks API approvals** |

### Money-making MVP (sequence)

1. Hyperframes template (40k)
2. CDN upload (25k)
3. Landing page (120k)
4. GSA payload (30k)
— **215k tokens = ~13 min gen + ~45 min user external setup = LIVE OUTREACH**

Social posting is NOT launch-critical. Manually post first batch while API approvals process. Don't gate revenue on Meta/TikTok approvals.

### Related Assets Already In Repo

User has extensive marketing strategy + creative direction captured in his Gemini conversations (see message history). Key assets mentioned:
- "Chaos Engine" — slot-machine ad variation concept
- "Style Set" app (`styleset.app` domain owned)
- "Normie Flows" brand
- "The Fixer" character concept
- "AI Slop" villain character
- "Hardware Hack" commercial series
- 8-step PRD Maker
- Overlay Tab browser extension concept

Don't try to build all of it in one session. **Finish the pipeline first, then Phase 2 starts with ONE template.**
