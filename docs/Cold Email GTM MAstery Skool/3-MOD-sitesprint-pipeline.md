# The SiteSprint Pipeline

**Scrape -> Generate -> Deploy -> Outreach -> Close at $1K/Site**

## What You'll Build

A fully automated pipeline that finds service businesses without websites, generates custom Next.js sites using their real Google data, deploys them to Vercel, and runs cold outreach campaigns showing the live site. Target: 10 closes/month at $1K each = $10K/mo at ~99% gross margin.

## Golden Rules

These rules are non-negotiable across the entire SiteSprint system:

1. **NOTHING IS EVER FABRICATED** -- Reviews must be from verifiable platforms (Google, Yelp, BBB, Facebook, Nextdoor, Houzz). Include the reviewer's name exactly as it appears. Never generate or paraphrase reviews. If reviews can't be scraped, replace the testimonials section with a "Verified Social Proof" section showing platform logos + ratings + links.
2. **ALL IMAGES FROM THEIR SITE** -- Scrape every image from the business's existing website. Use Wix image API format for consistent sizing. If no images are available, use CSS-only backgrounds (gradients, patterns) -- NEVER stock photos.
3. **LOGO IS ALWAYS INCORPORATED** -- Place it in the navbar, footer, and hero (if distinctive). If no logo is available, use a styled text logo with a Lucide icon.
4. **NO LINKS TO OLD SITES** -- Never link CTAs to the business's existing website. All CTAs link to `/contact#book`. Include a booking placeholder with a dashed border: "Calendar booking coming soon -- call or message for now."
5. **COLD EMAIL SCRIPTS -- NO SIGNATURES** -- SmartLead handles signatures and subject lines separately. Never include them in your email copy.

---

## Prerequisites

- Node.js 18+
- Claude Code installed and working
- Vercel account (free tier works)
- Google Cloud account with Places API enabled
- SmartLead account (outbound email platform)
- Anthropic API key
- Basic familiarity with Next.js and Tailwind CSS

## Estimated Time

4-6 hours for full pipeline build. 1-2 hours per week to operate.

## Environment Variables

Create a `.env` file in your project root:

```
GOOGLE_PLACES_API_KEY=your_google_places_api_key
VERCEL_TOKEN=your_vercel_api_token
SMARTLEAD_API_KEY=your_smartlead_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

---

## Step 1: Project Setup

Tell Claude:

```
Create a new Node.js project called sitesprint with this structure:

sitesprint/
  src/
    scrape/
      google-places.js      # Google Places API scraper
      lead-filter.js         # Filter and qualify leads
    generate/
      template-selector.js   # Map industry to theme
      content-builder.js     # Build page content from lead data
      site-generator.js      # Assemble Next.js project per lead
    deploy/
      vercel-deploy.js       # Deploy to Vercel subdomain
    outreach/
      smartlead.js           # SmartLead campaign management
      email-templates.js     # 3-step sequence templates
    pipeline.js              # Orchestrator: scrape -> generate -> deploy -> outreach
  templates/
    next-site/               # Base Next.js + Tailwind template
      pages/
        index.js             # Home
        services.js          # Services
        about.js             # About
        contact.js           # Contact/Book
      components/
        Hero.js
        ServicesGrid.js
        TestimonialsCarousel.js
        ContactForm.js
        BookingCTA.js
        Footer.js
        GoogleMapEmbed.js
      styles/
        themes.js            # 15 industry color themes
  data/
    leads.json               # Scraped leads storage
    deployed.json            # Tracking deployed sites
    campaigns.json           # Outreach campaign tracking
  package.json

Initialize with: npm init -y
Install: next react react-dom tailwindcss @vercel/client axios dotenv xlsx node-fetch
```

---

## Step 2: Research and Lead Scraping

The research process is multi-source. Google Places is just the starting point -- you cross-reference every business against multiple platforms to get verified, accurate data.

### Research Process (per business)

1. **WebFetch the business website** -- extract ALL content, images, reviews, services, contact info
2. **Check BBB** -- rating, complaints, years in business, owner name, license info
3. **Check Google Business** -- reviews, photos, hours, service area
4. **Check Facebook, Yelp, Nextdoor, Houzz** -- reviews, photos, ratings
5. **Extract Wix media URLs** (if their site is on Wix): use `curl` + `egrep` to pull Wix image CDN URLs for consistent sizing
6. **Save research** to `~/[business]-research.md` for reference during site build

### Google Places API Scraping

Tell Claude:

```
Build src/scrape/google-places.js that:

1. Takes a search query and location (e.g., "plumber", "Austin TX")
2. Uses Google Places API Text Search to find businesses
3. For each result, fetches Place Details including:
   - business_name
   - phone
   - rating
   - review_count
   - reviews (text + author)
   - address
   - city
   - state
   - website (or lack thereof)
   - place_id
   - photos (reference IDs)
   - business_type / industry
4. Returns structured JSON array

API calls:
- Text Search: POST https://places.googleapis.com/v1/places:searchText
  Headers: X-Goog-Api-Key, X-Goog-FieldMask
  Body: { textQuery: "plumber in Austin TX" }
  FieldMask: places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.reviews,places.photos,places.types,places.googleMapsUri

- Photo fetch: https://places.googleapis.com/v1/{photo_name}/media?maxHeightPx=800&key=API_KEY

Build src/scrape/lead-filter.js that filters results:
- rating >= 4.5
- review_count >= 20
- website is null/empty (NO existing website)
- phone exists
- Returns qualified leads array

Usage: node src/scrape/google-places.js "plumber" "Austin TX"
Output: saves to data/leads.json
```

---

## Step 3: Industry Color Themes (Dark Theme)

All SiteSprint sites use a **dark theme** with an industry-specific accent color. This is the production standard.

### Production Tech Stack

- **Next.js 14** (React 18)
- **Tailwind CSS**
- **Framer Motion** with enhanced animation components: `ParallaxSection`, `AnimatedCounter`, `TextReveal`, `RevealLine`, `ScrollZoom`, `SlideIn`
- **Lucide React** icons
- **Vercel** hosting (public, OIDC auth disabled)
- Dark theme with industry-specific accent color

### Dark Theme Industry Color Map

Tell Claude:

```
Create templates/next-site/styles/themes.js with industry color themes.

All themes are DARK -- dark backgrounds with accent colors:

const themes = {
  concrete:          { accent: 'amber',      bg: 'slate-900' },     // slate/amber
  tree_service:      { accent: 'green-500',  bg: 'slate-900' },     // forest green
  garage_doors:      { accent: 'blue-400',   bg: 'slate-900' },     // steel blue
  plumbing:          { accent: 'blue-500',   bg: 'slate-900' },     // blue
  landscaping:       { accent: 'green-500',  bg: 'slate-900' },     // green
  hvac:              { accent: 'sky-400',    bg: 'slate-900' },     // sky blue
  roofing:           { accent: 'amber-600',  bg: 'slate-900' },     // amber/brown
  electrical:        { accent: 'amber-400',  bg: 'slate-900' },
  cleaning:          { accent: 'cyan-400',   bg: 'slate-900' },
  painting:          { accent: 'violet-400', bg: 'slate-900' },
  pest_control:      { accent: 'red-400',    bg: 'slate-900' },
  moving:            { accent: 'orange-400', bg: 'slate-900' },
  auto_repair:       { accent: 'gray-400',   bg: 'slate-900' },
  dental:            { accent: 'sky-400',    bg: 'slate-900' },
  salon:             { accent: 'pink-400',   bg: 'slate-900' },
  flooring:          { accent: 'amber-700',  bg: 'slate-900' },
  fencing:           { accent: 'emerald-400',bg: 'slate-900' },
  pressure_washing:  { accent: 'blue-400',   bg: 'slate-900' }
};

Export a function getTheme(industry) that fuzzy-matches the business type to the closest theme. Default to plumbing theme if no match.
```

---

## Step 4: Site Generation Engine

Tell Claude:

```
Build src/generate/site-generator.js that takes a single lead object and:

1. Calls template-selector.js to pick the color theme based on industry
2. Calls content-builder.js to generate page content using Claude API:
   - Send lead data (name, services, reviews, location) to Claude
   - Prompt: "Generate website copy for {business_name}, a {industry} company in {city}. Use ONLY the real data provided. Do not fabricate any information. Return JSON with: heroHeadline, heroSubheadline, servicesIntro, aboutText (based on their reviews and rating), ctaText"
   - CRITICAL: Only use real reviews from verifiable platforms (Google, Yelp, BBB, Facebook, Nextdoor, Houzz). Never fabricate. If no reviews can be scraped, use a "Verified Social Proof" section with platform logos + ratings + links instead.
3. Copies the Next.js template to a temp build directory
4. Injects the dark theme colors with industry-specific accent into tailwind.config.js
5. Injects Framer Motion animation components (ParallaxSection, AnimatedCounter, TextReveal, RevealLine, ScrollZoom, SlideIn) into the layout
6. Injects content into each page:

HOME PAGE (index.js):
- Hero with business name, headline, phone CTA
- Services overview grid (3-6 services)
- Social proof bar: "{rating} stars from {review_count} reviews"
- Testimonials carousel (3-5 real Google reviews with author names)
- Bottom CTA: "Call Now" or "Book Online"

SERVICES PAGE (services.js):
- Full services list with descriptions
- Each service card with icon placeholder
- Trust signals: years in business, review count, rating
- CTA between sections

ABOUT PAGE (about.js):
- Business story (generated from review themes and location)
- Service area with Google Maps embed
- Google Maps iframe: https://www.google.com/maps/embed/v1/place?key={API_KEY}&q={place_id}
- Team/values section

CONTACT PAGE (contact.js):
- Contact form (name, email, phone, message)
- Phone number with click-to-call link
- Business address
- Hours placeholder
- Booking placeholder at /contact#book with dashed border: "Calendar booking coming soon -- call or message for now"
- NO links to their old/existing website

6. Runs next build to create production build
7. Returns the build output path

All images: scrape from their existing website. Use Wix image API format if applicable. If no images available, use CSS-only backgrounds (gradients, patterns). NEVER use stock photos. No fabricated content.

Logo: always incorporate in navbar, footer, and hero if distinctive. If no logo found, use styled text logo with Lucide icon.
```

---

## Step 5: Vercel Deployment

Tell Claude:

```
Build src/deploy/vercel-deploy.js that:

1. Takes a build output directory and lead data
2. Generates subdomain: {sanitized-business-name}-{city}.vercel.app
   - Sanitize: lowercase, replace spaces with hyphens, remove special chars
   - Example: "Joe's Plumbing" in Austin -> joes-plumbing-austin.vercel.app
3. Deploys using the Vercel CLI:

   npx vercel --prod --yes --name [business-slug] --scope alex-kamels-projects --token $VERCEL_TOKEN

4. CRITICAL: Disable OIDC auth after deploy so the site is publicly accessible (no Vercel login required):

   curl -X PATCH "https://api.vercel.com/v1/projects/[project-id]" \
     -H "Authorization: Bearer $VERCEL_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"oidcTokenConfig":{"enabled":false}}'

5. Redeploy after auth is disabled to apply the change
6. Verify the URL is publicly accessible (no Vercel login wall)
7. Returns the live URL
8. Saves to data/deployed.json: { lead_id, business_name, url, deployed_at }

Also build a batch deployer that loops through all generated sites and deploys them sequentially with a 5-second delay between each to avoid rate limits.
```

---

## Step 6: Email Outreach via SmartLead

Tell Claude:

```
Build src/outreach/email-templates.js with a 3-step sequence.

IMPORTANT: Do NOT include signatures or subject lines in the email body -- SmartLead handles those separately.

EMAIL 1 (Day 0) — The Hook:
Body:
Hey {{first_name}},

Saw {{company_name}} has {{review_count}} reviews at {{rating}} stars — your customers clearly love what you do.

I noticed you don't have a website yet, so I went ahead and built one for you:

{{site_url}}

It's got your real reviews, services, and contact info. Takes calls right from the page.

If you like it, I can point it to a custom domain and make it officially yours for $1,000 flat — no monthly fees, no contracts.

If not, no worries at all. Just wanted to show you what's possible.

EMAIL 2 (Day 3) — Social Proof:
Body:
Hey {{first_name}},

Quick follow up — did you get a chance to check out the site?

{{site_url}}

I've done this for a handful of other {{industry}} companies in {{city}} and the ones who grabbed their sites are already getting calls from it.

Happy to hop on a quick call if you have any questions.

EMAIL 3 (Day 7) — Last Chance:
Body:
Hey {{first_name}},

I'm going to pull down the demo site I built for {{company_name}} at the end of this week since I haven't heard back.

{{site_url}}

If you want to keep it, just reply "interested" and I'll walk you through next steps. $1,000 flat, you own it forever.

Either way — no hard feelings. Your reviews speak for themselves, just thought you deserved a site that matches.

Build src/outreach/smartlead.js that:
1. Creates a SmartLead campaign via API
   POST https://server.smartlead.ai/api/v1/campaigns/create?api_key={SMARTLEAD_API_KEY}
   Body: { name: "SiteSprint - {city} - {industry} - {date}" }
2. Adds the email sequence (3 steps with delays)
   POST https://server.smartlead.ai/api/v1/campaigns/{id}/sequences?api_key={SMARTLEAD_API_KEY}
3. Uploads leads with custom variables
   POST https://server.smartlead.ai/api/v1/campaigns/{id}/leads?api_key={SMARTLEAD_API_KEY}
   Each lead needs: email, first_name, company_name, review_count, rating, industry, city, site_url
4. Starts the campaign
   POST https://server.smartlead.ai/api/v1/campaigns/{id}/schedule?api_key={SMARTLEAD_API_KEY}
```

---

## Step 7: Pipeline Orchestrator

Tell Claude:

```
Build src/pipeline.js that chains everything together:

Usage: node src/pipeline.js --industry "plumber" --city "Austin TX" --limit 20

Flow:
1. Scrape: Find businesses matching industry + city
2. Filter: Keep only qualified leads (4.5+ stars, 20+ reviews, no website, has phone)
3. Log: "Found {n} qualified leads"
4. For each qualified lead:
   a. Generate site (select theme, build content, assemble Next.js project)
   b. Deploy to Vercel
   c. Log: "Deployed {business_name} -> {url}"
5. After all deployments:
   a. Create SmartLead campaign
   b. Upload all leads with their site URLs as custom variables
   c. Start campaign
6. Output summary:
   - Total leads found
   - Total qualified
   - Total sites deployed
   - Campaign ID and status
   - List of all deployed URLs

Add error handling:
- If a site fails to generate, skip it and continue
- If deployment fails, retry once, then skip
- Log all errors to data/errors.log
- Save progress to data/pipeline-runs/{timestamp}.json so you can resume
```

---

## Step 8: Unit Economics Tracker

Tell Claude:

```
Build a simple tracking module at src/tracking.js:

Per-site costs:
- Google Places API: ~$0.02 per lead (text search + details + photos)
- Claude API: ~$0.05 per site (content generation)
- Vercel: $0 (free tier, 100 deployments/day)
- SmartLead: ~$0.01 per email sent
- Total cost per site: ~$0.08

Revenue model:
- Price per site: $1,000
- Gross margin: ~99.99%
- Target: 10 closes/month = $10,000/mo
- At 5% close rate, need 200 sites deployed/month
- At 200 sites * $0.08 = $16/month in costs

Track in data/economics.json:
{
  total_leads_scraped: 0,
  total_qualified: 0,
  total_sites_deployed: 0,
  total_emails_sent: 0,
  total_replies: 0,
  total_closes: 0,
  total_revenue: 0,
  total_cost: 0,
  avg_cost_per_site: 0,
  close_rate: 0
}

Update after each pipeline run. Print summary to console.
```

---

## Testing Steps

1. **Test scraping**: `node src/scrape/google-places.js "plumber" "Austin TX"` -- verify you get 20+ results with ratings, reviews, and phone numbers
2. **Test filtering**: check that only leads without websites, with 4.5+ stars and 20+ reviews pass through
3. **Test theme selection**: pass different industries and verify correct color themes are returned
4. **Test site generation** (single lead): pick one lead, generate the site, open it locally with `npx next dev` and verify:
   - All 4 pages render
   - Reviews are REAL (match Google)
   - Phone number is clickable
   - Google Maps embed loads
   - Colors match the industry theme
   - Mobile responsive
5. **Test deployment**: deploy one site to Vercel, visit the URL, verify it loads
6. **Test email templates**: render templates with sample data, verify all variables are replaced
7. **Test full pipeline**: run with `--limit 3` to scrape, generate, deploy, and create campaign for 3 leads

## You're Done When...

- You can run `node src/pipeline.js --industry "plumber" --city "Austin TX" --limit 5` and it scrapes leads, generates 5 custom sites, deploys them to Vercel, and creates a SmartLead campaign with the 3-email sequence
- Each deployed site has 4 pages with real business data, real reviews, correct industry colors, and working phone links
- The SmartLead campaign is created with all leads loaded and the sequence ready to send
- No fabricated content anywhere -- every review, rating, phone number, and address comes from Google Places
- data/deployed.json tracks all live site URLs
- data/economics.json shows per-run cost breakdown
