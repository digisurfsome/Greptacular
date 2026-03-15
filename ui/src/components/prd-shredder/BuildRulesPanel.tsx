import { useState, useMemo } from 'react'
import {
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Pencil,
  Trash2,
  Shield,
  Wrench,
  Palette,
  TestTube,
  Building2,
  Code2,
  GitBranch,
  KeyRound,
  Loader2,
  Check,
} from 'lucide-react'
import type { BuildRule, BuildRuleCategory } from '@/lib/api'
import {
  useBuildRules,
  useCreateRule,
  useUpdateRule,
  useDeleteRule,
  useToggleRule,
  useShredderConfig,
  useUpdateShredderConfig,
} from '@/hooks/usePRDShredder'

// ---------------------------------------------------------------------------
// Category metadata — icon, color, label
// ---------------------------------------------------------------------------
const CATEGORY_META: Record<
  BuildRuleCategory,
  { label: string; color: string; dot: string; bg: string; border: string; icon: React.ReactNode }
> = {
  architecture:   { label: 'Architecture',  color: 'text-cyan-400',    dot: 'bg-cyan-500',    bg: 'bg-cyan-500/15',    border: 'border-cyan-500/30',    icon: <Building2 size={12} /> },
  'code-quality': { label: 'Code Quality',  color: 'text-emerald-400', dot: 'bg-emerald-500', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', icon: <Code2 size={12} /> },
  testing:        { label: 'Testing',       color: 'text-yellow-400',  dot: 'bg-yellow-500',  bg: 'bg-yellow-500/15',  border: 'border-yellow-500/30',  icon: <TestTube size={12} /> },
  security:       { label: 'Security',      color: 'text-red-400',     dot: 'bg-red-500',     bg: 'bg-red-500/15',     border: 'border-red-500/30',     icon: <Shield size={12} /> },
  style:          { label: 'Style',         color: 'text-violet-400',  dot: 'bg-violet-500',  bg: 'bg-violet-500/15',  border: 'border-violet-500/30',  icon: <Palette size={12} /> },
  custom:         { label: 'Custom',        color: 'text-amber-400',   dot: 'bg-amber-500',   bg: 'bg-amber-500/15',   border: 'border-amber-500/30',   icon: <Wrench size={12} /> },
}

const ALL_CATEGORIES: BuildRuleCategory[] = ['architecture', 'code-quality', 'testing', 'security', 'style', 'custom']

// ---------------------------------------------------------------------------
// Category badge — small colored pill
// ---------------------------------------------------------------------------
function CategoryBadge({ category }: { category: BuildRuleCategory }) {
  const meta = CATEGORY_META[category]
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold border ${meta.bg} ${meta.color} ${meta.border}`}>
      {meta.icon}
      {meta.label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Toggle switch — colored by category
// ---------------------------------------------------------------------------
function ToggleSwitch({ enabled, color, onToggle, disabled }: {
  enabled: boolean
  color: string
  onToggle: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      disabled={disabled}
      onClick={onToggle}
      className={`
        relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 transition-colors duration-200
        ${enabled ? `${color} border-transparent` : 'bg-zinc-700 border-zinc-600'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform duration-200
          ${enabled ? 'translate-x-4' : 'translate-x-0.5'}
        `}
      />
    </button>
  )
}

// ---------------------------------------------------------------------------
// Rule row — single rule display with actions
// ---------------------------------------------------------------------------
function RuleRow({ rule, onEdit, onDelete, onToggle }: {
  rule: BuildRule
  onEdit: (rule: BuildRule) => void
  onDelete: (id: string) => void
  onToggle: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const meta = CATEGORY_META[rule.category]
  const toggleRule = useToggleRule()
  const deleteRule = useDeleteRule()

  return (
    <div className={`
      bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-700/40 rounded-lg
      hover:border-zinc-300 dark:hover:border-zinc-600/60 transition-colors group
      ${!rule.enabled ? 'opacity-60' : ''}
    `}>
      <div className="flex items-center gap-3 px-3 py-2.5">
        {/* Toggle */}
        <ToggleSwitch
          enabled={rule.enabled}
          color={meta.dot}
          onToggle={() => onToggle(rule.id)}
          disabled={toggleRule.isPending}
        />

        {/* Name + truncated text */}
        <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpanded(v => !v)}>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-zinc-900 dark:text-white truncate">{rule.name}</span>
            <CategoryBadge category={rule.category} />
          </div>
          {!expanded && (
            <p className="text-[11px] text-zinc-500 dark:text-zinc-500 truncate mt-0.5">{rule.text}</p>
          )}
        </div>

        {/* Expand indicator */}
        <button
          className="h-6 w-6 flex items-center justify-center rounded text-zinc-500 hover:text-zinc-300 transition-colors"
          onClick={() => setExpanded(v => !v)}
          title={expanded ? 'Collapse' : 'Expand'}
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>

        {/* Actions — visible on hover */}
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            className="h-6 w-6 flex items-center justify-center rounded text-zinc-500 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors"
            onClick={() => onEdit(rule)}
            title="Edit rule"
          >
            <Pencil size={11} />
          </button>
          <button
            className="h-6 w-6 flex items-center justify-center rounded text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            onClick={() => onDelete(rule.id)}
            disabled={deleteRule.isPending}
            title="Delete rule"
          >
            <Trash2 size={11} />
          </button>
        </div>
      </div>

      {/* Expanded text */}
      {expanded && (
        <div className="px-3 pb-3 border-t border-zinc-200 dark:border-zinc-800/60 mt-1 pt-2">
          <p className="text-[11px] text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap leading-relaxed">{rule.text}</p>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Add/Edit form — inline form for rule creation/editing
// ---------------------------------------------------------------------------
function RuleForm({ editingRule, onSave, onCancel }: {
  editingRule: BuildRule | null
  onSave: (data: { name: string; text: string; category: BuildRuleCategory }) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(editingRule?.name || '')
  const [text, setText] = useState(editingRule?.text || '')
  const [category, setCategory] = useState<BuildRuleCategory>(editingRule?.category || 'custom')

  const isValid = name.trim().length > 0 && text.trim().length > 0

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid) return
    onSave({ name: name.trim(), text: text.trim(), category })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-zinc-50 dark:bg-zinc-900/60 border border-emerald-500/30 rounded-lg p-4 space-y-3 animate-slide-in-down"
    >
      <div className="flex items-center justify-between mb-1">
        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
          {editingRule ? 'Edit Rule' : 'New Rule'}
        </h4>
        <button type="button" onClick={onCancel} className="text-zinc-500 hover:text-zinc-300 transition-colors">
          <X size={14} />
        </button>
      </div>

      {/* Name */}
      <input
        type="text"
        placeholder="Rule name (e.g. Use TypeScript strict mode)"
        value={name}
        onChange={e => setName(e.target.value)}
        className="w-full bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-600/50 rounded-lg px-3 py-2 text-sm text-zinc-900 dark:text-zinc-200 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 focus:outline-none transition-colors"
        autoFocus
      />

      {/* Text */}
      <textarea
        placeholder="Rule content — this exact text gets injected into every PRD build prompt..."
        value={text}
        onChange={e => setText(e.target.value)}
        rows={4}
        className="w-full bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-600/50 rounded-lg px-3 py-2 text-xs font-mono text-zinc-700 dark:text-zinc-300 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 resize-y focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 focus:outline-none transition-colors"
      />

      {/* Category select */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">Category:</span>
        {ALL_CATEGORIES.map(cat => {
          const meta = CATEGORY_META[cat]
          const isSelected = category === cat
          return (
            <button
              key={cat}
              type="button"
              onClick={() => setCategory(cat)}
              className={`
                inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-semibold border transition-all
                ${isSelected
                  ? `${meta.bg} ${meta.color} ${meta.border} ring-1 ring-offset-0`
                  : 'bg-zinc-200/60 dark:bg-zinc-800/60 text-zinc-500 dark:text-zinc-500 border-zinc-300/50 dark:border-zinc-700/40 hover:border-zinc-400 dark:hover:border-zinc-600'
                }
              `}
            >
              {meta.icon}
              {meta.label}
            </button>
          )
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 justify-end pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="text-xs font-medium text-zinc-500 hover:text-zinc-300 px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 hover:border-zinc-500 dark:hover:border-zinc-500 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!isValid}
          className="flex items-center gap-1.5 text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg px-4 py-1.5 hover:opacity-90 transition-opacity disabled:opacity-40 shadow-lg shadow-emerald-500/20"
        >
          <Check size={12} />
          {editingRule ? 'Save Changes' : 'Add Rule'}
        </button>
      </div>
    </form>
  )
}

// ---------------------------------------------------------------------------
// GitHub config section
// ---------------------------------------------------------------------------
function GitHubConfigSection() {
  const { data: config, isLoading } = useShredderConfig()
  const updateConfig = useUpdateShredderConfig()

  const [tokenInput, setTokenInput] = useState('')
  const [branchInput, setBranchInput] = useState('')
  const [editing, setEditing] = useState(false)

  // Sync branch from server when data arrives
  const serverBranch = config?.default_branch || 'main'

  function handleSaveToken() {
    if (!tokenInput.trim()) return
    updateConfig.mutate(
      { github_token: tokenInput.trim() },
      { onSuccess: () => { setTokenInput(''); setEditing(false) } },
    )
  }

  function handleSaveBranch() {
    const branch = branchInput.trim() || serverBranch
    updateConfig.mutate({ default_branch: branch })
  }

  const hasToken = !!config?.github_token_masked

  return (
    <div className="border-t border-zinc-200 dark:border-zinc-700/40 pt-4 mt-4 space-y-3">
      <div className="flex items-center gap-2">
        <GitBranch size={14} className="text-zinc-400" />
        <h3 className="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">GitHub Access</h3>
        <span className={`w-2 h-2 rounded-full ${hasToken ? 'bg-emerald-400 shadow-lg shadow-emerald-400/30' : 'bg-amber-400 shadow-lg shadow-amber-400/30'}`} />
        <span className="text-[10px] text-zinc-500">{hasToken ? 'Token set' : 'No token'}</span>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Loader2 size={12} className="animate-spin" />
          Loading config...
        </div>
      ) : (
        <>
          {/* Token */}
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <KeyRound size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
              {editing ? (
                <input
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxx"
                  value={tokenInput}
                  onChange={e => setTokenInput(e.target.value)}
                  className="w-full bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-600/50 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-700 dark:text-zinc-300 placeholder:text-zinc-500 focus:border-cyan-500/50 focus:outline-none transition-colors"
                  autoFocus
                />
              ) : (
                <div
                  className="w-full bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-600/50 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-500 dark:text-zinc-500 cursor-pointer hover:border-zinc-400 dark:hover:border-zinc-500 transition-colors"
                  onClick={() => setEditing(true)}
                >
                  {config?.github_token_masked || 'Click to set token'}
                </div>
              )}
            </div>
            {editing ? (
              <div className="flex gap-1">
                <button
                  onClick={handleSaveToken}
                  disabled={!tokenInput.trim() || updateConfig.isPending}
                  className="flex items-center gap-1 text-[10px] font-semibold bg-emerald-500 text-white rounded px-2 py-1.5 hover:bg-emerald-600 disabled:opacity-40 transition-colors"
                >
                  {updateConfig.isPending ? <Loader2 size={10} className="animate-spin" /> : <Check size={10} />}
                  Save
                </button>
                <button
                  onClick={() => { setEditing(false); setTokenInput('') }}
                  className="text-[10px] text-zinc-500 hover:text-zinc-300 px-2 py-1.5 rounded border border-zinc-600/50 hover:border-zinc-500 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : null}
          </div>

          {/* Default branch */}
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <GitBranch size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                type="text"
                placeholder="Default branch (main)"
                defaultValue={serverBranch}
                onChange={e => setBranchInput(e.target.value)}
                onBlur={handleSaveBranch}
                className="w-full bg-white dark:bg-zinc-900/60 border border-zinc-300 dark:border-zinc-600/50 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-700 dark:text-zinc-300 placeholder:text-zinc-500 focus:border-cyan-500/50 focus:outline-none transition-colors"
              />
            </div>
            <span className="text-[10px] text-zinc-600 shrink-0">default branch</span>
          </div>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------
export function BuildRulesPanel({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [activeCategory, setActiveCategory] = useState<BuildRuleCategory | undefined>(undefined)
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState<BuildRule | null>(null)

  const { data: rulesData, isLoading } = useBuildRules()
  const createRule = useCreateRule()
  const updateRule = useUpdateRule()
  const deleteRuleMutation = useDeleteRule()
  const toggleRuleMutation = useToggleRule()

  // Stabilize the rules array reference to avoid re-render loops in downstream useMemo
  const allRules = useMemo(() => rulesData?.rules ?? [], [rulesData])

  // Filter by active category tab
  const filteredRules = useMemo(() => {
    if (!activeCategory) return allRules
    return allRules.filter(r => r.category === activeCategory)
  }, [allRules, activeCategory])

  // Category counts for tab badges
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const cat of ALL_CATEGORIES) {
      counts[cat] = allRules.filter(r => r.category === cat).length
    }
    return counts
  }, [allRules])

  // Active rule count and unique categories for footer
  const activeCount = allRules.filter(r => r.enabled).length
  const activeCategories = new Set(allRules.filter(r => r.enabled).map(r => r.category)).size

  if (!isOpen) return null

  function handleSaveRule(data: { name: string; text: string; category: BuildRuleCategory }) {
    if (editingRule) {
      updateRule.mutate(
        { ruleId: editingRule.id, updates: data },
        { onSuccess: () => { setEditingRule(null); setShowForm(false) } },
      )
    } else {
      createRule.mutate(
        { ...data, enabled: true },
        { onSuccess: () => setShowForm(false) },
      )
    }
  }

  function handleEdit(rule: BuildRule) {
    setEditingRule(rule)
    setShowForm(true)
  }

  function handleCancelForm() {
    setShowForm(false)
    setEditingRule(null)
  }

  function handleDelete(ruleId: string) {
    deleteRuleMutation.mutate(ruleId)
  }

  function handleToggle(ruleId: string) {
    toggleRuleMutation.mutate(ruleId)
  }

  return (
    <div className="animate-slide-in-down bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/60 rounded-xl overflow-hidden shadow-xl shadow-black/10">
      {/* Gradient left border accent — emerald to cyan */}
      <div className="h-1 bg-gradient-to-r from-emerald-500 via-cyan-400 to-teal-500" />

      <div className="p-5 space-y-4">
        {/* ---- Header ---- */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Shield size={14} className="text-white" />
            </div>
            <h2 className="text-sm font-bold text-zinc-900 dark:text-white uppercase tracking-wider">Build Rules</h2>
            {allRules.length > 0 && (
              <span className="text-[10px] font-bold text-zinc-500 bg-zinc-200 dark:bg-zinc-700/50 rounded px-1.5 py-0.5">
                {allRules.length}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {!showForm && (
              <button
                onClick={() => { setEditingRule(null); setShowForm(true) }}
                className="flex items-center gap-1.5 text-[11px] font-semibold bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg px-3 py-1.5 hover:opacity-90 transition-opacity shadow-md shadow-emerald-500/20"
              >
                <Plus size={12} />
                Add Rule
              </button>
            )}
            <button
              onClick={onClose}
              className="h-7 w-7 rounded flex items-center justify-center text-zinc-500 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
              title="Close panel"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* ---- Category tabs ---- */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* "All" tab */}
          <button
            onClick={() => setActiveCategory(undefined)}
            className={`
              inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-semibold border transition-all
              ${activeCategory === undefined
                ? 'bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-white border-zinc-300 dark:border-zinc-600'
                : 'bg-transparent text-zinc-500 border-zinc-300/50 dark:border-zinc-700/40 hover:border-zinc-400 dark:hover:border-zinc-600'
              }
            `}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
            All
            <span className="text-zinc-400 dark:text-zinc-500 ml-0.5">{allRules.length}</span>
          </button>

          {ALL_CATEGORIES.map(cat => {
            const meta = CATEGORY_META[cat]
            const count = categoryCounts[cat] || 0
            const isActive = activeCategory === cat
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(isActive ? undefined : cat)}
                className={`
                  inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-semibold border transition-all
                  ${isActive
                    ? `${meta.bg} ${meta.color} ${meta.border}`
                    : 'bg-transparent text-zinc-500 border-zinc-300/50 dark:border-zinc-700/40 hover:border-zinc-400 dark:hover:border-zinc-600'
                  }
                `}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                {meta.label}
                {count > 0 && <span className="text-zinc-400 dark:text-zinc-500 ml-0.5">{count}</span>}
              </button>
            )
          })}
        </div>

        {/* ---- Add/Edit form ---- */}
        {showForm && (
          <RuleForm
            editingRule={editingRule}
            onSave={handleSaveRule}
            onCancel={handleCancelForm}
          />
        )}

        {/* ---- Rules list ---- */}
        {isLoading ? (
          <div className="flex items-center justify-center gap-2 py-8 text-zinc-500">
            <Loader2 size={14} className="animate-spin" />
            <span className="text-xs">Loading rules...</span>
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-zinc-500">
            <Shield size={20} className="text-zinc-600 dark:text-zinc-700 mb-2" />
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-500">
              {activeCategory ? `No ${CATEGORY_META[activeCategory].label.toLowerCase()} rules` : 'No rules yet'}
            </p>
            <p className="text-[10px] text-zinc-400 dark:text-zinc-600 mt-0.5">
              Add rules that auto-inject into every PRD build
            </p>
          </div>
        ) : (
          <div className="space-y-1.5 max-h-[400px] overflow-y-auto pr-1">
            {filteredRules.map(rule => (
              <RuleRow
                key={rule.id}
                rule={rule}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}

        {/* ---- GitHub config ---- */}
        <GitHubConfigSection />

        {/* ---- Footer summary ---- */}
        {allRules.length > 0 && (
          <div className="border-t border-zinc-200 dark:border-zinc-700/40 pt-3 mt-3">
            <p className="text-[10px] text-zinc-500 dark:text-zinc-600 text-center">
              <span className="font-semibold text-emerald-400">{activeCount} rule{activeCount !== 1 ? 's' : ''}</span>
              {' '}active across{' '}
              <span className="font-semibold text-cyan-400">{activeCategories} categor{activeCategories !== 1 ? 'ies' : 'y'}</span>
              {' '}&mdash; auto-injected into every build
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
