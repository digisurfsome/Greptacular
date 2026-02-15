# Build Prompt: Restore Style Mixing Board

## What You Are Doing

Restore the style mixing feature that was removed during a UI restructure. The base style
selection (12 styles) works perfectly. The modifier selection (4 accessibility modifiers)
works perfectly. What's missing is the ACCENT STYLE selector — a second style picker where
the user picks one of the same 12 styles to mix with the base style.

## Read These First

- `.claude/handoffs/style-mixing-handoff.md` — Full spec for the mixing feature
- `.claude/handoffs/style-preview-grid-handoff.md` — Preview engine spec (includes mixing preview section)
- `server/services/style_manager.py` — Current style registry (12 styles, no accent data yet)
- `server/services/style_modifiers.py` — Working modifier system (follow this pattern)
- `ui/src/components/NewProjectModal.tsx` — Current style step (line ~547), modifiers work (line ~751)
- `server/routers/projects.py` — Style API endpoints (line ~116)
- `prompts.py` — `_get_style_context()` function (line ~137)

## What to Build

### 1. Backend: Add Accent Style Support to Style Manager

In `server/services/style_manager.py`:
- Add `accent_compatibility` to each style definition — a list of style IDs that work well as accents
- Every style should be compatible with every other style (all 12 options available as accents)
- Add `get_accent_tokens(base_style_id, accent_style_id)` function that returns merged tokens:
  - Base style provides: layout, backgrounds, typography, spacing
  - Accent style provides: button colors, card borders, link colors, focus rings, hover states

### 2. Backend: Add Accent API Endpoint

In `server/routers/projects.py`:
- Add `GET /api/styles/{style_id}/accents` — returns list of accent-compatible styles with preview tokens

### 3. Backend: Store Accent Style in Project Config

In `server/schemas.py`:
- Add `accent_style_id: str | None = None` to `ProjectCreate` and project models

In `prompts.py`:
- Extend `_get_style_context()` to inject accent style tokens when `accent_style_id` is set

### 4. UI: Add Accent Style Selector to NewProjectModal

In `ui/src/components/NewProjectModal.tsx`:
- After the base style is selected, show a section: "Mix with an accent style (optional)"
- Display the same 12 styles as small cards/pills that the user can click
- Selected accent gets highlighted
- "No accent" / "Skip" option to use base style alone
- The accent selection should appear in the same style step, below the base style grid
- Follow the exact same pattern as the modifier selector (line ~751) for consistency

### 5. UI: Update Preview to Show Mixed Styles

- When both base and accent are selected, the style preview should show the accent colors
  on buttons, cards, and interactive elements
- The preview already renders — just feed it the merged tokens

## What NOT to Build

- Do NOT change the 12 base styles
- Do NOT change the modifier system (it works)
- Do NOT change the style preview rendering engine (just feed it different tokens)
- Do NOT add complex compatibility rules — all 12 styles should be available as accents for any base
- Do NOT restructure the style step layout — just add the accent selector below the existing content

## Testing

```bash
cd ui && npm run build    # Type check + build
ruff check .              # Python lint
```

## How to Verify

- Select a base style → see 12 accent options appear below
- Click an accent → preview updates to show mixed colors on buttons/cards
- Skip accent → works exactly like before (no regression)
- Create a project with base + accent → both stored in config
- Agent gets accent style tokens in its prompt
