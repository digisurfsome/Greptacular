# Content Brief Generator

> **Replaces:** SurferSEO, Frase, Clearscope, MarketMuse
> **Saves:** $49-$149/mo in tool costs + 1-2 hours per brief

## What This Skill Does

Takes a target keyword and produces a production-ready content brief that a writer (human or AI) can execute against. Includes SERP analysis, content structure, semantic terms, and competitive positioning.

## When to Use

- Creating new blog posts, landing pages, or service pages
- Refreshing underperforming content
- Scaling content production across multiple writers
- Client content deliverables

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Target keyword** - Primary keyword to rank for
2. **Secondary keywords** (2-5) - Related terms to include
3. **Target URL** (if updating existing content)
4. **Content type** - Blog post, landing page, service page, guide
5. **Word count target** - Or leave blank for recommendation
6. **Client brand voice** (if available in brand context)

### Step 2: SERP Analysis

Analyze what's currently ranking by examining:

**Top 10 Analysis Framework:**
- What content types dominate? (listicle, guide, tool, comparison)
- What's the average word count of top results?
- What subtopics do ALL top results cover? (must-include topics)
- What subtopics do only 1-2 results cover? (differentiation opportunities)
- What's missing from all results? (content gap = your angle)
- What questions appear in "People Also Ask"?
- What related searches appear at bottom of SERP?

### Step 3: Build the Brief

Structure the brief with these sections:

```markdown
# Content Brief: [Target Keyword]

## Overview
- **Target Keyword:** [primary]
- **Secondary Keywords:** [list]
- **Search Intent:** [informational/commercial/transactional]
- **Content Type:** [blog/landing/service/guide]
- **Target Word Count:** [X - Y words]
- **Target Audience:** [who is searching this]
- **Goal:** [what should the reader do after reading]

## Title Options
1. [Option with exact keyword match]
2. [Option with emotional hook]
3. [Option with number/data]

## Meta Description
[155 characters max, includes keyword, has CTA]

## Recommended URL Slug
/[keyword-slug]/

## Content Outline

### H1: [Title]

### H2: [Section 1 - Address search intent immediately]
- Key points to cover
- Data/stats to include
- [word count allocation: ~X words]

### H2: [Section 2]
- Key points to cover
- [word count allocation: ~X words]

[Continue for all H2s]

### H2: FAQ Section
- Q: [People Also Ask question 1]
- Q: [People Also Ask question 2]
- Q: [People Also Ask question 3]

## Semantic Terms to Include
[List 15-25 related terms that should appear naturally in the content]

## Internal Links to Include
- Link to: [existing page URL] with anchor text: [suggested anchor]
- Link to: [existing page URL] with anchor text: [suggested anchor]

## External Links / Sources
- [Authoritative source to reference]
- [Data/study to cite]

## Competitive Differentiation
- What competitors cover that we MUST include: [list]
- What competitors MISS that we should add: [list]
- Our unique angle: [what makes this better than what's ranking]

## Visual Assets Needed
- [ ] Featured image
- [ ] [Infographic / chart / diagram description]
- [ ] [Screenshot needs]

## CTA Strategy
- Primary CTA: [what action to drive]
- CTA placement: [where in the content]
- Secondary CTA: [email signup, related content, etc.]
```

### Step 4: Quality Checks

Before delivering:
- [ ] Brief addresses the exact search intent (not tangential)
- [ ] Outline covers ALL subtopics from top-ranking content
- [ ] At least one differentiation angle identified
- [ ] Word count is realistic for the topic depth
- [ ] Semantic terms are natural (not keyword stuffed)
- [ ] Internal linking opportunities identified
- [ ] CTA matches business goal

## Output Format

Save to: `outputs/content-briefs/[client-name]/[keyword-slug]-brief.md`

## Batch Mode

For producing multiple briefs at once:
1. Accept a list of keywords from the Keyword Research skill output
2. Generate briefs in priority order
3. Save each to the output folder
4. Produce a summary index file linking to all briefs

## Notes

Pairs with:
- **Keyword Research** skill (feeds target keywords in)
- **Meta Tag Optimizer** skill (refine titles/descriptions)
- **Internal Linking Strategist** skill (linking recommendations)
