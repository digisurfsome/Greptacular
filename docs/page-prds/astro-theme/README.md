# Theme DNA — Agent OS Product Context
> Full context for any agent continuing this build. Read this entire file before writing a single line of code.

---

## LAYER 1 — STANDARDS

### Architecture Rule: Three Layers, Never Cross Them
The entire product is built on a strict three-layer separation:

**Layer 1: THEME** — CSS custom properties only. No HTML, no logic.
- Source: image-to-theme extractor (Puppeteer DOM + Claude Vision fallback) OR style renderer (morphism styles)
- Output: a `[data-theme="name"]` block in CSS setting ~40 semantic variables
- File: `docs/info/theme-variables-canonical.css` — the canonical variable contract

**Layer 2: COMPONENTS** — HTML structure only. References Layer 1 variables, never hardcodes colors/fonts.
- Source: component library (not yet built — next task)
- Each component is a pure function: data in → HTML out
- Components ONLY read semantic variables (--radius-card, --shadow-card, --color-brand, etc.)
- Components NEVER read scale variables directly (--space-4, --radius-lg)

**Layer 3: CONTENT** — Text, images, data. Edited by the page editor.
- Source: JSON block definitions (one per page, describes rows of components with their content)
- Edited by: the inline text editor + component inserter (not yet built)

**The golden rule:** Swap Layer 1 → site repaints. Edit Layer 3 → content updates. Layers 2 and 3 never change when switching themes.

### Code-First, AI-Fallback Rule (from Stripe Minions pattern)
If a task can be done deterministically with code, do it with code. Use AI only for tasks requiring genuine judgment.

Applied to theme extraction:
- FIRST: Puppeteer getComputedStyle() on DOM elements — exact hex values, $0 cost, 5 seconds
- ONLY IF low confidence: Claude Vision API — $0.02, 15 seconds
- Average cost target: ~$0.003 per generation

This pattern cuts API costs 85%+ and eliminates rate limit / outage dependencies.

### Variable Naming Contract
All theme sources output these exact names. All components read only these names.
Full definition: `docs/info/theme-variables-canonical.css`

Key semantic variables every component uses:
- `--color-brand` / `--color-brand-hover` / `--color-brand-text`
- `--color-bg-page` / `--color-bg-card` / `--color-bg-input`
- `--color-text-primary` / `--color-text-secondary` / `--color-text-muted`
- `--color-border` / `--color-border-strong` / `--color-border-focus`
- `--radius-card` / `--radius-btn` / `--radius-input` / `--radius-badge`
- `--shadow-card` / `--shadow-card-hover` / `--shadow-btn`
- `--spacing-card-padding` / `--spacing-section-y` / `--spacing-component-gap`
- `--font-family` / `--font-family-heading`
- `--transition-base` / `--transition-colors`

### Page Data Format
Pages are NOT freeform HTML. Every page is a JSON array of rows:
```json
[
  {
    "id": "row-1",
    "layout": "full",
    "component": "hero",
    "data": { "headline": "We Build Fast", "sub": "...", "cta": "Get Started", "ctaHref": "#" }
  },
  {
    "id": "row-2", 
    "layout": "3col",
    "components": [
      { "type": "card", "data": { "icon": "⚡", "title": "Speed", "text": "..." } },
      { "type": "card", "data": { "icon": "🎨", "title": "Design", "text": "..." } },
      { "type": "card", "data": { "icon": "📈", "title": "SEO", "text": "..." } }
    ]
  }
]
```
Layout options: `"full"` (1 column), `"2col"`, `"3col"`, `"sidebar-left"`, `"sidebar-right"`

AI generates pages by producing this JSON — not by writing Astro/HTML directly. The component library renders it. The editor reads/writes it. Everything flows from this one source of truth.

---

## LAYER 2 — PRODUCT

### What This Product Is
**Theme DNA** — paste any website URL (or upload a screenshot), get a complete, deployable Astro or WordPress/Elementor site in 10 minutes that matches the visual style of the source.

Not a theme marketplace. Not a template shop. A design system extractor + site generator. The output is a working codebase, not a zip of pretty mockups.

### The Core Value Proposition
> "Your client sends you a screenshot saying 'I want my site to look like this.' You paste the URL. 10 minutes later you hand them a complete 10-page Astro site — their brand colors, their fonts, their design energy — and they can edit every word themselves without calling you."

### Why It's Different From Every Competitor
- Lexington Themes ($99 all-access): 89 static templates, no AI, no editor, no content engine
- ThemeForest: Generic templates you skin manually
- Webflow: Subscription, designer-required, not Astro
- Elementor: WordPress only, runtime bloat
- TinaCMS / Keystatic: Dev-only editing, not a product

Theme DNA is the first tool that:
1. Extracts design language FROM a URL (not you picking from a catalog)
2. Generates a site that actually matches the source's vibe
3. Lets non-coders edit the result without touching code

### Target Market
**Primary:** Freelance web designers/developers building sites for small businesses. They build 5-20 sites/year, charge $1,500-5,000/site, spend 30-50% of that time on design and content population. Theme DNA cuts that to near zero.

**Secondary:** Small business owners who bought a theme, can't edit it, and pay their designer $20 per text change.

**Astro market size:** 547,000+ live Astro sites, 900K weekly npm downloads, 25% developer adoption in 2024. WordPress: 500M+ sites, 15M+ using Elementor. Combined addressable market is enormous.

### Business Model
| Tier | Price | What They Get |
|---|---|---|
| Free | $0 | Design DNA preview (colors, fonts extracted), 1 page generated |
| Pro | $97 one-time | Full 10-page site (Astro or Elementor), bonus assets, editor |
| Agency | $249 one-time | Everything + 40-piece brand kit (social frames, ad templates, business card) + white label |
| SaaS | $X/mo | Unlimited generations (future — launch one-time first) |

**Unit economics:**
- Average generation cost: ~$0.003 (code-first DOM extraction)
- Pro tier margin: $96.997 per sale (~99.99%)
- Agency tier margin: $248.997 per sale

### The 40-Piece Brand Kit (Agency tier)
All generated from the same design DNA extracted from one URL:
- Full 10-page Astro or Elementor site
- Facebook/Instagram/LinkedIn/Twitter/YouTube social profile headers
- Instagram post template (1:1), story template (9:16)
- Facebook ad frame (multiple sizes)
- Google Display ad (300x250, 728x90, 160x600)
- Email header + footer
- Business card (front + back)
- Letterhead
- Slide deck cover template
- Car wrap mockup (yes, really)
- Favicon set

**Progress theater:** The 40-piece kit "renders" over 10-12 minutes with a live progress UI showing each asset appearing. Real generation time is ~60 seconds but the wait makes it feel premium. During the wait: upsell offers are shown (monthly social templates, hosting, install service).

### Marketing Strategy
**Core hook:** "So easy your dog could do it." Viral video series showing pets, babies, and grandparents building websites. Each video is a product demo disguised as entertainment.

**The Fidget Spinner:** After theme extraction, users can tweak colors/fonts/styles using the style renderer — the "fidget spinner" mode where watching the design system morph in real time is inherently addictive. This is both a feature and a marketing asset (GIF/video content shows the morphing).

**Design Battle:** Social media challenge — two people screenshot different sites, generate themes, post side-by-side, public votes. Tags the account. Self-sustaining UGC content engine.

**Distribution:** Free Astro integration on npm/astro.build directory → 547K potential users see it → free tier converts → paid upsells. Same free-plugin-as-funnel model as Sanity CMS.

**WordPress plugin:** Thin plugin that adds a "paste URL" widget inside Elementor editor. Plugin is free, it calls the paid Theme DNA API. Listed on WordPress.org for organic discovery from 500M+ WP users.

### Confidence Scoring
Every generation returns a confidence score (0-100) based on:
- Are the detected colors solid hex (not gradients)?
- Is there one clear brand color (not 3 competing ones)?
- Is the font a known Google Font (not a custom webfont)?
- Are light/dark sections consistent?
- Did we find enough styled elements?

**Score display timing:** Results (the generated pages) appear FIRST. Confidence score animates in 800ms AFTER results are visible. User is already committed to trying — they see their theme, THEN they see the score and any adjustment suggestions. Never shown on sales page.

Score tiers + messaging:
- 90-100%: "Excellent match" — minimal copy needed
- 80-89%: "Strong match" — quick reassurance
- 70-79%: "Good match — adjust brand color to nail it" — color picker shown
- 60-69%: "Solid starting point" — explains gradient detection, says tweak in 30 seconds
- 40-59%: "Creative site detected" — always says "this is the 5% where manual adjustment shines"
- Never use words: broken, failed, error, wrong, bad

---

## LAYER 3 — SPECS

### What Has Been Built (Do Not Rebuild These)

#### Theme Extraction Pipeline
**File:** `server/services/astro-theme-generator/screenshot-to-theme.js`
CLI tool: `node screenshot-to-theme.js <image-path> [theme-name]`
Uses Claude Vision to extract design DNA from screenshot → generates full theme package

**File:** `server/services/astro-theme-generator/dom-extractor.js`
Puppeteer-based DOM extraction — getComputedStyle() on key elements, color frequency analysis, font detection. Returns confidence score. Used FIRST before calling Claude Vision.

**File:** `server/services/astro-theme-generator/dna-confidence-scorer.js`
Scores extraction quality, returns score + label + explanation + tips

**File:** `server/services/astro-theme-generator/style-to-tokens.js`
Converts raw design DNA → normalized token object using canonical variable names

**File:** `server/services/astro-theme-generator/index.js`
Main pipeline: `fromStyleSet(style, palette, font)` and `fromMentor(mentorOutput)` entry points

**File:** `server/services/astro-theme-generator/tokens-to-tailwind.js`
Converts token object → Tailwind preset config

#### Astro Theme Generator
`generateAstroThemePackage(tokens, themeName)` — outputs complete npm-publishable Astro integration:
- `package.json`, `src/index.js` (Astro integration hook), `src/styles/theme.css`, `src/styles/reset.css`
- `src/components/Card.astro`, `Button.astro`, `Badge.astro`, `Container.astro`, `Input.astro`
- `tailwind-preset.mjs`, `tailwind-preset-vars.mjs`
- `README.md`

#### Elementor Theme Generator
**File:** `server/services/astro-theme-generator/elementor-theme-generator.js`
`generateElementorTheme(designDNA, themeName)` — outputs 10 complete Elementor page JSON files:
1. Home, 2. About, 3. Services, 4. Contact, 5. Blog, 6. Landing Page, 7. Testimonials, 8. FAQ, 9. Pricing, 10. Portfolio

Each page is valid Elementor JSON importable via Elementor > Templates > Import.

#### API Routes
**File:** `server/routes/theme-generator.js` — registered in server/main.py
```
POST /api/theme-generator/from-url           → Astro theme from URL
POST /api/theme-generator/from-image         → Astro theme from base64 image
POST /api/theme-generator/elementor/from-url → Elementor pages from URL
POST /api/theme-generator/elementor/from-image → Elementor pages from image
POST /api/theme-generator/from-dna           → Both outputs from pre-extracted DNA
GET  /api/theme-generator/themes             → List generated themes
GET  /api/theme-generator/themes/:name       → Get specific theme files
```

All URL endpoints: DOM extraction first → confidence check → Claude Vision only if confidence < 70.

Response always includes: `{ designDNA, confidence: { score, label, explanation, reasons, tips }, extractionMethod: 'dom'|'claude-vision', ... }`

#### Frontend Page
**File:** `ui/src/pages/ThemeGeneratorPage.tsx`
Accessible via More menu → "Theme DNA"
Three stages: Input (URL/image toggle) → Progress theater (10-step animation) → Results (confidence panel + DNA tweaker + page grid)

#### Demo Site (in Prompted-Flows repo, not this repo)
`astro-theme-demo/` — 8 live demo pages, each from a different screenshot:
- `/` Elementor (light, hot pink)
- `/dark` BridgeVoice (black, neon green)
- `/searchatlas` Search Atlas (dark purple, mint)
- `/smarthome` Smart Home dashboard (glass, amber)
- `/finance` Finance dashboard (plum, pink gradient)
- `/barbershop` Lumberjack (dark, bold red, sharp)
- `/cafe` Moon Cafe (navy, electric yellow, serif)
- `/bike` Blowfish 01 (pure black, neon green, zero radius)

#### CSS Variable Standard
**File:** `docs/info/theme-variables-canonical.css`
480 lines. The contract between all theme sources and all components.
80 variables across 13 sections. 5 complete theme override examples included.

**File:** `docs/info/theme-variables-guide.md`
Explains the 3-tier model and how to use the variables.

#### WordPress Plugin (scaffolded, not published)
**Dir:** `wordpress-plugin/theme-dna-generator/`
- `theme-dna-generator.php` — plugin bootstrap, compatibility check
- `includes/class-plugin.php` — core plugin class
- `includes/class-admin-page.php` — WP admin UI, URL input, progress theater, results grid
- `readme.txt` — WordPress.org listing copy
Calls Theme DNA API from PHP, injects generated Elementor JSON via WP REST API.

#### Landing Page
**File:** `public/themedna/index.html`
Full sales page: hero, how-it-works, value grid, competitor comparison table, 3-tier pricing, FAQ.

---

### What To Build Next (In This Order)

#### NEXT: Component Library
This is the foundation everything else requires. Nothing else in "next steps" can be built until this exists.

**What it is:** 12-15 pre-built page section components defined as Astro components. Each component:
- Accepts a typed data object as props
- Renders semantic HTML using ONLY CSS custom property variables from the canonical set
- Has a defined JSON schema for its data props
- Has a defined component name used in page JSON definitions

**Components to build (in priority order):**
1. `Hero` — headline, subheadline, primary CTA, secondary CTA, optional image/illustration area
2. `FeatureCards` — grid of 2-4 cards with icon, title, and body text
3. `Stats` — row of 3-5 stat items (number + label)
4. `CTA` — full-width call-to-action section, headline + button, optionally dark background
5. `Testimonials` — 2-3 quote cards with avatar, name, role, company
6. `FAQ` — accordion list of question/answer pairs
7. `Pricing` — 2-3 tier cards with feature list and CTA, one highlighted as "popular"
8. `TextImage` — two-column section: text left/right + image left/right
9. `Team` — grid of person cards with photo, name, role, bio
10. `Portfolio` — grid of project cards with image, title, tags, result stat
11. `LogoBar` — row of client/partner logos (trust signal)
12. `Contact` — contact form + optional address/phone/email block
13. `BlogGrid` — grid of article cards with thumbnail, date, title, excerpt
14. `NavBar` — top navigation with logo, links, CTA button
15. `Footer` — multi-column footer with logo, links, social icons, copyright

**File structure:**
```
ui/src/components/theme-dna/
  Hero.astro
  FeatureCards.astro
  Stats.astro
  CTA.astro
  Testimonials.astro
  FAQ.astro
  Pricing.astro
  TextImage.astro
  Team.astro
  Portfolio.astro
  LogoBar.astro
  Contact.astro
  BlogGrid.astro
  NavBar.astro
  Footer.astro
  index.ts          ← exports all + component registry
  types.ts          ← TypeScript interfaces for all component data props
  schemas.ts        ← JSON schemas for validation
```

**Component HTML rules:**
- Use semantic HTML (`<section>`, `<article>`, `<nav>`, `<header>`, `<footer>`)
- CSS classes match component name: `.hero`, `.feature-cards`, `.stats-bar`
- All visual properties via CSS variables — zero hardcoded colors, fonts, or spacing
- Each component scoped: `.hero { ... }` not global classes
- Responsive by default — use CSS Grid/Flexbox, not fixed widths

**Example component (Hero):**
```astro
---
interface Props {
  headline: string
  sub?: string
  cta?: string
  ctaHref?: string
  ctaSecondary?: string
  ctaSecondaryHref?: string
  image?: string
  imageAlt?: string
  layout?: 'centered' | 'split-right' | 'split-left'
}
const { headline, sub, cta = 'Get Started', ctaHref = '#', layout = 'centered', ...rest } = Astro.props
---
<section class={`hero hero--${layout}`}>
  <div class="hero__content">
    <h1 class="hero__headline">{headline}</h1>
    {sub && <p class="hero__sub">{sub}</p>}
    <div class="hero__actions">
      <a href={ctaHref} class="btn btn--primary">{cta}</a>
      {rest.ctaSecondary && <a href={rest.ctaSecondaryHref || '#'} class="btn btn--secondary">{rest.ctaSecondary}</a>}
    </div>
  </div>
</section>
<style>
  .hero {
    padding: var(--spacing-section-y) var(--space-6);
    background: var(--color-bg-primary);
    text-align: center;
  }
  .hero__headline {
    font-family: var(--font-family-heading);
    font-size: var(--font-size-hero);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    line-height: var(--line-height-tight);
    letter-spacing: var(--letter-spacing-tight);
  }
  .hero__sub {
    font-size: var(--font-size-xl);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    max-width: 640px;
    margin: var(--space-4) auto 0;
  }
  .hero__actions {
    display: flex;
    gap: var(--space-4);
    justify-content: center;
    margin-top: var(--space-8);
  }
  .btn--primary {
    background: var(--color-brand);
    color: var(--color-brand-text);
    border-radius: var(--radius-btn);
    padding: var(--spacing-btn-y) var(--spacing-btn-x);
    font-weight: var(--font-weight-semibold);
    box-shadow: var(--shadow-btn);
    transition: var(--transition-colors), var(--transition-shadow);
  }
  .btn--primary:hover {
    background: var(--color-brand-hover);
    box-shadow: var(--shadow-btn-hover);
  }
</style>
```

#### AFTER Component Library: Page Renderer
A page renderer that takes a page JSON array and renders the correct components in the correct row layouts.

```astro
---
// PageRenderer.astro
import Hero from './Hero.astro'
import FeatureCards from './FeatureCards.astro'
// ... etc

const { blocks } = Astro.props
const componentMap = { hero: Hero, 'feature-cards': FeatureCards, ... }
---
{blocks.map(row => (
  <div class={`row row--${row.layout}`}>
    {row.layout === 'full'
      ? <Component is={componentMap[row.component]} {...row.data} />
      : row.components.map(col => <Component is={componentMap[col.type]} {...col.data} />)
    }
  </div>
))}
```

#### AFTER Page Renderer: Inline Text Editor
An edit mode overlay that lets non-coders edit any text on any page without touching code.

**How it works:**
1. Floating "Edit" toggle button on every page (injected by an Astro integration)
2. Edit mode ON → all text elements get `contenteditable` attribute + visual highlight border
3. User clicks any text, types their change
4. "Save" button collects all changed text → writes `content.json` → triggers `astro build`
5. Site rebuilds (2-3 seconds) → page refreshes with changes

**What's editable:** Any element with `data-editable` attribute. Components automatically add this attribute to their text nodes.

**What's NOT editable in text editor mode:** Layout, component order, images, colors. Those use other tools.

**Delivery:** Must be SaaS. Customer logs into your hosted web app, edits there. You host the Astro site, rebuild on save, serve the result. Customers cannot run `npm run build` themselves.

#### AFTER Text Editor: Component Inserter
A "+" button between each row that opens a component picker. User picks from the library, a new row appears with placeholder content, they edit the text.

Row reordering uses ↑↓ arrows (not drag and drop). Moving a row up swaps it with the row above in the JSON array. Impossible to break — no accidental drops.

**Side-by-side columns:** Handled at the row level. When inserting, user picks layout (full-width / 2 columns / 3 columns). Components slot into columns. Add/remove columns within a row (max 3). This covers 95% of real page layouts without drag and drop.

#### FUTURE: SaaS Platform Wrapper
Everything above requires a hosting layer to be usable by non-coders:
- Auth (user login, site ownership)
- Site storage (each user has their page JSON + theme CSS + assets)
- Build pipeline (save → astro build → serve output)
- Custom domain or subdomain support
- Billing (Stripe, $97/$249 one-time or future subscription)

This is a 7/10 difficulty, ~4-6 weeks of work. Do not start this until the component library + editor are proven.

---

## Reference Files

| File | What It Is |
|---|---|
| `docs/info/theme-variables-canonical.css` | The CSS variable contract (80 vars, 5 theme examples) |
| `docs/info/theme-variables-guide.md` | How to use the variables |
| `docs/info/theme-dna-session-worksheet.md` | Full session notes, all decisions, all built files |
| `docs/page-prds/astro-theme/README.md` | This file |
| `server/routes/theme-generator.js` | All API endpoints |
| `server/services/astro-theme-generator/` | Full pipeline directory |
| `server/services/astro-theme-generator/dom-extractor.js` | Code-first DOM extraction |
| `server/services/astro-theme-generator/dna-confidence-scorer.js` | Confidence scoring |
| `server/services/astro-theme-generator/elementor-theme-generator.js` | 10-page Elementor output |
| `ui/src/pages/ThemeGeneratorPage.tsx` | Frontend UI |
| `public/themedna/index.html` | Sales landing page |
| `wordpress-plugin/theme-dna-generator/` | WP plugin scaffold |

---

*Last updated: 2026-04-22 — session covered: canonical CSS variable definition, three-layer architecture decision, component-based page builder plan, text editor + component inserter design, image-to-theme + style renderer compatibility confirmation.*
