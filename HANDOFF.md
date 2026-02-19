# Agent Handoff: Design Step - Column 2b ColorCustomizer Fix

## Branch
`claude/autoforge-ui-stage-four-TVNQN`

## Problem Summary
The **ColorCustomizer** component in **Column 2b** of the Design step (Step 4 of the new project wizard) is **not rendering at all** in the UI. The user can see the FONT section at the top of Column 2b, but the Custom Colors / ColorCustomizer section below it is invisible — it either isn't rendering or is failing silently.

## What the User Wants (Reference Layout)

The Design step has 4 columns:

| Column 1 | Column 2a (200px) | Column 2b (200px) | Column 3 | Column 4 |
|-----------|-------------------|-------------------|----------|----------|
| Style cards (scrollable grid) | 1. ACCENT STYLE | 1. FONT (grid-cols-3) | AI DESIGN GUIDE chat | Preview (quad/single) |
| | 2. MODIFIERS | 2. CUSTOM COLORS (ColorCustomizer) | | |
| | 3. COLOR PALETTE | *(scrollable, both sections)* | | |

**Column 2a** (ACCENT STYLE → MODIFIERS → COLOR PALETTE) — this is DONE and working correctly.

**Column 2b** — FONT (#1) is working. CUSTOM COLORS (#2, the ColorCustomizer) is NOT showing up.

## Root Cause (Most Likely)

In `NewProjectModal.tsx` at lines **1652-1665**, the ColorCustomizer is wrapped in a conditional:

```tsx
{(() => {
  const selected = styles?.find((s: StyleOption) => s.id === styleId)
  if (!selected?.style_guide) return null  // <-- THIS IS LIKELY THE PROBLEM
  return (
    <ColorCustomizer
      styleGuide={selected.style_guide}
      customColors={customColors}
      onChange={setCustomColors}
      selectedPaletteId={selectedPaletteId}
      onPaletteSelect={setSelectedPaletteId}
    />
  )
})()}
```

The `if (!selected?.style_guide) return null` guard means if:
- `styles` is undefined/empty, OR
- `styleId` doesn't match any style, OR
- The matched style doesn't have a `style_guide` property

...then the ENTIRE ColorCustomizer is hidden. The user's screenshots show style cards selected in Column 1, so the data should be there, but `style_guide` might not be populated on the style objects.

**Possible fixes:**
1. Debug why `style_guide` might be null/undefined on the selected style — check the `StyleOption` type definition and how styles are generated/fetched
2. Make the ColorCustomizer render regardless (perhaps with fallback default colors), rather than hiding completely when `style_guide` is missing
3. Add a visible fallback message like "Select a style to customize colors" instead of returning null

## Files You Need to Work With

### Primary Files
- **`ui/src/components/NewProjectModal.tsx`** (~1900 lines) — The main modal. Column 2b is at lines 1604-1666. The conditional ColorCustomizer rendering is at lines 1652-1665.
- **`ui/src/components/ColorCustomizer.tsx`** (161 lines) — The component itself. Recently compacted to fit in 200px column. Takes `styleGuide`, `customColors`, `onChange`, `selectedPaletteId`, `onPaletteSelect` props.
- **`ui/src/components/PaletteStrip.tsx`** (142 lines) — Horizontal scrollable palette presets inside ColorCustomizer.

### Supporting Files (for understanding data flow)
- **`ui/src/lib/types.ts`** — TypeScript types. Check `StyleOption` and `StyleGuide` types to understand what `style_guide` looks like.
- **`ui/src/data/palettes.ts`** — Palette data (`PALETTES`, `PALETTE_CATEGORIES`)
- **`ui/src/data/fonts.ts`** — Font data (`FONT_OPTIONS`)

## What Was Already Done (Previous Agent Work)

### Commit `48c4e0e` - Reordered Column 2a
- Moved sections in Column 2a to: ACCENT STYLE → MODIFIERS → COLOR PALETTE
- Moved COLOR PALETTE from Column 2b into Column 2a
- Widened Column 2a from 180px to 200px

### Commit `478690e` - Compacted ColorCustomizer
- Shrunk color pickers from `w-8 h-8` → `w-5 h-5`
- Changed grid from `grid-cols-2 lg:grid-cols-3 gap-3` → `grid-cols-2 gap-1.5`
- Reduced all text sizes (header `text-[10px]`, labels `text-[9px]`, hex `text-[8px]`)
- Removed `pl-5` padding, `Badge` import, border-top wrapper
- Changed header from "Customize Colors" to "Custom Colors"
- Shrunk PaletteStrip dots, names, padding

## What the User's Reference Image Shows for Custom Colors

The reference image (from a previous working version) shows the Custom Colors section expanded with:
- **"Customize Colors"** header with a chevron toggle, an **"Optional"** badge, and a **"Modified"** indicator
- Description text: *"Pick a palette preset or tweak individual colors."*
- **"QUICK PALETTE PRESETS"** label above a horizontal scrollable strip of palette thumbnails
- **2-column grid** of color pickers: Primary, Secondary, Accent, Background, Surface, Text — each with a color swatch input and hex value
- **"Reset to Default"** button at the bottom

Note: The previous agent removed the "Optional" badge and description text during compacting. The user's reference image still shows them. You may want to restore those elements, but the **primary issue** is that the component isn't rendering at all.

## Steps to Fix

1. **Investigate why ColorCustomizer doesn't render** — Add a `console.log` or temporary visible debug text before the `if (!selected?.style_guide) return null` guard to verify the condition. Check what `styles`, `styleId`, and `selected?.style_guide` are at runtime.

2. **Fix the conditional** — Either:
   - Make ColorCustomizer always render with a sensible fallback
   - Fix the data flow so `style_guide` is populated when a style is selected
   - Show a message like "Select a style to customize colors" instead of returning null

3. **Verify it renders properly** — Once visible, make sure the 200px column doesn't cause overlap. The compacting edits should handle this, but verify.

4. **Build and test** — Run `cd ui && npm run build` to verify no TypeScript errors.

5. **Commit and push** to branch `claude/autoforge-ui-stage-four-TVNQN`

## Build & Test Commands

```bash
cd ui
npm run build    # TypeScript check + production build
npm run lint     # ESLint
```

## Current Git State

```
478690e Compact ColorCustomizer and PaletteStrip to fit 200px Column 2b
48c4e0e Fix design step section order to match reference: Accent Style → Modifiers → Color Palette
4a23ce3 Redesign Stage 4 Design page layout: split controls into two columns
```

Branch is up to date with remote `origin/claude/autoforge-ui-stage-four-TVNQN`.
