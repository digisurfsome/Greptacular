## POST-BUILD VERIFICATION PROTOCOL

You have just finished building features. Before marking anything as complete, execute this full verification protocol. This is non-negotiable — shipping unverified code is not an option.

---

## PHASE 1: PARALLEL RESEARCH (3 Investigations)

Run these three investigations simultaneously. Each one feeds into the testing phases that follow.

### Investigation 1: Application Structure & User Journeys

Research the codebase and document:

1. **Startup commands** — exact commands to install dependencies and run the dev server, including URL and port
2. **Authentication** — if the app has protected routes, how to create a test account or log in (check .env.example, seed data, or sign-up flow)
3. **Every user-facing route/page** — each URL path and what it renders
4. **Every user journey** — complete flows a user can take (e.g., "sign up → create profile → view dashboard"). For each journey, list specific steps, interactions (clicks, form fills, navigation), and expected outcomes
5. **Key UI components** — forms, modals, dropdowns, pickers, toggles, and other interactive elements

Be exhaustive. Testing will only cover what you identify here.

### Investigation 2: Database Schema & Data Flows

Research the database layer. Read `.env.example` to understand connection variables. **DO NOT read `.env` directly.** Document:

1. **Database type and connection** — what database is used (Postgres, SQLite, etc.) and the environment variable for the connection string
2. **Full schema** — every table, columns, types, and relationships
3. **Data flows per user action** — for each user-facing action, document exactly what records are created, updated, or deleted and in which tables
4. **Validation queries** — for each data flow, provide the exact query to verify records are correct after the action

### Investigation 3: Bug Hunting (Code Analysis)

Analyze the codebase for potential issues. Focus on:

1. **Logic errors** — incorrect conditionals, off-by-one errors, missing null checks, race conditions
2. **UI/UX issues** — missing error handling in forms, no loading states, broken layouts, accessibility problems
3. **Data integrity risks** — missing validation, potential orphaned records, incorrect cascade behavior
4. **Security concerns** — injection vulnerabilities, XSS, missing auth checks, exposed secrets

Return a prioritized list with file paths and line numbers.

---

## PHASE 2: STATIC VERIFICATION

Before touching the browser, verify the code compiles and passes static analysis.

### 2a. Lint & Type Check

```bash
# For TypeScript/JavaScript projects
npm run lint
npm run build          # Catches type errors

# For Python projects
ruff check .
mypy .
```

**If lint or type errors exist — fix them now.** Do not proceed with broken code.

### 2b. Run Existing Test Suites

```bash
# Unit tests
npm test               # or pytest, or whatever the project uses

# Generated E2E tests (if they exist)
npx playwright test tests/e2e/

# API tests
npx playwright test tests/api/
```

Document every failure. Fix what you can before proceeding.

### 2c. Dependency & Import Audit

1. Check for unused imports in files you modified
2. Verify no circular dependencies were introduced
3. Confirm all new dependencies are in package.json / requirements.txt
4. Run `npm ls` or `pip check` to verify dependency tree is clean

---

## PHASE 3: FUNCTIONAL VERIFICATION

For each feature you built, verify it actually works end-to-end.

### 3a. Start the Application

1. Install dependencies if needed
2. Start the dev server
3. Confirm it starts without errors
4. Check the console/terminal output for warnings

### 3b. Test Every User Journey

For each user journey identified in Investigation 1:

1. **Navigate** to the starting point
2. **Execute** each step in the journey
3. **Verify** the expected outcome at each step
4. **Check for errors** — console errors, network failures, unexpected behavior
5. **Document** what you find

If you have browser automation tools available (Playwright MCP, agent-browser, etc.), use them to:
- Take screenshots at key steps
- Capture console output
- Monitor network requests
- Interact with forms and buttons

If you do NOT have browser tools, verify through:
- API endpoint testing with curl/fetch
- Database queries to confirm data flows
- Log output analysis
- Code path tracing (manually walk through the logic)

### 3c. Database Validation

After any interaction that modifies data:

1. Query the database to verify records were created/updated/deleted correctly
   - **SQLite:** `sqlite3 path/to/db.sqlite "SELECT * FROM table WHERE condition"`
   - **Postgres:** `psql "$DATABASE_URL" -c "SELECT * FROM table WHERE condition"`
2. Verify:
   - Records match what was entered in the UI
   - Relationships between records are correct
   - No orphaned or duplicate records
   - Timestamps are reasonable
   - Default values applied correctly

### 3d. Edge Cases & Error States

Test these explicitly:

1. **Empty states** — what happens with no data?
2. **Invalid input** — submit forms with missing/malformed data
3. **Boundary values** — very long strings, zero values, negative numbers
4. **Concurrent operations** — rapid clicks, duplicate submissions
5. **Network failures** — what happens when API calls fail?
6. **Auth edge cases** — expired sessions, unauthorized access attempts

---

## PHASE 4: CROSS-FEATURE INTEGRATION

Features don't exist in isolation. Test interactions between them:

1. **Data dependencies** — does Feature B correctly read data created by Feature A?
2. **UI state** — does navigating between features maintain correct state?
3. **Side effects** — does modifying data in one feature break another?
4. **Shared components** — do shared UI components behave consistently across features?

---

## PHASE 5: RESPONSIVE & VISUAL CHECK

If browser tools are available, check key pages at these viewports:

| Device  | Width | Height |
|---------|-------|--------|
| Mobile  | 375   | 812    |
| Tablet  | 768   | 1024   |
| Desktop | 1440  | 900    |

Look for:
- Layout overflow or horizontal scrolling
- Overlapping elements
- Unreadable text sizes
- Touch targets too small on mobile
- Missing responsive breakpoints

If browser tools are NOT available, review CSS/Tailwind classes for responsive patterns:
- Check for `sm:`, `md:`, `lg:` breakpoint usage
- Verify flex/grid layouts handle different widths
- Look for hardcoded pixel widths that should be responsive

---

## PHASE 6: ISSUE HANDLING

When you find an issue:

1. **Document it** — expected vs actual behavior, file path, line number
2. **Classify severity:**
   - **Critical** — app crashes, data loss, security vulnerability
   - **High** — feature doesn't work, wrong data displayed
   - **Medium** — UI glitch, poor UX, missing error message
   - **Low** — cosmetic, minor text issue
3. **Fix critical and high issues immediately**
4. **Re-verify** the fix works
5. **Document medium/low issues** for follow-up if time is limited

---

## PHASE 7: FINAL VERIFICATION PASS

After all fixes:

1. Re-run lint and type check — confirm still clean
2. Re-run test suites — confirm nothing broke
3. Restart the dev server fresh — confirm clean startup
4. Quick smoke test of each feature — confirm still working
5. Check git status — no untracked files that should be committed

---

## PHASE 8: REPORT

Output a structured summary:

```
## Verification Report

**Features Verified:** [count]
**User Journeys Tested:** [count]
**Issues Found:** [count] ([count] fixed, [count] remaining)

### Static Analysis
- Lint: PASS/FAIL
- Type Check: PASS/FAIL
- Tests: [X] passing, [Y] failing

### Issues Fixed
- [Description] — [file:line] — [severity]

### Remaining Issues
- [Description] — [file:line] — [severity]

### Bug Hunt Findings (Code Analysis)
- [Description] — [severity] — [file:line]

### Database Validation
- [Table/query results summary]

### Notes
- [Anything the next agent or developer should know]
```

---

## IMPORTANT RULES

1. **Fix as you go** — don't just document issues, fix them
2. **Never skip database validation** — the UI looking right doesn't mean the data is right
3. **Test with real data** — not mocks, not empty states (unless testing empty states)
4. **Check console output** — zero errors, zero unhandled warnings
5. **Commit your fixes** — verification that finds bugs and fixes them is worth nothing if you don't save the work
6. **Be thorough** — the goal is that by the time this finishes, every part of the application has been exercised and verified

---

Begin with Phase 1. Run all three investigations before proceeding to Phase 2.
