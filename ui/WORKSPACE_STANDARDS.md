# Workspace UI Standards

> Permanent build standards for all new workspace pages and components.
> Every agent building workspace UI **must** follow these patterns.

## Stack (Mandatory)

- React 19 + TypeScript
- Tailwind CSS v4 (neobrutalism design system from `globals.css`)
- TanStack React Query for server state
- Radix UI primitives (via `components/ui/`)
- Lucide React for all icons
- Hash-based routing (`main.tsx`)

## File Structure

New workspace features follow this layout:

```
ui/src/
├── pages/
│   └── MyNewPage.tsx              # Top-level page (hash route target)
├── components/workspace/
│   └── my-feature/                # Feature folder for complex features
│       ├── MyFeatureList.tsx       # List/grid view
│       ├── MyFeatureDetail.tsx     # Detail/read-only view
│       ├── MyFeatureForm.tsx       # Create/edit form
│       └── MyFeatureCard.tsx       # Card component for list
├── hooks/
│   └── useMyFeature.ts            # React Query hooks for this feature
├── lib/
│   ├── api.ts                     # Add API functions here (don't create new files)
│   └── types.ts                   # Add TypeScript interfaces here
```

Rules:
- One component per file
- Group related components in feature folders under `components/workspace/`
- All TypeScript interfaces go in `lib/types.ts`
- All API functions go in `lib/api.ts`
- Custom hooks get their own file in `hooks/`

## Routing

Hash-based routing in `main.tsx`:

```tsx
// Add new routes in the Root() function
if (hash === '#/my-page') return <MyNewPage />
```

Add a route helper in `lib/routes.ts`:

```tsx
export function isMyPageRoute(): boolean {
  return window.location.hash === '#/my-page'
}
```

## Page Layout Pattern

Every workspace page uses this structure:

```tsx
<div className="h-screen flex flex-col bg-background">
  {/* Breadcrumb bar — h-10, matches workspace */}
  <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
    <nav className="flex items-center gap-1 text-sm">
      <Button variant="ghost" size="sm" className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
        onClick={() => { window.location.hash = '#/workspace' }}>
        <ArrowLeft size={14} />
        <span className="text-xs">Workspace</span>
      </Button>
      <ChevronRight size={12} className="text-muted-foreground" />
      <span className="text-xs font-semibold text-foreground">Page Title</span>
    </nav>
    <div className="ml-auto flex items-center gap-1">
      {/* Action buttons go here */}
    </div>
  </div>

  {/* Main scrollable content */}
  <main className="flex-1 overflow-auto p-6">
    <div className="max-w-7xl mx-auto">
      {/* Page content */}
    </div>
  </main>
</div>
```

## Design System

### Typography

| Element        | Classes                                          |
|----------------|--------------------------------------------------|
| Page Title     | `text-2xl font-semibold text-foreground`         |
| Section Header | `text-lg font-semibold text-foreground`          |
| Card Title     | `text-base font-medium text-foreground`          |
| Body Text      | `text-sm text-muted-foreground`                  |
| Small/Meta     | `text-xs text-muted-foreground`                  |

### Cards

```tsx
<div className="bg-card rounded-lg border border-border p-6 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer">
```

### Buttons

Use the existing `<Button>` component from `components/ui/button`:

```tsx
import { Button } from '@/components/ui/button'

<Button variant="default">Primary</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="outline">Outline</Button>
<Button variant="destructive">Danger</Button>
```

### Inputs

```tsx
<input className="w-full px-4 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground" />
```

### Color Tokens (from globals.css)

Use semantic Tailwind classes, not hardcoded colors:

- `bg-background` / `bg-card` / `bg-muted` — surfaces
- `text-foreground` / `text-muted-foreground` — text
- `border-border` — borders
- `bg-primary text-primary-foreground` — primary actions
- `bg-destructive text-destructive-foreground` — destructive actions

Status colors (neobrutalism tokens):
- Pending: `bg-[--color-neo-pending]` (yellow)
- In Progress: `bg-[--color-neo-progress]` (cyan)
- Done: `bg-[--color-neo-done]` (green)

### Spacing

- Card padding: `p-6`
- Section gaps: `gap-6`
- Element gaps: `gap-4`
- Page padding: `p-6`

## Responsive Design

Build mobile-aware but desktop-first (workspace is a desktop tool):

```tsx
// Card grid
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

// Responsive padding
<div className="p-4 lg:p-6">
```

## Data Patterns

### CRUD Views

Any user-created data follows this flow:

```
List View → click item → Detail View
   ↓                         ↓
Create Form              Edit Form
   ↓                         ↓
Detail View ← ← ← ← ← Detail View
```

- **List View**: Cards/grid with search when > 5 items expected
- **Detail View**: Read-only display, action buttons (Edit, Delete)
- **Create/Edit**: Form with validation, cancel returns to previous view
- Delete always uses a confirm dialog

### Loading States

- Lists: Skeleton cards (not spinners)
- Buttons during action: Spinner inside button, disable button
- Detail view: Skeleton matching content layout

```tsx
// Skeleton card
<div className="animate-pulse bg-muted rounded-lg h-32" />

// Loading button
<Button disabled={isPending}>
  {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
  {isPending ? 'Saving...' : 'Save'}
</Button>
```

### Empty States

Always use an icon + message + CTA button:

```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <PackageOpen className="w-12 h-12 text-muted-foreground mb-4" />
  <h3 className="text-lg font-medium text-foreground mb-1">No items yet</h3>
  <p className="text-sm text-muted-foreground mb-4">Get started by creating your first item.</p>
  <Button>Create Item</Button>
</div>
```

### Error States

Show error message + retry action:

```tsx
<div className="text-center py-8">
  <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
  <p className="text-sm text-muted-foreground mb-4">{error.message}</p>
  <Button variant="outline" onClick={() => refetch()}>Try Again</Button>
</div>
```

### Feedback

- Success/error: Use toast notifications (not `alert()`)
- Destructive actions: Always use confirm dialog (not `confirm()`)
- Never use `alert()`, `confirm()`, or `prompt()`

## Backend Patterns

### Database (workspace_database.py)

- SQLAlchemy ORM models in `workspace_database.py`
- Session-based queries with `get_db_session()`, always close in `finally`
- `Base.metadata.create_all()` auto-creates tables
- Migration code in `get_engine()` for adding columns to existing tables

### API Router (server/routers/)

- FastAPI router with Pydantic request models
- Prefix: `/api/workspace/{feature}`
- Register in `routers/__init__.py` and `main.py`
- Follow existing patterns: lazy imports from services

### React Query Hooks

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function useMyFeatures() {
  return useQuery({
    queryKey: ['workspace', 'my-features'],
    queryFn: () => fetchJSON<MyFeature[]>('/workspace/my-features'),
  })
}

export function useCreateMyFeature() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: MyFeatureCreate) =>
      fetchJSON<MyFeature>('/workspace/my-features', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workspace', 'my-features'] }),
  })
}
```

## Anti-Patterns (Do NOT Do)

- No `alert()`, `confirm()`, `prompt()`
- No inline styles — Tailwind only
- No `any` types — define TypeScript interfaces
- No database calls in components — use API layer
- No text-only empty states — always icon + CTA
- No loading states that are just "Loading..." text
- No clicking a saved item opening directly in edit mode
- No delete without confirmation
- No success/error without toast feedback
- No console.log for user feedback
- No hardcoded hex colors — use semantic Tailwind tokens

## Icons — Lucide React

```tsx
import { Home, Settings, Trash2, Plus, Loader2, Search, ArrowLeft, ChevronRight } from 'lucide-react'

<Home className="w-5 h-5" />
<Loader2 className="w-4 h-4 animate-spin" />
```

## Text Handling

- Truncate long text: `className="truncate"` or `className="line-clamp-2"`
- Format dates as relative time (not raw timestamps)
- Search/filter on lists with > 5 expected items

## Hover & Transitions

```tsx
// Cards — lift effect
className="hover:shadow-md hover:-translate-y-0.5 transition-all"

// Buttons — handled by Button component
// Links — color shift
className="hover:text-foreground transition-colors"
```

## Keyboard Accessibility

- Escape closes modals/panels
- Focus ring: `focus:outline-none focus:ring-2 focus:ring-primary`
- Icon buttons always have `aria-label`
