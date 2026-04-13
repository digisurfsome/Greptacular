# Wizard Questionnaire — Gaps & Improvements Log

> **What this is:** Real-time notes from running the wizard on actual systems. Every gap was discovered by hitting it during a live run — not theorized, observed. This file grows with each new system we run through the wizard. After ~10 runs, the gaps should stabilize and the wizard gets updated.

---

## Source: YouTube Video Intelligence Pipeline (Run #1)

Date: 2026-04-12

---

### STRUCTURAL GAPS (the wizard's question flow is missing these)

#### Gap 1: No "How many phases/levels?" question
**What happened:** The video system has two distinct phases — Ingest (always runs) and Filter (on demand). The wizard assumes a flat sequence of steps. I had to add "Level 1" and "Level 2" headers myself.
**What to add:** After A2, ask: *"Is this a single-pass process, or does it have distinct phases? Could someone use just Phase 1 without Phase 2? How many phases are there?"* Then repeat Section B per phase, not just per step.

#### Gap 2: No "Does this step repeat?" question
**What happened:** Filter Execution runs N times based on user choice — could be 1 filter or 7. The wizard's B section assumes each step runs once.
**What to add:** After B1, ask: *"Does this step run once per item, or can it repeat multiple times? If it repeats, what determines how many times? (User choice, data-driven, fixed count?)"*

#### Gap 3: No "Growing options library" concept
**What happened:** Filter types are a list that grows over time — tool extractor, checklist, skill creator, etc. New ones get added as the user discovers new use cases. The wizard doesn't capture dynamic option sets.
**What to add:** When B3 identifies decisions with options, ask: *"Are these options fixed (always the same list), or do new options get added over time? If they grow, who adds them — the user or the system?"*

#### Gap 4: No "Presets / saved combinations" concept  
**What happened:** The user wants to save common filter combinations as one-click presets (e.g., Preset 1 = transcript + worksheet only, Preset 2 = transcript + worksheet + checklist + tool spec). The wizard doesn't capture this.
**What to add:** In Section C or as a new question: *"Are there common combinations of choices/options that should be saved as reusable presets? What would Preset 1 be? Preset 2?"*

#### Gap 5: No "Cross-item batch/merge" concept
**What happened:** User wants to combine 3 videos through one filter to get a unified output. The wizard processes items one at a time — no concept of merge/combine operations.
**What to add:** After A5, ask: *"Do items ever need to be processed together as a group? Can you combine multiple items through the same step to get one merged output?"*

---

### PRACTICAL GAPS (things every build needs that the wizard never asks about)

#### Gap 6: No credentials/API keys checklist
**What happened:** The system needs YouTube API key, OpenAI/Whisper API key, Anthropic API key, Supabase URL + anon key, Telegram bot token. The wizard asks "what tools?" (A8) but never asks "what credentials do you need, and where do you get them?"
**What to add:** After A8, for each tool with an API, ask: *"What credential is needed? (API key, OAuth token, bearer token, username/password?) Where do you get it? Is it free or paid? Any setup steps required (create a bot, register an app, enable an API)?"*

Proposed format addition to A8:

| Tool/Service | What it's used for | Has API? | Credential Type | How to Get It | Setup Steps |
|---|---|---|---|---|---|
| | | | | | |

#### Gap 7: No environment/dependency setup section
**What happened:** The build needs Node.js or Python, specific packages (yt-dlp, whisper, anthropic SDK), a database (Supabase), possibly Docker. The wizard goes from architecture straight to "build it" with no setup checklist.
**What to add:** New section between C and D, or beginning of D: *"What needs to be installed before this system can run? List every runtime, package, service, and tool that must be set up on the machine."*

#### Gap 8: No cost-per-run estimation
**What happened:** I had to improvise cost math in D3 ($0.006/min for Whisper x 10 videos x 15 min = $27/month). The wizard asks "what's your budget?" but not "what does each API call cost and how many will you make per run?" You need both to know if the budget works.
**What to add:** Expand D3 to include per-step cost estimation:

| Step | API Used | Cost per Call | Calls per Run | Daily Cost | Monthly Cost |
|---|---|---|---|---|---|
| | | | | | |

#### Gap 9: No rate limits / throttling question
**What happened:** If you queue 10 videos at once, you'll hit YouTube API rate limits, Whisper API concurrent limits, Claude API rate limits. The wizard never asks about this.
**What to add:** In B7 (API tools), add: *"What are the rate limits? (requests/minute, requests/day, concurrent connections?) What happens when you hit the limit — queued, rejected, throttled?"*

#### Gap 10: No prompt template capture
**What happened:** The filter system's entire value IS the prompt templates. Each filter type is basically a Claude prompt that says "take this worksheet and extract X in Y format." The wizard captures what each step DOES but not the actual prompts that drive AI steps.
**What to add:** When B4 says "Yes, Claude can decide" — ask: *"What should the prompt look like? Write out the key instructions Claude needs. What format should the output be in? Any specific rules or constraints?"* This becomes the seed for the actual prompt template in the build file.

#### Gap 11: No "How does the user interact?" question
**What happened:** The wizard captures the backend pipeline perfectly but never asks about the user interface. Is this a CLI? A web app? A Telegram bot? A Slack command? An API endpoint? This determines the entire frontend architecture.
**What to add:** New question in Section A: *"How will you trigger and interact with this system? (CLI command, web interface, chat bot, API call, scheduled/automatic, combination?)"*

#### Gap 12: No data retention / storage lifecycle
**What happened:** Transcripts and filter outputs pile up. 10 videos/day = 300/month = 3,600/year. The wizard asks about state tracking (C1-C3) but not "how long do you keep data? Do you archive? Do old items get purged?"
**What to add:** In Section C, after C3: *"How long should processed data be kept? (Forever, 30 days, 1 year?) Should old data be archived, deleted, or compressed? What happens when storage grows large?"*

#### Gap 13: No output quality validation
**What happened:** How do you know a worksheet is GOOD? How do you know a filter output is actually useful? The wizard asks about success metrics (D1) but those are system-level. Individual output quality needs its own check.
**What to add:** After B5 (what's the output): *"How do you know the output is good? What does a 'bad' output look like? Should there be a quality check before the output is saved/delivered? (Human review, automated validation, confidence score?)"*

#### Gap 14: No versioning / re-processing concept
**What happened:** Filter prompts WILL improve over time. When you make a better checklist prompt, do you want to rerun all old videos through the new version? The wizard has no concept of prompt versioning or re-processing.
**What to add:** In Section C or as part of the "growing options" question: *"When you improve how a step works (better prompt, better rules), do you want to reprocess old items with the new version? Or is the old output fine as-is?"*

#### Gap 15: No dependency chain question
**What happened:** This system depends on Supabase being set up with specific tables, a Telegram bot existing, API keys being configured. If those aren't done first, the build fails. The wizard doesn't capture "what must exist BEFORE this system can be built?"
**What to add:** New question in Section A: *"What must already be set up before this system can work? (Database tables, API accounts, other systems running, infrastructure?) List every prerequisite."*

#### Gap 16: No sample data / test case
**What happened:** The build file will be more useful if it includes a specific test case — "use this exact YouTube URL to test the pipeline end-to-end." The wizard never asks for a concrete example to validate against.
**What to add:** In Section D, after D4 (MVP): *"Give me one specific example to test with. What's the exact input? What should the output look like? (This becomes the acceptance test for the build.)"*

#### Gap 17: No rollback / undo concept
**What happened:** What if a filter produces garbage? Can you delete the output and rerun? What if a worksheet is bad — can you re-trigger Step 3 without re-transcribing? The wizard has error cases (B8) for failures, but not for "it succeeded but the output is wrong."
**What to add:** After B8 (error case): *"What if this step succeeds but the output is bad? Can the user redo just this step? What gets thrown away and what gets kept?"*

#### Gap 18: No access control / permissions
**What happened:** Right now it's solo. But if this becomes a tool others use (or a SaaS), who can do what? The wizard asks "who needs to know?" (C4) but not "who can trigger runs, who can add filter types, who can see results?"
**What to add:** In Section C: *"Who can use this system? Just you, or others too? If others: can everyone do everything, or do different people have different access levels?"*

---

### META-INSIGHT: The Training Flywheel

The user identified something important: **the wizard improves by running it on real systems.** The process is:

1. Find a YouTube video describing a manual process
2. Transcribe it (this is literally what the Video Intelligence system does)
3. Run the wizard on the described process
4. Hit gaps → add them to this file
5. After ~10 runs, the gap list stabilizes
6. Update the wizard questionnaire with all discovered gaps
7. The wizard is now comprehensive enough to handle most processes

**This means the Video Intelligence system is the TRAINING TOOL for the wizard itself.** It's recursive — building this system makes the wizard better, and the better wizard builds better systems.

After 10 different process types, the wizard should be nearly complete. The kinds of processes to run through it:

- [x] Cold email warmup (done — simple, single-phase)
- [x] Bounce handling (done — simple, single-phase)
- [x] Reply classification (done — simple, single-phase)
- [x] CAN-SPAM compliance (done — simple, single-phase)
- [x] Domain health monitoring (done — simple, single-phase)
- [x] YouTube Video Intelligence (done — complex, multi-phase, stackable)
- [ ] Next: pick from user's lined-up app ideas
- [ ] Next: pick a completely different domain (not cold email, not content)
- [ ] Next: pick something with heavy human-in-the-loop
- [ ] Next: pick something with real-time / streaming requirements

---

### PRIORITY ORDER FOR WIZARD UPDATE

If we update the wizard questionnaire next, add these in this order (highest impact first):

1. **Credentials/API keys checklist** (Gap 6) — every single system needs this
2. **User interaction method** (Gap 11) — CLI vs web vs bot changes everything
3. **Multi-phase question** (Gap 1) — catches complex systems early
4. **Repeating steps** (Gap 2) — catches dynamic/stackable patterns
5. **Prompt template capture** (Gap 10) — AI-driven steps need this
6. **Environment/dependency setup** (Gap 7) — every build needs a setup checklist
7. **Cost-per-run estimation** (Gap 8) — budget validation
8. **Sample test case** (Gap 16) — makes the build file immediately testable
9. **Output quality validation** (Gap 13) — how do you know it's working right
10. **Rate limits** (Gap 9) — matters for batch/scale
11. **Prerequisites/dependencies** (Gap 15) — what must exist first
12. **Rollback/undo** (Gap 17) — handling bad-but-"successful" outputs
13. **Growing options library** (Gap 3) — extensible systems
14. **Presets** (Gap 4) — common combinations
15. **Cross-item merge** (Gap 5) — batch processing
16. **Data retention** (Gap 12) — long-term operations
17. **Versioning/reprocessing** (Gap 14) — prompt improvement lifecycle
18. **Access control** (Gap 18) — multi-user scenarios (lower priority for solo operator)
