/**
 * BuildPlannerPage - AI-powered build planning tool.
 *
 * Full-page layout at /#/build-planner providing:
 * - Project basics (name, description, tech stack)
 * - Dynamic rule blocks with AI-powered combination
 * - Feature list with size estimation
 * - Build settings (model, turns, phase transitions, error handling)
 * - Phase assignments
 * - Prompt generation for PRD, phase splitting, and build scripts
 */

import { useState, useCallback } from 'react'
import {
  ArrowLeft,
  Plus,
  Minus,
  Copy,
  Wand2,
  Cpu,
  Settings,
  Layers,
  Rocket,
  Sparkles,
  X,
  Loader2,
  Check,
  ChevronDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FeatureRow {
  id: number
  name: string
  size: 'S' | 'M' | 'L'
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TECH_STACKS = [
  'React + Python',
  'React + Node',
  'Next.js',
  'React Only',
  'Vue + Python',
  'Other',
]

const MODELS = [
  { label: 'Sonnet', value: 'claude-sonnet-4-6-20250514' },
  { label: 'Opus', value: 'claude-opus-4-6-20250514' },
  { label: 'Haiku', value: 'claude-haiku-4-5-20250414' },
]

const TURNS_OPTIONS = ['10', '25', '50', 'Unlimited']
const TRANSITION_OPTIONS = ['Pause', 'Auto-continue', 'Prompt me']
const ERROR_OPTIONS = ['Retry once then skip', 'Stop everything', 'Skip immediately']
const GIT_OPTIONS = ['After each feature', 'After each phase', 'Never']
const PHASE_COUNT_OPTIONS = ['2', '3', '4', '5', '6+']

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV
  ? 'http://localhost:8888'
  : ''

async function callGenerate(prompt: string, model: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/build-planner/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, model }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Generation failed')
  }
  const data = await res.json()
  return data.result
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {
    // Fallback for older browsers
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  })
}

// ---------------------------------------------------------------------------
// Subcomponents
// ---------------------------------------------------------------------------

function SectionCard({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      {children}
    </div>
  )
}

function TextInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <div>
      <label className="block text-sm text-zinc-400 mb-1.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors"
      />
    </div>
  )
}

function TextArea({
  label,
  value,
  onChange,
  rows = 3,
  placeholder,
  readOnly,
}: {
  label?: string
  value: string
  onChange?: (v: string) => void
  rows?: number
  placeholder?: string
  readOnly?: boolean
}) {
  return (
    <div>
      {label && <label className="block text-sm text-zinc-400 mb-1.5">{label}</label>}
      <textarea
        value={value}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        rows={rows}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors resize-y ${
          readOnly ? 'opacity-80 cursor-default' : ''
        }`}
      />
    </div>
  )
}

function SelectInput({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  options: string[] | { label: string; value: string }[]
}) {
  return (
    <div>
      <label className="block text-sm text-zinc-400 mb-1.5">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors pr-8"
        >
          {options.map((opt) => {
            const label = typeof opt === 'string' ? opt : opt.label
            const val = typeof opt === 'string' ? opt : opt.value
            return (
              <option key={val} value={val}>
                {label}
              </option>
            )
          })}
        </select>
        <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
      </div>
    </div>
  )
}

function OutputArea({
  label,
  value,
  loading,
  error,
  onRunWithAI,
  aiResult,
  aiLoading,
}: {
  label: string
  value: string
  loading?: boolean
  error?: string | null
  onRunWithAI: () => void
  aiResult?: string
  aiLoading?: boolean
}) {
  const [copied, setCopied] = useState(false)
  const [aiCopied, setAiCopied] = useState(false)

  const handleCopy = useCallback((text: string, setter: (v: boolean) => void) => {
    copyToClipboard(text)
    setter(true)
    setTimeout(() => setter(false), 2000)
  }, [])

  if (!value && !loading && !error) return null

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-400">{label}</span>
        <div className="flex gap-2">
          <button
            onClick={() => handleCopy(value, setCopied)}
            className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors px-2 py-1 rounded border border-zinc-700 hover:border-zinc-500"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={onRunWithAI}
            disabled={aiLoading || !value}
            className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 transition-colors px-2 py-1 rounded border border-purple-700/50 hover:border-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {aiLoading ? <Loader2 size={12} className="animate-spin" /> : <Wand2 size={12} />}
            {aiLoading ? 'Running...' : 'Run with AI'}
          </button>
        </div>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-zinc-400 py-4">
          <Loader2 size={16} className="animate-spin" />
          Generating...
        </div>
      ) : error ? (
        <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2">
          {error}
        </div>
      ) : (
        <pre className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-300 whitespace-pre-wrap max-h-96 overflow-y-auto font-mono text-xs leading-relaxed">
          {value}
        </pre>
      )}

      {/* AI Result */}
      {aiResult && (
        <div className="mt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-purple-400 flex items-center gap-1">
              <Sparkles size={14} />
              AI Response
            </span>
            <button
              onClick={() => handleCopy(aiResult, setAiCopied)}
              className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors px-2 py-1 rounded border border-zinc-700 hover:border-zinc-500"
            >
              {aiCopied ? <Check size={12} /> : <Copy size={12} />}
              {aiCopied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className="bg-purple-950/20 border border-purple-800/30 rounded-lg px-4 py-3 text-sm text-zinc-300 whitespace-pre-wrap max-h-96 overflow-y-auto font-mono text-xs leading-relaxed">
            {aiResult}
          </pre>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function BuildPlannerPage() {
  // ---- Project Basics ----
  const [appName, setAppName] = useState('')
  const [appDescription, setAppDescription] = useState('')
  const [techStack, setTechStack] = useState(TECH_STACKS[0])

  // ---- Rule Blocks ----
  const [ruleBlocks, setRuleBlocks] = useState<string[]>(['', '', ''])
  const [combinedRules, setCombinedRules] = useState('')
  const [combiningRules, setCombiningRules] = useState(false)
  const [combineError, setCombineError] = useState<string | null>(null)

  // ---- Features ----
  const [features, setFeatures] = useState<FeatureRow[]>([
    { id: 1, name: '', size: 'M' },
  ])
  const [dependencies, setDependencies] = useState('')
  let nextFeatureId = features.length > 0 ? Math.max(...features.map((f) => f.id)) + 1 : 1

  // ---- Build Settings ----
  const [model, setModel] = useState(MODELS[0].value)
  const [turns, setTurns] = useState('25')
  const [transition, setTransition] = useState(TRANSITION_OPTIONS[0])
  const [errorHandling, setErrorHandling] = useState(ERROR_OPTIONS[0])
  const [gitCommits, setGitCommits] = useState(GIT_OPTIONS[0])
  const [phaseCount, setPhaseCount] = useState('3')

  // ---- Phase Assignments ----
  const [phaseAssignments, setPhaseAssignments] = useState('')

  // ---- Outputs ----
  const [prdPrompt, setPrdPrompt] = useState('')
  const [phasePrompt, setPhasePrompt] = useState('')
  const [buildPrompt, setBuildPrompt] = useState('')

  const [prdAiResult, setPrdAiResult] = useState('')
  const [phaseAiResult, setPhaseAiResult] = useState('')
  const [buildAiResult, setBuildAiResult] = useState('')

  const [prdAiLoading, setPrdAiLoading] = useState(false)
  const [phaseAiLoading, setPhaseAiLoading] = useState(false)
  const [buildAiLoading, setBuildAiLoading] = useState(false)

  // ---- Rule block handlers ----
  const addRuleBlock = () => setRuleBlocks((prev) => [...prev, ''])
  const removeLastRuleBlock = () => {
    if (ruleBlocks.length > 1) setRuleBlocks((prev) => prev.slice(0, -1))
  }
  const updateRuleBlock = (index: number, value: string) => {
    setRuleBlocks((prev) => {
      const next = [...prev]
      next[index] = value
      return next
    })
  }

  const combineRules = async () => {
    const nonEmpty = ruleBlocks.filter((b) => b.trim())
    if (nonEmpty.length === 0) return

    setCombiningRules(true)
    setCombineError(null)
    try {
      const prompt = `I have ${nonEmpty.length} separate rule blocks for an AI coding agent. Combine them into ONE cohesive, non-redundant set of rules. Remove duplicates. Resolve conflicts (later blocks take priority). Keep the same level of detail.\n\n${nonEmpty.join('\n\n---\n\n')}`
      const result = await callGenerate(prompt, model)
      setCombinedRules(result)
    } catch (err) {
      setCombineError(err instanceof Error ? err.message : 'Failed to combine rules')
    } finally {
      setCombiningRules(false)
    }
  }

  // ---- Feature handlers ----
  const addFeature = () => {
    setFeatures((prev) => [...prev, { id: nextFeatureId++, name: '', size: 'M' }])
  }
  const removeFeature = (id: number) => {
    setFeatures((prev) => prev.filter((f) => f.id !== id))
  }
  const updateFeature = (id: number, field: 'name' | 'size', value: string) => {
    setFeatures((prev) =>
      prev.map((f) => (f.id === id ? { ...f, [field]: value } : f))
    )
  }

  // ---- Rules text helper ----
  const getRulesText = () => {
    if (combinedRules) return combinedRules
    const nonEmpty = ruleBlocks.filter((b) => b.trim())
    return nonEmpty.join('\n\n')
  }

  // ---- Feature list text ----
  const getFeatureListText = () => {
    return features
      .filter((f) => f.name.trim())
      .map((f, i) => `${i + 1}. ${f.name} [${f.size}]`)
      .join('\n')
  }

  // ---- Prompt assembly ----
  const generatePRD = () => {
    const prompt = `You are a senior software architect. Create a detailed PRD for:

App: ${appName || '[App Name]'}
Description: ${appDescription || '[App Description]'}
Tech Stack: ${techStack}

Features:
${getFeatureListText() || '[No features defined]'}

Dependencies:
${dependencies || '[No dependencies defined]'}

Build Rules:
${getRulesText() || '[No rules defined]'}

Create a comprehensive PRD with:
1. Every feature with detailed acceptance criteria
2. Technical architecture
3. Data models and API endpoints
4. UI/UX flow descriptions
5. Edge cases and error handling`
    setPrdPrompt(prompt)
    setPrdAiResult('')
  }

  const generatePhaseSplit = () => {
    const prdOutput = prdAiResult || '[Paste your PRD here]'
    const prompt = `Split this PRD into ${phaseCount} build phases for Claude Code sessions.

PRD:
${prdOutput}

Rules:
- Phase 1 = project setup + foundation (2-3 features max, heavy on rules)
- Phase 2+ = feature building (3-5 features per phase)
- Respect dependencies: if B depends on A, A goes first
- Each phase gets a fresh context window

Settings:
- Turns per phase: ${turns}
- Phase transition: ${transition}

Output a detailed phase plan with feature assignments.`
    setPhasePrompt(prompt)
    setPhaseAiResult('')
  }

  const generateBuildScripts = () => {
    const phasePlanOutput = phaseAiResult || phaseAssignments || '[Paste your phase plan here]'
    const prompt = `Generate bash scripts for a phased Claude Code build.

Phase Plan:
${phasePlanOutput}

Settings:
- Model: ${MODELS.find((m) => m.value === model)?.label || model}
- Max turns: ${turns}
- Between phases: ${transition}
- On error: ${errorHandling}
- Git: ${gitCommits}

Build Rules (include in Phase 1, summarize in Phase 2+):
${getRulesText() || '[No rules defined]'}

Generate:
1. phase1.sh through phaseN.sh (each calls claude --model ${model} --max-turns ${turns === 'Unlimited' ? '0' : turns} --print "...")
2. run_all.sh master script with phase transitions`
    setBuildPrompt(prompt)
    setBuildAiResult('')
  }

  // ---- Run with AI handlers ----
  const runPrdWithAI = async () => {
    if (!prdPrompt) return
    setPrdAiLoading(true)
    try {
      const result = await callGenerate(prdPrompt, model)
      setPrdAiResult(result)
    } catch (err) {
      setPrdAiResult(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setPrdAiLoading(false)
    }
  }

  const runPhaseWithAI = async () => {
    if (!phasePrompt) return
    setPhaseAiLoading(true)
    try {
      const result = await callGenerate(phasePrompt, model)
      setPhaseAiResult(result)
    } catch (err) {
      setPhaseAiResult(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setPhaseAiLoading(false)
    }
  }

  const runBuildWithAI = async () => {
    if (!buildPrompt) return
    setBuildAiLoading(true)
    try {
      const result = await callGenerate(buildPrompt, model)
      setBuildAiResult(result)
    } catch (err) {
      setBuildAiResult(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setBuildAiLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-zinc-800/60">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => { window.location.hash = '' }}
              className="text-zinc-400 hover:text-white transition-colors"
              title="Back to AutoForge"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-cyan-400 bg-clip-text text-transparent">
                Build Planner
              </h1>
              <p className="text-xs text-zinc-500 mt-0.5">
                Design your build. Generate your scripts. Ship your app.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Rocket size={20} className="text-purple-400" />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Section 1: Project Basics */}
        <SectionCard
          icon={<Cpu size={18} className="text-purple-400" />}
          title="Project Basics"
        >
          <div className="space-y-4">
            <TextInput
              label="App Name"
              value={appName}
              onChange={setAppName}
              placeholder="My Awesome App"
            />
            <TextArea
              label="App Description"
              value={appDescription}
              onChange={setAppDescription}
              rows={3}
              placeholder="A brief description of what your app does, who it's for, and what makes it special..."
            />
            <SelectInput
              label="Tech Stack"
              value={techStack}
              onChange={setTechStack}
              options={TECH_STACKS}
            />
          </div>
        </SectionCard>

        {/* Section 2: Build Rules */}
        <SectionCard
          icon={<Sparkles size={18} className="text-cyan-400" />}
          title="Build Rules"
        >
          <p className="text-sm text-zinc-500 mb-4">
            Define rules for the AI coding agent. Each block can be a separate concern (styling, architecture, testing, etc.). Use "Combine Rules" to merge them with AI.
          </p>
          <div className="space-y-3">
            {ruleBlocks.map((block, i) => (
              <div key={i}>
                <label className="block text-xs text-zinc-500 mb-1">
                  Rule Block {i + 1}
                </label>
                <textarea
                  value={block}
                  onChange={(e) => updateRuleBlock(i, e.target.value)}
                  rows={4}
                  placeholder={
                    i === 0
                      ? 'e.g., Use TypeScript strict mode. All components must be functional...'
                      : i === 1
                        ? 'e.g., Follow mobile-first responsive design. Use Tailwind CSS...'
                        : 'e.g., Write unit tests for all utility functions...'
                  }
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors resize-y"
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            <Button
              onClick={addRuleBlock}
              variant="outline"
              size="sm"
              className="gap-1 border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500 bg-transparent"
            >
              <Plus size={14} />
              Add Rule Block
            </Button>
            <Button
              onClick={removeLastRuleBlock}
              variant="outline"
              size="sm"
              disabled={ruleBlocks.length <= 1}
              className="gap-1 border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500 bg-transparent disabled:opacity-40"
            >
              <Minus size={14} />
              Remove Last
            </Button>
            <Button
              onClick={combineRules}
              disabled={combiningRules || ruleBlocks.every((b) => !b.trim())}
              size="sm"
              className="gap-1 bg-gradient-to-r from-purple-600 to-cyan-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40"
            >
              {combiningRules ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Wand2 size={14} />
              )}
              Combine Rules
            </Button>
          </div>
          {/* Combined rules output */}
          {(combinedRules || combiningRules || combineError) && (
            <div className="mt-4">
              {combiningRules ? (
                <div className="flex items-center gap-2 text-sm text-zinc-400 py-3">
                  <Loader2 size={16} className="animate-spin" />
                  Combining rules with AI...
                </div>
              ) : combineError ? (
                <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2">
                  {combineError}
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-purple-400 flex items-center gap-1">
                      <Sparkles size={14} />
                      Combined Rules
                    </span>
                    <button
                      onClick={() => copyToClipboard(combinedRules)}
                      className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors px-2 py-1 rounded border border-zinc-700 hover:border-zinc-500"
                    >
                      <Copy size={12} />
                      Copy
                    </button>
                  </div>
                  <pre className="bg-purple-950/20 border border-purple-800/30 rounded-lg px-4 py-3 text-sm text-zinc-300 whitespace-pre-wrap max-h-64 overflow-y-auto font-mono text-xs leading-relaxed">
                    {combinedRules}
                  </pre>
                </div>
              )}
            </div>
          )}
        </SectionCard>

        {/* Section 3: Features */}
        <SectionCard
          icon={<Layers size={18} className="text-green-400" />}
          title="Features"
        >
          <div className="space-y-2">
            {features.map((feature) => (
              <div key={feature.id} className="flex items-center gap-2">
                <input
                  type="text"
                  value={feature.name}
                  onChange={(e) => updateFeature(feature.id, 'name', e.target.value)}
                  placeholder="Feature name..."
                  className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors"
                />
                <div className="relative">
                  <select
                    value={feature.size}
                    onChange={(e) => updateFeature(feature.id, 'size', e.target.value)}
                    className="appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none transition-colors pr-7 w-16"
                  >
                    <option value="S">S</option>
                    <option value="M">M</option>
                    <option value="L">L</option>
                  </select>
                  <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
                </div>
                <button
                  onClick={() => removeFeature(feature.id)}
                  className="text-zinc-500 hover:text-red-400 transition-colors p-1"
                  title="Remove feature"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
          <Button
            onClick={addFeature}
            variant="outline"
            size="sm"
            className="gap-1 mt-3 border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500 bg-transparent"
          >
            <Plus size={14} />
            Add Feature
          </Button>
          <div className="mt-4">
            <TextArea
              label="Dependencies"
              value={dependencies}
              onChange={setDependencies}
              rows={3}
              placeholder="Describe which features depend on which, e.g.:\n- Auth must be built before Dashboard\n- API layer is required by all frontend features"
            />
          </div>
        </SectionCard>

        {/* Section 4: Build Settings */}
        <SectionCard
          icon={<Settings size={18} className="text-amber-400" />}
          title="Build Settings"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <SelectInput
              label="Model"
              value={model}
              onChange={setModel}
              options={MODELS}
            />
            <SelectInput
              label="Turns per Phase"
              value={turns}
              onChange={setTurns}
              options={TURNS_OPTIONS}
            />
            <SelectInput
              label="Phase Transition"
              value={transition}
              onChange={setTransition}
              options={TRANSITION_OPTIONS}
            />
            <SelectInput
              label="Error Handling"
              value={errorHandling}
              onChange={setErrorHandling}
              options={ERROR_OPTIONS}
            />
            <SelectInput
              label="Git Commits"
              value={gitCommits}
              onChange={setGitCommits}
              options={GIT_OPTIONS}
            />
            <SelectInput
              label="Number of Phases"
              value={phaseCount}
              onChange={setPhaseCount}
              options={PHASE_COUNT_OPTIONS}
            />
          </div>
        </SectionCard>

        {/* Section 5: Phase Assignments */}
        <SectionCard
          icon={<Layers size={18} className="text-indigo-400" />}
          title="Phase Assignments"
        >
          <TextArea
            value={phaseAssignments}
            onChange={setPhaseAssignments}
            rows={5}
            placeholder={"Phase 1: Project setup, Auth system\nPhase 2: Dashboard, API endpoints\nPhase 3: Settings page, User management\n..."}
          />
        </SectionCard>

        {/* Section 6: Generate */}
        <SectionCard
          icon={<Rocket size={18} className="text-purple-400" />}
          title="Generate"
        >
          <p className="text-sm text-zinc-500 mb-5">
            Generate prompts step-by-step: PRD first, then phase split, then build scripts. Each button assembles the prompt and shows it below so you can copy or run it with AI.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={generatePRD}
              className="flex flex-col items-center gap-2 bg-gradient-to-br from-purple-600/20 to-purple-800/20 border border-purple-700/40 rounded-xl px-4 py-5 text-white hover:border-purple-500/60 hover:from-purple-600/30 hover:to-purple-800/30 transition-all group"
            >
              <div className="w-10 h-10 rounded-full bg-purple-600/30 flex items-center justify-center group-hover:bg-purple-600/50 transition-colors">
                <Sparkles size={20} className="text-purple-300" />
              </div>
              <span className="font-semibold text-sm">Generate PRD Prompt</span>
              <span className="text-xs text-zinc-500">Project details + rules + features</span>
            </button>
            <button
              onClick={generatePhaseSplit}
              className="flex flex-col items-center gap-2 bg-gradient-to-br from-cyan-600/20 to-cyan-800/20 border border-cyan-700/40 rounded-xl px-4 py-5 text-white hover:border-cyan-500/60 hover:from-cyan-600/30 hover:to-cyan-800/30 transition-all group"
            >
              <div className="w-10 h-10 rounded-full bg-cyan-600/30 flex items-center justify-center group-hover:bg-cyan-600/50 transition-colors">
                <Layers size={20} className="text-cyan-300" />
              </div>
              <span className="font-semibold text-sm">Generate Phase-Split Prompt</span>
              <span className="text-xs text-zinc-500">Split PRD into build phases</span>
            </button>
            <button
              onClick={generateBuildScripts}
              className="flex flex-col items-center gap-2 bg-gradient-to-br from-green-600/20 to-green-800/20 border border-green-700/40 rounded-xl px-4 py-5 text-white hover:border-green-500/60 hover:from-green-600/30 hover:to-green-800/30 transition-all group"
            >
              <div className="w-10 h-10 rounded-full bg-green-600/30 flex items-center justify-center group-hover:bg-green-600/50 transition-colors">
                <Rocket size={20} className="text-green-300" />
              </div>
              <span className="font-semibold text-sm">Generate Build Scripts Prompt</span>
              <span className="text-xs text-zinc-500">Create executable bash scripts</span>
            </button>
          </div>

          {/* PRD Output */}
          <OutputArea
            label="PRD Prompt"
            value={prdPrompt}
            onRunWithAI={runPrdWithAI}
            aiResult={prdAiResult}
            aiLoading={prdAiLoading}
          />

          {/* Phase Split Output */}
          <OutputArea
            label="Phase-Split Prompt"
            value={phasePrompt}
            onRunWithAI={runPhaseWithAI}
            aiResult={phaseAiResult}
            aiLoading={phaseAiLoading}
          />

          {/* Build Scripts Output */}
          <OutputArea
            label="Build Scripts Prompt"
            value={buildPrompt}
            onRunWithAI={runBuildWithAI}
            aiResult={buildAiResult}
            aiLoading={buildAiLoading}
          />
        </SectionCard>

        {/* Footer spacing */}
        <div className="h-12" />
      </main>
    </div>
  )
}
