# Operating System Creator — Handoff Brief

> **Context:** We reverse-engineered a cold email system (21 MD files in `docs/Cold Email GTM MAstery Skool/`) and discovered a universal pattern for turning ANY manual business process into a Claude-powered operating system. This doc captures everything so a fresh session can build the deliverables without re-analyzing.

---

## What We Already Confirmed

The cold email system is **legit and production-tested** (real campaign IDs, real client names, real operational lessons). It has 15 components that ALL follow the same 6-step architecture pattern. We need to extract that pattern into a reusable framework.

---

## The Universal 6-Step Pattern (Reverse-Engineered)

Every component in the system follows this exact structure:

### Step 1: INPUT — Where data comes from

| Option | When to Use | Example from Cold Email |
|--------|------------|------------------------|
| **API call** | You need fresh data on demand from an external service | Apollo API to search for prospects by industry/title |
| **Database query** | Data already exists in your system from a previous step | Supabase query to get leads that need emails written |
| **Webhook listener** | An external system pushes data to you when something happens | SmartLead sends a webhook when someone replies to an email |
| **File read** | Data comes from a CSV, XLSX, or JSON file (batch processing) | Google Maps scraper outputs XLSX of businesses |
| **Web scrape** | Data lives on a public website and needs to be extracted | Cheerio/Puppeteer scraping a prospect's website for content |
| **Manual entry** | Human provides the starting data (smallest scale, good for testing) | Typing a domain name into the CLI to research one prospect |
| **Scheduled trigger** | Time-based — run at a specific interval regardless of events | n8n Schedule node fires daily at 8am to start the pipeline |

### Step 2: PROCESS — Claude makes a decision or generates something

| Option | When to Use | Example |
|--------|------------|---------|
| **Generate content** | Create text, code, or documents from data | Claude writes a personalized 80-word cold email from lead research |
| **Classify/categorize** | Sort incoming data into buckets for routing | Claude Haiku classifies a reply as "interested" / "not interested" / "wrong person" |
| **Score/rank** | Assign a numeric value to prioritize items | Claude scores leads 0-100 on ICP fit using a rubric |
| **Analyze/extract** | Pull structured insights from unstructured data | Claude reads a company website and extracts tech stack, pain points, team size |
| **Decide/route** | Choose what happens next based on conditions | If score > 70, send to campaign. If < 30, skip. If 30-70, flag for review |
| **Transform** | Convert data from one format to another | Claude takes raw Google CSE results and produces a structured research report JSON |

**Key rule:** Claude should ANALYZE, never RESEARCH. Always feed Claude real data from Step 1. Never ask Claude to look things up — it will hallucinate. Use Google CSE, Apify, or Perplexity to gather real data, then hand it to Claude.

### Step 3: OUTPUT — Where results go

| Option | When to Use | Example |
|--------|------------|---------|
| **API push** | Send data to an external service | Push leads + custom email scripts to SmartLead campaign via API |
| **Database write** | Store results for other steps or future reference | Save research reports and lead scores to Supabase |
| **File export** | Create a downloadable artifact (CSV, XLSX, HTML, PDF) | Export enriched lead list as XLSX with all research data |
| **Deploy** | Put something live on the internet | Deploy a generated Next.js site to Vercel |
| **Send message** | Deliver content to a person | Send the actual cold email via SMTP or SmartLead |
| **Return to pipeline** | Output of this step becomes input to the next step | Enriched leads flow directly into the script generation step |

### Step 4: STATE — How progress is tracked

| Option | When to Use | Example |
|--------|------------|---------|
| **Database status field** | Multi-step pipelines where items move through stages | Lead status: `new → enriched → scripted → pushed → sent → replied → booked` |
| **Event log table** | You need an audit trail of everything that happened | `lead_events` table with append-only rows: timestamp, lead_id, event_type, details |
| **JSON state file** | Simple single-machine tracking, no database needed | `state.json` tracking which leads have already been processed (dedup) |
| **CSV append log** | Human-readable record, good for debugging and reporting | Write every processed lead to `output/YYYY-MM-DD.csv` with incremental flush |

**Key rule:** Save incrementally, not at the end. Flush CSV every 10 rows. Write to database after each item. If the script crashes at row 100, you don't lose everything.

### Step 5: NOTIFY — How humans stay aware

| Option | When to Use | Example |
|--------|------------|---------|
| **Telegram bot** | Solo operator or small team, need instant mobile alerts | Bot sends: "Pipeline complete: 200 leads processed, 185 pushed, 15 skipped (dupes)" |
| **Email summary** | Formal reporting, client-facing, or daily digest format | Morning email: "Yesterday's campaign results — 3 replies, 1 meeting booked" |
| **Slack webhook** | Team environment where everyone lives in Slack | Post to #leads channel when a hot lead replies |
| **Dashboard/UI** | Need ongoing visibility, not just point-in-time alerts | Metabase dashboard connected to Supabase showing pipeline metrics |
| **Log file** | Developer debugging, not user-facing | `logs/pipeline-2026-04-12.log` with verbose output |

**Key rule:** Always notify on completion AND on failure. A silent failure is worse than a loud crash.

### Step 6: SCHEDULE — How it runs without you

| Option | When to Use | Example |
|--------|------------|---------|
| **Cron job** | Simple, reliable, runs on a Linux server at set times | `0 8 * * * node pipeline.js --client cenra --count 200` (daily at 8am) |
| **n8n Schedule trigger** | Visual workflow, need to chain multiple steps with conditions | n8n workflow fires daily, runs lead research, then email composer, then push |
| **Webhook trigger** | Event-driven — run when something happens, not on a timer | SmartLead webhook fires when a reply comes in, triggers the classifier |
| **n8n/Zapier webhook** | Same as above but within a no-code automation platform | n8n webhook node receives data and kicks off the pipeline |
| **macOS LaunchAgent** | Mac-only, runs when machine is awake | Plist file that runs SiteSprint monitor every 30 minutes |
| **systemd timer** | Linux server, more robust than cron (restart on failure, logging) | systemd unit that runs the pipeline and auto-restarts if it crashes |
| **Queue system** | High volume, need to process items as they arrive | Redis/BullMQ queue where each lead is a job that gets processed by a worker |
| **Manual CLI** | Testing, debugging, or low-volume operation | `node pipeline.js --client cenra --industry construction --count 50` |

**When to use which:**
- **Just starting out / testing:** Manual CLI
- **Proven and stable, simple schedule:** Cron job
- **Need visual workflow with branching:** n8n
- **Event-driven (react to things happening):** Webhook trigger
- **High volume / multiple workers:** Queue system
- **Enterprise / needs restart guarantees:** systemd timer

---

## The 15 Components We Reverse-Engineered From

### 10 Solid (full working code):

1. **Daily Lead Engine** — CLI pipeline: Apollo search → Blitz enrich → Claude generate → SmartLead push → Telegram notify
2. **Multi-Client Pipeline** — Blitz pull → MillionVerifier validate → Clay/Plusvibe deliver, with per-client data isolation
3. **3-Step Outreach Sequence** — SmartLead campaign setup via API, 13 merge fields, webhook tracking
4. **Google Maps Scraping** — Google Places API + Apify approaches, filter + export to XLSX
5. **n8n Lead Research** — 18-node workflow: Google CSE → Claude analysis → scoring → Supabase
6. **n8n Email Composer** — 12-node workflow: fetch research → Claude generate → SmartLead push
7. **Cold Email Masterclass** — Copywriting rules + Claude API code for personalized email generation
8. **SMTP Deep Dive** — Python smtplib sending with Google App Passwords (bypasses OAuth fingerprinting)
9. **Remote Claude Code** — Docker + Express + Telegram for headless server-based Claude Code execution
10. **SiteSprint Autobuilder** — SmartLead polling → Haiku classification → research → site build → Vercel deploy

### 5 Partial (specs/templates, pattern visible):

11. **Auto Site Generator** — Next.js site factory from XLSX lead data
12. **Voice Agent** — Vapi + Twilio + Deepgram + Claude + ElevenLabs phone system
13. **AI Expert Brain** — Domain-specific AI persona via CLAUDE.md + knowledge.md
14. **Prospect Pitch Generator** — Scrape → analyze → HTML presentation
15. **One-Shot Websites** — Detailed prompt templates for Claude to generate premium single-page sites

---

## The 4 Deliverables To Build

### Part 1: The Framework (this file covers the core pattern above — needs expansion into full doc with examples)

Expand the 6-step pattern above into a complete reference guide. For each step, include:
- The options table (done above)
- A "how to choose" decision tree
- Common mistakes and anti-patterns
- How the cold email system implements each step (concrete examples from the 15 components)

### Part 2: The Wizard Questionnaire

Questions to ask about ANY manual business process before building it into a Claude OS. Structure:

**Section A — Process Discovery:**
- What is the process called?
- What does a human do today, step by step?
- How long does each step take?
- How often is this process run?
- What decisions does the human make? What information do they need to make those decisions?
- Where does the starting data come from?
- Where does the end result go?
- What tools/services are already in use?
- What breaks? What goes wrong most often?

**Section B — For Each Step (repeat per step):**
- INPUT: Where does data come from for this step?
- PROCESS: What does the human do with that data? (Generate? Classify? Score? Analyze? Decide?)
- OUTPUT: Where does the result go?
- Can an API-first tool handle the data source? (Find one)
- Can Claude handle the decision/generation? (Define the prompt)
- What's the error case? What happens when it fails?

**Section C — Operations:**
- How often should this run? (Schedule type)
- Who needs to know when it completes? (Notification type)
- How do you track what's been done? (State type)
- What compliance/legal requirements exist?
- What's the budget for tools/APIs?

### Part 3: Proof of Concept — Email Warmup Sequence

Run the wizard on the "email warmup" gap from the cold email system. Fill out every question, map to the 6 steps, produce the full architecture. This proves the framework works.

**Warmup context:** When you set up new email sending domains/mailboxes, you can't just start blasting 200 cold emails. Google/Microsoft will flag you as spam immediately. You need to gradually "warm up" each mailbox by sending small volumes that get opened and replied to, building sender reputation over 14-21 days before cold sending.

### Part 4: The Gap-Fill CLAUDE.md

The actual build file that Claude Code would use to build the email warmup system. Follows the same format as the Skool guy's MD files. This is what we compare against his $27 version.

---

## Key Insights for the Builder

1. **Claude ANALYZES, never RESEARCHES.** Always feed it real data from APIs/scraping. Never ask it to look things up.
2. **Save incrementally.** Flush every 10 rows. Write to DB after each item. Crashes happen.
3. **One tool per job.** No overlap. Each tool has one responsibility.
4. **API-first.** If a tool doesn't have an API, it doesn't belong in the system.
5. **Everything connects through code.** Node.js scripts you control, not Zapier.
6. **The pattern is always the same:** INPUT → CLAUDE BRAIN → OUTPUT, wrapped in STATE + NOTIFY + SCHEDULE.

---

## File Locations

- Cold email source files: `docs/Cold Email GTM MAstery Skool/`
- Additional cold email research: `docs/COLD_EMAIL_SMTP_DEEP_DIVE.md`, `docs/COLD_EMAIL_PLAYBOOK_2026.md`, `docs/COLD_EMAIL_INFRASTRUCTURE_RESEARCH.md`, `docs/COLD_EMAIL_ADVANCED_OPTIONS.md`
- This framework: `docs/operating-system-creator/`
