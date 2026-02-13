# Domain Finder - Domain Intelligence Tool Handoff Document

## Overview

A domain intelligence pipeline that helps entrepreneurs find and validate domain names for their app and business ideas. The user describes their product in natural language, AI generates creative name suggestions, and the system checks availability, assesses brand risks, and provides deep-dive reports on taken domains -- all with affiliate buy links baked in.

This ships as two products: a standalone web and mobile app (Product A) and an integrated step in the AutoForge project creation wizard (Product B). Both share the same Supabase backend and intelligence pipeline.

---

## The Intelligence Pipeline (5 Stages)

### Stage 1: AI Name Generation

User describes their product or app in a paragraph. AI generates 20-30 creative name ideas based on the description, considering:

- **Brandability** -- Is it catchy? Does it roll off the tongue?
- **Memorability** -- Can someone hear it once and remember it?
- **Length** -- Prefer short names, 2-3 syllables, easy to type
- **Uniqueness** -- Avoid generic dictionary words alone
- **Relevance** -- Must relate to the described product
- **.com likelihood** -- Favor names less likely to already be taken

Each suggestion includes a brief reasoning explaining why the name fits.

Example input: "I'm building an app that helps diabetics track their sugar levels. It's aimed at people 50+ who aren't tech-savvy."

Example output names: GlucoEase, SugarSimple, SweetTrack, GlucoBuddy, etc. -- each with a one-line rationale.

### Stage 2: Domain Availability Check

For each name suggestion, check domain availability across multiple TLDs:
- `.com`, `.app`, `.io`, `.dev`, `.net`, `.co`

Uses the Namecheap API (reseller account required) or RDAP protocol for basic availability.

Results shown as color-coded badges per name:
- **Green** -- Available (shows price)
- **Red** -- Taken
- **Yellow** -- Premium / make offer

Pricing displayed for all available options. Results cached for 24 hours to avoid repeated API calls and respect rate limits.

### Stage 3: Threat Assessment

For available domains, search the web to check if anyone is already using that brand name (even without the exact domain). Looks for:

- **Existing businesses** with that name (Google search, LinkedIn, Crunchbase)
- **Trademark filings** via USPTO TESS
- **App Store / Play Store listings** with that name
- **Social media handles** availability (Twitter/X, Instagram, GitHub, TikTok)
- **Developer ecosystem** conflicts (npm packages, GitHub organizations)

AI summarizes findings into risk categories:
- **Direct competitor** (same industry, same name) --> RED
- **Unrelated business** (different industry, same name) --> YELLOW
- **No significant results** --> GREEN

Runs automatically for the top 10 name suggestions; on-demand for others (to manage API costs).

### Stage 4: Deep Dive Report (Paid Feature)

For taken or premium domains the user is particularly interested in. This is the monetizable feature ($1-2 per report, impulse-buy price point).

Report includes:
- **WHOIS / RDAP lookup** -- Registration date, expiry date, registrar, privacy protection status
- **Website activity** -- Is there an active website? When was it last updated? What does it look like?
- **Company research** -- Company size via LinkedIn and Crunchbase, estimated revenue
- **Legal risk assessment** -- Trademark history, active filings, litigation risk
- **Estimated domain value** -- Based on length, keyword value, comparable sales
- **Risk score** -- Green (safe to pursue) / Yellow (proceed with caution) / Red (avoid)

Payment via Stripe or Gumroad per-report checkout. Report saved to database and accessible in search history.

### Stage 5: Results Dashboard

Clean summary showing everything at a glance:
- Name suggestions ranked by availability and fit
- Color-coded risk indicators (green/yellow/red) per name
- Price comparisons across registrars and TLDs
- One-click "Buy" buttons with affiliate links (Namecheap, Hostinger, GoDaddy)
- Star/favorite individual names for shortlisting
- Filter tabs: All / Available / Favorites
- Expandable detail cards per name showing threat assessment and deep dive data

---

## Two Products

### Product A: Standalone App (Web + Mobile)

A full standalone product with its own landing page, user accounts, and monetization.

**Web App:**
- React 19 + TypeScript + Vite for full dashboard experience
- Landing page with the input form as the hero
- Email capture before showing results (or after 1 free search)
- Full results dashboard with all findings
- Affiliate links throughout (Namecheap, Hostinger, GoDaddy)
- Search history for logged-in users
- Stripe/Gumroad integration for per-report payments

**Mobile App:**
- Flutter for cross-platform (iOS + Android)
- On-the-go idea capture -- people get app ideas anywhere (shower, commute, conversation)
- Shares the same Supabase backend as web
- Simplified UI focused on quick name generation and favorites
- Push notifications when deep dive reports complete

**Both share:**
- Same Supabase backend (auth, database, Edge Functions)
- Same AI pipeline (name generation, availability, threat assessment)
- Same user accounts and search history

### Product B: AutoForge Integration

Embeds the domain intelligence pipeline into AutoForge's project creation flow.

- New step in project creation wizard after naming: "Find a Domain?"
- Same pipeline runs inline within AutoForge
- Results shown in a modal or panel (not a separate app)
- Selected domain saved to project config (`.autoforge/domain.json`)
- "Buy" link opens registrar with affiliate tag
- Lightweight integration -- reuses the standalone Supabase backend

---

## Business Model

### Revenue Streams

| Stream | Mechanism | Est. Revenue (1K MAU) |
|--------|-----------|----------------------|
| Deep Dive Reports | $1-2 per report, impulse buy | $450/mo (30% conversion) |
| Affiliate Links | Namecheap/GoDaddy/Hostinger commissions ($3 avg) | $150/mo (5% click-to-buy) |
| Pro Subscriptions | $5-9/month unlimited searches + deep dives + social checker | $350/mo (5% conversion) |
| **Total** | | **~$950/mo per 1K users** |

### Tier Structure

**Free Tier:**
- 3 name generations per day
- Domain availability check included
- Basic threat assessment (top 5 names only)
- Affiliate buy links (revenue for us)

**Per-Report ($1-2):**
- Deep dive report on any specific domain
- WHOIS data, company research, legal risk, estimated value
- Full report saved to account history
- No subscription required -- impulse buy

**Pro Plan ($5-9/month):**
- Unlimited name generations
- Unlimited deep dives
- Social handle checking across all platforms
- Priority API access (faster results)
- Export favorites as CSV
- Search history retention (unlimited)

### Why Affiliate Revenue Is the Biggest Opportunity

Every single user of this tool is a pre-qualified domain buyer. They are actively searching for a domain name to purchase. This is the highest-intent affiliate traffic possible:

1. User describes their idea
2. We show them available domains with prices
3. They click "Buy on Namecheap" with our affiliate tag
4. We earn $3-5 per domain registration

No cold traffic. No convincing needed. They came here TO buy a domain. We just help them find the right one.

---

## Tech Stack

### Frontend (Web)
- **React 19** + **TypeScript** + **Vite 7**
- **Tailwind CSS v4** for styling
- **React Router v7** with hash routing
- **TanStack Query** for server state management
- **Framer Motion** for animations and transitions
- **Lucide React** for icons

### Mobile
- **Flutter** (Dart) -- shares the same Supabase backend
- Recommended models: `qwen3-coder` or `deepseek-coder-v2` for local dev with Ollama
- Targeted at iOS and Android
- Deep linking support for sharing results

### Backend
- **Supabase** -- Auth, PostgreSQL database, Edge Functions, real-time subscriptions
- **Supabase Auth** -- Email/password + Google OAuth
- **Supabase Edge Functions** (Deno) -- AI calls, API proxying, rate limiting

### External APIs

| API | Purpose | Auth | Cost |
|-----|---------|------|------|
| **Namecheap API** | Domain availability + pricing | Reseller account + API key | Free (reseller) |
| **Claude Sonnet API** | Name generation + threat summarization | Anthropic API key | ~$0.01-0.03 per generation |
| **SerpAPI** (or similar) | Web search for brand/trademark research | API key | $50/mo for 5K searches |
| **RDAP Protocol** | Domain ownership lookup (replaces old WHOIS) | None (free, open protocol) | Free |
| **USPTO TESS API** | Trademark search | None (public) | Free |
| **Twitter/X API** | Social handle availability | OAuth bearer token | Free tier available |
| **Instagram API** | Social handle availability | Graph API token | Free tier available |

### Environment Variables

```bash
# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

# Set as Supabase Edge Function secrets (never exposed to client)
ANTHROPIC_API_KEY=sk-ant-...
NAMECHEAP_API_USER=your-username
NAMECHEAP_API_KEY=your-api-key
SERP_API_KEY=your-serp-key
```

---

## Supabase Schema

```sql
-- Users get Supabase Auth automatically (auth.users table)

-- Search sessions: one per "describe your app" submission
CREATE TABLE searches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- AI-generated name suggestions for each search
CREATE TABLE name_suggestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  search_id UUID REFERENCES searches(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  reasoning TEXT,
  is_favorite BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Domain availability results per suggestion per TLD
CREATE TABLE availability_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id UUID REFERENCES name_suggestions(id) ON DELETE CASCADE,
  tld TEXT NOT NULL,
  available BOOLEAN,
  price_cents INTEGER,
  registrar TEXT,
  checked_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(suggestion_id, tld)  -- one result per name per TLD
);

-- Automated threat assessment per suggestion
CREATE TABLE threat_assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id UUID REFERENCES name_suggestions(id) ON DELETE CASCADE,
  risk_score TEXT CHECK (risk_score IN ('green', 'yellow', 'red')),
  existing_businesses JSONB DEFAULT '[]'::jsonb,
  trademark_found BOOLEAN DEFAULT false,
  social_handles JSONB DEFAULT '{}'::jsonb,
  app_store_found BOOLEAN DEFAULT false,
  npm_github_found BOOLEAN DEFAULT false,
  summary TEXT,
  assessed_at TIMESTAMPTZ DEFAULT now()
);

-- Paid deep dive reports for taken/premium domains
CREATE TABLE deep_dives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id UUID REFERENCES name_suggestions(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  whois_data JSONB,
  website_active BOOLEAN,
  website_last_updated DATE,
  website_screenshot_url TEXT,
  company_info JSONB,
  estimated_value_cents INTEGER,
  legal_risk TEXT CHECK (legal_risk IN ('green', 'yellow', 'red')),
  legal_risk_details TEXT,
  full_report TEXT,
  payment_id TEXT,  -- Stripe/Gumroad payment reference
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Affiliate click tracking for analytics and optimization
CREATE TABLE affiliate_clicks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  suggestion_id UUID REFERENCES name_suggestions(id) ON DELETE SET NULL,
  tld TEXT NOT NULL,
  registrar TEXT NOT NULL,  -- 'namecheap', 'hostinger', 'godaddy'
  clicked_at TIMESTAMPTZ DEFAULT now()
);

-- User subscription status
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  tier TEXT NOT NULL CHECK (tier IN ('free', 'pro')) DEFAULT 'free',
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Daily usage tracking for free tier limits
CREATE TABLE daily_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
  search_count INTEGER DEFAULT 0,
  deep_dive_count INTEGER DEFAULT 0,
  UNIQUE(user_id, usage_date)
);

-- Row Level Security policies
ALTER TABLE searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE name_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE availability_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE threat_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE deep_dives ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliate_clicks ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_usage ENABLE ROW LEVEL SECURITY;

-- Users can only read/write their own data
CREATE POLICY "Users read own searches" ON searches
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own searches" ON searches
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own suggestions" ON name_suggestions
  FOR SELECT USING (
    search_id IN (SELECT id FROM searches WHERE user_id = auth.uid())
  );
CREATE POLICY "Users update own favorites" ON name_suggestions
  FOR UPDATE USING (
    search_id IN (SELECT id FROM searches WHERE user_id = auth.uid())
  );

CREATE POLICY "Users read own availability" ON availability_results
  FOR SELECT USING (
    suggestion_id IN (
      SELECT ns.id FROM name_suggestions ns
      JOIN searches s ON ns.search_id = s.id
      WHERE s.user_id = auth.uid()
    )
  );

CREATE POLICY "Users read own assessments" ON threat_assessments
  FOR SELECT USING (
    suggestion_id IN (
      SELECT ns.id FROM name_suggestions ns
      JOIN searches s ON ns.search_id = s.id
      WHERE s.user_id = auth.uid()
    )
  );

CREATE POLICY "Users read own deep dives" ON deep_dives
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users insert own clicks" ON affiliate_clicks
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own subscription" ON subscriptions
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users read own usage" ON daily_usage
  FOR SELECT USING (user_id = auth.uid());

-- Edge Functions need service_role key to insert results
-- (availability_results, threat_assessments, name_suggestions are written by Edge Functions)

-- Indexes for performance
CREATE INDEX idx_searches_user_id ON searches(user_id);
CREATE INDEX idx_searches_created_at ON searches(created_at DESC);
CREATE INDEX idx_name_suggestions_search_id ON name_suggestions(search_id);
CREATE INDEX idx_name_suggestions_favorite ON name_suggestions(is_favorite) WHERE is_favorite = true;
CREATE INDEX idx_availability_suggestion_id ON availability_results(suggestion_id);
CREATE INDEX idx_threat_suggestion_id ON threat_assessments(suggestion_id);
CREATE INDEX idx_deep_dives_suggestion_id ON deep_dives(suggestion_id);
CREATE INDEX idx_daily_usage_user_date ON daily_usage(user_id, usage_date);
```

---

## Feature Breakdown (AutoForge-Compatible, 12 Features)

These features are ordered by dependency and priority. Each is independently testable and maps to AutoForge's feature-by-feature build approach.

### Feature 1: Project Scaffolding
**Priority: 1** | Depends on: none

Set up the foundational project structure with all tooling configured.

- Vite + React 19 + TypeScript + Tailwind CSS v4
- React Router v7 with hash routing (`/#/` prefix)
- Supabase client setup (`@supabase/supabase-js`)
- Environment variables for API keys (`.env` with `VITE_` prefix)
- Basic layout component with header and footer
- Route stubs for all pages: `/`, `/search`, `/results/:id`, `/history`, `/profile`
- TanStack Query provider for server state
- Framer Motion installed for animations
- Lucide React installed for icons

**Steps:**
1. Initialize Vite project with React TypeScript template
2. Install all dependencies: `tailwindcss`, `react-router-dom`, `@supabase/supabase-js`, `@tanstack/react-query`, `framer-motion`, `lucide-react`
3. Configure Tailwind v4 with base design tokens (clean, professional palette)
4. Set up `src/router.tsx` with HashRouter and all route definitions
5. Create `src/components/Layout.tsx` with header (logo, nav links) and footer
6. Create stub page components for each route
7. Create `src/lib/supabase.ts` with client initialization from env vars
8. Create `.env.example` documenting all required environment variables
9. Verify: dev server starts, all routes render placeholder content, no TypeScript errors

### Feature 2: Supabase Auth and User Accounts
**Priority: 1** | Depends on: Feature 1

User authentication with email/password and Google OAuth.

- Sign up and sign in pages with email + password
- Google OAuth option (single button, redirects to Google)
- User profile page showing account info
- Protected routes: `/search`, `/results/:id`, `/history` require auth
- Auth context provider wrapping the app (`useAuth` hook)
- Session persistence via Supabase's built-in session management
- Free tier tracking: query `daily_usage` table, show remaining searches in the UI
- Sign out functionality

**Steps:**
1. Create `src/context/AuthContext.tsx` with Supabase auth state listener
2. Create `src/pages/SignInPage.tsx` with email/password form + Google OAuth button
3. Create `src/pages/SignUpPage.tsx` with registration form
4. Create `src/components/ProtectedRoute.tsx` that redirects unauthenticated users to sign-in
5. Create `src/pages/ProfilePage.tsx` showing user email, subscription tier, usage stats
6. Wire up auth state to the Layout header (show user avatar/email when logged in, sign-in link when not)
7. Implement free tier counter: query `daily_usage` for today, display "2 of 3 searches used today"
8. Verify: sign up, sign in, sign out all work; protected routes redirect when not authenticated

### Feature 3: AI Name Generator
**Priority: 2** | Depends on: Features 1, 2

The core input form and AI-powered name generation.

- Input form: large textarea with placeholder "Describe your app or business in a few sentences..."
- Character count indicator (min 50, max 2000)
- "Generate Names" submit button with loading state
- Calls Supabase Edge Function `generate-names` which calls Claude Sonnet API
- Prompt engineered to generate 20-30 names considering brandability, memorability, length, uniqueness, relevance, and .com likelihood
- Returns names with brief reasoning for each
- Saves search record + all name suggestions to database
- Loading state with animated progress and rotating tips ("Brainstorming creative names...", "Checking brandability...", "Evaluating uniqueness...")
- After generation completes, redirects to results page (`/results/:searchId`)
- Free tier check: if 3 searches used today, show upgrade prompt instead of form

**Steps:**
1. Create `src/pages/SearchPage.tsx` with the description textarea and submit button
2. Create `src/lib/nameGenerator.ts` with `generateNames(description: string)` function calling the Edge Function
3. Create Supabase Edge Function `supabase/functions/generate-names/index.ts`:
   - Receives `{ description: string, user_id: string }`
   - Checks daily usage limit (reject if >= 3 for free tier)
   - Calls Claude Sonnet with the name generation prompt
   - Parses response into structured name + reasoning pairs
   - Inserts search record and all name_suggestions into database
   - Increments daily_usage counter
   - Returns `{ search_id, suggestions: [{ id, name, reasoning }] }`
4. Build loading animation with rotating tip messages
5. On success, navigate to `/results/:searchId`
6. Add free tier check before allowing submission
7. Verify: submit a description, receive 20-30 name suggestions, see them saved in database

**Claude Sonnet Prompt (for the Edge Function):**
```
You are a creative brand naming expert. Given a product description, generate 20-30 unique name suggestions for the product.

For each name, consider:
1. Brandability - Is it catchy and distinctive?
2. Memorability - Easy to remember after hearing once?
3. Length - Prefer 2-3 syllables, easy to type
4. Uniqueness - Avoid common dictionary words alone
5. Domain likelihood - Favor names less likely to be taken as .com
6. Relevance - Must clearly relate to the described product

Product description:
{description}

Return a JSON array of objects with "name" and "reasoning" fields.
Each reasoning should be 1 sentence explaining why this name works.
Order by your confidence in the name (best first).
```

### Feature 4: Domain Availability Checker
**Priority: 2** | Depends on: Features 1, 3

Check domain availability across multiple TLDs for each generated name.

- For each name suggestion, check availability across: `.com`, `.app`, `.io`, `.dev`, `.net`, `.co`
- Calls Supabase Edge Function `check-availability` which calls Namecheap API
- Results displayed as color-coded badges per name:
  - Green badge with price: available
  - Red badge: taken
  - Yellow badge: premium / make offer
- Pricing shown in USD for available domains
- Sort and filter: available only, sort by price, filter by TLD
- Results cached in `availability_results` table for 24 hours
- Before checking API, query cache first -- skip API call if fresh results exist
- Batch processing: check all names in parallel with concurrency limit (5 at a time) to respect rate limits
- Progress indicator: "Checking 15 of 28 names..."

**Steps:**
1. Create Supabase Edge Function `supabase/functions/check-availability/index.ts`:
   - Receives `{ suggestion_ids: string[], names: string[] }`
   - For each name, check cache (availability_results where checked_at > now() - 24h)
   - For uncached names, call Namecheap API `namecheap.domains.check` for all TLDs
   - Also call `namecheap.domains.getList` or RDAP for pricing data
   - Insert results into `availability_results` table
   - Return all results (cached + fresh)
2. Create `src/lib/availabilityChecker.ts` with `checkAvailability(searchId: string)` function
3. Create `src/components/AvailabilityBadge.tsx` -- green/red/yellow badge with optional price
4. Create `src/components/TLDBadgeRow.tsx` -- row of 6 badges (one per TLD) for a single name
5. Add real-time progress tracking during batch checking
6. Add sort/filter controls above the results list
7. Verify: generate names, run availability check, see color-coded badges with prices

**Namecheap API Notes:**
- Requires a reseller account (free to set up at `ap.www.namecheap.com`)
- API endpoint: `https://api.namecheap.com/xml.response`
- Command: `namecheap.domains.check` for availability
- Whitelisted IP required (set in Namecheap account settings)
- Rate limit: 20 requests per minute for free reseller accounts
- Alternative: use RDAP protocol (`https://rdap.org/domain/{name}.{tld}`) for free basic availability checks (no pricing)

### Feature 5: Results Dashboard
**Priority: 3** | Depends on: Features 3, 4

The main results page showing all name suggestions with availability and risk data.

- Route: `/results/:searchId`
- Fetch search record + all suggestions + availability results from Supabase
- Main layout: ranked list of name suggestions
- Each row contains:
  - Name (large, bold text)
  - TLD availability badges (6 badges, one per TLD)
  - Best available price highlighted
  - Risk indicator dot (green/yellow/red) -- populated after threat assessment runs
  - Star/favorite toggle button
  - "Buy" affiliate link button (for available domains)
  - Expand/collapse arrow for detail card
- Expandable detail card per name:
  - All availability results with prices
  - Threat assessment summary (if run)
  - "Run Deep Dive" button (if applicable)
  - Reasoning from AI generation
- Filter tabs: All / Available / Favorites
- Search description shown at the top as context
- "Re-run Availability Check" button (prices change over time)
- Copy name button (clipboard)
- Responsive: full table on desktop, stacked cards on mobile

**Steps:**
1. Create `src/pages/ResultsPage.tsx` with route param extraction and data fetching
2. Create `src/components/NameSuggestionRow.tsx` -- the main row component
3. Create `src/components/NameDetailCard.tsx` -- expandable detail panel
4. Create `src/components/FilterTabs.tsx` -- All / Available / Favorites tabs
5. Create `src/hooks/useSearchResults.ts` -- TanStack Query hook fetching search + suggestions + availability
6. Implement favorite toggle (update `is_favorite` in Supabase, optimistic update in UI)
7. Implement copy-to-clipboard with toast confirmation
8. Build responsive layout (table on desktop, cards on mobile)
9. Verify: navigate to results page, see all names with badges, filter works, favorites persist

### Feature 6: Threat Assessment (Web Search)
**Priority: 3** | Depends on: Features 3, 5

Automated brand risk assessment for available domain names.

- For each available domain name, search the web for existing businesses using that name
- Supabase Edge Function `assess-threats` calls SerpAPI (or similar web search API)
- AI summarizes findings into risk categories:
  - **Direct competitor** (same industry, same name) --> RED
  - **Unrelated business** (different industry, same name) --> YELLOW
  - **No significant results** --> GREEN
- Checks for:
  - Business websites using the name
  - App Store and Play Store listings
  - Social media accounts (@name on major platforms)
  - npm packages and GitHub repositories
  - USPTO trademark filings
- Results shown as an expandable "Risk Report" card on the results dashboard
- Rate limited: runs automatically for the top 10 available names, on-demand for others
- Each assessment costs API calls, so batch processing with progress indicator
- "Assess Risk" button on names that have not been assessed yet

**Steps:**
1. Create Supabase Edge Function `supabase/functions/assess-threats/index.ts`:
   - Receives `{ suggestion_id: string, name: string, product_description: string }`
   - Runs web searches: `"{name}" business`, `"{name}" app`, `"{name}" trademark`
   - Calls Claude Sonnet to summarize findings and classify risk
   - Checks npm registry (`https://registry.npmjs.org/{name}`)
   - Checks GitHub (`https://api.github.com/repos/{name}` and `/orgs/{name}`)
   - Inserts results into `threat_assessments` table
   - Returns structured assessment
2. Create `src/lib/threatAssessment.ts` with `assessThreat(suggestionId, name)` function
3. Create `src/components/RiskReport.tsx` -- expandable risk summary card
4. Create `src/components/RiskBadge.tsx` -- green/yellow/red dot with tooltip
5. Auto-trigger assessment for top 10 available names after availability check completes
6. Add "Assess Risk" button for names not yet assessed
7. Show progress: "Assessing 3 of 10 names..."
8. Verify: after availability check, threat assessments run for top names, risk badges appear

**Claude Sonnet Prompt (for threat assessment summarization):**
```
You are a brand risk analyst. Given web search results about a potential business name, assess the risk of using this name for a new product.

Product being named: {description}
Proposed name: {name}

Web search results:
{search_results}

npm registry check: {npm_result}
GitHub check: {github_result}

Classify the risk as:
- "green" (safe): No significant existing use of this name in a similar or competing space
- "yellow" (caution): Some existing use but in unrelated industries, or minor conflicts
- "red" (avoid): Direct competitor or well-known brand using this exact name

Return JSON: {
  "risk_score": "green|yellow|red",
  "existing_businesses": [{ "name": "...", "industry": "...", "url": "..." }],
  "trademark_found": true/false,
  "social_handles": { "twitter": "available|taken", "instagram": "available|taken", ... },
  "app_store_found": true/false,
  "npm_github_found": true/false,
  "summary": "2-3 sentence plain English summary of the risk"
}
```

### Feature 7: Deep Dive Report
**Priority: 4** | Depends on: Features 5, 6

Paid deep-dive reports for taken or premium domains the user wants to pursue.

- Available for any name suggestion, but most useful for taken/premium domains
- This is the paid feature: $1-2 per report
- Payment flow: click "Run Deep Dive" --> Stripe Checkout or Gumroad overlay --> on success, trigger report
- Report generation via Supabase Edge Function `deep-dive`:
  - **RDAP/WHOIS lookup**: registration date, expiry, registrar, privacy protection
  - **Website check**: fetch the domain, check if active, capture last-modified header
  - **Company research**: AI-powered research using web search (LinkedIn, Crunchbase mentions)
  - **Legal risk**: trademark history search, active filings
  - **Estimated value**: based on domain length, keyword value, TLD, age, comparable sales
  - **Full narrative report**: AI-generated 500-word analysis with recommendation
- Report displayed as a formatted card with sections
- Risk score badge: Green (safe to pursue) / Yellow (caution) / Red (avoid)
- "Download Report" as PDF (client-side generation)
- Report saved to `deep_dives` table, accessible from search history
- Stripe webhook or client-side payment verification before generating

**Steps:**
1. Create Supabase Edge Function `supabase/functions/deep-dive/index.ts`:
   - Receives `{ suggestion_id: string, name: string, tld: string, payment_id: string }`
   - Verifies payment via Stripe API
   - Performs RDAP lookup (`https://rdap.org/domain/{name}.{tld}`)
   - Fetches the domain URL, checks HTTP status and last-modified header
   - Runs web searches for company info
   - Calls Claude Sonnet to compile full narrative report
   - Inserts into `deep_dives` table
   - Returns complete report
2. Create `src/lib/deepDive.ts` with `requestDeepDive(suggestionId, name, tld)` function
3. Create `src/lib/payment.ts` with Stripe checkout session creation
4. Create `src/components/DeepDiveReport.tsx` -- formatted report card with all sections
5. Create `src/components/PaymentButton.tsx` -- "Run Deep Dive ($1.50)" button with Stripe integration
6. Add "Download as PDF" functionality using browser print or a library like `jspdf`
7. Verify: click deep dive, complete payment, see full report generated and saved

### Feature 8: Affiliate Buy Links
**Priority: 3** | Depends on: Features 4, 5

Affiliate purchase links integrated throughout the results dashboard.

- "Buy on Namecheap" button with affiliate tracking tag on every available domain
- Also show Hostinger and GoDaddy options where applicable
- Affiliate links include the user's referral code (configured in environment variables)
- Track click-throughs in Supabase `affiliate_clicks` table for analytics
- After clicking buy: show a subtle prompt "Did you purchase? Save domain to your profile"
- Highlight value propositions: "Includes free WHOIS privacy" for Namecheap
- Show price comparison across registrars when data is available
- Affiliate link format:
  - Namecheap: `https://www.namecheap.com/domains/registration/results/?domain={name}.{tld}&aff={AFFILIATE_ID}`
  - Hostinger: `https://www.hostinger.com/domain-checker?domain={name}.{tld}&ref={AFFILIATE_ID}`
  - GoDaddy: `https://www.godaddy.com/domainsearch/find?domainToCheck={name}.{tld}&isc={AFFILIATE_ID}`

**Steps:**
1. Create `src/components/BuyButton.tsx` -- affiliate-linked purchase button with registrar logo
2. Create `src/components/RegistrarComparison.tsx` -- price comparison across registrars
3. Create `src/lib/affiliateLinks.ts` -- generates affiliate URLs with tracking params
4. Create `src/lib/affiliateTracking.ts` -- logs clicks to Supabase `affiliate_clicks` table
5. Add affiliate config to environment variables (`VITE_NAMECHEAP_AFF_ID`, `VITE_HOSTINGER_REF_ID`, `VITE_GODADDY_ISC`)
6. Integrate buy buttons into the results dashboard name rows
7. Add "post-purchase" prompt after clicking a buy link
8. Verify: click buy button, verify affiliate tag in URL, verify click logged in database

### Feature 9: Search History and Favorites
**Priority: 4** | Depends on: Features 2, 5

User profile page showing all past searches and favorited names.

- Route: `/history`
- List all past searches ordered by date (newest first)
- Each search card shows: description (truncated), date, number of suggestions, number of favorites
- Click to expand: shows all name suggestions with their latest availability and risk status
- Favorites section: aggregated list of all favorited names across all searches
- "Re-run Availability Check" button per search (prices and availability change over time)
- "Delete Search" button with confirmation dialog
- Export favorites as CSV: columns for name, best available TLD, price, risk score
- Pagination: 10 searches per page with "Load More" button
- Empty state: "No searches yet. Start by describing your app idea."

**Steps:**
1. Create `src/pages/HistoryPage.tsx` with search list and favorites section
2. Create `src/components/SearchHistoryCard.tsx` -- expandable search summary card
3. Create `src/components/FavoritesList.tsx` -- aggregated favorites across all searches
4. Create `src/hooks/useSearchHistory.ts` -- TanStack Query hook with pagination
5. Implement CSV export for favorites (`src/lib/exportCsv.ts`)
6. Implement search deletion with optimistic UI update
7. Implement re-run availability check (call the same Edge Function, update cached results)
8. Verify: view past searches, expand details, favorite/unfavorite names, export CSV, delete search

### Feature 10: Social Handle Checker
**Priority: 5** | Depends on: Features 3, 5

Check social media handle availability for each name suggestion.

- For each name suggestion, check if the handle is available on:
  - Twitter/X (`@name`)
  - Instagram (`@name`)
  - GitHub (`github.com/name`)
  - TikTok (`@name`)
- Display as platform icons with green check (available) or red X (taken)
- This is a **Pro feature** (included in $5-9/month plan)
- Free tier users see the icons grayed out with a lock: "Upgrade to Pro for social handle checking"
- Supabase Edge Function `check-social-handles`:
  - Twitter: check via API or scrape `twitter.com/{name}` for 404
  - Instagram: check via Graph API or scrape for 404
  - GitHub: `GET https://api.github.com/users/{name}` (404 = available)
  - TikTok: check via scrape `tiktok.com/@{name}` for 404
- Rate limited: check handles for top 10 names automatically, on-demand for others
- Results stored in the `social_handles` JSONB field of `threat_assessments`

**Steps:**
1. Create Supabase Edge Function `supabase/functions/check-social-handles/index.ts`
2. Create `src/lib/socialChecker.ts` with `checkSocialHandles(name: string)` function
3. Create `src/components/SocialHandleIcons.tsx` -- row of platform icons with status
4. Add Pro tier gate: check subscription status before allowing social handle checks
5. Integrate into the results dashboard name rows
6. Add "Check Handles" button for on-demand checking
7. Verify: check handles for a name, see green/red icons per platform, Pro gate works

### Feature 11: Mobile-Responsive UI + PWA
**Priority: 5** | Depends on: Features 5, 7, 9

Full mobile-responsive design and Progressive Web App support.

- Responsive design throughout all pages:
  - Search page: full-width textarea, large submit button
  - Results: stacked cards instead of table rows on mobile
  - History: single-column card list
  - Profile: stacked sections
- Touch-optimized interactions:
  - Large tap targets (minimum 44x44px)
  - Swipe to favorite (optional nice-to-have)
  - Pull-to-refresh on results and history pages
- PWA manifest for "Add to Home Screen":
  - `manifest.json` with app name, icons, theme color
  - Service worker for offline support (cached searches/favorites viewable offline)
  - Splash screen on iOS and Android
- Offline support: view saved searches and favorites without network
- Share results via native Web Share API where supported
- Font size: minimum 16px on mobile inputs to prevent iOS zoom

**Steps:**
1. Audit all pages for mobile responsiveness, fix any layout issues
2. Create `public/manifest.json` with PWA metadata and icons
3. Create service worker for offline caching of static assets and saved data
4. Register service worker in `src/main.tsx`
5. Add pull-to-refresh behavior on key pages
6. Add Web Share API integration for sharing results
7. Test on mobile viewports (375px, 414px, 768px)
8. Verify: install as PWA on mobile, view cached searches offline, share works

### Feature 12: Landing Page and Onboarding
**Priority: 6** | Depends on: Features 1, 2, 3

Marketing landing page and onboarding flow for new users.

- Hero section:
  - Headline: "Find the Perfect Domain for Your Next Idea"
  - Subtitle: "AI-powered name generation, instant availability checking, and brand risk assessment -- all in one place."
  - CTA button: "Start Free" --> sign up page
  - Secondary CTA: "See How It Works" --> scrolls to demo section
- Demo section:
  - Animated mockup showing the flow: describe idea --> get names --> see availability
  - Or a short embedded video placeholder
- Pricing section:
  - Three tier cards: Free / Per-Report / Pro
  - Free: "3 searches/day, availability check, basic risk assessment"
  - Per-Report: "$1.50 per deep dive report"
  - Pro: "$7/month for unlimited everything + social handle checking"
  - CTA on each: "Get Started Free" / "Pay As You Go" / "Go Pro"
- Social proof: "Join 500+ entrepreneurs who found their perfect domain"
- How it works: 4-step visual (Describe --> Generate --> Check --> Buy)
- FAQ section:
  - "Is the availability check real-time?" --> Yes, we check against the actual registrar API
  - "What registrars do you support?" --> Namecheap, Hostinger, GoDaddy
  - "Can I check domains I already thought of?" --> Coming soon (manual name input)
  - "Is my data private?" --> Yes, searches are only visible to your account
- Footer:
  - Affiliate disclosure (required by FTC): "Some links on this site are affiliate links. We may earn a commission if you purchase a domain through our links, at no extra cost to you."
  - Privacy policy link, Terms of service link
  - Copyright notice

**Steps:**
1. Create `src/pages/LandingPage.tsx` with all sections
2. Build hero section with headline, subtitle, and CTA buttons
3. Build demo/mockup section with animated flow illustration
4. Build pricing section with three tier cards
5. Build social proof bar
6. Build "How It Works" 4-step section with icons
7. Build FAQ section with expandable accordion items
8. Build footer with affiliate disclosure, legal links, copyright
9. Add smooth scroll behavior for "See How It Works" anchor link
10. Verify: landing page looks polished on desktop and mobile, all links work, CTAs navigate correctly

---

## Key UX Details

### Input Form Feel
The description textarea should feel like texting a friend, not filling out a corporate form. Placeholder text: "I'm building an app that helps diabetics track their sugar levels. It's aimed at people 50+ who aren't tech-savvy." Large, generous padding, conversational tone throughout.

### Results Feel
Results should feel like getting a curated list from a naming expert, not output from a random generator. Names are ranked by quality. Reasoning is visible. The dashboard feels like a professional report, not a wall of data.

### Risk Assessment Feel
The threat assessment should feel like having a lawyer briefly check things out for you. Clear, actionable language: "We found 2 businesses using this name, but both are in unrelated industries (flooring and pet food). Low risk for a health tech product." Not just raw data dumps.

### Buy Links Feel
Affiliate links should feel helpful, not salesy. Frame them as a service: "This domain is available for $11.98/yr on Namecheap (includes free WHOIS privacy)." The user should feel like we are helping them get the best deal, not pushing them toward a purchase.

### Mobile Experience
People get app ideas anywhere -- in the shower, on a commute, in a conversation. The mobile experience should support quick idea capture: open the app, type a description, get names, star your favorites. Come back later on desktop for the full deep dive.

---

## Supabase Edge Functions

All AI and external API calls go through Supabase Edge Functions. This keeps API keys server-side and enables rate limiting.

### `supabase/functions/generate-names/index.ts`
- Input: `{ description: string, user_id: string }`
- Checks daily usage limit
- Calls Claude Sonnet API with name generation prompt
- Parses response, inserts search + suggestions into database
- Returns search ID and suggestion list

### `supabase/functions/check-availability/index.ts`
- Input: `{ suggestion_ids: string[], names: string[] }`
- Checks cache (results < 24h old)
- Calls Namecheap API for uncached names
- Inserts/updates availability_results
- Returns all results

### `supabase/functions/assess-threats/index.ts`
- Input: `{ suggestion_id: string, name: string, product_description: string }`
- Calls SerpAPI for web search
- Checks npm registry and GitHub
- Calls Claude Sonnet for risk summarization
- Inserts threat_assessments
- Returns assessment

### `supabase/functions/check-social-handles/index.ts`
- Input: `{ name: string }`
- Checks Twitter, Instagram, GitHub, TikTok
- Returns handle availability per platform

### `supabase/functions/deep-dive/index.ts`
- Input: `{ suggestion_id: string, name: string, tld: string, payment_id: string }`
- Verifies Stripe payment
- Performs RDAP lookup
- Fetches domain, checks website activity
- Runs AI-powered company research
- Inserts deep_dives
- Returns full report

---

## File Structure

```
domain-finder/
+-- index.html                              # Meta tags, favicon
+-- .env.example                            # All environment variables documented
+-- package.json
+-- tsconfig.json
+-- vite.config.ts
+-- tailwind.config.ts
+-- public/
|   +-- manifest.json                       # PWA manifest
|   +-- icons/                              # PWA icons (192, 512)
|   +-- favicon.ico
+-- src/
|   +-- main.tsx                            # App entry point, service worker registration
|   +-- App.tsx                             # Router + QueryClient + AuthProvider
|   +-- router.tsx                          # Route definitions with ProtectedRoute
|   +-- styles/
|   |   +-- globals.css                     # Tailwind directives, base styles
|   +-- context/
|   |   +-- AuthContext.tsx                  # Supabase auth state
|   |   +-- ToastContext.tsx                 # Toast notification system
|   +-- components/
|   |   +-- Layout.tsx                      # Header, footer, Outlet
|   |   +-- ProtectedRoute.tsx              # Auth gate wrapper
|   |   +-- NameSuggestionRow.tsx           # Main result row per name
|   |   +-- NameDetailCard.tsx              # Expandable detail panel
|   |   +-- AvailabilityBadge.tsx           # Green/red/yellow TLD badge
|   |   +-- TLDBadgeRow.tsx                 # Row of 6 TLD badges
|   |   +-- RiskBadge.tsx                   # Green/yellow/red risk dot
|   |   +-- RiskReport.tsx                  # Expandable threat assessment card
|   |   +-- DeepDiveReport.tsx              # Full deep dive report card
|   |   +-- BuyButton.tsx                   # Affiliate purchase button
|   |   +-- RegistrarComparison.tsx         # Price comparison across registrars
|   |   +-- SocialHandleIcons.tsx           # Platform icons with availability
|   |   +-- PaymentButton.tsx               # Stripe checkout trigger
|   |   +-- FilterTabs.tsx                  # All / Available / Favorites
|   |   +-- SearchHistoryCard.tsx           # Past search summary card
|   |   +-- FavoritesList.tsx               # Aggregated favorites list
|   |   +-- Toast.tsx                       # Toast notification component
|   |   +-- LoadingSkeleton.tsx             # Shimmer placeholder
|   +-- pages/
|   |   +-- LandingPage.tsx                 # Marketing page + onboarding
|   |   +-- SignInPage.tsx                  # Email/password + Google OAuth
|   |   +-- SignUpPage.tsx                  # Registration form
|   |   +-- SearchPage.tsx                  # Description input + generate
|   |   +-- ResultsPage.tsx                 # Full results dashboard
|   |   +-- HistoryPage.tsx                 # Past searches + favorites
|   |   +-- ProfilePage.tsx                 # Account info + subscription
|   +-- hooks/
|   |   +-- useSearchResults.ts             # TanStack Query: search + suggestions + availability
|   |   +-- useSearchHistory.ts             # TanStack Query: paginated search history
|   |   +-- useDailyUsage.ts               # TanStack Query: free tier usage counter
|   +-- lib/
|   |   +-- supabase.ts                     # Supabase client initialization
|   |   +-- nameGenerator.ts               # generate-names Edge Function caller
|   |   +-- availabilityChecker.ts          # check-availability Edge Function caller
|   |   +-- threatAssessment.ts             # assess-threats Edge Function caller
|   |   +-- socialChecker.ts               # check-social-handles Edge Function caller
|   |   +-- deepDive.ts                     # deep-dive Edge Function caller
|   |   +-- payment.ts                      # Stripe checkout integration
|   |   +-- affiliateLinks.ts              # Affiliate URL generation
|   |   +-- affiliateTracking.ts           # Click tracking to Supabase
|   |   +-- exportCsv.ts                   # CSV export for favorites
|   +-- types/
|       +-- index.ts                        # All TypeScript interfaces
+-- supabase/
    +-- functions/
        +-- generate-names/
        |   +-- index.ts                    # AI name generation
        +-- check-availability/
        |   +-- index.ts                    # Namecheap API availability check
        +-- assess-threats/
        |   +-- index.ts                    # Web search + AI risk assessment
        +-- check-social-handles/
        |   +-- index.ts                    # Social platform handle checking
        +-- deep-dive/
            +-- index.ts                    # RDAP + AI company research report
```

---

## AutoForge Integration (Product B)

For embedding within AutoForge's project creation wizard:

### Integration Points

1. **New wizard step** after project naming in `ui/src/components/NewProjectModal.tsx`:
   - "Find a Domain?" optional step with skip button
   - Embeds the description input form inline
   - Shows condensed results in a panel/modal (not full dashboard)

2. **Shared backend**: calls the same Supabase Edge Functions as the standalone app

3. **Domain saved to project config**: selected domain written to `.autoforge/domain.json`:
   ```json
   {
     "name": "glucoease",
     "tld": ".app",
     "registrar": "namecheap",
     "purchased": false,
     "affiliate_link": "https://..."
   }
   ```

4. **Lightweight UI**: only the core flow (generate names --> check availability --> buy link). No search history, no deep dives, no social handles within AutoForge. Those are standalone app features.

### Files to Modify in AutoForge

- `ui/src/components/NewProjectModal.tsx` -- add domain step
- `ui/src/components/DomainFinderPanel.tsx` -- NEW: condensed domain finder UI
- `ui/src/lib/types.ts` -- add DomainConfig type
- `server/routers/projects.py` -- save domain config to project directory

---

## Revenue Projections (Conservative)

Based on 1,000 monthly active users:

| Revenue Stream | Conversion | Unit Revenue | Monthly Total |
|---------------|------------|-------------|---------------|
| Deep dive reports | 30% run at least one | $1.50 avg per report | $450 |
| Affiliate clicks | 10% click, 50% buy | $3.00 avg commission | $150 |
| Pro subscriptions | 5% subscribe | $7.00/month | $350 |
| **Total** | | | **~$950/month** |

### Growth Levers

- **SEO**: "domain name generator", "business name finder" are high-volume search terms
- **Content marketing**: blog posts about naming best practices, domain buying guides
- **Referral program**: give Pro users a referral link, both get 1 month free
- **API/white-label**: let other tools use the name generation pipeline
- **Premium reports**: $5-10 for enterprise-grade brand analysis with full trademark search

---

## Implementation Priority Order

For fastest time-to-revenue, build in this order:

1. **Scaffolding + Auth** (Features 1, 2) -- foundation
2. **Name Generator + Availability** (Features 3, 4) -- core value proposition
3. **Results Dashboard + Affiliate Links** (Features 5, 8) -- revenue from day one via affiliate links
4. **Threat Assessment** (Feature 6) -- differentiator that justifies the tool's existence
5. **Deep Dive Reports** (Feature 7) -- paid feature, direct revenue
6. **Search History** (Feature 9) -- retention, repeat usage
7. **Social Handles** (Feature 10) -- Pro tier upgrade incentive
8. **PWA + Mobile** (Feature 11) -- mobile capture, wider reach
9. **Landing Page** (Feature 12) -- marketing, SEO, conversion

Features 1-5 and 8 should be the MVP. Everything else is iteration.

---

## API Cost Estimates Per Search

| API Call | Cost | Calls Per Search |
|----------|------|------------------|
| Claude Sonnet (name generation) | ~$0.02 | 1 |
| Namecheap (availability, 30 names x 6 TLDs) | Free (reseller) | ~180 |
| SerpAPI (threat assessment, 10 names) | ~$0.10 | 10 |
| Claude Sonnet (threat summarization, 10 names) | ~$0.05 | 10 |
| **Total per search** | **~$0.17** | |
| **Deep dive (per report)** | **~$0.05** | 1 |

At $0.17 per search with 3 free searches/day, a heavy free user costs ~$0.51/day or ~$15/month. Pro users at $7/month become profitable after ~41 searches/month (roughly 1.4/day). Affiliate revenue and deep dive purchases more than cover the cost for free tier users.

---

## Security Considerations

- All API keys stored as Supabase Edge Function secrets (never exposed to client)
- Supabase anon key is safe for client-side use (RLS policies control access)
- Rate limiting enforced server-side in Edge Functions (not client-side)
- Input sanitization: description text validated for length and stripped of HTML
- RDAP data may contain personal information -- only display registration dates and registrar, not registrant contact info
- Affiliate link tracking is for analytics only -- no PII stored beyond user_id
- FTC affiliate disclosure required on every page with buy links
- GDPR considerations: search history deletion must cascade through all related tables (ON DELETE CASCADE handles this in schema)
