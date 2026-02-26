# Phase 6a: UI — Intake Dock

## Pre-Reading (Required)

Before building anything, read these files in order:
1. `docs/agent-os-phases/CONTEXT_PRIMER.md` — How everything connects
2. `AGENT_OS_PRD.md` — Focus on: Project Intake Dock (File Staging System) section
3. `docs/agent-os-phases/PHASE_5_ROUTER.md` — The REST + WebSocket endpoints you call
4. `ui/src/components/SpecCreationChat.tsx` — **CRITICAL.** The closest analog to what you're building. Study its structure, imports, and patterns.
5. `ui/src/components/FolderBrowser.tsx` — File browsing pattern (for drag & drop reference)
6. `ui/src/hooks/useSpecChat.ts` — Hook pattern for WebSocket-based chat
7. `ui/src/hooks/useDunkStack.ts` — Hook pattern for REST-based state management
8. `ui/src/lib/api.ts` — API client pattern (where you add Agent OS API functions)
9. `ui/src/components/ui/` — Available UI primitives (button, card, dialog, badge, etc.)

---

## What You're Building

Three pieces:
1. **React Query hooks** — `useAgentOS.ts` — API functions and hooks for all Agent OS endpoints
2. **Intake Dock component** — `IntakeDock.tsx` — File staging area with drag & drop, tagging, readiness checklist
3. **Backend service** — `agent_os_intake_dock.py` — File storage, auto-detection, distribution logic
4. **Router additions** — Intake dock endpoints added to `server/routers/agent_os.py`

---

## Dependencies

From Phase 5:
- The router at `server/routers/agent_os.py` with prefix `/api/agent-os`
- All REST endpoint patterns from Phase 5

Existing UI:
- `@/components/ui/button`, `card`, `badge`, `dialog` — Radix UI primitives
- `@/lib/api.ts` — API client (`apiClient`)
- `lucide-react` — Icons
- `@tanstack/react-query` — Data fetching
- Tailwind CSS v4 with neobrutalism design tokens from `globals.css`

---

## Files to Create

### 1. `ui/src/hooks/useAgentOS.ts` (~150 lines)

React Query hooks for all Agent OS API endpoints.

```typescript
/**
 * useAgentOS Hook
 *
 * React Query hooks for the Agent OS PRD creation system.
 * Covers: standards, product, specs, features, gaps, handoff, intake dock, sessions.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
```

**Query Key Factory:**

```typescript
export const agentOSKeys = {
  all: ['agent-os'] as const,
  standards: (projectName: string) => [...agentOSKeys.all, 'standards', projectName] as const,
  standardsFile: (projectName: string, filename: string) =>
    [...agentOSKeys.standards(projectName), filename] as const,
  product: (projectName: string) => [...agentOSKeys.all, 'product', projectName] as const,
  productFile: (projectName: string, filename: string) =>
    [...agentOSKeys.product(projectName), filename] as const,
  specs: (projectName: string) => [...agentOSKeys.all, 'specs', projectName] as const,
  features: (projectName: string) => [...agentOSKeys.all, 'features', projectName] as const,
  gaps: (projectName: string) => [...agentOSKeys.all, 'gaps', projectName] as const,
  handoff: (projectName: string) => [...agentOSKeys.all, 'handoff', projectName] as const,
  intakeDock: (projectName: string) => [...agentOSKeys.all, 'intake-dock', projectName] as const,
  sessions: () => [...agentOSKeys.all, 'sessions'] as const,
  session: (projectName: string) => [...agentOSKeys.all, 'session', projectName] as const,
}
```

**API Functions (add to `ui/src/lib/api.ts` or define inline):**

```typescript
// Standards
export const agentOSListStandards = (projectName: string) =>
  apiClient.get(`/api/agent-os/standards/${projectName}`).then(r => r.data)

export const agentOSGetStandard = (projectName: string, filename: string) =>
  apiClient.get(`/api/agent-os/standards/${projectName}/${filename}`).then(r => r.data)

export const agentOSUpdateStandard = (projectName: string, filename: string, content: string) =>
  apiClient.put(`/api/agent-os/standards/${projectName}/${filename}`, { filename, content })

export const agentOSInferStandards = (projectName: string) =>
  apiClient.post(`/api/agent-os/standards/${projectName}/infer`).then(r => r.data)

// Product
export const agentOSListProduct = (projectName: string) =>
  apiClient.get(`/api/agent-os/product/${projectName}`).then(r => r.data)

export const agentOSGetProduct = (projectName: string, filename: string) =>
  apiClient.get(`/api/agent-os/product/${projectName}/${filename}`).then(r => r.data)

// Features
export const agentOSListFeatures = (projectName: string) =>
  apiClient.get(`/api/agent-os/features/${projectName}`).then(r => r.data)

export const agentOSAddFeature = (projectName: string, feature: FeatureCreate) =>
  apiClient.post(`/api/agent-os/features/${projectName}`, feature).then(r => r.data)

export const agentOSRemoveFeature = (projectName: string, featureId: number) =>
  apiClient.delete(`/api/agent-os/features/${projectName}/${featureId}`)

// Gaps
export const agentOSListGaps = (projectName: string) =>
  apiClient.get(`/api/agent-os/gaps/${projectName}`).then(r => r.data)

export const agentOSResolveGap = (projectName: string, gapId: number, resolution: string) =>
  apiClient.post(`/api/agent-os/gaps/${projectName}/${gapId}/resolve`, { gap_id: gapId, resolution })

export const agentOSAutoResolveGaps = (projectName: string) =>
  apiClient.post(`/api/agent-os/gaps/${projectName}/auto-resolve`).then(r => r.data)

// Specs
export const agentOSListSpecs = (projectName: string) =>
  apiClient.get(`/api/agent-os/specs/${projectName}`).then(r => r.data)

export const agentOSGetSpec = (projectName: string, featureId: number) =>
  apiClient.get(`/api/agent-os/specs/${projectName}/${featureId}`).then(r => r.data)

// Handoff
export const agentOSPopulateDB = (projectName: string) =>
  apiClient.post(`/api/agent-os/handoff/${projectName}/populate-db`).then(r => r.data)

export const agentOSGetHandoffStatus = (projectName: string) =>
  apiClient.get(`/api/agent-os/handoff/${projectName}/status`).then(r => r.data)

export const agentOSAssembleHandoff = (projectName: string) =>
  apiClient.post(`/api/agent-os/handoff/${projectName}/assemble`).then(r => r.data)

export const agentOSGetBuildPlan = (projectName: string) =>
  apiClient.get(`/api/agent-os/handoff/${projectName}/build-plan`).then(r => r.data)

// Intake Dock
export const agentOSListStagedFiles = (projectName: string) =>
  apiClient.get(`/api/agent-os/intake-dock/${projectName}`).then(r => r.data)

export const agentOSStageFile = (projectName: string, formData: FormData) =>
  apiClient.post(`/api/agent-os/intake-dock/${projectName}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data)

export const agentOSTagFile = (projectName: string, fileId: string, tag: string) =>
  apiClient.put(`/api/agent-os/intake-dock/${projectName}/${fileId}/tag`, { tag })

export const agentOSRemoveStagedFile = (projectName: string, fileId: string) =>
  apiClient.delete(`/api/agent-os/intake-dock/${projectName}/${fileId}`)

export const agentOSProcessIntake = (projectName: string) =>
  apiClient.post(`/api/agent-os/intake-dock/${projectName}/process`).then(r => r.data)

export const agentOSGetReadiness = (projectName: string) =>
  apiClient.get(`/api/agent-os/intake-dock/${projectName}/readiness`).then(r => r.data)

// Sessions
export const agentOSListSessions = () =>
  apiClient.get('/api/agent-os/sessions').then(r => r.data)

export const agentOSGetSession = (projectName: string) =>
  apiClient.get(`/api/agent-os/sessions/${projectName}`).then(r => r.data)

export const agentOSCancelSession = (projectName: string) =>
  apiClient.delete(`/api/agent-os/sessions/${projectName}`)
```

**Hooks (use these in components):**

```typescript
// Example hooks — implement all of these following the same pattern:

export function useStandards(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.standards(projectName),
    queryFn: () => agentOSListStandards(projectName),
    enabled: !!projectName,
  })
}

export function useFeatures(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.features(projectName),
    queryFn: () => agentOSListFeatures(projectName),
    enabled: !!projectName,
  })
}

export function useGaps(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.gaps(projectName),
    queryFn: () => agentOSListGaps(projectName),
    enabled: !!projectName,
  })
}

export function useStagedFiles(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.intakeDock(projectName),
    queryFn: () => agentOSListStagedFiles(projectName),
    enabled: !!projectName,
  })
}

export function useHandoffStatus(projectName: string) {
  return useQuery({
    queryKey: agentOSKeys.handoff(projectName),
    queryFn: () => agentOSGetHandoffStatus(projectName),
    enabled: !!projectName,
  })
}

// Mutations
export function useStageFile(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (formData: FormData) => agentOSStageFile(projectName, formData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) }),
  })
}

export function useTagFile(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ fileId, tag }: { fileId: string; tag: string }) =>
      agentOSTagFile(projectName, fileId, tag),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) }),
  })
}

export function useProcessIntake(projectName: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentOSProcessIntake(projectName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: agentOSKeys.intakeDock(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.standards(projectName) })
      queryClient.invalidateQueries({ queryKey: agentOSKeys.product(projectName) })
    },
  })
}
```

**TypeScript types to define:**

```typescript
export interface StagedFile {
  id: string
  name: string
  size: number
  type: string        // MIME type
  tag: string | null   // "standards" | "product" | "spec" | "reference" | "intake" | null
  auto_tag: string | null  // System's auto-detected tag suggestion
  processed: boolean
  destination_path: string | null  // Set after processing
  created_at: string
}

export interface ReadinessStatus {
  standards: { count: number; ready: boolean }
  product: { count: number; ready: boolean }
  specs: { count: number; ready: boolean }
  reference: { count: number; ready: boolean }
  intake: { count: number; ready: boolean }
  untagged: number
  can_proceed: boolean  // True if minimum requirements met
}

export interface FeatureCreate {
  name: string
  description: string
  priority?: string
  complexity?: string
  category?: string
  dependencies?: number[]
}
```

---

### 2. `ui/src/components/appbuilder/IntakeDock.tsx` (~250 lines)

The file staging area component.

```typescript
/**
 * IntakeDock Component
 *
 * File staging area for Agent OS project intake.
 * Users drag & drop files, tag them by category, and process them
 * to start the Agent OS PRD creation workflow.
 */

import { useCallback, useRef, useState } from 'react'
import { Upload, FileText, Tag, CheckCircle2, AlertCircle, Trash2, Play, ClipboardPaste } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  useStagedFiles,
  useStageFile,
  useTagFile,
  useProcessIntake,
  type StagedFile,
  type ReadinessStatus,
} from '@/hooks/useAgentOS'
```

**Component Props:**

```typescript
interface IntakeDockProps {
  projectName: string
  onProcessComplete: () => void  // Called after files are processed, starts Agent OS session
  onSkip: () => void             // Skip intake dock, go straight to Agent OS chat
}
```

**Layout Structure (neobrutalism design):**

```
┌─────────────────────────────────────────────────────────────────┐
│  PROJECT INTAKE DOCK                                             │
│  ─────────────────────────────────────────────────────────────── │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  📁  Drop files here or click to upload                   │   │
│  │      Supports: .md, .txt, .pdf, .docx, .png, .json       │   │
│  │                                                           │   │
│  │           [Paste from Clipboard]                          │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  STAGED FILES                                                    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  📄 my-ideas.md          [Product ▼]          [🗑]        │   │
│  │  📄 ui-standards.md      [Standards ▼]        [🗑]        │   │
│  │  📄 competitor.txt       [Reference ▼]        [🗑]        │   │
│  │  ⚠ auth-spec.md          [Tag needed ▼]       [🗑]        │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  READINESS                                                       │
│  ┌─────────────┬─────────────┬──────────┬──────────┐            │
│  │ ✅ Standards │ ✅ Product   │ ⬚ Specs  │ ⬚ Ref    │            │
│  │ 1 file      │ 1 file      │ 0 files  │ 0 files  │            │
│  └─────────────┴─────────────┴──────────┴──────────┘            │
│                                                                   │
│  ⚠ 1 file needs a tag                                           │
│                                                                   │
│  [Skip — Start from Scratch]    [Process & Start Agent OS →]    │
└─────────────────────────────────────────────────────────────────┘
```

**Key behaviors to implement:**

1. **Drag & drop zone** — Uses native HTML5 drag events (`onDragOver`, `onDrop`). On drop, calls `useStageFile` mutation with `FormData` containing the file. Highlights the zone during drag with a border color change.

2. **Paste from clipboard** — Button that reads `navigator.clipboard.readText()`, prompts for a filename via a small input, creates a `.md` file from the pasted text, stages it.

3. **File list** — Shows each staged file with:
   - File icon + name
   - Tag dropdown (select element or Radix `DropdownMenu`): Standards, Product, Spec, Reference, Intake
   - If `auto_tag` is set and `tag` is null, show the auto_tag as a suggestion badge that can be clicked to accept
   - Delete button
   - "Processed" checkmark if already processed

4. **Readiness checklist** — Shows status per category. Green checkmark if category has files OR isn't required. Amber warning if Product/Intake has 0 files (can't proceed without at least one).

5. **Process button** — Disabled if `can_proceed` is false (no Product or Intake files). On click, calls `useProcessIntake`, shows a loading state, then calls `onProcessComplete`.

6. **Skip button** — Calls `onSkip` to bypass intake dock and start Agent OS chat from scratch.

**Tag dropdown options:**

```typescript
const TAG_OPTIONS = [
  { value: 'standards', label: 'Standards', description: 'Coding conventions, architecture, quality' },
  { value: 'product', label: 'Product', description: 'Vision, users, use cases, roadmap' },
  { value: 'spec', label: 'Spec', description: 'Feature specifications, requirements' },
  { value: 'reference', label: 'Reference', description: 'Background material, competitor docs' },
  { value: 'intake', label: 'Intake', description: 'Raw braindumps, conversation transcripts' },
]
```

**Styling notes (neobrutalism):**
- Use `border-2 border-black` for card borders
- Use `shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]` for neobrutalist shadow
- Drop zone uses dashed border: `border-dashed border-2`
- Tags use colored badges: Standards=blue, Product=purple, Spec=green, Reference=amber, Intake=gray
- Process button uses the primary action style: `bg-neo-done text-black font-bold`

---

### 3. `server/services/agent_os_intake_dock.py` (~150 lines)

Backend for the intake dock file staging.

```python
"""
Agent OS Intake Dock
=====================

Backend for the file staging area. Handles file upload, storage,
auto-detection of file types, tagging, and distribution to proper
directories when processing.
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)
```

**Class: `AgentOSIntakeDock`**

Constructor:
```python
def __init__(self, project_dir: Path, file_utils: "AgentOSFileUtils"):
    self.project_dir = project_dir
    self.file_utils = file_utils
    self.staging_dir = project_dir / ".agent" / "intake_staging"
    self.staging_dir.mkdir(parents=True, exist_ok=True)
    self._manifest_path = self.staging_dir / "manifest.json"
    self._manifest: list[dict] = self._load_manifest()
```

Required methods:

| Method | Signature | What It Does |
|--------|-----------|-------------|
| `stage_file` | `(filename: str, content: bytes, mime_type: str = "") -> dict` | Saves file to staging dir with a UUID. Runs auto-detection. Creates manifest entry. Returns the `StagedFile` dict. |
| `stage_text` | `(filename: str, text: str) -> dict` | Creates a .md file from pasted text. Calls `stage_file`. |
| `auto_detect_tag` | `(filename: str, content: str) -> Optional[str]` | Content-based tag suggestion. Scans for keywords: "coding conventions"/"style guide"/"architecture" → "standards". "vision"/"users"/"roadmap"/"problem" → "product". "requirements"/"acceptance criteria"/"user stories" → "spec". "competitor"/"research"/"analysis" → "reference". No match → "intake". Returns the suggested tag. |
| `tag_file` | `(file_id: str, tag: str) -> Optional[dict]` | Sets the tag for a staged file. Updates manifest. Returns updated entry. |
| `remove_file` | `(file_id: str) -> bool` | Removes file from staging and manifest. |
| `get_staged_files` | `() -> list[dict]` | Returns all staged files from manifest. |
| `get_readiness` | `() -> dict` | Returns readiness status per category + overall `can_proceed`. |
| `process_files` | `() -> dict` | Distributes tagged files to proper directories: standards → `agent-os/standards/`, product → `.agent/product/`, spec → `.agent/specs/`, reference → `.agent/knowledge/`, intake → `.agent/intake/`. Marks each as processed. Returns `{"processed": N, "destinations": {...}}`. |
| `_load_manifest` | `() -> list[dict]` | Loads manifest.json from staging dir. Returns empty list if not found. |
| `_save_manifest` | `() -> None` | Saves manifest to staging dir. |

**Auto-detection keyword lists:**

```python
DETECTION_KEYWORDS = {
    "standards": [
        "coding conventions", "style guide", "architecture pattern",
        "naming convention", "file organization", "design system",
        "component library", "linter", "formatter",
    ],
    "product": [
        "vision", "target user", "use case", "roadmap", "problem we solve",
        "competitive", "constraint", "success criteria", "mvp",
    ],
    "spec": [
        "requirement", "acceptance criteria", "user story", "as a user",
        "endpoint", "data model", "api spec", "feature spec",
    ],
    "reference": [
        "competitor", "research", "analysis", "reference", "benchmark",
        "comparison", "case study", "example",
    ],
}
```

---

### 4. Router Additions

Add these endpoints to `server/routers/agent_os.py` (the Phase 5 router):

| Method | Path | Handler | What It Does |
|--------|------|---------|-------------|
| GET | `/intake-dock/{project_name}` | `list_staged_files` | List all staged files |
| POST | `/intake-dock/{project_name}/upload` | `upload_file` | Upload and stage a file (multipart form) |
| POST | `/intake-dock/{project_name}/paste` | `paste_text` | Create file from pasted text |
| PUT | `/intake-dock/{project_name}/{file_id}/tag` | `tag_staged_file` | Set tag for a staged file |
| DELETE | `/intake-dock/{project_name}/{file_id}` | `remove_staged_file` | Remove a staged file |
| GET | `/intake-dock/{project_name}/readiness` | `get_readiness` | Get readiness checklist status |
| POST | `/intake-dock/{project_name}/process` | `process_intake` | Process all staged files → distribute to directories |

**Pydantic models for intake dock:**

```python
class PasteFileRequest(BaseModel):
    filename: str
    content: str

class TagFileRequest(BaseModel):
    tag: str  # "standards" | "product" | "spec" | "reference" | "intake"
```

---

## Completion Criteria

Phase 6a is DONE when:
- [ ] `ui/src/hooks/useAgentOS.ts` exists with all hooks and API functions
- [ ] `ui/src/components/appbuilder/IntakeDock.tsx` exists and renders
- [ ] `server/services/agent_os_intake_dock.py` exists with all methods
- [ ] Intake dock router endpoints added to `server/routers/agent_os.py`
- [ ] Drag & drop file upload works
- [ ] Paste from clipboard creates a staged file
- [ ] Tag dropdown changes persist
- [ ] Auto-detection suggests tags for known content patterns
- [ ] Readiness checklist updates in real-time
- [ ] Process button distributes files to correct directories
- [ ] UI passes `npm run lint` and `npm run build`
- [ ] Python passes `ruff check` and `mypy`

---

## What Phase 6b Expects from You

Phase 6b imports `useAgentOS.ts` hooks extensively. It needs:
- All query hooks working (`useStandards`, `useFeatures`, `useGaps`, etc.)
- All mutation hooks working (`useStageFile`, `useTagFile`, etc.)
- TypeScript types exported (`StagedFile`, `ReadinessStatus`, `FeatureCreate`)
- The `agentOSKeys` query key factory exported

Phase 6b also needs the `IntakeDock` component to call `onProcessComplete` correctly, which triggers the transition to the Agent OS chat view.

---

*End of Phase 6a PRD.*
