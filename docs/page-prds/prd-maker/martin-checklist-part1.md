# Martin's Build PRD — Technical Checklist (Section 4: Lines 104-800)

Extracted from `3-MARTINS-MAIN-BUILD-PRD.txt`, lines 104-800. Covers the core stack, file structure, configuration, auth context, theme context, and route guards.

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
