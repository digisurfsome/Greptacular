# ROI Calculator

> **Purpose:** Produce a one-page savings report that shows the prospect exactly how much time and money they'll save.
> **When to use:** After the demo, when they're interested but need to justify the expense (to themselves, a partner, or their team).
> **Output:** Clean markdown document they can share internally.

---

## Instructions

### Step 1: Gather Their Numbers

Ask for (or estimate during discovery):

**Tool Costs:**
- What SEO/marketing tools do you pay for monthly?
- List each tool and its monthly cost

**Time Costs:**
- How many hours/week does your team spend on [reporting / content briefs / audits / meta tags / etc.]?
- What's your team's effective hourly rate? (If they don't know, use $50-$75/hr for agency staff)
- How many clients do you serve?

**Revenue Context:**
- What do you charge per client per month?
- How many new clients could you take on if you had more capacity?

### Step 2: Calculate Savings

Use these formulas:

**Tool Replacement Savings:**
```
Monthly tool savings = Sum of tools being replaced
Annual tool savings = Monthly x 12
```

**Time Savings:**
```
Hours saved per task = (Current time - New time with Claude)
Monthly hours saved = Hours saved per task x Tasks per month
Monthly labor savings = Hours saved x Hourly rate
Annual labor savings = Monthly x 12
```

**Capacity Gains:**
```
New capacity (hours/month) = Hours saved from automation
Potential new clients = New capacity / Hours per client per month
Revenue potential = New clients x Monthly retainer
```

**Total ROI:**
```
Monthly investment = Claude Code subscription ($100-$200) + Setup fee amortized over 12 months
Monthly return = Tool savings + Labor savings + Revenue potential
ROI multiple = Monthly return / Monthly investment
Payback period = Setup fee / Monthly net savings
```

### Step 3: Produce the Report

```markdown
# ROI Analysis: AI-Powered SEO Operations
**Prepared for:** [Business Name]
**Date:** [Date]

---

## Your Current Costs

### Tools You're Paying For
| Tool | Monthly Cost | What You Use It For |
|------|-------------|-------------------|
| [Tool 1] | $[X] | [Primary use] |
| [Tool 2] | $[X] | [Primary use] |
| [Tool 3] | $[X] | [Primary use] |
| **Total** | **$[X]/mo** | |

### Time Your Team Spends

| Task | Hours/Month | Staff Rate | Monthly Cost |
|------|------------|-----------|-------------|
| [Task 1: e.g., Monthly reports] | [X] hrs | $[X]/hr | $[X] |
| [Task 2: e.g., Content briefs] | [X] hrs | $[X]/hr | $[X] |
| [Task 3: e.g., Meta tag optimization] | [X] hrs | $[X]/hr | $[X] |
| [Task 4: e.g., Technical audits] | [X] hrs | $[X]/hr | $[X] |
| **Total** | **[X] hrs/mo** | | **$[X]/mo** |

### Your Total Current Cost
- Tools: $[X]/month
- Labor on automatable tasks: $[X]/month
- **Total: $[X]/month ($[X x 12]/year)**

---

## With Claude Code Setup

### Tools Replaced
| Current Tool | Replaced By | Monthly Savings |
|-------------|------------|-----------------|
| [Tool 1] | [Skill name] | $[X] |
| [Tool 2] | [Skill name] | $[X] |
| [Tool 3] | [Skill name] | $[X] |
| **Total Tool Savings** | | **$[X]/mo** |

### Time Savings
| Task | Current Time | New Time | Hours Saved/Mo | Value Saved |
|------|-------------|----------|----------------|-------------|
| [Task 1] | [X] hrs | [X] min | [X] hrs | $[X] |
| [Task 2] | [X] hrs | [X] min | [X] hrs | $[X] |
| [Task 3] | [X] hrs | [X] min | [X] hrs | $[X] |
| [Task 4] | [X] hrs | [X] min | [X] hrs | $[X] |
| **Total** | | | **[X] hrs/mo** | **$[X]/mo** |

### Capacity Unlocked
- Hours freed up: [X] hours/month
- At your rate of [X] hrs/client/month: **[X] additional clients possible**
- At $[X]/client/month: **$[X] potential new revenue**

---

## The Math

### Investment
| Item | Cost | Frequency |
|------|------|-----------|
| Claude Code subscription | $[100-200] | Monthly |
| Setup & Configuration | $[750-1000] | One-time |
| **Monthly cost (amortized)** | **$[X]** | |

### Return
| Savings Type | Monthly | Annual |
|-------------|---------|--------|
| Tool replacement | $[X] | $[X] |
| Labor savings | $[X] | $[X] |
| Revenue capacity | $[X] | $[X] |
| **Total Return** | **$[X]** | **$[X]** |

### ROI Summary
- **Monthly net savings: $[X]**
- **Annual net savings: $[X]**
- **ROI multiple: [X]x your investment**
- **Payback period: [X] days**

---

## What This Looks Like

### Month 1
- System configured to your brand, clients, processes
- Team trained (2 hours)
- First reports generated automatically
- Immediate tool cancellations possible

### Month 2
- Full workflow running
- Team adapted to new process
- Additional skills activated as needed

### Month 3+
- Ongoing time savings compounding
- Additional clients taken on with freed capacity
- Custom skills added as new needs emerge

---

## Conservative vs. Optimistic

| Scenario | Monthly Savings | Annual Savings | Payback |
|----------|----------------|----------------|---------|
| Conservative (replace 2 tools, save 10 hrs) | $[X] | $[X] | [X] days |
| Moderate (replace 3 tools, save 20 hrs) | $[X] | $[X] | [X] days |
| Optimistic (replace 4 tools, save 30 hrs, add clients) | $[X] | $[X] | [X] days |

---

*This analysis is based on the information provided during our conversation on [date]. Actual results depend on implementation and usage consistency.*
```

### Step 4: Delivery

- Save as markdown
- Offer to convert to PDF if they need to share with a partner
- Follow up within 24 hours with "Did you get a chance to look at the numbers?"

---

## Quick Estimate Mode

If you don't have their exact numbers, use these industry averages for SEO agencies:

| Metric | Average |
|--------|---------|
| Monthly tool spend | $300-$800 |
| Hours on reporting per client | 2-4 hrs |
| Hours on content briefs | 1-2 hrs each |
| Staff hourly rate | $50-$75 |
| Clients served | 8-15 |
| Monthly retainer per client | $1,500-$5,000 |
| Hours per client per month | 10-20 |

Even with conservative estimates:
- Replace 2 tools: $200/mo saved
- Save 15 hrs/month on automatable tasks at $60/hr: $900/mo saved
- Total: $1,100/mo saved vs. ~$200/mo Claude Code cost = **5.5x ROI**
- Payback on $750 setup fee: **< 1 month**
