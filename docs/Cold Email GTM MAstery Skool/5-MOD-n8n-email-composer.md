# AI Email Composer -- n8n Workflow, $0.02/Email

## What You'll Build

A 12-node n8n workflow that receives a contact ID, fetches their research data from Supabase, generates a hyper-personalized cold email using AI, pushes it to SmartLead for sending, and logs everything. Total cost: ~$0.02 per email.

## Prerequisites

- n8n self-hosted or n8n Cloud account
- Supabase project with contacts and research_reports tables populated (see the Lead Research Pipeline guide)
- SmartLead account with API key and at least one active campaign
- OpenAI API key or Anthropic API key

## Estimated Time

30-45 minutes to build and test.

## Environment Variables

```
OPENAI_API_KEY=sk-... (or ANTHROPIC_API_KEY=sk-ant-...)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SMARTLEAD_API_KEY=your_smartlead_api_key
SMARTLEAD_CAMPAIGN_ID=your_campaign_id
```

---

## Step 0: Set Up External Services

### SmartLead API Setup

1. Log into SmartLead at https://app.smartlead.ai
2. Go to Settings > API > Generate API Key
3. Copy the API key
4. Create a campaign or use an existing one
5. Go to the campaign settings and copy the Campaign ID from the URL
6. In the campaign, make sure "Custom Script" is enabled -- this allows the API to push personalized email bodies per lead

SmartLead API base URL: `https://server.smartlead.ai/api/v1`

Key endpoints:
- `POST /campaigns/{campaign_id}/leads` -- add lead with custom email script
- `GET /campaigns/{campaign_id}/leads` -- list leads in campaign

### Supabase Additional Tables

Run this SQL to add the tables needed for this workflow (in addition to the tables from the Lead Research Pipeline):

```sql
-- Email templates table
CREATE TABLE email_templates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  template_type TEXT DEFAULT 'cold_outreach',
  subject_template TEXT,
  body_template TEXT,
  rules TEXT,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Activity log table
CREATE TABLE activity_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Add columns to contacts if not present
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS times_contacted INTEGER DEFAULT 0;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS smartlead_lead_id TEXT;

-- Index
CREATE INDEX idx_activity_log_contact_id ON activity_log(contact_id);
CREATE INDEX idx_activity_log_action ON activity_log(action);

-- Insert a default email template
INSERT INTO email_templates (name, template_type, subject_template, body_template, rules) VALUES (
  'Default Cold Outreach',
  'cold_outreach',
  'Use research to write a relevant subject line. Max 5 words. Lowercase. No clickbait.',
  'Write a cold email using the research and offer below. The email must feel like it was written by a human who actually researched this person.',
  'Under 100 words. No signatures or sign-offs. No "I hope this email finds you well." No "Best regards." End with a specific question. Use one concrete detail from research. First line must reference something specific about them or their company. Do not use the word "excited." Do not use exclamation marks. Do not use "just" or "wanted to." Sound like a peer, not a salesperson.'
);
```

### n8n Credentials

In n8n, go to Credentials and create:

1. **Supabase API**: URL + service role key
2. **OpenAI API** or **Anthropic API**: API key
3. **HTTP Header Auth** (for SmartLead): We'll pass the API key as a query parameter

---

## Step 1: Build the 12-Node Workflow

### Node 1 -- Webhook

- Type: Webhook
- HTTP Method: POST
- Path: `compose-email`
- Authentication: Header Auth
- Response Mode: "Respond to Webhook"

Expected payload:

```json
{
  "contact_id": "uuid-of-contact",
  "campaign_id": "optional-override-campaign-id",
  "offer": "We help B2B companies book 30+ meetings/month with AI-powered outbound.",
  "sender_name": "Alex",
  "sender_company": "Cenra"
}
```

### Node 2 -- Prepare Variables (Code Node)

```javascript
const input = $input.first().json;

if (!input.contact_id) {
  throw new Error('contact_id is required');
}

return [{
  json: {
    contact_id: input.contact_id,
    campaign_id: input.campaign_id || 'YOUR_DEFAULT_CAMPAIGN_ID',
    offer: input.offer || 'We help B2B companies book 30+ qualified meetings per month using AI-powered cold outbound.',
    sender_name: input.sender_name || 'Alex',
    sender_company: input.sender_company || 'Cenra',
    smartlead_api_key: 'YOUR_SMARTLEAD_API_KEY'
  }
}];
```

### Node 3 -- Fetch Lead (Supabase Node)

- Type: Supabase
- Operation: Get Many
- Table: contacts
- Filters: id equals `{{ $json.contact_id }}`
- Limit: 1

### Node 4 -- Fetch Research (Supabase Node)

- Type: Supabase
- Operation: Get Many
- Table: research_reports
- Filters: contact_id equals `{{ $json.contact_id }}`
- Sort: created_at DESC
- Limit: 1

### Node 5 -- Select Template (Code Node)

Combine the lead data, research, and offer into a single payload for the AI:

```javascript
const vars = $('Prepare Variables').first().json;
const lead = $('Fetch Lead').first().json;
const research = $('Fetch Research').first().json;

if (!lead.id) {
  throw new Error(`Contact not found: ${vars.contact_id}`);
}

const companyReport = research.company_report || {};
const personReport = research.person_report || {};

return [{
  json: {
    contact_id: lead.id,
    email: lead.email,
    first_name: lead.first_name,
    last_name: lead.last_name,
    full_name: lead.full_name,
    title: lead.title,
    company_name: lead.company_name,
    company_domain: lead.company_domain,
    lead_score: lead.lead_score,
    company_report: companyReport,
    person_report: personReport,
    offer: vars.offer,
    sender_name: vars.sender_name,
    sender_company: vars.sender_company,
    campaign_id: vars.campaign_id,
    smartlead_api_key: vars.smartlead_api_key
  }
}];
```

### Node 6 -- Personalize Email (OpenAI/Anthropic Node)

- Type: OpenAI Chat Completion or HTTP Request to Anthropic
- Model: gpt-4o or claude-3-5-sonnet
- Temperature: 0.7
- Max tokens: 500

System prompt:

```
You are an expert cold email copywriter. You write short, direct, personalized cold emails that get replies. You never sound like a salesperson. You sound like a smart peer who did their homework.

RULES (follow these exactly):
- Under 100 words total
- No signature, sign-off, or closing (no "Best," "Cheers," "Thanks," etc.)
- No "I hope this email finds you well" or any variation
- No exclamation marks
- Do not use the words "excited," "just," "wanted to," "reaching out," or "touching base"
- First line must reference something specific about the person or their company from the research
- Include one concrete detail from the research to prove you did homework
- End with a specific, easy-to-answer question
- Sound like a peer, not a salesperson
- Do not use bullet points or numbered lists
- Write in a conversational, lowercase-friendly tone
```

User prompt:

```
Write a cold email for this prospect:

Name: {{ $json.first_name }} {{ $json.last_name }}
Title: {{ $json.title }}
Company: {{ $json.company_name }}
Lead Score: {{ $json.lead_score }}/100

Company Research:
{{ JSON.stringify($json.company_report) }}

Person Research:
{{ JSON.stringify($json.person_report) }}

Our Offer: {{ $json.offer }}
Sender: {{ $json.sender_name }} at {{ $json.sender_company }}

Return your response in this exact format:
SUBJECT: <subject line here>
BODY: <email body here>
```

### Node 7 -- Extract Email (Code Node)

Parse the AI output into subject and body:

```javascript
const aiOutput = $input.first().json.message?.content || $input.first().json.text || '';

const subjectMatch = aiOutput.match(/SUBJECT:\s*(.*?)(?:\n|$)/i);
const bodyMatch = aiOutput.match(/BODY:\s*([\s\S]*?)$/i);

if (!subjectMatch || !bodyMatch) {
  throw new Error('Failed to parse AI output. Expected SUBJECT: and BODY: format.');
}

const subject = subjectMatch[1].trim();
const body = bodyMatch[1].trim();

// Validation
if (body.split(/\s+/).length > 120) {
  throw new Error(`Email too long: ${body.split(/\s+/).length} words. Must be under 100.`);
}

const previous = $('Select Template').first().json;

return [{
  json: {
    ...previous,
    subject,
    body,
    word_count: body.split(/\s+/).length
  }
}];
```

### Node 8 -- Push to SmartLead (HTTP Request Node)

- Type: HTTP Request
- Method: POST
- URL: `https://server.smartlead.ai/api/v1/campaigns/{{ $json.campaign_id }}/leads`
- Query Parameters:
  - `api_key`: `{{ $json.smartlead_api_key }}`
- Body (JSON):

```json
{
  "lead_list": [
    {
      "email": "{{ $json.email }}",
      "first_name": "{{ $json.first_name }}",
      "last_name": "{{ $json.last_name }}",
      "company_name": "{{ $json.company_name }}",
      "custom_fields": {
        "title": "{{ $json.title }}",
        "lead_score": "{{ $json.lead_score }}"
      },
      "custom_script": {
        "subject": "{{ $json.subject }}",
        "email_body": "{{ $json.body }}"
      }
    }
  ],
  "settings": {
    "ignore_global_block_list": false,
    "ignore_unsubscribe_list": false
  }
}
```

### Node 9 -- Update Contact (Supabase Node)

- Type: Supabase
- Operation: Update
- Table: contacts
- Filter: id equals `{{ $json.contact_id }}`
- Fields:
  - status: "contacted"
  - times_contacted: `{{ $json.times_contacted + 1 }}` (or use a Code node to increment)
  - last_contacted_at: `{{ $now.toISO() }}`
  - smartlead_lead_id: from SmartLead response

### Node 10 -- Log Activity (Supabase Node)

- Type: Supabase
- Operation: Insert
- Table: activity_log
- Fields:

```json
{
  "contact_id": "{{ $json.contact_id }}",
  "action": "email_composed",
  "details": {
    "subject": "{{ $json.subject }}",
    "body": "{{ $json.body }}",
    "word_count": "{{ $json.word_count }}",
    "campaign_id": "{{ $json.campaign_id }}",
    "ai_model": "gpt-4o",
    "cost_estimate": 0.02
  }
}
```

### Node 11 -- Success Response (Respond to Webhook Node)

- Status Code: 200
- Body:

```json
{
  "success": true,
  "contact_id": "{{ $json.contact_id }}",
  "subject": "{{ $json.subject }}",
  "word_count": "{{ $json.word_count }}",
  "message": "Email composed and pushed to SmartLead"
}
```

### Node 12 -- Error Response (Respond to Webhook Node)

Connect this to the Error output of any node that might fail. Use an Error Trigger node or catch errors with IF nodes.

- Status Code: 400
- Body:

```json
{
  "success": false,
  "error": "{{ $json.error.message }}",
  "contact_id": "{{ $json.contact_id }}"
}
```

---

## Integration Patterns

### Pattern 1: Sequential (Research then Compose)

Chain the Lead Research Pipeline directly into this workflow:

1. Lead Research webhook finishes
2. Add an HTTP Request node at the end that calls the Compose Email webhook
3. End-to-end: raw lead data in, researched and emailed out

### Pattern 2: Database Trigger

1. In Supabase, create a function trigger on the `scores` table
2. When a new score is inserted AND total_score >= 60, fire a webhook to compose-email
3. Only high-quality leads get emails automatically

### Pattern 3: Batch Job

1. Create a separate n8n workflow with a Schedule Trigger (e.g., daily at 9am)
2. Query Supabase: contacts WHERE status = 'researched' AND lead_score >= 50 LIMIT 20
3. Loop over each contact and call the compose-email webhook
4. Wait 3 seconds between calls

---

## Cost Breakdown

| Component | Cost per Email |
|---|---|
| AI Generation (1 call, ~800 tokens) | $0.015 |
| Supabase (3 reads + 2 writes) | ~$0.00 |
| SmartLead API | $0.00 (included in subscription) |
| **Total** | **~$0.02** |

At 1000 emails/month: ~$20/month for AI generation.

---

## Testing and Verification

1. **Populate test data**: Make sure you have at least one contact in Supabase with a research_report. If you built the Lead Research Pipeline, use a contact from there.

2. **Test the webhook**:

```bash
curl -X POST https://your-n8n-instance.com/webhook/compose-email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-token" \
  -d '{
    "contact_id": "your-contact-uuid",
    "offer": "We help B2B companies book 30+ meetings/month with AI-powered outbound.",
    "sender_name": "Alex",
    "sender_company": "Cenra"
  }'
```

3. **Verify email quality**: Read the returned subject and body. Check:
   - Under 100 words
   - No signature or sign-off
   - Ends with a question
   - References something specific from their research
   - Sounds human, not robotic

4. **Check SmartLead**: Log into SmartLead and verify the lead was added to the campaign with the custom script.

5. **Check Supabase**: Verify the contact status is "contacted", times_contacted incremented, and activity_log has a new row.

6. **Test error handling**: Send a request with a non-existent contact_id. Verify you get a 400 error.

7. **Test without SmartLead** (optional): Comment out the SmartLead node and test the email generation in isolation first.

---

## You're Done When

- You can POST a contact_id and get back a personalized email within 10 seconds
- The email follows all cold email rules (under 100 words, no signature, ends with question, uses research)
- The email is pushed to SmartLead with the correct custom script
- The contact record shows status = "contacted" and times_contacted is incremented
- The activity_log has a row for the compose action
- Errors return a 400 with a clear message
- You've composed and pushed at least 3 real emails end-to-end
