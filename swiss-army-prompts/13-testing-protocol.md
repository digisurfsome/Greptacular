# MODULE 13: TESTING PROTOCOL

## Verify Everything Works Before You Ship

**What this does:** A comprehensive testing checklist and automated test setup for your app. This isn't unit-test-every-function testing (overkill for vibe coding). This is "make sure everything actually works and doesn't break when you ship it" testing.

**When to use:**
- Before showing your app to anyone
- Before deploying to production
- After making significant changes
- When something feels "off" but you can't pinpoint it

**Two levels:**
1. **Manual Testing Checklist** — Walk through the app like a user (fast, no code)
2. **Automated Smoke Tests** — Playwright tests that catch regressions (optional, for apps you maintain long-term)

---

## --- START PROMPT ---

## TASK: Test This Application Thoroughly

Run through the complete testing protocol. Report every issue found, categorized by severity.

---

## SECTION 1: PRE-FLIGHT CHECKS

Before testing functionality, verify the basics:

### Build Check
```bash
npm run build
```
- [ ] Zero TypeScript errors
- [ ] Zero build warnings
- [ ] Build completes successfully

### Lint Check (if configured)
```bash
npm run lint
```
- [ ] Zero lint errors
- [ ] Zero lint warnings (or only pre-existing ones)

### Dev Server
```bash
npm run dev
```
- [ ] Starts without errors
- [ ] No warnings in terminal
- [ ] Accessible at localhost URL

### Environment
- [ ] `.env.local` exists with Supabase credentials
- [ ] Supabase project is accessible (check Dashboard)
- [ ] At least one test user account exists

---

## SECTION 2: MANUAL TESTING CHECKLIST

Open the app in browser. Open DevTools Console. Clear it. Then test each flow:

### Authentication Flow
- [ ] Landing page loads without console errors
- [ ] "Sign In" / "Get Started" button is visible and clickable
- [ ] Google OAuth popup/redirect works
- [ ] After sign-in, redirected to Dashboard
- [ ] User name/avatar appears correctly
- [ ] Profile page shows correct info
- [ ] Sign out works — returns to landing
- [ ] After sign out, `/dashboard` redirects to `/login`
- [ ] Refresh the page while signed in — session persists
- [ ] Console: zero errors during entire auth flow

### Navigation Flow
- [ ] Every sidebar link works
- [ ] Active page highlighted in sidebar
- [ ] Back buttons work on every detail/edit page
- [ ] Browser back button works correctly
- [ ] Invalid URL shows 404 page
- [ ] 404 page has link back to home

### CRUD Flow (for EACH entity)
**Create:**
- [ ] "New" button visible on list page
- [ ] Form loads with first input focused
- [ ] Required fields show validation errors when empty
- [ ] Submit shows loading state on button
- [ ] Success: toast appears, redirected to detail page
- [ ] New item appears in list (navigate back)

**Read (List):**
- [ ] Items display correctly in cards/list
- [ ] Dates show relative time (not raw timestamps)
- [ ] Long titles truncated properly
- [ ] Long descriptions truncated (line-clamp)
- [ ] Search filters results correctly
- [ ] Empty search shows "no results" message
- [ ] Clear search shows all items
- [ ] Pagination works (if > 12 items)

**Read (Detail):**
- [ ] All fields display correctly
- [ ] Null/empty fields show "—" not "null"
- [ ] Dates formatted as full date
- [ ] Edit button navigates to edit form
- [ ] Delete button opens ConfirmModal

**Update:**
- [ ] Edit form pre-filled with current data
- [ ] Changes are saved correctly
- [ ] Success: toast + redirect to detail with updated data
- [ ] Cancel returns to detail (not list) without saving

**Delete:**
- [ ] ConfirmModal appears with correct message
- [ ] Cancel closes modal without deleting
- [ ] Confirm shows loading state
- [ ] Success: toast + redirect to list, item gone
- [ ] Cannot delete an item that doesn't exist (handle gracefully)

### UI Component Testing
- [ ] Toast: success, error, info types all display correctly
- [ ] Toast: auto-dismisses after ~4 seconds
- [ ] Toast: dismiss button works
- [ ] Modal: Escape key closes
- [ ] Modal: clicking backdrop closes (if enabled)
- [ ] Modal: focus stays inside modal (tab doesn't escape)
- [ ] Buttons: loading state works (spinner + disabled)
- [ ] Skeleton: shows during loading, replaced by real content
- [ ] EmptyState: shows when lists are empty, with working CTA

### Error Handling
- [ ] Turn off WiFi → "You're offline" banner appears
- [ ] Turn WiFi back on → banner disappears
- [ ] Failed data fetch shows error with "Try Again" button
- [ ] "Try Again" actually retries
- [ ] Form submission with network error shows error toast, keeps form data

### Responsive Design
Test at each breakpoint (resize browser window):

**Mobile (375px):**
- [ ] No horizontal scroll on any page
- [ ] Sidebar hidden, hamburger menu works
- [ ] Cards stack vertically
- [ ] Buttons full-width where appropriate
- [ ] Text readable (16px minimum body text)
- [ ] Touch targets at least 44x44px
- [ ] Forms usable — inputs not cut off

**Tablet (768px):**
- [ ] Layout adapts (2-column grids)
- [ ] Sidebar may or may not show (either is fine)

**Desktop (1280px):**
- [ ] Sidebar visible
- [ ] Multi-column card grids
- [ ] Comfortable spacing

### Dark Mode
- [ ] Toggle works
- [ ] Every page looks correct in dark mode
- [ ] No white/light backgrounds leaking through
- [ ] Text is readable against dark backgrounds
- [ ] Brand color still looks good on dark
- [ ] Cards, modals, inputs all have dark variants
- [ ] Preference saved — refresh keeps the mode

### Console Audit
- [ ] Navigate through EVERY page
- [ ] Perform EVERY action
- [ ] Zero `console.log` output
- [ ] Zero React warnings
- [ ] Zero TypeScript runtime errors
- [ ] Zero 404 network requests
- [ ] Zero failed API calls (other than intentional error testing)

---

## SECTION 3: SEVERITY CLASSIFICATION

For every issue found, classify it:

| Severity | Definition | Example |
|----------|-----------|---------|
| **P0 — Blocker** | App is broken, can't do the core thing | Can't sign in, data doesn't save, white screen |
| **P1 — Critical** | Major feature broken | Delete doesn't work, search crashes, mobile unusable |
| **P2 — Major** | Feature works but poorly | Slow load, missing loading state, bad error message |
| **P3 — Minor** | Cosmetic or edge case | Alignment off, dark mode color wrong, rare edge case |
| **P4 — Nit** | Polish | Animation missing, hover state missing, date format wrong |

### Issue Report Format

For each issue:

```
[P1] Title of the issue
  Page: /dashboard
  Steps: 1. Click X  2. See Y
  Expected: Z
  Actual: W
  Console error: (if any)
```

---

## SECTION 4: AUTOMATED SMOKE TESTS (OPTIONAL)

For apps you'll maintain long-term, add Playwright tests that catch regressions.

### Setup

```bash
npm install -D @playwright/test
npx playwright install chromium
```

**playwright.config.ts:**
```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: true,
  },
})
```

### Core Smoke Tests

**tests/smoke.spec.ts:**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('landing page loads', async ({ page }) => {
    await page.goto('/')
    // Check that the page has content (not a white screen)
    await expect(page.locator('body')).not.toBeEmpty()
    // Check for console errors
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    await page.waitForTimeout(2000)
    expect(errors).toHaveLength(0)
  })

  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('body')).not.toBeEmpty()
  })

  test('404 page shows for invalid routes', async ({ page }) => {
    await page.goto('/this-page-does-not-exist')
    await expect(page.locator('text=404')).toBeVisible()
  })

  test('unauthenticated user redirected from protected routes', async ({ page }) => {
    await page.goto('/dashboard')
    // Should redirect to login
    await expect(page).toHaveURL(/login/)
  })

  test('no console errors on key pages', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })

    const pages = ['/', '/login']
    for (const url of pages) {
      await page.goto(url)
      await page.waitForTimeout(1000)
    }

    expect(errors).toHaveLength(0)
  })

  test('responsive: no horizontal scroll on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')
    const body = page.locator('body')
    const scrollWidth = await body.evaluate(el => el.scrollWidth)
    const clientWidth = await body.evaluate(el => el.clientWidth)
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1) // 1px tolerance
  })
})
```

### Run Tests

```bash
npx playwright test
npx playwright test --ui  # with visual UI
```

**Add to package.json scripts:**
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

---

## SECTION 5: PRE-DEPLOY CHECKLIST

Final checks before deploying to production:

- [ ] `npm run build` passes
- [ ] All P0 and P1 issues fixed
- [ ] Smoke tests pass (if set up)
- [ ] Environment variables documented in `.env.example`
- [ ] Production Supabase URL (not dev) ready for deploy config
- [ ] Redirect URL added in Supabase for production domain
- [ ] SPA routing configured:
  - **Vercel:** `vercel.json` with `"rewrites": [{"source": "/(.*)", "destination": "/index.html"}]`
  - **Netlify:** `public/_redirects` with `/* /index.html 200`
- [ ] Favicon set
- [ ] Page title set (not "Vite + React + TS")
- [ ] OpenGraph meta tags (optional but nice for sharing)
- [ ] One final manual walkthrough of the complete app

---

## SECTION 6: COMMIT

```bash
git add -A
git commit -m "test: add testing protocol and Playwright smoke tests"
```

---

## POST-TESTING: FIX ISSUES

Use Module 08 (Bug Fix) for each issue found, starting with P0 blockers and working down.

---

## --- END PROMPT ---
