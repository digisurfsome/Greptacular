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

## The Selection System (Multi-Mode)

This is the key interaction pattern for targeted refinement. Three ways to select what you're talking about:

### Selection Methods

**1. Checkbox Select (Primary)**
Every node has a checkbox. Click to check nodes — "I'm talking about THESE three things." Fastest, most precise, works at any zoom level.

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ☑ YouTube Channel                                   │
│  ☐ Products & Tools                                  │
│  ☑ Affiliate Pipeline                                │
│  ☐ Email System                                      │
│  ☐ Lead Magnet Funnel                                │
│                                                      │
│  Selected: 2 nodes                                   │
│  [Open Chat About These]                             │
│                                                      │
│  "Okay, YouTube connecting to the offer — let's      │
│   talk about just this part."                        │
└──────────────────────────────────────────────────────┘
```

This is the workhorse. Check, check, now you're scoped. The AI knows exactly what you're focused on.

**2. Freehand Lasso**
Draw a freeform shape around a cluster of nodes on the canvas. Good for grabbing a visual region when nodes are spatially grouped — circle around an area, everything inside gets selected.

**3. Box Select**
Click and drag a rectangle. Same as lasso but for rectangular regions.

All three methods do the same thing: scope the conversation to JUST those nodes. The mini chat opens with context about what's selected.

### Why This Matters — The Focus Problem

Human brains can't hold everything at once. AI context windows have limits too. A 200K context window is like 50 LOL compared to the full picture of a complex system. So you HAVE to be able to:

1. **Build the big framework first** — just the top-level nodes
2. **Drill down and focus** — check a few boxes, now we're ONLY talking about those
3. **Go deep on the small piece** — full detail conversation
4. **Pop back up** — uncheck, look at the big picture again

The checkbox/lasso system is what makes this possible. Without it, you're trying to describe "that part over there" in words and hoping the AI gets it. With it, you POINT at the things and say "these."

### Two Levels of Precision

**Rant Mode (Loose)**: Just talk. Stream of consciousness. AI listens and tries to organize your input into the right nodes on the map. Works okay for rough ideas. Gets you 60-70% of the way.

**Selection Mode (Precise)**: Check the specific nodes you're talking about. Now the AI KNOWS what you mean. No ambiguity. Gets you 90-100% of the way. For people who want to guarantee the pieces land in the right place.

Both work. Both are valid. Some people will never use checkboxes — they'll just rant and let AI sort it out. Others will click-click-click "I mean THESE three things" and get surgical precision. The system supports both, but the precision path is there for when it matters.

### Interaction Modes

| Mode | How | When |
|------|-----|------|
| **Checkbox + Chat** | Check nodes, open scoped chat | When you need to precisely scope what you're discussing |
| **Freehand Lasso + Chat** | Draw around a region, chat about it | When nodes are visually clustered and you want that whole area |
| **Box Select + Chat** | Drag rectangle, chat about selection | Same as lasso for rectangular regions |
| **Direct Drag** | Grab a node, move it, connect to another node | When it's faster to just show it |
| **Quick Add** | Double-click empty space, type node name | When you know exactly what to add |
| **Quick Delete** | Select node, press Delete | When something doesn't belong |
| **Quick Connect** | Drag from one node's port to another | When you need to wire things together |
| **AI Expand** | Right-click a node → "AI: Break this down" | When you want AI to detail a node's internals |
| **AI Suggest** | Right-click empty space → "AI: What's missing?" | When you want AI to find gaps |

---

## The Puzzle Piece Pattern

Building a complex system works exactly like building a jigsaw puzzle.

### How Humans Actually Build Puzzles

You don't start top-left and go pixel by pixel. You:
1. **Dump all the pieces out** — see what you're working with
2. **Build islands** — the face, the sky, the tree. Little clusters that make sense on their own
3. **Connect the islands** — slowly the clusters join together into bigger chunks
4. **Fill in the gaps** — the connecting tissue between the big chunks
5. **Complete the edges** — frame the whole thing

Attack Forge works the same way:

### Phase A: Dump The Pieces (Big Concepts)
Throw in everything you know. YouTube channel, products, email system, affiliate pipeline, lead magnets. Just get them on the canvas as top-level nodes. No connections yet. Just pieces on the table.

### Phase B: Build Islands (Detail The Components)
Pick one node — say YouTube Channel. Drill in. Build out everything IT needs: branding, scripts, video pipeline, SEO, thumbnails, upload automation. That's one island. Complete and self-contained. You KNOW what a YouTube channel needs — YouTube already tells you (channel art, description, videos, playlists, etc.).

Now do the same for Products & Tools. Another island. Same for Email System. Each one gets fully fleshed out on its own.

### Phase C: Connect The Islands (Wire The Relationships)
Now the interesting part. How does YouTube Channel connect to Affiliate Pipeline? Where does the lead magnet sit between the content and the offer? Where does the email capture happen? You start drawing lines between the islands.

This is where the TWO TYPES OF WORK become clear:

| Type | What You're Doing | Example |
|------|-------------------|---------|
| **Component Building** | Filling out what's INSIDE a node | "A YouTube channel needs: logo, banner, description, upload schedule..." |
| **Connection Wiring** | Defining how nodes RELATE to each other | "The YouTube video links to the landing page, which captures email, which feeds the email sequence..." |

You need the components first — you need to know what the pieces ARE before you can wire them together. But the wiring is where the real system design happens.

### Phase D: Fill The Gaps
Once islands are connected, you see what's missing. "Wait, there's no step between the YouTube video and the landing page — I need a lead magnet in between." Add the node, wire it in. The puzzle gets more complete.

### Phase E: Lock It In
When everything connects, every node has its components defined, and the flow makes sense end-to-end — that's when you have a complete blueprint. Now it becomes a template.

---

## The AI Conversation Loop

The AI doesn't just passively receive instructions. It asks questions back.

### How The Back-and-Forth Works

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   1. HUMAN DESCRIBES (rant, explain, dump ideas)     │
│          ↓                                           │
│   2. AI ORGANIZES (sorts rant into nodes/structure)  │
│          ↓                                           │
│   3. AI ASKS BACK (clarifying questions)             │
│      "You mentioned lead magnets — are these free    │
│       tools, free content, or both?"                 │
│      "When you say 'my products' — are these         │
│       the same tools from the Tool Library, or       │
│       separate offerings?"                           │
│          ↓                                           │
│   4. HUMAN ANSWERS (teaches the AI)                  │
│          ↓                                           │
│   5. AI ADJUSTS (updates the map with new info)      │
│          ↓                                           │
│   6. AI ASKS NEXT LEVEL (deeper questions)           │
│      "Got it. So the lead magnet is a free tool.     │
│       Does the user get it immediately, or do they   │
│       need to opt in with their email first?"        │
│          ↓                                           │
│   7. REPEAT until both sides agree it's complete     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Three Conversation Outcomes

**A) AI totally gets it** — it asks smart follow-up questions that show it understands. It's essentially filling in the gaps by asking the right questions. The human just confirms or corrects. Fast.

**B) AI mostly gets it** — it's close but asking slightly off-base questions. The human redirects: "No, you're thinking about it wrong. It's more like THIS." The selection tool helps here — check the nodes, point at the part that's wrong.

**C) AI doesn't get it** — it's asking questions way outside the scope. Human says "No, you don't even get what I'm talking about." This is where the human TEACHES the AI. You explain the concept differently, give examples, show connections manually. The AI learns from this context and tries again.

**The key**: The AI teaching itself by asking in-between questions. Each question it asks either confirms it understands or reveals where it's confused. Either way, progress happens. The human doesn't have to anticipate every detail — the AI's questions pull the details out.

---

## The Iterative Refinement Loop

Building a full system is NOT a single pass. It's this loop, repeated at every zoom level:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   1. DESCRIBE (human gives concepts/ideas/rant)      │
│          ↓                                           │
│   2. AI ORGANIZES (builds structure from input)      │
│          ↓                                           │
│   3. AI ASKS (clarifying questions back)             │
│          ↓                                           │
│   4. HUMAN ANSWERS (teaches, corrects, confirms)     │
│          ↓                                           │
│   5. AI ADJUSTS (updates map, fills gaps)            │
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
→ AI asks: "Are these all running simultaneously, or is there a sequence — like YouTube first, then products?"
→ Human: "YouTube first to drive traffic. Products come later as upsells."
→ AI adjusts connections to show sequence. Human approves.

**Pass 2 — Strategy level (YouTube Channel)**: AI breaks it down into Branding, Content Strategy, Video Pipeline, SEO, Upload, Analytics.
→ Human checks ☑ Video Pipeline: "I'm doing AI-generated tutorials, not traditional video. Screen recording style with voiceover."
→ AI asks: "Are the screen recordings automated, or is that a manual step for now?"
→ Human: "Manual for now, with a checkpoint."
→ AI adjusts, adds Checkpoint node.

**Pass 3 — Process level (Video Pipeline)**: AI breaks down into Script Gen, Voice Gen, Screen Recording, Assembly, Thumbnails.
→ Human: "Add a B-roll library."
→ AI asks: "Is the B-roll stock footage, AI-generated, or screen recordings you've already made?"
→ Human: "Mix of stock and my own screen recordings."
→ AI creates B-Roll Library node with two sub-sources.

**Pass 4 — Component level (Script Gen)**: AI shows the prompt template, the keyword input, the output format.
→ Human: "The prompt needs to focus on tutorial walkthroughs, not reviews. Here's an example of the tone I want: [pastes example]"
→ AI asks: "Should every script follow this tone, or do you want variations for different video types?"
→ Human: "Same tone for tutorials. Different tone for comparison videos. Let me add that as a second template."
→ AI creates two prompt template assets.

Each pass goes deeper. Each pass is a conversation. The system builds layer by layer.

---

## Known Structure Pre-Population

Some modules have **known requirements**. YouTube already defines what a channel needs. An email system already has standard components. When the AI creates one of these well-known module types, it should pre-populate the structure based on what's already known.

### How It Works

When you create a "YouTube Channel" node, AI doesn't start blank. It KNOWS:

```
YouTube Channel (pre-populated from known structure)
├── Required by YouTube:
│   ├── Channel Name
│   ├── Channel Art (banner 2560x1440)
│   ├── Profile Picture (800x800)
│   ├── Channel Description
│   ├── Channel Keywords
│   ├── Default Upload Settings
│   ├── Channel Sections / Playlists
│   └── About Page + Links
├── Required for Growth:
│   ├── Content Calendar
│   ├── SEO Strategy
│   ├── Thumbnail Style Guide
│   ├── Upload Schedule
│   └── Analytics Setup
└── Required for Automation:
    ├── Script Generation Pipeline
    ├── Video Production Pipeline
    ├── Upload Automation
    └── Performance Monitoring
```

This becomes a TEMPLATE. Once you build it out fully and prove it works, it's locked in as the "YouTube Channel Template." Every future YouTube channel you create starts from this template.

### Template Categories

| Category | What AI Pre-Populates |
|----------|----------------------|
| **YouTube Channel** | Channel setup, content pipeline, SEO, automation |
| **Landing Page** | Headline, CTA, form, thank you page, tracking |
| **Email Sequence** | Welcome email, value emails, offer email, follow-ups |
| **Product Launch** | Sales page, checkout, delivery, onboarding |
| **Lead Magnet** | Opt-in page, delivery mechanism, follow-up sequence |
| **Affiliate Campaign** | Tracking links, content strategy, promotion calendar |

When these templates exist, you don't rebuild from scratch each time. Clone the template, fill in the specifics, customize what's different. The structure is already proven.

---

## Two Types of Work (Components vs. Connections)

This is a critical distinction. When you're building a system, you're always doing one of two things:

### 1. Component Building (What's INSIDE a node)

"What does this thing need to function?"

- YouTube Channel needs: logo, banner, description, scripts, thumbnails, upload schedule
- Landing Page needs: headline, subheadline, CTA button, form fields, social proof
- Email Sequence needs: subject lines, body copy, timing, segmentation rules

This is the **asset checklist** work. Fill out each node's internals.

### 2. Connection Wiring (How nodes RELATE)

"How do the pieces work together? In what sequence? What triggers what?"

- YouTube video → links to → Landing Page
- Landing Page → captures email → Email System
- Email System → sends offer → Affiliate Link
- Affiliate conversion → triggers → Upsell Sequence

This is the **flow design** work. Draw the lines, define the triggers, map the data flow.

### You Need Both

Components without connections = a pile of parts that don't do anything.
Connections without components = a flowchart with empty boxes.

**Build components first** (you need to know what exists), **then wire connections** (now make them work together). But you'll go back and forth — wiring connections often reveals missing components ("Wait, I need a thank-you page between the opt-in and the email sequence").

### Sequence vs. Concert

Once all nodes are wired, two questions:

**Sequence**: What order do things happen in? What triggers what? (The linear flow)
**Concert**: What runs in parallel? What's always on? (The simultaneous operations)

```
SEQUENCE (one triggers the next):
  Video uploaded → SEO tags applied → Promoted on social → Analytics tracking starts

CONCERT (running simultaneously):
  Keyword engine (always scanning)
  Analytics monitor (always tracking)
  Email nurture (always dripping)
  Content calendar (always scheduling)
```

The canvas shows both — sequence as directional arrows, concert as parallel lanes.

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
