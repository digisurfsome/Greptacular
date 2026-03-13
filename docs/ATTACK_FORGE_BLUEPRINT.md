# Attack Forge: The Universal Project Blueprint System

> **Status**: Core Architecture Design
> **Date**: March 13, 2026
> **What this is**: The naming system, node architecture, and operational framework for turning ANY idea into an organized, executable, modular plan — not just tools, but strategies, campaigns, processes, and entire business plays.

---

## What Changed (The Realization)

YT Lab makes **tools**. That's one output type. But when you fed it a strategy idea, it rejected it — "crappy tool idea." Because it wasn't a tool. It was a **plan**. A tool could be ONE piece of that plan, but the plan itself is bigger.

**The shift**: The YouTube video (or any input) doesn't always become a tool. Sometimes it becomes:
- A strategy
- A campaign
- A process
- A checklist
- A monitoring system
- A tool
- A mix of all of the above

We need a system that takes ANY input and organizes it into the right kind of output — then lets you wire those outputs together into a visual, drillable, executable map.

**YT Lab = tool factory. Attack Forge = everything factory.**

---

## The Taxonomy (Naming Everything)

Every piece in the system is a **Node**. Nodes have types. Here's what we call them:

### Node Types

| Type | What It Is | Example |
|------|-----------|---------|
| **Objective** | The end goal. Where you're trying to get to. | "10,000 clicks to Jonathan's affiliate link" |
| **Strategy** | The high-level approach to reach the objective. | "Automated YouTube channels + viral short-form + paid ads" |
| **Campaign** | A time-bound execution of a strategy. | "March 2026 YouTube blitz — 100 videos/day for 30 days" |
| **Process** | A repeatable sequence of steps that accomplishes something. | "Research keywords → write script → generate video → upload" |
| **Tool** | An automated system that executes a process without human intervention. | "YouTube Video Factory — auto-generates and uploads tutorials" |
| **Component** | A single piece inside a tool or process. One job. | "Voice synthesizer" or "Thumbnail generator" |
| **Resource** | Something that gets consumed or referenced. Not executable. | "Keyword list" or "Competitor analysis data" or "API key" |
| **Checkpoint** | A decision point where human reviews and approves. | "Review generated videos before batch upload" |
| **Monitor** | A system that watches something and reports status. | "Track daily click count and commission earnings" |

### How They Nest

```
Objective
  └── Strategy (1 or more)
        └── Campaign (1 or more)
              └── Process (1 or more)
                    └── Tool (0 or more — some processes are manual)
                          └── Component (1 or more)
                                └── Resource (0 or more)
              └── Checkpoint (between any steps)
              └── Monitor (watching any level)
```

**But they're NOT strictly hierarchical.** That's the whole point. A Tool can serve multiple Campaigns. A Component can be shared across Tools. A Monitor can watch an Objective, a Campaign, or a single Tool. Everything connects any which way — just like the mind map.

---

## The Node System (Universal Container)

Every node, regardless of type, has the same base structure:

```
┌─────────────────────────────────────────┐
│  NODE                                   │
│                                         │
│  Name: "Automated YouTube Channel"      │
│  Type: Process                          │
│  Status: building / ready / running /   │
│          paused / complete / failed     │
│                                         │
│  ── INPUTS ──                           │
│  What this node needs to start:         │
│  • Keyword list (from SEO Engine)       │
│  • Script templates (from library)      │
│  • Voice model selection                │
│                                         │
│  ── OUTPUTS ──                          │
│  What this node produces:               │
│  • Published videos (URLs)              │
│  • View/click analytics                 │
│  • Content calendar updates             │
│                                         │
│  ── CONNECTIONS ──                      │
│  Feeds into: [Traffic Monitor]          │
│  Receives from: [SEO Engine], [Script   │
│    Writer]                              │
│  Sideways: [Analytics Dashboard] reads  │
│    this node's outputs                  │
│                                         │
│  ── INTERNALS ──                        │
│  Sub-nodes: [Script Gen] → [Video Gen]  │
│    → [Voice Gen] → [Upload]            │
│  Tools used: Remotion, Bark, YT API     │
│  Bones/Joints/Brain breakdown           │
│                                         │
│  ── SOURCES ──                          │
│  Built from: [Video URL 1], [Video URL  │
│    2], [GitHub repo X]                  │
│  Last updated: timestamp                │
│  Update history: [...]                  │
│                                         │
└─────────────────────────────────────────┘
```

**The key insight**: Whether it's a massive Objective or a tiny Component, it's the same container. Inputs, outputs, connections, internals, sources. This means ANYTHING can connect to ANYTHING. A Monitor can feed a Strategy. A Resource can trigger a Tool. A Checkpoint can gate an entire Campaign.

---

## The UI (What You See)

### Tab 1: Mission Control (The Big Map)

Full visual map. Think N8N / mind map hybrid. You see:
- All nodes as boxes on a canvas
- Lines connecting them (solid = chain, dotted = sideways data, dashed = monitoring)
- Color coding by status (green = running, yellow = building, red = broken, gray = planned)
- Zoom in/out to go from Objective level down to Component level
- Click any node → opens its detail page
- Drag to create connections between nodes

```
┌──────────────────────────────────────────────────────┐
│  MISSION CONTROL                            [+ Node] │
│                                                      │
│  ┌─────────────┐     ┌─────────────┐                │
│  │ OBJECTIVE:  │────▶│ STRATEGY:   │                │
│  │ 10K clicks  │     │ Auto YT +   │                │
│  │ ● running   │     │ Viral + Ads │                │
│  └─────────────┘     └──────┬──────┘                │
│                             │                        │
│                    ┌────────┼────────┐               │
│                    ▼        ▼        ▼               │
│              ┌──────────┐ ┌─────┐ ┌──────┐          │
│              │CAMPAIGN: │ │CAMP:│ │CAMP: │          │
│              │YT Blitz  │ │Viral│ │Paid  │          │
│              │● running │ │● bld│ │○ plan│          │
│              └────┬─────┘ └──┬──┘ └──────┘          │
│                   │          │                        │
│              ┌────┴────┐  ┌──┴───┐                   │
│              │PROCESS: │  │TOOL: │                   │
│              │Video    ├─▶│Short │                   │
│              │Factory  │  │Form  │                   │
│              │● running│  │● bld │                   │
│              └────┬────┘  └──────┘                   │
│                   │                                   │
│         ┌────────┼────────┐                          │
│         ▼        ▼        ▼                          │
│    ┌────────┐┌───────┐┌────────┐                    │
│    │Script  ││Video  ││Upload  │                    │
│    │Gen     ││Gen    ││Engine  │                    │
│    │● ready ││● ready││● ready │                    │
│    └────────┘└───────┘└────────┘                    │
│                                                      │
│  [Monitor: 47 clicks today | $1,645 est.]           │
└──────────────────────────────────────────────────────┘
```

### Tab 2: Node Builder (Create/Edit Any Node)

When you click [+ Node] or click into an existing node:
- Type selector (Objective / Strategy / Campaign / Process / Tool / Component / Resource / Checkpoint / Monitor)
- Name and description
- Input definition (what it needs)
- Output definition (what it produces)
- Source material (paste YouTube URLs, docs, text)
- Connection builder (wire to other nodes)
- For Tools: auto-routes to YT Lab build pipeline
- For Processes: breaks down into sub-steps
- For Strategies: breaks down into campaigns

### Tab 3: Build Queue (What's Being Made)

Shows everything currently being built or waiting to be built:
- Which nodes are in the YT Lab pipeline
- Which are being researched
- Which are waiting for human input
- Priority ordering (drag to reorder)
- Estimated completion

### Tab 4: Live Dashboard (What's Running)

Real-time monitoring of all active nodes:
- Video upload counts
- Click tracking
- Commission estimates
- Error alerts
- Performance metrics per channel/campaign

### Tab 5: Source Library (All Your Inputs)

Every YouTube video, document, idea, and GitHub repo you've fed in:
- Organized by topic
- Shows which nodes each source contributed to
- "Throw this at an existing node" button — adds new info to update a node
- Search across all source material

### Sidebar: Quick Nav

Dropdown tree of all nodes by hierarchy:
```
▼ Objective: 10K Affiliate Clicks
  ▼ Strategy: Organic + Paid Traffic
    ▼ Campaign: YouTube Tutorial Blitz
      ▼ Process: Automated Video Creation
        ▶ Tool: Script Generator
        ▶ Tool: Video Generator
        ▶ Tool: Voice Synthesizer
        ▶ Tool: YouTube Uploader
      ▼ Process: SEO Optimization
        ▶ Tool: Keyword Engine
    ▼ Campaign: Viral Short-Form
      ▶ Process: TikTok Content Machine
    ▼ Campaign: Paid Ads
      ○ (planned — not built yet)
  ▶ Monitor: Click Tracker
  ▶ Monitor: Commission Dashboard
```

Click any item → goes to its page. Same content as the node in Mission Control but in a full-page detail view.

---

## How Input Gets Processed (The Ingestion Flow)

### Step 1: Input Arrives
Could be: YouTube URL, text description, voice memo transcript, document

### Step 2: Classification
AI reads the input and determines: "This describes a _____"
- Tool idea → routes to tool builder (current YT Lab)
- Strategy/plan → routes to strategy organizer
- Process description → routes to process mapper
- Mixed → breaks it apart into separate nodes

### Step 3: Decomposition
Whatever it is gets broken down:
- Strategy → what campaigns are needed?
- Campaign → what processes are needed?
- Process → what tools/components are needed?
- Tool → what components/resources are needed?

### Step 4: Gap Analysis
For each node identified:
- What source material do we have?
- What's missing? (web search + GitHub scan)
- What existing nodes in our system already handle part of this?
- What can we reuse vs. what's new?

### Step 5: Human Review
Quick report: "Here's what I broke this into. Here are X nodes. Here are the gaps. Here's what I'd reuse. Approve?"

Checkboxes. 30 seconds. Go.

### Step 6: Build
Each node enters the build queue. Tools go through YT Lab. Processes get mapped. Strategies get organized. Everything gets wired into the Mission Control map.

---

## The Living System (Continuous Updates)

You said it: "5 hours later I see another video and I need to add it."

### How updates work:
1. You find new source material (video, article, tool, idea)
2. You paste it in and point it at an existing node: "This is for the YouTube Video Factory"
3. The Video Intelligence Combiner compares new info against what's already in the node
4. Report: "2 new techniques found. 1 better tool alternative. Here they are."
5. You approve
6. Node gets updated. If it's a running tool, it gets redeployed with the update.

### Auto-updates:
The Tech Radar (from the infrastructure framework) continuously scans for:
- New GitHub repos relevant to any active node
- New techniques or tools in the space
- API changes that affect running tools
- Competitor activity

Findings get queued as update proposals. You batch-approve during your daily review.

---

## The Business Play (Documented)

### Immediate Revenue (This Week)
- Jonathan's affiliate program: $35/click avg, $357 avg sale, up to $900/customer
- You're not the front face. His system handles conversion, support, everything.
- Your job: drive traffic. His job: convert and deliver.
- Bonus play: give away YOUR tools to people who buy the big package through your link

### Short Term (30-90 Days)
- Automated YouTube channels pumping tutorial content at scale
- Viral TikTok/Instagram driving immediate clicks
- 50-100 videos/day across channels once automation is running
- Target: 10,000 clicks = $350,000 in commissions
- Reinvest 50% into paid ads immediately

### Medium Term (3-6 Months)
- Jonathan notices your volume → invites you on lives
- You become the "automation guy" in his community
- Start offering YOUR tools directly to his audience
- High-ticket consulting: $5K-$20K for custom tool builds
- Subscription model: 20-30-40-50 tools in a monthly package

### Long Term (6-12 Months)
- 500+ tools in the library
- B2B play: go to companies, "what tools do you need? I'll build them right now"
- The moat: nobody can compete with 500+ tools, all interconnected, all improving daily
- VC potential: "I can build any tool in a meeting, on my phone, right now"
- Enterprise deals: custom tool suites for specific industries

### The Moat Strategy
- Don't go public with how easy this is yet
- Sell to businesses quietly — they see the output, not the process
- By the time the "four-minute mile" moment happens and everyone realizes they can do this, you have 500K tools and enterprise relationships
- The volume IS the moat
- Monitoring systems keep everything online — deterministic health checks, not human babysitting

### The Stripe Minions Principle
Everything possible is deterministic (scripts, schedules, uploads, health checks). AI only handles the parts that NEED flexibility (writing, decisions, creative). This means:
- Tools don't break randomly
- They run 24/7 without supervision
- When something does break, deterministic monitoring catches it immediately
- AI fixes are targeted, not blanket

---

## The 50-a-Day Machine

How you get to 500,000 tools:

1. **Input**: You or the system identifies a tool need (from videos, ideas, customer requests, market gaps)
2. **Research**: 5 minutes — auto-enriched by the Research Engine
3. **Build**: 10-15 minutes — YT Lab kicks out the tool
4. **Wire**: 2 minutes — connect to existing nodes if applicable
5. **Deploy**: Automatic — tool goes live
6. **Monitor**: Automatic — health checks run continuously

At 20-30 minutes per tool, 50/day is realistic with 8 hours of focused work. With batching and parallelization, could hit 100+.

The tools range from simple (prompt chain, one API) to complex (multi-component, GitHub wrappers, deterministic + AI hybrid). Even the simple ones have massive value because:
- They solve ONE specific problem really well
- They're interconnectable
- They update when new info comes in
- Nobody else has 500,000 of them

---

## What Gets Built First (Revised Priority)

Based on everything you just said, here's the updated build order:

### TODAY — Tool 0: Attack Forge Planner
The node-based planning system itself. Before we build any content tools, we need the war room to organize them. This is a new page in the workspace UI.

**Minimum viable version:**
- Node creation (type, name, description, inputs, outputs)
- Visual map (nodes as boxes, connections as lines)
- Sidebar tree navigation
- Source material attachment (paste YouTube URLs)
- Status tracking per node

### THIS WEEK — Tool 1: Video Intelligence Combiner
Multiple transcripts → unified knowledge. This is the research amplifier.

### THIS WEEK — Tool 2: YouTube Video Factory
Auto-generate tutorial videos. This is the traffic engine.

### NEXT WEEK — Tool 3: Viral Short-Form Machine
TikTok/Instagram/Shorts. Fast traffic, immediate clicks.

### NEXT WEEK — Tool 4: YouTube SEO Engine
Keyword mapping, content calendar, topic clustering.

### ONGOING — Tool 5: App Shield (Obfuscation)
Protect everything that gets built. Runs as a post-build step on all tools.

---

## Your Action Items RIGHT NOW

1. **Get your affiliate link live** — confirm program, get tracking set up
2. **Go find the YouTube videos** you need for:
   - YouTube automation (how to make automated channels)
   - YouTube SEO (keyword strategies, algorithm, tagging)
   - AI video generation (tools and techniques for auto-creating videos)
   - Viral short-form content (what makes AI content go viral)
3. **Collect URLs in a list** — organized by topic, ready to feed into the system
4. **Think about your TikTok/Instagram channel concept** — the viral AI video idea you mentioned. What's the theme? What makes each video unique but shareable?
5. **Don't wait for automation to post your first content** — put something out manually today. One TikTok. One short. Prove the concept.

---

## Naming Convention (For Our Communication)

So we can talk fast and know what we mean:

| When you say... | It means... |
|----------------|-------------|
| "Node" | Any container in the system (tool, process, strategy, etc.) |
| "Objective" | The end goal we're driving toward |
| "Strategy" | The high-level approach |
| "Campaign" | A time-bound execution of a strategy |
| "Process" | A repeatable sequence of steps |
| "Tool" | An automated system that runs a process |
| "Component" | A single piece inside a tool |
| "Resource" | Data or material that gets used (not executable) |
| "Checkpoint" | Human decision point |
| "Monitor" | Automated watcher/reporter |
| "Wire" / "Connect" | Link two nodes together |
| "Sideways" | Data sharing between non-chained nodes |
| "Chain" | Front-to-back sequential connection |
| "Throw it at [node]" | Feed new source material to update an existing node |
| "Bones" | Deterministic code |
| "Joints" | AI/prompt flexibility |
| "Brain" | Open-source GitHub tools |
| "The Map" | Mission Control visual view |
| "The Queue" | Build queue for nodes being constructed |

---

*This is the operating system for everything. Every idea, every video, every tool, every strategy — it all flows through this framework. The taxonomy is set. The node system is universal. Now we build it.*
