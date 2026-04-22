# Astro Theme Generator — PRD

> **Product:** Theme DNA Generator — Screenshot/URL → Complete Website Theme
> **Status:** Pipeline built, demo working, WordPress plugin scaffolded. Ready for live WordPress test + Stripe integration.
> **Branch (Prompted-Flows):** `claude/explain-codebase-mm30emi7o66xbpke-F0QtL`

---

## 📄 Full Session Documentation
> **All details, architecture decisions, built files, marketing strategy, and next steps are in the info doc:**
> **→ `docs/info/theme-dna-session-worksheet.md`**
> That doc also contains a complete index of all related AutoForge files at the bottom (Section 13).

---

## Product Summary

**What it is:** A SaaS tool that extracts a website's "Design DNA" (colors, fonts, spacing, component styles) from a URL or screenshot and generates a complete, deployable website theme — either Astro or WordPress/Elementor format.

**The pitch:** "Paste a URL. Get a complete website."

**Core differentiator:** DOM-first extraction (free, exact values) + Claude Vision fallback only when needed. Avg cost per generation: ~$0.003.

---

## Pricing Tiers

| Tier | Price | Deliverable |
|---|---|---|
| Free | $0 | 1 page + DNA preview (the hook) |
| Pro | $97 one-time | 10 full pages + bonus assets |
| Pro+ | $149 | Everything + Style Set live customizer |
| Agency | $249-297 | Everything + 40-piece brand kit |

---

## What's Built (Prompted-Flows repo)

| Component | File | Status |
|---|---|---|
| DOM extractor | `server/services/dom-dna-extractor.js` | ✅ Done |
| Claude Vision fallback | `server/services/astro-theme-generator/screenshot-to-theme.js` | ✅ Done |
| Confidence scorer | `server/services/dna-confidence-scorer.js` | ✅ Done |
| Astro theme generator | `server/services/astro-theme-generator/index.js` | ✅ Done |
| Elementor page generator | `server/services/elementor-theme-generator.js` | ✅ Done (10 pages) |
| API routes | `server/routes/theme-generator.js` | ✅ Done |
| Frontend page | `ui/src/pages/ThemeGeneratorPage.tsx` | ✅ Done |
| WordPress plugin | `wordpress-plugin/theme-dna-generator/` | ✅ Scaffolded |
| Landing page | `public/themedna/index.html` | ✅ Done |
| Astro demo (8 themes) | `astro-theme-demo/` | ✅ Done |

---

## Immediate Next Steps

- [ ] **TEST:** Import Elementor JSON into real WordPress site — confirm pages render
- [ ] **TEST:** Run `screenshot-to-theme.js` CLI with real Anthropic API key
- [ ] **BUILD:** Stripe payment integration ($97 / $249 gates)
- [ ] **BUILD:** Bonus asset generators (business card SVG, social frames, ad frames)
- [ ] **BUILD:** Extract Style Set renderer from AutoForge → standalone customizer
- [ ] **BUILD:** Wire custom colors + fonts to live preview (15-25 lines each — currently broken)
- [ ] **BUILD:** Design Battle / voting page (UGC flywheel)

---

## Key Technical Decisions

1. **Code-first, AI-fallback** — Puppeteer DOM reads exact computed CSS values. AI only when confidence is low. (Stripe Minions pattern)
2. **Confidence score shown AFTER results** — User sees theme first (800ms delay), then score slides in. Never blocks.
3. **Pre-built templates, not AI-generated layouts** — Avoids "I can do this myself in ChatGPT" reaction.
4. **Plugin = thin client** — All processing on your server. Plugin just calls API.
5. **Free integration = distribution channel** — npm package is free, SaaS behind it is paid.

---

## Market Position

**Astro ecosystem:**
- 547K live sites, 900K weekly downloads, fastest growing framework
- No visual builder exists (the Elementor gap = wide open)
- SEO plugins are all basic meta-tag inserters — zero intelligence

**WordPress/Elementor:**
- 15M+ Elementor sites, huge audience, non-technical users
- Nobody selling "paste URL → matching Elementor theme"
- Same pipeline, different output format

**Competitor benchmark:** Lexington Themes, 8K customers, $99 all-access — static templates, no AI, no content engine, flat list UX with no description or sorting.

---

## Astro Integration / Partnership Notes
- No approval needed to list integrations — it's just npm + a manifest
- Official partner categories available: SEO (EMPTY), Content (EMPTY), Image Generation (EMPTY)
- Contact: partner@astro.build — you'd be paying $2K-10K/month to own a category
- Free path: publish npm package → gets auto-indexed in astro.build/integrations
