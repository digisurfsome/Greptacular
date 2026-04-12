# Auto Site Generator

**Lead Data -> Deployed Next.js Website**

## What You'll Build

A site generation engine that reads lead data from an XLSX or JSON file and produces fully deployed, mobile-responsive Next.js websites on Vercel. Each site is themed to the business's industry, populated with real data (reviews, services, location), and deployed to a unique subdomain. You feed it a spreadsheet, it gives you live websites.

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
- Vercel account with API token
- Google Cloud account with Places API and Maps Embed API enabled
- Anthropic API key
- A lead data file (XLSX or JSON) with business information

## Estimated Time

3-4 hours for the generator. Under 2 minutes per site once built.

## Production Tech Stack

- **Next.js 14** (React 18)
- **Tailwind CSS**
- **Framer Motion** with enhanced animation components: `ParallaxSection`, `AnimatedCounter`, `TextReveal`, `RevealLine`, `ScrollZoom`, `SlideIn`
- **Lucide React** icons
- **Vercel** hosting (public, OIDC auth disabled)
- Dark theme with industry-specific accent color

## Environment Variables

Create a `.env` file in your project root:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_PLACES_API_KEY=your_google_places_api_key
VERCEL_TOKEN=your_vercel_api_token
```

---

## Step 1: Project Setup

Tell Claude:

```
Create a Node.js project called auto-site-generator with this structure:

auto-site-generator/
  src/
    ingest/
      parse-xlsx.js          # Read XLSX lead files
      parse-json.js          # Read JSON lead files
      validate-lead.js       # Validate required fields exist
    generate/
      template-engine.js     # Core: lead data -> Next.js project
      content-writer.js      # Claude API: generate copy from lead data
      theme-mapper.js        # Industry -> color scheme mapping
    components/
      Hero.jsx
      ServicesGrid.jsx
      TestimonialsCarousel.jsx
      ContactForm.jsx
      BookingCTA.jsx
      Footer.jsx
      GoogleMapEmbed.jsx
      TrustBar.jsx
      ServiceAreaMap.jsx
    pages/
      HomePage.jsx
      ServicesPage.jsx
      AboutPage.jsx
      ContactPage.jsx
    deploy/
      vercel.js              # Vercel API deployment
    batch.js                 # Process entire XLSX/JSON file
    generate-single.js       # Process one lead
  templates/
    base-next/               # Starter Next.js + Tailwind project
      package.json
      tailwind.config.js
      next.config.js
      postcss.config.js
  data/
    sample-leads.xlsx        # Example input file
    sample-leads.json        # Example input file
    output/                  # Generated site builds
    deployments.json         # Deployment tracking
  package.json

Install: next react react-dom tailwindcss postcss autoprefixer @anthropic-ai/sdk xlsx dotenv node-fetch framer-motion lucide-react
```

### Production File Structure Per Site

Each generated site follows this exact structure:

```
04-sites-built/[business-slug]/
├── site-config.json          # All business data
├── next.config.js            # Image remote patterns
├── public/                   # Local images if needed
├── src/
│   ├── app/
│   │   ├── page.tsx          # Homepage
│   │   ├── services/page.tsx
│   │   ├── about/page.tsx
│   │   ├── contact/page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── Motion.tsx        # All animation components
│   │   └── StarRating.tsx
│   └── lib/
│       ├── config.ts         # Types + theme
│       └── icons.ts          # Service icon mapping
```

---

## Step 2: Research Process and Lead Data

### Multi-Source Research (per business)

Before building any site, research the business across multiple platforms:

1. **WebFetch the business website** -- extract ALL content, images, reviews, services, contact info
2. **Check BBB** -- rating, complaints, years in business, owner name, license info
3. **Check Google Business** -- reviews, photos, hours, service area
4. **Check Facebook, Yelp, Nextdoor, Houzz** -- reviews, photos, ratings
5. **Extract Wix media URLs** (if their site is on Wix): use `curl` + `egrep` to pull Wix image CDN URLs for consistent sizing
6. **Save research** to `~/[business]-research.md` for reference during site build

### Lead Data Format and Ingestion

Tell Claude:

```
Build src/ingest/parse-xlsx.js and parse-json.js.

Expected lead data format (each row/object):
{
  company_name: "Joe's Plumbing",        // required
  phone: "(512) 555-0123",               // required
  rating: 4.8,                           // required
  review_count: 47,                      // required
  reviews: [                             // required, array of real Google reviews
    { author: "Sarah M.", text: "Best plumber in Austin...", rating: 5 },
    { author: "Mike T.", text: "Fixed our leak same day...", rating: 5 }
  ],
  services: ["Drain Cleaning", "Water Heater Repair", "Pipe Installation", "Emergency Plumbing"],
  city: "Austin",                        // required
  state: "TX",                           // required
  address: "123 Main St, Austin, TX",    // required
  industry: "plumbing",                  // required
  place_id: "ChIJ...",                   // optional, for Google Maps embed
  photos: ["photo_ref_1", "photo_ref_2"] // optional, Google Places photo refs
}

parse-xlsx.js:
- Read XLSX file using xlsx library
- Map columns to the schema above
- Handle reviews column: expect JSON string in cell, parse it
- Return array of lead objects

parse-json.js:
- Read JSON file
- Validate against schema
- Return array of lead objects

validate-lead.js:
- Check all required fields exist and are non-empty
- Check rating is a number between 1 and 5
- Check reviews is an array with at least 1 entry
- Check phone is present
- Return { valid: true/false, errors: [] }

Log validation errors per lead but don't halt the batch -- skip invalid leads.
```

---

## Step 3: Industry Theme Mapping (Dark Theme)

All SiteSprint sites use a **dark theme** with an industry-specific accent color. This is the production standard.

Tell Claude:

```
Build src/generate/theme-mapper.js with industry color schemes.

All themes are DARK -- dark backgrounds with industry-specific accent colors:

const INDUSTRY_THEMES = {
  concrete:           { accent: 'amber',      bg: 'slate-900', dark: '#0f172a' },
  tree_service:       { accent: 'green-500',  bg: 'slate-900', dark: '#0f172a' },
  garage_doors:       { accent: 'blue-400',   bg: 'slate-900', dark: '#0f172a' },
  plumbing:           { accent: 'blue-500',   bg: 'slate-900', dark: '#0f172a' },
  landscaping:        { accent: 'green-500',  bg: 'slate-900', dark: '#0f172a' },
  hvac:               { accent: 'sky-400',    bg: 'slate-900', dark: '#0f172a' },
  roofing:            { accent: 'amber-600',  bg: 'slate-900', dark: '#0f172a' },
  electrical:         { accent: 'amber-400',  bg: 'slate-900', dark: '#0f172a' },
  cleaning:           { accent: 'cyan-400',   bg: 'slate-900', dark: '#0f172a' },
  painting:           { accent: 'violet-400', bg: 'slate-900', dark: '#0f172a' },
  pest_control:       { accent: 'red-400',    bg: 'slate-900', dark: '#0f172a' },
  moving:             { accent: 'orange-400', bg: 'slate-900', dark: '#0f172a' },
  auto_repair:        { accent: 'gray-400',   bg: 'slate-900', dark: '#0f172a' },
  dental:             { accent: 'sky-400',    bg: 'slate-900', dark: '#0f172a' },
  salon:              { accent: 'pink-400',   bg: 'slate-900', dark: '#0f172a' },
  flooring:           { accent: 'amber-700',  bg: 'slate-900', dark: '#0f172a' },
  fencing:            { accent: 'emerald-400',bg: 'slate-900', dark: '#0f172a' },
  pressure_washing:   { accent: 'blue-400',   bg: 'slate-900', dark: '#0f172a' }
};

Export:
- getTheme(industry) — exact match first, then fuzzy match (e.g., "Plumbing Services" -> plumbing), default to plumbing if no match
- getAllThemes() — return the full map
- getTailwindConfig(theme) — return a tailwind.config.js extend block with the theme colors mapped to: primary, secondary, accent
```

---

## Step 4: Component Library

Tell Claude:

```
Build 8 React components in src/components/. Each accepts a theme object and content props. All use Tailwind CSS.

Hero.jsx:
- Full-width section with gradient background using theme colors
- Business name as h1
- Headline text
- Subheadline
- Two CTA buttons: "Call Now" (tel: link) and "Get a Free Quote" (scrolls to contact)
- Rating badge: "{rating} stars - {review_count} reviews on Google"

ServicesGrid.jsx:
- Section with heading "Our Services"
- Responsive grid: 1 col mobile, 2 cols tablet, 3 cols desktop
- Each service card: service name, short description, themed icon placeholder
- Bottom CTA linking to contact page

TestimonialsCarousel.jsx:
- Section with heading "What Our Customers Say"
- Carousel/slider showing one review at a time with navigation dots
- Each slide: review text in quotes, author name exactly as it appears on the platform, star rating display
- Auto-advances every 5 seconds
- ONLY real reviews from verifiable platforms (Google, Yelp, BBB, Facebook, Nextdoor, Houzz). Never fabricate or paraphrase.
- If no reviews can be scraped, replace this entire component with a "Verified Social Proof" section showing platform logos + ratings + links
- Add a badge showing which platform the review is from (e.g., "Review from Google")

ContactForm.jsx:
- Form fields: name, email, phone, message
- Submit button with theme primary color
- Form posts to a placeholder endpoint (can be swapped for Formspree, Netlify Forms, etc.)
- Client-side validation

BookingCTA.jsx:
- Banner section with dark theme and accent color highlight
- Headline: "Ready to Get Started?"
- Phone number as large clickable link
- Secondary "Send Us a Message" button
- All CTAs link to /contact#book -- NEVER link to their existing website
- Booking placeholder with dashed border: "Calendar booking coming soon -- call or message for now"

Footer.jsx:
- Business logo (scraped from their site, or styled text logo with Lucide icon if none)
- Business name, address, phone
- Quick links: Home, Services, About, Contact
- "Powered by SiteSprint" attribution (small, gray text)
- Copyright year

GoogleMapEmbed.jsx:
- Google Maps iframe embed
- If place_id provided: use Places embed URL
- If address only: use address-based embed URL
- Responsive: full width, 300px height on mobile, 400px on desktop

TrustBar.jsx:
- Horizontal bar showing: star rating, review count, years in business (if available), service area
- Subtle background, themed accent border
```

---

## Step 5: Page Templates

Tell Claude:

```
Build 4 page templates in src/pages/ that compose the components:

HomePage.jsx:
1. Hero (business name, headline, phone CTA)
2. TrustBar (rating, reviews, service area)
3. ServicesGrid (top 6 services, overview mode)
4. TestimonialsCarousel (3-5 real reviews)
5. BookingCTA
6. Footer

ServicesPage.jsx:
1. Page header with title "Our Services" and subtitle
2. Full ServicesGrid (all services, detailed mode with descriptions)
3. TrustBar
4. Section: "Why Choose {business_name}?" with 3 trust points derived from reviews
5. BookingCTA
6. Footer

AboutPage.jsx:
1. Page header "About {business_name}"
2. Business story section (2-3 paragraphs, generated from review themes and location data)
3. Service area section with GoogleMapEmbed
4. Values/commitment section (3 values derived from review sentiment)
5. TrustBar
6. Footer

ContactPage.jsx:
1. Page header "Get in Touch"
2. Two-column layout:
   - Left: ContactForm
   - Right: Business info (address, phone, hours placeholder), GoogleMapEmbed
3. Booking placeholder at /contact#book with dashed border: "Calendar booking coming soon -- call or message for now"
4. NO links to their existing website anywhere on this page
5. Footer

All pages use Framer Motion animation components: ParallaxSection for hero sections, AnimatedCounter for stats, TextReveal for headlines, RevealLine for text blocks, ScrollZoom for images, SlideIn for cards and sections.

Images: scrape from their existing website. Use Wix image API format if applicable. If no images available, use CSS-only backgrounds (gradients, patterns). NEVER use stock photos. Logo goes in Navbar and Footer.

Each page includes <Head> with:
- Title: "{business_name} - {page_name} | {city}, {state}"
- Meta description generated from business data
- Open Graph tags
```

---

## Step 6: Content Generation with Claude

Tell Claude:

```
Build src/generate/content-writer.js that uses the Anthropic SDK to generate website copy.

Function: generateSiteContent(lead)

Send this prompt to Claude (claude-sonnet-4-20250514):

"You are a website copywriter. Generate website copy for a local service business using ONLY the real data provided below. Do not fabricate any information.

Business: {lead.company_name}
Industry: {lead.industry}
City: {lead.city}, {lead.state}
Rating: {lead.rating} stars from {lead.review_count} reviews
Services: {lead.services.join(', ')}
Sample Reviews: {JSON.stringify(lead.reviews.slice(0, 5))}

Return a JSON object with:
{
  heroHeadline: '...',           // 8-12 words, speaks to the customer's need
  heroSubheadline: '...',        // 15-25 words, reinforces trust
  servicesIntro: '...',          // 2 sentences introducing their service offerings
  serviceDescriptions: {         // one 1-2 sentence description per service
    'Service Name': 'Description...'
  },
  aboutText: '...',              // 3 paragraphs about the business, based on review themes
  aboutValues: ['...', '...', '...'],  // 3 core values derived from reviews
  whyChoose: ['...', '...', '...'],    // 3 reasons to choose them, from review evidence
  ctaText: '...',                // CTA headline, 5-8 words
  metaDescription: '...'        // 155 chars, SEO meta description
}

Rules:
- Reference their real city and service area
- Pull themes from their actual reviews (e.g., if reviews mention 'fast response', use that)
- Never invent services they don't offer
- Never fabricate review quotes
- Keep tone professional but warm
- Every claim must be supported by the provided data"

Parse the JSON response. If parsing fails, retry once.
Return the content object merged with the lead data.
```

---

## Step 7: Template Engine (Core Generator)

Tell Claude:

```
Build src/generate/template-engine.js -- the core that assembles a complete Next.js project from lead data + generated content.

Function: generateSite(lead)

Steps:
1. Validate lead data using validate-lead.js
2. Get theme from theme-mapper.js
3. Generate content using content-writer.js
4. Copy templates/base-next/ to data/output/{slug}/
   - slug = sanitize(company_name + '-' + city): lowercase, hyphens, no special chars
5. Write tailwind.config.js with theme colors injected
6. Write each page file, injecting:
   - Theme object
   - Content object
   - Lead data (phone, address, reviews, services)
7. Write a site-config.json in the project root with all the data (for debugging)
8. Run: cd data/output/{slug} && npm install && npx next build
9. Return { slug, buildPath, lead, content, theme }

Error handling:
- If content generation fails, use fallback templates (generic but safe copy)
- If build fails, log the error and return { error: ... } instead of throwing
- Never let one failed site stop the batch
```

---

## Step 8: Vercel Deployment

Tell Claude:

```
Build src/deploy/vercel.js:

Function: deploySite(buildResult)

1. Read all files from the build output directory
2. Convert to Vercel's file format:
   - Each file: { file: relative_path, data: base64_content }
   - Or use the Vercel CLI: npx vercel --prod --yes --token $VERCEL_TOKEN
3. Deploy with subdomain: {slug}.vercel.app
   - Production command: npx vercel --prod --yes --name [business-slug] --scope alex-kamels-projects --token $VERCEL_TOKEN
4. CRITICAL: Disable OIDC auth after deploy so the site is publicly accessible (no Vercel login required):
   curl -X PATCH "https://api.vercel.com/v1/projects/[project-id]" \
     -H "Authorization: Bearer $VERCEL_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"oidcTokenConfig":{"enabled":false}}'
5. Redeploy after auth is disabled to apply the change
6. Verify the URL is publicly accessible (no Vercel login wall)
7. Return the live URL
8. Append to data/deployments.json:
   {
     slug: "joes-plumbing-austin",
     url: "https://joes-plumbing-austin.vercel.app",
     company_name: "Joe's Plumbing",
     city: "Austin",
     industry: "plumbing",
     deployed_at: "2024-01-15T10:30:00Z",
     status: "live"
   }

Use the Vercel CLI approach -- it handles file uploads and build more reliably than the API for Next.js projects. Always disable OIDC auth after deploy and redeploy to ensure public access.
```

---

## Step 9: Batch Processing

Tell Claude:

```
Build src/batch.js -- the main entry point for processing a file of leads.

Usage:
  node src/batch.js --file data/leads.xlsx
  node src/batch.js --file data/leads.json
  node src/batch.js --file data/leads.json --limit 5
  node src/batch.js --file data/leads.json --start 10 --limit 5  (resume from row 10)

Flow:
1. Detect file type from extension (.xlsx or .json)
2. Parse file using appropriate parser
3. Validate all leads, log and skip invalid ones
4. For each valid lead (respecting --limit and --start):
   a. Log: "[{index}/{total}] Generating site for {company_name}..."
   b. Generate site
   c. Deploy to Vercel
   d. Log: "[{index}/{total}] DEPLOYED: {url}"
   e. Save progress to data/batch-progress.json after each lead
5. On completion, print summary:
   - Total leads in file: X
   - Valid leads: X
   - Sites generated: X
   - Sites deployed: X
   - Failed: X
   - List of all live URLs

Also build src/generate-single.js for testing one lead:
  node src/generate-single.js --name "Joe's Plumbing" --city "Austin" --industry plumbing --phone "512-555-0123"
  (Generates and deploys a single site, useful for testing)
```

---

## Step 10: Quality Checklist Validator

Tell Claude:

```
Build src/quality-check.js that validates a deployed site:

Usage: node src/quality-check.js https://joes-plumbing-austin.vercel.app

Checks:
1. Site loads (HTTP 200 on all 4 pages: /, /services, /about, /contact)
2. Mobile responsive: check viewport meta tag exists
3. Phone link works: find tel: link in HTML, verify it matches lead data
4. Address is correct: find address text in HTML
5. Reviews are real: compare review text on site against reviews in lead data
6. No placeholder text: scan for "Lorem ipsum", "TODO", "placeholder", "[insert", "{{"
7. Images: check for broken image tags (no src="" or src="undefined")
8. Google Maps embed loads: check iframe src is valid
9. All internal links work: /, /services, /about, /contact return 200
10. Page titles are set (not "Next.js App" or empty)

Output: pass/fail for each check, overall score out of 10.
If score < 8, flag the site for manual review.
```

---

## Testing Steps

1. **Test data ingestion**: create a sample XLSX with 3 leads, run the parser, verify all fields are correctly extracted
2. **Test theme mapping**: call `getTheme('plumbing')`, `getTheme('HVAC Services')`, `getTheme('unknown')` -- verify correct themes and fallback
3. **Test content generation**: pass one lead to content-writer.js, verify the returned JSON has all fields, and no fabricated content
4. **Test single site generation**: run `generate-single.js` with test data, open the site locally with `npx next dev`, check all 4 pages
5. **Test deployment**: deploy the test site to Vercel, verify the URL loads
6. **Test batch processing**: run `batch.js` with 3 leads from an XLSX file, verify all 3 deploy successfully
7. **Test quality checker**: run against a deployed site, verify all 10 checks pass
8. **Test mobile**: open a deployed site on a phone or in Chrome DevTools mobile view

## You're Done When...

- `node src/batch.js --file data/leads.xlsx` reads a spreadsheet of leads and deploys a unique, themed Next.js site for each one
- Each site has 4 pages (Home, Services, About, Contact) with real business data and correct industry colors
- Every testimonial on every site is a real Google review, not fabricated
- Phone numbers are clickable tel: links
- Google Maps embeds show the correct business location
- Sites are mobile responsive
- The quality checker passes all 10 checks for each deployed site
- data/deployments.json tracks every live URL with metadata
- You can resume a batch from where it left off using --start
