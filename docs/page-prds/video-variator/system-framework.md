# Video Variator — System Framework

> Analysis of the full pipeline: what exists, how it connects, what needs to be built.
> Read this before touching any code. The Hyperframes kit is the template library;
> the Distribution Engine PRD is the automation layer; the commercial templates doc
> is the content strategy. All three fit together here.

---

## The Big Picture

```
CONTENT SOURCES                    VIDEO ENGINE                    DISTRIBUTION
──────────────                     ────────────                    ────────────
YouTube URL        ─┐              Hyperframes                     Late API
App info form      ─┤─→ Script ──→ HTML + GSAP  ──→ MP4 ──→ ──→  13 platforms
Chaos Engine JSON  ─┘   (Haiku)    CLI render                      $41/mo flat
Protocol Runner ───┘
```

Three layers. Each layer is independent — swapping the content source doesn't change the video engine; swapping the video engine doesn't change distribution.

---

## Layer 1 — Content Sources

### What Already Exists (From the Brainstorm)
| Source | Status | What It Produces |
|--------|--------|-----------------|
| YouTube transcript → Haiku worksheet | Described in PRD | Headline, 5-8 steps, hook, affiliate link |
| Chaos Engine JSON | Fully designed (see `commercial-templates.md`) | Hardware Hack + mix-ups + destruction |
| App info form | Planned | Product brief → commercial template selection |
| Protocol Runner | Separate product | Fasting/protocol content |

### The Chaos Engine is Source #3
The commercial templates we designed are a content source, not a template type. The JSON schema at the end of `commercial-templates.md` is the structured brief that feeds into the video engine. Same pipeline, different input.

---

## Layer 2 — The Video Engine (Hyperframes)

### What Hyperframes Actually Is
Plain HTML files + GSAP timelines → MP4 via headless Chrome CLI. No React. No complex build. A composition is just an HTML file where every element has `data-start`, `data-duration`, `data-track-index` attributes. The CLI renders it through Chrome.

```bash
npx hyperframes lint      # validate before render
npx hyperframes render --quality standard --output renders/final.mp4
# ~1-3 minutes, visually lossless 1080p
```

### What the Student Kit Gives You (12 Projects)

| Project | Type | Format | AIS Coupling | Use As |
|---------|------|--------|--------------|--------|
| `may-shorts-19` | TikTok talking-head + motion graphics + karaoke | 9:16 vertical | Minimal | **Primary template — best polish** |
| `may-shorts-18` | Earlier version of same format | 9:16 vertical | Minimal | Reference for iteration comparison |
| `may-shorts-6` | Landscape talking-head | 16:9 | Minimal | YouTube/LinkedIn format base |
| `clickup-demo` | 60s SaaS product demo | 16:9 | Minimal | **App demo template** |
| `linear-promo-30s` | 30s product promo — 8 beats, cinematic | 16:9 | Minimal | **Commercial template base** |
| `hyperframes-sizzle` | Sizzle reel via website-to-hyperframes | 16:9 | Minimal | Style reference |
| `first-agent-promo` | 32s launch film — React/Babel approach | 16:9 | Minimal | Counter-example (don't use React pattern) |
| `aisoc-lesson-5-1` | Full lesson: face-cam + motion graphics | 16:9 | Heavy | Reference only — rebuild |
| `golden-ratio-demo` | Educational lesson, polished draft | 16:9 | Heavy | Reference only |
| `claude-edit-intro` | Promo intro, minimal brand hardcoding | 16:9 | Minimal | **Easiest starting template** |
| `aisoc-hype` | 30s brand hype film | 16:9 | Heavy | Reference only — rebuild from scratch |
| `aisoc-app-release` | 30s mobile app release promo | 16:9 | Heavy | Reference only |

### How Composition Structure Works
Each project = `index.html` (root) + `compositions/` folder (sub-comps loaded via `data-composition-src`).

The `linear-promo-30s` pattern (8 beats × 30 seconds) is the cleanest example of how to build a modular commercial:
```
Beat 01: Problem kinetic type (4s)
Beat 02: Object morph / logo reveal (4s)
Beat 03: Brand moment (2s)
Beat 04: Features flowchart (4.8s)
Beat 05: Product surfaces (4.7s)
Beat 06: Visual callback (2.5s)
Beat 07: Foundation moment (3s)
Beat 08: CTA outro (5s)
```

This beat structure maps directly to the Chaos Engine commercial format:
```
Beat 01: Hook / Base Scene opener
Beat 02: Hardware Hack applied (Variable A)
Beat 03: Absurd Rationale (Variable B + C format)
Beat 04: Escalation
Beat 05: Destruction (Variable D)
Beat 06: Product reveal flash
Beat 07: Product demo (Style Set fidget spinner moment)
Beat 08: CTA outro
```

### The Registry (38 Blocks + 3 Components)
Install via `npx hyperframes add <name>`. The key ones for our commercial templates:

| Block | Used In |
|-------|---------|
| `tiktok-follow` | All TikTok format videos |
| `instagram-follow` | All Instagram format videos |
| `yt-lower-third` | YouTube Shorts |
| `grain-overlay` | Every template (mood/texture) |
| `whip-pan` | Transitions between beats |
| `cinematic-zoom` | Style Set reveal, product moments |
| `flash-through-white` | Destruction ending transitions |
| `x-post` | Social proof templates |
| `shimmer-sweep` | Product reveal moments |

### The Brand Swap (One-Time Setup)
The kit ships with AIS branding baked in. To make it yours:
1. Replace values in `assets/brand-tokens.css` (CSS custom props — `--ais-bg`, `--ais-accent`, etc.)
2. Swap logo files in `assets/`
3. Run the grep sweep: `grep -rEn "(#37bdf8|#f09025|#07121c|#195066|aisoc|AIS Logo|@aiautomationsociety)" video-projects/`
4. Replace each hit with the matching CSS custom prop or your own value

Estimate: 2 hours one-time. After that, every generated video is auto-branded.

### Template Tokens (The Gap to Fill)
The student kit HTML files use **hardcoded content** — no `{{HOOK}}` or `{{POINT_1}}` tokens. The PRD describes slot-filling, but the kit doesn't do it natively. This is the build task: create a code layer that takes the script JSON (from Haiku or the Chaos Engine) and writes it into the HTML files at generation time. Options:
- String replacement at known positions
- Haiku generates the entire composition HTML (knows the structure, fills it in)
- A Node.js script that reads a template HTML + a script JSON and outputs a rendered HTML

---

## Layer 3 — Distribution (Late API)

### What Late Does
Single API call → posts to 13 platforms simultaneously. $41/month flat for 50 profiles.

```
Platforms: TikTok, Instagram, YouTube, Twitter/X, LinkedIn, Facebook,
           Threads, Reddit, Pinterest, Bluesky, Google Business, Telegram
```

### Platform Format Matrix
| Platform | Video Format | Caption | Hook Energy |
|----------|-------------|---------|-------------|
| TikTok | 9:16, 15-45s | Short, hashtags, emojis | Highest — pattern interrupt |
| Instagram Reels | 9:16, 15-45s | Mid, hashtags, save CTA | High — save-this |
| YouTube Shorts | 9:16, 45-60s | Searchable title | Medium — topic-first |
| LinkedIn | 16:9, 30-60s | Professional, no hashtag spam | Low — insight lead |
| Twitter/X | 16:9, 15-30s | Punchy, thread teaser | High — bold statement |
| Facebook | 16:9, 15-60s | Community, conversational | Medium |
| Threads | Either, casual | Conversational | Medium |
| Pinterest | 9:16, static card | Keyword-rich, evergreen | N/A |

### One Video → 7 Platform Variants
Same core render. Different captions (Haiku generates per platform). Different format if needed (9:16 vs 16:9 — different Hyperframes template). Late handles the actual posting.

---

## How the Commercial Templates Map Into This System

From `commercial-templates.md`, the 5 templates map to Hyperframes projects:

| Our Template | Base Hyperframes Project | Format | Registry Blocks |
|--------------|--------------------------|--------|-----------------|
| Template 1: Hardware Hack | `linear-promo-30s` (8-beat structure) | 9:16 or 16:9 | `grain-overlay`, `whip-pan`, `flash-through-white`, `tiktok-follow` |
| Template 2: The Graduation | `claude-edit-intro` (minimal brand, easy to modify) | 9:16 | `grain-overlay`, `whip-pan`, `tiktok-follow` |
| Template 3: Hero vs. AI Slop | New build — cinematic fight scene | 9:16 or 16:9 | `cinematic-zoom`, `shimmer-sweep`, `grain-overlay`, `flash-through-white` |
| Template 4: Support Group | `may-shorts-19` (multi-character, talking-head) | 9:16 | `tiktok-follow`, `grain-overlay`, `whip-pan` |
| Template 5: Open Loop Engine | Not a template — it's the automation layer | — | — |

The Chaos Engine JSON schema (at the end of `commercial-templates.md`) is what feeds the slot-filling layer. Haiku reads the JSON + the base template HTML and outputs a composition-ready HTML file.

---

## Motion Laws to Apply to Every Commercial Template

From `MOTION_PHILOSOPHY.md` — non-negotiable even for funny/chaos-style videos:

1. **~1.5s average scene length** — fast cuts. Destruction scene can hold longer for impact.
2. **Black/dark as foundation** — even the "mess" scenes should read dark/cinematic, not washed out
3. **Perpetual motion** — even still frames have drift, particle movement, or vignette breathing
4. **Motion blur on transitions** — whip-pan between beats, never hard cut
5. **Typography as protagonist** — the rationale text should be kinetic, not just subtitles
6. **Hero moments hold still** — the product reveal and CTA must hold 4-6 seconds after the chaos
7. **≤5 symbolic colors** — the Hardware Hack series: dark bg, accent for the "hack" object, brand color for product reveal, white text, destruction color (neon green/orange depending on hack)

Pre-flight before every render:
- Average scene ≤ 2s (excluding intro/outro)
- Every transition uses motion (streak, morph, slide)
- Vignette + grain on every scene
- Outro holds 4+ seconds

---

## The Automation Layer (What Needs to Be Built)

This is the glue between the three layers. In order:

### Phase 1 — Template Library (Hyperframes side)
1. Fork the student kit into this repo (or reference it as a submodule)
2. Run the brand swap (2 hours)
3. Pick the 3 minimal-coupling projects as starting templates
4. Build 2 new compositions: Hardware Hack base + Hero vs. Slop base
5. Each template: fully working `final.mp4` target before any automation

### Phase 2 — Slot Filling (The Code Layer)
A Node.js script or Convex action that:
- Takes: `{ template_id, script_json, brand_config, platform_targets }`
- Reads: the base template HTML
- Outputs: a ready-to-render HTML with script content injected
- Then runs: `npx hyperframes lint && npx hyperframes render`

The Haiku generation step (from the PRD) handles script JSON → HTML composition generation. The `/short-form-video` skill in the student kit encodes exactly how compositions are structured — Haiku already has this context.

### Phase 3 — Chaos Engine Randomization
A separate module that:
- Reads the variable pools from the commercial templates JSON schema
- Randomly (or intentionally) selects Variable A + B + C + D
- Outputs a script JSON in the same format as Phase 2 expects
- Optional: user can lock specific variables and randomize the rest

### Phase 4 — Distribution
- Rendered MP4 → Convex file storage
- Haiku generates platform-specific captions (7 variants)
- Late API posts to all connected platforms
- Scheduling queue for 3 posts/day cadence

---

## What Already Exists vs. What Needs Building

| Component | Status |
|-----------|--------|
| Hyperframes render engine (CLI) | Exists — npm install |
| 12 base template projects | Exists in student kit |
| Registry blocks (38+) | Exists — `npx hyperframes add` |
| Brand swap instructions | Exists — documented in README |
| Commercial template designs (5 templates) | Exists — `commercial-templates.md` |
| Component master list (all variables) | Exists — `commercial-templates.md` |
| Chaos Engine JSON schema | Exists — `commercial-templates.md` |
| Slot-filling code layer | **Build** |
| Haiku composition generation | **Build** |
| Chaos Engine randomizer | **Build** |
| Server-side render job (Convex action) | **Build** |
| TTS voiceover integration | **Build** (CLI exists: `npx hyperframes tts`) |
| Late API distribution | **Build** |
| Platform caption generator | **Build** |
| App Promo Engine input form | **Build** |
| User brand config storage | **Build** |

---

## The Flywheel Once Live

```
Chaos Engine selects 3 mix-ups
        ↓
Haiku generates script JSON
        ↓
Slot-filler injects into Hyperframes HTML
        ↓
TTS generates narration (on-device, no API cost)
        ↓
Hyperframes CLI renders MP4 (~2 min)
        ↓
User approves (or auto-approve on Pro)
        ↓
Late API → 7 platforms simultaneously
        ↓
3 posts/day, every day, without touching it
        ↓
Google sees traffic from website-intent audience
        ↓
Astro keywords start ranking
        ↓
Organic traffic feeds SaaS signups
        ↓
Revenue → paid ads → scale
```

---

*Framework v1.0 — synthesized from: Hyperframes student kit README + CLAUDE.md + MOTION_PHILOSOPHY.md, Distribution Engine PRD v2.0, commercial-templates.md*
