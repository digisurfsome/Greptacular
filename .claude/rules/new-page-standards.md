# New Page Standards

> **Read this before building ANY new page.** Follow this structure exactly.
> Also read `ui/WORKSPACE_STANDARDS.md` for layout patterns, state management, and component patterns.

## 🚨 WHERE DOCS GO — 3 DIRECTORIES, NO EXCEPTIONS 🚨

```
┌─────────────────────────────────────────────────────────────────────┐
│  docs/page-prds/{page-name}/  — PRDs, specs, file maps for a page  │
│  docs/ideas/                  — brainstorms, concepts, "what if"   │
│  docs/info/                   — research, guides, saved context    │
│                                                                     │
│  NEVER drop loose .md files in docs/. Everything has a home.       │
│  Page PRD index: docs/page-prds/README.md                          │
│  If your page folder doesn't exist, CREATE IT.                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

Every new page MUST use this structure:

```
ui/src/pages/{PageName}Page.tsx          ← Main page component (route entry)
ui/src/components/{page-name}/           ← Page-specific components
ui/src/hooks/use{PageName}.ts            ← Page-specific hook (if needed)
server/routers/{page_name}.py            ← Backend API router
server/services/{page_name}_service.py   ← Backend business logic (if needed)
docs/page-prds/{page-name}/             ← PRD folder (create from day one)
```

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Page component | `{PageName}Page.tsx` | `TokenBudgetPage.tsx` |
| Component folder | `kebab-case` | `ui/src/components/token-budget/` |
| Hook file | `use{PageName}.ts` | `useTokenBudget.ts` |
| Router file | `snake_case.py` | `server/routers/token_budget.py` |
| Service file | `snake_case.py` | `server/services/token_budget.py` |
| PRD folder | `kebab-case` | `docs/page-prds/token-budget/` |

---

## Step-by-Step Checklist

### 1. Create the Page Component
- File: `ui/src/pages/{PageName}Page.tsx`
- Must export a default function component
- Must follow layout patterns from `ui/WORKSPACE_STANDARDS.md`

### 2. Add the Route
- File: `ui/src/App.tsx`
- Add route path constant to `ui/src/lib/routes.ts`
- Add lazy-loaded route in App.tsx

### 3. Create Component Folder
- Folder: `ui/src/components/{page-name}/`
- All page-specific components go here — NOT in the root components folder
- Only truly shared components (used by 3+ pages) go in the root

### 4. Create Page Hook (if needed)
- File: `ui/src/hooks/use{PageName}.ts`
- Use TanStack Query for API calls
- API functions go in `ui/src/lib/api.ts`
- Types go in `ui/src/lib/types.ts`

### 5. Create Backend Router
- File: `server/routers/{page_name}.py`
- Register in `server/main.py`
- Follow existing router patterns (see `server/CLAUDE.md` for examples)

### 6. Create Backend Service (if needed)
- File: `server/services/{page_name}_service.py`
- Business logic goes here, NOT in the router

### 7. Create PRD Folder
- Folder: `docs/page-prds/{page-name}/`
- Every page gets one from day one, even if empty

### 8. Update File Maps
- Add page entry to `ui/CLAUDE.md` (Pages table)
- Add component folder to `ui/CLAUDE.md` (Component Folders table)
- Add hook to `ui/CLAUDE.md` (Hooks table)
- Add router to `server/CLAUDE.md` (Routers table)
- Add service to `server/CLAUDE.md` (Services table)
- Add PRD folder to `docs/CLAUDE.md` (Page PRDs table)

---

## Anti-Patterns (Do NOT Do These)

1. **Do NOT put page-specific components in the root `components/` folder.** Use the page's subfolder.
2. **Do NOT create API fetch calls inside components.** All API calls go through `ui/src/lib/api.ts`.
3. **Do NOT define types inside component files.** Types go in `ui/src/lib/types.ts`.
4. **Do NOT skip the PRD folder.** Even if there's no PRD yet, create the folder.
5. **Do NOT create a new page without updating the file maps.** Other agents need to find your page.
6. **Do NOT create WebSocket connections directly.** Follow the existing hook pattern (see `useWorkspaceChat.ts`).

---

## Template

Minimal page component template:

```tsx
import { useState } from 'react'

export default function {PageName}Page() {
  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Breadcrumb bar */}
      <div className="flex items-center gap-2 border-b border-border px-4 py-2">
        <h1 className="text-lg font-bold">{Page Title}</h1>
      </div>
      
      {/* Main content */}
      <div className="flex-1 overflow-auto p-4">
        {/* Your content here */}
      </div>
    </div>
  )
}
```
