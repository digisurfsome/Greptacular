/**
 * CliScripterPage - AI-powered CLI script generation tool.
 *
 * Full-page layout at /#/cli-scripter providing:
 * - Project basics (name, description, tech stack)
 * - Dynamic rule blocks with AI-powered combination
 * - Feature list with size estimation
 * - Build settings (model, turns, phase transitions, error handling)
 * - Agent roles with customizable prompts per pipeline step
 * - Phase assignments
 * - Generate All (PRD -> Phases -> Scripts) plus individual generation
 * - Write scripts to disk
 * - Build queue for multi-app runs
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { usePersistedState } from '@/hooks/usePersistedState'
import { ClearButton } from '@/components/cli-scripter/ClearButton'
import { ProjectFileBrowser } from '@/components/cli-scripter/ProjectFileBrowser'
import { RuleBlockLibrary, createEmptyBlock, type RuleBlockData } from '@/components/cli-scripter/RuleBlock'
import { Combiner, getMergedText } from '@/components/cli-scripter/Combiner'
import { GatePopup, NEW_BUILD_PREFIX, EDIT_PATCH_PREFIX, type BuildMode, type PhaseMode } from '@/components/cli-scripter/GatePopup'
import { BuildLibrary, type BuildConfigFull } from '@/components/cli-scripter/BuildLibrary'
import { PromptBar } from '@/components/cli-scripter/PromptBar'
import { BuildDashboard } from '@/components/cli-scripter/BuildDashboard'
import { BuildLogPanel } from '@/components/cli-scripter/BuildLogPanel'
import { parseWaves, sequentialWaves } from '@/lib/waveParser'
import {
  ArrowLeft,
  Plus,
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
  Eye,
  EyeOff,
  Github,
  ExternalLink,
  Users,
  ListOrdered,
  ChevronUp,
  Terminal,
  FileText,
  Shield,
  Map,
  Zap,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { validateGitHubToken, createGitHubRepo } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FeatureRow {
  id: number
  name: string
  size: 'S' | 'M' | 'L'
}

interface AgentRole {
  id: string
  name: string
  model: string
  enabled: boolean
  prompt: string
  description: string
  runsWhen: string // once_before | per_phase | per_phase_after | once_after | once_final
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

interface Boilerplate {
  id: string
  label: string
  tech: string
  templateOwner: string | null
  templateRepo: string | null
}

const BOILERPLATES: Boilerplate[] = [
  {
    id: 'web-supabase-stripe',
    label: 'Web App (Supabase + Stripe)',
    tech: 'Next.js + TypeScript + Supabase + Stripe + PostHog + Loops.so + Netlify',
    templateOwner: 'digisurfsome',
    templateRepo: 'Web-BoilerPlate-D2D',
  },
  {
    id: 'mobile-flutter-firebase',
    label: 'Flutter Starter (Firebase)',
    tech: 'Flutter + Dart + Firebase + Riverpod + RevenueCat + Mixpanel + Sentry + GoRouter',
    templateOwner: 'digisurfsome',
    templateRepo: 'apparence-kit-firebase',
  },
  {
    id: 'web-mobile-supabase',
    label: 'Full Stack (Web + Mobile)',
    tech: 'Next.js + Flutter + Dart + TypeScript + Supabase + Stripe + PostHog',
    templateOwner: 'digisurfsome',
    templateRepo: 'Web-BoilerPlate-D2D',
  },
  {
    id: 'scratch',
    label: 'From Scratch',
    tech: 'You decide during spec creation',
    templateOwner: null,
    templateRepo: null,
  },
]

const MODELS = [
  { label: 'Sonnet', value: 'sonnet' },
  { label: 'Opus', value: 'opus' },
  { label: 'Haiku', value: 'haiku' },
]

const TURNS_OPTIONS = ['10', '25', '50', 'Unlimited']
const TRANSITION_OPTIONS = ['Pause', 'Auto-continue', 'Prompt me']
const ERROR_OPTIONS = ['Retry once then skip', 'Stop everything', 'Skip immediately']
const GIT_OPTIONS = ['After each feature', 'After each phase', 'Never']
const PHASE_COUNT_OPTIONS = ['Auto', '2', '3', '4', '5', '6+']

const DEFAULT_AGENT_ROLES: AgentRole[] = [
  {
    id: 'architect',
    name: 'Architect',
    model: 'opus',
    enabled: true,
    runsWhen: 'once_before',
    description: 'Creates ARCHITECTURE.md before coding — file structure, API contracts, data models',
    prompt: `You are a senior software architect. Read the PRD and build rules below, then create ARCHITECTURE.md in the project root.

ARCHITECTURE.md must contain:
1. **File Structure** — every file that will be created, organized by directory
2. **Data Models** — every database table/model with fields and types
3. **API Contracts** — every endpoint with method, path, request body, response body
4. **Component Tree** — every React component with props and parent-child relationships
5. **Shared Constants** — enums, config values, type names that multiple files reference
6. **Naming Conventions** — how files, functions, variables, and endpoints are named

This document is the single source of truth. Every coding agent will read it before writing code.

{build_rules}

{prd_content}`,
  },
  {
    id: 'coder',
    name: 'Coder',
    model: 'sonnet',
    enabled: true,
    runsWhen: 'per_phase',
    description: 'Implements features for each phase — reads ARCHITECTURE.md to stay aligned',
    prompt: `You are building Phase {phase_number} of {total_phases}.

FIRST: Read ARCHITECTURE.md in the project root. Follow its file structure, API contracts, data models, and naming conventions EXACTLY.

{build_rules}

{phase_spec}

BEFORE YOU FINISH:
1. Run ruff check on all Python files you created/modified
2. Run npm run build in ui/ to verify TypeScript compiles
3. Run npm run lint in ui/ to verify ESLint passes
4. Run any tests you wrote — all must pass
5. Fix any failures before committing
6. Commit your work with a descriptive message`,
  },
  {
    id: 'reviewer',
    name: 'Reviewer',
    model: 'opus',
    enabled: true,
    runsWhen: 'per_phase_after',
    description: 'Reviews code after each phase — catches bugs before the next phase starts',
    prompt: `You are a code reviewer. Phase {phase_number} of {total_phases} was just completed.

Review ALL code written in this phase:
1. Run ruff check on all Python files
2. Run npm run build to check TypeScript
3. Run npm run lint for ESLint
4. Run all tests
5. Read every new/modified file and check for:
   - Logic errors, missing null checks, off-by-one
   - Missing error handling
   - Integration mismatches with ARCHITECTURE.md
   - Security issues
   - Unused imports, dead code

Fix any Critical or High issues. Commit fixes with: "review(phase-{phase_number}): [description]"
Do NOT refactor working code for style. Only fix actual bugs.`,
  },
  {
    id: 'verifier',
    name: 'Verifier',
    model: 'opus',
    enabled: true,
    runsWhen: 'once_after',
    description: 'Full post-build verification — integration testing, bug hunting, edge cases',
    prompt: `Run full post-build verification:
1. Run all linters and type checkers
2. Run full test suite
3. Review all code for integration bugs
4. Check API contract consistency between frontend and backend
5. Test error handling and edge cases
6. Fix all Critical and High issues found
7. Commit all fixes`,
  },
  {
    id: 'cartographer',
    name: 'Cartographer',
    model: 'sonnet',
    enabled: true,
    runsWhen: 'once_final',
    description: 'Documents the codebase after build — creates the map for future agents',
    prompt: `You are a technical documentation specialist. The build is complete and verified.

Create or update:
1. **ARCHITECTURE.md** — Update with what was ACTUALLY built (final file structure, real API endpoints, DB schema)
2. **CONVENTIONS.md** — Document patterns: naming, imports, error handling, state management
3. **CLAUDE.md** — Add "## Codebase Map" with project summary, key directories, how to run, common gotchas

Read every source file. Document what's actually in the code, not what the PRD planned.`,
  },
]

// Role icon mapping
const ROLE_ICONS: Record<string, React.ReactNode> = {
  architect: <FileText size={16} className="text-purple-400" />,
  coder: <Terminal size={16} className="text-cyan-400" />,
  reviewer: <Shield size={16} className="text-orange-400" />,
  verifier: <Zap size={16} className="text-red-400" />,
  cartographer: <Map size={16} className="text-green-400" />,
}

const ROLE_MODEL_OPTIONS = [
  { label: 'Opus', value: 'opus' },
  { label: 'Sonnet', value: 'sonnet' },
  { label: 'Haiku', value: 'haiku' },
]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.DEV
  ? 'http://localhost:8888'
  : ''

async function callGenerate(prompt: string, model: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/cli-scripter/generate`, {
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
    <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl p-6 shadow-sm">
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
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 pr-8 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors"
        />
        <ClearButton
          value={value}
          onClear={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2"
        />
      </div>
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
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-sm text-zinc-400">{label}</label>
          {onChange && !readOnly && (
            <ClearButton value={value} onClear={() => onChange('')} />
          )}
        </div>
      )}
      <textarea
        value={value}
        onChange={onChange ? (e) => onChange(e.target.value) : undefined}
        rows={rows}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors resize-y ${
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
          className="w-full appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors pr-8"
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

export function CliScripterPage() {
  // ---- Project Basics (persisted to localStorage) ----
  const [appName, setAppName] = usePersistedState('cli_scripter_app_name', '')
  const [appDescription, setAppDescription] = usePersistedState('cli_scripter_app_description', '')
  const [boilerplate, setBoilerplate] = usePersistedState<string>('cli_scripter_boilerplate', BOILERPLATES[0].id)

  // ---- GitHub Repo Creation ----
  const [createRepo, setCreateRepo] = useState(false)
  const [repoName, setRepoName] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [githubUser, setGithubUser] = useState<{ login: string; name: string; avatar_url: string } | null>(null)
  const [githubValidating, setGithubValidating] = useState(false)
  const [githubError, setGithubError] = useState<string | null>(null)
  const [repoCreating, setRepoCreating] = useState(false)
  const [repoUrl, setRepoUrl] = useState<string | null>(null)
  const [repoError, setRepoError] = useState<string | null>(null)

  // ---- Rule Blocks (persisted to localStorage) ----
  const [ruleBlocks, setRuleBlocks] = usePersistedState<RuleBlockData[]>('cli_scripter_rule_blocks_v2', [
    createEmptyBlock(0),
  ])
  const [combinedRules, setCombinedRules] = usePersistedState('cli_scripter_combined_rules', '')
  const [combiningRules, setCombiningRules] = useState(false)
  const [combineError, setCombineError] = useState<string | null>(null)

  // ---- Gate popup (build mode + phase mode) ----
  const [gateOpen, setGateOpen] = useState(false)
  const [buildMode, setBuildMode] = usePersistedState<BuildMode>('cli_scripter_build_mode', 'new')
  const [phaseMode, setPhaseMode] = usePersistedState<PhaseMode>('cli_scripter_last_phase_mode', 'single')

  // ---- Phase-Specific Rules ("Top Bun") (persisted) ----
  // splitPhaseRules is now driven by phaseMode from the gate popup
  const splitPhaseRules = phaseMode === 'split'

  // ---- Backend sync for rule blocks ----
  const rulesLoadedRef = useRef(false)
  const rulesSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load rules from backend on mount
  useEffect(() => {
    if (rulesLoadedRef.current) return
    rulesLoadedRef.current = true

    fetch(`${API_BASE}/api/cli-scripter/rules`)
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data && Array.isArray(data.blocks) && data.blocks.length > 0) {
          setRuleBlocks(data.blocks as RuleBlockData[])
        }
      })
      .catch(() => {
        // Backend unavailable — fall back to localStorage (already loaded)
      })
  }, [])

  // Debounced save to backend on every ruleBlocks change (1 second)
  useEffect(() => {
    if (!rulesLoadedRef.current) return // Don't save during initial load

    if (rulesSaveTimerRef.current) {
      clearTimeout(rulesSaveTimerRef.current)
    }
    rulesSaveTimerRef.current = setTimeout(() => {
      fetch(`${API_BASE}/api/cli-scripter/rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version: 1,
          blocks: ruleBlocks,
          last_phase_mode: phaseMode,
        }),
      }).catch(() => {
        // Backend unavailable — localStorage still has the data
      })
    }, 1000)

    return () => {
      if (rulesSaveTimerRef.current) {
        clearTimeout(rulesSaveTimerRef.current)
      }
    }
  }, [ruleBlocks, phaseMode])
  const [phase1Rules, setPhase1Rules] = usePersistedState('cli_scripter_phase1_rules', '')
  const [phase2PlusRules, setPhase2PlusRules] = usePersistedState('cli_scripter_phase2plus_rules', '')

  // ---- Features (optional — skip if you already have a PRD) (persisted) ----
  const [features, setFeatures] = usePersistedState<FeatureRow[]>('cli_scripter_features', [
    { id: 1, name: '', size: 'M' },
  ])
  const [dependencies, setDependencies] = usePersistedState('cli_scripter_dependencies', '')
  const [showFeatures, setShowFeatures] = usePersistedState('cli_scripter_show_features', false)
  let nextFeatureId = features.length > 0 ? Math.max(...features.map((f) => f.id)) + 1 : 1

  // ---- Build Settings ----
  // Model defaults to sonnet; each agent role has its own model selector
  const model = MODELS[0].value
  const [turns, setTurns] = usePersistedState('cli_scripter_turns', '25')
  const [transition, setTransition] = usePersistedState('cli_scripter_transition', TRANSITION_OPTIONS[0])
  const [errorHandling, setErrorHandling] = usePersistedState('cli_scripter_error_handling', ERROR_OPTIONS[0])
  const [gitCommits, setGitCommits] = usePersistedState('cli_scripter_git_commits', GIT_OPTIONS[0])
  const [phaseCount, setPhaseCount] = usePersistedState('cli_scripter_phase_count', 'Auto')
  const [parallelMode, setParallelMode] = usePersistedState('cli_scripter_parallel_mode', false)

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

  // ---- Agent Roles (persisted) ----
  const [agentRoles, setAgentRoles] = usePersistedState<AgentRole[]>('cli_scripter_roles', DEFAULT_AGENT_ROLES)
  const [expandedRole, setExpandedRole] = useState<string | null>(null)

  // ---- Include verification (persisted) ----
  const [includeVerification, setIncludeVerification] = usePersistedState('cli_scripter_include_verification', true)

  // ---- Generate All ----
  const [generateAllLoading, setGenerateAllLoading] = useState(false)
  const [generateAllStep, setGenerateAllStep] = useState(0)
  const [generateAllError, setGenerateAllError] = useState<string | null>(null)

  // ---- Script writing ----
  const [scriptsWritten, setScriptsWritten] = useState<string[] | null>(null)
  const [writingScripts, setWritingScripts] = useState(false)
  const [writeError, setWriteError] = useState<string | null>(null)
  const [projectDir, setProjectDir] = usePersistedState('cli_scripter_project_dir', '')

  // ---- Build Queue (persisted) ----
  const [queueItems, setQueueItems] = usePersistedState<Array<{name: string, project_dir: string, scripts_dir?: string, status: string}>>('cli_scripter_queue', [])

  // ---- Build Library ----
  const [libraryOpen, setLibraryOpen] = usePersistedState('cli_scripter_library_open', false)

  // ---- Build Dashboard (refresh interval in ms, default 30s) ----
  // setBuildRefreshInterval is used by the RefreshIntervalSelector component (Phase 6)
  const [buildRefreshInterval, setBuildRefreshInterval] = usePersistedState('cli_scripter_refresh_interval', 30000)
  void setBuildRefreshInterval // Suppress unused warning until Phase 6 adds the selector UI

  // ---- Parsed wave structure (derived from phase AI result) ----
  const parsedWaves = useCallback(() => {
    const src = phaseAiResult || phaseAssignments
    if (!src) return []
    const waves = parseWaves(src)
    return waves.length > 0 ? waves : []
  }, [phaseAiResult, phaseAssignments])

  const selectedBoilerplate = BOILERPLATES.find((b) => b.id === boilerplate) || BOILERPLATES[0]

  // ---- GitHub helpers ----
  const slugifyName = (name: string) =>
    name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

  const effectiveRepoName = repoName.trim() || slugifyName(appName)

  const handleValidateToken = async (token: string) => {
    if (!token.trim()) return
    setGithubValidating(true)
    setGithubError(null)
    setGithubUser(null)
    try {
      const user = await validateGitHubToken(token)
      setGithubUser(user)
      localStorage.setItem('github_pat', token)
    } catch (err) {
      setGithubError(err instanceof Error ? err.message : 'Token validation failed')
    } finally {
      setGithubValidating(false)
    }
  }

  const handleCreateRepo = async () => {
    if (!githubToken || !effectiveRepoName) return
    setRepoCreating(true)
    setRepoError(null)
    setRepoUrl(null)
    try {
      const result = await createGitHubRepo({
        token: githubToken,
        repo_name: effectiveRepoName,
        private: true,
        description: appDescription || undefined,
        template_owner: selectedBoilerplate.templateOwner || undefined,
        template_repo: selectedBoilerplate.templateRepo || undefined,
      })
      setRepoUrl(result.repo_url)
    } catch (err) {
      setRepoError(err instanceof Error ? err.message : 'Repo creation failed')
    } finally {
      setRepoCreating(false)
    }
  }

  // Load saved GitHub token on mount and auto-validate
  useEffect(() => {
    const saved = localStorage.getItem('github_pat')
    if (saved) {
      setGithubToken(saved)
      handleValidateToken(saved)
    }
    // Run only on mount
  }, [])

  // Auto-populate phase assignments from AI phase split result
  useEffect(() => {
    if (phaseAiResult) {
      setPhaseAssignments(phaseAiResult)
    }
  }, [phaseAiResult])

  // ---- Rule block handlers ----
  const combineRules = async () => {
    const nonEmpty = ruleBlocks.filter((b) => b.content.trim())
    if (nonEmpty.length === 0) return

    setCombiningRules(true)
    setCombineError(null)
    try {
      const texts = nonEmpty.map((b) => b.content.trim())
      const prompt = `I have ${texts.length} separate rule blocks for an AI coding agent. Combine them into ONE cohesive, non-redundant set of rules. Remove duplicates. Resolve conflicts (later blocks take priority). Keep the same level of detail.\n\n${texts.join('\n\n---\n\n')}`
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
  // Uses combiner slots if blocks have combiner checkboxes set, otherwise falls back
  // to AI-combined text or raw concatenation of all blocks
  const getRulesText = () => {
    if (combinedRules) return combinedRules
    // Try Main Combined slot first
    const mainMerged = getMergedText(ruleBlocks, 'main')
    if (mainMerged) return mainMerged
    // Fallback: concatenate all non-empty blocks
    const nonEmpty = ruleBlocks.filter((b) => b.content.trim()).map((b) => b.content.trim())
    return nonEmpty.join('\n\n')
  }

  // ---- Phase-specific rules helper ----
  const getRulesForPhase = (phaseNum: number) => {
    if (!splitPhaseRules) return getRulesText() // all phases same
    if (phaseNum === 1) {
      // Try P1 combiner slot first, then phase1Rules, then general rules
      const p1Merged = getMergedText(ruleBlocks, 'p1')
      return p1Merged || phase1Rules || getRulesText()
    }
    // Phase 2+: Try P2+ combiner slot first, then phase2PlusRules, then general rules
    const p2Merged = getMergedText(ruleBlocks, 'p2plus')
    return p2Merged || phase2PlusRules || getRulesText()
  }

  // ---- Token estimation (rough: 1 token ≈ 4 chars) ----
  const estimateTokens = (text: string) => Math.ceil(text.length / 4)

  const getPhase1CabRide = () => {
    const rules = getRulesForPhase(1)
    const architectPrompt = agentRoles.find(r => r.id === 'architect')?.prompt || ''
    const coderPrompt = agentRoles.find(r => r.id === 'coder')?.prompt || ''
    return estimateTokens(rules) + estimateTokens(architectPrompt) + estimateTokens(coderPrompt)
  }

  const getPhase2PlusCabRide = () => {
    const rules = getRulesForPhase(2)
    const coderPrompt = agentRoles.find(r => r.id === 'coder')?.prompt || ''
    const reviewerPrompt = agentRoles.find(r => r.id === 'reviewer')?.prompt || ''
    return estimateTokens(rules) + estimateTokens(coderPrompt) + estimateTokens(reviewerPrompt)
  }

  const TOKEN_BUDGET = 100000 // max tokens per phase
  const BUFFER_PCT = 0.10 // 10% safety buffer

  // ---- Feature list text ----
  const getFeatureListText = () => {
    return features
      .filter((f) => f.name.trim())
      .map((f, i) => `${i + 1}. ${f.name} [${f.size}]`)
      .join('\n')
  }

  // ---- Agent role handler ----
  const updateRole = (roleId: string, updates: Partial<AgentRole>) => {
    setAgentRoles(prev => prev.map(r => r.id === roleId ? { ...r, ...updates } : r))
  }

  // ---- Prompt assembly ----
  const generatePRD = () => {
    const prompt = `You are a senior software architect. Create a detailed PRD for:

App: ${appName || '[App Name]'}
Description: ${appDescription || '[App Description]'}
Boilerplate: ${selectedBoilerplate.label}
Tech Stack: ${selectedBoilerplate.tech}${selectedBoilerplate.id !== 'scratch' ? `\n\nNote: This project uses the ${selectedBoilerplate.label} boilerplate. Many foundational features are already built. Focus the PRD on NEW features the user wants to add on top.` : ''}

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
    const p1Cab = getPhase1CabRide()
    const p2Cab = getPhase2PlusCabRide()
    const p1Available = Math.floor((TOKEN_BUDGET - p1Cab) * (1 - BUFFER_PCT))
    const p2Available = Math.floor((TOKEN_BUDGET - p2Cab) * (1 - BUFFER_PCT))

    const phaseCountText = phaseCount === 'Auto'
      ? 'as many phases as needed to stay under the token budget'
      : `${phaseCount} build phases`
    const prompt = `Split this PRD into ${phaseCountText} for Claude Code sessions.

PRD:
${prdOutput}

TOKEN BUDGET CONSTRAINTS:
- Each phase gets a fresh ${TOKEN_BUDGET.toLocaleString()}-token context window
- Phase 1 cab ride: ~${p1Cab.toLocaleString()} tokens → ${p1Available.toLocaleString()} available for content
- Phase 2+ cab ride: ~${p2Cab.toLocaleString()} tokens → ${p2Available.toLocaleString()} available for content
${splitPhaseRules ? '- Phase 1 uses FULL rules. Phase 2+ uses CONDENSED rules.' : '- All phases use the same rules.'}

SPLITTING RULES:
- Phase 1 = project setup + foundation (2-3 features max)
- Phase 2+ = feature building (3-5 features per phase)
- Respect dependencies: if B depends on A, A goes first
- Each phase must be testable on its own
- Find natural break points between feature groups
- IMPORTANT: After splitting, state which phases can run IN PARALLEL (no cross-dependencies) vs which must run sequentially. Format your answer with execution waves, e.g.: "Wave 1: [Phase 1] → Wave 2: [Phase 2, Phase 3] (parallel, no dependencies between them) → Wave 3: [Phase 4] (depends on Phase 2 and 3)"

TESTING PHASE SIZING:
- If the build has 3+ feature phases, the post-build verification (Verifier role) needs its OWN dedicated phase at the end.
- If the build has 6+ feature phases, give verification TWO phases (split by backend vs frontend).
- The verification phase prompt is long and thorough — budget at least 80,000 tokens for it.
- This means: for a 4-phase feature build, output 5 phases total (4 features + 1 verification).

Settings:
- Turns per phase: ${turns}
- Phase transition: ${transition}

Output a detailed phase plan with feature assignments and estimated token usage.`
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

  // ---- Helper to build PRD prompt text without setting state ----
  const buildPrdPromptText = () => {
    return `${getBuildModePrefix()}

You are a senior software architect. Create a detailed PRD for:

App: ${appName || '[App Name]'}
Description: ${appDescription || '[App Description]'}
Boilerplate: ${selectedBoilerplate.label}
Tech Stack: ${selectedBoilerplate.tech}

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
  }

  // ---- Gate popup handler ----
  const handleGateConfirm = (selectedBuildMode: BuildMode, selectedPhaseMode: PhaseMode) => {
    setBuildMode(selectedBuildMode)
    setPhaseMode(selectedPhaseMode)
    setGateOpen(false)
    // Proceed with generation
    runGenerateAll()
  }

  // ---- Get build mode prefix for prompt injection ----
  const getBuildModePrefix = () => {
    return buildMode === 'new' ? NEW_BUILD_PREFIX : EDIT_PATCH_PREFIX
  }

  // ---- Generate All handler ----
  const runGenerateAll = async () => {
    setGenerateAllLoading(true)
    setGenerateAllStep(1)
    setGenerateAllError(null)

    try {
      // Step 1: Generate PRD
      generatePRD()
      const prdResult = await callGenerate(prdPrompt || buildPrdPromptText(), model)
      setPrdAiResult(prdResult)
      setGenerateAllStep(2)

      // Step 2: Phase Split (with token math)
      const p1Cab = getPhase1CabRide()
      const p2Cab = getPhase2PlusCabRide()
      const p1Available = Math.floor((TOKEN_BUDGET - p1Cab) * (1 - BUFFER_PCT))
      const p2Available = Math.floor((TOKEN_BUDGET - p2Cab) * (1 - BUFFER_PCT))

      const phaseCountText = phaseCount === 'Auto'
        ? 'as many phases as needed to stay under the token budget'
        : `${phaseCount} build phases`
      const phasePromptText = `Split this PRD into ${phaseCountText} for Claude Code sessions.

PRD:
${prdResult}

TOKEN BUDGET CONSTRAINTS (CRITICAL):
- Each phase gets a fresh ${TOKEN_BUDGET.toLocaleString()}-token context window
- Phase 1 "cab ride" (overhead: rules + prompts): ~${p1Cab.toLocaleString()} tokens → ${p1Available.toLocaleString()} tokens available for feature content
- Phase 2+ "cab ride": ~${p2Cab.toLocaleString()} tokens → ${p2Available.toLocaleString()} tokens available for feature content
- ${Math.round(BUFFER_PCT * 100)}% safety buffer is already subtracted
${splitPhaseRules ? '- Phase 1 uses FULL rules. Phase 2+ uses CONDENSED rules referencing what Phase 1 built.' : '- All phases use the same rules.'}

SPLITTING RULES:
- Phase 1 = project setup + foundation (2-3 features max, gets the full rules overhead)
- Phase 2+ = feature building (3-5 features per phase, lighter rules overhead)
- Respect dependencies: if B depends on A, A goes in an earlier phase
- Each phase must be testable on its own — find natural break points
- NEVER split in the middle of a tightly coupled feature group
- IMPORTANT: After splitting, state which phases can run IN PARALLEL (no cross-dependencies). Format: "Wave 1: [Phase 1] → Wave 2: [Phase 2, Phase 3] (parallel) → Wave 3: [Phase 4]"

TESTING PHASE SIZING:
- If the build has 3+ feature phases, the post-build verification (Verifier role) needs its OWN dedicated phase at the end.
- If the build has 6+ feature phases, give verification TWO phases (split by backend vs frontend).
- The verification phase prompt is long and thorough — budget at least 80,000 tokens for it.
- This means: for a 4-phase feature build, output 5 phases total (4 features + 1 verification).

Settings:
- Turns per phase: ${turns}
- Phase transition: ${transition}

Output a detailed phase plan with feature assignments, estimated token usage per phase, and execution wave groupings.`
      const phaseResult = await callGenerate(phasePromptText, model)
      setPhaseAiResult(phaseResult)

      // Step 3 is now DETERMINISTIC — no LLM needed for script assembly.
      // Scripts are generated via the "Save Scripts to Disk" button which calls /write-scripts.
      // Show a note instead of a spinner for step 3.
      setBuildAiResult('Scripts ready for generation. Click "Save Scripts to Disk" to write deterministic bash scripts — no tokens used.')
      setGenerateAllStep(0)
    } catch (err) {
      setGenerateAllError(err instanceof Error ? err.message : 'Generation failed')
      setGenerateAllStep(0)
    } finally {
      setGenerateAllLoading(false)
    }
  }

  // ---- Write Scripts handler ----
  const handleWriteScripts = async () => {
    if (!projectDir.trim()) {
      setWriteError('Please enter a project directory path')
      return
    }
    setWritingScripts(true)
    setWriteError(null)
    setScriptsWritten(null)

    try {
      const phases = phaseAssignments
        .split('\n')
        .filter(l => l.trim())
        .map(l => l.trim())

      if (phases.length === 0) {
        // Fall back to generating numbered phases
        const fallbackCount = phaseCount === 'Auto' ? 3 : (parseInt(phaseCount) || 3)
        for (let i = 1; i <= fallbackCount; i++) {
          phases.push(`Phase ${i}`)
        }
      }

      const waves = parsedWaves()
      const effectiveWaves = waves.length > 0 ? waves : sequentialWaves(phases.length)

      const res = await fetch(`${API_BASE}/api/cli-scripter/write-scripts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_dir: projectDir,
          project_name: appName || 'my-app',
          build_rules: getRulesText(),
          phases,
          agent_roles: agentRoles.map(r => ({
            id: r.id,
            name: r.name,
            model: r.model,
            enabled: r.enabled,
            prompt: r.prompt,
            description: r.description,
            runs_when: r.runsWhen,
          })),
          include_verification: includeVerification,
          waves: effectiveWaves,
          parallel_mode: parallelMode,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Failed to write scripts')
      }
      const data = await res.json()
      setScriptsWritten(data.files)
    } catch (err) {
      setWriteError(err instanceof Error ? err.message : 'Failed to write scripts')
    } finally {
      setWritingScripts(false)
    }
  }

  // ---- Queue handlers ----
  const addToQueue = () => {
    if (!appName.trim() || !projectDir.trim()) return
    setQueueItems(prev => [...prev, {
      name: appName,
      project_dir: projectDir,
      status: 'pending',
    }])
  }

  const removeFromQueue = (index: number) => {
    setQueueItems(prev => prev.filter((_, i) => i !== index))
  }

  const moveQueueItem = (index: number, direction: 'up' | 'down') => {
    setQueueItems(prev => {
      const next = [...prev]
      const swapIdx = direction === 'up' ? index - 1 : index + 1
      if (swapIdx < 0 || swapIdx >= next.length) return prev
      ;[next[index], next[swapIdx]] = [next[swapIdx], next[index]]
      return next
    })
  }

  // ---- Build Library handlers ----
  const handleLibrarySaveRequest = async () => {
    return {
      name: appName || 'Untitled Build',
      config_json: {
        appName,
        appDescription,
        boilerplate,
        ruleBlocks,
        combinedRules,
        phase1Rules,
        phase2PlusRules,
        features,
        dependencies,
        turns,
        transition,
        errorHandling,
        gitCommits,
        phaseCount,
        agentRoles,
        includeVerification,
        phaseAssignments,
        projectDir,
        buildMode,
        phaseMode,
        // Prompt overrides — null means use auto-generated default
        prompts: {
          prd: prdPrompt || null,
          phase_split: phasePrompt || null,
          build_scripts: buildPrompt || null,
        },
      },
      project_dir: projectDir || undefined,
      phase_count: phaseCount === 'Auto' ? undefined : parseInt(phaseCount) || undefined,
    }
  }

  const handleLibraryLoad = (config: BuildConfigFull) => {
    const c = config.config_json as Record<string, unknown>
    if (typeof c.appName === 'string') setAppName(c.appName)
    if (typeof c.appDescription === 'string') setAppDescription(c.appDescription)
    if (typeof c.boilerplate === 'string') setBoilerplate(c.boilerplate)
    if (Array.isArray(c.ruleBlocks)) setRuleBlocks(c.ruleBlocks as RuleBlockData[])
    if (typeof c.combinedRules === 'string') setCombinedRules(c.combinedRules)
    if (typeof c.phase1Rules === 'string') setPhase1Rules(c.phase1Rules)
    if (typeof c.phase2PlusRules === 'string') setPhase2PlusRules(c.phase2PlusRules)
    if (Array.isArray(c.features)) setFeatures(c.features as FeatureRow[])
    if (typeof c.dependencies === 'string') setDependencies(c.dependencies)
    if (typeof c.turns === 'string') setTurns(c.turns)
    if (typeof c.transition === 'string') setTransition(c.transition)
    if (typeof c.errorHandling === 'string') setErrorHandling(c.errorHandling)
    if (typeof c.gitCommits === 'string') setGitCommits(c.gitCommits)
    if (typeof c.phaseCount === 'string') setPhaseCount(c.phaseCount)
    if (Array.isArray(c.agentRoles)) setAgentRoles(c.agentRoles as AgentRole[])
    if (typeof c.includeVerification === 'boolean') setIncludeVerification(c.includeVerification)
    if (typeof c.phaseAssignments === 'string') setPhaseAssignments(c.phaseAssignments)
    if (typeof c.projectDir === 'string') setProjectDir(c.projectDir)
    if (typeof c.buildMode === 'string') setBuildMode(c.buildMode as BuildMode)
    if (typeof c.phaseMode === 'string') setPhaseMode(c.phaseMode as PhaseMode)
    // Restore prompt overrides if saved
    const prompts = c.prompts as Record<string, string | null> | undefined
    if (prompts) {
      if (typeof prompts.prd === 'string') setPrdPrompt(prompts.prd)
      if (typeof prompts.phase_split === 'string') setPhasePrompt(prompts.phase_split)
      if (typeof prompts.build_scripts === 'string') setBuildPrompt(prompts.build_scripts)
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
              <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-400 via-amber-300 to-yellow-400 bg-clip-text text-transparent">
                CLI Scripter
              </h1>
              <p className="text-xs text-zinc-500 mt-0.5">
                Design your build. Generate your scripts. Ship your app.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Terminal size={20} className="text-orange-400" />
          </div>
        </div>
      </header>

      {/* Build Dashboard + Log Panel — shows during active builds */}
      <div className="max-w-4xl mx-auto px-4 pt-4 space-y-2">
        <BuildDashboard
          projectDir={projectDir}
          refreshInterval={buildRefreshInterval}
        />
        <BuildLogPanel
          refreshInterval={buildRefreshInterval}
        />
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Section 1: Project Basics */}
        <SectionCard
          icon={<Cpu size={18} className="text-orange-400" />}
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
              label="Boilerplate"
              value={boilerplate}
              onChange={setBoilerplate}
              options={BOILERPLATES.map((b) => ({ label: b.label, value: b.id }))}
            />
            {selectedBoilerplate && (
              <p className="text-xs text-zinc-500 -mt-2">
                {selectedBoilerplate.tech}
              </p>
            )}

            {/* GitHub Repo — checkbox + name + token */}
            <div className="border-t border-zinc-800 pt-4 mt-2 space-y-3">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={createRepo}
                  onChange={(e) => setCreateRepo(e.target.checked)}
                  className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-orange-500 focus:ring-purple-500 focus:ring-offset-0"
                />
                <Github size={16} className="text-zinc-400" />
                <span className="text-sm text-zinc-300">Create GitHub repo</span>
              </label>

              {createRepo && (
                <div className="space-y-3 pl-6">
                  {/* Repo name */}
                  <div>
                    <label className="block text-xs text-zinc-500 mb-1">Repo Name</label>
                    <input
                      type="text"
                      value={repoName}
                      onChange={(e) => setRepoName(e.target.value)}
                      placeholder={appName ? slugifyName(appName) : 'my-app'}
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors"
                    />
                  </div>

                  {/* Token */}
                  <div>
                    <label className="block text-xs text-zinc-500 mb-1">GitHub Token</label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <input
                          type={showToken ? 'text' : 'password'}
                          value={githubToken}
                          onChange={(e) => {
                            setGithubToken(e.target.value)
                            setGithubUser(null)
                            setGithubError(null)
                          }}
                          placeholder="ghp_..."
                          className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors pr-9"
                        />
                        <button
                          type="button"
                          onClick={() => setShowToken(!showToken)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                        >
                          {showToken ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                      <Button
                        onClick={() => handleValidateToken(githubToken)}
                        disabled={githubValidating || !githubToken.trim()}
                        size="sm"
                        className="gap-1 border-zinc-700 text-zinc-300 hover:text-white hover:border-zinc-500 bg-transparent border disabled:opacity-40"
                      >
                        {githubValidating ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                        Save
                      </Button>
                    </div>
                    {githubError && (
                      <p className="text-xs text-red-400 mt-1">{githubError}</p>
                    )}
                    {githubUser && (
                      <div className="flex items-center gap-2 mt-1.5 text-xs text-green-400">
                        <img src={githubUser.avatar_url} alt={githubUser.login} className="w-4 h-4 rounded-full" />
                        <span>{githubUser.login}</span>
                        <Check size={12} />
                      </div>
                    )}
                  </div>

                  {/* Create button + result */}
                  <div>
                    <Button
                      onClick={handleCreateRepo}
                      disabled={repoCreating || !githubUser || !effectiveRepoName}
                      size="sm"
                      className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40"
                    >
                      {repoCreating ? <Loader2 size={14} className="animate-spin" /> : <Github size={14} />}
                      Create Repo
                    </Button>
                    {selectedBoilerplate.templateRepo && !repoUrl && (
                      <p className="text-xs text-zinc-600 mt-1">
                        From template: {selectedBoilerplate.templateOwner}/{selectedBoilerplate.templateRepo}
                      </p>
                    )}
                    {repoError && <p className="text-xs text-red-400 mt-1">{repoError}</p>}
                    {repoUrl && (
                      <a
                        href={repoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300 mt-1.5 transition-colors"
                      >
                        <ExternalLink size={12} />
                        {repoUrl}
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Project file browser (synced with Generate section's project directory) */}
            <ProjectFileBrowser projectDir={projectDir} />
          </div>
        </SectionCard>

        {/* Section 2: Build Rules */}
        <SectionCard
          icon={<Sparkles size={18} className="text-cyan-400" />}
          title="Build Rules"
        >
          <p className="text-sm text-zinc-500 mb-4">
            Named rule blocks you create once and reuse across builds. Check the sidebar boxes (Main, P1, P2+) to include blocks in combiner slots.
          </p>

          {/* Rule Block Library */}
          <RuleBlockLibrary blocks={ruleBlocks} onBlocksChange={setRuleBlocks} />

          {/* Combiner slots — two-way bound with block checkboxes */}
          {ruleBlocks.length > 0 && (
            <div className="mt-4 pt-3 border-t border-zinc-800">
              <Combiner blocks={ruleBlocks} onBlocksChange={setRuleBlocks} />
            </div>
          )}

          {/* Combine button + output */}
          <div className="mt-4 pt-3 border-t border-zinc-800">
            <Button
              onClick={combineRules}
              disabled={combiningRules || ruleBlocks.every((b) => !b.content.trim())}
              size="sm"
              className="gap-1 bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:opacity-90 transition-opacity border-0 disabled:opacity-40"
            >
              {combiningRules ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Wand2 size={14} />
              )}
              Combine Rules with AI
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

        {/* Section: Phase Rules ("Top Bun") */}
        <SectionCard
          icon={<Layers size={18} className="text-amber-400" />}
          title="Phase Rules"
        >
          <p className="text-sm text-zinc-500 mb-4">
            The "top bun" — rules that get prepended to each phase's prompt. Phase 1 often needs the full ruleset (~1000 lines) while Phase 2+ can reference what's already built (~350 lines).
          </p>

          {/* Toggle */}
          <div className="flex items-center gap-3 mb-4">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={splitPhaseRules}
                onChange={(e) => setPhaseMode(e.target.checked ? 'split' : 'single')}
                className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-orange-500"
              />
              <span className="text-sm text-zinc-300">
                {splitPhaseRules ? 'Phase 1 and Phase 2+ have different rules' : 'All phases use the same rules'}
              </span>
            </label>
          </div>

          {!splitPhaseRules ? (
            <div className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-3">
              <p className="text-xs text-zinc-500 mb-1">Using the Build Rules from above for all phases.</p>
              <p className="text-xs text-zinc-600">
                Estimated cab ride: ~{(getPhase1CabRide()).toLocaleString()} tokens per phase
                {' '}({Math.round(getPhase1CabRide() / TOKEN_BUDGET * 100)}% of {(TOKEN_BUDGET).toLocaleString()} budget)
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Phase 1 rules */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm text-orange-400 font-medium">Phase 1 Rules (Full)</label>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-600">
                      ~{estimateTokens(phase1Rules).toLocaleString()} tokens
                      {' '}• Cab ride: ~{getPhase1CabRide().toLocaleString()}
                      {' '}({Math.round(getPhase1CabRide() / TOKEN_BUDGET * 100)}% of budget)
                    </span>
                    <ClearButton value={phase1Rules} onClear={() => setPhase1Rules('')} />
                  </div>
                </div>
                <textarea
                  value={phase1Rules}
                  onChange={(e) => setPhase1Rules(e.target.value)}
                  rows={6}
                  placeholder="Full ruleset for Phase 1 — complete schematics, coding standards, file structure rules, naming conventions...&#10;&#10;This is your detailed blueprint. The agent has no reference code yet, so be thorough."
                  className="w-full bg-zinc-900 border border-orange-700/40 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors resize-y"
                />
              </div>

              {/* Phase 2+ rules */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm text-cyan-400 font-medium">Phase 2+ Rules (Condensed)</label>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-600">
                      ~{estimateTokens(phase2PlusRules).toLocaleString()} tokens
                      {' '}• Cab ride: ~{getPhase2PlusCabRide().toLocaleString()}
                      {' '}({Math.round(getPhase2PlusCabRide() / TOKEN_BUDGET * 100)}% of budget)
                    </span>
                    <ClearButton value={phase2PlusRules} onClear={() => setPhase2PlusRules('')} />
                  </div>
                </div>
                <textarea
                  value={phase2PlusRules}
                  onChange={(e) => setPhase2PlusRules(e.target.value)}
                  rows={6}
                  placeholder="Condensed rules for Phase 2 onward — references what Phase 1 built, key conventions, critical constraints...&#10;&#10;The codebase exists now, so this is a summary referencing the live code."
                  className="w-full bg-zinc-900 border border-cyan-700/40 rounded-lg px-3 py-2 text-white text-sm focus:border-cyan-500 focus:outline-none transition-colors resize-y"
                />
              </div>

              {/* Token budget summary */}
              <div className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-3 space-y-1">
                <p className="text-xs text-zinc-400 font-medium">Token Budget Summary</p>
                <div className="flex gap-4 text-xs">
                  <span className="text-orange-400">
                    Phase 1: {getPhase1CabRide().toLocaleString()} cab ride → {(TOKEN_BUDGET - getPhase1CabRide()).toLocaleString()} for content
                  </span>
                  <span className="text-cyan-400">
                    Phase 2+: {getPhase2PlusCabRide().toLocaleString()} cab ride → {(TOKEN_BUDGET - getPhase2PlusCabRide()).toLocaleString()} for content
                  </span>
                </div>
                <p className="text-xs text-zinc-600">
                  Budget: {TOKEN_BUDGET.toLocaleString()} tokens/phase • {Math.round(BUFFER_PCT * 100)}% safety buffer
                </p>
              </div>
            </div>
          )}
        </SectionCard>

        {/* Section 3: Features (optional, collapsible) */}
        <div className="bg-zinc-800/40 border border-zinc-700/60 rounded-xl p-6 shadow-sm">
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => setShowFeatures(!showFeatures)}
          >
            <Layers size={18} className="text-green-400" />
            <h2 className="text-lg font-semibold text-white">Features</h2>
            <span className="text-xs text-zinc-600 ml-2">Optional — skip if you already have a PRD</span>
            <div className="flex-1" />
            {showFeatures ? <ChevronUp size={14} className="text-zinc-500" /> : <ChevronDown size={14} className="text-zinc-500" />}
          </div>
          {showFeatures && (
            <div className="mt-4">
              <p className="text-sm text-zinc-500 mb-3">
                Quick feature list for PRD generation. If you're bringing a finished PRD, skip this section entirely.
              </p>
              <div className="space-y-2">
                {features.map((feature) => (
                  <div key={feature.id} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={feature.name}
                      onChange={(e) => updateFeature(feature.id, 'name', e.target.value)}
                      placeholder="Feature name..."
                      className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors"
                    />
                    <div className="relative">
                      <select
                        value={feature.size}
                        onChange={(e) => updateFeature(feature.id, 'size', e.target.value)}
                        className="appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none transition-colors pr-7 w-16"
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
            </div>
          )}
        </div>

        {/* Section 4: Build Settings */}
        <SectionCard
          icon={<Settings size={18} className="text-amber-400" />}
          title="Build Settings"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <SelectInput
                label="Turns per Phase"
                value={turns}
                onChange={setTurns}
                options={TURNS_OPTIONS}
              />
              <p className="text-xs text-zinc-600 mt-1">Max agent conversation turns per phase. 25 is good for most builds.</p>
            </div>
            <div>
              <SelectInput
                label="Phase Transition"
                value={transition}
                onChange={setTransition}
                options={TRANSITION_OPTIONS}
              />
              <p className="text-xs text-zinc-600 mt-1">Pause = wait between phases. Auto-continue = overnight builds.</p>
            </div>
            <div>
              <SelectInput
                label="Error Handling"
                value={errorHandling}
                onChange={setErrorHandling}
                options={ERROR_OPTIONS}
              />
              <p className="text-xs text-zinc-600 mt-1">What to do when a phase fails its lint/type checks.</p>
            </div>
            <div>
              <SelectInput
                label="Git Commits"
                value={gitCommits}
                onChange={setGitCommits}
                options={GIT_OPTIONS}
              />
              <p className="text-xs text-zinc-600 mt-1">When the agent should commit its work.</p>
            </div>
            <div>
              <SelectInput
                label="Number of Phases"
                value={phaseCount}
                onChange={setPhaseCount}
                options={PHASE_COUNT_OPTIONS}
              />
              <p className="text-xs text-zinc-600 mt-1">Auto calculates from token budget. Override if needed.</p>
            </div>
          </div>

          {/* Parallel phases toggle */}
          <div className="mt-4 pt-3 border-t border-zinc-800 space-y-2">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={parallelMode}
                onChange={(e) => setParallelMode(e.target.checked)}
                className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-orange-500"
              />
              <span className="text-sm text-zinc-300">Parallel phases (run independent phases simultaneously)</span>
            </label>
            {parallelMode && (
              <div className="ml-6 bg-amber-900/20 border border-amber-700/40 rounded-lg px-3 py-2 text-xs text-amber-300">
                ⚠️ Parallel mode uses tokens ~2x faster per wall-clock hour. Each phase needs its own log file.
                Phases in the same wave from the AI's output will run concurrently.
              </div>
            )}
            <p className="text-xs text-zinc-600">
              Phases with no cross-dependencies run simultaneously. Requires the AI to output wave groups in the phase split.
            </p>
          </div>
        </SectionCard>

        {/* Section: Agent Roles */}
        <SectionCard
          icon={<Users size={18} className="text-orange-400" />}
          title="Agent Roles"
        >
          <p className="text-sm text-zinc-500 mb-4">
            Each build uses specialized agents. Toggle roles on/off and customize their prompts.
            Pipeline: Architect &rarr; Coder (per phase) &rarr; Reviewer (per phase) &rarr; Verifier &rarr; Cartographer.
          </p>

          <div className="space-y-2">
            {agentRoles.map((role) => (
              <div key={role.id} className="border border-zinc-800 rounded-lg overflow-hidden">
                {/* Header row */}
                <div
                  className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-zinc-800/30 transition-colors"
                  onClick={() => setExpandedRole(expandedRole === role.id ? null : role.id)}
                >
                  <input
                    type="checkbox"
                    checked={role.enabled}
                    onChange={(e) => {
                      e.stopPropagation()
                      updateRole(role.id, { enabled: e.target.checked })
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-orange-500"
                  />
                  {ROLE_ICONS[role.id] || <Cpu size={16} className="text-zinc-400" />}
                  <span className="font-medium text-white text-sm flex-1">{role.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    role.model === 'opus' ? 'bg-purple-900/50 text-purple-300' :
                    role.model === 'sonnet' ? 'bg-cyan-900/50 text-cyan-300' :
                    'bg-zinc-800 text-zinc-400'
                  }`}>
                    {role.model}
                  </span>
                  <span className="text-xs text-zinc-600">
                    {role.runsWhen === 'once_before' ? 'Before build' :
                     role.runsWhen === 'per_phase' ? 'Each phase' :
                     role.runsWhen === 'per_phase_after' ? 'After each phase' :
                     role.runsWhen === 'once_after' ? 'After all phases' :
                     'Final step'}
                  </span>
                  {expandedRole === role.id ? <ChevronUp size={14} className="text-zinc-500" /> : <ChevronDown size={14} className="text-zinc-500" />}
                </div>

                {/* Expanded content */}
                {expandedRole === role.id && (
                  <div className="px-4 pb-4 pt-2 border-t border-zinc-800 space-y-3">
                    <p className="text-xs text-zinc-500">{role.description}</p>
                    <div className="flex gap-3">
                      <div className="w-32">
                        <label className="block text-xs text-zinc-500 mb-1">Model</label>
                        <select
                          value={role.model}
                          onChange={(e) => updateRole(role.id, { model: e.target.value })}
                          className="w-full appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-2 py-1.5 text-white text-sm focus:border-orange-500 focus:outline-none"
                        >
                          {ROLE_MODEL_OPTIONS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <PromptBar
                      label="Prompt Template"
                      value={role.prompt}
                      defaultValue={DEFAULT_AGENT_ROLES.find(r => r.id === role.id)?.prompt || ''}
                      onChange={(v) => updateRole(role.id, { prompt: v })}
                    />
                    {role.id === 'verifier' && (
                      <p className="text-xs text-zinc-600">
                        Reads from .claude/templates/e2e_verification_prompt.template.md if it exists.
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Verification toggle */}
          <div className="flex items-center gap-2 mt-4 pt-3 border-t border-zinc-800">
            <input
              type="checkbox"
              checked={includeVerification}
              onChange={(e) => setIncludeVerification(e.target.checked)}
              className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-orange-500"
            />
            <span className="text-sm text-zinc-300">Include post-build verification phase (Opus)</span>
            <span className="text-xs text-zinc-600">&mdash; runs full test protocol after all phases</span>
          </div>
        </SectionCard>

        {/* Section 5: Phase Assignments (read-only — populated by AI phase split) */}
        <SectionCard
          icon={<Layers size={18} className="text-indigo-400" />}
          title="Phase Assignments"
        >
          {phaseAssignments ? (
            <div className="space-y-3">
              <div className="bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 max-h-96 overflow-y-auto">
                <pre className="text-sm text-zinc-300 whitespace-pre-wrap font-mono text-xs leading-relaxed">
                  {phaseAssignments}
                </pre>
              </div>
              <button
                onClick={() => {
                  setPhaseAssignments('')
                  setPhaseAiResult('')
                  generatePhaseSplit()
                }}
                disabled={phaseAiLoading}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-orange-400 transition-colors px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-orange-500/50 disabled:opacity-50"
              >
                {phaseAiLoading ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <RefreshCw size={12} />
                )}
                Regenerate Split
              </button>
            </div>
          ) : (
            <div className="bg-zinc-950/50 border border-dashed border-zinc-700 rounded-lg px-4 py-8 text-center">
              <p className="text-sm text-zinc-500">
                Phase assignments will appear here after generating the phase split.
              </p>
              <p className="text-xs text-zinc-600 mt-1">
                Click "Generate Phase-Split Prompt" or "Generate All" to populate.
              </p>
            </div>
          )}
        </SectionCard>

        {/* Section: Build Estimate */}
        <SectionCard
          icon={<Zap size={18} className="text-orange-400" />}
          title="Build Estimate"
        >
          {(() => {
            const numPhases = phaseCount === 'Auto' ? Math.max(2, Math.ceil(features.filter(f => f.name.trim()).length / 4) || 3) : parseInt(phaseCount) || 3
            const p1Cab = getPhase1CabRide()
            const p2Cab = getPhase2PlusCabRide()
            const enabledRoles = agentRoles.filter(r => r.enabled)
            const perPhaseRoles = enabledRoles.filter(r => r.runsWhen === 'per_phase' || r.runsWhen === 'per_phase_after')
            const oneTimeRoles = enabledRoles.filter(r => r.runsWhen === 'once_before' || r.runsWhen === 'once_after' || r.runsWhen === 'once_final')

            // Estimate tokens per role run (rough: prompt tokens + expected output)
            const roleEstimate = (role: typeof agentRoles[0]) => {
              const promptTokens = estimateTokens(role.prompt)
              // Opus roles tend to use more output, sonnet less
              const outputMultiplier = role.model === 'opus' ? 3 : 2
              return promptTokens * outputMultiplier
            }

            const phase1Total = p1Cab + perPhaseRoles.reduce((sum, r) => sum + roleEstimate(r), 0)
            const phase2Total = p2Cab + perPhaseRoles.reduce((sum, r) => sum + roleEstimate(r), 0)
            const oneTimeTotal = oneTimeRoles.reduce((sum, r) => sum + roleEstimate(r), 0)
            const grandTotal = phase1Total + (phase2Total * (numPhases - 1)) + oneTimeTotal

            // Verification phase estimate
            const verifier = agentRoles.find(r => r.id === 'verifier')
            const verifyEstimate = verifier?.enabled ? roleEstimate(verifier) * (numPhases > 4 ? 2 : 1) : 0

            // Suppress unused variable lint warning — verifyEstimate is used in the warnings below
            void verifyEstimate

            return (
              <div className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-zinc-900/60 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-orange-400">{numPhases}</p>
                    <p className="text-xs text-zinc-500">Phases</p>
                  </div>
                  <div className="bg-zinc-900/60 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-cyan-400">{enabledRoles.length}</p>
                    <p className="text-xs text-zinc-500">Active Roles</p>
                  </div>
                  <div className="bg-zinc-900/60 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-amber-400">{Math.round(grandTotal / 1000)}K</p>
                    <p className="text-xs text-zinc-500">Est. Total Tokens</p>
                  </div>
                  <div className="bg-zinc-900/60 rounded-lg p-3 text-center">
                    <p className="text-2xl font-bold text-green-400">{numPhases + oneTimeRoles.length}</p>
                    <p className="text-xs text-zinc-500">CLI Sessions</p>
                  </div>
                </div>

                {/* Pipeline card visualization */}
                <div className="bg-zinc-900/40 rounded-lg p-3 space-y-2">
                  {(() => {
                    const waves = parsedWaves()
                    const hasWaves = waves.length > 0 && waves.some(w => w.length > 1)
                    return hasWaves ? (
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-zinc-400 font-medium">Pipeline</p>
                        <span className="text-xs text-cyan-400 bg-cyan-900/30 border border-cyan-700/40 rounded px-1.5 py-0.5">
                          {waves.length} waves • parallel
                        </span>
                      </div>
                    ) : <p className="text-xs text-zinc-400 font-medium">Pipeline</p>
                  })()}
                  <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto pb-1">
                    {/* Pre-build roles */}
                    {oneTimeRoles.filter(r => r.runsWhen === 'once_before').map((r, idx) => (
                      <div key={r.id} className="flex items-center gap-1.5 shrink-0">
                        {idx > 0 && <span className="text-orange-500 text-xs">→</span>}
                        <div className="bg-zinc-900/60 border border-purple-700/50 rounded-lg p-2 min-w-[100px] text-center">
                          <p className="text-xs font-medium text-purple-300 truncate">{r.name}</p>
                          <p className="text-orange-400 text-xs font-bold mt-0.5">~{Math.round(roleEstimate(r) / 1000)}K ⚡</p>
                          <p className="text-zinc-600 text-[10px]">{r.model}</p>
                        </div>
                      </div>
                    ))}

                    {/* Arrow from pre-build to phases */}
                    {oneTimeRoles.filter(r => r.runsWhen === 'once_before').length > 0 && (
                      <span className="text-orange-500 text-xs shrink-0">→</span>
                    )}

                    {/* Phase 1 */}
                    <div className="bg-zinc-900/60 border border-orange-700/50 rounded-lg p-2 min-w-[100px] text-center shrink-0">
                      <p className="text-xs font-medium text-orange-300">Phase 1</p>
                      <p className="text-orange-400 text-xs font-bold mt-0.5">~{Math.round(phase1Total / 1000)}K ⚡</p>
                      <p className="text-zinc-600 text-[10px]">sonnet</p>
                    </div>

                    {/* Phase 2+ */}
                    {numPhases > 1 && Array.from({ length: Math.min(numPhases - 1, 4) }, (_, i) => i + 2).map(phaseNum => (
                      <div key={phaseNum} className="flex items-center gap-1.5 shrink-0">
                        <span className="text-orange-500 text-xs">→</span>
                        <div className="bg-zinc-900/60 border border-cyan-700/50 rounded-lg p-2 min-w-[100px] text-center">
                          <p className="text-xs font-medium text-cyan-300">Phase {phaseNum}</p>
                          <p className="text-orange-400 text-xs font-bold mt-0.5">~{Math.round(phase2Total / 1000)}K ⚡</p>
                          <p className="text-zinc-600 text-[10px]">sonnet</p>
                        </div>
                      </div>
                    ))}

                    {/* Ellipsis if more phases */}
                    {numPhases > 5 && (
                      <>
                        <span className="text-orange-500 text-xs shrink-0">→</span>
                        <div className="bg-zinc-900/40 border border-zinc-700/40 rounded-lg p-2 min-w-[60px] text-center shrink-0">
                          <p className="text-xs text-zinc-500">+{numPhases - 5} more</p>
                        </div>
                      </>
                    )}

                    {/* Post-build roles */}
                    {oneTimeRoles.filter(r => r.runsWhen === 'once_after' || r.runsWhen === 'once_final').map(r => (
                      <div key={r.id} className="flex items-center gap-1.5 shrink-0">
                        <span className="text-orange-500 text-xs">→</span>
                        <div className={`bg-zinc-900/60 rounded-lg p-2 min-w-[100px] text-center ${
                          r.runsWhen === 'once_after' ? 'border border-red-700/50' : 'border border-green-700/50'
                        }`}>
                          <p className={`text-xs font-medium truncate ${r.runsWhen === 'once_after' ? 'text-red-300' : 'text-green-300'}`}>
                            {r.name}
                          </p>
                          <p className="text-orange-400 text-xs font-bold mt-0.5">~{Math.round(roleEstimate(r) / 1000)}K ⚡</p>
                          <p className="text-zinc-600 text-[10px]">{r.model}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-zinc-600">
                    Total: ~{Math.round(grandTotal / 1000)}K tokens • {numPhases + oneTimeRoles.length} CLI sessions
                    {grandTotal > 0 && ` • Est. ~${(grandTotal / 200000).toFixed(1)} hrs`}
                    {parallelMode && parsedWaves().some(w => w.length > 1) && (
                      <span className="text-cyan-500"> • parallel waves active</span>
                    )}
                  </p>
                </div>

                {/* Warnings */}
                {grandTotal > 500000 && (
                  <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg px-3 py-2 text-xs text-amber-300">
                    Large build ({Math.round(grandTotal / 1000)}K tokens). Consider breaking into smaller builds or running overnight.
                  </div>
                )}
                {numPhases > 4 && verifier?.enabled && (
                  <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg px-3 py-2 text-xs text-zinc-400">
                    Verification will use {numPhases > 4 ? '2 sessions' : '1 session'} for {numPhases}-phase build.
                  </div>
                )}
              </div>
            )
          })()}
        </SectionCard>

        {/* Section: Generate */}
        <SectionCard
          icon={<Rocket size={18} className="text-orange-400" />}
          title="Generate"
        >
          {/* Project Directory for script output */}
          <div className="mb-5">
            <TextInput
              label="Project Directory (for saving scripts)"
              value={projectDir}
              onChange={setProjectDir}
              placeholder="C:/Projects/my-app"
            />
            {/* File browser below directory input */}
            <ProjectFileBrowser projectDir={projectDir} />
          </div>

          {/* Generate All button */}
          <button
            onClick={() => setGateOpen(true)}
            disabled={generateAllLoading}
            className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 rounded-xl px-6 py-4 text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 mb-4 shadow-lg shadow-orange-500/20"
          >
            {generateAllLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Step {generateAllStep} of 2: {generateAllStep === 1 ? 'Generating PRD...' : 'Splitting phases...'}
              </>
            ) : (
              <>
                <Rocket size={20} />
                Generate All (PRD &rarr; Phases)
              </>
            )}
          </button>

          {generateAllError && (
            <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2 mb-4">
              {generateAllError}
            </div>
          )}

          <p className="text-xs text-zinc-600 text-center mb-4">&mdash; or generate individually &mdash;</p>

          {/* Original 3 buttons */}
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

          {/* Prompt override bars for generation prompts */}
          {(prdPrompt || phasePrompt || buildPrompt) && (
            <div className="mt-3 pt-3 border-t border-zinc-800 space-y-2">
              <p className="text-xs text-zinc-600 mb-2">Override generated prompts before running with AI:</p>
              {prdPrompt && (
                <PromptBar
                  label="PRD Generation Prompt"
                  value={prdPrompt}
                  defaultValue={prdPrompt}
                  onChange={setPrdPrompt}
                />
              )}
              {phasePrompt && (
                <PromptBar
                  label="Phase-Split Prompt"
                  value={phasePrompt}
                  defaultValue={phasePrompt}
                  onChange={setPhasePrompt}
                />
              )}
              {buildPrompt && (
                <PromptBar
                  label="Build Scripts Prompt"
                  value={buildPrompt}
                  defaultValue={buildPrompt}
                  onChange={setBuildPrompt}
                />
              )}
            </div>
          )}

          {/* Write Scripts to Disk */}
          {(buildAiResult || prdAiResult) && projectDir && (
            <div className="mt-4 border-t border-zinc-800 pt-4">
              <button
                onClick={handleWriteScripts}
                disabled={writingScripts}
                className="flex items-center gap-2 bg-green-600/20 border border-green-700/40 rounded-lg px-4 py-2.5 text-green-300 hover:border-green-500/60 hover:bg-green-600/30 transition-all disabled:opacity-50"
              >
                {writingScripts ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
                {writingScripts ? 'Writing scripts...' : 'Save Scripts to Disk'}
              </button>
              {writeError && (
                <p className="text-xs text-red-400 mt-2">{writeError}</p>
              )}
              {scriptsWritten && (
                <div className="mt-2 text-xs text-green-400">
                  <p className="font-medium mb-1">Scripts written ({scriptsWritten.length} files):</p>
                  <ul className="space-y-0.5 text-zinc-400">
                    {scriptsWritten.map(f => (
                      <li key={f} className="flex items-center gap-1">
                        <Check size={10} className="text-green-500" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Start Build + Copy Commands */}
          {scriptsWritten && scriptsWritten.length > 0 && (
            <div className="mt-4 border-t border-zinc-700/50 pt-4 space-y-3">
              <p className="text-sm text-orange-400 font-medium">Ready to Build</p>

              {/* Start build button */}
              <button
                onClick={() => {
                  const cmd = `cd "${projectDir}" && bash scripts/cli-scripter/run_all.sh`
                  copyToClipboard(cmd)
                }}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-amber-500 rounded-lg px-4 py-3 text-white font-semibold hover:opacity-90 transition-opacity"
              >
                <Copy size={16} />
                Copy Start Command
              </button>
              <p className="text-xs text-zinc-600 text-center">Copies the run_all.sh command -- paste into your terminal to start the build.</p>

              {/* Individual phase commands */}
              <div className="space-y-1">
                {scriptsWritten.filter(f => f.includes('.sh')).map(f => {
                  const cmd = `cd "${projectDir}" && bash "${f}"`
                  return (
                    <div key={f} className="flex items-center gap-2 bg-zinc-900/50 rounded-lg px-3 py-2">
                      <Terminal size={12} className="text-zinc-500 shrink-0" />
                      <code className="text-xs text-zinc-400 flex-1 truncate">{f}</code>
                      <button
                        onClick={() => copyToClipboard(cmd)}
                        className="text-xs text-orange-400 hover:text-orange-300 shrink-0"
                      >
                        <Copy size={12} />
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </SectionCard>

        {/* Build Library — save/load configs */}
        <BuildLibrary
          open={libraryOpen}
          onToggle={() => setLibraryOpen(!libraryOpen)}
          onLoad={handleLibraryLoad}
          onSaveRequest={handleLibrarySaveRequest}
        />

        {/* Section: Build Queue */}
        <SectionCard
          icon={<ListOrdered size={18} className="text-amber-400" />}
          title="Build Queue"
        >
          <p className="text-sm text-zinc-500 mb-4">
            Queue up multiple apps. When one finishes, the next starts automatically.
          </p>

          {/* Add current app to queue */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={addToQueue}
              disabled={!appName.trim() || !projectDir.trim()}
              className="flex items-center gap-2 bg-amber-600/20 border border-amber-700/40 rounded-lg px-4 py-2 text-amber-300 hover:border-amber-500/60 hover:bg-amber-600/30 transition-all disabled:opacity-30 text-sm"
            >
              <Plus size={14} />
              Add Current App to Queue
            </button>
            {queueItems.length > 0 && (
              <button
                onClick={() => setQueueItems([])}
                className="flex items-center gap-2 text-zinc-500 hover:text-red-400 text-xs transition-colors"
              >
                <X size={12} />
                Clear Queue
              </button>
            )}
          </div>

          {/* Queue list */}
          {queueItems.length === 0 ? (
            <div className="text-center py-6 text-zinc-600 text-sm">
              No apps queued. Fill out the form above and click "Add Current App to Queue."
            </div>
          ) : (
            <div className="space-y-2">
              {queueItems.map((item, i) => (
                <div key={i} className="flex items-center gap-2 bg-zinc-900/50 border border-zinc-800 rounded-lg px-3 py-2.5">
                  {/* Position + reorder */}
                  <div className="flex flex-col items-center gap-0.5 shrink-0">
                    <button
                      onClick={() => moveQueueItem(i, 'up')}
                      disabled={i === 0}
                      className="text-zinc-600 hover:text-zinc-300 transition-colors disabled:opacity-20"
                      title="Move up"
                    >
                      <ChevronUp size={13} />
                    </button>
                    <span className="text-xs text-zinc-600 leading-none">{i + 1}</span>
                    <button
                      onClick={() => moveQueueItem(i, 'down')}
                      disabled={i === queueItems.length - 1}
                      className="text-zinc-600 hover:text-zinc-300 transition-colors disabled:opacity-20"
                      title="Move down"
                    >
                      <ChevronDown size={13} />
                    </button>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-medium truncate">{item.name}</p>
                    <p className="text-xs text-zinc-500 truncate">{item.project_dir}</p>
                  </div>

                  {/* Status badge */}
                  <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
                    item.status === 'pending' ? 'bg-zinc-800 text-zinc-400' :
                    item.status === 'running' ? 'bg-cyan-900/50 text-cyan-300 animate-pulse' :
                    item.status === 'completed' ? 'bg-green-900/50 text-green-300' :
                    'bg-red-900/50 text-red-300'
                  }`}>
                    {item.status}
                  </span>

                  <button
                    onClick={() => removeFromQueue(i)}
                    className="text-zinc-600 hover:text-red-400 transition-colors shrink-0"
                    title="Remove from queue"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}

              {/* Total estimate */}
              {queueItems.length > 1 && (() => {
                const numPhases = phaseCount === 'Auto' ? Math.max(2, Math.ceil(features.filter(f => f.name.trim()).length / 4) || 3) : parseInt(phaseCount) || 3
                const enabledRoles = agentRoles.filter(r => r.enabled)
                const perPhaseCount = enabledRoles.filter(r => r.runsWhen === 'per_phase' || r.runsWhen === 'per_phase_after').length
                const approxPerBuild = (numPhases * perPhaseCount + 2) * 60000 // rough token estimate
                const totalTokens = Math.round(approxPerBuild * queueItems.filter(q => q.status === 'pending').length / 1000)
                return (
                  <div className="text-xs text-zinc-500 border-t border-zinc-800 pt-2 mt-1">
                    {queueItems.filter(q => q.status === 'pending').length} pending builds •{' '}
                    est. ~{totalTokens}K tokens total
                  </div>
                )
              })()}
            </div>
          )}
        </SectionCard>

        {/* Footer spacing */}
        <div className="h-12" />
      </main>

      {/* Gate Popup — intercepts Generate All */}
      <GatePopup
        open={gateOpen}
        onConfirm={handleGateConfirm}
        onCancel={() => setGateOpen(false)}
        mainTokens={estimateTokens(getMergedText(ruleBlocks, 'main') || getRulesText())}
        p1Tokens={estimateTokens(getMergedText(ruleBlocks, 'p1') || phase1Rules || getRulesText())}
        p2PlusTokens={estimateTokens(getMergedText(ruleBlocks, 'p2plus') || phase2PlusRules || getRulesText())}
        lastBuildMode={buildMode}
        lastPhaseMode={phaseMode}
      />
    </div>
  )
}
