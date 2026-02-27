# PRD: Batch YouTube Video Import

## Overview
Allow users to paste multiple YouTube URLs at once, preview them all with thumbnails/titles, add context per video describing what to extract, then hit "Go" to process all videos into strategy projects on autopilot.

## Problem Statement
Currently, the system handles one video at a time. Users often have batches of 4-5+ videos queued up and want to set them all up, add context, and walk away while processing happens. They may be running errands or doing other work - the system should work autonomously once context is provided.

## User Flow

### Step 1: Paste URLs
- User navigates to YT Strategy Lab
- Clicks "Batch Import" button (or a dedicated import view)
- Pastes 1-N YouTube URLs into a text area (one per line, or comma-separated, or mixed)
- System parses and validates URLs, extracts video IDs
- Clicks "Fetch Previews"

### Step 2: Preview & Context
For each valid URL, the system fetches metadata and displays a card:
```
┌──────────────────────────────────────────────────┐
│ [Thumbnail]  Title: "How I Built an AI Agency"   │
│              Channel: WOP Academy                │
│              Duration: 10:09                     │
│              Published: Feb 2026                 │
│                                                  │
│  Context / Instructions:                         │
│  ┌──────────────────────────────────────────────┐│
│  │ I want to extract the step-by-step process   ││
│  │ he used to build the ad agency. Focus on     ││
│  │ the prompts and the order of operations.     ││
│  │ Also identify the computer-use tool...       ││
│  └──────────────────────────────────────────────┘│
│                                                  │
│  Niche/Tags: [AI Agency] [Car Dealerships]       │
│  ☐ Capture screenshots at key moments            │
│  Priority: [1] [2] [3] [4] [5]                  │
└──────────────────────────────────────────────────┘
```

### Step 3: Launch Processing
- User clicks "Process All" (or "Go")
- System queues all videos for processing in order of priority
- Processing happens sequentially (or optionally parallel)
- Progress bar shows overall completion
- Each video card updates with status: Queued → Processing → Complete

### Step 4: Results
- Each processed video becomes a new project in YT Strategy Lab
- Project is pre-populated with:
  - Video breakdown (section-by-section analysis)
  - Extracted steps
  - Draft prompt PRDs for each step
  - Notes and enhancements
- User returns to find all projects ready to review/refine

## Technical Requirements

### Frontend
- **BatchImportView** component in `ui/src/components/yt-lab/BatchImportView.tsx`
- URL parser that handles: youtube.com/watch?v=, youtu.be/, youtube.com/shorts/, mixed formats
- Metadata fetch for all URLs in parallel (using existing `/api/yt-lab/ingest` endpoint)
- Context textarea per video card
- Priority ordering (drag to reorder or number input)
- Progress tracking with WebSocket or polling
- "Process All" button that queues jobs

### Backend
- `POST /api/yt-lab/batch-ingest` - Accepts array of URLs with context
- `GET /api/yt-lab/batch-status/{batch_id}` - Returns progress of batch processing
- Background task queue (could use asyncio tasks, or simple SQLite queue)
- For each video in batch:
  1. Fetch transcript + metadata (existing ingestion)
  2. Send transcript + user context to AI model
  3. AI generates: breakdown, steps, prompt PRDs, notes
  4. Create project in localStorage (or future: database)
  5. Mark video as complete

### AI Processing Pipeline (per video)
The AI model receives:
- Full transcript
- User-provided context/instructions
- Description links and extracted content
- Screenshots (if enabled)

And produces:
- Section-by-section breakdown
- Numbered steps extracted from the content
- Draft prompts for each step
- Enhancement notes
- Niche identification

### Model Selection
- Default: Sonnet 4.6 (good balance of speed/quality for bulk processing)
- Option to upgrade to Opus 4.6 for higher-quality extraction
- Haiku 4.5 for metadata-only passes

## Input Variables
- `urls`: string[] - YouTube URLs
- `contexts`: Record<string, string> - Per-video context instructions
- `settings.captureScreenshots`: boolean
- `settings.model`: 'opus' | 'sonnet' | 'haiku'
- `settings.autoGenerateSteps`: boolean
- `settings.niche`: string (optional global niche)

## Success Criteria
- User can paste 5 URLs, add context to each, and walk away
- All 5 videos are processed into complete projects within 15-30 minutes
- Each project has meaningful steps, not just raw transcript dumps
- Context instructions are respected in the output
- No data loss if browser is closed during processing (queue persists)

## Dependencies
- Existing YouTube ingestion system (`/api/yt-lab/ingest`)
- AI model access (subscription-based, piped through AutoForge)
- WebSocket for progress updates (existing pattern in AutoForge)

## Future Enhancements
- Drag-and-drop URL reordering
- Template contexts (save reusable context instructions)
- Auto-detect video niche from title/description
- Cross-video deduplication (detect if same topic covered)
- Batch editing of generated projects
