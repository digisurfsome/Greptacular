# Operating System Creator — Proof of Concept: YouTube Video Intelligence Pipeline

> **What this is:** We're running the Wizard Questionnaire (Part 2) on a YouTube video processing system. This is the first MULTI-LEVEL test of the framework — the system has two distinct phases (Ingest then Filter), where the second phase is dynamic and stackable. This tests whether the 6-step pattern handles variable-depth processes.

---

## Section A: Big Picture (Filled Out)

**A1. Process name:** YouTube Video Intelligence Pipeline

**A2. Walk me through what a human does today:**

### Level 1 — Ingest (runs for every video, no exceptions):
1. Encounter a YouTube video worth processing (browsing, recommendations, someone shares a link, researching a topic)
2. Copy the video URL
3. Run a Python script that transcribes the video (pulls audio, runs through Whisper or similar)
4. Get back a raw transcript — it's one continuous stream of text, no structure, no paragraphs, no formatting. Nearly unreadable.
5. Read through the raw transcript manually
6. Pull out the key points, sub-points, supporting details, parameters, action items
7. Organize all of that into a worksheet format — structured, scannable, every point accounted for with hierarchy (main point → sub-points → details)
8. Save the worksheet somewhere (currently nowhere organized — that's a problem)

### Level 2 — Filter (runs on demand, 0 to many filters per video):
9. Decide what this video content is useful FOR — is it a tool to build? A checklist to follow? A skill to create? A step-by-step process? A reference for a knowledge base?
10. Based on that decision, reprocess the worksheet through a specific lens/filter
11. Extract a structured output in that filter's format (e.g., a checklist with numbered steps, or a skill file with specific sections, or a tool spec with inputs/outputs)
12. If multiple use cases apply — repeat steps 9-11 for each additional filter
13. Sometimes combine multiple videos through the same filter (e.g., "put these 3 videos together into one master checklist")
14. Sometimes come back days/weeks later and run a video through a NEW filter that didn't exist when it was first processed

**A3. How often:**
- [x] Multiple times per day
- Roughly 10 videos per day encounter rate. Not all get processed — but the backlog grows fast.

**A4. How long per run:**
- Level 1 (transcript + worksheet): 20-40 minutes per video manually (transcript is ~2 min automated, worksheet is the bottleneck)
- Level 2 (per filter): 10-20 minutes per filter per video manually
- Total for one video with 3 filters: 50-100 minutes

**A5. Items per run:** ~10 videos/day encountered. Currently only 2-3 get fully processed because it takes too long.

**A6. Starting data:**
- [x] A website or web app (YouTube — video URLs)
- [x] Someone sends it to you (links shared in Slack, Discord, email, social media)
- [x] Manual research (browsing YouTube, following channels, topic searches)

**A7. End result goes to:**
- [x] Into a database (processed transcripts + worksheets + filter outputs need persistent storage)
- [x] Saved to a file (individual filter outputs as standalone docs)
- [x] Into a software tool (AutoForge workspace — skills, tools, checklists feed back into the system)

**A8. Tools already in use:**

| Tool/Service | What it's used for | Has API? | API docs URL |
|---|---|---|---|
| YouTube | Source of videos | Yes (YouTube Data API v3) | developers.google.com/youtube |
| yt-dlp / Python transcript script | Downloading audio + transcribing | CLI tool (no API needed) | github.com/yt-dlp/yt-dlp |
| Whisper / transcription engine | Speech-to-text | Yes (OpenAI API or local) | platform.openai.com/docs |
| Claude (Haiku/Sonnet) | AI processing for worksheet + filters | Yes (Anthropic API) | docs.anthropic.com |
| AutoForge YT Lab | Existing rigid tool — single-format only | Internal | N/A |
| Supabase | Database for storage | Yes | supabase.com/docs |

**A9. What breaks most often:**
- Raw transcript is unreadable — one giant stream of words with no structure. This is the #1 bottleneck. Can't do anything useful until it's restructured.
- No way to save or organize processed videos — everything is one big mess with no projects, no categories, no retrieval
- Existing YT Lab is rigid — built one way, one format, no flexibility. Can't apply different filters or save results
- Can't go back and reprocess — once it's done, starting over is required to get a different format
- No presets — every time you process a video, you're starting from scratch on what you want from it
- Can't combine multiple videos — no way to say "merge these 3 transcripts and give me one unified checklist"
- Processing 10 videos/day manually is impossible — only getting to 2-3, missing the other 7-8

**A10. Legal/compliance:** None. Public YouTube content. No personal data handling. No regulated industry.

---

## Section B: Step Breakdown

---

## LEVEL 1 — INGEST PIPELINE (Every Video)

> Level 1 runs automatically for every video. The output is always the same: a structured transcript + worksheet stored in the database. No human decisions needed after providing the URL.

---

### Step 1: Video Capture

**B1. What the human does:** Copy a YouTube URL. Paste it into the system. Sometimes add a note about why they saved it or what category it belongs to.

**B2. Input needed:** YouTube video URL. Optional: user-provided tags, category, or note about why this video matters.

**B3. Decisions:** Is this video worth processing? (Human pre-filter — they already decided yes by the time they paste the URL.)

**B4. Could Claude decide?** No — this stays human. The human chooses what's worth their time. The system processes everything that comes in.

**B5. Output:** Video metadata record: URL, video title, channel name, duration, publish date, thumbnail, description, user tags.

**B6. Output goes to:**
- [x] Into a database (videos table — the starting record)
- [x] Into the next step (Step 2 gets the URL)

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| YouTube Data API v3 | Yes | Free (10,000 units/day) | Pulls title, channel, duration, description, thumbnail |
| yt-dlp | CLI | Free | Can also extract metadata without downloading |

**B8. Error case:** Invalid URL → reject with error message. Private/deleted video → mark as `unavailable`, alert user. Age-restricted → flag, may need auth.

**B9. Human time:** 30 seconds (copy-paste URL + optional tag).

---

### Step 2: Transcription

**B1. What the human does:** Run a Python script that downloads the audio from the YouTube video and transcribes it to text. Wait for it to finish.

**B2. Input needed:** YouTube URL from Step 1. Access to transcription service (Whisper API or local model).

**B3. Decisions:** None. This is a mechanical step — download audio, run through speech-to-text.

**B4. Could Claude decide?** No decisions to make — this is a pure pipeline step. Fully automated.

**B5. Output:** Raw transcript text — one continuous stream of words. Timestamps optional but useful if available.

**B6. Output goes to:**
- [x] Into a database (update the video record with raw_transcript field)
- [x] Into the next step (Step 3 uses the raw transcript)

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| YouTube captions (if available) | Yes (YouTube API) | Free | Fastest — pull existing captions. Quality varies. |
| yt-dlp + Whisper local | CLI | Free | Best quality, runs locally, slower |
| OpenAI Whisper API | Yes | $0.006/min | Fast, high quality, cloud-based |
| Deepgram | Yes | $0.0043/min | Alternative, fast |

**B8. Error case:** Audio download fails → retry once, then mark as `transcription_failed`. Whisper timeout (very long video) → chunk into segments. Language detection wrong → allow manual language override.

**B9. Human time:** 2-5 minutes wait time (automated, but human waits).

---

### Step 3: Worksheet Generation

**B1. What the human does:** Read through the raw transcript. Identify every key point. Organize into hierarchy: main points → sub-points → supporting details → action items. Format into a clean, scannable document.

**B2. Input needed:** Raw transcript from Step 2. Video metadata from Step 1 (title, channel — gives context for what the video is about).

**B3. Decisions:**
- What are the key points vs. filler/tangents?
- How to group related points together?
- What level of detail for each sub-point?
- What's an action item vs. just information?

**B4. Could Claude decide?** Yes, with judgment guidance:
- "Good" worksheet = every substantive point captured, no filler, clear hierarchy
- Use the video title + channel as context for what matters
- Action items = anything the speaker says to DO (not just know)
- Group by topic/theme, not by timestamp order
- Capture specific numbers, names, tools, URLs mentioned

**B5. Output:** Structured worksheet document:
- Video summary (2-3 sentences)
- Key points (numbered, with sub-points)
- Action items (bulleted)
- Tools/resources mentioned (listed)
- Notable quotes (if any)
- Metadata (speaker, date, duration, source URL)

**B6. Output goes to:**
- [x] Into a database (update video record with worksheet content)
- [x] This is the END of Level 1. The worksheet becomes the INPUT for Level 2 filters.

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Claude Sonnet | Yes | ~$0.01-0.05 per transcript | Best quality for understanding + structuring |
| Claude Haiku | Yes | ~$0.001-0.005 per transcript | Cheaper, may miss nuance on complex topics |

**B8. Error case:** Transcript too long for context window → chunk into sections, generate worksheet per section, then merge. Transcript is nonsense (bad audio quality) → flag as `low_quality_transcript`, alert user.

**B9. Human time:** 15-30 minutes per video (the biggest bottleneck — this is where all the time goes).

---

## LEVEL 2 — FILTER PIPELINE (On Demand, Stackable)

> Level 2 is where the wizard needs to handle VARIABLE DEPTH. The user applies 0 to many filters per video. Each filter is independent. Filters can be applied now or later. Multiple videos can be combined through one filter. This is the multi-level test.

---

### Step 4: Filter Selection

**B1. What the human does:** Look at a processed video (transcript + worksheet) and decide what formats/outputs they want from it. Select one or more filters from a library of filter types. Optionally select a preset (pre-configured combination of filters).

**B2. Input needed:** The worksheet from Step 3. The library of available filters. Any existing presets.

**B3. Decisions:**
- Which filter(s) apply to this video? (Could be 1, could be 7)
- Use a preset or pick individually?
- Process this video alone, or combine it with other videos?
- Any custom instructions for this specific run? (e.g., "focus on the Claude Code parts, ignore the marketing stuff")

**B4. Could Claude decide?** Partially:
- [x] Yes, with judgment — Claude could SUGGEST which filters are relevant based on the worksheet content ("This video talks about building automation — Tool Extractor and Checklist filters would be useful")
- [ ] No, must stay human — the final selection is the user's call. They know what they need it for.

**B5. Output:** A filter job: list of selected filter IDs + video ID(s) + any custom instructions.

**B6. Output goes to:**
- [x] Into the next step (Step 5 processes each filter)
- [x] Into a database (filter_jobs table — tracks what was requested)

**B7. API tool:** No external API needed. This is UI/UX — a selection interface.

**B8. Error case:** No filters selected → prompt user to select at least one. Video not yet worksheeted → run Level 1 first automatically.

**B9. Human time:** 1-2 minutes (pick from a list, maybe add a note).

---

### Step 5: Filter Execution (REPEATS per filter selected)

**B1. What the human does:** Take the worksheet and manually reprocess it through a specific lens. Each filter type has a different output format:

**FILTER LIBRARY (known filter types so far):**

| Filter Name | What It Produces | When You'd Use It |
|---|---|---|
| **Tool Extractor** | Tool specification: inputs, outputs, logic, build instructions | "Everything in this video can be made into a tool" |
| **Checklist Builder** | Numbered action checklist with checkboxes | "I need the step-by-step to-do list from this" |
| **Skill Creator** | Claude Code skill file format (trigger, instructions, examples) | "This describes a skill I want to build" |
| **Step-by-Step Wizard** | Guided walkthrough format with decision points | "Walk me through this process interactively" |
| **Knowledge Base Entry** | Structured reference doc for a topic | "This is my truth for how X works" |
| **Automation Identifier** | List of processes that could be automated + how | "What from this video can I automate?" |
| **Comparison Matrix** | Side-by-side comparison of options/tools discussed | "Compare the approaches this video covers" |

> **This list grows over time.** New filter types can be added without changing the pipeline. That's the whole point — the ingest is fixed, the filters are extensible.

**B2. Input needed:** Worksheet from Step 3 (or multiple worksheets if combining videos). The specific filter's prompt template. Any custom instructions from Step 4.

**B3. Decisions:**
- How to apply this filter's lens to this specific content
- What to include vs. exclude based on the filter's purpose
- How to handle content that doesn't fit the filter cleanly (e.g., a video about philosophy run through Tool Extractor — not everything maps)

**B4. Could Claude decide?** Yes, with clear prompt templates per filter:
- Each filter type has a PROMPT TEMPLATE that defines exactly what to extract and how to format it
- Claude applies the template to the worksheet content
- No human judgment needed during execution — the judgment was in Step 4 (choosing the filter)

**B5. Output:** Filter-specific output document in the defined format for that filter type. Self-contained — readable and usable on its own without needing the original video.

**B6. Output goes to:**
- [x] Into a database (filter_outputs table — linked to video_id + filter_type)
- [x] Saved to a file (if user wants standalone export)
- [x] Into a software tool (if the filter output IS a tool/skill/automation — it feeds into AutoForge)

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Claude Sonnet | Yes | ~$0.01-0.05 per filter run | Best for complex filters (tool extractor, skill creator) |
| Claude Haiku | Yes | ~$0.001-0.005 per filter run | Good enough for simple filters (checklist, comparison) |

**B8. Error case:** Worksheet content doesn't fit the filter → produce partial output + note what couldn't be mapped. Claude output malformed → retry once with stricter formatting instructions. Content too long → chunk and process sections, then merge.

**B9. Human time:** 10-20 minutes per filter per video (when done manually — reading, extracting, reformatting).

---

### Step 6: Multi-Video Merge (Optional — when combining videos)

**B1. What the human does:** Select 2+ already-worksheeted videos. Run them through a single filter together. The filter processes all worksheets as one combined input and produces a unified output.

**B2. Input needed:** Multiple worksheets from Step 3. The selected filter type. Custom instructions about how to merge (e.g., "deduplicate overlapping points", "organize chronologically", "keep the latest version's info when they conflict").

**B3. Decisions:**
- Which videos to combine?
- How to handle overlapping/conflicting information?
- Which video's perspective takes priority if they disagree?

**B4. Could Claude decide?** Partially:
- [x] Yes, with rules — Claude can deduplicate, merge, and resolve simple conflicts
- [ ] No, must stay human — choosing WHICH videos to combine and the merge strategy

**B5. Output:** A single merged output document in the selected filter's format, synthesized from multiple source videos.

**B6. Output goes to:**
- [x] Into a database (filter_outputs table — linked to multiple video_ids)
- [x] Saved to a file

**B7. API tool:**

| Tool | API? | Cost | Notes |
|---|---|---|---|
| Claude Sonnet | Yes | ~$0.02-0.10 per merge | More content = more tokens. Sonnet handles synthesis better. |

**B8. Error case:** Combined worksheets exceed context window → summarize each worksheet first, then merge summaries. Conflicting information → flag conflicts, present both versions, let user resolve.

**B9. Human time:** 30-60 minutes (reading multiple docs, finding overlaps, merging manually).

---

## ARE THERE MORE LEVELS?

> **Framework question:** After Level 1 (Ingest) and Level 2 (Filter), is there a Level 3?

**Answer:** Not right now. But the architecture should allow it. Possible future levels:
- **Level 3: Publish** — take filter outputs and push them somewhere (create a skill file, add to knowledge base, publish as a doc, create a project card)
- **Level 3: Review** — human reviews filter outputs, approves/edits/rejects, feedback improves future filter runs

These aren't built today. The framework handles them by just adding more steps in Section B when they're needed. The 6-step pattern scales — each level is just another set of INPUT → PROCESS → OUTPUT.

---

## Section C: Operations Layer (Filled Out)

### State Tracking

**C1. Statuses per video:**
`captured → transcribing → transcribed → worksheeting → worksheeted → filters_pending → filters_complete`

Statuses per filter job:
`queued → processing → complete → failed → retrying`

**C2. Audit trail:**
- [x] Full audit trail (event log with timestamps)
- Need to know: when was this video transcribed, when was the worksheet generated, which filters were applied, when, by whom, what version of the filter prompt was used. Critical for going back and reprocessing with improved prompts.

**C3. Dedup:**
- Unique identifier = YouTube video URL (or video ID extracted from URL)
- Same video submitted twice → don't re-transcribe, just surface the existing record
- Same filter applied twice to same video → allow it (user might want to rerun with different instructions), but track as a new run linked to the same video

### Notifications

**C4. Who needs to know:**
- [x] Just me (solo operator)

**C5. What they need to know:**
- [x] "It ran successfully" — "Video transcribed and worksheeted: [title]"
- [x] "It failed" — "Transcription failed for [URL] — reason: [error]"
- [x] Summary stats — daily: "Processed 8 videos today. 23 filter outputs generated. 2 failed."
- [x] Individual item alerts — "Worksheet ready for: [title] — apply filters?"

**C6. How:**
- [x] Telegram (instant alerts when processing completes or fails)
- [x] Dashboard (ongoing visibility — list of all videos, their status, their filter outputs)

### Scheduling

**C7. When:**
- [x] When triggered by an event — user submits a URL, that triggers the ingest pipeline
- [x] Manually for now, automate later — batch mode: user can queue up 10 URLs at once and walk away
- Future: watch a YouTube channel or playlist and auto-ingest new videos

**C8. Failure recovery:**
- [x] Resume from where it left off — if transcription worked but worksheet failed, don't re-transcribe. Each step is independent and checkpointed.

**C9. Infrastructure:**
- [x] A cloud server / VPS — same server running AutoForge
- [x] Could also run locally — transcript + worksheet don't need 24/7 uptime since they're triggered on-demand

---

## Section D: Success Criteria (Filled Out)

**D1. Metrics:**

| Metric | Current (Manual) | Target (Automated) |
|---|---|---|
| Videos processed per day | 2-3 (limited by human time) | 10+ (all encountered videos) |
| Time per video (transcript + worksheet) | 20-40 minutes | < 2 minutes (fully automated) |
| Time per filter application | 10-20 minutes manual | < 30 seconds (automated) |
| Videos with filters applied | ~30% (too tedious to do for all) | 100% (at least 1 preset filter on every video) |
| Ability to retrieve past processed videos | Near zero (no organized storage) | 100% (database with search) |
| Ability to reprocess with new filter | Start over from scratch | Instant (worksheet already exists, just apply new filter) |

**D2. Human cost:**
- 3 videos/day x 40 min average = 2 hours/day = 10 hours/week = 40 hours/month
- At $50/hour = $2,000/month in time
- But the REAL cost is the 7 videos/day NOT getting processed — lost knowledge, lost tools, lost checklists

**D3. Budget:**
- [x] Free/minimal (< $50/month)
- Whisper API: ~$0.006/min x 10 videos x 15 min avg = ~$0.90/day = ~$27/month
- Claude for worksheets + filters: ~$0.05/video x 10 + $0.03/filter x 30 filters/day = ~$1.40/day = ~$42/month
- Total: ~$69/month

**D4. MVP step:**
- MVP = Step 2 (Transcription) + Step 3 (Worksheet Generation) — these are Level 1
- This alone saves 90% of the time. Even without filters, just having every video auto-transcribed into a readable worksheet is transformative.
- Level 2 filters are Phase 2 of the build — add them once the ingest pipeline is solid.

---

## The 6-Step Architecture Map

```
┌─────────────────────────────────────────────────────────────┐
│                    LEVEL 1 — INGEST                         │
│              (runs for every video, always)                  │
│                                                             │
│  SCHEDULE: Event-triggered (user submits URL)               │
│      │         OR batch queue (10 URLs at once)             │
│      ▼                                                      │
│  INPUT: YouTube URL                                         │
│      │  → YouTube API (metadata: title, channel, duration)  │
│      │  → yt-dlp (download audio)                           │
│      ▼                                                      │
│  PROCESS:                                                   │
│      Step 1 — Capture: extract metadata, create record      │
│      Step 2 — Transcribe: Whisper API → raw text            │
│      Step 3 — Worksheet: Claude Sonnet → structured doc     │
│      │                                                      │
│      ▼                                                      │
│  OUTPUT: Structured worksheet + raw transcript              │
│      │   stored in database, linked to video record         │
│      ▼                                                      │
│  STATE: Supabase tables:                                    │
│      - videos (id, url, title, channel, duration,           │
│        raw_transcript, worksheet, status, created_at)       │
│      - processing_events (video_id, step, status,           │
│        started_at, completed_at, error)                     │
│      │                                                      │
│      ▼                                                      │
│  NOTIFY: Telegram — "Worksheet ready: [title]"              │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │  worksheet feeds into Level 2
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    LEVEL 2 — FILTER                          │
│           (on-demand, 0-N filters per video)                 │
│                                                             │
│  SCHEDULE: Event-triggered (user selects filters)           │
│      │         OR preset auto-applied after ingest          │
│      ▼                                                      │
│  INPUT: Worksheet(s) from Level 1                           │
│      │  + Selected filter type(s)                           │
│      │  + Custom instructions (optional)                    │
│      │  + Multiple videos (optional — merge mode)           │
│      ▼                                                      │
│  PROCESS:                                                   │
│      Step 4 — Select: user picks filters (or preset fires)  │
│      Step 5 — Execute: Claude applies filter prompt          │
│               template to worksheet content                 │
│               (REPEATS for each selected filter)            │
│      Step 6 — Merge: (optional) combine multi-video         │
│               worksheets into single filter output          │
│      │                                                      │
│      ▼                                                      │
│  OUTPUT: Filter-specific documents                          │
│      │   (checklist, tool spec, skill file, etc.)           │
│      │   Each self-contained and independently useful       │
│      ▼                                                      │
│  STATE: Supabase tables:                                    │
│      - filter_types (id, name, prompt_template,             │
│        description, output_format)                          │
│      - filter_jobs (id, video_ids[], filter_type_id,        │
│        custom_instructions, status, created_at)             │
│      - filter_outputs (id, job_id, video_id,                │
│        filter_type_id, content, created_at)                 │
│      - presets (id, name, filter_type_ids[],                │
│        description, is_default)                             │
│      │                                                      │
│      ▼                                                      │
│  NOTIFY: Telegram — "3 filters complete for: [title]"       │
│          Dashboard — filter outputs viewable/searchable     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## What This Test Revealed About the Framework

### What worked:
1. **Section A captured the full picture** — even with two levels, the A2 walkthrough naturally separated into "always happens" and "on demand" phases
2. **Section B handled each step independently** — the per-step breakdown (B1-B9) worked for both mechanical steps (transcription) and judgment steps (filter execution)
3. **Section C (Operations) mapped cleanly** — state tracking, notifications, and scheduling all applied the same way to both levels
4. **Section D focused the MVP** — correctly identified that Level 1 alone is transformative, Level 2 is Phase 2

### What the framework needs to handle better (multi-level gaps):
1. **No explicit "how many levels?" question** — the wizard assumes a flat list of steps. It should ask: "Is this a single-pass process, or does it have distinct phases? Could someone use just Phase 1 without Phase 2?"
2. **No "dynamic/stackable step" concept** — Step 5 (Filter Execution) repeats N times based on user choice. The wizard's B section assumes each step runs once. Need a question like: "Does this step repeat? If so, what determines how many times?"
3. **No "extensible library" pattern** — the filter types are a growing list. The wizard doesn't ask: "Are the options in this step fixed, or do new options get added over time?"
4. **No "preset/template" concept** — combining multiple steps into a one-click preset isn't captured by the wizard. Need: "Are there common combinations of choices that should be saved as presets?"
5. **No "cross-item merge" concept** — Step 6 processes multiple videos through one filter. The wizard asks about one item at a time. Need: "Can multiple items be processed together as a batch through the same step?"

---

## Proof This Framework Works (With Gaps Identified)

We ran the wizard on a two-level system (Ingest → Filter) with dynamic, stackable second-level steps. The framework WORKED — we got a complete architecture from it. But we had to IMPROVISE to handle:

- Multi-level phasing (we added "Level 1" / "Level 2" headers ourselves)
- Repeating steps (we noted "REPEATS per filter" ourselves)
- Growing option libraries (we added a filter type table ourselves)
- Presets (we added preset logic ourselves)
- Multi-item merge (we added Step 6 ourselves)

**These 5 gaps should be added to the wizard questionnaire as optional questions** — they only apply when the process has these patterns, but when they DO apply, they're critical to capture. Without them, a naive wizard run would produce a flat pipeline that misses the system's real architecture.

**Next step:** Add these 5 questions to the wizard, then produce the CLAUDE.md build file for this system.
