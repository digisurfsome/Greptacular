# App Builder Standards — Phase 2+ Code Reference Map

This file is used ALONGSIDE `APP_BUILDER_STANDARDS_COMPRESSED.md` (which contains all 193 lines of rules, banned patterns, design tokens, and the 25-rule checklist). That file is the law. This file tells you where every Phase 1 code schematic now lives in the built codebase.

**How to use:** Before modifying or extending anything, READ the referenced file first. The built code IS the schematic. Match its patterns exactly. Do not invent new patterns.

---

## THEME SYSTEM

**ThemeContext full implementation** — see `src/contexts/ThemeContext.tsx`.
Reads localStorage first, falls back to `prefers-color-scheme`, toggles `.dark` class on `document.documentElement`. Match this three-step detection order exactly.

**ThemeToggle component** — see `src/components/ui/ThemeToggle.tsx`.
Swaps between Lucide `Sun` and `Moon` icons. Uses `useTheme()` hook from ThemeContext.

## AUTH & ROUTE GUARDS

**ProtectedRoute component** — see `src/components/ProtectedRoute.tsx`.
Shows loading spinner while auth state resolves, then redirects to `/login` if unauthenticated. Never flash protected content.

**AdminRoute component** — see `src/components/AdminRoute.tsx`.
Same loading guard as ProtectedRoute, but redirects to `/dashboard` if user lacks admin role. Wraps ProtectedRoute — does not duplicate its logic.

**Conditional role-based UI** — see any page that uses `isAdmin` or `isPro` from `useAuth()`.
Entire sections or buttons are conditionally rendered based on role. Never hide with CSS — use conditional JSX.

## APP BOOTSTRAP & ROUTING

**App.tsx full routing structure** — see `src/App.tsx`.
Provider nesting order matters: BrowserRouter > ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > Routes. All protected routes wrapped in `<ProtectedRoute>`, admin routes in `<AdminRoute>`, authenticated pages wrapped in `<Layout>`. Catch-all `*` route renders `<NotFoundPage>`.

## LAYOUT & NAVIGATION

**Layout structure** — see `src/components/Layout.tsx`.
Flex row: Sidebar (fixed 240px) + vertical column (Header h-16 border-b + Main flex-1 overflow-y-auto p-8). Match this exact flex structure.

**Sidebar component** — see `src/components/Sidebar.tsx`.
240px width, `bg-surface-base border-r`. Contains: logo/brand at top, nav links with active state highlight, optional recent items section, help/support link pinned to bottom.

**Responsive layout behavior** — see `src/components/Layout.tsx` and `src/components/MobileNav.tsx`.
Desktop (lg+): sidebar always visible. Mobile (<lg): sidebar hidden, hamburger button in header, sidebar slides in as overlay (not push), closes on nav click or outside click. Body scroll locks when mobile nav is open.

**Component responsive behavior table** — reference the compressed doc's Responsive Design section, then see each component for implementation. Cards: stack vertically on mobile, 2-col at `sm:`, 3-col at `lg:`. Buttons: `w-full` on mobile, auto-width on desktop. Modals: nearly full-screen on mobile, centered `max-w-md` on desktop.

**Touch target rules** — all interactive elements on mobile must be minimum 44x44px. See Button and nav link implementations for `min-h-[44px] min-w-[44px]` patterns.

**Responsive Tailwind class patterns** — see any page grid for the pattern: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`. See Sidebar for `hidden lg:flex` / `flex lg:hidden`. See page containers for `p-4 sm:p-6 lg:p-8`.

## UTILITIES

**formatDate utility** — see `src/utils/formatDate.ts`.
Full relative time implementation: <1min = "Just now", <1hr = "Xm ago", <24hr = "Xh ago", <2d = "Yesterday", <7d = "Xd ago", older = "Jan 15". Match these exact thresholds and labels.

**Pluralize helper** — see `src/utils/pluralize.ts`.
Returns `"1 item"` vs `"5 items"`. Handles count + singular + optional irregular plural. Use this everywhere a count is displayed next to a noun.

**Text truncation patterns** — see Sidebar nav items for `truncate`, card descriptions for `line-clamp-2`, table cells for `truncate max-w-[200px]`. Always set a `max-w` when truncating.

## NAVIGATION PATTERNS

**Back navigation component** — see any Detail or Edit page for the pattern at the top of the page.
Uses Lucide `ArrowLeft` icon + "Back" text in a button/link. Navigates to parent list or detail view. Placed above the page title.

**CRUD navigation flow** — the full flow diagram is in the compressed doc. The implementation lives across your page files:
`List (Dashboard)` click item -> `DetailPage` click Edit -> `EditPage` save -> `DetailPage`.
`List` click New -> `CreatePage` save -> `DetailPage`.
`DetailPage` click Delete -> `ConfirmModal` confirm -> `List`.
Never skip the Detail View. Never open Edit directly from List.

## CSS & ANIMATIONS

**Animation classes** — see `src/index.css` for custom keyframes and transitions.
Modal: fade+scale in. Toast: slide-in from right. Card: `hover:shadow-md hover:-translate-y-0.5 transition-all duration-200`. Button press: `active:scale-[0.98]`. Sidebar mobile: slide from left with backdrop fade.

**Hover states catalog** — see each component for its hover pattern:
Cards = `hover:shadow-md hover:-translate-y-0.5`. Buttons = `hover:bg-brand-dark` (darken). Links = `hover:underline`. Icon buttons = `hover:bg-surface-muted rounded`. Table rows = `hover:bg-surface-muted`. Sidebar items = `hover:bg-surface-muted`. Match these exactly.

## ACCESSIBILITY

**Keyboard: Escape closes modals** — see `src/components/ui/Modal.tsx` for the `useEffect` with `keydown` listener that calls close on Escape. Every modal and overlay must implement this.

**Icon button aria-labels** — every icon-only button must have `aria-label` describing the action. See any toolbar or action button for the pattern: `<button aria-label="Delete item">`.

**Screen reader text** — see usage of `sr-only` class for visually hidden labels. Status messages use `role="status" aria-live="polite"` for dynamic updates.

## FORMS

**Form field states** — see any Create or Edit page for the full input pattern.
Each field: `<label>` + `<input>` with conditional red border on error (`border-red-500`) + error message below (`text-red-500 text-sm`) + helper text when no error (`text-text-tertiary text-xs`). Disabled state: `opacity-50 cursor-not-allowed` on the entire form during submission.

**Unsaved changes hook** — see Edit pages for the `beforeunload` event handler.
Uses `useEffect` to add/remove a `beforeunload` listener when form state differs from initial state. The handler calls `e.preventDefault()` and sets `e.returnValue`.

**Autofocus pattern** — see Create and Edit pages for `useRef` + `useEffect` that calls `inputRef.current?.focus()` on mount. Always autofocus the first input field.

## SEARCH & FILTERING

**Search/filter pattern** — see Dashboard or any list page.
State: `searchQuery` string. Filter: `.filter(item => item.title.toLowerCase().includes(...) || item.description.toLowerCase().includes(...))`. Input: search bar with Lucide `Search` icon. Empty result: "No results found" message with suggestion to adjust search. Add this to any list that may exceed 5 items.

## ERROR & EDGE CASE HANDLING

**ErrorBoundary class component** — see `src/components/ErrorBoundary.tsx`.
React class component with `static getDerivedStateFromError` and `componentDidCatch`. Fallback UI shows error icon, "Something went wrong" message, and a "Refresh Page" button that calls `window.location.reload()`. Wraps the entire app in `App.tsx`.

**Retry on error pattern** — see any data-fetching page's error state.
Shows Lucide `AlertCircle` icon + error message text + "Try Again" button that re-triggers the fetch. Never show a blank screen on error.

**Offline handling** — see app-level or Layout-level implementation.
Listens for `window.addEventListener('online'/'offline')`. When offline, shows a yellow banner (`bg-yellow-100 text-yellow-800`) at the top of the viewport. Banner disappears automatically when back online.

**404 / Not Found handling** — two levels:
Route-level: catch-all `*` route renders `NotFoundPage` — see `src/pages/NotFoundPage.tsx` for layout with icon + "Page not found" + link to dashboard.
Data-level: when a fetch-by-ID returns null, show `EmptyState` with "Item not found" message + "Go Back" CTA. See Detail pages for this pattern.

## PAGINATION

**Pagination options** — each list must use one of these three patterns. See the list page that best matches your needs:
1. **Pagination** (10 per page): Previous/Next buttons + page indicator. Best for large stable datasets.
2. **Load More**: "Load More" button at bottom of list. Best for feeds.
3. **Infinite Scroll**: `IntersectionObserver` triggers next page load. Best for social/media feeds.
Pick one per list and implement it consistently.

## SHARED UI COMPONENTS

**Button component** — see `src/components/ui/Button.tsx`.
Props: `variant` (primary/secondary/danger), `loading` (shows Spinner + disables), `disabled`, plus standard button props. Loading state replaces text with Spinner and sets `disabled`. Match the variant class mappings exactly.

**Avatar component** — see `src/components/ui/Avatar.tsx`.
Shows `<img>` with `onError` handler that switches to initials fallback. Initials calculated from user name (first letter of first + last name). Size variants via props. Always provide both `src` and `name`.

**usePageTitle hook** — see `src/hooks/usePageTitle.ts`.
Calls `document.title = "Page Name - AppName"` on mount. Cleanup restores previous title. Every page must call this hook.

## REQUIRED UI COMPONENTS LIST

The compressed doc's File Structure section lists every required component. Before shipping, verify all of these exist and function: ErrorBoundary, Layout, Sidebar, MobileNav, Modal, ConfirmModal, Toast, Button, Avatar, Skeleton, EmptyState, Spinner, ThemeToggle, ProtectedRoute, AdminRoute.

## BANNED PATTERNS (with reasoning)

The compressed doc lists all banned patterns. Key enforcement details:
`alert()/confirm()/prompt()` — blocked because they freeze the UI thread and cannot be styled. Use Modal, ConfirmModal, Toast.
`console.log` for user feedback — invisible to users. Use Toast for all user-facing messages.
"Loading..." text — looks unfinished. Use Skeleton (for lists/content areas) or Spinner (inside buttons/inline).
Single component for view+edit — violates the Detail/Edit separation rule and makes state management fragile. Always separate.
Delete without ConfirmModal — destructive actions are irreversible. Always confirm.
Direct edit from list — users lose context. Always route through Detail View first.

## CONSOLE CLEAN RULES

Before shipping, verify: zero `console.log` statements (remove all), zero React warnings in dev console, zero TypeScript errors, zero ESLint warnings. The production build must have a completely clean console.

---

## WHEN ADDING NEW FEATURES

1. Read the closest existing feature's files first (all of them: page, component, hook, service, types)
2. Copy the pattern exactly — same file naming, same structure, same error handling
3. Add types to `types/index.ts`, API calls to `services/api.ts`, routes to `App.tsx`
4. Follow all 25 rules from the Critical Rules Checklist in the compressed doc
5. The built code IS your template — do not invent new patterns

## WHEN FIXING BUGS

1. Read the component AND its parent layout AND the service it calls
2. Match existing error handling and feedback patterns
3. Do not refactor surrounding code — fix the bug only
4. Verify the fix follows the 25 rules

## FULL RULES REFERENCE

All rules, banned patterns, feedback patterns, form requirements, polish requirements, responsive breakpoints, navigation flow, routing, design system tokens, and the 25-item critical checklist are in: **APP_BUILDER_STANDARDS_COMPRESSED.md**

That file is the law. This file tells you where the schematics live in the built codebase.
