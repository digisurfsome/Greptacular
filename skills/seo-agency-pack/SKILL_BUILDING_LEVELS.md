# Skill Building Levels: The 7-Level Framework

> **Source:** Caleb's skill building guide (200+ hours, 20+ production skills)
> **Why this matters:** Skills are the foundation of everything we're building and selling. Understanding these levels means we can build better skills, assess marketplace skills faster, and teach clients what "good" looks like.

---

## The 7 Levels at a Glance

| Level | Name | What You Can Do | Business Value |
|-------|------|----------------|----------------|
| 1 | Install & Use | Drop in someone else's skill, Claude follows it | "I can use pre-built tools" |
| 2 | Build Properly | Create lean, well-structured skills that trigger correctly | "I can build custom automations" |
| 3 | Import & Refactor | Take bloated marketplace skills and fix them | "I can leverage anyone's expertise" |
| 4 | Contextualize | Add brand/business context so outputs sound like YOU | "My AI actually knows my business" |
| 5 | Evaluate & Measure | Test skills with benchmarks, A/B test reference files | "I know what works and what doesn't" |
| 6 | Self-Improving | Skills learn from every interaction via feedback loops | "My system gets better without me" |
| 7 | Orchestrated System | Skills work together, sharing context and triggering each other | "I have an AI workforce, not AI tools" |

---

## Level 1: Install & Use

**What it is:** Download a skill folder, drop it in `.claude/skills/`, Claude follows the instructions.

**Structure:**
```
skill-name/
  skill.md          ← Required. The brain. Claude reads this.
  scripts/           ← Optional. Executable code (API calls, data processing)
  references/        ← Optional. Deep knowledge Claude pulls when needed
  assets/            ← Optional. Templates, fonts, icons
```

**The one required file:** `skill.md` — an SOP (standard operating procedure) that tells Claude what to do, when, and how.

**Key concept: Progressive Disclosure (3 tiers)**

| Tier | What | When It Loads | Size Limit |
|------|------|--------------|-----------|
| Tier 1 | YAML front matter (name, description, triggers) | ALWAYS loaded every session | Part of 15,000 char total across ALL skills |
| Tier 2 | Body of skill.md (the actual steps) | Only when skill is ACTIVATED | Keep under 200 lines |
| Tier 3 | Reference files, scripts, assets | Only when a specific step NEEDS it | 200-300 lines each |

**Why this matters for us:** When we install skills for a client, we need to be mindful of how many skills they have. Too many = bloated Tier 1 context = everything degrades.

---

## Level 2: Build Properly

**The golden rule:** Keep skill.md under 200 lines max.

**Why:** Not arbitrary. It's based on how much context an LLM can efficiently scan to decide what to load next. Think of skill.md as a TABLE OF CONTENTS, not an encyclopedia.

**The two mistakes everyone makes:**

### Mistake 1: Everything in one file
- Bad: 1,000+ line skill.md with all knowledge dumped in
- Result: Context window explodes, Claude drifts, ignores instructions
- Fix: Skill.md = process steps (under 200 lines). Details = reference files.

### Mistake 2: Vague descriptions
- Bad: "Helps with SEO stuff"
- Result: Skill triggers 20% of the time (industry average for marketplace skills)
- Fix: Use the 3-part description framework:

**Description Framework:**
```yaml
---
description: |
  TRIGGERS: [specific keywords/phrases that should activate this skill]
  Example: "research what's trending", "trending topics", "Reddit research"
  
  DOES NOT TRIGGER: [what should NOT activate it]
  Example: "general web browsing", "simple URL fetching"
  
  PRODUCES: [what the output looks like]
  Example: "A research brief with trending topics, engagement metrics, and analysis"
---
```

**For our skills:** Every skill we built should be checked against this. Are any of them over 200 lines? Do they all have proper trigger/no-trigger/produces descriptions?

---

## Level 3: Import & Refactor

**The problem:** Most marketplace skills have great content but terrible structure. 400-1000+ line skill.md files with no progressive disclosure.

**The fix:** Use Anthropic's skill creator skill (or a custom meta-skill) to refactor:
1. Identify what Claude needs to see IMMEDIATELY (→ stays in skill.md)
2. Everything else → references/ folder
3. Add proper YAML front matter with trigger/no-trigger/produces

**Real example from the video:**
- Before: AI SEO skill at 400 lines in skill.md
- After: 148 lines in skill.md + 4 reference files
- Result: 60% reduction in context loaded per activation

**For our business:**
- When we find skills on GitHub/Reddit from our scraping → refactor them to proper structure before installing
- When a client has existing skills that aren't working → THIS is the service: "Your skills are bloated. Let me fix them."
- Refactoring is a sellable service on its own: $200-$500 per skill cleanup

---

## Level 4: Contextualize (Where Real Value Starts)

**The insight:** A generic skill produces generic output. A contextualized skill produces output that sounds like the business.

**What to add to every skill's references:**
- Brand voice / tone guidelines
- Audience personas / ICP
- Product/service details
- Competitor positioning
- Content pillars
- Case studies / proof points

**How it connects:** The skill.md includes a "Context Needs" section:
```markdown
## Context Needs
| Context File | What It Provides | When to Load |
|-------------|-----------------|-------------|
| brand-context/positioning.md | Brand differentiators | During content framing |
| brand-context/icp.md | Target audience details | During audience targeting |
| brand-context/voice-profile.md | Tone and style rules | During all content creation |
```

**For our business - THIS IS THE SERVICE:**
- We don't just install skills. We CONTEXTUALIZE them.
- Setup fee ($500-$1000) = building their brand context files + wiring them into every skill
- This is what makes the outputs go from "AI-generated" to "sounds like our team wrote it"
- Without this step, Claude is a generalist. WITH it, Claude is their employee.

**For our SEO agency skills:** Each skill we built should reference the client's brand context. We should add a `context-needs` section to every skill.md showing what business context it pulls from.

---

## Level 5: Evaluate & Measure

**The problem:** Before this, it's all "vibes" — you think the output is good but can't prove it or measure improvement.

**What Anthropic built:** Evaluation and benchmarking inside the skill creator skill.

**How it works:**
1. Define 3-5 criteria for what "good" looks like
2. Run the skill 5 times against a test task
3. Each run is graded against your criteria
4. Get a benchmark score (pass rate %, time, tokens)

**A/B Testing:**
- Run 5 times WITH a specific reference file
- Run 5 times WITHOUT it
- Compare: Does the reference file actually improve quality or just burn tokens?

**Real result from video:**
- With reference files: 93% pass rate, 184 seconds, higher token usage
- Without some references: 93% pass rate, LESS time, FEWER tokens
- Insight: Some reference files don't improve quality — just cost money

**For our business:**
- Before selling a skill to a client, we can PROVE it works: "This skill produces output that meets your criteria 93% of the time"
- When optimizing skills, we can measure before/after instead of guessing
- We can offer "skill optimization" as a service — run evals, prune unnecessary references, improve trigger rates

**For our skills:** Run evals on our top 10 skills. Which reference files actually matter? Which are just burning context? Prune the dead weight.

---

## Level 6: Self-Improving (Feedback Loops)

**The concept:** Skills learn from every interaction and get better over time via a `learnings.md` file.

**How it works:**
1. After every task, observations get captured in a learnings/rules file
2. The skill.md references this file so Claude reads it on every activation
3. Over time, the skill accumulates knowledge about what works and what doesn't

**Examples of learnings:**
- "Articles that open with a direct answer to the search query get picked up by AI search faster"
- "Comparison tables in the middle of articles increase time on page"
- "Meta descriptions under 140 chars perform better than those at 155"

**The wrap-up skill:** At the end of every session, any skill used + feedback given gets logged into `learnings.md` on a skill-by-skill basis.

**Critical rule:** Keep learnings file under control. Prune weekly. Too much = its own context problem.

**Connects to Level 5:** Use evals to validate that learnings are actually improving output quality. Run same eval before and after learnings → see the improvement.

**For our business:**
- When we set up a client, include the wrap-up skill so their system improves automatically
- After 3 months, their skills are dramatically better than day 1 — without them doing anything
- This is recurring value: "Your system gets smarter every time you use it"

**For our skills:** Add a learnings.md to each skill folder. Start capturing patterns from our own usage.

---

## Level 7: Orchestrated System (Skills Working Together)

**The endgame:** Skills aren't isolated tools — they're a coordinated workforce.

**How it works:**
- Skill A (copywriting) calls Skill B (humanizer) before saving output
- Skill C (content repurposing) calls Skill D (YouTube transcript puller) when it can't get transcripts
- All skills pull from shared brand context
- Skills trigger each other based on workflow needs

**Examples from the video:**
- Copywriting skill → passes ALL copy through humanizer skill before saving
- Content repurposing skill → uses YouTube transcript skill when needed
- All content skills → reference positioning doc + ICP + voice profile

**For our business:**
- This is the ultimate upsell: "I'm not just giving you 10 separate tools. I'm giving you a system where they all work together."
- An SEO agency workflow: Keyword Research → Content Brief → Blog Writer → Humanizer → Schema Markup → Internal Linking → all in one flow
- This is the difference between "$500 setup" and "$2,000 system build"

---

## How This Maps to Our Offerings

### When WE Build Skills (For Ourselves or Clients)

| Our Skill | Current Level | Should Be At | What's Missing |
|-----------|--------------|-------------|---------------|
| Keyword Research | 2 (properly built) | 4 (contextualized) | Brand context references, ICP targeting |
| Content Brief Generator | 2 | 4 | Voice profile, content pillar references |
| Technical SEO Auditor | 2 | 4 | Client-specific checklist preferences |
| All 10 skills | 2 | 4-6 | Context needs, learnings.md, eval criteria |

### When We ASSESS a Client's Skills

**Use this checklist during the Business Assessment:**

| Check | Level | Question to Ask/Verify |
|-------|-------|----------------------|
| Do they have skills at all? | 0-1 | "Are you using any skills in Claude Code?" |
| Are skills under 200 lines? | 2 | Check their skill.md files |
| Do descriptions have trigger/no-trigger/produces? | 2 | Check YAML front matter |
| Are marketplace skills refactored? | 3 | Check for bloated skill.md files |
| Is brand context wired in? | 4 | Check for context needs / brand references |
| Are they running evals? | 5 | "How do you know your skills work?" |
| Do skills have learnings files? | 6 | Check for learnings.md / feedback loops |
| Do skills work together? | 7 | Check for cross-skill references |

**Most businesses will be at Level 0-1.** Our service moves them to Level 4-5 immediately.

### Service Tiers Based on Skill Levels

| Service | What We Do | Skill Level Delivered | Price |
|---------|-----------|----------------------|-------|
| Quick Install | Install pre-built skills, basic config | Level 1-2 | $250 |
| Custom Setup | Install + contextualize + brand config | Level 4 | $750-$1,000 |
| Full System Build | Contextualized + evals + feedback loops + orchestration | Level 6-7 | $2,000-$3,000 |
| Skill Optimization | Audit existing skills, refactor, add evals | Level 3→5 | $200-$500/skill |
| Ongoing Tuning | Monthly learnings review, eval runs, skill updates | Level 6 maintenance | $200-$500/mo |

---

## Quick Reference: Skill Quality Checklist

Before delivering ANY skill (to ourselves or a client):

- [ ] skill.md under 200 lines
- [ ] YAML front matter has trigger / no-trigger / produces
- [ ] Detailed knowledge is in references/ not skill.md
- [ ] Each reference file is 200-300 lines max
- [ ] Brand context is wired in via context needs section
- [ ] learnings.md exists (even if empty to start)
- [ ] 3-5 eval criteria defined for testing
- [ ] Cross-skill connections documented (if applicable)

---

## The Pitch Angle

When talking to a business:

> "Most people who try AI skills find they work about 20% of the time. That's because 90% of skills out there are badly built — they're bloated, they don't trigger correctly, and they don't know anything about your business.
>
> What I do is build skills at a completely different level. They're lean so they don't slow things down. They're contextualized to YOUR brand, YOUR audience, YOUR processes. They test themselves. They learn from every interaction. And they work together as a system, not isolated tools.
>
> In 3 months, your skills will be dramatically better than day 1 — automatically. That's not something you get from installing a plugin."
