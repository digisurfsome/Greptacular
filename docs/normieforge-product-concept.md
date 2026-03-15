# NormieForge — Product Concept

**One-liner:** The AI operating system for regular people.

**What it is:** A personal AI agent that automates your life — finances, health, scheduling, home, productivity — and gets smarter the more you use it. No coding. No terminal. Just tell it what you want.

---

## The Market Insight

AI created a new class of power user: **everyone.**

But there's a massive gap:
- Normies WANT AI to run their budget, meal plans, workouts, schedules
- They CAN'T deal with terminals, git, APIs, config files, debugging
- Current solutions are either too technical (AutoForge, Claude Code) or too static (NormieClaw zip files)

**The gap:** Nobody owns the on-ramp from "I want this" to "it's running and maintaining itself."

NormieForge is that on-ramp.

## The Funnel (TAM)

```
┌─────────────────────────────────────────────────────┐
│  NORMIES — "Make my life easier"                     │
│  Market: 100M+ people                                │
│  Price: $9-19/mo                                     │
│  → NormieForge Core (life automation)                │
├─────────────────────────────────────────────────────┤
│  POWER NORMIES — "I want to customize this"          │
│  Market: 10M+ people                                 │
│  Price: $29-49/mo                                    │
│  → NormieForge Pro (custom automations + dashboards) │
├─────────────────────────────────────────────────────┤
│  VIBE CODERS — "I want to build my own tools"        │
│  Market: 1M+ people                                  │
│  Price: $49-99/mo                                    │
│  → AutoForge (full AI coding platform)               │
└─────────────────────────────────────────────────────┘
```

**Key:** Each tier is an UPSELL, not a separate product.
One account, one brain file, one agent that grows with you.

## The Product

### What the user sees:

1. **Sign up** → "What do you want help with?" (checkboxes)
   - [ ] Budget & finances
   - [ ] Meal planning & groceries
   - [ ] Fitness & health tracking
   - [ ] Schedule & calendar
   - [ ] Home maintenance
   - [ ] News & research briefings
   - [ ] Side hustle / business
   - [ ] Kids / family coordination

2. **Agent sets everything up** — connects to their accounts, builds dashboards, creates automations. They watch it happen (like AutoForge's kanban board but for life tasks).

3. **Daily dashboard** — one page showing everything:
   - Today's budget status
   - Meal plan + grocery list
   - Workout
   - Calendar with smart suggestions
   - News briefing relevant to THEM

4. **"Help" button** (VibeHelper) — anything goes wrong, press a button. Agent reads the screen, fixes it. Same tech we just built.

5. **It learns** — brain file gets smarter. After a month it knows:
   - You always overspend on Uber Eats on Fridays
   - You skip workouts on Wednesdays (suggests moving them)
   - Your electricity bill spikes in summer (suggests thermostat schedule)
   - You forget to pay rent until the 3rd (sets up auto-reminder on 28th)

### What's happening under the hood:

- Same agent architecture as AutoForge
- Screen agent (VibeHelper) for when things break
- Personal brain file that grows with every interaction
- Pre-built "life modules" (like NormieClaw's tools but LIVING)
- Deploys to user's own infra (Vercel/Supabase) = data ownership
- Claude/AI does the actual automation work

## Why This Is a Billion-Dollar Play

### 1. Massive TAM
Not "developers" or "vibe coders" — EVERYONE. Every person with a smartphone who's overwhelmed by life admin. That's hundreds of millions of people.

### 2. Recurring Revenue with Natural Expansion
- Start at $9/mo for basic life automation
- Upgrade to $29/mo when they want custom stuff
- Upgrade to $49/mo when they catch the building bug
- Each tier stacks — they never leave, they grow

### 3. Insane Lock-in (The Brain File)
After 3 months, the brain file knows their:
- Financial patterns and goals
- Health data and preferences
- Family schedule and routines
- Work patterns and deadlines
- Shopping habits and preferences

Switching cost is ENORMOUS. Not because of contracts — because the AI KNOWS them. Starting over with a new tool means losing months of personalization.

### 4. Network Effects
- Shared solution library (when the agent solves "how to connect X to Y" for one user, ALL users benefit)
- Community modules (power users create automations that normies can one-click install)
- Referral flywheel (people show friends their dashboard → "I want that")

### 5. Data Moat
Aggregate (anonymized) patterns across millions of users:
- "People who track budgets save 23% more"
- "This meal plan sequence has 89% adherence"
- "This workout schedule has lowest dropout"
- → Feed insights back into the product, making it better for everyone

### 6. Platform Play
Once you have millions of normies with AI agents managing their lives:
- Financial services partnerships (the agent recommends better accounts)
- Health/wellness partnerships (the agent suggests supplements, classes)
- Local services (the agent books the plumber, orders groceries)
- Each partnership = revenue share on a captive, high-intent audience

## Competitive Landscape

| Product | What they do | Gap |
|---------|-------------|-----|
| NormieClaw | Static tool zip files, $9 one-time | No maintenance, no learning, dies when it breaks |
| Notion AI | Smart docs and databases | Still requires manual setup and maintenance |
| Apple Shortcuts | Phone automations | Limited, no AI intelligence, no cross-platform |
| IFTTT/Zapier | Connect apps | Technical, expensive, no intelligence |
| ChatGPT | Answer questions | No persistent state, no automation, forgets you |
| Claude Code | Build software | Way too technical for normies |

**NormieForge's moat:** It's the only one that SETS UP, RUNS, MAINTAINS, and LEARNS — all without the user touching a terminal.

## MVP Scope (v0.1)

Ship the smallest thing that proves the concept:

1. **One life module:** Budget tracker
   - Connects to bank (Plaid API)
   - Categorizes spending automatically
   - Daily summary notification
   - Simple dashboard

2. **Brain file:** Learns spending patterns, suggests savings

3. **Help button:** VibeHelper screen agent for when setup goes wrong

4. **Landing page:** "AI that manages your money. $9/mo."

**Why budget first:**
- Universal pain point (everyone has money stress)
- Clear ROI ("saved me $200/mo" = obvious testimonial)
- High willingness to pay
- Natural upsell ("want me to also plan meals to save on groceries?")

## Revenue Model

| Tier | Price | What they get |
|------|-------|--------------|
| Free | $0 | 1 module, basic brain, 5 help sessions/mo |
| Core | $9/mo | 3 modules, full brain, 50 help sessions/mo |
| Pro | $29/mo | Unlimited modules, custom automations, unlimited help |
| Builder | $49/mo | Everything + AutoForge (build your own tools) |

**Unit economics:**
- Claude API cost per user: ~$2-5/mo (mostly Haiku for daily tasks, Sonnet for help sessions)
- Gross margin: 70-85%
- LTV/CAC: High (brain file = sticky, word of mouth = low CAC)

## The Pitch (to investors)

"Everyone wants AI to manage their life. Nobody's built the on-ramp.

We're building the personal AI operating system for regular people — not developers, not techies, regular people. It sets up your budget, plans your meals, manages your schedule, and gets smarter every day. When something breaks, you press one button and an AI agent fixes it.

We've already built the hard part: an autonomous agent platform (AutoForge) that builds and maintains software. NormieForge is that same tech, pointed at the 100x bigger market of people who want AI to run their life without touching a terminal.

$9/mo. 70%+ margins. Brain file creates massive lock-in. Platform play unlocks financial services, health, and local commerce partnerships.

We're raising $X to ship the MVP and acquire first 10,000 users."

---

## Next Steps

1. Validate demand: Landing page + waitlist
2. Build MVP: Budget module + brain file + help agent
3. Beta: 100 users, measure retention and expansion
4. Launch: ProductHunt, Twitter/X, TikTok (demo videos)
5. Iterate: Add modules based on user requests
6. Raise: Seed round on retention metrics + expansion revenue data
