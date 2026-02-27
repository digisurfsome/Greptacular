# YT Strategy Lab — Database Strategy

> **Status:** Ready to implement. This document covers the migration from localStorage to a real cloud database, with a phased approach that keeps the system working at every step.

---

## Why This Is Urgent

**Current state:** Everything lives in localStorage.

| Problem | Impact |
|---------|--------|
| **5-10MB browser limit** | At 500KB-1.5MB per project, you hit the wall at ~5-10 projects |
| **10+ videos/day target** | localStorage breaks within the first week |
| **Single browser = single device** | No mobile access, no cross-device sync |
| **Clear cache = lose everything** | One browser reset destroys all processed knowledge |
| **No knowledge merging** | Cross-video intelligence requires queryable, relational storage |
| **No staging queue** | The Knowledge Pipeline needs a persistent inbox |
| **No breakaway export** | Self-contained projects need server-side data, not browser-bound blobs |

**Bottom line:** localStorage was fine for prototyping. The system has outgrown it. Every major roadmap item (knowledge merging, staging queue, mobile app, breakaway architecture) requires a real database.

---

## The Recommendation: Supabase

### Why Supabase Over Neon

Both are excellent. Here's why Supabase wins for this system:

| Factor | Supabase | Neon |
|--------|----------|------|
| **Database** | Postgres (same as Neon) | Postgres |
| **Auth** | Built-in (email, OAuth, magic link) | None — BYO auth |
| **Realtime** | Built-in pub/sub (websocket) | None — BYO websocket |
| **Storage** | Built-in file storage (screenshots, exports) | None — need S3 separately |
| **Edge Functions** | Deno-based serverless functions | None |
| **Row Level Security** | Native Postgres RLS | Same (it's Postgres) |
| **Free tier** | 500MB DB, 1GB file storage, 50K monthly active users | 512MB storage, 0.25 compute units |
| **Pricing at scale** | $25/mo Pro (8GB DB, 100GB storage) | $19/mo Launch (10GB storage) |
| **Client SDK** | `@supabase/supabase-js` with auto-generated types | Raw SQL / Drizzle / Prisma |
| **Mobile ready** | Flutter SDK (`supabase_flutter`), React Native SDK | Raw HTTP/SQL only |

**The killer features for us:**
1. **Flutter SDK** — the mobile app connects directly, same auth, same realtime
2. **Built-in file storage** — screenshots and exports don't need a separate S3 bucket
3. **Realtime subscriptions** — when a video finishes processing on desktop, the mobile app knows instantly
4. **Auth** — multi-device access requires user accounts; Supabase auth is zero-config
5. **RLS** — each user's data is isolated at the database level, not application level

### When Neon Makes More Sense

If you decide later that you don't need auth, realtime, or file storage (unlikely given the roadmap), Neon gives you a cleaner Postgres-only experience with better cold-start performance and branching for development. It's the right pick for API-only backends. For this full-stack app with mobile, Supabase is the better fit.

---

## Database Schema

### Core Tables

```sql
-- Users (managed by Supabase Auth, this extends it)
create table profiles (
  id uuid references auth.users primary key,
  display_name text,
  settings jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- YouTube videos (one row per unique video, shared across projects)
create table videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  video_id text not null,          -- YouTube video ID (e.g., "dQw4w9WgXcQ")
  title text,
  channel text,
  duration integer,                -- seconds
  publish_date date,
  thumbnail_url text,
  description text,
  transcript jsonb,                -- array of {text, start, duration}
  extracted_urls text[],
  screenshot_suggestions jsonb,    -- array of {timestamp, reason}
  screenshot_summary text,
  raw_metadata jsonb,              -- full yt-dlp metadata for future use
  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(user_id, video_id)        -- one row per user per YouTube video
);

-- Discovery results (AI analysis of opportunities)
create table discoveries (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id) on delete cascade,
  user_id uuid references profiles(id) on delete cascade,
  video_context jsonb,             -- {speaker, core_topic, target_audience}
  key_insights jsonb,              -- array of insight objects
  app_opportunities jsonb,         -- array of opportunity objects
  recommendation jsonb,            -- {top_pick_index, reasoning, sequence, quick_win}
  model_used text,                 -- which Claude model produced this
  processing_time real,            -- seconds
  created_at timestamptz default now()
);

-- Projects (a processed video becomes a project with steps)
create table projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  video_id uuid references videos(id) on delete set null,
  discovery_id uuid references discoveries(id) on delete set null,
  name text not null,
  niche text,
  description text,
  tags text[],
  status text default 'draft',     -- draft, active, archived, exported
  selected_opportunity jsonb,       -- the chosen opportunity from discovery
  manifest jsonb,                  -- breakaway manifest (see VISION.md Rule 2)
  parent_project_id uuid references projects(id) on delete set null,  -- for sub-projects
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Strategy steps (the extracted workflow)
create table steps (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id) on delete cascade,
  "order" integer not null,
  title text not null,
  description text,
  prompt text,                     -- AI/computer-use prompt for this step
  expected_output text,
  notes text,
  model text,                      -- recommended model for execution
  status text default 'pending',   -- pending, in_progress, completed, skipped
  execution_result jsonb,          -- output from running this step
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Screenshots (stored in Supabase Storage, metadata here)
create table screenshots (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references videos(id) on delete cascade,
  storage_path text not null,       -- path in Supabase Storage bucket
  timestamp_sec real,
  reason text,
  ocr_text text,
  ui_detected boolean default false,
  classification text,
  relevance_score real,
  transcript_segment text,
  created_at timestamptz default now()
);

-- Knowledge tags (for cross-video merging — Roadmap Section 2)
create table knowledge_tags (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  tag text not null,                -- e.g., "lead-scraping", "email-enrichment"
  category text,                   -- e.g., "outreach", "research", "automation"
  created_at timestamptz default now(),

  unique(user_id, tag)
);

-- Step-to-tag mapping (which steps cover which knowledge areas)
create table step_tags (
  step_id uuid references steps(id) on delete cascade,
  tag_id uuid references knowledge_tags(id) on delete cascade,
  confidence real default 1.0,     -- AI's confidence this step covers this tag
  source_video_id uuid references videos(id),
  primary key (step_id, tag_id)
);

-- Staging queue (Knowledge Pipeline inbox — Roadmap Section 12)
create table staging_queue (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  source_type text not null,       -- 'video', 'manual', 'api', 'mobile_capture'
  source_url text,                 -- YouTube URL or other source
  source_metadata jsonb,           -- whatever context came with the submission
  user_description text,           -- what the user wants to extract
  auto_tags text[],                -- AI-assigned tags on intake
  auto_category text,              -- AI-assigned category
  priority integer default 0,     -- user can bump priority
  status text default 'queued',    -- queued, processing, routed, archived, failed
  routed_to uuid references projects(id),  -- where it ended up after processing
  error_message text,
  created_at timestamptz default now(),
  processed_at timestamptz
);

-- Creator tracking (Roadmap Section 3)
create table creators (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  channel_name text not null,
  channel_url text,
  specialty text[],                -- what they're known for
  trust_level integer default 3,   -- 1-5, how much you trust their advice
  notes text,
  video_count integer default 0,   -- how many of their videos you've processed
  created_at timestamptz default now(),

  unique(user_id, channel_name)
);

-- Link videos to creators
alter table videos add column creator_id uuid references creators(id) on delete set null;
```

### Row Level Security (RLS)

Every table gets the same pattern — users can only see their own data:

```sql
-- Enable RLS on all tables
alter table profiles enable row level security;
alter table videos enable row level security;
alter table discoveries enable row level security;
alter table projects enable row level security;
alter table steps enable row level security;
alter table screenshots enable row level security;
alter table knowledge_tags enable row level security;
alter table step_tags enable row level security;
alter table staging_queue enable row level security;
alter table creators enable row level security;

-- Policy pattern (repeat for each table)
create policy "Users see own data" on videos
  for all using (user_id = auth.uid());

create policy "Users see own data" on projects
  for all using (user_id = auth.uid());

-- Steps are accessed through project ownership
create policy "Users see own steps" on steps
  for all using (
    project_id in (select id from projects where user_id = auth.uid())
  );

-- Same pattern for screenshots through video ownership
create policy "Users see own screenshots" on screenshots
  for all using (
    video_id in (select id from videos where user_id = auth.uid())
  );
```

### Indexes

```sql
-- Fast lookups by user
create index idx_videos_user on videos(user_id);
create index idx_projects_user on projects(user_id);
create index idx_staging_user_status on staging_queue(user_id, status);

-- Fast lookups by video
create index idx_discoveries_video on discoveries(video_id);
create index idx_screenshots_video on screenshots(video_id);
create index idx_videos_youtube_id on videos(user_id, video_id);

-- Steps ordered within project
create index idx_steps_project_order on steps(project_id, "order");

-- Knowledge graph queries
create index idx_step_tags_tag on step_tags(tag_id);
create index idx_knowledge_tags_category on knowledge_tags(user_id, category);

-- Sub-project tree
create index idx_projects_parent on projects(parent_project_id);

-- Creator tracking
create index idx_videos_creator on videos(creator_id);
create index idx_creators_user on creators(user_id);
```

---

## Supabase Storage Buckets

```
yt-lab-screenshots/
  {user_id}/{video_id}/frame_{timestamp}.jpg

yt-lab-exports/
  {user_id}/{project_id}/export_{date}.zip    -- breakaway exports
```

Both buckets use RLS policies tied to user_id in the path.

---

## Migration Plan (3 Phases)

### Phase 1: Foundation (Days 1-3)

**Goal:** Supabase project running, schema deployed, client SDK wired in. Nothing migrated yet — localStorage still works.

**Steps:**
1. Create Supabase project at [supabase.com](https://supabase.com)
2. Run the schema SQL above in the SQL editor
3. Enable RLS on all tables
4. Create storage buckets with access policies
5. Install `@supabase/supabase-js` in the React app
6. Create `ui/src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'  // auto-generated

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
```

7. Generate TypeScript types: `npx supabase gen types typescript --project-id <id> > ui/src/lib/database.types.ts`
8. Add env vars to `.env` (not committed):
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

**Deliverable:** Supabase connected, types generated, no user-facing changes.

### Phase 2: Dual-Write (Days 4-7)

**Goal:** New data goes to both localStorage AND Supabase. Old data still reads from localStorage. Nothing breaks if Supabase is down.

**The pattern:**

```typescript
// Before (localStorage only)
const saveProject = (project: YTStrategyProject) => {
  const projects = loadProjects()
  projects.push(project)
  localStorage.setItem('yt-lab-projects', JSON.stringify(projects))
}

// After (dual-write)
const saveProject = async (project: YTStrategyProject) => {
  // Always write localStorage (instant, offline-safe)
  const projects = loadProjects()
  projects.push(project)
  localStorage.setItem('yt-lab-projects', JSON.stringify(projects))

  // Also write Supabase (async, best-effort)
  try {
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
      await supabase.from('projects').insert({
        user_id: user.id,
        name: project.name,
        niche: project.niche,
        description: project.description,
        tags: project.tags,
        status: project.status,
      })
    }
  } catch (err) {
    console.warn('Supabase write failed, localStorage still has it:', err)
  }
}
```

**Key principle:** localStorage is the primary during this phase. Supabase is the backup. If Supabase fails, nothing breaks.

**What gets dual-written:**
- New project creation → `projects` table
- Ingest results → `videos` table
- Discovery results → `discoveries` table
- Step extraction → `steps` table
- Screenshot metadata → `screenshots` table
- Screenshot files → Supabase Storage bucket

**Auth during this phase:**
- Add a simple "Sign in with Google" or magic link on the YT Lab page
- Anonymous users keep using localStorage only
- Signed-in users get dual-write
- No forced migration — gradual opt-in

**Deliverable:** All new data flows to Supabase. Old data still in localStorage. Users can sign in optionally.

### Phase 3: Supabase Primary (Days 8-14)

**Goal:** Supabase is the source of truth. localStorage becomes a cache/fallback only.

**Migration script (one-time):**

```typescript
async function migrateLocalStorageToSupabase(userId: string) {
  // 1. Migrate projects
  const projects = JSON.parse(localStorage.getItem('yt-lab-projects') || '[]')
  for (const project of projects) {
    const { data: dbProject } = await supabase
      .from('projects')
      .upsert({
        user_id: userId,
        name: project.name,
        niche: project.niche,
        description: project.description,
        tags: project.tags,
        status: project.status,
      })
      .select()
      .single()

    if (!dbProject) continue

    // 2. Migrate steps for this project
    const steps = JSON.parse(
      localStorage.getItem(`yt-lab-steps-${project.id}`) || '[]'
    )
    if (steps.length > 0) {
      await supabase.from('steps').insert(
        steps.map((s: any, i: number) => ({
          project_id: dbProject.id,
          order: s.order ?? i + 1,
          title: s.title,
          description: s.description,
          prompt: s.prompt,
          expected_output: s.expectedOutput,
          notes: s.notes,
          model: s.model,
          status: s.status || 'pending',
        }))
      )
    }

    // 3. Migrate ingest data
    const ingest = JSON.parse(
      localStorage.getItem(`yt-lab-ingest-${project.id}`) || 'null'
    )
    if (ingest) {
      await supabase.from('videos').upsert({
        user_id: userId,
        video_id: ingest.video_id,
        title: ingest.title,
        channel: ingest.channel,
        duration: ingest.duration,
        publish_date: ingest.publish_date,
        thumbnail_url: ingest.thumbnail_url,
        description: ingest.description,
        transcript: ingest.transcript,
        extracted_urls: ingest.extracted_urls,
        screenshot_suggestions: ingest.screenshot_suggestions,
        screenshot_summary: ingest.screenshot_summary,
      })
    }

    // 4. Migrate discovery data
    const discovery = JSON.parse(
      localStorage.getItem(`yt-lab-discovery-${project.id}`) || 'null'
    )
    if (discovery) {
      // Get the video DB id first
      const { data: videoRow } = await supabase
        .from('videos')
        .select('id')
        .eq('user_id', userId)
        .eq('video_id', ingest?.video_id)
        .single()

      if (videoRow) {
        await supabase.from('discoveries').insert({
          video_id: videoRow.id,
          user_id: userId,
          video_context: discovery.video_context,
          key_insights: discovery.key_insights,
          app_opportunities: discovery.app_opportunities,
          recommendation: discovery.recommendation,
        })
      }
    }
  }

  console.log(`Migrated ${projects.length} projects to Supabase`)
}
```

**Reading pattern flips:**

```typescript
// Before: localStorage primary
const projects = JSON.parse(localStorage.getItem('yt-lab-projects') || '[]')

// After: Supabase primary, localStorage fallback
const loadProjects = async (): Promise<YTStrategyProject[]> => {
  const { data: { user } } = await supabase.auth.getUser()

  if (user) {
    const { data, error } = await supabase
      .from('projects')
      .select('*, steps(*), videos(*)')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (!error && data) return data
  }

  // Fallback to localStorage (offline or not signed in)
  return JSON.parse(localStorage.getItem('yt-lab-projects') || '[]')
}
```

**Server-side changes:**
- Processing endpoints (`/api/yt-lab/process`, `/api/yt-lab/discover`) get optional `save_to_db=true` param
- When set, results are written to Supabase directly from the server (avoids large payloads going client → server → client → Supabase)
- Server uses Supabase service role key for direct DB writes

**Deliverable:** Supabase is primary. localStorage is offline cache. All data survives browser resets. Cross-device access works.

---

## Server-Side Supabase Integration

The Python backend also needs Supabase access for:
1. Writing processing results directly (avoid round-trip through client)
2. Staging queue management
3. Knowledge pipeline operations

```python
# server/services/supabase_client.py
import os
from supabase import create_client, Client

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")  # service role for server
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
    return create_client(url, key)
```

Add to requirements.txt:
```
supabase>=2.0.0
```

Add to `.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # NEVER expose this to the client
```

---

## Mobile Access (Flutter + Supabase)

Once Supabase is running, mobile access is straightforward:

```dart
// Flutter app
import 'package:supabase_flutter/supabase_flutter.dart';

await Supabase.initialize(
  url: 'https://your-project.supabase.co',
  anonKey: 'eyJ...',
);

final supabase = Supabase.instance.client;

// Sign in (same account as web)
await supabase.auth.signInWithOAuth(OAuthProvider.google);

// Load projects (same data as web — it's the same DB)
final projects = await supabase
    .from('projects')
    .select()
    .order('created_at', ascending: false);

// Realtime: get notified when desktop finishes processing
supabase
    .channel('staging_queue')
    .onPostgresChanges(
      event: PostgresChangeEvent.insert,
      schema: 'public',
      table: 'staging_queue',
      filter: PostgresChangeFilter(
        type: PostgresChangeFilterType.eq,
        column: 'user_id',
        value: supabase.auth.currentUser!.id,
      ),
      callback: (payload) {
        // Show notification: "New video queued for processing"
      },
    )
    .subscribe();
```

**The key point:** The mobile app doesn't need its own backend. It talks directly to Supabase, same as the web app. Same auth, same data, same realtime. The only thing the mobile app CAN'T do is run AI processing (that requires the Claude CLI on the user's computer). Mobile is for:
- Queuing videos to the staging queue (capture URLs on the go)
- Reviewing processed results
- Managing projects and steps
- Getting notifications when processing completes
- Quick capture (URL + description → staging queue)

AI processing still happens on the desktop where Claude CLI runs.

---

## Cost Estimate

### Free Tier (Good for getting started)

| Resource | Limit | Our Usage |
|----------|-------|-----------|
| Database | 500MB | ~50-100 projects worth of data |
| File Storage | 1GB | ~500-1000 screenshot sets |
| Auth | 50K MAU | Way more than needed |
| Realtime | 200 concurrent | Way more than needed |
| Edge Functions | 500K invocations/mo | Not needed initially |

**Free tier handles the first few months easily.**

### Pro Tier ($25/mo — when you need it)

| Resource | Limit |
|----------|-------|
| Database | 8GB |
| File Storage | 100GB |
| Auth | Unlimited |
| Daily backups | 7 days |
| No pausing | (free tier pauses after 1 week inactive) |

**Trigger for upgrade:** When you hit 500MB of data or need the project to stay online 24/7 (no auto-pause).

---

## What This Enables on the Roadmap

| Roadmap Item | localStorage | Supabase |
|-------------|-------------|----------|
| Discovery persistence | Works (just added) | Better — server-side, never lost |
| Cross-video knowledge merging | Impossible | SQL joins across videos/tags |
| Creator intelligence | Impossible | `creators` table + video aggregation |
| Smart tagging | Impossible | `knowledge_tags` + `step_tags` |
| Front page categories | Limited | `GROUP BY` on tags/categories |
| Mobile capture | Impossible | Direct Supabase insert from Flutter |
| Knowledge Pipeline | Impossible | `staging_queue` table + realtime |
| Staging queue | Impossible | Persistent queue with status tracking |
| Breakaway export | Messy | Clean project query + file storage |
| Mastermind Advisory Panel | Possible but fragile | Persistent advisor context per project |
| 10+ videos/day scale | Breaks | No limit |

---

## Implementation Priority

```
Week 1:  Phase 1 (Supabase project + schema + SDK setup)
         Phase 2 start (dual-write for new projects)

Week 2:  Phase 2 complete (all data dual-writing)
         Phase 3 start (migration script, Supabase primary reads)

Week 3:  Phase 3 complete (localStorage → cache only)
         Server-side Supabase writes for processing endpoints
         Staging queue operational

Week 4:  Flutter mobile app (quick capture + review)
         Realtime notifications
         Knowledge tagging on ingest
```

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database provider | Supabase over Neon | Built-in auth, storage, realtime, Flutter SDK — all needed for roadmap |
| Migration approach | Dual-write then flip | Zero downtime, no data loss, easy rollback |
| Auth method | Supabase Auth (Google OAuth) | Zero-config, same identity across web + mobile |
| Screenshot storage | Supabase Storage over S3 | Integrated with auth/RLS, simpler setup |
| Server-side writes | Service role key | Avoids large payload round-trips through the client |
| localStorage fate | Keep as offline cache | Graceful degradation when offline or not signed in |

---

## TL;DR

**Supabase. 3-phase migration. 4 weeks to full stack.**

Phase 1: Wire up Supabase (days 1-3). Phase 2: Dual-write new data to both localStorage and Supabase (days 4-7). Phase 3: Flip reads to Supabase, migrate old data, localStorage becomes offline cache (days 8-14). Then: Flutter mobile app talks directly to Supabase, staging queue goes live, knowledge merging becomes possible.

Free tier handles months of usage. $25/mo Pro when you scale. Every roadmap item that was impossible with localStorage becomes trivial with Supabase.
