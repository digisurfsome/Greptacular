# Build Prompt: Style Preview Layout Redesign + Restore Full Accent Mixing

## What You Are Doing

Two things in one build:
1. **Restore the accent style selector** to show ALL 12 styles (currently only shows 3)
2. **Redesign the style preview page layout** to pack everything on one screen with zero wasted space

## Read These First

- `.claude/handoffs/style-mixing-handoff.md` — Full spec for the mixing feature
- `.claude/handoffs/style-preview-grid-handoff.md` — Preview engine spec (includes mixing preview section)
- `server/services/style_manager.py` — Current style registry (12 styles)
- `server/services/style_modifiers.py` — Working modifier system
- `ui/src/components/NewProjectModal.tsx` — Current style step (line ~547), modifiers (line ~751)
- `server/routers/projects.py` — Style API endpoints (line ~116)
- `prompts.py` — `_get_style_context()` function (line ~137)

## Part 1: Layout Redesign

### Current Layout Problems
- Style cards waste ~60% of their width on empty space. Only the left portion (color dots,
  button preview, card sample) is unique per style. The rest is padding/whitespace.
- Modifiers section takes a full column but only has 4 items.
- Accent styles only show 3 of 12 — should show all 12.
- Color palettes only show ~4 of 25 — wasted vertical space above them.
- Too much scrolling. User loses context when scrolling between sections.

### Target Layout (3 columns, everything visible)

```
┌───────────────────┬──────────────────────┬──────────────────────────────┐
│                   │                      │  [Quad] [Single]             │
│  12 Base Style    │  MODIFIERS (compact) │                              │
│  Cards            │  ☐ High Contrast Btn │  ┌────────┐ ┌────────┐      │
│  (4 cols x 3 rows)│  ☐ Large Touch       │  │Landing │ │Dashbrd │      │
│                   │  ☐ High Contrast Txt │  │        │ │        │      │
│  Compact cards:   │  ☐ Large Type Scale  │  └────────┘ └────────┘      │
│  Only show the    │                      │  ┌────────┐ ┌────────┐      │
│  unique part      │  ACCENT STYLE        │  │Settings│ │ Feed   │      │
│  (color dots,     │  (all 12, compact    │  │        │ │        │      │
│  buttons, card    │   same card style    │  └────────┘ └────────┘      │
│  preview)         │   as base but tiny)  │                              │
│                   │                      │  ─── Favorites Bar ───       │
│  ★ = favorited    │  25 COLOR PALETTES   │  [Fav1] [Fav2] [Fav3]      │
│                   │  ← [palette dots] →  │                              │
│                   │  Arrow scroll thru   │                              │
└───────────────────┴──────────────────────┴──────────────────────────────┘
```

### Specific Layout Instructions

#### Left Column: 12 Base Style Cards (compact)
- **Crop the cards.** Each card should only show the unique visual portion — color swatch
  dots at top, button samples ("Primary", "Secondary"), and the small card preview below.
  Remove the right ~60% that's just whitespace/padding.
- **4 columns x 3 rows** to fit all 12 on screen without scrolling.
- Each card is clickable. Selected card gets a highlight border.
- **Favorite star** on each card — click to shortlist it. Favorited cards appear in the
  Favorites Bar above the preview area.

#### Middle Column: Controls (stacked tight)
- **Modifiers** at top — 4 checkboxes, compact. One line per modifier with a short label.
  No descriptions needed (tooltip on hover for details). Takes ~4 lines total.
- **Accent Styles** below modifiers — ALL 12 styles shown as very small cards or pills.
  Same compact format as the base cards but even smaller (just color dots + name).
  3 or 4 columns. Clickable. Selected accent gets highlight. Optional "None" pill to clear.
- **Color Palettes** at bottom — Show all 25 palette presets as dot groups (already exists).
  Add **left/right arrow buttons** to cycle through palettes one at a time.
  When user clicks an arrow, the preview updates live with the next palette.
  Show the palette name and the 6 color swatches (Primary, Secondary, Accent, Background, Surface, Text).

#### Right Side: Preview Area
- **Quad/Single toggle** at top (already exists).
- **Quad mode:** 4 preview pages at once (Landing, Dashboard, Settings, Feed). Good for
  quick browsing — scroll through base styles and see all 4 pages update.
- **Single mode:** One page at a time, larger. Good for detailed evaluation of a finalist.
- **Favorites Bar** between the toggle and preview — small thumbnails of favorited
  base styles. Click one to instantly switch to it. This lets you rapidly compare
  your top 3 without scrolling back to the left column.

### User Workflow This Layout Enables

1. Scan all 12 base styles (all visible, no scrolling) → star 3 favorites
2. Click through favorites in the bar → compare in quad view
3. Switch to single view on the winner → scroll through all 4 pages
4. Click accent styles → preview updates live → find the best mix
5. Toggle modifiers on/off → see effect immediately
6. Arrow through color palettes → preview updates live with each palette
7. Everything happens on ONE screen. No scrolling between sections.

## Part 2: Backend — Restore Full Accent Support

### 1. Show All 12 Styles as Accents

In `server/services/style_manager.py`:
- Ensure ALL 12 styles are available as accent options (currently only 3 appear)
- Add `get_accent_tokens(base_style_id, accent_style_id)` function:
  - Base provides: layout, backgrounds, typography, spacing
  - Accent provides: button colors, card borders, link colors, focus rings, hover states

### 2. API Endpoint for Accent Preview Tokens

In `server/routers/projects.py`:
- Add `GET /api/styles/{style_id}/accent-preview?accent={accent_id}` — returns merged
  tokens for the preview to render

### 3. Store Accent in Project Config

In `server/schemas.py`:
- Add `accent_style_id: str | None = None` to `ProjectCreate`

In `prompts.py`:
- Extend `_get_style_context()` to inject accent tokens when set

## What NOT to Do

- Do NOT change the 12 base style definitions
- Do NOT change the modifier system (it works perfectly)
- Do NOT change the preview rendering engine itself (just feed it different tokens)
- Do NOT break the existing Quad/Single toggle
- Do NOT add new dependencies
- Do NOT change any other pages or components outside the style preview page

## Testing

```bash
cd ui && npm run build    # Type check + build
ruff check .              # Python lint
```

## How to Verify

- All 12 base style cards visible on screen without scrolling (4x3 compact grid)
- All 12 accent styles visible in middle column
- All 25 color palettes accessible via arrow navigation
- Clicking any base/accent/modifier/palette updates preview live
- Favorites bar shows starred styles, clicking one switches instantly
- Quad view shows 4 pages, Single view shows 1 page larger
- Creating a project stores base + accent + modifiers + palette
- No regressions — existing style selection flow still works
