# Skill Library — Master Game Plan

> Last updated: 2026-04-06

---

## What We're Building

A curated library of **~60 Claude Code skills** covering the most popular web and mobile development libraries. Each skill is a `.md` file that lives in `.claude/skills/` and teaches Claude Code how to use a specific library correctly — using **real, current documentation** pulled by Context7.

This is not generic AI slop. Every skill is generated from the actual library docs via Context7, reviewed for quality, and kept up to date automatically. That is the product differentiator.

---

## The Product

| Tier | What They Get | Price |
|------|--------------|-------|
| **Free** | Pick any 3 skills (email gate) | $0 |
| **Monthly** | Full library + updates | $9/mo |
| **Lifetime** | Full library + updates forever | $79 one-time |

**Delivery method:** Buyers get access to a private GitHub repo. They clone it and run a one-line install script that copies the skills they want into their project's `.claude/skills/` folder. Monthly/lifetime subscribers get the full repo; free users get a download link for their 3 picks.

---

## Why This Works (Marketing Angle)

1. **Context7 credibility.** Every skill is generated from real-time library docs, not training data. That means the patterns are current — not 18 months stale.
2. **Time savings.** Instead of spending 20 minutes writing a skill file for each library, developers get production-ready skills in seconds.
3. **Stack bundles.** Pre-built bundles (Web SaaS, Flutter Mobile, Full Stack Dual, Indie Hacker) let buyers get their entire stack covered in one click.
4. **Auto-updates.** A GitHub Action checks for library version changes weekly and flags skills that need regeneration. Subscribers always have current skills.

---

## How the Repo Is Organized

```
skill-library/
  skills/           <- All 60+ skill files, organized by category
    frameworks/     <- Next.js, Nuxt, SvelteKit, Remix, Astro
    ui/             <- React, Vue, Svelte
    styling/        <- Tailwind, CSS Modules
    components/     <- shadcn/ui, Radix, Headless UI
    auth/           <- Supabase Auth, Clerk, Auth.js, Firebase Auth
    database/       <- Supabase DB, Drizzle, Prisma, Convex
    payments/       <- Stripe, LemonSqueezy
    analytics/      <- PostHog, Plausible
    email/          <- Resend, SendGrid, Loops.so
    storage/        <- Supabase Storage, UploadThing, Cloudflare R2
    testing/        <- Playwright, Vitest, Cypress
    deployment/     <- Vercel, Netlify, Railway, Cloudflare Workers, Docker
    mobile/         <- Flutter, React Native + Expo
    state/          <- Zustand, TanStack Query, Jotai, Riverpod
    realtime/       <- Supabase Realtime, Socket.io, Pusher
    devtools/       <- TypeScript, ESLint, Prettier, Turborepo, pnpm
    api-backend/    <- tRPC, Hono, FastAPI
    ai-ml/          <- Anthropic SDK, OpenAI SDK, Vercel AI SDK, LangChain
  bundles/          <- Pre-built skill sets for common stacks
  install.sh        <- One-line installer
  skill-versions.json  <- Version tracking for auto-updates
```

See `REPO-STRUCTURE.md` for the full breakdown including file contents.

---

## Generation Process (High Level)

This is the loop you follow to build the entire library. Detailed steps are in `GENERATION-GUIDE.md`.

### One-Time Setup
1. Install Context7: `npm install -g ctx7`
2. Make sure Claude Code is installed and working

### For Each Skill (repeat ~60 times)
1. Open your terminal
2. Run `npx ctx7 skills generate`
3. Paste the exact prompt from `MASTER-SKILL-LIST.md` for that skill
4. Answer any clarifying questions (the guide tells you what to pick)
5. Review the generated skill against `SKILL-TEMPLATE.md`
6. Save it to the correct category folder
7. Check it off in your tracking spreadsheet

### After All Skills Are Generated
1. Run the quality check pass (see Generation Guide)
2. Create the bundle JSON files
3. Set up the GitHub Action for auto-updates
4. Push to the private repo

---

## How Updates Work

### Version Tracking

The file `skill-versions.json` tracks what library version each skill was generated against:

```json
{
  "next-js-app-router": { "library": "next", "version": "16.2.0", "generated": "2026-04-06" },
  "tailwind-css-v4": { "library": "tailwindcss", "version": "4.1.0", "generated": "2026-04-06" }
}
```

### Automatic Checks

A GitHub Action runs weekly:
1. Checks npm/pub for the latest version of each tracked library
2. Compares against `skill-versions.json`
3. If a library has a new major or minor version, it opens a GitHub Issue flagging which skills need regeneration
4. You regenerate those skills using the same prompt from `MASTER-SKILL-LIST.md`, update the version in `skill-versions.json`, and push

### Manual Regeneration

If a library ships a breaking change or you hear about new patterns:
1. Find the skill in `MASTER-SKILL-LIST.md`
2. Run the generation command with the prompt
3. Replace the old skill file
4. Update `skill-versions.json`
5. Push to repo — subscribers get the update on next `git pull`

---

## Revenue Projections

Conservative estimates based on the Claude Code ecosystem:

| Scenario | Monthly Subs | Lifetime Sales | Monthly Revenue |
|----------|-------------|----------------|-----------------|
| Low | 50 | 10/mo | $1,240 |
| Medium | 200 | 30/mo | $4,170 |
| High | 500 | 50/mo | $8,450 |

The lifetime tier front-loads revenue. The monthly tier builds recurring income. The free tier (3 picks for email) builds the list for upsells.

---

## Launch Checklist

- [ ] Generate all P1 skills (25 skills)
- [ ] Generate all P2 skills (27 skills)
- [ ] Generate all P3 skills (12 skills)
- [ ] Quality check every skill against the template
- [ ] Create all 4 bundle JSON files
- [ ] Write the README for the repo
- [ ] Set up the install script
- [ ] Set up the GitHub Action for version checks
- [ ] Create the landing page
- [ ] Set up Stripe for $9/mo and $79 lifetime
- [ ] Set up email gate for free tier (3 picks)
- [ ] Create the private GitHub repo
- [ ] Announce on Twitter/X, Reddit, Hacker News

---

## File Index

| File | Purpose |
|------|---------|
| `GAME-PLAN.md` | This file — the master plan |
| `SKILL-TEMPLATE.md` | What every generated skill should look like |
| `GENERATION-GUIDE.md` | Step-by-step instructions for generating skills |
| `MASTER-SKILL-LIST.md` | All ~60 skills with exact prompts |
| `REPO-STRUCTURE.md` | The skill library repo structure with file contents |
