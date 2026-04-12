# Local SEO Optimizer

> **Replaces:** BrightLocal, Whitespark, Moz Local
> **Saves:** $39-$79/mo in tool costs + 2-4 hours per location

## What This Skill Does

Produces a complete local SEO optimization plan for a business location. Covers Google Business Profile optimization, citation strategy, review management, and local landing page recommendations.

## When to Use

- New local business client onboarding
- Google Business Profile optimization
- Multi-location SEO strategy
- Local pack ranking improvements
- Citation cleanup projects
- Review generation strategy

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Business name** (exactly as it should appear)
2. **Business category** (primary + secondary)
3. **Address** (full, per location)
4. **Phone number** (per location)
5. **Service area** (if service-area business)
6. **Website URL**
7. **Current GBP listing URL** (if exists)
8. **Hours of operation**
9. **Services/products offered**
10. **Unique selling points** / differentiators
11. **Photos available?** (types: storefront, interior, team, work examples)

### Step 2: Google Business Profile Audit & Optimization

**Profile Completeness Check:**

| Field | Status | Recommendation |
|-------|--------|---------------|
| Business Name | [Match/Mismatch] | [Exact legal name, no keyword stuffing] |
| Primary Category | [Current] | [Recommended] |
| Secondary Categories | [Current] | [Add up to 9 relevant] |
| Address | [Verified?] | [Consistency check] |
| Phone | [Current] | [Local number preferred] |
| Website URL | [Current] | [Should link to location page, not homepage] |
| Hours | [Complete?] | [Include special hours, holiday hours] |
| Business Description | [Has one?] | [750 chars, keywords natural, value prop first] |
| Services | [Listed?] | [Add all with descriptions] |
| Products | [Listed?] | [Add if applicable] |
| Photos | [Count/Quality] | [Minimum 10, specific types needed] |
| Posts | [Active?] | [Weekly posting recommended] |
| Q&A | [Seeded?] | [Pre-populate top 5-10 FAQs] |
| Attributes | [Set?] | [All relevant attributes checked] |

**Optimized Business Description Template:**
```
[Business Name] is [city]'s [unique selling point] [business type]. 
We specialize in [primary services] for [target customers] in [service area]. 

[2-3 sentences about what makes this business different - awards, years in business, unique approach]

Services include: [list top services]

Serving [city/neighborhoods/service area]. [CTA - call or visit today].
```

### Step 3: Citation Strategy

**NAP Consistency:**
- Name, Address, Phone must be IDENTICAL everywhere
- Document the exact format to use:
  ```
  Business Name: [exact]
  Address: [exact, including suite/unit format]
  Phone: [exact format: (XXX) XXX-XXXX]
  Website: [exact URL]
  ```

**Priority Citation Sources (build/claim in order):**

Tier 1 (Essential):
1. Google Business Profile
2. Apple Maps / Apple Business Connect
3. Bing Places
4. Facebook Business Page
5. Yelp

Tier 2 (Important):
6. BBB
7. Yellow Pages / YP.com
8. Foursquare
9. Nextdoor
10. Industry-specific directories

Tier 3 (Supplemental):
11-20. Local directories, chamber of commerce, industry associations

**For each citation:**
- Claim or create listing
- Ensure NAP matches exactly
- Add complete business info (categories, hours, photos, description)
- Add tracking URL where possible

### Step 4: Review Strategy

**Review Generation Plan:**

1. **Goal:** [X reviews per month] (aim for steady flow, not spikes)
2. **Review link:** Generate short link to Google review form
3. **Ask process:**
   - When to ask: After positive service experience, within 24 hours
   - How to ask: Email template, SMS template, in-person script
   - Who asks: [role/person responsible]

**Review Response Templates:**

Positive (5 stars):
```
Thank you [name]! We're glad [specific thing they mentioned] went well. 
[Personal touch related to their review]. We look forward to [next interaction].
```

Negative (1-3 stars):
```
[Name], thank you for your feedback. We're sorry about [specific issue]. 
[Brief explanation without being defensive]. We'd like to make this right - 
please contact [name] at [phone/email] so we can resolve this for you.
```

### Step 5: Local Landing Page Recommendations

If the client needs location-specific pages:

```markdown
## Location Page Template: [City/Neighborhood]

### Required Elements:
- H1: [Service] in [City] - [Business Name]
- Unique content (NOT duplicated across locations) - minimum 800 words
- NAP in consistent format
- Embedded Google Map
- Location-specific photos
- Location-specific testimonials/reviews
- Service area description
- Driving directions from major landmarks
- FAQ section with local questions
- LocalBusiness schema markup (use Schema Markup Generator skill)
- Click-to-call button
- Contact form

### Content Sections:
1. Hero: Service + Location + CTA
2. Services offered at this location
3. Why choose us in [city] (local credibility)
4. Service area map and neighborhoods served
5. Customer reviews from this area
6. FAQ (location-specific questions)
7. Contact info + map + directions
```

### Step 6: Output Deliverable

```markdown
# Local SEO Optimization Plan: [Business Name]
**Location:** [Address]
**Date:** [date]

## GBP Optimization Checklist
[From Step 2 - every field with current status and action needed]

## Citation Build List
[From Step 3 - prioritized list with status tracking columns]

## NAP Standard
[Exact format to use everywhere]

## Review Strategy
[From Step 4 - goals, templates, process]

## Local Landing Page Specs
[From Step 5 - if applicable]

## Monthly Maintenance Checklist
- [ ] Post 1x/week to GBP
- [ ] Respond to all new reviews within 24 hours
- [ ] Update hours for holidays/special events
- [ ] Add 2-3 new photos monthly
- [ ] Monitor and fix citation inconsistencies
- [ ] Track local pack rankings for target keywords
```

## Output Format

Save to: `outputs/local-seo/[client-name]-[location]-local-plan-[date].md`

## Multi-Location Mode

For businesses with multiple locations:
1. Create master NAP standards document
2. Generate individual location plans
3. Track citation build progress per location
4. Identify shared vs. location-specific content needs

## Context Needs

| Context File | What It Provides | When to Load |
|-------------|-----------------|-------------|
| `references/brand-context.md` → Identity | Business name, location(s), year founded | Always — NAP consistency, GBP profile data |
| `references/brand-context.md` → Products & Services | Offerings, price ranges | During GBP category and service optimization |
| `references/brand-context.md` → Target Audience | Geographic focus, customer type | During service area definition and local content strategy |
| `references/brand-context.md` → Competition | Local competitor names and URLs | During competitive local analysis and citation gap identification |
| `references/brand-context.md` → Voice & Tone | Tone words, vocabulary | During review response template creation |

**Without brand context:** Produces a generic local SEO checklist.
**With brand context:** GBP audit uses real business details, citation strategy targets industry-specific directories, review responses match brand voice, and local landing pages are pre-filled with actual service areas and offerings.
