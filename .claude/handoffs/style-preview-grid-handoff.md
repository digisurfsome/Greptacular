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

## UX Notes

- The "Help Me Choose" recommender panel and modifier toggles should still work
- After selecting a style from the grid or full preview, modifiers appear below
- Keep the filter tabs (All, Core, Vibe) working
- The grid should feel like browsing a design gallery, not picking from a dropdown
- Transitions should be smooth - no jarring popups
