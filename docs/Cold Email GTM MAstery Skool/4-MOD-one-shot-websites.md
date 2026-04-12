# One-Shot $5K Websites — The Prompt Formula for Premium Sites

## What You'll Build

A repeatable system for generating premium, client-ready websites using Claude Code and a single well-structured prompt. You'll learn the exact prompt formula, get 5 ready-to-use templates for high-value niches, and understand how to sell these sites for $3-10K while spending 1-3 hours of actual build time.

## Prerequisites

- Claude Pro or Claude Code access
- Node.js 18+ installed
- Vercel account (free tier)
- Basic understanding of HTML/CSS (you don't need to be a developer)
- A text editor for writing prompts

## Estimated Time

- **Learn the formula:** 30 minutes
- **First site build:** 1-2 hours
- **Refinement and polish:** 1-2 hours
- **Full client-ready site:** 2-4 hours total

## The 5-Part Prompt Formula

Every premium website prompt has 5 parts. Skip any one of them and the output drops from "$10K looking" to "template-looking." This is the difference between a site someone will pay $5K for and one they'd find on a free website builder.

### Part 1: Business Context

Tell Claude exactly who this business is. Generic prompts produce generic sites.

```
Business: [Full business name]
Industry: [Specific niche, not just "restaurant" but "upscale farm-to-table restaurant"]
Target audience: [Who visits this site — age, income, what they're looking for]
Brand personality: [3-5 adjectives — elegant, bold, minimal, playful, authoritative]
Positioning: [How they're different from competitors — "the only X that Y"]
Location: [City/region if local business]
```

### Part 2: Design Direction

Be prescriptive about visuals. Vague design requests produce vague designs.

```
Primary color: [Exact hex code]
Secondary color: [Exact hex code]
Accent color: [Exact hex code, used sparingly]
Background: [Dark #0A0A0A / Light #FAFAFA / Warm #1A1510 / etc.]
Theme: [Dark mode / Light mode / Warm / Cool]
Style reference: [Name actual brands — "Apple-level whitespace", "Stripe-style gradients"]
Fonts: [Specific Google Fonts or system fonts — "Inter for body, Playfair Display for headings"]
Visual effects: [Glassmorphism, grain texture, gradient meshes, parallax, scroll animations]
```

### Part 3: Page Structure

Map out every section. This is your wireframe.

```
1. Hero: [What it says, CTA button text, background treatment]
2. [Section name]: [What content goes here, number of items/cards]
3. [Section name]: [Layout preference — grid, carousel, alternating]
4. [Section name]: [Any interactive elements — tabs, accordions, hover effects]
5. Footer: [What links, contact info, social icons, newsletter signup]
```

### Part 4: Technical Requirements

Set constraints so the output is deployable.

```
Format: [Single HTML file with inline CSS/JS | Next.js app | Astro site]
Responsive: Must look perfect on mobile, tablet, and desktop
Animations: [Scroll-triggered fade-ins, hover effects, smooth transitions]
Fonts: Load from Google Fonts CDN
Images: Use placeholder images from unsplash or placehold.co with descriptive alt text
Performance: Lazy load images, minimal JS, fast first paint
```

### Part 5: Quality Bar

This is the most important part. Without it, Claude defaults to "good enough."

```
Quality standard: This should look like a $15,000 custom-designed website.
Do NOT make it look like a template. No generic stock photo layouts.
Use generous whitespace — 80-120px between major sections.
Typography should have clear hierarchy — headings command attention,
body text is comfortable to read. Every element should feel intentional.
No visual clutter. If a section doesn't earn its space, cut it.
```

## 5 Ready-to-Customize Prompt Templates

### Template 1: Premium Restaurant

```
Build a single-page website for an upscale restaurant.

BUSINESS CONTEXT:
- Name: [Restaurant Name]
- Type: Upscale farm-to-table restaurant
- Location: [City]
- Audience: Couples (date night), foodies, professionals aged 28-55
- Brand personality: Warm, intimate, sophisticated, artisanal
- Positioning: Locally sourced seasonal ingredients, chef-driven menu

DESIGN DIRECTION:
- Background: Dark #1A1412
- Primary color: Warm gold #D4A574
- Secondary color: Cream #F5E6D3
- Text: Light cream #FAF3EB on dark background
- Style: Warm and moody like a candlelit dinner. Think Noma or Eleven Madison Park websites.
- Fonts: Playfair Display for headings, Lora for body text
- Visual effects: Subtle parallax on hero image, fade-in on scroll, warm grain texture overlay

PAGE STRUCTURE:
1. Hero: Full-viewport background image (dimmed), restaurant name in elegant serif, tagline
   "Seasonal ingredients. Timeless flavors.", CTA "Reserve a Table"
2. About: Split layout — text left, image right. Chef's philosophy, 2-3 short paragraphs.
   Warm, personal tone.
3. Menu: 3-column grid for Starters / Mains / Desserts. 4-5 items each with name, short
   description, price. Elegant typography, no boxes or cards — just clean text layout.
4. Reservations: Simple centered section. "Join Us" heading, phone number, OpenTable embed
   placeholder, hours of operation (Tue-Sun, 5pm-10pm).
5. Testimonials: 3 quotes in a horizontal layout, italic serif font, reviewer name below.
   Subtle gold divider between each.
6. Location: Full-width map placeholder, address, parking info, cross streets.
7. Footer: Minimal — logo, address, phone, Instagram/Facebook icons, "© 2025"

TECHNICAL:
- Single HTML file with inline CSS and vanilla JS
- Fully responsive — mobile menu, stacked sections on small screens
- Smooth scroll between sections
- Google Fonts: Playfair Display + Lora
- Placeholder images from unsplash with food/restaurant themes

QUALITY BAR:
This should look like a $15,000 website designed by a boutique agency. No template feel.
Generous whitespace — 100px+ between sections. The dark background should feel luxurious,
not gloomy. Gold accents should be used sparingly — headings and dividers only, never
overwhelming. Every section should breathe. Typography hierarchy: 52px headings, 18px body,
1.7 line height for readability.
```

### Template 2: SaaS Landing Page

```
Build a single-page SaaS landing page.

BUSINESS CONTEXT:
- Name: [Product Name]
- Product: [What it does in one sentence]
- Target audience: [Startup founders / Marketing teams / Developers / etc.]
- Brand personality: Modern, trustworthy, technical but approachable
- Positioning: [How it's different — faster, simpler, cheaper, AI-powered, etc.]

DESIGN DIRECTION:
- Background: Dark navy #0A0F1C
- Primary accent: Electric blue #3B82F6
- Secondary accent: Purple #8B5CF6
- Text: White #FFFFFF for headings, #94A3B8 for body
- Style: Glassmorphism cards with subtle borders, gradient mesh backgrounds.
  Reference: Linear.app, Vercel.com, Raycast.com
- Fonts: Inter for everything, weight variation for hierarchy
- Visual effects: Glassmorphism panels, subtle gradient orbs in background,
  hover glow on cards, smooth scroll-triggered animations

PAGE STRUCTURE:
1. Navigation: Sticky top bar — logo left, nav links center (Features, Pricing, FAQ),
   "Get Started" button right with blue gradient background
2. Hero: Large heading (48-56px) with gradient text (blue to purple), subheading in gray,
   two CTAs ("Start Free" primary blue, "See Demo" outline), hero image/screenshot below
   with glassmorphism frame and subtle shadow
3. Social proof bar: "Trusted by 500+ teams" with 5-6 grayscale company logo placeholders
4. Features: 3-column grid of 6 features. Each: icon (use emoji or simple SVG), heading,
   2-line description. Glassmorphism card with subtle border on hover.
5. How it works: 3 steps, horizontal layout with numbered circles and connecting line.
   Step title + description for each.
6. Pricing: 3 tiers in cards — Free / Pro $29 / Team $79. Feature list with checkmarks.
   Pro card highlighted with blue border and "Most Popular" badge. Annual/monthly toggle.
7. Testimonials: 3 cards with avatar placeholder, name, title, company, quote.
   Glassmorphism style.
8. FAQ: 6 questions in accordion style. Click to expand with smooth animation.
9. Final CTA: Gradient background section, bold heading "Ready to get started?",
   email input + button, "No credit card required" subtext.
10. Footer: 4-column layout — Product links, Company links, Resources, Legal.
    Social icons. Copyright.

TECHNICAL:
- Single HTML file with inline CSS and vanilla JS
- Fully responsive with mobile hamburger menu
- Accordion JS for FAQ section
- Pricing toggle JS (monthly/annual with 20% discount)
- Scroll-triggered fade-in animations using IntersectionObserver
- Google Fonts: Inter (400, 500, 600, 700)

QUALITY BAR:
This must look like a VC-backed startup's landing page, not a template. Reference the
polish level of Linear, Vercel, or Notion's marketing sites. Glassmorphism should be
subtle — rgba(255,255,255,0.05) backgrounds with 1px rgba borders, not heavy frosted glass.
Background gradient orbs should be soft and atmospheric, not distracting. 100px+ spacing
between sections. Cards should have micro-interactions on hover (slight lift, border glow).
The pricing section should make the Pro tier obviously the best choice through visual weight.
```

### Template 3: Local Service Business

```
Build a single-page website for a local service business.

BUSINESS CONTEXT:
- Name: [Business Name]
- Service: [Plumbing / HVAC / Landscaping / Roofing / Cleaning / etc.]
- Location: [City, State — serves surrounding area]
- Audience: Homeowners aged 30-65, need reliable service, want to hire fast
- Brand personality: Trustworthy, professional, local, responsive
- Positioning: [Family-owned since X / 24/7 emergency service / Licensed & insured / etc.]

DESIGN DIRECTION:
- Background: Clean white #FFFFFF
- Primary color: Navy #1E3A5F
- Accent color: Orange #F97316 (for CTAs and highlights)
- Text: Dark #1A1A1A for body, Navy for headings
- Style: Clean and professional, NOT corporate. Friendly but competent.
  Think high-end contractor, not Fortune 500.
- Fonts: Montserrat for headings (bold), Open Sans for body
- Visual effects: Subtle shadow on cards, orange hover states, smooth scroll

PAGE STRUCTURE:
1. Hero: Left-aligned heading "Your Trusted [Service] Experts in [City]", subtext
   with key differentiator, two CTAs: "Get a Free Quote" (orange) and "Call Now:
   (555) 123-4567" (navy outline). Right side: image placeholder of work being done.
2. Trust bar: Horizontal strip — "Licensed & Insured", "500+ 5-Star Reviews",
   "Same-Day Service", "Family Owned Since [Year]". Icons for each.
3. Services: 2x3 grid of service cards. Each: icon, service name, 2-line description,
   "Learn More →" link. Services: [List 6 specific services for the industry].
4. Stats section: Navy background with white text. 4 big numbers in a row:
   "15+ Years", "500+ Projects", "4.9 Stars", "100% Satisfaction"
5. Work gallery: 2x3 image grid of before/after or completed work. Lightbox on click.
   Captions below each image.
6. Reviews: 3 review cards — 5 stars, reviewer name, review text (2-3 sentences),
   Google review badge. "See All Reviews on Google →" link.
7. Service area: Light gray background, heading "Proudly Serving [City] and Surrounding
   Areas", list of 8-12 nearby cities/neighborhoods, small map placeholder.
8. Contact / CTA: Split layout — left side: contact form (name, phone, email, service
   needed dropdown, message), right side: phone number (large), email, business hours,
   address. Orange "Submit" button.
9. Footer: Logo, quick links, service list, contact info, license numbers,
   social media icons, copyright.

TECHNICAL:
- Single HTML file with inline CSS and vanilla JS
- Fully responsive — mobile-first layout
- Click-to-call on phone numbers (tel: links)
- Form with client-side validation
- Smooth scroll navigation
- Google Fonts: Montserrat + Open Sans
- Placeholder images from unsplash related to the service industry

QUALITY BAR:
This should look like a $8,000 custom site, not a GoDaddy template. The difference is
whitespace and typography. 80-100px between sections. Orange is used ONLY for CTAs and
key highlights — never for backgrounds or large areas. Navy provides authority. The form
should look inviting, not intimidating — rounded corners, generous padding, clear labels.
Phone number should be visible within 2 seconds of landing. Mobile layout should put
"Call Now" as a sticky button at the bottom. Every section should answer one question
the homeowner has: "Can I trust them?" "What do they do?" "Are they good?" "Are they near me?"
"How do I contact them?"
```

### Template 4: Creative Portfolio

```
Build a single-page portfolio website for a creative professional.

BUSINESS CONTEXT:
- Name: [Full Name]
- Role: [Photographer / Designer / Art Director / Filmmaker / etc.]
- Audience: Potential clients (brands, agencies, magazines), collaborators
- Brand personality: Minimal, confident, design-forward, understated
- Positioning: Work speaks for itself — no gimmicks, no clutter

DESIGN DIRECTION:
- Background: Near-black #0A0A0A
- Text: White #FFFFFF for headings, #888888 for body/secondary
- Accent: None — no color accents. Pure monochrome. Let the work provide the color.
- Style: Ultra-minimal. Maximal whitespace. Think photography gallery.
  Reference: studios like Sagmeister & Walsh, photographers like Peter Lindbergh
- Fonts: Helvetica Neue or Inter for everything, thin weight for body, medium for headings
- Visual effects: Smooth hover zoom on portfolio images, fade-in on scroll, cursor effects

PAGE STRUCTURE:
1. Hero: Full-viewport. Name in large text (60-72px, thin weight), role underneath
   in small caps with letter-spacing. No image, no CTA — just the name. Scroll
   indicator at bottom (thin animated arrow).
2. Brief bio: 2-3 sentences max. Left-aligned, 50% width. "Based in [City].
   Working with [types of clients]. Focused on [what you do]." Small text, lots
   of whitespace around it.
3. Selected work: Masonry grid layout, 2-3 columns. 8-12 project images. Each image:
   hover reveals project title and category in overlay. Click opens project detail
   (or links to project page). Images should be large and prominent.
   No borders, no cards, no shadows — just images floating in space.
4. Client logos: Single row of 6-8 grayscale logos. No heading needed — maybe just
   "Selected clients" in tiny text above. Subtle, not boastful.
5. Contact: Minimal. Large email address as a mailto link. City. Instagram handle.
   Nothing else. No form — just the email.
6. Footer: Copyright line only. Nothing else.

TECHNICAL:
- Single HTML file with inline CSS and vanilla JS
- Masonry grid using CSS columns (no library needed)
- Smooth image hover effects (scale 1.02, overlay fade)
- Scroll-triggered fade-in using IntersectionObserver
- Fully responsive — masonry collapses to 1 column on mobile
- System fonts (no Google Fonts needed — Helvetica/Inter stack)
- Placeholder images from unsplash with artistic/creative themes

QUALITY BAR:
This is the hardest template to get right because there's nowhere to hide. Every pixel
matters. The site should feel like walking into a high-end gallery — quiet, confident,
spacious. Whitespace is the primary design element. 120px+ between sections. Images are
the content, everything else is secondary. Body text should be 14-15px, slightly gray,
never competing with the work. The hover effect on portfolio images should be smooth and
subtle — 0.4s ease transition, not jarring. No decorative elements anywhere. If you
removed the content, the layout itself should still look intentional.
```

### Template 5: Boutique E-Commerce

```
Build a single-page e-commerce landing for a boutique brand.

BUSINESS CONTEXT:
- Name: [Brand Name]
- Product: [Handcrafted leather goods / Artisan candles / Small-batch skincare / etc.]
- Audience: Design-conscious buyers, 25-45, value quality over quantity, willing to pay premium
- Brand personality: Artisanal, warm, considered, premium
- Positioning: Small-batch, handmade, story-driven — the opposite of mass-produced

DESIGN DIRECTION:
- Background: Warm dark #1A1510
- Primary text: Cream #F5F0E8
- Accent: Amber #D4956A (for CTAs and highlights)
- Card backgrounds: #231F18 (slightly lighter than bg)
- Style: Warm, tactile, organic. Should feel like touching fine paper.
  Reference: Aesop, Le Labo, Kinfolk Magazine
- Fonts: Cormorant Garamond for headings (elegant serif), Karla for body (clean sans)
- Visual effects: Soft parallax on hero, fade-in sections, warm grain texture overlay,
  subtle hover lift on product cards

PAGE STRUCTURE:
1. Hero: Full-viewport warm-toned image (dimmed), brand name in elegant serif (56px),
   tagline: "[Handcrafted / Artisan] [product] for [who]", single CTA
   "Shop the Collection" in amber.
2. Brand story: Centered text block, 60% width. 2-3 paragraphs about the craft,
   the maker, the materials. Pull quote in large serif between paragraphs.
   "Every piece tells a story." Warm, authentic tone.
3. Featured collection: Heading "The Collection". 2x2 or 3-column grid of 4-6 products.
   Each: large product image, product name, one-line description, price. Hover: subtle
   lift and amber "Add to Cart" text appears. Clean cards with rounded corners.
4. Process: "How It's Made" — 3-4 steps with image + text alternating left/right.
   Show the craft: materials, workshop, handwork, finished product. Builds perceived value.
5. Reviews: 3 testimonials in cream text on dark background. Reviewer name and location.
   5-star rating in amber. Centered, generous spacing between each.
6. Newsletter: "Join the Inner Circle" — email input + "Subscribe" button in amber.
   "First access to new collections, behind-the-scenes, and 10% off your first order."
7. Footer: Brand name, Instagram link, shipping info ("Free shipping over $100"),
   return policy one-liner, copyright. Simple and clean.

TECHNICAL:
- Single HTML file with inline CSS and vanilla JS
- Fully responsive — product grid goes to 2-col then 1-col on mobile
- Smooth scroll
- Newsletter form (client-side only, ready to connect to Resend/Mailchimp)
- Google Fonts: Cormorant Garamond + Karla
- Placeholder product images from unsplash
- Grain texture overlay using CSS (subtle noise filter)

QUALITY BAR:
This should feel like unboxing a luxury product. Warm, intentional, unhurried. The amber
accent should appear only on interactive elements — CTAs, stars, hover states — never as
decoration. 100px between sections. Product images should be large and aspirational. The
brand story section is critical — it should read like a magazine feature, not a corporate
About page. Grain texture should be barely perceptible (opacity 0.03-0.05). Typography:
48px headings in serif, 16px body in sans-serif, 1.8 line height for body text. The
overall feel: if Kinfolk Magazine designed a web store.
```

## Design Tips That Make the Difference

**Whitespace is your best tool.** 80-120px padding between major sections. Beginners cram things together. Premium sites let content breathe. When in doubt, add more space.

**Limit your palette.** 2-3 colors maximum. One dark/light base, one brand color, one accent for CTAs. Every additional color makes the site look cheaper.

**Typography hierarchy matters more than color.** 48-52px for main headings, 24-32px for subheadings, 16-18px for body. Use font weight (not just size) to create contrast.

**Scroll-triggered animations.** Fade-in and slight upward movement as sections enter the viewport. Use IntersectionObserver — it's native JS, no library needed. Keep animations subtle: 0.6s ease, 20px translateY.

**Reference real brands.** Tell Claude to reference Apple, Stripe, Linear, Aesop, or whichever brand matches the aesthetic. Claude knows what these sites look like and will match the quality bar.

**Anti-template language.** Always include "Do NOT make it look like a template" and "This should look like it cost $15,000" in your prompt. This primes Claude to avoid generic layouts.

## The Sales Process

### Finding Clients

1. Open Google Maps in any city
2. Search for businesses in high-value niches (see below)
3. Click through to their websites
4. If the website looks like it was built in 2015 (or doesn't exist), that's a prospect
5. Build a free demo using the appropriate template above
6. Email them with before/after: "I noticed your website doesn't match the quality of your business. I built this as a concept — what do you think?"

### The Pitch

```
Subject: Built you something — [Business Name]

Hi [Name],

I was looking at [business name] and your reviews are incredible — clearly
you run a great [business type]. But your website doesn't reflect that.

I put together a quick concept of what a modern site could look like for you:
[link to demo on Vercel]

If you like the direction, I can have the full thing live in a week.

Happy to jump on a quick call if you want to talk through it.

[Your name]
```

### Closing

- Show the demo (already built — they can see it live)
- Walk through on a call, share your screen
- Compare side-by-side with their current site
- Quote based on scope (see pricing below)
- 50% upfront, 50% on delivery
- 1-week turnaround for single page, 2 weeks for multi-page

## Pricing Guide

| Project Type | Price Range | Build Time | Your Cost |
|---|---|---|---|
| Single landing page | $2,000 - $5,000 | 1-2 days | ~$5-10 in API |
| Multi-page site (3-5 pages) | $5,000 - $10,000 | 3-5 days | ~$10-20 in API |
| SaaS marketing site | $8,000 - $15,000 | 5-7 days | ~$15-30 in API |
| Monthly maintenance | $100 - $300/mo | 1-2 hrs/mo | ~$2-5 in API |

### High-Value Niches

| Niche | Why They Pay | Typical Budget |
|---|---|---|
| Med Spas & Aesthetics | High customer LTV, image-driven | $5,000 - $12,000 |
| Law Firms | Need trust signals, high case values | $5,000 - $15,000 |
| Real Estate (Luxury) | Commission justifies spend | $5,000 - $10,000 |
| SaaS Companies | Need conversion-optimized pages | $8,000 - $20,000 |
| Dental Practices | Competitive local market | $3,000 - $8,000 |
| E-Commerce (Boutique) | Direct revenue from site | $5,000 - $15,000 |
| Restaurants (Upscale) | Ambiance extends to web presence | $3,000 - $7,000 |
| Fitness / Wellness Studios | Growing market, brand-focused | $3,000 - $8,000 |

## Testing Steps

1. Generate a site using each template — verify it renders correctly in Chrome, Safari, Firefox
2. Test responsive design at 375px (mobile), 768px (tablet), 1440px (desktop)
3. Run Lighthouse audit — target 90+ on Performance, 100 on Accessibility
4. Check all animations work on scroll (IntersectionObserver firing)
5. Verify all links, CTAs, and interactive elements function
6. Test the contact/newsletter form (client-side validation)
7. Deploy to Vercel and test the live URL
8. Load on a real phone and check: text readable? Buttons tappable? Images loading?

## Success Criteria

- Each template produces a visually distinct, premium-quality site in under 2 hours
- Generated sites score 90+ on Lighthouse Performance
- Sites are fully responsive with no layout breaking at any viewport size
- A non-technical person would estimate each site cost $5,000-15,000
- You can customize any template for a specific business in under 30 minutes
- At least one client agrees to a paid project within your first 10 outreach emails
