# Video Factory — Internal Dashboard PRD

> Full Agent OS PRD for the Video Factory dashboard. Internal tool, solo operator, zero SaaS wiring for v1.
> Path: `docs/page-prds/video-factory/README.md`
> Status: Draft v1 — 2026-04-23

---

## Why This Exists

Owner needs ONE place to run the video factory:
- Render Chaos Engine commercials (template-based, slot-variation, per-business)
- Render Loom audit videos (screen-record + TTS, per-business)
- Manage the business-data pool from existing scrapers
- Track outreach campaigns + reply rates
- Hand finished MP4s to Mixpost for distribution
- Host per-business landing pages
- Operate everything from a browser — no CLI fiddling

Currently everything is CLI + folder spelunking. Dashboard = the roof over all of it.

---

## Decisions Locked

| # | Decision | Why |
|---|----------|-----|
| 1 | **E: drive = system of record.** All templates, assets, renders, DB, logs, caches live on external drive. | C: drive full, E: has 200 GB, keeps host PC clean. |
| 2 | **SQLite DB on E:** (`E:\VideoFactory\db\factory.sqlite`) | Zero-config, zero-ops, file-based, perfect for single-user. |
| 3 | **NO Supabase wiring v1.** Boilerplate shell kept intact but auth/DB/Stripe features dormant. | Least work now. Future SaaS flip = re-enable the already-built code. |
| 4 | **NO Stripe wiring v1.** Same reason. | |
| 5 | **Auth = hardcoded env vars.** Single user, `FACTORY_USER` + `FACTORY_PASS` in `.env`. | No user management overhead. You're the only operator. |
| 6 | **Templates authored by Claude in code files on disk.** | Owner is not a coder. Claude ships templates in ~30 min each. In-dashboard builder = later. |
| 7 | **Dashboard exposes RENDER controls only** (pick template, pick biz, toggle slot variations, render). Template AUTHORING happens outside dashboard. | Separation of concerns. You tell me what template to build → I build it as code → it shows up in dashboard. |
| 8 | **Render worker lives on E:** in Python. Dashboard queues jobs via SQLite rows. Worker polls queue. | No Redis, no RabbitMQ, no infra. SQLite = queue + state + history. |
| 9 | **Housed in user's existing SaaS boilerplate.** Not AutoForge. Separate project dir. | Already built. Future SaaS = zero-migration flip. |
| 10 | **Pages designed software-tight** (Linear/Vercel/Notion dashboard style). Sidebar + content. Tables. Keyboard-first. | Owner hates sloppy blog-style layouts. |

---

## Agent OS Structure

Per agent-os framework — 3 layers.

---

# LAYER 1 — STANDARDS

## 1.1 Stack

| Layer | Tech | Notes |
|-------|------|-------|
| Dashboard shell | User's existing Supabase SaaS boilerplate (Next.js assumed — confirm when boilerplate shared) | Keep layout + component library. Strip Supabase calls v1. |
| DB | SQLite on E: via `better-sqlite3` (Node) or `sqlite3` (Python worker) | Single file: `E:\VideoFactory\db\factory.sqlite` |
| Render worker | Python 3.13 daemon on E: | Polls SQLite queue, dispatches to hyperframes / loom pipeline. |
| Auth | Hardcoded env creds + cookie session | Replace w/ Supabase Auth when SaaS-ing. |
| Storage | E:\VideoFactory\assets\ | Renders, template assets, biz photos, landing pages. |
| External services | Mixpost (already planned, Hetzner), Cloudflare R2 (optional CDN for landing pages — later) | Dashboard calls Mixpost API only. |
| Charts / UI | Whatever boilerplate ships w/ (shadcn/ui likely). No new dep unless needed. | |

## 1.2 E: Drive Layout

```
E:\VideoFactory\
├── app\                         (Next.js dashboard code — from boilerplate)
├── worker\                      (Python render worker service)
│   ├── orchestrator.py          (main queue poller)
│   ├── pipelines\
│   │   ├── commercial.py        (Chaos Engine runner)
│   │   ├── loom.py              (screen-record + TTS runner)
│   │   └── base.py              (shared: slot-pick, data-inject, ffmpeg wrapper)
│   ├── tools\                   (one file per integrated tool — sandboxed)
│   │   ├── hyperframes_runner.py
│   │   ├── playwright_runner.py
│   │   ├── edge_tts.py
│   │   ├── kokoro_tts.py
│   │   ├── xtts.py
│   │   └── mixpost_client.py
│   └── requirements.txt
├── templates\                   (CODE templates Claude authors)
│   ├── commercials\
│   │   ├── plumber-chaos-v1\
│   │   │   ├── template.yaml     (metadata + slot variation libraries)
│   │   │   ├── beat-01-intro.html
│   │   │   ├── beat-02-problem.html
│   │   │   ├── beat-03-slot.html
│   │   │   ├── beat-04-destruction.html
│   │   │   ├── beat-05-cta.html
│   │   │   └── assets\           (logos, icons, sfx specific to this template)
│   │   └── hvac-chaos-v1\
│   └── loom\
│       ├── plumber-seo-audit-v1\
│       │   ├── template.yaml
│       │   ├── script-generator.py    (builds script from biz data)
│       │   ├── beats.json             (timing + actions)
│       │   └── overlays\              (hyperframes cards rendered over browser capture)
│       └── hvac-seo-audit-v1\
├── assets\                      (shared across all templates)
│   ├── fonts\
│   ├── music\
│   ├── sfx\
│   ├── stock-footage\           (free-commercial-use b-roll)
│   └── characters\              (Fixer, villains — PNG/SVG)
├── businesses\                  (scraped biz data — 1 folder per biz)
│   └── {biz_id}\
│       ├── profile.json         (name, phone, site, GBP URL, SEO rank, competitors, etc)
│       ├── logo.png
│       ├── screenshots\         (cached Playwright captures)
│       └── renders\             (this biz's finished MP4s)
├── renders\                     (global render archive, symlinks back to biz folders)
├── landing-pages\               (static HTML per biz, served by Next.js public route)
├── db\
│   ├── factory.sqlite
│   └── factory.sqlite.backup-YYYY-MM-DD  (daily snapshot)
├── logs\
│   ├── worker-YYYY-MM-DD.log
│   └── render-errors\
├── cache\                       (whisper models, kokoro models, playwright browsers)
└── .env                         (secrets — never commit)
```

## 1.3 Tool Sandboxing (carried from loom doc §16)

Every pipeline file declares allowed tools:

```python
# worker/pipelines/commercial.py
ALLOWED_TOOLS = ['hyperframes', 'ffmpeg', 'edge_tts', 'kokoro_tts']
DENIED_TOOLS = ['playwright', 'browser_use']  # commercials don't browse
```

Runner refuses imports outside the whitelist. Enforced at module load.

## 1.4 Coding Conventions

- Python: PEP8, type hints, f-strings, `pathlib` over string paths
- Next.js: TS strict, server components by default, client components marked
- SQL: explicit column lists, no `SELECT *` in app code
- File naming: `kebab-case.ext` always
- No secrets in code — `.env` only
- Every write to E: goes through a path helper (`e_path("templates", template_id)`) so paths aren't scattered

## 1.5 UI Design Standards

Pages must look like Linear / Vercel / Notion. NOT like a blog or WordPress admin.

- **Layout:** Fixed left sidebar (60-240px collapsible), top breadcrumb bar (40px), content fills rest.
- **Spacing:** Tight. 12px gutters, not 32px. Software density, not marketing density.
- **Tables over cards** for lists. Cards only for dashboard summaries.
- **Keyboard-first.** `cmd+k` search, `j/k` row nav, `enter` to open, `/` focus search.
- **Mono font** for IDs, file paths, token counts, numbers.
- **Dark mode default.** Light mode toggle.
- **Color:** neutral grayscale + ONE accent color for primary actions. No rainbow.
- **Status indicators:** dot (green/yellow/red/gray) + text. Not giant pills.
- **Empty states:** single centered sentence + one button. Not illustrations.
- **Loading:** skeleton rows, not spinners (except first-paint).

## 1.6 Data Model (SQLite)

```sql
-- businesses from scraper
CREATE TABLE businesses (
  id              TEXT PRIMARY KEY,        -- slug, e.g. 'joes-plumbing-denver'
  name            TEXT NOT NULL,
  industry        TEXT,                    -- 'plumber', 'hvac', ...
  phone           TEXT,
  email           TEXT,
  website         TEXT,
  gbp_url         TEXT,
  city            TEXT,
  state           TEXT,
  seo_rank        INTEGER,
  keyword_tracked TEXT,
  competitors     TEXT,                    -- JSON array
  scraped_at      TEXT NOT NULL,
  profile_path    TEXT NOT NULL,           -- relative path under businesses\
  outreach_status TEXT DEFAULT 'untouched' -- untouched|sent|replied|closed|dead
);

-- templates registered on disk
CREATE TABLE templates (
  id              TEXT PRIMARY KEY,        -- 'plumber-chaos-v1'
  family          TEXT NOT NULL,           -- 'commercial' | 'loom'
  industry        TEXT,
  name            TEXT NOT NULL,
  version         TEXT,
  path            TEXT NOT NULL,           -- E:\VideoFactory\templates\commercials\plumber-chaos-v1
  slot_count      INTEGER,                 -- total variation combos
  preview_mp4     TEXT,
  status          TEXT DEFAULT 'draft',    -- draft|ready|deprecated
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

-- render jobs (queue + history)
CREATE TABLE renders (
  id              TEXT PRIMARY KEY,
  template_id     TEXT NOT NULL REFERENCES templates(id),
  business_id     TEXT REFERENCES businesses(id),     -- null for test renders
  slot_selections TEXT,                                -- JSON: which variation per slot
  voice_engine    TEXT,                                -- 'edge' | 'kokoro' | 'xtts'
  status          TEXT NOT NULL,                       -- queued|running|done|failed|cancelled
  queued_at       TEXT NOT NULL,
  started_at      TEXT,
  finished_at     TEXT,
  output_path     TEXT,
  duration_ms     INTEGER,
  error           TEXT,
  logs_path       TEXT
);

-- campaigns = batch outreach runs
CREATE TABLE campaigns (
  id              TEXT PRIMARY KEY,
  name            TEXT,
  template_id     TEXT NOT NULL REFERENCES templates(id),
  created_at      TEXT NOT NULL,
  status          TEXT DEFAULT 'draft',    -- draft|running|paused|done
  biz_count       INTEGER,
  render_count    INTEGER,
  send_count      INTEGER,
  reply_count     INTEGER
);

CREATE TABLE campaign_renders (
  campaign_id     TEXT NOT NULL REFERENCES campaigns(id),
  render_id       TEXT NOT NULL REFERENCES renders(id),
  outreach_sent   TEXT,                    -- timestamp
  outreach_channel TEXT,                   -- gsa|email|dm|manual
  landing_url     TEXT,
  landing_views   INTEGER DEFAULT 0,
  replied         INTEGER DEFAULT 0,
  PRIMARY KEY (campaign_id, render_id)
);

-- mixpost connections per biz
CREATE TABLE posting_accounts (
  biz_id          TEXT NOT NULL REFERENCES businesses(id),
  platform        TEXT NOT NULL,           -- facebook|instagram|tiktok|...
  mixpost_ws_id   TEXT NOT NULL,
  mixpost_acct_id TEXT NOT NULL,
  connected_at    TEXT NOT NULL,
  PRIMARY KEY (biz_id, platform)
);

CREATE TABLE scheduled_posts (
  id              TEXT PRIMARY KEY,
  render_id       TEXT NOT NULL REFERENCES renders(id),
  biz_id          TEXT NOT NULL REFERENCES businesses(id),
  platforms       TEXT NOT NULL,           -- JSON array
  caption         TEXT,
  scheduled_at    TEXT NOT NULL,
  mixpost_post_id TEXT,
  status          TEXT DEFAULT 'pending'   -- pending|posted|failed
);

-- system settings (single row)
CREATE TABLE settings (
  key             TEXT PRIMARY KEY,
  value           TEXT
);
```

---

# LAYER 2 — PRODUCT

## 2.1 Vision

One dashboard. Five minutes from "just scraped a new plumber" to "MP4 rendered + landing page live + outreach queued." No terminal. No file explorer. No thinking about which folder anything lives in.

## 2.2 User (exactly one)

Owner. Solo operator. Non-coder. Fast-moving. Hates friction. Hates blogs. Loves keyboard shortcuts. Loves Claude doing the heavy lift.

## 2.3 Use Cases

| # | Use Case | Frequency |
|---|----------|-----------|
| U1 | "Render one test commercial for ONE plumber to see if the template looks good" | Daily during template iteration |
| U2 | "Render one loom audit video for ONE plumber" | Daily |
| U3 | "Batch render 100 loom videos — one per plumber in my scrape list" | Weekly campaign |
| U4 | "Preview a finished video before sending" | Every render |
| U5 | "See which videos got replies, which didn't" | Weekly |
| U6 | "Tell Claude to build a new template (HVAC chaos engine)" → template appears in dashboard | Monthly |
| U7 | "Regenerate just ONE beat because the joke fell flat" | During iteration |
| U8 | "Push a finished video to Mixpost for this biz's social accounts" | Per-client, post-launch |
| U9 | "Send the per-biz landing page URL via GSA" | Per campaign |
| U10 | "Check render worker status + queue depth + today's cost" | Occasionally |

## 2.4 Non-Goals (Explicitly Out of Scope for v1)

- Public SaaS. Not now.
- Multi-user / team / permissions. One operator.
- In-browser template authoring. Claude writes templates as code files.
- Drag-drop timeline editor. Hyperframes already has one at localhost:3000 during iteration — fine.
- Mobile UI. Desktop only.
- AI script generation in-dashboard. Scripts generated by worker calling Haiku API; dashboard only shows results.
- Video hosting for third-party playback. Cloudflare R2 — later.
- Analytics beyond "did they reply." Later.

## 2.5 Roadmap

### Phase 1 — Skeleton (internal, v0.1)
Boilerplate stripped + pages mocked + DB wired + worker polling. Render ONE hardcoded template for ONE biz via CLI, watch it land in the dashboard.

### Phase 2 — Full Internal Tool (v1.0, ship target)
All 9 pages functional. One commercial template (plumber-chaos-v1) working end-to-end. One loom template (plumber-seo-audit-v1) working end-to-end. Batch campaigns. Mixpost bridge. Landing pages.

### Phase 3 — Template Library Growth (v1.x)
Claude ships 2-3 new templates per week. Dashboard gets filtering, preview reels, slot-variation UI polish.

### Phase 4 — SaaS Flip (separate PRD, later)
Re-enable Supabase auth + Stripe. Multi-tenant schema migration. Onboarding flow. Pricing page. Public launch.

## 2.6 Success Metrics (Phase 2 ship)

| Metric | Target |
|--------|--------|
| Time from "new biz in scraper" → "finished MP4" | < 5 min |
| Batch render 100 looms | < 2 hours wall time on your PC |
| Failed render rate | < 5% |
| Claude ship time for new template | < 45 min |
| Dashboard uptime | As long as PC + E: drive on |

## 2.7 Future SaaS Migration Path

Every v1 decision chosen so SaaS flip is a ~3 day job later:
- Boilerplate shell kept intact → Supabase re-enable = flip env flags
- SQLite → Postgres migration = script we write once, schema is compatible
- Single-user env-var auth → Supabase Auth = replace auth middleware
- E: drive → R2/S3 = swap storage adapter
- Stripe routes kept stubbed → un-stub

---

# LAYER 3 — SPECS

Each spec = one page or one service. Self-contained.

---

## SPEC-D1 — Boilerplate Integration

**Purpose:** Get user's existing Next.js + Supabase + Stripe boilerplate running on E: drive w/ Supabase/Stripe neutered.

**Input needed from user:** boilerplate repo URL or zip

**Work:**
1. Clone boilerplate → `E:\VideoFactory\app\`
2. Install deps w/ `npm install` from E:
3. Create `E:\VideoFactory\.env` with:
   - `FACTORY_USER` + `FACTORY_PASS` (auth)
   - `DATABASE_PATH` → `E:\VideoFactory\db\factory.sqlite`
   - `SUPABASE_*` → blank (disables Supabase)
   - `STRIPE_*` → blank (disables Stripe)
   - `MIXPOST_URL` + `MIXPOST_TOKEN` (for later)
4. Patch auth middleware: use env creds + cookie session instead of Supabase when `SUPABASE_URL` is blank
5. Stub out Stripe routes — return 404 if `STRIPE_*` blank
6. Replace landing/marketing pages w/ redirect to `/dashboard`
7. Wire SQLite client (`better-sqlite3`)
8. Migration script: `npm run db:migrate` creates all tables from §1.6

**Tokens:** ~80k. **Time:** ~5 min gen + 15 min user setup.

---

## SPEC-D2 — Page: Videos (Default Landing)

**Route:** `/dashboard` (default after login)
**Purpose:** At-a-glance factory status + most recent renders.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Video Factory]                                     [⌘K]  [●] [settings ⚙] │
├────────────┬───────────────────────────────────────────────────────────────┤
│ ▸ Videos   │  Videos                                    [+ New Render]     │
│   Templates│  ──────────────────────────────────────────────────────────   │
│   Loom     │                                                                │
│   Business │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│   Campaign │  │ IN QUEUE   │ │ RENDERING  │ │ DONE TODAY │ │ FAILED     │ │
│   Posting  │  │    12      │ │     3      │ │    47      │ │    2       │ │
│   Pages    │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
│   Admin    │                                                                │
│            │  [All] [Queued] [Running] [Done] [Failed]     Search: [____]  │
│            │  ┌──────────────────────────────────────────────────────────┐│
│            │  │ Status  Template         Business          Dur   Started ││
│            │  ├──────────────────────────────────────────────────────────┤│
│            │  │ ●      plumber-chaos-v1  joes-plumbing    00:32  2m ago  ││
│            │  │ ●      seo-audit-v1      ace-hvac         03:14  5m ago  ││
│            │  │ ◐      seo-audit-v1      pipe-masters     ....   12m ago ││
│            │  │ ○      plumber-chaos-v1  draintech         —    queued   ││
│            │  │ ○      seo-audit-v1      rooter-kings      —    queued   ││
│            │  │ ✗      plumber-chaos-v1  leaky-bros         —   failed   ││
│            │  └──────────────────────────────────────────────────────────┘│
│            │                                                                │
│            │  Worker: running • Queue depth: 12 • Cost today: $0.34        │
└────────────┴───────────────────────────────────────────────────────────────┘
```

### Behavior
- Row click → opens video detail drawer (right-side slide-in) w/ preview + metadata + actions (download, retry, delete, send to Mixpost)
- `[+ New Render]` → modal: pick template → pick biz → pick slot variations → queue
- Status dots: `●` done (green), `◐` running (amber), `○` queued (gray), `✗` failed (red)
- Polls every 3s while any row is running

**Tokens:** ~60k. **Time:** ~3.5 min.

---

## SPEC-D3 — Page: Templates

**Route:** `/dashboard/templates`
**Purpose:** Browse available templates. View details. Kick off a render.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Templates                                                                   │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Family: [All ▾]  Industry: [All ▾]  Status: [Ready ▾]   Search: [______]  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Name                    Family       Industry   Variations   Status  │ │
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ plumber-chaos-v1        commercial   plumber    50,625        ●ready │ │
│  │ hvac-chaos-v1           commercial   hvac       50,625        ●ready │ │
│  │ plumber-seo-audit-v1    loom         plumber    12,000        ●ready │ │
│  │ hvac-seo-audit-v1       loom         hvac       12,000        ◐draft │ │
│  │ restaurant-chaos-v1     commercial   restaurant 50,625        ○idea  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Template Detail Page (`/templates/[id]`)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Templates /  plumber-chaos-v1                      [Render...] [Edit...] │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌─────────────────────────────┐  Family:      commercial                  │
│  │                             │  Industry:    plumber                     │
│  │   [preview reel player]     │  Version:     1.0.0                       │
│  │                             │  Path:        templates\commercials\...   │
│  │   30s sample auto-plays     │  Status:      ready                       │
│  │                             │  Variations:  50,625                      │
│  └─────────────────────────────┘  Created:     2026-04-23                  │
│                                   Last render: 2026-04-23 14:32            │
│                                                                             │
│  Beats                                                                      │
│  ──────                                                                     │
│  01  intro           Card animates in w/ {business_name}                    │
│  02  problem         Shows {seo_rank} + {keyword}                          │
│  03  slot            [1 of 15] Hardware Hack options                       │
│  04  destruction     [1 of 10] Destruction endings                         │
│  05  cta             {phone} + "Call us to fix this"                       │
│                                                                             │
│  Slot Variation Libraries                                                   │
│  ─────────────────────                                                     │
│  ▸ hardware_hacks   (15 options)                                            │
│  ▸ rationales        (15 options)                                            │
│  ▸ destruction_modes (10 options)                                           │
│  ▸ closers           (10 options)                                           │
│                                                                             │
│  Required Business Data                                                     │
│  ──────────────────                                                        │
│  • name (string)       • phone (string)      • city (string)               │
│  • seo_rank (int)      • keyword_tracked     • competitors (array)          │
│                                                                             │
│  Recent Renders (12)                                          [view all →]  │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ joes-plumbing-denver     ●done    32s   2m ago       [preview] [→]   │ │
│  │ ace-plumbing-tulsa       ●done    32s   1h ago       [preview] [→]   │ │
│  │ ...                                                                   │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### Render Modal (`[Render...]` button)

```
┌────────────────────────────────────────────────────┐
│ Render — plumber-chaos-v1                       ✕  │
│ ──────────────────────────────────────────────────│
│                                                    │
│ Business           [Joe's Plumbing ▾]  [search...] │
│                                                    │
│ Slot Variations                                    │
│ ──────────────                                     │
│ hardware_hacks     [Random ▾]    (15 options)      │
│ rationales         [Random ▾]                      │
│ destruction_modes  [Random ▾]                      │
│ closers            [Random ▾]                      │
│                                                    │
│ Voice engine       ● edge  ○ kokoro  ○ xtts-clone │
│                                                    │
│ [Render now]  [Queue]   [Cancel]                   │
└────────────────────────────────────────────────────┘
```

**Tokens:** ~90k. **Time:** ~5 min.

---

## SPEC-D4 — Page: Loom

**Route:** `/dashboard/loom`
**Purpose:** Dedicated kickoff + tracking for screen-record audit videos. Same data as Videos page but filtered to loom family + extra controls.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Loom Videos                                             [+ New Audit]       │
│ ────────────────────────────────────────────────────────────────────────── │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ ⎯  One-off audit — paste a URL or pick from businesses               │ │
│  │                                                                        │ │
│  │    Business:  [pick ▾]   or   URL: [___________________]              │ │
│  │    Template:  [plumber-seo-audit-v1 ▾]                                 │ │
│  │    Voice:     ●edge ○kokoro ○xtts                                     │ │
│  │    Length:    ●2-3min ○4-5min ○auto                                   │ │
│  │                                                                        │ │
│  │                                               [Render Audit Now]       │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Recent Loom Renders                                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Business              Template       Duration    Status    Views     ││
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ joes-plumbing-denver  seo-audit-v1   3:14        ●done      7        ││
│  │ ace-hvac-tulsa        seo-audit-v1   2:58        ●done      0        ││
│  │ ...                                                                   ││
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tokens:** ~45k. **Time:** ~3 min.

---

## SPEC-D5 — Page: Businesses

**Route:** `/dashboard/businesses`
**Purpose:** Browse scraped leads. See what's been rendered for each. Track outreach status.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Businesses                                       [Import CSV] [+ Manual]    │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Industry: [All ▾]  City: [All ▾]  Status: [All ▾]     Search: [________] │
│                                                                             │
│  4,782 businesses  •  318 rendered  •  47 replied  •  12 closed             │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Name                    Industry  City         Rank  Videos  Status   ││
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ ☐ Joe's Plumbing        plumber   Denver CO    #14   2       ◐sent   ││
│  │ ☐ Ace HVAC              hvac      Tulsa OK     #8    1       ●replied ││
│  │ ☐ Pipe Masters          plumber   Miami FL     #22   0       ○untouched│
│  │ ☐ Draintech             plumber   Phoenix AZ   #31   3       ●closed  ││
│  │ ☐ Rooter Kings          plumber   Dallas TX    #6    0       ○untouched│
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ☐ 0 selected  |  [Render Batch] [Send Outreach] [Export]                  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Business Detail (`/businesses/[id]`)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ← Businesses / Joe's Plumbing              [Render Video] [Send Outreach]  │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌─────────────┐  Name          Joe's Plumbing                              │
│  │    LOGO     │  Phone         (303) 555-0100                              │
│  │             │  Website       joesplumbing.com    [open]                  │
│  └─────────────┘  GBP           [open]                                      │
│                   Industry      plumber                                     │
│                   City          Denver, CO                                  │
│                   Rank          #14 for "plumber denver"                    │
│                   Competitors   acme-plumbing, quick-pipe, denver-drain     │
│                   Scraped       2026-04-21                                  │
│                                                                             │
│  Videos (2)                                                                 │
│  ──────                                                                     │
│  ● plumber-chaos-v1      32s    2h ago    [preview][share][download]       │
│  ● seo-audit-v1          3:14   1h ago    [preview][share][download]       │
│                                                                             │
│  Landing Page                                                               │
│  ────────────                                                               │
│  URL: videofor.me/joes-plumbing-denver          [view] [copy] [regenerate] │
│  Views: 7  •  Last view: 1h ago                                             │
│                                                                             │
│  Outreach Timeline                                                          │
│  ─────────────                                                             │
│  • 2026-04-23 14:32  sent via GSA to contact form                           │
│  • 2026-04-23 15:15  landing page viewed                                    │
│  • —                  no reply yet                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tokens:** ~100k. **Time:** ~6 min.

---

## SPEC-D6 — Page: Campaigns

**Route:** `/dashboard/campaigns`
**Purpose:** Batch runs. Pick a template, pick N businesses, render everything, track results.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Campaigns                                            [+ New Campaign]       │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Name           Template          Biz  Rendered  Sent  Replies  Rate  ││
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ Plumbers Q2    plumber-chaos-v1  500  500       487   23       4.7% ││
│  │ HVAC April     hvac-chaos-v1     300  289       285   11       3.8% ││
│  │ Loom Test 1    seo-audit-v1      50   50        50    7        14%  ││
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### New Campaign Wizard

```
Step 1: Pick template
Step 2: Pick business list (filter or manual select)
Step 3: Review render plan (N videos, X tokens estimated, Y minutes ETA)
Step 4: Pick outreach channel (GSA / email / Mixpost / manual-only)
Step 5: Confirm + launch
```

**Tokens:** ~80k. **Time:** ~5 min.

---

## SPEC-D7 — Page: Posting (Mixpost Bridge)

**Route:** `/dashboard/posting`
**Purpose:** Route finished videos to clients' social accounts via Mixpost.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Posting                                                                     │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Mixpost status: ●connected   Workspaces: 127   Queued posts: 43            │
│                                                                             │
│  Scheduled                                                                  │
│  ────────                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Video                   Business         Platforms       When   Status││
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ chaos-v1-001.mp4        joes-plumbing    FB IG TT YT    tomorrow 9am ││
│  │ seo-audit-001.mp4       ace-hvac         FB IG          Fri 10am     ││
│  │ ...                                                                   ││
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Workspace Management                                                       │
│  ────────────────────                                                      │
│  [Connect new client to Mixpost →]                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tokens:** ~60k. **Time:** ~3.5 min.

---

## SPEC-D8 — Page: Landing Pages

**Route:** `/dashboard/landing-pages`
**Public-facing route:** `/v/[slug]` (e.g. `videofor.me/v/joes-plumbing-denver`)

### Admin wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Landing Pages                                                               │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Template: [sales-audit-v1 ▾]   [Edit template]                             │
│                                                                             │
│  Generated Pages (318)                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Slug                    Business         Views  Last view  Status     ││
│  ├──────────────────────────────────────────────────────────────────────┤ │
│  │ joes-plumbing-denver    Joe's Plumbing    7     1h ago     ●live      ││
│  │ ace-hvac-tulsa          Ace HVAC          12    2h ago     ●live      ││
│  │ ...                                                                   ││
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

### Public page (what the business sees)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                     JOE'S PLUMBING                                      │
│              We made you a video. Watch below.                          │
│                                                                         │
│    ┌───────────────────────────────────────────────────────────────┐   │
│    │                                                               │   │
│    │             [video player, autoplay muted]                    │   │
│    │                                                               │   │
│    └───────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   What we found wrong:                                                  │
│   • You rank #14 for "plumber Denver" — your competitors make $850k/yr  │
│   • Your GBP is missing 5 key fields                                    │
│   • 0 photos on your listing                                            │
│                                                                         │
│   We can fix this.                                                      │
│                                                                         │
│                   [Book a free call]   [Get 4 more videos free]         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Tokens:** ~80k. **Time:** ~5 min.

---

## SPEC-D9 — Page: Admin

**Route:** `/dashboard/admin`
**Purpose:** Pipeline health, costs, worker status, settings.

### Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Admin                                                                       │
│ ────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Render Worker                                                              │
│  ─────────────                                                              │
│  Status: ●running (PID 18234)   Started: 12h ago   Queue: 12 jobs           │
│  Current job: seo-audit-v1 × ace-hvac     Elapsed: 1:14                     │
│  [Restart worker]  [Pause queue]  [View live log →]                         │
│                                                                             │
│  Storage (E:\VideoFactory)                                                  │
│  ──────                                                                     │
│  Used: 42.3 GB / 200 GB  ▓▓▓▓▓░░░░░░░░░░░░░░░░                             │
│  Renders: 28.1 GB  Cache: 8.7 GB  Templates: 2.4 GB  DB: 14 MB              │
│  [Clean cache]  [Archive old renders]                                       │
│                                                                             │
│  Cost Today                                                                 │
│  ─────                                                                     │
│  Haiku calls: $0.14    Sonnet: $0.03    TTS: $0.00    Total: $0.17          │
│                                                                             │
│  Settings                                                                   │
│  ────────                                                                   │
│  ▸ Voice defaults      edge / GuyNeural                                     │
│  ▸ Mixpost endpoint    https://post.yourdomain.com                          │
│  ▸ CDN bucket          (not configured)                                     │
│  ▸ Backup schedule     daily at 03:00                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tokens:** ~55k. **Time:** ~3 min.

---

## SPEC-D10 — Render Worker Service

**Path:** `E:\VideoFactory\worker\orchestrator.py`
**Runs as:** Windows service or just `python orchestrator.py` in a terminal (auto-restart via `nssm` for v1)

### Behavior

```python
# pseudocode
while True:
    job = sqlite.fetch_next_queued_render()
    if not job:
        sleep(2); continue
    mark_running(job)
    try:
        pipeline = load_pipeline(job.template_family)     # commercial or loom
        check_sandbox(pipeline)                            # enforce ALLOWED_TOOLS
        output_path = pipeline.run(job)                    # actual render
        mark_done(job, output_path)
    except Exception as e:
        mark_failed(job, str(e))
        write_log(job, traceback)
```

**Tokens:** ~70k. **Time:** ~4 min.

---

## SPEC-D11 — Template Authoring Workflow (Claude-driven)

Since owner isn't coding templates, this spec is the PROCESS not a UI.

### Workflow

1. Owner: "I want a new template — HVAC chaos engine, angle: broken furnace in winter"
2. Claude reads `commercial-playbook.md` + `video-template-build-workflow.md`
3. Claude creates `E:\VideoFactory\templates\commercials\hvac-chaos-v1\`
4. Claude writes:
   - `template.yaml` (metadata, slot variation libraries, required biz-data fields)
   - `beat-*.html` (5-7 hyperframes beats)
   - `assets\` (any template-specific fonts/sfx/characters)
5. Claude runs worker in test mode → renders sample → opens preview
6. Owner watches preview in dashboard, gives feedback
7. Claude iterates
8. When ready: `sqlite INSERT INTO templates ... status='ready'`
9. Template appears in dashboard Templates page

### Admin "New Template" button
Just opens a modal: "Copy `/templates/templates\...` path → describe what you want to Claude in any chat → tell Claude to commit it when done."
Zero in-dashboard authoring code written v1.

**Tokens:** 0 (just process docs). **Time:** 0.

---

## SPEC-D12 — Slot Variation Controls (Per-Render)

Inside the `[Render...]` modal on Templates page and Business detail page.

Reads `template.yaml` slot libraries → renders a dropdown per slot w/ options:

```
hardware_hacks: [Random ▾]
                 ↓
                 Random (weighted)
                 ────────────
                 Spare tire rocket
                 Life jacket keyboard
                 IV drip Mountain Dew
                 Snorkel data lake
                 ...
```

`[Render now]` → job goes to queue with locked selections. `Random` → worker picks at render time.

**Tokens:** ~35k. **Time:** ~2 min.

---

## SPEC-D13 — Auth + Session (Env-var)

Very minimal, boilerplate has most of this.

```ts
// middleware.ts
if (!process.env.SUPABASE_URL) {
  // single-user mode
  if (!cookies.has('factory-session')) redirect('/login')
}

// /login
// form POST → if user === FACTORY_USER && pass === FACTORY_PASS → set cookie → redirect /dashboard
```

Replace w/ Supabase Auth when SaaS flip happens. Keep interface (`useUser()`, `requireAuth()`) stable.

**Tokens:** ~25k. **Time:** ~1.5 min.

---

## SPEC-D14 — Global Search (⌘K)

Searches across: businesses, templates, renders, campaigns.
Results grouped by type. Arrow keys nav, Enter opens.

Powered by SQLite FTS5 virtual tables (same trick we'll use in memory system — nice reuse).

**Tokens:** ~50k. **Time:** ~3 min.

---

# Build Plan — Tokens + Time

### Phase 1 — Skeleton (MVP, 1 template, 1 biz, end-to-end)

| # | Spec | Tokens | Time |
|---|------|--------|------|
| 1 | D1 Boilerplate strip + SQLite wire | 80k | 5 min |
| 2 | D13 Auth | 25k | 1.5 min |
| 3 | D10 Render worker | 70k | 4 min |
| 4 | D2 Videos page (read-only) | 40k | 2.5 min |
| 5 | D3 Templates page (read-only + render modal) | 60k | 3.5 min |
| 6 | D12 Slot variation controls | 35k | 2 min |
| 7 | plumber-chaos-v1 template (Claude authors the template itself) | 80k | 5 min |
| — | **Phase 1 total** | **390k** | **~24 min gen + ~30 min user setup** |

After Phase 1: you can render commercials for any biz in DB via the dashboard. Worker handles it. Result shows up in Videos page.

### Phase 2 — Full internal tool

| # | Spec | Tokens | Time |
|---|------|--------|------|
| 8 | D5 Businesses page + detail | 100k | 6 min |
| 9 | D4 Loom page + plumber-seo-audit-v1 template | 170k | 10 min |
| 10 | D6 Campaigns page + wizard | 80k | 5 min |
| 11 | D8 Landing pages (admin + public) | 80k | 5 min |
| 12 | D7 Posting / Mixpost bridge | 60k | 3.5 min |
| 13 | D9 Admin page | 55k | 3 min |
| 14 | D14 Global search | 50k | 3 min |
| — | **Phase 2 total** | **595k** | **~36 min gen** |

### Grand Total (Phase 1 + Phase 2)
**~985k tokens ≈ ~1 hour pure gen time.**
Real calendar time to ship: 1-3 days of focused work (includes testing, iteration, owner feedback loops).

---

# Open Questions (need user answer before build starts)

| # | Q |
|---|---|
| Q1 | **Boilerplate:** paste repo URL or zip path so I can inspect it. Need to know: Next.js? Remix? Other? What auth lib? What ORM? What UI component lib? |
| Q2 | **Dashboard domain:** `localhost:3000` locally fine? Or bind to a LAN IP so you can hit it from phone on same WiFi? |
| Q3 | **Landing page public domain:** `videofor.me`? Something else? Buy now or use subdomain of existing domain? |
| Q4 | **Worker auto-start:** install as Windows service via `nssm`? Or just a batch file you run? Service = survives reboot, batch = simpler. |
| Q5 | **Backup:** nightly SQLite backup + rsync to where? OneDrive? Another external drive? Skipping = risky. |

---

# Risks

| Risk | Mitigation |
|------|-----------|
| External drive disconnects mid-render | Worker detects, pauses queue, alerts. DB backed up daily. |
| E: drive fills (200 GB runs out in ~10k renders) | Admin storage page shows usage, auto-prompts to archive. |
| Owner pivots to SaaS early | Every design decision chosen to support clean SaaS flip (see §2.7). |
| Boilerplate has different stack than assumed | First step of Phase 1 = inspect boilerplate, may need small adjustments. ~20k token risk. |
| Worker crashes → queue stalls silently | Heartbeat in DB every 30s. Dashboard shows red if stale. |

---

# TL;DR

- **One dashboard, 9 pages, zero SaaS wiring, all on E: drive.**
- **~985k tokens / ~1 hr gen** to ship complete internal tool.
- **Claude authors templates in code.** Dashboard has render controls only.
- **Future SaaS flip = 3 days** because every seam designed for it.
- **Blocking on:** boilerplate repo + 5 small Qs above.

Ready to build on green light.
