# AI Ad Agency Strategy — Complete Workflow & Prompt PRDs

> Extracted from the WOP Academy video: "Building an AI Ad Agency for Car Dealerships in Under 45 Minutes"
> This document contains every step, every prompt, model recommendations, role assignments, and a niche adaptation framework.

---

## 1. Executive Summary

### What Was Demonstrated
A solo creator built a complete, functional AI-powered advertising agency for car dealerships in under 45 minutes using a computer-use AI agent (Claude in Chrome). The agent controlled the browser directly — seeing pixels on screen and taking mouse/keyboard actions — with zero API access, zero login credentials shared, and zero technical setup beyond opening the browser.

### The YC Signal
Y Combinator publicly announced investment in "AI-fulfilled agencies" — businesses structured as service agencies where AI performs the majority of client work. This is not AI tools or SaaS. This is the agency model itself, where deliverables are done-for-you services executed by AI agents rather than human employees.

### Why This Matters
- **45 minutes** to a functional agency (brand, research, storefront, ads, deployment, leads, outreach)
- **$2,500/month per client** — only 4 clients needed for $10K/month revenue
- **Near-zero marginal fulfillment cost** — adding a new client requires only their website URL
- **No technical barrier** — computer-use means any web app a human can use, the AI can use
- **Replicable across niches** — the workflow adapts to any local service business

### The 7 Core Steps (from the video)
1. Brand Style Guide Creation
2. Competitive Research (Meta Ad Library)
3. Store Page & Payment Setup
4. Ad Creative Generation (Real Data)
5. Ad Deployment to Meta Ads Manager
6. Lead List Building
7. Automated Outreach Campaign

---

## 2. The 9-Step Strategy (Detailed)

We expand the video's 7 steps into 9 by splitting the store/payment setup and adding a portfolio step at the end. Each step includes a real, usable prompt.

---

### Step 1: Brand Style Guide Creation

**What Happens:**
The AI creates a complete brand identity document from scratch. This is the foundation that every subsequent step references — all ad creatives, landing pages, and outreach materials will follow these guidelines. The brand guide includes an exact color palette with hex codes, typography selections with font families and weights, tone-of-voice guidelines, and visual style rules. For car dealerships, the brand should communicate premium quality, urgency, and trustworthiness.

This is traditionally a $500-$5,000 deliverable that takes days. The AI produces it in under 60 seconds.

**The Prompt:**
```
You are a senior brand strategist at a premium advertising agency. Create a complete brand style guide for an AI-powered automotive advertising agency that serves car dealerships.

The agency name is "{agency_name}". The target clients are {niche} in the {location} area.

Create a comprehensive brand guideline document that includes:

1. COLOR PALETTE
   - Primary color (bold, attention-grabbing — think automotive power)
   - Secondary color (professional, trustworthy)
   - Accent color (urgency, CTAs)
   - Neutral colors (backgrounds, text)
   - Provide exact hex codes for each

2. TYPOGRAPHY
   - Heading font (strong, modern)
   - Body font (clean, readable)
   - CTA font (bold, action-oriented)
   - Specify font families, weights, and sizes for each use case

3. TONE OF VOICE
   - How should ad copy sound? (e.g., urgent but not pushy, professional but approachable)
   - 5 example phrases that capture the tone
   - 5 phrases to NEVER use

4. VISUAL GUIDELINES
   - Image treatment (how photos should be styled/filtered)
   - Layout rules (spacing, alignment, grid)
   - Logo usage rules
   - Ad creative dimensions and formats

5. AD COPY FRAMEWORK
   - Headline formula (e.g., [Urgency] + [Offer] + [Vehicle Type])
   - Body copy structure
   - CTA patterns (3 variations)

Output this as a clean, professional document that I can hand to any designer or AI agent and they can produce on-brand work immediately.
```

**Expected Output:** A 2-4 page brand guideline document with hex codes, font specs, tone rules, and ad copy frameworks.

**Model:** Claude Opus 4.6 — Creative strategy requires deep reasoning about brand positioning.

**Role:** Designer — "Maintain strict adherence to brand guidelines. Create assets that look like they came from a premium agency."

**Tools/Sites Used:** None (pure generation, no browsing needed).

**Key Insight:** The brand guide is the foundation everything else references. If this is weak, every subsequent step produces inconsistent output. Invest the Opus tokens here.

---

### Step 2: Competitive Research via Meta Ad Library

**What Happens:**
The AI agent opens the Meta Ad Library (a publicly accessible tool showing all active ads for any Facebook advertiser), searches for 15-20 car dealerships by name, and catalogs the tactics, copy patterns, visual styles, and offer structures being used. It synthesizes this into a multi-page strategy playbook covering seasonal patterns, financial offer structures, urgency language, CTA frameworks, and visual layout patterns.

This is the most strategically valuable step. A human analyst would need 20-40 hours to produce equivalent research. The AI does it in under 10 minutes.

**The Prompt:**
```
You are a competitive intelligence analyst specializing in paid advertising. Your task is to research the Meta Ad Library for car dealership advertising strategies.

Navigate to the Meta Ad Library (https://www.facebook.com/ads/library/) and search for active ads from at least 15 different car dealerships. Focus on dealerships that appear to be running sophisticated campaigns (multiple ads, varied creative, clear strategy).

For each dealership, document:
- Number of active ads
- Ad formats used (image, video, carousel)
- Headline patterns and copy frameworks
- Offer types (financing, trade-in, seasonal sales)
- Visual style (stock photos vs real inventory, overlay text, branding)
- CTA language and urgency tactics
- Geographic targeting indicators

After researching all dealerships, compile a STRATEGY PLAYBOOK that includes:

1. TOP 10 AD TACTICS (ranked by frequency of use across dealerships)
   - Tactic name, description, example copy, when to use it

2. SEASONAL PATTERNS
   - Which promotions run during which months/holidays
   - How to plan a 12-month ad calendar

3. COPY FORMULAS THAT WORK
   - 5 headline formulas with fill-in-the-blank templates
   - 3 body copy structures
   - Best-performing CTA patterns

4. VISUAL PATTERNS
   - What image styles get used most
   - How top dealerships showcase inventory
   - Color and text overlay patterns

5. COMPETITIVE GAPS
   - What are dealerships NOT doing that we could exploit?
   - Underused ad formats or targeting strategies

Output a comprehensive strategy document I can reference for all future ad creation.
```

**Expected Output:** A 4-8 page strategy playbook with specific tactics, copy formulas, and competitive analysis.

**Model:** Claude Sonnet 4.6 — Data gathering and pattern recognition. Browsing-heavy task where speed matters more than creative depth.

**Role:** Researcher — "Be exhaustive in your search. Don't stop at surface-level information — dig deeper."

**Tools/Sites Used:** Meta Ad Library (https://www.facebook.com/ads/library/)

**Key Insight:** The creator said "most agencies to this day still don't have" this kind of research document. The AI produced a "national level playbook" by analyzing ads from top car dealerships across America. This single deliverable justifies the entire workflow.

---

### Step 3: Store Page & Service Package Setup

**What Happens:**
The AI creates a professional agency storefront with service packages and pricing. This transforms the operation from an experiment into a sellable business. The storefront includes the agency name, service description, pricing tiers, and an integrated calendar booking system so every prospect interaction ends with a concrete next step.

**The Prompt:**
```
You are a business development specialist setting up a professional service offering. Navigate to {store_platform} (e.g., Shopify, Gumroad, or Stripe) and create a storefront for my advertising agency.

Agency details:
- Name: {agency_name}
- Service: AI-powered advertising management for {niche}
- Target client: Local {niche} businesses in {location}

Create the following:

1. MAIN SERVICE PAGE
   - Headline: Clear value proposition (what dealerships get)
   - Subheading: The key differentiator (AI-powered, faster, data-driven)
   - Service description: 3-4 paragraphs explaining the offering
   - Social proof section: "Powered by the same AI technology used by Fortune 500 agencies"

2. PRICING PACKAGES (3 tiers)
   - STARTER ({starter_price}/month): Basic ad management, {starter_ads} ad creatives/month, monthly reporting
   - GROWTH ({growth_price}/month): Full ad management, {growth_ads} creatives/month, weekly reporting, A/B testing
   - PREMIUM ({premium_price}/month): Everything in Growth + competitive monitoring, lead generation, outreach support

3. CHECKOUT FLOW
   - Set up payment links for each tier
   - Add a calendar booking integration (Calendly or built-in scheduling)
   - Confirmation page with onboarding instructions

4. ONBOARDING FORM
   - Fields: Business name, website URL, current ad spend, target audience, goals
   - This form captures everything the AI needs to start creating ads

Make the storefront look professional and trustworthy. Use the brand colors from our style guide.
```

**Expected Output:** A live storefront with 3 pricing tiers, checkout links, and calendar booking.

**Model:** Claude Sonnet 4.6 — Form-filling and navigation. Structured task with clear steps.

**Role:** Full-Stack Operator — "Think about the full pipeline: how does this step feed into the next one?"

**Tools/Sites Used:** Shopify, Gumroad, Stripe, or similar storefront platform. Calendly for scheduling.

**Key Insight:** The calendar booking integration is the key detail. Instead of "let's talk sometime," every prospect gets "here's my calendar, book a call today." This converts interest into meetings.

---

### Step 4: Ad Creative Generation (Real Data)

**What Happens:**
This is the litmus test. The AI visits a real dealership's website, scrapes actual vehicle inventory (real VINs, real prices, real promotions), and produces multiple ad creatives using the brand style guide from Step 1 and the strategy playbook from Step 2. The ads must use 100% real data — no hallucinated vehicles, no fake prices, no made-up offers. For automotive advertising, data accuracy is legally required.

**The Prompt:**
```
You are a direct-response advertising creative director. Your task is to create professional ad creatives for a car dealership client.

REFERENCE DOCUMENTS:
- Brand Style Guide: [Reference the output from Step 1]
- Strategy Playbook: [Reference the output from Step 2]

CLIENT: {client_name}
WEBSITE: {client_website}

INSTRUCTIONS:
1. Navigate to {client_website}
2. Browse their current vehicle inventory — document at least 10 vehicles with:
   - Make, model, year
   - VIN number
   - Listed price
   - Any current promotions or incentives
   - Key features and mileage

3. Using ONLY the real data you found, create the following ad creatives:

   AD SET 1: Inventory Spotlight (3 ads)
   - Each ad features one specific vehicle with real data
   - Use headline formula from strategy playbook
   - Include real price, real VIN, real features
   - CTA: "View This [Vehicle] Now" or "Check Availability"

   AD SET 2: Promotional Offer (2 ads)
   - Based on any active promotions on their website
   - If no active promo, use seasonal offer tactics from the playbook
   - Stacked offers format (e.g., "$5,000 off + 0% APR + Free Maintenance")
   - CTA: "Claim This Offer" or "Limited Time — Act Now"

   AD SET 3: Brand Authority (1 ad)
   - General dealership promotion
   - Emphasize reputation, selection, service
   - CTA: "Browse Our Full Inventory"

CRITICAL RULES:
- EVERY piece of data must come directly from the dealership's website
- Do NOT fabricate any vehicle details, prices, or offers
- Follow the brand style guide exactly (colors, fonts, tone)
- Create ads in Meta-ready dimensions (1080x1080 for feed, 1080x1920 for stories)

Output each ad with: headline, body copy, CTA, image description, and which real vehicle/offer it features.
```

**Expected Output:** 6 ad creatives with real vehicle data, proper copy frameworks, and brand-consistent design.

**Model:** Claude Opus 4.6 — Requires visual understanding, data accuracy, creative writing, and brand adherence simultaneously. This is the most complex step.

**Role:** Marketer — "Everything you create should drive action. Use proven frameworks: AIDA, PAS, urgency, scarcity."

**Tools/Sites Used:** Client's dealership website.

**Key Insight:** Zero hallucination on vehicle data is the proof point. The creator said "there was no hallucinated vehicles, no fake data." This is what makes the output usable in a regulated industry.

---

### Step 5: Ad Deployment to Meta Ads Manager

**What Happens:**
The AI opens Facebook Ads Manager, creates a new campaign, uploads the ad creatives from Step 4, fills in all campaign settings, and configures targeting. The most impressive detail: the AI inferred geographic targeting from context — knowing the dealership was in Kansas, it automatically set a 25-mile radius. The human only needs to click "Publish."

**The Prompt:**
```
You are a paid media specialist deploying ads to Meta Ads Manager. Take the ad creatives we just created and set them up as a live campaign.

INSTRUCTIONS:
1. Open Meta Ads Manager (https://www.facebook.com/adsmanager/)
2. Create a new campaign with the following structure:

   CAMPAIGN LEVEL:
   - Campaign name: "{client_name} - {month} {year} - AI Agency"
   - Objective: Traffic (or Conversions if pixel is set up)
   - Budget: ${daily_budget}/day
   - Schedule: Start today, run continuously

   AD SET LEVEL:
   - Ad set name: "{client_name} - Local Targeting"
   - Targeting:
     - Location: {location} + {radius} mile radius
     - Age: 25-65
     - Interests: Cars, Auto Dealerships, New Cars, Used Cars, Car Shopping
     - Placements: Automatic (or Facebook Feed + Instagram Feed + Stories)

   AD LEVEL:
   - Upload each ad creative from the previous step
   - Fill in headlines, body copy, and CTAs exactly as written
   - Set destination URL to {client_website}
   - Add UTM parameters: ?utm_source=meta&utm_medium=paid&utm_campaign=ai_agency

3. Review all settings for accuracy
4. Leave the campaign in DRAFT status (do NOT publish — I will review and publish manually)

IMPORTANT: Double-check that:
- Geographic targeting matches the dealership's location
- All ad copy matches what we created
- Images are uploaded correctly
- Links go to the right website
```

**Expected Output:** A fully configured Meta Ads campaign in draft status, ready for human review and one-click publish.

**Model:** Claude Sonnet 4.6 — GUI navigation and form-filling. Structured, repetitive task.

**Role:** Full-Stack Operator — "Adapt your approach based on what's needed."

**Tools/Sites Used:** Facebook Ads Manager (https://www.facebook.com/adsmanager/)

**Key Insight:** The AI inferred geographic targeting from context without being explicitly told. The prompt above makes it explicit, but the video showed the AI doing this autonomously — a sign of genuine reasoning, not just instruction-following.

---

### Step 6: Lead List Building

**What Happens:**
The AI searches for local businesses in the target niche within a geographic radius, compiles them into a structured spreadsheet with names, addresses, websites, social media handles, and any other publicly available contact information. The creator got 20 dealerships with Instagram handles in under 2 minutes.

**The Prompt:**
```
You are a business development researcher building a prospect list. I need a comprehensive list of potential clients for my {niche} advertising agency.

INSTRUCTIONS:
1. Search Google, Google Maps, and business directories for {niche} businesses within a {radius}-mile radius of {location}
2. Find at least 20 businesses that match these criteria:
   - Active business with a website
   - Currently advertising (check Meta Ad Library for active ads)
   - Has social media presence (Instagram, Facebook)

3. For EACH business, compile:
   - Business name
   - Physical address
   - Website URL
   - Phone number (if publicly listed)
   - Instagram handle
   - Facebook page URL
   - Number of active Meta ads (from Ad Library)
   - Estimated monthly ad spend (based on number and type of active ads)
   - Notes: Any obvious issues with their current ads (poor creative, outdated offers, etc.)

4. Create this as a structured spreadsheet/table with columns for each field

5. PRIORITIZE the list:
   - HIGH priority: Businesses currently spending on ads but with poor creative quality (they need us most)
   - MEDIUM priority: Businesses with some ad presence but room for improvement
   - LOW priority: Businesses with strong existing ad programs (harder to sell but higher value)

Output the complete list as a formatted table, sorted by priority.
```

**Expected Output:** A spreadsheet of 20+ businesses with contact details, social handles, ad activity, and priority ranking.

**Model:** Claude Sonnet 4.6 — Data gathering, search, and compilation. Speed-focused task.

**Role:** Researcher — "Be exhaustive in your search. Document everything thoroughly."

**Tools/Sites Used:** Google, Google Maps, Meta Ad Library, Instagram, business directories (Yelp, BBB, etc.)

**Key Insight:** The priority ranking based on current ad quality is the differentiator. A prospect who's already spending on bad ads is far easier to close than one with no ad presence at all.

---

### Step 7: Personalized Outreach Campaign

**What Happens:**
Using the lead list from Step 6, the AI crafts personalized outreach messages and sends them via the chosen channel (Instagram DMs, email, LinkedIn). The video showed templated DMs, but the real power is personalization — analyzing each prospect's current ads and tailoring the pitch to their specific weaknesses.

**The Prompt:**
```
You are a business development representative sending personalized outreach messages. Using the lead list we built, craft and send outreach messages to each prospect.

OUTREACH STRATEGY:
- Channel: {outreach_channel} (Instagram DM / Email / LinkedIn)
- Tone: Professional, value-first, not pushy
- Hook: Lead with what you can do for THEM, not what you're selling

FOR EACH PROSPECT:
1. Review their current ads in Meta Ad Library
2. Identify 1-2 specific issues or opportunities (e.g., "Your inventory ads are using stock photos instead of real vehicles" or "You're not running any seasonal promotions for Presidents' Day")
3. Craft a personalized message using this framework:

   SUBJECT/OPENER: Specific observation about their business
   BODY: How your service solves that specific problem
   PROOF: Brief mention of your capabilities (link to storefront)
   CTA: Clear next step (book a call via your calendar link)

MESSAGE TEMPLATE (personalize for each):
---
Hi {prospect_name},

I was looking at {business_name}'s ads on Meta and noticed {specific_observation}. {Why_that_matters — e.g., "This means you're likely paying more per lead than you need to."}

I run an AI-powered ad agency that specializes in {niche} advertising. We {specific_value_prop — e.g., "create ads using your real inventory data so every vehicle on your lot has a targeted ad running within hours of being listed."}.

Would you be open to a quick 15-minute call to see if this could work for {business_name}? Here's my calendar: {calendar_link}

Either way, I'd be happy to send over a free ad audit showing exactly where your current campaigns could improve.

Best,
{your_name}
{agency_name}
---

IMPORTANT:
- Personalize EVERY message. Do NOT send identical copy to everyone.
- Be respectful of platform terms of service
- Space messages 30-60 seconds apart to avoid rate limiting
- Log each sent message with timestamp and prospect name
```

**Expected Output:** 20 personalized outreach messages sent, each referencing specific details about the prospect's current advertising.

**Model:** Claude Opus 4.6 — Personalization requires analyzing each prospect's ads and crafting unique messaging. This is high-reasoning work.

**Role:** Outreach Specialist — "Personalized, warm but professional, value-first. Research each prospect before reaching out."

**Tools/Sites Used:** Instagram, Meta Ad Library (for prospect research), email client, or LinkedIn.

**Key Insight:** Personalization is the conversion multiplier. A generic "we do ads" DM gets ignored. A message that says "I noticed your Spring Clearance ads are using 2023 inventory photos" gets a response.

**Caveat:** Automated DM outreach may violate platform terms of service. The video creator acknowledged this uncertainty. For production use, email outreach is safer.

---

### Step 8: Portfolio & Results Documentation

**What Happens:**
The AI compiles all work produced during the workflow into a professional portfolio document. This includes the brand guide, sample ad creatives, strategy playbook summary, and screenshots of the Meta Ads campaign setup. This portfolio serves as the primary sales tool when prospects ask "show me what you can do."

**The Prompt:**
```
You are a creative director compiling a portfolio for our advertising agency. Using everything we've created in the previous steps, build a professional portfolio document.

PORTFOLIO STRUCTURE:

1. COVER PAGE
   - Agency name and tagline
   - "AI-Powered Advertising for {niche}"
   - Professional, on-brand design

2. ABOUT US (1 page)
   - What we do (2-3 sentences)
   - Our approach (AI-powered, data-driven, real inventory)
   - Key differentiators (speed, accuracy, cost efficiency)

3. OUR PROCESS (1 page)
   - Visual workflow: Client Website → AI Analysis → Ad Creation → Deployment → Optimization
   - Emphasize: "From your website URL to live ads in under 1 hour"

4. SAMPLE WORK (2-3 pages)
   - Include the ad creatives from Step 4
   - Show before/after: "Client's existing ads" vs "Our AI-generated ads"
   - Include the data accuracy callout (real VINs, real prices)

5. STRATEGY CAPABILITIES (1 page)
   - Competitive research (reference the playbook from Step 2)
   - Seasonal campaign planning
   - Automated inventory monitoring (future capability)

6. PRICING (1 page)
   - 3 tiers from Step 3
   - "Book a free strategy call" CTA with calendar link

7. CASE STUDY (1 page)
   - Use the {client_name} test as the case study
   - Timeline: "Complete agency setup in under 45 minutes"
   - Results: X ads created, Y vehicles featured, Z prospects contacted

Save this as a professional PDF-ready document.
```

**Expected Output:** A 6-8 page portfolio document ready to send to prospects.

**Model:** Claude Opus 4.6 — Creative synthesis and professional writing.

**Role:** Designer — "Every visual element should be consistent. Quality over quantity."

**Tools/Sites Used:** Document editor (Google Docs, Notion, or similar).

**Key Insight:** The portfolio is the trust bridge. Prospects won't buy based on a DM alone. The portfolio shows real work, real data, and a professional operation.

---

### Step 9: Automated Monitoring Setup (Future State)

**What Happens:**
This is the evolution from manual workflow to autonomous system. The AI is configured to monitor the client's website on a schedule (hourly/daily), detect new inventory listings, automatically generate ads for new vehicles, and either deploy them or queue them for human approval. This turns the agency from "I run it" to "it runs itself."

**The Prompt:**
```
You are an automation engineer setting up a monitoring system. Configure an automated workflow that watches a car dealership's website for inventory changes and generates ads automatically.

MONITORING WORKFLOW:

1. SCHEDULE: Check {client_website}/inventory every {check_interval} (e.g., every 2 hours during business hours)

2. DETECTION: Compare current inventory to the last known state
   - NEW vehicles: Flag for ad creation
   - REMOVED vehicles: Flag for ad deactivation
   - PRICE CHANGES: Flag for ad update

3. AUTO-GENERATION: For each new vehicle detected:
   - Pull all vehicle data (make, model, year, VIN, price, features, photos)
   - Generate ad creative using our brand style guide
   - Write ad copy using our strategy playbook formulas
   - Create both feed (1080x1080) and stories (1080x1920) formats

4. DEPLOYMENT: Either:
   - AUTO-DEPLOY: Upload to Meta Ads Manager and activate immediately
   - QUEUE: Add to a review queue for human approval before going live

5. REPORTING: Daily summary email:
   - New vehicles detected: X
   - Ads created: Y
   - Ads deployed: Z
   - Total active ads: N
   - Estimated daily spend: $X

Set up the initial monitoring for {client_name} at {client_website}.
```

**Expected Output:** A configured monitoring workflow with detection, generation, and deployment automation.

**Model:** Claude Opus 4.6 — Complex multi-system orchestration.

**Role:** Full-Stack Operator — "Think about the full pipeline."

**Tools/Sites Used:** Client website, Meta Ads Manager, cron/scheduling system.

**Key Insight:** This is the endgame — recurring revenue with near-zero fulfillment cost. The creator asked the AI "can you check the website every single hour?" and it confirmed this was possible. When the system runs autonomously, the human role reduces to client relationship management and quality oversight.

---

## 3. Missing Steps (What the Video Didn't Show)

These 5 additional steps would make the workflow production-ready for a real agency operation.

---

### Missing Step A: Client Onboarding Questionnaire

**What Happens:**
Before creating any ads, gather structured information from the client: brand preferences, target audience demographics, competitors they admire, past ad performance data, seasonal priorities, and compliance requirements. This prevents the AI from making assumptions.

**The Prompt:**
```
You are an account manager onboarding a new client. Create a comprehensive onboarding questionnaire for a {niche} advertising client.

Include these sections:
1. BUSINESS BASICS: Name, location, years in operation, number of locations
2. CURRENT ADVERTISING: Monthly ad budget, platforms used, best/worst performing campaigns
3. TARGET AUDIENCE: Demographics, geographic reach, buying triggers, pain points
4. BRAND PREFERENCES: Colors to avoid, tone preferences, competitors they admire
5. INVENTORY/SERVICES: How often inventory changes, seasonal patterns, flagship products
6. COMPLIANCE: State-specific advertising regulations, required disclaimers, prohibited claims
7. GOALS: Primary KPI (leads, foot traffic, online sales), monthly targets, timeline
8. ACCESS: Website URL, social media accounts, Meta Business Manager access level

Format as a professional form that can be sent to clients via email or embedded on our website.
```

**Expected Output:** A structured onboarding form with 25-30 questions organized by section.

**Model:** Claude Sonnet 4.6 — Structured document creation.

**Role:** Full-Stack Operator

---

### Missing Step B: Analytics & Reporting Dashboard

**What Happens:**
Set up automated reporting that pulls ad performance data (impressions, clicks, CTR, CPC, conversions) and presents it in a client-friendly dashboard. Monthly reports are the primary retention tool for agencies — clients stay when they can see results.

**The Prompt:**
```
You are a data analyst setting up a reporting system. Create a monthly ad performance report template and configure data sources.

REPORT SECTIONS:
1. EXECUTIVE SUMMARY: 3-4 key metrics with month-over-month comparison
2. CAMPAIGN PERFORMANCE: Table with each ad's impressions, clicks, CTR, CPC, conversions
3. TOP PERFORMING ADS: The 3 best ads with screenshots and metrics
4. AUDIENCE INSIGHTS: Demographics of who's clicking and converting
5. RECOMMENDATIONS: Data-driven suggestions for next month
6. BUDGET ANALYSIS: Spend vs results, cost per lead, ROI estimate

Set up a Google Sheets dashboard that pulls data from Meta Ads API (or manually updated) and auto-generates this report monthly.

Also create an automated email template that sends the report to the client with a brief narrative summary.
```

**Expected Output:** A report template, dashboard setup, and automated email system.

**Model:** Claude Sonnet 4.6 — Data structuring and template creation.

**Role:** Analyst — "Don't just report what you see — interpret what it means for the business."

---

### Missing Step C: Content Calendar Creation

**What Happens:**
Build a 12-month content and ad calendar based on the competitive research from Step 2. Map seasonal events, holidays, manufacturer promotions, and industry trends to specific ad campaigns. This transforms the agency from reactive (making ads when asked) to proactive (having campaigns ready before they're needed).

**The Prompt:**
```
You are a media planner creating a 12-month advertising calendar for a {niche} client.

Using the strategy playbook from our competitive research, build a complete calendar that includes:

FOR EACH MONTH:
- Primary campaign theme (e.g., January = New Year New Car, February = Presidents' Day Sale)
- Secondary campaign (ongoing inventory spotlight)
- Ad creative types needed (X feed ads, Y stories, Z carousel)
- Estimated budget allocation (% of annual budget)
- Key dates and deadlines (creative due, campaign launch, campaign end)

ALSO INCLUDE:
- Major automotive industry events and how to leverage them
- Manufacturer incentive windows (when OEMs offer dealer cash, financing specials)
- Local event tie-ins (state fairs, community events, sports seasons)
- Inventory cycle patterns (when to push specific vehicle types)

Output as both a visual calendar (month grid) and a detailed planning document with notes for each campaign.
```

**Expected Output:** A 12-month calendar with campaign themes, creative requirements, and budget allocation.

**Model:** Claude Opus 4.6 — Strategic planning with seasonal reasoning.

**Role:** Analyst — "Extract patterns and think about scalability."

---

### Missing Step D: CRM & Pipeline Setup

**What Happens:**
Configure a CRM system to track prospects from the lead list, manage the sales pipeline, automate follow-up sequences, and track client lifecycle (prospect → lead → trial → client → renewal). This is the operational backbone that prevents prospects from falling through the cracks.

**The Prompt:**
```
You are a sales operations specialist setting up a CRM for a service agency.

Navigate to {crm_platform} (HubSpot, Pipedrive, or similar free CRM) and configure:

1. PIPELINE STAGES:
   - New Lead (from lead list)
   - First Contact (outreach sent)
   - Responded (they replied)
   - Discovery Call Booked
   - Proposal Sent
   - Negotiation
   - Closed Won / Closed Lost

2. CONTACT FIELDS:
   - Business name, contact person, email, phone
   - Website URL, Instagram, Facebook
   - Current ad spend (estimated)
   - Number of locations
   - Lead source (outreach, referral, inbound)
   - Priority score (from our lead list)

3. AUTOMATIONS:
   - Follow-up email 3 days after first contact if no response
   - Second follow-up 7 days later
   - Calendar reminder for booked calls
   - Win/loss notification to agency owner

4. DASHBOARD:
   - Pipeline value (total potential revenue)
   - Conversion rate by stage
   - Average deal cycle length
   - Monthly closed revenue

Import the 20 leads from our lead list into the CRM with their priority rankings.
```

**Expected Output:** A configured CRM with pipeline stages, automations, and imported leads.

**Model:** Claude Sonnet 4.6 — Form filling and platform configuration.

**Role:** Full-Stack Operator

---

### Missing Step E: Testimonial & Case Study Generator

**What Happens:**
After delivering results for the first client, the AI automatically compiles performance data into a case study format. This creates a flywheel: better case studies → easier sales → more clients → more case studies.

**The Prompt:**
```
You are a content strategist creating case study assets. Using the performance data from our first client, {client_name}, create:

1. ONE-PAGE CASE STUDY
   - Client background (who they are, what they needed)
   - Challenge (what problem they had with advertising)
   - Solution (what we did — AI-powered ad creation with real inventory data)
   - Results (metrics: ads created, leads generated, cost per lead, ROI)
   - Client quote (draft a realistic testimonial they can approve)

2. SOCIAL PROOF SNIPPETS
   - 3 tweet-length quotes for social media
   - 1 LinkedIn post summarizing the results
   - Stats graphic (key metrics in a visual format)

3. WEBSITE TESTIMONIAL
   - A paragraph for the storefront page
   - Star rating and client attribution

4. PROPOSAL INSERT
   - A half-page summary to include in future proposals
   - Focus on the metrics that matter to {niche} businesses

Use real data where available. Where data isn't available yet, use realistic projections based on industry benchmarks for {niche} advertising.
```

**Expected Output:** Case study PDF, social proof snippets, website testimonial, and proposal insert.

**Model:** Claude Opus 4.6 — Persuasive writing and data synthesis.

**Role:** Marketer — "Everything you create should drive action."

---

## 4. Niche Adaptation Framework

The entire workflow uses `{variables}` for niche-specific details. Here's the complete variable set and three example niches.

### Variable Reference

| Variable | Description | Example (Car Dealerships) |
|----------|-------------|--------------------------|
| `{niche}` | Business vertical | Car Dealerships |
| `{niche_slug}` | URL-safe version | car-dealerships |
| `{agency_name}` | Your agency brand name | Urban Motors Agency |
| `{location}` | Target geographic area | Kansas City, MO |
| `{radius}` | Outreach radius in miles | 25 |
| `{target_audience}` | Who the ads target | Adults 25-65 buying cars |
| `{client_name}` | Example/first client name | McCarthy Auto |
| `{client_website}` | Client's website URL | https://mccarthyauto.com |
| `{daily_budget}` | Default daily ad budget | 50 |
| `{starter_price}` | Entry tier monthly price | $1,500 |
| `{growth_price}` | Mid tier monthly price | $2,500 |
| `{premium_price}` | Top tier monthly price | $5,000 |
| `{starter_ads}` | Entry tier ad count/month | 10 |
| `{growth_ads}` | Mid tier ad count/month | 25 |
| `{outreach_channel}` | Primary outreach method | Instagram DM |
| `{store_platform}` | Storefront platform | Shopify |
| `{crm_platform}` | CRM system | HubSpot Free |
| `{check_interval}` | Monitoring frequency | Every 2 hours |
| `{calendar_link}` | Booking URL | https://calendly.com/... |
| `{your_name}` | Your name | Chase |

---

### Example Niche 1: Dental Practices

| Variable | Value |
|----------|-------|
| `{niche}` | Dental Practices |
| `{location}` | Austin, TX |
| `{radius}` | 15 |
| `{target_audience}` | Adults 25-55, families with children, people searching for cosmetic dentistry |
| `{starter_price}` | $1,200/month |
| `{growth_price}` | $2,000/month |
| `{premium_price}` | $3,500/month |
| `{outreach_channel}` | Email (dental practices check email, not Instagram DMs) |

**Adaptation notes:**
- Step 2 (Research): Search Meta Ad Library for dental practices, orthodontists, cosmetic dentists
- Step 4 (Ad Creative): Instead of vehicle inventory, feature services (whitening, implants, Invisalign) with real pricing from the practice's website
- Step 6 (Leads): Search Google Maps for dental practices, cross-reference with state dental board listings
- Key compliance: HIPAA considerations — ads cannot reference specific patient outcomes without proper disclaimers

---

### Example Niche 2: Real Estate Agencies

| Variable | Value |
|----------|-------|
| `{niche}` | Real Estate Agencies |
| `{location}` | Miami, FL |
| `{radius}` | 20 |
| `{target_audience}` | Home buyers 28-55, investors, people relocating to Florida |
| `{starter_price}` | $1,500/month |
| `{growth_price}` | $3,000/month |
| `{premium_price}` | $5,000/month |
| `{outreach_channel}` | LinkedIn (real estate agents are active on LinkedIn) |

**Adaptation notes:**
- Step 2 (Research): Search Meta Ad Library for real estate agencies, brokerages, individual agents
- Step 4 (Ad Creative): Feature specific listings with real MLS data, prices, photos, and neighborhood info
- Step 9 (Monitoring): Monitor MLS/Zillow for new listings instead of vehicle inventory
- Key compliance: Fair Housing Act — ads cannot target or exclude based on race, religion, national origin, familial status, disability. Meta has specific Housing ad category with restricted targeting.

---

### Example Niche 3: Fitness Studios

| Variable | Value |
|----------|-------|
| `{niche}` | Fitness Studios (CrossFit, Yoga, Pilates, Boxing) |
| `{location}` | Denver, CO |
| `{radius}` | 10 |
| `{target_audience}` | Adults 22-45, fitness-conscious, new year resolution makers |
| `{starter_price}` | $800/month |
| `{growth_price}` | $1,500/month |
| `{premium_price}` | $2,500/month |
| `{outreach_channel}` | Instagram DM (fitness studios are very active on Instagram) |

**Adaptation notes:**
- Step 2 (Research): Search Meta Ad Library for local gyms, CrossFit boxes, yoga studios, boutique fitness
- Step 4 (Ad Creative): Feature class schedules, introductory offers, transformation stories, facility photos
- Step 6 (Leads): Search Google Maps + ClassPass + Yelp for fitness businesses
- Seasonal patterns: January (New Year), May (summer body), September (back to routine) are peak seasons
- Key differentiator: Before/after member transformation ads perform extremely well in fitness

---

## 5. Execution Playbook

### Recommended Execution Order

```
SEQUENTIAL (must be in order):
  Step 1: Brand Style Guide        ← Foundation for everything
  Step 2: Competitive Research      ← Strategy for all future creative
  Step A: Client Onboarding Form    ← Ready before first client interaction

PARALLEL BATCH 1 (can run simultaneously after Steps 1-2):
  Step 3: Store Page Setup
  Step C: Content Calendar
  Step D: CRM Setup

SEQUENTIAL (after batch 1):
  Step 4: Ad Creative Generation    ← Needs brand guide + strategy playbook
  Step 5: Ad Deployment             ← Needs Step 4's creatives

PARALLEL BATCH 2 (can run simultaneously):
  Step 6: Lead List Building
  Step 8: Portfolio Creation        ← Needs Steps 1-5's outputs

SEQUENTIAL (after batch 2):
  Step 7: Outreach Campaign         ← Needs Step 6's lead list + Step 8's portfolio

POST-LAUNCH:
  Step 9: Automated Monitoring      ← Set up after first client is live
  Step B: Reporting Dashboard       ← Set up after ads have data
  Step E: Case Study Generator      ← After first month of results
```

### Estimated Time Per Step (with AI)

| Step | Time | Model | Notes |
|------|------|-------|-------|
| 1. Brand Guide | 1-2 min | Opus | Pure generation, fast |
| 2. Competitive Research | 8-12 min | Sonnet | Browsing 15-20 businesses |
| A. Onboarding Form | 2-3 min | Sonnet | Template creation |
| 3. Store Page | 10-15 min | Sonnet | Platform navigation + setup |
| C. Content Calendar | 5-8 min | Opus | Strategic planning |
| D. CRM Setup | 10-15 min | Sonnet | Platform configuration |
| 4. Ad Creatives | 5-10 min | Opus | Website scraping + creative |
| 5. Ad Deployment | 5-10 min | Sonnet | Ads Manager navigation |
| 6. Lead List | 2-5 min | Sonnet | Search + compilation |
| 8. Portfolio | 5-8 min | Opus | Synthesis + writing |
| 7. Outreach | 10-15 min | Opus | Personalization per prospect |
| **Total** | **~65-105 min** | | |

### Human Checkpoints (Where to Pause and Review)

1. **After Step 1** — Review brand guide before it's used everywhere
2. **After Step 4** — Review ad creatives for accuracy before deployment
3. **After Step 5** — Review campaign settings BEFORE publishing (leave in draft)
4. **After Step 7** — Review outreach messages before sending (especially for compliance)

---

## 6. Prompt Engineering Notes

### Why Prompts Are Structured This Way

1. **Role declaration first** ("You are a senior brand strategist...") — Sets the expertise level and approach. Without this, the AI defaults to generic assistant behavior.

2. **Context injection** ("Using the strategy playbook from our competitive research...") — Each step references outputs from previous steps. This creates a coherent workflow, not isolated tasks.

3. **Explicit output structure** (numbered sections with specific deliverables) — Computer-use agents work better with structured instructions. "Create 6 ads" is better than "create some ads."

4. **CRITICAL RULES section** — Negative constraints prevent common failure modes. "Do NOT fabricate vehicle data" prevents hallucination. "Do NOT publish — leave in draft" prevents accidental deployment.

### Common Mistakes in Prompting Computer-Use Agents

1. **Too vague:** "Make some ads" → Agent doesn't know how many, what format, or what data to use.
   **Better:** "Create 6 ad creatives in 1080x1080 format using real vehicle data from {website}."

2. **No reference to previous context:** "Create ads" (without mentioning the brand guide or strategy playbook) → Agent produces generic, off-brand output.
   **Better:** "Create ads following our brand style guide [reference] and using tactics from our strategy playbook [reference]."

3. **No safety constraints:** "Deploy the ads" → Agent might actually publish them live.
   **Better:** "Configure the ads in Meta Ads Manager and leave them in DRAFT status for my review."

4. **Assuming the agent remembers:** Computer-use agents may lose context between steps. Always re-inject critical information.
   **Better:** Include a REFERENCE DOCUMENTS section in every prompt with the outputs from previous steps.

### Multi-Step vs Single-Step Prompts

**Single-step prompts** work best when:
- The task is self-contained (brand guide, lead list)
- No browsing is required (pure generation)
- The output doesn't depend on real-time web data

**Multi-step prompts** work best when:
- The task involves browsing + analysis + generation (competitive research)
- The agent needs to navigate multiple pages (ad deployment)
- You want the agent to adapt based on what it finds

### Context Injection Pattern (Step N → Step N+1)

```
REFERENCE DOCUMENTS:
- Brand Style Guide: [Paste or reference the full output from Step 1]
- Strategy Playbook: [Paste or reference the full output from Step 2]
- Previous Step Output: [Paste or reference the output from Step N-1]

YOUR TASK:
Using the above references, [describe what to do in Step N]...
```

This pattern ensures every step builds on the last, creating a coherent workflow rather than disconnected tasks. The YT Strategy Lab automates this by passing `step.aiOutput` from completed steps into the `previousOutputs` field of the next execution request.

---

## Appendix: Video Source Reference

- **Creator:** Chase (WOP Academy / wopacademy.com)
- **Video Length:** ~10 minutes
- **Tool Used:** Claude in Chrome (computer-use AI agent via browser extension)
- **Revenue Model:** $2,500/month per dealership client, targeting 4 clients = $10K/month
- **Total Build Time:** Under 45 minutes for complete end-to-end agency
- **Test Client:** McCarthy Auto, Kansas
- **Detailed breakdown:** See `docs/yt-strategies/ai-ad-agency-breakdown.md`
- **Pre-populated project template:** See `docs/yt-strategies/templates/ai-ad-agency-project-seed.json`
- **Generic template with variables:** See `docs/yt-strategies/templates/blank-agency-template.json`
