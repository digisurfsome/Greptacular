# YT Strategy Lab: Discovery & Processing — Agent Brief

> AI-powered opportunity analysis and strategy extraction from YouTube video transcripts.

## What It Does

**Discovery:** Analyzes a video transcript to identify business opportunities, key insights, and actionable app ideas. Scores each opportunity 0-100 and recommends which to pursue first.

**Processing:** Takes a video transcript + user context and extracts a full strategy project with numbered steps, AI prompts, and expected outputs.

Both support SSE streaming for real-time progress logs.

## Files Involved

| File | Purpose |
|------|---------|
| `ui/src/components/yt-lab/DiscoveryPanel.tsx` (23KB) | UI — opportunity cards, score circles, type badges, expandable details |
| `ui/src/pages/YTStrategyLabPage.tsx` (89.7KB) | UI — main page with project list, strategy builder, step editor |
| `ui/src/lib/api.ts` | `discoverOpportunitiesStream()`, `processVideoStream()` |
| `ui/src/lib/types.ts` | `YTDiscoverResponse`, `YTAppOpportunity`, `YTKeyInsight`, `YTStrategyProject`, `YTStrategyStep` |
| `server/routers/yt_discovery.py` | Backend — discover and discover-stream endpoints |
| `server/routers/yt_processing.py` | Backend — process and process-stream endpoints |
| `server/services/yt_discovery.py` | YTDiscovery class — opportunity analysis AI service |
| `server/services/yt_processor.py` | YTProcessor class — strategy extraction AI service |

## Data Flow

```
Discovery:
  transcript + metadata → POST /api/yt-lab/discover-stream (SSE)
  → Claude analyzes → streams log entries → final YTDiscoverResponse

Processing:
  transcript + metadata + user_context → POST /api/yt-lab/process-stream (SSE)
  → Claude extracts strategy → streams progress → final project + steps
```

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/yt-lab/discover` | Synchronous discovery |
| POST | `/api/yt-lab/discover-stream` | SSE streaming discovery with progress logs |
| POST | `/api/yt-lab/process` | Synchronous processing |
| POST | `/api/yt-lab/process-stream` | SSE streaming processing with progress logs |

## Key Types

```typescript
interface YTAppOpportunity {
  name: string; type: 'companion'|'direct'|'derivative'|'teaching';
  one_liner: string; description: string; complexity: 1-5;
  score: 0-100; features: string[];
  why_this_works?: string; concerns?: string; strategic_value?: string;
}

interface YTStrategyProject {
  id: string; name: string; niche: string; description: string;
  status: 'draft'|'in-progress'|'complete'; tags: string[];
  steps: YTStrategyStep[];
}

interface YTStrategyStep {
  id: string; order: number; title: string; description: string;
  prompt: string; expectedOutput: string; notes: string;
  model: YTModelId; status: 'pending'|'in_progress'|'complete';
  subSteps: YTStrategySubStep[];
}
```

## SSE Streaming Pattern

Both discovery and processing use the same SSE pattern:
```typescript
// Client sends POST, receives SSE stream
// Events: { type: 'log', message: '...' }
//         { type: 'result', data: YTDiscoverResponse }
//         { type: 'error', message: '...' }
```

## Common Modifications

- **Change opportunity scoring:** `server/services/yt_discovery.py` (system prompt, scoring logic)
- **Add new opportunity fields:** `yt_discovery.py` (output schema) + `types.ts` (YTAppOpportunity) + `DiscoveryPanel.tsx`
- **Change strategy extraction:** `server/services/yt_processor.py` (system prompt, step structure)
- **Add new step fields:** `yt_processor.py` + `types.ts` (YTStrategyStep) + `YTStrategyLabPage.tsx`
