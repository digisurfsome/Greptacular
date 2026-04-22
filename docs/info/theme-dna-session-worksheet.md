# Theme DNA Generator — Session Worksheet
> Condensed from ~327 pages of session notes. All fluff removed. All key decisions, architecture, code built, and next steps preserved.

---

## 1. THE BUSINESS CONCEPT

**Core Model: "Elementor of Astro" (and WordPress)**
- Astro is free (like WordPress is free)
- You sell the add-ons, themes, and tools (like Elementor sells to WordPress users)
- Market position: First mover in a wide-open ecosystem

**The Product: Theme DNA Generator**
- User pastes a website URL (or uploads a screenshot)
- System extracts the "Design DNA" — colors, fonts, spacing, shadows, component styles
- Outputs a complete, deployable website theme (Astro or WordPress/Elementor)
- 10 fully styled page templates per generation

**Tagline candidate:** "Paste a URL. Get a complete website." / "So easy your dog can do it."

---

## 2. THE ASTRO ECOSYSTEM — MARKET OPPORTUNITY

**Market Size (verified numbers):**
- 547,406 live Astro websites
- 900,000+ weekly npm downloads (2.5x growth in 2025)
- 55,200 GitHub stars (top 300 repos on all of GitHub)
- 25% developer adoption in 2024; 30% more want to learn it

**Current Competition (weak):**

| Competitor | Offering | Gap |
|---|---|---|
| Lexington Themes | 89 templates, $99 all-access, 8,000 customers | No AI, no SEO, no content engine, flat list UX |
| Themefisher | 38+ themes, $137 all-access | Same — static templates only |
| Cosmic Themes | 18+ templates, $79-89 each | Same |
| astro-seo (plugin) | Basic meta tag inserter | 254K weekly downloads, zero intelligence |

**What doesn't exist in Astro yet:**
- Visual builder / theme engine (the Elementor gap)
- AI SEO suite (no Yoast equivalent)
- AI image generation integration
- AI content engine
- Screenshot-to-theme generator
- Style morphing / live customizer

**Astro vs WordPress for theme building:**
- Astro: one CSS file swaps entire theme (CSS custom properties), builds in ~2 seconds
- WordPress: 20+ PHP files, template hierarchy, hooks, child themes, plugin conflicts
- Astro integrations compile at BUILD TIME — 30 integrations don't slow the live site

**Official Partnership Program (astro.build/partnerships):**
- Standard sponsor: varies (Open Collective / GitHub Sponsors)
- Custom package: $2,000+/month
- Exclusive official partner: $10,000+/month (category ownership)
- "SEO", "Content", "Image Generation" categories are ALL EMPTY
- Contact: partner@astro.build

---

## 3. THE PIPELINE — HOW IT WORKS

```
User Input (URL or Screenshot)
         ↓
Step 1: DOM Extraction (Puppeteer — FREE, ~$0.00)
    - getComputedStyle() on all h1-h6, p, a, button, nav, section elements
    - Extracts exact hex values, fonts, spacing, border-radius, box-shadow
    - Confidence scored against 7 criteria
         ↓
Step 2: Confidence Check
    - Confident (85% of sites) → skip AI, go straight to generation
    - Low confidence (15%) → Claude Vision fallback (~$0.02)
         ↓
Step 3: Design DNA Object
    {
      colors: { brand, surface, text, border, status },
      typography: { fontFamily, sizes, weights },
      components: { cards, buttons, inputs, icons },
      spacing: { baseUnit, density, radiusRules },
      tailwindConfig: { ... }
    }
         ↓
Step 4: Theme Generation (pure code — FREE)
    ├── Astro: CSS custom properties + Tailwind preset + Astro components
    └── Elementor: 10 full page JSON templates (importable to WordPress)
         ↓
Step 5: Confidence Score Display (post-generation, 800ms delay)
    - Score tiers: 90-100% / 80-89% / 70-79% / 60-69% / 40-59%
    - Explanation shown AFTER results render (they already committed)
    - Color picker + font input for adjustments
    - "Regenerate with Changes" button
```

**Cost math:**
- 85% of generations: $0.00 (DOM extraction)
- 15% of generations: $0.02 (Claude Vision fallback)
- Average per generation: ~$0.003
- Margin at $97 sale: ~$96.997

**The Stripe Principle (applied here):** Code for predictable tasks, AI only for judgment calls. DOM extraction reads EXACT computed values — more accurate than AI guessing from a screenshot. AI handles the judgment call of "which of these 5 blues IS the brand color."

---

## 4. WHAT WAS ACTUALLY BUILT

All work committed to branch: `claude/explain-codebase-mm30emi7o66xbpke-F0QtL` in the Prompted-Flows repo.

### Backend Services (server/services/)

| File | What It Does |
|---|---|
| `astro-theme-generator/index.js` | Main pipeline: fromStyleSet(), fromMentor(), exportCSS(), exportTailwind(), generateAstroThemePackage() |
| `astro-theme-generator/style-to-tokens.js` | Converts Style Set output to unified design token format |
| `astro-theme-generator/tokens-to-tailwind.js` | Generates tailwind.config.js preset from tokens |
| `astro-theme-generator/screenshot-to-theme.js` | CLI tool: `node screenshot-to-theme.js <image-path> <theme-name>` |
| `elementor-theme-generator.js` | Generates 10 Elementor page templates from design DNA |
| `dna-confidence-scorer.js` | Scores extraction quality (0-100), returns label, explanation, tips, reasons |
| `dom-dna-extractor.js` | Puppeteer DOM-based extraction — reads exact computed CSS values, no AI needed |

### API Routes (server/routes/)

| Endpoint | What It Does |
|---|---|
| `POST /api/theme-generator/from-url` | URL → screenshot → DNA → Astro theme |
| `POST /api/theme-generator/from-image` | Base64 image → DNA → Astro theme |
| `POST /api/theme-generator/elementor/from-url` | URL → DNA → 10 Elementor pages |
| `POST /api/theme-generator/elementor/from-image` | Image → DNA → 10 Elementor pages |
| `GET /api/theme-generator/themes` | Lists all generated themes |
| `GET /api/theme-generator/themes/:name` | Gets specific theme files + DNA |

### 10 Elementor Page Templates Generated Per Run
1. Home
2. About
3. Services
4. Contact
5. Blog
6. Landing Page (sales/opt-in)
7. Testimonials (stats bar, 6 testimonial cards)
8. FAQ (8 Q&A accordion)
9. Pricing (3-tier with "popular" highlight)
10. Portfolio (project cards, results stats)

### 8 Themes Built and Tested (in astro-theme-demo/)

| URL | Theme | Vibe |
|---|---|---|
| `/` | Elementor.com | Light, hot pink, clean SaaS |
| `/dark` | BridgeVoice | Near-black, neon green, dev tool |
| `/searchatlas` | Search Atlas | Dark purple, mint cyan, SEO SaaS |
| `/smarthome` | Smart Home Dashboard | Glassmorphism, amber, IoT |
| `/finance` | Finance Dashboard | Dark plum, pink/rose, gradient cards |
| `/barbershop` | Lumberjack Barbers | Dark, bold red, sharp edges, Oswald font |
| `/cafe` | Moon Cafe | Dark navy, electric yellow, Playfair serif |
| `/bike` | Blowfish 01 | Pure black, neon green, ZERO radius, product |

### WordPress Plugin (wordpress-plugin/theme-dna-generator/)
Full scaffold ready for WordPress.org submission:
- Sits under Elementor menu in WP admin
- URL input → calls SaaS API → shows progress theater (10-min countdown)
- Shows extracted DNA (color swatches + font preview)
- Grid of 6 generated pages with "Import to Elementor" buttons
- License tier system (free/pro/agency)
- `readme.txt` formatted for WordPress.org listing
- Thin client architecture — all heavy lifting stays on your API server

### Frontend (ui/src/pages/ThemeGeneratorPage.tsx)
- Toggle: URL input vs image upload
- Output format selector: WordPress/Elementor, Astro, or Both
- Progress theater: 10-step animation, animated progress bar
- Results: screenshot + confidence score (800ms delayed reveal)
- Tier-based explanations for confidence score
- Color pickers + font input for tweaking
- "Regenerate with Changes" button
- Page grid showing all 10 generated pages
- DNA download as JSON

### Landing Page (public/themedna/index.html)
- Dark mode, Inter font, clean SaaS aesthetic
- Hero: "Paste a URL. Get a Complete Website."
- 3-step "How It Works"
- 8-card value grid ("What's Included")
- Competitor comparison table (Generic Theme vs WP Theme vs Theme DNA)
- 3-tier pricing: Free / Pro $97 / Agency $297
- FAQ section

### Mentor's Style Guide Prompt Integration
The mentor's prompt (Design System Architect persona, extracts Visual DNA from screenshots) outputs:
1. Abstract Color Tokens (brand, surface, text, border, status)
2. Typography System (font family, hierarchy, weights, line-heights)
3. Universal Component Patterns (cards, buttons, inputs, icons with CSS values)
4. Layout & Spacing Physics (base unit, density, radius rules)
5. Tailwind CSS Theme Extension (tailwind.config.js ready)

This output maps DIRECTLY into `fromMentor()` in the pipeline. The Tailwind config format he produces plugs straight into the token normalizer.

---

## 5. THE STYLE SET RENDERER (Existing AutoForge Tool to Extract)

**What exists now (inside AutoForge):**
- `StylePreview.tsx` — 1,353 lines, renders 4 fake app pages (Landing, Dashboard, Feed, Settings) with inline CSS from design tokens. Zero external dependencies.
- 12 design styles: Flat, Minimalism, Neumorphism, Glassmorphism, Skeuomorphism, Claymorphism, Bauhaus, Neubrutalism + more
- 24 color palettes across 9 categories
- 12 Google Fonts
- 11 refinement options (shadows, borders, animations, dark mode, etc.)
- Accent style mixing (overlay one style's buttons/inputs onto another style's layout)
- AI Design Guide with WebSocket chat (built but not fully wired)
- Screenshot extraction via Claude Vision (upload screenshot, detects style)

**What's BROKEN (gaps before extraction):**
- Custom colors DO NOT change the preview (~15 lines to fix)
- Font selection DOES NOT change the preview (~10 lines to fix)
- Refinements DO NOT change the preview (~80 lines to fix)
- AI Design Guide panel uses hardcoded placeholder instead of connecting to backend

**Extraction Decision: Pull it out of AutoForge, fix in standalone**
- The renderer has ZERO AutoForge dependencies — it takes a StyleGuide object and returns React elements with inline CSS
- Style definitions live in `style_manager.py` (2,780 lines) — export as static JSON for standalone app
- The wizard container (NewProjectModal.tsx, 1,992 lines) is what's causing layout issues — standalone app gets full viewport
- ~3,600 lines to extract, ~450 new lines to write

**Extraction checklist (ready to copy as-is):**
- `StylePreview.tsx` (1,353 lines — the renderer)
- `StyleCardPreview.tsx` (267 lines — mini thumbnails)
- `palettes.ts` (388 lines — 24 palette definitions)
- `fonts.ts` (27 lines — 12 font definitions)
- `refinementOptions.ts` (157 lines — 11 refinement groups)
- `paletteUtils.ts` (46 lines — palette-to-color converter)
- Type definitions from `types.ts` (~120 lines)

**Needs minor surgery:**
- `ColorCustomizer.tsx` — replace shadcn components with vanilla HTML
- `PaletteStrip.tsx` — replace Tailwind classes with vanilla CSS
- `DesignGuidePanel.tsx` — wire up actual useDesignGuide hook
- `useDesignGuide.ts` — change WebSocket URL to standalone backend

---

## 6. BUSINESS MODEL / PRICING

### Tier Structure

| Tier | Price | What They Get |
|---|---|---|
| Free | $0 | 1 page generation + DNA preview (the hook) |
| Pro | $97 one-time | 10-page full site + bonus assets + download |
| Pro+ | $149 | Everything + Style Set customizer (infinite tweaks) |
| Agency | $249-297 | Everything + 40-piece brand kit + white label |

### The $249 "40-Pack" Brand Kit Includes:
- 10 website pages (Home, About, Services, Contact, Blog, Landing, Testimonials, FAQ, Pricing, Portfolio)
- Landing page templates (sales page, opt-in, webinar, coming soon)
- Social media frames (Facebook cover, Instagram post/story, LinkedIn banner, YouTube thumbnail)
- Ad frames (Facebook ad, Google Display, Instagram ad)
- Email header/footer
- Business card layout
- Letterhead
- Bonus: business card surprise (under-promise, over-deliver)
- API cost per generation: ~$0.003 average

### Integration/SaaS Revenue Model
- Free npm package → distributed via Astro integration directory
- Free tier: basic meta tags, maybe 3 AI articles/month
- Paid tiers: AI content engine, image pipeline, style system
- WordPress.org plugin: free installs drive traffic, paywall unlocks full site
- Monthly recurring for AI features

### Competitor Math
- Lexington Themes: $99 × 8,000 customers = ~$792,000 (static templates only)
- Theme DNA at same customer count: higher ASP + recurring + brand kit upsells

---

## 7. MARKETING STRATEGY

### The "Fidget Spinner" Concept
- Take 3 popular styles × 3 color changes × 3 fonts = 27 combinations shown in renderer
- NOT overwhelming options — just enough to be addictive to click through
- Free renderer on homepage that morphs live between styles
- GIF-able, viral, "fun to play with"

### Social Media Viral Content
- **Core hook:** "Paste any website URL → get a full matching website in 10 minutes"
- **Video formats:** Show laptop screen, paste URL, watch progress bar, reveal themed site
- **The baby/dog series:** Dog/baby "builds" a website while owner is out of the room
- **Design battle/competition:** Friends/family upload different sites, public votes on best theme
- **Dribbble screenshots:** Infinite content — scroll Dribbble, screenshot designs, generate themes, post comparisons
- **Client use case:** "Client sent me a competitor's URL at 9pm, delivered their site by 10pm"
- **Cross-sell to Astro:** Every ad for your tool is an ad for Astro — they'll love you for bringing traffic

### Facebook/Instagram Ads
- Video: laptop screen view, clicking styles morphing on screen
- Match 3 "brother-sister" style combos per audience segment
- Facebook algo finds the right people; retarget with 5-7 feature reveal videos
- Top of funnel: "make a website" keywords (massive volume, not just Astro keywords)
- Retargeting flow → free download → paid upsell

### UGC Theme Challenge Flywheel
- "Upload any screenshot → get a custom Astro theme"
- Users upload designs (free market research)
- Every generated theme goes into community library (with permission)
- Library grows without you designing anything
- More themes → more traffic → more uploads → more themes
- Top voted themes = validated premium collection

### Progress Theater (Critical UX Decision)
- 10-12 minutes is the sweet spot (not instant = cheap, not 30+ min = broken)
- Show progress step by step: "Extracting color palette..." / "Building page templates..."
- Each asset appears in grid one by one as it "renders"
- The wait screen = upsell real estate (captive audience, credit card already on file)
- Show: add social media templates / add hosting / install-for-you during wait

---

## 8. KEY TECHNICAL DECISIONS MADE

1. **Code-first, AI-fallback** (Stripe Minions pattern): DOM extraction is free, fast, and more accurate for explicit values. AI only when confidence is low.

2. **Plugin = thin client**: WordPress plugin / Astro integration is just UI. All heavy processing on YOUR server. No API keys exposed, no AI in the plugin itself.

3. **Free integration = distribution channel**: Don't charge for the npm package. Charge for the SaaS behind it. This is how Sanity, Sentry, Netlify all work.

4. **Confidence score shows AFTER results**: They see their generated pages first (commitment), THEN the score slides in. If score is low, frame it as "starting point" + give tweak tools. Never say "bad" or "failed."

5. **Pre-built templates, not AI-generated layouts**: AI-generated layouts make users think "I can just do this myself." Pre-built professional templates feel like a product. AI extraction is invisible ("the tool reads your brand").

6. **Static JSON for style data**: No Python backend needed for standalone app. 12 styles, 24 palettes, 12 fonts all baked in as static JSON. AI design guide is premium/phase 2.

7. **Extraction path for Style Set**: Extract renderer from AutoForge to standalone app FIRST, then fix the broken wiring (colors, fonts, refinements) in the standalone context where it has full viewport.

---

## 9. OUTSTANDING / NEXT UP

### Test Immediately
- [ ] Test Elementor page export on a REAL WordPress site — import JSON, confirm pages render correctly
- [ ] Run the standalone `screenshot-to-theme.js` CLI with a real Anthropic API key
- [ ] Test the DOM extractor on 10 different sites to validate confidence scoring

### Build Next
- [ ] Bonus asset generators: business card, social media frames, ad templates (SVG with color slots)
- [ ] Style Set extraction from AutoForge → standalone app
- [ ] Wire custom colors + fonts → live preview in Style Set (15-25 lines each)
- [ ] Stripe payment integration for themedna.com
- [ ] "Design Battle" competition/voting page
- [ ] Car wrap mockup (it's just an SVG template with color slots — actually easy)

### WordPress Path
- [ ] Test Elementor JSON import on staging WordPress site
- [ ] Add more page types to match the design language (not just color-swapped generic)
- [ ] Submit plugin scaffold to WordPress.org (meet PHP standards + compatibility checks)
- [ ] Add Elementor license ($59-99/yr) for testing advanced features

### Astro Marketplace Path
- [ ] Package 8 demo themes as installable npm packages (@styleset/elementor-style-theme, etc.)
- [ ] List on astro.build/themes
- [ ] Consider official Astro partnership email (partner@astro.build) — SEO category is EMPTY

---

## 10. RELEVANT FILE LOCATIONS

### In This Repo (AutoForge Workspace)

**Style-related handoffs** (existing Style Set work):
- `.claude/handoffs/style-mixing-handoff.md` — base + accent style system design
- `.claude/handoffs/style-preview-grid-handoff.md` — full-screen style picker with live renderer
- `.claude/handoffs/color-picker-preview-task.md` — color customization work
- `.claude/handoffs/idea-code-integration-handoff.md`

**Relevant services already in this repo:**
- `server/services/style_manager.py` — 2,780 lines, all 12 style definitions (export as JSON for standalone)
- `server/services/style_extractor.py`
- `server/services/style_modifiers.py`
- `server/services/design_guide_session.py` — AI Design Guide backend (built, needs wiring)

**Related reference doc:**
- `docs/info/astro-convex-stripe-saas-build-worksheet.md` — Astro + Convex + Stripe SaaS boilerplate patterns

### AutoForge Global Handoffs (C:\Users\lober\.autoforge\handoffs\)
Most recent sessions:
- `session-157.md`
- `session-156.md`
- `session-155.md`
- `session-154.md`
- `session-153.md`
- `session-152.md`
- `session-151.md`
- `session-150.md`

### In Prompted-Flows Repo (the actual build repo)
Branch: `claude/explain-codebase-mm30emi7o66xbpke-F0QtL`

Built files (all committed and pushed):
```
server/
  routes/theme-generator.js
  services/
    astro-theme-generator/
      index.js
      style-to-tokens.js
      tokens-to-tailwind.js
      screenshot-to-theme.js          ← CLI tool
      output/                         ← 8 generated themes
        elementor-theme/
        bridgevoice-dark/
        searchatlas-theme/
        smarthome-dashboard/
        finance-dashboard/
        barbershop-theme/
        mooncafe-theme/
        blowfish-theme/
    elementor-theme-generator.js      ← 10 Elementor page templates
    dna-confidence-scorer.js          ← 0-100 scoring with explanations
    dom-dna-extractor.js              ← Puppeteer DOM extraction (free)

ui/src/pages/ThemeGeneratorPage.tsx   ← Full frontend page

astro-theme-demo/                     ← 8 live Astro themes
  src/pages/
    index.astro          (Elementor theme)
    dark.astro           (BridgeVoice)
    searchatlas.astro
    smarthome.astro
    finance.astro
    barbershop.astro
    cafe.astro
    bike.astro

wordpress-plugin/
  theme-dna-generator/               ← Full WP plugin scaffold
    theme-dna-generator.php
    includes/
      class-plugin.php
      class-admin-page.php
      class-api-client.php
    assets/
    readme.txt                       ← WP.org ready

public/themedna/index.html           ← Landing page
```

---

## 11. MENTOR'S STYLE GUIDE PROMPT — HOW TO USE

1. Find a screenshot of any website/app with a style you love
2. Paste the full prompt (stored in your Google Doc / idea-code template) into Claude/ChatGPT/Gemini along with the screenshot
3. It outputs: Color Tokens, Typography System, Component Patterns, Spacing Physics, and a Tailwind config block
4. That output feeds directly into `fromMentor()` in the pipeline → generates complete Astro theme package

The output format from the prompt maps 1:1 to the pipeline's token normalizer. No manual translation needed.

---

## 12. QUICK REFERENCE — CLI COMMANDS

```bash
# Set API key (Windows)
set ANTHROPIC_API_KEY=sk-ant-your-real-key-here

# Run screenshot-to-theme CLI
cd server\services\astro-theme-generator
node screenshot-to-theme.js "C:\Users\lober\Desktop\screenshot.png" my-theme-name

# View Astro demo
cd astro-theme-demo
npm install
npm run dev
# Open: http://localhost:4321

# Available demo pages:
# /              Elementor theme (pink + white)
# /dark          BridgeVoice (black + neon green)
# /searchatlas   Search Atlas (dark purple + mint)
# /smarthome     Smart Home (glass + amber)
# /finance       Finance (plum + pink gradients)
# /barbershop    Lumberjack (dark + bold red)
# /cafe          Moon Cafe (navy + electric yellow)
# /bike          Blowfish (black + neon green, zero radius)
```

---

*Session date: ~March 2026. Repo: Prompted-Flows. Branch: claude/explain-codebase-mm30emi7o66xbpke-F0QtL. Committed to this AutoForge workspace for reference.*

---

## 13. ASTRO THEME — COMPLETE DOCUMENT INDEX
> All AutoForge files related to the Astro Theme Generator / Theme DNA product, grouped by location.
> **PRD is at:** `docs/page-prds/astro-theme/README.md`

### This Repo — docs/info/
| File | What It Is |
|---|---|
| `docs/info/theme-dna-session-worksheet.md` | **← You are here.** Full session worksheet, all decisions and architecture |
| `docs/info/astro-convex-stripe-saas-build-worksheet.md` | Astro + Convex + Stripe SaaS launch boilerplate patterns (Income Stream Surfers demo) |

### This Repo — docs/page-prds/
| File | What It Is |
|---|---|
| `docs/page-prds/astro-theme/README.md` | **PRD** — product summary, next steps, built file inventory, market position |

### This Repo — .claude/handoffs/ (Style Set / Renderer — feeds into this product)
| File | What It Is |
|---|---|
| `.claude/handoffs/style-mixing-handoff.md` | Base + accent style system design — the fidget spinner engine architecture |
| `.claude/handoffs/style-preview-grid-handoff.md` | Full-screen style picker with live renderer (4-page preview, fanned card stack, Playwright screenshots) |
| `.claude/handoffs/color-picker-preview-task.md` | Color customization work — the broken wiring to fix before extraction |
| `.claude/handoffs/idea-code-integration-handoff.md` | Idea Code integration (mentor's style guide prompt workflow) |

### This Repo — Server Services (existing style infrastructure)
| File | What It Is |
|---|---|
| `server/services/style_manager.py` | 2,780 lines — all 12 style definitions. Export as JSON for standalone app |
| `server/services/style_extractor.py` | Style extraction service |
| `server/services/style_modifiers.py` | Style modifier logic |
| `server/services/design_guide_session.py` | AI Design Guide backend — built, needs wiring to frontend |

### AutoForge Global Handoffs (C:\Users\lober\.autoforge\handoffs\)
> Most recent sessions covering this work:
| File | What It Is |
|---|---|
| `session-157.md` | Most recent session |
| `session-156.md` | |
| `session-155.md` | |
| `session-154.md` | |
| `session-153.md` | |

### Prompted-Flows Repo — Built Files
> Branch: `claude/explain-codebase-mm30emi7o66xbpke-F0QtL`

| File | What It Is |
|---|---|
| `server/routes/theme-generator.js` | All 5 API endpoints |
| `server/services/astro-theme-generator/index.js` | Main pipeline (fromStyleSet, fromMentor, export functions) |
| `server/services/astro-theme-generator/style-to-tokens.js` | Style Set output → unified token format |
| `server/services/astro-theme-generator/tokens-to-tailwind.js` | Token → Tailwind config generator |
| `server/services/astro-theme-generator/screenshot-to-theme.js` | CLI tool (node screenshot-to-theme.js <img> <name>) |
| `server/services/astro-theme-generator/output/` | 8 generated themes from real screenshots |
| `server/services/elementor-theme-generator.js` | 10 Elementor page templates (Home → Portfolio) |
| `server/services/dna-confidence-scorer.js` | 0-100 quality scoring with tier explanations |
| `server/services/dom-dna-extractor.js` | Puppeteer DOM-based extraction — no AI, no cost |
| `ui/src/pages/ThemeGeneratorPage.tsx` | Full frontend: URL input, upload, progress theater, DNA tweaker |
| `wordpress-plugin/theme-dna-generator/` | Full WP plugin scaffold — ready for WP.org |
| `public/themedna/index.html` | themedna.com landing page |
| `astro-theme-demo/src/pages/` | 8 live Astro theme demo pages |
