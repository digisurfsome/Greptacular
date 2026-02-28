# YT Strategy Lab — Video Discovery & Queue System

> **Status:** Feature spec. This is the "input side" of the Knowledge Pipeline — how videos get into the system for processing.

---

## The Problem

Right now, YT Lab processes one video at a time. You paste a URL, wait, get results. But the real workflow is:

1. You're browsing YouTube (or your phone) and see 10-15 videos worth processing
2. You don't have time to watch them all — you just want the notes
3. Some are from creators you know (you can pre-configure how to extract)
4. Some are new discoveries (system should help find these)
5. You need to triage fast: read notes (or listen to them), then decide which ones get the full treatment

**The current system handles step 2 onward (after you have a URL). It completely misses step 1 — finding and selecting the videos.**

---

## What Gets Built

### 1. Video Browser (Your Channel Feed)

A panel at the top of YT Lab where you can browse your YouTube subscriptions/feed, search YouTube, and bulk-select videos for processing.

```
┌──────────────────────────────────────────────────────────────────┐
│  Video Browser                                            [⚡🔍] │
│  ┌──────────┐ ┌───────────┐ ┌──────────────┐                    │
│  │ My Feed  │ │ Discovery │ │ Mixed View   │                    │
│  └──────────┘ └───────────┘ └──────────────┘                    │
├──────────────────────────────────────────────────────────────────┤
│  🔍 [Search: "claude code tutorial"                        ] [Go]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ☐ ┌─────┐  AI Agency Automation 2025           Cody · 32 min  │
│    │ 📺  │  How to build an AI ad agency...     ⭐ Known Creator │
│    └─────┘  2 days ago · 45K views                              │
│                                                                  │
│  ☑ ┌─────┐  Lead Gen With Claude Agents         Nick · 18 min  │
│    │ 📺  │  Scraping + enrichment pipeline...   🆕 New Creator  │
│    └─────┘  1 week ago · 12K views                              │
│                                                                  │
│  ☑ ┌─────┐  Anthropic Claude Bot Overview       Matt · 25 min  │
│    │ 📺  │  New feature walkthrough...          ⭐ Known Creator │
│    └─────┘  3 hours ago · 8K views                              │
│                                                                  │
│  ☐ ┌─────┐  Claude vs ChatGPT for Coding        Sam · 15 min  │
│    │ 📺  │  Side-by-side comparison...          🆕 New Creator  │
│    └─────┘  5 days ago · 67K views                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  2 selected  [📋 Auto-Notes Only] [🚀 Full Processing] [Queue] │
└──────────────────────────────────────────────────────────────────┘
```

**Three tabs:**
- **My Feed** — Videos from your YouTube subscriptions (your current algorithm)
- **Discovery** — System-curated feed based on your processing history (the "new algorithm")
- **Mixed View** — Both feeds interleaved, tagged with source (🔵 My Feed / 🟢 Discovery)

**Key interactions:**
- Checkbox per video — select multiple for batch operations
- Search bar — search YouTube directly from within YT Lab
- Action buttons at bottom: "Auto-Notes Only" (fast), "Full Processing" (deep), "Queue" (add to staging)

### 2. Auto-Notes Pipeline

When videos are selected, the first thing that happens is **notes extraction** — not full strategy processing. This is the fast pass.

```
Video Queue → Transcript Pull → Auto-Notes → User Triage → Full Processing
   (yt-dlp)     (instant)      (30 sec/video)  (2 min total)  (only selected)
```

**What Auto-Notes produces:**

```
┌──────────────────────────────────────────────────────────────────┐
│  📝 Auto-Notes: "Lead Gen With Claude Agents"                   │
│  Nick · 18 min · Processed 35 sec ago                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🎯 CORE TOPIC                                                  │
│  Building a lead generation pipeline using Claude agents for     │
│  B2B SaaS companies. Focuses on LinkedIn + Apollo enrichment.    │
│                                                                  │
│  📌 KEY POINTS                                                   │
│  1. Uses Apollo API for company enrichment ($49/mo plan)         │
│  2. LinkedIn Sales Nav scraping with browser automation          │
│  3. Claude agent validates lead quality before adding to CRM     │
│  4. Claims 40% response rate on cold outreach with this method   │
│  5. Full pipeline runs in ~3 min per 100 leads                  │
│                                                                  │
│  🔧 TOOLS MENTIONED                                             │
│  Apollo, LinkedIn Sales Navigator, Claude Code, Instantly,       │
│  Google Sheets, Zapier                                           │
│                                                                  │
│  💡 NOTABLE QUOTES                                               │
│  "The enrichment step is where most people skip and that's why  │
│   their response rates are garbage" (8:42)                      │
│  "Don't use GPT for lead scoring — Claude understands context   │
│   10x better for B2B" (14:15)                                   │
│                                                                  │
│  📊 VERDICT                                                      │
│  High relevance. Covers a complete pipeline with specific tools  │
│  and pricing. Creator has hands-on experience (shows his own     │
│  dashboard). Worth full processing for the enrichment section.   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  [🔊 Listen] [⏩ 1.5x] [🚀 Full Process] [📝 Add Context] [Skip]│
└──────────────────────────────────────────────────────────────────┘
```

**The triage flow:**
1. Read the notes (or tap "Listen" to hear them read aloud)
2. Speed adjuster for audio playback (1x, 1.25x, 1.5x, 2x)
3. If worth deeper dive → tap "Full Process" (optionally add your context first)
4. If not interesting → tap "Skip"
5. Move to next video's notes

**Time savings:**
- Old way: Watch 18 min video at 1.5x = 12 minutes. Then write context for extraction.
- New way: Read notes in 2 minutes (or listen at 2x in 3 minutes). Add context in 30 seconds.
- **6x faster triage.** 15 videos in 30 minutes instead of 3 hours.

### 3. Creator Presets

Known creators get pre-configured extraction profiles.

```
┌──────────────────────────────────────────────────────────────────┐
│  Creator Presets                                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⭐ Cody (AI Automation Guy)                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Focus: Ad agency workflows, client acquisition systems    │  │
│  │  Note style: Detailed — he goes deep on implementation     │  │
│  │  Auto-context: "Focus on the automation stack and the      │  │
│  │    specific tools/APIs. Extract pricing for each tool.     │  │
│  │    Pay attention to client onboarding workflow."            │  │
│  │  Trust level: ⭐⭐⭐⭐⭐ (verified multiple times)            │  │
│  │  Videos processed: 12                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ⭐ Nick (Lead Gen Expert)                                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Focus: B2B lead generation, cold outreach automation      │  │
│  │  Note style: Summary — often covers same ground, look for  │  │
│  │    new tools or updated workflows only                     │  │
│  │  Auto-context: "Only extract if there's a NEW tool or      │  │
│  │    technique not covered in previous videos."              │  │
│  │  Trust level: ⭐⭐⭐⭐ (good but sometimes surface level)    │  │
│  │  Videos processed: 7                                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [+ Add Creator Preset]                                          │
└──────────────────────────────────────────────────────────────────┘
```

When a video from a known creator hits the queue, the system automatically applies their preset:
- Notes are extracted with the configured focus and style
- If auto-context is set, full processing can happen without user input
- Trust level affects how aggressively the system auto-processes

### 4. Topic Deep-Dive Templates

When something new drops (new tool, new feature, new technique), you want multiple perspectives. Templates pre-configure what you're looking for:

```
┌──────────────────────────────────────────────────────────────────┐
│  Topic Deep-Dive: "Claude Bot"                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Template: New Tool/Feature                                      │
│                                                                  │
│  ☑ Explainer     — What is it? How does it work?        0/1     │
│  ☑ Tutorial      — Step-by-step how to use it           0/2     │
│  ☑ Comparison    — How does it compare to alternatives?  0/1     │
│  ☐ Deep Analysis — Architecture, internals, limitations  0/1     │
│  ☐ Use Cases     — Real-world applications and examples  0/1     │
│                                                                  │
│  Auto-search: "claude bot tutorial", "claude bot review",        │
│               "claude bot vs chatgpt", "anthropic claude bot"    │
│                                                                  │
│  [🔍 Find Videos] [📋 Queue Auto-Notes] [Custom Search]         │
└──────────────────────────────────────────────────────────────────┘
```

**Preset templates:**
- **New Tool/Feature** — Explainer + Tutorial + Comparison
- **Technique/Strategy** — Overview + Implementation + Case Study
- **Industry Update** — News + Analysis + Impact Assessment
- **Creator Deep-Dive** — Binge a specific creator's best content

The system searches YouTube for each category, presents results, you check the ones you want, and they go through the auto-notes pipeline.

### 5. The "New Algorithm" (Discovery Feed)

This is the system-built feed that learns from your processing history. It's NOT your YouTube algorithm — it's yours.

**How it works:**
1. Track every video you process: topics, creators, tools mentioned, categories
2. Build a profile: "User is interested in: AI automation, lead gen, SaaS tools, Claude/Anthropic"
3. Use YouTube search API to find related content you haven't seen
4. Rank by relevance to your processing history
5. Surface new creators covering your topics

**The feed evolves:**
- Week 1: Mostly keyword-based search (topics from your processed videos)
- Week 2+: Creator network expansion (who do your favorite creators reference?)
- Week 4+: Trend detection (new topics appearing in your interest areas)
- Ongoing: Learns from what you skip vs. what you process

**Implementation:** This requires the YouTube Data API v3 for search. yt-dlp can list channel videos but can't do topic-based search or recommendation-style queries reliably.

---

## How YouTube Data Gets In (Technical)

### Option 1: yt-dlp Only (No API Key Needed)

yt-dlp can already do more than just download videos:

```bash
# List all videos from a channel
yt-dlp --flat-playlist --print "%(id)s %(title)s %(duration)s %(upload_date)s" \
  "https://www.youtube.com/@ChannelName/videos"

# Search YouTube (limited but works)
yt-dlp --flat-playlist --print "%(id)s %(title)s %(channel)s %(duration)s" \
  "ytsearch20:claude code tutorial"

# Get video metadata without downloading
yt-dlp --dump-json --no-download "https://www.youtube.com/watch?v=VIDEO_ID"

# List playlist contents
yt-dlp --flat-playlist --print "%(id)s %(title)s" \
  "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

**What yt-dlp CAN do:**
- List all videos from a specific channel URL
- Search YouTube by keyword (returns ~20 results per query)
- Get full metadata (title, description, duration, views, upload date, thumbnail)
- Get channel info
- Pull transcripts (via `--write-subs --write-auto-subs`)

**What yt-dlp CANNOT do:**
- Access your subscription feed (requires OAuth)
- Get personalized recommendations
- Advanced search filters (upload date ranges, category, etc.)
- Rate-limited and may get blocked with heavy use

### Option 2: YouTube Data API v3 (API Key Required)

**Cost:** Free quota of 10,000 units/day. That's approximately:
- 100 search queries (100 units each)
- 5,000 video detail lookups (1 unit each)
- 200 channel detail lookups (1 unit each)
- Far more than enough for daily use

**Getting a key:** Free at [console.cloud.google.com](https://console.cloud.google.com). Create project → Enable YouTube Data API v3 → Create API key. Takes 5 minutes.

**What the API gives us:**

```python
# Search YouTube
GET /youtube/v3/search?part=snippet&q=claude+code+tutorial&type=video&maxResults=25
# → returns: videoId, title, description, channelTitle, publishedAt, thumbnails

# Get video details (duration, views, likes)
GET /youtube/v3/videos?part=contentDetails,statistics&id=VIDEO_ID1,VIDEO_ID2,...
# → returns: duration, viewCount, likeCount, commentCount

# List channel videos
GET /youtube/v3/search?part=snippet&channelId=UC...&type=video&order=date&maxResults=50
# → returns: all videos from channel, newest first

# Get subscription feed (requires OAuth, not just API key)
GET /youtube/v3/subscriptions?part=snippet&mine=true
# → returns: channels you're subscribed to
# Then query each channel for recent videos
```

### Option 3: Hybrid (Recommended)

Use yt-dlp for transcripts and metadata (it's better at this) and YouTube API for search and channel browsing (it's better at this).

```
Search/Browse → YouTube Data API v3 (fast, structured, reliable)
Transcript pull → yt-dlp (already works, no API quota cost)
Video metadata → yt-dlp (richer than API for some fields)
Subscription feed → YouTube API with OAuth (future)
```

---

## The "My Channel" Toggle

To access your YouTube subscriptions, we need YouTube OAuth (not just an API key). This is a bigger setup:

1. Create OAuth 2.0 credentials in Google Cloud Console
2. User signs in with Google (grants YouTube read access)
3. System can then query subscriptions and feed

**Simpler alternative for now:** Instead of OAuth, let users add their favorite channels manually. The system remembers them and checks for new videos.

```
┌──────────────────────────────────────────────────────────────────┐
│  My Channels                                          [+ Add]   │
├──────────────────────────────────────────────────────────────────┤
│  ● Cody (@AIAutomationGuy)     3 new videos this week          │
│  ● Nick (@LeadGenNick)         1 new video this week           │
│  ● Matt (@MattWolfe)           5 new videos this week          │
│  ● Sam (@SamOnTech)            2 new videos this week          │
└──────────────────────────────────────────────────────────────────┘
```

When you add a channel URL, the system:
1. Pulls the channel's video list via yt-dlp or YouTube API
2. Shows recent videos you haven't processed
3. Checks for new uploads periodically (configurable)
4. Tags videos from known channels in the browser

**Phase 2:** Add proper YouTube OAuth for subscription sync. Then "My Feed" tab auto-populates from your actual YouTube subscriptions.

---

## Audio Notes (Text-to-Speech)

For the "listen to notes instead of reading" feature:

### Browser-Native (Free, Works Now)

```typescript
// Web Speech API — built into every modern browser
function speakNotes(text: string, speed: number = 1.5) {
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = speed  // 0.5 to 2.0
  utterance.pitch = 1.0
  utterance.voice = speechSynthesis.getVoices()
    .find(v => v.name.includes('Google') || v.name.includes('Natural'))
    || speechSynthesis.getVoices()[0]
  speechSynthesis.speak(utterance)
}

// Speed controls: 1x, 1.25x, 1.5x, 2x
// Pause/resume: speechSynthesis.pause() / .resume()
// Stop: speechSynthesis.cancel()
```

**Pros:** Free, instant, no API calls, works offline
**Cons:** Robot-sounding, limited voice quality

### Cloud TTS (Better Quality, Small Cost)

Google Cloud TTS or ElevenLabs for natural-sounding voices. ~$4/million characters. At ~500 chars per video note summary, that's 2,000 videos per dollar.

**Recommendation:** Start with browser-native. It's free and works today. Upgrade to cloud TTS later if the robot voice gets annoying.

---

## Implementation Plan

### Phase 1: Channel Browser + Search (Week 1)

**New backend endpoints:**
```
POST /api/yt-lab/search          → Search YouTube via yt-dlp
POST /api/yt-lab/channel/videos  → List videos from a channel URL
GET  /api/yt-lab/channels        → List saved channels
POST /api/yt-lab/channels        → Add a channel to track
DELETE /api/yt-lab/channels/{id} → Remove tracked channel
```

**New UI component:** `VideoBrowser.tsx`
- Search bar with YouTube search
- Channel list with "new videos" badges
- Video grid with checkboxes
- Bulk action bar (Queue / Auto-Notes / Full Process)

**Data flow:**
```
User searches → Backend calls yt-dlp → Returns video list → User selects → Queue
User adds channel → Backend stores URL → Periodic check for new videos
```

### Phase 2: Auto-Notes Pipeline (Week 2)

**New backend endpoint:**
```
POST /api/yt-lab/auto-notes      → Pull transcript + generate notes (fast pass)
POST /api/yt-lab/batch-notes     → Auto-notes for multiple videos
```

**New service:** `server/services/yt_notes.py`
- Pull transcript via yt-dlp (fast, already have this)
- Send to Claude with a focused "notes extraction" prompt (not full strategy)
- Return structured notes in 30-60 seconds per video
- Use Haiku for speed on notes extraction (Opus for full processing)

**New UI component:** `NotesTriageView.tsx`
- Swipeable card stack of auto-notes
- Listen button with speed control (Web Speech API)
- "Full Process" / "Add Context" / "Skip" actions
- Progress indicator (3 of 15 triaged)

### Phase 3: Creator Presets (Week 2-3)

**New backend endpoints:**
```
GET  /api/yt-lab/creators         → List creator presets
POST /api/yt-lab/creators         → Create/update preset
DELETE /api/yt-lab/creators/{id}  → Delete preset
```

**New UI component:** `CreatorPresets.tsx`
- Preset editor (focus areas, note style, auto-context, trust level)
- Auto-detection: when a video from a known channel is queued, apply preset
- Stats: videos processed per creator, last processed date

### Phase 4: Discovery Feed + Topic Templates (Week 3-4)

**Requires:** YouTube Data API v3 key (free, user configures in settings)

**New backend:**
- `server/services/yt_discovery_feed.py` — builds interest profile from processing history, generates search queries, ranks results
- Topic deep-dive template system

**New UI:**
- Discovery tab in Video Browser
- Topic Deep-Dive modal
- Mixed view with source tags

### Phase 5: YouTube OAuth (Future)

- Google OAuth for subscription access
- Auto-sync subscription feed
- "My Feed" tab shows actual YouTube feed
- Desktop-only (OAuth callback needs a server)

---

## Database Requirements

All of this requires the database (see DATABASE_STRATEGY.md). New tables needed:

```sql
-- Tracked YouTube channels
create table tracked_channels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  channel_url text not null,
  channel_name text,
  channel_id text,                  -- YouTube channel ID
  last_checked_at timestamptz,
  check_frequency interval default '6 hours',
  creator_preset_id uuid references creator_presets(id),
  created_at timestamptz default now()
);

-- Creator presets (extraction profiles)
create table creator_presets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  channel_name text not null,
  focus_areas text[],               -- what to pay attention to
  note_style text,                  -- 'detailed', 'summary', 'key-points-only'
  auto_context text,                -- pre-filled context for full processing
  trust_level integer default 3,    -- 1-5
  videos_processed integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Auto-notes (fast pass before full processing)
create table auto_notes (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  core_topic text,
  key_points jsonb,                 -- array of bullet points
  tools_mentioned text[],
  notable_quotes jsonb,             -- array of {quote, timestamp}
  verdict text,                     -- relevance assessment
  model_used text,
  processing_time real,
  triaged boolean default false,    -- user has reviewed these notes
  triage_action text,               -- 'process', 'skip', 'later'
  user_context text,                -- context added during triage
  created_at timestamptz default now()
);

-- Topic deep-dives
create table topic_dives (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  topic text not null,
  template text,                    -- 'new_tool', 'technique', 'industry_update'
  search_queries text[],            -- auto-generated search terms
  categories jsonb,                 -- {explainer: {needed: 2, found: 0}, tutorial: ...}
  status text default 'active',     -- active, completed, archived
  created_at timestamptz default now()
);

-- Interest profile (for Discovery feed)
create table interest_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  topics jsonb,                     -- weighted topic list
  creators jsonb,                   -- known creators with scores
  tools jsonb,                      -- tools/products tracked
  last_updated timestamptz default now(),

  unique(user_id)
);
```

---

## What Can Be Built TODAY (No Database, No API Key)

Even before Supabase and YouTube API:

1. **YouTube search via yt-dlp** — `ytsearch20:query` works right now
2. **Channel video listing via yt-dlp** — paste a channel URL, get video list
3. **Auto-notes extraction** — transcript pull + Haiku/Opus summarization
4. **Checkbox selection + batch queue** — UI-only, localStorage for now
5. **Web Speech API for listening** — browser-native, zero setup
6. **Creator presets** — localStorage-based until database exists

That's Phase 1 and most of Phase 2 — no external dependencies needed.

---

## TL;DR

**Video Browser** with search + channel tracking + checkboxes for bulk selection. **Auto-Notes Pipeline** that extracts key points from transcript in 30 seconds (instead of watching 30 minutes). **Creator Presets** that pre-configure extraction for known channels. **Topic Deep-Dives** for when something new drops and you want 5-10 perspectives. **Discovery Feed** that learns from your history and surfaces new content.

The whole point: **triage 15 videos in 30 minutes instead of 3 hours.** Read (or listen to) the notes, decide which ones get the full treatment, move on.

Phase 1-2 work TODAY with zero new infrastructure. Phase 3-5 need Supabase + YouTube API key (both free).
