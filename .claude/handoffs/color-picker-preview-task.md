# Task: Add Color Customization to Style Picker

## What Exists Now

The style picker is in **`ui/src/components/NewProjectModal.tsx`** — specifically the `step === 'style'` section (around line 546). It's Step 4 of the new project creation flow.

**Current UI (in order top to bottom):**
1. "Help Me Choose" AI recommender toggle + category filter tabs (Core/Vibe)
2. Style cards grid (`grid grid-cols-2`) — each card shows 4 color swatches, name, description, audience
3. Accessibility Modifiers section (shown after a style is selected, ~line 751) — toggle buttons for High Contrast Buttons, Large Touch Targets, etc.
4. Continue/Skip footer buttons

**Key state variables** (around line 99):
- `styleId` — selected style ID string
- `selectedModifiers` — array of modifier ID strings
- Styles data comes from `useStyles()` hook → `GET /api/styles` → `server/services/style_manager.py:get_style_registry()`

**Color swatch data** is hardcoded in `STYLE_SWATCHES` (line 67) as a `Record<string, string[]>` — 4 hex colors per style (brand, surface, text, accent). These are used ONLY for the preview swatches on style cards, not for any live rendering.

**Important:** The API endpoint `GET /api/styles` does NOT return `color_tokens`. It only returns `id`, `name`, `category`, `description`, `best_for`, `philosophy`. The full `color_tokens` are in `STYLE_REGISTRY` in `style_manager.py` but stripped by `get_style_registry()` (line 1249). You'll need to either:
- Add a new endpoint like `GET /api/styles/{id}/colors` that returns color_tokens
- Or expand the list endpoint to include color_tokens (they're small)
- Or use the existing `STYLE_SWATCHES` constant and expand it to 6 colors

**How style is saved to project** (line 228-234):
```ts
await createProject.mutateAsync({
  name, path, specMethod,
  boilerplateId,
  styleId,
  modifierIds: selectedModifiers,
})
```
You'll need to add `colorOverrides` to this payload.

**Backend project creation** is in `server/routers/projects.py` — search for `create_project`. The style config gets written to the project's `.autoforge/` directory.

## What To Add

Add a **Color Customization Panel** below the existing Accessibility Modifiers section (~line 797 in NewProjectModal.tsx) that lets users tweak individual color tokens for the selected style.

### UI Design

Add a new collapsible section below the modifiers:

```
COLORS (Optional)                    [▼ chevron]
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

When any color changes, the style card swatches for the selected style should update to reflect the overrides (visual feedback).

### Implementation Details

1. **Color state**: Add a `colorOverrides` state object. Shape: `{ primary?: string, background?: string, surface?: string, text?: string, accent?: string, muted?: string }`. When empty/undefined, the style's default colors are used.

2. **Default colors per style**: Either fetch `color_tokens` from the server (add to API) or expand the `STYLE_SWATCHES` constant at line 67 to include all 6 named colors per style (mapped from `style_manager.py`'s `color_tokens`). The 6 tokens to expose:
   - `primary` → maps to `color_tokens.brand.DEFAULT`
   - `background` → maps to `color_tokens.surface.canvas`
   - `surface` → maps to `color_tokens.surface.base`
   - `text` → maps to `color_tokens.text.primary`
   - `accent` → maps to `color_tokens.status.info` or `brand.light` (pick whichever is more distinct)
   - `muted` → maps to `color_tokens.text.tertiary`

3. **Applying overrides visually**: Update the selected style card's swatch colors to reflect overrides. The card swatches currently use `STYLE_SWATCHES[style.id]` (line 698). When overrides exist, merge them on top.

4. **Reset button**: Clears all overrides back to the selected style's defaults. Only show this button when at least one color has been overridden.

5. **Persistence**: Add `colorOverrides` to the `createProject.mutateAsync()` payload (line 228). The overrides should be saved alongside `styleId` in the project config. Update:
   - `ui/src/lib/api.ts` — add `colorOverrides` to the create project request
   - `ui/src/lib/types.ts` — add `colorOverrides` to the project creation types
   - `server/routers/projects.py` — accept and store `color_overrides` in project config
   - `prompts.py` — inject color overrides into the style context when building prompts

6. **When style changes**: Reset all color overrides (the new style has different defaults). The `handleStyleSelect` function is at line 197. Add `setColorOverrides({})` there.

7. **Visual feedback**: When a color is overridden (different from style default), show a small dot indicator or slightly different border on that color row so users know which colors they've customized.

### Where to Insert the UI

In `NewProjectModal.tsx`, the modifier section ends at approximately line 797 (closing `</div>` of the modifier block). Insert the color customization section right after that, still inside the `{styleId && ...}` conditional. Follow the same pattern as the modifier section:
- Border-top separator
- Section header with "Optional" badge
- Description text
- Grid of controls
- Collapsed by default (use a `showColors` boolean state + chevron toggle)

### Technical Notes

- Use native `<input type="color">` — cross-browser, zero dependencies
- The hex input should validate: must be 7 chars starting with `#`, only hex digits
- Keep the UI compact — the modal is `sm:max-w-2xl`, the style step scrolls vertically
- The color section should be collapsed by default (expandable with a chevron)
- Follow the existing code patterns in the file (Radix UI components, Tailwind classes, lucide-react icons)
- Import `ChevronDown` from lucide-react for the collapse toggle

### Files to Modify

1. **`ui/src/components/NewProjectModal.tsx`** — Main file. Add state, UI section, wire up to create payload
2. **`ui/src/lib/api.ts`** — Add `colorOverrides` to create project API call
3. **`ui/src/lib/types.ts`** — Add `ColorOverrides` type
4. **`server/routers/projects.py`** — Accept `color_overrides` in create project endpoint, store in config
5. **`server/services/style_manager.py`** — Reference only (do NOT modify). Check `color_tokens` structure in `STYLE_REGISTRY` (first style starts at ~line 183)
6. **Optionally**: `server/services/style_manager.py:get_style_registry()` (line 1249) — add `color_tokens` to the response so the UI can show real defaults

### What NOT To Do

- Don't add a full color wheel or HSL picker — native `<input type="color">` is sufficient
- Don't add custom palette suggestions yet (that's a separate feature)
- Don't change how styles are stored in `style_manager.py`
- Don't add a live page preview renderer (that's a separate handoff: `style-preview-grid-handoff.md`)
- Keep it simple — just the 6 color overrides with visual feedback on the style card swatches
