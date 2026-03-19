# MODULE 01: SCAFFOLD PROMPT

## The Foundation — New App From Zero

**What this does:** Creates a complete, production-ready project skeleton using Claude Code + Supabase + Vite + React + TypeScript + Tailwind CSS. This is your starting point for every single app.

**When to use:** Every time you start a new app. Before Auth, before UI, before anything.

---

## HOW TO USE THIS PROMPT

1. Open Claude Code in your terminal
2. Navigate to where you want the project: `cd ~/projects`
3. Copy everything below the **--- START PROMPT ---** line
4. Paste it into Claude Code
5. Fill in the [BRACKETS] before sending — there are only 3 things to fill in

---

## --- START PROMPT ---

## TASK: Scaffold a new application

Create a complete project from scratch. Follow every instruction exactly. Do not skip steps. Do not improvise the stack. Do not add libraries not listed here.

---

## SECTION 1: APP IDENTITY [FILL THESE IN]

**App Name:** [YOUR_APP_NAME]
**One-Line Description:** [What does this app do in one sentence?]
**App Slug:** [your-app-name] (lowercase, hyphens, used for folder name)

---

## SECTION 2: EXECUTION STEPS (DO THESE IN ORDER)

### STEP 1: Create the Vite Project

```bash
npm create vite@latest [your-app-name] -- --template react-ts
cd [your-app-name]
```

Do NOT use `--template react`. It MUST be `react-ts` for TypeScript.

### STEP 2: Install Core Dependencies

```bash
npm install @supabase/supabase-js react-router-dom lucide-react
```

That's it. Three dependencies. Do NOT install:
- State management libraries (no Redux, no Zustand, no Jotai)
- CSS frameworks besides Tailwind (no Chakra, no MUI, no Mantine)
- Form libraries (no Formik, no React Hook Form) — we use controlled components
- Animation libraries (no Framer Motion) — we use CSS transitions
- Date libraries (no date-fns, no dayjs) — we write a 15-line helper

### STEP 3: Install Tailwind CSS v4

```bash
npm install tailwindcss @tailwindcss/vite
```

Then configure Vite to use the Tailwind plugin:

**vite.config.ts:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})
```

**src/index.css** — Replace the entire contents with:
```css
@import "tailwindcss";

/* ============================================
   DESIGN TOKENS — LIGHT MODE (DEFAULT)
   ============================================ */

@theme {
  /* Brand Colors — REPLACE with your brand colors */
  --color-brand-light: #93c5fd;
  --color-brand: #3b82f6;
  --color-brand-dark: #1d4ed8;

  /* Surface Colors */
  --color-surface-canvas: #F9FAFB;
  --color-surface-base: #FFFFFF;
  --color-surface-muted: #F3F4F6;

  /* Text Colors */
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;

  /* Border Colors */
  --color-border-subtle: #E5E7EB;

  /* Semantic Colors */
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-info: #3B82F6;

  /* Typography */
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;

  /* Spacing & Radius */
  --radius-card: 12px;

  /* Shadows */
  --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

/* ============================================
   DARK MODE OVERRIDES
   ============================================ */

.dark {
  --color-surface-canvas: #0F172A;
  --color-surface-base: #1E293B;
  --color-surface-muted: #334155;
  --color-text-primary: #F1F5F9;
  --color-text-secondary: #94A3B8;
  --color-text-tertiary: #64748B;
  --color-border-subtle: #334155;
  --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.3);
}

/* ============================================
   BASE STYLES
   ============================================ */

body {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Smooth transitions when toggling dark mode */
* {
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
```

### STEP 4: Add Inter Font

**index.html** — Add inside `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Also update the `<title>` tag to: `[YOUR_APP_NAME]`

### STEP 5: Create the File Structure

Create ALL of these files. Empty files are fine — we fill them in subsequent modules. But the structure MUST exist now.

```
src/
├── App.tsx                        # Main app with routing (we build this below)
├── main.tsx                       # Entry point (Vite generates this)
├── index.css                      # Tailwind imports + tokens (done in Step 3)
├── config/
│   └── supabase.ts                # Supabase client configuration
├── contexts/
│   ├── AuthContext.tsx             # Auth state + user profile + role
│   ├── ThemeContext.tsx            # Dark mode state + toggle
│   └── ToastContext.tsx            # Toast notification state
├── hooks/
│   ├── useAuth.ts                 # Re-export from AuthContext (convenience)
│   └── usePageTitle.ts            # Dynamic document title
├── components/
│   ├── ProtectedRoute.tsx         # Route guard — any authenticated user
│   ├── AdminRoute.tsx             # Route guard — admin only
│   ├── ErrorBoundary.tsx          # Catches crashes, shows fallback UI
│   ├── Layout.tsx                 # Main layout — sidebar + header + content
│   ├── Sidebar.tsx                # Desktop sidebar navigation
│   ├── MobileNav.tsx              # Mobile header with hamburger toggle
│   └── ui/
│       ├── Modal.tsx              # Base modal (overlay, close, title, content)
│       ├── ConfirmModal.tsx       # "Are you sure?" for destructive actions
│       ├── Toast.tsx              # Slide-in notification component
│       ├── Button.tsx             # Button with loading state
│       ├── Avatar.tsx             # User avatar with initials fallback
│       ├── ThemeToggle.tsx        # Dark/light mode toggle
│       ├── Card.tsx               # Standard card wrapper
│       ├── Skeleton.tsx           # Animated loading placeholder
│       ├── EmptyState.tsx         # Empty list state with icon + CTA
│       └── Spinner.tsx            # Loading spinner
├── pages/
│   ├── LandingPage.tsx            # Public landing page
│   ├── LoginPage.tsx              # Login page
│   ├── Dashboard.tsx              # Main authenticated view
│   ├── Profile.tsx                # User profile + delete account
│   └── NotFoundPage.tsx           # 404 page
├── services/
│   └── database.ts                # All Supabase database operations
├── utils/
│   ├── formatDate.ts              # Relative time formatting
│   └── pluralize.ts              # "1 item" vs "2 items"
└── types/
    └── index.ts                   # ALL TypeScript interfaces
```

### STEP 6: Configure Supabase Client

**src/config/supabase.ts:**
```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from '../types/supabase'

// USER: Replace these with your Supabase project credentials
// Found at: https://supabase.com/dashboard → Project → Settings → API
const supabaseUrl = 'YOUR_SUPABASE_URL'
const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
```

**src/types/supabase.ts** — Create a placeholder that we'll generate properly later:
```typescript
// This file will be auto-generated by: npx supabase gen types typescript
// For now, use this placeholder so the app compiles
export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          email: string
          display_name: string | null
          avatar_url: string | null
          role: 'user' | 'pro' | 'admin'
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          display_name?: string | null
          avatar_url?: string | null
          role?: 'user' | 'pro' | 'admin'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          display_name?: string | null
          avatar_url?: string | null
          role?: 'user' | 'pro' | 'admin'
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: Record<string, never>
    Functions: Record<string, never>
    Enums: {
      user_role: 'user' | 'pro' | 'admin'
    }
  }
}
```

### STEP 7: Create Core Type Definitions

**src/types/index.ts:**
```typescript
// ============================================
// USER TYPES
// ============================================

export interface UserProfile {
  id: string
  email: string
  display_name: string | null
  avatar_url: string | null
  role: 'user' | 'pro' | 'admin'
  created_at: string
  updated_at: string
}

// ============================================
// UI TYPES
// ============================================

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  duration?: number
}

// ============================================
// APP-SPECIFIC TYPES — ADD YOUR ENTITIES HERE
// ============================================

// Example (replace with your actual data types):
// export interface Item {
//   id: string
//   user_id: string
//   title: string
//   description: string | null
//   created_at: string
//   updated_at: string
// }
```

### STEP 8: Create Utility Helpers

**src/utils/formatDate.ts:**
```typescript
/**
 * Formats a date string into human-readable relative time.
 * "Just now" → "5m ago" → "2h ago" → "Yesterday" → "3d ago" → "Jan 15" → "Jan 15, 2024"
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) return 'Just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 172800) return 'Yesterday'
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`

  const sameYear = date.getFullYear() === now.getFullYear()
  if (sameYear) {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Formats a date for display in detail views (more complete).
 * "January 15, 2024 at 3:45 PM"
 */
export function formatFullDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
```

**src/utils/pluralize.ts:**
```typescript
/**
 * Returns "1 item" or "5 items" — never "1 items".
 * Handles irregular plurals: pluralize(1, 'entry', 'entries')
 */
export function pluralize(count: number, singular: string, plural?: string): string {
  const form = count === 1 ? singular : (plural || `${singular}s`)
  return `${count} ${form}`
}
```

### STEP 9: Create the Page Title Hook

**src/hooks/usePageTitle.ts:**
```typescript
import { useEffect } from 'react'

const APP_NAME = '[YOUR_APP_NAME]'

/**
 * Updates the browser tab title. Every page MUST use this.
 * Usage: usePageTitle('Dashboard')  →  "Dashboard — AppName"
 */
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} — ${APP_NAME}` : APP_NAME
  }, [title])
}
```

### STEP 10: Create the Error Boundary

**src/components/ErrorBoundary.tsx:**
```typescript
import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
          <div className="text-center p-8">
            <h1 className="text-2xl font-semibold text-text-primary mb-2">
              Something went wrong
            </h1>
            <p className="text-text-secondary mb-6">
              Please refresh the page to try again.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-brand hover:bg-brand-dark text-white font-medium px-6 py-3 rounded-lg transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
```

### STEP 11: Create the 404 Page

**src/pages/NotFoundPage.tsx:**
```typescript
import { Link } from 'react-router-dom'
import { usePageTitle } from '../hooks/usePageTitle'

export default function NotFoundPage() {
  usePageTitle('Page Not Found')

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-surface-canvas text-center px-4">
      <h1 className="text-7xl font-bold text-text-tertiary">404</h1>
      <p className="text-xl text-text-secondary mt-4 mb-8">
        This page doesn't exist.
      </p>
      <Link
        to="/"
        className="text-brand hover:text-brand-dark font-medium transition-colors"
      >
        &larr; Back to Home
      </Link>
    </div>
  )
}
```

### STEP 12: Create the Minimal App Shell

**src/App.tsx:**
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import NotFoundPage from './pages/NotFoundPage'

/**
 * Minimal app shell. Auth, Theme, and Toast providers
 * get added by Module 02 (Auth) and Module 04 (UI Kit).
 *
 * Routes get added as you build pages.
 */
function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* PUBLIC ROUTES */}
          <Route path="/" element={<PlaceholderHome />} />

          {/* CATCH-ALL 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

/** Temporary landing page — replaced by Module 07 (Style & Theming) */
function PlaceholderHome() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-text-primary mb-2">
          [YOUR_APP_NAME]
        </h1>
        <p className="text-text-secondary">
          Scaffold complete. Ready for Auth (Module 02).
        </p>
      </div>
    </div>
  )
}

export default App
```

### STEP 13: Update main.tsx

**src/main.tsx** — Replace contents with:
```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

### STEP 14: Create the Favicon

Create a simple SVG favicon. Replace the letter and color with your brand:

**public/favicon.svg:**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#3b82f6"/>
  <text x="16" y="22" text-anchor="middle" font-family="system-ui" font-weight="bold" font-size="18" fill="#ffffff">A</text>
</svg>
```

Then update **index.html** `<head>` to include:
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

### STEP 15: Create .env.local (Git-Ignored)

**IMPORTANT:** Never commit Supabase credentials. Create `.env.local`:

```bash
# Supabase — get these from https://supabase.com/dashboard → Project → Settings → API
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

Then update **src/config/supabase.ts** to use env vars:
```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from '../types/supabase'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. ' +
    'Copy .env.example to .env.local and add your credentials.'
  )
}

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
```

Create **.env.example** (this one IS committed — it's the template):
```bash
# Copy this file to .env.local and fill in your values
# Get credentials from: https://supabase.com/dashboard → Project → Settings → API
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### STEP 16: Update .gitignore

Append to the existing `.gitignore`:
```
# Environment variables (credentials)
.env.local
.env.production.local

# Supabase
supabase/.temp/
```

### STEP 17: Verify the Build

Run these commands and fix any errors before proceeding:

```bash
npm run dev
```

Open the URL it shows (usually http://localhost:5173). You should see:
- "[YOUR_APP_NAME]" centered on screen
- "Scaffold complete. Ready for Auth (Module 02)."
- Clean console — zero errors, zero warnings

Then verify the production build:
```bash
npm run build
```

This must complete with zero TypeScript errors and zero warnings.

### STEP 18: Initial Git Commit

```bash
git init
git add -A
git commit -m "scaffold: [YOUR_APP_NAME] — Vite + React + TS + Tailwind + Supabase"
```

---

## SECTION 3: WHAT YOU NOW HAVE

After this module, your project has:

| Layer | Status | Details |
|-------|--------|---------|
| **Build system** | Done | Vite + React 19 + TypeScript |
| **Styling** | Done | Tailwind CSS v4 with design tokens + dark mode CSS vars |
| **Supabase client** | Done | Configured with env vars, type-safe |
| **Routing** | Done | React Router with 404 handling |
| **Error boundary** | Done | Catches crashes, shows recovery UI |
| **Type system** | Done | Base types + Supabase type placeholder |
| **Utilities** | Done | Date formatting + pluralization |
| **File structure** | Done | Every folder and file created |
| **Git** | Done | Clean initial commit |

## SECTION 4: WHAT'S NEXT

| Next Module | What It Adds |
|-------------|-------------|
| **02 — Auth** | Supabase auth, Google OAuth, AuthContext, protected routes, role-based access |
| **03 — Data Layer** | SQL migrations, RLS policies, database service functions |
| **04 — UI Kit** | Modal, Toast, Button, Avatar, Skeleton, EmptyState — every reusable component |

---

## SECTION 5: RULES — DO NOT VIOLATE

These rules apply to THIS scaffold and ALL subsequent modules:

### Stack Lock (NEVER change these)
- React 19 + TypeScript — no JavaScript files, ever
- Vite — no Next.js, no Remix, no CRA
- Tailwind CSS v4 — no other CSS frameworks, no CSS-in-JS
- Supabase — no Firebase, no Prisma, no raw SQL in components
- React Router — no TanStack Router, no file-based routing
- Lucide React — no other icon libraries
- No state management libraries — React Context only

### Dependency Lock (NEVER add these)
- NO Redux, Zustand, Jotai, Recoil, MobX
- NO Chakra UI, MUI, Mantine, Radix (we build our own UI kit)
- NO Formik, React Hook Form (controlled components)
- NO Framer Motion, React Spring (CSS transitions)
- NO Axios (use Supabase client or native fetch)
- NO date-fns, dayjs, moment (we wrote formatDate.ts)
- NO Docker (deployment is static hosting)
- NO backend API server (Supabase IS the backend)

### File Rules
- One component per file
- All types in `types/index.ts` (or `types/supabase.ts` for DB types)
- All database calls in `services/database.ts` — NEVER in components
- All Supabase config in `config/supabase.ts` — one client instance
- Group related components in feature folders under `components/`
- Custom hooks in `hooks/` — one hook per file

### Naming Conventions
- Files: PascalCase for components (`Dashboard.tsx`), camelCase for everything else (`formatDate.ts`)
- Components: PascalCase (`export default function Dashboard()`)
- Hooks: camelCase starting with `use` (`usePageTitle`)
- Types/Interfaces: PascalCase (`UserProfile`, `ToastMessage`)
- Constants: SCREAMING_SNAKE (`APP_NAME`, `ITEMS_PER_PAGE`)
- CSS: Tailwind classes only — no inline styles, no CSS modules

### Environment Variables
- All client-side env vars MUST start with `VITE_`
- NEVER commit `.env.local` — it holds credentials
- ALWAYS commit `.env.example` — it's the template
- Supabase credentials: `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

---

## --- END PROMPT ---
