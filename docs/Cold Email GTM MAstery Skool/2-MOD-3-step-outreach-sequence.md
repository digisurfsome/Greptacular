# The 3-Step Outreach Sequence — 40-50% Open Rates, 5-8% Reply Rates

> **Type:** Build guide / Claude Code instruction file
> **Description:** A complete 3-email cold outreach sequence with full email copy templates, SmartLead setup, 13 merge field variables, subject line variants, hot lead signal tracking, and Supabase lead status progression.
> **What you'll build:** A campaign-ready 3-step email sequence deployed in SmartLead with Supabase tracking and revenue projection logic.
> **Prerequisites:** Node.js 18+, SmartLead account, Supabase project, a warm sending domain.
> **Estimated time:** 2-3 hours for full build, sequence setup, and first campaign launch.

---

## Instructions for Claude

You are building a 3-step cold email outreach sequence. Every email must follow the cold email rules (under 100 words, no signature, no Subject line in body, ends with a question, never starts with "I"). Build the sequence templates, SmartLead integration, and Supabase tracking. Follow this spec exactly.

---

## Environment Variables

```
SMARTLEAD_API_KEY=your_smartlead_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

---

## The 13 Merge Field Variables

Every contact in your system should have these populated before the sequence starts:

| Variable | Description | Example |
|---|---|---|
| `company_name` | Prospect's company | "Apex Roofing" |
| `first_name` | Contact first name | "Mike" |
| `star_rating` | Google/Yelp star rating | "4.2" |
| `review_count` | Total review count | "87" |
| `site_url` | Their website URL | "apexroofing.com" |
| `specific_review_author` | Name from a real review | "Sarah M." |
| `specific_review_text` | Excerpt from that review | "took 3 weeks to get a callback" |
| `industry` | Their vertical | "roofing" |
| `city` | Their city | "Phoenix" |
| `service_type` | What they sell | "residential roof repair" |
| `competitor_name` | A direct competitor | "Desert Sun Roofing" |
| `pain_point` | Specific business problem | "losing leads to HomeAdvisor" |
| `cta_link` | Link to your free deliverable | "https://yourdomain.com/demo/apex" |

---

## The 3-Email Sequence

### Email 1 — Day 0: The Value-First Hook

**Timing:** Sent immediately when lead enters campaign
**Goal:** Open a conversation by leading with free value. No pitch. No ask for a call. Just give.

**Template:**

```
{{first_name}} — put together a quick mockup for {{company_name}}.

Looked at {{site_url}} and noticed a few things that might be costing you leads. {{specific_review_author}} left a review mentioning "{{specific_review_text}}" — that kind of feedback usually means there's a gap between how good your {{service_type}} actually is and how your online presence represents it.

Built a quick redesign that fixes the three biggest issues. Took about 20 minutes.

Want me to send it over?
```

**Word count:** ~75
**Why it works:**
- Opens with their name + something you built for them
- References a real review (proves you did research)
- Offers free value before asking for anything
- Ends with a yes/no question (low commitment)

### Email 2 — Day 3: The Follow-Up with Second Angle

**Timing:** 3 days after Email 1
**Goal:** Add a new piece of value. Reference a specific detail. Don't repeat Email 1.

**Template:**

```
One more thing on {{company_name}}, {{first_name}}.

Ran a quick comparison against {{competitor_name}} in {{city}}. They're ranking for 12 search terms you're not — and most of them are high-intent phrases like "{{service_type}} near me."

That gap is probably worth 15-20 inbound leads per month based on the search volume in {{city}}.

The mockup I mentioned covers this too. Worth 5 minutes to look at?

PS — {{company_name}} has {{review_count}} reviews at {{star_rating}} stars. That's actually a strong conversion asset that your current site doesn't use at all.
```

**Word count:** ~90
**Why it works:**
- New angle (competitor comparison) — doesn't rehash Email 1
- Specific numbers (12 search terms, 15-20 leads) make it concrete
- PS line introduces a third value angle (reviews as conversion asset)
- Still ends with a question

### Email 3 — Day 8: The Breakup with Respectful Urgency

**Timing:** 8 days after Email 1 (5 days after Email 2)
**Goal:** Create urgency without being pushy. Give a deadline. Make it easy to say yes or no.

**Template:**

```
{{first_name}} — circling back one last time on the {{company_name}} mockup.

I keep the custom pages live for about a week before I repurpose the work for other {{industry}} companies in {{city}}. Yours is at {{cta_link}} until Friday.

No pressure either way. If {{pain_point}} isn't a priority right now, totally get it.

Worth a look before it comes down?
```

**Word count:** ~65
**Why it works:**
- Clear deadline (Friday) creates urgency without being aggressive
- "No pressure" + "totally get it" is respectful, not desperate
- The link gives them something to click (tracks engagement)
- Short — respects their time after 2 previous emails

---

## Subject Line Variants

Generate 10+ per email. Use the prospect's first name. Use mismatched capitalization. Optimize for the full inbox preview (subject + preview text + first line).

### Email 1 Subject Lines
```
{{first_name}} - built this for {{company_name}}
quick mockup for {{company_name}}
{{first_name}}, something for {{company_name}}
put this together for you {{first_name}}
{{first_name}} - 20 min project
looked at {{site_url}}
{{first_name}} - saw something on your site
mockup for {{company_name}}
{{first_name}}, quick question about {{site_url}}
thought {{company_name}} could use this
```

### Email 2 Subject Lines
```
{{first_name}} - one more thing
re: {{company_name}} mockup
{{first_name}}, ran the numbers
{{company_name}} vs {{competitor_name}}
forgot to mention this {{first_name}}
{{first_name}} - {{city}} {{industry}} data
the {{competitor_name}} comparison
{{first_name}}, quick follow up
one more thing on {{company_name}}
{{first_name}} - the gap I found
```

### Email 3 Subject Lines
```
{{first_name}} - last note
taking this down friday
{{first_name}}, circling back
the {{company_name}} page
{{first_name}} - quick heads up
closing the loop
{{first_name}}, before I take it down
last one {{first_name}}
re: {{company_name}} redesign
{{first_name}} - expiring friday
```

---

## SmartLead Setup

### Step 1: Create the campaign via API

```javascript
const fetch = require("node-fetch");

async function createCampaign(apiKey, name) {
  const response = await fetch(
    `https://server.smartlead.ai/api/v1/campaigns/create?api_key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    }
  );
  const data = await response.json();
  console.log(`Campaign created: ${data.id}`);
  return data.id;
}
```

### Step 2: Add email accounts

```javascript
async function addEmailAccount(apiKey, campaignId, emailAccountId) {
  await fetch(
    `https://server.smartlead.ai/api/v1/campaigns/${campaignId}/email-accounts?api_key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email_account_ids: [emailAccountId]
      })
    }
  );
}
```

### Step 3: Configure the sequence

```javascript
async function setSequence(apiKey, campaignId, sequences) {
  await fetch(
    `https://server.smartlead.ai/api/v1/campaigns/${campaignId}/sequences?api_key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sequences })
    }
  );
}

// Usage:
const sequences = [
  {
    seq_number: 1,
    seq_delay_details: { delay_in_days: 0 },
    subject: "{{first_name}} - built this for {{company_name}}",
    email_body: "{{custom_script_1}}",
    variant_distribution: "equal"
  },
  {
    seq_number: 2,
    seq_delay_details: { delay_in_days: 3 },
    subject: "{{first_name}} - one more thing",
    email_body: "{{custom_script_2}}"
  },
  {
    seq_number: 3,
    seq_delay_details: { delay_in_days: 5 },
    subject: "{{first_name}} - last note",
    email_body: "{{custom_script_3}}"
  }
];
```

### Step 4: Configure warmup schedule

```javascript
async function configureWarmup(apiKey, emailAccountId) {
  await fetch(
    `https://server.smartlead.ai/api/v1/email-accounts/${emailAccountId}/warmup?api_key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        warmup_enabled: true,
        total_warmup_per_day: 40,
        daily_rampup: 2,
        warmup_randomness: "20-40"
      })
    }
  );
}
```

**Warmup rules:**
- Start at 2 emails/day, ramp by 2/day
- Wait at least 14 days before sending live campaigns
- Keep warmup running even during active campaigns
- Target 40 warmup emails/day alongside campaign sends

### Step 5: Push leads with custom scripts

When pushing leads to SmartLead, include up to 3 custom script fields:

```javascript
async function pushLeadWithScripts(apiKey, campaignId, lead) {
  await fetch(
    `https://server.smartlead.ai/api/v1/campaigns/${campaignId}/leads?api_key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify([
        {
          email: lead.email,
          first_name: lead.first_name,
          last_name: lead.last_name,
          company_name: lead.company_name,
          custom_fields: {
            company_domain: lead.company_domain,
            city: lead.city,
            industry: lead.industry,
            star_rating: lead.star_rating,
            review_count: lead.review_count,
            site_url: lead.site_url,
            competitor_name: lead.competitor_name,
            pain_point: lead.pain_point,
            cta_link: lead.cta_link,
            custom_script_1: lead.email_1_body,
            custom_script_2: lead.email_2_body,
            custom_script_3: lead.email_3_body
          }
        }
      ])
    }
  );
}
```

Use `{{custom_script_1}}`, `{{custom_script_2}}`, and `{{custom_script_3}}` as placeholders in the SmartLead sequence. Each lead gets fully unique copy for all 3 emails.

---

## Hot Lead Signals

Track engagement to prioritize follow-up. Ranked by signal strength:

| Signal | Priority | Action |
|---|---|---|
| **Replied** | Highest | Respond within 1 hour. Stop sequence. |
| **Clicked link** (Email 3) | High | They looked at the deliverable. Follow up manually. |
| **Opened all 3 emails** | Medium | Interested but hesitant. Send a manual 4th touch. |
| **Opened Email 1 only** | Low | Subject line worked but content didn't hook. |
| **No opens** | None | Deliverability issue or wrong contact. Check spam. |

### Webhook for real-time signals

SmartLead can send webhooks on reply/click/open events. Set up an endpoint:

```javascript
const express = require("express");
const { getDb } = require("./src/db");

const app = express();
app.use(express.json());

app.post("/webhook/smartlead", async (req, res) => {
  const { event_type, lead_email, campaign_id } = req.body;

  const db = getDb(config);

  const statusMap = {
    EMAIL_OPEN: "opened",
    LINK_CLICK: "clicked",
    EMAIL_REPLY: "replied"
  };

  const newStatus = statusMap[event_type];
  if (newStatus) {
    await db
      .from("contacts")
      .update({ status: newStatus })
      .eq("email", lead_email);
  }

  res.json({ ok: true });
});
```

---

## Supabase Lead Status Tracking

### Schema addition

Add to your existing contacts table or create a dedicated tracking table:

```sql
-- Lead status progression tracking
CREATE TABLE IF NOT EXISTS lead_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id UUID REFERENCES contacts(id),
  campaign_id UUID,
  event_type TEXT NOT NULL,
  email_step INTEGER,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lead_events_contact ON lead_events(contact_id);
CREATE INDEX IF NOT EXISTS idx_lead_events_type ON lead_events(event_type);

-- Status progression:
-- sent → opened → clicked → replied → booked → closed
-- Each transition is a new row in lead_events (append-only)
```

### Status progression logic

```javascript
const STATUS_ORDER = ["sent", "opened", "clicked", "replied", "booked", "closed"];

async function updateLeadStatus(db, contactId, newStatus, metadata = {}) {
  // Get current status
  const { data: contact } = await db
    .from("contacts")
    .select("status")
    .eq("id", contactId)
    .single();

  const currentIndex = STATUS_ORDER.indexOf(contact.status);
  const newIndex = STATUS_ORDER.indexOf(newStatus);

  // Only advance forward, never go backward
  if (newIndex > currentIndex) {
    await db
      .from("contacts")
      .update({ status: newStatus })
      .eq("id", contactId);
  }

  // Always log the event regardless of status change
  await db.from("lead_events").insert({
    contact_id: contactId,
    event_type: newStatus,
    metadata
  });
}
```

---

## Revenue Projections

Use this model to forecast campaign performance:

```
Emails sent per month:        500
Average open rate:            45%     → 225 opens
Average reply rate:           6%      → 30 replies
Positive reply rate:          60%     → 18 conversations
Meeting book rate:            70%     → 12 meetings
Close rate:                   10-15%  → 1-2 deals

If average deal value = $3,000/mo:
  Monthly recurring revenue from cold email = $3,000-$6,000

If average deal value = $10,000 one-time:
  Monthly revenue from cold email = $10,000-$20,000
```

### Projection calculator script

```javascript
function projectRevenue(params) {
  const {
    emailsPerMonth = 500,
    openRate = 0.45,
    replyRate = 0.06,
    positiveReplyRate = 0.60,
    meetingBookRate = 0.70,
    closeRate = 0.12,
    dealValue = 3000
  } = params;

  const opens = Math.round(emailsPerMonth * openRate);
  const replies = Math.round(emailsPerMonth * replyRate);
  const positiveReplies = Math.round(replies * positiveReplyRate);
  const meetings = Math.round(positiveReplies * meetingBookRate);
  const deals = Math.round(meetings * closeRate);
  const revenue = deals * dealValue;

  return {
    emailsSent: emailsPerMonth,
    opens,
    replies,
    positiveReplies,
    meetings,
    deals,
    revenue,
    revenueFormatted: `$${revenue.toLocaleString()}`
  };
}

// Example:
console.log(projectRevenue({ emailsPerMonth: 500, dealValue: 5000 }));
// { emailsSent: 500, opens: 225, replies: 30, positiveReplies: 18,
//   meetings: 13, deals: 2, revenue: 10000, revenueFormatted: "$10,000" }
```

---

## Full Build Sequence

### Step 1: Project setup
```bash
mkdir outreach-sequence && cd outreach-sequence
npm init -y
npm install dotenv @supabase/supabase-js node-fetch@2 express commander
```

### Step 2: Create Supabase tables
Run the SQL from the schema section above. Verify tables exist.

### Step 3: Build the script generator
Create a module that generates all 3 email bodies per lead using the Claude API. Each email must be unique. Use the templates above as structural guides, but the actual copy should be personalized per contact.

```javascript
// src/sequence-gen.js
const fetch = require("node-fetch");

const PROMPTS = {
  email1: `Write Email 1 of a 3-step cold email sequence. This is the value-first hook.
Rules: under 85 words, no signature, no Subject line, end with a question, never start with "I".
The hook: you built something for them (a mockup, a teardown, a redesign). Lead with that.
Reference a specific review or detail about their business. Be specific, not generic.
Return ONLY the email body.`,

  email2: `Write Email 2 of a 3-step cold email sequence. This is the follow-up with a second angle.
Rules: under 90 words, no signature, no Subject line, end with a question, never start with "I".
Introduce a competitor comparison or new data point. Don't repeat Email 1.
Include a PS line with a third angle. Return ONLY the email body.`,

  email3: `Write Email 3 of a 3-step cold email sequence. This is the breakup.
Rules: under 70 words, no signature, no Subject line, end with a question, never start with "I".
Create respectful urgency with a specific deadline. Include the CTA link.
Be short and direct. "No pressure" tone. Return ONLY the email body.`
};

async function generateSequence(config, lead) {
  const results = {};

  for (const [key, systemPrompt] of Object.entries(PROMPTS)) {
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": config.anthropic.apiKey,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 300,
        system: systemPrompt,
        messages: [{
          role: "user",
          content: `Prospect data:
Name: ${lead.first_name} ${lead.last_name}
Company: ${lead.company_name}
Website: ${lead.site_url}
Industry: ${lead.industry}
City: ${lead.city}
Service: ${lead.service_type}
Star rating: ${lead.star_rating} (${lead.review_count} reviews)
Specific review by ${lead.specific_review_author}: "${lead.specific_review_text}"
Competitor: ${lead.competitor_name}
Pain point: ${lead.pain_point}
CTA link: ${lead.cta_link}`
        }]
      })
    });

    const data = await response.json();
    results[key] = data.content[0].text;
  }

  return {
    email_1_body: results.email1,
    email_2_body: results.email2,
    email_3_body: results.email3
  };
}

module.exports = { generateSequence };
```

### Step 4: Build the campaign launcher
Create a script that takes a CSV of enriched leads, generates all 3 email bodies per lead, and pushes to SmartLead.

### Step 5: Set up the SmartLead webhook
Deploy the webhook endpoint to receive open/click/reply events and update Supabase.

### Step 6: Build the reporting dashboard
Query Supabase for funnel metrics: sent -> opened -> clicked -> replied -> booked -> closed.

---

## Testing & Verification

1. **Generate 1 sequence:** Run the script generator for a single test lead. Verify all 3 emails follow the rules (word count, no signature, ends with question, doesn't start with "I").

2. **SmartLead push:** Push 1 test lead with all 3 custom script fields. Open SmartLead and verify the lead appears with all custom fields populated.

3. **Sequence preview:** In SmartLead, preview the email sequence for the test lead. Verify `{{custom_script_1}}`, `{{custom_script_2}}`, and `{{custom_script_3}}` resolve correctly.

4. **Webhook test:** Send a test POST to your webhook endpoint simulating an open event. Verify the contact status updates in Supabase.

5. **Status progression:** Manually trigger events in order (sent -> opened -> clicked -> replied). Verify the status only moves forward, never backward.

6. **Revenue projection:** Run the calculator with your actual numbers. Verify the math is correct.

7. **Full dry run:** Generate sequences for 10 leads, push to SmartLead, verify in the UI.

---

## You're Done When...

- All 3 email templates generate unique copy per lead (no two leads get the same email)
- Every generated email is under 100 words, has no signature, ends with a question, and never starts with "I"
- SmartLead campaign is live with all 3 steps configured at Day 0, Day 3, Day 8
- Warmup is running on all connected email accounts (2/day ramp, 40/day target)
- Each lead in SmartLead has `custom_script_1`, `custom_script_2`, and `custom_script_3` populated
- Subject lines include `{{first_name}}` and use mismatched capitalization
- Supabase tracks lead status progression: sent -> opened -> clicked -> replied -> booked -> closed
- Webhook receives SmartLead events and updates contact status in real time
- `lead_events` table has a row for every status change (append-only audit trail)
- Revenue projection calculator outputs realistic numbers for your funnel
