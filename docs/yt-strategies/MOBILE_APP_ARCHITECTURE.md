# Mobile App Architecture — System Controller

> **Status:** Design document. This covers the Flutter mobile app that acts as a remote control for the entire Greptacular system — not just YT Lab, but Workspace, DunkStack, and AutoForge.

---

## The Core Concept

**The mobile app is a controller, not a computer.** It doesn't run AI, doesn't execute agents, doesn't do heavy processing. The desktop/server does all that. The phone mirrors every button, input, and result — you push buttons, see outcomes, manage queues, and stay in the loop while away from your desk.

Think TV remote, not TV. The TV (desktop) does the work. The remote (phone) tells it what to do and shows what's happening.

```
┌─────────────┐                    ┌──────────────────────┐
│  Mobile App  │───── Supabase ────│  Desktop/Server      │
│  (Flutter)   │    (shared DB +   │  (Python + Claude)   │
│              │     realtime)     │                      │
│  Controller  │                   │  Compute Engine      │
│  - buttons   │  ← realtime ←    │  - AI processing     │
│  - inputs    │  → commands →     │  - agent execution   │
│  - results   │                   │  - file operations   │
│  - queues    │                   │  - builds/tests      │
└─────────────┘                    └──────────────────────┘
```

**Why this works:** Every current UI control is just an HTTP call to an API endpoint or a WebSocket message. The Flutter app makes those same calls. The logic doesn't change. The server doesn't care if the button press came from a browser or a phone.

---

## What Lives Where

| Capability | Desktop (Browser) | Mobile (Flutter) | Notes |
|-----------|-------------------|-------------------|-------|
| **Agent start/stop** | Full control | Full control | Same API call |
| **Feature management** | Full CRUD + drag | Full CRUD + tap | Simplified layout |
| **Project selection** | Dropdown | List view | Same API |
| **Settings** | Full modal | Full page | Same fields |
| **Workspace chat** | 3-panel split | Single panel | One conversation at a time |
| **DunkStack** | Full view | Token gauge + status | Read-heavy, light control |
| **YT Lab** | Full pipeline | Queue + review | Capture URLs, review results |
| **Terminal** | xterm.js | Read-only log viewer | No interactive terminal on mobile |
| **Dependency graph** | Interactive DAG | Simplified list view | Touch-friendly alternative |
| **File browser** | Tree + preview | Flat list + preview | No deep navigation |
| **Agent logs** | Streaming panel | Streaming list | Same WebSocket feed |
| **AI processing** | Runs locally | Cannot run | Claude CLI needs desktop |
| **Notifications** | None currently | Push notifications | Phone's killer feature |

---

## Architecture: How Desktop + Mobile Connect

### Option A: Direct API (Simple, Works Now)

The mobile app talks directly to the FastAPI server running on the desktop. Works on the same WiFi network.

```
Phone ──── WiFi ──── Desktop (localhost:8765)
```

**Pros:** No cloud needed, zero cost, works today, no auth complexity
**Cons:** Only works on same network, no access away from home

### Option B: Supabase Bridge (Works Everywhere)

Once Supabase is set up (see DATABASE_STRATEGY.md), both desktop and mobile talk to the same Supabase instance. The desktop writes results, the mobile reads them. Commands go through a `commands` table that the desktop polls or subscribes to.

```
Phone ──── Supabase ──── Desktop
              │
              └── Shared DB + Realtime
```

**The command pattern:**

```sql
-- Mobile writes a command
create table commands (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id),
  command_type text not null,      -- 'agent_start', 'agent_stop', 'feature_create', etc.
  payload jsonb not null,          -- command-specific data
  status text default 'pending',   -- pending, acknowledged, completed, failed
  result jsonb,                    -- response from desktop
  created_at timestamptz default now(),
  completed_at timestamptz
);

-- Desktop subscribes to new commands via Supabase realtime
-- Executes command locally
-- Updates status + result
```

```dart
// Mobile: Start agent
await supabase.from('commands').insert({
  'user_id': userId,
  'command_type': 'agent_start',
  'payload': {
    'project_name': 'my-app',
    'model': 'claude-sonnet-4-6',
    'yolo': true,
    'concurrency': 3,
  },
});

// Desktop (Python): Listen and execute
supabase.channel('commands')
    .on_postgres_changes(event='INSERT', table='commands')
    .subscribe(handle_command)
```

```python
# Desktop command handler
async def handle_command(payload):
    cmd = payload['new']
    if cmd['command_type'] == 'agent_start':
        project = cmd['payload']['project_name']
        # Call the same endpoint the browser calls
        await start_agent(project, cmd['payload'])
        # Update command status
        await supabase.from('commands').update({
            'status': 'completed',
            'completed_at': 'now()'
        }).eq('id', cmd['id']).execute()
```

**Pros:** Works anywhere (coffee shop, commute, different building), phone becomes true remote
**Cons:** Requires Supabase setup (Phase 1 of DATABASE_STRATEGY.md), slight latency for commands

### Recommendation: Start with Option A, Graduate to Option B

Option A works today with zero infrastructure. Build the Flutter app against the local API first. When Supabase is up (Week 1-2 of database migration), add the command bridge. The app structure doesn't change — just swap the HTTP base URL from `localhost:8765` to `your-project.supabase.co`.

---

## App Structure (Flutter)

### Navigation

Bottom tab bar with 4 main sections:

```
┌──────────────────────────────────────┐
│                                      │
│          [Active Page Content]       │
│                                      │
│                                      │
├──────┬──────┬──────┬──────┬─────────┤
│  🏠  │  💬  │  🧪  │  📺  │  ⚙️   │
│ Home │ Work │Forge │ YT   │Settings │
└──────┴──────┴──────┴──────┴─────────┘
```

### Tab 1: Home (Dashboard)

The "what's happening right now" view.

```
┌──────────────────────────────────┐
│  Greptacular                  ☀️ │
├──────────────────────────────────┤
│                                  │
│  ┌────────────────────────────┐  │
│  │  Active Agent              │  │
│  │  ████████████░░░  73%      │  │
│  │  my-app · 11/15 features   │  │
│  │  [▶ Running] [■ Stop]      │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │  DunkStack Context         │  │
│  │  ██████████░░░░  67%       │  │
│  │  134K / 200K tokens        │  │
│  │  Zone: Safe                │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │  YT Lab Queue              │  │
│  │  3 queued · 1 processing   │  │
│  │  Last: "AI Agency v2"      │  │
│  │  [+ Add Video]             │  │
│  └────────────────────────────┘  │
│                                  │
│  Recent Activity                 │
│  ─────────────────────────       │
│  ✅ Feature: Auth flow - done    │
│  🔄 Processing: Lead Gen vid    │
│  📝 Workspace: 3 new messages   │
│  ✅ Feature: Dashboard - done    │
│                                  │
└──────────────────────────────────┘
```

**Controls:**
- Agent start/stop/pause (tap the status button)
- Quick-add video to staging queue
- Tap any card to dive into that section

**Data:**
- Active agent progress (project name, feature count, percentage)
- DunkStack token gauge (current/max, safety zone color)
- YT Lab queue status (queued count, processing count)
- Activity feed (last 10 events across all systems)

### Tab 2: Workspace (Chat)

Single-panel chat that connects to the same workspace conversations.

```
┌──────────────────────────────────┐
│  ← Workspace        Opus 200K ▼ │
├──────────────────────────────────┤
│  Conversations                   │
│  ┌────────────────────────────┐  │
│  │ 📌 Auth System Design      │  │
│  │    Last: 2 min ago          │  │
│  ├────────────────────────────┤  │
│  │    Lead Gen Pipeline        │  │
│  │    Last: 1 hour ago         │  │
│  ├────────────────────────────┤  │
│  │    API Refactor             │  │
│  │    Last: yesterday          │  │
│  └────────────────────────────┘  │
│                                  │
│  [+ New Conversation]            │
└──────────────────────────────────┘
```

Tap a conversation to open the chat view:

```
┌──────────────────────────────────┐
│  ← Auth System Design   Opus ▼  │
├──────────────────────────────────┤
│                                  │
│  You: What's the best approach   │
│  for JWT refresh tokens?         │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Claude: For JWT refresh     │  │
│  │ tokens, the most secure     │  │
│  │ approach is...              │  │
│  │                        📋  │  │
│  └────────────────────────────┘  │
│                                  │
│  You: Can you implement that     │
│  in the auth module?             │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Claude: I'll update the     │  │
│  │ auth module with the        │  │
│  │ refresh token logic...      │  │
│  │ ● typing...                 │  │
│  └────────────────────────────┘  │
│                                  │
├──────────────────────────────────┤
│  [Type a message...]      [Send] │
└──────────────────────────────────┘
```

**Controls:**
- Model selector (Opus/Sonnet, 200K/1M)
- Send messages
- Copy message content
- Create new conversations
- Pin/archive conversations

**Not on mobile:** Split view (Research/PRD/Coder panels). Too small for 3 panels. Use single conversation mode. The desktop handles multi-panel orchestration.

### Tab 3: AutoForge (Project Manager)

Project selection + feature kanban + agent controls.

```
┌──────────────────────────────────┐
│  ← AutoForge              ⚡▼   │
├──────────────────────────────────┤
│  Projects                        │
│  ┌────────────────────────────┐  │
│  │ ● my-app          11/15   │  │
│  │   Running · 73%            │  │
│  ├────────────────────────────┤  │
│  │ ○ portfolio-site    8/8   │  │
│  │   Complete · 100%          │  │
│  ├────────────────────────────┤  │
│  │ ○ api-service      0/12   │  │
│  │   Idle                     │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

Tap a project to see features:

```
┌──────────────────────────────────┐
│  ← my-app              11/15    │
│  ████████████░░░░  73%          │
│  [▶ Running] [■ Stop] [⚡YOLO]  │
├──────────────────────────────────┤
│  [Pending] [In Progress] [Done]  │
├──────────────────────────────────┤
│                                  │
│  ┌────────────────────────────┐  │
│  │ #12 Payment Integration    │  │
│  │ Priority: 1 · Backend      │  │
│  │ Blocked by: #11             │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ #13 Email Notifications    │  │
│  │ Priority: 2 · Backend      │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ #14 Admin Dashboard        │  │
│  │ Priority: 3 · Frontend     │  │
│  └────────────────────────────┘  │
│                                  │
│  [+ Add Feature]                 │
└──────────────────────────────────┘
```

Tap a feature:

```
┌──────────────────────────────────┐
│  ← #12 Payment Integration      │
├──────────────────────────────────┤
│  Status: Pending                 │
│  Priority: 1                     │
│  Category: Backend               │
│                                  │
│  Description:                    │
│  Integrate Stripe for one-time   │
│  and subscription payments...    │
│                                  │
│  Steps:                          │
│  1. Create Stripe service        │
│  2. Add checkout endpoint        │
│  3. Handle webhooks              │
│  4. Add payment UI               │
│                                  │
│  Dependencies:                   │
│  ├── #11 User Auth (pending)     │
│  └── #8 Database (done)          │
│                                  │
│  [Edit] [Delete]                 │
└──────────────────────────────────┘
```

**Controls:**
- Agent start/stop/pause per project
- YOLO mode toggle
- Concurrency slider
- Feature CRUD (add, edit, delete)
- Tab filter (Pending / In Progress / Done)
- Tap to expand feature details

**Not on mobile:** Dependency graph visualization (too complex for touch), drag-reorder (use move up/down buttons instead), terminal access.

### Tab 4: YT Lab

Video queue management, result review, and quick capture.

```
┌──────────────────────────────────┐
│  ← YT Strategy Lab         🔍   │
├──────────────────────────────────┤
│  Staging Queue (3)               │
│  ┌────────────────────────────┐  │
│  │ 🟡 AI Agency Automation    │  │
│  │    Queued · 2 min ago       │  │
│  │    [Process] [Edit] [×]     │  │
│  ├────────────────────────────┤  │
│  │ 🟡 Lead Gen Pipeline       │  │
│  │    Queued · 10 min ago      │  │
│  ├────────────────────────────┤  │
│  │ 🔵 Content Strategy        │  │
│  │    Processing... 45%        │  │
│  └────────────────────────────┘  │
│                                  │
│  Projects (7)                    │
│  ┌────────────────────────────┐  │
│  │ ✅ Car Dealership Ads       │  │
│  │    9 steps · Complete        │  │
│  ├────────────────────────────┤  │
│  │ ✅ Newsletter Growth        │  │
│  │    8 steps · Complete        │  │
│  ├────────────────────────────┤  │
│  │ 🔄 SaaS Onboarding        │  │
│  │    6 steps · In Progress    │  │
│  └────────────────────────────┘  │
│                                  │
│  [+ Quick Capture]               │
└──────────────────────────────────┘
```

**Quick Capture** — the killer mobile feature:

```
┌──────────────────────────────────┐
│  Quick Capture                 × │
├──────────────────────────────────┤
│                                  │
│  YouTube URL:                    │
│  ┌────────────────────────────┐  │
│  │ https://youtube.com/...    │  │
│  └────────────────────────────┘  │
│  [📋 Paste from clipboard]       │
│                                  │
│  What do you want from this?     │
│  ┌────────────────────────────┐  │
│  │ Extract the lead gen       │  │
│  │ automation from the first  │  │
│  │ 15 minutes — the scraping  │  │
│  │ + enrichment pipeline      │  │
│  └────────────────────────────┘  │
│                                  │
│  Priority: [Low] [Med] [★ High]  │
│                                  │
│  [Queue for Processing]          │
│                                  │
└──────────────────────────────────┘
```

This is the on-the-go use case: you're watching YouTube on your phone, you see a video worth processing, you paste the URL + a quick description, set priority, and it goes into the staging queue. When you get back to your desk, it's waiting to be processed.

Tap a completed project to review:

```
┌──────────────────────────────────┐
│  ← Car Dealership Ads    Export  │
├──────────────────────────────────┤
│  Source: youtube.com/watch?v=... │
│  9 steps · Complete              │
│                                  │
│  Discovery Insights:             │
│  ┌────────────────────────────┐  │
│  │ 💡 Speaker targets local   │  │
│  │    businesses with $500/mo  │  │
│  │    ad budgets...            │  │
│  └────────────────────────────┘  │
│                                  │
│  Steps:                          │
│  ┌────────────────────────────┐  │
│  │ 1. Create Style Sheet      │  │
│  │    Research competitor ads  │  │
│  │    and establish brand...   │  │
│  │                      [▶]   │  │
│  ├────────────────────────────┤  │
│  │ 2. Prospect Research       │  │
│  │    Find local businesses   │  │
│  │    using Apollo + Maps...  │  │
│  │                      [▶]   │  │
│  └────────────────────────────┘  │
│                                  │
└──────────────────────────────────┘
```

**Controls:**
- Quick Capture (URL + description + priority → staging queue)
- Review discovery results
- Browse project steps
- Edit step details
- Trigger processing from queue
- Route completed items (assign to pipeline destinations)

**Not on mobile:** Strategy extraction AI processing (needs Claude CLI), screenshot capture (needs ffmpeg), step execution with browser automation.

### Tab 5: Settings

```
┌──────────────────────────────────┐
│  Settings                        │
├──────────────────────────────────┤
│                                  │
│  Connection                      │
│  ┌────────────────────────────┐  │
│  │ Server: 192.168.1.100:8765 │  │
│  │ Status: ● Connected         │  │
│  │ [Change Server]             │  │
│  └────────────────────────────┘  │
│                                  │
│  Agent Defaults                  │
│  ┌────────────────────────────┐  │
│  │ Model: Sonnet 4.6      ▼  │  │
│  │ YOLO Mode:          [OFF]  │  │
│  │ Concurrency:     [●●●○○]  │  │
│  │ Batch Size:           3 ▼  │  │
│  └────────────────────────────┘  │
│                                  │
│  Notifications                   │
│  ┌────────────────────────────┐  │
│  │ Agent complete:     [ON]   │  │
│  │ Feature done:       [ON]   │  │
│  │ Processing done:    [ON]   │  │
│  │ Agent crashed:      [ON]   │  │
│  │ Queue full:         [OFF]  │  │
│  └────────────────────────────┘  │
│                                  │
│  Appearance                      │
│  ┌────────────────────────────┐  │
│  │ Theme: Neobrutalism     ▼  │  │
│  │ Dark Mode:          [ON]   │  │
│  └────────────────────────────┘  │
│                                  │
│  Account                         │
│  ┌────────────────────────────┐  │
│  │ Signed in as: user@...     │  │
│  │ [Sign Out]                  │  │
│  └────────────────────────────┘  │
│                                  │
└──────────────────────────────────┘
```

---

## Push Notifications (The Killer Mobile Feature)

The desktop has no notification system. You have to keep the browser open and watch. The mobile app fixes this:

| Event | Notification | Priority |
|-------|-------------|----------|
| Agent finished all features | "my-app: All 15 features complete!" | High |
| Agent crashed | "my-app: Agent crashed — authentication error" | High |
| Video processing complete | "YT Lab: 'Lead Gen Pipeline' ready to review" | Medium |
| Feature completed | "my-app: #12 Payment Integration done" | Low |
| Staging queue item ready | "YT Lab: New item ready for routing" | Medium |
| DunkStack context warning | "DunkStack: 85% context — approaching handoff zone" | Medium |

**Implementation with Supabase:**

```sql
-- Supabase Edge Function triggered by realtime events
-- Sends push notification via Firebase Cloud Messaging (FCM)

create or replace function notify_on_agent_complete()
returns trigger as $$
begin
  -- When agent_status changes to 'completed'
  if NEW.status = 'completed' and OLD.status != 'completed' then
    perform net.http_post(
      url := 'https://fcm.googleapis.com/...',
      body := jsonb_build_object(
        'to', (select fcm_token from profiles where id = NEW.user_id),
        'notification', jsonb_build_object(
          'title', NEW.project_name || ': Complete!',
          'body', 'All features implemented successfully'
        )
      )
    );
  end if;
  return NEW;
end;
$$ language plpgsql;
```

---

## Realtime State Sync

Both the desktop browser and mobile app subscribe to the same Supabase realtime channels. When the desktop updates agent status, the mobile app reflects it instantly.

```dart
// Flutter: Subscribe to agent status changes
supabase
    .channel('agent_status')
    .onPostgresChanges(
      event: PostgresChangeEvent.update,
      schema: 'public',
      table: 'agent_sessions',
      callback: (payload) {
        setState(() {
          agentStatus = payload.newRecord['status'];
          agentProgress = payload.newRecord['progress'];
        });
      },
    )
    .subscribe();

// Flutter: Subscribe to feature completions
supabase
    .channel('features')
    .onPostgresChanges(
      event: PostgresChangeEvent.update,
      schema: 'public',
      table: 'features',
      filter: PostgresChangeFilter(
        type: PostgresChangeFilterType.eq,
        column: 'status',
        value: 'passing',
      ),
      callback: (payload) {
        // Show completion animation, update kanban
        showFeatureComplete(payload.newRecord);
      },
    )
    .subscribe();
```

---

## What the Mobile App CANNOT Do (By Design)

These require the desktop and should never be on mobile:

1. **Run Claude CLI / AI processing** — needs local CLI installation + subscription auth
2. **Interactive terminal** — typing in a terminal on a phone is miserable
3. **3-panel workspace** — screen too small, pointless to try
4. **File editing** — use the desktop for code
5. **Dependency graph manipulation** — drag-and-drop doesn't translate to touch
6. **Browser automation / computer-use** — needs desktop browser
7. **Screenshot capture from videos** — needs ffmpeg + yt-dlp

The phone does: **monitor, control, queue, review, route.** The desktop does: **compute, execute, build, test.**

---

## Flutter Project Structure

```
greptacular_mobile/
├── lib/
│   ├── main.dart                    -- App entry, Supabase init
│   ├── app.dart                     -- MaterialApp with theme + routing
│   │
│   ├── core/
│   │   ├── supabase_client.dart     -- Supabase singleton
│   │   ├── api_client.dart          -- Direct API client (Option A fallback)
│   │   ├── theme.dart               -- Neobrutalism theme (match web)
│   │   ├── constants.dart           -- Colors, sizes, strings
│   │   └── notifications.dart       -- FCM setup + handlers
│   │
│   ├── models/
│   │   ├── project.dart             -- AutoForge project
│   │   ├── feature.dart             -- Feature with status/deps
│   │   ├── conversation.dart        -- Workspace conversation
│   │   ├── yt_project.dart          -- YT Lab project
│   │   ├── staging_item.dart        -- Queue item
│   │   └── command.dart             -- Remote command
│   │
│   ├── providers/                   -- Riverpod state management
│   │   ├── auth_provider.dart
│   │   ├── projects_provider.dart
│   │   ├── agent_provider.dart
│   │   ├── features_provider.dart
│   │   ├── workspace_provider.dart
│   │   ├── yt_lab_provider.dart
│   │   ├── dunkstack_provider.dart
│   │   └── settings_provider.dart
│   │
│   ├── screens/
│   │   ├── home/
│   │   │   └── home_screen.dart         -- Dashboard overview
│   │   ├── workspace/
│   │   │   ├── conversations_screen.dart
│   │   │   └── chat_screen.dart
│   │   ├── autoforge/
│   │   │   ├── projects_screen.dart
│   │   │   ├── features_screen.dart
│   │   │   └── feature_detail_screen.dart
│   │   ├── yt_lab/
│   │   │   ├── yt_lab_screen.dart
│   │   │   ├── quick_capture_screen.dart
│   │   │   ├── project_detail_screen.dart
│   │   │   └── staging_queue_screen.dart
│   │   ├── settings/
│   │   │   └── settings_screen.dart
│   │   └── auth/
│   │       └── login_screen.dart
│   │
│   └── widgets/
│       ├── agent_status_card.dart
│       ├── progress_bar.dart
│       ├── feature_card.dart
│       ├── activity_feed.dart
│       ├── context_gauge.dart       -- DunkStack token meter
│       ├── queue_item_card.dart
│       └── chat_bubble.dart
│
├── pubspec.yaml
│   # Dependencies:
│   # supabase_flutter: ^2.0.0
│   # flutter_riverpod: ^2.0.0
│   # firebase_messaging: ^15.0.0
│   # go_router: ^14.0.0
│   # shared_preferences: ^2.0.0
│
└── README.md
```

---

## Implementation Timeline

### Phase 1: Scaffold + Local API (Week 1)

- Flutter project setup
- Neobrutalism theme matching web
- Home dashboard with hardcoded data
- Direct API client (Option A — local network)
- Project list + feature kanban
- Agent start/stop controls

**Deliverable:** Basic controller works on same WiFi network.

### Phase 2: Supabase Integration (Week 2)

- Auth (Google OAuth, same as web)
- Replace API client with Supabase queries
- Realtime subscriptions for agent status + features
- YT Lab staging queue (Supabase table)
- Quick Capture screen

**Deliverable:** Works anywhere, data synced with web.

### Phase 3: Chat + Notifications (Week 3)

- Workspace chat (single-panel)
- Push notifications via FCM
- DunkStack context gauge (read-only)
- Activity feed with realtime updates
- Settings page with full controls

**Deliverable:** Feature-complete controller.

### Phase 4: Polish + Release (Week 4)

- Offline mode (cached data from last sync)
- Deep links (tap notification → specific feature/project)
- Widget for home screen (agent status at a glance)
- App store submission (TestFlight / Play Console)

---

## Technology Choices

| Choice | Why |
|--------|-----|
| **Flutter** | Cross-platform (iOS + Android), Supabase has first-class Flutter SDK, fast iteration |
| **Riverpod** | State management that handles realtime streams cleanly |
| **go_router** | Declarative routing with deep link support |
| **Supabase Flutter** | Auth + DB + Realtime + Storage in one package |
| **Firebase Messaging** | Push notifications (works with Supabase Edge Functions) |
| **Neobrutalism theme** | Match the web UI so it feels like the same product |

---

## The "Almost Full Control" Reality

You said it right — the mobile app can almost mimic every single button and input. Here's the breakdown:

**100% parity (same API call, same result):**
- Agent start/stop/pause/resume
- Project create/delete/select
- Feature add/edit/delete
- Settings changes (model, YOLO, concurrency, batch size, theme)
- Conversation create/delete
- Chat messages send/receive
- YT Lab video queue/process/route
- Schedule management

**Simplified parity (same data, different presentation):**
- Feature kanban → list view with tabs instead of drag columns
- Dependency graph → text list of dependencies instead of DAG
- Agent logs → scrolling list instead of fixed panel
- File browser → flat list instead of tree

**Desktop-only (no mobile equivalent):**
- AI processing execution (Claude CLI)
- Interactive terminal (xterm.js)
- 3-panel workspace split
- Code file editing
- Browser automation
- Screenshot capture

That's maybe 10% of the surface area that's desktop-only. The other 90% is just buttons and inputs that work identically from a phone.

---

## TL;DR

**Flutter mobile app = remote control for the entire Greptacular system.** Not just YT Lab — Workspace chat, AutoForge project management, DunkStack monitoring, and YT Lab queue management. Phone does controller stuff (buttons, inputs, results, notifications). Desktop does compute stuff (AI, agents, builds, tests).

Start with local WiFi API calls (works today, zero infrastructure). Graduate to Supabase bridge (works anywhere) when the database migration is done. 4 weeks to feature-complete. The killer feature is push notifications — know when agents finish, features complete, videos process, or things crash, without sitting at your desk.
