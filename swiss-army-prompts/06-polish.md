# MODULE 06: POLISH PROMPT

## The "Make It Not Look Vibe-Coded" Module

**What this does:** Adds every professional detail that separates amateur apps from production-quality ones. Hover states, transitions, accessibility, offline handling, session expiry, keyboard navigation, responsive micro-interactions, and error recovery.

**Prerequisite:** Modules 01-05 should be complete. This module polishes everything that exists.

**When to use:** After your app's core functionality works but before you show it to anyone.

---

## --- START PROMPT ---

## TASK: Polish This App to Production Quality

Review the entire codebase and add every missing professional detail. Go through each section below systematically. Do not skip any section.

Read ALL files in `src/components/`, `src/pages/`, `src/contexts/`, and `src/index.css` before starting. Understand what exists.

---

## SECTION 1: HOVER STATES

Every interactive element MUST have a visible hover response. Audit every component and page.

| Element Type | Required Hover Effect |
|---|---|
| Cards (clickable) | `hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer` |
| Primary buttons | `hover:bg-brand-dark transition-colors` |
| Secondary buttons | `hover:bg-border-subtle transition-colors` |
| Ghost buttons | `hover:bg-surface-muted transition-colors` |
| Danger buttons | `hover:bg-red-700 transition-colors` |
| Text links | `hover:text-brand hover:underline transition-colors` |
| Icon buttons | `hover:bg-surface-muted rounded-lg p-2 transition-colors` |
| Table/list rows | `hover:bg-surface-muted transition-colors` |
| Sidebar nav items | `hover:bg-surface-muted rounded-lg transition-colors` |
| Dropdown items | `hover:bg-surface-muted transition-colors` |

**Rule:** If you can click it, it must visually respond to hover. No exceptions.

---

## SECTION 2: TRANSITIONS AND ANIMATIONS

Add these CSS animations and apply them throughout the app.

**Add to src/index.css (animations section):**

```css
/* Modal backdrop fade */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal content scale */
@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

/* Toast slide in from right */
@keyframes slide-in-right {
  from { opacity: 0; transform: translateX(100%); }
  to { opacity: 1; transform: translateX(0); }
}

/* Mobile sidebar slide in from left */
@keyframes slide-in-left {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

/* Subtle fade for page content */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in { animation: fade-in 0.2s ease-out; }
.animate-scale-in { animation: scale-in 0.2s ease-out; }
.animate-slide-in-right { animation: slide-in-right 0.3s ease-out; }
.animate-slide-in-left { animation: slide-in-left 0.3s ease-out; }
.animate-fade-up { animation: fade-up 0.3s ease-out; }
```

**Apply to components:**
- Modal backdrop → `animate-fade-in`
- Modal content → `animate-scale-in`
- Toast → `animate-slide-in-right`
- Mobile sidebar → `animate-slide-in-left`
- Page main content → `animate-fade-up`
- Buttons → `active:scale-[0.98] transition-all duration-150`
- Cards → `transition-all duration-200`

---

## SECTION 3: ACCESSIBILITY

### Focus States

Every interactive element needs a visible focus ring for keyboard navigation:

```
focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2
```

Apply to: buttons, links, inputs, selects, textareas, cards (if clickable).

For dark mode, add: `focus:ring-offset-surface-base` (so the offset matches the background).

### Keyboard Navigation

**Modals:**
```typescript
// Already in Modal from Module 04, but verify:
// - Escape closes
// - Tab cycles through focusable elements (focus trap)
// - First focusable element receives focus on open
// - Focus returns to trigger element on close
```

**Dropdown menus (if any):**
- Arrow keys move selection
- Enter/Space selects
- Escape closes

### ARIA Labels

Audit every icon-only button and add `aria-label`:

```tsx
// Good
<button aria-label="Close modal" onClick={onClose}>
  <X className="w-5 h-5" />
</button>

// Good
<button aria-label="Delete item" onClick={onDelete}>
  <Trash2 className="w-5 h-5" />
</button>

// Good
<button aria-label="Toggle dark mode" onClick={toggleTheme}>
  {theme === 'light' ? <Moon /> : <Sun />}
</button>
```

### Screen Reader Support

```tsx
// Loading states
{loading && <span className="sr-only">Loading content...</span>}

// Status messages
<div role="status" aria-live="polite">
  {toasts.map(toast => ...)}
</div>

// Form errors
<p role="alert" className="text-sm text-red-600">{error}</p>
```

Add `sr-only` class if not already in CSS:
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
```

### Touch Targets

On mobile, all clickable elements must be at least 44x44px:

```tsx
// Icon buttons — ensure min size
className="p-2.5 ..." // 20px icon + 10px padding each side = 40px. Add more if needed.

// Or use min-h and min-w
className="min-h-[44px] min-w-[44px] ..."
```

---

## SECTION 4: OFFLINE HANDLING

Detect network status and inform the user.

**Create src/hooks/useOnlineStatus.ts:**

```typescript
import { useEffect, useState } from 'react'

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  )

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}
```

**Add an offline banner to Layout.tsx:**

```tsx
const isOnline = useOnlineStatus()

// At the top of the layout, above the header:
{!isOnline && (
  <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 px-4 py-2 text-center text-sm font-medium">
    You're offline. Some features may not work until you reconnect.
  </div>
)}
```

---

## SECTION 5: SESSION EXPIRY HANDLING

Supabase sessions expire. Handle it gracefully instead of showing cryptic errors.

**Update src/contexts/AuthContext.tsx:**

In the `onAuthStateChange` listener, add handling for token refresh failures:

```typescript
// Inside the onAuthStateChange callback:
if (event === 'TOKEN_REFRESHED' && session?.user) {
  setUser(session.user)
} else if (event === 'SIGNED_OUT') {
  setUser(null)
  setProfile(null)
  // If they were on a protected route, redirect gracefully
  if (window.location.pathname !== '/' && window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}
```

**Wrap service calls to catch auth errors:**

Update `src/services/database.ts` — add a helper:

```typescript
function handleSupabaseError(error: { code: string; message: string }, operation: string): never {
  if (error.code === 'PGRST301' || error.code === '401' || error.message.includes('JWT')) {
    throw new Error('Your session has expired. Please sign in again.')
  }
  if (error.code === '42501' || error.message.includes('permission denied')) {
    throw new Error('You don\'t have permission to do this.')
  }
  if (error.code === 'PGRST116') {
    throw new Error('Item not found. It may have been deleted.')
  }
  throw new Error(`Failed to ${operation}. Please try again.`)
}
```

Then use it in every service function:
```typescript
if (error) handleSupabaseError(error, 'load items')
```

---

## SECTION 6: ERROR RECOVERY

Every error state should be actionable, not a dead end.

**Pattern for pages with data fetching:**

```tsx
if (error) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      <h2 className="text-lg font-semibold text-text-primary mb-2">Something went wrong</h2>
      <p className="text-text-secondary mb-6 max-w-sm">{error}</p>
      <Button variant="secondary" onClick={refetch}>
        Try Again
      </Button>
    </div>
  )
}
```

**Pattern for inline actions (save/delete/update):**

```typescript
try {
  await updateEntity(id, data)
  showToast({ type: 'success', message: 'Saved!' })
} catch (err) {
  const message = err instanceof Error ? err.message : 'Something went wrong'
  showToast({ type: 'error', message })
  // IMPORTANT: Do NOT navigate away. Stay on the page. Keep the form data.
}
```

---

## SECTION 7: TEXT AND DATA FORMATTING

Audit every page and ensure:

### Dates
- NO raw timestamps displayed anywhere
- List views: `formatRelativeTime` ("3d ago")
- Detail views: `formatFullDate` ("January 15, 2026 at 3:45 PM")

### Numbers
- Use `pluralize` helper: "1 item" not "1 items"
- Large numbers: toLocaleString() — "1,234" not "1234"

### Long Text
- Card titles: `truncate` class (single line ellipsis)
- Card descriptions: `line-clamp-2` (two line ellipsis)
- Sidebar items: `truncate max-w-[180px]`
- Table cells: `truncate max-w-[200px]`

### Empty Values
- Show "—" (em dash) for null/empty fields, not "null" or blank space
- `{item.description || '—'}`

---

## SECTION 8: FORM FIELD POLISH

Audit all forms (Create and Edit pages):

1. **Labels:** Every input has a label. Required fields show `*` in red.
2. **Placeholder text:** Helpful hint, not just the field name ("e.g., My First Project")
3. **Error states:** Red border, red background tint, error message below
4. **Disabled during submit:** All fields disabled while `isSubmitting`
5. **Autofocus:** First input focused on page load
6. **Enter key:** Forms submit on Enter (via `<form onSubmit>`)
7. **Tab order:** Logical tab order (top to bottom, left to right)

---

## SECTION 9: CONSOLE CLEANUP

Open the app and navigate through EVERY page and action. Fix any:

- `console.log` statements (remove them all)
- React key warnings (ensure unique keys in all `.map()` calls)
- Missing useEffect dependency warnings (fix dependencies or add eslint-disable with justification)
- TypeScript errors in the console
- Network errors (404s, failed fetches)
- Unused variable warnings

**Goal: Zero console output on a clean run through the entire app.**

---

## SECTION 10: RESPONSIVE SPOT CHECK

Resize browser to mobile width (375px) and verify every page:

| Page | Check |
|------|-------|
| Landing | Text readable, CTA visible, no horizontal scroll |
| Login | Card fits screen, button full width |
| Dashboard | Cards stack vertically, no overflow |
| List | Cards single column, search full width, pagination controls accessible |
| Detail | Content fits, buttons full width or stacked, back link visible |
| Create/Edit | Inputs full width, labels visible, submit button accessible |
| Profile | Content fits, danger zone visible |
| 404 | Centered, readable |

Also check at tablet (768px) and desktop (1280px).

---

## COMMIT

```bash
git add -A
git commit -m "polish: add hover states, animations, a11y, offline handling, error recovery, responsive fixes"
```

---

## WHAT THIS MODULE FIXED

| Category | Before | After |
|----------|--------|-------|
| Hover states | Some elements have no feedback | Every clickable element responds |
| Animations | Instant/jarring transitions | Smooth fade, scale, slide |
| Accessibility | No focus rings, no ARIA | Full keyboard nav, screen reader support |
| Offline | Cryptic errors | "You're offline" banner |
| Session expiry | Broken state | Graceful redirect to login |
| Errors | Dead ends | Retry buttons, helpful messages |
| Text | Raw timestamps, "null" | Relative dates, em dashes |
| Forms | Minimal feedback | Full validation, disabled states, autofocus |
| Console | Warnings and errors | Clean — zero output |
| Mobile | Maybe works | Verified at 375px, 768px, 1280px |

---

## WHAT'S NEXT

| Module | What It Adds |
|--------|-------------|
| **07 — Style & Theming** | Your specific visual identity, landing page, brand colors |
| **08 — Bug Fix Protocol** | Systematic approach to fixing bugs |

---

## --- END PROMPT ---
