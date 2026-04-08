# Spec 003 — Skin + Hinge System

## What This Is
The **Skin** is a branded React shell that sits in front of Activepieces. Clients see your product — not a builder. The **Hinge** is an admin-only flag that reveals the builder underneath so you can edit the pipeline in minutes. The client never sees the hinge.

The analogy: it's like a mobile home with a skirt. The skirt hides the foundation from view. When you need to work on the foundation, you lift the skirt panel, do the work, and put it back. The house looks finished from the outside the whole time.

## Why It Matters
Without the skin, clients see an automation builder. With it, they see YOUR product. This is the difference between "here's a tool you can use" and "here's a product I built for you." Same pipeline underneath. Completely different perception. This is also how you ship client work fast — one pipeline, many skins.

---

## The Skin Template

Build this once. Reuse it for every client or product. Change logo, colors, domain.

### File Structure
```
skin/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Root — routes between skin and builder mode
│   ├── api.ts                # All calls to Activepieces API go here
│   ├── auth/
│   │   ├── LoginPage.tsx     # Uses AP's user system
│   │   └── useAuth.ts        # Auth hook
│   ├── pages/
│   │   ├── DashboardPage.tsx # Main client-facing page
│   │   └── [product-pages]   # Whatever your tool needs
│   └── components/
│       ├── CoPilotPanel.tsx  # AI co-pilot chat (from Spec 002)
│       └── [brand-components]
├── public/
│   └── logo.svg              # Replace per deployment
├── .env
├── .env.example
├── vite.config.ts
├── tailwind.config.ts
└── Dockerfile
```

### `.env.example`
```bash
# Activepieces connection
VITE_AP_BASE_URL=http://localhost:8080
VITE_AP_PROJECT_ID=your_project_id

# Skin behavior
VITE_BUILDER_MODE=false        # true = show builder (admin only, never for clients)
VITE_PRODUCT_NAME=Your Product Name
VITE_PRODUCT_LOGO=/logo.svg

# Branding (overridden by Skin Builder output — see Spec 007)
VITE_PRIMARY_COLOR=#000000
VITE_ACCENT_COLOR=#FF6B00
```

### `App.tsx` — The Hinge Logic
```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'

const BUILDER_MODE = import.meta.env.VITE_BUILDER_MODE === 'true'

export default function App() {
  if (BUILDER_MODE) {
    // Admin mode: embed the full Activepieces builder in an iframe
    return (
      <div className="h-screen w-screen">
        <div className="bg-yellow-400 text-black text-sm px-4 py-1 font-bold">
          ADMIN MODE — Builder visible. Clients cannot see this.
        </div>
        <iframe
          src={import.meta.env.VITE_AP_BASE_URL}
          className="w-full"
          style={{ height: 'calc(100vh - 28px)' }}
        />
      </div>
    )
  }

  // Client mode: show your branded skin
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### `api.ts` — Calls Activepieces Under the Hood
```typescript
const AP_BASE = import.meta.env.VITE_AP_BASE_URL
const PROJECT_ID = import.meta.env.VITE_AP_PROJECT_ID

async function apFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('ap_token')
  return fetch(`${AP_BASE}/api/v1${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  })
}

export async function runFlow(flowId: string, payload: Record<string, unknown>) {
  const resp = await apFetch('/flow-runs', {
    method: 'POST',
    body: JSON.stringify({ flowId, projectId: PROJECT_ID, payload })
  })
  return resp.json()
}

export async function getFlowStatus(runId: string) {
  const resp = await apFetch(`/flow-runs/${runId}`)
  return resp.json()
}
```

---

## The Hinge System — How It Works

### What "The Hinge" Is
An environment variable: `VITE_BUILDER_MODE=true/false`

When `false` (default): client sees your skin.
When `true` (admin only): the full Activepieces builder renders in an iframe inside the skin. A yellow admin banner appears so you know you're in builder mode.

### Hinge Workflow for Making Changes

1. **You get a change request** (from a client, or you think of something)
2. Stop the skin dev server (or in production: update env var)
3. Set `VITE_BUILDER_MODE=true`
4. Start/restart the skin server
5. Open the skin URL — you see the Activepieces builder
6. Make changes to the pipeline in the builder (which saves to the blueprint JSON)
7. Set `VITE_BUILDER_MODE=false`
8. Restart skin server
9. Client opens the URL — sees the updated skin with updated pipeline behavior

**In development:** Just toggle an env var. Takes 5 seconds.
**In production:** Can be a config file flag or environment variable in your deployment.

### Optional: Admin Toggle Button
For faster iteration, add a hidden admin toggle (not visible to clients):

```tsx
// In App.tsx — only renders if admin secret in localStorage
const isAdmin = localStorage.getItem('admin_secret') === import.meta.env.VITE_ADMIN_SECRET

{isAdmin && (
  <button
    onClick={() => setBuilderMode(!builderMode)}
    className="fixed bottom-4 right-4 opacity-20 hover:opacity-100"
  >
    {builderMode ? 'Hide Builder' : 'Show Builder'}
  </button>
)}
```

---

## Using the Skin as a Template (Per-Client / Per-Product)

### How to Deploy a New Instance
```bash
# Copy the skin template
cp -r skin/ my-client-tool/

# Update branding
cd my-client-tool
# Edit .env: set PRODUCT_NAME, PRODUCT_LOGO, colors
# Replace public/logo.svg with client logo
# Or run Skin Builder (Spec 007) for full auto-theming from a screenshot

# Point at the right AP instance
# Edit .env: set VITE_AP_BASE_URL to your AP instance for this client

# Deploy
docker build -t my-client-tool .
docker run -p 3000:80 my-client-tool
```

Each client gets:
- Their own Activepieces instance (separate docker-compose) OR a separate project in a shared instance
- Their own skin deployment (separate domain/subdomain)
- Their own `.env` with their branding and AP URL

The pipeline blueprints live in the Activepieces instance. The skin just connects to them.

---

## What the Client Sees vs What You See

| View | What's There | URL |
|------|-------------|-----|
| Client view | Your branded product, no builder visible | `yourclient.com` |
| Admin/edit view | Full Activepieces builder in iframe | `yourclient.com` (with BUILDER_MODE=true) |
| Builder direct URL | Raw Activepieces UI | `localhost:8080` (internal only, never shared) |

---

## Success Criteria

- [ ] Skin template runs and shows branded UI (logo, colors, product name from `.env`)
- [ ] `VITE_BUILDER_MODE=false` → client sees branded skin only, no builder visible
- [ ] `VITE_BUILDER_MODE=true` → builder iframe appears with yellow admin banner
- [ ] `api.ts` successfully triggers a flow run and returns status
- [ ] Copying skin template + changing `.env` branding = new deployment in under 10 minutes
- [ ] Skin Builder (Spec 007) output (CSS stylesheet) applies to the skin template correctly
