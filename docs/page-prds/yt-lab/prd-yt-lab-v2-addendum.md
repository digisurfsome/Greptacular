# PRD Addendum: YT Lab v2 — Filing System, Paste Input, Worksheet Mode, Bulk Fix

**Date:** 2026-04-15
**Builds on:** `docs/prd-yt-lab-v2.md` (Features 1-5), `docs/prd-yt-lab-tool-analyzer.md` (Phases 1-6)
**Priority:** HIGH — these are daily-use features for 3-5 video ingestions per day

---

## CONTEXT

The owner is ingesting 3-5 videos per day minimum, sometimes bulk runs of 50-70 URLs at once (e.g., all top videos on a new feature like Google Maps AI). The current YT Lab has NO filing system — everything is one giant list. Transcripts disappear after processing. There's no way to paste a transcript directly (needed for YouTube Lives where auto-transcript doesn't exist). The batch import UI exists and backend code looks functional but hasn't been verified end-to-end.

---

## FEATURE A: Filing System (Video Library)

### The Problem
Right now all processed videos are in one flat list. At 3-5 videos per day, that's 100+ videos per month with no way to find anything. Need folders, categories, search, and filters — similar to the Workspace library system.

### How It Works

**Folder Structure:**
```
📁 All Videos (default view)
📁 AI Automation
   📁 Claude Code Tutorials
   📁 Agent Building
   📁 Automation Workflows
📁 SEO
   📁 Google Maps AI (new)
   📁 Traditional SEO
📁 Marketing
   📁 GTM Strategies
   📁 Ad Creative
📁 Research Queue (unprocessed)
📁 Favorites
```

**Features:**
1. **Create/rename/delete folders** — drag-and-drop videos between folders
2. **Auto-categorize on ingest** — AI suggests a folder based on video title/content (user confirms or overrides)
3. **Tags** — each video can have multiple tags (already in BatchImportView but not used for filtering)
4. **Search** — full-text search across video titles, channels, transcripts, and worksheets
5. **Filters** — by folder, tag, date range, channel, processed/unprocessed status
6. **Sort** — by date added, date published, title, channel, duration
7. **Bulk select** — select multiple videos for move/tag/delete/re-process

### UI Layout
```
┌─────────────────────────────────────────────────────────────────────┐
│  YT STRATEGY LAB                                                    │
├────────────┬────────────────────────────────────────────────────────┤
│            │  🔍 Search...              [Filter ▼] [Sort ▼] [+New] │
│  FOLDERS   │                                                        │
│            │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│  📁 All    │  │ 🎬   │ │ 🎬   │ │ 🎬   │ │ 🎬   │ │ 🎬   │        │
│  📁 AI     │  │ thumb│ │ thumb│ │ thumb│ │ thumb│ │ thumb│        │
│    📁 Clau │  │      │ │      │ │      │ │      │ │      │        │
│    📁 Agent│  │Title │ │Title │ │Title │ │Title │ │Title │        │
│  📁 SEO    │  │Chan  │ │Chan  │ │Chan  │ │Chan  │ │Chan  │        │
│    📁 Maps │  │Tags  │ │Tags  │ │Tags  │ │Tags  │ │Tags  │        │
│  📁 Market │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘        │
│  📁 Queue  │                                                        │
│  📁 Favs   │  ┌──────┐ ┌──────┐ ┌──────┐                          │
│            │  │ 🎬   │ │ 🎬   │ │ 🎬   │                          │
│  ──────    │  │ ...  │ │ ...  │ │ ...  │                          │
│  + Folder  │  └──────┘ └──────┘ └──────┘                          │
│            │                                                        │
│            │  Showing 47 videos in "AI Automation"                  │
├────────────┴────────────────────────────────────────────────────────┤
│  [Batch Import]  [+ Paste Transcript]  [+ YouTube URL]              │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Model Additions
```python
# New table: yt_folders
class YTFolder:
    id: str           # UUID
    name: str         # Folder name
    parent_id: str    # Parent folder ID (nullable for root)
    icon: str         # Emoji icon (optional)
    sort_order: int   # Position in sidebar
    created_at: datetime

# Additions to existing video record:
class YTVideo:
    # ... existing fields ...
    folder_id: str           # Which folder this video lives in (nullable = root)
    tags: list[str]          # Tags for filtering
    is_favorite: bool        # Quick favorite toggle
    worksheet: str           # Auto-generated worksheet (persistent)
    worksheet_generated_at: datetime
```

### Implementation
- **Storage:** SQLite (same DB as workspace) — NOT localStorage
- **Folder CRUD:** New endpoints in `server/routers/yt_batch.py` or new `yt_library.py` router
- **Auto-categorize:** After video is ingested, Claude Haiku reads title + first 500 chars of transcript → suggests folder + tags. User sees suggestion, clicks to confirm or change.
- **Migrate existing videos:** On first load, all existing localStorage videos get imported into SQLite with folder_id = null (shows in "All Videos")

### Difficulty: 4/10
The Workspace library already has a folder/category system. Pattern exists — adapt it for YT Lab.

---

## FEATURE B: Paste Transcript Input

### The Problem
YouTube Lives don't have auto-generated transcripts accessible via yt-dlp or the YouTube API. The owner already has a local Whisper script that generates transcripts from any video. But there's no way to paste that transcript into YT Lab — it only accepts YouTube URLs.

Also useful for: podcast transcripts, conference talks, Zoom recordings, Twitter/X spaces, any non-YouTube source.

### How It Works

**New input mode alongside YouTube URL:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  ADD NEW VIDEO                                                       │
│                                                                       │
│  [🔗 YouTube URL]  [📋 Paste Transcript]  [📁 Upload File]         │
│                                                                       │
│  ─── Paste Transcript Mode ───                                       │
│                                                                       │
│  Title: ____________________________                                 │
│  Channel/Source: ____________________                                │
│  Duration (optional): _______________                                │
│  URL (optional): ____________________                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  Paste your transcript here...                                  │ │
│  │                                                                 │ │
│  │  (Accepts plain text, timestamped transcripts, SRT/VTT files)  │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Format detected: [Timestamped transcript]                            │
│  Word count: 48,230 words (~6 hours of content)                      │
│                                                                       │
│  [Process Now]                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

**Accepted formats:**
1. **Plain text** — just the words, no timestamps
2. **Timestamped transcript** — `[00:00:00] text here` or `00:00 - text here` (auto-detected, timestamps stripped for clean version, kept for raw version)
3. **SRT/VTT subtitles** — standard subtitle formats, parsed automatically
4. **File upload** — .txt, .srt, .vtt files dragged in or file-picker

**Processing flow:**
```
Pasted text → Auto-detect format → Strip timestamps → Save clean + raw versions
    → Feed into existing AI pipeline (game plan → tool ideas)
    → Same output as a YouTube URL, just different input source
```

### Backend
- New endpoint: `POST /api/yt-lab/ingest-transcript`
- Request body: `{ title, source, duration?, url?, transcript_text, format? }`
- Creates a video record with `source_type: "paste"` instead of `"youtube"`
- Skips the yt-dlp metadata fetch step — uses provided title/source
- Feeds transcript directly into the processing pipeline

### Difficulty: 2/10
The processing pipeline already accepts a transcript as input. This just adds a new entry point that skips the YouTube-specific ingestion step.

---

## FEATURE C: Auto-Worksheet Format

### The Problem
The v2 PRD describes "Game Plan Distillation" (Feature 2) which is close but not exactly what the owner wants. The owner wants a **worksheet** — structured, actionable, point-by-point — not a narrative summary. Think: study guide, not book report.

### What a Worksheet Looks Like

```markdown
# WORKSHEET: How to Build AI Agents with Claude Code
**Source:** Cody Schneider — 6h 51m
**Generated:** 2026-04-15

---

## Section 1: Environment Setup (0:00:00 - 0:45:00)

### Key Concepts
- Claude Code runs as a CLI tool, not just an API
- The CLAUDE.md file acts as persistent memory across sessions
- Environment variables go in .env, Claude reads them automatically

### Action Items
☐ Install Claude Code via `npm install -g @anthropic-ai/claude-code`
☐ Create project directory with .env file
☐ Create CLAUDE.md with company context, ICP, brand voice
☐ Test with simple prompt: "Read my CLAUDE.md and summarize my business"

### Tools Mentioned
- Claude Code (CLI)
- VS Code terminal
- Node.js / npm

### Exact Prompts Used
> "I am setting up a GTM automation workspace. Please help me create a .env template..."

### Pro Tips / Warnings
⚠️ Never put real API keys in CLAUDE.md — use .env for secrets
💡 Add a SKILL.md file for reusable instructions across sessions

---

## Section 2: ICP Research Pipeline (0:45:00 - 1:30:00)
...
```

### How It Differs From "Game Plan Distillation"

| Game Plan (v2 PRD) | Worksheet (this addendum) |
|-------------------|--------------------------|
| 3-7 key topics with summaries | Sections with timestamps + boundaries |
| Bullet points per topic | Checkboxes (action items) you can tick off |
| "Actionable takeaways" | Exact prompts, commands, and tool names verbatim |
| Good for overview | Good for following along step-by-step |
| AI-summarized narrative | Structured data extraction |

### The Prompt Difference

The Game Plan prompt says: "Summarize the key topics and create actionable takeaways."

The Worksheet prompt says: "Extract every actionable step, exact prompt, tool name, command, and setting mentioned. Format as a checkable worksheet with sections, action items, and verbatim quotes. Do NOT summarize — extract."

### Implementation
- Same pipeline as Game Plan, just a different system prompt
- Both versions should be generated: Game Plan (for quick reference) + Worksheet (for doing)
- Stored alongside transcript in DB
- Three tabs per video: **Transcript** | **Game Plan** | **Worksheet**

### Auto-Generation
When a video is processed, the worksheet should be generated automatically — not manually triggered. The flow:

```
Video ingested → Clean transcript saved → Game Plan generated → Worksheet generated
                                                                    ↓
                                                          Worksheet is PERSISTENT
                                                          Available every time you
                                                          come back to this video
```

### Difficulty: 2/10
Same infrastructure as Game Plan, just a different prompt and a third tab in the UI.

---

## FEATURE D: Bulk Import — Verify and Fix

### Current State
- **Frontend:** BatchImportView.tsx — fully built, 666 lines, multi-URL paste → preview cards → process all. Looks complete.
- **Backend:** yt_batch.py — fully coded, has ingest + process + status endpoints. Uses in-memory state (lost on server restart).
- **Verdict:** Code looks functional but needs end-to-end testing. Key risks:

### Known Issues to Verify
1. **In-memory state** — Batches stored in `_batches` dict. Server restart = all batch state gone. Need to persist to SQLite.
2. **Max 50 videos per batch** — Hardcoded limit in `BatchIngestRequest`. For 70-URL bulk runs, need to either raise this or auto-split into multiple batches.
3. **Sequential ingestion** — `_ingest_batch` processes videos one at a time. For 70 videos, this could take 30+ minutes just for metadata. Should run in parallel (5-10 concurrent).
4. **No folder assignment** — Batch import has no way to assign videos to a folder. After Feature A (filing system), batch import should let you pick a destination folder.
5. **No transcript paste in batch** — Batch mode only accepts YouTube URLs. Should also support pasting multiple transcripts.

### Fixes Needed
| Fix | Difficulty | Impact |
|-----|-----------|--------|
| Persist batch state to SQLite | 3/10 | Batches survive restart |
| Raise or remove 50-video limit | 1/10 | Support 70+ URL bulk runs |
| Parallel ingestion (5 concurrent) | 3/10 | 70 videos in ~10 min instead of 30+ |
| Add folder destination picker | 2/10 | Videos go to right folder immediately |
| Add transcript paste mode to batch | 2/10 | Bulk paste for non-YouTube sources |

### Difficulty: 3/10 total for all fixes

---

## IMPLEMENTATION PRIORITY (THESE 4 FEATURES)

```
1. Feature B: Paste Transcript Input (2/10)
   → Unblocks YouTube Lives immediately
   → Smallest change, biggest immediate value

2. Feature C: Auto-Worksheet Format (2/10)  
   → Adds the worksheet tab to every video
   → Just a different prompt + third tab

3. Feature A: Filing System (4/10)
   → Critical for organization as volume grows
   → Pattern exists from Workspace library

4. Feature D: Bulk Import Fixes (3/10)
   → Needed before the 70-URL runs
   → Mostly backend hardening
```

### How These Connect to the Existing v2 PRD

```
v2 PRD Phase 1 (Transcript Fix) ← DONE (already designed, just build it)
v2 PRD Phase 2 (Game Plan)      ← ENHANCED by Feature C (add Worksheet alongside)
v2 PRD Phase 3 (Multi-Video)    ← Needs Feature A (filing) to organize multi-video groups
v2 PRD Phase 4 (Tool Selection)  ← Independent, can be done anytime
v2 PRD Phase 5 (Discovery Feed) ← Needs Feature A (filing) first

This Addendum Feature A (Filing)      ← Build BEFORE v2 Phase 3
This Addendum Feature B (Paste Input) ← Build alongside v2 Phase 1
This Addendum Feature C (Worksheet)   ← Build alongside v2 Phase 2
This Addendum Feature D (Bulk Fix)    ← Build alongside v2 Phase 3
```

---

## DATA MIGRATION PLAN

Currently all YT Lab data is in **localStorage** (browser-only). All these features require **SQLite** (server-side). Migration plan:

1. Create SQLite tables: `yt_videos`, `yt_folders`, `yt_worksheets`, `yt_batches`
2. On first page load, detect localStorage data and offer "Import to database" button
3. Import creates records in SQLite, marks localStorage as "migrated"
4. All new features read/write to SQLite only
5. After successful migration, localStorage data can be cleared

This is the same migration pattern used by the Workspace chat (it went from localStorage → SQLite too).

### Difficulty: 3/10 (pattern already exists)

---

## FILES TO CREATE / MODIFY

### New Files
```
server/routers/yt_library.py              — Folder CRUD, search, filter endpoints
server/services/yt_library_service.py     — Filing system business logic
server/services/yt_worksheet_generator.py — Worksheet prompt + generation
ui/src/components/yt-lab/FolderSidebar.tsx — Folder tree sidebar
ui/src/components/yt-lab/VideoGrid.tsx     — Grid view of videos with search/filter
ui/src/components/yt-lab/PasteTranscriptModal.tsx — Paste transcript input
ui/src/components/yt-lab/WorksheetView.tsx — Worksheet tab renderer
```

### Modified Files
```
server/routers/yt_batch.py     — Persist state to SQLite, parallel ingestion, folder assignment
server/services/yt_processor.py — Add worksheet generation step after game plan
ui/src/pages/YTStrategyLabPage.tsx — New layout with folder sidebar + video grid
ui/src/components/yt-lab/BatchImportView.tsx — Add folder picker + transcript paste mode
ui/src/lib/api.ts              — New API functions for folders, search, paste
ui/src/lib/types.ts            — New types for folders, worksheets, paste input
```

---

## SUCCESS CRITERIA

1. **Filing:** Can create folders, drag videos between them, search across all videos, filter by tag/folder/date
2. **Paste:** Can paste a 250K character transcript, have it process identically to a YouTube URL input
3. **Worksheet:** Every processed video automatically gets a structured worksheet with action items, exact prompts, and tools — persistent across sessions
4. **Bulk:** Can paste 70 YouTube URLs, have them all process successfully with progress tracking, videos land in the right folder
