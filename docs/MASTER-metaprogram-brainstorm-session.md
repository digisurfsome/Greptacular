# MASTER: Metaprogram Brainstorm Session — Complete Record

**Created: 2026-03-15**
**Status: Preservation document**
**Purpose: Capture EVERYTHING from the brainstorm session — every idea, every system designed, every line of code built**

---

## Table of Contents

1. [Session Summary](#1-session-summary)
2. [The Big Picture](#2-the-big-picture)
3. [Metaprogram System](#3-metaprogram-system)
4. [What Was Built](#4-what-was-built)
5. [Architecture Decisions](#5-architecture-decisions)
6. [The Vision](#6-the-vision)
7. [Cross-Reference Index](#7-cross-reference-index)
8. [What's Next](#8-whats-next)

---

## 1. Session Summary

This session designed and partially built an interconnected ecosystem of products and systems centered around one core insight: **people respond differently to the same information depending on their unconscious communication patterns (metaprograms), and if you can detect those patterns and adapt your messaging, everything — products, marketing, coaching, automation — gets dramatically more effective.**

### What was designed:

- **NormieForge** — A consumer AI assistant ("AI operating system for regular people") that uses metaprogram detection to personalize every interaction from the first 60 seconds
- **Meta Engine** — A content creator's tool for ingesting training material, detecting audience metaprograms, and generating adapted copy across all channels
- **Timonacci Labs** — A universal knowledge hub that evolved from YT Lab into a knowledge ingestion/synthesis/distribution system with truth documents that sharpen with every source
- **Tool Chamber** — A modular execution layer ("revolver of tools") where AI decides which tool to use, tools execute deterministically, and successful paths get frozen as reusable skills
- **SkillForge** — A Karpathy-style auto-research loop that autonomously refines skills overnight using binary assertions

### What was built (actual code):

- Full MetaScraper package (social scraping, metaprogram detection, message rewriting, pipeline orchestration)
- Meta Engine backend (training ingestor, writing engine, output router, API endpoints)
- Meta Engine frontend (4-tab React page with dark theme)
- VibeHelper (screen-reading AI assistant with hotkey activation, setup wizard, brain file)
- Screen Agent (standalone screen-reading command runner)
- Deploy Agent (auto-pull-and-restart background watcher)

---

## 2. The Big Picture

### The Four Systems and How They Connect

```
                    ┌─────────────────────────────┐
                    │      TIMONACCI LABS          │
                    │   Universal Knowledge Hub    │
                    │                              │
                    │  Paste URL → Walk away →     │
                    │  Knowledge organized,        │
                    │  skills created, tools built │
                    └──────────┬──────────────────┘
                               │
                    Routes knowledge to:
                               │
        ┌──────────────────────┼──────────────────────────┐
        │                      │                           │
        v                      v                           v
┌───────────────┐   ┌──────────────────┐        ┌──────────────────┐
│  NORMIEFORGE  │   │   META ENGINE    │        │  TOOL CHAMBER    │
│   Consumer    │   │  Content Creator │        │   Execution      │
│   Product     │   │     Tool         │        │    Layer         │
│               │   │                  │        │                  │
│ Detects user  │   │ Ingests training │        │ Steps from YT    │
│ metaprograms  │   │ material, writes │        │ Lab → tools      │
│ → speaks      │   │ adapted copy for │        │ execute them     │
│ their         │   │ every audience   │        │ → skills freeze  │
│ language      │   │ segment          │        │ successful paths │
└───────┬───────┘   └────────┬─────────┘        └────────┬─────────┘
        │                    │                            │
        │                    │                            │
        └────────────────────┴────────────────────────────┘
                             │
                    All feed into:
                             │
                    ┌────────v─────────┐
                    │   SKILLFORGE     │
                    │  Overnight       │
                    │  Refinement      │
                    │                  │
                    │  Binary assert   │
                    │  → improve →     │
                    │  commit/revert   │
                    │  → repeat        │
                    └──────────────────┘
```

### The Product Funnel

```
┌─────────────────────────────────────────────────────┐
│  NORMIES — "Make my life easier"                     │
│  Market: 100M+ people                                │
│  Price: $9-19/mo                                     │
│  → NormieForge Core (life automation)                │
├─────────────────────────────────────────────────────┤
│  POWER NORMIES — "I want to customize this"          │
│  Market: 10M+ people                                 │
│  Price: $29-49/mo                                    │
│  → NormieForge Pro (custom automations + dashboards) │
├─────────────────────────────────────────────────────┤
│  VIBE CODERS — "I want to build my own tools"        │
│  Market: 1M+ people                                  │
│  Price: $49-99/mo                                    │
│  → AutoForge (full AI coding platform)               │
└─────────────────────────────────────────────────────┘
```

Each tier is an upsell, not a separate product. One account, one brain file, one agent that grows with you. The brain file is the moat — after 3 months, switching cost is enormous because the AI KNOWS the user.

---

## 3. Metaprogram System

### What Metaprograms Are

Metaprograms are unconscious cognitive patterns that determine how people process information, make decisions, and communicate. Everyone has them. Nobody knows what they're called. But everyone FEELS when something matches their pattern — it just "clicks."

The core insight: **Same information, different frame = completely different feeling.** An "away from" person hearing "you'll gain $200" feels nothing. That same person hearing "you'll stop losing $200" feels urgency. The facts are identical. The frame is everything.

### The Original 3 Core Metaprograms (NormieForge Consumer Detection)

These three are enough to create 8 distinct communication profiles. They're detectable from social scraping or 3 quick taps.

#### 1. Motivation Direction: Toward vs Away From

Are you motivated by moving TOWARD goals or AWAY FROM pain?

| Away From signals | Toward signals |
|---|---|
| "stop wasting money" | "build my savings" |
| "tired of being disorganized" | "get my life together" |
| "can't keep doing this" | "ready to level up" |
| "avoid late fees" | "stay ahead of bills" |
| "prevent / protect / avoid" | "achieve / create / build" |

**Away From user morning briefing:**
> "No fires today. Electric bill is covered. Nothing overdue. You dodged a $35 late fee — I paid it yesterday."

**Toward user morning briefing:**
> "Good morning! You're $200 ahead of your savings target. 8-day streak. Keep it going."

#### 2. Frame of Reference: Internal vs External

Do you trust your own judgment or look to others for validation?

| External signals | Internal signals |
|---|---|
| "what do you guys think?" | "I've decided to..." |
| "any recommendations?" | "I figured it out" |
| shares polls and surveys | shares opinions and takes |
| "is this normal?" | "this is what works for me" |
| "everyone says..." | "I believe..." |

**External user:**
> "87% of people with your spending pattern start with cutting subscriptions. The average savings is $89/mo. Want me to scan yours?"

**Internal user:**
> "Here's your spending breakdown. Three categories stand out. Take a look and tell me where you want to start."

#### 3. Work Style: Options vs Procedures

Do you want choices and flexibility, or step-by-step instructions?

| Procedures signals | Options signals |
|---|---|
| "just tell me what to do" | "what are my options?" |
| follows recipes exactly | improvises in the kitchen |
| "what's the right way?" | "what's the best way?" |
| uses words like "correct, proper" | uses words like "flexible, depends" |

**Procedures user:**
> "Here's your morning plan: 1. Bills — all covered this week. 2. Dinner tonight — Thai basil chicken (recipe below). 3. Tomorrow — Jake needs cleats for practice. I'll handle each one in order."

**Options user:**
> "A few things on your radar today: Dinner — I've got 3 ideas (Thai chicken, pasta, or leftovers). Jake needs cleats tomorrow — Amazon, Target, or that store on Main? Budget's flexible this week — splurge or save? Your call."

### The Expanded Set (Meta Engine / Writing Engine)

The writing engine and training ingestor expanded beyond the consumer-facing 3 to include 5 metaprogram axes, each with a 4-level dominance spectrum:

| # | Metaprogram | Pole A | Pole B | Priority |
|---|---|---|---|---|
| 1 | Motivation | Toward | Away From | Highest — detect first |
| 2 | Reference | Internal | External | High |
| 3 | Work Style | Options | Procedures | High |
| 4 | Chunk Size | Big Picture | Detail | Bonus |
| 5 | Action | Proactive | Reactive | Bonus |

### The 4-Level Dominance Spectrum

People are rarely 100% one pole. Most are dominant one way with a secondary lean. This matters enormously for messaging — the ORDER of lead/follow changes everything.

| Level | Description | Messaging Rule |
|---|---|---|
| 1 | PURE pole_a (85%+ ratio) | Talk ONLY in pole_a frame. No mixing. |
| 2 | DOMINANT pole_a (60-85%) | LEAD with pole_a, FOLLOW with pole_b |
| 3 | DOMINANT pole_b (60-85%) | LEAD with pole_b, FOLLOW with pole_a |
| 4 | PURE pole_b (85%+ ratio) | Talk ONLY in pole_b frame. No mixing. |

**Level 2 example (dominant toward, secondary away):**
> "Here's what you'll gain [toward lead] — and you'll never deal with X again [away follow]"

**Level 3 example (dominant away, secondary toward):**
> "Stop dealing with X [away lead] — and start building Y [toward follow]"

Same words. Different sequence. Completely different feeling.

### The 8 Communication Profiles (Core 3 Metaprograms)

| # | Toward/Away | Internal/External | Options/Procedures | Voice |
|---|---|---|---|---|
| 1 | Toward | Internal | Options | Empowering, choices, "your call" |
| 2 | Toward | Internal | Procedures | Structured wins, "here's the plan" |
| 3 | Toward | External | Options | Social proof + choices |
| 4 | Toward | External | Procedures | "Here's what winners do, step by step" |
| 5 | Away From | Internal | Options | Risk data + "you decide" |
| 6 | Away From | Internal | Procedures | "Here's how to stay safe, step by step" |
| 7 | Away From | External | Options | "Most people avoid this by..." + choices |
| 8 | Away From | External | Procedures | "Experts say do these 3 things to avoid..." |

With the expanded 5 metaprograms, this becomes 32 profiles (2^5). The writing engine can generate copy for all combinations.

### Detection Methods

#### Method 1: Social Scraping (Best — 0 questions needed)

Scan last 20 tweets / captions / posts. Usually get all 3 core metaprograms from language patterns alone. User never knows it happened.

The MetaScraper package implements this with parallel async scrapers for:
- Twitter/X (bio + recent tweets)
- LinkedIn (headline + about + posts)
- Facebook (bio + public posts + groups)
- Instagram (bio + captions + hashtags)
- Google results (personal websites, forum posts)
- Reddit (comments are gold — people are unfiltered)

All scrapers run in parallel with a 3-second timeout. Whatever we get by then, we use. Speed over completeness. Even 1-2 sources with decent text is enough.

#### Method 2: 3-Tap Quiz (Good — feels like a fun personality quiz)

If no social data available, ask 3 natural questions:

**Q1 (Toward/Away):** "When you imagine next month going perfectly, is it more like..."
- "Everything I want is falling into place" → Toward
- "Nothing is stressing me out anymore" → Away From

**Q2 (Internal/External):** "When you're about to try something new, you usually..."
- "Just go for it and figure it out" → Internal
- "Check what other people say first" → External

**Q3 (Options/Procedures):** "When someone's helping you with something, you'd rather they..."
- "Give me options and let me pick" → Options
- "Just tell me exactly what to do" → Procedures

Key design principle: both options are equally socially desirable. No "right" answer. Questions about THEIR life, not about buying. Past tense preferred (harder to fake than hypotheticals).

#### Method 3: First Message Analysis (Fallback)

Analyze whatever they typed in the hero input:
- "I want to stop wasting money" → Away From + (need more data)
- "I'm always broke by the 20th" → Away From + External (comparing to norm)

Even 1 metaprogram detected is better than 0. Default the others to the statistical middle and refine over the first few interactions.

#### Method 4: Text Pattern Detection (Implemented in MetaScraper)

The `patterns.py` file contains weighted keyword/phrase clusters for all 5 metaprogram axes, organized by signal strength (strong/medium/weak). The detection engine in `detector.py`:
- Scores text against both poles of each axis
- Uses diminishing returns on repeat hits (log scale)
- Runs in under 100ms (pure pattern matching, no API call)
- Returns confidence levels and dominance ratios
- Generates messaging instructions per axis

### How Metaprograms Apply to WRITING (The Content Creator Angle)

This is the Meta Engine use case — not detecting end users, but profiling entire audiences for copywriting.

**The flow:**
1. Upload training material (NLP videos, sales transcripts, communication courses)
2. AI extracts metaprogram training data (real examples, detection questions, language patterns)
3. Training library accumulates across all sources
4. When writing copy: select target profile + topic + channel
5. Writing engine generates copy calibrated to that profile using the training library as a "manual"

**Three writing modes:**
- **GENERATE** — fresh copy for a profile + topic + channel
- **REWRITE** — take existing copy and adapt it to a specific profile (same info, different frame)
- **COACH** — real-time coaching prompts for a live conversation (SAY / WHY / LEAD-FOLLOW / DON'T)

**Batch generation:** Generate copy for EVERY metaprogram combination at once. With 3 metaprograms = 8 variants. With 2 metaprograms = 4 variants. Complete copy library for a topic, ready to deploy.

**The compound effect:** First upload = decent copy. 10 uploads = scary good. 50 uploads = Tony Robbins level.

### Refinement Over Time

The initial detection is the STARTING POINT. Every interaction refines:
- They ignore the social proof line → probably more Internal than we thought
- They always pick "just do it" over choices → shift toward Procedures
- They respond more to "you're saving $X" than "you avoided $X" → shift Toward

The brain file tracks these shifts. By week 2, the profile is dialed.

---

## 4. What Was Built

### Backend Services

#### `server/services/meta_training_ingestor.py`
**What it does:** Master ingest pipeline. Upload ANYTHING — YouTube URL, audio file, video file, text transcript — and it:
1. TRANSCRIBES it (YouTube API for URLs, Whisper for audio/video)
2. EXTRACTS metaprogram training data (examples, patterns, questions, how types talk)
3. ORGANIZES into structured training material the detection engine can learn from
4. Feeds the WRITING ENGINE so it generates adapted copy per profile combo

**Key classes:**
- `TranscriptResult` — output of the transcription step
- `TrainingExtraction` — structured training data (examples, questions, patterns, type descriptions, coaching scenarios, raw insights)
- `TrainingLibrary` — accumulated training material from all sources; the "brain" that the writing engine reads

**Storage:** `~/.autoforge/meta_training/` with subdirs for transcripts, extractions, and the master `training_library.json`

**Source types handled:**
- YouTube URLs (via `youtube-transcript-api`, free, no API key)
- Audio files (.mp3, .wav, .m4a, .ogg, .flac) via Whisper
- Video files (.mp4, .mov, .webm, .mkv) via ffmpeg audio extraction + Whisper
- Text files (.txt, .md, .srt, .vtt)
- Raw pasted text

**AI extraction:** Uses Claude Sonnet with a detailed system prompt that knows all 5 metaprograms and the 4-level dominance spectrum. Extracts 6 categories of training data from every transcript.

#### `server/services/meta_writing_engine.py`
**What it does:** Takes a detected metaprogram profile + the training library and generates adapted copy for any channel, topic, and scenario.

**Three modes:**
- `generate_copy()` — fresh copy with training context injected
- Rewrite mode — same info, different frame
- Coach mode — real-time earpiece coaching (SAY / WHY / LEAD-FOLLOW / DON'T)

**Key functions:**
- `_build_training_context()` — selects relevant examples, patterns, type descriptions, and coaching scenarios from the library for the target profile
- `_build_dominance_instructions()` — converts profile into lead/follow messaging rules
- `generate_all_combos()` — batch generation for every metaprogram combination

**Channels supported:** general, instagram, email, landing_page, shorts, x, dm, ad

#### `server/services/meta_output_router.py`
**What it does:** The last mile. Routes generated copy to organized file storage with full metadata tags so any downstream system knows exactly WHO it's for, WHAT it is, WHERE it goes, and HOW to deploy it.

**Key classes:**
- `CopyTag` — universal metadata tag (topic, channel, profile, dominance levels, sequence position, variant ID)
- `TaggedCopy` — content + tags + file path
- `OutputManifest` — master index per topic
- `OutputRouter` — routes to files, manifests, webhooks, exports

**File organization:**
```
meta_output/
├── by_topic/{topic_slug}/
│   ├── manifest.json
│   ├── by_channel/{channel}/{profile_code}.md
│   ├── by_profile/{profile_code}/{channel}.md
│   ├── sequences/
│   └── exports/ (CSV, JSON, HTML)
├── by_channel/ (cross-topic index)
└── webhooks/delivery_log.json
```

**Export formats:** CSV (spreadsheet/CRM ready), JSON (API ready), HTML (browseable preview page)

**Query API:** `find_copy(channel="email", profile_code="toward_external")` — downstream systems query by tags.

### API Router

#### `server/routers/meta_training.py`
Full REST API with these endpoint groups:

**Ingest endpoints:**
- `POST /api/meta-training/ingest/url` — YouTube URL
- `POST /api/meta-training/ingest/upload` — file upload (100MB max audio/video, 10MB text)
- `POST /api/meta-training/ingest/text` — paste raw text

**Training library endpoints:**
- `GET /api/meta-training/library` — stats
- `GET /api/meta-training/library/examples` — filterable by metaprogram/pole
- `GET /api/meta-training/library/patterns` — filterable
- `GET /api/meta-training/library/coaching` — coaching scenarios
- `GET /api/meta-training/library/insights` — raw insights
- `DELETE /api/meta-training/library` — clear all

**Writing engine endpoints:**
- `POST /api/meta-training/write/generate` — fresh copy for a profile
- `POST /api/meta-training/write/rewrite` — rewrite existing copy
- `POST /api/meta-training/write/coach` — real-time coaching prompt
- `POST /api/meta-training/write/all-combos` — batch generate all combinations

**Output/routing endpoints:**
- `POST /api/meta-training/route` — route copy with tags
- `POST /api/meta-training/route/sequence` — route entire decision tree
- `GET /api/meta-training/output/topics` — list topics with output
- `GET /api/meta-training/output/{slug}` — full manifest
- `GET /api/meta-training/output/{slug}/export/{csv|json|html}` — exports
- `GET /api/meta-training/output/find` — query by tags
- `DELETE /api/meta-training/output/{slug}` — delete topic output

### Frontend

#### `ui/src/pages/MetaEnginePage.tsx`
Dark-themed React page (bg-[#0a0a0a], orange/cyan/green accents — matches CLI Scripter aesthetic).

**Four tabs:**
1. **Upload / Ingest** — YouTube URL input, drag-and-drop file upload zone, text paste area. Results panel shows success/error for each ingest.
2. **Training Library** — Stats row (sources, examples, patterns, scenarios), filterable by metaprogram, sub-views for examples/patterns/coaching. Refresh button loads from API.
3. **Writing Engine** — Audience profile selector (motivation, reference, work style), content setup (topic, channel, tone), Generate + Generate All Combos buttons, output preview with copy-to-clipboard.
4. **Output / Export** — Browse generated topics, expand to see individual variants, CSV/JSON export buttons per topic.

### MetaScraper Package

#### `metascraper/detector.py`
Pure pattern matching metaprogram detector. Speed target: <100ms.

**Key classes:**
- `MetaprogramScore` — score for a single axis with confidence, dominance level (1-4), lead/follow pair, and plain-English messaging instructions
- `MetaprogramProfile` — complete profile with primary/confident profiles, profile code (e.g., "T-E-P"), and detection quality rating

**Functions:**
- `detect_metaprograms(text, programs=None)` — full detection on any text corpus
- `detect_from_short_text(text)` — optimized for bios/one-liners (core 3 only)

#### `metascraper/patterns.py`
Language pattern database. 5 metaprogram axes, each with weighted keyword/phrase clusters organized by signal strength (strong=3x, medium=2x, weak=1x).

Contains 200+ phrases across all poles. Examples:
- Toward strong: "i want to", "excited about", "level up", "crushing it", "momentum"
- Away From strong: "tired of", "sick of", "avoid", "never again", "fix this"
- Internal strong: "i decided", "i trust my gut", "my philosophy"
- External strong: "what do you guys think", "studies show", "highly rated"

All patterns registered in the `METAPROGRAMS` dict with priority ordering.

#### `metascraper/rewriter.py`
Two rewriting systems:

1. **AI-powered rewriter** — sends copy + detected profile to Claude Haiku for intelligent rewriting. Handles single messages and batch rewrites. ~$0.001 per rewrite.

2. **Instant template rewriter** — pre-written template variants for common messages (welcome, CTA, savings notification). Zero latency, zero cost. Falls back when no exact match found.

Also contains the fallback quiz questions with enticing, personality-quiz-style framing.

#### `metascraper/scraper.py`
Parallel async social scraper. 6 platform scrapers running concurrently with 3-second timeout.

**Identity signal extraction:** Handles Facebook OAuth, Google OAuth, and email-based name extraction.

**Platform scrapers:** Twitter, LinkedIn, Facebook, Instagram, Google results, Reddit. Currently scaffolded with production hooks noted (real API calls would go in `# PRODUCTION CODE` sections).

**Key class:** `ScrapedCorpus` — combines all scraped content into a single text corpus for analysis.

#### `metascraper/pipeline.py`
Complete pipeline from identity signal to personalized copy.

**Main pipeline:** `run_pipeline()` — handles any entry point (OAuth, email, hero input), runs scraping + detection, returns profile + needed questions.

**Cold outreach pipeline:** `profile_for_outreach()` — profile someone from email/name/handles for cold email personalization. `personalize_cold_email()` — full pipeline from scrape to rewritten email.

### VibeHelper Package

#### `vibehelper/agent.py`
Screen-reading AI assistant. Captures screenshots, sends to Claude Sonnet with vision, receives JSON action plans, executes commands, loops until the task is done.

**Features:**
- `HelpWindow` — floating tkinter window showing real-time progress
- Screenshot capture with auto-resize (1280px max width for token efficiency)
- Command execution with timeout (300s default)
- Brain file integration — loads `~/.vibehelper/my_brain.md` as context
- Learning — saves new solutions to brain file automatically
- Multi-step agent loop with up to 15 rounds
- Error recovery: takes fresh screenshot when commands fail to diagnose visual issues (Vim dialogs, error popups)

#### `vibehelper/cli.py`
Entry point with global hotkey listener (using `pynput`).

**Hotkeys:**
- `Ctrl+Shift+X` — read screen and help
- `Ctrl+Shift+S` — stop current task
- `Ctrl+Shift+Q` — quit

**CLI flags:** `--setup` (wizard), `--brain` (open brain file), `--version`

#### `vibehelper/setup_wizard.py`
First-run experience. Auto-detects:
- OS and shell
- Installed dev tools (git, node, npm, python, pip, claude, code)
- Project directories (searches common locations for git repos)

Personalizes the brain file with detected environment info. Handles API key setup.

### Standalone Agents

#### `screen_agent.py`
Earlier version of the screen agent concept, before it became VibeHelper. Same core idea — Ctrl+Shift+X reads screen, runs commands, loops until done — but simpler (no setup wizard, no brain file migration).

Lives at project root. Uses `~/.autoforge/my_brain.md` and `my_brain_default.md` as the default template.

#### `deploy_agent.py`
Background deployment watcher. Polls remote every 30 seconds, auto-pulls new commits on main, kills existing servers, restarts `start_ui.bat`.

Hardcoded to the owner's Windows paths (`C:\Users\lober\Greptacular`). Includes retry logic on git fetch failures (exponential backoff, 3 attempts).

### Brain Files

#### `my_brain_default.md`
Default template for the Screen Agent's personal knowledge file. Contains:
- User identity placeholders
- Machine setup info (AutoForge paths, deploy chain)
- Common problems and solutions (Vim during git, path issues, npm failures, port conflicts)
- User preferences
- Tool list
- Empty "Learned Solutions" section that the agent auto-populates

---

## 5. Architecture Decisions

### Why Pattern Matching for Detection (Not AI)

The metaprogram detector uses pure pattern matching with weighted keyword clusters — no API calls. This is deliberate:
- **Free:** Zero cost per detection
- **Fast:** Under 100ms, even for large text corpora
- **Predictable:** Same input always gives same output
- **Scalable:** Can run client-side, no server dependency

AI is used for the HARDER parts: extracting training data from transcripts, generating adapted copy, coaching. Detection itself doesn't need AI — it needs speed and consistency.

### Why Claude Sonnet for Extraction, Not Opus

The training extraction and copy generation use Claude Sonnet (not Opus). Rationale:
- Cost efficiency — extraction happens on every upload, potentially many times per day
- Sonnet's quality is sufficient for structured extraction tasks
- The SYSTEM PROMPT does the heavy lifting with detailed metaprogram knowledge
- Opus is reserved for complex reasoning tasks, not structured data extraction

### Why Haiku for Rewriting

The message rewriter uses Claude Haiku. Rationale:
- Rewrites are called frequently (potentially per message in real-time)
- Cost: ~$0.001 per rewrite
- Speed: faster response for real-time use
- The rewriting task is constrained enough (same info, different frame) that Haiku handles it well

### Why a Training Library Instead of Templates

The writing engine is NOT template-based. Instead, it builds a training context from accumulated real examples:
- Templates are rigid — they can't handle edge cases or nuance
- The training library approach IMPROVES with more data — the AI gets better examples to work from
- Same topic + different training data = different (and better) copy
- This creates a genuine competitive moat — the library is the product

### Why the Output Router is Infrastructure, Not a Feature

The output router was built as a tagging/routing infrastructure layer, not a user-facing feature. Every piece of generated copy carries full metadata tags. This enables:
- Any downstream system can query by tags (email tool, social scheduler, CRM, ad manager)
- Export to any format (CSV, JSON, HTML)
- Webhook delivery to external systems
- The same copy can be found by channel, by profile, by topic, or by sequence position
- Future integrations don't require rebuilding — they just query tags

### Why the 4-Level Dominance Spectrum

Most systems treat metaprograms as binary (toward OR away). The 4-level spectrum is more accurate and more useful:
- People are rarely 100% one pole — most live at levels 2 and 3
- The LEAD/FOLLOW order (which pole to mention first) is what makes messaging click
- Level 1 and 4 (pure) are rare but powerful — when you spot them, you know exactly how to talk
- The dominance ratio gives a continuous score, not a binary label

### Why Social Scraping Before Questions

Detection priority: scraping first, quiz second, first-message analysis third. Reasoning:
- Scraping is invisible — the user never knows it happened
- It's faster than questions (3 seconds vs 60 seconds of user interaction)
- It captures unconscious patterns (how they ACTUALLY talk) vs conscious self-reporting
- The quiz is only for gaps — we only ask what we can't detect
- This minimizes onboarding friction while maximizing personalization

### Why Parallel Async Scrapers with Timeout

All 6 platform scrapers run concurrently with a 3-second timeout. Reasoning:
- We don't need ALL sources — even 1-2 with decent text is enough
- Speed matters more than completeness for first-impression personalization
- Timeout ensures we never block the user waiting for a slow scrape
- Results from slow scrapers can backfill the profile asynchronously later

---

## 6. The Vision

### The Full Compound Flywheel

```
INGEST CONTENT
    → Transcribe (YouTube, audio, video, text)
    → Extract metaprogram training data
    → Add to training library (accumulates)
         ↓
BUILD TRAINING LIBRARY
    → Real examples of how each type talks
    → Detection questions (what to ask)
    → Language patterns (what to look for)
    → Coaching scenarios (what to say when)
         ↓
GENERATE ADAPTED COPY
    → For any profile + topic + channel
    → Batch: all 8+ combinations at once
    → Three modes: generate, rewrite, coach
         ↓
ROUTE OUTPUTS
    → Tagged with full metadata
    → Organized by topic/channel/profile
    → Exported to CSV/JSON/HTML
    → Webhooks to external systems
         ↓
FEEDS BACK INTO:
    → Better training data → better copy
    → More sources → sharper truth documents
    → More examples → more accurate detection
```

### Truth Documents That Sharpen With Each Source

This is Timonacci Labs' core innovation:

- **Day 1:** Upload video #1 about AI SEO → New truth doc created (v1)
- **Day 3:** Upload video #2 → +12% new insights (v2)
- **Day 7:** Upload article → +8% new (v3)
- **Day 10:** Upload video #3 → Nothing new. Absorbed. Time saved.
- **Day 14:** Upload video #4 → +5% new (v4)
- **Day 28:** Upload PDF → +3% new (v5)
- **Result:** Truth doc v5 covers 99% of everything known about AI SEO. Synthesized from 7 sources. Sharper than any single one.

The matching system uses two layers:
1. **[ROBOT] Keyword/tag matching** — fast, free, handles 70% of cases
2. **[AGENT] Semantic similarity via Claude Haiku** — catches cases where different words describe the same concept

### Skill-Sleeved Determinism (The "Something New Nobody Has Thought Of")

This is the creative synthesis from the Tool Chamber research:

> What if the WALLS themselves are AI-generated, and then FROZEN into deterministic structure?

**The idea: Skills as Frozen Hallways**

1. First time a step type is encountered: AI figures out how to do it (expensive, creative, might fail)
2. The successful execution path is CAPTURED as a skill — a deterministic sequence of tool calls
3. Next time that step type appears: the SKILL runs, not the AI
4. The AI only activates when the skill fails (fallback) or when there's no skill yet

```
First time (no skill exists):
  [AGENT] → Decides: use Computer Use → navigates YouTube Studio → uploads → succeeds
  [CAPTURE] → Records the exact sequence as a skill
  [FREEZE] → Skill saved as "youtube_upload_v1"

Second time:
  [ROBOT] → Runs "youtube_upload_v1" skill → deterministic, fast, no AI tokens
  [FALLBACK] → If skill fails (YouTube redesigned?), fall back to [AGENT]
  [LEARN] → If agent succeeds with new approach, update skill to v2
```

**The compound effect:**
```
Week 1:  AI runs 100% of steps   → Expensive, slow, sometimes fails
Week 2:  AI runs 60% of steps    → 40% are now frozen skills
Week 4:  AI runs 20% of steps    → 80% are frozen skills
Week 8:  AI runs 5% of steps     → 95% are frozen skills, near-zero cost
```

The system literally learns its own deterministic structure over time. It's not AI OR deterministic. It's AI CREATING determinism, then RUNNING within it.

### Karpathy Loop for Overnight Skill Refinement

Based on Andrej Karpathy's auto-research pattern (and its application to Claude skills):

**The 3-file pattern:**
1. `skill.md` — the skill instructions to improve
2. `eval.json` — binary assertions (true/false) across test prompts
3. The loop prompt — "Keep going until perfect score or I stop you"

**The loop:**
```
READ skill.md
→ MAKE ONE CHANGE to skill instructions
→ RUN 5 test prompts through the skill
→ CHECK 25 binary assertions (true/false)
→ CALCULATE pass rate (e.g., 23/25 = 92%)
→ Score improved? → git commit, keep change
→ Score dropped?  → git reset, try different change
→ REPEAT until perfect score or human interrupts
```

**Key insight: Binary assertions are everything.**
- "First line is a standalone sentence" → true/false (automatable)
- "Contains at least one statistic" → true/false (automatable)
- "Does it have a compelling subject line?" → subjective (NOT automatable)

Structural quality (70-80% of what makes a skill reliable) can be fully automated. Creative quality still needs human review.

**The compound effect is THREE layers deep:**
1. **Tool Chamber** spins to the right tool for each step type
2. **Skill Capture** freezes successful execution paths into deterministic skills
3. **Karpathy Loop** autonomously refines those skills overnight using binary assertions

```
Week 1:  AI runs steps raw          → Expensive, unreliable
Week 2:  Skills captured from v1    → Cheaper, somewhat reliable
Week 4:  Skills refined to v3-v5    → Near-free, highly reliable
Week 8:  Skills at v10+             → Near-perfect structural quality
```

### The Overnight Factory (Full Vision)

```
Queue 10 YouTube videos → extract steps → build tools
    ↓
Tool Analyzer checks readiness → gaps found → PRD Shredder builds missing components
    ↓
Tool Chamber executes step chains → skills captured from successes
    ↓
OVERNIGHT: Karpathy loop runs on ALL captured skills
    - Each skill runs 5 test prompts x 25 assertions = 125 binary checks
    - Failed assertions → skill.md modified → retest → keep or revert
    - Loops until perfect or morning
    ↓
MORNING: 10 tools built + skills refined to v3-v5 + component library expanded
```

### The Self-Improving System (Applied to Everything)

Timonacci Labs applies the Karpathy loop pattern to every layer:

| Layer | What It Measures | How It Improves |
|---|---|---|
| Truth Doc Quality | Can it answer test queries about the topic? | Flags gaps, suggests missing content |
| Diverter Accuracy | Did routed outputs actually get used/succeed? | Stops suggesting unused output types |
| Matching Accuracy | Did content match the right topic? | Adjusts tags and thresholds from corrections |
| Skill Quality | Binary assertions on skill output | SkillForge refinement loop |

All four can be automated. All four use the same pattern: measure with binary assertions, loop until perfect, keep or revert each change.

---

## 7. Cross-Reference Index

### Where to Find What

| Topic | Primary Document | Also Referenced In |
|---|---|---|
| NormieForge product concept | `docs/normieforge-product-concept.md` | Landing page, onboarding |
| Metaprogram detection (consumer) | `docs/normieforge-metaprogram-engine.md` | This master doc, section 3 |
| Social scraping + onboarding | `docs/normieforge-onboarding-personalization.md` | Product concept, metaprogram engine |
| Landing page copy + psychology | `docs/normieforge-landing-page.md` | Product concept |
| Timonacci Labs (knowledge hub) | `docs/prd-timonacci-labs.md` | This master doc, section 6 |
| Tool Chamber + SkillForge | `docs/research-workflow-tool-chamber.md` | This master doc, section 6 |
| Brain file (Screen Agent) | `my_brain_default.md` | Screen agent, VibeHelper |
| Meta Engine backend code | `server/services/meta_training_ingestor.py` | This master doc, section 4 |
| Meta Engine writing | `server/services/meta_writing_engine.py` | This master doc, section 4 |
| Meta Engine routing | `server/services/meta_output_router.py` | This master doc, section 4 |
| Meta Engine API | `server/routers/meta_training.py` | This master doc, section 4 |
| Meta Engine UI | `ui/src/pages/MetaEnginePage.tsx` | This master doc, section 4 |
| MetaScraper detection | `metascraper/detector.py` | This master doc, sections 3-4 |
| MetaScraper patterns | `metascraper/patterns.py` | This master doc, sections 3-4 |
| MetaScraper rewriting | `metascraper/rewriter.py` | This master doc, section 4 |
| MetaScraper pipeline | `metascraper/pipeline.py` | This master doc, section 4 |
| MetaScraper scraping | `metascraper/scraper.py` | This master doc, section 4 |
| VibeHelper agent | `vibehelper/agent.py` | This master doc, section 4 |
| VibeHelper CLI | `vibehelper/cli.py` | This master doc, section 4 |
| VibeHelper setup | `vibehelper/setup_wizard.py` | This master doc, section 4 |
| Screen Agent | `screen_agent.py` | This master doc, section 4 |
| Deploy Agent | `deploy_agent.py` | This master doc, section 4 |

### Complete File Inventory

**Design Documents (7 files):**
- `docs/normieforge-product-concept.md`
- `docs/normieforge-metaprogram-engine.md`
- `docs/normieforge-onboarding-personalization.md`
- `docs/normieforge-landing-page.md`
- `docs/prd-timonacci-labs.md`
- `docs/research-workflow-tool-chamber.md`
- `my_brain_default.md`

**Meta Engine Backend (4 files):**
- `server/services/meta_training_ingestor.py`
- `server/services/meta_writing_engine.py`
- `server/services/meta_output_router.py`
- `server/routers/meta_training.py`

**Meta Engine Frontend (1 file):**
- `ui/src/pages/MetaEnginePage.tsx`

**MetaScraper Package (6 files):**
- `metascraper/__init__.py`
- `metascraper/detector.py`
- `metascraper/patterns.py`
- `metascraper/rewriter.py`
- `metascraper/scraper.py`
- `metascraper/pipeline.py`

**VibeHelper Package (4 files):**
- `vibehelper/__init__.py`
- `vibehelper/agent.py`
- `vibehelper/cli.py`
- `vibehelper/setup_wizard.py`

**Standalone Agents (2 files):**
- `screen_agent.py`
- `deploy_agent.py`

**Total: 24 files created this session**

---

## 8. What's Next

### Immediate (This Week)

1. **SkillForge Loop** — Build the Karpathy auto-research loop for skill refinement. Fully specified in `docs/research-workflow-tool-chamber.md`. Few-day build, immediate ROI on every existing skill. This is infrastructure the entire system feeds into.

2. **Wire MetaScraper scrapers to real APIs** — The scraper scaffolding exists but platform API calls are `pass` placeholders. Need real implementations for Twitter (via Nitter or API v2), LinkedIn (via Proxycurl or Google SERP), and Instagram (via Instaloader).

3. **Test Meta Engine end-to-end** — Upload a real NLP training video, verify extraction quality, generate copy for all 8 profiles, verify output routing creates proper files.

### Near-Term (This Month)

4. **Timonacci Labs Phase 1: Truth Documents** — Build the truth document system with SQLite models, topic matching (keyword + semantic layers), Sword Sharpener diff engine, version history, CRUD API, and basic viewer UI.

5. **Timonacci Labs Phase 2: Multi-Source Ingestion** — Article adapter (URL scraping), PDF adapter, transcript adapter. Universal `IngestedContent` model so the Matcher doesn't care where content came from.

6. **NormieForge MVP** — Landing page + waitlist. One life module (budget tracker with Plaid API). Brain file. VibeHelper screen agent for when setup goes wrong. Metaprogram detection from hero input + 3-tap quiz.

### Medium-Term (Next Quarter)

7. **Timonacci Labs Phase 3: The Diverter** — Auto-route knowledge from truth documents to skills, prompts, reference files, PRDs, build rules. Human-in-loop review UI. Auto-approve mode for trusted categories.

8. **Tool Chamber v1** — LangGraph orchestrator + Activepieces pieces for connectors + Stripe Blueprint execution control. Skill capture from successful execution paths.

9. **NormieForge social scraping** — Full MetaScraper integration for instant personalization on sign-up. All 3 metaprograms detected from social data. 8 voice templates.

### Long-Term (The Vision)

10. **NormieForge AI voice blending** — Not just 8 templates, but a continuous spectrum. Real-time refinement from interaction patterns. Metaprogram shift detection ("you've become more proactive this month!").

11. **Full metaprogram suite** — Expand consumer detection to all 5 axes (add big picture/detail and proactive/reactive). Voice becomes truly unique per user — no templates, pure AI calibration.

12. **Platform play** — With millions of NormieForge users with AI agents managing their lives: financial services partnerships, health/wellness partnerships, local services. Each partnership = revenue share on a captive, high-intent audience.

---

## Key Quotes Worth Preserving

> "Nobody else is doing this. ChatGPT talks to everyone the same way. Every app has one voice. NormieForge has 8 voices and picks the right one."

> "Users can't articulate why it works. They just say 'it gets me.' That feeling = retention. That feeling = word of mouth."

> "The personalization IS the virality. Generic briefings don't get screenshotted. But a briefing that sounds like your best friend who also happens to be an accountant? That gets shared."

> "The walls matter more than the model." — Stripe Minion blog analysis

> "What if the WALLS themselves are AI-generated, and then FROZEN into deterministic structure?"

> "The system literally learns its own deterministic structure over time."

> "Triggering reliably and producing great outputs are different problems."

> "After 3 months, the AI knows your financial personality, your communication style, your life rhythms, your blind spots, your values. No other product has this. This is the moat. It's not the features. It's the RELATIONSHIP."

---

*This document was created as a preservation record. Every concept, every system design, every piece of code, every architectural decision from this brainstorm session is captured here. When picking up any of these threads in a future session, start by reading this document and then diving into the specific referenced docs and code files.*
