# SEO Agency Skills Pack

Skills designed for SEO agencies using Claude Code. Each skill replaces or reduces dependency on paid tools.

## Skills Overview

| Skill | Replaces | Tool Cost Saved |
|-------|----------|-----------------|
| Keyword Research & Clustering | Ahrefs/Semrush keyword tools | $99-$249/mo |
| Content Brief Generator | SurferSEO / Frase | $49-$149/mo |
| Technical SEO Auditor | Screaming Frog reports | $259/yr |
| Competitor Gap Analysis | Ahrefs Content Gap | $99-$249/mo |
| Schema Markup Generator | Schema Pro / manual work | $79/yr + hours |
| SEO Report Generator | AgencyAnalytics / DashThis | $49-$199/mo |
| Meta Tag Optimizer | Yoast / RankMath premium | $99/yr |
| Internal Linking Strategist | Link Whisper / manual work | $77/yr + hours |
| Local SEO Optimizer | BrightLocal | $39-$79/mo |
| Cold Email for SEO Agencies | Instantly / Smartlead | $30-$97/mo |

**Total potential tool cost savings: $400-$1,200/mo per agency**

## How to Use

Each skill folder contains:
- `skill.md` - The main instruction file (drop into Claude Code skills directory)
- `learnings.md` - Auto-populated insights from each run (Level 6 feedback loop)
- `reference/` - Templates, examples, and supporting docs (where applicable)

All 10 skills are **Level 4** (contextualized) with brand context references. Fill out `references/brand-context-template.md` once per client and every skill automatically personalizes output.

## Installation

1. Copy `references/brand-context-template.md` → fill it out for the client → save as `references/brand-context.md`
2. Copy the skill folders into your `.claude/skills/` directory or the Agentic OS skills folder
3. Each skill's Context Needs section tells Claude when to load brand context

## Skill Level Status

| Level | Status | What It Means |
|-------|--------|--------------|
| Level 2: Properly Built | Done | Under 200 lines, proper YAML, progressive disclosure |
| Level 4: Contextualized | Done | Brand context references wired into every skill |
| Level 5: Evaluated | Next | Define eval criteria, run benchmarks |
| Level 6: Self-Improving | Scaffolded | learnings.md in every skill, ready for feedback loops |
| Level 7: Orchestrated | Planned | Cross-skill references documented in Notes sections |

## Supporting Documents

| Document | What It Covers |
|----------|---------------|
| `BUSINESS_PITCH_REPORT.md` | Discovery framework, pitch formulas, 5 core concepts for business owners |
| `SKILL_BUILDING_LEVELS.md` | 7-level framework for building and assessing skills |
| `AGENTIC_PATTERNS.md` | 5 patterns for running Claude Code, decision engine |
| `SKILL_TEMPLATES.md` | Questionnaire system for customizing skills per business |
| `REVENUE_STRATEGY.md` | Affiliate math, content calendar, full funnel strategy |
| `TOS_COMPLIANCE.md` | What you can/can't sell, OpenClaw analysis, safe business models |
| `sales-tools/` | Quick-win demos, ROI calculator, business assessment |

---

## Full Master List: Every Skill an SEO Agency Could Need

This is the complete list. The 10 skills above are BUILT. The rest are identified opportunities - build them as needed for specific clients or verticals.

### Content & On-Page (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| Keyword Research & Clustering | BUILT | Seed topic → full keyword universe with clusters, intent, priority scoring | Ahrefs/Semrush keyword tools |
| Content Brief Generator | BUILT | Target keyword → production-ready brief with SERP analysis, outline, semantic terms | SurferSEO / Frase / Clearscope |
| Meta Tag Optimizer | BUILT | Bulk title tag + meta description optimization with CTR focus | Yoast / RankMath Pro |
| Internal Linking Strategist | BUILT | Site-wide internal link audit + specific linking recommendations | Link Whisper / InLinks |
| Schema Markup Generator | BUILT | Page → valid JSON-LD structured data, any schema type | Schema Pro / manual coding |
| Blog Post Writer | NOT BUILT | Takes a content brief and writes the full post matching brand voice | Jasper / Copy.ai |
| Content Audit & Pruning | NOT BUILT | Identifies thin content, cannibalization, merge/delete/update recommendations | Manual spreadsheet work |
| Content Refresh Planner | NOT BUILT | Finds pages losing traffic/rankings and produces update plans | Manual GSC analysis |
| FAQ Generator | NOT BUILT | Pulls People Also Ask + industry questions → FAQ sections with schema | Manual research |
| Content Calendar Builder | NOT BUILT | Takes keyword clusters → mapped publishing schedule with dependencies | CoSchedule / spreadsheets |

### Technical SEO (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| Technical SEO Auditor | BUILT | Crawl data → prioritized audit report with fix recommendations | Screaming Frog report writing |
| Competitor Gap Analysis | BUILT | Client vs competitors → content/keyword gaps with priority scoring | Ahrefs Content Gap |
| Page Speed Optimizer | NOT BUILT | Analyzes Core Web Vitals data → specific fix recommendations per page | PageSpeed Insights manual work |
| Redirect Map Builder | NOT BUILT | Old URLs → new URLs mapping for site migrations | Manual spreadsheet mapping |
| Robots.txt & Sitemap Auditor | NOT BUILT | Reviews robots.txt + XML sitemaps for issues | Manual review |
| Hreflang Generator | NOT BUILT | Multi-language sites → correct hreflang tag implementation | Manual tag creation |
| Log File Analyzer | NOT BUILT | Server logs → crawl budget analysis and bot behavior insights | Screaming Frog log analyzer |
| Site Migration Checklist | NOT BUILT | Platform/domain migration → comprehensive pre/post launch checklist | Manual documentation |

### Local SEO (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| Local SEO Optimizer | BUILT | Full local SEO plan: GBP optimization, citations, reviews, local pages | BrightLocal / Whitespark |
| GBP Post Writer | NOT BUILT | Weekly Google Business Profile posts matching business events/offers | Manual posting |
| Review Response Generator | NOT BUILT | Auto-generates review responses matching brand voice (positive + negative) | Manual response writing |
| Citation Audit Report | NOT BUILT | Checks NAP consistency across directories → fix list | Moz Local / Yext |
| Location Page Generator | NOT BUILT | Bulk creates unique location/service-area landing pages | Manual page creation |

### Link Building & Outreach (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| Cold Email for SEO Agencies | BUILT | Complete cold email campaign: sequences, subject lines, objection handling | Instantly templates / Lemlist |
| Link Prospect Qualifier | NOT BUILT | List of URLs → scored by DA, relevance, likelihood of response | Manual prospect vetting |
| Guest Post Pitch Generator | NOT BUILT | Target site + topic → personalized pitch email | Manual outreach |
| Broken Link Finder Report | NOT BUILT | Competitor URLs → broken outbound links to build links from | Ahrefs broken link checker |
| HARO / Journalist Pitch Writer | NOT BUILT | Source request → expert response pitch for backlink opportunities | Manual HARO responses |
| Digital PR Angle Generator | NOT BUILT | Business + data → newsworthy story angles for press coverage | Manual brainstorming |

### Client Management & Reporting (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| SEO Report Generator | BUILT | Raw data → client-ready monthly report with business impact framing | AgencyAnalytics / DashThis |
| Client Onboarding Checklist | NOT BUILT | New client → complete onboarding workflow with data collection | Manual checklists |
| SEO Proposal Generator | NOT BUILT | Prospect info → professional proposal with pricing, timeline, deliverables | Manual proposal writing |
| Scope of Work Builder | NOT BUILT | Agreed services → detailed SOW document | Manual documentation |
| Quarterly Business Review | NOT BUILT | 3 months of data → QBR presentation with trends, wins, next quarter plan | Manual slide creation |
| Client Health Score | NOT BUILT | Ranks all clients by health metrics → flags at-risk accounts | Gut feel / manual tracking |
| Invoice & Deliverable Tracker | NOT BUILT | Tracks what was delivered vs what was promised per client | Spreadsheets |

### Agency Operations (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| SOP Writer | NOT BUILT | Process description → detailed standard operating procedure document | Manual documentation |
| Team Task Delegator | NOT BUILT | Project scope → broken down tasks assigned by role with deadlines | Manual project management |
| Competitor Agency Analyzer | NOT BUILT | Competitor agency URLs → pricing, services, positioning analysis | Manual research |
| Case Study Writer | NOT BUILT | Client results data → polished case study for marketing | Manual writing |
| Social Proof Collector | NOT BUILT | Client wins → formatted testimonials, stats, and case study snippets | Manual collection |

### Sales & Business Development (Skills)

| Skill | Status | What It Does | Replaces |
|-------|--------|-------------|----------|
| Sales Call Prep | NOT BUILT | Prospect URL → pre-call research brief with talking points and quick wins | Manual research |
| Objection Handler | NOT BUILT | Common SEO sales objections → response scripts with proof points | Sales training docs |
| ROI Calculator | NOT BUILT | Client data → projected SEO ROI with conservative/moderate/aggressive scenarios | Manual spreadsheet |
| Upsell Identifier | NOT BUILT | Current client services → expansion opportunities with justification | Manual account review |
| Churn Prevention Alert | NOT BUILT | Client signals → early warning system with save strategies | Gut feel |

---

## Summary Stats

| Category | Built | Not Built | Total |
|----------|-------|-----------|-------|
| Content & On-Page | 5 | 5 | 10 |
| Technical SEO | 2 | 6 | 8 |
| Local SEO | 1 | 4 | 5 |
| Link Building & Outreach | 1 | 5 | 6 |
| Client Management & Reporting | 1 | 6 | 7 |
| Agency Operations | 0 | 5 | 5 |
| Sales & Business Development | 0 | 5 | 5 |
| **TOTAL** | **10** | **36** | **46** |

## What to Build Next (Priority Order)

Based on what saves the most time and replaces the most expensive tools:

1. **Blog Post Writer** - Every agency needs content at scale
2. **Client Onboarding Checklist** - First impression with new clients
3. **SEO Proposal Generator** - Closes deals faster
4. **Content Audit & Pruning** - High-value deliverable clients love
5. **Sales Call Prep** - Makes every prospect call 10x better
6. **Review Response Generator** - Saves hours for local SEO clients
7. **Location Page Generator** - Pairs with the bulk page builder tool
8. **Case Study Writer** - Turns wins into more wins
9. **SOP Writer** - Scales the agency beyond the founder
10. **ROI Calculator** - Closes price objection immediately

## The Pitch

"I looked at your tool stack. You're paying $800/mo across 5-6 tools. I can replace 3 of them with AI skills that run inside Claude Code, save you $400/mo, AND the outputs are customized to your brand voice and clients. Let me set it up for you."
