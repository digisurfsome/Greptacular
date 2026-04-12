# Skill Template System: Customize Any Skill in Minutes

> **Purpose:** Give any business owner (or yourself when onboarding a new client) a structured way to take a generic skill and make it theirs. Training wheels that produce professional results.
> **Works as:** Internal tool, client handoff material, lead magnet content, tutorial content for YouTube

---

## The Concept

Every skill has two layers:
1. **Generic base** - The process, the steps, the structure (same for everyone)
2. **Custom fill-ins** - The brand voice, audience, specific preferences (unique per business)

The template system separates these cleanly. A business owner reads through, checks off what the generic version covers, and fills in blanks to customize. No skill-building knowledge needed.

---

## Template Structure

Every skill template has 3 sections:

### Section A: "Does This Cover You?" (Checklist)
Pre-filled capabilities of the generic skill. Business owner checks yes/no.
- If all yes → generic skill works fine, minimal customization needed
- If some no → those gaps become the customization spots

### Section B: "Make It Yours" (Required Fill-Ins)
The blanks that MUST be filled for the skill to produce good output.
These are the basics - brand name, audience, tone, etc.

### Section C: "Go Deeper" (Optional Customization)
Advanced questions that make the skill dramatically better but aren't required.
This is where a business owner who really knows their stuff can dial it in.
Beginners skip this. Pros fill it all in.

---

## Example Template: Content Brief Generator

### Section A: Does This Cover You?

| Capability | Included? | Notes |
|-----------|-----------|-------|
| Analyzes top-ranking content for your keyword | Yes | |
| Recommends word count and content type | Yes | |
| Creates full H2/H3 outline | Yes | |
| Includes semantic/LSI terms | Yes | |
| Identifies content gaps vs competitors | Yes | |
| Includes internal linking suggestions | Yes | |
| Writes meta title and description | Yes | |
| Matches your specific brand voice | **NO - needs Section B** | |
| Knows your product/service details | **NO - needs Section B** | |
| Follows your specific content guidelines | **NO - needs Section C** | |
| References your existing content library | **NO - needs Section C** | |

### Section B: Make It Yours (Required)

Fill in these fields. These get added to the skill's reference files.

**1. Business Identity**
```
Business Name: _______________
Website URL: _______________
Industry/Niche: _______________
What you sell/offer (1-2 sentences): _______________
```

**2. Target Audience**
```
Who is your ideal customer? _______________
What problem do they have? _______________
What do they search for when looking for you? _______________
Where are they located? (local/national/global) _______________
```

**3. Brand Voice**
```
Our tone is (pick 2-3): 
[ ] Professional  [ ] Casual  [ ] Authoritative  [ ] Friendly
[ ] Technical  [ ] Simple  [ ] Witty  [ ] Serious  [ ] Inspirational

Words we ALWAYS use: _______________
Words we NEVER use: _______________
We sound like: _______________ (example: "a smart friend who happens to be an expert")
```

**4. Content Basics**
```
Our blog URL: _______________
How often do we publish? _______________
Who writes the content? (in-house / freelance / AI-assisted) _______________
Primary goal of content: [ ] Traffic  [ ] Leads  [ ] Brand awareness  [ ] Education
```

### Section C: Go Deeper (Optional)

These make the skill significantly better but aren't required to start.

**5. Competitive Landscape**
```
Top 3 competitors:
1. _______________ (URL: _______________)
2. _______________ (URL: _______________)
3. _______________ (URL: _______________)

What makes us different from competitors: _______________
What do competitors do better than us: _______________
```

**6. Content Strategy Details**
```
Content pillars (main topics we cover):
1. _______________
2. _______________
3. _______________

Topics we explicitly AVOID: _______________
Existing high-performing content (URLs of our best posts):
1. _______________
2. _______________
3. _______________
```

**7. SEO Specifics**
```
Keywords we already rank for: _______________
Keywords we want to rank for: _______________
Do we have Google Search Console access? [ ] Yes  [ ] No
Do we have analytics data? [ ] Yes  [ ] No
Current domain authority/rating (if known): _______________
```

**8. Style Preferences**
```
Preferred content length: [ ] Short (500-800)  [ ] Medium (1000-1500)  [ ] Long (2000+)  [ ] Depends on topic
Use emojis? [ ] Yes  [ ] No  [ ] Sometimes
Include stats/data? [ ] Always  [ ] When relevant  [ ] Rarely
Call-to-action style: [ ] Direct ("Book a call")  [ ] Soft ("Learn more")  [ ] Question-based ("Ready to start?")
Format preference: [ ] Listicles  [ ] How-to guides  [ ] Deep dives  [ ] Mix of all
```

### How the Template Becomes a Skill

Once filled in:
- Section B answers → go into `references/brand-context.md`
- Section C answers → go into `references/strategy-context.md`  
- The skill.md gets a Context Needs section pointing to both files
- Claude loads brand-context on every run, strategy-context when relevant

---

## Master Template (Works for ANY Skill)

This is the universal fill-in that applies to every skill, not just content briefs.

### Universal Section B (Every Business Fills This Once)

```markdown
# Business Context Template

## Identity
- Business Name: ___
- Website: ___
- Industry: ___
- One-line description: ___
- Year founded: ___
- Location(s): ___

## Audience
- Primary customer type: ___
- Their biggest pain point: ___
- How they find us: ___
- Decision-making factors: ___

## Voice & Tone
- We sound like: ___
- Tone words (pick 3): ___
- Words we use: ___
- Words we avoid: ___
- Example sentence in our voice: ___

## Products/Services
- Main offering 1: ___ (price range: ___)
- Main offering 2: ___ (price range: ___)
- Main offering 3: ___ (price range: ___)
- What we're known for: ___

## Competition
- Competitor 1: ___ (their strength: ___)
- Competitor 2: ___ (their strength: ___)
- Our key differentiator: ___

## Goals
- #1 business goal right now: ___
- Biggest bottleneck: ___
- What success looks like in 90 days: ___
```

### Skill-Specific Section C Templates

Each skill type has its own deeper questions:

| Skill Type | Extra Questions |
|-----------|----------------|
| Content/Writing skills | Content pillars, style preferences, existing content library, SEO targets |
| Reporting skills | KPIs that matter, report frequency, audience (technical vs business owner), data sources |
| Technical/Audit skills | Platform (WordPress/Shopify/custom), known issues, priority areas, compliance requirements |
| Outreach/Email skills | Offer details, proof points, case studies, sending volume, objection history |
| Local SEO skills | Locations, service areas, GBP details, review platforms, local competitors |
| Client Management skills | Number of clients, retainer structure, deliverables per client, communication preferences |

---

## How to Use This System

### For You (Managing a New Client)

1. Send them the **Universal Section B** as a Google Form or simple doc
2. They fill it in (takes 15-20 minutes)
3. You convert their answers into `brand-context.md`
4. Drop that file into every skill's references folder
5. Now every skill is customized to their business

**That's what the $500-$1000 setup fee pays for.** You're not just installing skills - you're doing this translation work.

### For a Business Owner (Self-Service)

1. They open the template for the skill they want to customize
2. Check Section A - does the generic version work?
3. Fill in Section B - the basics
4. Optionally fill in Section C - go deeper
5. The system (or you) converts it into reference files
6. Skill is now personalized

### For Content/Tutorials

Each template is a tutorial:
- "How to Customize Your Content Brief Skill in 10 Minutes"
- "How to Set Up Your SEO Report Skill for Your Agency"
- "How to Make Claude Sound Like Your Brand"

Each video walks through the template, shows before/after outputs.

---

## Template Status

| Skill | Template Built? | Priority |
|-------|----------------|----------|
| Universal (brand context) | IN THIS DOC | Use for every client |
| Content Brief Generator | EXAMPLE ABOVE | High |
| SEO Report Generator | NOT BUILT | High - every agency needs |
| Keyword Research | NOT BUILT | Medium |
| Technical SEO Auditor | NOT BUILT | Medium |
| Cold Email | NOT BUILT | High - for our own outreach |
| Competitor Gap Analysis | NOT BUILT | Medium |
| Meta Tag Optimizer | NOT BUILT | Low - mostly automated |
| Schema Markup Generator | NOT BUILT | Low - mostly automated |
| Internal Linking | NOT BUILT | Low |
| Local SEO Optimizer | NOT BUILT | High - lots of custom data |

---

## The Guardrails (So They Don't Go Wild)

When handing this to a business owner, include these rules:

1. **Section B is mandatory.** Don't skip it. Generic skills produce generic output.
2. **Section C is optional.** Start without it. Add it later if outputs need improvement.
3. **Keep answers short.** One sentence per field. Claude doesn't need essays.
4. **Be specific, not aspirational.** "We help plumbers in Denver" not "We empower home service professionals to achieve excellence."
5. **Update quarterly.** Your business changes. Your context should too.
6. **One brand context file per business.** Don't create separate ones per skill - one master file, all skills reference it.
