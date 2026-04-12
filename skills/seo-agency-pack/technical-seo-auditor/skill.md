# Technical SEO Auditor

> **Replaces:** Screaming Frog report generation, Sitebulb summaries, manual audit spreadsheets
> **Saves:** $259/yr tool cost + 4-8 hours per audit report

## What This Skill Does

Takes a website URL or crawl data export and produces a prioritized technical SEO audit with specific fix recommendations. Focuses on actionable findings, not just listing problems.

## When to Use

- New client onboarding audit
- Quarterly technical health checks
- After a site migration or redesign
- When organic traffic drops unexpectedly
- Pre-launch technical review

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Website URL** - The site to audit
2. **Crawl data** (optional) - Screaming Frog CSV export, Sitebulb export, or similar
3. **Google Search Console data** (optional) - Coverage report, Core Web Vitals
4. **Known issues** - Anything the client already knows about
5. **Site platform** - WordPress, Shopify, custom, etc.
6. **Site size** - Approximate number of pages

### Step 2: Audit Categories

Analyze each category and assign a health score (Red / Yellow / Green):

**1. Crawlability & Indexation**
- Robots.txt analysis (blocking important pages?)
- XML sitemap presence and validity
- Index bloat (indexed pages vs. intended pages)
- Crawl budget issues (for large sites)
- Noindex/nofollow misuse
- Canonical tag implementation
- Pagination handling

**2. Site Architecture**
- URL structure and hierarchy
- Click depth (important pages within 3 clicks?)
- Orphan pages (pages with no internal links)
- Faceted navigation issues
- Breadcrumb implementation
- Internal link distribution

**3. Page Speed & Core Web Vitals**
- LCP (Largest Contentful Paint) - target < 2.5s
- INP (Interaction to Next Paint) - target < 200ms
- CLS (Cumulative Layout Shift) - target < 0.1
- Image optimization opportunities
- Render-blocking resources
- Server response time

**4. On-Page Technical Elements**
- Title tag issues (missing, duplicate, too long/short)
- Meta description issues
- H1 tag issues (missing, multiple, duplicate)
- Image alt text coverage
- Structured data/schema markup
- Hreflang (for multi-language sites)

**5. Mobile & UX**
- Mobile-friendliness
- Viewport configuration
- Touch target sizing
- Content parity (mobile vs desktop)

**6. Security & Trust**
- HTTPS implementation
- Mixed content issues
- Security headers
- SSL certificate validity

**7. Redirect & Error Management**
- 404 errors (broken pages)
- Redirect chains (more than 1 hop)
- Redirect loops
- 301 vs 302 usage
- Soft 404s

### Step 3: Priority Scoring

For each issue found, classify:

| Priority | Criteria | Action Timeline |
|----------|----------|-----------------|
| Critical | Blocking indexation or causing major traffic loss | Fix this week |
| High | Significantly impacting rankings or UX | Fix within 2 weeks |
| Medium | Moderate impact, improving would help rankings | Fix within 30 days |
| Low | Minor issues, nice to have | Fix when convenient |

### Step 4: Output Deliverable

```markdown
# Technical SEO Audit: [Client Name]
**Date:** [date]
**Audited by:** [your agency name]
**Site:** [URL]

## Executive Summary
- Overall Health Score: [X/100]
- Critical Issues: [count]
- High Priority Issues: [count]
- Estimated Traffic Impact of Fixes: [description]

## Health Scorecard

| Category | Score | Status |
|----------|-------|--------|
| Crawlability & Indexation | X/100 | [Red/Yellow/Green] |
| Site Architecture | X/100 | [Red/Yellow/Green] |
| Page Speed & CWV | X/100 | [Red/Yellow/Green] |
| On-Page Elements | X/100 | [Red/Yellow/Green] |
| Mobile & UX | X/100 | [Red/Yellow/Green] |
| Security | X/100 | [Red/Yellow/Green] |
| Redirects & Errors | X/100 | [Red/Yellow/Green] |

## Critical Issues (Fix Immediately)
### Issue 1: [Name]
- **What:** [description]
- **Why it matters:** [impact on rankings/traffic]
- **How to fix:** [specific steps]
- **Pages affected:** [count or list]
- **Estimated effort:** [hours]

[Repeat for each critical issue]

## High Priority Issues
[Same format]

## Medium Priority Issues
[Same format]

## Low Priority Issues
[Same format]

## 30-Day Fix Roadmap
Week 1: [Critical fixes]
Week 2: [High priority fixes]
Week 3-4: [Medium priority fixes + monitoring]

## Appendix
- Full issue list with affected URLs
- Tool/data sources used
```

### Step 5: Quality Checks

Before delivering:
- [ ] Every issue has a specific fix recommendation (not just "fix this")
- [ ] Priority levels are justified by actual impact
- [ ] Fix roadmap is realistic for client's team size
- [ ] No false positives (verify issues are real)
- [ ] Executive summary is non-technical enough for client stakeholders

## Output Format

Save to: `outputs/technical-audits/[client-name]-audit-[date].md`

## Notes

This produces the REPORT, not the crawl itself. For the actual crawl data, the agency still needs Screaming Frog or similar. This skill turns raw crawl data into a client-ready deliverable in minutes instead of hours.
