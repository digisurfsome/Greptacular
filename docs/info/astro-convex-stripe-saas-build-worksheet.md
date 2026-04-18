# SaaS Build Worksheet: Astro + Convex + Stripe + AI Fulfillment
**Source:** Income Stream Surfers video — Opus 4.7 live build demo  
**Purpose:** Workflow reference for replicating this build as an Archon-automated agency pipeline

---

## The Business Model (What Was Built)

A print-on-demand e-commerce site where:
1. Customer picks a style/character (e.g., "Roman Emperor")
2. Uploads a pet photo
3. AI generates a historical portrait of their pet
4. They pay via Stripe
5. Order is automatically sent to Gelato for printing and fulfillment
6. Ships to customer while owner does nothing

**Replicable for:** Any product where price lives in a DB, not Stripe. Coaching, courses, custom art, digital downloads, physical goods — anything.

---

## Full Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Frontend | **Astro** | SSR mode, dictionary-based i18n from day one |
| Database / Backend | **Convex** | DB + functions + backend as a service. Most env vars live here, not Vercel |
| Payments | **Stripe** | Dynamic pricing — send price from Convex to Stripe. No Stripe products needed |
| Email | **Resend** | For order confirmation emails (not built in video but called out as required) |
| Auth / Accounts | **Clerk** | For customer accounts (not built in video, mentioned as next layer) |
| AI Image Gen | **Nano Banana 2.1** via **Open Router** | Medium thinking mode. Reference image + prompt → portrait |
| Print Fulfillment | **Gelato** | Print on demand. Webhook auto-creates orders. Also has Printify as alternative |
| Deployment | **Vercel** | CLI-based push. Convex handles most vars so minimal Vercel config |
| Repo | **GitHub** | CLI-based creation and push |
| AI Coding Agent | **Claude Desktop App (Claude Code)** | Opus 4.7, medium thinking |

---

## Step-by-Step Build Workflow

### Phase 1 — Project Scaffolding (Minutes 0–4)

**Step 1: Open Claude Desktop, new workspace**
- Say explicitly: **"do not use any skills here"** (or omit if you want skills)
- Claude Code, Opus 4.7

**Step 2: Init Astro + Convex**

Prompt:
```
help me set up Astro with convex to start please. I can run commands if needed. For example, convex is interactive terminal.
```

**Step 3: Run Convex dev in terminal**
```bash
npx convex dev
```
- Name the project (e.g., `astro-commerce-cloud-deployment-eu-west`)
- This creates: database, functions, backend — everything
- Astro sits on top of Convex

**Step 4: Verify project runs** (Claude often does this automatically)

---

### Phase 2 — Stripe Setup (Minutes 4–6)

**Step 5: Request dynamic Stripe setup**

Prompt:
```
please set up Stripe whereby you can store a price in convex and when someone goes to buy said object it charges them the price given to it instead of me making Stripe products. Also give me the Stripe webhook to set up in my Stripe dashboard.
```

**Step 6: Get Stripe test keys**
- Stripe Dashboard → Developers → API Keys
- Copy: `pk_test_...` (publishable) and `sk_test_...` (secret)

**Step 7: Feed keys to Claude**

Prompt:
```
these are my stripe variables: [paste keys]
Please add — make sure that everything is easily changeable so I can just switch to live Stripe variables later and we're live. Thanks.
```

**Step 8: Create Stripe webhook**
- Stripe Dashboard → Developers → Webhooks → Add endpoint
- Endpoint URL: use the URL Claude provided
- Select events: `checkout.session.completed` (and others Claude specified)
- Copy the webhook signing secret (`whsec_...`)

**Step 9: Store webhook secret**

Prompt:
```
please also store my whsec: [paste secret]. Put it in the env variables.
```

---

### Phase 3 — First Test Buy (Minute 6)

**Step 10: Seed a test product and verify end-to-end**
- Claude seeds a product automatically
- Click Buy on the test page
- Use Stripe test card: `4242 4242 4242 4242`, any future date, any CVC
- Verify: webhook fires, order appears in dashboard as `paid`

**Checkpoint:** Full Stripe payment loop working in ~6 minutes from zero.

---

### Phase 4 — Gelato Integration (Minutes ~8–15)

**Step 11: Get Gelato credentials**
- Gelato Dashboard → Developer → API Keys → Add API Key
- Gelato Dashboard → Developer → Webhooks → Add webhook
  - Method: POST
  - Select all relevant order events (needed to update order status back)
- Copy API key and webhook URL/secret

**Step 12: Connect Gelato + fetch catalog**

Prompt:
```
I added a gelato webhook. Here's my gelato API key: [key]
Please set these and find all poster types. I want to also note that shipping is around €24. I want to ship all around the world. Start by making a connection to Gelato for me.
```

What Claude returns: list of catalog types (framed canvas, posters, mounted posters, hanging posters, wallpaper, etc.) with all sizes and variants.

---

### Phase 5 — AI Image Generation Integration (Minutes ~15–20)

**Step 13: Get Open Router API key**
- openrouter.ai → API → Create API Key
- Model to use: **Nano Banana 2.1** (image generation)
- Recommended: use Open Router SDK

**Step 14: Wire up AI image gen + Gelato draft order**

Prompt:
```
make a connection to open router using the SDK. Basically a user should upload a reference image with a prompt. Then the user can select the frame, poster size, etc. Add some leeway for shipping. And then press okay. And then that sends a draft order to Gelato inside my Gelato dashboard.
```

**Step 15: Test locally as a script FIRST (critical pattern)**

Prompt:
```
make sure you test using a reference image to perfect it.
```

**KEY METHOD:** Always build and test as a local script before wiring to the frontend. Claude runs: generate image → save to Convex storage → create Gelato draft order. Get this working in isolation, then plug into UI.

**Common error here:** Convex doesn't allow Node.js inside functions. Claude will hit this and fix it automatically.

---

### Phase 6 — Full Frontend Build (Minutes ~20–35)

**Step 16: Build the entire site in one prompt**

Prompt:
```
create the entire website around people being able to generate historical portraits, oil paintings of their cats and dogs. Each product should be a type of character, for example, astronaut, but think more historical stuff. Generate each image using a pet that makes sense. Dogs and cats for that historical character, not real characters. Give the cat a latinized name and put a plaque on the painting to make it seem like it's a historical piece. Use dictionaries throughout and in English. This is the English version of the site so we can easily translate later into different languages. Wow me with the design. The flow is: click a style → upload image → wait for builder to finish → put shipping/date details → pay → get order confirmation/access page. Do it.
```

**Critical instruction in this prompt:**
- "Use dictionaries throughout" — mandatory for i18n. If you skip this, you'll redo everything when you add languages.
- Specify the full user flow in one line
- "Wow me with the design" — give it creative latitude

**What Claude builds in ~10–15 min:**
- Full multi-page Astro site
- Product catalog (historical character styles)
- Image upload + AI generation flow
- Shipping details form
- Stripe checkout integration
- Order confirmation page
- Convex-backed order storage

---

### Phase 7 — i18n / Translation (Minutes ~35–40)

**Step 17: Add language (Italian example)**

Prompt:
```
translate this entire site into Italian and put it at /it
```

**If you forgot dictionaries:** Claude will need to refactor first. Add this as a follow-up:
```
make sure this is fully language-aware
```

**Result:** `/it` route serves full Italian version. Pattern works for any language.

---

### Phase 8 — Deploy to Vercel (Minutes ~40–45)

**Pre-requisite (do this in terminal before prompting):**
```bash
vercel login    # authenticate Vercel CLI
gh auth login   # authenticate GitHub CLI
```

**Step 18: Create repo and deploy**

Prompt:
```
create a GitHub repo and then push this to Vercel. You have the Vercel CLI.
```

Claude will:
1. `gh repo create` — creates GitHub repo
2. Push code
3. `vercel --prod` — deploys to Vercel

**Why almost no Vercel env vars needed:** Convex stores most secrets. Only Vercel-specific vars need to be added in the Vercel dashboard.

**Step 19: Go live**
- Add domain in Vercel dashboard
- Swap Stripe test keys for production keys (in Vercel env vars or Convex dashboard)
- Done.

---

## Key Patterns & Insights

### Stripe Dynamic Pricing (Most Important)
Instead of creating Stripe products for every item:
- Store price in Convex DB alongside the product
- At checkout, send `{ amount: price_from_db, currency: 'eur' }` directly to Stripe
- No Stripe product catalog needed — one Stripe account handles unlimited SKUs

### Local-Script-First Development
Build each integration as a standalone test script before touching the UI:
1. Write script → test script → fix script → perfect script
2. Then: plug perfected logic into Astro components
3. This is faster and produces cleaner integrations than building UI-first

### Dictionary-First i18n
From the very first prompt that builds the site, include "Use dictionaries throughout." This means:
- All user-facing strings live in a translation dictionary
- Adding `/it`, `/es`, `/fr` etc. is a single prompt later
- Skipping this = full refactor to add languages

### Convex as the Hub
Convex is not just a database — it holds:
- Products and prices
- Orders
- Generated image storage
- Most API keys/secrets
This is why almost no env vars need to be set on Vercel.

### Medium Thinking Mode for Image Gen
When setting up the AI image generation step, use medium thinking mode on Claude. Mentioned as the best balance of quality vs. speed.

### Image Upscaling (Unresolved Gap)
Nano Banana 2.1 cannot produce truly transparent images (issue for t-shirts). Upscaling before sending to Gelato is recommended but no specific tool was named. Flag this as a TODO when building for real.

---

## Full User Flow (End-to-End)

```
Customer lands on site
    ↓
Picks a portrait style (e.g., "Roman Emperor")
    ↓
Clicks "Begin Portrait"
    ↓
Uploads pet photo + enters pet name/description
    ↓
AI generates portrait (Nano Banana 2.1 via Open Router)
    → Reference image + prompt → historical portrait with Latinized name + plaque
    ↓
Customer selects frame, size (A2, A3, etc.)
    ↓
Enters shipping details
    ↓
Stripe checkout (price pulled from Convex, sent dynamically)
    ↓
Webhook fires → Order saved to Convex as "paid"
    ↓
Gelato webhook creates print order → ships to customer
    ↓
(TODO: Resend confirmation email)
```

---

## What He Said About Skills

- He explicitly said **"do not use any skills here"** at the start to demonstrate raw Opus 4.7 power
- He has skills built for this type of workflow in other videos
- No repo URL or skill names mentioned in this video
- He mentioned wanting to go back and find those skills — worth watching his other videos specifically about Claude skills/slash commands
- The implication: with skills, this build would be even faster — the skill would pre-configure the stack setup steps

**What to search for:** His other videos on Claude skills, slash commands, or workflow templates for Astro/Convex/Stripe builds.

---

## Archon Workflow Map

To turn this into an Archon workflow, the nodes would be:

```
[Node 1] Project Init
  Input: project name, business type, product description
  Steps: scaffold Astro + Convex, run npx convex dev
  Output: working dev server

[Node 2] Stripe Setup
  Input: Stripe test publishable key, secret key
  Steps: configure dynamic pricing, create webhook endpoint
  Output: webhook URL, working test checkout

[Node 3] Fulfillment Setup (optional)
  Input: Gelato API key, webhook secret
  Steps: connect Gelato, fetch catalog, map product types
  Output: draft order flow working

[Node 4] AI Integration
  Input: Open Router API key, image gen model
  Steps: wire reference image → AI generation → Gelato draft
  Output: local script tested end-to-end

[Node 5] Full Site Build
  Input: brand name, niche, product styles list, design prompt, languages
  Steps: one-shot full site build prompt with dictionaries
  Output: complete Astro site

[Node 6] i18n (optional)
  Input: list of target languages
  Steps: translate each language, add routes
  Output: multi-language site

[Node 7] Deploy
  Input: GitHub org/name, Vercel account
  Steps: create repo, push, deploy via CLI
  Output: live Vercel URL

[Node 8] Go Live
  Input: production Stripe keys, custom domain
  Steps: swap env vars, add domain
  Output: live business
```

---

## Prompts Cheat Sheet (Copy-Paste Ready)

```
PHASE 1 - SCAFFOLD
help me set up Astro with convex to start please. I can run commands if needed. For example, convex is interactive terminal.

PHASE 2 - STRIPE
please set up Stripe whereby you can store a price in convex and when someone goes to buy said object it charges them the price given to it instead of me making Stripe products. Also give me the Stripe webhook to set up in my Stripe dashboard.

[after getting keys]
these are my stripe variables: [PUBLISHABLE_KEY] [SECRET_KEY]
Please add — make sure that everything is easily changeable so I can just switch to live Stripe variables later and we're live. Thanks.

[after webhook]
please also store my whsec: [WEBHOOK_SECRET]. Put it in the env variables.

PHASE 3 - GELATO
I added a gelato webhook. Here's my gelato API key: [API_KEY]
Please set these and find all poster types. I want to also note that shipping is around €24. I want to ship all around the world. Start by making a connection to Gelato for me.

PHASE 4 - AI IMAGE GEN
make a connection to open router using the SDK. Basically a user should upload a reference image with a prompt. Then the user can select the frame, poster size, etc. Add some leeway for shipping. And then press okay. And then that sends a draft order to Gelato inside my Gelato dashboard.

make sure you test using a reference image to perfect it.

PHASE 5 - FULL SITE
create the entire website around people being able to generate [NICHE: e.g., historical portraits, oil paintings] of their [SUBJECT: e.g., cats and dogs]. Each product should be a type of character [LIST STYLES]. Use dictionaries throughout and in English. This is the English version of the site so we can easily translate later into different languages. Wow me with the design. The flow is: click a style → upload image → wait for builder to finish → put shipping/date details → pay → get order confirmation/access page. Do it.

PHASE 6 - TRANSLATE
translate this entire site into [LANGUAGE] and put it at /[LANG_CODE]

PHASE 7 - DEPLOY
create a GitHub repo and then push this to Vercel. You have the Vercel CLI.
```

---

## TODO / Gaps to Resolve Before Using as Agency Template

- [ ] Image upscaling step between AI gen and Gelato (tool TBD)
- [ ] Resend email setup for order confirmations
- [ ] Clerk for customer accounts / order history
- [ ] Address validation on shipping form
- [ ] Production Stripe key swap checklist
- [ ] Gelato auto-order (not draft) — automation step for unattended fulfillment
- [ ] Find his skills videos for the Claude skill that wraps this workflow
- [ ] Transparent image handling for t-shirt products (Nano Banana limitation)
