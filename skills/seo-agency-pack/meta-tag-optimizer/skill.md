# Meta Tag Optimizer

> **Replaces:** Yoast Premium, RankMath Pro meta suggestions, manual optimization
> **Saves:** $99/yr in plugin costs + 15-30 min per page

## What This Skill Does

Takes a list of pages (URLs or titles + target keywords) and produces optimized title tags and meta descriptions. Focuses on CTR optimization, not just keyword inclusion.

## When to Use

- Bulk meta tag optimization across a site
- New page launches
- Improving CTR on pages that rank but don't get clicks
- After keyword research identifies new targets
- Content refresh / re-optimization projects

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Page list** - URLs, page titles, or spreadsheet export
2. **Target keywords** per page
3. **Brand name** - For title tag branding pattern
4. **Title format preference** - e.g., "Primary Keyword | Brand" or "Primary Keyword - Secondary | Brand"
5. **Industry context** - What does the business do
6. **Current meta tags** (if optimizing existing pages)

### Step 2: Title Tag Rules

**Hard Rules:**
- Maximum 60 characters (Google truncates at ~580px, roughly 60 chars)
- Primary keyword appears as early as possible
- Brand name at end (separated by | or -)
- Every title must be unique across the site
- No keyword stuffing (keyword appears once, naturally)

**CTR Optimization Patterns:**
- Use numbers when relevant: "7 Ways to...", "2025 Guide"
- Use power words: "Complete", "Ultimate", "Proven", "Free"
- Match search intent in the title:
  - Informational: "How to...", "Guide to...", "What is..."
  - Commercial: "Best...", "Top...", "X vs Y"
  - Transactional: Include "Buy", "Hire", "Get", pricing signals
- Create curiosity gap where appropriate
- Consider what SERP competitors' titles look like and differentiate

**Formula options:**
```
[Primary Keyword]: [Benefit/Hook] | [Brand]
[Number] [Primary Keyword] [Power Word] [Year] | [Brand]
[Primary Keyword] - [Secondary Keyword] | [Brand]
How to [Primary Keyword] ([Benefit]) | [Brand]
```

### Step 3: Meta Description Rules

**Hard Rules:**
- Maximum 155 characters (Google truncates at ~920px)
- Include primary keyword (Google bolds matching terms)
- Include a call to action
- Must accurately describe page content
- Every description must be unique

**CTR Optimization:**
- Start with the value proposition or key benefit
- Include a specific detail (number, stat, timeframe)
- End with CTA: "Learn more", "Get started", "See pricing"
- Match the emotional tone to the search intent
- Consider using a question format for informational queries

**Formula:**
```
[What you'll get/learn]. [Specific detail/proof point]. [CTA].
```

### Step 4: Output Format

```markdown
# Meta Tag Optimization: [Client Name]
**Date:** [date]
**Pages Optimized:** [count]

| Page | Target Keyword | Title Tag | Chars | Meta Description | Chars |
|------|---------------|-----------|-------|-----------------|-------|
| [URL] | [keyword] | [optimized title] | [##] | [optimized description] | [###] |
```

Also provide implementation format:
```html
<!-- Page: [URL] -->
<title>[Optimized Title]</title>
<meta name="description" content="[Optimized Description]">
```

### Step 5: Quality Checks

Before delivering:
- [ ] No title exceeds 60 characters
- [ ] No description exceeds 155 characters
- [ ] No duplicate titles across the site
- [ ] No duplicate descriptions across the site
- [ ] Primary keyword present in every title
- [ ] Primary keyword present in every description
- [ ] Every description has a CTA
- [ ] Titles match search intent
- [ ] No clickbait that misrepresents page content

## Output Format

Save to: `outputs/meta-tags/[client-name]-meta-optimization-[date].md`

## Batch Mode

Can process 100+ pages at once. Provide a CSV or list with columns:
- URL
- Current Title
- Current Description
- Target Keyword

Output: Optimized versions for all pages in a single deliverable.
