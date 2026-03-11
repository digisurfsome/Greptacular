# App Builder Standards (Compressed)
# ~350 lines — keeps all rules, drops code examples the AI already knows how to write

## STACK (MANDATORY)
- React 19 with TypeScript (strict mode)
- Tailwind CSS for ALL styling (no inline styles)
- React Router for routing
- React Context for state (NO Redux, NO external state libraries)
- Lucide React for ALL icons
- Authentication with role-based access control (user, pro, admin)
- Database/persistence layer for all user data

## FILE STRUCTURE
```
src/
├── App.tsx                    # Router + context providers
├── main.tsx                   # Entry point
├── index.css                  # Tailwind imports + CSS variables for theming
├── config/                    # Backend configuration
├── contexts/
│   ├── AuthContext.tsx         # Auth state + UserProfile with role
│   ├── ThemeContext.tsx        # Dark/light toggle, persists to localStorage, respects prefers-color-scheme
│   ├── ToastContext.tsx        # Global showToast(message, type) function
│   └── [Feature]Context.tsx    # One context per complex feature
├── hooks/
│   ├── useAuth.ts
│   ├── usePageTitle.ts         # Sets document.title on every page
│   └── use[Feature].ts
├── components/
│   ├── ProtectedRoute.tsx      # Redirect to /login if not authenticated
│   ├── AdminRoute.tsx          # Redirect to /dashboard if not admin
│   ├── ErrorBoundary.tsx       # Class component, catches crashes, shows refresh button
│   ├── Layout.tsx              # Sidebar + header + main content area
│   ├── Sidebar.tsx             # 240px, nav links, help/support link at bottom
│   ├── MobileNav.tsx           # Hamburger toggle, sidebar slides in as overlay
│   ├── ui/
│   │   ├── Modal.tsx           # Overlay + close button + title + content slots
│   │   ├── ConfirmModal.tsx    # "Are you sure?" for destructive actions
│   │   ├── Toast.tsx           # Slide-in notification (success/error/info)
│   │   ├── Button.tsx          # primary/secondary/danger variants + loading state with spinner
│   │   ├── Avatar.tsx          # Image with initials fallback on error
│   │   ├── ThemeToggle.tsx     # Sun/Moon icon toggle
│   │   ├── Card.tsx            # Standard card wrapper
│   │   ├── Skeleton.tsx        # Animated loading placeholders matching content shape
│   │   ├── EmptyState.tsx      # Icon + message + CTA button
│   │   └── Spinner.tsx
│   └── [Feature]/              # Group components by feature
├── pages/
│   ├── LandingPage.tsx         # Public
│   ├── LoginPage.tsx
│   ├── Dashboard.tsx           # Main list view
│   ├── Profile.tsx             # User settings + danger zone (delete account)
│   ├── NotFoundPage.tsx        # 404 with link back to dashboard
│   ├── [Item]DetailPage.tsx    # Read-only view of single item
│   ├── [Item]CreatePage.tsx    # Create form
│   └── [Item]EditPage.tsx      # Edit form (pre-filled)
├── services/
│   └── api.ts                  # ALL database operations (no DB calls in components)
├── utils/
│   ├── formatDate.ts           # Relative time: "Just now", "5m ago", "2h ago", "Yesterday", "Jan 15"
│   └── pluralize.ts            # "1 item" vs "5 items"
└── types/
    └── index.ts                # ALL TypeScript interfaces
```

One component per file. No `any` types. All data writes include createdAt/updatedAt.

## DARK MODE THEMING
- Define CSS variables in :root (light) and .dark (dark)
- Reference variables in Tailwind config via var(--color-*)
- NEVER hardcode hex colors in Tailwind config
- ThemeContext reads localStorage + prefers-color-scheme, toggles .dark class on documentElement

## DESIGN SYSTEM
| Element | Classes |
|---|---|
| Page Title | text-2xl font-semibold text-text-primary |
| Section Header | text-lg font-semibold text-text-primary |
| Card Title | text-base font-medium text-text-primary |
| Body Text | text-sm text-text-secondary |
| Small/Meta | text-xs text-text-tertiary |
| Card | bg-surface-base rounded-card border border-border-subtle shadow-card p-6 |
| Primary Button | bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg |
| Input | bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg focus:ring-2 focus:ring-brand |
| Spacing | Card padding: p-6. Section gaps: gap-6. Element gaps: gap-4 |

Layout: Sidebar 240px (bg-surface-base border-r) | Header full-width h-16 border-b | Main flex-1 overflow-y-auto p-8

## RESPONSIVE DESIGN (MOBILE-FIRST)
- Mobile (<640px): Sidebar hidden behind hamburger, cards stack vertically, primary buttons full-width, modals nearly full-screen
- Tablet (sm:640px+): 2-column card grid
- Desktop (lg:1024px+): Sidebar always visible, 3-column card grid, modals centered max-w-md
- Minimum touch target: 44x44px on mobile
- Sidebar on mobile: slides in as overlay (not push), closes on nav click or outside click

## NAVIGATION FLOW (MANDATORY)
Every type of user-created data MUST have these four views:
1. **List View** — card grid/rows, "Create New" button, clicking item goes to Detail
2. **Detail View** — read-only display, action buttons (Edit, Delete, Share)
3. **Create View** — form, save → Detail View, cancel → List View
4. **Edit View** — pre-filled form, save → Detail View, cancel → Detail View

```
List → (click item) → Detail → (click Edit) → Edit → (save) → Detail
List → (click New) → Create → (save) → Detail
Detail → (click Delete) → ConfirmModal → (confirm) → List
```

## ROUTING
```
Public:  /  (landing)  |  /login
Protected:  /dashboard  |  /profile  |  /items/:id  |  /items/new  |  /items/:id/edit
Admin:  /admin/*
Catch-all:  * → NotFoundPage
```
All protected routes wrapped in ProtectedRoute. Admin routes wrapped in AdminRoute. Layout wraps all authenticated pages.

## BANNED — DO NOT USE
- ❌ alert(), confirm(), prompt() → use Toast, ConfirmModal, Modal
- ❌ console.log for user feedback → use Toast
- ❌ Text-only empty states → use EmptyState with icon + CTA
- ❌ Raw timestamps → use formatDate (relative time)
- ❌ Inline styles → Tailwind only
- ❌ `any` type → define interfaces
- ❌ DB calls in components → use services/api.ts
- ❌ Clicking item opens edit mode directly → must go to Detail View first
- ❌ Single component for both view and edit
- ❌ Delete without ConfirmModal
- ❌ Success/error without Toast feedback
- ❌ "Loading..." text → use Skeleton for lists, spinner in buttons
- ❌ "No items" text without icon and CTA button

## FEEDBACK PATTERNS
- **Success**: Toast + navigate to appropriate view
- **Error**: Toast + stay on current view + keep form data
- **Delete**: ConfirmModal → loading state on button → success Toast + redirect to List | error Toast + close modal
- **Loading lists**: Skeleton cards (not spinner)
- **Loading detail**: Skeleton matching content layout
- **Loading button**: Spinner inside button + disable button + "Loading..." text

## FORM REQUIREMENTS
- Validate before submission
- Autofocus first input
- Show error state per field (red border + error message below)
- Show helper text when no error
- Disabled state during submission (opacity-50, cursor-not-allowed)
- Unsaved changes warning (beforeunload event)

## POLISH REQUIREMENTS
- **Dates**: Relative time only ("Just now", "5m ago", "2h ago", "Yesterday", "3d ago", "Jan 15")
- **Truncation**: Sidebar items truncate, card descriptions line-clamp-2, table cells truncate. Always set max-w.
- **Back navigation**: Every detail/edit page has ArrowLeft + "Back" button at top
- **Hover states**: Cards lift (hover:shadow-md hover:-translate-y-0.5), buttons darken, links underline, icon buttons get bg, table rows highlight
- **Animations**: Modal fade+scale, Toast slide-in, card hover lift, button press scale(0.98), sidebar slide on mobile
- **Focus states**: focus:ring-2 focus:ring-brand focus:ring-offset-2 on all interactive elements
- **Keyboard**: Escape closes modals. Icon buttons have aria-label. Status messages have role="status" aria-live="polite"
- **Search**: Add search bar when list may have >5 items. Filter across title + description. Show "No results" message.
- **Pagination**: Choose one — pagination (10/page), load more, or infinite scroll. Required for any list.
- **Retry on error**: Show error icon + message + "Try Again" button
- **Offline handling**: Listen for online/offline events, show yellow banner when offline
- **404 handling**: Route-level (NotFoundPage) + data-level (EmptyState with "Item not found")
- **Page titles**: Every page calls usePageTitle("Page Name") → "Page Name - AppName"
- **Pluralization**: Use pluralize helper ("1 item" vs "5 items")
- **Console clean**: Zero console.log, zero React warnings, zero TS errors in production
- **Avatar fallback**: Show initials when image fails to load
- **Conditional UI**: Show/hide features based on role (isAdmin, isPro)

## CRITICAL RULES CHECKLIST
1. No database calls in components — services only
2. No unprotected routes for authenticated features
3. No inline styles — Tailwind only
4. No `any` types — define interfaces for everything
5. All writes include createdAt/updatedAt
6. All user data scoped to authenticated user
7. App wrapped in ErrorBoundary
8. No alert/confirm/prompt — Modal/ConfirmModal/Toast only
9. All destructive actions require ConfirmModal
10. All async operations show loading state
11. All empty lists use EmptyState with icon and CTA
12. All success/error shows Toast
13. All saved items have separate Detail View and Edit View
14. All forms validate before submission
15. All buttons show loading during async
16. All avatars have fallback
17. All pages set document title
18. All forms autofocus first input
19. All lists have search/filter when >5 items expected
20. All error states have retry
21. All dates as relative time
22. All long text truncated
23. All detail pages have back navigation
24. Lucide React for all icons
25. Zero console errors in production
