# YT Lab — Ingestion Expansion PRD

**Status:** Ready to build (open questions resolved)
**Owner:** Lober
**Goal:** Turn YT Lab from "YouTube-only, single-URL, captions-only" into "any video, any platform, one-at-a-time or bulk, with cross-video synthesis."

## Locked-in Decisions
1. **Whisper engine:** Local Whisper is default. User can add OpenAI Whisper API key in settings → toggle per job or globally to switch to paid API (faster, ~$0.006/min).
2. **Batch size cap:** 50 URLs per batch.
3. **Storage:** Audio deleted immediately after transcription. Video NOT downloaded by default (toggle per job). Transcripts kept forever. "Save video" is a v2 feature (Google Drive target) — skip for v1.
4. **Synthesis model:** Sonnet default, Opus toggle. Auto-generate a worksheet/checklist (Sonnet) after every transcription. Opus reserved for deep reasoning / tool-spec generation from transcripts.
5. **YouTube Live retry logic:** When a live video has no captions yet, retry `youtube-transcript-api` every 6 hours for up to 48 hours before falling back to Whisper. Most lives get auto-captions within 24 hours — this saves money on the 95% case.

---

## The Three Segments

The user's ask breaks into three distinct pieces of work. This PRD gives **full scope for Segments 1 + 2** (build now) and **descriptions only for Segment 3** (build later).

| Segment | What | Build When |
|---|---|---|
| 1 | Universal single-video ingestion | NOW |
| 2 | Bulk ingestion + cross-video synthesis | NOW |
| 3 | In-app YouTube discovery (search, follow creators, notifications, mobile) | LATER |

---

# SEGMENT 1 — Universal Single-Video Ingestion

## Problem
Today YT Lab only works on regular YouTube videos that have captions enabled. Fails on:
- YouTube live streams
- YouTube videos with captions disabled
- Twitter/X videos
- TikTok, Vimeo, Instagram, Reddit, etc.
- Files already on disk (mp3/mp4)
- Anything gated behind a login

## Solution — Fallback Chain

User pastes any URL or uploads any file. Backend runs this chain automatically, no user choice needed:

```
1. Is it a YouTube URL with captions?
   YES → youtube-transcript-api (fast, free)            [existing path]
   NO  → continue

2. Is it a YouTube Live URL with no captions yet?
   YES → queue a retry job: check every 6h for 48h       [NEW]
         if captions appear → use free path
         if timeout → fall back to Whisper (step 4)

3. Is it a URL yt-dlp can handle? (~1000 supported sites)
   YES → yt-dlp downloads audio → Whisper transcribes   [NEW]
   NO  → continue

4. Is it an uploaded audio/video file?
   YES → Whisper transcribes                             [NEW]
   NO  → show "unsupported source" error
```

### Whisper engine selection (inside step 3 / 4)
- Default: local Whisper (free, slow)
- If user has Whisper API key configured AND toggle is on → use OpenAI Whisper API (paid, ~10x faster)
- Auto-compress audio to mono 32kbps mp3 before API upload (stays under 25MB limit for files up to ~2 hours)

User sees one progress bar. Behind the scenes the backend picks the right path.

## User-Facing UI Changes

1. **Input box** accepts:
   - Any URL (YouTube, Twitter/X, TikTok, Vimeo, Instagram, etc.)
   - Or a **drag-and-drop file upload** zone (mp3, mp4, wav, m4a, webm)

2. **Optional checkboxes** (collapsed under "Advanced"):
   - `[ ] Also save the video file` (download mp4 alongside transcript)
   - `[ ] Also save the audio file` (download mp3 alongside transcript)
   - `[ ] Use cookies for gated content` (paste cookies.txt — power user only, defer to v2)

3. **Source detection badge** — once URL is pasted, show "Detected: YouTube Live" or "Detected: Twitter/X" or "Detected: File upload" so user knows which path will run.

## Backend Changes

### New service: `server/services/yt_lab_ingest.py`
Single entry point: `ingest(source)` where `source` is a URL or file path.

Functions:
- `detect_source_type(url)` → `"youtube_captioned" | "youtube_live" | "yt_dlp_supported" | "file_upload" | "unsupported"`
- `fetch_transcript_youtube_captions(url)` → existing path
- `download_media_yt_dlp(url, audio_only=True)` → returns local file path
- `transcribe_whisper(file_path)` → returns transcript text
- `ingest(source, options)` → orchestrates the chain, returns `{transcript, video_path?, audio_path?, metadata}`

### New dependencies
- `yt-dlp` (Python package)
- `openai-whisper` (local, free, slow) OR OpenAI Whisper API (paid, fast) — **decide below**
- `ffmpeg` system binary (already needed for Whisper)

### Transcription engine choice
Three options. Recommend **hybrid**: local for personal use, API as fallback/opt-in for speed.

| Engine | Cost | Speed | Quality |
|---|---|---|---|
| Whisper local (medium) | Free | Slow (CPU: ~0.3x realtime) | Good |
| OpenAI Whisper API | $0.006/min | Fast (~10x realtime) | Good |
| Deepgram / AssemblyAI | ~$0.004/min | Fastest, best diarization | Best |

**Decision for v1:** Local Whisper only. Add API toggle in v2 when bulk ingestion makes speed matter.

### File storage (disk-space-conscious)
Lober's system has ~10-15GB free. Video/audio files cannot accumulate locally.
- Transcripts → existing YT Lab transcript store, kept forever (tiny text files)
- Audio files → temp folder, **deleted immediately after transcription completes** (success or failure)
- Video files → **not downloaded by default.** "Save video" feature deferred to v2 (Google Drive target)
- No "pin" feature needed in v1 since nothing local persists by default

## Data Model (new fields)
Extend existing YT Lab job record:
```
job {
  id
  source_url | source_file
  source_type           # which path ran
  transcript_text
  transcript_path       # NEW
  audio_path            # NEW, nullable
  video_path            # NEW, nullable
  duration_seconds      # NEW
  ingest_engine         # "captions" | "whisper-local" | "whisper-api"
  created_at
  status                # queued | downloading | transcribing | done | error
  error_message
}
```

## Acceptance Criteria — Segment 1
- [ ] Paste a regular YouTube URL → works exactly as today
- [ ] Paste a YouTube live URL → downloads audio, transcribes, returns text
- [ ] Paste a Twitter/X video URL → same
- [ ] Paste a TikTok URL → same
- [ ] Upload an mp3 file → transcribes, returns text
- [ ] Upload an mp4 file → extracts audio, transcribes
- [ ] Checkbox "save video" produces a downloadable mp4 in results
- [ ] Error states clear: "unsupported source," "transcription failed," "download failed"
- [ ] Progress bar shows current phase ("downloading… transcribing… done")

---

# SEGMENT 2 — Bulk Ingestion + Cross-Video Synthesis

## Problem
You want to research a topic (example: Google Ask Maps) by ingesting **8 videos at once** from multiple creators, then having an LLM combine them into one master checklist / worksheet. Today you'd have to run YT Lab eight separate times and manually stitch the outputs.

## Solution — "Batch Jobs"

### Concept
A **Batch** = a named container for N individual ingestion jobs, with an optional synthesis step at the end.

```
Batch: "Google Ask Maps Research"
├── Job 1: [creator A's video]  → transcript
├── Job 2: [creator B's video]  → transcript
├── Job 3: [creator C's video]  → transcript
├── ... (up to N)
└── Synthesis: combined output (master notes / checklist / SOP)
```

### User-Facing UI — "Create Batch" Screen

1. **Name the batch** (text input, required) — e.g. "Google Ask Maps Research"
2. **Add URLs** — one of:
   - Paste-list box (one URL per line, up to 50)
   - Drag-and-drop multiple files
   - (Future: "import from YouTube channel" — see Segment 3)
3. **Synthesis prompt template** — dropdown with presets:
   - "Master checklist — combine all unique steps, dedupe overlaps"
   - "Consensus + edge cases — what do most say, what does only one say"
   - "SOP / tutorial — step-by-step in order"
   - "Raw — just concatenate all transcripts, no LLM synthesis"
   - "Custom" (user writes their own prompt)
4. **Submit** — queues all jobs

### Batch Detail Page
- Header: batch name, progress bar ("5 of 8 complete")
- Table of jobs — each row shows URL/filename, status, duration, link to individual transcript
- Synthesis section at the bottom:
  - Locked until all jobs complete
  - Shows combined output as markdown
  - "Regenerate" button with new prompt
  - "Copy all" / "Download as .md" / "Send to Claude" buttons

### Synthesis Pipeline
1. Wait for all jobs done (or user clicks "synthesize partial")
2. Concatenate transcripts with headers: `## Video 1: [title]\n[transcript]\n\n## Video 2: ...`
3. Feed to Claude with chosen prompt template
4. Save output as part of the batch record
5. Allow re-synthesis with different prompt without re-ingesting

### Concurrency
- yt-dlp downloads: 3 parallel max (avoid rate limits / IP blocks)
- Whisper transcription: 1 at a time on CPU (queue the rest)
- If Whisper API enabled: 5 parallel

## Backend Changes

### New service: `server/services/yt_lab_batch.py`
- `create_batch(name, sources, synthesis_prompt)` → batch_id
- `get_batch_status(batch_id)` → progress
- `run_synthesis(batch_id, prompt_override?)` → synthesis_text

### New router: `server/routers/yt_lab_batch.py`
Endpoints:
- `POST /api/yt-lab/batches` — create
- `GET /api/yt-lab/batches` — list
- `GET /api/yt-lab/batches/{id}` — detail
- `POST /api/yt-lab/batches/{id}/synthesize` — (re)run synthesis
- `DELETE /api/yt-lab/batches/{id}`

### Data Model
```
batch {
  id
  name
  synthesis_prompt
  synthesis_output
  synthesis_output_updated_at
  status                   # queued | running | done | partial | error
  created_at
}
batch_job {
  id
  batch_id
  source_url | source_file
  job_id                   # FK to existing ingest job table
  order_index
}
```

## UI Layout
Add a **"Batches"** tab to YT Lab alongside the existing single-video flow.
- `/yt-lab` — single video (existing)
- `/yt-lab/batches` — list of batches
- `/yt-lab/batches/new` — create
- `/yt-lab/batches/{id}` — detail

## Acceptance Criteria — Segment 2
- [ ] Paste 8 URLs, name the batch, submit → all 8 queue and process
- [ ] Progress bar updates as each job completes
- [ ] Individual transcripts viewable per-job
- [ ] Synthesis runs automatically when all jobs done
- [ ] Synthesis output is a clean markdown doc combining all transcripts per the chosen prompt
- [ ] "Regenerate with different prompt" works without re-downloading
- [ ] Batches persist across sessions (list view shows history)
- [ ] Can mix sources in one batch (YouTube + Twitter + uploaded file = fine)

---

# SEGMENT 3 — In-App Discovery (DESCRIPTION ONLY, build later)

This is the "don't make me copy/paste URLs anymore" segment. Three sub-pieces:

## 3A — YouTube Search & Channel Tracking Inside YT Lab

**What:** Search YouTube directly from YT Lab. Save creators you trust. See their new videos without leaving the app. Check-mark the ones you want → click "ingest selected" → auto-creates a batch.

**How (tech):**
- **YouTube Data API v3** — official Google API
- **Cost:** Free up to 10,000 "units" per day per project. Search = 100 units, video details = 1 unit. Translation: ~100 searches/day free, which is plenty for personal use. Paid tier exists but you likely never hit it
- **Auth:** Google Cloud project + API key. Free to set up
- **Limits:** Can't stream videos via API, but you don't need to — you already have yt-dlp for that. API is just for search + metadata

**UX sketch:**
- New tab "Discover" in YT Lab
- Search bar, results list with thumbnails
- "Follow creator" button
- "Followed creators" feed shows their latest videos
- Checkboxes on each video → "Ingest Selected (3)" button at bottom → sends to Batch flow from Segment 2

**Categorization:**
- Tag creators with labels ("AI tools," "SEO," "Anthropic news")
- Filter feed by tag
- Create "topic watchlists" — saved searches that auto-refresh

## 3B — Notifications

**What:** When a followed creator posts, or a watchlist finds a new match, notify you.

**Options:**
- **Email** — cheapest, reliable
- **Push notification via web app** — requires PWA setup, works on phone/desktop browsers
- **Discord/Slack webhook** — dead simple, free
- **SMS** — Twilio, ~$0.01/msg

**Recommendation:** Start with email + Discord webhook. Zero infra, zero cost.

## 3C — Mobile App

**The real question:** do you need a native mobile app, or does a **PWA** (Progressive Web App) cover it?

**PWA path (recommended):**
- Same codebase as YT Lab web app
- Add a manifest + service worker → users "install to home screen" from their browser
- Gets an app icon, runs fullscreen, can send push notifications
- Works on iOS and Android
- **Zero extra cost, zero app store approval, zero new stack**

**Native app path (only if PWA hits a wall):**
- React Native or Expo — reuses React knowledge
- App Store: $99/yr Apple + $25 one-time Google
- Review process, resubmission for updates
- Only worth it if you need deep OS integration (share sheet from YouTube app → YT Lab, background downloads, etc.)

**Subscription model impact:** Neither PWA nor native breaks your subscription model. Both can point to the same backend + auth. Only caveat: if you put it in the Apple App Store and charge via in-app purchase, Apple takes 30%. You can avoid this by making subscriptions web-only and the app "login with existing account."

**Share Sheet integration (the real win):**
On mobile, the dream flow is: you're in the YouTube app, tap Share, tap "Send to YT Lab," done. This requires either a native app OR a PWA with share_target in the manifest. PWAs support this on Android fully, partially on iOS.

## Segment 3 Summary
- **3A YouTube search:** Feasible, mostly free (YouTube API free tier covers personal use). Moderate build.
- **3B Notifications:** Easy. Email + Discord webhook first, push later.
- **3C Mobile:** PWA first. Native only if you hit limits. Share-sheet integration is the killer feature — aim for it.

**Build order when you come back to Segment 3:** 3A search → 3B email/Discord notifications → 3C PWA + share target. Native app last or never.

---

# Out of Scope (For Now)
- Screen recording of gated content (OBS + VB-Cable) — **desktop-tool problem, not YT Lab's job.** Recommend users upload the resulting file.
- Real-time transcription of live streams (transcribe as it airs). Possible but not needed yet.
- Speaker diarization (who said what). Defer — Deepgram/AssemblyAI upgrade later.
- Translation. Whisper can do it; expose as v2 checkbox.
- Multi-user / team features. YT Lab is personal tool today.

---

# Build Order

1. **Segment 1 first** — universal single-video ingestion with fallback chain
2. **Segment 2 right after** — bulk + synthesis (reuses all of Segment 1's plumbing)
3. **Ship, use for a week, adjust**
4. **Segment 3 later** — discovery, notifications, mobile PWA

Segments 1 + 2 are the immediate PRD. Segment 3 is on the roadmap but not scoped for coding yet.

---

# Open Questions — RESOLVED
See "Locked-in Decisions" at top of document.

# Post-Transcription Auto-Worksheet (default behavior)
Every successful transcription automatically kicks off a Sonnet pass that converts the narrative transcript into a structured worksheet:
- Key features / claims highlighted
- Action items / steps extracted
- Quotes worth keeping
- Open questions / edge cases
- One-line summary

Worksheet is stored alongside the transcript. User can re-run with Opus via a toggle for higher-stakes content (e.g. "turn this into a buildable tool spec").
