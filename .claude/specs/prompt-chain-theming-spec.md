# Prompt Chain Dashboard — Theming Spec

> **Purpose:** This document maps every visual property of the Apps Script Web App
> (prompt chain dashboard) so that the Style Set tool can generate themes for it.
> Feed a screenshot of any app/website into the Style Set tool → it outputs a theme →
> that theme plugs directly into this spec → the dashboard now looks like that app/website.

---

## THE KEY INSIGHT

The Google Sheet itself? Proprietary styling, limited control.
The **Apps Script Web App**? Pure HTML + CSS. Fully themeable. Same as any website.

When deployed, it's just a web page at a URL. The browser sees HTML and CSS.
Your Style Set tool already knows how to theme HTML/CSS.
So: screenshot of any app → Style Set → theme variables → paste into this dashboard → done.

---

## ARCHITECTURE: Where Styles Live

```
Apps Script Web App
  └── index.html
       └── <style> tag
            └── CSS Custom Properties (variables) ← THIS IS WHAT GETS THEMED
                 └── :root { --var-name: value; }
```

ALL styling flows through CSS custom properties (variables) defined in one place.
Change the variables → entire app re-themes instantly.

---

## THEME VARIABLE SPEC

These are the exact variables the dashboard uses. This is what your Style Set
tool needs to output.

### Core Colors

```css
:root {
  /* === BACKGROUND === */
  --bg-primary: #0f0f0f;          /* Page background */
  --bg-secondary: #1a1a1a;        /* Card/step background */
  --bg-tertiary: #0a0a0a;         /* Output areas, code blocks */
  --bg-input: #0f0f0f;            /* Input fields background */
  --bg-header: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);  /* Header gradient */

  /* === TEXT === */
  --text-primary: #e5e5e5;        /* Main body text */
  --text-secondary: #888888;      /* Labels, helper text, descriptions */
  --text-muted: #666666;          /* Placeholder text, subtle info */
  --text-code: #aaaaaa;           /* Output/code text (before content) */
  --text-code-active: #e5e5e5;    /* Output/code text (with content) */

  /* === ACCENT (Primary Brand Color) === */
  --accent-primary: #7b68ee;      /* Buttons, active states, links */
  --accent-secondary: #00d2ff;    /* Gradient end, highlights */
  --accent-gradient: linear-gradient(90deg, var(--accent-secondary), var(--accent-primary));
  --accent-button: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));

  /* === STATUS COLORS === */
  --color-success: #00c853;       /* Completed steps, success states */
  --color-error: #ff5252;         /* Error messages */
  --color-warning: #ffd740;       /* Warnings */
  --color-info: #448aff;          /* Info messages */

  /* === BORDERS === */
  --border-default: #333333;      /* Card borders, input borders */
  --border-active: #7b68ee;       /* Active/focused element borders */
  --border-success: #00c853;      /* Completed step borders */
  --border-subtle: #222222;       /* Output area borders */

  /* === SHADOWS === */
  --shadow-card: none;            /* Card shadow (neobrutalism = none, glass = blur) */
  --shadow-button: none;          /* Button shadow */
  --shadow-hover: 0 4px 20px rgba(123, 104, 238, 0.15);  /* Hover state */

  /* === SPACING === */
  --radius-sm: 8px;               /* Input fields, small elements */
  --radius-md: 12px;              /* Cards, steps */
  --radius-lg: 16px;              /* Large containers */
  --radius-full: 9999px;          /* Circles (step numbers) */
  --padding-card: 24px;           /* Card internal padding */
  --padding-page: 32px;           /* Page-level padding */
  --gap-steps: 24px;              /* Space between chain steps */

  /* === TYPOGRAPHY === */
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  --font-size-xs: 12px;           /* Tiny labels */
  --font-size-sm: 13px;           /* Helper text, secondary info */
  --font-size-base: 14px;         /* Body text, inputs */
  --font-size-lg: 18px;           /* Step names */
  --font-size-xl: 24px;           /* Page title */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* === ANIMATION === */
  --transition-fast: 0.2s ease;   /* Hover states, opacity changes */
  --transition-medium: 0.3s ease; /* Border color changes, transforms */

  /* === STEP NUMBER BADGE === */
  --badge-size: 32px;
  --badge-bg: var(--accent-primary);
  --badge-bg-complete: var(--color-success);
  --badge-text: white;
  --badge-font-size: 14px;

  /* === PROMPT EDITOR (Edit Mode) === */
  --editor-bg: #1a0a2e;
  --editor-border: rgba(123, 104, 238, 0.27);
  --editor-text: #c4b5fd;
}
```

### Component-Level Styles

These map directly to HTML elements in the dashboard:

```css
/* === HEADER BAR === */
.header {
  background: var(--bg-header);
  padding: 24px var(--padding-page);
  border-bottom: 1px solid var(--border-default);
}
.header h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* === CHAIN STEP CARD === */
.chain-step {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--padding-card);
  margin-bottom: var(--gap-steps);
  box-shadow: var(--shadow-card);
  transition: border-color var(--transition-medium);
}
.chain-step.active {
  border-color: var(--border-active);
}
.chain-step.complete {
  border-color: var(--border-success);
}

/* === INPUT FIELDS === */
.input-group input,
.input-group textarea,
.input-group select {
  background: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: var(--font-size-base);
}
.input-group input:focus,
.input-group textarea:focus {
  border-color: var(--border-active);
  outline: none;
  box-shadow: 0 0 0 3px rgba(123, 104, 238, 0.1);
}

/* === BUTTONS === */
.run-btn {
  background: var(--accent-button);
  border: none;
  color: white;
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  box-shadow: var(--shadow-button);
  transition: opacity var(--transition-fast);
}
.run-btn:hover {
  opacity: 0.9;
  box-shadow: var(--shadow-hover);
}

/* === OUTPUT AREA === */
.output-area {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 16px;
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--text-code);
}
.output-area.has-content {
  color: var(--text-code-active);
}

/* === STEP CONNECTOR ARROW === */
.connector {
  color: var(--border-default);
  font-size: 24px;
  text-align: center;
  padding: 8px 0;
}

/* === STEP NUMBER BADGE === */
.step-number {
  width: var(--badge-size);
  height: var(--badge-size);
  background: var(--badge-bg);
  border-radius: var(--radius-full);
  color: var(--badge-text);
  font-weight: var(--font-weight-bold);
  font-size: var(--badge-font-size);
  display: flex;
  align-items: center;
  justify-content: center;
}
.step-number.complete {
  background: var(--badge-bg-complete);
}
```

---

## STYLE SET INTEGRATION: How to Theme It

### Step 1: User Screenshots a Website/App They Like

They feed the screenshot into your Style Set tool.

### Step 2: Style Set Analyzes and Outputs a Theme

Your Style Set tool already extracts:
- Color palette (primary, secondary, accent, backgrounds)
- Typography (font families, sizes, weights)
- Border radius patterns (sharp, rounded, pill)
- Shadow style (none, subtle, heavy, glass)
- Overall vibe (morphism type: neo, glass, flat, etc.)

### Step 3: Map Style Set Output → Dashboard Variables

Here's the mapping your Style Set tool needs to produce:

```
STYLE SET OUTPUT          →  DASHBOARD VARIABLE
─────────────────────────────────────────────────
Background (darkest)      →  --bg-primary
Background (card/surface) →  --bg-secondary
Background (recessed)     →  --bg-tertiary
Background (input)        →  --bg-input
Header style              →  --bg-header

Text (primary)            →  --text-primary
Text (secondary)          →  --text-secondary
Text (muted)              →  --text-muted

Brand color 1             →  --accent-primary
Brand color 2             →  --accent-secondary

Success green             →  --color-success
Error red                 →  --color-error

Border color              →  --border-default
Border (active)           →  --border-active (usually = accent-primary)

Border radius             →  --radius-sm, --radius-md, --radius-lg
Shadow style              →  --shadow-card, --shadow-button, --shadow-hover

Font (body)               →  --font-body
Font (code/mono)          →  --font-mono
Font sizes                →  --font-size-xs through --font-size-xl
```

### Step 4: Generate the CSS Override Block

The output is a single `:root` block that overrides the defaults:

```css
/* Theme: "Stripe Dashboard" — generated by Style Set */
:root {
  --bg-primary: #f6f9fc;
  --bg-secondary: #ffffff;
  --bg-tertiary: #f0f3f7;
  --bg-input: #ffffff;
  --bg-header: linear-gradient(135deg, #635bff 0%, #0a2540 100%);

  --text-primary: #0a2540;
  --text-secondary: #425466;
  --text-muted: #8898aa;

  --accent-primary: #635bff;
  --accent-secondary: #00d4aa;
  --accent-gradient: linear-gradient(90deg, #635bff, #00d4aa);
  --accent-button: linear-gradient(135deg, #635bff, #7a73ff);

  --color-success: #00d4aa;
  --color-error: #ff5567;

  --border-default: #e3e8ee;
  --border-active: #635bff;
  --border-success: #00d4aa;
  --border-subtle: #eef1f6;

  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-button: 0 2px 4px rgba(99, 91, 255, 0.2);
  --shadow-hover: 0 8px 24px rgba(99, 91, 255, 0.15);

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;

  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

### Step 5: User Pastes the Theme Block

Two options for how the user applies the theme:

**Option A (Simple):** Paste the `:root` block into a "Theme" cell in the Google Sheet config tab. The Apps Script reads it and injects it into the HTML. One cell = one theme.

**Option B (Advanced):** Theme selector dropdown in the dashboard itself. Multiple themes stored in a "Themes" tab. Pick from dropdown → CSS variables swap instantly.

---

## MORPHISM STYLES MAPPING

Your Style Set has multiple morphism types. Here's how each maps to the dashboard:

### Flat / Minimal
```css
:root {
  --shadow-card: none;
  --shadow-button: none;
  --border-default: #e0e0e0;
  --radius-sm: 4px;
  --radius-md: 6px;
}
```

### Neobrutalism
```css
:root {
  --shadow-card: 4px 4px 0px #000000;
  --shadow-button: 3px 3px 0px #000000;
  --border-default: 2px solid #000000;
  --radius-sm: 0px;
  --radius-md: 0px;
}
```

### Glassmorphism
```css
:root {
  --bg-secondary: rgba(255, 255, 255, 0.05);
  --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.12);
  --border-default: 1px solid rgba(255, 255, 255, 0.1);
  /* Add to .chain-step: */
  /* backdrop-filter: blur(12px); */
}
```

### Neumorphism
```css
:root {
  --bg-primary: #e0e5ec;
  --bg-secondary: #e0e5ec;
  --shadow-card: 8px 8px 16px #a3b1c6, -8px -8px 16px #ffffff;
  --border-default: none;
  --radius-md: 16px;
}
```

### Claymorphism
```css
:root {
  --shadow-card: 0 4px 0 rgba(0,0,0,0.15), inset 0 -3px 0 rgba(0,0,0,0.08);
  --border-default: none;
  --radius-md: 24px;
  --radius-sm: 16px;
}
```

---

## WEBSITE BUILDER FORMAT MAPPINGS

The same theme variables can output to different website builder formats:

### For the Apps Script Web App (native)
Output: CSS custom properties as shown above

### For WordPress
Output: `style.css` theme file + `theme.json` (block theme)

```json
{
  "version": 2,
  "settings": {
    "color": {
      "palette": [
        { "slug": "primary", "color": "#7b68ee", "name": "Primary" },
        { "slug": "secondary", "color": "#00d2ff", "name": "Secondary" },
        { "slug": "background", "color": "#0f0f0f", "name": "Background" },
        { "slug": "surface", "color": "#1a1a1a", "name": "Surface" },
        { "slug": "text", "color": "#e5e5e5", "name": "Text" }
      ]
    },
    "typography": {
      "fontFamilies": [
        { "fontFamily": "'Inter', sans-serif", "slug": "body", "name": "Body" },
        { "fontFamily": "'JetBrains Mono', monospace", "slug": "mono", "name": "Mono" }
      ]
    },
    "spacing": {
      "units": ["px", "rem"]
    }
  },
  "styles": {
    "color": {
      "background": "#0f0f0f",
      "text": "#e5e5e5"
    },
    "typography": {
      "fontFamily": "'Inter', sans-serif"
    },
    "elements": {
      "button": {
        "color": { "background": "#7b68ee", "text": "#ffffff" },
        "border": { "radius": "8px" }
      },
      "link": {
        "color": { "text": "#7b68ee" }
      }
    }
  }
}
```

### For Astro
Output: Tailwind config + CSS variables file

```javascript
// tailwind.config.mjs (Astro uses this)
export default {
  theme: {
    extend: {
      colors: {
        primary: '#7b68ee',
        secondary: '#00d2ff',
        bg: { DEFAULT: '#0f0f0f', card: '#1a1a1a', input: '#0f0f0f' },
        surface: '#1a1a1a',
        success: '#00c853',
        error: '#ff5252',
      },
      fontFamily: {
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm: '8px', md: '12px', lg: '16px',
      },
    },
  },
};
```

```css
/* src/styles/theme.css (Astro global styles) */
:root {
  /* Same CSS custom properties as the dashboard */
  --bg-primary: #0f0f0f;
  --accent-primary: #7b68ee;
  /* ... all variables ... */
}
```

### For Shadcn/UI (React apps)
Output: CSS variables matching shadcn's convention

```css
/* globals.css */
:root {
  --background: 0 0% 6%;           /* #0f0f0f */
  --foreground: 0 0% 90%;          /* #e5e5e5 */
  --card: 0 0% 10%;                /* #1a1a1a */
  --card-foreground: 0 0% 90%;
  --primary: 249 83% 67%;          /* #7b68ee */
  --primary-foreground: 0 0% 100%;
  --secondary: 189 100% 50%;       /* #00d2ff */
  --muted: 0 0% 53%;               /* #888888 */
  --accent: 249 83% 67%;
  --destructive: 0 84% 66%;        /* #ff5252 */
  --border: 0 0% 20%;              /* #333333 */
  --input: 0 0% 20%;
  --ring: 249 83% 67%;
  --radius: 0.75rem;
}
```

---

## SINGLE PIPELINE: Screenshot → Theme → Any Format

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────────┐
│  Screenshot  │ ──→ │  Style Set    │ ──→ │  Theme Variables     │
│  of any app  │     │  Tool         │     │  (universal format)  │
│  or website  │     │  (your app)   │     │                      │
└──────────────┘     └───────────────┘     └──────────┬───────────┘
                                                       │
                              ┌─────────────────────────┼────────────────────────┐
                              │                         │                        │
                              ▼                         ▼                        ▼
                    ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
                    │  CSS :root   │          │  WordPress   │         │  Astro /     │
                    │  (Web App /  │          │  theme.json  │         │  Tailwind    │
                    │   Dashboard) │          │  + style.css │         │  config      │
                    └──────────────┘          └──────────────┘         └──────────────┘
                              │                         │                        │
                              ▼                         ▼                        ▼
                    ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
                    │  Prompt      │          │  WordPress   │         │  Astro       │
                    │  Chain       │          │  Theme       │         │  Website     │
                    │  Dashboard   │          │              │         │              │
                    └──────────────┘          └──────────────┘         └──────────────┘
```

One screenshot → one Style Set analysis → output to ANY format.

The dashboard, a WordPress theme, an Astro site, a React app with shadcn —
they ALL get themed from the same source image.

---

## WHAT YOUR STYLE SET TOOL NEEDS TO OUTPUT

For the prompt chain dashboard specifically, the Style Set tool needs to produce
a JSON object with these exact keys:

```json
{
  "theme_name": "Stripe Dashboard",
  "morphism": "flat",
  "colors": {
    "bg_primary": "#f6f9fc",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#f0f3f7",
    "bg_input": "#ffffff",
    "bg_header_start": "#635bff",
    "bg_header_end": "#0a2540",
    "text_primary": "#0a2540",
    "text_secondary": "#425466",
    "text_muted": "#8898aa",
    "accent_primary": "#635bff",
    "accent_secondary": "#00d4aa",
    "success": "#00d4aa",
    "error": "#ff5567",
    "border": "#e3e8ee",
    "border_active": "#635bff"
  },
  "typography": {
    "font_body": "'Inter', -apple-system, sans-serif",
    "font_mono": "'JetBrains Mono', monospace",
    "font_size_base": "14px",
    "font_size_lg": "18px",
    "font_size_xl": "24px"
  },
  "shape": {
    "radius_sm": "6px",
    "radius_md": "10px",
    "radius_lg": "14px",
    "shadow_card": "0 2px 8px rgba(0, 0, 0, 0.08)",
    "shadow_button": "0 2px 4px rgba(99, 91, 255, 0.2)",
    "shadow_hover": "0 8px 24px rgba(99, 91, 255, 0.15)"
  }
}
```

A simple function converts this JSON → CSS `:root` block → injected into the dashboard.

The same JSON can be converted to WordPress `theme.json`, Astro Tailwind config,
shadcn CSS variables, or any other format.

**One JSON. Every platform.**
