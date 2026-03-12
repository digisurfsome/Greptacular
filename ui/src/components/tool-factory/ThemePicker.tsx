/**
 * Modal for selecting a theme preset, uploading an image for extraction, or skipping.
 */

import { useState, useRef, useCallback } from 'react'
import { Upload, Loader2, Palette, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { ThemePreviewCard } from './ThemePreviewCard'
import { useThemes, useExtractTheme } from '@/hooks/useToolThemes'
import type { TFThemeConfig } from '@/lib/types'

interface ThemePickerProps {
  isOpen: boolean
  onSelect: (theme: TFThemeConfig | null) => void
  onClose: () => void
}

export function ThemePicker({ isOpen, onSelect, onClose }: ThemePickerProps) {
  const [selectedTheme, setSelectedTheme] = useState<TFThemeConfig | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { data: themes, isLoading } = useThemes()
  const extractTheme = useExtractTheme()

  const handleImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setIsExtracting(true)
    try {
      const result = await extractTheme.mutateAsync(file)
      setSelectedTheme(result)
    } catch {
      // Extraction failed -- user can pick a preset instead
    } finally {
      setIsExtracting(false)
    }
  }, [extractTheme])

  const handleConfirm = useCallback(() => {
    onSelect(selectedTheme)
  }, [selectedTheme, onSelect])

  const handleSkip = useCallback(() => {
    onSelect(null)
  }, [onSelect])

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Palette size={20} />
            Choose a Theme
          </DialogTitle>
          <DialogDescription>
            Pick a preset theme, upload a screenshot to extract colors, or skip for the default.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-primary" />
          </div>
        ) : (
          <div className="space-y-4 max-h-[400px] overflow-y-auto">
            {/* Theme grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {themes?.map((t) => (
                <ThemePreviewCard
                  key={t.theme_id}
                  theme={t}
                  selected={selectedTheme?.theme_id === t.theme_id}
                  onClick={() => setSelectedTheme(t)}
                />
              ))}
            </div>

            {/* Upload screenshot */}
            <div className="flex items-center gap-3 pt-2 border-t border-border">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => fileInputRef.current?.click()}
                disabled={isExtracting}
              >
                {isExtracting ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Upload size={14} />
                )}
                {isExtracting ? 'Extracting...' : 'Upload Screenshot'}
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              {selectedTheme?.source === 'extracted' && (
                <span className="text-xs text-muted-foreground">
                  Extracted theme selected
                </span>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="ghost" onClick={handleSkip}>
            Skip
          </Button>
          <Button variant="outline" onClick={onClose}>
            <X size={14} className="mr-1" />
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={!selectedTheme}>
            Use Theme
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
