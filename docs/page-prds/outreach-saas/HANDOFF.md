# FormBlast Outreach Pipeline — Morning Handoff

## What This Is

A fully built automated contact form outreach system for SEO agencies.
Not cold email — the business's own contact form sends the notification.
Your reply-to email only appears as the return address.

The pipeline is complete and committed to `main`. The only thing left to prove
is that the browser agent actually fills a form live. That's blocked by one
specific Windows networking issue described below.

---

## What Was Built (All Committed to main)

### Pipeline Scripts — `outreach/`

| File | What It Does | Cost |
|------|-------------|------|
| `keyword_discovery.py` | Generates 3 buyer-intent keywords per niche+city | $0 |
| `serp_search.py` | DataForSEO API, pulls top 100 SERP results + Google Maps 3-pack | ~$0.01/city |
| `build_list.py` | Enriches businesses with ranking data, assigns Tier A/B/C/D | $0 |
| `classify_businesses.py` | Haiku flags national chains (Roto-Rooter, HomeAdvisor, etc.) — cached forever | ~$0.001 once per niche |
| `generate_variants.py` | ONE Haiku call, generates 10 variants × 6 blocks × 4 tiers = 240 sentences | ~$0.05 once per hook |
| `assemble_emails.py` | random.choice() from variant pool, str.format() variables | $0/email forever |
| `filter.py` | Visits each site, finds contact form, detects CAPTCHA — pure Python | $0 |
| `runner.py` | browser-use + Haiku fills and submits each form | ~$0.01-0.03/form |
| `run_campaign.py` | Single command wraps entire pipeline | — |
| `test_agent.py` | Visual proof-of-concept, opens browser window you can watch | — |
| `test_api_connection.py` | Diagnoses Anthropic API connectivity step by step | — |

### Hook Framework — `outreach/hooks/`

| File | What It Does |
|------|-------------|
| `base.py` | HookModule ABC — fetch_data(), assign_tier(), TIER_ANGLES |
| `seo_rankings.py` | Hook 1 — DataForSEO SERP rankings angle (built) |
| `pagespeed.py` | Hook 2 — Google PageSpeed Insights angle (built, free API) |
| `registry.py` | get_hook(name), list_hooks() |
| `orchestrator.py` | Runs hook against business list, writes enriched CSV |

### PRD Docs — `docs/page-prds/outreach-saas/`

| File | What It Covers |
|------|---------------|
| `prd-v1.md` | Full V1 SaaS product — 9 UI pages, pricing, tech stack |
| `prd-v2.md` | V2 Hook Builder — 8-step no-code wizard, BYOK API keys, community hooks |
| `hook-framework.md` | Hook module design, pluggable data sources, tier logic |
| `README.md` | Overview and pipeline summary |
| `HANDOFF.md` | This file |

---

## The Tier System (How Leads Are Prioritized)

```
Tier A — in the Google Maps 3-pack (positions 1-3)
         These get "you're close, fine-tune" angle
Tier B — organic positions 4-10
         Meaningful gap from top competitor
Tier C — organic positions 11-20
         Buried, serious gap, prime prospect
Tier D — not ranked at all
         AI Search pivot angle ("your competitors are getting found on AI")
```

The tier drives which email angle gets used. Each tier has 10 spinner variants
per block (opener, hook, pain, pitch, CTA, subject). Assembly is random.choice()
so every email looks different at zero cost.

---

## The Windows Networking Problem (Why Agent Hasn't Been Proven Yet)

### What Works
- DNS resolves api.anthropic.com ✓
- Raw TLS socket connects on port 443 ✓
- Playwright opens Chromium browser ✓

### What Fails
- Anthropic SDK (uses httpx) cannot send HTTP requests — "Connection error"
- LangChain Anthropic also fails with same error
- Even with `trust_env=False` (proxy bypass) — still fails
- `NO_PROXY=*` env var — still fails

### Root Cause
The raw socket handshake works because it just opens a TCP connection.
The Anthropic SDK uses `httpx` which sends actual HTTP request data.
Something on this Windows machine (antivirus deep packet inspection —
Kaspersky, Bitdefender, Windows Defender with network inspection, or
a router with SSL inspection) allows the handshake but kills the
HTTP payload to api.anthropic.com.

### The Fix Options (in order of preference)

**Option A — Ollama local model (recommended, zero API cost)**
```cmd
winget install Ollama.Ollama
```
Open new CMD:
```cmd
ollama pull qwen2.5:7b
python outreach/test_agent.py --url https://reliantplumbing.com/contact --local-model
```
No API key needed. No network issues. Browser opens, Qwen fills the form.
This is also the production path for a VPS setup.

**Option B — Whitelist Python in antivirus**
Open your antivirus (Kaspersky / Bitdefender / Windows Defender) and add
`python.exe` to the trusted applications / allowed outbound list.
Then retest: `python outreach/test_api_connection.py`

**Option C — Curl test to confirm if it's Python-specific**
```cmd
curl -s -X POST https://api.anthropic.com/v1/messages ^
  -H "x-api-key: %ANTHROPIC_API_KEY%" ^
  -H "anthropic-version: 2023-06-01" ^
  -H "content-type: application/json" ^
  -d "{\"model\":\"claude-haiku-4-5-20251001\",\"max_tokens\":5,\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}]}"
```
If this returns JSON, antivirus is blocking Python specifically → whitelist python.exe.
If this also fails, the router/ISP is blocking Anthropic → use VPS.

**Option D — Run on VPS directly**
The pipeline is designed for server use. Linux VPS + headless Playwright = no browser window.
RunPod, DigitalOcean, Hetzner all work. Anthropic API unrestricted on Linux VPS.

---

## What "Prove It" Looks Like

The goal is to watch the agent fill a real plumber's contact form live:

```cmd
python outreach/test_agent.py --url https://reliantplumbing.com/contact --local-model
```

Expected behavior:
1. Chromium opens visibly
2. Navigates to the contact page
3. Fills: Name = "Test User", Email = "test@example.com", Subject = "[TEST]...", Message = "[TEST MESSAGE...]"
4. Stops BEFORE hitting submit (safe mode by default)
5. Reports back what fields it found, what it filled, whether there's a CAPTCHA

Once that works, the full pipeline proof is:
```cmd
python outreach/run_campaign.py --niche plumber --city Austin --state Texas --reply-to you@gmail.com --local-model --dry-run
```

---

## The Full One-Command Pipeline

```cmd
python outreach/run_campaign.py ^
  --niche plumber ^
  --city Austin ^
  --state Texas ^
  --reply-to you@gmail.com ^
  --local-model
```

Steps it runs automatically:
1. Discover businesses via DataForSEO (3 keywords = ~$0.01)
2. Generate email variant pool (one-time ~$0.05 if not cached, then $0)
3. Assemble personalized emails ($0 — random.choice())
4. Filter contact forms / detect CAPTCHA ($0 — pure Python)
5. Submit forms via browser agent (~$0 with local model)

Total cost with local model: ~$0.01/city (just DataForSEO)
Total cost with Haiku API: ~$0.50-0.60/city

---

## Required Env Vars

```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-...    ← Only needed WITHOUT --local-model
set DATAFORSEO_LOGIN=your@email.com        ← Always needed for Step 1
set DATAFORSEO_PASSWORD=your_password      ← Always needed for Step 1
set SENDER_NAME=Your Name                  ← Name shown in contact forms
```

---

## What's Left to Build

### To Complete the Proof-of-Concept
- [ ] Get Ollama installed and pull qwen2.5:7b
- [ ] Run test_agent.py with --local-model against a live plumber URL
- [ ] Watch it fill the form
- [ ] Run full run_campaign.py --dry-run to see all 4 steps

### To Complete V1 SaaS
- [ ] Frontend: 9 UI pages from prd-v1.md (React, existing boilerplate)
- [ ] Backend: API endpoints wrapping the pipeline scripts
- [ ] Job queue: Celery + Redis for async campaign runs
- [ ] Reply tracking: IMAP polling on reply-to inbox
- [ ] Multi-touch scheduler: Touch 1 → Touch 2 → Touch 3 auto-scheduling
- [ ] Hook #3: Reviews (SerpAPI) — needed for multi-touch sequences
- [ ] Hook #4: Citations (BrightLocal) — 4 hooks at V1 launch

### The 9 SaaS Pages (prd-v1.md)
1. Dashboard — live stats, active campaigns, recent replies
2. Campaigns (list) — all campaigns with status
3. Campaign Detail — live progress, tier breakdown, business table
4. New Campaign (wizard) — hook → target → preview → schedule
5. Pipeline Planner — calendar, daily send volume, 2-day low alert
6. Drafts — saved campaigns not yet launched
7. Email Studio — spintax editor with [bracket ▾] inline display
8. Analytics — reply rate by tier/hook/niche/city
9. Settings — sender details, delay ranges, multi-touch config

---

## Key Technical Decisions (Don't Change These)

- **browser-use version: 0.1.40** — V2.x dropped langchain compatibility. Pin to 0.1.40.
- **Model for form filling: Haiku (or Ollama)** — DOM-first, reads HTML not screenshots, cheap.
- **Variants generated once, assembled forever** — generate_variants.py is the expensive step (~$0.05). assemble_emails.py is $0/email.
- **Sequential form submission** — 15-45s random delays between forms, looks human.
- **Filter before AI runs** — filter.py checks for CAPTCHA/no-form before browser-use ever opens. Saves money.
- **No user-facing API keys** — DataForSEO, Anthropic, etc. are managed backend. Users pay the SaaS subscription. That's the margin.

---

## File Locations

```
Greptacular/
├── outreach/
│   ├── keyword_discovery.py
│   ├── serp_search.py
│   ├── build_list.py
│   ├── classify_businesses.py
│   ├── generate_variants.py
│   ├── assemble_emails.py
│   ├── filter.py
│   ├── runner.py
│   ├── run_campaign.py
│   ├── test_agent.py          ← Start here for the demo
│   ├── test_api_connection.py ← Run this if API key issues
│   ├── orchestrator.py
│   ├── spinner_variants/      ← JSON variant cache (empty until first run)
│   └── hooks/
│       ├── base.py
│       ├── seo_rankings.py
│       ├── pagespeed.py
│       └── registry.py
└── docs/page-prds/outreach-saas/
    ├── prd-v1.md              ← Full SaaS product spec
    ├── prd-v2.md              ← Hook Builder + BYOK expansion
    ├── hook-framework.md      ← Hook module design
    └── README.md              ← Pipeline overview
```

---

## Morning Priority Order

1. Install Ollama → pull qwen2.5:7b → run test_agent.py --local-model
2. Watch it fill the form live (that's the proof)
3. Run run_campaign.py --dry-run to see full pipeline output
4. If Ollama works cleanly → start SaaS UI (9 pages from prd-v1.md)
