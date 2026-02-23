# Sugar Scanner App - Complete Game Plan

> Full session notes: app concept, competitor analysis, scraping strategy, Fig app mapping, revenue model, and go-to-market.

---

## 1. App Overview

| Element | Details |
|---------|---------|
| **What** | Sugar scanning app — scan food labels, detect hidden sugars |
| **Core Database** | 92 known sugar aliases used in food products |
| **Tech Stack** | Flutter boilerplate (already has scanner built in) |
| **Target Market** | Keto community (primary), sugar-sensitive individuals, health-conscious shoppers |
| **Legal Strategy** | Market to keto (lifestyle choice), NOT diabetes (medical = lawsuit risk) |

### Why This Wins
- Personal need (heavy metal poisoning = zero sugar tolerance, mom at 83 affected cognitively by sugar)
- Friends and family on keto, diabetic family members — built-in test group
- Market validated: Sugar AI has 50K downloads in ~9 months with minimal features
- Flutter boilerplate already has scanner — core functionality is nearly done
- Simple app = perfect for AutoForge, fast to ship

---

## 2. Competitor Analysis

### Sugar AI (Primary Competitor)
| Metric | Value | Your Opportunity |
|--------|-------|-----------------|
| Downloads | 50,000+ | Market exists and is hungry |
| Rating | 4.5 stars / 5.15K reviews | Good but users complaining about missing features |
| Price | $9.99 - $34.99/yr | Room to match or undercut with more value |
| Released | ~May 2025 | Only ~9 months head start |
| Version | 1.1.5 | Barely iterating — sitting on his hands |
| Features | Scan + macros, no accounts | You can lap him on day one |
| Logo/Brand | Red strawberry square — ugly | Massive design advantage for you |
| Weakness | No user accounts, no tracking, no product recs, ignoring feature requests in reviews |

### Other Competitors
- **1-2 other sugar apps** — under 1,000 downloads, not updated in 1-2 years, essentially dead
- **Fig** — allergen-focused, NOT sugar. Beautiful app, professional feel, "homie Apple" vibe. 9 doctors on team. **Model this design/UX quality but for sugar/keto market**
- **Calorie/macro apps** — MyFitnessPal, Lose It, etc. — big but not sugar-specific, bloated

### Features Sugar AI Is Missing (From User Reviews)
- User accounts / profiles
- Food tracking / history
- Favorite products list
- Notifications when product recipes change
- Product recommendations
- Community features
- Better product database coverage

---

## 3. Feature Roadmap

### Phase 1: Launch (Beat Sugar AI)
- [ ] Barcode scanner (already in Flutter boilerplate)
- [ ] 92-sugar database detection
- [ ] Clean scan results UI (safe / warning / danger)
- [ ] User accounts and profiles
- [ ] Scan history
- [ ] Favorite/save products
- [ ] Keto-friendly branding and positioning

### Phase 2: Moat Features
- [ ] Product tracking — get notified if a product's recipe/ingredients change
- [ ] Sugar-free product recommendations (curated alternatives)
- [ ] Product search without scanning (browse the database)
- [ ] Shopping lists
- [ ] Community ratings/reviews on products

### Phase 3: Revenue Expansion
- [ ] Amazon affiliate integration — recommend sugar-free alternatives with affiliate links
- [ ] Sponsored product features — sugar-free brands pay for visibility
- [ ] New product alerts — "This week's new sugar-free products"
- [ ] Articles/content hub about sugar-free products, keto tips
- [ ] Store locator — find which stores carry specific products (HEB use case)

### Phase 4: Platform Play
- [ ] Allergy scanning (Fig's market, done better)
- [ ] Calorie/macro tracking (capture the combined market Sugar AI is attempting)
- [ ] Store inventory tracker — which location has your product (HEB problem)
- [ ] Price comparison across stores
- [ ] High-quality supplement finder
- [ ] Multi-app ecosystem — same product database, different audiences, different branding

---

## 4. Scraping Keto Organizations — Full Plan

### Goal
Build a database of every English-speaking keto organization, community, influencer, and brand for partnership outreach.

### Target Categories

**Tier 1: Large Organizations & Media (10K+ audience)**
- Keto certification bodies
- Keto diet organizations / foundations
- Major keto blogs and media sites (Diet Doctor, Ruled.me, etc.)
- Keto podcast networks
- Keto YouTube channels (100K+ subscribers)
- Keto Instagram accounts (50K+ followers)
- Keto TikTok creators

**Tier 2: Communities & Groups (1K-10K members)**
- Facebook Groups (search "keto" — hundreds of groups, some with 500K+ members)
- Reddit communities (r/keto = 3M+, r/ketorecipes, r/ketogains, etc.)
- Discord servers
- Keto forums

**Tier 3: Brands & Products**
- Sugar-free food brands (potential affiliate partners)
- Keto-specific food companies
- Keto supplement brands
- Keto meal delivery services
- Keto cookbook authors

### Scraping Tools & Methods

#### Finding Organizations
| Tool | What It Does | Cost | Best For |
|------|-------------|------|----------|
| **Google Search Operators** | Targeted searches with specific queries | Free | Initial discovery |
| **Apollo.io** | B2B contact database, search by keyword + role | Free tier: 50 leads/mo, Paid: $49+/mo | Finding founders/marketing contacts |
| **Hunter.io** | Find email addresses for any domain | Free tier: 25 searches/mo, Paid: $49+/mo | Getting emails from keto org websites |
| **PhantomBuster** | Automated social media scraping | $69+/mo | Scraping Facebook groups, Instagram, LinkedIn |
| **Apify** | Web scraping platform with pre-built scrapers | Free tier available, $49+/mo | Google results, directories, any website |
| **BuzzSumo** | Find top content and influencers by topic | $199+/mo | Finding keto influencers by engagement |
| **SparkToro** | Audience research — find where keto people hang out | Free tier available | Discovering platforms and accounts |

#### Google Search Queries to Run
```
"keto" "organization" "contact us"
"keto" "community" "partner with us"
"keto" "affiliate program"
"keto" "sponsor" OR "partnership" OR "collaborate"
"keto certification" organization
"keto" "association" -recipe
site:facebook.com/groups "keto"
site:linkedin.com/company "keto"
"keto influencer" "contact" OR "email" OR "business inquiries"
"keto blog" "advertise with us"
"keto podcast" "sponsor"
"sugar free" "brand" "wholesale" OR "retail" OR "partner"
```

#### Facebook Group Scraping
1. Search "keto" in Facebook Groups
2. Sort by member count
3. Use **GroupLeads** or **Groupboss** to extract admin/moderator info
4. Target groups with 10K-500K members (big enough to matter, admin still accessible)

#### Instagram/TikTok Discovery
1. Search #keto, #ketodiet, #ketolife, #sugarfree
2. Sort creators by follower count
3. Use PhantomBuster to extract profile info and contact details
4. Focus on 10K-500K followers (micro-influencers respond and convert better)

#### Podcast Discovery
1. Search "keto" on Apple Podcasts, Spotify, Podchaser
2. Use Podchaser's database to find host contact info
3. Podcast hosts are GREAT partners — they need content, you have a product to talk about

### Output: The Master Spreadsheet

Columns:
| Column | Description |
|--------|-------------|
| **Name** | Organization/person name |
| **Type** | Organization / Influencer / Brand / Community / Podcast |
| **Platform** | Website / Facebook / Instagram / YouTube / TikTok / Podcast |
| **Size** | Followers, members, subscribers, monthly visitors |
| **Contact Name** | Decision maker name |
| **Contact Email** | Email address |
| **Contact Phone** | If available |
| **Website** | URL |
| **Notes** | What they focus on, how they could partner |
| **Status** | Not contacted / Contacted / Responded / Meeting / Partner |
| **Last Contact Date** | For follow-up tracking |

### Outreach Strategy (For Your Ex-Wife)

**The Pitch (keep it simple):**
> "Hey [name], I'm [name] — we just built a sugar scanner app for the keto community. You scan any food label and it instantly catches all 92 hidden sugar names. Your [group/audience/community] would love this. We're setting up partnerships — would you be open to a quick chat about how we can work together?"

**Partnership Tiers to Offer:**

| Tier | What They Get | What You Get |
|------|--------------|-------------|
| **Affiliate** (easiest sell) | 20-30% of subscriptions they drive, custom referral link | Distribution to their audience |
| **Co-branded** | Their logo in the app, custom landing page | Credibility + their promotion |
| **White label** (big orgs) | Their brand ON the app, you run backend | Massive distribution, recurring revenue |
| **Content partner** | You feature their content/products in app | Cross-promotion, content pipeline |
| **Sponsored reviews** | Free products to review in app | Amazon affiliate revenue + content |

**Her Workflow:**
1. Start with 50 best leads (biggest audience, easiest to reach)
2. Call/email 10 per day
3. She does what she does — connects authentically
4. Track everything in the spreadsheet
5. Close partnerships, move to next 50
6. Goal: 10-20 active partners in first 2 months

---

## 5. Fig App Mapping Plan

### Goal
Document every screen, feature, and flow in the Fig app to use as UX reference for AutoForge build.

### Approach: Manual Screenshots First (Option B — fastest)

**Step 1: Install and Screenshot (20-30 minutes)**
1. Install Fig app on phone
2. Go through EVERY screen systematically:
   - Onboarding / signup flow
   - Home / dashboard
   - Scanner / camera view
   - Scan results
   - Product detail page
   - Search / browse
   - Profile / settings
   - Subscription / paywall
   - Lists / favorites
   - History
   - Alerts / notifications
   - Any educational content
   - Error states
   - Empty states
3. Screenshot each unique screen
4. Note the navigation (how do you get from A to B)

**Step 2: AI Documentation**
1. Upload all screenshots to Claude
2. Prompt: "Document every screen. For each: name it, list all UI elements, describe the layout, note the navigation paths, and list every feature visible. Output as a structured app map."
3. Claude produces a complete screen-by-screen spec

**Step 3: Feed to AutoForge**
1. Take the documented app map
2. Add your modifications (sugar-focused, your branding, extra features)
3. Use your Flutter boilerplate as the starting point
4. Feed the spec into AutoForge
5. Let it build

### Future: Computer Use Agent (Option A — more thorough)
- Android Studio emulator + Claude computer use
- Agent navigates every flow automatically
- Catches edge cases, animations, micro-interactions
- Better for v2 refinement after initial build

---

## 6. Revenue Model

### Direct Revenue
| Stream | Model | Potential |
|--------|-------|-----------|
| **Freemium subscription** | Free: 5 scans/day. Pro: unlimited + features | $9.99-29.99/yr (match Sugar AI) |
| **Amazon affiliate** | Link to sugar-free alternatives after scan | 4-10% commission per sale |
| **Sponsored products** | Sugar-free brands pay for featured placement | CPM or flat monthly fee |
| **White label licensing** | Keto orgs pay for branded version | $500-5000/mo per org |

### Indirect Revenue
- Affiliate commissions from keto organization partnerships
- Content monetization (articles, product reviews)
- Data insights (aggregate product scanning trends — what people are scanning most)

---

## 7. The Bigger Vision: Product Intelligence Platform

The sugar scanner is app #1. The real play is a product database that powers multiple apps:

| App | Audience | Scan Focus |
|-----|----------|------------|
| **Sugar Scanner** (launch) | Keto, sugar-sensitive | Hidden sugars |
| **Allergy Scanner** | Food allergy sufferers | Allergens (Fig's market) |
| **Calorie Scanner** | Weight loss / fitness | Calories + macros |
| **Clean Label Scanner** | Health-conscious | Additives, preservatives, artificial ingredients |
| **Store Finder** | Everyone | Which store near you carries this product (HEB problem) |
| **Supplement Finder** | Health/wellness | High-quality supplements near you |
| **Price Scanner** | Budget shoppers | Compare prices across stores |

**Key insight:** Same underlying product database, same scanning tech, different branding and audience for each app. Build once, deploy many. The "Wendy's and McDonald's on the same corner" strategy — you can own multiple segments simultaneously because the work is already done.

### The Flywheel
1. Sugar scanner launches → builds product database
2. Users scan products → database grows automatically
3. Amazon affiliate generates revenue → funds development
4. Ex-wife closes keto org partnerships → distribution grows
5. Video marketing app creates content → awareness on 78 platforms, 3-5x/day
6. Revenue funds next app (allergy, calories, etc.) → same database, new audience
7. Each new app feeds the database → every app gets better
8. Repeat

---

## 8. Integration with Other Projects

| Project | How It Connects |
|---------|----------------|
| **AutoForge** | Builds the app from spec + Flutter boilerplate |
| **StyleSet** | Gives the app a distinctive design that crushes Sugar AI's strawberry logo |
| **Video Marketing App** | Creates keto/sugar content for 78 platforms on autopilot |
| **All 5 first apps** | Each one feeds content through the video app = gorilla marketing warfare |

### The Content Flywheel Across All Apps
- 5 apps running
- Each posting 3-5x/day
- Across 78 platforms
- Using proven ad templates
- Mix of funny, meaningful, deep content
- Every post is a Super Bowl-level ad on autopilot
- Each app cross-promotes the others

---

## 9. Immediate Next Steps

- [ ] Map the Fig app (screenshots + AI documentation)
- [ ] Write AutoForge app spec (sugar scanner, using Fig UX as reference + your features)
- [ ] Run AutoForge with Flutter boilerplate
- [ ] Build the 92-sugar database (if not already structured for the app)
- [ ] Design brand/logo (use StyleSet for the UI style)
- [ ] Set up scraping tools (Apollo.io free tier + Google search operators)
- [ ] Build the master keto organizations spreadsheet (first 100 leads)
- [ ] Brief ex-wife on the pitch and partnership tiers
- [ ] She starts outreach (10 calls/day, 50 best leads first)
- [ ] Submit to Google Play Store
- [ ] Launch Amazon affiliate integration
- [ ] Start video content production (when video app is ready)

---

## 10. The Personal Why

This isn't just a business play:
- **You**: Heavy metal poisoning 15 years ago, can't eat sugar without severe mental/physical fatigue
- **Mom (83)**: Sugar causes cognitive decline bad enough that people at church question her capability — threatens her biggest source of meaning (church decoration leadership)
- **Ex-wife**: Keto for 20+ years, authentic connection to the community, needs a sales job she can do from home
- **Friends/family**: Multiple people on keto, multiple diabetics — all need this tool
- **Every person in a nursing home**: How many are there "because of sugar" when they could be sharper with dietary changes?

You're building this regardless because you and your people need it. The business model is a bonus.

---

*Session notes compiled — February 2026*
