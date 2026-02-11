# Style Preview Grid - Handoff Document

## Overview

Redesign the "Choose a Design Style" modal to use a full-screen grid layout where each style card shows **both** the style metadata AND a visual preview of actual UI components rendered in that style. Users should be able to evaluate styles at a glance without hovering. Hover provides a full-screen detailed preview.

## Current State

- Style picker at `ui/src/components/NewProjectModal.tsx` (the `step === 'style'` section)
- 12 styles defined in `server/services/style_manager.py` with full color tokens, typography, components, spacing, and Tailwind config
- Each style card currently shows: 4 color swatches + name + description + audience tags
- The modal is `sm:max-w-2xl` - does NOT use the full screen
- Swatches are just colored rectangles - no actual UI component previews

## Desired Design

### Grid Layout (Default View)

The style picker should use the **full available screen space** (not a cramped modal). Options:
- Make the dialog `sm:max-w-7xl` or near full-width
- Or replace the dialog with a full-page overlay for this step

Each style card in the grid should show **two sections side by side**:

```
┌─────────────────────────────────────────────────┐
│  [LEFT: Style Info]     │  [RIGHT: UI Preview]  │
│                         │                       │
│  Style Name             │  ┌─ Sample Card ────┐ │
│  Description            │  │ Heading Text      │ │
│  ● ● ● ● (colors)      │  │ Body text here    │ │
│                         │  │ [Button] [Button] │ │
│  Audience: ...          │  │ [Input field    ]  │ │
│  Vibe: ...              │  └──────────────────┘ │
│                         │                       │
│  Do's: ✓ ✓ ✓            │  Toggle  ○──●         │
│  Don'ts: ✗ ✗ ✗          │  Radio   ◉ ○ ○       │
│                         │                       │
└─────────────────────────────────────────────────┘
```

The RIGHT side should render actual UI elements styled with that design system:
- A heading (H1/H2) in the style's typography
- Body text paragraph
- Primary button + secondary/outline button
- A text input field
- A card/container with shadow/border per the style
- A toggle switch or radio buttons
- Background color of the preview area should match the style's bg color

### Card Sizing

Cards should be large enough to clearly see the style differences at a glance. Think ~400-500px wide per card minimum. A 2-column grid for 12 styles = 6 rows, scrollable. On very wide screens, 3 columns.

### Hover/Click → Full-Screen Preview

When user hovers (or clicks) a style card, show a **full-screen overlay** that fills the viewport (top to bottom, edge to edge) showing:
- A full mock landing page or app screen rendered in that style
- Multiple component types: navbar, hero section, feature cards, form, footer
- Large enough to really evaluate the design system
- Close button or click-outside to dismiss
- "Select This Style" button in the preview

### Preview Rendering Approach

The previews should be **pure CSS/inline styles** derived from each style's tokens in `style_manager.py`. Each style has:
- `color_tokens`: primary, secondary, accent, background, surface, text, muted, border, success, warning, error
- `typography`: font_family, headings (font, weight, tracking), body (font, size, line_height)
- `components`: border_radius, border_width, shadow, button (padding, font_weight, text_transform, hover_effect), card (padding, shadow, border), input (border_width, padding, focus_ring)
- `spacing`: base_unit, section_padding, element_gap

**Option A (Recommended)**: Create a `StylePreview` React component that takes a style's tokens and renders inline-styled elements. No Tailwind needed for the preview - use CSS variables or direct style objects.

**Option B**: Generate static preview images server-side. More complex, less interactive.

### Data Source

All style data is already available via:
- `GET /api/styles` → returns all 12 styles with full `css_preview` data
- `server/services/style_manager.py` → `STYLE_REGISTRY` has all tokens
- The API already returns color tokens, typography, components, spacing for each style

You may need to add a new API field or endpoint that returns the full token set needed for rendering previews. Currently `css_preview` only has a subset.

## Implementation Plan

### Step 1: Create StylePreview Component
- `ui/src/components/StylePreview.tsx`
- Props: style tokens (colors, typography, components, spacing)
- Renders: heading, paragraph, buttons, input, card, toggle - all styled via inline CSS from tokens
- Two sizes: `compact` (for grid card) and `full` (for hover overlay)

### Step 2: Create FullScreenPreview Component
- `ui/src/components/StyleFullPreview.tsx`
- Triggered on hover/click from grid
- Renders a mock app layout: navbar + hero + feature cards + form + footer
- All styled with the selected style's tokens
- Overlay with backdrop blur, close button, "Select This Style" button

### Step 3: Update Style Picker Grid
- Widen the dialog to `sm:max-w-7xl` or use full-screen overlay for style step
- Replace current card layout with the two-column info+preview cards
- Each card: left side = current metadata, right side = `<StylePreview size="compact" />`

### Step 4: Ensure Full Token Data Available
- Check if `GET /api/styles` returns enough data for rendering
- If not, add a `tokens` field to the style API response from `style_manager.py`
- All 12 styles already have complete token definitions in `STYLE_REGISTRY`

### Step 5: Wire Up Hover/Click
- Hover on card → show `<StyleFullPreview />` overlay after ~300ms delay
- Click → also opens full preview
- "Select This Style" in preview → calls `handleStyleSelect(id)`

## Files to Modify

- `ui/src/components/NewProjectModal.tsx` - Widen style step, use new grid layout
- `ui/src/components/StylePreview.tsx` - NEW: compact preview component
- `ui/src/components/StyleFullPreview.tsx` - NEW: full-screen preview component
- `server/services/style_manager.py` - May need to expose more tokens via API
- `server/routers/projects.py` - May need to return full tokens in style endpoint
- `ui/src/lib/types.ts` - May need to extend StyleOption type with full tokens

## Style Token Reference

Each style in `STYLE_REGISTRY` has this structure:
```python
{
    "color_tokens": {
        "primary": "#...",
        "secondary": "#...",
        "accent": "#...",
        "background": "#...",
        "surface": "#...",
        "text": "#...",
        "muted": "#...",
        "border": "#...",
    },
    "typography": {
        "font_family": "...",
        "headings": {"font": "...", "weight": "...", "tracking": "..."},
        "body": {"font": "...", "size": "...", "line_height": "..."},
    },
    "components": {
        "border_radius": "...",
        "border_width": "...",
        "shadow": "...",
        "button": {"padding": "...", "font_weight": "...", "text_transform": "...", "hover_effect": "..."},
        "card": {"padding": "...", "shadow": "...", "border": "..."},
        "input": {"border_width": "...", "padding": "...", "focus_ring": "..."},
    },
    "spacing": {
        "base_unit": "...",
        "section_padding": "...",
        "element_gap": "...",
    },
}
```

## CRITICAL: Modifier & Style Mixing Previews

The preview engine is NOT just for the 12 base styles. It must also show live previews for:

### Modifier Previews (Contrasting Buttons, etc.)

When a user selects a style and then toggles a modifier (e.g., "High-Contrast Buttons"), the preview must **update in real-time** to show the effect.

Current modifiers (defined in `server/services/style_modifiers.py`):
- `high-contrast-buttons` - Bolder colors, thicker borders on buttons
- `large-touch-targets` - Bigger click areas, more padding on interactive elements
- `high-contrast-text` - Darker text, better readability
- `larger-type` - Bumped up font sizes across the board

Each modifier has `token_overrides` that describe what CSS properties change. The preview component should accept modifiers as a prop and merge their overrides into the base style tokens before rendering.

**Flow:**
1. User sees 12 style cards with previews → picks Minimalism
2. Modifier toggles appear below with their own mini preview strip
3. Each modifier toggle shows a **before/after** or the preview updates live as toggles are flipped
4. User can SEE that "high-contrast buttons" makes the buttons pop before committing

### Style Mixing Previews (Base + Accent)

When style mixing is built (see `style-mixing-handoff.md`), the preview engine must support showing a **base style + accent style** combination.

- Base style controls: background, text, typography, layout, spacing
- Accent style controls: buttons, cards, interactive elements only
- The preview shows the base style's page layout but with accent-styled buttons and cards

**Flow:**
1. User picks a base style (e.g., Minimalism)
2. Optional: picks an accent style (e.g., Cyberpunk)
3. The full-screen preview renders Minimalism layout with Cyberpunk-styled buttons/cards
4. User can SEE the exact combination before committing

### Preview Component Architecture

The `StylePreview` component should accept:
```tsx
interface StylePreviewProps {
  baseTokens: StyleTokens          // The base style's full token set
  accentTokens?: StyleTokens       // Optional accent style (for mixing)
  modifierOverrides?: TokenOverrides[] // Active modifier overrides
  size: 'compact' | 'full'         // Grid card vs full-screen
}
```

The rendering logic:
1. Start with `baseTokens`
2. If `accentTokens` provided, override button/card/interactive tokens only
3. If `modifierOverrides` provided, apply those on top
4. Render the sample page using the final merged tokens

This way ONE component handles all combinations:
- Bauhaus alone → `baseTokens=bauhaus`
- Bauhaus + high-contrast buttons → `baseTokens=bauhaus, modifierOverrides=[highContrast]`
- Bauhaus base + Cyberpunk accent → `baseTokens=bauhaus, accentTokens=cyberpunk`
- Bauhaus + Cyberpunk accent + large touch targets → all three props

### Sample Page Layout (Same For All Previews)

The full-screen preview renders this **identical layout** for every style/combination so differences are immediately obvious:

```
┌──────────────────────────────────────────────────┐
│  NAVBAR: Logo  |  Home  |  Features  |  [CTA]   │
├──────────────────────────────────────────────────┤
│                                                  │
│           ★ Hero Heading Text ★                  │
│     A subtitle paragraph explaining the app      │
│     [Primary Button]   [Outline Button]          │
│                                                  │
├──────────────────────────────────────────────────┤
│  ┌─ Card 1 ─┐  ┌─ Card 2 ─┐  ┌─ Card 3 ─┐     │
│  │ Icon      │  │ Icon      │  │ Icon      │     │
│  │ Title     │  │ Title     │  │ Title     │     │
│  │ Body text │  │ Body text │  │ Body text │     │
│  │ [Button]  │  │ [Button]  │  │ [Button]  │     │
│  └───────────┘  └───────────┘  └───────────┘     │
├──────────────────────────────────────────────────┤
│  Form Section                                    │
│  [Name input     ]  [Email input     ]           │
│  [Message textarea                   ]           │
│  [Submit Button]                                 │
│                                                  │
│  ○ Option A   ○ Option B   ● Option C            │
│  ☐ Checkbox 1  ☑ Checkbox 2                      │
│  Toggle: ○──●                                    │
├──────────────────────────────────────────────────┤
│  FOOTER: Links  |  Links  |  Links  |  © 2026   │
└──────────────────────────────────────────────────┘
```

### Multiple Preview Pages (Like Dribbble Showcases)

The full-screen preview should NOT be just one page. Show **3-4 pages** that users can swipe/tab through, like Dribbble mockup showcases:

**Page 1: Landing/Home Page** (the layout above)
- Navbar, hero, feature cards, form, footer

**Page 2: Dashboard/App Interior**
- Sidebar navigation
- Data cards/stats (numbers, progress bars)
- A data table with rows
- Action buttons (edit, delete, add)

**Page 3: Settings/Form Page**
- Profile form with multiple input types
- Toggle switches, radio groups, checkboxes
- Dropdown select
- File upload area
- Save/Cancel buttons

**Page 4: Card/Content Feed**
- Grid of content cards (like a blog or product catalog)
- Each card: image placeholder, title, description, tags, button
- Pagination or load-more button
- Search bar + filter chips

Navigation between pages: tab bar at the top of the preview ("Home | Dashboard | Settings | Feed") or left/right arrows to swipe through.

This gives users a COMPLETE picture of what their app will feel like - not just the front door, but the rooms inside.

This layout has EVERY common UI element:
- Buttons (primary, outline, in cards, submit)
- Cards with shadows/borders
- Input fields, textarea
- Radio buttons, checkboxes, toggles
- Navbar, footer
- Typography (H1, H2, body, small text)
- Background colors, surface colors

When comparing Bauhaus vs Cyberpunk vs Minimalism, users see the EXACT same layout with completely different visual treatment. The differences jump out immediately.

## Combination Count (Not Pre-Made - Live Rendered)

Do NOT pre-generate images for every combination. The math is impossible:
- 12 base styles = 12
- 12 × 4 modifiers = 48
- 12 × 11 mixing combos = 132
- 12 × 4 × 11 = 528 total combos

Instead, the preview component renders LIVE based on current selections. One component, dynamic inputs, instant preview. Like a car configurator - not a photo gallery.

## UX Notes

- The "Help Me Choose" recommender panel and modifier toggles should still work
- After selecting a style from the grid or full preview, modifiers appear below
- Keep the filter tabs (All, Core, Vibe) working
- The grid should feel like browsing a design gallery, not picking from a dropdown
- Transitions should be smooth - no jarring popups
- The preview is the SELLING POINT of this feature - it must look polished and real, not like a wireframe
- Every preview must use the exact same page layout so differences between styles are immediately clear
- Modifier and mixing previews update LIVE as the user toggles options - no page reload, no delay

## Step 6: Automated Screenshot Generation

After the live preview engine is built and working, use Playwright to automatically screenshot all 12 base styles across all 4 preview pages. This produces 48 polished images that can be used as static thumbnails in the grid cards for fast loading.

### Script: `scripts/generate-style-screenshots.ts`

Create a Playwright script that:
1. Starts the dev server (or uses a running instance)
2. Navigates to a dedicated preview route (e.g., `/#/style-preview/:styleId/:page`)
3. Loops through all 12 styles × 4 pages
4. Sets viewport to a consistent size (e.g., 1280×800)
5. Screenshots each rendered page
6. Saves to `ui/public/style-previews/{style-id}-{page}.png`

```
ui/public/style-previews/
├── bauhaus-landing.png
├── bauhaus-dashboard.png
├── bauhaus-settings.png
├── bauhaus-feed.png
├── claymorphism-landing.png
├── claymorphism-dashboard.png
├── ... (48 total)
```

### Dedicated Preview Route

Add a clean route at `/#/style-preview/:styleId/:page` that renders ONLY the preview component (no modal chrome, no header, no overlay). This makes it easy for Playwright to screenshot just the preview content. It also serves as a standalone preview URL that can be shared.

### Usage in Grid Cards

The grid cards can use these static images as thumbnails for fast initial load:
- Show the static `.png` in the grid card (instant, no rendering delay)
- On hover/click, switch to the live HTML renderer for the full interactive experience
- Best of both worlds: fast grid browsing + interactive deep dive

### npm Script

Add to `ui/package.json`:
```json
{
  "scripts": {
    "generate:previews": "playwright test scripts/generate-style-screenshots.ts"
  }
}
```

This can be re-run anytime styles are updated to regenerate all 48 images automatically.
