# Color Customization - Handoff Document

## Overview

Add the ability to customize colors within a chosen design style. Users pick a base style (e.g., Minimalism) and then optionally tweak individual colors (primary, accent, background, etc.) while keeping the style's typography, spacing, and component patterns intact.

## Current State

- 12 styles in `server/services/style_manager.py` each have fixed `color_tokens`
- Colors: primary, secondary, accent, background, surface, text, muted, border, success, warning, error
- Style guide markdown is generated in `get_style_guide_markdown()` and saved to `.autoforge/style_guide.md`
- Prompt injection happens in `prompts.py` → `_get_style_context()`
- No UI for customizing colors - you pick a style and get its exact colors

## Desired Feature

### UI: Color Customization Panel

After selecting a style in the style picker, show an **optional** "Customize Colors" expandable section:

```
┌─ Customize Colors (Optional) ──────────────────┐
│                                                  │
│  Primary:    [████████] #3B82F6  [color picker]  │
│  Secondary:  [████████] #6366F1  [color picker]  │
│  Accent:     [████████] #F59E0B  [color picker]  │
│  Background: [████████] #FFFFFF  [color picker]  │
│  Surface:    [████████] #F8FAFC  [color picker]  │
│  Text:       [████████] #1E293B  [color picker]  │
│                                                  │
│  [Reset to Default]                              │
└──────────────────────────────────────────────────┘
```

- Each color shows a swatch + hex value + native color picker input
- Default values come from the selected style's `color_tokens`
- "Reset to Default" restores the style's original colors
- Only show the 6 main colors (primary, secondary, accent, background, surface, text). Don't overwhelm with all 11.

### Smart Presets (Stretch Goal)

Offer quick color presets for each style:
- "Original" (default)
- "Dark variant" (inverted bg/text)
- "High contrast" (more saturated primary/accent)
- "Muted" (desaturated, pastel version)

### Data Flow

1. User picks a style → color tokens loaded as defaults
2. User optionally tweaks colors → stored as `customColors` object
3. On project creation, `customColors` merged with style's base tokens
4. Style guide generation uses custom colors instead of defaults
5. Agent prompt includes the customized color values

### Storage

Add to `project_config.json` (saved by `boilerplate_manager.py`):
```json
{
  "style_id": "minimalism",
  "style_modifiers": ["high-contrast-buttons"],
  "custom_colors": {
    "primary": "#FF6B00",
    "accent": "#00D4FF"
  }
}
```

Only store colors that differ from the style's defaults. Empty object = no customization.

## Implementation Plan

### Backend

1. **`server/services/style_manager.py`**
   - Add `get_style_with_overrides(style_id, custom_colors)` function
   - Merges custom colors into style's `color_tokens` before generating style guide
   - Update `get_style_guide_markdown()` to accept optional color overrides

2. **`server/services/boilerplate_manager.py`**
   - Add `custom_colors` parameter to `save_project_config()`
   - Save to `project_config.json`

3. **`server/routers/projects.py`**
   - Accept `custom_colors` in `ProjectCreate` schema
   - Pass to `save_project_config()`

4. **`server/schemas.py`**
   - Add `custom_colors: dict[str, str] = Field(default_factory=dict)` to `ProjectCreate`

5. **`prompts.py`**
   - Update `_get_style_context()` to read `custom_colors` from config
   - Pass overrides to style guide generation

### Frontend

6. **`ui/src/components/ColorCustomizer.tsx`** (NEW)
   - Props: `styleId`, `colors` (defaults from style), `onChange`
   - Renders color picker grid with swatches + hex inputs
   - Uses native `<input type="color">` for picker
   - "Reset to Default" button

7. **`ui/src/components/NewProjectModal.tsx`**
   - Add `customColors` state
   - Show `<ColorCustomizer>` below modifiers when a style is selected
   - Pass `customColors` to `createProject`

8. **`ui/src/lib/api.ts`**
   - Update `createProject()` to accept and send `customColors`

9. **`ui/src/lib/types.ts`**
   - Update `StyleOption` type if needed

## Files to Modify

- `server/services/style_manager.py` - Add color override support
- `server/services/boilerplate_manager.py` - Save custom colors
- `server/routers/projects.py` - Accept custom colors
- `server/schemas.py` - Add custom_colors field
- `prompts.py` - Use custom colors in style context
- `ui/src/components/ColorCustomizer.tsx` - NEW component
- `ui/src/components/NewProjectModal.tsx` - Wire in ColorCustomizer
- `ui/src/lib/api.ts` - Pass custom colors
- `ui/src/lib/types.ts` - Type updates

## Notes

- Color customization is OPTIONAL - users can skip it entirely
- The style's typography, spacing, and component patterns are NOT customizable here (keep it simple)
- Validation: ensure hex color format, ensure sufficient contrast between text and background (warn if low contrast)
- The color customizer should appear collapsed by default with a "Customize Colors" toggle to expand it
