# SEO Report Generator

> **Replaces:** AgencyAnalytics, DashThis, manual Google Sheets reporting
> **Saves:** $49-$199/mo in tool costs + 2-4 hours per report per client

## What This Skill Does

Takes raw SEO data (rankings, traffic, conversions) and produces a client-ready monthly SEO report. Translates technical metrics into business outcomes the client actually cares about.

## When to Use

- Monthly client reporting
- Quarterly business reviews
- Campaign performance summaries
- New client baseline/benchmark reports

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Client name and URL**
2. **Reporting period** - Month/quarter
3. **Data sources** (any combination):
   - Google Analytics / GA4 export (traffic, conversions)
   - Google Search Console export (impressions, clicks, positions)
   - Rank tracking data (keyword positions)
   - Backlink data (new/lost links)
   - Previous month's report (for comparison)
4. **Client goals** - What KPIs matter to this client?
5. **Work completed this period** - What did the agency actually do?
6. **Tone** - Technical (marketing manager) or simple (business owner)

### Step 2: Report Structure

```markdown
# SEO Performance Report
**Client:** [Name]
**Period:** [Month Year]
**Prepared by:** [Agency Name]

---

## The Headlines
[3-4 bullet points a CEO can read in 10 seconds]
- Organic traffic [up/down] X% vs last month
- [Top achievement this month]
- [Key metric movement]
- [Next month focus]

---

## Traffic Overview

### Organic Traffic
- This month: [sessions]
- Last month: [sessions]
- Change: [+/- %]
- Year over year: [+/- %]

### Traffic by Landing Page (Top 10)
| Page | Sessions | Change | Top Keyword |
|------|----------|--------|-------------|
[Top 10 pages by organic sessions]

### Traffic by Device
- Desktop: [%]
- Mobile: [%]
- Tablet: [%]

---

## Keyword Rankings

### Summary
- Keywords tracked: [count]
- Keywords in top 3: [count] ([change])
- Keywords in top 10: [count] ([change])
- Keywords in top 20: [count] ([change])
- Average position: [number] ([change])

### Biggest Wins
| Keyword | Previous Position | Current Position | Change |
|---------|-------------------|-----------------|--------|
[Top 5-10 improvements]

### Positions to Watch
| Keyword | Position | Notes |
|---------|----------|-------|
[Keywords close to page 1, or dropping]

---

## Conversions & Business Impact

### Goal Completions from Organic
- Leads/form fills: [count] ([change])
- Phone calls: [count] ([change])
- [Custom goal]: [count] ([change])

### Revenue Attribution (if available)
- Estimated revenue from organic: $[amount]
- Cost per lead from SEO: $[amount]
- ROI on SEO investment: [X]%

---

## Technical Health

### Site Health Score: [X/100]
- Critical issues: [count]
- Warnings: [count]
- Issues fixed this month: [count]

### Core Web Vitals
| Metric | Score | Status |
|--------|-------|--------|
| LCP | [time] | [Pass/Fail] |
| INP | [time] | [Pass/Fail] |
| CLS | [score] | [Pass/Fail] |

---

## Backlink Profile
- Total referring domains: [count] ([change])
- New links this month: [count]
- Lost links this month: [count]
- Domain authority/rating: [score] ([change])

### Notable New Links
| Source | DA/DR | Type |
|--------|-------|------|
[Top 3-5 new backlinks]

---

## Work Completed This Month

### Content
- [List of content created/published]

### Technical
- [List of technical fixes]

### Link Building
- [Outreach/link building activities]

### On-Page
- [Pages optimized]

---

## Next Month Plan

### Priorities
1. [Priority 1 with expected impact]
2. [Priority 2 with expected impact]
3. [Priority 3 with expected impact]

### Content Calendar
| Week | Content Piece | Target Keyword |
|------|--------------|----------------|
[4-week content plan]

---

## Appendix
[Full keyword ranking data, complete page-by-page data if needed]
```

### Step 3: Tone Adaptation

**For technical audience (marketing managers):**
- Include all metrics and data tables
- Use SEO terminology
- Show granular data

**For business owners:**
- Lead with business impact (leads, revenue, phone calls)
- Translate metrics: "Position 3 → you appear in the top 3 results on Google"
- Use visual indicators: arrows, color-coded status
- Keep it under 3 pages for the main report, put details in appendix

### Step 4: Quality Checks

Before delivering:
- [ ] All numbers are accurate (double-check calculations)
- [ ] Month-over-month comparisons use same date ranges
- [ ] Wins are highlighted (client needs to feel progress)
- [ ] Drops are explained honestly (with fix plan)
- [ ] Next month plan is specific and actionable
- [ ] No jargon without explanation (for business owner reports)
- [ ] Report tells a story, not just data dumps

## Output Format

Save to: `outputs/reports/[client-name]/[month-year]-seo-report.md`

## Batch Mode

For agencies with multiple clients:
1. Process each client's data in sequence
2. Generate individual reports
3. Produce an agency-level summary showing all clients' performance
