import { Component, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Position,
  MarkerType,
  ConnectionMode,
  Handle,
} from '@xyflow/react'
import dagre from 'dagre'
import { CheckCircle2, Circle, Loader2, AlertTriangle, RefreshCw } from 'lucide-react'
import type { DependencyGraph as DependencyGraphData, GraphNode, ActiveAgent, AgentMascot, AgentState } from '../lib/types'
import { AgentAvatar } from './AgentAvatar'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import '@xyflow/react/dist/style.css'

// Node dimensions
const NODE_WIDTH = 220
const NODE_HEIGHT = 80

interface DependencyGraphProps {
  graphData: DependencyGraphData
  onNodeClick?: (nodeId: number) => void
  activeAgents?: ActiveAgent[]
}

// Agent info to display on a node
interface NodeAgentInfo {
  name: AgentMascot | 'Unknown'
  state: AgentState
}

// Error boundary to catch and recover from ReactFlow rendering errors
interface ErrorBoundaryProps {
  children: ReactNode
  onReset?: () => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class GraphErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('DependencyGraph error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    this.props.onReset?.()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full w-full flex items-center justify-center bg-muted">
          <div className="text-center p-6">
            <AlertTriangle size={48} className="mx-auto mb-4 text-amber-500 dark:text-amber-400" />
            <div className="text-foreground font-medium mb-2">Graph rendering error</div>
            <div className="text-sm text-muted-foreground mb-4">
              The dependency graph encountered an issue.
            </div>
            <Button onClick={this.handleReset} className="gap-2">
              <RefreshCw size={16} />
              Reload Graph
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Map status to CSS variable names for graph node colors
const STATUS_COLOR_VAR: Record<string, string> = {
  pending: 'var(--color-graph-node-pending)',
  in_progress: 'var(--color-graph-node-progress)',
  done: 'var(--color-graph-node-done)',
  blocked: 'var(--color-graph-node-failing)',
}

// Custom node component
function FeatureNode({ data }: { data: GraphNode & { onClick?: () => void; agent?: NodeAgentInfo } }) {
  const nodeColor = STATUS_COLOR_VAR[data.status] || STATUS_COLOR_VAR.pending

  const StatusIcon = () => {
    switch (data.status) {
      case 'done':
        return <CheckCircle2 size={16} style={{ color: nodeColor }} />
      case 'in_progress':
        return <Loader2 size={16} className="animate-spin" style={{ color: nodeColor }} />
      case 'blocked':
        return <AlertTriangle size={16} className="text-destructive" />
      default:
        return <Circle size={16} style={{ color: nodeColor }} />
    }
  }

  return (
    <>
      <Handle type="target" position={Position.Left} className="!bg-border !w-2 !h-2" />
      <div
        className="px-3 py-2 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md relative"
        onClick={data.onClick}
        style={{
          minWidth: NODE_WIDTH - 20,
          maxWidth: NODE_WIDTH,
          borderColor: nodeColor,
          backgroundColor: `color-mix(in srgb, ${nodeColor} 12%, var(--color-background))`,
          color: nodeColor,
        }}
      >
        {/* Agent avatar badge - positioned at top right */}
        {data.agent && (
          <div className="absolute -top-3 -right-3 z-10">
            <div className="rounded-full border-2 border-border bg-background shadow-sm">
              <AgentAvatar name={data.agent.name} state={data.agent.state} size="sm" />
            </div>
          </div>
        )}
        <div className="flex items-center gap-2 mb-1">
          <StatusIcon />
          <span className="text-xs font-mono opacity-70">
            #{data.priority}
          </span>
          {/* Show agent name inline if present */}
          {data.agent && (
            <span className="text-xs font-bold ml-auto">
              {data.agent.name}
            </span>
          )}
        </div>
        <div className="font-medium text-sm truncate" title={data.name}>
          {data.name}
        </div>
        <div className="text-xs opacity-70 truncate" title={data.category}>
          {data.category}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-border !w-2 !h-2" />
    </>
  )
}

const nodeTypes = {
  feature: FeatureNode,
}

// Layout nodes using dagre
function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'LR'
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  const isHorizontal = direction === 'LR'
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 100,
    marginx: 50,
    marginy: 50,
  })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
      targetPosition: isHorizontal ? Position.Left : Position.Top,
    }
  })

  return { nodes: layoutedNodes, edges }
}

function DependencyGraphInner({ graphData, onNodeClick, activeAgents = [] }: DependencyGraphProps) {
  const [direction, setDirection] = useState<'TB' | 'LR'>('LR')

  // Use ref for callback to avoid triggering re-renders when callback identity changes
  const onNodeClickRef = useRef(onNodeClick)
  useEffect(() => {
    onNodeClickRef.current = onNodeClick
  }, [onNodeClick])

  // Create a stable click handler that uses the ref
  const handleNodeClick = useCallback((nodeId: number) => {
    onNodeClickRef.current?.(nodeId)
  }, [])

  // Create a map of featureId to agent info for quick lookup
  // Maps ALL batch feature IDs to the same agent
  const agentByFeatureId = useMemo(() => {
    const map = new Map<number, NodeAgentInfo>()
    for (const agent of activeAgents) {
      const ids = agent.featureIds || [agent.featureId]
      for (const fid of ids) {
        map.set(fid, { name: agent.agentName, state: agent.state })
      }
    }
    return map
  }, [activeAgents])

  // Convert graph data to React Flow format
  // Only recalculate when graphData or direction changes (not when onNodeClick changes)
  const initialElements = useMemo(() => {
    const nodes: Node[] = graphData.nodes.map((node) => ({
      id: String(node.id),
      type: 'feature',
      position: { x: 0, y: 0 },
      data: {
        ...node,
        onClick: () => handleNodeClick(node.id),
        agent: agentByFeatureId.get(node.id),
      },
    }))

    const edgeColor = getComputedStyle(document.documentElement).getPropertyValue('--color-graph-edge').trim() || '#a1a1aa'

    const edges: Edge[] = graphData.edges.map((edge, index) => ({
      id: `e${edge.source}-${edge.target}-${index}`,
      source: String(edge.source),
      target: String(edge.target),
      type: 'smoothstep',
      animated: false,
      style: { stroke: edgeColor, strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edgeColor,
      },
    }))

    return getLayoutedElements(nodes, edges, direction)
  }, [graphData, direction, handleNodeClick, agentByFeatureId])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialElements.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialElements.edges)

  // Update layout when initialElements changes
  // Using a ref to track previous graph data to avoid unnecessary updates
  const prevGraphDataRef = useRef<string>('')
  const prevDirectionRef = useRef<'TB' | 'LR'>(direction)

  useEffect(() => {
    // Create a simple hash of the graph data to detect actual changes
    // Include agent assignments so nodes update when agents change
    const agentInfo = Array.from(agentByFeatureId.entries()).map(([id, agent]) => ({
      featureId: id,
      agentName: agent.name,
      agentState: agent.state,
    }))
    const graphHash = JSON.stringify({
      nodes: graphData.nodes.map(n => ({ id: n.id, status: n.status })),
      edges: graphData.edges,
      agents: agentInfo,
    })

    // Only update if graph data or direction actually changed
    if (graphHash !== prevGraphDataRef.current || direction !== prevDirectionRef.current) {
      prevGraphDataRef.current = graphHash
      prevDirectionRef.current = direction

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialElements.nodes,
        initialElements.edges,
        direction
      )
      setNodes(layoutedNodes)
      setEdges(layoutedEdges)
    }
  }, [graphData, direction, setNodes, setEdges, initialElements, agentByFeatureId])

  const onLayout = useCallback(
    (newDirection: 'TB' | 'LR') => {
      setDirection(newDirection)
    },
    []
  )

  // Color nodes for minimap using CSS variables
  const minimapNodeColor = useCallback((node: Node) => {
    const status = (node.data as unknown as GraphNode).status
    const style = getComputedStyle(document.documentElement)
    switch (status) {
      case 'done':
        return style.getPropertyValue('--color-graph-node-done').trim() || '#22c55e'
      case 'in_progress':
        return style.getPropertyValue('--color-graph-node-progress').trim() || '#06b6d4'
      case 'blocked':
        return style.getPropertyValue('--color-graph-node-failing').trim() || '#ef4444'
      default:
        return style.getPropertyValue('--color-graph-node-pending').trim() || '#eab308'
    }
  }, [])

  if (graphData.nodes.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-muted">
        <div className="text-center">
          <div className="text-muted-foreground mb-2">No features to display</div>
          <div className="text-sm text-muted-foreground/70">
            Create features to see the dependency graph
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative bg-background">
      {/* Layout toggle */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <Button
          variant={direction === 'LR' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onLayout('LR')}
        >
          Horizontal
        </Button>
        <Button
          variant={direction === 'TB' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onLayout('TB')}
        >
          Vertical
        </Button>
      </div>

      {/* Legend */}
      <Card className="absolute top-4 right-4 z-10">
        <CardContent className="p-4">
          <div className="text-xs font-medium mb-2">Status</div>
          <div className="space-y-1.5">
            {[
              { label: 'Pending', colorVar: 'var(--color-graph-node-pending)' },
              { label: 'In Progress', colorVar: 'var(--color-graph-node-progress)' },
              { label: 'Done', colorVar: 'var(--color-graph-node-done)' },
              { label: 'Blocked', colorVar: 'var(--color-graph-node-failing)' },
            ].map(({ label, colorVar }) => (
              <div key={label} className="flex items-center gap-2 text-xs">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: colorVar, border: `1px solid ${colorVar}` }}
                />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="var(--color-graph-bg)" gap={20} size={1} />
        <Controls
          className="!bg-card !border !border-border !rounded-lg !shadow-sm"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={minimapNodeColor}
          className="!bg-card !border !border-border !rounded-lg !shadow-sm"
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  )
}

// Wrapper component with error boundary for stability
export function DependencyGraph({ graphData, onNodeClick, activeAgents }: DependencyGraphProps) {
  // Use a key based on graph data length to force remount on structural changes
  // This helps recover from corrupted ReactFlow state
  const [resetKey, setResetKey] = useState(0)

  const handleReset = useCallback(() => {
    setResetKey(k => k + 1)
  }, [])

  return (
    <GraphErrorBoundary key={resetKey} onReset={handleReset}>
      <DependencyGraphInner graphData={graphData} onNodeClick={onNodeClick} activeAgents={activeAgents} />
    </GraphErrorBoundary>
  )
}
