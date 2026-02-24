import { useState, useMemo, useCallback } from 'react'
import {
  ArrowLeft,
  ChevronRight,
  Plus,
  Search,
  PackageOpen,
  Loader2,
  AlertCircle,
  Trash2,
  Edit,
  X,
  FileText,
  Tag,
  RefreshCw,
  Wrench,
  TestTube,
  Rocket,
  Shield,
  Cog,
  Eye,
  Bot,
  FolderOpen,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  useBlueprints,
  useCreateBlueprint,
  useUpdateBlueprint,
  useDeleteBlueprint,
} from '@/hooks/useRoleLibrary'
import type { RoleBlueprint, RoleBlueprintCreate, BlueprintStatus } from '@/lib/types'

// ---------------------------------------------------------------------------
// Category visual config
// ---------------------------------------------------------------------------

interface CategoryMeta {
  label: string
  icon: React.ReactNode
  color: string       // bg for the category header pill
  cardBorder: string  // left-border accent on cards
}

const CATEGORY_META: Record<string, CategoryMeta> = {
  updating: {
    label: 'Updating',
    icon: <RefreshCw size={16} />,
    color: 'bg-blue-500 text-white',
    cardBorder: 'border-l-blue-500',
  },
  building: {
    label: 'Building',
    icon: <Wrench size={16} />,
    color: 'bg-amber-500 text-white',
    cardBorder: 'border-l-amber-500',
  },
  testing: {
    label: 'Testing',
    icon: <TestTube size={16} />,
    color: 'bg-green-500 text-white',
    cardBorder: 'border-l-green-500',
  },
  deploying: {
    label: 'Deploying',
    icon: <Rocket size={16} />,
    color: 'bg-violet-500 text-white',
    cardBorder: 'border-l-violet-500',
  },
  security: {
    label: 'Security',
    icon: <Shield size={16} />,
    color: 'bg-red-500 text-white',
    cardBorder: 'border-l-red-500',
  },
  devops: {
    label: 'DevOps',
    icon: <Cog size={16} />,
    color: 'bg-cyan-500 text-white',
    cardBorder: 'border-l-cyan-500',
  },
  monitoring: {
    label: 'Monitoring',
    icon: <Eye size={16} />,
    color: 'bg-orange-500 text-white',
    cardBorder: 'border-l-orange-500',
  },
  research: {
    label: 'Research',
    icon: <Bot size={16} />,
    color: 'bg-pink-500 text-white',
    cardBorder: 'border-l-pink-500',
  },
}

const DEFAULT_CATEGORY_META: CategoryMeta = {
  label: 'Other',
  icon: <FolderOpen size={16} />,
  color: 'bg-zinc-500 text-white',
  cardBorder: 'border-l-zinc-500',
}

function getCategoryMeta(cat: string): CategoryMeta {
  return CATEGORY_META[cat] ?? { ...DEFAULT_CATEGORY_META, label: cat.charAt(0).toUpperCase() + cat.slice(1) }
}

const STATUS_BADGE: Record<BlueprintStatus, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30' },
  ready: { label: 'Ready', className: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  built: { label: 'Built', className: 'bg-green-500/20 text-green-400 border-green-500/30' },
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function RoleLibraryPage(): React.JSX.Element {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  const { data: blueprints, isLoading, error, refetch } = useBlueprints()
  const deleteMut = useDeleteBlueprint()

  // Filter blueprints by search query
  const filtered = useMemo(() => {
    if (!blueprints) return []
    if (!searchQuery) return blueprints
    const q = searchQuery.toLowerCase()
    return blueprints.filter(
      (b) =>
        b.name.toLowerCase().includes(q) ||
        b.one_liner.toLowerCase().includes(q) ||
        b.role_tag.toLowerCase().includes(q) ||
        b.category.toLowerCase().includes(q) ||
        (b.subcategory && b.subcategory.toLowerCase().includes(q))
    )
  }, [blueprints, searchQuery])

  // Group by category
  const grouped = useMemo(() => {
    const map = new Map<string, RoleBlueprint[]>()
    for (const bp of filtered) {
      const arr = map.get(bp.category) ?? []
      arr.push(bp)
      map.set(bp.category, arr)
    }
    // Sort categories: known ones first in order, then unknowns alphabetically
    const knownOrder = Object.keys(CATEGORY_META)
    const sortedEntries = [...map.entries()].sort(([a], [b]) => {
      const ai = knownOrder.indexOf(a)
      const bi = knownOrder.indexOf(b)
      if (ai >= 0 && bi >= 0) return ai - bi
      if (ai >= 0) return -1
      if (bi >= 0) return 1
      return a.localeCompare(b)
    })
    return sortedEntries
  }, [filtered])

  const selectedBp = useMemo(
    () => blueprints?.find((b) => b.id === selectedId) ?? null,
    [blueprints, selectedId]
  )

  const handleDelete = useCallback(() => {
    if (confirmDeleteId === null) return
    deleteMut.mutate(confirmDeleteId, {
      onSuccess: () => {
        if (selectedId === confirmDeleteId) setSelectedId(null)
        setConfirmDeleteId(null)
      },
    })
  }, [confirmDeleteId, deleteMut, selectedId])

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb bar */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => { window.location.hash = '#/workspace' }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">Workspace</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Role Library</span>
        </nav>
        <div className="ml-auto flex items-center gap-1">
          <Button
            size="sm"
            className="h-7 px-3 gap-1.5"
            onClick={() => { setShowCreateForm(true); setEditingId(null) }}
          >
            <Plus size={14} />
            <span className="text-xs">New Role</span>
          </Button>
        </div>
      </div>

      {/* Main layout: list + detail */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel: category browser */}
        <div className="flex-1 overflow-auto p-6">
          {/* Search bar */}
          <div className="max-w-7xl mx-auto mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search roles by name, tag, category..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground"
              />
            </div>
          </div>

          {/* Content */}
          <div className="max-w-7xl mx-auto">
            {isLoading && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="animate-pulse bg-muted rounded-lg h-28" />
                ))}
              </div>
            )}

            {error && (
              <div className="text-center py-16">
                <AlertCircle className="w-12 h-12 text-destructive mx-auto mb-4" />
                <p className="text-sm text-muted-foreground mb-4">{(error as Error).message}</p>
                <Button variant="outline" onClick={() => refetch()}>Try Again</Button>
              </div>
            )}

            {!isLoading && !error && grouped.length === 0 && !searchQuery && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <PackageOpen className="w-12 h-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-1">No roles yet</h3>
                <p className="text-sm text-muted-foreground mb-4 max-w-md">
                  Start building your agent role library. Each role is a pre-PRD blueprint
                  for an agent you can build in the terminal.
                </p>
                <Button onClick={() => { setShowCreateForm(true); setEditingId(null) }}>
                  <Plus size={14} className="mr-1.5" />
                  Create First Role
                </Button>
              </div>
            )}

            {!isLoading && !error && grouped.length === 0 && searchQuery && (
              <p className="text-center text-sm text-muted-foreground py-16">
                No results for &ldquo;{searchQuery}&rdquo;
              </p>
            )}

            {/* Category sections */}
            {grouped.map(([category, items]) => {
              const meta = getCategoryMeta(category)
              return (
                <section key={category} className="mb-8">
                  {/* Category header */}
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${meta.color}`}>
                      {meta.icon}
                      {meta.label}
                    </span>
                    <span className="text-xs text-muted-foreground">{items.length} role{items.length !== 1 ? 's' : ''}</span>
                  </div>

                  {/* Cards grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {items.map((bp) => {
                      const statusMeta = STATUS_BADGE[bp.status as BlueprintStatus] ?? STATUS_BADGE.draft
                      const isSelected = selectedId === bp.id
                      return (
                        <button
                          key={bp.id}
                          type="button"
                          onClick={() => setSelectedId(isSelected ? null : bp.id)}
                          className={`text-left bg-card rounded-lg border border-border border-l-4 ${meta.cardBorder} p-4 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer ${
                            isSelected ? 'ring-2 ring-primary shadow-md' : ''
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2 mb-1.5">
                            <h4 className="text-sm font-medium text-foreground truncate">{bp.name}</h4>
                            <span className={`shrink-0 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border ${statusMeta.className}`}>
                              {statusMeta.label}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-2">{bp.one_liner}</p>
                          <div className="flex items-center gap-2">
                            <code className="text-[10px] bg-muted px-1.5 py-0.5 rounded font-mono text-muted-foreground truncate max-w-[140px]">
                              {bp.role_tag}
                            </code>
                            {bp.subcategory && (
                              <span className="text-[10px] text-muted-foreground">{bp.subcategory}</span>
                            )}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </section>
              )
            })}
          </div>
        </div>

        {/* Right panel: detail view (slides in when selected) */}
        {selectedBp && (
          <div className="w-[420px] border-l border-border bg-card overflow-auto shrink-0">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground truncate">{selectedBp.name}</h3>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0"
                  title="Edit"
                  onClick={() => { setEditingId(selectedBp.id); setShowCreateForm(true) }}
                >
                  <Edit size={14} />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                  title="Delete"
                  onClick={() => setConfirmDeleteId(selectedBp.id)}
                >
                  <Trash2 size={14} />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setSelectedId(null)}
                >
                  <X size={14} />
                </Button>
              </div>
            </div>

            <div className="p-4 space-y-4">
              {/* Status + category */}
              <div className="flex flex-wrap gap-2">
                {(() => {
                  const sm = STATUS_BADGE[selectedBp.status as BlueprintStatus] ?? STATUS_BADGE.draft
                  return (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${sm.className}`}>
                      {sm.label}
                    </span>
                  )
                })()}
                <Badge variant="outline" className="text-[10px]">{getCategoryMeta(selectedBp.category).label}</Badge>
                {selectedBp.subcategory && (
                  <Badge variant="secondary" className="text-[10px]">{selectedBp.subcategory}</Badge>
                )}
              </div>

              {/* One-liner */}
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide block mb-1">Description</span>
                <p className="text-sm text-foreground">{selectedBp.one_liner}</p>
              </div>

              {/* Role tag */}
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide block mb-1">Role Tag</span>
                <code className="text-xs bg-muted px-2 py-1 rounded font-mono">{selectedBp.role_tag}</code>
              </div>

              {/* Target files */}
              {selectedBp.target_files.length > 0 && (
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide block mb-1">
                    <Tag size={10} className="inline mr-1" />
                    Target Files
                  </span>
                  <div className="space-y-1">
                    {selectedBp.target_files.map((f, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs">
                        <FileText size={12} className="text-muted-foreground shrink-0" />
                        <code className="font-mono text-muted-foreground truncate">{f}</code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PRD Content */}
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide block mb-1">PRD / Documentation</span>
                {selectedBp.prd_content ? (
                  <div className="bg-muted/50 rounded-lg p-3 text-xs text-foreground whitespace-pre-wrap font-mono max-h-[400px] overflow-auto border border-border">
                    {selectedBp.prd_content}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground italic">No PRD content yet. Click Edit to add documentation.</p>
                )}
              </div>

              {/* Timestamps */}
              <div className="text-[10px] text-muted-foreground pt-2 border-t border-border">
                {selectedBp.created_at && <div>Created: {new Date(selectedBp.created_at).toLocaleDateString()}</div>}
                {selectedBp.updated_at && <div>Updated: {new Date(selectedBp.updated_at).toLocaleDateString()}</div>}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <BlueprintFormDialog
        open={showCreateForm}
        onOpenChange={setShowCreateForm}
        editingBlueprint={editingId ? blueprints?.find((b) => b.id === editingId) ?? null : null}
        onCreated={(bp) => {
          setShowCreateForm(false)
          setEditingId(null)
          setSelectedId(bp.id)
        }}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={confirmDeleteId !== null} onOpenChange={(open) => { if (!open) setConfirmDeleteId(null) }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Role Blueprint</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this role? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDeleteId(null)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMut.isPending}
            >
              {deleteMut.isPending && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
              {deleteMut.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Create / Edit Form Dialog
// ---------------------------------------------------------------------------

const CATEGORY_OPTIONS = [
  'updating', 'building', 'testing', 'deploying',
  'security', 'devops', 'monitoring', 'research',
]

function BlueprintFormDialog({
  open,
  onOpenChange,
  editingBlueprint,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingBlueprint: RoleBlueprint | null
  onCreated: (bp: RoleBlueprint) => void
}) {
  const createMut = useCreateBlueprint()
  const updateMut = useUpdateBlueprint()
  const isEditing = editingBlueprint !== null
  const isPending = createMut.isPending || updateMut.isPending

  const [name, setName] = useState('')
  const [roleTag, setRoleTag] = useState('')
  const [category, setCategory] = useState('updating')
  const [subcategory, setSubcategory] = useState('')
  const [oneLiner, setOneLiner] = useState('')
  const [prdContent, setPrdContent] = useState('')
  const [targetFilesStr, setTargetFilesStr] = useState('')
  const [status, setStatus] = useState<BlueprintStatus>('draft')

  // Reset form when opening
  const handleOpenChange = useCallback(
    (isOpen: boolean) => {
      if (isOpen && editingBlueprint) {
        setName(editingBlueprint.name)
        setRoleTag(editingBlueprint.role_tag)
        setCategory(editingBlueprint.category)
        setSubcategory(editingBlueprint.subcategory ?? '')
        setOneLiner(editingBlueprint.one_liner)
        setPrdContent(editingBlueprint.prd_content)
        setTargetFilesStr(editingBlueprint.target_files.join('\n'))
        setStatus(editingBlueprint.status as BlueprintStatus)
      } else if (isOpen) {
        setName('')
        setRoleTag('')
        setCategory('updating')
        setSubcategory('')
        setOneLiner('')
        setPrdContent('')
        setTargetFilesStr('')
        setStatus('draft')
      }
      onOpenChange(isOpen)
    },
    [editingBlueprint, onOpenChange]
  )

  // Auto-generate role_tag from name (only in create mode)
  const handleNameChange = useCallback(
    (val: string) => {
      setName(val)
      if (!isEditing) {
        setRoleTag(val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''))
      }
    },
    [isEditing]
  )

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      const targetFiles = targetFilesStr
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean)

      if (isEditing && editingBlueprint) {
        updateMut.mutate(
          {
            id: editingBlueprint.id,
            data: { name, role_tag: roleTag, category, subcategory: subcategory || null, one_liner: oneLiner, prd_content: prdContent, target_files: targetFiles, status },
          },
          {
            onSuccess: (bp) => onCreated(bp),
          }
        )
      } else {
        const payload: RoleBlueprintCreate = {
          name,
          role_tag: roleTag,
          category,
          one_liner: oneLiner,
          prd_content: prdContent,
          subcategory: subcategory || null,
          target_files: targetFiles,
          status,
        }
        createMut.mutate(payload, {
          onSuccess: (bp) => onCreated(bp),
        })
      }
    },
    [name, roleTag, category, subcategory, oneLiner, prdContent, targetFilesStr, status, isEditing, editingBlueprint, createMut, updateMut, onCreated]
  )

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Role Blueprint' : 'New Role Blueprint'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update this agent role blueprint.'
              : 'Define a new agent role. This creates a pre-PRD entry in your role library.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name + Tag */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-foreground block mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="SDK Update Agent"
                required
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-foreground block mb-1">Role Tag</label>
              <input
                type="text"
                value={roleTag}
                onChange={(e) => setRoleTag(e.target.value)}
                placeholder="sdk-update-agent"
                required
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground font-mono"
              />
            </div>
          </div>

          {/* Category + Subcategory */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-foreground block mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary"
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>{getCategoryMeta(c).label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-foreground block mb-1">Subcategory (optional)</label>
              <input
                type="text"
                value={subcategory}
                onChange={(e) => setSubcategory(e.target.value)}
                placeholder="sdk, dependencies, etc."
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground"
              />
            </div>
          </div>

          {/* Status */}
          <div>
            <label className="text-xs font-medium text-foreground block mb-1">Status</label>
            <div className="flex gap-2">
              {(['draft', 'ready', 'built'] as const).map((s) => {
                const sm = STATUS_BADGE[s]
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStatus(s)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                      status === s
                        ? `${sm.className} ring-2 ring-primary`
                        : 'bg-muted text-muted-foreground border-border hover:bg-accent'
                    }`}
                  >
                    {sm.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* One-liner */}
          <div>
            <label className="text-xs font-medium text-foreground block mb-1">One-Liner Description</label>
            <input
              type="text"
              value={oneLiner}
              onChange={(e) => setOneLiner(e.target.value)}
              placeholder="Agent that keeps the Claude Agent SDK up to date with automated testing"
              required
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground"
            />
          </div>

          {/* Target files */}
          <div>
            <label className="text-xs font-medium text-foreground block mb-1">
              Target Files <span className="font-normal text-muted-foreground">(one per line — files this role touches)</span>
            </label>
            <textarea
              value={targetFilesStr}
              onChange={(e) => setTargetFilesStr(e.target.value)}
              placeholder={`.claude/agents/sdk-updater.md\nrequirements.txt\nCLAUDE.md`}
              rows={3}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground font-mono"
            />
          </div>

          {/* PRD content */}
          <div>
            <label className="text-xs font-medium text-foreground block mb-1">PRD / Documentation</label>
            <textarea
              value={prdContent}
              onChange={(e) => setPrdContent(e.target.value)}
              placeholder="Detailed description of the agent role, what it does, how to build it, steps involved..."
              rows={10}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg outline-none focus:ring-2 focus:ring-primary placeholder:text-muted-foreground font-mono"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending || !name || !roleTag || !oneLiner}>
              {isPending && <Loader2 className="w-4 h-4 animate-spin mr-1.5" />}
              {isPending ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
