# The Lead Gen Agent — Automated Prospecting That Runs 24/7

## What You'll Build

A fully automated lead generation pipeline that scrapes prospects, researches their companies, scores them against your ideal customer profile, writes personalized cold emails, and sends them — every day, without you touching it. 20-30 personalized messages per day, targeting a 15-25% response rate.

## Prerequisites

- n8n cloud account (or self-hosted)
- Anthropic API key (Claude)
- Apify account (web scraping) or Apollo account (lead data)
- Perplexity API key (company research) or Google Custom Search Engine
- SmartLead or Instantly account (email sending)
- Supabase account (database and logging)
- At least one warmed-up email account

## Estimated Time

3-4 hours for the full pipeline. 1-2 hours if you skip the research step and use pre-enriched data.

---

## Pipeline Overview

```
Scrape (Apify/Apollo)
  → Research (Perplexity/Google CSE)
    → Score (Claude, 1-10 ICP fit)
      → Write (Claude, unique personalized email)
        → Send (SmartLead/Instantly)
          → Log (Supabase)
```

Each step feeds into the next. The pipeline runs daily at 7am. You wake up to a Telegram notification telling you how many emails were sent.

---

## Full Build Instructions

### Step 1: Set Up Supabase Tables

Create these tables in your Supabase project:

**prospects**
```sql
CREATE TABLE prospects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  title TEXT,
  company TEXT,
  company_domain TEXT,
  linkedin_url TEXT,
  source TEXT,
  status TEXT DEFAULT 'new',
  icp_score INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**research_cache**
```sql
CREATE TABLE research_cache (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  domain TEXT UNIQUE NOT NULL,
  company_summary TEXT,
  recent_news TEXT,
  tech_stack TEXT,
  headcount TEXT,
  funding TEXT,
  pain_points TEXT,
  researched_at TIMESTAMPTZ DEFAULT NOW()
);
```

**outreach_log**
```sql
CREATE TABLE outreach_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  prospect_id UUID REFERENCES prospects(id),
  email_to TEXT NOT NULL,
  email_body TEXT NOT NULL,
  campaign_id TEXT,
  smartlead_id TEXT,
  status TEXT DEFAULT 'sent',
  sent_at TIMESTAMPTZ DEFAULT NOW()
);
```

**campaign_config**
```sql
CREATE TABLE campaign_config (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  client_id TEXT UNIQUE NOT NULL,
  client_name TEXT,
  icp_description TEXT,
  email_template TEXT,
  smartlead_campaign_id TEXT,
  min_score INTEGER DEFAULT 7,
  daily_limit INTEGER DEFAULT 30,
  active BOOLEAN DEFAULT true
);
```

### Step 2: Build the n8n Workflow

Create a new workflow called "Lead Gen Pipeline."

**Node 1: Schedule Trigger**
- Type: Schedule Trigger
- Time: Every day at 7:00 AM (your timezone)

**Node 2: Fetch Campaign Config**
- Type: Supabase
- Operation: Get Many
- Table: campaign_config
- Filter: active = true

**Node 3: Loop Through Campaigns**
- Type: Loop Over Items (Split In Batches)
- Batch Size: 1

**Node 4: Fetch Prospects**
- Type: Supabase
- Operation: Get Many
- Table: prospects
- Filter: status = 'new'
- Limit: `{{ $json.daily_limit }}`

**Node 5: Loop Through Prospects**
- Type: Loop Over Items (Split In Batches)
- Batch Size: 1

**Node 6: Check Deduplication**
- Type: Supabase
- Operation: Get Many
- Table: outreach_log
- Filter: email_to = `{{ $json.email }}`
- If results > 0, skip this prospect

**Node 7: Research Company**
- Type: HTTP Request
- URL: `https://api.perplexity.ai/chat/completions`
- Method: POST
- Headers: Authorization: Bearer `{{ $env.PERPLEXITY_API_KEY }}`
- Body:
```json
{
  "model": "sonar",
  "messages": [
    {
      "role": "user",
      "content": "Give me a brief summary of the company at {{$json.company_domain}}. Include: what they do, approximate size, recent news or changes, and their likely tech stack. Keep it under 200 words."
    }
  ]
}
```

**Node 8: Cache Research**
- Type: Supabase
- Operation: Upsert
- Table: research_cache
- Data: domain, company_summary, researched_at

**Node 9: Score Prospect (AI Agent)**
- Type: AI Agent or HTTP Request to Claude API
- System prompt:

```
You are an ICP scoring engine. Score this prospect on a scale of 1-10 based on how well they match the ideal customer profile.

ICP CRITERIA:
{{ $('Fetch Campaign Config').item.json.icp_description }}

SCORING RUBRIC:
- Company Fit (0-3 points): Industry match, company size, location
- Decision Maker (0-3 points): Title level (C-suite=3, VP=2, Director=1, Manager=0), relevant department
- Pain Point Match (0-2 points): Tech stack gaps, hiring signals suggesting growth/pain
- Timing (0-2 points): Recent funding, new leadership, expansion, or other buying signals

PROSPECT:
Name: {{ $json.first_name }} {{ $json.last_name }}
Title: {{ $json.title }}
Company: {{ $json.company }}

COMPANY RESEARCH:
{{ $('Research Company').item.json.choices[0].message.content }}

Respond with ONLY a JSON object:
{"score": 7, "reasoning": "one sentence explanation"}
```

**Node 10: Check Score**
- Type: IF
- Condition: score >= `{{ $('Fetch Campaign Config').item.json.min_score }}`
- True: continue to email generation
- False: update prospect status to "low_score" and skip

**Node 11: Generate Email (AI Agent)**
- Type: AI Agent or HTTP Request to Claude API
- System prompt:

```
You are a cold email writer. Write a unique, personalized email for this prospect.

RULES:
- Maximum 85 words
- No generic compliments ("I love what you're doing")
- No buzzwords ("synergy," "leverage," "unlock," "revolutionize")
- No signatures or sign-offs
- Reference something specific about their company or situation
- First line must be about them, not about you
- End with a low-friction question (not "Let's book a call")
- Every email must be unique — never repeat the same angle

PROSPECT:
Name: {{ $json.first_name }}
Title: {{ $json.title }}
Company: {{ $json.company }}

COMPANY RESEARCH:
{{ $('Research Company').item.json.choices[0].message.content }}

ICP SCORE REASONING:
{{ $('Score Prospect').item.json.reasoning }}

Output ONLY the email body. No subject line. No signature.
```

**Node 12: Push to SmartLead**
- Type: HTTP Request
- URL: `https://server.smartlead.ai/api/v1/campaigns/{{ campaign_id }}/leads`
- Method: POST
- Headers: Authorization: Bearer `{{ $env.SMARTLEAD_API_KEY }}`
- Body:
```json
{
  "lead_list": [
    {
      "email": "{{ $json.email }}",
      "first_name": "{{ $json.first_name }}",
      "last_name": "{{ $json.last_name }}",
      "company_name": "{{ $json.company }}",
      "custom_script": "{{ $('Generate Email').item.json.output }}"
    }
  ]
}
```

**Node 13: Log to Supabase**
- Type: Supabase
- Operation: Insert
- Table: outreach_log
- Data: prospect_id, email_to, email_body, campaign_id, status

**Node 14: Update Prospect Status**
- Type: Supabase
- Operation: Update
- Table: prospects
- Set: status = 'sent'
- Filter: id = prospect_id

**Node 15: Send Summary (After all loops complete)**
- Type: HTTP Request (Telegram API)
- URL: `https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendMessage`
- Body:
```json
{
  "chat_id": "{{ $env.TELEGRAM_CHAT_ID }}",
  "text": "Pipeline complete.\nProcessed: {{ $json.total_processed }}\nSent: {{ $json.total_sent }}\nSkipped (low score): {{ $json.total_skipped }}\nErrors: {{ $json.total_errors }}"
}
```

### Step 3: ICP Scoring Criteria

Your ICP description in the campaign_config table should include:

**Company Fit (0-3 points)**
- Target industries (SaaS, fintech, healthcare, etc.)
- Company size (10-50, 50-200, 200-1000 employees)
- Revenue range if known
- Location (US, EU, specific countries)

**Decision Maker (0-3 points)**
- Target titles (CEO, VP Sales, Head of Growth, etc.)
- Department (Sales, Marketing, Operations)
- Seniority level (C-suite = 3, VP = 2, Director = 1)
- Tenure (new in role = higher timing score)

**Pain Point Match (0-2 points)**
- Tech stack gaps (no CRM, outdated tools, manual processes)
- Hiring signals (posting for roles your product replaces)
- Competitor usage (using a tool you replace)

**Timing (0-2 points)**
- Recent funding round
- New leadership (new VP Sales, new CTO)
- Company expansion (new office, new market)
- Layoffs (cost-cutting = open to efficiency tools)

### Step 4: Personalization Rules

Every email must reference something specific. Generic benefits don't work. Follow these rules:

- **Reference their situation, not your product.** "Saw you just opened a London office" beats "We help companies expand internationally."
- **One insight per email.** Don't cram three personalization points into 85 words.
- **Match the angle to the pain point.** If they're hiring SDRs, talk about SDR efficiency. If they just raised, talk about scaling.
- **Each email must be unique.** Never reuse the same opening line or angle for different prospects.

### Step 5: Follow-Up Automation

Set up follow-up sequences in SmartLead:

**Follow-up 1 (3 days after initial email):**
- Add value, don't ask again
- Share a relevant insight, case study, or data point
- No "just checking in" or "bumping this to the top"

**Follow-up 2 (7 days after follow-up 1):**
- Different angle entirely
- If the first email was about their problem, the second is about a result you achieved for someone similar
- Still short, still specific

**Follow-up 3 (7 days after follow-up 2):**
- Breakup email — give them an easy out
- "If this isn't a priority right now, no worries. But if [pain point] is still on your plate, worth a quick look at [one-liner value prop]."

### Step 6: SmartLead Setup

1. Create a campaign in SmartLead
2. Add your warmed-up email accounts (minimum 2 weeks of warmup)
3. Set sending limits: 30-50 emails per account per day
4. Enable warmup alongside live sending
5. In the campaign sequence, use the `{{custom_script}}` variable for the AI-generated email body
6. Set timezone to match your prospects
7. Enable open and click tracking

---

## Step-by-Step Plan

1. Create Supabase tables (prospects, research_cache, outreach_log, campaign_config)
2. Insert your first campaign config with ICP description
3. Load prospects into the prospects table (from Apollo export, CSV, or Apify scrape)
4. Build the n8n workflow node by node
5. Test research step with one prospect
6. Test scoring step — verify scores match your expectations
7. Test email generation — verify personalization quality
8. Test SmartLead push — verify lead appears in campaign
9. Run full pipeline with 5 prospects
10. Review all 5 emails for quality
11. Activate the schedule trigger
12. Monitor for 3 days, adjust scoring and email prompts

---

## Expected Results

- **Volume**: 20-30 personalized messages per day per campaign
- **Quality**: each email references specific company details
- **Response rate**: 15-25% for well-targeted, personalized outreach
- **Time saved**: 3-4 hours per day of manual prospecting replaced
- **Scale**: add new campaigns by inserting rows into campaign_config

---

## Environment Variables

```
APIFY_API_KEY=apify_api_...           # Web scraping (prospect sourcing)
ANTHROPIC_API_KEY=sk-ant-...          # Claude API (scoring + email writing)
SMARTLEAD_API_KEY=sl_...              # Email sending platform
SUPABASE_URL=https://xxx.supabase.co  # Database
SUPABASE_KEY=eyJ...                   # Supabase service role key
PERPLEXITY_API_KEY=pplx-...           # Company research
TELEGRAM_BOT_TOKEN=123456:ABC...      # Completion notifications
TELEGRAM_CHAT_ID=5915551069           # Your Telegram chat ID
```

---

## Testing Steps

1. Insert 5 test prospects into Supabase — verify they appear with status "new"
2. Trigger the workflow manually — verify research step returns company data
3. Check research_cache table — verify research is cached
4. Check scoring output — verify scores are 1-10 with reasoning
5. Check generated emails — verify each is unique and references specific company details
6. Check SmartLead — verify leads appeared in the campaign with custom scripts
7. Check outreach_log — verify all sends are logged
8. Check prospect status — all processed prospects should be "sent" or "low_score"
9. Run the pipeline again — verify it skips already-sent prospects (deduplication)
10. Check Telegram — verify summary notification arrived

---

## Success Criteria

- Pipeline runs daily at 7am without manual intervention
- Each prospect is researched before scoring
- ICP scoring correctly filters out low-fit prospects (below threshold)
- Every email is unique and references specific company details
- Emails are pushed to SmartLead with custom scripts
- All activity is logged to Supabase
- Deduplication prevents sending to the same prospect twice
- Telegram notification arrives with daily summary
- 15-25% response rate after 2 weeks of sending
