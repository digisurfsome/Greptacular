# Agent Brief 3: Generation Flow UI + Tool Manager UI

**Phases:** 5 + 6 from `docs/prd-video-to-tool-factory.md`
**Scope:** All React/TypeScript — no Python backend changes
**Estimated Tokens:** ~50-60k
**Dependencies:** Agent 1 must be complete (needs TypeScript types in types.ts)
**Can Run Parallel With:** Agent 2 (they don't touch the same files)

---

## ARCHITECTURE CONTEXT (read this first)

### What This System Is
A UI for turning strategy blueprints into Google Sheets tools. The backend (Agents 1+2) handles data models, blueprint generation, theming, and Sheet deployment. **This agent builds the React frontend** — the generation flow (user triggers blueprint creation) and the tool manager (browse/manage/re-theme tools).

### Where This Agent Fits
```
User clicks "Generate Tool" → ThemePicker → progress bar → preview → deploy confirmation → success
User clicks "From PRD" → upload/paste PRD → same flow as above
User visits /#/tools → tool grid → tool detail (blueprint, theme, history, settings)
```

### Tech Stack & Design System
- **React 19**, TypeScript, **Vite 7**, **Tailwind CSS v4**, **TanStack Query** (React Query), **Radix UI** (modals/dropdowns), **lucide-react** (icons)
- **Design:** Neobrutalism style defined in `ui/src/styles/globals.css` via `@theme` directive
- **Color tokens:** `--color-neo-pending` (yellow), `--color-neo-progress` (cyan), `--color-neo-done` (green)
- **Animations:** `animate-slide-in`, `animate-pulse-neo`, `animate-shimmer`
- **Layout patterns:** Follow `ui/WORKSPACE_STANDARDS.md` — breadcrumb bar, responsive grid, CRUD view flow (List → Detail → Create/Edit), loading/empty/error state patterns

### Step Type Badge Colors (used in BlueprintPreview and ChainVisualizer)
- **RESEARCH** → blue badge
- **GENERATION** → purple badge
- **ACTION** → orange badge
- **MANUAL** → yellow badge

### Two Entry Points (YouTube + PRD)
The generation flow has two entry points that converge into the same pipeline:
1. **"Generate from Video"** button — appears on YT Lab project detail when steps exist. Uses project's existing YTStrategyStep[] data.
2. **"From PRD"** button — NEW. Opens upload/paste modal. Calls `POST /api/tool-factory/upload-prd` (built by Agent 1). Returns PRDExtractionResult with structured steps. Then same flow: ThemePicker → progress → preview → deploy.

Both paths produce the same `SheetBlueprint` that gets previewed and deployed.

### TypeScript Types Available (Agent 1 added these to `ui/src/lib/types.ts`)
- `SheetBlueprint`, `ChainConfigRow`, `DetectedAPI` — blueprint data
- `GeneratedTool`, `ToolStatus` — tool registry data
- `ThemeConfig`, `ThemeColors`, `ThemeTypography`, `ThemeComponents` — theme data
- `StepType` — step classification (research/generation/action/manual)
- `PRDUpload`, `PRDExtractionResult` — PRD input data
- `IngestionSource` — youtube | prd_upload | manual

### Existing UI Patterns to Follow
- **`ui/src/components/yt-lab/VideoIngestPanel.tsx`** — panel component pattern with progress states
- **`ui/src/components/yt-lab/DiscoveryPanel.tsx`** — card layout with badges and scoring
- **`ui/src/components/DependencyGraph.tsx`** — reference for ChainVisualizer (node graph, but this is simpler — linear chain)
- **`ui/src/hooks/useProjects.ts`** — React Query hook patterns
- **`ui/src/lib/api.ts`** — API client pattern (same fetch wrapper, same error handling)
- **`ui/src/App.tsx`** — router setup, navigation structure

---

## STRIPE MINIONS CONTEXT

- **[ROBOT]** = Deterministic code. No LLM calls. Pure React components, hooks, API calls.
- **[AGENT]** = Would require LLM. **Not applicable to this agent** — UI code is 100% [ROBOT].

**This entire agent is [ROBOT].** All React components, hooks, and API functions are deterministic TypeScript. No Claude calls in the frontend.

---

## WHAT TO BUILD

### Phase 5: Generation Flow UI

The flow starts when a user has a completed YT Lab project (or uploaded PRD) and wants to turn it into a Google Sheets tool.

#### 5.1 Generation Flow — UX Diagram

```
YT Lab Project Detail (existing page)
  ↓ User clicks "Generate Tool" button          ← GenerateToolButton.tsx
  ↓ OR User clicks "From PRD" button             ← PRDUploadButton.tsx (NEW)
ThemePicker modal opens                          ← ThemePicker.tsx
  ↓ User picks theme (preset / upload image / skip)
GenerationProgress overlay                       ← GenerationProgress.tsx
  ↓ SSE stream shows pipeline steps completing
BlueprintPreview full-screen                     ← BlueprintPreview.tsx
  ↓ User reviews chain, can edit inline
DeployConfirmation modal                         ← DeployConfirmation.tsx
  ↓ User confirms → Google OAuth if not connected
DeploymentSuccess screen                         ← DeploymentSuccess.tsx
  ↓ Link to Google Sheet, generate another option
```

#### 5.2 Components — `ui/src/components/tool-factory/`

**All components are [ROBOT].**

| Component | Purpose | Key Props/State |
|-----------|---------|-----------------|
| `GenerateToolButton.tsx` | Entry point in YT Lab project view. Blue button with sparkle icon. Disabled if project has no steps. | `projectId: string`, `stepCount: number` |
| `PRDUploadButton.tsx` | **NEW — not in original PRD.** "From PRD" button next to Generate Tool. Opens file picker for .md/.txt upload, or paste-in textarea. | `onUploadComplete: (result: PRDExtractionResult) => void` |
| `ThemePicker.tsx` | Modal: grid of 10 preset theme cards + "Upload Screenshot" button + "Skip" option + "Custom" option. | `onSelect: (theme: ThemeConfig \| null) => void`, `onClose: () => void` |
| `ThemePreviewCard.tsx` | Single card in ThemePicker grid. Shows color swatches, font names, style classification badge. Hover → expanded preview. | `theme: ThemeConfig`, `selected: boolean`, `onClick: () => void` |
| `GenerationProgress.tsx` | Full-screen overlay with progress steps. Connects to SSE endpoint. Shows: "Classifying steps... Detecting APIs... Converting prompts... Assembling blueprint..." with checkmarks as each completes. | `projectId: string`, `theme: ThemeConfig \| null`, `onComplete: (blueprint: SheetBlueprint) => void` |
| `BlueprintPreview.tsx` | Full blueprint review. Shows chain as a vertical flow with step cards. Each card: title, type badge (color-coded), prompt preview, input/output references, detected APIs. Inline editing of prompts. | `blueprint: SheetBlueprint`, `onConfirm: (blueprint: SheetBlueprint) => void`, `onBack: () => void` |
| `DeployConfirmation.tsx` | Modal: sheet name (editable), tab count, theme preview, list of required API keys with setup status, Google account connection status. "Deploy" button. | `blueprint: SheetBlueprint`, `theme: ThemeConfig`, `googleConnected: boolean`, `onDeploy: () => void` |
| `DeploymentSuccess.tsx` | Success screen: big checkmark, sheet link (clickable), copy-to-clipboard button, QR code for mobile. "Generate Another" and "Go to Tool Manager" buttons. | `sheetUrl: string`, `sheetTitle: string`, `toolId: string` |

#### 5.3 PRD Upload Flow (NEW — "From PRD" Direct Input)

The PRDUploadButton provides an alternative entry to the pipeline:

```
User clicks "From PRD" button
  ↓
PRDUploadModal opens:
  - Tab 1: "Upload File" — drag-and-drop .md or .txt
  - Tab 2: "Paste Content" — textarea for pasting PRD text
  ↓
User submits → calls POST /api/tool-factory/upload-prd
  ↓
Loading state with "Extracting steps from PRD..." message
  ↓
PRDExtractionResult returned → same flow as YouTube:
  ThemePicker → GenerationProgress → BlueprintPreview → Deploy
```

**Component: `PRDUploadModal.tsx`** — [ROBOT]
```typescript
interface PRDUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onExtractionComplete: (result: PRDExtractionResult) => void
}
```

- Two tabs: "Upload File" and "Paste Content"
- File upload accepts `.md`, `.txt`, `.pdf` (text only)
- Paste textarea with character count (min 100, max 100,000)
- Submit button calls `uploadPRD()` API function
- Loading state with spinner while Claude extracts steps
- Error handling: shows toast if extraction fails

#### 5.4 Integration Points

**Where GenerateToolButton goes:**
Add to the existing YT Lab project detail view (`YTStrategyLabPage.tsx` or wherever the project steps are displayed). It sits in the action bar alongside existing buttons, visible when `project.status === 'complete'` or when steps exist.

**Where PRDUploadButton goes:**
Same location as GenerateToolButton. Two buttons side by side:
```
[⚡ Generate from Video]  [📄 From PRD]
```

The "From PRD" button is always visible (doesn't need a completed YT Lab project).

---

### Phase 6: Tool Manager UI

#### 6.1 Tool Manager Page — new route `/#/tools`

Accessible from the main navigation sidebar (new nav item: "Tools" with a wrench icon).

| View | Description |
|------|-------------|
| **Tool List** | Default view. Grid of ToolCards. Filter by status (All / Active / Draft / Error / Archived). Search by name. Sort by created date, last run, name. |
| **Tool Detail** | Click a ToolCard → full detail view. Tabs: Blueprint, Theme, History, Settings. |

#### 6.2 Components — `ui/src/components/tool-factory/`

**All components are [ROBOT].**

| Component | Purpose | Key Props/State |
|-----------|---------|-----------------|
| `ToolManagerPage.tsx` | Main page. Manages list/detail view state. Has filter bar, search, and sort controls. | Route: `/#/tools` |
| `ToolCard.tsx` | Card in the grid. Shows: tool name, status badge (colored), theme thumbnail (color swatches strip), source (YouTube icon or PRD icon), stats (runs, last run date). Click → detail view. | `tool: GeneratedTool`, `onClick: () => void` |
| `ToolDetailView.tsx` | Full tool view with 4 tabs. Header: tool name, status, actions (Re-theme, Re-deploy, Archive, Open Sheet). | `toolId: string` |
| `ChainVisualizer.tsx` | Visual flow diagram of chain steps. Vertical layout, arrows between steps. Each step: title, type badge, input source label, output reference. Similar to DependencyGraph.tsx but simpler (linear chain, not DAG). | `chain: ChainConfigRow[]` |
| `ExecutionHistory.tsx` | Table: Run # \| Timestamp \| Steps Completed \| Tokens Used \| Duration. Expandable rows show per-step details. | `toolId: string` |
| `ShareToolModal.tsx` | Modal: Copy sheet URL, export blueprint as JSON, copy embed code (iframe for the sheet). | `tool: GeneratedTool` |

#### 6.3 Tool Detail Tabs

| Tab | Contents |
|-----|----------|
| **Blueprint** | ChainVisualizer + detected APIs list + user variables list + source info (video title or PRD name) |
| **Theme** | Current theme preview (swatches + fonts) + "Change Theme" button (opens ThemePicker) + theme history |
| **History** | ExecutionHistory table + total stats (runs, tokens, avg duration) |
| **Settings** | Tool name (editable), tags (editable), archive/delete button, re-generate button |

---

### Shared Hooks and API Functions

#### 6.4 React Query Hooks — `ui/src/hooks/useToolFactory.ts` — [ROBOT]

```typescript
// Tool CRUD
export function useTools(status?: ToolStatus)           // GET /api/tool-factory/tools
export function useTool(toolId: string)                 // GET /api/tool-factory/tools/{id}
export function useArchiveTool()                        // DELETE /api/tool-factory/tools/{id}
export function useToolStats()                          // GET /api/tool-factory/stats

// Generation
export function useGenerateBlueprint()                  // POST /api/tool-factory/generate
export function useUploadPRD()                          // POST /api/tool-factory/upload-prd
export function useDeployTool()                         // POST /api/tool-factory/deploy/{id}

// Google Auth
export function useGoogleAuthStatus()                   // GET /api/tool-factory/google/status
export function useGoogleAuthUrl()                      // GET /api/tool-factory/google/auth-url
```

#### 6.5 React Query Hooks — `ui/src/hooks/useToolThemes.ts` — [ROBOT]

```typescript
export function useThemes()                             // GET /api/tool-factory/themes
export function useTheme(themeId: string)               // GET /api/tool-factory/themes/{id}
export function useExtractTheme()                       // POST /api/tool-factory/themes/extract
export function useThemePreview()                       // POST /api/tool-factory/themes/preview
export function useSwapTheme()                          // PUT /api/tool-factory/tools/{id}/theme
export function useCreateCustomTheme()                  // POST /api/tool-factory/themes/custom
```

#### 6.6 API Client Functions — Edit `ui/src/lib/api.ts` — [ROBOT]

Add all API client functions that the hooks call. Follow existing patterns in api.ts (same base URL, same error handling, same fetch wrapper).

```typescript
// Tool Factory API
export async function fetchTools(status?: string): Promise<GeneratedTool[]>
export async function fetchTool(toolId: string): Promise<GeneratedTool>
export async function archiveTool(toolId: string): Promise<void>
export async function fetchToolStats(): Promise<ToolFactoryStats>
export async function generateBlueprint(projectId: string, theme?: ThemeConfig): Promise<SheetBlueprint>
export async function uploadPRD(content: string, filename: string): Promise<PRDExtractionResult>
export async function deployTool(toolId: string, folderId?: string): Promise<DeployResult>
export async function fetchGoogleAuthStatus(): Promise<{authenticated: boolean}>
export async function fetchGoogleAuthUrl(): Promise<{url: string}>

// Theme API
export async function fetchThemes(): Promise<ThemeConfig[]>
export async function fetchTheme(themeId: string): Promise<ThemeConfig>
export async function extractTheme(imageFile: File): Promise<ThemeConfig>
export async function previewTheme(themeId: string): Promise<ThemePreview>
export async function swapTheme(toolId: string, themeId: string): Promise<GeneratedTool>
export async function createCustomTheme(config: Partial<ThemeConfig>): Promise<ThemeConfig>
```

---

## FILES TO CREATE/MODIFY

| File | Action | Phase |
|------|--------|-------|
| `ui/src/components/tool-factory/GenerateToolButton.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/PRDUploadButton.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/PRDUploadModal.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/ThemePicker.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/ThemePreviewCard.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/GenerationProgress.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/BlueprintPreview.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/DeployConfirmation.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/DeploymentSuccess.tsx` | **Create** | 5 |
| `ui/src/components/tool-factory/ToolManagerPage.tsx` | **Create** | 6 |
| `ui/src/components/tool-factory/ToolCard.tsx` | **Create** | 6 |
| `ui/src/components/tool-factory/ToolDetailView.tsx` | **Create** | 6 |
| `ui/src/components/tool-factory/ChainVisualizer.tsx` | **Create** | 6 |
| `ui/src/components/tool-factory/ExecutionHistory.tsx` | **Create** | 6 |
| `ui/src/components/tool-factory/ShareToolModal.tsx` | **Create** | 6 |
| `ui/src/hooks/useToolFactory.ts` | **Create** | 5 |
| `ui/src/hooks/useToolThemes.ts` | **Create** | 5 |
| `ui/src/lib/api.ts` | **Edit** (add API functions) | 5 |
| `ui/src/App.tsx` | **Edit** (add /#/tools route + nav item) | 6 |

---

## DESIGN SYSTEM REQUIREMENTS

Follow the existing neobrutalism design system. Read these files first:

| File | Why |
|------|-----|
| `ui/src/styles/globals.css` | CSS variables, color tokens, animations |
| `ui/WORKSPACE_STANDARDS.md` | Layout patterns, CRUD flow, loading/empty/error states |
| `ui/src/components/yt-lab/VideoIngestPanel.tsx` | Example of existing panel component pattern |
| `ui/src/components/yt-lab/DiscoveryPanel.tsx` | Example of card layout with badges |
| `ui/src/components/DependencyGraph.tsx` | Reference for ChainVisualizer (similar concept) |
| `ui/src/App.tsx` | Router setup, nav structure, existing routes |

**Key design tokens:**
- `--color-neo-pending` (yellow) — for draft/pending states
- `--color-neo-progress` (cyan) — for deploying/in-progress
- `--color-neo-done` (green) — for active/complete
- Use existing Tailwind v4 classes
- Use Radix UI for modals and dropdowns
- Use lucide-react for icons

**Step type colors (for badges in BlueprintPreview and ChainVisualizer):**
- RESEARCH → blue
- GENERATION → purple
- ACTION → orange
- MANUAL → yellow

---

## TEST PLAN

### Build Test — [ROBOT]

```bash
cd ui && npm run build
```

This is the primary test. TypeScript compilation catches type errors, missing imports, and interface mismatches. If it builds, the types are correct.

### Lint Test — [ROBOT]

```bash
cd ui && npm run lint
```

ESLint catches unused variables, missing dependencies in hooks, etc.

### Component Smoke Tests (Manual Verification)

After build succeeds, verify these visually:

| Check | What to Verify |
|-------|---------------|
| GenerateToolButton renders | Button appears in YT Lab when project has steps |
| PRDUploadButton renders | "From PRD" button appears next to Generate Tool |
| ThemePicker shows 10 presets | Grid of theme cards with color swatches |
| GenerationProgress connects to SSE | Progress steps animate on mock data |
| BlueprintPreview shows chain | Vertical flow of step cards with type badges |
| ToolManagerPage loads | Grid of tool cards at /#/tools route |
| ToolDetailView tabs work | All 4 tabs render without errors |
| ChainVisualizer renders | Linear flow diagram with arrows |
| Navigation includes "Tools" | Sidebar has new nav item |

### Type Safety Checks

Ensure these TypeScript types from Agent 1 are used correctly:
- `SheetBlueprint` — used in BlueprintPreview, GenerationProgress
- `GeneratedTool` — used in ToolCard, ToolDetailView, ToolManagerPage
- `ThemeConfig` — used in ThemePicker, ThemePreviewCard
- `ChainConfigRow` — used in ChainVisualizer, BlueprintPreview
- `PRDExtractionResult` — used in PRDUploadModal
- `StepType` — used for badge coloring in multiple components

### How to Run Tests
```bash
cd "C:/Users/lober/GitHub/Greptacular - AutoForge Build/Greptacular/ui"
npm run lint && npm run build
```

---

## EXISTING CODE REFERENCES

| File | Why |
|------|-----|
| `ui/src/lib/types.ts` | All TypeScript types (Agent 1 added tool factory types here) |
| `ui/src/lib/api.ts` | Existing API client pattern — follow same fetch wrapper |
| `ui/src/hooks/useProjects.ts` | React Query hook patterns — follow same structure |
| `ui/src/hooks/useWebSocket.ts` | WebSocket/SSE pattern for real-time updates |
| `ui/src/components/yt-lab/` | Existing YT Lab components — understand where to add buttons |
| `ui/src/components/DependencyGraph.tsx` | Reference for ChainVisualizer |
| `ui/src/App.tsx` | Router and navigation structure |
| `ui/WORKSPACE_STANDARDS.md` | Required layout and CRUD patterns |

---

## ACCEPTANCE CRITERIA

1. `npm run build` succeeds with zero TypeScript errors
2. `npm run lint` passes with zero warnings
3. All 15 new components render without runtime errors
4. GenerateToolButton appears in YT Lab project detail when steps exist
5. PRDUploadButton provides file upload and paste-in options
6. ThemePicker shows all preset themes as cards with swatches
7. GenerationProgress connects to SSE and shows step completion
8. BlueprintPreview renders chain with editable prompts
9. ToolManagerPage at /#/tools shows tool grid with filtering
10. ToolDetailView has 4 working tabs
11. ChainVisualizer renders linear flow with step type badges
12. Navigation sidebar includes "Tools" item
13. All API functions added to api.ts
14. All hooks created in useToolFactory.ts and useToolThemes.ts
