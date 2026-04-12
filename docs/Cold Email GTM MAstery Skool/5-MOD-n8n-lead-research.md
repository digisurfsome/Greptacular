# AI Lead Research Pipeline -- n8n Workflow, $0.10/Lead

## What You'll Build

A 4-stage n8n workflow that takes a lead's basic info (name, email, company, title), runs automated company and person research via Google Custom Search, scores the lead with AI, and stores everything in Supabase. Total cost: ~$0.10 per lead. Execution time: 60-90 seconds per lead.

## Prerequisites

- n8n self-hosted or n8n Cloud account
- Google Cloud account (for Custom Search Engine API)
- OpenAI API key or Anthropic API key
- Supabase project (free tier works)
- Basic familiarity with n8n node configuration

## Estimated Time

45-60 minutes to build and test end-to-end.

## Environment Variables

```
GOOGLE_CSE_API_KEY=your_google_api_key
GOOGLE_CSE_ENGINE_ID=your_search_engine_id
OPENAI_API_KEY=sk-... (or ANTHROPIC_API_KEY=sk-ant-...)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

---

## Step 0: Set Up External Services

### Google Custom Search Engine

1. Go to https://programmablesearchengine.google.com/controlpanel/all
2. Click "Add" to create a new search engine
3. Under "What to search" select "Search the entire web"
4. Name it "Lead Research Engine"
5. Click "Create" and copy the Search Engine ID (cx parameter)
6. Go to https://console.cloud.google.com/apis/library/customsearch.googleapis.com
7. Enable the "Custom Search API"
8. Go to Credentials > Create Credentials > API Key
9. Copy the API key
10. Optional: Restrict the key to Custom Search API only

Cost: 100 free queries/day. After that, $5 per 1000 queries. Each lead uses ~10 queries = ~$0.03/lead for search.

### Supabase Tables

Run this SQL in the Supabase SQL Editor:

```sql
-- Contacts table
CREATE TABLE contacts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  full_name TEXT,
  title TEXT,
  company_name TEXT,
  company_domain TEXT,
  phone TEXT,
  linkedin_url TEXT,
  status TEXT DEFAULT 'new',
  lead_score INTEGER,
  score_breakdown JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Research reports table
CREATE TABLE research_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  report_type TEXT NOT NULL CHECK (report_type IN ('company', 'person', 'combined')),
  company_report JSONB,
  person_report JSONB,
  raw_search_results JSONB,
  ai_model TEXT,
  tokens_used INTEGER,
  cost_estimate NUMERIC(10,4),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Scores table
CREATE TABLE scores (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  total_score INTEGER NOT NULL,
  company_fit INTEGER,
  decision_maker INTEGER,
  pain_point INTEGER,
  engagement INTEGER,
  timing INTEGER,
  reasoning TEXT,
  scored_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_status ON contacts(status);
CREATE INDEX idx_contacts_lead_score ON contacts(lead_score DESC);
CREATE INDEX idx_research_reports_contact_id ON research_reports(contact_id);
CREATE INDEX idx_scores_contact_id ON scores(contact_id);
```

### n8n Credentials

In n8n, go to Credentials and create:

1. **HTTP Header Auth** (for Google CSE): Header Name = `X-Custom`, Value = not needed (we'll pass API key as query param)
2. **OpenAI API** or **Anthropic API**: Paste your API key
3. **Supabase API**: Enter your Supabase URL and service role key

---

## Step 1: Build the n8n Workflow

Create a new workflow in n8n. You will add nodes in this exact order.

### Stage 1: Intake and Validation

#### Node 1 -- Webhook (Trigger)

- Type: Webhook
- HTTP Method: POST
- Path: `lead-research`
- Authentication: Header Auth (set a secret token)
- Response Mode: "Respond to Webhook" (we'll send response at the end)

Expected payload:

```json
{
  "email": "john@acme.com",
  "first_name": "John",
  "last_name": "Smith",
  "company": "Acme Corp",
  "title": "VP of Sales",
  "domain": "acme.com"
}
```

#### Node 2 -- Validate and Normalize (Code Node)

- Type: Code
- Language: JavaScript

```javascript
const input = $input.first().json;

// Validate required fields
const required = ['email', 'first_name', 'last_name', 'company'];
const missing = required.filter(f => !input[f] || input[f].trim() === '');

if (missing.length > 0) {
  throw new Error(`Missing required fields: ${missing.join(', ')}`);
}

// Normalize
const email = input.email.toLowerCase().trim();
const domain = input.domain || email.split('@')[1];
const firstName = input.first_name.trim();
const lastName = input.last_name.trim();
const fullName = `${firstName} ${lastName}`;
const company = input.company.trim();
const title = (input.title || '').trim();

return [{
  json: {
    email,
    domain,
    first_name: firstName,
    last_name: lastName,
    full_name: fullName,
    company,
    title,
    research_started_at: new Date().toISOString()
  }
}];
```

#### Node 3 -- Check for Duplicate (Supabase Node)

- Type: Supabase
- Operation: Get Many
- Table: contacts
- Filters: email equals `{{ $json.email }}`
- Limit: 1

#### Node 4 -- IF Duplicate (IF Node)

- Condition: `{{ $json.id }}` exists
- True path: Update existing contact and continue
- False path: Insert new contact and continue

#### Node 5 -- Upsert Contact (Supabase Node)

- Type: Supabase
- Operation: Upsert
- Table: contacts
- Conflict Column: email
- Fields: email, first_name, last_name, full_name, title, company_name, company_domain, status = "researching"

Save the returned `id` -- you need it for all subsequent nodes.

### Stage 2: Company Research

#### Node 6 -- Company Search Queries (Code Node)

Generate 6 Google CSE search queries:

```javascript
const lead = $input.first().json;
const company = lead.company_name || lead.company;
const domain = lead.company_domain || lead.domain;

const queries = [
  `"${company}" company overview about`,
  `site:linkedin.com/company "${company}"`,
  `site:crunchbase.com "${company}"`,
  `"${company}" news ${new Date().getFullYear()}`,
  `"${domain}" technology stack built with`,
  `"${company}" hiring jobs open positions`
];

return queries.map((query, index) => ({
  json: {
    query,
    query_type: ['overview', 'linkedin', 'crunchbase', 'news', 'tech_stack', 'hiring'][index],
    contact_id: lead.id,
    company,
    domain
  }
}));
```

#### Node 7 -- Google CSE HTTP Request (HTTP Request Node, in loop)

- Type: HTTP Request
- Method: GET
- URL: `https://www.googleapis.com/customsearch/v1`
- Query Parameters:
  - `key`: `{{ $credentials.google_cse_api_key }}` (or hardcode from env)
  - `cx`: your Search Engine ID
  - `q`: `{{ $json.query }}`
  - `num`: 5
- Add a Wait node before this set to 200ms to avoid rate limiting

#### Node 8 -- Merge Company Results (Merge Node)

Merge all 6 search results back into a single item.

#### Node 9 -- AI Company Analysis (OpenAI/Anthropic Node)

- Type: OpenAI (Chat Completion) or HTTP Request to Anthropic
- Model: gpt-4o or claude-3-5-haiku
- Temperature: 0.2

System prompt:

```
You are a B2B sales research analyst. Given raw Google search results about a company, produce a structured company research report. Be factual -- only include information supported by the search results.
```

User prompt:

```
Analyze these search results for {{ $json.company }} ({{ $json.domain }}).

Search Results:
{{ JSON.stringify($json.search_results, null, 2) }}

Return a JSON object with these fields:
{
  "company_summary": "2-3 sentence overview",
  "industry": "primary industry",
  "estimated_size": "employee count range",
  "funding_stage": "bootstrapped/seed/series_a/etc or unknown",
  "recent_news": ["array of recent developments"],
  "tech_stack": ["known technologies"],
  "hiring_signals": ["open roles or hiring patterns"],
  "pain_points": ["likely business challenges based on research"],
  "linkedin_url": "company linkedin URL if found",
  "crunchbase_url": "crunchbase URL if found"
}
```

### Stage 3: Person Research

#### Node 10 -- Person Search Queries (Code Node)

```javascript
const lead = $input.first().json;
const name = lead.full_name;
const company = lead.company_name || lead.company;

const queries = [
  `"${name}" "${company}" background`,
  `site:linkedin.com/in "${name}" "${company}"`,
  `"${name}" speaker conference presentation`,
  `"${name}" article blog post author`
];

return queries.map((query, index) => ({
  json: {
    query,
    query_type: ['background', 'linkedin', 'speaking', 'content'][index],
    contact_id: lead.contact_id,
    full_name: name,
    company
  }
}));
```

#### Node 11 -- Google CSE for Person (HTTP Request Node, in loop)

Same configuration as Node 7 but looping over person queries.

#### Node 12 -- Merge Person Results (Merge Node)

#### Node 13 -- AI Person Analysis (OpenAI/Anthropic Node)

System prompt:

```
You are a B2B sales research analyst. Given raw Google search results about a person, produce a structured person brief. Only include information supported by search results.
```

User prompt:

```
Analyze these search results for {{ $json.full_name }} at {{ $json.company }}.

Search Results:
{{ JSON.stringify($json.search_results, null, 2) }}

Return a JSON object:
{
  "person_summary": "2-3 sentence bio",
  "current_role": "title and responsibilities",
  "career_history": "brief background",
  "linkedin_url": "LinkedIn profile URL if found",
  "content_published": ["articles, posts, talks"],
  "interests": ["professional interests"],
  "communication_style": "formal/casual/technical/etc based on their content",
  "talking_points": ["3 personalized conversation starters based on research"]
}
```

### Stage 4: Scoring and Storage

#### Node 14 -- AI Lead Scoring (OpenAI/Anthropic Node)

System prompt:

```
You are a B2B lead scoring engine. Score this lead on a 100-point scale using the rubric below. Be strict -- only give high scores when there is clear evidence.

Scoring Rubric:
- Company Fit (0-30): Does the company match the ICP? Right size, industry, growth stage?
- Decision Maker (0-20): Is this person a decision maker or influencer for the relevant purchase?
- Pain Point Alignment (0-25): Does the research reveal pain points that align with B2B outbound services?
- Engagement Signals (0-15): Has this person published content, spoken at events, or shown engagement in relevant topics?
- Timing (0-10): Are there hiring signals, funding events, or other indicators of good timing?
```

User prompt:

```
Score this lead:

Company Research:
{{ JSON.stringify($json.company_report) }}

Person Research:
{{ JSON.stringify($json.person_report) }}

Return JSON:
{
  "total_score": 0-100,
  "company_fit": 0-30,
  "decision_maker": 0-20,
  "pain_point": 0-25,
  "engagement": 0-15,
  "timing": 0-10,
  "reasoning": "2-3 sentence explanation of the score"
}
```

#### Node 15 -- Save Research Report (Supabase Node)

- Table: research_reports
- Operation: Insert
- Fields:
  - contact_id: from the upserted contact
  - report_type: "combined"
  - company_report: AI company analysis JSON
  - person_report: AI person analysis JSON
  - raw_search_results: merged raw results
  - ai_model: "gpt-4o" or "claude-3-5-haiku"
  - cost_estimate: 0.10

#### Node 16 -- Save Score (Supabase Node)

- Table: scores
- Operation: Insert
- Fields: contact_id, total_score, company_fit, decision_maker, pain_point, engagement, timing, reasoning

#### Node 17 -- Update Contact Score (Supabase Node)

- Table: contacts
- Operation: Update
- Filter: id equals contact_id
- Fields: lead_score = total_score, score_breakdown = score JSON, status = "researched", updated_at = now()

#### Node 18 -- Respond to Webhook (Respond to Webhook Node)

```json
{
  "success": true,
  "contact_id": "{{ $json.contact_id }}",
  "lead_score": "{{ $json.total_score }}",
  "message": "Research complete"
}
```

---

## Three Trigger Methods

### Method 1: HTTP Webhook (Real-Time)

The workflow above already uses this. Call it with:

```bash
curl -X POST https://your-n8n-instance.com/webhook/lead-research \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-token" \
  -d '{
    "email": "john@acme.com",
    "first_name": "John",
    "last_name": "Smith",
    "company": "Acme Corp",
    "title": "VP of Sales",
    "domain": "acme.com"
  }'
```

### Method 2: Batch Script

Create a separate n8n workflow:

1. Schedule Trigger (e.g., every hour)
2. Supabase node: Get contacts WHERE status = 'new' LIMIT 10
3. Loop over each contact
4. HTTP Request to the webhook above for each lead
5. Wait 5 seconds between calls to respect rate limits

### Method 3: Supabase Database Trigger

1. In Supabase, create a database webhook on INSERT to the contacts table
2. Point it to your n8n webhook URL
3. Every new contact inserted automatically triggers research

---

## Cost Breakdown

| Component | Cost per Lead |
|---|---|
| Google CSE (10 queries) | $0.03 |
| AI Analysis (3 calls, ~2000 tokens each) | $0.06 |
| Supabase (3 writes) | ~$0.00 |
| **Total** | **~$0.10** |

At 1000 leads/month: ~$100/month total cost.

---

## Testing and Verification

1. **Test the webhook manually**: Send a curl request with test data. Verify you get a 200 response with a contact_id and lead_score.

2. **Check Supabase tables**: After the test, verify rows exist in all three tables (contacts, research_reports, scores).

3. **Validate research quality**: Read the company_report and person_report in research_reports. They should contain real, accurate information about the company.

4. **Test error handling**: Send a request with missing fields. Verify you get a clear error message.

5. **Test duplicate handling**: Send the same email twice. Verify the contact is updated (not duplicated) and a new research report is created.

6. **Check rate limits**: Run 5 leads in sequence. Verify Google CSE doesn't return 429 errors.

---

## You're Done When

- You can POST a lead to the webhook and get back a score within 90 seconds
- The contacts table has a row with lead_score populated
- The research_reports table has a combined report with real company and person data
- The scores table has a breakdown across all 5 scoring dimensions
- Duplicate emails update the existing contact instead of creating a new row
- Error payloads return a 400 with a clear message
- You've successfully researched at least 3 real leads end-to-end
