/**
 * Confirmation modal before deploying a tool to Google Sheets.
 * Shows sheet name, tab count, theme preview, API key status.
 */

import { useState } from 'react'
import { Loader2, ExternalLink, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import type { TFSheetBlueprint, TFThemeConfig } from '@/lib/types'

interface DeployConfirmationProps {
  isOpen: boolean
  blueprint: TFSheetBlueprint
  theme: TFThemeConfig | null
  googleConnected: boolean
  isDeploying: boolean
  onDeploy: (sheetName: string) => void
  onClose: () => void
  onConnectGoogle: () => void
}

export function DeployConfirmation({
  isOpen,
  blueprint,
  theme,
  googleConnected,
  isDeploying,
  onDeploy,
  onClose,
  onConnectGoogle,
}: DeployConfirmationProps) {
  const [sheetName, setSheetName] = useState(blueprint.tool_name)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Deploy to Google Sheets</DialogTitle>
          <DialogDescription>
            Review and confirm your tool deployment.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Sheet name */}
          <div>
            <label className="text-xs font-medium text-muted-foreground">Sheet Name</label>
            <Input
              value={sheetName}
              onChange={(e) => setSheetName(e.target.value)}
              className="mt-1"
            />
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-md border border-border p-2">
              <span className="text-muted-foreground">Tabs</span>
              <p className="font-semibold">{blueprint.chain_config.length}</p>
            </div>
            <div className="rounded-md border border-border p-2">
              <span className="text-muted-foreground">APIs</span>
              <p className="font-semibold">{blueprint.detected_apis.length}</p>
            </div>
          </div>

          {/* Theme preview */}
          {theme && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-muted-foreground">Theme</span>
              <div className="flex items-center gap-2">
                <div className="flex gap-0.5">
                  {[theme.colors.brand_light, theme.colors.brand_default, theme.colors.brand_dark].map((c, i) => (
                    <div key={i} className="w-5 h-5 rounded border border-border/50" style={{ backgroundColor: c }} />
                  ))}
                </div>
                <span className="text-sm text-foreground">{theme.theme_name}</span>
              </div>
            </div>
          )}

          {/* Google connection status */}
          <div className="flex items-center gap-2 rounded-md border border-border p-3">
            <Shield size={16} className={googleConnected ? 'text-[var(--color-neo-done)]' : 'text-muted-foreground'} />
            <span className="text-sm flex-1">
              {googleConnected ? 'Google account connected' : 'Google account not connected'}
            </span>
            {!googleConnected && (
              <Button variant="outline" size="sm" onClick={onConnectGoogle}>
                <ExternalLink size={12} className="mr-1" />
                Connect
              </Button>
            )}
          </div>

          {/* Required APIs */}
          {blueprint.detected_apis.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-muted-foreground">Required API Keys</span>
              <div className="flex flex-wrap gap-1">
                {blueprint.detected_apis.map((api) => (
                  <Badge key={api.service_key} variant="outline" className="text-xs">
                    {api.service_name}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isDeploying}>
            Cancel
          </Button>
          <Button
            onClick={() => onDeploy(sheetName)}
            disabled={!sheetName.trim() || !googleConnected || isDeploying}
          >
            {isDeploying ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Deploying...
              </>
            ) : (
              'Deploy'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
