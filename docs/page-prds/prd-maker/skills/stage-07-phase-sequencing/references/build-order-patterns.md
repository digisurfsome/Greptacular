# Build Order Patterns — Phase Sequencing Reference

## Martin's Pattern: The Four Layers

Every phase follows the same forced linear sequence. This is derived from Martin's structural checklist and ensures predictable, auditable builds.

```
Layer 1: CORE LOGIC      — Business logic, utilities, helpers, types, database schemas
Layer 2: STATE MANAGEMENT — Contexts, stores, hooks, data fetching, API clients
Layer 3: UI COMPONENTS    — Pages, components, forms, modals, layouts
Layer 4: INTEGRATION      — Route wiring, exports, entry points, app configuration
```

## Why This Order

- **Core logic first**: Everything downstream depends on the types, utilities, and business rules defined here. Building UI before logic forces the agent to make assumptions that it later has to fix.
- **State second**: State management wraps core logic and exposes it to UI. Without it, UI components can't access data.
- **UI third**: With logic and state in place, UI components are straightforward — they consume hooks and call functions. No guessing.
- **Integration last**: Wiring routes and exports is the final step that connects everything. Doing it earlier means wiring to components that don't exist yet.

## Concrete Examples By Tech Stack

### React + TypeScript

```
1. src/lib/auth.ts              (core logic — auth functions)
2. src/lib/validators.ts        (core logic — validation rules)
3. src/types/user.ts            (core logic — type definitions)
4. src/contexts/AuthContext.tsx  (state — wraps auth logic)
5. src/hooks/useAuth.ts         (state — hook for consuming auth)
6. src/pages/SignIn.tsx          (UI — sign-in page)
7. src/pages/SignUp.tsx          (UI — sign-up page)
8. src/components/AuthGuard.tsx  (UI — route protection component)
9. src/App.tsx                   (integration — add routes)
```

### Next.js + TypeScript

```
1. src/lib/db.ts                (core logic — database client)
2. src/lib/auth.ts              (core logic — auth utilities)
3. src/types/index.ts           (core logic — type definitions)
4. src/app/api/auth/route.ts    (state/API — auth API route)
5. src/hooks/useAuth.ts         (state — client-side auth hook)
6. src/app/sign-in/page.tsx     (UI — sign-in page)
7. src/app/sign-up/page.tsx     (UI — sign-up page)
8. src/middleware.ts             (integration — route protection)
9. src/app/layout.tsx            (integration — layout wrapper)
```

### Python + FastAPI

```
1. src/models/user.py           (core logic — data models)
2. src/services/auth_service.py (core logic — business logic)
3. src/schemas/user.py          (core logic — Pydantic schemas)
4. src/dependencies/auth.py     (state — dependency injection)
5. src/routers/auth.py          (UI/API — route handlers)
6. src/main.py                  (integration — register router)
```

### Flutter + Dart

```
1. lib/models/user.dart         (core logic — data models)
2. lib/services/auth_service.dart (core logic — business logic)
3. lib/providers/auth_provider.dart (state — state management)
4. lib/screens/sign_in_screen.dart  (UI — sign-in screen)
5. lib/screens/sign_up_screen.dart  (UI — sign-up screen)
6. lib/app.dart                     (integration — route registration)
```

## Build Order Entry Format

Each entry in the `build_order` array MUST have:

```json
{
  "file_path": "src/lib/auth.ts",
  "operation": "create",
  "rationale": "Core auth logic — session management, token validation. All auth UI and state depend on this."
}
```

### Operation Values

| Value | When to Use |
|-------|-------------|
| `create` | File does not exist, phase creates it from scratch |
| `modify` | File exists (from a prior phase or boilerplate), phase adds to or changes it |

### Rationale Guidelines

Good rationales explain WHY this file is at this position:
- "Core auth logic — all auth UI depends on these functions"
- "State wrapper — must exist before any component can consume auth"
- "Page component — consumes AuthContext, must come after state layer"
- "Route wiring — final integration step, all pages must exist first"

Bad rationales (too vague — avoid these):
- "Needed for the app"
- "Important file"
- "Should come first"
- "Related to auth"

## Cross-Phase Patterns

When a file is MODIFIED across phases (e.g., `App.tsx` gets new routes in each phase):

- Phase 1: `{ "file_path": "src/App.tsx", "operation": "create", "rationale": "Initial app shell with auth routes" }`
- Phase 2: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add dashboard routes — auth routes already wired" }`
- Phase 3: `{ "file_path": "src/App.tsx", "operation": "modify", "rationale": "Add settings routes — all prior routes stable" }`

The file appears in `files_allowed` for ALL phases that touch it, but only Phase 1 has `"create"`. Subsequent phases use `"modify"` and their rationale references what was already done.
