# Martin's Platform-Agnostic App Builder

> UI/UX constitution for all DunkStack and agent-built interfaces.
> The agent reads the heading it needs and drills into that section.

---

## How To Use This Template

### Step 1: Clarify Your App Idea (Optional)

Have a rough idea but not sure how to describe it?
Use an App Idea Generator Prompt to structure it.
Paste the output into Sections 1 & 2 below.

### Step 2: Generate Your Style Guide (Optional but Recommended)

Find a screenshot of an app/website whose visual style you love.
Use a Style Guide Generator Prompt with that image.
Paste the output into Section 3 below.

### Step 3: Fill In Any Remaining Details

Review Sections 1, 2, and 3.
Fill in anything that's still blank.

### Step 4: Generate Your App

Copy everything below "THE PROMPT" line.
Paste into your AI code generation tool.
DO NOT MODIFY Section 4 - these are the technical guardrails that make it work.

---

## THE PROMPT (Copy Everything Below This Line)

### SECTION 1: APP IDENTITY [FILL THIS IN]

- **App Name:** [YOUR_APP_NAME]
- **One-Line Description:** [What does this app do in one sentence?]
- **Target User:** [Who is this for? Be specific]
- **Core Problem It Solves:** [What pain point does this eliminate?]

### SECTION 2: FEATURES [FILL THIS IN]

**Core Features (3-5 max):**

1. [Feature 1 - be specific about what it does]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4 - optional]
5. [Feature 5 - optional]

**What Users Can Do:**

1. [Main action 1 - e.g., "Create and save recipes"]
2. [Main action 2 - e.g., "Organize recipes into collections"]
3. [Main action 3 - e.g., "Search their saved recipes"]

### SECTION 3: STYLE GUIDE [FILL THIS IN OR PASTE FROM STYLE GENERATOR]

> Tip: Use a Style Guide Generator Prompt with a screenshot of an app you like, then paste the output here.

- **Visual Style:** [Modern/Minimal/Playful/Corporate]
- **Primary Brand Color:** [e.g., #DFFF5E or "electric lime"]
- **Secondary Color:** [e.g., #10B981 or "emerald green"]
- **Personality/Tone:** [Friendly/Professional/Casual/Serious]
- **Design Inspiration:** [Optional - "Like Notion" or "Like Linear" or "Clean SaaS dashboard"]

---

### SECTION 4: TECHNICAL REQUIREMENTS [DO NOT MODIFY]

#### STACK (MANDATORY)

- React with TypeScript
- Tailwind CSS for all styling
- Authentication (with role-based access control)
- Database for persistent storage
- React Context for auth state
- NO external state libraries

#### FILE STRUCTURE (MINIMUM BASE - EXPAND AS NEEDED)

```
src/
├── App.tsx                    # Main app with routing
├── main.tsx                   # Entry point
├── index.css                  # Tailwind imports only
├── config/
│   └── [backend].ts           # Backend/service configuration
├── contexts/
│   ├── AuthContext.tsx        # Auth state + user profile with role
│   ├── ThemeContext.tsx       # Dark mode state + toggle
│   ├── ToastContext.tsx       # Toast notification state
│   └── [FeatureName]Context.tsx  # ADD contexts for complex state
├── hooks/
│   ├── useAuth.ts             # Auth hook (re-exported from context)
│   ├── usePageTitle.ts        # Dynamic document title
│   └── use[Feature].ts        # ADD custom hooks per feature
├── components/
│   ├── ProtectedRoute.tsx     # Route guard - any authenticated user
│   ├── AdminRoute.tsx         # Route guard - admin only
│   ├── ProRoute.tsx           # Route guard - pro/admin only (optional)
│   ├── ErrorBoundary.tsx      # Catches crashes, shows fallback UI
│   ├── Layout.tsx             # Main layout - handles responsive sidebar
│   ├── Sidebar.tsx            # Sidebar nav + help link at bottom
│   ├── MobileNav.tsx          # Mobile header with hamburger toggle
│   ├── ui/                    # REQUIRED reusable UI components
│   │   ├── Modal.tsx          # REQUIRED - for confirmations, dialogs
│   │   ├── ConfirmModal.tsx   # REQUIRED - delete/destructive action confirmation
│   │   ├── Toast.tsx          # REQUIRED - success/error notifications
│   │   ├── Button.tsx         # REQUIRED - with loading state support
│   │   ├── Avatar.tsx         # REQUIRED - user avatar with fallback
│   │   ├── ThemeToggle.tsx    # REQUIRED - dark/light mode toggle
│   │   ├── Card.tsx           # Standard card wrapper
│   │   ├── Skeleton.tsx       # REQUIRED - loading placeholders
│   │   ├── EmptyState.tsx     # REQUIRED - empty list states with CTA
│   │   └── Spinner.tsx        # Loading spinner
│   └── [FeatureName]/         # ADD folders grouping feature components
├── pages/
│   ├── LandingPage.tsx        # Public landing page
│   ├── LoginPage.tsx          # Login page
│   ├── Dashboard.tsx          # Main authenticated view (list view)
│   ├── Profile.tsx            # User profile + delete account (danger zone)
│   ├── NotFoundPage.tsx       # 404 page
│   ├── [Item]DetailPage.tsx   # ADD: Detail view for saved items
│   ├── [Item]CreatePage.tsx   # ADD: Create new item
│   └── [Item]EditPage.tsx     # ADD: Edit existing item (if separate from create)
├── services/
│   └── api.ts                 # All backend/database operations
├── utils/
│   ├── formatDate.ts          # Date formatting helpers (relative time)
│   └── pluralize.ts           # Pluralization helper (1 item vs 2 items)
└── types/
    └── index.ts               # ALL TypeScript interfaces (UserProfile, etc.)
```

File rules: One component per file. Group related components in feature folders. Create interfaces for all data types. Add custom hooks for reusable logic.

#### IMPORTANT: DARK-FIRST STYLE GUIDES

If the style guide in Section 3 is dark-themed (dark backgrounds, light text), you MUST:

- Use CSS variables for BOTH modes - not hardcoded hex values
- Set light mode values in `:root` (the default)
- Set dark mode values in `.dark` class

Example for a dark-first design:

```css
:root {
  /* Light mode (yes, still define this even if style guide is dark) */
  --color-surface-canvas: #F9FAFB;
  --color-surface-base: #FFFFFF;
  --color-text-primary: #111827;
}

.dark {
  /* Dark mode - use the style guide's dark colors here */
  --color-surface-canvas: #05010D;
  --color-surface-base: #0F0A1F;
  --color-text-primary: #FFFFFF;
}
```

DO NOT hardcode dark colors directly in Tailwind config. Use `var(--color-*)` references so the theme toggle works.

---

## Theme Context (Dark Mode)

### contexts/ThemeContext.tsx

```tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme') as Theme;
      if (stored) return stored;
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    }
    return 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setThemeState(t => t === 'light' ? 'dark' : 'light');
  const setTheme = (t: Theme) => setThemeState(t);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
```

### components/ui/ThemeToggle.tsx

```tsx
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      className="p-2 rounded-lg hover:bg-surface-muted transition-colors"
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5 text-text-secondary" />
      ) : (
        <Sun className="w-5 h-5 text-text-secondary" />
      )}
    </button>
  );
}
```

---

## Protected Route Patterns

### components/ProtectedRoute.tsx

```tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Spinner from './ui/Spinner';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

### components/AdminRoute.tsx

```tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Spinner from './ui/Spinner';

export default function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, userProfile, loading, isAdmin } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
```

### Usage in App.tsx routes

```tsx
// Public routes
<Route path="/" element={<LandingPage />} />
<Route path="/login" element={<LoginPage />} />

// Protected routes (any authenticated user)
<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
<Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

// Admin-only routes
<Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
```

### Conditional UI based on role

```tsx
const { isAdmin, isPro, userProfile } = useAuth();

{isAdmin && (
  <Link to="/admin" className="text-text-secondary hover:text-text-primary">
    Admin Dashboard
  </Link>
)}

{!isPro && (
  <Card className="bg-brand/10 border-brand">
    <p>Upgrade to Pro for unlimited features</p>
    <Button>Upgrade Now</Button>
  </Card>
)}
```

---

## Routing Structure (Exact Pattern)

### App.tsx

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={
                <ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>
              } />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
export default App;
```

---

## Design System

### Typography

| Element        | Size  | Weight    | Class                                        |
|----------------|-------|-----------|----------------------------------------------|
| Page Title     | 24px  | Semi-bold | `text-2xl font-semibold text-text-primary`   |
| Section Header | 18px  | Semi-bold | `text-lg font-semibold text-text-primary`    |
| Card Title     | 16px  | Medium    | `text-base font-medium text-text-primary`    |
| Body Text      | 14px  | Regular   | `text-sm text-text-secondary`                |
| Small/Meta     | 12px  | Regular   | `text-xs text-text-tertiary`                 |

### Spacing

- Card padding: `p-6` (24px)
- Section gaps: `gap-6` (24px)
- Element gaps: `gap-4` (16px)

### Cards

```
bg-surface-base rounded-card border border-border-subtle shadow-card p-6
```

### Primary Button

```
bg-brand hover:bg-brand-dark text-text-primary font-medium px-6 py-3 rounded-lg transition-colors
```

### Inputs

```
bg-surface-muted text-text-primary placeholder:text-text-tertiary px-4 py-3 rounded-lg w-full outline-none focus:ring-2 focus:ring-brand
```

### Layout Structure

```
┌─────────────────────────────────────────────────┐
│ HEADER: Logo          User Avatar | Sign Out    │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│   SIDEBAR    │         MAIN CONTENT             │
│   (240px)    │         (scrollable)             │
│              │                                  │
│   - Nav      │         Cards, forms,            │
│   - [Items]  │         data display             │
│   - Help     │                                  │
└──────────────┴──────────────────────────────────┘
```

- Sidebar: 240px wide, `bg-surface-base`, `border-r`
- Header: Full width, `bg-surface-base`, `border-b`, `h-16`
- Main: `flex-1`, `overflow-y-auto`, `p-8`

### Sidebar Structure

```tsx
<aside className="w-60 bg-surface-base border-r border-border-subtle flex flex-col h-full">
  <div className="flex-1 p-4 overflow-y-auto">
    <nav className="space-y-2">
      <Link to="/dashboard">Dashboard</Link>
      <Link to="/profile">Profile</Link>
      {isAdmin && <Link to="/admin">Admin</Link>}
    </nav>

    <div className="mt-6">
      <h3 className="text-xs font-medium text-text-tertiary mb-2">Recent Items</h3>
    </div>
  </div>

  <div className="p-4 border-t border-border-subtle">
    <a
      href="mailto:support@yourdomain.com"
      className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary"
    >
      <HelpCircle className="w-4 h-4" />
      Help & Support
    </a>
  </div>
</aside>
```

---

## Responsive Design (Mandatory)

Build mobile-first. Design for mobile, then scale up for larger screens.

### Breakpoints (Tailwind defaults)

- Mobile: < 640px (default styles, no prefix)
- Tablet: `sm:` 640px and up
- Desktop: `lg:` 1024px and up

### Layout Behavior

```
MOBILE (< 640px):
┌─────────────────────┐
│ HEADER    [☰] [avatar]  │
├─────────────────────┤
│                     │
│    MAIN CONTENT     │
│    (scrollable)     │
│                     │
│    Cards stack      │
│    vertically       │
│                     │
└─────────────────────┘

TABLET/DESKTOP (≥ 1024px):
┌─────────────────────────────────────────────────┐
│ HEADER: Logo          User Avatar | Sign Out    │
├──────────────┬──────────────────────────────────┤
│   SIDEBAR    │         MAIN CONTENT             │
│   (240px)    │         (scrollable)             │
└──────────────┴──────────────────────────────────┘
```

### Mobile Navigation

- Sidebar hidden by default on mobile
- Hamburger icon in header toggles sidebar
- Sidebar slides in as overlay (not push)
- Clicking outside or nav item closes sidebar
- Add close button inside mobile sidebar

### Component Responsive Rules

| Component | Mobile                        | Desktop                  |
|-----------|-------------------------------|--------------------------|
| Sidebar   | Hidden, hamburger toggle      | Always visible, 240px    |
| Cards     | Full width, stack vertically  | Grid 2-3 columns        |
| Forms     | Full width inputs             | Max-width container      |
| Buttons   | Full width for primary actions| Auto width               |
| Modals    | Full screen or nearly full    | Centered, max-w-md       |
| Text      | Base size 16px minimum        | Can be smaller           |

### Touch Targets

- Minimum 44px x 44px for all clickable elements on mobile
- Add padding to small icons/buttons to meet minimum
- Adequate spacing between touch targets (no accidental taps)

### Responsive Classes Pattern

```tsx
// Card grid
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

// Hide on mobile, show on desktop
<div className="hidden lg:block">

// Show on mobile, hide on desktop
<div className="lg:hidden">

// Full width mobile, contained desktop
<div className="w-full lg:max-w-md">

// Padding adjustments
<div className="p-4 lg:p-8">
```

---

## UI/UX Standards (Mandatory)

### Required UI Components

You MUST create and use these components. They are NOT optional:

- **Modal.tsx** - Base modal with overlay, close button, title, content slots
- **ConfirmModal.tsx** - "Are you sure?" dialog for destructive actions
- **Toast.tsx** - Slide-in notification (success, error, info variants)
- **ToastContext.tsx** - Global toast state with `showToast(message, type)` function
- **Skeleton.tsx** - Animated placeholder matching content shape
- **EmptyState.tsx** - Illustration/icon + message + CTA button

### BANNED - DO NOT USE

These are strictly forbidden:

- `alert()` - Use Toast for messages
- `confirm()` - Use ConfirmModal for confirmations
- `prompt()` - Use a proper form Modal
- `console.log` for user feedback - Use Toast
- Text-only empty states - Use EmptyState component with icon and CTA
- Browser default dialogs of any kind

### Page Types For User Data

Any data the user creates/saves MUST follow this pattern:

**List View** (e.g., Dashboard)
- Shows all items as cards or rows
- Clicking an item navigates to Detail View
- Has "Create New" button

**Detail View** (e.g., /items/:id)
- Read-only display of single item
- Shows all item data nicely formatted
- Action buttons: Edit, Delete, Share, etc.
- Delete opens ConfirmModal, then redirects to List on success

**Create View** (e.g., /items/new)
- Form to create new item
- Save navigates to Detail View of new item
- Cancel returns to List View

**Edit View** (e.g., /items/:id/edit)
- Form pre-filled with existing data
- Save navigates back to Detail View
- Cancel returns to Detail View (not List)

### Navigation Flow

```
┌──────────┐     click item      ┌──────────────┐
│   LIST   │ ─────────────────▶  │    DETAIL    │
│   VIEW   │                     │     VIEW     │
└──────────┘                     └──────────────┘
     │                                  │
     │ click "New"              click "Edit"
     ▼                                  │
┌──────────┐                           │
│  CREATE  │                           │
│   VIEW   │                           ▼
└──────────┘                     ┌──────────────┐
     │                           │     EDIT     │
     │ save                      │     VIEW     │
     ▼                           └──────────────┘
┌──────────────┐                       │
│    DETAIL    │ ◀─────────────────────┘
│     VIEW     │         save
└──────────────┘
```

### Anti-Patterns - DO NOT DO THESE

- Clicking saved item opens it in edit mode directly
- Using Create form as Edit form by pre-loading data
- No way to view an item without editing it
- Single "smart" component that handles both view and edit
- Delete with no confirmation
- Success/error with no feedback to user
- Empty lists with just "No items" text (needs icon + CTA)
- Loading states that are just the word "Loading..."

### Feedback Patterns

**On Success:**
- Show success Toast ("Item created successfully")
- Navigate to appropriate view

**On Error:**
- Show error Toast with helpful message
- Stay on current view
- Keep form data intact

**On Delete:**
- User clicks delete
- ConfirmModal appears: "Delete this item? This cannot be undone."
- User confirms
- Show loading state on button
- On success: Toast + redirect to List
- On error: Toast + close modal

**On Loading:**
- Lists: Show Skeleton cards (not spinner)
- Detail View: Show Skeleton matching content layout
- Buttons during action: Show spinner inside button, disable button

---

## Polish & UX Details (Mandatory)

### Date & Time Formatting

Never show raw timestamps. Format dates for humans:

```ts
// utils/formatDate.ts
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 172800) return 'Yesterday';
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
```

Display examples:
- "Just now", "5m ago", "2h ago" (within 24 hours)
- "Yesterday" (24-48 hours)
- "3d ago" (within a week)
- "Jan 15" (older than a week)
- "Jan 15, 2024" (different year)

### Text Truncation

Long text MUST be truncated to prevent layout breaking:

```tsx
// Sidebar items: max 30 characters
<span className="truncate max-w-[200px]">{title}</span>

// Card descriptions: max 2 lines
<p className="line-clamp-2">{description}</p>

// Table cells: single line truncate
<td className="truncate max-w-[150px]">{content}</td>
```

Tailwind classes:
- `truncate` - Single line with ellipsis
- `line-clamp-2` - Multi-line (2 lines) with ellipsis
- Always set `max-w-` when using truncate

### Back Navigation

Every detail/edit page MUST have back navigation:

```tsx
<button
  onClick={() => navigate(-1)}
  className="flex items-center gap-2 text-text-secondary hover:text-text-primary mb-6"
>
  <ArrowLeftIcon className="w-4 h-4" />
  Back
</button>
```

### Transitions & Animations

Add subtle animations for polish:

```css
/* Modal backdrop fade */
.modal-backdrop { @apply transition-opacity duration-200; }

/* Modal content scale */
.modal-content { @apply transition-all duration-200 ease-out; }

/* Toast slide in */
.toast { @apply transition-transform duration-300 ease-out; }

/* Card hover lift */
.card-hover { @apply transition-all duration-200 hover:shadow-md hover:-translate-y-0.5; }

/* Button press */
.btn { @apply transition-all duration-150 active:scale-[0.98]; }
```

Required animations:
- Modals: Fade in backdrop, scale up content
- Toasts: Slide in from top-right
- Cards: Subtle lift on hover
- Buttons: Slight scale on press
- Sidebar: Slide in on mobile

### Accessibility Basics

**Focus States:**
```
className="focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
```

**Keyboard Navigation:**
```tsx
useEffect(() => {
  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };
  document.addEventListener('keydown', handleEsc);
  return () => document.removeEventListener('keydown', handleEsc);
}, [onClose]);
```

**Icon Buttons:**
```tsx
<button aria-label="Close modal" onClick={onClose}>
  <XIcon className="w-5 h-5" />
</button>
```

**Screen Reader Text:**
```tsx
<span className="sr-only">Loading...</span>
<div role="status" aria-live="polite">{message}</div>
```

### Pagination / List Limits

Lists MUST handle large amounts of data. Choose ONE approach:

**Option 1: Pagination**
```tsx
const ITEMS_PER_PAGE = 10;
const [page, setPage] = useState(1);

<div className="flex justify-center gap-2 mt-6">
  <Button disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
  <span className="py-2 px-4">Page {page} of {totalPages}</span>
  <Button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
</div>
```

**Option 2: Load More**
```tsx
const [limit, setLimit] = useState(10);
<Button onClick={() => setLimit(l => l + 10)}>
  Load More ({remaining} remaining)
</Button>
```

**Option 3: Infinite Scroll** (use Intersection Observer)

### Form Field States

```tsx
<div className="space-y-1">
  <label className="text-sm font-medium text-text-primary">Email</label>
  <input
    className={`
      w-full px-4 py-3 rounded-lg border transition-colors
      ${error
        ? 'border-red-500 bg-red-50 focus:ring-red-500'
        : 'border-border-subtle bg-surface-muted focus:ring-brand'
      }
      ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      focus:outline-none focus:ring-2
    `}
    disabled={isSubmitting}
  />
  {error && <p className="text-sm text-red-600">{error}</p>}
  {helperText && !error && <p className="text-sm text-text-tertiary">{helperText}</p>}
</div>
```

States to handle: Default, Focused, Filled, Error, Disabled, Helper text

### Unsaved Changes Warning

```tsx
function useUnsavedChanges(hasChanges: boolean) {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);
}
```

### 404 / Not Found Handling

**Route-level 404:**
```tsx
<Route path="*" element={<NotFoundPage />} />
```

**NotFoundPage component:**
```tsx
function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-bold text-text-tertiary">404</h1>
      <p className="text-xl text-text-secondary mt-4">Page not found</p>
      <Link to="/dashboard" className="mt-6 text-brand hover:underline">
        Back to Dashboard
      </Link>
    </div>
  );
}
```

**Data-level not found:**
```tsx
if (!loading && !item) {
  return (
    <EmptyState
      icon={<SearchIcon />}
      title="Item not found"
      description="This item may have been deleted or doesn't exist."
      action={{ label: "Back to Dashboard", href: "/dashboard" }}
    />
  );
}
```

### Hover States

All interactive elements need hover feedback:

```tsx
// Cards - lift effect
className="hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer"

// Buttons - darken
className="hover:bg-brand-dark transition-colors"

// Links - underline or color change
className="hover:text-brand hover:underline"

// Icon buttons - background
className="hover:bg-surface-muted rounded-lg p-2 transition-colors"

// Table rows - highlight
className="hover:bg-surface-muted transition-colors"

// Sidebar items - background
className="hover:bg-surface-muted rounded-lg transition-colors"
```

---

## Additional Standards (Mandatory)

### Icons - Use Lucide React

```tsx
import { Home, Settings, Trash2, Copy, Check, X, Menu, ArrowLeft, Search, Plus, Loader2 } from 'lucide-react';

<Home className="w-5 h-5" />
<button><Plus className="w-4 h-4 mr-2" /> New Item</button>
<Loader2 className="w-5 h-5 animate-spin" />
```

Common icons needed:
- Navigation: Home, Settings, User, LogOut, Menu, X, ArrowLeft
- Actions: Plus, Trash2, Edit, Copy, Check, Download, Share
- Status: Loader2 (spinner), AlertCircle, CheckCircle, XCircle
- UI: Search, ChevronDown, ChevronRight, MoreVertical

### Error Boundary

```tsx
class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() { return { hasError: true }; }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-canvas">
          <div className="text-center p-8">
            <h1 className="text-2xl font-semibold text-text-primary mb-2">Something went wrong</h1>
            <p className="text-text-secondary mb-4">Please refresh the page to try again.</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-brand hover:bg-brand-dark text-text-primary px-6 py-3 rounded-lg"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Wrap in App.tsx
<ErrorBoundary>
  <AuthProvider>...</AuthProvider>
</ErrorBoundary>
```

### Loading Button Pattern

```tsx
interface ButtonProps {
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'danger';
}

function Button({ loading, disabled, children, onClick, type = 'button', variant = 'primary' }: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading || disabled}
      className={`
        flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium
        transition-all duration-150 active:scale-[0.98]
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variant === 'primary' ? 'bg-brand hover:bg-brand-dark text-text-primary' : ''}
        ${variant === 'secondary' ? 'bg-surface-muted hover:bg-border-subtle text-text-primary' : ''}
        ${variant === 'danger' ? 'bg-red-600 hover:bg-red-700 text-white' : ''}
      `}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {loading ? 'Loading...' : children}
    </button>
  );
}
```

### User Avatar With Fallback

```tsx
function Avatar({ src, name, size = 'md' }: { src?: string | null; name?: string | null; size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-12 h-12 text-base' };

  const initials = name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || '?';

  if (src) {
    return (
      <img
        src={src}
        alt={name || 'User'}
        className={`${sizes[size]} rounded-full object-cover`}
        onError={(e) => {
          e.currentTarget.style.display = 'none';
          e.currentTarget.nextElementSibling?.classList.remove('hidden');
        }}
      />
    );
  }

  return (
    <div className={`${sizes[size]} rounded-full bg-brand flex items-center justify-center font-medium text-text-primary`}>
      {initials}
    </div>
  );
}
```

### Dynamic Page Titles

```tsx
function usePageTitle(title: string) {
  useEffect(() => {
    const appName = 'AppName';
    document.title = title ? `${title} - ${appName}` : appName;
  }, [title]);
}

// Usage
function Dashboard() {
  usePageTitle('Dashboard');
  return ...;
}
```

### Autofocus on Forms

```tsx
const inputRef = useRef<HTMLInputElement>(null);
useEffect(() => { inputRef.current?.focus(); }, []);
<input ref={inputRef} ... />

// Or simply
<input autoFocus ... />
```

### Pluralization Helper

```ts
function pluralize(count: number, singular: string, plural?: string): string {
  const pluralForm = plural || `${singular}s`;
  return count === 1 ? `${count} ${singular}` : `${count} ${pluralForm}`;
}

// Usage
pluralize(1, 'item')                   // "1 item"
pluralize(5, 'item')                   // "5 items"
pluralize(1, 'entry', 'entries')       // "1 entry"
```

### Search / Filter for Lists

```tsx
const [searchQuery, setSearchQuery] = useState('');

const filteredItems = items.filter(item =>
  item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
  item.description?.toLowerCase().includes(searchQuery.toLowerCase())
);

<div className="relative mb-6">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-tertiary" />
  <input
    type="text"
    placeholder="Search..."
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    className="w-full pl-10 pr-4 py-3 bg-surface-muted rounded-lg outline-none focus:ring-2 focus:ring-brand"
  />
</div>

{filteredItems.length === 0 && searchQuery && (
  <p className="text-center text-text-secondary py-8">
    No results for "{searchQuery}"
  </p>
)}
```

### Retry on Error

```tsx
<div className="text-center py-8">
  <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
  <p className="text-text-secondary mb-4">{error}</p>
  <Button onClick={retry} variant="secondary">Try Again</Button>
</div>
```

### Network / Offline Handling

```tsx
const [isOnline, setIsOnline] = useState(navigator.onLine);

useEffect(() => {
  const handleOnline = () => setIsOnline(true);
  const handleOffline = () => setIsOnline(false);
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}, []);

{!isOnline && (
  <div className="bg-yellow-100 text-yellow-800 px-4 py-2 text-center text-sm">
    You're offline. Some features may not work.
  </div>
)}
```

### Console Clean

Production apps must have zero console errors/warnings:
- No `console.log` statements (use proper error handling)
- No React key warnings (always use unique keys in lists)
- No missing dependency warnings (fix useEffect deps)
- No unused variable warnings
- No TypeScript errors

---

## Critical Rules

### Technical

1. NO database calls in components - use service layer only
2. NO unprotected routes for authenticated features
3. NO inline styles - Tailwind only
4. NO `any` types - define TypeScript interfaces
5. ALL database writes include `createdAt`/`updatedAt` timestamps
6. ALL user data scoped to the authenticated user
7. Wrap app in ErrorBoundary component

### UI/UX

8. NO `alert()`, `confirm()`, `prompt()` - use Modal/ConfirmModal/Toast
9. ALL destructive actions require ConfirmModal
10. ALL async operations show loading state (Skeleton for lists, spinner in buttons)
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
