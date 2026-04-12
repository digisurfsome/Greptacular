# Replace Your $2K/Month SaaS Stack for $25

## What You'll Build

A complete business operating stack using free and open-source tools that replaces $2,000+/month in SaaS subscriptions. You'll migrate your CRM, automation, website, email marketing, scheduling, support, and analytics to self-hosted and free-tier alternatives — all managed through Claude Code.

## Prerequisites

- A computer with terminal access (Mac, Linux, or WSI)
- Claude Pro subscription ($20/mo)
- Basic comfort with the command line
- A VPS account (DigitalOcean or Hetzner) for n8n hosting (~$5/mo)
- Domain name (for self-hosted services)
- 1-2 weekends of focused time

## Estimated Time

- **Audit & planning:** 2-3 hours
- **Core setup (Supabase, n8n, Cal.com):** 4-6 hours
- **Website build & deploy:** 3-5 hours
- **Automation rebuilds:** 4-8 hours
- **Parallel testing period:** 2-4 weeks
- **Total active work:** 15-25 hours across 2-4 weekends

## The Problem

Most businesses run 10-20+ SaaS subscriptions and only use 20% of the features in each one. You're paying enterprise prices for tools you barely touch. The average small business or freelancer spends $500-2,000/month on software — that's $6,000-24,000/year going to tools that could be replaced with free or near-free alternatives.

The AI-native stack changes this. Claude Code can build what you need. Free-tier services handle the infrastructure. Self-hosted tools give you unlimited usage with no per-seat pricing.

## The Replacement Map

| Category | Current Tool | Monthly Cost | Replacement | Monthly Cost |
|---|---|---|---|---|
| CRM | Salesforce | $150 | Supabase | Free |
| Website | Webflow | $39 | Claude Code + Vercel | Free |
| Automation | Zapier | $49 | n8n (self-hosted) | Free |
| Copywriting | Jasper | $59 | Claude Pro | $20 |
| Scheduling | Calendly | $12 | Cal.com | Free |
| Email Marketing | Mailchimp | $29 | Resend + n8n | Free |
| Design | Canva Pro | $49 | Claude + Figma | Free |
| Support | Intercom | $79 | n8n AI Agent | Free |
| Project Mgmt | Notion Team | $25 | Notion Free | Free |
| Analytics | Mixpanel | $49 | Plausible / Umami | Free |
| Code Assistant | GitHub Copilot | $19 | Claude Code | $0 |
| Storage | Google Workspace | $29 | Google Free + Cloudflare R2 | Free |

**Total Before:** ~$2,088/month ($25,056/year)
**Total After:** ~$20/month ($240/year)
**Annual Savings:** $24,816

Even if you add a $5/mo VPS for n8n, you're at $25/month. That's $22,416/year back in your pocket.

## Environment Variables

You'll collect these as you set up each service:

```bash
# Supabase (CRM replacement)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# n8n (self-hosted)
N8N_HOST=n8n.yourdomain.com
N8N_PORT=5678
N8N_BASIC_AUTH_USER=your-username
N8N_BASIC_AUTH_PASSWORD=your-password
N8N_ENCRYPTION_KEY=generate-a-random-string

# Resend (email)
RESEND_API_KEY=re_your-key

# Vercel
VERCEL_TOKEN=your-vercel-token

# Cal.com
CALCOM_API_KEY=your-calcom-key

# Cloudflare R2 (storage)
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
```

## Full Build Instructions

### Step 1: Audit Your Current Stack

Before replacing anything, know exactly what you're paying for.

```
Open a spreadsheet or markdown file. For every tool you pay for, record:

1. Tool name
2. Monthly cost
3. What you actually use it for (be specific — not "email marketing" but "send weekly newsletter to 2,400 subscribers")
4. Usage frequency (daily, weekly, monthly, rarely)
5. Estimated feature usage % (most people find it's 10-30%)
6. Data that lives there (contacts, automations, content, files)
7. Integration dependencies (what connects to what)
```

Sort by cost descending. The top 3-5 tools are your first targets.

### Step 2: Set Up Supabase (CRM Replacement)

Supabase replaces your CRM, database, and backend in one free tool.

```
1. Go to supabase.com → New Project
2. Save your project URL and API keys
3. Create your core tables using the SQL editor:

-- Contacts table (your CRM)
CREATE TABLE contacts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  company TEXT,
  title TEXT,
  phone TEXT,
  source TEXT,
  status TEXT DEFAULT 'lead',
  tags TEXT[],
  notes TEXT,
  last_contacted TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deals / pipeline
CREATE TABLE deals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id),
  title TEXT NOT NULL,
  value NUMERIC,
  stage TEXT DEFAULT 'discovery',
  probability INTEGER DEFAULT 10,
  expected_close DATE,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity log
CREATE TABLE activities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contact_id UUID REFERENCES contacts(id),
  deal_id UUID REFERENCES deals(id),
  type TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

4. Export your existing CRM data as CSV
5. Import via Supabase dashboard (Table Editor → Import CSV)
6. Enable Row Level Security if you'll have multiple users
```

### Step 3: Deploy n8n on a VPS

n8n is the backbone — it replaces Zapier, handles email sequences, and powers your AI support agent.

**Option A: Hetzner (cheapest, EU-based, $4.50/mo)**

```bash
# SSH into your new Hetzner CX22 server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Create n8n directory
mkdir -p /opt/n8n
cd /opt/n8n

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.yourdomain.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.yourdomain.com/
      - N8N_ENCRYPTION_KEY=your-random-encryption-key
      - GENERIC_TIMEZONE=America/New_York
    volumes:
      - n8n_data:/home/node/.n8n

  caddy:
    image: caddy:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

volumes:
  n8n_data:
  caddy_data:
  caddy_config:
COMPOSE

# Create Caddyfile for automatic SSL
cat > Caddyfile << 'CADDY'
n8n.yourdomain.com {
  reverse_proxy n8n:5678
}
CADDY

# Point your domain's DNS to the server IP first, then:
docker compose up -d
```

**Option B: DigitalOcean ($6/mo, US-based)**

Same Docker setup. Create a $6/mo droplet (1GB RAM, Ubuntu 22.04). Follow the same steps above.

**SSL is automatic** with Caddy. No certbot, no renewal cron jobs.

### Step 4: Rebuild Core Automations in n8n

Start with the 3 automations that matter most:

**Lead Capture → CRM:**
```
Trigger: Webhook (from your website contact form)
→ Insert row into Supabase contacts table
→ Send welcome email via Resend
→ Send yourself a notification (Telegram/email)
```

**Email Sequences:**
```
Trigger: When new contact is added with status = 'lead'
→ Wait 1 day → Send email 1 via Resend
→ Wait 3 days → Check if replied (Resend webhook)
→ If no reply → Send email 2
→ Wait 3 days → Send email 3
→ Update contact status in Supabase
```

**AI Support Agent:**
```
Trigger: Webhook (from website chat widget or email)
→ Send message to Claude API with system prompt + knowledge base
→ If confidence > 80% → Auto-reply
→ If confidence < 80% → Forward to you with suggested reply
→ Log interaction in Supabase activities table
```

### Step 5: Build Your Website with Claude Code

```bash
# In your terminal with Claude Code:
mkdir my-website && cd my-website
npx create-next-app@latest . --typescript --tailwind --app

# Then tell Claude Code:
# "Build me a [your business type] website. [Describe your business,
#  brand colors, sections you need]. Make it look like it cost $10K.
#  Single-page, responsive, scroll animations."

# When done:
npx vercel --prod
```

Your website is now live on Vercel's free tier. Custom domain included.

### Step 6: Set Up Cal.com

```
1. Go to cal.com → Create free account
2. Connect your Google/Outlook calendar
3. Create event types:
   - Discovery Call (30 min)
   - Strategy Session (60 min)
   - Quick Chat (15 min)
4. Set availability (working hours, buffer time, minimum notice)
5. Set up webhooks to n8n:
   - On booking → Add to Supabase + send confirmation via Resend
   - On cancellation → Update Supabase + notify you
6. Embed on your website or use direct links
```

### Step 7: Run Both Stacks in Parallel (2-4 Weeks)

Do NOT cancel anything yet. Run old and new side by side.

```
Week 1-2:
- Route new leads to BOTH systems
- Compare: Are contacts syncing? Are automations firing?
- Check email deliverability from Resend vs old provider
- Test every automation end-to-end

Week 3-4:
- Start using new stack as primary
- Old stack becomes backup only
- Confirm nothing is missed
- Document any gaps
```

### Step 8: Cancel the Old Stack

Cancel in order of highest cost first. Before each cancellation:

```
1. Export ALL data (contacts, emails, files, automation configs)
2. Verify the replacement is handling 100% of that tool's jobs
3. Screenshot your automation configs for reference
4. Cancel and note the date (in case you need to reactivate within grace period)
5. Monitor for 1 week after each cancellation
```

## Testing Steps

1. **Supabase CRM:** Add a test contact → verify it appears → update deal stage → check activity log
2. **n8n automations:** Trigger each webhook manually → verify the full chain fires (email sends, Supabase updates, notifications arrive)
3. **Website:** Load on mobile and desktop → check all links → test contact form → verify form submission reaches n8n → reaches Supabase
4. **Cal.com:** Book a test meeting → confirm calendar block → verify n8n webhook fires → check Supabase entry
5. **Email (Resend):** Send test emails → check deliverability → verify they don't land in spam
6. **AI Support:** Send a test message through your support flow → verify Claude responds correctly → check logging
7. **End-to-end:** Simulate a full customer journey: visit site → fill form → get email → book call → verify everything is tracked

## Success Criteria

- All contacts from old CRM are in Supabase with no data loss
- n8n automations handle 100% of what Zapier was doing
- Website loads in under 2 seconds on mobile and desktop
- Email deliverability rate is above 95%
- Cal.com bookings sync to your calendar and CRM
- Support queries get responded to (AI or manual) within target SLA
- You can run your full business workflow for 2 weeks without touching the old stack
- Monthly tool spend is under $30

## The Honest Take

**What you gain:**
- Full ownership of your data and infrastructure
- Unlimited usage with no per-seat or per-action pricing
- AI-native workflows that are impossible in traditional SaaS
- $22,000+ annual savings
- Skills that compound (every tool you build makes you faster)

**What you lose:**
- Managed support (you're the admin now)
- Drag-and-drop simplicity (n8n has a learning curve)
- Setup time (15-25 hours upfront vs clicking "Sign Up")
- Some polish and edge-case features in mature SaaS products
- Automatic updates (you manage n8n upgrades)

**Who should do this:**
- Freelancers paying for tools they barely use
- Agency owners with tight margins
- Solopreneurs who want maximum control
- Small teams (2-5 people) who don't need enterprise features
- Anyone comfortable spending a weekend to save $22K/year

**Who should NOT do this:**
- Teams over 10 people who need enterprise admin controls
- Anyone who genuinely uses 80%+ of their current tools' features
- Businesses where 2-4 weeks of migration risk is unacceptable
