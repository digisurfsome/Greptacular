# Competitor Gap Analysis

> **Replaces:** Ahrefs Content Gap tool, Semrush Keyword Gap, manual competitor research
> **Saves:** $99-$249/mo in tool costs + 2-4 hours per analysis

## What This Skill Does

Compares a client's content and keyword coverage against 2-5 competitors to find gaps and opportunities. Produces a prioritized list of content to create or improve.

## When to Use

- New client strategy development
- Quarterly content planning
- When a competitor starts outranking the client
- Before building a new content hub or topic cluster
- When the client asks "why is [competitor] ranking above us?"

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Client URL** - The site we're analyzing
2. **Competitor URLs** (2-5) - Direct competitors
3. **Industry/niche** - For context on what matters
4. **Client's top pages** (if known) - Their current best performers
5. **Target keywords** (if available) - From keyword research skill output
6. **Competitor data exports** (optional) - Ahrefs/Semrush exports if available

### Step 2: Analysis Framework

**A. Content Coverage Gaps**

For each competitor, catalog:
- What topics do they cover that the client doesn't?
- What content types do they use? (tools, calculators, guides, templates)
- What content depth do they provide? (surface vs. comprehensive)
- What content formats? (video, infographic, interactive, long-form)

Produce a matrix:

```
| Topic | Client | Comp 1 | Comp 2 | Comp 3 | Gap? |
|-------|--------|--------|--------|--------|------|
| [topic] | Yes/No | Yes/No | Yes/No | Yes/No | [Y/N] |
```

**B. Keyword Coverage Gaps**

Identify keywords where:
- ALL competitors rank but client doesn't (high priority)
- 2+ competitors rank but client doesn't (medium priority)
- 1 competitor ranks well, others don't (potential quick win)
- Client ranks but lower than all competitors (optimization opportunity)

**C. Content Quality Gaps**

For topics where client HAS content, compare:
- Word count / depth
- Freshness (last updated date)
- Media richness (images, video, interactive elements)
- E-E-A-T signals (author bios, citations, expertise markers)
- User engagement signals (comments, shares if visible)

**D. Technical/Feature Gaps**

- Do competitors have tools/calculators the client doesn't?
- Do competitors have better site structure/navigation?
- Do competitors have FAQ sections, schema markup, featured snippet optimization?
- Do competitors have better internal linking?

### Step 3: Opportunity Scoring

Score each gap opportunity:

| Factor | Weight | Scale |
|--------|--------|-------|
| Search Volume Potential | 25% | 1-10 (estimated traffic opportunity) |
| Competition Level | 25% | 1-10 (inverse - lower competition = higher score) |
| Business Relevance | 25% | 1-10 (how closely it ties to revenue) |
| Effort to Create | 25% | 1-10 (inverse - easier = higher score) |

**Priority Tiers:**
- Score 8-10: Attack immediately
- Score 5-7: Plan for next quarter
- Score 1-4: Backlog / long-term

### Step 4: Output Deliverable

```markdown
# Competitor Gap Analysis: [Client Name]
**Date:** [date]
**Competitors Analyzed:** [list]

## Executive Summary
- Total content gaps identified: [count]
- High-priority opportunities: [count]
- Estimated traffic opportunity: [description]
- Top 3 recommended actions:
  1. [action]
  2. [action]
  3. [action]

## Content Coverage Matrix
[Full topic matrix from Step 2A]

## Top 20 Keyword Gaps
| Keyword | Est. Volume | Competitors Ranking | Difficulty | Priority |
|---------|-------------|--------------------| -----------|----------|
[Sorted by priority score]

## Content Quality Gaps (Existing Pages to Improve)
| Client Page | Issue | Competitor Benchmark | Recommended Fix |
|-------------|-------|---------------------|-----------------|
[List pages where client has content but it's weaker]

## Feature/Tool Gaps
[List of tools, calculators, or interactive content competitors have]

## 90-Day Attack Plan
### Month 1: Quick Wins
- [Low effort, high opportunity gaps to fill]

### Month 2: Core Content
- [Medium effort, high-value content to create]

### Month 3: Differentiation
- [Unique angle content that leapfrogs competitors]

## Individual Competitor Breakdowns
### [Competitor 1]
- Strengths: [what they do well]
- Weaknesses: [where they're vulnerable]
- Key content to study: [their best pages]

[Repeat for each competitor]
```

## Output Format

Save to: `outputs/competitor-analysis/[client-name]-gap-analysis-[date].md`

## Notes

## Context Needs

| Context File | What It Provides | When to Load |
|-------------|-----------------|-------------|
| `references/brand-context.md` | Business identity, one-line description | Always — defines what "our content" covers |
| `references/brand-context.md` → Competition | Competitor names, URLs, strengths | Always — these ARE the competitors being analyzed |
| `references/brand-context.md` → SEO Specifics | Current rankings, target keywords, domain authority | During gap scoring — assess realistic difficulty |
| `references/brand-context.md` → Content Strategy | Content pillars, topics to avoid | During opportunity filtering — skip gaps outside content pillars |

**Without brand context:** Compares generic content coverage between sites.
**With brand context:** Identifies gaps specifically relevant to the client's niche, filters out irrelevant competitor content, and scores opportunities against the client's actual ranking ability.

## Notes

Pairs with:
- **Keyword Research** skill (cross-reference keyword gaps)
- **Content Brief Generator** skill (turn top gaps into briefs immediately)
