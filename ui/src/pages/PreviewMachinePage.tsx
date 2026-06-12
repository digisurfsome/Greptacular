/**
 * PreviewMachinePage — the Scraper hub.
 *
 * A small toggle at the top switches between two tools that share the Scraper
 * nav tab:
 *   - "Preview Machine" (default): drives the scripts/preview_machine/ pipeline.
 *   - "Market Scraper": the existing Reddit scraper, rendered unchanged.
 *
 * The Market Scraper component is imported and rendered as-is — its internals
 * are never modified here.
 */

import { useState } from 'react'
import { ArrowLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { MarketScraperPage } from './MarketScraperPage'
import { PipelinePanel } from '@/components/preview-machine/PipelinePanel'
import { CalibrationCard } from '@/components/preview-machine/CalibrationCard'
import type { CopywriterSettings } from '@/components/preview-machine/CopywriterControls'

type HubTool = 'preview-machine' | 'market-scraper'

/** Sensible defaults for the copywriter stage (matches script defaults). */
const DEFAULT_COPYWRITER: CopywriterSettings = {
  model: 'sonnet',
  perHour: 0,
  autoRetry: false,
  autoRetryMinutes: 60,
  batchSize: 10,
}

export function PreviewMachinePage() {
  const [tool, setTool] = useState<HubTool>('preview-machine')

  // Copywriter settings live at the page level so the calibration card's
  // "Use this" button can fill the Per hour input shown inside PipelinePanel.
  const [copywriter, setCopywriter] = useState<CopywriterSettings>(DEFAULT_COPYWRITER)

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb + tool toggle */}
      <div className="flex items-center h-10 px-3 border-b border-border bg-card shrink-0">
        <nav className="flex items-center gap-1 text-sm">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground h-7 px-2"
            onClick={() => {
              window.location.hash = '#/dashboard'
            }}
          >
            <ArrowLeft size={14} />
            <span className="text-xs">Dashboard</span>
          </Button>
          <ChevronRight size={12} className="text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Scraper</span>
        </nav>

        <div className="ml-auto flex items-center gap-1 rounded-lg border border-border p-0.5">
          <Button
            variant={tool === 'preview-machine' ? 'default' : 'ghost'}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setTool('preview-machine')}
          >
            Preview Machine
          </Button>
          <Button
            variant={tool === 'market-scraper' ? 'default' : 'ghost'}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setTool('market-scraper')}
          >
            Market Scraper
          </Button>
        </div>
      </div>

      {/* Body */}
      {tool === 'market-scraper' ? (
        // Existing Reddit scraper, rendered unchanged.
        <div className="flex-1 overflow-hidden">
          <MarketScraperPage />
        </div>
      ) : (
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Preview Machine</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Run the lead pipeline one step at a time: pull businesses, filter, audit their
                sites, write copy, then build preview sites.
              </p>
            </div>

            <PipelinePanel copywriter={copywriter} onCopywriterChange={setCopywriter} />

            <CalibrationCard
              onUseSuggested={(perHour) => setCopywriter((prev) => ({ ...prev, perHour }))}
            />
          </div>
        </main>
      )}
    </div>
  )
}
