# Theme DNA -- CSS Variable Guide

## What This Is

`theme-variables-canonical.css` is the **contract** between theme sources and components. Every theme source (image extractor, style renderer) writes these exact variable names. Every component reads only these variable names. If a variable is not in that file, it does not exist.

## Three Tiers

| Tier | Who sets it | Examples | Override? |
|------|------------|---------|-----------|
| **Scale** | `:root` only | `--space-4`, `--radius-sm`, `--font-size-lg` | Never -- these are the raw design tokens |
| **Semantic** | Theme `[data-theme]` blocks | `--radius-card`, `--shadow-btn`, `--spacing-card-padding` | Yes -- themes point these at different scale values |
| **Color** | Theme `[data-theme]` blocks | `--color-brand`, `--color-bg-card`, `--color-text-primary` | Yes -- every theme sets its own palette directly |

Components read semantic and color vars. They never reference scale vars for layout decisions.

## How a Theme Source Uses It

A theme source (image extractor or style renderer) outputs a `[data-theme]` block that overrides only semantic and color vars:

```css
[data-theme="my-theme"] {
  --color-brand:       #e11d48;
  --color-bg-card:     #1e1e2e;
  --radius-card:       var(--radius-2xl);
  --shadow-card:       0 8px 24px rgba(0, 0, 0, 0.3);
  /* ... only the vars that differ from :root defaults */
}
```

Scale vars (`--space-4`, `--font-size-base`, etc.) stay untouched.

## How a Component Uses It

```css
.card {
  background:    var(--color-bg-card);
  border:        1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding:       var(--spacing-card-padding);
  box-shadow:    var(--shadow-card);
  transition:    var(--transition-shadow);
}
.card:hover {
  box-shadow:    var(--shadow-card-hover);
}
```

The component never hard-codes a colour, radius, or shadow. Swap the `data-theme` attribute on `<html>` and every component updates automatically.

## How to Add a New Theme

1. Pick a name (lowercase, hyphenated): `my-new-theme`.
2. Copy one of the five override blocks in the canonical file.
3. Change only the values. Do not add new variable names.
4. Apply it: `<html data-theme="my-new-theme">`.

If you need a variable that does not exist yet, add it to `:root` in the canonical file first, then use it in your theme block.

## File Locations

| File | Purpose |
|------|---------|
| `docs/info/theme-variables-canonical.css` | The variable contract (source of truth) |
| `docs/info/theme-variables-guide.md` | This guide |
