# Attack Forge: Module Dashboard System

> **Status**: V2 Design Spec — Extends Attack Forge Blueprint
> **Date**: March 13, 2026
> **Core Insight**: Every module has its OWN dashboard built in. The dashboard isn't a separate thing — it's part of the module. From the smallest component to the largest objective, each one knows its own status, its own completion, its own numbers.

---

## The Key Realization

The dashboard is NOT a separate layer sitting on top. **The dashboard IS the module.** Every single node — whether it's a tiny component or a massive campaign — carries its own:
- Status display
- Completion metrics
- To-do list
- Performance numbers
- Success criteria

When you zoom out, you see the big picture dashboard (all modules aggregated). When you zoom in, you see one module's dashboard. Same system, different zoom level.

---

## Module Lifecycle (Every Module Goes Through These Phases)

Every module, regardless of type or size, progresses through the same phases. Each phase has its own dashboard view. These phases become **tabs** on the module page.

### Phase 1: INGESTION
**What happens**: Ideas come in. Could be YouTube video, text, audio, document, voice memo, screenshot — anything.

**Dashboard shows**:
- Total inputs ingested (videos, docs, text blocks, etc.)
- Type breakdown (3 videos, 2 docs, 1 text idea)
- Coverage map: what topics/areas have been fed in
- Gaps: what areas still need input
- Human comments/annotations on each input
- Completion bar: "Ingestion is 60% complete based on identified topic areas"

**What "complete" means for this phase**: All identified topic areas have at least one source. Gaps are filled. Human has reviewed and said "that's enough input, let's move on."

```
┌─────────────────────────────────────────────────┐
│  INGESTION                        72% Complete  │
│                                                 │
│  Sources: 5 videos, 2 docs, 1 text    [+ Add]  │
│                                                 │
│  ✅ Core process         3 sources              │
│  ✅ SEO techniques       2 sources              │
│  ⬜ Monetization         0 sources  ← GAP      │
│  ✅ Automation tools     2 sources              │
│  ⬜ Analytics setup      0 sources  ← GAP      │
│                                                 │
│  Comments: "Need a video on tracking setup"     │
│                                                 │
│  [Mark Ingestion Complete]                      │
└─────────────────────────────────────────────────┘
```

### Phase 2: ASSEMBLY
**What happens**: All the ingested material gets organized into the actual plan. Components get identified. Sub-modules get defined. The skeleton takes shape.

**Dashboard shows**:
- Total components/pieces identified
- How many are defined vs. still vague
- Dependencies mapped (what needs what)
- Which pieces already exist in other modules (reusable)
- Which pieces need to be built from scratch
- Which pieces have GitHub/open-source candidates
- Completion bar: "Assembly is 40% complete — 12 of 30 pieces defined"

**What "complete" means for this phase**: Every piece is identified, defined, and has a plan for how it gets built (reuse, build, wrap open-source).

```
┌─────────────────────────────────────────────────┐
│  ASSEMBLY                         40% Complete  │
│                                                 │
│  Pieces: 12/30 defined                          │
│                                                 │
│  ✅ Script Generator       defined, reuse Tool#47│
│  ✅ Video Renderer         defined, GitHub wrap  │
│  ✅ Voice Synth            defined, API (Bark)   │
│  🔨 Thumbnail Gen          in progress          │
│  ⬜ Upload Scheduler       not started           │
│  ⬜ Analytics Connector    not started           │
│  ... (+24 more)                                 │
│                                                 │
│  Reusable from existing: 4 pieces               │
│  GitHub wraps needed: 3 pieces                  │
│  Build from scratch: 5 pieces                   │
│  Undefined: 18 pieces                           │
│                                                 │
│  To-Do:                                         │
│  ☐ Define upload scheduling logic               │
│  ☐ Research analytics API options               │
│  ☐ Decide on thumbnail style/template           │
│                                                 │
│  [Mark Assembly Complete]                       │
└─────────────────────────────────────────────────┘
```

### Phase 3: BUILDING
**What happens**: The pieces actually get constructed. Tools go through YT Lab. Processes get coded. Components get wired. This is where the work happens.

**Dashboard shows**:
- Build progress per piece (not started / in progress / complete / failed)
- Overall build completion percentage
- Active builds (what's currently being worked on)
- Blockers (what's stuck and why)
- Test results per piece as they complete
- Resource usage (API calls, tokens, etc.)

**What "complete" means for this phase**: Every piece is built and passes its individual tests.

```
┌─────────────────────────────────────────────────┐
│  BUILDING                         65% Complete  │
│                                                 │
│  Built: 19/30 pieces                            │
│                                                 │
│  ● Script Generator        ✅ built + tested   │
│  ● Video Renderer          ✅ built + tested   │
│  ● Voice Synth             ✅ built + tested   │
│  ● Thumbnail Gen           🔨 building...      │
│  ● Upload Scheduler        ✅ built + tested   │
│  ● Analytics Connector     ⬜ queued            │
│  ... (+24 more)                                 │
│                                                 │
│  Active now: Thumbnail Gen (est. 12 min)        │
│  Blockers: 0                                    │
│  Failed: 1 (Voice Synth v1 — rebuilt as v2 ✅) │
│                                                 │
│  To-Do:                                         │
│  ☐ Build Analytics Connector                    │
│  ☐ Build Channel Manager                        │
│  ☐ Wire SEO Engine output to Script Gen input   │
│                                                 │
│  [Mark Building Complete]                       │
└─────────────────────────────────────────────────┘
```

### Phase 4: TESTING
**What happens**: All pieces are built. Now test them together. End-to-end runs. Does the whole flow work? Do connections pass data correctly? Does the output match expectations?

**Dashboard shows**:
- Test scenarios defined vs. executed
- Pass/fail per test
- End-to-end flow test results
- Data flow verification (did the right data move between the right nodes?)
- Performance metrics (speed, cost per run, error rate)
- Human review checkpoints (sample outputs for approval)

**What "complete" means for this phase**: All tests pass. Human has reviewed sample outputs and approved. Ready to go live.

```
┌─────────────────────────────────────────────────┐
│  TESTING                          80% Complete  │
│                                                 │
│  Tests: 8/10 passing                            │
│                                                 │
│  ✅ Script generation quality     PASS          │
│  ✅ Video renders correctly       PASS          │
│  ✅ Voice sounds natural          PASS          │
│  ✅ Thumbnail matches brand       PASS          │
│  ✅ Upload to YouTube works       PASS          │
│  ✅ SEO tags applied correctly    PASS          │
│  ✅ Full pipeline end-to-end      PASS          │
│  ❌ Analytics tracking            FAIL          │
│     → tracking pixel not firing                 │
│  ✅ Schedule posts correctly      PASS          │
│  ⬜ Load test (50 videos)         NOT RUN       │
│                                                 │
│  Sample outputs for review:                     │
│  [▶ Watch Sample Video 1] [▶ Sample 2]         │
│  Owner approved: ✅ Yes                         │
│                                                 │
│  [Mark Testing Complete]                        │
└─────────────────────────────────────────────────┘
```

### Phase 5: RUNNING (Live Operations)
**What happens**: Module is live. Producing real output. Real numbers flowing.

**Dashboard shows**:
- Real-time performance metrics (output count, success rate, errors)
- Business metrics (clicks, revenue, conversions — whatever this module drives)
- Health status (all systems green/yellow/red)
- Recent activity log
- Cost tracking (API spend, resource usage)
- Improvement proposals (from the continuous improvement engine)
- Quick actions (pause, scale up, update, clone)

**What "complete" means for this phase**: It doesn't. This phase runs indefinitely. "Success" is defined by the Objective node it serves.

```
┌─────────────────────────────────────────────────┐
│  RUNNING                     ● ALL SYSTEMS GO   │
│                                                 │
│  Today:                                         │
│  📹 Videos produced: 47                         │
│  📤 Videos uploaded: 47                         │
│  👁  Total views: 2,340                         │
│  🖱  Clicks to offer: 156                       │
│  💰 Est. revenue: $5,460                        │
│                                                 │
│  This week:                                     │
│  📹 329 videos | 👁 18.2K views | 🖱 1,089 clicks│
│  💰 $38,115 est. revenue                        │
│                                                 │
│  Health:                                        │
│  ● Script Gen      🟢 healthy                  │
│  ● Video Render    🟢 healthy                  │
│  ● Voice Synth     🟡 slow (queue backed up)   │
│  ● Uploader        🟢 healthy                  │
│  ● Analytics       🟢 healthy                  │
│                                                 │
│  Improvements available: 2                      │
│  → "New voice model 40% faster" [Approve]       │
│  → "Better thumbnail CTR template" [Approve]    │
│                                                 │
│  [⏸ Pause] [📈 Scale Up] [🔄 Update] [📋 Clone]│
└─────────────────────────────────────────────────┘
```

---

## Dashboard Zoom Levels

### Level 1: God View (All Objectives)
See every objective and its overall status. One screen.

```
┌──────────────────────────────────────────────────────┐
│  ATTACK FORGE — ALL OBJECTIVES                       │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐     │
│  │ Affiliate Traffic  │  │ Tool Library        │     │
│  │ ● RUNNING          │  │ 🔨 BUILDING         │     │
│  │ 1,089 clicks/wk    │  │ 47/500 tools        │     │
│  │ $38K est/wk        │  │ 9.4% complete       │     │
│  └────────────────────┘  └────────────────────┘     │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐     │
│  │ Product Suite      │  │ B2B Enterprise      │     │
│  │ ⬜ PLANNING         │  │ ⬜ PLANNING          │     │
│  │ 0/20 products      │  │ 0 clients           │     │
│  │ Not started        │  │ Not started         │     │
│  └────────────────────┘  └────────────────────┘     │
│                                                      │
│  Total modules: 23 | Running: 4 | Building: 8       │
│  Total to-dos: 47 (12 urgent)                        │
└──────────────────────────────────────────────────────┘
```

### Level 2: Objective View (One Objective, All Its Strategies)
Click into an objective. See all strategies and campaigns under it.

### Level 3: Campaign View (One Campaign, All Its Processes)
Click into a campaign. See all processes, tools, connections.

### Level 4: Module View (One Module, Full Detail)
Click into any module. See the 5-phase tabs (Ingestion → Assembly → Building → Testing → Running). Full dashboard for that module.

### Level 5: Component View (One Piece, Granular Detail)
Click into a component. See its code, its config, its connections, its health, its logs.

**Every level has the same structure**: status, completion %, to-do list, metrics, connections. Just different granularity.

---

## The To-Do System

Every module at every level has a to-do list. To-dos can exist at any level and roll up.

### To-Do Properties
```
- Task description
- Assigned to: (human / AI / waiting)
- Priority: (urgent / normal / low)
- Phase: (ingestion / assembly / building / testing / running)
- Blocking: (is this blocking something else?)
- Parent module: (which module does this belong to)
```

### Roll-Up
- Component to-dos roll up into Tool to-dos
- Tool to-dos roll up into Process to-dos
- Process to-dos roll up into Campaign to-dos
- Campaign to-dos roll up into Strategy to-dos
- Strategy to-dos roll up into Objective to-dos

So at the God View, you see: "Total to-dos: 47 (12 urgent)" — that's the sum of everything. Click in and drill down to find exactly what needs attention.

### The Master To-Do View
One page that shows ALL to-dos across all modules, sortable by:
- Priority
- Module
- Phase
- Who's responsible (human vs. AI)
- What's blocking other work

This is the "what do I need to do RIGHT NOW" view.

---

## The Template System (Clone & Reuse)

You said it: "Once you have a system that works, you can copy the template."

### How Templates Work

1. **A module reaches RUNNING phase and proves successful** (metrics meet success criteria)
2. **"Save as Template" button** — captures:
   - The full module structure (all sub-modules, components, connections)
   - The prompts and configurations that worked
   - The success criteria and test scenarios
   - The tools and GitHub repos used
   - NOT the specific content (that's unique per instance)
3. **Template goes into the Template Library**
4. **"Clone from Template" button** — creates a new module with:
   - Same structure, same components, same connections
   - Blank content slots (fill in your new topic/niche/product)
   - Same success criteria and test scenarios
   - Pre-wired to the same tool pipeline

### Example: YouTube Channel Template

You build the first automated YouTube channel for Jonathan's affiliate offer. It works. It's producing 50 videos/day, getting clicks, earning commissions.

**Save as template**: "Automated Tutorial YouTube Channel"

Now clone it:
- Clone #1: YouTube channel for a different affiliate product
- Clone #2: YouTube channel for YOUR product
- Clone #3: YouTube channel for a client's product
- Clone #4: YouTube channel for a different niche entirely

Each clone starts at the Ingestion phase — you feed in the new topic's videos and content. But the entire structure, pipeline, and automation is already built. You're just filling in the blanks.

**This is how 1 channel becomes 20 channels.** Same machine, different fuel.

---

## Success Criteria Framework

Every module needs to know what "done" looks like. Without this, the dashboard can't show completion.

### Success Criteria by Type

| Node Type | What Success Looks Like |
|-----------|------------------------|
| **Objective** | Measurable metric hit (e.g., "10,000 clicks achieved") |
| **Strategy** | All campaigns under it are running and meeting targets |
| **Campaign** | All processes are running, metrics above minimum thresholds |
| **Process** | All steps execute without errors, output meets quality bar |
| **Tool** | Runs autonomously, output passes quality checks, uptime > 99% |
| **Component** | Does its one job correctly every time |
| **Resource** | Available, up-to-date, accessible |
| **Checkpoint** | Human has reviewed and approved |
| **Monitor** | Reporting accurately, alerting on issues |

### How Completion Gets Calculated

Each phase has its own completion logic:
- **Ingestion**: (topics covered / total topics identified) × 100
- **Assembly**: (pieces defined / total pieces needed) × 100
- **Building**: (pieces built and tested / total pieces) × 100
- **Testing**: (tests passing / total tests) × 100
- **Running**: Not a % — it's a health score based on metrics vs. success criteria

---

## Connection Points Between Modules

When you clone a YouTube channel template and run 5 of them, they're 5 separate modules. But they share:

### Shared Resources
- Same voice model configuration
- Same thumbnail template library
- Same SEO keyword database
- Same affiliate tracking system

### Shared Data Bus
- All channels publish to a "total clicks" channel that feeds the Objective dashboard
- All channels publish performance data that feeds the optimization engine
- The SEO engine reads from all channels to avoid keyword overlap

### Shared Components
- The Video Renderer component can be shared (one instance, multiple consumers)
- The Upload Engine is shared
- Analytics tracking is shared

This is the sideways connection system from the Infrastructure Framework — modules that aren't chained together but share data and resources.

---

## The Affiliate Funnel As a Module Chain

Here's what the full Jonathan affiliate play looks like as Attack Forge modules:

```
OBJECTIVE: $350K in affiliate commissions
│
├── STRATEGY: Multi-channel organic + paid traffic
│   │
│   ├── CAMPAIGN: YouTube Tutorial Blitz
│   │   ├── PROCESS: Automated Video Creation
│   │   │   ├── TOOL: Script Generator
│   │   │   ├── TOOL: Video Renderer
│   │   │   ├── TOOL: Voice Synthesizer
│   │   │   ├── TOOL: Thumbnail Generator
│   │   │   └── TOOL: YouTube Uploader
│   │   ├── PROCESS: SEO Optimization
│   │   │   └── TOOL: Keyword Engine
│   │   └── MONITOR: Channel Analytics
│   │
│   ├── CAMPAIGN: Viral Short-Form
│   │   ├── PROCESS: TikTok Content Machine
│   │   ├── PROCESS: Instagram Reels Machine
│   │   └── MONITOR: Viral Metrics
│   │
│   ├── CAMPAIGN: Paid Ads (Phase 2 — after first revenue)
│   │   ├── PROCESS: Ad Creative Generation
│   │   ├── PROCESS: Audience Targeting
│   │   └── MONITOR: ROAS Tracker
│   │
│   └── CAMPAIGN: Lead Magnet Funnel
│       ├── PROCESS: Free Tool Giveaways (your tools as bonuses)
│       ├── PROCESS: Email Sequence
│       ├── CHECKPOINT: Review leads before upsell
│       └── PROCESS: Upsell Pipeline (your products after Jonathan's)
│
├── STRATEGY: Product Development (parallel)
│   ├── CAMPAIGN: Build Tool Suite
│   │   └── (50 tools in subscription model)
│   └── CAMPAIGN: High-Ticket Offers
│       └── ($5K-$20K consulting packages)
│
└── MONITOR: Revenue Dashboard
    ├── Affiliate commissions tracking
    ├── Direct product sales
    ├── Email list growth
    └── Overall ROI per channel
```

Every single item in that tree is a module with its own dashboard, its own phase tabs, its own to-do list, its own success criteria. Zoom in on any one. Zoom out to see the whole picture.

---

## The Pipeline Stages (Post-Jonathan)

You described the full customer journey. Here it is as a module chain:

```
VIEWER sees content (YouTube/TikTok/Instagram)
    ↓
LEAD MAGNET: Free tool or resource (your creation)
    ↓
CHECKPOINT: Did they engage with the lead magnet?
    ↓
AFFILIATE OFFER: Jonathan's product (your affiliate link)
    ↓  [You earn commission here]
    ↓
EMAIL CAPTURE: They're now in YOUR system
    ↓
EMAIL SEQUENCE: Nurture + value delivery
    ↓
YOUR PRODUCTS: Tool subscriptions, individual tools
    ↓
UPSELL: Premium tools, bundles
    ↓
HIGH-TICKET: Consulting, custom builds ($5K-$20K)
    ↓
REPEAT: They stay in the ecosystem, get updates, buy more
```

Each arrow is a connection. Each box is a module. The whole thing is one Campaign-level module that you can see on one dashboard, or drill into any step.

---

## Implementation Notes

### What This Means for the UI

The Attack Forge page needs:

1. **Universal Module Component** — one React component that renders ANY module at ANY zoom level. It knows:
   - What phase it's in (5 tabs)
   - Its completion %
   - Its to-do list
   - Its connections
   - Its metrics
   - Its children (sub-modules)

2. **Zoom/Drill Component** — click to go deeper, breadcrumb to go back up. Like file explorer but for modules.

3. **Visual Map Component** — the N8N-style canvas showing modules as boxes with connection lines. Reuses the concept from the DependencyGraph component that already exists in the codebase.

4. **To-Do Aggregator** — pulls to-dos from all modules, sorts, filters, shows the "what do I do right now" view.

5. **Template Manager** — save working modules as templates, browse template library, clone into new modules.

### What Stays The Same

- YT Lab still makes tools — it just becomes one builder that Attack Forge can route to
- The tool registry still tracks tools — but now tools are just one node type in Attack Forge
- The workspace chat still works — it's where you talk to AI about building/debugging modules
- The existing data models extend — they don't get replaced

### What's New

- Module data model (universal container with phases, to-dos, success criteria, connections)
- Visual map renderer
- Phase-based dashboard renderer
- Template system
- To-do roll-up system
- Multi-level zoom navigation

---

*Every module is its own little world with its own dashboard. Zoom out and they're boxes on a map. Zoom in and they're full operational control centers. Same structure, fractal — works at every scale from a single component to an entire business objective.*
