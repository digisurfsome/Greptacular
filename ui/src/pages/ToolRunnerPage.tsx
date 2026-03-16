/**
 * ToolRunnerPage — Hybrid Execution Engine UI for YT Lab tool chains.
 *
 * Route: /#/tools/:toolId/run
 *
 * Layout:
 *   Left panel  — chain steps list with status indicators
 *   Center panel — current step output (prompt + result)
 *   Right panel  — variables panel (editable inputs)
 *   Bottom bar   — Run All / Run Step / Pause / Resume / Stop controls
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  ArrowLeft,
  Play,
  Square,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  ChevronRight,
  Zap,
  Globe,
  FileText,
  MousePointer,
  Webhook,
  Eye,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChainStep {
  row_number: number
  title: string
  step_type: string
  execution_mode: string
  prompt_template: string
  expected_output: string
  model_recommendation: string
  apis_required: string[]
  is_gate: boolean
  webhook_url?: string
}

interface StepResult {
  step_number: number
  title: string
  step_type: string
  execution_mode: string
  status: 'pending' | 'running' | 'done' | 'error' | 'skipped' | 'waiting'
  output: string
  action_result?: Record<string, unknown>
  error?: string
  tokens_used: number
  duration_seconds: number
}

interface RunEvent {
  type: string
  run_id?: string
  tool_name?: string
  total_steps?: number
  step_number?: number
  title?: string
  step_type?: string
  execution_mode?: string
  message?: string
  result?: StepResult
  error?: string
  output_so_far?: string
  status?: string
  total_tokens?: number
  duration?: number
  steps_completed?: number
}

interface Tool {
  tool_id: string
  blueprint: {
    tool_name: string
    tool_description: string
    chain_config: ChainStep[]
    user_input_variables: string[]
  }
  status: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStepTypeIcon(stepType: string, execMode: string) {
  if (execMode === 'computer_use') return <MousePointer className="w-3.5 h-3.5" />
  if (execMode === 'direct_action') return <Zap className="w-3.5 h-3.5" />
  if (execMode === 'human_checkpoint') return <Eye className="w-3.5 h-3.5" />
  switch (stepType) {
    case 'research': return <Globe className="w-3.5 h-3.5" />
    case 'file_create': return <FileText className="w-3.5 h-3.5" />
    case 'webhook': return <Webhook className="w-3.5 h-3.5" />
    case 'browser_action': return <MousePointer className="w-3.5 h-3.5" />
    case 'api_call': return <Zap className="w-3.5 h-3.5" />
    default: return <ChevronRight className="w-3.5 h-3.5" />
  }
}

function getStepStatusColor(status: string) {
  switch (status) {
    case 'done': return 'text-green-400'
    case 'running': return 'text-cyan-400'
    case 'error': return 'text-red-400'
    case 'waiting': return 'text-yellow-400'
    case 'skipped': return 'text-gray-500'
    default: return 'text-gray-400'
  }
}

function StepStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'done': return <CheckCircle className="w-4 h-4 text-green-400" />
    case 'running': return <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
    case 'error': return <XCircle className="w-4 h-4 text-red-400" />
    case 'waiting': return <Eye className="w-4 h-4 text-yellow-400" />
    default: return <Clock className="w-4 h-4 text-gray-600" />
  }
}

function execModeLabel(mode: string): string {
  switch (mode) {
    case 'ai_only': return 'AI'
    case 'ai_then_act': return 'AI + Act'
    case 'direct_action': return 'Direct'
    case 'computer_use': return 'Browser'
    case 'human_checkpoint': return 'Review'
    default: return mode
  }
}

function execModeBadgeColor(mode: string): string {
  switch (mode) {
    case 'ai_only': return 'bg-blue-900/50 text-blue-300 border-blue-700'
    case 'ai_then_act': return 'bg-purple-900/50 text-purple-300 border-purple-700'
    case 'direct_action': return 'bg-yellow-900/50 text-yellow-300 border-yellow-700'
    case 'computer_use': return 'bg-orange-900/50 text-orange-300 border-orange-700'
    case 'human_checkpoint': return 'bg-cyan-900/50 text-cyan-300 border-cyan-700'
    default: return 'bg-gray-800 text-gray-400 border-gray-600'
  }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ToolRunnerPage() {
  const hash = window.location.hash
  // Parse /#/tools/:toolId/run
  const toolId = hash.replace('#/tools/', '').replace('/run', '').split('/')[0] ?? ''

  const [tool, setTool] = useState<Tool | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Run state
  const [runStatus, setRunStatus] = useState<'idle' | 'running' | 'paused' | 'done' | 'error' | 'cancelled'>('idle')
  const [stepStatuses, setStepStatuses] = useState<Record<number, StepResult>>({})
  const [activeStep, setActiveStep] = useState<number | null>(null)
  const [logs, setLogs] = useState<Array<{ step: number | null; msg: string }>>([])
  const [totalTokens, setTotalTokens] = useState(0)
  const [runDuration, setRunDuration] = useState<number | null>(null)

  // Variables panel
  const [variables, setVariables] = useState<Record<string, string>>({})

  // Selected step for center panel
  const [selectedStep, setSelectedStep] = useState<number>(1)

  const evtSourceRef = useRef<EventSource | null>(null)
  const logsEndRef = useRef<HTMLDivElement | null>(null)

  // Load tool
  useEffect(() => {
    if (!toolId) return
    setLoading(true)
    fetch(`/api/tool-factory/tools/${toolId}`)
      .then(r => r.json())
      .then((data: Tool) => {
        setTool(data)
        // Init variables
        const initVars: Record<string, string> = {}
        for (const v of data.blueprint.user_input_variables ?? []) {
          initVars[v] = ''
        }
        setVariables(initVars)
        setSelectedStep(data.blueprint.chain_config[0]?.row_number ?? 1)
        setLoading(false)
      })
      .catch(err => {
        setError(String(err))
        setLoading(false)
      })
  }, [toolId])

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const appendLog = useCallback((step: number | null, msg: string) => {
    setLogs(prev => [...prev.slice(-499), { step, msg }])
  }, [])

  // Run all steps
  const startRun = useCallback(() => {
    if (!tool || runStatus === 'running') return

    setRunStatus('running')
    setStepStatuses({})
    setLogs([])
    setTotalTokens(0)
    setRunDuration(null)

    const url = `/api/tool-runner/${toolId}/run`
    const body = JSON.stringify({ variables, start_from_step: 1 })

    // Use fetch + ReadableStream for SSE
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    }).then(async resp => {
      if (!resp.ok) {
        setRunStatus('error')
        setError(`HTTP ${resp.status}`)
        return
      }
      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event: RunEvent = JSON.parse(line.slice(6))
            handleRunEvent(event)
          } catch {
            // ignore parse errors
          }
        }
      }
    }).catch(err => {
      setRunStatus('error')
      setError(String(err))
    })
  }, [tool, toolId, variables, runStatus])

  const handleRunEvent = useCallback((event: RunEvent) => {
    switch (event.type) {
      case 'run_started':
        appendLog(null, `▶ Run started: ${event.tool_name} (${event.total_steps} steps)`)
        break

      case 'step_started':
        setActiveStep(event.step_number!)
        setSelectedStep(event.step_number!)
        setStepStatuses(prev => ({
          ...prev,
          [event.step_number!]: {
            step_number: event.step_number!,
            title: event.title!,
            step_type: event.step_type!,
            execution_mode: event.execution_mode!,
            status: 'running',
            output: '',
            tokens_used: 0,
            duration_seconds: 0,
          },
        }))
        appendLog(event.step_number!, `⚡ Step ${event.step_number}: ${event.title} [${event.execution_mode}]`)
        break

      case 'log':
        appendLog(event.step_number ?? null, event.message!)
        break

      case 'step_done':
        if (event.result) {
          setStepStatuses(prev => ({ ...prev, [event.result!.step_number]: event.result! }))
          appendLog(event.step_number!, `✅ Step ${event.step_number} done (${event.result.duration_seconds?.toFixed(1)}s)`)
        }
        break

      case 'step_error':
        if (event.result) {
          setStepStatuses(prev => ({ ...prev, [event.result!.step_number]: event.result! }))
        }
        appendLog(event.step_number!, `❌ Step ${event.step_number} error: ${event.error}`)
        break

      case 'checkpoint':
        setRunStatus('paused')
        appendLog(event.step_number!, `⏸ Checkpoint: ${event.title} — review required`)
        break

      case 'run_done':
        setRunStatus(event.status === 'done' ? 'done' : (event.status as typeof runStatus))
        setActiveStep(null)
        setTotalTokens(event.total_tokens ?? 0)
        setRunDuration(event.duration ?? null)
        appendLog(null, `🏁 Run complete: ${event.steps_completed} steps | ${event.duration?.toFixed(1)}s`)
        break

      case 'run_error':
        setRunStatus('error')
        setError(event.error!)
        appendLog(null, `💥 Run error: ${event.error}`)
        break
    }
  }, [appendLog])

  const stopRun = useCallback(() => {
    evtSourceRef.current?.close()
    setRunStatus('cancelled')
    appendLog(null, '⏹ Run cancelled by user')
  }, [appendLog])

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    )
  }

  if (error && !tool) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-red-400">
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-3" />
          <p className="text-lg font-medium">Failed to load tool</p>
          <p className="text-sm text-gray-500 mt-1">{error}</p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => { window.location.hash = '#/tools' }}
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Tools
          </Button>
        </div>
      </div>
    )
  }

  if (!tool) return null

  const steps = tool.blueprint.chain_config
  const selectedStepData = steps.find(s => s.row_number === selectedStep)
  const selectedResult = stepStatuses[selectedStep]
  const isRunning = runStatus === 'running'
  const isDone = runStatus === 'done' || runStatus === 'cancelled' || runStatus === 'error'

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/10 bg-[#111]">
        <div className="flex items-center gap-3">
          <button
            onClick={() => { window.location.hash = '#/tools' }}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-base font-semibold text-white leading-tight">{tool.blueprint.tool_name}</h1>
            <p className="text-xs text-gray-500 leading-tight">{tool.blueprint.tool_description}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-400">
          {totalTokens > 0 && (
            <span className="bg-blue-900/30 border border-blue-700/40 px-2 py-0.5 rounded text-blue-300">
              {(totalTokens / 1000).toFixed(1)}K tokens
            </span>
          )}
          {runDuration && (
            <span className="bg-gray-800 border border-gray-700 px-2 py-0.5 rounded">
              {runDuration.toFixed(1)}s
            </span>
          )}
          <span className={`px-2 py-0.5 rounded border font-medium ${
            runStatus === 'running' ? 'bg-cyan-900/40 text-cyan-300 border-cyan-700' :
            runStatus === 'done' ? 'bg-green-900/40 text-green-300 border-green-700' :
            runStatus === 'error' ? 'bg-red-900/40 text-red-300 border-red-700' :
            runStatus === 'paused' ? 'bg-yellow-900/40 text-yellow-300 border-yellow-700' :
            'bg-gray-800 text-gray-400 border-gray-700'
          }`}>
            {runStatus.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left: Step list */}
        <div className="w-64 flex-shrink-0 border-r border-white/10 bg-[#0d0d0d] flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b border-white/10 text-xs font-medium text-gray-400 uppercase tracking-wide">
            Chain Steps ({steps.length})
          </div>
          <div className="flex-1 overflow-y-auto">
            {steps.map(step => {
              const result = stepStatuses[step.row_number]
              const status = result?.status ?? (step.row_number === activeStep ? 'running' : 'pending')
              const isSelected = selectedStep === step.row_number

              return (
                <button
                  key={step.row_number}
                  onClick={() => setSelectedStep(step.row_number)}
                  className={`w-full text-left px-3 py-2.5 border-b border-white/5 flex items-start gap-2 transition-colors hover:bg-white/5 ${
                    isSelected ? 'bg-white/8 border-l-2 border-l-cyan-500' : ''
                  }`}
                >
                  <div className="mt-0.5 flex-shrink-0">
                    <StepStatusIcon status={status} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="text-xs text-gray-500 font-mono">{step.row_number}</span>
                      <div className={`flex-shrink-0 ${getStepStatusColor(status)}`}>
                        {getStepTypeIcon(step.step_type, step.execution_mode)}
                      </div>
                    </div>
                    <p className={`text-xs font-medium leading-tight truncate ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                      {step.title}
                    </p>
                    <span className={`inline-block mt-1 text-[10px] px-1.5 py-0 rounded border ${execModeBadgeColor(step.execution_mode)}`}>
                      {execModeLabel(step.execution_mode)}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Center: Step detail */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {selectedStepData ? (
            <>
              {/* Step header */}
              <div className="px-5 py-3 border-b border-white/10 bg-[#0d0d0d]">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-gray-500">Step {selectedStepData.row_number}</span>
                  <span className={`text-[10px] px-1.5 py-0 rounded border ${execModeBadgeColor(selectedStepData.execution_mode)}`}>
                    {execModeLabel(selectedStepData.execution_mode)}
                  </span>
                  <span className="text-[10px] px-1.5 py-0 rounded border border-gray-700 text-gray-400">
                    {selectedStepData.step_type}
                  </span>
                  {selectedStepData.model_recommendation && (
                    <span className="text-[10px] px-1.5 py-0 rounded border border-gray-700 text-gray-500">
                      {selectedStepData.model_recommendation}
                    </span>
                  )}
                </div>
                <h2 className="text-sm font-semibold text-white">{selectedStepData.title}</h2>
                <p className="text-xs text-gray-400 mt-0.5">{selectedStepData.expected_output}</p>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {/* Prompt template */}
                <div>
                  <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Prompt Template</h3>
                  <pre className="bg-[#111] border border-white/10 rounded-lg p-3 text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed max-h-48 overflow-y-auto">
                    {selectedStepData.prompt_template}
                  </pre>
                </div>

                {/* Output */}
                {selectedResult && (
                  <div>
                    <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      Output
                      {selectedResult.duration_seconds > 0 && (
                        <span className="text-gray-600 font-normal normal-case">({selectedResult.duration_seconds.toFixed(1)}s)</span>
                      )}
                    </h3>
                    {selectedResult.status === 'error' ? (
                      <div className="bg-red-900/20 border border-red-700/40 rounded-lg p-3">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                          <p className="text-xs text-red-300 font-mono">{selectedResult.error}</p>
                        </div>
                      </div>
                    ) : selectedResult.status === 'running' ? (
                      <div className="flex items-center gap-2 text-cyan-400 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Executing...</span>
                      </div>
                    ) : selectedResult.output ? (
                      <pre className="bg-[#111] border border-white/10 rounded-lg p-3 text-xs text-green-200 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto">
                        {selectedResult.output}
                      </pre>
                    ) : null}

                    {selectedResult.action_result && Object.keys(selectedResult.action_result).length > 0 && (
                      <div className="mt-2">
                        <h3 className="text-xs font-medium text-gray-500 mb-1">Action Result</h3>
                        <pre className="bg-[#111] border border-white/10 rounded-lg p-2 text-xs text-yellow-200 font-mono max-h-32 overflow-y-auto">
                          {JSON.stringify(selectedResult.action_result, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
              Select a step to view details
            </div>
          )}

          {/* Log panel */}
          <div className="h-36 border-t border-white/10 bg-[#0a0a0a] flex flex-col">
            <div className="px-3 py-1.5 border-b border-white/10 text-xs font-medium text-gray-500 uppercase tracking-wide">
              Execution Log
            </div>
            <div className="flex-1 overflow-y-auto px-3 py-1.5 space-y-0.5">
              {logs.map((entry, i) => (
                <p key={i} className="text-[11px] text-gray-400 font-mono leading-tight">
                  {entry.step != null && (
                    <span className="text-gray-600">[{entry.step}] </span>
                  )}
                  {entry.msg}
                </p>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>

        {/* Right: Variables */}
        <div className="w-56 flex-shrink-0 border-l border-white/10 bg-[#0d0d0d] flex flex-col">
          <div className="px-3 py-2 border-b border-white/10 text-xs font-medium text-gray-400 uppercase tracking-wide">
            Variables
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {Object.keys(variables).length === 0 ? (
              <p className="text-xs text-gray-600 italic">No variables for this tool</p>
            ) : (
              Object.entries(variables).map(([key, val]) => (
                <div key={key}>
                  <label className="text-[11px] text-gray-400 font-mono block mb-1">{key}</label>
                  <textarea
                    value={val}
                    onChange={e => setVariables(prev => ({ ...prev, [key]: e.target.value }))}
                    disabled={isRunning}
                    rows={2}
                    className="w-full bg-[#111] border border-white/10 rounded px-2 py-1 text-xs text-gray-200 font-mono resize-none focus:outline-none focus:border-cyan-600 disabled:opacity-50"
                    placeholder={`Enter ${key}...`}
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Bottom control bar */}
      <div className="flex items-center justify-between px-5 py-2.5 border-t border-white/10 bg-[#111]">
        <div className="flex items-center gap-2">
          {!isRunning && !isDone && (
            <Button
              size="sm"
              onClick={startRun}
              className="bg-cyan-600 hover:bg-cyan-500 text-white border-0 gap-1.5"
            >
              <Play className="w-4 h-4" />
              Run All
            </Button>
          )}
          {isRunning && (
            <Button
              size="sm"
              variant="outline"
              onClick={stopRun}
              className="border-red-700 text-red-400 hover:bg-red-900/20 gap-1.5"
            >
              <Square className="w-4 h-4" />
              Stop
            </Button>
          )}
          {(isDone) && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setRunStatus('idle')
                setStepStatuses({})
                setLogs([])
                setTotalTokens(0)
                setRunDuration(null)
                setActiveStep(null)
              }}
              className="border-gray-700 text-gray-300 hover:bg-white/5 gap-1.5"
            >
              <RefreshCw className="w-4 h-4" />
              Reset
            </Button>
          )}
        </div>

        <div className="text-xs text-gray-500">
          {steps.length} steps · {tool.blueprint.user_input_variables?.length ?? 0} variables
        </div>
      </div>
    </div>
  )
}
