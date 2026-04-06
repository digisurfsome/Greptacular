# Skill Library — Repo Structure

This document defines the folder structure, key files, and delivery model for the Claude Code Skills Library product. Skills are curated Claude Code skill files backed by Context7 documentation. The product is NOT a public GitHub repo — buyers access skills through a dashboard or CLI tool.

---

## 1. Internal Repo Structure (Your Private Repo)

This is the private repo that only you control. Buyers never see this structure directly.

```
skill-library/
├── README.md                          # Internal docs: how to add/update skills
├── skill-versions.json                # Version tracking for every skill (see section 2)
├── skills/                            # All skill files, organized by category
│   ├── frameworks/
│   │   ├── next-js-app-router.md
│   │   ├── nuxt-4.md
│   │   ├── sveltekit.md
│   │   ├── remix.md
│   │   └── astro.md
│   ├── ui/
│   │   ├── react-19.md
│   │   ├── vue-3.md
│   │   └── svelte-5.md
│   ├── styling/
│   │   ├── tailwind-css-v4.md
│   │   └── css-modules.md
│   ├── auth/
│   │   ├── supabase-auth.md
│   │   ├── clerk-auth.md
│   │   ├── auth-js.md
│   │   └── firebase-auth.md
│   ├── database/
│   │   ├── supabase-database.md
│   │   ├── drizzle-orm.md
│   │   ├── prisma.md
│   │   └── convex.md
│   ├── components/
│   │   ├── shadcn-ui.md
│   │   ├── radix-ui.md
│   │   └── headless-ui.md
│   ├── payments/
│   │   ├── stripe-payments.md
│   │   └── lemonsqueezy.md
│   ├── analytics/
│   │   ├── posthog.md
│   │   └── plausible.md
│   ├── email/
│   │   ├── resend.md
│   │   ├── sendgrid.md
│   │   └── loops-so.md
│   ├── storage/
│   │   ├── supabase-storage.md
│   │   ├── uploadthing.md
│   │   └── cloudflare-r2.md
│   ├── testing/
│   │   ├── playwright.md
│   │   ├── vitest.md
│   │   └── cypress.md
│   ├── deployment/
│   │   ├── vercel.md
│   │   ├── netlify.md
│   │   ├── railway.md
│   │   ├── cloudflare-workers.md
│   │   └── docker.md
│   ├── mobile/
│   │   ├── flutter.md
│   │   └── react-native-expo.md
│   ├── state/
│   │   ├── zustand.md
│   │   ├── tanstack-query.md
│   │   ├── jotai.md
│   │   └── riverpod.md
│   ├── realtime/
│   │   ├── supabase-realtime.md
│   │   ├── socket-io.md
│   │   └── pusher.md
│   ├── devtools/
│   │   ├── typescript-5.md
│   │   ├── eslint-flat-config.md
│   │   ├── prettier.md
│   │   ├── turborepo.md
│   │   └── pnpm.md
│   ├── api-backend/
│   │   ├── trpc.md
│   │   ├── hono.md
│   │   ├── fastapi.md
│   │   └── supabase-edge-functions.md
│   └── ai-ml/
│       ├── anthropic-sdk.md
│       ├── openai-sdk.md
│       ├── vercel-ai-sdk.md
│       └── langchain.md
├── bundles/                           # Pre-defined skill bundles (see section 3)
│   ├── web-saas-d2d.json
│   ├── mobile-flutter.json
│   ├── full-stack-dual.json
│   └── indie-hacker-minimal.json
└── .github/
    └── workflows/
        └── update-skills.yml          # Weekly version check (see section 4)
```

---

## 2. skill-versions.json (Example)

This file tracks the exact library version each skill was generated against. When a library ships a major or minor update, the skill may need regeneration via Context7 MCP.

```json
{
  "schema_version": 1,
  "skills": [
    {
      "skill_name": "next-js-app-router",
      "library": "next",
      "npm_package": "next",
      "version_when_generated": "15.3.1",
      "generation_date": "2026-03-28",
      "context7_library_id": "/vercel/next.js",
      "last_checked_date": "2026-04-06"
    },
    {
      "skill_name": "react-19",
      "library": "react",
      "npm_package": "react",
      "version_when_generated": "19.1.0",
      "generation_date": "2026-03-25",
      "context7_library_id": "/facebook/react",
      "last_checked_date": "2026-04-06"
    },
    {
      "skill_name": "tailwind-css-v4",
      "library": "tailwindcss",
      "npm_package": "tailwindcss",
      "version_when_generated": "4.1.3",
      "generation_date": "2026-03-20",
      "context7_library_id": "/tailwindlabs/tailwindcss",
      "last_checked_date": "2026-04-06"
    },
    {
      "skill_name": "supabase-auth",
      "library": "@supabase/supabase-js",
      "npm_package": "@supabase/supabase-js",
      "version_when_generated": "2.49.4",
      "generation_date": "2026-03-22",
      "context7_library_id": "/supabase/supabase-js",
      "last_checked_date": "2026-04-06"
    },
    {
      "skill_name": "flutter",
      "library": "flutter",
      "pub_package": "flutter",
      "version_when_generated": "3.29.3",
      "generation_date": "2026-03-18",
      "context7_library_id": "/flutter/flutter",
      "last_checked_date": "2026-04-06"
    }
  ]
}
```

**Field reference:**

| Field | What it means |
|-------|---------------|
| `skill_name` | The filename (without `.md`) in the `skills/` folder |
| `library` | Human-readable library name |
| `npm_package` | The npm package to check for version updates (omit for non-npm) |
| `pub_package` | The pub.dev package to check (for Dart/Flutter skills) |
| `version_when_generated` | The exact version the skill was generated against |
| `generation_date` | When the skill file was last regenerated via Context7 |
| `context7_library_id` | The Context7 MCP library identifier used during generation |
| `last_checked_date` | When the version check last ran (updated by GitHub Action) |

---

## 3. Bundle Definitions

Bundles are pre-selected groups of skills for common use cases. Each bundle is a JSON file listing the included skill names.

### web-saas-d2d.json

The D2D web boilerplate stack — everything you need for a production SaaS.

```json
{
  "bundle_name": "web-saas-d2d",
  "display_name": "Web SaaS (D2D Stack)",
  "description": "Full-stack SaaS boilerplate: Next.js App Router, Supabase, Stripe, and all the trimmings.",
  "skills": [
    "next-js-app-router",
    "react-19",
    "tailwind-css-v4",
    "shadcn-ui",
    "radix-ui",
    "supabase-auth",
    "supabase-database",
    "stripe-payments",
    "posthog",
    "vercel",
    "typescript-5",
    "eslint-flat-config",
    "tanstack-query",
    "supabase-edge-functions",
    "supabase-storage",
    "resend"
  ]
}
```

### mobile-flutter.json

```json
{
  "bundle_name": "mobile-flutter",
  "display_name": "Mobile (Flutter)",
  "description": "Flutter mobile app stack with Supabase backend and Firebase auth fallback.",
  "skills": [
    "flutter",
    "riverpod",
    "supabase-auth",
    "supabase-database",
    "supabase-storage",
    "firebase-auth"
  ]
}
```

### full-stack-dual.json

```json
{
  "bundle_name": "full-stack-dual",
  "display_name": "Full-Stack Dual (Web + Mobile)",
  "description": "Web SaaS D2D stack plus Flutter mobile — every skill you need for both platforms, deduplicated.",
  "skills": [
    "next-js-app-router",
    "react-19",
    "tailwind-css-v4",
    "shadcn-ui",
    "radix-ui",
    "supabase-auth",
    "supabase-database",
    "stripe-payments",
    "posthog",
    "vercel",
    "typescript-5",
    "eslint-flat-config",
    "tanstack-query",
    "supabase-edge-functions",
    "supabase-storage",
    "resend",
    "flutter",
    "riverpod",
    "firebase-auth"
  ]
}
```

### indie-hacker-minimal.json

```json
{
  "bundle_name": "indie-hacker-minimal",
  "display_name": "Indie Hacker (Minimal)",
  "description": "Lean SaaS stack — just the essentials to ship fast with zero bloat.",
  "skills": [
    "next-js-app-router",
    "react-19",
    "tailwind-css-v4",
    "shadcn-ui",
    "supabase-auth",
    "supabase-database",
    "stripe-payments",
    "vercel"
  ]
}
```

---

## 4. GitHub Action: update-skills.yml

This workflow runs every Sunday at midnight. It checks each skill's underlying library for version updates and creates a GitHub issue if any skills are stale.

```yaml
# .github/workflows/update-skills.yml
#
# WHAT THIS DOES:
# Every Sunday at midnight, this workflow checks whether the libraries
# behind your skills have released new versions. If a library shipped a
# new MAJOR or MINOR version (not just a patch), it flags that skill as
# stale and opens a GitHub issue listing everything that needs updating.
#
# WHY:
# Skills are generated against a specific library version. When the library
# changes significantly, the skill may contain outdated patterns or miss
# new features. This workflow catches that drift automatically.
#
# NOTE:
# This does NOT regenerate skills automatically. That would require calling
# Context7 MCP, which is a future enhancement. For now, a human reviews
# the issue and regenerates manually.

name: Check Skill Versions

# Run every Sunday at midnight UTC
on:
  schedule:
    - cron: '0 0 * * 0'
  # Also allow manual trigger from the GitHub Actions tab
  workflow_dispatch:

jobs:
  check-versions:
    runs-on: ubuntu-latest

    steps:
      # Step 1: Check out the repo so we can read skill-versions.json
      - name: Checkout repository
        uses: actions/checkout@v4

      # Step 2: Set up Node.js (needed to query the npm registry)
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      # Step 3: Run the version check script
      # This reads skill-versions.json, queries npm/pub.dev for each
      # package, and compares the latest version against what the skill
      # was generated with. Only MAJOR or MINOR bumps are flagged
      # (patch bumps like 1.2.3 -> 1.2.4 are ignored).
      - name: Check for stale skills
        id: check
        run: |
          cat << 'SCRIPT' > check-versions.mjs
          import { readFileSync } from 'fs';

          // Read the version tracking file
          const data = JSON.parse(readFileSync('skill-versions.json', 'utf-8'));
          const stale = [];
          const today = new Date().toISOString().split('T')[0];

          // Helper: compare major.minor between two semver strings
          // Returns true if the latest version has a higher major or minor number
          function hasSignificantUpdate(current, latest) {
            const [curMajor, curMinor] = current.split('.').map(Number);
            const [latMajor, latMinor] = latest.split('.').map(Number);
            return latMajor > curMajor || (latMajor === curMajor && latMinor > curMinor);
          }

          // Helper: fetch the latest version from npm registry
          async function getLatestNpm(packageName) {
            const url = `https://registry.npmjs.org/${packageName}/latest`;
            const res = await fetch(url);
            if (!res.ok) return null;
            const json = await res.json();
            return json.version;
          }

          // Helper: fetch the latest version from pub.dev (for Dart/Flutter packages)
          async function getLatestPub(packageName) {
            const url = `https://pub.dev/api/packages/${packageName}`;
            const res = await fetch(url);
            if (!res.ok) return null;
            const json = await res.json();
            return json.latest?.version ?? null;
          }

          // Check each skill
          for (const skill of data.skills) {
            let latestVersion = null;

            // Determine which registry to check
            if (skill.npm_package) {
              latestVersion = await getLatestNpm(skill.npm_package);
            } else if (skill.pub_package) {
              latestVersion = await getLatestPub(skill.pub_package);
            } else {
              // No package registry to check — skip this skill
              console.log(`SKIP: ${skill.skill_name} — no package registry configured`);
              continue;
            }

            if (!latestVersion) {
              console.log(`WARN: ${skill.skill_name} — could not fetch latest version`);
              continue;
            }

            const registry = skill.npm_package ? 'npm' : 'pub.dev';

            if (hasSignificantUpdate(skill.version_when_generated, latestVersion)) {
              console.log(`STALE: ${skill.skill_name} — generated against ${skill.version_when_generated}, latest is ${latestVersion} (${registry})`);
              stale.push({
                name: skill.skill_name,
                library: skill.library,
                generated: skill.version_when_generated,
                latest: latestVersion,
                registry,
                context7_id: skill.context7_library_id,
              });
            } else {
              console.log(`OK: ${skill.skill_name} — ${skill.version_when_generated} is current (latest: ${latestVersion})`);
            }
          }

          // Write results to files that later steps can read
          // (GitHub Actions passes data between steps via files)
          const count = stale.length;
          const fs = await import('fs');
          fs.writeFileSync('/tmp/stale-count.txt', String(count));
          fs.writeFileSync('/tmp/stale-skills.json', JSON.stringify(stale, null, 2));

          if (count > 0) {
            console.log(`\n${count} skill(s) need updating.`);
          } else {
            console.log('\nAll skills are up to date.');
          }
          SCRIPT

          node check-versions.mjs

          # Pass the stale count to the next step
          echo "stale_count=$(cat /tmp/stale-count.txt)" >> "$GITHUB_OUTPUT"

      # Step 4: If any skills are stale, create a GitHub issue listing them
      # This only runs if the previous step found at least one stale skill.
      - name: Create GitHub issue for stale skills
        if: steps.check.outputs.stale_count != '0'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const stale = JSON.parse(fs.readFileSync('/tmp/stale-skills.json', 'utf-8'));
            const today = new Date().toISOString().split('T')[0];

            // Build a markdown table of stale skills
            let body = `## Stale Skills Detected (${today})\n\n`;
            body += `The weekly version check found **${stale.length} skill(s)** generated against outdated library versions.\n\n`;
            body += `| Skill | Library | Generated Against | Latest | Registry | Context7 ID |\n`;
            body += `|-------|---------|-------------------|--------|----------|-------------|\n`;

            for (const s of stale) {
              body += `| ${s.name} | ${s.library} | ${s.generated} | ${s.latest} | ${s.registry} | \`${s.context7_id}\` |\n`;
            }

            body += `\n### Next Steps\n\n`;
            body += `1. For each stale skill, regenerate the \`.md\` file using Context7 MCP with the latest docs\n`;
            body += `2. Update \`skill-versions.json\` with the new version and generation date\n`;
            body += `3. Test the updated skill in a Claude Code session to verify it works\n`;
            body += `4. Close this issue when all skills are updated\n`;

            // Create the issue
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[Skill Update] ${stale.length} skill(s) need regeneration (${today})`,
              body,
              labels: ['skill-update', 'automated'],
            });

      # Step 5: Update the last_checked_date in skill-versions.json
      # so we have a record of when the check last ran
      - name: Update last checked dates
        run: |
          cat << 'SCRIPT' > update-dates.mjs
          import { readFileSync, writeFileSync } from 'fs';

          const today = new Date().toISOString().split('T')[0];
          const data = JSON.parse(readFileSync('skill-versions.json', 'utf-8'));

          // Update every skill's last_checked_date to today
          for (const skill of data.skills) {
            skill.last_checked_date = today;
          }

          writeFileSync('skill-versions.json', JSON.stringify(data, null, 2) + '\n');
          console.log(`Updated last_checked_date to ${today} for ${data.skills.length} skills.`);
          SCRIPT

          node update-dates.mjs

      # Step 6: Commit the updated dates back to the repo
      - name: Commit updated dates
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add skill-versions.json
          git diff --cached --quiet || git commit -m "chore: update skill version check dates"
          git push
```

---

## 5. Delivery Model

Three tiers, from simplest to most sophisticated. Each builds on the previous one.

### MVP (Day 1) — Password-Protected Page

The fastest way to start selling. No code required.

**How it works:**
- Host skills on a password-protected Notion page, Gumroad product, or simple static site
- Skills are listed individually. Buyer clicks one, copies the markdown
- Free tier: "Pick 3 skills, enter your email, get them emailed to you." This builds your email list while giving people a taste of the product
- Paid tier: one-time purchase or monthly subscription unlocks full access to the page

**Pros:** Ship in a day. Zero infrastructure. Test demand before building anything.

**Cons:** No access control per skill. Hard to watermark. Easy to screenshot and share.

### V2 (Week 2-4) — Dashboard

A proper web app built with the D2D boilerplate (Next.js + Supabase + Stripe).

**How it works:**
- Buyer creates an account, logs in, browses skills by category
- Each skill has a "Copy to Clipboard" button (no raw file downloads)
- Subscription check via Stripe: free users see 3 skills, paid users see all
- "Pick 3 free" onboarding flow built into the signup process
- Skills are served from a database, not static files — you push updates and buyers see them instantly

**Pros:** Real access control. Per-skill analytics (which skills are popular?). Watermarking possible. Subscription revenue.

**Cons:** Requires building and hosting a web app. Buyers can still copy-paste and share.

### V3 (Month 2+) — Branded CLI Tool

The defensible moat. This is what makes the product hard to replicate.

**How it works:**
- Buyer installs via `npx skillstack install next-js-app-router`
- The CLI authenticates with an API key tied to the buyer's active subscription
- Skills are delivered one at a time to the local `.claude/skills/` directory
- Auto-update: when you regenerate a skill, buyers get the latest version on next install
- No bulk download endpoint. No zip files. One skill per request.

**Pros:** Impossible to bulk-scrape. Subscription enforcement at the CLI level. Seamless developer experience. Auto-updates are a genuine value-add.

**Cons:** Requires building a CLI, an API, and auth infrastructure. Buyers must have an active subscription to access skills (which is the point, but some will complain).

---

## 6. Anti-Piracy Notes

These are the rules that protect the business. Every delivery mechanism must enforce them.

1. **Never deliver a full repo or zip file.** Skills are accessed individually — one at a time, through the dashboard or CLI. There is no "download all" button, no export, no archive endpoint.

2. **Individual skill access only.** Even paid subscribers retrieve skills one by one. The API does not support batch downloads.

3. **Rate limit: max 5 skill downloads per hour.** This prevents automated scraping. A real user installing skills one at a time will never hit this limit. A scraper will.

4. **Watermark each skill with the buyer's email.** Every skill file delivered to a buyer includes a comment at the bottom:
   ```
   <!-- Licensed to buyer@example.com — not for redistribution -->
   ```
   If a pirated skill surfaces online, you can trace it back to the leaker.

5. **CLI auth tokens expire and require active subscription.** Tokens are short-lived (30 days). When the subscription lapses, the token stops working. Buyers must maintain their subscription to keep accessing skills. Previously downloaded skills continue to work (they are just markdown files), but they will not receive updates.

6. **Terms of service: skills are for personal use, not redistribution.** Make this explicit in the purchase flow. Skills are licensed per-seat. Sharing, reselling, or publishing them is a violation. This gives you legal recourse if watermarked skills appear on competitor sites.
