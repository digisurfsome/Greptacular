# Schema Markup Generator

> **Replaces:** Schema Pro, manual JSON-LD writing, Schema App
> **Saves:** $79/yr in tool costs + 30-60 min per page

## What This Skill Does

Takes a page URL or page content and generates valid JSON-LD structured data markup. Handles all common schema types SEO agencies need. Outputs copy-paste ready code.

## When to Use

- Adding schema to new pages
- Fixing missing or broken schema on existing pages
- Implementing FAQ, HowTo, or Product schema for rich results
- Local business markup
- Article/blog post markup
- Bulk schema generation across page templates

## Instructions

### Step 1: Gather Inputs

Ask for:
1. **Page URL or content** - What page needs schema?
2. **Page type** - What kind of page is it?
3. **Business info** (for Organization/LocalBusiness schema)
4. **Specific rich result target** (optional) - FAQ, HowTo, Product, etc.

### Step 2: Determine Schema Types

Based on page type, apply these schema combinations:

| Page Type | Primary Schema | Additional Schema |
|-----------|---------------|-------------------|
| Homepage | Organization + WebSite | SiteNavigationElement, SearchAction |
| About page | Organization + AboutPage | Person (for team members) |
| Service page | Service + Organization | FAQ, Offer, AggregateRating |
| Blog post | Article + Organization | FAQ, HowTo, BreadcrumbList |
| Product page | Product | Offer, AggregateRating, Review |
| Local landing page | LocalBusiness | GeoCoordinates, OpeningHours, FAQ |
| FAQ page | FAQPage | BreadcrumbList |
| How-to guide | HowTo | Article, FAQ |
| Event page | Event | Offer, Place |
| Contact page | Organization + ContactPage | LocalBusiness |

### Step 3: Generate JSON-LD

For each schema type, produce valid JSON-LD:

**Requirements:**
- Must pass Google Rich Results Test validation
- Must pass Schema.org validator
- Use `@context: "https://schema.org"`
- Nest related schemas properly (don't create separate script tags when nesting works)
- Include all REQUIRED properties per Google's documentation
- Include RECOMMENDED properties where data is available
- Use proper data types (DateTime, URL, Text, Number)

**Template structure:**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "[Type]",
  [properties]
}
</script>
```

### Step 4: Common Schema Templates

**Organization (use on every site):**
- name, url, logo, description
- contactPoint, sameAs (social profiles)
- address (if applicable)

**LocalBusiness:**
- All Organization fields plus:
- geo (latitude/longitude)
- openingHoursSpecification
- priceRange
- areaServed
- hasMap

**Article/BlogPosting:**
- headline, datePublished, dateModified
- author (Person with name, url)
- publisher (Organization)
- image, description
- mainEntityOfPage

**FAQPage:**
- mainEntity array of Question objects
- Each Question has acceptedAnswer with Text

**HowTo:**
- name, description, totalTime
- step array with HowToStep objects
- Each step has name, text, image (optional)

**Service:**
- name, description, provider
- areaServed, serviceType
- offers (if pricing available)

**BreadcrumbList:**
- itemListElement array
- Each with position, name, item (URL)

### Step 5: Validation Checklist

Before delivering:
- [ ] Valid JSON (no syntax errors, proper comma placement)
- [ ] All required properties present per Google docs
- [ ] URLs are absolute (not relative)
- [ ] Dates in ISO 8601 format
- [ ] No deprecated properties used
- [ ] Image URLs point to real images
- [ ] Nested schemas use proper @type
- [ ] BreadcrumbList matches actual site hierarchy
- [ ] FAQ questions match actual page content (not fabricated)

### Step 6: Output

Provide:
1. **The JSON-LD code block** - Copy-paste ready
2. **Implementation instructions** - Where to add it (head section, per page, via plugin)
3. **Platform-specific notes** - WordPress: use Rank Math custom schema or theme header. Shopify: add to theme.liquid. Custom: add before closing `</head>`

## Output Format

Save to: `outputs/schema-markup/[client-name]/[page-slug]-schema.json`

## Batch Mode

For generating schema across a site:
1. Accept a list of page URLs and types
2. Generate appropriate schema for each
3. Output all files to the client folder
4. Create an implementation checklist showing which schema goes where

## Notes

This replaces the need for schema plugins on most platforms. The agency generates the markup, the client's dev pastes it in. Or if the client is on WordPress, provide the custom schema field instructions for their SEO plugin.
