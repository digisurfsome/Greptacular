# Task: Add Color Customization to Style Preview Renderer

## What Exists Now

The style preview renderer is in the AutoForge UI project creation flow (Step 4: Design). It shows 4 preview pages (Landing, Dashboard, Settings, Feed) in a quad-view layout. Users can:
- Pick a base style from 12 options (left sidebar)
- Pick an accent style to mix (left sidebar)
- Toggle modifiers (High Contrast Buttons, Large Touch Targets, High Contrast Text, Larger Type Scale)
- Switch between Quad and Single view

The styles are defined in `server/services/style_manager.py` with full color tokens, typography, and component patterns. The preview renderer applies these tokens as CSS variables to render the 4 pages live.

## What To Add

Add a **Color Customization Panel** to the preview sidebar (below the existing MODIFIERS section) that lets users override individual color tokens for the selected style.

### UI Design

Add a new collapsible section in the sidebar:

```
COLORS (Optional)
  Primary:    [■ swatch] #3B82F6  [picker]
  Background: [■ swatch] #FFFFFF  [picker]
  Surface:    [■ swatch] #F8FAFC  [picker]
  Text:       [■ swatch] #1E293B  [picker]
  Accent:     [■ swatch] #F59E0B  [picker]
  Muted:      [■ swatch] #94A3B8  [picker]
  [Reset to Style Defaults]
```

Each row shows:
- A small color swatch (16x16px square with rounded corners)
- The hex value (editable text input, 7 chars wide)
- A native HTML color picker input (`<input type="color">`)

When any color changes, the preview updates LIVE (instant, no save needed).

### Implementation Details

1. **Color state**: Add a `colorOverrides` state object to the preview component. Shape: `{ primary?: string, background?: string, surface?: string, text?: string, accent?: string, muted?: string }`. When empty/undefined, the style's default colors are used.

2. **Applying overrides**: When rendering the preview, merge `colorOverrides` on top of the selected style's `color_tokens`. The override values should be applied as CSS custom properties on the preview container, overriding the style's defaults.

3. **The color tokens to expose** (from `style_manager.py` each style has these in `color_tokens`):
   - `primary` - Main brand/interaction color
   - `background` - Page background
   - `surface` - Card/container background
   - `text` - Primary text color
   - `accent` - Secondary interaction color
   - `muted` - Muted/disabled text, borders

4. **Reset button**: Clears all overrides back to the selected style's defaults. Only show this button when at least one color has been overridden.

5. **Persistence**: Store `colorOverrides` in the same state that gets passed forward when the user clicks "Continue" to proceed to the next setup step. The overrides should be saved alongside the selected style in the project config.

6. **When style changes**: Reset all color overrides (the new style has different defaults). Show a brief toast/note: "Color customizations reset for new style."

7. **Visual feedback**: When a color is overridden (different from style default), show a small dot indicator or slightly different border on that color row so users know which colors they've customized.

### Technical Notes

- Use native `<input type="color">` for the picker -- it's cross-browser and requires zero dependencies
- The hex input should validate: must be 7 chars starting with `#`, only hex digits
- Preview update should be instant (just changing CSS variables on a container element)
- Keep the UI compact -- the sidebar is already dense with styles + modifiers
- The color section should be collapsed by default (expandable with a chevron)

### Files to Modify

Look at the existing preview renderer components in `ui/src/components/` -- find the component that renders the style preview sidebar (the one with the style list, accent list, and modifiers). Add the color customization section there.

Also check:
- `server/services/style_manager.py` - for the color_tokens structure
- `server/routers/projects.py` - for how style selection is saved to project config
- The existing modifier toggle implementation - follow the same pattern for color overrides

### What NOT To Do

- Don't add a full color wheel or HSL picker -- native `<input type="color">` is sufficient
- Don't add custom palette suggestions yet (that's a separate feature)
- Don't change how styles are stored in `style_manager.py`
- Don't modify the preview page templates themselves
- Keep it simple -- just the 6 color overrides with live preview
