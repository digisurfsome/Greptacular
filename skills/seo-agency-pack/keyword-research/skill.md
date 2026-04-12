# Keyword Research & Clustering

> **Replaces:** Ahrefs Keyword Explorer, Semrush Keyword Magic Tool, Keywords Everywhere
> **Saves:** $99-$249/mo in tool costs + 3-5 hours per research session

## What This Skill Does

Takes a seed topic or URL and produces a full keyword research deliverable:
- Keyword list with search intent classification
- Topic clusters grouped by semantic relevance
- Content gap opportunities
- Priority scoring based on difficulty vs. opportunity
- Ready-to-use content calendar mapping

## When to Use

- New client onboarding (initial keyword universe)
- Quarterly content planning
- Launching a new service page or blog category
- Competitive keyword gap fill

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Seed topic or URL** - What's the main topic or existing page?
2. **Business type** - What does the client sell/offer?
3. **Target location** - Local, national, or international?
4. **Current rankings** (if available) - What are they already ranking for?
5. **Competitors** (2-3 URLs) - Who are they competing against?

### Step 2: Generate Keyword Universe

Using the seed topic, generate keywords across these categories:

**By Intent:**
- Informational (how to, what is, guide, tutorial)
- Commercial Investigation (best, top, review, comparison, vs)
- Transactional (buy, hire, service, near me, pricing, cost)
- Navigational (brand + keyword combinations)

**By Funnel Stage:**
- Top of Funnel: broad awareness terms
- Middle of Funnel: comparison and evaluation terms
- Bottom of Funnel: purchase/hire intent terms

**By Modifier Type:**
- Question modifiers (how, what, why, when, where, can)
- Location modifiers (city, state, "near me")
- Long-tail variations (3-5 word phrases)
- LSI/semantic variations

### Step 3: Cluster by Topic

Group keywords into topic clusters:
- Each cluster gets a **pillar page** (broad topic)
- Each cluster gets 5-15 **supporting pages** (specific subtopics)
- Map internal linking structure between pillar and supporting content

Use this format for each cluster:

```
## Cluster: [Topic Name]
Pillar: [Main keyword - target page type]
Search Intent: [Informational / Commercial / Transactional]
Priority: [High / Medium / Low]

Supporting Keywords:
- [keyword 1] | [intent] | [suggested content type]
- [keyword 2] | [intent] | [suggested content type]
- [keyword 3] | [intent] | [suggested content type]
```

### Step 4: Priority Scoring

Score each cluster on a 1-10 scale using:

| Factor | Weight | Description |
|--------|--------|-------------|
| Relevance | 30% | How closely does this match what the business offers? |
| Opportunity | 25% | Is there content gap here competitors aren't filling? |
| Estimated Difficulty | 25% | How competitive is the SERP? (check top results) |
| Business Impact | 20% | Does ranking here directly drive leads/revenue? |

### Step 5: Output Deliverable

Produce a structured markdown document with:

1. **Executive Summary** - Top 5 opportunities, recommended priorities
2. **Full Keyword Universe** - All keywords organized by cluster
3. **Topic Cluster Map** - Visual hierarchy of pillar → supporting content
4. **90-Day Content Calendar** - Which clusters to attack first, in what order
5. **Quick Wins** - Low-competition keywords to target immediately

## Output Format

Save to: `outputs/keyword-research/[client-name]-[date].md`

## Quality Checks

Before delivering:
- [ ] Every keyword has intent classification
- [ ] Clusters have clear pillar/supporting hierarchy
- [ ] Priority scores are justified, not arbitrary
- [ ] Content calendar is realistic (not 50 posts in month 1)
- [ ] Quick wins are genuinely low competition (check SERPs if possible)

## Notes

This skill works best when combined with:
- **Competitor Gap Analysis** skill (feed competitor data in)
- **Content Brief Generator** skill (turn priorities into briefs)
- **SEO Report Generator** skill (track progress over time)
