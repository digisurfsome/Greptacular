# ATTACK PLAN: Affiliate Marketing Engine + Automated YouTube System

> **Status**: ACTIVE — Execute Immediately
> **Date**: March 13, 2026
> **Priority**: Revenue-generating. This funds everything else.

---

## The Opportunity (Plain English)

Jonathan's affiliate program: up to $900/customer, $35 average per click, $357 average sale, 75% commission on entry products. Weekly live training events that pitch the big package. You already made $1,000+ from one sale years ago. He's legit — watched him grow from 5am videos before work to $15M+.

**The play**: Don't sell your own stuff as the front-facing product yet. Use his proven system as the revenue engine. You push traffic → his funnel converts → you earn commissions → you give away YOUR tools as bonuses for people who buy the bigger packages → this builds YOUR audience → eventually you flip to selling direct with paid ads.

**The math**:
- 10 clicks/day × $35/click = $350/day
- 100 clicks/day = $3,500/day
- 1,000 clicks/day = $35,000/day
- 10,000 total clicks = $350,000

**Traffic strategy**: Automated YouTube tutorial channels + viral TikTok/Instagram AI content. Not you on camera. AI-generated tutorials, walkthroughs, voiceovers, screen recordings. 50-100 videos/day at scale across multiple channels.

---

## The Human Body Analogy (How Tools Get Built)

This is the architecture for EVERYTHING we build:

- **Bones** = Deterministic code (the reliable, repeatable parts — upload schedules, file management, API calls)
- **Joints** = AI prompting (the flexible decision-making parts — writing scripts, choosing topics, adapting content)
- **Brain** = Open-source GitHub tools (the heavy lifting already built — video generators, voice synthesizers, SEO analyzers)

Every tool we make is a mix of these three. We're not building everything from scratch. We're not doing everything with prompts. We're assembling a body.

---

## TOOLS TO BUILD (Priority Order)

### Tool 1: Video Intelligence Combiner
**What it does**: Takes multiple YouTube video transcripts about the same topic, combines them, and extracts:
- What's the same across all videos (the proven core — 80%)
- What's unique to each video (the missing pieces — 15%)
- What's contradictory (needs human judgment — 5%)
- What none of them covered but research found (the edge — bonus)

**Why it's first**: Every other tool needs this. Before you build any automation, you need to combine the knowledge from 3-5 top creators into one super-blueprint. This is the "fill up the tool with everything possible" engine.

**How it works**:
1. Paste 3-5 YouTube URLs about the same topic
2. All transcripts get extracted and processed
3. AI cross-references them and produces a unified knowledge document
4. Gap analysis runs automatically (web search + GitHub scan)
5. You get a report: "Here's everything combined. Here's what's new. Approve?"
6. You check boxes in 30 seconds
7. NOW it goes to YT Lab to build the tool

**Open-source candidates**: `youtube-transcript-api`, text similarity/clustering libraries, existing transcript tools

### Tool 2: YouTube Automation Factory
**What it does**: Creates complete tutorial-style YouTube videos on autopilot:
- AI writes the tutorial script from a topic/keyword
- AI generates screen recording walkthrough or slide-based visual
- AI generates voiceover (text-to-speech)
- AI creates thumbnail
- AI writes title, description, tags (SEO optimized)
- Auto-uploads to YouTube channel

**Why it's second**: This IS the traffic engine. No traffic = no clicks = no commissions. This tool directly prints money.

**Components needed**:
- Script writer (prompt chain — the "joints")
- Video generator (open-source tool — the "brain") — look at: Remotion, FFmpeg automation, Puppeteer for screen recordings
- Voice synthesizer (open-source/API — the "brain") — ElevenLabs API, Coqui TTS (open source), Bark
- Thumbnail generator (AI image + template overlay)
- YouTube uploader (deterministic code — the "bones") — YouTube Data API v3, `youtube-upload` CLI tools
- SEO optimizer (hybrid) — keyword research + tag generation

**Open-source candidates**: `Remotion` (programmatic video), `yt-dlp` (research), `Bark`/`Coqui TTS` (voice), `youtube-upload`, various GitHub YouTube automation repos

### Tool 3: YouTube SEO & Keyword Engine
**What it does**: Researches and maps out every possible keyword arrangement for a topic area, then creates a content calendar showing exactly which videos to make and in what order.

**Why it's third**: Without this, the Video Factory is shooting blind. This tells it WHAT to make.

**Components**:
- Keyword research (scrape YouTube autocomplete, Google Trends, competitor analysis)
- Topic clustering (group related keywords into video topics)
- Competition analysis (what's already ranking, where are the gaps)
- Content calendar generation (priority order, posting schedule)
- Keyword-to-script pipeline (feeds directly into Tool 2)

**Open-source candidates**: YouTube autocomplete scrapers, `google-trends-api`, various SEO tools on GitHub

### Tool 4: Viral Short-Form Content Machine
**What it does**: Creates viral TikTok/Instagram Reels/YouTube Shorts about AI topics that funnel viewers to the affiliate offer.

**Why it's fourth**: This is the FAST traffic. YouTube tutorials are long-game SEO. Short-form viral content can get clicks TODAY.

**Your concept**: AI-themed viral videos, each unique but following a proven theme/format, posted 3-5x daily across platforms. Shareable, eye-catching, drives curiosity about AI tools.

**Components**:
- Viral hook writer (AI — what makes people stop scrolling)
- Short video generator (15-60 second clips)
- Multi-platform uploader (TikTok, Instagram, YouTube Shorts simultaneously)
- A/B testing different hooks/styles
- Link-in-bio / call-to-action optimization

**Open-source candidates**: FFmpeg for video editing, various social media API tools, `instagrapi`, TikTok upload tools

### Tool 5: Attack Plan Organizer (The War Room)
**What it does**: A dashboard where you map out multi-tool campaigns. You define the objective (e.g., "Get 10,000 clicks to Jonathan's offer"), then wire together the tools needed to accomplish it.

**Why it's fifth**: Once you have the content tools (1-4), you need to orchestrate them into campaigns. This is the command center.

**Features**:
- Campaign builder: define objective → list required tools → wire them together
- Video source collector: paste YouTube URLs, organize by topic, track what's been processed
- Tool status dashboard: which tools are running, what's their output
- Revenue tracker: clicks sent, estimated commissions, conversion rates
- Quick-add: "I just saw a new video" → paste URL → it finds where it fits in existing tools → updates the tool

**This is basically the YT Lab dashboard evolved into a campaign command center.**

---

## WHAT YOU NEED TO DO TODAY (Your Action Items)

### Right Now (Next 2 Hours)
1. **Sign up / confirm Jonathan's affiliate program** — get your affiliate link, understand the commission structure, get any affiliate resources he provides
2. **Find 3-5 YouTube videos about YouTube automation** — creators you trust who explain the full process of making automated tutorial channels. These feed into Tool 1.
3. **Find 2-3 YouTube videos about YouTube SEO/keywords** — how the algorithm works in 2025/2026, keyword strategies, tagging systems
4. **Find 1-2 YouTube videos about viral short-form content** — what makes AI content go viral on TikTok/Instagram

### Today (Next 6 Hours)
5. **Set up the affiliate funnel basics** — your affiliate link, a simple landing page or link-in-bio, tracking in place
6. **Draft your bonus offer** — what free tools/resources do you give people who buy through your link? This doesn't need to be built yet, just defined
7. **Start collecting video URLs** in a list — every video that will feed into the tools above. Organize by topic: (a) YouTube automation, (b) SEO/keywords, (c) viral content, (d) affiliate marketing funnels

### This Week
8. **Feed the first batch of videos into YT Lab** — start with YouTube automation videos → combine knowledge → build Tool 2 (the video factory)
9. **Set up your first YouTube channel** — name, branding, description optimized for the niche
10. **Set up TikTok/Instagram accounts** — for the viral short-form content
11. **Post your FIRST piece of content manually** — don't wait for automation. Put something out there today even if it's rough. One TikTok. One YouTube short. Prove the concept manually first.

---

## THE FLYWHEEL (How This Compounds)

```
Week 1: Manual content + affiliate link live
         ↓
Week 2: Tool 1 (Combiner) built → better tool blueprints
         ↓
Week 3: Tool 2 (Video Factory) built → automated tutorials start posting
         ↓
Week 4: Tool 3 (SEO Engine) built → videos target right keywords
         ↓
Month 2: Tool 4 (Viral Machine) built → short-form drives immediate traffic
          ↓
Month 2: First significant commission checks coming in
          ↓
Month 2: Take 50% of commissions → paid ads
          ↓
Month 3: Paid ads + organic + viral = massive traffic
          ↓
Month 3: Jonathan notices your volume → invites you on lives
          ↓
Month 3-4: You become known as the automation guy
          ↓
Month 4+: Start selling YOUR tools directly
          ↓
Month 6+: High-ticket consulting ($5k-$20k)
          ↓
Full flywheel spinning: traffic → commissions → reinvest → more traffic → your brand grows → direct sales
```

---

## THE TOOL UPDATE SYSTEM (Living Tools)

You said it perfectly: "5 hours later I see another video and we need to add it."

**How it works**:
1. Every tool has a **knowledge base** — all the source material that built it
2. When you find a new video/article/tool, you throw it at the system
3. The Video Intelligence Combiner (Tool 1) compares new info against existing knowledge
4. It says: "This video has 2 new techniques not in your current tool. Here they are."
5. You approve
6. Tool gets updated and redeployed immediately
7. Every instance of that tool (every channel using it) gets the update

**Tools are never frozen. They're living systems that get better every time you feed them new information.**

---

## REVENUE PROJECTIONS (Conservative)

| Timeline | Daily Clicks | Daily Revenue | Monthly Revenue |
|----------|-------------|---------------|-----------------|
| Week 1 (manual) | 5-10 | $175-350 | — |
| Week 4 (first automation) | 20-50 | $700-1,750 | $21k-52k |
| Month 2 (full automation) | 100-200 | $3,500-7,000 | $105k-210k |
| Month 3 (+ paid ads) | 500-1,000 | $17,500-35,000 | $525k-1M |
| Month 6 (+ direct sales) | 1,000+ | $35,000+ + tool sales | $1M+ |

These numbers use Jonathan's stated $35/click average. Your actual results depend on traffic quality and conversion rates. But even at 10% of these numbers, you're profitable from week 1.

---

## WHAT I BUILD NEXT (For You In YT Lab)

Once you bring me the YouTube videos, here's the build order:

1. **Video Intelligence Combiner** — Feed it your YouTube automation videos
2. **YouTube SEO Engine** — Feed it your keyword strategy videos
3. **YouTube Video Factory** — Feed it videos about automated video creation
4. **Viral Short-Form Machine** — Feed it videos about viral TikTok/IG content
5. **Attack Plan Dashboard** — Wire it all together

Each tool gets built from combined video knowledge + research + open-source GitHub tools. The human body: bones (code), joints (AI), brain (open source).

---

## KEY INSIGHT YOU HAD

> "These YouTube videos are just being turned into text. We just need to turn everything into a text format, combine them, find what's different, find what's additive, and then build."

That's exactly right. The Video Intelligence Combiner is the unlock. Once that exists, every tool gets built from the combined wisdom of the best creators in that space, not just one video. And it keeps getting better because you can always throw more text at it.

> "Everyone wants to make a tool. We're making a flexible tool that changes every day."

This is the paradigm shift. Tools aren't products you ship and forget. They're living systems that improve every time new information comes in. The infrastructure supports continuous updates pushed instantly.

---

*This document is the attack plan. Execute in order. Revenue starts flowing before the infrastructure is complete — that's the whole point.*
