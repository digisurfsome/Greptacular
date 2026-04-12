# Internal Linking Strategist

> **Replaces:** Link Whisper, InLinks, manual internal link auditing
> **Saves:** $77-$228/yr in tool costs + 3-6 hours per audit

## What This Skill Does

Analyzes a site's content inventory and produces an internal linking strategy: what pages should link to what, with specific anchor text recommendations. Identifies orphan pages, over-linked pages, and linking gaps.

## When to Use

- After publishing new content (where should it link, what should link to it)
- Quarterly internal link audits
- Building topic cluster structures
- Fixing orphan pages
- After keyword research identifies pillar/cluster hierarchy
- When pages aren't ranking despite good content (often a linking issue)

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Site URL or content inventory** - List of all pages with URLs and target keywords
2. **Sitemap** (optional) - XML sitemap for full page list
3. **Current site crawl data** (optional) - Internal link data from Screaming Frog or similar
4. **Topic clusters** (if defined) - From keyword research skill output
5. **Priority pages** - Which pages matter most for rankings/revenue?

### Step 2: Build the Link Map

**A. Categorize All Pages**

For every page, identify:
- Page type (pillar, supporting, product, service, blog, resource)
- Target keyword
- Topic cluster it belongs to
- Current internal links pointing TO it (inlinks)
- Current internal links pointing FROM it (outlinks)

**B. Identify Issues**

| Issue | What It Means | Fix |
|-------|--------------|-----|
| Orphan pages | 0 internal links pointing to page | Add links from related content |
| Thin link pages | Only 1-2 internal links pointing to page | Add 3-5 more contextual links |
| Over-linked pages | 50+ internal links (dilutes value) | Reduce to most relevant links |
| Broken internal links | Links pointing to 404 pages | Fix URL or remove link |
| Pillar pages with few links | Topic authority not flowing properly | Every cluster page should link to pillar |
| Missing cross-cluster links | Related topics not connected | Add contextual bridges |

**C. Define Link Hierarchy**

```
[Pillar Page: "SEO Services"]
  ├── [Supporting: "On-Page SEO Guide"] → links to pillar
  ├── [Supporting: "Technical SEO Checklist"] → links to pillar
  ├── [Supporting: "Local SEO Tips"] → links to pillar
  ├── [Supporting: "Link Building Strategies"] → links to pillar
  └── Cross-cluster link to → [Pillar: "Content Marketing"]
```

### Step 3: Generate Recommendations

For each recommendation, provide:

```markdown
### Link Recommendation #[X]
- **From page:** [URL of page that should contain the link]
- **To page:** [URL of page being linked to]
- **Suggested anchor text:** [exact text to use as link]
- **Context:** [sentence or paragraph where link naturally fits]
- **Priority:** [High / Medium / Low]
- **Reason:** [Why this link helps - relevance, orphan fix, pillar support, etc.]
```

**Anchor Text Rules:**
- Primary anchor: Exact match or close variant of target keyword (use sparingly)
- Secondary anchors: Natural language variations
- Never: "click here", "read more", "learn more" as sole anchor
- Mix it up: Don't use identical anchor text for all links to the same page
- Keep it contextual: The anchor should make sense in the sentence

### Step 4: Output Deliverable

```markdown
# Internal Linking Strategy: [Client Name]
**Date:** [date]
**Pages Analyzed:** [count]

## Summary
- Total internal linking issues found: [count]
- Orphan pages: [count]
- Thin-linked priority pages: [count]
- Recommended new links to add: [count]
- Recommended links to remove: [count]

## Issues Found

### Orphan Pages (No Internal Links)
| Page | Target Keyword | Recommended Action |
|------|---------------|-------------------|
[List all orphan pages]

### Under-Linked Priority Pages
| Page | Current Inlinks | Target Inlinks | Gap |
|------|----------------|----------------|-----|
[Priority pages that need more internal links]

## Link Recommendations (Sorted by Priority)
[All recommendations from Step 3]

## Topic Cluster Link Map
[Visual hierarchy showing how clusters should link together]

## Implementation Checklist
- [ ] [Page X]: Add link to [Page Y] with anchor "[text]"
- [ ] [Page X]: Add link to [Page Z] with anchor "[text]"
[Continue for all recommendations]
```

## Output Format

Save to: `outputs/internal-linking/[client-name]-link-strategy-[date].md`

## Notes

This is one of the highest-ROI SEO activities and most agencies do it manually or not at all. A proper internal linking strategy can move rankings significantly with zero new content creation.

## Context Needs

| Context File | What It Provides | When to Load |
|-------------|-----------------|-------------|
| `references/brand-context.md` → Content Strategy | Content pillars, blog URL | Always — defines the hub-and-spoke structure for linking |
| `references/brand-context.md` → Products & Services | Main offerings | During link prioritization — ensure money pages get link equity |
| `references/brand-context.md` → SEO Specifics | Target keywords | During anchor text optimization — align anchor text with ranking targets |

**Without brand context:** Maps existing pages and suggests logical links.
**With brand context:** Prioritizes links toward money pages and conversion targets, uses strategically chosen anchor text aligned with keyword targets, and structures the link graph around content pillars.
