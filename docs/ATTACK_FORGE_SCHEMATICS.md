# Attack Forge: System Schematics

> **Status**: Visual Reference
> **Date**: March 13, 2026
> **What This Is**: Diagrams showing how all the components connect. These are the "how it flows" views. Each section below would be a different canvas view in the actual UI.

---

## Schematic 1: The Big Picture (God View)

Everything at the highest level. Six strategy blocks, one objective.

```
                        ┌─────────────────────────────┐
                        │       💰 OBJECTIVE           │
                        │  Automated Revenue Empire    │
                        │                             │
                        │  Target: $350K+ affiliate   │
                        │  + product revenue/year     │
                        └──────────┬──────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼────────┐ ┌────────▼─────────┐ ┌───────▼──────────┐
    │  📺 YOUTUBE      │ │  🎁 LEAD MAGNET  │ │  🤝 AFFILIATE    │
    │  CONTENT MACHINE │ │  FUNNEL          │ │  PIPELINE        │
    │                  │ │                  │ │  (Jonathan)      │
    │  Automated video │ │  Free tools &    │ │                  │
    │  production &    │ │  resources that  │ │  The offer that  │
    │  publishing      │ │  capture emails  │ │  earns commission│
    └────────┬─────────┘ └────────┬─────────┘ └───────┬──────────┘
             │                    │                    │
             │         ┌─────────▼──────────┐         │
             │         │  📧 EMAIL NURTURE  │         │
             │         │  SYSTEM            │         │
             │         │                    │         │
             │         │  Sequences that    │         │
             │         │  build trust &     │         │
             │         │  drive purchases   │         │
             │         └─────────┬──────────┘         │
             │                   │                    │
    ┌────────▼─────────┐ ┌──────▼───────────┐        │
    │  🛠️ YOUR OWN     │ │  ⚙️ AUTOMATION   │        │
    │  PRODUCTS        │ │  & INFRA         │        │
    │                  │ │                  │        │
    │  Tools, subs,    │ │  Prompt chains,  │        │
    │  consulting      │ │  pipelines, APIs │        │
    └──────────────────┘ └──────────────────┘        │
                                                      │
```

---

## Schematic 2: The Customer Journey (Flow View)

How a stranger becomes a customer. Left to right, one path.

```
STRANGER                                                              REPEAT BUYER
   │                                                                       │
   ▼                                                                       ▼
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  ┌──────────┐
│ SEES │───▶│ WATCHES  │───▶│ CLICKS   │───▶│ GETS     │───▶│ BUYS     │─▶│ ENTERS   │
│VIDEO │    │ CONTENT  │    │ LINK IN  │    │ FREE     │    │JONATHAN'S│  │ YOUR     │
│      │    │          │    │ DESC     │    │ TOOL     │    │ OFFER    │  │ FUNNEL   │
└──────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  └────┬─────┘
                                                 │              │              │
YouTube /                              Email     │    You earn  │    Now in    │
TikTok /                               captured  │    commission│    YOUR      │
Shorts                                 here ─────┘              │    ecosystem │
                                                                │              │
                                                                │    ┌─────────▼────────┐
                                                                │    │  📧 EMAIL NURTURE │
                                                                │    │  Value → Trust →  │
                                                                │    │  Your Products    │
                                                                │    └─────────┬────────┘
                                                                │              │
                                                        ┌───────┘    ┌────────▼────────┐
                                                        │            │  🛠️ YOUR TOOLS  │
                                                        │            │  $9-99/mo subs  │
                                                        │            └────────┬────────┘
                                                        │                     │
                                                        │            ┌────────▼────────┐
                                                        │            │  💎 HIGH-TICKET │
                                                        │            │  $5K-$20K       │
                                                        │            │  consulting     │
                                                        │            └─────────────────┘
                                                        │
                                               $$ REVENUE STREAMS $$
                                               1. Affiliate commission
                                               2. Tool subscriptions
                                               3. Individual tool sales
                                               4. Consulting packages
```

---

## Schematic 3: The Video Pipeline (Process View)

What happens when you enter one keyword. The full automation chain.

```
                    ┌─────────────┐
                    │  🔑 KEYWORD │
                    │  (one input)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  KEYWORD    │  Validates volume, competition,
                    │  ENGINE     │  finds related terms
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌─────▼─────┐ ┌───▼────────┐
     │  SCRIPT    │ │  SEO      │ │  THUMBNAIL │
     │  GENERATOR │ │  PACKAGE  │ │  GENERATOR │
     │            │ │           │ │            │
     │  Full 8min │ │  Title    │ │  3 options │
     │  tutorial  │ │  Tags     │ │  matching  │
     │  script    │ │  Desc     │ │  style     │
     └────────┬───┘ └─────┬─────┘ └───┬────────┘
              │           │            │
     ┌────────▼───┐       │            │
     │  VOICE     │       │            │
     │  SYNTH     │       │            │
     │            │       │            │
     │  Narration │       │            │
     │  audio     │       │            │
     └────────┬───┘       │            │
              │           │            │
     ┌────────▼───┐       │            │
     │  VIDEO     │       │            │
     │  ASSEMBLER │       │            │
     │            │       │            │
     │  Voice +   │       │            │
     │  Screen +  ◄── B-Roll Library   │
     │  B-roll +  │       │            │
     │  Overlays  │       │            │
     └────────┬───┘       │            │
              │           │            │
              └─────┬─────┘────────────┘
                    │
             ┌──────▼──────┐
             │  UPLOAD     │  Video + SEO + Thumbnail
             │  AUTOMATION │  all assembled, scheduled
             └──────┬──────┘
                    │
           ┌────────┼────────┐
           │        │        │
    ┌──────▼──┐ ┌───▼────┐ ┌▼──────────┐
    │ YOUTUBE │ │ SHORTS │ │ CROSS-POST│
    │ PUBLISH │ │ CUT    │ │ TikTok,   │
    │         │ │ 3 clips│ │ Reels, X  │
    └─────────┘ └────────┘ └───────────┘
```

---

## Schematic 4: The Email System (Sequence View)

What happens after someone enters your funnel.

```
     ┌──────────────────┐
     │  📧 NEW SUBSCRIBER│
     │  (from any source)│
     └────────┬─────────┘
              │
              ▼
     ┌────────────────────┐
     │  TAG & SEGMENT     │  Which lead magnet? Which video?
     │  Based on source   │  Which topic? Tag accordingly.
     └────────┬───────────┘
              │
              ▼
     ┌────────────────────┐    Day 0
     │  WELCOME EMAIL     │───────────────────────────────────┐
     │  Deliver lead mag  │    "Here's your free tool +       │
     │  + introduce self  │     who I am & what I do"         │
     └────────┬───────────┘                                   │
              │                                               │
              ▼                                               │
     ┌────────────────────┐    Days 1-5                       │
     │  VALUE SEQUENCE    │───────────────────────────────────┤
     │  3-5 pure value    │    Tips, insights, quick wins     │
     │  emails            │    NO selling yet                 │
     └────────┬───────────┘                                   │
              │                                               │
              ▼                                               │
     ┌────────────────────┐    Days 6-10                      │
     │  AFFILIATE OFFER   │───────────────────────────────────┤
     │  Jonathan's product│    Social proof, bonuses,         │
     │  3-email sequence  │    urgency, transformation story  │
     └────────┬───────────┘                                   │
              │                                               │
         ┌────┴────┐                                          │
         │         │                                          │
    ┌────▼───┐ ┌───▼────┐                                     │
    │ BOUGHT │ │ DIDN'T │                                     │
    │        │ │ BUY    │                                     │
    └────┬───┘ └───┬────┘                                     │
         │         │                                          │
         │    ┌────▼────────────┐   Days 14-20                │
         │    │  SOFT FOLLOW-UP │──────────────────────────────┤
         │    │  Different angle│   "Here's a result someone  │
         │    │  or testimonial │    got using this..."        │
         │    └────┬────────────┘                              │
         │         │                                          │
         ▼         ▼                                          │
    ┌────────────────────┐    Days 20+                        │
    │  YOUR PRODUCTS     │────────────────────────────────────┤
    │  Upsell sequence   │    "Now that you know the basics,  │
    │  Your tools/subs   │     here's how to go further..."   │
    └────────┬───────────┘                                    │
             │                                                │
             ▼                                                │
    ┌────────────────────┐    Ongoing                         │
    │  NURTURE LOOP      │────────────────────────────────────┘
    │  Weekly value email │
    │  + occasional offer │    Never stops. Always providing
    │  + new content      │    value + monetizing.
    └─────────────────────┘


    ┌──────────────────────────────────────┐
    │  DORMANT SUBSCRIBERS (30+ days idle) │
    │                                      │
    │  → Re-engagement sequence            │
    │  → Win back or unsubscribe           │
    │  → Keep list clean                   │
    └──────────────────────────────────────┘
```

---

## Schematic 5: The Prompt Chain Architecture (Infrastructure View)

Where prompts live in the system. Almost everything runs on prompts.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MASTER PROMPT LIBRARY                         │
│                                                                 │
│  Every prompt in the system lives here. Versioned. Tested.      │
│  A/B tested. The "fuel" for the entire machine.                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VIDEO PROMPTS              EMAIL PROMPTS                       │
│  ├─ Script Gen (tutorial)   ├─ Welcome email                    │
│  ├─ Script Gen (comparison) ├─ Value email (tips)               │
│  ├─ Script Gen (listicle)   ├─ Affiliate pitch                  │
│  ├─ Title optimizer         ├─ Upsell sequence                  │
│  ├─ Description writer      ├─ Re-engagement                    │
│  ├─ Tag generator           └─ Broadcast template               │
│  ├─ Thumbnail concept                                           │
│  └─ Shorts repurposer      PAGE PROMPTS                        │
│                             ├─ Landing page headline             │
│  SEO PROMPTS                ├─ Landing page body                 │
│  ├─ Keyword expansion       ├─ Sales page copy                   │
│  ├─ Competition analysis    ├─ Opt-in page                       │
│  └─ Content gap finder      └─ Thank you page                    │
│                                                                 │
│  PRODUCT PROMPTS            META PROMPTS                        │
│  ├─ Tool description        ├─ Prompt improver (meta!)           │
│  ├─ Feature list            ├─ A/B test analyzer                 │
│  ├─ Demo script             └─ Output quality scorer             │
│  └─ Onboarding email                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

How prompts chain:

  KEYWORD ──▶ [Keyword Expansion Prompt]
                    │
                    ▼
             Expanded keywords + topic angle
                    │
                    ├──▶ [Script Gen Prompt] ──▶ Full script
                    │
                    ├──▶ [Title Optimizer Prompt] ──▶ 5 title options
                    │
                    ├──▶ [Tag Generator Prompt] ──▶ 15 tags
                    │
                    ├──▶ [Description Writer Prompt] ──▶ Templated desc
                    │
                    └──▶ [Thumbnail Concept Prompt] ──▶ Design brief
                              │
                              ▼
                    [Thumbnail Generator] ──▶ 3 images

  EVERYTHING cascades from one input.
  EVERYTHING runs on prompts.
  Change a prompt = change the output of every future video.
```

---

## Schematic 6: The Template & Clone System (Replication View)

How one working system becomes many.

```
  BUILD FIRST INSTANCE                    CLONE & CUSTOMIZE
  ──────────────────                      ─────────────────

  ┌─────────────────┐
  │ YouTube Channel  │
  │ "AI Tools Niche" │
  │                  │
  │ All 76 components│    ──────▶  Save as Template
  │ filled out       │                    │
  │ Pipeline working │                    ▼
  │ Revenue flowing  │           ┌────────────────────┐
  └─────────────────┘           │  TEMPLATE LIBRARY   │
                                │                    │
                                │  "Automated YT     │
                                │   Channel v1.0"    │
                                │                    │
                                │  Structure: ✅      │
                                │  Prompts: ✅        │
                                │  Pipeline: ✅       │
                                │  Success criteria:✅│
                                └────────┬───────────┘
                                         │
                    ┌────────────────┬────┴────┬────────────────┐
                    │                │         │                │
                    ▼                ▼         ▼                ▼
           ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
           │ Clone #1     │ │ Clone #2   │ │ Clone #3   │ │ Clone #4   │
           │ Fitness niche│ │ Finance    │ │ Cooking    │ │ Client's   │
           │              │ │ niche      │ │ niche      │ │ business   │
           │ Same machine │ │ Same       │ │ Same       │ │ Same       │
           │ New content  │ │ machine    │ │ machine    │ │ machine    │
           └──────────────┘ └────────────┘ └────────────┘ └────────────┘

  What changes per clone:
  ✎ Keywords/topics (new niche)
  ✎ Branding (logo, colors, name)
  ✎ Affiliate links (different offers)
  ✎ Content angle (different audience)

  What stays the same:
  ═ Video production pipeline
  ═ Upload automation
  ═ SEO optimization system
  ═ Email sequences (structure)
  ═ Analytics dashboards
  ═ Prompt chains (adapted but same structure)
```

---

## Schematic 7: Concurrent Operations (Concert View)

What runs simultaneously once the system is live.

```
  ALWAYS RUNNING (concert mode — parallel operations)
  ═══════════════════════════════════════════════════

  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 🔍 KEYWORD   │  │ 📊 ANALYTICS │  │ 📧 EMAIL     │
  │ ENGINE       │  │ MONITOR      │  │ DRIP         │
  │              │  │              │  │              │
  │ Always       │  │ Always       │  │ Always       │
  │ scanning for │  │ tracking     │  │ sending      │
  │ new topics   │  │ performance  │  │ sequences    │
  └──────────────┘  └──────────────┘  └──────────────┘

  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ 📅 CONTENT   │  │ 🔄 RECYCLER  │  │ 💰 REVENUE   │
  │ CALENDAR     │  │              │  │ TRACKER      │
  │              │  │ Always       │  │              │
  │ Always       │  │ repurposing  │  │ Always       │
  │ scheduling   │  │ old content  │  │ counting     │
  │ next videos  │  │ into shorts  │  │ commissions  │
  └──────────────┘  └──────────────┘  └──────────────┘


  TRIGGERED (sequence mode — fires on events)
  ═══════════════════════════════════════════

  New keyword found ──▶ Script Gen ──▶ Voice ──▶ Video ──▶ Upload
  New subscriber    ──▶ Tag ──▶ Welcome ──▶ Value sequence
  Purchase made     ──▶ Tag "buyer" ──▶ Upsell sequence
  Video hits 1K     ──▶ Create shorts ──▶ Cross-post
  30 days inactive  ──▶ Re-engagement sequence
  Revenue milestone ──▶ Notification + dashboard update
```

---

## Schematic 8: The Dashboard Hierarchy (Zoom Levels)

What you see at each zoom level.

```
  LEVEL 1: GOD VIEW
  ┌─────────────────────────────────────────────────────────┐
  │  Revenue: $12,400/mo  │  Videos: 47/day  │  Subs: 2.3K │
  │                                                         │
  │  [YT Machine: 🟢]  [Lead Funnel: 🟢]  [Affiliate: 🟢] │
  │  [Email: 🟢]       [Products: 🟡]     [Infra: 🟢]     │
  │                                                         │
  │  To-Dos: 12 remaining (3 urgent)                        │
  └─────────────────────────────────────────────────────────┘
          │
          │  Click "YT Machine"
          ▼
  LEVEL 2: STRATEGY VIEW
  ┌─────────────────────────────────────────────────────────┐
  │  YouTube Content Machine                    🟢 Running  │
  │                                                         │
  │  Videos today: 47  │  Avg views: 340  │  CTR: 6.2%     │
  │                                                         │
  │  [Channel Setup: ✅] [Video Pipeline: 🟢]              │
  │  [SEO: 🟢]          [Upload: 🟢]                       │
  │  [Analytics: 🟢]    [Cross-Post: 🟡 queue backed up]   │
  │                                                         │
  │  To-Dos: 3 (1 urgent: cross-post queue)                 │
  └─────────────────────────────────────────────────────────┘
          │
          │  Click "Video Pipeline"
          ▼
  LEVEL 3: PROCESS VIEW
  ┌─────────────────────────────────────────────────────────┐
  │  Video Production Pipeline                  🟢 Running  │
  │                                                         │
  │  Today: 47 videos produced | Avg time: 4.2 min/video   │
  │                                                         │
  │  [Keyword Engine: 🟢]  ──▶  [Script Gen: 🟢]          │
  │       ──▶  [Voice Synth: 🟡 slow]  ──▶  [Assembler: 🟢]│
  │       ──▶  [Thumbnails: 🟢]  ──▶  [Upload: 🟢]        │
  │                                                         │
  │  B-Roll Library: 2,340 clips                            │
  │  Voice queue: 12 pending (normally 0-3)                 │
  │                                                         │
  │  To-Dos: 1 (investigate voice synth slowdown)           │
  └─────────────────────────────────────────────────────────┘
          │
          │  Click "Script Gen"
          ▼
  LEVEL 4: COMPONENT VIEW
  ┌─────────────────────────────────────────────────────────┐
  │  Script Generator                           🟢 Healthy  │
  │                                                         │
  │  Scripts today: 47 | Avg length: 1,200 words            │
  │  Quality score: 8.4/10 | Rejection rate: 2%            │
  │                                                         │
  │  Prompt: "tutorial_script_v3.2" (last updated 3/10)     │
  │  [View Prompt] [Edit Prompt] [A/B Test]                 │
  │                                                         │
  │  Recent outputs:                                        │
  │  ├─ "How to automate email..." (8.7/10) ✅              │
  │  ├─ "5 AI tools for..." (8.2/10) ✅                    │
  │  ├─ "Why most people fail..." (7.9/10) ✅              │
  │  └─ "Complete guide to..." (6.1/10) ⚠️ below threshold │
  │                                                         │
  │  Config:                                                │
  │  ├─ Model: Claude Sonnet                                │
  │  ├─ Max tokens: 4,000                                   │
  │  ├─ Temperature: 0.7                                    │
  │  └─ Quality threshold: 7.0/10                           │
  │                                                         │
  │  [View Logs] [View History] [Run Manual Test]           │
  └─────────────────────────────────────────────────────────┘
```

---

*Every schematic above is a view in Attack Forge. God View is the home page. Click to zoom in. Breadcrumb to zoom out. The canvas shows the same data at every level — just different granularity. The diagrams in this doc are what the AI would generate in about two minutes when you say "I want to build an automated YouTube affiliate system."*
