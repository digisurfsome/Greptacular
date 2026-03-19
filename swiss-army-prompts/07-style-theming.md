# MODULE 07: STYLE & THEMING PROMPT

## Apply Your Visual Identity — Brand Colors, Typography, Landing Page

**What this does:** Transforms your functional app into a visually distinctive product. Applies your specific brand colors, typography feel, and design personality. Builds a real landing page. This is where your app stops looking like "every other Tailwind app."

**Prerequisite:** Modules 01-06 should be complete. This module reskins everything.

**The mentor's approach:** He uses a separate "Style Guide Generator Prompt" that takes a screenshot of an app/website you like and produces a detailed style sheet. That's brilliant — we keep that concept but adapt it for Tailwind CSS v4 design tokens.

---

## --- START PROMPT ---

## TASK: Apply Visual Style and Build the Landing Page

Transform this app's visual identity. Apply the style guide below to every component, page, and layout element. Then build a real landing page.

Read these files first: `src/index.css` (design tokens), `src/components/Layout.tsx`, `src/components/Sidebar.tsx`, `src/pages/LandingPage.tsx`, and scan all files in `src/components/ui/`.

---

## SECTION 1: STYLE GUIDE [FILL THIS IN]

*Option A: Describe your style in plain language.*
*Option B: Paste output from a Style Guide Generator.*
*Option C: Provide a screenshot URL and I'll analyze it.*

**Visual Style:** [Modern / Minimal / Playful / Corporate / Dark & Techy / Warm & Friendly]

**Primary Brand Color:** [e.g., "#DFFF5E" or "electric lime" or "deep purple"]
**Secondary Color:** [e.g., "#10B981" or "coral" or "warm gray"]
**Accent Color (optional):** [e.g., for highlights, badges, CTAs]

**Personality/Tone:** [Friendly / Professional / Casual / Serious / Playful / Premium]

**Design Inspiration:** [Optional — "Like Notion" or "Like Linear" or "Like Stripe" or "Clean SaaS dashboard" or "Warm productivity app"]

**Dark Mode Primary:** [Is the app dark-first or light-first? Default: light-first]

---

## SECTION 2: UPDATE DESIGN TOKENS

Based on the style guide above, update **src/index.css** `@theme` block.

### Color Token Mapping

Replace the placeholder brand colors with the actual brand:

```css
@theme {
  /* Brand — derived from the primary color in 3 shades */
  --color-brand-light: [lighter shade — for hover backgrounds, badges];
  --color-brand: [primary — for buttons, links, active states];
  --color-brand-dark: [darker shade — for button hover, emphasis];

  /* Surface — adjust warmth/coolness to match the personality */
  /* Cool personality (techy, minimal): use blue-gray tones */
  /* Warm personality (friendly, casual): use warm gray tones */
  --color-surface-canvas: [page background];
  --color-surface-base: [card/panel background];
  --color-surface-muted: [input backgrounds, hover backgrounds];

  /* Text — ensure contrast ratios meet WCAG AA (4.5:1 for body text) */
  --color-text-primary: [main text — near black or near white];
  --color-text-secondary: [secondary text — medium contrast];
  --color-text-tertiary: [least important text — low contrast but still readable];

  /* Border */
  --color-border-subtle: [dividers, card borders — should be subtle];
}
```

### Dark Mode Tokens

Update the `.dark` block with corresponding dark mode colors:

```css
.dark {
  --color-surface-canvas: [dark page background];
  --color-surface-base: [dark card background];
  --color-surface-muted: [dark input/hover background];
  --color-text-primary: [light text on dark];
  --color-text-secondary: [medium text on dark];
  --color-text-tertiary: [dim text on dark];
  --color-border-subtle: [dark dividers];
}
```

**RULE: If the style guide is dark-first, still define light mode as the :root default and dark mode in .dark. The theme toggle must work both ways.**

### Typography Feel

Adjust the font stack based on personality:

| Personality | Font Stack |
|-------------|------------|
| Modern/Clean | `'Inter', ui-sans-serif, system-ui, sans-serif` (default) |
| Premium/Editorial | `'Plus Jakarta Sans', 'Inter', ui-sans-serif, sans-serif` |
| Techy/Code | `'JetBrains Mono', 'Fira Code', monospace` (for headers only) |
| Warm/Friendly | `'Nunito', 'Inter', ui-sans-serif, sans-serif` |
| Corporate | `'IBM Plex Sans', 'Inter', ui-sans-serif, sans-serif` |

If changing from Inter, update the Google Fonts `<link>` in `index.html`.

### Corner Radius

Adjust `--radius-card` based on personality:

| Feel | Radius |
|------|--------|
| Sharp/Corporate | `8px` |
| Standard | `12px` (default) |
| Soft/Friendly | `16px` |
| Rounded/Playful | `20px` |

### Shadow Depth

Adjust card shadow:

| Feel | Shadow |
|------|--------|
| Flat/Minimal | `none` or `0 0 0 1px var(--color-border-subtle)` |
| Standard | `0 1px 3px rgba(0,0,0,0.05)` (default) |
| Elevated | `0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)` |

---

## SECTION 3: COMPONENT RESKINNING

After updating tokens, audit each component to ensure the new brand works:

### Buttons
- Primary button text color: ensure contrast against brand color
  - Light brand colors (yellow, lime, cyan) → use dark text (`text-gray-900`)
  - Dark brand colors (purple, blue, red) → use white text (`text-white`)
- Check all button variants still look good with new colors

### Cards
- Verify border, shadow, and radius match the new feel
- Hover effect should feel natural with new shadow depth

### Sidebar
- Active nav item highlight should use `bg-brand/10 text-brand` (brand at 10% opacity for background)
- Ensure sidebar feels cohesive with the new palette

### Badges / Status Indicators
- If your app has status badges (draft, active, completed), choose colors that work with the brand:
  - Don't use brand color for status — it creates confusion
  - Use semantic colors: green for success, yellow for pending, red for error, gray for draft

### Login Page
- Update to reflect brand personality
- Consider adding a brand-colored gradient or pattern to one side (split layout on desktop)

---

## SECTION 4: BUILD THE REAL LANDING PAGE

Replace the placeholder `LandingPage.tsx` with a proper marketing-style landing page.

### Structure

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR: Logo                    [Sign In] [Get Started] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│           HERO SECTION                                   │
│  Big headline (value proposition)                        │
│  Subtitle (one sentence description)                     │
│  [Primary CTA Button]    [Secondary CTA]                 │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│           FEATURES SECTION (3 cards)                     │
│  ┌────────┐  ┌────────┐  ┌────────┐                    │
│  │ Icon   │  │ Icon   │  │ Icon   │                    │
│  │ Title  │  │ Title  │  │ Title  │                    │
│  │ Desc   │  │ Desc   │  │ Desc   │                    │
│  └────────┘  └────────┘  └────────┘                    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│           HOW IT WORKS (3 steps)                         │
│  1. Step one      2. Step two      3. Step three        │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│           FINAL CTA                                      │
│  Ready to get started?                                   │
│  [Get Started — It's Free]                               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  FOOTER: © 2026 AppName                                  │
└──────────────────────────────────────────────────────────┘
```

### Requirements

1. **Navbar:** Sticky top, transparent initially, becomes solid on scroll
2. **Hero:** Full viewport height (min-h-screen or large padding), compelling headline
3. **Features:** 3 cards with Lucide icons, responsive grid
4. **How it works:** 3 numbered steps
5. **Final CTA:** Centered call to action with brand button
6. **Footer:** Simple, copyright + optional links
7. **Auth-aware:** Show "Go to Dashboard" if signed in, "Get Started" if not
8. **Responsive:** All sections stack on mobile
9. **Uses brand colors** from the updated design tokens
10. **Smooth scroll** between sections (optional)

---

## SECTION 5: UPDATE FAVICON

Update `public/favicon.svg` to use the new brand color:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="[BRAND_COLOR]"/>
  <text x="16" y="22" text-anchor="middle" font-family="system-ui" font-weight="bold" font-size="18" fill="[CONTRAST_TEXT_COLOR]">[FIRST_LETTER]</text>
</svg>
```

---

## SECTION 6: VERIFY

1. `npm run build` — zero errors
2. Light mode looks correct on: Landing, Login, Dashboard, List, Detail, Create/Edit, Profile
3. Dark mode looks correct on all the same pages
4. Brand color has sufficient contrast for:
   - Button text readability
   - Link visibility against background
   - Active sidebar item visibility
5. Mobile layout still works after reskinning
6. Landing page is compelling and professional

---

## COMMIT

```bash
git add -A
git commit -m "style: apply brand identity — [describe the style, e.g., 'dark premium theme with purple accents']"
```

---

## REUSABLE PATTERN: STYLE GUIDE FROM SCREENSHOT

If you have a screenshot of an app/website you want to match, use this sub-prompt before running this module:

```
Analyze this screenshot and extract a complete style guide:
1. Primary color (hex)
2. Secondary color (hex)
3. Background color
4. Text colors (primary, secondary, tertiary)
5. Border/divider color
6. Corner radius (sharp/standard/soft/rounded)
7. Shadow depth (flat/standard/elevated)
8. Typography feel (clean/premium/techy/warm/corporate)
9. Overall personality in 3 words
10. Is it dark-first or light-first?

Format the output so I can paste it directly into the style guide section of my build prompt.
```

---

## --- END PROMPT ---
