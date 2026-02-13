# Mentor's Platform-Agnostic Build Standards

## Source
Distilled from mentor's App Builder Prompt Template. Firebase/Gemini-specific content removed.
This is the reference copy for incorporating into AutoForge's coding prompt and UI standards.

## Critical Rules (25 Rules)

### Technical (1-7)
1. NO database calls in components - use service layer only
2. NO unprotected routes for authenticated features
3. NO inline styles - Tailwind only
4. NO `any` types - define TypeScript interfaces
5. ALL database writes include createdAt/updatedAt timestamps
6. ALL user data scoped to the authenticated user
7. Wrap app in ErrorBoundary component

### UI/UX (8-25)
8. NO alert(), confirm(), prompt() - use Modal/ConfirmModal/Toast
9. ALL destructive actions require ConfirmModal
10. ALL async operations show loading state (Skeleton for lists, Spinner in buttons)
11. ALL empty lists use EmptyState component with icon and CTA
12. ALL success/error actions show Toast feedback
13. ALL saved items have Detail View (read-only) separate from Edit View
14. ALL forms validate before submission
15. ALL buttons show loading state during async actions
16. ALL avatars have fallback for failed images
17. ALL pages set document title via usePageTitle hook
18. ALL forms autofocus first input
19. ALL lists have search/filter when > 5 items expected
20. ALL error states have retry action
21. ALL dates formatted as relative time (not raw timestamps)
22. ALL long text truncated with ellipsis
23. ALL detail pages have back navigation
24. Use Lucide React for all icons
25. Zero console errors in production

## Design System

### Typography Scale
| Element | Size | Weight | Tailwind |
|---------|------|--------|----------|
| Page Title | 24px | Semi-bold | text-2xl font-semibold text-text-primary |
| Section Header | 18px | Semi-bold | text-lg font-semibold text-text-primary |
| Card Title | 16px | Medium | text-base font-medium text-text-primary |
| Body Text | 14px | Regular | text-sm text-text-secondary |
| Small/Meta | 12px | Regular | text-xs text-text-tertiary |

### Spacing
- Card padding: p-6 (24px)
- Section gaps: gap-6 (24px)
- Element gaps: gap-4 (16px)

### Component Patterns
- Cards: `bg-surface-base rounded-card border border-border-subtle shadow-card p-6`
- Primary Button: `bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors`
- Inputs: `bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand`

### Layout Structure
- Sidebar: 240px wide, bg-surface-base, border-r
- Header: Full width, bg-surface-base, border-b, h-16
- Main: flex-1, overflow-y-auto, p-8

### Responsive Breakpoints
- Mobile: < 640px (default, no prefix)
- Tablet: sm:640px+
- Desktop: lg:1024px+
- Touch targets: minimum 44x44px

## Required File Structure
```
src/
├── config/          # Backend configuration
├── contexts/        # Auth, Theme, Toast, feature contexts
├── hooks/           # useAuth, usePageTitle, custom hooks
├── components/
│   ├── ProtectedRoute.tsx
│   ├── AdminRoute.tsx
│   ├── ErrorBoundary.tsx
│   ├── Layout.tsx
│   ├── Sidebar.tsx
│   ├── MobileNav.tsx
│   └── ui/          # Modal, ConfirmModal, Toast, Button, Avatar, ThemeToggle, Card, Skeleton, EmptyState, Spinner
├── pages/           # LandingPage, LoginPage, Dashboard, Profile, NotFoundPage, [Item]Detail/Create/Edit
├── services/        # api.ts (ALL backend operations)
├── utils/           # formatDate.ts, pluralize.ts
└── types/           # index.ts (ALL TypeScript interfaces)
```

## Navigation Flow Pattern
```
LIST → click item → DETAIL → click edit → EDIT → save → DETAIL
LIST → click new  → CREATE → save → DETAIL
DETAIL → delete (with ConfirmModal) → LIST
```

## Key Patterns
- Dark-first styles use CSS variables for both modes
- Unsaved changes warning via beforeunload
- Network/offline detection with banner
- Pagination or Load More for all lists
- Search/filter when list > 5 items
- 404 handling at route and data level
