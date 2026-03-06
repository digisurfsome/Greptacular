# YTLAB.md — Context Override

> When working in this app, THIS file takes priority over root CLAUDE.md.
> Only reference root CLAUDE.md for shared infrastructure (build, server, design tokens).

## Identity

YT Strategy Lab extracts, organizes, and operationalizes strategies from YouTube videos. Users ingest videos, capture screenshots, build strategy steps with sub-steps, run batch imports, and use AI discovery to find app-building opportunities. All data is stored in localStorage — there is no backend API for this app.

## Route

`/#/yt-lab` — Full-page layout with sub-routes

## Components

### Page
- `ui/src/pages/YTStrategyLabPage.tsx` — Main page with project list, detail/builder, create form

### Core Components (`ui/src/components/yt-lab/`)
- `VideoIngestPanel.tsx` — Video URL input and processing
- `ScreenshotGallery.tsx` — Captured screenshot management
- `ExecutionViewer.tsx` — Strategy execution tracking
- `DiscoveryPanel.tsx` — AI-powered opportunity discovery
- `BatchImportView.tsx` — Bulk strategy import

## State & Data

- **All localStorage** — No backend API calls
- `yt-lab-projects` — Project list storage key
- `yt-lab-steps-{projectId}` — Per-project strategy steps
- `yt-lab-screenshots-{projectId}` — Per-project screenshots

### Key Types (from `ui/src/lib/types.ts`)
- `YTStrategyProject` — Project with title, URL, status
- `YTStrategyStep` / `YTStrategySubStep` — Hierarchical strategy steps
- `YTIngestResponse` — Video processing result
- `YTScreenshotCapture` — Screenshot with analysis
- `YTAppOpportunity` — Discovered app opportunity
- `YTDiscoverResponse` — AI discovery result
- `YTProjectStatus` / `YTStrategyStepStatus` — Status enums

### API Functions (streaming)
- `processVideoStream()` — Stream video processing with log entries
- `startExecution()` — Start strategy execution

## Patterns

- Three views: Project List (default) → Project Detail/Builder → Create New
- Strategy steps are hierarchical: Step → SubStep
- Drag-and-drop reordering via GripVertical handles
- Collapsible sidebar for project navigation
- AI discovery uses streaming API for real-time results

## Skill Recommendations

### Recommended
- `frontend-design` — When restyling cards/panels (~8% context)
- `webapp-testing` — When testing video ingest flow (~5% context)

### Specialized (load on demand)
- `doc-coauthoring` — If writing strategy documentation (~4% context)
- `canvas-design` — If building visual strategy exports (~7% context)

### Context Budget: 1-2 skills ideal, 3+ not recommended

## Anti-Patterns

- Do NOT add backend API calls — this app is intentionally localStorage-only
- Do NOT modify DunkStackPage, WorkspacePage, or DashboardPage components
- Do NOT change AutoForge kanban/feature management from this context
- Do NOT break the localStorage schema without migration logic
- Do NOT import heavy dependencies — this app should stay lightweight

## Agent Personality

You are a content strategist and product thinker focused on extracting actionable insights from video content. Think in terms of strategies, steps, execution, and discovery. When describing changes, reference the video-to-strategy pipeline. Be structured and action-oriented.
