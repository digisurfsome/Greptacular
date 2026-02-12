# StyleVault - Free UI Design System Gallery

## What This Is

A standalone lead-magnet web app for giving away at a live class. Users enter their email to access a gallery of 12 professional UI design systems with live previews and downloadable style sheets. Plus a screenshot extractor: upload a screenshot of any app you like, and AI analyzes it to generate a matching style sheet with extracted colors, typography, and component patterns.

The app itself uses the Minimalism style -- clean, professional, generous whitespace -- to showcase good design while letting the 12 gallery styles shine on their own terms.

## Business Context

- Given away free at a class (tomorrow night)
- Email capture feeds into a leads pipeline
- Positions the creator as a design systems authority
- Upsell path: leads receive follow-up about the full AutoForge product
- The style sheets themselves are genuinely useful and reusable

---

## App Specification (AutoForge-Compatible)

```xml
<project_specification>
  <project_name>StyleVault</project_name>

  <overview>
    StyleVault is a free email-gated gallery of 12 professional UI design systems.
    Users enter their name and email on a landing page, then gain access to browse
    all 12 styles with live component previews, color swatches, typography details,
    and one-click downloads of complete style sheets. Built as a static React app
    with Supabase for email storage and download analytics.
  </overview>

  <technology_stack>
    <frontend>
      <framework>React 19 with Vite 7</framework>
      <language>TypeScript (strict mode)</language>
      <styling>Tailwind CSS v4</styling>
      <state_management>React hooks, context for auth gate</state_management>
      <routing>React Router v7 (hash router for static hosting)</routing>
      <icons>Lucide React</icons>
      <animations>Framer Motion for page transitions and card interactions</animations>
      <port>5173</port>
    </frontend>
    <backend>
      <service>Supabase (hosted, no self-managed backend)</service>
      <database>Supabase PostgreSQL - single "leads" table</database>
      <auth>None - localStorage flag after email submission</auth>
    </backend>
    <deployment>
      <hosting>Static site (Vercel, Netlify, or Cloudflare Pages)</hosting>
      <build>vite build produces static dist/ folder</build>
    </deployment>
  </technology_stack>

  <prerequisites>
    <environment_setup>
      - Node.js 20+
      - npm package manager
      - Supabase project with anon key (free tier is fine)
      - Environment variable: VITE_SUPABASE_URL
      - Environment variable: VITE_SUPABASE_ANON_KEY
      - Environment variable: VITE_ANTHROPIC_PROXY_URL (for screenshot extractor Edge Function)
      - Supabase Edge Function deployed for screenshot analysis (calls Claude Sonnet vision API)
      - Anthropic API key stored as Supabase Edge Function secret (never exposed to client)
    </environment_setup>
  </prerequisites>

  <core_features>
    <landing_page>
      - Hero section with headline: "12 Professional UI Design Systems - Free"
      - Subtitle explaining these are ready-to-use design tokens (colors, typography, spacing, component patterns)
      - Visual preview strip showing 3-4 style cards in a horizontal scroll to tease the gallery
      - Email capture form: name field + email field + "Get Free Access" button
      - Form validation: required fields, email format check
      - On submit: store to Supabase "leads" table, set localStorage flag, redirect to gallery
      - Social proof section with placeholder metrics ("Join 500+ developers")
      - "What You Get" section: 4 feature cards (12 Design Systems, Tailwind Configs, Screenshot Extractor, Component Patterns)
      - Footer with minimal branding
    </landing_page>

    <email_gate>
      - AccessGate context provider wrapping the app
      - Check localStorage for "sv_access" key on mount
      - If present: user can access /gallery and /style/:id routes
      - If absent: redirect to landing page
      - No real auth, no tokens, no sessions - just a localStorage boolean
      - Supabase insert on email capture (fire-and-forget, do not block UX on failure)
    </email_gate>

    <style_gallery>
      - Grid of 12 style cards: 3 columns on desktop (lg), 2 on tablet (md), 1 on mobile
      - Each card contains:
        - Style name and category badge ("Core" or "Vibe")
        - Row of 5-6 color swatches from that style's palette
        - A mini live preview: a small card component (heading, paragraph, button) rendered
          using that style's actual design tokens (inline styles, not Tailwind)
        - One-line description
        - "Best for" text in muted color
        - "View Details" button
      - Click card or button: navigate to /style/:id expanded view
      - Filter tabs at top: All / Core (8 styles) / Vibe (4 styles)
      - Responsive grid with consistent card heights
    </style_gallery>

    <style_detail_page>
      - Full-page view for a single style
      - Back button to return to gallery
      - Left column (or top on mobile): style metadata
        - Name, category badge, description, philosophy quote
        - Full color palette with hex values (click to copy)
        - Typography specimen: font family, heading/body hierarchy table
        - Component specs: card, button, input patterns with exact values
        - Do's and Don'ts guidelines
      - Right column (or bottom on mobile): large live preview
        - A sample page section rendered entirely with that style's tokens
        - Contains: heading, paragraph, primary button, outline button, card with content,
          text input, and a small form
        - Background color matches the style's canvas color
        - All elements styled with inline CSS derived from the style's tokens
      - Download section at bottom:
        - "Download Style Sheet" primary CTA button
        - Format options: JSON (all tokens) / CSS (custom properties) / Tailwind Config
        - Download triggers Supabase analytics increment (style_id + format)
      - Previous/Next navigation to browse styles sequentially
    </style_detail_page>

    <screenshot_style_extractor>
      - "Extract from Screenshot" page accessible from gallery navigation
      - Upload area: drag-and-drop or click-to-upload (accepts .png, .jpg, .webp, max 5MB)
      - Image preview shown after upload with "Analyze" button
      - On analyze: sends base64 image to a Supabase Edge Function
      - The Edge Function calls Claude Sonnet API with a vision prompt that:
        1. Identifies the closest base style from the 12 known styles
        2. Detects if it's a mix of two styles (base + accent)
        3. Extracts actual hex colors, font guesses, component patterns, spacing
        4. Returns structured JSON with all extracted tokens
      - Results display:
        - "This looks like: Minimalism with Glassmorphism accents" (with confidence %)
        - Extracted color palette shown as swatches
        - Typography guess (font family, sizes)
        - Component pattern summary
        - Side-by-side: uploaded screenshot vs our closest style preview
      - Download extracted style sheet in all 3 formats (CSS, Tailwind, JSON)
      - "Browse Similar Styles" link to the matching style(s) in the gallery
      - Rate limit: 3 extractions per email per day (tracked in Supabase)
      - Loading state: animated progress bar with "Analyzing design patterns..." text
      - Error handling: graceful message if API fails, with retry button
    </screenshot_style_extractor>

    <color_palette_switcher>
      - Separate from style selection: style = structure (shapes, shadows, typography, spacing),
        palette = paint (colors only). User picks a style THEN picks a palette.
      - 15 curated UI palettes, each with 6 functional color slots:
        - brand: primary action color (buttons, links, CTAs)
        - background: page/app background
        - surface: cards, modals, panels
        - text: primary readable text
        - accent: highlights, badges, secondary actions
        - muted: borders, dividers, subtle backgrounds
      - All palettes tested for WCAG AA contrast (text on background >= 4.5:1)
      - Palette selector UI: horizontal scrollable strip of palette thumbnails (6 colored dots each)
        - Appears on the Style Detail page above the live preview
        - Click a palette → live preview instantly recolors
        - Selected palette highlighted with ring
        - "Default" option resets to the style's original colors
      - Palettes are style-agnostic: any palette works with any of the 12 styles
      - Downloaded style sheets include the selected palette's colors (not just the default)

      PALETTE DATA (15 curated palettes):

      Professional / Corporate:
      1. "Midnight Office"
         brand: #2563EB  background: #F8FAFC  surface: #FFFFFF  text: #0F172A  accent: #F59E0B  muted: #E2E8F0
         Vibe: Corporate trust, clean authority

      2. "Charcoal & Cream"
         brand: #374151  background: #FFFBEB  surface: #FFFFFF  text: #1F2937  accent: #DC2626  muted: #D1D5DB
         Vibe: Sophisticated, editorial

      3. "Deep Teal"
         brand: #0D9488  background: #F0FDFA  surface: #FFFFFF  text: #134E4A  accent: #F97316  muted: #CCFBF1
         Vibe: Calm professionalism, healthcare/finance

      Warm & Friendly:
      4. "Sunset Glow"
         brand: #EA580C  background: #FFFBEB  surface: #FFFFFF  text: #431407  accent: #7C3AED  muted: #FED7AA
         Vibe: Warm, inviting, food/lifestyle

      5. "Rose Garden"
         brand: #E11D48  background: #FFF1F2  surface: #FFFFFF  text: #1C1917  accent: #0EA5E9  muted: #FECDD3
         Vibe: Friendly, approachable, community

      6. "Terracotta"
         brand: #C2410C  background: #FEF3C7  surface: #FFFBEB  text: #292524  accent: #4F46E5  muted: #D6D3D1
         Vibe: Earthy, artisan, handmade

      Cool & Modern:
      7. "Arctic Blue"
         brand: #0284C7  background: #F0F9FF  surface: #FFFFFF  text: #0C4A6E  accent: #E11D48  muted: #BAE6FD
         Vibe: Clean tech, SaaS

      8. "Indigo Night"
         brand: #6366F1  background: #EEF2FF  surface: #FFFFFF  text: #1E1B4B  accent: #10B981  muted: #C7D2FE
         Vibe: Modern, creative tools

      9. "Mint Fresh"
         brand: #059669  background: #ECFDF5  surface: #FFFFFF  text: #064E3B  accent: #8B5CF6  muted: #A7F3D0
         Vibe: Fresh, health/wellness

      Bold & Energetic:
      10. "Electric Coral"
          brand: #F43F5E  background: #FFFFFF  surface: #FFF1F2  text: #18181B  accent: #06B6D4  muted: #F4F4F5
          Vibe: Bold, startups, social apps

      11. "Neon Slate"
          brand: #8B5CF6  background: #020617  surface: #0F172A  text: #E2E8F0  accent: #22D3EE  muted: #334155
          Vibe: Dark mode, developer tools, gaming

      12. "Sunburst"
          brand: #D97706  background: #FFFFF0  surface: #FFFFFF  text: #1C1917  accent: #2563EB  muted: #FDE68A
          Vibe: Energetic, marketplaces, education

      Nature-Inspired:
      13. "Forest Floor"
          brand: #15803D  background: #F5F5F4  surface: #FFFFFF  text: #1C1917  accent: #B45309  muted: #D6D3D1
          Vibe: Organic, outdoors, sustainability

      14. "Ocean Dusk"
          brand: #1D4ED8  background: #0F172A  surface: #1E293B  text: #CBD5E1  accent: #F59E0B  muted: #334155
          Vibe: Deep, immersive, storytelling (dark)

      15. "Sand & Stone"
          brand: #92400E  background: #FAF5F0  surface: #FFFFFF  text: #292524  accent: #0891B2  muted: #E7E5E4
          Vibe: Warm minimal, boutique, calm
    </color_palette_switcher>

    <style_downloads>
      - Each style generates three downloadable files:
        1. JSON file: complete token object (colors, typography, components, spacing)
        2. CSS file: all tokens as CSS custom properties (--sv-brand, --sv-surface-canvas, etc.)
        3. Tailwind config snippet: theme.extend object ready to paste into tailwind.config.js
      - Files are generated client-side from the hardcoded style data (no server needed)
      - Use Blob + URL.createObjectURL for browser download
      - Track downloads in Supabase: table "download_events" (style_id, format, created_at)
      - Analytics tracking is best-effort (do not block download on Supabase failure)
    </style_downloads>

    <live_preview_engine>
      - StylePreview React component that takes a style's full token set as props
      - Renders HTML elements using inline styles derived from the tokens
      - Two sizes: "compact" (for gallery cards, ~200px tall) and "full" (for detail page, ~500px tall)
      - Compact preview: single card with heading, body text, and a button
      - Full preview: hero section with heading + subtitle + buttons, then a feature card row,
        then a form section with inputs
      - Background matches the style's surface-canvas color
      - All text uses the style's font family (loaded via Google Fonts link in index.html)
      - No Tailwind classes inside previews - pure inline styles from tokens
      - Preview container has overflow:hidden and rounded corners to frame it cleanly
    </live_preview_engine>

    <responsive_design>
      - Mobile-first layout throughout
      - Landing page: stacked sections, full-width form, single-column
      - Gallery: 1-col (mobile) -> 2-col (md:768px) -> 3-col (lg:1024px)
      - Detail page: stacked on mobile, side-by-side on lg
      - Touch targets: minimum 44x44px on all interactive elements
      - Font sizes: minimum 16px on mobile inputs to prevent iOS zoom
    </responsive_design>

    <polish_and_ux>
      - Page transitions: fade between routes (Framer Motion AnimatePresence)
      - Card hover: subtle lift with shadow increase (200ms transition)
      - Color swatch click-to-copy with brief toast confirmation
      - Loading skeleton for gallery grid during initial render
      - Smooth scroll behavior
      - Focus rings on all interactive elements for keyboard navigation
      - Dynamic document.title per page ("StyleVault", "StyleVault - Gallery", "StyleVault - Minimalism")
    </polish_and_ux>
  </core_features>

  <database_schema>
    <tables>
      <leads>
        - id (UUID, PRIMARY KEY, auto-generated)
        - name (TEXT, NOT NULL)
        - email (TEXT, NOT NULL)
        - source (TEXT, DEFAULT 'stylevault')
        - created_at (TIMESTAMPTZ, DEFAULT now())
      </leads>

      <download_events>
        - id (UUID, PRIMARY KEY, auto-generated)
        - style_id (TEXT, NOT NULL)
        - format (TEXT, NOT NULL - 'json', 'css', or 'tailwind')
        - created_at (TIMESTAMPTZ, DEFAULT now())
      </download_events>
    </tables>

    <supabase_sql>
      ```sql
      -- Run in Supabase SQL Editor
      CREATE TABLE leads (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        source TEXT DEFAULT 'stylevault',
        created_at TIMESTAMPTZ DEFAULT now()
      );

      CREATE TABLE download_events (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        style_id TEXT NOT NULL,
        format TEXT NOT NULL CHECK (format IN ('json', 'css', 'tailwind')),
        created_at TIMESTAMPTZ DEFAULT now()
      );

      -- Enable Row Level Security but allow anonymous inserts
      ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
      ALTER TABLE download_events ENABLE ROW LEVEL SECURITY;

      CREATE POLICY "Allow anonymous inserts on leads"
        ON leads FOR INSERT
        WITH CHECK (true);

      CREATE POLICY "Allow anonymous inserts on download_events"
        ON download_events FOR INSERT
        WITH CHECK (true);
      ```
    </supabase_sql>
  </database_schema>

  <design_system>
    <!-- The app itself uses the Minimalism style -->
    <color_tokens>
      <brand>
        - brand-light: #E5E7EB
        - brand-DEFAULT: #111827 (near-black, Apple-inspired)
        - brand-dark: #030712
      </brand>
      <surfaces>
        - surface-canvas: #FFFFFF (pure white background)
        - surface-base: #FFFFFF (cards)
        - surface-muted: #F9FAFB (inputs, hover states)
      </surfaces>
      <text_hierarchy>
        - text-primary: #111827 (headings, key values)
        - text-secondary: #6B7280 (body text, labels)
        - text-tertiary: #9CA3AF (placeholders, inactive)
      </text_hierarchy>
      <borders>
        - border-subtle: #F3F4F6 (near-invisible dividers)
        - border-DEFAULT: #E5E7EB
      </borders>
      <status>
        - success: #10B981
        - error: #EF4444
        - warning: #F59E0B
        - info: #6366F1
      </status>
    </color_tokens>

    <typography>
      <font_family>SF Pro Display, Inter, system-ui, -apple-system, sans-serif</font_family>
      <hierarchy>
        | Level   | Size  | Weight | Line-Height | Usage                    |
        |---------|-------|--------|-------------|--------------------------|
        | Display | 48px  | 600    | 1.1         | Landing page hero        |
        | H1      | 32px  | 600    | 1.2         | Page titles              |
        | H2      | 24px  | 500    | 1.3         | Section headers          |
        | H3      | 18px  | 500    | 1.4         | Card titles              |
        | Body    | 15px  | 400    | 1.7         | Regular text             |
        | Micro   | 12px  | 400    | 1.5         | Labels, captions         |
      </hierarchy>
    </typography>

    <component_patterns>
      <cards>
        - Background: surface-base (#FFFFFF)
        - Border: 1px solid border-subtle (#F3F4F6)
        - Radius: 12px
        - Shadow: 0 1px 3px rgba(0,0,0,0.04)
        - Padding: 24px
        - Hover: shadow increase + subtle -translate-y-0.5 lift
      </cards>
      <buttons>
        <primary>Background: #111827, Text: #FFFFFF, Radius: 10px, Padding: 12px 24px</primary>
        <secondary>Background: transparent, Border: 1px solid #E5E7EB, Radius: 10px</secondary>
        <ghost>Background: transparent, Hover: #F9FAFB, Radius: 10px</ghost>
      </buttons>
      <inputs>
        - Background: #F9FAFB (surface-muted)
        - Border: none by default, 2px ring on focus (#111827)
        - Radius: 10px
        - Padding: 12px 16px
      </inputs>
    </component_patterns>

    <spacing_system>
      <base_unit>8px</base_unit>
      <density>Cozy (generous whitespace, Minimalism demands breathing room)</density>
      <scale>
        - xs: 4px
        - sm: 8px
        - md: 16px
        - lg: 24px
        - xl: 32px
        - 2xl: 48px (section gaps, generous margins)
      </scale>
    </spacing_system>

    <animations>
      - Page transitions: 200ms fade (Framer Motion)
      - Card hover: 200ms ease, translate-y -2px, shadow increase
      - Button press: active:scale-[0.98]
      - Toast: slide-in from top-right, auto-dismiss 2s
      - Color swatch copy: brief scale pulse
    </animations>
  </design_system>

  <key_interactions>
    <user_flow_primary>
      1. User arrives at landing page from class link
      2. Sees hero headline, preview strip, and email form
      3. Enters name and email, clicks "Get Free Access"
      4. Form validates, email stored in Supabase, localStorage flag set
      5. Redirected to /gallery with fade transition
      6. Browses 12 style cards, can filter by Core/Vibe
      7. Clicks a card to see the detail page
      8. Reviews full token details, sees large live preview
      9. Clicks "Download" choosing JSON/CSS/Tailwind format
      10. File downloads instantly, event logged to Supabase
      11. Uses Previous/Next to browse more styles
    </user_flow_primary>

    <returning_user_flow>
      1. User returns to the site (localStorage flag still set)
      2. Landing page detects flag and shows "Go to Gallery" button
      3. Or user navigates directly to /gallery (works because flag exists)
    </returning_user_flow>
  </key_interactions>

  <ui_layout>
    <landing_page>
      Full-width, vertically stacked sections:
      - Navbar: logo left, minimal (no navigation needed on landing page)
      - Hero: centered text, large headline, subtitle, email form below
      - Preview strip: horizontal scroll of 3-4 mini style cards
      - "What You Get" section: 3 feature cards in a row
      - Social proof bar: centered text with metrics
      - Footer: minimal branding, copyright
    </landing_page>

    <gallery_page>
      - Sticky header: logo left, filter tabs center (All/Core/Vibe), total count right
      - Grid of style cards below header
      - No sidebar, no footer - full focus on the grid
    </gallery_page>

    <detail_page>
      - Back button at top left
      - Two-column layout on desktop:
        - Left (40%): metadata, color palette, typography table, component specs
        - Right (60%): large live preview with style's background
      - Download bar: sticky at bottom or inline after preview
      - Previous/Next navigation at the very bottom
    </detail_page>
  </ui_layout>
</project_specification>
```

---

## The 12 Styles (Hardcoded Data)

All style data is embedded directly in the React app. No API calls needed. Each style object contains the full token set for rendering previews and generating downloads.

### Core Styles (8)

| # | ID | Name | Brand Color | Font Family | Category |
|---|-----|------|-------------|-------------|----------|
| 1 | flat-design | Flat Design | #3B82F6 | Inter | Core |
| 2 | minimalism | Minimalism | #111827 | SF Pro Display, Inter | Core |
| 3 | neumorphism | Neumorphism | #6366F1 | Inter | Core |
| 4 | glassmorphism | Glassmorphism | #A855F7 | Inter | Core |
| 5 | skeuomorphism | Skeuomorphism | #2563EB | Georgia, Palatino | Core |
| 6 | neubrutalism | Neubrutalism | #FACC15 | Space Grotesk, DM Sans | Core |
| 7 | bauhaus | Bauhaus | #DC2626 | DM Sans, Helvetica Neue | Core |
| 8 | claymorphism | Claymorphism | #F59E0B | Nunito, Quicksand | Core |

### Vibe Styles (4)

| # | ID | Name | Brand Color | Font Family | Category |
|---|-----|------|-------------|-------------|----------|
| 9 | retro-futurism | Retro Futurism | #D946EF | Orbitron, Space Mono | Vibe |
| 10 | cyberpunk | Cyberpunk | #06B6D4 | JetBrains Mono, Fira Code | Vibe |
| 11 | dark-mode | Dark Mode Elegant | #3B82F6 | Inter | Vibe |
| 12 | warmer-shades | Warmer Shades | #D97706 | Lora, Merriweather | Vibe |

### Key Color Swatches Per Style (for gallery cards)

Each gallery card shows these swatches (derived from the style's color_tokens):

- **Flat Design**: #3B82F6, #FFFFFF, #F8FAFC, #0F172A, #E2E8F0, #22C55E
- **Minimalism**: #111827, #FFFFFF, #F9FAFB, #6B7280, #F3F4F6, #6366F1
- **Neumorphism**: #6366F1, #E0E5EC, #D1D9E6, #2D3748, #818CF8, #48BB78
- **Glassmorphism**: #A855F7, #667eea, #764ba2, #FFFFFF, rgba(255,255,255,0.15), #4ADE80
- **Skeuomorphism**: #2563EB, #E8E0D8, #F5F0EB, #1A1A1A, #C4B8AB, #22A559
- **Neubrutalism**: #FACC15, #FFFBEB, #FFFFFF, #18181B, #FEF3C7, #EF4444
- **Bauhaus**: #DC2626, #2563EB, #FACC15, #FAFAFA, #0A0A0A, #22C55E
- **Claymorphism**: #F59E0B, #FFF7ED, #FFFFFF, #292524, #FEF3E2, #4ADE80
- **Retro Futurism**: #D946EF, #06B6D4, #F97316, #0C0A1A, #1A1730, #4ADE80
- **Cyberpunk**: #06B6D4, #22D3EE, #F43F5E, #09090B, #18181B, #FBBF24
- **Dark Mode Elegant**: #3B82F6, #0F172A, #1E293B, #F1F5F9, #334155, #4ADE80
- **Warmer Shades**: #D97706, #FFFBF5, #FFF8F0, #292524, #F5E6D3, #65A30D

---

## Google Fonts Required

Load these font families in `index.html` via Google Fonts link:

```
Inter, Space Grotesk, DM Sans, Nunito, Quicksand, Orbitron, Space Mono,
JetBrains Mono, Fira Code, Lora, Merriweather
```

Georgia and Palatino are system fonts (no need to load). SF Pro Display falls back to Inter.

Suggested Google Fonts link:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&family=Lora:wght@400;500;600;700&family=Merriweather:wght@400;700&family=Nunito:wght@400;500;600;700;800&family=Orbitron:wght@400;500;600;700;800&family=Quicksand:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
```

---

## Download File Formats

### 1. CSS Custom Properties (`{style-name}-tokens.css`)

```css
/* StyleVault - Flat Design Tokens */
/* https://stylevault.app */

:root {
  /* Brand */
  --sv-brand-light: #60A5FA;
  --sv-brand: #3B82F6;
  --sv-brand-dark: #2563EB;

  /* Surfaces */
  --sv-surface-canvas: #FFFFFF;
  --sv-surface-base: #F8FAFC;
  --sv-surface-muted: #F1F5F9;

  /* Text */
  --sv-text-primary: #0F172A;
  --sv-text-secondary: #475569;
  --sv-text-tertiary: #94A3B8;

  /* Borders */
  --sv-border-subtle: #E2E8F0;
  --sv-border: #CBD5E1;

  /* Status */
  --sv-success: #22C55E;
  --sv-error: #EF4444;
  --sv-warning: #F59E0B;
  --sv-info: #3B82F6;

  /* Typography */
  --sv-font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --sv-font-display: 36px;
  --sv-font-h1: 28px;
  --sv-font-h2: 22px;
  --sv-font-h3: 18px;
  --sv-font-body: 14px;
  --sv-font-micro: 12px;

  /* Components */
  --sv-radius-card: 8px;
  --sv-radius-input: 6px;
  --sv-radius-btn: 6px;
  --sv-shadow-card: none;
  --sv-card-padding: 16px;
  --sv-btn-padding: 10px 20px;

  /* Spacing */
  --sv-space-base: 4px;
  --sv-space-card-gap: 16px;
  --sv-space-section-gap: 24px;
}
```

### 2. Tailwind Config (`{style-name}-tailwind.js`)

```javascript
// StyleVault - Flat Design Tailwind Config
// Paste into your tailwind.config.js theme.extend

/** @type {import('tailwindcss').Config['theme']['extend']} */
const flatDesignTheme = {
  colors: {
    brand: { light: "#60A5FA", DEFAULT: "#3B82F6", dark: "#2563EB" },
    surface: { canvas: "#FFFFFF", base: "#F8FAFC", muted: "#F1F5F9" },
    text: { primary: "#0F172A", secondary: "#475569", tertiary: "#94A3B8" },
    border: { subtle: "#E2E8F0" },
  },
  fontFamily: {
    sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
  },
  borderRadius: {
    card: "8px",
    input: "6px",
    btn: "6px",
  },
  boxShadow: {
    card: "none",
  },
};
```

### 3. JSON Tokens (`{style-name}-tokens.json`)

The complete style object as-is from the data, including color_tokens, typography, components, spacing, and tailwind_config.

---

## Feature Breakdown (AutoForge-Compatible)

These features are ordered by dependency and map to AutoForge's feature-by-feature build approach. Each feature is independently testable.

### Feature 1: Project Scaffolding and Routing
**Priority: 1 (Foundation)**

- Initialize Vite + React 19 + TypeScript project
- Install dependencies: tailwindcss v4, react-router-dom v7, lucide-react, framer-motion, @supabase/supabase-js
- Configure Tailwind v4 with the Minimalism design tokens as custom theme
- Set up HashRouter with three routes: `/` (landing), `/gallery`, `/style/:id`
- Create bare page components: LandingPage, GalleryPage, StyleDetailPage
- Create shared Layout component with minimal header (logo text only)
- Verify all routes render and navigation works

**Steps:**
1. Run `npm create vite@latest . -- --template react-ts` and install deps
2. Configure `tailwind.config.ts` with Minimalism color tokens, fonts, spacing
3. Set up `src/router.tsx` with HashRouter and route definitions
4. Create `src/pages/LandingPage.tsx`, `GalleryPage.tsx`, `StyleDetailPage.tsx` as stubs
5. Create `src/components/Layout.tsx` with Outlet and header
6. Verify dev server starts, all three routes render placeholder content

### Feature 2: Style Data Module
**Priority: 1 (Foundation)**
**Depends on: Feature 1**

- Create `src/data/styles.ts` with the complete 12-style registry as a typed array
- Define TypeScript interfaces: StyleData, ColorTokens, Typography, Components, Spacing, TailwindConfig
- Each style has: id, name, category, description, bestFor, philosophy, colorTokens, typography, components, spacing, tailwindConfig, dosAndDonts
- Export helper functions: getStyleById(id), getStylesByCategory(category), getAllStyles()
- Include all color values, font families, component specs, and spacing values exactly as defined

**Steps:**
1. Create `src/data/types.ts` with all TypeScript interfaces
2. Create `src/data/styles.ts` with the full 12-style array matching the spec above
3. Create `src/data/helpers.ts` with lookup/filter functions
4. Export everything from `src/data/index.ts` barrel file
5. Verify: import the data in a test component, confirm all 12 styles load with correct types

### Feature 3: Supabase Client and Email Storage
**Priority: 2**
**Depends on: Feature 1**

- Create `src/lib/supabase.ts` initializing the Supabase client from env vars
- Create `src/lib/leads.ts` with `submitLead(name, email)` function that inserts into the "leads" table
- Create `src/lib/analytics.ts` with `trackDownload(styleId, format)` function for the "download_events" table
- Both functions are fire-and-forget: return silently on error (console.warn only)
- Create `.env.example` documenting VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
- If env vars are missing, all Supabase functions silently no-op (app works without Supabase for local dev)

**Steps:**
1. Install `@supabase/supabase-js`
2. Create `src/lib/supabase.ts` with createClient using env vars
3. Create `src/lib/leads.ts` with the submitLead function, try/catch wrapped
4. Create `src/lib/analytics.ts` with the trackDownload function, try/catch wrapped
5. Create `.env.example` with placeholder values
6. Verify: call submitLead with test data, confirm it either succeeds or silently handles missing config

### Feature 4: Access Gate (Email Wall)
**Priority: 2**
**Depends on: Feature 1**

- Create `src/context/AccessContext.tsx` with React context
- Provider checks localStorage for `sv_access` key on mount
- Exposes `hasAccess: boolean` and `grantAccess(): void` (sets localStorage + updates state)
- Create `src/components/ProtectedRoute.tsx` wrapper: if no access, redirect to `/`
- Wrap `/gallery` and `/style/:id` routes with ProtectedRoute
- Landing page checks `hasAccess`: if true, show "Go to Gallery" button alongside the form

**Steps:**
1. Create AccessContext with provider, useAccess hook
2. Create ProtectedRoute component using Navigate from react-router
3. Wrap gallery and detail routes in router config
4. Update LandingPage to conditionally show "Go to Gallery" when already authenticated
5. Verify: without localStorage flag, /gallery redirects to /. After setting flag, /gallery renders

### Feature 5: Landing Page
**Priority: 3**
**Depends on: Features 1, 2, 3, 4**

- Hero section: large Display-size headline, Body-size subtitle, generous whitespace
- Email form: name input + email input + submit button, all using Minimalism style tokens
- Form validation: both required, email regex check, inline error messages below fields
- On submit: call submitLead(), then grantAccess(), then navigate to /gallery
- Button shows loading spinner during submission (brief, ~500ms minimum for perceived feedback)
- Preview strip below hero: horizontal row of 3-4 mini style cards from the data
  - Each mini card is ~160px wide, shows style name + 4 color dots + tiny preview rectangle
  - Horizontal scroll on mobile, centered row on desktop
- "What You Get" section: 3 cards (Design Tokens, Tailwind Config, Component Patterns) with Lucide icons
- Social proof bar: centered text "Join 500+ developers using these design systems"
- Footer: "Made with care" + current year

**Steps:**
1. Build the hero section with headline and subtitle
2. Build the email capture form with validation and submit handler
3. Wire form to Supabase submitLead and AccessContext grantAccess
4. Build the preview strip with mini style cards (horizontal layout)
5. Build the "What You Get" section with 3 feature cards
6. Build the social proof bar and footer
7. Verify: form validates, submits, sets access, redirects to /gallery

### Feature 6: Live Preview Component (StylePreview)
**Priority: 3**
**Depends on: Feature 2**

- Create `src/components/StylePreview.tsx`
- Props: `tokens: StyleData['colorTokens' & related]`, `size: 'compact' | 'full'`
- Renders sample UI elements using pure inline styles derived from the token values
- Compact mode (~200px tall): a single card containing a heading, one paragraph, and a primary button
- Full mode (~500px tall): hero heading + subtitle + 2 buttons, then a row of 2 feature cards, then a form with name input + email input + submit button
- Container: set background to the style's surface.canvas, overflow hidden, rounded corners (12px)
- All text elements use the style's font family (via inline `fontFamily`)
- Buttons use the style's button tokens (bg, text color, radius, padding, shadow, border)
- Cards use the style's card tokens (bg, border, radius, shadow, padding)
- Inputs use the style's input tokens
- No Tailwind inside the preview -- everything is inline CSS so it works regardless of the host app's styling

**Steps:**
1. Create the component with `compact` and `full` conditional rendering
2. Build a helper function `tokensToStyles(style)` that maps style tokens to React CSSProperties objects for each element type
3. Implement compact mode: card with heading, paragraph, button
4. Implement full mode: hero + card row + form
5. Verify: render with at least 3 different style datasets, confirm visual differences are clear

### Feature 7: Style Gallery Page
**Priority: 4**
**Depends on: Features 2, 4, 6**

- Page header: "Design System Gallery" title, filter tabs (All / Core / Vibe)
- Filter tabs use URL search params or local state
- Grid: CSS grid, 3 cols on lg, 2 on md, 1 on mobile
- Each StyleCard component:
  - Style name (H3) and category badge (small pill: "Core" in gray, "Vibe" in purple)
  - Row of 6 color swatches (small circles, 24px diameter, with border for light colors)
  - StylePreview in compact mode showing the mini live preview
  - Description text (1 line, truncated with ellipsis)
  - "Best for" text in muted color
  - "View Details" link/button
- Click anywhere on card navigates to `/style/:id`
- Card hover: slight lift (translate-y -2px) + shadow increase, 200ms transition
- Animate cards in with staggered fade-in on mount (Framer Motion)

**Steps:**
1. Create `src/components/StyleCard.tsx` with all card content
2. Build the filter tabs with state management
3. Build the grid layout with responsive columns
4. Wire card clicks to navigate to detail page
5. Add hover animation and staggered entrance animation
6. Verify: all 12 cards render, filter tabs work, clicking navigates correctly

### Feature 8: Download Generator
**Priority: 4**
**Depends on: Features 2, 3**

- Create `src/lib/downloads.ts` with three generator functions:
  - `generateCSS(style: StyleData): string` - outputs CSS custom properties file content
  - `generateTailwind(style: StyleData): string` - outputs a JS/TS config snippet
  - `generateJSON(style: StyleData): string` - outputs the full token object as formatted JSON
- Create `src/lib/downloadFile.ts` with `triggerDownload(content, filename, mimeType)` using Blob + URL.createObjectURL + click-to-download pattern
- CSS generator: maps all tokens to `--sv-*` custom properties in a `:root {}` block with header comment
- Tailwind generator: creates a `theme.extend` object as a JS module export with header comment
- JSON generator: wraps the complete style data in a clean JSON structure with metadata (name, version, generated date)
- After triggering download, call `trackDownload(styleId, format)` for Supabase analytics

**Steps:**
1. Create the three generator functions with formatted output
2. Create the triggerDownload utility
3. Create a `downloadStyle(style, format)` orchestrator function that generates content, triggers download, and tracks analytics
4. Verify: call each generator, confirm output is well-formatted and valid

### Feature 9: Style Detail Page
**Priority: 5**
**Depends on: Features 2, 6, 8**

- Route: `/style/:id` - extract id from URL params, look up style from data
- If style not found: show a "Style not found" message with back link
- Back button at top left: "Back to Gallery" with left arrow icon
- Two-column layout on desktop (lg), stacked on mobile:
  - Left column (metadata):
    - Style name (H1), category badge
    - Description paragraph
    - Philosophy quote in a subtle blockquote
    - Color palette: grid of swatches (48px circles) with hex labels, click-to-copy
    - Typography table: font family name, hierarchy table with Level/Size/Weight columns
    - Component specs: cards, buttons, inputs details in a clean list
    - Do's (green checkmarks) and Don'ts (red X marks) lists
  - Right column (preview):
    - StylePreview in full mode, filling the column
    - Takes up ~60% width on desktop
- Download section below the columns:
  - "Download This Style" heading
  - Three buttons: "CSS Variables" / "Tailwind Config" / "JSON Tokens"
  - Each triggers the corresponding download
- Previous/Next navigation at the bottom: links to adjacent styles in the list
- Color swatch click-to-copy: copies hex value, shows brief toast "Copied #3B82F6"

**Steps:**
1. Set up the route param extraction and style lookup
2. Build the metadata column with all sections
3. Build the preview column with full-size StylePreview
4. Build the download section with three format buttons
5. Build the Previous/Next navigation
6. Implement click-to-copy on color swatches with toast feedback
7. Handle 404 case when style ID is invalid
8. Verify: navigate to each of the 12 styles, confirm all data renders, downloads work

### Feature 10: Toast Notification System
**Priority: 3**
**Depends on: Feature 1**

- Create `src/components/Toast.tsx` and `src/context/ToastContext.tsx`
- Simple toast system: `showToast(message, type?)` where type is 'success' | 'info' | 'error'
- Toast slides in from top-right, auto-dismisses after 2 seconds
- Stacks multiple toasts vertically
- Used for: color copy confirmation, download confirmation, error feedback
- Styled with Minimalism tokens: clean, subtle, with small icon

**Steps:**
1. Create ToastContext with provider and useToast hook
2. Create Toast component with slide-in animation (Framer Motion)
3. Implement auto-dismiss timer and stacking
4. Style with success/info/error variants
5. Verify: trigger multiple toasts, confirm they stack and auto-dismiss

### Feature 12: Screenshot Style Extractor
**Priority: 5**
**Depends on: Features 2, 3, 6, 10**

- New page: `/extract` accessible from gallery header navigation
- Upload area with drag-and-drop zone + click-to-upload button
- Accepts .png, .jpg, .webp (max 5MB, validate client-side)
- After upload: shows image preview + "Analyze Design" button
- On analyze: converts image to base64, calls Supabase Edge Function `extract-style`
- The Edge Function:
  - Receives base64 image
  - Calls Claude Sonnet API with vision prompt (see screenshot-style-extractor-handoff.md for full prompt)
  - Identifies closest style(s) from the 12 known styles
  - Extracts hex colors, font guesses, component patterns, spacing estimates
  - Returns structured JSON response
- Results display:
  - Style match: "This looks like: **Minimalism** with **Glassmorphism** accents" + confidence badges
  - Extracted color palette: row of color swatches with hex values (click to copy)
  - Typography guess: font family name, size hierarchy
  - Side-by-side comparison: uploaded screenshot (left) | closest style's live preview (right)
  - "Browse This Style" button links to the matched style's detail page
- Download section: same 3 formats (CSS, Tailwind, JSON) but using the EXTRACTED tokens, not the predefined ones
- Rate limit: 3 extractions per day per email (check against Supabase `extraction_events` table)
- Loading state: progress bar animation with rotating tips ("Analyzing color palette...", "Detecting typography...", "Mapping component patterns...")
- Error handling: retry button on API failure, friendly message

**Steps:**
1. Create `src/pages/ExtractPage.tsx` with upload zone and results layout
2. Create `src/components/ImageUploader.tsx` with drag-and-drop + file input
3. Create `src/lib/extractor.ts` with `analyzeScreenshot(base64)` function calling the Edge Function
4. Create Supabase Edge Function `supabase/functions/extract-style/index.ts` with the Claude vision API call
5. Build the results display with style match, color swatches, and side-by-side preview
6. Wire up download buttons for extracted tokens
7. Add rate limiting check (query extraction_events count for today)
8. Add navigation link in gallery header
9. Verify: upload a screenshot, get analysis, download extracted tokens

**Supabase Edge Function (`supabase/functions/extract-style/index.ts`):**
```typescript
// Receives: { image: string (base64), email: string }
// Calls Claude Sonnet with vision prompt
// Returns: { identified_style, extracted_tokens, outputs }
// Anthropic API key stored as Edge Function secret
// Rate limit: check extraction_events table, reject if >= 3 today
```

**New Supabase table:**
```sql
create table extraction_events (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  identified_style text,
  confidence numeric,
  created_at timestamptz default now()
);
alter table extraction_events enable row level security;
create policy "Anyone can insert" on extraction_events for insert with check (true);
```

### Feature 13: Color Palette Switcher
**Priority: 5**
**Depends on: Features 2, 6, 9**

- 15 curated color palettes hardcoded in `src/data/palettes.ts`
- Each palette has 6 slots: brand, background, surface, text, accent, muted
- Palette selector appears on the Style Detail page, above the live preview
- UI: horizontal scrollable strip of palette thumbnails
  - Each thumbnail: a row of 6 small color circles (16px) + palette name below
  - Selected palette has a ring highlight
  - First option is "Default" which uses the style's built-in colors
  - Click a palette → live preview re-renders instantly with new colors
- The StylePreview component already takes tokens as props, so palette switching just
  overrides the color tokens while keeping typography/spacing/component tokens from the style
- Create `src/lib/paletteUtils.ts` with `applyPalette(styleTokens, palette)` that merges
  palette colors into a style's token set
- Downloads include the selected palette: if user selected "Sunset Glow" palette on
  Minimalism style, the CSS/Tailwind/JSON files contain Sunset Glow colors, not Minimalism defaults
- Palette categories shown as subtle section headers: Professional, Warm, Cool, Bold, Nature
- On mobile: palette strip wraps to 2 rows or scrolls horizontally

**Steps:**
1. Create `src/data/palettes.ts` with all 15 palettes as typed data (PaletteData interface)
2. Create `src/components/PaletteStrip.tsx` - horizontal scrollable palette selector
3. Create `src/lib/paletteUtils.ts` with `applyPalette()` merge function
4. Add PaletteStrip to StyleDetailPage above the preview, with state for selected palette
5. Wire palette selection to StylePreview - pass merged tokens when palette is active
6. Update download functions to accept optional palette override
7. Verify: select Minimalism, switch through 3+ palettes, confirm preview updates and downloads match

### Feature 11: Page Transitions and Final Polish
**Priority: 6**
**Depends on: Features 5, 7, 9, 10, 12, 13**

- Wrap route outlet in Framer Motion AnimatePresence for page transitions
- Add fade + slight slide-up on page enter, fade out on exit (200ms)
- Dynamic document.title updates on each page via useEffect
- Add favicon (simple "SV" monogram or a vault icon)
- Add meta description and Open Graph tags in index.html
- Loading skeleton for gallery: 12 placeholder cards with shimmer animation while fonts load
- Ensure all focus rings are visible on keyboard tab navigation
- Test complete flow end to end: landing -> form -> gallery -> detail -> download
- Audit for any console errors or TypeScript warnings

**Steps:**
1. Add AnimatePresence to the Layout component around Outlet
2. Add motion.div wrappers to each page with enter/exit animations
3. Add useEffect to each page updating document.title
4. Add favicon, meta tags, and Open Graph tags
5. Build a skeleton/shimmer component for the gallery grid
6. Perform keyboard navigation audit and fix any missing focus rings
7. Full end-to-end verification of the complete user flow

---

## File Structure

```
stylevault/
├── index.html                          # Google Fonts links, meta tags, favicon
├── .env.example                        # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts                  # Minimalism tokens for the app shell
├── src/
│   ├── main.tsx                        # App entry point
│   ├── App.tsx                         # Router provider
│   ├── router.tsx                      # Route definitions with ProtectedRoute
│   ├── styles/
│   │   └── globals.css                 # Tailwind directives, base styles
│   ├── context/
│   │   ├── AccessContext.tsx            # Email gate context
│   │   └── ToastContext.tsx             # Toast notification context
│   ├── components/
│   │   ├── Layout.tsx                  # Shared layout with header
│   │   ├── ProtectedRoute.tsx          # Access gate wrapper
│   │   ├── StylePreview.tsx            # Live preview engine (compact/full)
│   │   ├── StyleCard.tsx               # Gallery card component
│   │   ├── ColorSwatch.tsx             # Clickable color circle with copy
│   │   ├── Toast.tsx                   # Toast notification component
│   │   ├── LoadingSkeleton.tsx         # Shimmer placeholder for gallery
│   │   └── CategoryBadge.tsx           # "Core" / "Vibe" pill badge
│   ├── pages/
│   │   ├── LandingPage.tsx             # Hero + form + preview strip
│   │   ├── GalleryPage.tsx             # Filter tabs + style grid
│   │   ├── StyleDetailPage.tsx         # Full style view + download
│   │   └── ExtractPage.tsx             # Screenshot upload + AI analysis
│   ├── data/
│   │   ├── index.ts                    # Barrel export
│   │   ├── types.ts                    # TypeScript interfaces
│   │   ├── styles.ts                   # All 12 styles with full tokens
│   │   └── helpers.ts                  # Lookup and filter functions
│   └── lib/
│       ├── supabase.ts                 # Supabase client init
│       ├── leads.ts                    # Email storage function
│       ├── analytics.ts               # Download tracking
│       ├── downloads.ts               # CSS/Tailwind/JSON generators
│       ├── downloadFile.ts            # Browser download trigger utility
│       └── extractor.ts              # Screenshot analysis API call
├── supabase/
│   └── functions/
│       └── extract-style/
│           └── index.ts               # Edge Function: Claude vision API for style extraction
```

---

## Supabase Setup Checklist

1. Create a free Supabase project at https://supabase.com
2. Run the SQL from the `<supabase_sql>` section above in the SQL Editor
3. Copy the project URL and anon key from Settings > API
4. Create a `.env` file with `VITE_SUPABASE_URL=...` and `VITE_SUPABASE_ANON_KEY=...`
5. The anon key is safe to expose in client-side code (RLS policies control access)
6. No service role key is needed -- all operations use the anon key with RLS

---

## Deployment Checklist

1. Run `npm run build` to produce `dist/` folder
2. Deploy `dist/` to Vercel, Netlify, or Cloudflare Pages
3. Set environment variables (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY) in the hosting platform
4. Verify: visit the URL, submit the email form, browse gallery, download a style
5. Share the URL at the class

---

## Name Alternatives Considered

- **StyleVault** (recommended) - evokes a vault of valuable design assets, implies security and collection
- **DesignTokens.free** - descriptive but less brandable
- **StyleKit** - short but generic, likely taken
- **TokenDrop** - implies a giveaway/airdrop, catchy
- **12Styles** - descriptive, easy to remember, good for a class handout URL
