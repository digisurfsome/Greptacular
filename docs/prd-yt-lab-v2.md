# PRD: YT Lab v2 — Multi-Video Pipeline + Discovery Feed

> **Owner context:** This is a descriptive PRD — what the feature does, not how to code it.
> A technical agent will turn this into implementation specs.
>
> **Priority order:**
> 1. Fix transcript (remove timestamps, make persistent)
> 2. Add game plan distillation
> 3. Multi-video tool creation
> 4. Discovery feed + creator management
>
> Items 1-3 are the immediate need. Item 4 is the bigger vision.

---

## WHAT EXISTS TODAY

The YT Lab currently:
- Takes a single YouTube URL
- Grabs the transcript (but with timestamps jumbled in — messy, unreadable)
- The transcript is NOT persistent — leave the page, it's gone. Have to re-run to get it back
- Processes the video and generates:
  - **Top section:** Software/tool ideas ranked by confidence (e.g., "90% — GTM Research Tool", "82% — Ad Copy Generator")
  - **Main area:** Detailed plan for the selected tool idea — context, description, main prompt, step-by-step phases
  - **Left sidebar:** The phases/steps of the tool (like Cody Schneider's 9-step GTM process)
- The transcript retrieval uses a bash command (yt-dlp or similar), not the YouTube API
- Currently: **1 video = 1 tool idea**

### What's Broken / Missing
1. Transcript has timestamps embedded — unreadable jumble
2. Transcript is not saved — lost when you navigate away
3. No way to input multiple videos for one tool idea
4. The tool ideas at the top don't seem to switch the detailed plan below when clicked
5. No way to go back and add more information to an existing tool later
6. No search/discovery for finding relevant YouTube videos
7. No creator management (favorites, tiers, tracking)

---

## FEATURE 1: Clean Transcript (Persistent)

### What It Does
When a video is processed, create TWO versions of the transcript:
1. **Raw transcript** — The original with timestamps (keep this too, just in case)
2. **Clean transcript** — Timestamps removed, properly formatted as readable paragraphs

### How It Works
- [ROBOT] Strip timestamps using regex — this is deterministic, no LLM needed
- Timestamps follow patterns like `[0:00]`, `(0:00:00)`, `00:00 -` etc.
- Clean up resulting text: merge broken sentences, add paragraph breaks at natural pauses
- Save both versions to the database permanently
- Show a "Transcript" tab/button that's always accessible for any processed video

### Persistence
- Both transcript versions saved to SQLite (same DB pattern as features.db)
- Associated with the video record by video ID
- Once processed, never needs to be re-fetched
- Available instantly when you click on any previously processed video

---

## FEATURE 2: Game Plan Distillation

### What It Does
Take the clean transcript and create a structured "game plan" document — like reading a book summary with clear topics, bullet points, and actionable steps.

### How It Works
- [AGENT] LLM reads the clean transcript and produces:
  1. **Main topics** — What are the 3-7 key subjects covered?
  2. **For each topic:**
     - Summary paragraph (2-3 sentences)
     - Key bullet points (what did they say about this?)
     - Actionable takeaways (what would you DO with this info?)
  3. **Overall thesis** — What's the one big idea of this video?
- This is definitely an LLM task — needs understanding, not just text processing
- Saved permanently alongside the transcript

### UI
- Shows as a second tab next to the transcript: "Transcript" | "Game Plan"
- Always available for any processed video
- The game plan is the "truth document" — this is what the video is about, distilled

### Why This Matters
- The game plan is the SOURCE MATERIAL for tool ideas
- When combining multiple videos (Feature 3), you combine game plans, not raw transcripts
- It's also just useful on its own — quick reference for "what did this video say?"

---

## FEATURE 3: Multi-Video Tool Creation

### The Problem
Right now: 1 video → 1 tool idea. But often, multiple creators cover the SAME topic with slightly different approaches. Combining their knowledge produces a BETTER tool than any single video.

### Real Example
The owner follows 10-15 AI/coding YouTubers. When a hot topic hits (like AI SEO), 3-5 of them will release videos about it within a 3-5 day window. Each one covers ~85-90% of the same ground, but each has unique 10-15% insights, techniques, or tweaks. Combining all of them creates the DEFINITIVE tool for that topic.

### How It Works

#### Step 1: Add Multiple Videos
- Instead of one URL input, allow adding multiple URLs
- "Add another video" button adds more URL fields
- Each video gets processed independently (transcript + game plan)
- All videos are grouped under one "project" or "tool workspace"

#### Step 2: Individual Processing (per video)
Each video goes through the existing pipeline:
1. Grab transcript → clean it (remove timestamps) [ROBOT]
2. Generate game plan distillation [AGENT]
3. Save both permanently

#### Step 3: Cross-Video Synthesis (NEW — the key feature)
Once all videos are processed, a new [AGENT] step:

**"Synthesize All Videos"** button triggers an LLM that:
1. Reads all game plans from all videos in the group
2. Identifies the **COMMON GROUND** — what do 85-90% of them agree on?
3. Identifies the **UNIQUE INSIGHTS** — what does only one or two mention?
4. Identifies **CONTRADICTIONS** — where do they disagree?
5. Produces a **UNIFIED STRATEGY DOCUMENT**:
   - Core process (the 85-90% everyone agrees on)
   - Edge techniques (the unique 10-15% from each creator)
   - Decision points (where approaches diverge, pros/cons of each)
   - Recommended sequence (what order should the tool do things?)

This unified document becomes the new source material for tool idea generation.

#### Step 4: Generate Tool Ideas (same as today, but from unified doc)
- "What tools could we make from this?" prompt runs against the unified document
- Shows ranked tool ideas at the top (same UI as today)
- Clicking a tool idea loads its detailed plan below

### The Flow Diagram
```
Video 1 URL → Transcript → Clean Transcript → Game Plan ─┐
Video 2 URL → Transcript → Clean Transcript → Game Plan ─┤
Video 3 URL → Transcript → Clean Transcript → Game Plan ─┼→ Synthesize → Unified Doc → Tool Ideas
Video 4 URL → Transcript → Clean Transcript → Game Plan ─┤
Video 5 URL → Transcript → Clean Transcript → Game Plan ─┘
```

### Tool Versioning
- A tool created from 3 videos can later have more videos added
- Adding a new video and re-synthesizing creates an updated unified document
- The tool idea can be regenerated from the new unified doc → V2 of the tool
- Old versions are kept (version history)
- This is how tools evolve over time as the topic/strategy matures

---

## FEATURE 4: Discovery Feed + Creator Management (Vision — Build Later)

### Creator Tiers
Organize followed YouTube creators into tiers:
- **A-Tier** — Top 5-10 creators you ALWAYS pay attention to. Every video matters.
- **B-Tier** — Good creators, watch when relevant. 10-15 more.
- **Specialists** — Only care about them for ONE specific topic. Tag what they specialize in.
- **Watch List** — New creators you're evaluating. Not committed yet.

### Daily Feed
- Automated check: "What did my A-Tier creators publish today?"
- Morning + evening digest (configurable)
- Shows new videos with titles, thumbnails, duration
- One-click to mark: "Watched", "Watch Later", "Pre-Tool" (see below)
- Videos you've seen disappear from the feed (unless tagged "Watch Later")

### Pre-Tool Tagging
When you see a video that's relevant to a tool you want to build eventually:
- Tag it as "Pre-Tool" and name the tool concept (e.g., "AI SEO Tool")
- Now the system watches for MORE videos about that topic
- Smart logic: "Hey, 3 of your A-Tier creators just posted about AI SEO this week. You tagged this as a pre-tool — want to start building?"
- Pre-tools accumulate videos over time until you're ready to synthesize

### YouTube Search (In-App)
- Search YouTube from within YT Lab
- Results show on a full-screen grid
- Highlight which results are from your followed creators
- Click to add videos to a tool workspace or pre-tool
- Filter by: creator tier, date, duration, topic tags

### Smart Suggestions
- "You follow 12 creators who posted about [topic] this week"
- "This video matches your pre-tool [AI SEO Tool] — want to add it?"
- "New creator [name] has 3 highly-rated videos on topics you care about — want to add them to your watch list?"

### Mobile App (Future)
- Companion app for phone
- Browse daily feed on the go
- Tag videos for later processing
- Push notifications: "Your A-Tier creator just posted"
- "Send to YT Lab" button that queues the video for desktop processing

---

## FEATURE 5: Tool Idea Selection + Detail View Fix

### Current Issue
The top section shows ranked tool ideas (e.g., "90% — GTM Tool"). Clicking one SHOULD switch the detailed view below to show that tool's plan. This may not be working properly — needs investigation.

### Expected Behavior
1. Tool ideas at top are clickable cards
2. Clicking one highlights it and loads its detailed plan below
3. The left sidebar updates to show that tool's phases/steps
4. The main area shows context, description, prompt, step details
5. Each tool idea has its own independent plan (not shared)

### Persistence
- All tool ideas and their detailed plans are saved to the database
- Switching between tool ideas is instant (no re-generation)
- Can go back to previously generated tools at any time

---

## IMPLEMENTATION PRIORITY

### Phase 1: Transcript Fix + Persistence (Small, do first)
- Strip timestamps [ROBOT]
- Save clean transcript to DB [ROBOT]
- Add "Transcript" tab that's always available [ROBOT]
- ~2/10 difficulty, 1 agent

### Phase 2: Game Plan Distillation (Medium)
- LLM processes clean transcript into structured game plan [AGENT]
- Save game plan to DB [ROBOT]
- Add "Game Plan" tab [ROBOT]
- ~3/10 difficulty, 1 agent

### Phase 3: Multi-Video Support (Medium-Large)
- Multiple URL input [ROBOT]
- Group videos into workspaces [ROBOT]
- Cross-video synthesis LLM step [AGENT]
- Unified document generation [AGENT]
- Tool ideas from unified doc [AGENT]
- ~5/10 difficulty, 1-2 agents

### Phase 4: Tool Idea Selection Fix (Small)
- Investigate current click behavior
- Fix tool idea → detail view switching
- Ensure persistence
- ~2/10 difficulty, 1 agent

### Phase 5: Discovery Feed (Large — future)
- Creator management + tiers [ROBOT]
- YouTube API search integration [ROBOT]
- Daily feed automation [ROBOT + AGENT]
- Pre-tool tagging + smart suggestions [AGENT]
- ~7/10 difficulty, 2-3 agents

### Phase 6: Mobile App (Large — future)
- React Native or Flutter companion
- Push notifications
- "Send to YT Lab" integration
- ~8/10 difficulty, separate project

---

## KEY DESIGN DECISIONS

### What's [ROBOT] vs [AGENT]?
- **Stripping timestamps from transcript** → [ROBOT] — regex, deterministic, zero tokens
- **Formatting clean transcript into paragraphs** → [ROBOT] — text processing rules
- **Creating game plan from transcript** → [AGENT] — needs understanding/reasoning
- **Cross-video synthesis** → [AGENT] — needs to compare, contrast, merge ideas
- **Tool idea generation** → [AGENT] — creative reasoning
- **Search, tagging, sorting, DB operations** → [ROBOT] — all deterministic
- **Smart suggestions ("this matches your pre-tool")** → Could be [ROBOT] with keyword matching, or [AGENT] for semantic matching. Start with [ROBOT], upgrade to [AGENT] if accuracy is too low.

### Subscription Auth
All [AGENT] steps use Claude CLI subprocess (`claude -p --model sonnet`) via subscription — zero API credits. Same pattern as the Build Planner fix.

### Data Model
Every video record needs:
- `video_id` (YouTube ID)
- `url`
- `title`, `channel`, `duration`, `published_date`
- `raw_transcript` (with timestamps)
- `clean_transcript` (timestamps removed, formatted)
- `game_plan` (LLM-generated structured summary)
- `workspace_id` (which tool workspace this video belongs to, nullable)
- `created_at`, `updated_at`

Every workspace (multi-video group) needs:
- `workspace_id`
- `name` (e.g., "AI SEO Tool")
- `unified_document` (synthesized from all videos' game plans)
- `tool_ideas` (JSON array of ranked ideas)
- `selected_tool_id` (which tool idea is currently active)
- `status` (collecting / ready / synthesized / tool_generated)

---

## THE BIG PICTURE

This is the full pipeline the owner is building:

```
YouTube Videos (raw knowledge)
    ↓
YT Lab v2 (transcript → game plan → synthesis → tool ideas)
    ↓
Build Planner (preset rules + PRD + phases → bash scripts)
    ↓
5-Role Pipeline (architect → coder → reviewer → verifier → cartographer)
    ↓
Deployed Tool (Google Sheet or web app)
    ↓
Marketing Stack (email capture → nurture → cross-sell other tools)
```

The owner's goal: **3 tools per day**, drawn from a library of 50-60 ideas, using preset build rules that get better over time. The YT Lab is the INTAKE — where raw YouTube knowledge becomes actionable tool specs. The Build Planner is the FACTORY — where specs become running code. The verification protocol is QUALITY CONTROL. The marketing stack is DISTRIBUTION.

Each piece feeds the next. This PRD covers the intake stage.
