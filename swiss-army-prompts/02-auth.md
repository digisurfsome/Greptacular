# MODULE 02: AUTH PROMPT

## Supabase Authentication — Google OAuth + Roles + Protected Routes

**What this does:** Adds complete authentication to your scaffolded app. Google sign-in, user profiles with roles (user/pro/admin), protected routes, and session management. After this module, your app has login/logout, route protection, and role-based access control.

**Prerequisite:** Module 01 (Scaffold) must be complete.

**Supabase setup required before running this prompt:**
1. Go to https://supabase.com/dashboard → your project → Authentication → Providers
2. Enable Google provider
3. Add your Google OAuth credentials (from Google Cloud Console)
4. Your `.env.local` must have `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

---

## --- START PROMPT ---

## TASK: Add Supabase Authentication

Add complete authentication to this existing Vite + React + TypeScript + Supabase app. Follow every instruction exactly. Do not skip steps.

Read the existing files first: `src/config/supabase.ts`, `src/App.tsx`, `src/types/index.ts`, and `src/index.css`. Understand the existing structure before making changes.

---

## STEP 1: Create the Profiles Table in Supabase

Run this SQL in the Supabase SQL Editor (Dashboard → SQL Editor → New Query):

**IMPORTANT: Print this SQL for me to copy — do NOT try to run it yourself. You cannot connect to Supabase directly.**

```sql
-- ============================================
-- PROFILES TABLE
-- Stores user metadata + role
-- Auto-created on first sign-in via trigger
-- ============================================

-- Create the role enum
CREATE TYPE public.user_role AS ENUM ('user', 'pro', 'admin');

-- Create the profiles table
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  role public.user_role NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can read own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

-- Policy: Users can update their own profile (but NOT the role field)
CREATE POLICY "Users can update own profile except role"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (
    auth.uid() = id
    AND role = (SELECT role FROM public.profiles WHERE id = auth.uid())
  );

-- Policy: Allow insert during sign-up (trigger or first login)
CREATE POLICY "Users can insert own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id AND role = 'user');

-- Auto-create profile on sign-up via trigger
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, display_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', NULL)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger: fire on every new auth.users row
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
```

**What this does vs. Firebase:**
| Firebase Pattern | Supabase Equivalent |
|---|---|
| `onAuthStateChanged` creates user doc | Trigger auto-creates profile row |
| Firestore security rules block role changes | RLS policy `WITH CHECK` prevents role changes |
| `users/{uid}` document | `profiles` table, `id` = auth user UUID |
| `serverTimestamp()` | `DEFAULT now()` + `update_updated_at()` trigger |
| Role changes via Firebase Console | Role changes via Supabase Dashboard SQL or Table Editor |

---

## STEP 2: Create AuthContext

**src/contexts/AuthContext.tsx:**
```typescript
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import type { User, Session } from '@supabase/supabase-js'
import { supabase } from '../config/supabase'
import type { UserProfile } from '../types'

interface AuthContextType {
  /** Supabase auth user (null if signed out) */
  user: User | null
  /** Profile from the profiles table (null if signed out or loading) */
  profile: UserProfile | null
  /** True while checking initial session */
  loading: boolean
  /** Sign in with Google OAuth popup/redirect */
  signInWithGoogle: () => Promise<void>
  /** Sign out and clear state */
  signOut: () => Promise<void>
  /** Convenience: profile.role === 'admin' */
  isAdmin: boolean
  /** Convenience: profile.role === 'pro' || 'admin' */
  isPro: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch the user's profile from the profiles table
  async function fetchProfile(userId: string) {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single()

    if (error) {
      console.error('Failed to fetch profile:', error.message)
      return null
    }
    return data as UserProfile
  }

  useEffect(() => {
    // 1. Check for existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setUser(session.user)
        fetchProfile(session.user.id).then((p) => {
          setProfile(p)
          setLoading(false)
        })
      } else {
        setLoading(false)
      }
    })

    // 2. Listen for auth state changes (sign in, sign out, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        setUser(session.user)
        // Small delay to allow the trigger to create the profile
        // (only needed on very first sign-in)
        const p = await fetchProfile(session.user.id)
        if (!p) {
          // Trigger hasn't fired yet — wait briefly and retry
          await new Promise((r) => setTimeout(r, 1000))
          const retried = await fetchProfile(session.user.id)
          setProfile(retried)
        } else {
          setProfile(p)
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null)
        setProfile(null)
      } else if (event === 'TOKEN_REFRESHED' && session?.user) {
        setUser(session.user)
        // Profile doesn't change on token refresh, but re-fetch to be safe
        const p = await fetchProfile(session.user.id)
        setProfile(p)
      }
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
      },
    })
    if (error) throw error
  }

  const handleSignOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
    setUser(null)
    setProfile(null)
  }

  const isAdmin = profile?.role === 'admin'
  const isPro = profile?.role === 'pro' || profile?.role === 'admin'

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        signInWithGoogle,
        signOut: handleSignOut,
        isAdmin,
        isPro,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

---

## STEP 3: Create ThemeContext

**src/contexts/ThemeContext.tsx:**
```typescript
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme') as Theme | null
      if (stored) return stored
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark'
    }
    return 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => setThemeState((t) => (t === 'light' ? 'dark' : 'light'))
  const setTheme = (t: Theme) => setThemeState(t)

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
```

---

## STEP 4: Create ToastContext (Minimal — Full component in Module 04)

**src/contexts/ToastContext.tsx:**
```typescript
import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react'
import type { ToastMessage } from '../types'

interface ToastContextType {
  toasts: ToastMessage[]
  showToast: (toast: Omit<ToastMessage, 'id'>) => void
  dismissToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const showToast = useCallback((toast: Omit<ToastMessage, 'id'>) => {
    const id = crypto.randomUUID()
    const duration = toast.duration ?? 4000

    setToasts((prev) => [...prev, { ...toast, id }])

    // Auto-dismiss
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, duration)
  }, [])

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
      {/* Toast renderer — Module 04 replaces this with the full Toast component */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium animate-slide-in ${
              toast.type === 'success' ? 'bg-green-600' :
              toast.type === 'error' ? 'bg-red-600' :
              toast.type === 'warning' ? 'bg-yellow-600' :
              'bg-blue-600'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used within ToastProvider')
  return context
}
```

Add the slide-in animation to **src/index.css** (inside the file, after the dark mode block):
```css
/* ============================================
   ANIMATIONS
   ============================================ */

@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
```

---

## STEP 5: Create Route Guards

**src/components/ProtectedRoute.tsx:**
```typescript
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

/**
 * Wraps any route that requires authentication.
 * Redirects to /login if not signed in.
 */
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
        <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}
```

**src/components/AdminRoute.tsx:**
```typescript
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

/**
 * Wraps admin-only routes.
 * Redirects non-admins to /dashboard.
 */
export default function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading, isAdmin } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
        <div className="w-8 h-8 border-4 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  if (!isAdmin) return <Navigate to="/dashboard" replace />

  return <>{children}</>
}
```

---

## STEP 6: Create the Login Page

**src/pages/LoginPage.tsx:**
```typescript
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { usePageTitle } from '../hooks/usePageTitle'
import { useEffect, useState } from 'react'

export default function LoginPage() {
  usePageTitle('Sign In')
  const { user, signInWithGoogle, loading } = useAuth()
  const navigate = useNavigate()
  const [isSigningIn, setIsSigningIn] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // If already signed in, redirect to dashboard
  useEffect(() => {
    if (user && !loading) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, loading, navigate])

  const handleGoogleSignIn = async () => {
    setIsSigningIn(true)
    setError(null)
    try {
      await signInWithGoogle()
      // OAuth redirects the page — no need to navigate manually
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Sign-in failed. Please try again.'
      setError(message)
      setIsSigningIn(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-canvas px-4">
      <div className="w-full max-w-sm">
        <div className="bg-surface-base rounded-xl border border-border-subtle shadow-card p-8">
          <h1 className="text-2xl font-semibold text-text-primary text-center mb-2">
            Welcome Back
          </h1>
          <p className="text-text-secondary text-center mb-8">
            Sign in to continue
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleGoogleSignIn}
            disabled={isSigningIn}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg border border-border-subtle bg-surface-base hover:bg-surface-muted transition-colors font-medium text-text-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSigningIn ? (
              <div className="w-5 h-5 border-2 border-text-tertiary border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            )}
            {isSigningIn ? 'Signing in...' : 'Continue with Google'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

---

## STEP 7: Create a Minimal Dashboard (Placeholder)

**src/pages/Dashboard.tsx:**
```typescript
import { useAuth } from '../contexts/AuthContext'
import { usePageTitle } from '../hooks/usePageTitle'

export default function Dashboard() {
  usePageTitle('Dashboard')
  const { profile, signOut } = useAuth()

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Dashboard</h1>
          <p className="text-text-secondary mt-1">
            Welcome back, {profile?.display_name || 'there'}
          </p>
        </div>
        <button
          onClick={signOut}
          className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          Sign Out
        </button>
      </div>

      {/* Placeholder — your app's content goes here */}
      <div className="bg-surface-base rounded-xl border border-border-subtle shadow-card p-12 text-center">
        <p className="text-text-tertiary">
          Auth complete. Ready for Data Layer (Module 03).
        </p>
      </div>
    </div>
  )
}
```

---

## STEP 8: Create a Minimal Profile Page

**src/pages/Profile.tsx:**
```typescript
import { useAuth } from '../contexts/AuthContext'
import { usePageTitle } from '../hooks/usePageTitle'
import { formatFullDate } from '../utils/formatDate'

export default function Profile() {
  usePageTitle('Profile')
  const { profile, user } = useAuth()

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold text-text-primary mb-8">Profile</h1>

      <div className="bg-surface-base rounded-xl border border-border-subtle shadow-card p-6">
        <div className="flex items-center gap-4 mb-6">
          {profile?.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt={profile.display_name || 'Avatar'}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-brand flex items-center justify-center text-white text-xl font-semibold">
              {profile?.display_name?.[0]?.toUpperCase() || '?'}
            </div>
          )}
          <div>
            <h2 className="text-lg font-medium text-text-primary">
              {profile?.display_name || 'Unknown'}
            </h2>
            <p className="text-text-secondary text-sm">{profile?.email}</p>
          </div>
        </div>

        <dl className="space-y-4">
          <div>
            <dt className="text-xs font-medium text-text-tertiary uppercase tracking-wide">
              Account Type
            </dt>
            <dd className="text-text-primary mt-1 capitalize">
              {profile?.role || 'user'}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-text-tertiary uppercase tracking-wide">
              Member Since
            </dt>
            <dd className="text-text-primary mt-1">
              {profile?.created_at ? formatFullDate(profile.created_at) : '—'}
            </dd>
          </div>
        </dl>
      </div>

      {/* Danger Zone — delete account. Full implementation in Module 03 (Data Layer) */}
      <div className="mt-12 pt-8 border-t border-red-200">
        <h3 className="text-lg font-semibold text-red-600 mb-2">Danger Zone</h3>
        <p className="text-text-secondary text-sm mb-4">
          Account deletion will be available after the data layer is set up (Module 03).
        </p>
      </div>
    </div>
  )
}
```

---

## STEP 9: Create a Minimal Landing Page

**src/pages/LandingPage.tsx:**
```typescript
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { usePageTitle } from '../hooks/usePageTitle'

export default function LandingPage() {
  usePageTitle('')
  const { user, loading } = useAuth()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-surface-canvas px-4">
      <h1 className="text-5xl font-bold text-text-primary mb-4 text-center">
        [YOUR_APP_NAME]
      </h1>
      <p className="text-xl text-text-secondary mb-8 text-center max-w-md">
        [One-line description of what the app does]
      </p>

      {!loading && (
        <Link
          to={user ? '/dashboard' : '/login'}
          className="bg-brand hover:bg-brand-dark text-white font-medium px-8 py-3 rounded-lg transition-colors"
        >
          {user ? 'Go to Dashboard' : 'Get Started'}
        </Link>
      )}
    </div>
  )
}
```

---

## STEP 10: Wire Up App.tsx

Replace **src/App.tsx** with:

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ThemeProvider>
          <ToastProvider>
            <BrowserRouter>
              <Routes>
                {/* Public routes */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />

                {/* Protected routes — any authenticated user */}
                <Route path="/dashboard" element={
                  <ProtectedRoute><Dashboard /></ProtectedRoute>
                } />
                <Route path="/profile" element={
                  <ProtectedRoute><Profile /></ProtectedRoute>
                } />

                {/* Admin routes — add when needed:
                <Route path="/admin" element={
                  <AdminRoute><AdminDashboard /></AdminRoute>
                } />
                */}

                {/* 404 */}
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </BrowserRouter>
          </ToastProvider>
        </ThemeProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
```

**Provider nesting order matters:**
1. ErrorBoundary (outermost — catches everything)
2. AuthProvider (needs to be outside everything that checks auth)
3. ThemeProvider (independent, but inside auth for convenience)
4. ToastProvider (innermost — so toasts can appear over everything)

---

## STEP 11: Configure Supabase Auth Redirect

For OAuth to work in development, you need to add `http://localhost:5173` as an allowed redirect URL:

1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add `http://localhost:5173/**` to "Redirect URLs"
3. For production, also add your production URL

**IMPORTANT: Print this as a reminder for me. Do NOT try to configure Supabase remotely.**

---

## STEP 12: Verify

Run `npm run dev` and verify:

1. Landing page shows with "Get Started" button
2. Clicking "Get Started" goes to /login
3. Google sign-in button appears and is clickable
4. After sign-in, redirects to /dashboard
5. Dashboard shows the user's name
6. /profile shows user info
7. Sign out returns to landing
8. Navigating to /dashboard while signed out redirects to /login
9. Navigating to /nonexistent shows 404
10. Zero console errors

Then verify the build:
```bash
npm run build
```

Must complete with zero errors.

---

## STEP 13: Commit

```bash
git add -A
git commit -m "auth: add Supabase Google OAuth, profiles, protected routes, role-based access"
```

---

## WHAT YOU NOW HAVE

| Feature | Status |
|---------|--------|
| Google OAuth sign-in | Done |
| Auto-created user profiles | Done (via DB trigger) |
| Role system (user/pro/admin) | Done |
| Role can't be self-changed | Done (RLS policy) |
| Protected routes | Done |
| Admin-only routes | Done (ready to use) |
| Pro-only routes | Pattern ready |
| Session persistence | Done (Supabase handles refresh tokens) |
| Auth loading states | Done (spinner while checking session) |
| Login page with error handling | Done |
| Landing page with auth-aware CTA | Done |
| Dashboard with sign-out | Done |
| Profile page | Done |
| Dark mode toggle | Done (context ready, toggle component in Module 04) |
| Toast notifications | Done (basic renderer, full component in Module 04) |

## KEY DIFFERENCES FROM FIREBASE (for your understanding)

| Concept | Firebase | Supabase (what we built) |
|---------|----------|--------------------------|
| User creation | `onAuthStateChanged` + manual doc write | Database trigger (automatic) |
| Auth state | `onAuthStateChanged` callback | `onAuthStateChange` subscription |
| Sign-in | `signInWithPopup` | `signInWithOAuth` (redirect-based) |
| Profile storage | `users/{uid}` document | `profiles` table row |
| Security | Firestore rules (JSON-like) | RLS policies (SQL) |
| Role protection | Client-side check + rules | Client-side check + RLS |
| Token refresh | Automatic + `onAuthStateChanged` | Automatic + `TOKEN_REFRESHED` event |
| Session | Firebase manages cookies | Supabase manages localStorage tokens |

## WHAT'S NEXT

| Module | What It Adds |
|--------|-------------|
| **03 — Data Layer** | SQL tables for your app data, RLS policies, service functions, delete account |
| **04 — UI Kit** | Full Modal, Toast, Button, Avatar, Skeleton, EmptyState components |

---

## --- END PROMPT ---
