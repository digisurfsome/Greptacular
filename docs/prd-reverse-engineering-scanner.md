# Agent OS Blueprint: Reverse Engineering Scanner

**Status:** Draft
**Date:** 2026-03-04
**Author:** Owner + Claude (Session 10)
**Depends on:** Factory Controller (built), Registry (built), Subscription Auth (built)
**Implementation:** 6 phases, each under 50% context window

---

## STANDARDS LAYER

### Technology Stack
- **Backend:** Python 3.11+ with FastAPI, Pydantic models, async/await
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS v4, TanStack Query (React Query)
- **Data Storage:** JSON file (`~/.autoforge/re_queue.json`) for queue, output specs saved per-scan
- **Real-time:** WebSocket events via existing `server/websocket.py` broadcast pattern
- **Web Scanning Engine:** [Browser Use](https://github.com/browser-use/browser-use) (MIT licensed, Python, connects to Claude API)
- **Mobile Scanning Engine:** ADB (Android Debug Bridge) controlling LDPlayer emulator
- **AI Model:** Claude Sonnet 4.6 via subscription (`force_subscription=True`) — vision-capable for screenshot analysis
- **Screenshot Analysis:** Claude's vision API reads screenshots, identifies UI components, navigation elements

### Architecture Patterns
- **Services** live in `server/services/` — one file per domain (`re_scanner.py`, `re_queue_store.py`)
- **Routers** live in `server/routers/` — thin REST layer, Pydantic request/response models
- **React hooks** in `ui/src/hooks/` — wrap TanStack Query `useQuery`/`useMutation`
- **UI components** in `ui/src/components/scanner/` — new directory for scanner UI
- **Scan output** stored in `~/.autoforge/scans/{scan_id}/` — screenshots, spec, metadata
- **Registration** — new routers registered in `server/routers/__init__.py` AND `server/main.py`

### Key Existing Code to Understand
| File | What It Does | Why It Matters |
|---|---|---|
| `registry.py` → `get_effective_sdk_env()` | Auth for Claude API calls | Scanner uses subscription auth, not API key |
| `.claude/references/subscription-billing-pattern.md` | Full auth pattern docs | Follow Use Case 1 (prompt-in/text-out) for analysis |
| `server/services/task_queue_store.py` | JSON queue storage pattern | RE queue follows same pattern |
| `server/routers/task_queue.py` | Queue REST API pattern | RE queue API follows same structure |
| `server/services/factory_controller.py` | Agent lifecycle management | Pattern for managing long-running scan processes |
| `server/websocket.py` | WebSocket broadcast pattern | Live scan status updates |
| `ui/src/components/factory/TaskQueuePanel.tsx` | Queue UI pattern | RE queue UI follows same structure |

### Coding Conventions
- Python: ruff-clean, type hints on public methods, `logging.getLogger(__name__)`
- TypeScript: ESLint-clean, `interface` for data shapes, `type` for unions
- Tailwind: semantic tokens (`bg-card`, `text-foreground`, `border-border`), no hardcoded colors
- Pydantic: `BaseModel` for all request/response schemas, `Optional` with `Field` for validation
- File I/O: always handle missing dirs (`mkdir(parents=True, exist_ok=True)`), corrupted JSON (reset to default), OS errors (log and continue)
- Commits: conventional commits (`feat:`, `fix:`, `docs:`), directly to `main`

### Quality Standards
- `cd ui && npm run build` must pass (TypeScript + build)
- `ruff check .` must pass (Python linting)
- No hardcoded paths — use `Path.home() / ".autoforge"` for global
- All UI must work with existing themes (no custom colors, use semantic tokens)
- WebSocket events must follow existing `{"type": "...", "data": {...}}` pattern

### Dependencies to Install
| Package | Purpose | Install |
|---|---|---|
| `browser-use` | Web app scanning engine | `pip install browser-use` |
| `playwright` | Browser automation (used by browser-use) | `pip install playwright && playwright install chromium` |
| `Pillow` | Screenshot processing / image handling | `pip install Pillow` |

**ADB** comes bundled with LDPlayer (no separate install). The scanner calls ADB commands via `subprocess`.

---

## PRODUCT LAYER

### Vision

**A reverse engineering queue where you point it at any web app or mobile app, and it maps every screen, every flow, every component — outputting a structural spec you can feed into AutoForge.**

This is a SEPARATE queue from the main Task Queue ("The Train"). The main queue builds/debugs/refactors apps — that's heavy work, hours per task, backed up for weeks. The RE queue scans apps — that's fast work, 15-30 minutes per scan. They run independently so scans don't wait behind builds.

### Target User
- Non-coder owner who wants to model apps after existing ones
- Needs structural blueprints (page maps, navigation flows, component inventories)
- Already has AutoForge for building — needs the "what to build" input
- Has 60-70 projects, many modeled after existing apps in the market

### Core Concept

```
RE QUEUE (separate from Task Queue)
┌─────────────────────────────────────────────────────────────┐
│  1. 🌐 Fig website         web     full_scan    RUNNING    │
│  2. 📱 Fig mobile app      mobile  full_scan    QUEUED     │
│  3. 🌐 CompetitorSaaS.com  web     onboarding   QUEUED     │
│  4. 📱 FitnessApp          mobile  full_scan    QUEUED     │
│  5. 🌐 CoolLandingPage.io  web     landing_only QUEUED     │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions
1. **Separate queue from Task Queue** — RE scans are fast (15-30 min), coding tasks are slow (hours). Don't mix them.
2. **Two scan backends** — Browser Use for web apps, ADB + LDPlayer for mobile apps. Same output format.
3. **Subscription auth** — uses `force_subscription=True` for all Claude vision calls. Zero API cost.
4. **Output = AutoForge-ready spec** — scan output can be directly used as input for AutoForge app_spec.
5. **Sequential scanning** — one scan at a time to avoid rate limit conflicts with other AutoForge services.
6. **LDPlayer for mobile** — free, lightweight, has ADB built in, best automation support.
7. **Appetize.io as optional backend** — cloud browser-based emulator, configured per-scan. Future enhancement.

### Use Cases
1. **Competitive Analysis** — Scan a competitor's web app, get full structural breakdown
2. **Mobile App Modeling** — Scan a mobile app via emulator, map every screen for your own version
3. **Onboarding Study** — Scan just the signup/onboarding flow of an app
4. **Landing Page Analysis** — Capture a landing page's structure, CTAs, sections
5. **Batch Research** — Queue 10 apps in a category, scan them all overnight, compare structures
6. **AutoForge Pipeline** — Scan → spec → feed into AutoForge → build your version

### How Scanning Works

#### Web App Scanning (Browser Use)

```
1. Browser Use opens Chrome (headless or headed)
2. Navigates to target URL
3. Claude vision analyzes the page:
   - What components are visible?
   - What navigation options exist?
   - What is the page structure/layout?
4. Screenshots the page
5. Claude decides what to click next (nav items, buttons, links)
6. Browser Use clicks → new page loads
7. Repeat until all reachable pages are mapped
8. Output: screenshots/ + structural spec
```

Browser Use handles the browser automation. Claude Sonnet 4.6 (with vision) handles the analysis and navigation decisions. The scanner service orchestrates the loop.

#### Mobile App Scanning (ADB + LDPlayer)

```
1. LDPlayer must be running with target app installed
2. Scanner connects via ADB (adb connect localhost:5555)
3. Takes screenshot: adb exec-out screencap -p > screen.png
4. Claude vision analyzes the screenshot:
   - What screen is this?
   - What UI elements are visible?
   - What should we tap next?
5. Claude returns tap coordinates
6. Scanner sends tap: adb shell input tap X Y
7. Waits for screen to settle (500ms)
8. Repeat until all screens mapped
9. Output: screenshots/ + structural spec
```

ADB provides the "hands" (tap, swipe, screenshot). Claude provides the "brain" (what am I looking at, what should I tap next). The scanner service orchestrates the loop.

### Output Format

Each completed scan produces a folder:

```
~/.autoforge/scans/{scan_id}/
├── metadata.json              # Scan config, timestamps, status
├── screenshots/
│   ├── 001_splash_screen.png
│   ├── 002_login_page.png
│   ├── 003_home_screen.png
│   ├── 004_search_results.png
│   └── ...
├── analysis/
│   ├── page_map.md            # Every screen with description
│   ├── navigation_flow.md     # How screens connect (A → B → C)
│   ├── component_inventory.md # All UI components found
│   └── onboarding_flow.md     # Signup/onboarding steps (if applicable)
└── spec/
    └── structural_spec.txt    # AutoForge-compatible app_spec format
```

#### page_map.md Example
```markdown
## Screen 1: Splash Screen
- **Type:** Loading/splash
- **Components:** Logo (centered), tagline text, loading spinner
- **Navigation:** Auto-advances to Screen 2 after 2 seconds
- **Screenshot:** 001_splash_screen.png

## Screen 2: Login Page
- **Type:** Authentication
- **Components:** Email input, password input, "Sign In" button, "Sign Up" link, "Forgot Password" link, social login buttons (Google, Apple)
- **Navigation:** "Sign In" → Screen 3 (Home), "Sign Up" → Screen 7 (Registration)
- **Screenshot:** 002_login_page.png
```

#### structural_spec.txt Example (AutoForge-Ready)
```xml
<app_spec>
  <overview>
    <name>Sugar Tracker (modeled after Fig)</name>
    <description>Barcode-scanning app for tracking sugar content in foods</description>
    <tech_stack>Flutter, Firebase, Barcode Scanner API</tech_stack>
  </overview>
  <pages>
    <page name="Splash Screen" route="/">
      <components>Logo, Tagline, Loading Spinner</components>
      <behavior>Auto-navigate to Login after 2s</behavior>
    </page>
    <page name="Login" route="/login">
      <components>Email Input, Password Input, Sign In Button, Social Login (Google, Apple), Sign Up Link</components>
      <behavior>Authenticate user, redirect to Home on success</behavior>
    </page>
    <!-- ... all pages ... -->
  </pages>
  <navigation_flow>
    Splash → Login → Home → Scanner → Results → Product Detail
    Home → Search → Results → Product Detail
    Home → Profile → Settings
    Home → History → Product Detail
  </navigation_flow>
</app_spec>
```

---

## SPECS LAYER

### Data Model: Scan Job

```python
# Stored in ~/.autoforge/re_queue.json as a list
{
  "scans": [
    {
      "id": "uuid-string",
      "position": 1,                       # Queue order
      "status": "queued",                   # queued | scanning | completed | failed | paused
      "platform": "web",                    # web | mobile
      "target": "https://fig.co",           # URL for web, app name for mobile
      "scope": "full_scan",                 # full_scan | onboarding | landing_only | custom
      "custom_instructions": "",            # Extra directions for the AI scanner
      "login_required": false,              # Does the target need login?
      "login_notes": "",                    # "Use test@email.com / password123"
      "emulator": "ldplayer",              # ldplayer | appetize (mobile only)
      "output_name": "fig-analysis",        # Human-friendly name for output folder
      "model": "claude-sonnet-4-6",         # Model for vision analysis
      "max_pages": 50,                      # Safety limit on pages to scan
      "created_at": "2026-03-04T...",
      "started_at": null,
      "completed_at": null,
      "pages_found": 0,                    # Tracked during scan
      "screenshots_taken": 0,              # Tracked during scan
      "error": null,
      "output_dir": null,                  # Set when scan starts
      "notes": ""
    }
  ],
  "queue_status": "idle",                  # idle | scanning | paused
  "total_scans_completed": 0
}
```

### API Endpoints

All endpoints on a new router: `server/routers/re_scanner.py`
Prefix: `/api/re-scanner`

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/re-scanner` | — | Get full queue (all scans + queue_status) |
| `POST` | `/api/re-scanner/scans` | `ScanCreateRequest` | Add a new scan to the queue |
| `PUT` | `/api/re-scanner/scans/{scan_id}` | `ScanUpdateRequest` | Edit a scan |
| `DELETE` | `/api/re-scanner/scans/{scan_id}` | — | Remove a scan from the queue |
| `POST` | `/api/re-scanner/scans/reorder` | `ReorderRequest` | Reorder scans |
| `POST` | `/api/re-scanner/start` | — | Start processing the queue |
| `POST` | `/api/re-scanner/stop` | — | Stop scanning (finish current page) |
| `POST` | `/api/re-scanner/pause` | — | Pause between scans |
| `POST` | `/api/re-scanner/resume` | — | Resume paused queue |
| `GET` | `/api/re-scanner/scans/{scan_id}/output` | — | Get scan output (spec, screenshots list) |
| `GET` | `/api/re-scanner/scans/{scan_id}/screenshots/{filename}` | — | Serve a screenshot image |

#### Pydantic Models

```python
class ScanCreateRequest(BaseModel):
    platform: str = "web"                    # web | mobile
    target: str                              # URL or app name
    scope: str = "full_scan"                 # full_scan | onboarding | landing_only | custom
    custom_instructions: str = ""
    login_required: bool = False
    login_notes: str = ""
    emulator: str = "ldplayer"               # ldplayer | appetize (mobile only)
    output_name: str = ""                    # Auto-generated from target if empty
    model: str = "claude-sonnet-4-6"
    max_pages: int = 50
    notes: str = ""

class ScanUpdateRequest(BaseModel):
    platform: Optional[str] = None
    target: Optional[str] = None
    scope: Optional[str] = None
    custom_instructions: Optional[str] = None
    login_required: Optional[bool] = None
    login_notes: Optional[str] = None
    emulator: Optional[str] = None
    output_name: Optional[str] = None
    model: Optional[str] = None
    max_pages: Optional[int] = None
    notes: Optional[str] = None

class ReorderRequest(BaseModel):
    scan_ids: list[str]

class ScanResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
```

### Scanner Service

`server/services/re_scanner.py` — the core scanning engine.

```python
class REScanner:
    """Reverse engineering scanner with web and mobile backends."""

    async def start_queue(self):
        """Start processing scan queue sequentially."""
        # 1. Load queue from re_queue_store
        # 2. Find first scan with status=queued
        # 3. Set queue_status = "scanning"
        # 4. Call _execute_scan(scan)
        # 5. On completion, mark done, pull next
        # 6. On queue empty, set queue_status = "idle"

    async def stop(self):
        """Stop after current page finishes."""

    async def _execute_scan(self, scan: dict):
        """Route to web or mobile scanner based on platform."""
        if scan["platform"] == "web":
            await self._scan_web(scan)
        else:
            await self._scan_mobile(scan)

    async def _scan_web(self, scan: dict):
        """Web app scanning using Browser Use."""
        # 1. Create output directory: ~/.autoforge/scans/{scan_id}/
        # 2. Initialize Browser Use agent with Claude Sonnet
        # 3. Navigate to target URL
        # 4. Loop:
        #    a. Screenshot current page
        #    b. Send screenshot to Claude vision: "What is this page? What components do you see? What navigation options exist?"
        #    c. Save screenshot with descriptive name
        #    d. Save page analysis to running document
        #    e. Ask Claude: "What should I click next to see a new screen?"
        #    f. Browser Use clicks the element
        #    g. Track visited URLs to avoid duplicates
        #    h. Stop when: max_pages reached OR no new pages found OR scope completed
        # 5. Generate spec from accumulated analysis
        # 6. Save all output files

    async def _scan_mobile(self, scan: dict):
        """Mobile app scanning using ADB + emulator."""
        # 1. Create output directory
        # 2. Verify ADB connection: subprocess.run(["adb", "devices"])
        # 3. Loop:
        #    a. Screenshot: adb exec-out screencap -p > screenshot.png
        #    b. Send screenshot to Claude vision (same analysis prompt)
        #    c. Save screenshot with descriptive name
        #    d. Save page analysis
        #    e. Ask Claude: "What coordinates should I tap to see a new screen?"
        #    f. Send tap: subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
        #    g. Wait 500ms-1000ms for screen transition
        #    h. Compare new screenshot hash to previous to detect if screen changed
        #    i. Stop when: max_pages reached OR stuck (same screen 3x) OR scope completed
        # 4. Generate spec
        # 5. Save output

    async def _analyze_screenshot(self, screenshot_path: str, scan: dict) -> dict:
        """Send screenshot to Claude vision for analysis."""
        # Uses subscription auth pattern:
        # sdk_env = get_effective_sdk_env(force_subscription=True)
        # ClaudeSDKClient with vision prompt
        #
        # System prompt tells Claude:
        # "You are a UI analyst. Analyze this screenshot and return:
        #  1. Page name/type
        #  2. All visible components (buttons, inputs, text, images, navigation)
        #  3. Layout structure (header, sidebar, main content, footer)
        #  4. Available navigation actions (what can be clicked/tapped)
        #  5. Notable design patterns
        #  Return as structured JSON."
        #
        # Returns: { page_name, page_type, components[], layout, nav_actions[], design_notes }

    async def _decide_next_action(self, analysis: dict, visited: list, scan: dict) -> dict:
        """Ask Claude what to click/tap next."""
        # Prompt: "Given this page analysis and the pages already visited,
        #          what should I click next to discover a new screen?
        #          If this is a web app, return a CSS selector.
        #          If this is a mobile app, return tap coordinates {x, y}.
        #          If there are no more new pages to discover, return {done: true}."
        #
        # Returns: { action: "click", selector: "..." } or { action: "tap", x: 350, y: 715 } or { done: true }

    def _generate_spec(self, scan: dict, analyses: list[dict]) -> str:
        """Generate AutoForge-compatible structural spec from all page analyses."""
        # Takes all the individual page analyses
        # Calls Claude one final time with ALL analyses as context:
        # "Given these page analyses, generate:
        #  1. page_map.md — every screen documented
        #  2. navigation_flow.md — how screens connect
        #  3. component_inventory.md — all UI components
        #  4. structural_spec.txt — AutoForge app_spec XML format
        # The spec should be ready to use as input for building a similar app."
```

### ADB Helper Module

`server/services/adb_helper.py` — thin wrapper around ADB subprocess calls.

```python
class ADBHelper:
    """Wraps ADB commands for controlling Android emulator."""

    def __init__(self, device_address: str = "localhost:5555"):
        self.device = device_address

    def connect(self) -> bool:
        """Connect to emulator via ADB. Returns True if connected."""
        # subprocess.run(["adb", "connect", self.device])
        # Check output for "connected"

    def is_connected(self) -> bool:
        """Check if device is connected."""
        # subprocess.run(["adb", "devices"])
        # Check if self.device appears in output

    def screenshot(self, output_path: str) -> bool:
        """Take screenshot and save to local path."""
        # subprocess.run(["adb", "exec-out", "screencap", "-p"], capture stdout)
        # Write bytes to output_path
        # Returns True if successful

    def tap(self, x: int, y: int):
        """Tap at coordinates."""
        # subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        """Swipe gesture."""
        # subprocess.run(["adb", "shell", "input", "swipe", ...])

    def back(self):
        """Press back button."""
        # subprocess.run(["adb", "shell", "input", "keyevent", "4"])

    def home(self):
        """Press home button."""
        # subprocess.run(["adb", "shell", "input", "keyevent", "3"])

    def launch_app(self, package_name: str):
        """Launch an app by package name."""
        # subprocess.run(["adb", "shell", "monkey", "-p", package_name, "1"])

    def get_current_activity(self) -> str:
        """Get current foreground activity name."""
        # subprocess.run(["adb", "shell", "dumpsys", "activity", "activities"])
        # Parse output for current activity

    def get_screen_size(self) -> tuple[int, int]:
        """Get emulator screen dimensions."""
        # subprocess.run(["adb", "shell", "wm", "size"])
        # Parse "Physical size: 1080x1920"
```

### Queue Store

`server/services/re_queue_store.py` — JSON storage for scan queue. Same pattern as `task_queue_store.py`.

```python
class REQueueStore:
    """JSON-based storage for reverse engineering scan queue."""

    QUEUE_FILE = Path.home() / ".autoforge" / "re_queue.json"
    SCANS_DIR = Path.home() / ".autoforge" / "scans"

    def load(self) -> dict
    def save(self, data: dict)
    def add_scan(self, scan_data: dict) -> dict
    def update_scan(self, scan_id: str, updates: dict)
    def delete_scan(self, scan_id: str)
    def reorder_scans(self, scan_ids: list[str])
    def get_scan(self, scan_id: str) -> dict
    def get_next_queued(self) -> Optional[dict]
    def mark_scanning(self, scan_id: str)
    def mark_completed(self, scan_id: str, pages_found: int, screenshots_taken: int)
    def mark_failed(self, scan_id: str, error: str)
    def get_queue_status(self) -> str
    def set_queue_status(self, status: str)
    def get_scan_output_dir(self, scan_id: str) -> Path
    def create_scan_output_dir(self, scan_id: str) -> Path
```

### WebSocket Events

| Event Type | When | Data |
|---|---|---|
| `re_queue_started` | Queue begins processing | `{scan_count}` |
| `re_scan_started` | A scan begins | `{scan_id, target, platform}` |
| `re_scan_progress` | Page scanned within a scan | `{scan_id, page_name, pages_found, screenshots_taken}` |
| `re_scan_completed` | A scan finishes | `{scan_id, target, pages_found, output_dir}` |
| `re_scan_failed` | A scan fails | `{scan_id, target, error}` |
| `re_queue_completed` | All scans done | `{completed, failed, total}` |
| `re_queue_paused` | Queue was paused | `{current_scan_id}` |
| `re_queue_stopped` | Queue was stopped | `{completed_so_far}` |

### UI Components

#### REScannerPanel (new component)

Lives in `ui/src/components/scanner/REScannerPanel.tsx`. Displayed as a new top-level section/tab in the AutoForge UI.

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 REVERSE ENGINEERING SCANNER                    [+ Add]  │
├─────────────────────────────────────────────────────────────┤
│  ▶ 1. 🌐 fig.co              Web    Full Scan    SCANNING  │
│      Pages found: 12 | Screenshots: 12         ~5 min      │
│      [View Output] [Edit] [Remove]                          │
│                                                              │
│  ⏳ 2. 📱 Fig App             Mobile Full Scan    QUEUED    │
│      LDPlayer | Login required                              │
│      [Edit] [Remove]                                        │
│                                                              │
│  ⏳ 3. 🌐 competitor.com      Web    Onboarding   QUEUED    │
│      Signup flow only                                       │
│      [Edit] [Remove]                                        │
│                                                              │
│  ✅ 4. 🌐 coolapp.io          Web    Full Scan    COMPLETE  │
│      18 pages | 18 screenshots | 4 min                      │
│      [View Output] [Remove]                                 │
├─────────────────────────────────────────────────────────────┤
│  [▶ Start Queue]  [⏸ Pause]        3 queued | 1 complete   │
└─────────────────────────────────────────────────────────────┘
```

Features:
- Scan rows: platform icon (🌐/📱), target name, scope badge, status badge
- Running scan shows live progress (pages found, screenshots taken)
- Completed scans have "View Output" button
- Drag-to-reorder queued scans
- Start/Stop/Pause controls in footer

#### ScanFormModal (new component)

Modal for creating or editing a scan. `ui/src/components/scanner/ScanFormModal.tsx`.

Fields:
1. **Platform** — toggle pills: Web | Mobile
2. **Target** — text input (URL for web, app name for mobile)
3. **Scope** — pills: Full Scan | Onboarding Only | Landing Only | Custom
4. **Custom Instructions** — textarea (visible when scope=custom): "Focus on the checkout flow" etc.
5. **Login Required** — toggle
6. **Login Notes** — textarea (visible when login_required=true): "Use test@email.com / pass123"
7. **Emulator** — dropdown (visible when platform=mobile): LDPlayer | Appetize
8. **Output Name** — text input (auto-generated from target)
9. **Max Pages** — number input (default 50)
10. **Notes** — textarea
11. **Save / Cancel** buttons

#### ScanOutputModal (new component)

Modal for viewing completed scan output. `ui/src/components/scanner/ScanOutputModal.tsx`.

Features:
- Tab navigation: Page Map | Navigation Flow | Components | Spec
- Each tab renders the corresponding markdown file from the scan output
- Screenshot gallery with thumbnails — click to enlarge
- "Copy Spec" button — copies structural_spec.txt to clipboard
- "Use in AutoForge" button — creates a new AutoForge project with this spec as the app_spec

### React Hooks

In `ui/src/hooks/useREScanner.ts`:

```typescript
// Fetch the full queue
useREQueue()                 // GET /api/re-scanner, polls every 3s when scanning

// Scan CRUD
useCreateScan()              // POST /api/re-scanner/scans
useUpdateScan()              // PUT /api/re-scanner/scans/{id}
useDeleteScan()              // DELETE /api/re-scanner/scans/{id}
useReorderScans()            // POST /api/re-scanner/scans/reorder

// Queue controls
useStartREQueue()            // POST /api/re-scanner/start
useStopREQueue()             // POST /api/re-scanner/stop
usePauseREQueue()            // POST /api/re-scanner/pause
useResumeREQueue()           // POST /api/re-scanner/resume

// Scan output
useScanOutput(scanId)        // GET /api/re-scanner/scans/{id}/output
```

### API Client Functions

In `ui/src/lib/api.ts`, add:

```typescript
// RE Scanner API
export interface REScan {
  id: string
  position: number
  status: 'queued' | 'scanning' | 'completed' | 'failed' | 'paused'
  platform: 'web' | 'mobile'
  target: string
  scope: string
  custom_instructions: string
  login_required: boolean
  login_notes: string
  emulator: string
  output_name: string
  model: string
  max_pages: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  pages_found: number
  screenshots_taken: number
  error: string | null
  output_dir: string | null
  notes: string
}

export interface REQueueState {
  scans: REScan[]
  queue_status: string
  total_scans_completed: number
}

export const reScannerGet = () => fetchJSON<REQueueState>('/api/re-scanner')
export const reScannerCreateScan = (data: ScanCreateRequest) => fetchJSON('/api/re-scanner/scans', { method: 'POST', body: data })
export const reScannerUpdateScan = (scanId: string, data: ScanUpdateRequest) => fetchJSON(`/api/re-scanner/scans/${scanId}`, { method: 'PUT', body: data })
export const reScannerDeleteScan = (scanId: string) => fetchJSON(`/api/re-scanner/scans/${scanId}`, { method: 'DELETE' })
export const reScannerReorder = (scanIds: string[]) => fetchJSON('/api/re-scanner/scans/reorder', { method: 'POST', body: { scan_ids: scanIds } })
export const reScannerStart = () => fetchJSON('/api/re-scanner/start', { method: 'POST' })
export const reScannerStop = () => fetchJSON('/api/re-scanner/stop', { method: 'POST' })
export const reScannerPause = () => fetchJSON('/api/re-scanner/pause', { method: 'POST' })
export const reScannerResume = () => fetchJSON('/api/re-scanner/resume', { method: 'POST' })
export const reScannerGetOutput = (scanId: string) => fetchJSON(`/api/re-scanner/scans/${scanId}/output`)
```

---

## IMPLEMENTATION PHASES

Each phase is designed to be completed by ONE agent session staying under 50% context window. The agent reads this PRD (~15% context), reads existing code (~10-15% context), implements (~15-20% context), leaving buffer.

---

### Phase 1: RE Queue Store + ADB Helper

**Goal:** Create the backend data layer — JSON queue storage for scans and ADB helper for mobile control.

**Files to create:**
- `server/services/re_queue_store.py` — REQueueStore class
- `server/services/adb_helper.py` — ADBHelper class

**What to build:**

1. `REQueueStore` class with all methods from the Specs section above:
   - `load()`, `save()`, `add_scan()`, `update_scan()`, `delete_scan()`
   - `reorder_scans()`, `get_scan()`, `get_next_queued()`
   - `mark_scanning()`, `mark_completed()`, `mark_failed()`
   - `get_queue_status()`, `set_queue_status()`
   - `create_scan_output_dir()` — creates `~/.autoforge/scans/{scan_id}/screenshots/` and `analysis/` and `spec/` subdirs

2. `ADBHelper` class with all methods from the Specs section:
   - `connect()`, `is_connected()`, `screenshot()`, `tap()`, `swipe()`
   - `back()`, `home()`, `launch_app()`, `get_current_activity()`, `get_screen_size()`
   - All methods use `subprocess.run()` with `capture_output=True`
   - Handle ADB not found gracefully (log warning, return False)

**Pattern to follow:** `server/services/task_queue_store.py` for JSON storage pattern. `server/services/rate_limit_logger.py` for safe file I/O.

**Estimated context usage:** ~30%

---

### Phase 2: RE Scanner REST API

**Goal:** REST endpoints for scan CRUD and queue controls. No scanning execution yet.

**Files to create:**
- `server/routers/re_scanner.py` — REST router

**Files to modify:**
- `server/routers/__init__.py` — register `re_scanner_router`
- `server/main.py` — include `re_scanner_router`

**What to build:**
1. All 11 endpoints from the API table
2. Pydantic models: `ScanCreateRequest`, `ScanUpdateRequest`, `ReorderRequest`, `ScanResponse`
3. Each endpoint calls `REQueueStore` methods
4. Validation: URL format for web targets, platform enum validation
5. Screenshot serving endpoint: reads image from scan output dir, returns as `FileResponse`
6. Queue start/stop/pause/resume just set the `queue_status` field (execution is Phase 4)

**Pattern to follow:** `server/routers/task_queue.py` — same router prefix, Pydantic models, response wrapper.

**Estimated context usage:** ~30%

---

### Phase 3: RE Scanner UI — Queue List + Scan Form

**Goal:** React components for viewing, adding, editing, and reordering scans.

**Files to create:**
- `ui/src/components/scanner/REScannerPanel.tsx` — queue list view
- `ui/src/components/scanner/ScanFormModal.tsx` — create/edit scan modal
- `ui/src/hooks/useREScanner.ts` — React Query hooks

**Files to modify:**
- `ui/src/lib/api.ts` — add scanner API functions + TypeScript interfaces
- `ui/src/App.tsx` — add scanner panel as a new section/tab (below or alongside factory)
- `ui/src/lib/types.ts` — add REScan and REQueueState types

**What to build:**
1. **REScannerPanel** — list view per wireframe above
   - Platform icons (🌐 web, 📱 mobile)
   - Scope badges (Full Scan, Onboarding, Landing, Custom)
   - Status badges matching factory panel style
   - [+ Add] button → ScanFormModal
   - [View Output] for completed scans (opens output modal — Phase 5)
   - Footer with Start/Stop/Pause + queue summary

2. **ScanFormModal** — form per the Specs section
   - Platform toggle (Web/Mobile) — shows/hides mobile-only fields
   - Auto-generate output_name from target URL/app name
   - Scope pills with visual selection
   - Conditional fields (login notes, emulator dropdown)

3. **useREScanner hooks** — following `useTaskQueue.ts` patterns
   - `useREQueue()` — polls every 3s when scanning, 10s idle
   - CRUD mutations that invalidate queue query
   - Queue control mutations

4. **API functions** — in `api.ts`, matching the endpoint table

5. **App.tsx integration** — new section header "🔍 Reverse Engineering" with REScannerPanel

**Pattern to follow:** `TaskQueuePanel.tsx` for Tailwind styling, status badges. `useTaskQueue.ts` for hook structure.

**Estimated context usage:** ~40%

---

### Phase 4: Web Scanner Engine (Browser Use)

**Goal:** The core web scanning engine using Browser Use + Claude vision.

**Files to create:**
- `server/services/re_scanner.py` — REScanner class (web scanning only in this phase)

**Files to modify:**
- `server/routers/re_scanner.py` — wire start/stop to REScanner
- `requirements.txt` — add `browser-use`, `playwright`

**What to build:**

1. **REScanner class** with:
   - `start_queue()` — loads queue, processes scans sequentially
   - `stop()` — stops after current page
   - `_execute_scan()` — routes to web or mobile
   - `_scan_web()` — the core web scanning loop:

2. **Web scanning loop details:**
   ```
   a. Install/check browser-use and playwright chromium
   b. Create Browser Use agent with target URL
   c. Set up tracking: visited_urls set, page_analyses list
   d. For each page:
      - Browser Use navigates to page
      - Take screenshot via playwright
      - Save screenshot to output dir
      - Send screenshot to Claude via _analyze_screenshot()
      - Record analysis (page name, components, nav options)
      - Ask Claude for next action via _decide_next_action()
      - If no new pages to visit, break
      - If max_pages reached, break
   e. After loop: call _generate_spec() with all analyses
   f. Write output files (page_map.md, navigation_flow.md, etc.)
   ```

3. **Claude vision calls** using subscription auth:
   ```python
   sdk_env = get_effective_sdk_env(force_subscription=True)
   # Use ClaudeSDKClient with vision prompt
   # System prompt for analysis
   # Send screenshot as base64 in user message
   ```

4. **Spec generation** — final Claude call that takes ALL page analyses and produces the four output files

5. **WebSocket broadcasts** — emit `re_scan_started`, `re_scan_progress`, `re_scan_completed` events

**Key detail:** Browser Use has its own agent loop. The scanner can either:
- Use Browser Use's built-in agent (give it a task: "map every page of this website") and capture its output
- OR use Browser Use as a lower-level browser controller and run our own navigation loop

Start with Browser Use's built-in agent — it's simpler. If it doesn't give enough control, drop to the lower-level API in a follow-up.

**Pattern to follow:** `server/services/factory_controller.py` for async process management. `subscription-billing-pattern.md` for auth.

**Estimated context usage:** ~40%

---

### Phase 5: Mobile Scanner Engine (ADB + LDPlayer)

**Goal:** Mobile app scanning using ADB to control LDPlayer emulator.

**Files to modify:**
- `server/services/re_scanner.py` — add `_scan_mobile()` implementation

**What to build:**

1. **`_scan_mobile()` implementation:**
   ```
   a. Check ADB connection: adb_helper.connect()
   b. If not connected, fail with clear error: "LDPlayer not running or ADB not available"
   c. Get screen size for coordinate calculations
   d. Set up tracking: visited_activities set, page_analyses list
   e. For each screen:
      - Take screenshot: adb_helper.screenshot(path)
      - Send to Claude vision: _analyze_screenshot()
      - Record current activity: adb_helper.get_current_activity()
      - Track as visited
      - Ask Claude for next action: _decide_next_action()
      - Returns {action: "tap", x: 350, y: 715}
      - Execute: adb_helper.tap(x, y)
      - Wait 800ms for transition
      - Take new screenshot
      - Compare to previous (image hash or Claude comparison) to detect if screen changed
      - If same screen 3x in a row → try back button, then move on
      - If max_pages reached → break
   f. Generate spec from analyses
   g. Write output files
   ```

2. **Screen change detection:**
   - Simple: compare file sizes of consecutive screenshots (crude but fast)
   - Better: compute image hash (Pillow) and compare (if hash matches, screen didn't change)
   - Best: ask Claude "is this the same screen as before?" (costs tokens but most accurate)
   - Start with image hash, fall back to Claude if ambiguous

3. **Navigation intelligence for mobile:**
   - Mobile apps don't have URLs — track by activity name + screen hash
   - Common patterns to teach Claude:
     - Bottom navigation bar → tap each tab
     - Hamburger menu → open and tap each item
     - Back button → return to previous screen
     - Scroll down → reveal more content
   - Claude's system prompt includes these patterns

4. **Error handling:**
   - ADB disconnects mid-scan → retry connection 3x, then fail
   - App crashes → detect via activity change, relaunch app
   - Emulator not found → clear error message with setup instructions

**Estimated context usage:** ~35%

---

### Phase 6: Scan Output Viewer + AutoForge Integration

**Goal:** UI for viewing completed scan output, and a button to create an AutoForge project from a scan.

**Files to create:**
- `ui/src/components/scanner/ScanOutputModal.tsx` — output viewer
- `ui/src/components/scanner/ScreenshotGallery.tsx` — thumbnail grid with lightbox

**Files to modify:**
- `ui/src/components/scanner/REScannerPanel.tsx` — wire "View Output" button
- `ui/src/hooks/useREScanner.ts` — add `useScanOutput()` hook
- `ui/src/lib/api.ts` — add `reScannerGetOutput()` function
- `server/routers/re_scanner.py` — add output endpoint (returns spec files + screenshot list)
- `ui/src/hooks/useWebSocket.ts` — handle `re_scan_*` events for live updates

**What to build:**

1. **ScanOutputModal** — tabbed viewer:
   - **Page Map tab** — renders page_map.md as formatted HTML
   - **Navigation Flow tab** — renders navigation_flow.md
   - **Components tab** — renders component_inventory.md
   - **Spec tab** — shows structural_spec.txt with syntax highlighting
   - **Screenshots tab** — thumbnail grid, click to enlarge

2. **ScreenshotGallery** — grid of thumbnails:
   - Lazy-loaded images from `/api/re-scanner/scans/{id}/screenshots/{filename}`
   - Click thumbnail → full-size lightbox overlay
   - Screenshot name below each thumbnail (from page analysis)

3. **"Copy Spec" button** — copies structural_spec.txt content to clipboard

4. **"Use in AutoForge" button:**
   - Calls POST `/api/projects` with a new project name
   - Copies structural_spec.txt into the new project's `.autoforge/prompts/app_spec.txt`
   - Redirects user to the new project in the main AutoForge UI
   - Project is ready for AutoForge to build from the scanned spec

5. **Live scan progress in REScannerPanel:**
   - WebSocket events update the scanning row in real-time
   - Shows current page being analyzed
   - Updates pages_found and screenshots_taken counters

**Estimated context usage:** ~40%

---

## SUCCESS METRICS

- Owner can queue web and mobile app scans and walk away
- Web scans complete in 15-30 minutes per app
- Mobile scans complete in 15-30 minutes per app
- Output spec is detailed enough to build from
- "Use in AutoForge" creates a buildable project
- Queue runs independently from the main Task Queue
- Subscription auth — zero API cost for scanning
- UI updates in real-time as pages are discovered

## OUT OF SCOPE (For Now)

- Video recording of scan sessions
- iOS emulator support (iOS Simulator requires Mac + Xcode)
- Appetize.io cloud emulator integration (future enhancement)
- Parallel scanning (multiple scans at once)
- Automated app installation in emulator (user installs manually for now)
- Side-by-side comparison of two scans
- SaaS/multi-user version
- Scan scheduling (time-based automated rescans)
- Login automation (user logs in manually before scan, scanner continues from there)
