# AutoForge UI Style Guide

This document defines the locked-in design system for the AutoForge React UI. All components must follow these rules. Agents and contributors should reference this guide before making any UI changes.

## Typography Scale

Only these 6 tiers are allowed. Do not invent intermediate sizes.

| Role | Tailwind Classes | Usage |
|------|-----------------|-------|
| **Page Title** | `text-2xl font-semibold` | Top-level headings (h1), page names |
| **Section Header** | `text-lg font-semibold` | Card titles, section headings (h2/h3) |
| **Card Title** | `text-base font-medium` | Labels within cards, feature names |
| **Body** | `text-sm` | Default body text, descriptions |
| **Small / Meta** | `text-xs text-muted-foreground` | Timestamps, secondary info, badges |
| **Micro** | `text-[10px] text-muted-foreground` | Graph node labels, step indicators only |

### Rules

- Never use `text-xl` (gap in scale between `text-lg` and `text-2xl`)
- Never use arbitrary sizes like `text-[13px]` or `text-[15px]`
- Use `font-semibold` for headings, `font-medium` for card titles, default weight for body
- Never use `font-bold` except for `text-[10px]` micro labels where legibility demands it

## Spacing

All spacing follows an 8px grid. Use symmetric padding.

| Token | Size | Usage |
|-------|------|-------|
| `xs` | `1` (4px) | Tight inner gaps (icon to text) |
| `sm` | `2` (8px) | Element inner padding, tight gaps |
| `md` | `4` (16px) | Standard card padding, section gaps within |
| `lg` | `6` (24px) | Section gaps, column gaps |
| `xl` | `8` (32px) | Page-level vertical spacing |
| `2xl` | `12` (48px) | Hero sections only |

### Rules

- Cards use `p-4` (standard) or `p-6` (spacious/modal)
- Section gaps: `gap-6`
- Element gaps within sections: `gap-4`
- Always use symmetric padding: `p-4` not `pt-3 pb-3 px-4`
- Exception: `CardHeader` may use `pb-0` to tighten against `CardContent`

## Colors

Never hardcode colors. Always use CSS variables or Tailwind semantic tokens.

### Semantic Tokens (Tailwind)

| Token | Usage |
|-------|-------|
| `text-foreground` | Primary text |
| `text-muted-foreground` | Secondary/meta text |
| `bg-background` | Page background |
| `bg-card` | Card surfaces |
| `bg-muted` | Subtle backgrounds, hover states |
| `bg-primary` / `text-primary` | Brand/accent color |
| `bg-destructive` / `text-destructive` | Errors, danger actions |
| `border-border` | All borders |

### CSS Variable Colors

For specialized UI that needs inline styles, use these CSS variables:

**Log levels** (defined per-theme in `globals.css`):
- `var(--color-log-error)` - Error messages
- `var(--color-log-warning)` - Warnings
- `var(--color-log-success)` - Success messages
- `var(--color-log-info)` - Info/debug messages
- `var(--color-log-muted)` - Muted/secondary log text

**Graph colors** (for DependencyGraph and related visualizations):
- `var(--color-graph-edge)` - Edge strokes and markers
- `var(--color-graph-node-pending)` - Pending status nodes
- `var(--color-graph-node-progress)` - In-progress status nodes
- `var(--color-graph-node-done)` - Completed status nodes
- `var(--color-graph-node-failing)` - Blocked/failing status nodes
- `var(--color-graph-bg)` - Background dots/grid

**Category badges** (for feature category differentiation):
- `var(--color-category-1)` through `var(--color-category-7)` - 7 distinct hues for badge backgrounds

### Amber/Emerald Exception

For semantic colors that don't have theme CSS variables yet (warning icons, success indicators), use dark-mode-aware Tailwind:
- Warning: `text-amber-500 dark:text-amber-400`
- Success: `text-emerald-500 dark:text-emerald-400`

These should eventually be migrated to CSS variables.

### Creating Tinted Backgrounds

When you need a status color at reduced opacity for a background:

```css
background-color: color-mix(in srgb, var(--color-graph-node-pending) 15%, var(--color-background));
border-color: var(--color-graph-node-pending);
```

## Component Patterns

### Use Primitives

Always use the Radix UI primitives from `@/components/ui/`:

| Need | Use | Not |
|------|-----|-----|
| Clickable action | `<Button>` | `<button className="...">` |
| Text input | `<Input>` | `<input className="...">` |
| Container surface | `<Card>` | `<div className="border rounded-lg...">` |
| Toggle | `<Switch>` | custom checkbox |
| Label | `<Label>` | `<label>` |
| Popup | `<Dialog>` | custom modal div |
| Dropdown | `<DropdownMenu>` | custom positioned div |

### Button Variants

- `variant="default"` - Primary actions
- `variant="outline"` - Secondary actions, toolbar buttons
- `variant="ghost"` - Tertiary actions, collapse toggles
- `variant="destructive"` - Danger actions (delete, reset)
- `size="sm"` - Toolbar/header buttons
- `size="default"` - Form submit, primary CTAs

### Card Padding

- Standard cards: `<CardContent className="p-4">`
- Modal/spacious cards: `<CardContent className="p-6">`
- Legend/compact cards: `<CardContent className="p-4">`

## Theme System

The UI supports 6 themes (Twitter, Claude, Neo Brutalism, Retro Arcade, Aurora, Business) each with light and dark modes. All 12 variants are defined in `globals.css`.

### Adding New CSS Variables

When you need a new themed color:
1. Add it to `:root` and `.dark` in `globals.css`
2. All themes inherit from these unless they override
3. Only add per-theme overrides when the theme needs a visually distinct value
4. Use hex values for simplicity (matching the existing log color pattern)

### Do NOT

- Hardcode hex values in component files
- Use Tailwind palette colors (`bg-red-500`, `text-blue-400`) for theme-dependent UI
- Use `font-bold` where `font-semibold` or `font-medium` is correct
- Use asymmetric padding (`pt-3 pb-3`) where symmetric (`py-3`) works
- Add `text-xl` (it's not in our scale)
- Create raw `<button>` or `<input>` elements when a primitive exists
