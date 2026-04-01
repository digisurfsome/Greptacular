# Trial Idea 1: Martin's Build PRD — Structural Technical Checklist

## Theory: The Structural-Mechanism Split

Building any app has two halves:

**The Structural Half** covers how the code is organized — file structure, component patterns, state management, auth setup, styling rules, what's banned. This is the same for EVERY app regardless of the idea. Martin's 1,500-line Build PRD covers this half. So do boilerplates. This checklist makes that knowledge systematic and matchable.

**The Mechanism Half** covers what the specific app DOES — its features, user flows, data transformations, integrations. This varies per app and is handled by the Mechanism Identification Framework (A-N categories) in a separate document (`mechanism-identification-framework.md`).

Together, the structural checklist + the mechanism framework = a complete app specification with zero gaps.

### How This Checklist Works

Each row captures one technical rule from Martin's narrative:
- **Martin Says** — his exact words (quoted)
- **Technical Spec** — precise, implementable translation
- **Boilerplate Match** — intentionally blank; filled during the boilerplate matching step

### The Preamble System

This checklist becomes a "preamble" injected before every pipeline stage. It tells the agent what's already decided so it doesn't waste time asking about structure. The agent only asks about mechanisms (what the app DOES).

### The Boilerplate Matching Step

A separate agent reads this checklist + a specific boilerplate and fills in the "Boilerplate Match" column:
- **MATCH** — Martin says X, boilerplate does X → keep as-is
- **REPLACE** — Martin says Firebase, boilerplate uses Supabase → replace with boilerplate specifics
- **ENHANCE** — Martin says "handle auth," boilerplate has full auth system → point to exact files
- **HANDLED** — Martin says "set up routing," boilerplate already has it → mark "don't touch"

Result: a boilerplate-specific preamble (e.g., `web-supabase.md`, `mobile-flutter.md`, `dual.md`, `no-boilerplate.md`).

### Alternative Approaches to Consider

1. **Flat merge** — Concatenate Martin's rules + boilerplate docs into one big context file. Simpler but agents may get confused by contradictions between Martin's Firebase rules and a Supabase boilerplate.

2. **Category-first** — Start from the 30-category master checklist and slot Martin's rules into matching categories. More complete coverage but loses Martin's opinionated coherence.

3. **Progressive disclosure** — Only inject the categories relevant to the current pipeline stage (e.g., Stage 6 only gets Styling/UI rules). Smaller context window but risks missing cross-cutting rules.

4. **LLM-scored importance** — Have an agent score each item 1-10 and only inject items above a threshold. Reduces noise but risks dropping something critical.

5. **Master merge with industry frameworks** — Combine Martin's checklist with arc42, 12-Factor App, and the 30-category master list into one unified structural checklist. Most complete but potentially overwhelming.

### What We're Asking Reviewers

Review this checklist and tell us:
- Is the categorization right?
- Is anything missing that the industry frameworks (arc42, 12-Factor, 30-category master list) would add?
- Which approach (above) makes the most sense for a 10-stage PRD pipeline?
- How should the preamble be structured for maximum determinism?
- Should Martin's Firebase-specific rules be kept or agnosticized for the generic version?

---

## The Checklist

**Total: ~192 rules across 18 categories + 43 banned patterns**

---
---

### Stack (Mandatory)

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | React 19 with TypeScript | "React 19 with TypeScript" | Use React 19.x with TypeScript strict mode enabled | _[to be filled]_ |
| 2 | Tailwind CSS only | "Tailwind CSS for all styling" | All styling via Tailwind utility classes; no CSS modules, no styled-components, no inline styles | _[to be filled]_ |
| 3 | Firebase Auth (Google only) | "Firebase Authentication (Google Sign-In only)" | Use Firebase Auth with `signInWithPopup` and `GoogleAuthProvider`; no email/password, no other OAuth providers | _[to be filled]_ |
| 4 | Firestore for database | "Cloud Firestore for database" | All persistent data in Cloud Firestore; no Realtime Database, no external DB | _[to be filled]_ |
| 5 | React Context for state | "React Context for auth state" | Auth state managed via React Context + `useContext`; feature state via additional contexts | _[to be filled]_ |
| 6 | No external state libraries | "NO external state libraries" | No Redux, Zustand, Jotai, MobX, or any third-party state management | _[to be filled]_ |
| 7 | No Docker | "NO Docker" | No Dockerfiles, no docker-compose, no containerization | _[to be filled]_ |
| 8 | No backend APIs | "NO backend APIs" | No Express, no FastAPI, no server-side code; Firebase/Firestore only | _[to be filled]_ |
| 9 | Lucide React for icons | "Use Lucide React for all icons" | All icons from `lucide-react` via importmap; standard size `w-5 h-5`; spinner uses `Loader2` with `animate-spin` | _[to be filled]_ |
| 10 | ESM via importmap | Locked importmap in index.html | All dependencies loaded via browser-native ES modules through `<script type="importmap">`; no bundler, no npm install | _[to be filled]_ |

---

### File Structure

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | One component per file | "One component per file" | Each `.tsx` file exports exactly one React component as default export | _[to be filled]_ |
| 2 | Feature folders for grouping | "Group related components in feature folders" | Related components go in `components/[FeatureName]/` directories | _[to be filled]_ |
| 3 | Interfaces in types/index.ts | "Create interfaces for all data types" | All TypeScript interfaces in `types/index.ts`; no inline type definitions | _[to be filled]_ |
| 4 | Custom hooks per feature | "Add custom hooks for reusable logic" | Extract shared stateful logic into `hooks/use[Feature].ts` files | _[to be filled]_ |
| 5 | Required directory structure | File tree showing src/ layout | `src/` with: `config/`, `contexts/`, `hooks/`, `components/ui/`, `pages/`, `services/`, `utils/`, `types/` | _[to be filled]_ |
| 6 | Config folder for Firebase | `config/firebase.ts` | Firebase configuration lives in `src/config/firebase.ts` only | _[to be filled]_ |
| 7 | Contexts folder | `contexts/AuthContext.tsx`, `ThemeContext.tsx`, `ToastContext.tsx` | All React Context providers in `src/contexts/`; add `[FeatureName]Context.tsx` as needed | _[to be filled]_ |
| 8 | Services folder for Firestore | `services/firestore.ts` | All Firestore CRUD operations in `src/services/firestore.ts`; components never import Firestore directly | _[to be filled]_ |
| 9 | Utils folder | `utils/formatDate.ts`, `utils/pluralize.ts` | Helper functions in `src/utils/`; at minimum `formatDate.ts` and `pluralize.ts` | _[to be filled]_ |
| 10 | Pages folder with naming convention | `pages/[Item]DetailPage.tsx`, `[Item]CreatePage.tsx`, `[Item]EditPage.tsx` | Page components follow `[Entity][Action]Page.tsx` naming; one page per route | _[to be filled]_ |
| 11 | UI components folder | `components/ui/` with Modal, Toast, etc. | All reusable UI primitives in `src/components/ui/` | _[to be filled]_ |

---

### Configuration (index.html)

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Importmap is locked | "IMPORTMAP IS LOCKED. DO NOT MODIFY" | Copy importmap exactly as provided; no version changes, no additions, no removals | _[to be filled]_ |
| 2 | No Firebase sub-imports | "DO NOT ADD firebase/app, firebase/auth, or firebase/firestore to the importmap" | Only `"firebase/"` with trailing slash; no individual Firebase package entries | _[to be filled]_ |
| 3 | Tailwind via CDN | `<script src="https://cdn.tailwindcss.com">` | Tailwind loaded via CDN script tag with inline `tailwind.config` | _[to be filled]_ |
| 4 | Inter font loaded | Google Fonts link for Inter | Load `Inter` with weights 400, 500, 600, 700 via Google Fonts CDN | _[to be filled]_ |
| 5 | CSS variables for dark mode | "Use `var(--color-*)` references so the theme toggle works" | Light mode values in `:root`; dark mode overrides in `.dark` class; reference via `var(--color-*)` | _[to be filled]_ |
| 6 | Dark mode via class strategy | `darkMode: 'class'` | Tailwind dark mode uses `class` strategy; `.dark` class on `<html>` element toggles dark mode | _[to be filled]_ |
| 7 | Color token system | Surface, text, border color tokens | Colors defined as semantic tokens: `surface-canvas/base/muted`, `text-primary/secondary/tertiary`, `border-subtle`, `brand/brand-dark` | _[to be filled]_ |
| 8 | Custom border radius | `borderRadius: { card: '12px' }` | Custom `rounded-card` utility set to 12px | _[to be filled]_ |
| 9 | Custom card shadow | `boxShadow: { card: '...' }` | Custom `shadow-card` utility with subtle dual-shadow | _[to be filled]_ |
| 10 | Gemini AI optional import | "Add this single line to the importmap" for @google/genai | If using Gemini AI, add `"@google/genai": "https://esm.sh/@google/genai"` — no version pin | _[to be filled]_ |

---

### Authentication Context

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | UserProfile interface with role | `interface UserProfile { uid, email, displayName, photoURL, role, createdAt, updatedAt }` | UserProfile stored in Firestore includes `role: 'user' \| 'pro' \| 'admin'` field | _[to be filled]_ |
| 2 | AuthContext provides full interface | `user`, `userProfile`, `loading`, `signInWithGoogle`, `logout`, `isAdmin`, `isPro` | AuthContext exposes Firebase User, Firestore UserProfile, loading state, auth functions, and role convenience booleans | _[to be filled]_ |
| 3 | Profile created on first login | `setDoc` on first sign-in | On first `onAuthStateChanged` where user exists but no Firestore profile, create profile with `role: 'user'` and `serverTimestamp()` | _[to be filled]_ |
| 4 | Default role is 'user' | "Default role - change via Firebase Console" | New profiles get `role: 'user'`; only changeable via Firebase Console (not through app UI) | _[to be filled]_ |
| 5 | Firebase import order critical | "CRITICAL: Import order matters - app must be initialized FIRST" | `initializeApp()` first, then `getAuth(app)` and `getFirestore(app)` | _[to be filled]_ |
| 6 | signInWithPopup for login | Code showing `signInWithPopup(auth, googleProvider)` | Google login uses popup flow, not redirect; catches errors and shows toast on failure | _[to be filled]_ |
| 7 | Loading state during auth check | `const [loading, setLoading] = useState(true)` | App shows loading state while `onAuthStateChanged` resolves; prevents flash of wrong content | _[to be filled]_ |

---

### Theme Context (Dark Mode)

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | localStorage persistence | Theme preference saved to localStorage | Read `localStorage.getItem('theme')` on mount; save on toggle | _[to be filled]_ |
| 2 | System preference fallback | Check `prefers-color-scheme: dark` | If no localStorage value, check `window.matchMedia('(prefers-color-scheme: dark)')` | _[to be filled]_ |
| 3 | Class on html element | `.dark` class toggled on `document.documentElement` | `document.documentElement.classList.add/remove('dark')` toggles dark mode globally | _[to be filled]_ |
| 4 | ThemeToggle component required | `ThemeToggle.tsx` in ui/ | Toggle button using `Sun`/`Moon` Lucide icons; shows opposite of current mode | _[to be filled]_ |

---

### Route Guards

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | ProtectedRoute for auth users | `ProtectedRoute.tsx` | Checks `user` from AuthContext; redirects to `/login` if not authenticated; shows spinner while loading | _[to be filled]_ |
| 2 | AdminRoute for admin only | `AdminRoute.tsx` | Extends ProtectedRoute; also checks `userProfile?.role === 'admin'`; redirects non-admins to dashboard | _[to be filled]_ |
| 3 | ProRoute for pro/admin | `ProRoute.tsx` (optional) | Checks role is `'pro'` or `'admin'`; redirects others to dashboard or upgrade page | _[to be filled]_ |
| 4 | Route wrapping order | "ProtectedRoute > Layout > Page" | Nesting: `<ProtectedRoute><Layout><PageComponent /></Layout></ProtectedRoute>` | _[to be filled]_ |
| 5 | Provider nesting order | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Outermost to innermost: ErrorBoundary > AuthProvider > ThemeProvider > ToastProvider > BrowserRouter > Routes | _[to be filled]_ |

---

### Firestore Data Structure

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | User data in subcollections | "users/{uid}/{collectionName}/{documentId}" | All user-owned data nested under user document; never in top-level collections | _[to be filled]_ |
| 2 | Helper for user collections | `getUserCollection(uid, collectionName)` | Utility function returns `collection(db, 'users', uid, collectionName)` | _[to be filled]_ |
| 3 | Timestamps on all writes | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every create includes both; every update includes `updatedAt` | _[to be filled]_ |
| 4 | Default sort newest first | "orderBy('createdAt', 'desc')" | All collection queries default to descending `createdAt` order | _[to be filled]_ |

---

### Firestore Service Layer

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | No Firestore in components | "NO Firestore calls in components - use firestore service only" | All CRUD through `services/firestore.ts`; components call service functions | _[to be filled]_ |
| 2 | CRUD helper functions | `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Four base functions wrapping Firestore operations with timestamp injection | _[to be filled]_ |
| 3 | Realtime subscription pattern | "return onSnapshot(q, ...)" | `onSnapshot` with ordered query; maps docs to `{ id: doc.id, ...doc.data() }`; returns unsubscribe function | _[to be filled]_ |
| 4 | Delete account function | `deleteUserAccount(uid, subcollections[])` | Iterates subcollection names, deletes all docs in each via `Promise.all`, then deletes parent user doc | _[to be filled]_ |

---

### Routing Structure

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | HashRouter for static hosting | Uses `HashRouter` or `BrowserRouter` | Router wraps all Routes; public routes (landing, login) outside ProtectedRoute | _[to be filled]_ |
| 2 | Public vs protected routes | Landing and Login are public; Dashboard, Profile, CRUD pages are protected | Public: `/`, `/login`. Protected: `/dashboard`, `/profile`, `/items/:id`, etc. | _[to be filled]_ |
| 3 | 404 catch-all | `<Route path="*" element={<NotFoundPage />} />` | Last route in Routes catches all unmatched paths | _[to be filled]_ |
| 4 | CRUD route pattern | Detail, Create, Edit routes per entity | `/items` (list), `/items/new` (create), `/items/:id` (detail), `/items/:id/edit` (edit) | _[to be filled]_ |
---

### Data/API Patterns

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete account removes subcollections | "Delete all documents in each subcollection" | `deleteUserAccount(uid, subcollections)` iterates subcollection names, calls `getDocs` then `deleteDoc` on every doc via `Promise.all`, then deletes the parent `users/{uid}` document. | _[to be filled]_ |
| 2 | Subcollection list is explicit | "List all subcollections your app uses" | Pass an explicit string array of subcollection names (e.g. `['items', 'settings']`) to the delete function -- no dynamic discovery. | _[to be filled]_ |
| 3 | Realtime subscription pattern | "For realtime updates ... return onSnapshot(q, ...)" | Use `onSnapshot` with a query ordered by `createdAt desc`; map snapshot docs to `{ id: doc.id, ...doc.data() }` and pass to callback. Return the unsubscribe function. | _[to be filled]_ |
| 4 | CRUD helper layer | Code block showing `addDocument`, `updateDocument`, `deleteDocument`, `getDocuments` | Wrap all Firestore operations in a `services/firestore.ts` helper module. Every write sets `updatedAt: serverTimestamp()`; creates also set `createdAt: serverTimestamp()`. | _[to be filled]_ |
| 5 | Documents always include timestamps | "createdAt: serverTimestamp(), updatedAt: serverTimestamp()" | Every Firestore document must have `createdAt` (set on create) and `updatedAt` (set on create and every update) using `serverTimestamp()`. | _[to be filled]_ |
| 6 | Default sort order | "orderBy('createdAt', 'desc')" | All collection queries default to `orderBy('createdAt', 'desc')` -- newest first. | _[to be filled]_ |
| 7 | List pagination is mandatory | "Lists MUST handle large amounts of data" | Every list view must implement one of: pagination (10-20 items per page), load-more button, or infinite scroll via Intersection Observer. Pick ONE and use it consistently. | _[to be filled]_ |
| 8 | Pagination controls pattern | "Show 10-20 items per page ... Pagination controls at bottom" | Use `ITEMS_PER_PAGE = 10` constant, `page` state starting at 1, Previous/Next buttons disabled at bounds, "Page X of Y" label centered between buttons. | _[to be filled]_ |
| 9 | Load-more shows remaining count | "Load More ({remaining} remaining)" | Load-more button must display how many items remain unloaded. Initial `limit` state of 10, increment by 10 on click. | _[to be filled]_ |

---

### Authentication/Security

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete account requires typed confirmation | "Type DELETE to confirm" | Delete account flow requires user to type the exact string `"DELETE"` into a text input. Submit button is `disabled` until `confirmText !== 'DELETE'`. | _[to be filled]_ |
| 2 | Delete button disabled during operation | "disabled={confirmText !== 'DELETE' \|\| isDeleting}" | Delete confirmation button must check both confirmation text match AND `isDeleting` state. Show `"Deleting..."` text while in progress. | _[to be filled]_ |
| 3 | Logout after account deletion | "await deleteUserAccount(user.uid, ...); await logout();" | After successful account deletion, immediately call `logout()` to clear the auth session before showing success toast. | _[to be filled]_ |
| 4 | Protected routes wrap layout | "ProtectedRoute > Layout > Page" | All authenticated pages must be wrapped as `<ProtectedRoute><Layout><Page /></Layout></ProtectedRoute>`. Public pages (landing, login) have no wrapper. | _[to be filled]_ |
| 5 | Auth/theme/toast providers wrap router | "AuthProvider > ThemeProvider > ToastProvider > BrowserRouter" | Provider nesting order (outermost to innermost): `AuthProvider` > `ThemeProvider` > `ToastProvider` > `BrowserRouter` > `Routes`. | _[to be filled]_ |
| 6 | Admin-only nav items are conditional | "isAdmin && <Link to='/admin'>Admin</Link>" | Sidebar navigation must conditionally render admin links based on an `isAdmin` flag. | _[to be filled]_ |

---

### Database/Storage

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | User data in subcollections | "getUserCollection(uid, collectionName)" | All user-owned data lives under `users/{uid}/{collectionName}/{docId}`. Use a helper that returns `collection(db, 'users', uid, collectionName)`. | _[to be filled]_ |
| 2 | Delete cascades to subcollections | "removes user profile and all subcollections" | Account deletion must delete all documents in every known subcollection BEFORE deleting the parent user profile document. | _[to be filled]_ |
| 3 | Batch deletes via Promise.all | "const deletePromises = snapshot.docs.map(doc => deleteDoc(doc.ref)); await Promise.all(deletePromises);" | Subcollection deletion fetches all docs, maps to `deleteDoc` promises, then awaits `Promise.all` for each subcollection sequentially. | _[to be filled]_ |

---

### Error Handling

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Delete failure keeps modal open | "catch (error) { showToast({ type: 'error', message: 'Failed to delete account' }); setIsDeleting(false); }" | On delete error: show error toast, reset `isDeleting` to false, do NOT close modal, do NOT navigate away. | _[to be filled]_ |
| 2 | Success feedback is toast + navigate | "Show success Toast ... Navigate to appropriate view" | Every successful mutation: show a success toast with descriptive message, then navigate to the next logical view. | _[to be filled]_ |
| 3 | Error feedback preserves form state | "Show error Toast with helpful message ... Stay on current view ... Keep form data intact" | On error: show error toast, remain on current view, do NOT clear or reset form data. | _[to be filled]_ |
| 4 | Delete flow is 6-step | "1. User clicks delete 2. ConfirmModal appears ... 3. User confirms 4. Show loading state on button 5. On success: Toast + redirect to List 6. On error: Toast + close modal" | Delete flow: click > ConfirmModal > confirm > button loading spinner + disabled > success toast + redirect to list view, OR error toast + close modal. | _[to be filled]_ |
| 5 | Loading states match content shape | "Lists: Show Skeleton cards (not spinner) ... Detail View: Show Skeleton matching content layout ... Buttons during action: Show spinner inside button, disable button" | Lists show skeleton cards, detail views show skeleton matching layout, action buttons show inline spinner and become disabled. Never use bare text "Loading...". | _[to be filled]_ |

---

### Performance

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Animations use short durations | "transition-opacity duration-200 ... transition-all duration-200 ease-out ... transition-transform duration-300 ease-out ... transition-all duration-150" | Modal backdrop: 200ms opacity. Modal content: 200ms ease-out. Toast: 300ms ease-out. Card hover: 200ms. Button press: 150ms. Never exceed 300ms for UI transitions. | _[to be filled]_ |
| 2 | Card hover uses translate not box-shadow alone | "hover:shadow-md hover:-translate-y-0.5" | Card hover effect combines `shadow-md` with `translateY(-0.5)` for a lift effect. Use `transition-all duration-200`. | _[to be filled]_ |
| 3 | Button press uses scale | "active:scale-[0.98]" | Buttons must have `active:scale-[0.98]` with `transition-all duration-150` for tactile feedback on click. | _[to be filled]_ |
| 4 | Choose one pagination strategy | "Choose ONE approach and implement it consistently" | Pick one list-handling strategy (pagination, load-more, or infinite scroll) and apply it to ALL list views in the app. Do not mix approaches. | _[to be filled]_ |

---

### UX Standards

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Six required UI components | "You MUST create and use these components. They are NOT optional: 1. Modal.tsx 2. ConfirmModal.tsx 3. Toast.tsx 4. ToastContext.tsx 5. Skeleton.tsx 6. EmptyState.tsx" | Create all six components: `Modal.tsx` (overlay + close + title + content slots), `ConfirmModal.tsx` (destructive action dialog), `Toast.tsx` (success/error/info slide-in), `ToastContext.tsx` (global `showToast(message, type)`), `Skeleton.tsx` (animated placeholder matching content shape), `EmptyState.tsx` (icon + message + CTA button). | _[to be filled]_ |
| 2 | Browser dialogs are banned | "These are strictly forbidden. Using them fails the build: alert(), confirm(), prompt(), console.log for user feedback" | Never use `alert()`, `confirm()`, `prompt()`, or `console.log` for user-facing feedback. Use Toast for messages, ConfirmModal for confirmations, Modal for prompts. | _[to be filled]_ |
| 3 | Text-only empty states are banned | "Text-only empty states ... needs icon + CTA" | Empty states must use the `EmptyState` component with an icon/illustration, descriptive message, AND a call-to-action button. Plain "No items" text is forbidden. | _[to be filled]_ |
| 4 | Loading text is banned | "Loading states that are just the word 'Loading...'" | Never display bare "Loading..." text. Use `Skeleton` components that match the shape of the content being loaded. | _[to be filled]_ |
| 5 | List-Detail-Create-Edit flow | "Any data the user creates/saves MUST follow this pattern: List View ... Detail View ... Create View ... Edit View" | All user data CRUD must implement four distinct views: List (cards/rows + "Create New"), Detail (read-only + Edit/Delete/Share), Create (form, save > Detail), Edit (pre-filled form, save > Detail, cancel > Detail not List). | _[to be filled]_ |
| 6 | No edit-first pattern | "Clicking saved item opens it in edit mode directly ... Using Create form as Edit form ... No way to view an item without editing it ... Single 'smart' component that handles both view and edit" | Items always open in read-only Detail view. Create and Edit are separate views/components. Never combine view+edit into one "smart" component. | _[to be filled]_ |
| 7 | Delete always requires confirmation | "Delete with no confirmation" listed as anti-pattern | Every delete action must go through `ConfirmModal` with explicit user confirmation. No silent deletes. | _[to be filled]_ |
| 8 | Every action needs user feedback | "Success/error with no feedback to user" listed as anti-pattern | Every mutation (create, update, delete) must show either a success or error toast. No silent operations. | _[to be filled]_ |
| 9 | Cancel-edit returns to detail | "Cancel returns to Detail View (not List)" | In Edit view, the Cancel button navigates back to the Detail view of the same item, not to the List view. | _[to be filled]_ |
| 10 | Cancel-create returns to list | "Cancel returns to List View" | In Create view, the Cancel button navigates back to the List view. | _[to be filled]_ |
| 11 | Never show raw timestamps | "Never show raw timestamps. Format dates for humans" | Create a `utils/formatDate.ts` helper. Display: "Just now" (<60s), "Xm ago" (<1h), "Xh ago" (<24h), "Yesterday" (24-48h), "Xd ago" (<7d), "Jan 15" (>7d same year), "Jan 15, 2024" (different year). | _[to be filled]_ |
| 12 | Text truncation is mandatory | "Long text MUST be truncated to prevent layout breaking" | Sidebar items: `truncate max-w-[200px]` (~30 chars). Card descriptions: `line-clamp-2`. Table cells: `truncate max-w-[150px]`. Always pair `truncate` with a `max-w-` value. | _[to be filled]_ |
| 13 | Back navigation on every sub-page | "Every detail/edit page MUST have back navigation" | Detail and Edit pages must have a back button at the top (`mb-6`) using either `navigate(-1)` or an explicit `<Link>` with left arrow icon and "Back" / "Back to [List]" text. | _[to be filled]_ |
| 14 | Five required animations | "Required animations: Modals: Fade in backdrop, scale up content. Toasts: Slide in from top-right. Cards: Subtle lift on hover. Buttons: Slight scale on press. Sidebar: Slide in on mobile" | Implement all five animation types: modal backdrop fade + content scale, toast slide-in from top-right, card hover lift, button press scale, sidebar mobile slide-in. | _[to be filled]_ |
| 15 | Danger zone styling | "mt-12 pt-8 border-t border-red-200 ... text-red-600 ... bg-red-600 hover:bg-red-700" | Account deletion section uses: `mt-12 pt-8` top spacing, `border-t border-red-200` separator, red-600 heading, red-600/700 button. Labeled "Danger Zone". | _[to be filled]_ |
| 16 | Modal overlay pattern | "fixed inset-0 bg-black/50 flex items-center justify-center z-50" | Modals use fixed full-screen overlay with `bg-black/50`, flex centering, `z-50`. Inner content: `bg-surface-base rounded-lg p-6 max-w-md w-full mx-4`. | _[to be filled]_ |
| 17 | Focus states on all interactive elements | "All interactive elements need visible focus ... focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2" | Every button, link, and input must have `focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2`. | _[to be filled]_ |
| 18 | Escape key closes modals | "Modals must handle Escape key" | Every modal must add a `keydown` event listener for `Escape` that calls `onClose()`. Clean up listener on unmount. | _[to be filled]_ |
| 19 | Focus trap in modals | "Focus trap in modals - focus first element, trap Tab key" | Modals must trap keyboard focus: focus the first interactive element on open, cycle Tab within the modal only. | _[to be filled]_ |
| 20 | Icon buttons need aria-label | "Icon-only buttons need aria-label" | Every button containing only an icon (no visible text) must have an `aria-label` attribute describing the action (e.g. "Close modal", "Delete item"). | _[to be filled]_ |
| 21 | Screen reader loading states | "Loading states ... <span className='sr-only'>Loading...</span>" | Add `<span className="sr-only">Loading...</span>` alongside visual loading indicators for screen readers. | _[to be filled]_ |
| 22 | Status updates use aria-live | "<div role='status' aria-live='polite'>{message}</div>" | Dynamic status messages must use `role="status"` and `aria-live="polite"` so screen readers announce changes. | _[to be filled]_ |
| 23 | 404 catch-all route | "<Route path='*' element={<NotFoundPage />} />" | The router must include a `path="*"` catch-all route rendering a `NotFoundPage` component. | _[to be filled]_ |

---

### Mobile/Responsive

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Mobile-first design | "Build mobile-first. Design for mobile, then scale up for larger screens." | Write default (unprefixed) CSS for mobile. Use `sm:` and `lg:` prefixes to add tablet/desktop overrides. | _[to be filled]_ |
| 2 | Three breakpoints | "Mobile: < 640px (default styles, no prefix) ... Tablet: sm:640px and up ... Desktop: lg:1024px and up" | Use Tailwind defaults: mobile (<640px, no prefix), tablet (sm:640px+), desktop (lg:1024px+). | _[to be filled]_ |
| 3 | Sidebar hidden on mobile | "Sidebar hidden by default on mobile ... Hamburger icon in header toggles sidebar" | Sidebar uses `hidden lg:block` (or equivalent). Mobile header has hamburger menu icon to toggle sidebar visibility. | _[to be filled]_ |
| 4 | Sidebar is overlay on mobile | "Sidebar slides in as overlay (not push) ... Clicking outside or nav item closes sidebar ... Add close button inside mobile sidebar" | Mobile sidebar slides over content (not push layout), closes on outside click or nav item click, has a close (X) button inside. | _[to be filled]_ |
| 5 | Cards stack vertically on mobile | "Cards: Full width, stack vertically (mobile) ... Grid 2-3 columns (desktop)" | Card grids: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`. | _[to be filled]_ |
| 6 | Forms full width on mobile | "Forms: Full width inputs (mobile) ... Max-width container (desktop)" | Form inputs: `w-full lg:max-w-md`. | _[to be filled]_ |
| 7 | Primary buttons full width on mobile | "Buttons: Full width for primary actions (mobile) ... Auto width (desktop)" | Primary action buttons: `w-full lg:w-auto`. | _[to be filled]_ |
| 8 | Modals nearly full screen on mobile | "Modals: Full screen or nearly full (mobile) ... Centered, max-w-md (desktop)" | Modals on mobile should be full-screen or near-full. Desktop: centered with `max-w-md`. | _[to be filled]_ |
| 9 | Minimum 16px text on mobile | "Text: Base size 16px minimum (mobile) ... Can be smaller (desktop)" | Body text must be at least 16px (Tailwind `text-base`) on mobile. Smaller sizes allowed only at `lg:` breakpoint and above. | _[to be filled]_ |
| 10 | 44px minimum touch targets | "Minimum 44px x 44px for all clickable elements on mobile ... Add padding to small icons/buttons to meet minimum ... Adequate spacing between touch targets" | All clickable elements must have a minimum touch area of 44x44px on mobile. Add padding to small icons/buttons. Ensure adequate spacing between adjacent targets. | _[to be filled]_ |
| 11 | Responsive class patterns | "hidden lg:block ... lg:hidden ... w-full lg:max-w-md ... p-4 lg:p-8" | Use `hidden lg:block` for desktop-only, `lg:hidden` for mobile-only, `w-full lg:max-w-md` for responsive width, `p-4 lg:p-8` for responsive padding. | _[to be filled]_ |
| 12 | Layout structure dimensions | "Sidebar: 240px wide, bg-surface-base, border-r ... Header: Full width, bg-surface-base, border-b, h-16 ... Main: flex-1, overflow-y-auto, p-8" | Sidebar: `w-60 bg-surface-base border-r border-border-subtle`. Header: full width, `bg-surface-base border-b h-16`. Main content: `flex-1 overflow-y-auto p-8`. | _[to be filled]_ |
| 13 | Sidebar has bottom help link | "Bottom section: help link (always visible) ... p-4 border-t border-border-subtle" | Sidebar must have a pinned bottom section with `p-4 border-t border-border-subtle` containing a Help & Support link (`mailto:` or equivalent) with a HelpCircle icon. | _[to be filled]_ |
| 14 | Padding scales with breakpoint | "p-4 lg:p-8" | Main content padding: `p-4` on mobile, `p-8` on desktop (lg:). | _[to be filled]_ |

---

### Design System

| # | Rule | Martin Says | Technical Spec | Boilerplate Match |
|---|------|-------------|----------------|-------------------|
| 1 | Typography scale | "Page Title: 24px Semi-bold ... Section Header: 18px Semi-bold ... Card Title: 16px Medium ... Body Text: 14px Regular ... Small/Meta: 12px Regular" | Page Title: `text-2xl font-semibold text-text-primary`. Section Header: `text-lg font-semibold text-text-primary`. Card Title: `text-base font-medium text-text-primary`. Body: `text-sm text-text-secondary`. Small/Meta: `text-xs text-text-tertiary`. | _[to be filled]_ |
| 2 | Spacing scale | "Card padding: p-6 (24px) ... Section gaps: gap-6 (24px) ... Element gaps: gap-4 (16px)" | Card internal padding: `p-6`. Between sections: `gap-6`. Between elements within a section: `gap-4`. | _[to be filled]_ |
| 3 | Card component class | "bg-surface-base rounded-card border border-border-subtle shadow-card p-6" | Standard card: `bg-surface-base rounded-card border border-border-subtle shadow-card p-6`. | _[to be filled]_ |
| 4 | Primary button class | "bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors" | Primary button: `bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors`. | _[to be filled]_ |
| 5 | Input field class | "bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand" | Text inputs: `bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand`. | _[to be filled]_ |
| 6 | Sidebar nav item classes | "space-y-2 ... text-sm text-text-secondary hover:text-text-primary" | Nav links: vertical stack with `space-y-2`, text style `text-sm text-text-secondary hover:text-text-primary`. | _[to be filled]_ |
| 7 | Sidebar recent items section | "mt-6 ... text-xs font-medium text-text-tertiary mb-2" | Sidebar optional items section: `mt-6` spacing, heading `text-xs font-medium text-text-tertiary mb-2`, labeled "Recent Items" or similar. | _[to be filled]_ |
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
