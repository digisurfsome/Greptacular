# YT Strategy Lab: Database Migration — Agent Brief

> Migration from localStorage to Supabase. Schema design, connection setup, and phased rollout.

## Current State

YT Lab projects are stored in **browser localStorage** only. This limits storage to ~5-10MB, is single-device, and can be wiped by clearing browser cache. Batch processing state lives **in-memory** on the server.

## Target State

All YT Lab data in **Supabase** (cloud PostgreSQL + auth + realtime + file storage).

## Connection Setup

### Python Backend
```bash
pip install supabase
```
```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# Then: supabase.table('videos').insert({...}).execute()
```

### React Frontend
```bash
npm install @supabase/supabase-js
```
```typescript
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
// Then: supabase.from('videos').insert({...})
```

### Environment Variables
```
SUPABASE_URL=https://xyzproject.supabase.co
SUPABASE_KEY=eyJ...  (service role key for backend)
SUPABASE_ANON_KEY=eyJ...  (anon key for frontend)
```

## Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| profiles | User accounts (extends Supabase Auth) | id, display_name, settings |
| videos | Ingested YouTube videos | video_id, title, channel, transcript (jsonb), extracted_urls |
| discoveries | AI opportunity analysis results | video_id, key_insights (jsonb), app_opportunities (jsonb), recommendation |
| projects | Strategy projects from processed videos | video_id, discovery_id, name, niche, status, tags, manifest |
| steps | Strategy steps within projects | project_id, order, title, prompt, expected_output, status |
| screenshots | Screenshot metadata (files in Supabase Storage) | video_id, storage_path, timestamp, ocr_text, classification |
| staging_queue | Knowledge Pipeline inbox | source_url, user_description, auto_tags, priority, status |
| creators | Tracked YouTube channels | channel_url, channel_name, videos_processed |
| creator_presets | Per-creator extraction profiles | channel_name, focus_areas, note_style, auto_context |
| auto_notes | Fast-pass notes before full processing | video_id, key_points (jsonb), tools_mentioned, verdict |
| tracked_channels | Channels monitored for new uploads | channel_url, last_checked_at, check_frequency |
| knowledge_tags | Cross-video topic tags | tag, category |
| step_tags | Links steps to knowledge tags | step_id, tag_id, confidence |
| topic_dives | Topic deep-dive sessions | topic, template, search_queries, categories |
| interest_profiles | User interest model for discovery feed | topics (jsonb), creators (jsonb), tools (jsonb) |

## Migration Strategy

### Phase 1: Dual-Write (No Breaking Changes)
- Backend writes to both localStorage (via API) and Supabase
- Frontend reads from Supabase, falls back to localStorage
- Existing data migrated on first Supabase connection

### Phase 2: Supabase Primary
- Frontend reads only from Supabase
- localStorage used as offline cache only
- Realtime subscriptions for cross-device sync

### Phase 3: localStorage Removed
- All data in Supabase
- Auth required for access
- RLS policies enforce per-user isolation

## Files That Change During Migration

| File | Change |
|------|--------|
| `ui/src/pages/YTStrategyLabPage.tsx` | Replace localStorage reads/writes with Supabase client calls |
| `ui/src/lib/api.ts` | Add Supabase client initialization + new data functions |
| `ui/src/lib/types.ts` | Add Supabase-specific types (may extend existing) |
| `server/routers/yt_ingestion.py` | Write ingest results to `videos` table |
| `server/routers/yt_discovery.py` | Write discovery results to `discoveries` table |
| `server/routers/yt_processing.py` | Write processed projects/steps to `projects` + `steps` tables |
| `server/routers/yt_batch.py` | Replace in-memory batch state with `staging_queue` table |
| New: `server/services/yt_supabase.py` | Supabase client wrapper for YT Lab |
| New: `ui/src/lib/supabase.ts` | Frontend Supabase client initialization |
| New: `ui/src/hooks/useYTLabData.ts` | React Query hooks for Supabase data |

## Common Modifications

- **Add a new table:** Create in Supabase dashboard → add to `yt_supabase.py` → add types → add hooks → add UI
- **Add a column:** Alter in Supabase dashboard → update service → update types → update UI
- **Add realtime subscription:** `supabase.channel('table').on('postgres_changes', ...).subscribe()`
