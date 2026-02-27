# YT Strategy Lab — Knowledge Engine Roadmap

> **Status:** Seed document. Each section is a future epic. Expand into PRDs when ready to build.
>
> **Context:** This captures the next evolution of YT Strategy Lab — from a video-to-template tool into a **compounding knowledge engine** that gets smarter with every video processed.

---

## The Core Insight

One video gives you one perspective. Ten videos on the same topic give you the **complete picture**. Creator A explains LinkedIn scraping in depth but glosses over enrichment. Creator B barely mentions scraping but spends 20 minutes on enrichment. The system that has both doesn't just have two videos — it has **one complete workflow** that neither creator could give you alone.

This is the compounding effect. The library doesn't just get wider — it gets **deeper**. Video #20 isn't producing 20 new things. It's completing and improving the ones that already exist.

---

## 1. Discovery Results Persistence

**Problem:** Discovery phase results (the colored insight sections with deep analysis) disappear when navigating away. All that extracted gold — gone. The AI did the work, the user saw it, but it's not saved.

**What needs to happen:**
- Save discovery results to the database when they come back from AI processing
- Load and display saved results when the user revisits a video
- Discovery results should be as permanent as strategy extraction results
- Each video should have: raw transcript, discovery insights, strategy steps — all persisted

**Priority:** CRITICAL — this is data loss. The most expensive operation (AI processing) runs, produces gold, and then throws it away.

---

## 2. Cross-Video Knowledge Merging

**The Obsidian model:** Obsidian doesn't just store notes — it links them. It finds connections between ideas across different documents. YT Strategy Lab needs the same thing but for automation knowledge.

**How it works:**
- After processing, the system tags each strategy step with semantic categories (e.g., "lead scraping", "email enrichment", "cold outreach", "ad creative")
- When a new video is processed, the system checks: "Do I already have steps for this category?"
- If yes, it **merges** — takes the best from each source, fills gaps, resolves conflicts
- The result: a unified "best of all sources" workflow for each category

**Example:**
```
Video 1 (Cody): LinkedIn scraping (detailed) → enrichment (surface level) → outreach (good)
Video 2 (Other): LinkedIn scraping (basic) → enrichment (expert level) → outreach (different angle)

Merged knowledge:
  LinkedIn scraping: Video 1's approach (more detailed)
  Enrichment: Video 2's approach (expert level)
  Outreach: Both approaches preserved as variants
```

**Architecture thought:** Each "knowledge unit" (a step or technique) gets a semantic fingerprint. When two units have high similarity (>80%), the system flags them for merge. When similarity is moderate (40-80%), it flags them as "related — consider combining." Below 40%, they're independent.

---

## 3. Creator Intelligence (Who Teaches What)

**Problem:** At scale (10+ videos/day), you lose track of who said what and what each creator's strengths are.

**What the system should know about each creator:**
- Name, channel, typical topics
- Teaching style (hands-on demo vs. conceptual, beginner vs. advanced)
- Strength areas (e.g., "Cody is great at ad systems, weak on backend infra")
- Videos processed from this creator
- Quality score (based on how actionable their extracted steps are)

**Why it matters:** When the system has 50+ processed videos, creator intelligence lets you say: "Show me everything from the top 3 creators on cold email automation" — and get a curated, credibility-weighted knowledge base.

**Smart recommendations:** "You've processed 4 videos on ad automation but none from [Creator X] who is known for this topic. Here's their best video on it."

---

## 4. Smart Tagging and Auto-Categorization

**Problem:** With 10+ videos/day, manual organization is impossible. The system needs to self-organize.

**Tag hierarchy:**
```
Category (top level):     AI Automation, Health/Wellness, SaaS, Content, Lead Gen, ...
Topic (mid level):        Cold Email, Ad Creative, Landing Pages, SEO, ...
Technique (granular):     LinkedIn Scraping, GPT Prompt Chaining, Webhook Pipelines, ...
```

**Auto-tagging flow:**
1. Video gets processed
2. AI analyzes the content and assigns tags at all three levels
3. Tags are matched against existing taxonomy — new tags created only if truly new
4. Related videos are automatically linked

**Search:** Full-text search across all processed videos, strategies, steps, and discovery results. "Find everything about email enrichment" returns results from across all videos, ranked by relevance and creator quality.

---

## 5. Front Page Redesign for Scale

**Problem:** Current layout shows ~6-9 large project cards. At 10 videos/day, that's unusable within a week.

**New layout concept:**
- **Left sidebar:** Category tree (AI Automation, Health, SaaS, etc.) with counts
- **Main area:** Filtered list/grid of projects within selected category
- **Top bar:** Search, filters (by creator, date, tag, quality), sort options
- **Card size:** Smaller, denser — show 20-30 per page minimum
- **Quick preview:** Hover or click to see discovery highlights without navigating away

**Views:**
- **Category view** (default): Grouped by top-level category
- **Creator view:** Grouped by who made the video
- **Timeline view:** Chronological, most recent first
- **Knowledge map view:** Visual graph showing connections between topics

---

## 6. Mobile Capture App

**Problem:** Video discovery happens on the phone (YouTube algorithm). But processing happens on desktop. The gap means videos get lost.

**MVP mobile flow:**
1. User sees a video on their phone
2. Shares the URL to the YT Lab mobile app (or uses a share extension)
3. App queues it for processing with optional quick context note
4. Desktop system picks up the queue and processes it
5. Results available on both mobile and desktop

**Implementation options:**
- **Progressive Web App (PWA):** Fastest to build. Works on any phone browser. Share target API for receiving URLs from YouTube app. No app store needed.
- **React Native:** Better native feel. More work. Needed if we want push notifications or background processing.
- **Shortcut/Automation:** iOS Shortcut or Android Tasker that sends the URL to our API endpoint. Zero UI work. Just a webhook.

**Recommendation:** Start with the webhook + iOS Shortcut approach (1 hour to build). Graduate to PWA when the workflow proves itself.

---

## 7. Knowledge Consolidation Engine

**This is the big one.** The system that takes 10 videos on the same topic and produces one unified, best-of-all-sources workflow.

**How it works:**
1. **Cluster:** Group processed videos by topic similarity
2. **Compare:** For each cluster, align the steps across all videos (step matching)
3. **Merge:** For each aligned step, pick the best explanation/prompt, fill gaps from other sources
4. **Synthesize:** Produce a "master workflow" that represents the combined knowledge
5. **Attribute:** Each step in the master workflow links back to which video(s) contributed to it

**Output:** A "consolidated strategy" that is better than any single video because it contains the best parts of all of them.

**The 80/10/10 principle (from user):**
- 80% of videos on the same topic say the same thing
- Each video has ~10% unique insight the others miss
- The consolidation engine extracts that 10% from each and adds it to the shared 80%
- Result: 100% knowledge from 10% of each source

**This is the moat.** No one else is doing cross-video knowledge synthesis. Individual video summaries are commodity. Merged, synthesized knowledge across sources is genuinely new.

---

## 8. Practitioner AI Platform (Future Product)

**Concept:** Train AI agents to be practitioners — hypnotherapists, NLP coaches, psychologists, meditation guides, fitness coaches, nutritionists.

**How it connects to YT Lab:**
- Process training videos from certified practitioners
- Extract their techniques, frameworks, session structures
- Consolidate knowledge across multiple practitioners in the same discipline
- Package as an AI agent that can conduct sessions

**Business model:**
- Low marginal cost (AI does the sessions, no human expert needed)
- 24/7 availability (no scheduling, no time zones)
- Subscription pricing (fraction of real practitioner cost)
- Massive addressable market (everyone wants access to coaching/therapy, few can afford it)

**Build path:**
1. YT Lab processes practitioner training content
2. Knowledge consolidation produces "master technique" for each discipline
3. Separate app wraps the technique in a conversational session interface
4. User talks to the AI practitioner, AI follows the extracted framework
5. Breakaway product — own branding, own billing, own app

---

## My Recommendations (Agent's Two Cents)

Having seen the full codebase and how this system works, here's what I'd prioritize:

### Build order (highest impact first):

1. **Discovery persistence** — Stop losing data. This is a bug, not a feature. Fix it immediately. (This session.)

2. **Auto-tagging on ingest** — When a video is processed, have the AI also output 5-10 tags. Store them. This is almost free (add a field to the existing prompt) and unlocks everything else.

3. **Search** — Full-text search across all stored content. The data is already in SQLite. Add a search endpoint and a search bar. Transforms the UX from "scroll and hope" to "find anything instantly."

4. **Knowledge linking** — After auto-tagging, add a "Related strategies" section to each project. Simple tag overlap query. Shows which other videos cover similar ground. This is the seed of the Obsidian-like linking.

5. **Front page categories** — Group projects by their top-level tag. Sidebar navigation. Essential when you hit 20+ projects.

6. **Creator tracking** — Add a `creator` field to projects. Populate from video metadata. Enable "show me everything from Cody" queries.

7. **Consolidation engine** — The cross-video merge. This is the hardest but highest-value feature. Build it after you have 20+ videos with good tagging, so there's enough data to merge meaningfully.

8. **Mobile capture** — PWA with share target. Queue videos for processing. Build this when the daily volume makes it painful to copy-paste URLs.

### What makes this system genuinely powerful:

The thing that separates this from "yet another YouTube summarizer" is **persistence + accumulation + synthesis**. Any tool can summarize one video. The value here is that video #50 makes videos #1-49 more valuable because the system can now see patterns, fill gaps, and synthesize knowledge that no single source contains.

The compounding effect is real. But it only works if:
- Every piece of extracted knowledge is **saved** (persistence)
- Everything is **tagged and searchable** (organization)
- Related knowledge is **linked** (knowledge graph)
- Overlapping knowledge is **merged** (consolidation)

Build those four pillars and you have something nobody else has.

---

## 9. Mastermind Advisory Panel (The Think and Grow Rich Model)

> **Origin:** Napoleon Hill's "Think and Grow Rich" — the Mastermind principle. You assemble a group of minds, each with a different lens, and run every decision through all of them. The combined intelligence exceeds any individual member.

**What it is:** A panel of AI advisors embedded directly into YT Strategy Lab. Not a chatbot. A **thinking council** that reacts to every video, every strategy, every decision — each from their own perspective.

### The Advisors

Three core advisors, each with a distinct lens:

1. **The App Architect** — Thinks in products, features, user flows, and technical feasibility. When a video comes through, this advisor sees: "What app does this become? What's the MVP? What's the tech stack? What existing apps in the portfolio could absorb this as a feature?"

2. **The Marketing Strategist** — Thinks in audiences, positioning, distribution, and messaging. Sees: "Who buys this? How do you reach them? What's the hook? What content does this generate? How does this position against competitors?"

3. **The Business Operator** — Thinks in revenue, operations, scalability, and leverage. Sees: "What's the revenue model? What's the margin? Does this scale? What's the unfair advantage? How does this compound with what already exists?"

### How It Works

**Passive mode (auto-react):** Every time a video is processed, each advisor gives a brief take. Three short paragraphs that appear automatically. No user action needed. This is the "round table" — you just see three perspectives without asking.

**Active mode (ask the panel):** User can ask a question and route it to:
- One specific advisor ("Marketing, how would I position this?")
- All three ("Round table: should I build this or add it to an existing app?")
- A custom combination

**Context-aware:** Each advisor has access to:
- All processed videos and their extracted knowledge
- All apps that have been built from the system
- The tag/relationship graph connecting everything
- The user's stated goals and priorities

### Architecture: Two Modes (Try Both)

**Mode A — Unified Panel (one AI, multiple personas):**
- Single system prompt that defines all three personas
- AI responds as each advisor in sequence
- Simpler to build, lower resource usage
- Natural for round-table discussions where advisors riff off each other
- Risk: perspectives might blend together over long conversations

**Mode B — Separate Advisors (independent instances):**
- Each advisor is its own chat session with its own system prompt
- Each maintains its own conversation thread and memory
- Toggle between them in the UI (tabs or sidebar)
- Cleaner separation of perspectives
- Can go deeper on any single advisor's domain
- Higher resource usage (3x the context windows)

**Recommendation:** Build Mode A first (unified panel, fast to ship). Add Mode B as an option once the concept proves itself. The toggle between them lets the user decide what works better for their thinking style.

### The Deeper Vision: Historical Mastermind

Beyond the three business advisors, the Think and Grow Rich model goes further — you can populate your mastermind with **anyone who has ever existed**. The AI can embody:
- A specific business figure (their known philosophy, decisions, patterns)
- A specific author (their frameworks, mental models)
- A specific practitioner (their techniques, approaches)

This connects directly to the **Practitioner AI Platform** (Section 8). The mastermind is the advisory layer; the practitioner platform is the execution layer. Same underlying capability, different use case.

### Integration Points

- **Video processing:** Auto-generate advisor reactions for every new video
- **App feedback loop:** When an app gets updated, advisors are notified and can suggest cross-pollination ("The email enrichment technique from video #23 would be a killer feature for the cold outreach app you built from video #7")
- **Decision support:** Before building anything, run it through the panel. Three perspectives in 30 seconds.
- **Knowledge graph:** Advisors can reference connections between videos, strategies, and apps that the user might not see

---

## 10. App Feedback Loop (Closed-Loop Intelligence)

**The missing piece:** Right now, knowledge flows one way — from videos into the system. Apps get built, but the system forgets about them. It doesn't know what was built, what features exist, or what's working.

**What needs to happen:**

1. **App Registry:** Every app built from YT Lab knowledge registers back with the system. The registry stores: app name, what video(s) it came from, current feature list, tech stack, status (prototype/live/revenue).

2. **Feature Sync:** When an app gets a new feature or update, that change propagates back to YT Lab. The system now knows the current state of every app in the portfolio.

3. **Smart Feature Suggestions:** When a new video is processed, the system cross-references the extracted knowledge against ALL registered apps. "This video's lead enrichment technique would improve apps X, Y, and Z — here's specifically how for each one."

4. **Portfolio Intelligence:** The system can answer: "Which of my apps would benefit most from this new technique?" or "Which apps overlap in functionality and should be merged?" or "What's the gap in my portfolio that no current app addresses?"

**The loop:**
```
New video → Extract knowledge → Cross-reference against app portfolio
    ↑                                        ↓
    │                          Suggest features for existing apps
    │                                        ↓
    │                          App gets updated with new features
    │                                        ↓
    └───────── App reports update back to system ←──┘
```

This is what turns a collection of apps into an **ecosystem**. Each app makes every other app smarter because they share a common knowledge base that keeps growing.

---

## 11. Instant Micro-Tools (5-Minute Personal Tools)

> **Principle:** Every extracted strategy should be USABLE within 5 minutes. Not "documented for later" — usable NOW.

**The problem with PRDs:** A PRD is a planning document. It describes what to build. But for personal tools, you don't need a plan — you need the tool. A text box, a prompt chain, and an output. That's it.

**How it works:**

For every strategy extracted from a video, the system auto-generates the simplest possible tool:

```
Extracted strategy: "4 types of prompts for 10x output"
                         ↓
         Auto-generated micro-tool:
         ┌─────────────────────────────┐
         │  [Text box: Enter your idea] │
         │                              │
         │  [Button: Run]               │
         │                              │
         │  [Output: Optimized result]  │
         └─────────────────────────────┘
```

- **Input:** One text box. What's your idea / raw input?
- **Processing:** The extracted prompt chain from the video (1-3 prompts, chained)
- **Output:** The result. Immediately usable.
- **No auth, no database, no routing.** Just the knowledge made executable.

### The Dual Path (runs in parallel, doesn't block each other)

```
Strategy extracted from video
         ↓
    ┌────┴────┐
    ↓         ↓
Path A:    Path B:
PERSONAL   SaaS EXPLORATION
TOOL       (background)

Text box    "What would this
+ prompt    look like as a
+ output    product? Who buys
            it? What's the
Usable      pricing? What's
in 5 min    the market?"
    ↓         ↓
USE IT     SAVE IT
NOW        (ready when PRD
            machine ships)
```

**Path A (personal tool)** is instant. Built the moment the strategy is extracted. Could be as simple as a prompt the user copies into Claude, or as polished as a mini-page with a text box and button.

**Path B (SaaS exploration)** is a second AI pass that runs in the background. It explores the commercial opportunity: market size, pricing, competitors, differentiation. This gets saved alongside the strategy. When the PRD machine is ready, this exploration becomes the input — it's already done the thinking.

### Connection to the Ecosystem

The micro-tool's output doesn't just sit on screen:
- Output can be pushed to **Workspace** (as a new conversation context)
- Output can feed into **Dunk Stack** (as a build spec)
- Output can feed into **AutoForge** (as a feature spec)
- The tool itself registers in the **App Feedback Loop** (Section 10)

This means: process a video → get a micro-tool → use it → the output flows into the rest of the system. No copy-paste. No manual bridging. The knowledge moves through the pipeline automatically.

### Build Priority

1. **Now:** For each strategy, generate a "Quick Use" prompt the user can immediately paste and use. Zero code needed — just the extracted prompt formatted for direct use.
2. **Soon:** Auto-generate a micro-page (text box + button + output) within YT Lab for each strategy. One-click access.
3. **Later:** PRD machine formalizes Path B. Auto-generates full product specs from the SaaS exploration.

