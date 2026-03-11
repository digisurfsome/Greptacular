# PRD: Reusable Dependency Graph Component

## Overview

A reusable, standalone React component for visualizing tasks, features, or any items with dependency relationships as an interactive directed graph. Designed to be dropped into any React + TypeScript project with zero configuration. Powered by `@xyflow/react` (v12+) for rendering and `dagre` (v0.8.5) for automatic hierarchical layout.

The component accepts a simple array of nodes with dependency IDs and renders a fully interactive graph with pan, zoom, drag, minimap, and status-based color coding. No API calls, no global state, no external services required.

## Use Cases

- **AutoForge Build Planner**: Visualize features after PRD generation, plan implementation phases, identify parallel work opportunities, and spot dependency bottlenecks.
- **Project Management Tools**: Task dependency visualization, sprint planning boards, milestone tracking with prerequisite chains.
- **Documentation and Architecture**: System architecture diagrams, data flow visualization, module dependency maps.
- **CI/CD Pipeline Visualization**: Build stage dependencies, deployment pipeline graphs, test suite ordering.
- **Curriculum and Learning Paths**: Course prerequisite chains, skill trees, learning progression maps.

## Core Features (Must Have)

### 1. Self-Contained Component
Single import, no API calls required. All data passed as props. No global state, context providers, or external setup needed beyond installing peer dependencies.

```tsx
import { DependencyGraph } from '@/components/DependencyGraph'
```

### 2. Auto-Layout with dagre
Nodes are automatically positioned in a hierarchical layout using the dagre graph layout algorithm. No manual positioning required. Layout settings: `nodesep: 50`, `ranksep: 100`, `margin: 50`.

### 3. Layout Direction Toggle
Built-in toggle between horizontal (left-to-right, `LR`) and vertical (top-to-bottom, `TB`) layout. Direction change re-runs dagre and repositions all nodes with correct handle positions (Left/Right for horizontal, Top/Bottom for vertical).

### 4. Status-Based Node Styling
Each node is colored based on its status:

| Status        | Color   | Icon           | CSS Variable                    |
|---------------|---------|----------------|---------------------------------|
| `pending`     | Yellow  | Circle (empty) | `--color-graph-node-pending`    |
| `in_progress` | Cyan    | Loader spinner | `--color-graph-node-progress`   |
| `done`        | Green   | CheckCircle    | `--color-graph-node-done`       |
| `blocked`     | Red     | AlertTriangle  | `--color-graph-node-failing`    |

Node appearance: 220x80px cards with 2px colored border, tinted background using `color-mix(in srgb, {statusColor} 12%, {backgroundColor})`, status icon + priority number + name + category.

### 5. Interactive Controls
Full interactivity powered by ReactFlow:
- **Pan**: Click and drag on background
- **Zoom**: Scroll wheel, pinch gesture, or zoom controls
- **Drag nodes**: Click and drag individual nodes to reposition
- **Fit view**: Auto-fit all nodes in viewport on initial render (padding: 0.2)
- **Minimap**: Overview panel showing all nodes with status colors
- **Zoom controls**: +/- buttons and fit-to-view

### 6. Click Handler
Callback prop `onNodeClick` fires with the numeric node ID when a node is clicked. Uses a ref-based pattern internally to avoid unnecessary re-renders when the callback identity changes.

### 7. Responsive Layout
Component fills its parent container (100% width and height). Parent must have a defined height (ReactFlow requirement).

### 8. Dark/Light Theme Support
All colors are defined as CSS custom properties with sensible defaults. The component reads from CSS variables at runtime, so it automatically respects the host application's theme. Default values provided for both light and dark modes.

**Light mode defaults:**
```css
--color-graph-edge: #a1a1aa;
--color-graph-node-pending: #eab308;
--color-graph-node-progress: #06b6d4;
--color-graph-node-done: #22c55e;
--color-graph-node-failing: #ef4444;
--color-graph-bg: #d4d4d8;
```

**Dark mode defaults:**
```css
--color-graph-edge: #71717a;
--color-graph-node-pending: #facc15;
--color-graph-node-progress: #22d3ee;
--color-graph-node-done: #4ade80;
--color-graph-node-failing: #f87171;
--color-graph-bg: #3f3f46;
```

### 9. Edge Rendering
Smooth-step edges with directional arrow markers (`MarkerType.ArrowClosed`). Edge color reads from `--color-graph-edge` CSS variable. Stroke width: 2px.

### 10. Zero-Config Defaults
The component works with just a `nodes` array. Edges are automatically derived from each node's `dependencies` array. Explicit edges can also be passed for advanced use cases.

### 11. Error Boundary
Wrapped in a class-based error boundary that catches ReactFlow rendering errors and displays a recovery UI with a "Reload Graph" button. Prevents the entire host application from crashing due to graph rendering issues.

### 12. Empty State
When no nodes are provided, displays a centered placeholder message ("No features to display") instead of an empty canvas.

### 13. Status Legend
A floating legend card in the top-right corner showing all four status types with their corresponding colors.

## Data Format

### Node Interface

```typescript
type NodeStatus = 'pending' | 'in_progress' | 'done' | 'blocked'

interface GraphNode {
  id: number
  name: string
  category: string
  status: NodeStatus
  priority: number
  dependencies: number[]  // Array of node IDs this node depends on
}
```

### Edge Interface (optional, auto-derived from dependencies)

```typescript
interface GraphEdge {
  source: number  // ID of the dependency (upstream node)
  target: number  // ID of the dependent (downstream node)
}
```

### Graph Data Interface

```typescript
interface DependencyGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}
```

### Edge Auto-Derivation

When `edges` are not explicitly provided, the component generates them from each node's `dependencies` array:

```typescript
// For each node, create an edge from each dependency to that node
const edges = nodes.flatMap(node =>
  node.dependencies.map(depId => ({
    source: depId,
    target: node.id,
  }))
)
```

## Props API

```typescript
interface DependencyGraphProps {
  /** Array of graph nodes. Required. */
  nodes: GraphNode[]

  /**
   * Explicit edges. Optional.
   * If omitted, edges are auto-derived from each node's dependencies array.
   */
  edges?: GraphEdge[]

  /** Layout direction. 'LR' = left-to-right, 'TB' = top-to-bottom. Default: 'LR' */
  direction?: 'LR' | 'TB'

  /** Callback when a node is clicked. Receives the numeric node ID. */
  onNodeClick?: (nodeId: number) => void

  /** Additional CSS class name for the root container. */
  className?: string

  /** Show the minimap overview panel. Default: true */
  showMinimap?: boolean

  /** Show the zoom/fit controls. Default: true */
  showControls?: boolean

  /** Show the status legend card. Default: true */
  showLegend?: boolean

  /** Show the horizontal/vertical layout toggle buttons. Default: true */
  showLayoutToggle?: boolean

  /** Node card width in pixels. Default: 220 */
  nodeWidth?: number

  /** Node card height in pixels. Default: 80 */
  nodeHeight?: number

  /** Minimum zoom level. Default: 0.1 */
  minZoom?: number

  /** Maximum zoom level. Default: 2 */
  maxZoom?: number
}
```

## Technical Architecture

### Component Hierarchy

```
DependencyGraph (public export)
  └── GraphErrorBoundary (error recovery wrapper)
       └── DependencyGraphInner (main logic)
            ├── Layout Toggle Buttons (top-left)
            ├── Status Legend Card (top-right)
            └── ReactFlow
                 ├── Background (dot grid)
                 ├── Controls (zoom +/- and fit)
                 ├── MiniMap (overview with status colors)
                 └── FeatureNode[] (custom node type)
                      ├── Handle (target, left or top)
                      ├── Node Card (status icon, priority, name, category)
                      └── Handle (source, right or bottom)
```

### Layout Engine

The dagre layout is computed as a pure function with no side effects:

1. Create a new `dagre.graphlib.Graph` instance
2. Set graph options: `rankdir`, `nodesep`, `ranksep`, `marginx`, `marginy`
3. Add all nodes with their dimensions
4. Add all edges
5. Run `dagre.layout()`
6. Read computed positions, centering nodes on their dagre coordinates
7. Set `sourcePosition` and `targetPosition` on each node based on direction

### State Management

- No global state, context, or external stores
- Internal state managed with `useState` (direction) and `useNodesState`/`useEdgesState` (ReactFlow)
- Callback ref pattern (`useRef` + `useEffect`) to avoid re-renders from callback prop changes
- Graph data change detection via JSON hash comparison to prevent unnecessary layout recalculations

### Theming Strategy

- All colors defined as CSS custom properties
- Component reads computed styles at runtime via `getComputedStyle(document.documentElement)`
- Host application overrides colors by setting the CSS variables
- Fallback hex values hardcoded for environments where CSS variables are not set
- Node background uses `color-mix()` for a subtle tinted fill

### Peer Dependencies

```json
{
  "@xyflow/react": "^12.0.0",
  "dagre": "^0.8.5",
  "lucide-react": ">=0.300.0",
  "react": ">=18.0.0",
  "react-dom": ">=18.0.0"
}
```

Note: `@types/dagre` is needed as a dev dependency for TypeScript support.

## File Structure

```
src/components/DependencyGraph/
  index.ts                    — Public exports (DependencyGraph, types)
  DependencyGraph.tsx         — Main component with error boundary wrapper
  DependencyGraphInner.tsx    — Core graph logic (ReactFlow, state, layout toggle)
  DependencyGraphNode.tsx     — Custom ReactFlow node renderer (FeatureNode)
  DependencyGraphLegend.tsx   — Status legend floating card
  layout.ts                   — dagre layout helper (pure function)
  types.ts                    — TypeScript interfaces (GraphNode, GraphEdge, props)
  styles.css                  — Default CSS variable definitions (light + dark)
  __tests__/
    DependencyGraph.test.tsx  — Component rendering and interaction tests
    layout.test.ts            — Layout computation unit tests
```

## Integration Example

### Minimal Usage (zero config)

```tsx
import { DependencyGraph } from '@/components/DependencyGraph'

const features = [
  { id: 1, name: 'Auth System', category: 'Backend', status: 'done', priority: 1, dependencies: [] },
  { id: 2, name: 'Dashboard', category: 'Frontend', status: 'in_progress', priority: 2, dependencies: [1] },
  { id: 3, name: 'Settings Page', category: 'Frontend', status: 'pending', priority: 3, dependencies: [1] },
  { id: 4, name: 'Reports', category: 'Analytics', status: 'blocked', priority: 4, dependencies: [2, 3] },
]

function App() {
  return (
    <div style={{ width: '100%', height: '600px' }}>
      <DependencyGraph
        nodes={features}
        onNodeClick={(id) => console.log('Clicked node:', id)}
      />
    </div>
  )
}
```

### Full Props Usage

```tsx
<DependencyGraph
  nodes={features}
  edges={customEdges}
  direction="TB"
  onNodeClick={handleNodeClick}
  className="my-graph"
  showMinimap={true}
  showControls={true}
  showLegend={true}
  showLayoutToggle={true}
  nodeWidth={260}
  nodeHeight={90}
  minZoom={0.2}
  maxZoom={3}
/>
```

### Custom Theming

```css
/* Override graph colors in your app's CSS */
:root {
  --color-graph-edge: #6366f1;
  --color-graph-node-pending: #f59e0b;
  --color-graph-node-progress: #3b82f6;
  --color-graph-node-done: #10b981;
  --color-graph-node-failing: #ef4444;
  --color-graph-bg: #e5e7eb;
}

.dark {
  --color-graph-edge: #818cf8;
  --color-graph-node-pending: #fbbf24;
  --color-graph-node-progress: #60a5fa;
  --color-graph-node-done: #34d399;
  --color-graph-node-failing: #f87171;
  --color-graph-bg: #374151;
}
```

## Build Planner Integration

When used inside the AutoForge Build Planner page, the graph serves as a visual planning tool:

1. **Parse features from PRD output**: After the AI generates a PRD with features, parse them into the `GraphNode[]` format and render the dependency graph immediately.

2. **Visual dependency editing**: Let users draw dependency edges by dragging from one node's source handle to another node's target handle. Use ReactFlow's `onConnect` callback to add new edges and update the underlying data model.

3. **Phase auto-detection**: Run a topological sort (Kahn's algorithm) on the graph to identify dependency layers. Each layer represents a phase where all nodes can execute in parallel. Display phase boundaries as visual groupings.

4. **Parallel work highlighting**: Within each phase/layer, highlight nodes that share no mutual dependencies, indicating they can be worked on simultaneously by different agents.

5. **Feed back to prompt pipeline**: Export the finalized graph data (nodes with phases, dependency edges, parallel groups) as structured input for the phase-split prompt, enabling better AI-driven phase generation.

### Build Planner Data Flow

```
PRD AI Output
  → Parse features into GraphNode[]
  → Render DependencyGraph (visual review)
  → User adds/removes dependency edges
  → Topological sort → phase assignment
  → Parallel group detection per phase
  → Export structured plan → Phase-split prompt
```

## Stretch Features (Nice to Have)

These are not required for the initial implementation but would add significant value in future iterations:

1. **Critical path highlighting** — Identify and visually highlight the longest dependency chain (the bottleneck path that determines minimum total time). Use a distinct edge color or glow effect.

2. **Parallel group detection** — Automatically identify and label groups of nodes that can run simultaneously within each dependency layer. Display with a shared background color or grouping border.

3. **Phase boundary visualization** — Draw dashed-border rectangles around nodes that belong to the same dependency layer/phase. Label each phase (Phase 1, Phase 2, etc.).

4. **Export as PNG/SVG** — Button to export the current graph view as a PNG or SVG image for documentation, presentations, or sharing.

5. **Node grouping by category** — Visually group nodes by their `category` field with color-coded background regions (e.g., all "Backend" nodes in one shaded area, all "Frontend" in another).

6. **Animated edge flow** — Subtle animation on edges showing the direction of dependency flow (small dots or dashes moving along the edge path).

7. **Tooltip on hover** — Show a rich tooltip on node hover with full details: name, category, status, priority, list of dependencies by name, and list of dependents.

8. **Search and filter** — Text input to search nodes by name or category. Filter by status. Matched nodes highlighted, non-matched nodes dimmed.

9. **Undo/redo for node positions** — Track node position changes and support undo/redo for manual repositioning.

10. **Drag-to-connect edges** — Allow users to create new dependency edges by dragging from a node's source handle to another node's target handle, with cycle detection to prevent circular dependencies.

## Acceptance Criteria

The component is considered complete when:

1. Renders a graph from a `GraphNode[]` array with no additional configuration.
2. Edges are auto-derived from `dependencies` arrays when `edges` prop is omitted.
3. Nodes are automatically positioned using dagre layout.
4. Layout direction toggles between LR and TB correctly, repositioning all nodes and handles.
5. Nodes display status icon, priority number, name, and category.
6. Node border and background color matches the node's status.
7. Edges render as smooth-step with arrow markers.
8. Pan, zoom, and node drag all work.
9. Minimap shows nodes colored by status.
10. `onNodeClick` callback fires with the correct node ID.
11. Component fills its parent container responsively.
12. Error boundary catches rendering errors and shows recovery UI.
13. Empty state displayed when nodes array is empty.
14. CSS variables can be overridden by the host application for theming.
15. All TypeScript types are exported for consumer use.
16. No console errors or warnings in normal operation.
