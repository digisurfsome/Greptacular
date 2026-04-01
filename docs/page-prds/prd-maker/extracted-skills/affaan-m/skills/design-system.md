# Design System — Generate & Audit Visual Systems

**Name**: design-system
**Description**: Use this skill to generate or audit design systems, check visual consistency, and review PRs that touch styling.
**Origin**: ECC

## When to Use

1. Starting a new project that needs a design system
2. Auditing an existing codebase for visual consistency
3. Before a redesign — understand what you have
4. When the UI looks "off" but you can't pinpoint why
5. Reviewing pull requests affecting styling

## Three Operating Modes

### Mode 1: Generate Design System

6-step pipeline:
1. Scan styling code
2. Extract design tokens
3. Research competitors via browser MCP
4. Propose token sets
5. Generate documentation with rationale
6. Create a self-contained preview page

**Deliverables:**
- `DESIGN.md`
- `design-tokens.json`
- `design-preview.html`

### Mode 2: Visual Audit

Evaluates ten dimensions on 0-10 scales:

1. Color consistency
2. Typography hierarchy
3. Spacing rhythm
4. Component consistency
5. Responsive behavior
6. Dark mode implementation
7. Animation appropriateness
8. Accessibility standards
9. Information density
10. Polish (hover states, loading indicators)

### Mode 3: AI Slop Detection

Identifies overused AI-design patterns:
- Gratuitous gradients
- Purple-to-blue defaults
- Glass morphism cards
- Excessive rounded corners
- Scroll animations
- Generic hero layouts
- Characterless sans-serif stacks

## Command Examples

```
/design-system generate --style minimal --palette earth-tones
/design-system audit --url http://localhost:3000 --pages / /pricing /docs
/design-system slop-check
```
