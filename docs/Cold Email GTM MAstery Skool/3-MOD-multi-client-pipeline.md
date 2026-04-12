# Multi-Client Lead Pipeline — Shared Infrastructure, Isolated Data

> **Type:** Build guide / Claude Code instruction file
> **Description:** A multi-client lead generation pipeline using Supabase for data isolation, Blitz for enrichment, and MillionVerifier for email validation. Every contact is tagged by client and campaign. One system, many clients, zero data leaks.
> **What you'll build:** 5 sequential scripts (blitz-pull.js, email-validation.js, clay-delivery.js, plusvibe-delivery.js, report.js) with Supabase as the central data store.
> **Prerequisites:** Node.js 18+, npm, Supabase project, Blitz API key, MillionVerifier API key.
> **Estimated time:** 4-5 hours.

---

## Instructions for Claude

You are building a multi-client lead pipeline. Every contact must be tagged with a `client_id` and `campaign_id`. Never run a script without a `client_id`. Data isolation between clients is non-negotiable. Follow this spec exactly.

---

## Environment Variables

Create a `.env` file:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
BLITZ_API_KEY=your_blitz_api_key
MILLIONVERIFIER_API_KEY=your_millionverifier_api_key
```

All 4 are required. Every script checks for them on startup.

---

## Project Structure

```
multi-client-pipeline/
  .env
  package.json
  blitz-pull.js          # Step 1: Pull leads from Blitz
  email-validation.js    # Step 2: Validate emails via MillionVerifier
  clay-delivery.js       # Step 3: Deliver to Clay
  plusvibe-delivery.js    # Step 4: Deliver to Plusvibe
  report.js              # Step 5: Generate per-client summary
  src/
    config.js            # Env loader + validation
    db.js                # Supabase client + helpers
    blitz.js             # Blitz API wrapper
    validation.js        # MillionVerifier wrapper
    delivery.js          # Clay + Plusvibe push
    logger.js            # Pipeline logging
  sql/
    schema.sql           # Supabase table creation
```

---

## Step 1: Supabase Schema

Create `sql/schema.sql` and run it in the Supabase SQL editor:

```sql
-- Clients table
CREATE TABLE IF NOT EXISTS clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  domain TEXT,
  industry TEXT,
  delivery_method TEXT DEFAULT 'clay',
  clay_webhook_url TEXT,
  plusvibe_api_key TEXT,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id),
  name TEXT NOT NULL,
  industry TEXT,
  location TEXT,
  titles TEXT[],
  employee_range TEXT,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id),
  campaign_id UUID NOT NULL REFERENCES campaigns(id),
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  email_valid BOOLEAN,
  email_validation_result TEXT,
  title TEXT,
  company_name TEXT,
  company_domain TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,
  industry TEXT,
  employee_count INTEGER,
  status TEXT DEFAULT 'new',
  delivered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(client_id, linkedin_url)
);

-- Pipeline logs table (append-only audit trail)
CREATE TABLE IF NOT EXISTS pipeline_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id),
  campaign_id UUID REFERENCES campaigns(id),
  step TEXT NOT NULL,
  status TEXT NOT NULL,
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contacts_client ON contacts(client_id);
CREATE INDEX IF NOT EXISTS idx_contacts_campaign ON contacts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_linkedin ON contacts(client_id, linkedin_url);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_client ON pipeline_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_step ON pipeline_logs(step);
```

**Key design decisions:**
- `UNIQUE(client_id, linkedin_url)` on contacts — same LinkedIn URL is blocked within a client but allowed across clients
- `pipeline_logs` is append-only — never update or delete rows. This is the audit trail.
- `email_valid` is null until validation runs, then true/false
- `status` on contacts tracks the lifecycle: new → validated → delivered → failed

---

## Step 2: Project Setup

```bash
mkdir multi-client-pipeline && cd multi-client-pipeline
npm init -y
npm install dotenv @supabase/supabase-js node-fetch@2 commander cli-table3
mkdir src sql
```

### `src/config.js`

```javascript
require("dotenv").config();

const REQUIRED = [
  "SUPABASE_URL",
  "SUPABASE_SERVICE_KEY",
  "BLITZ_API_KEY",
  "MILLIONVERIFIER_API_KEY"
];

function loadConfig() {
  const missing = REQUIRED.filter((k) => !process.env[k]);
  if (missing.length > 0) {
    console.error(`Missing env vars: ${missing.join(", ")}`);
    process.exit(1);
  }
  return {
    supabase: {
      url: process.env.SUPABASE_URL,
      serviceKey: process.env.SUPABASE_SERVICE_KEY
    },
    blitz: { apiKey: process.env.BLITZ_API_KEY },
    millionverifier: { apiKey: process.env.MILLIONVERIFIER_API_KEY }
  };
}

module.exports = { loadConfig };
```

### `src/db.js`

```javascript
const { createClient } = require("@supabase/supabase-js");

let client = null;

function getDb(config) {
  if (!client) {
    client = createClient(config.supabase.url, config.supabase.serviceKey);
  }
  return client;
}

async function getClient(db, clientId) {
  const { data, error } = await db
    .from("clients")
    .select("*")
    .eq("id", clientId)
    .single();

  if (error || !data) {
    throw new Error(`Client not found: ${clientId}`);
  }
  return data;
}

async function getCampaign(db, campaignId) {
  const { data, error } = await db
    .from("campaigns")
    .select("*")
    .eq("id", campaignId)
    .single();

  if (error || !data) {
    throw new Error(`Campaign not found: ${campaignId}`);
  }
  return data;
}

async function getExistingLinkedins(db, clientId) {
  const urls = new Set();
  let from = 0;
  const batchSize = 1000;

  while (true) {
    const { data } = await db
      .from("contacts")
      .select("linkedin_url")
      .eq("client_id", clientId)
      .not("linkedin_url", "is", null)
      .range(from, from + batchSize - 1);

    if (!data || data.length === 0) break;
    data.forEach((row) => urls.add(row.linkedin_url));
    if (data.length < batchSize) break;
    from += batchSize;
  }

  return urls;
}

async function insertContacts(db, contacts) {
  const { data, error } = await db
    .from("contacts")
    .upsert(contacts, { onConflict: "client_id,linkedin_url", ignoreDuplicates: true })
    .select();

  if (error) throw new Error(`Insert failed: ${error.message}`);
  return data;
}

async function logPipeline(db, entry) {
  await db.from("pipeline_logs").insert({
    client_id: entry.clientId,
    campaign_id: entry.campaignId || null,
    step: entry.step,
    status: entry.status,
    details: entry.details || {}
  });
}

module.exports = { getDb, getClient, getCampaign, getExistingLinkedins, insertContacts, logPipeline };
```

---

## Step 3: Blitz Pull Script (`blitz-pull.js`)

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { getDb, getClient, getCampaign, getExistingLinkedins, insertContacts, logPipeline } = require("./src/db");
const fetch = require("node-fetch");

const RATE_LIMIT_MS = 200;

program
  .requiredOption("--client-id <uuid>", "Client UUID (required)")
  .requiredOption("--campaign-id <uuid>", "Campaign UUID")
  .option("--count <number>", "Number of contacts to pull", "200")
  .parse();

const opts = program.opts();

async function blitzSearch(config, params) {
  const response = await fetch(
    "https://api.blitz-api.ai/api/search/waterfall-icp",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${config.blitz.apiKey}`
      },
      body: JSON.stringify({
        cascade: ["linkedin", "apollo", "contactout"],
        include_title: params.titles || ["CEO", "Founder", "Owner"],
        industry: params.industry,
        location: params.location || "United States",
        employee_range: params.employeeRange || "1-100",
        limit: Math.min(params.count, 100)
      })
    }
  );
  return response.json();
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
      body: JSON.stringify({ person_linkedin_url: linkedinUrl })
    }
  );
  return response.json();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function run() {
  const config = loadConfig();
  const db = getDb(config);

  // Validate client exists
  const client = await getClient(db, opts.clientId);
  const campaign = await getCampaign(db, opts.campaignId);

  console.log(`\n=== Blitz Pull ===`);
  console.log(`Client: ${client.name} (${opts.clientId})`);
  console.log(`Campaign: ${campaign.name}`);

  await logPipeline(db, {
    clientId: opts.clientId,
    campaignId: opts.campaignId,
    step: "blitz-pull",
    status: "started",
    details: { target_count: parseInt(opts.count) }
  });

  // Get existing LinkedIn URLs for dedup
  const existingUrls = await getExistingLinkedins(db, opts.clientId);
  console.log(`[Dedup] ${existingUrls.size} existing contacts for this client`);

  // Search via Blitz
  const searchResults = await blitzSearch(config, {
    industry: campaign.industry,
    location: campaign.location,
    titles: campaign.titles,
    count: parseInt(opts.count)
  });

  if (!searchResults.results || searchResults.results.length === 0) {
    console.error("No results from Blitz search");
    await logPipeline(db, {
      clientId: opts.clientId,
      campaignId: opts.campaignId,
      step: "blitz-pull",
      status: "failed",
      details: { reason: "no_results" }
    });
    process.exit(1);
  }

  // Filter out existing
  const newProspects = searchResults.results.filter(
    (r) => r.linkedin_url && !existingUrls.has(r.linkedin_url)
  );
  console.log(`[Dedup] ${searchResults.results.length} found, ${newProspects.length} new`);

  // Enrich emails
  const contacts = [];
  for (let i = 0; i < newProspects.length; i++) {
    const prospect = newProspects[i];

    try {
      const enrichment = await enrichEmail(config, prospect.linkedin_url);

      if (enrichment.email) {
        contacts.push({
          client_id: opts.clientId,
          campaign_id: opts.campaignId,
          first_name: prospect.first_name || "",
          last_name: prospect.last_name || "",
          email: enrichment.email,
          title: prospect.title || "",
          company_name: prospect.company_name || "",
          company_domain: prospect.company_domain || "",
          linkedin_url: prospect.linkedin_url,
          city: prospect.city || "",
          state: prospect.state || "",
          industry: campaign.industry,
          employee_count: prospect.employee_count || 0,
          status: "new"
        });
      }
    } catch (err) {
      console.error(`[Blitz] Error enriching ${prospect.linkedin_url}: ${err.message}`);
    }

    await delay(RATE_LIMIT_MS);

    if ((i + 1) % 25 === 0) {
      console.log(`[Blitz] Enriched ${i + 1}/${newProspects.length} (${contacts.length} emails found)`);
    }
  }

  // Insert to Supabase
  if (contacts.length > 0) {
    const inserted = await insertContacts(db, contacts);
    console.log(`[DB] Inserted ${inserted.length} contacts`);
  }

  await logPipeline(db, {
    clientId: opts.clientId,
    campaignId: opts.campaignId,
    step: "blitz-pull",
    status: "completed",
    details: {
      searched: searchResults.results.length,
      new_prospects: newProspects.length,
      emails_found: contacts.length
    }
  });

  console.log(`\n=== Blitz Pull Complete: ${contacts.length} contacts added ===\n`);
}

run().catch((err) => {
  console.error("blitz-pull failed:", err);
  process.exit(1);
});
```

---

## Step 4: Email Validation Script (`email-validation.js`)

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { getDb, getClient, logPipeline } = require("./src/db");
const fetch = require("node-fetch");

program
  .requiredOption("--client-id <uuid>", "Client UUID (required)")
  .option("--campaign-id <uuid>", "Filter to specific campaign")
  .parse();

const opts = program.opts();

async function validateEmail(apiKey, email) {
  const url = `https://api.millionverifier.com/api/v3/?api=${apiKey}&email=${encodeURIComponent(email)}`;
  const response = await fetch(url);
  return response.json();
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function run() {
  const config = loadConfig();
  const db = getDb(config);

  await getClient(db, opts.clientId);

  // Get unvalidated contacts for this client
  let query = db
    .from("contacts")
    .select("*")
    .eq("client_id", opts.clientId)
    .is("email_valid", null)
    .not("email", "is", null);

  if (opts.campaignId) {
    query = query.eq("campaign_id", opts.campaignId);
  }

  const { data: contacts, error } = await query;

  if (error) throw new Error(`Query failed: ${error.message}`);
  if (!contacts || contacts.length === 0) {
    console.log("No contacts to validate.");
    return;
  }

  console.log(`\n=== Email Validation ===`);
  console.log(`Client: ${opts.clientId}`);
  console.log(`Contacts to validate: ${contacts.length}\n`);

  let valid = 0;
  let invalid = 0;

  for (let i = 0; i < contacts.length; i++) {
    const contact = contacts[i];

    try {
      const result = await validateEmail(
        config.millionverifier.apiKey,
        contact.email
      );

      const isValid = result.result === "ok" || result.result === "catch_all";

      await db
        .from("contacts")
        .update({
          email_valid: isValid,
          email_validation_result: result.result,
          status: isValid ? "validated" : "invalid"
        })
        .eq("id", contact.id);

      if (isValid) valid++;
      else invalid++;
    } catch (err) {
      console.error(`[Validation] Error for ${contact.email}: ${err.message}`);
    }

    await delay(100);

    if ((i + 1) % 50 === 0) {
      console.log(`[Validation] ${i + 1}/${contacts.length} (${valid} valid, ${invalid} invalid)`);
    }
  }

  await logPipeline(db, {
    clientId: opts.clientId,
    campaignId: opts.campaignId,
    step: "email-validation",
    status: "completed",
    details: { total: contacts.length, valid, invalid }
  });

  console.log(`\n=== Validation Complete: ${valid} valid, ${invalid} invalid ===\n`);
}

run().catch((err) => {
  console.error("email-validation failed:", err);
  process.exit(1);
});
```

---

## Step 5: Delivery Scripts

### `clay-delivery.js`

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { getDb, getClient, logPipeline } = require("./src/db");
const fetch = require("node-fetch");

program
  .requiredOption("--client-id <uuid>", "Client UUID (required)")
  .option("--campaign-id <uuid>", "Filter to specific campaign")
  .parse();

const opts = program.opts();

async function run() {
  const config = loadConfig();
  const db = getDb(config);

  const client = await getClient(db, opts.clientId);

  if (!client.clay_webhook_url) {
    console.error("No clay_webhook_url configured for this client.");
    process.exit(1);
  }

  // Get validated, undelivered contacts
  let query = db
    .from("contacts")
    .select("*")
    .eq("client_id", opts.clientId)
    .eq("status", "validated")
    .eq("email_valid", true);

  if (opts.campaignId) {
    query = query.eq("campaign_id", opts.campaignId);
  }

  const { data: contacts, error } = await query;

  if (error) throw new Error(`Query failed: ${error.message}`);
  if (!contacts || contacts.length === 0) {
    console.log("No contacts ready for delivery.");
    return;
  }

  console.log(`\n=== Clay Delivery ===`);
  console.log(`Client: ${client.name}`);
  console.log(`Contacts to deliver: ${contacts.length}\n`);

  // Send in batches of 50
  const batchSize = 50;
  let delivered = 0;

  for (let i = 0; i < contacts.length; i += batchSize) {
    const batch = contacts.slice(i, i + batchSize);

    const payload = batch.map((c) => ({
      email: c.email,
      first_name: c.first_name,
      last_name: c.last_name,
      title: c.title,
      company_name: c.company_name,
      company_domain: c.company_domain,
      linkedin_url: c.linkedin_url,
      city: c.city,
      state: c.state,
      industry: c.industry
    }));

    try {
      await fetch(client.clay_webhook_url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      // Mark as delivered
      const ids = batch.map((c) => c.id);
      await db
        .from("contacts")
        .update({ status: "delivered", delivered_at: new Date().toISOString() })
        .in("id", ids);

      delivered += batch.length;
      console.log(`[Clay] Delivered ${delivered}/${contacts.length}`);
    } catch (err) {
      console.error(`[Clay] Batch delivery failed: ${err.message}`);

      const ids = batch.map((c) => c.id);
      await db.from("contacts").update({ status: "failed" }).in("id", ids);
    }
  }

  await logPipeline(db, {
    clientId: opts.clientId,
    campaignId: opts.campaignId,
    step: "clay-delivery",
    status: "completed",
    details: { total: contacts.length, delivered }
  });

  console.log(`\n=== Clay Delivery Complete: ${delivered} delivered ===\n`);
}

run().catch((err) => {
  console.error("clay-delivery failed:", err);
  process.exit(1);
});
```

### `plusvibe-delivery.js`

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { getDb, getClient, logPipeline } = require("./src/db");
const fetch = require("node-fetch");

program
  .requiredOption("--client-id <uuid>", "Client UUID (required)")
  .option("--campaign-id <uuid>", "Filter to specific campaign")
  .parse();

const opts = program.opts();

async function run() {
  const config = loadConfig();
  const db = getDb(config);

  const client = await getClient(db, opts.clientId);

  if (!client.plusvibe_api_key) {
    console.error("No plusvibe_api_key configured for this client.");
    process.exit(1);
  }

  // Get validated, undelivered contacts
  let query = db
    .from("contacts")
    .select("*")
    .eq("client_id", opts.clientId)
    .eq("status", "validated")
    .eq("email_valid", true);

  if (opts.campaignId) {
    query = query.eq("campaign_id", opts.campaignId);
  }

  const { data: contacts, error } = await query;

  if (error) throw new Error(`Query failed: ${error.message}`);
  if (!contacts || contacts.length === 0) {
    console.log("No contacts ready for delivery.");
    return;
  }

  console.log(`\n=== Plusvibe Delivery ===`);
  console.log(`Client: ${client.name}`);
  console.log(`Contacts to deliver: ${contacts.length}\n`);

  let delivered = 0;

  for (const contact of contacts) {
    try {
      await fetch("https://api.plusvibe.com/v1/contacts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${client.plusvibe_api_key}`
        },
        body: JSON.stringify({
          email: contact.email,
          first_name: contact.first_name,
          last_name: contact.last_name,
          company: contact.company_name,
          title: contact.title,
          custom_fields: {
            domain: contact.company_domain,
            linkedin: contact.linkedin_url,
            city: contact.city,
            industry: contact.industry
          }
        })
      });

      await db
        .from("contacts")
        .update({ status: "delivered", delivered_at: new Date().toISOString() })
        .eq("id", contact.id);

      delivered++;
    } catch (err) {
      console.error(`[Plusvibe] Failed for ${contact.email}: ${err.message}`);
      await db.from("contacts").update({ status: "failed" }).eq("id", contact.id);
    }

    if (delivered % 25 === 0) {
      console.log(`[Plusvibe] Delivered ${delivered}/${contacts.length}`);
    }
  }

  await logPipeline(db, {
    clientId: opts.clientId,
    campaignId: opts.campaignId,
    step: "plusvibe-delivery",
    status: "completed",
    details: { total: contacts.length, delivered }
  });

  console.log(`\n=== Plusvibe Delivery Complete: ${delivered} delivered ===\n`);
}

run().catch((err) => {
  console.error("plusvibe-delivery failed:", err);
  process.exit(1);
});
```

---

## Step 6: Reporting Script (`report.js`)

```javascript
#!/usr/bin/env node
const { program } = require("commander");
const { loadConfig } = require("./src/config");
const { getDb, logPipeline } = require("./src/db");
const Table = require("cli-table3");

program
  .option("--client-id <uuid>", "Report for specific client (omit for all)")
  .parse();

const opts = program.opts();

async function run() {
  const config = loadConfig();
  const db = getDb(config);

  // Get all clients (or specific one)
  let clientQuery = db.from("clients").select("*").eq("active", true);
  if (opts.clientId) {
    clientQuery = clientQuery.eq("id", opts.clientId);
  }

  const { data: clients } = await clientQuery;

  if (!clients || clients.length === 0) {
    console.log("No clients found.");
    return;
  }

  console.log(`\n=== Pipeline Report ===\n`);

  for (const client of clients) {
    // Get contact counts by status
    const { data: contacts } = await db
      .from("contacts")
      .select("status, email_valid")
      .eq("client_id", client.id);

    if (!contacts) continue;

    const stats = {
      total: contacts.length,
      new: contacts.filter((c) => c.status === "new").length,
      validated: contacts.filter((c) => c.status === "validated").length,
      invalid: contacts.filter((c) => c.status === "invalid").length,
      delivered: contacts.filter((c) => c.status === "delivered").length,
      failed: contacts.filter((c) => c.status === "failed").length,
      email_valid: contacts.filter((c) => c.email_valid === true).length,
      email_invalid: contacts.filter((c) => c.email_valid === false).length
    };

    // Get campaign breakdown
    const { data: campaigns } = await db
      .from("campaigns")
      .select("id, name, industry, status")
      .eq("client_id", client.id);

    // Get recent pipeline logs
    const { data: logs } = await db
      .from("pipeline_logs")
      .select("step, status, details, created_at")
      .eq("client_id", client.id)
      .order("created_at", { ascending: false })
      .limit(10);

    // Print client summary
    const table = new Table({
      head: ["Metric", "Count"],
      colWidths: [25, 15]
    });

    table.push(
      ["Total contacts", stats.total],
      ["New (unprocessed)", stats.new],
      ["Email valid", stats.email_valid],
      ["Email invalid", stats.email_invalid],
      ["Validated (ready)", stats.validated],
      ["Delivered", stats.delivered],
      ["Failed", stats.failed]
    );

    console.log(`--- ${client.name} (${client.id}) ---`);
    console.log(table.toString());

    if (campaigns && campaigns.length > 0) {
      const cTable = new Table({
        head: ["Campaign", "Industry", "Status"],
        colWidths: [30, 20, 12]
      });
      campaigns.forEach((c) => cTable.push([c.name, c.industry || "-", c.status]));
      console.log(cTable.toString());
    }

    if (logs && logs.length > 0) {
      console.log("\nRecent activity:");
      logs.forEach((log) => {
        const time = new Date(log.created_at).toLocaleString();
        console.log(`  ${time} | ${log.step} | ${log.status} | ${JSON.stringify(log.details)}`);
      });
    }

    console.log("");
  }
}

run().catch((err) => {
  console.error("report failed:", err);
  process.exit(1);
});
```

---

## Trigger Methods

### Manual
```bash
# Full pipeline for one client
node blitz-pull.js --client-id=<uuid> --campaign-id=<uuid> --count 200
node email-validation.js --client-id=<uuid>
node clay-delivery.js --client-id=<uuid>
node report.js --client-id=<uuid>
```

### Scheduled (Trigger.dev)
Set up a Trigger.dev task that runs the pipeline daily per active client:

```javascript
// trigger/daily-pipeline.js
import { schedules } from "@trigger.dev/sdk/v3";
import { exec } from "child_process";

export const dailyPipeline = schedules.task({
  id: "daily-pipeline",
  cron: "0 8 * * 1-5",  // 8 AM weekdays
  run: async () => {
    // Fetch active clients from Supabase, run pipeline for each
    const clients = await getActiveClients();
    for (const client of clients) {
      await execPromise(`node blitz-pull.js --client-id=${client.id} --campaign-id=${client.activeCampaignId} --count 200`);
      await execPromise(`node email-validation.js --client-id=${client.id}`);
      await execPromise(`node clay-delivery.js --client-id=${client.id}`);
    }
  }
});
```

### Webhook
Expose a simple Express endpoint that triggers a pull for a specific client:

```javascript
app.post("/webhook/pull", async (req, res) => {
  const { client_id, campaign_id, count } = req.body;
  // Validate client_id exists, then spawn pipeline
  exec(`node blitz-pull.js --client-id=${client_id} --campaign-id=${campaign_id} --count=${count || 200}`);
  res.json({ status: "started" });
});
```

---

## Adding a New Client

```sql
-- 1. Insert the client
INSERT INTO clients (name, domain, industry, delivery_method, clay_webhook_url)
VALUES ('Acme Corp', 'acmecorp.com', 'construction', 'clay', 'https://hooks.clay.com/...');

-- 2. Create their first campaign
INSERT INTO campaigns (client_id, name, industry, location, titles)
VALUES (
  '<client_uuid>',
  'Construction CEOs - US',
  'construction',
  'United States',
  ARRAY['CEO', 'Owner', 'President']
);
```

Then run: `node blitz-pull.js --client-id=<uuid> --campaign-id=<uuid>`

---

## Testing & Verification

1. **Schema:** Run `sql/schema.sql` in Supabase. Verify all 4 tables exist with correct columns.

2. **Client setup:** Insert a test client and campaign. Verify with: `node report.js`

3. **Blitz pull test:** Run `node blitz-pull.js --client-id=<uuid> --campaign-id=<uuid> --count 5`. Verify 5 contacts appear in Supabase.

4. **Dedup test:** Run the same command again. Verify 0 new contacts are added (all deduped).

5. **Validation test:** Run `node email-validation.js --client-id=<uuid>`. Verify `email_valid` and `email_validation_result` are populated.

6. **Delivery test:** Run `node clay-delivery.js --client-id=<uuid>`. Verify status changes to "delivered" and `delivered_at` is set.

7. **Report test:** Run `node report.js`. Verify counts match what you expect.

8. **Audit trail:** Check `pipeline_logs` table — every step should have a row with timestamps and details.

---

## You're Done When...

- All 4 Supabase tables are created and indexed
- `node blitz-pull.js --client-id=<uuid> --campaign-id=<uuid> --count 5` adds 5 contacts to the database
- Running the same pull a second time adds 0 (dedup working)
- `node email-validation.js --client-id=<uuid>` validates all emails and updates their status
- `node clay-delivery.js --client-id=<uuid>` pushes validated contacts to Clay and marks them delivered
- `node report.js` shows an accurate summary of all clients and their pipeline status
- `pipeline_logs` has a row for every step of every run
- No data from Client A ever appears in Client B's pipeline
- Every script refuses to run without a `--client-id` flag
