# Attack Forge: Interactive Builder — Iterative AI + Human Construction

> **Status**: UX Design Spec
> **Date**: March 13, 2026
> **Core Insight**: You don't one-shot describe a system. You lay out the big picture, then drill in node by node, iterating with AI. AI builds 80%, human dials in the last 20%. Either party can work at any time — AI filling things out, human grabbing nodes and rewiring, back and forth until it's right.

---

## The Problem With One-Shotting

Traditional approach: "Describe everything you want in one prompt and the AI builds it."

That doesn't work for complex systems because:
- You don't KNOW everything upfront
- The system is too big to describe in one pass
- Details emerge as you build
- Some things are easier to SHOW than TELL (drag a node here, connect this to that)
- The AI gets most of it right but needs human correction on the last 20%

**The solution: Multi-pass iterative building with mixed AI + human input at every step.**

---

## How Building Actually Works

### Step 1: Throw In The Big Concepts

You start loose. Just name the big pieces:

```
"I need a YouTube channel, products and tools to sell,
a lead magnet funnel, an email system, and an affiliate pipeline."
```

AI creates 5 top-level nodes on the canvas. Big boxes. No detail yet. Just the skeleton.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  YouTube     │    │  Products &  │    │  Lead Magnet │
│  Channel     │    │  Tools       │    │  Funnel      │
└──────────────┘    └──────────────┘    └──────────────┘

┌──────────────┐    ┌──────────────┐
│  Email       │    │  Affiliate   │
│  System      │    │  Pipeline    │
└──────────────┘    └──────────────┘
```

### Step 2: AI Takes First Pass

AI looks at each top-level node and fills in what it can figure out on its own. For "YouTube Channel" it might generate:

```
YouTube Channel
├── Channel Branding (logo, banner, about)
├── Content Strategy (topics, posting schedule)
├── Video Production Pipeline
│   ├── Script Writing
│   ├── Voice Generation
│   ├── Video Rendering
│   └── Thumbnail Creation
├── SEO & Discovery
│   ├── Keyword Research
│   └── Tag Optimization
├── Upload & Scheduling
└── Analytics & Tracking
```

It does this for ALL 5 top-level nodes. Now you have a rough framework. Maybe 60-80% right.

### Step 3: Human Reviews and Corrects

You zoom into the canvas and see what AI laid out. Three scenarios:

**A) It's right** — move on, drill deeper into something else.

**B) It's almost right** — use the selection tool (lasso/box select) to highlight the part that needs fixing. A mini chat opens for JUST that section:

```
┌─────────────────────────────────────────────────────────┐
│  Selected: Video Production Pipeline                    │
│                                                         │
│  You: "This is close but I'm not doing traditional      │
│  video rendering. I'm using AI-generated tutorial        │
│  walkthroughs with screen recordings. And I need a      │
│  B-roll library component."                             │
│                                                         │
│  AI: "Got it. Updated the pipeline to:"                 │
│  ├── Script Writing                                     │
│  ├── Voice Generation                                   │
│  ├── Screen Recording Automation                        │
│  ├── B-Roll Asset Library                               │
│  ├── Video Assembly (compositing layers)                │
│  └── Thumbnail Creation                                 │
│                                                         │
│  You: "Yes, that's it."                                 │
│  [Apply Changes]                                        │
└─────────────────────────────────────────────────────────┘
```

Changes get applied to the canvas. Mini chat closes. You're back to the big picture.

**C) It's wrong** — just grab the nodes yourself. Drag, delete, reconnect. Sometimes it's faster to just DO it than explain it:

- Drag "Analytics" node and connect it to "Email System" instead
- Delete a node AI created that doesn't apply
- Create a new node manually and wire it in
- Rearrange the layout to match how you think about the flow

**The canvas is ALWAYS directly editable. AI suggestions are just starting points.**

---

## The Asset Checklist System

Every module — at any level — has an asset checklist. These are all the things that need to exist for the module to work.

### What Counts As An "Asset"

Not just graphics. EVERYTHING the module needs:

| Asset Type | Examples |
|-----------|---------|
| **Visual** | Logo, banner, thumbnails, brand colors, style guide |
| **Copy** | Scripts, descriptions, email templates, ad copy, CTAs |
| **Code** | Python scripts, automation code, API integrations, webhooks |
| **Content** | Video files, audio files, B-roll clips, music tracks |
| **Data** | Keywords, rankings, competitor analysis, audience research |
| **Prompts** | AI prompts for generation, system prompts, template prompts |
| **Config** | API keys, account credentials, platform settings |
| **Pages** | Landing pages, opt-in pages, sales pages, thank you pages |
| **Sequences** | Email sequences, follow-up flows, drip campaigns |
| **Accounts** | Platform accounts, tool subscriptions, service logins |

### How The Checklist Works

When a module is created (either by AI or human), the system generates an asset checklist:

```
┌─────────────────────────────────────────────────────────┐
│  YouTube Channel — Asset Checklist                      │
│                                                         │
│  VISUAL ASSETS                          3/7 complete    │
│  ✅ Channel logo (400x400)                              │
│  ✅ Channel banner (2560x1440)                          │
│  ✅ Brand color palette                                 │
│  ⬜ Thumbnail template (main style)                     │
│  ⬜ Thumbnail template (tutorial style)                 │
│  ⬜ End screen template                                 │
│  ⬜ Watermark                                           │
│                                                         │
│  COPY ASSETS                            1/5 complete    │
│  ✅ Channel description                                 │
│  ⬜ Default video description template                  │
│  ⬜ About page text                                     │
│  ⬜ Pinned comment template                             │
│  ⬜ Community post templates (3 variations)             │
│                                                         │
│  CODE ASSETS                            0/4 complete    │
│  ⬜ Script generation prompt                            │
│  ⬜ Voice synthesis config                              │
│  ⬜ Upload automation script                            │
│  ⬜ Analytics tracking pixel                            │
│                                                         │
│  DATA ASSETS                            2/3 complete    │
│  ✅ Keyword research (500 keywords)                     │
│  ✅ Competitor channel analysis                         │
│  ⬜ Content calendar (30 days)                          │
│                                                         │
│  ACCOUNTS                               1/2 complete    │
│  ✅ YouTube account created                             │
│  ⬜ YouTube API access configured                       │
│                                                         │
│  Overall: 7/21 assets ready (33%)                       │
│                                                         │
│  [+ Add Asset]  [AI: Fill What You Can]                 │
└─────────────────────────────────────────────────────────┘
```

### AI-Assisted Asset Filling

The "AI: Fill What You Can" button is key. When clicked:

1. AI looks at what's missing
2. For things it CAN generate (copy, prompts, templates, basic code, keyword lists) — it generates them and marks them as "AI-generated, needs review"
3. For things it CAN'T generate (logos, account creation, API keys) — it marks them as "human required" and optionally suggests tools or services
4. Human reviews AI-generated assets, approves or edits them

```
┌─────────────────────────────────────────────────────────┐
│  AI filled 8 of 14 missing assets                       │
│                                                         │
│  🤖 Default video description template     [Review]     │
│  🤖 About page text                        [Review]     │
│  🤖 Pinned comment template                [Review]     │
│  🤖 Community post templates (3)           [Review]     │
│  🤖 Script generation prompt               [Review]     │
│  🤖 Voice synthesis config                 [Review]     │
│  🤖 Upload automation script               [Review]     │
│  🤖 Content calendar (30 days)             [Review]     │
│                                                         │
│  👤 Human needed for 6 assets:                          │
│  → Thumbnail templates (need brand style decisions)     │
│  → End screen template (need brand style decisions)     │
│  → Watermark (need brand asset)                         │
│  → Analytics tracking pixel (need account setup)        │
│  → YouTube API access (need account setup)              │
│  → Channel logo (already uploaded ✅)                   │
└─────────────────────────────────────────────────────────┘
```

---

## The Selection Tool (Lasso / Box Select)

This is the key interaction pattern for targeted refinement.

### How It Works

1. You're looking at the canvas — nodes, connections, the whole map
2. You draw a box (or lasso) around a section you want to work on
3. A mini chat panel opens, scoped to JUST those selected nodes
4. You have a conversation with AI about that specific section
5. AI proposes changes — shown as a preview overlay on the canvas
6. You approve, modify, or reject
7. Changes apply, mini chat closes, you're back to the full canvas

### Why This Matters

Traditional approach: "AI, change the video production pipeline to use screen recordings instead of rendered video."

Problem: AI might misinterpret which pipeline, what you mean by screen recordings, how that affects downstream nodes.

Selection tool approach:
1. **You visually select** the exact nodes you mean (no ambiguity about WHICH part)
2. **You describe the change** in the context of what you can both see
3. **AI shows the change as a preview** before applying (no surprises)
4. **You iterate in-place** if the preview isn't right

It's like pointing at something on a whiteboard and saying "change THIS" versus describing it over the phone.

### Interaction Modes

| Mode | How | When |
|------|-----|------|
| **Select + Chat** | Draw box around nodes, type in mini chat | When you need to explain a change |
| **Direct Drag** | Grab a node, move it, connect to another node | When it's faster to just show it |
| **Quick Add** | Double-click empty space, type node name | When you know exactly what to add |
| **Quick Delete** | Select node, press Delete | When something doesn't belong |
| **Quick Connect** | Drag from one node's port to another | When you need to wire things together |
| **AI Expand** | Right-click a node → "AI: Break this down" | When you want AI to detail a node's internals |
| **AI Suggest** | Right-click empty space → "AI: What's missing?" | When you want AI to find gaps |

---

## The Iterative Refinement Loop

Building a full system is NOT a single pass. It's this loop, repeated at every zoom level:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   1. DESCRIBE (human gives concepts/ideas)           │
│          ↓                                           │
│   2. AI BUILDS (first pass — 60-80% right)           │
│          ↓                                           │
│   3. HUMAN REVIEWS (zoom in, look at what AI made)   │
│          ↓                                           │
│   4. CORRECT (select area, chat, drag, rewire)       │
│          ↓                                           │
│   5. AI ADJUSTS (applies changes, fills gaps)        │
│          ↓                                           │
│   6. REPEAT until this level is solid                │
│          ↓                                           │
│   7. DRILL DEEPER (pick a node, go one level down)   │
│          ↓                                           │
│   → Back to step 1 for the deeper level              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Level-by-Level Example

**Pass 1 — Objective level**: "I want to make money through affiliate marketing and my own products using automated YouTube content."
→ AI creates: YouTube Channel, Products, Lead Funnel, Email System, Affiliate Pipeline
→ Human: "Looks right. Let me drill into YouTube Channel."

**Pass 2 — Strategy level (YouTube Channel)**: AI breaks it down into Branding, Content Strategy, Video Pipeline, SEO, Upload, Analytics.
→ Human selects Video Pipeline: "I'm doing AI-generated tutorials, not traditional video. Screen recording style with voiceover."
→ AI adjusts. Human approves.

**Pass 3 — Process level (Video Pipeline)**: AI breaks down into Script Gen, Voice Gen, Screen Recording, Assembly, Thumbnails.
→ Human: "Add a B-roll library. And the screen recording isn't automated yet — that's a manual step for now with a CHECKPOINT."
→ AI adjusts, adds B-roll node and Checkpoint node.

**Pass 4 — Component level (Script Gen)**: AI shows the prompt template, the keyword input, the output format.
→ Human: "The prompt needs to focus on tutorial walkthroughs, not reviews. Here's an example of the tone I want: [pastes example]"
→ AI updates the prompt asset.

Each pass goes deeper. Each pass is a conversation. The system builds layer by layer.

---

## Canvas Behaviors

### When AI Adds Nodes
- New nodes appear with a subtle glow/highlight (so you can see what changed)
- Connection lines are auto-routed to avoid overlap
- Layout auto-adjusts to accommodate new nodes (but human can always reposition)

### When Human Drags Nodes
- Connections follow the node (rubberbanding)
- Snapping to grid (optional)
- Nodes can be grouped (select multiple, group into a cluster)
- Undo/redo for all manual changes

### When Conflicts Arise
- If AI suggests removing a node the human placed: warning, not auto-remove
- If human connects two nodes that don't logically fit: AI suggests a bridge node or explains the issue
- If a node has dependencies that would break: show those before allowing delete

### Version History
- Every change (AI or human) is versioned
- Can roll back to any previous state
- Can compare two versions side-by-side
- Can fork: "Try two different approaches and compare"

---

## The Mini Chat Pattern

The mini chat is the bridge between visual and verbal interaction.

### When It Opens
- Box-select / lasso on the canvas
- Right-click → "Discuss this"
- Click the chat icon on any node
- Keyboard shortcut while node is selected

### What It Shows
- The selected nodes, highlighted on the canvas behind it
- Chat input with context already loaded ("You've selected: Video Pipeline, containing 5 sub-nodes")
- Previous mini-chats for this same selection (conversation history per node/area)

### What You Can Do In It
- Describe changes in natural language
- Ask questions ("What should go here?", "What's missing?")
- Give examples ("Here's what I mean: [paste]")
- Approve AI suggestions ("Yes, do that")
- Reject and redirect ("No, I meant X not Y")

### What Happens When It Closes
- Changes from the chat are applied to the canvas
- The conversation is saved (can reopen later to see the history)
- Modified nodes get a "recently updated" indicator

---

## How This Fits Into The Module Lifecycle

The Interactive Builder is primarily used in **Phase 1 (Ingestion)** and **Phase 2 (Assembly)**:

| Phase | Builder's Role |
|-------|---------------|
| **Ingestion** | Feed in source material. AI extracts concepts. Human reviews. Canvas shows what's been covered and what gaps remain. |
| **Assembly** | AI lays out the component structure. Human iterates via select+chat and direct manipulation until the blueprint is solid. Asset checklists get generated. |
| **Building** | Builder becomes read-mostly. Shows build progress on each node. Can still restructure if you realize something's wrong. |
| **Testing** | Builder shows test results overlaid on nodes (green/red). Failed nodes can be selected for debugging chat. |
| **Running** | Builder shows live metrics overlaid on nodes. Health indicators on each connection. |

The canvas is always there. It evolves from a planning tool to a monitoring tool as the module progresses through phases.

---

*The AI builds 80%. The human fine-tunes 20%. Neither works alone. The canvas is the shared workspace where both can see, point, adjust, and iterate — as many passes as it takes, drilling deeper each time, until the system is fully specified and ready to build.*
