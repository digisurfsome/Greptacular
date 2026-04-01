# Martin's Build PRD -- Technical Checklist (Section 4: Lines 1500-2227)

Extracted from `3-MARTINS-MAIN-BUILD-PRD.txt`, covering the final third of the document: form field states, additional standards, critical rules, and post-generation steps.

---

### Testing

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Console clean before deploy | "Production apps must have zero console errors/warnings" | Open browser DevTools Console, navigate through entire app, fix all red errors and yellow warnings until console is clean | _[to be filled]_ |
| 2 | No console.log statements | "No `console.log` statements (use proper error handling)" | Remove all `console.log` calls from production code; use Toast or structured error handling instead | _[to be filled]_ |
| 3 | No React key warnings | "No React key warnings (always use unique keys in lists)" | Every `.map()` rendering a list must provide a unique `key` prop; never use array index as key for dynamic lists | _[to be filled]_ |
| 4 | No missing dep warnings | "No missing dependency warnings (fix useEffect deps)" | All `useEffect`, `useMemo`, `useCallback` must have complete dependency arrays; fix or suppress with justification | _[to be filled]_ |
| 5 | No unused variables | "No unused variable warnings" | Remove all unused imports, variables, and parameters; zero warnings in linter output | _[to be filled]_ |
| 6 | No TypeScript errors | "No TypeScript errors" | `tsc --noEmit` must pass with zero errors; no `@ts-ignore` without documented reason | _[to be filled]_ |
| 7 | Full app navigation test | "Navigate through entire app" | Before deploying, manually click through every route, form, modal, and interactive element to verify no console output | _[to be filled]_ |

---

### Deployment/Hosting

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Firebase config placeholder | "Firebase config in firebase.ts with placeholder values" | `config/firebase.ts` ships with `YOUR_API_KEY`, `YOUR_PROJECT_ID`, etc. as string placeholders; never hardcode real credentials in source | _[to be filled]_ |
| 2 | Favicon required | "Every app needs a favicon. Add to index.html" | Create `public/favicon.svg` with app's first letter and brand color; link in `<head>` as `<link rel="icon" type="image/svg+xml" href="/favicon.svg" />` | _[to be filled]_ |
| 3 | Error boundary wraps app | "Wrap app in error boundary to prevent white screen of death" | `<ErrorBoundary>` component wraps `<AuthProvider>` at the top level in `App.tsx`; shows "Something went wrong" with Refresh button on crash | _[to be filled]_ |
| 4 | Importmap locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY." | Do not add, remove, or change version numbers in the `<script type="importmap">` block in `index.html`; the `firebase/` trailing slash handles all Firebase sub-imports | _[to be filled]_ |
| 5 | No Firebase sub-path imports in importmap | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap! The 'firebase/' trailing slash handles ALL Firebase imports. Adding specific paths will BREAK the app." | Only the `"firebase/"` entry with trailing slash is allowed; no `"firebase/app"`, `"firebase/auth"`, or `"firebase/firestore"` entries | _[to be filled]_ |

---

### Post-Generation Steps

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Replace Firebase config | "After generation, open `src/config/firebase.ts` and replace the placeholder values with your actual Firebase config from the Firebase Console." | Open `config/firebase.ts`, replace all `YOUR_*` placeholder strings with real values from Firebase Console > Project Settings > General > Your Apps > Config | _[to be filled]_ |
| 2 | Replace favicon letter | "Replace 'A' with app's first letter and fill color with brand color." | Edit `public/favicon.svg`: change the `<text>` content to the app's initial and the `<rect fill>` to the brand primary color | _[to be filled]_ |
| 3 | Replace app name in title hook | "const appName = 'AppName'; // Replace with your app name" | In `hooks/usePageTitle.ts`, change the `appName` constant to the actual application name | _[to be filled]_ |
| 4 | Set subcollection names for delete | "List all subcollections your app uses" | In the `DangerZone` component's `handleDeleteAccount`, update the array `['items', 'settings']` to list every Firestore subcollection used by the app | _[to be filled]_ |
| 5 | Set help email | "mailto:support@yourdomain.com" | In `Sidebar.tsx`, replace the placeholder email in the Help & Support link with the real support email address | _[to be filled]_ |

---

### Build Instructions

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Complete file structure | "Create the complete file structure" | Generate all files listed in the FILE STRUCTURE section; one component per file; group related components in feature folders | _[to be filled]_ |
| 2 | Follow exact patterns | "Implement all components following the exact patterns" | Use the provided code verbatim for: AuthContext, ThemeContext, ProtectedRoute, AdminRoute, ProRoute, ErrorBoundary, firestore service, and all UI components | _[to be filled]_ |
| 3 | Build Section 2 features | "Build the features described in Section 2" | Implement all core features from Section 2 using the CRUD view pattern (List > Detail > Create > Edit) | _[to be filled]_ |
| 4 | Apply Section 3 styling | "Apply the styling from Section 3 using the design system" | Use the design tokens from Section 3 mapped to the CSS variable system; respect typography scale, spacing, card styles, and color tokens | _[to be filled]_ |
| 5 | Auth and Firestore working | "Ensure all routes, auth flows, and Firestore operations work" | Google Sign-In flow, protected routes, Firestore CRUD through the service layer, and role-based access must all function end-to-end | _[to be filled]_ |
| 6 | Production ready | "Make it production-ready with proper error handling" | ErrorBoundary, Toast feedback on all actions, ConfirmModal on destructive actions, Skeleton loading states, offline handling, session expiry handling | _[to be filled]_ |
| 7 | Use Lucide React for icons | "Use Lucide React for all icons. Consistent style, tree-shakeable." | Import all icons from `lucide-react` via the importmap entry `"lucide-react": "https://esm.sh/lucide-react"`; standard size `w-5 h-5`; spinner uses `Loader2` with `animate-spin` | _[to be filled]_ |
| 8 | Dynamic page titles | "Update document title on each page" | Every page component calls `usePageTitle('Page Name')` hook which sets `document.title` to `"Page Name - AppName"` | _[to be filled]_ |
| 9 | Autofocus on forms | "First input should be focused when page/modal loads" | Use `autoFocus` attribute or `useRef` + `useEffect` to focus the first input field on mount; for modals, focus first input when `isOpen` becomes true | _[to be filled]_ |
| 10 | Pluralization helper | "Never show '1 items' - always handle plurals" | Create `utils/pluralize.ts` with `pluralize(count, singular, plural?)` function; use it everywhere counts are displayed | _[to be filled]_ |
| 11 | Search/filter for lists | "Any list that can grow needs search/filter" | Lists expected to exceed 5 items must include a search input filtering by title and description; show "No results for '...'" when filter yields empty | _[to be filled]_ |
| 12 | Retry on error states | "Error states should be actionable, not dead ends" | Every error display includes a "Try Again" button that re-invokes the failed operation; Toast errors may include an `action` with retry callback | _[to be filled]_ |
| 13 | Network/offline handling | "Handle Firebase/network errors gracefully" | Wrap Firestore calls to catch `unavailable` and `permission-denied` error codes with user-friendly messages; monitor `navigator.onLine` and show offline banner | _[to be filled]_ |
| 14 | Session expiry handling | "Firebase tokens expire. Handle gracefully" | Catch `unauthenticated` and `permission-denied` errors in Firestore calls; show "Session expired" Toast and call `logout()` to redirect to login | _[to be filled]_ |
| 15 | Loading button pattern | "Buttons during async actions must show loading state" | Button component accepts `loading` prop; when true, show `Loader2` spinner, display "Loading..." text, and set `disabled` | _[to be filled]_ |
| 16 | User avatar with fallback | "Google profile images can fail. Always have fallback" | Avatar component shows `<img>` with `onError` handler that hides the image and shows initials fallback; initials derived from name, max 2 characters | _[to be filled]_ |
| 17 | Form field states | "Forms need proper visual states" | Every form input handles 6 states: default (empty), focused (ring), filled, error (red border + message), disabled (opacity-50), helper text | _[to be filled]_ |
| 18 | Unsaved changes warning | "Warn users before losing form data" | Implement `useUnsavedChanges(hasChanges)` hook using `beforeunload` event; also intercept in-app navigation with a `ConfirmModal` | _[to be filled]_ |
| 19 | 404 / not found handling | "Handle invalid routes and missing data" | Add `<Route path="*" element={<NotFoundPage />} />` catch-all route; detail pages show `EmptyState` with "Item not found" when data is missing | _[to be filled]_ |
| 20 | Hover states on all interactives | "Every clickable element should visually respond to hover." | Cards: `hover:shadow-md hover:-translate-y-0.5`; Buttons: `hover:bg-brand-dark`; Links: `hover:underline`; Icon buttons: `hover:bg-surface-muted`; Table rows: `hover:bg-surface-muted`; all with `transition-*` | _[to be filled]_ |
| 21 | Date formatting | "Never show raw timestamps. Format dates for humans" | Create `utils/formatDate.ts` with `formatRelativeTime()` returning "Just now", "5m ago", "2h ago", "Yesterday", "3d ago", "Jan 15", or "Jan 15, 2024" | _[to be filled]_ |
| 22 | Text truncation | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: `truncate max-w-[200px]`; Card descriptions: `line-clamp-2`; Table cells: `truncate max-w-[150px]`; always set `max-w-` with `truncate` | _[to be filled]_ |
| 23 | Back navigation | "Every detail/edit page MUST have back navigation" | Place a back button at the top of every detail/edit page using `navigate(-1)` or explicit `<Link>` to the parent list route | _[to be filled]_ |
| 24 | Transitions and animations | "Add subtle animations for polish" | Required: modal fade/scale (200ms), toast slide-in (300ms), card hover lift (200ms), button press scale (150ms, `active:scale-[0.98]`), sidebar slide on mobile | _[to be filled]_ |
| 25 | Accessibility - focus states | "All interactive elements need visible focus" | Apply `focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2` to all buttons, inputs, and links | _[to be filled]_ |
| 26 | Accessibility - keyboard nav | "Modals must handle Escape key" | Add `keydown` listener for Escape to close modals; implement focus trap within modals (Tab cycles through modal elements only) | _[to be filled]_ |
| 27 | Accessibility - icon buttons | "Icon-only buttons need aria-label" | Every button with only an icon (no visible text) must have an `aria-label` describing the action, e.g. `aria-label="Close modal"` | _[to be filled]_ |
| 28 | Accessibility - screen reader | "Loading states" need sr-only text | Add `<span className="sr-only">Loading...</span>` for visual-only loading indicators; use `role="status" aria-live="polite"` for dynamic status text | _[to be filled]_ |
| 29 | Pagination or load-more | "Lists MUST handle large amounts of data" | Choose ONE pagination approach (pagination / load more / infinite scroll) and implement consistently across all list views; 10-20 items per page | _[to be filled]_ |
| 30 | CSS variables for dark mode | "DO NOT hardcode dark colors directly in Tailwind config. Use `var(--color-*)` references so the theme toggle works." | Define light mode values in `:root` and dark mode in `.dark` class; reference via `var(--color-*)` in Tailwind config | _[to be filled]_ |

---

### Miscellaneous Rules

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | No Firestore in components | "NO Firestore calls in components - use firestore service only" | All Firestore operations go through `services/firestore.ts`; components call service functions, never import `firebase/firestore` directly | _[to be filled]_ |
| 2 | No unprotected auth routes | "NO unprotected routes for authenticated features" | Every route that requires login must be wrapped in `<ProtectedRoute>`, `<AdminRoute>`, or `<ProRoute>` | _[to be filled]_ |
| 3 | No inline styles | "NO inline styles - Tailwind only" | Never use `style={{}}` prop; all styling via Tailwind CSS utility classes | _[to be filled]_ |
| 4 | No `any` types | "NO `any` types - define TypeScript interfaces" | Define TypeScript interfaces for all data shapes in `types/index.ts`; no `any` in function signatures, state, or props | _[to be filled]_ |
| 5 | Timestamps on all writes | "ALL Firestore writes include createdAt/updatedAt timestamps" | Every `addDoc` includes `createdAt: serverTimestamp(), updatedAt: serverTimestamp()`; every `updateDoc` includes `updatedAt: serverTimestamp()` | _[to be filled]_ |
| 6 | User data in subcollections | "ALL user data in subcollections under users/{uid}/" | Never store user data in top-level Firestore collections; always nest under `users/{uid}/{collectionName}/{docId}` | _[to be filled]_ |
| 7 | Detail view separate from edit | "ALL saved items have Detail View (read-only) separate from Edit View" | Detail page is read-only display; editing happens on a separate route (`/items/:id/edit`); never combine view and edit in one component | _[to be filled]_ |
| 8 | Validate before submit | "ALL forms validate before submission" | Client-side validation on all required fields before calling Firestore; show inline error messages per field | _[to be filled]_ |
| 9 | One component per file | "One component per file." | Each React component lives in its own `.tsx` file; no multi-component files | _[to be filled]_ |
| 10 | Feature folders for grouping | "Group related components in feature folders." | Related components go in `components/[FeatureName]/` directories; don't flatten everything into `components/` | _[to be filled]_ |
| 11 | Interfaces for all data types | "Create interfaces for all data types." | Every data shape used in Firestore, props, or state has a corresponding TypeScript interface in `types/index.ts` | _[to be filled]_ |
| 12 | Custom hooks for reusable logic | "Add custom hooks for reusable logic." | Extract shared stateful logic into `hooks/use[Feature].ts` files; components should be thin wrappers over hooks | _[to be filled]_ |
| 13 | Gemini importmap rule | "DO NOT pin a version number. Let esm.sh resolve the latest compatible version." | When adding `@google/genai` to the importmap, use `"https://esm.sh/@google/genai"` with no version pinned | _[to be filled]_ |
| 14 | Mobile-first responsive | "Build mobile-first. Design for mobile, then scale up for larger screens." | Default (unprefixed) styles target mobile; use `sm:`, `lg:` breakpoint prefixes to add tablet/desktop overrides | _[to be filled]_ |
| 15 | Touch targets 44px minimum | "Minimum 44px x 44px for all clickable elements on mobile" | Add padding to small icons/buttons to meet 44px minimum tap target; ensure adequate spacing between adjacent touch targets | _[to be filled]_ |
| 16 | Firebase init order | "CRITICAL: Import order matters - app must be initialized FIRST" | In `firebase.ts`: call `initializeApp(firebaseConfig)` first, then `getAuth(app)` and `getFirestore(app)` after | _[to be filled]_ |
| 17 | Role only editable via console | "role only editable via Firebase Console" | Firestore security rules enforce `request.resource.data.role == resource.data.role` on user updates; users cannot change their own role | _[to be filled]_ |
| 18 | Default role is 'user' | "Default role - change via Firebase Console" | New user profiles are created with `role: 'user'`; Firestore rules enforce `request.resource.data.role == 'user'` on create | _[to be filled]_ |

---

### Complete Banned Patterns

Every prohibition Martin states across the entire document, collected into one list:

1. No `alert()` -- use Toast for messages
2. No `confirm()` -- use ConfirmModal for confirmations
3. No `prompt()` -- use a proper form Modal
4. No `console.log` for user feedback -- use Toast
5. No text-only empty states -- use EmptyState component with icon and CTA
6. No browser default dialogs of any kind
7. No external state libraries (Redux, Zustand, etc.) -- React Context only
8. No Docker
9. No backend APIs (Firebase/Firestore only)
10. No inline styles -- Tailwind only
11. No `any` types -- define TypeScript interfaces
12. No Firestore calls in components -- use firestore service only
13. No unprotected routes for authenticated features
14. No hardcoded dark colors in Tailwind config -- use `var(--color-*)` references
15. No modifying the importmap (locked, copy exactly as shown)
16. No adding `firebase/app`, `firebase/auth`, or `firebase/firestore` to the importmap individually
17. No pinning version numbers for `@google/genai` in the importmap
18. No clicking a saved item to open it directly in edit mode
19. No using the Create form as the Edit form by pre-loading data
20. No "view-only impossible" pattern (must be able to view without editing)
21. No single "smart" component that handles both view and edit
22. No delete without confirmation (ConfirmModal required)
23. No success/error actions without feedback to user (Toast required)
24. No empty lists with just "No items" text (needs icon + CTA via EmptyState)
25. No loading states that are just the word "Loading..." (use Skeleton or spinner)
26. No raw timestamps displayed to users (use relative time formatting)
27. No untruncated long text (use `truncate` or `line-clamp-*`)
28. No detail/edit pages without back navigation
29. No React key warnings in console
30. No missing useEffect dependency warnings
31. No unused variable warnings
32. No TypeScript errors in production
33. No Firestore writes without `createdAt`/`updatedAt` timestamps
34. No user data stored in top-level Firestore collections (must be subcollections under `users/{uid}/`)
35. No forms without validation before submission
36. No buttons without loading state during async actions
37. No avatars without fallback for failed images
38. No pages without dynamic document title (usePageTitle hook)
39. No forms without autofocus on first input
40. No growable lists without search/filter (when >5 items expected)
41. No error states without retry action
42. No icons from libraries other than Lucide React
43. No console errors/warnings in production
