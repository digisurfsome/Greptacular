# Automated Prospect Pitch Generator

**Domain In, Full Strategy Out**

## What You'll Build

A prospect intelligence system that takes an email address or domain, scrapes the company's website, analyzes it with Claude, and generates a complete outbound strategy -- ICP fit score, audience segments with pain points, personalized cold email scripts, and call talking points. Output is a polished HTML presentation and structured JSON data. You get a Telegram notification when each pitch is ready.

## Prerequisites

- Node.js 18+
- Claude Code installed and working
- Anthropic API key
- Telegram bot (create via @BotFather) with your chat ID
- Basic understanding of cold email and outbound sales

## Estimated Time

2-3 hours for the full build. Each pitch generates in 30-60 seconds.

## Environment Variables

Create a `.env` file in your project root:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

---

## Step 1: Project Setup

Tell Claude:

```
Create a Node.js project called prospect-pitch with this structure:

prospect-pitch/
  src/
    scrape/
      domain-extractor.js    # Extract domain from email or URL
      site-scraper.js        # Scrape up to 5 pages of a website
    analyze/
      claude-analyzer.js     # Send scraped content to Claude for analysis
      strategy-builder.js    # Structure Claude output into strategy format
    output/
      html-builder.js        # Generate HTML presentation
      json-exporter.js       # Export research.json and strategy.json
    notify/
      telegram.js            # Send Telegram notification on completion
    pitch.js                 # Main entry point: domain in -> pitch out
  templates/
    pitch.html               # HTML presentation template
    styles.css               # Dark theme + purple accent styles
  pitches/                   # Output directory: one folder per domain
  package.json

Install: @anthropic-ai/sdk node-fetch cheerio dotenv
```

---

## Step 2: Domain Extraction

Tell Claude:

```
Build src/scrape/domain-extractor.js:

Function: extractDomain(input)

Accepts:
- Email: "john@acmecorp.com" -> "acmecorp.com"
- Domain: "acmecorp.com" -> "acmecorp.com"
- URL: "https://www.acmecorp.com/about" -> "acmecorp.com"
- URL with subdomain: "https://app.acmecorp.com" -> "acmecorp.com"

Rules:
- Strip protocol (http/https)
- Strip www prefix
- Strip paths and query strings
- Strip port numbers
- Handle edge cases: trailing slashes, uppercase
- Return null if input is not a valid domain/email/URL

Also export:
- domainToSlug(domain): "acmecorp.com" -> "acmecorp-com"
- domainToCompanyName(domain): "acmecorp.com" -> "Acmecorp" (rough guess, used as fallback)
```

---

## Step 3: Website Scraper

Tell Claude:

```
Build src/scrape/site-scraper.js:

Function: scrapeWebsite(domain)

1. Build a list of target URLs to scrape (in order of priority):
   - https://{domain}/                    (homepage)
   - https://{domain}/about               (about page)
   - https://{domain}/services or /solutions or /products  (offerings)
   - https://{domain}/pricing             (pricing page)
   - https://{domain}/careers or /jobs    (hiring page)

2. For each URL, try to fetch with a 10-second timeout:
   - Use node-fetch with a browser-like User-Agent header
   - If the exact path 404s, try common variations:
     /about -> /about-us -> /company -> /who-we-are
     /services -> /solutions -> /products -> /what-we-do
     /pricing -> /plans -> /packages
     /careers -> /jobs -> /join-us -> /hiring
   - If HTTPS fails, try HTTP

3. For each successful page, extract using cheerio:
   - Page title
   - Meta description
   - All h1, h2, h3 headings
   - Main body text (strip nav, footer, scripts, styles)
   - Links to external sites (partners, integrations)
   - Any email addresses found on the page
   - Any phone numbers
   - Social media links
   - Schema.org structured data if present

4. Return a research object:
   {
     domain: "acmecorp.com",
     scraped_at: ISO timestamp,
     pages: [
       {
         url: "https://acmecorp.com/",
         title: "Acme Corp - ...",
         meta_description: "...",
         headings: ["h1 text", "h2 text", ...],
         body_text: "cleaned text content...",
         links: [...],
         emails: [...],
         phones: [...]
       },
       ...
     ],
     social_links: { linkedin: "...", twitter: "...", ... },
     technologies_detected: []  // check for common scripts: HubSpot, Salesforce, Intercom, etc.
   }

5. Save raw research to pitches/{domain-slug}/research.json
```

---

## Step 4: Claude Analysis Engine

Tell Claude:

```
Build src/analyze/claude-analyzer.js:

Function: analyzeProspect(research)

Send the scraped research to Claude (claude-sonnet-4-20250514) with this prompt:

"You are a B2B outbound strategist. Analyze this company's website data and produce a complete outbound strategy.

Company domain: {research.domain}
Website data:
{JSON.stringify(research.pages, null, 2)}

Technologies detected: {research.technologies_detected}
Social links: {research.social_links}

Produce a JSON response with this exact structure:

{
  company_overview: {
    name: 'Best guess at company name',
    industry: 'Their industry',
    company_size_estimate: 'Startup / SMB / Mid-Market / Enterprise',
    what_they_do: '2-3 sentence summary',
    target_market: 'Who they sell to'
  },
  icp_fit_score: {
    score: 7,           // 1-10 scale
    reasoning: 'Why this score',
    fit_signals: ['signal 1', 'signal 2'],
    risk_signals: ['risk 1']
  },
  audience_segments: [
    {
      title: 'Segment name (e.g., VP of Marketing)',
      role_titles: ['VP Marketing', 'Head of Marketing', 'CMO'],
      pain_points: ['pain 1', 'pain 2', 'pain 3'],
      pitch_angle: 'The specific angle to use when reaching this persona',
      trigger_events: ['What would make them buy now'],
      objections: ['Likely objection 1', 'Likely objection 2']
    }
    // 3 segments total
  ],
  intent_signals: {
    hiring: ['roles they are hiring for, from careers page'],
    expansion: ['signs of growth or expansion'],
    new_products: ['recently launched products or features'],
    pain_indicators: ['things on their site that suggest problems we can solve'],
    technology_gaps: ['tools they should be using but aren\'t']
  },
  cold_email_scripts: [
    {
      segment: 'Segment name',
      subject: 'Email subject line',
      body: 'Full email body, 70-90 words, personalized to this company',
      follow_up: 'Follow-up email body'
    }
    // One per segment
  ],
  call_talking_points: {
    opener: 'First 15 seconds of the call',
    discovery_questions: ['question 1', 'question 2', 'question 3'],
    value_props: ['prop 1', 'prop 2'],
    close: 'How to end the call with next steps'
  }
}

Rules:
- Every recommendation must be grounded in data from their actual website
- Cold emails must be 70-90 words, never start with 'I'
- Reference specific things from their site (product names, features, messaging)
- Pain points should be specific to their industry and company size
- Score ICP fit honestly -- don't inflate"

Parse the response. If JSON parsing fails, extract JSON from between ```json and ``` markers and retry.

Return the strategy object.
```

---

## Step 5: Strategy Builder

Tell Claude:

```
Build src/analyze/strategy-builder.js:

Function: buildStrategy(research, analysis)

Merges the raw research and Claude analysis into a final strategy object:

{
  meta: {
    domain: "acmecorp.com",
    generated_at: ISO timestamp,
    version: "1.0"
  },
  research: { ...research },
  strategy: { ...analysis },
  summary: {
    one_liner: "Acmecorp is a mid-market SaaS company selling to HR teams. Best angle: their hiring surge suggests growth pain.",
    recommended_segment: "The highest-scoring segment",
    recommended_email: "The email script for that segment",
    urgency: "high/medium/low based on intent signals"
  }
}

Save to pitches/{domain-slug}/strategy.json
```

---

## Step 6: HTML Presentation Builder

Tell Claude:

```
Build src/output/html-builder.js and templates/pitch.html:

The HTML presentation uses a dark theme with purple accent (#8B5CF6). It has 7 sections displayed as a single-page scrollable document.

SECTION 1 - COVER:
- Company name large
- Domain
- "Outbound Strategy" subtitle
- Generation date
- ICP fit score displayed as large number with color coding (red <4, yellow 4-6, green 7+)

SECTION 2 - COMPANY OVERVIEW:
- What they do
- Industry
- Size estimate
- Target market
- Key links (website, social)

SECTION 3 - AUDIENCE SEGMENTS:
- 3 cards, one per segment
- Each card: title, role titles as tags, pain points as bullet list, pitch angle highlighted
- Trigger events listed per segment

SECTION 4 - INTENT SIGNALS:
- Four columns: Hiring, Expansion, New Products, Pain Indicators
- Each with bullet points
- Color-coded severity/opportunity

SECTION 5 - COLD EMAIL SCRIPTS:
- One tab/card per segment
- Subject line displayed prominently
- Email body in a styled "email preview" container
- Follow-up email below
- Copy-to-clipboard button for each email

SECTION 6 - CALL TALKING POINTS:
- Opener script in a highlighted box
- Discovery questions as numbered list
- Value props
- Close script

SECTION 7 - RAW DATA:
- Collapsible sections showing research.json and strategy.json
- For transparency and further analysis

CSS (templates/styles.css):
- Background: #0F172A (dark navy)
- Card background: #1E293B
- Text: #F8FAFC
- Purple accent: #8B5CF6 for highlights, buttons, section dividers
- Font: Inter or system sans-serif
- Responsive: works on desktop and tablet
- Print-friendly: @media print styles that switch to light background

Generate the HTML by reading templates/pitch.html and replacing {{placeholders}} with strategy data.
Save to pitches/{domain-slug}/index.html

The presentation should look professional enough to share with a client or team.
```

---

## Step 7: Telegram Notification

Tell Claude:

```
Build src/notify/telegram.js:

Function: notifyPitchComplete(domain, strategy)

Send a Telegram message via Gerald bot:

POST https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage
Body: {
  chat_id: TELEGRAM_CHAT_ID,
  text: message,
  parse_mode: "Markdown"
}

Message format:
"*Pitch Ready: {domain}*

Score: {icp_fit_score}/10
Industry: {industry}
Size: {company_size_estimate}

Top segment: {recommended_segment}
Urgency: {urgency}

View: file://pitches/{domain-slug}/index.html"

If the Telegram API call fails, log the error but don't fail the pitch generation.
```

---

## Step 8: Main Entry Point

Tell Claude:

```
Build src/pitch.js -- the main CLI entry point.

Usage:
  node src/pitch.js acmecorp.com
  node src/pitch.js john@acmecorp.com
  node src/pitch.js https://www.acmecorp.com/about

Flow:
1. Extract domain from input
2. Create output directory: pitches/{domain-slug}/
3. Log: "Researching {domain}..."
4. Scrape website (5 pages)
5. Log: "Scraped {n} pages. Analyzing..."
6. Analyze with Claude
7. Build strategy object
8. Log: "Generating pitch presentation..."
9. Generate HTML presentation
10. Export strategy.json and research.json
11. Send Telegram notification
12. Log: "Done! Pitch saved to pitches/{domain-slug}/"
13. Log: "Open pitches/{domain-slug}/index.html to view"

Error handling:
- If domain is unreachable, exit with clear error: "Could not reach {domain}. Check the URL and try again."
- If only 1-2 pages scrape successfully, proceed with reduced data (still useful)
- If Claude analysis fails, retry once, then exit with error
- All errors logged to pitches/{domain-slug}/error.log
```

---

## Step 9: Batch Mode (Optional)

Tell Claude:

```
Add batch mode to src/pitch.js:

Usage: node src/pitch.js --batch domains.txt

Where domains.txt is a newline-separated list of domains or emails.

Process each sequentially with a 3-second delay between pitches to avoid rate limits.
Log progress: "[3/25] Pitching acmecorp.com..."
Skip domains that already have a pitches/{domain-slug}/ folder (use --force to regenerate).
Print summary at end: total pitched, total succeeded, total failed.
```

---

## Testing Steps

1. **Test domain extraction**: verify all input formats work -- email, bare domain, full URL, URL with path, URL with subdomain
2. **Test scraper**: scrape a known company website, verify research.json has meaningful content for at least 3 pages
3. **Test Claude analysis**: pass scraped data through the analyzer, verify the strategy JSON has all required fields and the analysis is specific (not generic)
4. **Test HTML output**: open the generated index.html in a browser, verify all 7 sections render correctly with real data
5. **Test Telegram**: verify notification arrives with correct domain, score, and summary
6. **Test full pipeline**: run `node src/pitch.js` against 3 different domains:
   - A SaaS company
   - A local service business
   - A consulting firm
   Verify each produces a unique, specific strategy (not cookie-cutter)
7. **Test error handling**: try an invalid domain, verify it exits cleanly with a useful error message

## You're Done When...

- `node src/pitch.js acmecorp.com` scrapes the website, analyzes it with Claude, generates a complete outbound strategy, saves it as a polished HTML presentation, and sends you a Telegram notification -- all in under 60 seconds
- The HTML presentation at `pitches/{domain-slug}/index.html` has 7 sections with dark theme and purple accent, and looks professional enough to show a client
- `pitches/{domain-slug}/strategy.json` contains structured data: ICP score, 3 audience segments, intent signals, cold email scripts, and call talking points
- `pitches/{domain-slug}/research.json` contains raw scraped data for transparency
- Every cold email script is 70-90 words, never starts with "I", and references specific details from the prospect's website
- The system handles errors gracefully: unreachable domains, partial scrapes, and API failures all produce clear error messages without crashing
