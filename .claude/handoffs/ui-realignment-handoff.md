# Handoff: AutoForge UI Realignment to Mentor's Design System

## Overview

AutoForge's own UI was built ad-hoc by different agents over time, resulting in inconsistent typography, spacing, colors, and component patterns across the interface. This handoff realigns ALL existing components to follow a single, locked-in design standard based on a professional design system.

After this realignment, a `STYLE_GUIDE.md` will be created and committed to the repo. ALL future UI changes must follow this guide.

**This is NOT about adding features. This is about making what already exists consistent and professional.**

---

## The Current Problems (Audit Results)

### 1. Hardcoded Colors Everywhere
- `FeatureCard.tsx`: Category badges use hardcoded `bg-pink-500`, `bg-cyan-500`, etc. (lines 19-25)
- `DebugLogViewer.tsx`: Log levels hardcoded as `text-red-500`, `text-yellow-500`, `text-blue-400` (lines 282-286)
- `DependencyGraph.tsx`: Node colors hardcoded as hex values (`#a1a1aa`, `#22c55e`, `#06b6d4`, etc.)
- `App.tsx`: GLM badge uses hardcoded `bg-purple-500 text-white hover:bg-purple-600`

### 2. No Consistent Spacing Scale
- `DebugLogViewer.tsx`: `px-1 py-0.5` for log items
- `FeatureCard.tsx`: `py-3` card, `p-4 space-y-3` content
- `SettingsModal.tsx`: `p-3` theme buttons vs `py-1.5 px-3` provider buttons
- `ProgressDashboard.tsx`: `pt-3 pb-3` instead of `py-3`
- No consistent relationship between outer padding and inner gaps

### 3. Ad-hoc Typography
- Text sizes scattered: `text-[10px]`, `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`
- No defined hierarchy (what's a page title vs section header vs card title vs body text?)
- Font weights inconsistent for similar roles

### 4. Button/Input Inconsistency
- Theme selection buttons: `p-3`
- API provider buttons: `py-1.5 px-3`
- Model selection buttons: `py-2 px-3`
- Similar roles, different sizing

---

## The Target Design System

### Typography Scale (Locked In)

| Role | Tailwind Classes | Usage |
|------|---------|-------|
| **Page Title** | `text-2xl font-semibold` | One per page/view. Dashboard title, Settings title, etc. |
| **Section Header** | `text-lg font-semibold` | Groups within a page. "Agent Controls", "Features", etc. |
| **Card Title** | `text-base font-medium` | Card headers, modal titles, panel headers |
| **Body Text** | `text-sm` | Default readable text, descriptions, paragraphs |
| **Small/Meta** | `text-xs text-muted-foreground` | Timestamps, counts, labels, badges |
| **Micro** | `text-[10px] text-muted-foreground` | Only for extremely space-constrained spots (graph nodes, minimap labels) |

**Rules:**
- NEVER use `text-xl` (it's between card title and page title — pick one)
- NEVER use arbitrary sizes like `text-[13px]` — stick to the scale
- Page titles are always `font-semibold`, card titles always `font-medium`, body always regular weight

### Spacing Scale (8px Grid)

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| **xs** | 4px | `gap-1`, `p-1` | Icon-to-text spacing, tight inline elements |
| **sm** | 8px | `gap-2`, `p-2` | Between related inline items, badge padding |
| **md** | 12px | `gap-3`, `p-3` | Between form fields, compact card padding |
| **lg** | 16px | `gap-4`, `p-4` | Standard card padding, section internal spacing |
| **xl** | 24px | `gap-6`, `p-6` | Between major sections, spacious card padding |
| **2xl** | 32px | `gap-8`, `p-8` | Main content area padding |

**Rules:**
- Card padding: `p-4` (standard) or `p-6` (spacious) — pick ONE per component type and be consistent
- Section gaps: `gap-6` between major sections
- Element gaps within sections: `gap-4`
- Always use symmetric padding (`p-4`, not `pt-3 pb-3 px-4`) unless there's a specific visual reason

### Color Rules

**NEVER hardcode colors.** Use CSS variables from the theme:

| Need | Use | NOT |
|------|-----|-----|
| Primary action color | `text-primary` / `bg-primary` | `text-blue-500` / `bg-blue-600` |
| Muted text | `text-muted-foreground` | `text-gray-500` |
| Card background | `bg-card` | `bg-white` / `bg-gray-900` |
| Borders | `border-border` | `border-gray-200` |
| Destructive | `text-destructive` / `bg-destructive` | `text-red-500` |
| Success | `text-emerald-500 dark:text-emerald-400` | `text-green-500` (no dark variant) |
| Warning | `text-amber-500 dark:text-amber-400` | `text-yellow-500` |
| Info | `text-sky-500 dark:text-sky-400` | `text-blue-400` |

**For status/category colors** (like Kanban columns, feature badges, log levels), use the CSS variables already defined in `globals.css`:
- `var(--color-status-pending)`, `var(--color-status-progress)`, `var(--color-status-done)`
- `var(--color-log-error)`, `var(--color-log-warning)`, `var(--color-log-info)`, etc.

Where CSS variables don't exist for a needed color, ADD them to `:root` in `globals.css` rather than hardcoding.

### Component Patterns

**Cards** (standardize to ONE pattern):
```html
<Card>
  <CardContent className="p-4">
    <!-- content -->
  </CardContent>
</Card>
```
Use the Radix UI Card components already in `ui/src/components/ui/card.tsx`. Don't create ad-hoc `div` cards with custom borders/shadows.

**Buttons** (use the Button component from `ui/src/components/ui/button.tsx`):
- Primary: `<Button>` (default variant)
- Secondary: `<Button variant="outline">`
- Destructive: `<Button variant="destructive">`
- Ghost: `<Button variant="ghost">`
- Size: `size="sm"` for compact areas, default for standard, `size="lg"` for primary CTAs
- NEVER style buttons with raw Tailwind when the Button component exists

**Inputs** (use the Input component from `ui/src/components/ui/input.tsx`):
- Standard: `<Input />` (already styled)
- NEVER create custom styled `<input>` elements when the component exists

---

## Files to Modify

### Priority 1: Highest Impact (fix these first)

**`ui/src/components/DependencyGraph.tsx`**
- Replace ALL hardcoded hex colors (`#a1a1aa`, `#22c55e`, `#06b6d4`, `#ef4444`, `#eab308`) with CSS variable references
- Add new CSS variables to `globals.css` if needed for graph-specific colors:
  ```css
  --color-graph-edge: oklch(...);
  --color-graph-node-pending: oklch(...);
  --color-graph-node-progress: oklch(...);
  --color-graph-node-done: oklch(...);
  --color-graph-node-failing: oklch(...);
  ```
- Standardize node padding to `px-3 py-2`

**`ui/src/components/DebugLogViewer.tsx`**
- Replace `text-red-500`, `text-yellow-500`, `text-blue-400` with the CSS variable colors already defined in globals.css (`var(--color-log-error)`, etc.)
- Replace hardcoded `bg-yellow-500 text-yellow-950` badge with proper CSS variable usage
- Standardize log item spacing to `px-2 py-1` (consistent `sm` spacing)

**`ui/src/components/FeatureCard.tsx`**
- Replace hardcoded category badge colors (`bg-pink-500`, `bg-cyan-500`, etc.) with CSS variable-based approach
- Add category color CSS variables to `globals.css` (or use a consistent mapping object)
- Standardize card padding to `p-4`

### Priority 2: Medium Impact

**`ui/src/App.tsx`**
- Replace hardcoded `bg-purple-500` GLM badge with proper semantic class
- Standardize header padding
- Ensure page title follows `text-2xl font-semibold`

**`ui/src/components/SettingsModal.tsx`**
- Standardize ALL button padding to consistent sizing:
  - Action buttons: use `<Button size="sm">` component
  - Toggle/selection buttons: consistent `py-2 px-3` everywhere
- Standardize input styling to use `<Input>` component

**`ui/src/components/AgentMissionControl.tsx`**
- Standardize card padding to `p-4`
- Fix ad-hoc `mt-4 pt-4 border-t` with proper `space-y-4` or `gap-4` patterns

**`ui/src/components/ProgressDashboard.tsx`**
- Fix `pt-3 pb-3` → `py-3`
- Standardize title to `text-lg font-semibold` (section header)
- Percentage text follows the typography scale

### Priority 3: Polish

**`ui/src/components/KanbanBoard.tsx`**
- Standardize gaps to `gap-4` or `gap-6` consistently

**`ui/src/components/ProjectSelector.tsx`**
- Standardize dropdown padding

**`ui/src/components/NewProjectModal.tsx`**
- Verify typography follows the scale (this file is 934 lines, may have inconsistencies)

---

## Create STYLE_GUIDE.md

After completing the realignment, create `ui/STYLE_GUIDE.md` with the full locked-in design system:

```markdown
# AutoForge UI Style Guide

This is the authoritative reference for AutoForge's UI design. ALL components
must follow these standards. When adding new UI, reference this guide.

## Typography
[the scale from above]

## Spacing
[the 8px grid from above]

## Colors
[the color rules from above]

## Component Patterns
[cards, buttons, inputs from above]

## Dark Mode
- All colors use CSS variables from globals.css
- Light/dark variants are handled by the theme system
- NEVER use hardcoded colors that don't adapt to dark mode
- Test both modes when making UI changes

## Adding New Components
1. Check if a primitive exists in `ui/src/components/ui/` first
2. Follow the typography scale — no arbitrary font sizes
3. Follow the spacing scale — no arbitrary padding
4. Use CSS variables for ALL colors
5. Test in both light and dark mode
6. Test at mobile (375px) and desktop (1280px) widths
```

---

## Process

1. Read `ui/src/styles/globals.css` to understand existing CSS variables and themes
2. Read `ui/src/components/ui/*.tsx` to understand the existing primitive components
3. Add any missing CSS variables to `globals.css` (:root AND .dark sections of ALL 6 themes)
4. Fix Priority 1 files first (DependencyGraph, DebugLogViewer, FeatureCard)
5. Fix Priority 2 files
6. Fix Priority 3 files
7. Create `ui/STYLE_GUIDE.md`
8. Run `cd ui && npm run build` to verify no TypeScript errors
9. Run `cd ui && npm run lint` to verify no lint errors

## What NOT To Do

- Do NOT change the existing theme color values — only replace hardcoded colors with CSS variable references
- Do NOT change functionality or layout of any component — only standardize typography, spacing, and colors
- Do NOT add new features or components
- Do NOT change the 6 theme definitions in globals.css (Twitter, Claude, Neo Brutalism, Retro Arcade, Aurora, Business)
- Do NOT refactor component structure or move files — just fix the styling
- Do NOT change any API calls, state management, or business logic
- Keep changes minimal and focused — this is a STYLE cleanup, not a rewrite
