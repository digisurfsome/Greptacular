# The Daily Lead Engine — 200+ Personalized Leads Per Campaign Per Day

> **Type:** Build guide / Claude Code instruction file
> **Description:** A fully automated Node.js pipeline that pulls prospects from Apollo, enriches emails via Blitz, generates unique cold email scripts with Claude API, deduplicates against SmartLead, pushes leads with custom scripts, and notifies you via Telegram.
> **What you'll build:** A CLI tool (`node pipeline.js --client cenra --industry construction --count 200`) that produces 200+ ready-to-send personalized leads per run.
> **Prerequisites:** Node.js 18+, npm, accounts with Apollo, Blitz, Anthropic, SmartLead, and a Telegram bot.
> **Estimated time:** 3-4 hours for full build and first successful run.

---

## Instructions for Claude

You are building a cold email lead generation pipeline. Follow this spec exactly. Do not add features that aren't listed. Do not skip steps. Build each module, test it, then move to the next.

---

## Environment Variables

Create a `.env` file in the project root with these values:

```
APOLLO_API_KEY=your_apollo_api_key
BLITZ_API_KEY=your_blitz_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SMARTLEAD_API_KEY=your_smartlead_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Before running anything, verify all 6 variables are present. If any are missing, stop and tell the user.

---

## Project Structure

```
lead-engine/
  .env
  package.json
  pipeline.js          # Main CLI entry point
  src/
    apollo.js          # Apollo prospect search
    blitz.js           # Blitz email enrichment
    scriptgen.js       # Claude API email generation
    smartlead.js       # SmartLead dedup + push
    notify.js          # Telegram notifications
    csv.js             # CSV logging
    config.js          # Env loader + validation
  output/
    (CSV files land here)
```

---

## Step-by-Step Build Plan

### Step 1: Project setup

```bash
mkdir lead-engine && cd lead-engine
npm init -y
npm install dotenv node-fetch@2 csv-writer commander
```

Create `src/config.js`:

```javascript
require("dotenv").config();

const REQUIRED = [
  "APOLLO_API_KEY",
  "BLITZ_API_KEY",
  "ANTHROPIC_API_KEY",
  "SMARTLEAD_API_KEY",
  "TELEGRAM_BOT_TOKEN",
  "TELEGRAM_CHAT_ID"
];

function loadConfig() {
  const missing = REQUIRED.filter((k) => !process.env[k]);
  if (missing.length > 0) {
    console.error(`Missing env vars: ${missing.join(", ")}`);
    process.exit(1);
  }
  return {
    apollo: { apiKey: process.env.APOLLO_API_KEY },
    blitz: { apiKey: process.env.BLITZ_API_KEY },
    anthropic: { apiKey: process.env.ANTHROPIC_API_KEY },
    smartlead: { apiKey: process.env.SMARTLEAD_API_KEY },
    telegram: {
      botToken: process.env.TELEGRAM_BOT_TOKEN,
      chatId: process.env.TELEGRAM_CHAT_ID
    }
  };
}

module.exports = { loadConfig };
```

### Step 2: Apollo prospect search (`src/apollo.js`)

**Endpoint:** `POST https://api.apollo.io/api/v1/mixed_people/search`

**Headers:**
- `Content-Type: application/json`
- `X-Api-Key: <APOLLO_API_KEY>`

```javascript
const fetch = require("node-fetch");

async function searchProspects(config, options) {
  const {
    industry,
    count = 200,
    titles = ["CEO", "Founder", "Owner", "President"],
    employeeRange = ["1,10", "11,20", "21,50", "51,100"],
    location = "United States"
  } = options;

  const results = [];
  let page = 1;
  const perPage = 100;

  while (results.length < count) {
    const response = await fetch(
      "https://api.apollo.io/api/v1/mixed_people/search",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Api-Key": config.apollo.apiKey
        },
        body: JSON.stringify({
          page: page,
          per_page: perPage,
          person_titles: titles,
          q_organization_keyword_tags: [industry],
          person_locations: [location],
          organization_num_employees_ranges: employeeRange
        })
      }
    );

    const data = await response.json();
    if (!data.people || data.people.length === 0) break;

    for (const person of data.people) {
      results.push({
        first_name: person.first_name,
        last_name: person.last_name,
        title: person.title,
        company_name: person.organization?.name || "",
        company_domain: person.organization?.primary_domain || "",
        linkedin_url: person.linkedin_url || "",
        city: person.city || "",
        state: person.state || "",
        industry: industry,
        employee_count: person.organization?.estimated_num_employees || 0
      });
      if (results.length >= count) break;
    }
    page++;
  }

  console.log(`[Apollo] Found ${results.length} prospects`);
  return results;
}

module.exports = { searchProspects };
```

**Intent signals to prioritize in Apollo filters:**
- Hiring for sales/marketing roles (signals growth, no outbound system)
- Recent funding (Series A/B — money to spend, pressure to grow)
- No CRM tools detected (technology filter)
- New CMO/CRO in last 90 days (job change filter — new leaders make new vendor decisions)

### Step 3: Blitz email enrichment (`src/blitz.js`)

**Rate limit: 5 requests per second.** Use a delay queue.

**Two endpoints:**

1. **Waterfall ICP search:** `POST https://api.blitz-api.ai/api/search/waterfall-icp`
   - `cascade` must be an array
   - `include_title` must be an array of strings

2. **Email enrichment:** `POST https://api.blitz-api.ai/v2/enrichment/email`
   - Requires `person_linkedin_url`

```javascript
const fetch = require("node-fetch");

const RATE_LIMIT_MS = 200; // 5 req/sec

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function enrichEmail(config, linkedinUrl) {
  const response = await fetch(
    "https://api.blitz-api.ai/v2/enrichment/email",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${config.blitz.apiKey}`
      },
      body: JSON.stringify({
        person_linkedin_url: linkedinUrl
      })
    }
  );
  return response.json();
}

async function enrichBatch(config, prospects) {
  const enriched = [];
  let found = 0;
  let failed = 0;

  for (let i = 0; i < prospects.length; i++) {
    const prospect = prospects[i];

    if (!prospect.linkedin_url) {
      failed++;
      continue;
    }

    try {
      const result = await enrichEmail(config, prospect.linkedin_url);

      if (result.email) {
        enriched.push({
          ...prospect,
          email: result.email,
          email_confidence: result.confidence || "unknown"
        });
        found++;
      } else {
        failed++;
      }
    } catch (err) {
      console.error(`[Blitz] Error for ${prospect.linkedin_url}: ${err.message}`);
      failed++;
    }

    // Rate limiting
    await delay(RATE_LIMIT_MS);

    if ((i + 1) % 50 === 0) {
      console.log(`[Blitz] Processed ${i + 1}/${prospects.length} (${found} found, ${failed} failed)`);
    }
  }

  console.log(`[Blitz] Enrichment complete: ${found} emails found, ${failed} failed`);
  return enriched;
}

module.exports = { enrichBatch };
```

### Step 4: SmartLead deduplication + push (`src/smartlead.js`)

**Dedup logic:** Fetch all existing leads from the campaign, build a Set of emails, skip any prospects whose email is already in the set.

```javascript
const fetch = require("node-fetch");

const BASE = "https://server.smartlead.ai/api/v1";

async function getExistingLeads(config, campaignId) {
  const emails = new Set();
  let offset = 0;
  const limit = 100;

  while (true) {
    const url = `${BASE}/campaigns/${campaignId}/leads?api_key=${config.smartlead.apiKey}&offset=${offset}&limit=${limit}`;
    const response = await fetch(url);
    const data = await response.json();

    if (!data || !Array.isArray(data) || data.length === 0) break;

    for (const lead of data) {
      if (lead.email) emails.add(lead.email.toLowerCase());
    }

    if (data.length < limit) break;
    offset += limit;
  }

  console.log(`[SmartLead] Found ${emails.size} existing leads in campaign`);
  return emails;
}

async function deduplicateProspects(prospects, existingEmails) {
  const unique = prospects.filter(
    (p) => !existingEmails.has(p.email.toLowerCase())
  );
  console.log(`[SmartLead] ${prospects.length - unique.length} duplicates removed, ${unique.length} new leads`);
  return unique;
}

async function pushLeads(config, campaignId, leads) {
  // SmartLead accepts batches of up to 100
  const batchSize = 100;
  let pushed = 0;

  for (let i = 0; i < leads.length; i += batchSize) {
    const batch = leads.slice(i, i + batchSize);

    const payload = batch.map((lead) => ({
      email: lead.email,
      first_name: lead.first_name,
      last_name: lead.last_name,
      company_name: lead.company_name,
      custom_fields: {
        company_domain: lead.company_domain,
        title: lead.title,
        city: lead.city,
        state: lead.state,
        industry: lead.industry,
        custom_script: lead.custom_script || ""
      }
    }));

    const response = await fetch(
      `${BASE}/campaigns/${campaignId}/leads?api_key=${config.smartlead.apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );

    const result = await response.json();
    pushed += batch.length;
    console.log(`[SmartLead] Pushed ${pushed}/${leads.length}`);
  }

  return pushed;
}

module.exports = { getExistingLeads, deduplicateProspects, pushLeads };
```

### Step 5: Claude API script generation (`src/scriptgen.js`)

**5 concurrent workers.** Each lead gets a unique email. Follow all cold email rules.

```javascript
const fetch = require("node-fetch");

const SYSTEM_PROMPT = `You are a cold email copywriter. Write a single cold email following these rules exactly:

STRUCTURE:
- 70-90 words. Never exceed 100.
- Never start with "I"
- Never use "I hope this finds you well" or "I noticed"
- End with a low-commitment question, not a hard CTA
- No signature, no sign-off, no "Best," no "Thanks"
- No "Subject:" line
- Plain text only. Short paragraphs (1-2 sentences each).

PERSONALIZATION:
- Reference something specific about the prospect's business
- Use the "So What?" principle — lead with the emotional outcome, not the feature
- The email must read like a human spent 5 minutes researching this prospect

TONE:
- Conversational, peer-to-peer
- Confident but not pushy

OUTPUT: Return ONLY the email body. Nothing else.`;

async function generateScript(config, lead, clientOffer) {
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
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: `Write a cold email for this prospect:
Name: ${lead.first_name} ${lead.last_name}
Title: ${lead.title}
Company: ${lead.company_name}
Domain: ${lead.company_domain}
Industry: ${lead.industry}
City: ${lead.city}
Employee count: ${lead.employee_count}

Our offer: ${clientOffer}`
        }
      ]
    })
  });

  const data = await response.json();

  if (data.content && data.content[0]) {
    return data.content[0].text;
  }

  throw new Error(`Claude API error: ${JSON.stringify(data)}`);
}

async function generateScriptsBatch(config, leads, clientOffer, concurrency = 5) {
  const results = [];
  let index = 0;

  async function worker() {
    while (index < leads.length) {
      const i = index++;
      try {
        const script = await generateScript(config, leads[i], clientOffer);
        leads[i].custom_script = script;
        results.push(leads[i]);

        if (results.length % 10 === 0) {
          console.log(`[ScriptGen] ${results.length}/${leads.length} scripts generated`);
        }
      } catch (err) {
        console.error(`[ScriptGen] Failed for ${leads[i].email}: ${err.message}`);
        leads[i].custom_script = "";
        results.push(leads[i]);
      }
    }
  }

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);

  const withScript = results.filter((r) => r.custom_script);
  console.log(`[ScriptGen] Complete: ${withScript.length}/${leads.length} scripts generated`);
  return results;
}

module.exports = { generateScriptsBatch };
```

### Step 6: Telegram notification (`src/notify.js`)

```javascript
const fetch = require("node-fetch");

async function sendNotification(config, message) {
  const url = `https://api.telegram.org/bot${config.telegram.botToken}/sendMessage`;

  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: config.telegram.chatId,
      text: message,
      parse_mode: "Markdown"
    })
  });
}

module.exports = { sendNotification };
```

### Step 7: CSV logging (`src/csv.js`)

Save incrementally every 10 rows. Output to `output/` directory.

```javascript
const fs = require("fs");
const path = require("path");

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function buildCsvRow(lead) {
  const fields = [
    lead.email,
    lead.first_name,
    lead.last_name,
    lead.title,
    lead.company_name,
    lead.company_domain,
    lead.city,
    lead.state,
    lead.industry,
    lead.employee_count,
    (lead.custom_script || "").replace(/"/g, '""')
  ];
  return fields.map((f) => `"${f || ""}"`).join(",");
}

const CSV_HEADER =
  '"email","first_name","last_name","title","company_name","company_domain","city","state","industry","employee_count","custom_script"';

class CsvLogger {
  constructor(clientName, industry) {
    const timestamp = new Date().toISOString().split("T")[0];
    const dir = path.join(__dirname, "..", "output");
    ensureDir(dir);
    this.filePath = path.join(dir, `${clientName}-${industry}-${timestamp}.csv`);
    this.buffer = [];
    this.written = false;
  }

  add(lead) {
    this.buffer.push(lead);
    if (this.buffer.length >= 10) {
      this.flush();
    }
  }

  flush() {
    if (this.buffer.length === 0) return;

    let content = "";
    if (!this.written) {
      content = CSV_HEADER + "\n";
      this.written = true;
    }

    content += this.buffer.map(buildCsvRow).join("\n") + "\n";
    fs.appendFileSync(this.filePath, content);
    this.buffer = [];
  }

  finalize() {
    this.flush();
    return this.filePath;
  }
}

module.exports = { CsvLogger };
```

### Step 8: Main pipeline (`pipeline.js`)

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { searchProspects } = require("./src/apollo");
const { enrichBatch } = require("./src/blitz");
const { generateScriptsBatch } = require("./src/scriptgen");
const {
  getExistingLeads,
  deduplicateProspects,
  pushLeads
} = require("./src/smartlead");
const { sendNotification } = require("./src/notify");
const { CsvLogger } = require("./src/csv");

program
  .requiredOption("--client <name>", "Client name")
  .requiredOption("--industry <industry>", "Target industry")
  .option("--count <number>", "Number of prospects to pull", "200")
  .option("--campaign-id <id>", "SmartLead campaign ID")
  .option("--offer <text>", "Client offer description for script generation")
  .option("--skip-push", "Skip SmartLead push (generate CSV only)")
  .parse();

const opts = program.opts();

async function run() {
  const config = loadConfig();
  const startTime = Date.now();

  console.log(`\n=== Daily Lead Engine ===`);
  console.log(`Client: ${opts.client}`);
  console.log(`Industry: ${opts.industry}`);
  console.log(`Target count: ${opts.count}\n`);

  // Step 1: Apollo search
  const prospects = await searchProspects(config, {
    industry: opts.industry,
    count: parseInt(opts.count)
  });

  if (prospects.length === 0) {
    console.error("No prospects found. Check your Apollo filters.");
    process.exit(1);
  }

  // Step 2: Blitz enrichment
  const enriched = await enrichBatch(config, prospects);

  if (enriched.length === 0) {
    console.error("No emails found after enrichment.");
    process.exit(1);
  }

  // Step 3: Deduplication against SmartLead
  let readyLeads = enriched;
  if (opts.campaignId && !opts.skipPush) {
    const existingEmails = await getExistingLeads(config, opts.campaignId);
    readyLeads = await deduplicateProspects(enriched, existingEmails);
  }

  // Step 4: Script generation
  const offer = opts.offer || `${opts.client} services for ${opts.industry} companies`;
  const scripted = await generateScriptsBatch(config, readyLeads, offer);

  // Step 5: CSV logging
  const csv = new CsvLogger(opts.client, opts.industry);
  for (const lead of scripted) {
    csv.add(lead);
  }
  const csvPath = csv.finalize();
  console.log(`\n[CSV] Saved to ${csvPath}`);

  // Step 6: SmartLead push
  let pushCount = 0;
  if (opts.campaignId && !opts.skipPush) {
    pushCount = await pushLeads(config, opts.campaignId, scripted);
  }

  // Step 7: Telegram notification
  const elapsed = Math.round((Date.now() - startTime) / 1000);
  const message = [
    `*Daily Lead Engine Complete*`,
    ``,
    `Client: ${opts.client}`,
    `Industry: ${opts.industry}`,
    `Apollo pulled: ${prospects.length}`,
    `Emails found: ${enriched.length}`,
    `After dedup: ${readyLeads.length}`,
    `Scripts generated: ${scripted.filter((s) => s.custom_script).length}`,
    pushCount > 0 ? `Pushed to SmartLead: ${pushCount}` : `SmartLead push: skipped`,
    `CSV: ${csvPath}`,
    `Time: ${elapsed}s`
  ].join("\n");

  await sendNotification(config, message);
  console.log(`\n[Telegram] Notification sent`);
  console.log(`\n=== Done in ${elapsed}s ===\n`);
}

run().catch((err) => {
  console.error("Pipeline failed:", err);
  process.exit(1);
});
```

---

## CLI Usage

```bash
# Full run with SmartLead push
node pipeline.js --client cenra --industry construction --count 200 --campaign-id 12345 --offer "We build outbound systems that book 30+ meetings/month for construction companies"

# CSV-only mode (no SmartLead push)
node pipeline.js --client cenra --industry construction --count 50 --skip-push

# Different industry and count
node pipeline.js --client acme --industry saas --count 100 --campaign-id 67890
```

---

## Testing & Verification

### Test each module independently before running the full pipeline:

1. **Config test:** Run `node -e "require('./src/config').loadConfig()"` — should exit cleanly if all env vars are set, or error listing which are missing.

2. **Apollo test:** Run a search for 5 prospects and verify the response structure:
   ```bash
   node -e "
   const {loadConfig} = require('./src/config');
   const {searchProspects} = require('./src/apollo');
   searchProspects(loadConfig(), {industry:'construction', count:5}).then(r => console.log(JSON.stringify(r[0], null, 2)));
   "
   ```

3. **Blitz test:** Take one LinkedIn URL from Apollo results and test enrichment:
   ```bash
   node -e "
   const {loadConfig} = require('./src/config');
   const {enrichBatch} = require('./src/blitz');
   enrichBatch(loadConfig(), [{linkedin_url:'https://linkedin.com/in/test-user'}]).then(console.log);
   "
   ```

4. **Script generation test:** Generate one email and verify it follows the rules (under 100 words, no signature, ends with question):
   ```bash
   node -e "
   const {loadConfig} = require('./src/config');
   const {generateScriptsBatch} = require('./src/scriptgen');
   const lead = {first_name:'John', last_name:'Smith', title:'CEO', company_name:'Acme Roofing', company_domain:'acmeroofing.com', industry:'roofing', city:'Phoenix', employee_count:25};
   generateScriptsBatch(loadConfig(), [lead], 'We build outbound systems for roofing companies', 1).then(r => console.log(r[0].custom_script));
   "
   ```

5. **Full dry run:** Run with `--skip-push --count 5` to verify the whole pipeline without pushing to SmartLead.

---

## You're Done When...

- `node pipeline.js --client test --industry construction --count 5 --skip-push` runs end-to-end without errors
- A CSV file appears in `output/` with all columns populated
- Each `custom_script` value is a unique email under 100 words, doesn't start with "I", ends with a question, and has no signature
- No duplicate emails appear in the output
- Telegram notification arrives with the run summary
- The pipeline handles API errors gracefully (logs the error, skips the lead, continues)
- Running the same command twice with a `--campaign-id` shows deduplication working (second run pushes 0 new leads)
