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
