# Style Guide Generator

Extract a visual design system from any screenshot. Use this with Claude Code or any AI tool that accepts images.

## How to Use

1. Find a screenshot of an app/website whose visual style you like
2. Paste the screenshot along with the prompt below into Claude Code
3. Paste the output into Section 3 of `BUILD_PROMPT.md`

---

## THE PROMPT (Copy Below This Line)

---

Analyze this screenshot and extract a complete visual design system. Output the following sections:

### Color Palette

Extract every distinct color visible in the UI. For each, provide:
- Hex value
- Where it's used (background, text, accent, border, etc.)
- A semantic name (e.g., "surface-primary", "text-muted", "accent-brand")

Group into:
- **Backgrounds**: Canvas, card/surface, muted/secondary, elevated
- **Text**: Primary, secondary, muted/tertiary, inverse
- **Borders**: Subtle, default, strong
- **Accents**: Brand/primary, success, warning, error, info
- **Interactive**: Hover states, active states, focus rings

### Typography

For each text level visible:
- Approximate size (px or rem)
- Weight (regular, medium, semibold, bold)
- Color (reference palette above)
- Letter-spacing if notable
- Line-height if notable

Organize as: Page title, Section header, Card title, Body, Small/Meta, Button text, Input text

### Spacing & Layout

- Base spacing unit (4px or 8px grid?)
- Card padding
- Gap between sections
- Gap between elements within sections
- Page margins/padding
- Maximum content width

### Border Radius

- Cards
- Buttons
- Inputs
- Avatars/badges
- Tags/chips

### Shadows

- Card shadow
- Elevated/dropdown shadow
- Button shadow (if any)
- Focus ring style

### Component Patterns

Describe the visual treatment of:
- **Cards**: Background, border, shadow, radius, padding
- **Buttons**: Primary, secondary, ghost/text variants
- **Inputs**: Background, border, focus state, placeholder color
- **Navigation**: Active state, hover state, icon treatment
- **Badges/Tags**: Background, text, radius

### Animation & Motion

Note any visible:
- Hover transitions
- Card lift effects
- Button press effects
- Modal/dialog appearance

### Overall Vibe

In 2-3 sentences, describe the design personality: Is it minimal? Bold? Playful? Corporate? Warm? Cold? What makes it distinctive?

### Tailwind Theme Tokens

Output as CSS custom properties that integrate into an existing Tailwind + shadcn/ui setup. Use the shadcn/ui CSS variable convention:

```css
/* Paste into your globals.css @layer base */
:root {
  --background: [h s% l%];
  --foreground: [h s% l%];
  --card: [h s% l%];
  --card-foreground: [h s% l%];
  --primary: [h s% l%];
  --primary-foreground: [h s% l%];
  --secondary: [h s% l%];
  --secondary-foreground: [h s% l%];
  --muted: [h s% l%];
  --muted-foreground: [h s% l%];
  --accent: [h s% l%];
  --accent-foreground: [h s% l%];
  --destructive: [h s% l%];
  --destructive-foreground: [h s% l%];
  --border: [h s% l%];
  --input: [h s% l%];
  --ring: [h s% l%];
  --radius: [value];
}

.dark {
  --background: [h s% l%];
  --foreground: [h s% l%];
  /* ... same variables, dark mode values */
}
```

**Important:** The boilerplate already uses Tailwind + shadcn/ui with these CSS variables defined. The generated tokens should be designed to **replace values in the existing theme**, not create a parallel system. Just swap the HSL values.
