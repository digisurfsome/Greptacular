# YT Strategy Lab: Ingestion — Agent Brief

> YouTube video import pipeline: URL → transcript, metadata, screenshots, extracted URLs.

## What It Does

Takes a YouTube URL, extracts the transcript via `youtube-transcript-api`, pulls metadata via `yt-dlp`, identifies screenshot-worthy moments via regex pattern matching, optionally captures frames with `ffmpeg`, and returns a structured response with all extracted data.

## Files Involved

| File | Purpose |
|------|---------|
| `ui/src/components/yt-lab/VideoIngestPanel.tsx` (17KB) | UI — URL input, progress steps, transcript preview |
| `ui/src/components/yt-lab/BatchImportView.tsx` (23KB) | UI — multi-URL batch import with per-video config |
| `ui/src/lib/api.ts` | `ingestYouTubeVideo()`, `batchIngestVideos()`, `getBatchStatus()` |
| `ui/src/lib/types.ts` | `YTIngestResponse`, `YTTranscriptSegment`, `YTScreenshotSuggestion`, `YTBatchVideoState` |
| `server/routers/yt_ingestion.py` (672 lines) | Backend — ingest endpoint, screenshot capture, URL extraction |
| `server/routers/yt_batch.py` | Backend — batch ingest/process/status endpoints |

## Data Flow

```
Single video:
  URL → POST /api/yt-lab/ingest → yt-dlp metadata + youtube-transcript-api → response

Batch:
  URLs[] → POST /api/yt-lab/batch/ingest → queued
  Poll GET /api/yt-lab/batch/status/{id} → per-video status
  POST /api/yt-lab/batch/process → triggers processing
```

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/yt-lab/ingest` | Single video ingest (url, captureScreenshots) |
| GET | `/api/yt-lab/health` | Check yt-dlp, ffmpeg, transcript API availability |
| POST | `/api/yt-lab/batch/ingest` | Queue batch of videos |
| POST | `/api/yt-lab/batch/process` | Trigger batch processing |
| GET | `/api/yt-lab/batch/status/{id}` | Poll batch progress |
| DELETE | `/api/yt-lab/screenshots` | Cleanup cached screenshots |
| GET | `/api/yt-lab/screenshots/{video_id}/{file}` | Serve screenshot file |

## Key Types

```typescript
interface YTIngestResponse {
  video_id: string; title: string; channel: string;
  duration: number; publish_date: string; thumbnail_url: string;
  description: string; transcript: YTTranscriptSegment[];
  extracted_urls: string[]; screenshot_suggestions: YTScreenshotSuggestion[];
  analyzed_screenshots: YTScreenshotCapture[]; screenshot_summary: string;
}
```

## Common Modifications

- **Add a new field to ingest response:** `yt_ingestion.py` (extraction logic) + `types.ts` (YTIngestResponse) + `VideoIngestPanel.tsx` (display)
- **Change screenshot logic:** `yt_ingestion.py` (visual cue patterns, frame extraction)
- **Add new batch field:** `yt_batch.py` + `types.ts` (YTBatchVideoInput) + `BatchImportView.tsx`
