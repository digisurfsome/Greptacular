# Style Mixing: Base + Accent Style System

## Status: Ready to Implement
**Prerequisite:** Accessibility modifiers (DONE) - see `server/services/style_modifiers.py`

## What This Is

Allow users to pick TWO styles: a **dominant base** and a **lesser accent**. The base controls 80% of the app (layout, typography, colors, cards, backgrounds). The accent controls interactive elements (buttons, inputs, toggles, hover states, focus rings).

This is NOT mixing 50/50. It's dominant + accent. Think of it like a suit (base) with a tie (accent).

### Example Combinations
- **Minimalism + Neumorphism accent** = Clean layout, but buttons feel physically pressable (great for older users)
- **Flat Design + Neubrutalism accent** = Simple layout, but buttons are bold and impossible to miss
- **Dark Mode + Glassmorphism accent** = Dark surfaces, but interactive panels have frosted glass depth
- **Warmer Shades + Claymorphism accent** = Warm reading feel, but buttons are soft and inviting

### What the Accent Overrides (and ONLY these)
```
accent_overrides:
  buttons:       # Background, border, radius, shadow, hover, padding
  inputs:        # Background, border, radius, shadow, focus
  toggles:       # Track color, thumb style, active state
  focus_rings:   # Color, width, offset
  hover_states:  # Transform, shadow change, color shift
  icons_style:   # Only for interactive icons (not decorative)
```

Everything else comes from the base: colors, typography, layout density, spacing, cards, backgrounds, status colors.

## Architecture

### Data Model

In `server/services/style_manager.py`, add to each style definition:

```python
"accent_compatibility": {
    "works_as_accent_for": ["minimalism", "flat-design", "dark-mode", ...],
    "accent_token_overrides": {
        "buttons": {
            # This style's button treatment when used as accent
            "radius": "12px",
            "shadow": "4px 4px 8px #b8bec7, -4px -4px 8px #ffffff",
            "hover": "inset shadow effect",
        },
        "inputs": { ... },
    },
}
```

Not every style works as an accent for every base. The compatibility matrix:

| Accent \ Base | Flat | Minimal | Neumorph | Glass | Skeuo | Neubr | Bauhaus | Clay | Retro | Cyber | Dark | Warm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Neumorphism | Y | Y | - | N | N | N | N | Y | N | N | N | Y |
| Neubrutalism | Y | Y | N | N | N | - | Y | N | N | N | Y | N |
| Glassmorphism | N | Y | N | - | N | N | N | N | Y | Y | Y | N |
| Claymorphism | Y | Y | N | N | N | N | N | - | N | N | N | Y |
| Skeuomorphism | N | N | N | N | - | N | N | N | Y | N | N | Y |

(Y = good combo, N = clashing, dash = same style)

Simpler styles (Flat, Minimal, Dark, Warm) work best as bases.
Distinctive styles (Neumorphism, Neubrutalism, Glassmorphism) work best as accents.

### Storage

In `.autoforge/project_config.json`:
```json
{
  "style": "minimalism",
  "accent_style": "neumorphism",
  "style_modifiers": ["high-contrast-buttons", "larger-type"]
}
```

### Prompt Injection (prompts.py `_get_style_context`)

The generated prompt would be structured as:

```markdown
## DESIGN SYSTEM

### Base Style: Minimalism
[Full minimalism style guide - colors, typography, layout, spacing]

### Accent Style: Neumorphism (Interactive Elements Only)
**IMPORTANT:** Use Neumorphism ONLY for buttons, inputs, toggles, and interactive feedback.
All other elements (cards, layout, backgrounds, typography) follow the Minimalism base above.

**Button Override:**
- Radius: 12px (from Neumorphism, not Minimalism's 10px)
- Shadow: 4px 4px 8px #b8bec7, -4px -4px 8px #ffffff
- Pressed state: inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff
...

### DO (Accent Mixing):
- Keep ALL layout/typography/cards following the base style
- Apply accent treatment ONLY to interactive elements
- Ensure accent button colors still work with base color palette

### DON'T (Accent Mixing):
- Don't apply accent card styles to layout containers
- Don't change the typography to match the accent style
- Don't use the accent style's background colors
```

### API Changes

```
GET /api/styles/{style_id}/accent-compatibility
  Returns: list of style IDs that work as accents for this base

GET /api/styles/combinations
  Returns: pre-validated base+accent combos with preview data
```

### UI Changes (NewProjectModal.tsx)

After picking a base style, show an optional "Add Accent Style" section:
1. Filter to only compatible accent styles for the chosen base
2. Show them as smaller cards with just the button/input preview
3. "No accent" is the default (skip = use base style for everything)

### Implementation Order

1. Add `accent_compatibility` data to each style in `style_manager.py`
2. Add `get_accent_styles(base_id)` function that returns compatible accents
3. Add `get_mixed_style_prompt(base_id, accent_id)` that generates the combined prompt
4. Update `save_project_config()` to store `accent_style`
5. Update `_get_style_context()` in `prompts.py` to handle accent
6. Add API endpoints
7. Add UI: accent picker step after base style selection (before modifiers)
8. Update TypeScript types/hooks/api

### Prompt Budget

- Base style guide: ~3,500 chars
- Accent overrides: ~1,500 chars
- Modifiers: ~800 chars per modifier (max 3 = 2,400)
- **Total max: ~7,400 chars** - well within context budget

### Guard Rails

- Max 1 accent style (no triple-mixing)
- Accent must be in the base's compatibility list
- Accent does NOT bring its own color palette - it uses the base's colors with its own shapes/shadows/effects
- If accent + modifier conflict (e.g., Neumorphism accent buttons + High Contrast Buttons modifier), the modifier wins (accessibility always wins)
