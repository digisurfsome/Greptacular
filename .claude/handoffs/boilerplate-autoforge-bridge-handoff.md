# Boilerplate-to-AutoForge Integration Bridge PRD

## Status: Ready to Implement

## The Problem

AutoForge (the coding agent system) and the Gen-Ai SaaS boilerplate (the web frontend at autoforge.com) are two completely separate systems:

| System | Stack | Current State |
|---|---|---|
| **AutoForge** | Python, FastAPI, SQLite, Claude Agent SDK | Runs locally on user's machine, `127.0.0.1:8000`, no auth, single-user |
| **Gen-Ai Boilerplate** | Next.js, Supabase, Stripe, Vercel | Cloud-deployed SaaS shell with auth, billing, admin dashboard |

This PRD defines the **integration bridge** — how the web app triggers builds, streams progress, delivers files, and manages multi-tenant isolation. Without this bridge, the boilerplate and AutoForge are just two unrelated applications.

### What This PRD Does NOT Cover

- Credit system details (see `credit-pricing-system-handoff-v2.md`)
- Boilerplate features that already exist (auth, Stripe, admin)
- AutoForge's internal agent logic (prompts, MCP tools, security hooks)
- The AutoForge React UI (`ui/` directory) — this is replaced by the boilerplate's frontend

---

## Architecture Overview

### Deployment Model: Cloud Build Workers

AutoForge cannot stay as a localhost tool for SaaS. Each build needs an isolated cloud environment where the agent can:
- Execute bash commands (npm, git, python, etc.)
- Run a dev server and browser automation (Playwright)
- Read/write project files on disk
- Run for 30-120 minutes per build

**Solution: Dedicated build worker VMs per active build.**

```
┌─────────────────────────────────────────────────────────┐
│  autoforge.com (Vercel)                                 │
│  Next.js + Supabase Auth + Stripe                       │
│                                                         │
│  User clicks "Start Build"                              │
│       │                                                 │
│       ▼                                                 │
│  POST /api/builds/start                                 │
│       │                                                 │
│       ├─ Check auth (Supabase JWT)                      │
│       ├─ Check credits (credit_balances)                │
│       ├─ Consume credit atomically                      │
│       ├─ Check rate limits                              │
│       │                                                 │
│       ▼                                                 │
│  Build Orchestrator Service                             │
│       │                                                 │
│       ├─ Provision worker VM (or claim from pool)       │
│       ├─ Copy project spec + config to worker           │
│       ├─ Start AutoForge on worker                      │
│       ├─ Store worker_url in builds table               │
│       │                                                 │
│       ▼                                                 │
│  WebSocket proxy: client ↔ worker                       │
│       │                                                 │
│       ├─ Progress streaming                             │
│       ├─ Log streaming                                  │
│       ├─ Agent state updates                            │
│       │                                                 │
│       ▼                                                 │
│  Build completes                                        │
│       │                                                 │
│       ├─ Package project files → cloud storage          │
│       ├─ Generate download link                         │
│       ├─ Record usage metrics (build_usage)             │
│       ├─ Tear down worker VM                            │
│       └─ Notify user (email, webhook)                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Build Worker VM (per-build, ephemeral)                 │
│                                                         │
│  Ubuntu 24.04 LTS                                       │
│  Python 3.12, Node.js 22, Claude CLI                    │
│  AutoForge server on port 8000 (internal only)          │
│  Playwright browsers pre-installed                      │
│                                                         │
│  ┌───────────────────────────────────────┐              │
│  │ AutoForge FastAPI Server              │              │
│  │ - Feature MCP, agent pipeline         │              │
│  │ - SQLite features.db (per-build)      │              │
│  │ - WebSocket streaming                 │              │
│  │ - AUTOFORGE_ALLOW_REMOTE=1            │              │
│  └───────────────────────────────────────┘              │
│                                                         │
│  ┌───────────────────────────────────────┐              │
│  │ Auth Token Validation Middleware      │              │
│  │ - Validates per-build JWT from proxy  │              │
│  │ - Rejects all other requests          │              │
│  └───────────────────────────────────────┘              │
│                                                         │
│  Lifecycle: provision → configure → build → package →   │
│             upload → teardown                           │
└─────────────────────────────────────────────────────────┘
```

### Why Dedicated VMs (Not Containers)

- **Long-running:** Builds run 30-120 minutes — too long for serverless
- **Heavy compute:** AI agent + Playwright browser + dev server simultaneously
- **Disk I/O:** Frequent npm installs, git operations, file writes
- **Isolation:** Each build gets a clean filesystem — no cross-contamination
- **Claude CLI:** Requires a proper Linux environment with PTY support
- **Security:** Bash command execution needs VM-level sandboxing, not just container namespaces

### Cloud Provider Options

| Provider | Service | Cost (est.) | Notes |
|---|---|---|---|
| **GCP** | Compute Engine (e2-standard-4) | ~$0.13/hr | Preemptible for cost savings |
| **AWS** | EC2 (t3.xlarge) | ~$0.17/hr | Spot instances available |
| **Fly.io** | Machines API | ~$0.10/hr | Fastest cold start, auto-stop |
| **Hetzner** | Cloud (CPX31) | ~$0.03/hr | Best price, EU only |

**Recommendation:** Start with **Fly.io Machines** for MVP — instant cold start, per-second billing, easy teardown, built-in private networking. Migrate to GCP Compute Engine at scale for more control.

---

## Feature 1: Build Orchestrator Service

The central service that manages the lifecycle of build worker VMs. Runs as a long-lived process on the web app's infrastructure (or a dedicated orchestrator server).

### Responsibilities

1. **VM Pool Management** — Maintain a warm pool of pre-provisioned workers
2. **Build Assignment** — Match incoming build requests to available workers
3. **Health Monitoring** — Detect crashed/stuck builds, auto-recover
4. **Teardown** — Clean up workers after build completion
5. **Queue Management** — Priority ordering when all workers are busy

### New Database Tables (Supabase)

```sql
-- Build records (central tracking)
create table builds (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  project_id uuid not null,
  project_name text not null,
  credit_type text not null,
  is_byok boolean default false,

  -- Worker assignment
  worker_id text,                   -- VM identifier (fly machine ID, GCP instance name)
  worker_url text,                  -- Internal URL to reach worker's AutoForge API
  worker_region text,               -- Deployment region

  -- Build configuration
  app_spec text not null,           -- Full app_spec.txt content
  boilerplate_id text,
  style_id text,
  custom_colors jsonb,
  yolo_mode boolean default false,
  model text default 'claude-sonnet-4-5-20250929',
  max_concurrency integer default 3,
  batch_size integer default 3,

  -- BYOK
  anthropic_api_key_encrypted bytea, -- Decrypted from byok_keys, re-encrypted for transit

  -- Progress
  status text not null default 'queued'
    check (status in ('queued', 'provisioning', 'initializing', 'building',
                       'testing', 'packaging', 'completed', 'failed', 'cancelled', 'refunded')),
  features_total integer default 0,
  features_completed integer default 0,
  features_failed integer default 0,
  current_phase text,               -- 'spec_analysis', 'architecture', 'initialization', 'coding', 'testing'
  progress_percentage numeric(5,2) default 0,

  -- Deliverables
  artifact_url text,                -- Cloud storage URL for packaged project
  artifact_size_bytes bigint,
  artifact_expires_at timestamptz,  -- Pre-signed URL expiry (7 days)
  spec_analysis_md text,            -- Spec analysis report
  architecture_md text,             -- ARCHITECTURE.md content
  qa_report_md text,                -- QA report

  -- Timing
  queued_at timestamptz default now(),
  started_at timestamptz,
  completed_at timestamptz,
  duration_minutes integer,

  -- Error handling
  error_message text,
  retry_count integer default 0,
  max_retries integer default 2,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index idx_builds_user on builds(user_id, created_at desc);
create index idx_builds_status on builds(status) where status in ('queued', 'provisioning', 'building');
create index idx_builds_worker on builds(worker_id) where worker_id is not null;

alter table builds enable row level security;
create policy "Users read own builds" on builds for select using (auth.uid() = user_id);

-- Worker pool tracking
create table build_workers (
  id text primary key,              -- VM identifier
  provider text not null,           -- 'fly', 'gcp', 'aws'
  region text not null,
  status text not null default 'idle'
    check (status in ('idle', 'provisioning', 'assigned', 'running', 'draining', 'terminated')),
  current_build_id uuid references builds(id),
  ip_address text,
  internal_url text,                -- Private network URL
  machine_type text,                -- e2-standard-4, t3.xlarge, etc.
  created_at timestamptz default now(),
  last_heartbeat_at timestamptz,
  terminated_at timestamptz
);
```

### Build Start Flow (Detailed)

```
POST /api/builds/start
  Body: {
    project_name: string,
    app_spec: string,
    boilerplate_id?: string,
    style_id?: string,
    custom_colors?: object,
    credit_type: "standard_web" | "standard_dual" | "pro_web" | "pro_dual" | "enterprise",
    yolo_mode?: boolean,
    model?: string
  }

Steps:
  1. Validate Supabase JWT from Authorization header
  2. Validate app_spec is non-empty and < 100KB
  3. Check credit_balances for sufficient typed credits
  4. Check rate_limits for concurrent/daily/monthly limits
  5. Consume credit atomically via consume_build_credit()
  6. Insert builds row with status='queued'
  7. If BYOK user: decrypt API key from byok_keys, re-encrypt for transit
  8. Check worker pool for idle worker
     a. If available: assign worker, set status='provisioning'
     b. If none: add to priority queue, return queue position
  9. Return build_id + WebSocket URL for progress streaming

Response: {
  build_id: uuid,
  status: "queued" | "provisioning",
  queue_position?: number,
  ws_url: "wss://autoforge.com/api/builds/{build_id}/ws"
}
```

### Worker Provisioning Flow

```
1. Orchestrator selects idle worker (or provisions new one)
2. SSH/API call to worker:
   a. Create project directory: /builds/{build_id}/
   b. Write app_spec.txt to .autoforge/prompts/
   c. Clone boilerplate repo (if boilerplate_id specified)
   d. Write style config to .autoforge/project_config.json
   e. Set environment variables:
      - ANTHROPIC_API_KEY (platform key or BYOK key)
      - AUTOFORGE_ALLOW_REMOTE=1
      - BUILD_AUTH_TOKEN={per-build JWT}
      - BUILD_CALLBACK_URL=https://autoforge.com/api/builds/{build_id}/callback
   f. Start AutoForge: python autonomous_agent_demo.py --project-dir /builds/{build_id}/
3. Update builds row: status='initializing', worker_id, worker_url
4. Start health monitoring (heartbeat every 30s)
```

---

## Feature 2: WebSocket Proxy (Real-Time Progress)

The web app needs to stream AutoForge's real-time updates to the user's browser. The proxy sits between the user and the build worker.

### Architecture

```
Browser (autoforge.com)
    │
    │ wss://autoforge.com/api/builds/{build_id}/ws
    │ (Supabase JWT in query param or header)
    │
    ▼
Next.js API Route / Edge Function (WebSocket proxy)
    │
    │ Validates JWT, looks up builds row for worker_url
    │
    │ ws://{worker_internal_url}/ws/projects/{project_name}
    │ (BUILD_AUTH_TOKEN in header)
    │
    ▼
AutoForge Worker (FastAPI WebSocket)
    │
    │ Streams: progress, log, agent_status, agent_update,
    │          orchestrator_update, feature_update
    │
    ▼
Proxy forwards events back to browser
```

### WebSocket Event Translation

AutoForge emits events in its own format. The proxy translates to a SaaS-friendly format:

```typescript
// AutoForge internal format (from worker)
{ type: "progress", passing: 5, in_progress: 1, total: 12, percentage: 41.7 }
{ type: "agent_status", status: "running" }
{ type: "log", line: "Creating login page component...", featureId: 3, agentIndex: 0 }
{ type: "agent_update", agentIndex: 0, agentName: "Spark", state: "working", featureId: 3, featureName: "Login Page", thought: "Creating components..." }

// Translated format (to browser)
{
  type: "build_progress",
  build_id: "uuid",
  data: {
    features_completed: 5,
    features_in_progress: 1,
    features_total: 12,
    percentage: 41.7,
    phase: "coding",
    agents: [
      { name: "Spark", state: "working", feature: "Login Page", thought: "Creating components..." }
    ]
  },
  timestamp: "2026-02-15T10:30:00Z"
}
```

### Events to Persist

Some WebSocket events should be written back to the `builds` table for historical access:

| Event | Action |
|---|---|
| `progress` | Update `features_completed`, `features_total`, `progress_percentage` |
| `agent_status: stopped` | Set `status='completed'` or `status='failed'` |
| `agent_status: crashed` | Set `status='failed'`, trigger auto-retry |
| Phase transitions | Update `current_phase` |

### Reconnection Handling

- Browser disconnects are common (tab switch, network glitch)
- Proxy buffers last 100 events per build
- On reconnect, replay missed events
- If build completed during disconnect, send final state

---

## Feature 3: Build Artifact Delivery

When a build completes, the project files need to be packaged and delivered to the user.

### Packaging Flow

```
Build completes (all features passing or max retries)
    │
    ├─ Run on worker: tar -czf /tmp/{build_id}.tar.gz /builds/{build_id}/
    │   Exclude: node_modules/, .git/, venv/, __pycache__/, .autoforge/
    │
    ├─ Upload to cloud storage (GCS / S3 / R2)
    │   Path: builds/{user_id}/{build_id}/project.tar.gz
    │
    ├─ Generate pre-signed download URL (7-day expiry)
    │
    ├─ Also upload:
    │   - spec-analysis.md (if generated)
    │   - ARCHITECTURE.md (if generated)
    │   - qa-report.md (if generated)
    │   - qa-screenshots/ (if generated)
    │
    ├─ Update builds row:
    │   artifact_url, artifact_size_bytes, artifact_expires_at,
    │   spec_analysis_md, architecture_md, qa_report_md,
    │   status='completed', completed_at, duration_minutes
    │
    ├─ Record build_usage metrics (tokens, cost, margin)
    │
    ├─ Send notification (email via Resend)
    │
    └─ Tear down worker VM (after 5-minute grace period)
```

### Download API

```
GET /api/builds/{build_id}/download
  Auth: Supabase JWT
  Returns: 302 redirect to pre-signed cloud storage URL

GET /api/builds/{build_id}/reports
  Auth: Supabase JWT
  Returns: { spec_analysis, architecture, qa_report }

GET /api/builds/{build_id}/screenshots
  Auth: Supabase JWT
  Returns: Array of pre-signed URLs for QA screenshots
```

### GitHub Integration (Optional, Pro+ tiers)

Instead of (or in addition to) a download:
1. User connects GitHub account via OAuth (boilerplate has this)
2. On build completion, create a new repo or push to existing
3. Include CI/CD workflow file for deployment
4. Open PR if pushing to existing repo

```
POST /api/builds/{build_id}/deploy-github
  Body: { repo_name?: string, existing_repo?: string, branch?: string }
  Auth: Supabase JWT + GitHub token
```

---

## Feature 4: Multi-Tenant Isolation

AutoForge is currently single-user. SaaS needs strict isolation between users.

### Isolation Boundaries

| Layer | Isolation Method |
|---|---|
| **Compute** | Separate VM per build (strongest — no shared processes) |
| **Filesystem** | Each build gets `/builds/{build_id}/` — VM destroyed after |
| **Network** | Workers on private network, only reachable via proxy |
| **Database** | Supabase RLS on all tables (user_id = auth.uid()) |
| **API Keys** | BYOK keys encrypted per-user, decrypted only on assigned worker |
| **Secrets** | Platform Anthropic key injected via env var, never written to disk on worker |
| **Logs** | Logs tagged with build_id, stored in cloud logging, RLS-filtered for users |

### Worker Security Hardening

Each worker VM must:
1. Run AutoForge with `AUTOFORGE_ALLOW_REMOTE=1` but behind auth middleware
2. Accept only requests with valid `BUILD_AUTH_TOKEN` (short-lived JWT, per-build)
3. Have no SSH access after provisioning (provision via cloud API, not SSH)
4. Have no access to other workers' networks
5. Be destroyed within 10 minutes of build completion
6. Have no persistent storage (ephemeral disk only)
7. Have outbound internet access (for npm install, git clone) but no inbound except from proxy

---

## Feature 5: Authentication Bridge

The boilerplate uses Supabase Auth. AutoForge has no auth. The bridge connects them.

### Token Flow

```
1. User logs in via Supabase Auth (email/OAuth) — boilerplate handles this
2. Browser has Supabase JWT (access_token)
3. All /api/builds/* requests include: Authorization: Bearer {supabase_jwt}
4. Next.js API routes validate JWT via Supabase server client
5. Extract user_id from JWT for database queries
6. When provisioning a worker:
   a. Generate short-lived BUILD_AUTH_TOKEN (JWT signed with server secret)
   b. Claims: { build_id, user_id, exp: now + build_duration + 1hr }
   c. Pass to worker via env var
7. Proxy requests to worker include: X-Build-Token: {BUILD_AUTH_TOKEN}
8. Worker middleware validates BUILD_AUTH_TOKEN on every request
```

### AutoForge Worker Auth Middleware (New)

A lightweight middleware added to AutoForge's FastAPI server for SaaS mode:

```python
# Only active when BUILD_AUTH_TOKEN env var is set
# In local mode (no env var), middleware is a no-op

@app.middleware("http")
async def validate_build_token(request, call_next):
    expected = os.environ.get("BUILD_AUTH_TOKEN")
    if not expected:
        return await call_next(request)  # Local mode, no auth

    token = request.headers.get("X-Build-Token")
    if token != expected:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    return await call_next(request)
```

This is intentionally simple — the worker is already on a private network and only reachable via the proxy. The token is a defense-in-depth layer, not the primary security boundary.

---

## Feature 6: Build Dashboard (Web App Frontend)

New pages/components in the boilerplate's Next.js app for managing builds.

### Pages

| Route | Description |
|---|---|
| `/dashboard` | Overview: active builds, recent builds, credit balance |
| `/builds/new` | New build wizard: spec → boilerplate → style → review → start |
| `/builds/{id}` | Live build view: progress, logs, agent activity |
| `/builds/{id}/results` | Completed build: download, reports, screenshots, deploy |
| `/builds` | Build history: list with filters, search, status |
| `/pricing` | Credit types, bundles, BYOK, annual plans |
| `/settings/byok` | BYOK API key management |

### New Build Wizard Flow

```
Step 1: App Spec
  - Paste or type app specification
  - Or: upload existing spec file
  - Or: AI-assisted spec creation (chat interface)
  - Character limit: 100,000 chars
  - Validation: minimum 500 chars, XML format check

Step 2: Boilerplate Selection
  - Grid of available boilerplates with preview images
  - "Start from scratch" option
  - Filter by framework (React, Next.js, etc.)

Step 3: Style Selection
  - Style picker with live preview
  - Audience/vibe/age_group filters
  - Custom color overrides
  - Accent style selection

Step 4: Build Configuration
  - Credit type selection (Standard/Pro/Enterprise)
  - BYOK toggle (if key configured)
  - YOLO mode toggle
  - Model selection (Sonnet/Opus)
  - Review estimated cost

Step 5: Review & Start
  - Summary of all selections
  - Credit deduction confirmation
  - "Start Build" button
```

### Live Build View (`/builds/{id}`)

Real-time dashboard showing:

1. **Progress Bar** — Features completed / total with percentage
2. **Phase Indicator** — Spec Analysis → Architecture → Initialization → Coding → Testing
3. **Agent Cards** — Active agents with mascot names, current feature, state (thinking/working/testing)
4. **Log Stream** — Scrolling log output with feature-level filtering
5. **Feature Board** — Mini kanban: Pending → In Progress → Done
6. **Actions** — Pause, Resume, Cancel buttons
7. **Estimated Time** — Based on historical builds of similar size

### Build Results View (`/builds/{id}/results`)

1. **Download Button** — Tar.gz download (7-day link)
2. **Deploy to GitHub** — One-click repo creation (Pro+ tiers)
3. **Spec Analysis Report** — Rendered markdown
4. **Architecture Document** — Rendered markdown
5. **QA Report** — Test results with screenshots
6. **Build Metrics** — Duration, tokens used, features completed/failed

---

## Feature 7: Build Callbacks (Worker → Web App)

Workers need to notify the web app of lifecycle events that aren't covered by WebSocket (e.g., when no client is connected).

### Callback Endpoint

```
POST /api/builds/{build_id}/callback
  Auth: X-Build-Token header
  Body: {
    event: "started" | "phase_change" | "progress" | "completed" | "failed" | "crashed",
    data: { ... event-specific payload ... }
  }
```

### Events

| Event | When | Data |
|---|---|---|
| `started` | Agent begins running | `{ features_total }` |
| `phase_change` | Phase transition | `{ phase, previous_phase }` |
| `progress` | Feature completed | `{ features_completed, features_total, percentage }` |
| `completed` | All features done | `{ features_completed, features_failed, duration_minutes }` |
| `failed` | Build cannot continue | `{ error_message, features_completed, features_total }` |
| `crashed` | Process died | `{ exit_code, last_log_lines }` |

### Crash Recovery

```
Worker crashes (process dies, OOM, etc.)
    │
    ├─ Heartbeat stops (30s timeout)
    ├─ OR: callback event "crashed"
    │
    ▼
Orchestrator detects failure
    │
    ├─ retry_count < max_retries (2)?
    │   YES:
    │     ├─ Increment retry_count
    │     ├─ Re-provision worker (or reuse if still alive)
    │     ├─ Copy features.db from worker (preserves completed features)
    │     ├─ Restart agent (will pick up from uncompleted features)
    │     └─ Update status='building', notify user via WebSocket
    │   NO:
    │     ├─ Set status='failed'
    │     ├─ Package whatever was completed
    │     ├─ Trigger auto-refund via refund_build_credit()
    │     ├─ Notify user (email + WebSocket)
    │     └─ Tear down worker
```

---

## Feature 8: Worker Health Monitoring

### Heartbeat System

```
Every 30 seconds, worker sends:
  POST /api/builds/{build_id}/heartbeat
  Body: {
    timestamp: ISO 8601,
    cpu_percent: number,
    memory_percent: number,
    disk_percent: number,
    agent_pid: number | null,
    active_agents: number
  }

Orchestrator checks:
  - No heartbeat for 90s? Mark worker as unhealthy
  - No heartbeat for 180s? Assume crashed, trigger recovery
  - Memory > 90%? Alert admin
  - Disk > 85%? Alert admin
  - Build running > 180 minutes? Alert admin, consider termination
```

### Admin Alerts

Extend boilerplate's admin dashboard with build health monitoring:
- Unhealthy workers
- Builds exceeding time limits
- Worker pool utilization
- Failed build rate

---

## Feature 9: Spec Creation Chat (SaaS Version)

AutoForge has an interactive spec creation WebSocket at `/api/spec/ws/{project_name}`. For SaaS, this needs to work BEFORE a build is started (and before a worker is provisioned).

### Approach: Lightweight Spec Chat (No Worker Needed)

Spec creation is just a Claude conversation — it doesn't need a full build worker. Run it directly from the web app using the Anthropic API.

```
Browser
    │
    │ wss://autoforge.com/api/spec/ws
    │ (Supabase JWT)
    │
    ▼
Next.js WebSocket handler
    │
    │ Anthropic API (Messages API with streaming)
    │ System prompt: spec creation template from .claude/templates/
    │ Model: claude-sonnet-4-5 (fast, cheap)
    │
    ▼
Returns structured app_spec.txt
    │
    └─ Stored in Supabase: user_specs table
       Ready to pass to build worker when user starts build
```

### New Database Table

```sql
create table user_specs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  name text not null,
  content text not null,              -- app_spec.txt content
  chat_history jsonb,                 -- Conversation for context
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table user_specs enable row level security;
create policy "Users manage own specs" on user_specs for all using (auth.uid() = user_id);
```

### Spec Management UI

- `/specs` — List saved specs with edit/delete/duplicate
- `/specs/new` — Chat-based spec creation
- `/specs/{id}/edit` — Edit existing spec (text editor + chat refinement)
- Specs can be used across multiple builds

---

## Feature 10: AutoForge Server Modifications

The AutoForge codebase needs minimal changes to support SaaS mode. The goal is to keep AutoForge functional as BOTH a local tool AND a SaaS worker.

### Changes Required

| File | Change | Purpose |
|---|---|---|
| `server/main.py` | Add `BUILD_AUTH_TOKEN` middleware | Per-build auth on workers |
| `server/main.py` | Add `/callback` endpoint registration | Worker → web app notifications |
| `client.py` | Support `ANTHROPIC_API_KEY` env var override | BYOK key injection |
| `autonomous_agent_demo.py` | Add `--callback-url` flag | Enable callback notifications |
| `autonomous_agent_demo.py` | Add `--build-id` flag | Tag logs with build ID |
| `progress.py` | Add HTTP callback on feature completion | Notify orchestrator |
| New: `server/middleware/build_auth.py` | Token validation middleware | SaaS auth |
| New: `server/callbacks.py` | HTTP callback client | Report events to web app |
| New: `heartbeat.py` | Background heartbeat sender | Health monitoring |

### SaaS Mode Detection

```python
# AutoForge detects SaaS mode via environment variables
SAAS_MODE = bool(os.environ.get("BUILD_AUTH_TOKEN"))

if SAAS_MODE:
    # Enable auth middleware
    # Enable callback notifications
    # Enable heartbeat
    # Disable local-only UI serving (worker doesn't need React UI)
```

### What Stays the Same

- Agent pipeline (prompts, MCP tools, security hooks)
- Feature MCP server
- WebSocket streaming format
- Project structure on disk
- Parallel orchestration
- All existing CLI flags

---

## Feature 11: Project Expand & Assistant (SaaS Version)

AutoForge has two interactive chat features that need SaaS equivalents:

### Expand Project (Add Features Post-Build)

After a build completes, users may want to add features. This requires a running AutoForge instance.

**Approach:** Spin up a worker with the existing project files (from cloud storage), run the expand chat, then re-package and upload.

```
POST /api/builds/{build_id}/expand
  Auth: Supabase JWT
  Requires: 1 additional credit of matching type
  Returns: { expansion_build_id, ws_url }
```

### Project Assistant (Q&A About Built Project)

Read-only chat about the project's architecture, code, etc. Does NOT need a full worker — just needs file access.

**Approach:** Download project files to a temporary directory on the web server, use Claude API with file context.

```
POST /api/builds/{build_id}/assistant/message
  Auth: Supabase JWT
  Body: { message: string, conversation_id?: uuid }
  Returns: streamed response
```

This is a lower priority — implement after core build flow is working.

---

## New API Endpoints Summary

### Build Lifecycle

| Endpoint | Method | Description |
|---|---|---|
| `/api/builds` | GET | List user's builds (paginated, filtered) |
| `/api/builds/start` | POST | Start new build (consumes credit) |
| `/api/builds/{id}` | GET | Get build details |
| `/api/builds/{id}/cancel` | POST | Cancel build (refund if not started) |
| `/api/builds/{id}/pause` | POST | Pause active build |
| `/api/builds/{id}/resume` | POST | Resume paused build |
| `/api/builds/{id}/ws` | WS | Real-time progress streaming |
| `/api/builds/{id}/download` | GET | Download completed project |
| `/api/builds/{id}/reports` | GET | Get build reports |
| `/api/builds/{id}/screenshots` | GET | Get QA screenshots |
| `/api/builds/{id}/deploy-github` | POST | Deploy to GitHub repo |
| `/api/builds/{id}/expand` | POST | Add features (new build) |
| `/api/builds/{id}/assistant/message` | POST | Project Q&A chat |

### Build Callbacks (Worker → Web App)

| Endpoint | Method | Description |
|---|---|---|
| `/api/builds/{id}/callback` | POST | Worker lifecycle events |
| `/api/builds/{id}/heartbeat` | POST | Worker health heartbeat |

### Spec Management

| Endpoint | Method | Description |
|---|---|---|
| `/api/specs` | GET | List user's saved specs |
| `/api/specs` | POST | Create new spec |
| `/api/specs/{id}` | GET | Get spec content |
| `/api/specs/{id}` | PATCH | Update spec |
| `/api/specs/{id}` | DELETE | Delete spec |
| `/api/specs/chat/ws` | WS | AI-assisted spec creation |

### Build Admin (Extends Boilerplate Admin)

| Endpoint | Method | Description |
|---|---|---|
| `/api/admin/builds` | GET | All builds (admin view) |
| `/api/admin/workers` | GET | Worker pool status |
| `/api/admin/workers/{id}/terminate` | POST | Force terminate worker |
| `/api/admin/builds/{id}/refund` | POST | Manual credit refund |

---

## New Environment Variables (Web App)

```bash
# Cloud provider for build workers
BUILD_WORKER_PROVIDER=fly              # fly | gcp | aws
BUILD_WORKER_REGION=iad                # Primary region
BUILD_WORKER_MACHINE_TYPE=shared-cpu-4x # Fly machine size

# Worker pool
BUILD_WORKER_POOL_SIZE=5               # Warm pool size
BUILD_WORKER_MAX_TOTAL=20              # Hard limit on concurrent workers
BUILD_WORKER_TIMEOUT_MINUTES=180       # Max build duration

# Cloud storage for artifacts
ARTIFACT_STORAGE_PROVIDER=r2           # r2 | s3 | gcs
ARTIFACT_STORAGE_BUCKET=autoforge-builds
ARTIFACT_STORAGE_REGION=auto
ARTIFACT_DOWNLOAD_EXPIRY_DAYS=7

# Platform Anthropic key (for managed builds)
PLATFORM_ANTHROPIC_API_KEY=sk-ant-...

# Build auth
BUILD_JWT_SECRET=...                   # Signs per-build JWTs

# Spec creation (lightweight, runs on web app)
SPEC_ANTHROPIC_API_KEY=sk-ant-...      # Can be same as platform key
SPEC_MODEL=claude-sonnet-4-5-20250929
```

---

## Implementation Priority

### Phase 1: Core Build Flow (Week 1-3)
1. `builds` and `build_workers` Supabase tables
2. Build orchestrator service (Fly.io Machines integration)
3. Worker provisioning: spin up, configure, start AutoForge
4. WebSocket proxy: browser → proxy → worker → browser
5. Build start API with credit consumption (from v2 PRD)
6. Artifact packaging and cloud storage upload
7. Download API with pre-signed URLs
8. AutoForge: add `BUILD_AUTH_TOKEN` middleware, `--callback-url`, `--build-id`

### Phase 2: Build Dashboard (Week 4-5)
1. New build wizard (spec → boilerplate → style → config → start)
2. Live build view (progress, logs, agent cards)
3. Build results view (download, reports, screenshots)
4. Build history page with filters

### Phase 3: Reliability (Week 6)
1. Worker heartbeat monitoring
2. Crash recovery with auto-retry
3. Build timeout enforcement
4. Callback event handling
5. Admin build health dashboard

### Phase 4: Spec Management (Week 7)
1. `user_specs` Supabase table
2. Spec creation chat (Anthropic API, no worker needed)
3. Spec CRUD pages
4. Spec import/export

### Phase 5: Advanced Features (Week 8-9)
1. GitHub deployment integration
2. Project expand (spin up worker with existing files)
3. Project assistant (lightweight Q&A)
4. Worker pool auto-scaling
5. Multi-region worker deployment

### Phase 6: Scale & Optimization (Week 10+)
1. Worker image pre-baking (npm cache, Playwright browsers, etc.)
2. Worker warm pool auto-sizing based on demand
3. Build queue optimization (batch provisioning)
4. Cost optimization (spot/preemptible instances)
5. CDN for artifact delivery
6. Build analytics and insights

---

## Cost Estimates

### Per-Build Infrastructure Cost

| Component | Cost (est.) |
|---|---|
| Worker VM (60 min avg) | $0.10-0.17 |
| Cloud storage (500MB avg, 7 days) | $0.001 |
| Bandwidth (download) | $0.01 |
| WebSocket proxy compute | $0.002 |
| **Total infrastructure per build** | **~$0.15-0.20** |

Infrastructure cost is negligible compared to AI cost ($50-250 per build). Even at $219 minimum credit price, infrastructure is < 0.1% of revenue per build.

### Monthly Fixed Costs

| Component | Cost (est.) |
|---|---|
| Warm worker pool (5 idle VMs) | $50-100/mo |
| Cloud storage (accumulating) | $10-50/mo (scales with builds) |
| WebSocket proxy (edge compute) | $20-50/mo |
| Monitoring/logging | $20-50/mo |
| **Total monthly overhead** | **~$100-250/mo** |

Break-even at ~1-2 builds per month. Scales linearly with demand.

---

## Open Questions

1. **Worker provider:** Start with Fly.io Machines or go directly to GCP Compute Engine?
2. **Artifact retention:** 7 days for free, longer for paid tiers? Or permanent storage?
3. **Live preview:** Should the worker's dev server be accessible to the user during build? (Security implications)
4. **Build notifications:** Email only, or also push notifications / Slack webhooks?
5. **Collaborative builds:** Can multiple users watch the same build? (Team/Agency tier)
6. **Build resume:** If a build fails at 80%, can the user resume from where it left off without a new credit?
7. **Source code access:** Should users get access to the git history, or just the final snapshot?
8. **Custom CLAUDE.md:** Should users be able to provide their own CLAUDE.md with coding preferences?
