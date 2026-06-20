# BUILD.md — The Lego Block Architecture

> Every new mechanism, feature, or module follows these rules. No exceptions.
> This is how we build: modular, composable, extractable. Like snapping Legos together.

---

## The Core Principle

**Every piece is an island.** Services don't reach into other services. Hooks don't import other hooks' internals. Pages are just composition layers that plug islands together. When you want to pull a module out into its own product, you copy self-contained files — not untangle spaghetti.

---

## The 5-Layer Stack

Every mechanism in this codebase lives across exactly 5 layers. Each layer has one job:

```
┌─────────────────────────────────────────────────┐
│  1. PAGE          — Composition & layout only   │
│     ui/src/pages/MyPage.tsx                     │
├─────────────────────────────────────────────────┤
│  2. COMPONENTS    — Domain-specific UI blocks   │
│     ui/src/components/my-domain/                │
├─────────────────────────────────────────────────┤
│  3. HOOK          — State + API bridge          │
│     ui/src/hooks/useMyDomain.ts                 │
├─────────────────────────────────────────────────┤
│  4. API CLIENT    — Typed fetch functions        │
│     ui/src/lib/api.ts (add functions here)      │
│     ui/src/lib/types.ts (add types here)        │
├─────────────────────────────────────────────────┤
│  5. BACKEND       — Router → Service → Database │
│     server/routers/my_domain.py                 │
│     server/services/my_domain_*.py              │
└─────────────────────────────────────────────────┘
```

**Data flows DOWN.** Pages call hooks. Hooks call API functions. API functions call backend routers. Routers call services. Never the reverse.

---

## Layer 1: Pages

**Location:** `ui/src/pages/`
**Naming:** `{DomainName}Page.tsx`

Pages are **composition shells**. They import hooks and components, wire them together, and handle layout. They contain ZERO business logic.

### Rules

1. One page per major section of the app
2. Pages import from their own domain's components folder and hooks
3. Pages can import shared components from `ui/src/components/` (top-level)
4. Pages NEVER import from another domain's component folder
5. Layout state (sidebar collapsed, active panel) lives in the page
6. Business state (data, mutations) comes from hooks

### Pattern (from DunkStackPage.tsx)

```tsx
// ✅ CORRECT: Page is just composition
export function DunkStackPage(): React.JSX.Element {
  // Hook provides all state and actions
  const { commsLog, sendMessage, tokenState, ... } = useDunkStack()

  // Page handles layout decisions only
  const [rightPanel, setRightPanel] = useState<RightPanel>('safety')
  const [centerView, setCenterView] = useState<CenterView>('chat')

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb bar */}
      <div className="flex items-center h-10 px-3 border-b ...">...</div>

      {/* Compose domain components */}
      <DunkStackContextGauge totalTokens={...} />
      <DunkStackCommsChat commsLog={commsLog} onSendMessage={sendMessage} />
      <DunkStackSafetyPanel safety={safetyStatus} />
    </div>
  )
}
```

```tsx
// ❌ WRONG: Business logic in the page
export function BadPage() {
  const [data, setData] = useState(null)
  useEffect(() => {
    fetch('/api/something').then(r => r.json()).then(setData)  // NO — this belongs in a hook
  }, [])
}
```

### Current Pages

| Page | Domain | Route |
|------|--------|-------|
| `DashboardPage.tsx` | Project management, Kanban, features | `/#/` (default) |
| `DunkStackPage.tsx` | Agent orchestration, context tracking | `/#/dunkstack` |
| `WorkspacePage.tsx` | IDE workspace, conversations, library | `/#/workspace` |
| `YTStrategyLabPage.tsx` | YouTube discovery & processing | `/#/yt-lab` |
| `RoleLibraryPage.tsx` | Role blueprint management | `/#/roles` |

---

## Layer 2: Components

**Location:** `ui/src/components/{domain-name}/`
**Naming:** `{DomainPrefix}{ComponentName}.tsx`

### Rules

1. **Domain components go in domain folders:** `dunkstack/`, `workspace/`, `appbuilder/`, `yt-lab/`
2. **Shared/reusable components stay at top level:** `ui/src/components/`
3. **UI primitives live in `ui/`:** Radix wrappers (`button.tsx`, `dialog.tsx`, etc.)
4. Components receive data via props — they don't fetch their own data
5. Components emit events via callback props (`onSendMessage`, `onClose`, etc.)
6. Domain components are prefixed with their domain name for grep-ability

### Folder Structure

```
ui/src/components/
├── dunkstack/                    # Domain: DunkStack
│   ├── DunkStackContextGauge.tsx
│   ├── DunkStackCommsChat.tsx
│   ├── DunkStackSafetyPanel.tsx
│   ├── DunkStackGuidePanel.tsx
│   └── DunkStackAgentPanel.tsx
├── workspace/                    # Domain: Workspace
│   ├── WorkspaceChat.tsx
│   ├── WorkspaceSidebar.tsx
│   └── ...
├── appbuilder/                   # Domain: Agent OS
│   ├── IntakeDock.tsx
│   ├── AgentOSChat.tsx
│   └── ...
├── yt-lab/                       # Domain: YouTube Lab
│   ├── YTDiscoveryPanel.tsx
│   └── ...
├── ui/                           # Primitives (Radix wrappers)
│   ├── button.tsx
│   ├── dialog.tsx
│   └── ...
├── KanbanBoard.tsx               # Shared — used by multiple pages
├── ProjectSelector.tsx           # Shared
├── ThemeSelector.tsx             # Shared
├── Terminal.tsx                  # Shared
└── ...
```

### When to Create a New Domain Folder

Create a new folder when you're building a **mechanism** — a self-contained feature area with its own:
- Backend service(s)
- API endpoints
- React hook
- 3+ components

If it's just one component used across pages, it stays at the top level.

---

## Layer 3: Hooks

**Location:** `ui/src/hooks/`
**Naming:** `use{DomainName}.ts`

Hooks are the **bridge** between the UI and the API. They wrap API calls, manage caching, and expose a clean interface to pages.

### Two Hook Patterns

#### Pattern A: React Query (CRUD data) — use for standard REST resources

Used by: `useRoleLibrary.ts`, `useProjects.ts`, `useAgentOS.ts`, `useSchedules.ts`

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listItems, createItem, updateItem, deleteItem } from '@/lib/api'
import type { ItemCreate, ItemUpdate } from '@/lib/types'

// 1. Define query key hierarchy
const ALL_KEYS = ['my-domain'] as const

const KEYS = {
  all: ALL_KEYS,
  list: (filter?: string) => [...ALL_KEYS, 'list', filter] as const,
  detail: (id: number) => [...ALL_KEYS, 'detail', id] as const,
}

// 2. Export one hook per operation
export function useItems(filter?: string) {
  return useQuery({
    queryKey: KEYS.list(filter),
    queryFn: () => listItems(filter),
  })
}

export function useItem(id: number | null) {
  return useQuery({
    queryKey: KEYS.detail(id!),
    queryFn: () => getItem(id!),
    enabled: id !== null,
  })
}

export function useCreateItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ItemCreate) => createItem(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useUpdateItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemUpdate }) => updateItem(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useDeleteItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteItem(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}
```

#### Pattern B: Stateful + WebSocket (real-time mechanisms)

Used by: `useDunkStack.ts`, `useWorkspaceChat.ts`, `useWebSocket.ts`

```tsx
export function useMyMechanism(): UseMyMechanismReturn {
  // Local state
  const [data, setData] = useState<DataType[]>([])
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)

  // Load initial data on mount
  useEffect(() => {
    async function loadInitial() {
      const result = await fetchInitialData()
      setData(result)
      setLoading(false)
    }
    loadInitial()
  }, [])

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(wsUrl)
    ws.onopen = () => setConnected(true)
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      // Update state based on message type
    }
    ws.onclose = () => setTimeout(connect, 3000)  // Auto-reconnect
    return () => ws.close()
  }, [])

  // Actions wrapped in useCallback
  const doAction = useCallback(async (payload: ActionPayload) => {
    await apiCallForAction(payload)
  }, [])

  return { data, doAction, connected, loading }
}
```

### Rules

1. **One hook file per domain** (can export multiple hooks from it)
2. **Always define a `KEYS` constant** for React Query cache management
3. **Invalidate `KEYS.all`** on any mutation — keeps the cache consistent
4. **Export a typed return interface** for Pattern B hooks
5. **Never call `fetch()` directly** — always go through `api.ts` functions
6. **WebSocket reconnection:** 3-second delay, auto-reconnect on close

### Current Hooks by Domain

| Hook File | Domain | Pattern |
|-----------|--------|---------|
| `useProjects.ts` | Dashboard | A (React Query) |
| `useRoleLibrary.ts` | Role Library | A (React Query) |
| `useAgentOS.ts` | Agent OS | A (React Query) |
| `useSchedules.ts` | Schedules | A (React Query) |
| `useDunkStack.ts` | DunkStack | B (Stateful + WS) |
| `useWorkspaceChat.ts` | Workspace | B (Stateful + WS) |
| `useWebSocket.ts` | Dashboard | B (Stateful + WS) |
| `useAssistantChat.ts` | Assistant | B (Stateful + WS) |
| `useSpecChat.ts` | Spec Creation | B (Stateful + WS) |

---

## Layer 4: API Client & Types

### API Client

**Location:** `ui/src/lib/api.ts`
**Pattern:** Typed async functions that call `fetchJSON<T>()`

```tsx
// Standard CRUD pattern
export async function listItems(filter?: string): Promise<Item[]> {
  const params = filter ? `?filter=${filter}` : ''
  return fetchJSON<Item[]>(`/my-domain${params}`)
}

export async function getItem(id: number): Promise<Item> {
  return fetchJSON<Item>(`/my-domain/${id}`)
}

export async function createItem(data: ItemCreate): Promise<Item> {
  return fetchJSON<Item>('/my-domain', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateItem(id: number, data: ItemUpdate): Promise<Item> {
  return fetchJSON<Item>(`/my-domain/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteItem(id: number): Promise<void> {
  return fetchJSON<void>(`/my-domain/${id}`, { method: 'DELETE' })
}
```

### Rules

1. **Every API function is typed** — input params and return type
2. **All functions use `fetchJSON<T>()`** — the shared fetch wrapper
3. **URL paths match the backend router prefix** exactly
4. **Group functions by domain** in the file with comment headers
5. **Naming convention:** `{verb}{Domain}{Entity}` — e.g., `listBlueprints`, `createFeature`, `dunkstackReadConfig`

### Types

**Location:** `ui/src/lib/types.ts`
**Pattern:** Interfaces grouped by domain with comment section headers

```tsx
// ---- Role Library types ----

export interface RoleBlueprint {
  id: number
  name: string
  role_tag: string
  category: string
  one_liner: string
  prd_content: string
  status: string
  created_at: string
  updated_at: string
}

export interface RoleBlueprintCreate {
  name: string
  role_tag: string
  category: string
  one_liner: string
  prd_content?: string
}

export interface RoleBlueprintUpdate {
  name?: string
  role_tag?: string
  // ... all fields optional
}
```

### Rules

1. **Three interface variants per entity:** `Entity`, `EntityCreate`, `EntityUpdate`
2. **`Create` has required fields**, `Update` has all optional (partial update)
3. **Group types by domain** with comment headers
4. **Export everything** — hooks and API functions import from here
5. **Match backend Pydantic schemas** — field names must be identical (snake_case from Python becomes the JSON contract)

---

## Layer 5: Backend

### Router

**Location:** `server/routers/{domain_name}.py`
**Pattern:** FastAPI `APIRouter` with prefix and tags

```python
"""
My Domain Router
================

CRUD API for my domain resources.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/my-domain", tags=["my_domain"])


# Pydantic request schemas (inline in router file)
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


# Endpoints — thin wrappers that delegate to services
@router.get("/")
async def list_items(category: str | None = None):
    from ..services.my_domain_database import list_items as _list
    return _list(category=category)


@router.get("/{item_id}")
async def get_item(item_id: int):
    from ..services.my_domain_database import get_item as _get
    item = _get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", status_code=201)
async def create_item(body: ItemCreate):
    from ..services.my_domain_database import create_item as _create
    return _create(name=body.name, description=body.description)


@router.put("/{item_id}")
async def update_item(item_id: int, body: ItemUpdate):
    from ..services.my_domain_database import update_item as _update
    result = _update(item_id, **body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int):
    from ..services.my_domain_database import delete_item as _delete
    if not _delete(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
```

### Rules

1. **Prefix pattern:** `/api/{domain-name}` (kebab-case)
2. **Tags match domain name** (snake_case) for OpenAPI grouping
3. **Pydantic schemas live in the router file** — they're request/response contracts, not business logic
4. **Services are lazy-imported** inside endpoint functions (`from ..services.xxx import yyy`)
5. **Routers are THIN** — they validate input, call service, return result. Zero business logic
6. **Error handling:** `HTTPException(404)` for not found, let services raise for business errors

### Router Registration Checklist

When you add a new router:

1. Create `server/routers/my_domain.py`
2. Add to `server/routers/__init__.py`:
   ```python
   from .my_domain import router as my_domain_router
   ```
3. Add to `__all__` list in `__init__.py`
4. Add to `server/main.py`:
   ```python
   from .routers import my_domain_router
   # ...
   app.include_router(my_domain_router)
   ```

### Service

**Location:** `server/services/{domain_name}_{concern}.py`
**Pattern:** Module-level functions (not classes) with SQLAlchemy

```python
"""
My Domain Database
==================

SQLAlchemy models and CRUD functions for my domain.
"""

from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

class MyItem(Base):
    __tablename__ = "my_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

# Engine/session setup (cached, thread-safe)
def _get_session():
    # ... (see workspace_database.py for the engine cache pattern)
    pass

# CRUD functions
def list_items(category=None):
    with _get_session() as session:
        query = session.query(MyItem)
        if category:
            query = query.filter_by(category=category)
        return [_to_dict(item) for item in query.all()]

def create_item(name, description=""):
    with _get_session() as session:
        item = MyItem(name=name, description=description)
        session.add(item)
        session.commit()
        return _to_dict(item)
```

### Rules

1. **Service files are named `{domain}_{concern}.py`:**
   - `workspace_database.py` — database CRUD
   - `workspace_chat_session.py` — chat session logic
   - `workspace_library.py` — file library management
2. **Services NEVER import from routers** — data flows one direction
3. **Services NEVER import from other domains' services** — if you need shared logic, create a shared utility in `server/utils/`
4. **SQLAlchemy models live in the service** that owns the table
5. **Use module-level functions, not classes** (consistent with existing pattern)
6. **Every service with cleanup needs exposes a `cleanup_*()` function** registered in `main.py` lifespan

---

## Adding a New Mechanism — The Checklist

When you build something new, follow this exact sequence:

### Step 1: Define the Domain Name

Pick a short, clear name. This name flows through every layer:

| Domain Name | Router Prefix | Component Folder | Hook File | Service Files |
|-------------|---------------|-------------------|-----------|---------------|
| `dunkstack` | `/api/dunkstack` | `dunkstack/` | `useDunkStack.ts` | `dunkstack_*.py` |
| `role-library` | `/api/workspace/roles` | (in workspace/) | `useRoleLibrary.ts` | (in workspace_database.py) |
| `yt-lab` | `/api/yt/*` | `yt-lab/` | (multiple) | `yt_*.py` |

### Step 2: Backend First

```
1. server/services/{domain}_database.py    ← SQLAlchemy models + CRUD
2. server/services/{domain}_session.py     ← Session/business logic (if needed)
3. server/routers/{domain}.py              ← FastAPI router with Pydantic schemas
4. server/routers/__init__.py              ← Register import
5. server/main.py                          ← Include router + cleanup
```

### Step 3: API Bridge

```
6. ui/src/lib/types.ts                     ← Add TypeScript interfaces
7. ui/src/lib/api.ts                       ← Add typed fetch functions
```

### Step 4: Frontend

```
8.  ui/src/hooks/use{Domain}.ts            ← React Query or Stateful hook
9.  ui/src/components/{domain}/            ← Domain components (3+ files)
10. ui/src/pages/{Domain}Page.tsx           ← Page composition (if new page)
11. ui/src/App.tsx                          ← Add route (if new page)
```

### Step 5: Verify Isolation

Ask yourself:
- Can I delete the entire `components/{domain}/` folder without breaking other domains? **Must be yes.**
- Can I delete the hook file without breaking other domains? **Must be yes.**
- Can I delete the service files without breaking other services? **Must be yes.**
- If I copy these files to another project, do they work standalone? **Must be yes.**

---

## Naming Conventions Summary

| What | Convention | Example |
|------|-----------|---------|
| Page file | `{Domain}Page.tsx` | `DunkStackPage.tsx` |
| Component folder | `{domain}/` (kebab-case) | `dunkstack/` |
| Component file | `{DomainPrefix}{Name}.tsx` | `DunkStackCommsChat.tsx` |
| Hook file | `use{Domain}.ts` | `useDunkStack.ts` |
| API function | `{verb}{Domain}{Entity}` | `dunkstackReadConfig()` |
| Type interface | `{Entity}` / `{Entity}Create` / `{Entity}Update` | `RoleBlueprint` |
| Router file | `{domain_name}.py` (snake_case) | `dunkstack.py` |
| Router prefix | `/api/{domain-name}` | `/api/dunkstack` |
| Service file | `{domain}_{concern}.py` | `workspace_database.py` |
| SQLAlchemy table | `{domain}_{entities}` | `workspace_conversations` |

---

## Cross-Domain Communication

Sometimes two domains need to talk. The ONLY allowed patterns:

### Pattern 1: Shared Hook Import (Frontend)

A page can import hooks from multiple domains. That's the page's job — composition.

```tsx
// ✅ Page imports from two domains
import { useDunkStack } from '@/hooks/useDunkStack'
import { useProjects } from '@/hooks/useProjects'

export function DunkStackPage() {
  const { tokenState } = useDunkStack()
  const { data: projects } = useProjects()   // Cross-domain, but through the page
}
```

### Pattern 2: Shared Utility (Backend)

If two services need the same logic, extract to `server/utils/`:

```
server/utils/
├── project_helpers.py    ← Path resolution used by many routers
├── process_utils.py      ← Process management shared utilities
└── validation.py         ← Input validation shared logic
```

### What's NOT Allowed

```python
# ❌ Service importing from another domain's service
from ..services.workspace_database import get_conversation  # NO
```

```tsx
// ❌ Component importing from another domain's component
import { DunkStackGauge } from '@/components/dunkstack/DunkStackContextGauge'  // NO from yt-lab component
```

```tsx
// ❌ Hook importing from another domain's hook
import { useDunkStack } from '@/hooks/useDunkStack'  // NO from inside useWorkspaceChat
```

---

## Shared Components (The Lego Shelf)

These components live at `ui/src/components/` (top level) and can be used by ANY page:

| Component | Purpose |
|-----------|---------|
| `ThemeSelector.tsx` | Theme picker dropdown |
| `Terminal.tsx` / `TerminalTabs.tsx` | xterm.js terminal |
| `KanbanBoard.tsx` / `KanbanColumn.tsx` | Drag-and-drop board |
| `DependencyGraph.tsx` | Node graph visualization |
| `ProjectSelector.tsx` | Project dropdown |
| `FolderBrowser.tsx` | Filesystem browser |
| `ConfirmDialog.tsx` | Confirmation modal |
| `CelebrationOverlay.tsx` | Confetti on completion |
| `SettingsModal.tsx` | Global settings |

**Rule:** If a component is used by 2+ pages, it graduates from a domain folder to the top level.

---

## The Extraction Test

Before you consider your module "done," verify it passes the extraction test:

> **If I wanted to ship this module as its own standalone micro-app, what would I need to copy?**

The answer should ALWAYS be:
1. The service file(s) — `server/services/{domain}_*.py`
2. The router file — `server/routers/{domain}.py`
3. The hook file — `ui/src/hooks/use{Domain}.ts`
4. The component folder — `ui/src/components/{domain}/`
5. The relevant types from `types.ts`
6. The relevant API functions from `api.ts`

If you also need to copy files from other domains, **you've broken the architecture.** Fix it.

---

## Design System

- **Framework:** Tailwind CSS v4 with `@theme` directive
- **Style:** Neobrutalism
- **CSS Variables:** Defined in `ui/src/styles/globals.css`
- **Color tokens:** `--color-neo-pending`, `--color-neo-progress`, `--color-neo-done`
- **Animations:** `animate-slide-in`, `animate-pulse-neo`, `animate-shimmer`
- **UI Primitives:** Radix UI wrapped in `ui/src/components/ui/`
- **Icons:** Lucide React

All new components use these tokens and primitives. Never hardcode colors.

---

## Quick Reference: File Locations

```
ui/src/
├── pages/              ← Layer 1: Page shells
├── components/
│   ├── {domain}/       ← Layer 2: Domain components
│   ├── ui/             ← Radix UI primitives
│   └── *.tsx           ← Shared components (Lego shelf)
├── hooks/              ← Layer 3: State bridges
├── lib/
│   ├── api.ts          ← Layer 4: API client
│   └── types.ts        ← Layer 4: Type definitions
└── styles/
    └── globals.css     ← Design tokens

server/
├── routers/            ← Layer 5a: HTTP/WS handlers
│   └── __init__.py     ← Router registry
├── services/           ← Layer 5b: Business logic + DB
├── utils/              ← Shared utilities (cross-domain OK)
├── schemas.py          ← Shared Pydantic models
└── main.py             ← App setup + router registration
```

---

## TL;DR

1. **Every mechanism = 5 layers** (Page → Components → Hook → API → Backend)
2. **Every layer is self-contained** — no reaching across domains
3. **Pages compose, hooks bridge, services compute** — each does ONE thing
4. **The extraction test must pass** — you can copy any domain out as standalone
5. **Follow the naming conventions** — consistency makes the codebase scannable
6. **New mechanism? Follow the 10-step checklist** above, every time
