# Sequential Build Briefing for Fresh Agent

## CRITICAL: Read This Before Starting

### What This Task Is
Produce 5 Exact Reality Sheets for the DevToDollars web boilerplate. These are documentation files (markdown), NOT code.

### Why Sequential Matters
The previous agent tried to parallelize this across 5 sub-agents. That's WRONG. The sheets diverged — different wording, different interpretations, inconsistent tagging. **One agent must build all 5 sheets in order**, because each sheet builds on the previous one:

1. **Sheet 1: `web_base.md`** — Write this FIRST. Go through ALL 192 Martin rules + 71 industry standards + 14 mechanisms + 43 banned patterns. Tag DB/Auth/Payments rules as `PRESENT_NOT_WIRED`. This is 800+ lines and takes the most work.
2. **Sheet 2: `web_autoforge.md`** — Copy Sheet 1 as your starting point. Add the AutoForge connection section. Change relevant rules. Save.
3. **Sheet 3: `web_db.md`** — Copy Sheet 1 as your starting point. Change DB rules from `PRESENT_NOT_WIRED` to `EXACT`/`ADAPTED`. Save.
4. **Sheet 4: `web_db_auth.md`** — Copy Sheet 3 as your starting point. Change Auth rules from `PRESENT_NOT_WIRED` to `EXACT`/`ADAPTED`. Save.
5. **Sheet 5: `web_db_auth_payments.md`** — Copy Sheet 4 as your starting point. Change Payments rules from `PRESENT_NOT_WIRED` to `EXACT`/`ADAPTED`. Save. This is the full SaaS sheet.

**Save each file before moving to the next.** The voice, format, and rule entries must be consistent across all 5.

---

## The AutoForge Connection (Sheet 2) — BOLTED, NOT WELDED

The owner's exact words: "bolted not welded." Here's what that means:

### Concept
Think of it like a guitar plugging into an amp. The guitar (your app) is its own standalone instrument. The amp (AutoForge) provides power (auth, DB, subscription). The cable (SDK) connects them. You can unplug anytime and plug into a different amp (standalone Supabase/Stripe).

### How It Works Technically
- The app is a standard Next.js app built on the DevToDollars boilerplate
- It connects to AutoForge via the **Claude Agent SDK subscription model** (NOT API keys)
- This is the same pattern all existing AutoForge pages use (see `server/services/workspace_chat_session.py` for the SDK client pattern)
- Connection is through the SDK — the app calls AutoForge's API on port 8888
- Auth comes from AutoForge's session (Claude subscription OAuth)
- DB comes from AutoForge's SQLite/SQLAlchemy backend
- Subscription/billing comes from AutoForge (Claude Max subscription)

### The Key Principle: Minimal Coupling
- The app is its own standalone Next.js unit with its own `package.json`, its own routes, its own components
- The AutoForge connection is isolated to a small adapter layer (e.g., `utils/autoforge/client.ts`)
- The standalone Supabase/Stripe code stays in the boilerplate but is dormant (`PRESENT_NOT_WIRED`)
- To disconnect from AutoForge and make a standalone SaaS: delete the adapter, wire up Supabase/Stripe (use Sheet 5's instructions)

### Why Not Welded
The existing AutoForge pages (WorkspacePage, DashboardPage, etc.) are welded — they import AutoForge components directly, use AutoForge's router, live inside AutoForge's UI. You can't extract them into a standalone app.

The boilerplate approach is different: the app is always a complete, self-contained Next.js app. AutoForge is just a backend it talks to. Swap the backend, the app still works.

### SDK Subscription Model (NOT API Keys)
From the main CLAUDE.md — this is NON-NEGOTIABLE:
- All Claude models → subscription auth only
- `force_subscription=True` in `registry.py`
- The SDK clears `ANTHROPIC_API_KEY` and uses `~/.claude/.credentials.json` (subscription OAuth)
- Permission mode: `"acceptEdits"` + settings file (NEVER `"bypassPermissions"`)
- Wrap `receive_response()` in try/except for rate_limit_event recovery

---

## Files to Read (In This Order)

1. `docs/page-prds/prd-maker/boilerplates/handoffs/agent-a-web-handoff.md` — Full instructions
2. `docs/page-prds/prd-maker/boilerplates/prd-stage-0a-boilerplate-matching.md` — Output format
3. `docs/page-prds/prd-maker/martin-agnostic-checklist.md` — 192 rules (READ IN SECTIONS, file is large)
4. `docs/page-prds/prd-maker/industry-standards-checklist.md` — 71 rules (READ IN SECTIONS)
5. `docs/page-prds/prd-maker/skills/stage-00-technical-foundation/references/mechanism-categories.md` — 14 categories

## Boilerplate Repo to Clone and Explore
```
git clone https://github.com/digisurfsome/Web-BoilerPlate-D2D.git /tmp/Web-BoilerPlate-D2D
```

The Next.js app is in the `nextjs/` directory. Key files to read:
- `nextjs/package.json` — Dependencies (Next.js 16.1.6, React 19, Tailwind v4, Supabase, Stripe, shadcn/ui, lucide-react, next-themes, PostHog)
- `nextjs/tsconfig.json` — TypeScript strict mode, path aliases
- `nextjs/app/layout.tsx` — Root layout with ThemeProvider (next-themes), PostHog, Toaster
- `nextjs/app/page.tsx` — Landing page
- `nextjs/app/account/page.tsx` — Account page (protected, shows subscription)
- `nextjs/app/auth/[id]/page.tsx` — Auth pages (signin/signup/forgot/reset/verify)
- `nextjs/app/api/auth_callback/route.ts` — OAuth callback
- `nextjs/utils/supabase/` — client.ts, server.ts, admin.ts, middleware.ts, queries.ts, api.ts
- `nextjs/utils/types.ts` — AuthState enum, types
- `nextjs/utils/helpers.ts` — getURL(), postData(), date helpers
- `nextjs/types_db.ts` — Auto-generated Supabase DB types (users, customers, products, prices, subscriptions, checkout_sessions)
- `nextjs/schema.sql` — Full PostgreSQL schema with RLS policies
- `nextjs/styles/main.css` — Tailwind v4 with CSS variables (oklch colors), semantic tokens, animations
- `nextjs/components/ui/` — shadcn/ui components
- `nextjs/components/landing/` — Landing page components including Pricing.tsx
- `nextjs/components/misc/` — AccountPage.tsx, AuthForm.tsx
- `supabase/functions/` — Stripe webhook, get_stripe_url, on_user_modify edge functions
- `supabase/migrations/` — Initial DB migration
- `.env.example` — Required env vars

## For AutoForge Context (Sheet 2 Only)
Also read:
- `/home/user/Greptacular/CLAUDE.md` — AutoForge architecture (especially SDK auth section)
- `server/main.py` — How routers register
- `ui/src/App.tsx` — How pages route
- `ui/WORKSPACE_STANDARDS.md` — Layout standards

## Output Directory
Write all 5 sheets to: `docs/page-prds/prd-maker/boilerplates/final/`

## Commit Hash
The boilerplate commit is: `6a8d545`

---

## Match Tags
- `EXACT` — boilerplate implements this exactly
- `ADAPTED` — principle applies, implementation differs (document how)
- `NOT_PRESENT` — boilerplate doesn't have this; agent builds from scratch
- `PRESENT_NOT_WIRED` — code exists in boilerplate but is dormant
- `NOT_ACTIVATED` — toggled off for this variant
